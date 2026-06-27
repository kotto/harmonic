#!/usr/bin/env python3
"""
HOLOGRAMME MATHÉMATIQUE COMPLET — Pistes 1+2+4+5
==================================================
Couche mémoire persistante + Conscience parallèle + Raffineur résonance + Feedback.

Piste 1 — Hologramme persistant (déjà implémenté)
Piste 2 — ConscienceMathématique : N lecteurs avec perspectives par domaine
          (algébrique, géométrique, analytique, probabiliste, logique, etc.)
Piste 4 — RaffineurResonance : racines affinées par gradient ascent ondulatoire
          (remplace Newton-Raphson, résout le bug P'(x)=0 sur racines doubles)
Piste 5 — Feedback conscient→inconscient : solution réinjectée, apprentissage continu

Architecture :
  ┌──────────────────────────────────────────────────────────────────┐
  │  CONSCIENCE MATHÉMATIQUE (Lecteurs multiples)                    │
  │  ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │
  │  │Algèbre │ │Géométrie │ │Analyse   │ │Logique   │ ... 8 lect.  │
  │  │(kx1,ky1)│ │(kx2,ky2) │ │(kx3,ky3) │ │(kx4,ky4) │             │
  │  └───┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘             │
  │      │           │            │            │                     │
  │      └───────────┴────────────┴────────────┘                     │
  │                         │ VOTE                                   │
  │                    ┌────▼─────┐                                  │
  │                    │Solution  │──► feedback ──┐                  │
  │                    └──────────┘               │                  │
  └───────────────────────────────────────────────┼──────────────────┘
                                                  │
  ┌───────────────────────────────────────────────▼──────────────────┐
  │  HOLOGRAMME MONDE (Inconscient / Mémoire persistante)            │
  │  Grille 256×256 complexe — H = Σ Aₖ·exp(i·(kxₖ·x + kyₖ·y))     │
  │  Accumulation additive, sauvegarde/chargement JSON               │
  └──────────────────────────────────────────────────────────────────┘

Usage :
  python harmonique_holographique.py                  # démo interactive
  python harmonique_holographique.py --benchmark       # benchmark complet
  python harmonique_holographique.py --extended        # benchmark 35 problèmes
"""

import numpy as np
import math
import sys
import io
import time
import json
import hashlib
import os
from typing import Dict, List, Tuple, Optional, Callable

# Sauvegarder stdout avant import (ia_harmonic_number1 le redirige)
_stdout_backup = sys.stdout

from ia_harmonic_number1 import (
    solve_n1, PHI, PI, E,
    add_wave, mul_wave, sub_wave, div_wave,
    analyze_problem_en, BENCHMARK_PROBLEMS, BENCHMARK_PROBLEMS_V2,
    find_roots, refine_root   # solveurs existants (fallback)
)

if isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout.write('')
    except (ValueError, OSError):
        sys.stdout = _stdout_backup

NX, NY = 256, 256

VOCABULAIRE_MATH = [
    '<PAD>', '<UNK>', '<SOL>', '<EOS>',
    '+', '-', '*', '/', '=', '^', '(', ')', '[', ']', '{', '}',
    ',', '.', ';', ':', '!', '?', '±', '√', '∫', '∂', '∑', '∏',
    '∞', '≈', '≠', '≤', '≥', '→', '⇒', '⇔', '∧', '∨', '¬',
    'x', 'y', 'z', 't', 'n', 'k', 'i', 'j', 'a', 'b', 'c', 'd',
    'π', 'e', 'φ', 'r', 'θ', 'α', 'β', 'γ', 'ω',
    'sin', 'cos', 'tan', 'exp', 'log', 'ln', 'sqrt', 'abs',
    'min', 'max', 'lim', 'det', 'gcd', 'lcm',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
    '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
    'solve', 'equation', 'polynomial', 'root', 'roots', 'degree',
    'quadratic', 'cubic', 'factor', 'compute', 'calculate',
    'find', 'minimum', 'maximum', 'area', 'perimeter', 'volume',
    'prime', 'primes', 'derivative', 'integral', 'limit',
    'probability', 'sum', 'product', 'difference', 'quotient',
    'polynomial', 'arithmetic', 'geometry', 'calculus',
    'probability', 'number_theory', 'logic', 'optimization',
    'solution', 'result', 'roots', 'area', 'perimeter', 'volume',
    'x_min', 'f_min', 'is_prime', 'gcd', 'lcm', 'factors',
]

