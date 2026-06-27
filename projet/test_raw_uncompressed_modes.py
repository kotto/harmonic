#!/usr/bin/env python3
"""
Test pour signaux RAW non compressés - Modes GRAIN_SYNTH et SIGNAL_ONLY
Validation de la qualité maximale et de la fidélité des signaux
"""

import numpy as np
import json
import time
from pathlib import Path
import cv2

class RawUncompressedTester:
    def __init__(self):
        self.test_results = {}
        self.raw_data = None
        
    def generate_test_signal(self, width=1920, height=1080, frames=10):
        """Génère un signal de test RAW haute qualité"""
        print(f"Génération signal RAW {width}x{height} - {frames} frames")
        
        # Signal de test avec gradients et textures fines
        signal = np.zeros((frames, height, width, 3), dtype=np.float32)
        
        for f in range(frames):
            # Gradient horizontal
            for x in range(width):
                signal[f, :, x, 0] = x / width
            
            # Gradient vertical
            for y in range(height):
                signal[f, y, :, 1] = y / height
            
            # Texture fine avec grain
            noise = np.random.normal(0, 0.01, (height, width))
            signal[f, :, :, 2] = 0.5 + noise
            
            # Animation temporelle
            signal[f] += 0.1 * np.sin(f * 0.5)
        
        self.raw_data = signal
        return signal
    
    def test_grain_synth_mode(self):
        """Test du mode GRAIN_SYNTH pour signaux RAW"""
        print("\n=== TEST MODE GRAIN_SYNTH ===")
        
        if self.raw_data is None:
            self.generate_test_signal()
        
        start_time = time.time()
        
        # Configuration GRAIN_SYNTH
        config = {
            "mode": "GRAIN_SYNTH",
            "compression": "NONE",
            "quality": "LOSSLESS",
            "grain_preservation": True,
            "synthesis_level": "MAXIMUM",
            "temporal_coherence": True
        }
        
        # Simulation du traitement GRAIN_SYNTH
        processed_data = self.simulate_grain_synth_processing(self.raw_data, config)
        
        # Métriques de qualité
        psnr = self.calculate_psnr(self.raw_data, processed_data)
        ssim = self.calculate_ssim(self.raw_data, processed_data)
        grain_fidelity = self.measure_grain_fidelity(self.raw_data, processed_data)
        
        processing_time = time.time() - start_time
        
        results = {
            "mode": "GRAIN_SYNTH",
            "psnr_db": float(psnr),
            "ssim": float(ssim),
            "grain_fidelity": float(grain_fidelity),
            "processing_time": processing_time,
            "data_size": self.raw_data.nbytes,
            "compression_ratio": 1.0,  # Pas de compression
            "quality_score": (psnr + ssim * 100 + grain_fidelity * 50) / 3
        }
        
        self.test_results["grain_synth"] = results
        
        print(f"PSNR: {psnr:.2f} dB")
        print(f"SSIM: {ssim:.4f}")
        print(f"Grain Fidelity: {grain_fidelity:.4f}")
        print(f"Processing Time: {processing_time:.2f}s")
        
        return results
    
    def test_signal_only_mode(self):
        """Test du mode SIGNAL_ONLY pour signaux RAW"""
        print("\n=== TEST MODE SIGNAL_ONLY ===")
        
        if self.raw_data is None:
            self.generate_test_signal()
        
        start_time = time.time()
        
        # Configuration SIGNAL_ONLY
        config = {
            "mode": "SIGNAL_ONLY",
            "compression": "NONE",
            "quality": "PERFECT",
            "signal_purity": True,
            "noise_filtering": False,  # Préservation du signal original
            "bit_depth": 32
        }
        
        # Simulation du traitement SIGNAL_ONLY
        processed_data = self.simulate_signal_only_processing(self.raw_data, config)
        
        # Métriques de qualité
        psnr = self.calculate_psnr(self.raw_data, processed_data)
        ssim = self.calculate_ssim(self.raw_data, processed_data)
        signal_purity = self.measure_signal_purity(self.raw_data, processed_data)
        
        processing_time = time.time() - start_time
        
        results = {
            "mode": "SIGNAL_ONLY",
            "psnr_db": float(psnr),
            "ssim": float(ssim),
            "signal_purity": float(signal_purity),
            "processing_time": processing_time,
            "data_size": self.raw_data.nbytes,
            "compression_ratio": 1.0,  # Pas de compression
            "quality_score": (psnr + ssim * 100 + signal_purity * 60) / 3
        }
        
        self.test_results["signal_only"] = results
        
        print(f"PSNR: {psnr:.2f} dB")
        print(f"SSIM: {ssim:.4f}")
        print(f"Signal Purity: {signal_purity:.4f}")
        print(f"Processing Time: {processing_time:.2f}s")
        
        return results
    
    def simulate_grain_synth_processing(self, data, config):
        """Simule le traitement GRAIN_SYNTH"""
        # Mode GRAIN_SYNTH préserve et synthétise le grain
        processed = data.copy()
        
        # Analyse du grain existant
        grain_pattern = self.extract_grain_pattern(data)
        
        # Synthèse adaptative du grain
        enhanced_grain = self.synthesize_grain(grain_pattern, data.shape)
        
        # Application du grain synthétisé
        processed = processed * 0.98 + enhanced_grain * 0.02
        
        return processed
    
    def simulate_signal_only_processing(self, data, config):
        """Simule le traitement SIGNAL_ONLY"""
        # Mode SIGNAL_ONLY préserve uniquement le signal pur
        processed = data.copy()
        
        # Préservation parfaite du signal (pas de modification)
        # En mode RAW non compressé, le signal reste identique
        
        return processed
    
    def extract_grain_pattern(self, data):
        """Extrait le pattern de grain du signal"""
        # Analyse fréquentielle pour identifier le grain
        grain = np.zeros_like(data)
        
        for f in range(data.shape[0]):
            for c in range(data.shape[3]):
                frame = data[f, :, :, c]
                # Filtre passe-haut pour isoler le grain
                kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
                grain[f, :, :, c] = cv2.filter2D(frame, -1, kernel)
        
        return grain
    
    def synthesize_grain(self, pattern, shape):
        """Synthétise un grain adaptatif"""
        # Génération de grain basée sur le pattern analysé
        synthetic_grain = np.random.normal(0, 0.005, shape)
        
        # Modulation par le pattern existant
        grain_strength = np.std(pattern, axis=(1, 2, 3), keepdims=True)
        synthetic_grain *= grain_strength
        
        return synthetic_grain
    
    def calculate_psnr(self, original, processed):
        """Calcule le PSNR entre signaux"""
        mse = np.mean((original - processed) ** 2)
        if mse == 0:
            return float('inf')
        
        max_val = np.max(original)
        psnr = 20 * np.log10(max_val / np.sqrt(mse))
        return psnr
    
    def calculate_ssim(self, original, processed):
        """Calcule le SSIM moyen"""
        ssim_values = []
        
        for f in range(original.shape[0]):
            for c in range(original.shape[3]):
                # Conversion en uint8 pour SSIM
                orig_frame = (original[f, :, :, c] * 255).astype(np.uint8)
                proc_frame = (processed[f, :, :, c] * 255).astype(np.uint8)
                
                # SSIM simplifié
                mean_orig = np.mean(orig_frame)
                mean_proc = np.mean(proc_frame)
                var_orig = np.var(orig_frame)
                var_proc = np.var(proc_frame)
                cov = np.mean((orig_frame - mean_orig) * (proc_frame - mean_proc))
                
                c1, c2 = 0.01**2, 0.03**2
                ssim = ((2*mean_orig*mean_proc + c1) * (2*cov + c2)) / \
                       ((mean_orig**2 + mean_proc**2 + c1) * (var_orig + var_proc + c2))
                
                ssim_values.append(ssim)
        
        return np.mean(ssim_values)
    
    def measure_grain_fidelity(self, original, processed):
        """Mesure la fidélité du grain"""
        orig_grain = self.extract_grain_pattern(original)
        proc_grain = self.extract_grain_pattern(processed)
        
        # Corrélation entre patterns de grain
        correlation = np.corrcoef(orig_grain.flatten(), proc_grain.flatten())[0, 1]
        return abs(correlation)
    
    def measure_signal_purity(self, original, processed):
        """Mesure la pureté du signal"""
        # Différence absolue normalisée
        diff = np.abs(original - processed)
        max_val = np.max(original)
        purity = 1.0 - (np.mean(diff) / max_val)
        return purity
    
    def compare_modes(self):
        """Compare les deux modes"""
        print("\n=== COMPARAISON DES MODES ===")
        
        if "grain_synth" not in self.test_results or "signal_only" not in self.test_results:
            print("Erreur: Tests non effectués")
            return
        
        grain_results = self.test_results["grain_synth"]
        signal_results = self.test_results["signal_only"]
        
        print(f"GRAIN_SYNTH - Quality Score: {grain_results['quality_score']:.2f}")
        print(f"SIGNAL_ONLY - Quality Score: {signal_results['quality_score']:.2f}")
        
        print(f"\nPSNR - GRAIN_SYNTH: {grain_results['psnr_db']:.2f} dB")
        print(f"PSNR - SIGNAL_ONLY: {signal_results['psnr_db']:.2f} dB")
        
        print(f"\nSSIM - GRAIN_SYNTH: {grain_results['ssim']:.4f}")
        print(f"SSIM - SIGNAL_ONLY: {signal_results['ssim']:.4f}")
        
        # Recommandation
        if grain_results['quality_score'] > signal_results['quality_score']:
            print("\nRECOMMANDATION: GRAIN_SYNTH pour ce type de signal")
        else:
            print("\nRECOMMANDATION: SIGNAL_ONLY pour ce type de signal")
    
    def save_results(self, filename="raw_uncompressed_test_results.json"):
        """Sauvegarde les résultats"""
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\nRésultats sauvegardés: {filename}")
    
    def run_complete_test(self):
        """Lance le test complet"""
        print("=== TEST SIGNAUX RAW NON COMPRESSÉS ===")
        print("Modes: GRAIN_SYNTH et SIGNAL_ONLY")
        
        # Génération du signal de test
        self.generate_test_signal()
        
        # Tests des deux modes
        self.test_grain_synth_mode()
        self.test_signal_only_mode()
        
        # Comparaison
        self.compare_modes()
        
        # Sauvegarde
        self.save_results()
        
        return self.test_results

if __name__ == "__main__":
    tester = RawUncompressedTester()
    results = tester.run_complete_test()