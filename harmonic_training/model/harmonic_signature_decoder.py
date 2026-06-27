"""
Harmonic Signature Decoder
==========================
Decodeur harmonique base sur l'INVERSE de la derivee ABC.

     Derivee ABC (forward)            Integrale ABC (inverse/decoder)
    ===========================     =================================
    K(t) = B(alpha) * E_alpha       W_inv(d,v) = PHI / K_abc(d)
         x (-alpha*t^alpha/(1-a))              x cos(v*d*PHI/V)

    Applique aux embeddings         Applique aux signatures 7D
    -> signatures 7D                -> logits V
    
    "differentie" la sequence       "integre" les signatures
    (capture le changement)         (reconstruit le token original)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Optional, Tuple
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.abc_kernel import PHI, ALPHA, B_1_PHI


class PhiInverseDecoder(nn.Module):
    """
    Decodeur = Inverse de la derivee ABC = Integrale fractionnaire.
    
    embedding_i[d] = cos(i*d*PHI/V) * exp(-d*ALPHA/V)
    K_abc(d) = exp(-d*ALPHA/V)  [noyau ABC]
    decodeur[d,v] = cos(v*d*PHI/V) * PHI / K_abc(d)
                  = cos(v*d*PHI/V) * PHI * exp(d*ALPHA/V)
    """
    
    def __init__(self, vocab_size: int, signature_dim: int = 7):
        super().__init__()
        self.vocab_size = vocab_size
        self.signature_dim = signature_dim
        
        d = torch.arange(signature_dim, dtype=torch.float32)
        k_abc = torch.exp(-d * ALPHA / signature_dim)
        inv_k = PHI / (k_abc + 1e-8)
        
        v = torch.arange(vocab_size, dtype=torch.float32).unsqueeze(1)
        d2 = d.unsqueeze(0)
        
        phase = v * d2 * PHI / vocab_size
        weight = torch.cos(phase) * inv_k.unsqueeze(0)
        weight = weight / (weight.norm(dim=0, keepdim=True) + 1e-8)
        
        self.register_buffer('weight', weight)
    
    def forward(self, signatures: torch.Tensor) -> torch.Tensor:
        return F.linear(signatures, self.weight) * PHI


class PhiInversePipeline:
    def __init__(self, vocab_size=5000, hidden_size=256, num_layers=4, max_len=512):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from model.tokenizer import HarmonicTokenizer
        from model.harmonic_pure_model import HarmonicPureForCausalLM
        
        print("[PhiInverse] Initialisation...")
        self.tokenizer = HarmonicTokenizer(vocab_size=vocab_size)
        actual_vocab = self.tokenizer.get_vocab_size()
        
        self.model = HarmonicPureForCausalLM(
            vocab_size=actual_vocab, hidden_size=hidden_size,
            num_layers=num_layers, max_len=max_len,
        )
        self.decoder = PhiInverseDecoder(vocab_size=actual_vocab, signature_dim=7)
        
        n_total = sum(p.numel() for p in self.model.parameters())
        n_dec = sum(p.numel() for p in self.decoder.parameters())
        print(f"  Vocab={actual_vocab} | Decoder={n_dec:,} params (fixes)")
        print(f"  Modele={n_total:,} + Decoder={n_dec:,} = {n_total+n_dec:,} totaux (0 entrainables)")
    
    @torch.no_grad()
    def generate(self, prompt, max_new=40, temperature=0.85, top_k=30, top_p=0.92,
                 repetition_penalty=1.3, use_inverse=True):
        tokens = self.tokenizer.encode(prompt)
        generated = torch.tensor([tokens], dtype=torch.long)
        token_hist = []
        
        for step in range(max_new):
            if generated.shape[1] > self.model.max_len:
                generated = generated[:, -self.model.max_len:]
            
            _, signatures = self.model(generated)
            last_sig = signatures[-1, 0, -1, :]
            
            if use_inverse:
                logits = self.decoder(last_sig.unsqueeze(0))  # [1, V]
            else:
                hidden = self.model.token_embedding(generated[:, -1:])
                for layer in self.model.layers:
                    hidden, _ = layer(hidden, None)
                logits = self.model.lm_head(hidden)  # [1, 1, V]
                logits = logits[:, -1, :]  # [1, V]
            
            if repetition_penalty > 1.0:
                for tok in generated[0, -50:]:
                    if tok < logits.shape[1]:
                        if logits[0, tok] < 0:
                            logits[0, tok] *= repetition_penalty
                        else:
                            logits[0, tok] /= repetition_penalty
            
            probs = F.softmax(logits / temperature, dim=-1)
            
            if top_k > 0:
                vals, idx = torch.topk(probs, min(top_k, probs.shape[-1]), dim=-1)
                probs = torch.zeros_like(probs)
                probs.scatter_(1, idx, vals)
                probs = probs / probs.sum(dim=-1, keepdim=True)
            
            if top_p < 1.0:
                sp, si = torch.sort(probs, descending=True, dim=-1)
                cum = torch.cumsum(sp, dim=-1)
                rmv = cum > top_p
                rmv[:, 1:] = rmv[:, :-1].clone()
                rmv[:, 0] = False
                for b in range(probs.shape[0]):
                    idx_rmv = si[b][rmv[b]]
                    probs[b, idx_rmv] = 0.0
                probs = probs / probs.sum(dim=-1, keepdim=True)
            
            next_t = torch.multinomial(probs, 1)
            generated = torch.cat([generated, next_t], dim=-1)
            token_hist.append(next_t.item())
            
            if next_t.item() == 3:
                break
        
        text = self.tokenizer.decode(generated[0].tolist())
        info = {
            'unique': len(set(token_hist)),
            'total': len(token_hist),
            'diversity': len(set(token_hist)) / max(len(token_hist), 1),
        }
        return text, info


def test():
    print("=" * 70)
    print("TEST PHI INVERSE DECODER")
    print("=" * 70)
    
    pipe = PhiInversePipeline()
    
    prompts = ["Le nombre d or", "La conscience est", "Dans l univers",
               "La verite est", "Le sens de la vie"]
    
    for use_inv, label in [(False, "LM Head fixe"), (True, "PhiInverse (inverse ABC)")]:
        all_new = []
        print(f"\n--- {label} ---")
        for p in prompts:
            text, info = pipe.generate(p, max_new=20, use_inverse=use_inv,
                                        temperature=0.85, top_k=30)
            new_ids = pipe.tokenizer.encode(text)[len(pipe.tokenizer.encode(p)):]
            uniq = len(set(new_ids))
            all_new.extend(new_ids)
            print(f"  [{p:<20s}] -> {text[:80]:.80s}")
            print(f"    {len(new_ids)} t, {uniq} u ({uniq/max(len(new_ids),1):.2f})")
        tu = len(set(all_new)); tn = len(all_new)
        print(f"  [{label}] {tu}/{tn} = {tu/max(tn,1):.3f}")
    
    print("\n[OK] Test termine")


if __name__ == '__main__':
    test()
