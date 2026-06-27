#!/usr/bin/env python3
"""
ANALYSE COMPARATIVE AVEC SYSTÈMES CONCURRENTS
Comparaison de notre système d'optimisation vidéo avec les meilleures solutions du marché
"""

import numpy as np
import cv2
import time
import os
import tempfile
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Tuple
import json

# Notre système
from core.hybrid_video_parameter_optimizer import (
    HybridVideoParameterOptimizer,
    VideoOptimizationTarget
)

# Simulations des systèmes concurrents
class CompetitorSystem:
    """Classe de base pour simuler les systèmes concurrents"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def optimize_video(self, video_path: str, target_quality: str) -> Dict[str, Any]:
        """Simule l'optimisation vidéo du système concurrent"""
        raise NotImplementedError

class H264AVCSystem(CompetitorSystem):
    """Simulateur H.264/AVC (standard industriel)"""
    
    def __init__(self):
        super().__init__("H.264/AVC", "Standard industriel de compression vidéo")
    
    def optimize_video(self, video_path: str, target_quality: str) -> Dict[str, Any]:
        """Simule H.264 avec différents profils"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        original_size = os.path.getsize(video_path)
        cap.release()
        
        # Simulation H.264 selon la qualité
        quality_params = {
            'high': {'crf': 18, 'preset': 'slow', 'ratio': 15},
            'medium': {'crf': 23, 'preset': 'medium', 'ratio': 25},
            'low': {'crf': 28, 'preset': 'fast', 'ratio': 40}
        }
        
        params = quality_params.get(target_quality, quality_params['medium'])
        
        # Simulation des métriques
        compressed_size = original_size / params['ratio']
        processing_time = duration * 0.5  # H.264 est relativement lent
        
        return {
            'system': self.name,
            'target_quality': target_quality,
            'compression_ratio': params['ratio'],
            'original_size_mb': original_size / 1024 / 1024,
            'compressed_size_mb': compressed_size / 1024 / 1024,
            'storage_saving_percent': (1 - 1/params['ratio']) * 100,
            'processing_time': processing_time,
            'fps_capability': fps * 2,  # H.264 peut décoder 2x le temps réel
            'bandwidth_kbps': (compressed_size * 8) / duration / 1024 if duration > 0 else 0,
            'quality_score': 0.85 if target_quality == 'high' else 0.70 if target_quality == 'medium' else 0.55,
            'crf': params['crf'],
            'preset': params['preset']
        }

class H265HEVCSystem(CompetitorSystem):
    """Simulateur H.265/HEVC (nouveau standard)"""
    
    def __init__(self):
        super().__init__("H.265/HEVC", "Nouveau standard haute efficacité")
    
    def optimize_video(self, video_path: str, target_quality: str) -> Dict[str, Any]:
        """Simule H.265 avec meilleure compression"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        original_size = os.path.getsize(video_path)
        cap.release()
        
        # H.265 offre ~50% de compression en plus que H.264
        quality_params = {
            'high': {'crf': 20, 'preset': 'slow', 'ratio': 30},
            'medium': {'crf': 25, 'preset': 'medium', 'ratio': 50},
            'low': {'crf': 30, 'preset': 'fast', 'ratio': 80}
        }
        
        params = quality_params.get(target_quality, quality_params['medium'])
        
        compressed_size = original_size / params['ratio']
        processing_time = duration * 0.8  # H.265 est plus lent à encoder
        
        return {
            'system': self.name,
            'target_quality': target_quality,
            'compression_ratio': params['ratio'],
            'original_size_mb': original_size / 1024 / 1024,
            'compressed_size_mb': compressed_size / 1024 / 1024,
            'storage_saving_percent': (1 - 1/params['ratio']) * 100,
            'processing_time': processing_time,
            'fps_capability': fps * 1.5,  # H.265 est plus lent à décoder
            'bandwidth_kbps': (compressed_size * 8) / duration / 1024 if duration > 0 else 0,
            'quality_score': 0.90 if target_quality == 'high' else 0.75 if target_quality == 'medium' else 0.60,
            'crf': params['crf'],
            'preset': params['preset']
        }