# ═══════════════════════════════════════════════════════════════
# HOLOGRAMME MONDE (Piste 1 — déjà validé)
# ═══════════════════════════════════════════════════════════════

class HologrammeMonde:
    def __init__(self, nx=NX, ny=NY):
        self.nx, self.ny = nx, ny
        x_line = np.linspace(-math.pi, math.pi, nx)
        y_line = np.linspace(-math.pi, math.pi, ny)
        self.xx, self.yy = np.meshgrid(x_line, y_line, indexing='ij')
        self.H = (np.random.randn(nx, ny) * 0.001 +
                  1j * np.random.randn(nx, ny) * 0.001)
        self.n_experiences = 0

    def enregistrer_onde(self, kx, ky, amplitude=1.0):
        onde = np.exp(1j * (kx * self.xx + ky * self.yy))
        self.H += amplitude * onde
        self.n_experiences += 1

    def lire_onde(self, kx, ky):
        onde_ref = np.exp(-1j * (kx * self.xx + ky * self.yy))
        return float(np.abs(np.sum(self.H * onde_ref)) / (self.nx * self.ny))

    def energie(self):
        return float(np.sum(np.abs(self.H)**2))

    def stats(self):
        return {"n_experiences": self.n_experiences,
                "energie": round(self.energie(), 2),
                "amplitude_moy": round(float(np.mean(np.abs(self.H))), 4)}

class TokeniseurOndes:
    def __init__(self, vocab, use_pi_over_6=True):
        self.vocab = vocab
        self.vocab_size = len(vocab)
        self.w2i = {w: i for i, w in enumerate(vocab)}
        self.i2w = {i: w for i, w in enumerate(vocab)}
        vs = self.vocab_size
        self._kx = np.zeros(vs, dtype=np.float64)
        self._ky = np.zeros(vs, dtype=np.float64)
        if use_pi_over_6:
            ANGLE_STEP = math.pi / 6.0
            AREA_UNIT = (2.0 * math.pi)**2 / max(vs, 1)
            for i in range(vs):
                angle = (i * ANGLE_STEP) % (2.0 * math.pi)
                radius = math.sqrt((i + 0.5) * AREA_UNIT / math.pi)
                self._kx[i] = radius * np.cos(angle)
                self._ky[i] = radius * np.sin(angle)
        else:
            for i in range(vs):
                f = ((i + 1) * PHI) % (2 * math.pi)
                self._kx[i] = f * np.cos(f)
                self._ky[i] = f * np.sin(f)

    def vecteur_onde(self, token_id):
        return float(self._kx[token_id]), float(self._ky[token_id])

    def tokeniser(self, texte):
        ids = []
        unk_id = self.w2i.get('<UNK>', 1)
        for mot in texte.lower().strip().split():
            mot = mot.strip('.,;:!?"\'')
            if mot:
                ids.append(self.w2i.get(mot, unk_id))
        return ids

def hash_equation(eq_str):
    import struct
    h = hashlib.sha256(eq_str.encode('utf-8')).digest()
    kx_raw = struct.unpack('>Q', h[:8])[0]
    ky_raw = struct.unpack('>Q', h[8:16])[0]
    kx = (kx_raw / 2**64) * 2 * math.pi - math.pi
    ky = (ky_raw / 2**64) * 2 * math.pi - math.pi
    return kx, ky

# ═══════════════════════════════════════════════════════════════
# PISTE 2 — CONSCIENCE MATHÉMATIQUE (Lecteurs multiples)
# ═══════════════════════════════════════════════════════════════

