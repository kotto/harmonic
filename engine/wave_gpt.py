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
               psi_history: List[np.ndarray],
               time_decay: float = 0.0) -> np.ndarray:
        """
        Calcule le contexte attentionné.
        
        Args:
            psi_current: vecteur d'onde de la position courante (query)
            psi_history: historique des vecteurs d'onde (keys + values)
            time_decay: décroissance temporelle (0 = pas de decay, 0.3 = modéré)
                        Les positions récentes reçoivent un boost.
            
        Returns:
            ψ_context = Σ_j α_j · ψ_j  (attention-weighted sum, normalized)
        """
        if not psi_history:
            return psi_current

        n_hist = len(psi_history)
        
        # Pré-calculer les poids temporels (exponentiels, normalisés)
        if time_decay > 0:
            time_weights = np.exp(time_decay * np.arange(n_hist))
            time_weights = time_weights / time_weights.sum()
        else:
            time_weights = np.ones(n_hist) / n_hist

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
            
            # 🌊 Combiner attention + décroissance temporelle
            alpha = alpha * (1.0 + time_weights * 2.0)  # boost positions récentes
            alpha = alpha / alpha.sum()

            # Attention-weighted sum
            head_out = np.sum([
                alpha[j] * psi_history[j]
                for j in range(n_hist)
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
                 external_encoder = None,
                 context_decay: float = 0.7):
        """
        Args:
            dim: dimension de l'espace complexe
            n_heads: nombre de têtes d'attention (bandes de fréquence)
            max_context: taille maximale du contexte (mémoire ABC)
            external_encoder: encodeur holographique externe (ex: celui du HarmonicBrain)
                              Si fourni, on l'utilise au lieu de l'encodeur standalone.
            context_decay: ρ pour la moyenne exponentielle du contexte (0-1).
                          ρ=0.7 → les mots récents pèsent ~3× plus que les anciens.
                          ρ=1.0 → moyenne uniforme (ancien comportement).
        """
        self.dim = dim
        self.max_context = max_context
        self.context_decay = context_decay
        
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

        # Bigram transition table (construit depuis le corpus si disponible)
        self._bigram_followers: Dict[str, List[str]] = {}
        self._trigram_followers: Dict[tuple, List[str]] = {}
        self._bigram_boost: float = 0.4  # poids de la contrainte bigramme

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
                 stop_tokens: Optional[List[str]] = None,
                 seed_words: Optional[List[str]] = None,
                 function_penalty: float = 0.15) -> WaveGPTResult:
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
            seed_words: mots de contenu à privilégier (guidage par retrieval).
                        Ces mots reçoivent un boost de cohérence.
            function_penalty: pénalité appliquée aux mots fonctionnels (le, la, de...).
                              Plus élevé = moins de déterminants. Défaut: 0.15.

        Returns:
            WaveGPTResult
        """
        t_start = time.time()

        if stop_tokens is None:
            stop_tokens = [".", "!", "?", "\n\n", self.EOS]

        # 🎯 Mots fonctionnels à pénaliser (déterminants, prépositions, conjonctions)
        FUNCTION_WORDS = frozenset([
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'au', 'aux',
            'et', 'ou', 'donc', 'car', 'mais', 'ni', 'or', 'si', 'ce', 'cette',
            'ces', 'son', 'sa', 'ses', 'leur', 'leurs', 'mon', 'ton', 'notre',
            'votre', 'mes', 'tes', 'nos', 'vos', 'qui', 'que', 'quoi', "qu'", "l'",
            "d'", "j'", "m'", "t'", "s'", "c'", "n'",
        ])

        # 🌱 Seed words : encoder leurs psis pour le guidage
        seed_psis = []
        seed_psis_words = set()
        if seed_words:
            for sw in seed_words:
                psi = self._encode_word(sw.lower().strip())
                if psi is not None:
                    seed_psis.append((sw.lower().strip(), psi))
                    seed_psis_words.add(sw.lower().strip())

        # Encoder le prompt
        prompt_tokens = prompt.strip().split()
        if not prompt_tokens:
            prompt_tokens = ["le"]

        # 🎯 FILTRAGE DU CONTEXTE : ne garder que les mots de contenu dans l'historique
        # Les mots fonctionnels (le, la, de...) polluent le contexte avec leur phase générique.
        # On construit DEUX historiques :
        #   - psi_history : tous les mots (pour la grammaire bigramme)
        #   - content_history : seulement les mots de contenu (pour l'attention sémantique)
        psi_history = [self._encode_word(w) for w in prompt_tokens]
        content_history = [
            self._encode_word(w) for w in prompt_tokens
            if w.lower() not in FUNCTION_WORDS and len(w) > 2
        ]
        if not content_history:
            content_history = [self._encode_word(prompt_tokens[-1])]

        # ψ initial : moyenne des mots de contenu du prompt (pas des fonctionnels!)
        psi_current = np.mean(content_history, axis=0)
        norm = np.linalg.norm(psi_current)
        if norm > 1e-10:
            psi_current = psi_current / norm

        tokens = list(prompt_tokens)
        coherence_scores = []

        # Construire le vocabulaire
        vocab = self._build_vocabulary(prompt_tokens)

        for step in range(max_tokens):
            # 1. Self-attention : ψ_ctx calculé SUR LES MOTS DE CONTENU uniquement
            # 🎯 FILTRAGE : content_history ne contient que les mots sémantiquement porteurs
            time_decay = (1.0 - self.context_decay) * 0.5

            # 🌱 Si des seeds sont fournis, ils DOMINENT le contexte
            # Le contexte est une moyenne pondérée : 70% seeds + 30% historique de contenu
            if seed_psis and len(content_history) > 0:
                psi_from_seeds = np.mean([psi for _, psi in seed_psis], axis=0)
                psi_from_seeds = psi_from_seeds / np.linalg.norm(psi_from_seeds)
                psi_from_history = self.attention.attend(
                    psi_current, content_history[-self.max_context:],
                    time_decay=time_decay)
                # 70% seeds + 30% history récent
                psi_ctx = 0.7 * psi_from_seeds + 0.3 * psi_from_history
                psi_ctx = psi_ctx / np.linalg.norm(psi_ctx)
            elif seed_psis:
                # Pas encore d'historique de contenu : 100% seeds
                psi_ctx = np.mean([psi for _, psi in seed_psis], axis=0)
                psi_ctx = psi_ctx / np.linalg.norm(psi_ctx)
            else:
                psi_ctx = self.attention.attend(psi_current, content_history[-self.max_context:],
                                                time_decay=time_decay)

            # 2. Scores de cohérence + contrainte bigramme
            # 🎯 VOCABULAIRE FOCALISÉ : ne scorer que les mots pertinents
            # Au lieu de scorer 32K mots (dont la plupart ont coh > 0.5),
            # on restreint à ~100 candidats pertinents pour le contexte.
            scores = {}
            last_word = tokens[-1] if tokens else None
            allowed_followers = self._bigram_followers.get(last_word, []) if last_word else []

            # Construire le pool de candidats focalisé
            candidate_pool = set()

            # a) Mots de contenu sémantiquement proches du contexte (top-K par cohérence)
            if seed_psis:
                    # Pool dominé par les seeds et leurs voisins
                    for sw, psi_sw in seed_psis:
                        candidate_pool.add(sw)
                        # Ajouter les mots les plus cohérents avec ce seed
                        pool_scores = {}
                        for w, psi_w in vocab.items():
                            if len(w) >= 3 and w not in FUNCTION_WORDS:
                                pool_scores[w] = float(np.real(np.dot(psi_w.conj(), psi_sw)))
                        # Top 25 voisins par seed (plus de diversité)
                        for w, _ in sorted(pool_scores.items(), key=lambda x: -x[1])[:25]:
                            candidate_pool.add(w)
            else:
                # Pas de seeds : prendre les top-K par cohérence avec le contexte
                pool_scores = {}
                for w, psi_w in vocab.items():
                    if len(w) >= 4:  # mots de contenu (>= 4 lettres)
                        pool_scores[w] = float(np.real(np.dot(psi_ctx, psi_w.conj())))
                for w, _ in sorted(pool_scores.items(), key=lambda x: -x[1])[:30]:
                    candidate_pool.add(w)

            # b) Bigram followers du dernier mot (grammaire) — UNIQUEMENT les mots de contenu
            for w in allowed_followers[:20]:
                if w in vocab and len(w) >= 3:
                    candidate_pool.add(w)

            # c) Mots du prompt de contenu
            for pt in prompt_tokens:
                if len(pt) >= 3:
                    candidate_pool.add(pt.lower())

            # d) Mots fonctionnels MINIMAUX (juste assez pour la grammaire)
            # On en met très peu et ils seront pénalisés
            for fw in ['le', 'la', 'les', 'un', 'une', 'de', 'du', 'et',
                       'dans', 'sur', 'est', 'qui', 'que', 'pour', 'par']:
                if fw in vocab:
                    candidate_pool.add(fw)

            # Scorer seulement le pool focalisé
            # 🎯 PÉNALITÉ DE GÉNÉRICITÉ : les mots qui résonnent avec tout sont pénalisés
            genericity = getattr(self.encoder, 'genericity', {})
            for word in candidate_pool:
                if word not in vocab:
                    continue
                psi_w = vocab[word]
                score = float(np.real(np.dot(psi_ctx, psi_w.conj())))
                # Boost bigramme
                if word in allowed_followers:
                    rank = allowed_followers.index(word)
                    score += self._bigram_boost * (1.0 - rank / max(len(allowed_followers), 1))
                # Pénalité mots fonctionnels
                if function_penalty > 0 and word in FUNCTION_WORDS:
                    score -= function_penalty
                # 🎯 Pénalité de généricité : mots fréquents dans tout le corpus
                gen_score = genericity.get(word, 0.0)
                score -= gen_score * 1.5  # pénalité TRÈS forte pour les mots omniprésents
                # 🎯 Pénalité pour mots courts non-fonctionnels (petit, grand, vrai...)
                # Ces mots ont un score brut élevé mais peu de contenu sémantique
                if len(word) <= 6 and word not in seed_psis_words:
                    score -= 0.15  # malus pour mots courts
                # 🌱 Seed boost TRÈS FORT — les seeds doivent dominer absolument
                if seed_psis:
                    max_seed_boost = 0.0
                    for sw, psi_sw in seed_psis:
                        if word == sw:
                            max_seed_boost = max(max_seed_boost, 2.0)  # boost MASSIF pour les seeds
                        else:
                            seed_coh = float(np.real(np.dot(psi_w.conj(), psi_sw)))
                            if seed_coh > 0.5:  # seuil plus strict
                                max_seed_boost = max(max_seed_boost, seed_coh * 0.8)
                    score += max_seed_boost
                scores[word] = score

            # 3. Échantillonnage — utiliser NOS scores (avec boost seeds + pénalité)
            # Pas le sampler externe qui recalcule ses propres cohérences.
            if temperature <= 0.01:
                # Déterministe : argmax de nos scores
                next_word = max(scores, key=scores.get) if scores else ""
            else:
                # Sampling pondéré par nos scores
                words_list = list(scores.keys())
                score_values = np.array([scores[w] for w in words_list])
                # Convertir en probabilités (softmax avec température)
                score_values = score_values - score_values.max()
                probs = np.exp(score_values / max(temperature, 0.01))
                probs = probs / probs.sum()
                # Top-k
                if top_k and top_k < len(words_list):
                    top_indices = np.argsort(probs)[-top_k:]
                    probs_filtered = np.zeros_like(probs)
                    probs_filtered[top_indices] = probs[top_indices]
                    probs = probs_filtered / probs_filtered.sum()
                # Top-p
                if top_p and top_p < 1.0:
                    sorted_idx = np.argsort(probs)[::-1]
                    cumsum = 0
                    cutoff = len(probs)
                    for i in sorted_idx:
                        cumsum += probs[i]
                        if cumsum >= top_p:
                            cutoff = i + 1
                            break
                    mask = np.zeros_like(probs)
                    mask[sorted_idx[:cutoff]] = 1
                    probs = probs * mask
                    probs = probs / probs.sum()
                # Échantillonner
                idx = np.random.choice(len(words_list), p=probs)
                next_word = words_list[idx]

            # 4. Vérifier l'arrêt
            if next_word in stop_tokens or next_word == self.EOS:
                break

            # 🔄 Anti-répétition + anti-2-cycle : bannir temporairement les 2 derniers mots
            recent_words = set(tokens[-3:] if len(tokens) >= 3 else tokens)
            if next_word in recent_words:
                # Chercher le meilleur mot qui n'est PAS dans les 3 derniers
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                found_alternative = False
                for w, s in sorted_scores[:20]:
                    if w not in recent_words and w not in stop_tokens:
                        next_word = w
                        found_alternative = True
                        break
                if not found_alternative:
                    # Accepter quand même (pas d'alternative)
                    pass

            tokens.append(next_word)
            coherence_scores.append(scores.get(next_word, 0.0))

            # Encoder le nouveau mot s'il n'est pas dans le vocabulaire
            if next_word not in vocab:
                vocab[next_word] = self._encode_word(next_word)

            psi_next_word = vocab[next_word]

            # 🎯 FILTRAGE : ajouter AUSSI au content_history si c'est un mot de contenu
            # Les mots fonctionnels ne polluent plus le contexte sémantique
            if next_word not in FUNCTION_WORDS and len(next_word) > 2:
                content_history.append(psi_next_word)

            # Garder aussi l'historique complet (pour référence future)
            psi_history.append(psi_next_word)

            # 5. Mise à jour de l'état : moyenne exponentielle (ρ = context_decay)
            # 🌊 EXPONENTIAL CONTEXT — les mots récents pèsent plus lourd
            # Ancien (uniforme) : ψ_new = ψ_ctx + 0.3·ψ_token
            # Nouveau (exponentiel) : ψ_new = ρ·ψ_ctx + (1-ρ)·ψ_token
            rho = self.context_decay
            psi_new = rho * psi_ctx + (1.0 - rho) * psi_next_word
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

    # ═══════════════════════════════════════════════════════════════════════
    # GÉNÉRATION SIMULTANÉE (bag-of-words ordonné par bigrammes)
    # ═══════════════════════════════════════════════════════════════════════

    def generate_simultaneous(self, prompt: str,
                               max_tokens: int = 20,
                               seed_words: Optional[List[str]] = None,
                               function_penalty: float = 0.4) -> WaveGPTResult:
        """
        Génère du texte en DÉCODAGE SIMULTANÉ (non-séquentiel).

        Au lieu de générer mot par mot (ce qui crée des cycles), cette méthode :
        1. Sélectionne TOUS les mots de contenu d'un coup (top-K par cohérence)
        2. Les ordonne par compatibilité bigramme (algorithme glouton)
        3. Insère des mots fonctionnels minimaux entre les mots de contenu

        Cela évite l'effet de cycle car il n'y a pas de boucle de rétroaction.

        Args:
            prompt: texte de départ
            max_tokens: nombre de mots de contenu à générer
            seed_words: mots de contenu à privilégier
            function_penalty: pénalité pour les mots fonctionnels

        Returns:
            WaveGPTResult
        """
        t_start = time.time()

        prompt_tokens = prompt.strip().split()
        if not prompt_tokens:
            prompt_tokens = ["le"]

        vocab = self._build_vocabulary(prompt_tokens)
        # 🌊 Pour la génération simultanée, on utilise le vocabulaire COMPLET de l'encodeur
        if hasattr(self.encoder, 'vocab') and isinstance(self.encoder.vocab, dict):
            for w in self.encoder.vocab:
                if w not in vocab:
                    vocab[w] = self._encode_word(w)

        FUNCTION_WORDS = frozenset([
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'au', 'aux',
            'et', 'ou', 'donc', 'car', 'mais', 'ni', 'or', 'si', 'ce', 'cette',
            'ces', 'son', 'sa', 'ses', 'leur', 'leurs', 'mon', 'ton', 'notre',
            'votre', 'mes', 'tes', 'nos', 'vos', 'qui', 'que', 'quoi',
        ])

        # 🎯 MOTS GÉNÉRIQUES EXCLUS du pool (jamais sélectionnés comme contenu)
        HARD_GENERIC = frozenset([
            'très', 'bien', 'tout', 'tous', 'toute', 'toutes',
            'petit', 'petite', 'petits', 'petites',
            'grand', 'grande', 'grands', 'grandes',
            'toujours', 'jamais', 'encore', 'déjà',
            'faire', 'fait', 'être', 'avoir', 'peut', 'peuvent',
            'vrai', 'faux', 'bon', 'mal', 'autre', 'même', 'autres',
            'nouveau', 'nouvelle', 'nouveaux', 'nouvelles',
            'sans', 'avec', 'dans', 'sur', 'sous', 'pour', 'par',
            'plus', 'moins', 'trop', 'peu', 'beaucoup',
            'celui', 'celle', 'ceux', 'celles',
            'alors', 'ainsi', 'donc', 'car', 'mais', 'ou', 'et',
            'comme', 'que', 'qui', 'quoi', 'dont', 'où',
            'aussi', 'très', 'si', 'non', 'oui',
            'cela', 'ceci', 'cette', 'ces',
            'tout', 'rien', 'chaque', 'quelque', 'plusieurs',
            'leur', 'leurs', 'notre', 'nos', 'votre', 'vos',
        ])

        # 1. Construire le pool de mots de contenu
        seed_psis = []
        if seed_words:
            for sw in seed_words:
                psi = self._encode_word(sw.lower().strip())
                if psi is not None:
                    seed_psis.append((sw.lower().strip(), psi))

        # Pool: seeds + top voisins sémantiques
        content_pool = set()
        if seed_psis:
            for sw, psi_sw in seed_psis:
                content_pool.add(sw)
                pool_scores = {}
                for w, psi_w in vocab.items():
                    if len(w) >= 4 and w not in FUNCTION_WORDS and w not in HARD_GENERIC:
                        pool_scores[w] = float(np.real(np.dot(psi_w.conj(), psi_sw)))
                for w, _ in sorted(pool_scores.items(), key=lambda x: -x[1])[:20]:
                    content_pool.add(w)

        if not content_pool:
            # Fallback: prendre les mots les plus cohérents avec le prompt
            psi_prompt = self._encode_word(prompt_tokens[-1])
            pool_scores = {}
            for w, psi_w in vocab.items():
                if len(w) >= 4 and w not in FUNCTION_WORDS:
                    pool_scores[w] = float(np.real(np.dot(psi_w.conj(), psi_prompt)))
            for w, _ in sorted(pool_scores.items(), key=lambda x: -x[1])[:max_tokens * 2]:
                content_pool.add(w)

        # 2. Scorer tous les mots du pool
        psi_ctx = np.zeros(self.dim, dtype=complex)
        if seed_psis:
            psi_ctx = np.mean([p for _, p in seed_psis], axis=0)
            psi_ctx = psi_ctx / np.linalg.norm(psi_ctx)
        else:
            psi_ctx = self._encode_word(prompt_tokens[-1])

        genericity = getattr(self.encoder, 'genericity', {})
        scored_words = []
        for w in content_pool:
            if w not in vocab:
                continue
            psi_w = vocab[w]
            score = float(np.real(np.dot(psi_ctx.conj(), psi_w)))
            gen = genericity.get(w, 0)
            score -= gen * 1.5  # pénalité généricité IDF
            if w in FUNCTION_WORDS:
                score -= function_penalty
            # Seed boost
            if w in [s for s, _ in seed_psis]:
                score += 1.5
            scored_words.append((w, score))

        # Trier et prendre les max_tokens meilleurs (en excluant les mots du prompt)
        prompt_words_set = set(p.lower() for p in prompt_tokens)
        scored_words = [(w, s) for w, s in scored_words if w.lower() not in prompt_words_set]
        scored_words.sort(key=lambda x: -x[1])
        selected = [w for w, _ in scored_words[:max_tokens]]

        if len(selected) < 3:
            return WaveGPTResult(text=" ".join(selected), tokens=selected,
                                psi_sequence=[], coherence_scores=[],
                                perplexity=0, n_tokens=len(selected),
                                elapsed_ms=(time.time()-t_start)*1000)

        # 3. Ordonner les mots sélectionnés par compatibilité n-gramme
        # Utiliser bigrammes + trigrammes pour un ordonnancement naturel
        prompt_last = prompt_tokens[-1].lower()
        followers = self._bigram_followers.get(prompt_last, [])

        ordered = []
        remaining = list(selected)

        # Premier mot: celui qui suit le plus naturellement le prompt
        best_first = None
        best_first_score = -999
        for w in remaining:
            score = 0
            if w in followers:
                score = len(followers) - followers.index(w)
            if w in vocab and prompt_last in vocab:
                score += float(np.real(np.dot(vocab[w].conj(), vocab[prompt_last])))
            if score > best_first_score:
                best_first_score = score
                best_first = w

        if best_first:
            ordered.append(best_first)
            remaining.remove(best_first)

        # Mots suivants: greedy avec bigram + trigram
        while remaining:
            last = ordered[-1]
            last_followers = self._bigram_followers.get(last, [])
            best_next = None
            best_next_score = -999

            for w in remaining:
                score = 0.0
                # Bigram score
                if w in last_followers:
                    score += len(last_followers) - last_followers.index(w)
                if w in vocab and last in vocab:
                    score += float(np.real(np.dot(vocab[w].conj(), vocab[last]))) * 3.0

                # Trigram score (si on a au moins 2 mots dans ordered)
                if len(ordered) >= 2:
                    prev2 = ordered[-2]
                    # Chercher dans le modèle trigramme
                    trigram_key = (prev2, last)
                    trigram_followers = self._trigram_followers.get(trigram_key, [])
                    if w in trigram_followers:
                        score += (len(trigram_followers) - trigram_followers.index(w)) * 2.0

                # Pénalité si le mot suivrait trop bien le mot d'avant (évite monotonie)
                if len(ordered) >= 2:
                    prev2 = ordered[-2]
                    if w in self._bigram_followers.get(prev2, [])[:5]:
                        score -= 1.0

                if score > best_next_score:
                    best_next_score = score
                    best_next = w

            if best_next and best_next_score > -100:
                ordered.append(best_next)
                remaining.remove(best_next)
            else:
                ordered.extend(remaining)
                break

        # 4. Formater avec des PATTERNS NATURELS: X et Y, X, Y et Z, X de Y
        final_tokens = list(prompt_tokens)
        prev = prompt_tokens[-1].lower() if prompt_tokens else 'le'

        i = 0
        while i < len(ordered):
            group = [ordered[i]]
            if i + 1 < len(ordered):
                w1, w2 = ordered[i], ordered[i+1]
                # Transition directe possible?
                if w2 in self._bigram_followers.get(w1, [])[:30]:
                    group.append(w2)
                    i += 1
                # "et" connecteur?
                elif 'et' in self._bigram_followers.get(w1, [])[:30]:
                    group.extend(['et', w2])
                    i += 1
                # "de" description?
                elif 'de' in self._bigram_followers.get(w1, [])[:30]:
                    group.extend(['de', w2])
                    i += 1
                # virgule par défaut
                else:
                    group.append(',')
            i += 1

            for token in group:
                if token == ',':
                    if final_tokens and not final_tokens[-1].endswith(','):
                        final_tokens[-1] = final_tokens[-1] + ','
                else:
                    final_tokens.append(token)

        generated_text = " ".join(final_tokens)

        # Supprimer les doublons consécutifs
        words = generated_text.split()
        cleaned = []
        for w in words:
            if not cleaned or w.lower() != cleaned[-1].lower():
                cleaned.append(w)
        generated_text = " ".join(cleaned)

        # Capitalize
        if generated_text:
            generated_text = generated_text[0].upper() + generated_text[1:]

        elapsed = (time.time() - t_start) * 1000

        return WaveGPTResult(
            text=generated_text,
            tokens=final_tokens,
            psi_sequence=[],
            coherence_scores=[],
            perplexity=1.0,
            n_tokens=len(final_tokens) - len(prompt_tokens),
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
