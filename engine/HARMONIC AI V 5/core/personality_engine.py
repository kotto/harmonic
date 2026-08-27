"""
HARMONIC AI V 5 — Personality Engine
====================================
Module de personnalité et d'émotions par modulation de phase φ.

Remplace le « role-playing par system prompt » des LLM par une
modulation géométrique réelle de l'espace des phases ℂ⁵¹².

Capacités :
  - 10 émotions par rotation de phase + paramètres vocaux
  - Interpolation continue entre émotions (blend)
  - Fusion de personnalités H_A + H_B = nouvelle personnalité
  - Détection d'émotion par résonance
  - Profil de personnalité persistante (Big Five harmonique)

Usage :
  from personality_engine import PersonalityEngine

  pers = PersonalityEngine()
  pers.set_emotion('warm')
  pers.set_personality('empathique')

  # Moduler un ψ avec l'émotion courante
  psi_modulated = pers.modulate_emotion(psi)

  # Fusionner deux personnalités
  pers.blend_personalities('sophie', 'paul', ratio=0.3)
"""

import math
import time
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

import numpy as np

from config import (
    PHI, TAU, PHI_INV, DIM_PSI, EMOTIONS, HOLOGRAM_DIR,
)
from core.memory_core import (
    text_to_psi, psi_resonate, psi_superpose, psi_bind, psi_unbind,
)


# ═══════════════════════════════════════════════════════════
# TRAITS DE PERSONNALITÉ (Big Five Harmonique)
# ═══════════════════════════════════════════════════════════

# Chaque trait est un point dans ℂ⁵¹² avec une intensité [-1, 1]
# L'intensité module l'amplitude dans les dimensions correspondantes

BIG_FIVE = {
    'openness':          {'label': 'Ouverture',     'dims': slice(0, 102),    'phi_idx': 0},
    'conscientiousness': {'label': 'Conscience',     'dims': slice(102, 204), 'phi_idx': 1},
    'extraversion':      {'label': 'Extraversion',   'dims': slice(204, 306), 'phi_idx': 2},
    'agreeableness':     {'label': 'Agréabilité',    'dims': slice(306, 409), 'phi_idx': 3},
    'neuroticism':       {'label': 'Stabilité Émotionnelle', 'dims': slice(409, 512), 'phi_idx': 4},
}

# Archétypes de personnalité prédéfinis (profils Big Five)
ARCHETYPES = {
    'empathique':      {'openness': 0.6, 'conscientiousness': 0.5, 'extraversion': 0.4, 'agreeableness': 0.9, 'neuroticism': -0.3},
    'joyeux':          {'openness': 0.5, 'conscientiousness': 0.2, 'extraversion': 0.9, 'agreeableness': 0.6, 'neuroticism': -0.5},
    'sage':            {'openness': 0.8, 'conscientiousness': 0.7, 'extraversion': 0.2, 'agreeableness': 0.5, 'neuroticism': -0.7},
    'protecteur':      {'openness': 0.3, 'conscientiousness': 0.8, 'extraversion': 0.3, 'agreeableness': 0.8, 'neuroticism': -0.4},
    'creatif':         {'openness': 0.9, 'conscientiousness': 0.3, 'extraversion': 0.5, 'agreeableness': 0.4, 'neuroticism': -0.2},
    'mysterieux':      {'openness': 0.7, 'conscientiousness': 0.4, 'extraversion': 0.1, 'agreeableness': 0.3, 'neuroticism': 0.1},
    'energique':       {'openness': 0.5, 'conscientiousness': 0.6, 'extraversion': 0.9, 'agreeableness': 0.5, 'neuroticism': -0.6},
    'calme':           {'openness': 0.4, 'conscientiousness': 0.6, 'extraversion': 0.1, 'agreeableness': 0.7, 'neuroticism': -0.8},
    'rebelle':         {'openness': 0.8, 'conscientiousness': 0.1, 'extraversion': 0.8, 'agreeableness': 0.1, 'neuroticism': 0.3},
    'compagnon':       {'openness': 0.5, 'conscientiousness': 0.5, 'extraversion': 0.5, 'agreeableness': 0.7, 'neuroticism': -0.5},
}


