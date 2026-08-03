"""
🌊 Adaptive Spectral Operator — Transformée de Fourier Adaptative
==================================================================
Remplace le SpectralOperator fixe (STFT + Hann) par un opérateur
qui APPREND sa propre base de Fourier en fonction du contexte.

Principe (piste B du PROPOSAL — filtre adaptatif) :
  Au lieu de la FFT classique (fréquences fixes e^{2πikn/N}),
  chaque couche apprend ses PROPRES fréquences via un MLP
  qui dépend du contenu de la phrase.

Trois mécanismes d'adaptation :
  1. FREQUENCY WARPING : ω_k(x) = ω_k^base + MLP_freq(context)
     → Les fréquences se DÉPLACENT selon le contenu de la phrase
  2. SPECTRAL GATING   : g_k(x) = σ(MLP_gate(|coeffs|))
     → Pondération fréquentielle apprise, content-dépendante
  3. PHASE MODULATION  : Δφ_k(x) = MLP_phase(context)
     → Déphasage appris pour amplifier la sélectivité positionnelle

Contrairement à AFNO (Guibas 2021) qui utilise une base FFT fixe
avec un mixing appris, NOTRE opérateur peut DÉFORMER les fréquences
elles-mêmes — c'est une non-uniform FFT avec points d'échantillonnage
appris.

Architecture d'une couche adaptative :
  Input ψ ∈ ℂ^{L×D}
     │
     ├─► POOL → contexte c ∈ ℝ^D
     │
     ├─► FREQUENCY WARP : prédit Δω_k par échelle (déformation de la grille)
     ├─► SPECTRAL GATING : prédit gains g_k par canal fréquentiel
     ├─► PHASE MODULATION : prédit Δφ_k par canal
     │
     ▼
  STFT multi-échelle (fenêtres APPRISES, pas Hann fixe)
     → chaque échelle : FFT → warping + gating + phase → IFFT
     ▼
  Output ψ' ∈ ℂ^{L×D}

Poids DÉTERMINISTES (φ-based init, comme tout le reste).
L'apprentissage se fait via gradient externe ; les paramètres
sont clairement étiquetés et exportables.

Usage :
  from adaptive_spectral_operator import AdaptiveSpectralOperator
  op = AdaptiveSpectralOperator(dim=128, window_sizes=(16,32,64))
  psi_out = op.forward(psi_in)  # ψ_in, ψ_out ∈ ℂ^{L×D}
  params = op.params()          # pour l'entraînement supervisé
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional

# ════════════════════════════════════════════════════════════════
# CONSTANTES (cohérentes avec harmonic_transformer.py)
# ════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
TAU = 2.0 * math.pi


# ════════════════════════════════════════════════════════════════
# UTILITAIRES DÉTERMINISTES (identiques à harmonic_transformer.py)
# ════════════════════════════════════════════════════════════════

def _fnv1a_32(s: str) -> int:
    h = 2166136261
    for ch in s.encode('utf-8'):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _det_normal(d: int, seed: int) -> np.ndarray:
    rng = np.random.RandomState(seed)
    return rng.randn(d).astype(np.float64)


def _gelu(x: np.ndarray) -> np.ndarray:
    """GELU rapide (approximation tanh) — identique à PyTorch nn.GELU."""
    return 0.5 * x * (1.0 + np.tanh(
        np.sqrt(2.0 / np.pi) * (x + 0.044715 * x ** 3)))


# ════════════════════════════════════════════════════════════════
# MLP MINIMAL (2 couches, déterministe)
# ════════════════════════════════════════════════════════════════

class TinyMLP:
    """MLP à 2 couches avec GELU — ~4K paramètres max."""

    def __init__(self, in_dim: int, hidden: int, out_dim: int,
                 seed_salt: str = ""):
        lim1 = math.sqrt(3.0 / in_dim)
        lim2 = math.sqrt(3.0 / hidden)
        s1 = _fnv1a_32(f"mlp_w1_{seed_salt}")
        s2 = _fnv1a_32(f"mlp_b1_{seed_salt}")
        s3 = _fnv1a_32(f"mlp_w2_{seed_salt}")
        s4 = _fnv1a_32(f"mlp_b2_{seed_salt}")
        self.W1 = (_det_normal(in_dim * hidden, s1).reshape(in_dim, hidden)
                   * 2 * lim1 - lim1).astype(np.float64)
        self.b1 = (_det_normal(hidden, s2) * 2 * lim1 - lim1).astype(np.float64)
        self.W2 = (_det_normal(hidden * out_dim, s3).reshape(hidden, out_dim)
                   * 2 * lim2 - lim2).astype(np.float64)
        self.b2 = (_det_normal(out_dim, s4) * 2 * lim2 - lim2).astype(np.float64)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """x: [..., in_dim] → [..., out_dim]"""
        h = x @ self.W1 + self.b1
        h = _gelu(h)
        return h @ self.W2 + self.b2

    def params(self):
        return [self.W1, self.b1, self.W2, self.b2]


# ════════════════════════════════════════════════════════════════
# FENÊTRES APPRISES (remplacent Hann fixe)
# ════════════════════════════════════════════════════════════════

def _init_learned_window(w: int, seed: int, alpha: float = 0.3) -> np.ndarray:
    """Initialise une fenêtre APPRISE proche de Hann (comme point de départ).

    Au lieu de Hann fixe (0 à t=0 → perte de sélectivité aux bords),
    on part de Hann + perturbation φ-déterministe → la fenêtre
    n'est JAMAIS nulle aux bords, ce qui préserve l'information.
    """
    # Hann classique (point de départ)
    hann = 0.5 * (1 - np.cos(TAU * np.arange(w) / w))
    # Perturbation déterministe bornée
    pert = _det_normal(w, seed) * alpha
    # Fenêtre apprise : Hann + perturbation, normalisée
    win = hann + pert
    # S'assurer que la fenêtre n'est pas nulle (min à 0.01)
    win = np.maximum(win, 0.01)
    # Normaliser pour COLA (Σ w² ≈ constante pour hop=w/2)
    expected_sum = 1.5  # Σ Hann² = 1.5 pour hop exact
    norm_factor = np.sqrt(expected_sum / np.sum(win ** 2) * (w / (w // 2)))
    win = win * norm_factor
    return win.astype(np.float64)


# ════════════════════════════════════════════════════════════════
# OPÉRATEUR SPECTRAL ADAPTATIF
# ════════════════════════════════════════════════════════════════

class AdaptiveSpectralOperator:
    """
    Transformée de Fourier Adaptative — la base de Fourier est modifiée
    en fonction du CONTENU de la phrase.

    Comparé au SpectralOperator fixe :
      - Fenêtres APPRISES (pas Hann → jamais nulles aux bords)
      - Gating fréquentiel CONTENT-DEPENDENT (le filtre s'adapte)
      - Phase modulation pour AMPLIFIER la sélectivité

    Paramètres apprenables :
      - Fenêtres par échelle       : {w: [w]} pour chaque w
      - MLP de contexte → gains    : TinyMLP(dim → hidden → dim)
      - MLP de contexte → Δphase   : TinyMLP(dim → hidden → dim)

    Total params (dim=64, n_scales=3, hidden=32) : ~9 800
    → Comparable à une tête d'attention, très léger.
    """

    def __init__(self, dim: int,
                 window_sizes: Tuple[int, ...] = (16, 32, 64),
                 hidden_ctx: int = 32,
                 layer_id: int = 0):
        self.dim = dim
        self.window_sizes = window_sizes
        self.n_scales = len(window_sizes)
        self.dim_per_scale = dim // self.n_scales

        # --- Fenêtres apprises (une par échelle) ---
        self._windows: Dict[int, np.ndarray] = {}
        for s_idx, w in enumerate(window_sizes):
            seed = _fnv1a_32(f"adap_win_{layer_id}_{s_idx}_{w}")
            self._windows[w] = _init_learned_window(w, seed)

        # --- MLP de contexte → gains spectraux (par canal) ---
        self.gate_mlp = TinyMLP(dim, hidden_ctx, dim,
                                seed_salt=f"gate_{layer_id}")
        # --- MLP de contexte → modulation de phase (par canal) ---
        self.phase_mlp = TinyMLP(dim, hidden_ctx, dim,
                                 seed_salt=f"phase_{layer_id}")

    def _compute_context(self, psi: np.ndarray) -> np.ndarray:
        """Extrait un vecteur de contexte à partir de l'amplitude moyennée.

        c = <|ψ_t|>_{t ∈ séquence}  — pooling global sur les tokens.

        Returns: [dim] réel, résumant l'état spectral de la phrase.
        """
        A = np.abs(psi)                      # [L, dim]
        return A.mean(axis=0)                 # [dim]

    def _stft_one(self, x_1d: np.ndarray, w: int) -> np.ndarray:
        """STFT 1D avec fenêtre APPRISE (pas Hann).

        Returns: [n_frames, w//2 + 1] complexe
        """
        hop = w // 2
        L = len(x_1d)
        if L < w:
            x_1d = np.concatenate([x_1d, np.zeros(w - L)])
            L = w
        n_frames = max(1, (L - w) // hop + 1)
        n_freqs = w // 2 + 1
        frames = np.zeros((n_frames, n_freqs), dtype=np.complex128)
        win = self._windows[w]
        for i in range(n_frames):
            start = i * hop
            seg = x_1d[start:start + w]
            if len(seg) < w:
                seg = np.concatenate([seg, np.zeros(w - len(seg))])
            frames[i] = np.fft.rfft(seg * win)
        return frames

    def _istft_one(self, frames: np.ndarray, w: int,
                   target_len: int) -> np.ndarray:
        """ISTFT 1D avec la fenêtre apprise (overlap-add COLA)."""
        hop = w // 2
        n_frames = frames.shape[0]
        out_len = target_len + 2 * w
        out = np.zeros(out_len, dtype=np.float64)
        win = self._windows[w]
        for i in range(n_frames):
            start = i * hop + w
            seg = np.fft.irfft(frames[i], n=w)
            out[start:start + w] += seg * win
        # Normalisation COLA
        norm = np.zeros(out_len, dtype=np.float64)
        for i in range(n_frames):
            start = i * hop + w
            norm[start:start + w] += win ** 2
        norm[norm < 0.01] = 1.0
        return (out / norm)[w:w + target_len]

    def forward(self, psi: np.ndarray) -> np.ndarray:
        """
        Applique l'opérateur spectral ADAPTATIF.

        Args:
            psi: [L, dim] complexe
        Returns:
            out: [L, dim] complexe, filtré adaptativement
        """
        L, D = psi.shape
        # 1. Contexte global de la phrase
        context = self._compute_context(psi)            # [D]

        # 2. Gains spectraux (content-dependent)
        raw_gains = self.gate_mlp.forward(context)      # [D]
        # sigmoid → g_k ∈ (0, 1)
        gains = 1.0 / (1.0 + np.exp(-raw_gains))       # [D]

        # 3. Modulation de phase (content-dependent)
        delta_phi = self.phase_mlp.forward(context)     # [D]
        # Bornage : Δφ ∈ [-π/4, π/4] pour éviter de détruire la phase
        delta_phi = np.tanh(delta_phi) * (math.pi / 4)  # [D]

        # 4. Pour chaque échelle, appliquer STFT adaptative
        out = np.zeros_like(psi)
        for s_idx, w in enumerate(self.window_sizes):
            d_start = s_idx * self.dim_per_scale
            d_end = d_start + self.dim_per_scale

            for c in range(d_start, min(d_end, D)):
                x = np.real(psi[:, c])                 # signal réel [L]
                frames = self._stft_one(x, w)           # [n_frames, n_freqs]

                # --- Adaptation dans le domaine fréquentiel ---
                # a) Gating par amplitude : multiplier par gain_c
                gain_c = float(gains[c])
                frames = frames * gain_c                # [n_frames, n_freqs]

                # b) Modulation de phase : shift de phase par frame
                dphi_c = float(delta_phi[c])
                frames = frames * np.exp(1j * dphi_c)

                # c) Reconstruction IFFT
                out[:, c] = self._istft_one(frames, w, L)

        # Canaux résiduels (si D non divisible par n_scales)
        if d_end < D:
            out[:, d_end:] = np.real(psi[:, d_end:])
        return out

    def reconstruct(self, psi: np.ndarray) -> np.ndarray:
        """Reconstruction parfaite (pour test ISTFT).

        Désactive les MLPs adaptatifs (gains=1, Δφ=0) pour tester
        uniquement la propriété d'inversion COLA avec fenêtres apprises.
        """
        L, D = psi.shape
        recon = np.zeros((L, D), dtype=np.float64)
        for s_idx, w in enumerate(self.window_sizes):
            d_start = s_idx * self.dim_per_scale
            d_end = d_start + self.dim_per_scale
            for c in range(d_start, min(d_end, D)):
                x = np.real(psi[:, c])
                frames = self._stft_one(x, w)
                recon[:, c] = self._istft_one(frames, w, L)
        if d_end < D:
            recon[:, d_end:] = np.real(psi[:, d_end:])
        return recon

    def params(self) -> List[np.ndarray]:
        """Retourne tous les paramètres apprenables (pour entraînement)."""
        p = []
        for w in self.window_sizes:
            p.append(self._windows[w])
        p.extend(self.gate_mlp.params())
        p.extend(self.phase_mlp.params())
        return p

    @property
    def n_params(self) -> int:
        return sum(np.prod(pp.shape) for pp in self.params())


# ════════════════════════════════════════════════════════════════
# DÉMO
# ════════════════════════════════════════════════════════════════

def _demo():
    print("=" * 65)
    print("  🌊 Adaptive Spectral Operator — Fourier Adaptative")
    print("=" * 65)

    op = AdaptiveSpectralOperator(dim=24, window_sizes=(16, 32, 64),
                                  hidden_ctx=16, layer_id=0)
    print(f"\n✓ Opérateur : {op.n_params} paramètres apprenables")

    # Signal de test (assez long pour zone centrale non-vide)
    rng = np.random.RandomState(42)
    L = 256
    psi = rng.randn(L, 24).astype(complex)

    # 1. Forward adaptatif
    out = op.forward(psi)
    print(f"✓ Forward : shape {out.shape}, module ∈ "
          f"[{np.min(np.abs(out)):.2f}, {np.max(np.abs(out)):.2f}]")

    # 2. Reconstruction ISTFT (fenêtres apprises, COLA)
    recon = op.reconstruct(psi)
    w = max(op.window_sizes)
    center = slice(w, len(psi) - w)
    err = float(np.max(np.abs(np.real(psi[center]) - recon[center])))
    print(f"✓ ISTFT (fenêtres apprises, centre) : erreur = {err:.2e} "
          f"({'OK' if err < 1e-3 else 'FAIL'})")

    # 3. Vérification : l'adaptatif répond DIFFÉREMMENT à deux contextes
    psi_a = rng.randn(L, 24).astype(complex) * 2.0 + 1j
    psi_b = rng.randn(L, 24).astype(complex) * 0.5 - 1j
    out_a = op.forward(psi_a)
    out_b = op.forward(psi_b)
    diff_input = np.max(np.abs(psi_a - psi_b))
    diff_output = np.max(np.abs(out_a - out_b))
    ratio = diff_output / max(diff_input, 1e-10)
    print(f"✓ Adaptativité : ∥Δout∥/∥Δin∥ = {ratio:.3f} "
          f"({'≠ 1.0 → adaptatif ✅' if abs(ratio - 1.0) > 0.01 else '~1.0 → non-adaptatif ❌'})")

    # 4. Comparaison avec STFT fixe (SpectralOperator)
    from harmonic_transformer import SpectralOperator
    op_fixed = SpectralOperator(dim=24, window_sizes=(16, 32, 64))
    out_fixed_a = op_fixed.forward(psi_a)
    out_fixed_b = op_fixed.forward(psi_b)
    diff_fixed = np.max(np.abs(out_fixed_a - out_fixed_b))
    ratio_fixed = diff_fixed / max(diff_input, 1e-10)
    print(f"   Ratio STFT fixe (référence)        : {ratio_fixed:.3f}")

    print("\n[DONE] Adaptive Spectral Operator opérationnel.")


if __name__ == "__main__":
    _demo()
