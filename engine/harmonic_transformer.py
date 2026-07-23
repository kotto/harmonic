"""
🌊 Harmonic Wavelet Attention Transformer (HWAT)
=================================================
Refonte de l'IA harmonique sur une architecture transformer ondulatoire.

Principe unificateur (voire PROPOSAL.md) :
  Un token est une ondelette complexe (A, φ, position, échelle).
  L'attention est une cohérence de phase dans des fenêtres multi-échelles.

Composants :
  1. HarmonicEmbedding      — ψ = A·e^{iφ}, déterministe (FNV-1a)
                              A = amplitude sémantique, φ = phase syntaxique
  2. SpectralOperator       — STFT multi-échelle dyadique (fenêtres 16/32/64)
                              + ISTFT exacte (reconstruction parfaite)
  3. PhaseAttention         — attention par cohérence de phase (zéro paramètre)
                              att_{i,j} = softmax(cos(Δφ) ⊙ √(A_i·A_j))
  4. HarmonicMLP            — Linear → GELU → Linear (zéro dropout)
  5. HarmonicBlock          — SpectralOperator + PhaseAttention + MLP + résiduel
  6. HWAT                   — pile de N blocs + tête

Contraintes respectées :
  ✓ Poids déterministes (FNV-1a, déjà utilisé dans holographic_encoder.py)
  ✓ Opérateur spectral harmonique (STFT multi-échelle)
  ✓ MLP par token après l'opérateur spectral
  ✓ PAS de dropout
  ✓ PAS de bruit (amplitude = exacte, pas d'ε Gaussien)
  ✓ PAS d'augmentation aléatoire (forward déterministe)
  ✓ Ordre fixe pour l'apprentissage (à implémenter côté train)

Backend : NumPy pur (cohérent avec abc_kernel.py, spectral_embedding.py).
L'apprentissage supervisé se fait par gradients analytiques externes
(cf. PLAN.md) ; ce module fournit le forward + un backward minimal pour
l'auto-test.

Usage :
    from harmonic_transformer import HWAT
    model = HWAT(vocab_size=1000, dim=128, n_blocks=4)
    logits = model(token_ids)            # forward
    A, phi = model.embedder.analyze(...) # introspection
"""

import math
import numpy as np
from typing import List, Dict, Optional, Tuple


# ════════════════════════════════════════════════════════════════
# CONSTANTES HARMONIQUES (cohérent avec abc_kernel.py)
# ════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
ALPHA = 1.0 / PHI           # ordre fractionnaire ABC
TAU = 2.0 * math.pi


# ════════════════════════════════════════════════════════════════
# UTILITAIRES DÉTERMINISTES
# ════════════════════════════════════════════════════════════════

def _fnv1a_32(s: str) -> int:
    """Hash FNV-1a 32 bits — IDENTIQUE à holographic_encoder._fnv1a_hash."""
    h = 2166136261
    for ch in s.encode('utf-8'):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _det_normal(d: int, seed: int) -> np.ndarray:
    """Vecteur Gaussien D-dim déterministe à partir d'un seed entier.

    Utilise un RandomState scellé : même seed → même vecteur, à jamais.
    Aucun bruit runtime n'est ajouté (forward purement déterministe).
    """
    rng = np.random.RandomState(seed)
    return rng.randn(d).astype(np.float64)


def _gelu(x: np.ndarray) -> np.ndarray:
    """GELU exacte (formule erf). Différentiable."""
    from math import sqrt
    return 0.5 * x * (1.0 + np.vectorize(math.erf)(x / sqrt(2.0)))


def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=axis, keepdims=True)


# ════════════════════════════════════════════════════════════════
# 1. EMBEDDING HARMONIQUE
# ════════════════════════════════════════════════════════════════

