"""
🔤 train_medical_tokenizer.py — Entraînement tokenizer BPE médical
=================================================================
Entraîne un tokenizer Byte-Pair Encoding (BPE) sur le corpus médical
pour HWAT-Med. Vocabulaire cible: 50k tokens.

Basé sur tokenizers (Rust) via Python bindings - ultra rapide.
"""

import sys
from pathlib import Path

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

# Vérifier tokenizers
try:
    from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders, normalizers
    from tokenizers.processors import TemplateProcessing
except ImportError:
    print("❌ 'tokenizers' non installé. Installer: pip install tokenizers")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

VOCAB_SIZE = 50000
MIN_FREQUENCY = 2
SPECIAL_TOKENS = [
    "<pad>", "<unk>", "<bos>", "<eos>", "<mask>",
    "<med>", "<diag>", "<rx>", "<dose>", "<icd10>",  # Tokens médicaux spéciaux
    "<fr>", "<en>", "<wo>", "<bm>", "<ha>",           # Langues africaines
]

CORPUS_FILES = [
    "data/medical_corpus/train.txt",
    "data/medical_corpus/val.txt",
]

OUTPUT_DIR = _ENGINE / "tokenizer_medical_50k"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRAÎNEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def train_tokenizer():
    print("═" * 70)
    print(f"  🔤 ENTRAÎNEMENT TOKENIZER BPE MÉDICAL — {VOCAB_SIZE:,} tokens")
    print("═" * 70)
    
    # Vérifier fichiers corpus
    corpus_paths = [_ENGINE / f for f in CORPUS_FILES]
    for p in corpus_paths:
        if not p.exists():
            print(f"❌ Fichier manquant: {p}")
            return 1
        print(f"  📄 Corpus: {p} ({p.stat().st_size/1e6:.1f} MB)")
    
    # Initialiser tokenizer BPE
    tokenizer = Tokenizer(models.BPE(unk_token="<unk>"))
    
    # Normalisation : NFD + lowercase + strip accents (optionnel pour médical)
    tokenizer.normalizer = normalizers.Sequence([
        normalizers.NFD(),
        normalizers.Lowercase(),
        normalizers.StripAccents(),
    ])
    
    # Pre-tokenization : split sur whitespace + ponctuation
    tokenizer.pre_tokenizer = pre_tokenizers.Sequence([
        pre_tokenizers.Whitespace(),
        pre_tokenizers.Punctuation(),
    ])
    
    # Décodeur BPE
    tokenizer.decoder = decoders.BPEDecoder()
    
    # Post-processor pour ajouter tokens spéciaux
    tokenizer.post_processor = TemplateProcessing(
        single="<bos> $A <eos>",
        pair="<bos> $A <eos> $B <eos>",
        special_tokens=[
            ("<bos>", 2), ("<eos>", 3), ("<pad>", 0), ("<unk>", 1), ("<mask>", 4),
        ],
    )
    
    # Trainer BPE
    trainer = trainers.BpeTrainer(
        vocab_size=VOCAB_SIZE,
        min_frequency=MIN_FREQUENCY,
        special_tokens=SPECIAL_TOKENS,
        show_progress=True,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
    )
    
    print(f"\n🚀 Entraînement sur {len(corpus_paths)} fichiers...")
    print(f"   Vocab size: {VOCAB_SIZE:,}")
    print(f"   Min frequency: {MIN_FREQUENCY}")
    print(f"   Special tokens: {len(SPECIAL_TOKENS)}")
    
    # Entraîner
    tokenizer.train([str(p) for p in corpus_paths], trainer)
    
    # Statistiques
    vocab = tokenizer.get_vocab()
    print(f"\n✅ Tokenizer entraîné: {len(vocab):,} tokens")
    
    # Vérifier tokens médicaux clés
    medical_terms = [
        "paludisme", "pneumonie", "tuberculose", "diabète", "hypertension",
        "amoxicilline", "artéméther", "luméfantrine", "paracétamol", "ibuprofène",
        "icd10", "posologie", "contre-indication", "interaction", "pharmacologie",
        "grossesse", "accouchement", "césarienne", "prénatal", "postnatal",
        "viih", "antirétroviral", "charge virale", "cd4", "prophylaxie",
    ]
    
    print("\n🔍 Vérification termes médicaux clés:")
    for term in medical_terms:
        ids = tokenizer.encode(term).ids
        if len(ids) == 1:
            print(f"   ✅ '{term}' → 1 token (id={ids[0]})")
        else:
            print(f"   ⚠️  '{term}' → {len(ids)} tokens {ids}")
    
    # Sauvegarder
    tokenizer_path = OUTPUT_DIR / "tokenizer.json"
    tokenizer.save(str(tokenizer_path), pretty=True)
    print(f"\n💾 Tokenizer sauvé: {tokenizer_path}")
    
    # Aussi sauvegarder vocab seul pour inspection
    vocab_path = OUTPUT_DIR / "vocab.json"
    import json
    with open(vocab_path, 'w', encoding='utf-8') as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)
    print(f"💾 Vocab sauvé: {vocab_path}")
    
    # Test encodage/décodage
    test_texts = [
        "Patient: 45 ans, Homme. Symptômes: fièvre, toux, dyspnée. Diagnostic: Pneumonie.",
        "Posologie: Amoxicilline 500mg 3x/jour pendant 7 jours.",
        "Paludisme grave: artésunate IV 2.4 mg/kg H0, H12, H24.",
    ]
    
    print("\n🧪 Test encodage/décodage:")
    for text in test_texts:
        encoded = tokenizer.encode(text)
        decoded = tokenizer.decode(encoded.ids)
        print(f"   Original:  {text[:60]}...")
        print(f"   Tokens:    {len(encoded.ids)} | IDs: {encoded.ids[:20]}...")
        print(f"   Décodé:    {decoded[:60]}...")
        print()
    
    return 0

if __name__ == "__main__":
    sys.exit(train_tokenizer())