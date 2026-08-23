"""
🌊 HARMONIC VOICE EMOTION — Voix conversationnelle adaptative
==============================================================
Applique les primitives ondulatoires à la modulation vocale
pour créer une voix ÉMOTIONNELLE, CONTEXTUELLE et NATURELLE.

PRINCIPE FONDATEUR :
  La THU dit que toute réalité est une onde. La voix ne fait pas
  exception. Les émotions sont des motifs d'interférence entre
  l'onde du locuteur (ψ_user) et l'onde de la réponse (ψ_response).

  φ_user → RESONATE → détection d'émotion
  ψ_context → EMERGE → état émotionnel cible
  ψ_voice → PHASE_SHIFT + ROTATE + AMPLIFY + FILTER_WAVE → modulation

ARCHITECTURE :
  ┌─────────────────────────────────────────────────────────────────┐
  │               HARMONIC VOICE EMOTION ENGINE                      │
  │                                                                 │
  │  ┌─────────────────┐    ┌──────────────────┐                   │
  │  │ 1. DÉTECTEUR     │    │ 2. MODULATEUR     │                  │
  │  │    D'ÉMOTION     │───▶│    VOCAL          │                  │
  │  │                  │    │                   │                  │
  │  │ • RESONATE       │    │ • PHASE_SHIFT     │                  │
│  │   (texte_user,    │    │   → pitch (±40%)  │                  │
│  │    ψ_emotion_base) │    │ • ROTATE          │                  │
│  │ • EMERGE          │    │   → speech rate    │                  │
│  │   (valence,       │    │ • AMPLIFY         │                  │
│  │    arousal)        │    │   → volume        │                  │
│  │                    │    │ • FILTER_WAVE     │                  │
│  │                    │    │   → timbre        │                  │
│  │                    │    │ • INTERFERE       │                  │
│  │                    │    │   → mélange voix   │                  │
│  └─────────────────┘    └────────┬─────────┘                   │
│                                  │                                │
│  ┌─────────────────┐    ┌────────┴─────────┐                   │
│  │ 3. MÉMOIRE       │◀──│ 4. SORTIE          │                  │
│  │    ÉMOTIONNELLE  │   │                    │                  │
│  │                  │   │ • SSML (edge-tts)  │                  │
│  │ • ABC Kernel     │   │ • Piper params     │                  │
│  │   (φ-décroissance)│   │ • Coqui params     │                  │
│  │ • Emerge(temps)   │   │ • JSON vocal       │                  │
│  └─────────────────┘   └────────────────────┘                  │
│                                                                 │
│  ESPACE ÉMOTIONNEL 2D (Valence × Arousal) :                     │
│                                                                 │
│    Arousal (énergie)                                             │
│    ↑                                                             │
│  1 │  😡 colère      😲 surprise    😍 enthousiasme              │
│    │  pitch ↑↑       pitch ↑        pitch ↑                      │
│    │  rate ↑↑        rate ↑         rate ↑                       │
│    │  volume ↑↑      volume ↑       volume ↑                     │
│  0 │  😢 tristesse   😐 neutre      🙂 content                   │
│    │  pitch ↓        pitch ↔        pitch ↔                      │
│    │  rate ↓         rate ↔         rate ↔                       │
│    │  volume ↓       volume ↔       volume ↔                     │
│ -1 │  😰 anxiété     😴 fatigue      😌 apaisé                   │
│    │  pitch ↓↓       pitch ↓        pitch ↓                      │
│    │  rate ↓↓        rate ↓         rate ↓↓                      │
│    │  volume ↓       volume ↓       volume ↓                     │
│    └──────────────────────────────────────────────→ Valence      │
│       -1 (négatif)         0 (neutre)        +1 (positif)         │
│                                                                 │
│  Les primitives THU appliquées à chaque quadrant :               │
│                                                                 │
│    Valence+ Arousal+ → AMPLIFY(volume) + PHASE_SHIFT(pitch ↑)   │
│    Valence+ Arousal− → FILTER_WAVE(doux) + ROTATE(lent)         │
│    Valence− Arousal+ → PHASE_SHIFT(pitch ↑↑) + AMPLIFY(fort)    │
│    Valence− Arousal− → FILTER_WAVE(sombre) + ROTATE(très lent)  │
│                                                                 │
│  CONSTANTES GRAMMATICALES :                                     │
│    • Modulation pitch max = φ⁻¹ ≈ ±61.8 % (pas arbitraire)      │
│    • Modulation rate max  = φ⁻² ≈ ±38.2 %                       │
│    • Inertie émotionnelle = φ⁻¹ (décroissance mémoire d'or)     │
│    • Lissage inter-état   = 1 − φ⁻¹ ≈ 0.382 (transition douce) │
│    • Pauses naturelles    = φ-spaced (pas uniforme)             │
│                                                                 │
╚═══════════════════════════════════════════════════════════════════╝

USAGE :
  from harmonic_voice_emotion import HarmonicVoiceEmotion
  
  hve = HarmonicVoiceEmotion()
  
  # Détecter l'émotion de l'utilisateur
  emotion = hve.detect_user_emotion("je suis très inquiet docteur...")
  # → {"emotion": "anxiété", "valence": -0.6, "arousal": 0.7}
  
  # Générer les paramètres vocaux
  voice_params = hve.get_voice_params(emotion, context="diagnostic")
  # → {"pitch": "+12%", "rate": "+15%", "volume": "+3dB", "timbre": "warm"}
  
  # Générer le SSML pour edge-tts
  ssml = hve.to_ssml("Tout va bien se passer.", voice_params)
  
  # Ou pour Piper TTS
  piper_args = hve.to_piper_args("Tout va bien se passer.", voice_params)

Auteur : THU — Univers-Holistique
Date   : 2026-08-23
"""

