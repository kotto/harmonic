#!/usr/bin/env python3
"""
HARMONIC SPEECH ORCHESTRATOR — Contrôle intelligent de la parole
===================================================================
Interface haut niveau pour le pipeline vocal KA :
  Micro → STT (Whisper) → KA Core → Speech Orchestrator → TTS (XTTS) → Audio

Contrairement à un simple TTS, cet orchestrateur :
  1. Détecte l'émotion du contexte conversationnel
  2. Sélectionne la voix appropriée (Kemet, Moderne, Sage...)
  3. Applique des templates prosodiques (φ-proportions)
  4. Contrôle la vitesse et la hauteur par mémoire ABC

Le réseau de neurones TTS est le haut-parleur.
L'Orchestrator est le cerveau qui décide QUOI dire et COMMENT.

Usage :
  from harmonic_speech_orchestrator import HarmonicSpeechOrchestrator
  hso = HarmonicSpeechOrchestrator()
  audio_path = hso.speak("Bonjour, je suis KA Phone.")
  # → data/speech/output_abc123.wav
"""

import os, sys, time, random, math, json, re, wave, io, tempfile, hashlib
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np

PHI = 1.618033988749895
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data", "speech")
os.makedirs(DATA_DIR, exist_ok=True)

# ═══ AUDIO POST-PROCESSOR ═══
try:
    from harmonic_audio_postprocessor import HarmonicAudioPostProcessor
    audio_enhancer = HarmonicAudioPostProcessor()
    HAS_AUDIO_ENHANCER = True
except ImportError:
    audio_enhancer = None
    HAS_AUDIO_ENHANCER = False

# ══════════════════════════════════════════════════════════════════════════
# VOICE PROFILES
# ══════════════════════════════════════════════════════════════════════════

VOICE_PROFILES = {
    "kemet_sage": {
        "name": "Le Sage de Kemet",
        "description": "Voix grave, lente, sage — parfait pour les réponses sur Kemet et l'Afrique",
        "speed": 0.85,       # Plus lent que la normale
        "pitch_shift": -0.15, # Plus grave
        "energy": 0.7,        # Moins d'énergie (calme)
        "pauses": 1.3,        # Pauses plus longues
        "emotion": "serene",
        "template": "conte",
    },
    "kemet_moderne": {
        "name": "La Voix Moderne de Kemet",
        "description": "Voix claire, dynamique, jeune — pour les conversations quotidiennes",
        "speed": 1.0,
        "pitch_shift": 0.0,
        "energy": 0.9,
        "pauses": 1.0,
        "emotion": "neutral",
        "template": "discours",
    },
    "griot": {
        "name": "Le Griot",
        "description": "Voix de conteur africain — pour les histoires et légendes",
        "speed": 0.9,
        "pitch_shift": -0.05,
        "energy": 0.85,
        "pauses": 1.2,
        "emotion": "inspirational",
        "template": "conte",
    },
    "enfant": {
        "name": "L'Enfant de Kemet",
        "description": "Voix plus aiguë, curieuse — pour les réponses éducatives",
        "speed": 1.05,
        "pitch_shift": 0.2,
        "energy": 0.8,
        "pauses": 0.9,
        "emotion": "curious",
        "template": "lecon",
    },
    "poete": {
        "name": "Le Poète",
        "description": "Voix lyrique, rythmée — pour les poèmes et créations",
        "speed": 0.95,
        "pitch_shift": 0.05,
        "energy": 0.75,
        "pauses": 1.1,
        "emotion": "lyrical",
        "template": "poeme_libre",
    },
}

# ══════════════════════════════════════════════════════════════════════════
# PROSODIC TEMPLATES (comme PoeticKB mais pour la voix)
# ══════════════════════════════════════════════════════════════════════════