class VP9WebMSystem(CompetitorSystem):
    """Simulateur VP9/WebM (Google)"""
    
    def __init__(self):
        super().__init__("VP9/WebM", "Solution open-source de Google")
    
    def optimize_video(self, video_path: str, target_quality: str) -> Dict[str, Any]:
        """Simule VP9 avec optimisation web"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        original_size = os.path.getsize(video_path)
        cap.release()
        
        # VP9 similaire à H.265 mais optimisé pour web
        quality_params = {
            'high': {'crf': 15, 'target_bitrate': 1000, 'ratio': 35},
            'medium': {'crf': 25, 'target_bitrate': 500, 'ratio': 55},
            'low': {'crf': 35, 'target_bitrate': 250, 'ratio': 85}
        }
        
        params = quality_params.get(target_quality, quality_params['medium'])
        
        compressed_size = original_size / params['ratio']
        processing_time = duration * 0.7  # VP9 est moyennement rapide
        
        return {
            'system': self.name,
            'target_quality': target_quality,
            'compression_ratio': params['ratio'],
            'original_size_mb': original_size / 1024 / 1024,
            'compressed_size_mb': compressed_size / 1024 / 1024,
            'storage_saving_percent': (1 - 1/params['ratio']) * 100,
            'processing_time': processing_time,
            'fps_capability': fps * 1.8,  # Bon décodage web
            'bandwidth_kbps': (compressed_size * 8) / duration / 1024 if duration > 0 else 0,
            'quality_score': 0.88 if target_quality == 'high' else 0.73 if target_quality == 'medium' else 0.58,
            'crf': params['crf'],
            'target_bitrate_kbps': params['target_bitrate']
        }

class AV1System(CompetitorSystem):
    """Simulateur AV1 (dernière génération)"""
    
    def __init__(self):
        super().__init__("AV1", "Dernière génération de codec")
    
    def optimize_video(self, video_path: str, target_quality: str) -> Dict[str, Any]:
        """Simule AV1 avec compression maximale"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        original_size = os.path.getsize(video_path)
        cap.release()
        
        # AV1 offre ~30% de plus que H.265
        quality_params = {
            'high': {'crf': 25, 'preset': 'slow', 'ratio': 45},
            'medium': {'crf': 30, 'preset': 'medium', 'ratio': 70},
            'low': {'crf': 35, 'preset': 'fast', 'ratio': 110}
        }
        
        params = quality_params.get(target_quality, quality_params['medium'])
        
        compressed_size = original_size / params['ratio']
        processing_time = duration * 1.2  # AV1 est très lent à encoder
        
        return {
            'system': self.name,
            'target_quality': target_quality,
            'compression_ratio': params['ratio'],
            'original_size_mb': original_size / 1024 / 1024,
            'compressed_size_mb': compressed_size / 1024 / 1024,
            'storage_saving_percent': (1 - 1/params['ratio']) * 100,
            'processing_time': processing_time,
            'fps_capability': fps * 1.2,  # AV1 est lent à décoder
            'bandwidth_kbps': (compressed_size * 8) / duration / 1024 if duration > 0 else 0,
            'quality_score': 0.92 if target_quality == 'high' else 0.78 if target_quality == 'medium' else 0.65,
            'crf': params['crf'],
            'preset': params['preset']
        }

