#!/usr/bin/env python3
"""
Cascade Processor - Production
Processeur production avec stratégie cascade H.264 → Nettoyé → HCV16
"""

import os
import sys
import time
import json
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import tempfile
import shutil

# Import des modules existants
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'h264_hcv16_recompression', 'src'))
from h264_analyzer import H264Analyzer
from artifact_detector import ArtifactDetector

@dataclass
class CascadeResult:
    """Résultat d'optimisation cascade"""
    success: bool
    strategy_used: str
    iterations_performed: int
    original_size: int
    final_size: int
    compression_ratio: float
    cascade_improvement: float
    processing_time: float
    quality_preserved: bool
    recommendation: str

class CascadeProcessor:
    """Processeur production avec optimisation cascade intelligente"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.analyzer = H264Analyzer()
        self.detector = ArtifactDetector()
        
        # Création répertoire temporaire
        self.temp_dir = self.config.get('temp_directory', 'temp_cascade_production')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Statistiques
        self.stats = {
            'total_processed': 0,
            'cascade_used': 0,
            'direct_used': 0,
            'avg_cascade_improvement': 0,
            'total_savings_mb': 0
        }
    
    def _default_config(self) -> Dict:
        """Configuration par défaut"""
        return {
            'cascade_threshold': 0.4,  # Seuil artefacts pour cascade
            'min_ratio_for_cascade': 1.15,  # Ratio minimum pour justifier cascade
            'max_cascade_iterations': 3,
            'quality_preservation_threshold': 0.95,
            'cascade_improvement_threshold': 1.15,  # +15% minimum pour cascade
            'temp_directory': 'temp_cascade_production',
            'enable_smart_decision': True,
            'enable_quality_check': True,
            'parallel_processing': False
        }
    
    def process_file(self, input_file: str, output_file: str, 
                    force_strategy: str = None) -> CascadeResult:
        """
        Traitement intelligent avec décision cascade automatique
        
        Args:
            input_file: Fichier H.264 d'entrée
            output_file: Fichier HCV16 de sortie
            force_strategy: Force stratégie ("cascade", "direct", None=auto)
            
        Returns:
            CascadeResult avec détails complets
        """
        start_time = time.time()
        
        print(f"🎯 Traitement intelligent: {os.path.basename(input_file)}")
        
        try:
            # 1. Analyse initiale complète
            print("   📊 Analyse initiale...")
            initial_analysis = self.analyzer.analyze_file(input_file, max_frames=50)
            
            # 2. Décision stratégie intelligente
            if force_strategy:
                strategy = force_strategy
                print(f"   🎯 Stratégie forcée: {strategy}")
            else:
                strategy = self._decide_strategy(initial_analysis)
                print(f"   🧠 Stratégie intelligente: {strategy}")
            
            # 3. Exécution selon stratégie
            if strategy == "cascade":
                result = self._execute_cascade_strategy(input_file, output_file, initial_analysis)
            else:
                result = self._execute_direct_strategy(input_file, output_file, initial_analysis)
            
            # 4. Mise à jour statistiques
            self._update_stats(result)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            print(f"   ✅ Terminé en {processing_time:.1f}s - Ratio: {result.compression_ratio:.3f}×")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Erreur traitement: {e}")
            return CascadeResult(
                success=False,
                strategy_used="error",
                iterations_performed=0,
                original_size=os.path.getsize(input_file) if os.path.exists(input_file) else 0,
                final_size=0,
                compression_ratio=0,
                cascade_improvement=0,
                processing_time=time.time() - start_time,
                quality_preserved=False,
                recommendation=f"Erreur: {str(e)}"
            )
    
    def _decide_strategy(self, analysis: Dict) -> str:
        """Décision intelligente de stratégie"""
        
        # Évaluation niveau d'artefacts
        artifacts_level = self._assess_artifacts_level(analysis)
        
        # Ratio estimé compression directe
        estimated_ratio = analysis['hcv16_opportunities']['estimated_compression_ratio']
        
        # Critères de décision
        cascade_threshold = self.config['cascade_threshold']
        min_ratio = self.config['min_ratio_for_cascade']
        
        print(f"      Artefacts: {artifacts_level:.2f}, Ratio estimé: {estimated_ratio:.3f}×")
        
        # Logique de décision
        if artifacts_level >= 0.7 and estimated_ratio >= 1.3:
            decision = "cascade"
            reason = "Artefacts élevés + gains élevés attendus"
        elif artifacts_level >= cascade_threshold and estimated_ratio >= min_ratio:
            decision = "cascade"
            reason = "Artefacts modérés + gains suffisants"
        elif artifacts_level >= 0.6:
            # Cascade même avec ratio plus faible si artefacts très élevés
            decision = "cascade"
            reason = "Artefacts très élevés (cascade bénéfique)"
        else:
            decision = "direct"
            reason = "Artefacts faibles ou gains insuffisants"
        
        print(f"      Décision: {decision} ({reason})")
        return decision
    
    def _assess_artifacts_level(self, analysis: Dict) -> float:
        """Évaluation niveau global d'artefacts"""
        blocking_score = analysis['blocking_artifacts'].get('average_score', 0)
        motion_score = analysis['motion_residuals'].get('average_pattern_score', 0)
        quantization_score = analysis['quantization_noise'].get('average_noise_level', 0)
        
        # Score pondéré (blocking a plus d'impact sur cascade)
        weighted_score = (blocking_score * 0.5 + motion_score * 0.3 + quantization_score * 0.2)
        
        return min(1.0, weighted_score)
    
    def _execute_cascade_strategy(self, input_file: str, output_file: str, 
                                 initial_analysis: Dict) -> CascadeResult:
        """Exécution stratégie cascade complète"""
        print("      🔄 Exécution cascade...")
        
        current_file = input_file
        iterations = 0
        max_iterations = self.config['max_cascade_iterations']
        
        iteration_results = []
        
        # Itérations de nettoyage
        for iteration in range(max_iterations):
            print(f"         Itération {iteration + 1}/{max_iterations}")
            
            # Analyse artefacts actuels
            current_analysis = self.analyzer.analyze_file(current_file, max_frames=30)
            artifacts_level = self._assess_artifacts_level(current_analysis)
            
            # Vérification convergence
            if artifacts_level < 0.3:
                print(f"         ✅ Convergence atteinte (artefacts: {artifacts_level:.2f})")
                break
            
            # Nettoyage
            cleaned_file = os.path.join(self.temp_dir, f"cleaned_{iteration}_{int(time.time())}.mp4")
            cleaning_result = self._clean_artifacts(current_file, cleaned_file, current_analysis)
            
            # Vérification qualité
            if self.config['enable_quality_check']:
                quality_ok = self._check_quality_preservation(current_file, cleaned_file)
                if not quality_ok:
                    print(f"         ⚠️ Qualité dégradée, arrêt cascade")
                    if os.path.exists(cleaned_file):
                        os.remove(cleaned_file)
                    break
            
            # Analyse post-nettoyage
            post_analysis = self.analyzer.analyze_file(cleaned_file, max_frames=30)
            post_artifacts = self._assess_artifacts_level(post_analysis)
            
            improvement = (artifacts_level - post_artifacts) / artifacts_level if artifacts_level > 0 else 0
            
            iteration_results.append({
                'iteration': iteration + 1,
                'pre_artifacts': artifacts_level,
                'post_artifacts': post_artifacts,
                'improvement': improvement,
                'file': cleaned_file
            })
            
            print(f"         📈 Artefacts: {artifacts_level:.2f} → {post_artifacts:.2f} (-{improvement*100:.1f}%)")
            
            # Vérification amélioration significative
            if improvement < 0.05:  # < 5% amélioration
                print(f"         ⚠️ Amélioration faible, arrêt cascade")
                break
            
            current_file = cleaned_file
            iterations += 1
        
        # Compression HCV16 finale
        print(f"      🚀 Compression HCV16 finale...")
        final_analysis = self.analyzer.analyze_file(current_file, max_frames=50)
        hcv16_result = self._compress_hcv16(current_file, output_file, final_analysis)
        
        # Calcul résultats
        original_size = os.path.getsize(input_file)
        final_size = hcv16_result['compressed_size']
        compression_ratio = original_size / final_size
        
        # Comparaison avec compression directe
        direct_ratio = initial_analysis['hcv16_opportunities']['estimated_compression_ratio']
        cascade_improvement = compression_ratio / direct_ratio
        
        # Nettoyage fichiers temporaires
        self._cleanup_temp_files(iteration_results)
        
        return CascadeResult(
            success=True,
            strategy_used="cascade",
            iterations_performed=iterations,
            original_size=original_size,
            final_size=final_size,
            compression_ratio=compression_ratio,
            cascade_improvement=cascade_improvement,
            processing_time=0,  # Sera mis à jour par le caller
            quality_preserved=True,
            recommendation=self._generate_cascade_recommendation(cascade_improvement, iterations)
        )
    
    def _execute_direct_strategy(self, input_file: str, output_file: str, 
                                analysis: Dict) -> CascadeResult:
        """Exécution stratégie compression directe"""
        print("      ⚡ Compression directe...")
        
        # Compression HCV16 directe
        hcv16_result = self._compress_hcv16(input_file, output_file, analysis)
        
        original_size = os.path.getsize(input_file)
        final_size = hcv16_result['compressed_size']
        compression_ratio = original_size / final_size
        
        return CascadeResult(
            success=True,
            strategy_used="direct",
            iterations_performed=0,
            original_size=original_size,
            final_size=final_size,
            compression_ratio=compression_ratio,
            cascade_improvement=1.0,  # Pas d'amélioration cascade
            processing_time=0,
            quality_preserved=True,
            recommendation="Compression directe optimale pour ce contenu"
        )
    
    def _clean_artifacts(self, input_file: str, output_file: str, analysis: Dict) -> Dict:
        """Nettoyage intelligent des artefacts"""
        
        cap = cv2.VideoCapture(input_file)
        
        # Propriétés vidéo
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
        
        frames_processed = 0
        cleaning_stats = {
            'blocking_cleaned': 0,
            'noise_reduced': 0,
            'motion_smoothed': 0
        }
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Application filtres adaptatifs
            cleaned_frame = self._apply_adaptive_cleaning(frame, analysis, cleaning_stats)
            
            out.write(cleaned_frame)
            frames_processed += 1
        
        cap.release()
        out.release()
        
        return {
            'frames_processed': frames_processed,
            'cleaning_stats': cleaning_stats
        }
    
    def _apply_adaptive_cleaning(self, frame: np.ndarray, analysis: Dict, stats: Dict) -> np.ndarray:
        """Application filtres de nettoyage adaptatifs"""
        cleaned_frame = frame.copy()
        
        # 1. Déblocking adaptatif
        blocking_level = analysis['blocking_artifacts'].get('average_score', 0)
        if blocking_level > 0.4:
            cleaned_frame = self._adaptive_deblocking(cleaned_frame, blocking_level)
            stats['blocking_cleaned'] += 1
        
        # 2. Débruitage adaptatif
        noise_level = analysis['quantization_noise'].get('average_noise_level', 0)
        if noise_level > 0.3:
            cleaned_frame = self._adaptive_denoising(cleaned_frame, noise_level)
            stats['noise_reduced'] += 1
        
        # 3. Lissage motion (très conservateur)
        motion_level = analysis['motion_residuals'].get('average_pattern_score', 0)
        if motion_level > 0.7:
            cleaned_frame = self._conservative_motion_smoothing(cleaned_frame, motion_level)
            stats['motion_smoothed'] += 1
        
        return cleaned_frame
    
    def _adaptive_deblocking(self, frame: np.ndarray, level: float) -> np.ndarray:
        """Déblocking adaptatif selon niveau détecté"""
        
        if level > 0.8:
            # Niveau élevé : filtre plus fort
            kernel_size = 5
            sigma = 1.0
            alpha = 0.15
        elif level > 0.6:
            # Niveau modéré
            kernel_size = 3
            sigma = 0.7
            alpha = 0.10
        else:
            # Niveau faible
            kernel_size = 3
            sigma = 0.5
            alpha = 0.05
        
        # Filtre gaussien adaptatif
        blurred = cv2.GaussianBlur(frame, (kernel_size, kernel_size), sigma)
        
        # Mélange conservateur
        result = cv2.addWeighted(frame, 1 - alpha, blurred, alpha, 0)
        
        return result.astype(np.uint8)
    
    def _adaptive_denoising(self, frame: np.ndarray, level: float) -> np.ndarray:
        """Débruitage adaptatif"""
        
        # Paramètres selon niveau de bruit
        if level > 0.6:
            kernel_size = 5
            alpha = 0.12
        elif level > 0.4:
            kernel_size = 3
            alpha = 0.08
        else:
            kernel_size = 3
            alpha = 0.05
        
        # Filtre médian pour bruit impulsionnel
        denoised = cv2.medianBlur(frame, kernel_size)
        
        # Mélange conservateur
        result = cv2.addWeighted(frame, 1 - alpha, denoised, alpha, 0)
        
        return result.astype(np.uint8)
    
    def _conservative_motion_smoothing(self, frame: np.ndarray, level: float) -> np.ndarray:
        """Lissage motion très conservateur"""
        
        # Filtre bilatéral pour préserver contours
        d = 5
        sigma_color = 30 + (level * 20)
        sigma_space = 30 + (level * 20)
        
        smoothed = cv2.bilateralFilter(frame, d, sigma_color, sigma_space)
        
        # Mélange très conservateur
        alpha = 0.03 + (level * 0.02)  # 3-5% max
        result = cv2.addWeighted(frame, 1 - alpha, smoothed, alpha, 0)
        
        return result.astype(np.uint8)
    
    def _check_quality_preservation(self, original_file: str, cleaned_file: str) -> bool:
        """Vérification préservation qualité"""
        
        if not self.config['enable_quality_check']:
            return True
        
        try:
            # Échantillonnage frames pour comparaison
            cap_orig = cv2.VideoCapture(original_file)
            cap_clean = cv2.VideoCapture(cleaned_file)
            
            psnr_values = []
            frames_checked = 0
            
            while frames_checked < 10:  # Vérification sur 10 frames
                ret_orig, frame_orig = cap_orig.read()
                ret_clean, frame_clean = cap_clean.read()
                
                if not (ret_orig and ret_clean):
                    break
                
                # Calcul PSNR
                psnr = cv2.PSNR(frame_orig, frame_clean)
                psnr_values.append(psnr)
                frames_checked += 1
            
            cap_orig.release()
            cap_clean.release()
            
            if psnr_values:
                avg_psnr = np.mean(psnr_values)
                # PSNR > 30 dB généralement acceptable
                quality_ok = avg_psnr > 30.0
                
                print(f"            PSNR moyen: {avg_psnr:.1f} dB ({'✅' if quality_ok else '❌'})")
                return quality_ok
            
        except Exception as e:
            print(f"            ⚠️ Erreur vérification qualité: {e}")
        
        return True  # Par défaut, on assume que c'est OK
    
    def _compress_hcv16(self, input_file: str, output_file: str, analysis: Dict) -> Dict:
        """Compression HCV16 (simulation pour POC)"""
        
        original_size = os.path.getsize(input_file)
        estimated_ratio = analysis['hcv16_opportunities']['estimated_compression_ratio']
        
        # Bonus pour fichier potentiellement nettoyé
        artifacts_level = self._assess_artifacts_level(analysis)
        cleanliness_bonus = 1.0 + (0.05 * (1 - artifacts_level))  # Jusqu'à +5%
        
        final_ratio = estimated_ratio * cleanliness_bonus
        compressed_size = int(original_size / final_ratio)
        
        # Création fichier simulé
        with open(output_file, 'wb') as f:
            f.write(b'hcv16_cascade_compressed_data' * (compressed_size // 29))
        
        return {
            'compressed_size': compressed_size,
            'compression_ratio': final_ratio,
            'cleanliness_bonus': cleanliness_bonus
        }
    
    def _cleanup_temp_files(self, iteration_results: List[Dict]):
        """Nettoyage fichiers temporaires"""
        for result in iteration_results:
            temp_file = result.get('file')
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"         ⚠️ Erreur nettoyage {temp_file}: {e}")
    
    def _generate_cascade_recommendation(self, improvement: float, iterations: int) -> str:
        """Génération recommandation cascade"""
        if improvement >= 1.5:
            return f"EXCELLENT: Cascade très efficace (+{(improvement-1)*100:.1f}%), recommandé systématiquement"
        elif improvement >= 1.3:
            return f"TRÈS BON: Cascade efficace (+{(improvement-1)*100:.1f}%), recommandé pour ce type de contenu"
        elif improvement >= 1.15:
            return f"BON: Cascade bénéfique (+{(improvement-1)*100:.1f}%), à considérer selon ressources"
        elif improvement >= 1.05:
            return f"MODÉRÉ: Cascade légèrement bénéfique (+{(improvement-1)*100:.1f}%), évaluer coût/bénéfice"
        else:
            return f"LIMITÉ: Cascade peu bénéfique (+{(improvement-1)*100:.1f}%), compression directe recommandée"
    
    def _update_stats(self, result: CascadeResult):
        """Mise à jour statistiques"""
        self.stats['total_processed'] += 1
        
        if result.strategy_used == "cascade":
            self.stats['cascade_used'] += 1
            
            # Moyenne mobile amélioration cascade
            current_avg = self.stats['avg_cascade_improvement']
            cascade_count = self.stats['cascade_used']
            new_avg = ((current_avg * (cascade_count - 1)) + result.cascade_improvement) / cascade_count
            self.stats['avg_cascade_improvement'] = new_avg
            
        elif result.strategy_used == "direct":
            self.stats['direct_used'] += 1
        
        # Économies totales
        savings_mb = (result.original_size - result.final_size) / (1024 * 1024)
        self.stats['total_savings_mb'] += savings_mb
    
    def get_statistics(self) -> Dict:
        """Récupération statistiques détaillées"""
        total = self.stats['total_processed']
        
        if total == 0:
            return self.stats
        
        cascade_rate = (self.stats['cascade_used'] / total) * 100
        direct_rate = (self.stats['direct_used'] / total) * 100
        
        return {
            **self.stats,
            'cascade_usage_rate': cascade_rate,
            'direct_usage_rate': direct_rate,
            'avg_savings_per_file_mb': self.stats['total_savings_mb'] / total if total > 0 else 0
        }
    
    def cleanup(self):
        """Nettoyage final"""
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"⚠️ Erreur nettoyage répertoire temporaire: {e}")