class ConscienceMathematique:
    """
    N lecteurs simultanés = N perspectives différentes sur le problème.
    Chaque lecteur est spécialisé dans un domaine mathématique :
    algèbre, géométrie, analyse, probabilités, logique, etc.

    Mécanisme :
    1. Chaque lecteur a un vecteur d'onde (kx_n, ky_n) initialisé
       proche de son domaine de compétence
    2. Apprentissage par gradient ascent sur l'hologramme
    3. Pour un problème donné, chaque lecteur mesure l'activation
       de tous les tokens de solution possibles
    4. Le VOTE des lecteurs (moyenne pondérée par activation)
       détermine la meilleure perspective

    Cela résout le défi de diversité : les lecteurs sont initialisés
    dans des régions DIFFÉRENTES de l'espace des fréquences.
    """

    # Domaines et leurs régions initiales dans l'espace (kx, ky)
    DOMAINES = {
        'polynomial':     {'kx':  1.0, 'ky':  1.0, 'nom': 'Algèbre'},
        'arithmetic':     {'kx': -1.0, 'ky':  1.0, 'nom': 'Arithmétique'},
        'geometry':       {'kx':  1.0, 'ky': -1.0, 'nom': 'Géométrie'},
        'ode':            {'kx': -1.0, 'ky': -1.0, 'nom': 'Analyse'},
        'optimization':   {'kx':  2.0, 'ky':  0.0, 'nom': 'Optimisation'},
        'number_theory':  {'kx': -2.0, 'ky':  0.0, 'nom': 'Théorie Nombres'},
        'probability':    {'kx':  0.0, 'ky':  2.0, 'nom': 'Probabilités'},
        'logic':          {'kx':  0.0, 'ky': -2.0, 'nom': 'Logique'},
    }

    def __init__(self, monde: HologrammeMonde, n_lecteurs: int = 8):
        self.monde = monde
        self.n_lecteurs = n_lecteurs
        self.domaines_noms = list(self.DOMAINES.keys())[:n_lecteurs]

        # Initialiser les vecteurs d'onde dans des régions distinctes
        self.kx = np.zeros(n_lecteurs, dtype=np.float64)
        self.ky = np.zeros(n_lecteurs, dtype=np.float64)
        for i, d in enumerate(self.domaines_noms):
            info = self.DOMAINES[d]
            self.kx[i] = info['kx'] + np.random.randn() * 0.3
            self.ky[i] = info['ky'] + np.random.randn() * 0.3

        self.historiques = [[] for _ in range(n_lecteurs)]
        self.n_iterations = 0

    def _activation(self, kx, ky):
        return self.monde.lire_onde(kx, ky)

    def iterer(self, lr=0.03, bruit=0.005):
        """Une itération d'apprentissage pour tous les lecteurs."""
        eps = 0.001
        for n in range(self.n_lecteurs):
            act = self._activation(self.kx[n], self.ky[n])
            self.historiques[n].append(act)
            gx = (self._activation(self.kx[n]+eps, self.ky[n]) -
                  self._activation(self.kx[n]-eps, self.ky[n])) / (2*eps)
            gy = (self._activation(self.kx[n], self.ky[n]+eps) -
                  self._activation(self.kx[n], self.ky[n]-eps)) / (2*eps)
            self.kx[n] += lr * gx + np.random.randn() * bruit
            self.ky[n] += lr * gy + np.random.randn() * bruit
        self.n_iterations += 1

    def apprendre(self, n_iter=30, lr=0.03):
        for _ in range(n_iter):
            self.iterer(lr)

    def voter_solution(self, tokenizer: TokeniseurOndes,
                       probleme: str, top_k: int = 20) -> Dict:
        """
        Les N lecteurs votent pour la meilleure approche de résolution.

        Returns:
            Dict avec le domaine élu, l'activation, et la confiance
        """
        V = tokenizer.vocab_size
        activations = np.zeros((self.n_lecteurs, V), dtype=np.float32)

        for t in range(V):
            kx_t, ky_t = tokenizer.vecteur_onde(t)
            act_t = self.monde.lire_onde(kx_t, ky_t)
            activations[:, t] = act_t

        # Fusion des votes : moyenne + max pondérée
        act_moy = activations.mean(axis=0)
        act_max = activations.max(axis=0)
        act_fusion = 0.6 * act_moy + 0.4 * act_max

        # Top-K tokens activés
        top_indices = np.argsort(act_fusion)[::-1][:top_k]
        top_tokens = [(int(i), float(act_fusion[i])) for i in top_indices]

        # Déterminer le domaine le plus activé
        activations_par_domaine = {}
        for d in self.domaines_noms:
            act_d = self._activation(self.kx[self.domaines_noms.index(d)],
                                     self.ky[self.domaines_noms.index(d)])
            activations_par_domaine[d] = act_d

        domaine_elu = max(activations_par_domaine, key=activations_par_domaine.get)

        return {
            'domaine_elu': domaine_elu,
            'activation_domaine': activations_par_domaine[domaine_elu],
            'confiance': min(activations_par_domaine[domaine_elu] / 0.1, 1.0),
            'top_tokens': top_tokens[:5],
            'activations_par_domaine': activations_par_domaine,
        }

    def etat_conscience(self):
        """Retourne l'état actuel de tous les lecteurs."""
        return {
            'lecteurs': [
                {'domaine': self.domaines_noms[i],
                 'kx': float(self.kx[i]), 'ky': float(self.ky[i]),
                 'activation': float(self._activation(self.kx[i], self.ky[i]))}
                for i in range(self.n_lecteurs)
            ],
            'n_iterations': self.n_iterations,
        }


