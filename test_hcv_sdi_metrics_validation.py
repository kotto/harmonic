#!/usr/bin/env python3
"""
Test de validation directe des métriques HCV SDI
Vérifie les ratios de compression annoncés et les métriques de qualité
"""

import numpy as np
import cv2
import json
import time
import zstandard as zstd
from pathlib import Path
import hashlib

class HCVSDIValidator:
    def __init__(self):
        self.modes = {
            'fast': {'zstd_level': 3, 'expected_ratio': 9.56},
            'sdi': {'zstd_level': 11, 'expected_ratio': 11.85}, 
            'archive': {'zstd_level': 19, 'expected_ratio': 16.19}
        }
        
    def generate_test_sdi_signal(self, width=1920, height=1080, frames=50):
        """Génère un signal SDI synthétique YCbCr 4:2:2 10 bits"""
        print(f"Génération signal SDI test: {width}x{height}, {frames} frames")
        
        # Simulation signal broadcast typique
        video_data = []
        
        for frame_idx in range(frames):
            # Génération frame YCbCr avec caractéristiques broadcast
            y_channel = np.random.randint(64, 940, (height, width), dtype=np.uint16)  # 10-bit range
            cb_channel = np.random.randint(64, 960, (height//2, width//2), dtype=np.uint16)
            cr_channel = np.random.randint(64, 960, (height//2, width//2), dtype=np.uint16)
            
            # Ajout corrélation spatiale (caractéristique broadcast)
            y_channel = cv2.GaussianBlur(y_channel.astype(np.float32), (5, 5), 1.0).astype(np.uint16)
            
            # Simulation grain capteur
            grain = np.random.normal(0, 2.5, (height, width)).astype(np.int16)
            y_channel = np.clip(y_channel + grain, 64, 940).astype(np.uint16)
            
            frame_data = {
                'y': y_channel,
                'cb': cb_channel, 
                'cr': cr_channel,
                'frame_idx': frame_idx
            }
            video_data.append(frame_data)
            
        return video_data
    
    def calculate_raw_size(self, video_data):
        """Calcule la taille raw SMPTE 2110-20"""
        if not video_data:
            return 0
            
        frame = video_data[0]
        h, w = frame['y'].shape
        
        # YCbCr 4:2:2 10-bit = 20 bits par pixel (2.5 bytes)
        bytes_per_pixel = 2.5
        frame_size = int(w * h * bytes_per_pixel)
        total_size = frame_size * len(video_data)
        
        print(f"Taille raw SMPTE 2110-20: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        return total_size
    
    def compress_hcv_sdi(self, video_data, mode='sdi'):
        """Compression HCV SDI avec séparation signal/grain"""
        print(f"Compression HCV SDI mode: {mode}")
        
        config = self.modes[mode]
        compressor = zstd.ZstdCompressor(level=config['zstd_level'])
        
        compressed_frames = []
        total_compressed_size = 0
        
        for frame in video_data:
            # Séparation signal/grain (simulation)
            y_signal = self.extract_signal_component(frame['y'])
            y_grain = frame['y'] - y_signal
            
            # Prédiction Delta-H sur signal
            y_delta = self.delta_h_prediction(y_signal)
            
            # Compression des composantes
            y_compressed = compressor.compress(y_delta.tobytes())
            cb_compressed = compressor.compress(frame['cb'].tobytes())
            cr_compressed = compressor.compress(frame['cr'].tobytes())
            grain_compressed = compressor.compress(y_grain.tobytes())
            
            frame_compressed = {
                'y_data': y_compressed,
                'cb_data': cb_compressed,
                'cr_data': cr_compressed,
                'grain_data': grain_compressed,
                'original_shape': frame['y'].shape
            }
            
            frame_size = len(y_compressed) + len(cb_compressed) + len(cr_compressed) + len(grain_compressed)
            total_compressed_size += frame_size
            compressed_frames.append(frame_compressed)
            
        print(f"Taille compressée: {total_compressed_size:,} bytes ({total_compressed_size/1024/1024:.2f} MB)")
        return compressed_frames, total_compressed_size
    
    def extract_signal_component(self, y_channel):
        """Extraction composante signal (simulation filtre passe-bas)"""
        return cv2.GaussianBlur(y_channel.astype(np.float32), (3, 3), 0.8).astype(np.uint16)
    
    def delta_h_prediction(self, signal):
        """Prédiction Delta-H horizontale"""
        predicted = np.zeros_like(signal)
        predicted[:, 1:] = signal[:, :-1]  # Prédiction horizontale simple
        delta = signal.astype(np.int32) - predicted.astype(np.int32)
        return delta.astype(np.int16)
    
    def decompress_hcv_sdi(self, compressed_frames):
        """Décompression HCV SDI"""
        print("Décompression HCV SDI...")
        
        decompressor = zstd.ZstdDecompressor()
        reconstructed_frames = []
        
        for comp_frame in compressed_frames:
            # Décompression des composantes
            y_delta_bytes = decompressor.decompress(comp_frame['y_data'])
            cb_bytes = decompressor.decompress(comp_frame['cb_data'])
            cr_bytes = decompressor.decompress(comp_frame['cr_data'])
            grain_bytes = decompressor.decompress(comp_frame['grain_data'])
            
            h, w = comp_frame['original_shape']
            
            # Reconstruction des arrays
            y_delta = np.frombuffer(y_delta_bytes, dtype=np.int16).reshape(h, w)
            cb = np.frombuffer(cb_bytes, dtype=np.uint16).reshape(h//2, w//2)
            cr = np.frombuffer(cr_bytes, dtype=np.uint16).reshape(h//2, w//2)
            y_grain = np.frombuffer(grain_bytes, dtype=np.int16).reshape(h, w)
            
            # Reconstruction inverse Delta-H
            y_signal = self.inverse_delta_h(y_delta)
            
            # Reconstruction Y final
            y_reconstructed = np.clip(y_signal.astype(np.int32) + y_grain.astype(np.int32), 64, 940).astype(np.uint16)
            
            frame_reconstructed = {
                'y': y_reconstructed,
                'cb': cb,
                'cr': cr
            }
            reconstructed_frames.append(frame_reconstructed)
            
        return reconstructed_frames
    
    def inverse_delta_h(self, delta):
        """Reconstruction inverse de la prédiction Delta-H"""
        reconstructed = np.zeros_like(delta, dtype=np.uint16)
        reconstructed[:, 0] = delta[:, 0]  # Premier pixel = delta
        
        for x in range(1, delta.shape[1]):
            reconstructed[:, x] = np.clip(
                reconstructed[:, x-1].astype(np.int32) + delta[:, x].astype(np.int32),
                64, 940
            ).astype(np.uint16)
            
        return reconstructed
    
    def calculate_psnr(self, original, reconstructed):
        """Calcul PSNR entre original et reconstruit"""
        if len(original) != len(reconstructed):
            return 0.0
            
        total_mse = 0.0
        pixel_count = 0
        
        for orig_frame, rec_frame in zip(original, reconstructed):
            # PSNR sur canal Y (luminance)
            mse = np.mean((orig_frame['y'].astype(np.float64) - rec_frame['y'].astype(np.float64)) ** 2)
            total_mse += mse
            pixel_count += orig_frame['y'].size
            
        if total_mse == 0:
            return float('inf')  # Lossless parfait
            
        avg_mse = total_mse / len(original)
        max_val = 940  # 10-bit range max
        psnr = 20 * np.log10(max_val / np.sqrt(avg_mse))
        return psnr
    
    def calculate_ssim(self, original, reconstructed):
        """Calcul SSIM approximatif"""
        if len(original) != len(reconstructed):
            return 0.0
            
        total_ssim = 0.0
        
        for orig_frame, rec_frame in zip(original, reconstructed):
            # Conversion pour SSIM (OpenCV)
            orig_8bit = (orig_frame['y'] / 4).astype(np.uint8)  # 10->8 bit
            rec_8bit = (rec_frame['y'] / 4).astype(np.uint8)
            
            # SSIM simple (corrélation normalisée)
            mean_orig = np.mean(orig_8bit)
            mean_rec = np.mean(rec_8bit)
            
            cov = np.mean((orig_8bit - mean_orig) * (rec_8bit - mean_rec))
            var_orig = np.var(orig_8bit)
            var_rec = np.var(rec_8bit)
            
            if var_orig == 0 and var_rec == 0:
                ssim = 1.0
            else:
                ssim = (2 * mean_orig * mean_rec + 1) * (2 * cov + 1) / \
                       ((mean_orig**2 + mean_rec**2 + 1) * (var_orig + var_rec + 1))
            
            total_ssim += ssim
            
        return total_ssim / len(original)
    
    def validate_lossless(self, original, reconstructed):
        """Validation lossless bit-à-bit"""
        if len(original) != len(reconstructed):
            return False
            
        for orig_frame, rec_frame in zip(original, reconstructed):
            if not np.array_equal(orig_frame['y'], rec_frame['y']):
                return False
            if not np.array_equal(orig_frame['cb'], rec_frame['cb']):
                return False  
            if not np.array_equal(orig_frame['cr'], rec_frame['cr']):
                return False
                
        return True
    
    def run_validation_test(self, width=1920, height=1080, frames=50):
        """Test complet de validation HCV SDI"""
        print("=" * 60)
        print("VALIDATION HCV SDI - TEST DIRECT")
        print("=" * 60)
        
        # Génération signal test
        video_data = self.generate_test_sdi_signal(width, height, frames)
        raw_size = self.calculate_raw_size(video_data)
        
        results = {
            'test_config': {
                'resolution': f"{width}x{height}",
                'frames': frames,
                'raw_size_bytes': raw_size,
                'raw_size_mb': raw_size / 1024 / 1024
            },
            'modes': {}
        }
        
        # Test des 3 modes
        for mode_name, mode_config in self.modes.items():
            print(f"\n--- TEST MODE {mode_name.upper()} ---")
            
            start_time = time.time()
            
            # Compression
            compressed_frames, compressed_size = self.compress_hcv_sdi(video_data, mode_name)
            
            # Décompression
            reconstructed_frames = self.decompress_hcv_sdi(compressed_frames)
            
            # Métriques
            compression_ratio = raw_size / compressed_size
            psnr = self.calculate_psnr(video_data, reconstructed_frames)
            ssim = self.calculate_ssim(video_data, reconstructed_frames)
            is_lossless = self.validate_lossless(video_data, reconstructed_frames)
            
            processing_time = time.time() - start_time
            
            # Résultats
            mode_results = {
                'compressed_size_bytes': compressed_size,
                'compressed_size_mb': compressed_size / 1024 / 1024,
                'compression_ratio': compression_ratio,
                'expected_ratio': mode_config['expected_ratio'],
                'ratio_difference': abs(compression_ratio - mode_config['expected_ratio']),
                'psnr': psnr,
                'ssim': ssim,
                'is_lossless': is_lossless,
                'processing_time_sec': processing_time,
                'storage_reduction_percent': (1 - compressed_size/raw_size) * 100
            }
            
            results['modes'][mode_name] = mode_results
            
            # Affichage résultats
            print(f"Taille compressée: {compressed_size:,} bytes ({compressed_size/1024/1024:.2f} MB)")
            print(f"Ratio mesuré: {compression_ratio:.2f}×")
            print(f"Ratio attendu: {mode_config['expected_ratio']:.2f}×")
            print(f"Écart: {abs(compression_ratio - mode_config['expected_ratio']):.2f}")
            print(f"PSNR: {psnr:.2f} dB")
            print(f"SSIM: {ssim:.6f}")
            print(f"Lossless: {'✓' if is_lossless else '✗'}")
            print(f"Réduction stockage: {(1 - compressed_size/raw_size) * 100:.1f}%")
            print(f"Temps traitement: {processing_time:.2f}s")
            
        return results
    
    def save_results(self, results, filename="hcv_sdi_validation_results.json"):
        """Sauvegarde des résultats"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nRésultats sauvegardés: {filename}")

def main():
    validator = HCVSDIValidator()
    
    # Test avec différentes résolutions
    test_configs = [
        (1920, 1080, 30),  # HD 1080p
        (1280, 720, 30),   # HD 720p  
        (3840, 2160, 10)   # 4K (moins de frames pour la vitesse)
    ]
    
    all_results = {}
    
    for width, height, frames in test_configs:
        print(f"\n{'='*80}")
        print(f"TEST RÉSOLUTION: {width}x{height} - {frames} frames")
        print(f"{'='*80}")
        
        results = validator.run_validation_test(width, height, frames)
        all_results[f"{width}x{height}"] = results
        
        # Analyse des écarts
        print(f"\n--- ANALYSE ÉCARTS RATIOS ---")
        for mode, data in results['modes'].items():
            expected = data['expected_ratio']
            measured = data['compression_ratio']
            diff_percent = (abs(measured - expected) / expected) * 100
            
            status = "✓ CONFORME" if diff_percent < 15 else "⚠ ÉCART IMPORTANT"
            print(f"{mode.upper()}: {measured:.2f}× vs {expected:.2f}× attendu ({diff_percent:.1f}% écart) - {status}")
    
    # Sauvegarde résultats globaux
    validator.save_results(all_results, "hcv_sdi_complete_validation.json")
    
    print(f"\n{'='*80}")
    print("VALIDATION HCV SDI TERMINÉE")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()