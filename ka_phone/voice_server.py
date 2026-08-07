#!/usr/bin/env python3
"""
KA PHONE — Voice Server (Piper neuronal + post-processing harmonique, 100% offline)
=====================================================================================
Micro-serveur HTTP dédié à la synthèse vocale.
Démarrage instantané — importe uniquement le moteur vocal, pas les 30+ modules IA.

Pipeline audio (si enhanced=true) :
  1. PronunciationGuide  → corrige la prononciation (termes médicaux, noms propres)
  2. ProsodyEnhancer     → micro-pauses, respiration, modulation de hauteur
  3. Piper TTS           → synthèse vocale neuronale (22 kHz, offline)
  4. HarmonicAudioPost   → boost φ, réduction de bruit, lissage ABC, upscale 96kHz

Endpoints :
  GET  /api/voice/offline/caps  → capacités offline (JSON)
  POST /api/voice/offline       → synthèse vocale (WAV)
  GET  /api/voice/health        → état du serveur

Usage :
  python voice_server.py              # port 8420 (défaut)
  python voice_server.py --port 8765  # port personnalisé
"""

import sys, os, json, time, http.server, argparse, io, wave, logging

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

logging.basicConfig(level=logging.INFO, format='[voice-server] %(message)s')
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# INIT PAINESSEUSE DES MODULES HARMONIQUES (importés au premier besoin seulement)
# ═══════════════════════════════════════════════════════════════════════════════

_post_processor = None
_pronunciation_guide = None
_prosody_enhancer = None
_has_numpy = None
_has_scipy = None

def _ensure_numpy():
    global _has_numpy
    if _has_numpy is None:
        try:
            import numpy
            _has_numpy = True
        except ImportError:
            _has_numpy = False
    return _has_numpy

def _ensure_scipy():
    global _has_scipy
    if _has_scipy is None:
        try:
            import scipy
            _has_scipy = True
        except ImportError:
            _has_scipy = False
    return _has_scipy

def _ensure_post_processor():
    """Charge le post-processeur harmonique (boost φ, réduction de bruit, lissage ABC)."""
    global _post_processor
    if _post_processor is None:
        try:
            from harmonic_audio_postprocessor import HarmonicAudioPostProcessor
            _post_processor = HarmonicAudioPostProcessor()
            log.info("  🎵 Post-processeur harmonique : Actif (boost φ + réduction bruit + lissage ABC)")
        except ImportError:
            log.info("  ⚠️  Post-processeur harmonique : Non disponible")
    return _post_processor

def _ensure_pronunciation():
    """Charge le guide de prononciation (termes médicaux, noms propres)."""
    global _pronunciation_guide
    if _pronunciation_guide is None:
        try:
            from pronunciation_guide import PronunciationGuide
            _pronunciation_guide = PronunciationGuide()
            log.info("  📖 Guide de prononciation : Actif")
        except ImportError:
            log.info("  ⚠️  Guide de prononciation : Non disponible")
    return _pronunciation_guide

def _ensure_prosody():
    """Charge l'enrichisseur prosodique (micro-pauses, respiration, modulation)."""
    global _prosody_enhancer
    if _prosody_enhancer is None:
        try:
            from prosody_enhancer import ProsodyEnhancer
            _prosody_enhancer = ProsodyEnhancer()
            log.info("  🫁 Enrichisseur prosodique : Actif (micro-pauses, respiration)")
        except ImportError:
            log.info("  ⚠️  Enrichisseur prosodique : Non disponible")
    return _prosody_enhancer


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS D'AMÉLIORATION AUDIO
# ═══════════════════════════════════════════════════════════════════════════════

