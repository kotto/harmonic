#!/usr/bin/env python3
"""
TEST COMPLET DU SYSTÈME HYBRIDE AUDIO+VIDÉO
Tests de compression et décompression multimédias avec métriques détaillées
"""

import numpy as np
import cv2
import os
import tempfile
import time
import matplotlib.pyplot as plt
from typing import Dict, Any, List
import json

from core.hybrid_audio_video_system import (
    HybridAudioVideoSystem,
    MediaType,
    ProcessingMode
)
from core.hybrid_audio_compressor import (
    AudioQualityMode,
    AudioCompressionLevel
)
from core.hybrid_video_parameter_optimizer import VideoOptimizationTarget

def create_test_audio_video_files() -> Dict[str, str]:
    """Crée des fichiers audio et vidéo de test"""
    files = {}
    temp_dir = tempfile.mkdtemp(prefix="av_test_")
    
    print("📹 Création des fichiers de test...")
    
    # Vidéo 1: Animation simple avec audio
    print("   🎬 Création vidéo 'animation_with_audio'...")
    
    # Création des frames vidéo
    frames = []
    for i in range(90):  # 3 secondes @ 30fps
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Fond dégradé animé
        frame[:, :, 0] = np.linspace(0, 255, 320) + int(50 * np.sin(i * 0.1))
        frame[:, :, 1] = np.linspace(255, 0, 320) + int(50 * np.cos(i * 0.1))
        frame[:, :, 2] = 128
        
        # Animation de cercles
        x = int(160 + 60 * np.cos(i * 0.1))
        y = int(120 + 40 * np.sin(i * 0.1))
        cv2.circle(frame, (x, y), 20, (255, 255, 255), -1)
        
        # Texte
        cv2.putText(frame, f"Frame {i+1}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        frames.append(frame)
    
    # Création vidéo temporaire
    temp_video = os.path.join(temp_dir, "animation_temp.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, 30.0, (320, 240))
    for frame in frames:
        out.write(frame)
    out.release()
    
    # Création audio
    sample_rate = 44100
    duration = 3.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Audio complexe avec plusieurs fréquences
    audio_data = (
        0.5 * np.sin(2 * np.pi * 440 * t) +  # La4
        0.3 * np.sin(2 * np.pi * 880 * t) +  # La5 octave
        0.2 * np.sin(2 * np.pi * 220 * t) +  # La3 octave inférieure
        0.1 * np.sin(2 * np.pi * 660 * t)    # Mi4
    )
    
    # Ajout d'enveloppe pour éviter les clics
    envelope = np.ones_like(audio_data)
    fade_samples = int(0.1 * sample_rate)  # 100ms fade
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    audio_data *= envelope
    
    # Sauvegarde audio temporaire
    temp_audio = os.path.join(temp_dir, "audio_temp.wav")
    import scipy.io.wavfile as wavfile
    audio_int16 = np.int16(audio_data * 32767)
    wavfile.write(temp_audio, sample_rate, audio_int16)
    
    # Combinaison vidéo+audio (si moviepy disponible)
    try:
        import moviepy.editor as mp
        
        video_clip = mp.VideoFileClip(temp_video)
        audio_clip = mp.AudioFileClip(temp_audio)
        
        # Ajustement durée
        video_duration = len(frames) / 30.0
        audio_duration = len(audio_data) / sample_rate
        
        if audio_duration < video_duration:
            audio_clip = audio_clip.loop(duration=video_duration)
        elif audio_duration > video_duration:
            audio_clip = audio_clip.subclip(0, video_duration)
        
        final_clip = video_clip.set_audio(audio_clip)
        output_path = os.path.join(temp_dir, "animation_with_audio.mp4")
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', verbose=False, logger=None)
        
        video_clip.close()
        audio_clip.close()
        
        files['animation_with_audio'] = output_path
        
    except ImportError:
        print("   ⚠️ moviepy non disponible, création vidéo sans audio")
        files['animation_with_audio'] = temp_video
    
    # Vidéo 2: Haute résolution
    print("   🎬 Création vidéo 'high_resolution'...")
    
    hd_frames = []
    for i in range(60):  # 2 secondes @ 30fps
        frame = np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8)
        
        # Pattern animé
        for j in range(5):
            x = int(1280/2 + 200 * np.cos(i * 0.1 + j * 1.2))
            y = int(720/2 + 150 * np.sin(i * 0.1 + j * 1.2))
            cv2.circle(frame, (x, y), 30, (255, 255, 255), -1)
        
        hd_frames.append(frame)
    
    hd_video_path = os.path.join(temp_dir, "high_resolution.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(hd_video_path, fourcc, 30.0, (1280, 720))
    for frame in hd_frames:
        out.write(frame)
    out.release()
    
    files['high_resolution'] = hd_video_path
    
    # Audio 3: Musique complexe
    print("   🎵 Création audio 'complex_music'...")
    
    duration_music = 4.0
    t_music = np.linspace(0, duration_music, int(sample_rate * duration_music))
    
    # Simulation de musique avec harmoniques
    base_freq = 261.63  # Do4
    music_data = np.zeros_like(t_music)
    
    # Ajout de plusieurs harmoniques (simulation d'instrument)
    for harmonic in range(1, 8):
        freq = base_freq * harmonic
        amplitude = 1.0 / harmonic  # Harmoniques décroissantes
        music_data += amplitude * np.sin(2 * np.pi * freq * t_music)
    
    # Modulation d'amplitude (vibrato)
    vibrato = 0.1 * np.sin(2 * np.pi * 5 * t_music)  # 5 Hz vibrato
    music_data *= (1 + vibrato)
    
    # Enveloppe ADSR simplifiée
    attack_time = 0.1
    decay_time = 0.2
    sustain_level = 0.7
    release_time = 0.3
    
    adsr = np.ones_like(music_data)
    attack_samples = int(attack_time * sample_rate)
    decay_samples = int(decay_time * sample_rate)
    release_samples = int(release_time * sample_rate)
    
    adsr[:attack_samples] = np.linspace(0, 1, attack_samples)
    adsr[attack_samples:attack_samples+decay_samples] = np.linspace(1, sustain_level, decay_samples)
    adsr[-release_samples:] = np.linspace(sustain_level, 0, release_samples)
    
    music_data *= adsr * 0.3  # Volume réduit
    
    # Sauvegarde
    music_path = os.path.join(temp_dir, "complex_music.wav")
    music_int16 = np.int16(music_data * 32767)
    wavfile.write(music_path, sample_rate, music_int16)
    
    files['complex_music'] = music_path
    
    print(f"✅ {len(files)} fichiers de test créés")
    return files

def test_audio_only_compression(system: HybridAudioVideoSystem, audio_files: Dict[str, str]):
    """Test la compression audio uniquement"""
    print("\n🎵 TEST COMPRESSION AUDIO SEULEMENT")
    print("=" * 60)
    
    results = {}
    
    for file_name, file_path in audio_files.items():
        print(f"\n🎵 Test: {file_name}")
        
        try:
            # Compression
            start_time = time.time()
            result = system.compress_media(file_path, MediaType.AUDIO_ONLY)
            compression_time = time.time() - start_time
            
            # Décompression
            start_time = time.time()
            decompression_result = system.decompress_media(
                audio_compressed=result.audio_compressed
            )
            decompression_time = time.time() - start_time
            
            # Métriques
            original_size = os.path.getsize(file_path)
            
            metrics = {
                'original_size_mb': original_size / 1024 / 1024,
                'compressed_size_mb': result.compressed_size / 1024 / 1024,
                'compression_ratio': result.compression_ratio,
                'compression_time': compression_time,
                'decompression_time': decompression_time,
                'total_time': compression_time + decompression_time,
                'quality_score': result.quality_metrics['audio_metrics']['quality_score'],
                'sample_rate': result.quality_metrics['audio_metrics']['sample_rate']
            }
            
            results[file_name] = metrics
            
            print(f"   📊 Ratio: {metrics['compression_ratio']:.2f}:1")
            print(f"   🎨 Qualité: {metrics['quality_score']:.3f}")
            print(f"   ⚡ Temps total: {metrics['total_time']:.3f}s")
            print(f"   📈 Efficacité: {metrics['compression_ratio'] / metrics['total_time']:.1f}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[file_name] = {'error': str(e)}
    
    return results

def test_video_only_compression(system: HybridAudioVideoSystem, video_files: Dict[str, str]):
    """Test la compression vidéo uniquement"""
    print("\n📹 TEST COMPRESSION VIDÉO SEULEMENT")
    print("=" * 60)
    
    results = {}
    
    for file_name, file_path in video_files.items():
        print(f"\n📹 Test: {file_name}")
        
        try:
            # Compression
            start_time = time.time()
            result = system.compress_media(file_path, MediaType.VIDEO_ONLY)
            compression_time = time.time() - start_time
            
            # Décompression
            start_time = time.time()
            decompression_result = system.decompress_media(
                video_compressed=result.video_compressed
            )
            decompression_time = time.time() - start_time
            
            # Métriques
            original_size = os.path.getsize(file_path)
            
            metrics = {
                'original_size_mb': original_size / 1024 / 1024,
                'compressed_size_mb': result.compressed_size / 1024 / 1024,
                'compression_ratio': result.compression_ratio,
                'compression_time': compression_time,
                'decompression_time': decompression_time,
                'total_time': compression_time + decompression_time,
                'quality_score': result.quality_metrics['video_metrics']['quality_score'],
                'fps_capability': result.quality_metrics['video_metrics']['fps_capability']
            }
            
            results[file_name] = metrics
            
            print(f"   📊 Ratio: {metrics['compression_ratio']:.2f}:1")
            print(f"   🎨 Qualité: {metrics['quality_score']:.3f}")
            print(f"   ⚡ FPS capability: {metrics['fps_capability']:.1f}")
            print(f"   ⏱️  Temps total: {metrics['total_time']:.3f}s")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[file_name] = {'error': str(e)}
    
    return results

def test_combined_audio_video(system: HybridAudioVideoSystem, files: Dict[str, str]):
    """Test la compression audio+vidéo combinée"""
    print("\n🎬🎵 TEST COMPRESSION AUDIO+VIDÉO COMBINÉE")
    print("=" * 60)
    
    results = {}
    
    for file_name, file_path in files.items():
        print(f"\n🎬🎵 Test: {file_name}")
        
        try:
            # Pipeline complet
            temp_output = tempfile.mktemp(suffix="_output.mp4")
            
            start_time = time.time()
            pipeline_result = system.full_pipeline(file_path, temp_output, MediaType.AUDIO_VIDEO)
            total_time = time.time() - start_time
            
            # Métriques
            original_size = os.path.getsize(file_path)
            output_size = os.path.getsize(temp_output) if os.path.exists(temp_output) else 0
            
            metrics = {
                'original_size_mb': original_size / 1024 / 1024,
                'output_size_mb': output_size / 1024 / 1024,
                'compression_ratio': pipeline_result.combined_metrics['compression_ratio'],
                'total_time': total_time,
                'quality_preservation': pipeline_result.combined_metrics['quality_preservation'],
                'processing_efficiency': pipeline_result.combined_metrics['processing_efficiency'],
                'pipeline_success': pipeline_result.success,
                'synchronization_quality': pipeline_result.combined_metrics['synchronization_quality']
            }
            
            results[file_name] = metrics
            
            print(f"   ✅ Succès: {metrics['pipeline_success']}")
            print(f"   📊 Ratio: {metrics['compression_ratio']:.2f}:1")
            print(f"   🎨 Qualité préservée: {metrics['quality_preservation']:.3f}")
            print(f"   📈 Efficacité: {metrics['processing_efficiency']:.1f}")
            print(f"   🔄 Synchronisation: {metrics['synchronization_quality']:.3f}")
            print(f"   ⏱️  Temps total: {metrics['total_time']:.3f}s")
            
            # Nettoyage
            try:
                os.remove(temp_output)
            except:
                pass
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[file_name] = {'error': str(e)}
    
    return results

def test_different_configurations(files: Dict[str, str]):
    """Test différentes configurations du système"""
    print("\n🔧 TEST DIFFÉRENTES CONFIGURATIONS")
    print("=" * 60)
    
    configurations = [
        {
            'name': 'Haute Qualité',
            'video_target': VideoOptimizationTarget.MAX_TEMPORAL_QUALITY,
            'audio_quality': AudioQualityMode.ULTRA_HIGH,
            'audio_compression': AudioCompressionLevel.HIGH_QUALITY
        },
        {
            'name': 'Compression Maximale',
            'video_target': VideoOptimizationTarget.MAX_COMPRESSION_RATIO,
            'audio_quality': AudioQualityMode.MEDIUM,
            'audio_compression': AudioCompressionLevel.EXTREME
        },
        {
            'name': 'Temps Réel',
            'video_target': VideoOptimizationTarget.REAL_TIME_PROCESSING,
            'audio_quality': AudioQualityMode.HIGH,
            'audio_compression': AudioCompressionLevel.BALANCED
        },
        {
            'name': 'Équilibré',
            'video_target': VideoOptimizationTarget.BALANCED_VIDEO,
            'audio_quality': AudioQualityMode.HIGH,
            'audio_compression': AudioCompressionLevel.BALANCED
        }
    ]
    
    config_results = {}
    
    for config in configurations:
        print(f"\n🔧 Configuration: {config['name']}")
        
        try:
            # Création du système avec la configuration
            system = HybridAudioVideoSystem(
                video_target=config['video_target'],
                audio_quality=config['audio_quality'],
                audio_compression=config['audio_compression']
            )
            
            # Test sur un fichier représentatif
            test_file = list(files.values())[0]  # Premier fichier
            temp_output = tempfile.mktemp(suffix="_config_test.mp4")
            
            start_time = time.time()
            result = system.full_pipeline(test_file, temp_output, MediaType.AUDIO_VIDEO)
            processing_time = time.time() - start_time
            
            metrics = {
                'compression_ratio': result.combined_metrics['compression_ratio'],
                'quality_preservation': result.combined_metrics['quality_preservation'],
                'processing_efficiency': result.combined_metrics['processing_efficiency'],
                'processing_time': processing_time,
                'success': result.success
            }
            
            config_results[config['name']] = metrics
            
            print(f"   📊 Ratio: {metrics['compression_ratio']:.2f}:1")
            print(f"   🎨 Qualité: {metrics['quality_preservation']:.3f}")
            print(f"   📈 Efficacité: {metrics['processing_efficiency']:.1f}")
            print(f"   ⏱️  Temps: {metrics['processing_time']:.3f}s")
            
            # Nettoyage
            try:
                os.remove(temp_output)
            except:
                pass
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            config_results[config['name']] = {'error': str(e)}
    
    return config_results

def generate_comprehensive_report(audio_results: Dict, video_results: Dict, 
                               combined_results: Dict, config_results: Dict):
    """Génère un rapport complet des tests"""
    print("\n📊 GÉNÉRATION DU RAPPORT COMPLET")
    print("=" * 60)
    
    try:
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Rapport Système Hybride Audio+Vidéo', fontsize=16)
        
        # Graphique 1: Ratios de compression audio
        if audio_results:
            audio_files = [name for name in audio_results.keys() if 'error' not in audio_results[name]]
            audio_ratios = [audio_results[name]['compression_ratio'] for name in audio_files]
            
            axes[0, 0].bar(audio_files, audio_ratios, color='lightblue', alpha=0.7)
            axes[0, 0].set_title('Ratio Compression Audio')
            axes[0, 0].set_ylabel('Ratio:1')
            axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Graphique 2: Ratios de compression vidéo
        if video_results:
            video_files = [name for name in video_results.keys() if 'error' not in video_results[name]]
            video_ratios = [video_results[name]['compression_ratio'] for name in video_files]
            
            axes[0, 1].bar(video_files, video_ratios, color='lightgreen', alpha=0.7)
            axes[0, 1].set_title('Ratio Compression Vidéo')
            axes[0, 1].set_ylabel('Ratio:1')
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Graphique 3: Qualité audio vs vidéo
        if audio_results and video_results:
            audio_qualities = [audio_results[name]['quality_score'] for name in audio_files]
            video_qualities = [video_results[name]['quality_score'] for name in video_files]
            
            x = np.arange(max(len(audio_files), len(video_files)))
            width = 0.35
            
            axes[0, 2].bar(x - width/2, audio_qualities[:len(x)], width, label='Audio', color='orange', alpha=0.7)
            axes[0, 2].bar(x + width/2, video_qualities[:len(x)], width, label='Vidéo', color='purple', alpha=0.7)
            axes[0, 2].set_title('Qualité Audio vs Vidéo')
            axes[0, 2].set_ylabel('Score de Qualité')
            axes[0, 2].set_xticks(x)
            axes[0, 2].set_xticklabels([f'Test {i+1}' for i in range(len(x))])
            axes[0, 2].legend()
        
        # Graphique 4: Performance combinée
        if combined_results:
            combined_files = [name for name in combined_results.keys() if 'error' not in combined_results[name]]
            combined_ratios = [combined_results[name]['compression_ratio'] for name in combined_files]
            combined_qualities = [combined_results[name]['quality_preservation'] for name in combined_files]
            
            axes[1, 0].scatter(combined_ratios, combined_qualities, alpha=0.7, s=100, c='red')
            axes[1, 0].set_title('Performance Combinée')
            axes[1, 0].set_xlabel('Ratio Compression')
            axes[1, 0].set_ylabel('Qualité Préservée')
            axes[1, 0].grid(True, alpha=0.3)
        
        # Graphique 5: Comparaison configurations
        if config_results:
            config_names = [name for name in config_results.keys() if 'error' not in config_results[name]]
            config_efficiencies = [config_results[name]['processing_efficiency'] for name in config_names]
            
            axes[1, 1].bar(config_names, config_efficiencies, color='gold', alpha=0.7)
            axes[1, 1].set_title('Efficacité par Configuration')
            axes[1, 1].set_ylabel('Efficacité (Ratio/Temps)')
            axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Graphique 6: Temps de traitement
        if config_results:
            config_times = [config_results[name]['processing_time'] for name in config_names]
            
            axes[1, 2].bar(config_names, config_times, color='lightcoral', alpha=0.7)
            axes[1, 2].set_title('Temps de Traitement')
            axes[1, 2].set_ylabel('Temps (s)')
            axes[1, 2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('F:/FINAL/DEFINITIF/hcs_v2-P3/hybrid_audio_video_report.png', 
                   dpi=150, bbox_inches='tight')
        print("✅ Rapport visuel sauvegardé: hybrid_audio_video_report.png")
        
    except Exception as e:
        print(f"⚠️ Erreur génération rapport: {e}")
    
    # Sauvegarde JSON
    report_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'audio_results': audio_results,
        'video_results': video_results,
        'combined_results': combined_results,
        'configuration_results': config_results
    }
    
    with open('F:/FINAL/DEFINITIF/hcs_v2-P3/hybrid_audio_video_results.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print("✅ Résultats sauvegardés: hybrid_audio_video_results.json")

def main():
    """Fonction principale de test"""
    print("🎬🎵 TEST COMPLET SYSTÈME HYBRIDE AUDIO+VIDÉO")
    print("Tests de compression et décompression multimédias")
    print("=" * 80)
    
    # Création des fichiers de test
    test_files = create_test_audio_video_files()
    
    # Séparation des fichiers par type
    audio_files = {name: path for name, path in test_files.items() if name.endswith('.wav')}
    video_files = {name: path for name, path in test_files.items() if name.endswith('.mp4')}
    
    # Système de test
    system = HybridAudioVideoSystem(
        video_target=VideoOptimizationTarget.BALANCED_VIDEO,
        audio_quality=AudioQualityMode.HIGH,
        audio_compression=AudioCompressionLevel.BALANCED
    )
    
    # Tests individuels
    audio_results = test_audio_only_compression(system, audio_files)
    video_results = test_video_only_compression(system, video_files)
    combined_results = test_combined_audio_video(system, test_files)
    
    # Tests de configurations
    config_results = test_different_configurations(test_files)
    
    # Rapport complet
    generate_comprehensive_report(audio_results, video_results, combined_results, config_results)
    
    # Statistiques finales
    stats = system.get_system_stats()
    print(f"\n📊 STATISTIQUES FINALES DU SYSTÈME:")
    print(f"   Traitements totaux: {stats['total_processings']}")
    print(f"   Ratio moyen: {stats['avg_compression_ratio']:.2f}:1")
    print(f"   Temps moyen: {stats['avg_processing_time']:.3f}s")
    print(f"   Vidéo seule: {stats['video_only_count']}")
    print(f"   Audio seule: {stats['audio_only_count']}")
    print(f"   Combiné: {stats['combined_count']}")
    
    # Nettoyage
    print("\n🧹 Nettoyage des fichiers temporaires...")
    for file_path in test_files.values():
        try:
            os.remove(file_path)
        except:
            pass
    
    print("\n✅ Tests système terminés!")
    print("🎬🎵 Système hybride audio+vidéo validé!")
    print("📊 Rapports détaillés disponibles!")
    
    return {
        'audio_results': audio_results,
        'video_results': video_results,
        'combined_results': combined_results,
        'config_results': config_results,
        'system_stats': stats
    }

if __name__ == "__main__":
    main()
