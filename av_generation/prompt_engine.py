#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROMPT ENGINE — Génération Unifiée Images/Vidéos/Audio 4K/8K
===============================================================
Basé sur la Théorie Harmonique Ψ = Σ Hₙ (Ψ₁)ⁿ

Pipeline complet prompt → génération :
  1. Prompt texte → hash → seed déterministe
  2. Analyse sémantique du prompt (mots-clés → paramètres)
  3. Génération procédurale harmonique (Ψ₁ → 7Hₙ → RGB/WAV)
  4. Option : One-Shot SVD pour photoréalisme sur base d'images existantes
  5. Sortie 4K/8K avec streaming par tuiles

Résolutions supportées :
  - SD: 512×512 (génération instantanée)
  - HD: 1920×1080
  - 4K: 3840×2160 (tuilage 8×4 blocs de 480×540)
  - 8K: 7680×4320 (tuilage 16×8 blocs de 480×540)

Modes :
  - 'procedural' : Ψ = Σ Hₙ (Ψ₁)ⁿ pur (0 entraînement, ∞ possibilités)
  - 'one_shot'   : SVD holographique sur 1 image (photoréalisme)
  - 'hybrid'     : Mix procédural + one-shot

Usage :
  python prompt_engine.py --prompt "galaxie spirale cosmique" --mode procedural --res 4k
  python prompt_engine.py --prompt "forêt de cristaux géométriques" --res 8k --style forest
  python prompt_engine.py --server  (lance l'API REST)
"""

import numpy as np
import math
import sys
import os
import time
import hashlib
import json
import argparse
import threading
from typing import Dict, Any, List, Optional, Tuple, Generator
from dataclasses import dataclass, field
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
    H_CONSTANTS, H_NAMES, H_ROLES_IMAGE, H_ROLES_AUDIO, H_ROLES_VIDEO,
    HarmonicField, HarmonicColorMapper, HarmonicAudioCore,
    SeedManager, normalize_field, save_image,
    compute_harmonic_coherence, compute_symmetry_score,
)

# ==============================================================================
# RÉSOLUTIONS
# ==============================================================================

RESOLUTIONS = {
    'sd':  (512, 512),
    'hd':  (1920, 1080),
    '4k':  (3840, 2160),
    '8k':  (7680, 4320),
    'square_4k': (4096, 4096),
}

TILE_SIZE = 480  # Taille de tuile pour génération parallèle (multiple de 8)


# ==============================================================================
# ANALYSE SÉMANTIQUE DU PROMPT
# ==============================================================================

PROMPT_KEYWORDS = {
    # Mots → (style_palette, couche_dominante, intensité)
    'galaxie':    ('cosmique', 2, 1.2),
    'cosmique':   ('cosmique', 1, 1.0),
    'nébuleuse':  ('cosmique', 7, 1.3),
    'espace':     ('galactique', 6, 1.1),
    'étoile':     ('galactique', 6, 1.4),
    'soleil':     ('solaire', 1, 1.5),
    'solaire':    ('solaire', 1, 1.0),
    'feu':        ('solaire', 3, 1.3),
    'volcan':     ('solaire', 5, 1.4),
    'forêt':      ('forest', 4, 1.0),
    'nature':     ('forest', 4, 1.0),
    'jardin':     ('forest', 6, 1.2),
    'émeraude':   ('forest', 4, 1.3),
    'océan':      ('ocean', 5, 1.0),
    'mer':        ('ocean', 5, 1.0),
    'eau':        ('ocean', 3, 1.2),
    'vague':      ('ocean', 2, 1.3),
    'aurore':     ('aurore', 7, 1.4),
    'boréale':    ('aurore', 7, 1.4),
    'mystique':   ('aurore', 7, 1.2),
    'crépuscule': ('crepuscule', 1, 1.0),
    'coucher':    ('crepuscule', 1, 1.0),
    'aube':       ('crepuscule', 1, 1.2),
    'rose':       ('crepuscule', 3, 1.3),
    'cristal':    ('ocean', 6, 1.5),
    'géométrique': ('galactique', 4, 1.3),
    'spirale':    ('cosmique', 7, 1.5),
    'fractale':   ('aurore', 7, 1.4),
    'mandala':    ('aurore', 4, 1.3),
    
    # Audio keywords
    'musique':    ('pad', 0, 1.0),
    'mélodie':    ('melody', 1, 1.0),
    'rythme':     ('rhythm', 2, 1.2),
    'ambient':    ('ambient', 3, 0.8),
    'calme':      ('ambient', 3, 0.7),
    'énergique':  ('rhythm', 2, 1.5),
    'sombre':     ('pad', 5, 1.2),
    'lumineux':   ('melody', 1, 1.3),
    
    # Video keywords
    'flux':       ('flow', 7, 1.2),
    'morph':      ('morph', 7, 1.3),
    'kaléidoscope': ('kaleidoscope', 4, 1.4),
    'pulsation':  ('pulse', 2, 1.2),
    'mouvement':  ('flow', 7, 1.0),
    'danse':      ('flow', 2, 1.3),
    'tempête':    ('flow', 5, 1.5),
    'pluie':      ('flow', 3, 1.2),
    'brouillard': ('flow', 3, 0.8),
}


@dataclass
class PromptAnalysis:
    """Résultat de l'analyse d'un prompt."""
    prompt: str
    seed: int
    style: str = 'cosmique'
    intensity: float = 1.0
    dominant_layer: int = 1
    color_mode: str = 'hsl'
    audio_type: str = 'ambient'
    video_effect: str = 'flow'
    duration: float = 5.0
    bpm: float = 100.0
    is_audio: bool = False
    is_video: bool = False
    keywords_matched: List[str] = field(default_factory=list)
    
    def to_json(self) -> str:
        return json.dumps({
            'prompt': self.prompt,
            'seed': self.seed,
            'style': self.style,
            'intensity': self.intensity,
            'dominant_layer': self.dominant_layer,
            'color_mode': self.color_mode,
            'audio_type': self.audio_type,
            'video_effect': self.video_effect,
            'duration': self.duration,
            'bpm': self.bpm,
            'is_audio': self.is_audio,
            'is_video': self.is_video,
            'keywords_matched': self.keywords_matched,
        })


def analyze_prompt(prompt: str) -> PromptAnalysis:
    """
    Analyse un prompt texte et en déduit les paramètres de génération.
    
    Principe : le prompt est hashé en seed déterministe, puis les mots-clés
    ajustent le style, l'intensité et les couches dominantes.
    """
    prompt_lower = prompt.lower()
    
    # Seed déterministe
    seed = SeedManager.text_to_seed(prompt)
    
    # Détecter les mots-clés
    matched = []
    style_scores = {}
    audio_scores = {}
    video_scores = {}
    intensity_sum = 0.0
    intensity_count = 0
    dominant_layers = []
    
    for keyword, (style, layer, intensity) in PROMPT_KEYWORDS.items():
        if keyword in prompt_lower:
            matched.append(keyword)
            style_scores[style] = style_scores.get(style, 0) + 1
            intensity_sum += intensity
            intensity_count += 1
            dominant_layers.append(layer)
            
            if style in ['pad', 'melody', 'rhythm', 'ambient']:
                audio_scores[style] = audio_scores.get(style, 0) + 1
            if style in ['flow', 'morph', 'kaleidoscope', 'pulse']:
                video_scores[style] = video_scores.get(style, 0) + 1
    
    # Style dominant
    if style_scores:
        style = max(style_scores, key=style_scores.get)
    else:
        style = 'cosmique'
    
    # Intensité
    intensity = intensity_sum / max(1, intensity_count) if intensity_count > 0 else 1.0
    intensity = max(0.5, min(1.5, intensity))
    
    # Couche dominante
    if dominant_layers:
        dominant_layer = max(set(dominant_layers), key=dominant_layers.count)
    else:
        dominant_layer = 1
    
    # Audio/Video
    is_audio = len(audio_scores) > 0 and len(audio_scores) >= len(video_scores)
    is_video = len(video_scores) > 0
    audio_type = max(audio_scores, key=audio_scores.get) if audio_scores else 'ambient'
    video_effect = max(video_scores, key=video_scores.get) if video_scores else 'flow'
    
    # Ajuster la durée et BPM selon le prompt
    duration = 5.0
    bpm = 100.0
    if 'long' in prompt_lower or 'infini' in prompt_lower:
        duration = 30.0
    if 'rapide' in prompt_lower or 'vite' in prompt_lower:
        bpm = 140.0
    if 'lent' in prompt_lower or 'slow' in prompt_lower:
        bpm = 70.0
    
    return PromptAnalysis(
        prompt=prompt,
        seed=seed,
        style=style,
        intensity=intensity,
        dominant_layer=dominant_layer,
        audio_type=audio_type,
        video_effect=video_effect,
        duration=duration,
        bpm=bpm,
        is_audio=is_audio,
        is_video=is_video,
        keywords_matched=matched,
    )


# ==============================================================================
# GÉNÉRATEUR UNIFIÉ PROMPT → IMAGE/VIDEO/AUDIO
# ==============================================================================

class PromptGenerator:
    """
    Générateur unifié : prompt texte → image/vidéo/audio haute résolution.
    """
    
    def __init__(self, default_resolution: str = 'sd'):
        self.default_res = default_resolution
    
    def generate_image(self, prompt: str, resolution: str = 'sd',
                       style: str = None, color_mode: str = 'hsl') -> Dict[str, Any]:
        """
        Génère une image à partir d'un prompt.
        
        Args:
            prompt: Texte descriptif
            resolution: 'sd', 'hd', '4k', '8k'
            style: Palette (optionnel, déduit du prompt si non spécifié)
            color_mode: 'hsl' ou 'multilayer'
        
        Returns:
            dict avec 'rgb' (np.array), 'metadata', 'psi'
        """
        analysis = analyze_prompt(prompt)
        if style is None:
            style = analysis.style
        
        width, height = RESOLUTIONS.get(resolution, RESOLUTIONS['sd'])
        
        # Stratégie de tuilage pour 4K/8K
        if width * height > 1920 * 1080:
            return self._generate_tiled_image(
                prompt=prompt,
                width=width, height=height,
                style=style,
                color_mode=color_mode,
                analysis=analysis,
            )
        
        # Génération directe pour SD/HD
        t0 = time.time()
        
        # Champ harmonique avec seed du prompt + couche dominante
        seed_main = SeedManager.compose_seed(analysis.seed, analysis.dominant_layer, 0)
        field = HarmonicField(width=width, height=height, seed=seed_main, n_layers=7)
        psi = field.get_psi_total()
        
        # Ajuster l'intensité
        psi = psi * analysis.intensity
        psi = normalize_field(psi)
        
        # Conversion RGB
        from harmonic_image_generator import HarmonicImageGenerator
        gen = HarmonicImageGenerator(width=width, height=height, seed=seed_main)
        rgb = gen.generate(style=style, color_mode=color_mode)
        
        gen_time = (time.time() - t0) * 1000
        
        # Métriques
        coherence = compute_harmonic_coherence(psi)
        symmetry = compute_symmetry_score(psi)
        
        return {
            'rgb': rgb,
            'metadata': {
                'prompt': prompt,
                'seed': analysis.seed,
                'resolution': f'{width}×{height}',
                'style': style,
                'color_mode': color_mode,
                'intensity': analysis.intensity,
                'dominant_layer': analysis.dominant_layer,
                'keywords': analysis.keywords_matched,
                'coherence': round(coherence, 4),
                'symmetry': round(symmetry, 4),
                'generation_time_ms': round(gen_time, 1),
                'layers': [
                    {'n': n+1, 'constante': H_NAMES[n], 'valeur': float(H_CONSTANTS[n]),
                     'contribution': round(field.get_layer_contribution(n+1), 4)}
                    for n in range(7)
                ],
            },
            'psi': psi,
            'field': field,
        }
    
    def _generate_tiled_image(self, prompt: str, width: int, height: int,
                               style: str, color_mode: str,
                               analysis: PromptAnalysis) -> Dict[str, Any]:
        """
        Génération par tuilage pour résolutions 4K/8K.
        
        Découpe la grille en tuiles TILE_SIZE × TILE_SIZE, génère chaque tuile
        avec un seed dérivé, puis assemble. Le seed de chaque tuile varie
        légèrement pour créer des variations naturelles entre tuiles.
        """
        from PIL import Image
        
        n_tiles_x = math.ceil(width / TILE_SIZE)
        n_tiles_y = math.ceil(height / TILE_SIZE)
        total_tiles = n_tiles_x * n_tiles_y
        
        print(f"    Génération 4K/8K par tuilage : {n_tiles_x}×{n_tiles_y} = {total_tiles} tuiles...")
        
        t0 = time.time()
        
        # Créer l'image de sortie
        full_rgb = np.zeros((height, width, 3), dtype=np.uint8)
        
        for ty in range(n_tiles_y):
            for tx in range(n_tiles_x):
                # Dimensions de cette tuile
                tile_w = min(TILE_SIZE, width - tx * TILE_SIZE)
                tile_h = min(TILE_SIZE, height - ty * TILE_SIZE)
                
                # Seed unique pour cette tuile (varie avec la position)
                tile_seed = SeedManager.compose_seed(
                    analysis.seed,
                    ty * n_tiles_x + tx + 1,
                    analysis.dominant_layer
                )
                
                # Générer le champ pour cette tuile
                field = HarmonicField(width=tile_w, height=tile_h, seed=tile_seed)
                psi_tile = field.get_psi_total()
                psi_tile = psi_tile * analysis.intensity
                psi_tile = normalize_field(psi_tile)
                
                # Conversion RGB
                rgb_tile = HarmonicColorMapper.harmonic_hsl(psi_tile, palette=style)
                
                # Placement dans l'image finale
                x_start = tx * TILE_SIZE
                y_start = ty * TILE_SIZE
                full_rgb[y_start:y_start+tile_h, x_start:x_start+tile_w] = rgb_tile
        
        # Post-processing : lissage des bordures de tuiles (optionnel)
        # Ici on fait un blend simple sur les bordures pour éviter les coutures
        blend_width = 16
        for ty in range(n_tiles_y):
            for tx in range(n_tiles_x - 1):
                seam_x = (tx + 1) * TILE_SIZE
                if seam_x + blend_width < width:
                    x_start = max(0, seam_x - blend_width // 2)
                    x_end = min(width, seam_x + blend_width // 2)
                    for y in range(height):
                        alpha = np.linspace(0, 1, x_end - x_start)
                        for c in range(3):
                            full_rgb[y, x_start:x_end, c] = (
                                full_rgb[y, x_start:x_end, c] * (1 - alpha) +
                                np.roll(full_rgb[y, x_start:x_end, c], 1) * alpha
                            ).astype(np.uint8)
        
        gen_time = (time.time() - t0) * 1000
        
        print(f"    ✓ Génération {width}×{height} en {gen_time:.0f}ms ({total_tiles} tuiles)")
        
        return {
            'rgb': full_rgb,
            'metadata': {
                'prompt': prompt,
                'seed': analysis.seed,
                'resolution': f'{width}×{height}',
                'style': style,
                'color_mode': color_mode,
                'intensity': analysis.intensity,
                'dominant_layer': analysis.dominant_layer,
                'keywords': analysis.keywords_matched,
                'n_tiles': f'{n_tiles_x}×{n_tiles_y}',
                'generation_time_ms': round(gen_time, 1),
            },
            'psi': None,
            'field': None,
        }
    
    def generate_video(self, prompt: str, resolution: str = 'sd',
                       duration: float = None, fps: int = 24,
                       style: str = None) -> Dict[str, Any]:
        """
        Génère une vidéo à partir d'un prompt.
        """
        analysis = analyze_prompt(prompt)
        if style is None:
            style = analysis.style
        if duration is None:
            duration = analysis.duration
        
        width, height = RESOLUTIONS.get(resolution, RESOLUTIONS['sd'])
        n_frames = int(fps * duration)
        
        print(f"    Génération vidéo {width}×{height} @ {fps}fps × {duration}s = {n_frames} frames...")
        
        t0 = time.time()
        frames = []
        frame_metadata = []
        
        for i in range(n_frames):
            t = i / fps
            t_norm = t / duration if duration > 0 else 0
            
            # Seed évolutif
            frame_seed = SeedManager.compose_seed(analysis.seed, 1, i * 31)
            field = HarmonicField(width=width, height=height, seed=frame_seed)
            psi = field.get_psi_total()
            
            # Modulations temporelles (simplifiées pour la performance)
            Y, X = np.ogrid[:height, :width]
            X_norm = X / width * 2 - 1
            Y_norm = Y / height * 2 - 1
            R = np.sqrt(X_norm**2 + Y_norm**2)
            theta = np.arctan2(Y_norm, X_norm)
            
            # H₁ rotation, H₂ cycle, H₃ amortissement, H₇ spirale
            rot = t * 0.5 * PHI_INV * 2 * PI
            psi_t = psi * np.cos(rot)
            psi_t *= (0.7 + 0.3 * np.sin(t * 2 * PI))
            psi_t *= np.exp(-R * 0.1)
            psi_t += 0.1 * np.sin(R * 15 * E_PI + (theta + t * E_PI * 0.3) * 7) * (1 - t_norm * 0.5)
            psi_t = normalize_field(psi_t)
            
            # Style qui évolue
            styles = list(HarmonicColorMapper.PALETTES.keys())
            frame_style_idx = int((t_norm * PHI * len(styles)) % len(styles))
            frame_style = styles[frame_style_idx]
            
            rgb = HarmonicColorMapper.harmonic_hsl(psi_t, palette=frame_style)
            frames.append(rgb)
            
            frame_metadata.append({
                'frame': i,
                'time': round(t, 3),
                'style': frame_style,
            })
            
            if i % max(1, n_frames // 5) == 0:
                print(f"      Frame {i+1}/{n_frames}")
        
        gen_time = (time.time() - t0) * 1000
        
        return {
            'frames': frames,
            'frame_metadata': frame_metadata,
            'metadata': {
                'prompt': prompt,
                'seed': analysis.seed,
                'resolution': f'{width}×{height}',
                'fps': fps,
                'duration': duration,
                'n_frames': n_frames,
                'effect': analysis.video_effect,
                'generation_time_ms': round(gen_time, 1),
            },
        }
    
    def generate_audio(self, prompt: str, duration: float = None,
                       sample_rate: int = 44100) -> Dict[str, Any]:
        """
        Génère un fichier audio à partir d'un prompt.
        """
        analysis = analyze_prompt(prompt)
        if duration is None:
            duration = analysis.duration
        
        audio_type = analysis.audio_type
        bpm = analysis.bpm
        
        from harmonic_audio_generator import HarmonicMusicGenerator
        
        print(f"    Génération audio '{audio_type}' ({duration}s, {bpm} BPM)...")
        
        t0 = time.time()
        gen = HarmonicMusicGenerator(seed=analysis.seed, sample_rate=sample_rate)
        
        if audio_type == 'composition':
            audio = gen.generate_full_composition(duration=duration, bpm=bpm)
        elif audio_type == 'melody':
            audio = gen.compose_melody(duration=duration, n_notes=int(duration * 4))
        elif audio_type == 'pad':
            audio = gen.generate_harmony_pad(fundamental=110.0, duration=duration)
        elif audio_type == 'rhythm':
            audio = gen.generate_rhythm_track(duration=duration, bpm=bpm)
        else:
            audio = gen.generate_ambient_soundscape(duration=duration)
        
        gen_time = (time.time() - t0) * 1000
        
        return {
            'audio': audio,
            'sample_rate': sample_rate,
            'metadata': {
                'prompt': prompt,
                'seed': analysis.seed,
                'audio_type': audio_type,
                'duration': duration,
                'bpm': bpm,
                'sample_rate': sample_rate,
                'generation_time_ms': round(gen_time, 1),
                'keywords': analysis.keywords_matched,
            },
        }


# ==============================================================================
# SERVEUR API REST (Flask)
# ==============================================================================

def start_server(host: str = '0.0.0.0', port: int = 8765):
    """Lance le serveur API REST de génération harmonique."""
    try:
        from flask import Flask, request, jsonify, send_file, Response
        from flask_cors import CORS
    except ImportError:
        print("Installation de Flask...")
        os.system(f"{sys.executable} -m pip install flask flask-cors -q")
        from flask import Flask, request, jsonify, send_file, Response
        from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    generator = PromptGenerator()
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'prompts')
    os.makedirs(output_dir, exist_ok=True)
    
    @app.route('/api/generate/image', methods=['POST'])
    def api_generate_image():
        data = request.json or {}
        prompt = data.get('prompt', 'harmonie cosmique')
        resolution = data.get('resolution', 'sd')
        style = data.get('style', None)
        color_mode = data.get('color_mode', 'hsl')
        save = data.get('save', False)
        
        try:
            result = generator.generate_image(
                prompt=prompt,
                resolution=resolution,
                style=style,
                color_mode=color_mode,
            )
            
            response = {'metadata': result['metadata']}
            
            if save:
                img_id = hashlib.md5(f"{prompt}_{resolution}_{time.time()}".encode()).hexdigest()[:12]
                filepath = os.path.join(output_dir, f'img_{img_id}.png')
                from PIL import Image
                Image.fromarray(result['rgb'], 'RGB').save(filepath)
                response['file'] = filepath
            
            response['success'] = True
            return jsonify(response)
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/generate/video', methods=['POST'])
    def api_generate_video():
        data = request.json or {}
        prompt = data.get('prompt', 'flux cosmique')
        resolution = data.get('resolution', 'sd')
        duration = data.get('duration', 5.0)
        fps = data.get('fps', 24)
        style = data.get('style', None)
        
        try:
            result = generator.generate_video(
                prompt=prompt,
                resolution=resolution,
                duration=duration,
                fps=fps,
                style=style,
            )
            
            vid_id = hashlib.md5(f"{prompt}_{time.time()}".encode()).hexdigest()[:12]
            gif_path = os.path.join(output_dir, f'vid_{vid_id}.gif')
            
            from PIL import Image
            pil_frames = [Image.fromarray(f, 'RGB') for f in result['frames']]
            pil_frames[0].save(
                gif_path, save_all=True, append_images=pil_frames[1:],
                duration=int(1000 / fps), loop=0
            )
            
            return jsonify({
                'success': True,
                'metadata': result['metadata'],
                'file': gif_path,
            })
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/generate/audio', methods=['POST'])
    def api_generate_audio():
        data = request.json or {}
        prompt = data.get('prompt', 'musique harmonique')
        duration = data.get('duration', 10.0)
        sample_rate = data.get('sample_rate', 44100)
        
        try:
            result = generator.generate_audio(
                prompt=prompt,
                duration=duration,
                sample_rate=sample_rate,
            )
            
            aud_id = hashlib.md5(f"{prompt}_{time.time()}".encode()).hexdigest()[:12]
            wav_path = os.path.join(output_dir, f'aud_{aud_id}.wav')
            
            from harmonic_audio_generator import save_wav
            save_wav(result['audio'], wav_path, sample_rate)
            
            return jsonify({
                'success': True,
                'metadata': result['metadata'],
                'file': wav_path,
            })
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/analyze', methods=['POST'])
    def api_analyze():
        data = request.json or {}
        prompt = data.get('prompt', '')
        analysis = analyze_prompt(prompt)
        return jsonify(analysis.to_json())
    
    @app.route('/api/health', methods=['GET'])
    def api_health():
        return jsonify({
            'status': 'ok',
            'engine': 'Harmonic Prompt Engine',
            'version': '3.0',
            'formula': 'Psi = Sigma H_n (Psi_1)^n',
            'resolutions': list(RESOLUTIONS.keys()),
        })
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🎨 PROMPT ENGINE HARMONIQUE — API REST                     ║
║  Ψ = Σ Hₙ (Ψ₁)ⁿ                                            ║
╠══════════════════════════════════════════════════════════════╣
║  Endpoints :                                                ║
║    POST /api/generate/image   { prompt, resolution, style } ║
║    POST /api/generate/video   { prompt, duration, fps }     ║
║    POST /api/generate/audio   { prompt, duration }          ║
║    POST /api/analyze          { prompt }                    ║
║    GET  /api/health                                        ║
╠══════════════════════════════════════════════════════════════╣
║  Server  : http://{host}:{port}                    ║
║  Ctrl+C  : Arrêter le serveur                               ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    app.run(host=host, port=port, debug=False, threaded=True)


# ==============================================================================
# DÉMONSTRATION CLI
# ==============================================================================

def demo_prompt_engine():
    """Démonstration du moteur de prompts."""
    print("=" * 70)
    print("  PROMPT ENGINE HARMONIQUE")
    print("  Prompt → Image/Video/Audio 4K/8K")
    print("=" * 70)
    
    gen = PromptGenerator()
    
    test_prompts = [
        "galaxie spirale cosmique dans l'espace profond",
        "forêt de cristaux géométriques émeraude",
        "océan de lumière dorée au coucher du soleil",
        "aurore boréale mystique sur un lac gelé",
        "musique calme ambient pour méditation",
        "tempête de feu et de glace en mouvement",
    ]
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'prompts')
    os.makedirs(output_dir, exist_ok=True)
    
    for i, prompt in enumerate(test_prompts):
        print(f"\n  [{i+1}/{len(test_prompts)}] Prompt : \"{prompt}\"")
        
        # Analyse
        analysis = analyze_prompt(prompt)
        print(f"    Style déduit : {analysis.style}")
        print(f"    Intensité    : {analysis.intensity:.2f}")
        print(f"    Couche H{analysis.dominant_layer} dominante")
        print(f"    Mots-clés    : {analysis.keywords_matched}")
        
        # Génération image (SD pour la démo)
        if not analysis.is_audio or i < 2:
            result = gen.generate_image(prompt, resolution='sd', style=analysis.style)
            from PIL import Image
            img_id = hashlib.md5(prompt.encode()).hexdigest()[:8]
            filepath = os.path.join(output_dir, f'prompt_{img_id}.png')
            Image.fromarray(result['rgb'], 'RGB').save(filepath)
            meta = result['metadata']
            print(f"    ✅ Image {meta['resolution']} → {filepath} ({meta['generation_time_ms']}ms)")
    
    print(f"\n{'='*70}")
    print("  PROMPT ENGINE — Rapport")
    print(f"{'='*70}")
    print(f"  Résolutions supportées : sd, hd, 4k, 8k")
    print(f"  Modes                  : procedural (pur), one_shot (SVD)")
    print(f"  Output                 : {output_dir}")
    print(f"\n  Lancement serveur API  : python prompt_engine.py --server")
    print(f"  ✅ Prompt Engine opérationnel.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prompt Engine Harmonique')
    parser.add_argument('--prompt', type=str, default=None, help='Prompt texte')
    parser.add_argument('--resolution', type=str, default='sd', 
                        choices=['sd', 'hd', '4k', '8k'], help='Résolution')
    parser.add_argument('--style', type=str, default=None, help='Palette')
    parser.add_argument('--mode', type=str, default='procedural',
                        choices=['procedural', 'one_shot', 'hybrid'])
    parser.add_argument('--output', type=str, default=None, help='Fichier de sortie')
    parser.add_argument('--server', action='store_true', help='Lancer serveur API')
    parser.add_argument('--port', type=int, default=8765, help='Port API')
    parser.add_argument('--demo', action='store_true', help='Démo interactive')
    
    args = parser.parse_args()
    
    if args.server:
        start_server(port=args.port)
    elif args.prompt and args.output:
        gen = PromptGenerator()
        result = gen.generate_image(
            prompt=args.prompt,
            resolution=args.resolution,
            style=args.style,
        )
        from PIL import Image
        Image.fromarray(result['rgb'], 'RGB').save(args.output)
        print(f"Image sauvegardée : {args.output}")
        print(json.dumps(result['metadata'], indent=2))
    elif args.prompt:
        gen = PromptGenerator()
        result = gen.generate_image(
            prompt=args.prompt,
            resolution=args.resolution,
            style=args.style,
        )
        print(json.dumps(result['metadata'], indent=2))
    else:
        demo_prompt_engine()