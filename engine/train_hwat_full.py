"""
🌊 train_hwat_full.py — HWAT à l'échelle sur 750K faits + Wikipédia
=====================================================================
Utilise TOUTES les données disponibles pour entraîner un HWAT
de taille réelle (~15M params).

Sources :
  - 250K faits structurés (knowledge_base_300k.npz)
  - 2×250K faits additionnels (kb_shards)
  - 594 MB Wikipédia français (wikipedia_fr_merged.txt)

Pipeline :
  1. Charger faits → convertir en phrases naturelles
  2. Charger Wikipédia → découper en phrases
  3. Tokenisation mots (vocab 30K)
  4. Entraînement HWAT (dim=128, blocs=4, epochs=5)
  5. Sauvegarde + évaluation

Lancer : python train_hwat_full.py
"""

import sys, math, time, os, re, json, random, gc
from pathlib import Path
from collections import Counter
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

import torch
import torch.nn as nn
import torch.nn.functional as F

# ════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════

DIM = 64
N_BLOCKS = 2
N_HEADS = 4
MAX_LEN = 32
LR = 0.001
EPOCHS = 2
MAX_FACTS = 10000
MAX_WIKI_CHARS = 200_000
MAX_VOCAB = 5000
PRINT_EVERY = 100

PHI = 1.618033988749895
TAU = 2.0 * math.pi


# ════════════════════════════════════════════════════════════════
# 1. CHARGEMENT DES DONNÉES
# ════════════════════════════════════════════════════════════════

def load_facts(max_facts: int = None) -> list:
    """Charge les faits depuis les fichiers NPZ."""
    facts = []

    # Source 1: knowledge_base_300k
    path1 = _ENGINE / "data" / "bootstrapper_output" / "knowledge_base_300k.npz"
    if path1.exists():
        data = np.load(str(path1), allow_pickle=True)
        arr = data[list(data.keys())[0]]
        for i in range(min(len(arr), max_facts or len(arr))):
            s, r, o, sec = arr[i]
            facts.append((str(s), str(r), str(o), str(sec)))
        print(f"  knowledge_base_300k: {len(facts):,} faits chargés")

    # Source 2: kb_shards (si plus de faits nécessaires)
    if max_facts and len(facts) >= max_facts:
        return facts[:max_facts]

    for shard_name in ['shard_0000.npz', 'shard_0001.npz']:
        path = _ENGINE / "data" / "kb_shards" / shard_name
        if path.exists() and (max_facts is None or len(facts) < max_facts):
            data = np.load(str(path), allow_pickle=True)
            arr = data[list(data.keys())[0]]
            remaining = (max_facts - len(facts)) if max_facts else len(arr)
            for i in range(min(len(arr), remaining)):
                if len(arr[i]) >= 4:
                    s, r, o = arr[i][0], arr[i][1], arr[i][2]
                    sec = arr[i][3] if len(arr[i]) > 3 else "GENERAL"
                    facts.append((str(s), str(r), str(o), str(sec)))
            print(f"  {shard_name}: +{min(len(arr), remaining):,} faits")

    return facts[:max_facts] if max_facts else facts


def load_wikipedia(max_chars: int = None) -> str:
    """Charge le texte Wikipédia français."""
    path = _ENGINE / "data" / "corpora" / "wikipedia_fr_merged.txt"
    if not path.exists():
        print("  Wikipédia non trouvé, skip")
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        if max_chars:
            text = f.read(max_chars)
        else:
            text = f.read()
    print(f"  Wikipédia: {len(text):,} caractères")
    return text


# ════════════════════════════════════════════════════════════════
# 2. CONVERSION FAITS → PHRASES NATURELLES
# ════════════════════════════════════════════════════════════════

FACT_TEMPLATES_FR = {
    "est_un": ["{sujet} est {objet}.", "{sujet} constitue {objet}."],
    "a_découvert": [
        "{sujet} a découvert {objet}.",
        "{objet} a été découvert par {sujet}.",
        "La découverte de {objet} est due à {sujet}."
    ],
    "a_écrit": ["{sujet} a écrit {objet}.", "{objet} est l'œuvre de {sujet}."],
    "a_inventé": ["{sujet} a inventé {objet}.", "{objet} fut inventé par {sujet}."],
    "signifie": ["{sujet} signifie {objet}.", "Le terme {sujet} veut dire {objet}."],
    "vaut": ["{sujet} vaut {objet}.", "La valeur de {sujet} est {objet}."],
    "contient": ["{sujet} contient {objet}.", "{objet} se trouve dans {sujet}."],
    "fait_partie_de": ["{sujet} fait partie de {objet}.", "{objet} inclut {sujet}."],
    "a_eu_lieu_en": ["{sujet} a eu lieu en {objet}.", "{sujet} s'est déroulé en {objet}."],
    "a_été_construit_en": ["{sujet} a été construit en {objet}."],
    "a_commencé_en": ["{sujet} a commencé en {objet}."],
    "a_pris_fin_en": ["{sujet} a pris fin en {objet}."],
    "a_une_population_de": ["{sujet} a une population de {objet}."],
    "a_une_superficie_de": ["{sujet} a une superficie de {objet}."],
    "constitue": ["{sujet} constitue {objet}.", "{objet} est constitué de {sujet}."],
    "DEFAULT": ["{sujet} est lié à {objet}.", "Il y a un lien entre {sujet} et {objet}."]
}


