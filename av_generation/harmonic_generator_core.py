#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GÉNÉRATEUR HARMONIQUE UNIVERSEL — Cœur Théorique
==================================================
Basé sur la Théorie Harmonique : Ψ = Σ Hₙ (Ψ₁)ⁿ

Ce module implémente le noyau de génération d'images, vidéos et audio
en utilisant les 7 constantes harmoniques fondamentales comme signatures
spectrales pour produire des textures, des animations et des sons structurés.

Principes :
  - Ψ₁ = champ d'onde fondamental (bruit harmonique structuré)
  - Hₙ = [φ, π, e, √2, √3, √5, e/π] — les 7 constantes harmoniques
  - Ψ = Σ Hₙ (Ψ₁)ⁿ — superposition des couches harmoniques

Chaque Hₙ gouverne une propriété visuelle/sonore :
  H₁ (φ)   : anti-résonance — espacement, structure globale, proportion dorée
  H₂ (π)   : périodicité — motifs répétitifs, cycles, textures circulaires
  H₃ (e)   : amortissement — dégradés doux, suppression du bruit, lissage
  H₄ (√2)  : symétrie planaire — réflexions horizontales/verticales
  H₅ (√3)  : symétrie volumique — profondeur 3D, perspective isométrique
  H₆ (√5)  : textures fines — détails haute fréquence, micro-structures
  H₇ (e/π) : spirale de synthèse — rotation, mouvement organique, grain final

