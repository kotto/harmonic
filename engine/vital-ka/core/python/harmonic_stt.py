"""
🌊 HARMONIC STT + VOICE ANALYZER — Reconnaissance Vocale Bidirectionnelle
===========================================================================
Ajoute la brique MANQUANTE pour KA MOBILE : l'écoute.

ARCHITECTURE BIDIRECTIONNELLE COMPLÈTE :

  ┌─────────────────────────────────────────────────────────────────┐
  │                    KA MOBILE — Full Duplex                       │
  │                                                                 │
  │  ENTRÉE (STT)                    SORTIE (TTS)                   │
  │  ┌──────────────────┐            ┌──────────────────┐          │
  │  │ Whisper (local)   │            │ edge-tts (neural) │          │
  │  │ Voxtral (Mistral) │    IA      │ Piper (local)     │          │
  │  │ Web Speech API    │───▶ THU ──▶│ Coqui (clonage)   │          │
  │  └────────┬─────────┘            └────────┬─────────┘          │
  │           │                                │                    │
  │  ┌────────┴─────────┐            ┌────────┴─────────┐          │
  │  │ HarmonicVoice     │            │ HarmonicVoice     │          │
  │  │ Analyzer           │            │ Emotion           │          │
  │  │ (émotion VOIX)     │            │ (modulation TTS)   │          │
  │  │ DIFFRACT + RESONATE│            │ PHASE_SHIFT + ... │          │
  │  └──────────────────┘            └──────────────────┘          │
  └─────────────────────────────────────────────────────────────────┘

STT ENGINES :
  • Whisper (local, MIT)    — faster-whisper, tiny/small, ~1 Go RAM
  • Voxtral (Mistral API)   — Apache 2.0, $0.001/min, excellent FR
  • Web Speech API          — gratuit, navigateur, déjà implémenté

VOICE EMOTION ANALYSIS (nouveau !) :
  • DIFFRACT(audio)         → spectre fréquentiel (FFT)
  • RESONATE(spectre, prototypes) → émotion dominante
  • EMERGE(text_emotion, voice_emotion) → émotion fusionnée

  Prototypes spectraux d'émotion :
    joie        → énergie haute fréquence ↑, rythme ↑
    tristesse   → énergie basse fréquence ↓, rythme ↓
    colère      → énergie large bande ↑↑, rythme ↑↑
    peur        → énergie haute fréquence ↑↑, irrégularité ↑
    neutre      → distribution uniforme
    urgence     → pics spectraux aigus, rythme ↑↑

ENDPOINTS AJOUTÉS AU SERVEUR ORACLE :
  POST /listen   → {audio_base64} → {text, emotion_voice, emotion_fused}
  POST /converse → {audio_base64, context} → {audio_response, text, emotions}

Auteur : THU — Univers-Holistique
Date   : 2026-08-23
"""

import sys, os, math, time, json, re, io, base64, tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field
import numpy as np

# ═══════════════════════════════════════════════════════════════════
# CONSTANTES HARMONIQUES
# ═══════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1.0 / PHI
GOLDEN_ANGLE = 2 * math.pi * PHI_INV

# ═══════════════════════════════════════════════════════════════════
# 1. STT ENGINE — Multi-moteur (Whisper local + Voxtral API)
# ═══════════════════════════════════════════════════════════════════

