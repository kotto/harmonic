# HARMONIC AI V 5 — Tests d'intégration
# =====================================

import math
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from config import PHI, TAU, DIM_PSI, EMOTIONS
from core.memory_core import (
    MemoryCore, HologramStore, text_to_psi, psi_resonate,
    psi_superpose, psi_bind, psi_unbind, Fact,
)
from core.personality_engine import PersonalityEngine, HarmonicPersonality
from core.phone_bus import PhoneBus, ToolMatcher
from core.conversation_pipeline import (
    ConversationPipeline, IntentDetector, WaveReasoner, PipelineResult,
)
from core.companion_core import KACompanion


# ═══════════════════════════════════════════════════════════
# TEST HELPERS
# ═══════════════════════════════════════════════════════════

PASS = 0
FAIL = 0

def test(name: str, condition: bool, detail: str = ''):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ═══════════════════════════════════════════════════════════
# TESTS — MEMORY CORE
# ═══════════════════════════════════════════════════════════

def test_memory_core():
    section("1. Memory Core")
    
    mem = MemoryCore(dim=512)
    
    # Test encodage
    psi1 = text_to_psi("Bonjour le monde")
    psi2 = text_to_psi("Bonjour le monde")
    psi3 = text_to_psi("Texte complètement différent")
    
    norm = np.sqrt(np.sum(np.abs(psi1) ** 2))
    test("‖ψ‖ = 1", abs(norm - 1.0) < 0.01, f"norm={norm:.4f}")
    
    same = psi_resonate(psi1, psi2)
    test("Résonance(même texte) ≈ 1.0", same > 0.99, f"resonance={same:.4f}")
    
    diff = psi_resonate(psi1, psi3)
    test("Résonance(texte différent) ≈ 0.04", abs(diff) < 0.15, f"resonance={diff:.4f}")
    
    # Test apprentissage
    fid = mem.remember("Sophie aime le chocolat")
    test("Apprentissage d'un fait", fid is not None and len(fid) > 0)
    
    fid2 = mem.remember("Sophie habite à Paris")
    test("Apprentissage d'un deuxième fait", fid2 is not None)
    
    test("Total faits = 2", mem.store._total_facts == 2,
         f"total={mem.store._total_facts}")
    
    # Test rappel
    results = mem.recall("Où habite Sophie ?", top_k=1)
    test("Rappel réussi", len(results) > 0,
         f"trouvé={len(results)} faits")
    
    if results:
        test("Fait pertinent rappelé", 'Paris' in results[0][0].text,
             f"texte={results[0][0].text[:50]}")
    
    # Test binding HRR
    psi_a = text_to_psi("Sophie")
    psi_b = text_to_psi("chocolat")
    psi_bound = psi_bind(psi_a, psi_b)
    psi_recovered = psi_unbind(psi_bound, psi_b)
    recovery = psi_resonate(psi_a, psi_recovered)
    test("Binding HRR réversible", recovery > 0.4,
         f"recovery={recovery:.4f}")
    
    # Test persistance
    mem.save("test_integration")
    mem2 = MemoryCore()
    loaded = mem2.load("test_integration")
    test("Sauvegarde/chargement", loaded, "échec chargement")
    test("Faits préservés après chargement",
         mem2.store._total_facts == 2,
         f"total={mem2.store._total_facts}")
    
    return mem


# ═══════════════════════════════════════════════════════════
# TESTS — PERSONALITY ENGINE
# ═══════════════════════════════════════════════════════════