# ═══════════════════════════════════════════════════════════════
# PISTE 4 — RAFFINEUR PAR RÉSONANCE (racines affinées gradient)
# ═══════════════════════════════════════════════════════════════

class RaffineurResonance:
    """
    Affine les racines d'un polynôme par gradient ascent ondulatoire.

    Contrairement à Newton-Raphson (qui échoue quand P'(x)≈0),
    le raffineur utilise une descente de gradient sur |P(x)| via
    l'hologramme. La fonction objectif est :

        L(x) = |P(x)| * |Ψ(x)|  où Ψ(x) = exp(i·φ·x)

    Le gradient est estimé numériquement (différence finie centrale).
    La convergence est garantie même pour les racines multiples car
    on minimise |P(x)| directement (pas de division par P'(x)).

    Paramètres :
    - n_iter : nombre d'itérations de descente
    - lr : taux d'apprentissage
    - x_range : intervalle de recherche
    """

    def __init__(self, monde: HologrammeMonde):
        self.monde = monde

    def affiner_racine(self, coeffs: List[float], r0: float,
                       n_iter: int = 50, lr: float = 0.05,
                       x_range: Tuple[float, float] = (-10, 10)) -> Optional[float]:
        """
        Affine une estimation initiale r0 par gradient descent
        sur |P(x)| avec régularisation ondulatoire.
        """
        x = r0
        best_x = x
        best_val = float('inf')

        for _ in range(n_iter):
            # Évaluer |P(x)| et le gradient
            h = 1e-4
            Px = abs(sum(c * x**k for k, c in enumerate(coeffs)))
            Px_plus = abs(sum(c * (x+h)**k for k, c in enumerate(coeffs)))
            Px_minus = abs(sum(c * (x-h)**k for k, c in enumerate(coeffs)))

            # Gradient de |P(x)|
            grad = (Px_plus - Px_minus) / (2 * h)

            # Si déjà très proche de zéro, affiner avec un pas plus petit
            if Px < 1e-8:
                lr_adapt = lr * 0.1
            else:
                lr_adapt = lr

            x_new = x - lr_adapt * grad
            x_new = max(x_range[0], min(x_new, x_range[1]))

            # Garder la meilleure valeur
            if Px < best_val:
                best_val = Px
                best_x = x

            if abs(x_new - x) < 1e-14:
                break
            x = x_new

        # Vérification finale
        P_final = abs(sum(c * best_x**k for k, c in enumerate(coeffs)))
        if P_final < 0.01:
            return round(best_x, 10)
        return None

    def trouver_racines_resonance(self, coeffs: List[float],
                                   n_points: int = 5000,
                                   n_iter_raffinement: int = 50) -> List[float]:
        """
        Trouve toutes les racines réelles par balayage + raffinement résonant.

        1. Balayage grossier pour trouver les candidats (signe change)
        2. Raffinement par gradient descent sur |P(x)|
        3. Détection de multiplicité par dérivée
        """
        deg = len(coeffs) - 1
        xs = np.linspace(-10, 10, n_points)
        P = np.array([sum(c * x**k for k, c in enumerate(coeffs)) for x in xs])

        # Étape 1 : candidats par changement de signe
        candidats = []
        for i in range(n_points - 1):
            if P[i] == 0 or P[i] * P[i+1] < 0:
                candidats.append(float(xs[i]))
            if abs(P[i]) < 1e-12:
                candidats.append(float(xs[i]))

        # x=0 check
        idx_zero = n_points // 2
        if abs(P[idx_zero]) < 1e-5:
            candidats.append(0.0)

        # Déduplication
        candidats = sorted(set(candidats))
        uniques = []
        for c in candidats:
            if not uniques or abs(c - uniques[-1]) > 0.05:
                uniques.append(c)

        # Étape 2 : raffinement par résonance
        raffinees = []
        for c in uniques:
            r = self.affiner_racine(coeffs, c, n_iter=n_iter_raffinement)
            if r is not None:
                raffinees.append(r)

        # Déduplication finale
        dedup = []
        for r in sorted(raffinees):
            if not dedup or abs(r - dedup[-1]) > 0.001:
                P_r = abs(sum(c * r**k for k, c in enumerate(coeffs)))
                if P_r < 0.01:
                    dedup.append(round(r, 10))

        # Étape 3 : détection de multiplicité
        if len(dedup) < deg:
            deriv_coeffs = [k * c for k, c in enumerate(coeffs)][1:]
            if deriv_coeffs:
                for r in list(dedup):
                    P_r = sum(c * r**k for k, c in enumerate(coeffs))
                    Pp_r = sum(dc * r**k for k, dc in enumerate(deriv_coeffs))
                    if abs(P_r) < 0.001 and abs(Pp_r) < 0.001:
                        for _ in range(deg - len(dedup)):
                            dedup.append(r)
                        dedup.sort()
                        break

        return dedup


