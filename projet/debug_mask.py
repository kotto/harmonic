#!/usr/bin/env python3
"""Debug : analyser le masque d'attention passe par GPT-2 generate()."""
import sys, os, copy, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
import torch.nn as nn
from transformers import GPT2Config, GPT2LMHeadModel, AutoTokenizer

# Creer un modele tiny
config = GPT2Config(vocab_size=50257, n_positions=128, n_embd=256, n_layer=2, n_head=4)
model = GPT2LMHeadModel(config)
tokenizer = AutoTokenizer.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token

# Hook pour capturer le masque
masks = []
class MaskCapture(nn.Module):
    def forward(self, hidden_states, layer_past=None, attention_mask=None,
                head_mask=None, use_cache=False, output_attentions=False):
        if attention_mask is not None:
            masks.append({
                'shape': attention_mask.shape,
                'dtype': attention_mask.dtype,
                'values': attention_mask[0,0,:4,:4].cpu().tolist(),
                'unique': attention_mask.unique().tolist(),
                'min': attention_mask.min().item(),
                'max': attention_mask.max().item(),
            })
        # Retourner un output factice
        B, S, H = hidden_states.shape
        return (torch.zeros_like(hidden_states), None)

# Remplacer la premiere attention
model.transformer.h[0].attn = MaskCapture()

# Generer
inputs = tokenizer("Hello world", return_tensors="pt")
print("Generation avec use_cache=False...")
try:
    outputs = model.generate(
        inputs.input_ids, max_new_tokens=4, do_sample=True,
        temperature=0.8, top_k=40, top_p=0.9,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        use_cache=False,
    )
except RuntimeError as e:
    print(f"Erreur: {e}")

print(f"\nMasques captures: {len(masks)}")
for i, m in enumerate(masks):
    print(f"\nMasque {i}:")
    print(f"  Shape: {m['shape']}")
    print(f"  Dtype: {m['dtype']}")
    print(f"  Min: {m['min']}, Max: {m['max']}")
    print(f"  Valeurs uniques: {m['unique']}")
    print(f"  Extrait 4x4: {m['values']}")