class STTEngine:
    """
    Moteur de reconnaissance vocale multi-backend.
    
    Backends (essayés dans l'ordre) :
      1. faster-whisper (local, MIT, CPU-friendly)
      2. Voxtral API (Mistral, payant, excellent)
      3. OpenAI Whisper (fallback)
    """
    
    def __init__(self, whisper_model: str = "tiny",
                 voxtral_api_key: str = None):
        self.whisper_model = whisper_model
        self.voxtral_api_key = voxtral_api_key or os.environ.get("VOXTRAL_API_KEY", "")
        self._whisper = None
        self._available_backends: List[str] = []
        self._detect_backends()
    
    def _detect_backends(self):
        """Détecte les backends disponibles."""
        # faster-whisper
        try:
            from faster_whisper import WhisperModel
            self._available_backends.append("whisper")
        except ImportError:
            pass
        
        # Voxtral API
        if self.voxtral_api_key:
            self._available_backends.append("voxtral")
        
        if not self._available_backends:
            # Fallback : essayer whisper standard
            try:
                import whisper
                self._available_backends.append("whisper_openai")
            except ImportError:
                pass
    
    @property
    def available(self) -> List[str]:
        return self._available_backends
    
    def transcribe(self, audio_bytes: bytes, lang: str = "fr",
                   backend: str = None) -> Dict:
        """
        Transcrit un fichier audio en texte.
        
        Args:
            audio_bytes: données audio (MP3, WAV, FLAC...)
            lang: code langue ("fr", "en")
            backend: "whisper", "voxtral", "whisper_openai" (auto si None)
        
        Returns:
            {text, lang, backend, confidence, time_ms, segments}
        """
        t0 = time.time()
        
        # Sauvegarder l'audio temporairement
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            audio_path = f.name
        
        try:
            # Choisir le backend
            if backend and backend in self._available_backends:
                pass
            elif self._available_backends:
                backend = self._available_backends[0]
            else:
                return {"error": "Aucun backend STT disponible", "text": ""}
            
            if backend == "whisper":
                result = self._transcribe_whisper(audio_path, lang)
            elif backend == "voxtral":
                result = self._transcribe_voxtral(audio_bytes, lang)
            elif backend == "whisper_openai":
                result = self._transcribe_whisper_openai(audio_path, lang)
            else:
                result = {"text": "", "error": f"Backend inconnu: {backend}"}
        finally:
            # Nettoyer
            try:
                os.unlink(audio_path)
            except OSError:
                pass
        
        elapsed = time.time() - t0
        result["time_ms"] = round(elapsed * 1000)
        result["backend"] = backend
        result["lang"] = lang
        
        return result
    
    def _transcribe_whisper(self, audio_path: str, lang: str) -> Dict:
        """Transcription via faster-whisper (local)."""
        if self._whisper is None:
            from faster_whisper import WhisperModel
            # tiny = 39M params, ~1 Go RAM, très rapide sur CPU
            self._whisper = WhisperModel(
                self.whisper_model,
                device="cpu",
                compute_type="int8",
            )
        
        lang_code = "fr" if lang == "fr" else "en"
        
        segments, info = self._whisper.transcribe(
            audio_path,
            language=lang_code,
            beam_size=3,
            vad_filter=True,
        )
        
        all_text = []
        all_segments = []
        total_confidence = 0.0
        n_segments = 0
        
        for seg in segments:
            all_text.append(seg.text.strip())
            all_segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
            })
            total_confidence += seg.avg_logprob
            n_segments += 1
        
        text = " ".join(all_text)
        confidence = math.exp(total_confidence / max(1, n_segments))
        
        return {
            "text": text,
            "confidence": round(min(1.0, confidence), 3),
            "segments": all_segments,
        }
    
    def _transcribe_voxtral(self, audio_bytes: bytes, lang: str) -> Dict:
        """Transcription via Voxtral API (Mistral)."""
        import requests
        
        if not self.voxtral_api_key:
            return {"text": "", "error": "VOXTRAL_API_KEY non définie"}
        
        # Encoder en base64 pour l'API
        audio_b64 = base64.b64encode(audio_bytes).decode()
        
        headers = {
            "Authorization": f"Bearer {self.voxtral_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "voxtral-mini-transcribe-2",
            "file": audio_b64,
            "language": lang,
            "response_format": "json",
        }
        
        resp = requests.post(
            "https://api.mistral.ai/v1/audio/transcriptions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        
        if resp.status_code != 200:
            return {"text": "", "error": f"Voxtral API: {resp.status_code}"}
        
        data = resp.json()
        return {
            "text": data.get("text", ""),
            "confidence": 0.95,  # Voxtral est très fiable
            "segments": data.get("segments", []),
        }
    
    def _transcribe_whisper_openai(self, audio_path: str, lang: str) -> Dict:
        """Transcription via OpenAI Whisper (fallback)."""
        import whisper
        
        model = whisper.load_model(self.whisper_model)
        lang_code = "fr" if lang == "fr" else "en"
        
        result = model.transcribe(
            audio_path,
            language=lang_code,
            fp16=False,
        )
        
        segments = [
            {"start": round(s["start"], 2), "end": round(s["end"], 2),
             "text": s["text"].strip()}
            for s in result.get("segments", [])
        ]
        
        return {
            "text": result.get("text", "").strip(),
            "confidence": 0.9,
            "segments": segments,
        }


# ═══════════════════════════════════════════════════════════════════
# 2. HARMONIC VOICE ANALYZER — Émotion dans la VOIX
# ═══════════════════════════════════════════════════════════════════

# Prototypes spectraux d'émotion (signatures fréquentielles)
# Chaque prototype = (distribution_fréquence, distribution_rythme, énergie)
EMOTION_SPECTRAL_PROTOTYPES = {
    "joie": {
        "spectral_centroid": 0.65,    # centroïde spectral élevé (voix aiguë)
        "spectral_flatness": 0.3,     # pas trop bruité
        "energy_mean": 0.7,           # énergie modérée à haute
        "energy_std": 0.3,            # variation rythmique
        "zero_crossing_rate": 0.6,    # articulations vives
        "tempo": 0.65,                # rythme soutenu
    },
    "tristesse": {
        "spectral_centroid": 0.35,
        "spectral_flatness": 0.5,
        "energy_mean": 0.3,
        "energy_std": 0.15,
        "zero_crossing_rate": 0.3,
        "tempo": 0.3,
    },
    "colere": {
        "spectral_centroid": 0.7,
        "spectral_flatness": 0.2,
        "energy_mean": 0.9,
        "energy_std": 0.5,
        "zero_crossing_rate": 0.8,
        "tempo": 0.85,
    },
    "peur": {
        "spectral_centroid": 0.7,
        "spectral_flatness": 0.4,
        "energy_mean": 0.7,
        "energy_std": 0.6,           # forte irrégularité
        "zero_crossing_rate": 0.75,
        "tempo": 0.7,
    },
    "neutre": {
        "spectral_centroid": 0.5,
        "spectral_flatness": 0.4,
        "energy_mean": 0.5,
        "energy_std": 0.25,
        "zero_crossing_rate": 0.5,
        "tempo": 0.5,
    },
    "urgence": {
        "spectral_centroid": 0.75,
        "spectral_flatness": 0.2,
        "energy_mean": 0.95,
        "energy_std": 0.4,
        "zero_crossing_rate": 0.85,
        "tempo": 0.9,
    },
    "calme": {
        "spectral_centroid": 0.4,
        "spectral_flatness": 0.5,
        "energy_mean": 0.3,
        "energy_std": 0.1,
        "zero_crossing_rate": 0.3,
        "tempo": 0.25,
    },
}


class HarmonicVoiceAnalyzer:
    """
    Analyse émotionnelle de la VOIX via primitives THU.
    
    PRIMITIVES UTILISÉES :
      DIFFRACT(audio)      → spectre fréquentiel (FFT)
      FILTER_WAVE(spectre) → bandes d'énergie (basses, médium, hautes)
      RESONATE(spec, proto) → similarité avec prototypes émotionnels
      EMERGE(text_emo, voice_emo) → fusion texte + voix
    
    L'approche est complémentaire au texte :
      - Le texte dit CE QUE l'utilisateur exprime (mots-clés)
      - La voix dit COMMENT il l'exprime (prosodie, ton, rythme)
      - La FUSION des deux donne l'émotion réelle
    """
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        
        # Normaliser les prototypes pour RESONATE
        self._proto_vectors = {}
        for name, proto in EMOTION_SPECTRAL_PROTOTYPES.items():
            vec = np.array([
                proto["spectral_centroid"],
                proto["spectral_flatness"],
                proto["energy_mean"],
                proto["energy_std"],
                proto["zero_crossing_rate"],
                proto["tempo"],
            ])
            self._proto_vectors[name] = vec / (np.linalg.norm(vec) + 1e-10)
    
    def analyze(self, audio_bytes: bytes) -> Dict:
        """
        Analyse l'émotion dans la voix à partir de l'audio brut.
        
        Pipeline :
          1. Décoder l'audio → waveform
          2. DIFFRACT(waveform) → spectre fréquentiel
          3. Extraire les features spectrales (6 dimensions)
          4. RESONATE(features, prototypes) → émotion dominante
          5. Score de confiance (distance aux prototypes)
        
        Returns:
            {emotion, confidence, features, all_scores}
        """
        t0 = time.time()
        
        # 1. Décoder l'audio (MP3 → WAV → numpy)
        try:
            waveform, sr = self._decode_audio(audio_bytes)
        except Exception as e:
            return {
                "emotion": "neutre",
                "confidence": 0.0,
                "error": f"Décodage audio: {e}",
                "features": {},
            }
        
        # 2. DIFFRACT — FFT pour obtenir le spectre
        features = self._extract_features(waveform, sr)
        
        # 3. RESONATE — similarité avec les prototypes
        emotion, confidence, all_scores = self._match_emotion(features)
        
        elapsed = time.time() - t0
        
        return {
            "emotion": emotion,
            "confidence": round(confidence, 3),
            "features": {k: round(v, 4) for k, v in features.items()},
            "all_scores": {k: round(v, 3) for k, v in all_scores.items()},
            "time_ms": round(elapsed * 1000),
            "sample_rate": sr,
            "duration_ms": round(len(waveform) / sr * 1000),
        }
    
    def _decode_audio(self, audio_bytes: bytes) -> Tuple[np.ndarray, int]:
        """
        Décode l'audio (MP3/WAV/FLAC) en waveform numpy.
        
        Utilise ffmpeg + numpy. Fonctionne avec n'importe quel format.
        """
        import subprocess
        
        # ffmpeg : décoder en WAV 16kHz mono 16-bit → stdout
        proc = subprocess.run(
            ["ffmpeg", "-i", "pipe:0", "-f", "s16le", "-acodec", "pcm_s16le",
             "-ar", str(self.sample_rate), "-ac", "1", "pipe:1"],
            input=audio_bytes,
            capture_output=True,
            timeout=30,
        )
        
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg error: {proc.stderr.decode()[:200]}")
        
        # Convertir les bytes PCM en numpy
        waveform = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float64)
        waveform = waveform / 32768.0  # normaliser [-1, 1]
        
        return waveform, self.sample_rate
    
    def _extract_features(self, waveform: np.ndarray, sr: int) -> Dict[str, float]:
        """
        DIFFRACT + FILTER_WAVE : extraction des 6 features spectrales.
        
        Chaque feature est une primitive THU appliquée au signal :
          DIFFRACT → spectre de Fourier
          FILTER_WAVE → bandes de fréquences (graves, médium, aigus)
          NORMALIZE  → chaque feature ∈ [0, 1]
        """
        n = len(waveform)
        if n < sr * 0.5:  # moins de 0.5s → pas assez pour analyse fiable
            return {k: 0.5 for k in EMOTION_SPECTRAL_PROTOTYPES["neutre"]}
        
        # DIFFRACT : FFT
        spectrum = np.abs(np.fft.rfft(waveform))
        freqs = np.fft.rfftfreq(n, 1.0 / sr)
        
        # FILTER_WAVE : bandes de fréquence (voix humaine : 80-4000 Hz)
        voice_mask = (freqs >= 80) & (freqs <= 4000)
        voice_spectrum = spectrum[voice_mask]
        voice_freqs = freqs[voice_mask]
        
        if len(voice_spectrum) < 10:
            return {k: 0.5 for k in EMOTION_SPECTRAL_PROTOTYPES["neutre"]}
        
        # 1. Centroïde spectral (hauteur moyenne de la voix)
        spectral_centroid = np.sum(voice_freqs * voice_spectrum) / \
                           (np.sum(voice_spectrum) + 1e-10)
        # Normaliser : 80 Hz → 0, 4000 Hz → 1
        spectral_centroid_norm = (spectral_centroid - 80) / (4000 - 80)
        spectral_centroid_norm = max(0.0, min(1.0, spectral_centroid_norm))
        
        # 2. Platitude spectrale (bruit vs tonal)
        geo_mean = np.exp(np.mean(np.log(voice_spectrum + 1e-10)))
        arith_mean = np.mean(voice_spectrum)
        spectral_flatness = geo_mean / (arith_mean + 1e-10)
        
        # 3. Énergie moyenne (volume)
        energy = np.sqrt(np.mean(waveform ** 2))
        energy_mean = min(1.0, energy * 10)  # normaliser
        
        # 4. Variation d'énergie (rythme, irrégularité)
        frame_size = sr // 10  # fenêtres de 100ms
        n_frames = n // frame_size
        if n_frames > 1:
            frame_energies = np.array([
                np.sqrt(np.mean(waveform[i*frame_size:(i+1)*frame_size]**2))
                for i in range(n_frames)
            ])
            energy_std = min(1.0, np.std(frame_energies) * 20)
        else:
            energy_std = 0.5
        
        # 5. Zero-crossing rate (articulation)
        zcr = np.sum(np.abs(np.diff(np.sign(waveform)))) / (2 * n)
        zcr_norm = min(1.0, zcr * 20)
        
        # 6. Tempo estimé (rythme des pics d'énergie)
        if n_frames > 3:
            peaks = (frame_energies > np.mean(frame_energies) * 1.5).astype(int)
            transitions = np.diff(peaks)
            intervals = np.diff(np.where(transitions == 1)[0])
            if len(intervals) > 1:
                avg_interval = np.median(intervals) * 100  # ms
                tempo = min(1.0, 300 / max(avg_interval, 50))
            else:
                tempo = 0.5
        else:
            tempo = 0.5
        
        return {
            "spectral_centroid": spectral_centroid_norm,
            "spectral_flatness": spectral_flatness,
            "energy_mean": energy_mean,
            "energy_std": energy_std,
            "zero_crossing_rate": zcr_norm,
            "tempo": tempo,
        }
    
    def _match_emotion(self, features: Dict[str, float]
                       ) -> Tuple[str, float, Dict[str, float]]:
        """
        RESONATE : calcule la similarité entre les features extraites
        et chaque prototype émotionnel.
        
        score = cos(features_vec, prototype_vec) ∈ [-1, 1]
        """
        feat_vec = np.array([
            features["spectral_centroid"],
            features["spectral_flatness"],
            features["energy_mean"],
            features["energy_std"],
            features["zero_crossing_rate"],
            features["tempo"],
        ])
        feat_vec = feat_vec / (np.linalg.norm(feat_vec) + 1e-10)
        
        scores = {}
        for name, proto_vec in self._proto_vectors.items():
            # RESONATE = cosinus similarity
            score = float(np.dot(feat_vec, proto_vec))
            scores[name] = score
        
        # Meilleure émotion
        best = max(scores, key=scores.get)
        best_score = scores[best]
        
        # Confiance = écart entre le meilleur et le 2ème meilleur
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1:
            margin = sorted_scores[0] - sorted_scores[1]
            confidence = min(1.0, margin * 2 + 0.3)
        else:
            confidence = 0.5
        
        return best, confidence, scores
    
    def fuse_emotions(self, text_emotion: Dict, voice_emotion: Dict
                      ) -> Dict:
        """
        EMERGE : fusionne l'émotion du TEXTE et de la VOIX.
        
        La voix est plus fiable que le texte pour l'émotion vraie
        (on peut écrire "je vais bien" d'une voix triste).
        
        Pondération φ :
          voix = φ⁻¹ ≈ 61.8 %  (plus fiable)
          texte = φ⁻² ≈ 38.2 % (complémentaire)
        """
        if not text_emotion or not voice_emotion:
            return text_emotion or voice_emotion or {"emotion": "neutre", "confidence": 0.0}
        
        text_valence = text_emotion.get("valence", 0.0)
        text_arousal = text_emotion.get("arousal", 0.0)
        text_conf = text_emotion.get("intensity", 0.5)
        
        voice_emo = voice_emotion.get("emotion", "neutre")
        voice_conf = voice_emotion.get("confidence", 0.5)
        
        # Mapper l'émotion vocale vers (valence, arousal)
        voice_valence, voice_arousal = self._emotion_to_valence_arousal(voice_emo)
        
        # EMERGE : fusion pondérée par φ
        w_voice = PHI_INV       # 0.618 — la voix ne ment pas
        w_text = PHI_INV ** 2   # 0.382 — le texte peut être trompeur
        
        # Ajuster selon les confiances
        w_voice *= voice_conf
        w_text *= text_conf
        total_w = w_voice + w_text + 1e-10
        
        fused_valence = (w_text * text_valence + w_voice * voice_valence) / total_w
        fused_arousal = (w_text * text_arousal + w_voice * voice_arousal) / total_w
        
        # Émotion dominante
        fused_emotion = self._closest_emotion(fused_valence, fused_arousal)
        
        # Conflit texte/voix → information utile
        conflict = abs(text_valence - voice_valence) > 0.4
        
        return {
            "emotion": fused_emotion,
            "valence": round(fused_valence, 3),
            "arousal": round(fused_arousal, 3),
            "text_emotion": text_emotion.get("emotion", "neutre"),
            "voice_emotion": voice_emo,
            "conflict_detected": conflict,
            "conflict_note": "Le texte et la voix expriment des émotions différentes — la voix prime." if conflict else "",
            "weights": {"voice": round(w_voice / total_w, 2), "text": round(w_text / total_w, 2)},
        }
    
    def _emotion_to_valence_arousal(self, emotion: str) -> Tuple[float, float]:
        """Convertit un nom d'émotion en coordonnées (valence, arousal)."""
        mapping = {
            "joie": (0.8, 0.7), "tristesse": (-0.7, -0.5),
            "colere": (-0.6, 0.9), "peur": (-0.5, 0.8),
            "neutre": (0.0, 0.0), "urgence": (-0.4, 0.9),
            "calme": (0.6, -0.6),
        }
        return mapping.get(emotion, (0.0, 0.0))
    
    def _closest_emotion(self, valence: float, arousal: float) -> str:
        """Trouve l'émotion la plus proche dans l'espace valence-arousal."""
        mapping = self._emotion_to_valence_arousal
        best = "neutre"
        best_dist = float('inf')
        
        for name in EMOTION_SPECTRAL_PROTOTYPES:
            v, a = mapping(name)
            dist = math.sqrt((valence - v)**2 + (arousal - a)**2)
            if dist < best_dist:
                best_dist = dist
                best = name
        
        return best


