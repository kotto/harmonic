"""
Counterfactual Reasoner — Raisonnement Holographique par Perturbation
======================================================================
Répond aux questions « que se passerait-il si... » en appliquant une
PERTURBATION au champ d'onde de la réalité et en observant les faits
les plus affectés.

Principe ondulatoire :
  Soit Ψ_actuel le vecteur d'onde représentant l'état actuel d'un concept.
  Pour répondre à « que se passerait-il si X changeait ? » :
  
    1. Ψ_perturbé = Ψ_actuel - v_X_actuel + v_X_modifié
    2. Pour chaque fait F dans la KB, calculer l'impact :
       impact(F) = |Re(⟨Ψ_perturbé | ψ_F⟩) - Re(⟨Ψ_actuel | ψ_F⟩)|
    3. Les faits avec le plus grand impact sont les CONSÉQUENCES du changement
    4. Décrire ces conséquences en langage naturel

C'est une opération purement géométrique — aucun mécanisme d'inférence
supplémentaire n'est nécessaire.

Usage :
  from counterfactual_reasoner import CounterfactualReasoner
  cr = CounterfactualReasoner(encoder, knowledge_base)
  reponse = cr.ask("que se passerait-il si la gravité était 10 fois plus forte ?")
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
class CounterfactualResult:
    """Résultat d'un raisonnement contrefactuel."""
    concept_modifie: str         # ce qui a été changé
    etat_initial: str            # description de l'état initial
    etat_modifie: str            # description de l'état modifié
    consequences: List[Tuple[str, float]]  # (description, impact) trié par impact décroissant
    synthese: str                # réponse en langage naturel


# Préfixes de questions contrefactuelles
_CF_PREFIXES_FR = [
    'que se passerait-il si', 'que se passerait il si',
    'qu arriverait-il si', 'qu arriverait il si',
    'et si', 'que ferait', 'comment serait',
    'imagine si', 'imaginons si', 'supposons que',
    'dans l hypothèse où', 'dans l hypothese ou',
    'si on changeait', 'si on modifiait',
    'si x etait', 'si x était',
    'que deviendrait', 'comment evoluerait',
]

_CF_PREFIXES_EN = [
    'what would happen if', 'what if',
    'how would', 'suppose', 'imagine if',
    'what would change if',
    'in a world where',
]


# ═══════════════════════════════════════════════════════════════════════════════
# RAISONNEUR CONTREFACTUEL
# ═══════════════════════════════════════════════════════════════════════════════

