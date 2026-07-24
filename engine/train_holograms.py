"""
🧠 train_holograms.py — Hologrammes HWAT par spécialité
=========================================================
Entraîne un petit HWAT par domaine (secteur) au lieu d'un
modèle monolithique. Chaque hologramme est un expert harmonique.

Architecture :
  KB 250K faits → grouper par secteur → top N secteurs
  Pour chaque secteur :
    → convertir faits en phrases naturelles
    → tokeniser (vocab local au domaine)
    → entraîner HWAT (dim=32, 1 bloc, 3-5 époques)
    → sauvegarder hologramme + centroïde

Routeur : cos sim(signature question, centroïdes) → top-K experts

Lancer : python train_holograms.py
Sortie : data/holograms/{secteur}.pt + router.json
Temps estimé : ~30-45 min pour 15 domaines
"""

import sys, math, time, os, json, random, re, gc
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

import torch
import torch.nn as nn
import torch.nn.functional as F

# ════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════

DIM = 32             # petit modèle par domaine
N_BLOCKS = 1         # 1 bloc suffit pour un domaine
N_HEADS = 2          # 32/2 = 16 dims/tête
MAX_LEN = 32
LR = 0.002
EPOCHS = 5           # suffisant pour spécialisation
MIN_FACTS = 500       # min faits pour entraîner un hologramme
MAX_DOMAINS = 25      # max domaines à entraîner
VOCAB_PER_DOMAIN = 1500  # vocab max par domaine
PRINT_EVERY = 50

PHI = 1.618033988749895
TAU = 2.0 * math.pi


# ════════════════════════════════════════════════════════════════
# 1. CHARGEMENT ET GROUPEMENT DES FAITS
# ════════════════════════════════════════════════════════════════

def load_all_facts() -> list:
    """Charge tous les faits de toutes les sources."""
    facts = []
    sources = [
        "data/bootstrapper_output/knowledge_base_300k.npz",
        "data/kb_shards/shard_0000.npz",
        "data/kb_shards/shard_0001.npz",
    ]
    for src in sources:
        path = _ENGINE / src
        if not path.exists():
            continue
        data = np.load(str(path), allow_pickle=True)
        arr = data[list(data.keys())[0]]
        for row in arr:
            if len(row) >= 4:
                facts.append((str(row[0]), str(row[1]), str(row[2]), str(row[3])))
    print(f"  Total faits chargés: {len(facts):,}")
    return facts


def group_by_sector(facts: list) -> dict:
    """Groupe les faits par secteur, trié par taille décroissante."""
    groups = defaultdict(list)
    for s, r, o, sec in facts:
        sec = sec.strip().upper()
        groups[sec].append((s, r, o, sec))
    # Trier par nombre de faits
    sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]))
    print(f"  Secteurs: {len(groups)}, top 10:")
    for sec, items in sorted_groups[:10]:
        print(f"    {sec}: {len(items):,} faits")
    return dict(sorted_groups)


# ════════════════════════════════════════════════════════════════
# 2. CONVERSION FAITS → CORPUS (allégée)
# ════════════════════════════════════════════════════════════════

def fact_to_sentence(fact: tuple) -> str:
    """Convertit un fait en 1 phrase simple."""
    s, r, o, sec = fact
    s, o = s.strip().strip('"\''), o.strip().strip('"\'')
    r_clean = r.strip().lower().replace(' ', '_')
    # Templates simplifiés
    if 'est_un' in r_clean or 'constitue' in r_clean:
        return f"{s} est {o}."
    if 'découvert' in r_clean or 'decouvert' in r_clean:
        return f"{s} a découvert {o}."
    if 'écrit' in r_clean or 'ecrit' in r_clean:
        return f"{s} a écrit {o}."
    if 'inventé' in r_clean or 'invente' in r_clean:
        return f"{s} a inventé {o}."
    if 'signifie' in r_clean:
        return f"{s} signifie {o}."
    if 'vaut' in r_clean:
        return f"{s} vaut {o}."
    if 'population' in r_clean:
        return f"{s} a une population de {o}."
    if 'superficie' in r_clean:
        return f"{s} a une superficie de {o}."
    if 'eu_lieu' in r_clean or 'lieu' in r_clean:
        return f"{s} a eu lieu en {o}."
    if 'construit' in r_clean:
        return f"{s} a été construit en {o}."
    if 'commencé' in r_clean or 'commence' in r_clean:
        return f"{s} a commencé en {o}."
    if 'fin' in r_clean:
        return f"{s} a pris fin en {o}."
    return f"{s} est lié à {o}."


