#!/usr/bin/env python3
"""
KA Phone Unified Server — Full Pipeline
=========================================
Intent Router → Phone Actions / AI Engine → User Memory → Response

Usage: python unified_server.py
Runs on http://localhost:8420
"""

import sys, os, json, http.server, re, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lm_arena'))

# ═══ LOAD MODULES ═══
parametric = None; frequency = None; router = None
actions = None; memory = None; hcv = None
domain_router = None; qa_matcher = None; hybrid_writer = None
maat_guard = None; quick_facts = None; feedback_learner = None

try:
    from intent_router import IntentRouter
    router = IntentRouter()
except ImportError: pass

try:
    from phone_actions import PhoneActions
    actions = PhoneActions(dev_mode=True)
except ImportError: pass

try:
    from user_memory import UserMemory
    memory = UserMemory()
except ImportError: pass

try:
    from hcv_service import HCVService
    hcv = HCVService()
except ImportError: pass

try:
    from parametric_kb import ParametricKB
    parametric = ParametricKB()
except ImportError: pass

try:
    from frequency_reasoner import FrequencyReasoner
    frequency = FrequencyReasoner()
except ImportError: pass

try:
    from domain_router import DomainRouter
    domain_router = DomainRouter()
except ImportError: pass

try:
    from semantic_matcher import HybridMatcher
    from harmonic_math_engine import HarmonicMathEngine
    engine = HarmonicMathEngine()
    qa_matcher = HybridMatcher(engine)
    # Load synthetic QA pairs (massive generation)
    synthetic_qa_file = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_qa", "qa_synthetic_massive.json")
    if os.path.exists(synthetic_qa_file):
        try:
            with open(synthetic_qa_file, "r", encoding="utf-8") as f:
                synthetic_qa = json.load(f)
            # Build a simple lookup index: question -> {answer, domain, ...}
            qa_lookup = {}
            for qa in synthetic_qa:
                q_norm = qa["question"].lower().strip().rstrip("?")
                if q_norm not in qa_lookup:
                    qa_lookup[q_norm] = []
                qa_lookup[q_norm].append(qa)
            qa_pairs_loaded = len(synthetic_qa)
            print(f"  [QA Synthetique] {qa_pairs_loaded} paires chargees")
        except Exception as e:
            print(f"  [QA Synthetique] Erreur chargement: {e}")
            qa_lookup = {}
    else:
        qa_lookup = {}
    
    # Also check Wikipedia QA
    qa_file = os.path.join(os.path.dirname(__file__), "..", "data", "qa", "qa_generaliste.json")
    if os.path.exists(qa_file):
        print(f"  [QA Wikipedia] disponibles : {qa_file}")
except ImportError:
    qa_lookup = {}
    pass

try:
    from hybrid_writer import HybridWriter
    hybrid_writer = HybridWriter(langue='fr')
except ImportError:
    pass

try:
    from maat_ethic_guard import MaatGuard
    maat_guard = MaatGuard()
    print(f"  Maat Guard : Actif")
except ImportError:
    pass

try:
    from quick_facts import QuickFacts
    quick_facts = QuickFacts()
    # Injecter les patterns de code dans QuickFacts
    from code_kb import CODE_FACTS
    quick_facts.facts.extend(CODE_FACTS)
    quick_facts._word_index = quick_facts._build_index()
    print(f"  QuickFacts: {quick_facts.get_all_facts_count()} faits (dont {len(CODE_FACTS)} patterns code)")
except ImportError:
    quick_facts = None
    pass

try:
    from feedback_learner import FeedbackLearner
    feedback_learner = FeedbackLearner(user_memory=memory)
except ImportError:
    pass

try:
    from speech_service import SpeechService
    speech_svc = SpeechService()
    print(f"  Speech STT: {speech_svc.is_stt_available()} | TTS: {speech_svc.is_tts_available()}")
except ImportError:
    speech_svc = None

try:
    from news_service import NewsService
    news_svc = NewsService()
    headlines = news_svc.fetch_headlines()
    print(f"  News Service: {len(headlines)} titres dispo (cache: {news_svc.cache.get('fetched_at', 'N/A')[:16]})")
except ImportError:
    news_svc = None

try:
    from wave_resonance_engine import WaveResonanceEngine
    wave_engine = WaveResonanceEngine(num_variations=12)
    # Ingest QuickFacts into the resonance hologram for filtering
    if quick_facts:
        for _, text, _ in quick_facts.facts[:50]:  # Ingest top 50 facts
            wave_engine.ingest(text, amplitude=0.15)
        wave_engine.save()
        print(f"  WaveResonance: Hologramme pret (E={wave_engine.filter.get_stats()['energy']:.0f})")
