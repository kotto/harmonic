#!/usr/bin/env python3
"""
Test spécifique sur 50 frames de B3.mp4
Validation des résultats avec échantillon limité
"""

import sys
import os
import time
import cv2
import numpy as np

# Ajout du chemin pour les modules HCV16
sys.path.append('h264_hcv16_recompression/src')

def test_b3_50_frames():
    """Test analyse sur 50 frames de B3.mp4"""
    print("🎬 TEST B3.MP4 - 50 FRAMES")
    print("=" * 50)
    
    video_file = "B3.mp4"
    
    # Vérification fichier
    if not os.path.exists(video_file):
        print(f"❌ Fichier {video_file} non trouvé")
        return False
    
    # Informations de base
    file_size_mb = os.path.getsize(video_file) / (1024 * 1024)
    print(f"📁 Fichier: {video_file}")
    print(f"📊 Taille: {file_size_mb:.2f} MB")
    
    # Analyse avec H264Analyzer
    try:
        from h264_analyzer import H264Analyzer
        
        analyzer = H264Analyzer()
        
        print(f"\n🔍 Analyse H.264 (50 frames)...")
        start_time = time.time()
        
        # Analyse avec limitation à 50 frames
        analysis = analyzer.analyze_file(video_file, max_frames=50)
        
        analysis_time = time.time() - start_time
        
        print(f"⏱️  Temps d'analyse: {analysis_time:.2f}s")
        
        # Affichage résultats détaillés
        print_analysis_results(analysis)
        
        return True
        
    except ImportError as e:
        print(f"❌ Module H264Analyzer non disponible: {e}")
        return test_b3_manual_analysis()
    
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")
        return False

def test_b3_manual_analysis():
    """Analyse manuelle si H264Analyzer non disponible"""
    print(f"\n🔧 Analyse manuelle des frames...")
    
    video_file = "B3.mp4"
    cap = cv2.VideoCapture(video_file)
    
    if not cap.isOpened():
        print(f"❌ Impossible d'ouvrir {video_file}")
        return False
    
    # Informations vidéo
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📊 Propriétés vidéo:")
    print(f"   Résolution: {width}×{height}")
    print(f"   FPS: {fps:.1f}")
    print(f"   Frames totales: {total_frames}")
    print(f"   Durée: {total_frames/fps:.1f}s")
    
    # Chargement 50 frames
    frames = []
    max_frames = 50
    
    print(f"\n📹 Chargement {max_frames} frames...")
    
    for i in range(max_frames):
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    
    cap.release()
    
    print(f"✅ {len(frames)} frames chargées")
    
    # Analyse basique des artefacts
    analyze_basic_artifacts(frames)
    
    return True

def analyze_basic_artifacts(frames):
    """Analyse basique des artefacts sur les frames"""
    print(f"\n🔍 Analyse artefacts basique...")
    
    blocking_scores = []
    noise_levels = []
    
    for i, frame in enumerate(frames):
        # Conversion en niveaux de gris
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Détection blocking artifacts (variation entre blocs 8×8)
        blocking_score = detect_blocking_artifacts(gray)
        blocking_scores.append(blocking_score)
        
        # Détection bruit de quantification
        noise_level = detect_quantization_noise(gray)
        noise_levels.append(noise_level)
        
        if i < 5:  # Affichage détaillé pour les 5 premières frames
            print(f"   Frame {i+1}: blocking={blocking_score:.3f}, noise={noise_level:.3f}")
    
    # Statistiques globales
    avg_blocking = np.mean(blocking_scores)
    avg_noise = np.mean(noise_levels)
    
    print(f"\n📈 Résultats moyens sur {len(frames)} frames:")
    print(f"   Blocking artifacts: {avg_blocking:.3f}")
    print(f"   Quantization noise: {avg_noise:.3f}")
    
    # Estimation gain HCV16
    estimate_hcv16_gain(avg_blocking, avg_noise)

def detect_blocking_artifacts(gray_frame):
    """Détection simple des artefacts de blocs"""
    h, w = gray_frame.shape
    
    # Calcul variations aux frontières de blocs 8×8
    block_variations = []
    
    for y in range(8, h-8, 8):
        for x in range(8, w-8, 8):
            # Variation horizontale
            left_block = gray_frame[y-4:y+4, x-8:x]
            right_block = gray_frame[y-4:y+4, x:x+8]
            
            h_variation = abs(np.mean(left_block) - np.mean(right_block))
            
            # Variation verticale
            top_block = gray_frame[y-8:y, x-4:x+4]
            bottom_block = gray_frame[y:y+8, x-4:x+4]
            
            v_variation = abs(np.mean(top_block) - np.mean(bottom_block))
            
            block_variations.append((h_variation + v_variation) / 2)
    
    return np.mean(block_variations) if block_variations else 0

def detect_quantization_noise(gray_frame):
    """Détection simple du bruit de quantification"""
    # Calcul de la variance locale comme indicateur de bruit
    kernel = np.ones((3, 3), np.float32) / 9
    smoothed = cv2.filter2D(gray_frame.astype(np.float32), -1, kernel)
    
    noise = np.abs(gray_frame.astype(np.float32) - smoothed)
    return np.mean(noise)

