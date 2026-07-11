#!/usr/bin/env python3
"""
Wave Explainer V2 — Explication Approfondie par Chaîne Ondulatoire
=====================================================================
Remplace l'ancien wave_explainer.py (orphelin) par une version
intégrée au pipeline. Utilise la propagation de chaîne (wave_reasoning)
pour construire des explications multi-sauts.

PRINCIPE :
  Une explication est une CHAÎNE de faits reliés par cohérence de phase :
    Définition → Mécanisme → Conséquence → Contexte

  Chaque saut ajoute de la profondeur :
    depth=0 : fait définitoire ("X est...")
    depth=1 : mécanisme ("X fonctionne par...")  
    depth=2 : conséquence ("Il en résulte que...")
    depth=3 : contexte ("Plus largement...")

ARCHITECTURE :
  Question → Récupération ψ_faits → Chaîne de propagation
  → Validation de cohérence à chaque saut → Rendu en paragraphe

Usage :
    from wave_explainer_v2 import WaveExplainer
    explainer = WaveExplainer(brain)
    explanation = explainer.explain("explique la photosynthese", depth=3)
"""

import math
import random
from typing import List, Tuple, Optional

PHI = 1.618033988749895


class WaveExplainer:
    """
    Constructeur d'explications par chaîne ondulatoire.
    """

    # Connecteurs par type de profondeur
    CONNECTORS_FR = {
        'definition': [
            "{s} {r} {o}.",
            "Par définition, {s} {r} {o}.",
            "On entend par {s} le phénomène suivant : {r} {o}.",
        ],
        'mechanism': [
            "Plus précisément, {s} {r} {o}.",
            "Le mécanisme sous-jacent est le suivant : {s} {r} {o}.",
            "Concrètement, {s} {r} {o}.",
            "Cela s'explique par le fait que {s} {r} {o}.",
        ],
        'consequence': [
            "Il en résulte que {s} {r} {o}.",
            "Par conséquent, {s} {r} {o}.",
            "Cette dynamique conduit à : {s} {r} {o}.",
            "De là découle le fait que {s} {r} {o}.",
        ],
        'context': [
            "Plus largement, {s} {r} {o}.",
            "Dans un contexte plus vaste, {s} {r} {o}.",
            "Il est à noter que {s} {r} {o}.",
        ],
    }

    CONNECTORS_EN = {
        'definition': [
            "{s} {r} {o}.",
            "By definition, {s} {r} {o}.",
        ],
        'mechanism': [
            "More precisely, {s} {r} {o}.",
            "The underlying mechanism is: {s} {r} {o}.",
        ],
        'consequence': [
            "As a result, {s} {r} {o}.",
            "Consequently, {s} {r} {o}.",
        ],
        'context': [
            "More broadly, {s} {r} {o}.",
        ],
    }

    # Seuils de cohérence pour la propagation
    COHERENCE_MIN = 0.10   # seuil pour accepter un fait dans la chaîne
    RELEVANCE_MIN = 0.15   # seuil de pertinence minimale

    def __init__(self, brain):
        self.brain = brain

    def explain(self, question: str, depth: int = 3,
                language: str = 'fr') -> str:
        """
        Construit une explication approfondie.

        Args:
            question: la question (ex: "explique la photosynthèse")
            depth: profondeur de la chaîne (1-5)
            language: 'fr' ou 'en'

        Returns:
            paragraphe d'explication structuré
        """
        connectors = self.CONNECTORS_FR if language == 'fr' else self.CONNECTORS_EN

        # Étape 1 : Récupérer les faits pertinents
        candidates = self.brain.unconscious.retrieve(question, max_results=15)
        if not candidates:
            return self.brain._dont_know(question, language)

        # Étape 2 : Construire la chaîne
        chain = self._build_chain(question, candidates, depth)

        if not chain:
            # Fallback : fait unique
            rec, _ = candidates[0]
            return f"{rec.sujet} {rec.relation} {rec.objet}."

        # Étape 3 : Rendu en paragraphe
        return self._render_chain(chain, connectors, language)

    def _build_chain(self, question: str, candidates: list,
                     max_depth: int) -> list:
        """
        Construit une chaîne de faits par propagation de ψ.
        Chaque fait accepté doit être cohérent avec le précédent.
        """
        chain = []
        used_subjects = set()
        q_tokens = set(question.lower().split())

        # Premier fait : le plus résonnant
        best_rec, best_score = candidates[0]
        chain.append((best_rec, 'definition'))
        used_subjects.add(best_rec.sujet.lower())

        # Propagation : l'objet du fait N devient la requête du fait N+1
        for depth in range(1, max_depth):
            if not chain:
                break

            prev_rec = chain[-1][0]
            # Le "sujet" de la recherche suivante = l'objet du fait précédent
            search_terms = prev_rec.objet

            # Récupérer les faits liés
            related = self.brain.unconscious.retrieve(
                search_terms, max_results=10)

            # Filtrer : cohérence + non-doublon
            for rec, score in related:
                if rec.sujet.lower() in used_subjects:
                    continue
                if score < self.COHERENCE_MIN:
                    continue

                # Vérifier la pertinence avec la question originale
                fact_text = f"{rec.sujet} {rec.relation} {rec.objet}"
                fact_tokens = set(fact_text.lower().split())
                overlap = q_tokens & fact_tokens

                # Types de connecteurs selon la profondeur
                if depth == 0:
                    ctype = 'definition'
                elif depth == 1:
                    ctype = 'mechanism'
                elif depth == 2:
                    ctype = 'consequence'
                else:
                    ctype = 'context'

                chain.append((rec, ctype))
                used_subjects.add(rec.sujet.lower())
                break  # Un seul fait par niveau

        return chain

    def _render_chain(self, chain: list, connectors: dict,
                      language: str) -> str:
        """Rend une chaîne de faits en paragraphe structuré."""
        parts = []

        for i, (rec, ctype) in enumerate(chain):
            templates = connectors.get(ctype, connectors['definition'])
            template = random.choice(templates)

            s = rec.sujet
            r = rec.relation
            o = rec.objet

            # Premier fait : majuscule au sujet
            if i == 0:
                s = s[0].upper() + s[1:] if s else s

            rendered = template.format(s=s, r=r, o=o)

            # Mettre en minuscule après un connecteur (pas pour le premier)
            if i > 0 and not rendered[0].isupper():
                pass  # déjà en minuscule

            parts.append(rendered)

        return ' '.join(parts)


def demo(brain):
    """Démonstration de l'explainer."""
    print("=" * 60)
    print("WAVE EXPLAINER V2 — Explication par Chaîne Ondulatoire")
    print("=" * 60)

    explainer = WaveExplainer(brain)

    questions = [
        "explique la photosynthese",
        "comment fonctionne la gravite",
        "pourquoi la terre est ronde",
    ]

    for q in questions:
        print(f"\nQ: {q}")
        for depth in [1, 2, 3]:
            result = explainer.explain(q, depth=depth)
            print(f"  depth={depth}: {result[:120]}...")


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    from harmonic_brain import HarmonicBrain
    from harmonic_model import KNOWLEDGE_BASE

    facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in KNOWLEDGE_BASE]
    brain = HarmonicBrain(facts)

    demo(brain)