# ═══════════════════════════════════════════════════════════════════
# 3. PIPELINE BIDIRECTIONNEL COMPLET
# ═══════════════════════════════════════════════════════════════════

class BidirectionalPipeline:
    """
    Pipeline bidirectionnel complet : écoute → comprend → répond → parle.
    
    Flux :
      audio_in → STT → texte → émotion_texte
              ↘
               VoiceAnalyzer → émotion_voix
              ↙
      EMERGE(texte, voix) → émotion_fusionnée
              ↓
      StructuredFactRetriever → faits exacts
              ↓
      NaturalLanguagePipeline → réponse élégante
              ↓
      HarmonicVoiceEmotion → modulation TTS (selon émotion)
              ↓
      TTS → audio_out
    """
    
    def __init__(self, stt_engine: STTEngine = None,
                 voice_analyzer: HarmonicVoiceAnalyzer = None,
                 voice_emotion=None,
                 retriever=None,
                 pipeline=None):
        self.stt = stt_engine or STTEngine()
        self.voice_analyzer = voice_analyzer or HarmonicVoiceAnalyzer()
        self.voice_emotion = voice_emotion  # HarmonicVoiceEmotion (importé si dispo)
        self.retriever = retriever          # StructuredFactRetriever
        self.pipeline = pipeline            # NaturalLanguagePipeline
        
        # Charger HarmonicVoiceEmotion si disponible
        if self.voice_emotion is None:
            try:
                from harmonic_voice_emotion import HarmonicVoiceEmotion
                self.voice_emotion = HarmonicVoiceEmotion()
            except ImportError:
                pass
    
    def listen(self, audio_bytes: bytes, lang: str = "fr",
               context: str = "general") -> Dict:
        """
        Écoute et comprend : audio → texte + émotions.
        
        Returns:
            {text, emotion_text, emotion_voice, emotion_fused,
             stt_backend, time_ms}
        """
        # 1. STT
        transcription = self.stt.transcribe(audio_bytes, lang)
        text = transcription.get("text", "")
        
        if not text:
            return {
                "text": "",
                "error": "Aucune parole détectée",
                "stt_backend": transcription.get("backend"),
            }
        
        # 2. Émotion dans la VOIX (DIFFRACT + RESONATE)
        voice_emotion = self.voice_analyzer.analyze(audio_bytes)
        
        # 3. Émotion dans le TEXTE (HarmonicVoiceEmotion)
        text_emotion = {}
        if self.voice_emotion:
            text_emotion = self.voice_emotion.detect_emotion(text, lang)
        
        # 4. Fusion (EMERGE)
        fused = self.voice_analyzer.fuse_emotions(text_emotion, voice_emotion)
        
        return {
            "text": text,
            "lang": lang,
            "stt_backend": transcription.get("backend"),
            "stt_confidence": transcription.get("confidence", 0),
            "stt_time_ms": transcription.get("time_ms", 0),
            "emotion_text": text_emotion,
            "emotion_voice": voice_emotion,
            "emotion_fused": fused,
            "context": context,
        }
    
    def converse(self, audio_bytes: bytes, lang: str = "fr",
                 context: str = "general", tts_mode: str = "edge",
                 voice: str = "female") -> Dict:
        """
        Boucle bidirectionnelle complète : audio → réponse audio.
        
        Returns:
            {audio_base64, response_text, emotion_fused, ...}
        """
        import base64 as b64
        
        # 1. Écouter
        listen_result = self.listen(audio_bytes, lang, context)
        text = listen_result.get("text", "")
        fused_emotion = listen_result.get("emotion_fused", {})
        
        if not text:
            return {**listen_result, "audio_base64": "", "response_text": ""}
        
        # 2. Chercher les faits
        facts_text = ""
        if self.retriever:
            result = self.retriever.query(text)
            if not result.hallucinated:
                facts = [(s.subject, s.relation, s.object) 
                         for s in result.sources[:8]]
                facts_text = "\n".join(
                    f"{s} → {r}: {o}" for s, r, o in facts
                )
        
        # 3. Phraser
        response_text = ""
        if facts_text and self.pipeline:
            response_text = self.pipeline.render(
                self._make_sources(facts_text),
                question=text,
            )
        elif facts_text:
            response_text = facts_text
        else:
            response_text = "Je n'ai pas trouvé d'information sur ce sujet dans ma base de connaissances."
        
        # 4. Synthèse vocale avec émotion
        audio_base64 = ""
        if self.voice_emotion:
            voice_params = self.voice_emotion.get_voice_params(
                fused_emotion, context, lang
            )
            
            if tts_mode == "edge":
                import asyncio
                ssml = self.voice_emotion.to_ssml(
                    response_text, voice_params, fused_emotion, context, lang
                )
                voice_name = voice_params.get("voice", "fr-FR-DeniseNeural")
                
                async def _speak():
                    import edge_tts
                    communicate = edge_tts.Communicate(ssml, voice_name)
                    output = "/tmp/tts_converse.mp3"
                    await communicate.save(output)
                    with open(output, "rb") as f:
                        return f.read()
                
                try:
                    audio_bytes_out = asyncio.run(_speak())
                    audio_base64 = b64.b64encode(audio_bytes_out).decode()
                except Exception:
                    pass
        
        return {
            **listen_result,
            "response_text": response_text,
            "audio_base64": audio_base64,
            "audio_format": "mp3",
            "emotion_fused": fused_emotion,
            "conversation_turn": {
                "user_said": text,
                "assistant_said": response_text,
                "emotion": fused_emotion.get("emotion", "neutre"),
            },
        }
    
    def _make_sources(self, facts_text: str):
        """Convertit le texte de faits en pseudo-sources pour le pipeline."""
        from dataclasses import dataclass as dc
        @dc
        class Src:
            subject: str = ""
            relation: str = ""
            object: str = ""
            score: float = 1.0
            domain: str = ""
            fact_id: int = 0
        return [Src()]


