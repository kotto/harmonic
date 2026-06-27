#!/usr/bin/env python3
"""
Intégration de la Cohérence Temporelle Avancée dans le Pipeline Vidéo
Extension du quantum_harmonic_video_upscaler.py avec les nouvelles fonctionnalités
"""

import cv2
import numpy as np
import os
import time
import json
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import sys

# Ajout du chemin pour les modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(current_dir)

try:
    from core.harmonic_upscaler import harmonic_upscaler_api
    from core.advanced_temporal_coherence import AdvancedTemporalCoherence, TemporalFrame, MotionField
    from core.quantum_harmonic_video_upscaler import (
        QuantumHarmonicVideoUpscaler, 
        VideoAnalysisResult, 
        FrameUpscalingResult,
        TemporalRealityLevel
    )
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print(f"Current dir: {current_dir}")
    print(f"Parent dir: {parent_dir}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

class EnhancedQuantumHarmonicVideoUpscaler(QuantumHarmonicVideoUpscaler):
    """Version améliorée avec cohérence temporelle avancée"""
    
    def __init__(self, enable_temporal_coherence: bool = True, buffer_size: int = 5):
        super().__init__()
        
        # Système de cohérence temporelle avancée
        self.enable_temporal_coherence = enable_temporal_coherence
        if enable_temporal_coherence:
            self.temporal_coherence = AdvancedTemporalCoherence(
                buffer_size=buffer_size,
                enable_optical_flow=True
            )
            print(f"🌊 Cohérence temporelle activée (buffer: {buffer_size} frames)")
        else:
            self.temporal_coherence = None
            print("📊 Cohérence temporelle désactivée")
        
        # Paramètres d'amélioration temporelle
        self.temporal_enhancement_strength = 0.3
        self.motion_compensation_strength = 0.5
        self.harmonic_fusion_strength = 0.4
    
    def analyze_video(self, video_path: str) -> VideoAnalysisResult:
        """Analyse vidéo améliorée avec cohérence temporelle"""
        print("🔍 Analyse vidéo avancée avec cohérence temporelle...")
        
        # Analyse de base
        base_analysis = super().analyze_video(video_path)
        
        # Analyse temporelle avancée si activée
        if self.enable_temporal_coherence:
            temporal_analysis = self._perform_advanced_temporal_analysis(video_path)
            
            # Fusion des analyses
            enhanced_analysis = self._merge_analyses(base_analysis, temporal_analysis)
            return enhanced_analysis
        
        return base_analysis
    
    def _perform_advanced_temporal_analysis(self, video_path: str) -> Dict[str, float]:
        """Effectue l'analyse temporelle avancée"""
        print("🌊 Analyse temporelle avancée...")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {}
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Échantillonnage pour l'analyse temporelle
        sample_frames = min(30, frame_count)  # Max 30 frames pour l'analyse
        step = max(1, frame_count // sample_frames)
        
        temporal_metrics = {
            'optical_flow_consistency': [],
            'motion_complexity': [],
            'harmonic_coherence_evolution': [],
            'temporal_stability': []
        }
        
        prev_frame = None
        frame_idx = 0
        
        while frame_idx < frame_count:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % step == 0:
                # Ajout au buffer temporel
                temporal_frame = self.temporal_coherence.add_frame(frame, frame_idx)
                
                if temporal_frame.harmonic_features:
                    temporal_metrics['harmonic_coherence_evolution'].append(
                        temporal_frame.harmonic_features.get('harmonic_coherence', 0)
                    )
                    temporal_metrics['motion_complexity'].append(
                        temporal_frame.harmonic_features.get('motion_intensity', 0)
                    )
                    temporal_metrics['temporal_stability'].append(
                        temporal_frame.harmonic_features.get('temporal_symmetry', 0)
                    )
                
                # Analyse de l'optical flow
                if temporal_frame.optical_flow is not None:
                    flow_magnitude = np.sqrt(
                        temporal_frame.optical_flow[..., 0]**2 + 
                        temporal_frame.optical_flow[..., 1]**2
                    )
                    consistency = 1.0 - np.std(flow_magnitude) / (np.mean(flow_magnitude) + 1e-10)
                    temporal_metrics['optical_flow_consistency'].append(consistency)
            
            frame_idx += 1
        
        cap.release()
        
        # Calcul des métriques finales
        advanced_metrics = {}
        for key, values in temporal_metrics.items():
            if values:
                advanced_metrics[f'avg_{key}'] = float(np.mean(values))
                advanced_metrics[f'std_{key}'] = float(np.std(values))
                advanced_metrics[f'min_{key}'] = float(np.min(values))
                advanced_metrics[f'max_{key}'] = float(np.max(values))
        
        print(f"🌊 Analyse temporelle: {len(advanced_metrics)} métriques calculées")
        return advanced_metrics
    
    def _merge_analyses(self, base_analysis: VideoAnalysisResult, 
                       temporal_analysis: Dict[str, float]) -> VideoAnalysisResult:
        """Fusionne l'analyse de base avec l'analyse temporelle avancée"""
        
        # Ajustement des scores basé sur l'analyse temporelle
        motion_complexity = base_analysis.motion_complexity
        temporal_symmetry = base_analysis.temporal_symmetry
        frame_correlation = base_analysis.frame_correlation
        quantum_coherence = base_analysis.quantum_coherence
        
        # Incorporation des métriques avancées
        if 'avg_optical_flow_consistency' in temporal_analysis:
            flow_consistency = temporal_analysis['avg_optical_flow_consistency']
            # Amélioration de la symétrie temporelle avec la consistance du flow
            temporal_symmetry = temporal_symmetry * 0.7 + flow_consistency * 0.3
        
        if 'avg_harmonic_coherence_evolution' in temporal_analysis:
            coherence_evolution = temporal_analysis['avg_harmonic_coherence_evolution']
            # Amélioration de la cohérence quantique
            quantum_coherence = quantum_coherence * 0.6 + coherence_evolution * 0.4
        
        if 'std_motion_complexity' in temporal_analysis:
            motion_stability = 1.0 - temporal_analysis['std_motion_complexity']
            # Ajustement de la complexité du mouvement
            motion_complexity = motion_complexity * 0.8 + (1.0 - motion_stability) * 0.2
        
        # Détermination du niveau optimal avec les nouvelles métriques
        reality_level = self._determine_enhanced_temporal_reality(
            motion_complexity, temporal_symmetry, frame_correlation, quantum_coherence,
            temporal_analysis
        )
        
        return VideoAnalysisResult(
            motion_complexity=motion_complexity,
            temporal_symmetry=temporal_symmetry,
            frame_correlation=frame_correlation,
            quantum_coherence=quantum_coherence,
            optimal_reality_level=reality_level,
            frame_count=base_analysis.frame_count,
            fps=base_analysis.fps,
            duration=base_analysis.duration
        )
    
    def _determine_enhanced_temporal_reality(self, motion_complexity: float, 
                                          temporal_symmetry: float,
                                          frame_correlation: float,
                                          quantum_coherence: float,
                                          temporal_analysis: Dict[str, float]) -> TemporalRealityLevel:
        """Détermination améliorée du niveau de réalité temporel"""
        
        # Scores pondérés de base
        harmonique_score = (temporal_symmetry * 0.3 + 
                          quantum_coherence * 0.4 + 
                          frame_correlation * 0.3)
        
        quantique_score = (quantum_coherence * 0.5 + 
                         motion_complexity * 0.3 + 
                         (1.0 - temporal_symmetry) * 0.2)
        
        classique_score = ((1.0 - motion_complexity) * 0.4 + 
                        (1.0 - quantum_coherence) * 0.3 + 
                        frame_correlation * 0.3)
        
        # Bonus basés sur les métriques avancées
        if 'avg_optical_flow_consistency' in temporal_analysis:
            flow_bonus = temporal_analysis['avg_optical_flow_consistency'] * 0.1
            harmonique_score += flow_bonus
            quantique_score += flow_bonus * 0.5
        
        if 'avg_harmonic_coherence_evolution' in temporal_analysis:
            coherence_bonus = temporal_analysis['avg_harmonic_coherence_evolution'] * 0.1
            harmonique_score += coherence_bonus
            quantique_score += coherence_bonus * 0.8
        
        print(f"🎯 Scores temporels améliorés:")
        print(f"   Harmonique: {harmonique_score:.3f}")
        print(f"   Quantique: {quantique_score:.3f}")
        print(f"   Classique: {classique_score:.3f}")
        
        # Sélection du meilleur score
        max_score = max(harmonique_score, quantique_score, classique_score)
        
        if max_score == harmonique_score:
            return TemporalRealityLevel.HARMONIQUE_TEMPORAL
        elif max_score == quantique_score:
            return TemporalRealityLevel.QUANTIQUE_TEMPORAL
        else:
            return TemporalRealityLevel.CLASSIQUE_TEMPORAL
    
    def upscale_video(self, video_path: str, target_resolution: str = "4K", 
                    energy_level: str = "standard", output_path: str = None) -> List[FrameUpscalingResult]:
        """Pipeline principal d'upscaling vidéo avec cohérence temporelle avancée"""
        
        print(f"🚀 Lancement upscaling vidéo avancé: {video_path}")
        print(f"🌊 Cohérence temporelle: {'Activée' if self.enable_temporal_coherence else 'Désactivée'}")
        
        # 1. Analyse vidéo améliorée
        analysis = self.analyze_video(video_path)
        self.current_reality_level = analysis.optimal_reality_level
        
        print(f"\n🌊 Niveau de réalité temporel optimal: {analysis.optimal_reality_level.value}")
        
        # 2. Préparation de l'upscaling
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        target_size = self._parse_target_resolution(target_resolution)
        
        # 3. Pipeline frame-by-frame avec cohérence temporelle
        results = []
        processed_frames = 0
        
        if output_path:
            os.makedirs(output_path, exist_ok=True)
            frames_dir = os.path.join(output_path, "frames")
            os.makedirs(frames_dir, exist_ok=True)
        
        print(f"\n🎬 Début du traitement frame-by-frame avec cohérence temporelle...")
        start_time = time.time()
        
        for frame_idx in range(frame_count):
            ret, frame = cap.read()
            if not ret:
                break
            
            # Ajout au buffer temporel si activé
            if self.enable_temporal_coherence:
                temporal_frame = self.temporal_coherence.add_frame(frame, frame_idx)
                
                # Récupération du contexte temporel
                temporal_context = self.temporal_coherence.get_temporal_context(frame_idx)
                
                # Amélioration temporelle de la frame
                enhanced_frame = self.temporal_coherence.enhance_temporal_coherence(
                    frame, temporal_context
                )
            else:
                enhanced_frame = frame
                temporal_context = {}
            
            # Upscaling avec l'upscaler existant
            try:
                frame_energy = self._calculate_enhanced_frame_energy(energy_level, analysis, temporal_context)
                
                result = harmonic_upscaler_api.upscale_image(
                    image_array=enhanced_frame,
                    target_size=target_size,
                    energy_level='custom',
                    custom_energy=frame_energy
                )
                
                if result['success']:
                    upscaled_frame = self._decode_base64_image(result['upscaled_image_base64'])
                    
                    # Post-processing temporel si activé
                    if self.enable_temporal_coherence and temporal_context.get('motion_field'):
                        upscaled_frame = self._apply_temporal_post_processing(
                            upscaled_frame, temporal_context
                        )
                    
                    # Sauvegarde
                    if output_path:
                        frame_output_path = os.path.join(frames_dir, f"frame_{frame_idx:06d}.png")
                        cv2.imwrite(frame_output_path, upscaled_frame)
                    
                    # Création du résultat
                    frame_result = FrameUpscalingResult(
                        frame_number=frame_idx,
                        original_shape=frame.shape,
                        upscaled_shape=upscaled_frame.shape,
                        reality_level_used=result['reality_level_used'],
                        processing_time=result['processing_time'],
                        quality_metrics=result['quality_metrics'],
                        efficiency_metrics=result['efficiency_metrics']
                    )
                    
                    results.append(frame_result)
                    processed_frames += 1
                    
                    # Progression
                    if frame_idx % 10 == 0:
                        progress = (frame_idx / frame_count) * 100
                        elapsed = time.time() - start_time
                        eta = (elapsed / frame_idx) * (frame_count - frame_idx) if frame_idx > 0 else 0
                        
                        # Affichage du statut temporel
                        if self.enable_temporal_coherence:
                            buffer_status = self.temporal_coherence.get_buffer_status()
                            print(f"📈 Progression: {progress:.1f}% ({frame_idx}/{frame_count}) - ETA: {eta:.1f}s - Buffer: {buffer_status['buffer_size']}/{buffer_status['max_buffer_size']}")
                        else:
                            print(f"📈 Progression: {progress:.1f}% ({frame_idx}/{frame_count}) - ETA: {eta:.1f}s")
                
            except Exception as e:
                print(f"❌ Erreur frame {frame_idx}: {e}")
                continue
        
        cap.release()
        
        # 4. Reconstruction vidéo
        if output_path and results:
            self._reconstruct_video(results, output_path, fps)
        
        # 5. Rapport final amélioré
        self._generate_enhanced_video_report(results, analysis, output_path)
        
        total_time = time.time() - start_time
        print(f"\n🎉 Upscaling vidéo avancé terminé!")
        print(f"📊 Frames traitées: {processed_frames}/{frame_count}")
        print(f"⏱️ Temps total: {total_time:.2f}s")
        print(f"🚀 Vitesse: {processed_frames/total_time:.2f} fps")
        
        if self.enable_temporal_coherence:
            final_buffer_status = self.temporal_coherence.get_buffer_status()
            print(f"🌊 Buffer temporel final: {final_buffer_status}")
        
        return results
    
    def _calculate_enhanced_frame_energy(self, energy_level: str, analysis: VideoAnalysisResult, 
                                     temporal_context: Dict[str, Any]) -> float:
        """Calcul amélioré de l'énergie par frame"""
        base_energy = super()._calculate_frame_energy(energy_level, analysis)
        
        if not temporal_context:
            return base_energy
        
        # Ajustements basés sur le contexte temporel
        energy_multiplier = 1.0
        
        # Bonus pour frames avec forte cohérence temporelle
        if 'harmonic_trend' in temporal_context:
            trend = temporal_context['harmonic_trend']
            if 'harmonic_coherence_trend' in trend:
                coherence_trend = trend['harmonic_coherence_trend']
                if coherence_trend > 0:  # Tendance positive
                    energy_multiplier *= 1.1
        
        # Ajustement selon le champ de mouvement
        if 'motion_field' in temporal_context and temporal_context['motion_field']:
            motion_field = temporal_context['motion_field']
            avg_motion = np.mean(motion_field.motion_magnitude)
            
            # Plus d'énergie pour les frames avec beaucoup de mouvement
            if avg_motion > 1.0:
                energy_multiplier *= 1.2
            elif avg_motion < 0.1:
                energy_multiplier *= 0.9
        
        return base_energy * energy_multiplier
    
    def _apply_temporal_post_processing(self, upscaled_frame: np.ndarray, 
                                    temporal_context: Dict[str, Any]) -> np.ndarray:
        """Applique le post-processing temporel à la frame upscalée"""
        processed_frame = upscaled_frame.copy()
        
        # 1. Stabilisation harmonique finale
        if 'harmonic_trend' in temporal_context:
            processed_frame = self.temporal_coherence._apply_harmonic_stabilization(
                processed_frame, 
                temporal_context['harmonic_trend']
            )
        
        # 2. Fusion temporelle finale
        if 'previous_frames' in temporal_context and temporal_context['previous_frames']:
            processed_frame = self.temporal_coherence._apply_harmonic_temporal_fusion(
                processed_frame,
                temporal_context['previous_frames'][-1:]  # Dernière frame précédente
            )
        
        return processed_frame
    
    def _generate_enhanced_video_report(self, results: List[FrameUpscalingResult], 
                                     analysis: VideoAnalysisResult, output_path: str):
        """Génère un rapport détaillé avec métriques temporelles"""
        if not results:
            return
        
        # Rapport de base
        base_report = {
            "video_analysis": {
                "motion_complexity": float(analysis.motion_complexity),
                "temporal_symmetry": float(analysis.temporal_symmetry),
                "frame_correlation": float(analysis.frame_correlation),
                "quantum_coherence": float(analysis.quantum_coherence),
                "optimal_reality_level": analysis.optimal_reality_level.value,
                "frame_count": int(analysis.frame_count),
                "fps": float(analysis.fps),
                "duration": float(analysis.duration)
            },
            "upscaling_results": {
                "total_frames_processed": len(results),
                "average_processing_time": float(np.mean([r.processing_time for r in results])),
                "average_psnr": float(np.mean([r.quality_metrics.get('psnr', 0) for r in results])),
                "average_ssim": float(np.mean([r.quality_metrics.get('ssim', 0) for r in results])),
                "reality_levels_used": list(set([r.reality_level_used for r in results]))
            },
            "performance_metrics": {
                "total_processing_time": float(sum([r.processing_time for r in results])),
                "processing_fps": float(len(results) / sum([r.processing_time for r in results])) if results else 0.0
            }
        }
        
        # Ajout des métriques temporelles avancées
        if self.enable_temporal_coherence:
            buffer_status = self.temporal_coherence.get_buffer_status()
            base_report["temporal_coherence_metrics"] = {
                "enabled": True,
                "buffer_size": buffer_status['buffer_size'],
                "max_buffer_size": buffer_status['max_buffer_size'],
                "optical_flow_available": buffer_status['has_optical_flow'],
                "harmonic_features_available": buffer_status['harmonic_features_available'],
                "enhancement_strength": self.temporal_enhancement_strength,
                "motion_compensation_strength": self.motion_compensation_strength,
                "harmonic_fusion_strength": self.harmonic_fusion_strength
            }
        
        if output_path:
            report_path = os.path.join(output_path, "enhanced_video_upscaling_report.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(base_report, f, indent=2, ensure_ascii=False)
            print(f"📄 Rapport amélioré sauvegardé: {report_path}")

def test_enhanced_video_upscaler():
    """Test complet de l'upscaler vidéo amélioré"""
    print("🚀 TEST DE L'UPSCALER VIDÉO AMÉLIORÉ")
    print("=" * 60)
    
    # Création vidéo de test
    from test_video_upscaler import create_test_video
    test_video_path = create_test_video(
        output_path="enhanced_test_video.mp4",
        duration=3,
        fps=15
    )
    
    if not os.path.exists(test_video_path):
        print("❌ Échec de création de la vidéo de test")
        return False
    
    # Test avec cohérence temporelle activée
    print("\n🌊 Test AVEC cohérence temporelle:")
    enhanced_upscaler = EnhancedQuantumHarmonicVideoUpscaler(
        enable_temporal_coherence=True,
        buffer_size=5
    )
    
    results_with_temporal = enhanced_upscaler.upscale_video(
        video_path=test_video_path,
        target_resolution="1080p",
        energy_level="standard",
        output_path="enhanced_upscaled_video_with_temporal"
    )
    
    # Test sans cohérence temporelle
    print("\n📊 Test SANS cohérence temporelle:")
    basic_upscaler = EnhancedQuantumHarmonicVideoUpscaler(
        enable_temporal_coherence=False
    )
    
    results_without_temporal = basic_upscaler.upscale_video(
        video_path=test_video_path,
        target_resolution="1080p",
        energy_level="standard",
        output_path="enhanced_upscaled_video_without_temporal"
    )
    
    # Comparaison des résultats
    print("\n📊 COMPARAISON DES RÉSULTATS:")
    print("=" * 40)
    
    if results_with_temporal and results_without_temporal:
        # Métriques avec cohérence temporelle
        avg_psnr_with = np.mean([r.quality_metrics.get('psnr', 0) for r in results_with_temporal])
        avg_ssim_with = np.mean([r.quality_metrics.get('ssim', 0) for r in results_with_temporal])
        time_with = sum([r.processing_time for r in results_with_temporal])
        
        # Métriques sans cohérence temporelle
        avg_psnr_without = np.mean([r.quality_metrics.get('psnr', 0) for r in results_without_temporal])
        avg_ssim_without = np.mean([r.quality_metrics.get('ssim', 0) for r in results_without_temporal])
        time_without = sum([r.processing_time for r in results_without_temporal])
        
        print(f"📊 PSNR Moyen:")
        print(f"   Avec cohérence: {avg_psnr_with:.2f} dB")
        print(f"   Sans cohérence: {avg_psnr_without:.2f} dB")
        print(f"   Amélioration: {avg_psnr_with - avg_psnr_without:+.2f} dB")
        
        print(f"\n🎯 SSIM Moyen:")
        print(f"   Avec cohérence: {avg_ssim_with:.4f}")
        print(f"   Sans cohérence: {avg_ssim_without:.4f}")
        print(f"   Amélioration: {avg_ssim_with - avg_ssim_without:+.4f}")
        
        print(f"\n⏱️ Temps Total:")
        print(f"   Avec cohérence: {time_with:.2f}s")
        print(f"   Sans cohérence: {time_without:.2f}s")
        print(f"   Surcoût: {((time_with - time_without) / time_without * 100):+.1f}%")
        
        # Vérification des fichiers
        print(f"\n📁 Fichiers générés:")
        test_files = [
            "enhanced_upscaled_video_with_temporal/enhanced_video_upscaling_report.json",
            "enhanced_upscaled_video_without_temporal/enhanced_video_upscaling_report.json"
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"  ✅ {file_path} ({size} bytes)")
            else:
                print(f"  ❌ {file_path} (manquant)")
        
        return True
    else:
        print("❌ Échec du test")
        return False

if __name__ == "__main__":
    test_enhanced_video_upscaler()
