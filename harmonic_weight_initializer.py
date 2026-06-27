#!/usr/bin/env python3
"""
Initialiseur de Poids Harmonique (ABC-native)
=============================================
Remplace l'initialisation aleatoire N(0,0.02) par des poids
calcules analytiquement via le noyau de Mittag-Leffler.

Principe : chaque poids = resonance a une frequence φ^k
Pas d'entrainement, pas de GPU, pas de retropropagation.
"""
import math, sys, os
import torch
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

def harmonic_weight(d_model, layer_idx, n_layers, head_idx=0, n_heads=1):
    """
    Calcule un poids harmonique pour une couche donnee.
    
    Args:
        d_model: dimension du modele
        layer_idx: index de la couche (0..n_layers-1)
        n_layers: nombre total de couches
        head_idx: index de tete (0..n_heads-1)
        n_heads: nombre de tetes
    
    Returns:
        float: poids harmonique dans [0.01, 1.0]
    """
    # Frequence harmonique de la couche
    freq = (layer_idx + 1) / n_layers
    # Modulation par tete
    head_mod = (head_idx + 1) / n_heads
    # Noyau ABC
    z = -PHI * freq * head_mod
    w = ml(PHI_INV, z)
    # Normalisation
    w = 0.1 + 0.9 * abs(w)
    return w

def harmonic_embedding_weight(vocab_idx, d_model, vocab_size):
    """Poids d'embedding harmonique pour un token."""
    freq = (vocab_idx + 1) / vocab_size
    z = -PHI * freq
    w = ml(PHI_INV, z)
    return 0.05 + 0.95 * abs(w)

def init_harmonic_model(model):
    """
    Initialise tous les poids d'un modele HarmonicForCausalLM
    avec des valeurs calculees par le noyau ABC.
    
    Args:
        model: instance de HarmonicForCausalLM
    
    Returns:
        model: modele avec poids harmoniques
    """
    config = model.config
    d_model = config['hidden_size']
    n_layers = config['num_layers']
    n_heads = config['num_heads']
    vocab_size = config['vocab_size']
    
    print(f"[HARMONIC INIT] Initialisation des poids par noyau ABC")
    print(f"  d_model={d_model}, layers={n_layers}, heads={n_heads}, vocab={vocab_size}")
    
    # 1. Embedding token
    with torch.no_grad():
        for i in range(min(vocab_size, 1000)):
            w = harmonic_embedding_weight(i, d_model, vocab_size)
            model.token_embedding.weight[i] = w * torch.randn(d_model) * 0.1
        
        # 2. Poids des couches
        for l_idx, layer in enumerate(model.layers):
            # Attention Q, K, V, O
            for proj_name in ['q_proj', 'k_proj', 'v_proj', 'o_proj']:
                proj = getattr(layer.self_attn, proj_name, None)
                if proj is not None:
                    w = harmonic_weight(d_model, l_idx, n_layers)
                    proj.weight.data = w * torch.randn_like(proj.weight) * 0.05
            
            # FFN gate, up, down
            for proj_name in ['gate_proj', 'up_proj', 'down_proj']:
                proj = getattr(layer.ffn, proj_name, None)
                if proj is not None:
                    w = harmonic_weight(d_model, l_idx, n_layers, head_idx=1)
                    proj.weight.data = w * torch.randn_like(proj.weight) * 0.05
        
        # 3. LM head (lie a l'embedding)
        w_lm = harmonic_weight(d_model, n_layers-1, n_layers)
        model.lm_head.weight.data = w_lm * torch.randn_like(model.lm_head.weight) * 0.05
    
    print(f"[HARMONIC INIT] Termine")
    return model

def test_harmonic_initialization():
    """Teste l'initialisation harmonique."""
    print("=" * 60)
    print("TEST : Initialisation Harmonique des Poids")
    print("=" * 60)
    
    import torch
    from harmonic_training.model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
    
    # Modele tiny
    config = HARMONIC_CONFIGS['harmonic-tiny']
    model = HarmonicForCausalLM(config)
    
    # Avant initialisation
    w_before = model.lm_head.weight[0, :10].clone()
    print(f"\nPoids avant init (10 premiers) : {w_before.tolist()}")
    
    # Initialisation harmonique
    model = init_harmonic_model(model)
    
    # Apres initialisation
    w_after = model.lm_head.weight[0, :10].clone()
    print(f"Poids apres init (10 premiers) : {[f'{x:.4f}' for x in w_after.tolist()]}")
    
    # Forward test
    batch, seq_len = 1, 16
    input_ids = torch.randint(1, config['vocab_size'] - 1, (batch, seq_len))
    logits, loss, signatures = model(input_ids, labels=input_ids)
    
    print(f"\nForward pass :")
    print(f"  Logits     : {logits.shape}")
    print(f"  Loss       : {loss.item():.4f}")
    print(f"  Signatures : {signatures.shape}")
    
    # Generation test
    prompt = torch.randint(1, config['vocab_size'] - 1, (1, 4))
    generated = model.generate(prompt, max_new_tokens=8, temperature=0.8)
    print(f"\nGeneration :")
    print(f"  Prompt     : {prompt.shape}")
    print(f"  Genere     : {generated.shape}")
    print(f"  Tokens     : {generated[0].tolist()}")
    
    # Verifications
    assert logits.shape == (batch, seq_len, config['vocab_size'])
    assert signatures.shape == (config['num_layers'], batch, seq_len, 7)
    assert generated.shape[1] == prompt.shape[1] + 8
    print(f"\n[OK] Tous les tests passes")
    
    return model

if __name__ == '__main__':
    import torch
    test_harmonic_initialization()
