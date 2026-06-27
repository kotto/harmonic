#!/usr/bin/env python3
"""
DEMO : Generation harmonique avec GPT-2 tiny + tokenizer realiste
=================================================================
Utilise un petit GPT-2 (4 couches, 256 hidden) mais avec un tokenizer
realiste pour generer du texte lisible et comparer original vs harmonique.
"""

import os, sys, math, copy
import torch
import torch.nn as nn

# Forcer UTF-8 pour l'encodage console Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transformers import GPT2Config, GPT2LMHeadModel, AutoTokenizer
from harmonic_training.model.harmonic_attention import HarmonicAttention

PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1.0 / PHI


class GPT2HarmonicAttention(nn.Module):
    """Wrapper compatible GPT-2 pour HarmonicAttention."""
    
    def __init__(self, harmonic_attn):
        super().__init__()
        self.attn = harmonic_attn
        self.num_heads = harmonic_attn.num_heads
        self.head_dim = harmonic_attn.head_dim
        self.embed_dim = harmonic_attn.hidden_size
        self.register_buffer('bias', torch.tril(
            torch.ones(1, 1, 2048, 2048, dtype=torch.float16)
        ).view(1, 1, 2048, 2048))
    
    def forward(self, hidden_states, layer_past=None, attention_mask=None,
                head_mask=None, use_cache=False, output_attentions=False):
        # GPT-2 passe un masque [1, 1, 1, S] avec -0.0 (pas de padding)
        # Le masque causal est gere par le bias interne de GPT-2
        # Notre attention harmonique construit son propre masque causal
        
        # Appeler l'attention harmonique standard (qui a son masque causal)
        output, signatures = self.attn(hidden_states, attention_mask=None)
        present = (output, output) if use_cache else None
        
        if output_attentions:
            return (output, signatures, present)
        return (output, present)


def create_harmonic_model(model):
    """Injecte HarmonicAttention dans un GPT-2."""
    harmonic = copy.deepcopy(model)
    config = model.config
    hidden_size = config.n_embd
    num_heads = config.n_head
    
    for i, block in enumerate(harmonic.transformer.h):
        attn_orig = block.attn
        c_attn_w = attn_orig.c_attn.weight.data.clone()
        c_proj_w = attn_orig.c_proj.weight.data.clone()
        
        q_weight = c_attn_w[:, :hidden_size].contiguous()
        k_weight = c_attn_w[:, hidden_size:2*hidden_size].contiguous()
        v_weight = c_attn_w[:, 2*hidden_size:].contiguous()
        
        h_attn = HarmonicAttention(
            hidden_size=hidden_size, num_heads=num_heads,
            dropout=config.attn_pdrop, max_len=config.n_positions
        )
        
        with torch.no_grad():
            h_attn.q_proj.weight.data = q_weight
            h_attn.k_proj.weight.data = k_weight
            h_attn.v_proj.weight.data = v_weight
            h_attn.o_proj.weight.data = c_proj_w
            nn.init.xavier_uniform_(h_attn.signature_proj.projection.weight, gain=PHI_INV)
            nn.init.zeros_(h_attn.signature_proj.projection.bias)
            # Poids tres faibles pour ne pas perturber le modele pre-entraine
            h_attn.resonance_weight.data.fill_(0.01)
            h_attn.abc_weight.data.fill_(0.001)
        
        block.attn = GPT2HarmonicAttention(h_attn)
    
    return harmonic


def generate_text(model, tokenizer, prompt, max_new=32, temperature=0.8):
    """Genere du texte avec le modele."""
    model.eval()
    inputs = tokenizer(prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            max_new_tokens=max_new,
            do_sample=True,
            temperature=temperature,
            top_k=40,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=False,
        )
    
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


def get_signatures(model, tokenizer, text):
    """Extrait les signatures 7D pour chaque couche."""
    inputs = tokenizer(text, return_tensors="pt")
    signatures_by_layer = {}
    
    for i, block in enumerate(model.transformer.h):
        if hasattr(block.attn, 'attn') and hasattr(block.attn.attn, 'signature_proj'):
            sigs = []
            def hook(m, i, o):
                if isinstance(o, tuple) and len(o) == 2:
                    sigs.append(o[1])
            hook_handle = block.attn.attn.register_forward_hook(hook)
            with torch.no_grad():
                _ = model(inputs.input_ids)
            hook_handle.remove()
            
            if sigs:
                signatures_by_layer[i] = sigs[0]
    
    return signatures_by_layer


def main():
    print("=" * 60)
    print("DEMO : GENERATION HARMONIQUE VS ORIGINALE")
    print("=" * 60)
    
    # 1. Creer le modele tiny avec tokenizer realiste
    print("\n1. Creation du modele tiny GPT-2...")
    config = GPT2Config(
        vocab_size=50257, n_positions=128,
        n_embd=256, n_layer=4, n_head=4, n_inner=1024
    )
    model = GPT2LMHeadModel(config)
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    tokenizer.pad_token = tokenizer.eos_token
    print(f"   Vocabulaire: {config.vocab_size} tokens")
    print(f"   Parametres: {sum(p.numel() for p in model.parameters()):,}")
    
    # 2. Creer le modele harmonique
    print("\n2. Injection des attentions harmoniques...")
    harmonic = create_harmonic_model(model)
    print("   OK")
    
    # 3. Prompts de test
    prompts = [
        "The future of artificial intelligence is",
        "In mathematics, the most beautiful equation is",
        "To solve the climate crisis, we must",
        "The meaning of consciousness has puzzled",
    ]
    
    for prompt in prompts:
        print(f"\n{'='*60}")
        print(f"PROMPT: \"{prompt}\"")
        print(f"{'='*60}")
        
        # Generation originale
        print("\n[ORIGINAL]")
        orig_text = generate_text(model, tokenizer, prompt, max_new=24)
        print(f"  {orig_text}")
        
        # Generation harmonique
        print("\n[HARMONIQUE]")
        harm_text = generate_text(harmonic, tokenizer, prompt, max_new=24)
        print(f"  {harm_text}")
        
        # Signatures 7D
        print("\n[SIGNATURES 7D]")
        sigs = get_signatures(harmonic, tokenizer, prompt)
        for layer_idx, sig in sorted(sigs.items()):
            sig_mean = sig[0].mean(dim=0)
            print(f"  Couche {layer_idx}: "
                  f"phi={sig_mean[0]:.3f} alpha={sig_mean[1]:.3f} "
                  f"reasoning={sig_mean[2]:.3f} creativity={sig_mean[3]:.3f} "
                  f"math={sig_mean[4]:.3f} factual={sig_mean[5]:.3f} "
                  f"code={sig_mean[6]:.3f}")
    
    print("\n" + "=" * 60)
    print("DEMO TERMINEE")
    print("=" * 60)


if __name__ == "__main__":
    main()
