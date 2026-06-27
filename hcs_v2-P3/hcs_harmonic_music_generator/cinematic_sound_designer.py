#!/usr/bin/env python3
"""
HCS Cinematic Sound Designer - Génération de bruitages cinématographiques haute qualité
Synthèse procédurale, modélisation physique, spatialisation 3D
"""

import numpy as np
import torch
import torchaudio
import librosa
import soundfile as sf
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional, Union
from scipy import signal
from scipy.signal import butter, filtfilt, convolve
import json
import time

logger = logging.getLogger(__name__)

class CinematicSoundDesigner:
    """
    Générateur de bruitages cinématographiques professionnels
    Qualité cinéma : 96kHz/24-bit, spatialisation 3D, dynamique étendue
    """
    
    def __init__(self, sample_rate: int = 96000, bit_depth: int = 24):
        self.sample_rate = sample_rate
        self.bit_depth = bit_depth
        self.channels = 6  # 5.1 surround
        
        # Configuration cinématographique
        self.cinema_config = {
            'sample_rate': sample_rate,
            'bit_depth': bit_depth,
            'channels': self.channels,
            'dynamic_range': 120,  # dB
            'spatial_resolution': '5.1',
            'quality_standard': 'cinema'
        }
        
        # Catégories de bruitages
        self.sound_categories = {
            'ambient': self.init_ambient_generators(),
            'effects': self.init_effects_generators(),
            'foley': self.init_foley_generators(),
            'creatures': self.init_creature_generators(),
            'vehicles': self.init_vehicle_generators(),
            'technology': self.init_tech_generators(),
            'weapons': self.init_weapon_generators(),
            'nature': self.init_nature_generators()
        }
        
        # Bibliothèque de presets
        self.presets = self.load_cinematic_presets()
        
        logger.info(f"🎬 Cinematic Sound Designer initialisé: {sample_rate}Hz/{bit_depth}-bit, 5.1 surround")
    
    def init_ambient_generators(self) -> Dict:
        """Initialise les générateurs d'ambiances"""
        return {
            'forest': self.generate_forest_ambient,
            'ocean': self.generate_ocean_ambient,
            'city': self.generate_city_ambient,
            'space': self.generate_space_ambient,
            'desert': self.generate_desert_ambient,
            'jungle': self.generate_jungle_ambient,
            'underwater': self.generate_underwater_ambient,
            'cave': self.generate_cave_ambient
        }
    
    def init_effects_generators(self) -> Dict:
        """Initialise les générateurs d'effets spéciaux"""
        return {
            'explosion': self.generate_explosion,
            'impact': self.generate_impact,
            'whoosh': self.generate_whoosh,
            'power_up': self.generate_power_up,
            'teleport': self.generate_teleport,
            'shield': self.generate_shield,
            'laser': self.generate_laser,
            'plasma': self.generate_plasma
        }
    
    def init_foley_generators(self) -> Dict:
        """Initialise les générateurs de foley"""
        return {
            'footsteps': self.generate_footsteps,
            'clothing': self.generate_clothing,
            'doors': self.generate_doors,
            'weapons_handling': self.generate_weapons_handling,
            'equipment': self.generate_equipment,
            'paper': self.generate_paper,
            'metal': self.generate_metal,
            'wood': self.generate_wood
        }
    
    def init_creature_generators(self) -> Dict:
        """Initialise les générateurs de créatures"""
        return {
            'dragon': self.generate_dragon,
            'alien': self.generate_alien,
            'monster': self.generate_monster,
            'robot': self.generate_robot,
            'insect': self.generate_insect,
            'bird': self.generate_bird,
            'mammal': self.generate_mammal,
            'aquatic': self.generate_aquatic
        }
    
    def init_vehicle_generators(self) -> Dict:
        """Initialise les générateurs de véhicules"""
        return {
            'spaceship': self.generate_spaceship,
            'car': self.generate_car,
            'helicopter': self.generate_helicopter,
            'tank': self.generate_tank,
            'motorcycle': self.generate_motorcycle,
            'train': self.generate_train,
            'boat': self.generate_boat,
            'airplane': self.generate_airplane
        }
    
    def init_tech_generators(self) -> Dict:
        """Initialise les générateurs technologiques"""
        return {
            'computer': self.generate_computer,
            'hologram': self.generate_hologram,
            'scanner': self.generate_scanner,
            'alarm': self.generate_alarm,
            'interface': self.generate_interface,
            'power_core': self.generate_power_core,
            'shield_generator': self.generate_shield_generator,
            'teleporter': self.generate_teleporter
        }
    
    def init_weapon_generators(self) -> Dict:
        """Initialise les générateurs d'armes"""
        return {
            'laser_gun': self.generate_laser_gun,
            'plasma_rifle': self.generate_plasma_rifle,
            'rocket_launcher': self.generate_rocket_launcher,
            'sword': self.generate_sword,
            'bow': self.generate_bow,
            'grenade': self.generate_grenade,
            'cannon': self.generate_cannon,
            'railgun': self.generate_railgun
        }
    
    def init_nature_generators(self) -> Dict:
        """Initialise les générateurs naturels"""
        return {
            'wind': self.generate_wind,
            'rain': self.generate_rain,
            'thunder': self.generate_thunder,
            'fire': self.generate_fire,
            'water': self.generate_water,
            'earthquake': self.generate_earthquake,
            'volcano': self.generate_volcano,
            'avalanche': self.generate_avalanche
        }
    
    def generate_cinematic_sound(self, 
                               category: str, 
                               sound_type: str, 
                               duration: float = 5.0,
                               parameters: Optional[Dict] = None) -> np.ndarray:
        """
        Génère un son cinématographique de haute qualité
        """
        try:
            logger.info(f"🎬 Génération sonore: {category}/{sound_type}, {duration}s")
            
            # Récupération du générateur
            if category not in self.sound_categories:
                raise ValueError(f"Catégorie non supportée: {category}")
            
            if sound_type not in self.sound_categories[category]:
                raise ValueError(f"Type non supporté: {sound_type}")
            
            generator = self.sound_categories[category][sound_type]
            
            # Paramètres par défaut
            if parameters is None:
                parameters = {}
            
            # Génération du son
            samples = int(self.sample_rate * duration)
            audio = generator(samples, parameters)
            
            # Post-traitement cinématographique
            audio = self.apply_cinematic_processing(audio, parameters)
            
            # Spatialisation 5.1
            audio = self.apply_5_1_spatialization(audio, parameters)
            
            # Mastering cinéma
            audio = self.apply_cinema_mastering(audio)
            
            logger.info(f"✅ Son cinématographique généré: {audio.shape}")
            
            return audio
            
        except Exception as e:
            logger.error(f"❌ Erreur génération sonore: {e}")
            # Fallback : bruit blanc
            return self.generate_fallback_sound(samples)
    
    def apply_cinematic_processing(self, audio: np.ndarray, parameters: Dict) -> np.ndarray:
        """Applique le traitement cinématographique"""
        
        # Filtrage multi-bandes
        audio = self.apply_multiband_filtering(audio)
        
        # Saturation harmonique
        if parameters.get('saturation', 0.5) > 0.3:
            audio = self.apply_harmonic_saturation(audio, parameters['saturation'])
        
        # Compression dynamique
        audio = self.apply_cinema_compression(audio)
        
        # Réverbération spatiale
        if parameters.get('reverb', 0.5) > 0.2:
            audio = self.apply_spatial_reverb(audio, parameters['reverb'])
        
        return audio
    
    def apply_5_1_spatialization(self, audio: np.ndarray, parameters: Dict) -> np.ndarray:
        """Applique la spatialisation 5.1"""
        
        # Configuration 5.1 : [L, R, C, LFE, LS, RS]
        audio_5_1 = np.zeros((6, len(audio)))
        
        # Distribution spatiale selon les paramètres
        spatial_params = parameters.get('spatial', {
            'front_center': 0.4,
            'front_left': 0.3,
            'front_right': 0.3,
            'lfe': 0.2,
            'rear_left': 0.2,
            'rear_right': 0.2
        })
        
        # Canaux principaux
        audio_5_1[0] = audio * spatial_params['front_left']   # L
        audio_5_1[1] = audio * spatial_params['front_right']  # R
        audio_5_1[2] = audio * spatial_params['front_center'] # C
        audio_5_1[3] = self.generate_lfe_channel(audio)     # LFE
        audio_5_1[4] = audio * spatial_params['rear_left']   # LS
        audio_5_1[5] = audio * spatial_params['rear_right']  # RS
        
        return audio_5_1
    
    def apply_cinema_mastering(self, audio: np.ndarray) -> np.ndarray:
        """Applique le mastering cinématographique"""
        
        # Égalisation cinéma
        audio = self.apply_cinema_eq(audio)
        
        # Limiting brickwall
        audio = self.apply_brickwall_limiter(audio)
        
        # Dithering 24-bit
        audio = self.apply_dithering(audio)
        
        return audio
    
    # Générateurs d'ambiances
    def generate_forest_ambient(self, samples: int, params: Dict) -> np.ndarray:
        """Génère une ambiance forêt cinématographique"""
        t = np.linspace(0, samples/self.sample_rate, samples)
        
        # Vent dans les arbres
        wind = self.generate_wind_noise(samples, {'intensity': 0.3, 'variation': 0.8})
        
        # Oiseaux (synthétiques)
        birds = self.generate_bird_calls(samples, {'density': 0.2, 'variety': 0.7})
        
        # Bruits de feuilles
        leaves = self.generate_leaves_rustle(samples, {'intensity': 0.4})
        
        # Mélange des couches
        ambient = wind * 0.5 + birds * 0.3 + leaves * 0.2
        
        return ambient
    
    def generate_ocean_ambient(self, samples: int, params: Dict) -> np.ndarray:
        """Génère une ambiance océan cinématographique"""
        t = np.linspace(0, samples/self.sample_rate, samples)
        
        # Vagues principales
        waves = self.generate_ocean_waves(samples, {'size': 'large', 'intensity': 0.6})
        
        # Écume
        foam = self.generate_foam_noise(samples, {'density': 0.3})
        
        # Mouvement d'eau
        water_movement = self.generate_water_movement(samples, {'current': 0.4})
        
        # Mélange
        ambient = waves * 0.6 + foam * 0.2 + water_movement * 0.2
        
        return ambient
    
    def generate_city_ambient(self, samples: int, params: Dict) -> np.ndarray:
        """Génère une ambiance ville cinématographique"""
        t = np.linspace(0, samples/self.sample_rate, samples)
        
        # Trafic lointain
        traffic = self.generate_distant_traffic(samples, {'density': 0.3})
        
        # Sirenes occasionnelles
        sirens = self.generate_occasional_sirens(samples, {'frequency': 0.1})
        
        # Bourdonnement urbain
        urban_hum = self.generate_urban_hum(samples, {'intensity': 0.4})
        
        # Mélange
        ambient = traffic * 0.4 + sirens * 0.2 + urban_hum * 0.4
        
        return ambient
    
    def generate_space_ambient(self, samples: int, params: Dict) -> np.ndarray:
        """Génère une ambiance espace cinématographique"""
        t = np.linspace(0, samples/self.sample_rate, samples)
        
        # Bourdonnement de vaisseau
        ship_hum = self.generate_ship_hum(samples, {'frequency': 60, 'intensity': 0.3})
        
        # Sons de systèmes
        systems = self.generate_life_support_noise(samples, {'intensity': 0.2})
        
        # Communications radio
        radio = self.generate_space_radio(samples, {'activity': 0.1})
        
        # Mélange
        ambient = ship_hum * 0.5 + systems * 0.3 + radio * 0.2
        
        return ambient
    
    # Générateurs d'effets spéciaux
    def generate_explosion(self, samples: int, params: Dict) -> np.ndarray:
        """Génère une explosion cinématographique"""
        t = np.linspace(0, samples/self.sample_rate, samples)
        
        # Paramètres de l'explosion
        intensity = params.get('intensity', 0.8)
        size = params.get('size', 'medium')
        
        # Phase initiale : détonation
        detonation = self.generate_detonation(samples, intensity)
        
        # Phase principale : onde de choc
        shockwave = self.generate_shockwave(samples, size)
        
        # Phase finale : débris
        debris = self.generate_debris_fall(samples, {'density': 0.5})
        
        # Enveloppe d'explosion
        envelope = self.create_explosion_envelope(t, size)
        
        # Assemblage
        explosion = (detonation * 0.6 + shockwave * 0.3 + debris * 0.1) * envelope
        
        return explosion
    
    def generate_impact(self, samples: int, params: Dict) -> np.ndarray:
        """Génère un impact cinématographique"""
        t = np.linspace(0, samples/self.sample_rate, samples)
        
        # Paramètres
        material = params.get('material', 'metal')
        force = params.get('force', 0.7)
        
        # Son d'impact selon le matériau
        if material == 'metal':
            impact = self.generate_metal_impact(samples, force)
        elif material == 'concrete':
            impact = self.generate_concrete_impact(samples, force)
        elif material == 'wood':
            impact = self.generate_wood_impact(samples, force)
        else:
            impact = self.generate_generic_impact(samples, force)
        
        # Résonance post-impact
        resonance = self.generate_impact_resonance(samples, material)
        
        # Enveloppe d'impact
        envelope = self.create_impact_envelope(t)
        
        # Assemblage
        impact_sound = (impact * 0.8 + resonance * 0.2) * envelope
        
        return impact_sound
    
    def generate_whoosh(self, samples: int, params: Dict) -> np.ndarray:
        """Génère un effet whoosh cinématographique"""
        t = np.linspace(0, samples/self.sample_rate, samples)
        
        # Paramètres
        speed = params.get('speed', 0.7)
        intensity = params.get('intensity', 0.6)
        
        # Bruit de base filtré
        noise = self.generate_filtered_noise(samples, {'type': 'pink', 'cutoff': 2000})
        
        # Modulation de fréquence pour l'effet de mouvement
        freq_mod = 1.0 + speed * np.sin(2 * np.pi * 2 * t)
        
        # Application de la modulation
        whoosh = noise * freq_mod * intensity
        
        # Enveloppe de mouvement
        envelope = self.create_whoosh_envelope(t, speed)
        
        whoosh_sound = whoosh * envelope
        
        return whoosh_sound
    
    # Générateurs de foley
    def generate_footsteps(self, samples: int, params: Dict) -> np.ndarray:
        """Génère des pas cinématographiques"""
        t = np.linspace(0, samples/self.sample_rate, samples)
        
        # Paramètres
        surface = params.get('surface', 'concrete')
        character = params.get('character', 'male')
        speed = params.get('speed', 1.0)
        
        # Génération du son de pas selon la surface
        if surface == 'concrete':
            step_sound = self.generate_concrete_step(samples)
        elif surface == 'grass':
            step_sound = self.generate_grass_step(samples)
        elif surface == 'metal':
            step_sound = self.generate_metal_step(samples)
        else:
            step_sound = self.generate_generic_step(samples)
        
        # Rythme des pas
        step_rhythm = self.create_step_rhythm(t, speed)
        
        # Assemblage
        footsteps = step_sound * step_rhythm
        
        return footsteps
    
    def generate_clothing(self, samples: int, params: Dict) -> np.ndarray:
        """Génère des bruits de vêtements cinématographiques"""
        t = np.linspace(0, samples/self.sample_rate, samples)
        
        # Paramètres
        fabric = params.get('fabric', 'cotton')
        movement = params.get('movement', 'walking')
        
        # Bruit de tissu
        fabric_noise = self.generate_fabric_rustle(samples, fabric)
        
        # Modulation selon le mouvement
        movement_mod = self.create_movement_modulation(t, movement)
        
        clothing_sound = fabric_noise * movement_mod
        
        return clothing_sound
    
    # Outils de traitement audio
    def generate_filtered_noise(self, samples: int, params: Dict) -> np.ndarray:
        """Génère du bruit filtré"""
        noise_type = params.get('type', 'white')
        cutoff = params.get('cutoff', 1000)
        
        # Génération du bruit
        if noise_type == 'white':
            noise = np.random.randn(samples)
        elif noise_type == 'pink':
            noise = self.generate_pink_noise(samples)
        elif noise_type == 'brown':
            noise = self.generate_brown_noise(samples)
        else:
            noise = np.random.randn(samples)
        
        # Filtrage passe-bas
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff / nyquist
        b, a = butter(4, normalized_cutoff, btype='low')
        filtered_noise = filtfilt(b, a, noise)
        
        return filtered_noise
    
    def generate_pink_noise(self, samples: int) -> np.ndarray:
        """Génère du bruit rose"""
        # Algorithme de Voss-McCartney pour le bruit rose
        num_octaves = 8
        white_noise = np.random.randn(samples + num_octaves)
        
        pink_noise = np.zeros(samples)
        for k in range(num_octaves):
            white_octave = white_noise[k::2**k][:samples]
            pink_noise += white_octave / (k + 1)
        
        return pink_noise / np.sqrt(num_octaves)
    
    def generate_brown_noise(self, samples: int) -> np.ndarray:
        """Génère du bruit brun"""
        white_noise = np.random.randn(samples)
        
        # Intégration pour le bruit brun
        brown_noise = np.cumsum(white_noise)
        brown_noise = brown_noise - np.mean(brown_noise)
        
        # Normalisation
        brown_noise = brown_noise / np.max(np.abs(brown_noise))
        
        return brown_noise
    
    def create_explosion_envelope(self, t: np.ndarray, size: str) -> np.ndarray:
        """Crée une enveloppe d'explosion"""
        if size == 'small':
            attack_time = 0.01
            decay_time = 0.5
        elif size == 'large':
            attack_time = 0.05
            decay_time = 2.0
        else:  # medium
            attack_time = 0.02
            decay_time = 1.0
        
        # Enveloppe exponentielle
        envelope = np.zeros_like(t)
        attack_samples = int(attack_time * self.sample_rate)
        decay_samples = int(decay_time * self.sample_rate)
        
        # Phase d'attaque
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Phase de déclin
        envelope[attack_samples:attack_samples+decay_samples] = np.exp(-3 * np.linspace(0, 1, decay_samples))
        
        return envelope
    
    def create_impact_envelope(self, t: np.ndarray) -> np.ndarray:
        """Crée une enveloppe d'impact"""
        attack_time = 0.001
        decay_time = 0.1
        
        attack_samples = int(attack_time * self.sample_rate)
        decay_samples = int(decay_time * self.sample_rate)
        
        envelope = np.zeros_like(t)
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[attack_samples:attack_samples+decay_samples] = np.exp(-5 * np.linspace(0, 1, decay_samples))
        
        return envelope
    
    def create_whoosh_envelope(self, t: np.ndarray, speed: float) -> np.ndarray:
        """Crée une enveloppe de whoosh"""
        # Enveloppe de mouvement
        envelope = np.abs(np.sin(np.pi * t * speed)) * np.exp(-2 * t)
        
        return envelope
    
    def apply_multiband_filtering(self, audio: np.ndarray) -> np.ndarray:
        """Applique un filtrage multi-bandes"""
        # Définition des bandes
        bands = [
            (20, 250),      # Sub-bass
            (250, 500),     # Bass
            (500, 2000),    # Low-mid
            (2000, 4000),   # High-mid
            (4000, 8000),   # Presence
            (8000, 20000)   # High
        ]
        
        filtered_audio = np.zeros_like(audio)
        
        for low, high in bands:
            # Filtre passe-bande
            nyquist = self.sample_rate / 2
            low_norm = low / nyquist
            high_norm = high / nyquist
            
            b, a = butter(4, [low_norm, high_norm], btype='band')
            band_audio = filtfilt(b, a, audio)
            
            # Ajout de la bande
            filtered_audio += band_audio * 0.5
        
        return filtered_audio / len(bands)
    
    def apply_harmonic_saturation(self, audio: np.ndarray, amount: float) -> np.ndarray:
        """Applique une saturation harmonique"""
        # Saturation douce
        saturated = np.tanh(audio * amount * 3) / amount
        
        # Mélange avec le signal original
        mixed = audio * (1 - amount * 0.5) + saturated * amount * 0.5
        
        return mixed
    
    def apply_cinema_compression(self, audio: np.ndarray) -> np.ndarray:
        """Applique une compression cinématographique"""
        # Compression simple (ratio 4:1, threshold -20dB)
        threshold = 0.1
        ratio = 4.0
        
        compressed = np.where(
            np.abs(audio) > threshold,
            threshold + (np.abs(audio) - threshold) / ratio,
            audio
        )
        
        # Restauration du signe
        compressed = np.sign(audio) * compressed
        
        return compressed
    
    def apply_spatial_reverb(self, audio: np.ndarray, amount: float) -> np.ndarray:
        """Applique une réverbération spatiale"""
        # Réverbération simple (convolution avec IR)
        reverb_length = int(0.5 * self.sample_rate)  # 0.5 secondes
        reverb_ir = np.exp(-np.linspace(0, 5, reverb_length)) * np.random.randn(reverb_length) * 0.1
        
        # Convolution
        reverb_signal = convolve(audio, reverb_ir, mode='same')
        
        # Mélange
        wet_signal = audio * (1 - amount) + reverb_signal * amount
        
        return wet_signal
    
    def apply_cinema_eq(self, audio: np.ndarray) -> np.ndarray:
        """Applique une égalisation cinématographique"""
        # EQ paramétrique simple
        # Boost des basses et des aigus pour le cinéma
        eq_filters = [
            {'type': 'lowshelf', 'freq': 100, 'gain': 3},    # +3dB à 100Hz
            {'type': 'highshelf', 'freq': 8000, 'gain': 2},  # +2dB à 8kHz
        ]
        
        eq_audio = audio.copy()
        
        for filt in eq_filters:
            if filt['type'] == 'lowshelf':
                # Filtre low-shelf
                nyquist = self.sample_rate / 2
                freq_norm = filt['freq'] / nyquist
                b, a = butter(2, freq_norm, btype='low')
                filtered = filtfilt(b, a, eq_audio)
                eq_audio = eq_audio + (filtered - eq_audio) * (10 ** (filt['gain'] / 20) - 1)
            
            elif filt['type'] == 'highshelf':
                # Filtre high-shelf
                nyquist = self.sample_rate / 2
                freq_norm = filt['freq'] / nyquist
                b, a = butter(2, freq_norm, btype='high')
                filtered = filtfilt(b, a, eq_audio)
                eq_audio = eq_audio + (filtered - eq_audio) * (10 ** (filt['gain'] / 20) - 1)
        
        return eq_audio
    
    def apply_brickwall_limiter(self, audio: np.ndarray) -> np.ndarray:
        """Applique un limiteur brickwall"""
        # Limitation à -1.0 dB
        limit = 0.95
        
        limited = np.where(
            np.abs(audio) > limit,
            np.sign(audio) * limit,
            audio
        )
        
        return limited
    
    def apply_dithering(self, audio: np.ndarray) -> np.ndarray:
        """Applique un dithering pour 24-bit"""
        # Dithering triangulaire simple
        dither = np.random.uniform(-0.5, 0.5, audio.shape) / (2**24)
        
        dithered = audio + dither
        
        return dithered
    
    def generate_lfe_channel(self, audio: np.ndarray) -> np.ndarray:
        """Génère le canal LFE (subwoofer)"""
        # Extraction des basses fréquences
        nyquist = self.sample_rate / 2
        cutoff = 120 / nyquist  # Coupure à 120Hz
        
        b, a = butter(4, cutoff, btype='low')
        lfe = filtfilt(b, a, audio)
        
        # Amplification pour le LFE
        lfe = lfe * 2.0
        
        return lfe
    
    def generate_fallback_sound(self, samples: int) -> np.ndarray:
        """Génère un son de fallback"""
        # Bruit rose filtré comme fallback
        noise = self.generate_pink_noise(samples)
        
        # Filtrage passe-bas
        nyquist = self.sample_rate / 2
        cutoff = 1000 / nyquist
        b, a = butter(4, cutoff, btype='low')
        filtered = filtfilt(b, a, noise)
        
        return filtered * 0.1
    
    def load_cinematic_presets(self) -> Dict:
        """Charge les presets cinématographiques"""
        return {
            'explosion_large': {
                'category': 'effects',
                'type': 'explosion',
                'parameters': {
                    'intensity': 1.0,
                    'size': 'large',
                    'spatial': {'front_center': 0.8, 'lfe': 0.6}
                }
            },
            'forest_night': {
                'category': 'ambient',
                'type': 'forest',
                'parameters': {
                    'intensity': 0.3,
                    'time': 'night',
                    'spatial': {'front_center': 0.4, 'rear_left': 0.3, 'rear_right': 0.3}
                }
            },
            'spaceship_bridge': {
                'category': 'ambient',
                'type': 'space',
                'parameters': {
                    'ship_type': 'bridge',
                    'activity': 0.4,
                    'spatial': {'front_center': 0.6, 'front_left': 0.2, 'front_right': 0.2}
                }
            }
        }
    
    def save_cinematic_sound(self, audio: np.ndarray, filename: str, format: str = 'wav'):
        """Sauvegarde un son cinématographique"""
        try:
            # Conversion en 24-bit
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Normalisation
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val * 0.95
            
            # Sauvegarde
            if format.lower() == 'wav':
                sf.write(
                    filename,
                    audio.T,  # Transposer pour format (channels, samples)
                    self.sample_rate,
                    subtype='PCM_24'  # 24-bit
                )
            
            logger.info(f"💾 Son cinématographique sauvegardé: {filename}")
            logger.info(f"   Format: {self.sample_rate}Hz/{self.bit_depth}-bit, 5.1 surround")
            logger.info(f"   Shape: {audio.shape}")
            logger.info(f"   Duration: {audio.shape[1]/self.sample_rate:.2f}s")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde son cinématographique: {e}")
            raise
    
    def list_available_sounds(self) -> Dict:
        """Liste tous les sons disponibles"""
        available_sounds = {}
        
        for category, generators in self.sound_categories.items():
            available_sounds[category] = list(generators.keys())
        
        return available_sounds

