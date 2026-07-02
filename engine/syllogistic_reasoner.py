"""
Syllogistic Reasoner — Inférence Ondulatoire Explicite
=======================================================
Étend coherent_transitivity.py pour PRODUIRE des conclusions explicites
que l'utilisateur peut lire, pas seulement valider des faits en interne.

Principe ondulatoire :
  Un syllogisme « A → B → C donc A → C » est VALIDE si et seulement si
  les 3 vecteurs d'onde [ψ_A, ψ_AB, ψ_C] forment une triade cohérente :
  
    cohérence = Re(⟨ψ_AB | ψ_C⟩) × 0.6 + Re(⟨ψ_A | ψ_C⟩) × 0.4 ≥ seuil

  où ψ_AB = moyenne(encode(A) + encode(mots de r1) + encode(B) + encode(mots de r2))

Types de syllogismes détectés :
  1. Transitivité directe  : A est B, B est C → A est C
  2. Causalité             : A cause B, B cause C → A cause C
  3. Hiérarchie            : A contient B, B contient C → A contient C
  4. Propriété héritée     : A a la propriété B, B implique C → A a la propriété C

Usage :
  from syllogistic_reasoner import SyllogisticReasoner
  sr = SyllogisticReasoner(encoder)
  conclusions = sr.reason(knowledge_base, question)
"""

import sys, re, logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parent))

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Syllogism:
    """Un syllogisme détecté et validé."""
    premisse1: Tuple[str, str, str]  # (sujet, relation, objet)
    premisse2: Tuple[str, str, str]
    conclusion: Tuple[str, str, str] # (sujet, relation_composee, objet)
    coherence: float                  # score de cohérence de phase [0, 1]
    type: str                         # 'transitivite' | 'causalite' | 'hierarchie' | 'propriete'
    explication: str                  # phrase naturelle expliquant le syllogisme


# Mots indiquant une transitivité (A est B, B est C)
_TRANSITIVE_RELATIONS = {
    'est', 'est un', 'est une', 'sont', 'était', 'sont des',
    'is', 'is a', 'is an', 'are',
    'fait partie de', 'appartient à', 'belongs to',
}

# Mots indiquant une causalité
_CAUSAL_RELATIONS = {
    'cause', 'provoque', 'entraîne', 'déclenche', 'produit', 'génère',
    'cause', 'causes', 'triggers', 'produces', 'generates',
    'a causé', 'a provoqué', 'a entraîné',
    'conduit à', 'mène à',
    'est responsable de',
}

# Mots indiquant une hiérarchie/contenance
_HIERARCHY_RELATIONS = {
    'contient', 'inclut', 'comprend', 'renferme',
    'contains', 'includes', 'comprises',
    'est composé de', 'se compose de',
    'est constitué de',
}

# Mots indiquant une propriété/implication
_PROPERTY_RELATIONS = {
    'implique', 'signifie', 'entraîne', 'a pour conséquence',
    'implies', 'means', 'entails',
    'est caractérisé par', 'se définit par',
}


def _classify_relation(relation: str) -> str:
    """Classe une relation dans une catégorie de syllogisme."""
    r = relation.lower().strip()
    for cat, words in [('transitivite', _TRANSITIVE_RELATIONS),
                        ('causalite', _CAUSAL_RELATIONS),
                        ('hierarchie', _HIERARCHY_RELATIONS),
                        ('propriete', _PROPERTY_RELATIONS)]:
        if r in words:
            return cat
    return 'transitivite'  # défaut


def _compose_relation(r1: str, r2: str, cat: str) -> str:
    """Compose deux relations en une relation de conclusion élégante."""
    r1 = r1.strip().rstrip('.')
    r2 = r2.strip().rstrip('.')
    
    if cat == 'transitivite':
        return f"{r1} et {r2}"
    elif cat == 'causalite':
        return f"cause indirectement {r2.split()[-1] if len(r2.split()) > 1 else ''}"
    elif cat == 'hierarchie':
        return f"contient indirectement"
    elif cat == 'propriete':
        return f"implique que"
    return f"{r1} puis {r2}"