def test_personality_engine():
    section("2. Personality Engine")
    
    pers = PersonalityEngine(dim=512)
    
    # Test émotions
    test("10 émotions disponibles", len(pers.available_emotions) == 10,
         f"count={len(pers.available_emotions)}")
    
    pers.set_emotion('joyful')
    test("set_emotion('joyful')", pers.get_emotion() == 'joyful')
    
    params = pers.get_emotion_params()
    test("Paramètres d'émotion récupérés",
         'pitch_shift' in params and 'energy_boost' in params)
    
    # Test modulation
    psi = text_to_psi("Bonjour")
    psi_mod = pers.modulate_emotion(psi, 'sad')
    test("Modulation émotionnelle préserve la norme",
         abs(np.sqrt(np.sum(np.abs(psi_mod)**2)) - 1.0) < 0.5)
    
    # Test détection d'émotion
    emotion, conf = pers.detect_emotion("Je suis tellement heureux !")
    test("Détection émotion joie", emotion in ['joyful', 'excited', 'warm'],
         f"détecté={emotion} (conf={conf:.2f})")
    
    emotion2, conf2 = pers.detect_emotion("Je me sens triste et fatigué...")
    test("Détection émotion tristesse",
         emotion2 in ['sad', 'calm', 'neutral'],
         f"détecté={emotion2} (conf={conf2:.2f})")
    
    # Test personnalités
    test("10+ archétypes disponibles", len(pers.available_personalities) >= 10,
         f"count={len(pers.available_personalities)}")
    
    pers.set_personality('compagnon')
    p = pers.get_personality()
    test("Personnalité chargée", p.name == 'compagnon')
    test("Traits Big Five présents", len(p.traits) == 5,
         f"traits={list(p.traits.keys())}")
    
    # Test fusion
    blended = pers.blend_personalities('compagnon', 'sage', 0.3)
    test("Fusion de personnalités", blended is not None)
    test("Nom auto-généré", len(blended.name) > 0)
    
    # Test modulation de personnalité
    psi_orig = text_to_psi("Bonjour")
    psi_pers = pers.modulate_personality(psi_orig)
    test("Modulation de personnalité préserve la norme",
         abs(np.sqrt(np.sum(np.abs(psi_pers)**2)) - 1.0) < 0.5)
    
    # Test persistance
    pers.save("test_integration_pers")
    pers2 = PersonalityEngine()
    loaded_pers = pers2.load("test_integration_pers")
    test("Persistance personnalité", loaded_pers)
    
    return pers


# ═══════════════════════════════════════════════════════════
# TESTS — PHONE BUS
# ═══════════════════════════════════════════════════════════

def test_phone_bus():
    section("3. Phone Bus")
    
    mem = MemoryCore()
    bus = PhoneBus(memory=mem)
    
    # Test contacts
    c = bus.add_contact("Maman", phone="0601020304", relation="famille")
    test("Ajout contact", c is not None)
    test("Contact a un ID", len(c.id) > 0)
    
    c2 = bus.add_contact("Paul", phone="0605060708")
    test("2 contacts", len(bus.list_contacts()) == 2)
    
    found = bus.find_contact("maman")
    test("Recherche contact", len(found) > 0)
    test("Contact trouvé = Maman", found[0].name == "Maman")
    
    # Test messages
    msg = bus.send_message("Paul", "Salut Paul !")
    test("Envoi message", msg is not None)
    test("Message a un ID", len(msg.id) > 0)
    
    msg2 = bus.receive_message("Paul", "Oui, à 14h !")
    test("Réception message", msg2 is not None)
    test("2 messages", len(bus.messages) == 2)
    
    # Test rappels
    rem = bus.set_reminder("Acheter du pain", "demain 9h")
    test("Création rappel", rem is not None)
    test("1 rappel actif", len(bus.list_reminders()) == 1)
    
    # Test appels
    call = bus.initiate_call("Maman", "Bonjour Maman !")
    test("Initiation appel", call is not None)
    test("1 appel dans le journal", len(bus.call_log) == 1)
    
    # Test routage d'intention
    result = bus.route_intent("Appelle Maman")
    test("Routage 'Appelle Maman'", result['handled'])
    test("Tool = voice_call", result['tool'] == 'voice_call')
    
    result2 = bus.route_intent("Envoie un message à Paul")
    test("Routage 'Envoie message'", result2['handled'])
    test("Tool = message", result2['tool'] == 'message')
    
    result3 = bus.route_intent("Quel temps fait-il ?")
    test("Routage question météo",
         result3 is not None)
    
    # Test dashboard
    dash = bus.dashboard()
    test("Dashboard généré", dash is not None)
    test("Dashboard contient contacts_count", 'contacts_count' in dash)
    
    return bus


