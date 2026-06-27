#!/usr/bin/env python3
"""
Test de coherence du LLM Harmonique PUR
=========================================
Valide le pipeline complet :
1. Tokenizer texte → tokens
2. Modele logits → generation
3. Decode tokens → texte
4. Analyse de coherence

Usage:
    python test_llm_pur.py
"""

import sys
import os
import time
import importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
torch.set_num_threads(4)  # Optimisation CPU

# Import direct du module sans passer par le package (qui a des imports cassés)
_MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'harmonic_training', 'model')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'harmonic_training'))

def _import_module(module_name, file_path):
    """Importe un module Python directement depuis son chemin."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

# Importer le tokenizer
tokenizer_mod = _import_module(
    'tokenizer',
    os.path.join(_MODEL_DIR, 'tokenizer.py')
)
HarmonicTokenizer = tokenizer_mod.HarmonicTokenizer

# Importer le modele pur (avec tous ses sous-modules necessaires)
pure_model_mod = _import_module(
    'harmonic_pure_model',
    os.path.join(_MODEL_DIR, 'harmonic_pure_model.py')
)
HarmonicPureForCausalLM = pure_model_mod.HarmonicPureForCausalLM


def test_pipeline_complet():
    """Test complet du pipeline tokenizer → modele → generation → coherence."""
    
    print("=" * 70)
    print("TEST DU PIPELINE LLM HARMONIQUE PUR")
    print("=" * 70)
    
    # ========= 1. INITIALISATION =========
    print("\n[1] Initialisation du tokenizer...")
    t0 = time.time()
    tokenizer = HarmonicTokenizer(vocab_size=5000)
    print(f"    Tokenizer: {tokenizer.get_vocab_size()} tokens "
          f"(charge en {time.time()-t0:.2f}s)")
    
    print("\n[2] Initialisation du modele...")
    t0 = time.time()
    
    # Modele de taille moyenne pour la Phase 1
    model = HarmonicPureForCausalLM(
        vocab_size=tokenizer.get_vocab_size(),
        hidden_size=256,     # 256 pour la phase 1 (vs 512 en production)
        num_layers=4,        # 4 couches (vs 8 en production)
        max_len=512,
    )
    
    params = sum(p.numel() for p in model.parameters())
    trained = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"    Modele: {model.__class__.__name__}")
    print(f"    Parametres: {params:,} (dont {trained} entrainables)")
    print(f"    Taille memoire: ~{params*4/1024/1024:.1f} MB")
    print(f"    Charge en {time.time()-t0:.2f}s")
    
    # ========= 2. ENCODAGE =========
    print("\n[3] Test d'encodage de phrases...")
    
    prompts = [
        "Le nombre d or phi est",
        "Harmonic resonance is",
        "La conscience est",
        "L intelligence artificielle",
        "Dans l univers tout est",
    ]
    
    for prompt in prompts:
        tokens = tokenizer.encode(prompt)
        decoded = tokenizer.decode(tokens)
        coverage = sum(1 for t in tokens if t != tokenizer.unk_id) / max(len(tokens), 1)
        print(f"    Prompt: '{prompt}'")
        print(f"    Tokens: {tokens}")
        print(f"    Decode: '{decoded}'")
        print(f"    Couverture: {coverage:.0%}")
        print()
    
    # ========= 3. GENERATION =========
    print("[4] Test de generation...")
    
    test_cases = [
        {
            'prompt': "Le nombre d or phi est",
            'params': {'temperature': 0.85, 'top_k': 40, 'top_p': 0.9, 'max_new_tokens': 20},
            'description': "Temperature 0.85, top-k=40, top-p=0.9"
        },
        {
            'prompt': "L intelligence artificielle",
            'params': {'temperature': 0.7, 'top_k': 30, 'top_p': 0.95, 'max_new_tokens': 20},
            'description': "Temperature 0.7, conservative"
        },
        {
            'prompt': "Dans l univers tout est",
            'params': {'temperature': 0.9, 'top_k': 50, 'top_p': 0.85, 'max_new_tokens': 20},
            'description': "Temperature 0.9, creative"
        },
        {
            'prompt': "Bonjour le monde de la",
            'params': {'temperature': 0.8, 'top_k': 40, 'top_p': 0.9, 'repetition_penalty': 1.2, 'max_new_tokens': 30},
            'description': "Avec repetition penalty 1.2"
        },
    ]
    
    all_generations = []
    
    for case in test_cases:
        prompt = case['prompt']
        desc = case['description']
        params = case['params']
        
        print(f"\n  {'='*60}")
        print(f"  Cas: {desc}")
        print(f"  Prompt: '{prompt}'")
        
        # Encoder le prompt
        prompt_tokens = tokenizer.encode(prompt)
        print(f"  Tokens prompt ({len(prompt_tokens)}): {prompt_tokens}")
        
        # Generer
        t0 = time.time()
        input_ids = torch.tensor([prompt_tokens], dtype=torch.long)
        
        generated, tokens_info = model.generate(
            input_ids,
            **params
        )
        
        gen_time = time.time() - t0
        gen_tokens = generated[0].tolist()
        new_tokens = gen_tokens[len(prompt_tokens):]
        
        # Decoder
        full_text = tokenizer.decode(gen_tokens)
        generated_text = tokenizer.decode(new_tokens)
        
        print(f"  Generation: {len(new_tokens)} tokens en {gen_time:.2f}s "
              f"({len(new_tokens)/max(gen_time,0.01):.0f} tok/s)")
        print(f"  Genere:    '{generated_text[:100]}'")
        print(f"  Complet:   '{full_text[:150]}'")
        
        # Scores
        if tokens_info:
            avg_score = sum(t.get('score', 0) for t in tokens_info) / len(tokens_info)
            print(f"  Score moyen: {avg_score:.4f}")
        
        all_generations.append({
            'prompt': prompt,
            'full_text': full_text,
            'generated_text': generated_text,
            'tokens_count': len(new_tokens),
            'time_seconds': gen_time,
            'tokens_per_sec': len(new_tokens) / max(gen_time, 0.01),
        })
    
    # ========= 4. ANALYSE DE COHERENCE =========
    print(f"\n{'='*70}")
    print("[5] Analyse de coherence")
    print("=" * 70)
    
    coherence_metrics = {}
    
    for gen in all_generations:
        text = gen['generated_text']
        
        # Metriques basiques
        n_tokens = gen['tokens_count']
        has_unk = '<?>' in text
        unique_ratio = len(set(text.split())) / max(len(text.split()), 1)
        avg_token_len = sum(len(w) for w in text.split()) / max(len(text.split()), 1)
        
        coherence_metrics[gen['prompt']] = {
            'text': text,
            'tokens_count': n_tokens,
            'has_unk': has_unk,
            'unique_ratio': unique_ratio,
            'avg_token_len': avg_token_len,
            'speed_tok_s': gen['tokens_per_sec'],
        }
        
        print(f"\n  Prompt: '{gen['prompt']}'")
        print(f"  Texte: '{text[:80]}'")
        print(f"  Tokens: {n_tokens}, Ratio unique: {unique_ratio:.2f}, "
              f"Longueur moy.: {avg_token_len:.1f}")
        print(f"  Vitesse: {gen['tokens_per_sec']:.0f} tok/s")
        if has_unk:
            print(f"  ⚠ Contient des tokens inconnus")
    
    # ========= 5. VERIFICATION STRUCTURE =========
    print(f"\n{'='*70}")
    print("[6] Verification de la structure du modele")
    print("=" * 70)
    
    # Verifier que le modele est bien deterministe
    input_test = torch.randint(1, model.vocab_size - 1, (1, 16))
    logits1, sig1 = model(input_test)
    logits2, sig2 = model(input_test)
    is_deterministic = torch.allclose(logits1, logits2) and torch.allclose(sig1, sig2)
    print(f"  Deterministe: {'OUI' if is_deterministic else 'NON'}")
    
    # Verifier les signatures
    has_signatures = sig1.shape[-1] == 7
    print(f"  Signatures 7D: {'OUI' if has_signatures else 'NON'}")
    
    # Verifier le profil de resonance
    profile = model.get_signature_profile(input_test)
    print(f"  Profil resonance ({len(profile)} couches):")
    dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code']
    for i, vals in enumerate(profile):
        vals_str = " | ".join(f"{d}={v.item():.3f}" for d, v in zip(dims, vals))
        print(f"    Couche {i}: {vals_str}")
    
    # ========= 6. RESULTATS =========
    print(f"\n{'='*70}")
    print("RESULTATS DU TEST")
    print("=" * 70)
    
    all_ok = True
    
    # Verifications
    if not is_deterministic:
        print("  [ECHEC] Le modele n'est pas deterministe")
        all_ok = False
    else:
        print("  [OK] Modele deterministe (reproductible)")
    
    if not has_signatures:
        print("  [ECHEC] Pas de signatures 7D")
        all_ok = False
    else:
        print("  [OK] Signatures harmoniques 7D presentes")
    
    # Verifier que la generation produit au moins 5 tokens
    min_tokens = min(gen['tokens_count'] for gen in all_generations)
    if min_tokens < 5:
        print(f"  [ECHEC] Generation trop courte: {min_tokens} tokens (min 5)")
        all_ok = False
    else:
        print(f"  [OK] Generation minimale: {min_tokens} tokens")
    
    # Verifier la vitesse de generation
    avg_speed = sum(gen['tokens_per_sec'] for gen in all_generations) / len(all_generations)
    print(f"  [INFO] Vitesse moyenne: {avg_speed:.0f} tok/s")
    if avg_speed < 1:
        print(f"  [⚠] Generation lente (< 1 tok/s), optimiser CPU")
    
    print(f"\n{'='*70}")
    if all_ok:
        print("  ✅ PHASE 1 — LLM HARMONIQUE PUR OPERATIONNEL")
        print(f"  ✅ {len(all_generations)} generations reussies")
        print(f"  ✅ Tokenizer: {tokenizer.get_vocab_size()} tokens")
        print(f"  ✅ Modele: {params:,} parametres (0 entrainables)")
    else:
        print("  ❌ PHASE 1 — ECHEC")
    
    print(f"\n  Pour interagir avec le modele:")
    print(f"    python -c \"")
    print(f"  from harmonic_training.model.harmonic_pure_model import HarmonicPureForCausalLM")
    print(f"  from harmonic_training.model.tokenizer import HarmonicTokenizer")
    print(f"  t = HarmonicTokenizer(5000)")
    print(f"  m = HarmonicPureForCausalLM(vocab_size=len(t), hidden_size=256, num_layers=4)")
    print(f"  tokens = t.encode('Votre message ici')")
    print(f"  gen, info = m.generate(torch.tensor([tokens]), max_new_tokens=50)")
    print(f"  print(t.decode(gen[0].tolist()))")
    print(f"    \"")
    print("=" * 70)
    
    return all_ok


def interactive_demo():
    """Mode interactif pour tester le modele."""
    print("\n" + "=" * 70)
    print("DEMO INTERACTIVE — LLM HARMONIQUE PUR")
    print("=" * 70)
    print("(Appuyez sur Ctrl+C pour quitter)")
    print()
    
    tokenizer = HarmonicTokenizer(vocab_size=5000)
    model = HarmonicPureForCausalLM(
        vocab_size=tokenizer.get_vocab_size(),
        hidden_size=256,
        num_layers=4,
        max_len=512,
    )
    
    print(f"Modele pret ({sum(p.numel() for p in model.parameters()):,} parametres)")
    print()
    
    try:
        while True:
            prompt = input(">>> ").strip()
            if not prompt:
                continue
            if prompt.lower() in ('quit', 'exit', 'q'):
                break
            
            # Encoder
            tokens = tokenizer.encode(prompt)
            
            # Generer
            t0 = time.time()
            input_ids = torch.tensor([tokens], dtype=torch.long)
            generated, tokens_info = model.generate(
                input_ids, max_new_tokens=40, temperature=0.8,
                top_k=40, top_p=0.9
            )
            gen_time = time.time() - t0
            
            # Decoder
            full_text = tokenizer.decode(generated[0].tolist())
            print(f"  {full_text}")
            print(f"  ({len(generated[0])-len(tokens)} tokens, {gen_time:.1f}s)")
            print()
    except KeyboardInterrupt:
        print("\nAu revoir!")
    
    return True


if __name__ == '__main__':
    # Executer le test
    success = test_pipeline_complet()
    
    # Si succes, proposer le mode interactif
    if success:
        print("\n\nTapez 'python test_llm_pur.py --demo' pour le mode interactif")
        
        if '--demo' in sys.argv:
            interactive_demo()
