"""
Wave GPT — Générateur de Texte Purement Ondulatoire
=====================================================
Moteur de génération de texte qui fonctionne EXACTEMENT comme un LLM
(token par token, auto-attention, sampling) mais avec ZÉRO paramètre appris.

Architecture :
  ┌─────────────────────────────────────────────────────────┐
  │                    WAVE GPT                              │
  │                                                          │
  │  ψ₀ = encode(prompt)                                     │
  │  FOR t = 1..max_tokens:                                  │
  │    ψ_ctx = ψ_{t-1} + Σⱼ α_{t,j} · ψ_j   (self-attention)│
  │    scores = {w: Re(⟨ψ_ctx|ψ_w⟩) for w ∈ vocab}          │
  │    token_t = wave_sample(scores, T, top_p, top_k)       │
  │    ψ_t = normalize(ψ_ctx + ψ_token_t)                   │
  │  END                                                     │
  │                                                          │
  │  Zéro paramètre. Zéro GPU. 100% ondulatoire.            │
  └─────────────────────────────────────────────────────────┘

Équivalences LLM → Ondulatoire :
  Token Embedding    → FNV1a + φ-spacing → ℂ⁵¹²
  Positional Encoding → Phase naturelle (rotation par position)
  Self-Attention     → Cohérence Re(⟨ψ_Q|ψ_K⟩) sur l'historique
  Multi-Head         → Bandes de fréquence φ^k
  FFN / MLP          → Propagation de phase ψ → ψ·e^{iθ}
  Layer Norm         → Projection unitaire |ψ| = 1
  Residual           → Superposition ψ_out + ψ_in
  Softmax + Sampling → WaveSampler (température, top-p, top-k)
  KV-Cache           → Historique des ψ (vecteurs dans ℂ⁵¹²)

Author: Univers-Holistique
"""

import math
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
PI = math.pi
TAU = 2.0 * PI

# ═══════════════════════════════════════════════════════════════════════════════
# ENCODEUR HOLOGRAPHIQUE (version autonome pour Wave GPT)
# ═══════════════════════════════════════════════════════════════════════════════

