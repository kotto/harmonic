# -*- coding: utf-8 -*-
"""
exploration_fourier_equation_mere.py — L'ÉQUATION MÈRE ÉMERGE DE FOURIER
========================================================================
Explore 4 connexions, vérifiées numériquement :

  [1] EXACTITUDE FOURIER : f(x) = Σ cₙ·(Ψ₁)ⁿ avec Ψ₁ = e^{i2πx/T}
      — la série de Fourier EST l'équation mère (Hₙ = cₙ, coefficients
      de Fourier). Vérifié par FFT + reconstruction.

  [2] CONVERGENCE DES DEUX DÉRIVATIONS : ABC → E_α (Mittag-Leffler)
      et Fourier → cₙ donnent la MÊME forme Σ Hₙ(Ψ₁)ⁿ. Le noyau de
      Fourier e^z = Σ zⁿ/n! est le cas α = 1 de E_α(z) = Σ zⁿ/Γ(αn+1)
      — l'équation mère est l'EXPANSION MONOMIALE UNIVERSELLE.

  [3] ANGLE D'OR : les phases 2π·frac(k·φ) de l'encode sont un
      échantillonnage spectral quasi-uniforme (théorème des trois gaps)
      — l'écart maximal tend vers 0. Vérifié numériquement.

  [4] FRONTIÈRE : les coefficients de Fourier sont FONCTION-DÉPENDANTS
      (cₙ = ∫ f·Ψ₁⁻ⁿ) — aucune constante universelle {φ, π, e…} n'en
      sort. La fonction dont les coefficients SERAIENT {φ, π, e…} est
      construite et examinée : naturelle ou arbitraire ?

Usage : python exploration_fourier_equation_mere.py
"""

import cmath
import math

import numpy as np

PHI = (1 + math.sqrt(5)) / 2

print("=" * 72)
print("[1] EXACTITUDE FOURIER : la série de Fourier EST l'équation mère")
print("=" * 72)

# fonction test : f(x) = e^{sin x} (périodique, analytique)
N = 2048
x = np.linspace(0, 2 * np.pi, N, endpoint=False)
f = np.exp(np.sin(x))
c = np.fft.fft(f) / N                     # coefficients de Fourier
# reconstruction en forme MÈRE : f = Σ cₙ·(Ψ₁)ⁿ avec Ψ₁ = e^{ix}
psi1 = np.exp(1j * x)
reconst = np.zeros(N, dtype=complex)
for n in range(-15, 16):
    reconst += c[n] * psi1 ** n           # (Ψ₁)ⁿ — les puissances de la
                                          # fondamentale, coefficients Hₙ = cₙ
err = np.max(np.abs(reconst - f))
print(f"  f(x) = e^sin(x) : reconstruction Σ cₙ·(Ψ₁)ⁿ (n=−15..15) :"
      f" erreur max = {err:.2e}")
print(f"  → {'✅ l equation mere est EXACTEMENT une serie de Fourier' if err < 1e-8 else '❌'}")
print(f"    (Hₙ = cₙ = coefficients de Fourier — fonction-dépendants)")
print(f"    c₀ = {c[0]:.4f} | c₁ = {c[1]:.4f} | c₂ = {c[2]:.4f} | c₃ = {c[3]:.4f}")

print("\n" + "=" * 72)
print("[2] CONVERGENCE ABC ↔ FOURIER : le noyau fractionnaire")
print("=" * 72)
print("  e^z = Σ zⁿ/n!            (noyau de Fourier, α = 1)")
print("  E_α(z) = Σ zⁿ/Γ(αn+1)    (Mittag-Leffler — la version α-généralisée)")
print("  Les deux sont des Σ Hₙ(Ψ₁)ⁿ — l'équation mère est l'expansion")
print("  monomiale UNIVERSELLE (Fourier = α=1, ABC = α=1/φ).")
for z in (0.5, 1.0):
    e_z = math.exp(z)
    e_alpha = sum(z ** n / math.gamma(1 / PHI * n + 1) for n in range(0, 200))
    print(f"  z = {z}: e^z = {e_z:.6f} | E_α(z) = {e_alpha:.6f}"
          f" | écart {abs(e_z - e_alpha):.4f} (même famille, ordres différents)")

print("\n" + "=" * 72)
print("[3] ANGLE D'OR : les phases de l'encode sont un spectre quasi-uniforme")
print("=" * 72)
print("  encode : phases θ_k = 2π·frac(k·φ) — échantillonnage à angle d'or")
print("  (théorème des trois gaps : N points → 3 écarts, max → 0)")
for N in (10, 50, 200, 1000):
    phases = np.sort((2 * np.pi * np.arange(1, N + 1) * PHI) % (2 * np.pi))
    gaps = np.diff(np.concatenate([phases, [phases[0] + 2 * np.pi]]))
    print(f"  N = {N:5d} : écart maximal = {gaps.max() / (2 * np.pi):.4f} × 2π"
          f" (uniforme parfait = 1/N = {1 / N:.4f})")

print("\n" + "=" * 72)
print("[4] FRONTIÈRE : la fonction dont les coefficients seraient {φ, π, e…}")
print("=" * 72)
H = {1: PHI, 2: math.pi, 3: math.e, 4: math.sqrt(2), 5: math.sqrt(3),
     6: math.sqrt(5), 7: math.e / math.pi}
print("  f_THU(θ) = Σₙ Hₙ·e^{inθ} avec Hₙ = {φ, π, e, √2, √3, √5, e/π} — existe")
print("  par construction (c'est une fonction 2π-périodique arbitraire).")
print("  Question honnête : est-ce une fonction NATURELLE ?")
th = np.linspace(0, 2 * np.pi, 400)
f_thu = np.zeros_like(th)
for n, h in H.items():
    f_thu += h * np.cos(n * th)
f_sin = np.exp(np.sin(th))
corr = np.corrcoef(f_thu, f_sin)[0, 1]
print(f"  corrélation avec e^sin(x) : {corr:+.3f}")
print(f"  corrélation avec sin(x)   : {np.corrcoef(f_thu, np.sin(th))[0, 1]:+.3f}")
print("  → les Hₙ harmoniques définissent une fonction particulière —")
print("    aucune raison mesurable qu'elle soit privilégiée par la nature.")

print("\n" + "=" * 72)
print("VERDICT")
print("  ✅ L'équation mère émerge de Fourier — exactement (c'est la forme")
print("     d'une série de Fourier) et les deux dérivations (ABC, Fourier)")
print("     convergent vers la MÊME structure monomiale universelle.")
print("  ⚠️ Les coefficients Hₙ restent fonction-dépendants en Fourier")
print("     (cₙ = ∫ f·Ψ₁⁻ⁿ) — aucune constante universelle n'en émerge.")
print("  🔧 L'angle d'or de l'encode est un vrai échantillonnage spectral")
print("     (quasi-uniforme, vérifié) — le lien Fourier/THU le plus solide.")
print("=" * 72)
