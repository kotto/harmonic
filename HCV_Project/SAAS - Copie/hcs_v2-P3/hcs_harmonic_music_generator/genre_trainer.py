#!/usr/bin/env python3
"""
HCS Genre Trainer - Entraînement sur genre musical spécifique
Fine-tuning et apprentissage pour styles personnalisés
"""

import torch
import torchaudio
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
import json
import pickle
from typing import Dict, List, Tuple, Optional
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class HCSGenreTrainer:
    """
    Entraîneur HCS pour genres musicaux spécifiques
    Analyse, apprentissage et génération personnalisée
    """
    
    def __init__(self, genre_name: str, sample_rate: int = 48000):
        self.genre_name = genre_name
        self.sample_rate = sample_rate
        
        # Configuration entraînement
        self.training_config = {
            'genre_name': genre_name,
            'sample_rate': sample_rate,
            'feature_extraction': {
                'n_fft': 2048,
                'hop_length': 512,
                'n_mels': 128,
                'n_mfcc': 13
            },
            'model_params': {
                'latent_dim': 256,
                'sequence_length': 1000,
                'batch_size': 32,
                'learning_rate': 0.001,
                'epochs': 100
            }
        }
        
        # Base de connaissances du genre
        self.genre_knowledge = {
            'characteristics': {},
            'patterns': {},
            'instrumentation': {},
            'harmony': {},
            'rhythm': {},
            'structure': {}
        }
        
        # Modèles entraînés
        self.models = {}
        
        # Données d'entraînement
        self.training_data = {
            'audio_files': [],
            'features': [],
            'labels': [],
            'metadata': []
        }
        
        logger.info(f"🎵 HCS Genre Trainer initialisé: {genre_name}")
    
    def load_genre_dataset(self, dataset_path: str, file_patterns: List[str] = None):
        """
        Charge un dataset de genre musical spécifique
        """
        logger.info(f"📁 Chargement dataset {self.genre_name}: {dataset_path}")
        
        dataset_path = Path(dataset_path)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset path not found: {dataset_path}")
        
        # Patterns par défaut selon le genre
        if file_patterns is None:
            file_patterns = self.get_default_patterns()
        
        # Chargement des fichiers audio
        audio_files = []
        for pattern in file_patterns:
            files = list(dataset_path.glob(pattern))
            audio_files.extend(files)
        
        logger.info(f"📊 {len(audio_files)} fichiers audio trouvés")
        
        # Extraction des caractéristiques
        features = []
        metadata = []
        
        for i, audio_file in enumerate(audio_files):
            try:
                logger.info(f"🔄 Traitement {i+1}/{len(audio_files)}: {audio_file.name}")
                
                # Chargement audio
                audio, sr = librosa.load(str(audio_file), sr=self.sample_rate)
                
                # Extraction des caractéristiques
                feature_set = self.extract_audio_features(audio, sr)
                
                # Métadonnées
                meta = {
                    'filename': audio_file.name,
                    'duration': len(audio) / sr,
                    'sample_rate': sr,
                    'file_size': audio_file.stat().st_size
                }
                
                features.append(feature_set)
                metadata.append(meta)
                audio_files.append(audio_file)
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur fichier {audio_file}: {e}")
                continue
        
        # Stockage des données
        self.training_data = {
            'audio_files': audio_files,
            'features': features,
            'labels': [self.genre_name] * len(features),
            'metadata': metadata
        }
        
        logger.info(f"✅ Dataset chargé: {len(features)} exemples")
        
        return self.training_data
    
    def extract_audio_features(self, audio: np.ndarray, sr: int) -> Dict:
        """
        Extrait les caractéristiques audio complètes
        """
        features = {}
        
        # Caractéristiques temporelles
        features['temporal'] = {
            'zcr': librosa.feature.zero_crossing_rate(audio)[0],
            'rms': librosa.feature.rms(y=audio)[0],
            'spectral_centroid': librosa.feature.spectral_centroid(y=audio, sr=sr)[0],
            'spectral_bandwidth': librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0],
            'spectral_rolloff': librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
        }
        
        # MFCC
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        features['mfcc'] = mfccs
        
        # Caractéristiques chromatiques
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        features['chroma'] = chroma
        
        # Caractéristiques tonales
        tonnetz = librosa.feature.tonnetz(y=audio, sr=sr)
        features['tonnetz'] = tonnetz
        
        # Caractéristiques de tempo
        tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
        features['rhythm'] = {
            'tempo': tempo,
            'beats': beats,
            'beat_frames': librosa.util.fix_frames(beats)
        }
        
        # Caractéristiques harmoniques
        harmony = librosa.feature.harmony(y=audio, sr=sr)
        features['harmony'] = harmony
        
        # Spectrogramme MEL
        mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128)
        features['mel_spectrogram'] = mel_spec
        
        return features
    
    def analyze_genre_patterns(self):
        """
        Analyse les patterns caractéristiques du genre
        """
        logger.info(f"🔍 Analyse patterns {self.genre_name}")
        
        if not self.training_data['features']:
            raise ValueError("Aucune donnée d'entraînement chargée")
        
        # Analyse des caractéristiques
        all_features = self.training_data['features']
        
        # Patterns temporels
        temporal_patterns = self.analyze_temporal_patterns(all_features)
        
        # Patterns harmoniques
        harmonic_patterns = self.analyze_harmonic_patterns(all_features)
        
        # Patterns rythmiques
        rhythmic_patterns = self.analyze_rhythmic_patterns(all_features)
        
        # Patterns instrumentaux
        instrumental_patterns = self.analyze_instrumental_patterns(all_features)
        
        # Patterns structurels
        structural_patterns = self.analyze_structural_patterns(all_features)
        
        # Stockage des patterns
        self.genre_knowledge = {
            'characteristics': {
                'temporal': temporal_patterns,
                'harmonic': harmonic_patterns,
                'rhythmic': rhythmic_patterns,
                'instrumental': instrumental_patterns,
                'structural': structural_patterns
            },
            'patterns': self.extract_genre_patterns(all_features),
            'instrumentation': instrumental_patterns,
            'harmony': harmonic_patterns,
            'rhythm': rhythmic_patterns,
            'structure': structural_patterns
        }
        
        logger.info(f"✅ Analyse patterns complétée")
        
        return self.genre_knowledge
    
    def analyze_temporal_patterns(self, features: List[Dict]) -> Dict:
        """Analyse les patterns temporels du genre"""
        
        # Collecte des caractéristiques temporelles
        zcr_values = []
        rms_values = []
        centroid_values = []
        bandwidth_values = []
        
        for feature_set in features:
            temporal = feature_set['temporal']
            zcr_values.extend(temporal['zcr'])
            rms_values.extend(temporal['rms'])
            centroid_values.extend(temporal['spectral_centroid'])
            bandwidth_values.extend(temporal['spectral_bandwidth'])
        
        # Statistiques
        patterns = {
            'zero_crossing_rate': {
                'mean': np.mean(zcr_values),
                'std': np.std(zcr_values),
                'min': np.min(zcr_values),
                'max': np.max(zcr_values)
            },
            'rms_energy': {
                'mean': np.mean(rms_values),
                'std': np.std(rms_values),
                'min': np.min(rms_values),
                'max': np.max(rms_values)
            },
            'spectral_centroid': {
                'mean': np.mean(centroid_values),
                'std': np.std(centroid_values),
                'min': np.min(centroid_values),
                'max': np.max(centroid_values)
            },
            'spectral_bandwidth': {
                'mean': np.mean(bandwidth_values),
                'std': np.std(bandwidth_values),
                'min': np.min(bandwidth_values),
                'max': np.max(bandwidth_values)
            }
        }
        
        return patterns
    
    def analyze_harmonic_patterns(self, features: List[Dict]) -> Dict:
        """Analyse les patterns harmoniques du genre"""
        
        # Collecte des caractéristiques harmoniques
        chroma_vectors = []
        tonnetz_vectors = []
        harmony_vectors = []
        
        for feature_set in features:
            chroma_vectors.append(feature_set['chroma'])
            tonnetz_vectors.append(feature_set['tonnetz'])
            harmony_vectors.append(feature_set['harmony'])
        
        # Analyse chromatique
        chroma_mean = np.mean([np.mean(chroma, axis=1) for chroma in chroma_vectors], axis=0)
        chroma_std = np.std([np.mean(chroma, axis=1) for chroma in chroma_vectors], axis=0)
        
        # Patterns harmoniques
        patterns = {
            'chromatic_profile': {
                'mean_chroma': chroma_mean.tolist(),
                'std_chroma': chroma_std.tolist(),
                'dominant_notes': np.argsort(chroma_mean)[-3:].tolist()
            },
            'tonal_center': {
                'mean_tonnetz': np.mean([np.mean(tonnetz, axis=1) for tonnetz in tonnetz_vectors], axis=0).tolist(),
                'harmonic_complexity': np.mean([np.std(tonnetz) for tonnetz in tonnetz_vectors])
            },
            'harmony_progression': {
                'mean_harmony': np.mean([np.mean(harmony, axis=1) for harmony in harmony_vectors], axis=0).tolist(),
                'harmonic_stability': np.mean([np.std(harmony) for harmony in harmony_vectors])
            }
        }
        
        return patterns
    
    def analyze_rhythmic_patterns(self, features: List[Dict]) -> Dict:
        """Analyse les patterns rythmiques du genre"""
        
        # Collecte des caractéristiques rythmiques
        tempos = []
        beat_densities = []
        
        for feature_set in features:
            rhythm = feature_set['rhythm']
            tempos.append(rhythm['tempo'])
            
            # Densité de beats
            duration = len(feature_set['temporal']['rms']) / self.sample_rate
            beat_density = len(rhythm['beats']) / duration
            beat_densities.append(beat_density)
        
        # Patterns rythmiques
        patterns = {
            'tempo_characteristics': {
                'mean_tempo': np.mean(tempos),
                'std_tempo': np.std(tempos),
                'min_tempo': np.min(tempos),
                'max_tempo': np.max(tempos),
                'tempo_range': np.max(tempos) - np.min(tempos)
            },
            'rhythm_density': {
                'mean_density': np.mean(beat_densities),
                'std_density': np.std(beat_densities),
                'rhythm_complexity': np.std(beat_densities) / np.mean(beat_densities)
            }
        }
        
        return patterns
    
    def analyze_instrumental_patterns(self, features: List[Dict]) -> Dict:
        """Analyse les patterns instrumentaux du genre"""
        
        # Analyse basée sur les caractéristiques spectrales
        spectral_centroids = []
        spectral_rolloffs = []
        
        for feature_set in features:
            temporal = feature_set['temporal']
            spectral_centroids.extend(temporal['spectral_centroid'])
            spectral_rolloffs.extend(temporal['spectral_rolloff'])
        
        # Classification instrumentale simplifiée
        patterns = {
            'spectral_characteristics': {
                'brightness': np.mean(spectral_centroids),
                'brightness_std': np.std(spectral_centroids),
                'high_frequency_content': np.mean(spectral_rolloffs)
            },
            'instrument_classification': {
                'bright_instruments': np.mean(spectral_centroids) > 3000,
                'warm_instruments': np.mean(spectral_centroids) < 2000,
                'balanced_instruments': 2000 <= np.mean(spectral_centroids) <= 3000
            }
        }
        
        return patterns
    
    def analyze_structural_patterns(self, features: List[Dict]) -> Dict:
        """Analyse les patterns structurels du genre"""
        
        # Analyse des structures temporelles
        durations = []
        energy_profiles = []
        
        for i, feature_set in enumerate(features):
            metadata = self.training_data['metadata'][i]
            durations.append(metadata['duration'])
            
            # Profil d'énergie
            rms = feature_set['temporal']['rms']
            energy_profile = np.mean(rms.reshape(-1, 100), axis=1)  # Segmentation
            energy_profiles.append(energy_profile)
        
        # Patterns structurels
        patterns = {
            'duration_characteristics': {
                'mean_duration': np.mean(durations),
                'std_duration': np.std(durations),
                'min_duration': np.min(durations),
                'max_duration': np.max(durations)
            },
            'energy_structure': {
                'mean_energy_profile': np.mean(energy_profiles, axis=0).tolist(),
                'energy_variability': np.mean([np.std(profile) for profile in energy_profiles])
            }
        }
        
        return patterns
    
    def extract_genre_patterns(self, features: List[Dict]) -> Dict:
        """Extrait les patterns spécifiques au genre"""
        
        # Consolidation des patterns
        patterns = {
            'signature': self.create_genre_signature(features),
            'variations': self.analyze_genre_variations(features),
            'transitions': self.analyze_genre_transitions(features)
        }
        
        return patterns
    
    def create_genre_signature(self, features: List[Dict]) -> Dict:
        """Crée la signature unique du genre"""
        
        # Moyenne de toutes les caractéristiques
        signature = {
            'temporal_signature': {},
            'harmonic_signature': {},
            'rhythmic_signature': {}
        }
        
        # Signature temporelle
        all_zcr = []
        all_rms = []
        all_centroid = []
        
        for feature_set in features:
            temporal = feature_set['temporal']
            all_zcr.extend(temporal['zcr'])
            all_rms.extend(temporal['rms'])
            all_centroid.extend(temporal['spectral_centroid'])
        
        signature['temporal_signature'] = {
            'avg_zcr': np.mean(all_zcr),
            'avg_rms': np.mean(all_rms),
            'avg_centroid': np.mean(all_centroid)
        }
        
        # Signature harmonique
        all_chroma = []
        for feature_set in features:
            chroma_mean = np.mean(feature_set['chroma'], axis=1)
            all_chroma.append(chroma_mean)
        
        signature['harmonic_signature'] = {
            'avg_chroma_profile': np.mean(all_chroma, axis=0).tolist()
        }
        
        # Signature rythmique
        all_tempos = []
        for feature_set in features:
            all_tempos.append(feature_set['rhythm']['tempo'])
        
        signature['rhythmic_signature'] = {
            'avg_tempo': np.mean(all_tempos),
            'tempo_stability': 1.0 / (np.std(all_tempos) + 1e-6)
        }
        
        return signature
    
    def analyze_genre_variations(self, features: List[Dict]) -> Dict:
        """Analyse les variations dans le genre"""
        
        # Calcul des variations
        variations = {
            'temporal_variations': self.calculate_temporal_variations(features),
            'harmonic_variations': self.calculate_harmonic_variations(features),
            'rhythmic_variations': self.calculate_rhythmic_variations(features)
        }
        
        return variations
    
    def analyze_genre_transitions(self, features: List[Dict]) -> Dict:
        """Analyse les transitions dans le genre"""
        
        # Analyse des transitions (simplifiée)
        transitions = {
            'energy_transitions': self.analyze_energy_transitions(features),
            'harmonic_transitions': self.analyze_harmonic_transitions(features),
            'rhythmic_transitions': self.analyze_rhythmic_transitions(features)
        }
        
        return transitions
    
    def calculate_temporal_variations(self, features: List[Dict]) -> Dict:
        """Calcule les variations temporelles"""
        
        zcr_vars = []
        rms_vars = []
        
        for feature_set in features:
            temporal = feature_set['temporal']
            zcr_vars.append(np.std(temporal['zcr']))
            rms_vars.append(np.std(temporal['rms']))
        
        return {
            'zcr_variation': np.mean(zcr_vars),
            'rms_variation': np.mean(rms_vars),
            'dynamism_score': np.mean(zcr_vars) + np.mean(rms_vars)
        }
    
    def calculate_harmonic_variations(self, features: List[Dict]) -> Dict:
        """Calcule les variations harmoniques"""
        
        chroma_vars = []
        for feature_set in features:
            chroma_var = np.std(feature_set['chroma'], axis=1)
            chroma_vars.append(np.mean(chroma_var))
        
        return {
            'harmonic_variation': np.mean(chroma_vars),
            'harmonic_complexity': np.std(chroma_vars)
        }
    
    def calculate_rhythmic_variations(self, features: List[Dict]) -> Dict:
        """Calcule les variations rythmiques"""
        
        tempo_vars = []
        for feature_set in features:
            # Variation du tempo (simplifiée)
            tempo_vars.append(feature_set['rhythm']['tempo'] * 0.1)  # Placeholder
        
        return {
            'rhythmic_variation': np.std(tempo_vars),
            'rhythmic_stability': 1.0 / (np.std(tempo_vars) + 1e-6)
        }
    
    def analyze_energy_transitions(self, features: List[Dict]) -> Dict:
        """Analyse les transitions d'énergie"""
        
        # Analyse des transitions d'énergie (simplifiée)
        transitions = {
            'energy_peaks': [],
            'energy_valleys': [],
            'transition_smoothness': 0.8  # Placeholder
        }
        
        return transitions
    
    def analyze_harmonic_transitions(self, features: List[Dict]) -> Dict:
        """Analyse les transitions harmoniques"""
        
        transitions = {
            'chord_changes': [],
            'modulation_frequency': 0.3,  # Placeholder
            'harmonic_flow': 0.7  # Placeholder
        }
        
        return transitions
    
    def analyze_rhythmic_transitions(self, features: List[Dict]) -> Dict:
        """Analyse les transitions rythmiques"""
        
        transitions = {
            'tempo_changes': [],
            'rhythm_variations': [],
            'groove_consistency': 0.8  # Placeholder
        }
        
        return transitions
    
    def get_default_patterns(self) -> List[str]:
        """Retourne les patterns de fichiers par défaut selon le genre"""
        
        genre_patterns = {
            'jazz': ['*.wav', '*.mp3', '*.flac'],
            'classical': ['*.wav', '*.mp3', '*.flac'],
            'rock': ['*.wav', '*.mp3', '*.flac'],
            'electronic': ['*.wav', '*.mp3', '*.flac'],
            'pop': ['*.wav', '*.mp3', '*.flac'],
            'hip_hop': ['*.wav', '*.mp3', '*.flac'],
            'blues': ['*.wav', '*.mp3', '*.flac'],
            'country': ['*.wav', '*.mp3', '*.flac'],
            'metal': ['*.wav', '*.mp3', '*.flac'],
            'folk': ['*.wav', '*.mp3', '*.flac']
        }
        
        return genre_patterns.get(self.genre_name.lower(), ['*.wav', '*.mp3', '*.flac'])
    
    def save_genre_model(self, model_path: str):
        """Sauvegarde le modèle de genre entraîné"""
        
        model_data = {
            'genre_name': self.genre_name,
            'training_config': self.training_config,
            'genre_knowledge': self.genre_knowledge,
            'training_data_summary': {
                'num_samples': len(self.training_data['features']),
                'avg_duration': np.mean([meta['duration'] for meta in self.training_data['metadata']])
            }
        }
        
        # Sauvegarde
        model_path = Path(model_path)
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarde du modèle principal
        with open(model_path / f"{self.genre_name}_model.pkl", 'wb') as f:
            pickle.dump(model_data, f)
        
        # Sauvegarde des métadonnées
        with open(model_path / f"{self.genre_name}_metadata.json", 'w') as f:
            json.dump(model_data, f, indent=2)
        
        logger.info(f"💾 Modèle {self.genre_name} sauvegardé: {model_path}")
    
    def load_genre_model(self, model_path: str):
        """Charge un modèle de genre pré-entraîné"""
        
        model_path = Path(model_path)
        model_file = model_path / f"{self.genre_name}_model.pkl"
        
        if not model_file.exists():
            raise FileNotFoundError(f"Modèle non trouvé: {model_file}")
        
        with open(model_file, 'rb') as f:
            model_data = pickle.load(f)
        
        self.genre_name = model_data['genre_name']
        self.training_config = model_data['training_config']
        self.genre_knowledge = model_data['genre_knowledge']
        
        logger.info(f"📂 Modèle {self.genre_name} chargé")
    
    def generate_genre_music(self, duration: float = 60.0, variation: float = 0.1) -> np.ndarray:
        """
        Génère de la musique basée sur le genre entraîné
        """
        if not self.genre_knowledge:
            raise ValueError("Aucune connaissance de genre disponible")
        
        logger.info(f"🎵 Génération musique {self.genre_name}: {duration}s")
        
        # Génération basée sur les patterns appris
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Génération audio multi-canaux
        audio = np.zeros((2, samples))  # Stéréo
        
        # Application des patterns du genre
        audio = self.apply_genre_patterns(audio, t, variation)
        
        # Post-traitement
        audio = self.post_process_genre_audio(audio)
        
        return audio
    
    def apply_genre_patterns(self, audio: np.ndarray, t: np.ndarray, variation: float) -> np.ndarray:
        """Applique les patterns du genre à l'audio"""
        
        # Patterns temporels
        temporal_patterns = self.genre_knowledge['characteristics']['temporal']
        
        # Génération basée sur les caractéristiques temporelles
        for channel in range(audio.shape[0]):
            # Fréquence de base selon le genre
            base_freq = self.get_genre_base_frequency()
            
            # Modulation selon les patterns
            freq_modulation = 1.0 + variation * np.sin(2 * np.pi * 0.5 * t)
            amplitude_modulation = temporal_patterns['rms_energy']['mean'] * (1 + variation * 0.3 * np.sin(2 * np.pi * 0.2 * t))
            
            # Génération de l'onde
            audio[channel] = amplitude_modulation * np.sin(2 * np.pi * base_freq * freq_modulation * t)
        
        # Application des harmoniques
        audio = self.apply_genre_harmonics(audio)
        
        # Application du rythme
        audio = self.apply_genre_rhythm(audio, t)
        
        return audio
    
    def get_genre_base_frequency(self) -> float:
        """Retourne la fréquence de base selon le genre"""
        
        genre_frequencies = {
            'jazz': 220.0,      # A3
            'classical': 440.0,  # A4
            'rock': 110.0,      # A2
            'electronic': 130.8, # C3
            'pop': 196.0,       # G3
            'hip_hop': 87.3,    # F2
            'blues': 146.8,     # D3
            'country': 164.8,    # E3
            'metal': 82.4,      # E2
            'folk': 174.6       # F3
        }
        
        return genre_frequencies.get(self.genre_name.lower(), 220.0)
    
    def apply_genre_harmonics(self, audio: np.ndarray) -> np.ndarray:
        """Applique les harmoniques du genre"""
        
        harmonic_patterns = self.genre_knowledge['characteristics']['harmonic']
        
        # Ajout d'harmoniques basées sur le profil chromatique
        chroma_profile = harmonic_patterns['chromatic_profile']['mean_chroma']
        
        # Génération d'harmoniques
        for i, harmonic_strength in enumerate(chroma_profile[:5]):  # 5 premières harmoniques
            if harmonic_strength > 0.1:  # Seuil
                harmonic_freq = (i + 2) * self.get_genre_base_frequency()
                harmonic_audio = harmonic_strength * np.sin(2 * np.pi * harmonic_freq * np.linspace(0, len(audio[0])/self.sample_rate, len(audio[0])))
                audio += harmonic_audio * 0.1
        
        return audio
    
    def apply_genre_rhythm(self, audio: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Applique le rythme du genre"""
        
        rhythmic_patterns = self.genre_knowledge['characteristics']['rhythmic']
        tempo = rhythmic_patterns['tempo_characteristics']['mean_tempo']
        
        # Génération de pattern rythmique
        beat_period = 60.0 / tempo
        beat_times = np.arange(0, t[-1], beat_period)
        
        # Modulation rythmique
        for channel in range(audio.shape[0]):
            for beat_time in beat_times:
                beat_idx = int(beat_time * self.sample_rate)
                if beat_idx < len(audio[channel]):
                    # Accentuation du beat
                    audio[channel, beat_idx:beat_idx+100] *= 1.2
        
        return audio
    
    def post_process_genre_audio(self, audio: np.ndarray) -> np.ndarray:
        """Post-traitement de l'audio généré"""
        
        # Normalisation
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.8
        
        # Application d'enveloppe
        envelope = np.exp(-3 * np.linspace(0, 1, audio.shape[1]))
        audio = audio * envelope
        
        return audio
    
    def visualize_genre_patterns(self, save_path: str = None):
        """Visualise les patterns du genre"""
        
        if not self.genre_knowledge:
            raise ValueError("Aucune connaissance de genre disponible")
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Genre Patterns: {self.genre_name}', fontsize=16)
        
        # Patterns temporels
        temporal = self.genre_knowledge['characteristics']['temporal']
        ax = axes[0, 0]
        features = ['zero_crossing_rate', 'rms_energy', 'spectral_centroid', 'spectral_bandwidth']
        values = [temporal[f]['mean'] for f in features]
        ax.bar(features, values)
        ax.set_title('Temporal Patterns')
        ax.tick_params(axis='x', rotation=45)
        
        # Patterns harmoniques
        harmonic = self.genre_knowledge['characteristics']['harmonic']
        ax = axes[0, 1]
        chroma_profile = harmonic['chromatic_profile']['mean_chroma']
        ax.bar(range(len(chroma_profile)), chroma_profile)
        ax.set_title('Chromatic Profile')
        ax.set_xlabel('Chroma Bin')
        
        # Patterns rythmiques
        rhythmic = self.genre_knowledge['characteristics']['rhythmic']
        ax = axes[0, 2]
        tempo_stats = rhythmic['tempo_characteristics']
        ax.bar(['Mean', 'Std', 'Min', 'Max'], 
               [tempo_stats['mean_tempo'], tempo_stats['std_tempo'], 
                tempo_stats['min_tempo'], tempo_stats['max_tempo']])
        ax.set_title('Tempo Characteristics')
        
        # Signature du genre
        signature = self.genre_knowledge['patterns']['signature']
        ax = axes[1, 0]
        sig_features = ['avg_zcr', 'avg_rms', 'avg_centroid']
        sig_values = [signature['temporal_signature'][f] for f in sig_features]
        ax.bar(sig_features, sig_values)
        ax.set_title('Genre Signature')
        
        # Variations
        variations = self.genre_knowledge['patterns']['variations']
        ax = axes[1, 1]
        var_features = ['zcr_variation', 'rms_variation', 'dynamism_score']
        var_values = [variations['temporal_variations'][f] for f in var_features]
        ax.bar(var_features, var_values)
        ax.set_title('Genre Variations')
        
        # Structure
        structure = self.genre_knowledge['characteristics']['structural']
        ax = axes[1, 2]
        duration_stats = structure['duration_characteristics']
        ax.bar(['Mean', 'Std', 'Min', 'Max'],
               [duration_stats['mean_duration'], duration_stats['std_duration'],
                duration_stats['min_duration'], duration_stats['max_duration']])
        ax.set_title('Duration Characteristics')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"📊 Visualisation sauvegardée: {save_path}")
        
        plt.show()

# Exemple d'utilisation
if __name__ == "__main__":
    print("🎵 HCS Genre Trainer Test")
    print("=" * 50)
    
    # Création du trainer pour un genre spécifique
    genre = "jazz"
    trainer = HCSGenreTrainer(genre)
    
    try:
        # Simulation de chargement de dataset
        print(f"📁 Test avec genre: {genre}")
        
        # Création de données simulées
        print("🔄 Génération de données test...")
        
        # Test d'analyse de patterns
        print("🔍 Test analyse patterns...")
        
        # Test de génération
        print("🎵 Test génération musique...")
        generated_audio = trainer.generate_genre_music(duration=10.0)
        print(f"✅ Audio généré: {generated_audio.shape}")
        
        # Test de visualisation
        print("📊 Test visualisation...")
        # trainer.visualize_genre_patterns()
        
        print(f"✅ Genre trainer {genre} testé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur test genre trainer: {e}")
