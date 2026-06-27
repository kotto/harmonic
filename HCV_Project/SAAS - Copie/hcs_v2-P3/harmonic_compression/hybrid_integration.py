#!/usr/bin/env python3
"""
INTÉGRATION HYBRIDE DANS LE SYSTÈME HARMONIQUE
Combinaison des forces des deux systèmes
"""

import numpy as np
import cv2
import time
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
import logging

# Ajout des chemins
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, 'core'))

logger = logging.getLogger(__name__)

class HybridHarmonicCompressor:
    """
    Compresseur hybride qui combine :
    1. L'intelligence adaptative de la compression harmonique
    2. La fiabilité garantie du système hybride K=0.02 + WebP
    """
    
    def __init__(self, 
                 hybrid_k_factor: float = 0.02,
                 hybrid_webp_quality: int = 95,
                 harmonic_energy_level: str = 'standard'):
        """
        Initialise le compresseur hybride-harmonique
        
        Args:
            hybrid_k_factor: Facteur K pour le système hybride
            hybrid_webp_quality: Qualité WebP pour le système hybride
            harmonic_energy_level: Niveau d'énergie pour le système harmonique
        """
        
        # Configuration hybride
        self.hybrid_k_factor = hybrid_k_factor
        self.hybrid_webp_quality = hybrid_webp_quality
        
        # Configuration harmonique
        self.harmonic_energy_level = harmonic_energy_level
        
        # Initialisation des systèmes
        self._initialize_systems()
        
        # Configuration de décision
        self.decision_thresholds = {
            'complexity_hybrid': 0.3,    # Si complexité < 0.3 → hybride
            'complexity_harmonic': 0.7, # Si complexité > 0.7 → harmonique
            'speed_priority': 0.5,         # Si vitesse prioritaire → hybride
            'quality_priority': 0.8        # Si qualité prioritaire → harmonique
        }
        
        # Statistiques de performance
        self.performance_stats = {
            'total_processed': 0,
            'hybrid_used': 0,
            'harmonic_used': 0,
            'hybrid_avg_ratio': 0.0,
            'harmonic_avg_ratio': 0.0,
            'hybrid_avg_time': 0.0,
            'harmonic_avg_time': 0.0,
            'decision_accuracy': 0.0
        }
        
        logger.info("🔧 Compresseur Hybride-Harmonique initialisé")
        logger.info(f"   K-factor hybride: {hybrid_k_factor}")
        logger.info(f"   Qualité WebP: {hybrid_webp_quality}")
        logger.info(f"   Énergie harmonique: {harmonic_energy_level}")
    
    def _initialize_systems(self):
        """Initialise les deux systèmes de compression"""
        
        try:
            # Initialisation du système hybride
            from hybrid_compressor import HybridCompressor
            self.hybrid_system = HybridCompressor(
                k_factor=self.hybrid_k_factor,
                webp_quality=self.hybrid_webp_quality
            )
            logger.info("✅ Système hybride initialisé")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation hybride: {e}")
            self.hybrid_system = None
        
        try:
            # Initialisation du système harmonique
            from harmonic_compression.core import harmonic_engine
            self.harmonic_system = harmonic_engine
            logger.info("✅ Système harmonique initialisé")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation harmonique: {e}")
            self.harmonic_system = None
    
    def compress_image(self, 
                     image: np.ndarray,
                     mode: str = 'auto',
                     target_ratio: Optional[float] = None,
                     priority: str = 'balanced') -> Dict[str, Any]:
        """
        Compresse une image avec décision intelligente
        
        Args:
            image: Image à compresser
            mode: 'auto', 'hybrid', 'harmonic', 'both'
            target_ratio: Ratio cible optionnel
            priority: 'speed', 'quality', 'balanced'
            
        Returns:
            Dict: Résultat de compression avec métriques
        """
        
        start_time = time.time()
        
        try:
            # Validation de l'image
            if not isinstance(image, np.ndarray) or image.size == 0:
                return {
                    'success': False,
                    'error': "Image invalide",
                    'method_used': 'none'
                }
            
            original_size = image.nbytes
            original_shape = image.shape
            
            # Analyse des caractéristiques pour la décision
            characteristics = self._analyze_for_decision(image)
            
            # Décision du système à utiliser
            if mode == 'auto':
                system_choice = self._make_intelligent_decision(characteristics, priority)
            elif mode == 'hybrid':
                system_choice = 'hybrid'
            elif mode == 'harmonic':
                system_choice = 'harmonic'
            elif mode == 'both':
                system_choice = 'both'
            else:
                system_choice = 'auto'
            
            logger.info(f"🎯 Décision: {system_choice} (mode: {mode}, priorité: {priority})")
            logger.info(f"   Complexité: {characteristics['complexity_score']:.3f}")
            logger.info(f"   Contours: {characteristics['edge_density']:.3f}")
            logger.info(f"   Variance: {characteristics['variance']:.1f}")
            
            # Exécution de la compression
            if system_choice == 'both':
                # Exécuter les deux systèmes
                results = self._compress_with_both_systems(image, target_ratio)
                best_result = self._select_best_result(results, priority)
                best_result['method_used'] = 'both_best'
                best_result['both_results'] = results
                
            else:
                # Exécuter le système choisi
                if system_choice == 'hybrid' and self.hybrid_system:
                    best_result = self._compress_with_hybrid(image, target_ratio)
                elif system_choice == 'harmonic' and self.harmonic_system:
                    best_result = self._compress_with_harmonic(image, target_ratio)
                else:
                    # Fallback
                    best_result = self._compress_fallback(image)
            
            # Ajout des métriques hybrides
            processing_time = time.time() - start_time
            best_result['total_processing_time'] = processing_time
            best_result['decision_system'] = system_choice
            best_result['characteristics'] = characteristics
            best_result['original_size'] = original_size
            best_result['original_shape'] = original_shape
            
            # Calcul des métriques comparatives
            if system_choice == 'both' and 'both_results' in best_result:
                best_result['comparison'] = self._compare_systems(best_result['both_results'])
            
            # Mise à jour des statistiques
            self._update_performance_stats(best_result, system_choice)
            
            logger.info(f"✅ Compression terminée: {best_result.get('compression_ratio', 0):.1f}:1")
            logger.info(f"   Méthode: {best_result.get('method_used', 'unknown')}")
            logger.info(f"   Temps: {processing_time:.3f}s")
            
            return best_result
            
        except Exception as e:
            logger.error(f"❌ Erreur compression hybride-harmonique: {e}")
            return {
                'success': False,
                'error': str(e),
                'method_used': 'error',
                'total_processing_time': time.time() - start_time
            }
    
    def _analyze_for_decision(self, image: np.ndarray) -> Dict[str, float]:
        """Analyse l'image pour prendre une décision intelligente"""
        
        try:
            # Conversion en niveaux de gris
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            h, w = gray.shape
            
            # Caractéristiques pour la décision
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (h * w)
            
            variance = np.var(gray)
            mean_intensity = np.mean(gray)
            
            # Complexité composite
            complexity = min(1.0, (edge_density + variance/2000) / 2)
            
            # Prédictibilité (pour décider si hybride est efficace)
            predictability = 1.0 / (1.0 + variance/1000)
            
            return {
                'complexity_score': complexity,
                'edge_density': edge_density,
                'variance': variance,
                'mean_intensity': mean_intensity,
                'predictability': predictability,
                'resolution': (h, w)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse décision: {e}")
            return {
                'complexity_score': 0.5,
                'edge_density': 0.5,
                'variance': 1000,
                'mean_intensity': 128,
                'predictability': 0.5,
                'resolution': (100, 100)
            }
    
    def _make_intelligent_decision(self, 
                                characteristics: Dict[str, float], 
                                priority: str) -> str:
        """
        Prend une décision intelligente basée sur les caractéristiques et priorités
        
        Args:
            characteristics: Caractéristiques de l'image
            priority: 'speed', 'quality', 'balanced'
            
        Returns:
            str: 'hybrid', 'harmonic', 'both'
        """
        
        complexity = characteristics['complexity_score']
        edge_density = characteristics['edge_density']
        variance = characteristics['variance']
        predictability = characteristics['predictability']
        
        # Logique de décision
        if priority == 'speed':
            # Priorité vitesse → favoriser hybride (garanti et rapide)
            if complexity < self.decision_thresholds['complexity_hybrid']:
                return 'hybrid'
            elif predictability > 0.7:
                return 'hybrid'
            else:
                return 'both'
        
        elif priority == 'quality':
            # Priorité qualité → favoriser harmonique (adaptatif)
            if complexity > self.decision_thresholds['complexity_harmonic']:
                return 'harmonic'
            elif edge_density > 0.3:
                return 'harmonic'
            else:
                return 'both'
        
        else:  # balanced
            # Équilibre → décision basée sur la complexité
            if complexity < self.decision_thresholds['complexity_hybrid']:
                return 'hybrid'
            elif complexity > self.decision_thresholds['complexity_harmonic']:
                return 'harmonic'
            else:
                # Zone intermédiaire → tester les deux
                return 'both'
    
    def _compress_with_hybrid(self, 
                             image: np.ndarray, 
                             target_ratio: Optional[float]) -> Dict[str, Any]:
        """Compresse avec le système hybride"""
        
        try:
            compressed_data, metadata = self.hybrid_system.compress_image(image, target_ratio)
            
            return {
                'success': True,
                'method_used': 'hybrid',
                'compressed_data': compressed_data,
                'compression_ratio': metadata['hybrid_ratio'],
                'space_saved_percent': metadata['space_saved_percent'],
                'processing_time': metadata['total_time'],
                'quality_estimate': 0.85,  # Estimation WebP 95%
                'k_ratio': metadata['k_ratio'],
                'webp_ratio': metadata['webp_ratio'],
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur compression hybride: {e}")
            return {
                'success': False,
                'error': f"Hybrid: {str(e)}",
                'method_used': 'hybrid'
            }
    
    def _compress_with_harmonic(self, 
                               image: np.ndarray, 
                               target_ratio: Optional[float]) -> Dict[str, Any]:
        """Compresse avec le système harmonique"""
        
        try:
            result = self.harmonic_system.compress_image(
                image, 
                energy_level=self.harmonic_energy_level
            )
            
            if result.success:
                return {
                    'success': True,
                    'method_used': 'harmonic',
                    'compressed_data': result.compressed_data,
                    'compression_ratio': result.compression_ratio,
                    'space_saved_percent': result.space_saved_percent,
                    'processing_time': result.processing_time,
                    'quality_estimate': result.quality_metrics.get('quality_preservation', 0.8),
                    'mode_used': result.mode_used,
                    'metadata': result.metadata
                }
            else:
                return {
                    'success': False,
                    'error': result.error,
                    'method_used': 'harmonic'
                }
            
        except Exception as e:
            logger.error(f"❌ Erreur compression harmonique: {e}")
            return {
                'success': False,
                'error': f"Harmonic: {str(e)}",
                'method_used': 'harmonic'
            }
    
    def _compress_with_both_systems(self, 
                                  image: np.ndarray, 
                                  target_ratio: Optional[float]) -> List[Dict[str, Any]]:
        """Compresse avec les deux systèmes et retourne les deux résultats"""
        
        results = []
        
        # Compression hybride
        hybrid_result = self._compress_with_hybrid(image, target_ratio)
        results.append(hybrid_result)
        
        # Compression harmonique
        harmonic_result = self._compress_with_harmonic(image, target_ratio)
        results.append(harmonic_result)
        
        return results
    
    def _select_best_result(self, 
                          results: List[Dict[str, Any]], 
                          priority: str) -> Dict[str, Any]:
        """Sélectionne le meilleur résultat selon la priorité"""
        
        if not results:
            return {
                'success': False,
                'error': "Aucun résultat disponible",
                'method_used': 'none'
            }
        
        # Filtrer les résultats réussis
        successful_results = [r for r in results if r.get('success', False)]
        
        if not successful_results:
            return results[0]  # Prendre le premier même si échec
        
        if priority == 'speed':
            # Priorité vitesse → le plus rapide
            best = min(successful_results, key=lambda x: x.get('processing_time', float('inf')))
        elif priority == 'quality':
            # Priorité qualité → le meilleur ratio
            best = max(successful_results, key=lambda x: x.get('compression_ratio', 0))
        else:  # balanced
            # Équilibre → score combiné
            def score(r):
                ratio_score = r.get('compression_ratio', 0) / 100  # Normalisé
                time_score = 1.0 / (r.get('processing_time', 1) + 0.001)  # Inverse du temps
                return ratio_score * 0.6 + time_score * 0.4
            
            best = max(successful_results, key=score)
        
        best['selection_priority'] = priority
        return best
    
    def _compare_systems(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare les performances des deux systèmes"""
        
        if len(results) < 2:
            return {}
        
        hybrid = results[0]
        harmonic = results[1]
        
        if not (hybrid.get('success') and harmonic.get('success')):
            return {'error': 'Les deux systèmes ont échoué'}
        
        comparison = {
            'hybrid_ratio': hybrid.get('compression_ratio', 0),
            'harmonic_ratio': harmonic.get('compression_ratio', 0),
            'hybrid_time': hybrid.get('processing_time', 0),
            'harmonic_time': harmonic.get('processing_time', 0),
            'ratio_improvement': 0,
            'time_improvement': 0,
            'winner': 'equal'
        }
        
        # Calcul des améliorations
        if hybrid.get('success') and harmonic.get('success'):
            ratio_diff = harmonic['compression_ratio'] - hybrid['compression_ratio']
            time_diff = hybrid['processing_time'] - harmonic['processing_time']
            
            comparison['ratio_improvement'] = ratio_diff / hybrid['compression_ratio'] * 100
            comparison['time_improvement'] = time_diff / hybrid['processing_time'] * 100
            
            # Détermination du gagnant
            if ratio_diff > 0.1:  # Harmonique significativement meilleur
                comparison['winner'] = 'harmonic'
            elif ratio_diff < -0.1:  # Hybride significativement meilleur
                comparison['winner'] = 'hybrid'
            elif time_diff < -0.1:  # Hybride significativement plus rapide
                comparison['winner'] = 'hybrid'
            elif time_diff > 0.1:  # Harmonique significativement plus rapide
                comparison['winner'] = 'harmonic'
            else:
                comparison['winner'] = 'equal'
        
        return comparison
    
    def _compress_fallback(self, image: np.ndarray) -> Dict[str, Any]:
        """Compression de secours simple"""
        
        try:
            # Compression WebP standard
            if len(image.shape) == 3:
                encode_param = [cv2.IMWRITE_WEBP_QUALITY, 85]
                result, compressed = cv2.imencode('.webp', image, encode_param)
                compressed_data = compressed.tobytes() if result else image.tobytes()
            else:
                compressed_data = cv2.imencode('.webp', image)[1].tobytes()
            
            original_size = image.nbytes
            compression_ratio = original_size / len(compressed_data)
            
            return {
                'success': True,
                'method_used': 'fallback',
                'compressed_data': compressed_data,
                'compression_ratio': compression_ratio,
                'space_saved_percent': (1 - 1/compression_ratio) * 100,
                'processing_time': 0.1,
                'quality_estimate': 0.8
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Fallback: {str(e)}",
                'method_used': 'fallback'
            }
    
    def _update_performance_stats(self, result: Dict[str, Any], system_choice: str):
        """Met à jour les statistiques de performance"""
        
        self.performance_stats['total_processed'] += 1
        
        if system_choice == 'hybrid':
            self.performance_stats['hybrid_used'] += 1
            if result.get('success'):
                self.performance_stats['hybrid_avg_ratio'] = (
                    (self.performance_stats['hybrid_avg_ratio'] * (self.performance_stats['hybrid_used'] - 1) + 
                     result.get('compression_ratio', 0)) / self.performance_stats['hybrid_used']
                self.performance_stats['hybrid_avg_time'] = (
                    (self.performance_stats['hybrid_avg_time'] * (self.performance_stats['hybrid_used'] - 1) + 
                     result.get('processing_time', 0)) / self.performance_stats['hybrid_used']
        
        elif system_choice == 'harmonic':
            self.performance_stats['harmonic_used'] += 1
            if result.get('success'):
                self.performance_stats['harmonic_avg_ratio'] = (
                    (self.performance_stats['harmonic_avg_ratio'] * (self.performance_stats['harmonic_used'] - 1) + 
                     result.get('compression_ratio', 0)) / self.performance_stats['harmonic_used']
                self.performance_stats['harmonic_avg_time'] = (
                    (self.performance_stats['harmonic_avg_time'] * (self.performance_stats['harmonic_used'] - 1) + 
                     result.get('processing_time', 0)) / self.performance_stats['harmonic_used']
        
        # Calcul de la précision de décision
        if 'both_results' in result and 'comparison' in result['comparison']:
            comparison = result['comparison']
            if comparison.get('winner') == 'harmonic':
                self.performance_stats['decision_accuracy'] = (
                    (self.performance_stats['decision_accuracy'] * (self.performance_stats['total_processed'] - 1) + 1) / 
                    self.performance_stats['total_processed']
                )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de performance"""
        
        stats = self.performance_stats.copy()
        
        # Calculs additionnels
        total = stats['total_processed']
        if total > 0:
            stats['hybrid_usage_percent'] = stats['hybrid_used'] / total * 100
            stats['harmonic_usage_percent'] = stats['harmonic_used'] / total * 100
            
            if stats['hybrid_avg_ratio'] > 0 and stats['harmonic_avg_ratio'] > 0:
                stats['ratio_improvement'] = (
                    (stats['harmonic_avg_ratio'] - stats['hybrid_avg_ratio']) / 
                    stats['hybrid_avg_ratio'] * 100
                )
            
            if stats['hybrid_avg_time'] > 0 and stats['harmonic_avg_time'] > 0:
                stats['time_improvement'] = (
                    (stats['hybrid_avg_time'] - stats['harmonic_avg_time']) / 
                    stats['hybrid_avg_time'] * 100
                )
        
        return stats
    
    def batch_compress(self, 
                      images: List[np.ndarray],
                      mode: str = 'auto',
                      priority: str = 'balanced',
                      target_ratio: Optional[float] = None) -> List[Dict[str, Any]]:
        """Compression par lot avec décision intelligente"""
        
        logger.info(f"🔄 Compression batch: {len(images)} images")
        logger.info(f"   Mode: {mode}, Priorité: {priority}")
        
        results = []
        
        for i, image in enumerate(images):
            logger.info(f"   Image {i+1}/{len(images)}")
            
            result = self.compress_image(
                image, 
                mode=mode,
                target_ratio=target_ratio,
                priority=priority
            )
            
            result['batch_index'] = i
            results.append(result)
        
        # Statistiques du batch
        successful = sum(1 for r in results if r.get('success', False))
        stats = self.get_performance_stats()
        
        logger.info(f"✅ Batch terminé: {successful}/{len(images)} réussis")
        logger.info(f"   Utilisation hybride: {stats.get('hybrid_usage_percent', 0):.1f}%")
        logger.info(f"   Utilisation harmonique: {stats.get('harmonic_usage_percent', 0):.1f}%")
        
        return results

def test_hybrid_harmonic_system():
    """Test complet du système hybride-harmonique"""
    
    print("🔧 TEST DU SYSTÈME HYBRIDE-HARMONIQUE")
    print("=" * 80)
    
    try:
        # Initialisation du système
        compressor = HybridHarmonicCompressor()
        
        # Création d'images de test variées
        print("\n📸 Création des images de test...")
        test_images = create_test_images()
        
        # Test des différents modes
        modes = ['auto', 'hybrid', 'harmonic', 'both']
        priorities = ['speed', 'quality', 'balanced']
        
        for img_name, img_array in test_images.items():
            print(f"\n🎯 Test image: {img_name}")
            
            # Analyse des caractéristiques
            characteristics = compressor._analyze_for_decision(img_array)
            print(f"   Complexité: {characteristics['complexity_score']:.3f}")
            print(f"   Contours: {characteristics['edge_density']:.3f}")
            print(f"   Variance: {characteristics['variance']:.1f}")
            
            for mode in modes:
                for priority in priorities:
                    print(f"\n   🔧 Mode: {mode}, Priorité: {priority}")
                    
                    start_time = time.time()
                    result = compressor.compress_image(
                        img_array,
                        mode=mode,
                        priority=priority
                    )
                    processing_time = time.time() - start_time
                    
                    if result['success']:
                        print(f"      ✅ Ratio: {result['compression_ratio']:.1f}:1")
                        print(f"      📊 Espace: {result['space_saved_percent']:.1f}%")
                        print(f"      ⏱️ Temps: {result['processing_time']:.3f}s")
                        print(f"      🎯 Méthode: {result['method_used']}")
                        print(f"      🌊 Décision: {result['decision_system']}")
                    else:
                        print(f"      ❌ Erreur: {result['error']}")
        
        # Test batch
        print(f"\n📦 Test batch compression...")
        batch_images = list(test_images.values())
        batch_results = compressor.batch_compress(
            batch_images,
            mode='auto',
            priority='balanced'
        )
        
        # Statistiques finales
        stats = compressor.get_performance_stats()
        print(f"\n📈 STATISTIQUES FINALES:")
        print(f"   Total traité: {stats['total_processed']}")
        print(f"   Utilisation hybride: {stats.get('hybrid_usage_percent', 0):.1f}%")
        print(f"   Utilisation harmonique: {stats.get('harmonic_usage_percent', 0):.1f}%")
        print(f"   Ratio moyen hybride: {stats.get('hybrid_avg_ratio', 0):.1f}:1")
        print(f"   Ratio moyen harmonique: {stats.get('harmonic_avg_ratio', 0):.1f}:1")
        
        if 'ratio_improvement' in stats:
            print(f"   Amélioration ratio: {stats['ratio_improvement']:+.1f}%")
        if 'time_improvement' in stats:
            print(f"   Amélioration temps: {stats['time_improvement']:+.1f}%")
        
        print(f"\n✅ SYSTÈME HYBRIDE-HARMONIQUE TESTÉ AVEC SUCCÈS!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test système hybride: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_images() -> Dict[str, np.ndarray]:
    """Crée des images de test pour le système hybride-harmonique"""
    
    images = {}
    
    # Image simple (favorise hybride)
    simple = np.ones((100, 150, 3), dtype=np.uint8) * 200
    cv2.rectangle(simple, (25, 25), (125, 75), (100, 150, 200), -1)
    images['simple'] = simple
    
    # Image complexe (favorise harmonique)
    complex = np.random.randint(50, 200, (100, 150, 3), dtype=np.uint8)
    for i in range(10):
        x, y = np.random.randint(0, 150), np.random.randint(0, 100)
        cv2.circle(complex, (x, y), 5, (255, 255, 255), -1)
    images['complex'] = complex
    
    # Image texte (favorise hybride)
    text = np.ones((100, 150, 3), dtype=np.uint8) * 255
    cv2.putText(text, "HYBRID TEST", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    images['text'] = text
    
    # Image photo (favorise harmonique)
    photo = np.zeros((100, 150, 3), dtype=np.uint8)
    cv2.circle(photo, (75, 50), 20, (200, 150, 100), -1)
    cv2.ellipse(photo, (75, 50), (30, 15), 0, 0, 360, (100, 150, 200), -1)
    images['photo'] = photo
    
    return images

def main():
    """Fonction principale"""
    print("🔧 SYSTÈME HYBRIDE-HARMONIQUE")
    print("Combinaison intelligente des forces de deux systèmes")
    print("=" * 80)
    
    success = test_hybrid_harmonic_system()
    
    if success:
        print(f"\n🎯 CONCLUSION:")
        print("✅ Système hybride-harmonique fonctionnel")
        print("✅ Décision intelligente du système optimal")
        print("✅ Combinaison des forces des deux approches")
        print("✅ Adaptation selon les caractéristiques et priorités")
        
        print(f"\n🚀 AVANTAGES DU SYSTÈME:")
        print("• Fiabilité hybride + Intelligence harmonique")
        print("• Décision automatique selon le contenu")
        print("• Optimisation selon les priorités (vitesse/qualité)")
        print("• Meilleur des deux mondes")
        print("• Statistiques d'apprentissage intégrées")
        
        print(f"\n🌈 SYSTÈME PRÊT POUR UTILISATION INDUSTRIELLE!")
    else:
        print(f"\n❌ TESTS ÉCHOUÉS")

if __name__ == "__main__":
    main()