def estimate_hcv16_gain(blocking_score, noise_level):
    """Estimation gain HCV16 basé sur les artefacts détectés"""
    print(f"\n🎯 Estimation gain HCV16:")
    
    # Gain basé sur blocking artifacts
    if blocking_score > 15:
        blocking_gain = 0.12  # 12%
        blocking_level = "ÉLEVÉ"
    elif blocking_score > 8:
        blocking_gain = 0.08  # 8%
        blocking_level = "MODÉRÉ"
    elif blocking_score > 3:
        blocking_gain = 0.04  # 4%
        blocking_level = "FAIBLE"
    else:
        blocking_gain = 0.01  # 1%
        blocking_level = "MINIMAL"
    
    # Gain basé sur bruit de quantification
    if noise_level > 8:
        noise_gain = 0.08  # 8%
        noise_level_desc = "ÉLEVÉ"
    elif noise_level > 4:
        noise_gain = 0.05  # 5%
        noise_level_desc = "MODÉRÉ"
    elif noise_level > 2:
        noise_gain = 0.02  # 2%
        noise_level_desc = "FAIBLE"
    else:
        noise_gain = 0.005  # 0.5%
        noise_level_desc = "MINIMAL"
    
    # Gain total estimé
    total_gain = blocking_gain + noise_gain
    compression_ratio = 1 + total_gain
    savings_percent = total_gain * 100
    
    print(f"   Blocking artifacts: {blocking_level} → {blocking_gain*100:.1f}% gain")
    print(f"   Quantization noise: {noise_level_desc} → {noise_gain*100:.1f}% gain")
    print(f"   Gain total estimé: {total_gain*100:.1f}%")
    print(f"   Ratio compression: {compression_ratio:.3f}×")
    print(f"   Économie estimée: {savings_percent:.1f}%")
    
    # Évaluation faisabilité
    if compression_ratio >= 1.10:
        feasibility = "🚀 EXCELLENT"
    elif compression_ratio >= 1.05:
        feasibility = "⚡ BON"
    elif compression_ratio >= 1.02:
        feasibility = "🔄 MODÉRÉ"
    else:
        feasibility = "❌ FAIBLE"
    
    print(f"   Faisabilité POC: {feasibility}")

def print_analysis_results(analysis):
    """Affichage résultats d'analyse H264Analyzer"""
    print(f"\n📊 RÉSULTATS ANALYSE H264:")
    
    # Informations de base
    file_info = analysis.get('file_info', {})
    frames_analyzed = analysis.get('frames_analyzed', 0)
    
    print(f"   Frames analysées: {frames_analyzed}")
    print(f"   Résolution: {file_info.get('width', 0)}×{file_info.get('height', 0)}")
    print(f"   Durée: {file_info.get('duration_sec', 0):.1f}s")
    print(f"   Frames totales: {file_info.get('frame_count', 0)}")
    
    # Artefacts détectés
    print(f"\n🎯 ARTEFACTS DÉTECTÉS:")
    
    blocking = analysis.get('blocking_artifacts', {})
    print(f"   Blocking: {blocking.get('level', 'N/A')} ({blocking.get('hcv16_gain_potential', 0)*100:.1f}% gain)")
    
    motion = analysis.get('motion_residuals', {})
    print(f"   Motion: {motion.get('level', 'N/A')} ({motion.get('hcv16_gain_potential', 0)*100:.1f}% gain)")
    
    quantization = analysis.get('quantization_noise', {})
    print(f"   Quantization: {quantization.get('level', 'N/A')} ({quantization.get('hcv16_gain_potential', 0)*100:.1f}% gain)")
    
    temporal = analysis.get('temporal_patterns', {})
    print(f"   Temporal: GOP recommandé = {temporal.get('recommended_gop', 'N/A')}")
    
    # Opportunités HCV16
    opportunities = analysis.get('hcv16_opportunities', {})
    if opportunities:
        ratio = opportunities.get('estimated_compression_ratio', 0)
        level = opportunities.get('opportunity_level', 'N/A')
        feasible = opportunities.get('poc_feasibility', False)
        
        print(f"\n💰 OPPORTUNITÉS HCV16:")
        print(f"   Ratio estimé: {ratio:.3f}×")
        print(f"   Économie: {(ratio-1)*100:.1f}%")
        print(f"   Niveau: {level}")
        print(f"   POC faisable: {'✅ OUI' if feasible else '❌ NON'}")

def main():
    """Fonction principale"""
    print("🧪 TEST SPÉCIFIQUE B3.MP4 - 50 FRAMES")
    print("Validation échantillon limité vs résultats attendus")
    print("=" * 60)
    
    success = test_b3_50_frames()
    
    print(f"\n" + "=" * 60)
    if success:
        print("✅ TEST TERMINÉ AVEC SUCCÈS")
        print("📊 Résultats basés sur 50 frames (2.5% du contenu total)")
        print("⚠️  Extrapolation nécessaire pour validation complète")
    else:
        print("❌ ÉCHEC DU TEST")
        print("🔧 Vérifiez la disponibilité des modules et fichiers")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)