Author: Système Harmonique
Version: 1.0.0
"""

import numpy as np
import math
from typing import Tuple, Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import colorsys
import hashlib
import time

# ==============================================================================
# CONSTANTES HARMONIQUES FONDAMENTALES
# ==============================================================================

PHI = (1 + math.sqrt(5)) / 2       # 1.618... Nombre d'or
PI = math.pi                        # 3.141... Pi
E = math.e                          # 2.718... Base naturelle
SQRT2 = math.sqrt(2)                # 1.414... Diagonale du carré
SQRT3 = math.sqrt(3)                # 1.732... Diagonale du cube
SQRT5 = math.sqrt(5)                # 2.236... Racine de 5
E_PI = E / PI                       # 0.865... Spirale de synthèse
PHI_INV = 1.0 / PHI                 # 0.618... Ordre mémoire optimal

# Les 7 constantes harmoniques (Hₙ)
H_CONSTANTS = np.array([PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI])
H_NAMES = ['φ (Phi)', 'π (Pi)', 'e (Euler)', '√2', '√3', '√5', 'e/π']
H_ROLES_IMAGE = [
    'Anti-résonance — structure globale, proportions dorées, espacement',
    'Périodicité — motifs répétitifs, cercles, cycles visuels',
    'Amortissement — dégradés doux, lissage, transitions naturelles',
    'Symétrie planaire — réflexions H/V, géométrie 2D',
    'Symétrie volumique — profondeur, perspective, relief 3D',
    'Textures fines — micro-détails, haute fréquence, grain',
    'Spirale de synthèse — rotation, mouvement organique, touche finale'
]
H_ROLES_AUDIO = [
    'Fondamentale dorée — fréquence de base (ratio 1.618:1)',
    'Pulsation cyclique — rythme, enveloppes périodiques',
    'Amortissement naturel — decay, release, réverbération',
    'Harmonique d\'octave — doublement de fréquence (2^(1/2))',
    'Harmonique de quinte — rapport 3:1, profondeur sonore',
    'Harmonique supérieure — brillance, présence haute fréquence',
    'Tremblement spiral — modulation de phase, vibrato naturel'
]
H_ROLES_VIDEO = [
    'Cadence φ — vitesse d\'évolution temporelle dorée',
    'Cycle π — boucle périodique, retour circulaire',
    'Fondu e — transitions exponentielles douces',
    'Symétrie 2D — motifs de mouvement planaires',
    'Parallaxe 3D — profondeur et perspective animée',
    'Micro-mouvements — tremblements fins, vie',
    'Rotation spirale — mouvements organiques continus'
]

# Fréquence fondamentale de résonance
FREQUENCE_FONDAMENTALE = 137.507764  # Hz — angle d'or en acoustique
ANGLE_HARMONIQUE = 2 * PI * PHI_INV  # Angle de rotation harmonique (~137.5°)


@dataclass
class HarmonicField:
    """
    Champ harmonique 2D/3D — le Ψ fondamental dont tout émerge.
    
    Représente Ψ₁ élevé à différentes puissances, pondéré par les Hₙ.
    """
    width: int = 512
    height: int = 512
    seed: int = 42
    n_layers: int = 7
    
    # Champs internes
    _psi_1: Optional[np.ndarray] = field(default=None, repr=False)
    _layers: List[np.ndarray] = field(default_factory=list, repr=False)
    _psi_total: Optional[np.ndarray] = field(default=None, repr=False)
    
    def __post_init__(self):
        self._generate_psi1()
    
    def _generate_psi1(self):
        """
        Génère Ψ₁ — la fonction d'onde fondamentale.
        
        Ψ₁ est un champ de bruit harmonique structuré qui combine :
          - Un spectre 1/f² : somme dense de sinusoïdes à fréquences
            distribuées avec amplitude ∝ 1/f (énergie ∝ 1/f²)
          - Une modulation dorée (spirale de Fibonacci)
          - Une symétrie cyclique basée sur π
        
        V2 — Spectre 1/f² physique (pas juste 7 fréquences fixes).
        Utilise 42 ondes à fréquences croissantes avec décroissance 1/f.
        """
        rng = np.random.RandomState(self.seed % (2**31))
        
        # Grille de coordonnées normalisées [-1, 1]
        x = np.linspace(-1, 1, self.width)
        y = np.linspace(-1, 1, self.height)
        X, Y = np.meshgrid(x, y)
        
        # Coordonnées polaires pour la spirale
        R = np.sqrt(X**2 + Y**2)
        theta = np.arctan2(Y, X)
        
        # Ψ₁ — somme d'ondes avec spectre 1/f²
        psi_1 = np.zeros((self.height, self.width), dtype=np.float64)
        
        # --- CATEGORIE 1 : Très basses fréquences (structure globale) ---
        # f ~ 1-3 cycles/image, amplitude forte
        n_low = 6
        low_freqs = np.linspace(1.5, 4.0, n_low)
        low_amps = 1.0 / low_freqs  # décroissance 1/f
        low_amps = low_amps / np.sum(low_amps) * 0.40  # 40% énergie totale
        
        for i in range(n_low):
            fx = low_freqs[i] * (0.3 + 0.7 * H_CONSTANTS[i % 7] / PHI)
            fy = low_freqs[i] * (0.3 + 0.7 * H_CONSTANTS[(i+3) % 7] / PHI)
            phase_x = rng.random() * 2 * PI
            phase_y = rng.random() * 2 * PI
            # Spirale dorée pour les BF (structure)
            psi_1 += low_amps[i] * (
                np.cos(fx * X * PI + phase_x) * np.cos(fy * Y * PI + phase_y) +
                0.3 * np.cos(PHI * R * low_freqs[i] + theta * PHI)
            )
        
        # --- CATEGORIE 2 : Moyennes fréquences (textures, motifs) ---
        # f ~ 5-25 cycles/image, amplitude décroissante 1/f
        n_mid = 16
        mid_freqs = np.linspace(5.0, 28.0, n_mid)
        mid_amps = 1.0 / mid_freqs
        mid_amps = mid_amps / np.sum(mid_amps) * 0.35  # 35% énergie
        
        for i in range(n_mid):
            fx = mid_freqs[i]
            fy = mid_freqs[i] * (rng.random() * 0.6 + 0.7)
            angle = rng.random() * 2 * PI
            # Rotation aléatoire des motifs
            Xr = X * np.cos(angle) + Y * np.sin(angle)
            Yr = -X * np.sin(angle) + Y * np.cos(angle)
            phase = rng.random() * 2 * PI
            h = H_CONSTANTS[i % 7]
            # Alternance sin/cos pour varier les structures
            if i % 3 == 0:
                psi_1 += mid_amps[i] * np.sin(fx * Xr * PI) * np.cos(fy * Yr * PI + phase)
            elif i % 3 == 1:
                psi_1 += mid_amps[i] * np.cos(fx * Xr * PI + phase) * np.sin(fy * Yr * PI)
            else:
                # Grille diagonale (√3)
                psi_1 += mid_amps[i] * 0.7 * np.cos((fx*Xr + fy*Yr) * PI * SQRT3/3)
        
        # --- CATEGORIE 3 : Hautes fréquences (micro-détails, grain) ---
        # f ~ 30-80 cycles/image, amplitude faible mais dense spectralement
        n_high = 14
        high_freqs = np.linspace(30.0, 75.0, n_high)
        high_amps = 1.0 / (high_freqs ** 1.2)  # décroissance légèrement > 1/f
        high_amps = high_amps / np.sum(high_amps) * 0.18  # 18% énergie
        
        for i in range(n_high):
            fx = high_freqs[i] * (0.8 + rng.random() * 0.4)
            fy = high_freqs[i] * (0.8 + rng.random() * 0.4)
            phase_x = rng.random() * 2 * PI
            phase_y = rng.random() * 2 * PI
            # Micro-textures fines (√5)
            psi_1 += high_amps[i] * np.sin(fx * X * PI + phase_x) * np.cos(fy * Y * PI + phase_y)
        
        # --- CATEGORIE 4 : Grain organique (très HF isotrope, e/π) ---
        n_grain = 6
        grain_freqs = np.linspace(50.0, 120.0, n_grain)
        grain_amps = 1.0 / (grain_freqs ** 1.5)
        grain_amps = grain_amps / np.sum(grain_amps) * 0.07  # 7% énergie
        
        for i in range(n_grain):
            f = grain_freqs[i]
            # Grain isotrope (symétrie radiale)
            psi_1 += grain_amps[i] * np.sin(R * f * PI * E_PI + theta * (i+1) * PHI_INV)
        
        # Normaliser dans [-1, 1]
        psi_max = np.max(np.abs(psi_1))
        if psi_max > 1e-12:
            psi_1 = psi_1 / psi_max
        
        self._psi_1 = psi_1
    
    def compute_layers(self) -> List[np.ndarray]:
        """
        Calcule les 7 couches harmoniques : Hₙ × (Ψ₁)ⁿ
        
        Chaque couche = constante harmonique × (champ fondamental)^n
        """
        if self._psi_1 is None:
            self._generate_psi1()
        
        self._layers = []
        self._psi_total = np.zeros((self.height, self.width), dtype=np.float64)
        
        for n in range(1, self.n_layers + 1):
            h_n = H_CONSTANTS[n - 1]
            # (Ψ₁)ⁿ — puissance n du champ fondamental
            psi_n = np.power(np.abs(self._psi_1), n) * np.sign(self._psi_1)
            # Pondération harmonique
            layer = h_n * psi_n
            self._layers.append(layer)
            self._psi_total += layer
        
        # Normalisation globale
        total_max = np.max(np.abs(self._psi_total))
        if total_max > 1e-12:
            self._psi_total = self._psi_total / total_max
        
        return self._layers
    
    def get_psi_total(self) -> np.ndarray:
        """Retourne Ψ = Σ Hₙ (Ψ₁)ⁿ — le champ harmonique total."""
        if self._psi_total is None:
            self.compute_layers()
        return self._psi_total
    
    def get_layer(self, n: int) -> Optional[np.ndarray]:
        """Retourne la couche harmonique n (1-indexed)."""
        if not self._layers:
            self.compute_layers()
        if 1 <= n <= len(self._layers):
            return self._layers[n - 1]
        return None
    
    def get_layer_contribution(self, n: int) -> float:
        """Calcule la contribution relative (énergie) de la couche n."""
        if not self._layers:
            self.compute_layers()
        if 1 <= n <= len(self._layers):
            layer = self._layers[n - 1]
            total = self._psi_total
            return float(np.sum(layer**2) / (np.sum(total**2) + 1e-12))
        return 0.0
    
    def regenerate(self, seed: int = None):
        """Régénère le champ avec un nouveau seed."""
        if seed is not None:
            self.seed = seed
        self._psi_1 = None
        self._layers = []
        self._psi_total = None
        self._generate_psi1()
        self.compute_layers()


class HarmonicColorMapper:
    """
    Mapper le champ harmonique vers des couleurs RGB.
    
    Utilise les constantes harmoniques pour déterminer les palettes :
      - φ → teinte dominante (proportion dorée sur la roue chromatique)
      - π → saturation cyclique
      - e → luminosité amortie
    """
    
    # Palettes de couleurs harmoniques prédéfinies
    PALETTES = {
        'cosmique': {
            'hue_shift': 0.0,
            'sat_boost': 1.2,
            'description': 'Bleus profonds, violets, touches dorées — espace profond'
        },
        'solaire': {
            'hue_shift': 0.15,
            'sat_boost': 1.5,
            'description': 'Oranges, rouges, jaunes — énergie solaire'
        },
        'forest': {
            'hue_shift': 0.35,
            'sat_boost': 0.9,
            'description': 'Verts, émeraudes, bruns — nature luxuriante'
        },
        'ocean': {
            'hue_shift': 0.55,
            'sat_boost': 1.1,
            'description': 'Cyans, bleus turquoise, blancs — profondeur océanique'
        },
        'aurore': {
            'hue_shift': 0.75,
            'sat_boost': 1.3,
            'description': 'Violets, magentas, verts — aurore boréale'
        },
        'crepuscule': {
            'hue_shift': 0.08,
            'sat_boost': 1.4,
            'description': 'Roses, pourpres, oranges — coucher de soleil'
        },
        'galactique': {
            'hue_shift': 0.0,
            'sat_boost': 0.7,
            'description': 'Noir profond, touches de bleu et blanc — voie lactée'
        },
    }
    
    @staticmethod
    def harmonic_hsl(harmonic_field: np.ndarray,
                     palette: str = 'cosmique',
                     layer_weights: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Convertit un champ harmonique en image RGB via l'espace HSL harmonique.
        
        Args:
            harmonic_field: Ψ total normalisé dans [-1, 1]
            palette: Nom de la palette de couleurs
            layer_weights: Pondérations des 7 couches pour le mixage
        
        Returns:
            Array RGB shape (height, width, 3) en uint8
        """
        config = HarmonicColorMapper.PALETTES.get(palette, HarmonicColorMapper.PALETTES['cosmique'])
        
        field = np.clip(harmonic_field, -1, 1)
        
        # Teinte (H) : basée sur la valeur du champ + spirale dorée
        hue = (field * 0.5 + 0.5)  # [0, 1]
        hue = (hue * PHI + config['hue_shift']) % 1.0
        
        # Saturation (S) : basée sur le gradient du champ (π)
        gy, gx = np.gradient(field)
        grad_mag = np.sqrt(gx**2 + gy**2)
        grad_mag = grad_mag / (np.max(grad_mag) + 1e-12)
        saturation = np.clip(0.3 + grad_mag * config['sat_boost'], 0, 1)
        
        # Luminosité (L) : basée sur la valeur absolue amortie (e)
        lightness = 0.3 + 0.5 * (1 - np.exp(-np.abs(field) * 3))
        
        # Assemblage RGB
        h = hue.flatten()
        s = saturation.flatten()
        l_flat = lightness.flatten()
        
        rgb = np.zeros((len(h), 3), dtype=np.float64)
        for i in range(len(h)):
            r, g, b = colorsys.hls_to_rgb(h[i], l_flat[i], s[i])
            rgb[i] = [r, g, b]
        
        rgb = rgb.reshape(harmonic_field.shape[0], harmonic_field.shape[1], 3)
        rgb = np.clip(rgb * 255, 0, 255).astype(np.uint8)
        
        return rgb
    
    @staticmethod
    def multi_layer_rgb(layers: List[np.ndarray],
                        palette: str = 'cosmique') -> np.ndarray:
        """
        Combine les 7 couches harmoniques en RGB avec des teintes distinctes.
        Chaque couche Hₙ reçoit une teinte légèrement différente.
        """
        config = HarmonicColorMapper.PALETTES.get(palette, HarmonicColorMapper.PALETTES['cosmique'])
        
        h, w = layers[0].shape
        result = np.zeros((h, w, 3), dtype=np.float64)
        
        for n, layer in enumerate(layers):
            # Teinte différente par couche (décalée par le ratio doré)
            hue_shift_layer = (n * PHI_INV + config['hue_shift']) % 1.0
            
            # Normaliser la couche
            l_max = np.max(np.abs(layer))
            if l_max < 1e-12:
                continue
            layer_norm = layer / l_max
            
            # Amplitude
            amplitude = np.abs(layer_norm)
            
            # Teinte basée sur la valeur
            hue = (layer_norm * 0.3 + hue_shift_layer) % 1.0
            saturation = 0.5 + amplitude * config['sat_boost'] * 0.5
            lightness = 0.3 + amplitude * 0.5
            
            h_flat = hue.flatten()
            s_flat = np.clip(saturation.flatten(), 0, 1)
            l_flat = np.clip(lightness.flatten(), 0, 1)
            a_flat = amplitude.flatten()
            
            for i in range(len(h_flat)):
                r, g, b = colorsys.hls_to_rgb(h_flat[i], l_flat[i], s_flat[i])
                weight = a_flat[i] * H_CONSTANTS[n] / np.sum(H_CONSTANTS[:len(layers)])
                result.flat[i*3 + 0] += r * weight
                result.flat[i*3 + 1] += g * weight
                result.flat[i*3 + 2] += b * weight
        
        # Normalisation
        max_val = np.max(result)
        if max_val > 1e-12:
            result = result / max_val
        
        return np.clip(result * 255, 0, 255).astype(np.uint8)
    
    @staticmethod
    def depth_map(harmonic_field: np.ndarray) -> np.ndarray:
        """
        Génère une carte de profondeur à partir du champ harmonique.
        Utile pour le rendu 3D et les effets de parallaxe vidéo.
        """
        # La profondeur = combinaison de la magnitude et du laplacien
        field_abs = np.abs(harmonic_field)
        gy, gx = np.gradient(harmonic_field)
        lap = np.gradient(gx)[1] + np.gradient(gy)[0]  # Laplacien approximé
        
        depth = field_abs * 0.7 + np.abs(lap) * 0.3
        depth = depth / (np.max(depth) + 1e-12)
        
        return depth


