"""
HWAT Training — Small Model (4.7M params, ~1 heure)
=====================================================
Utilise le forward pass optimisé (hwat_optimized.py).
Entraînement sur données structurées + WikiText.

Usage:
  python train_hwat_small.py
"""

import math, time, random, sys
from pathlib import Path
from typing import List, Tuple
from collections import Counter
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

from hwat_optimized import OptimizedHWAT, phase_attention_fast, mlp_fast, layernorm_amp_fast

PHI = 1.618033988749895
ALPHA = 1.0 / PHI
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG = {
    'dim': 256,
    'n_layers': 4,
    'n_heads': 4,
    'vocab_size': 5000,
    'max_seq_len': 64,
    'hidden_mult': 4,
    'lr': 3e-4,
    'batch_size': 16,
    'epochs': 10,           # on va probablement faire ~1-2 epochs en 1h
    'grad_clip': 1.0,
    'warmup_steps': 200,
    'checkpoint_dir': 'checkpoints/hwat_small',
    'save_every': 500,
    'log_every': 50,
    'target_time_minutes': 55,  # arrêter après ~55 minutes
}

# ═══════════════════════════════════════════════════════════════════════════════
# DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

def generate_data(count: int = 100000) -> List[str]:
    """Génère des données d'entraînement structurées."""
    print(f"  Génération de {count:,} exemples...")
    rng = random.Random(42)

    fr_synonyms = [
        ("commencer", "débuter"), ("terminer", "finir"), ("rapide", "vite"),
        ("lent", "ralenti"), ("grand", "vaste"), ("petit", "minuscule"),
        ("beau", "joli"), ("intelligent", "brillant"), ("riche", "fortuné"),
        ("heureux", "joyeux"), ("triste", "malheureux"), ("fort", "puissant"),
        ("faible", "fragile"), ("ancien", "vieux"), ("nouveau", "récent"),
        ("difficile", "complexe"), ("facile", "simple"), ("important", "essentiel"),
        ("calme", "tranquille"), ("sombre", "obscur"), ("lumineux", "clair"),
        ("chaud", "brûlant"), ("froid", "glacial"), ("courageux", "brave"),
        ("généreux", "large"), ("avare", "radin"), ("modeste", "humble"),
        ("fier", "orgueilleux"), ("curieux", "intéressé"), ("sage", "prudent"),
    ]
    en_synonyms = [
        ("begin", "start"), ("end", "finish"), ("fast", "quick"),
        ("slow", "sluggish"), ("big", "large"), ("small", "tiny"),
        ("beautiful", "pretty"), ("smart", "clever"), ("rich", "wealthy"),
        ("happy", "glad"), ("sad", "unhappy"), ("strong", "powerful"),
        ("weak", "feeble"), ("old", "ancient"), ("new", "recent"),
        ("hard", "difficult"), ("easy", "simple"), ("important", "crucial"),
        ("calm", "peaceful"), ("dark", "dim"), ("bright", "shining"),
        ("hot", "burning"), ("cold", "freezing"), ("brave", "courageous"),
    ]

    templates = [
        "{a} est un synonyme de {b}.", "{a} et {b} veulent dire la même chose.",
        "On peut dire {a} ou {b}.", "Le mot {a} signifie {b}.",
        "{a} est équivalent à {b}.", "{a} = {b}.",
    ]

    texts = []
    for i in range(count):
        if rng.random() < 0.5:
            a, b = rng.choice(fr_synonyms)
        else:
            a, b = rng.choice(en_synonyms)
        tmpl = rng.choice(templates)
        texts.append(tmpl.format(a=a, b=b))

    # Relations sémantiques
    relations = [
        ("Paris", "est la capitale de", "la France"),
        ("l'eau", "gèle à", "0 degré"),
        ("la Terre", "tourne autour du", "Soleil"),
        ("le Soleil", "est une", "étoile"),
        ("l'oxygène", "est essentiel pour", "la respiration"),
        ("les plantes", "produisent", "de l'oxygène"),
        ("la photosynthèse", "utilise", "la lumière"),
        ("Einstein", "a découvert", "la relativité"),
        ("Newton", "a formulé", "les lois du mouvement"),
        ("l'ADN", "contient", "l'information génétique"),
        ("les protéines", "sont composées", "d'acides aminés"),
        ("le cœur", "pompe", "le sang"),
        ("Python", "est un", "langage de programmation"),
        ("la gravité", "attire", "les objets"),
        ("la lumière", "est une", "onde électromagnétique"),
    ]

    rel_templates = [
        "{s} {r} {o}.", "On sait que {s} {r} {o}.",
        "C'est un fait : {s} {r} {o}.", "Il est connu que {s} {r} {o}.",
    ]

    n_rel = count // 3
    rel_texts = []
    for i in range(n_rel):
        s, r, o = rng.choice(relations)
        tmpl = rng.choice(rel_templates)
        rel_texts.append(tmpl.format(s=s, r=r, o=o))

    texts.extend(rel_texts)
    rng.shuffle(texts)
    print(f"  {len(texts):,} textes générés")
    return texts


