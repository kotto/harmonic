"""
🚀 Point d'Entrée Principal - Phase 1
Application principale pour tester l'amélioration PSNR harmonique
"""

import numpy as np
import time
import sys
import os
from pathlib import Path

# Ajout du chemin src au PYTHONPATH
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from core.harmonic_compression import HarmonicCompressor
from utils.psnr_calculator import PSNRCalculator
from precision.extended_precision import ExtendedPrecision


def create_test_signals():
    """
    Crée des signaux de test variés
    
    Returns:
        Dictionnaire de signaux de test
    """
    np.random.seed(42)
    
    signals = {
        'sine_wave': {
            'signal': np.sin(np.linspace(0, 10*np.pi, 1000)).astype(np.float64),
            'description': 'Onde sinusoïdale pure'
        },
        
        'random_noise': {
            'signal': np.random.randn(1000).astype(np.float64) * 100,
            'description': 'Bruit aléatoire'
        },
        
        'composite': {
            'signal': (
                np.sin(np.linspace(0, 5*np.pi, 1000)) + 
                0.5 * np.sin(np.linspace(0, 20*np.pi, 1000)) +
                np.random.randn(1000) * 0.1
            ).astype(np.float64),
            'description': 'Signal composite (sinusoïdes + bruit)'
        },
        
        'step_function': {
            'signal': np.concatenate([
                np.ones(250) * 10,
                np.ones(250) * 50,
                np.ones(250) * 100,
                np.ones(250) * 25
            ]).astype(np.float64),
            'description': 'Fonction échelon'
        },
        
        'exponential': {
            'signal': np.exp(np.linspace(-5, 5, 1000)).astype(np.float64),
            'description': 'Fonction exponentielle'
        }
    }
    
    return signals


def test_baseline_compression(signals: dict):
    """
    Test la compression de base (baseline)
    
    Args:
        signals: Signaux de test
        
    Returns:
        Résultats du test baseline
    """
    print("🔬 Test de compression baseline (précision standard)")
    print("="*60)
    
    # Compresseur avec précision standard
    compressor_baseline = HarmonicCompressor(precision_bits=64)
    psnr_calc = PSNRCalculator()
    
    baseline_results = {}
    
    for name, data in signals.items():
        signal = data['signal']
        description = data['description']
        
        print(f"\n📊 Test: {name} - {description}")
        
        try:
            # Compression
            start_time = time.time()
            compressed = compressor_baseline.encode(signal)
            encoding_time = time.time() - start_time
            
            # Décompression
            start_time = time.time()
            reconstructed = compressor_baseline.decode(compressed)
            decoding_time = time.time() - start_time
            
            # Qualité
            psnr_result = psnr_calc.calculate_psnr_harmonic(signal, reconstructed)
            
            # Statistiques
            stats = compressor_baseline.get_compression_stats()
            
            baseline_results[name] = {
                'psnr': psnr_result['psnr'],
                'ssim': psnr_result.get('ssim', 0),
                'compression_ratio': stats['compression_ratio'],
                'encoding_time': encoding_time,
                'decoding_time': decoding_time,
                'quality_level': psnr_result['quality_level']
            }
            
            print(f"   PSNR: {psnr_result['psnr']:.2f} dB")
            print(f"   Qualité: {psnr_result['quality_level']}")
            print(f"   Ratio compression: {stats['compression_ratio']:.2f}x")
            print(f"   Temps total: {encoding_time + decoding_time:.4f}s")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            baseline_results[name] = {'error': str(e)}
    
    return baseline_results


