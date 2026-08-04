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