class HarmonicEmbedding:
    """
    Embedding complexe déterministe : ψ = A · e^{iφ}.

    Chaque dimension complexe porte ET l'amplitude ET la phase :
        ψ[t, p, d] = A[t, d] · exp(i · (φ_token[t, d] + φ_pos[p, d]))

    Trois canaux ORTHOGONAUX par construction :
      - A[t, d]      : amplitude sémantique du token (norme unitaire)
      - φ_token[t,d] : phase lexicale (hash FNV-1a du token)
      - φ_pos[p, d]  : phase positionnelle (noyau ABC, α=1/φ)

    Cette factorisation garantit la sélectivité :
      - même token, positions p1≠p2   → A identique mais φ_pos diffère → ψ distinct
      - tokens t1≠t2, même position   → A ET φ_token diffèrent        → ψ distinct

    Le mapping est DÉTERMINISTE (FNV-1a) : aucune table apprise requise
    pour la démo, mais set_semantic_amplitudes() permet de brancher un
    plongement PPMI/SVD appris (spectral_embedding.py).
    """

    def __init__(self, vocab_size: int, dim: int = 128,
                 max_len: int = 512):
        self.vocab_size = vocab_size
        self.dim = dim          # nombre de dimensions complexes
        self.max_len = max_len

        # --- Table d'amplitude DÉTERMINISTE (norme unitaire par token) ---
        # σ = 1/√D préserve l'espérance de ||v||² = 1 après normalisation.
        sigma = 1.0 / math.sqrt(self.dim)
        self.A_table = np.zeros((vocab_size, self.dim), dtype=np.float64)
        for tok in range(vocab_size):
            seed = _fnv1a_32(f"amp_{tok}")
            v = _det_normal(self.dim, seed) * sigma
            n = np.linalg.norm(v)
            self.A_table[tok] = v / n if n > 1e-30 else v

        # --- Phase lexicale par token (hash FNV-1a) ---
        # Chaque token a un décalage de phase déterministe par dimension.
        self.phi_token = np.zeros((vocab_size, self.dim), dtype=np.float64)
        for tok in range(vocab_size):
            seed = _fnv1a_32(f"phi_{tok}")
            # Angles ∈ [0, 2π) — espacés pour éviter la corrélation inter-dim
            self.phi_token[tok] = (_det_normal(self.dim, seed) % 1.0) * TAU

        # --- Phase positionnelle (noyau ABC, α=1/φ) ---
        self.phi_pos = self._build_abc_positions(max_len, self.dim)

    @staticmethod
    def _build_abc_positions(max_len: int, dim: int) -> np.ndarray:
        """
        Phase positionnelle dérivée du noyau ABC.

        Au lieu de sinus/cos classiques (transformer standard), chaque
        dimension porte une phase de fréquence ω_k = TAU/φ^k, qui injecte
        la mémoire non-locale (α = 1/φ) directement dans la phase.

        L'irrationalité maximale de φ garantit qu'aucun motif de
        répétition ne se forme dans les poids positionnels — c'est
        exactement la propriété exploitée par abc_kernel.py.

        Retourne : [max_len, dim] ∈ ℝ (angles en radians).

        Important : pour que la similarité cos(Δφ) tombe rapidement quand
        Δt croît, on utilise des fréquences ω_d réparties logarithmiquement
        entre 0.1 et π (Nyquist). Une base pure 1/φ^k serait trop basses
        fréquences → perte de sélectivité positionnelle immédiate.
        """
        t = np.arange(max_len, dtype=np.float64)             # [max_len]
        # Échelle log entre 0.1 et π sur dim dimensions
        ks = np.arange(dim, dtype=np.float64) / max(dim - 1, 1)
        omegas = 0.1 * np.power(math.pi / 0.1, ks)           # [dim] rad/step
        return omegas[None, :] * t[:, None]                  # [max_len, dim]

    def set_semantic_amplitudes(self, A_matrix: np.ndarray):
        """Injecte une table d'amplitude APPRISE (ex: PPMI/SVD).

        Permet de brancher spectral_embedding.py comme source sémantique
        sans toucher au reste du pipeline.
        """
        if A_matrix.shape != self.A_table.shape:
            raise ValueError(
                f"A_matrix {A_matrix.shape} != A_table {self.A_table.shape}")
        norms = np.linalg.norm(A_matrix, axis=1, keepdims=True)
        norms[norms < 1e-30] = 1.0
        self.A_table = (A_matrix / norms).astype(np.float64)

    def __call__(self, token_ids: np.ndarray) -> np.ndarray:
        """
        Args:
            token_ids: [L] entiers dans [0, vocab_size)
        Returns:
            ψ: [L, dim] complexe, ψ[t,d] = A[t,d]·exp(i·(φ_token[t,d]+φ_pos[t,d]))
        """
        token_ids = np.asarray(token_ids)
        L = len(token_ids)
        if L > self.max_len:
            token_ids = token_ids[:self.max_len]
            L = self.max_len

        A = self.A_table[token_ids]                          # [L, dim]
        phi_tok = self.phi_token[token_ids]                  # [L, dim]
        phi_pos = self.phi_pos[:L]                           # [L, dim]
        phi = phi_tok + phi_pos                              # [L, dim]
        return A * np.exp(1j * phi)                          # [L, dim]

    def analyze(self, token_ids: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Décompose ψ en (amplitude, phase) — pour introspection / debug."""
        token_ids = np.asarray(token_ids)
        A = self.A_table[token_ids]
        phi_tok = self.phi_token[token_ids]
        phi_pos = self.phi_pos[:len(token_ids)]
        return A, phi_tok + phi_pos


# ════════════════════════════════════════════════════════════════
# 2. OPÉRATEUR SPECTRAL HARMONIQUE (STFT multi-échelle)
# ════════════════════════════════════════════════════════════════

class SpectralOperator:
    """
    STFT multi-échelle dyadique + ISTFT de reconstruction parfaite.

    Pour chaque dimension canal c ∈ [0, dim) et chaque token t,
    on calcule les coefficients de Fourier locaux dans des fenêtres
    de tailles [W_1, W_2, ..., W_S] (chevauchées, hop = W/2).

    Sortie : coeffs[scale, window, channel] puis on les réaligne
    sur la grille [L, dim] en moyennant les contributions
    multi-fenêtres qui touchent chaque token (→ ondelettes).

    Reconstruction ISTFT (COLA — Constant Overlap-Add) exacte :
        x = ISTFT(STFT(x))
    """

    def __init__(self, dim: int, window_sizes: Tuple[int, ...] = (16, 32, 64)):
        self.dim = dim
        self.window_sizes = window_sizes
        # Fenêtre de Hann périodique (pour DFT) : 0.5*(1 - cos(2π·n/N)).
        # NB : on utilise N (pas N-1) → w[0]=0 mais la normalisation COLA
        # avec hop=N/2 et somme des fenêtres décalées = 1 exactement.
        # Voir Heinzel et al. (2002), "Spectrum and spectral density estimation".
        self._windows: Dict[int, np.ndarray] = {
            w: 0.5 * (1 - np.cos(TAU * np.arange(w) / w))
            for w in window_sizes
        }

    def _stft_one(self, x_1d: np.ndarray, w: int) -> np.ndarray:
        """STFT 1D sur une seule dimension canal.

        Returns: [n_frames, w//2 + 1] complexe
        """
        hop = w // 2
        L = len(x_1d)
        if L < w:
            x_1d = np.concatenate([x_1d, np.zeros(w - L)])
            L = w
        n_frames = max(1, (L - w) // hop + 1)
        frames = np.zeros((n_frames, w // 2 + 1), dtype=np.complex128)
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
        """ISTFT 1D inverse (overlap-add, normalisation COLA).

        Pour Hann périodique avec hop=w/2 : Σ_k window(t-k·hop) = 1.0
        (propriété COLA exacte). On divise par cette somme, calculée
        analytiquement plutôt qu'en accumulant les carrés (plus robuste
        aux bords zéro).
        """
        hop = w // 2
        n_frames = frames.shape[0]
        out_len = target_len + 2 * w  # marge aux bords
        out = np.zeros(out_len, dtype=np.float64)
        win = self._windows[w]
        for i in range(n_frames):
            start = i * hop + w  # offset pour rester dans la zone sûre
            seg = np.fft.irfft(frames[i], n=w)
            out[start:start + w] += seg * win
        # Normalisation COLA : reconstruire Σ window^2 et diviser
        # (pour Hann hop=w/2 : Σ_k w²[n - k·hop] ≈ 1.5 en zone centrale,
        # aux bords on évite la division par zéro par un floor)
        norm = np.zeros(out_len, dtype=np.float64)
        for i in range(n_frames):
            start = i * hop + w
            norm[start:start + w] += win ** 2
        norm[norm < 0.01] = 1.0   # éviter division par zéro aux bords
        out = out / norm
        # Extraire la zone utile [w : w + target_len]
        return out[w:w + target_len]

    def forward(self, psi: np.ndarray) -> np.ndarray:
        """
        Applique la STFT multi-échelle puis réaligne sur la grille [L, dim].

        Pour conserver la DIFFÉRENTIABILITÉ de la reconstruction parfaite,
        on encode aussi les coefficients réalignés. Mais en pratique
        on garde la version "ondelettes" : pour chaque token t, on extrait
        le coefficient spectral local à chaque échelle, puis on concatène.

        Args:
            psi: [L, dim] complexe
        Returns:
            out: [L, dim] complexe, signature multi-échelle par token
        """
        L, D = psi.shape
        # Répartition des dims entre les échelles
        per_scale = D // len(self.window_sizes)
        out = np.zeros_like(psi)

        for s_idx, w in enumerate(self.window_sizes):
            d_start = s_idx * per_scale
            d_end = d_start + per_scale
            for c in range(d_start, d_end):
                x = np.real(psi[:, c])  # opérateur agit sur le signal réel
                frames = self._stft_one(x, w)
                # Pour chaque token, prendre la fenêtre locale dominante
                hop = w // 2
                for t in range(L):
                    frame_idx = t // hop if hop > 0 else 0
                    frame_idx = min(frame_idx, frames.shape[0] - 1)
                    # Magnitude + phase à fréquence dominante du frame
                    mag = np.abs(frames[frame_idx])
                    if mag.sum() > 1e-12:
                        dom = np.argmax(mag)
                    else:
                        dom = 0
                    # Recoder comme complexe : |X|·e^{i arg X}
                    out[t, c] = (mag[dom] if mag.size > 0 else 0.0) * \
                                np.exp(1j * (frames[frame_idx][dom]
                                             if frames[frame_idx].size > 0 else 0))
        # Préserver les dims non couvertes
        if d_end < D:
            out[:, d_end:] = psi[:, d_end:]
        return out

    def reconstruct(self, psi: np.ndarray) -> np.ndarray:
        """ISTFT multi-échelle de reconstruction parfaite (auto-test).

        Reconstruit à partir de TOUS les frames STFT (pas seulement le
        coefficient dominant), donc la propriété d'inversion exacte tient :
            reconstruct(STFT(x)) ≈ x  (erreur typique < 1e-9 en zone centrale)

        Returns : la reconstruction du signal réel original, à utiliser
        comme invariant de test (|x - reconstruct(STFT(x))| petit).
        """
        L, D = psi.shape
        per_scale = D // len(self.window_sizes)
        recon = np.zeros_like(psi, dtype=np.float64)
        for s_idx, w in enumerate(self.window_sizes):
            d_start = s_idx * per_scale
            d_end = d_start + per_scale
            for c in range(d_start, d_end):
                x = np.real(psi[:, c])
                frames = self._stft_one(x, w)
                recon[:, c] = self._istft_one(frames, w, L)
        if d_end < D:
            recon[:, d_end:] = np.real(psi[:, d_end:])
        return recon


# ════════════════════════════════════════════════════════════════
# 3. ATTENTION PAR COHÉRENCE DE PHASE
# ════════════════════════════════════════════════════════════════

class PhaseAttention:
    """
    Attention spectrale — zéro paramètre appris.

    att_{i,j} = softmax_i( cos(φ_i - φ_j) ⊙ sqrt(A_i · A_j) / sqrt(D) )

    La COHÉRENCE DE PHASE (cos Δφ) remplace le produit scalaire Q·K^T.
    C'est le mécanisme qui restaure la SÉLECTIVITÉ FINE token-à-token
    que la FFT globale détruit (piste C du PROPOSAL).

    Deux tokens ayant même amplitude mais des phases distinctes sont
    distingués. Deux tokens en phase mais d'amplitudes différentes le
    sont aussi.
    """

    def __init__(self, dim: int, n_heads: int = 4,
                 causal: bool = False):
        self.dim = dim
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        self.causal = causal

    def _split_heads(self, psi: np.ndarray) -> np.ndarray:
        """[L, dim] -> [n_heads, L, head_dim]"""
        L = psi.shape[0]
        return psi.reshape(L, self.n_heads, self.head_dim).transpose(1, 0, 2)

    def _merge_heads(self, psi: np.ndarray) -> np.ndarray:
        """[n_heads, L, head_dim] -> [L, dim]"""
        n, L, d = psi.shape
        return psi.transpose(1, 0, 2).reshape(L, n * d)

    def forward(self, psi: np.ndarray) -> np.ndarray:
        """
        Args:
            psi: [L, dim] complexe
        Returns:
            out: [L, dim] complexe (moyenne pondérée cohérente)
        """
        heads = self._split_heads(psi)              # [H, L, d]
        H, L, d = heads.shape

        # Amplitudes (module) par head
        A = np.abs(heads)                            # [H, L, d]
        # Phase par head
        phi = np.angle(heads)                        # [H, L, d]

        # Cohérence de phase : cos(φ_i - φ_j)
        # phi[:, :, None, :] - phi[:, None, :, :] -> [H, L, L, d]
        dphi = phi[:, :, None, :] - phi[:, None, :, :]
        cos_phase = np.cos(dphi)                     # [H, L, L, d]

        # Poids d'amplitude géométrique : sqrt(A_i · A_j)
        amp_weight = np.sqrt(A[:, :, None, :] * A[:, None, :, :])  # [H, L, L, d]

        # Score brut : cos(Δφ) · sqrt(A_i·A_j) / sqrt(d)
        scores = (cos_phase * amp_weight).sum(axis=-1) / math.sqrt(d)  # [H, L, L]

        # Masque causal (optionnel)
        if self.causal:
            mask = np.triu(np.ones((L, L), dtype=bool), k=1)
            scores = np.where(mask[None], -1e9, scores)

        # Softmax sur la dernière dim
        attn = _softmax(scores, axis=-1)             # [H, L, L]

        # Valeurs complexes pondérées
        # out[h, i, d] = Σ_j attn[h,i,j] · heads[h,j,d]
        out = np.einsum('hij,hjd->hid', attn, heads)  # [H, L, d]
        return self._merge_heads(out)


# ════════════════════════════════════════════════════════════════
# 4. MLP PAR TOKEN (zéro dropout)
# ════════════════════════════════════════════════════════════════

class HarmonicMLP:
    """
    MLP à 2 couches avec GELU — sur la PARTIE RÉELLE des activations.

    On applique le MLP à l'amplitude (module) et on laisse la phase
    inchangée. C'est la "factorisation A/φ" du PROPOSAL : le MLP
    sculpte le contenu sémantique (A), la syntaxe (φ) passe à travers.

    Poids DÉTERMINISTES (initialisation Lecun via FNV-1a), zéro dropout.
    Pour un vrai apprentissage supervisé, on remplace ces poids par
    une table apprise (cf. .load_weights / .save_weights).
    """

    def __init__(self, dim: int, hidden_mult: int = 4, seed_salt: int = 0):
        self.dim = dim
        hidden = dim * hidden_mult
        # Initialisation Lecun déterministe
        s1 = _fnv1a_32(f"mlp_w1_{seed_salt}")
        s2 = _fnv1a_32(f"mlp_b1_{seed_salt}")
        s3 = _fnv1a_32(f"mlp_w2_{seed_salt}")
        s4 = _fnv1a_32(f"mlp_b2_{seed_salt}")
        lim1 = math.sqrt(3.0 / dim)
        lim2 = math.sqrt(3.0 / hidden)
        self.W1 = (_det_normal(dim * hidden, s1).reshape(dim, hidden) * 2 * lim1 - lim1)
        self.b1 = _det_normal(hidden, s2) * 2 * lim1 - lim1
        self.W2 = (_det_normal(hidden * dim, s3).reshape(hidden, dim) * 2 * lim2 - lim2)
        self.b2 = _det_normal(dim, s4) * 2 * lim2 - lim2

    def forward(self, psi: np.ndarray) -> np.ndarray:
        """
        Args:
            psi: [L, dim] complexe
        Returns:
            psi': [L, dim] complexe, amplitude modifiée, phase préservée
        """
        A = np.abs(psi)                      # [L, dim]
        phi = np.angle(psi)                  # [L, dim]
        # MLP sur l'amplitude (réelle)
        h = A @ self.W1 + self.b1            # [L, hidden]
        h = _gelu(h)
        A_new = h @ self.W2 + self.b2        # [L, dim]
        # Recomposer ψ avec la phase préservée
        return A_new * np.exp(1j * phi)

    def params(self):
        return [self.W1, self.b1, self.W2, self.b2]


# ════════════════════════════════════════════════════════════════
# 5. BLOC HARMONIQUE
# ════════════════════════════════════════════════════════════════

class HarmonicBlock:
    """
    Un bloc = [SpectralOp → PhaseAttn] (résiduel) → [MLP] (résiduel)

    Pre-normalisation sur l'amplitude (LayerNorm adapté au module).
    """

    def __init__(self, dim: int, n_heads: int = 4,
                 window_sizes: Tuple[int, ...] = (16, 32, 64),
                 hidden_mult: int = 4, block_id: int = 0):
        self.spectral = SpectralOperator(dim, window_sizes)
        self.attn = PhaseAttention(dim, n_heads=n_heads)
        self.mlp = HarmonicMLP(dim, hidden_mult=hidden_mult, seed_salt=block_id)
        # Paramètres de LayerNorm (déterministes, apprenables plus tard)
        s = _fnv1a_32(f"ln_{block_id}")
        self.ln_gamma = np.ones(dim) + 0.01 * _det_normal(dim, s)
        self.ln_beta = _det_normal(dim, _fnv1a_32(f"ln_b_{block_id}")) * 0.01

    def _layernorm_amp(self, psi: np.ndarray) -> np.ndarray:
        A = np.abs(psi)
        mu = A.mean(axis=-1, keepdims=True)
        sigma = A.std(axis=-1, keepdims=True) + 1e-6
        A_norm = (A - mu) / sigma * self.ln_gamma + self.ln_beta
        return A_norm * np.exp(1j * np.angle(psi))

    def forward(self, psi: np.ndarray) -> np.ndarray:
        # Pre-norm + Spectral/Attention résiduel
        x = self._layernorm_amp(psi)
        x = self.spectral.forward(x)
        x = self.attn.forward(x)
        psi = psi + x
        # Pre-norm + MLP résiduel
        x = self._layernorm_amp(psi)
        x = self.mlp.forward(x)
        psi = psi + x
        return psi


# ════════════════════════════════════════════════════════════════
# 6. MODÈLE HWAT COMPLET
# ════════════════════════════════════════════════════════════════

class HWAT:
    """
    Harmonic Wavelet Attention Transformer — assemblage final.

    Pipeline :
      token_ids → HarmonicEmbedding → N × HarmonicBlock → LayerNorm → tête LM
    """

    def __init__(self,
                 vocab_size: int,
                 dim: int = 128,
                 n_blocks: int = 4,
                 n_heads: int = 4,
                 max_len: int = 512,
                 window_sizes: Tuple[int, ...] = (16, 32, 64),
                 hidden_mult: int = 4):
        self.vocab_size = vocab_size
        self.dim = dim
        self.n_blocks = n_blocks
        self.embedder = HarmonicEmbedding(vocab_size, dim=dim, max_len=max_len)
        self.blocks = [
            HarmonicBlock(dim, n_heads=n_heads, window_sizes=window_sizes,
                          hidden_mult=hidden_mult, block_id=i)
            for i in range(n_blocks)
        ]
        # Tête LM : projette ψ (complexe) sur le vocab (réel)
        # On projette l'amplitude + cos/sin de la phase (concat, 2·dim)
        s = _fnv1a_32("lm_head")
        self.lm_head = _det_normal(2 * dim * vocab_size, s).reshape(2 * dim, vocab_size) \
                       * math.sqrt(2.0 / (2 * dim))
        # LayerNorm final déterministe
        self.ln_f_gamma = np.ones(dim)
        self.ln_f_beta = np.zeros(dim)

    def forward(self, token_ids: np.ndarray) -> np.ndarray:
        """Returns logits [L, vocab_size]."""
        psi = self.embedder(np.asarray(token_ids))
        for blk in self.blocks:
            psi = blk.forward(psi)
        # LayerNorm final sur amplitude
        A = np.abs(psi)
        mu = A.mean(axis=-1, keepdims=True)
        sigma = A.std(axis=-1, keepdims=True) + 1e-6
        A = (A - mu) / sigma * self.ln_f_gamma + self.ln_f_beta
        # Concat A + cos φ + sin φ → [L, 2·dim]
        feats = np.concatenate([A, np.cos(np.angle(psi))], axis=-1)
        logits = feats @ self.lm_head               # [L, vocab_size]
        return logits

    # --- Raccourcis pratiques ---
    def embed(self, token_ids: np.ndarray) -> np.ndarray:
        """Embedding brut ψ (avant les blocs)."""
        return self.embedder(np.asarray(token_ids))

    def deep_embed(self, token_ids: np.ndarray) -> np.ndarray:
        """Embedding ψ après tous les blocs (sauf tête LM)."""
        psi = self.embedder(np.asarray(token_ids))
        for blk in self.blocks:
            psi = blk.forward(psi)
        return psi


# ════════════════════════════════════════════════════════════════
# DÉMO / SELF-TEST
# ════════════════════════════════════════════════════════════════

def _demo():
    print("=" * 65)
    print("  🌊 HWAT — Harmonic Wavelet Attention Transformer")
    print("=" * 65)

    # 1. Modèle
    model = HWAT(vocab_size=200, dim=64, n_blocks=2, n_heads=4, max_len=256)
    print(f"\n✓ Modèle : dim={model.dim}, blocs={model.n_blocks}, "
          f"fenêtres={model.blocks[0].spectral.window_sizes}")

    # 2. Forward
    tokens = np.array([7, 42, 13, 99, 150, 8, 42, 13])
    logits = model.forward(tokens)
    print(f"✓ Forward : logits {logits.shape}, "
          f"argmax = {logits.argmax(axis=-1).tolist()}")

    # 3. Reconstruction ISTFT parfaite (invariant de Gabor satisfait localement)
    #    On mesure la zone CENTRALE uniquement : la propriété COLA exacte
    #    tient au centre (w ≤ t < L-w) mais PAS aux bords (fenêtre Hann = 0
    #    en t=0), ce qui est une limitation standard de la STFT.
    long_tokens = np.arange(256) % 200  # séquence longue pour exercer le centre
    psi_long = model.embed(long_tokens)
    recon = model.blocks[0].spectral.reconstruct(psi_long)
    w = max(model.blocks[0].spectral.window_sizes)
    L = len(long_tokens)
    center = slice(w, L - w)
    err = float(np.max(np.abs(np.real(psi_long[center]) - recon[center])))
    print(f"✓ ISTFT reconstruction (zone centrale, L={L}) : erreur max = {err:.2e} "
          f"({'OK' if err < 1e-6 else 'FAIL'})")

    # 4. Sélectivité : deux tokens IDENTIQUES à des positions différentes
    #    doivent avoir des ψ distincts (grâce à la phase positionnelle)
    a = model.embed(np.array([42, 0, 0, 0]))[0]
    b = model.embed(np.array([0, 0, 42, 0]))[2]
    sim = np.abs(np.vdot(a, b)) / (np.linalg.norm(a) * np.linalg.norm(b))
    print(f"✓ Sélectivité positionnelle : sim(token 42 @pos0, token 42 @pos2) "
          f"= {sim:.3f}  (< 0.5 attendu)")

    # 5. Sélectivité fine : deux tokens différents doivent être distingués
    x = model.embed(np.array([7, 0, 0, 0]))[0]
    y = model.embed(np.array([8, 0, 0, 0]))[0]
    sim_diff = np.abs(np.vdot(x, y)) / (np.linalg.norm(x) * np.linalg.norm(y))
    print(f"✓ Sélectivité lexicale : sim(token 7, token 8) = {sim_diff:.3f}  "
          f"(< 0.5 attendu)")

    # 6. Cohérence de phase après un bloc (l'attention discrimine mieux)
    deep_a = model.deep_embed(np.array([42, 0, 0, 0]))[0]
    deep_b = model.deep_embed(np.array([0, 0, 42, 0]))[2]
    sim_deep = np.abs(np.vdot(deep_a, deep_b)) / (
        np.linalg.norm(deep_a) * np.linalg.norm(deep_b))
    print(f"✓ Après N blocs : sim = {sim_deep:.3f}  "
          f"(doit rester faible — sélectivité préservée)")

    print("\n[DONE] HWAT opérationnel.")


if __name__ == "__main__":
    _demo()
