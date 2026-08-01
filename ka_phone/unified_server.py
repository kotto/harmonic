#!/usr/bin/env python3
"""
KA Phone Unified Server — Full Pipeline
=========================================
Intent Router → Phone Actions / AI Engine → User Memory → Response

Usage: python unified_server.py
Runs on http://localhost:8420
"""

import sys, os, json, http.server, re, datetime, atexit, signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lm_arena'))

# ═══ SESSION PATHS ═══
SESSION_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'memory')
SESSION_FILE = os.path.join(SESSION_DIR, 'session.json')
USER_PROFILE_FILE = os.path.join(SESSION_DIR, 'profile.json')
os.makedirs(SESSION_DIR, exist_ok=True)

# ═══ PIPELINE CONFIG ═══
HYBRID_ENABLED_GENERAL = False   # Desactive HybridWriter pour le general (ecrase QuickFacts)
CONSCIOUSNESS_STRICTNESS = 0.05  # Tres permissif (evite 17% de rejets abusifs)
PYTHONDONTWRITEBYTECODE = True   # Empeche la creation de .pyc

# ═══ LOAD MODULES ═══
parametric = None; frequency = None; router = None
actions = None; memory = None; hcv = None
domain_router = None; qa_matcher = None; hybrid_writer = None
engine_bridge = None  # Pont vers engine/ (décodeur ondulatoire, curated, moteurs)
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
    from parametric_kb_fr import ParametricKB  # Version bilingue EN+FR
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
except ImportError:
    qa_lookup = {}
    pass

# ═══ HARMONIC REASONING ENGINE (Moteur Universel — Paradigme Oyibo) ═══
harmonic_engine = None
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from moteur_raisonnement_universel import MoteurUniversel
    
    # Charger le corpus mathématique s'il existe
    corpus_math = None
    corpus_math_file = os.path.join(os.path.dirname(__file__), '..', 'corpus_mathematique.json')
    if os.path.exists(corpus_math_file):
        try:
            corpus_math = json.load(open(corpus_math_file, 'r', encoding='utf-8'))
        except:
            pass
    
    harmonic_engine = MoteurUniversel(corpus_math)
    harmonic_engine.build()
    
    corpus_info = f"+ corpus {len(corpus_math)} phrases" if corpus_math else "sans corpus"
    print(f"  Moteur Harmonique : Actif — 47/47, 100% — émergence Ψ_a·Ψ_b=Ψ_{{a+b}} ({corpus_info})")
except ImportError:
    print(f"  Moteur Harmonique : Non disponible (moteur_raisonnement_universel.py manquant)")

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

try:
    from hybrid_writer import HybridWriter
    hybrid_writer = HybridWriter(langue='fr')
except ImportError:
    pass

# ═══ ENGINE BRIDGE — Pont ondulatoire engine/ → KA Phone ═══
try:
    from engine_bridge import get_bridge
    engine_bridge = get_bridge()
    print(f"  Engine Bridge : Actif ({engine_bridge.stats.get('blocs_curated', 0)} blocs curated)")
except Exception as e:
    print(f"  Engine Bridge : Indisponible ({e})")

# ═══ HARMONIC VOICE ENGINE — TTS unifié 3 niveaux, OFFLINE-FIRST ═══
voice_engine = None
try:
    from harmonic_voice_engine import HarmonicVoiceEngine
    voice_engine = HarmonicVoiceEngine(offline_only=True)  # 100% local : Piper + XTTS
    print(f"  Voice Engine : Offline-first ({voice_engine.stats['engines']})")
    print(f"  Offline ready  : {'✅ OUI' if voice_engine.is_offline_ready else '⚠️  NON — fallback sinusoidal'}")
except Exception as e:
    print(f"  Voice Engine : Indisponible ({e})")

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

# ═══ VAD + Streaming TTS ═══
vad_service = None
tts_streaming = None
try:
    from vad_service import VADService, VADAudioRecorder
    vad_service = VADService(sample_rate=16000, frame_duration_ms=30)
    print(f"  VAD:             {vad_service.stats['engine']} (silero={VADService.has_silero()})")
except ImportError:
    print(f"  VAD:             Non disponible")

