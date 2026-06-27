#!/usr/bin/env python3
"""
HCS AudioCraft - Intégration Meta AudioCraft/MusicGen avec compression harmonique
Solution complète de génération musicale harmonique
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

# Import AudioCraft (si disponible)
try:
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
    AUDIOCRAFT_AVAILABLE = True
except ImportError:
    AUDIOCRAFT_AVAILABLE = False
    logging.warning("AudioCraft non disponible, utilisation du fallback")

from harmonic_engine import HarmonicGenerator

logger = logging.getLogger(__name__)

class HCSAudioCraft:
    """
    Intégration HCS + AudioCraft pour génération musicale avancée
    """
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.sample_rate = 32000  # Taux standard AudioCraft
        
        # Générateur harmonique HCS
        self.hcs_generator = HarmonicGenerator(
            sample_rate=self.sample_rate,
            duration=30.0
        )
        
        # Modèle AudioCraft
        self.musicgen_model = None
        self.load_audiocraft_model()
        
        logger.info(f"HCS AudioCraft initialisé: device={device}, audiocraft={AUDIOCRAFT_AVAILABLE}")
    
    def load_audiocraft_model(self):
        """Charge le modèle MusicGen"""
        if not AUDIOCRAFT_AVAILABLE:
            logger.warning("AudioCraft non disponible, utilisation du mode fallback")
            return
        
        try:
            # Charger le modèle pré-entraîné
            self.musicgen_model = MusicGen.get_pretrained('facebook/musicgen-small')
            self.musicgen_model.set_generation_params(
                use_sampling=True,
                top_k=250,
                top_p=0.0,
                temperature=1.0,
                duration=30,
                cfg_coef=3.0
            )
            self.musicgen_model.to(self.device)
            
            logger.info("✅ MusicGen model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Error loading MusicGen: {e}")
            self.musicgen_model = None
    
    def generate_with_audiocraft(self, description: str, duration: float = 30.0) -> torch.Tensor:
        """
        Génère de la musique avec AudioCraft/MusicGen
        """
        if self.musicgen_model is None:
            raise Exception("MusicGen model not available")
        
        try:
            # Génération avec AudioCraft
            with torch.no_grad():
                wav = self.musicgen_model.generate(
                    descriptions=[description],
                    progress=True,
                    duration=duration
                )
            
            # Prendre le premier élément (batch size = 1)
            audio = wav[0].cpu()
            
            logger.info(f"AudioCraft generation completed: {audio.shape}")
            return audio
            
        except Exception as e:
            logger.error(f"AudioCraft generation error: {e}")
            raise
    
    def generate_hcs_enhanced(self, description: str, style: str = "pop", 
                           key: str = "C", tempo: int = 120, 
                           duration: float = 30.0) -> np.ndarray:
        """
        Génération musicale complète avec HCS + AudioCraft
        """
        start_time = time.time()
        
        try:
            # Étape 1: Génération AudioCraft si disponible
            if AUDIOCRAFT_AVAILABLE and self.musicgen_model is not None:
                logger.info("🎵 Génération AudioCraft...")
                audio_craft = self.generate_with_audiocraft(description, duration)
                
                # Convertir en numpy
                audio_np = audio_craft.numpy()
                if len(audio_np.shape) > 1:
                    audio_np = np.mean(audio_np, axis=0)  # Mono
                
                # Rééchantillonner si nécessaire
                if len(audio_np) != self.sample_rate * duration:
                    audio_np = librosa.resample(
                        audio_np, 
                        orig_sr=len(audio_np) / duration, 
                        target_sr=self.sample_rate
                    )
                
            else:
                # Fallback: génération HCS pure
                logger.info("🎵 Génération HCS fallback...")
                audio_np = self.hcs_generator.generate_full_track(
                    style=style, key=key, tempo=tempo, duration=duration
                )
            
            # Étape 2: Amélioration harmonique HCS
            logger.info("🎵 Amélioration harmonique HCS...")
            enhanced_audio = self.apply_harmonic_enhancement(
                audio_np, style, key, tempo
            )
            
            # Étape 3: Post-traitement et mastering
            logger.info("🎵 Post-traitement et mastering...")
            final_audio = self.apply_mastering(enhanced_audio)
            
            generation_time = time.time() - start_time
            
            logger.info(f"✅ Génération HCS-AudioCraft complétée: {generation_time:.2f}s")
            
            return final_audio
            
        except Exception as e:
            logger.error(f"❌ Erreur génération HCS-AudioCraft: {e}")
            # Fallback complet
            return self.hcs_generator.generate_full_track(
                style=style, key=key, tempo=tempo, duration=duration
            )
    
    def apply_harmonic_enhancement(self, audio: np.ndarray, style: str, 
                                key: str, tempo: int) -> np.ndarray:
        """
        Applique l'amélioration harmonique HCS
        """
        try:
            # Analyse spectrale
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Détection des harmoniques principales
            harmonic_freqs = self.detect_harmonics(magnitude)
            
            # Amélioration selon le style
            if style == "jazz":
                # Ajout d'harmoniques complexes pour le jazz
                enhanced_magnitude = self.enhance_jazz_harmonics(magnitude, harmonic_freqs)
            elif style == "classical":
                # Harmoniques riches et équilibrées
                enhanced_magnitude = self.enhance_classical_harmonics(magnitude, harmonic_freqs)
            elif style == "electronic":
                # Harmoniques synthétiques
                enhanced_magnitude = self.enhance_electronic_harmonics(magnitude, harmonic_freqs)
            else:
                # Pop: harmoniques équilibrées
                enhanced_magnitude = self.enhance_pop_harmonics(magnitude, harmonic_freqs)
            
            # Reconstruction avec phase originale
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft, hop_length=512)
            
            # Normalisation
            enhanced_audio = enhanced_audio / np.max(np.abs(enhanced_audio)) * 0.8
            
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"Erreur enhancement harmonique: {e}")
            return audio
    
    def detect_harmonics(self, magnitude: np.ndarray) -> List[Tuple[float, float]]:
        """
        Détecte les fréquences harmoniques principales
        """
        # Moyenne sur le temps
        avg_magnitude = np.mean(magnitude, axis=1)
        
        # Trouver les pics
        peaks = []
        for i in range(1, len(avg_magnitude) - 1):
            if (avg_magnitude[i] > avg_magnitude[i-1] and 
                avg_magnitude[i] > avg_magnitude[i+1] and
                avg_magnitude[i] > np.max(avg_magnitude) * 0.1):
                
                freq = i * self.sample_rate / (2 * len(avg_magnitude))
                peaks.append((freq, avg_magnitude[i]))
        
        # Trier par magnitude
        peaks.sort(key=lambda x: x[1], reverse=True)
        
        return peaks[:10]  # Top 10 harmoniques
    
    def enhance_jazz_harmonics(self, magnitude: np.ndarray, 
                             harmonics: List[Tuple[float, float]]) -> np.ndarray:
        """Amélioration harmonique pour le jazz"""
        enhanced = magnitude.copy()
        
        # Ajouter des harmoniques complexes (7ème, 9ème, 13ème)
        for freq, mag in harmonics[:5]:  # Top 5 harmoniques
            # 7ème harmonique (septième)
            h7_idx = int(freq * 7 / (self.sample_rate / 2) * len(magnitude))
            if 0 < h7_idx < len(magnitude):
                enhanced[h7_idx] *= 1.3
            
            # 9ème harmonique (neuvième)
            h9_idx = int(freq * 9 / (self.sample_rate / 2) * len(magnitude))
            if 0 < h9_idx < len(magnitude):
                enhanced[h9_idx] *= 1.2
        
        return enhanced
    
    def enhance_classical_harmonics(self, magnitude: np.ndarray, 
                                harmonics: List[Tuple[float, float]]) -> np.ndarray:
        """Amélioration harmonique pour la musique classique"""
        enhanced = magnitude.copy()
        
        # Renforcer les harmoniques naturelles (2, 3, 4, 5)
        for freq, mag in harmonics[:8]:  # Top 8 harmoniques
            for harmonic in [2, 3, 4, 5]:
                h_idx = int(freq * harmonic / (self.sample_rate / 2) * len(magnitude))
                if 0 < h_idx < len(magnitude):
                    # Décroissance naturelle
                    boost = 1.0 + (0.5 / harmonic)
                    enhanced[h_idx] *= boost
        
        return enhanced
    
    def enhance_electronic_harmonics(self, magnitude: np.ndarray, 
                                  harmonics: List[Tuple[float, float]]) -> np.ndarray:
        """Amélioration harmonique pour la musique électronique"""
        enhanced = magnitude.copy()
        
        # Ajouter des harmoniques synthétiques (sub-harmoniques)
        for freq, mag in harmonics[:6]:  # Top 6 harmoniques
            # Sub-harmoniques
            for sub in [0.5, 0.25]:
                sub_idx = int(freq * sub / (self.sample_rate / 2) * len(magnitude))
                if 0 < sub_idx < len(magnitude):
                    enhanced[sub_idx] *= 1.4
            
            # Harmoniques aiguës
            for high in [8, 12, 16]:
                high_idx = int(freq * high / (self.sample_rate / 2) * len(magnitude))
                if 0 < high_idx < len(magnitude):
                    enhanced[high_idx] *= 1.2
        
        return enhanced
    
    def enhance_pop_harmonics(self, magnitude: np.ndarray, 
                            harmonics: List[Tuple[float, float]]) -> np.ndarray:
        """Amélioration harmonique pour la pop"""
        enhanced = magnitude.copy()
        
        # Harmoniques équilibrées pour la pop
        for freq, mag in harmonics[:5]:  # Top 5 harmoniques
            # 2ème et 3ème harmoniques (octave et quinte)
            for harmonic in [2, 3]:
                h_idx = int(freq * harmonic / (self.sample_rate / 2) * len(magnitude))
                if 0 < h_idx < len(magnitude):
                    enhanced[h_idx] *= 1.25
        
        return enhanced
    
    def apply_mastering(self, audio: np.ndarray) -> np.ndarray:
        """
        Applique le mastering audio professionnel
        """
        try:
            # 1. Normalisation LUFS (Loudness)
            audio_lufs = librosa.feature.rms(y=audio)
            target_lufs = -14.0  # Standard streaming
            if audio_lufs > 0:
                audio = audio * (10 ** (target_lufs / 20) / audio_lufs)
            
            # 2. Égalisation simple
            # Boost des basses et aigus pour la clarté
            eq_audio = self.apply_simple_eq(audio)
            
            # 3. Compression légère
            compressed_audio = self.apply_compression(eq_audio)
            
            # 4. Limiter pour éviter les clips
            limited_audio = np.tanh(compressed_audio * 0.95) / 0.95
            
            # 5. Normalisation finale
            final_audio = limited_audio / np.max(np.abs(limited_audio)) * 0.8
            
            return final_audio
            
        except Exception as e:
            logger.error(f"Erreur mastering: {e}")
            return audio
    
    def apply_simple_eq(self, audio: np.ndarray) -> np.ndarray:
        """Égalisation simple 3-bandes"""
        try:
            # Séparation par fréquences
            bass = librosa.effects.hpss(audio)[0]  # Basses
            mids = audio - bass  # Moyennes
            
            # Boost léger
            bass_enhanced = bass * 1.1
            mids_enhanced = mids * 1.05
            
            # Recombinaison
            eq_audio = bass_enhanced + mids_enhanced
            
            return eq_audio
            
        except Exception as e:
            logger.error(f"Erreur EQ: {e}")
            return audio
    
    def apply_compression(self, audio: np.ndarray, ratio: float = 4.0, 
                       threshold: float = 0.7) -> np.ndarray:
        """Compression audio simple"""
        try:
            # Compression par onde redressée
            compressed = np.where(
                np.abs(audio) > threshold,
                threshold + (np.abs(audio) - threshold) / ratio,
                audio
            )
            
            # Restaurer le signe
            compressed = np.sign(audio) * compressed
            
            return compressed
            
        except Exception as e:
            logger.error(f"Erreur compression: {e}")
            return audio
    
    def analyze_harmonic_content(self, audio: np.ndarray) -> Dict:
        """
        Analyse complète du contenu harmonique
        """
        try:
            # Analyse spectrale
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            
            # Détection de hauteur (pitch)
            pitches, magnitudes = librosa.piptrack(
                y=audio, sr=self.sample_rate, threshold=0.1
            )
            
            # Analyse chromatique
            chroma = librosa.feature.chroma_stft(y=audio, sr=self.sample_rate)
            
            # Tempo et rythme
            tempo, beats = librosa.beat.beat_track(y=audio, sr=self.sample_rate)
            
            # Harmonie
            harmonic, percussive = librosa.effects.hpss(audio)
            
            return {
                'spectral_centroid': librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate),
                'spectral_rolloff': librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate),
                'zero_crossing_rate': librosa.feature.zero_crossing_rate(audio),
                'chroma': chroma,
                'tempo': float(tempo),
                'beat_frames': beats,
                'harmonic_ratio': float(np.mean(harmonic**2) / (np.mean(harmonic**2) + np.mean(percussive**2))),
                'key_detection': {
                    'dominant_chroma': int(np.argmax(np.mean(chroma, axis=1))),
                    'chroma_profile': np.mean(chroma, axis=1).tolist()
                },
                'harmonic_peaks': self.detect_harmonics(magnitude)
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse harmonique: {e}")
            return {}
    
    def save_audio(self, audio: np.ndarray, filename: str, 
                  format: str = 'wav', sample_rate: Optional[int] = None):
        """
        Sauvegarde l'audio généré
        """
        sr = sample_rate or self.sample_rate
        
        try:
            sf.write(filename, audio, sr)
            logger.info(f"Audio sauvegardé: {filename} ({len(audio)} samples @ {sr}Hz)")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde audio: {e}")
            raise
    
    def generate_description_from_params(self, style: str, key: str, 
                                   tempo: int, duration: float) -> str:
        """
        Génère une description pour AudioCraft à partir des paramètres
        """
        style_descriptions = {
            'pop': f"catchy pop song in {key} major, {tempo} BPM, upbeat and energetic",
            'jazz': f"smooth jazz track in {key}, {tempo} BPM, with piano and saxophone",
            'classical': f"classical music in {key}, {tempo} BPM, orchestral and elegant",
            'electronic': f"electronic music in {key}, {tempo} BPM, synthesizers and drums"
        }
        
        return style_descriptions.get(style, f"{style} music in {key}, {tempo} BPM")

# Test du générateur
if __name__ == "__main__":
    print("🎵 HCS AudioCraft Test")
    print("=" * 40)
    
    # Initialisation
    generator = HCSAudioCraft()
    
    # Test de génération
    try:
        description = generator.generate_description_from_params(
            style="pop", key="C", tempo=120, duration=10.0
        )
        
        print(f"Description: {description}")
        
        # Génération
        audio = generator.generate_hcs_enhanced(
            description=description,
            style="pop",
            key="C", 
            tempo=120,
            duration=10.0
        )
        
        # Analyse
        analysis = generator.analyze_harmonic_content(audio)
        
        print(f"✅ Génération réussie")
        print(f"   Shape: {audio.shape}")
        print(f"   Duration: {len(audio)/generator.sample_rate:.2f}s")
        print(f"   Harmonic peaks: {len(analysis.get('harmonic_peaks', []))}")
        
        # Sauvegarde
        generator.save_audio(audio, "test_hcs_audiocraft.wav")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
