"""
🌊 HWAT Kaggle/Colab Training Script
=====================================
Copier-coller ce script dans un notebook Kaggle ou Google Colab.
GPU activé automatiquement.

Usage Kaggle :
  1. Créer un nouveau notebook : kaggle.com → Code → New Notebook
  2. Activer GPU : Settings → Accelerator → GPU P100
  3. Copier tout ce fichier dans une cellule
  4. Exécuter

Usage Colab :
  1. Créer un nouveau notebook : colab.research.google.com
  2. Activer GPU : Runtime → Change runtime type → T4 GPU
  3. Copier tout ce fichier dans une cellule
  4. Exécuter
"""

import math, time, random, sys, os
from pathlib import Path
from collections import Counter
from typing import List, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# 0. SETUP — Vérification GPU
# ═══════════════════════════════════════════════════════════════════════════════

import torch
import torch.nn as nn
import torch.nn.functional as F

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("=" * 60)
print("  🌊 HWAT Training — Kaggle/Colab GPU")
print(f"  Device: {device}")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"  CUDA version: {torch.version.cuda}")
print("=" * 60)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. MODÈLE (hwat_torch.py intégré)
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
ALPHA = 1.0 / PHI
TAU = 2.0 * math.pi

def _fnv1a(s: str) -> int:
    h = 2166136261
    for ch in s.encode('utf-8'):
        h ^= ch; h = (h * 16777619) & 0xFFFFFFFF
    return h

def phase_attention_fast(psi: torch.Tensor, n_heads: int, causal: bool = True) -> torch.Tensor:
    L, D = psi.shape; head_dim = D // n_heads
    heads = psi.reshape(L, n_heads, head_dim).permute(1, 0, 2)
    H, L, d = heads.shape
    A = heads.abs().float(); phi = heads.angle().float()
    cos_phi = torch.cos(phi); sin_phi = torch.sin(phi)
    phase_scores = (cos_phi @ cos_phi.transpose(1,2) + sin_phi @ sin_phi.transpose(1,2)) / d
    A_norm_sq = (A**2).sum(dim=-1)
    amp_scores = torch.sqrt(torch.clamp(A_norm_sq.unsqueeze(2)*A_norm_sq.unsqueeze(1), min=1e-10))
    scores = phase_scores * amp_scores
    if causal:
        mask = torch.triu(torch.ones(L,L,device=psi.device,dtype=torch.float32), diagonal=1)
        scores = scores - 1e9 * mask.unsqueeze(0)
    scores = scores - scores.max(dim=-1,keepdim=True).values
    attn = torch.softmax(scores.double(), dim=-1).float()
    out = attn.to(heads.dtype) @ heads
    return out.permute(1,0,2).reshape(L,D).to(psi.dtype)

def mlp_fast(psi, W1, W2, b1=None, b2=None):
    A = psi.abs().float(); phase = psi.angle().float()
    h = A @ W1
    if b1 is not None:
        h = h + b1
    h = F.relu(h)
    A_new = h @ W2
    if b2 is not None:
        A_new = A_new + b2
    return (A_new * (torch.cos(phase) + 1j*torch.sin(phase))).to(psi.dtype)

def layernorm_amp_fast(psi, gamma=None, beta=None, eps=1e-6):
    A = psi.abs(); mu = A.mean(dim=-1,keepdim=True)
    sigma = A.std(dim=-1,keepdim=True) + eps; A_norm = (A-mu)/sigma
    if gamma is not None: A_norm = A_norm * gamma
    if beta is not None: A_norm = A_norm + beta
    phase = psi.angle()
    return (A_norm*(torch.cos(phase)+1j*torch.sin(phase))).to(psi.dtype)

