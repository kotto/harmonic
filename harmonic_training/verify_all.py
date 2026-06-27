"""
Verification complete du projet d'entrainement harmonique
==========================================================
Execute tous les tests unitaires et verifie l'integrite du package.

Usage:
    python verify_all.py
"""

import os
import sys
import time
import importlib

# Ajouter le repertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUCCESS = 0
FAILURE = 0
TOTAL_TESTS = 0


def test(name, func):
    """Execute un test et affiche le resultat."""
    global SUCCESS, FAILURE, TOTAL_TESTS
    TOTAL_TESTS += 1
    
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"{'='*60}")
    
    try:
        start = time.time()
        result = func()
        elapsed = time.time() - start
        if result:
            print(f"[PASS] {elapsed:.2f}s")
            SUCCESS += 1
        else:
            print(f"[FAIL] {elapsed:.2f}s")
            FAILURE += 1
    except Exception as e:
        print(f"[ERROR] {e}")
        FAILURE += 1


def test_imports():
    """Verifie que tous les modules s'importent correctement."""
    modules = [
        'model.abc_kernel',
        'model.harmonic_attention',
        'model.harmonic_layers',
        'model.harmonic_model',
        'config.training_config',
    ]
    
    for module_name in modules:
        try:
            importlib.import_module(module_name)
            print(f"  [OK] {module_name}")
        except Exception as e:
            print(f"  [FAIL] {module_name}: {e}")
            return False
    
    return True


def test_abc_kernel():
    """Teste le noyau ABC."""
    from model.abc_kernel import test_abc_kernel
    return test_abc_kernel()


def test_harmonic_attention():
    """Teste l'attention harmonique 7D."""
    from model.harmonic_attention import test_harmonic_attention
    return test_harmonic_attention()


def test_harmonic_layers():
    """Teste les couches du decodeur."""
    from model.harmonic_layers import test_harmonic_decoder_layer
    return test_harmonic_decoder_layer()


def test_harmonic_model():
    """Teste le modele complet."""
    from model.harmonic_model import test_harmonic_model
    return test_harmonic_model()


def test_configs():
    """Verifie toutes les configurations predefinies."""
    from model.harmonic_model import HARMONIC_CONFIGS
    
    for name, config in HARMONIC_CONFIGS.items():
        # Verifier les champs requis
        required = ['hidden_size', 'num_heads', 'num_layers', 'intermediate_size',
                    'vocab_size', 'max_len', 'dropout']
        for field in required:
            assert field in config, f"Config {name} manque {field}"
        
        # Verifier la divisibilite
        assert config['hidden_size'] % config['num_heads'] == 0, \
            f"{name}: hidden_size % num_heads != 0"
        
        print(f"  [OK] {name}: {config['hidden_size']}D, {config['num_layers']} couches, "
              f"{config['num_heads']} tetes")
    
    return True


def test_model_sizes():
    """Verifie les tailles des modeles (sans creer les gros modeles)."""
    from model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
    
    # Ne tester que harmonic-tiny (les autres sont trop gros pour la RAM)
    config = HARMONIC_CONFIGS['harmonic-tiny']
    model = HarmonicForCausalLM(config)
    params = sum(p.numel() for p in model.parameters())
    
    assert params == 59_358_096, f"harmonic-tiny: {params:,} (attendu 59,358,096)"
    print(f"  [OK] harmonic-tiny: {params:,} parametres")
    
    # Verifier les autres configurations sans creer les modeles
    for name in ['harmonic-small', 'harmonic-base', 'harmonic-large', 'harmonic-xl']:
        c = HARMONIC_CONFIGS[name]
        # Estimer le nombre de parametres
        embed_params = c['vocab_size'] * c['hidden_size']
        layer_params = (
            4 * c['hidden_size'] * c['intermediate_size'] +  # FFN (gate+up+down)
            4 * c['hidden_size'] * c['hidden_size'] +         # Attention (Q,K,V,O)
            2 * c['hidden_size']                              # LayerNorms
        ) * c['num_layers']
        head_params = c['hidden_size'] * c['vocab_size']
        estimated = embed_params + layer_params + head_params
        
        print(f"  [OK] {name}: ~{estimated:,} parametres (estimation)")
    
    return True


