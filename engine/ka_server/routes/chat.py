"""
KA Server — Routes Chat
========================
Endpoints pour le chat Harmonic AI avec rappel holographique M4.
"""

import logging
import re
from flask import request, jsonify, Response, stream_with_context
from flask import g as flask_g

log = logging.getLogger(__name__)


def register_chat_routes(app, services):
    """Enregistre les routes de chat."""
    
    harmonic_ai = services.get('harmonic_ai')
    brain = services.get('brain')
    hwat_bridge = services.get('hwat_bridge')
    web_retriever = services.get('web_retriever')
    hologram_store = services.get('hologram_store')
    wave_poet = services.get('wave_poet')
    config = services.get('config', {})
    
    @app.route('/api/chat', methods=['POST', 'OPTIONS'])
    def api_chat():
        """Endpoint principal de chat Harmonic AI."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        mode = data.get('mode', 'auto')  # 'auto', 'harmonic', 'llm', 'web', 'hybrid'
        user_id = data.get('user_id', 'anonymous')
        session_id = data.get('session_id', '')
        stream = data.get('stream', False)
        
        if not message:
            return jsonify({'error': 'Message vide', 'code': 'EMPTY_MESSAGE'}), 400
        
        # Récupérer services
        ai = harmonic_ai or services.get('harmonic_ai')
        brain_svc = brain or services.get('brain')
        
        if not ai and not brain_svc:
            return jsonify({
                'error': 'Service IA non disponible',
                'code': 'AI_UNAVAILABLE',
                'fallback': True
            }), 503
        
        try:
            # 🌊 HarmonicAI v3 — ARITHMÉTIQUE ÉMERGENTE EN PREMIER
            # "combien font 15*7 ?" → 105 par émergence, sans RAG, sans LLM
            try:
                from ka_server.services.harmonic_v3 import detect_and_solve_math
                math_result = detect_and_solve_math(message)
                if math_result.get('handled'):
                    return jsonify({
                        'response': math_result['explanation'],
                        'result': math_result['result'],
                        'expression': math_result['expression'],
                        'method': math_result['method'],
                        'engine': 'harmonic_v3',
                        'emergence': True,
                        'facts_stored': 0,
                        'code': 'EMERGENCE_ARITHMETIC',
                    }), 200
            except Exception as e:
                log.debug(f"Arithmetic emergence failed: {e}")

            # 🧠 MEMORY-FIRST — la mémoire répond AVANT le LLM
            # « Le LLM ne sait rien : il formule ce que la mémoire certifie,
            #    et se tait quand elle se tait. » — la réponse vient du fait
            #    stocké (avec provenance), jamais d'une fabrication.
            try:
                from ka_server.services.memory_first import ask as memory_first_ask
                mf = memory_first_ask(message)
                if not mf['refused']:
                    return jsonify({
                        'response': mf['answer'],
                        'provenance': mf['provenance'],
                        'confidence': mf['confidence'],
                        'method': 'memory-first — le fait stocké, pas le LLM',
                        'engine': 'memory_first',
                        'code': 'MEMORY_FIRST_ANSWER',
                    }), 200
            except Exception as e:
                log.debug(f"Memory-first failed: {e}")
            
            # Détection intention spécialisation
            if _is_specialize_intent(message):
                return jsonify({
                    'redirect': '/api/specialize',
                    'message': message,
                    'code': 'SPECIALIZE_INTENT'
                }), 200
            
            # Rappel holographique M4 (consensus multi-domaines)
            consensus_facts = []
            best_holo_id = None
            if brain_svc and hologram_store:
                try:
                    from ka_server.services.harmonic_ai import holographic_consensus_recall
                    consensus_facts, best_holo_id = holographic_consensus_recall(
                        message, top_domains=3, top_k=5
                    )
                except Exception as e:
                    log.warning(f"Holographic recall failed: {e}")
            
            # Construction contexte
            context = _build_context(message, consensus_facts, best_holo_id, brain_svc)
            
            # Génération réponse
            if stream:
                return Response(
                    stream_with_context(_generate_stream(ai, brain_svc, message, context, mode, user_id)),
                    mimetype='text/event-stream'
                )
            else:
                response = _generate_response(ai, brain_svc, message, context, mode, user_id)
                return jsonify(response)
                
        except Exception as e:
            log.error(f"Chat error: {e}")
            return jsonify({
                'error': str(e),
                'code': 'CHAT_ERROR'
            }), 500
    
    @app.route('/api/chat/voice', methods=['POST'])
    def api_chat_voice():
        """Chat avec réponse vocale (TTS)."""
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        voice = data.get('voice', 'fr_FR')  # Piper voice
        
        if not message:
            return jsonify({'error': 'Message vide'}), 400
        
        # Générer réponse texte
        chat_response = api_chat()
        if isinstance(chat_response, tuple):
            response_data, status = chat_response
            if status != 200:
                return chat_response
        else:
            response_data = chat_response.get_json()
        
        text = response_data.get('response', '')
        
        # Synthèse vocale (si voice engine dispo)
        voice_engine = services.get('voice_engine')
        if voice_engine:
            try:
                audio_data = voice_engine.synthesize(text, voice=voice)
                if audio_data:
                    import base64
                    return jsonify({
                        'response': text,
                        'audio_base64': base64.b64encode(audio_data).decode('utf-8'),
                        'voice': voice,
                        'format': 'wav'
                    })
            except Exception as e:
                log.warning(f"TTS failed: {e}")
        
        return jsonify({
            'response': text,
            'tts_available': False,
            'fallback': 'text_only'
        })
    
    @app.route('/api/chat/history', methods=['GET'])
    def api_chat_history():
        """Historique de conversation (si session gérée)."""
        session_id = request.args.get('session_id', '')
        user_id = request.args.get('user_id', 'anonymous')
        limit = min(int(request.args.get('limit', 50)), 200)
        
        # TODO: Implémenter persistance session (Redis/DB)
        return jsonify({
            'session_id': session_id,
            'user_id': user_id,
            'history': [],
            'message': 'History persistence not yet implemented'
        })
    
    @app.route('/api/chat/feedback', methods=['POST'])
    def api_chat_feedback():
        """Feedback utilisateur sur la réponse (pour apprentissage)."""
        data = request.get_json() or {}
        session_id = data.get('session_id', '')
        message_id = data.get('message_id', '')
        rating = data.get('rating')  # 1-5 ou -1/1
        feedback_text = data.get('feedback', '')
        
        # TODO: Stocker feedback pour RLHF
        log.info(f"Feedback: session={session_id} msg={message_id} rating={rating}")
        
        return jsonify({'status': 'ok', 'message': 'Feedback enregistré'})


def _is_specialize_intent(message: str) -> bool:
    """Détecte si l'utilisateur demande une spécialisation."""
    from ka_server.services.harmonic_ai import _SPECIALIZE_RE
    return bool(_SPECIALIZE_RE.match(message.strip()))


