#!/usr/bin/env python3
"""
WAVE RESONANCE ENGINE — "Waves Are All You Need"
====================================================
Transforme une question en multiples variations ondulatoires,
les filtre par resonance holographique et fait emerger la
meilleure formulation pour interroger la base de connaissances.

Principe :
  1. WAVE VARIATOR : N variations quantiques de la question
  2. HOLOGRAPHIC FILTER : correlation de phase avec l'hologramme
  3. WAVE COLLAPSE : la meilleure variation interroge les sources

Philosophie :
  "Un point de l'hologramme contient l'information du tout.
  La question n'est pas cherchee — elle resonne.
  La reponse n'est pas trouvee — elle emerge."

Usage :
  from wave_resonance_engine import WaveResonanceEngine
  wre = WaveResonanceEngine()
  best_variation, score = wre.resonate("Qui etait le pharaon de la 4e dynastie ?")
  # → ("Quels etaient les souverains de la quatrieme dynastie egyptienne ?", 0.87)
"""

import os, sys, re, json, hashlib, random, math
from typing import List, Tuple, Dict, Optional
import numpy as np

# ══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895  # Nombre d'or
ALPHA = 1.0 / PHI        # Inverse du nombre d'or
HOLOGRAM_SIZE = 256
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "wave_resonance")
os.makedirs(DATA_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════
# 1. WAVE VARIATOR — Génération quantique de variations
# ══════════════════════════════════════════════════════════════════════════

# Opérateurs de transformation sémantique
SEMANTIC_SUBSTITUTIONS = {
    # Synonymes / variantes
    "pharaon": ["roi d'Égypte", "souverain egyptien", "monarque de Kemet", "pharaon"],
    "roi": ["souverain", "monarque", "pharaon", "roi"],
    "reine": ["souveraine", "pharaonne", "reine"],
    "dynastie": ["lignee", "dynastie", "famille royale", "maison"],
    "egypte": ["Kemet", "Égypte", "terre des pharaons", "vallee du Nil"],
    "egyptien": ["de Kemet", "egyptien", "pharaonique", "du Nil"],
    "pyramide": ["tombeau", "pyramide", "monument funeraire", "sepulture"],
    "capitale": ["capitale", "ville principale", "siege du gouvernement"],
    "pays": ["nation", "pays", "etat", "territoire"],
    "guerre": ["conflit", "guerre", "bataille decisive", "affrontement"],
    "bataille": ["combat", "bataille", "affrontement", "conflit arme"],
    "decouverte": ["trouvaille", "decouverte", "invention", "revelation"],
    "important": ["crucial", "essentiel", "fondamental", "primordial"],
    "celebre": ["connu", "renomme", "illustre", "celebre"],
    "grand": ["vaste", "immense", "majestueux", "imposant"],
    "ancien": ["antique", "ancien", "millenaire", "seculaire"],
    "premier": ["initial", "premier", "fondateur", "originel"],
    "histoire": ["recit", "histoire", "passé", "chronique"],
    "construire": ["edifier", "batir", "eriger", "construire"],
    "savoir": ["connaissance", "science", "sagesse", "erudition"],
    "monde": ["univers", "monde", "planete", "humanite"],
    "vie": ["existence", "vie", "destin", "parcours"],
    "mort": ["decess", "trepas", "fin", "mort"],
    "dieu": ["divinite", "deite", "dieu", "etre supreme"],
    "temple": ["sanctuaire", "temple", "lieu sacre", "edifice religieux"],
    "empire": ["royaume", "empire", "domination", "puissance"],
    "civilisation": ["culture", "civilisation", "societe", "peuple"],
}

# Opérateurs numériques (4 → quatrième, quatrième → 4e, 4e → IV)
NUMERIC_VARIANTS = {
    # Seulement les variantes non-ambigues (pas de "I" tout seul qui = "1")
    "1": ["premiere", "1ere"], "premiere": ["1ere", "1"],
    "2": ["deuxieme", "2e", "II"], "deuxieme": ["2e", "2"],
    "3": ["troisieme", "3e", "III"], "troisieme": ["3e", "3"],
    "4": ["quatrieme", "4e", "IV"], "quatrieme": ["4e", "4"],
    "5": ["cinquieme", "5e", "V"], "cinquieme": ["5e", "5"],
    "6": ["sixieme", "6e", "VI"], "sixieme": ["6e", "6"],
    "7": ["septieme", "7e", "VII"],
    "8": ["huitieme", "8e", "VIII"],
    "9": ["neuvieme", "9e", "IX"],
    "10": ["dixieme", "10e", "X"],
    "12": ["douzieme", "12e", "XII"],
    "18": ["dix-huitieme", "18e", "XVIII"],
    "19": ["dix-neuvieme", "19e", "XIX"],
    "25": ["vingt-cinquieme", "25e", "XXV"],
}

# Opérateurs de structure de question
QUESTION_STRUCTURES = [
    "{question}",                          # Original
    "Je voudrais savoir : {question}",     # Formel
    "Dis-moi {question}",                  # Direct
    "Peux-tu m'expliquer {question} ?",    # Demande
    "J'aimerais comprendre {question}",    # Personnel
    "{question} s'il te plait",            # Poli
    "Une question : {question}",           # Simple
    "Parle-moi de {sujet}",                # Ouvert
]


class WaveVariator:
    """
    Générateur de variations quantiques d'une question.
    Applique des opérateurs de transformation pour créer
    N formulations différentes à partir d'une question source.
    """

    def __init__(self, num_variations: int = 15):
        self.num_variations = num_variations
        self.substitutions = SEMANTIC_SUBSTITUTIONS
        self.numeric_variants = NUMERIC_VARIANTS
        self.structures = QUESTION_STRUCTURES

    def vary(self, question: str) -> List[str]:
        """
        Génère N variations ondulatoires de la question.

        Stratégie :
        1. Substitution sémantique (remplacer des mots par synonymes)
        2. Variation numérique (1 → première → I)
        3. Permutation (réordonner les concepts)
        4. Amplification structurelle (changer la forme de la question)
        5. Extraction de sujet (question → "Parle-moi de X")
        """
        variations = [question]  # Toujours inclure l'original
        words = re.findall(r'[a-zA-Zéèêëàâîïôûùçœæ]+', question)
        words_lower = [w.lower() for w in words]

        # 1. Substitution sémantique (remplacer 1 mot aléatoire)
        for i, wl in enumerate(words_lower):
            if wl in self.substitutions and len(variations) < self.num_variations:
                original_word = words[i]
                options = [s for s in self.substitutions[wl]
                          if s.lower() != wl]
                if options:
                    sub = random.choice(options)
                    # Préserver la casse
                    if original_word[0].isupper():
                        sub = sub[0].upper() + sub[1:]
                    new_words = list(words)
                    new_words[i] = sub
                    var = " ".join(new_words)
                    var = self._format_question(var, question)
                    if var not in variations:
                        variations.append(var)

        # 2. Variation numérique
        for i, wl in enumerate(words_lower):
            if wl in self.numeric_variants and len(variations) < self.num_variations:
                options = [s for s in self.numeric_variants[wl] if s != wl]
                if options:
                    sub = random.choice(options)
                    new_words = list(words)
                    new_words[i] = sub
                    var = " ".join(new_words)
                    var = self._format_question(var, question)
                    if var not in variations:
                        variations.append(var)

        # 3. Amplification structurelle
        for struct in self.structures:
            if len(variations) >= self.num_variations:
                break
            if struct == "{question}":
                continue
            var = struct.format(question=question, sujet=self._extract_subject(question))
            if var != question and var not in variations:
                variations.append(var)

        # 4. Extraction de sujet pur
        sujet = self._extract_subject(question)
        if sujet:
            var = f"Parle-moi de {sujet}"
            if var not in variations:
                variations.append(var)

        # 5. Combinaison : substitution + structure
        if len(variations) < self.num_variations:
            for v in list(variations):
                if v == question:
                    continue
                subst_count = sum(1 for wl in words_lower
                                 if wl in self.substitutions and random.random() < 0.3)
                if subst_count == 0:
                    continue
                # Appliquer une substitution aleatoire a une variation existante
                for i, wl in enumerate(re.findall(r'[a-zéèêëàâîïôûùç]+', v.lower())):
                    if wl in self.substitutions:
                        options = [s for s in self.substitutions[wl] if s.lower() != wl]
                        if options:
                            sub = random.choice(options)
                            v_new = re.sub(r'\b' + re.escape(wl) + r'\b',
                                         sub, v, count=1, flags=re.IGNORECASE)
                            if v_new not in variations:
                                variations.append(v_new)
                                break
                if len(variations) >= self.num_variations:
                    break

        return variations[:self.num_variations]

    def _format_question(self, text: str, original: str) -> str:
        """Ajoute un ? final si l'original en a un."""
        text = text.strip()
        if original.strip().endswith("?") and not text.endswith("?"):
            text += " ?"
        return text

    def _extract_subject(self, question: str) -> str:
        """Extrait le sujet principal d'une question."""
        # Nettoyer les mots question
        q = re.sub(r'^(?:qui |qu[\'e]est-ce que |que |quoi |quel(?:le)?s? |comment |pourquoi |quand |ou |combien de )',
                  '', question, flags=re.IGNORECASE)
        q = re.sub(r'[?!.]*$', '', q).strip()
        # Prendre les 2-3 premiers mots significatifs
        words = q.split()
        # Filtrer les mots vides
        stop_words = {"le", "la", "les", "un", "une", "des", "de", "du", "est",
                     "etait", "sont", "dans", "sur", "pour", "avec", "par", "en",
                     "au", "aux", "ce", "cette", "ces", "mon", "ton", "son"}
        significatifs = [w for w in words if w.lower() not in stop_words]
        if len(significatifs) >= 2:
            return " ".join(significatifs[:3])
        return q[:60]


# ══════════════════════════════════════════════════════════════════════════
# 2. HOLOGRAPHIC FILTER — Filtrage par résonance
# ══════════════════════════════════════════════════════════════════════════

class HolographicFilter:
    """
    Filtre les variations par résonance holographique.
    Calcule la corrélation de phase entre chaque variation
    et l'hologramme de connaissances.
    """

    def __init__(self, hologram_size: int = HOLOGRAM_SIZE):
        self.size = hologram_size
        self.hologram = self._load_or_create_hologram()

    def _load_or_create_hologram(self):
        """Charge l'hologramme existant ou en crée un nouveau."""
        holo_file = os.path.join(DATA_DIR, "resonance_hologram.npy")
        if os.path.exists(holo_file):
            return np.load(holo_file)
        return np.zeros((self.size, self.size), dtype=np.complex128)

    def _text_to_signature(self, text: str) -> Tuple[float, float]:
        """Convertit un texte en signature fréquentielle (kx, ky)."""
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % (self.size * 100)) / 100.0
        ky = (int(h[16:32], 16) % (self.size * 100)) / 100.0
        kx = (kx - self.size / 2) / self.size * 20
        ky = (ky - self.size / 2) / self.size * 20
        return kx, ky

    def _gaussian_wave(self, kx: float, ky: float, sigma: float = 5.0,
                       amplitude: float = 0.5) -> np.ndarray:
        """Crée un paquet d'onde gaussien."""
        x = np.linspace(-self.size / 2, self.size / 2, self.size)
        y = np.linspace(-self.size / 2, self.size / 2, self.size)
        X, Y = np.meshgrid(x, y)
        env = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
        wave = np.exp(1j * (kx * X / 20 + ky * Y / 20))
        return amplitude * env * wave

    def score(self, text: str) -> float:
        """
        Calcule le score de résonance d'un texte avec l'hologramme.
        Retourne un score entre 0 et 1.
        
        La résonance est la corrélation normalisée entre l'onde du texte
        et l'hologramme. Plus le score est élevé, plus le texte "résonne"
        avec les connaissances stockées.
        """
        if np.sum(np.abs(self.hologram)) < 1e-10:
            return 0.5  # Hologramme vide → score neutre

        kx, ky = self._text_to_signature(text)
        wave = self._gaussian_wave(kx, ky)

        # Corrélation normalisée (cohérence quantique)
        correlation = np.abs(np.sum(wave * np.conj(self.hologram)))
        norm_wave = np.sqrt(np.sum(np.abs(wave)**2))
        norm_holo = np.sqrt(np.sum(np.abs(self.hologram)**2))

        if norm_wave < 1e-10 or norm_holo < 1e-10:
            return 0.0

        coherence = correlation / (norm_wave * norm_holo)
        return float(coherence)

    def filter(self, variations: List[str]) -> List[Tuple[str, float]]:
        """
        Filtre les variations par score de résonance.
        Retourne la liste triée (meilleur score en premier).
        """
        scored = [(v, self.score(v)) for v in variations]
        scored.sort(key=lambda x: -x[1])
        return scored

    def ingest_knowledge(self, text: str, amplitude: float = 0.3):
        """
        Ingère une connaissance dans l'hologramme.
        Chaque connaissance est superposée comme une onde.
        """
        kx, ky = self._text_to_signature(text)
        wave = self._gaussian_wave(kx, ky, amplitude=amplitude)
        self.hologram += wave

        # Normalisation anti-saturation
        max_amp = np.max(np.abs(self.hologram))
        if max_amp > 500.0:
            self.hologram *= 0.98

    def save(self):
        np.save(os.path.join(DATA_DIR, "resonance_hologram.npy"), self.hologram)

    def get_stats(self) -> Dict:
        return {
            "size": f"{self.size}x{self.size}",
            "energy": float(np.sum(np.abs(self.hologram)**2)),
            "density": float(np.mean(np.abs(self.hologram))),
            "max_amplitude": float(np.max(np.abs(self.hologram))),
        }


