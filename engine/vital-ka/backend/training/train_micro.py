"""
HWAT Training — Micro run (~2 minutes, ~500 steps)
====================================================
Version ultra-rapide pour vérifier que l'entraînement converge.
"""
import math, time, random, sys
from pathlib import Path
from collections import Counter
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

from hwat_optimized import OptimizedHWAT, phase_attention_fast, mlp_fast, layernorm_amp_fast

PHI = 1.618033988749895

# ═══════════════════════════════════════════════════════════════
# CONFIG — Ultra rapide
# ═══════════════════════════════════════════════════════════════

DIM = 128
N_LAYERS = 2
N_HEADS = 2
VOCAB = 1000
MAX_LEN = 32
BATCH = 2
EPOCHS = 3
N_DATA = 2000
LR = 1e-3
LOG_EVERY = 50
SAVE_EVERY = 200

# ═══════════════════════════════════════════════════════════════
# 1. DONNÉES RAPIDES
# ═══════════════════════════════════════════════════════════════

def make_data(n=2000):
    rng = random.Random(42)
    templates = [
        "{a} est un synonyme de {b}.", "{a} signifie {b}.",
        "On peut dire {a} ou {b}.", "{a} = {b}.",
        "{s} {r} {o}.", "On sait que {s} {r} {o}.",
    ]
    syns = [("vite","rapide"),("beau","joli"),("grand","vaste"),
            ("petit","minuscule"),("fort","puissant"),("calme","tranquille")]
    rels = [("Paris","capitale","France"),("Soleil","etoile","chaud"),
            ("eau","liquide","vie"),("Terre","planete","Soleil")]

    texts = []
    for _ in range(n):
        if rng.random() < 0.5:
            a,b = rng.choice(syns)
            texts.append(rng.choice(templates[:4]).format(a=a,b=b))
        else:
            s,r,o = rng.choice(rels)
            texts.append(rng.choice(templates[4:]).format(s=s,r=r,o=o))
    return texts

def tokenize(texts, vocab_size=1000):
    wc = Counter()
    for t in texts:
        wc.update(t.lower().split())
    w2i = {'<pad>':0,'<unk>':1,'<s>':2,'</s>':3}
    for w,_ in wc.most_common(vocab_size-4):
        w2i[w] = len(w2i)
    seqs = []
    for t in texts:
        ids = [w2i.get(w,1) for w in t.lower().split()]
        seqs.append([2]+ids[:MAX_LEN-2]+[3])
    return seqs, w2i

# ═══════════════════════════════════════════════════════════════
# 2. ENTRAÎNEMENT
# ═══════════════════════════════════════════════════════════════

print("=" * 60)
print("  HWAT Micro Run — ~500 steps, ~2 minutes")
print("=" * 60)

# Data
texts = make_data(N_DATA)
seqs, w2i = tokenize(texts, VOCAB)
print(f"  Data: {len(seqs)} sequences, vocab={len(w2i)}")

# Model
model = OptimizedHWAT(vocab_size=VOCAB, dim=DIM, n_layers=N_LAYERS,
                      n_heads=N_HEADS, max_seq_len=MAX_LEN,
                      hidden_mult=2, use_float32=True)

params = model.get_params()
m = [np.zeros_like(p) for p in params]
v = [np.zeros_like(p) for p in params]
t_count = 0
step = 0

print(f"  Training: {EPOCHS} epochs, batch={BATCH}, seq_len={MAX_LEN}")
t_start = time.time()

for epoch in range(EPOCHS):
    random.shuffle(seqs)
    n_batches = len(seqs) // BATCH
    t0 = time.time()

    for bi in range(n_batches):
        # Get batch
        batch_seqs = seqs[bi*BATCH:(bi+1)*BATCH]
        inputs = np.zeros((BATCH, MAX_LEN), dtype=np.int32)
        targets = np.zeros((BATCH, MAX_LEN), dtype=np.int32)
        for i, s in enumerate(batch_seqs):
            n = min(len(s), MAX_LEN+1)
            inputs[i,:n-1] = s[:n-1]
            targets[i,:n-1] = s[1:n]

        # Forward + backward (batch together)
        all_losses = []
        all_grads = [np.zeros_like(p) for p in params]

        for b in range(BATCH):
            # Forward — single pass for both loss and grad
            psi = model.embed(inputs[b])
            for li in range(model.n_layers):
                x = layernorm_amp_fast(psi, model.ln_gamma[li], model.ln_beta[li])
                x = phase_attention_fast(x, model.n_heads, causal=True, dtype_out=model.ctype)
                psi = psi + x
                x = layernorm_amp_fast(psi, model.ln_gamma[li], model.ln_beta[li])
                x = mlp_fast(x, model.W1[li], model.W2[li], model.b1[li], model.b2[li])
                psi = psi + x

            psi_real = np.real(psi).astype(np.float32)
            psi_imag = np.imag(psi).astype(np.float32)
            psi_flat = np.concatenate([psi_real, psi_imag], axis=-1)
            logits = psi_flat @ model.lm_head + model.lm_bias

            # Loss + grad
            L, V = logits.shape
            logits_s = logits - logits.max(axis=-1, keepdims=True)
            probs = np.exp(logits_s.astype(np.float64))
            probs = probs / probs.sum(axis=-1, keepdims=True)
            probs = np.clip(probs, 1e-10, 1.0)

            flat_targets = targets[b]
            nll = -np.log(probs[np.arange(L), flat_targets])
            mask = (flat_targets != 0).astype(np.float64)
            loss_val = (nll * mask).sum() / max(mask.sum(), 1)
            all_losses.append(float(loss_val))

            # Gradient logits
            grad_logits = probs.copy().astype(np.float32)
            grad_logits[np.arange(L), flat_targets] -= 1
            grad_logits *= mask[:, None].astype(np.float32) / max(mask.sum(), 1)

            # Store head gradients
            hi = len(params) - 2
            all_grads[hi] += psi_flat.T @ grad_logits
            all_grads[hi+1] += grad_logits.sum(axis=0)

        loss = sum(all_losses) / len(all_losses)

        # Adam update
        t_count += 1
        lr = LR
        for i in range(len(params)):
            g = all_grads[i] / BATCH
            g_norm = np.sqrt((g**2).sum())
            if g_norm > 1.0:
                g *= 1.0 / (g_norm + 1e-8)
            m[i] = 0.9*m[i] + 0.1*g
            v[i] = 0.999*v[i] + 0.001*(g**2)
            mh = m[i]/(1-0.9**t_count)
            vh = v[i]/(1-0.999**t_count)
            params[i] -= lr * mh/(np.sqrt(vh)+1e-8)
        model.set_params(params)
        step += 1

        if step % LOG_EVERY == 0:
            elapsed = time.time() - t_start
            print(f"  step {step:5d} | loss: {loss:.4f} | "
                  f"{elapsed:.1f}s | lr: {lr:.6f}")

    print(f"  Epoch {epoch+1} done. Loss: {loss:.4f}")

total = time.time() - t_start
print(f"\n  Total: {step} steps in {total:.0f}s ({step/total:.1f} step/s)")
print(f"  Final loss: {loss:.4f}")
print("  Done.")