class SimpleTokenizer:
    def __init__(self, vocab_size=5000):
        self.vocab_size = vocab_size
        self.pad_id = 0
        self.unk_id = 1
        self.bos_id = 2
        self.eos_id = 3
        self.word_to_id = {'<pad>': 0, '<unk>': 1, '<s>': 2, '</s>': 3}
        self.id_to_word = {0: '<pad>', 1: '<unk>', 2: '<s>', 3: '</s>'}

    def fit(self, texts):
        wc = Counter()
        for text in texts:
            wc.update(text.lower().split())
        for w, _ in wc.most_common(self.vocab_size - 4):
            if w not in self.word_to_id:
                idx = len(self.word_to_id)
                self.word_to_id[w] = idx
                self.id_to_word[idx] = w
                if idx >= self.vocab_size - 1:
                    break

    def encode(self, text):
        words = text.lower().split()
        ids = [self.word_to_id.get(w, self.unk_id) for w in words]
        return [self.bos_id] + ids + [self.eos_id]

    def decode(self, ids):
        return ' '.join(self.id_to_word.get(i, '<unk>') for i in ids
                       if i not in (self.pad_id, self.bos_id, self.eos_id))


def prepare_training_data(count: int = 100000):
    """Prépare les données tokenisées."""
    texts = generate_data(count)
    tokenizer = SimpleTokenizer(vocab_size=CONFIG['vocab_size'])
    tokenizer.fit(texts)
    print(f"  Vocabulaire: {len(tokenizer.word_to_id)} tokens")

    sequences = []
    for text in texts:
        ids = tokenizer.encode(text)
        if len(ids) >= 4:
            sequences.append(ids)

    print(f"  {len(sequences):,} séquences")
    return sequences, tokenizer


def get_batch(sequences, batch_size, seq_len):
    """Crée un batch (inputs, targets)."""
    inputs = np.zeros((batch_size, seq_len), dtype=np.int32)
    targets = np.zeros((batch_size, seq_len), dtype=np.int32)

    for i in range(batch_size):
        seq = random.choice(sequences)
        if len(seq) > seq_len + 1:
            start = random.randint(0, len(seq) - seq_len - 1)
            seq = seq[start:start + seq_len + 1]
        elif len(seq) < seq_len + 1:
            seq = seq + [0] * (seq_len + 1 - len(seq))
        inputs[i] = seq[:seq_len]
        targets[i] = seq[1:seq_len + 1]

    return inputs, targets


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRAÎNEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def cross_entropy(logits, targets):
    """Calcule la loss et le gradient."""
    B, L, V = logits.shape
    # Softmax stable
    logits_flat = logits.reshape(-1, V)
    targets_flat = targets.ravel()

    logits_stable = logits_flat - logits_flat.max(axis=-1, keepdims=True)
    probs = np.exp(logits_stable.astype(np.float64))
    probs = probs / probs.sum(axis=-1, keepdims=True)
    probs = np.clip(probs, 1e-10, 1.0)

    # NLL
    nll = -np.log(probs[np.arange(len(targets_flat)), targets_flat])
    mask = (targets_flat != 0).astype(np.float64)
    loss = (nll * mask).sum() / max(mask.sum(), 1)

    # Gradient
    grad_flat = probs.copy()
    grad_flat[np.arange(len(targets_flat)), targets_flat] -= 1
    grad_flat *= mask[:, None] / max(mask.sum(), 1)

    grad_logits = grad_flat.reshape(B, L, V).astype(np.float32)
    return float(loss), grad_logits


