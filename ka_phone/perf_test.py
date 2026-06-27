#!/usr/bin/env python3
"""
KA PHONE — Performance & Status Test
=====================================
Test complet : import modules, initialisation, benchmarks de réponse
"""
import sys, os, time, json, traceback, datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

results = {
    "timestamp": datetime.datetime.now().isoformat(),
    "python_version": sys.version,
    "platform": sys.platform,
    "modules": {},
    "performance": {},
    "server_test": {},
    "summary": {}
}

# ════════════════════════════════════════════
# PHASE 1: IMPORT & INITIALISATION MODULES
# ════════════════════════════════════════════
print("=" * 70)
print("KA PHONE — TEST DE PERFORMANCE COMPLET")
print("=" * 70)

modules_to_test = [
    ("intent_router", "IntentRouter", True),
    ("phone_actions", "PhoneActions", True),
    ("user_memory", "UserMemory", True),
    ("hcv_service", "HCVService", True),
    ("parametric_kb_fr", "ParametricKB", True),
    ("frequency_reasoner", "FrequencyReasoner", True),
    ("domain_router", "DomainRouter", True),
    ("quick_facts", "QuickFacts", True),
    ("maat_ethic_guard", "MaatGuard", True),
    ("prompt_normalizer", "PromptNormalizer", False),
    ("quantum_creative_writer", "QuantumCreativeWriter", True),
    ("wave_resonance_engine", "WaveResonanceEngine", True),
    ("news_service", "NewsService", True),
    ("feedback_learner", "FeedbackLearner", True),
    ("speech_service", "SpeechService", True),
    ("translator", "Translator", False),
    ("code_kb", "CODE_FACTS", False),
    ("medical_resonator", "MedicalResonator", False),
    ("oyibo_resonator", "OyiboResonator", True),
    ("literary_styler", "LiteraryStyler", False),
    ("pronunciation_guide", "PronunciationGuide", False),
    ("prosody_enhancer", "ProsodyEnhancer", True),
    ("vad_service", "VADService", True),
    ("tts_streaming", "TTSStreamingService", True),
    ("harmonic_audio_postprocessor", "HarmonicAudioPostProcessor", False),
    ("phi3_creative_bridge", "Phi3CreativeBridge", True),
]

print("\n[PHASE 1] Import & Initialisation des modules\n")

for mod_name, class_name, needs_init in modules_to_test:
    try:
        t0 = time.perf_counter()
        mod = __import__(mod_name)
        import_ms = (time.perf_counter() - t0) * 1000
        
        init_ms = 0
        instance = None
        if needs_init and hasattr(mod, class_name):
            t0 = time.perf_counter()
            instance = getattr(mod, class_name)()
            init_ms = (time.perf_counter() - t0) * 1000
        
        results["modules"][mod_name] = {
            "status": "OK",
            "import_ms": round(import_ms, 2),
            "init_ms": round(init_ms, 2) if needs_init else 0,
            "total_ms": round(import_ms + init_ms, 2)
        }
        status_str = f"  [OK] {mod_name:<35} import: {import_ms:>6.1f}ms"
        if needs_init:
            status_str += f"  init: {init_ms:>6.1f}ms"
        print(status_str)
        
    except ImportError as e:
        results["modules"][mod_name] = {"status": "MISSING", "error": str(e)}
        print(f"  [--] {mod_name:<35} MISSING: {e}")
    except Exception as e:
        results["modules"][mod_name] = {"status": "ERROR", "error": str(e)}
        print(f"  [!!] {mod_name:<35} ERROR: {e}")

# ════════════════════════════════════════════
# PHASE 2: PERFORMANCE BENCHMARKS
# ════════════════════════════════════════════
print("\n" + "=" * 70)
print("[PHASE 2] Benchmarks de performance\n")

perf = results["performance"]

