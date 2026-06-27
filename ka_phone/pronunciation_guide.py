#!/usr/bin/env python3
"""
PRONUNCIATION GUIDE — Dictionnaire phonétique + Templates vocaux dynamiques
============================================================================
Deux fonctionnalités :
  1. PHONETIC DICT : remplace les mots difficiles par leur prononciation
     avant synthèse TTS (Edge-TTS prononce mieux le texte phonétique).
  2. VOCAL TEMPLATES : personas vocales complètes (style, vocabulaire,
     patterns de reformulation) sur lesquelles la voix se cale.

Usage :
    from pronunciation_guide import PronunciationGuide
    pg = PronunciationGuide()
    
    # Appliquer le dictionnaire phonétique
    text = pg.apply_pronunciation("Bienvenue à Kemet, patrie de Maât.")
    # → "Bienvenue à Kémette, patrie de Maatte."
    
    # Appliquer un template vocal complet
    text, meta = pg.apply_template("Bonjour", "savant_africain")
    # → texte reformulé + métadonnées vocales (style, voix, vitesse)
"""

import re
import json
import os
from typing import Dict, List, Tuple, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data", "speech")
DICT_FILE = os.path.join(DATA_DIR, "pronunciation_dict.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# DICTIONNAIRE PHONÉTIQUE
# ══════════════════════════════════════════════════════════════════════════

PHONETIC_DICT = {
    # Afrique / Kemet
    "Kemet": "Kémette",
    "kemet": "kémette",
    "KEMET": "KÉMETTE",
    "Maât": "Ma ate",
    "maât": "ma ate",
    "MAÂT": "MA ATE",
    "pharaon": "fara-on",
    "Pharaon": "Fara-on",
    "PHARAON": "FARA-ON",
    "Nubie": "Noubie",
    "nubie": "noubie",
    "hieroglyphe": "hiéroglyfe",
    "Hieroglyphe": "Hiéroglyfe",
    "obelique": "obéliske",
    "Obelique": "Obéliske",
    "Kheops": "Kéopsse",
    "kheops": "kéopsse",
    
    # KA / Technique
    "SOPC": "S.O.P.C.",
    "sopc": "S.O.P.C.",
    "HCV": "H.C.V.",
    "hcv": "H.C.V.",
    "SDI": "S.D.I.",
    "sdi": "S.D.I.",
    "GGUF": "Gou-Goufe",
    "gguf": "gougoufe",
    "LLM": "L.L.M.",
    "llm": "L.L.M.",
    "faster-whisper": "fasteur ouissepeur",
    "Faster-Whisper": "Fasteur Ouissepeur",
    "edge-tts": "edge tétéesse",
    "Edge-TTS": "Edge Tétéesse",
    "Piper": "Paillepeur",
    "piper": "paillepeur",
    "XTTS": "X.T.T.S.",
    "xtts": "X.T.T.S.",
    
    # Mathématiques
    "dérivée": "dérivée",
    "intégrale": "intégrale",
    "équation": "équation",
    "solve": "solv",
    "compute": "comput",
    
    # Noms propres
    "Sénégal": "Sénégal",
    "Dakar": "Dakar",
    "Bamako": "Bamako",
    "Abidjan": "Abidjane",
    "Cameroun": "Cameroune",
    "Éthiopie": "Étiopie",
    "Sahara": "Saara",
}

# ══════════════════════════════════════════════════════════════════════════
# TEMPLATES VOCAUX DYNAMIQUES
# ══════════════════════════════════════════════════════════════════════════

VOCAL_TEMPLATES = {
    "savant_kemet": {
        "name": "Le Savant de Kemet",
        "description": "Ton posé, sage, vocabulaire africain ancien",
        "style": "conteur",
        "voice": "henri",
        "speed": 0.92,
        "pitch": "-3%",
        "vocabulary": {
            # Mots à substituer pour un style plus ancien/savant
            "ordinateur": "machine à calculer",
            "internet": "le réseau des savoirs",
            "intelligence artificielle": "conscience ondulatoire",
            "algorithme": "formule de résonance",
            "donnée": "connaissance",
            "cloud": "les nuages distants",
            "téléphone": "tablette de communication",
            "application": "outil numérique",
        },
        "rephrase_patterns": [
            # (pattern regex, replacement) pour reformuler les phrases
            (r"^Je suis (.*?)\.", r"Je suis \1, fils de Kemet."),
            (r"^Bonjour", r"Que la paix de Maât soit avec toi"),
            (r"^Merci", r"Je te rends grâce"),
            (r"^Au revoir", r"Que les anciens guident tes pas"),
            (r"^Oui", r"Certes, il en est ainsi"),
            (r"^Non", r"Cela n'est point"),
        ],
        "tone_markers": {
            "prefix": "Écoute, enfant de la terre... ",
            "suffix": " Ainsi parlaient les anciens.",
            "probability": 0.25,  # 25% du temps
        },
    },
    
    "griot_conteur": {
        "name": "Le Griot",
        "description": "Voix de conteur, rythme lent, ponctuation expressive",
        "style": "conteur",
        "voice": "henri",
        "speed": 0.88,
        "pitch": "-2%",
        "vocabulary": {
            "histoire": "récit",
            "raconter": "transmettre",
            "bonjour": "je te salue",
            "merci": "que ta route soit douce",
            "il était une fois": "jadis, au temps où les ancêtres parlaient",
        },
        "rephrase_patterns": [
            (r"^Il était une fois", r"Écoute... Jadis, au temps où le vent portait les voix des anciens"),
            (r"^Bonjour", r"Je te salue, voyageur"),
            (r"^(.*?)\.$", r"\1... Ainsi va le monde."),
        ],
        "tone_markers": {
            "prefix": "Écoute bien ce que je vais te conter... ",
            "suffix": " Voilà, le conte est terminé.",
            "probability": 0.30,
        },
    },
    
    "assistant_tech": {
        "name": "L'Assistant Technique",
        "description": "Ton vif, précis, vocabulaire technique",
        "style": "professionnel",
        "voice": "henri",
        "speed": 1.05,
        "pitch": "+0%",
        "vocabulary": {},
        "rephrase_patterns": [],
        "tone_markers": {
            "prefix": "",
            "suffix": "",
            "probability": 0,
        },
    },
    
    "coach_bienveillant": {
        "name": "Le Coach",
        "description": "Ton chaleureux, encouragements, positif",
        "style": "chaleureux",
        "voice": "henri",
        "speed": 1.02,
        "pitch": "+5%",
        "vocabulary": {
            "problème": "défi",
            "difficile": "stimulant",
            "impossible": "un excellent challenge",
            "échouer": "apprendre",
            "erreur": "leçon",
        },
        "rephrase_patterns": [
            (r"^Je ne (.*?) pas", r"Tu peux \1, j'en suis certain"),
            (r"^C'est difficile", r"C'est un défi passionnant"),
        ],
        "tone_markers": {
            "prefix": "Super ! ",
            "suffix": " Tu es sur la bonne voie !",
            "probability": 0.20,
        },
    },
    
    "poete_lyrique": {
        "name": "Le Poète",
        "description": "Voix lyrique, métaphores, rimes",
        "style": "enthousiaste",
        "voice": "henri",
        "speed": 0.95,
        "pitch": "+5%",
        "vocabulary": {
            "beau": "splendide",
            "triste": "mélancolique",
            "joie": "allégresse",
            "amour": "passion ardente",
            "ciel": "voûte céleste",
            "mer": "l'immensité bleue",
        },
        "rephrase_patterns": [
            (r"^(.*?)\.$", r"\1, tel un poème gravé dans le marbre du temps."),
        ],
        "tone_markers": {
            "prefix": "Laisse-moi te dire, en vers et en rimes... ",
            "suffix": "",
            "probability": 0.20,
        },
    },
    
    "naturel": {
        "name": "Naturel",
        "description": "Conversation quotidienne, neutre",
        "style": "naturel",
        "voice": "henri",
        "speed": 1.0,
        "pitch": "+0%",
        "vocabulary": {},
        "rephrase_patterns": [],
        "tone_markers": {"prefix": "", "suffix": "", "probability": 0},
    },
}


# ══════════════════════════════════════════════════════════════════════════
# PRONUNCIATION GUIDE
# ══════════════════════════════════════════════════════════════════════════

class PronunciationGuide:
    """
    Guide de prononciation et templates vocaux.
    Améliore la qualité de synthèse en remplaçant les mots difficiles
    et en appliquant des styles de parole complets.
    """

    def __init__(self):
        self.phonetic_dict: Dict[str, str] = dict(PHONETIC_DICT)
        self.templates: Dict[str, dict] = dict(VOCAL_TEMPLATES)
        self._load_custom_dict()

    # ═══ DICTIONNAIRE PHONÉTIQUE ═══

    def apply_pronunciation(self, text: str) -> str:
        """
        Remplace les mots du dictionnaire phonétique par leur prononciation.
        Respecte la casse (majuscule/minuscule).
        """
        result = text
        
        # Trier par longueur décroissante pour éviter les remplacements partiels
        # (ex: "SOPC" avant "SO")
        sorted_words = sorted(self.phonetic_dict.keys(), key=len, reverse=True)
        
        for word in sorted_words:
            pronunciation = self.phonetic_dict[word]
            # Remplacer le mot exact (respecte les frontières de mots)
            # Utiliser \b pour les frontières de mots
            pattern = r'\b' + re.escape(word) + r'\b'
            result = re.sub(pattern, pronunciation, result)

        return result

    def add_word(self, word: str, pronunciation: str):
        """Ajoute un mot au dictionnaire phonétique (en mémoire)."""
        self.phonetic_dict[word] = pronunciation

    def add_words(self, words: Dict[str, str]):
        """Ajoute plusieurs mots au dictionnaire."""
        self.phonetic_dict.update(words)

    def remove_word(self, word: str):
        """Retire un mot du dictionnaire."""
        self.phonetic_dict.pop(word, None)

    def get_dict(self) -> Dict[str, str]:
        """Retourne le dictionnaire complet."""
        return dict(self.phonetic_dict)

    # ═══ TEMPLATES VOCAUX ═══

    def apply_template(self, text: str, template_name: str = "naturel",
                       custom_overrides: Optional[Dict] = None) -> Tuple[str, Dict]:
        """
        Applique un template vocal complet au texte.
        
        Args:
            text: texte original
            template_name: nom du template ("savant_kemet", "griot_conteur", etc.)
            custom_overrides: dict optionnel pour surcharger des parties du template
            
        Returns:
            (texte_reformulé, métadonnées_vocales)
            Les métadonnées contiennent : style, voice, speed, pitch
        """
        template = self.templates.get(template_name, self.templates["naturel"]).copy()

        # Appliquer les surcharges custom
        if custom_overrides:
            template.update(custom_overrides)

        # Étape 1 : Remplacer le vocabulaire spécifique
        result = text
        vocab = template.get("vocabulary", {})
        if vocab:
            sorted_vocab = sorted(vocab.keys(), key=len, reverse=True)
            for word in sorted_vocab:
                replacement = vocab[word]
                pattern = r'\b' + re.escape(word) + r'\b'
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # Étape 2 : Appliquer les patterns de reformulation
        patterns = template.get("rephrase_patterns", [])
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # Étape 3 : Ajouter les tone markers (préfixe/suffixe avec probabilité)
        import random
        markers = template.get("tone_markers", {})
        if markers.get("prefix") and random.random() < markers.get("probability", 0):
            result = markers["prefix"] + result[0].lower() + result[1:]
        if markers.get("suffix") and random.random() < markers.get("probability", 0):
            result = result.rstrip(".,;:!? ") + ". " + markers["suffix"]

        # Étape 4 : Appliquer la prononciation phonétique
        result = self.apply_pronunciation(result)

        # Métadonnées vocales pour le TTS
        vocal_meta = {
            "style": template.get("style", "naturel"),
            "voice": template.get("voice", "henri"),
            "speed": template.get("speed", 1.0),
            "pitch": template.get("pitch", "+0%"),
            "template": template_name,
            "template_name": template.get("name", template_name),
        }

        return result, vocal_meta

    def list_templates(self) -> List[Dict]:
        """Liste tous les templates disponibles."""
        return [
            {
                "id": name,
                "name": t["name"],
                "description": t["description"],
                "style": t["style"],
                "voice": t["voice"],
                "speed": t["speed"],
            }
            for name, t in self.templates.items()
        ]

    def add_template(self, name: str, template: dict):
        """Ajoute un template vocal personnalisé."""
        self.templates[name] = template

    def remove_template(self, name: str):
        """Retire un template (sauf 'naturel' qui est le fallback)."""
        if name != "naturel":
            self.templates.pop(name, None)

    # ═══ PERSISTANCE ═══

    def _load_custom_dict(self):
        """Charge le dictionnaire personnalisé depuis le disque."""
        if os.path.exists(DICT_FILE):
            try:
                with open(DICT_FILE, 'r', encoding='utf-8') as f:
                    custom = json.load(f)
                self.phonetic_dict.update(custom)
            except Exception:
                pass

    def save_custom_dict(self):
        """Sauvegarde le dictionnaire personnalisé sur le disque."""
        try:
            with open(DICT_FILE, 'w', encoding='utf-8') as f:
                # Sauvegarder seulement les entrées ajoutées par l'utilisateur
                custom = {k: v for k, v in self.phonetic_dict.items()
                          if k not in PHONETIC_DICT}
                json.dump(custom, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pg = PronunciationGuide()

    print("=" * 60)
    print("PRONUNCIATION GUIDE — Test")
    print("=" * 60)

    # Test prononciation
    test_text = "Bienvenue à Kemet, patrie de Maât. Le SOPC est un LLM sans cloud."
    pronounced = pg.apply_pronunciation(test_text)
    print(f"\nOriginal:     {test_text}")
    print(f"Prononciation: {pronounced}")

    # Test templates
    for tpl_name in ["savant_kemet", "griot_conteur", "coach_bienveillant", "naturel"]:
        text, meta = pg.apply_template("Bonjour, je suis KA, ton double numérique.", tpl_name)
        print(f"\n--- {tpl_name} ---")
        print(f"  Texte:  {text[:80]}...")
        print(f"  Meta:   style={meta['style']}, voice={meta['voice']}, speed={meta['speed']}")

    # Liste des templates
    print(f"\nTemplates disponibles: {len(pg.list_templates())}")
    for t in pg.list_templates():
        print(f"  - {t['id']}: {t['name']} ({t['description'][:40]}...)")

    print("\n✅ Pronunciation Guide fonctionnel")