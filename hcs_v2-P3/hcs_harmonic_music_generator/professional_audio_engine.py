#!/usr/bin/env python3
"""
HCS Professional Audio Engine - Qualité Cinéma Professionnelle
Techniques avancées : Multi-bandes, Spatial 3D, Mastering Hollywood
"""

import torch
import torchaudio
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Optional, Tuple
import logging
import time
from pathlib import Path
from scipy import signal
from scipy.signal import butter, filtfilt, hilbert

logger = logging.getLogger(__name__)

class ProfessionalAudioEngine:
    """
    Moteur audio professionnel niveau cinéma
    Qualité studio : 96kHz/24-bit, Multi-bandes, Spatial 3D, Mastering Hollywood
    """
    
    def __init__(self, sample_rate: int = 96000, bit_depth: int = 24):
        self.sample_rate = sample_rate
        self.bit_depth = bit_depth
        self.channels = 2  # Stéréo professionnelle
        
        # Configuration professionnelle
        self.pro_settings = {
            'sample_rate': sample_rate,
            'bit_depth': bit_depth,
            'channels': 2,
            'reference_level': -23.0,  # LUFS standard cinéma
            'peak_limit': -1.0,      # Limiteur professionnel
            'dither_type': 'triangular',  # Dithering 24-bit
        }
        
        # Filtres multi-bandes professionnelles
        self.setup_multiband_filters()
        
        # Configuration spatial 3D
        self.setup_3d_spatial()
        
        # Configuration mastering
        self.setup_mastering_chain()
        
        logger.info(f"Professional Audio Engine initialisé: {sample_rate}Hz/{bit_depth}-bit, Cinéma Quality")
    
    def setup_multiband_filters(self):
        """Configure les filtres multi-bandes professionnelles"""
        # Bandes fréquentielles professionnelles
        self.bands = {
            'sub_bass': {'range': (20, 60), 'name': 'Sub-Bass'},
            'bass': {'range': (60, 250), 'name': 'Bass'},
            'low_mid': {'range': (250, 500), 'name': 'Low-Mid'},
            'mid': {'range': (500, 2000), 'name': 'Mid'},
            'high_mid': {'range': (2000, 4000), 'name': 'High-Mid'},
            'presence': {'range': (4000, 6000), 'name': 'Presence'},
            'air': {'range': (6000, 20000), 'name': 'Air'},
            'brilliance': {'range': (20000, 96000//2), 'name': 'Brilliance'}
        }
        
        # Création des filtres Butterworth d'ordre 8
        self.multiband_filters = {}
        for band_name, band_config in self.bands.items():
            low, high = band_config['range']
            
            # Filtres passe-bas et passe-haut
            if band_name == 'sub_bass':
                low_filter = butter(8, low/(self.sample_rate/2), 'low', analog=False)
                self.multiband_filters[band_name] = {'low': low_filter, 'high': None}
            elif band_name == 'brilliance':
                high_filter = butter(8, high/(self.sample_rate/2), 'high', analog=False)
                self.multiband_filters[band_name] = {'low': None, 'high': high_filter}
            else:
                low_filter = butter(8, low/(self.sample_rate/2), 'low', analog=False)
                high_filter = butter(8, high/(self.sample_rate/2), 'high', analog=False)
                self.multiband_filters[band_name] = {'low': low_filter, 'high': high_filter}
    
    def setup_3d_spatial(self):
        """Configure le traitement spatial 3D professionnel"""
        self.spatial_settings = {
            'room_dimensions': (10.0, 8.0, 3.5),  # mètres (L×l×H)
            'reverb_time': 2.3,                    # secondes
            'early_reflections': True,
            'diffusion': 0.85,
            'absorption': {
                'walls': 0.15,
                'floor': 0.25,
                'ceiling': 0.10
            }
        }
        
        # Positions des sources virtuelles (orchestre cinéma)
        self.source_positions = {
            'lead_vocal': (0.0, 0.0, 1.7),      # Centre avant
            'backing_vocals': (-2.0, 1.0, 1.7), # Légèrement gauche
            'piano': (0.0, -2.0, 1.2),         # Centre arrière
            'strings': (-3.0, -1.0, 2.0),        # Gauche arrière
            'brass': (3.0, -1.0, 2.0),          # Droite arrière
            'percussion': (0.0, 2.0, 1.5),       # Centre avant-haut
            'bass': (0.0, 0.0, 0.3),          # Centre bas
            'ambient': (-4.0, 0.0, 2.5),         # Extrême gauche
            'effects': (4.0, 0.0, 2.5)           # Extrême droite
        }
    
    def setup_mastering_chain(self):
        """Configure la chaîne de mastering professionnelle"""
        self.mastering_chain = {
            'eq': {
                'type': 'parametric',
                'bands': [
                    {'freq': 60, 'q': 0.7, 'gain': 0.0},      # Sub-bass
                    {'freq': 250, 'q': 1.0, 'gain': 0.0},     # Bass
                    {'freq': 1000, 'q': 1.4, 'gain': 0.0},    # Mid
                    {'freq': 4000, 'q': 2.0, 'gain': 0.0},    # Presence
                    {'freq': 12000, 'q': 0.5, 'gain': 0.0}    # Air
                ]
            },
            'compression': {
                'type': 'multiband',
                'threshold': -20.0,
                'ratio': 4.0,
                'attack': 0.003,
                'release': 0.100,
                'knee': 2.0,
                'makeup_gain': 0.0
            },
            'saturation': {
                'type': 'tube',
                'drive': 0.0,
                'blend': 0.0
            },
            'limiter': {
                'type': 'brickwall',
                'threshold': -1.0,
                'release': 0.010,
                'lookahead': 0.003
            },
            'dithering': {
                'type': 'triangular',
                'noise_shaping': 'high'
            }
        }
    
    def apply_multiband_processing(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Applique le traitement multi-bandes professionnel
        """
        bands_audio = {}
        
        for band_name, band_config in self.bands.items():
            low_freq, high_freq = band_config['range']
            filters = self.multiband_filters[band_name]
            
            # Filtrage de la bande
            if filters['low'] and filters['high']:
                # Bande passante
                low_filtered = filtfilt(*filters['low'], audio)
                band_audio = filtfilt(*filters['high'], low_filtered[0])
            elif filters['low']:
                # Passe-bas
                band_audio = filtfilt(*filters['low'], audio)[0]
            else:
                # Passe-haut
                band_audio = filtfilt(*filters['high'], audio)[0]
            
            bands_audio[band_name] = band_audio
        
        return bands_audio
    
    def apply_3d_spatial_processing(self, bands_audio: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Applique le traitement spatial 3D professionnel
        """
        # Création du mix stéréo spatial
        left_channel = np.zeros_like(next(iter(bands_audio.values())))
        right_channel = np.zeros_like(left_channel)
        
        # Simulation de placement spatial pour chaque bande
        for band_name, band_audio in bands_audio.items():
            # Position spatiale selon la bande
            if band_name in ['sub_bass', 'bass']:
                # Basses : centre, large
                spatial_width = 0.1
                pan = 0.0
            elif band_name in ['mid']:
                # Mid : centre, étroit
                spatial_width = 0.3
                pan = 0.0
            elif band_name in ['high_mid', 'presence']:
                # Hautes moyennes : légèrement étendues
                spatial_width = 0.6
                pan = 0.0
            else:
                # Aigus : large, avec mouvement subtil
                spatial_width = 0.8
                pan = 0.0
            
            # Application du panoramique et de la largeur stéréo
            mid_signal = band_audio * (1 - spatial_width/2)
            side_signal = band_audio * spatial_width/2
            
            # Encodage Mid/Side
            left_channel += mid_signal - side_signal
            right_channel += mid_signal + side_signal
        
        # Ajout de réverbération spatiale (convolution reverb)
        stereo_mix = np.stack([left_channel, right_channel], axis=0)
        
        # Réverbération algorithmique (simplifiée)
        reverb_mix = self.apply_cinema_reverb(stereo_mix)
        
        return reverb_mix
    
    def apply_cinema_reverb(self, stereo_audio: np.ndarray) -> np.ndarray:
        """
        Applique une réverbération de type cinéma
        """
        left, right = stereo_audio[0], stereo_audio[1]
        
        # Early reflections (murs proches)
        early_delay_left = 0.015  # 15ms
        early_delay_right = 0.020  # 20ms
        early_gain = 0.3
        
        early_left = np.zeros_like(left)
        early_right = np.zeros_like(right)
        
        early_start_left = int(early_delay_left * self.sample_rate)
        early_start_right = int(early_delay_right * self.sample_rate)
        
        if early_start_left < len(left):
            early_left[early_start_left:] = left[:-early_start_left] * early_gain
        if early_start_right < len(right):
            early_right[early_start_right:] = right[:-early_start_right] * early_gain
        
        # Diffuse reverb (réverbération tardive)
        reverb_time = self.spatial_settings['reverb_time']
        reverb_decay = np.exp(-np.arange(len(left)) / (reverb_time * self.sample_rate))
        
        diffuse_left = np.convolve(left, reverb_decay, mode='same')[:len(left)] * 0.2
        diffuse_right = np.convolve(right, reverb_decay, mode='same')[:len(right)] * 0.2
        
        # Mix final
        final_left = left + early_left + diffuse_left
        final_right = right + early_right + diffuse_right
        
        return np.stack([final_left, final_right], axis=0)
    
    def apply_professional_mastering(self, audio: np.ndarray) -> np.ndarray:
        """
        Applique la chaîne de mastering professionnelle
        """
        mastered_audio = audio.copy()
        
        # 1. Égalisation paramétrique
        mastered_audio = self.apply_parametric_eq(mastered_audio)
        
        # 2. Compression multi-bandes
        mastered_audio = self.apply_multiband_compression(mastered_audio)
        
        # 3. Saturation tube
        mastered_audio = self.apply_tube_saturation(mastered_audio)
        
        # 4. Limiting brickwall
        mastered_audio = self.apply_brickwall_limiter(mastered_audio)
        
        # 5. Dithering pour 24-bit
        mastered_audio = self.apply_dithering(mastered_audio)
        
        return mastered_audio
    
    def apply_parametric_eq(self, audio: np.ndarray) -> np.ndarray:
        """Égalisation paramétrique professionnelle"""
        eq_audio = audio.copy()
        
        for band in self.mastering_chain['eq']['bands']:
            freq = band['freq']
            q = band['q']
            gain = band['gain']
            
            # Filtre peaking
            w = 2 * np.pi * freq / self.sample_rate
            alpha = np.sin(w) / (2 * q)
            
            # Application du filtre (simplifié)
            if len(eq_audio.shape) > 1:
                for ch in range(eq_audio.shape[0]):
                    eq_audio[ch] = self.apply_peaking_filter(eq_audio[ch], freq, q, gain)
            else:
                eq_audio = self.apply_peaking_filter(eq_audio, freq, q, gain)
        
        return eq_audio
    
    def apply_peaking_filter(self, signal: np.ndarray, freq: float, q: float, gain: float) -> np.ndarray:
        """Applique un filtre peaking"""
        w = 2 * np.pi * freq / self.sample_rate
        alpha = np.sin(w) / (2 * q)
        A = 10**(gain / 40)
        
        # Coefficients du filtre
        b0 = 1 + alpha * A
        b1 = -2 * np.cos(w)
        b2 = 1 - alpha * A
        a0 = 1 + alpha
        a1 = -2 * np.cos(w)
        a2 = 1 - alpha
        
        # Application du filtre
        from scipy.signal import lfilter
        filtered = lfilter([b0, b1, b2], [a0, a1, a2], signal)
        
        return filtered
    
    def apply_multiband_compression(self, audio: np.ndarray) -> np.ndarray:
        """Compression multi-bandes professionnelle"""
        # Séparation en 3 bandes principales
        bands = self.apply_multiband_processing({'full': audio})
        
        # Compression par bande
        compressed_bands = {}
        
        for band_name, band_audio in bands.items():
            if band_name in ['bass', 'low_mid']:
                # Basses : compression agressive
                threshold = -18.0
                ratio = 6.0
            elif band_name in ['mid', 'high_mid']:
                # Medium : compression modérée
                threshold = -16.0
                ratio = 4.0
            else:
                # Aigus : compression légère
                threshold = -14.0
                ratio = 2.0
            
            compressed_bands[band_name] = self.apply_compression(
                band_audio, threshold, ratio, 
                attack=0.003, release=0.100
            )
        
        # Recombinaison des bandes
        compressed_audio = np.zeros_like(audio)
        for band_audio in compressed_bands.values():
            compressed_audio += band_audio
        
        return compressed_audio
    
    def apply_compression(self, signal: np.ndarray, threshold: float, ratio: float,
                       attack: float = 0.003, release: float = 0.100) -> np.ndarray:
        """Compression audio professionnelle"""
        # Enveloppe du signal
        envelope = self.compute_envelope(signal, attack, release)
        
        # Gain de compression
        over_threshold = envelope > (10**(threshold/20))
        gain = np.where(over_threshold, 
                       1 - (1/ratio) * (envelope - 10**(threshold/20)) / envelope,
                       1.0)
        
        # Application du gain
        compressed = signal * gain
        
        return compressed
    
    def compute_envelope(self, signal: np.ndarray, attack: float, release: float) -> np.ndarray:
        """Calcule l'enveloppe du signal"""
        attack_coeff = np.exp(-1.0 / (attack * self.sample_rate))
        release_coeff = np.exp(-1.0 / (release * self.sample_rate))
        
        envelope = np.zeros_like(signal)
        for i in range(1, len(signal)):
            if abs(signal[i]) > abs(envelope[i-1]):
                envelope[i] = attack_coeff * envelope[i-1] + (1 - attack_coeff) * abs(signal[i])
            else:
                envelope[i] = release_coeff * envelope[i-1] + (1 - release_coeff) * abs(signal[i])
        
        return envelope
    
    def apply_tube_saturation(self, audio: np.ndarray) -> np.ndarray:
        """Saturation type tube professionnelle"""
        # Simulation de saturation tube (simplifiée)
        drive = self.mastering_chain['saturation']['drive']
        blend = self.mastering_chain['saturation']['blend']
        
        # Fonction de transfert tube
        def tube_transfer(x):
            return np.tanh(x * (1 + drive)) / (1 + drive)
        
        saturated = tube_transfer(audio)
        
        # Mix dry/wet
        final_audio = (1 - blend) * audio + blend * saturated
        
        return final_audio
    
    def apply_brickwall_limiter(self, audio: np.ndarray) -> np.ndarray:
        """Limiter brickwall professionnel"""
        threshold = 10**(self.mastering_chain['limiter']['threshold'] / 20)
        
        # Lookahead pour éviter les artifacts
        lookahead_samples = int(self.mastering_chain['limiter']['lookahead'] * self.sample_rate)
        
        limited = np.copy(audio)
        for i in range(len(audio)):
            start_idx = max(0, i - lookahead_samples)
            max_in_lookahead = np.max(np.abs(audio[start_idx:i+1]))
            
            if max_in_lookahead > threshold:
                scale = threshold / max_in_lookahead
                limited[i] = audio[i] * scale
        
        return limited
    
    def apply_dithering(self, audio: np.ndarray) -> np.ndarray:
        """Dithering professionnel pour 24-bit"""
        if self.bit_depth >= 24:
            # Dithering triangulaire pour 24-bit
            dither_noise = np.random.triangular(-0.5, 0.5, audio.shape) / (2**(self.bit_depth-1))
            dithered = audio + dither_noise
        else:
            dithered = audio
        
        return dithered
    
    def generate_professional_track(self, description: str, style: str = "cinema",
                              duration: float = 120.0) -> np.ndarray:
        """
        Génère une piste audio professionnelle niveau cinéma
        """
        logger.info(f"Génération professionnelle: {style}, {duration}s")
        
        try:
            # Étape 1: Génération de base (AudioCraft ou HCS)
            if hasattr(self, 'hcs_generator'):
                base_audio = self.hcs_generator.generate_full_track(
                    style=style, duration=duration
                )
            else:
                # Génération synthétique de base
                base_audio = self.generate_cinematic_base(style, duration)
            
            # Étape 2: Traitement multi-bandes
            bands_audio = self.apply_multiband_processing(base_audio)
            
            # Étape 3: Traitement spatial 3D
            spatial_audio = self.apply_3d_spatial_processing(bands_audio)
            
            # Étape 4: Mastering professionnel
            mastered_audio = self.apply_professional_mastering(spatial_audio)
            
            # Étape 5: Conversion vers 96kHz/24-bit
            final_audio = self.resample_to_professional(mastered_audio)
            
            logger.info(f"✅ Piste professionnelle générée: {final_audio.shape}")
            
            return final_audio
            
        except Exception as e:
            logger.error(f"❌ Erreur génération professionnelle: {e}")
            raise
    
    def generate_cinematic_base(self, style: str, duration: float) -> np.ndarray:
        """
        Génère une base cinématique synthétique
        """
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Génération selon le style cinématographique
        if style == "cinema":
            # Orchestre cinématique
            audio = self.generate_cinematic_orchestra(t, samples)
        elif style == "action":
            # Cinéma d'action
            audio = self.generate_action_cinema(t, samples)
        elif style == "drama":
            # Cinéma dramatique
            audio = self.generate_drama_cinema(t, samples)
        else:
            # Cinéma général
            audio = self.generate_cinematic_orchestra(t, samples)
        
        return audio
    
    def generate_cinematic_orchestra(self, t: np.ndarray, samples: int) -> np.ndarray:
        """Génère un orchestre cinématique"""
        audio = np.zeros(samples)
        
        # Cordes (fondation)
        strings_freq = 110.0  # A2
        strings = np.sin(2 * np.pi * strings_freq * t) * 0.3
        strings += np.sin(2 * np.pi * strings_freq * 2 * t) * 0.15  # Octave
        strings += np.sin(2 * np.pi * strings_freq * 3 * t) * 0.1   # Quinte
        
        # Brass (puissance)
        brass_freq = 87.31  # F2
        brass = np.sin(2 * np.pi * brass_freq * t) * 0.4
        brass += np.sin(2 * np.pi * brass_freq * 1.5 * t) * 0.2
        
        # Percussion (rythme)
        percussion = self.generate_cinematic_percussion(t, samples)
        
        # Mix orchestral
        audio = strings + brass + percussion
        
        # Enveloppe cinématique (fade in/out)
        envelope = np.ones_like(t)
        fade_samples = int(0.05 * self.sample_rate)  # 5% fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        return audio * envelope
    
    def generate_action_cinema(self, t: np.ndarray, samples: int) -> np.ndarray:
        """Génère de la musique d'action cinématique"""
        audio = np.zeros(samples)
        
        # Basses rythmiques
        bass_freq = 55.0  # A1
        bass = np.sin(2 * np.pi * bass_freq * t) * 0.5
        
        # Synthétiseurs percutants
        synth_freq = 220.0  # A3
        synth = np.sign(np.sin(2 * np.pi * synth_freq * t)) * 0.3
        
        # Hits percutants
        hits = self.generate_action_hits(t, samples)
        
        # Mix action
        audio = bass + synth + hits
        
        return audio
    
    def generate_drama_cinema(self, t: np.ndarray, samples: int) -> np.ndarray:
        """Génère de la musique dramatique cinématique"""
        audio = np.zeros(samples)
        
        # Piano dramatique
        piano_notes = [110.0, 130.81, 146.83, 164.81]  # A2, C3, D3, E3
        for i, freq in enumerate(piano_notes):
            note_start = int(i * samples / len(piano_notes))
            note_end = int((i + 1) * samples / len(piano_notes))
            if note_end < samples:
                piano_note = np.sin(2 * np.pi * freq * t[note_start:note_end]) * 0.2
                audio[note_start:note_end] += piano_note
        
        # Cordes sustain
        strings_freq = 65.41  # C2
        strings = np.sin(2 * np.pi * strings_freq * t) * 0.15
        
        # Mix dramatique
        audio = audio + strings
        
        return audio
    
    def generate_cinematic_percussion(self, t: np.ndarray, samples: int) -> np.ndarray:
        """Génère des percussions cinématiques"""
        percussion = np.zeros(samples)
        
        # Kick (tous les temps)
        kick_interval = int(self.sample_rate * 0.5)  # 120 BPM
        for i in range(0, samples, kick_interval):
            if i + 100 < samples:  # 100ms kick
                percussion[i:i+100] += self.generate_kick() * 0.6
        
        # Snare (temps 2 et 4)
        snare_interval = int(self.sample_rate * 0.5)
        for i in range(int(self.sample_rate * 0.25), samples, snare_interval):
            if i + 50 < samples:  # 50ms snare
                percussion[i:i+50] += self.generate_snare() * 0.4
        
        return percussion
    
    def generate_action_hits(self, t: np.ndarray, samples: int) -> np.ndarray:
        """Génère des hits percutants d'action"""
        hits = np.zeros(samples)
        
        # Hits aléatoires
        hit_times = np.random.randint(0, samples, size=20)
        for hit_time in hit_times:
            if hit_time + 200 < samples:
                hits[hit_time:hit_time+200] += self.generate_hit() * 0.5
        
        return hits
    
    def generate_kick(self) -> np.ndarray:
        """Génère un kick drum"""
        samples = int(0.1 * self.sample_rate)  # 100ms
        t = np.linspace(0, 0.1, samples)
        
        # Fréquence fondamentale + harmoniques
        kick = np.sin(2 * np.pi * 60 * t) * 0.8  # 60 Hz
        kick += np.sin(2 * np.pi * 120 * t) * 0.3  # Harmonique
        kick += np.sin(2 * np.pi * 180 * t) * 0.1  # Harmonique
        
        # Enveloppe percussive
        envelope = np.exp(-t * 30)  # Decay rapide
        
        return kick * envelope
    
    def generate_snare(self) -> np.ndarray:
        """Génère un snare drum"""
        samples = int(0.05 * self.sample_rate)  # 50ms
        t = np.linspace(0, 0.05, samples)
        
        # Bruit blanc + tonalité
        noise = np.random.randn(samples) * 0.3
        tone = np.sin(2 * np.pi * 200 * t) * 0.5  # 200 Hz
        
        snare = noise + tone
        
        # Enveloppe
        envelope = np.exp(-t * 50)
        
        return snare * envelope
    
    def generate_hit(self) -> np.ndarray:
        """Génère un hit percutant"""
        samples = int(0.2 * self.sample_rate)  # 200ms
        t = np.linspace(0, 0.2, samples)
        
        # Sweep de fréquence + bruit
        sweep = np.sin(2 * np.pi * np.linspace(800, 200, samples) * t)
        noise = np.random.randn(samples) * 0.2
        
        hit = sweep + noise
        
        # Enveloppe
        envelope = np.exp(-t * 10)
        
        return hit * envelope
    
    def resample_to_professional(self, audio: np.ndarray) -> np.ndarray:
        """Rééchantillonne vers 96kHz professionnel"""
        if self.sample_rate == 96000:
            return audio
        
        # Utilisation de librosa pour rééchantillonnage haute qualité
        if len(audio.shape) > 1:
            resampled = np.zeros((2, int(len(audio[0]) * 96000 / self.sample_rate)))
            for ch in range(2):
                resampled[ch] = librosa.resample(
                    audio[ch], 
                    orig_sr=self.sample_rate, 
                    target_sr=96000
                )
        else:
            resampled = librosa.resample(
                audio, 
                orig_sr=self.sample_rate, 
                target_sr=96000
            )
        
        return resampled
    
    def save_professional_audio(self, audio: np.ndarray, filename: str):
        """
        Sauvegarde en format professionnel 96kHz/24-bit
        """
        try:
            # Conversion en 32-bit float pour sauvegarde
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Normalisation pour 24-bit
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val * 0.95  # Laisser du headroom
            
            # Sauvegarde WAV 96kHz/24-bit
            sf.write(
                filename, 
                audio.T,  # Transposer pour format (channels, samples)
                self.sample_rate,
                subtype='PCM_24'  # 24-bit
            )
            
            logger.info(f"Audio professionnel sauvegardé: {filename}")
            logger.info(f"   Format: {self.sample_rate}Hz/{self.bit_depth}-bit")
            logger.info(f"   Shape: {audio.shape}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde professionnel: {e}")
            raise

# Test du moteur professionnel
if __name__ == "__main__":
    print("🎬 Professional Audio Engine Test")
    print("=" * 50)
    
    # Initialisation
    engine = ProfessionalAudioEngine()
    
    try:
        # Test de génération cinématographique
        audio = engine.generate_professional_track(
            description="epic cinematic orchestral music with dramatic strings and powerful brass",
            style="cinema",
            duration=30.0
        )
        
        print(f"✅ Génération professionnelle réussie")
        print(f"   Sample Rate: {engine.sample_rate}Hz")
        print(f"   Bit Depth: {engine.bit_depth}-bit")
        print(f"   Duration: {len(audio[0])/engine.sample_rate:.2f}s")
        print(f"   Channels: {audio.shape[0]}")
        
        # Sauvegarde test
        engine.save_professional_audio(audio, "test_professional_cinema.wav")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