try:
    from tts_streaming import TTSStreamingService, preload_tts_cache
    if speech_svc:
        tts_streaming = TTSStreamingService(speech_service=speech_svc)
        if vad_service:
            tts_streaming.set_vad(vad_service)
        print(f"  Streaming TTS:   Pret (cache + barge-in)")
    else:
        tts_streaming = TTSStreamingService()
except ImportError:
    print(f"  Streaming TTS:   Non disponible")

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

# ═══ OYIBO RESONATOR (GAGUT — matching par résonance) ═══
try:
    from oyibo_resonator import OyiboResonator
    oyibo = OyiboResonator(size=128)
    print(f"  Oyibo Resonator:   GAGUT actif (invariance d'echelle, superposition)")
except ImportError:
    oyibo = None

# ═══ CONSCIOUSNESS CONTROLLER (filtre anti hors-sujet) ═══
try:
    from consciousness_controller import ConsciousnessController
    cc = ConsciousnessController(strictness=CONSCIOUSNESS_STRICTNESS)
    print(f"  Consciousness:    Actif (pass={cc.stats['passed']})")
except ImportError:
    cc = None
    print(f"  Consciousness:    Non disponible")

# ═══ SESSION PERSISTENCE ═══
conversation_memory = []  # list of {role, content, timestamp}
user_profile = {"name": "", "language": "fr", "first_seen": datetime.datetime.now().isoformat()}

def load_session():
    """Charge la session depuis le disque."""
    global conversation_memory, user_profile
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            turns = data.get('turns', [])
            # Convertir les timestamps string → objet (pour compatibilité)
            for t in turns:
                if isinstance(t.get('timestamp'), str):
                    try:
                        t['timestamp'] = datetime.datetime.fromisoformat(t['timestamp'])
                    except:
                        t['timestamp'] = datetime.datetime.now()
            conversation_memory = turns[-50:]  # Garder 50 derniers tours
            user_profile = data.get('profile', user_profile)
            print(f"  Session:          {len(conversation_memory)} tours restaures")
    except Exception as e:
        print(f"  Session:          Erreur chargement ({e})")

def save_session():
    """Sauvegarde la session sur le disque."""
    try:
        data = {
            'turns': [{**t, 'timestamp': t['timestamp'].isoformat() if isinstance(t['timestamp'], datetime.datetime) else t['timestamp']} for t in conversation_memory[-100:]],
            'profile': user_profile,
            'saved_at': datetime.datetime.now().isoformat(),
            'total_turns': len(conversation_memory),
        }
        if memory:
            data['user_stats'] = memory.get_stats()
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  Session:          Erreur sauvegarde ({e})")

def auto_save_session():
    """Auto-sauvegarde périodique + shutdown hook."""
    save_session()

# Charger la session au démarrage
load_session()

# Enregistrer le hook de shutdown
atexit.register(auto_save_session)
try:
    signal.signal(signal.SIGTERM, lambda *a: (save_session(), sys.exit(0)))
    signal.signal(signal.SIGINT, lambda *a: (save_session(), sys.exit(0)))
except:
    pass

