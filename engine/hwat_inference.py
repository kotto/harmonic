"""
🌊 hwat_inference.py — Module d'inférence HWAT (prêt à déployer)
==================================================================
Charge le modèle entraîné (Phase 2) et fournit une API simple :

  from hwat_inference import load_hwat, generate

  model, tokenizer = load_hwat()
  reponse = generate("théorème de", max_tokens=30)
  vecteur  = model.encode("lumière onde")

Prérequis : avoir lancé train_hwat_v2.py pour produire data/hwat_v2.pt

Utilisable immédiatement — import dans harmonic_brain.py ou standalone.
"""

import sys, math, re, json
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

import torch
import torch.nn as nn
import torch.nn.functional as F

PHI = 1.618033988749895
TAU = 2.0 * math.pi


# ════════════════════════════════════════════════════════════════
# 1. ARCHITECTURE (replique exacte de train_hwat_v2.py)
# ════════════════════════════════════════════════════════════════

class EmbeddingV2(nn.Module):
    def __init__(self, vocab_size, dim, max_len):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, dim)
        t = torch.arange(max_len, dtype=torch.float32)
        ks = torch.arange(dim, dtype=torch.float32)
        omegas = 0.1 * (math.pi / 0.1) ** (ks / max(dim - 1, 1))
        self.register_buffer('pos_enc', omegas[None] * t[:, None])

    def forward(self, ids):
        return self.token_emb(ids) + self.pos_enc[:ids.shape[0]]


class PhaseAttentionV2(nn.Module):
    def __init__(self, dim, n_heads, causal=True):
        super().__init__()
        self.dim, self.n_heads = dim, n_heads
        self.head_dim = dim // n_heads
        self.causal = causal
        self.Wq_re = nn.Linear(dim, dim, bias=False)
        self.Wq_im = nn.Linear(dim, dim, bias=False)
        self.Wk_re = nn.Linear(dim, dim, bias=False)
        self.Wk_im = nn.Linear(dim, dim, bias=False)
        self.Wv_re = nn.Linear(dim, dim, bias=False)
        self.Wv_im = nn.Linear(dim, dim, bias=False)
        self.Wo_re = nn.Linear(dim, dim, bias=False)
        self.Wo_im = nn.Linear(dim, dim, bias=False)

    def forward(self, x):
        L, D = x.shape
        H, d = self.n_heads, self.head_dim
        Q = self.Wq_re(x) + 1j * self.Wq_im(x)
        K = self.Wk_re(x) + 1j * self.Wk_im(x)
        V = self.Wv_re(x) + 1j * self.Wv_im(x)
        Qh = Q.reshape(L, H, d).permute(1, 0, 2)
        Kh = K.reshape(L, H, d).permute(1, 0, 2)
        Vh = V.reshape(L, H, d).permute(1, 0, 2)
        dphi = Qh.angle()[:, :, None] - Kh.angle()[:, None, :]
        cos_phase = torch.cos(dphi)
        amp_w = torch.sqrt(Qh.abs()[:, :, None] * Kh.abs()[:, None, :] + 1e-12)
        scores = (cos_phase * amp_w).sum(-1) / math.sqrt(d)
        if self.causal:
            mask = torch.triu(torch.ones(L, L, device=x.device), diagonal=1).bool()
            scores = scores.masked_fill(mask[None], float('-inf'))
        attn = F.softmax(scores, dim=-1).to(dtype=Vh.dtype)
        out = torch.einsum('hij,hjd->hid', attn, Vh)
        out = out.permute(1, 0, 2).reshape(L, D)
        return self.Wo_re(out.real) + self.Wo_im(out.imag)