class HWAT(nn.Module):
    def __init__(self, vocab_size, dim=256, n_layers=4, n_heads=4, max_seq_len=64, hidden_mult=4):
        super().__init__()
        self.vocab_size, self.dim, self.n_layers, self.n_heads = vocab_size, dim, n_layers, n_heads
        self.max_seq_len, self.hidden_dim = max_seq_len, dim*hidden_mult
        self.ctype = torch.complex64

        # Embedding deterministe
        sigma = 1.0/math.sqrt(dim)
        def det_norm(size, seed):
            g = torch.Generator(); g.manual_seed(seed & 0xFFFFFFFF)
            return torch.randn(size, generator=g, dtype=torch.float32)
        A_tab = torch.zeros(vocab_size, dim); phi_tok = torch.zeros(vocab_size, dim)
        for tok in range(vocab_size):
            v = det_norm(dim, _fnv1a(f"amp_{tok}"))*sigma
            A_tab[tok] = v/(v.norm()+1e-30)
            phi_tok[tok] = det_norm(dim, _fnv1a(f"phi_{tok}")).fmod(1.0)*TAU
        phi_pos = torch.zeros(max_seq_len, dim)
        ks = torch.arange(dim, dtype=torch.float32)/max(dim-1,1)
        omegas = 0.1*torch.pow(torch.tensor(math.pi/0.1), ks)
        for p in range(max_seq_len): phi_pos[p] = omegas*p
        self.register_buffer('A_table', A_tab)
        self.register_buffer('phi_token', phi_tok)
        self.register_buffer('phi_pos', phi_pos)

        # Blocs MLP
        self.W1, self.b1, self.W2, self.b2 = nn.ParameterList(), nn.ParameterList(), nn.ParameterList(), nn.ParameterList()
        self.ln_gamma, self.ln_beta = nn.ParameterList(), nn.ParameterList()
        for lid in range(n_layers):
            H = self.hidden_dim; D = dim
            g1 = torch.Generator(); g1.manual_seed(_fnv1a(f"mlp_w1_{lid}")&0xFFFFFFFF)
            g3 = torch.Generator(); g3.manual_seed(_fnv1a(f"mlp_w2_{lid}")&0xFFFFFFFF)
            lim1, lim2 = math.sqrt(3.0/D), math.sqrt(3.0/H)
            self.W1.append(nn.Parameter(torch.randn(D,H,generator=g1)*2*lim1-lim1))
            self.b1.append(nn.Parameter(torch.zeros(H)))
            self.W2.append(nn.Parameter(torch.randn(H,D,generator=g3)*2*lim2-lim2))
            self.b2.append(nn.Parameter(torch.zeros(D)))
            self.ln_gamma.append(nn.Parameter(torch.ones(D)))
            self.ln_beta.append(nn.Parameter(torch.zeros(D)))

        # LM head
        g = torch.Generator(); g.manual_seed(_fnv1a("lm_head")&0xFFFFFFFF)
        self.lm_head = nn.Parameter(torch.randn(2*dim, vocab_size, generator=g)*math.sqrt(2.0/(2*dim)))
        self.lm_bias = nn.Parameter(torch.zeros(vocab_size))

    def embed(self, token_ids):
        L = min(len(token_ids), self.max_seq_len); token_ids = token_ids[:L]
        A = self.A_table[token_ids]; phi_t = self.phi_token[token_ids]; phi_p = self.phi_pos[:L]
        phi = phi_t + phi_p
        return (A*(torch.cos(phi)+1j*torch.sin(phi))).to(self.ctype)

    def forward(self, token_ids):
        psi = self.embed(token_ids)
        for li in range(self.n_layers):
            x = layernorm_amp_fast(psi, self.ln_gamma[li], self.ln_beta[li])
            x = phase_attention_fast(x, self.n_heads, causal=True)
            psi = psi + x
            x = layernorm_amp_fast(psi, self.ln_gamma[li], self.ln_beta[li])
            x = mlp_fast(x, self.W1[li], self.W2[li], self.b1[li], self.b2[li])
            psi = psi + x
        psi_flat = torch.cat([psi.real.float(), psi.imag.float()], dim=-1)
        return psi_flat @ self.lm_head + self.lm_bias

# ═══════════════════════════════════════════════════════════════════════════════
# 2. DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

print("\n── Génération des données ──")
rng = random.Random(42)
syns = [('commencer','debuter'),('terminer','finir'),('rapide','vite'),
        ('lent','ralenti'),('grand','vaste'),('petit','minuscule'),
        ('beau','joli'),('intelligent','brillant'),('fort','puissant'),
        ('begin','start'),('end','finish'),('fast','quick'),('big','large'),
        ('small','tiny'),('beautiful','pretty'),('smart','clever')]
rels = [('Paris','capitale','France'),('Soleil','etoile','chaud'),
        ('eau','liquide','vie'),('Terre','planete','Soleil'),
        ('lumiere','onde','electromagnetique'),('Einstein','decouvert','relativite'),
        ('Python','langage','programmation'),('ADN','contient','information genetique'),
        ('coeur','pompe','sang'),('gravite','attire','objets')]
templates = ['{a} est un synonyme de {b}.','Le mot {a} signifie {b}.','{a} = {b}.',
             '{a} et {b} sont equivalents.','On peut dire {a} ou {b}.',
             '{s} {r} {o}.','On sait que {s} {r} {o}.','C est un fait: {s} {r} {o}.']

texts = []
for _ in range(100000):
    if rng.random()<0.6:
        a,b=rng.choice(syns); texts.append(rng.choice(templates[:5]).format(a=a,b=b))
    else:
        s,r,o=rng.choice(rels); texts.append(rng.choice(templates[5:]).format(s=s,r=r,o=o))
rng.shuffle(texts)