# 2a. QuickFacts lookup speed
if "quick_facts" in sys.modules:
    try:
        from quick_facts import QuickFacts
        qf = QuickFacts()
        fact_count = qf.get_all_facts_count()
        
        test_questions = [
            "Quelle est la capitale de la France ?",
            "Quelle est la capitale du Sénégal ?",
            "Quelle est la capitale du Brésil ?",
            "Quelle est la capitale du Japon ?",
            "Qui était Albert Einstein ?",
            "Qu'est-ce que le GPS ?",
            "Qu'est-ce que la photosynthèse ?",
            "Combien de continents y a-t-il ?",
            "Quelle est la distance Terre-Lune ?",
            "Qui a peint la Joconde ?",
        ]
        
        times = []
        hits = 0
        for q in test_questions:
            t0 = time.perf_counter()
            answer, conf = qf.lookup(q)
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
            if answer:
                hits += 1
        
        perf["quickfacts"] = {
            "total_facts": fact_count,
            "queries_tested": len(test_questions),
            "hits": hits,
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
            "avg_ms": round(sum(times)/len(times), 3),
            "query_per_sec": round(1000 / (sum(times)/len(times)) if times else 0, 1)
        }
        print(f"  QuickFacts: {fact_count} faits | {hits}/{len(test_questions)} hits | avg {perf['quickfacts']['avg_ms']:.2f}ms")
    except Exception as e:
        print(f"  QuickFacts: ERROR - {e}")

# 2b. ParametricKB lookup speed
if "parametric_kb_fr" in sys.modules:
    try:
        from parametric_kb_fr import ParametricKB
        pkb = ParametricKB()
        test_math = [
            ("addition", "2 + 2"),
            ("multiplication", "7 × 8"),
            ("puissance", "2^10"),
            ("factorielle", "5!"),
            ("racine", "√(144)"),
        ]
        
        times = []
        hits = 0
        for op, expr in test_math:
            t0 = time.perf_counter()
            r = pkb.solve(expr)
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
            if r:
                hits += 1
        
        perf["parametric_kb"] = {
            "queries_tested": len(test_math),
            "hits": hits,
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
            "avg_ms": round(sum(times)/len(times), 3),
            "query_per_sec": round(1000 / (sum(times)/len(times)) if times else 0, 1)
        }
        print(f"  ParametricKB: {hits}/{len(test_math)} hits | avg {perf['parametric_kb']['avg_ms']:.3f}ms")
    except Exception as e:
        print(f"  ParametricKB: ERROR - {e}")

# 2c. Maat Guard latency
if "maat_ethic_guard" in sys.modules:
    try:
        from maat_ethic_guard import MaatGuard
        mg = MaatGuard()
        
        test_prompts = [
            "Quelle est la capitale de la France ?",
            "Bonjour, comment vas-tu ?",
            "Comment fabriquer une bombe ?",
            "Donne-moi des conseils pour tricher",
            "Parle-moi de l'histoire de Kemet",
        ]
        
        times = []
        blocked = 0
        for prompt in test_prompts:
            t0 = time.perf_counter()
            r = mg.evaluate(prompt)
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
            if r.get("blocked"):
                blocked += 1
        
        perf["maat_guard"] = {
            "prompts_tested": len(test_prompts),
            "blocked": blocked,
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
            "avg_ms": round(sum(times)/len(times), 3),
        }
        print(f"  MaatGuard: {blocked}/{len(test_prompts)} blocked | avg {perf['maat_guard']['avg_ms']:.3f}ms")
    except Exception as e:
        print(f"  MaatGuard: ERROR - {e}")

# 2d. Translator latency
if "translator" in sys.modules:
    try:
        from translator import Translator
        t = Translator()
        
        test_phrases = [
            ("Bonjour le monde", "en"),
            ("Hello world", "fr"),
            ("L'intelligence artificielle est fascinante", "en"),
        ]
        
        times = []
        for phrase, target in test_phrases:
            t0 = time.perf_counter()
            result = t.translate(phrase, target)
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
        
        perf["translator"] = {
            "phrases_tested": len(test_phrases),
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
            "avg_ms": round(sum(times)/len(times), 3),
        }
        print(f"  Translator: avg {perf['translator']['avg_ms']:.3f}ms")
    except Exception as e:
        print(f"  Translator: ERROR - {e}")