# Test du designer sonore cinématographique
if __name__ == "__main__":
    print("🎬 Cinematic Sound Designer Test")
    print("=" * 50)
    
    # Initialisation
    designer = CinematicSoundDesigner()
    
    try:
        # Test génération ambiance forêt
        print("🌲 Test ambiance forêt...")
        forest_ambient = designer.generate_cinematic_sound(
            'ambient', 'forest', duration=10.0,
            parameters={'intensity': 0.5, 'time': 'day'}
        )
        designer.save_cinematic_sound(forest_ambient, "test_forest_ambient.wav")
        
        # Test génération explosion
        print("💥 Test explosion...")
        explosion = designer.generate_cinematic_sound(
            'effects', 'explosion', duration=3.0,
            parameters={'intensity': 0.8, 'size': 'large'}
        )
        designer.save_cinematic_sound(explosion, "test_explosion.wav")
        
        # Test génération pas
        print("👣 Test pas...")
        footsteps = designer.generate_cinematic_sound(
            'foley', 'footsteps', duration=5.0,
            parameters={'surface': 'concrete', 'character': 'male'}
        )
        designer.save_cinematic_sound(footsteps, "test_footsteps.wav")
        
        # Test preset
        print("🎬 Test preset...")
        preset = designer.presets['explosion_large']
        preset_sound = designer.generate_cinematic_sound(
            preset['category'], preset['type'], 
            duration=4.0, parameters=preset['parameters']
        )
        designer.save_cinematic_sound(preset_sound, "test_preset_explosion.wav")
        
        # Liste des sons disponibles
        available = designer.list_available_sounds()
        print(f"\n📊 Sons disponibles:")
        for category, sounds in available.items():
            print(f"   {category}: {len(sounds)} types")
        
        print(f"\n✅ Tests cinématographiques complétés")
        
    except Exception as e:
        print(f"❌ Erreur test designer cinématographique: {e}")