def create_test_videos_for_comparison() -> Dict[str, str]:
    """Crée des vidéos de test pour la comparaison"""
    videos = {}
    temp_dir = tempfile.mkdtemp(prefix="comparison_test_")
    
    # Vidéo 1: Test standard (basse résolution)
    frames = []
    for i in range(90):  # 3 secondes @ 30fps
        frame = np.random.randint(50, 200, (240, 320, 3), dtype=np.uint8)
        cv2.circle(frame, (160, 120), 30, (255, 255, 255), -1)
        cv2.putText(frame, f"Frame {i+1}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "standard_test.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['standard'] = video_path
    
    # Vidéo 2: Test haute résolution
    frames = []
    for i in range(60):  # 2 secondes @ 30fps
        frame = np.random.randint(0, 256, (720, 1280, 3), dtype=np.uint8)
        # Ajout de détails
        for j in range(10):
            x, y = np.random.randint(0, 1280), np.random.randint(0, 720)
            cv2.circle(frame, (x, y), 5, (255, 255, 255), -1)
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "hd_test.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['hd'] = video_path
    
    return videos

def create_video_from_frames(frames: List[np.ndarray], output_path: str, fps: float):
    """Crée une vidéo à partir de frames"""
    if not frames:
        return
    
    height, width = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    for frame in frames:
        out.write(frame)
    
    out.release()

def run_competitive_analysis() -> Dict[str, Any]:
    """Lance l'analyse comparative complète"""
    print("🏆 ANALYSE COMPARATIVE AVEC SYSTÈMES CONCURRENTS")
    print("=" * 80)
    
    # Création des vidéos de test
    test_videos = create_test_videos_for_comparison()
    print(f"✅ {len(test_videos)} vidéos de test créées")
    
    # Systèmes concurrents
    competitors = [
        H264AVCSystem(),
        H265HEVCSystem(),
        VP9WebMSystem(),
        AV1System()
    ]
    
    # Qualités à tester
    qualities = ['high', 'medium', 'low']
    
    # Résultats
    all_results = {}
    
    # Test de notre système
    print("\n🎯 Test de notre système hybride...")
    our_system = HybridVideoParameterOptimizer(
        optimization_target=VideoOptimizationTarget.BALANCED_VIDEO,
        max_iterations=10
    )
    
    for video_name, video_path in test_videos.items():
        print(f"   📹 Optimisation: {video_name}")
        
        try:
            result = our_system.optimize_video_parameters(video_path, method="grid")
            
            all_results[f"hybrid_{video_name}"] = {
                'system': 'Hybrid Optimization',
                'video_type': video_name,
                'compression_ratio': result.performance_metrics['compression_ratio'],
                'original_size_mb': result.performance_metrics.get('original_size', 0) / 1024 / 1024,
                'compressed_size_mb': result.performance_metrics.get('estimated_compressed_size', 0) / 1024 / 1024,
                'storage_saving_percent': (1 - 1/result.performance_metrics['compression_ratio']) * 100,
                'processing_time': result.performance_metrics['processing_time'],
                'fps_capability': result.performance_metrics['fps_capability'],
                'bandwidth_kbps': result.performance_metrics['bandwidth'],
                'quality_score': result.quality_metrics['spatial_quality'],
                'k_factor': result.best_parameters.k_factor,
                'webp_quality': result.best_parameters.webp_quality
            }
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    our_system.cleanup()
    
    # Test des systèmes concurrents
    print("\n🏆 Test des systèmes concurrents...")
    
    for competitor in competitors:
        print(f"\n   📊 Test: {competitor.name}")
        
        for video_name, video_path in test_videos.items():
            for quality in qualities:
                try:
                    result = competitor.optimize_video(video_path, quality)
                    result['video_type'] = video_name
                    
                    key = f"{competitor.name}_{video_name}_{quality}"
                    all_results[key] = result
                    
                except Exception as e:
                    print(f"      ❌ Erreur {competitor.name} {video_name} {quality}: {e}")
    
    # Nettoyage
    for video_path in test_videos.values():
        try:
            os.remove(video_path)
        except:
            pass
    
    return all_results

def analyze_comparative_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyse les résultats comparatifs"""
    print("\n📊 ANALYSE DES RÉSULTATS COMPARATIFS")
    print("=" * 80)
    
    # Organisation des résultats
    systems_data = {}
    
    for key, result in results.items():
        if 'system' not in result:
            continue
            
        system = result['system']
        if system not in systems_data:
            systems_data[system] = []
        
        systems_data[system].append(result)
    
    # Calcul des moyennes par système
    system_averages = {}
    
    for system, data in systems_data.items():
        if not data:
            continue
        
        avg_ratio = np.mean([r['compression_ratio'] for r in data])
        avg_quality = np.mean([r['quality_score'] for r in data])
        avg_fps = np.mean([r['fps_capability'] for r in data])
        avg_bandwidth = np.mean([r['bandwidth_kbps'] for r in data])
        avg_saving = np.mean([r['storage_saving_percent'] for r in data])
        avg_time = np.mean([r['processing_time'] for r in data])
        
        system_averages[system] = {
            'compression_ratio': avg_ratio,
            'quality_score': avg_quality,
            'fps_capability': avg_fps,
            'bandwidth_kbps': avg_bandwidth,
            'storage_saving_percent': avg_saving,
            'processing_time': avg_time,
            'sample_count': len(data)
        }
    
    # Affichage des résultats
    print("\n🏆 CLASSEMENT DES SYSTÈMES:")
    print("-" * 60)
    
    # Classement par ratio de compression
    print("\n🗜️  PAR RATIO DE COMPRESSION:")
    sorted_by_ratio = sorted(system_averages.items(), key=lambda x: x[1]['compression_ratio'], reverse=True)
    for i, (system, metrics) in enumerate(sorted_by_ratio, 1):
        print(f"   {i}. {system}: {metrics['compression_ratio']:.1f}:1")
    
    # Classement par qualité
    print("\n🎨 PAR QUALITÉ:")
    sorted_by_quality = sorted(system_averages.items(), key=lambda x: x[1]['quality_score'], reverse=True)
    for i, (system, metrics) in enumerate(sorted_by_quality, 1):
        print(f"   {i}. {system}: {metrics['quality_score']:.3f}")
    
    # Classement par performance FPS
    print("\n⚡ PAR PERFORMANCE FPS:")
    sorted_by_fps = sorted(system_averages.items(), key=lambda x: x[1]['fps_capability'], reverse=True)
    for i, (system, metrics) in enumerate(sorted_by_fps, 1):
        print(f"   {i}. {system}: {metrics['fps_capability']:.1f} FPS")
    
    # Classement par bande passante
    print("\n📶 PAR BANDE PASSANTE (plus bas est mieux):")
    sorted_by_bandwidth = sorted(system_averages.items(), key=lambda x: x[1]['bandwidth_kbps'])
    for i, (system, metrics) in enumerate(sorted_by_bandwidth, 1):
        print(f"   {i}. {system}: {metrics['bandwidth_kbps']:.1f} KB/s")
    
    # Classement par temps de traitement
    print("\n⏱️  PAR TEMPS DE TRAITEMENT (plus bas est mieux):")
    sorted_by_time = sorted(system_averages.items(), key=lambda x: x[1]['processing_time'])
    for i, (system, metrics) in enumerate(sorted_by_time, 1):
        print(f"   {i}. {system}: {metrics['processing_time']:.2f}s")
    
    return {
        'systems_data': systems_data,
        'system_averages': system_averages,
        'rankings': {
            'compression': sorted_by_ratio,
            'quality': sorted_by_quality,
            'fps': sorted_by_fps,
            'bandwidth': sorted_by_bandwidth,
            'time': sorted_by_time
        }
    }

def generate_comparative_report(results: Dict[str, Any], analysis: Dict[str, Any]):
    """Génère un rapport visuel comparatif"""
    print("\n📊 GÉNÉRATION DU RAPPORT COMPARATIF")
    print("=" * 80)
    
    try:
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Analyse Comparative des Systèmes d\'Optimisation Vidéo', fontsize=16)
        
        systems = list(analysis['system_averages'].keys())
        
        # Graphique 1: Ratio de compression
        ratios = [analysis['system_averages'][sys]['compression_ratio'] for sys in systems]
        bars = axes[0, 0].bar(systems, ratios, color='skyblue', alpha=0.7)
        axes[0, 0].set_title('Ratio de Compression Moyen')
        axes[0, 0].set_ylabel('Ratio:1')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Ajout des valeurs
        for bar, ratio in zip(bars, ratios):
            axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(ratios)*0.01,
                            f'{ratio:.0f}:1', ha='center', va='bottom', fontsize=8)
        
        # Graphique 2: Qualité
        qualities = [analysis['system_averages'][sys]['quality_score'] for sys in systems]
        axes[0, 1].bar(systems, qualities, color='lightgreen', alpha=0.7)
        axes[0, 1].set_title('Qualité Moyenne')
        axes[0, 1].set_ylabel('Score (0-1)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Graphique 3: Performance FPS
        fps_values = [analysis['system_averages'][sys]['fps_capability'] for sys in systems]
        axes[0, 2].bar(systems, fps_values, color='orange', alpha=0.7)
        axes[0, 2].set_title('Performance FPS Moyenne')
        axes[0, 2].set_ylabel('FPS')
        axes[0, 2].tick_params(axis='x', rotation=45)
        axes[0, 2].axhline(y=30, color='red', linestyle='--', alpha=0.5, label='30 FPS (Real-time)')
        axes[0, 2].legend()
        
        # Graphique 4: Bande passante
        bandwidths = [analysis['system_averages'][sys]['bandwidth_kbps'] for sys in systems]
        axes[1, 0].bar(systems, bandwidths, color='purple', alpha=0.7)
        axes[1, 0].set_title('Bande Passante Moyenne')
        axes[1, 0].set_ylabel('Bandwidth (KB/s)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Graphique 5: Économie de stockage
        savings = [analysis['system_averages'][sys]['storage_saving_percent'] for sys in systems]
        axes[1, 1].bar(systems, savings, color='gold', alpha=0.7)
        axes[1, 1].set_title('Économie Stockage Moyenne')
        axes[1, 1].set_ylabel('Économie (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Graphique 6: Temps de traitement
        times = [analysis['system_averages'][sys]['processing_time'] for sys in systems]
        axes[1, 2].bar(systems, times, color='lightcoral', alpha=0.7)
        axes[1, 2].set_title('Temps Traitement Moyen')
        axes[1, 2].set_ylabel('Temps (s)')
        axes[1, 2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('F:/FINAL/DEFINITIF/hcs_v2-P3/competitive_analysis_report.png', 
                   dpi=150, bbox_inches='tight')
        print("✅ Rapport visuel sauvegardé: competitive_analysis_report.png")
        
    except Exception as e:
        print(f"⚠️ Erreur génération rapport: {e}")

def save_comparative_results(results: Dict[str, Any], analysis: Dict[str, Any]):
    """Sauvegarde les résultats comparatifs"""
    print("\n💾 SAUVEGARDE DES RÉSULTATS COMPARATIFS")
    
    # Conversion des types numpy
    clean_results = {}
    for key, value in results.items():
        if isinstance(value, dict):
            clean_results[key] = {}
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, (np.integer, np.int32, np.int64)):
                    clean_results[key][sub_key] = int(sub_value)
                elif isinstance(sub_value, (np.floating, np.float32, np.float64)):
                    clean_results[key][sub_key] = float(sub_value)
                else:
                    clean_results[key][sub_key] = sub_value
        else:
            clean_results[key] = value
    
    clean_analysis = {}
    for key, value in analysis.items():
        if isinstance(value, dict):
            clean_analysis[key] = {}
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, (np.integer, np.int32, np.int64)):
                    clean_analysis[key][sub_key] = int(sub_value)
                elif isinstance(sub_value, (np.floating, np.float32, np.float64)):
                    clean_analysis[key][sub_key] = float(sub_value)
                else:
                    clean_analysis[key][sub_key] = sub_value
        else:
            clean_analysis[key] = value
    
    # Sauvegarde
    output_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'results': clean_results,
        'analysis': clean_analysis
    }
    
    with open('F:/FINAL/DEFINITIF/hcs_v2-P3/competitive_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("✅ Résultats sauvegardés: competitive_analysis_results.json")

def main():
    """Fonction principale d'analyse comparative"""
    print("🏆 ANALYSE COMPARATIVE AVEC SYSTÈMES CONCURRENTS")
    print("Comparaison de notre système hybride avec les meilleures solutions du marché")
    print("=" * 80)
    
    # Lancement de l'analyse comparative
    results = run_competitive_analysis()
    
    # Analyse des résultats
    analysis = analyze_comparative_results(results)
    
    # Génération du rapport
    generate_comparative_report(results, analysis)
    
    # Sauvegarde des résultats
    save_comparative_results(results, analysis)
    
    print("\n" + "="*80)
    print("🎯 CONCLUSIONS DE L'ANALYSE COMPARATIVE")
    print("="*80)
    
    # Notre système dans les classements
    our_system = analysis['system_averages'].get('Hybrid Optimization', {})
    
    if our_system:
        print(f"\n🏆 NOTRE SYSTÈME HYBRIDE:")
        print(f"   📊 Ratio compression: {our_system['compression_ratio']:.1f}:1")
        print(f"   🎨 Qualité: {our_system['quality_score']:.3f}")
        print(f"   ⚡ Performance FPS: {our_system['fps_capability']:.1f}")
        print(f"   📶 Bande passante: {our_system['bandwidth_kbps']:.1f} KB/s")
        print(f"   💾 Économie stockage: {our_system['storage_saving_percent']:.1f}%")
        print(f"   ⏱️  Temps traitement: {our_system['processing_time']:.2f}s")
        
        # Position dans les classements
        compression_rank = next(i for i, (sys, _) in enumerate(analysis['rankings']['compression'], 1) 
                             if sys == 'Hybrid Optimization')
        quality_rank = next(i for i, (sys, _) in enumerate(analysis['rankings']['quality'], 1) 
                          if sys == 'Hybrid Optimization')
        fps_rank = next(i for i, (sys, _) in enumerate(analysis['rankings']['fps'], 1) 
                       if sys == 'Hybrid Optimization')
        
        print(f"\n🏅 CLASSEMENT DE NOTRE SYSTÈME:")
        print(f"   🗜️  Compression: {compression_rank}/{len(analysis['rankings']['compression'])}")
        print(f"   🎨 Qualité: {quality_rank}/{len(analysis['rankings']['quality'])}")
        print(f"   ⚡ Performance FPS: {fps_rank}/{len(analysis['rankings']['fps'])}")
    
    print("\n✅ Analyse comparative terminée!")
    print("📊 Rapports visuels et détaillés disponibles!")
    print("🏆 Système hybride positionné par rapport à la concurrence!")
    
    return results, analysis

if __name__ == "__main__":
    main()