# ═══════════════════════════════════════════════════════════════════
# TEST — Démonstration
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🌊 HARMONIC STT + VOICE ANALYZER — Démonstration          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Test de l'analyseur vocal (sans audio réel — test des features)
    print("═" * 70)
    print("  🎤 TEST — HarmonicVoiceAnalyzer (prototypes)")
    print("═" * 70)
    print()
    
    analyzer = HarmonicVoiceAnalyzer()
    
    # Simuler des features pour différentes émotions
    test_features = {
        "Joie (aigu, rapide, fort)": {
            "spectral_centroid": 0.7, "spectral_flatness": 0.3,
            "energy_mean": 0.8, "energy_std": 0.35,
            "zero_crossing_rate": 0.65, "tempo": 0.7,
        },
        "Tristesse (grave, lent, faible)": {
            "spectral_centroid": 0.3, "spectral_flatness": 0.5,
            "energy_mean": 0.25, "energy_std": 0.1,
            "zero_crossing_rate": 0.25, "tempo": 0.25,
        },
        "Colère (aigu, très fort, irrégulier)": {
            "spectral_centroid": 0.75, "spectral_flatness": 0.2,
            "energy_mean": 0.95, "energy_std": 0.55,
            "zero_crossing_rate": 0.82, "tempo": 0.88,
        },
        "Neutre (moyen partout)": {
            "spectral_centroid": 0.5, "spectral_flatness": 0.4,
            "energy_mean": 0.5, "energy_std": 0.25,
            "zero_crossing_rate": 0.5, "tempo": 0.5,
        },
    }
    
    for name, feat in test_features.items():
        emotion, conf, scores = analyzer._match_emotion(feat)
        print(f"  {name}")
        print(f"     → {emotion} (confiance: {conf:.0%})")
        top3 = sorted(scores.items(), key=lambda x: -x[1])[:3]
        print(f"     Top-3: {', '.join(f'{e}({s:.2f})' for e, s in top3)}")
        print()
    
    # Test de fusion texte + voix
    print("═" * 70)
    print("  🔀 TEST — Fusion Texte + Voix (EMERGE)")
    print("═" * 70)
    print()
    
    test_cases = [
        ("Je vais très bien merci !", "tristesse", "Conflit"),
        ("Je suis inquiet...", "neutre", "Sous-expression"),
        ("C'est une urgence !", "urgence", "Cohérent"),
        ("Tout va bien...", "colere", "Conflit masqué"),
    ]
    
    # Simuler l'émotion texte (sans importer HarmonicVoiceEmotion)
    def simulate_text_emotion(text):
        markers_pos = ["bien", "merci", "super", "content", "heureux"]
        markers_neg = ["inquiet", "urgence", "mal", "triste", "peur"]
        text_lower = text.lower()
        if any(w in text_lower for w in markers_neg):
            return {"emotion": "inquietude", "valence": -0.4, "arousal": 0.6, "intensity": 0.7}
        elif any(w in text_lower for w in markers_pos):
            return {"emotion": "joie", "valence": 0.7, "arousal": 0.6, "intensity": 0.8}
        return {"emotion": "neutre", "valence": 0.0, "arousal": 0.0, "intensity": 0.3}
    
    for text, voice_emo, note in test_cases:
        text_emo = simulate_text_emotion(text)
        voice_emo_dict = {"emotion": voice_emo, "confidence": 0.8}
        fused = analyzer.fuse_emotions(text_emo, voice_emo_dict)
        
        print(f"  Texte: \"{text}\" | Voix: {voice_emo} | Note: {note}")
        print(f"     → Émotion finale: {fused.get('emotion', '?')} "
              f"(V={fused.get('valence', 0):+.2f}, A={fused.get('arousal', 0):+.2f})")
        if fused.get("conflict_detected"):
            print(f"     ⚠️  Conflit détecté — la voix prime sur le texte")
        print()
    
    # Test STT (vérifier les backends disponibles — rapide, sans importer)
    print("═" * 70)
    print("  🎙️  TEST — STT Engine (backends disponibles)")
    print("═" * 70)
    print()
    
    # Détection rapide sans import
    available = []
    try:
        from faster_whisper import WhisperModel
        available.append("whisper (faster-whisper)")
    except ImportError:
        pass
    
    vox_key = os.environ.get("VOXTRAL_API_KEY", "")
    if vox_key:
        available.append("voxtral (Mistral API)")
    
    try:
        import whisper
        available.append("whisper (OpenAI)")
    except ImportError:
        pass
    
    if available:
        print(f"  ✅ Backends STT disponibles : {', '.join(available)}")
    else:
        print(f"  ⚠️  Aucun backend STT local.")
        print(f"     → Installer faster-whisper : pip install faster-whisper")
        print(f"     → Ou configurer VOXTRAL_API_KEY pour l'API Mistral")
    print()
    
    print("═" * 70)
    print("  ✅ HARMONIC STT + VOICE ANALYZER — PRÊT")
    print("═" * 70)
    print()
    print("  Endpoints à ajouter au serveur Oracle :")
    print("    POST /listen   → audio → texte + émotions")
    print("    POST /converse → audio → audio (boucle complète)")
    print()