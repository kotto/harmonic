#!/usr/bin/env python3
"""
Test B3.mp4 avec stratégie d'échantillonnage avancée
Analyse représentative sur toute la durée de la vidéo
"""

import sys
import os
import time
import cv2
import numpy as np

# Ajout du chemin pour les modules HCV16
sys.path.append('h264_hcv16_recompression/src')

def test_b3_sampling_strategy():
    """Test avec échantillonnage stratégique sur B3.mp4"""
    print("🎬 TEST B3.MP4 - ÉCHANTILLONNAGE STRATÉGIQUE")
    print("=" * 60)
    
    video_file = "B3.mp4"
    
    if not os.path.exists(video_file):
        print(f"❌ Fichier {video_file} non trouvé")
        return False
    
    # Informations de base
    cap = cv2.VideoCapture(video_file)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps
    
    print(f"📁 Fichier: {video_file}")
    print(f"📊 Frames totales: {total_frames}")
    print(f"📊 Durée: {duration:.1f}s")
    print(f"📊 FPS: {fps:.1f}")
    
    cap.release()
    
    # Stratégies d'échantillonnage
    strategies = [
        ("Début seulement", test_beginning_frames, 50),
        ("Échantillonnage uniforme", test_uniform_sampling, 100),
        ("Segments représentatifs", test_segment_sampling, 150),
        ("Analyse complète", test_full_analysis, 500)
    ]
    
    results = []
    
    for strategy_name, test_func, frame_count in strategies:
        print(f"\n{'='*20} {strategy_name} {'='*20}")
        print(f"🎯 Analyse de {frame_count} frames...")
        
        start_time = time.time()
        result = test_func(video_file, frame_count, total_frames)
        analysis_time = time.time() - start_time
        
        if result:
            result['strategy'] = strategy_name
            result['analysis_time'] = analysis_time
            result['frames_analyzed'] = frame_count
            results.append(result)
            
            print(f"⏱️  Temps: {analysis_time:.1f}s")
            print(f"📊 Ratio: {result['compression_ratio']:.3f}×")
            print(f"💰 Économie: {result['savings_percent']:.1f}%")
    
    # Comparaison des résultats
    compare_strategies(results)
    
    return len(results) > 0

def test_beginning_frames(video_file, frame_count, total_frames):
    """Test sur les premières frames seulement"""
    try:
        from h264_analyzer import H264Analyzer
        analyzer = H264Analyzer()
        
        # Analyse limitée au début
        analysis = analyzer.analyze_file(video_file, max_frames=frame_count)
        
        opportunities = analysis.get('hcv16_opportunities', {})
        ratio = opportunities.get('estimated_compression_ratio', 1.0)
        
        return {
            'compression_ratio': ratio,
            'savings_percent': (ratio - 1) * 100,
            'sample_type': 'début',
            'coverage_percent': (frame_count / total_frames) * 100
        }
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_uniform_sampling(video_file, frame_count, total_frames):
    """Test avec échantillonnage uniforme sur toute la vidéo"""
    print("   📍 Échantillonnage uniforme sur toute la durée...")
    
    cap = cv2.VideoCapture(video_file)
    
    # Calcul des positions d'échantillonnage
    step = total_frames // frame_count
    sample_positions = [i * step for i in range(frame_count)]
    
    frames = []
    artifacts_data = []
    
    for pos in sample_positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        
        if ret:
            frames.append(frame)
            
            # Analyse rapide des artefacts
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blocking = detect_blocking_simple(gray)
            noise = detect_noise_simple(gray)
            
            artifacts_data.append({
                'position': pos,
                'time_sec': pos / cap.get(cv2.CAP_PROP_FPS),
                'blocking': blocking,
                'noise': noise
            })
    
    cap.release()
    
    # Calcul moyennes
    avg_blocking = np.mean([d['blocking'] for d in artifacts_data])
    avg_noise = np.mean([d['noise'] for d in artifacts_data])
    
    # Estimation gain
    ratio = estimate_compression_ratio(avg_blocking, avg_noise)
    
    print(f"   📊 Positions échantillonnées: {len(sample_positions)}")
    print(f"   📊 Blocking moyen: {avg_blocking:.3f}")
    print(f"   📊 Noise moyen: {avg_noise:.3f}")
    
    return {
        'compression_ratio': ratio,
        'savings_percent': (ratio - 1) * 100,
        'sample_type': 'uniforme',
        'coverage_percent': 100,
        'artifacts_data': artifacts_data,
        'avg_blocking': avg_blocking,
        'avg_noise': avg_noise
    }