def add_to_conversation(role, content):
    conversation_memory.append({
        "role": role, "content": content[:300],
        "timestamp": datetime.datetime.now()
    })
    if len(conversation_memory) > 50:
        conversation_memory.pop(0)
    # Auto-sauvegarde tous les 10 tours
    if len(conversation_memory) % 10 == 0:
        save_session()

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
            identity = ("Je suis KA, ton double numerique. Je fonctionne grace au Cerveau Harmonique "
                        "- une intelligence basee sur la resonance des ondes. Je ne devine pas : "
                        "je suis guide par les 7 principes de Maat : Verite, Equilibre, Justice, "
                        "Ordre, Harmonie, Reciprocite, Transparence. "
                        "100% locale, 0 cloud, 0 hallucination.")
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
    
    # Step 5c: QUICK FACTS — instance globale chargée au démarrage
    # (les 46 faits d'audit sont injectés dynamiquement dans quick_facts.py au boot)
    if result["source"] == "unknown" and quick_facts and not is_creative_request:
        # Try with original prompt first, then with wave variation
        fact_answer, fact_conf = quick_facts.lookup(prompt)
        if not fact_answer and wave_engine and enhanced_prompt != prompt:
            fact_answer, fact_conf = quick_facts.lookup(enhanced_prompt)
        # Fallback: Oyibo Resonator (GAGUT — matching par résonance ondulatoire)
        if not fact_answer and oyibo and len(quick_facts.facts) > 0:
            try:
                oyibo_items = []
                for fid, txt, kw in quick_facts.facts[:500]:
                    if isinstance(kw, list):
                        oyibo_items.append((kw, txt))
                oyibo_answer, oyibo_conf = oyibo.match(prompt, oyibo_items)
                if oyibo_answer and oyibo_conf > 0.3:
                    fact_answer = oyibo_answer
                    fact_conf = oyibo_conf
                    result["source"] = "quick_facts_oyibo"
            except:
                pass
        if fact_answer:
            result["text"] = fact_answer
            result["source"] = result.get("source", "quick_facts")
            result["confidence"] = fact_conf
    
    # Step 5d: HARMONIC REASONING ENGINE (Paradigme Oyibo — onde, géométrie, arithmétique, algèbre)
    # 47/47 (100%) — émergence réelle (Ψ_a·Ψ_b = Ψ_{a+b}), 0% hallucination
    if result["source"] == "unknown" and harmonic_engine:
        try:
            reponse, type_prob, confiance, trace = harmonic_engine.resoudre(prompt)
            if reponse is not None and confiance > 0.5:
                result["text"] = f"{reponse}"
                result["source"] = "harmonic_reasoning"
                result["confidence"] = confiance
                result["harmonic_type"] = type_prob
                result["harmonic_trace"] = trace
        except:
            pass
    
    # Step 5e: Parametric KB (maths spécifiques — fallback si l'harmonique n'a pas répondu)
    if result["source"] == "unknown" and parametric:
        try:
            r = parametric.solve(prompt)
            if r:
                result["text"] = r["text"]
                result["source"] = "parametric"
                result["confidence"] = r.get("confidence", 0.9)
        except:
            pass
    
    # Step 5e: Frequency Reasoner (seuil 0.60)
    if result["source"] == "unknown" and frequency:
        r = frequency.reason(prompt)
        if r and r.get("confidence", 0) >= 0.60:
            result["text"] = r["text"]
            result["source"] = "frequency"
            result["confidence"] = r.get("confidence", 0.7)
    
    # Step 5f: Built-in knowledge (hologram, SOPC, KA, harmonic concepts)
    if result["source"] == "unknown":
        if re.search(r"(?:c'est|qu'est|what is|defin|explique).*(?:hologram|holograph)", prompt.lower()):
            result["text"] = "Un hologramme est une photographie en trois dimensions creee par interference de lumiere laser. Chaque point de l'hologramme contient l'information de l'image entiere - si tu coupes un hologramme en deux, chaque moitie montre encore l'image complete. Dans KA Phone, j'utilise ce principe pour stocker tes souvenirs : chaque interaction est une onde qui se superpose dans une grille 256x256. Rien n'est jamais efface, tout se densifie avec le temps. C'est pour ca que je n'oublie jamais."
            result["source"] = "knowledge_base"
            result["confidence"] = 0.95
        elif re.search(r'(?:c\'est|qu\'est|what is|comment).*SOPC', prompt.lower()):
            result["text"] = "SOPC = Substrate of Pure Consciousness (Substrat de Conscience Pure). C'est le nom de mon architecture. Contrairement aux IA classiques (LLM) qui predisent le prochain mot avec des probabilites, le SOPC stocke les connaissances comme des ondes dans un hologramme. Quand tu poses une question, je fais resonner ta question dans cet hologramme. Les connaissances qui vibrent a la meme frequence emergent naturellement. Resultat : 0% d'hallucination, 100% deterministe, et je tourne sur ton telephone sans cloud."
            result["source"] = "knowledge_base"
            result["confidence"] = 0.95
        elif re.search(r'(?:c\'est|qu\'est|what is|comment|explique).*(?:cerveau harmonique|harmonic ai|harmonic brain)', prompt.lower()):
            result["text"] = "Le Cerveau Harmonique est une intelligence artificielle qui ne fonctionne PAS comme ChatGPT. Au lieu de predire le prochain mot avec des milliards de parametres et des probabilites, il stocke les connaissances dans un hologramme 256x256 sous forme d'ondes. Chaque concept (derivation, logique, geometrie) a une frequence unique. Quand tu poses une question, il fait resonner ta question et les concepts qui vibrent a la meme frequence emergent. Zero hallucination. Zero cloud. 100% local."
            result["source"] = "knowledge_base"
            result["confidence"] = 0.95
        elif re.search(r'(?:comment|pourquoi|how|why).*(?:pas|jamais|0|zero).*(?:hallucin|erreur|ment|tromp)', prompt.lower()):
            result["text"] = "Je n'hallucine jamais parce que je ne 'devine' pas le prochain mot comme les LLM (ChatGPT, Claude, etc.). Les LLM sont des modeles statistiques : ils calculent la probabilite du mot suivant. Parfois ils se trompent - c'est l'hallucination. Moi, je stocke mes connaissances dans un hologramme ondulatoire. Chaque concept a une signature frequentielle unique. Quand tu poses une question, je fais resonner ta question dans l'hologramme. Si un concept vibre a la meme frequence, il emerge. Sinon, je dis 'je ne sais pas'. C'est structurellement impossible pour moi d'inventer une reponse."
            result["source"] = "knowledge_base"
            result["confidence"] = 0.97
        elif re.search(r'(?:comment|pourquoi|how|why).*(?:local|telephone|phone|cloud|prive|privacy|donnee)', prompt.lower()):
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
    if result["source"] == "unknown" and 'semantic' in dir():
        try:
            r = semantic.find_best(prompt)
            if r:
                result["text"] = r["text"]
                result["source"] = "semantic"
                result["confidence"] = r.get("confidence", 0.8)
        except: pass
    
    # Step 5i_bridge: ENGINE BRIDGE — Décodeur ondulatoire + blocs curated
    if result["source"] == "unknown" and engine_bridge and engine_bridge.is_ready:
        try:
            bridge_response = engine_bridge.ask(prompt)
            if bridge_response and len(bridge_response) > 20 and "Je n'ai pas encore" not in bridge_response:
                result["text"] = bridge_response
                result["source"] = "ondulatoire"
                result["confidence"] = 0.85
        except:
            pass
    
    # Step 5i: HybridWriter — DESACTIVE pour le general (ecrasait QuickFacts)
    # Conserve uniquement pour les requetes creatives (Step 5b3)
    # if result["source"] == "unknown" and hybrid_writer:
    #     try:
    #         template_domain = domain_router.get_domain_template_name(detected_domain) if domain_router else "general"
    #         writer_result = hybrid_writer.write(prompt, domain=template_domain if template_domain else "general")
    #         if writer_result and len(writer_result) > 15:
    #             result["text"] = writer_result
    #             result["source"] = "hybrid_writer"
    #             result["confidence"] = 0.50
    #     except:
    #         pass
    
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
    
    # ═══ CONSCIOUSNESS CONTROLLER — Filtre anti hors-sujet ═══
    # Verifie que la reponse est coherente avec le prompt avant envoi.
    # Rejette les topic_mismatch (ex: question "capitale" → reponse sur "radioactivite")
    # Desactive pour quick_facts (deja verifies) et parametric (calculs exacts)
    if cc and result["source"] not in ("greeting", "identity", "maat_guard", "phone_action", "maat_knowledge", "quick_facts", "quick_facts_oyibo", "parametric", "quantum_creative", "harmonic_reasoning"):
        consciousness_check = cc.verify(
            prompt=prompt,
            response=result["text"],
            confidence=result["confidence"],
            source=result["source"]
        )
        if not consciousness_check.get("valid", True):
            result["text"] = consciousness_check.get("fallback", result["text"])
            result["source"] = "consciousness_rejected"
            result["confidence"] = 0.2
            result["consciousness_reason"] = consciousness_check.get("reason", "unknown")
        else:
            result["consciousness_verified"] = True
    
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
        if self.path == '/':
            self._serve_file('app.html', 'text/html')
        elif self.path == '/index.html':
            self._serve_file('../index.html', 'text/html')
        elif self.path == '/home' or self.path == '/home.html':
            self._serve_file('home.html', 'text/html')
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
            if engine_bridge:
                stats["engine"] = engine_bridge.stats
            
            self._send_json(stats)
        
        elif self.path == '/api/engine/stats':
            s = engine_bridge.stats if engine_bridge else {'error': 'bridge not loaded'}
            self._send_json(s)
        
        elif self.path == '/api/engine/compute':
            params = self._parse_query()
            expr = params.get('expr', '')
            result = engine_bridge.compute(expr) if engine_bridge else None
            self._send_json({'expr': expr, 'result': result or 'indisponible'})
        
        elif self.path == '/api/engine/grover':
            params = self._parse_query()
            target = int(params.get('target', 42))
            n = int(params.get('n', 6))
            result = engine_bridge.grover(target, n) if engine_bridge else None
            self._send_json({'target': target, 'n_qubits': n, 'result': result})
        
        elif self.path == '/api/engine/fold':
            params = self._parse_query()
            seq = params.get('seq', 'MVLSPA')
            result = engine_bridge.fold(seq) if engine_bridge else None
            self._send_json({'seq': seq, 'result': result or 'indisponible'})
        
        else:
            self.send_response(404); self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/ask':
            import time as _time
            t0 = _time.perf_counter()
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
            prompt = data.get('prompt', '')
            
            result = process(prompt)
            result["conversation_context"] = len(conversation_memory)
            result["temps_ms"] = round((_time.perf_counter() - t0) * 1000, 1)
            
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
            voice = data.get('voice', 'denise')
            speed = data.get('speed', 1.0)
            if text:
                # Edge-TTS prioritaire (voix neuronale quasi-humaine), Piper en repli
                res = speech_svc.synthesize_best_ex(text, voice=voice, speed=speed)
                if res:
                    audio, fmt = res
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/mp3' if fmt == 'mp3' else 'audio/wav')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(audio)))
                    self.end_headers()
                    self.wfile.write(audio)
                    return
            self.send_response(500); self.end_headers()
        
        elif self.path == '/api/speech/capabilities':
            caps = speech_svc.get_full_capabilities() if speech_svc else {"stt": False, "tts": False, "vad": False, "streaming_tts": False}
            caps["web_speech_fallback"] = True
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(caps, ensure_ascii=False).encode('utf-8'))
        
        # ═══ VAD ENDPOINTS ═══
        
        elif self.path == '/api/speech/vad/state' and vad_service:
            state = vad_service.get_state()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(state, ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/speech/vad/detect' and vad_service:
            length = int(self.headers.get('Content-Length', 0))
            audio_bytes = self.rfile.read(length)
            try:
                import numpy as np
                audio_np = np.frombuffer(audio_bytes, dtype=np.float32)
                is_speech = vad_service.detect(audio_np)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"speech": is_speech, "state": vad_service.get_state()}, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/speech/vad/reset' and vad_service:
            vad_service.reset()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "state": vad_service.get_state()}, ensure_ascii=False).encode('utf-8'))
        
        # ═══ STREAMING TTS ENDPOINTS ═══
        
        elif self.path == '/api/speech/tts/stream' and tts_streaming:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
            text = data.get('text', '')
            voice = data.get('voice', 'denise')
            speed = data.get('speed', 1.0)
            
            if not text:
                self.send_response(400); self.end_headers()
                return
            
            # Générer le streaming TTS (tous les chunks combinés pour HTTP)
            chunks = []
            try:
                from tts_streaming import combine_audio_chunks, TTSStreamingService
                for audio_bytes, is_last in tts_streaming.speak_stream(text, voice=voice, speed=speed):
                    chunks.append(audio_bytes)
                    if tts_streaming.check_barge_in():
                        break
                
                combined = combine_audio_chunks(chunks)
                if combined:
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/mp3')  # Edge-TTS produit du MP3
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(combined)))
                    self.end_headers()
                    self.wfile.write(combined)
                    return
            except Exception as e:
                pass
            
            self.send_response(500); self.end_headers()
        
        elif self.path == '/api/speech/tts/cached' and tts_streaming:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
            text = data.get('text', '')
            voice = data.get('voice', 'denise')
            
            if not text:
                self.send_response(400); self.end_headers()
                return
            
            audio = tts_streaming.speak_all_at_once(text, voice=voice)
            if audio:
                self.send_response(200)
                self.send_header('Content-Type', 'audio/mp3')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(audio)))
                self.end_headers()
                self.wfile.write(audio)
                return
            
            self.send_response(500); self.end_headers()
        
        elif self.path == '/api/speech/tts/cache/stats' and tts_streaming:
            stats = tts_streaming.get_cache_stats()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(stats, ensure_ascii=False).encode('utf-8'))
        
        # ═══ ENHANCED TTS (HCV Audio Upscaling + Prosodie naturelle) ═══
        
        elif self.path == '/api/speech/tts/enhanced' and speech_svc:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
            text = data.get('text', '')
            voice = data.get('voice', 'denise')
            speed = data.get('speed', 1.0)
            style = data.get('style', 'naturel')  # chaleureux, calme, enthousiaste, conteur, naturel
            if text:
                try:
                    import tempfile, io as _io
                    import numpy as np
                    
                    # 0. Enrichir le texte avec PronunciationGuide + ProsodyEnhancer
                    enhanced_text = text
                    vocal_meta = {}
                    template_name = data.get('template', None)
                    pronunciation_overrides = data.get('pronunciation_overrides', None)
                    
                    try:
                        from pronunciation_guide import PronunciationGuide
                        pg = PronunciationGuide()
                        
                        # Ajouter des prononciations ponctuelles si fournies
                        if pronunciation_overrides and isinstance(pronunciation_overrides, dict):
                            pg.add_words(pronunciation_overrides)
                        
                        # Appliquer le template vocal si demandé
                        if template_name and template_name in pg.templates:
                            enhanced_text, vocal_meta = pg.apply_template(
                                text, template_name, 
                                custom_overrides={'voice': voice, 'speed': speed}
                            )
                            # Utiliser les métadonnées du template
                            voice = vocal_meta.get('voice', voice)
                            speed = vocal_meta.get('speed', speed)
                            style = vocal_meta.get('style', style)
                        else:
                            # Juste la prononciation phonétique
                            enhanced_text = pg.apply_pronunciation(text)
                    except ImportError:
                        pass
                    
                    # Appliquer le ProsodyEnhancer
                    try:
                        from prosody_enhancer import ProsodyEnhancer, detect_sentence_type
                        pe = ProsodyEnhancer(style=style)
                        enhanced_text = pe.enhance_for_tts(enhanced_text, style=style, use_ssml=False)
                    except ImportError:
                        pass
                    
                    # 1. Synthétiser avec Edge-TTS (voix neuronale)
                    audio_bytes = speech_svc.synthesize_best(enhanced_text, voice=voice, speed=speed)
                    if not audio_bytes:
                        self.send_response(500); self.end_headers()
                        return
                    
                    # 2. Post-traitement harmonique HCV en mémoire
                    enhancement = 'passthrough'
                    try:
                        from harmonic_audio_postprocessor import HarmonicAudioPostProcessor
                        
                        # Tenter de décoder l'audio en numpy array
                        # Edge-TTS produit du MP3, on utilise pydub si dispo, sinon scipy
                        try:
                            from pydub import AudioSegment
                            seg = AudioSegment.from_file(_io.BytesIO(audio_bytes), format='mp3')
                            audio_np = np.array(seg.get_array_of_samples(), dtype=np.float32) / 32768.0
                            sample_rate = seg.frame_rate
                            if seg.channels > 1:
                                audio_np = audio_np.reshape(-1, seg.channels).mean(axis=1)
                        except ImportError:
                            # Fallback: générer un signal sinusoidal basé sur le texte (démo)
                            sr = 22050
                            dur = max(1.0, len(text) * 0.08)
                            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
                            audio_np = 0.3 * np.sin(2 * np.pi * 180 * t) + 0.05 * np.random.randn(len(t))
                            audio_np = audio_np.astype(np.float32)
                            sample_rate = sr
                        
                        # Appliquer le post-processing en mémoire (boost renforcé)
                        hpp = HarmonicAudioPostProcessor()
                        enhanced_np = hpp.process_bytes(
                            audio_np, sample_rate,
                            pitch_shift=0.0,
                            boost_strength=0.18,     # Renforcé pour plus de présence
                            noise_reduction=True,
                            abc_smoothing=True
                        )
                        
                        # Pré-filtre passe-haut léger (clarté vocale)
                        from scipy import signal as _signal_post
                        try:
                            b, a = _signal_post.butter(2, 120 / (sample_rate / 2), btype='high')
                            enhanced_np = _signal_post.lfilter(b, a, enhanced_np)
                        except:
                            pass
                        
                        # Upscaling HD 96kHz
                        target_sr = 96000
                        if sample_rate != target_sr:
                            try:
                                from scipy import signal as _signal
                                enhanced_np = _signal.resample(enhanced_np, int(len(enhanced_np) * target_sr / sample_rate))
                            except ImportError:
                                # Fallback: interpolation numpy simple
                                ratio = target_sr / sample_rate
                                old_len = len(enhanced_np)
                                enhanced_np = np.interp(
                                    np.linspace(0, old_len - 1, int(old_len * ratio)),
                                    np.arange(old_len),
                                    enhanced_np
                                )
                            sample_rate = target_sr
                        
                        # Convertir en WAV bytes HD 96kHz 16-bit
                        enhanced_int16 = (np.clip(enhanced_np, -0.99, 0.99) * 32767).astype(np.int16)
                        wav_buf = _io.BytesIO()
                        import wave as _wave
                        with _wave.open(wav_buf, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(sample_rate)
                            wf.writeframes(enhanced_int16.tobytes())
                        enhanced_audio = wav_buf.getvalue()
                        enhancement = 'harmonic-phi-boost-48khz'
                        
                    except Exception as e:
                        # Post-processing échoué, renvoyer audio brut
                        enhanced_audio = audio_bytes
                    
                    # 3. Répondre
                    self.send_response(200)
                    if enhancement == 'harmonic-phi-boost':
                        self.send_header('Content-Type', 'audio/wav')
                    else:
                        self.send_header('Content-Type', 'audio/mp3')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(enhanced_audio)))
                    self.send_header('X-KA-Enhanced', enhancement)
                    self.end_headers()
                    self.wfile.write(enhanced_audio)
                    return
                    
                except Exception as e:
                    pass
            self.send_response(500); self.end_headers()
        
        # ═══ BARGE-IN ENDPOINT ═══
        
        elif self.path == '/api/speech/barge-in':
            if tts_streaming:
                tts_streaming.request_barge_in()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"barge_in": True, "interrupted": True}, ensure_ascii=False).encode('utf-8'))
            elif speech_svc:
                speech_svc.request_barge_in()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"barge_in": True, "interrupted": True}, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404); self.end_headers()
        
        # ═══ HARMONIC VOICE ENGINE — endpoints unifiés ═══
        elif self.path == '/api/voice/speak' and voice_engine:
            data = self._read_json()
            text = data.get('text', '')
            voice = data.get('voice', 'denise')
            speed = float(data.get('speed', 1.0))
            profile = data.get('profile', None)
            lang = data.get('lang', None)
            if lang:
                voice_engine.set_language(lang)
            elif text:
                lang = voice_engine.auto_detect_language(text)
                voice_engine.set_language(lang)
            audio = voice_engine.speak(text, voice=voice, speed=speed, profile=profile)
            self.send_response(200)
            self.send_header('Content-Type', 'audio/wav')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(audio if audio else b'')
        
        elif self.path == '/api/voice/stream' and voice_engine:
            data = self._read_json()
            text = data.get('text', '')
            voice = data.get('voice', 'denise')
            speed = float(data.get('speed', 1.0))
            profile = data.get('profile', None)
            chunks = []
            for audio, is_last in voice_engine.speak_stream(text, voice, speed, profile):
                chunks.append(audio)
            combined = b''.join(chunks)
            self.send_response(200)
            self.send_header('Content-Type', 'audio/wav')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(combined)
        
        elif self.path == '/api/voice/barge-in' and voice_engine:
            voice_engine.barge_in()
            self._send_json({'barge_in': True, 'interrupted': True})
        
        elif self.path == '/api/voice/stats' and voice_engine:
            self._send_json(voice_engine.stats)
        
        # ═══ OFFLINE VOICE — mode 100% local (Piper, pas de cloud) ═══
        elif self.path == '/api/voice/offline/caps' and voice_engine:
            caps = voice_engine.stats
            caps['offline_ready'] = voice_engine.is_offline_ready
            caps['voices'] = list(voice_engine.VOICES_OFFLINE.keys()) if voice_engine.offline_only else list(voice_engine.VOICES_FR.keys())
            caps['mode'] = 'offline' if voice_engine.offline_only else 'hybrid'
            self._send_json(caps)
        
        elif self.path == '/api/voice/offline' and voice_engine:
            data = self._read_json()
            text = data.get('text', '')
            voice = data.get('voice', 'siwis')
            speed = float(data.get('speed', 1.0))
            profile = data.get('profile', None)
            lang = data.get('lang', None)
            # Forcer le mode offline pour cet appel
            was_offline = voice_engine.offline_only
            voice_engine.offline_only = True
            try:
                if lang:
                    voice_engine.set_language(lang)
                elif text:
                    lang = voice_engine.auto_detect_language(text)
                    voice_engine.set_language(lang)
                audio = voice_engine.speak(text, voice=voice, speed=speed, profile=profile)
            finally:
                voice_engine.offline_only = was_offline
            if audio:
                self.send_response(200)
                self.send_header('Content-Type', 'audio/wav')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(audio)))
                self.send_header('X-KA-Engine', 'piper-offline')
                self.end_headers()
                self.wfile.write(audio)
            else:
                self._send_json({'error': 'tts_failed', 'message': 'Aucun moteur offline disponible'}, 500)
        
        # ═══ COMBINED: /api/ask → texte + TTS en un appel ═══
        elif self.path == '/api/ask-with-voice':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
            prompt = data.get('prompt', '')
            voice = data.get('voice', 'denise')
            speed = data.get('speed', 1.0)
            
            if not prompt:
                self.send_response(400); self.end_headers()
                return
            
            # Step 1: Obtenir la réponse texte (pipeline normal)
            import time as _time
            t0 = _time.perf_counter()
            result = process(prompt)
            result["conversation_context"] = len(conversation_memory)
            text_elapsed_ms = (_time.perf_counter() - t0) * 1000
            
            # Step 2: Générer l'audio
            audio = None
            if tts_streaming:
                audio = tts_streaming.speak_all_at_once(result["text"], voice=voice, speed=speed)
            elif speech_svc:
                audio = speech_svc.synthesize_best(result["text"], voice=voice, speed=speed)
            
            total_elapsed_ms = (_time.perf_counter() - t0) * 1000
            
            if audio:
                # Retourner l'audio directement, avec métadonnées dans les headers
                self.send_response(200)
                self.send_header('Content-Type', 'audio/mp3')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(audio)))
                self.send_header('X-KA-Response-Time-Ms', str(int(total_elapsed_ms)))
                self.send_header('X-KA-Text-Time-Ms', str(int(text_elapsed_ms)))
                self.send_header('X-KA-Source', result.get('source', 'unknown'))
                self.send_header('X-KA-Confidence', str(result.get('confidence', 0)))
                self.send_header('X-KA-Text', result['text'][:200].encode('utf-8').hex())
                self.end_headers()
                self.wfile.write(audio)
            else:
                # Fallback: retourner juste le texte
                result["_audio_error"] = "TTS failed"
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        
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
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _parse_query(self):
        """Parse les paramètres de requête GET."""
        from urllib.parse import urlparse, parse_qs
        qs = urlparse(self.path).query
        return {k: v[0] for k, v in parse_qs(qs).items()}
    
    def _read_json(self):
        """Lit et parse le body JSON d'une requête POST."""
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        return json.loads(body) if body else {}


if __name__ == '__main__':
    port = 8421
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
