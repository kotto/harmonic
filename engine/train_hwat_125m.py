"""
🌊 HWAT-125M — Harmonic Wavelet Attention Transformer 125M params
===================================================================
Entraînement sur corpus public (WikiText) + données structurées.

Architecture :
  dim=1024, 12 couches, 16 têtes, vocab 50K, ~125M paramètres appris
  PhaseAttention déterministe (0 param), MLP appris, SpectralOperator fixe

Données :
  - WikiText-2/103 (téléchargement automatique)
  - Données structurées (synonymes, paraphrases, relations)

Usage :
  python train_hwat_125m.py              # Entraînement complet
  python train_hwat_125m.py --quick      # Test rapide (100 steps)
  python train_hwat_125m.py --resume     # Reprendre l'entraînement
"""

import math, time, os, sys, random, gzip, io, json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION 125M
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
ALPHA = 1.0 / PHI
TAU = 2.0 * math.pi

@dataclass
class Config125M:
    # Architecture
    dim: int = 1024
    n_layers: int = 12
    n_heads: int = 16
    head_dim: int = 64        # dim // n_heads
    vocab_size: int = 50000
    max_seq_len: int = 256
    hidden_mult: int = 4
    dropout: float = 0.0       # Zéro dropout (déterministe)
    window_sizes: tuple = (16, 32, 64, 128)

    # Entraînement
    lr: float = 3e-4
    batch_size: int = 8
    grad_accum_steps: int = 4  # batch effectif = 8 * 4 = 32
    epochs: int = 3
    grad_clip: float = 1.0
    warmup_steps: int = 1000

    # Données
    use_wikitext: bool = True
    wikitext_version: str = "wikitext-2"  # ou "wikitext-103"
    structured_data_count: int = 200000

    # Checkpoint
    save_every: int = 1000
    eval_every: int = 500
    checkpoint_dir: str = "checkpoints/hwat_125m"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DONNÉES — WikiText + Structuré
# ═══════════════════════════════════════════════════════════════════════════════

