#!/usr/bin/env python3
"""
Test HCV SDI sur B3.mp4 - Validation métriques réelles
"""

import cv2
import numpy as np
import json
import time
import zstandard as zstd
from pathlib import Path
import os

class HCVSDIRealValidator:
    def __init__(self):
        self.modes = {
            'fast': {'zstd_level': 3, 'expected_ratio': 9.56},
            'sdi': {'zstd_level': 11, 'expected_ratio': 11.85}, 
            'archive': {'zstd_level': 19, 'expected_ratio': 16.19}
        }
        
    def load_video_frames(self, video_path, max_frames=50):
        """Charge les frames de B3.mp4"""
        print(f"Chargement vidéo: {video_path}")
        
        if not os.path.exists(video_path):
            print(f"❌ Fichier non trouvé: {video_path}")
            return None, None
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Impossible d'ouvrir: {video_path}")
            return None, None
            
        # Propriétés vidéo
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Résolution: {width}x{height}")
        print(f"FPS: {fps}")
        print(f"Frames totales: {frame_count}")
        print(f"Frames à analyser: {min(max_frames, frame_count)}")
        
        video_info = {
            'width': width,
            'height': height,
            'fps': fps,
            'total_frames': frame_count,
            'analyzed_frames': min(max_frames, frame_count)
        }
        
        frames = []
        frame_idx = 0
        
        while frame_idx < max_frames and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Conversion BGR -> YCbCr (simulation 10-bit)
            frame_yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            
            # Simulation 10-bit (8-bit * 4 pour approximer 10-bit range)
            y_channel = frame_yuv[:, :, 0].astype(np.uint16) * 4 + 64  # Range 64-940
            cb_channel = frame_yuv[:, :, 1].astype(np.uint16) * 4 + 64
            cr_channel = frame_yuv[:, :, 2].astype(np.uint16) * 4 + 64
            
            # Sous-échantillonnage chrominance 4:2:2
            cb_422 = cb_channel[::2, ::2]  # Sous-échantillonnage vertical
            cr_422 = cr_channel[::2, ::2]
            
            frame_data = {
                'y': y_channel,
                'cb': cb_422,
                'cr': cr_422,
                'frame_idx': frame_idx
            }
            frames.append(frame_data)
            frame_idx += 1
            
            if frame_idx % 10 == 0:
                print(f"Chargé {frame_idx} frames...")
                
        cap.release()
        print(f"✅ {len(frames)} frames chargées")
        return frames, video_info
    
    def calculate_raw_sdi_size(self, frames, video_info):
        """Calcule la taille raw SDI équivalente"""
        if not frames:
            return 0
            
        # YCbCr 4:2:2 10-bit = 20 bits par pixel = 2.5 bytes
        width = video_info['width']
        height = video_info['height']
        bytes_per_pixel = 2.5
        
        frame_size = int(width * height * bytes_per_pixel)
        total_size = frame_size * len(frames)
        
        print(f"Taille raw SDI calculée: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        return total_size
    
    def analyze_content_characteristics(self, frames):
        """Analyse les caractéristiques du contenu B3"""
        print("\n--- ANALYSE CONTENU B3 ---")
        
        if not frames:
            return {}
            
        # Analyse sur quelques frames représentatives
        sample_frames = frames[::max(1, len(frames)//5)]  # 5 frames échantillons
        
        stats = {
            'entropy_y': [],
            'variance_y': [],
            'edge_density': [],
            'uniform_regions': []
        }
        
        for frame in sample_frames:
            y_data = frame['y']
            
            # Entropie
            hist, _ = np.histogram(y_data.flatten(), bins=256, range=(64, 940))
            hist_norm = hist / np.sum(hist)
            entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
            stats['entropy_y'].append(entropy)
            
            # Variance (complexité)
            variance = np.var(y_data)
            stats['variance_y'].append(variance)
            
            # Détection contours (densité détails)
            y_8bit = (y_data / 4).astype(np.uint8)
            edges = cv2.Canny(y_8bit, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            stats['edge_density'].append(edge_density)
            
            # Régions uniformes (zones compressibles)
            uniform_mask = cv2.GaussianBlur(y_8bit, (5, 5), 1.0)
            uniform_regions = np.sum(np.abs(y_8bit.astype(np.int16) - uniform_mask.astype(np.int16)) < 5) / y_8bit.size
            stats['uniform_regions'].append(uniform_regions)
        
        # Moyennes
        analysis = {
            'avg_entropy': np.mean(stats['entropy_y']),
            'avg_variance': np.mean(stats['variance_y']),
            'avg_edge_density': np.mean(stats['edge_density']),
            'avg_uniform_regions': np.mean(stats['uniform_regions']),
            'compressibility_score': np.mean(stats['uniform_regions']) * (8.0 - np.mean(stats['entropy_y']))
        }
        
        print(f"Entropie moyenne: {analysis['avg_entropy']:.2f} bits/symbole")
        print(f"Variance moyenne: {analysis['avg_variance']:.0f}")
        print(f"Densité contours: {analysis['avg_edge_density']:.3f}")
        print(f"Régions uniformes: {analysis['avg_uniform_regions']:.3f}")
        print(f"Score compressibilité: {analysis['compressibility_score']:.2f}")
        
        return analysis
    
    def compress_hcv_sdi_real(self, frames, mode='sdi'):
        """Compression HCV SDI réaliste sur B3"""
        print(f"\n--- COMPRESSION HCV SDI MODE {mode.upper()} ---")
        
        config = self.modes[mode]
        compressor = zstd.ZstdCompressor(level=config['zstd_level'])
        
        # Header HCV
        header_data = {
            'version': 'HCV16',
            'mode': mode,
            'frames': len(frames),
            'resolution': f"{frames[0]['y'].shape[1]}x{frames[0]['y'].shape[0]}",
            'grain_model': np.random.bytes(256)  # Modèle grain simulé
        }
        header_compressed = compressor.compress(json.dumps({k: v for k, v in header_data.items() if k != 'grain_model'}).encode())
        
        total_size = len(header_compressed) + 256  # Header + grain model
        
        compressed_frames = []
        
        for i, frame in enumerate(frames):
            # Séparation signal/grain
            y_signal = cv2.GaussianBlur(frame['y'].astype(np.float32), (3, 3), 0.8).astype(np.uint16)
            y_grain = frame['y'].astype(np.int16) - y_signal.astype(np.int16)
            
            # Prédiction temporelle si possible
            if i > 0:
                prev_signal = cv2.GaussianBlur(frames[i-1]['y'].astype(np.float32), (3, 3), 0.8).astype(np.uint16)
                y_predicted = y_signal.astype(np.int16) - prev_signal.astype(np.int16)
            else:
                # Prédiction spatiale
                y_predicted = np.zeros_like(y_signal, dtype=np.int16)
                y_predicted[:, 1:] = y_signal[:, 1:].astype(np.int16) - y_signal[:, :-1].astype(np.int16)
            
            # Compression des composantes
            y_compressed = compressor.compress(y_predicted.tobytes())
            cb_compressed = compressor.compress(frame['cb'].tobytes())
            cr_compressed = compressor.compress(frame['cr'].tobytes())
            grain_compressed = compressor.compress(y_grain.tobytes())
            
            frame_size = len(y_compressed) + len(cb_compressed) + len(cr_compressed) + len(grain_compressed)
            total_size += frame_size
            
            compressed_frames.append({
                'y_size': len(y_compressed),
                'cb_size': len(cb_compressed),
                'cr_size': len(cr_compressed),
                'grain_size': len(grain_compressed),
                'total_size': frame_size
            })
            
            if (i + 1) % 10 == 0:
                print(f"Compressé {i + 1}/{len(frames)} frames...")
        
        print(f"Taille totale compressée: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        return total_size, compressed_frames
    
    def calculate_metrics(self, raw_size, compressed_size, mode):
        """Calcule les métriques finales"""
        ratio = raw_size / compressed_size if compressed_size > 0 else 0
        expected = self.modes[mode]['expected_ratio']
        reduction = (1 - compressed_size / raw_size) * 100
        
        return {
            'compression_ratio': ratio,
            'expected_ratio': expected,
            'ratio_achievement': (ratio / expected) * 100 if expected > 0 else 0,
            'storage_reduction_percent': reduction,
            'size_mb_original': raw_size / 1024 / 1024,
            'size_mb_compressed': compressed_size / 1024 / 1024
        }
    
    def run_b3_validation(self, max_frames=50):
        """Test complet sur B3.mp4"""
        print("=" * 70)
        print("VALIDATION HCV SDI SUR B3.MP4")
        print("=" * 70)
        
        # Chargement vidéo
        frames, video_info = self.load_video_frames('B3.mp4', max_frames)
        if not frames:
            return None
            
        # Calcul taille raw
        raw_size = self.calculate_raw_sdi_size(frames, video_info)
        
        # Analyse contenu
        content_analysis = self.analyze_content_characteristics(frames)
        
        # Test des 3 modes
        results = {
            'video_info': video_info,
            'content_analysis': content_analysis,
            'raw_size_bytes': raw_size,
            'modes': {}
        }
        
        for mode_name in self.modes.keys():
            start_time = time.time()
            
            compressed_size, frame_details = self.compress_hcv_sdi_real(frames, mode_name)
            metrics = self.calculate_metrics(raw_size, compressed_size, mode_name)
            
            processing_time = time.time() - start_time
            
            results['modes'][mode_name] = {
                **metrics,
                'processing_time_sec': processing_time,
                'frame_details': frame_details[:5]  # Premiers frames pour debug
            }
            
            # Affichage résultats
            print(f"\nRésultats mode {mode_name.upper()}:")
            print(f"  Ratio mesuré: {metrics['compression_ratio']:.2f}×")
            print(f"  Ratio attendu: {metrics['expected_ratio']:.2f}×")
            print(f"  Atteinte objectif: {metrics['ratio_achievement']:.1f}%")
            print(f"  Réduction stockage: {metrics['storage_reduction_percent']:.1f}%")
            print(f"  Temps traitement: {processing_time:.2f}s")
            
            # Évaluation
            if metrics['ratio_achievement'] >= 80:
                status = "✅ CONFORME"
            elif metrics['ratio_achievement'] >= 50:
                status = "⚠️ PARTIEL"
            else:
                status = "❌ NON CONFORME"
            print(f"  Statut: {status}")
        
        return results

def main():
    validator = HCVSDIRealValidator()
    
    # Test avec différents nombres de frames
    frame_counts = [10, 30, 50]
    
    all_results = {}
    
    for frame_count in frame_counts:
        print(f"\n{'='*80}")
        print(f"TEST B3.MP4 - {frame_count} FRAMES")
        print(f"{'='*80}")
        
        results = validator.run_b3_validation(frame_count)
        if results:
            all_results[f"{frame_count}_frames"] = results
            
            # Analyse comparative
            print(f"\n--- ANALYSE COMPARATIVE {frame_count} FRAMES ---")
            for mode, data in results['modes'].items():
                ratio = data['compression_ratio']
                expected = data['expected_ratio']
                achievement = data['ratio_achievement']
                
                if achievement >= 80:
                    verdict = "✅ Objectif atteint"
                elif achievement >= 50:
                    verdict = "⚠️ Objectif partiellement atteint"
                else:
                    verdict = "❌ Objectif non atteint"
                    
                print(f"{mode.upper()}: {ratio:.2f}× ({achievement:.1f}%) - {verdict}")
    
    # Sauvegarde résultats
    if all_results:
        with open('b3_hcv_sdi_validation_results.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n✅ Résultats sauvegardés: b3_hcv_sdi_validation_results.json")
        
        # Conclusion générale
        print(f"\n{'='*80}")
        print("CONCLUSION GÉNÉRALE SUR B3.MP4")
        print(f"{'='*80}")
        
        # Analyse du contenu
        if '30_frames' in all_results:
            content = all_results['30_frames']['content_analysis']
            print(f"Caractéristiques contenu B3:")
            print(f"  - Entropie: {content['avg_entropy']:.2f} bits/symbole")
            print(f"  - Score compressibilité: {content['compressibility_score']:.2f}")
            
            if content['compressibility_score'] > 2.0:
                print("  → Contenu favorable à la compression HCV SDI")
            else:
                print("  → Contenu difficile pour la compression HCV SDI")

if __name__ == "__main__":
    main()