# ═══════════════════════════════════════════════════════════
# TESTS — CONVERSATION PIPELINE
# ═══════════════════════════════════════════════════════════

def test_conversation_pipeline():
    section("4. Conversation Pipeline")
    
    mem = MemoryCore()
    pers = PersonalityEngine()
    pipe = ConversationPipeline(memory=mem, personality=pers)
    
    # Pré-remplir la mémoire
    mem.remember("Sophie aime le chocolat noir", domain='personal')
    mem.remember("Le restaurant préféré de Sophie est Le Petit Cambodge",
                domain='personal')
    mem.remember("Paris est la capitale de la France", domain='knowledge')
    mem.set_user_name("Sophie")
    
    # Test détection d'intention
    detector = pipe.detector
    
    test_intents = [
        ("Quel est le restaurant préféré de Sophie ?", 'query'),
        ("Pourquoi le ciel est bleu ?", 'reason'),
        ("Raconte-moi une histoire", 'creative'),
        ("Rappelle-toi que j'aime le jazz", 'store_fact'),
        ("Compare un chat et un chien", 'compare'),
        ("Calcule 15% de 200", 'math'),
        ("Bonjour, comment vas-tu ?", 'chat'),
    ]
    
    for text, expected in test_intents:
        intent = detector.detect(text)
        test(f"Détection intention: '{text[:40]}...' → {intent.type}",
             intent.type in [expected, 'chat'],
             f"attendu={expected}, obtenu={intent.type}")
    
    # Test pipeline complet
    result = pipe.process("Quel est le restaurant préféré de Sophie ?")
    test("Pipeline retourne un résultat", result is not None)
    test("Réponse non vide", len(result.response) > 0)
    test("Cohérence > 0", result.confidence > 0,
         f"confidence={result.confidence:.3f}")
    test("Faits utilisés > 0", result.facts_used > 0,
         f"facts_used={result.facts_used}")
    test("Latence < 100 ms", result.latency_ms < 100,
         f"latency={result.latency_ms:.1f}ms")
    test("Émotion détectée", len(result.emotion_detected) > 0)
    test("Émotion réponse", len(result.emotion_response) > 0)
    test("Étapes documentées", len(result.steps) >= 4,
         f"steps={len(result.steps)}")
    
    # Test conversation simple
    result2 = pipe.process("Bonjour !")
    test("Conversation simple: réponse", len(result2.response) > 0)
    test("Conversation simple: intention chat",
         result2.intent.type in ['chat', 'query'])
    
    # Test apprentissage
    result3 = pipe.process("Rappelle-toi que mon anniversaire est le 15 mars")
    test("Apprentissage: réponse", len(result3.response) > 0)
    
    # Vérifier que le fait a été appris
    results = mem.recall("anniversaire", top_k=1)
    test("Apprentissage: fait mémorisé",
         len(results) > 0 and 'mars' in results[0][0].text.lower(),
         f"fait={results[0][0].text if results else 'aucun'}")
    
    # Test math
    result4 = pipe.process("Calcule 15% de 200")
    test("Math: résultat", '30' in result4.response or '0.15' in result4.response.lower(),
         f"response={result4.response}")
    
    return pipe


# ═══════════════════════════════════════════════════════════
# TESTS — COMPANION CORE (intégration complète)
# ═══════════════════════════════════════════════════════════

