#!/usr/bin/env python3
import sys, os, time, traceback, json

os.chdir(os.path.dirname(__file__))

with open("_test_result.txt", "w", encoding="utf-8") as log:
    log.write(f"=== Test Phi-3 Bridge ===\n")
    log.write(f"Time: {time.ctime()}\n\n")

    try:
        from phi3_creative_bridge import Phi3CreativeBridge

        log.write("[1] Import OK\n")
        log.write("[2] Initialisation du bridge (chargement du modele 2.4 Go sur CPU)...\n")
        log.flush()

        t0 = time.time()
        bridge = Phi3CreativeBridge(verbose=True)
        elapsed = time.time() - t0

        log.write(f"[3] Temps d'initialisation: {elapsed:.1f}s\n")
        log.write(f"[4] Modele disponible: {bridge.is_available()}\n")
        log.write(f"[5] Backend: {getattr(bridge, '_llm_backend', 'inconnu')}\n\n")
        log.flush()

        # Test generation creative
        log.write("[6] Test: generation poeme 'le Nil'...\n")
        log.flush()
        t0 = time.time()
        result = bridge.generate('poeme', sujet='le Nil', ton='lyrique', max_tokens=80)
        elapsed = time.time() - t0

        log.write(f"    Temps generation: {elapsed:.1f}s\n")
        log.write(f"    Source: {result['source']}\n")
        log.write(f"    Confiance: {result['confidence']}\n")
        log.write(f"    Verifie: {result.get('verified', 'N/A')}\n")
        log.write(f"    Hallucination: {result.get('hallucination_detected', 'N/A')}\n")
        log.write(f"    Texte:\n")
        for line in result['text'].split('\n')[:10]:
            log.write(f"      {line}\n")
        log.write(f"\n")
        log.flush()

        # Test generation histoire
        log.write("[7] Test: generation histoire 'un voyageur dans le desert'...\n")
        log.flush()
        result2 = bridge.generate('histoire', sujet='un voyageur dans le desert', ton='neutre', max_tokens=100)
        log.write(f"    Source: {result2['source']}\n")
        log.write(f"    Texte: {result2['text'][:250]}\n")
        log.write(f"\n")
        log.flush()

        # Test conversation
        log.write("[8] Test: conversation contextuelle...\n")
        log.flush()
        conv = bridge.generate_conversation(
            "Quelle est la capitale du Senegal ?",
            context=[
                {"role": "user", "content": "Parle-moi du Senegal"},
                {"role": "assistant", "content": "Le Senegal est un pays d'Afrique de l'Ouest."},
            ]
        )
        log.write(f"    Source: {conv['source']}\n")
        log.write(f"    Reponse: {conv.get('text', 'N/A')}\n")

        log.write(f"\n=== TEST TERMINE ===\n")

    except Exception as e:
        log.write(f"\nERREUR: {e}\n")
        traceback.print_exc(file=log)

print("Test lance. Resultat dans _test_result.txt")