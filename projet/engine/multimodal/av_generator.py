"""
engine.multimodal.av_generator — Générateur Audio/Vidéo harmonique
===================================================================
Intègre le moteur AV existant (GENERATION_AV_HARMONIQUE/engine/harmonic_av_core.py)
ou fournit une version autonome simplifiée.

Fonctions publiques :
    generate_audio_from_prompt(prompt, duration)  → samples + signature
    generate_video_from_prompt(prompt, duration)   → frames + signature
    generate_av_from_prompt(prompt, duration)      → AV sync complet
    HarmonicAVGenerator                            → Classe principale
"""

import math
import time
import os
import sys
from typing import List, Tuple, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

from .analyzers import PHI, PHI_INV, ALPHA, compute_resonance, analyze_document

# ---------------------------------------------------------------------------
# CONSTANTES
# ---------------------------------------------------------------------------

RESONANCE_HIGH = 0.75
RESONANCE_MEDIUM = 0.65
RESONANCE_LOW = 0.55


# ---------------------------------------------------------------------------
# FONCTIONS MATHÉMATIQUES (autonomes)
# ---------------------------------------------------------------------------

def gamma_stirling(x: float) -> float:
    """Fonction Gamma par approximation de Stirling-Lanczos."""
    if x <= 0 and x == int(x):
        return float('nan')
    temp = x
    if temp < 0.5:
        return math.pi / (math.sin(math.pi * x) * gamma_stirling(1.0 - x))
    temp -= 1.0
    sqrt2pi = math.sqrt(2.0 * math.pi)
    coefs = [1.0, 1.0/12.0, 1.0/288.0, -139.0/51840.0, -571.0/2488320.0]
    series = coefs[0]
    factor = 1.0
    for i in range(1, len(coefs)):
        factor /= temp
        series += coefs[i] * factor
    return sqrt2pi * (temp ** (temp + 0.5)) * math.exp(-temp) * series


def mittag_leffler(alpha: float, z: float, terms: int = 50) -> float:
    """Fonction de Mittag-Leffler E_α(z) — noyau ABC."""
    result = 0.0
    for k in range(terms):
        try:
            term = (z ** k) / gamma_stirling(alpha * k + 1.0)
            result += term
            if abs(term) < 1e-12:
                break
        except (ValueError, ZeroDivisionError):
            break
    return result


# ---------------------------------------------------------------------------
# TEMPLETS AUDIO/VIDÉO FONDAMENTAUX
# ---------------------------------------------------------------------------

AUDIO_TEMPLATES = {
    'oceano': {
        'amplitudes': [0.9, 0.6, 0.3, 0.2],
        'basis_states': ['vague_douce', 'vague_moyenne', 'vague_forte', 'écume'],
        'frequencies': [80, 200, 400, 800],
        'envelope': [0.05, 0.3, 0.5, 0.15],
        'signature': [0.6, 0.3, 0.1, 0.8, 0.0, 0.5, 0.0],
        'k_factor': 0.85,
    },
    'piano': {
        'amplitudes': [0.8, 0.7, 0.5, 0.3],
        'basis_states': ['do', 'mi', 'sol', 'si'],
        'frequencies': [261.63, 329.63, 392.00, 493.88],
        'envelope': [0.01, 0.5, 0.8, 0.3],
        'signature': [0.4, 0.5, 0.2, 0.9, 0.0, 0.2, 0.0],
        'k_factor': 0.82,
    },
    'vent': {
        'amplitudes': [0.7, 0.5, 0.4],
        'basis_states': ['brise', 'rafale', 'tempête'],
        'frequencies': [100, 300, 600],
        'envelope': [0.1, 0.4, 0.9, 0.2],
        'signature': [0.3, 0.2, 0.1, 0.6, 0.0, 0.3, 0.0],
        'k_factor': 0.78,
    },
    'silence': {
        'amplitudes': [0.1],
        'basis_states': ['silence'],
        'frequencies': [0],
        'envelope': [0.0, 0.0, 0.0, 0.0],
        'signature': [0.0, 0.0, 0.0, 0.2, 0.0, 0.1, 0.0],
        'k_factor': 0.5,
    }
}

