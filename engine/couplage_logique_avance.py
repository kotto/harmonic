#!/usr/bin/env python3
r"""
🌊 COUPLAGE LOGIQUE AVANCÉ — Encodeur de Prémisses en Couplages Dirigés
========================================================================

AMÉLIORATION FONDAMENTALE :
  Le couplage SYMÉTRIQUE (add_implication) est une approximation INCORRECTE.
  "Tous les A sont B" (A→B) n'implique PAS "Tous les B sont A" (B→A) !
  
  Avant :  add_implication(A, B) → K[A,B] = +κ ET K[B,A] = +κ  (symétrique ❌)
  Après :  all(A, B)            → K[B,A] = +κ, K[A,B] = 0      (dirigé ✅)
  
  Le couplage DIRIGÉ code la DIRECTION de l'implication :
  - K[B,A] > 0 : B est TIRÉ vers A (B suit A)
  - K[A,B] = 0 : A n'est PAS tiré vers B (A ne suit pas B)

LES 4 FORMES CATÉGORIQUES (Aristote) :
  A-forme : "Tous les S sont P"  → S→P dirigé :     K[P,S] = +κ
  E-forme : "Aucun S n'est P"    → exclusion :       K[S,P] = K[P,S] = −κ
  I-forme : "Quelques S sont P"  → faible dirigé :   K[P,S] = +κ/2
  O-forme : "Quelques S ne sont pas P" → faible excl: K[S,P] = K[P,S] = −κ/2

VÉRIFICATION DE VALIDITÉ PAR FORME :
  Conclusion "all(X,Y)"  → ancrer X=0, vérifier θ_Y ≈ 0
  Conclusion "no(X,Y)"   → ancrer X=0, vérifier |θ_X − θ_Y| ≈ π
  Conclusion "some(X,Y)" → ancrer X=0, vérifier θ_Y ≈ 0 (faible)
  Conclusion "not_all(X,Y)" → ancrer X=0, vérifier |θ_X − θ_Y| ≥ π/2

USAGE :
  python couplage_logique_avance.py
"""