PROSODIC_TEMPLATES = {
    "factuel": {
        "pattern": r"(?:quelle|quel|quand|combien|qui|quoi|comment|definition|capital|date)",
        "speed": 1.0, "pitch_shift": 0.0, "energy": 0.8, "pauses": 1.0,
        "prefix_phrases": ["Voici la réponse : ", "Je te réponds : ", "D'après mes sources : "],
        "suffix_phrases": ["Voilà.", "C'est tout.", "J'espère que cela t'aide."],
    },
    "emotionnel": {
        "pattern": r"(?:aime|déteste|heureux|triste|peur|joie|amour|colère|merci|désolé)",
        "speed": 1.1, "pitch_shift": 0.1, "energy": 0.95, "pauses": 0.8,
        "prefix_phrases": ["Oh, je comprends ! ", "Écoute : ", "Laisse-moi te dire : "],
        "suffix_phrases": ["Je suis avec toi.", "C'est important.", "N'oublie jamais ça."],
    },
    "conte": {
        "pattern": r"(?:raconte|histoire|conte|légende|mythe|jadis|autrefois|il était)",
        "speed": 0.85, "pitch_shift": -0.05, "energy": 0.7, "pauses": 1.3,
        "prefix_phrases": ["Écoute bien... ", "Je vais te raconter... ", "Les anciens disaient : "],
        "suffix_phrases": ["Ainsi finit l'histoire.", "Et c'est depuis ce jour que...", "Voilà, tu sais tout."],
    },
    "mathematique": {
        "pattern": r"(?:calcule|résous|dérivée|intégrale|équation|solve|compute)",
        "speed": 0.95, "pitch_shift": 0.0, "energy": 0.85, "pauses": 1.1,
        "prefix_phrases": ["Analysons cela : ", "Voici le calcul : ", "Regardons ensemble : "],
        "suffix_phrases": ["C'est la solution.", "Le calcul est terminé.", "Pas d'erreur possible."],
    },
}


# ══════════════════════════════════════════════════════════════════════════
# HARMONIC SPEECH ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════

