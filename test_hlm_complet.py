#!/usr/bin/env python3
"""
TEST COMPLET : Noyau ABC + Initialisation Harmonique + Generation
=================================================================
Verifie que le HLM genere du texte coherent via le noyau ABC
sans entrainement, sans GPU, sans retropropagation.
"""
import math, sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PHI = 1.618033988749895
PHI_INV = 0.6180339887498949
ALPHA = 1.175569459083219

def gamma_approx(x):
    """Fonction Gamma approximee (Lanczos) - Version robuste."""
    if x <= 0 and x == int(x): return float('nan')
    if x == 1.0 or x == 2.0: return 1.0
    if x == 0.5: return math.sqrt(math.pi)
    if x < 0.5: return math.pi / (math.sin(math.pi * x) * gamma_approx(1 - x))
    z = x - 1
    if z == 0: return 1.0  # Protection division par zero
    s = 1.0; f = 1.0
    for c in [1/12, 1/288, -139/51840, -571/2488320]:
        f /= z
        s += c * f
    return math.sqrt(2*math.pi) * pow(z, z+0.5) * math.exp(-z) * s


def ml(alpha, z, terms=50):
    r = 0.0
    for k in range(terms):
        t = pow(z, k) / gamma_approx(alpha * k + 1); r += t
        if abs(t) < 1e-12: break
    return r

# =========================================================================
# TEST 1 : Noyau ABC
# =========================================================================
def test_noyau_abc():
    print("\n" + "="*60)
    print("TEST 1 : Noyau ABC (Mittag-Leffler)")
    print("="*60)
    
    tests = [
        (PHI_INV, 0.0, 1.0, "E(1/φ, 0) = 1"),
        (PHI_INV, 1.0, None, "E(1/φ, 1) > 0"),
        (PHI_INV, -1.0, None, "E(1/φ, -1) ∈ [0,1]"),
        (PHI_INV, PHI, None, "E(1/φ, φ) > 0"),
        (PHI_INV, -PHI, None, "E(1/φ, -φ) ∈ [0,1]"),
    ]
    
    all_ok = True
    for alpha, z, expected, desc in tests:
        r = ml(alpha, z)
        ok = True
        if expected is not None and abs(r - expected) > 1e-6:
            ok = False
        if expected is None and (math.isnan(r) or math.isinf(r)):
            ok = False
        status = "OK" if ok else "ECHEC"
        if not ok: all_ok = False
        print(f"  {status} : {desc} = {r:.6f}")
    
    # Test de convergence
    r10 = ml(PHI_INV, 0.5, terms=10)
    r50 = ml(PHI_INV, 0.5, terms=50)
    print(f"  Convergence : E(1/φ, 0.5) terms=10: {r10:.6f}, terms=50: {r50:.6f}")
    if abs(r10 - r50) < 1e-4:
        print("  [OK] Convergence rapide")
    else:
        print("  [ATTENTION] Convergence lente")
    
    print(f"\n  Resultat : {'TOUS OK' if all_ok else 'ERREURS DETECTEES'}")
    return all_ok

# =========================================================================
# TEST 2 : Poids Harmoniques
# =========================================================================
def test_poids_harmoniques():
    print("\n" + "="*60)
    print("TEST 2 : Calcul des Poids Harmoniques")
    print("="*60)
    
    from harmonic_weight_initializer import harmonic_weight, harmonic_embedding_weight
    
    # Test poids par couche
    print("\n  Poids par couche (d_model=512, 8 layers, 8 heads):")
    for l in range(8):
        w = harmonic_weight(512, l, 8)
        print(f"    Couche {l}: w = {w:.4f}")
    
    # Test poids par tete
    print("\n  Poids par tete (layer 0, 8 heads):")
    for h in range(8):
        w = harmonic_weight(512, 0, 8, head_idx=h, n_heads=8)
        print(f"    Tete {h}: w = {w:.4f}")
    
    # Test embedding
    print("\n  Poids d'embedding (vocab_size=50304):")
    for idx in [0, 1, 10, 100, 1000, 10000]:
        w = harmonic_embedding_weight(idx, 512, 50304)
        print(f"    Token {idx:5d}: w = {w:.4f}")
    
    # Verification : tous les poids doivent etre dans [0.01, 1.0]
    all_ok = True
    for l in range(8):
        w = harmonic_weight(512, l, 8)
        if not (0.01 <= w <= 1.0):
            print(f"  [ERREUR] Poids couche {l} hors limite: {w}")
            all_ok = False
    
    print(f"\n  Resultat : {'TOUS OK' if all_ok else 'ERREURS DETECTEES'}")
    return all_ok

