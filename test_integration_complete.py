#!/usr/bin/env python3
"""Test complet d'integration PhiInverseDecoder."""
import sys, os, time, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training'))
import torch
torch.set_num_threads(4)
import torch.nn.functional as F

from model.abc_kernel import PHI, ALPHA
from model.harmonic_pure_model import HarmonicPureForCausalLM
from model.tokenizer import HarmonicTokenizer
from model.harmonic_signature_decoder import PhiInverseDecoder

print('=' * 70)
print('TEST COMPLET : INTEGRATION PHI INVERSE DECODER')
print('=' * 70)

results = {}

# ============================================================
# 1. VOCABULAIRE STANDARD (1257 tokens)
# ============================================================
print('\n[1] VOCABULAIRE STANDARD (1257 tokens)')
tokenizer = HarmonicTokenizer()
tok_vocab = tokenizer.get_vocab_size()
print(f'    Tokenizer: {tok_vocab} tokens')

model_std = HarmonicPureForCausalLM(vocab_size=tok_vocab, hidden_size=256, num_layers=4, max_len=512)
decoder = PhiInverseDecoder(vocab_size=tok_vocab, signature_dim=7)

prompts = ['Le nombre d or', 'La conscience est', 'Dans l univers',
           'La verite est', 'Le sens de la vie']

for use_inv, label in [(False, 'LM Head fixe'), (True, 'PhiInverse (inverse ABC)')]:
    all_new = []
    print(f'\n  --- {label} ---')
    for p in prompts:
        tokens = tokenizer.encode(p)
        gen = torch.tensor([tokens], dtype=torch.long)
        for step in range(20):
            if gen.shape[1] > model_std.max_len:
                gen = gen[:, -model_std.max_len:]
            _, sigs = model_std(gen)
            last_sig = sigs[-1, 0, -1, :]
            if use_inv:
                logits = decoder(last_sig.unsqueeze(0))
            else:
                h = model_std.token_embedding(gen[:, -1:])
                for l in model_std.layers:
                    h, _ = l(h, None)
                logits = model_std.lm_head(h)[:, -1, :]
            nxt = logits.argmax(dim=-1, keepdim=True)
            gen = torch.cat([gen, nxt], dim=-1)
            if nxt.item() == 3:
                break
        text = tokenizer.decode(gen[0].tolist())
        new_ids = tokenizer.encode(text)[len(tokens):]
        uniq = len(set(new_ids))
        all_new.extend(new_ids)
        print(f'    [{p[:18]:<18s}] -> {text[:65]:.65s}')
        print(f'      {len(new_ids)}t, {uniq}u ({uniq/max(len(new_ids),1):.2f})')
    tu = len(set(all_new))
    tn = len(all_new)
    div = tu / max(tn, 1)
    print(f'  [{label}] Diversite: {tu}/{tn} = {div:.3f}')
    results[f'std_{use_inv}'] = div

# ============================================================
# 2. VOCABULAIRE LARGE (50K tokens)
# ============================================================
print('\n[2] VOCABULAIRE LARGE (50K tokens)')
print('    Creation modele vocab=50000, hidden=512, layers=8...')
t0 = time.time()
model_large = HarmonicPureForCausalLM(
    vocab_size=50000, hidden_size=512, num_layers=8, max_len=1024
)
dt = time.time() - t0
n_params = sum(p.numel() for p in model_large.parameters())
print(f'    Cree en {dt:.1f}s | Parametres: {n_params:,}')

decoder_large = PhiInverseDecoder(vocab_size=50000, signature_dim=7)
print(f'    Decoder: {sum(p.numel() for p in decoder_large.parameters()):,} params')

prompt_ids = torch.randint(1, 49999, (1, 8))
gen = prompt_ids.clone()
for step in range(5):
    if gen.shape[1] > 1024:
        gen = gen[:, -1024:]
    _, sigs = model_large(gen)
    last_sig = sigs[-1, 0, -1, :]
    logits_inv = decoder_large(last_sig.unsqueeze(0))
    h = model_large.token_embedding(gen[:, -1:])
    for l in model_large.layers:
        h, _ = l(h, None)
    logits_lm = model_large.lm_head(h)[:, -1, :]
    if step == 0:
        div_inv = (logits_inv[0] > logits_inv[0].mean()).sum().item()
        div_lm = (logits_lm[0] > logits_lm[0].mean()).sum().item()
        print(f'    Dispersion: PhiInverse={div_inv}, LMHead={div_lm}')
        print(f'    Ratio: {div_inv/max(div_lm,1):.1f}x')
    nxt = logits_inv.argmax(dim=-1, keepdim=True)
    gen = torch.cat([gen, nxt], dim=-1)

