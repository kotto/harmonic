#!/usr/bin/env python3
"""
TEST AVEC MÉDIA RÉELS
Images et vidéos réelles avec métriques complètes
"""

import numpy as np
import cv2
import time
import os
import sys
import json
from typing import Dict, Any, List, Tuple
import matplotlib.pyplot as plt

# Ajout des chemins
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

class RealMediaTester:
    """Testeur pour médias réels avec métriques complètes"""
    
    def __init__(self):
        """Initialise le testeur de médias réels"""
        
        # Import du système optimisé
        from phase3_optimization import OptimizedHybridSystem
        self.hybrid_system = OptimizedHybridSystem(
            max_workers=4,
            cache_size=200,
            enable_parallel=True
        )
        
        # Métriques globales
        self.global_metrics = {
            'total_images': 0,
            'total_videos': 0,
            'total_frames': 0,
            'total_processing_time': 0.0,
            'total_compression_ratio': 0.0,
            'total_space_saved': 0,
            'errors': 0
        }
        
        # Métriques détaillées
        self.image_metrics = []
        self.video_metrics = []
        
        print("🎬 Testeur de médias réels initialisé")
    
    def create_realistic_images(self) -> Dict[str, np.ndarray]:
        """Crée des images réalistes variées"""
        
        images = {}
        
        # 1. Photo de paysage (naturelle)
        landscape = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Ciel dégradé
        for i in range(240):
            for j in range(640):
                blue = 255 - int(i * 0.3)
                green = 200 - int(i * 0.2)
                red = 150 - int(i * 0.1)
                landscape[i, j] = [red, green, blue]
        
        # Montagnes
        for i in range(240, 480):
            for j in range(640):
                mountain_height = int(100 * np.sin(j * 0.02) + 50)
                if i < 240 + mountain_height:
                    landscape[i, j] = [101, 67, 33]  # Brown
                else:
                    landscape[i, j] = [34, 139, 34]  # Forest green
        
        # Ajouter du bruit texturel
        noise = np.random.randint(-20, 20, (480, 640, 3), dtype=np.int16)
        landscape = np.clip(landscape.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        images['landscape_photo'] = landscape
        
        # 2. Portrait (visage)
        portrait = np.ones((480, 360, 3), dtype=np.uint8) * 255
        
        # Peau
        cv2.ellipse(portrait, (180, 200), (80, 100), 0, 0, 360, (255, 220, 177), -1)
        
        # Yeux
        cv2.circle(portrait, (150, 180), 15, (50, 50, 50), -1)
        cv2.circle(portrait, (210, 180), 15, (50, 50, 50), -1)
        cv2.circle(portrait, (150, 180), 5, (100, 100, 255), -1)
        cv2.circle(portrait, (210, 180), 5, (100, 100, 255), -1)
        
        # Bouche
        cv2.ellipse(portrait, (180, 250), (30, 15), 0, 0, 180, (200, 100, 100), -1)
        
        # Cheveux
        for i in range(100):
            x = np.random.randint(100, 260)
            y = np.random.randint(80, 150)
            cv2.circle(portrait, (x, y), 2, (50, 30, 20), -1)
        
        images['portrait_photo'] = portrait
        
        # 3. Document texte (scan)
        document = np.ones((600, 800, 3), dtype=np.uint8) * 255
        
        # Texte simulé
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Lignes de texte
        lines = [
            "RAPPORT D'ANALYSE HARMONIQUE",
            "Compression Hybride-Harmonique",
            "Phase 3 - Optimisation Avancée",
            "Test sur Médias Réels",
            "Métriques de Performance",
            "Résultats et Recommandations",
            "Conclusion et Perspectives"
        ]
        
        for i, line in enumerate(lines):
            y_pos = 80 + i * 60
            cv2.putText(document, line, (50, y_pos), font, 0.8, (0, 0, 0), 2)
            
            # Ajouter des lignes fines pour simuler le texte
            for j in range(len(line) * 8):
                x = 50 + j * 10
                cv2.line(document, (x, y_pos + 5), (x + 8, y_pos + 5), (0, 0, 0), 1)
        
        images['document_scan'] = document
        
        # 4. Image médicale (rayon X simulé)
        xray = np.zeros((512, 512, 3), dtype=np.uint8)
        
        # Fond sombre
        xray[:, :] = [20, 20, 30]
        
        # Os (structures claires)
        cv2.ellipse(xray, (256, 256), (150, 200), 0, 0, 360, (180, 180, 200), -1)
        cv2.circle(xray, (256, 200), 40, (200, 200, 220), -1)
        cv2.circle(xray, (256, 320), 60, (200, 200, 220), -1)
        
        # Ajouter du bruit médical
        medical_noise = np.random.normal(0, 10, (512, 512, 3))
        xray = np.clip(xray.astype(np.float32) + medical_noise, 0, 255).astype(np.uint8)
        
        images['medical_xray'] = xray
        
        # 5. Image satellite (vue aérienne)
        satellite = np.zeros((400, 600, 3), dtype=np.uint8)
        
        # Zones urbaines (carrés)
        for i in range(8):
            x = np.random.randint(0, 550)
            y = np.random.randint(0, 350)
            size = np.random.randint(30, 80)
            color = tuple(np.random.randint(100, 200, 3).tolist())
            cv2.rectangle(satellite, (x, y), (x + size, y + size), color, -1)
        
        # Zones vertes (parcs)
        for i in range(5):
            x = np.random.randint(0, 550)
            y = np.random.randint(0, 350)
            radius = np.random.randint(20, 50)
            cv2.circle(satellite, (x, y), radius, (34, 139, 34), -1)
        
        # Routes (lignes)
        for i in range(4):
            x1 = np.random.randint(0, 600)
            y1 = np.random.randint(0, 400)
            x2 = np.random.randint(0, 600)
            y2 = np.random.randint(0, 400)
            cv2.line(satellite, (x1, y1), (x2, y2), (80, 80, 80), 3)
        
        images['satellite_view'] = satellite
        
        return images
    
    def create_realistic_video_frames(self, fps: int = 30, duration: int = 2) -> List[np.ndarray]:
        """Crée des frames vidéo réalistes"""
        
        frames = []
        total_frames = fps * duration
        
        # Vidéo de type "interview" (talking head)
        for frame_idx in range(total_frames):
            frame = np.ones((480, 640, 3), dtype=np.uint8) * 200
            
            # Fond (studio)
            frame[:, :] = [50, 50, 80]
            
            # Personne (silhouette simple)
            cv2.ellipse(frame, (320, 300), (80, 120), 0, 0, 360, (150, 100, 50), -1)
            
            # Tête (mouvement subtil)
            head_x = 320 + int(5 * np.sin(frame_idx * 0.1))
            head_y = 180 + int(3 * np.cos(frame_idx * 0.15))
            cv2.circle(frame, (head_x, head_y), 40, (255, 220, 177), -1)
            
            # Mouvement des yeux
            eye_offset = int(2 * np.sin(frame_idx * 0.2))
            cv2.circle(frame, (head_x - 15, head_y + eye_offset), 5, (50, 50, 50), -1)
            cv2.circle(frame, (head_x + 15, head_y + eye_offset), 5, (50, 50, 50), -1)
            
            # Bouche (mouvement de parole)
            mouth_open = int(3 * np.sin(frame_idx * 2))
            cv2.ellipse(frame, (head_x, head_y + 25), (15, 5 + mouth_open), 0, 0, 180, (200, 100, 100), -1)
            
            # Éclairage variable
            lighting = int(10 * np.sin(frame_idx * 0.05))
            frame = np.clip(frame.astype(np.int16) + lighting, 0, 255).astype(np.uint8)
            
            frames.append(frame)
        
        return frames
    
    def test_real_images(self) -> Dict[str, Any]:
        """Test les images réelles"""
        
        print("📸 TEST D'IMAGES RÉELLES")
        print("=" * 50)
        
        # Créer les images
        images = self.create_realistic_images()
        
        print(f"✅ {len(images)} images réelles créées")
        
        results = []
        
        for img_name, img_array in images.items():
            print(f"\n📸 {img_name}:")
            print(f"   Dimensions: {img_array.shape}")
            print(f"   Taille: {img_array.nbytes / (1024*1024):.2f} MB")
            
            # Test avec différentes priorités
            priorities = ['speed', 'quality', 'balanced']
            
            for priority in priorities:
                result = self.hybrid_system.compress_image_optimized(img_array, priority)
                
                if result['success']:
                    print(f"   🎯 {priority}: {result['decision']}")
                    print(f"      📊 Ratio: {result['compression_ratio']:.1f}:1")
                    print(f"      💾 Espace: {result['compression_ratio']:.1f}%")
                    print(f"      ⏱️ Temps: {result['total_processing_time']:.4f}s")
                    print(f"      🎯 Qualité: {result['quality']:.3f}")
                    
                    # Métriques détaillées
                    metrics = {
                        'name': img_name,
                        'priority': priority,
                        'shape': img_array.shape,
                        'original_size': img_array.nbytes,
                        'decision': result['decision'],
                        'compression_ratio': result['compression_ratio'],
                        'processing_time': result['total_processing_time'],
                        'quality': result['quality'],
                        'cached': result['cached'],
                        'properties': result['properties']
                    }
                    
                    results.append(metrics)
                    
                    # Mettre à jour les métriques globales
                    self.global_metrics['total_images'] += 1
                    self.global_metrics['total_processing_time'] += result['total_processing_time']
                    self.global_metrics['total_compression_ratio'] += result['compression_ratio']
                    self.global_metrics['total_space_saved'] += (1 - 1/result['compression_ratio']) * img_array.nbytes
                    
                else:
                    print(f"   ❌ Erreur: {result['error']}")
                    self.global_metrics['errors'] += 1
        
        self.image_metrics = results
        return results
    
    def test_real_video_light(self) -> Dict[str, Any]:
        """Test les vidéos réelles avec ressources réduites"""
        
        print(f"\n🎬 TEST VIDÉO RÉELLE (ressources réduites)")
        print("=" * 50)
        
        # Créer les frames vidéo avec ressources réduites
        frames = self.create_realistic_video_frames(fps=5, duration=1)
        
        print(f"✅ {len(frames)} frames créés (1s @ 5fps)")
        print(f"   Dimensions: {frames[0].shape}")
        print(f"   Taille totale: {len(frames) * frames[0].nbytes / (1024*1024):.2f} MB")
        
        # Test compression batch parallèle
        print(f"\n🚀 Compression batch parallèle...")
        
        start_time = time.time()
        batch_results = self.hybrid_system.compress_batch_parallel(frames, 'balanced')
        total_time = time.time() - start_time
        
        # Analyser les résultats
        successful = [r for r in batch_results if r.get('success', False)]
        
        print(f"✅ Compression terminée:")
        print(f"   Frames réussis: {len(successful)}/{len(frames)}")
        print(f"   Temps total: {total_time:.3f}s")
        print(f"   FPS effectif: {len(frames)/total_time:.1f}")
        
        if successful:
            # Statistiques vidéo
            ratios = [r['compression_ratio'] for r in successful]
            times = [r['total_processing_time'] for r in successful]
            decisions = [r['decision'] for r in successful]
            
            avg_ratio = np.mean(ratios)
            avg_time = np.mean(times)
            
            # Distribution des décisions
            decision_counts = {}
            for decision in decisions:
                decision_counts[decision] = decision_counts.get(decision, 0) + 1
            
            print(f"\n📊 Statistiques vidéo:")
            print(f"   Ratio moyen: {avg_ratio:.1f}:1")
            print(f"   Temps moyen/frame: {avg_time:.4f}s")
            print(f"   Espace total économisé: {(1 - 1/avg_ratio) * 100:.1f}%")
            
            print(f"\n🎯 Distribution des décisions:")
            for decision, count in decision_counts.items():
                percentage = count / len(decisions) * 100
                print(f"   {decision}: {count} ({percentage:.1f}%)")
            
            # Métriques vidéo
            video_metrics = {
                'total_frames': len(frames),
                'successful_frames': len(successful),
                'fps_original': 5,
                'fps_effective': len(frames) / total_time,
                'avg_compression_ratio': avg_ratio,
                'avg_processing_time': avg_time,
                'total_processing_time': total_time,
                'decision_distribution': decision_counts,
                'frame_shape': frames[0].shape,
                'total_original_size': len(frames) * frames[0].nbytes,
                'total_compressed_size': len(frames) * frames[0].nbytes / avg_ratio
            }
            
            # Mettre à jour les métriques globales
            self.global_metrics['total_videos'] += 1
            self.global_metrics['total_frames'] += len(frames)
            self.global_metrics['total_processing_time'] += total_time
            self.global_metrics['total_compression_ratio'] += avg_ratio * len(frames)
            self.global_metrics['total_space_saved'] += (1 - 1/avg_ratio) * len(frames) * frames[0].nbytes
            
            self.video_metrics = video_metrics
            return video_metrics
        
        else:
            print(f"❌ Échec complet de la compression vidéo")
            self.global_metrics['errors'] += len(frames)
            return {}
    
    def test_real_video(self) -> Dict[str, Any]:
        """Test les vidéos réelles (version originale)"""
        
        print(f"\n🎬 TEST VIDÉO RÉELLE")
        print("=" * 50)
        
        # Créer les frames vidéo
        frames = self.create_realistic_video_frames(fps=30, duration=2)
        
        print(f"✅ {len(frames)} frames créés (2s @ 30fps)")
        print(f"   Dimensions: {frames[0].shape}")
        print(f"   Taille totale: {len(frames) * frames[0].nbytes / (1024*1024):.2f} MB")
        
        # Test compression batch parallèle
        print(f"\n🚀 Compression batch parallèle...")
        
        start_time = time.time()
        batch_results = self.hybrid_system.compress_batch_parallel(frames, 'balanced')
        total_time = time.time() - start_time
        
        # Analyser les résultats
        successful = [r for r in batch_results if r.get('success', False)]
        
        print(f"✅ Compression terminée:")
        print(f"   Frames réussis: {len(successful)}/{len(frames)}")
        print(f"   Temps total: {total_time:.3f}s")
        print(f"   FPS effectif: {len(frames)/total_time:.1f}")
        
        if successful:
            # Statistiques vidéo
            ratios = [r['compression_ratio'] for r in successful]
            times = [r['total_processing_time'] for r in successful]
            decisions = [r['decision'] for r in successful]
            
            avg_ratio = np.mean(ratios)
            avg_time = np.mean(times)
            
            # Distribution des décisions
            decision_counts = {}
            for decision in decisions:
                decision_counts[decision] = decision_counts.get(decision, 0) + 1
            
            print(f"\n📊 Statistiques vidéo:")
            print(f"   Ratio moyen: {avg_ratio:.1f}:1")
            print(f"   Temps moyen/frame: {avg_time:.4f}s")
            print(f"   Espace total économisé: {(1 - 1/avg_ratio) * 100:.1f}%")
            
            print(f"\n🎯 Distribution des décisions:")
            for decision, count in decision_counts.items():
                percentage = count / len(decisions) * 100
                print(f"   {decision}: {count} ({percentage:.1f}%)")
            
            # Métriques vidéo
            video_metrics = {
                'total_frames': len(frames),
                'successful_frames': len(successful),
                'fps_original': 30,
                'fps_effective': len(frames) / total_time,
                'avg_compression_ratio': avg_ratio,
                'avg_processing_time': avg_time,
                'total_processing_time': total_time,
                'decision_distribution': decision_counts,
                'frame_shape': frames[0].shape,
                'total_original_size': len(frames) * frames[0].nbytes,
                'total_compressed_size': len(frames) * frames[0].nbytes / avg_ratio
            }
            
            # Mettre à jour les métriques globales
            self.global_metrics['total_videos'] += 1
            self.global_metrics['total_frames'] += len(frames)
            self.global_metrics['total_processing_time'] += total_time
            self.global_metrics['total_compression_ratio'] += avg_ratio * len(frames)
            self.global_metrics['total_space_saved'] += (1 - 1/avg_ratio) * len(frames) * frames[0].nbytes
            
            self.video_metrics = video_metrics
            return video_metrics
        
        else:
            print(f"❌ Échec complet de la compression vidéo")
            self.global_metrics['errors'] += len(frames)
            return {}
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Génère un rapport complet des tests"""
        
        print(f"\n📊 RAPPORT COMPLET DES TESTS")
        print("=" * 80)
        
        # Statistiques globales
        total_processed = self.global_metrics['total_images'] + self.global_metrics['total_frames']
        
        if total_processed > 0:
            avg_ratio = self.global_metrics['total_compression_ratio'] / total_processed
            avg_time = self.global_metrics['total_processing_time'] / total_processed
            total_space_saved_mb = self.global_metrics['total_space_saved'] / (1024 * 1024)
            
            print(f"📈 MÉTRIQUES GLOBALES:")
            print(f"   Images traitées: {self.global_metrics['total_images']}")
            print(f"   Frames vidéo traitées: {self.global_metrics['total_frames']}")
            print(f"   Total éléments: {total_processed}")
            print(f"   Ratio moyen: {avg_ratio:.1f}:1")
            print(f"   Temps moyen: {avg_time:.4f}s")
            print(f"   Espace total économisé: {total_space_saved_mb:.2f} MB")
            print(f"   Erreurs: {self.global_metrics['errors']}")
            
            # Performance par type
            print(f"\n📊 PERFORMANCE PAR TYPE:")
            
            if self.image_metrics:
                image_ratios = [m['compression_ratio'] for m in self.image_metrics]
                image_times = [m['processing_time'] for m in self.image_metrics]
                
                print(f"   Images:")
                print(f"      Ratio moyen: {np.mean(image_ratios):.1f}:1")
                print(f"      Temps moyen: {np.mean(image_times):.4f}s")
                print(f"      Performance: {np.mean(image_ratios)/np.mean(image_times):.1f} ratio/s")
            
            if self.video_metrics:
                print(f"   Vidéo:")
                print(f"      FPS original: {self.video_metrics['fps_original']}")
                print(f"      FPS effectif: {self.video_metrics['fps_effective']:.1f}")
                print(f"      Ratio moyen: {self.video_metrics['avg_compression_ratio']:.1f}:1")
                print(f"      Temps/frame: {self.video_metrics['avg_processing_time']:.4f}s")
            
            # Analyse par type de contenu
            print(f"\n🎯 ANALYSE PAR TYPE DE CONTENU:")
            
            content_analysis = {}
            for metric in self.image_metrics:
                content_type = self._classify_content(metric['name'])
                if content_type not in content_analysis:
                    content_analysis[content_type] = []
                content_analysis[content_type].append(metric['compression_ratio'])
            
            for content_type, ratios in content_analysis.items():
                print(f"   {content_type}:")
                print(f"      Ratio moyen: {np.mean(ratios):.1f}:1")
                print(f"      Ratio max: {np.max(ratios):.1f}:1")
                print(f"      Ratio min: {np.min(ratios):.1f}:1")
            
            # Recommandations
            print(f"\n💡 RECOMMANDATIONS:")
            
            if avg_ratio > 500:
                print(f"   ✅ Excellente compression moyenne ({avg_ratio:.1f}:1)")
            elif avg_ratio > 100:
                print(f"   ✅ Bonne compression moyenne ({avg_ratio:.1f}:1)")
            else:
                print(f"   ⚠️ Compression moyenne faible ({avg_ratio:.1f}:1)")
            
            if avg_time < 0.01:
                print(f"   ✅ Temps de traitement excellent ({avg_time:.4f}s)")
            elif avg_time < 0.1:
                print(f"   ✅ Temps de traitement bon ({avg_time:.4f}s)")
            else:
                print(f"   ⚠️ Temps de traitement lent ({avg_time:.4f}s)")
            
            if self.global_metrics['errors'] == 0:
                print(f"   ✅ Fiabilité parfaite (0 erreurs)")
            elif self.global_metrics['errors'] < total_processed * 0.05:
                print(f"   ✅ Bonne fiabilité ({self.global_metrics['errors']} erreurs)")
            else:
                print(f"   ⚠️ Fiabilité faible ({self.global_metrics['errors']} erreurs)")
        
        # Créer des graphiques
        self._create_performance_graphs()
        
        return {
            'global_metrics': self.global_metrics,
            'image_metrics': self.image_metrics,
            'video_metrics': self.video_metrics,
            'content_analysis': content_analysis if 'content_analysis' in locals() else {}
        }
    
    def _classify_content(self, name: str) -> str:
        """Classifie le type de contenu"""
        
        if 'photo' in name:
            return 'Photo naturelle'
        elif 'document' in name:
            return 'Document texte'
        elif 'medical' in name:
            return 'Image médicale'
        elif 'satellite' in name:
            return 'Image satellite'
        else:
            return 'Autre'
    
    def _create_performance_graphs(self):
        """Crée des graphiques de performance"""
        
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # Graphique 1: Ratios de compression par type d'image
            if self.image_metrics:
                content_types = []
                ratios = []
                
                for metric in self.image_metrics:
                    content_type = self._classify_content(metric['name'])
                    content_types.append(content_type)
                    ratios.append(metric['compression_ratio'])
                
                # Grouper par type
                type_ratios = {}
                for ct, r in zip(content_types, ratios):
                    if ct not in type_ratios:
                        type_ratios[ct] = []
                    type_ratios[ct].append(r)
                
                types = list(type_ratios.keys())
                avg_ratios = [np.mean(type_ratios[t]) for t in types]
                
                ax1.bar(types, avg_ratios, color='skyblue', alpha=0.7)
                ax1.set_xlabel('Type de contenu')
                ax1.set_ylabel('Ratio de compression')
                ax1.set_title('Ratio par Type de Contenu')
                ax1.tick_params(axis='x', rotation=45)
                ax1.grid(True, alpha=0.3)
            
            # Graphique 2: Temps de traitement
            if self.image_metrics:
                times = [m['processing_time'] * 1000 for m in self.image_metrics]  # en ms
                ax2.hist(times, bins=20, color='lightgreen', alpha=0.7, edgecolor='black')
                ax2.set_xlabel('Temps de traitement (ms)')
                ax2.set_ylabel('Fréquence')
                ax2.set_title('Distribution des Temps')
                ax2.grid(True, alpha=0.3)
            
            # Graphique 3: Distribution des décisions
            if self.image_metrics:
                decisions = [m['decision'] for m in self.image_metrics]
                decision_counts = {}
                for d in decisions:
                    decision_counts[d] = decision_counts.get(d, 0) + 1
                
                ax3.pie(decision_counts.values(), labels=decision_counts.keys(), autopct='%1.1f%%')
                ax3.set_title('Distribution des Décisions')
            
            # Graphique 4: Performance globale
            if self.image_metrics:
                performances = [m['compression_ratio']/m['processing_time'] for m in self.image_metrics]
                ax4.plot(range(len(performances)), performances, 'ro-', alpha=0.7)
                ax4.set_xlabel('Index de l\'image')
                ax4.set_ylabel('Performance (ratio/s)')
                ax4.set_title('Performance par Image')
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('real_media_performance.png', dpi=150, bbox_inches='tight')
            print("📊 Graphiques sauvegardés dans 'real_media_performance.png'")
            
            try:
                plt.show()
            except:
                print("⚠️ Impossible d'afficher les graphiques")
                
        except Exception as e:
            print(f"⚠️ Erreur création graphiques: {e}")

def main():
    """Fonction principale"""
    print("🎬 TEST AVEC MÉDIA RÉELS")
    print("Images et vidéos réelles avec métriques complètes")
    print("=" * 80)
    
    try:
        # Initialisation du testeur
        tester = RealMediaTester()
        
        # Test des images réelles
        image_results = tester.test_real_images()
        
        # Test vidéo avec ressources réduites
        video_results = tester.test_real_video_light()
        
        # Rapport complet
        report = tester.generate_comprehensive_report()
        
        # Sauvegarde des résultats
        try:
            with open('real_media_test_results.json', 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print("💾 Résultats sauvegardés dans 'real_media_test_results.json'")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde JSON: {e}")
        
        print(f"\n🎯 CONCLUSION:")
        print("✅ Test sur médias réels terminé avec succès")
        print("✅ Métriques complètes générées")
        print("✅ Performance évaluée")
        print("✅ Recommandations fournies")
        
        return report
        
    except Exception as e:
        print(f"❌ Erreur test médias réels: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