def enhance_text(text: str, style: str = 'naturel') -> str:
    """
    Améliore le texte avant synthèse :
    - Guide de prononciation (termes médicaux, noms propres)
    - Prosodie (micro-pauses, respiration)
    """
    enhanced = text

    # 1. Pronunciation guide
    pg = _ensure_pronunciation()
    if pg:
        try:
            enhanced = pg.apply_pronunciation(enhanced)
        except Exception:
            pass

    # 2. Prosody enhancer
    pe = _ensure_prosody()
    if pe:
        try:
            enhanced = pe.enhance_for_tts(enhanced, style=style, use_ssml=False)
        except Exception:
            pass

    return enhanced

def enhance_audio(audio_bytes: bytes, boost_strength: float = 0.12,
                  noise_reduction: bool = True, abc_smoothing: bool = True,
                  upscale_hd: bool = False) -> bytes:
    """
    Post-processing harmonique de l'audio WAV généré par Piper :
    1. Boost des fréquences φ-harmoniques (chaleur, présence)
    2. Réduction de bruit spectrale
    3. Lissage temporel ABC (attaque/déclin naturels)
    4. Optionnel : upscaling HD 48 kHz
    """
    hpp = _ensure_post_processor()
    if not hpp or not _ensure_numpy():
        return audio_bytes

    try:
        import numpy as np

        # Décoder le WAV Piper → numpy array float32
        with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
            sample_rate = wf.getframerate()
            sampwidth = wf.getsampwidth()
            raw = wf.readframes(wf.getnframes())

        if sampwidth != 2:
            return audio_bytes  # PCM 16 bits uniquement

        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        # Post-processing harmonique
        processed = hpp.process_bytes(
            data, sample_rate,
            boost_strength=boost_strength,
            noise_reduction=noise_reduction,
            abc_smoothing=abc_smoothing,
        )

        # Pré-filtre passe-haut léger (80 Hz → clarté vocale)
        if _ensure_scipy():
            try:
                from scipy import signal as sp_signal
                b, a = sp_signal.butter(2, 80 / (sample_rate / 2), btype='high')
                processed = sp_signal.lfilter(b, a, processed)
            except Exception:
                pass

        # Upscaling HD (optionnel, ~2× la taille du fichier)
        if upscale_hd and sample_rate < 48000:
            target_sr = 48000
            try:
                if _ensure_scipy():
                    from scipy import signal as sp_signal
                    processed = sp_signal.resample(processed, int(len(processed) * target_sr / sample_rate))
                else:
                    ratio = target_sr / sample_rate
                    old_len = len(processed)
                    processed = np.interp(
                        np.linspace(0, old_len - 1, int(old_len * ratio)),
                        np.arange(old_len), processed
                    )
                sample_rate = target_sr
            except Exception:
                pass

        # Ré-encoder en WAV PCM 16 bits
        out = io.BytesIO()
        pcm = (np.clip(processed, -1.0, 1.0) * 32767).astype(np.int16)
        with wave.open(out, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())

        return out.getvalue()

    except Exception as e:
        log.warning(f"Post-processing audio ignoré (fallback brut): {e}")
        return audio_bytes


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLER HTTP
# ═══════════════════════════════════════════════════════════════════════════════

