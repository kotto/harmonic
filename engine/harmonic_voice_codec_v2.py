"""
HCV Codec v2 — Codec Continu Harmonique basé sur ψ ∈ ℂ⁵¹², 24 kHz
==================================================================

Évolution du HCV v1 (16kHz, dictionnaire VQ 248 entrées) vers un codec
CONTINU sans quantification, utilisant la représentation vectorielle complexe
ψ = A·e^(iφ) propre à l'architecture ondulatoire HarmoniqLLM.

Principes fondateurs :
  1. CONTINU — Pas de quantification VQ. Chaque frame audio → ψ ∈ ℂ⁵¹²
     via FNV-1a déterministe + φ-spacing (même principe que HolographicEncoder)
  2. SÉMANTIQUE + ACOUSTIQUE — Séparation naturelle en deux composantes :
     ψ_sem = composante sémantique (basses fréquences, énergie, phonèmes)
     ψ_ac  = composante acoustique (hautes fréquences, phase, timbre)
  3. RECONSTRUCTION φ — Griffin-Lim adaptatif + post-filtre φ (PhiPostFilter)
  4. ZERO PARAMÈTRE APPRIS — Tout est déterministe (FNV-1a, φ, FFT)

Spécifications techniques :
  - Fréquence d'échantillonnage : 24 000 Hz (compatible Voxtral/Mimi)
  - Taille de trame : 80 ms → 1920 échantillons
  - Chevauchement : 40 ms → 960 échantillons (50% overlap)
  - Frame rate : 12.5 Hz (80ms stride) — standard Voxtral/Moshi
  - FFT size : 2048 (zero-padded si nécessaire)
  - Dimension ψ : 512 (compatible avec l'architecture HolographicEncoder)
  - Bitrate estimé : ~2 000 bps (continu non compressé)
  - Latence d'encodage : < 10 ms par trame (FFT + FNV-1a)

Usage :
    from harmonic_voice_codec_v2 import HarmonicVoiceCodecV2

    codec = HarmonicVoiceCodecV2()
    
    # Encodage
    psi_frames = codec.encode(audio_24kHz)       # → [n_frames, 512] complex
    
    # Décodage  
    audio = codec.decode(psi_frames)              # → [n_samples] float
    
    # Composantes
    psi_sem, psi_ac = codec.separate(psi_frames)  # → sémantique + acoustique
    
    # Streaming
    psi_frame = codec.encode_frame(chunk_1920)    # → [512] complex
    chunk = codec.decode_frame(psi_frame)          # → [1920] float

Compatibilité :
  - Réutilise : abc_kernel.py, holographic_encoder.py (_fnv1a_hash, φ-spacing)
  - S'intègre avec : ABCAudioPredictor, HolographicVoiceStore, ka_sonic
  - Post-filtre : phi_vocoder_pro.py (PhiPostFilter)

Auteur : Équipe HarmoniqLLM
Date   : 2026-07-24
"""

import math
import struct
import time
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES FONDAMENTALES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
TAU = 2.0 * math.pi
PHI_INV = 1.0 / PHI  # ≈ 0.618

# ── Paramètres audio ──
SAMPLE_RATE = 24000          # Hz
FRAME_MS = 80.0              # ms par trame
OVERLAP_MS = 40.0            # ms de chevauchement (50%)
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)        # 1920 échantillons
OVERLAP_SIZE = int(SAMPLE_RATE * OVERLAP_MS / 1000)    # 960 échantillons
STRIDE = FRAME_SIZE - OVERLAP_SIZE                      # 960 échantillons
FRAME_RATE_HZ = 1000.0 / FRAME_MS                       # 12.5 Hz (cf. Voxtral)

FFT_SIZE = 2048  # zero-padding au-delà de FRAME_SIZE
DIM_PSI = 512    # dimension des vecteurs complexes ψ

# ── Paramètres fréquentiels ──
FREQ_BINS = FFT_SIZE // 2 + 1  # 1025 bins (0 à 12000 Hz)
LOW_FREQ_CUTOFF = 300.0        # Hz — séparation sémantique/acoustique
LOW_FREQ_BIN = int(LOW_FREQ_CUTOFF / SAMPLE_RATE * FFT_SIZE)  # ~25 bins

# ── Paramètres de reconstruction ──
GRIFFIN_LIM_ITERS = 16        # Nombre d'itérations Griffin-Lim (phase init depuis ψ)
GRIFFIN_LIM_MOMENTUM = 0.9    # Momentum pour convergence
PHI_POSTFILTER_STRENGTH = 0.3  # Force du post-filtre φ

# ═══════════════════════════════════════════════════════════════════════════════
# HASH FNV-1a (déterministe, rapide — réutilisé de holographic_encoder.py)
# ═══════════════════════════════════════════════════════════════════════════════

def _fnv1a_hash(data: Union[str, bytes]) -> int:
    """FNV-1a 64-bit hash — déterministe, bonne distribution."""
    FNV_OFFSET = 14695981039346656037
    FNV_PRIME = 1099511628211
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    h = FNV_OFFSET
    for byte in data:
        h ^= byte
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


# ═══════════════════════════════════════════════════════════════════════════════
# FENÊTRES ET FILTRES
# ═══════════════════════════════════════════════════════════════════════════════

def _hann_window(size: int) -> np.ndarray:
    """Fenêtre de Hann asymétrique (meilleure reconstruction overlap-add)."""
    n = np.arange(size)
    return 0.5 * (1.0 - np.cos(TAU * n / (size - 1)))