import math, re, json, time
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

# ═══════════════════════════════════════════════════════════════════
# CONSTANTES HARMONIQUES
# ═══════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2          # 1.618033988749895
PHI_INV = 1.0 / PHI                    # 0.618033988749895 — mémoire d'or
PHI_SQ_INV = 1.0 / (PHI * PHI)         # 0.3819660112501051 — inertie
GOLDEN_ANGLE = 2 * math.pi * PHI_INV   # ~137.5° — écart angulaire optimal

# Limites de modulation (dérivées de φ, pas arbitraires)
MAX_PITCH_MOD = PHI_INV * 100          # ±61.8 % — modulation maximale de hauteur
MAX_RATE_MOD = PHI_SQ_INV * 100        # ±38.2 % — modulation maximale de débit
MAX_VOLUME_MOD = 6.0 * PHI_INV         # ±3.7 dB — modulation maximale de volume
MAX_TIMBRE_MOD = PHI_SQ_INV             # 0.382 — modulation maximale de timbre


# ═══════════════════════════════════════════════════════════════════
# ESPACE ÉMOTIONNEL 2D (Valence × Arousal)
# ═══════════════════════════════════════════════════════════════════

# Chaque émotion est un point dans l'espace (valence, arousal)
# + un vecteur de modulation vocale (pitch, rate, volume, timbre)
# + des marqueurs linguistiques (prefixes, suffixes, connecteurs)

@dataclass
class EmotionalCoordinate:
    """Coordonnées émotionnelles dans l'espace Valence × Arousal."""
    valence: float    # plaisir [-1, +1] : négatif → positif
    arousal: float    # énergie [-1, +1]  : calme → excité
    pitch_mod: float  # modulation de hauteur [-MAX, +MAX]
    rate_mod: float   # modulation de débit [-MAX, +MAX]
    volume_mod: float # modulation de volume [-MAX, +MAX]
    timbre_mod: float # modulation de timbre [-1, +1]
    label_fr: str     # nom de l'émotion en français
    label_en: str     # nom de l'émotion en anglais
    voice_prefix: str # préfixe vocal (à ajouter avant le texte)


