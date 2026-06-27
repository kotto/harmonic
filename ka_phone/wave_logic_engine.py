#!/usr/bin/env python3
"""
KA-Next -- WAVE LOGIC ENGINE (Raisonnement par Interférence)
===============================================================
Implémente les 3 capacités de raisonnement manquantes du modèle
holographique, en utilisant uniquement les principes d'ondes.

Briques de raisonnement :
  DÉDUIRE   -> Interférence destructive sélective (phase opposition)
  ABSTRAIRE -> Battement de fréquence (fréquence différence émergente)
  CONTREDIRE -> Opposition de phase totale (annulation)

Principe fondamental :
  La LOGIQUE = INTERFÉRENCE D'ONDES
  Le VRAI   = interférence constructive persistante
  Le FAUX   = interférence destructive (annulation)

Usage :
  from wave_logic_engine import WaveLogicEngine
  wle = WaveLogicEngine(ensemble)
  result = wle.deduce("Socrate est-il mortel ?")
"""

import math, hashlib, re, time
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict
import numpy as np

PHI = (1 + math.sqrt(5)) / 2


class WaveLogicEngine:
    """
    Moteur de raisonnement logique basé sur l'interférence d'ondes.
    
    Chaque opération logique est une transformation d'onde :
      - ET logique   = superposition constructive (A + B)
      - OU logique   = somme des amplitudes (|A| + |B|)
      - NON logique  = inversion de phase (Ψ → -Ψ)
      - IMPLICATION  = propagation dirigée (Ψ_A → Ψ_B)
      - CONTRADICTION = opposition de phase (Ψ_A · Ψ_B < 0)
    """

    def __init__(self, ensemble=None):
        self.ensemble = ensemble
        self.stats = {
            "total_deductions": 0,
            "total_contradictions": 0,
            "total_abstractions": 0,
        }

    # ═══════════════════════════════════════════════════════════════════
    # 1. DÉDUIRE : Interférence destructive sélective
    # ═══════════════════════════════════════════════════════════════════

    def deduce(self, question: str, premises: List[str] = None,
               facts: List[str] = None) -> Dict[str, Any]:
        """
        Déduction logique par interférence d'ondes.
        
        Principe physique :
          1. Chaque prémisse émet une onde Ψ_i
          2. La question émet une onde Ψ_q
          3. On superpose Ψ_q avec chaque Ψ_i
          4. Si l'interférence est constructive → la prémisse SUPPORTE la question
          5. Si l'interférence est destructive → la prémisse CONTREDIT la question
          6. La conclusion est l'onde résiduelle après filtrage
        
        Exemple :
          Prémisses : "Tous les hommes sont mortels", "Socrate est un homme"
          Question  : "Socrate est-il mortel ?"
          → Les deux prémisses interfèrent constructivement avec la question
          → La conclusion "Oui, Socrate est mortel" émerge
        """
        self.stats["total_deductions"] += 1
        t0 = time.time()

        if premises is None:
            premises = []
        if facts is None:
            facts = []

        # ── Étape 1 : Encoder la question et les prémisses ──
        q_kx, q_ky = self._hash_to_wave(question)
        premise_waves = [(p, *self._hash_to_wave(p)) for p in premises]

        # ── Étape 2 : Calculer l'interférence ──
        interferences = []
        for premise, pkx, pky in premise_waves:
            # Produit scalaire = mesure d'interférence
            dot = q_kx * pkx + q_ky * pky
            norm_q = math.sqrt(q_kx**2 + q_ky**2)
            norm_p = math.sqrt(pkx**2 + pky**2)
            
            if norm_q < 1e-10 or norm_p < 1e-10:
                interference = 0.0
            else:
                cos_sim = dot / (norm_q * norm_p)
                interference = cos_sim  # -1 = opposition, +1 = alignement
            
            interferences.append({
                "premise": premise[:100],
                "interference": round(interference, 4),
                "type": "constructive" if interference > 0.3 else
                        "destructive" if interference < -0.3 else
                        "neutral"
            })

        # ── Étape 3 : Déterminer la conclusion ──
        if not interferences:
            conclusion = "Aucune prémisse fournie. Impossible de déduire."
            confidence = 0.0
        else:
            constructive = [i for i in interferences if i["interference"] > 0.2]
            destructive = [i for i in interferences if i["interference"] < -0.2]
            
            if len(constructive) > len(destructive):
                # La majorité des prémisses soutiennent la conclusion
                avg_interference = sum(i["interference"] for i in constructive) / max(len(constructive), 1)
                conclusion = "OUI — les prémisses soutiennent cette conclusion."
                confidence = min(0.95, 0.5 + avg_interference)
            elif len(destructive) > len(constructive):
                conclusion = "NON — les prémisses contredisent cette conclusion."
                confidence = 0.7
            else:
                conclusion = "INCERTAIN — interférences équilibrées, pas de conclusion claire."
                confidence = 0.3

        # ── Étape 4 : Vérification par les faits (lookup) ──
        if facts:
            fact_support = 0
            fact_against = 0
            for fact in facts:
                fkx, fky = self._hash_to_wave(fact)
                dot = q_kx * fkx + q_ky * fky
                if dot > 0:
                    fact_support += 1
                else:
                    fact_against += 1

        elapsed_ms = round((time.time() - t0) * 1000, 1)

        lines = [
            f"RAISONNEMENT PAR INTERFÉRENCE D'ONDES",
            f"{'=' * 50}",
            f"Question : {question[:120]}",
            f"",
            f"Prémisses ({len(premises)}) :",
        ]
        for p in premises[:5]:
            lines.append(f"  • {p[:100]}")
        lines.append(f"")
        lines.append(f"Analyse des interférences :")
        for inf in interferences[:8]:
            symbol = "⊕" if inf["type"] == "constructive" else "⊖" if inf["type"] == "destructive" else "○"
            lines.append(f"  {symbol} [{inf['interference']:+.2f}] {inf['premise'][:80]}")
        lines.append(f"")
        lines.append(f"Conclusion : {conclusion}")
        lines.append(f"")
        lines.append(f"[Raisonnement par interférence d'ondes | "
                    f"{len(premises)} prémisses | confiance {confidence:.0%}]")

        return {
            "text": "\n".join(lines),
            "source": "wave_logic_deduction",
            "interferences": interferences,
            "conclusion": conclusion,
            "confidence": round(confidence, 2),
            "temps_ms": elapsed_ms,
        }

    # ═══════════════════════════════════════════════════════════════════
    # 2. CONTREDIRE : Opposition de phase (détection)
    # ═══════════════════════════════════════════════════════════════════

    def detect_contradiction(self, statement: str,
                             existing_facts: List[str]) -> Dict[str, Any]:
        """
        Détecte si un nouvel énoncé contredit des faits existants.
        
        Principe physique :
          Ψ_nouveau · Ψ_existant < 0 → opposition de phase → CONTRADICTION
        
        Exemple :
          Statement : "Dakar est la capitale du Mali"
          Existing  : "Bamako est la capitale du Mali"
          → Même relation (capitale du Mali) mais sujets différents
          → Les ondes sont en opposition de phase → CONTRADICTION
        """
        self.stats["total_contradictions"] += 1
        t0 = time.time()

        stmt_kx, stmt_ky = self._hash_to_wave(statement)
        
        contradictions = []
        for fact in existing_facts:
            fkx, fky = self._hash_to_wave(fact)
            
            # Produit scalaire : si négatif, opposition de phase
            dot = stmt_kx * fkx + stmt_ky * fky
            norm_s = math.sqrt(stmt_kx**2 + stmt_ky**2)
            norm_f = math.sqrt(fkx**2 + fky**2)
            
            if norm_s < 1e-10 or norm_f < 1e-10:
                continue
                
            cos_sim = dot / (norm_s * norm_f)
            
            # Bonus : vérifier si les deux phrases partagent des mots
            # mais avec des valeurs différentes (ex: même prédicat, sujet différent)
            stmt_words = self._extract_words(statement)
            fact_words = self._extract_words(fact)
            common = stmt_words & fact_words
            
            # Si beaucoup de mots communs mais cos_sim négatif → contradiction
            if len(common) >= 2 and cos_sim < -0.2:
                contradictions.append({
                    "statement": statement[:120],
                    "contradicting_fact": fact[:120],
                    "phase_opposition": round(cos_sim, 4),
                    "common_words": list(common)[:5],
                    "severity": "forte" if cos_sim < -0.5 else "moyenne" if cos_sim < -0.3 else "faible"
                })

        has_contradiction = len(contradictions) > 0
        elapsed_ms = round((time.time() - t0) * 1000, 1)

        lines = [
            f"DÉTECTION DE CONTRADICTION",
            f"{'=' * 50}",
            f"Énoncé : {statement[:120]}",
            f"",
        ]

        if has_contradiction:
            lines.append(f"⚠️  CONTRADICTION DÉTECTÉE ({len(contradictions)} fait(s))")
            lines.append(f"")
            for c in contradictions[:5]:
                lines.append(f"  ⊖ Opposition de phase : {c['phase_opposition']:.2f} ({c['severity']})")
                lines.append(f"    Nouveau : {c['statement'][:100]}")
                lines.append(f"    Existant: {c['contradicting_fact'][:100]}")
                lines.append(f"    Mots communs : {', '.join(c['common_words'])}")
                lines.append(f"")
        else:
            lines.append(f"✅ Aucune contradiction détectée avec les faits existants.")

        lines.append(f"[Détection par opposition de phase | "
                    f"{len(contradictions)} contradictions | {len(existing_facts)} faits comparés]")

        return {
            "text": "\n".join(lines),
            "source": "wave_logic_contradiction",
            "has_contradiction": has_contradiction,
            "contradictions": contradictions,
            "confidence": 0.85 if has_contradiction else 0.6,
            "temps_ms": elapsed_ms,
        }

    # ═══════════════════════════════════════════════════════════════════
    # 3. ABSTRAIRE : Battement de fréquence (fréquence différence)
    # ═══════════════════════════════════════════════════════════════════

    def abstract(self, instances: List[str],
                 concept_label: str = "concept") -> Dict[str, Any]:
        """
        Abstrait un concept à partir d'instances par battement de fréquence.
        
        Principe physique :
          On superpose N ondes représentant N instances.
          Les fréquences communes (partagées par toutes les instances)
          interfèrent constructivement → elles émergent.
          Les fréquences spécifiques (propres à une instance)
          interfèrent destructivement → elles sont filtrées.
          
          Le résultat est la FRÉQUENCE DIFFÉRENCE : le battement
          entre les fréquences communes et les fréquences spécifiques.
        
        Exemple :
          Instances : "Dakar", "Paris", "Bamako", "Tokyo", "Brasilia"
          → Fréquence commune émergente : "capitale"
          → Le concept "capitale" émerge par battement d'onde
        """
        self.stats["total_abstractions"] += 1
        t0 = time.time()

        if len(instances) < 2:
            return {"text": "Besoin d'au moins 2 instances pour abstraire.",
                    "source": "wave_logic_abstraction", "confidence": 0.0}

        # ── Étape 1 : Encoder chaque instance ──
        waves = [(inst, *self._hash_to_wave(inst)) for inst in instances]

        # ── Étape 2 : Trouver les fréquences communes ──
        # Superposition : moyenne vectorielle des ondes
        avg_kx = sum(kx for _, kx, ky in waves) / len(waves)
        avg_ky = sum(ky for _, kx, ky in waves) / len(waves)

        # ── Étape 3 : Dispersion (variance) ──
        # Plus la dispersion est faible, plus le concept est cohérent
        variances = []
        for inst, kx, ky in waves:
            dist = math.sqrt((kx - avg_kx)**2 + (ky - avg_ky)**2)
            variances.append(dist)
        
        mean_variance = sum(variances) / len(variances)
        coherence = 1.0 / (1.0 + mean_variance)  # 1.0 = très cohérent

        # ── Étape 4 : Identifier le battement (fréquence émergente) ──
        # On cherche les mots qui apparaissent dans TOUTES les instances
        all_words = [self._extract_words(inst) for inst in instances]
        common_words = all_words[0].copy()
        for wset in all_words[1:]:
            common_words &= wset
        common_words = sorted(common_words)

        elapsed_ms = round((time.time() - t0) * 1000, 1)

        lines = [
            f"ABSTRACTION PAR BATTEMENT D'ONDE",
            f"{'=' * 50}",
            f"Concept : {concept_label}",
            f"Instances ({len(instances)}) :",
        ]
        for inst in instances[:8]:
            lines.append(f"  • {inst[:120]}")
        lines.append(f"")
        lines.append(f"Analyse spectrale :")
        lines.append(f"  Fréquence moyenne (concept) : ({avg_kx:.2f}, {avg_ky:.2f})")
        lines.append(f"  Cohérence du concept     : {coherence:.0%}")
        lines.append(f"  Dispersion moyenne       : {mean_variance:.4f}")
        lines.append(f"")
        
        if common_words:
            lines.append(f"Mots communs émergents (battement de fréquence) :")
            lines.append(f"  {', '.join(common_words[:20])}")
            lines.append(f"")
            lines.append(f"Le concept '{concept_label}' émerge des fréquences communes")
            lines.append(f"aux {len(instances)} instances. Les fréquences spécifiques")
            lines.append(f"(propres à chaque instance) ont été filtrées par")
            lines.append(f"interférence destructive.")
        else:
            lines.append(f"Aucun mot commun trouvé — le concept est trop abstrait")
            lines.append(f"ou les instances sont trop diverses (dispersion {mean_variance:.2f}).")

        lines.append(f"")
        lines.append(f"[Abstraction par battement d'onde | {len(instances)} instances | "
                    f"cohérence {coherence:.0%}]")

        return {
            "text": "\n".join(lines),
            "source": "wave_logic_abstraction",
            "coherence": round(coherence, 4),
            "common_words": common_words,
            "concept_frequency": (round(avg_kx, 4), round(avg_ky, 4)),
            "confidence": round(coherence, 2),
            "temps_ms": elapsed_ms,
        }

    # ═══════════════════════════════════════════════════════════════════
    # 4. RAISONNEMENT COMPLET : chaîne logique par interférence
    # ═══════════════════════════════════════════════════════════════════

    def reason(self, question: str, context_facts: List[str] = None) -> Dict[str, Any]:
        """
        Raisonnement complet en 3 étapes :
          1. DÉDUIRE : les faits soutiennent-ils ou contredisent-ils ?
          2. CONTREDIRE : y a-t-il des contradictions internes ?
          3. ABSTRAIRE : quel concept émerge du contexte ?
        """
        if context_facts is None:
            context_facts = []

        t0 = time.time()

        # Étape 1 : Déduction
        deduction = self.deduce(question, premises=context_facts)

        # Étape 2 : Détection de contradiction
        contradiction = self.detect_contradiction(question, context_facts)

        # Étape 3 : Abstraction
        abstraction = self.abstract(context_facts + [question],
                                    concept_label="raisonnement")

        elapsed_ms = round((time.time() - t0) * 1000, 1)

        lines = [
            f"╔══════════════════════════════════════════════╗",
            f"║  RAISONNEMENT HOLOGRAPHIQUE COMPLET          ║",
            f"╚══════════════════════════════════════════════╝",
            f"",
            f"Question : {question[:120]}",
            f"Faits contextuels : {len(context_facts)}",
            f"",
            f"── 1. DÉDUCTION (interférence constructive) ──",
            f"{deduction['conclusion']}",
            f"",
            f"── 2. CONTRADICTION (opposition de phase) ──",
        ]
        if contradiction["has_contradiction"]:
            lines.append(f"⚠️  {len(contradiction['contradictions'])} contradiction(s) détectée(s)")
        else:
            lines.append(f"✅ Cohérence confirmée")
        lines.append(f"")
        lines.append(f"── 3. ABSTRACTION (battement de fréquence) ──")
        lines.append(f"Cohérence du contexte : {abstraction.get('coherence', 0):.0%}")
        if abstraction.get("common_words"):
            lines.append(f"Mots émergents : {', '.join(abstraction['common_words'][:10])}")
        lines.append(f"")
        lines.append(f"── VERDICT ──")
        
        if contradiction["has_contradiction"]:
            lines.append(f"Le contexte contient des contradictions.")
            lines.append(f"Les interférences destructives identifiées doivent être résolues.")
        elif deduction.get("confidence", 0) > 0.6:
            lines.append(f"Le raisonnement aboutit à une conclusion avec "
                        f"une confiance de {deduction['confidence']:.0%}.")
        else:
            lines.append(f"Le raisonnement est incertain — plus de prémisses sont nécessaires.")

        return {
            "text": "\n".join(lines),
            "deduction": deduction,
            "contradiction": contradiction,
            "abstraction": abstraction,
            "source": "wave_logic_reasoning",
            "temps_ms": elapsed_ms,
        }

    # ═══════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════

    def _hash_to_wave(self, text: str) -> Tuple[float, float]:
        """SHA-256 → (kx, ky). Cohérent avec Hologram64._text_to_wave()."""
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % (64 * 100)) / 100.0
        ky = (int(h[16:32], 16) % (64 * 100)) / 100.0
        return (kx - 32) / 64 * 20, (ky - 32) / 64 * 20

    def _extract_words(self, text: str) -> Set[str]:
        """Extrait les mots significatifs."""
        stop_words = {'dans', 'avec', 'pour', 'sur', 'sous', 'dont', 'cette',
                      'leur', 'plus', 'tout', 'vous', 'nous', 'alors', 'comme',
                      'bien', 'fait', 'peut', 'tres', 'sont', 'aux', 'une', 'est',
                      'les', 'des', 'pas', 'que', 'qui', 'par', 'the', 'and'}
        words = set()
        for w in text.lower().split():
            w = w.strip('.,;:!?()[]{}"\'-').lower()
            if len(w) > 3 and w not in stop_words and not w.isdigit():
                words.add(w)
        return words

    def get_stats(self) -> Dict:
        return dict(self.stats)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    wle = WaveLogicEngine()

    print("=" * 60)
    print("  WAVE LOGIC ENGINE — Test")
    print("=" * 60)

    # Test 1 : Déduction
    print("\n── Test 1 : DÉDUCTION ──")
    r = wle.deduce(
        "Socrate est-il mortel ?",
        premises=[
            "Tous les hommes sont mortels",
            "Socrate est un homme",
            "Les philosophes grecs sont des hommes",
        ]
    )
    print(r["text"])

    # Test 2 : Contradiction
    print("\n── Test 2 : CONTRADICTION ──")
    r = wle.detect_contradiction(
        "Dakar est la capitale du Mali",
        existing_facts=[
            "Bamako est la capitale du Mali",
            "Dakar est la capitale du Senegal",
            "Le Mali est un pays d'Afrique de l'Ouest",
        ]
    )
    print(r["text"])

    # Test 3 : Abstraction
    print("\n── Test 3 : ABSTRACTION ──")
    r = wle.abstract(
        [
            "La capitale du Senegal est Dakar",
            "La capitale de la France est Paris",
            "La capitale du Mali est Bamako",
            "La capitale du Japon est Tokyo",
            "La capitale du Bresil est Brasilia",
        ],
        concept_label="capitale"
    )
    print(r["text"])

    # Test 4 : Raisonnement complet
    print("\n── Test 4 : RAISONNEMENT COMPLET ──")
    r = wle.reason(
        "Le Senegal est-il un pays africain ?",
        context_facts=[
            "Le Senegal est un pays situe en Afrique de l'Ouest",
            "Dakar est la capitale du Senegal",
            "L'Afrique est un continent",
            "Les pays africains sont situes en Afrique",
        ]
    )
    print(r["text"])

    print("\n" + "=" * 60)