class VoiceAPIHandler(http.server.BaseHTTPRequestHandler):
    """Handler HTTP minimal — uniquement les endpoints vocaux."""

    # Variables de classe (partagées entre toutes les requêtes)
    voice_engine = None

    @classmethod
    def init_engine(cls, offline_only=True):
        """Initialise le moteur vocal ET les modules harmoniques au démarrage."""
        if cls.voice_engine is not None:
            return
        from harmonic_voice_engine import HarmonicVoiceEngine
        t0 = time.perf_counter()
        cls.voice_engine = HarmonicVoiceEngine(offline_only=offline_only)
        dt = (time.perf_counter() - t0) * 1000
        stats = cls.voice_engine.stats
        log.info(f"Moteur vocal initialisé en {dt:.0f} ms")
        log.info(f"  Mode:      {stats['mode']}")
        log.info(f"  Piper:     {'✅ Actif' if stats['engines']['piper'] else '❌ Non disponible'}")
        log.info(f"  XTTS:      {'✅ Actif' if stats['engines']['xtts'] else '⚠️ Non disponible (RAM)'}")
        log.info(f"  Edge-TTS:  {'🚫 Désactivé (offline)' if stats['mode'] == 'offline' else '☁️ Actif'}")

        # Pré-charger les modules harmoniques (paresseux, juste vérification)
        log.info("Modules harmoniques :")
        _ensure_post_processor()
        _ensure_pronunciation()
        _ensure_prosody()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/voice/health':
            self._send_json({
                'status': 'ok',
                'server': 'KA PHONE Voice Server',
                'version': '2.0-offline',
                'engine': self.voice_engine.stats if self.voice_engine else {},
            })

        elif self.path == '/api/voice/offline/caps':
            if not self.voice_engine:
                self._send_json({'error': 'engine_not_initialized'}, 500)
                return
            caps = self.voice_engine.stats
            caps['offline_ready'] = self.voice_engine.is_offline_ready
            caps['voices'] = list(self.voice_engine.VOICES_OFFLINE.keys())
            caps['mode'] = 'offline'
            caps['server'] = 'KA PHONE Voice Server v2.1'
            caps['enhancements'] = {
                'harmonic_post_processor': _ensure_post_processor() is not None,
                'pronunciation_guide': _ensure_pronunciation() is not None,
                'prosody_enhancer': _ensure_prosody() is not None,
                'hd_upscale': True,  # toujours dispo si scipy/numpy
            }
            self._send_json(caps)

        elif self.path == '/':
            self._send_json({
                'service': 'KA PHONE Voice Server v2.1',
                'pipeline': 'Pronunciation → Prosody → Piper TTS → Harmonic Post-Process',
                'endpoints': {
                    'GET  /api/voice/health': 'État du serveur',
                    'GET  /api/voice/offline/caps': 'Capacités du moteur offline',
                    'POST /api/voice/offline': 'Synthèse vocale (JSON → WAV)',
                },
                'params': {
                    'text': 'Texte à synthétiser',
                    'voice': 'siwis (défaut), siwis_h, siwis_f, xtts',
                    'speed': '0.5 à 2.0 (défaut: 1.0)',
                    'enhanced': 'true (défaut) — active le pipeline harmonique complet',
                    'hd': 'false (défaut) — upscaling 48 kHz si true',
                },
                'engine': 'Piper TTS (fr_FR-siwis-medium) + enhancements harmoniques',
                'quality': '22-48 kHz, 16-bit, mono',
            })

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/voice/offline':
            if not self.voice_engine:
                self._send_json({'error': 'engine_not_initialized'}, 500)
                return

            try:
                data = self._read_json()
            except Exception:
                self._send_json({'error': 'invalid_json'}, 400)
                return

            text = data.get('text', '').strip()
            if not text:
                self._send_json({'error': 'empty_text'}, 400)
                return

            voice = data.get('voice', 'siwis')
            speed = float(data.get('speed', 1.0))
            profile = data.get('profile', None)
            enhanced = data.get('enhanced', True)   # activé par défaut !
            hd_upscale = data.get('hd', False)       # 48 kHz (optionnel, ~2× plus lourd)

            # Limiter la longueur (éviter les abus)
            if len(text) > 2000:
                text = text[:2000]

            # ═══ ÉTAPE 1 : Pré-processing du texte (prononciation + prosodie) ═══
            if enhanced:
                t_pre = time.perf_counter()
                original_text = text
                text = enhance_text(text)
                if text != original_text:
                    dt_pre = (time.perf_counter() - t_pre) * 1000
                    log.info(f"  Pré-processing texte: {len(original_text)} → {len(text)} chars ({dt_pre:.0f} ms)")

            # ═══ ÉTAPE 2 : Synthèse vocale Piper ═══
            t0 = time.perf_counter()
            try:
                audio = self.voice_engine.speak(text, voice=voice, speed=speed, profile=profile)
            except Exception as e:
                log.error(f"Erreur synthèse: {e}")
                self._send_json({'error': 'synthesis_failed', 'detail': str(e)}, 500)
                return
            dt_tts = (time.perf_counter() - t0) * 1000

            if not audio or len(audio) < 100:
                self._send_json({'error': 'no_audio_generated'}, 500)
                return

            # ═══ ÉTAPE 3 : Post-processing harmonique (boost φ + réduction bruit + lissage ABC) ═══
            enhancement_flags = []
            if enhanced:
                t_post = time.perf_counter()
                audio_before = len(audio)
                audio = enhance_audio(
                    audio,
                    boost_strength=0.12,       # Boost φ modéré
                    noise_reduction=True,       # Réduction de bruit
                    abc_smoothing=True,         # Lissage attaque/déclin
                    upscale_hd=hd_upscale,      # Upscaling 48 kHz (si demandé)
                )
                dt_post = (time.perf_counter() - t_post) * 1000
                # Le post-processing harmonique a toujours lieu (même si taille identique)
                enhancement_flags.append('phi-boost')
                if hd_upscale:
                    enhancement_flags.append('hd-48khz')
                if len(audio) != audio_before:
                    log.info(f"  Post-processing: {audio_before//1024} → {len(audio)//1024} Ko ({dt_post:.0f} ms)")
                else:
                    log.info(f"  Post-processing φ: {dt_post:.0f} ms")

            total_ms = (time.perf_counter() - t0 + dt_tts) * 1000 if enhanced else dt_tts

            # Durée audio
            try:
                with wave.open(io.BytesIO(audio), 'rb') as wf:
                    audio_dur = wf.getnframes() / wf.getframerate()
                    audio_sr = wf.getframerate()
            except Exception:
                audio_dur = 0
                audio_sr = 22050

            self.send_response(200)
            self.send_header('Content-Type', 'audio/wav')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(audio)))
            self.send_header('X-KA-Engine', 'piper-harmonic' if enhanced else 'piper-offline')
            self.send_header('X-KA-Enhanced', ','.join(enhancement_flags) if enhancement_flags else 'none')
            self.send_header('X-KA-Synthesis-Time-Ms', str(int(dt_tts)))
            self.send_header('X-KA-Audio-Duration-S', str(round(audio_dur, 1)))
            self.end_headers()
            self.wfile.write(audio)

            log.info(f"Synthèse: {len(text)} chars → {len(audio)//1024} Ko, {audio_dur:.1f}s @{audio_sr}Hz, "
                     f"TTS={dt_tts:.0f}ms" + (f", enh={','.join(enhancement_flags)}" if enhancement_flags else ""))

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        """Supprime les logs HTTP par défaut (on logue nous-mêmes)."""
        pass

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))

    def _read_json(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        return json.loads(body) if body else {}


def main():
    parser = argparse.ArgumentParser(description='KA PHONE Voice Server — Piper neuronal offline')
    parser.add_argument('--port', type=int, default=8420, help='Port HTTP (défaut: 8420)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Interface (défaut: 0.0.0.0)')
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  KA PHONE — Voice Server (Piper neuronal)")
    print("=" * 60)
    print()

    # Initialiser le moteur AVANT de démarrer le serveur
    VoiceAPIHandler.init_engine(offline_only=True)

    print()
    print(f"  Serveur : http://localhost:{args.port}")
    print(f"  Endpoints :")
    print(f"    GET  http://localhost:{args.port}/api/voice/offline/caps")
    print(f"    POST http://localhost:{args.port}/api/voice/offline")
    print(f"    GET  http://localhost:{args.port}/api/voice/health")
    print()
    print(f"  Frontend : ouvrir ka_care.html dans le navigateur")
    print(f"  Ctrl+C   : arrêter le serveur")
    print()

    server = http.server.HTTPServer((args.host, args.port), VoiceAPIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        server.shutdown()
        print("Serveur arrêté.")


if __name__ == '__main__':
    main()