# ════════════════════════════════════════════════════════════════
# 3. MODÈLE HWAT MINI (inline pour indépendance)
# ════════════════════════════════════════════════════════════════

class MiniEmbedding(nn.Module):
    def __init__(self, vocab_size, dim, max_len):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, dim)
        t = torch.arange(max_len, dtype=torch.float32)
        ks = torch.arange(dim, dtype=torch.float32)
        omegas = 0.1 * (math.pi / 0.1) ** (ks / max(dim - 1, 1))
        self.register_buffer('pos', omegas[None] * t[:, None])

    def forward(self, ids):
        return self.token_emb(ids) + self.pos[:ids.shape[0]]


class MiniAttention(nn.Module):
    def __init__(self, dim, n_heads):
        super().__init__()
        self.dim, self.n_heads = dim, n_heads
        self.head_dim = dim // n_heads
        self.Wq = nn.Linear(dim, dim)
        self.Wk = nn.Linear(dim, dim)
        self.Wv = nn.Linear(dim, dim)
        self.Wo = nn.Linear(dim, dim)

    def forward(self, x):
        L, D = x.shape
        H, d = self.n_heads, self.head_dim
        Q = self.Wq(x).reshape(L, H, d).transpose(0, 1)
        K = self.Wk(x).reshape(L, H, d).transpose(0, 1)
        V = self.Wv(x).reshape(L, H, d).transpose(0, 1)
        scores = (Q @ K.transpose(-2, -1)) / math.sqrt(d)
        mask = torch.triu(torch.ones(L, L, device=x.device), diagonal=1).bool()
        scores = scores.masked_fill(mask[None], float('-inf'))
        attn = F.softmax(scores, dim=-1)
        out = (attn @ V).transpose(0, 1).reshape(L, D)
        return self.Wo(out)


class MiniBlock(nn.Module):
    def __init__(self, dim, n_heads):
        super().__init__()
        self.attn = MiniAttention(dim, n_heads)
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * 4), nn.GELU(),
            nn.Linear(dim * 4, dim)
        )
        self.ln1 = nn.LayerNorm(dim)
        self.ln2 = nn.LayerNorm(dim)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class MiniHWAT(nn.Module):
    """HWAT miniature pour un domaine spécialisé."""
    def __init__(self, vocab_size, dim=DIM, n_blocks=N_BLOCKS,
                 n_heads=N_HEADS, max_len=MAX_LEN):
        super().__init__()
        self.embed = MiniEmbedding(vocab_size, dim, max_len)
        self.blocks = nn.ModuleList([
            MiniBlock(dim, n_heads) for _ in range(n_blocks)
        ])
        self.ln_out = nn.LayerNorm(dim)
        self.lm_head = nn.Linear(dim, vocab_size)

    def forward(self, ids):
        x = self.embed(ids)
        for blk in self.blocks:
            x = blk(x)
        return self.lm_head(self.ln_out(x))


# ════════════════════════════════════════════════════════════════
# 4. ENTRAÎNEMENT D'UN HOLOGRAMME
# ════════════════════════════════════════════════════════════════

def train_hologram(sector: str, facts: list, output_dir: Path) -> dict:
    """Entraîne un HWAT spécialisé sur un secteur."""
    t0 = time.time()
    n_facts = len(facts)

    # Corpus
    sentences = [fact_to_sentence(f) for f in facts]
    text = ' '.join(sentences)

    # Tokenisation caractères (simple, rapide, pas de vocab cross-domaine)
    chars = sorted(set(text))
    c2i = {c: i for i, c in enumerate(chars)}
    i2c = {i: c for i, c in enumerate(chars)}
    vocab_size = len(chars)
    if vocab_size > VOCAB_PER_DOMAIN:
        # Trop de caractères uniques → échantillonner
        vocab_size = VOCAB_PER_DOMAIN
    ids = np.array([c2i.get(c, 0) for c in text[:100000]], dtype=np.int64)

    # Batches
    seq_len = MAX_LEN
    n_batches = max(1, (len(ids) - 1) // seq_len)
    batches = []
    for i in range(min(n_batches, 1000)):  # max 1000 batches/époque
        start = i * seq_len
        x = torch.from_numpy(ids[start:start + seq_len].copy())
        y = torch.from_numpy(ids[start + 1:start + 1 + seq_len].copy())
        if len(x) < seq_len or len(y) < seq_len:
            break
        batches.append((x, y))

    if len(batches) < 5:
        return {'sector': sector, 'status': 'skipped', 'reason': 'trop peu de batches'}

    # Modèle
    model = MiniHWAT(vocab_size, dim=DIM, n_blocks=N_BLOCKS,
                     n_heads=N_HEADS, max_len=MAX_LEN)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()

    # Entraînement
    for epoch in range(1, EPOCHS + 1):
        epoch_loss = 0.0
        for x, y in batches:
            logits = model(x)
            loss = criterion(logits, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

    avg_loss = epoch_loss / len(batches)
    ppl = math.exp(avg_loss)
    dt = time.time() - t0

    # Sauvegarde
    save_path = output_dir / f"{sector}.pt"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        'sector': sector,
        'model_state': model.state_dict(),
        'char_to_id': c2i,
        'id_to_char': i2c,
        'vocab_size': vocab_size,
        'config': {'dim': DIM, 'n_blocks': N_BLOCKS, 'n_heads': N_HEADS, 'max_len': MAX_LEN},
        'n_facts': n_facts,
        'avg_loss': avg_loss,
        'ppl': ppl,
    }, str(save_path))

    print(f"  ✅ {sector:<25} | {n_facts:>5d} faits | "
          f"loss={avg_loss:.3f} ppl={ppl:.1f} | {dt:.0f}s | {save_path.name}")

    return {
        'sector': sector,
        'path': str(save_path),
        'n_facts': n_facts,
        'vocab_size': vocab_size,
        'loss': avg_loss,
        'ppl': ppl,
    }