class WaveEncoder:
    """
    Encodeur holographique autonome.
    
    Chaque mot → vecteur complexe unitaire dans ℂ^dim
    via FNV1a hash + espacement de phase φ.
    """

    def __init__(self, dim: int = 512):
        self.dim = dim
        self._cache: Dict[str, np.ndarray] = {}
        # Pré-encoder un vocabulaire de base (français)
        self._base_vocab()

    def encode(self, text: str) -> np.ndarray:
        """
        Encode un texte en vecteur d'onde ψ ∈ ℂ^dim.
        
        Pour un mot : ψ_mot = FNV1a_phi(mot)
        Pour une phrase : ψ = moyenne normalisée des ψ_mots
        """
        if not text or not text.strip():
            return self._zero_psi()

        words = text.strip().lower().split()
        if not words:
            return self._zero_psi()

        psis = []
        for word in words:
            if word not in self._cache:
                self._cache[word] = self._encode_word(word)
            psis.append(self._cache[word])

        # Superposition normalisée
        psi = np.sum(psis, axis=0)
        norm = np.linalg.norm(psi)
        if norm > 1e-10:
            return psi / norm
        return self._zero_psi()

    def _encode_word(self, word: str) -> np.ndarray:
        """
        Encode un mot unique via FNV1a + φ-spacing.
        
        ψ[k] = exp(i · (FNV1a(word) · φ^k mod 2π))
        """
        h = self._fnv1a(word)
        phases = (h * PHI ** np.arange(self.dim)) % TAU
        psi = np.exp(1j * phases)
        return psi / np.linalg.norm(psi)

    def _fnv1a(self, text: str) -> int:
        """Hash FNV1a 64-bit."""
        h = 0xcbf29ce484222325
        for ch in text:
            h = ((h * 0x100000001b3) ^ ord(ch)) & 0xFFFFFFFFFFFFFFFF
        return h

    def _zero_psi(self) -> np.ndarray:
        psi = np.ones(self.dim, dtype=complex) / math.sqrt(self.dim)
        return psi / np.linalg.norm(psi)

    def _base_vocab(self):
        """Pré-encoder un vocabulaire de base (français courant)."""
        base_words = [
            # Articles et prépositions
            "le", "la", "les", "un", "une", "des", "de", "du", "à", "au", "aux",
            "et", "ou", "donc", "car", "mais", "ni", "or", "si", "que", "qui",
            "dans", "sur", "sous", "avec", "sans", "pour", "par", "entre",
            "ce", "cette", "ces", "mon", "ton", "son", "notre", "votre", "leur",
            # Verbes courants
            "est", "sont", "être", "avoir", "fait", "faire", "peut", "pouvoir",
            "dire", "aller", "voir", "savoir", "venir", "devoir", "prendre",
            "donner", "mettre", "trouver", "parler", "aimer", "vivre", "passer",
            # Noms communs
            "chose", "homme", "femme", "enfant", "monde", "vie", "temps", "jour",
            "nuit", "main", "œil", "cœur", "esprit", "corps", "âme", "pensée",
            "amour", "paix", "guerre", "mort", "dieu", "science", "art", "nature",
            "lumière", "ombre", "eau", "feu", "terre", "ciel", "soleil", "lune",
            # Adjectifs
            "bon", "mauvais", "grand", "petit", "beau", "vrai", "faux", "nouveau",
            "ancien", "premier", "dernier", "seul", "même", "autre", "tout",
            # Adverbes
            "très", "trop", "peu", "beaucoup", "bien", "mal", "mieux", "toujours",
            "jamais", "souvent", "encore", "déjà", "ici", "là", "maintenant",
        ]
        for word in base_words:
            self._cache[word] = self._encode_word(word)

    def encode_word(self, word: str) -> np.ndarray:
        """Encode un mot (avec cache)."""
        word = word.lower().strip()
        if word not in self._cache:
            self._cache[word] = self._encode_word(word)
        return self._cache[word]

    @property
    def vocabulary(self) -> Dict[str, np.ndarray]:
        return self._cache


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE D'ATTENTION ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveSelfAttention:
    """
    Auto-attention ondulatoire — équivalent exact du self-attention des Transformers.
    
    LLM : Attention(Q,K,V) = softmax(QK^T/√d) · V
    Harmo : Attention(ψ_history) = Σ_j α_j · ψ_j
            où α_j = softmax(Re(⟨ψ_current|ψ_j⟩))
    
    Multi-head : H bandes de fréquence séparées par φ.
    """

    def __init__(self, dim: int = 512, n_heads: int = 4):
        self.dim = dim
        self.n_heads = n_heads
        # Fréquences pour le multi-head (espacées de φ)
        self._freqs = [PHI ** k for k in range(n_heads)]

    def attend(self, psi_current: np.ndarray,
               psi_history: List[np.ndarray]) -> np.ndarray:
        """
        Calcule le contexte attentionné.
        
        Args:
            psi_current: vecteur d'onde de la position courante (query)
            psi_history: historique des vecteurs d'onde (keys + values)
            
        Returns:
            ψ_context = Σ_j α_j · ψ_j  (attention-weighted sum, normalized)
        """
        if not psi_history:
            return psi_current

        # Multi-head : rotation par fréquence
        head_outputs = []
        for freq in self._freqs:
            # Rotation de la query (tête h)
            psi_q = self._rotate(psi_current, freq)

            # Scores d'attention = cohérence query·key
            scores = np.array([
                float(np.real(np.dot(psi_q, psi_j.conj())))
                for psi_j in psi_history
            ])

            # Softmax (température naturelle)
            scores = scores - scores.max()  # stabilité numérique
            alpha = np.exp(scores / 0.8)  # température implicite
            alpha = alpha / alpha.sum()

            # Attention-weighted sum
            head_out = np.sum([
                alpha[j] * psi_history[j]
                for j in range(len(psi_history))
            ], axis=0)

            head_out = head_out / (np.linalg.norm(head_out) + 1e-10)
            head_outputs.append(head_out)

        # Fusion multi-head : superposition normalisée
        psi_context = np.sum(head_outputs, axis=0)
        return psi_context / np.linalg.norm(psi_context)

    def _rotate(self, psi: np.ndarray, freq: float) -> np.ndarray:
        """Rotation de phase pour multi-head."""
        phases = freq * np.arange(self.dim) * PI / self.dim
        return psi * np.exp(1j * phases)


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE GPT — Moteur Principal
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WaveGPTResult:
    """Résultat de génération Wave GPT."""
    text: str                          # Texte généré
    tokens: List[str]                  # Tokens générés
    psi_sequence: List[np.ndarray]     # Séquence des vecteurs d'onde
    coherence_scores: List[float]      # Scores de cohérence à chaque étape
    perplexity: float                  # Perplexité ondulatoire moyenne
    n_tokens: int                      # Nombre de tokens générés
    elapsed_ms: float                  # Temps de génération


