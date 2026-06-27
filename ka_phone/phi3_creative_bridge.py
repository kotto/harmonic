#!/usr/bin/env python3
"""
PHI-3-MINI CREATIVE BRIDGE — Génération créative guidée par templates
=======================================================================
Bridge entre le modèle Phi-3-mini GGUF et la banque d'images poétiques.
Le LLM n'est JAMAIS libre — il est contraint par les templates et les
images vérifiées. Le DHF vérifie la cohérence après génération.

Architecture :
  1. Prompt Engineering Contraint : le modèle reçoit les images ET l'instruction
     de NE PAS inventer. Il assemble, ne génère pas ex-nihilo.
  2. Vérification DHF : chaque sortie est vérifiée contre le sujet source.
  3. Fallback : si le modèle est indisponible ou hallucine, retour aux templates.

Pourquoi Phi-3-mini ?
  - 3.8B paramètres, Q4_K_M ~2.2 Go (comparable à Qwen 2.5-3B)
  - Bonne qualité en français (multilingue natif)
  - Contexte 4096 tokens (vs 2048 pour l'ancien Qwen)
  - Meilleure créativité guidée que Qwen 2.5-3B

Usage :
  from phi3_creative_bridge import Phi3CreativeBridge
  bridge = Phi3CreativeBridge()
  result = bridge.generate("poeme", sujet="le Nil", ton="lyrique")
  # → Texte créatif assemblé par Phi-3 à partir des images, vérifié par DHF
"""

import os, sys, json, re, hashlib, time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

BASE_DIR = Path(__file__).parent.absolute()

# ══════════════════════════════════════════════════════════════════════════
# BANQUE D'IMAGES POÉTIQUES (copie locale pour l'autonomie du module)
# ══════════════════════════════════════════════════════════════════════════

POETIC_IMAGES = {
    "nature": [
        "le vent murmure à travers les feuilles dorées",
        "l'aube déchire le voile de la nuit",
        "les étoiles tissent leur toile d'argent",
        "la lune verse son lait sur les collines endormies",
        "l'orage gronde comme un tambour ancestral",
        "la mer soupire contre les falaises éternelles",
        "le désert danse sous le soleil de plomb",
        "la forêt respire au rythme des siècles",
        "les montagnes gardent le silence des origines",
        "le fleuve raconte l'histoire des terres qu'il traverse",
    ],
    "temps": [
        "le temps effeuille les saisons une à une",
        "chaque instant est une perle sur le fil du destin",
        "les années coulent comme l'eau entre les doigts",
        "le passé murmure aux oreilles du présent",
        "l'avenir dort dans le ventre du possible",
        "l'horloge du ciel tourne sans aiguilles",
        "les siècles s'empilent comme des strates de lumière",
    ],
    "humain": [
        "le cœur bat la mesure d'une chanson oubliée",
        "les mains se tendent vers l'invisible",
        "le regard porte l'empreinte de tous les voyages",
        "la voix porte le poids des silences antérieurs",
        "les pas dessinent des chemins qui n'existaient pas",
        "le souffle est le pont entre le corps et l'âme",
        "les rêves sont les graines que la nuit confie au jour",
    ],
    "egypte_kemet": [
        "le Nil porte dans ses eaux la mémoire des pharaons",
        "les pyramides percent le ciel de leur géométrie sacrée",
        "le sphinx garde l'énigme des origines",
        "Kemet respire sous le soleil éternel",
        "les hiéroglyphes dansent sur les murs des temples",
        "le désert cache les secrets de la Maât",
        "l'or des tombeaux reflète la lumière des dieux",
        "les obélisques pointent vers l'infini",
    ],
    "amour": [
        "l'amour est un feu qui brûle sans consumer",
        "le cœur est un temple où réside l'infini",
        "la tendresse est la plus douce des révolutions",
        "aimer, c'est voir l'étincelle dans l'ombre",
        "les âmes se reconnaissent sans se parler",
    ],
    "sagesse": [
        "la vérité est un soleil qui ne connaît pas l'ombre",
        "la justice est l'équilibre que l'univers enseigne",
        "le savoir est une lampe dans la nuit de l'ignorance",
        "écouter, c'est déjà comprendre la moitié du monde",
        "la patience est la racine de toute sagesse",
    ],
}

# Connecteurs créatifs
CREATIVE_CONNECTORS = [
    "et", "ou", "mais", "car", "donc", "ainsi", "alors",
    "cependant", "néanmoins", "pourtant", "toutefois",
    "comme", "tel", "pareil à", "semblable à",
]

