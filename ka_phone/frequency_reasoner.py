#!/usr/bin/env python3
"""
Frequency Reasoner — Raisonnement par fréquence et résonance
=============================================================
Module de raisonnement basé sur l'analyse fréquentielle des concepts.
Intégré au pipeline unified_server.py comme étape 5h.

Usage:
  from frequency_reasoner import FrequencyReasoner
  fr = FrequencyReasoner()
  result = fr.reason("Quelle est la relation entre X et Y ?")
"""

import re
from typing import Optional, Dict, Any


class FrequencyReasoner:
    """Raisonne par association fréquentielle de concepts."""

    def __init__(self):
        self.concept_weights: Dict[str, float] = {}
        self._load_base_concepts()

    def _load_base_concepts(self):
        """Charge les concepts de base avec leurs poids fréquentiels."""
        base = {
            "temps": 0.95, "espace": 0.90, "énergie": 0.88,
            "matière": 0.85, "onde": 0.92, "fréquence": 0.90,
            "harmonie": 0.88, "résonance": 0.87, "information": 0.82,
            "conscience": 0.78, "vie": 0.85, "univers": 0.80,
        }
        self.concept_weights.update(base)

    def reason(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Analyse le prompt par résonance fréquentielle.
        Retourne un dict avec texte de raisonnement ou None si pas de match.
        """
        p = prompt.lower().strip()
        
        # Détecter les concepts présents
        matched_concepts = []
        for concept, weight in self.concept_weights.items():
            if re.search(r'\b' + concept + r'\b', p, re.IGNORECASE):
                matched_concepts.append((concept, weight))
        
        if not matched_concepts:
            return None
        
        # Trier par poids décroissant
        matched_concepts.sort(key=lambda x: x[1], reverse=True)
        
        # Construire une réponse basée sur les concepts les plus forts
        top = matched_concepts[:3]
        concepts_str = ", ".join(c[0] for c in top)
        avg_weight = sum(c[1] for c in top) / len(top)
        
        if avg_weight > 0.85:
            resonance = "forte"
        elif avg_weight > 0.75:
            resonance = "modérée"
        else:
            resonance = "faible"
        
        text = (
            f"Analyse fréquentielle : résonance {resonance} (poids moyen {avg_weight:.2f}). "
            f"Concepts dominants : {concepts_str}. "
            f"La réponse combine {len(matched_concepts)} concepts en résonance."
        )
        
        return {
            "text": text,
            "confidence": min(avg_weight, 0.85),
            "domain": "frequency_reasoning",
            "method": "frequency_resonance",
            "concepts": [c[0] for c in matched_concepts],
            "avg_weight": round(avg_weight, 3),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "loaded_concepts": len(self.concept_weights),
            "engine": "frequency_resonance_v1",
        }


if __name__ == "__main__":
    fr = FrequencyReasoner()
    tests = [
        "Quelle est la relation entre temps et espace ?",
        "Explique l'harmonie des ondes",
        "Qu'est-ce que la conscience ?",
    ]
    for t in tests:
        r = fr.reason(t)
        print(f"[{r['confidence']:.2f}] {t[:50]:50s} -> {r['text'][:80] if r else 'N/A'}")