"""
🖥️ train_code_hologram.py — Hologramme CODE sur corpus élargi
===============================================================
Combine TOUTES les sources de code disponibles :
  1. KB CODE : 10 442 faits structurés
  2. code_corpus_massive.npz : 2 798 snippets (description + code)
  3. code_corpus.npz : 548 snippets
  4. Patterns extraits des fichiers .py du workspace

Entraîne un HWAT CODE de taille réelle (dim=64, blocs=2, époques=10)
pour la génération de code.

Lancer : python train_code_hologram.py
Sortie : data/holograms/CODE.pt (remplace l'ancien)
"""

import sys, math, time, os, json, re, random
from pathlib import Path
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

import torch
import torch.nn as nn
import torch.nn.functional as F

# ════════════════════════════════════════════════════════════════
# CONFIG — Modèle plus gros pour le code
# ════════════════════════════════════════════════════════════════

DIM = 64             # ×2 vs hologrammes standard
N_BLOCKS = 2         # ×2 vs standard
N_HEADS = 4
MAX_LEN = 48
LR = 0.001
EPOCHS = 8           # époques
PRINT_EVERY = 300
VOCAB_SIZE = 1500    # caractères
MAX_BATCHES = 2500   # limite pour la vitesse


# ════════════════════════════════════════════════════════════════
# 1. CHARGEMENT DE TOUTES LES SOURCES
# ════════════════════════════════════════════════════════════════

def load_code_corpus() -> str:
    """Charge et combine toutes les sources de code."""
    sentences = []

    # ── Source 1 : KB CODE faits (10 442) ──
    kb_path = _ENGINE / "data" / "bootstrapper_output" / "knowledge_base_300k.npz"
    if kb_path.exists():
        data = np.load(str(kb_path), allow_pickle=True)
        facts = data['facts']
        code_facts = [f for f in facts if f[3] == 'CODE']
        print(f"  KB CODE: {len(code_facts)} faits")

        for s, r, o, sec in code_facts:
            s, r, o = str(s).strip(), str(r).strip(), str(o).strip()
            # Convertir en phrases techniques
            if 'bug' in r.lower() or 'error' in r.lower():
                sentences.append(f"Bug: {s} — {o}")
            elif 'fonction' in r.lower() or 'function' in r.lower():
                sentences.append(f"Fonction {s}: {o}")
            elif 'api' in r.lower():
                sentences.append(f"API {s} → {o}")
            else:
                sentences.append(f"{s} {r} {o}")

    # ── Source 2 : code_corpus_massive.npz (2 798 snippets) ──
    massive_path = _ENGINE / "data" / "corpus" / "code_corpus_massive.npz"
    if massive_path.exists():
        data = np.load(str(massive_path), allow_pickle=True)
        descriptions = data['descriptions']
        codes = data['codes']
        languages = data['languages']
        print(f"  code_corpus_massive: {len(descriptions)} snippets")

        for desc, code, lang in zip(descriptions, codes, languages):
            desc, code, lang = str(desc).strip(), str(code).strip(), str(lang).strip()
            # Format : description + code
            sentences.append(f"// {desc} ({lang})")
            # Ajouter le code ligne par ligne (max 10 lignes)
            for line in code.split('\n')[:10]:
                line = line.strip()
                if line and not line.startswith('//'):
                    sentences.append(line)

    # ── Source 3 : code_corpus.npz (548 snippets) ──
    corpus_path = _ENGINE / "data" / "corpus" / "code_corpus.npz"
    if corpus_path.exists():
        data = np.load(str(corpus_path), allow_pickle=True)
        descriptions = data['descriptions']
        codes = data['codes']
        print(f"  code_corpus: {len(descriptions)} snippets")

        for desc, code in zip(descriptions, codes):
            desc, code = str(desc).strip(), str(code).strip()
            sentences.append(f"// {desc}")
            for line in code.split('\n')[:8]:
                line = line.strip()
                if line and not line.startswith('//'):
                    sentences.append(line)

    # ── Source 4 : Patterns depuis les .py du workspace ──
    py_files = list(_ENGINE.glob("code_*.py")) + list(_ENGINE.glob("wave_*.py"))
    py_files = [f for f in py_files if f.stat().st_size < 50000][:5]
    py_snippets = 0
    for pyf in py_files:
        try:
            with open(pyf, 'r', encoding='utf-8') as f:
                content = f.read()
            # Extraire les fonctions comme patterns
            funcs = re.findall(r'def (\w+)\([^)]*\):', content)
            for func in funcs:
                sentences.append(f"def {func}(): # fonction Python")
                py_snippets += 1
        except Exception:
            pass
    print(f"  Patterns .py: {py_snippets} fonctions")

    # ── Assemblage ──
    text = '\n'.join(sentences)
    print(f"  Corpus total: {len(sentences):,} lignes, {len(text):,} caractères")
    return text


# ════════════════════════════════════════════════════════════════
# 2. MODÈLE HWAT (réutilise train_holograms.py)
# ════════════════════════════════════════════════════════════════

from train_holograms import MiniHWAT, MiniEmbedding, MiniBlock, MiniAttention


