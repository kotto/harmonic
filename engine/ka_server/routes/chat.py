"""
KA Server — Routes Chat
========================
Endpoints pour le chat Harmonic AI avec rappel holographique M4
+ PromptComprehendor (routeur d'intention unifié).

Pipeline :
  1. PromptComprehendor → classification d'intention + slots
  2. Si ambigu → question de clarification
  3. Routage par intent → handler spécialisé
  4. Fallback → LLM (HarmonicAI / HarmonicBrain)
"""

import logging
import re
import json
import time
from flask import request, jsonify, Response, stream_with_context
from flask import g as flask_g

log = logging.getLogger(__name__)

# ── Session context: mémorise le dernier intent pour les follow-ups ──────────
_SESSION_LAST_HANDLER = {}  # session_id → {'handler': str, 'message': str, 'ts': float}

# ── Seuil de déclenchement du LLM en renfort ────────────────────────────────
_LLM_RENFORT_THRESHOLD = 0.35  # en dessous de cette confiance, on appelle le LLM

# ── Helpers Phi renfort (pooling + contexte) ────────────────────────────────
_PHI_API = "http://localhost:8080"
_phi_session = None  # requests.Session, paresseux


def _get_phi_session():
    """Session réutilisable (keep-alive) pour les appels Phi. None si requests absent."""
    global _phi_session
    if _phi_session is not None:
        return _phi_session
    try:
        import requests
        _phi_session = requests.Session()
        return _phi_session
    except ImportError:
        return None


def _phi_query(question: str, context_text: str = "", timeout: int = 30) -> str | None:
    """
    Appel Phi non-streaming. Le contexte conversationnel est passé dans le
    système pour que les follow-ups restent cohérents.
    """
    import json as _json
    system = "Tu es un assistant utile qui répond en français de façon claire et concise."
    if context_text:
        system = (
            "Tu es un assistant utile qui répond en français de façon claire et concise.\n"
            "Voici le contexte de la conversation :\n" + context_text
        )
    payload = _json.dumps({"question": question, "system": system}).encode()

    sess = _get_phi_session()
    try:
        if sess:
            r = sess.post(_PHI_API + "/phi/query", data=payload,
                          headers={"Content-Type": "application/json"}, timeout=timeout)
            data = r.json()
        else:
            import urllib.request as _ur
            req = _ur.Request(_PHI_API + "/phi/query", data=payload,
                              headers={"Content-Type": "application/json"})
            data = _json.loads(_ur.urlopen(req, timeout=timeout).read().decode())
        answer = data.get("answer", "")
        return answer if len(answer) > 10 else None
    except Exception as e:
        log.debug(f"Phi query failed: {e}")
        return None


