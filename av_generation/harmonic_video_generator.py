#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GÉNÉRATEUR DE VIDÉOS HARMONIQUES
==================================
Basé sur la Théorie Harmonique : Ψ(t) = Σ Hₙ (Ψ₁(t))ⁿ

Génère des animations fluides en faisant évoluer Ψ₁ dans le temps.
Chaque Hₙ gouverne un aspect du mouvement temporel :
  H₁ (φ)   → cadence d'évolution (vitesse dorée)
  H₂ (π)   → boucle périodique (retour cyclique)
  H₃ (e)   → fondu exponentiel (transitions douces)
  H₄ (√2)  → symétrie temporelle (mouvements plans)
  H₅ (√3)  → parallaxe 3D (profondeur animée)
  H₆ (√5)  → micro-mouvements (tremblements fins)
  H₇ (e/π) → rotation spirale (mouvements organiques)

Usage :
  python harmonic_video_generator.py --demo
  python harmonic_video_generator.py --seed 42 --duration 5 --fps 30 --style cosmique
"""

import numpy as np
import math
import sys
import os
import argparse
import time
import subprocess
from typing import Dict, Any, List, Optional, Tuple, Generator
from dataclasses import dataclass, field
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    HarmonicField, HarmonicColorMapper,
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
    H_CONSTANTS, H_NAMES, H_ROLES_VIDEO,
    normalize_field, SeedManager,
    compute_harmonic_coherence, compute_symmetry_score
)
from harmonic_image_generator import (
    HarmonicImageGenerator, create_mandala, save_as_png
)


class HarmonicVideoGenerator:
    """
    Générateur de vidéos harmoniques.
    
    Le temps t fait évoluer Ψ₁ via des modulations basées sur les 7 constantes.
    À chaque frame, un nouveau Ψ(t) est calculé, puis converti en RGB.
    """
    
    def __init__(self, width: int = 512, height: int = 512,
                 fps: int = 30, duration: float = 5.0,
                 seed: int = 42):
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.n_frames = int(fps * duration)
        self.base_seed = seed
        
        # Générateur d'images sous-jacent
        self.img_gen = HarmonicImageGenerator(width=width, height=height, seed=seed)
        
        # Paramètres temporels
        self._time_params = self._compute_time_params()
    
    def _compute_time_params(self) -> Dict[str, float]:
        """Calcule les paramètres temporels basés sur les Hₙ."""
        return {
            'phi_speed': 0.5 * PHI_INV,        # Vitesse d'évolution dorée (~0.3)
            'pi_cycle': 1.0,                     # Période du cycle π
            'e_decay': 0.1,                      # Taux d'amortissement
            'sqrt2_phase': PI / 4,               # Déphasage planaire
            'sqrt3_parallax': 0.05,              # Amplitude parallaxe
            'sqrt5_micro': 0.02,                 # Amplitude micro-mouvements
            'epi_spiral_speed': E_PI * 0.3,      # Vitesse de spirale
        }
    
    def get_frame(self, frame_idx: int) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Calcule une frame vidéo harmonique.
        
        Args:
            frame_idx: Index de la frame (0 à n_frames-1)
        
        Returns:
            (rgb_array, frame_metadata)
        """
        t = frame_idx / self.fps  # Temps en secondes
        t_norm = t / self.duration  # Temps normalisé [0, 1]
        
        # Faire évoluer Ψ₁ dans le temps
        seed_t = SeedManager.compose_seed(self.base_seed, 1, frame_idx)
        field_t = HarmonicField(
            width=self.width, height=self.height,
            seed=seed_t, n_layers=7
        )
        
        # Obtenir le champ de base
        psi_base = field_t.get_psi_total()
        
        # Modulations temporelles basées sur les Hₙ
        psi_modulated = self._apply_temporal_modulations(psi_base, t, t_norm, field_t)
        
        # Style qui évolue aussi légèrement
        style_idx = int((t_norm * PHI * 7) % 7)
        styles = list(HarmonicColorMapper.PALETTES.keys())
        style = styles[style_idx]
        
        # Conversion RGB
        rgb = HarmonicColorMapper.harmonic_hsl(psi_modulated, palette=style)
        
        metadata = {
            'frame': frame_idx,
            'time': t,
            'time_norm': t_norm,
            'style': style,
            'coherence': compute_harmonic_coherence(psi_modulated),
            'symmetry': compute_symmetry_score(psi_modulated),
            'seed_frame': seed_t,
        }
        
        return rgb, metadata
    
    def _apply_temporal_modulations(self, psi: np.ndarray, t: float,
                                     t_norm: float,
                                     field: HarmonicField) -> np.ndarray:
        """
        Applique les 7 modulations temporelles basées sur Hₙ.
        
        Chaque Hₙ module une propriété différente du champ.
        """
        tp = self._time_params
        h, w = psi.shape
        
        Y, X = np.ogrid[:h, :w]
        X_norm = X / w * 2 - 1
        Y_norm = Y / h * 2 - 1
        R = np.sqrt(X_norm**2 + Y_norm**2)
        theta = np.arctan2(Y_norm, X_norm)
        
        # H₁ (φ) : Rotation globale à vitesse dorée
        rot_angle = t * tp['phi_speed'] * 2 * PI
        psi_t = psi * np.cos(rot_angle)  # Modulation d'amplitude lente
        
        # H₂ (π) : Cycle périodique sinusoïdal
        cycle = np.sin(t * 2 * PI / tp['pi_cycle'])
        psi_t = psi_t * (0.7 + 0.3 * cycle)
        
        # H₃ (e) : Amortissement exponentiel selon R
        decay = np.exp(-R * tp['e_decay'] * (1 + 0.5 * np.sin(t * 2 * PI)))
        psi_t = psi_t * decay
        
        # H₄ (√2) : Ondulation planaire horizontale
        wave_h = np.cos(X_norm * 5 * SQRT2 + t * PI)
        psi_t = psi_t + 0.15 * wave_h * np.abs(psi)
        
        # H₅ (√3) : Parallaxe (déplacement 3D simulé)
        parallax_x = np.sin(t * PI * 0.7) * tp['sqrt3_parallax']
        parallax_y = np.cos(t * PI * 0.7) * tp['sqrt3_parallax']
        Y_shift = Y_norm + parallax_y
        X_shift = X_norm + parallax_x
        # Effet de flou directionnel simple
        blur = np.exp(-(X_shift**2 + Y_shift**2) * 2)
        psi_t = psi_t * (0.9 + 0.1 * blur)
        
        # H₆ (√5) : Micro-mouvements (tremblement haute fréquence)
        micro = np.sin(X_norm * 30 * SQRT5 + t * 20) * np.cos(Y_norm * 30 * SQRT5 + t * 20)
        psi_t = psi_t + micro * tp['sqrt5_micro']
        
        # H₇ (e/π) : Spirale de synthèse organique
        spiral_angle = theta + t * tp['epi_spiral_speed']
        spiral_mod = np.sin(R * 15 * E_PI + spiral_angle * 7)
        psi_t = psi_t + 0.1 * spiral_mod * (1.0 - t_norm * 0.5)  # S'atténue avec le temps
        
        return normalize_field(psi_t)
    
    def generate_frames(self, style: str = 'cosmique',
                        progress_callback=None) -> Generator[Tuple[np.ndarray, Dict], None, None]:
        """
        Générateur de frames vidéo.
        
        Yields (rgb_array, metadata) pour chaque frame.
        """
        for i in range(self.n_frames):
            rgb, meta = self.get_frame(i)
            if progress_callback:
                progress_callback(i, self.n_frames)
            yield rgb, meta
    
    def generate_to_directory(self, output_dir: str,
                              style: str = 'cosmique',
                              image_format: str = 'png') -> List[str]:
        """
        Génère toutes les frames et les sauvegarde dans un dossier.
        
        Returns:
            Liste des chemins de fichiers.
        """
        os.makedirs(output_dir, exist_ok=True)
        files = []
        
        for i in range(self.n_frames):
            rgb, meta = self.get_frame(i)
            filename = os.path.join(output_dir, f'frame_{i:06d}.{image_format}')
            save_as_png(rgb, filename)
            files.append(filename)
            
            if i % max(1, self.n_frames // 10) == 0:
                print(f"    Frame {i+1}/{self.n_frames} ({(i+1)/self.n_frames*100:.0f}%)")
        
        return files
    
    def save_video(self, output_path: str, style: str = 'cosmique',
                   codec: str = 'libx264', crf: int = 18):
        """
        Sauvegarde la vidéo en MP4 en utilisant FFmpeg.
        
        Nécessite FFmpeg installé.
        """
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"  Génération des {self.n_frames} frames...")
            frame_files = self.generate_to_directory(tmpdir, style=style)
            
            print(f"  Encodage vidéo avec FFmpeg...")
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(self.fps),
                '-i', os.path.join(tmpdir, 'frame_%06d.png'),
                '-c:v', codec,
                '-crf', str(crf),
                '-pix_fmt', 'yuv420p',
                output_path
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✅ Vidéo sauvegardée : {output_path}")
                    return output_path
                else:
                    print(f"  ⚠️ Erreur FFmpeg : {result.stderr[:500]}")
                    return None
            except FileNotFoundError:
                print(f"  ⚠️ FFmpeg non trouvé. Frames sauvegardées dans : {tmpdir}")
                # Garder les frames
                import shutil
                persistent_dir = output_path.replace('.mp4', '_frames')
                shutil.copytree(tmpdir, persistent_dir)
                print(f"  Frames copiées dans : {persistent_dir}")
                return persistent_dir