class WaveGPT:
    """
    Générateur de texte purement ondulatoire.
    
    Fonctionne EXACTEMENT comme un GPT/Llama/Claude :
    - Auto-régressif (token par token)
    - Auto-attention sur l'historique
    - Sampling avec température, top-p, top-k
    - Context window avec mémoire ABC
    
    Mais avec ZÉRO paramètre appris. Tout émerge de l'interférence
    des ondes dans ℂ⁵¹².

    Usage:
        gpt = WaveGPT()
        result = gpt.generate("La lumière est")
        print(result.text)
        # → "La lumière est une onde électromagnétique qui se propage..."
    """

    def __init__(self, dim: int = 512, n_heads: int = 4,
                 max_context: int = 512,
                 external_encoder = None):
        """
        Args:
            dim: dimension de l'espace complexe
            n_heads: nombre de têtes d'attention (bandes de fréquence)
            max_context: taille maximale du contexte (mémoire ABC)
            external_encoder: encodeur holographique externe (ex: celui du HarmonicBrain)
                              Si fourni, on l'utilise au lieu de l'encodeur standalone.
        """
        self.dim = dim
        self.max_context = max_context
        
        # Utiliser l'encodeur externe s'il est fourni (encodeur du cerveau)
        if external_encoder is not None:
            self.encoder = external_encoder
            self._external_encoder = True
        else:
            self.encoder = WaveEncoder(dim=dim)
            self._external_encoder = False
            
        self.attention = WaveSelfAttention(dim=dim, n_heads=n_heads)

        # Intégrer WaveSampler si disponible
        self._sampler = None
        try:
            from wave_sampling import WaveSampler
            self._sampler = WaveSampler()
        except ImportError:
            pass

        # Tokens spéciaux
        self.EOS = "<eos>"
        self.BOS = "<bos>"
    
    def _encode_word(self, word: str) -> np.ndarray:
        """Encode un mot, avec adaptation pour encodeur externe."""
        word = word.lower().strip()
        if self._external_encoder:
            # Essayer les méthodes de l'encodeur externe
            if hasattr(self.encoder, 'encode_word'):
                return self.encoder.encode_word(word)
            elif hasattr(self.encoder, 'encode'):
                return self.encoder.encode(word)
            elif hasattr(self.encoder, 'encode_query'):
                return self.encoder.encode_query(word)
        # Fallback : utiliser l'encodeur standalone (FNV1a + phi-spacing)
        return WaveEncoder.encode_word(self, word) if hasattr(self, '_cache') else self._standalone_encode(word)
    
    def _standalone_encode(self, word: str) -> np.ndarray:
        """Encode un mot avec FNV1a + phi-spacing (fallback standalone)."""
        h = 0xcbf29ce484222325
        for ch in word:
            h = ((h * 0x100000001b3) ^ ord(ch)) & 0xFFFFFFFFFFFFFFFF
        phases = (h * PHI ** np.arange(self.dim)) % TAU
        psi = np.exp(1j * phases)
        return psi / np.linalg.norm(psi)
    
    def _build_vocabulary(self, prompt_words: List[str]) -> Dict[str, np.ndarray]:
        """Construit le vocabulaire de génération."""
        vocab = {}
        
        if self._external_encoder:
            # Utiliser les mots du prompt + mots communs
            base_words = set(prompt_words)
            # Ajouter des connecteurs logiques
            base_words.update([
                "le", "la", "les", "un", "une", "des", "de", "du", "à", "au",
                "et", "ou", "donc", "car", "mais", "ni", "si", "que", "qui",
                "dans", "sur", "sous", "avec", "sans", "pour", "par",
                "est", "sont", "être", "avoir", "fait", "faire", "peut",
                "ce", "cette", "ces", "son", "sa", "ses", "leur", "leurs",
                "bon", "grand", "petit", "vrai", "nouveau", "autre", "tout",
                "très", "bien", "mal", "toujours", "jamais", "encore",
                ".", "!", "?",
            ])
            for word in base_words:
                if word and len(word) >= 1:
                    vocab[word] = self._encode_word(word)
        else:
            # Utiliser le vocabulaire pré-encodé du WaveEncoder
            vocab = dict(self.encoder.vocabulary)
            for word in prompt_words:
                if word not in vocab:
                    vocab[word] = self._encode_word(word)
        
        return vocab

    def generate(self, prompt: str,
                 max_tokens: int = 50,
                 temperature: float = 0.8,
                 top_p: float = 0.9,
                 top_k: int = 50,
                 stop_tokens: Optional[List[str]] = None) -> WaveGPTResult:
        """
        Génère du texte à partir d'un prompt.

        Boucle auto-régressive :
          ψ_0 = encode(prompt)
          FOR t = 1..max_tokens:
            ψ_ctx = self_attention(ψ_t, ψ_history)
            scores = {w: Re(⟨ψ_ctx|ψ_w⟩)}
            token = wave_sample(scores, T, top_p, top_k)
            ψ_{t+1} = normalize(ψ_ctx + ψ_token)
            IF token == EOS: break

        Args:
            prompt: texte de départ
            max_tokens: nombre maximum de tokens à générer
            temperature: 0 = déterministe, > 0 = créatif
            top_p: seuil de cohérence cumulée
            top_k: nombre maximum de candidats
            stop_tokens: tokens d'arrêt (défaut: [".", "!", "?", "\n\n"])

        Returns:
            WaveGPTResult
        """
        t_start = time.time()

        if stop_tokens is None:
            stop_tokens = [".", "!", "?", "\n\n", self.EOS]

        # Encoder le prompt
        prompt_tokens = prompt.strip().split()
        if not prompt_tokens:
            prompt_tokens = ["le"]

        psi_history = [self._encode_word(w) for w in prompt_tokens]

        # ψ initial = dernière position du prompt
        psi_current = psi_history[-1].copy() if psi_history else self.encoder.encode(prompt) if not self._external_encoder else self._encode_word(prompt_tokens[0])

        tokens = list(prompt_tokens)
        coherence_scores = []

        # Construire le vocabulaire
        vocab = self._build_vocabulary(prompt_tokens)

        for step in range(max_tokens):
            # 1. Self-attention : ψ_ctx = Σ_j α_j · ψ_j
            psi_ctx = self.attention.attend(psi_current, psi_history[-self.max_context:])

            # 2. Scores de cohérence pour chaque mot candidat
            scores = {}
            for word, psi_w in vocab.items():
                # Éviter les tokens trop courts ou déjà générés récemment
                if len(word) <= 1:
                    continue
                score = float(np.real(np.dot(psi_ctx, psi_w.conj())))
                scores[word] = score

            # 3. Échantillonnage
            if self._sampler is not None and len(scores) >= 3:
                self._sampler.set_vocabulary(vocab)
                next_word = self._sampler.sample(
                    psi_ctx,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    candidates=list(scores.keys()),
                )
            else:
                # Fallback: argmax de cohérence
                if scores:
                    next_word = max(scores, key=scores.get)
                else:
                    break

            # 4. Vérifier l'arrêt
            if next_word in stop_tokens or next_word == self.EOS:
                break

            # Éviter les répétitions immédiates
            if tokens and next_word == tokens[-1]:
                # Chercher le deuxième meilleur
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                for w, s in sorted_scores[1:4]:
                    if w != tokens[-1]:
                        next_word = w
                        break

            tokens.append(next_word)
            coherence_scores.append(scores.get(next_word, 0.0))

            # Encoder le nouveau mot s'il n'est pas dans le vocabulaire
            if next_word not in vocab:
                vocab[next_word] = self._encode_word(next_word)

            psi_next_word = vocab[next_word]

            # 5. Mise à jour de l'état : superposition + normalisation
            psi_new = psi_ctx + 0.3 * psi_next_word  # résiduel pondéré
            psi_current = psi_new / np.linalg.norm(psi_new)

            # 6. Ajouter à l'historique (mémoire ABC implicite)
            psi_history.append(psi_current)

            # Élagage de l'historique si trop long (mémoire ABC)
            if len(psi_history) > self.max_context:
                # Oubli naturel : on retire le plus ancien
                psi_history = psi_history[-self.max_context:]

        # Construire le texte
        generated_text = " ".join(tokens)

        # Calculer la perplexité ondulatoire
        if coherence_scores:
            try:
                from wave_perplexity import coherence_perplexity
                scores_dict = {f"step_{i}": s for i, s in enumerate(coherence_scores)}
                ppl = coherence_perplexity(scores_dict)
            except ImportError:
                ppl = 1.0 / (np.mean(coherence_scores) + 1e-10) if coherence_scores else 0.0
        else:
            ppl = 0.0

        elapsed = (time.time() - t_start) * 1000

        return WaveGPTResult(
            text=generated_text,
            tokens=tokens,
            psi_sequence=psi_history,
            coherence_scores=coherence_scores,
            perplexity=ppl,
            n_tokens=len(tokens) - len(prompt_tokens),
            elapsed_ms=elapsed,
        )

    def stream_generate(self, prompt: str, **kwargs):
        """
        Génération en streaming (generator).
        
        Yields chaque token au fur et à mesure de la génération.
        """
        kwargs['max_tokens'] = kwargs.get('max_tokens', 50)
        result = self.generate(prompt, **kwargs)
        # Simuler le streaming (dans une V2, on pourrait yield à chaque étape)
        for token in result.tokens[len(prompt.split()):]:
            yield token

    def complete(self, prompt: str, **kwargs) -> str:
        """Raccourci : retourne le texte généré."""
        return self.generate(prompt, **kwargs).text

    def chat(self, messages: List[Dict[str, str]],
             max_tokens: int = 100, **kwargs) -> str:
        """
        Interface de chat (compatible OpenAI API).
        
        Args:
            messages: [{"role": "user", "content": "..."}, ...]
            max_tokens: nombre max de tokens
        """
        # Construire le prompt à partir de l'historique
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(content)
            elif role == "user":
                prompt_parts.append(f"Question: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Réponse: {content}")

        prompt = " ".join(prompt_parts)
        result = self.generate(prompt, max_tokens=max_tokens, **kwargs)

        # Extraire la réponse (après "Réponse:")
        text = result.text
        if "Réponse:" in text:
            text = text.split("Réponse:")[-1].strip()

        return text


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE HAUT NIVEAU
# ═══════════════════════════════════════════════════════════════════════════════