def _phi_stream(question: str, context_text: str = "", timeout: int = 60):
    """
    Générateur SSE de vrai streaming token-par-token depuis /phi/stream.
    Le contexte est passé dans le système (cohérence des follow-ups).
    """
    import json as _json
    import urllib.request as _ur

    system = "Tu es un assistant utile qui répond en français de façon claire et concise."
    if context_text:
        system = (
            "Tu es un assistant utile qui répond en français de façon claire et concise.\n"
            "Voici le contexte de la conversation :\n" + context_text
        )

    yield f"data: {_json.dumps({'type': 'start', 'message': question})}\n\n"
    full = []
    try:
        req = _ur.Request(
            _PHI_API + "/phi/stream",
            data=_json.dumps({"question": question, "system": system}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with _ur.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'):
                    continue
                try:
                    p = _json.loads(line[5:].lstrip())
                except Exception:
                    continue
                t = p.get('type')
                if t == 'token':
                    tok = p.get('token', '')
                    full.append(tok)
                    yield f"data: {_json.dumps({'type': 'chunk', 'content': tok})}\n\n"
                elif t in ('done', 'end'):
                    break
                elif t == 'error':
                    log.warning(f"Phi stream error: {p.get('message')}")
                    break
    except Exception as e:
        log.debug(f"Phi stream connection failed: {e}")
        yield f"data: {_json.dumps({'type': 'end', 'error': 'Phi stream indisponible'})}\n\n"
        return

    text = ''.join(full)
    yield f"data: {_json.dumps({'type': 'meta', 'source': 'phi-3.5-mini-stream'})}\n\n"
    yield f"data: {_json.dumps({'type': 'end', 'done': True, 'source': 'phi-3.5-mini-stream', 'response': text})}\n\n"


def _llm_classify_intent(message: str, ai, brain) -> dict | None:
    """
    LLM en renfort pour classifier une intention que le PromptComprehendor
    n'a pas comprise avec assez de confiance.
    
    Utilise un prompt structuré qui demande un JSON en sortie.
    Ne modifie pas l'état du LLM, ne coûte qu'une inférence légère.
    
    Returns:
        dict avec {intent, handler, confidence, slots, explanation} ou None
    """
    prompt = (
        "Tu es un classifieur d'intention pour l'assistant KA Mobile. "
        "Réponds UNIQUEMENT au format JSON suivant, sans texte avant ni après :\n"
        "{\n"
        '  "intent": "nom_intention",\n'
        '  "handler": "nom_handler",\n'
        '  "confidence": 0.0-1.0,\n'
        '  "slots": { "slot1": "valeur1" },\n'
        '  "explanation": "pourquoi cette intention"\n'
        "}\n\n"
        "Intention | Handler | Description\n"
        "--- | --- | ---\n"
        "storage_action | storage_saver | L'utilisateur veut nettoyer, compresser, libérer de l'espace sur son téléphone\n"
        "action_command | agent_action | L'utilisateur veut appeler, SMS, ouvrir une app, wifi, batterie\n"
        "arithmetic | arithmetic_emergence | L'utilisateur demande un calcul mathématique\n"
        "specialize_request | specialize | L'utilisateur demande une spécialisation ou un hologramme\n"
        "learning | learning | L'utilisateur veut mémoriser/apprendre une information\n"
        "comparison | comparison | L'utilisateur compare deux choses\n"
        "generation | generation | L'utilisateur demande une création (poème, histoire, briefing)\n"
        "greeting | greeting | Salutation, remerciement, au revoir\n"
        "factual_question | knowledge_retrieval | Question de connaissance (qui, quand, où, pourquoi, comment)\n"
        "identity_question | identity | L'utilisateur demande qui est KA, son rôle, ce qu'il peut faire\n"
        "general_chat | llm_fallback | Conversation générale, tout le reste\n\n"
        f"Message utilisateur: \"{message}\"\n\n"
        "JSON:"
    )
    
    # Essayer HarmonicAI d'abord
    if ai and hasattr(ai, 'ask'):
        try:
            result = ai.ask(prompt)
            if isinstance(result, dict):
                text = result.get('answer', '')
            else:
                text = str(result)
            parsed = _parse_llm_json(text)
            if parsed:
                return parsed
        except Exception as e:
            log.debug(f"LLM renfort (HarmonicAI) failed: {e}")
    
    # Fallback HarmonicBrain
    if brain and hasattr(brain, 'ask'):
        try:
            text = brain.ask(prompt)
            parsed = _parse_llm_json(text)
            if parsed:
                return parsed
        except Exception as e:
            log.debug(f"LLM renfort (Brain) failed: {e}")
    
    return None


def _parse_llm_json(text: str) -> dict | None:
    """
    Extrait et parse un objet JSON d'une réponse LLM.
    Tolère les marques de code ```json ... ``` et le texte autour.
    """
    if not text:
        return None
    
    # Nettoyer la réponse
    cleaned = text.strip()
    
    # Enlever les blocs de code markdown
    cleaned = re.sub(r'```(?:json)?\s*', '', cleaned)
    
    # Chercher un objet JSON dans la réponse
    try:
        # Essayer de parser directement
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Chercher { ... } dans le texte
    match = re.search(r'\{[^{}]*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Chercher une ligne avec intent=
    match = re.search(r'intent["\']?\s*:\s*["\'](\w+)["\']', cleaned)
    if match:
        intent = match.group(1)
        handler_map = {
            'storage_action': 'storage_saver',
            'action_command': 'agent_action',
            'arithmetic': 'arithmetic_emergence',
            'reason': 'wave_reasoner',
            'specialize_request': 'specialize',
            'learning': 'learning',
            'comparison': 'comparison',
            'generation': 'generation',
            'greeting': 'greeting',
            'factual_question': 'knowledge_retrieval',
            'identity_question': 'identity',
            'general_chat': 'llm_fallback',
        }
        return {
            'intent': intent,
            'handler': handler_map.get(intent, 'llm_fallback'),
            'confidence': 0.7,
            'slots': {},
            'explanation': 'extraction regex fallback',
        }
    
    return None


INTENTS_FR = {
    'storage_action': 'libérer de l\'espace / compression',
    'action_command': 'une action téléphone (appel, SMS, app)',
    'arithmetic': 'un calcul',
    'reason': 'un raisonnement / calcul harmonique',
    'specialize_request': 'une spécialisation / hologramme',
    'learning': 'mémoriser une information',
    'comparison': 'une comparaison',
    'generation': 'une création de contenu',
    'greeting': 'une salutation',
    'factual_question': 'une question de connaissance',
    'identity_question': 'une question sur mon identité',
    'general_chat': 'une discussion générale',
}


def _resolve_handler_with_session(frame, session_id: str, message: str) -> str:
    """Résout le handler final en tenant compte du contexte de session."""
    handler = frame.suggested_handler if frame else None
    if not session_id:
        return handler
    
    prev = _SESSION_LAST_HANDLER.get(session_id)
    if not prev:
        return handler
    
    confirmation_words = ['oui', 'ok', 'okay', 'd\'accord', 'vas-y', 'lance',
                          'go', 'pourquoi pas', 'allez', 'yes', 'bien sur',
                          'bien s\'ûr', 'carr\'ément', 'super', 'parfait',
                          'volontiers', 'je veux bien', 'fais le', 'fais-le']
    
    msg_lower = message.lower().strip().rstrip('?!.')
    is_confirmation = any(msg_lower == cw or msg_lower.startswith(cw)
                          for cw in confirmation_words)
    
    if is_confirmation and prev['handler'] == 'storage_saver':
        log.info(f'🔄 Session follow-up: confirmation → storage_saver (was: {handler})')
        return 'storage_saver'
    
    return handler


def _update_session_handler(session_id: str, handler: str, message: str):
    """Mémorise le handler de la réponse pour les follow-ups."""
    if session_id:
        _SESSION_LAST_HANDLER[session_id] = {
            'handler': handler,
            'message': message,
            'ts': time.time(),
        }


def _llm_fallback_ambiguity(frame, message: str) -> str:
    """
    Génère une question de clarification basée sur les scores du PC,
    en proposant les options les plus probables.
    """
    if not frame or not frame.all_scores:
        return "Je n'ai pas bien compris. Pouvez-vous reformuler ?"
    
    top = sorted(frame.all_scores.items(), key=lambda x: -x[1])[:3]
    top = [(i, s) for i, s in top if s > 0.1]
    
    if len(top) >= 2:
        options = []
        for intent_id, score in top:
            desc = INTENTS_FR.get(intent_id, intent_id)
            options.append(f"« {desc} »")
        
        if len(options) == 2:
            return (f"J'hésite entre {options[0]} ou {options[1]}. "
                    f"Que souhaitez-vous faire ?")
        else:
            return (f"Je vois plusieurs possibilités : {', '.join(options[:-1])} "
                    f"ou {options[-1]}. Laquelle vous intéresse ?")
    
    return "Je n'ai pas compris votre demande. Pouvez-vous préciser ?"


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
        
        # ═══════════════════════════════════════════════════════════════════
        # ÉTAPE 1 : COMPRÉHENSION DU PROMPT (PromptComprehendor)
        # ═══════════════════════════════════════════════════════════════════
        frame = None
        llm_renfort_used = False
        fasttext_renfort_used = False
        try:
            from ka_server.services.prompt_comprehendor import comprehend
            frame = comprehend(message, session_id=session_id, user_id=user_id)
            log.debug(f"🧠 Intent PC: {frame.intent} (conf={frame.confidence:.2f}, "
                     f"handler={frame.suggested_handler})")
            
            # ── RENFORT si confiance insuffisante ──
            # 3 niveaux : FastText (0.7ms, offline) → LLM (2-5s, cloud/local)
            # FastText capture les reformulations que les patterns regex ratent
            # et le fait sans LLM, sans GPU, sans latence.
            if frame.confidence < _LLM_RENFORT_THRESHOLD:
                # ── Niveau 1 : FastText (sklearn, char n-grams 2-5) ──
                try:
                    from ka_server.services.fasttext_classifier import get_classifier
                    ft = get_classifier()
                    if ft.is_ready:
                        ft_intent, ft_conf = ft.predict(message)
                        log.info(f"🔤 FastText renfort: PC conf={frame.confidence:.2f} "
                                 f"→ FT={ft_intent} (conf={ft_conf:.2f})")
                        # Seuil FastText plus bas que LLM (0.25 vs 0.35)
                        # car le classifieur sklearn est calibré / le modèle
                        # FastText a des scores plus conservateurs
                        FT_CONF_THRESHOLD = 0.25
                        if ft_conf > FT_CONF_THRESHOLD:
                            handler_map = {
                                'storage_action': 'storage_saver',
                                'action_command': 'agent_action',
                                'arithmetic': 'arithmetic_emergence',
                                'reason': 'wave_reasoner',
                                'specialize_request': 'specialize',
                                'learning': 'learning',
                                'comparison': 'comparison',
                                'generation': 'generation',
                                'greeting': 'greeting',
                                'factual_question': 'knowledge_retrieval',
                                'identity_question': 'identity',
                                'general_chat': 'llm_fallback',
                            }
                            frame.intent = ft_intent
                            frame.confidence = ft_conf
                            frame.suggested_handler = handler_map.get(
                                ft_intent, frame.suggested_handler)
                            frame.metadata['fasttext_renfort'] = {
                                'intent': ft_intent, 'confidence': ft_conf}
                            fasttext_renfort_used = True
                            log.info(f"   ✅ FastText renfort → {ft_intent} "
                                     f"(conf={ft_conf:.2f})")
                except Exception as e:
                    log.debug(f"FastText renfort indisponible: {e}")
                
                # ── Niveau 2 : LLM (Phi-3.5-mini ou HarmonicAI) ──
                # Déclenché seulement si FastText n'a pas pu classer
                if not fasttext_renfort_used:
                    ai = harmonic_ai or services.get('harmonic_ai')
                    brain_svc = brain or services.get('brain')
                    if ai or brain_svc:
                        log.info(f"🔎 LLM renfort: PC conf={frame.confidence:.2f} "
                                 f"(seuil={_LLM_RENFORT_THRESHOLD})")
                        llm_frame = _llm_classify_intent(message, ai, brain_svc)
                        if llm_frame and llm_frame.get('confidence', 0) > _LLM_RENFORT_THRESHOLD:
                            log.info(f"   LLM renfort → {llm_frame['intent']} "
                                     f"(conf={llm_frame['confidence']})")
                            frame.intent = llm_frame['intent']
                            frame.confidence = llm_frame['confidence']
                            frame.suggested_handler = llm_frame.get('handler', frame.suggested_handler)
                            if llm_frame.get('slots'):
                                frame.slots.update(llm_frame['slots'])
                            frame.metadata['llm_renfort'] = llm_frame
                            llm_renfort_used = True
                        else:
                            log.debug(f"   LLM renfort n'a pas amélioré la classification")
        except Exception as e:
            log.debug(f"PromptComprehendor unavailable, fallback to cascade: {e}")
        
        # ── AMBIGUÏTÉ → question de clarification ──
        if frame and frame.ambiguity:
            # Utiliser une question plus contextuelle avec les options les plus probables
            question = _llm_fallback_ambiguity(frame, message)
            return jsonify({
                'response': question,
                'engine': 'prompt_comprehendor',
                'method': 'clarification',
                'code': 'AMBIGUITY_DETECTED',
                'intent': frame.intent,
                'confidence': frame.confidence,
                'all_scores': frame.all_scores,
                'llm_renfort_used': llm_renfort_used,
                'fasttext_renfort_used': fasttext_renfort_used,
                'suggestions': ['Reformuler',
                                f'Je cherche à {INTENTS_FR.get(list(sorted(frame.all_scores.items(), key=lambda x:-x[1]))[0][0], "…")}'
                                if frame.all_scores else '…'],
            }), 200
        
        # ── ROUTAGE PAR INTENT (avec contexte de session) ──
        handler = _resolve_handler_with_session(frame, session_id, message)
        
        # 🗜️ STORAGE_SAVER
        if handler == 'storage_saver':
            _update_session_handler(session_id, 'storage_saver', message)
            try:
                storage_response = _handle_storage_intent(message, services)
                if storage_response:
                    storage_response['intent_frame'] = frame.to_dict() if frame else None
                    return jsonify(storage_response), 200
            except Exception as e:
                log.debug(f"Storage handler failed: {e}")
        
        # 🌊 ARITHMETIC_EMERGENCE (WaveReasoner FHRR d'abord, puis harmonic_v3)
        if handler == 'arithmetic_emergence':
            try:
                # Priorité 1 : WaveReasoner FHRR (local, sans dépendances)
                from ka_server.services.wave_reasoner import get_reasoner
                wr = get_reasoner()
                wr_result = wr.reason_arithmetic(message)
                if wr_result.get('handled'):
                    return jsonify({
                        'response': wr_result['explanation'],
                        'result': wr_result['result'],
                        'expression': wr_result.get('expression', message),
                        'method': wr_result['method'],
                        'engine': 'wave_reasoner',
                        'resonance': wr_result.get('resonance', 0),
                        'steps': wr_result.get('steps', []),
                        'emergence': True,
                        'code': 'WAVE_REASONER_ARITHMETIC',
                        'intent_frame': frame.to_dict() if frame else None,
                    }), 200
            except Exception as e:
                log.debug(f"WaveReasoner FHRR failed: {e}")
            
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
                        'intent_frame': frame.to_dict() if frame else None,
                    }), 200
            except Exception as e:
                log.debug(f"Arithmetic emergence harmonic_v3 failed: {e}")
        
        # 🌊 WAVE_REASONER (FHRR arithmétique + logique + comparaison)
        if handler == 'wave_reasoner':
            try:
                from ka_server.services.wave_reasoner import get_reasoner
                reasoner = get_reasoner()
                
                # Essayer arithmétique FHRR directe d'abord (PEMDAS)
                arith_result = reasoner.reason_arithmetic(message)
                if arith_result.get('handled'):
                    return jsonify({
                        'response': arith_result['explanation'],
                        'result': arith_result['result'],
                        'expression': arith_result.get('expression', message),
                        'resonance': arith_result.get('resonance', 0),
                        'method': arith_result['method'],
                        'engine': 'wave_reasoner',
                        'steps': arith_result.get('steps', []),
                        'rpn': arith_result.get('rpn', ''),
                        'emergence': True,
                        'code': 'WAVE_REASONER_ARITHMETIC',
                        'intent_frame': frame.to_dict() if frame else None,
                    }), 200
                
                # Essayer comparaison si pattern détecté
                comp_match = re.search(
                    r'(?:compare|comparaison|quel\s+(?:est\s+)?(?:le|la)\s+(?:meilleur|pire)|'
                    r'(?:lequel|laquelle)\s+(?:est|serait)\s+(?:mieux|meilleur|pire))\s+'
                    r'(?:entre\s+)?(\w+)\s+(?:et|vs\.?|versus|ou)\s+(\w+)',
                    message, re.IGNORECASE
                )
                if comp_match:
                    entity_a, entity_b = comp_match.group(1), comp_match.group(2)
                    # Extraire les critères si présents
                    crit_match = re.search(
                        r'(?:sur|pour|critèr\w*|selon)\s+(?:le|la|les?\s+)?(.+?)(?:\s*\?|\s*$)',
                        message, re.IGNORECASE
                    )
                    criteria = []
                    if crit_match:
                        criteria_text = crit_match.group(1)
                        criteria = [c.strip() for c in re.split(r'[,;]|et|&', criteria_text) if c.strip()]
                    
                    comp_result = reasoner.reason_comparison(
                        entity_a, entity_b,
                        criterion=criteria[0] if len(criteria) == 1 else "",
                        criteria_list=criteria if len(criteria) > 1 else None
                    )
                    if comp_result.get('handled'):
                        return jsonify({
                            'response': comp_result['explication'],
                            'winner': comp_result['winner'],
                            'scores': comp_result['scores'],
                            'scores_detail': comp_result.get('scores_detail'),
                            'confidence': comp_result['confidence'],
                            'engine': 'wave_reasoner',
                            'method': 'wave_comparison',
                            'code': 'WAVE_REASONER_COMPARISON',
                            'intent_frame': frame.to_dict() if frame else None,
                        }), 200
                
                # Logique si prémisses détectées
                if 'si' in message.lower() or 'alors' in message.lower() or 'donc' in message.lower():
                    premise_match = re.search(r'(?:si\s+(.+?)\s+alors\s+(.+))', message, re.IGNORECASE)
                    if premise_match:
                        premises = [premise_match.group(1)]
                        query = premise_match.group(2)
                        logic_result = reasoner.reason_logic(premises, query)
                        if logic_result.get('handled'):
                            return jsonify({
                                'response': logic_result['explication'],
                                'conclusion': logic_result['conclusion'],
                                'confidence': logic_result['confidence'],
                                'warm_started': logic_result.get('warm_started', False),
                                'strategies_stored': logic_result.get('strategies_stored', 0),
                                'engine': 'wave_reasoner',
                                'method': 'wave_logic',
                                'code': 'WAVE_REASONER_LOGIC',
                                'intent_frame': frame.to_dict() if frame else None,
                            }), 200
                
            except Exception as e:
                log.debug(f"WaveReasoner failed: {e}")
        
        # ⚡ AGENT_ACTION
        if handler == 'agent_action':
            try:
                from ka_server.services.memory_first import detect_action
                action = detect_action(message)
                if action:
                    return jsonify({
                        'response': f"Commande reconnue : {action['action']}.",
                        'action': action['action'],
                        'relation': action['relation'],
                        'source': action.get('source', ''),
                        'engine': 'agent_action',
                        'method': 'detection lexicale d\'action',
                        'code': 'AGENT_ACTION',
                        'intent_frame': frame.to_dict() if frame else None,
                    }), 200
            except Exception as e:
                log.debug(f"Agent action failed: {e}")
        
        # 📚 LEARNING (mémorisation explicite)
        if handler == 'learning':
            fact_text = (frame.slots.get('fact', '') if frame else '') or message
            try:
                from ka_server.services.memory_first import store_fact
                # Extraire sujet, relation, objet du texte
                parts = fact_text.split(None, 2)
                if len(parts) >= 3:
                    sujet, relation, objet = parts[0], parts[1], parts[2]
                elif len(parts) == 2:
                    sujet, relation, objet = parts[0], 'est', parts[1]
                else:
                    sujet, relation, objet = parts[0], 'est', 'vrai'
                store_fact(sujet, relation, objet, source='utilisateur')
                return jsonify({
                    'response': f"✅ J'ai mémorisé : {sujet} {relation} {objet}.",
                    'fact': {'sujet': sujet, 'relation': relation, 'objet': objet},
                    'engine': 'memory_first',
                    'method': 'apprentissage explicite',
                    'code': 'LEARNING_STORED',
                    'intent_frame': frame.to_dict() if frame else None,
                }), 200
            except Exception as e:
                log.debug(f"Learning failed: {e}")
        
        # 🎯 SPECIALIZE_REQUEST
        if handler == 'specialize':
            domain = (frame.slots.get('domain', '') if frame else '') or message
            return jsonify({
                'redirect': '/api/specialize',
                'message': message,
                'domain': domain,
                'code': 'SPECIALIZE_INTENT',
                'intent_frame': frame.to_dict() if frame else None,
            }), 200
        
        # 👋 GREETING
        if handler == 'greeting':
            return jsonify({
                'response': _fallback_response(message),
                'engine': 'greeting',
                'method': 'réponse sociale',
                'code': 'GREETING',
                'intent_frame': frame.to_dict() if frame else None,
            }), 200

        # 🆔 IDENTITY — l'utilisateur demande qui est KA
        if handler == 'identity':
            return jsonify({
                'response': (
                    "Je suis **KA (Knowledge Amplifier)**, votre assistant harmonique 🌊\n\n"
                    "Je peux vous aider à :\n"
                    "• 📱 **Nettoyer / compresser** votre téléphone pour libérer de l'espace\n"
                    "• 🧠 **Répondre à vos questions** sur tous les sujets\n"
                    "• 🧬 **Créer des hologrammes de connaissances** (spécialisation sur un domaine)\n"
                    "• ⚡ **Exécuter des actions** : appeler, envoyer un SMS, ouvrir une app, gérer le wifi\n"
                    "• ✍️ **Générer du contenu** : poèmes, briefings, histoires\n\n"
                    "Je fonctionne avec le **PromptComprehendor** (compréhension déterministe des intentions) "
                    "et je peux utiliser **Qwen 3B** ou **Phi-3.5-mini** en renfort pour les cas complexes. "
                    "Je suis 100% déterministe — pas d'hallucination, pas de fabrication."
                ),
                'engine': 'identity',
                'method': 'présentation de KA',
                'code': 'IDENTITY_ANSWER',
                'intent_frame': frame.to_dict() if frame else None,
            }), 200
        
        # ═══════════════════════════════════════════════════════════════════
        # ÉTAPE 2 : PIPELINE IA (si pas déjà routé)
        # ═══════════════════════════════════════════════════════════════════
        
        # Récupérer services
        ai = harmonic_ai or services.get('harmonic_ai')
        brain_svc = brain or services.get('brain')
        
        # ── WaveContextManager : contexte conversationnel ──
        context_manager = None
        if session_id:
            try:
                from ka_server.services.wave_context_manager import get_context
                context_manager = get_context(session_id)
                context_manager.add_turn("user", message)
            except Exception as e:
                log.debug(f"Context manager unavailable: {e}")
        
        if not ai and not brain_svc:
            if context_manager:
                context_manager.add_turn("assistant", _fallback_response(message))
            return jsonify({
                'response': _fallback_response(message),
                'source': 'fallback',
                'code': 'AI_UNAVAILABLE',
                'fallback': True,
                'intent_frame': frame.to_dict() if frame else None,
            }), 200
        
        try:
            # 🧠 MEMORY-FIRST (questions factuelles, comparaisons)
            if handler in ('knowledge_retrieval', 'comparison', 'factual_question', None):
                memory_answered = False
                try:
                    from ka_server.services.memory_first import ask as memory_first_ask
                    mf = memory_first_ask(message)
                    if not mf['refused']:
                        answer = mf['answer']
                        if context_manager:
                            context_manager.add_turn("assistant", answer)
                        return jsonify({
                            'response': answer,
                            'provenance': mf['provenance'],
                            'confidence': mf['confidence'],
                            'method': 'memory-first — le fait stocké, pas le LLM',
                            'engine': 'memory_first',
                            'code': 'MEMORY_FIRST_ANSWER',
                            'intent_frame': frame.to_dict() if frame else None,
                        }), 200
                    memory_answered = True
                except Exception as e:
                    log.debug(f"Memory-first failed: {e}")
                
                # ⚡ PHI-3.5-mini renfort pour les questions factuelles
                if memory_answered and handler in ('knowledge_retrieval', 'factual_question'):
                    phi_answer = None
                    ctx = None
                    ctx_text = ""
                    if context_manager:
                        ctx_text = context_manager.build_prompt(
                            current_message=message,
                            phi_api="http://localhost:8080"
                        )
                    if stream:
                        # Streaming réel token-par-token
                        return Response(
                            stream_with_context(_phi_stream(message, ctx_text)),
                            mimetype='text/event-stream',
                            headers={
                                'Cache-Control': 'no-cache',
                                'X-Accel-Buffering': 'no',
                                'Connection': 'keep-alive',
                            }
                        )
                    else:
                        phi_answer = _phi_query(message, ctx_text)
                        if phi_answer:
                            if context_manager:
                                context_manager.add_turn("assistant", phi_answer)
                            return jsonify({
                                'response': phi_answer,
                                'source': 'phi-3.5-mini',
                                'method': 'renfort Phi pour question factuelle',
                                'engine': 'phi_renfort',
                                'code': 'PHI_FACTUAL_ANSWER',
                                'intent_frame': frame.to_dict() if frame else None,
                            }), 200
            
            # Détection intention spécialisation (fallback regex si pas de frame)
            if not frame and _is_specialize_intent(message):
                if context_manager:
                    context_manager.add_turn("assistant", f"Redirection vers spécialisation: {message}")
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
            context_data = _build_context(message, consensus_facts, best_holo_id, brain_svc)
            
            # Injecter le contexte conversationnel WaveContextManager
            if context_manager:
                context_data['context_prompt'] = context_manager.build_prompt(
                    current_message=message,
                    phi_api="http://localhost:8080"  # pour le résumé via Phi si besoin
                )
            
            # Génération réponse
            response = _generate_response(ai, brain_svc, message, context_data, mode, user_id)
            response['intent_frame'] = frame.to_dict() if frame else None
            response['fasttext_renfort_used'] = fasttext_renfort_used
            response['llm_renfort_used'] = llm_renfort_used

            # 🎛️ FINE-TUNING CONVERSATIONNEL : enregistrer le tour +
            # détecter le feedback implicite (re-question / follow-up).
            try:
                from ka_server.services.conversation_tuner import get_tuner
                tuner = get_tuner()
                tuner.register_turn(session_id, user_id, message,
                                    response.get('response', ''))
                implicit = tuner.detect_implicit(session_id, message)
                if implicit:
                    log.info(f"🎛️ Implicite: {implicit['type']} ({implicit['message']})")
            except Exception as e:
                log.debug(f"Tuner implicit failed: {e}")
            
            # Enregistrer la réponse dans le contexte
            if context_manager:
                context_manager.add_turn("assistant", response.get('response', ''))
            
            if stream:
                return Response(
                    stream_with_context(_generate_stream(ai, brain_svc, message, context_data, mode, user_id)),
                    mimetype='text/event-stream'
                )
            else:
                return jsonify(response)
                
        except Exception as e:
            log.error(f"Chat error: {e}")
            return jsonify({
                'error': str(e),
                'code': 'CHAT_ERROR',
                'intent_frame': frame.to_dict() if frame else None,
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
        """Historique de conversation + dernières réponses (pour le feedback UI)."""
        session_id = request.args.get('session_id', '')
        user_id = request.args.get('user_id', 'anonymous')
        limit = min(int(request.args.get('limit', 50)), 200)

        # Historique réel depuis le profil conversationnel (tuner)
        history = []
        try:
            from ka_server.services.conversation_tuner import get_tuner
            tuner = get_tuner()
            profile = tuner.get_profile(user_id)
            history = [
                {'question': h[1], 'fact': h[2], 'rating': h[3], 'ts': h[0]}
                for h in profile.data.get('dernieres_reponses', [])
            ][:limit]
        except Exception as e:
            log.debug(f"History from tuner failed: {e}")

        return jsonify({
            'session_id': session_id,
            'user_id': user_id,
            'history': history,
            'count': len(history),
        })
    
    @app.route('/api/chat/turn', methods=['POST'])
    def api_chat_turn():
        """Enregistre un tour de conversation (feedback implicite)."""
        data = request.get_json() or {}
        user_id = data.get('user_id', 'anonymous')
        session_id = data.get('session_id', '')
        question = data.get('question', '')
        response = data.get('response', '')
        latency_ms = data.get('latency_ms', 0)

        try:
            from ka_server.services.conversation_tuner import get_tuner
            tuner = get_tuner()
            tuner.register_turn(session_id, user_id, question, response, latency_ms)
            implicit = tuner.detect_implicit(session_id, question)
            return jsonify({
                'status': 'ok',
                'implicit': implicit,
            }), 200
        except Exception as e:
            log.debug(f"Turn tuner failed: {e}")
            return jsonify({'status': 'ok', 'implicit': None}), 200

    @app.route('/api/chat/feedback', methods=['POST'])
    def api_chat_feedback():
        """Feedback utilisateur sur la réponse → fine-tuning conversationnel."""
        data = request.get_json() or {}
        session_id = data.get('session_id', '')
        user_id = data.get('user_id', 'anonymous')
        rating = data.get('rating')  # 1-5 ou -1/1
        fact_text = data.get('fact_text', '')      # le fait concerné
        phrase_keys = data.get('phrase_keys', [])  # structures de phraséologie
        correction = data.get('correction', '')    # correction au format s|r|o
        question = data.get('question', '')

        log.info(f"Feedback: user={user_id} session={session_id} rating={rating} "
                 f"fact={fact_text[:40]}")

        try:
            from ka_server.services.conversation_tuner import get_tuner
            tuner = get_tuner()
            result = tuner.apply_feedback(
                user_id=user_id,
                rating=float(rating) if rating is not None else 3.0,
                fact_text=fact_text,
                phrase_keys=phrase_keys or [],
                correction=correction,
                session_id=session_id,
                question=question,
            )
            return jsonify({
                'status': 'ok',
                'message': 'Feedback appliqué au fine-tuning',
                'delta': result['delta'],
                'operations': result['operations'],
            }), 200
        except Exception as e:
            log.debug(f"Feedback tuner failed: {e}")
            return jsonify({'status': 'ok', 'message': 'Feedback enregistré'}), 200
    
    @app.route('/api/chat/debug/intent', methods=['POST'])
    def api_debug_intent():
        """Debug : comprendre un message sans exécuter le pipeline complet."""
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message vide', 'code': 'EMPTY_MESSAGE'}), 400
        
        try:
            from ka_server.services.prompt_comprehendor import PromptComprehendor
            pc = PromptComprehendor(use_semantic=False)
            frame = pc.comprehend(message)

            # Renfort FastText (info diagnostique)
            ft_info = None
            try:
                from ka_server.services.fasttext_classifier import get_classifier
                ft = get_classifier()
                if ft.is_ready:
                    ft_intent, ft_conf = ft.predict(message)
                    ft_info = {'intent': ft_intent, 'confidence': round(ft_conf, 4),
                               'backend': ft.info['backend']}
            except Exception:
                pass

            return jsonify({
                'message': message,
                'normalized': frame.normalized,
                'intent': frame.intent,
                'confidence': frame.confidence,
                'slots': frame.slots,
                'suggested_handler': frame.suggested_handler,
                'ambiguity': frame.ambiguity,
                'clarification_question': frame.clarification_question,
                'fasttext_renfort': ft_info,
                'all_scores': frame.all_scores,
                'stats': pc.stats(),
            }), 200
        except Exception as e:
            return jsonify({'error': str(e), 'code': 'INTENT_ERROR'}), 500
    
    @app.route('/api/chat/debug/reasoner', methods=['GET'])
    def api_debug_reasoner():
        """Debug : statistiques du WaveReasoner (policy, distillation)."""
        try:
            from ka_server.services.wave_reasoner import get_reasoner
            reasoner = get_reasoner()
            return jsonify(reasoner.stats()), 200
        except Exception as e:
            return jsonify({'error': str(e), 'code': 'REASONER_ERROR'}), 500


_STORAGE_PATTERNS = [
    r'compress(er|ion|é|eur)?',
    r'(mon |le )?(t[eéèêë]l[eéèêë]phone|appareil|portable) (plein|satur[eéèêë]|rempli|surcharg[eéèêë])',
    r'lib[eéèêë]re(r)? (de )?(la )?(l[\' ])?espace',
    r'lib[eéèêë]re mon (t[eéèêë]l[eéèêë]phone|appareil|portable|stockage)',
    r'espace (libre|disque|stockage|m[eéèêë]moire)',
    r'stockage (plein|satur[eéèêë]|insuffisant|presque plein)',
    r'nettoy(er|e|ons)? (le )?t[eéèêë]l[eéèêë]phone',
    r'nettoie (mon |le )?(stockage|t[eéèêë]l[eéèêë]phone|appareil)',
    r'faire (du )?m[eéèêë]nage',
    r'supprimer (des|les) fichiers',
    r'optimiser (le )?stockage',
    r'gagner (de )?l\'?espace|gb (en )?moins|(kg|gb|go) d\'?espace',
    r'espace sur mon (t[eéèêë]l[eéèêë]phone|appareil)',
    r'vider (la )?corbeille|corbeille (est )?pleine',
    # Analyse / vérification
    r'analys(er|e|é)? (mon |le |ma )?(t[eéèêë]l[eéèêë]phone|appareil|stockage|m[eéèêë]moire|donn[eéèêë]es?)',
    r'vérifi(er|e|é|ons)? (mon |le |ma )?(t[eéèêë]l[eéèêë]phone|appareil|stockage|m[eéèêë]moire)',
    r'check(er|e|é)? (mon |le )?(t[eéèêë]l[eéèêë]phone|appareil|stockage)',
    r'regard(er|e|ons)? (mon |le )?(t[eéèêë]l[eéèêë]phone|appareil|stockage)',
    r'(fais|faire) (un(e)? )?(analyse|vérification|scan|diagnostic) (de |du |de mon |de ma )?(t[eéèêë]l[eéèêë]phone|appareil|stockage)',
]


def _detect_storage_intent(message: str) -> bool:
    """Détecte si l'utilisateur parle de compression/libération d'espace."""
    msg_lower = message.lower().strip()
    for pattern in _STORAGE_PATTERNS:
        if re.search(pattern, msg_lower):
            return True
    return False


def _handle_storage_intent(message: str, services: dict) -> dict | None:
    """Gère une intention de compression — propose l'analyse du téléphone."""
    if not _detect_storage_intent(message):
        return None
    
    log.info(f"🧹 Storage intent detected: {message[:80]}")
    
    # Vérifier si le message demande explicitement l'action immédiate
    action_words = ['oui', 'vas-y', 'lance', 'analyse', 'scan', 'go', 'ok', 'd\'accord', 'lance l\'analyse']
    wants_action = any(w in message.lower() for w in action_words)
    
    if wants_action:
        # L'utilisateur accepte → direction le scan GhostCompressor
        return {
            'response': (
                "Super, je lance l'analyse de votre appareil ! 🔍\n\n"
                "Vous pouvez suivre la progression ici : "
                "je vais inspecter vos fichiers et vous proposer une compression "
                "intelligente qui préserve la qualité des photos et vidéos. "
                "Je vous tiens au courant dès que j'ai les résultats !"
            ),
            'engine': 'storage_saver',
            'method': 'analyse GhostCompressor',
            'code': 'STORAGE_SCAN_STARTED',
            'scan_url': '/api/compress/storage/scan',
            'activate_url': '/api/compress/storage/activate',
        }
    
    # Premier contact — proposition gracieuse avec 3 suggestions
    return {
        'response': (
            "Je vois que vous souhaitez libérer de l'espace sur votre téléphone ! 📱\n\n"
            "Je peux m'en occuper pour vous : je vais analyser votre appareil, "
            "compresser vos photos et vidéos sans perte de qualité visible, "
            "et vous faire gagner jusqu'à 80% d'espace — le tout intelligemment, "
            "en préservant vos souvenirs les plus précieux.\n\n"
            "**Voulez-vous que je lance l'analyse ?** 😊"
        ),
        'engine': 'storage_saver',
        'method': 'détection intention compression',
        'code': 'STORAGE_SAVER_OFFER',
        'suggestions': ['Oui, lance l\'analyse', 'Non merci', 'Explique moi comment ça marche'],
    }


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
    """Génère une réponse (non-streaming) avec contexte conversationnel."""
    response_text = ""
    source = "unknown"
    
    # Injecter le contexte WaveContextManager si disponible
    prompt_message = _build_context_prompt(message, context)
    
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
            result = ai.ask(prompt_message)
            response_text = result.get('answer', '') if isinstance(result, dict) else str(result)
            source = 'harmonic_ai'
        except Exception as e:
            log.warning(f"HarmonicAI failed: {e}")
            mode = 'brain'
    
    if mode == 'brain' and brain:
        try:
            response_text = brain.ask(prompt_message)
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
    
    # Refus inutile ou garbage → Phi renfort avec contexte conversationnel
    if (is_ref or is_garbage or not response_text or 
        'not connected' in response_text.lower() or 
        "i'm not" in response_text.lower()[:50]):
        log.info(f"⚠️ Mauvaise réponse détectée, tentative Phi-3.5-mini...")
        ctx_text = context.get('context_prompt', '')
        phi_answer = _phi_query(message, ctx_text)
        if phi_answer:
            response_text = phi_answer
            source = 'phi-3.5-mini'
            is_ref = False
            is_garbage = False
            log.info(f"✅ Phi-3.5-mini a répondu ({len(phi_answer)} chars)")
    
    # Style wave si dispo (WaveStylizer)
    styled = response_text
    try:
        from ka_server.services.wave_stylizer import WaveStylizer
        stylizer = WaveStylizer()
        if not is_ref and not is_garbage:
            styled = stylizer.render(response_text, style='warm')
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
    """Générateur de pseudo-streaming (une seule génération, plus de bug double appel)."""
    import json as _json
    import time as _time

    yield f"data: {_json.dumps({'type': 'start', 'message': message})}\n\n"

    # Génération unique (fix du bug)
    response = _generate_response(ai, brain, message, context, mode, user_id)
    text = response['response']
    
    if not text:
        yield f"data: {_json.dumps({'type': 'end', 'error': 'Réponse vide'})}\n\n"
        return
    
    # Streaming mot par mot pour l'effet temps réel
    # Découpage intelligent : phrases d'abord, puis mots longs
    chunks = []
    current = ""
    for char in text:
        current += char
        # Couper après un mot complet (espace) ou une ponctuation forte
        if char in (' ', '\n') and len(current) >= 15:
            chunks.append(current)
            current = ""
        elif char in ('.', '!', '?') and len(current) >= 10:
            chunks.append(current + ' ')
            current = ""
    if current:
        chunks.append(current)
    
    if not chunks:
        chunks = [text]
    
    # Envoyer les chunks avec délai progressif
    # Les premiers chunks arrivent vite, puis ralentissement naturel
    total_chars = len(text)
    for i, chunk in enumerate(chunks):
        yield f"data: {_json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
        
        # Délai adaptatif : proportionnel à la taille du chunk, mais
        # accéléré pour donner l'impression de rapidité
        delay = (len(chunk) / total_chars) * 1.5  # ~1.5s pour tout le texte
        delay = min(max(delay, 0.01), 0.08)  # entre 10ms et 80ms par chunk
        _time.sleep(delay)
    
    # Envoyer le signal de fin avec les métadonnées
    end_data = {k: v for k, v in response.items() if k not in ('response', 'raw_response')}
    end_data['type'] = 'end'
    yield f"data: {_json.dumps(end_data)}\n\n"


def _build_context_prompt(message: str, context: dict) -> str:
    """
    Construit le message enrichi avec le contexte conversationnel.
    Utilise WaveContextManager si une session_id est disponible.
    """
    # Si le contexte contient déjà un prompt formaté (WaveContextManager), l'utiliser
    if context.get('context_prompt'):
        return context['context_prompt']
    
    # Contexte holographique (consensus facts)
    if context.get('facts_context'):
        return f"{context['facts_context']}\n\nQuestion: {message}"
    
    return message


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