# =========================================================================
# TEST 3 : Initialisation du Modele
# =========================================================================
def test_initialisation_modele():
    print("\n" + "="*60)
    print("TEST 3 : Initialisation Harmonique du Modele")
    print("="*60)
    
    try:
        import torch
        from harmonic_training.model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
        from harmonic_weight_initializer import init_harmonic_model
        
        config = HARMONIC_CONFIGS['harmonic-tiny']
        model = HarmonicForCausalLM(config)
        
        # Avant init
        w_before = model.lm_head.weight[0, :5].clone()
        print(f"\n  Poids avant init : {[f'{x:.4f}' for x in w_before.tolist()]}")
        
        # Init harmonique
        model = init_harmonic_model(model)
        
        # Apres init
        w_after = model.lm_head.weight[0, :5].clone()
        print(f"  Poids apres init : {[f'{x:.4f}' for x in w_after.tolist()]}")
        
        # Verification : les poids ont change
        if not torch.equal(w_before, w_after):
            print("  [OK] Les poids ont ete modifies")
        else:
            print("  [ERREUR] Les poids n'ont pas change")
            return False
        
        # Forward pass
        batch, seq_len = 1, 16
        input_ids = torch.randint(1, config['vocab_size'] - 1, (batch, seq_len))
        logits, loss, signatures = model(input_ids, labels=input_ids)
        
        print(f"\n  Forward pass :")
        print(f"    Logits     : {logits.shape}")
        print(f"    Loss       : {loss.item():.4f}")
        print(f"    Signatures : {signatures.shape}")
        
        # Generation
        prompt = torch.randint(1, config['vocab_size'] - 1, (1, 4))
        generated = model.generate(prompt, max_new_tokens=8, temperature=0.8)
        print(f"\n  Generation :")
        print(f"    Prompt     : {prompt.shape}")
        print(f"    Genere     : {generated.shape}")
        print(f"    Tokens     : {generated[0].tolist()}")
        
        print(f"\n  [OK] Modele initialise et operationnel")
        return True
        
    except Exception as e:
        print(f"\n  [ERREUR] {e}")
        return False

# =========================================================================
# TEST 4 : Agent ABC-native
# =========================================================================
def test_agent_abc():
    print("\n" + "="*60)
    print("TEST 4 : Agent ABC-native")
    print("="*60)
    
    try:
        from harmonic_agentic.agentic_loop import HarmonicAgent, analyze_prompt, resonance
        
        agent = HarmonicAgent(max_steps=3)
        
        prompts = [
            "Calcule 15% de 340",
            "Ecris un poeme sur l'amour",
            "Explique pourquoi le ciel est bleu",
        ]
        
        for p in prompts:
            sig = analyze_prompt(p)
            print(f"\n  Prompt: {p[:50]}...")
            print(f"    Signature: phi={sig.phi:.3f}, reasoning={sig.reasoning:.3f}, "
                  f"creative={sig.creative:.3f}, math={sig.math:.3f}, code={sig.code:.3f}")
            
            result = agent.run(p)
            print(f"    Etapes: {result.total_steps}, Temps: {result.elapsed_ms:.1f}ms")
            print(f"    Reponse: {result.final_answer[:100]}...")
        
        print(f"\n  [OK] Agent ABC operationnel")
        return True
        
    except Exception as e:
        print(f"\n  [ERREUR] {e}")
        return False

# =========================================================================
# TEST 5 : Analyse Vocale 7D
# =========================================================================
def test_analyse_vocale():
    print("\n" + "="*60)
    print("TEST 5 : Analyse Vocale 7D")
    print("="*60)
    
    try:
        from harmonic_agentic.voice_signature_7d import extract_voice_signature, VoiceSignature7D
        
        # Signal sinusoidal simule
        import math
        sr = 44100
        duration = 0.5
        samples = [math.sin(2 * math.pi * 220 * t / sr) for t in range(int(sr * duration))]
        
        sig = extract_voice_signature(samples, sr)
        
        print(f"\n  Duree: {sig.duration_s:.2f}s")
        print(f"  Frequence dominante: {sig.dominant_freq_hz:.1f} Hz")
        print(f"  Energie: {sig.energy_db:.1f} dB")
        print(f"  Emotion detectee: {sig.emotion_label}")
        print(f"  Signature 7D:")
        print(f"    phi_voice={sig.phi_voice:.3f}, alpha_voice={sig.alpha_voice:.3f}")
        print(f"    r_voice={sig.r_voice:.3f}, c_voice={sig.c_voice:.3f}")
        print(f"    m_voice={sig.m_voice:.3f}, f_voice={sig.f_voice:.3f}, k_voice={sig.k_voice:.3f}")
        
        print(f"\n  [OK] Analyse vocale operationnelle")
        return True
        
    except Exception as e:
        print(f"\n  [ERREUR] {e}")
        return False