class HarmonicAudioCore:
    """
    Noyau de génération audio harmonique.
    
    Les 7 constantes Hₙ deviennent :
      - Ratios de fréquences pour les harmoniques
      - Coefficients d'enveloppe
      - Paramètres de modulation
    """
    
    SAMPLE_RATE = 44100
    
    # Notes de la gamme dorée (basée sur φ)
    DORIAN_SCALE = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88]  # Do Ré Mi Fa Sol La Si
    
    @staticmethod
    def harmonic_frequencies(fundamental: float = 220.0, n_harmonics: int = 7) -> np.ndarray:
        """
        Génère les fréquences harmoniques basées sur les Hₙ.
        
        fₙ = fondamentale × Hₙ (les constantes comme multiplicateurs)
        """
        return np.array([fundamental * h for h in H_CONSTANTS[:n_harmonics]])
    
    @staticmethod
    def harmonic_envelope(duration: float, n: int, sample_rate: int = 44100) -> np.ndarray:
        """
        Enveloppe ADSR basée sur la constante harmonique Hₙ.
        
        - φ → attaque lente et soutenue (proportion dorée)
        - e → decay exponentiel naturel
        - e/π → release avec tremblement
        """
        t = np.linspace(0, duration, int(sample_rate * duration))
        h = H_CONSTANTS[min(n - 1, 6)]
        
        # Attaque (basée sur φ : n=1 → attaque longue, n=7 → attaque courte)
        attack_time = duration * 0.1 * (1.0 + h / 10.0)
        attack_samples = int(attack_time * sample_rate)
        
        # Decay (basé sur e)
        decay_time = duration * 0.3 / math.sqrt(h)
        decay_samples = int(decay_time * sample_rate)
        
        # Sustain (basé sur √2)
        sustain_level = 0.6 + 0.2 * math.sin(n * PI / 7)
        
        # Release (basé sur e/π)
        release_time = duration * 0.4 / (h + 0.5)
        release_samples = int(release_time * sample_rate)
        
        envelope = np.ones(len(t)) * sustain_level
        
        # Ramp up (attack)
        if attack_samples > 0 and attack_samples < len(t):
            envelope[:attack_samples] = np.linspace(0, 1.0, attack_samples)
        
        # Ramp to sustain (decay)
        decay_end = min(attack_samples + decay_samples, len(t))
        if decay_end > attack_samples:
            decay_len = decay_end - attack_samples
            envelope[attack_samples:decay_end] = np.linspace(1.0, sustain_level, decay_len)
        
        # Release
        release_start = max(1, len(t) - release_samples)
        envelope[release_start:] = np.linspace(sustain_level, 0, len(t) - release_start)
        
        return envelope
    
    @staticmethod
    def generate_harmonic_wave(frequency: float, duration: float,
                               wave_type: str = 'sine',
                               n_layer: int = 1,
                               sample_rate: int = 44100) -> np.ndarray:
        """
        Génère une onde audio pure pour une couche harmonique.
        
        Args:
            frequency: Fréquence en Hz
            duration: Durée en secondes
            wave_type: 'sine', 'triangle', 'square', 'sawtooth'
            n_layer: Numéro de couche harmonique (1-7)
        """
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        h = H_CONSTANTS[min(n_layer - 1, 6)]
        
        if wave_type == 'sine':
            wave = np.sin(2 * PI * frequency * t)
        elif wave_type == 'triangle':
            wave = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
        elif wave_type == 'square':
            wave = np.sign(np.sin(2 * PI * frequency * t))
        elif wave_type == 'sawtooth':
            wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
        else:
            wave = np.sin(2 * PI * frequency * t)
        
        # Appliquer l'enveloppe harmonique
        envelope = HarmonicAudioCore.harmonic_envelope(duration, n_layer, sample_rate)
        
        # Modulation de phase subtile basée sur e/π (spirale)
        phase_mod = np.sin(2 * PI * frequency * t * E_PI * 0.1) * 0.05 * h / PHI
        
        return wave * envelope * (1.0 + phase_mod)