VIDEO_TEMPLATES = {
    'coucher_soleil': {
        'amplitudes': [0.9, 0.7, 0.5, 0.3, 0.2],
        'basis_states': ['ciel_orange', 'horizon_rouge', 'mer_reflet',
                         'nuage_doré', 'silhouette'],
        'colors': [(255, 180, 50), (255, 100, 30), (200, 120, 60),
                   (255, 220, 100), (50, 50, 80)],
        'texture': 'gradient_horizontal',
        'signature': [0.5, 0.4, 0.2, 0.8, 0.0, 0.3, 0.0],
        'k_factor': 0.88,
    },
    'foret': {
        'amplitudes': [0.8, 0.6, 0.5, 0.3],
        'basis_states': ['arbre_fond', 'feuille_premier_plan', 'sol', 'lumière'],
        'colors': [(40, 80, 40), (60, 120, 60), (80, 60, 30), (200, 220, 150)],
        'texture': 'feuillage',
        'signature': [0.4, 0.5, 0.1, 0.7, 0.0, 0.4, 0.0],
        'k_factor': 0.85,
    },
    'mer': {
        'amplitudes': [0.9, 0.6, 0.4],
        'basis_states': ['eau_profonde', 'écume', 'reflet_ciel'],
        'colors': [(20, 60, 120), (200, 220, 230), (100, 150, 200)],
        'texture': 'vagues_sinus',
        'signature': [0.3, 0.2, 0.1, 0.6, 0.0, 0.5, 0.0],
        'k_factor': 0.80,
    },
    'abstrait': {
        'amplitudes': [0.7, 0.5, 0.5, 0.4, 0.3],
        'basis_states': ['tourbillon_1', 'tourbillon_2', 'lueur', 'particule', 'traînée'],
        'colors': [(100, 50, 200), (50, 200, 100), (200, 100, 50),
                   (255, 255, 100), (150, 50, 200)],
        'texture': 'turbulence',
        'signature': [0.7, 0.6, 0.3, 0.9, 0.0, 0.1, 0.0],
        'k_factor': 0.90,
    }
}


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------

@dataclass
class AudioVisualTemplate:
    """Template audio ou vidéo pour la génération harmonique."""
    name: str
    amplitudes: List[float]
    basis_states: List[str]
    signature: List[float]
    k_factor: float
    frequencies: Optional[List[float]] = None       # Audio
    envelope: Optional[List[float]] = None           # Audio
    colors: Optional[List[Tuple[int, int, int]]] = None  # Vidéo
    texture: Optional[str] = None                    # Vidéo

    @classmethod
    def from_dict(cls, name: str, d: dict) -> 'AudioVisualTemplate':
        return cls(
            name=name,
            amplitudes=d.get('amplitudes', [0.5]),
            basis_states=d.get('basis_states', []),
            signature=d.get('signature', [0.5]*7),
            k_factor=d.get('k_factor', 0.8),
            frequencies=d.get('frequencies'),
            envelope=d.get('envelope'),
            colors=d.get('colors'),
            texture=d.get('texture'),
        )