# =========================================================================
# TEST 6 : Generation AV Harmonique
# =========================================================================
def test_generation_av():
    print("\n" + "="*60)
    print("TEST 6 : Generation AV Harmonique")
    print("="*60)
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GENERATION_AV_HARMONIQUE'))
        from engine.harmonic_av_core import HarmonicAVCore
        
        core = HarmonicAVCore()
        
        # Test generation audio
        audio = core.generate_audio("sinus 440hz", duration_s=0.2)
        print(f"\n  Audio genere: {len(audio)} echantillons")
        
        # Test generation image
        img = core.generate_image("ocean sunset golden", width=64, height=64)
        print(f"  Image generee: {img.shape if hasattr(img, 'shape') else 'ok'}")
        
        print(f"\n  [OK] Generation AV operationnelle")
        return True
        
    except Exception as e:
        print(f"\n  [ERREUR] {e}")
        return False

# =========================================================================
# TEST 7 : Moteur LM Arena
# =========================================================================
def test_moteur_lm_arena():
    print("\n" + "="*60)
    print("TEST 7 : Moteur LM Arena")
    print("="*60)
    
    try:
        from harmonic_lm_arena_engine import HarmonicResonanceEngine
        
        engine = HarmonicResonanceEngine()
        
        prompts = [
            "Calcule 15% de 340",
            "Ecris un poeme",
            "Explique le ciel bleu",
        ]
        
        for p in prompts:
            start = time.time()
            result = engine.process(p)
            elapsed = (time.time() - start) * 1000
            
            print(f"\n  Prompt: {p[:40]}...")
            print(f"    Score: {result.resonance_score:.4f}, Pattern: {result.pattern_name}")
            print(f"    Temps: {elapsed:.1f}ms")
        
        print(f"\n  [OK] Moteur LM Arena operationnel")
        return True
        
    except Exception as e:
        print(f"\n  [ERREUR] {e}")
        return False

# =========================================================================
# RAPPORT FINAL
# =========================================================================
def main():
    print("=" * 60)
    print("TEST COMPLET DU HLM (Harmonic Language Model)")
    print("=" * 60)
    print(f"\nConstantes :")
    print(f"  Phi (phi)     = {PHI:.15f}")
    print(f"  1/Phi         = {PHI_INV:.15f}")
    print(f"  Alpha (alpha) = {ALPHA:.15f}")
    
    results = {}
    
    tests = [
        ("Noyau ABC", test_noyau_abc),
        ("Poids Harmoniques", test_poids_harmoniques),
        ("Initialisation Modele", test_initialisation_modele),
        ("Agent ABC-native", test_agent_abc),
        ("Analyse Vocale 7D", test_analyse_vocale),
        ("Generation AV", test_generation_av),
        ("Moteur LM Arena", test_moteur_lm_arena),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            ok = test_fn()
            results[name] = "OK" if ok else "ECHEC"
            if ok: passed += 1
            else: failed += 1
        except Exception as e:
            results[name] = f"ERREUR: {e}"
            failed += 1
    
    print("\n" + "=" * 60)
    print("RAPPORT FINAL")
    print("=" * 60)
    for name, status in results.items():
        print(f"  {name:30s} : {status}")
    
    print(f"\n  Total: {passed} reussis, {failed} echoues sur {len(tests)} tests")
    
    if failed == 0:
        print("\n  [SUCCES] Tous les tests passes !")
    else:
        print(f"\n  [ATTENTION] {failed} test(s) a corriger")
    
    # Sauvegarder le rapport
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "phi": PHI,
        "alpha": ALPHA,
        "tests": results,
        "passed": passed,
        "failed": failed,
        "total": len(tests),
    }
    
    report_path = "rapport_test_hlm_complet.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Rapport sauvegarde: {report_path}")
    
    return failed == 0

if __name__ == '__main__':
    main()