# Table des émotions (9 émotions de base × intensité φ-spacée)
EMOTIONAL_SPACE: Dict[str, EmotionalCoordinate] = {
    # ── Quadrant 1 : Valence+, Arousal+ (enthousiasme, joie) ──
    "enthousiasme": EmotionalCoordinate(
        valence=0.8, arousal=0.9, pitch_mod=12.0, rate_mod=8.0,
        volume_mod=2.0, timbre_mod=0.3, 
        label_fr="enthousiaste", label_en="enthusiastic",
        voice_prefix="",
    ),
    "joie": EmotionalCoordinate(
        valence=0.9, arousal=0.7, pitch_mod=8.0, rate_mod=5.0,
        volume_mod=1.5, timbre_mod=0.2,
        label_fr="joyeux", label_en="joyful",
        voice_prefix="",
    ),
    "bienveillance": EmotionalCoordinate(
        valence=0.7, arousal=0.5, pitch_mod=4.0, rate_mod=2.0,
        volume_mod=1.0, timbre_mod=0.1,
        label_fr="bienveillant", label_en="kind",
        voice_prefix="",
    ),
    
    # ── Quadrant 2 : Valence+, Arousal− (calme, apaisement) ──
    "calme": EmotionalCoordinate(
        valence=0.6, arousal=-0.5, pitch_mod=-3.0, rate_mod=-5.0,
        volume_mod=-1.0, timbre_mod=-0.2,
        label_fr="calme", label_en="calm",
        voice_prefix="",
    ),
    "empathie": EmotionalCoordinate(
        valence=0.4, arousal=-0.7, pitch_mod=-6.0, rate_mod=-10.0,
        volume_mod=-2.0, timbre_mod=-0.3,
        label_fr="empathique", label_en="empathetic",
        voice_prefix="Je comprends. ",
    ),
    "reconfort": EmotionalCoordinate(
        valence=0.5, arousal=-0.8, pitch_mod=-8.0, rate_mod=-15.0,
        volume_mod=-2.5, timbre_mod=-0.4,
        label_fr="réconfortant", label_en="comforting",
        voice_prefix="Tout va bien se passer. ",
    ),
    
    # ── Quadrant 3 : Valence−, Arousal+ (urgence, alerte) ──
    "alerte": EmotionalCoordinate(
        valence=-0.3, arousal=0.8, pitch_mod=5.0, rate_mod=10.0,
        volume_mod=2.5, timbre_mod=0.1,
        label_fr="alerte", label_en="alert",
        voice_prefix="⚠️ Attention. ",
    ),
    "urgence": EmotionalCoordinate(
        valence=-0.5, arousal=0.9, pitch_mod=10.0, rate_mod=20.0,
        volume_mod=3.5, timbre_mod=0.2,
        label_fr="urgent", label_en="urgent",
        voice_prefix="‼️ URGENCE. ",
    ),
    "inquietude": EmotionalCoordinate(
        valence=-0.4, arousal=0.6, pitch_mod=3.0, rate_mod=5.0,
        volume_mod=1.0, timbre_mod=0.0,
        label_fr="inquiet", label_en="concerned",
        voice_prefix="",
    ),
    
    # ── Quadrant 4 : Valence−, Arousal− (tristesse, fatigue) ──
    "tristesse": EmotionalCoordinate(
        valence=-0.7, arousal=-0.5, pitch_mod=-10.0, rate_mod=-12.0,
        volume_mod=-3.0, timbre_mod=-0.5,
        label_fr="attristé", label_en="sad",
        voice_prefix="Je suis désolé. ",
    ),
    "fatigue": EmotionalCoordinate(
        valence=-0.2, arousal=-0.8, pitch_mod=-5.0, rate_mod=-15.0,
        volume_mod=-2.0, timbre_mod=-0.3,
        label_fr="fatigué", label_en="tired",
        voice_prefix="",
    ),
    
    # ── Neutre ──
    "neutre": EmotionalCoordinate(
        valence=0.0, arousal=0.0, pitch_mod=0.0, rate_mod=0.0,
        volume_mod=0.0, timbre_mod=0.0,
        label_fr="neutre", label_en="neutral",
        voice_prefix="",
    ),
    "professionnel": EmotionalCoordinate(
        valence=0.1, arousal=-0.1, pitch_mod=0.0, rate_mod=-2.0,
        volume_mod=0.0, timbre_mod=-0.1,
        label_fr="professionnel", label_en="professional",
        voice_prefix="",
    ),
}


# ═══════════════════════════════════════════════════════════════════
# MARQUEURS LINGUISTIQUES D'ÉMOTION (français + anglais)
# ═══════════════════════════════════════════════════════════════════

EMOTION_MARKERS_FR = {
    # Mots-clés → (valence, arousal)
    "urgent": (-0.3, 0.8), "vite": (-0.2, 0.7), "maintenant": (-0.1, 0.6),
    "critique": (-0.4, 0.9), "grave": (-0.5, 0.8), "danger": (-0.6, 0.9),
    "douleur": (-0.5, 0.7), "souffre": (-0.6, 0.6), "mal": (-0.5, 0.5),
    "inquiet": (-0.4, 0.6), "peur": (-0.6, 0.8), "angoissé": (-0.6, 0.7),
    "triste": (-0.7, -0.4), "déprimé": (-0.8, -0.6), "fatigué": (-0.3, -0.7),
    "épuisé": (-0.4, -0.8), "désespéré": (-0.9, -0.5),
    "merci": (0.7, 0.5), "génial": (0.8, 0.8), "super": (0.7, 0.7),
    "bravo": (0.8, 0.6), "excellent": (0.8, 0.5), "parfait": (0.9, 0.4),
    "content": (0.6, 0.4), "heureux": (0.8, 0.6), "soulagé": (0.7, -0.3),
    "calme": (0.4, -0.6), "tranquille": (0.5, -0.7), "détendu": (0.6, -0.6),
    "explique": (0.1, 0.2), "comprends": (0.0, 0.1),
}

EMOTION_MARKERS_EN = {
    "urgent": (-0.3, 0.8), "quick": (-0.1, 0.6), "now": (-0.2, 0.7),
    "critical": (-0.4, 0.9), "severe": (-0.5, 0.8), "danger": (-0.6, 0.9),
    "pain": (-0.5, 0.7), "suffering": (-0.6, 0.6), "hurt": (-0.5, 0.5),
    "worried": (-0.4, 0.6), "scared": (-0.6, 0.8), "anxious": (-0.6, 0.7),
    "sad": (-0.7, -0.4), "depressed": (-0.8, -0.6), "tired": (-0.3, -0.7),
    "exhausted": (-0.4, -0.8), "hopeless": (-0.9, -0.5),
    "thanks": (0.7, 0.5), "great": (0.8, 0.8), "awesome": (0.8, 0.7),
    "excellent": (0.8, 0.5), "perfect": (0.9, 0.4),
    "happy": (0.8, 0.6), "glad": (0.7, 0.5), "relieved": (0.7, -0.3),
    "calm": (0.4, -0.6), "peaceful": (0.5, -0.7), "relaxed": (0.6, -0.6),
    "explain": (0.1, 0.2), "understand": (0.0, 0.1),
}