def _build_context(message: str, consensus_facts: list, best_holo_id: str, brain) -> dict:
    """Construit le contexte pour la génération."""
    context = {
        'message': message,
        'consensus_facts': consensus_facts[:10] if consensus_facts else [],
        'best_domain': best_holo_id,
        'holographic_recall': bool(consensus_facts),
    }
    
    if consensus_facts:
        # Construire le contexte factuel pour le prompt
        facts_text = '\n'.join([
            f"- {s} {r} {o} (score: {score:.2f})"
            for s, r, o, _, score in consensus_facts[:8]
        ])
        context['facts_context'] = f"Contexte factuel (holographique):\n{facts_text}"
    
    return context


def _generate_response(ai, brain, message: str, context: dict, mode: str, user_id: str) -> dict:
    """Génère une réponse (non-streaming)."""
    response_text = ""
    source = "unknown"
    
    # Mode auto : décider selon dispo
    if mode == 'auto':
        if ai and hasattr(ai, 'ask'):
            mode = 'harmonic'
        elif brain:
            mode = 'brain'
        else:
            mode = 'fallback'
    
    if mode == 'harmonic' and ai:
        try:
            result = ai.ask(message)
            response_text = result.get('answer', '') if isinstance(result, dict) else str(result)
            source = 'harmonic_ai'
        except Exception as e:
            log.warning(f"HarmonicAI failed: {e}")
            mode = 'brain'
    
    if mode == 'brain' and brain:
        try:
            response_text = brain.ask(message)
            source = 'harmonic_brain'
        except Exception as e:
            log.warning(f"Brain failed: {e}")
            mode = 'fallback'
    
    if mode == 'fallback':
        response_text = _fallback_response(message)
        source = 'fallback'
    
    # Vérifier refus calibré
    from ka_server.services.harmonic_ai import is_refusal, is_garbage_answer
    is_ref = is_refusal(response_text)
    is_garbage = is_garbage_answer(message, response_text) if not is_ref else False
    
    # Style wave si dispo
    styled = response_text
    try:
        from ka_server.services.harmonic_ai import get_wave_poet
        poet = get_wave_poet()
        if poet and not is_ref and not is_garbage:
            styled = poet.render(response_text, style='balanced')
    except Exception:
        pass
    
    return {
        'response': styled,
        'raw_response': response_text,
        'source': source,
        'is_refusal': is_ref,
        'is_garbage': is_garbage,
        'holographic_context': context.get('holographic_recall', False),
        'best_domain': context.get('best_domain'),
        'consensus_facts_count': len(context.get('consensus_facts', [])),
    }


def _generate_stream(ai, brain, message: str, context: dict, mode: str, user_id: str):
    """Générateur de réponse en streaming (SSE)."""
    import json
    import time
    
    yield f"data: {json.dumps({'type': 'start', 'message': message})}\n\n"
    
    # Simuler streaming pour l'instant
    response = _generate_response(ai, brain, message, context, mode, user_id)
    
    # Streamer par chunks
    text = response['response']
    words = text.split()
    chunk_size = 3
    
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i+chunk_size]) + ' '
        yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
        import time as t
        t.sleep(0.02)  # Petit délai pour effet streaming
    
    yield f"data: {json.dumps({'type': 'end', **{k: v for k, v in response.items() if k != 'response'}})}\n\n"


def _fallback_response(message: str) -> str:
    """Réponse de secours basique."""
    msg_lower = message.lower()
    
    if any(w in msg_lower for w in ['bonjour', 'salut', 'hello', 'hi']):
        return "Bonjour ! Je suis KA, votre assistant harmonique. Comment puis-je vous aider ?"
    
    if any(w in msg_lower for w in ['merci', 'thanks', 'thank you']):
        return "Je vous en prie ! N'hésitez pas si vous avez d'autres questions."
    
    if any(w in msg_lower for w in ['au revoir', 'bye', 'goodbye', 'à plus']):
        return "Au revoir ! À bientôt pour de nouvelles découvertes harmoniques."
    
    if '?' in message:
        return "C'est une excellente question. Pour une réponse précise, j'aurais besoin d'accéder à mes connaissances holographiques. Voulez-vous que je me spécialise sur ce sujet ?"
    
    return "Je comprends. Dites-m'en plus pour que je puisse mieux vous aider avec mes connaissances harmoniques."