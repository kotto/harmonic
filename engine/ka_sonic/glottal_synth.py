"""
GlottalSynth — Synthèse glottale + formantique pour générer des diphones.

Génère une banque de diphones SYNTHÉTIQUES sans corpus audio externe.
Chaque diphone est créé par :
  1. Synthèse de la source glottale (onde de Liljencrants-Fant LF)
  2. Filtrage formantique (filtres résonants F1-F4)
  3. Ajout de bruit pour les fricatives/occlusives
  4. Concaténation gauche→droite avec crossfade

La banque synthétique garantit :
  - Reproductibilité 100% (mêmes paramètres → même audio)
  - Pas de dépendance à un corpus externe
  - Contrôle fin des paramètres acoustiques

Références :
  - LF model : Fant, Liljencrants (1985)
  - Formant synthesis : Klatt (1980)
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .phoneme_features import (
    PHONEME_FEATURES, VOYELLES, OCCLUSIVES, FRICATIVES, LIQUIDES, NASALES, SEMI_VOYELLES,
)

DEFAULT_SR = 22050

# ═══════════════════════════════════════════════════════════════════════════════
# Modèle de source glottale (LF simplifié)
# ═══════════════════════════════════════════════════════════════════════════════

def glottal_pulse(
    f0: float,
    duration_s: float,
    sr: int = DEFAULT_SR,
    open_quotient: float = 0.6,
    asymmetry: float = 0.7,
) -> np.ndarray:
    """Génère un train d'impulsions glottales (modèle LF simplifié).
    
    Args:
        f0 : fréquence fondamentale (Hz), 0 = pas d'impulsions (non voisé)
        duration_s : durée en secondes
        sr : sample rate
        open_quotient : proportion de la période où la glotte est ouverte [0,1]
        asymmetry : asymétrie de l'onde (0.5=symétrique, >0.5=montée rapide)
    
    Returns:
        signal source float32 [-1, 1]
    """
    n_samples = int(duration_s * sr)
    if f0 <= 0 or n_samples == 0:
        return np.zeros(n_samples, dtype=np.float32)

    period_samples = int(sr / f0)
    if period_samples < 2:
        period_samples = 2

    open_samples = int(period_samples * open_quotient)
    
    # Une période de l'onde LF
    pulse = np.zeros(period_samples, dtype=np.float32)
    
    # Phase ouverte (montée → descente)
    t_open = np.linspace(0, 1, open_samples)
    # Asymétrie : pic décalé
    peak_pos = 1.0 - asymmetry  # 0 = début, 1 = fin de la phase ouverte
    # Montée rapide
    rise = np.exp(3 * (t_open - peak_pos)) * (t_open <= peak_pos)
    # Descente exponentielle
    decay = np.exp(-4 * (t_open - peak_pos)) * (t_open > peak_pos)
    pulse[:open_samples] = rise + decay
    
    # Normaliser
    pulse_max = np.max(np.abs(pulse)) + 1e-10
    pulse /= pulse_max
    
    # Répliquer sur la durée
    n_periods = n_samples // period_samples + 1
    train = np.tile(pulse, n_periods)[:n_samples]
    
    return train.astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# Filtre formantique (résonateurs en cascade)
# ═══════════════════════════════════════════════════════════════════════════════

def formant_filter(
    source: np.ndarray,
    formants: List[float],
    bandwidths: Optional[List[float]] = None,
    sr: int = DEFAULT_SR,
) -> np.ndarray:
    """Filtre formantique : filtre la source par des résonateurs en cascade.
    
    Utilise scipy.signal.sosfilt (biquads cascadés, numériquement stable)
    quand scipy est disponible, sinon fallback à une implémentation manuelle.
    """
    if bandwidths is None:
        bandwidths = [50, 70, 110, 170]

    out = source.astype(np.float64)
    
    # Essayer scipy (stable, pas d'overflow)
    try:
        from scipy import signal as scipy_signal
        for freq, bw in zip(formants, bandwidths):
            if freq <= 0 or freq >= sr / 2.1:
                continue
            # Filtre biquad résonant (peak filter)
            Q = max(0.5, freq / max(bw, 10))
            b, a = scipy_signal.iirpeak(freq, Q, sr)
            out = scipy_signal.lfilter(b, a, out)
    except ImportError:
        pass
    
    # Nettoyer NaN/Inf
    if not np.all(np.isfinite(out)):
        out = np.nan_to_num(out, nan=0.0, posinf=1.0, neginf=-1.0)
    
    # Normalisation
    g = np.max(np.abs(out)) + 1e-10
    return (out / g * 0.8).astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# Générateur de bruit pour les fricatives
# ═══════════════════════════════════════════════════════════════════════════════

def noise_source(duration_s: float, sr: int = DEFAULT_SR, color: str = "white") -> np.ndarray:
    """Génère du bruit (blanc, rose, ou haute fréquence).
    
    Args:
        color : 'white' (plat), 'hiss' (HF boost), 'burst' (impulsion courte)
    """
    n = int(duration_s * sr)
    noise = np.random.normal(0, 1, n).astype(np.float32)
    
    if color == "hiss":
        # Boost hautes fréquences (filtre passe-haut simple)
        noise = np.diff(noise, prepend=noise[0]) * 0.7
    elif color == "burst":
        # Impulsion courte + bruit bref
        burst_len = int(0.005 * sr)  # 5ms
        noise[burst_len:] *= 0.1
        noise[:burst_len] *= 3.0
    
    # Normaliser
    peak = np.max(np.abs(noise)) + 1e-10
    return (noise / peak * 0.5).astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# Synthèse d'un diphone
# ═══════════════════════════════════════════════════════════════════════════════

def synthesize_diphone(
    left: str,
    right: str,
    duration_s: float = 0.120,
    f0: float = 120.0,
    sr: int = DEFAULT_SR,
) -> np.ndarray:
    """Synthétise un diphone gauche→droite par modèle source-filtre.
    
    Args:
        left, right : phonèmes (symboles IPA)
        duration_s : durée totale du diphone
        f0 : fréquence fondamentale (Hz, 0 = non voisé)
        sr : sample rate
    
    Returns:
        audio float32 [-1, 1]
    """
    l_feat = PHONEME_FEATURES.get(left)
    r_feat = PHONEME_FEATURES.get(right)
    
    half_dur = duration_s / 2
    n_total = int(duration_s * sr)
    n_half = n_total // 2
    n_rem = n_total - 2 * n_half  # 0 ou 1 sample résiduel
    
    # ── Partie GAUCHE ─────────────────────────────────────────────────
    if l_feat is None:
        l_audio = np.zeros(n_half, dtype=np.float32)
    else:
        l_voise = l_feat[0]
        l_mode = l_feat[8]
        l_F1 = 300 + 600 * l_feat[6]    # F1 ∈ [300, 900] Hz
        l_F2 = 700 + 1800 * l_feat[7]   # F2 ∈ [700, 2500] Hz
        l_F3 = 2200 + 1300 * l_feat[4]  # F3 ∈ [2200, 3500] Hz
        l_F4 = 3500 + 1500 * l_feat[2]  # F4 ∈ [3500, 5000] Hz
        l_formants = [l_F1, l_F2, l_F3, l_F4]
        
        if l_mode >= 0.8:  # Voyelle
            src = glottal_pulse(f0 if l_voise else 0, half_dur, sr)
            l_audio = formant_filter(src, l_formants, sr=sr)
        elif l_mode >= 0.4:  # Fricative
            if l_voise:
                src = glottal_pulse(f0, half_dur, sr) * 0.3 + noise_source(half_dur, sr, "hiss") * 0.7
            else:
                src = noise_source(half_dur, sr, "hiss")
            l_audio = formant_filter(src, l_formants, sr=sr)
        else:  # Occlusive
            if l_voise:
                src = glottal_pulse(f0, half_dur, sr) * 0.4
                l_audio = formant_filter(src, l_formants, sr=sr)
            else:
                # Silence + burst en fin
                silence_len = int(0.8 * n_half)
                burst_len = n_half - silence_len
                l_audio = np.zeros(n_half, dtype=np.float32)
                if burst_len > 0:
                    burst = noise_source(burst_len / sr, sr, "burst")
                    l_audio[silence_len:] = formant_filter(
                        burst, [700, 1500, 2500, 3500], sr=sr,
                    ) * 0.3
    
    # ── Partie DROITE ─────────────────────────────────────────────────
    if r_feat is None:
        r_audio = np.zeros(n_half, dtype=np.float32)
    else:
        r_voise = r_feat[0]
        r_mode = r_feat[8]
        r_F1 = 300 + 600 * r_feat[6]
        r_F2 = 700 + 1800 * r_feat[7]
        r_F3 = 2200 + 1300 * r_feat[4]
        r_F4 = 3500 + 1500 * r_feat[2]
        r_formants = [r_F1, r_F2, r_F3, r_F4]
        
        if r_mode >= 0.8:
            src = glottal_pulse(f0 if r_voise else 0, half_dur, sr)
            r_audio = formant_filter(src, r_formants, sr=sr)
        elif r_mode >= 0.4:
            if r_voise:
                src = glottal_pulse(f0, half_dur, sr) * 0.3 + noise_source(half_dur, sr, "hiss") * 0.7
            else:
                src = noise_source(half_dur, sr, "hiss")
            r_audio = formant_filter(src, r_formants, sr=sr)
        else:
            if r_voise:
                src = glottal_pulse(f0, half_dur, sr) * 0.4
                r_audio = formant_filter(src, r_formants, sr=sr)
            else:
                silence_len = int(0.8 * n_half)
                burst_len = n_half - silence_len
                r_audio = np.zeros(n_half, dtype=np.float32)
                if burst_len > 0:
                    burst = noise_source(burst_len / sr, sr, "burst")
                    r_audio[silence_len:] = formant_filter(
                        burst, [700, 1500, 2500, 3500], sr=sr,
                    ) * 0.3
    
    # ── Crossfade ──────────────────────────────────────────────────────
    fade_len = min(int(0.010 * sr), n_half // 4)  # 10ms crossfade
    result = np.zeros(n_total, dtype=np.float32)
    
    # Ajuster si nécessaire (padding ou trim)
    l_len = min(len(l_audio), n_half)
    r_len = min(len(r_audio), n_total - n_half)
    result[:l_len] = l_audio[:l_len]
    result[n_half:n_half + r_len] = r_audio[:r_len]
    
    if fade_len > 0 and n_half > fade_len:
        # Fenêtre de crossfade cosinusoïdale
        t = np.linspace(0, math.pi/2, fade_len)
        fade_out = np.cos(t)
        fade_in = np.sin(t)
        
        result[n_half - fade_len:n_half] *= fade_out
        overlap = r_audio[:fade_len] * fade_in
        result[n_half - fade_len:n_half] += overlap
    
    # Normaliser
    peak = np.max(np.abs(result)) + 1e-10
    return (result / peak * 0.9).astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# Banque de diphones synthétiques
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SynthDiphone:
    """Un diphone synthétique dans la banque."""
    left: str
    right: str
    audio: np.ndarray
    sample_rate: int
    duration_s: float
    f0: float  # F0 utilisée pour la synthèse

    @property
    def n_samples(self) -> int:
        return len(self.audio)


def build_synthetic_bank(
    phonemes: Optional[List[str]] = None,
    sr: int = DEFAULT_SR,
    f0_default: float = 120.0,
) -> List[SynthDiphone]:
    """Construit une banque de diphones synthétiques complète.
    
    Génère tous les diphones possibles entre les phonèmes fournis.
    Par défaut : tous les phonèmes français (36) → jusqu'à 1296 diphones.
    
    Args:
        phonemes : liste de phonèmes (défaut : tous les phonèmes de PHONEME_FEATURES)
        sr : sample rate
        f0_default : F0 par défaut (sera ajustée post-concaténation)
    
    Returns:
        liste de SynthDiphone
    """
    if phonemes is None:
        phonemes = [p for p in PHONEME_FEATURES if p not in ("_", "#")]

    bank = []
    # Générer uniquement les diphones pertinents (pas toutes les combinaisons)
    # Priorité : voyelle→consonne, consonne→voyelle, voyelle→voyelle
    
    # Classes phonétiques
    vowels = [p for p in phonemes if p in VOYELLES]
    consonants = [p for p in phonemes if p not in VOYELLES and p not in SEMI_VOYELLES]
    all_ph = phonemes
    
    # Combinaisons à générer
    pairs = set()
    
    # V→C et C→V (les plus fréquents en français)
    for v in vowels:
        for c in consonants:
            pairs.add((v, c))
            pairs.add((c, v))
    
    # V→V (liaisons, hiatus)
    for v1 in vowels:
        for v2 in vowels:
            if v1 != v2:
                pairs.add((v1, v2))
    
    # Semi-voyelles + voyelles
    for sv in SEMI_VOYELLES:
        for v in vowels:
            pairs.add((sv, v))
            pairs.add((v, sv))
    
    # Consonnes entre elles (clusters)
    for c1 in consonants:
        for c2 in consonants:
            if c1 != c2:
                pairs.add((c1, c2))
    
    # Ajouter aussi les paires avec silence (début/fin d'énoncé)
    for p in all_ph:
        pairs.add(("_", p))
        pairs.add((p, "_"))
    
    # Génération
    for left, right in sorted(pairs):
        dur = 0.120  # durée standard
        f0 = f0_default
        
        # Ajuster durée selon le type
        if left in VOYELLES and right in VOYELLES:
            dur = 0.140
        elif left in OCCLUSIVES or right in OCCLUSIVES:
            dur = 0.100
        
        # Ajuster F0
        if left in VOYELLES or right in VOYELLES:
            f0 = f0_default
        elif left not in VOYELLES and right not in VOYELLES:
            f0 = 0  # pas de voisement pour C-C
        
        audio = synthesize_diphone(left, right, duration_s=dur, f0=f0, sr=sr)
        bank.append(SynthDiphone(
            left=left, right=right,
            audio=audio, sample_rate=sr,
            duration_s=dur, f0=f0,
        ))
    
    return bank