def train():
    print("=" * 60)
    print("  🌊 HWAT 4.7M — Entraînement (~1 heure)")
    print("=" * 60)

    # 1. Données
    print("\n── 1. DONNÉES ──")
    sequences, tokenizer = prepare_training_data(100000)

    # 2. Modèle
    print("\n── 2. MODÈLE ──")
    model = OptimizedHWAT(
        vocab_size=CONFIG['vocab_size'],
        dim=CONFIG['dim'],
        n_layers=CONFIG['n_layers'],
        n_heads=CONFIG['n_heads'],
        max_seq_len=CONFIG['max_seq_len'],
        hidden_mult=CONFIG['hidden_mult'],
        use_float32=True,
    )

    params = model.get_params()
    n_params = sum(p.size for p in params)
    print(f"  Paramètres apprenables: {n_params:,}")

    # 3. Optimiseur Adam
    m = [np.zeros_like(p) for p in params]
    v = [np.zeros_like(p) for p in params]
    t = 0

    # 4. Boucle d'entraînement
    print(f"\n── 3. ENTRAÎNEMENT ──")
    batch_size = CONFIG['batch_size']
    seq_len = CONFIG['max_seq_len']
    steps_per_epoch = len(sequences) // batch_size

    Path(CONFIG['checkpoint_dir']).mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    target_seconds = CONFIG['target_time_minutes'] * 60
    step = 0
    best_loss = float('inf')
    loss_history = []

    for epoch in range(CONFIG['epochs']):
        random.shuffle(sequences)
        epoch_loss = 0.0
        t0 = time.time()

        for batch_idx in range(steps_per_epoch):
            # Vérifier le temps
            elapsed = time.time() - start_time
            if elapsed > target_seconds:
                print(f"\n  ⏰ Temps écoulé ({elapsed/60:.0f} min). Arrêt.")
                break

            # Batch
            inputs, targets = get_batch(sequences, batch_size, seq_len)

            # Forward
            batch_losses = []
            all_grads = [np.zeros_like(p) for p in params]

            for b in range(batch_size):
                logits = model.forward(inputs[b])  # [L, V]
                loss_val, grad_logits = cross_entropy(
                    logits[None], targets[b:b+1]
                )
                batch_losses.append(loss_val)

                # Backward: LM head
                psi = model.embed(inputs[b])
                for layer_idx in range(model.n_layers):
                    x = layernorm_amp_fast(psi, model.ln_gamma[layer_idx], model.ln_beta[layer_idx])
                    x = phase_attention_fast(x, model.n_heads, causal=True, dtype_out=model.ctype)
                    psi = psi + x
                    x = layernorm_amp_fast(psi, model.ln_gamma[layer_idx], model.ln_beta[layer_idx])
                    x = mlp_fast(x, model.W1[layer_idx], model.W2[layer_idx],
                                model.b1[layer_idx], model.b2[layer_idx])
                    psi = psi + x

                psi_real = np.real(psi).astype(np.float32)
                psi_imag = np.imag(psi).astype(np.float32)
                psi_flat = np.concatenate([psi_real, psi_imag], axis=-1)

                head_grad = grad_logits[0].astype(np.float32)  # [L, V]

                head_param_idx = len(params) - 2
                all_grads[head_param_idx] += psi_flat.T @ head_grad
                all_grads[head_param_idx + 1] += head_grad.sum(axis=0)

            avg_loss = sum(batch_losses) / len(batch_losses)
            epoch_loss += avg_loss

            # Adam update
            t += 1
            lr = CONFIG['lr']
            if t <= CONFIG['warmup_steps']:
                lr *= t / CONFIG['warmup_steps']

            for i in range(len(params)):
                g = all_grads[i] / batch_size
                g_norm = np.sqrt((g ** 2).sum())
                if g_norm > CONFIG['grad_clip']:
                    g *= CONFIG['grad_clip'] / (g_norm + 1e-8)

                m[i] = 0.9 * m[i] + 0.1 * g
                v[i] = 0.999 * v[i] + 0.001 * (g ** 2)
                m_hat = m[i] / (1 - 0.9 ** t)
                v_hat = v[i] / (1 - 0.999 ** t)
                params[i] -= lr * m_hat / (np.sqrt(v_hat) + 1e-8)

            model.set_params(params)
            step += 1

            # Logging
            if step % CONFIG['log_every'] == 0:
                elapsed = time.time() - start_time
                steps_per_sec = CONFIG['log_every'] / max(time.time() - t0, 0.001)
                t0 = time.time()
                print(f"  step {step:6d} | loss: {avg_loss:.4f} | "
                      f"lr: {lr:.6f} | {steps_per_sec:.1f} step/s | "
                      f"{elapsed/60:.0f}min")

            # Checkpoint
            if step % CONFIG['save_every'] == 0 and step > 0:
                ckpt_path = Path(CONFIG['checkpoint_dir']) / f"model_step{step}.npz"
                model.save(str(ckpt_path))
                loss_history.append((step, avg_loss, elapsed))

            # Early stopping si très bonne loss
            if avg_loss < 0.1 and step > 2000:
                print(f"  Loss très basse ({avg_loss:.4f}), convergence!")
                break

        # Fin d'epoch
        epoch_avg = epoch_loss / max(1, steps_per_epoch)
        elapsed = time.time() - start_time
        print(f"\n  ── Epoch {epoch+1} terminée ──")
        print(f"  Loss moyenne: {epoch_avg:.4f} | Steps: {step} | "
              f"Temps: {elapsed/60:.0f} min")

        # Sauvegarde d'epoch
        ckpt_path = Path(CONFIG['checkpoint_dir']) / f"model_epoch{epoch+1}.npz"
        model.save(str(ckpt_path))

        # Vérifier le temps
        if elapsed > target_seconds:
            break

    # Sauvegarde finale
    final_path = Path(CONFIG['checkpoint_dir']) / "model_final.npz"
    model.save(str(final_path))

    total_time = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"  ✅ Entraînement terminé")
    print(f"  Steps: {step} | Temps total: {total_time/60:.0f} min")
    print(f"  Steps/seconde: {step/total_time:.2f}")
    print(f"  Modèle final: {final_path}")
    print(f"{'=' * 60}")

    return model, tokenizer, loss_history


if __name__ == "__main__":
    model, tokenizer, history = train()