VOCAB_SIZE = 5000; MAX_LEN = 64
wc = Counter()
for t in texts: wc.update(t.lower().split())
w2i = {'<pad>':0,'<unk>':1,'<s>':2,'</s>':3}
for w,_ in wc.most_common(VOCAB_SIZE-4): w2i[w]=len(w2i)
seqs = [[2]+[w2i.get(w,1) for w in t.lower().split()[:MAX_LEN-2]]+[3] for t in texts]
print(f"  {len(seqs):,} sequences, vocab={len(w2i)}")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. ENTRAÎNEMENT
# ═══════════════════════════════════════════════════════════════════════════════

MODEL_DIM = 256
MODEL_LAYERS = 4
MODEL_HEADS = 4
BATCH_SIZE = 8
EPOCHS = 5
LR = 3e-4
LOG_EVERY = 100
SAVE_EVERY = 2000

print(f"\n── Création du modèle (dim={MODEL_DIM}, {MODEL_LAYERS} couches) ──")
model = HWAT(vocab_size=min(len(w2i), VOCAB_SIZE), dim=MODEL_DIM,
             n_layers=MODEL_LAYERS, n_heads=MODEL_HEADS,
             max_seq_len=MAX_LEN, hidden_mult=4).to(device)
n_params = sum(p.numel() for p in model.parameters())
print(f"  {n_params:,} paramètres")

optimizer = torch.optim.Adam(model.parameters(), lr=LR)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS*len(seqs)//BATCH_SIZE)

print(f"\n── Entraînement ({EPOCHS} epochs, batch={BATCH_SIZE}) ──")
t_start = time.time()
step = 0
best_loss = float('inf')
loss_history = []

for epoch in range(EPOCHS):
    random.shuffle(seqs)
    epoch_loss = 0.0
    n_batches = len(seqs)//BATCH_SIZE
    t_epoch = time.time()

    for bi in range(n_batches):
        batch_seqs = seqs[bi*BATCH_SIZE:(bi+1)*BATCH_SIZE]
        inputs = torch.zeros(BATCH_SIZE, MAX_LEN, dtype=torch.long, device=device)
        targets = torch.zeros(BATCH_SIZE, MAX_LEN, dtype=torch.long, device=device)
        for i, s in enumerate(batch_seqs):
            n = min(len(s), MAX_LEN+1)
            inputs[i,:n-1] = torch.tensor(s[:n-1], device=device)
            targets[i,:n-1] = torch.tensor(s[1:n], device=device)

        # Forward + backward batché
        optimizer.zero_grad()
        batch_loss = 0.0
        for b in range(BATCH_SIZE):
            logits = model(inputs[b])
            loss = F.cross_entropy(logits.unsqueeze(0).transpose(1,2),
                                   targets[b].unsqueeze(0), ignore_index=0)
            batch_loss += loss
        batch_loss = batch_loss / BATCH_SIZE
        batch_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        epoch_loss += batch_loss.item()
        step += 1

        if step % LOG_EVERY == 0:
            elapsed = time.time() - t_start
            avg_loss = batch_loss.item()
            loss_history.append((step, avg_loss))
            print(f"  step {step:5d} | loss: {avg_loss:.4f} | "
                  f"{elapsed/60:.0f}min | {step/(elapsed+1e-10):.1f} step/s", flush=True)

            if avg_loss < best_loss:
                best_loss = avg_loss
                torch.save(model.state_dict(), 'model_best.pt')

        if step % SAVE_EVERY == 0:
            torch.save({
                'step': step, 'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': avg_loss,
            }, f'model_step{step}.pt')

    # Fin d'époque
    epoch_avg = epoch_loss / max(1, n_batches)
    elapsed = time.time() - t_start
    print(f"  ── Epoch {epoch+1} | avg loss: {epoch_avg:.4f} | "
          f"{elapsed/60:.0f}min ──", flush=True)

# Final
total_time = time.time() - t_start
torch.save(model.state_dict(), 'model_final.pt')
print(f"\n{'='*60}")
print(f"  ✅ Entraînement terminé")
print(f"  Steps: {step} | Temps: {total_time/60:.0f} min")
print(f"  Steps/sec: {step/total_time:.1f}")
print(f"  Best loss: {best_loss:.4f}")
print(f"  Modèle: model_final.pt")
print(f"{'='*60}")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. TEST DE GÉNÉRATION
# ═══════════════════════════════════════════════════════════════════════════════

print("\n── Test de génération ──")
model.eval()
i2w = {v:k for k,v in w2i.items()}

test_prompts = ["le mot rapide", "Paris est", "la lumiere"]
for prompt in test_prompts:
    tokens = [w2i.get(w, 1) for w in prompt.lower().split()]
    input_ids = torch.tensor([2]+tokens, device=device)

    with torch.no_grad():
        logits = model(input_ids)
        next_token_logits = logits[-1]
        top5 = torch.topk(next_token_logits, 5)
        top_words = [i2w.get(idx.item(), '?') for idx in top5.indices]
        print(f"  '{prompt}' → {top_words}")

print("\n  ✅ Terminé !")
