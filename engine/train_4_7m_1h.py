"""
HWAT 4.7M — Entraînement 1 heure
=================================
Modèle : dim=256, 4 couches, 4 têtes, vocab=5000 → 4.7M params
Données : 100K exemples structurés
Durée : 55 minutes
"""

import math, time, random, sys
from pathlib import Path
from collections import Counter
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

from hwat_optimized import OptimizedHWAT, phase_attention_fast, mlp_fast, layernorm_amp_fast

# Config 4.7M
DIM, N_LAYERS, N_HEADS, VOCAB, MAX_LEN = 256, 4, 4, 5000, 64
BATCH, HIDDEN_MULT = 4, 4
LR, TARGET_MINUTES = 1e-3, 55

print("=" * 60)
print("  🌊 HWAT 4.7M — Entraînement 1 heure")
print(f"  dim={DIM}, layers={N_LAYERS}, vocab={VOCAB}, L={MAX_LEN}")
print("=" * 60)

# ═══════════════════════════════════════════════════════════════
# 1. DONNÉES
# ═══════════════════════════════════════════════════════════════
print("\n── Données ──")
rng = random.Random(42)

# Synonymes
fr_syns = [
    ("commencer","débuter"),("terminer","finir"),("rapide","vite"),
    ("lent","ralenti"),("grand","vaste"),("petit","minuscule"),
    ("beau","joli"),("intelligent","brillant"),("riche","fortuné"),
    ("heureux","joyeux"),("triste","malheureux"),("fort","puissant"),
    ("faible","fragile"),("ancien","vieux"),("nouveau","récent"),
    ("difficile","complexe"),("facile","simple"),("important","essentiel"),
    ("calme","tranquille"),("sombre","obscur"),("lumineux","clair"),
    ("chaud","brûlant"),("froid","glacial"),("courageux","brave"),
    ("généreux","large"),("avare","radin"),("modeste","humble"),
]
en_syns = [
    ("begin","start"),("end","finish"),("fast","quick"),("slow","sluggish"),
    ("big","large"),("small","tiny"),("beautiful","pretty"),("smart","clever"),
    ("happy","glad"),("sad","unhappy"),("strong","powerful"),("weak","feeble"),
    ("old","ancient"),("new","recent"),("hard","difficult"),("easy","simple"),
    ("important","crucial"),("calm","peaceful"),("dark","dim"),("bright","shining"),
]

templates = [
    "{a} est un synonyme de {b}.", "{a} et {b} veulent dire la même chose.",
    "On peut dire {a} ou {b}.", "Le mot {a} signifie {b}.", "{a} = {b}.",
]

# Relations
relations = [
    ("Paris","est la capitale de","la France"),
    ("l'eau","gèle à","0 degré Celsius"),
    ("la Terre","tourne autour du","Soleil"),
    ("le Soleil","est une","étoile"),
    ("l'oxygène","est essentiel pour","la respiration"),
    ("les plantes","produisent de","l'oxygène"),
    ("Einstein","a découvert","la relativité"),
    ("Newton","a formulé","les lois du mouvement"),
    ("l'ADN","contient","l'information génétique"),
    ("Python","est un","langage de programmation"),
    ("la gravité","attire","les objets"),
    ("la lumière","est une","onde électromagnétique"),
    ("le cœur","pompe","le sang"),
    ("les poumons","absorbent","l'oxygène"),
    ("le cerveau","traite","l'information"),
]
rel_templates = ["{s} {r} {o}.", "On sait que {s} {r} {o}.", "C'est un fait : {s} {r} {o}."]

N = 80000
texts = []
for i in range(N):
    if rng.random() < 0.6:
        syns_pool = fr_syns if rng.random() < 0.7 else en_syns
        a, b = rng.choice(syns_pool)
        texts.append(rng.choice(templates).format(a=a, b=b))
    else:
        s, r, o = rng.choice(relations)
        texts.append(rng.choice(rel_templates).format(s=s, r=r, o=o))
rng.shuffle(texts)

# Tokenizer
wc = Counter()
for t in texts:
    wc.update(t.lower().split())
w2i = {'<pad>': 0, '<unk>': 1, '<s>': 2, '</s>': 3}
for w, _ in wc.most_common(VOCAB - 4):
    w2i[w] = len(w2i)

seqs = []
for t in texts:
    ids = [w2i.get(w, 1) for w in t.lower().split()]
    seqs.append([2] + ids[:MAX_LEN-2] + [3])

print(f"  {len(seqs):,} séquences, vocab={len(w2i)}")

# ═══════════════════════════════════════════════════════════════
# 2. MODÈLE
# ═══════════════════════════════════════════════════════════════
print("\n── Modèle ──")
model = OptimizedHWAT(vocab_size=VOCAB, dim=DIM, n_layers=N_LAYERS,
                      n_heads=N_HEADS, max_seq_len=MAX_LEN,
                      hidden_mult=HIDDEN_MULT, use_float32=True)