def test_gradient_flow():
    """Verifie que le gradient traverse tout le modele."""
    import torch
    from model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
    
    config = HARMONIC_CONFIGS['harmonic-tiny']
    model = HarmonicForCausalLM(config)
    
    batch, seq_len = 2, 32
    x = torch.randint(1, config['vocab_size'] - 1, (batch, seq_len))
    labels = x.clone()
    
    logits, loss, signatures = model(x, labels=labels)
    loss.backward()
    
    # Verifier que tous les parametres ont un gradient
    zero_grads = 0
    for name, param in model.named_parameters():
        if param.grad is None:
            print(f"  [WARN] {name} n'a pas de gradient")
            zero_grads += 1
        elif param.grad.abs().sum().item() == 0:
            print(f"  [WARN] {name} a un gradient nul")
            zero_grads += 1
    
    if zero_grads > 0:
        print(f"  {zero_grads} parametres sans gradient")
        return False
    
    print(f"  [OK] Gradient traverse les {sum(p.numel() for p in model.parameters()):,} parametres")
    return True


def test_generation():
    """Teste la generation autoregressive."""
    import torch
    from model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
    
    config = HARMONIC_CONFIGS['harmonic-tiny']
    model = HarmonicForCausalLM(config)
    model.eval()
    
    prompt = torch.randint(1, config['vocab_size'] - 1, (1, 8))
    
    # Test avec temperature
    generated = model.generate(prompt, max_new_tokens=16, temperature=0.8, top_k=50)
    assert generated.shape[1] == 24, f"Generation: {generated.shape}"
    
    # Test avec temperature basse (plus deterministe)
    generated_det = model.generate(prompt, max_new_tokens=16, temperature=0.1, top_k=1)
    assert generated_det.shape[1] == 24
    
    print(f"  [OK] Generation: {generated.shape}")
    return True


def test_signature_profile():
    """Teste le profil de signature harmonique."""
    import torch
    from model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
    
    config = HARMONIC_CONFIGS['harmonic-tiny']
    model = HarmonicForCausalLM(config)
    
    x = torch.randint(1, config['vocab_size'] - 1, (2, 64))
    profile = model.get_signature_profile(x)
    
    assert profile.shape == (config['num_layers'], 7), f"Profile: {profile.shape}"
    assert torch.all(profile >= 0) and torch.all(profile <= 1), "Profile hors [0,1]"
    
    # Verifier que les signatures varient entre les couches
    variance = profile.var(dim=0).mean().item()
    assert variance > 0, f"Variance nulle: {variance}"
    
    print(f"  [OK] Profil harmonique: {profile.shape}, variance={variance:.4f}")
    return True


def test_training_config():
    """Teste la configuration d'entrainement."""
    from config.training_config import TrainingConfig
    
    config = TrainingConfig()
    
    # Verifier les valeurs par defaut
    assert config.model_name == 'harmonic-tiny'
    assert config.learning_rate == 3e-4
    assert config.max_steps == 100000
    
    # Verifier la validation
    try:
        config.model_name = 'invalid'
        config.__post_init__()
        return False
    except AssertionError:
        pass
    
    print(f"  [OK] Configuration d'entrainement valide")
    return True


def test_package_structure():
    """Verifie la structure du package."""
    required_files = [
        'model/__init__.py',
        'model/abc_kernel.py',
        'model/harmonic_attention.py',
        'model/harmonic_layers.py',
        'model/harmonic_model.py',
        'config/training_config.py',
        'training/train.py',
        'evaluation/run_benchmarks.py',
    ]
    
    base = os.path.dirname(os.path.abspath(__file__))
    for filepath in required_files:
        full_path = os.path.join(base, filepath)
        assert os.path.exists(full_path), f"Fichier manquant: {filepath}"
        print(f"  [OK] {filepath}")
    
    return True


# =========================================================================
# MAIN
# =========================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("VERIFICATION COMPLETE DU PROJET HARMONIQUE")
    print("=" * 60)
    
    # Tests
    test("Imports", test_imports)
    test("Structure du package", test_package_structure)
    test("Noyau ABC", test_abc_kernel)
    test("Attention Harmonique 7D", test_harmonic_attention)
    test("Couches du decodeur", test_harmonic_layers)
    test("Modele complet", test_harmonic_model)
    test("Configurations predefinies", test_configs)
    test("Tailles des modeles", test_model_sizes)
    test("Gradient flow", test_gradient_flow)
    test("Generation", test_generation)
    test("Profil de signature", test_signature_profile)
    test("Configuration d'entrainement", test_training_config)
    
    # Resume
    print(f"\n{'='*60}")
    print(f"RESUME: {SUCCESS}/{TOTAL_TESTS} tests passes")
    if FAILURE > 0:
        print(f"        {FAILURE} tests echoues")
        sys.exit(1)
    else:
        print(f"        TOUS LES TESTS ONT REUSSI")
    print(f"{'='*60}")