class SeedManager:
    """
    Gestionnaire de seeds pour la génération reproductible.
    Chaque seed produit un Ψ₁ unique.
    """
    
    @staticmethod
    def text_to_seed(text: str) -> int:
        """Convertit un texte en seed déterministe."""
        h = hashlib.sha256(text.encode()).hexdigest()
        return int(h[:8], 16)
    
    @staticmethod
    def time_seed() -> int:
        """Seed basée sur le temps."""
        return int(time.time() * 1000) % (2**31)
    
    @staticmethod
    def compose_seed(base: int, layer: int, variant: int = 0) -> int:
        """Compose un seed à partir d'une base + numéro de couche."""
        return (base * 7 + layer) * 31 + variant


# ==============================================================================
# MÉTRIQUES HARMONIQUES
# ==============================================================================

def compute_harmonic_coherence(field: np.ndarray) -> float:
    """
    Mesure la cohérence harmonique d'un champ.
    1.0 = parfaitement harmonique, 0.0 = chaos total.
    """
    # Analyse de Fourier 2D
    fft = np.abs(np.fft.fft2(field))
    fft_shifted = np.fft.fftshift(fft)
    
    # Mesure de concentration spectrale (plus concentré = plus harmonique)
    total_energy = np.sum(fft_shifted**2)
    if total_energy < 1e-12:
        return 0.0
    
    # Énergie dans les pics principaux vs énergie totale
    sorted_fft = np.sort(fft_shifted.flatten())[::-1]
    top_energy = np.sum(sorted_fft[:100]**2)
    
    return float(top_energy / total_energy)