# ══════════════════════════════════════════════════════════════════════════
# 3. WAVE RESONANCE ENGINE — Orchestrateur
# ══════════════════════════════════════════════════════════════════════════

class WaveResonanceEngine:
    """
    Moteur de resonance ondulatoire.
    
    Transforme une question en onde, la fait resonner dans l'hologramme,
    et fait emerger la meilleure formulation pour interroger la base.
    
    "Waves are all you need"
    """

    def __init__(self, num_variations: int = 15, hologram_size: int = HOLOGRAM_SIZE):
        self.variator = WaveVariator(num_variations=num_variations)
        self.filter = HolographicFilter(hologram_size=hologram_size)
        self.stats = {"total_resonances": 0, "total_variations": 0}

    def resonate(self, question: str, verbose: bool = False) -> Tuple[str, float, List[Tuple[str, float]]]:
        """
        Fait resonner une question dans l'hologramme.
        
        Retourne :
        - best_variation : la meilleure formulation
        - best_score : le score de résonance
        - all_scored : toutes les variations avec leurs scores
        """
        self.stats["total_resonances"] += 1

        # Phase 1 : Génération quantique de variations
        variations = self.variator.vary(question)
        self.stats["total_variations"] += len(variations)

        # Phase 2 : Filtrage holographique
        scored = self.filter.filter(variations)

        if verbose:
            print(f"  [WaveResonance] {len(variations)} variations generees")
            for v, s in scored[:3]:
                print(f"    {s:.3f} | {v[:80]}")

        best_variation, best_score = scored[0] if scored else (question, 0.0)

        return best_variation, best_score, scored

    def ingest(self, text: str, amplitude: float = 0.3):
        """Ingère une connaissance dans l'hologramme de résonance."""
        self.filter.ingest_knowledge(text, amplitude)

    def ingest_batch(self, texts: List[str], amplitude: float = 0.2):
        """Ingère un lot de connaissances."""
        for i, text in enumerate(texts):
            self.filter.ingest_knowledge(text, amplitude)
        self.filter.save()

    def save(self):
        self.filter.save()

    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "hologram": self.filter.get_stats(),
            "avg_variations": (
                self.stats["total_variations"] / max(self.stats["total_resonances"], 1)
            ),
        }


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    engine = WaveResonanceEngine(num_variations=12)

    # Ingérer quelques connaissances pour tester la résonance
    print("Ingestion de connaissances test...")
    engine.ingest("La quatrieme dynastie egyptienne est l'age d'or des pyramides avec Kheops", amplitude=0.5)
    engine.ingest("Kheops etait le pharaon de la 4e dynastie, constructeur de la Grande Pyramide", amplitude=0.5)
    engine.ingest("Le Cameroun a pour capitale Yaounde, ville situee au centre du pays", amplitude=0.5)
    engine.save()

    tests = [
        "Qui etait le pharaon de la 4e dynastie ?",
        "Quelle est la capitale du Cameroun ?",
        "Qui a construit la Grande Pyramide de Gizeh ?",
        "Parle-moi des souverains de la quatrieme dynastie",
    ]

    print(f"\n{'='*60}")
    print("WAVE RESONANCE ENGINE — Test")
    print(f"{'='*60}")

    for q in tests:
        print(f"\n--- Question: {q}")
        best_var, score, all_scored = engine.resonate(q, verbose=True)
        print(f"  Best: {best_var[:80]} (score: {score:.3f})")

    print(f"\n{engine.get_stats()}")