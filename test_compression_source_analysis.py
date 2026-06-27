#!/usr/bin/env python3
"""
Test des techniques d'optimisation classiques pour atteindre < 11 MB
"""

import numpy as np
import cv2
from harmonic_codec_v16 import HCV16Writer
import time
import os

def analyze_source_content():
    """Analyse le contenu source pour identifier les optimisations possibles"""
    print("🔍 ANALYSE DU CONTENU SOURCE")
    print("=" * 40)
    
    source_video = "B3.mp4"
    cap = cv2.VideoCapture(source_video)
    
    # Analyse de quelques frames
    frames_to_analyze = 50
    frames = []
    
    for i in range(frames_to_analyze):
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    
    cap.release()
    
    if not frames:
        return None
    
    print(f"📊 Analyse de {len(frames)} frames:")
    
    # 1. Détection de zones statiques
    static_regions = analyze_static_regions(frames)
    print(f"   Zones statiques: {static_regions['percentage']:.1f}%")
    
    # 2. Analyse de la complexité
    complexity = analyze_complexity(frames)
    print(f"   Complexité moyenne: {complexity['score']:.2f}/10")
    print(f"   Détails: {complexity['details']}")
    
    # 3. Détection de patterns répétitifs
    patterns = analyze_patterns(frames)
    print(f"   Patterns répétitifs: {patterns['count']} détectés")
    
    # 4. Analyse de la redondance temporelle
    temporal_redundancy = analyze_temporal_redundancy(frames)
    print(f"   Redondance temporelle: {temporal_redundancy['percentage']:.1f}%")
    
    return {
        'static_regions': static_regions,
        'complexity': complexity,
        'patterns': patterns,
        'temporal_redundancy': temporal_redundancy
    }

def analyze_static_regions(frames):
    """Détecte les zones qui ne bougent pas entre frames"""
    if len(frames) < 2:
        return {'percentage': 0}
    
    total_pixels = frames[0].shape[0] * frames[0].shape[1]
    static_pixels = 0
    
    for i in range(1, min(10, len(frames))):  # Analyse sur 10 frames max
        diff = cv2.absdiff(frames[0], frames[i])
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        static_mask = gray_diff < 10  # Seuil de différence
        static_pixels += np.sum(static_mask)
    
    avg_static = static_pixels / min(9, len(frames) - 1) / total_pixels * 100
    return {'percentage': avg_static}

def analyze_complexity(frames):
    """Analyse la complexité visuelle du contenu"""
    complexities = []
    
    for frame in frames[:10]:  # Analyse sur 10 frames
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calcul de la variance (indicateur de complexité)
        variance = np.var(gray)
        
        # Détection de contours (indicateur de détails)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
        
        # Score de complexité combiné
        complexity_score = min(10, (variance / 1000) + (edge_density * 20))
        complexities.append(complexity_score)
    
    avg_complexity = np.mean(complexities)
    
    if avg_complexity < 3:
        details = "Contenu simple (fond uni, peu de détails)"
    elif avg_complexity < 6:
        details = "Contenu modéré (quelques détails, mouvement limité)"
    else:
        details = "Contenu complexe (beaucoup de détails, mouvement)"
    
    return {'score': avg_complexity, 'details': details}

def analyze_patterns(frames):
    """Détecte les patterns répétitifs dans le contenu"""
    # Analyse simplifiée : détection de blocs similaires
    patterns_found = 0
    
    if len(frames) > 5:
        frame = frames[0]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Découpage en blocs 32x32
        h, w = gray.shape
        block_size = 32
        
        blocks = []
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = gray[y:y+block_size, x:x+block_size]
                blocks.append(block)
        
        # Recherche de blocs similaires (simplifiée)
        for i, block1 in enumerate(blocks):
            for j, block2 in enumerate(blocks[i+1:], i+1):
                if np.mean(np.abs(block1.astype(int) - block2.astype(int))) < 20:
                    patterns_found += 1
                    break
    
    return {'count': patterns_found}