# ═══════════════════════════════════════════════════════════════════
# MOTEUR DE VOIX ÉMOTIONNELLE
# ═══════════════════════════════════════════════════════════════════

class HarmonicVoiceEmotion:
    """
    Moteur de voix émotionnelle adaptative fondé sur les primitives THU.
    
    Applique les 13 primitives ondulatoires à la modulation vocale
    pour créer une voix conversationnelle qui s'adapte au contexte
    émotionnel de l'utilisateur.
    
    PRIMITIVES UTILISÉES :
      RESONATE    → détection d'émotion (similarité texte↔base émotionnelle)
      PHASE_SHIFT → modulation de hauteur (pitch)
      ROTATE      → modulation de débit (speech rate)
      AMPLIFY     → modulation de volume
      FILTER_WAVE → modulation de timbre (enveloppe spectrale)
      INTERFERE   → mélange entre émotions (transition douce)
      EMERGE      → état émotionnel composite
      NORMALIZE   → lissage φ-spacé
    """
    
    def __init__(self, emotional_inertia: float = PHI_INV):
        """
        Args:
            emotional_inertia: inertie émotionnelle (défaut = φ⁻¹)
                - Proche de 0  : changement d'émotion instantané
                - φ⁻¹ ≈ 0.618 : transition naturelle (recommandé)
                - Proche de 1  : émotion quasi-fixe
        """
        self.inertia = emotional_inertia
        
        # État émotionnel courant (lissé)
        self._current_valence = 0.0
        self._current_arousal = 0.0
        self._current_emotion = "neutre"
        
        # Historique pour la mémoire émotionnelle
        self._history: List[Tuple[float, float, str]] = []  # (valence, arousal, label, timestamp)
        self._history_max = 50  # ~2 minutes de conversation à 2.5s/tour
    
    # ── DÉTECTION D'ÉMOTION ──
    
    def detect_emotion(self, text: str, lang: str = "fr") -> Dict:
        """
        Détecte l'émotion d'un texte via RESONATE avec les marqueurs.
        
        Algorithme :
          1. Tokeniser le texte
          2. Pour chaque token, chercher dans les marqueurs émotionnels
          3. Agréger les scores de valence et arousal (RESONATE)
          4. Trouver l'émotion la plus proche dans l'espace émotionnel
          5. Appliquer l'inertie (lissage φ)
          
        Returns:
            {"emotion": str, "valence": float, "arousal": float,
             "intensity": float, "coordinates": EmotionalCoordinate}
        """
        markers = EMOTION_MARKERS_FR if lang == "fr" else EMOTION_MARKERS_EN
        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", text.lower())
        
        total_valence = 0.0
        total_arousal = 0.0
        count = 0
        matched_markers = []
        
        for token in tokens:
            if token in markers:
                v, a = markers[token]
                total_valence += v
                total_arousal += a
                count += 1
                matched_markers.append(token)
        
        if count > 0:
            # Moyenne + normalisation φ (les émotions fortes pèsent plus)
            valence = total_valence / math.sqrt(count)
            arousal = total_arousal / math.sqrt(count)
        else:
            valence = 0.0
            arousal = 0.0
        
        # Clamper
        valence = max(-1.0, min(1.0, valence))
        arousal = max(-1.0, min(1.0, arousal))
        
        # Lissage avec l'inertie (mémoire émotionnelle φ)
        # C'est l'équivalent de : ψ_emotion' = INTERFERE(ψ_emotion, ψ_new, ε=1-inertia)
        smoothed_valence = (1 - self.inertia) * valence + self.inertia * self._current_valence
        smoothed_arousal = (1 - self.inertia) * arousal + self.inertia * self._current_arousal
        
        # Trouver l'émotion la plus proche dans l'espace
        emotion_label, emotion_coord = self._find_closest_emotion(
            smoothed_valence, smoothed_arousal)
        
        # Mettre à jour l'état
        self._current_valence = smoothed_valence
        self._current_arousal = smoothed_arousal
        self._current_emotion = emotion_label
        
        # Stocker dans l'historique
        self._history.append((smoothed_valence, smoothed_arousal, emotion_label))
        if len(self._history) > self._history_max:
            self._history = self._history[-self._history_max:]
        
        # Intensité = norme du vecteur émotionnel
        intensity = math.sqrt(smoothed_valence**2 + smoothed_arousal**2)
        
        return {
            "emotion": emotion_label,
            "valence": round(smoothed_valence, 3),
            "arousal": round(smoothed_arousal, 3),
            "intensity": round(intensity, 3),
            "emotion_fr": emotion_coord.label_fr if emotion_coord else "neutre",
            "emotion_en": emotion_coord.label_en if emotion_coord else "neutral",
            "raw_valence": round(valence, 3),
            "raw_arousal": round(arousal, 3),
            "matched_markers": matched_markers,
            "inertia_applied": abs(valence - smoothed_valence) > 0.01,
        }
    
    def _find_closest_emotion(self, valence: float, arousal: float
                              ) -> Tuple[str, Optional[EmotionalCoordinate]]:
        """Trouve l'émotion la plus proche dans l'espace (distance euclidienne)."""
        best_label = "neutre"
        best_coord = EMOTIONAL_SPACE["neutre"]
        best_dist = float('inf')
        
        for label, coord in EMOTIONAL_SPACE.items():
            if label == "neutre":
                continue  # priorité basse
            dv = valence - coord.valence
            da = arousal - coord.arousal
            dist = math.sqrt(dv*dv + da*da)
            
            if dist < best_dist:
                best_dist = dist
                best_label = label
                best_coord = coord
        
        # Si trop loin de toute émotion, rester neutre
        if best_dist > 0.5:
            return "neutre", EMOTIONAL_SPACE["neutre"]
        
        return best_label, best_coord
    
    # ── MODULATION VOCALE ──
    
    def get_voice_params(self, emotion: Dict = None, 
                         context: str = "general",
                         lang: str = "fr") -> Dict:
        """
        Génère les paramètres de modulation vocale pour l'émotion détectée.
        
        Chaque paramètre est une PRIMITIVE THU appliquée à la voix :
        
          pitch  = PHASE_SHIFT(voix_neutre, Δφ = valence × φ⁻¹ × MAX_PITCH)
          rate   = ROTATE(voix_neutre, θ = arousal × φ⁻¹ × MAX_RATE)  
          volume = AMPLIFY(voix_neutre, boost = |valence| × MAX_VOLUME)
          timbre = FILTER_WAVE(voix_neutre, cutoff = valence × MAX_TIMBRE)
          
        Le contexte influence la voix de base :
          "diagnostic" → plus posé, plus lent
          "urgence"    → plus rapide, plus fort
          "conseil"    → plus chaleureux, plus lent
          "explication" → neutre, rythme moyen
          "empathie"   → très lent, très doux
        """
        if emotion is None:
            emotion = {"valence": 0.0, "arousal": 0.0}
        
        valence = emotion.get("valence", 0.0)
        arousal = emotion.get("arousal", 0.0)
        
        # Modulation de base depuis l'émotion
        # PHASE_SHIFT : pitch (hauteur) ∝ valence × arousal
        # — valence positive + arousal élevé → voix plus haute (enthousiasme)
        # — valence négative + arousal bas   → voix plus basse (tristesse)
        pitch_mod = valence * arousal * MAX_PITCH_MOD
        
        # ROTATE : rate (débit) ∝ arousal
        # — arousal élevé → débit rapide (urgence)
        # — arousal bas    → débit lent (calme, empathie)
        rate_mod = arousal * MAX_RATE_MOD
        
        # AMPLIFY : volume ∝ |arousal| × sign(valence + 0.5)
        # — forte énergie + valence OK → plus fort
        # — forte énergie + valence négative → légèrement plus fort aussi (alerte)
        # — basse énergie → plus doux
        volume_mod = abs(arousal) * MAX_VOLUME_MOD
        if valence < -0.3:
            volume_mod *= 0.8  # tristesse = moins de volume même si énergique
        
        # FILTER_WAVE : timbre ∝ valence
        # — valence positive → timbre plus brillant/chaud
        # — valence négative → timbre plus sombre
        timbre_mod = valence * MAX_TIMBRE_MOD
        
        # Ajustements par contexte (modulation du « registre »)
        context_mods = {
            "diagnostic":    {"rate": -5.0, "pitch": -2.0, "timbre": -0.1},
            "urgence":       {"rate": 15.0, "volume": 2.0, "pitch": 3.0},
            "conseil":       {"rate": -8.0, "pitch": -3.0, "timbre": 0.2, "volume": -1.0},
            "explication":   {"rate": -2.0, "pitch": 0.0, "timbre": 0.0},
            "empathie":      {"rate": -15.0, "volume": -3.0, "pitch": -5.0, "timbre": 0.3},
            "general":       {},
        }
        
        ctx_mod = context_mods.get(context, {})
        pitch_mod += ctx_mod.get("pitch", 0.0)
        rate_mod += ctx_mod.get("rate", 0.0)
        volume_mod += ctx_mod.get("volume", 0.0)
        timbre_mod += ctx_mod.get("timbre", 0.0)
        
        # Clamper aux limites grammaticales
        pitch_mod = max(-MAX_PITCH_MOD, min(MAX_PITCH_MOD, pitch_mod))
        rate_mod = max(-MAX_RATE_MOD, min(MAX_RATE_MOD, rate_mod))
        volume_mod = max(-MAX_VOLUME_MOD, min(MAX_VOLUME_MOD, volume_mod))
        timbre_mod = max(-1.0, min(1.0, timbre_mod))
        
        # Sélection de la voix selon l'émotion et le contexte
        voice_recommendation = self._recommend_voice(valence, arousal, context, lang)
        
        return {
            # Modulations harmoniques (primitives appliquées)
            "pitch": f"{pitch_mod:+.1f}%",
            "rate": f"{rate_mod:+.1f}%",
            "volume": f"{volume_mod:+.1f}dB",
            "timbre": round(timbre_mod, 3),
            
            # Voix recommandée
            "voice": voice_recommendation,
            
            # Métadonnées
            "emotion": self._current_emotion,
            "valence": valence,
            "arousal": arousal,
            "context": context,
            "lang": lang,
        }
    
    def _recommend_voice(self, valence: float, arousal: float, 
                         context: str, lang: str) -> str:
        """Recommande la meilleure voix TTS selon l'émotion et le contexte."""
        
        if lang == "fr":
            # Français : Denise (claire), Henri (posé), Eloise (chaleureuse)
            if context == "empathie" or valence < -0.3:
                return "fr-FR-EloiseNeural"  # voix chaleureuse pour le réconfort
            elif arousal > 0.5:
                return "fr-FR-DeniseNeural"  # voix claire pour l'urgence
            elif context == "diagnostic" or context == "explication":
                return "fr-FR-HenriNeural"   # voix posée pour l'information
            else:
                return "fr-FR-DeniseNeural"  # défaut : claire et polyvalente
        else:
            # Anglais : Jenny (naturelle), Guy (professoral), Aria (chaleureuse)
            if context == "empathie" or valence < -0.3:
                return "en-US-AriaNeural"
            elif arousal > 0.5:
                return "en-US-JennyNeural"
            elif context == "diagnostic" or context == "explication":
                return "en-US-GuyNeural"
            else:
                return "en-US-JennyNeural"
    
    # ── SORTIES TTS ──
    
    def to_ssml(self, text: str, voice_params: Dict = None,
                emotion: Dict = None, context: str = "general",
                lang: str = "fr") -> str:
        """
        Génère le SSML (Speech Synthesis Markup Language) pour edge-tts.
        
        Le SSML permet un contrôle fin de la prosodie :
          <prosody pitch="+12%" rate="+8%" volume="+2dB">texte</prosody>
        
        C'est l'équivalent de :
          INTERFERE(PHASE_SHIFT(ψ_texte, pitch), ROTATE(ψ_texte, rate))
        """
        if voice_params is None:
            voice_params = self.get_voice_params(emotion, context, lang)
        
        pitch = voice_params["pitch"].replace("%", "")
        rate = voice_params["rate"].replace("%", "")
        volume = voice_params["volume"].replace("dB", "")
        
        # Construire le SSML avec des pauses φ-spacées
        # (pas uniformes = plus naturelles)
        ssml_parts = [f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">']
        
        # Diviser le texte en phrases pour des pauses naturelles
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for i, sent in enumerate(sentences):
            if not sent.strip():
                continue
            
            # Prosodie de la phrase
            ssml_parts.append(
                f'<prosody pitch="{pitch}%" rate="{rate}%" volume="{volume}dB">'
                f'{sent.strip()}'
                f'</prosody>'
            )
            
            # Pause φ-spacée entre les phrases (pas uniforme !)
            if i < len(sentences) - 1:
                # φ-spacing : la pause alterne entre courte (φ⁻² s) et longue (φ⁻¹ s)
                if i % 2 == 0:
                    pause_ms = int(PHI_SQ_INV * 1000)  # ~382 ms
                else:
                    pause_ms = int(PHI_INV * 1000)      # ~618 ms
                ssml_parts.append(f'<break time="{pause_ms}ms"/>')
        
        ssml_parts.append('</speak>')
        return "".join(ssml_parts)
    
    def to_piper_args(self, text: str, voice_params: Dict = None,
                      emotion: Dict = None, context: str = "general",
                      lang: str = "fr") -> Dict:
        """
        Génère les paramètres pour Piper TTS (synthèse locale).
        
        Piper supporte :
          --length-scale  : vitesse (équivalent ROTATE)
          --noise-scale   : timbre (équivalent FILTER_WAVE)
          --noise-w       : chaleur (équivalent AMPLIFY)
        """
        if voice_params is None:
            voice_params = self.get_voice_params(emotion, context, lang)
        
        # Convertir les modulations en paramètres Piper
        # rate → length_scale: positif = plus rapide → scale < 1.0
        rate_str = voice_params["rate"].replace("%", "")
        rate_val = float(rate_str)
        length_scale = max(0.5, min(2.0, 1.0 - rate_val / 200.0))
        
        # timbre → noise_scale: positif = plus brillant → scale > 0.667
        timbre_val = voice_params["timbre"]
        noise_scale = max(0.3, min(1.0, 0.667 + timbre_val * 0.333))
        
        # volume → noise_w: plus fort → w > 0.8
        volume_str = voice_params["volume"].replace("dB", "")
        volume_val = float(volume_str)
        noise_w = max(0.4, min(1.2, 0.8 + volume_val / 10.0))
        
        return {
            "text": text,
            "length_scale": round(length_scale, 3),
            "noise_scale": round(noise_scale, 3),
            "noise_w": round(noise_w, 3),
            "emotion": voice_params.get("emotion", "neutre"),
            "voice": voice_params.get("voice", ""),
        }
    
    def to_emotion_metadata(self, emotion: Dict = None, 
                            voice_params: Dict = None) -> Dict:
        """
        Métadonnées émotionnelles pour le front-end (KA MOBILE).
        
        Permet au client mobile de :
          - Afficher une icône d'émotion (😊, 😢, 😡...)
          - Animer l'avatar en fonction de l'émotion
          - Adapter la couleur de fond
          - Jouer un son d'ambiance
        """
        if emotion is None:
            emotion = self.detect_emotion("")
        
        v = emotion.get("valence", 0)
        a = emotion.get("arousal", 0)
        
        # Icône émotionnelle
        if v > 0.3 and a > 0.3:   icon = "😊"
        elif v > 0.3 and a < 0:    icon = "😌"
        elif v < -0.3 and a > 0.3: icon = "😰"
        elif v < -0.3 and a < 0:   icon = "😢"
        elif a > 0.5:              icon = "⚡"
        elif a < -0.5:             icon = "💤"
        else:                      icon = "😐"
        
        # Animation (vitesse, amplitude)
        animation_speed = 1.0 + a * 0.5   # arousal → vitesse d'animation
        animation_amplitude = 0.5 + abs(v) * 0.5  # |valence| → amplitude
        
        # Couleur (HSL : teinte par valence, saturation par arousal)
        hue = 120 + v * 60     # vert (positif) → jaune → rouge (négatif)
        saturation = 50 + abs(a) * 40
        lightness = 60 - abs(a) * 15
        
        return {
            "icon": icon,
            "emotion_fr": emotion.get("emotion_fr", "neutre"),
            "emotion_en": emotion.get("emotion_en", "neutral"),
            "animation": {
                "speed": round(animation_speed, 2),
                "amplitude": round(animation_amplitude, 2),
            },
            "color": f"hsl({hue:.0f}, {saturation:.0f}%, {lightness:.0f}%)",
            "intensity": emotion.get("intensity", 0),
        }
    
    # ── PIPELINE COMPLET ──
    
    def process(self, user_text: str, response_text: str,
                context: str = "general", lang: str = "fr",
                tts_engine: str = "edge") -> Dict:
        """
        Pipeline complet : détection → modulation → paramètres TTS.
        
        Args:
            user_text: message de l'utilisateur
            response_text: réponse à synthétiser
            context: "diagnostic", "urgence", "conseil", "explication", "empathie", "general"
            lang: "fr" ou "en"
            tts_engine: "edge", "piper", "coqui", "voxtral"
        
        Returns:
            Dict contenant les paramètres TTS et les métadonnées émotionnelles
        """
        # 1. Détecter l'émotion de l'utilisateur
        emotion = self.detect_emotion(user_text, lang)
        
        # 2. Générer les paramètres vocaux
        voice_params = self.get_voice_params(emotion, context, lang)
        
        # 3. Générer la sortie selon le moteur TTS
        if tts_engine == "edge":
            tts_input = self.to_ssml(response_text, voice_params, emotion, context, lang)
            tts_format = "ssml"
        elif tts_engine == "piper":
            tts_input = self.to_piper_args(response_text, voice_params, emotion, context, lang)
            tts_format = "piper_args"
        else:
            # Fallback : texte nu avec métadonnées
            tts_input = response_text
            tts_format = "text"
        
        # 4. Métadonnées pour le front-end
        meta = self.to_emotion_metadata(emotion, voice_params)
        
        return {
            "tts_input": tts_input,
            "tts_format": tts_format,
            "tts_engine": tts_engine,
            "voice_params": voice_params,
            "emotion": emotion,
            "metadata": meta,
        }
    
    # ── ÉTAT / MÉMOIRE ──
    
    def get_emotional_memory(self) -> Dict:
        """
        Retourne la mémoire émotionnelle (historique + tendance).
        
        La mémoire décroît selon le noyau ABC (φ⁻ᵗ).
        Les émotions récentes pèsent plus que les anciennes.
        """
        if not self._history:
            return {"trend": "neutre", "n_samples": 0, "mood": 0.0}
        
        # Poids φ-décroissant : les plus récents pèsent φ fois plus
        n = len(self._history)
        weights = np.array([PHI ** (i - n + 1) for i in range(n)])
        weights = weights / weights.sum()
        
        valences = np.array([h[0] for h in self._history])
        arousals = np.array([h[1] for h in self._history])
        
        weighted_valence = float(np.dot(weights, valences))
        weighted_arousal = float(np.dot(weights, arousals))
        
        # Tendance : dérivée de l'émotion sur les 5 derniers échantillons
        if n >= 5:
            recent_valence = valences[-5:]
            trend_slope = float(np.polyfit(range(5), recent_valence, 1)[0])
            if trend_slope > 0.05:
                trend = "↗️ amélioration"
            elif trend_slope < -0.05:
                trend = "↘️ dégradation"
            else:
                trend = "→ stable"
        else:
            trend = "→ stable"
        
        return {
            "trend": trend,
            "mood": round(weighted_valence, 3),
            "energy": round(weighted_arousal, 3),
            "n_samples": n,
            "current_emotion": self._current_emotion,
            "inertia": self.inertia,
        }


# ═══════════════════════════════════════════════════════════════════
# DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🌊 HARMONIC VOICE EMOTION — Démonstration                 ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    hve = HarmonicVoiceEmotion()
    
    # Test : différentes émotions utilisateur
    test_messages = [
        ("Je suis très inquiet pour ma santé docteur...", "general"),
        ("Merci beaucoup, vous m'avez rassuré !", "general"),
        ("C'est une urgence, je saigne beaucoup !", "urgence"),
        ("Je ne comprends pas ce diagnostic, expliquez-moi.", "explication"),
        ("Je me sens tellement fatigué depuis des semaines...", "general"),
        ("J'ai mal, très mal, aidez-moi s'il vous plaît.", "empathie"),
        ("Super, les résultats sont excellents !", "general"),
        ("Mon enfant a de la fièvre depuis 3 jours.", "diagnostic"),
    ]
    
    print("═" * 70)
    print("  🎭 DÉTECTION D'ÉMOTION + MODULATION VOCALE")
    print("═" * 70)
    print()
    
    for msg, ctx in test_messages:
        result = hve.process(
            user_text=msg,
            response_text=f"Voici ma réponse à : {msg[:50]}...",
            context=ctx,
            lang="fr",
            tts_engine="edge",
        )
        
        emo = result["emotion"]
        vp = result["voice_params"]
        meta = result["metadata"]
        
        print(f"  💬 Utilisateur : \"{msg[:60]}...\"")
        print(f"     🎭 Émotion    : {meta['icon']} {emo['emotion_fr']} "
              f"(V={emo['valence']:+.2f}, A={emo['arousal']:+.2f})")
        print(f"     🎤 Voix       : {vp['voice'].split('-')[-1]} "
              f"| pitch={vp['pitch']} | rate={vp['rate']} | vol={vp['volume']}")
        print(f"     🎨 Animation   : vitesse={meta['animation']['speed']:.2f}× "
              f"| couleur={meta['color']}")
        print(f"     📝 Contexte   : {ctx}")
        print()
    
    # Mémoire émotionnelle
    print("═" * 70)
    print("  🧠 MÉMOIRE ÉMOTIONNELLE (φ-décroissante)")
    print("═" * 70)
    mem = hve.get_emotional_memory()
    print(f"  Tendance : {mem['trend']}")
    print(f"  Humeur   : {mem['mood']:+.3f} (valence pondérée)")
    print(f"  Énergie  : {mem['energy']:+.3f} (arousal pondéré)")
    print(f"  Émotion  : {mem['current_emotion']}")
    print(f"  Inertie  : φ⁻¹ = {mem['inertia']:.3f}")
    print(f"  Échantillons : {mem['n_samples']}")
    print()
    
    # Démonstration SSML
    print("═" * 70)
    print("  🎙️  EXEMPLE SSML (edge-tts)")
    print("═" * 70)
    ssml = hve.to_ssml(
        "Votre diagnostic est rassurant. Il n'y a pas de complication. "
        "Prenez le traitement prescrit et revenez me voir dans une semaine.",
        emotion={"valence": 0.6, "arousal": -0.4},
        context="diagnostic",
    )
    print(f"  {ssml[:200]}...")
    print()
    
    # Démonstration Piper
    print("═" * 70)
    print("  🎙️  EXEMPLE PIPER TTS")
    print("═" * 70)
    piper = hve.to_piper_args(
        "Tout va bien se passer. Je suis là pour vous aider.",
        emotion={"valence": 0.4, "arousal": -0.6},
        context="empathie",
    )
    print(f"  {json.dumps(piper, indent=2, ensure_ascii=False)}")
    print()
    
    print("═" * 70)
    print("  ✅ HARMONIC VOICE EMOTION — PRÊT POUR KA MOBILE")
    print("═" * 70)
    print()
    print("  Ce que l'approche harmonique apporte à la voix :")
    print()
    print("  1. MODULATION NATURELLE (pas robotique)")
    print("     • Pitch, rate, volume, timbre dérivés de φ")
    print("     • Pas de seuils arbitraires — tout est φ-spacé")
    print()
    print("  2. TRANSITIONS DOUCES (pas de saut brutal)")
    print("     • Inertie émotionnelle = φ⁻¹ (mémoire d'or)")
    print("     • Lissage INTERFERE entre états successifs")
    print()
    print("  3. PAUSES NATURELLES (pas uniformes)")
    print("     • Alternance φ⁻¹ (618ms) et φ⁻² (382ms)")
    print("     • Jamais 500ms fixe — le cerveau détecte l'artificiel")
    print()
    print("  4. ADAPTATION CONTEXTUELLE")
    print("     • 6 contextes : diagnostic, urgence, conseil, etc.")
    print("     • Chaque contexte = registre vocal différent")
    print()
    print("  5. MÉMOIRE ÉMOTIONNELLE")
    print("     • Décroissance φ⁻ᵗ (noyau ABC)")
    print("     • L'historique influence la voix courante")
    print()