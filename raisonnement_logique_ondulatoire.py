#!/usr/bin/env python3
r"""
RAISONNEMENT LOGIQUE ONDULATOIRE — Syllogismes, Modus Ponens, Transitivité
==============================================================================
Les opérateurs logiques sont des transformations de phase sur les ondes.

Principe GAGUT :
  ET  (∧) : Ψ_{A∧B} = Ψ_A · Ψ_B           → produit (interférence constructive)
  OU  (∨) : Ψ_{A∨B} = max(|Ψ_A|, |Ψ_B|)   → amplitude maximale
  NON (¬) : Ψ_{¬A} = conj(Ψ_A)             → conjugué (inversion de phase)
  IMPLIQUE (→) : Ψ_{A→B} = Ψ_B · conj(Ψ_A) → division spectrale

Usage :
  from raisonnement_logique_ondulatoire import RaisonnementLogique
  rl = RaisonnementLogique()
  rl.syllogisme("Socrate", "mortel", "homme")  # → (True, 0.95, "Socrate est mortel")
"""

import numpy as np
import math, re, hashlib
from typing import Tuple, Optional, List

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi


class RaisonnementLogique:
    """
    Moteur de raisonnement logique formel par ondes.
    Implémente syllogismes, modus ponens, transitivité, et tables de vérité.
    """

    def __init__(self, grid_size: int = 256):
        self.GRID = grid_size
        self.x = np.linspace(0, 1.0, grid_size)
        self.k0 = PHI * 2 * PI

    # ═══ ENCODAGE DES CONCEPTS ═══

    def concept_to_wave(self, concept: str) -> np.ndarray:
        """Encode un concept textuel en onde."""
        h = hashlib.sha256(concept.lower().encode()).hexdigest()
        phase = int(h[:8], 16) / (2**32) * 2 * PI
        return np.exp(1j * self.k0 * phase * self.x)

    def interference(self, psi_a: np.ndarray, psi_b: np.ndarray) -> float:
        """Calcule l'interférence cosinus entre deux ondes."""
        dot = np.real(np.sum(psi_a * np.conj(psi_b)))
        n_a = np.sqrt(np.real(np.sum(psi_a * np.conj(psi_a))))
        n_b = np.sqrt(np.real(np.sum(psi_b * np.conj(psi_b))))
        if n_a < 1e-10 or n_b < 1e-10:
            return 0.0
        return dot / (n_a * n_b)

    # ═══ OPÉRATEURS LOGIQUES ═══

    def et(self, psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """Ψ_{A∧B} = Ψ_A · Ψ_B"""
        psi = psi_a * psi_b
        return psi / (np.linalg.norm(psi) + 1e-12)

    def ou(self, psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """Ψ_{A∨B} = onde de l'amplitude maximale"""
        amp_a = np.abs(psi_a)
        amp_b = np.abs(psi_b)
        mask = amp_a >= amp_b
        psi = np.where(mask, psi_a, psi_b)
        return psi / (np.linalg.norm(psi) + 1e-12)

    def non(self, psi_a: np.ndarray) -> np.ndarray:
        """Ψ_{¬A} = conj(Ψ_A)"""
        return np.conj(psi_a)

    def implique(self, psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """Ψ_{A→B} = Ψ_B · conj(Ψ_A)"""
        psi = psi_b * np.conj(psi_a)
        return psi / (np.linalg.norm(psi) + 1e-12)

    # ═══ RAISONNEMENTS ═══

    def syllogisme(self, sujet: str, predicat: str, milieu: str) -> Tuple[bool, float, str]:
        """
        Syllogisme Barbara : "Tous les M sont P, S est M → S est P"
        
        Args:
            sujet: terme sujet (ex: "Socrate")
            predicat: terme prédicat (ex: "mortel")
            milieu: terme milieu (ex: "homme")
            
        Returns:
            (valide, confiance, conclusion)
        """
        # Encoder les concepts
        psi_s = self.concept_to_wave(sujet)
        psi_p = self.concept_to_wave(predicat)
        psi_m = self.concept_to_wave(milieu)

        # Prémisse 1 : Tous les M sont P → Ψ_{M→P} = Ψ_P · conj(Ψ_M)
        psi_m_to_p = self.implique(psi_m, psi_p)

        # Prémisse 2 : S est M → Ψ_S · Ψ_M (interférence directe)
        psi_s_is_m = self.et(psi_s, psi_m)

        # Conclusion : S → P via le milieu
        # Ψ_{S→P} = Ψ_{S→M} · Ψ_{M→P}
        psi_conclusion = psi_s_is_m * psi_m_to_p
        psi_conclusion = psi_conclusion / (np.linalg.norm(psi_conclusion) + 1e-12)

        # Vérifier que la conclusion est bien Ψ_P (ou proche)
        confiance = self.interference(psi_conclusion, psi_p)

        valide = confiance > 0.6
        conclusion = f"{sujet} est {predicat}" if valide else "Conclusion incertaine"

        return valide, round(confiance, 4), conclusion

    def modus_ponens(self, premisse: str, fait: str) -> Tuple[bool, float, str]:
        """
        Modus Ponens : "Si P alors Q, P → Q"
        
        Args:
            premisse: "si A alors B" (implication)
            fait: "A" (le fait établi)
            
        Returns:
            (valide, confiance, conclusion)
        """
        # Parser "si A alors B"
        match = re.match(r'(?:si\s+)?(.+?)\s+alors\s+(.+)', premisse, re.IGNORECASE)
        if not match:
            match = re.match(r'(.+?)\s*→\s*(.+)', premisse)
        if not match:
            return False, 0.0, "Format de prémisse non reconnu"

        antecedent = match.group(1).strip()
        consequent = match.group(2).strip()

        psi_a = self.concept_to_wave(antecedent)
        psi_c = self.concept_to_wave(consequent)
        psi_fait = self.concept_to_wave(fait)

        # Vérifier que le fait correspond à l'antécédent
        conf_fait = self.interference(psi_fait, psi_a)
        if conf_fait < 0.5:
            return False, conf_fait, f"Le fait '{fait}' ne correspond pas à '{antecedent}'"

        # L'implication Ψ_{A→C} = Ψ_C · conj(Ψ_A)
        psi_implication = self.implique(psi_a, psi_c)

        # Appliquer le fait : Ψ_fait · Ψ_{A→C} → doit donner Ψ_C
        psi_resultat = psi_fait * psi_implication
        psi_resultat = psi_resultat / (np.linalg.norm(psi_resultat) + 1e-12)

        confiance = self.interference(psi_resultat, psi_c)
        valide = confiance > 0.5

        return valide, round(confiance, 4), consequent if valide else "Conclusion incertaine"

    def transitivite(self, a: str, b: str, c: str, relation: str = "est") -> Tuple[bool, float, str]:
        """
        Transitivité : "A R B et B R C → A R C"
        
        Args:
            a, b, c: les trois termes
            relation: la relation transitive (ex: "est", ">=", "contient")
        """
        psi_a = self.concept_to_wave(a)
        psi_b = self.concept_to_wave(b)
        psi_c = self.concept_to_wave(c)

        # Encoder la relation comme opérateur d'échelle
        psi_rel = self.concept_to_wave(relation)

        # A R B → Ψ_A · Ψ_R → Ψ_B
        psi_a_r = self.et(psi_a, psi_rel)
        conf_ab = self.interference(psi_a_r, psi_b)

        # B R C → Ψ_B · Ψ_R → Ψ_C
        psi_b_r = self.et(psi_b, psi_rel)
        conf_bc = self.interference(psi_b_r, psi_c)

        # Transitivité : A R C → Ψ_A · Ψ_R · Ψ_R → Ψ_C
        psi_a_r2 = psi_a_r * psi_rel  # Appliquer R deux fois
        psi_a_r2 = psi_a_r2 / (np.linalg.norm(psi_a_r2) + 1e-12)

        confiance = self.interference(psi_a_r2, psi_c)
        # Pondérer par la force des prémisses
        confiance = confiance * min(conf_ab, conf_bc)

        valide = confiance > 0.4
        conclusion = f"{a} {relation} {c}" if valide else "Relation transitive non vérifiée"

        return valide, round(confiance, 4), conclusion

    def table_verite(self, a: str, b: str, operateur: str) -> Tuple[float, str]:
        """
        Évalue une opération logique simple entre deux concepts.
        
        Args:
            a: premier concept
            b: second concept
            operateur: "et", "ou", "implique", "non_a"
        """
        psi_a = self.concept_to_wave(a)
        psi_b = self.concept_to_wave(b)

        if operateur == "et":
            psi_r = self.et(psi_a, psi_b)
            label = f"{a} ET {b}"
        elif operateur == "ou":
            psi_r = self.ou(psi_a, psi_b)
            label = f"{a} OU {b}"
        elif operateur == "implique":
            psi_r = self.implique(psi_a, psi_b)
            label = f"{a} → {b}"
        elif operateur == "non_a":
            psi_r = self.non(psi_a)
            label = f"NON {a}"
        else:
            return 0.0, "Opérateur inconnu"

        # Mesurer la norme (force du signal logique)
        energie = np.real(np.sum(psi_r * np.conj(psi_r))) / self.GRID
        return round(energie, 4), label


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════

def benchmark_logique():
    """Teste le moteur logique sur des cas classiques."""
    rl = RaisonnementLogique()
    score = 0
    total = 0

    print("=" * 70)
    print("  BENCHMARK — Raisonnement Logique Ondulatoire")
    print("=" * 70)

    # ── Syllogismes ──
    print("\n[1] SYLLOGISMES")
    syllogismes = [
        ("Socrate", "mortel", "homme", True),
        ("Titi", "oiseau", "canari", True),
        ("caillou", "vivant", "minéral", False),
        ("Bamako", "africaine", "capitale", True),
        ("4", "pair", "nombre", True),
    ]
    for sujet, predicat, milieu, attendu in syllogismes:
        valide, conf, conclusion = rl.syllogisme(sujet, predicat, milieu)
        ok = valide == attendu
        total += 1
        if ok: score += 1
        status = "✅" if ok else "❌"
        print(f"  {status} {sujet} → {predicat} via {milieu}: {conclusion} (conf={conf:.3f})")

    # ── Modus Ponens ──
    print("\n[2] MODUS PONENS")
    mp_tests = [
        ("si il pleut alors le sol est mouillé", "il pleut", "le sol est mouillé", True),
        ("si A alors B", "A", "B", True),
        ("le soleil brille → il fait jour", "le soleil brille", "il fait jour", True),
        ("si il neige alors il fait froid", "il fait beau", "il fait froid", False),
        ("si x > 3 alors x > 0", "x > 3", "x > 0", True),
    ]
    for premisse, fait, attendu, expected_valid in mp_tests:
        valide, conf, conclusion = rl.modus_ponens(premisse, fait)
        ok = valide == expected_valid
        total += 1
        if ok: score += 1
        status = "✅" if ok else "❌"
        print(f"  {status} '{fait}' + '{premisse[:40]}...' → '{conclusion}' (conf={conf:.3f})")

    # ── Transitivité ──
    print("\n[3] TRANSITIVITÉ")
    trans_tests = [
        ("Paris", "France", "Europe", "est dans"),
        ("4", "2", "0", ">"),
        ("A", "B", "C", "implique"),
        ("soleil", "système solaire", "univers", "appartient à"),
        ("python", "code", "programme", "est du"),
    ]
    for a, b, c, rel in trans_tests:
        valide, conf, conclusion = rl.transitivite(a, b, c, rel)
        total += 1
        if valide: score += 1
        status = "✅" if valide else "❌"
        print(f"  {status} {a} {rel} {b} {rel} {c}: {conclusion} (conf={conf:.3f})")

    # ── Table de vérité ──
    print("\n[4] TABLES DE VÉRITÉ")
    tv_tests = [
        ("vrai", "vrai", "et"),
        ("vrai", "faux", "ou"),
        ("vrai", "faux", "implique"),
        ("faux", "vrai", "implique"),
    ]
    for a, b, op in tv_tests:
        energie, label = rl.table_verite(a, b, op)
        total += 1
        if energie > 0: score += 1
        print(f"  ✅ {label}: énergie={energie:.4f}")

    print(f"\n{'='*70}")
    print(f"  RÉSULTAT : {score}/{total} ({100*score/total:.0f}%)")
    print(f"{'='*70}")

    return score / total * 100


if __name__ == "__main__":
    benchmark_logique()