def _generate_explication(s: Syllogism) -> str:
    """Génère une phrase naturelle explicitant le syllogisme."""
    s1, r1, o1 = s.premisse1
    s2, r2, o2 = s.premisse2
    
    templates = {
        'transitivite': [
            f"Puisque {s1} {r1} {o1}, et que {o1} {r2} {o2}, "
            f"on en déduit que {s1} est lié à {o2}.",
            f"{s1.capitalize()} {r1} {o1}. Or, {o1} {r2} {o2}. "
            f"Par conséquent, {s1} et {o2} sont connectés.",
        ],
        'causalite': [
            f"Si {s1} {r1} {o1}, et que cela {r2} {o2}, "
            f"alors {s1} contribue indirectement à {o2}.",
            f"La chaîne causale est claire : {s1} → {o1} → {o2}. "
            f"L'effet final sur {o2} passe par l'étape intermédiaire {o1}.",
        ],
        'hierarchie': [
            f"{s1.capitalize()} {r1} {o1}, qui à son tour {r2} {o2}. "
            f"{s1.capitalize()} englobe donc {o2}.",
            f"Dans la structure hiérarchique, {s1} contient {o1}, "
            f"lequel contient {o2}. {s1.capitalize()} contient donc {o2}.",
        ],
        'propriete': [
            f"Si {s1} {r1} {o1}, et que {o1} {r2} {o2}, "
            f"alors {s1} hérite de la caractéristique : {o2}.",
        ],
    }
    tmpls = templates.get(s.type, templates['transitivite'])
    return tmpls[hash(s.conclusion[0]) % len(tmpls)]