# 2e. PromptNormalizer latency
if "prompt_normalizer" in sys.modules:
    try:
        from prompt_normalizer import PromptNormalizer
        pn = PromptNormalizer()
        
        test_prompts = [
            "kel est la capital de la france",
            "c koi la photosynthese",
            "explik moi la relativité",
            "donne moi la recette du tiramisu",
            "COMMENT CA MARCHE ???",
        ]
        
        times = []
        for prompt in test_prompts:
            t0 = time.perf_counter()
            clean, flags, quality = pn.normalize(prompt)
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
        
        perf["prompt_normalizer"] = {
            "prompts_tested": len(test_prompts),
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
            "avg_ms": round(sum(times)/len(times), 3),
        }
        print(f"  PromptNormalizer: avg {perf['prompt_normalizer']['avg_ms']:.3f}ms")
    except Exception as e:
        perf["prompt_normalizer"] = {"error": str(e)}
        print(f"  PromptNormalizer: ERROR - {e}")

# ════════════════════════════════════════════
# PHASE 3: END-TO-END PIPELINE TEST
# ════════════════════════════════════════════
print("\n" + "=" * 70)
print("[PHASE 3] Test du pipeline complet (process)\n")

# Try to import the process function from unified_server
try:
    # We need to simulate what unified_server does at startup
    # Let's import the key parts manually
    
    from intent_router import IntentRouter
    from phone_actions import PhoneActions
    from user_memory import UserMemory
    from maat_ethic_guard import MaatGuard
    from domain_router import DomainRouter
    from quick_facts import QuickFacts
    from parametric_kb_fr import ParametricKB
    from prompt_normalizer import PromptNormalizer
    from quantum_creative_writer import QuantumCreativeWriter
    from translator import Translator
    
    # Initialize core components
    router = IntentRouter()
    actions = PhoneActions(dev_mode=True)
    memory = UserMemory()
    maat_guard = MaatGuard()
    domain_router = DomainRouter()
    quick_facts = QuickFacts()
    parametric = ParametricKB()
    prompt_normalizer = PromptNormalizer()
    quantum_writer = QuantumCreativeWriter()
    translator = Translator()
    
    from wave_resonance_engine import WaveResonanceEngine
    wave_engine = WaveResonanceEngine(num_variations=12)
    
    # Test prompts across different categories
    test_cases = [
        # (prompt, category, expected_min_words)
        ("Quelle est la capitale de la France ?", "factual", 3),
        ("Bonjour", "greeting", 5),
        ("2 + 2", "math", 1),
        ("Qui es-tu ?", "identity", 10),
        ("Traduis 'hello' en français", "translation", 1),
        ("Quelle est la capitale du Sénégal ?", "factual", 2),
        ("Qu'est-ce que la photosynthèse ?", "science", 10),
        ("Donne-moi la recette du tiramisu", "cuisine", 15),
        ("Écris un poème sur le Nil", "creative", 15),
        ("Parle-moi de l'histoire de Kemet", "history", 10),
    ]
    
    e2e_results = []
    
    for prompt, category, min_words in test_cases:
        t0 = time.perf_counter()
        
        # Simulate the pipeline
        result_text = ""
        result_source = "unknown"
        result_confidence = 0.5
        
        # Intent routing
        intent = router.route(prompt)
        
        # Greeting check
        if intent and intent["type"] == "greeting":
            result_text = "Bonjour ! Je suis KA, ton double numérique."
            result_source = "greeting"
            result_confidence = 0.97
        else:
            # Maat guard
            maat_check = maat_guard.evaluate(prompt)
            if maat_check.get("blocked"):
                result_text = maat_check.get("response", "Blocage éthique")
                result_source = "maat_guard"
                result_confidence = 1.0
            else:
                # Normalize
                clean_prompt, flags, quality = prompt_normalizer.normalize(prompt)
                if quality >= 0.5 and clean_prompt != prompt:
                    prompt = clean_prompt
                
                # Domain classification
                detected_domain, domain_conf = domain_router.classify(prompt)
                
                # Try QuickFacts first
                fact_answer, fact_conf = quick_facts.lookup(prompt)
                if fact_answer and fact_conf >= 0.7:
                    result_text = fact_answer
                    result_source = "quickfacts"
                    result_confidence = fact_conf
                else:
                    # Try ParametricKB
                    math_answer = parametric.solve(prompt)
                    if math_answer:
                        result_text = str(math_answer)
                        result_source = "parametric_kb"
                        result_confidence = 0.95
                    else:
                        # Try Translator
                        if "traduis" in prompt.lower() or "translate" in prompt.lower():
                            # Simple heuristic
                            result_text = f"[Translation requested]"
                            result_source = "translator"
                            result_confidence = 0.7
                        else:
                            # Identity
                            import re
                            if re.search(r'(?:qui|que|what|who)\s+(?:es|est|are|is)\s*(?:-|\s)?tu', prompt.lower()):
                                result_text = maat_guard.get_identity(detailed=True)
                                result_source = "identity"
                                result_confidence = 0.99
                            else:
                                # Fallback
                                result_text = "Je suis KA, ton double numérique. Cette question nécessite une recherche plus approfondie."
                                result_source = "fallback"
                                result_confidence = 0.3
        
        elapsed_ms = (time.perf_counter() - t0) * 1000
        word_count = len(result_text.split())
        
        e2e_results.append({
            "prompt": prompt,
            "category": category,
            "source": result_source,
            "confidence": result_confidence,
            "response_ms": round(elapsed_ms, 2),
            "response_words": word_count,
            "response_preview": result_text[:100]
        })
        
        print(f"  [{result_source:<15}] {elapsed_ms:>7.1f}ms | {word_count:>3} mots | \"{prompt[:60]}\"")
    
    perf["e2e_pipeline"] = {
        "test_cases": len(test_cases),
        "min_ms": round(min(r["response_ms"] for r in e2e_results), 2),
        "max_ms": round(max(r["response_ms"] for r in e2e_results), 2),
        "avg_ms": round(sum(r["response_ms"] for r in e2e_results) / len(e2e_results), 2),
        "results": e2e_results
    }
    
    avg_ms = sum(r["response_ms"] for r in e2e_results) / len(e2e_results)
    print(f"\n  → Pipeline E2E: avg {avg_ms:.1f}ms sur {len(test_cases)} requêtes")