def train_code_model(corpus_text: str, output_path: Path):
    """Entraîne un HWAT CODE sur le corpus élargi."""

    # Tokenisation caractères
    chars = sorted(set(corpus_text))[:VOCAB_SIZE]
    c2i = {c: i for i, c in enumerate(chars)}
    i2c = {i: c for i, c in enumerate(chars)}
    vocab_size = len(chars)
    print(f"  Vocab: {vocab_size} caractères")

    # Encodage
    text_sample = corpus_text[:200000]  # max 200K chars pour la vitesse
    ids = np.array([c2i.get(c, 0) for c in text_sample], dtype=np.int64)

    # Batches
    seq_len = MAX_LEN
    n_batches = min(MAX_BATCHES, (len(ids) - 1) // seq_len)
    batches = []
    for i in range(n_batches):
        start = i * seq_len
        x = torch.from_numpy(ids[start:start + seq_len].copy())
        y = torch.from_numpy(ids[start + 1:start + 1 + seq_len].copy())
        if len(x) < seq_len or len(y) < seq_len:
            break
        batches.append((x, y))

    print(f"  Batches: {len(batches)}")

    # Modèle
    model = MiniHWAT(vocab_size, dim=DIM, n_blocks=N_BLOCKS,
                     n_heads=N_HEADS, max_len=MAX_LEN)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  Params: {n_params:,}")

    # Entraînement
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()
    t0 = time.time()

    for epoch in range(1, EPOCHS + 1):
        epoch_loss = 0.0
        for bidx, (x, y) in enumerate(batches):
            logits = model(x)
            loss = criterion(logits, y)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item()

            if (bidx + 1) % PRINT_EVERY == 0:
                avg = epoch_loss / (bidx + 1)
                ppl = math.exp(avg)
                elapsed = time.time() - t0
                print(f"  E{epoch:02d} B{bidx+1:>5d} | loss={avg:.4f} "
                      f"ppl={ppl:.1f} | {elapsed:.0f}s")

        avg_loss = epoch_loss / len(batches)
        ppl = math.exp(avg_loss)
        dt = time.time() - t0
        print(f"  ── EPOCH {epoch}/{EPOCHS} ── Loss: {avg_loss:.4f}, "
              f"PPL: {ppl:.1f}, Time: {dt:.0f}s ──")

        # Checkpoint toutes les 2 époques
        if epoch % 2 == 0:
            ckpt_path = output_path.with_suffix(f".epoch{epoch}.pt")
            torch.save({
                'sector': 'CODE', 'model_state': model.state_dict(),
                'char_to_id': c2i, 'id_to_char': i2c,
                'vocab_size': vocab_size,
                'config': {'dim': DIM, 'n_blocks': N_BLOCKS, 'n_heads': N_HEADS,
                           'max_len': MAX_LEN},
                'epoch': epoch, 'avg_loss': avg_loss, 'ppl': ppl,
            }, str(ckpt_path))
            print(f"  💾 Checkpoint: {ckpt_path.name}")

    # Sauvegarde
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        'sector': 'CODE',
        'model_state': model.state_dict(),
        'char_to_id': c2i,
        'id_to_char': i2c,
        'vocab_size': vocab_size,
        'config': {'dim': DIM, 'n_blocks': N_BLOCKS, 'n_heads': N_HEADS,
                   'max_len': MAX_LEN},
        'n_facts': len(batches),
        'avg_loss': avg_loss,
        'ppl': ppl,
        'n_params': n_params,
    }, str(output_path))

    print(f"\n  ✅ Hologramme CODE sauvegardé: {output_path}")
    print(f"     Params: {n_params:,}, PPL: {ppl:.1f}")
    return model, c2i, i2c


# ════════════════════════════════════════════════════════════════
# 3. TEST DE GÉNÉRATION
# ════════════════════════════════════════════════════════════════

def test_generation(model, c2i: dict, i2c: dict, prompts: list):
    """Teste la génération de code."""
    print(f"\n{'═'*55}")
    print(f"  TEST GÉNÉRATION CODE")
    print(f"{'═'*55}")

    for prompt in prompts:
        ids = [c2i.get(c, 0) for c in prompt]
        ids = ids[-MAX_LEN:] if len(ids) > MAX_LEN else [0]*(MAX_LEN-len(ids)) + ids

        generated = []
        with torch.no_grad():
            for _ in range(60):
                x = torch.tensor(ids[-MAX_LEN:], dtype=torch.long)
                logits = model(x)
                # Top-k sampling
                topk = torch.topk(logits[-1], min(20, len(logits[-1])))
                probs = F.softmax(topk.values, dim=-1).numpy()
                idx = np.random.choice(len(probs), p=probs)
                next_id = topk.indices[idx].item()
                ids.append(next_id)
                generated.append(next_id)
                if i2c[next_id] == '\n' and len(generated) > 15:
                    break

        code = ''.join(i2c.get(i, '?') for i in generated)
        print(f"  > {prompt}")
        print(f"  {code[:120]}")
        print()


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print("═" * 55)
    print("  🖥️  HOLOGRAMME CODE — Entraînement sur corpus élargi")
    print("═" * 55)
    print(f"  Config: dim={DIM}, blocs={N_BLOCKS}, époques={EPOCHS}")

    # Charger corpus
    print("\n📂 Chargement des sources...")
    corpus = load_code_corpus()

    # Entraîner
    print(f"\n🏋️ Entraînement...")
    output_path = _ENGINE / "data" / "holograms" / "CODE.pt"
    model, c2i, i2c = train_code_model(corpus, output_path)

    # Tester
    test_generation(model, c2i, i2c, [
        "def reverse_string",
        "function sortArray",
        "import numpy",
        "class UserService",
        "// SQL query",
        "<div class=",
    ])

    print("✅ Hologramme CODE prêt.")


if __name__ == "__main__":
    main()
