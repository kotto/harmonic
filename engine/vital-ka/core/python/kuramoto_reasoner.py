# -*- coding: utf-8 -*-
"""kuramoto_reasoner.py — le raisonnement comme synchronisation de phase.

Chaque proposition i = un oscillateur de phase θᵢ(t) :

    θ̇ᵢ = ωᵢ + Σⱼ Kᵢⱼ·sin(θⱼ − θᵢ) + ξᵢ(t)

  • axiomes ancrés : θ = 0 (« vrai ») ou θ = π (« faux »), jamais assignés
    aux propositions dérivées — leur équilibre émerge du couplage.
  • implication A→B  : K_AB = +κ  → les deux oscillateurs se tirent vers
    la synchronisation (même phase).
  • contradiction A↔B : K_AB = −κ → répulsion vers l'antiphase θ = π.
  • bruit ξ ~ N(0, σ²) : incertitude / ambiguïté du signal d'entrée.

Paramètre d'ordre global : r·e^{iψ} = (1/N)·Σ e^{iθᵢ}
  r → 1  : réseau synchronisé, système de croyances cohérent.
  r bas ou oscillant sans se stabiliser : contradiction non résolue
  (frustration de verre de spin — « tenir deux idées contradictoires »).

La validité d'un argument devient une question d'existence d'un point
fixe stable dans la topologie de couplage — pas une propriété des
symboles.

La dynamique est une descente de gradient (bruitée) du potentiel
  V(θ) = −½ Σᵢⱼ Kᵢⱼ·cos(θⱼ − θᵢ)
sur le tore — c'est un système de spins XY (verre de spin continu).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


class KuramotoReasoner:
    """Réseau d'oscillateurs : chaque proposition = une phase sur le cercle."""

    def __init__(self, names: Sequence[str], kappa: float = 1.0,
                 sigma: float = 0.0, dt: float = 0.02):
        self.names = list(names)
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.n = len(self.names)
        self.kappa = kappa
        self.sigma = sigma
        self.dt = dt
        self.K = np.zeros((self.n, self.n))      # matrice de couplage
        self.anchors: Dict[int, float] = {}      # indice → phase imposée (0 ou π)

    # ── Construction de la topologie ─────────────────────────────────────────
    def add_implication(self, a: str, b: str) -> None:
        """A → B : soutien mutuel (synchronisation vers la même phase)."""
        i, j = self.idx[a], self.idx[b]
        self.K[i, j] += self.kappa
        self.K[j, i] += self.kappa

    def add_contradiction(self, a: str, b: str) -> None:
        """A ↔ ¬B : incompatibilité (répulsion vers l'antiphase π)."""
        i, j = self.idx[a], self.idx[b]
        self.K[i, j] -= self.kappa
        self.K[j, i] -= self.kappa

    def anchor(self, name: str, truth: bool) -> None:
        """Axiome : phase imposée (0 = vrai, π = faux)."""
        self.anchors[self.idx[name]] = 0.0 if truth else np.pi

    # ── Dynamique ────────────────────────────────────────────────────────────
    def run(self, steps: int = 2000, seed: Optional[int] = None,
            ) -> Tuple[np.ndarray, np.ndarray]:
        """Intègre la dynamique (Euler). Retourne (θ final, série de r)."""
        rng = np.random.default_rng(seed)
        theta = rng.uniform(0.0, 2 * np.pi, self.n)
        for i, ph in self.anchors.items():
            theta[i] = ph
        r_series = np.empty(steps)
        dt = self.dt
        for t in range(steps):
            # dθᵢ = Σⱼ Kᵢⱼ·sin(θⱼ − θᵢ)
            dtheta = (self.K * np.sin(theta[None, :] - theta[:, None])).sum(axis=1)
            if self.sigma > 0:
                dtheta = dtheta + rng.normal(0.0, self.sigma, self.n)
            theta = theta + dt * dtheta
            for i, ph in self.anchors.items():
                theta[i] = ph
            r_series[t] = abs(np.mean(np.exp(1j * theta)))
        return theta, r_series

    @staticmethod
    def verdict(theta: float, tol: float = 0.35) -> str:
        """θ ≈ 0 → 'true' ; θ ≈ π → 'false' ; sinon '?' (indécidable)."""
        w = theta % (2 * np.pi)
        if min(w, 2 * np.pi - w) < tol:
            return 'true'
        if abs(w - np.pi) < tol:
            return 'false'
        return '?'

    def infer(self, name: str, steps: int = 2000, seed: int = 0,
              ) -> Tuple[str, float, float]:
        """Interroge une proposition : verdict, phase finale, cohérence r."""
        theta, r = self.run(steps, seed=seed)
        i = self.idx[name]
        return self.verdict(theta[i]), float(theta[i]), float(r[-1])


def potential(K: np.ndarray, theta: np.ndarray) -> float:
    """V(θ) = −½ Σ Kᵢⱼ cos(θⱼ − θᵢ) — l'« énergie de tension » du réseau."""
    d = theta[None, :] - theta[:, None]
    return -0.5 * float(np.sum(K * np.cos(d)))