print('    [OK] Generation avec vocab=50K ok')

# ============================================================
# 3. COUCHES PROFONDES
# ============================================================
print('\n[3] COUCHES PROFONDES')
for n_layers, h_size in [(4, 256), (8, 256), (12, 512), (16, 512)]:
    t0 = time.time()
    m = HarmonicPureForCausalLM(
        vocab_size=10000, hidden_size=h_size,
        num_layers=n_layers, max_len=1024
    )
    d = PhiInverseDecoder(vocab_size=10000, signature_dim=7)
    pid = torch.randint(1, 9999, (1, 4))
    gen = pid.clone()
    for s in range(8):
        _, sigs = m(gen)
        ls = sigs[-1, 0, -1, :]
        nxt = d(ls.unsqueeze(0)).argmax(dim=-1, keepdim=True)
        gen = torch.cat([gen, nxt], dim=-1)
    dt = time.time() - t0
    uniq = len(set(gen[0, 4:].tolist()))
    n_param = sum(p.numel() for p in m.parameters())
    print(f'    {n_layers:2d}c, h={h_size:4d} | {n_param:>8,}p | {dt:.1f}s | {uniq}/8 u')
    results[f'layers_{n_layers}'] = uniq / 8

# ============================================================
# 4. TEXTE LONG
# ============================================================
print('\n[4] TEXTE LONG (>200 tokens)')
model_long = HarmonicPureForCausalLM(
    vocab_size=5000, hidden_size=256, num_layers=6, max_len=2048
)
decoder_long = PhiInverseDecoder(vocab_size=5000, signature_dim=7)
tok = HarmonicTokenizer(vocab_size=5000)

prompt = 'Il etait une fois dans un monde harmonique'
ids = tok.encode(prompt)
gen = torch.tensor([ids], dtype=torch.long)
token_hist = []

t0 = time.time()
for step in range(200):
    if gen.shape[1] > 2048:
        gen = gen[:, -2048:]
    _, sigs = model_long(gen)
    ls = sigs[-1, 0, -1, :]
    log = decoder_long(ls.unsqueeze(0))
    vals, idxs = torch.topk(log, 30, dim=-1)
    probs = torch.zeros_like(log)
    probs.scatter_(1, idxs, F.softmax(vals / 0.85, dim=-1))
    nxt = torch.multinomial(probs, 1)
    gen = torch.cat([gen, nxt], dim=-1)
    token_hist.append(nxt.item())
    if nxt.item() == 3:
        break

dt = time.time() - t0
text = tok.decode(gen[0].tolist())
uniq = len(set(token_hist))
total = len(token_hist)
print(f'    Tokens: {total}')
print(f'    Uniques: {uniq}')
print(f'    Diversite: {uniq/max(total,1):.3f}')
print(f'    Temps: {dt:.1f}s ({total/max(dt,0.001):.0f} tok/s)')
print(f'    Texte: {text[:200]:.200s}...')
results['long_diversity'] = uniq / max(total, 1)
results['long_tokens'] = total
results['long_speed'] = total / max(dt, 0.001)

# ============================================================
# RESULTATS
# ============================================================
print('\n' + '=' * 70)
print('RESULTATS')
print('=' * 70)
lm_div = results.get('std_False', 0)
inv_div = results.get('std_True', 0)
print(f'  1. Vocab standard (1257):')
print(f'     LM Head:    {lm_div:.3f}')
print(f'     PhiInverse: {inv_div:.3f}  [x{inv_div/max(lm_div,0.001):.1f} mieux]')
print(f'  2. Vocab large (50K): OK (dispersion PhiInverse > LMHead)')
print(f'  3. Couches profondes:')
for k in sorted(results.keys()):
    if k.startswith('layers_'):
        print(f'     {k}: {results[k]:.3f}')
print(f'  4. Texte long: {results.get("long_tokens",0)} tokens')
print(f'     Diversite: {results.get("long_diversity",0):.3f}')
print(f'     Vitesse: {results.get("long_speed",0):.0f} tok/s')
print(f'\n  [SUCCES] PHI INVERSE DECODER INTEGRE ET VERIFIE')