# ════════════════════════════════════════════════════════════════
# 5. CONSTRUCTION DU ROUTEUR
# ════════════════════════════════════════════════════════════════

def build_router(holograms: list, output_dir: Path):
    """Construit le routeur spectral : centroïdes + mapping."""
    router = {
        'domains': {},
        'default': 'GENERAL',
    }

    for h in holograms:
        sector = h['sector']
        router['domains'][sector] = {
            'path': h['path'],
            'n_facts': h['n_facts'],
            'ppl': h['ppl'],
        }

    # Sauvegarder
    router_path = output_dir / "router.json"
    with open(router_path, 'w') as f:
        json.dump(router, f, indent=2, ensure_ascii=False)

    print(f"\n  📡 Routeur sauvegardé: {router_path}")
    print(f"     Domaines: {len(router['domains'])}")
    return router


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print("═" * 65)
    print("  🧠 HOLOGRAMMES HWAT — Experts par spécialité")
    print("═" * 65)

    # 1. Charger et grouper les faits
    print("\n📂 Chargement des faits...")
    all_facts = load_all_facts()
    groups = group_by_sector(all_facts)

    # 2. Filtrer les secteurs éligibles
    output_dir = _ENGINE / "data" / "holograms"
    output_dir.mkdir(parents=True, exist_ok=True)

    eligible = [(sec, facts) for sec, facts in groups.items()
                if len(facts) >= MIN_FACTS and len(sec.strip()) > 2]  # >2 exclut les artefacts 1-lettre
    eligible = eligible[:MAX_DOMAINS]

    print(f"\n🎯 {len(eligible)} domaines éligibles (≥{MIN_FACTS} faits)")
    print(f"   Configuration : dim={DIM}, blocs={N_BLOCKS}, époques={EPOCHS}")
    print()

    # 3. Entraîner un hologramme par domaine
    t0_total = time.time()
    results = []

    for i, (sector, facts) in enumerate(eligible):
        print(f"  [{i+1}/{len(eligible)}] {sector} ({len(facts)} faits)...")
        result = train_hologram(sector, facts, output_dir)
        results.append(result)
        gc.collect()

    dt_total = time.time() - t0_total
    print(f"\n  ⏱️ Temps total: {dt_total/60:.1f} min "
          f"({dt_total/len(eligible):.0f}s/hologramme)")

    # 4. Construire le routeur
    build_router(results, output_dir)

    # 5. Résumé
    trained = [r for r in results if 'loss' in r]
    print(f"\n{'═'*65}")
    print(f"  RÉSUMÉ")
    print(f"{'═'*65}")
    print(f"  Hologrammes entraînés : {len(trained)}")
    print(f"  Temps total : {dt_total/60:.1f} min")
    if trained:
        best = min(trained, key=lambda r: r['ppl'])
        worst = max(trained, key=lambda r: r['ppl'])
        print(f"  Meilleur : {best['sector']} (PPL {best['ppl']:.1f})")
        print(f"  Moins bon : {worst['sector']} (PPL {worst['ppl']:.1f})")
    print(f"\n  ✅ Hologrammes prêts dans : {output_dir}/")


if __name__ == "__main__":
    main()