class HarmonicEffectGenerator:
    """
    Effets vidéo spéciaux harmoniques.
    
    Effets disponibles :
      - 'morph'     : Transformation continue entre deux seeds
      - 'pulse'     : Pulsation de lumière harmonique
      - 'kaleidoscope' : Effet kaléidoscopique temporel
      - 'flow'      : Flux de champ harmonique
    """
    
    @staticmethod
    def morph_effect(width: int, height: int, fps: int, duration: float,
                     seed_a: int, seed_b: int) -> Generator[np.ndarray, None, None]:
        """Morphing continu entre deux champs harmoniques."""
        field_a = HarmonicField(width=width, height=height, seed=seed_a)
        field_b = HarmonicField(width=width, height=height, seed=seed_b)
        
        psi_a = field_a.get_psi_total()
        psi_b = field_b.get_psi_total()
        
        n_frames = int(fps * duration)
        
        for i in range(n_frames):
            t = i / (n_frames - 1) if n_frames > 1 else 0.5
            # Interpolation non-linéaire basée sur φ
            alpha = 1.0 / (1.0 + np.exp(-(t - 0.5) * PHI * 5))
            
            psi_morph = alpha * psi_a + (1 - alpha) * psi_b
            psi_morph = normalize_field(psi_morph)
            
            rgb = HarmonicColorMapper.harmonic_hsl(psi_morph, palette='aurore')
            yield rgb
    
    @staticmethod
    def pulse_effect(gen: HarmonicImageGenerator, width: int, height: int,
                     fps: int, duration: float) -> Generator[np.ndarray, None, None]:
        """Pulsation harmonique : le champ respire."""
        field = HarmonicField(width=width, height=height, seed=gen.seed)
        base_psi = field.get_psi_total()
        
        n_frames = int(fps * duration)
        
        for i in range(n_frames):
            t = i / fps
            # Pulsation basée sur le cycle cardiaque (π)
            pulse = 1.0 + 0.3 * np.sin(t * PI * 1.5) * np.exp(-0.1 * t)
            # Tremblement haute fréquence (√5)
            tremble = 1.0 + 0.05 * np.sin(t * 20 * SQRT5)
            
            psi_pulsed = base_psi * pulse * tremble
            psi_pulsed = normalize_field(psi_pulsed)
            
            rgb = HarmonicColorMapper.harmonic_hsl(psi_pulsed, palette='solaire')
            yield rgb
    
    @staticmethod
    def kaleidoscope_effect(field: HarmonicField, width: int, height: int,
                            fps: int, duration: float,
                            n_segments: int = 8) -> Generator[np.ndarray, None, None]:
        """Effet kaléidoscopique temporel."""
        psi = field.get_psi_total()
        center_x, center_y = width // 2, height // 2
        
        n_frames = int(fps * duration)
        
        for i in range(n_frames):
            t = i / fps
            angle = t * PI * 0.5  # Rotation lente
            
            # Créer l'image kaléidoscopique
            result = np.zeros((height, width), dtype=np.float64)
            
            for seg in range(n_segments):
                seg_angle = seg * 2 * PI / n_segments + angle
                
                # Rotation du champ source
                cos_a, sin_a = np.cos(seg_angle), np.sin(seg_angle)
                
                for y in range(height):
                    for x in range(width):
                        dx = x - center_x
                        dy = y - center_y
                        src_x = int(center_x + dx * cos_a - dy * sin_a)
                        src_y = int(center_y + dx * sin_a + dy * cos_a)
                        
                        if 0 <= src_x < width and 0 <= src_y < height:
                            result[y, x] = psi[src_y, src_x]
            
            result = normalize_field(result)
            rgb = HarmonicColorMapper.harmonic_hsl(result, palette='ocean')
            yield rgb
    
    @staticmethod
    def flow_effect(width: int, height: int, fps: int, duration: float,
                    seed: int = 42) -> Generator[np.ndarray, None, None]:
        """Flux continu de champ harmonique."""
        base_field = HarmonicField(width=width, height=height, seed=seed)
        
        n_frames = int(fps * duration)
        
        for i in range(n_frames):
            t = i / fps
            
            # Créer un nouveau champ à chaque frame avec évolution du seed
            frame_seed = SeedManager.compose_seed(seed, i % 7 + 1, i)
            frame_field = HarmonicField(width=width, height=height, seed=frame_seed)
            psi = frame_field.get_psi_total()
            
            # Mélanger avec le champ précédent
            if i > 0:
                alpha = np.exp(-t * E_PI)  # Fondu exponentiel
                psi = alpha * psi + (1 - alpha) * base_field.get_psi_total()
            
            psi = normalize_field(psi)
            rgb = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
            yield rgb