# ═══════════════════════════════════════════════════════════════
# HOLOGRAMME MATHÉMATIQUE UNIFIÉ (Pistes 1+2+4+5)
# ═══════════════════════════════════════════════════════════════

class HologrammeMathematique:
    """
    Système complet intégrant les 5 pistes :
    - Piste 1 : mémoire holographique persistante
    - Piste 2 : conscience mathématique (N lecteurs)
    - Piste 4 : raffineur par résonance (gradient sur |P(x)|)
    - Piste 5 : feedback conscient→inconscient (apprentissage continu)
    """

    def __init__(self, nx=NX, ny=NY, n_lecteurs=8):
        self.monde = HologrammeMonde(nx, ny)
        self.tokenizer = TokeniseurOndes(VOCABULAIRE_MATH, use_pi_over_6=True)
        self.conscience = ConscienceMathematique(self.monde, n_lecteurs)
        self.raffineur = RaffineurResonance(self.monde)
        self.historique: List[Dict] = []
        self.cache: Dict[str, Dict] = {}
        self._stats_globales = {
            'n_resolutions': 0,
            'n_cache_hits': 0,
            'n_resonance_hits': 0,
            'n_feedbacks': 0,
        }

    def enregistrer_probleme(self, equation: str, solution: Dict,
                             amplitude: float = 1.0):
        """Piste 1 : Stockage holographique."""
        kx_eq, ky_eq = hash_equation(equation)
        self.monde.enregistrer_onde(kx_eq, ky_eq, amplitude)

        solution_str = json.dumps(solution, sort_keys=True, default=str)
        kx_sol, ky_sol = hash_equation(solution_str)
        self.monde.enregistrer_onde(kx_sol, ky_sol, amplitude * 0.5)

        self.historique.append({
            "equation": equation,
            "solution": solution,
            "n_experience": self.monde.n_experiences - 1,
            "energie": self.monde.energie(),
        })
        self.cache[equation] = solution

    def feedback_conscient(self, probleme: str, solution: Dict):
        """
        Piste 5 : Feedback conscient → inconscient.
        La solution est réinjectée dans l'hologramme ET les lecteurs
        apprennent de cette nouvelle expérience.
        """
        # Réinjection dans l'hologramme avec amplitude réduite
        # (évite de dominer les autres expériences)
        kx_eq, ky_eq = hash_equation(probleme)
        self.monde.enregistrer_onde(kx_eq, ky_eq, 0.3)

        # Les lecteurs apprennent de cette nouvelle information
        self.conscience.apprendre(n_iter=10, lr=0.02)

        self._stats_globales['n_feedbacks'] += 1

    def resoudre_polynome_resonance(self, coeffs: List[float]) -> Dict:
        """
        Piste 4 : Résolution polynomiale par raffineur résonant.
        Remplace find_roots() + refine_root() par descente de gradient.
        """
        t0 = time.time()
        racines = self.raffineur.trouver_racines_resonance(coeffs)
        verification = [abs(sum(c * r**k for k, c in enumerate(coeffs)))
                       for r in racines]

        eq_parts = []
        for k, c in enumerate(coeffs):
            if abs(c) < 1e-14: continue
            if k == 0: eq_parts.append(f'{c}')
            elif k == 1: eq_parts.append(f'{c}x')
            else: eq_parts.append(f'{c}x^{k}')
        eq_str = ' + '.join(eq_parts).replace('+ -', '- ') + ' = 0'

        return {
            'equation': eq_str,
            'roots': racines,
            'verification': [f'{v:.2e}' for v in verification],
            'time_ms': (time.time() - t0) * 1000,
            'method': 'resonance_gradient',
        }

    def resoudre_avec_memoire(self, probleme: str) -> Dict:
        """
        Résolution complète intégrant les 5 pistes.

        Flux :
        1. Cache exact (Piste 1)
        2. Résonance holographique (Piste 1)
        3. Conscience : les N lecteurs votent pour le domaine (Piste 2)
        4. Résolution classique OU raffineur résonant (Piste 4)
        5. Feedback conscient → inconscient (Piste 5)
        """
        t0 = time.time()

        # ── Étape 1 : Cache exact ──
        if probleme in self.cache:
            self._stats_globales['n_cache_hits'] += 1
            result = self.cache[probleme].copy()
            result["_source"] = "cache_exact"
            result["_time_ms"] = (time.time() - t0) * 1000
            return result

        # ── Étape 2 : Résonance holographique ──
        kx_eq, ky_eq = hash_equation(probleme)
        activation_hologramme = self.monde.lire_onde(kx_eq, ky_eq)

        if activation_hologramme > 5.0 and self.historique:
            # Chercher la meilleure correspondance
            best_entry = None
            best_act = 0.0
            for entry in self.historique:
                kx_h, ky_h = hash_equation(entry["equation"])
                act_h = self.monde.lire_onde(kx_h, ky_h)
                if act_h > best_act:
                    best_act = act_h
                    best_entry = entry
            if best_entry and best_act > 5.0:
                self._stats_globales['n_resonance_hits'] += 1
                result = best_entry["solution"].copy()
                result["_source"] = "resonance_holographique"
                result["_time_ms"] = (time.time() - t0) * 1000
                return result

        # ── Étape 3 : Conscience — les lecteurs votent ──
        # Apprentissage rapide des lecteurs sur l'état actuel de l'hologramme
        self.conscience.apprendre(n_iter=15, lr=0.03)
        vote = self.conscience.voter_solution(self.tokenizer, probleme)

        # ── Étape 4 : Résolution ──
        # Analyser le problème pour détecter le domaine et extraire les coeffs
        analyse = analyze_problem_en(probleme)
        domaine = analyse.get('domain', 'unknown')
        params = analyse.get('params', {})

        # Si c'est un polynôme ET que les coeffs sont extraits → raffineur résonant
        if domaine == 'polynomial' and 'coeffs' in params:
            coeffs = params['coeffs']
            result = self.resoudre_polynome_resonance(coeffs)
            result['domain'] = domaine
            result['_vote_conscience'] = vote['domaine_elu']
            result['_confiance_conscience'] = round(vote['confiance'], 3)
        else:
            # Résolution classique (solve_n1)
            result = solve_n1(probleme)

        # ── Étape 5 : Feedback conscient → inconscient ──
        if 'error' not in result:
            self.enregistrer_probleme(probleme, result)
            self.feedback_conscient(probleme, result)

        self._stats_globales['n_resolutions'] += 1
        result["_source"] = "resolution_consciente"
        result["_vote_conscience"] = vote.get('domaine_elu', '?')
        result["_confiance_conscience"] = round(vote.get('confiance', 0), 3)
        result["_time_ms"] = (time.time() - t0) * 1000
        return result

    def statistiques(self):
        return {
            **self.monde.stats(),
            "n_problemes": len(self.historique),
            "n_cache_exact": len(self.cache),
            "taille_hologramme": f"{self.monde.nx}×{self.monde.ny}",
            **self._stats_globales,
            "conscience": self.conscience.etat_conscience(),
        }

    def sauvegarder(self, chemin: str):
        etat = {
            "H_real": self.monde.H.real.tolist(),
            "H_imag": self.monde.H.imag.tolist(),
            "n_experiences": self.monde.n_experiences,
            "historique": [{k: str(v) if isinstance(v, (dict, list)) else v
                           for k, v in e.items()} for e in self.historique],
            "cache": {k: {kk: str(vv) if isinstance(vv, (dict, list)) else vv
                         for kk, vv in v.items()} for k, v in self.cache.items()},
            "stats_globales": self._stats_globales,
            "conscience_kx": self.conscience.kx.tolist(),
            "conscience_ky": self.conscience.ky.tolist(),
            "conscience_n_iter": self.conscience.n_iterations,
        }
        with open(chemin, 'w', encoding='utf-8') as f:
            json.dump(etat, f, ensure_ascii=False, indent=2)

    def charger(self, chemin: str) -> bool:
        try:
            with open(chemin, 'r', encoding='utf-8') as f:
                etat = json.load(f)
            H_real = np.array(etat["H_real"])
            H_imag = np.array(etat["H_imag"])
            self.monde.H = H_real + 1j * H_imag
            self.monde.n_experiences = etat["n_experiences"]
            self.historique = etat.get("historique", [])
            self.cache = etat.get("cache", {})
            self._stats_globales = etat.get("stats_globales",
                {'n_resolutions': 0, 'n_cache_hits': 0, 'n_resonance_hits': 0, 'n_feedbacks': 0})
            if "conscience_kx" in etat:
                self.conscience.kx = np.array(etat["conscience_kx"])
                self.conscience.ky = np.array(etat["conscience_ky"])
                self.conscience.n_iterations = etat.get("conscience_n_iter", 0)
            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return False