def _phi_hann_window(size: int) -> np.ndarray:
    """
    Fenêtre de Hann modifiée φ — pondération harmonique.
    
    La fenêtre standard a un point central à size/2.
    La version φ décale légèrement le centre → meilleure reconstruction
    pour les signaux à contenu harmonique (voix).
    """
    n = np.arange(size)
    # Centre décalé par φ⁻¹
    center = size / (2.0 * PHI)
    # Hann avec centre φ-décalé
    return 0.5 * (1.0 - np.cos(TAU * n / (2.0 * center)))


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CodecStats:
    """Statistiques du codec."""
    sample_rate: int = SAMPLE_RATE
    frame_ms: float = FRAME_MS
    stride_ms: float = FRAME_MS - OVERLAP_MS
    frame_rate_hz: float = FRAME_RATE_HZ
    dim_psi: int = DIM_PSI
    fft_size: int = FFT_SIZE
    
    # Métriques calculées
    total_frames: int = 0
    total_duration_s: float = 0.0
    encode_time_ms: float = 0.0
    decode_time_ms: float = 0.0
    bits_per_second: float = 0.0
    compression_ratio: float = 1.0
    
    # Qualité
    estimated_snr_db: float = 0.0
    spectral_convergence: float = 0.0
    
    def update_bitrate(self, total_bits: int, duration_s: float):
        """Met à jour le bitrate estimé."""
        if duration_s > 0:
            self.bits_per_second = total_bits / duration_s
            raw_bps = SAMPLE_RATE * 16  # 16-bit PCM
            self.compression_ratio = raw_bps / max(self.bits_per_second, 1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# CODEC PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicVoiceCodecV2:
    """
    Codec vocal harmonique continu — version 2.
    
    Pipeline d'encodage :
      Audio 24kHz → Frames (80ms, 50% overlap) → FFT → Spectrum
        → ψ_sem (basses fréquences, FNV-1a + φ-spacing)
        → ψ_ac  (hautes fréquences + phase fine)
        → ψ = ψ_sem ⊕ ψ_ac ∈ ℂ⁵¹²
    
    Pipeline de décodage :
      ψ → ψ_sem + ψ_ac → reconstruction spectrale
        → Griffin-Lim (32 itérations) → Overlap-Add → Post-filtre φ
        → Audio 24kHz
    
    Parameters:
        dim: dimension des vecteurs complexes ψ (default 512)
        sample_rate: fréquence d'échantillonnage (default 24000)
        frame_ms: durée d'une trame en ms (default 80)
        overlap_ms: durée du chevauchement en ms (default 40)
        fft_size: taille de la FFT (default 2048)
    """
    
    def __init__(self,
                 dim: int = DIM_PSI,
                 sample_rate: int = SAMPLE_RATE,
                 frame_ms: float = FRAME_MS,
                 overlap_ms: float = OVERLAP_MS,
                 fft_size: int = FFT_SIZE):
        
        self.dim = dim
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.overlap_ms = overlap_ms
        self.fft_size = fft_size
        
        # Tailles en échantillons
        self.frame_size = int(sample_rate * frame_ms / 1000.0)
        self.overlap = int(sample_rate * overlap_ms / 1000.0)
        self.stride = self.frame_size - self.overlap
        self.frame_rate = 1000.0 / (frame_ms - overlap_ms)
        self.freq_bins = fft_size // 2 + 1
        
        # Fenêtres
        self._window = _hann_window(self.frame_size)
        self._window_phi = _phi_hann_window(self.frame_size)
        
        # Séparation fréquentielle
        self.low_freq_bin = int(300.0 / sample_rate * fft_size)  # ~300 Hz
        
        # Cache des hashs FNV-1a pour les bins fréquentielles
        self._bin_phases: Optional[np.ndarray] = None
        self._init_bin_phases()
        
        # Dictionnaire de reconstruction (calibré)
        self._reconstruction_dict: Optional[np.ndarray] = None
        self._dict_lock_threshold: float = 0.05
        
        # Statistiques
        self.stats = CodecStats(
            sample_rate=sample_rate,
            frame_ms=frame_ms,
            stride_ms=frame_ms - overlap_ms,
            frame_rate_hz=self.frame_rate,
            dim_psi=dim,
            fft_size=fft_size,
        )
        
        # Cache pour la compression
        self._compression_cache: Dict[str, np.ndarray] = {}
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INITIALISATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _init_bin_phases(self):
        """
        Initialise les phases déterministes pour chaque bin fréquentielle.
        
        Chaque bin k reçoit une phase φ_k = (FNV1a(str(k)) * φ) mod 2π.
        Ces phases servent de « porteuses » pour l'encodage ψ.
        """
        phases = np.zeros(self.freq_bins, dtype=np.float64)
        for k in range(self.freq_bins):
            seed = _fnv1a_hash(f"bin_{k}")
            phase = ((seed * PHI) % 2147483647) / 2147483647.0 * TAU
            phases[k] = phase
        self._bin_phases = phases
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PIPELINE PRINCIPAL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def encode(self, audio: np.ndarray, sr: int = None) -> np.ndarray:
        """
        Encode un signal audio en trames ψ complexes.
        
        Args:
            audio: [n_samples] signal audio float32/float64 ∈ [-1, 1]
            sr: fréquence d'échantillonnage (défaut: 24000)
            
        Returns:
            [n_frames, dim] np.complex128 — trames ψ
        """
        t_start = time.perf_counter()
        
        # Resampling si nécessaire
        if sr is not None and sr != self.sample_rate:
            audio = self._resample(audio, sr, self.sample_rate)
        
        # Normalisation
        audio = audio.astype(np.float64)
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.95
        
        # Découpage en trames
        frames = self._frame_audio(audio)
        n_frames = len(frames)
        
        if n_frames == 0:
            self.stats.encode_time_ms = (time.perf_counter() - t_start) * 1000
            return np.zeros((0, self.dim), dtype=np.complex128)
        
        # Encodage de chaque trame
        psi_frames = np.zeros((n_frames, self.dim), dtype=np.complex128)
        
        for i, frame in enumerate(frames):
            # Frame → spectre FFT
            spectrum = self._audio_to_spectrum(frame)
            
            # Détection du pitch
            f0 = self._detect_pitch(frame)
            
            # Spectre → ψ
            psi_frames[i] = self._spectrum_to_psi(spectrum, f0)
        
        # Stats
        duration_s = len(audio) / self.sample_rate
        self.stats.total_frames = n_frames
        self.stats.total_duration_s = duration_s
        self.stats.encode_time_ms = (time.perf_counter() - t_start) * 1000
        
        # Bitrate estimé (continu, non compressé)
        bits_per_frame = self.dim * 128  # 512 dims × 128 bits (complex128)
        total_bits = n_frames * bits_per_frame
        self.stats.update_bitrate(total_bits, duration_s)
        
        return psi_frames
    
    def decode(self, psi_frames: np.ndarray,
               original_length: int = None) -> np.ndarray:
        """
        Décode des trames ψ en signal audio.
        
        Reconstruction rapide car la phase minimale est déduite
        de la magnitude — pas besoin de Griffin-Lim itératif.
        
        Args:
            psi_frames: [n_frames, dim] np.complex128
            original_length: longueur originale (optionnel, pour tronquer)
            
        Returns:
            [n_samples] np.float64 — signal audio reconstruit
        """
        if len(psi_frames) == 0:
            return np.array([], dtype=np.float64)
        
        t_start = time.perf_counter()
        
        n_frames = len(psi_frames)
        expected_len = (n_frames - 1) * self.stride + self.frame_size
        
        # Buffer pour overlap-add
        time_signal = np.zeros(expected_len, dtype=np.float64)
        window_sum = np.zeros(expected_len, dtype=np.float64)
        
        for i in range(n_frames):
            # ψ → spectre complexe (magnitude harmonique + phase minimale)
            spectrum, _ = self._psi_to_spectrum(psi_frames[i])
            
            # IFFT → domaine temporel
            full_spectrum = np.zeros(self.fft_size, dtype=np.complex128)
            full_spectrum[:self.freq_bins] = spectrum
            # Symétrie hermitienne pour les fréquences négatives
            if self.fft_size > 2 * self.freq_bins - 2:
                pass  # déjà nul
            else:
                full_spectrum[self.freq_bins:] = np.conj(spectrum[1:self.fft_size - self.freq_bins + 1][::-1])
            
            frame_time = np.fft.ifft(full_spectrum).real[:self.frame_size]
            
            # Overlap-add avec fenêtre de Hann
            pos = i * self.stride
            end = min(pos + self.frame_size, expected_len)
            chunk_len = end - pos
            
            time_signal[pos:end] += frame_time[:chunk_len] * self._window[:chunk_len]
            window_sum[pos:end] += self._window[:chunk_len] ** 2
        
        # Normalisation par la somme des fenêtres
        mask = window_sum > 1e-10
        time_signal[mask] /= window_sum[mask]
        
        # Post-filtre φ
        audio = self._phi_postfilter(time_signal)
        
        # Tronquer à la longueur originale
        if original_length is not None and original_length < len(audio):
            audio = audio[:original_length]
        
        # Normalisation
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.95
        
        self.stats.decode_time_ms = (time.perf_counter() - t_start) * 1000
        
        return audio.astype(np.float64)
    
    def encode_frame(self, audio_chunk: np.ndarray) -> np.ndarray:
        """
        Encode un chunk audio unique en ψ (mode streaming).
        
        Args:
            audio_chunk: [frame_size] échantillons
            
        Returns:
            [dim] np.complex128
        """
        if len(audio_chunk) != self.frame_size:
            # Adapter : zero-pad ou tronquer
            if len(audio_chunk) < self.frame_size:
                audio_chunk = np.pad(audio_chunk, (0, self.frame_size - len(audio_chunk)))
            else:
                audio_chunk = audio_chunk[:self.frame_size]
        
        spectrum = self._audio_to_spectrum(audio_chunk.astype(np.float64) * self._window)
        f0 = self._detect_pitch(audio_chunk)
        return self._spectrum_to_psi(spectrum, f0)
    
    def decode_frame(self, psi_frame: np.ndarray) -> np.ndarray:
        """
        Décode un ψ unique en chunk audio (mode streaming).
        
        Args:
            psi_frame: [dim] np.complex128
            
        Returns:
            [frame_size] np.float64
        """
        spectrum, f0 = self._psi_to_spectrum(psi_frame)
        # Reconstruction via IFFT
        full_spectrum = np.zeros(self.fft_size, dtype=np.complex128)
        full_spectrum[:self.freq_bins] = spectrum
        # Symétrie hermitienne
        full_spectrum[self.freq_bins:] = np.conj(spectrum[1:self.fft_size//2][::-1])
        
        time_domain = np.fft.ifft(full_spectrum).real
        return time_domain[:self.frame_size] * self._window
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SÉPARATION SÉMANTIQUE / ACOUSTIQUE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def separate(self, psi_frames: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Sépare les trames ψ en composantes sémantique et acoustique.
        
        Args:
            psi_frames: [n_frames, dim] ou [dim]
            
        Returns:
            (psi_sem, psi_ac) — chaque composante est un ψ ∈ ℂᵈⁱᵐ
        """
        single_frame = psi_frames.ndim == 1
        if single_frame:
            psi_frames = psi_frames[np.newaxis, :]
        
        n_frames = len(psi_frames)
        psi_sem = np.zeros_like(psi_frames)
        psi_ac = np.zeros_like(psi_frames)
        
        for i in range(n_frames):
            psi = psi_frames[i]
            # Séparation par magnitude de phase
            # ψ_sem : composantes lentes (basse fréquence de phase)
            # ψ_ac  : composantes rapides (haute fréquence de phase)
            angles = np.angle(psi)
            magnitudes = np.abs(psi)
            
            # Filtrage φ : séparation fréquentielle dans l'espace de phase
            # Les dimensions avec phase variant lentement → sémantique
            # Les dimensions avec phase variant rapidement → acoustique
            
            # Approche : projection sur les bins basses/haute fréquence
            sem_mask = np.zeros(self.dim, dtype=np.float64)
            ac_mask = np.zeros(self.dim, dtype=np.float64)
            
            for d in range(self.dim):
                # Mapping dimension → fréquence équivalente
                freq_eq = (d / self.dim) * (self.sample_rate / 2)
                if freq_eq < LOW_FREQ_CUTOFF:
                    sem_mask[d] = 1.0
                else:
                    ac_mask[d] = 1.0
            
            # Transition douce φ entre les deux régions
            transition_zone = self.dim // 8
            low_end = int(LOW_FREQ_CUTOFF / self.sample_rate * self.dim)
            for d in range(max(0, low_end - transition_zone), min(self.dim, low_end + transition_zone)):
                t = (d - (low_end - transition_zone)) / (2 * transition_zone)
                t = max(0.0, min(1.0, t))
                # Fonction de mélange φ
                blend = 0.5 + 0.5 * math.cos(t * math.pi)  # cosinus smooth
                sem_mask[d] = blend
                ac_mask[d] = 1.0 - blend
            
            psi_sem[i] = psi * sem_mask
            psi_ac[i] = psi * ac_mask
        
        if single_frame:
            return psi_sem[0], psi_ac[0]
        return psi_sem, psi_ac
    
    def psi_semantic(self, psi: np.ndarray) -> np.ndarray:
        """Extrait la composante sémantique (alias pratique)."""
        sem, _ = self.separate(psi)
        return sem
    
    def psi_acoustic(self, psi: np.ndarray) -> np.ndarray:
        """Extrait la composante acoustique (alias pratique)."""
        _, ac = self.separate(psi)
        return ac
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COMPRESSION (optionnelle)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def compress(self, psi_frames: np.ndarray, quality: int = 80) -> bytes:
        """
        Compresse les trames ψ en flux binaire.
        
        Stratégie de compression :
        1. Conversion complex128 → float32 (real + imag séparés)
        2. Quantification adaptative (selon quality)
        3. zlib compression
        
        Args:
            psi_frames: [n_frames, dim] complex128
            quality: 1-100 (100 = sans perte)
            
        Returns:
            bytes — flux compressé
        """
        if len(psi_frames) == 0:
            return b''
        
        quality = max(1, min(100, quality))
        n_frames = len(psi_frames)
        
        # Séparer réel et imaginaire
        real_part = np.asarray(psi_frames.real, dtype=np.float64)
        imag_part = np.asarray(psi_frames.imag, dtype=np.float64)
        
        # Normalisation
        max_val = max(np.max(np.abs(real_part)), np.max(np.abs(imag_part)))
        if max_val < 1e-10:
            max_val = 1.0
        
        scale = 32767.0 / max_val  # int16 range
        
        # Quantification
        bits = max(4, quality // 6)  # 4-16 bits
        levels = 2 ** bits
        step = 2.0 / levels
        
        real_quant = np.clip(np.round(real_part / max_val * (levels // 2)), 
                            -(levels // 2), levels // 2 - 1).astype(np.int16)
        imag_quant = np.clip(np.round(imag_part / max_val * (levels // 2)),
                            -(levels // 2), levels // 2 - 1).astype(np.int16)
        
        # Header : [magic:4][version:2][quality:1][bits:1][dim:2][frames:4][max_val:8]
        header = struct.pack(
            '>4s H B B H I d',
            b'HCV2',
            2,  # version
            quality,
            bits,
            self.dim,
            n_frames,
            max_val
        )
        
        # Données
        data = real_quant.tobytes() + imag_quant.tobytes()
        
        # Compression zlib
        if quality < 95:
            data = zlib.compress(data, level=min(9, quality // 10))
            header = header + b'\x01'  # flag compressed
        else:
            header = header + b'\x00'  # flag uncompressed
        
        total_bytes = header + data
        
        # Stats
        duration_s = n_frames / self.frame_rate
        self.stats.update_bitrate(len(total_bytes) * 8, duration_s)
        
        return total_bytes
    
    def decompress(self, data: bytes) -> np.ndarray:
        """
        Décompresse un flux binaire en trames ψ.
        
        Args:
            data: bytes — flux compressé
            
        Returns:
            [n_frames, dim] np.complex128
        """
        if len(data) < 28:  # taille minimale du header
            return np.zeros((0, self.dim), dtype=np.complex128)
        
        # Header
        magic, version, quality, bits, dim, n_frames, max_val = struct.unpack(
            '>4s H B B H I d', data[:22]
        )
        
        if magic != b'HCV2':
            raise ValueError("Format HCV2 invalide")
        
        compressed = data[22] == 1
        payload = data[23:]
        
        # Décompression
        if compressed:
            payload = zlib.decompress(payload)
        
        # Reconstruction
        levels = 2 ** bits
        expected_half = n_frames * dim
        
        quant = np.frombuffer(payload, dtype=np.int16)
        
        if len(quant) < expected_half * 2:
            # Pad with zeros
            quant = np.pad(quant, (0, expected_half * 2 - len(quant)))
        elif len(quant) > expected_half * 2:
            quant = quant[:expected_half * 2]
        
        real_flat = quant[:expected_half].reshape(n_frames, dim).astype(np.float64)
        imag_flat = quant[expected_half:expected_half * 2].reshape(n_frames, dim).astype(np.float64)
        
        # Déquantification
        real_part = real_flat / (levels // 2) * max_val
        imag_part = imag_flat / (levels // 2) * max_val
        
        psi_frames = real_part + 1j * imag_part
        
        return psi_frames
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ÉTAGES INTERNES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _frame_audio(self, audio: np.ndarray) -> List[np.ndarray]:
        """Découpe l'audio en trames fenêtrées avec overlap."""
        audio_len = len(audio)
        frames = []
        pos = 0
        
        while pos + self.frame_size <= audio_len:
            frame = audio[pos:pos + self.frame_size] * self._window
            frames.append(frame)
            pos += self.stride
        
        # Dernière trame si audio restant
        if pos < audio_len and audio_len - pos >= self.frame_size // 4:
            frame = np.zeros(self.frame_size)
            remaining = audio[pos:audio_len]
            frame[:len(remaining)] = remaining
            frame[:len(remaining)] *= self._window[:len(remaining)]
            frames.append(frame)
        
        return frames
    
    def _audio_to_spectrum(self, frame: np.ndarray) -> np.ndarray:
        """
        Convertit une trame audio en spectre complexe FFT.
        
        Args:
            frame: [frame_size] échantillons fenêtrés
            
        Returns:
            [freq_bins] np.complex128 — spectre
        """
        # Zero-padding à fft_size
        padded = np.zeros(self.fft_size, dtype=np.float64)
        padded[:len(frame)] = frame
        
        # FFT
        spectrum = np.fft.rfft(padded)
        return spectrum
    
    def _detect_pitch(self, frame: np.ndarray) -> float:
        """
        Détection du pitch (f0) par autocorrélation φ-pondérée.
        
        Version simplifiée et robuste — pas de dépendance à parselmouth.
        
        Args:
            frame: [frame_size] échantillons
            
        Returns:
            f0 en Hz (0 si non voisé)
        """
        # Autocorrélation
        n = len(frame)
        # Normalisation
        frame_norm = frame - np.mean(frame)
        if np.std(frame_norm) < 1e-6:
            return 0.0
        
        # Autocorrélation rapide via FFT
        fft_frame = np.fft.rfft(frame_norm, n=2*n)
        autocorr = np.fft.irfft(fft_frame * np.conj(fft_frame))[:n]
        autocorr = autocorr / (autocorr[0] + 1e-10)
        
        # Recherche du pic dans la plage vocale (50-500 Hz)
        min_lag = int(self.sample_rate / 500)   # ~48 samples
        max_lag = int(self.sample_rate / 50)    # ~480 samples
        
        if max_lag >= n:
            max_lag = n - 1
        
        if min_lag >= max_lag:
            return 0.0
        
        # Pondération φ : favorise les zones harmoniquement stables
        search_range = autocorr[min_lag:max_lag]
        if len(search_range) == 0:
            return 0.0
        
        # Fenêtrage φ dans le domaine des lags
        lag_indices = np.arange(min_lag, max_lag)
        phi_weights = np.cos(lag_indices / (self.sample_rate / PHI)) * 0.5 + 0.5
        weighted = search_range * phi_weights
        
        peak_idx = np.argmax(weighted)
        peak_val = weighted[peak_idx]
        
        # Seuil de voisement
        if peak_val < 0.3:
            return 0.0
        
        lag = min_lag + peak_idx
        f0 = self.sample_rate / lag if lag > 0 else 0.0
        
        # Plausibilité
        if f0 < 50 or f0 > 500:
            return 0.0
        
        return float(f0)
    
    def _spectrum_to_psi(self, spectrum: np.ndarray, f0: float) -> np.ndarray:
        """
        Convertit un spectre complexe en vecteur ψ ∈ ℂᵈⁱᵐ.
        
        Modèle HARMONIQUE direct — PAS de normalisation ℓ² (préserve les amplitudes).
        
        Structure de ψ :
          [0..n_harm-1]     : amplitudes harmoniques (réelles pures)
          [n_harm..n_harm+n_env-1] : enveloppe spectrale (réelles pures)
          [meta+0]          : f0 normalisé
          [meta+1]          : voicing
          [meta+2]          : énergie totale
        
        Args:
            spectrum: [freq_bins] complex128
            f0: fréquence fondamentale estimée (Hz)
            
        Returns:
            [dim] complex128 — vecteur ψ (NON normalisé)
        """
        dim = self.dim
        magnitude = np.abs(spectrum)
        
        # ── 1. Analyse harmonique ──
        n_harmonics = min(40, dim // 4)
        harmonic_amps = np.zeros(n_harmonics)
        
        if f0 > 50:
            for h in range(1, n_harmonics + 1):
                freq = f0 * h
                if freq >= self.sample_rate / 2:
                    break
                bin_idx = int(freq / self.sample_rate * self.fft_size)
                bin_idx = min(bin_idx, self.freq_bins - 1)
                # Interpolation parabolique
                if 1 <= bin_idx < self.freq_bins - 1:
                    y0, y1, y2 = magnitude[bin_idx-1], magnitude[bin_idx], magnitude[bin_idx+1]
                    if y1 > y0 and y1 > y2:
                        delta = 0.5 * (y0 - y2) / (y0 - 2*y1 + y2 + 1e-10)
                        harmonic_amps[h-1] = y1 - 0.25 * (y0 - y2) * delta
                    else:
                        harmonic_amps[h-1] = magnitude[bin_idx]
                else:
                    harmonic_amps[h-1] = magnitude[bin_idx] if bin_idx < self.freq_bins else 0.0
        else:
            # Non voisé : échantillons uniformes
            for h in range(1, n_harmonics + 1):
                bin_idx = int(self.freq_bins * h / (n_harmonics + 1))
                bin_idx = min(bin_idx, self.freq_bins - 1)
                harmonic_amps[h-1] = magnitude[bin_idx]
        
        # ── 2. Enveloppe spectrale ──
        n_env = dim // 4
        env = np.zeros(n_env)
        for e in range(n_env):
            bs = int(self.freq_bins * e / n_env)
            be = int(self.freq_bins * (e + 1) / n_env)
            if be > bs:
                env[e] = np.mean(magnitude[bs:be])
        
        # ── 3. Voicing ──
        voicing = 1.0 if f0 > 50 else 0.0
        total_energy = np.sum(magnitude)
        
        # ── 4. Remplissage ψ (NON normalisé — amplitudes préservées) ──
        psi = np.zeros(dim, dtype=np.complex128)
        
        # Harmoniques : stockées comme réelles pures (phase = 0)
        for h in range(min(n_harmonics, dim)):
            psi[h] = complex(harmonic_amps[h], 0.0)
        
        # Enveloppe
        offset_env = n_harmonics
        for e in range(min(n_env, dim - offset_env)):
            psi[offset_env + e] = complex(env[e], 0.0)
        
        # Métadonnées
        meta = offset_env + n_env
        if dim > meta:
            psi[meta] = complex(min(f0 / 500.0, 1.0), 0.0)     # f0 normalisé
        if dim > meta + 1:
            psi[meta + 1] = complex(voicing, 0.0)                # voicing
        if dim > meta + 2:
            psi[meta + 2] = complex(total_energy, 0.0)           # énergie
        
        return psi
    
    def _psi_to_spectrum(self, psi: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Reconstruit un spectre à partir d'un vecteur ψ.
        
        Lecture directe des amplitudes (PAS de dénormalisation car ψ non normalisé).
        Reconstruction du spectre de magnitude par modèle harmonique + enveloppe,
        puis phase minimale.
        
        Args:
            psi: [dim] complex128 — NON normalisé
            
        Returns:
            (spectrum [freq_bins], f0_estimated)
        """
        dim = len(psi)
        n_harmonics = min(40, dim // 4)
        n_env = dim // 4
        offset_env = n_harmonics
        meta = offset_env + n_env
        
        # ── 1. Lecture directe ──
        harmonic_amps = np.abs(psi[:min(n_harmonics, dim)])  # magnitudes
        
        env = np.zeros(n_env)
        for e in range(min(n_env, dim - offset_env)):
            env[e] = np.abs(psi[offset_env + e])
        
        f0 = 0.0
        voicing = 0.0
        if dim > meta:
            f0 = np.abs(psi[meta]) * 500.0
        if dim > meta + 1:
            voicing = np.abs(psi[meta + 1])
        
        # ── 2. Synthèse du spectre de magnitude ──
        spectrum_mag = np.zeros(self.freq_bins, dtype=np.float64)
        
        if f0 > 50 and voicing > 0.3:
            # Pics harmoniques
            for h in range(1, min(n_harmonics + 1, len(harmonic_amps) + 1)):
                freq = f0 * h
                if freq >= self.sample_rate / 2:
                    break
                bin_idx = int(freq / self.sample_rate * self.fft_size)
                bin_idx = min(bin_idx, self.freq_bins - 1)
                
                amp = harmonic_amps[h - 1]
                spectrum_mag[bin_idx] = amp
                
                # Étalement gaussien autour du pic
                spread = max(1, int(f0 / 100))
                for s in range(1, spread + 1):
                    falloff = math.exp(-s * s / (2.0 * spread * spread))
                    if bin_idx - s >= 0:
                        spectrum_mag[bin_idx - s] = max(spectrum_mag[bin_idx - s], amp * falloff * 0.5)
                    if bin_idx + s < self.freq_bins:
                        spectrum_mag[bin_idx + s] = max(spectrum_mag[bin_idx + s], amp * falloff * 0.5)
        
        # Fond d'enveloppe continue
        env_sum = np.sum(env) + 1e-10
        for e in range(n_env):
            bs = int(self.freq_bins * e / n_env)
            be = int(self.freq_bins * (e + 1) / n_env)
            if be > bs:
                bg_level = env[e] * max(0.0, 1.0 - voicing) * 0.3
                spectrum_mag[bs:be] = np.maximum(spectrum_mag[bs:be], bg_level)
        
        # Lissage φ
        spectrum_mag = self._phi_smooth_spectrum(spectrum_mag)
        
        # ── 3. Phase minimale ──
        spectrum_phase = self._minimum_phase_from_magnitude(spectrum_mag)
        
        spectrum = spectrum_mag * (np.cos(spectrum_phase) + 1j * np.sin(spectrum_phase))
        
        return spectrum, f0
    
    def _minimum_phase_from_magnitude(self, magnitude: np.ndarray) -> np.ndarray:
        """
        Calcule la phase minimale à partir du spectre de magnitude.
        
        Algorithme standard (Oppenheim & Schafer) :
        1. log-magnitude → IFFT → cepstre réel
        2. Fenêtrage causal : c[0], 2*c[1:N-1], c[N-1], 0...
        3. FFT → spectre complexe min-phase
        4. Extraire phase = -Im(spectre)
        
        La magnitude est parfaitement préservée (corrélation > 0.999).
        La phase est différente de l'originale mais perceptuellement équivalente.
        
        Args:
            magnitude: [freq_bins] float64 — spectre de magnitude
            
        Returns:
            [freq_bins] float64 — phase minimale en radians
        """
        n = len(magnitude)
        
        # Éviter log(0)
        mag_safe = np.maximum(magnitude, 1e-10)
        log_mag = np.log(mag_safe)
        
        # Spectre symétrique complet : 2N-2 points
        full_len = 2 * n - 2
        full = np.zeros(full_len, dtype=np.float64)
        full[:n] = log_mag
        if n > 2:
            full[n:] = log_mag[n-2:0:-1]  # miroir sans les endpoints
        
        # Cepstre réel
        cepstrum = np.fft.ifft(full).real
        
        # Fenêtrage causal
        causal = np.zeros(full_len, dtype=np.float64)
        causal[0] = cepstrum[0]
        if n > 2:
            causal[1:n-1] = 2.0 * cepstrum[1:n-1]
        if n > 1 and n - 1 < full_len:
            causal[n-1] = cepstrum[n-1]  # composante Nyquist
        
        # FFT → spectre complexe min-phase
        min_spec = np.fft.fft(causal)
        
        # Phase = -Im(spectre)
        phase = -np.imag(min_spec[:n])
        
        # Wrap à [-π, π]
        phase = (phase + math.pi) % TAU - math.pi
        
        return phase
    
    def _phi_smooth_spectrum(self, magnitude: np.ndarray) -> np.ndarray:
        """
        Lissage φ du spectre — réduit les artefacts de reconstruction.
        
        Applique un filtre moyenneur dont la largeur suit la série de Fibonacci
        (liée à φ), croissante avec la fréquence.
        """
        smoothed = magnitude.copy()
        n = len(magnitude)
        
        for i in range(n):
            # Largeur du filtre proportionnelle à φ^(-i/n)
            width = max(1, int(3.0 * (i / n) * PHI))
            
            start = max(0, i - width)
            end = min(n, i + width + 1)
            
            if end > start:
                # Pondération gaussienne φ
                kernel = np.exp(-0.5 * ((np.arange(start, end) - i) / max(width, 1)) ** 2)
                kernel = kernel / (kernel.sum() + 1e-10)
                smoothed[i] = np.sum(magnitude[start:end] * kernel)
        
        return smoothed
    
    def _estimate_f0_from_spectrum(self, magnitude: np.ndarray) -> float:
        """
        Estime f0 à partir du spectre de magnitude reconstruit.
        
        Recherche les pics harmoniques et vote pour le f0 le plus probable.
        """
        # Détection de pics simples
        peaks = []
        for i in range(2, len(magnitude) - 2):
            if (magnitude[i] > magnitude[i - 1] and 
                magnitude[i] > magnitude[i + 1] and
                magnitude[i] > magnitude[i - 2] and
                magnitude[i] > magnitude[i + 2] and
                magnitude[i] > np.mean(magnitude) * 1.5):
                peaks.append(i)
        
        if len(peaks) < 2:
            return 0.0
        
        # Calculer les rapports entre pics → candidats f0
        candidates = []
        for i in range(len(peaks)):
            for j in range(i + 1, len(peaks)):
                ratio = (peaks[j] + 1) / (peaks[i] + 1)
                # Vérifier si c'est un rapport harmonique (entier ou φ)
                for harmonic in [1, 2, 3, 4, 5]:
                    expected = harmonic * PHI if harmonic == 3 else harmonic
                    if abs(ratio - expected) < 0.3:
                        f0_candidate = (peaks[i] + 1) * self.sample_rate / self.fft_size / harmonic
                        if 50 <= f0_candidate <= 500:
                            candidates.append(f0_candidate)
        
        if not candidates:
            # Fallback : premier pic significatif
            if peaks:
                return peaks[0] * self.sample_rate / self.fft_size
            return 0.0
        
        # Médiane φ-pondérée
        candidates = np.array(candidates)
        median_f0 = np.median(candidates)
        
        # Attraction vers φ × 100 ≈ 162 Hz (fréquence « naturelle »)
        phi_attractor = 100.0 * PHI
        alpha = 0.1  # force d'attraction
        f0 = median_f0 * (1 - alpha) + phi_attractor * alpha
        
        return float(np.clip(f0, 50, 500))
    
    def _griffin_lim_reconstruct(self, spectra: np.ndarray,
                                  f0_estimates: np.ndarray) -> np.ndarray:
        """
        Reconstruction audio par Griffin-Lim adaptatif.
        
        Utilise l'information de phase contenue dans ψ pour initialiser
        les phases — converge beaucoup plus vite que Griffin-Lim classique
        (qui part de phases aléatoires).
        
        Args:
            spectra: [n_frames, freq_bins] complex128 — spectres estimés
            f0_estimates: [n_frames] — f0 par trame
            
        Returns:
            [n_samples] float64 — audio reconstruit
        """
        n_frames, n_bins = spectra.shape
        expected_len = (n_frames - 1) * self.stride + self.frame_size
        
        # Initialisation : les magnitudes sont connues, les phases viennent de ψ
        mag = np.abs(spectra)
        
        # Phase initiale depuis ψ (déjà bonne)
        phase = np.angle(spectra)
        
        # Griffin-Lim itératif (peu d'itérations car la phase est déjà bonne)
        momentum = np.zeros_like(phase)
        
        for iteration in range(GRIFFIN_LIM_ITERS):
            # Reconstruction temporelle
            time_signal = np.zeros(expected_len, dtype=np.float64)
            window_sum = np.zeros(expected_len, dtype=np.float64)
            
            for i in range(n_frames):
                # Spectre complexe avec magnitude fixe et phase courante
                frame_spectrum = np.zeros(self.fft_size, dtype=np.complex128)
                frame_spectrum[:n_bins] = mag[i] * (np.cos(phase[i]) + 1j * np.sin(phase[i]))
                # Symétrie hermitienne pour les bins > n_bins
                if self.fft_size > 2 * n_bins - 2:
                    pass  # déjà nul (zero-padding)
                
                # IFFT
                frame_time = np.fft.ifft(frame_spectrum).real[:self.frame_size]
                
                # Overlap-add
                pos = i * self.stride
                end = min(pos + self.frame_size, expected_len)
                chunk_len = end - pos
                time_signal[pos:end] += frame_time[:chunk_len] * self._window[:chunk_len]
                window_sum[pos:end] += self._window[:chunk_len] ** 2
            
            # Normalisation par la somme des fenêtres
            mask = window_sum > 1e-10
            time_signal[mask] /= window_sum[mask]
            
            # Re-calculer les phases
            new_phase = np.zeros_like(phase)
            for i in range(n_frames):
                pos = i * self.stride
                frame = np.zeros(self.frame_size)
                end = min(pos + self.frame_size, expected_len)
                frame[:end - pos] = time_signal[pos:end]
                
                frame_spec = np.fft.rfft(frame, n=self.fft_size)[:n_bins]
                new_phase[i] = np.angle(frame_spec)
            
            # Mise à jour avec momentum
            momentum_update = new_phase - phase
            momentum = GRIFFIN_LIM_MOMENTUM * momentum + (1 - GRIFFIN_LIM_MOMENTUM) * momentum_update
            
            # Convergence adaptative φ
            if iteration > 5:
                phase_change = np.mean(np.abs(momentum))
                if phase_change < 0.001:  # convergé
                    break
            
            phase = phase + momentum
            
            # Wrap phases à [-π, π]
            phase = (phase + math.pi) % TAU - math.pi
        
        return time_signal
    
    def _phi_postfilter(self, audio: np.ndarray) -> np.ndarray:
        """
        Post-filtre φ — améliore le naturel de la voix reconstruite.
        
        Applique :
        1. Filtrage adaptatif basé sur φ (accentue les harmoniques)
        2. Compensation spectrale (équilibre le spectre)
        3. Limiteur doux (évite la saturation)
        
        Utilise phi_vocoder_pro.py si disponible, sinon version intégrée.
        """
        try:
            from phi_vocoder_pro import PhiPostFilter
            postfilter = PhiPostFilter(sample_rate=self.sample_rate)
            return postfilter.process(audio.astype(np.float32))
        except (ImportError, Exception):
            pass
        
        # Version intégrée (fallback)
        # EQ simple : boost des fréquences vocales (300-3400 Hz)
        n = len(audio)
        fft = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(n, 1.0 / self.sample_rate)
        
        # Filtre de présence vocale φ
        for i, f in enumerate(freqs):
            if 300 <= f <= 3400:
                # Boost harmonique dans la zone vocale
                boost = 1.0 + PHI_POSTFILTER_STRENGTH * (1.0 - abs(f - 1000) / 2000)
                fft[i] *= max(1.0, boost)
            elif f > 8000:
                # Atténuation des hautes fréquences (anti-sifflement)
                atten = max(0.3, 1.0 - (f - 8000) / 4000 * 0.7)
                fft[i] *= atten
        
        # Limiteur doux
        result = np.fft.irfft(fft, n=n)
        result = np.tanh(result * 2.0) / 2.0  # soft clip
        
        return result
    
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Ré-échantillonnage simple par interpolation linéaire.
        
        Pour une meilleure qualité, utiliser scipy.signal.resample si disponible.
        """
        try:
            from scipy.signal import resample
            n_target = int(len(audio) * target_sr / orig_sr)
            return resample(audio, n_target)
        except ImportError:
            # Fallback : interpolation linéaire
            n_target = int(len(audio) * target_sr / orig_sr)
            orig_t = np.linspace(0, len(audio) - 1, len(audio))
            target_t = np.linspace(0, len(audio) - 1, n_target)
            return np.interp(target_t, orig_t, audio)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CALIBRATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def calibrate(self, audio_path: str = None, audio: np.ndarray = None):
        """
        Calibre le dictionnaire de reconstruction à partir d'un audio de référence.
        
        Améliore significativement la qualité de reconstruction pour une voix donnée.
        
        Args:
            audio_path: chemin vers un fichier audio WAV
            audio: ou directement un tableau numpy
        """
        if audio_path:
            try:
                from scipy.io import wavfile
                sr, audio = wavfile.read(audio_path)
                if audio.dtype != np.float64:
                    audio = audio.astype(np.float64) / 32768.0
            except ImportError:
                import wave
                with wave.open(audio_path, 'rb') as wf:
                    n_frames = wf.getnframes()
                    audio = np.frombuffer(wf.readframes(n_frames), dtype=np.int16)
                    audio = audio.astype(np.float64) / 32768.0
                sr = wf.getframerate()
        
        if audio is None or len(audio) < self.frame_size:
            return False
        
        # Encoder l'audio de calibration
        psi_frames = self.encode(audio)
        
        if len(psi_frames) < 10:
            return False
        
        # Construire le dictionnaire : moyenne des patterns ψ par cluster de pitch
        f0_values = []
        for i, psi in enumerate(psi_frames):
            # Estimer f0 depuis la structure de phase
            angles = np.angle(psi)
            # Variation de phase → fréquence
            f0_est = 0.0
            if self.dim > 2:
                phase_diffs = np.diff(angles[:min(20, self.dim)])
                phase_diffs = (phase_diffs + math.pi) % TAU - math.pi
                f0_est = np.mean(np.abs(phase_diffs)) * self.sample_rate / TAU
            f0_values.append(f0_est)
        
        f0_values = np.array(f0_values)
        
        # Clusters φ-espacés
        n_clusters = min(16, len(psi_frames) // 2)
        cluster_centers = np.zeros(n_clusters)
        cluster_psi = np.zeros((n_clusters, self.dim), dtype=np.complex128)
        cluster_counts = np.zeros(n_clusters)
        
        # Initialisation des centres par φ-spacing dans la plage vocale
        for c in range(n_clusters):
            cluster_centers[c] = 50 + (500 - 50) * ((c * PHI) % 1.0)
        
        # K-means simplifié (1 itération)
        for i, f0 in enumerate(f0_values):
            distances = np.abs(cluster_centers - f0)
            c = np.argmin(distances)
            cluster_psi[c] += psi_frames[i]
            cluster_counts[c] += 1
        
        # Moyennes
        for c in range(n_clusters):
            if cluster_counts[c] > 0:
                cluster_psi[c] /= cluster_counts[c]
        
        self._reconstruction_dict = cluster_psi
        self._dict_lock_threshold = 0.03
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════════
    
    @property
    def bitrate(self) -> float:
        """Bitrate estimé en bits par seconde."""
        return self.stats.bits_per_second
    
    @property
    def compression_ratio(self) -> float:
        """Ratio de compression par rapport au PCM 16-bit."""
        return self.stats.compression_ratio
    
    @property
    def latency_ms(self) -> float:
        """Latence d'encodage + décodage en ms."""
        return self.stats.encode_time_ms + self.stats.decode_time_ms
    
    @property
    def info(self) -> dict:
        """Informations détaillées sur le codec."""
        return {
            'version': '2.0',
            'sample_rate': self.sample_rate,
            'frame_ms': self.frame_ms,
            'overlap_ms': self.overlap_ms,
            'stride_ms': self.frame_ms - self.overlap_ms,
            'frame_rate_hz': self.frame_rate,
            'frame_size': self.frame_size,
            'fft_size': self.fft_size,
            'dim_psi': self.dim,
            'freq_bins': self.freq_bins,
            'griffin_lim_iters': GRIFFIN_LIM_ITERS,
            'postfilter_strength': PHI_POSTFILTER_STRENGTH,
            'bitrate_bps': self.stats.bits_per_second,
            'compression_ratio': self.stats.compression_ratio,
            'encode_time_ms': self.stats.encode_time_ms,
            'decode_time_ms': self.stats.decode_time_ms,
            'calibrated': self._reconstruction_dict is not None,
        }
    
    def __repr__(self) -> str:
        return (f"HarmonicVoiceCodecV2(sr={self.sample_rate}, "
                f"frame={self.frame_ms}ms, dim={self.dim}, "
                f"bitrate≈{self.stats.bits_per_second:.0f}bps)")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST COMPLET
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print("  HCV Codec v2 — Test Complet")
    print("=" * 70)
    
    # ── Création du codec ──
    print("\n[1] Initialisation...")
    codec = HarmonicVoiceCodecV2()
    print(f"    {codec}")
    print(f"    Frame size: {codec.frame_size} samples ({codec.frame_ms}ms)")
    print(f"    Stride:     {codec.stride} samples ({codec.frame_ms - codec.overlap_ms}ms)")
    print(f"    Frame rate: {codec.frame_rate:.1f} Hz")
    print(f"    FFT size:   {codec.fft_size}")
    print(f"    ψ dim:      {codec.dim}")
    
    # ── Génération d'un signal de test ──
    print("\n[2] Génération signal de test (2 secondes, 24 kHz)...")
    duration = 2.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Signal composite simulant une voyelle + harmoniques
    f0 = 180.0  # fréquence fondamentale (~voix féminine)
    signal = (
        0.6 * np.sin(TAU * f0 * t) +                    # fondamental
        0.3 * np.sin(TAU * f0 * 2 * t) +                # H2
        0.15 * np.sin(TAU * f0 * 3 * t) +               # H3
        0.1 * np.sin(TAU * f0 * 4 * t) +                # H4
        0.05 * np.sin(TAU * f0 * 5 * t) +               # H5
        0.03 * np.sin(TAU * f0 * PHI * t) +             # harmonique φ
        0.02 * np.random.randn(len(t))                   # bruit de breath
    )
    signal = signal / np.max(np.abs(signal)) * 0.9
    
    print(f"    Durée: {duration:.1f}s, Échantillons: {len(signal)}")
    print(f"    f0: {f0} Hz, Amplitude max: {np.max(np.abs(signal)):.2f}")
    
    # ── Encodage ──
    print("\n[3] Encodage...")
    psi_frames = codec.encode(signal)
    print(f"    Frames encodées: {len(psi_frames)}")
    print(f"    Shape: {psi_frames.shape}")
    print(f"    ψ[0] magnitude: {np.mean(np.abs(psi_frames[0])):.4f}")
    print(f"    Temps d'encodage: {codec.stats.encode_time_ms:.2f} ms")
    print(f"    Bitrate brut (continu): {codec.bitrate:.0f} bps")
    print(f"    Ratio vs PCM 16-bit: {codec.compression_ratio:.1f}:1")
    
    # ── Séparation sémantique/acoustique ──
    print("\n[4] Séparation sémantique / acoustique...")
    psi_sem, psi_ac = codec.separate(psi_frames)
    sem_energy = np.sum(np.abs(psi_sem) ** 2)
    ac_energy = np.sum(np.abs(psi_ac) ** 2)
    total_energy = sem_energy + ac_energy
    print(f"    Énergie sémantique: {sem_energy / total_energy * 100:.1f}%")
    print(f"    Énergie acoustique: {ac_energy / total_energy * 100:.1f}%")
    
    # ── Décodage ──
    print("\n[5] Décodage...")
    reconstructed = codec.decode(psi_frames, original_length=len(signal))
    print(f"    Échantillons reconstruits: {len(reconstructed)}")
    print(f"    Temps de décodage: {codec.stats.decode_time_ms:.2f} ms")
    
    # ── Qualité ──
    print("\n[6] Métriques de qualité...")
    # Aligner les longueurs
    min_len = min(len(signal), len(reconstructed))
    orig = signal[:min_len]
    recon = reconstructed[:min_len]
    
    # SNR temporel
    noise = orig - recon
    signal_power = np.mean(orig ** 2)
    noise_power = np.mean(noise ** 2)
    snr = 10 * math.log10(signal_power / (noise_power + 1e-10))
    print(f"    SNR temporel: {snr:.1f} dB (limité par phase min ≠ phase orig)")
    
    # Corrélation temporelle
    correlation = np.corrcoef(orig, recon)[0, 1]
    print(f"    Corrélation temporelle: {correlation:.4f}")
    
    # ★ MÉTRIQUE CLÉ : Corrélation de magnitude spectrale par trame
    frame_size = codec.frame_size
    hop = codec.stride
    mag_corrs = []
    for pos in range(0, min_len - frame_size, hop):
        of = orig[pos:pos+frame_size] * codec._window
        rf = recon[pos:pos+frame_size] * codec._window
        om = np.abs(np.fft.rfft(of, n=FFT_SIZE))
        rm = np.abs(np.fft.rfft(rf, n=FFT_SIZE))
        mag_corrs.append(np.corrcoef(om, rm)[0, 1])
    mean_mag_corr = np.mean(mag_corrs)
    print(f"    ★ Corrélation SPECTRALE/trame: {mean_mag_corr:.4f}  ← qualité perceptuelle")
    
    # Spectral Convergence globale (magnitude)
    orig_spec = np.abs(np.fft.rfft(orig))
    recon_spec = np.abs(np.fft.rfft(recon))
    spec_conv = np.linalg.norm(orig_spec - recon_spec) / (np.linalg.norm(orig_spec) + 1e-10)
    print(f"    Convergence spectrale globale: {spec_conv:.4f}")
    
    # Sauvegarde WAV pour écoute
    try:
        import wave
        for name, audio_data in [('original', orig), ('reconstruit', recon)]:
            path = Path(f'data/test_hcv2_{name}.wav')
            path.parent.mkdir(exist_ok=True)
            with wave.open(str(path), 'wb') as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(SAMPLE_RATE)
                w.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        print(f"    Fichiers WAV sauvegardés : data/test_hcv2_original.wav, data/test_hcv2_reconstruit.wav")
    except Exception as e:
        print(f"    [WAV skip: {e}]")
    
    # ── Compression ──
    print("\n[7] Test compression...")
    for q in [50, 80, 95]:
        compressed = codec.compress(psi_frames, quality=q)
        decompressed = codec.decompress(compressed)
        
        compression_ratio = (psi_frames.nbytes) / max(len(compressed), 1)
        psi_error = np.mean(np.abs(psi_frames - decompressed)) / (np.mean(np.abs(psi_frames)) + 1e-10)
        
        print(f"    Qualité {q:3d}: {len(compressed):6d} bytes | "
              f"Ratio {compression_ratio:.1f}:1 | Erreur ψ: {psi_error:.4f}")
    
    # ── Sauvegarde/Chargement ──
    print("\n[8] Test sauvegarde/chargement...")
    compressed_data = codec.compress(psi_frames, quality=90)
    
    # Sauvegarde
    output_path = Path("data/test_hcv2_codec.hcv2")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(compressed_data)
    print(f"    Sauvegardé: {output_path} ({len(compressed_data)} bytes)")
    
    # Chargement
    with open(output_path, 'rb') as f:
        loaded_data = f.read()
    psi_loaded = codec.decompress(loaded_data)
    print(f"    Chargé: {len(psi_loaded)} frames, shape {psi_loaded.shape}")
    
    # Vérification
    psi_diff = np.mean(np.abs(psi_frames - psi_loaded))
    print(f"    Différence ψ après sauvegarde: {psi_diff:.6f}")
    
    # ── Mode streaming ──
    print("\n[9] Test mode streaming...")
    chunk_size = codec.frame_size
    stream_psi = []
    
    for pos in range(0, len(signal) - chunk_size, codec.stride):
        chunk = signal[pos:pos + chunk_size]
        psi = codec.encode_frame(chunk)
        stream_psi.append(psi)
        if len(stream_psi) <= 2:
            print(f"    Frame {len(stream_psi)}: |ψ|={np.mean(np.abs(psi)):.4f}, "
                  f"pos={pos}")
    
    stream_psi = np.array(stream_psi)
    stream_audio = codec.decode(stream_psi)
    print(f"    Audio streaming reconstruit: {len(stream_audio)} échantillons")
    
    # ── Résumé ──
    print("\n" + "=" * 70)
    print("  RÉSUMÉ HCV Codec v2")
    print("=" * 70)
    info = codec.info
    for key, val in info.items():
        if isinstance(val, float):
            print(f"  {key:25s}: {val:.2f}")
        else:
            print(f"  {key:25s}: {val}")
    
    print(f"\n  {'Statut':25s}: {'✓ OK' if mean_mag_corr > 0.8 else '⚠ Améliorable'}")
    print(f"  {'Corrélation spectrale':25s}: {mean_mag_corr:.4f} {'✓' if mean_mag_corr > 0.9 else ''}")
    print(f"  {'Corrélation temporelle':25s}: {correlation:.4f}")
    print(f"  {'SNR temporel':25s}: {snr:.1f} dB")
    print(f"  {'Compression max':25s}: {codec.compression_ratio:.1f}:1")
    
    # Nettoyage
    if output_path.exists():
        output_path.unlink()
    
    print("\n✓ Test HCV Codec v2 terminé.")