# ═══════════════════════════════════════════════════════════
# PERSONNALITÉ ONDULATOIRE
# ═══════════════════════════════════════════════════════════

@dataclass
class HarmonicPersonality:
    """Personnalité encodée en ψ."""
    name: str
    traits: Dict[str, float]  # Big Five values [-1, 1]
    psi: np.ndarray           # Signature ψ de la personnalité
    created_at: float = 0.0
    updated_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.updated_at == 0.0:
            self.updated_at = self.created_at
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'traits': self.traits,
            'psi': self.psi,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


# ═══════════════════════════════════════════════════════════
# PersonalityEngine
# ═══════════════════════════════════════════════════════════

class PersonalityEngine:
    """
    Moteur de personnalité et d'émotions harmonique.
    
    La personnalité n'est pas un « system prompt » — c'est une
    configuration de l'espace des phases qui module toutes les
    réponses de façon géométrique.
    """
    
    def __init__(self, dim: int = DIM_PSI):
        self.dim = dim
        
        # État courant
        self._current_emotion = 'warm'
        self._current_personality_name = 'compagnon'
        self._emotion_params = dict(EMOTIONS)
        
        # Personnalités
        self._personalities: Dict[str, HarmonicPersonality] = {}
        self._load_default_personalities()
        
        # Historique émotionnel
        self._emotion_history: List[Tuple[str, float]] = []
        
        # Compteur de modulation
        self._modulation_count = 0
        
        # Signatures ψ des émotions (pré-calculées une fois — évite
        # 11 encodages par détection)
        self._emotion_psi: Dict[str, np.ndarray] = {}
        self._emotion_keywords = {
            'joyful':    ['heureux', 'joyeux', 'content', 'super', 'génial', 'excellent',
                         'formidable', 'youpi', 'hourra', 'yeah', ':)', '😊'],
            'sad':       ['triste', 'malheureux', 'déçu', 'chagrin', 'pleure', 'désolé',
                         'fatigué', 'déprimé', 'seul', ':(', '😢'],
            'urgent':    ['urgent', 'vite', 'immédiat', 'alerte', 'danger', 'aide',
                         'au secours', 'maintenant', 'tout de suite'],
            'excited':   ['excité', 'incroyable', 'wow', 'fantastique', 'magnifique',
                         'extraordinaire', 'wahou', '!!'],
            'calm':      ['calme', 'tranquille', 'paisible', 'serein', 'détendu',
                         'relax', 'zen'],
            'authoritative': ['sérieux', 'important', 'professionnel', 'officiel'],
            'playful':   ['drôle', 'amusant', 'rire', 'blague', 'jeu', 'mdr', 'lol'],
            'whisper':   ['secret', 'confidentiel', 'chuchote', 'discret'],
        }
        for em_name, params in self._emotion_params.items():
            desc = f"{em_name}_{params['pitch_shift']:.2f}_{params['energy_boost']:.2f}"
            self._emotion_psi[em_name] = text_to_psi(desc, dim)
    
    def _load_default_personalities(self):
        """Charge les archétypes par défaut."""
        for name, traits in ARCHETYPES.items():
            psi = self._traits_to_psi(traits, name)
            self._personalities[name] = HarmonicPersonality(
                name=name, traits=traits, psi=psi,
            )
    
    # ── TRAITS ↔ ψ ────────────────────────────────────────
    
    def _traits_to_psi(self, traits: Dict[str, float],
                       name: str = '') -> np.ndarray:
        """
        Convertit un profil Big Five en signature ψ.
        
        Chaque trait est un « formant » dans une bande de dimensions.
        L'intensité module l'amplitude et la phase dans cette bande.
        """
        psi = np.zeros(self.dim, dtype=np.complex128)
        
        for trait_name, trait_info in BIG_FIVE.items():
            intensity = traits.get(trait_name, 0.0)
            dims = trait_info['dims']
            phi_idx = trait_info['phi_idx']
            
            # Phase de base pour ce trait (φ-espacée)
            base_phase = (phi_idx * PHI) % 1.0 * TAU
            
            # Amplitude signée (négatif → opposition de phase)
            amp = abs(intensity)
            phase_shift = 0.0 if intensity >= 0 else math.pi
            
            for d in range(dims.start, min(dims.stop, self.dim)):
                local_idx = d - dims.start
                local_phase = (local_idx * PHI_INV) % 1.0 * TAU
                phase = base_phase + local_phase + phase_shift
                psi[d] = amp * (math.cos(phase) + 1j * math.sin(phase))
        
        # Normaliser
        norm = np.sqrt(np.sum(np.abs(psi) ** 2))
        if norm > 1e-10:
            psi /= norm
        return psi
    
    def _psi_to_traits(self, psi: np.ndarray) -> Dict[str, float]:
        """Extrait les traits Big Five d'une signature ψ (approché)."""
        traits = {}
        for trait_name, trait_info in BIG_FIVE.items():
            dims = trait_info['dims']
            band = psi[dims.start:min(dims.stop, self.dim)]
            # L'intensité est la norme de la bande
            energy = np.sqrt(np.sum(np.abs(band) ** 2))
            # La polarité est donnée par la phase moyenne
            mean_phase = np.mean(np.angle(band))
            polarity = 1.0 if abs(mean_phase) < math.pi / 2 else -1.0
            traits[trait_name] = float(energy * polarity * 2.5)  # Scale to [-1, 1]
        return traits
    
    # ── ÉMOTIONS ──────────────────────────────────────────
    
    def set_emotion(self, emotion: str):
        """Définit l'émotion courante."""
        if emotion not in self._emotion_params:
            raise ValueError(f"Émotion inconnue: {emotion}. Options: {list(self._emotion_params)}")
        self._current_emotion = emotion
        self._emotion_history.append((emotion, time.time()))
    
    def get_emotion(self) -> str:
        return self._current_emotion
    
    def get_emotion_params(self, emotion: str = None) -> dict:
        """Retourne les paramètres d'une émotion."""
        if emotion is None:
            emotion = self._current_emotion
        return self._emotion_params.get(emotion, self._emotion_params['neutral'])
    
    def add_custom_emotion(self, name: str, params: dict):
        """Ajoute une émotion personnalisée."""
        required = ['pitch_shift', 'energy_boost', 'speed_factor',
                   'breathiness', 'formant_spread']
        for k in required:
            if k not in params:
                raise ValueError(f"Paramètre '{k}' requis")
        self._emotion_params[name] = params
    
    def blend_emotions(self, emotion_a: str, emotion_b: str,
                       ratio: float = 0.5) -> dict:
        """
        Crée une émotion intermédiaire par interpolation φ.
        
        Args:
            emotion_a, emotion_b: noms des émotions
            ratio: 0.0 = pure A, 1.0 = pure B
            
        Returns:
            dict de paramètres blended
        """
        pa = self._emotion_params[emotion_a]
        pb = self._emotion_params[emotion_b]
        
        # Interpolation φ (non linéaire — plus naturelle)
        t = ratio ** PHI_INV
        
        blended = {}
        for key in pa:
            blended[key] = pa[key] * (1 - t) + pb[key] * t
        
        return blended
    
    def detect_emotion(self, text: str) -> Tuple[str, float]:
        """
        Détecte l'émotion dans un texte par résonance + mots-clés.
        
        Combine :
        1. Mots-clés émotionnels (prioritaires, 0.7)
        2. Résonance ψ (0.3, signatures pré-calculées)
        """
        text_lower = text.lower()
        
        # Score par mots-clés
        keyword_scores = {}
        for em, keywords in self._emotion_keywords.items():
            hits = sum(1 for kw in keywords if kw in text_lower)
            keyword_scores[em] = hits / max(len(keywords), 1) * 0.7
        
        # Score par résonance ψ (signatures pré-calculées — 1 seul encodage)
        psi_text = text_to_psi(text, self.dim)
        psi_scores = {}
        for em_name, psi_emotion in self._emotion_psi.items():
            score = psi_resonate(psi_text, psi_emotion)
            psi_scores[em_name] = (score + 1.0) / 2.0 * 0.3  # Normaliser, poids 0.3
        
        # Score combiné
        combined = {}
        for em in self._emotion_params:
            combined[em] = keyword_scores.get(em, 0) + psi_scores.get(em, 0)
        
        # Si aucun signal fort, chercher des indices plus subtils
        max_score = max(combined.values()) if combined else 0
        
        if max_score < 0.1:
            # Indices subtils : ponctuation, longueur, intensité
            if '!' in text and len(text) < 100:
                return 'excited', 0.6
            if '...' in text or text_lower.endswith(('...', '.')):
                return 'neutral', 0.5
            if '?' in text:
                return 'neutral', 0.5
            return 'neutral', 0.3
        
        best = max(combined, key=combined.get)
        return best, min(1.0, combined[best])
    
    def modulate_emotion(self, psi_frames: np.ndarray,
                         emotion: str = None) -> np.ndarray:
        """
        Applique la modulation émotionnelle aux frames ψ.
        
        Transformations géométriques dans ℂ⁵¹² :
        - Pitch shift → rotation de phase par dimension
        - Energy boost → amplification sélective
        - Breathiness → bruit φ-corrélé additif
        - Formant spread → dilatation/contraction spectrale
        """
        if emotion is None:
            emotion = self._current_emotion
        
        params = self._emotion_params.get(emotion, self._emotion_params['neutral'])
        
        psi = np.atleast_2d(psi_frames.copy())
        n_frames, dim = psi.shape
        
        if n_frames == 0:
            return psi
        
        # 1. Pitch shift (rotation de phase)
        pitch_shift = params['pitch_shift']
        if abs(pitch_shift) > 0.001:
            phase_per_dim = pitch_shift * TAU / dim
            for d in range(dim):
                rotation = complex(math.cos(phase_per_dim * d),
                                 math.sin(phase_per_dim * d))
                psi[:, d] *= rotation
        
        # 2. Energy boost (amplification des pics)
        energy = params['energy_boost']
        if abs(energy - 1.0) > 0.01:
            for i in range(n_frames):
                amps = np.abs(psi[i])
                threshold = np.median(amps) * 2
                mask = amps > threshold
                psi[i, mask] *= energy
        
        # 3. Breathiness (bruit φ-corrélé)
        breath = params['breathiness']
        if breath > 0.01:
            for i in range(n_frames):
                noise = (np.random.randn(dim) + 1j * np.random.randn(dim))
                noise *= breath * np.mean(np.abs(psi[i]))
                # Rendre le bruit φ-corrélé (moins artificiel)
                for d in range(1, dim):
                    noise[d] = noise[d] * (1 - PHI_INV) + noise[d-1] * PHI_INV
                psi[i] += noise
        
        # 4. Formant spread
        spread = params['formant_spread']
        if abs(spread - 1.0) > 0.01:
            mid = dim // 2
            for d in range(dim):
                dist = (d - mid) / mid
                scale = 1.0 + (spread - 1.0) * abs(dist)
                psi[:, d] *= scale
        
        # 5. Speed factor (si appliqué au niveau frames, ré-échantillonnage)
        speed = params['speed_factor']
        if abs(speed - 1.0) > 0.01 and n_frames > 2:
            new_n = max(2, int(n_frames / speed))
            old_idx = np.arange(n_frames)
            new_idx = np.linspace(0, n_frames - 1, new_n)
            new_psi = np.zeros((new_n, dim), dtype=np.complex128)
            for d in range(dim):
                new_psi[:, d] = (np.interp(new_idx, old_idx, psi[:, d].real) +
                                1j * np.interp(new_idx, old_idx, psi[:, d].imag))
            psi = new_psi
        
        self._modulation_count += 1
        return psi
    
    # ── PERSONNALITÉ ──────────────────────────────────────
    
    def set_personality(self, name: str):
        """Définit la personnalité courante."""
        if name not in self._personalities:
            raise ValueError(f"Personnalité inconnue: {name}. Options: {list(self._personalities)}")
        self._current_personality_name = name
    
    def get_personality(self) -> HarmonicPersonality:
        return self._personalities[self._current_personality_name]
    
    def create_personality(self, name: str, traits: Dict[str, float]) -> HarmonicPersonality:
        """Crée une personnalité personnalisée."""
        psi = self._traits_to_psi(traits, name)
        pers = HarmonicPersonality(name=name, traits=traits, psi=psi)
        self._personalities[name] = pers
        return pers
    
    def blend_personalities(self, name_a: str, name_b: str,
                            ratio: float = 0.5,
                            new_name: str = '') -> HarmonicPersonality:
        """
        Fusionne deux personnalités H_A + H_B = nouvelle personnalité.
        
        Unique au paradigme harmonique — impossible avec des LLMs.
        
        Args:
            name_a, name_b: noms des personnalités à fusionner
            ratio: 0.0 = pure A, 1.0 = pure B
            new_name: nom de la nouvelle personnalité (défaut: auto-généré)
        """
        pers_a = self._personalities[name_a]
        pers_b = self._personalities[name_b]
        
        # Interpolation φ des traits
        t = ratio ** PHI_INV
        blended_traits = {}
        for key in pers_a.traits:
            blended_traits[key] = pers_a.traits[key] * (1 - t) + pers_b.traits[key] * t
        
        # Interpolation des ψ (superposition pondérée)
        psi_blended = pers_a.psi * (1 - t) + pers_b.psi * t
        norm = np.sqrt(np.sum(np.abs(psi_blended) ** 2))
        if norm > 1e-10:
            psi_blended /= norm
        
        if not new_name:
            new_name = f"{name_a[:3]}_{name_b[:3]}_{int(ratio*100)}"
        
        pers = HarmonicPersonality(
            name=new_name,
            traits=blended_traits,
            psi=psi_blended,
        )
        self._personalities[new_name] = pers
        return pers
    
    def modulate_personality(self, psi: np.ndarray) -> np.ndarray:
        """
        Module un ψ par la personnalité courante.
        
        La personnalité agit comme un « filtre » : elle amplifie
        certaines dimensions et en atténue d'autres.
        """
        pers = self.get_personality()
        
        # La modulation de personnalité est un binding partiel
        # avec la signature de personnalité
        psi_pers = pers.psi
        
        # Produit de Hadamard (modulation par dimension)
        modulated = psi * (1.0 + 0.3 * psi_pers)
        
        norm = np.sqrt(np.sum(np.abs(modulated) ** 2))
        if norm > 1e-10:
            modulated /= norm
        
        return modulated
    
    def match_personality(self, text: str) -> Tuple[str, float]:
        """
        Trouve la personnalité la plus proche d'un texte.
        
        Utile pour : « Je voudrais un compagnon qui me ressemble »
        → analyse de la personnalité implicite de l'utilisateur.
        """
        psi_text = text_to_psi(text, self.dim)
        
        scores = {}
        for name, pers in self._personalities.items():
            score = psi_resonate(psi_text, pers.psi)
            scores[name] = (score + 1.0) / 2.0
        
        best = max(scores, key=scores.get)
        return best, scores[best]
    
    # ── PERSISTANCE ──────────────────────────────────────
    
    def save(self, user_id: str = 'default'):
        path = HOLOGRAM_DIR / f"personality_{user_id}.pkl"
        data = {
            'current_emotion': self._current_emotion,
            'current_personality': self._current_personality_name,
            'emotion_params': self._emotion_params,
            'personalities': {n: p.to_dict() for n, p in self._personalities.items()},
            'emotion_history': self._emotion_history[-50:],
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        return str(path)
    
    def load(self, user_id: str = 'default') -> bool:
        path = HOLOGRAM_DIR / f"personality_{user_id}.pkl"
        if not path.exists():
            return False
        
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self._current_emotion = data.get('current_emotion', 'warm')
        self._current_personality_name = data.get('current_personality', 'compagnon')
        self._emotion_params = data.get('emotion_params', dict(EMOTIONS))
        self._emotion_history = data.get('emotion_history', [])
        
        # Restaurer les personnalités
        for name, pdata in data.get('personalities', {}).items():
            self._personalities[name] = HarmonicPersonality(
                name=pdata['name'],
                traits=pdata['traits'],
                psi=np.array(pdata['psi'], dtype=np.complex128),
                created_at=pdata.get('created_at', 0),
                updated_at=pdata.get('updated_at', 0),
            )
        
        return True
    
    # ── STATISTIQUES ──────────────────────────────────────
    
    @property
    def available_emotions(self) -> List[str]:
        return list(self._emotion_params.keys())
    
    @property
    def available_personalities(self) -> List[str]:
        return list(self._personalities.keys())
    
    @property
    def stats(self) -> dict:
        return {
            'current_emotion': self._current_emotion,
            'current_personality': self._current_personality_name,
            'emotions_count': len(self._emotion_params),
            'personalities_count': len(self._personalities),
            'modulation_count': self._modulation_count,
            'emotion_history_len': len(self._emotion_history),
        }
    
    def __repr__(self) -> str:
        return (f"PersonalityEngine(emotion='{self._current_emotion}', "
                f"personality='{self._current_personality_name}', "
                f"{len(self._personalities)} archétypes)")


# ═══════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("  HARMONIC AI V5 — Personality Engine Test")
    print("=" * 60)
    
    # ── Init ──
    pers = PersonalityEngine()
    print(f"\n[1] Initialisation: {pers}")
    print(f"    Émotions: {pers.available_emotions}")
    print(f"    Personnalités: {pers.available_personalities}")
    
    # ── Test émotions ──
    print("\n[2] Test modulation émotionnelle...")
    psi_test = text_to_psi("Bonjour, comment allez-vous ?")
    
    for emotion in ['warm', 'joyful', 'sad', 'calm', 'excited']:
        pers.set_emotion(emotion)
        params = pers.get_emotion_params()
        psi_mod = pers.modulate_emotion(psi_test, emotion)
        coherence = psi_resonate(psi_test, psi_mod)
        print(f"    {emotion:12s}: pitch={params['pitch_shift']:+.2f} "
              f"energy={params['energy_boost']:.2f} "
              f"coherence(orig, mod)={coherence:.4f}")
    
    # ── Test détection d'émotion ──
    print("\n[3] Test détection d'émotion...")
    test_texts = [
        "Je suis tellement heureux aujourd'hui !",
        "Je me sens triste et fatigué...",
        "C'EST URGENT, RÉPONDS VITE !",
        "Quelle belle journée, tout va bien.",
        "Je voudrais te confier un secret...",
    ]
    for text in test_texts:
        emotion, confidence = pers.detect_emotion(text)
        print(f"    '{text[:50]}...' → {emotion} ({confidence:.3f})")
    
    # ── Test personnalités ──
    print("\n[4] Test personnalités...")
    for name in ['compagnon', 'empathique', 'joyeux', 'sage']:
        pers.set_personality(name)
        p = pers.get_personality()
        print(f"    {name:12s}: " + ", ".join(
            f"{k[:4]}={v:+.2f}" for k, v in p.traits.items()
        ))
    
    # ── Test fusion ──
    print("\n[5] Test fusion de personnalités...")
    blended = pers.blend_personalities('compagnon', 'sage', ratio=0.3, new_name='sage_compagnon')
    print(f"    Fusion compagnon(70%) + sage(30%) → '{blended.name}':")
    print(f"    " + ", ".join(f"{k[:4]}={v:+.2f}" for k, v in blended.traits.items()))
    
    # ── Test modulation de personnalité ──
    print("\n[6] Test modulation de personnalité sur ψ...")
    psi_orig = text_to_psi("Bonjour")
    psi_mod = pers.modulate_personality(psi_orig)
    print(f"    coherence(original, modulé) = {psi_resonate(psi_orig, psi_mod):.4f}")
    
    # ── Test création personnalisée ──
    print("\n[7] Test création de personnalité...")
    custom = pers.create_personality('mon_compagnon', {
        'openness': 0.7, 'conscientiousness': 0.6,
        'extraversion': 0.8, 'agreeableness': 0.9,
        'neuroticism': -0.4,
    })
    print(f"    Créé: {custom.name}")
    print(f"    Traits: " + ", ".join(f"{k[:4]}={v:+.2f}" for k, v in custom.traits.items()))
    
    # ── Stats ──
    print("\n[8] Statistiques...")
    for k, v in pers.stats.items():
        print(f"    {k}: {v}")
    
    print("\n✓ Personality Engine test terminé.")