class HWATBlockV2(nn.Module):
    def __init__(self, dim, n_heads):
        super().__init__()
        self.gate_mlp = nn.Sequential(
            nn.Linear(dim, dim // 4), nn.GELU(),
            nn.Linear(dim // 4, dim), nn.Sigmoid()
        )
        self.attn = PhaseAttentionV2(dim, n_heads, causal=False)
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * 4), nn.GELU(),
            nn.Linear(dim * 4, dim)
        )
        self.ln1 = nn.LayerNorm(dim)
        self.ln2 = nn.LayerNorm(dim)

    def forward(self, x):
        X = x.T.contiguous()
        F = torch.fft.rfft(X, dim=-1)
        gains = self.gate_mlp(F.abs().mean(-1))
        F = F * gains[:, None]
        x_spec = torch.fft.irfft(F, n=x.shape[0], dim=-1).T
        x = x + self.attn(self.ln1(x + x_spec))
        x = x + self.mlp(self.ln2(x))
        return x


class HWATv2Inference(nn.Module):
    def __init__(self, vocab_size, dim, n_blocks, n_heads, max_len):
        super().__init__()
        self.embed = EmbeddingV2(vocab_size, dim, max_len)
        self.blocks = nn.ModuleList([
            HWATBlockV2(dim, n_heads) for _ in range(n_blocks)
        ])
        self.ln_out = nn.LayerNorm(dim)
        self.lm_head = nn.Linear(dim, vocab_size)

    def forward(self, ids):
        x = self.embed(ids)
        for blk in self.blocks:
            x = blk(x)
        return self.lm_head(self.ln_out(x))

    def encode(self, ids) -> np.ndarray:
        """Retourne le vecteur [L, dim] après les blocs (avant tête LM)."""
        with torch.no_grad():
            x = self.embed(ids)
            for blk in self.blocks:
                x = blk(x)
            return self.ln_out(x).numpy()


# ════════════════════════════════════════════════════════════════
# 2. TOKENIZER (pur Python, pas de dépendance torch)
# ════════════════════════════════════════════════════════════════

class WordTokenizer:
    def __init__(self, word_to_id: dict, id_to_word: dict):
        self.word_to_id = word_to_id
        self.id_to_word = {int(k): v for k, v in id_to_word.items()}
        self.PAD = 0
        self.UNK = 1

    def encode(self, text: str) -> list:
        tokens = re.findall(r"[a-zA-ZÀ-ÿ]+|[^\s\w]", text.lower())
        return [self.word_to_id.get(t, self.UNK) for t in tokens]

    def decode(self, ids) -> str:
        if isinstance(ids, np.ndarray):
            ids = ids.tolist()
        return ' '.join(self.id_to_word.get(i, '?') for i in ids)

    @property
    def vocab_size(self):
        return len(self.word_to_id)


# ════════════════════════════════════════════════════════════════
# 3. API PUBLIQUE
# ════════════════════════════════════════════════════════════════

_model_cache = None
_tokenizer_cache = None


def load_hwat(model_path: str = None):
    """Charge le modèle HWAT entraîné.

    Returns:
        (model: HWATv2Inference, tokenizer: WordTokenizer)
    """
    global _model_cache, _tokenizer_cache
    if _model_cache is not None:
        return _model_cache, _tokenizer_cache

    if model_path is None:
        # Priorité : v3 naturel > v2 universel
        for candidate in ["hwat_v3_natural.pt", "hwat_v2.pt"]:
            p = _ENGINE / "data" / candidate
            if p.exists():
                model_path = str(p)
                break
        if model_path is None:
            raise FileNotFoundError("Aucun modèle trouvé dans data/")

    ckpt = torch.load(str(model_path), weights_only=False, map_location='cpu')

    # Tokenizer
    tk_data = ckpt['tokenizer']
    tokenizer = WordTokenizer(tk_data['word_to_id'], tk_data['id_to_word'])

    # Modèle
    cfg = ckpt['config']
    n_heads = cfg.get('n_heads', 4)
    model = HWATv2Inference(
        vocab_size=tk_data['vocab_size'],
        dim=cfg['dim'],
        n_blocks=cfg['n_blocks'],
        n_heads=n_heads,
        max_len=cfg['max_len']
    )
    model.load_state_dict(ckpt['model_state'])
    model.eval()

    _model_cache, _tokenizer_cache = model, tokenizer
    print(f"  ✅ HWAT chargé : {sum(p.numel() for p in model.parameters()):,} "
          f"params, vocab={tokenizer.vocab_size}")
    return model, tokenizer