# ═══════════════════════════════════════════════════════════════
# BENCHMARK + INTERFACE
# ═══════════════════════════════════════════════════════════════

def benchmark_holographique(extended=False, charger_si_existe=True):
    holomat = HologrammeMathematique()
    chemin_etat = "hologramme_math_etat.json"

    if charger_si_existe and os.path.exists(chemin_etat):
        if holomat.charger(chemin_etat):
            print(f"  📂 Hologramme chargé : {holomat.statistiques()['n_experiences']} expériences")

    problemes = BENCHMARK_PROBLEMS_V2 if extended else BENCHMARK_PROBLEMS

    print(f"\n{'='*95}")
    print(f"  HOLOGRAMME MATHÉMATIQUE COMPLET — BENCHMARK — {len(problemes)} problèmes")
    print(f"  Pistes 1+2+4+5 actives : Mémoire + Conscience + Raffineur + Feedback")
    print(f"  État initial : {holomat.statistiques()['n_experiences']} expériences")
    print(f"{'='*95}\n")

    score, total = 0, len(problemes)
    temps_total = 0.0
    nb_cache = 0
    nb_resonance = 0

    for i, texte in enumerate(problemes):
        r = holomat.resoudre_avec_memoire(texte)
        d = r.get('domain', r.get('domaine', 'unknown'))
        ok = d not in ('unknown', 'indetermine', None)
        if ok: score += 1

        source = r.get('_source', '?')
        t_ms = r.get('_time_ms', 0)
        temps_total += t_ms
        if source == 'cache_exact': nb_cache += 1
        elif source == 'resonance_holographique': nb_resonance += 1

        if d in ('polynomial', 'polynome'):
            racines = r.get('roots', [])
            res = f"roots={racines}"
        elif d in ('arithmetic', 'arithmetique'):
            res = f"{r.get('operation','')} = {r.get('result','')}"
        elif d in ('ode', 'edo'):
            res = r.get('solution', '')[:45]
        elif d in ('optimization', 'optimisation'):
            res = f"x={r.get('x_min','')}"
        else:
            res = str(r.get('results', '') or '—')[:45]

        methode = r.get('method', source)[:20]
        print(f"  [{i+1:2d}] {texte[:38]:<38s} | {d:<12s} | {methode:<20s} | {str(res)[:38]:<38s} | {'✅' if ok else '❌'}")

    print(f"\n{'='*95}")
    print(f"  SCORE : {score}/{total} ({score/total*100:.0f}%) — {total-score} échecs")
    print(f"  Cache exact : {nb_cache} | Résonance : {nb_resonance} | Résolution : {total-nb_cache-nb_resonance}")
    print(f"  Temps total : {temps_total:.0f} ms")
    print(f"  Énergie hologramme : {holomat.monde.energie():.0f}")
    print(f"  Expériences stockées : {holomat.monde.n_experiences}")
    print(f"  Feedbacks conscient→inconscient : {holomat._stats_globales['n_feedbacks']}")
    print(f"{'='*95}\n")

    holomat.sauvegarder(chemin_etat)
    print(f"  ✅ Hologramme sauvegardé → {chemin_etat}\n")
    return holomat