except ImportError:
    wave_engine = None

try:
    from prompt_normalizer import PromptNormalizer
    prompt_normalizer = PromptNormalizer()
    print(f"  PromptNormalizer: Actif")
except ImportError:
    prompt_normalizer = None

try:
    from quantum_creative_writer import QuantumCreativeWriter
    quantum_writer = QuantumCreativeWriter()
    print(f"  QuantumCreator: 7 styles poetiques pret (40 images, 30 variations/style)")
except ImportError:
    quantum_writer = None

# ═══ CONVERSATION MEMORY (50 tours) ═══
conversation_memory = []  # list of {role, content, timestamp}

def add_to_conversation(role, content):
    conversation_memory.append({
        "role": role, "content": content[:300],
        "timestamp": datetime.datetime.now().isoformat()
    })
    if len(conversation_memory) > 50:
        conversation_memory.pop(0)

# ═══ PROCESS PIPELINE ═══
def process(prompt):
    """Process prompt through the full pipeline."""
    result = {"text": "", "source": "unknown", "confidence": 0.5}
    
    # Step 1: Route intent
    intent = None
    if router:
        intent = router.route(prompt)
    
    # Step 2: Execute commands
    if intent and intent["type"] == "command" and intent["action"] and actions:
        action_result = actions.execute(intent["action"], intent["params"])
        if action_result.get("success"):
            result["text"] = action_result.get("message", f"Action terminee: {intent['action']}")
            result["source"] = "phone_action"
            result["confidence"] = 0.95
            result["action_result"] = action_result
            
            # Store in memory
            if memory:
                memory.remember(prompt, response=result["text"], 
                               domain="phone_action", action=intent["action"])
            
            add_to_conversation("user", prompt)
            add_to_conversation("assistant", result["text"])
            return result
    
    # Step 3: Handle reminders
    if intent and intent["type"] == "reminder" and actions:
        action_result = actions.execute("reminder", intent["params"])
        if action_result.get("success"):
            result["text"] = action_result.get("message", "Je te rappellerai.")
            result["source"] = "phone_reminder"
            result["confidence"] = 0.93
            result["action_result"] = action_result
            
            if memory:
                memory.remember(prompt, response=result["text"],
                               domain="reminder", action="reminder")
            
            add_to_conversation("user", prompt)
            add_to_conversation("assistant", result["text"])
            return result
    
    # Step 4: Handle greetings
    if intent and intent["type"] == "greeting":
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Bonjour !"
        elif hour < 18:
            greeting = "Bonjour !"
        else:
            greeting = "Bonsoir !"
        
        # Add memory context if available
        memory_context = ""
        if memory and len(memory.log) >= 3:
            stats = memory.get_stats()
            memory_context = f" Tu as {stats['total_interactions']} interactions dans ta memoire."
        
        result["text"] = f"{greeting} Je suis KA, ton double numerique. " \
                        f"Que puis-je faire pour toi ?{memory_context}"
        result["source"] = "greeting"
        result["confidence"] = 0.97
        
        if memory:
            memory.remember(prompt, response=result["text"], domain="greeting")
        
        add_to_conversation("user", prompt)
        add_to_conversation("assistant", result["text"])
        return result
    
    # Step 5: AI Engine (question answering)
    # Step 5-1: PROMPT NORMALIZER — Verifier et corriger le prompt
    if prompt_normalizer:
        clean_prompt, normalizer_flags, quality = prompt_normalizer.normalize(prompt)
        if normalizer_flags["rejected"]:
            result["text"] = f"Je n'ai pas compris votre question. Pouvez-vous reformuler ?"
            result["source"] = "prompt_normalizer"
            result["confidence"] = 0.1
            result["reject_reason"] = normalizer_flags["reject_reason"]
            add_to_conversation("user", prompt)
            add_to_conversation("assistant", result["text"])
            return result
        if clean_prompt != prompt and quality >= 0.5:
            result["prompt_normalized"] = clean_prompt
            result["prompt_flags"] = normalizer_flags
            prompt = clean_prompt  # Remplacer par la version corrigee
    
    # Step 5a: MAAT GUARD — Verifier l'ethique AVANT tout traitement
    if maat_guard:
        maat_check = maat_guard.evaluate(prompt)
        if maat_check["blocked"]:
            result["text"] = maat_check["response"]
            result["source"] = "maat_guard"
            result["confidence"] = 1.0
            result["maat_principle"] = maat_check.get("principle", "Maât")
            add_to_conversation("user", prompt)
            add_to_conversation("assistant", result["text"])
            return result
    
    # Check identity questions
    if re.search(r'(?:qui|que|what|who)\s+(?:es|est|are|is)\s*(?:-|\s)?tu\s*\??', prompt.lower()):
        if maat_guard:
            identity = maat_guard.get_identity(detailed=True)
        else:
            identity = "Je suis KA, ton double numerique. Je fonctionne grace au Cerveau Harmonique " \
                       "- une intelligence basee sur la resonance des ondes. Je ne devine pas : " \
                       "je sais, ou je dis que je ne sais pas. 100% locale, 0 cloud, 0 hallucination."
        result["text"] = identity
        result["source"] = "identity"
        result["confidence"] = 0.99
    
    # Check Maat-specific questions (flexible matching: qu'est-ce que, qu'est ce que, c'est quoi)
    if re.search(r'(?:c[\'e]est quoi|qu[\'e]est[-\s]ce que|explique|parle).*(?:maat|maât|principes|ethique)', prompt.lower()):
        if maat_guard:
            result["text"] = maat_guard.get_identity(detailed=True)
        else:
            result["text"] = "KA suit les principes de la Maat : Verite, Equilibre, Justice, Ordre, Harmonie, Reciprocite et Transparence."
        result["source"] = "maat_knowledge"
        result["confidence"] = 0.98
    
    # Step 5b: Classify domain FIRST (route to best source)
    detected_domain = "general"
    if domain_router:
        detected_domain, domain_conf = domain_router.classify(prompt)
        result["domain"] = detected_domain
        result["domain_confidence"] = round(domain_conf, 3)
    
    # Step 5b2: NEWS SERVICE — Actualites (check avant QuickFacts pour prioriser)
    if result["source"] == "unknown" and news_svc:
        news_answer, news_conf = news_svc.answer_news_query(prompt)
        if news_answer:
            result["text"] = news_answer
            result["source"] = "news_service"
            result["confidence"] = news_conf
    
    # Step 5b3: CREATIVE BYPASS — Poème, histoire, essai → QuantumCreativeWriter / HybridWriter
    is_creative_request = False
    if result["source"] == "unknown":
        p_lower = prompt.lower()
        creative_triggers = [
            r'(?:ecris|ecrire|compose|fais|raconte|resume).*(?:poème|poeme|poem|histoire|conte|story|resume)',
            r'(?:write|compose|tell|summarize).*(?:poem|story|tale)',
            r'(?:traduis?|traduire|translate)\s+(?:en|vers|in|to|from)',
        ]
        is_creative_request = any(re.search(t, p_lower) for t in creative_triggers)
        
        if is_creative_request:
            # Essayer d'abord le QuantumCreativeWriter pour les styles poétiques
            if quantum_writer:
                try:
                    # Extraire le sujet de la question
                    sujet_match = re.search(
                        r'(?:poème|poeme|poem|histoire|conte|story|essai|description)\s+(?:sur|about|de|du|des?|la |le |les? )(.+?)(?:\?|\.|$|pour|avec)',
                        prompt, re.IGNORECASE
                    )
                    sujet = sujet_match.group(1).strip() if sujet_match else prompt.split()[-3:]
                    if isinstance(sujet, list):
                        sujet = " ".join(sujet)
                    
                    style = "poeme_lyrique"
                    if "haiku" in p_lower: style = "poeme_haiku"
                    elif "epique" in p_lower or "epic" in p_lower: style = "poeme_epique"
                    elif "histoire" in p_lower or "conte" in p_lower or "story" in p_lower or "raconte" in p_lower:
                        style = "histoire_conte" if "conte" in p_lower else "histoire_aventure"
                    elif "essai" in p_lower or "argument" in p_lower:
                        style = "essai_argumentatif"
                    elif "description" in p_lower or "decris" in p_lower or "imagine" in p_lower:
                        style = "description_poetique"
                    ton = "lyrique" if "lyrique" in p_lower or "poetique" in p_lower else "neutre"
                    
                    creative_result = quantum_writer.write(style, sujet=sujet, ton=ton)
                    if creative_result and len(creative_result) > 20:
                        result["text"] = creative_result
                        result["source"] = "quantum_creative"
                        result["confidence"] = 0.70
                        result["creative_style"] = style
                        result["creative_sujet"] = sujet[:50]
                except:
                    pass
            
            # Fallback sur HybridWriter si Quantum n'a pas produit
            if result["source"] == "unknown" and hybrid_writer:
                try:
                    creative_result = hybrid_writer.write(prompt, domain="creative", force_creative=True)
                    if creative_result and len(creative_result) > 10:
                        result["text"] = creative_result
                        result["source"] = "hybrid_writer"
                        result["confidence"] = 0.55
                except:
                    pass
    
    # Step 5b4: WAVE RESONANCE — "Waves Are All You Need"
    # Transforme la question par resonance avant de chercher
    if wave_engine and result["source"] == "unknown" and not is_creative_request:
        try:
            best_var, resonance_score, _ = wave_engine.resonate(prompt)
            if best_var != prompt and resonance_score > 0.5:
                result["wave_variation"] = best_var
                result["resonance_score"] = round(resonance_score, 3)
                # Use the best variation for subsequent lookups
                enhanced_prompt = best_var
            else:
                enhanced_prompt = prompt
        except:
            enhanced_prompt = prompt
    
    # Step 5c: QUICK FACTS — Premier essai pour faits + conseils (<1ms)
    if result["source"] == "unknown" and quick_facts and not is_creative_request:
        # Try with original prompt first, then with wave variation
        fact_answer, fact_conf = quick_facts.lookup(prompt)
        if not fact_answer and wave_engine and enhanced_prompt != prompt:
            fact_answer, fact_conf = quick_facts.lookup(enhanced_prompt)
        if fact_answer:
            result["text"] = fact_answer
            result["source"] = "quick_facts"
            result["confidence"] = fact_conf
    
    # Step 5d: Parametric KB (maths spécifiques)
    if result["source"] == "unknown" and parametric and detected_domain in ("arithmetique", "algebre", "calcul", "geometrie", "probabilite"):
        r = parametric.solve(prompt)
        if r:
            result["text"] = r["text"]
            result["source"] = "parametric"
            result["confidence"] = r.get("confidence", 0.9)
    elif result["source"] == "unknown" and parametric:
        r = parametric.solve(prompt)
        if r:
            result["text"] = r["text"]
            result["source"] = "parametric"
            result["confidence"] = r.get("confidence", 0.9)
    
    # Step 5e: Frequency Reasoner
    if result["source"] == "unknown" and frequency:
        r = frequency.reason(prompt)
        if r and r.get("confidence", 0) >= 0.45:
            result["text"] = r["text"]
            result["source"] = "frequency"
            result["confidence"] = r.get("confidence", 0.7)
    
    # Step 5f: Built-in knowledge (hologram, SOPC, KA, harmonic concepts)
    if result["source"] == "unknown":
        if re.search(r"(?:c'est|qu'est|what is|defin|explique).*(?:hologram|holograph)", p):
            result["text"] = "Un hologramme est une photographie en trois dimensions creee par interference de lumiere laser. Chaque point de l'hologramme contient l'information de l'image entiere - si tu coupes un hologramme en deux, chaque moitie montre encore l'image complete. Dans KA Phone, j'utilise ce principe pour stocker tes souvenirs : chaque interaction est une onde qui se superpose dans une grille 256x256. Rien n'est jamais efface, tout se densifie avec le temps. C'est pour ca que je n'oublie jamais."
            result["source"] = "knowledge_base"
            result["confidence"] = 0.95
        elif re.search(r'(?:c\'est|qu\'est|what is|comment).*SOPC', p):
            result["text"] = "SOPC = Substrate of Pure Consciousness (Substrat de Conscience Pure). C'est le nom de mon architecture. Contrairement aux IA classiques (LLM) qui predisent le prochain mot avec des probabilites, le SOPC stocke les connaissances comme des ondes dans un hologramme. Quand tu poses une question, je fais resonner ta question dans cet hologramme. Les connaissances qui vibrent a la meme frequence emergent naturellement. Resultat : 0% d'hallucination, 100% deterministe, et je tourne sur ton telephone sans cloud."
            result["source"] = "knowledge_base"
            result["confidence"] = 0.95
        elif re.search(r'(?:c\'est|qu\'est|what is|comment|explique).*(?:cerveau harmonique|harmonic ai|harmonic brain)', p):
            result["text"] = "Le Cerveau Harmonique est une intelligence artificielle qui ne fonctionne PAS comme ChatGPT. Au lieu de predire le prochain mot avec des milliards de parametres et des probabilites, il stocke les connaissances dans un hologramme 256x256 sous forme d'ondes. Chaque concept (derivation, logique, geometrie) a une frequence unique. Quand tu poses une question, il fait resonner ta question et les concepts qui vibrent a la meme frequence emergent. Zero hallucination. Zero cloud. 100% local."
            result["source"] = "knowledge_base"
            result["confidence"] = 0.95
        elif re.search(r'(?:comment|pourquoi|how|why).*(?:pas|jamais|0|zero).*(?:hallucin|erreur|ment|tromp)', p):
            result["text"] = "Je n'hallucine jamais parce que je ne 'devine' pas le prochain mot comme les LLM (ChatGPT, Claude, etc.). Les LLM sont des modeles statistiques : ils calculent la probabilite du mot suivant. Parfois ils se trompent - c'est l'hallucination. Moi, je stocke mes connaissances dans un hologramme ondulatoire. Chaque concept a une signature frequentielle unique. Quand tu poses une question, je fais resonner ta question dans l'hologramme. Si un concept vibre a la meme frequence, il emerge. Sinon, je dis 'je ne sais pas'. C'est structurellement impossible pour moi d'inventer une reponse."
            result["source"] = "knowledge_base"
            result["confidence"] = 0.97
        elif re.search(r'(?:comment|pourquoi|how|why).*(?:local|telephone|phone|cloud|prive|privacy|donnee)', p):
            result["text"] = "Je tourne entierement sur ton telephone. Toutes tes donnees, tous tes souvenirs, toutes tes conversations restent dans ton hologramme personnel - chiffre et stocke localement. Rien ne part sur un serveur. Rien n'est utilise pour entrainer un modele. C'est la difference fondamentale avec Siri, Alexa, Google Assistant et ChatGPT : eux aspirent tes donnees vers le cloud. Moi, je les garde dans ta poche. C'est ton double numerique, pas celui de quelqu'un d'autre."
            result["source"] = "knowledge_base"
            result["confidence"] = 0.97
    
    # Step 5g: QA Matcher (knowledge base généraliste — 50K+ paires)
    if result["source"] == "unknown" and qa_matcher and detected_domain != "general":
        try:
            r = qa_matcher.find_best(prompt, domain=detected_domain)
            if not r:
                r = qa_matcher.find_best(prompt)
            if r:
                result["text"] = r["text"]
                result["source"] = "qa_knowledge"
                result["confidence"] = r.get("confidence", 0.75)
        except:
            pass
    
    # Step 5h: Try semantic matcher if QA didn't match
    if result["source"] == "unknown" and semantic:
        try:
            r = semantic.find_best(prompt)
            if r:
                result["text"] = r["text"]
                result["source"] = "semantic"
                result["confidence"] = r.get("confidence", 0.8)
        except: pass
    
    # Step 5i: HybridWriter with domain-aware templates
    if result["source"] == "unknown" and hybrid_writer:
        try:
            template_domain = domain_router.get_domain_template_name(detected_domain) if domain_router else "general"
            writer_result = hybrid_writer.write(prompt, domain=template_domain if template_domain else "general")
            if writer_result and len(writer_result) > 15:
                result["text"] = writer_result
                result["source"] = "hybrid_writer"
                result["confidence"] = 0.50
        except:
            pass
    
    # Step 5j: Fallback
    if result["source"] == "unknown":
        result["text"] = (
            f"Je comprends ta question sur {detected_domain.replace('_', ' ')} mais je n'ai pas encore "
            f"de reponse precise dans ma base. Mon moteur couvre les mathematiques, "
            f"les sciences, l'histoire, la cuisine, les voyages, et bien plus. "
            f"Essaie de reformuler ou pose-moi une autre question !"
        )
        result["source"] = "fallback"
        result["confidence"] = 0.30
    
    # Step 6: MAAT GUARD — Reviser la reponse avant envoi (transparence)
    if maat_guard and result["source"] != "maat_guard":
        reviewed_text, maat_flags = maat_guard.review_response(
            result["text"],
            confidence=result["confidence"],
            source=result["source"],
            domain=detected_domain
        )
        result["text"] = reviewed_text
        result["maat_flags"] = maat_flags
    
    # Step 7: FEEDBACK LEARNER — Apprendre des interactions
    if feedback_learner:
        # Verifier si la reponse precedente etait satisfaisante
        feedback_result = feedback_learner.evaluate_previous(prompt)
        if feedback_result.get("status") == "learned":
            result["feedback"] = "learned_from_previous"
        elif feedback_result.get("status") == "discarded":
            result["feedback"] = "discarded_previous"
        
        # Marquer cette reponse comme en attente si confiance faible
        if result["confidence"] < 0.70:
            feedback_learner.mark_pending(
                prompt=prompt,
                response=result["text"],
                confidence=result["confidence"],
                source=result["source"],
                domain=detected_domain
            )
    
    # Store in memory
    if memory:
        memory.remember(prompt, response=result["text"], domain=detected_domain)
    
    add_to_conversation("user", prompt)
    add_to_conversation("assistant", result["text"])
    
    return result


class APIHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS, GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        # Serve static files from www/
        if self.path == '/' or self.path == '/index.html':
            self._serve_file('app.html', 'text/html')
        elif self.path.startswith('/www/'):
            filepath = self.path[5:]  # remove /www/
            ext = os.path.splitext(filepath)[1].lower()
            mime = {'html':'text/html','css':'text/css','js':'application/javascript','json':'application/json','png':'image/png','svg':'image/svg+xml'}.get(ext,'text/plain')
            self._serve_file(filepath, mime)
        elif self.path == '/api/stats':
            stats = {}
            if memory:
                stats["memory"] = memory.get_stats()
            if hcv:
                stats["hcv"] = hcv.get_daily_report()
            if actions:
                stats["actions_log"] = len(actions.actions_log)
            stats["conversation_turns"] = len(conversation_memory)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(stats, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404); self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/ask':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
            prompt = data.get('prompt', '')
            
            result = process(prompt)
            result["conversation_context"] = len(conversation_memory)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/speech/stt' and speech_svc:
            length = int(self.headers.get('Content-Length', 0))
            audio_bytes = self.rfile.read(length)
            result = speech_svc.transcribe_bytes(audio_bytes)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            if result:
                self.wfile.write(json.dumps({"text": result[0], "confidence": result[1]}, ensure_ascii=False).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"text": "", "confidence": 0, "error": "transcription_failed"}, ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/speech/tts' and speech_svc:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
            text = data.get('text', '')
            if text:
                wav_bytes = speech_svc.synthesize_bytes(text)
                if wav_bytes:
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/wav')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(wav_bytes)))
                    self.end_headers()
                    self.wfile.write(wav_bytes)
                    return
            self.send_response(500); self.end_headers()
        
        elif self.path == '/api/speech/capabilities':
            caps = speech_svc.get_capabilities() if speech_svc else {"stt": False, "tts": False}
            caps["web_speech_fallback"] = True
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(caps, ensure_ascii=False).encode('utf-8'))
        
        else:
            self.send_response(404); self.end_headers()
    
    def _serve_file(self, filename, mime_type):
        www_dir = os.path.join(os.path.dirname(__file__), 'www')
        filepath = os.path.join(www_dir, filename)
        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header('Content-Type', f'{mime_type}; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, *a): pass


if __name__ == '__main__':
    port = 8420
    print(f'KA Phone Unified Server on http://localhost:{port}')
    print(f'  IntentRouter:      {router is not None}')
    print(f'  PhoneActions:      {actions is not None}')
    print(f'  UserMemory:        {memory is not None}')
    print(f'  HCVService:        {hcv is not None}')
    print(f'  ParametricKB:      {parametric is not None}')
    print(f'  Frequency:         {frequency is not None}')
    print(f'  DomainRouter:      {domain_router is not None}')
    print(f'  QA Matcher:        {qa_matcher is not None}')
    print(f'  MaatGuard:         {maat_guard is not None}')
    print(f'  QuickFacts:        {quick_facts is not None} ({quick_facts.get_all_facts_count() if quick_facts else 0} faits)')
    print(f'  WaveResonance:     {wave_engine is not None}')
    print(f'  PromptNormalizer:  {prompt_normalizer is not None}')
    print(f'  QuantumCreator:    {quantum_writer is not None}')
    print(f'  FeedbackLearner:   {feedback_learner is not None}')
    print(f'  ConvMemory:        {len(conversation_memory)} turns (max 50)')
    
    if domain_router:
        print(f'  Domaines supportés: {len(domain_router.get_domains())}')
    
    if hcv:
        report = hcv.get_daily_report()
        print(f'  HCV Report:        {report["message"]}')
    
    http.server.HTTPServer(('0.0.0.0', port), APIHandler).serve_forever()