def test_segment_sampling(video_file, frame_count, total_frames):
    """Test par segments (début, milieu, fin)"""
    print("   📍 Analyse par segments (début/milieu/fin)...")
    
    cap = cv2.VideoCapture(video_file)
    
    # Définition des segments
    segment_size = frame_count // 3
    segments = [
        ("Début", 0, segment_size),
        ("Milieu", total_frames//2 - segment_size//2, total_frames//2 + segment_size//2),
        ("Fin", total_frames - segment_size, total_frames)
    ]
    
    segment_results = []
    all_artifacts = []
    
    for segment_name, start_frame, end_frame in segments:
        print(f"     🔍 Segment {segment_name}: frames {start_frame}-{end_frame}")
        
        segment_artifacts = []
        frames_analyzed = 0
        
        for frame_pos in range(start_frame, min(end_frame, total_frames), 5):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blocking = detect_blocking_simple(gray)
                noise = detect_noise_simple(gray)
                
                segment_artifacts.append({
                    'blocking': blocking,
                    'noise': noise,
                    'position': frame_pos
                })
                frames_analyzed += 1
        
        if segment_artifacts:
            avg_blocking = np.mean([a['blocking'] for a in segment_artifacts])
            avg_noise = np.mean([a['noise'] for a in segment_artifacts])
            ratio = estimate_compression_ratio(avg_blocking, avg_noise)
            
            segment_results.append({
                'name': segment_name,
                'blocking': avg_blocking,
                'noise': avg_noise,
                'ratio': ratio,
                'frames': frames_analyzed
            })
            
            all_artifacts.extend(segment_artifacts)
            
            print(f"       Ratio: {ratio:.3f}× ({(ratio-1)*100:.1f}%)")
    
    cap.release()
    
    # Moyenne pondérée
    if segment_results:
        total_frames_analyzed = sum(s['frames'] for s in segment_results)
        weighted_ratio = sum(s['ratio'] * s['frames'] for s in segment_results) / total_frames_analyzed
        
        print(f"   📊 Ratio pondéré: {weighted_ratio:.3f}×")
        
        return {
            'compression_ratio': weighted_ratio,
            'savings_percent': (weighted_ratio - 1) * 100,
            'sample_type': 'segments',
            'coverage_percent': 100,
            'segment_results': segment_results,
            'total_frames_analyzed': total_frames_analyzed
        }
    
    return None

def test_full_analysis(video_file, frame_count, total_frames):
    """Analyse plus complète avec plus de frames"""
    print("   📍 Analyse étendue...")
    
    try:
        from h264_analyzer import H264Analyzer
        analyzer = H264Analyzer()
        
        # Analyse avec plus de frames
        analysis = analyzer.analyze_file(video_file, max_frames=frame_count)
        
        opportunities = analysis.get('hcv16_opportunities', {})
        ratio = opportunities.get('estimated_compression_ratio', 1.0)
        
        # Détails supplémentaires
        blocking = analysis.get('blocking_artifacts', {})
        motion = analysis.get('motion_residuals', {})
        quantization = analysis.get('quantization_noise', {})
        
        return {
            'compression_ratio': ratio,
            'savings_percent': (ratio - 1) * 100,
            'sample_type': 'étendue',
            'coverage_percent': (frame_count / total_frames) * 100,
            'blocking_level': blocking.get('level', 'N/A'),
            'motion_level': motion.get('level', 'N/A'),
            'quantization_level': quantization.get('level', 'N/A'),
            'frames_analyzed': analysis.get('frames_analyzed', frame_count)
        }
        
    except Exception as e:
        print(f"❌ Erreur analyse étendue: {e}")
        return None

def detect_blocking_simple(gray_frame):
    """Détection simple blocking artifacts"""
    h, w = gray_frame.shape
    variations = []
    
    # Échantillonnage sur grille 8×8
    for y in range(8, h-8, 16):
        for x in range(8, w-8, 16):
            # Variation aux frontières de blocs
            left = np.mean(gray_frame[y-4:y+4, x-8:x])
            right = np.mean(gray_frame[y-4:y+4, x:x+8])
            top = np.mean(gray_frame[y-8:y, x-4:x+4])
            bottom = np.mean(gray_frame[y:y+8, x-4:x+4])
            
            h_var = abs(left - right)
            v_var = abs(top - bottom)
            variations.append((h_var + v_var) / 2)
    
    return np.mean(variations) if variations else 0

def detect_noise_simple(gray_frame):
    """Détection simple bruit quantification"""
    # Filtre passe-bas
    kernel = np.ones((3, 3), np.float32) / 9
    smoothed = cv2.filter2D(gray_frame.astype(np.float32), -1, kernel)
    
    # Différence = bruit
    noise = np.abs(gray_frame.astype(np.float32) - smoothed)
    return np.mean(noise)

def estimate_compression_ratio(blocking_score, noise_level):
    """Estimation ratio de compression basé sur artefacts"""
    # Gain blocking
    if blocking_score > 15:
        blocking_gain = 0.15
    elif blocking_score > 10:
        blocking_gain = 0.10
    elif blocking_score > 5:
        blocking_gain = 0.06
    else:
        blocking_gain = 0.02
    
    # Gain noise
    if noise_level > 8:
        noise_gain = 0.08
    elif noise_level > 4:
        noise_gain = 0.05
    else:
        noise_gain = 0.02
    
    total_gain = blocking_gain + noise_gain
    return 1 + total_gain

def compare_strategies(results):
    """Comparaison des différentes stratégies"""
    print(f"\n" + "="*60)
    print("📊 COMPARAISON DES STRATÉGIES D'ÉCHANTILLONNAGE")
    print("="*60)
    
    if not results:
        print("❌ Aucun résultat à comparer")
        return
    
    # Tableau comparatif
    print(f"{'Stratégie':<20} {'Frames':<8} {'Temps':<8} {'Ratio':<8} {'Économie':<10} {'Couverture'}")
    print("-" * 70)
    
    for result in results:
        strategy = result['strategy'][:18]
        frames = result['frames_analyzed']
        time_s = f"{result['analysis_time']:.1f}s"
        ratio = f"{result['compression_ratio']:.3f}×"
        savings = f"{result['savings_percent']:.1f}%"
        coverage = f"{result.get('coverage_percent', 0):.0f}%"
        
        print(f"{strategy:<20} {frames:<8} {time_s:<8} {ratio:<8} {savings:<10} {coverage}")
    
    # Analyse des variations
    ratios = [r['compression_ratio'] for r in results]
    savings = [r['savings_percent'] for r in results]
    
    min_ratio = min(ratios)
    max_ratio = max(ratios)
    avg_ratio = np.mean(ratios)
    std_ratio = np.std(ratios)
    
    print(f"\n📈 ANALYSE DES VARIATIONS:")
    print(f"   Ratio min: {min_ratio:.3f}× ({(min_ratio-1)*100:.1f}%)")
    print(f"   Ratio max: {max_ratio:.3f}× ({(max_ratio-1)*100:.1f}%)")
    print(f"   Ratio moyen: {avg_ratio:.3f}× ({(avg_ratio-1)*100:.1f}%)")
    print(f"   Écart-type: {std_ratio:.3f}")
    print(f"   Variation: {((max_ratio-min_ratio)/avg_ratio)*100:.1f}%")
    
    # Recommandations
    print(f"\n🎯 RECOMMANDATIONS:")
    
    if std_ratio < 0.05:
        print("   ✅ Résultats cohérents entre stratégies")
        print("   📊 L'échantillonnage limité semble représentatif")
    elif std_ratio < 0.10:
        print("   ⚠️  Variation modérée entre stratégies")
        print("   📊 Recommandé: analyse sur plus de frames")
    else:
        print("   ❌ Forte variation entre stratégies")
        print("   📊 OBLIGATOIRE: analyse complète nécessaire")
    
    # Estimation fiabilité
    variation_percent = ((max_ratio - min_ratio) / avg_ratio) * 100
    
    if variation_percent < 10:
        reliability = "🟢 ÉLEVÉE"
    elif variation_percent < 25:
        reliability = "🟡 MODÉRÉE"
    else:
        reliability = "🔴 FAIBLE"
    
    print(f"   Fiabilité extrapolation: {reliability}")
    
    # Estimation pour 1967 frames complètes
    print(f"\n🔮 PROJECTION 1967 FRAMES COMPLÈTES:")
    print(f"   Économie estimée: {avg_ratio-1:.1%} ± {std_ratio:.1%}")
    
    file_size_mb = 11.31
    estimated_savings_mb = file_size_mb * (avg_ratio - 1)
    uncertainty_mb = file_size_mb * std_ratio
    
    print(f"   Économie absolue: {estimated_savings_mb:.2f} ± {uncertainty_mb:.2f} MB")
    print(f"   Taille finale: {file_size_mb - estimated_savings_mb:.2f} MB")

def main():
    """Fonction principale"""
    print("🧪 ANALYSE COMPARATIVE B3.MP4")
    print("Validation de la représentativité des échantillons")
    print("=" * 70)
    
    success = test_b3_sampling_strategy()
    
    print(f"\n" + "=" * 70)
    if success:
        print("✅ ANALYSE COMPARATIVE TERMINÉE")
        print("📊 Évaluation de la fiabilité des extrapolations")
    else:
        print("❌ ÉCHEC DE L'ANALYSE COMPARATIVE")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)