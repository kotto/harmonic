"""
KA Server — Routes Voice (TTS/STT)
===================================
Endpoints pour synthèse vocale (Piper) et reconnaissance (Vosk).
"""

import logging
import base64
from flask import request, jsonify, send_file
import io

log = logging.getLogger(__name__)


def register_voice_routes(app, services):
    """Enregistre les routes Voice."""
    
    voice_engine = services.get('voice_engine')
    
    @app.route('/api/voice/tts', methods=['POST', 'OPTIONS'])
    def api_tts():
        """Synthèse vocale (Text-to-Speech) avec Piper."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        text = data.get('text', '').strip()
        voice = data.get('voice', 'fr_FR')  # ex: fr_FR, en_US, fr_FR-siwis
        speed = float(data.get('speed', 1.0))
        return_base64 = data.get('base64', False)
        
        if not text:
            return jsonify({'error': 'Texte requis', 'code': 'MISSING_TEXT'}), 400
        
        if len(text) > 5000:
            return jsonify({'error': 'Texte trop long (max 5000 caractères)', 'code': 'TEXT_TOO_LONG'}), 413
        
        if not voice_engine:
            return jsonify({
                'error': 'Moteur vocal non disponible',
                'code': 'VOICE_UNAVAILABLE',
                'fallback': 'Install Piper TTS models'
            }), 503
        
        try:
            audio_data = voice_engine.synthesize(text, voice=voice, speed=speed)
            
            if not audio_data:
                return jsonify({'error': 'Synthèse échouée', 'code': 'TTS_FAILED'}), 500
            
            # Post-filtre φ-harmonique (optionnel, activé par défaut)
            if data.get('phi_enhance', True):
                try:
                    import numpy as np
                    import sys
                    sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))
                    from thu.phi_post_filter import PhiPostFilter
                    sr = 22050  # fréquence Piper par défaut
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                    pf = PhiPostFilter(sample_rate=sr, strength=0.35)
                    enhanced = pf.process(audio_np)
                    audio_data = (np.clip(enhanced * 32768, -32768, 32767).astype(np.int16)).tobytes()
                except Exception as e:
                    log.warning(f"Phi post-filter skipped: {e}")
            
            if return_base64:
                b64 = base64.b64encode(audio_data).decode('utf-8')
                return jsonify({
                    'success': True,
                    'audio_base64': b64,
                    'format': 'wav',
                    'voice': voice,
                    'text_length': len(text),
                })
            else:
                output = io.BytesIO(audio_data)
                output.seek(0)
                return send_file(
                    output,
                    mimetype='audio/wav',
                    as_attachment=True,
                    download_name=f'tts_{voice}.wav'
                )
                
        except Exception as e:
            log.error(f"TTS error: {e}")
            return jsonify({'error': str(e), 'code': 'TTS_ERROR'}), 500
    
    @app.route('/api/voice/stt', methods=['POST', 'OPTIONS'])
    def api_stt():
        """Reconnaissance vocale (Speech-to-Text) avec Vosk."""
        if request.method == 'OPTIONS':
            return '', 200
        
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({'error': 'Content-Type multipart/form-data requis'}), 400
        
        file = request.files.get('audio')
        if not file:
            return jsonify({'error': 'Fichier audio requis', 'code': 'NO_AUDIO'}), 400
        
        language = request.form.get('language', 'fr')  # fr, en, etc.
        
        audio_data = file.read()
        
        if not voice_engine:
            return jsonify({
                'error': 'Moteur vocal non disponible',
                'code': 'VOICE_UNAVAILABLE'
            }), 503
        
        try:
            text = voice_engine.transcribe(audio_data, language=language)
            
            if text is None:
                return jsonify({'error': 'Transcription échouée', 'code': 'STT_FAILED'}), 500
            
            return jsonify({
                'success': True,
                'text': text,
                'language': language,
                'audio_duration_estimate': len(audio_data) / 32000,  # estimation rough
            })
            
        except Exception as e:
            log.error(f"STT error: {e}")
            return jsonify({'error': str(e), 'code': 'STT_ERROR'}), 500
    
    @app.route('/api/voice/voices', methods=['GET'])
    def api_voices():
        """Liste les voix Piper disponibles."""
        if not voice_engine:
            return jsonify({'error': 'Moteur vocal non disponible', 'code': 'VOICE_UNAVAILABLE'}), 503
        
        try:
            voices = voice_engine.list_voices()
            return jsonify({'voices': voices})
        except Exception as e:
            log.error(f"List voices error: {e}")
            return jsonify({'error': str(e), 'code': 'VOICES_FAILED'}), 500
    
    @app.route('/api/voice/status', methods=['GET'])
    def api_voice_status():
        """Statut du moteur vocal."""
        if not voice_engine:
            return jsonify({
                'available': False,
                'tts': False,
                'stt': False,
                'message': 'Voice engine not initialized'
            })
        
        try:
            status = voice_engine.get_status()
            return jsonify(status)
        except Exception as e:
            return jsonify({
                'available': True,
                'tts': True,
                'stt': True,
                'error': str(e)
            })
    
    @app.route('/api/voice/stream', methods=['POST'])
    def api_voice_stream():
        """Streaming TTS (chunked response)."""
        data = request.get_json() or {}
        text = data.get('text', '').strip()
        voice = data.get('voice', 'fr_FR')
        
        if not text:
            return jsonify({'error': 'Texte requis'}), 400
        
        if not voice_engine:
            return jsonify({'error': 'Moteur vocal non disponible'}), 503
        
        try:
            # Générer audio complet puis streamer par chunks
            audio_data = voice_engine.synthesize(text, voice=voice)
            if not audio_data:
                return jsonify({'error': 'Synthèse échouée'}), 500
            
            def generate():
                chunk_size = 4096
                for i in range(0, len(audio_data), chunk_size):
                    yield audio_data[i:i+chunk_size]
            
            return app.response_class(
                generate(),
                mimetype='audio/wav',
                headers={
                    'Content-Disposition': f'attachment; filename=stream_{voice}.wav',
                    'X-Voice': voice,
                    'X-Text-Length': str(len(text))
                }
            )
        except Exception as e:
            log.error(f"Stream TTS error: {e}")
            return jsonify({'error': str(e)}), 500

    # ── Endpoints pour le client mobile KA MOBILE (vital_ka_voice.js) ──
    # Ces endpoints sont appelés par le module vocal côté client (port 8420).
    # Compatibilité avec l'interface attendue par vital_ka_voice.js.

    @app.route('/api/voice/offline/caps', methods=['GET', 'OPTIONS'])
    def api_voice_offline_caps():
        """Capacités du moteur TTS hors-ligne (appelé par KA MOBILE)."""
        if request.method == 'OPTIONS':
            return '', 200

        piper_ready = False
        piper_info = None

        if voice_engine:
            try:
                status = voice_engine.get_status()
                piper_info = status.get('tts', {})
                if isinstance(piper_info, dict):
                    piper_ready = piper_info.get('available', False)
                elif isinstance(piper_info, bool):
                    piper_ready = piper_info
            except Exception:
                pass

        return jsonify({
            'offline_ready': piper_ready,
            'engines': {
                'piper': {
                    'available': piper_ready,
                    'voices': voice_engine.list_voices() if voice_engine else [],
                    'sample_rate': 22050,
                    'format': 'wav',
                }
            },
            'enhancements': {
                'harmonic_post_processor': False,
            },
            'server': {
                'backend': 'ka_server',
                'version': '4.0',
                'port': request.host.split(':')[-1] if ':' in request.host else '8767',
            }
        })

    @app.route('/api/voice/offline', methods=['POST', 'OPTIONS'])
    def api_voice_offline():
        """Synthèse vocale hors-ligne (appelé par KA MOBILE).

        Body: { "text": "bonjour", "voice": "fr_FR", "speed": 1.0, "enhanced": false, "hd": false }
        Retourne un fichier WAV (comme /api/voice/tts).
        """
        if request.method == 'OPTIONS':
            return '', 200

        data = request.get_json(silent=True) or {}
        text = data.get('text', '').strip()
        voice = data.get('voice', 'fr_FR')
        speed = float(data.get('speed', 1.0))
        enhanced = data.get('enhanced', False)
        hd = data.get('hd', False)

        if not text:
            return jsonify({'error': 'Texte requis', 'code': 'MISSING_TEXT'}), 400
        if len(text) > 5000:
            return jsonify({'error': 'Texte trop long', 'code': 'TEXT_TOO_LONG'}), 413
        if not voice_engine:
            return jsonify({
                'error': 'Moteur vocal non disponible',
                'code': 'VOICE_UNAVAILABLE',
                'fallback_supported': True,
            }), 503

        try:
            audio_data = voice_engine.synthesize(text, voice=voice, speed=speed)
            if not audio_data:
                return jsonify({'error': 'Synthèse échouée', 'code': 'TTS_FAILED'}), 500

            output = io.BytesIO(audio_data)
            output.seek(0)
            return send_file(
                output,
                mimetype='audio/wav',
                as_attachment=True,
                download_name=f'offline_{voice}.wav'
            )
        except Exception as e:
            log.error(f"Offline TTS error: {e}")
            return jsonify({'error': str(e), 'code': 'TTS_ERROR'}), 500