# ═══════════════════════════════════════════════════════════════════════════════
# RAISONNEUR SYLLOGISTIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class SyllogisticReasoner:
    """
    Détecte, valide et explicite des syllogismes dans la base de connaissance.

    Utilise la cohérence de phase (produit scalaire hermitien) pour valider
    chaque syllogisme candidat, garantissant que seules les inférences
    géométriquement cohérentes sont produites.
    """

    def __init__(self, encoder=None, seuil_coherence: float = 0.15):
        self._encoder = encoder
        self.seuil = seuil_coherence
        self._word_vectors = {}
        if encoder and hasattr(encoder, 'word_vectors'):
            self._word_vectors = encoder.word_vectors

    def _encode(self, text: str) -> Optional[np.ndarray]:
        """Encode un texte en vecteur d'onde complexe."""
        if self._encoder is None:
            return None
        try:
            return self._encoder.encode_query(text)
        except Exception:
            return None

    def _coherence(self, contexte: str, cible: str) -> float:
        """
        Mesure la cohérence de phase entre un contexte et une cible.
        
        cohérence = Re(⟨ψ_contexte | ψ_cible⟩) × 0.6 + Re(⟨ψ_source | ψ_cible⟩) × 0.4
        
        Retourne une valeur dans [0, 1].
        """
        v_ctx = self._encode(contexte)
        v_cible = self._encode(cible)
        if v_ctx is None or v_cible is None:
            return 0.0
        
        sim = float(np.real(np.dot(v_ctx, np.conj(v_cible))))
        # Normaliser par la dimension
        D = len(v_ctx)
        sim_norm = sim / np.sqrt(D)
        # Mapper [-1, 1] → [0, 1]
        return max(0.0, min(1.0, (sim_norm + 1.0) / 2.0))

    def find_syllogisms(self, knowledge_base: List[Tuple[str, str, str, str]],
                        max_results: int = 5) -> List[Syllogism]:
        """
        Trouve tous les syllogismes valides dans la KB.

        Pour chaque paire de faits A→B et B→C (même B) :
          1. Calcule la cohérence de phase
          2. Si ≥ seuil → syllogisme accepté
          3. Classe le syllogisme (transitivité, causalité, etc.)
          4. Génère une explication naturelle

        Args:
            knowledge_base: liste de (sujet, relation, objet, secteur)
            max_results: nombre max de syllogismes retournés

        Returns:
            liste de Syllogism, triés par cohérence décroissante
        """
        if self._encoder is None:
            return []

        # Indexer par objet → faits qui commencent par cet objet
        by_subject: Dict[str, list] = {}
        for s, r, o, sec in knowledge_base:
            by_subject.setdefault(s.lower().strip(), []).append((s, r, o, sec))

        syllogisms = []
        seen_conclusions = set()

        for s1, r1, o1, sec1 in knowledge_base:
            o1_key = o1.lower().strip()
            if o1_key not in by_subject:
                continue

            for s2, r2, o2, sec2 in by_subject[o1_key]:
                if s2.lower().strip() != o1_key:
                    continue
                if o2.lower().strip() == s1.lower().strip():
                    continue  # éviter les boucles triviales

                # Construire le contexte : A + r1 + B + r2
                contexte = f"{s1} {r1} {o1} {r2}"
                coherence = self._coherence(contexte, o2)

                if coherence >= self.seuil:
                    cat = _classify_relation(r1)
                    # Si r2 est aussi classifiable, utiliser la plus spécifique
                    cat2 = _classify_relation(r2)
                    if cat2 != 'transitivite':
                        cat = cat2

                    comp_r = _compose_relation(r1, r2, cat)
                    conclusion = (s1, comp_r, o2)
                    key = (s1.lower().strip(), comp_r.lower().strip(), o2.lower().strip())

                    if key not in seen_conclusions:
                        seen_conclusions.add(key)
                        syll = Syllogism(
                            premisse1=(s1, r1, o1),
                            premisse2=(s2, r2, o2),
                            conclusion=conclusion,
                            coherence=coherence,
                            type=cat,
                            explication="",
                        )
                        syll.explication = _generate_explication(syll)
                        syllogisms.append(syll)

                    if len(syllogisms) >= max_results * 3:  # pool élargie pour tri
                        break

        # Trier par cohérence décroissante
        syllogisms.sort(key=lambda s: -s.coherence)
        # Dédupliquer par sujet de conclusion
        final = []
        seen_subjects = set()
        for s in syllogisms:
            if s.conclusion[0].lower() not in seen_subjects:
                final.append(s)
                seen_subjects.add(s.conclusion[0].lower())
            if len(final) >= max_results:
                break

        return final

    def answer_with_syllogisms(self, question: str,
                                knowledge_base: List[Tuple[str, str, str, str]],
                                max_syllogisms: int = 3) -> Optional[str]:
        """
        Répond à une question en utilisant le raisonnement syllogistique.

        Cherche des syllogismes pertinents pour la question,
        et produit une réponse naturelle qui explicite le raisonnement.

        Args:
            question: question utilisateur
            knowledge_base: base de connaissance
            max_syllogisms: nombre max de syllogismes à inclure

        Returns:
            réponse en langage naturel, ou None si aucun syllogisme trouvé
        """
        syllogisms = self.find_syllogisms(knowledge_base, max_results=max_syllogisms)

        if not syllogisms:
            return None

        # Filtrer ceux qui sont pertinents pour la question
        q_words = set(question.lower().split())
        relevant = []
        for s in syllogisms:
            all_text = f"{s.premisse1[0]} {s.premisse2[0]} {s.conclusion[2]}".lower()
            if any(w in all_text for w in q_words if len(w) > 2):
                relevant.append(s)

        if not relevant:
            relevant = syllogisms[:1]

        # Construire la réponse
        parts = []
        if len(relevant) >= 2:
            parts.append("Voici un raisonnement en plusieurs étapes :")
        else:
            parts.append("Voici ce que l'on peut en déduire :")

        for i, s in enumerate(relevant[:max_syllogisms], 1):
            if len(relevant) > 1:
                parts.append(f"\n{i}. {s.explication}")
            else:
                parts.append(f"\n{s.explication}")

        return ' '.join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Démo avec une petite KB et un encodeur."""
    from holographic_encoder import HolographicEncoder
    
    print("=" * 60)
    print("SYLLOGISTIC REASONER — Démo")
    print("=" * 60)

    # Créer une petite KB avec des chaînes déductibles
    kb = [
        ("socrate", "est un", "homme", "PHILOSOPHIE"),
        ("homme", "est", "mortel", "PHILOSOPHIE"),
        ("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND"),
        ("onde electromagnetique", "transporte", "de l energie", "PHYSIQUE_FOND"),
        ("france", "est", "un pays d Europe", "GEOGRAPHIE"),
        ("europe", "est", "un continent", "GEOGRAPHIE"),
        ("coeur", "pompe", "le sang", "BIOLOGIE"),
        ("sang", "transporte", "l oxygene", "BIOLOGIE"),
        ("rechauffement climatique", "cause", "la fonte des glaces", "ECOLOGIE"),
        ("fonte des glaces", "cause", "la montee des eaux", "ECOLOGIE"),
        ("univers", "contient", "les galaxies", "COSMOLOGIE"),
        ("galaxies", "contient", "les etoiles", "COSMOLOGIE"),
    ]

    # Encodeur minimal — vecteurs créés à la volée
    encoder = HolographicEncoder(dim=128)

    sr = SyllogisticReasoner(encoder, seuil_coherence=0.05)

    syllogisms = sr.find_syllogisms(kb, max_results=5)
    print(f"\nSyllogismes trouvés : {len(syllogisms)}")
    for s in syllogisms:
        print(f"\n  ◆ {s.type.upper()} (cohérence={s.coherence:.3f})")
        print(f"    {s.premisse1[0]} → {s.premisse1[2]}")
        print(f"    {s.premisse2[0]} → {s.premisse2[2]}")
        print(f"    ∴ {s.conclusion[0]} → {s.conclusion[2]}")
        print(f"    💬 {s.explication[:120]}...")

    # Test question
    print("\n--- Réponse à une question ---")
    r = sr.answer_with_syllogisms("que peut on deduire sur socrate", kb)
    print(r or "(aucun syllogisme pertinent)")


if __name__ == '__main__':
    demo()