def analyze_temporal_redundancy(frames):
    """Analyse la redondance entre frames consécutives"""
    if len(frames) < 2:
        return {'percentage': 0}
    
    redundancies = []
    
    for i in range(1, min(10, len(frames))):
        diff = cv2.absdiff(frames[i-1], frames[i])
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Pourcentage de pixels identiques (différence < 5)
        similar_pixels = np.sum(gray_diff < 5)
        total_pixels = gray_diff.shape[0] * gray_diff.shape[1]
        redundancy = similar_pixels / total_pixels * 100
        redundancies.append(redundancy)
    
    avg_redundancy = np.mean(redundancies)
    return {'percentage': avg_redundancy}

def test_preprocessing_optimizations():
    """Test des techniques de préprocessing"""
    print("\n🛠️ TEST TECHNIQUES DE PRÉPROCESSING")
    print("=" * 45)
    
    source_video = "B3.mp4"
    test_frames = 20
    
    cap = cv2.VideoCapture(source_video)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Chargement frames originales
    original_frames = []
    for i in range(test_frames):
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_12bit = (frame_rgb.astype(np.uint16) << 4)
        original_frames.append(frame_12bit)
    
    cap.release()
    
    optimizations = [
        {
            'name': 'Original (baseline)',
            'frames': original_frames,
            'description': 'Aucune optimisation'
        },
        {
            'name': 'Débruitage léger',
            'frames': apply_denoising(original_frames, strength=0.3),
            'description': 'Réduction du bruit capteur'
        },
        {
            'name': 'Lissage adaptatif',
            'frames': apply_adaptive_smoothing(original_frames),
            'description': 'Lissage zones homogènes'
        },
        {
            'name': 'Quantification 10-bit',
            'frames': apply_quantization(original_frames, target_bits=10),
            'description': 'Réduction précision couleur'
        },
        {
            'name': 'Optimisation Delta-H',
            'frames': apply_delta_h_optimization(original_frames),
            'description': 'Préparation pour Delta-H'
        }
    ]
    
    results = []
    
    for opt in optimizations:
        print(f"\n🧪 Test: {opt['name']}")
        print(f"   Description: {opt['description']}")
        
        if not opt['frames']:
            print("   ❌ Échec génération frames")
            continue
        
        try:
            output_file = f"test_opt_{len(results)}.hcv16"
            
            params = {
                'path': output_file,
                'mode': 'LOSSLESS',
                'bit_depth': 12,
                'width': width,
                'height': height,
                'fps': (int(fps), 1),
                'colorspace': 'BGR',
                'ref_interval': 120,  # Optimisé
                'seq_id': 42
            }
            
            start_time = time.time()
            writer = HCV16Writer(**params)
            
            for i, frame in enumerate(opt['frames']):
                writer.add_frame(frame, i)
            
            file_size = writer.finalize()
            encoding_time = time.time() - start_time
            
            # Extrapolation
            estimated_full_mb = (file_size / len(opt['frames']) * total_frames) / (1024 * 1024)
            
            result = {
                'name': opt['name'],
                'test_size_mb': file_size / (1024 * 1024),
                'estimated_full_mb': estimated_full_mb,
                'encoding_time': encoding_time,
                'improvement': 0 if len(results) == 0 else ((results[0]['estimated_full_mb'] - estimated_full_mb) / results[0]['estimated_full_mb'] * 100)
            }
            
            results.append(result)
            
            print(f"   Taille test: {result['test_size_mb']:.2f} MB")
            print(f"   Estimation complète: {result['estimated_full_mb']:.1f} MB")
            if result['improvement'] != 0:
                print(f"   Amélioration: {result['improvement']:+.1f}%")
            
            # Nettoyage
            if os.path.exists(output_file):
                os.remove(output_file)
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    return results

def apply_denoising(frames, strength=0.3):
    """Applique un débruitage léger"""
    denoised_frames = []
    for frame in frames:
        # Conversion pour débruitage
        frame_8bit = (frame >> 4).astype(np.uint8)
        
        # Débruitage par canal
        denoised_channels = []
        for c in range(3):
            channel = frame_8bit[:, :, c]
            denoised = cv2.bilateralFilter(channel, 5, int(strength * 50), int(strength * 50))
            denoised_channels.append(denoised)
        
        denoised_8bit = np.stack(denoised_channels, axis=2)
        denoised_12bit = (denoised_8bit.astype(np.uint16) << 4)
        denoised_frames.append(denoised_12bit)
    
    return denoised_frames