class HarmonicSpeechOrchestrator:
    """
    Orchestre la parole de KA : décide QUOI dire, COMMENT le dire,
    et passe la commande au synthétiseur vocal (TTS).
    
    Le TTS n'est qu'un instrument. L'Orchestrator est le musicien.
    """

    def __init__(self, voice_profile: str = "kemet_moderne"):
        """
        Args:
            voice_profile: "kemet_sage", "kemet_moderne", "griot", "enfant", "poete"
        """
        self.voice_profile = voice_profile
        self.voice_config = VOICE_PROFILES.get(voice_profile, VOICE_PROFILES["kemet_moderne"])
        self.tts_engine = self._init_tts()
        self.stats = {"total_speech_generated": 0, "total_duration_ms": 0}

    def _init_tts(self):
        """
        Initialise le moteur TTS.
        Priorité : 1. XTTS-v2 (si installé), 2. Piper (fallback), 3. Synthèse de base
        """
        engine = {"type": "none", "available": False}
        
        # Essayer Piper (déjà intégré à speech_service.py)
        try:
            from speech_service import SpeechService
            svc = SpeechService()
            if svc.piper_available:
                engine = {"type": "piper", "instance": svc, "available": True}
        except:
            pass
        
        # Essayer XTTS (qualité supérieure si installé)
        try:
            from TTS.api import TTS
            tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
            engine = {"type": "xtts", "instance": tts, "available": True}
        except:
            pass
        
        print(f"[SpeechOrchestrator] TTS engine: {engine['type']} (available: {engine['available']})")
        return engine

    # ═══ INTERFACE PRINCIPALE ═══

    def speak(self, text: str, voice_profile: str = None, 
              context: Dict = None, output_path: str = None) -> Dict:
        """
        Transforme un texte en parole avec contrôle prosodique complet.
        
        Args:
            text: texte à synthétiser
            voice_profile: override de la voix
            context: contexte conversationnel (pour détection émotion)
            output_path: chemin de sortie (None = auto)
            
        Returns:
            Dict avec 'audio_path', 'duration_s', 'voice', 'prosody'
        """
        t0 = time.time()
        
        # Step 1: Sélection de la voix
        voice = VOICE_PROFILES.get(voice_profile, self.voice_config) if voice_profile else self.voice_config
        
        # Step 2: Détection prosodique (quel TEMPLATE utiliser)
        prosody = self._detect_prosody(text, context or {})
        
        # Step 3: Enrichissement du texte (préfixes/suffixes prosodiques)
        enriched_text = self._enrich_text(text, prosody)
        
        # Step 4: Application des paramètres de voix
        speech_params = self._compute_speech_params(voice, prosody)
        
        # Step 5: Synthèse vocale (avec streaming TTS + cache si disponible)
        duration_s = 0.0
        try:
            from tts_streaming import TTSStreamingService
            streaming_tts = TTSStreamingService()
            if not output_path:
                text_hash = hashlib.md5(enriched_text.encode()).hexdigest()[:8]
                output_path = os.path.join(DATA_DIR, f"speech_{text_hash}.wav")
            
            # Utiliser le streaming TTS avec cache
            audio_bytes = streaming_tts.speak_cached(enriched_text, voice="denise", speed=speech_params.get("speed", 1.0))
            if audio_bytes:
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
                duration_s = self._get_audio_duration(output_path)
            else:
                duration_s = self._synthesize(enriched_text, speech_params, output_path)
        except ImportError:
            if not output_path:
                text_hash = hashlib.md5(enriched_text.encode()).hexdigest()[:8]
                output_path = os.path.join(DATA_DIR, f"speech_{text_hash}.wav")
            duration_s = self._synthesize(enriched_text, speech_params, output_path)
        
        # === POST- PROCESSING HARMONIQUE ===
        if HAS_AUDIO_ENHANCER and os.path.exists(output_path):
            try:
                audio_enhancer.process(
                    output_path, output_path,
                    pitch_shift=speech_params.get("pitch_shift", 0.0),
                    boost_strength=0.12,
                    noise_reduction=True,
                    abc_smoothing=True
                )
            except Exception:
                pass  # L'audio est déjà fonctionnel sans post-processing
        
        dt_ms = (time.time() - t0) * 1000
        self.stats["total_speech_generated"] += 1
        self.stats["total_duration_ms"] += dt_ms
        
        return {
            "audio_path": output_path,
            "duration_s": duration_s,
            "voice": voice["name"],
            "voice_profile": voice_profile or self.voice_profile,
            "prosody_template": prosody["template_name"],
            "speed": speech_params["speed"],
            "pitch": speech_params["pitch_shift"],
            "synthesis_time_ms": dt_ms,
        }

    def speak_response(self, prompt: str, response_text: str, 
                       conversation_context: Dict = None) -> Dict:
        """
        Version complète : prend le prompt original + la réponse KA,
        et orchestre la parole avec tout le contexte.
        
        Args:
            prompt: question originale de l'utilisateur
            response_text: réponse générée par KA
            conversation_context: contexte du ConversationOrchestrator
            
        Returns:
            Dict avec audio + métadonnées
        """
        # Analyser le prompt pour déterminer l'émotion et le style
        prosody = self._detect_prosody(prompt, conversation_context or {})
        
        # Choisir la voix en fonction du domaine
        if conversation_context and conversation_context.get("topic"):
            topic = conversation_context["topic"]
            if topic in ("kemet", "africa"):
                voice = "kemet_sage"
            elif topic == "creative":
                voice = "poete"
            elif topic in ("science", "tech"):
                voice = "kemet_moderne"
            else:
                voice = self.voice_profile
        else:
            voice = self.voice_profile
        
        return self.speak(response_text, voice_profile=voice, context=conversation_context)

    # ═══ PROSODY DETECTION ═══

    def _detect_prosody(self, text: str, context: Dict) -> Dict:
        """
        Détecte le template prosodique le plus approprié.
        Même architecture que SceneDetector mais pour la voix.
        """
        p = text.lower()
        scores = {}
        
        for template_name, config in PROSODIC_TEMPLATES.items():
            score = 0
            if re.search(config["pattern"], p, re.IGNORECASE):
                score += 2.0
            # Bonus si le contexte conversationnel correspond
            if context.get("topic") == "creative" and template_name == "conte":
                score += 1.0
            if context.get("topic") in ("science", "math") and template_name == "mathematique":
                score += 1.0
            if context.get("topic") in ("geography", "history") and template_name == "factuel":
                score += 1.0
            if score > 0:
                scores[template_name] = score
        
        if not scores:
            return {"template_name": "factuel", **PROSODIC_TEMPLATES["factuel"]}
        
        best = max(scores, key=scores.get)
        return {"template_name": best, **PROSODIC_TEMPLATES[best]}

    def _enrich_text(self, text: str, prosody: Dict) -> str:
        """Ajoute des préfixes/suffixes prosodiques pour guider le TTS."""
        enriched = text.strip()
        
        # Ajouter un préfixe (30% du temps pour éviter la monotonie)
        if random.random() < 0.3 and prosody.get("prefix_phrases"):
            prefix = random.choice(prosody["prefix_phrases"])
            enriched = prefix + enriched
        
        # Ajouter un suffixe (20% du temps)
        if random.random() < 0.2 and prosody.get("suffix_phrases"):
            suffix = random.choice(prosody["suffix_phrases"])
            enriched = enriched + " " + suffix
        
        return enriched

    def _compute_speech_params(self, voice: Dict, prosody: Dict) -> Dict:
        """
        Calcule les paramètres de synthèse finaux en combinant
        la voix et le template prosodique.
        """
        return {
            "speed": voice["speed"] * prosody.get("speed", 1.0),
            "pitch_shift": voice["pitch_shift"] + prosody.get("pitch_shift", 0.0),
            "energy": voice["energy"] * prosody.get("energy", 0.8),
            "pauses": voice["pauses"] * prosody.get("pauses", 1.0),
            "emotion": prosody.get("emotion", voice["emotion"]),
        }

    # ═══ TTS BACKEND ═══

    def _synthesize(self, text: str, params: Dict, output_path: str) -> float:
        """
        Synthétise le texte en audio via le meilleur backend disponible.
        
        Returns:
            Durée audio en secondes
        """
        engine = self.tts_engine
        
        if engine["type"] == "xtts" and engine["available"]:
            return self._synth_xtts(text, params, output_path, engine["instance"])
        
        elif engine["type"] == "piper" and engine["available"]:
            return self._synth_piper(text, params, output_path, engine["instance"])
        
        else:
            # Fallback ultime : synthèse sinusoïdale de base
            return self._synth_fallback(text, params, output_path)

    def _synth_piper(self, text: str, params: Dict, output_path: str, svc) -> float:
        """Synthèse via Piper TTS (open-source, local)."""
        try:
            svc.synthesize(text, output_path)
            return self._get_audio_duration(output_path)
        except:
            return self._synth_fallback(text, params, output_path)

    def _synth_xtts(self, text: str, params: Dict, output_path: str, tts) -> float:
        """Synthèse via XTTS-v2 (qualité supérieure)."""
        # XTTS supporte le contrôle de vitesse/langue
        language = "fr"
        try:
            tts.tts_to_file(
                text=text,
                language=language,
                file_path=output_path,
                speed=params.get("speed", 1.0),
            )
            return self._get_audio_duration(output_path)
        except:
            return self._synth_piper_or_fallback(text, params, output_path)

    def _synth_fallback(self, text: str, params: Dict, output_path: str) -> float:
        """
        Synthèse sinusoïdale de base (toujours disponible, 0 dépendance).
        Génère un son sinusoïdal modulé — pas de la parole, mais ça parle.
        """
        sample_rate = 22050
        duration = max(0.5, len(text) * 0.08)  # ~80ms par caractère
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        
        # Fréquence porteuse basée sur le pitch
        base_freq = 220 * (PHI ** params.get("pitch_shift", 0.0))  # φ-proportions
        carrier = np.sin(2 * np.pi * base_freq * t)
        
        # Modulation d'amplitude par la longueur des mots
        envelope = np.ones_like(t)
        words = text.split()
        for i, word in enumerate(words):
            start = i * duration / len(words)
            end = start + duration / len(words)
            mask = (t >= start) & (t < end)
            envelope[mask] = 0.5 + 0.5 * np.sin(np.pi * (t[mask] - start) / (duration / len(words)))
        
        audio = carrier * envelope * 0.3
        audio = np.clip(audio, -1, 1)
        
        audio_int16 = (audio * 32767).astype(np.int16)
        with wave.open(output_path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        
        return duration

    def _synth_piper_or_fallback(self, text, params, output_path):
        """Essaie Piper, puis fallback."""
        try:
            from speech_service import SpeechService
            svc = SpeechService()
            if svc.piper_available:
                svc.synthesize(text, output_path)
                return self._get_audio_duration(output_path)
        except:
            pass
        return self._synth_fallback(text, params, output_path)

    def _get_audio_duration(self, path: str) -> float:
        """Retourne la durée d'un fichier WAV en secondes."""
        try:
            with wave.open(path, 'r') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / rate
        except:
            return 1.0

    def list_voices(self) -> List[Dict]:
        """Liste les profils de voix disponibles."""
        return [{"id": k, **v} for k, v in VOICE_PROFILES.items()]

    def get_stats(self) -> Dict:
        return self.stats


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    hso = HarmonicSpeechOrchestrator(voice_profile="kemet_moderne")
    
    print("=" * 60)
    print("HARMONIC SPEECH ORCHESTRATOR — Test")
    print("=" * 60)
    
    tests = [
        "Bonjour, je suis KA Phone, ton assistant intelligent.",
        "La capitale du Sénégal est Dakar.",
        "Il était une fois, dans le royaume de Kemet, un pharaon qui aimait la sagesse.",
        "La dérivée de x puissance n est n fois x puissance n moins un.",
    ]
    
    for text in tests:
        result = hso.speak(text)
        print(f"\nTexte: '{text[:60]}...'")
        print(f"  Voix: {result['voice']}")
        print(f"  Prosodie: {result['prosody_template']}")
        print(f"  Audio: {result['audio_path']} ({result['duration_s']:.1f}s)")
    
    print(f"\nVoix disponibles: {len(hso.list_voices())}")
    print(f"Stats: {hso.get_stats()}")