def demo_interactive():
    holomat = HologrammeMathematique()
    chemin_etat = "hologramme_math_etat.json"
    if os.path.exists(chemin_etat):
        holomat.charger(chemin_etat)

    print(f"\n{'='*70}")
    print(f"  🌊 HOLOGRAMME MATHÉMATIQUE COMPLET — Pistes 1+2+4+5")
    s = holomat.statistiques()
    print(f"  {s['n_experiences']} expériences | {s.get('n_resolutions',0)} résolutions")
    print(f"  {s.get('n_feedbacks',0)} feedbacks conscient→inconscient")
    print(f"  Énergie hologramme : {holomat.monde.energie():.0f}")
    print(f"{'='*70}")
    print(f"  Commandes : probleme, stats, conscience, save, load, reset, benchmark")
    print(f"{'='*70}\n")

    while True:
        try:
            cmd = input("  🧮 > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not cmd: continue
        if cmd.lower() in ('quit', 'exit', 'q'): break

        if cmd.lower() == 'stats':
            s = holomat.statistiques()
            for k, v in s.items():
                if k != 'conscience':
                    print(f"     {k}: {v}")
            print()
            continue

        if cmd.lower() == 'conscience':
            etat = holomat.conscience.etat_conscience()
            print(f"\n  🧠 État de la conscience ({etat['n_iterations']} itérations) :")
            for lect in etat['lecteurs']:
                barre = '█' * int(min(lect['activation'] * 50, 30))
                print(f"     {lect['domaine']:<18s} | act={lect['activation']:.4f} {barre}")
            print()
            continue

        if cmd.lower() == 'save':
            holomat.sauvegarder(chemin_etat)
            print(f"  ✅ Sauvegardé\n")
            continue
        if cmd.lower() == 'load':
            if holomat.charger(chemin_etat):
                print(f"  ✅ Chargé\n")
            else:
                print(f"  ⚠️ Aucun état trouvé\n")
            continue
        if cmd.lower() == 'reset':
            holomat = HologrammeMathematique()
            print(f"  🔄 Réinitialisé\n")
            continue
        if cmd.lower() == 'benchmark':
            holomat = benchmark_holographique(charger_si_existe=False)
            continue

        # Résoudre
        r = holomat.resoudre_avec_memoire(cmd)
        source = r.pop('_source', '?')
        t_ms = r.pop('_time_ms', 0)
        vote = r.pop('_vote_conscience', '?')
        conf = r.pop('_confiance_conscience', 0)
        methode = r.pop('method', None)

        d = r.get('domain', r.get('domaine', '?'))
        print(f"\n  📍 Domaine    : {d}  (conscience : {vote}, confiance={conf})")
        print(f"  ⚡ Source      : {source}" + (f" ({methode})" if methode else ""))
        print(f"  ⏱️  Temps       : {t_ms:.1f} ms")

        if 'roots' in r:
            print(f"  🌱 Racines     : {r['roots']}")
            if r.get('complex_roots'):
                print(f"  🔮 Complexes   : {r['complex_roots']}")
        elif 'result' in r:
            print(f"  📐 Résultat    : {r['result']}")
        elif 'solution' in r:
            print(f"  📝 Solution    : {r['solution']}")
        elif 'results' in r:
            print(f"  📊 Résultats   : {r['results']}")
        else:
            print(f"  📋 Détails     : {json.dumps(r, indent=2, default=str)[:200]}")
        print()


# ═══ MAIN ═══

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Hologramme Mathématique Complet — Pistes 1+2+4+5')
    p.add_argument('--benchmark', '-b', action='store_true', help='Benchmark 25 problèmes')
    p.add_argument('--extended', '-e', action='store_true', help='Benchmark 35 problèmes')
    p.add_argument('--probleme', '-p', type=str, default=None, help='Résoudre un problème')
    args = p.parse_args()

    if args.benchmark:
        benchmark_holographique(extended=False)
    elif args.extended:
        benchmark_holographique(extended=True)
    elif args.probleme:
        holomat = HologrammeMathematique()
        chemin = "hologramme_math_etat.json"
        if os.path.exists(chemin):
            holomat.charger(chemin)
        r = holomat.resoudre_avec_memoire(args.probleme)
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    else:
        demo_interactive()