def compute_symmetry_score(field: np.ndarray) -> float:
    """Mesure de symétrie du champ (0 = asymétrique, 1 = parfaitement symétrique)."""
    h, w = field.shape
    
    # Symétrie horizontale
    h_flip = np.fliplr(field)
    h_sym = 1.0 - np.mean(np.abs(field - h_flip)) / (np.mean(np.abs(field)) + 1e-12)
    
    # Symétrie verticale
    v_flip = np.flipud(field)
    v_sym = 1.0 - np.mean(np.abs(field - v_flip)) / (np.mean(np.abs(field)) + 1e-12)
    
    return float(np.clip((h_sym + v_sym) / 2, 0, 1))


def compute_golden_ratio_score(field: np.ndarray) -> float:
    """
    Score de présence du nombre d'or dans la structure.
    Mesure à quel point les proportions spatiales suivent φ.
    """
    h, w = field.shape
    ratio = w / h if w > h else h / w
    
    # Distance au nombre d'or
    golden_distance = abs(ratio - PHI) / PHI
    
    return float(1.0 / (1.0 + golden_distance * 10))


# ==============================================================================
# EXPORT / UTILITAIRES
# ==============================================================================

def normalize_field(field: np.ndarray) -> np.ndarray:
    """Normalise un champ dans [-1, 1]."""
    f_max = np.max(np.abs(field))
    if f_max < 1e-12:
        return field
    return field / f_max


