#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GÉNÉRATEUR AUDIO HARMONIQUE
=============================
Basé sur la Théorie Harmonique : Ψ(t) = Σ Hₙ (Ψ₁)ⁿ en audio

Transforme les 7 constantes harmoniques en musique et paysages sonores :
  H₁ (φ)   : Fondamentale dorée — fréquence de base (ratio 1.618:1)
  H₂ (π)   : Pulsation cyclique — rythme, enveloppes périodiques
  H₃ (e)   : Amortissement naturel — decay, release, réverbération
  H₄ (√2)  : Harmonique d'octave — doublement de fréquence
  H₅ (√3)  : Harmonique de quinte — profondeur sonore
  H₆ (√5)  : Harmonique supérieure — brillance, présence
  H₇ (e/π) : Tremblement spiral — modulation de phase, vibrato

Usage :
  python harmonic_audio_generator.py --demo
  python harmonic_audio_generator.py --seed 42 --duration 10 --output musique.wav
"""

import numpy as np
import math
import sys
import os
import argparse
import time
import struct
import wave
from typing import Dict, Any, List, Optional, Tuple, Generator
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
    H_CONSTANTS, H_NAMES, H_ROLES_AUDIO,
    HarmonicAudioCore, SeedManager,
    FREQUENCE_FONDAMENTALE
)


class HarmonicMusicGenerator:
    """
    Générateur de musique et d'audio harmonique.
    
    Utilise les 7 constantes Hₙ pour créer :
      - Mélodies basées sur la gamme dorée
      - Harmonies par superposition des couches
      - Rythmes basés sur les ratios des Hₙ
      - Effets de réverbération naturelle (e)
    """
    
    SAMPLE_RATE = 44100
    
    # Gamme pentatonique dorée (basée sur φ)
    DORIAN_SCALE = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88]
    
    # Gamme pentatonique chinoise ancienne
    PENTATONIC = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33]
    
    # Modes harmoniques
    MODES = {
        'dorian': [0, 2, 3, 5, 7, 9, 10],
        'phrygian': [0, 1, 3, 5, 7, 8, 10],
        'lydian': [0, 2, 4, 6, 7, 9, 11],
        'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    }
    
    def __init__(self, seed: int = 42, sample_rate: int = 44100):
        self.seed = seed
        self.sample_rate = sample_rate
        np.random.seed(seed)
    
    def generate_harmonic_scale(self, fundamental: float = 220.0) -> np.ndarray:
        """Génère une gamme basée sur les ratios Hₙ."""
        return np.array([fundamental * h / PHI for h in H_CONSTANTS])
    
    def compose_melody(self, duration: float = 8.0,
                       n_notes: int = 32,
                       mode: str = 'dorian',
                       octaves: int = 2) -> np.ndarray:
        """
        Compose une mélodie harmonique.
        
        Les notes sont choisies selon une marche aléatoire guidée par φ :
        - La probabilité de saut est proportionnelle à 1/φ (petits sauts privilégiés)
        - Le rythme suit les ratios des Hₙ
        """
        scale = self.generate_harmonic_scale(220.0)
        scale = np.concatenate([scale, scale * 2])  # 2 octaves
        n_scale = len(scale) // octaves
        
        note_duration = duration / n_notes
        total_samples = int(self.sample_rate * duration)
        audio = np.zeros(total_samples, dtype=np.float64)
        
        current_note = n_scale // 2  # Commencer au milieu de la gamme
        
        for i in range(n_notes):
            # Choisir la prochaine note (marche aléatoire harmonique)
            # Probabilité de saut basée sur φ : favorise les sauts de 2, 3, 5, 7
            jump_probs = np.array([1.0 / abs(j) if j != 0 else 0
                                   for j in range(-n_scale, n_scale + 1)])
            jump_probs = np.exp(-np.arange(-n_scale, n_scale + 1)**2 / (2 * PHI**2))
            jump_probs = jump_probs / jump_probs.sum()
            jump_choice = np.random.choice(np.arange(-n_scale, n_scale + 1), p=jump_probs)
            
            current_note = max(0, min(len(scale) - 1, current_note + jump_choice))
            freq = scale[current_note]
            
            # Rythme : durée de la note basée sur les ratios Hₙ
            h_idx = i % 7
            rhythm_factor = H_CONSTANTS[h_idx] / PHI
            actual_duration = note_duration * rhythm_factor * 0.7
            
            # Générer la note
            start_sample = int(i * note_duration * self.sample_rate)
            n_samples = int(actual_duration * self.sample_rate)
            end_sample = min(start_sample + n_samples, total_samples)
            actual_samples = end_sample - start_sample
            
            if actual_samples > 0:
                # Onde principale (sinusoïdale)
                t = np.linspace(0, actual_duration, actual_samples, endpoint=False)
                
                # Mélange de types d'ondes selon la couche Hₙ
                wave_type_idx = h_idx % 4
                if wave_type_idx == 0:
                    wave = np.sin(2 * PI * freq * t)
                elif wave_type_idx == 1:
                    wave = np.sin(2 * PI * freq * t) + 0.3 * np.sin(2 * PI * freq * 2 * t)
                elif wave_type_idx == 2:
                    wave = np.sin(2 * PI * freq * t) + 0.2 * np.sin(2 * PI * freq * 3 * t)
                else:
                    wave = np.sin(2 * PI * freq * t) + 0.15 * np.sin(2 * PI * freq * PHI * t)
                
                # Enveloppe harmonique
                env = HarmonicAudioCore.harmonic_envelope(
                    actual_duration, h_idx + 1, self.sample_rate
                )[:actual_samples]
                
                # Vibrato spirale (e/π)
                vibrato = np.sin(2 * PI * freq * t * E_PI * 0.01) * 0.02 * H_CONSTANTS[h_idx]
                wave *= (1.0 + vibrato)
                
                audio[start_sample:end_sample] += wave * env * 0.3
        
        # Normalisation
        audio_max = np.max(np.abs(audio))
        if audio_max > 1e-12:
            audio = audio / audio_max * 0.9
        
        return audio
    
    def generate_harmony_pad(self, fundamental: float = 110.0,
                             duration: float = 5.0,
                             n_harmonics: int = 7) -> np.ndarray:
        """
        Génère un pad harmonique (nappe sonore).
        
        Superpose les 7 fréquences harmoniques avec leurs enveloppes Hₙ.
        """
        total_samples = int(self.sample_rate * duration)
        audio = np.zeros(total_samples, dtype=np.float64)
        t = np.linspace(0, duration, total_samples, endpoint=False)
        
        for n in range(1, n_harmonics + 1):
            h = H_CONSTANTS[n - 1]
            freq = fundamental * h / PHI
            
            # Onde sinusoïdale avec légère modulation
            mod_freq = freq * E_PI * 0.01  # Modulation spirale
            wave = np.sin(2 * PI * freq * t + np.sin(2 * PI * mod_freq * t) * 0.1)
            
            # Harmoniques supérieures (√5)
            if n >= 5:
                wave += np.sin(2 * PI * freq * 2 * t) * 0.15 * SQRT5 / 5
            
            # Enveloppe
            env = HarmonicAudioCore.harmonic_envelope(duration, n, self.sample_rate)
            
            # Volume inversement proportionnel à l'indice (plus aigu = plus faible)
            volume = 0.3 / math.sqrt(n)
            
            audio += wave * env * volume
        
        audio_max = np.max(np.abs(audio))
        if audio_max > 1e-12:
            audio = audio / audio_max * 0.85
        
        return audio
    
    def generate_rhythm_track(self, duration: float = 8.0,
                              bpm: float = 120.0) -> np.ndarray:
        """
        Génère une piste rythmique basée sur les ratios harmoniques.
        
        Les percussions sont modélisées comme des impulsions avec decay exponentiel (e).
        """
        total_samples = int(self.sample_rate * duration)
        audio = np.zeros(total_samples, dtype=np.float64)
        
        beat_duration = 60.0 / bpm  # Durée d'un temps en secondes
        
        # Motif rythmique basé sur les ratios Hₙ
        # φ:1 = temps fort, 1/φ = temps faible
        rhythm_pattern = np.array([PHI, 1.0, PHI, PHI_INV, PHI, 1.0, PHI_INV, 1.0])
        rhythm_pattern = rhythm_pattern / PHI  # Normaliser
        
        beat_times = []
        current_time = 0.0
        
        while current_time < duration:
            for ratio in rhythm_pattern:
                if current_time >= duration:
                    break
                beat_times.append((current_time, ratio))
                current_time += beat_duration * ratio
        
        for beat_time, strength in beat_times:
            start_sample = int(beat_time * self.sample_rate)
            
            # Impulsion : bruit blanc filtré + decay exponentiel (e)
            pulse_duration = 0.2  # secondes
            pulse_samples = int(pulse_duration * self.sample_rate)
            end_sample = min(start_sample + pulse_samples, total_samples)
            actual_samples = end_sample - start_sample
            
            if actual_samples > 0:
                t_pulse = np.linspace(0, actual_samples / self.sample_rate,
                                      actual_samples, endpoint=False)
                
                # Synthèse de kick drum simplifiée
                # Fréquence qui descend (pitch bend exponentiel)
                freq_start = 150.0
                freq_end = 40.0
                freq_t = freq_start * np.exp(-t_pulse * E * 15)
                
                phase = 2 * PI * np.cumsum(freq_t) / self.sample_rate
                kick = np.sin(phase)
                
                # Bruit pour l'attaque
                noise = np.random.random(actual_samples) * 0.5 - 0.25
                noise_env = np.exp(-t_pulse * E * 30)
                
                kick = kick * 0.7 + noise * noise_env * 0.3
                
                # Enveloppe d'amplitude
                amp_env = np.exp(-t_pulse * E * 8) * strength
                kick *= amp_env
                
                audio[start_sample:end_sample] += kick * 0.4
        
        audio_max = np.max(np.abs(audio))
        if audio_max > 1e-12:
            audio = audio / audio_max * 0.9
        
        return audio
    
    def generate_full_composition(self, duration: float = 15.0,
                                  bpm: float = 100.0) -> np.ndarray:
        """
        Compose une pièce musicale complète combinant :
          - Mélodie harmonique
          - Pad d'harmonie
          - Piste rythmique
        """
        print(f"  Composition harmonique ({duration:.0f}s, {bpm:.0f} BPM)...")
        
        # Générer les pistes
        melody = self.compose_melody(duration=duration, n_notes=int(duration * 4))
        pad = self.generate_harmony_pad(fundamental=110.0, duration=duration)
        rhythm = self.generate_rhythm_track(duration=duration, bpm=bpm)
        
        # Mixage
        pad_short = pad[:len(melody)] if len(pad) > len(melody) else np.pad(pad, (0, len(melody) - len(pad)))
        rhythm_short = rhythm[:len(melody)] if len(rhythm) > len(melody) else np.pad(rhythm, (0, len(melody) - len(rhythm)))
        melody = melody[:min(len(melody), len(pad_short), len(rhythm_short))]
        pad_short = pad_short[:len(melody)]
        rhythm_short = rhythm_short[:len(melody)]
        
        # Mix : mélodie 40%, pad 35%, rythme 25%
        mix = melody * 0.40 + pad_short * 0.35 + rhythm_short * 0.25
        
        # Réverbération naturelle simplifiée (e - amortissement)
        reverb_length = int(0.3 * self.sample_rate)  # 300ms de réverb
        reverb_ir = np.exp(-np.arange(reverb_length) * E / (reverb_length * 0.3))
        reverb_ir = reverb_ir / np.sum(reverb_ir)
        
        # Convolution pour la réverb
        mix_reverb = np.convolve(mix, reverb_ir, mode='same') * 0.3
        mix_final = mix + mix_reverb
        
        # Normalisation finale
        mix_max = np.max(np.abs(mix_final))
        if mix_max > 1e-12:
            mix_final = mix_final / mix_max * 0.95
        
        return mix_final
    
    def generate_ambient_soundscape(self, duration: float = 30.0,
                                    n_layers: int = 4) -> np.ndarray:
        """
        Génère un paysage sonore ambient (nappe évolutive).
        
        Plusieurs couches de pads évoluent avec des modulations lentes.
        """
        total_samples = int(self.sample_rate * duration)
        audio = np.zeros(total_samples, dtype=np.float64)
        t = np.linspace(0, duration, total_samples, endpoint=False)
        
        fundamentals = [55.0, 82.41, 110.0, 146.83, 220.0]  # La, Mi, La, Ré, La
        
        for layer in range(n_layers):
            fund = fundamentals[layer % len(fundamentals)]
            
            # Modulation lente de la fréquence
            freq_mod = fund * (1.0 + 0.01 * np.sin(t * PI * 0.1 * (layer + 1)))
            
            # Génération du pad pour cette couche
            layer_audio = np.zeros(total_samples, dtype=np.float64)
            
            for n in range(1, 5):  # 4 harmoniques par couche
                h = H_CONSTANTS[(layer + n) % 7]
                harm_freq = freq_mod * h / PHI
                
                # Onde avec modulation de phase lente
                phase = 2 * PI * np.cumsum(harm_freq) / self.sample_rate
                phase += np.sin(t * PI * 0.05 * h) * 0.2
                wave = np.sin(phase)
                
                # Filtrage passe-bas simple (moyenne mobile)
                window = 10
                wave_smooth = np.convolve(wave, np.ones(window)/window, mode='same')
                
                # Volume
                volume = 0.15 / (n + layer * 0.5)
                layer_audio += wave_smooth * volume
            
            # Panoramique lent (gauche-droite) basé sur π
            pan = 0.5 + 0.5 * np.sin(t * PI * 0.03 * (layer + 1))
            
            audio += layer_audio * 0.7
        
        # Normalisation
        audio_max = np.max(np.abs(audio))
        if audio_max > 1e-12:
            audio = audio / audio_max * 0.9
        
        return audio
    
    def generate_sound_effect(self, effect_type: str = 'sweep',
                              duration: float = 1.0) -> np.ndarray:
        """
        Génère un effet sonore harmonique.
        
        Types :
          - 'sweep'  : Balayage de fréquence (comme un whoosh)
          - 'bling'  : Son cristallin bref
          - 'bass'   : Impact basse fréquence
          - 'spiral' : Son tourbillonnant
        """
        total_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, total_samples, endpoint=False)
        
        if effect_type == 'sweep':
            # Balayage logarithmique de fréquence
            f_start, f_end = 100, 8000
            freq = f_start * (f_end / f_start) ** (t / duration)
            phase = 2 * PI * np.cumsum(freq) / self.sample_rate
            audio = np.sin(phase)
            env = np.exp(-t * E * 2)  # Decay exponentiel
            audio *= env * 0.5
        
        elif effect_type == 'bling':
            # Son cristallin : superposition d'harmoniques avec decay rapide
            audio = np.zeros(total_samples, dtype=np.float64)
            for n in range(1, 8):
                h = H_CONSTANTS[n - 1]
                freq = 2000 * h / PHI
                audio += np.sin(2 * PI * freq * t) * np.exp(-t * E * 10 / n)
            audio = audio / (np.max(np.abs(audio)) + 1e-12) * 0.7
        
        elif effect_type == 'bass':
            # Impact basse : sinus grave + bruit
            audio = np.sin(2 * PI * 60 * t) * np.exp(-t * E * 5)
            noise = np.random.random(total_samples) * 0.3 * np.exp(-t * E * 20)
            audio = (audio * 0.7 + noise * 0.3) * 0.8
        
        elif effect_type == 'spiral':
            # Son tourbillonnant : modulation de fréquence spirale
            freq_base = 440.0
            freq_mod = 100.0 * np.sin(t * PI * E_PI * 10)
            freq = freq_base + freq_mod
            phase = 2 * PI * np.cumsum(freq) / self.sample_rate
            audio = np.sin(phase) * np.exp(-t * 2)
            audio *= 0.6
        
        else:
            audio = np.zeros(total_samples)
        
        audio_max = np.max(np.abs(audio))
        if audio_max > 1e-12:
            audio = audio / audio_max * 0.9
        
        return audio


def save_wav(audio: np.ndarray, filepath: str, sample_rate: int = 44100):
    """Sauvegarde un array numpy en fichier WAV."""
    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16 bits
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    
    return filepath


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================

def demo_audio_generator():
    """Démonstration du générateur audio harmonique."""
    print("=" * 70)
    print("  GÉNÉRATEUR AUDIO HARMONIQUE")
    print("  Ψ(t) = Σ Hₙ (Ψ₁)ⁿ → Musique et Sons")
    print("=" * 70)
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'audio')
    os.makedirs(output_dir, exist_ok=True)
    
    gen = HarmonicMusicGenerator(seed=42, sample_rate=44100)
    
    # 1. Composition complète
    print(f"\n  [1] Composition harmonique (15s, 100 BPM)...")
    composition = gen.generate_full_composition(duration=15.0, bpm=100.0)
    filepath = os.path.join(output_dir, 'harmonic_composition.wav')
    save_wav(composition, filepath)
    print(f"    ✅ Composition : {filepath} ({len(composition)/44100:.1f}s)")
    
    # 2. Mélodie seule
    print(f"\n  [2] Mélodie harmonique (8s)...")
    gen2 = HarmonicMusicGenerator(seed=123, sample_rate=44100)
    melody = gen2.compose_melody(duration=8.0, n_notes=32)
    filepath = os.path.join(output_dir, 'harmonic_melody.wav')
    save_wav(melody, filepath)
    print(f"    ✅ Mélodie : {filepath}")
    
    # 3. Pad harmonique
    print(f"\n  [3] Pad harmonique (5s, La 110Hz)...")
    pad = gen.generate_harmony_pad(fundamental=110.0, duration=5.0)
    filepath = os.path.join(output_dir, 'harmonic_pad.wav')
    save_wav(pad, filepath)
    print(f"    ✅ Pad : {filepath}")
    
    # 4. Rythme
    print(f"\n  [4] Piste rythmique (8s, 120 BPM)...")
    rhythm = gen.generate_rhythm_track(duration=8.0, bpm=120.0)
    filepath = os.path.join(output_dir, 'harmonic_rhythm.wav')
    save_wav(rhythm, filepath)
    print(f"    ✅ Rythme : {filepath}")
    
    # 5. Paysage sonore ambient
    print(f"\n  [5] Paysage sonore ambient (20s)...")
    ambient = gen.generate_ambient_soundscape(duration=20.0, n_layers=4)
    filepath = os.path.join(output_dir, 'harmonic_ambient.wav')
    save_wav(ambient, filepath)
    print(f"    ✅ Ambient : {filepath}")
    
    # 6. Effets sonores
    print(f"\n  [6] Effets sonores harmoniques...")
    effects = ['sweep', 'bling', 'bass', 'spiral']
    for effect in effects:
        sfx = gen.generate_sound_effect(effect_type=effect, duration=1.0)
        filepath = os.path.join(output_dir, f'harmonic_sfx_{effect}.wav')
        save_wav(sfx, filepath)
        print(f"    ✅ {effect:<8s} → {filepath}")
    
    # Rapport
    print(f"\n{'='*70}")
    print("  RAPPORT AUDIO HARMONIQUE")
    print(f"{'='*70}")
    
    print(f"\n  Constantes harmoniques en audio :")
    for n, (name, role) in enumerate(zip(H_NAMES, H_ROLES_AUDIO)):
        print(f"    H{n+1} {name:<12s} : {role}")
    
    print(f"\n  Tous les fichiers sauvegardés dans : {output_dir}")
    print(f"  ✅ Générateur audio harmonique opérationnel.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Générateur Audio Harmonique')
    parser.add_argument('--demo', action='store_true', help='Démonstration complète')
    parser.add_argument('--seed', type=int, default=42, help='Seed')
    parser.add_argument('--duration', type=float, default=10.0, help='Durée en secondes')
    parser.add_argument('--output', type=str, default=None, help='Fichier de sortie (.wav)')
    parser.add_argument('--type', type=str, default='composition',
                        choices=['composition', 'melody', 'pad', 'rhythm', 'ambient', 'sweep', 'bling', 'bass', 'spiral'],
                        help='Type de génération')
    
    args = parser.parse_args()
    
    if args.output:
        gen = HarmonicMusicGenerator(seed=args.seed)
        
        if args.type == 'composition':
            audio = gen.generate_full_composition(duration=args.duration)
        elif args.type == 'melody':
            audio = gen.compose_melody(duration=args.duration)
        elif args.type == 'pad':
            audio = gen.generate_harmony_pad(duration=args.duration)
        elif args.type == 'rhythm':
            audio = gen.generate_rhythm_track(duration=args.duration)
        elif args.type == 'ambient':
            audio = gen.generate_ambient_soundscape(duration=args.duration)
        else:
            audio = gen.generate_sound_effect(effect_type=args.type)
        
        save_wav(audio, args.output)
        print(f"Audio sauvegardé : {args.output}")
    else:
        demo_audio_generator()