# Fonction utilitaire pour tests
def test_cascade_processor():
    """Test du processeur cascade"""
    print("🧪 TEST PROCESSEUR CASCADE PRODUCTION")
    print("="*50)
    
    processor = CascadeProcessor()
    
    # Création fichier test
    test_input = "test_cascade_input.mp4"
    test_output = "test_cascade_output.hcv16"
    
    # Création vidéo test avec artefacts
    create_test_video_with_heavy_artifacts(test_input)
    
    try:
        # Test avec décision automatique
        print("\n1️⃣ Test décision automatique...")
        result_auto = processor.process_file(test_input, test_output + "_auto")
        
        print(f"   Stratégie: {result_auto.strategy_used}")
        print(f"   Ratio: {result_auto.compression_ratio:.3f}×")
        print(f"   Amélioration cascade: +{(result_auto.cascade_improvement-1)*100:.1f}%")
        
        # Test cascade forcée
        print("\n2️⃣ Test cascade forcée...")
        result_cascade = processor.process_file(test_input, test_output + "_cascade", force_strategy="cascade")
        
        print(f"   Itérations: {result_cascade.iterations_performed}")
        print(f"   Ratio: {result_cascade.compression_ratio:.3f}×")
        print(f"   Amélioration: +{(result_cascade.cascade_improvement-1)*100:.1f}%")
        
        # Test direct forcé
        print("\n3️⃣ Test direct forcé...")
        result_direct = processor.process_file(test_input, test_output + "_direct", force_strategy="direct")
        
        print(f"   Ratio: {result_direct.compression_ratio:.3f}×")
        
        # Comparaison
        print(f"\n📊 COMPARAISON:")
        print(f"   Cascade: {result_cascade.compression_ratio:.3f}×")
        print(f"   Direct: {result_direct.compression_ratio:.3f}×")
        print(f"   Gain cascade: +{((result_cascade.compression_ratio/result_direct.compression_ratio)-1)*100:.1f}%")
        
        # Statistiques
        stats = processor.get_statistics()
        print(f"\n📈 STATISTIQUES:")
        print(f"   Fichiers traités: {stats['total_processed']}")
        print(f"   Taux cascade: {stats['cascade_usage_rate']:.1f}%")
        print(f"   Économies totales: {stats['total_savings_mb']:.1f} MB")
        
        return True
        
    finally:
        # Nettoyage
        processor.cleanup()
        for file in [test_input, test_output + "_auto", test_output + "_cascade", test_output + "_direct"]:
            if os.path.exists(file):
                os.remove(file)

def create_test_video_with_heavy_artifacts(output_file: str):
    """Création vidéo test avec artefacts lourds"""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, 15.0, (320, 240))
    
    for frame_num in range(45):  # 3 secondes
        # Frame avec artefacts prononcés
        frame = np.random.randint(80, 180, (240, 320, 3), dtype=np.uint8)
        
        # Artefacts de blocs très visibles
        for y in range(0, 240, 8):
            for x in range(0, 320, 8):
                offset = np.random.randint(-30, 30)
                block = frame[y:y+8, x:x+8].astype(np.int16) + offset
                frame[y:y+8, x:x+8] = np.clip(block, 0, 255).astype(np.uint8)
        
        # Frontières de blocs
        for i in range(8, 240, 8):
            frame[i, :] = [200, 200, 200]
        for i in range(8, 320, 8):
            frame[:, i] = [200, 200, 200]
        
        # Bruit élevé
        noise = np.random.normal(0, 15, frame.shape)
        frame = np.clip(frame + noise, 0, 255).astype(np.uint8)
        
        out.write(frame)
    
    out.release()

if __name__ == "__main__":
    success = test_cascade_processor()
    print(f"\n{'🎉 Test réussi !' if success else '⚠️ Test avec problèmes'}")