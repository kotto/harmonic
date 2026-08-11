#!/usr/bin/env python3
"""
exploration_piste5_entropie.py — P5↔P6 : la dorée et SON domaine
================================================================
La distribution dorée pₙ = (1−1/φ)(1/φ)ⁿ (E3) ne fit pas les données du
codec dans le domaine de Fourier (mesuré, publié). La piste 6 a montré
que le contenu À MÉMOIRE appartient au domaine doré. Ce test croise :

  CONTENUS × DOMAINES
  · contenus : bruit doré (1/f^{1/φ}) · bruit blanc · une ligne d'image
  · domaines : Fourier · FrFT dorée (ordre 1/φ, méthode de groupe)
  · métrique : le ratio géométrique empirique des occupations de niveau
               vs 1/φ = 0,618 (la dorée) — et le chi² du fit

Si le contenu doré transformé dans le domaine doré produit des données
dont la géométrique empirique ≈ la dorée → l'entropie dorée a trouvé
SON domaine (P5↔P6 fermé).
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vital-ka' / 'core' / 'python'))
from exploration_piste6_frft import frft, GOLDEN_ORDER  # noqa: E402

PHI = (1 + np.sqrt(5)) / 2
Q = 1 / PHI


def make_content(kind: str, n: int = 256, rng=None) -> np.ndarray:
    rng = rng or np.random.default_rng(5)
    if kind == 'gold_noise':
        k = np.fft.fftfreq(n)
        k_safe = np.where(k == 0, 1.0, k)
        sig = np.fft.ifft(np.fft.fftshift(
            np.abs(k_safe) ** (-1 / (2 * PHI)) * np.exp(1j * rng.uniform(0, 2 * math.pi, n))))
        return sig / np.linalg.norm(sig) * np.sqrt(n)
    if kind == 'white_noise':
        return rng.normal(size=n) + 1j * rng.normal(size=n)
    if kind == 'image_row':
        from PIL import Image
        img = np.array(Image.open(
            r'E:\SAAS - Copie\COMPRESSION-CAMERA\METHOD_2_SDI_LIKE_IMAGE_COMPRESSION\architecture_photo.png'
        ).convert('L'))
        return img[100, :n].astype(np.float64)


def geometric_ratio(coeffs: np.ndarray) -> float:
    """Les occupations de niveau par la VRAIE quantification du codec :
    la chaîne cₙ (64 niveaux) appliquée aux magnitudes gardées — puis le
    ratio de décroissance empirique de l'histogramme des niveaux :
    r_emp = ⟨hist[k+1]/hist[k]⟩ — la dorée prédit r = 1/φ = 0,618."""
    from hcv2_modal_codec import CHAIN_LEVELS, golden_chain
    mag = np.abs(coeffs.ravel())
    p = mag ** 2
    p /= p.sum()
    keep = p > 1 / (PHI * p.size)
    mags = mag[keep]
    if mags.size < 20:
        return 0.0, 99.0
    lev = golden_chain()[::-1]                    # croissant
    q = np.minimum(np.searchsorted(lev, mags / mags.max()), CHAIN_LEVELS - 1)
    hist = np.bincount(q, minlength=CHAIN_LEVELS).astype(np.float64)
    ratios = hist[1:] / (hist[:-1] + 1e-9)
    r_emp = float(np.mean(ratios[ratios < 1.0])) if np.any(ratios < 1.0) else 0.0
    # chi² vs la géométrique de même raison (les 20 premiers niveaux)
    gold = (1 - r_emp) * r_emp ** np.arange(20)
    emp = hist[:20] / (hist[:20].sum() + 1e-9)
    chi2 = float(np.sum((emp - gold) ** 2 / (gold + 1e-9)))
    return r_emp, chi2


print("═" * 70)
print("P5↔P6 — LA DISTRIBUTION DORÉE ET SON DOMAINE (contenus × domaines)")
print("═" * 70)
rng = np.random.default_rng(5)
contents = {
    'bruit doré 1/f^{1/φ}': make_content('gold_noise', rng=rng),
    'bruit blanc          ': make_content('white_noise', rng=rng),
    'ligne d\'image réelle ': make_content('image_row'),
}
print(f"\n   Le ratio géométrique empirique des occupations vs la dorée "
      f"1/φ = {Q:.3f} :")
print(f"   {'contenu':<22}{'Fourier':>14}{'domaine doré':>16}")
print('─' * 56)
for name, sig in contents.items():
    row = []
    for dom, transform in [('Fourier', np.fft.fft), ('doré (1/φ)', None)]:
        coeffs = transform(sig) if transform else frft(sig, GOLDEN_ORDER)
        r_emp, chi2 = geometric_ratio(coeffs)
        fit = '✅' if abs(r_emp - Q) < 0.1 and chi2 < 0.05 else ''
        row.append(f'{r_emp:.3f} (χ² {chi2:.2f}) {fit}')
    print(f"   {name:<22}{row[0]:>14}{row[1]:>18}")

print("\n   Lecture : la dorée prédit un ratio 0,618 partout où les")
print("   occupations de niveau suivent la géométrique dorée.")
print("   → si le bruit doré DANS le domaine doré fit : P5 a trouvé son domaine")
print("═" * 70)