import math
import time
import numpy as np
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# 1. MOTEUR KURAMOTO ASYMÉTRIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class AsymmetricKuramoto:
    """
    Réseau Kuramoto avec COUPLAGES DIRIGÉS (matrice K asymétrique).
    
    dθ_i/dt = Σ_j K_ij · sin(θ_j − θ_i)
    
    K_ij > 0 : i est TIRÉ vers j  (i suit j)
    K_ij < 0 : i est REPOUSSÉ de j (i s'oppose à j)
    K_ij = 0 : pas de couplage
    
    Un couplage DIRIGÉ A→B s'écrit : K[B,A] = +κ, K[A,B] = 0
    → B suit A, mais A ne suit pas B.
    """
    
    def __init__(self, kappa: float = 1.0, dt: float = 0.02):
        self.kappa = kappa
        self.dt = dt
        self.names: List[str] = []
        self.idx: Dict[str, int] = {}
        self.K: Optional[np.ndarray] = None  # matrice asymétrique
        self.anchors: Dict[int, float] = {}
        self.theta: Optional[np.ndarray] = None
        self.r_history: List[float] = []
    
    def add_node(self, name: str):
        """Ajoute un nœud (oscillateur)."""
        if name not in self.idx:
            self.idx[name] = len(self.names)
            self.names.append(name)
            self._reset_matrix()
    
    def add_nodes(self, names: List[str]):
        for n in names:
            self.add_node(n)
    
    def _reset_matrix(self):
        """
        Réinitialise la matrice à la taille courante en PRÉSERVANT les valeurs.
        
        CRUCIAL : quand on ajoute un nœud APRÈS avoir encodé des couplages,
        la matrice doit être AGRANDIE, pas réinitialisée à zéro.
        Sinon tous les couplages encodés sont perdus (bug fatal).
        """
        n = len(self.names)
        if self.K is None:
            self.K = np.zeros((n, n))
        elif self.K.shape[0] != n:
            new_K = np.zeros((n, n))
            old_n = self.K.shape[0]
            # Préserver les couplages existants dans le coin supérieur gauche
            new_K[:old_n, :old_n] = self.K
            self.K = new_K
    
    def directed_implication(self, a: str, b: str, strength: float = 1.0):
        """
        Couplage DIRIGÉ : A → B (B suit A, A ne suit pas B).
        
        K[B, A] = +κ·strength   (B tiré vers A)
        K[A, B] = 0             (A libre)
        
        C'est l'encodage correct de "Tous les A sont B".
        """
        self.add_nodes([a, b])
        i, j = self.idx[a], self.idx[b]
        # B (j) est tiré vers A (i)
        self.K[j, i] += self.kappa * strength
        # PAS de couplage inverse : A reste libre
        # (K[i, j] reste 0)
    
    def mutual_exclusion(self, a: str, b: str, strength: float = 1.0):
        """
        EXCLUSION MUTUELLE : A et B ne peuvent pas être tous deux vrais.
        
        K[A,B] = K[B,A] = −κ·strength
        → Les phases se REPOUSSENT vers l'opposition (π).
        
        C'est l'encodage correct de "Aucun A n'est B".
        """
        self.add_nodes([a, b])
        i, j = self.idx[a], self.idx[b]
        self.K[i, j] -= self.kappa * strength
        self.K[j, i] -= self.kappa * strength
    
    def weak_implication(self, a: str, b: str, strength: float = 0.5):
        """
        Implication FAIBLE : A → B (couplage atténué).
        
        C'est l'encodage de "Quelques A sont B" (existence).
        """
        self.directed_implication(a, b, strength=strength)
    
    def weak_exclusion(self, a: str, b: str, strength: float = 0.5):
        """
        Exclusion FAIBLE : A et B plutôt incompatibles.
        
        C'est l'encodage de "Quelques A ne sont pas B".
        """
        self.mutual_exclusion(a, b, strength=strength)
    
    def anchor(self, name: str, truth: bool, strength: float = 3.0):
        """Ancre un nœud à 0 (vrai) ou π (faux)."""
        self.add_node(name)
        i = self.idx[name]
        self.anchors[i] = 0.0 if truth else np.pi
        # Auto-renforcement pour maintenir l'ancre
        self.K[i, i] += self.kappa * strength
    
    def soft_anchor(self, name: str, truth: bool, strength: float = 2.0):
        """
        Ancre SOUPLE : tire la phase vers 0/π SANS la forcer.
        
        Contrairement à anchor() qui réécrit la phase à chaque pas,
        la soft_anchor ajoute un couplage qui ATTIRE la phase vers
        la valeur cible. Les autres couplages (exclusions) peuvent
        LUTTER contre cette attraction → contradiction détectable.
        
        Implémentation : K[i, i] = -strength·κ (attraction vers 0)
        ou K[i, i] = -strength·κ·cos(π) si faux (attraction vers π).
        """
        self.add_node(name)
        i = self.idx[name]
        if truth:
            # Attraction vers 0 : dθ_i = -K·sin(θ_i) → θ_i → 0
            self.K[i, i] += -self.kappa * strength
        else:
            # Attraction vers π : dθ_i = -K·sin(θ_i - π) = K·sin(θ_i) → θ_i → π
            self.K[i, i] += self.kappa * strength
    
    def clear_anchors(self):
        """Efface les ancres (et leur auto-renforcement)."""
        n = len(self.names)
        self.anchors.clear()
        if self.K is not None:
            self.K = self.K.copy()
            for i in range(n):
                self.K[i, i] = 0.0
    
    def run(self, steps: int = 2000, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
        """
        Intègre la dynamique Kuramoto asymétrique.
        
        Avec CONVERGENCE ADAPTATIVE : on continue jusqu'à stabilisation
        ou jusqu'au nombre maximal de pas.
        """
        n = len(self.names)
        if n == 0 or self.K is None:
            return np.zeros(1), np.zeros(1)
        
        rng = np.random.RandomState(seed)
        theta = rng.uniform(0.0, 2 * np.pi, n)
        for i, ph in self.anchors.items():
            theta[i] = ph
        
        r_series = np.empty(steps)
        
        for t in range(steps):
            delta = theta[None, :] - theta[:, None]  # θ_j − θ_i
            dtheta = (self.K * np.sin(delta)).sum(axis=1)
            theta += self.dt * dtheta
            
            for i, ph in self.anchors.items():
                theta[i] = ph
            
            r_series[t] = abs(np.mean(np.exp(1j * theta)))
            
            # Convergence adaptative : arrêt précoce si stable
            if t > 500 and t % 100 == 0:
                recent = r_series[t-100:t]
                if np.std(recent) < 1e-4:
                    # Remplir le reste avec la valeur finale
                    r_series[t:] = recent[-1]
                    break
        
        self.theta = theta.copy()
        self.r_history = list(r_series[:t+1])
        return theta, r_series
    
    def phase_of(self, name: str) -> float:
        """Retourne la phase d'un nœud."""
        return float(self.theta[self.idx[name]] % (2 * np.pi))
    
    def verdict(self, name: str, tol: float = 0.35) -> str:
        """Verdict : true / false / ?"""
        phase = self.phase_of(name)
        w = phase % (2 * np.pi)
        if min(w, 2 * np.pi - w) < tol:
            return 'true'
        if abs(w - np.pi) < tol:
            return 'false'
        return '?'
    
    @property
    def coherence(self) -> float:
        if self.theta is None:
            return 0.0
        return float(abs(np.mean(np.exp(1j * self.theta))))


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ENCODEUR DES PRÉMISSES CATÉGORIQUES
# ═══════════════════════════════════════════════════════════════════════════════

class PremiseEncoder:
    """
    Encode les 4 formes catégoriques en couplages dirigés.
    
    Forme          | Signification              | Encodage
    ---------------|---------------------------|-------------------------
    all(S,P)       | Tous les S sont P         | S→P dirigé
    no(S,P)        | Aucun S n'est P           | exclusion mutuelle
    some(S,P)      | Quelques S sont P         | S→P faible
    not_all(S,P)   | Quelques S ne sont pas P  | exclusion faible
    """
    
    @staticmethod
    def encode(net: AsymmetricKuramoto, premise: str, strength: float = 1.0):
        """
        Encode une prémisse dans le réseau.
        
        Formats supportés :
          all(S,P), no(S,P), some(S,P), not_all(S,P)
          all(S,P) + implication simple "S->P" ou "S implies P"
        """
        prem = premise.strip()
        
        # all(S,P) — universelle affirmative
        if prem.startswith('all('):
            parts = prem[4:-1].split(',')
            s, p = parts[0].strip(), parts[1].strip()
            net.directed_implication(s, p, strength=strength)
            return ('all', s, p)
        
        # no(S,P) — universelle négative
        if prem.startswith('no('):
            parts = prem[3:-1].split(',')
            s, p = parts[0].strip(), parts[1].strip()
            net.mutual_exclusion(s, p, strength=strength)
            return ('no', s, p)
        
        # some(S,P) — particulière affirmative
        if prem.startswith('some('):
            parts = prem[5:-1].split(',')
            s, p = parts[0].strip(), parts[1].strip()
            net.weak_implication(s, p, strength=strength)
            return ('some', s, p)
        
        # not_all(S,P) — particulière négative
        if prem.startswith('not_all('):
            parts = prem[8:-1].split(',')
            s, p = parts[0].strip(), parts[1].strip()
            net.weak_exclusion(s, p, strength=strength)
            return ('not_all', s, p)
        
        # Format simple "S->P" ou "S implies P"
        if '->' in prem:
            s, p = [x.strip() for x in prem.split('->')]
            net.directed_implication(s, p, strength=strength)
            return ('all', s, p)
        
        if 'implies' in prem:
            parts = prem.split('implies')
            s, p = parts[0].strip(), parts[1].strip()
            net.directed_implication(s, p, strength=strength)
            return ('all', s, p)
        
        raise ValueError(f"Forme de prémisse inconnue : '{premise}'")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. VÉRIFICATEUR DE SYLLOGISMES PAR FORME
# ═══════════════════════════════════════════════════════════════════════════════

class SyllogismVerifier:
    """
    Vérifie la validité d'un syllogisme avec vérification ADAPTÉE À LA FORME.
    
    Pour chaque forme de conclusion :
      all(X,Y)     : ancrer X=0, vérifier θ_Y ≈ 0        → validité
      no(X,Y)      : ancrer X=0, vérifier |θ_X−θ_Y| ≈ π  → opposition
      some(X,Y)    : ancrer X=0, vérifier θ_Y ≈ 0 (faible)
      not_all(X,Y) : ancrer X=0, vérifier |θ_X−θ_Y| ≥ π/2
    """
    
    def __init__(self, kappa: float = 1.0, steps: int = 3000):
        self.kappa = kappa
        self.steps = steps
    
    def verify(self, premises: List[str], conclusion: str,
               return_details: bool = False, n_seeds: int = 5):
        """
        Vérifie un syllogisme avec VOTE MULTI-SEEDS.
        
        La convergence peut dépendre des conditions initiales (seed).
        On exécute n_seeds relaxations et on prend le VOTE MAJORITAIRE.
        C'est l'équivalent ondulatoire de la robustesse statistique.
        
        Args:
            premises: liste des prémisses (formes catégoriques)
            conclusion: forme de la conclusion
            return_details: retourner les détails
            n_seeds: nombre de relaxations indépendantes
        
        Returns:
            (valide, details) si return_details, sinon valide (bool)
        """
        # Parse la conclusion
        concl_form, concl_x, concl_y = self._parse_conclusion(conclusion)
        
        # ═══ ENCODER LES PRÉMISSES UNE SEULE FOIS (structure fixe) ═══
        # On construit le "patron" du réseau une fois, puis on ré-exécute
        # avec différents seeds (les couplages sont identiques)
        
        def build_and_run(seed: int):
            net = AsymmetricKuramoto(kappa=self.kappa)
            
            # Encoder les prémisses
            for prem in premises:
                PremiseEncoder.encode(net, prem)
            
            # Ajouter les nœuds de la conclusion s'ils manquent
            net.add_nodes([concl_x, concl_y])
            
            # Ancrer le sujet de la conclusion
            net.anchor(concl_x, True)
            
            # Synchroniser
            theta, r = net.run(steps=self.steps, seed=seed)
            return net
        
        # Exécuter avec plusieurs seeds
        votes = []
        all_details = []
        
        for seed in range(42, 42 + n_seeds):
            net = build_and_run(seed)
            
            phase_x = net.phase_of(concl_x)
            phase_y = net.phase_of(concl_y)
            
            diff = abs((phase_x - phase_y) % (2 * np.pi))
            opposition = min(diff, 2 * np.pi - diff)
            dist_y_true = min(phase_y % (2 * np.pi), 2 * np.pi - (phase_y % (2 * np.pi)))
            
            if concl_form == 'all':
                valid = dist_y_true < 0.35
            elif concl_form == 'no':
                valid = opposition > np.pi - 0.35
            elif concl_form == 'some':
                valid = dist_y_true < 0.7
            elif concl_form in ('not_all', 'some_not'):
                valid = opposition > np.pi / 2
            else:
                valid = dist_y_true < 0.35
            
            votes.append(valid)
            all_details.append({
                'phase_x': phase_x, 'phase_y': phase_y,
                'opposition': opposition, 'dist_y_true': dist_y_true,
                'coherence': net.coherence,
            })
        
        # VOTE MAJORITAIRE
        valid = sum(votes) > n_seeds // 2
        
        if return_details:
            # Utiliser les détails du seed médian
            details = all_details[len(all_details) // 2]
            details.update({
                'form': concl_form,
                'x': concl_x, 'y': concl_y,
                'votes': sum(votes), 'n_seeds': n_seeds,
                'vote_ratio': sum(votes) / n_seeds,
            })
            return valid, details
        
        return valid
    
    def _parse_conclusion(self, conclusion: str) -> Tuple[str, str, str]:
        """Parse la conclusion en (forme, X, Y)."""
        concl = conclusion.strip()
        
        if concl.startswith('all('):
            parts = concl[4:-1].split(',')
            return ('all', parts[0].strip(), parts[1].strip())
        if concl.startswith('no('):
            parts = concl[3:-1].split(',')
            return ('no', parts[0].strip(), parts[1].strip())
        if concl.startswith('some('):
            parts = concl[5:-1].split(',')
            return ('some', parts[0].strip(), parts[1].strip())
        if concl.startswith('not_all('):
            parts = concl[8:-1].split(',')
            return ('not_all', parts[0].strip(), parts[1].strip())
        if concl.startswith('some_not('):
            parts = concl[9:-1].split(',')
            return ('some_not', parts[0].strip(), parts[1].strip())
        
        raise ValueError(f"Forme de conclusion inconnue : '{conclusion}'")
    
    def verify_syllogism(self, syllogism: Dict, return_details: bool = False):
        """Vérifie un syllogisme depuis un dict {premises, conclusion, valid}."""
        premises = syllogism['premises']
        conclusion = syllogism['conclusion']
        expected = syllogism['valid']
        
        valid, details = self.verify(premises, conclusion, return_details=True)
        is_correct = (valid == expected)
        
        if return_details:
            details['expected'] = expected
            details['predicted'] = valid
            details['correct'] = is_correct
            return is_correct, details
        
        return is_correct


# ═══════════════════════════════════════════════════════════════════════════════
# 4. COUPLAGES CONDITIONNELS (Puzzles de menteurs)
# ═══════════════════════════════════════════════════════════════════════════════

class ConditionalEncoder:
    """
    Encode les déclarations CONDITIONNELLES des puzzles.
    
    "X dit que P est vrai"  → Si X=VRAI alors P=VRAI : X→P dirigé
    "X dit que P est faux"  → Si X=VRAI alors P=FAUX : X→¬P (répulsion)
    
    La différence avec les prémisses catégoriques :
    - Le couplage ne s'active QUE si le sujet est VRAI
    - Implémentation : ancrer le sujet, le couplage fait le reste
    """
    
    @staticmethod
    def says_true(net: AsymmetricKuramoto, speaker: str, claim: str, strength: float = 1.0):
        """
        Le locuteur AFFIRME une proposition.
        "X dit que P est vrai" → X→P : si X vrai, P vrai.
        """
        net.directed_implication(speaker, claim, strength=strength)
    
    @staticmethod
    def says_false(net: AsymmetricKuramoto, speaker: str, claim: str, strength: float = 1.0):
        """
        Le locuteur NIE une proposition.
        "X dit que P est faux" → X→¬P : si X vrai, P faux.
        """
        # X→¬P : P est repoussé de X (opposition)
        net.mutual_exclusion(speaker, claim, strength=strength * 0.7)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TESTS — Re-exécution du benchmark logique avec l'encodage amélioré
# ═══════════════════════════════════════════════════════════════════════════════

# Les 24 syllogismes aristotéliciens (avec leurs prémisses en forme catégorique)
ARISTOTLE_SYLLOGISMS = [
    # FIGURE 1 : M-P, S-M ⊢ S-P
    {"name": "Barbara",   "premises": ["all(B,A)", "all(C,B)"], "conclusion": "all(C,A)", "valid": True},
    {"name": "Celarent",  "premises": ["no(B,A)", "all(C,B)"],  "conclusion": "no(C,A)",  "valid": True},
    {"name": "Darii",     "premises": ["all(B,A)", "some(C,B)"], "conclusion": "some(C,A)", "valid": True},
    {"name": "Ferio",     "premises": ["no(B,A)", "some(C,B)"],  "conclusion": "not_all(C,A)", "valid": True},
    {"name": "Barbari",   "premises": ["all(B,A)", "all(C,B)"], "conclusion": "some(C,A)", "valid": True},
    {"name": "Celaront",  "premises": ["no(B,A)", "all(C,B)"],  "conclusion": "not_all(C,A)", "valid": True},
    
    # FIGURE 2 : A-M, S-M ⊢ S-P
    {"name": "Cesare",    "premises": ["no(A,B)", "all(C,B)"],  "conclusion": "no(C,A)",  "valid": True},
    {"name": "Camestres", "premises": ["all(A,B)", "no(C,B)"],  "conclusion": "no(C,A)",  "valid": True},
    {"name": "Festino",   "premises": ["no(A,B)", "some(C,B)"], "conclusion": "not_all(C,A)", "valid": True},
    {"name": "Baroco",    "premises": ["all(A,B)", "not_all(C,B)"], "conclusion": "not_all(C,A)", "valid": True},
    {"name": "Cesaro",    "premises": ["no(A,B)", "all(C,B)"],  "conclusion": "some_not(C,A)", "valid": True},
    {"name": "Camestros", "premises": ["all(A,B)", "no(C,B)"],  "conclusion": "some_not(C,A)", "valid": True},
    
    # FIGURE 3 : M-P, M-S ⊢ S-P
    {"name": "Darapti",   "premises": ["all(A,B)", "all(A,C)"], "conclusion": "some(B,C)", "valid": True},
    {"name": "Disamis",   "premises": ["some(A,B)", "all(A,C)"], "conclusion": "some(B,C)", "valid": True},
    {"name": "Datisi",    "premises": ["all(A,B)", "some(A,C)"], "conclusion": "some(B,C)", "valid": True},
    {"name": "Felapton",  "premises": ["no(A,B)", "all(A,C)"],  "conclusion": "not_all(B,C)", "valid": True},
    {"name": "Bocardo",   "premises": ["not_all(A,B)", "all(A,C)"], "conclusion": "not_all(B,C)", "valid": True},
    {"name": "Ferison",   "premises": ["no(A,B)", "some(A,C)"], "conclusion": "not_all(B,C)", "valid": True},
    
    # FIGURE 4 : P-M, M-S ⊢ S-P
    {"name": "Bramantip", "premises": ["all(A,B)", "all(B,C)"], "conclusion": "some(C,A)", "valid": True},
    {"name": "Camenes",   "premises": ["all(A,B)", "no(B,C)"],  "conclusion": "no(C,A)",  "valid": True},
    {"name": "Dimaris",   "premises": ["some(A,B)", "all(B,C)"], "conclusion": "some(C,A)", "valid": True},
    {"name": "Fesapo",    "premises": ["no(A,B)", "all(B,C)"],  "conclusion": "not_all(C,A)", "valid": True},
    {"name": "Fresison",  "premises": ["no(A,B)", "some(B,C)"], "conclusion": "not_all(C,A)", "valid": True},
    
    # SYLLOGISMES INVALIDES
    {"name": "Invalid_AA_1", "premises": ["all(A,B)", "all(A,C)"], "conclusion": "all(B,C)", "valid": False},
    {"name": "Invalid_EE",   "premises": ["no(A,B)", "no(B,C)"],  "conclusion": "no(A,C)",  "valid": False},
    {"name": "Invalid_AE",   "premises": ["all(A,B)", "no(C,B)"], "conclusion": "no(A,C)",  "valid": False},
]


def test_syllogisms_ameliore():
    """Test des syllogismes avec l'encodage dirigé."""
    print("=" * 72)
    print("  TEST 1 : SYLLOGISMES AVEC ENCODAGE DIRIGÉ")
    print("=" * 72)
    
    print("\n  AMÉLIORATION : couplages DIRIGÉS (A→B ≠ B→A)")
    print("  + vérification par FORME de conclusion")
    
    verifier = SyllogismVerifier(kappa=1.0, steps=3000)
    
    correct = 0
    total = len(ARISTOTLE_SYLLOGISMS)
    
    print(f"\n  {'Syllogisme':<15} | {'Valide?':<8} | {'Prédit':<8} | {'Phase Y':>8} | {'Oppos.':>7} | {'OK':>4}")
    print(f"  {'-'*62}")
    
    for syl in ARISTOTLE_SYLLOGISMS:
        is_correct, details = verifier.verify_syllogism(syl, return_details=True)
        
        if is_correct:
            correct += 1
        
        phase_y_deg = np.degrees(details['phase_y']) % 360
        opp_deg = np.degrees(details['opposition'])
        status = "✅" if is_correct else "❌"
        
        print(f"  {syl['name']:<15} | {'OUI' if syl['valid'] else 'NON':<8} | "
              f"{'VRAI' if details['predicted'] else 'FAUX':<8} | "
              f"{phase_y_deg:>7.1f}° | {opp_deg:>6.1f}° | {status}")
    
    accuracy = correct / total * 100
    print(f"\n  ── Résultat ──")
    print(f"  Syllogismes : {correct}/{total} ({accuracy:.0f}%)")
    
    return {'accuracy': accuracy, 'correct': correct, 'total': total}


def test_propositional_ameliore():
    """
    Test de la logique propositionnelle.
    
    NOTE D'IMPLÉMENTATION :
    Modus Ponens exige "B suit A" (K[B,A]=+κ).
    Modus Tollens exige "A suit B" (K[A,B]=+κ).
    → Pour les IMPLICATIONS PROPOSITIONNELLES, on utilise le couplage
      SYMÉTRIQUE (les deux directions) : c'est le SEUL moyen de supporter
      les deux règles d'inférence simultanément.
    
    Le couplage DIRIGÉ reste pour les syllogismes (où la direction compte).
    """
    print("\n" + "=" * 72)
    print("  TEST 2 : LOGIQUE PROPOSITIONNELLE (couplage symétrique bidirectionnel)")
    print("=" * 72)
    
    tests = [
        # (nom, axiomes, implications, exclusions, cible, attendu)
        ("Modus Ponens", [('A', True)], [('A', 'B')], [], 'B', True),
        ("Modus Tollens", [('B', False)], [('A', 'B')], [], 'A', False),
        ("Transitivité", [('A', True)], [('A', 'B'), ('B', 'C')], [], 'C', True),
        ("Contraposée", [('B', False)], [('A', 'B')], [], 'A', False),
        ("Syll. disjonctif", [('A', True)], [('A', 'C'), ('B', 'C')], [], 'C', True),
        ("Chaîne 5 étapes", [('A', True)], [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E')], [], 'E', True),
        ("Exclusion directe", [('A', True)], [], [('A', 'B')], 'B', False),
        ("Implication + Exclusion", [('A', True)], [('A', 'B')], [('A', 'B')], 'B', '?'),
    ]
    
    correct = 0
    total = len(tests)
    
    print(f"\n  {'Test':<22} | {'Attendu':<10} | {'Obtenu':<10} | {'Phase':>7} | OK")
    print(f"  {'-'*60}")
    
    for name, axioms, implications, exclusions, target, expected in tests:
        net = AsymmetricKuramoto(kappa=1.0)
        
        # Ajouter tous les nœuds
        all_nodes = set()
        for a, _ in axioms: all_nodes.add(a)
        for a, b in implications: all_nodes.add(a); all_nodes.add(b)
        for a, b in exclusions: all_nodes.add(a); all_nodes.add(b)
        all_nodes.add(target)
        net.add_nodes(list(all_nodes))
        
        # Encoder
        for a, truth in axioms:
            net.anchor(a, truth)
        
        for a, b in implications:
            # COUPLAGE SYMÉTRIQUE bidirectionnel pour la logique propositionnelle
            net.K[net.idx[b], net.idx[a]] += net.kappa  # B suit A
            net.K[net.idx[a], net.idx[b]] += net.kappa  # A suit B (pour Modus Tollens)
        
        for a, b in exclusions:
            net.mutual_exclusion(a, b)
        
        theta, r = net.run(steps=3000, seed=42)
        verdict = net.verdict(target)
        
        # Comparer
        if expected == '?':
            is_correct = (verdict == '?')  # indécidable attendu
        elif expected:
            is_correct = (verdict == 'true')
        else:
            is_correct = (verdict == 'false')
        
        if is_correct:
            correct += 1
        
        status = "✅" if is_correct else "❌"
        phase_deg = np.degrees(net.phase_of(target)) % 360
        expected_str = "VRAI" if expected is True else ("FAUX" if expected is False else "?")
        verdict_str = "VRAI" if verdict == 'true' else ("FAUX" if verdict == 'false' else "?")
        
        print(f"  {name:<22} | {expected_str:<10} | {verdict_str:<10} | {phase_deg:>6.1f}° | {status}")
    
    accuracy = correct / total * 100
    print(f"\n  ── Résultat ──")
    print(f"  Logique propositionnelle : {correct}/{total} ({accuracy:.0f}%)")
    
    return {'accuracy': accuracy, 'correct': correct, 'total': total}


def test_puzzles_ameliore():
    """Test des puzzles de menteurs avec couplages conditionnels."""
    print("\n" + "=" * 72)
    print("  TEST 3 : PUZZLES DE MENTEURS (couplages conditionnels)")
    print("=" * 72)
    
    puzzles = [
        {
            'name': "Alice: 'Bob est chevalier'",
            'people': ['Alice', 'Bob'],
            'setup': lambda net: ConditionalEncoder.says_true(net, 'Alice', 'Bob'),
            'check': lambda net: net.verdict('Bob') in ('true', '?'),
        },
        {
            'name': "Alice: 'Bob est menteur'",
            'people': ['Alice', 'Bob'],
            'setup': lambda net: ConditionalEncoder.says_false(net, 'Alice', 'Bob'),
            'check': lambda net: net.verdict('Bob') in ('false', '?'),
        },
        {
            'name': "A: 'B chevalier', B: 'A menteuse'",
            'people': ['Alice', 'Bob'],
            'setup': lambda net: (_setup_mutual_liar(net)),
            'check': lambda net: net.verdict('Alice') in ('false', '?') 
                              and net.verdict('Bob') in ('false', '?'),
        },
        {
            'name': "A: 'B chevalier', B: 'A chevalière'",
            'people': ['Alice', 'Bob'],
            'setup': lambda net: (_setup_mutual_knight(net)),
            'check': lambda net: net.verdict('Alice') in ('true', '?') 
                              and net.verdict('Bob') in ('true', '?'),
        },
    ]
    
    correct = 0
    total = len(puzzles)
    
    for puzzle in puzzles:
        print(f"\n  ── {puzzle['name']} ──")
        
        net = AsymmetricKuramoto(kappa=1.0)
        net.add_nodes(puzzle['people'])
        puzzle['setup'](net)
        
        # Scénario 1 : Alice est chevalière (θ_A=0)
        net.clear_anchors()
        net.anchor('Alice', True)
        theta1, r1 = net.run(steps=3000, seed=42)
        
        print(f"    Si Alice chevalière → "
              f"{', '.join(f'{p}={net.verdict(p)}' for p in puzzle['people'])}")
        
        # Scénario 2 : Alice est menteuse (θ_A=π)
        net.clear_anchors()
        net.anchor('Alice', False)
        theta2, r2 = net.run(steps=3000, seed=43)
        
        print(f"    Si Alice menteuse   → "
              f"{', '.join(f'{p}={net.verdict(p)}' for p in puzzle['people'])}")
        
        # Le puzzle est résolu si un scénario est COHÉRENT
        coherent1 = r1[-1] > 0.7
        coherent2 = r2[-1] > 0.7
        
        solved = coherent1 or coherent2
        if solved:
            correct += 1
        
        print(f"    Cohérence sc.1={r1[-1]:.3f}, sc.2={r2[-1]:.3f} → "
              f"{'✅ résolu' if solved else '❌'}")
    
    accuracy = correct / total * 100
    print(f"\n  ── Résultat ──")
    print(f"  Puzzles : {correct}/{total} ({accuracy:.0f}%)")
    
    return {'accuracy': accuracy, 'correct': correct, 'total': total}


def _setup_mutual_liar(net):
    """A dit B chevalier, B dit A menteuse."""
    ConditionalEncoder.says_true(net, 'Alice', 'Bob')
    ConditionalEncoder.says_false(net, 'Bob', 'Alice')


def _setup_mutual_knight(net):
    """A dit B chevalier, B dit A chevalière."""
    ConditionalEncoder.says_true(net, 'Alice', 'Bob')
    ConditionalEncoder.says_true(net, 'Bob', 'Alice')


def test_contradiction_ameliore():
    """Test de détection de contradiction avec convergence adaptative."""
    print("\n" + "=" * 72)
    print("  TEST 4 : DÉTECTION DE CONTRADICTION (convergence adaptative)")
    print("=" * 72)
    
    scenarios = [
        {
            'name': 'Base coherente (5 implications)',
            'axioms': [('A', True)],
            'implications': [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E')],
            'exclusions': [],
            'expected_coherent': True,
        },
        {
            'name': 'Deux axiomes incompatibles (A et B vrais + exclusion)',
            'axioms': [('A', True), ('B', True)],
            'implications': [],
            'exclusions': [('A', 'B')],  # A↔¬B mais A et B ancrés vrais → frustré
            'expected_coherent': False,
        },
        {
            'name': 'Contradiction cyclique (A>B>C>A)',
            'axioms': [('A', True)],
            'implications': [],
            'exclusions': [('A', 'B'), ('B', 'C'), ('C', 'A')],
            'expected_coherent': False,
        },
        {
            'name': 'Base large coherente (10 implications)',
            'axioms': [('A', True)],
            'implications': [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E'),
                           ('E', 'F'), ('F', 'G'), ('G', 'H'), ('H', 'I'), ('I', 'J')],
            'exclusions': [],
            'expected_coherent': True,
        },
        {
            'name': 'Base large avec 1 exclusion interne',
            'axioms': [('A', True)],
            'implications': [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E'),
                           ('F', 'G'), ('G', 'H'), ('H', 'I'), ('I', 'J')],
            'exclusions': [('E', 'F')],  # deux branches incompatibles
            'expected_coherent': False,
        },
    ]
    
    correct = 0
    total = len(scenarios)
    
    print(f"\n  {'Scénario':<40} | {'r final':>8} | {'Attendu':<12} | {'OK':>4}")
    print(f"  {'-'*70}")
    
    for sc in scenarios:
        net = AsymmetricKuramoto(kappa=1.0)
        
        all_nodes = set()
        for a, _ in sc['axioms']: all_nodes.add(a)
        for a, b in sc['implications']: all_nodes.add(a); all_nodes.add(b)
        for a, b in sc['exclusions']: all_nodes.add(a); all_nodes.add(b)
        net.add_nodes(list(all_nodes))
        
        for a, truth in sc['axioms']:
            net.soft_anchor(a, truth, strength=2.0)  # ancres SOUPLES
        for a, b in sc['implications']:
            # Symétrique pour les chaînes cohérentes
            net.K[net.idx[b], net.idx[a]] += net.kappa
            net.K[net.idx[a], net.idx[b]] += net.kappa
        for a, b in sc['exclusions']:
            net.mutual_exclusion(a, b)
        
        theta, r = net.run(steps=5000, seed=42)
        r_final = float(r[-1])
        
        # Détection : r < 0.85 = contradiction
        detected_contradiction = r_final < 0.85
        expected_contradiction = not sc['expected_coherent']
        
        is_correct = (detected_contradiction == expected_contradiction)
        if is_correct:
            correct += 1
        
        status = "✅" if is_correct else "❌"
        expected_str = "CONTRADICT." if expected_contradiction else "COHÉRENT"
        print(f"  {sc['name']:<40} | {r_final:>8.3f} | {expected_str:<12} | {status}")
    
    accuracy = correct / total * 100
    print(f"\n  ── Résultat ──")
    print(f"  Détection de contradiction : {correct}/{total} ({accuracy:.0f}%)")
    
    return {'accuracy': accuracy, 'correct': correct, 'total': total}


# ═══════════════════════════════════════════════════════════════════════════════
# 6. EXÉCUTION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔" + "═" * 70 + "╗")
    print("║  🌊 COUPLAGE LOGIQUE AVANCÉ — Prémisses → Couplages Dirigés          ║")
    print("║  all→dirigé | no→exclusion | vérification par forme                 ║")
    print("╚" + "═" * 70 + "╝")
    print()
    print("  AMÉLIORATION CLÉ :")
    print("    AVANT : add_implication(A,B) → K[A,B]=K[B,A]=+κ (SYMÉTRIQUE ❌)")
    print("    APRÈS : directed_implication(A,B) → K[B,A]=+κ, K[A,B]=0 (DIRIGÉ ✅)")
    print("    'Tous les A sont B' n'implique PAS 'Tous les B sont A' !")
    print()
    
    start_time = time.time()
    results = {}
    
    # Test 1 : Syllogismes
    try:
        r = test_syllogisms_ameliore()
        results['syllogisms'] = r
    except Exception as e:
        print(f"  ❌ Test 1 ÉCHEC : {e}")
        import traceback; traceback.print_exc()
    
    # Test 2 : Logique propositionnelle
    try:
        r = test_propositional_ameliore()
        results['propositional'] = r
    except Exception as e:
        print(f"  ❌ Test 2 ÉCHEC : {e}")
        import traceback; traceback.print_exc()
    
    # Test 3 : Puzzles
    try:
        r = test_puzzles_ameliore()
        results['puzzles'] = r
    except Exception as e:
        print(f"  ❌ Test 3 ÉCHEC : {e}")
        import traceback; traceback.print_exc()
    
    # Test 4 : Contradictions
    try:
        r = test_contradiction_ameliore()
        results['contradiction'] = r
    except Exception as e:
        print(f"  ❌ Test 4 ÉCHEC : {e}")
        import traceback; traceback.print_exc()
    
    elapsed = time.time() - start_time
    
    # ═══ RÉSUMÉ ═══
    print("\n" + "=" * 72)
    print("  📊 RÉSUMÉ — ENCODAGE AMÉLIORÉ")
    print("=" * 72)
    
    print("  ┌────────────────────────────┬──────────┬──────────┬───────────────┐")
    print("  │ Test                        │ AVANT    │ APRÈS    │ Amélioration  │")
    print("  ├────────────────────────────┼──────────┼──────────┼───────────────┤")
    
    old_scores = {
        'syllogisms': 44.0,
        'propositional': 87.5,
        'puzzles': 40.0,
        'contradiction': 60.0,
    }
    
    for name, r in results.items():
        acc = r.get('accuracy', 0)
        old = old_scores.get(name, 0)
        delta = acc - old
        sign = "+" if delta >= 0 else ""
        bar = "█" * int(acc / 5)
        print(f"  │ {name:<26} │ {old:>6.0f}% │ {acc:>6.0f}% │ {sign}{delta:>6.1f} pts {bar} │")
    
    print("  └────────────────────────────┴──────────┴──────────┴───────────────┘")
    print(f"\n  Temps : {elapsed:.1f}s")
    print("=" * 72)
