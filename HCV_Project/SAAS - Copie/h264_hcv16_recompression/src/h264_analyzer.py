#!/usr/bin/env python3
"""
H.264 Bitstream Analyzer
Analyse les artefacts et patterns exploitables par HCV16
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import struct
import os

class H264Analyzer:
    """Analyseur de fichiers H.264 pour identifier les opportunités HCV16"""
    
    def __init__(self):
        self.analysis_results = {}
        self.frame_cache = []
        self.artifact_patterns = {}
        
    def analyze_file(self, h264_file: str, max_frames: int = 100) -> Dict:
        """
        Analyse complète d'un fichier H.264
        
        Args:
            h264_file: Chemin vers fichier H.264
            max_frames: Nombre max de frames à analyser
            
        Returns:
            Dict avec résultats d'analyse
        """
        print(f"🔍 Analyse H.264: {h264_file}")
        
        if not os.path.exists(h264_file):
            raise FileNotFoundError(f"Fichier non trouvé: {h264_file}")
        
        # Informations de base
        file_info = self._get_file_info(h264_file)
        
        # Chargement frames pour analyse
        frames = self._load_frames(h264_file, max_frames)
        
        # Analyses spécialisées
        blocking_analysis = self._analyze_blocking_artifacts(frames)
        motion_analysis = self._analyze_motion_residuals(frames)
        quantization_analysis = self._analyze_quantization_noise(frames)
        temporal_analysis = self._analyze_temporal_patterns(frames)
        
        # Compilation résultats
        results = {
            'file_info': file_info,
            'frames_analyzed': len(frames),
            'blocking_artifacts': blocking_analysis,
            'motion_residuals': motion_analysis,
            'quantization_noise': quantization_analysis,
            'temporal_patterns': temporal_analysis,
            'hcv16_opportunities': self._calculate_hcv16_opportunities({
                'blocking': blocking_analysis,
                'motion': motion_analysis,
                'quantization': quantization_analysis,
                'temporal': temporal_analysis
            })
        }
        
        self.analysis_results = results
        return results
    
    def _get_file_info(self, h264_file: str) -> Dict:
        """Extraction informations de base du fichier"""
        try:
            cap = cv2.VideoCapture(h264_file)
            
            info = {
                'file_size_mb': os.path.getsize(h264_file) / (1024 * 1024),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'duration_sec': 0
            }
            
            if info['fps'] > 0:
                info['duration_sec'] = info['frame_count'] / info['fps']
            
            # Calcul bitrate approximatif
            if info['duration_sec'] > 0:
                info['bitrate_mbps'] = (info['file_size_mb'] * 8) / info['duration_sec']
            else:
                info['bitrate_mbps'] = 0
            
            cap.release()
            return info
            
        except Exception as e:
            print(f"⚠️  Erreur extraction info: {e}")
            return {'error': str(e)}
    
    def _load_frames(self, h264_file: str, max_frames: int) -> List[np.ndarray]:
        """Chargement frames pour analyse"""
        frames = []
        cap = cv2.VideoCapture(h264_file)
        
        frame_count = 0
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Conversion en YUV pour analyse
            yuv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            frames.append(yuv_frame)
            frame_count += 1
            
            if frame_count % 20 == 0:
                print(f"   Chargé {frame_count} frames...")
        
        cap.release()
        self.frame_cache = frames
        print(f"   ✅ {len(frames)} frames chargées")
        return frames
    
    def _analyze_blocking_artifacts(self, frames: List[np.ndarray]) -> Dict:
        """Détection artefacts de blocs 8×8/16×16"""
        print("   🔍 Analyse blocking artifacts...")
        
        if not frames:
            return {'error': 'Pas de frames'}
        
        block_scores = []
        
        for i, frame in enumerate(frames[:20]):  # Analyse sur 20 frames max
            y_channel = frame[:, :, 0]  # Canal Y (luminance)
            
            # Détection de grilles 8×8 et 16×16
            block_8_score = self._detect_block_grid(y_channel, 8)
            block_16_score = self._detect_block_grid(y_channel, 16)
            
            block_scores.append({
                'frame': i,
                'block_8_score': block_8_score,
                'block_16_score': block_16_score,
                'combined_score': (block_8_score + block_16_score) / 2
            })
        
        avg_block_score = np.mean([s['combined_score'] for s in block_scores])
        
        # Classification niveau d'artefacts
        if avg_block_score > 0.7:
            level = 'ÉLEVÉ'
            hcv16_gain = 0.15  # 15% gain potentiel
        elif avg_block_score > 0.4:
            level = 'MODÉRÉ'
            hcv16_gain = 0.08  # 8% gain potentiel
        else:
            level = 'FAIBLE'
            hcv16_gain = 0.03  # 3% gain potentiel
        
        return {
            'average_score': avg_block_score,
            'level': level,
            'hcv16_gain_potential': hcv16_gain,
            'frame_scores': block_scores,
            'exploitability': 'HAUTE' if avg_block_score > 0.5 else 'MOYENNE'
        }
    
    def _detect_block_grid(self, image: np.ndarray, block_size: int) -> float:
        """Détection de grille de blocs de taille donnée"""
        h, w = image.shape
        
        # Calcul des différences aux frontières de blocs
        vertical_diffs = []
        horizontal_diffs = []
        
        # Frontières verticales
        for x in range(block_size, w, block_size):
            if x < w - 1:
                diff = np.mean(np.abs(image[:, x].astype(int) - image[:, x-1].astype(int)))
                vertical_diffs.append(diff)
        
        # Frontières horizontales
        for y in range(block_size, h, block_size):
            if y < h - 1:
                diff = np.mean(np.abs(image[y, :].astype(int) - image[y-1, :].astype(int)))
                horizontal_diffs.append(diff)
        
        # Score basé sur la régularité des différences
        if vertical_diffs and horizontal_diffs:
            avg_vertical = np.mean(vertical_diffs)
            avg_horizontal = np.mean(horizontal_diffs)
            
            # Normalisation (0-1)
            score = min(1.0, (avg_vertical + avg_horizontal) / 50.0)
            return score
        
        return 0.0
    
    def _analyze_motion_residuals(self, frames: List[np.ndarray]) -> Dict:
        """Analyse des résidus de compensation de mouvement"""
        print("   🔍 Analyse motion residuals...")
        
        if len(frames) < 2:
            return {'error': 'Pas assez de frames'}
        
        residual_patterns = []
        
        for i in range(1, min(len(frames), 21)):  # Analyse sur 20 frames max
            prev_frame = frames[i-1][:, :, 0]  # Y channel
            curr_frame = frames[i][:, :, 0]
            
            # Calcul résidu simple (différence inter-frame)
            residual = np.abs(curr_frame.astype(int) - prev_frame.astype(int))
            
            # Analyse patterns dans résidu
            pattern_score = self._analyze_residual_patterns(residual)
            
            residual_patterns.append({
                'frame_pair': f"{i-1}-{i}",
                'mean_residual': np.mean(residual),
                'pattern_score': pattern_score,
                'predictability': 1.0 - (np.std(residual) / (np.mean(residual) + 1e-6))
            })
        
        avg_predictability = np.mean([p['predictability'] for p in residual_patterns])
        avg_pattern_score = np.mean([p['pattern_score'] for p in residual_patterns])
        
        # Estimation gain HCV16
        if avg_predictability > 0.7 and avg_pattern_score > 0.6:
            level = 'ÉLEVÉ'
            hcv16_gain = 0.20  # 20% gain
        elif avg_predictability > 0.5:
            level = 'MODÉRÉ'
            hcv16_gain = 0.12  # 12% gain
        else:
            level = 'FAIBLE'
            hcv16_gain = 0.05  # 5% gain
        
        return {
            'average_predictability': avg_predictability,
            'average_pattern_score': avg_pattern_score,
            'level': level,
            'hcv16_gain_potential': hcv16_gain,
            'frame_analysis': residual_patterns,
            'exploitability': 'HAUTE' if avg_predictability > 0.6 else 'MOYENNE'
        }
    
    def _analyze_residual_patterns(self, residual: np.ndarray) -> float:
        """Analyse patterns dans résidus de mouvement"""
        # Détection de patterns réguliers dans les résidus
        
        # 1. Analyse fréquentielle simple
        fft_residual = np.fft.fft2(residual)
        fft_magnitude = np.abs(fft_residual)
        
        # 2. Détection de pics réguliers
        h, w = fft_magnitude.shape
        center_h, center_w = h // 2, w // 2
        
        # Analyse quadrants pour détecter régularité
        quadrants = [
            fft_magnitude[:center_h, :center_w],
            fft_magnitude[:center_h, center_w:],
            fft_magnitude[center_h:, :center_w],
            fft_magnitude[center_h:, center_w:]
        ]
        
        # Score basé sur la similarité des quadrants
        similarities = []
        for i in range(len(quadrants)):
            for j in range(i+1, len(quadrants)):
                if quadrants[i].shape == quadrants[j].shape:
                    corr = np.corrcoef(quadrants[i].flatten(), quadrants[j].flatten())[0, 1]
                    if not np.isnan(corr):
                        similarities.append(abs(corr))
        
        pattern_score = np.mean(similarities) if similarities else 0.0
        return min(1.0, pattern_score)
    
    def _analyze_quantization_noise(self, frames: List[np.ndarray]) -> Dict:
        """Analyse du bruit de quantification"""
        print("   🔍 Analyse quantization noise...")
        
        if not frames:
            return {'error': 'Pas de frames'}
        
        noise_characteristics = []
        
        for i, frame in enumerate(frames[:10]):  # Analyse sur 10 frames
            y_channel = frame[:, :, 0]
            
            # Détection bruit haute fréquence
            noise_level = self._estimate_noise_level(y_channel)
            noise_uniformity = self._analyze_noise_uniformity(y_channel)
            
            noise_characteristics.append({
                'frame': i,
                'noise_level': noise_level,
                'uniformity': noise_uniformity
            })
        
        avg_noise_level = np.mean([n['noise_level'] for n in noise_characteristics])
        avg_uniformity = np.mean([n['uniformity'] for n in noise_characteristics])
        
        # Estimation gain HCV16 grain synthesis
        if avg_uniformity > 0.7 and avg_noise_level > 0.3:
            level = 'ÉLEVÉ'
            hcv16_gain = 0.08  # 8% gain
        elif avg_uniformity > 0.5:
            level = 'MODÉRÉ'
            hcv16_gain = 0.05  # 5% gain
        else:
            level = 'FAIBLE'
            hcv16_gain = 0.02  # 2% gain
        
        return {
            'average_noise_level': avg_noise_level,
            'average_uniformity': avg_uniformity,
            'level': level,
            'hcv16_gain_potential': hcv16_gain,
            'grain_synthesis_applicable': avg_uniformity > 0.6,
            'exploitability': 'MOYENNE' if avg_uniformity > 0.5 else 'FAIBLE'
        }
    
    def _estimate_noise_level(self, image: np.ndarray) -> float:
        """Estimation niveau de bruit"""
        # Filtre passe-haut pour isoler le bruit
        kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        high_freq = cv2.filter2D(image.astype(np.float32), -1, kernel)
        
        # Niveau de bruit basé sur variance haute fréquence
        noise_level = np.std(high_freq) / 255.0
        return min(1.0, noise_level)
    
    def _analyze_noise_uniformity(self, image: np.ndarray) -> float:
        """Analyse uniformité du bruit (pour grain synthesis)"""
        h, w = image.shape
        
        # Division en blocs pour analyse locale
        block_size = 32
        block_variances = []
        
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = image[y:y+block_size, x:x+block_size]
                block_variances.append(np.var(block))
        
        # Uniformité basée sur la consistance des variances
        if len(block_variances) > 1:
            uniformity = 1.0 - (np.std(block_variances) / (np.mean(block_variances) + 1e-6))
            return max(0.0, min(1.0, uniformity))
        
        return 0.0
    
    def _analyze_temporal_patterns(self, frames: List[np.ndarray]) -> Dict:
        """Analyse patterns temporels pour GOP optimization"""
        print("   🔍 Analyse temporal patterns...")
        
        if len(frames) < 3:
            return {'error': 'Pas assez de frames'}
        
        temporal_correlations = []
        scene_changes = []
        
        for i in range(2, min(len(frames), 31)):  # Analyse sur 30 frames max
            # Corrélation temporelle
            corr_prev = self._calculate_frame_correlation(frames[i-1], frames[i])
            corr_prev2 = self._calculate_frame_correlation(frames[i-2], frames[i])
            
            temporal_correlations.append({
                'frame': i,
                'correlation_t1': corr_prev,
                'correlation_t2': corr_prev2
            })
            
            # Détection changements de scène
            scene_change = self._detect_scene_change(frames[i-1], frames[i])
            scene_changes.append(scene_change)
        
        avg_correlation = np.mean([t['correlation_t1'] for t in temporal_correlations])
        scene_change_rate = np.mean(scene_changes)
        
        # Recommandation GOP HCV16
        if avg_correlation > 0.8 and scene_change_rate < 0.1:
            recommended_gop = 50
            hcv16_gain = 0.15  # 15% gain avec GOP long
        elif avg_correlation > 0.6:
            recommended_gop = 25
            hcv16_gain = 0.08  # 8% gain
        else:
            recommended_gop = 12
            hcv16_gain = 0.03  # 3% gain
        
        return {
            'average_correlation': avg_correlation,
            'scene_change_rate': scene_change_rate,
            'recommended_gop': recommended_gop,
            'hcv16_gain_potential': hcv16_gain,
            'temporal_stability': 'HAUTE' if avg_correlation > 0.7 else 'MOYENNE'
        }
    
    def _calculate_frame_correlation(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """Calcul corrélation entre deux frames"""
        y1 = frame1[:, :, 0].flatten()
        y2 = frame2[:, :, 0].flatten()
        
        correlation = np.corrcoef(y1, y2)[0, 1]
        return 0.0 if np.isnan(correlation) else abs(correlation)
    
    def _detect_scene_change(self, frame1: np.ndarray, frame2: np.ndarray) -> bool:
        """Détection changement de scène"""
        # Différence moyenne entre frames
        diff = np.mean(np.abs(frame1.astype(int) - frame2.astype(int)))
        
        # Seuil empirique pour changement de scène
        threshold = 30.0
        return diff > threshold  
  
    def _calculate_hcv16_opportunities(self, analyses: Dict) -> Dict:
        """Calcul opportunités globales HCV16"""
        print("   📊 Calcul opportunités HCV16...")
        
        # Extraction gains potentiels
        blocking_gain = analyses['blocking'].get('hcv16_gain_potential', 0)
        motion_gain = analyses['motion'].get('hcv16_gain_potential', 0)
        quantization_gain = analyses['quantization'].get('hcv16_gain_potential', 0)
        temporal_gain = analyses['temporal'].get('hcv16_gain_potential', 0)
        
        # Calcul gain total (non-linéaire)
        # Les gains ne s'additionnent pas directement
        total_gain = 1.0
        total_gain *= (1.0 + blocking_gain)
        total_gain *= (1.0 + motion_gain)
        total_gain *= (1.0 + quantization_gain)
        total_gain *= (1.0 + temporal_gain)
        
        compression_ratio = total_gain
        
        # Classification opportunité
        if compression_ratio >= 1.15:
            opportunity_level = 'EXCELLENTE'
        elif compression_ratio >= 1.08:
            opportunity_level = 'BONNE'
        elif compression_ratio >= 1.03:
            opportunity_level = 'MODÉRÉE'
        else:
            opportunity_level = 'FAIBLE'
        
        return {
            'estimated_compression_ratio': compression_ratio,
            'opportunity_level': opportunity_level,
            'individual_gains': {
                'blocking_artifacts': blocking_gain,
                'motion_residuals': motion_gain,
                'quantization_noise': quantization_gain,
                'temporal_patterns': temporal_gain
            },
            'recommended_strategy': self._recommend_strategy(compression_ratio, analyses),
            'poc_feasibility': compression_ratio >= 1.02
        }
    
    def _recommend_strategy(self, ratio: float, analyses: Dict) -> str:
        """Recommandation stratégie basée sur analyse"""
        if ratio >= 1.15:
            return "Décodage Partiel + HCV16 + GOP optimisé"
        elif ratio >= 1.08:
            return "Décodage Partiel + HCV16"
        elif ratio >= 1.03:
            return "Analyse Bitstream + Repackaging"
        else:
            return "Hybrid Container (gains limités)"
    
    def generate_report(self) -> str:
        """Génération rapport d'analyse"""
        if not self.analysis_results:
            return "Aucune analyse disponible"
        
        results = self.analysis_results
        
        report = f"""
🔍 RAPPORT ANALYSE H.264 → HCV16
{'='*50}

📊 INFORMATIONS FICHIER:
   Taille: {results['file_info'].get('file_size_mb', 0):.1f} MB
   Résolution: {results['file_info'].get('width', 0)}×{results['file_info'].get('height', 0)}
   Durée: {results['file_info'].get('duration_sec', 0):.1f}s
   Frames analysées: {results['frames_analyzed']}

🎯 ARTEFACTS DÉTECTÉS:
   Blocking artifacts: {results['blocking_artifacts']['level']} ({results['blocking_artifacts']['hcv16_gain_potential']*100:.1f}% gain)
   Motion residuals: {results['motion_residuals']['level']} ({results['motion_residuals']['hcv16_gain_potential']*100:.1f}% gain)
   Quantization noise: {results['quantization_noise']['level']} ({results['quantization_noise']['hcv16_gain_potential']*100:.1f}% gain)
   Temporal patterns: {results['temporal_patterns']['temporal_stability']} ({results['temporal_patterns']['hcv16_gain_potential']*100:.1f}% gain)

🚀 OPPORTUNITÉ HCV16:
   Ratio estimé: {results['hcv16_opportunities']['estimated_compression_ratio']:.3f}×
   Niveau: {results['hcv16_opportunities']['opportunity_level']}
   Stratégie recommandée: {results['hcv16_opportunities']['recommended_strategy']}
   POC faisable: {'✅ OUI' if results['hcv16_opportunities']['poc_feasibility'] else '❌ NON'}

💰 IMPACT BUSINESS:
   Économie potentielle: {((results['hcv16_opportunities']['estimated_compression_ratio'] - 1) * 100):.1f}%
   
📈 RECOMMANDATIONS:
   - GOP recommandé: {results['temporal_patterns'].get('recommended_gop', 'N/A')}
   - Grain synthesis: {'Applicable' if results['quantization_noise'].get('grain_synthesis_applicable', False) else 'Non applicable'}
   - Priorité développement: {'HAUTE' if results['hcv16_opportunities']['estimated_compression_ratio'] >= 1.05 else 'MOYENNE'}
"""
        
        return report