@dataclass
class AVGenerationResult:
    """Résultat complet d'une génération audio/vidéo."""
    prompt: str
    duration_seconds: float
    fps: int
    sample_rate: int
    resolution: Tuple[int, int]

    # Audio
    audio_samples: List[float] = field(default_factory=list)
    audio_harmonic_signature: List[float] = field(default_factory=list)

    # Vidéo
    video_frames: List[List[List[Tuple[int, int, int]]]] = field(default_factory=list)
    video_harmonic_signature: List[float] = field(default_factory=list)

    # Métadonnées
    resonance_audio: float = 0.0
    resonance_video: float = 0.0
    av_sync_quality: float = 0.0
    processing_time_ms: float = 0.0
    scene_type: str = ''
    mood: str = ''
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            'prompt': self.prompt[:100],
            'duration': self.duration_seconds,
            'fps': self.fps,
            'sample_rate': self.sample_rate,
            'resolution': list(self.resolution),
            'audio_samples': len(self.audio_samples),
            'video_frames': len(self.video_frames),
            'resonance_audio': round(self.resonance_audio, 4),
            'resonance_video': round(self.resonance_video, 4),
            'av_sync_quality': round(self.av_sync_quality, 4),
            'processing_time_ms': round(self.processing_time_ms, 2),
            'scene_type': self.scene_type,
            'mood': self.mood,
        }


# ---------------------------------------------------------------------------
# ANALYSEUR DE PROMPT AV
# ---------------------------------------------------------------------------

class AVHarmonicPromptAnalyzer:
    """
    Analyse un prompt texte et produit une signature harmonique 7D
    avec détection de scène, ambiance et mouvement pour l'AV.
    """
    
    RARE_WORDS = {
        'paradigme', 'épistémologique', 'ontologique', 'phénoménologique',
        'transcendantal', 'axiomatique', 'heuristique', 'stochastique',
        'quantique', 'relativiste', 'algorithmique', 'computationnel',
    }
    
    SCENE_PATTERNS = {
        'nature': ['océan', 'montagne', 'forêt', 'coucher', 'soleil', 'mer',
                    'rivière', 'cascade', 'plage', 'paysage', 'ciel', 'nuage'],
        'urbain': ['ville', 'rue', 'immeuble', 'pont', 'route', 'bâtiment',
                    'quartier', 'métro', 'gare', 'aéroport'],
        'intérieur': ['pièce', 'salon', 'chambre', 'cuisine', 'bureau',
                       'restaurant', 'café', 'théâtre', 'salle'],
        'abstrait': ['rêve', 'imagination', 'fantaisie', 'cosmos', 'galaxie',
                      'nébuleuse', 'univers', 'dimension'],
    }
    
    MOOD_PATTERNS = {
        'calme': ['calme', 'paisible', 'doux', 'serein', 'tranquille', 'apaisant'],
        'dynamique': ['rapide', 'dynamique', 'énergique', 'vif', 'rythmé'],
        'mélancolique': ['triste', 'mélancolique', 'nostalgique', 'sombre'],
        'joyeux': ['joyeux', 'heureux', 'lumineux', 'chantant', 'gai'],
        'dramatique': ['dramatique', 'intense', 'puissant', 'épique'],
    }
    
    def analyze(self, prompt: str) -> dict:
        """Analyse complète : signature 7D + métadonnées AV."""
        words = prompt.lower().split()
        if not words:
            return self._empty_result()
        
        word_count = len(words)
        
        # Signature 7D
        rare_count = sum(1 for w in words if w.strip('.,!?;:') in self.RARE_WORDS)
        phi_ratio = min(1.0, (rare_count / max(word_count, 1)) * PHI)
        
        avg_len = sum(len(w) for w in words) / word_count
        variance = sum((len(w) - avg_len) ** 2 for w in words) / word_count
        std_dev = math.sqrt(variance)
        alpha_complexity = min(1.0, ((avg_len / 15.0 + std_dev / 5.0) / 2.0) * PHI_INV)
        
        category_scores = self._compute_category_scores(prompt)
        
        # Métadonnées AV
        scene_type = self._detect_scene(prompt)
        mood = self._detect_mood(prompt)
        motion = self._estimate_motion(prompt)
        
        signature_7d = [
            phi_ratio, alpha_complexity,
            category_scores.get('reasoning', 0),
            category_scores.get('creative', 0),
            category_scores.get('mathematical', 0),
            category_scores.get('factual', 0),
            category_scores.get('code', 0),
        ]
        
        return {
            'signature_7d': signature_7d,
            'phi_ratio': phi_ratio,
            'alpha_complexity': alpha_complexity,
            'scene_type': scene_type,
            'mood': mood,
            'motion_level': motion,
            'category': self._classify(signature_7d),
            'words': words,
            'prompt': prompt,
        }
    
    def _compute_category_scores(self, prompt: str) -> dict:
        patterns = {
            'mathematical': (['calcul', 'somme', 'équation', 'nombre'], 0.35),
            'code': (['python', 'algorithme', 'programme', 'code'], 0.25),
            'creative': (['poème', 'histoire', 'crée', 'imagine', 'art', 'rêve'], 0.30),
            'reasoning': (['pourquoi', 'explique', 'analyse', 'cause'], 0.35),
            'factual': (['qu\'est-ce que', 'définition', 'liste', 'fait'], 0.25),
        }
        scores = {}
        total = sum(
            sum(1 for kw in kws if kw in prompt.lower())
            for cat, (kws, _) in patterns.items()
        )
        total = max(total, 1)
        for cat, (kws, weight) in patterns.items():
            count = sum(1 for kw in kws if kw in prompt.lower())
            scores[cat] = min(1.0, (count / total) * weight * PHI * 2)
        return scores
    
    def _detect_scene(self, prompt: str) -> str:
        p = prompt.lower()
        best = 'neutre'
        best_count = 0
        for scene, keywords in self.SCENE_PATTERNS.items():
            count = sum(1 for kw in keywords if kw in p)
            if count > best_count:
                best_count = count
                best = scene
        return best
    
    def _detect_mood(self, prompt: str) -> str:
        p = prompt.lower()
        best = 'neutre'
        best_count = 0
        for mood, keywords in self.MOOD_PATTERNS.items():
            count = sum(1 for kw in keywords if kw in p)
            if count > best_count:
                best_count = count
                best = mood
        return best
    
    def _estimate_motion(self, prompt: str) -> float:
        motion_keywords = ['vague', 'vent', 'courant', 'mouvement', 'danse',
                           'flux', 'course', 'vol', 'chute', 'tourbillon']
        p = prompt.lower()
        count = sum(1 for kw in motion_keywords if kw in p)
        return min(1.0, count / 5.0 * PHI_INV)
    
    def _classify(self, sig: List[float]) -> str:
        labels = ['mathematical', 'code', 'creative', 'reasoning', 'factual']
        scores = {labels[i]: sig[i + 2] for i in range(5)}
        best = max(scores, key=scores.get)
        return best if scores[best] > 0.15 else 'general'
    
    def _empty_result(self) -> dict:
        return {
            'signature_7d': [0.0] * 7,
            'phi_ratio': 0.0, 'alpha_complexity': 0.0,
            'scene_type': 'neutre', 'mood': 'neutre',
            'motion_level': 0.0, 'category': 'general',
            'words': [], 'prompt': ''
        }