# ==============================================================================
# DÉMONSTRATIONS
# ==============================================================================

def demo_video_generator():
    """Démonstration du générateur de vidéos harmoniques."""
    print("=" * 70)
    print("  GÉNÉRATEUR DE VIDÉOS HARMONIQUES")
    print("  Ψ(t) = Σ Hₙ (Ψ₁(t))ⁿ → Animations Structurées")
    print("=" * 70)
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'videos')
    os.makedirs(output_dir, exist_ok=True)
    
    # Test : générer quelques frames et les sauvegarder en GIF
    print(f"\n  [1] Test de génération de frames (2 secondes @ 15fps)...")
    gen = HarmonicVideoGenerator(
        width=256, height=256,
        fps=15, duration=2.0,
        seed=42
    )
    
    frames = list(gen.generate_frames(style='cosmique'))
    
    # Sauvegarder comme GIF
    gif_path = os.path.join(output_dir, 'harmonic_animation.gif')
    pil_frames = [Image.fromarray(f[0], 'RGB') for f in frames]
    pil_frames[0].save(
        gif_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=int(1000 / 15),
        loop=0
    )
    print(f"  ✅ GIF sauvegardé : {gif_path} ({len(frames)} frames)")
    
    # Rapport
    print(f"\n  [2] Rapport de l'animation :")
    coherences = [m['coherence'] for _, m in frames]
    symmetries = [m['symmetry'] for _, m in frames]
    
    print(f"    Cohérence harmonique moyenne : {np.mean(coherences):.4f}")
    print(f"    Cohérence min/max            : {np.min(coherences):.4f} / {np.max(coherences):.4f}")
    print(f"    Symétrie moyenne             : {np.mean(symmetries):.4f}")
    
    # Effets spéciaux
    print(f"\n  [3] Effets spéciaux :")
    
    # Morph
    print(f"    Génération morph (1s)...")
    morph_frames = list(HarmonicEffectGenerator.morph_effect(
        256, 256, 15, 1.0, seed_a=42, seed_b=137
    ))
    morph_path = os.path.join(output_dir, 'harmonic_morph.gif')
    pil_morph = [Image.fromarray(f, 'RGB') for f in morph_frames]
    pil_morph[0].save(morph_path, save_all=True, append_images=pil_morph[1:],
                      duration=67, loop=0)
    print(f"    ✅ Morph sauvegardé : {morph_path}")
    
    # Flow
    print(f"    Génération flow (1s)...")
    flow_frames = list(HarmonicEffectGenerator.flow_effect(
        256, 256, 15, 1.0, seed=42
    ))
    flow_path = os.path.join(output_dir, 'harmonic_flow.gif')
    pil_flow = [Image.fromarray(f, 'RGB') for f in flow_frames]
    pil_flow[0].save(flow_path, save_all=True, append_images=pil_flow[1:],
                     duration=67, loop=0)
    print(f"    ✅ Flow sauvegardé : {flow_path}")
    
    print(f"\n  ✅ Toutes les vidéos sauvegardées dans : {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Générateur de Vidéos Harmoniques')
    parser.add_argument('--demo', action='store_true', help='Démonstration complète')
    parser.add_argument('--seed', type=int, default=42, help='Seed de base')
    parser.add_argument('--duration', type=float, default=5.0, help='Durée en secondes')
    parser.add_argument('--fps', type=int, default=30, help='Images par seconde')
    parser.add_argument('--size', type=int, default=512, help='Taille en pixels')
    parser.add_argument('--style', type=str, default='cosmique', help='Palette')
    parser.add_argument('--output', type=str, default=None, help='Fichier de sortie (.mp4)')
    
    args = parser.parse_args()
    
    if args.output:
        gen = HarmonicVideoGenerator(
            width=args.size, height=args.size,
            fps=args.fps, duration=args.duration,
            seed=args.seed
        )
        gen.save_video(args.output, style=args.style)
    else:
        demo_video_generator()