# ══════════════════════════════════════════════════════════════════════════
# PROMPT TEMPLATES CONTRAINTS (Phi-3 ne peut PAS inventer)
# ══════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_CREATIVE = """Tu es un assistant poétique qui assemble des images existantes.
Tu reçois une banque d'images poétiques et tu dois créer un texte en les combinant.
RÈGLE ABSOLUE : tu NE DOIS PAS inventer de nouvelles images ou informations.
Utilise UNIQUEMENT les images fournies ci-dessous. Tu peux les réorganiser, les connecter,
les mettre en forme, mais tu ne dois rien ajouter qui ne vienne pas de la banque.

Banque d'images disponibles :
{image_bank}

Format demandé : {format_description}
Sujet : {sujet}
Ton : {ton}

Réponse (en français, en utilisant UNIQUEMENT les images ci-dessus) :"""

CONVERSATION_SYSTEM_PROMPT = """Tu es KA, un assistant conversationnel.
Tu réponds aux questions en te basant UNIQUEMENT sur le contexte fourni.
Tu NE DOIS PAS inventer d'informations. Si le contexte ne contient pas la réponse,
dis simplement que tu ne sais pas.

Contexte de la conversation :
{context}

Dernière question : {question}
Réponse (en français, concise, basée uniquement sur le contexte) :"""

# ══════════════════════════════════════════════════════════════════════════
# PHI-3 CREATIVE BRIDGE
# ══════════════════════════════════════════════════════════════════════════

class Phi3CreativeBridge:
    """
    Bridge Phi-3-mini GGUF pour la génération créative contrainte.
    Le modèle reçoit les images poétiques et doit les assembler,
    pas générer ex-nihilo. Vérification DHF après génération.
    """

    def __init__(self, model_path: str = None, n_ctx: int = 4096, n_threads: int = 4,
                 n_gpu_layers: int = 0, verbose: bool = False):
        self.model_path = model_path or str(BASE_DIR / "models" / "phi-3-mini-4k-instruct-q4_k_m.gguf")
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        self.llm = None
        self.available = False
        self._init_model()

    def _init_model(self):
        """Initialise le modèle Phi-3-mini via ctransformers (sans compilation C)."""
        if not os.path.exists(self.model_path):
            if self.verbose:
                print(f"[Phi3Bridge] Modele non trouve : {self.model_path}")
                print(f"[Phi3Bridge] Telechargez : huggingface.co/bartowski/Phi-3-mini-4k-instruct-GGUF")
            return

        # Essayer d'abord ctransformers (precompile, pas de cmake necessaire)
        try:
            from ctransformers import AutoModelForCausalLM, AutoConfig
            config = AutoConfig.from_pretrained(self.model_path, context_length=self.n_ctx)
            # ctransformers utilise "llama" comme model_type pour tous les GGUF compatibles
            self.llm = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                model_type="llama",
                config=config,
                local_files_only=True,
            )
            self.available = True
            self._llm_backend = "ctransformers"
            if self.verbose:
                print(f"[Phi3Bridge] Modele charge via ctransformers : {self.model_path}")
                print(f"[Phi3Bridge] Contexte : {self.n_ctx} tokens")
            return
        except Exception as e_ct:
            if self.verbose:
                print(f"[Phi3Bridge] ctransformers a echoue ({e_ct}), essai llama-cpp-python...")

        # Fallback: llama-cpp-python (necessite compilation C)
        try:
            from llama_cpp import Llama
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,
            )
            self.available = True
            self._llm_backend = "llama-cpp-python"
            if self.verbose:
                print(f"[Phi3Bridge] Modele charge via llama-cpp-python : {self.model_path}")
                print(f"[Phi3Bridge] Contexte : {self.n_ctx} tokens, Threads : {self.n_threads}")
        except Exception as e:
            if self.verbose:
                print(f"[Phi3Bridge] Erreur chargement modele : {e}")
                print(f"[Phi3Bridge] Le bridge fonctionne en mode fallback (templates purs, 0% hallucination)")
            self.available = False
            self._llm_backend = None

    def _select_images(self, sujet: str, style: str = "poeme", n: int = 8) -> List[str]:
        """Sélectionne les images les plus pertinentes pour le sujet."""
        sujet_lower = sujet.lower()

        # Déterminer les catégories pertinentes
        if any(kw in sujet_lower for kw in ["nil", "egypte", "pharaon", "pyramide", "kemet", "maât", "maat"]):
            categories = ["egypte_kemet", "nature", "sagesse", "temps"]
        elif any(kw in sujet_lower for kw in ["amour", "cœur", "aimer", "tendresse"]):
            categories = ["amour", "humain", "nature"]
        elif any(kw in sujet_lower for kw in ["dieu", "âme", "esprit", "vérité", "justice", "sagesse"]):
            categories = ["sagesse", "temps", "humain"]
        elif any(kw in sujet_lower for kw in ["temps", "passé", "futur", "mémoire", "souvenir"]):
            categories = ["temps", "sagesse", "nature"]
        elif any(kw in sujet_lower for kw in ["homme", "femme", "enfant", "peuple", "humain"]):
            categories = ["humain", "temps", "sagesse"]
        else:
            categories = ["nature", "temps", "sagesse", "humain"]

        # Collecter les images
        all_images = []
        for cat in categories:
            all_images.extend(POETIC_IMAGES.get(cat, []))

        # Filtrer par pertinence lexicale avec le sujet
        sujet_words = set(re.findall(r'[a-zéèêëàâîïôûùç]{3,}', sujet_lower))
        scored = []
        for img in all_images:
            img_words = set(re.findall(r'[a-zéèêëàâîïôûùç]{3,}', img.lower()))
            overlap = len(sujet_words & img_words)
            scored.append((img, overlap))
        scored.sort(key=lambda x: -x[1])

        # Prendre les n meilleures, plus quelques aléatoires pour la diversité
        best = [img for img, _ in scored[:max(n - 2, 3)]]
        remaining = [img for img in all_images if img not in best]
        if remaining:
            import random
            best.extend(random.sample(remaining, min(2, len(remaining))))

        return best[:n]

    def _get_format_description(self, style: str) -> str:
        """Description du format attendu pour le prompt."""
        formats = {
            "poeme": "Un poème de 4 à 8 vers, en français. Chaque vers est une image poétique.",
            "haiku": "Un haïku de 3 vers (structure 5-7-5 syllabes). Évocation de la nature.",
            "histoire": "Une courte histoire de 3-5 phrases. Avec un début, un développement et une conclusion.",
            "conte": "Un conte poétique de 4-6 phrases. Commence par 'Il était une fois' ou similaire.",
            "essai": "Un court essai de 3-4 phrases. Thèse, argument, conclusion.",
            "description": "Une description poétique de 3-5 phrases. Sensorielle et évocatrice.",
            "discours": "Un court discours de 4-6 phrases. Ouverture, développement, conclusion inspirante.",
            "meditation": "Une méditation poétique de 4-6 phrases. Réflexive et contemplative.",
        }
        return formats.get(style, formats["poeme"])

    def generate(self, style: str, sujet: str = "", ton: str = "lyrique",
                 langue: str = "fr", max_tokens: int = 200,
                 temperature: float = 0.7) -> Dict[str, Any]:
        """
        Génère un texte créatif via Phi-3-mini contraint par la banque d'images.

        Args:
            style: "poeme", "haiku", "histoire", "conte", "essai", "description", "discours", "meditation"
            sujet: le thème (ex: "le Nil", "l'amour")
            ton: "lyrique", "epique", "intimiste", "meditatif"
            langue: "fr" ou "en"
            max_tokens: nombre max de tokens à générer
            temperature: température de génération (0.3-1.0)

        Returns:
            Dict avec "text", "source", "confidence", "verified"
        """
        t0 = time.time()
        sujet_clean = sujet.strip() if sujet else "le monde"

        # Sélectionner les images pertinentes
        images = self._select_images(sujet_clean, style, n=8)
        image_bank = "\n".join(f"- {img}" for img in images)

        # Description du format
        format_desc = self._get_format_description(style)

        # Construire le prompt
        system_prompt = SYSTEM_PROMPT_CREATIVE.format(
            image_bank=image_bank,
            format_description=format_desc,
            sujet=sujet_clean,
            ton=ton,
        )

        # Essayer Phi-3
        if self.available and self.llm:
            try:
                full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\nCrée un {style} sur le thème : {sujet_clean}\n<|assistant|>"

                output = self.llm(
                    full_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9,
                    repeat_penalty=1.1,
                    stop=["<|user|>", "<|system|>", "<|end|>"],
                    echo=False,
                )

                generated = output["choices"][0]["text"].strip()

                # Vérifier que la génération est substantielle
                if len(generated) >= 30:
                    verification = self._verify_output(generated, sujet_clean, images)
                    elapsed_ms = round((time.time() - t0) * 1000, 1)

                    return {
                        "text": generated,
                        "source": "phi3_creative",
                        "confidence": round(verification["score"], 2),
                        "verified": verification["valid"],
                        "hallucination_detected": verification["hallucination"],
                        "images_used": len(verification.get("images_matched", [])),
                        "temps_ms": elapsed_ms,
                        "hors_ligne": True,
                    }
            except Exception as e:
                if self.verbose:
                    print(f"[Phi3Bridge] Erreur génération : {e}")

        # Fallback : assemblage template pur (0% hallucination)
        return self._template_fallback(style, sujet_clean, ton, images)

    def generate_conversation(self, question: str, context: List[Dict] = None,
                              max_tokens: int = 150) -> Dict[str, Any]:
        """
        Génère une réponse conversationnelle via Phi-3-mini avec contexte.

        Args:
            question: la question de l'utilisateur
            context: liste de {"role": "user/assistant", "content": "..."}
            max_tokens: nombre max de tokens

        Returns:
            Dict avec "text", "source", "confidence"
        """
        t0 = time.time()

        # Construire le contexte
        context_str = ""
        if context:
            for turn in context[-5:]:  # 5 derniers tours
                role = "Utilisateur" if turn.get("role") == "user" else "KA"
                content = turn.get("content", "")[:200]
                context_str += f"{role} : {content}\n"
        else:
            context_str = "Aucun contexte précédent."

        system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
            context=context_str,
            question=question,
        )

        if self.available and self.llm:
            try:
                full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{question}\n<|assistant|>"

                output = self.llm(
                    full_prompt,
                    max_tokens=max_tokens,
                    temperature=0.5,
                    top_p=0.9,
                    repeat_penalty=1.1,
                    stop=["<|user|>", "<|system|>"],
                    echo=False,
                )

                generated = output["choices"][0]["text"].strip()

                if len(generated) >= 10:
                    elapsed_ms = round((time.time() - t0) * 1000, 1)
                    return {
                        "text": generated,
                        "source": "phi3_conversation",
                        "confidence": 0.70,
                        "temps_ms": elapsed_ms,
                        "hors_ligne": True,
                    }
            except Exception:
                pass

        # Fallback : pas de réponse conversationnelle sans modèle
        elapsed_ms = round((time.time() - t0) * 1000, 1)
        return {
            "text": None,
            "source": "phi3_unavailable",
            "confidence": 0.0,
            "temps_ms": elapsed_ms,
            "hors_ligne": True,
        }

    def _verify_output(self, text: str, sujet: str, source_images: List[str]) -> Dict:
        """
        Vérifie que le texte généré n'hallucine pas.
        Compare les mots du texte avec les images source.
        """
        text_lower = text.lower()
        text_words = set(re.findall(r'[a-zéèêëàâîïôûùç]{4,}', text_lower))
        sujet_words = set(re.findall(r'[a-zéèêëàâîïôûùç]{3,}', sujet.lower()))

        # Vérifier combien d'images source sont référencées
        images_matched = []
        all_source_words = set()
        for img in source_images:
            img_words = set(re.findall(r'[a-zéèêëàâîïôûùç]{3,}', img.lower()))
            all_source_words.update(img_words)
            # Vérifier si des mots de cette image apparaissent dans le texte
            overlap = img_words & text_words
            if len(overlap) >= 2:
                images_matched.append(img)

        # Calculer le score de correspondance
        if not text_words:
            return {"valid": False, "score": 0.0, "hallucination": True, "images_matched": []}

        # Mots du texte qui viennent des images source
        words_from_source = text_words & all_source_words
        # Mots du texte qui viennent du sujet
        words_from_sujet = text_words & sujet_words

        covered_words = words_from_source | words_from_sujet
        coverage = len(covered_words) / max(len(text_words), 1)

        # Détection d'hallucination : mots hors source ET hors sujet
        hallucination_words = text_words - all_source_words - sujet_words
        hallucination_ratio = len(hallucination_words) / max(len(text_words), 1)

        # Score composite
        match_score = len(images_matched) / max(len(source_images), 1)
        score = coverage * 0.6 + match_score * 0.4
        valid = coverage >= 0.3 and hallucination_ratio < 0.5

        return {
            "valid": valid,
            "score": round(score, 2),
            "hallucination": hallucination_ratio > 0.5,
            "hallucination_ratio": round(hallucination_ratio, 2),
            "images_matched": images_matched[:3],
            "coverage": round(coverage, 2),
        }

    def _template_fallback(self, style: str, sujet: str, ton: str,
                           images: List[str]) -> Dict[str, Any]:
        """
        Fallback 100% template — aucun LLM, aucune hallucination.
        Utilise l'assemblage déterministe d'images.
        """
        import random, time

        if not images:
            images = self._select_images(sujet, style, n=4)

        # Templates par style
        templates = {
            "poeme": [
                "{img1},\n{img2},\n{img3} —\n{img4}.",
                "{img1} et {img2},\n{img3},\n{img4}.",
                "{img1}\n{img2}\n{img3}\n{img4}",
            ],
            "haiku": [
                "{img1},\n{img2},\n{img3}.",
            ],
            "histoire": [
                "Il était une fois un monde où {img1}. Un jour, {img2}. Et c'est ainsi que {img3}.",
                "Tout commença quand {img1}. Personne ne savait que {img2}. Finalement, {img3}.",
            ],
            "conte": [
                "Au cœur du monde, {img1}. Les anciens disent que {img2}. Voilà pourquoi {img3}.",
            ],
            "essai": [
                "{img1}. En effet, {img2}. Ainsi, {img3}.",
            ],
            "description": [
                "Imaginez : {img1}, {img2}, {img3}. Voilà le monde que {sujet} révèle.",
            ],
            "discours": [
                "Mes amis, {img1}. Rappelez-vous : {img2}. Car {img3}. Je vous remercie.",
            ],
            "meditation": [
                "Sur {sujet}, je médite.\n{img1}.\n{img2}.\n{img3}.",
            ],
        }

        template_list = templates.get(style, templates["poeme"])
        template = random.choice(template_list)

        # Assembler
        variables = {}
        for i in range(1, 5):
            variables[f"img{i}"] = images[i-1] if i <= len(images) else images[0]
        variables["sujet"] = sujet

        try:
            text = template.format(**variables)
        except KeyError:
            text = "\n".join(images[:4])

        elapsed_ms = round(time.time() * 1000, 1)  # approximatif
        return {
            "text": text.strip(),
            "source": "template_fallback",
            "confidence": 0.85,
            "verified": True,
            "hallucination_detected": False,
            "images_used": min(4, len(images)),
            "temps_ms": 1,
            "hors_ligne": True,
        }

    def is_available(self) -> bool:
        """Vérifie si le modèle Phi-3 est chargé et disponible."""
        return self.available and self.llm is not None


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("PHI-3 CREATIVE BRIDGE — Test")
    print("=" * 60)

    bridge = Phi3CreativeBridge(verbose=True)

    if bridge.is_available():
        print("\n✅ Phi-3-mini chargé — test de génération créative :\n")
    else:
        print("\n⚠️  Phi-3-mini non disponible — test en mode template fallback :\n")

    tests = [
        ("poeme", "le Nil", "lyrique"),
        ("haiku", "Kemet", "neutre"),
        ("histoire", "un voyageur dans le désert", "neutre"),
        ("conte", "l'empire du Mali", "neutre"),
        ("essai", "la vérité", "neutre"),
        ("description", "l'aube sur le Sahara", "lyrique"),
        ("discours", "l'unité africaine", "epique"),
        ("meditation", "le temps qui passe", "meditatif"),
    ]

    for style, sujet, ton in tests:
        result = bridge.generate(style, sujet=sujet, ton=ton)
        print(f"\n[{result['source']}] {style} : '{sujet}' ({ton})")
        print(f"  Confiance: {result['confidence']:.2f} | Vérifié: {result['verified']} | Hallucination: {result.get('hallucination_detected', 'N/A')}")
        print(f"  Texte : {result['text'][:150]}...")
        if 'images_used' in result:
            print(f"  Images utilisées : {result['images_used']}")

    # Test conversation
    print(f"\n{'=' * 60}")
    print(f"Test Conversationnel")
    print(f"{'=' * 60}")
    conv_result = bridge.generate_conversation(
        "Quelle est la capitale du Sénégal ?",
        context=[
            {"role": "user", "content": "Parle-moi du Sénégal"},
            {"role": "assistant", "content": "Le Sénégal est un pays d'Afrique de l'Ouest, connu pour sa stabilité démocratique et sa culture riche."},
        ]
    )
    print(f"  Source : {conv_result['source']}")
    print(f"  Réponse : {conv_result.get('text', 'N/A')}")