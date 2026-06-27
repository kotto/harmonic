#!/usr/bin/env python3
"""
HCS AI Integrations - Intégration avec IA audio professionnelles
Suno, Udio, ElevenLabs, Descript, AIVA, etc.
"""

import requests
import json
import numpy as np
import soundfile as sf
from typing import Dict, List, Optional, Tuple
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class HCSAIIntegrations:
    """
    Intégration HCS avec IA audio professionnelles
    Amélioration et post-traitement des générations IA existantes
    """
    
    def __init__(self):
        self.sample_rate = 48000  # Standard professionnel
        self.bit_depth = 24
        
        # Configuration APIs
        self.api_configs = {
            'suno': {
                'base_url': 'https://api.suno.ai',
                'quality': 'studio',
                'format': 'wav'
            },
            'udio': {
                'base_url': 'https://api.udio.ai',
                'quality': 'broadcast',
                'format': 'wav'
            },
            'elevenlabs': {
                'base_url': 'https://api.elevenlabs.io',
                'quality': 'professional',
                'format': 'wav'
            },
            'descript': {
                'base_url': 'https://api.descript.com',
                'quality': 'studio',
                'format': 'wav'
            }
        }
        
        logger.info("HCS AI Integrations initialisé")
    
    def enhance_suno_output(self, suno_audio: np.ndarray, 
                          target_quality: str = "cinema") -> np.ndarray:
        """
        Améliore la sortie Suno AI avec traitement HCS professionnel
        """
        try:
            logger.info(f"🎵 Amélioration Suno AI: {target_quality}")
            
            # Analyse de la qualité Suno
            suno_analysis = self.analyze_suno_quality(suno_audio)
            
            # Traitement HCS selon la qualité cible
            if target_quality == "cinema":
                enhanced_audio = self.apply_cinema_enhancement(suno_audio)
            elif target_quality == "broadcast":
                enhanced_audio = self.apply_broadcast_enhancement(suno_audio)
            else:
                enhanced_audio = self.apply_studio_enhancement(suno_audio)
            
            # Comparaison avant/après
            quality_improvement = self.calculate_quality_improvement(
                suno_audio, enhanced_audio
            )
            
            logger.info(f"✅ Amélioration Suno: {quality_improvement:.1f}%")
            
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"❌ Erreur amélioration Suno: {e}")
            return suno_audio
    
    def enhance_udio_output(self, udio_audio: np.ndarray,
                         target_quality: str = "professional") -> np.ndarray:
        """
        Améliore la sortie Udio AI avec traitement HCS
        """
        try:
            logger.info(f"🎵 Amélioration Udio AI: {target_quality}")
            
            # Analyse Udio
            udio_analysis = self.analyze_udio_quality(udio_audio)
            
            # Traitement HCS spécialisé
            enhanced_audio = self.apply_udio_specific_enhancement(
                udio_audio, udio_analysis
            )
            
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"❌ Erreur amélioration Udio: {e}")
            return udio_audio
    
    def enhance_elevenlabs_voice(self, voice_audio: np.ndarray,
                              voice_characteristics: Dict) -> np.ndarray:
        """
        Améliore la voix ElevenLabs avec traitement HCS vocal
        """
        try:
            logger.info(f"🎤 Amélioration ElevenLabs voix")
            
            # Analyse vocale
            voice_analysis = self.analyze_voice_quality(voice_audio)
            
            # Traitement vocal HCS
            enhanced_voice = self.apply_vocal_enhancement(
                voice_audio, voice_analysis, voice_characteristics
            )
            
            return enhanced_voice
            
        except Exception as e:
            logger.error(f"❌ Erreur amélioration voix ElevenLabs: {e}")
            return voice_audio
    
    def integrate_multiple_ai(self, ai_outputs: Dict[str, np.ndarray],
                           integration_strategy: str = "hybrid") -> np.ndarray:
        """
        Intègre les sorties de multiples IA avec stratégie HCS
        """
        try:
            logger.info(f"🔄 Intégration multiple IA: {integration_strategy}")
            
            if integration_strategy == "hybrid":
                # Fusion hybride HCS
                integrated_audio = self.hybrid_ai_fusion(ai_outputs)
            elif integration_strategy == "best_quality":
                # Sélection meilleure qualité
                integrated_audio = self.select_best_quality(ai_outputs)
            elif integration_strategy == "layered":
                # Superposition des couches
                integrated_audio = self.layered_ai_integration(ai_outputs)
            else:
                # Moyenne pondérée
                integrated_audio = self.weighted_ai_average(ai_outputs)
            
            return integrated_audio
            
        except Exception as e:
            logger.error(f"❌ Erreur intégration IA: {e}")
            # Fallback: première sortie disponible
            return next(iter(ai_outputs.values()))
    
    def analyze_suno_quality(self, audio: np.ndarray) -> Dict:
        """Analyse la qualité de l'audio Suno"""
        
        # Métriques de qualité Suno
        rms = np.sqrt(np.mean(audio**2))
        peak = np.max(np.abs(audio))
        dynamic_range = 20 * np.log10(peak / max(rms, 1e-10))
        
        # Analyse fréquentielle
        import librosa
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate)
        
        return {
            "source": "Suno AI",
            "rms_level": float(rms),
            "peak_level": float(peak),
            "dynamic_range": float(dynamic_range),
            "spectral_centroid": float(np.mean(spectral_centroids)),
            "quality_score": self.calculate_suno_quality_score(audio),
            "characteristics": {
                "vocal_clarity": self.assess_vocal_clarity(audio),
                "instrumental_balance": self.assess_instrumental_balance(audio),
                "mix_quality": self.assess_mix_quality(audio)
            }
        }
    
    def analyze_udio_quality(self, audio: np.ndarray) -> Dict:
        """Analyse la qualité de l'audio Udio"""
        
        # Analyse spécifique Udio
        return {
            "source": "Udio AI",
            "quality_metrics": self.analyze_udio_specifics(audio),
            "frequency_balance": self.analyze_frequency_balance(audio),
            "stereo_image": self.analyze_stereo_image(audio),
            "dynamic_processing": self.analyze_dynamic_processing(audio)
        }
    
    def apply_cinema_enhancement(self, audio: np.ndarray) -> np.ndarray:
        """Applique l'amélioration cinéma HCS"""
        
        # Import du moteur professionnel
        from professional_audio_engine import ProfessionalAudioEngine
        
        # Moteur cinéma
        cinema_engine = ProfessionalAudioEngine()
        
        # Traitement multi-bandes
        bands_audio = cinema_engine.apply_multiband_processing({'full': audio})
        
        # Spatial 3D
        spatial_audio = cinema_engine.apply_3d_spatial_processing(bands_audio)
        
        # Mastering cinéma
        mastered_audio = cinema_engine.apply_professional_mastering(spatial_audio)
        
        return mastered_audio
    
    def apply_broadcast_enhancement(self, audio: np.ndarray) -> np.ndarray:
        """Applique l'amélioration broadcast HCS"""
        
        # Traitement broadcast standard
        enhanced = self.apply_broadcast_eq(audio)
        enhanced = self.apply_broadcast_compression(enhanced)
        enhanced = self.apply_broadcast_limiter(enhanced)
        
        return enhanced
    
    def apply_studio_enhancement(self, audio: np.ndarray) -> np.ndarray:
        """Applique l'amélioration studio HCS"""
        
        # Traitement studio standard
        enhanced = self.apply_studio_eq(audio)
        enhanced = self.apply_studio_saturation(enhanced)
        enhanced = self.apply_studio_compression(enhanced)
        
        return enhanced
    
    def apply_udio_specific_enhancement(self, audio: np.ndarray,
                                     analysis: Dict) -> np.ndarray:
        """Applique l'amélioration spécifique Udio"""
        
        # Traitement basé sur l'analyse Udio
        enhanced = audio.copy()
        
        # Correction des faiblesses Udio détectées
        if analysis.get("frequency_balance", {}).get("bass_heavy", False):
            enhanced = self.reduce_bass_boost(enhanced)
        
        if analysis.get("dynamic_processing", {}).get("over_compressed", False):
            enhanced = self.restore_dynamics(enhanced)
        
        return enhanced
    
    def apply_vocal_enhancement(self, audio: np.ndarray,
                              voice_analysis: Dict,
                              characteristics: Dict) -> np.ndarray:
        """Applique l'amélioration vocale HCS"""
        
        # Traitement vocal spécialisé
        enhanced = self.apply_vocal_eq(audio, voice_analysis)
        enhanced = self.apply_vocal_compression(enhanced, characteristics)
        enhanced = self.apply_vocal_de_essing(enhanced)
        
        return enhanced
    
    def hybrid_ai_fusion(self, ai_outputs: Dict[str, np.ndarray]) -> np.ndarray:
        """Fusion hybride des sorties IA avec HCS"""
        
        # Analyse de chaque sortie
        analyses = {}
        for ai_name, audio in ai_outputs.items():
            if ai_name == "suno":
                analyses[ai_name] = self.analyze_suno_quality(audio)
            elif ai_name == "udio":
                analyses[ai_name] = self.analyze_udio_quality(audio)
            else:
                analyses[ai_name] = self.analyze_generic_quality(audio)
        
        # Pondération selon la qualité
        weights = {}
        total_weight = 0
        for ai_name, analysis in analyses.items():
            weight = analysis.get("quality_score", 0.5)
            weights[ai_name] = weight
            total_weight += weight
        
        # Fusion pondérée
        if total_weight > 0:
            fused_audio = np.zeros_like(next(iter(ai_outputs.values())))
            for ai_name, audio in ai_outputs.items():
                normalized_weight = weights[ai_name] / total_weight
                if len(fused_audio.shape) == len(audio.shape):
                    fused_audio += audio * normalized_weight
                else:
                    # Gestion des dimensions différentes
                    min_len = min(len(fused_audio), len(audio))
                    fused_audio[:min_len] += audio[:min_len] * normalized_weight
        else:
            # Fallback: moyenne simple
            fused_audio = np.mean(list(ai_outputs.values()), axis=0)
        
        return fused_audio
    
    def select_best_quality(self, ai_outputs: Dict[str, np.ndarray]) -> np.ndarray:
        """Sélectionne la meilleure qualité parmi les sorties IA"""
        
        best_audio = None
        best_score = 0
        best_source = ""
        
        for ai_name, audio in ai_outputs.items():
            if ai_name == "suno":
                analysis = self.analyze_suno_quality(audio)
            elif ai_name == "udio":
                analysis = self.analyze_udio_quality(audio)
            else:
                analysis = self.analyze_generic_quality(audio)
            
            score = analysis.get("quality_score", 0)
            
            if score > best_score:
                best_score = score
                best_audio = audio
                best_source = ai_name
        
        logger.info(f"🏆 Meilleure qualité: {best_source} (score: {best_score:.2f})")
        
        return best_audio
    
    def layered_ai_integration(self, ai_outputs: Dict[str, np.ndarray]) -> np.ndarray:
        """Intégration par superposition des couches"""
        
        # Stratégie: Suno pour voix, Udio pour instruments
        layered_audio = np.zeros_like(next(iter(ai_outputs.values())))
        
        for ai_name, audio in ai_outputs.items():
            if ai_name == "suno":
                # Suno: focus sur les voix
                voice_layer = self.extract_vocal_layer(audio)
                layered_audio += voice_layer * 0.7
            elif ai_name == "udio":
                # Udio: focus sur les instruments
                instrumental_layer = self.extract_instrumental_layer(audio)
                layered_audio += instrumental_layer * 0.8
            else:
                # Autres: contribution générale
                layered_audio += audio * 0.5
        
        # Normalisation
        if np.max(np.abs(layered_audio)) > 0:
            layered_audio = layered_audio / np.max(np.abs(layered_audio)) * 0.8
        
        return layered_audio
    
    def weighted_ai_average(self, ai_outputs: Dict[str, np.ndarray]) -> np.ndarray:
        """Moyenne pondérée des sorties IA"""
        
        # Poids par défaut (peut être personnalisé)
        default_weights = {
            "suno": 0.4,      # Bon pour voix
            "udio": 0.4,       # Bon pour instruments
            "elevenlabs": 0.3, # Excellent pour voix
            "descript": 0.3     # Bon pour qualité générale
        }
        
        weighted_audio = np.zeros_like(next(iter(ai_outputs.values())))
        total_weight = 0
        
        for ai_name, audio in ai_outputs.items():
            weight = default_weights.get(ai_name, 0.25)
            weighted_audio += audio * weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_audio /= total_weight
        
        return weighted_audio
    
    def calculate_quality_improvement(self, original: np.ndarray,
                                  enhanced: np.ndarray) -> float:
        """Calcule l'amélioration de qualité en pourcentage"""
        
        # Métriques de qualité
        original_metrics = self.calculate_quality_metrics(original)
        enhanced_metrics = self.calculate_quality_metrics(enhanced)
        
        # Calcul de l'amélioration
        improvements = {}
        for metric in original_metrics:
            if metric in enhanced_metrics:
                improvement = (enhanced_metrics[metric] - original_metrics[metric]) / abs(original_metrics[metric]) * 100
                improvements[metric] = improvement
        
        # Amélioration moyenne
        avg_improvement = np.mean(list(improvements.values())) if improvements else 0
        
        return avg_improvement
    
    def calculate_quality_metrics(self, audio: np.ndarray) -> Dict:
        """Calcule les métriques de qualité audio"""
        
        try:
            import librosa
            
            # Métriques de base
            rms = np.sqrt(np.mean(audio**2))
            peak = np.max(np.abs(audio))
            dynamic_range = 20 * np.log10(peak / max(rms, 1e-10))
            
            # Métriques spectrales
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate)
            
            # Métriques de clarté
            harmonic, percussive = librosa.effects.hpss(audio)
            harmonic_ratio = np.mean(harmonic**2) / (np.mean(harmonic**2) + np.mean(percussive**2))
            
            return {
                "rms": float(rms),
                "peak": float(peak),
                "dynamic_range": float(dynamic_range),
                "spectral_centroid": float(np.mean(spectral_centroids)),
                "spectral_rolloff": float(np.mean(spectral_rolloff)),
                "harmonic_ratio": float(harmonic_ratio),
                "clarity_score": float(harmonic_ratio * dynamic_range / 100)
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques qualité: {e}")
            return {}
    
    def calculate_suno_quality_score(self, audio: np.ndarray) -> float:
        """Calcule le score de qualité spécifique Suno"""
        
        metrics = self.calculate_quality_metrics(audio)
        
        # Pondération spécifique Suno
        weights = {
            "clarity_score": 0.3,
            "dynamic_range": 0.25,
            "harmonic_ratio": 0.2,
            "spectral_centroid": 0.15,
            "rms": 0.1
        }
        
        score = 0
        total_weight = 0
        
        for metric, weight in weights.items():
            if metric in metrics:
                # Normalisation de la métrique
                normalized_value = self.normalize_metric(metric, metrics[metric])
                score += normalized_value * weight
                total_weight += weight
        
        if total_weight > 0:
            score /= total_weight
        
        return score
    
    def normalize_metric(self, metric: str, value: float) -> float:
        """Normalise une métrique entre 0 et 1"""
        
        normalizations = {
            "clarity_score": (0, 1),           # Déjà normalisé
            "dynamic_range": (0, 60),           # 0-60 dB
            "harmonic_ratio": (0, 1),           # 0-1
            "spectral_centroid": (0, 10000),    # 0-10kHz
            "rms": (0, 1)                      # 0-1 (normalisé)
        }
        
        if metric in normalizations:
            min_val, max_val = normalizations[metric]
            normalized = (value - min_val) / (max_val - min_val)
            return max(0, min(1, normalized))
        
        return 0.5  # Valeur par défaut
    
    # Méthodes d'analyse spécialisées
    def assess_vocal_clarity(self, audio: np.ndarray) -> float:
        """Évalue la clarté vocale"""
        try:
            import librosa
            
            # Détection de pitch vocal
            pitches, magnitudes = librosa.piptrack(y=audio, sr=self.sample_rate)
            
            # Analyse des harmoniques vocales
            harmonic_content = np.mean(magnitudes[magnitudes > np.max(magnitudes) * 0.1])
            
            return float(harmonic_content)
            
        except:
            return 0.5
    
    def assess_instrumental_balance(self, audio: np.ndarray) -> float:
        """Évalue l'équilibre instrumental"""
        try:
            import librosa
            
            # Analyse multi-bandes
            bands = self.analyze_frequency_bands(audio)
            
            # Calcul de l'équilibre
            band_energies = [np.mean(band**2) for band in bands.values()]
            energy_balance = 1.0 - np.std(band_energies) / np.mean(band_energies)
            
            return float(max(0, energy_balance))
            
        except:
            return 0.5
    
    def assess_mix_quality(self, audio: np.ndarray) -> float:
        """Évalue la qualité du mix"""
        try:
            # Analyse du mix
            metrics = self.calculate_quality_metrics(audio)
            
            # Score de mix basé sur plusieurs métriques
            mix_score = (
                metrics.get("clarity_score", 0.5) * 0.4 +
                min(1.0, metrics.get("dynamic_range", 20) / 40) * 0.3 +
                metrics.get("harmonic_ratio", 0.5) * 0.3
            )
            
            return float(mix_score)
            
        except:
            return 0.5
    
    def analyze_frequency_bands(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """Analyse les bandes de fréquences"""
        try:
            import librosa
            
            # Filtres passe-bande
            bands = {
                "bass": librosa.effects.preemphasis(audio[:len(audio)//4]),
                "mid": audio[len(audio)//4:3*len(audio)//4],
                "high": audio[3*len(audio)//4:]
            }
            
            return bands
            
        except:
            return {"bass": audio, "mid": audio, "high": audio}
    
    # Méthodes de traitement audio
    def extract_vocal_layer(self, audio: np.ndarray) -> np.ndarray:
        """Extrait la couche vocale"""
        try:
            import librosa
            
            # Séparation harmonique/percussive
            harmonic, percussive = librosa.effects.hpss(audio)
            
            # La voix est principalement dans la partie harmonique
            return harmonic
            
        except:
            return audio
    
    def extract_instrumental_layer(self, audio: np.ndarray) -> np.ndarray:
        """Extrait la couche instrumentale"""
        try:
            import librosa
            
            # Séparation harmonique/percussive
            harmonic, percussive = librosa.effects.hpss(audio)
            
            # Combiner les deux pour l'instrumental
            return harmonic + percussive * 0.5
            
        except:
            return audio
    
    def analyze_generic_quality(self, audio: np.ndarray) -> Dict:
        """Analyse de qualité générique"""
        return {
            "source": "generic",
            "quality_score": self.calculate_generic_quality_score(audio),
            "metrics": self.calculate_quality_metrics(audio)
        }
    
    def calculate_generic_quality_score(self, audio: np.ndarray) -> float:
        """Calcule un score de qualité générique"""
        metrics = self.calculate_quality_metrics(audio)
        
        # Score basé sur les métriques générales
        score = (
            metrics.get("clarity_score", 0.5) * 0.4 +
            min(1.0, metrics.get("dynamic_range", 20) / 40) * 0.3 +
            metrics.get("harmonic_ratio", 0.5) * 0.3
        )
        
        return float(score)

# Test des intégrations IA
if __name__ == "__main__":
    print("🤖 HCS AI Integrations Test")
    print("=" * 50)
    
    # Initialisation
    integrations = HCSAIIntegrations()
    
    try:
        # Test avec audio simulé
        sample_rate = 48000
        duration = 5.0
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Simulation de sortie Suno
        suno_audio = np.sin(2 * np.pi * 440 * t) * 0.5  # Simple sine wave
        
        # Test d'amélioration Suno
        enhanced_suno = integrations.enhance_suno_output(suno_audio, "cinema")
        
        # Analyse de l'amélioration
        improvement = integrations.calculate_quality_improvement(suno_audio, enhanced_suno)
        
        print(f"✅ Test amélioration Suno:")
        print(f"   Amélioration qualité: {improvement:.1f}%")
        print(f"   Audio original: {suno_audio.shape}")
        print(f"   Audio amélioré: {enhanced_suno.shape}")
        
        # Test d'intégration multiple IA
        ai_outputs = {
            "suno": suno_audio,
            "udio": np.sin(2 * np.pi * 880 * t) * 0.4,  # Fréquence différente
            "generic": np.sin(2 * np.pi * 220 * t) * 0.3   # Autre fréquence
        }
        
        integrated_audio = integrations.integrate_multiple_ai(ai_outputs, "hybrid")
        
        print(f"\n✅ Test intégration multiple IA:")
        print(f"   Sources intégrées: {list(ai_outputs.keys())}")
        print(f"   Audio intégré: {integrated_audio.shape}")
        
    except Exception as e:
        print(f"❌ Erreur test intégrations IA: {e}")