def fact_to_sentences(fact: tuple) -> list:
    """Convertit un fait en 1-3 phrases naturelles françaises."""
    sujet, relation, objet, secteur = fact
    sujet = sujet.strip().strip('"\'')
    objet = objet.strip().strip('"\'')
    relation_clean = relation.strip().lower().replace(' ', '_')

    # Chercher le template le plus proche
    templates = None
    for key, tmpls in FACT_TEMPLATES_FR.items():
        if key in relation_clean:
            templates = tmpls
            break

    if templates is None:
        templates = FACT_TEMPLATES_FR["DEFAULT"]

    sentences = []
    for tmpl in templates[:3]:  # max 3 variantes
        try:
            sent = tmpl.format(sujet=sujet, objet=objet)
            sentences.append(sent)
        except Exception:
            pass

    return sentences if sentences else [f"{sujet} {relation} {objet}."]


def build_corpus(facts: list, wiki_text: str) -> str:
    """Construit le corpus d'entraînement complet."""
    sentences = []

    # Faits → phrases
    for i, fact in enumerate(facts):
        sents = fact_to_sentences(fact)
        sentences.extend(sents)
        if (i + 1) % 25000 == 0:
            print(f"  Faits convertis: {i+1:,}/{len(facts):,}")

    print(f"  Phrases de faits: {len(sentences):,}")

    # Wikipédia → phrases
    if wiki_text:
        wiki_sents = [s.strip() + '.' for s in re.split(r'[.!?\n]+', wiki_text)
                     if len(s.strip()) > 30]
        # En prendre un échantillon
        wiki_sents = wiki_sents[:len(sentences)]  # équilibrer faits/wiki
        sentences.extend(wiki_sents)
        print(f"  Phrases Wikipédia: {len(wiki_sents):,}")

    # Mélanger
    random.shuffle(sentences)
    text = '\n'.join(sentences)
    print(f"  Corpus total: {len(sentences):,} phrases, {len(text):,} caractères")
    return text


# ════════════════════════════════════════════════════════════════
# 3. TOKENISATION + MODÈLE (réutilise train_hwat_v2.py)
# ════════════════════════════════════════════════════════════════

# [Les classes EmbeddingV2, PhaseAttentionV2, HWATBlockV2, HWATv2,
#  BaselineTransformer sont importées de train_hwat_v2.py]
from train_hwat_v2 import (
    EmbeddingV2, PhaseAttentionV2, HWATBlockV2, HWATv2,
    BaselineTransformer, WordTokenizer, build_batches
)


def train_model_simple(model, batches, name, epochs=EPOCHS):
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()
    losses = []
    t0 = time.time()

    for epoch in range(1, epochs + 1):
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
                losses.append((epoch + bidx/len(batches), avg, ppl))

        avg = epoch_loss / len(batches)
        ppl = math.exp(avg)
        dt = time.time() - t0
        print(f"  [{name}] Epoch {epoch}/{epochs} — Loss: {avg:.4f}, "
              f"PPL: {ppl:.1f}, Time: {dt:.1f}s")

    return losses


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print("═" * 65)
    print("  🌊 HWAT FULL — Entraînement à l'échelle")
    print("═" * 65)

    # 1. Charger les données
    print("\n📂 Chargement des données...")
    facts = load_facts(max_facts=MAX_FACTS)
    wiki_text = load_wikipedia(max_chars=MAX_WIKI_CHARS)
    print(f"  Total faits: {len(facts):,}")

    # 2. Construire le corpus
    print("\n📝 Construction du corpus...")
    corpus_text = build_corpus(facts, wiki_text)

    # 3. Tokenisation
    print("\n🔤 Tokenisation...")
    tokenizer = WordTokenizer(corpus_text, min_freq=3, max_vocab=MAX_VOCAB)
    ids = tokenizer.encode(corpus_text)
    print(f"  Vocabulaire: {tokenizer.vocab_size} mots")
    print(f"  Tokens: {len(ids):,}")

    # 4. Batches
    batches = build_batches(ids, MAX_LEN)
    print(f"  Batches: {len(batches):,}")

    # 5. Modèle
    V = tokenizer.vocab_size
    print(f"\n🧠 Construction du modèle (dim={DIM}, blocs={N_BLOCKS})...")
    hwat = HWATv2(V, dim=DIM, n_blocks=N_BLOCKS, max_len=MAX_LEN)
    n_params = sum(p.numel() for p in hwat.parameters())
    print(f"  HWAT: {n_params:,} paramètres")

    # 6. Entraînement
    print(f"\n🏋️ Entraînement ({EPOCHS} époques)...")
    losses = train_model_simple(hwat, batches, "HWAT", epochs=EPOCHS)

    # 7. Sauvegarde
    save_path = _ENGINE / "data" / "hwat_full.pt"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        'model_state': hwat.state_dict(),
        'tokenizer': {
            'word_to_id': tokenizer.word_to_id,
            'id_to_word': tokenizer.id_to_word,
            'vocab_size': tokenizer.vocab_size,
        },
        'config': {
            'dim': DIM, 'n_blocks': N_BLOCKS, 'n_heads': N_HEADS,
            'max_len': MAX_LEN
        },
        'losses': losses,
    }, str(save_path))
    print(f"\n  ✅ Modèle sauvegardé: {save_path}")

    # 8. Stats finales
    if losses:
        print(f"\n{'═'*65}")
        print(f"  RÉSULTATS")
        print(f"{'═'*65}")
        print(f"  Loss initiale : {losses[0][1]:.4f}")
        print(f"  Loss finale   : {losses[-1][1]:.4f}")
        print(f"  PPL initiale  : {losses[0][2]:.1f}")
        print(f"  PPL finale    : {losses[-1][2]:.1f}")
        print(f"  Réduction     : {(losses[0][1]-losses[-1][1])/losses[0][1]*100:.1f}%")
        print(f"  Params        : {n_params:,}")
        print(f"  Vocab         : {tokenizer.vocab_size}")


if __name__ == "__main__":
    main()