# ---------------------------------------------------------------------------
# MOTEUR AV PRINCIPAL
# ---------------------------------------------------------------------------

class HarmonicAVGenerator:
    """
    Générateur audio/vidéo harmonique principal.
    Orchestre l'analyse du prompt, la sélection des templates,
    l'évolution ABC, et la synchronisation AV.
    
    Usage:
        gen = HarmonicAVGenerator()
        result = gen.generate_from_prompt(
            "Coucher de soleil sur l'océan",
            duration_seconds=10.0
        )
        print(f"Résonance audio: {result.resonance_audio:.3f}")
        print(f"Sync AV: {result.av_sync_quality:.3f}")
        
        # Output numpy array pour traitement
        import numpy as np
        audio_np = np.array(result.audio_samples)
    """
    
    def __init__(self):
        self.analyzer = AVHarmonicPromptAnalyzer()
    
    def find_best_template(self, signature: List[float], templates: dict) -> Tuple[str, dict, float]:
        """Trouve le template le plus résonant avec la signature."""
        best_id = None
        best_template = None
        best_resonance = 0.0
        
        for tid, tpl in templates.items():
            R = compute_resonance(signature, tpl.get('signature', signature))
            if R > best_resonance:
                best_resonance = R
                best_id = tid
                best_template = tpl
        
        return best_id, best_template, best_resonance
    
    def generate_audio(self, analysis: dict, duration: float, sample_rate: int = 44100) -> dict:
        """
        Génère le signal audio par évolution ABC.
        
        Principe :
        - Chaque état de base du template = une fréquence
        - L'évolution ABC module l'amplitude de chaque fréquence dans le temps
        - Le collapsus à chaque pas de temps échantillonné donne l'onde
        """
        signature = analysis['signature_7d']
        mood = analysis['mood']
        motion = analysis['motion_level']
        
        # Trouver le template audio
        tid, template, resonance = self.find_best_template(signature, AUDIO_TEMPLATES)
        if not template or resonance < RESONANCE_LOW:
            tid, template = 'silence', AUDIO_TEMPLATES['silence']
            resonance = 0.3
        
        num_samples = int(duration * sample_rate)
        samples = []
        
        freqs = template['frequencies']
        amps = template['amplitudes']
        env = template['envelope']
        
        for t_idx in range(num_samples):
            t = t_idx / sample_rate
            t_scaled = t ** PHI_INV
            
            # Noyau ABC : E_{1/φ}(-φ * R * t^{1/φ})
            kernel = mittag_leffler(PHI_INV, -PHI * resonance * t_scaled)
            
            # Ajustement selon l'humeur
            mood_factor = 1.0
            if mood == 'calme':
                mood_factor = 0.6 + 0.4 * math.cos(t * 0.5)
            elif mood == 'dynamique':
                mood_factor = 0.5 + 0.5 * math.sin(t * 3.0)
            elif mood == 'mélancolique':
                mood_factor = 0.7 + 0.3 * math.sin(t * 0.3 + math.pi)
            elif mood == 'joyeux':
                mood_factor = 0.8 + 0.2 * math.sin(t * 2.0)
            
            motion_mod = 1.0 + motion * 0.3 * math.sin(t * 2.0 * motion)
            
            # Sample = superposition des fréquences modulées
            sample = 0.0
            for i, (freq, amp) in enumerate(zip(freqs, amps)):
                evolved_amp = amp * kernel * mood_factor
                t_ratio = t / duration
                env_amp = (env[0] + (env[1] - env[0]) * t_ratio) * \
                          math.exp(-env[2] * t_ratio) + env[3] * (1 - math.exp(-t_ratio))
                wave = evolved_amp * env_amp * \
                       math.sin(2.0 * math.pi * freq * motion_mod * t +
                                i * PHI * math.pi / len(freqs))
                sample += wave
            
            samples.append(sample / len(freqs))
        
        return {
            'samples': samples,
            'sample_rate': sample_rate,
            'template_id': tid,
            'resonance': resonance,
            'frequencies': list(freqs),
        }
    
    def generate_video(self, analysis: dict, duration: float,
                       fps: int = 24, resolution: Tuple[int, int] = (1920, 1080)) -> dict:
        """
        Génère les frames vidéo par évolution ABC.
        
        Principe :
        - Chaque pixel = superposition d'états de couleur
        - L'évolution ABC fait évoluer les couleurs dans le temps
        - Le collapsus produit la couleur finale de chaque pixel
        """
        signature = analysis['signature_7d']
        scene_type = analysis['scene_type']
        mood = analysis['mood']
        motion = analysis['motion_level']
        
        tid, template, resonance = self.find_best_template(signature, VIDEO_TEMPLATES)
        if not template or resonance < RESONANCE_LOW:
            tid, template = 'abstrait', VIDEO_TEMPLATES['abstrait']
            resonance = 0.3
        
        width, height = resolution
        num_frames = int(duration * fps)
        frames = []
        
        colors = template['colors']
        amps = template['amplitudes']
        
        for frame_idx in range(num_frames):
            t = frame_idx / fps
            t_scaled = t ** PHI_INV
            kernel = mittag_leffler(PHI_INV, -PHI * resonance * t_scaled)
            
            frame = []
            for y in range(height):
                row = []
                for x in range(width):
                    nx = x / width
                    ny = y / height
                    
                    if scene_type == 'nature':
                        dx = motion * 0.02 * math.sin(t * 0.5 + ny * 3.0)
                        dy = motion * 0.01 * math.cos(t * 0.3 + nx * 2.0)
                    elif scene_type == 'abstrait':
                        dx = 0.05 * math.sin(t * 1.5 + nx * 4.0 + ny * 2.0)
                        dy = 0.05 * math.cos(t * 1.2 + ny * 3.0 - nx * 2.0)
                    else:
                        dx = 0.01 * motion * math.sin(t * 0.2)
                        dy = 0.01 * motion * math.cos(t * 0.2)
                    
                    r, g, b = 0.0, 0.0, 0.0
                    for i, (color, amp) in enumerate(zip(colors, amps)):
                        cx = 0.5 + 0.4 * math.cos(i * 2.0 * math.pi / len(colors) + t * 0.1)
                        cy = 0.5 + 0.4 * math.sin(i * 2.0 * math.pi / len(colors) + t * 0.1)
                        dist = math.sqrt((nx - cx + dx) ** 2 + (ny - cy + dy) ** 2)
                        weight = max(0.0, 1.0 - dist * 3.0) * amp * kernel
                        r += color[0] * weight
                        g += color[1] * weight
                        b += color[2] * weight
                    
                    total = max(r + g + b, 0.001)
                    r = min(255, max(0, int(r / total * 255)))
                    g = min(255, max(0, int(g / total * 255)))
                    b = min(255, max(0, int(b / total * 255)))
                    row.append((r, g, b))
                frame.append(row)
            
            frames.append(frame)
        
        return {
            'frames': frames,
            'fps': fps,
            'resolution': resolution,
            'template_id': tid,
            'resonance': resonance,
            'num_frames': num_frames,
        }
    
    def compute_av_sync(self, audio_result: dict, video_result: dict) -> float:
        """Calcule la synchronisation AV par corrélation enveloppe/luminosité."""
        audio_samples = audio_result['samples']
        video_frames = video_result['frames']
        
        if not audio_samples or not video_frames:
            return 0.0
        
        samples_per_frame = len(audio_samples) // len(video_frames)
        audio_envelope = []
        for i in range(len(video_frames)):
            start = i * samples_per_frame
            end = start + samples_per_frame
            seg = audio_samples[start:end]
            if seg:
                rms = math.sqrt(sum(s ** 2 for s in seg) / len(seg))
                audio_envelope.append(rms)
            else:
                audio_envelope.append(0.0)
        
        video_brightness = []
        for frame in video_frames:
            total = 0.0
            count = 0
            for row in frame:
                for r, g, b in row:
                    total += 0.299 * r + 0.587 * g + 0.114 * b
                    count += 1
            video_brightness.append(total / max(count, 1))
        
        n = min(len(audio_envelope), len(video_brightness))
        if n < 2:
            return 0.5
        
        a = audio_envelope[:n]
        b_env = video_brightness[:n]
        a_mean = sum(a) / n
        b_mean = sum(b_env) / n
        
        num = sum((a[i] - a_mean) * (b_env[i] - b_mean) for i in range(n))
        den = math.sqrt(sum((a[i] - a_mean) ** 2 for i in range(n)) *
                        sum((b_env[i] - b_mean) ** 2 for i in range(n)))
        
        if den == 0:
            return 0.5
        
        return min(1.0, abs(num / den) * (1.0 / PHI_INV))
    
    def generate_from_prompt(self, prompt: str, duration_seconds: float = 10.0,
                              fps: int = 24, sample_rate: int = 44100,
                              resolution: Tuple[int, int] = (1920, 1080)) -> AVGenerationResult:
        """Pipeline complet : analyse → audio → vidéo → sync."""
        start_time = time.time()
        
        # 1. Analyse harmonique du prompt
        analysis = self.analyzer.analyze(prompt)
        signature = analysis['signature_7d']
        
        # 2. Génération audio
        audio_result = self.generate_audio(analysis, duration_seconds, sample_rate)
        
        # 3. Génération vidéo (résolution réduite pour la performance)
        preview_res = (resolution[0] // 4, resolution[1] // 4)  # 480x270
        video_result = self.generate_video(analysis, duration_seconds, fps, preview_res)
        
        # 4. Synchronisation AV
        av_sync = self.compute_av_sync(audio_result, video_result)
        
        processing_time = (time.time() - start_time) * 1000
        
        return AVGenerationResult(
            prompt=prompt,
            duration_seconds=duration_seconds,
            fps=fps,
            sample_rate=sample_rate,
            resolution=resolution,
            audio_samples=audio_result['samples'],
            audio_harmonic_signature=signature[:],
            video_frames=video_result['frames'],
            video_harmonic_signature=signature[:],
            resonance_audio=audio_result['resonance'],
            resonance_video=video_result['resonance'],
            av_sync_quality=av_sync,
            processing_time_ms=processing_time,
            scene_type=analysis['scene_type'],
            mood=analysis['mood'],
        )


# ---------------------------------------------------------------------------
# FONCTIONS PUBLIQUES
# ---------------------------------------------------------------------------

def generate_audio_from_prompt(prompt: str, duration_seconds: float = 5.0,
                                sample_rate: int = 44100) -> List[float]:
    """
    Génère un signal audio harmonique à partir d'un prompt texte.
    
    Args:
        prompt: Description textuelle de l'audio à générer
        duration_seconds: Durée en secondes
        sample_rate: Taux d'échantillonnage
    
    Returns:
        Liste d'échantillons audio (float dans [-1, 1])
    """
    gen = HarmonicAVGenerator()
    analysis = gen.analyzer.analyze(prompt)
    result = gen.generate_audio(analysis, duration_seconds, sample_rate)
    return result['samples']


def generate_video_from_prompt(prompt: str, duration_seconds: float = 5.0,
                                fps: int = 24,
                                resolution: Tuple[int, int] = (480, 270)) -> List:
    """
    Génère des frames vidéo harmoniques à partir d'un prompt texte.
    
    Args:
        prompt: Description textuelle de la vidéo
        duration_seconds: Durée en secondes
        fps: Images par seconde
        resolution: (largeur, hauteur) en pixels
    
    Returns:
        Liste de frames (chaque frame = liste de lignes = liste de tuples RGB)
    """
    gen = HarmonicAVGenerator()
    analysis = gen.analyzer.analyze(prompt)
    result = gen.generate_video(analysis, duration_seconds, fps, resolution)
    return result['frames']


def generate_av_from_prompt(prompt: str, duration_seconds: float = 5.0,
                             fps: int = 24, sample_rate: int = 44100,
                             resolution: Tuple[int, int] = (1920, 1080)) -> AVGenerationResult:
    """
    Génère audio + vidéo synchronisés à partir d'un prompt texte.
    
    Args:
        prompt: Description textuelle
        duration_seconds: Durée en secondes
        fps: Images par seconde
        sample_rate: Taux d'échantillonnage audio
        resolution: Résolution vidéo (largeur, hauteur)
    
    Returns:
        AVGenerationResult avec samples, frames et métadonnées de sync
    """
    gen = HarmonicAVGenerator()
    return gen.generate_from_prompt(prompt, duration_seconds, fps, sample_rate, resolution)