def apply_adaptive_smoothing(frames):
    """Applique un lissage adaptatif dans les zones homogènes"""
    smoothed_frames = []
    for frame in frames:
        frame_8bit = (frame >> 4).astype(np.uint8)
        
        # Détection des zones homogènes
        gray = cv2.cvtColor(frame_8bit, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilatation des contours pour protéger les détails
        kernel = np.ones((3,3), np.uint8)
        edges_dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Masque des zones à lisser (inverse des contours)
        smooth_mask = (edges_dilated == 0)
        
        # Lissage conditionnel
        smoothed = frame_8bit.copy()
        for c in range(3):
            channel = frame_8bit[:, :, c]
            smoothed_channel = cv2.GaussianBlur(channel, (3, 3), 0.5)
            smoothed[:, :, c] = np.where(smooth_mask, smoothed_channel, channel)
        
        smoothed_12bit = (smoothed.astype(np.uint16) << 4)
        smoothed_frames.append(smoothed_12bit)
    
    return smoothed_frames

def apply_quantization(frames, target_bits=10):
    """Réduit la précision des couleurs"""
    quantized_frames = []
    shift = 12 - target_bits
    
    for frame in frames:
        # Quantification par décalage de bits
        quantized = (frame >> shift) << shift
        quantized_frames.append(quantized)
    
    return quantized_frames

def apply_delta_h_optimization(frames):
    """Optimise le contenu pour la compression Delta-H"""
    optimized_frames = []
    
    for frame in frames:
        frame_8bit = (frame >> 4).astype(np.uint8)
        
        # Lissage horizontal léger pour améliorer Delta-H
        optimized = frame_8bit.copy()
        for c in range(3):
            channel = frame_8bit[:, :, c]
            # Filtre horizontal léger
            kernel = np.array([[0.1, 0.8, 0.1]])
            smoothed = cv2.filter2D(channel, -1, kernel)
            optimized[:, :, c] = smoothed
        
        optimized_12bit = (optimized.astype(np.uint16) << 4)
        optimized_frames.append(optimized_12bit)
    
    return optimized_frames

def main():
    # Analyse du contenu source
    analysis = analyze_source_content()
    
    if analysis:
        print(f"\n💡 RECOMMANDATIONS BASÉES SUR L'ANALYSE:")
        
        if analysis['static_regions']['percentage'] > 50:
            print("   ✅ Beaucoup de zones statiques → Optimisation inter-frame efficace")
        
        if analysis['complexity']['score'] < 4:
            print("   ✅ Contenu simple → Débruitage et lissage recommandés")
        
        if analysis['temporal_redundancy']['percentage'] > 80:
            print("   ✅ Forte redondance temporelle → Augmenter ref_interval")
    
    # Test des optimisations
    results = test_preprocessing_optimizations()
    
    if results:
        print(f"\n📊 RÉSUMÉ DES OPTIMISATIONS")
        print("=" * 50)
        print(f"{'Technique':<25} {'Taille estimée':<15} {'Amélioration'}")
        print("-" * 55)
        
        for result in results:
            improvement_str = f"{result['improvement']:+.1f}%" if result['improvement'] != 0 else "baseline"
            print(f"{result['name']:<25} {result['estimated_full_mb']:.1f} MB{'':<8} {improvement_str}")
        
        # Meilleure optimisation
        best = min(results[1:], key=lambda x: x['estimated_full_mb']) if len(results) > 1 else None
        if best:
            print(f"\n🏆 MEILLEURE OPTIMISATION:")
            print(f"   Technique: {best['name']}")
            print(f"   Taille: {best['estimated_full_mb']:.1f} MB")
            print(f"   Amélioration: {best['improvement']:+.1f}%")
            
            if best['estimated_full_mb'] < 11.31:
                print(f"   🎉 OBJECTIF ATTEINT !")
            else:
                print(f"   ⚠️  Encore {best['estimated_full_mb'] - 11.31:.1f} MB au-dessus de l'objectif")

if __name__ == "__main__":
    main()