def test_phase1_optimization(signals: dict):
    """
    Test l'optimisation Phase 1
    
    Args:
        signals: Signaux de test
        
    Returns:
        Résultats du test Phase 1
    """
    print("\n🚀 Test d'optimisation Phase 1 (précision étendue)")
    print("="*60)
    
    # Compresseur avec précision étendue
    compressor_phase1 = HarmonicCompressor(precision_bits=128)
    psnr_calc = PSNRCalculator()
    
    phase1_results = {}
    
    for name, data in signals.items():
        signal = data['signal']
        description = data['description']
        
        print(f"\n📊 Test: {name} - {description}")
        
        try:
            # Compression
            start_time = time.time()
            compressed = compressor_phase1.encode(signal)
            encoding_time = time.time() - start_time
            
            # Décompression
            start_time = time.time()
            reconstructed = compressor_phase1.decode(compressed)
            decoding_time = time.time() - start_time
            
            # Qualité
            psnr_result = psnr_calc.calculate_psnr_harmonic(signal, reconstructed)
            
            # Statistiques
            stats = compressor_phase1.get_compression_stats()
            
            phase1_results[name] = {
                'psnr': psnr_result['psnr'],
                'ssim': psnr_result.get('ssim', 0),
                'compression_ratio': stats['compression_ratio'],
                'encoding_time': encoding_time,
                'decoding_time': decoding_time,
                'quality_level': psnr_result['quality_level'],
                'harmonic_metrics': psnr_result['harmonic_metrics']
            }
            
            print(f"   PSNR: {psnr_result['psnr']:.2f} dB")
            print(f"   Qualité: {psnr_result['quality_level']}")
            print(f"   Ratio compression: {stats['compression_ratio']:.2f}x")
            print(f"   Temps total: {encoding_time + decoding_time:.4f}s")
            print(f"   Fidélité harmonique: {psnr_result['harmonic_metrics']['harmonic_fidelity']:.4f}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            phase1_results[name] = {'error': str(e)}
    
    return phase1_results


def compare_results(baseline_results: dict, phase1_results: dict):
    """
    Compare les résultats baseline et Phase 1
    
    Args:
        baseline_results: Résultats baseline
        phase1_results: Résultats Phase 1
    """
    print("\n📈 COMPARAISON DES RÉSULTATS")
    print("="*60)
    
    comparison_summary = {
        'psnr_improvements': [],
        'quality_upgrades': [],
        'performance_impact': []
    }
    
    for name in baseline_results.keys():
        if name in phase1_results and 'error' not in baseline_results[name] and 'error' not in phase1_results[name]:
            
            baseline = baseline_results[name]
            phase1 = phase1_results[name]
            
            psnr_improvement = phase1['psnr'] - baseline['psnr']
            time_increase = (phase1['encoding_time'] + phase1['decoding_time']) - (baseline['encoding_time'] + baseline['decoding_time'])
            
            print(f"\n📊 {name}:")
            print(f"   PSNR baseline: {baseline['psnr']:.2f} dB ({baseline['quality_level']})")
            print(f"   PSNR Phase 1: {phase1['psnr']:.2f} dB ({phase1['quality_level']})")
            print(f"   Amélioration PSNR: {psnr_improvement:+.2f} dB")
            print(f"   Impact temps: {time_increase:+.4f}s")
            
            if phase1['psnr'] > baseline['psnr']:
                comparison_summary['psnr_improvements'].append(name)
            
            if phase1['quality_level'] != baseline['quality_level']:
                comparison_summary['quality_upgrades'].append(name)
                print(f"   🎯 Amélioration de qualité: {baseline['quality_level']} → {phase1['quality_level']}")
            
            if time_increase > 0:
                comparison_summary['performance_impact'].append(name)
                print(f"   ⏱️  Surcoût temps: +{time_increase:.4f}s")
    
    # Résumé global
    print(f"\n📊 RÉSUMÉ GLOBAL:")
    print(f"   Signaux testés: {len(baseline_results)}")
    print(f"   Améliorations PSNR: {len(comparison_summary['psnr_improvements'])}")
    print(f"   Améliorations qualité: {len(comparison_summary['quality_upgrades'])}")
    print(f"   Impact performance: {len(comparison_summary['performance_impact'])}")
    
    # Calcul des améliorations moyennes
    if comparison_summary['psnr_improvements']:
        improvements = [phase1_results[name]['psnr'] - baseline_results[name]['psnr'] 
                        for name in comparison_summary['psnr_improvements']]
        avg_improvement = np.mean(improvements)
        max_improvement = np.max(improvements)
        
        print(f"   Amélioration PSNR moyenne: {avg_improvement:+.2f} dB")
        print(f"   Amélioration PSNR maximale: {max_improvement:+.2f} dB")
    
    return comparison_summary


def test_precision_validation():
    """
    Test la validation de la précision
    """
    print("\n🔍 VALIDATION DE LA PRÉCISION")
    print("="*60)
    
    # Test de la précision étendue
    precision_manager = ExtendedPrecision(128)
    
    # Validation des constantes harmoniques
    phi_computed = precision_manager.to_mp((1 + precision_manager.to_mp(5).sqrt()) / 2)
    phi_expected = precision_manager.harmonic_constants['phi']
    
    difference = abs(phi_computed - phi_expected)
    tolerance = precision_manager.to_mp('1e-30')
    
    print(f"📊 Test de précision des constantes harmoniques:")
    print(f"   φ calculé: {phi_computed}")
    print(f"   φ attendu: {phi_expected}")
    print(f"   Différence: {difference}")
    print(f"   Tolérance: {tolerance}")
    
    if difference < tolerance:
        print(f"   ✅ Validation réussie")
    else:
        print(f"   ❌ Validation échouée")
    
    # Test des opérations de précision
    test_values = [1e-15, 1e15, -1e15, 1e-15]
    normal_sum = sum(test_values)
    kahan_sum = precision_manager.to_mp(0)
    compensation = precision_manager.to_mp(0)
    
    for value in test_values:
        mp_value = precision_manager.to_mp(value)
        y = mp_value - compensation
        t = kahan_sum + y
        compensation = (t - kahan_sum) - y
        kahan_sum = t
    
    print(f"\n📊 Test de sommation précise:")
    print(f"   Somme normale: {normal_sum}")
    print(f"   Somme Kahan: {float(kahan_sum)}")
    print(f"   Différence: {abs(normal_sum - float(kahan_sum))}")


def main():
    """
    Fonction principale
    """
    print("🚀 AMÉLIORATION PSNR HARMONIQUE - PHASE 1")
    print("="*60)
    print("Objectif: Améliorer le PSNR de 42dB → 50-54dB")
    print("Méthodes: Précision 128-bit + Optimisation calculs critiques")
    print()
    
    # Création des signaux de test
    print("📊 Création des signaux de test...")
    signals = create_test_signals()
    print(f"   {len(signals)} signaux créés")
    
    # Test baseline
    print("\n" + "="*60)
    baseline_results = test_baseline_compression(signals)
    
    # Test Phase 1
    phase1_results = test_phase1_optimization(signals)
    
    # Comparaison
    comparison = compare_results(baseline_results, phase1_results)
    
    # Validation précision
    test_precision_validation()
    
    # Conclusion
    print("\n🎯 CONCLUSION PHASE 1")
    print("="*60)
    
    if comparison['psnr_improvements']:
        avg_improvement = np.mean([
            phase1_results[name]['psnr'] - baseline_results[name]['psnr']
            for name in comparison['psnr_improvements']
        ])
        
        print(f"✅ Phase 1 réussie!")
        print(f"   Amélioration PSNR moyenne: {avg_improvement:+.2f} dB")
        
        if avg_improvement >= 8:
            print(f"   🎯 Objectif atteint (+8 à +12 dB)")
        elif avg_improvement >= 5:
            print(f"   ⚡ Progression significative (+5 à +8 dB)")
        else:
            print(f"   📈 Progression modérée (< +5 dB)")
        
        print(f"   Signaux améliorés: {len(comparison['psnr_improvements'])}/{len(signals)}")
        
        # Qualité atteinte
        max_psnr = max([r['psnr'] for r in phase1_results.values() if 'psnr' in r])
        print(f"   PSNR maximal atteint: {max_psnr:.2f} dB")
        
        if max_psnr >= 50:
            print(f"   🏆 Objectif PSNR atteint (≥50dB)")
        else:
            print(f"   📈 PSNR en progression vers l'objectif")
    
    else:
        print("❌ Phase 1 nécessite des ajustements")
    
    print(f"\n📊 Prochaines étapes:")
    print(f"   - Phase 2: Base adaptative (+10 à +18 dB)")
    print(f"   - Phase 3: Algorithmes itératifs (+15 à +25 dB)")
    print(f"   - Phase 4: Approches quantiques (+8 à +15 dB)")
    print(f"   - Objectif final: 87-90 dB")
    
    print(f"\n🌊 Phase 1 terminée!")


if __name__ == "__main__":
    main()