def encode(text: str) -> np.ndarray:
    """Encode un texte → vecteur contextuel [L, dim]."""
    model, tok = load_hwat()
    ids = torch.tensor(tok.encode(text), dtype=torch.long)
    return model.encode(ids)


def generate(prompt: str, max_tokens: int = 30,
            temperature: float = 0.8, repetition_penalty: float = 1.2,
            top_k: int = 40) -> str:
    """Génère du texte à partir d'un prompt.

    Args:
        prompt: texte de départ
        max_tokens: nombre max de tokens à générer
        temperature: 0 = greedy, > 0 = sampling
        repetition_penalty: > 1 pénalise les tokens déjà vus
        top_k: nombre de tokens les plus probables à considérer (0 = tous)
    """
    model, tok = load_hwat()
    ids = tok.encode(prompt)
    max_len = model.embed.pos_enc.shape[0]
    seen = set(ids)
    recently_seen = []

    with torch.no_grad():
        for _ in range(max_tokens):
            x = torch.tensor(ids[-max_len:], dtype=torch.long)
            logits = model(x)
            next_logits = logits[-1] / max(temperature, 0.01)

            # Pénalité de répétition
            if repetition_penalty != 1.0:
                for tid in seen:
                    if next_logits[tid] < 0:
                        next_logits[tid] *= repetition_penalty
                    else:
                        next_logits[tid] /= repetition_penalty

            # Top-k filtering
            if top_k > 0:
                topk_vals, topk_idx = torch.topk(next_logits, min(top_k, len(next_logits)))
                mask = torch.ones_like(next_logits) * float('-inf')
                mask[topk_idx] = next_logits[topk_idx]
                next_logits = mask

            if temperature < 0.01:
                next_id = next_logits.argmax().item()
            else:
                probs = F.softmax(next_logits, dim=-1).numpy()
                probs = np.nan_to_num(probs, nan=0.0)
                s = probs.sum()
                if s > 0:
                    probs = probs / s
                    next_id = np.random.choice(len(probs), p=probs)
                else:
                    next_id = next_logits.argmax().item()

            ids.append(next_id)
            seen.add(next_id)
            recently_seen.append(next_id)
            if len(recently_seen) > 20:
                old = recently_seen.pop(0)
                if old not in recently_seen:
                    seen.discard(old)

            if next_id == tok.word_to_id.get('\n', -1):
                break

    return tok.decode(ids)


def perplexity(text: str) -> float:
    """Calcule la perplexité d'un texte sous le modèle."""
    model, tok = load_hwat()
    ids = tok.encode(text)
    if len(ids) < 2:
        return float('inf')

    x = torch.tensor(ids[:-1], dtype=torch.long)
    y = torch.tensor(ids[1:], dtype=torch.long)

    with torch.no_grad():
        logits = model(x)
        loss = F.cross_entropy(logits, y)
    return math.exp(loss.item())


# ════════════════════════════════════════════════════════════════
# 4. TEST END-TO-END
# ════════════════════════════════════════════════════════════════

def demo():
    print("═" * 60)
    print("  🌊 HWAT INFERENCE — Test end-to-end")
    print("═" * 60)

    # Charger
    model, tok = load_hwat()
    print(f"  Modèle : dim={model.embed.token_emb.weight.shape[1]}, "
          f"blocs={len(model.blocks)}")

    # Encodage
    v = encode("théorème de superposition")
    print(f"  Encode 'théorème de superposition' → vecteur {v.shape}")

    # Génération
    prompts = [
        "théorème de",
        "loi de",
        "équation",
        "principe",
    ]
    print(f"\n  Générations :")
    for p in prompts:
        gen = generate(p, max_tokens=20, temperature=0.7)
        print(f"  > {gen[:100]}")

    # Perplexité
    ppl = perplexity("théorème de Pythagore est_un_concept_de Mathématiques")
    print(f"\n  Perplexité : {ppl:.1f}")

    print(f"\n  ✅ HWAT prêt à être intégré.")


if __name__ == "__main__":
    demo()