def blend_fields(field_a: np.ndarray, field_b: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """Mélange deux champs harmoniques avec poids alpha."""
    return alpha * field_a + (1 - alpha) * field_b


def save_image(rgb: np.ndarray, filepath: str):
    """Sauvegarde une image RGB au format PNG."""
    from PIL import Image
    img = Image.fromarray(rgb, 'RGB')
    img.save(filepath)


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 70)
    print("  GENERATEUR HARMONIQUE -- Noyau Theorique")
    print("  Psi = Sigma H_n (Psi_1)^n")
    print("=" * 70)
    
    print("\n  Constantes harmoniques H_n :")
    for i, (name, val) in enumerate(zip(H_NAMES, H_CONSTANTS)):
        print(f"    H{i+1} = {val:.6f}  ({name})")
    
    print(f"\n  Génération d'un champ harmonique 256×256...")
    field = HarmonicField(width=256, height=256, seed=42)
    psi = field.get_psi_total()
    
    print(f"    Dimensions : {psi.shape}")
    print(f"    Min/Max    : {psi.min():.4f} / {psi.max():.4f}")
    print(f"    Énergie    : {np.sum(psi**2):.2f}")
    
    print(f"\n  Contributions des couches :")
    for n in range(1, 8):
        contrib = field.get_layer_contribution(n)
        bar = '█' * int(contrib * 40)
        print(f"    H{n} ({H_NAMES[n-1]:<12s}) : {contrib:6.2%}  {bar}")
    
    print(f"\n  Métriques :")
    print(f"    Cohérence harmonique : {compute_harmonic_coherence(psi):.4f}")
    print(f"    Symétrie            : {compute_symmetry_score(psi):.4f}")
    print(f"    Score doré          : {compute_golden_ratio_score(psi):.4f}")
    
    # Test RGB conversion
    print(f"\n  Conversion RGB (palette 'cosmique')...")
    rgb = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
    print(f"    Dimensions RGB : {rgb.shape}")
    print(f"    Plage valeurs  : [{rgb.min()}, {rgb.max()}]")
    
    print(f"\n  ✅ Noyau harmonique opérationnel.")