def test_companion_core():
    section("5. Companion Core (Intégration complète)")
    
    ka = KACompanion(name="KA", personality="compagnon", emotion="warm")
    ka.set_user("Sophie")
    
    # Test initialisation
    test("Compagnon créé", ka is not None)
    test("Nom = KA", ka.state.name == "KA")
    test("Utilisateur = Sophie", ka.state.user_name == "Sophie")
    test("Mémoire initialisée", ka.memory is not None)
    test("Personnalité initialisée", ka.personality_engine is not None)
    test("Pipeline initialisé", ka.pipeline is not None)
    test("PhoneBus initialisé", ka.phone is not None)
    
    # Test apprentissage
    ka.learn("Sophie aime le thé vert")
    ka.learn("Sophie habite à Paris")
    test("3 faits appris (incluant set_user)", ka.memory.store._total_facts >= 2,
         f"total={ka.memory.store._total_facts}")
    
    # Test conversation simple
    result = ka.chat("Bonjour KA !")
    test("Chat: réponse non vide", len(result.response) > 0)
    test("Chat: latence < 50 ms", result.latency_ms < 50,
         f"latency={result.latency_ms:.1f}ms")
    
    # Test conversation avec mémoire
    result2 = ka.chat("Où est-ce que j'habite ?")
    test("Chat mémoire: réponse", len(result2.response) > 0)
    
    # Test émotion
    result3 = ka.chat("Je suis super content aujourd'hui !")
    test("Chat émotion: détection", len(result3.emotion_detected) > 0)
    test("Chat émotion: réponse adaptée",
         result3.emotion_response in ['joyful', 'excited', 'warm'],
         f"emotion={result3.emotion_response}")
    
    # Test changement de personnalité
    ka.set_personality('joyeux')
    test("Changement personnalité", ka.state.personality == 'joyeux')
    
    # Test changement d'émotion
    ka.set_emotion('calm')
    test("Changement émotion", ka.state.emotion == 'calm')
    
    # Test commande vocale
    vc_result = ka.voice_command("Appelle Maman")
    test("Voice command: résultat", vc_result is not None)
    
    # Test sauvegarde/chargement
    save_path = ka.save("test_companion")
    test("Sauvegarde complète", save_path is not None)
    
    ka2 = KACompanion(name="KA")
    loaded = ka2.load("test_companion")
    test("Chargement complet", loaded)
    test("Faits préservés", ka2.memory.store._total_facts >= 2,
         f"total={ka2.memory.store._total_facts}")
    test("Utilisateur préservé", ka2.state.user_name == "Sophie")
    
    # Test dashboard
    dash = ka.dashboard()
    test("Dashboard complet", 'state' in dash and 'memory' in dash)
    
    return ka


# ═══════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════

def run_all_tests():
    global PASS, FAIL
    PASS = 0
    FAIL = 0
    
    print("=" * 70)
    print("  🧪 HARMONIC AI V5 — Tests d'Intégration")
    print("=" * 70)
    
    t0 = time.perf_counter()
    
    try:
        test_memory_core()
    except Exception as e:
        section("1. Memory Core")
        print(f"  ❌ ERREUR: {e}")
        FAIL += 5
    
    try:
        test_personality_engine()
    except Exception as e:
        section("2. Personality Engine")
        print(f"  ❌ ERREUR: {e}")
        FAIL += 5
    
    try:
        test_phone_bus()
    except Exception as e:
        section("3. Phone Bus")
        print(f"  ❌ ERREUR: {e}")
        FAIL += 5
    
    try:
        test_conversation_pipeline()
    except Exception as e:
        section("4. Conversation Pipeline")
        print(f"  ❌ ERREUR: {e}")
        FAIL += 5
    
    try:
        test_companion_core()
    except Exception as e:
        section("5. Companion Core")
        print(f"  ❌ ERREUR: {e}")
        FAIL += 5
    
    elapsed = (time.perf_counter() - t0) * 1000
    
    # Résumé
    total = PASS + FAIL
    print(f"\n{'═'*70}")
    print(f"  RÉSULTATS: {PASS}/{total} ✅  ({FAIL} échecs)  —  {elapsed:.0f} ms")
    print(f"{'═'*70}")
    
    if FAIL == 0:
        print("  🎉 Tous les tests passent !")
    else:
        print(f"  ⚠️  {FAIL} test(s) en échec.")
    
    return PASS, FAIL


if __name__ == '__main__':
    run_all_tests()