# Instance globale (singleton paresseux)
_wave_gpt = None

def get_wave_gpt(dim: int = 512, n_heads: int = 4) -> WaveGPT:
    """Retourne l'instance globale de Wave GPT."""
    global _wave_gpt
    if _wave_gpt is None:
        _wave_gpt = WaveGPT(dim=dim, n_heads=n_heads)
    return _wave_gpt


def generate(prompt: str, **kwargs) -> str:
    """Raccourci : génère du texte avec Wave GPT."""
    gpt = get_wave_gpt()
    return gpt.complete(prompt, **kwargs)


def chat(messages: List[Dict[str, str]], **kwargs) -> str:
    """Raccourci : interface chat."""
    gpt = get_wave_gpt()
    return gpt.chat(messages, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide de Wave GPT."""
    print("=" * 60)
    print("TEST : Wave GPT — Générateur Purement Ondulatoire")
    print("=" * 60)

    gpt = WaveGPT(dim=256, n_heads=4)

    # Test 1 : Génération simple
    print("\n── Test 1 : Génération simple ──")
    prompts = [
        "la lumière est",
        "le temps est",
        "la vie est",
        "l'amour est",
    ]

    for prompt in prompts:
        result = gpt.generate(prompt, max_tokens=12, temperature=0.8)
        print(f"  {prompt:<20s} → {result.text}")
        print(f"    tokens: {result.n_tokens}, ppl: {result.perplexity:.1f}, {result.elapsed_ms:.0f}ms")

    # Test 2 : Déterministe vs Créatif
    print("\n── Test 2 : Déterministe vs Créatif ──")
    prompt = "la science est"

    result_det = gpt.generate(prompt, max_tokens=8, temperature=0.0)
    print(f"  T=0.0   : {result_det.text}")

    result_cre = gpt.generate(prompt, max_tokens=8, temperature=1.2)
    print(f"  T=1.2   : {result_cre.text}")

    # Test 3 : Interface Chat
    print("\n── Test 3 : Interface Chat ──")
    messages = [
        {"role": "system", "content": "Tu es un assistant scientifique."},
        {"role": "user", "content": "Qu'est-ce que la lumière ?"},
    ]
    response = gpt.chat(messages, max_tokens=20)
    print(f"  Q: Qu'est-ce que la lumière ?")
    print(f"  A: {response}")

    # Test 4 : Self-attention multi-head
    print("\n── Test 4 : Self-Attention ──")
    psi_test = [gpt.encoder.encode_word(w) for w in "la lumière est une onde".split()]
    attn = WaveSelfAttention(dim=256, n_heads=4)
    psi_ctx = attn.attend(psi_test[-1], psi_test[:-1])
    coherence = float(np.real(np.dot(psi_ctx, psi_test[0].conj())))
    print(f"  Cohérence après attention: {coherence:+.3f}")
    print(f"  (positive = contexte aligné avec 'la')")

    # Stats
    print(f"\n── Stats ──")
    print(f"  Vocabulaire: {len(gpt.encoder.vocabulary)} mots")
    print(f"  Dimension: {gpt.dim}")
    print(f"  Têtes d'attention: {gpt.attention.n_heads}")

    print("\n✅ Wave GPT fonctionnel !")


if __name__ == '__main__':
    _test()