params = model.get_params()
m = [np.zeros_like(p, dtype=np.float64) for p in params]
v = [np.zeros_like(p, dtype=np.float64) for p in params]
t_count, step = 0, 0

# ═══════════════════════════════════════════════════════════════
# 3. ENTRAÎNEMENT
# ═══════════════════════════════════════════════════════════════
print(f"\n── Entraînement ({TARGET_MINUTES} min) ──")
t_start = time.time()
target_sec = TARGET_MINUTES * 60
best_loss = float('inf')
n_batches = len(seqs) // BATCH
ckpt_dir = Path("checkpoints/hwat_4_7m")
ckpt_dir.mkdir(parents=True, exist_ok=True)
print(f"  {n_batches:,} batches/epoch, log every 50 steps", flush=True)
print("  Training starts now...", flush=True)
sys.stdout.flush()

epoch = 0
while True:
    epoch += 1
    random.shuffle(seqs)
    epoch_loss = 0.0
    t_epoch = time.time()

    for bi in range(n_batches):
        elapsed = time.time() - t_start
        if elapsed > target_sec:
            break

        # Batch
        batch_seqs = seqs[bi*BATCH:(bi+1)*BATCH]
        inputs = np.zeros((BATCH, MAX_LEN), dtype=np.int32)
        targets = np.zeros((BATCH, MAX_LEN), dtype=np.int32)
        for i, s in enumerate(batch_seqs):
            n = min(len(s), MAX_LEN+1)
            inputs[i, :n-1] = s[:n-1]
            targets[i, :n-1] = s[1:n]

        # Forward + backward
        all_losses, all_grads = [], [np.zeros_like(p, dtype=np.float64) for p in params]

        for b in range(BATCH):
            psi = model.embed(inputs[b])
            for li in range(model.n_layers):
                x = layernorm_amp_fast(psi, model.ln_gamma[li], model.ln_beta[li])
                x = phase_attention_fast(x, model.n_heads, causal=True, dtype_out=model.ctype)
                psi = psi + x
                x = layernorm_amp_fast(psi, model.ln_gamma[li], model.ln_beta[li])
                x = mlp_fast(x, model.W1[li], model.W2[li], model.b1[li], model.b2[li])
                psi = psi + x

            psi_real, psi_imag = np.real(psi).astype(np.float32), np.imag(psi).astype(np.float32)
            psi_flat = np.concatenate([psi_real, psi_imag], axis=-1)
            logits = psi_flat @ model.lm_head + model.lm_bias

            L, V = logits.shape
            logits_s = logits - logits.max(axis=-1, keepdims=True)
            probs = np.exp(logits_s.astype(np.float64))
            probs = probs / probs.sum(axis=-1, keepdims=True)
            probs = np.clip(probs, 1e-10, 1.0)
            flat_tgt = targets[b]
            nll = -np.log(probs[np.arange(L), flat_tgt])
            mask = (flat_tgt != 0).astype(np.float64)
            loss_val = (nll * mask).sum() / max(mask.sum(), 1)
            all_losses.append(float(loss_val))

            grad_logits = probs.copy().astype(np.float32)
            grad_logits[np.arange(L), flat_tgt] -= 1
            grad_logits *= mask[:, None].astype(np.float32) / max(mask.sum(), 1)

            hi = len(params) - 2
            all_grads[hi] += psi_flat.T @ grad_logits
            all_grads[hi+1] += grad_logits.sum(axis=0)

        loss = sum(all_losses) / len(all_losses)
        epoch_loss += loss

        # Adam
        t_count += 1
        lr = LR * min(1.0, t_count / 500)  # warmup
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

        if step % 50 == 0:
            elapsed = time.time() - t_start
            print(f"  step {step:5d} | loss: {loss:.4f} | "
                  f"lr: {lr:.6f} | {elapsed/60:.0f}min | "
                  f"{step/(elapsed+1e-10):.1f} step/s", flush=True)

            if loss < best_loss:
                best_loss = loss
                model.save(str(ckpt_dir / "model_best.npz"))

        if step % 2000 == 0:
            model.save(str(ckpt_dir / f"model_step{step}.npz"))

    # Fin d'epoch
    elapsed = time.time() - t_start
    print(f"  ── Epoch {epoch} | avg loss: {epoch_loss/max(1,n_batches):.4f} | "
          f"{elapsed/60:.0f}min ──")
    model.save(str(ckpt_dir / f"model_epoch{epoch}.npz"))

    if elapsed > target_sec:
        break

# Final
total = time.time() - t_start
model.save(str(ckpt_dir / "model_final.npz"))
print(f"\n{'=' * 60}")
print(f"  ✅ Entraînement terminé")
print(f"  Steps: {step} | Temps: {total/60:.0f} min")
print(f"  Steps/sec: {step/total:.1f}")
print(f"  Best loss: {best_loss:.4f}")
print(f"  Modèle: {ckpt_dir}/model_final.npz")
print(f"{'=' * 60}")
