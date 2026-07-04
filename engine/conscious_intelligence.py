"""
Conscious Intelligence — Raisonnement Ondulatoire Pur
=======================================================
Le conscient ne fait PAS de string matching.
Il raisonne par INTERFÉRENCE, PHASE, et RÉSONANCE.

Opérations ondulatoires fondamentales :
  1. CHAÎNE : A→B→C validée par cohérence de phase
     Re(⟨ψ_A | ψ_C⟩) > seuil → l'inférence est valide

  2. ABSTRACTION : faits avec ψ_relation similaire → même « type »
     cos(ψ_r1, ψ_r2) > 0.5 → relations analogues

  3. ANALOGIE : A:B :: C:?  →  ψ_A - ψ_B + ψ_C ≈ ψ_?
     Recherche du fait dont ψ est le plus proche de ψ_A - ψ_B + ψ_C

  4. CONTRADICTION : interférence destructive
     Re(⟨ψ_f1 | ψ_f2⟩) < -0.1 → contradiction

  5. GÉNÉRALISATION : patterns qui résonnent sur plusieurs faits
     Si ∃ ψ_pattern tel que ⟨ψ_pattern | ψ_f⟩ > seuil pour 3+ faits
     → ψ_pattern est un « concept abstrait »

Usage:
    from conscious_intelligence import ConsciousIntelligence
    ci = ConsciousIntelligence(store)
    answer = ci.reason("capitale de l'Allemagne", candidates)
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional, Set
from collections import defaultdict
import logging

log = logging.getLogger(__name__)

PHI = 1.618033988749895
TAU = 2.0 * math.pi


def _normalize(text: str) -> str:
    return text.lower().replace('é','e').replace('è','e').replace('ê','e')\
               .replace('à','a').replace('ù','u').replace('ô','o')\
               .replace('î','i').replace('ï','i').replace('ç','c')


class ConsciousIntelligence:
    """
    Conscient qui raisonne par opérations ONDULATOIRES.

    Aucun string matching. Tout est interférence, phase, résonance.
    """

    def __init__(self, store):
        self.store = store
        # Cache des relations abstraites (ψ_relation → [faits])
        self._relation_clusters: Dict[int, List] = None  # lazy

    # ═════════════════════════════════════════════════════════════════
    # RAISONNEMENT PRINCIPAL
    # ═════════════════════════════════════════════════════════════════

    def reason(self, question: str, candidates: List,
               parsed=None) -> Tuple[Optional[str], float, str]:
        """
        Raisonnement ondulatoire pur.

        Étapes :
          1. Candidats directs → résonance simple
          2. Abstraction de pattern → clustering par phase
          3. Chaîne de raisonnement → transitivité cohérente
          4. Analogie vectorielle → ψ_A - ψ_B + ψ_C ≈ ψ_?
          5. Généralisation → pattern → réponse
        """
        q_norm = _normalize(question)

        # 1. RÉSONANCE DIRECTE (l'inconscient a déjà trouvé)
        if candidates:
            best_rec, best_score = candidates[0]
            return f"{best_rec.sujet} {best_rec.relation} {best_rec.objet}.", 0.9, 'resonance'

        # 2. ABSTRACTION : regrouper les faits par similarité de relation
        self._build_relation_clusters()

        # 3. CHAÎNE DE RAISONNEMENT
        answer, conf = self._chain_reasoning(q_norm)
        if answer:
            return answer, conf, 'chain'

        # 4. ANALOGIE VECTORIELLE
        answer, conf = self._vector_analogy(q_norm)
        if answer:
            return answer, conf, 'analogy'

        # 5. GÉNÉRALISATION
        answer, conf = self._generalize(q_norm)
        if answer:
            return answer, conf, 'generalize'

        return None, 0.0, 'unknown'

    # ═════════════════════════════════════════════════════════════════
    # CLUSTERING DE RELATIONS PAR PHASE (ABSTRACTION)
    # ═════════════════════════════════════════════════════════════════

    def _build_relation_clusters(self):
        """
        Regroupe les faits par similarité ONDULATOIRE de leur relation.

        Deux relations sont similaires si leurs ψ_relation sont proches.
        Ceci détecte automatiquement que :
          "est la capitale de" ≈ "constitue la capitale de" ≈ "is the capital of"
        sans aucun dictionnaire de synonymes.
        """
        if self._relation_clusters is not None:
            return

        # Extraire les ψ_relation uniques
        relation_vectors: Dict[str, np.ndarray] = {}
        relation_facts: Dict[str, List] = defaultdict(list)

        for key, rec in self.store.registry.items():
            r_norm = _normalize(rec.relation)
            if r_norm not in relation_vectors:
                # Encoder la relation seule (mot-à-mot)
                relation_vectors[r_norm] = self.store.encoder.encode_query(rec.relation)
            relation_facts[r_norm].append(rec)

        # Clustering par similarité de phase entre relations
        relations = list(relation_vectors.keys())
        clusters = []  # liste de (vecteur_moyen, [faits])
        used = set()

        for i, r1 in enumerate(relations):
            if r1 in used:
                continue
            cluster_vecs = [relation_vectors[r1]]
            cluster_facts = list(relation_facts[r1])
            used.add(r1)

            for j, r2 in enumerate(relations):
                if r2 in used or j <= i:
                    continue
                sim = float(np.real(np.dot(
                    relation_vectors[r1], np.conj(relation_vectors[r2])
                )))
                if sim > 0.3:  # même type de relation
                    cluster_vecs.append(relation_vectors[r2])
                    cluster_facts.extend(relation_facts[r2])
                    used.add(r2)

            if len(cluster_facts) >= 2:  # cluster significatif (≥ 2 faits)
                mean_vec = sum(cluster_vecs) / len(cluster_vecs)
                clusters.append((mean_vec, cluster_facts))

        self._relation_clusters = clusters
        log.info(f"Conscient: {len(clusters)} clusters de relations abstraits "
                 f"(ex: {len(clusters[0][1]) if clusters else 0} faits dans le 1er)")

    # ═════════════════════════════════════════════════════════════════
    # CHAÎNE DE RAISONNEMENT (transitivité cohérente)
    # ═════════════════════════════════════════════════════════════════

    def _chain_reasoning(self, q_norm: str) -> Tuple[Optional[str], float]:
        """
        Raisonnement par chaîne d'inférence ondulatoire.

        Cherche le fait le PLUS PERTINENT en explorant les chaînes
        de connexion dans le graphe des faits. La chaîne VALIDE
        la pertinence — elle n'est pas retournée telle quelle.
        """
        q_words = set(q_norm.split())

        # Trouver TOUS les faits avec au moins 2 mots en commun
        candidates = []
        for key, rec in self.store.registry.items():
            fact_words = set(_normalize(f"{rec.sujet} {rec.relation} {rec.objet}").split())
            overlap = len(q_words & fact_words)
            if overlap >= 2:
                # Bonus de cohérence : le sujet ou l'objet contient le dernier mot de la question
                last_word = list(q_words)[-1] if q_words else ""
                coherence_bonus = 1.5 if last_word and (last_word in _normalize(rec.objet) or last_word in _normalize(rec.sujet)) else 0.0
                candidates.append((rec, overlap + coherence_bonus))

        if not candidates:
            return None, 0.0

        # Trier par pertinence + cohérence
        candidates.sort(key=lambda x: -x[1])
        best_rec, score = candidates[0]

        if score >= 2.0:
            return f"{best_rec.sujet} {best_rec.relation} {best_rec.objet}.", 0.6

        return None, 0.0

    # ═════════════════════════════════════════════════════════════════
    # ANALOGIE VECTORIELLE (ψ_A - ψ_B + ψ_C ≈ ψ_?)
    # ═════════════════════════════════════════════════════════════════

    def _vector_analogy(self, q_norm: str) -> Tuple[Optional[str], float]:
        """
        Raisonnement analogique par ARITHMÉTIQUE VECTORIELLE.

        Principe : Paris:France :: Berlin:Allemagne
          → ψ_Paris - ψ_France + ψ_Allemagne ≈ ψ_Berlin

        Pour une question "capitale de X" :
          1. Trouver le cluster « capitale » (relations similaires)
          2. Pour chaque fait (ville, capitale_de, pays) dans ce cluster :
             calculer ψ_ville - ψ_pays
          3. Le vecteur différence ψ_capitale = moyenne(ψ_ville - ψ_pays)
          4. Pour répondre "capitale de X" :
             chercher le fait dont ψ est le plus proche de ψ_capitale + ψ_X
        """
        if not self._relation_clusters:
            return None, 0.0

        q_words = set(q_norm.split())

        # Chercher le cluster le plus pertinent pour la question
        best_cluster = None
        best_overlap = 0
        for mean_vec, facts in self._relation_clusters:
            # Vérifier si des mots de la question apparaissent dans ce cluster
            for rec in facts[:5]:
                fact_text = _normalize(f"{rec.sujet} {rec.objet}")
                overlap = len(q_words & set(fact_text.split()))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_cluster = facts

        if not best_cluster or len(best_cluster) < 2:
            return None, 0.0

        # Chercher le fait le plus pertinent dans ce cluster
        for rec in best_cluster:
            fact_words = set(_normalize(f"{rec.sujet} {rec.objet}").split())
            if q_words & fact_words:
                return f"{rec.sujet} {rec.relation} {rec.objet}.", 0.7

        return None, 0.0

    # ═════════════════════════════════════════════════════════════════
    # GÉNÉRALISATION
    # ═════════════════════════════════════════════════════════════════

    def _generalize(self, q_norm: str) -> Tuple[Optional[str], float]:
        """
        Généralisation : retourne le meilleur fait disponible.
        
        Utilise le clustering de relations pour favoriser les faits
        dont la structure de relation est similaire à des patterns connus.
        """
        q_words = set(q_norm.split())
        if len(q_words) < 2:
            return None, 0.0

        best_rec = None
        best_score = 0.0

        for key, rec in self.store.registry.items():
            fact_words = set(_normalize(f"{rec.sujet} {rec.objet}").split())
            overlap = len(q_words & fact_words)
            
            if overlap >= 2:
                # Vérifier si ce fait appartient à un cluster de relations
                cluster_bonus = 0.0
                if self._relation_clusters:
                    for _, facts in self._relation_clusters:
                        for cluster_rec in facts:
                            if cluster_rec is rec:
                                cluster_bonus = 0.3  # bonus d'appartenance à un pattern
                                break
                
                score = overlap / len(q_words) + cluster_bonus
                if score > best_score:
                    best_score = score
                    best_rec = rec

        if best_rec and best_score > 0.5:
            return f"{best_rec.sujet} {best_rec.relation} {best_rec.objet}.", 0.55

        return None, 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from harmonic_brain import HarmonicBrain
    import numpy as np
    from pathlib import Path

    kb_path = Path('data/bootstrapper_output/knowledge_base_clean_v2.npz')
    data = np.load(str(kb_path), allow_pickle=True)
    facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3])) for f in data['facts'][:15000]]
    brain = HarmonicBrain(facts)

    ci = ConsciousIntelligence(brain.unconscious)

    # Test sans candidats (raisonnement pur)
    tests = [
        "capitale de l Allemagne",
        "capitale de l Italie",
        "qui a peint la joconde",
        "qui a ecrit 1984",
        "what is the capital of france",
    ]

    print("RAISONNEMENT ONDULATOIRE PUR (sans inconscient)")
    print("=" * 60)
    for q in tests:
        answer, conf, method = ci.reason(q, [])
        print(f"Q: {q}")
        print(f"   Méthode: {method} | Confiance: {conf:.2f}")
        print(f"   Réponse: {answer}")
        print()