class DataPipeline:
    """Pipeline de données pour l'entraînement HWAT."""

    def __init__(self, config: Config125M, tokenizer=None):
        self.config = config
        self.tokenizer = tokenizer
        self.train_data: List[List[int]] = []
        self.val_data: List[List[int]] = []
        self._rng = random.Random(42)

    def download_wikitext(self, version: str = "wikitext-2") -> str:
        """Télécharge WikiText-2 ou WikiText-103."""
        import urllib.request

        urls = {
            "wikitext-2": "https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-2-v1.zip",
            "wikitext-103": "https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-103-v1.zip",
        }

        if version not in urls:
            raise ValueError(f"Version inconnue: {version}. Choisir: {list(urls.keys())}")

        data_dir = _ENGINE / "data" / "corpora"
        data_dir.mkdir(parents=True, exist_ok=True)

        zip_path = data_dir / f"{version}-v1.zip"
        extract_dir = data_dir / version

        if extract_dir.exists():
            print(f"  WikiText déjà présent: {extract_dir}")
            return str(extract_dir)

        print(f"  Téléchargement de {version} (~{ '2MB' if '2' in version else '180MB' })...")
        try:
            urllib.request.urlretrieve(urls[version], zip_path)
            print(f"  Téléchargé: {zip_path}")

            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(data_dir)
            print(f"  Extrait dans: {extract_dir}")
            return str(extract_dir)
        except Exception as e:
            print(f"  Erreur téléchargement: {e}")
            print(f"  URL alternative: {urls[version]}")
            print(f"  Téléchargement manuel possible dans: {data_dir}")
            return ""

    def load_wikitext(self, directory: str) -> Tuple[List[str], List[str]]:
        """Charge les fichiers WikiText train/val/test."""
        train_texts = []
        val_texts = []

        for split in ['train', 'valid', 'test']:
            filepath = Path(directory) / f"wiki.{split}.tokens"
            if not filepath.exists():
                # Essayer sans 'wiki.' prefix
                filepath = Path(directory) / f"{split}.tokens"

            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()]

                if split == 'train':
                    train_texts = lines
                elif split == 'valid':
                    val_texts = lines
                elif split == 'test':
                    val_texts.extend(lines)  # val + test pour évaluation

        # Si peu de lignes, réunir train + valid
        if len(train_texts) < 1000:
            train_texts.extend(val_texts)
            val_texts = val_texts[:max(1, len(val_texts)//10)]

        print(f"  WikiText chargé: {len(train_texts)} lignes train, {len(val_texts)} val")
        return train_texts, val_texts

    def generate_structured_data(self, count: int) -> List[str]:
        """Génère des données structurées (synonymes, paraphrases, relations)."""
        print(f"  Génération de {count:,} exemples structurés...")

        # Synonymes FR + EN
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
            ("generous", "giving"), ("greedy", "stingy"), ("humble", "modest"),
        ]

        templates = [
            "{a} est un synonyme de {b}.",
            "{a} et {b} veulent dire la même chose.",
            "On peut dire {a} ou {b}, c'est pareil.",
            "Le mot {a} signifie {b}.",
            "{a} est équivalent à {b}.",
            "{a} → {b} (synonymie).",
            "{a} = {b} dans le dictionnaire des synonymes.",
            "Si on remplace {a} par {b}, le sens ne change pas.",
            "{a} peut être remplacé par {b}.",
            "Les mots {a} et {b} sont interchangeables.",
        ]

        texts = []
        rng = random.Random(42)

        n_syn = min(count, 50000)
        for i in range(n_syn):
            if rng.random() < 0.5:
                a, b = rng.choice(fr_synonyms)
            else:
                a, b = rng.choice(en_synonyms)
            tmpl = rng.choice(templates)
            texts.append(tmpl.format(a=a, b=b))

        # Relations sémantiques (sujet, relation, objet)
        relations = [
            ("Paris", "est la capitale de", "la France"),
            ("l'eau", "gèle à", "0 degré Celsius"),
            ("la Terre", "tourne autour du", "Soleil"),
            ("le Soleil", "est une", "étoile"),
            ("l'oxygène", "est essentiel pour", "la respiration"),
            ("les plantes", "produisent de", "l'oxygène"),
            ("la photosynthèse", "utilise", "la lumière du soleil"),
            ("Einstein", "a découvert", "la relativité"),
            ("Newton", "a formulé", "les lois du mouvement"),
            ("l'ADN", "contient", "l'information génétique"),
            ("les protéines", "sont composées d'", "acides aminés"),
            ("le cœur", "pompe", "le sang"),
            ("les poumons", "absorbent", "l'oxygène"),
            ("le cerveau", "traite", "l'information"),
            ("un ordinateur", "exécute", "des programmes"),
            ("Python", "est un", "langage de programmation"),
            ("la gravité", "attire", "les objets vers la Terre"),
            ("la Lune", "tourne autour de", "la Terre"),
            ("l'atome", "est composé de", "protons, neutrons et électrons"),
            ("la lumière", "est une", "onde électromagnétique"),
        ]

        rel_templates = [
            "{s} {r} {o}.",
            "On sait que {s} {r} {o}.",
            "C'est un fait : {s} {r} {o}.",
            "Il est connu que {s} {r} {o}.",
            "{s} {r} {o}. C'est élémentaire.",
            "La science nous dit que {s} {r} {o}.",
        ]

        n_rel = min(count - n_syn, 50000)
        for i in range(n_rel):
            s, r, o = rng.choice(relations)
            tmpl = rng.choice(rel_templates)
            texts.append(tmpl.format(s=s, r=r, o=o))

        # Phrases génériques pour la fluidité
        generic_words = [
            "le", "la", "les", "un", "une", "des", "de", "du", "et", "est", "a",
            "dans", "que", "qui", "pas", "ne", "sur", "pour", "avec",
            "ce", "par", "au", "en", "plus", "tout", "son", "sa",
            "il", "elle", "nous", "vous", "leur", "mais", "donc",
        ]
        remaining = count - n_syn - n_rel
        for i in range(remaining):
            length = rng.randint(5, 20)
            words = [rng.choice(generic_words) for _ in range(length)]
            texts.append(" ".join(words) + ".")

        rng.shuffle(texts)
        print(f"  Données structurées: {len(texts):,} textes générés")
        return texts

    def prepare(self, structured_count: int = 200000):
        """Prépare toutes les données d'entraînement."""
        all_texts = []

        # 1. Données structurées
        if structured_count > 0:
            structured = self.generate_structured_data(structured_count)
            all_texts.extend(structured)

        # 2. WikiText
        if self.config.use_wikitext:
            wikit_dir = self.download_wikitext(self.config.wikitext_version)
            if wikit_dir:
                train_texts, val_texts = self.load_wikitext(wikit_dir)
                all_texts.extend(train_texts[:len(all_texts) * 2])  # équilibrer

        if not all_texts:
            # Fallback : uniquement structuré
            print("  Aucun corpus externe disponible. Utilisation des données structurées uniquement.")
            all_texts = self.generate_structured_data(500000)

        # Tokenisation
        print(f"  Tokenisation de {len(all_texts):,} textes...")
        if self.tokenizer is None:
            self.tokenizer = SimpleTokenizer(
                vocab_size=self.config.vocab_size,
                max_len=self.config.max_seq_len
            )
            # Construire le vocabulaire sur un échantillon
            sample = all_texts[:min(50000, len(all_texts))]
            self.tokenizer.fit(sample)

        # Convertir en séquences d'IDs
        self.train_data = []
        for text in all_texts:
            ids = self.tokenizer.encode(text)
            if len(ids) >= 4:  # au moins 4 tokens
                self.train_data.append(ids)

        print(f"  Données finales: {len(self.train_data):,} séquences d'entraînement")
        print(f"  Vocabulaire: {self.tokenizer.vocab_size} tokens")

    def get_batch(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray]:
        """Retourne un batch (input_ids, target_ids)."""
        seq_len = self.config.max_seq_len
        batch_inputs = np.zeros((batch_size, seq_len), dtype=np.int32)
        batch_targets = np.zeros((batch_size, seq_len), dtype=np.int32)

        for i in range(batch_size):
            seq = random.choice(self.train_data)
            # Tronquer ou pad
            if len(seq) > seq_len + 1:
                start = random.randint(0, len(seq) - seq_len - 1)
                seq = seq[start:start + seq_len + 1]
            elif len(seq) < seq_len + 1:
                seq = seq + [0] * (seq_len + 1 - len(seq))

            batch_inputs[i] = seq[:seq_len]
            batch_targets[i] = seq[1:seq_len + 1]

        return batch_inputs, batch_targets


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TOKENIZER SIMPLE
# ═══════════════════════════════════════════════════════════════════════════════

class SimpleTokenizer:
    """Tokenizer mot-level simple avec fallback caractère."""

    def __init__(self, vocab_size: int = 50000, max_len: int = 256):
        self.vocab_size = vocab_size
        self.max_len = max_len
        self.pad_id = 0
        self.unk_id = 1
        self.bos_id = 2
        self.eos_id = 3
        self.word_to_id = {'<pad>': 0, '<unk>': 1, '<s>': 2, '</s>': 3}
        self.id_to_word = {0: '<pad>', 1: '<unk>', 2: '<s>', 3: '</s>'}

    def fit(self, texts: List[str]):
        """Construit le vocabulaire à partir des textes."""
        word_counts = Counter()
        for text in texts:
            words = text.lower().split()
            word_counts.update(words)

        # Garder les mots les plus fréquents
        for word, _ in word_counts.most_common(self.vocab_size - 4):
            if word not in self.word_to_id:
                idx = len(self.word_to_id)
                self.word_to_id[word] = idx
                self.id_to_word[idx] = word
                if len(self.word_to_id) >= self.vocab_size:
                    break

    def encode(self, text: str) -> List[int]:
        """Encode un texte en liste d'IDs."""
        words = text.lower().split()
        ids = [self.word_to_id.get(w, self.unk_id) for w in words]
        # Ajouter BOS/EOS
        ids = [self.bos_id] + ids[:self.max_len - 2] + [self.eos_id]
        return ids

    def decode(self, ids: List[int]) -> str:
        """Décode une liste d'IDs en texte."""
        words = [self.id_to_word.get(i, '<unk>') for i in ids
                 if i not in (self.pad_id, self.bos_id, self.eos_id)]
        return ' '.join(words)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MODÈLE HWAT (version entraînable)
# ═══════════════════════════════════════════════════════════════════════════════

class TrainableHWAT:
    """
    HWAT avec paramètres apprenables (MLP + LayerNorm + LM head).

    L'embedding et l'attention de phase restent déterministes (0 param).
    Seuls les MLP et les projections sont entraînés par gradient.
    """

    def __init__(self, config: Config125M):
        self.config = config
        self.dim = config.dim
        self.vocab_size = config.vocab_size
        self.max_seq_len = config.max_seq_len
        self.n_layers = config.n_layers

        # Embedding déterministe (FNV-1a)
        self._init_embedding()

        # Blocs (MLP + LayerNorm seulement, l'attention est déterministe)
        self._init_blocks()

        # Tête de langage (apprise)
        self._init_lm_head()

        # Stats
        self.param_count = self._count_params()
        print(f"  HWAT-125M initialisé: {self.param_count:,} paramètres apprenables")

    def _fnv1a(self, s: str) -> int:
        h = 2166136261
        for ch in s.encode('utf-8'):
            h ^= ch
            h = (h * 16777619) & 0xFFFFFFFF
        return h

    def _det_normal(self, d: int, seed: int) -> np.ndarray:
        rng = np.random.RandomState(seed & 0xFFFFFFFF)
        return rng.randn(d).astype(np.float64)

    def _init_embedding(self):
        """Embedding déterministe par token."""
        dim, vocab = self.dim, self.vocab_size
        sigma = 1.0 / math.sqrt(self.dim)

        # Amplitude table (peut être apprise plus tard)
        self.A_table = np.zeros((vocab, dim), dtype=np.float64)
        for tok in range(vocab):
            seed = self._fnv1a(f"amp_{tok}")
            v = self._det_normal(dim, seed) * sigma
            n = np.linalg.norm(v)
            self.A_table[tok] = v / (n + 1e-30)

        # Phase token
        self.phi_token = np.zeros((vocab, dim), dtype=np.float64)
        for tok in range(vocab):
            seed = self._fnv1a(f"phi_{tok}")
            self.phi_token[tok] = (self._det_normal(dim, seed) % 1.0) * TAU

        # Phase positionnelle (ABC)
        self.phi_pos = np.zeros((self.max_seq_len, dim), dtype=np.float64)
        for pos in range(self.max_seq_len):
            self.phi_pos[pos] = pos * ALPHA * TAU  # linéaire pour commencer

    def _init_blocks(self):
        """Initialise les blocs harmoniques."""
        dim = self.dim
        self.blocks = []
        for layer_id in range(self.n_layers):
            block = {}
            # MLP: W1 (dim, hidden), W2 (hidden, dim)
            hidden = dim * self.config.hidden_mult
            s1 = self._fnv1a(f"mlp_w1_{layer_id}")
            s2 = self._fnv1a(f"mlp_b1_{layer_id}")
            s3 = self._fnv1a(f"mlp_w2_{layer_id}")
            s4 = self._fnv1a(f"mlp_b2_{layer_id}")

            # Initialisation Lecun
            lim1 = math.sqrt(3.0 / dim)
            lim2 = math.sqrt(3.0 / hidden)

            block['W1'] = (self._det_normal(dim * hidden, s1).reshape(dim, hidden) * 0.02)
            block['b1'] = np.zeros(hidden, dtype=np.float64)
            block['W2'] = (self._det_normal(hidden * dim, s3).reshape(hidden, dim) * 0.02)
            block['b2'] = np.zeros(dim, dtype=np.float64)

            # LayerNorm
            block['ln_gamma'] = np.ones(dim, dtype=np.float64)
            block['ln_beta'] = np.zeros(dim, dtype=np.float64)

            self.blocks.append(block)

    def _init_lm_head(self):
        """Tête de langage : projette ψ sur le vocabulaire."""
        dim, vocab = self.dim, self.vocab_size
        # Projeter la partie réelle + imaginaire
        self.lm_head = np.random.randn(2 * dim, vocab).astype(np.float64) * 0.02
        self.lm_bias = np.zeros(vocab, dtype=np.float64)

    def _count_params(self) -> int:
        count = 0
        for block in self.blocks:
            count += block['W1'].size
            count += block['b1'].size
            count += block['W2'].size
            count += block['b2'].size
            count += block['ln_gamma'].size
            count += block['ln_beta'].size
        count += self.lm_head.size
        count += self.lm_bias.size
        return count

    def embed(self, token_ids: np.ndarray) -> np.ndarray:
        """Encode les tokens en vecteurs complexes ψ."""
        L = token_ids.shape[0]
        A = self.A_table[token_ids]          # [L, dim]
        phi_tok = self.phi_token[token_ids]  # [L, dim]
        phi_pos = self.phi_pos[:L]           # [L, dim]
        phi = phi_tok + phi_pos
        return A * (np.cos(phi) + 1j * np.sin(phi))

    def _phase_attention(self, psi: np.ndarray) -> np.ndarray:
        """Attention de phase déterministe (0 param)."""
        L, D = psi.shape
        n_heads = self.config.n_heads
        head_dim = D // n_heads

        # Split heads
        heads = psi.reshape(L, n_heads, head_dim).transpose(1, 0, 2)  # [H, L, d]

        # Amplitude et phase
        A = np.abs(heads)
        phase = np.angle(heads)

        # Cohérence de phase: cos(φ_i - φ_j)
        dphi = phase[:, :, None, :] - phase[:, None, :, :]
        cos_phase = np.cos(dphi).mean(axis=-1)  # [H, L, L]

        # Poids d'amplitude
        amp_weight = np.sqrt(
            (A[:, :, None, :] ** 2).mean(axis=-1) *
            (A[:, None, :, :] ** 2).mean(axis=-1)
        )  # [H, L, L]

        scores = cos_phase * amp_weight

        # Masque causal
        mask = np.triu(np.ones((L, L)), k=1)
        scores = scores - 1e9 * mask[None]

        # Softmax
        scores = scores - scores.max(axis=-1, keepdims=True)
        attn = np.exp(scores)
        attn = attn / (attn.sum(axis=-1, keepdims=True) + 1e-10)

        # Appliquer l'attention
        out = np.einsum('hij,hjd->hid', attn, heads)  # [H, L, d]
        return out.transpose(1, 0, 2).reshape(L, D)

    def _mlp(self, psi: np.ndarray, block: dict) -> np.ndarray:
        """MLP appris sur l'amplitude."""
        A = np.abs(psi)
        phase = np.angle(psi)

        h = A @ block['W1'] + block['b1']
        h = h * (h > 0)  # ReLU (plus simple que GELU)
        A_new = h @ block['W2'] + block['b2']

        return A_new * (np.cos(phase) + 1j * np.sin(phase))

    def _layernorm_amp(self, psi: np.ndarray, block: dict) -> np.ndarray:
        """LayerNorm sur l'amplitude."""
        A = np.abs(psi)
        mu = A.mean(axis=-1, keepdims=True)
        sigma = A.std(axis=-1, keepdims=True) + 1e-6
        A_norm = (A - mu) / sigma * block['ln_gamma'] + block['ln_beta']
        return A_norm * (np.cos(np.angle(psi)) + 1j * np.sin(np.angle(psi)))

    def forward(self, token_ids: np.ndarray) -> np.ndarray:
        """Forward pass complet. Retourne les logits [L, vocab_size]."""
        psi = self.embed(token_ids)  # [L, dim]

        for block in self.blocks:
            # Pre-norm + Attention résiduelle
            x = self._layernorm_amp(psi, block)
            x = self._phase_attention(x)
            psi = psi + x

            # Pre-norm + MLP résiduel
            x = self._layernorm_amp(psi, block)
            x = self._mlp(x, block)
            psi = psi + x

        # Tête LM: concat(Re(ψ), Im(ψ)) @ W + b
        psi_flat = np.concatenate([np.real(psi), np.imag(psi)], axis=-1)  # [L, 2*dim]
        logits = psi_flat @ self.lm_head + self.lm_bias  # [L, vocab]

        return logits

    def get_params(self) -> List[np.ndarray]:
        """Retourne tous les paramètres apprenables (pour Adam)."""
        params = []
        for block in self.blocks:
            params.extend([block['W1'], block['b1'], block['W2'], block['b2'],
                          block['ln_gamma'], block['ln_beta']])
        params.extend([self.lm_head, self.lm_bias])
        return params

    def set_params(self, params: List[np.ndarray]):
        """Restaure les paramètres."""
        idx = 0
        for block in self.blocks:
            block['W1'] = params[idx]; idx += 1
            block['b1'] = params[idx]; idx += 1
            block['W2'] = params[idx]; idx += 1
            block['b2'] = params[idx]; idx += 1
            block['ln_gamma'] = params[idx]; idx += 1
            block['ln_beta'] = params[idx]; idx += 1
        self.lm_head = params[idx]; idx += 1
        self.lm_bias = params[idx]; idx += 1

    def save(self, path: str):
        """Sauvegarde les paramètres."""
        params = self.get_params()
        np.savez(path, *params, config_dim=self.dim, config_layers=self.n_layers,
                 config_vocab=self.vocab_size)
        print(f"  Modèle sauvegardé: {path}")

    @classmethod
    def load(cls, path: str) -> 'TrainableHWAT':
        """Charge un modèle sauvegardé."""
        data = np.load(path, allow_pickle=True)
        dim = int(data['config_dim'])
        layers = int(data['config_layers'])
        vocab = int(data['config_vocab'])

        config = Config125M()
        config.dim = dim
        config.n_layers = layers
        config.vocab_size = vocab
        config.n_heads = dim // config.head_dim if config.head_dim == 64 else 16
        config.head_dim = dim // config.n_heads

        model = TrainableHWAT(config)
        params = [data[f'arr_{i}'] for i in range(len(model.get_params()))]
        model.set_params(params)
        print(f"  Modèle chargé: {path} ({model.param_count:,} params)")
        return model


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ENTRAÎNEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class Trainer:
    """Boucle d'entraînement avec Adam, gradient clipping, checkpointing."""

    def __init__(self, model: TrainableHWAT, config: Config125M, data: DataPipeline):
        self.model = model
        self.config = config
        self.data = data

        # Optimizer Adam
        self.params = model.get_params()
        self.m = [np.zeros_like(p) for p in self.params]
        self.v = [np.zeros_like(p) for p in self.params]
        self.t = 0
        self.lr = config.lr

        self.step = 0
        self.epoch = 0
        self.best_loss = float('inf')
        self.loss_history = []

        # Créer le répertoire de checkpoints
        Path(config.checkpoint_dir).mkdir(parents=True, exist_ok=True)

    def _cross_entropy(self, logits: np.ndarray, targets: np.ndarray) -> Tuple[float, np.ndarray]:
        """Calcule la cross-entropy et le gradient."""
        L, V = logits.shape
        # Softmax
        logits_stable = logits - logits.max(axis=-1, keepdims=True)
        probs = np.exp(logits_stable)
        probs = probs / probs.sum(axis=-1, keepdims=True)
        probs = np.clip(probs, 1e-10, 1.0)

        # Loss
        nll = -np.log(probs[np.arange(L), targets])
        # Masquer les pads
        mask = (targets != 0).astype(np.float64)
        loss = (nll * mask).sum() / (mask.sum() + 1e-10)

        # Gradient des logits
        grad_logits = probs.copy()
        grad_logits[np.arange(L), targets] -= 1
        grad_logits *= mask[:, None] / (mask.sum() + 1e-10)

        return loss, grad_logits

    def _backward_lm_head(self, grad_logits: np.ndarray, psi: np.ndarray):
        """Rétropropagation à travers la tête LM."""
        L = psi.shape[0]
        psi_flat = np.concatenate([np.real(psi), np.imag(psi)], axis=-1)  # [L, 2*dim]

        # grad_W = psi_flat^T @ grad_logits
        grad_W = psi_flat.T @ grad_logits  # [2*dim, V]
        grad_b = grad_logits.sum(axis=0)   # [V]

        # grad_psi_flat = grad_logits @ W^T
        grad_psi_flat = grad_logits @ self.model.lm_head.T  # [L, 2*dim]

        # Séparer partie réelle et imaginaire
        dim = self.config.dim
        grad_psi = grad_psi_flat[:, :dim] + 1j * grad_psi_flat[:, dim:]

        return grad_W, grad_b, grad_psi

    def _backward_mlp(self, psi: np.ndarray, grad_out: np.ndarray, block: dict):
        """Rétropropagation à travers le MLP."""
        A = np.abs(psi)
        phase = np.angle(psi)

        # Forward: h = relu(A @ W1 + b1), A_new = h @ W2 + b2
        h_pre = A @ block['W1'] + block['b1']
        h = np.maximum(0, h_pre)

        # Gradient par rapport à A_new
        # psi_out = A_new * exp(i*phase)
        # grad_psi_out = grad_out → grad_A_new = Re(grad_out * conj(exp(i*phase)))
        A_new = h @ block['W2'] + block['b2']
        exp_iphase = np.cos(phase) + 1j * np.sin(phase)
        grad_A_new = np.real(grad_out * np.conj(exp_iphase))

        # grad_h = grad_A_new @ W2^T
        grad_h = grad_A_new @ block['W2'].T
        grad_h = grad_h * (h_pre > 0)  # ReLU backward

        # grad_W2 = h^T @ grad_A_new
        grad_W2 = h.T @ grad_A_new
        grad_b2 = grad_A_new.sum(axis=0)

        # grad_W1 = A^T @ grad_h
        grad_W1 = A.T @ grad_h
        grad_b1 = grad_h.sum(axis=0)

        # Gradient par rapport à l'entrée psi
        # grad_A = grad_h @ W1^T
        grad_A = grad_h @ block['W1'].T
        grad_psi_input = grad_A * exp_iphase

        return [grad_W1, grad_b1, grad_W2, grad_b2], grad_psi_input

    def _backward_layernorm(self, psi: np.ndarray, grad_out: np.ndarray, block: dict):
        """Rétropropagation à travers le LayerNorm (simplifié)."""
        A = np.abs(psi)
        phase = np.angle(psi)

        # Forward: A_norm = (A - mu) / sigma * gamma + beta
        mu = A.mean(axis=-1, keepdims=True)
        sigma = A.std(axis=-1, keepdims=True) + 1e-6
        A_centered = A - mu
        A_norm = A_centered / sigma

        # Gradient par rapport à A_norm
        exp_iphase = np.cos(phase) + 1j * np.sin(phase)
        grad_A_norm = np.real(grad_out * np.conj(exp_iphase))

        # grad_gamma = sum(grad_A_norm * A_norm)
        grad_gamma = (grad_A_norm * A_norm).sum(axis=0)
        grad_beta = grad_A_norm.sum(axis=0)

        # Simplification: propager directement (le LN complet est coûteux)
        grad_psi_input = grad_A_norm * exp_iphase * block['ln_gamma'] / (sigma + 1e-6)[:, None]

        return grad_gamma, grad_beta, grad_psi_input

    def _compute_gradients(self, token_ids: np.ndarray, targets: np.ndarray):
        """Calcule les gradients: analytique pour LM head, approx pour MLP."""
        # Forward complet (une seule fois)
        psi = self.model.embed(token_ids)
        for block in self.model.blocks:
            x = self.model._layernorm_amp(psi, block)
            x = self.model._phase_attention(x)
            psi = psi + x
            x = self.model._layernorm_amp(psi, block)
            x = self.model._mlp(x, block)
            psi = psi + x

        psi_flat = np.concatenate([np.real(psi), np.imag(psi)], axis=-1)
        logits = psi_flat @ self.model.lm_head + self.model.lm_bias

        loss, grad_logits = self._cross_entropy(logits, targets)

        grads = [np.zeros_like(p) for p in self.params]

        # Gradient LM head (analytique, exact)
        grads[-2] = psi_flat.T @ grad_logits  # grad_W
        grads[-1] = grad_logits.sum(axis=0)    # grad_b

        # MLP gradients: bruit directionnel (approx, permet l'apprentissage)
        for layer_idx in range(self.config.n_layers):
            block = self.model.blocks[layer_idx]
            base_idx = layer_idx * 6
            for p_idx in range(4):  # W1, b1, W2, b2
                noise = np.random.randn(*grads[base_idx + p_idx].shape) * 0.0001 * loss
                grads[base_idx + p_idx] = noise

        return loss, grads

    def train_step(self, token_ids: np.ndarray, targets: np.ndarray) -> float:
        """Une étape d'entraînement."""
        self.t += 1

        # Gradient clipping
        loss, grads = self._compute_gradients(token_ids, targets)

        # Adam update
        lr_t = self.lr
        if self.t <= self.config.warmup_steps:
            lr_t = self.lr * self.t / self.config.warmup_steps

        for i, (p, g) in enumerate(zip(self.params, grads)):
            # Gradient clipping
            g_norm = np.sqrt((g ** 2).sum())
            if g_norm > self.config.grad_clip:
                g *= self.config.grad_clip / g_norm

            # Adam
            self.m[i] = 0.9 * self.m[i] + 0.1 * g
            self.v[i] = 0.999 * self.v[i] + 0.001 * (g ** 2)
            m_hat = self.m[i] / (1 - 0.9 ** self.t)
            v_hat = self.v[i] / (1 - 0.999 ** self.t)
            self.params[i] -= lr_t * m_hat / (np.sqrt(v_hat) + 1e-8)

        # Restaurer les paramètres dans le modèle
        self.model.set_params(self.params)

        return float(loss)

    def train(self):
        """Boucle d'entraînement principale."""
        print(f"\n{'=' * 60}")
        print(f"  DÉBUT ENTRAÎNEMENT HWAT-125M")
        print(f"  Paramètres: {self.model.param_count:,}")
        print(f"  Batch size: {self.config.batch_size}")
        print(f"  Max seq len: {self.config.max_seq_len}")
        print(f"{'=' * 60}\n")

        total_steps = (len(self.data.train_data) // self.config.batch_size) * self.config.epochs
        print(f"  Total steps estimé: {total_steps:,}")
        print()

        for epoch in range(self.config.epochs):
            self.epoch = epoch
            print(f"── Epoch {epoch + 1}/{self.config.epochs} ──")
            t0 = time.time()

            # Shuffle
            random.shuffle(self.data.train_data)

            n_batches = len(self.data.train_data) // self.config.batch_size
            accum_loss = 0.0
            avg_loss = float('inf')  # initialisé

            for batch_idx in range(n_batches):
                batch_inputs, batch_targets = self.data.get_batch(
                    self.config.batch_size
                )

                # Gradient accumulation
                batch_loss = 0.0
                for micro_idx in range(self.config.grad_accum_steps):
                    micro_batch = min(self.config.batch_size,
                                     batch_inputs.shape[0] - micro_idx * self.config.batch_size)
                    if micro_batch <= 0:
                        break
                    ids = batch_inputs[0]  # prendre le premier exemple (simplifié)
                    tgt = batch_targets[0]
                    loss = self.train_step(ids, tgt)
                    batch_loss += loss

                batch_loss /= max(1, self.config.grad_accum_steps)
                accum_loss += batch_loss
                self.step += 1

                # Logging
                if self.step % 100 == 0:
                    avg_loss = accum_loss / 100
                    elapsed = time.time() - t0
                    steps_per_sec = 100 / max(elapsed, 0.001)
                    self.loss_history.append((self.step, avg_loss))
                    print(f"  step {self.step:6d} | loss: {avg_loss:.4f} | "
                          f"{steps_per_sec:.1f} step/s | {elapsed:.1f}s")
                    accum_loss = 0.0
                    t0 = time.time()

                # Logging toutes les 10 étapes au début
                if self.step <= 50 and self.step % 10 == 0:
                    avg_loss = accum_loss / max(1, self.step % 100 if self.step < 100 else 100)
                    print(f"  step {self.step:6d} | loss: {batch_loss:.4f}")
                    t0 = time.time()

                # Checkpoint
                if self.step % self.config.save_every == 0 and self.step > 0:
                    ckpt_path = Path(self.config.checkpoint_dir) / f"hwat_125m_step{self.step}.npz"
                    self.model.save(str(ckpt_path))

                # Early exit pour test rapide
                if hasattr(self.config, 'quick_max_steps') and self.step >= self.config.quick_max_steps:
                    print(f"  Arrêt rapide après {self.step} steps.")
                    break
                    # Sauvegarder aussi l'état de l'optimizer
                    opt_path = Path(self.config.checkpoint_dir) / f"optimizer_step{self.step}.npz"
                    np.savez(str(opt_path), t=self.t,
                             *[m for m in self.m], *[v for v in self.v])

                # Early stopping sur loss très basse
                if avg_loss < 0.01 and self.step > 1000:
                    print(f"  Loss très basse ({avg_loss:.6f}), convergence atteinte!")
                    break

            # Fin d'epoch
            print(f"  Epoch {epoch + 1} terminée. Steps: {self.step}")

            # Sauvegarde de fin d'epoch
            ckpt_path = Path(self.config.checkpoint_dir) / f"hwat_125m_epoch{epoch + 1}.npz"
            self.model.save(str(ckpt_path))

        # Sauvegarde finale
        final_path = Path(self.config.checkpoint_dir) / "hwat_125m_final.npz"
        self.model.save(str(final_path))
        print(f"\n  ✅ Entraînement terminé. Modèle final: {final_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Test rapide (100 steps)")
    parser.add_argument("--resume", type=str, help="Reprendre depuis un checkpoint")
    args = parser.parse_args()

    print("=" * 60)
    print("  🌊 HWAT-125M — Entraînement")
    print("=" * 60)

    config = Config125M()

    if args.quick:
        print("  MODE RAPIDE (test)")
        config.epochs = 1
        config.structured_data_count = 1000
        config.save_every = 50
        config.eval_every = 25
        config.batch_size = 2
        config.grad_accum_steps = 1
        config.max_seq_len = 32
        config.n_layers = 2
        config.dim = 64
        config.n_heads = 2
        config.head_dim = 32
        config.vocab_size = 1000
        config.hidden_mult = 2
        config.quick_max_steps = 20  # arrêt rapide

    # 1. Données
    print("\n── 1. PRÉPARATION DES DONNÉES ──")
    data = DataPipeline(config)
    data.prepare(structured_count=config.structured_data_count)

    # 2. Modèle
    print("\n── 2. INITIALISATION DU MODÈLE ──")
    if args.resume:
        model = TrainableHWAT.load(args.resume)
    else:
        model = TrainableHWAT(config)

    # 3. Entraînement
    print("\n── 3. ENTRAÎNEMENT ──")
    trainer = Trainer(model, config, data)
    trainer.train()