class CounterfactualReasoner:
    """
    Raisonne sur des scénarios hypothétiques en perturbant le champ
    d'onde et en observant les conséquences.
    """

    def __init__(self, encoder=None, knowledge_base=None):
        self._encoder = encoder
        self.kb = knowledge_base or []

    def _encode(self, text: str) -> Optional[np.ndarray]:
        if self._encoder is None:
            return None
        try:
            return self._encoder.encode_query(text)
        except Exception:
            return None

    def _similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Similarité cosinus entre deux vecteurs d'onde."""
        sim = float(np.real(np.dot(v1, np.conj(v2))))
        D = len(v1)
        return max(0.0, min(1.0, (sim / np.sqrt(D) + 1.0) / 2.0))

    def _parse_counterfactual(self, question: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse une question contrefactuelle.

        Ex: "que se passerait-il si la gravité était 10 fois plus forte ?"
          → (concept='gravite', propriete='force', modification='10 fois plus forte')

        Returns:
            (concept, propriete, modification) ou None si pas contrefactuel
        """
        q = question.lower().strip()

        # Détecter si c'est une question contrefactuelle
        is_cf = False
        for prefix in _CF_PREFIXES_FR + _CF_PREFIXES_EN:
            if q.startswith(prefix):
                is_cf = True
                q = q[len(prefix):].strip()
                break
        if not is_cf and not q.startswith('si '):
            return None

        # Nettoyer
        q = q.strip('?.,!;: ')

        # Patterns : "X était/est Y" ou "X avait/avait plus de Y" ou "X n'existait pas"
        patterns = [
            (r"(.+?)\s+(?:était|est|devenait|devient)\s+(.+)", 'etat'),
            (r"(.+?)\s+(?:avait|a)\s+(.+)", 'possession'),
            (r"(.+?)\s+n[' ]existait\s+pas", 'absence'),
            (r"(.+?)\s+n[' ]existait\s+plus", 'absence'),
            (r"(.+?)\s+(?:changeait|changeait de|modifiait)\s+(.+)", 'changement'),
        ]

        for pattern, ptype in patterns:
            m = re.match(pattern, q)
            if m:
                concept = m.group(1).strip()
                modif = m.group(2).strip() if ptype != 'absence' else "n'existait pas"
                propriete = ptype
                return (concept, propriete, modif)

        # Fallback : prendre les premiers mots comme concept
        words = q.split()
        if len(words) >= 2:
            return (words[0], 'etat', ' '.join(words[1:]))

        return None

    def reason(self, question: str,
               knowledge_base: List[Tuple] = None,
               max_consequences: int = 5) -> Optional[CounterfactualResult]:
        """
        Raisonne sur un scénario contrefactuel.

        Args:
            question: question hypothétique
            knowledge_base: KB (utilise self.kb si None)
            max_consequences: nombre max de conséquences à lister

        Returns:
            CounterfactualResult ou None si pas contrefactuel ou pas de données
        """
        kb = knowledge_base or self.kb
        if not kb or not self._encoder:
            return None

        parsed = self._parse_counterfactual(question)
        if parsed is None:
            return None

        concept, propriete, modification = parsed

        # 1. Trouver l'état actuel du concept dans la KB
        current_facts = []
        for s, r, o, sec in kb:
            if concept in s.lower() or concept in o.lower():
                current_facts.append((s, r, o, sec))

        if not current_facts:
            return None

        # 2. Construire le vecteur de perturbation
        # Ψ_perturbé = somme_des_vecteurs_des_faits_actuels + δ
        # où δ est le vecteur de la modification
        v_actuel = self._encode(' '.join([f"{s} {r} {o}" for s, r, o, _ in current_facts[:5]]))
        v_modification = self._encode(modification)
        v_concept = self._encode(concept)

        if v_actuel is None:
            return None

        # Perturbation : soustraire le concept actuel, ajouter la modification
        if v_modification is not None and v_concept is not None:
            v_perturbe = v_actuel - 0.3 * v_concept + 0.5 * v_modification
        else:
            v_perturbe = v_actuel

        # Normaliser
        norm = np.sqrt(np.real(np.dot(v_perturbe, np.conj(v_perturbe))))
        if norm > 0:
            v_perturbe = v_perturbe / norm

        # 3. Calculer l'impact sur chaque fait de la KB
        impacts = []
        seen = set()
        for s, r, o, sec in kb:
            # Éviter de ré-évaluer les faits déjà liés au concept
            if (s, r, o) in seen:
                continue
            seen.add((s, r, o))

            v_fact = self._encode(f"{s} {r} {o}")
            if v_fact is None:
                continue

            # Impact = différence de similarité avant/après perturbation
            sim_before = self._similarity(v_actuel, v_fact)
            sim_after = self._similarity(v_perturbe, v_fact)
            impact = abs(sim_after - sim_before)

            if impact > 0.01:  # seuil minimal
                desc = f"{s} {r} {o}"
                impacts.append((desc, impact))

        # 4. Trier par impact décroissant
        impacts.sort(key=lambda x: -x[1])
        top_impacts = impacts[:max_consequences]

        # 5. Synthétiser la réponse
        etat_initial = f"{concept} est actuellement décrit comme : " + \
                       '; '.join([f"{s} {r} {o}" for s, r, o, _ in current_facts[:3]])

        etat_modifie = f"Dans le scénario où {concept} {modification}"

        synthese = self._synthesize(concept, modification, current_facts, top_impacts)

        return CounterfactualResult(
            concept_modifie=concept,
            etat_initial=etat_initial,
            etat_modifie=etat_modifie,
            consequences=top_impacts,
            synthese=synthese,
        )

    def _synthesize(self, concept: str, modification: str,
                    current_facts: list, consequences: list) -> str:
        """Synthétise une réponse naturelle au scénario contrefactuel."""

        if not consequences:
            return (f"Si {concept} {modification}, les conséquences "
                    f"seraient difficiles à prédire avec les connaissances "
                    f"actuelles. Le système n'a pas détecté de faits "
                    f"suffisamment impactés par ce changement.")

        # Intro
        parts = [f"Si {concept} {modification}, voici ce qui changerait :"]

        # Conséquences principales (top 3)
        for i, (desc, impact) in enumerate(consequences[:3], 1):
            intensite = "fortement" if impact > 0.1 else ("modérément" if impact > 0.03 else "légèrement")
            parts.append(f"{i}. Le fait « {desc} » serait {intensite} affecté.")

        # Conclusion
        if len(consequences) > 3:
            parts.append(f"D'autres aspects seraient également touchés "
                        f"({len(consequences) - 3} conséquences supplémentaires "
                        f"détectées).")

        # Ajouter une mise en garde
        parts.append(
            f"\n⚠️ Ce raisonnement est basé sur la structure actuelle "
            f"de la base de connaissance et sur des perturbations "
            f"géométriques du champ d'onde. Il s'agit d'une exploration "
            f"hypothétique, pas d'une prédiction certaine."
        )

        return ' '.join(parts)

    def ask(self, question: str,
            knowledge_base: List[Tuple] = None) -> Optional[str]:
        """
        Interface simple : retourne la réponse contrefactuelle
        ou None si la question n'est pas contrefactuelle.
        """
        result = self.reason(question, knowledge_base)
        if result is None:
            return None
        return result.synthese


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    from holographic_encoder import HolographicEncoder

    print("=" * 60)
    print("COUNTERFACTUAL REASONER — Démo")
    print("=" * 60)

    # KB de test
    kb = [
        ("gravite", "est", "une force d attraction", "PHYSIQUE_FOND"),
        ("gravite", "maintient", "les planetes en orbite", "PHYSIQUE_FOND"),
        ("gravite", "maintient", "l atmosphere terrestre", "PHYSIQUE_FOND"),
        ("gravite", "cause", "la formation des etoiles", "PHYSIQUE_FOND"),
        ("soleil", "est", "une etoile", "ASTRONOMIE"),
        ("soleil", "fournit", "de la lumiere", "ASTRONOMIE"),
        ("soleil", "fournit", "de la chaleur", "ASTRONOMIE"),
        ("plantes", "utilisent", "la photosynthese", "BIOLOGIE"),
        ("photosynthese", "necessite", "la lumiere du soleil", "BIOLOGIE"),
        ("oxygene", "est produit par", "la photosynthese", "BIOLOGIE"),
        ("atmosphere", "contient", "de l oxygene", "BIOLOGIE"),
        ("terre", "a une", "atmosphere", "GEOGRAPHIE"),
        ("etres humains", "respirent", "l oxygene", "BIOLOGIE"),
    ]

    encoder = HolographicEncoder(dim=128)

    cr = CounterfactualReasoner(encoder, kb)

    questions = [
        "que se passerait-il si la gravite etait 10 fois plus forte ?",
        "que se passerait-il si le soleil n existait pas ?",
        "et si la photosynthese n existait pas ?",
    ]

    for q in questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        r = cr.ask(q)
        if r:
            print(f"R: {r}")
        else:
            print("R: (pas une question contrefactuelle ou pas assez de données)")


if __name__ == '__main__':
    demo()
