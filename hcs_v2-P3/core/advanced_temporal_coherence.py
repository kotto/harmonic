#!/usr/bin/env python3
"""
Module de Cohérence Temporelle Avancée pour l'Upscaling Vidéo Quantique-Harmonique
Buffer temporel, Optical Flow Integration, Motion Compensation
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from collections import deque
import time

@dataclass
class TemporalFrame:
    """Frame avec métadonnées temporelles"""
    frame: np.ndarray
    timestamp: float
    frame_number: int
    optical_flow: Optional[np.ndarray] = None
    motion_vectors: Optional[np.ndarray] = None
    harmonic_features: Optional[Dict[str, float]] = None

@dataclass
class MotionField:
    """Champ de mouvement entre frames"""
    forward_flow: np.ndarray  # Flow frame t → t+1
    backward_flow: np.ndarray  # Flow frame t+1 → t
    confidence: np.ndarray  # Confiance du flow
    motion_magnitude: np.ndarray  # Magnitude du mouvement
    motion_angle: np.ndarray  # Direction du mouvement

class AdvancedTemporalCoherence:
    """Système avancé de cohérence temporelle"""
    
    def __init__(self, buffer_size: int = 5, enable_optical_flow: bool = True):
        self.buffer_size = buffer_size
        self.enable_optical_flow = enable_optical_flow
        
        # Buffer temporel circulaire
        self.temporal_buffer = deque(maxlen=buffer_size)
        
        # Configuration optical flow
        # Note: cv2.optflow n'est pas disponible dans toutes les versions d'OpenCV
        # Utilisation de la méthode standard Farneback
        self.optical_flow_params = dict(
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0
        )
        
        # Cache pour optimisation
        self.flow_cache = {}
        self.harmonic_cache = {}
        
    def add_frame(self, frame: np.ndarray, frame_number: int) -> TemporalFrame:
        """Ajoute une frame au buffer temporel avec analyse complète"""
        timestamp = time.time()
        
        # Création de l'objet TemporalFrame
        temporal_frame = TemporalFrame(
            frame=frame.copy(),
            timestamp=timestamp,
            frame_number=frame_number
        )
        
        # Calcul des caractéristiques temporelles
        if len(self.temporal_buffer) > 0:
            temporal_frame = self._analyze_temporal_features(temporal_frame)
        
        # Ajout au buffer
        self.temporal_buffer.append(temporal_frame)
        
        # Calcul des optical flows si buffer suffisamment rempli
        if len(self.temporal_buffer) >= 2 and self.enable_optical_flow:
            self._update_optical_flows()
        
        return temporal_frame
    
    def _analyze_temporal_features(self, current_frame: TemporalFrame) -> TemporalFrame:
        """Analyse les caractéristiques temporelles de la frame"""
        if len(self.temporal_buffer) == 0:
            return current_frame
        
        # Frame précédente pour comparaison
        prev_frame = self.temporal_buffer[-1]
        
        # Conversion en niveaux de gris pour les calculs
        prev_gray = cv2.cvtColor(prev_frame.frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(current_frame.frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Caractéristiques harmoniques temporelles
        harmonic_features = self._compute_harmonic_temporal_features(prev_gray, curr_gray)
        current_frame.harmonic_features = harmonic_features
        
        # 2. Optical flow (si activé)
        if self.enable_optical_flow:
            flow = self._compute_optical_flow(prev_gray, curr_gray)
            current_frame.optical_flow = flow
            
            # Extraction des vecteurs de mouvement
            motion_vectors = self._extract_motion_vectors(flow)
            current_frame.motion_vectors = motion_vectors
        
        return current_frame
    
    def _compute_harmonic_temporal_features(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> Dict[str, float]:
        """Calcule les caractéristiques harmoniques temporelles"""
        
        # Différence frame par frame
        diff = cv2.absdiff(prev_gray, curr_gray)
        
        # Transformée de Fourier pour analyse fréquentielle
        prev_fft = np.fft.fft2(prev_gray)
        curr_fft = np.fft.fft2(curr_gray)
        
        # Analyse de cohérence harmonique
        coherence = np.abs(prev_fft * np.conj(curr_fft)) / (np.abs(prev_fft) * np.abs(curr_fft) + 1e-10)
        harmonic_coherence = np.mean(coherence)
        
        # Détection de patterns périodiques
        diff_fft = np.fft.fft2(diff.astype(np.float32))
        periodic_energy = np.sum(np.abs(diff_fft[1:10, 1:10]))  # Basses fréquences
        
        # Symétrie temporelle
        symmetry_score = self._compute_temporal_symmetry(prev_gray, curr_gray)
        
        # Entropie temporelle
        temporal_entropy = self._compute_temporal_entropy(diff)
        
        return {
            'harmonic_coherence': float(harmonic_coherence),
            'periodic_energy': float(periodic_energy),
            'temporal_symmetry': float(symmetry_score),
            'temporal_entropy': float(temporal_entropy),
            'motion_intensity': float(np.mean(diff) / 255.0)
        }
    
    def _compute_temporal_symmetry(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> float:
        """Calcule la symétrie temporelle entre deux frames"""
        # Gradient symétrique
        prev_grad_x = cv2.Sobel(prev_gray, cv2.CV_64F, 1, 0, ksize=3)
        prev_grad_y = cv2.Sobel(prev_gray, cv2.CV_64F, 0, 1, ksize=3)
        curr_grad_x = cv2.Sobel(curr_gray, cv2.CV_64F, 1, 0, ksize=3)
        curr_grad_y = cv2.Sobel(curr_gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Symétrie des gradients
        grad_sym_x = 1.0 - np.mean(np.abs(prev_grad_x - curr_grad_x)) / 255.0
        grad_sym_y = 1.0 - np.mean(np.abs(prev_grad_y - curr_grad_y)) / 255.0
        
        return (grad_sym_x + grad_sym_y) / 2.0
    
    def _compute_temporal_entropy(self, diff: np.ndarray) -> float:
        """Calcule l'entropie temporelle de la différence"""
        hist = cv2.calcHist([diff], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()
        hist = hist[hist > 0]  # Éviter log(0)
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        return entropy / 8.0  # Normalisation
    
    def _compute_optical_flow(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> np.ndarray:
        """Calcule l'optical flow entre deux frames"""
        try:
            # Utilisation de Farneback (disponible dans toutes les versions)
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, curr_gray, None, 
                **self.optical_flow_params
            )
            return flow
        except Exception as e:
            print(f"Warning: Optical flow calculation failed: {e}")
            # Retourner un flow nul en cas d'erreur
            return np.zeros((prev_gray.shape[0], prev_gray.shape[1], 2), dtype=np.float32)
    
    def _extract_motion_vectors(self, flow: np.ndarray) -> np.ndarray:
        """Extrait les vecteurs de mouvement significatifs"""
        # Calcul de magnitude et direction
        magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        
        # Seuillage pour ne garder que les mouvements significatifs
        threshold = np.percentile(magnitude, 75)  # Top 25% des mouvements
        significant_motion = magnitude > threshold
        
        # Création des vecteurs de mouvement
        motion_vectors = np.zeros_like(flow)
        motion_vectors[significant_motion] = flow[significant_motion]
        
        return motion_vectors
    
    def _update_optical_flows(self):
        """Met à jour les optical flows dans le buffer"""
        if len(self.temporal_buffer) < 2:
            return
        
        # Mise à jour des flows entre frames consécutives
        for i in range(len(self.temporal_buffer) - 1):
            curr_frame = self.temporal_buffer[i]
            next_frame = self.temporal_buffer[i + 1]
            
            # Calcul du flow forward
            if curr_frame.optical_flow is None:
                prev_gray = cv2.cvtColor(curr_frame.frame, cv2.COLOR_BGR2GRAY)
                next_gray = cv2.cvtColor(next_frame.frame, cv2.COLOR_BGR2GRAY)
                flow = self._compute_optical_flow(prev_gray, next_gray)
                curr_frame.optical_flow = flow
    
    def get_temporal_context(self, target_frame_number: int) -> Dict[str, Any]:
        """Récupère le contexte temporel pour une frame cible"""
        if not self.temporal_buffer:
            return {}
        
        # Trouver la frame cible dans le buffer
        target_frame = None
        target_index = -1
        
        for i, frame in enumerate(self.temporal_buffer):
            if frame.frame_number == target_frame_number:
                target_frame = frame
                target_index = i
                break
        
        if target_frame is None:
            return {}
        
        # Contexte temporel
        context = {
            'target_frame': target_frame,
            'buffer_position': target_index,
            'total_frames': len(self.temporal_buffer),
            'previous_frames': [],
            'next_frames': [],
            'motion_field': None,
            'harmonic_trend': None
        }
        
        # Frames précédentes
        for i in range(target_index):
            context['previous_frames'].append(self.temporal_buffer[i])
        
        # Frames suivantes
        for i in range(target_index + 1, len(self.temporal_buffer)):
            context['next_frames'].append(self.temporal_buffer[i])
        
        # Champ de mouvement
        if target_frame.optical_flow is not None:
            context['motion_field'] = MotionField(
                forward_flow=target_frame.optical_flow,
                backward_flow=None,  # Pourrait être calculé
                confidence=np.ones_like(target_frame.optical_flow[..., 0]),
                motion_magnitude=np.sqrt(target_frame.optical_flow[..., 0]**2 + target_frame.optical_flow[..., 1]**2),
                motion_angle=np.arctan2(target_frame.optical_flow[..., 1], target_frame.optical_flow[..., 0])
            )
        
        # Tendance harmonique
        if len(self.temporal_buffer) >= 3:
            context['harmonic_trend'] = self._compute_harmonic_trend()
        
        return context
    
    def _compute_harmonic_trend(self) -> Dict[str, float]:
        """Calcule la tendance harmonique sur le buffer temporel"""
        if len(self.temporal_buffer) < 3:
            return {}
        
        # Extraction des caractéristiques harmoniques
        harmonic_values = []
        for frame in self.temporal_buffer:
            if frame.harmonic_features:
                harmonic_values.append(frame.harmonic_features)
        
        if not harmonic_values:
            return {}
        
        # Calcul des tendances
        trends = {}
        for key in harmonic_values[0].keys():
            values = [h[key] for h in harmonic_values]
            
            # Tendance linéaire
            if len(values) >= 2:
                x = np.arange(len(values))
                coeffs = np.polyfit(x, values, 1)
                trends[f'{key}_trend'] = float(coeffs[0])  # Pente
                trends[f'{key}_mean'] = float(np.mean(values))
                trends[f'{key}_std'] = float(np.std(values))
        
        return trends
    
    def apply_motion_compensation(self, frame: np.ndarray, motion_field: MotionField, 
                               compensation_strength: float = 0.5) -> np.ndarray:
        """Applique la compensation de mouvement à une frame"""
        if motion_field is None or motion_field.forward_flow is None:
            return frame
        
        # Création de la carte de remapping
        h, w = frame.shape[:2]
        map_x, map_y = np.meshgrid(np.arange(w), np.arange(h))
        
        # Application du flow avec compensation
        compensated_x = map_x + motion_field.forward_flow[..., 0] * compensation_strength
        compensated_y = map_y + motion_field.forward_flow[..., 1] * compensation_strength
        
        # Remapping de l'image
        compensated_frame = cv2.remap(
            frame, 
            compensated_x.astype(np.float32), 
            compensated_y.astype(np.float32),
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT
        )
        
        return compensated_frame
    
    def enhance_temporal_coherence(self, frame: np.ndarray, 
                                 temporal_context: Dict[str, Any]) -> np.ndarray:
        """Améliore la cohérence temporelle d'une frame"""
        if not temporal_context:
            return frame
        
        enhanced_frame = frame.copy()
        
        # 1. Compensation de mouvement
        if 'motion_field' in temporal_context and temporal_context['motion_field']:
            enhanced_frame = self.apply_motion_compensation(
                enhanced_frame, 
                temporal_context['motion_field'],
                compensation_strength=0.3
            )
        
        # 2. Fusion temporelle harmonique
        if 'previous_frames' in temporal_context and temporal_context['previous_frames']:
            enhanced_frame = self._apply_harmonic_temporal_fusion(
                enhanced_frame,
                temporal_context['previous_frames']
            )
        
        # 3. Stabilisation harmonique
        if 'harmonic_trend' in temporal_context and temporal_context['harmonic_trend']:
            enhanced_frame = self._apply_harmonic_stabilization(
                enhanced_frame,
                temporal_context['harmonic_trend']
            )
        
        return enhanced_frame
    
    def _apply_harmonic_temporal_fusion(self, current_frame: np.ndarray, 
                                     previous_frames: List[TemporalFrame]) -> np.ndarray:
        """Applique une fusion temporelle basée sur les principes harmoniques"""
        if not previous_frames:
            return current_frame
        
        # Pondération harmonique basée sur la cohérence
        weights = []
        frames_to_fuse = [current_frame]
        
        for prev_frame in previous_frames[-2:]:  # 2 frames précédentes max
            if prev_frame.harmonic_features:
                # Poids basé sur la cohérence harmonique
                coherence = prev_frame.harmonic_features.get('harmonic_coherence', 0.5)
                weight = coherence * 0.3  # Facteur de fusion temporel
                weights.append(weight)
                frames_to_fuse.append(prev_frame.frame)
        
        if len(frames_to_fuse) <= 1:
            return current_frame
        
        # Normalisation des poids
        weights = [1.0] + weights  # Frame actuelle avec poids 1.0
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Fusion pondérée
        fused_frame = np.zeros_like(current_frame, dtype=np.float32)
        for i, (frame, weight) in enumerate(zip(frames_to_fuse, weights)):
            fused_frame += frame.astype(np.float32) * weight
        
        return fused_frame.astype(np.uint8)
    
    def _apply_harmonic_stabilization(self, frame: np.ndarray, 
                                  harmonic_trend: Dict[str, float]) -> np.ndarray:
        """Applique une stabilisation basée sur les tendances harmoniques"""
        stabilized = frame.copy().astype(np.float32)
        
        # Application de corrections basées sur les tendances
        for key, trend_value in harmonic_trend.items():
            if key.endswith('_trend'):
                feature_name = key.replace('_trend', '')
                
                # Correction douce basée sur la tendance
                if abs(trend_value) > 0.01:  # Seuil de correction
                    correction_factor = 1.0 - np.clip(trend_value * 0.1, -0.1, 0.1)
                    
                    if 'coherence' in feature_name:
                        # Amélioration de la cohérence
                        stabilized = self._enhance_coherence(stabilized, correction_factor)
                    elif 'symmetry' in feature_name:
                        # Amélioration de la symétrie
                        stabilized = self._enhance_symmetry(stabilized, correction_factor)
        
        return stabilized.astype(np.uint8)
    
    def _enhance_coherence(self, frame: np.ndarray, factor: float) -> np.ndarray:
        """Améliore la cohérence spatiale/temporelle"""
        # Filtre bilateral pour préserver les edges tout en lissant
        enhanced = cv2.bilateralFilter(frame, 9, 75, 75)
        
        # Fusion avec l'original selon le facteur
        return frame * (1.0 - factor) + enhanced * factor
    
    def _enhance_symmetry(self, frame: np.ndarray, factor: float) -> np.ndarray:
        """Améliore la symétrie harmonique"""
        # Application de filtres symétriques
        kernel = np.array([
            [0.1, 0.1, 0.1],
            [0.1, 0.2, 0.1],
            [0.1, 0.1, 0.1]
        ])
        
        enhanced = cv2.filter2D(frame, -1, kernel)
        return frame * (1.0 - factor) + enhanced * factor
    
    def get_buffer_status(self) -> Dict[str, Any]:
        """Retourne le statut du buffer temporel"""
        return {
            'buffer_size': len(self.temporal_buffer),
            'max_buffer_size': self.buffer_size,
            'frame_numbers': [f.frame_number for f in self.temporal_buffer],
            'has_optical_flow': self.enable_optical_flow,
            'cached_flows': len(self.flow_cache),
            'harmonic_features_available': all(f.harmonic_features is not None for f in self.temporal_buffer)
        }
    
    def clear_buffer(self):
        """Vide le buffer temporel"""
        self.temporal_buffer.clear()
        self.flow_cache.clear()
        self.harmonic_cache.clear()

# Test et démonstration
def test_advanced_temporal_coherence():
    """Test du module de cohérence temporelle avancée"""
    print("🌊 TEST DE COHÉRENCE TEMPORELLE AVANCÉE")
    print("=" * 60)
    
    # Création du système
    temporal_system = AdvancedTemporalCoherence(buffer_size=5, enable_optical_flow=True)
    
    # Simulation de frames
    test_frames = []
    for i in range(10):
        # Création de frame test avec mouvement
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        
        # Ajout de mouvement simulé
        offset = int(10 * np.sin(i * 0.5))
        if offset > 0:
            frame[:, offset:] = frame[:, :-offset]
        
        test_frames.append(frame)
    
    print(f"📊 Test avec {len(test_frames)} frames")
    
    # Traitement des frames
    for i, frame in enumerate(test_frames):
        temporal_frame = temporal_system.add_frame(frame, i)
        
        print(f"Frame {i}:")
        if temporal_frame.harmonic_features:
            features = temporal_frame.harmonic_features
            print(f"  🌊 Cohérence: {features.get('harmonic_coherence', 0):.3f}")
            print(f"  🔄 Symétrie: {features.get('temporal_symmetry', 0):.3f}")
            print(f"  📈 Entropie: {features.get('temporal_entropy', 0):.3f}")
        
        if i == 5:  # Test du contexte temporel au milieu
            context = temporal_system.get_temporal_context(i)
            print(f"  📦 Contexte: {len(context.get('previous_frames', []))} précédentes, {len(context.get('next_frames', []))} suivantes")
    
    # Statut final
    status = temporal_system.get_buffer_status()
    print(f"\n📊 Statut final du buffer:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Test de cohérence temporelle avancée terminé!")

if __name__ == "__main__":
    test_advanced_temporal_coherence()
