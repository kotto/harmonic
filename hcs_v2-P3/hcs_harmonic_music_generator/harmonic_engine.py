#!/usr/bin/env python3
"""
HCS Harmonic Music Generator - Moteur de Génération Harmonique
Basé sur les principes de la compression harmonique appliqués à la musique
"""

import numpy as np
import librosa
import soundfile as sf
import torch
import torch.nn as nn
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class HarmonicGenerator:
    """
    Générateur de musique basé sur les principes harmoniques HCS
    """
    
    def __init__(self, sample_rate: int = 44100, duration: float = 30.0):
        self.sample_rate = sample_rate
        self.duration = duration
        self.num_samples = int(sample_rate * duration)
        
        # Fréquences fondamentales (notes musicales)
        self.fundamental_freqs = {
            'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
            'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
            'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88
        }
        
        # Harmoniques naturelles (série harmonique)
        self.harmonics = [1.0, 0.5, 0.33, 0.25, 0.2, 0.17, 0.14, 0.12]
        
        # Gammes musicales
        self.scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],  # Majeure
            'minor': [0, 2, 3, 5, 7, 8, 10],  # Mineure
            'pentatonic': [0, 2, 4, 7, 9],  # Pentatonique
            'blues': [0, 3, 5, 6, 7, 10],  # Blues
            'chromatic': list(range(12))  # Chromatique
        }
        
        logger.info(f"Harmonic Generator initialisé: {sample_rate}Hz, {duration}s")
    
    def generate_harmonic_series(self, fundamental_freq: float, duration: float, 
                            amplitude: float = 0.1) -> np.ndarray:
        """
        Génère une série harmonique complète
        """
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        signal = np.zeros_like(t)
        
        for i, harmonic_strength in enumerate(self.harmonics):
            harmonic_freq = fundamental_freq * (i + 1)
            harmonic_signal = amplitude * harmonic_strength * np.sin(2 * np.pi * harmonic_freq * t)
            signal += harmonic_signal
        
        # Enveloppe ADSR simple
        envelope = self._create_adsr_envelope(duration, attack=0.1, decay=0.2, sustain=0.7, release=0.3)
        signal *= envelope
        
        return signal
    
    def _create_adsr_envelope(self, duration: float, attack: float, decay: float, 
                           sustain: float, release: float) -> np.ndarray:
        """Crée une enveloppe ADSR"""
        samples = int(self.sample_rate * duration)
        envelope = np.zeros(samples)
        
        attack_samples = int(self.sample_rate * attack)
        decay_samples = int(self.sample_rate * decay)
        release_samples = int(self.sample_rate * release)
        sustain_samples = samples - attack_samples - decay_samples - release_samples
        
        # Attack
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay
        if decay_samples > 0:
            envelope[attack_samples:attack_samples + decay_samples] = np.linspace(1, sustain, decay_samples)
        
        # Sustain
        if sustain_samples > 0:
            envelope[attack_samples + decay_samples:attack_samples + decay_samples + sustain_samples] = sustain
        
        # Release
        if release_samples > 0:
            envelope[-release_samples:] = np.linspace(sustain, 0, release_samples)
        
        return envelope
    
    def generate_chord(self, root_note: str, chord_type: str = 'major', 
                    duration: float = 2.0) -> np.ndarray:
        """
        Génère un accord harmonique
        """
        if root_note not in self.fundamental_freqs:
            raise ValueError(f"Note {root_note} non valide")
        
        root_freq = self.fundamental_freqs[root_note]
        
        # Définition des accords
        chord_intervals = {
            'major': [0, 4, 7],      # Majeur
            'minor': [0, 3, 7],      # Mineur
            'dim': [0, 3, 6],         # Diminué
            'aug': [0, 4, 8],         # Augmenté
            'maj7': [0, 4, 7, 11],   # 7ème majeur
            'min7': [0, 3, 7, 10],   # 7ème mineur
            'sus4': [0, 5, 7],       # Sus4
            'sus2': [0, 2, 7]        # Sus2
        }
        
        if chord_type not in chord_intervals:
            chord_type = 'major'
        
        chord_signal = np.zeros(int(self.sample_rate * duration))
        
        for interval in chord_intervals[chord_type]:
            note_freq = root_freq * (2 ** (interval / 12))
            note_signal = self.generate_harmonic_series(note_freq, duration, amplitude=0.3)
            chord_signal += note_signal
        
        # Normalisation
        chord_signal = chord_signal / np.max(np.abs(chord_signal)) * 0.7
        
        return chord_signal
    
    def generate_melody(self, scale: str = 'major', key: str = 'C', 
                      tempo: int = 120, bars: int = 4) -> np.ndarray:
        """
        Génère une mélodie harmonique
        """
        if scale not in self.scales:
            scale = 'major'
        
        scale_intervals = self.scales[scale]
        
        # Générer une séquence de notes
        notes_per_bar = 4
        total_notes = notes_per_bar * bars
        
        melody_signal = np.zeros(self.num_samples)
        note_duration = 60.0 / tempo  # Durée d'une noire en secondes
        
        current_time = 0
        for i in range(total_notes):
            # Choisir une note dans la gamme
            scale_degree = np.random.choice(len(scale_intervals))
            octave = np.random.choice([0, 1])  # Octave 0 ou 1
            
            interval = scale_intervals[scale_degree]
            note_freq = self.fundamental_freqs[key] * (2 ** (octave + interval / 12))
            
            # Générer la note
            note_signal = self.generate_harmonic_series(note_freq, note_duration * 0.9, amplitude=0.2)
            
            # Ajouter à la mélodie
            start_sample = int(current_time * self.sample_rate)
            end_sample = min(start_sample + len(note_signal), len(melody_signal))
            
            if start_sample < len(melody_signal):
                melody_signal[start_sample:end_sample] += note_signal[:end_sample-start_sample]
            
            current_time += note_duration
        
        return melody_signal
    
    def generate_bass_line(self, scale: str = 'major', key: str = 'C', 
                         tempo: int = 120, bars: int = 4) -> np.ndarray:
        """
        Génère une ligne de basse harmonique
        """
        if scale not in self.scales:
            scale = 'major'
        
        scale_intervals = self.scales[scale]
        
        # Notes de basse (fondamentales principalement)
        bass_notes = [0, 2, 4]  # Tons principaux de la gamme
        
        bass_signal = np.zeros(self.num_samples)
        note_duration = 60.0 / tempo  # Noire
        
        current_time = 0
        for bar in range(bars):
            for beat in range(4):
                # Choisir une note de basse
                scale_degree = np.random.choice(bass_notes)
                interval = scale_intervals[scale_degree]
                note_freq = self.fundamental_freqs[key] * (2 ** (interval / 12))
                
                # Générer la note de basse (plus grave)
                note_signal = self.generate_harmonic_series(
                    note_freq / 2,  # Une octave plus bas
                    note_duration * 0.95, 
                    amplitude=0.4
                )
                
                # Ajouter à la ligne de basse
                start_sample = int(current_time * self.sample_rate)
                end_sample = min(start_sample + len(note_signal), len(bass_signal))
                
                if start_sample < len(bass_signal):
                    bass_signal[start_sample:end_sample] += note_signal[:end_sample-start_sample]
                
                current_time += note_duration
        
        return bass_signal
    
    def generate_harmonic_progression(self, key: str = 'C', scale: str = 'major', 
                                  bars: int = 8, tempo: int = 120) -> np.ndarray:
        """
        Génère une progression harmonique complète
        """
        # Progressions d'accords courantes
        progressions = {
            'major': [
                ['I', 'IV', 'V', 'I'],      # I-IV-V-I
                ['I', 'vi', 'IV', 'V'],      # I-vi-IV-V
                ['I', 'V', 'vi', 'iii'],     # I-V-vi-iii
                ['ii', 'V', 'I', 'vi'],       # ii-V-I-vi
            ],
            'minor': [
                ['i', 'iv', 'v', 'i'],       # i-iv-v-i
                ['i', 'VI', 'III', 'VII'],    # i-VI-III-VII
                ['i', 'iv', 'VII', 'VI'],     # i-iv-VII-VI
            ]
        }
        
        if scale not in progressions:
            scale = 'major'
        
        progression = np.random.choice(progressions[scale])
        
        # Mapping des accords
        chord_map = {
            'I': ('C', 'major'), 'ii': ('D', 'minor'), 'iii': ('E', 'minor'),
            'IV': ('F', 'major'), 'V': ('G', 'major'), 'vi': ('A', 'minor'),
            'VII': ('B', 'dim'), 'i': ('C', 'minor'), 'iv': ('F', 'minor'),
            'v': ('G', 'minor'), 'VI': ('A', 'major'), 'III': ('E', 'major')
        }
        
        progression_signal = np.zeros(self.num_samples)
        chord_duration = (60.0 / tempo) * 4  # 4 temps par accord
        
        current_time = 0
        for chord_symbol in progression:
            if chord_symbol in chord_map:
                note_root, chord_type = chord_map[chord_symbol]
                
                # Ajuster pour la tonalité
                if key != 'C':
                    # Transposition simplifiée
                    note_root = key  # Pour l'instant, utiliser la note de base
                
                chord_signal = self.generate_chord(note_root, chord_type, chord_duration)
                
                start_sample = int(current_time * self.sample_rate)
                end_sample = min(start_sample + len(chord_signal), len(progression_signal))
                
                if start_sample < len(progression_signal):
                    progression_signal[start_sample:end_sample] += chord_signal[:end_sample-start_sample]
                
                current_time += chord_duration
        
        return progression_signal
    
    def generate_full_track(self, style: str = 'pop', key: str = 'C', 
                          tempo: int = 120, duration: float = 30.0) -> np.ndarray:
        """
        Génère une piste musicale complète
        """
        self.duration = duration
        self.num_samples = int(self.sample_rate * duration)
        
        # Configuration selon le style
        styles = {
            'pop': {
                'scale': 'major',
                'bass': True,
                'melody': True,
                'chords': True,
                'drums': False
            },
            'jazz': {
                'scale': 'major',
                'bass': True,
                'melody': True,
                'chords': True,
                'drums': False
            },
            'classical': {
                'scale': 'major',
                'bass': True,
                'melody': True,
                'chords': True,
                'drums': False
            },
            'electronic': {
                'scale': 'pentatonic',
                'bass': True,
                'melody': True,
                'chords': True,
                'drums': False
            }
        }
        
        if style not in styles:
            style = 'pop'
        
        config = styles[style]
        bars = int(duration / (60.0 / tempo) * 4)  # Nombre de mesures
        
        full_signal = np.zeros(self.num_samples)
        
        # Générer les couches
        if config['chords']:
            chords = self.generate_harmonic_progression(key, config['scale'], bars, tempo)
            full_signal += chords * 0.3
        
        if config['bass']:
            bass = self.generate_bass_line(config['scale'], key, tempo, bars)
            full_signal += bass * 0.4
        
        if config['melody']:
            melody = self.generate_melody(config['scale'], key, tempo, bars)
            full_signal += melody * 0.3
        
        # Normalisation finale
        if np.max(np.abs(full_signal)) > 0:
            full_signal = full_signal / np.max(np.abs(full_signal)) * 0.8
        
        return full_signal
    
    def save_audio(self, signal: np.ndarray, filename: str, format: str = 'wav'):
        """
        Sauvegarde l'audio généré
        """
        sf.write(filename, signal, self.sample_rate)
        logger.info(f"Audio sauvegardé: {filename}")
    
    def analyze_harmonics(self, signal: np.ndarray) -> Dict:
        """
        Analyse le contenu harmonique d'un signal
        """
        # Analyse FFT
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/self.sample_rate)
        magnitude = np.abs(fft)
        
        # Trouver les pics de fréquence
        peaks = []
        for i in range(1, len(magnitude)//2):
            if magnitude[i] > magnitude[i-1] and magnitude[i] > magnitude[i+1]:
                if magnitude[i] > np.max(magnitude) * 0.1:  # Seuil de 10%
                    peaks.append((freqs[i], magnitude[i]))
        
        # Trier par magnitude
        peaks.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'dominant_frequencies': peaks[:10],
            'fundamental_freq': peaks[0][0] if peaks else 0,
            'harmonic_content': len(peaks),
            'spectral_centroid': np.sum(freqs[:len(freqs)//2] * magnitude[:len(magnitude)//2]) / np.sum(magnitude[:len(magnitude)//2])
        }