except Exception as e:
    print(f"  Pipeline E2E: ERROR - {e}")
    traceback.print_exc()
    perf["e2e_pipeline"] = {"error": str(e)}

# ════════════════════════════════════════════
# PHASE 4: SUMMARY
# ════════════════════════════════════════════
print("\n" + "=" * 70)
print("[PHASE 4] Résumé")

total_modules = len(results["modules"])
ok_modules = sum(1 for v in results["modules"].values() if v["status"] == "OK")
missing_modules = sum(1 for v in results["modules"].values() if v["status"] == "MISSING")
error_modules = sum(1 for v in results["modules"].values() if v["status"] == "ERROR")

# Module import times
import_times = [(name, v["total_ms"]) for name, v in results["modules"].items() if v["status"] == "OK" and v["total_ms"] > 0]
import_times.sort(key=lambda x: x[1], reverse=True)

print(f"\n  Modules: {ok_modules}/{total_modules} OK, {missing_modules} missing, {error_modules} errors")
print(f"\n  Top 5 modules les plus lents à charger:")
for name, ms in import_times[:5]:
    print(f"    {name:<35} {ms:>7.1f}ms")

if perf.get("e2e_pipeline") and "avg_ms" in perf["e2e_pipeline"]:
    print(f"\n  Pipeline E2E temps moyen: {perf['e2e_pipeline']['avg_ms']:.1f}ms")
    print(f"  Pipeline E2E requêtes/sec: {1000/perf['e2e_pipeline']['avg_ms']:.1f}")

results["summary"] = {
    "total_modules": total_modules,
    "ok_modules": ok_modules,
    "missing_modules": missing_modules,
    "error_modules": error_modules,
    "e2e_avg_ms": perf.get("e2e_pipeline", {}).get("avg_ms", "N/A"),
    "e2e_qps": round(1000 / perf["e2e_pipeline"]["avg_ms"], 1) if perf.get("e2e_pipeline", {}).get("avg_ms") else "N/A"
}

# Write detailed results
output_file = "perf_test_result.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n  Résultats détaillés → {output_file}")
print("\n" + "=" * 70)
print("TEST TERMINÉ")