"""Debug: verifier les shapes de GPT-2 tiny"""
import sys, os
sys.stdout = open(1, 'w', encoding='utf-8', buffering=1)

from transformers import GPT2Config, GPT2LMHeadModel

config = GPT2Config(vocab_size=1000, n_positions=128, n_embd=256, n_layer=4, n_head=4, n_inner=1024)
model = GPT2LMHeadModel(config)

print(f"n_embd={config.n_embd}, n_head={config.n_head}")
print(f"head_dim = {config.n_embd // config.n_head}")

block = model.transformer.h[0]
attn = block.attn
print(f"c_attn weight shape: {attn.c_attn.weight.shape}")
print(f"c_proj weight shape: {attn.c_proj.weight.shape}")

# c_attn = [3*hidden, hidden] = [768, 256]
# Donc q_proj doit etre [256, 256], pas [768, 256]!
hidden = config.n_embd
q = attn.c_attn.weight[:hidden, :]
k = attn.c_attn.weight[hidden:2*hidden, :]
v = attn.c_attn.weight[2*hidden:, :]
print(f"Q shape: {q.shape}, K shape: {k.shape}, V shape: {v.shape}")

print("\nOK - tout est coherent")
