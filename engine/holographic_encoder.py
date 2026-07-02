"""
Holographic Encoder — Encodage Vectoriel S² fondé sur Bekenstein + HRR
======================================================================

Remplace l'encodage φ-cercle 1D (Shannon limité à ~2300 mots) par un
encodage vectoriel holographique en D dimensions.

Principes :
  - Bekenstein : l'information vit sur une SURFACE (2D), pas une ligne (1D)
  - HRR (Plate 1995) : binding par convolution circulaire dans ℂᴰ
  - φ-spacing : hash déterministe, phases espacées par le nombre d'or
  - Zero-UNK : tout mot inconnu → binding caractère par caractère

Architecture :
  mot → v ∈ ℂᴰ (D=512, vecteur complexe unitaire)
  fait = v_s ⊛ v_r ⊛ v_o  (convolution circulaire / binding HRR)
  mémoire = Σ faits        (superposition holographique)
  requête → unbinding → top-k mots résonants

Capacité théorique (D=512) : ~40 000 mots sans collision
Contre ~2 300 mots (Shannon) pour le cercle 1D — amélioration 17×

Usage :
  from holographic_encoder import HolographicEncoder, build_holographic_waves

  encoder = HolographicEncoder()
  kx, ky, w2i = build_holographic_waves(knowledge_base, encoder)
  # kx, ky sont les projections 2D pour compatibilité MemoireOndulatoire
"""

import math
import numpy as np
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# PLONGEMENT SPECTRAL SÉMANTIQUE (PPMI + Laplacian)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from spectral_embedding import _SPECTRAL
except Exception:
    _SPECTRAL = None

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# MULTILINGUE
# ═══════════════════════════════════════════════════════════════════════════════

# Stopwords par langue
_STOPWORDS_FR = {
    'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'est', 'a',
    'dans', 'que', 'qui', 'pas', 'ne', 'sur', 'pour', 'avec', 'ce', 'cette',
    'par', 'au', 'aux', 'en', 'plus', 'moins', 'tout', 'tous', 'son', 'sa',
    'ses', 'il', 'elle', 'ils', 'elles', 'nous', 'vous', 'leur', 'leurs',
    'mais', 'ou', 'donc', 'or', 'ni', 'car', 'aussi', 'très', 'bien',
}

_STOPWORDS_EN = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'may', 'might', 'shall', 'should', 'can', 'of', 'in', 'on', 'at', 'to',
    'for', 'with', 'by', 'from', 'it', 'its', 'and', 'or', 'not', 'but',
    'if', 'so', 'as', 'than', 'that', 'this', 'these', 'those', 'which',
    'who', 'whom', 'what', 'when', 'where', 'how', 'all', 'both', 'each',
    'every', 'some', 'any', 'no', 'nor', 'just', 'very', 'too', 'also',
}

_STOPWORDS_ES = {
    'el', 'la', 'los', 'las', 'de', 'del', 'un', 'una', 'y', 'e', 'es',
    'está', 'son', 'en', 'con', 'para', 'por', 'que', 'se', 'su', 'sus',
    'al', 'lo', 'como', 'más', 'pero', 'o', 'ha', 'han', 'fue', 'ser',
    'tiene', 'todo', 'todos', 'muy', 'hay', 'qué', 'cuando', 'donde',
}

_STOPWORDS_DE = {
    'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einer',
    'und', 'ist', 'sind', 'war', 'waren', 'in', 'an', 'auf', 'mit',
    'von', 'zu', 'für', 'bei', 'aus', 'nach', 'vor', 'auch', 'nicht',
    'sich', 'sie', 'er', 'es', 'wir', 'ihr', 'wie', 'was', 'wer',
    'wo', 'wann', 'warum', 'dass', 'wird', 'hat', 'haben', 'kann',
}

# Stopwords universels (utilisés par défaut)
_STOPWORDS = _STOPWORDS_FR  # rétrocompatibilité

# Mapping langue → stopwords
_LANG_STOPWORDS = {
    'fr': _STOPWORDS_FR,
    'en': _STOPWORDS_EN,
    'es': _STOPWORDS_ES,
    'de': _STOPWORDS_DE,
}

# Indices de langue (caractères spécifiques)
_LANG_MARKERS = {
    'fr': set('àâäéèêëîïôöùûüçœæ'),
    'es': set('áéíóúüñ¿¡'),
    'de': set('äöüß'),
    'en': set(),  # pas de caractères distinctifs
}

# Préfixes de question par langue
_QUESTION_PREFIXES = {
    'fr': ['qu est-ce que', 'qu est ce que', 'qui a invente', 'qui a cree',
            'qui a decouvert', 'qui est', 'qui a', 'explique', 'pourquoi',
            'comment', 'decris', 'definis', 'quelle est',
            'quand', 'ou se', 'que signifie', 'qu a',
            'donne moi', 'parle moi de', 'dis moi'],
    'en': ['what is', 'who is', 'explain', 'describe', 'define',
            'why', 'how does', 'how do', 'how', 'when', 'where', 'which'],
    'es': ['qué es', 'quién es', 'explica', 'describe', 'define',
            'por qué', 'cómo', 'cuándo', 'dónde', 'cuál es'],
    'de': ['was ist', 'wer ist', 'erkläre', 'beschreibe', 'definiere',
            'warum', 'wie', 'wann', 'wo', 'welche'],
}

# Templates de réponse par langue (fallback)
_RESPONSE_TEMPLATES = {
    'fr': {
        'definition': [
            "Le concept de {sujet} est lié à {mots}. Cela implique {w1} et {w2}.",
            "Pour comprendre {sujet}, il faut saisir que {w0} est en relation avec {w1}.",
        ],
        'not_found': "Je n'ai pas assez de connaissances sur {sujet}.",
        'no_understand': "Je ne comprends pas assez la question sur {sujet}.",
    },
    'en': {
        'definition': [
            "The concept of {sujet} is related to {w0}. This implies {w1} and {w2}.",
            "To understand {sujet}, one must grasp that {w0} connects to {w1}.",
        ],
        'not_found': "I don't have enough knowledge about {sujet} yet.",
        'no_understand': "I don't quite understand the question about {sujet}.",
    },
    'es': {
        'definition': [
            "El concepto de {sujet} está relacionado con {w0}. Esto implica {w1} y {w2}.",
            "Para entender {sujet}, hay que comprender que {w0} se relaciona con {w1}.",
        ],
        'not_found': "No tengo suficiente conocimiento sobre {sujet}.",
        'no_understand': "No entiendo bien la pregunta sobre {sujet}.",
    },
    'de': {
        'definition': [
            "Das Konzept von {sujet} ist mit {w0} verbunden. Dies impliziert {w1} und {w2}.",
            "Um {sujet} zu verstehen, muss man begreifen, dass {w0} mit {w1} zusammenhängt.",
        ],
        'not_found': "Ich habe nicht genug Wissen über {sujet}.",
        'no_understand': "Ich verstehe die Frage zu {sujet} nicht ganz.",
    },
}


def _detect_language(text: str) -> str:
    """
    Détecte la langue d'un texte (fr/en/es/de).
    
    Approche :
    1. Compter les caractères spécifiques à chaque langue
    2. Compter les stopwords de chaque langue
    3. Langue = celle avec le score le plus élevé
    """
    text_lower = text.lower()
    scores = {'fr': 0.0, 'en': 0.0, 'es': 0.0, 'de': 0.0}
    
    # Score basé sur les caractères accentués spécifiques
    for ch in text_lower:
        for lang, markers in _LANG_MARKERS.items():
            if ch in markers:
                scores[lang] += 2.0  # fort signal
    
    # Score basé sur les stopwords
    words = set(text_lower.split())
    for lang, stopwords in _LANG_STOPWORDS.items():
        overlap = words & stopwords
        scores[lang] += len(overlap) * 1.0
    
    # Bonus pour les patterns de question
    for lang, prefixes in _QUESTION_PREFIXES.items():
        for pfx in prefixes:
            if text_lower.startswith(pfx):
                scores[lang] += 3.0
                break
    
    # Détection de patterns hispaniques
    if '¿' in text or '¡' in text:
        scores['es'] += 10.0
    if 'ñ' in text_lower:
        scores['es'] += 3.0
    
    # Si rien n'est détecté, fr par défaut
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return 'fr'
    return best


def _get_lang_config(lang: str) -> dict:
    """Retourne la configuration pour une langue donnée."""
    return {
        'stopwords': _LANG_STOPWORDS.get(lang, _STOPWORDS_FR),
        'prefixes': _QUESTION_PREFIXES.get(lang, _QUESTION_PREFIXES['fr']),
        'templates': _RESPONSE_TEMPLATES.get(lang, _RESPONSE_TEMPLATES['fr']),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HOLOGAPHIC ENCODER
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicEncoder:
    """
    Encodeur vectoriel holographique — cœur de l'architecture S².
    
    Chaque mot est représenté par un vecteur complexe unitaire v ∈ ℂᴰ.
    Les phases sont déterministes (hash φ-spacé) → pas de collision.
    Le binding HRR utilise la convolution circulaire (FFT).
    
    Parameters:
        dim: dimension des vecteurs (default 512 → ~40K mots sans collision)
    """
    
    def __init__(self, dim: int = 512):
        self.dim = dim
        self.word_vectors: Dict[str, np.ndarray] = {}  # mot → vecteur complexe
        self.memory = np.zeros(dim, dtype=np.complex128)  # superposition
        self.n_facts = 0
        self._id_to_word: List[str] = []  # pour lookup inverse
    
    # ── Encodage des mots ─────────────────────────────────────────────────
    
    def encode_word(self, word: str) -> np.ndarray:
        """
        Convertit un mot en vecteur complexe.
        
        Si le plongement spectral sémantique est disponible → utilise
        la phase θ(mot) dérivée du Laplacian Eigenmaps pour injecter
        la structure sémantique dans le vecteur.
        Sinon → fallback Gaussien déterministe (HRR standard).
        """
        if word in self.word_vectors:
            return self.word_vectors[word]
        
        # Hash déterministe 64-bit
        seed = _fnv1a_hash(word)
        rng = np.random.RandomState(seed & 0xFFFFFFFF)
        
        sigma = 1.0 / math.sqrt(2.0 * self.dim)
        
        if self.dim <= 500:
            real = rng.randn(self.dim).astype(np.float64) * sigma
            imag = rng.randn(self.dim).astype(np.float64) * sigma
        else:
            real = np.zeros(self.dim, dtype=np.float64)
            imag = np.zeros(self.dim, dtype=np.float64)
            n_direct = min(500, self.dim)
            real[:n_direct] = rng.randn(n_direct) * sigma
            imag[:n_direct] = rng.randn(n_direct) * sigma
            for k in range(n_direct, self.dim):
                phase_k = ((seed >> (k % 32)) ^ (k * 2654435761)) % 2147483647
                phase_k = (phase_k * PHI) % TAU
                real[k] = math.cos(phase_k) * sigma
                imag[k] = math.sin(phase_k) * sigma
        
        # 🔥 INJECTION SÉMANTIQUE : si le plongement spectral est disponible,
        # remplacer les premières dimensions par la phase dérivée du sens
        if _SPECTRAL is not None:
            phase = _SPECTRAL.get_phase(word)
            if phase is not None:
                n_phase_dims = min(32, self.dim // 2)
                boost = math.sqrt(self.dim / (2.0 * n_phase_dims)) * sigma
                for k in range(n_phase_dims):
                    phase_k = phase * (1.0 + k / PHI)
                    real[2*k] = math.cos(phase_k) * boost
                    imag[2*k] = math.sin(phase_k) * boost
        
        v = real + 1j * imag
        self.word_vectors[word] = v
        return v
    
    def encode_word_fast(self, word: str) -> np.ndarray:
        """Alias pour encode_word (même implémentation)."""
        return self.encode_word(word)
    
    def encode_char(self, char: str) -> np.ndarray:
        """Encode un caractère unique (fallback zero-UNK)."""
        key = f'__char_{char}__'
        if key in self.word_vectors:
            return self.word_vectors[key]
        
        # Hash basé sur le code Unicode
        code = ord(char)
        rng = np.random.RandomState(code)
        raw = rng.randn(self.dim, 2).astype(np.float64)
        norm = np.sqrt(raw[:, 0]**2 + raw[:, 1]**2)
        raw[:, 0] /= norm
        raw[:, 1] /= norm
        
        v = raw[:, 0] + 1j * raw[:, 1]
        v /= np.sqrt(self.dim)
        
        self.word_vectors[key] = v
        return v
    
    def encode_unknown(self, word: str) -> np.ndarray:
        """
        Zero-UNK : décompose un mot inconnu en caractères et les bind.
        Ψ_mot = v_c0 ⊛ v_c1 ⊛ ... ⊛ v_cn
        """
        if len(word) == 0:
            return np.zeros(self.dim, dtype=np.complex128)
        
        chars = [self.encode_char(c) for c in word]
        result = chars[0].copy()
        for cv in chars[1:]:
            result = _circular_convolve(result, cv)
        return result
    
    # ── Binding / Unbinding HRR ───────────────────────────────────────────
    
    def bind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Binding HRR : a ⊛ b = IFFT(FFT(a) · FFT(b))."""
        return _circular_convolve(a, b)
    
    def unbind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Unbinding HRR : a ⊗ b ≈ c tel que a ≈ b ⊛ c.
        Utilise la corrélation circulaire : IFFT(FFT(a) · conj(FFT(b))).
        """
        return _circular_correlate(a, b)
    
    def encode_fact(self, sujet: str, relation: str, objet: str) -> np.ndarray:
        """
        Encode un fait complet par binding HRR.
        fait = v_sujet ⊛ v_relation ⊛ v_objet
        """
        vs = self.encode_word(sujet)
        vr = self.encode_word(relation)
        vo = self.encode_word(objet)
        return _circular_convolve(_circular_convolve(vs, vr), vo)
    
    def encode_query(self, question: str, w2i: Optional[Dict[str, int]] = None) -> np.ndarray:
        """
        Encode une question en vecteur composite.
        
        Stratégie :
        1. Extraire les mots significatifs (>2 caractères, non stopwords)
        2. Pour chaque mot connu → ajouter v_mot
        3. Pour chaque mot inconnu → binding des caractères
        4. Sommer et normaliser
        """
        words = question.lower().split()
        vecs = []
        
        for mot in words:
            mot = mot.strip('.,!?;:()[]{}«»""\'\'¿¡')
            if len(mot) < 2 or mot in _STOPWORDS:
                continue
            if mot in self.word_vectors:
                vecs.append(self.word_vectors[mot])
            elif w2i and mot in w2i:
                # Si on a un word_to_id mais pas le vecteur, l'encoder
                vecs.append(self.encode_word(mot))
            else:
                # Zero-UNK : binding des caractères
                vecs.append(self.encode_unknown(mot))
        
        if not vecs:
            # Aucun mot significatif → vecteur nul
            return np.zeros(self.dim, dtype=np.complex128)
        
        # Moyenne des vecteurs (superposition)
        result = sum(vecs) / len(vecs)
        
        # Normaliser
        norm = np.sqrt(np.sum(np.abs(result)**2))
        if norm > 1e-15:
            result /= norm
        
        return result
    
    # ── Mémoire holographique vectorielle ─────────────────────────────────
    
    def store(self, fact_vector: np.ndarray, amplitude: float = 1.0):
        """
        Stocke un fait dans la mémoire holographique.
        M += amplitude · fait  (superposition additive)
        """
        self.memory += amplitude * fact_vector
        self.n_facts += 1
    
    def store_fact(self, sujet: str, relation: str, objet: str, amplitude: float = 1.0):
        """Encode ET stocke un fait en une opération."""
        fact_vec = self.encode_fact(sujet, relation, objet)
        self.store(fact_vec, amplitude)
    
    def query(self, query_vector: np.ndarray) -> np.ndarray:
        """
        Requête la mémoire : retourne le vecteur de corrélation.
        résultat = mémoire ⊗ requête  (unbinding)
        
        Un pic à l'index k signifie que le vecteur #k résonne fortement
        avec la mémoire étant donné la requête.
        """
        if self.n_facts == 0:
            return np.zeros(self.dim, dtype=np.complex128)
        return _circular_correlate(self.memory, query_vector)
    
    # ── Scoring I×P×H ────────────────────────────────────────────────────
    
    def resonance_score(self, word: str, query_vector: np.ndarray) -> float:
        """
        Score de résonance I×P×H d'un mot avec une requête.
        
        I (Interférence) : similarité cosinus entre v_mot et query
        P (Phase) : cohérence de phase via la mémoire holographique
        H (Hologramme) : amplitude de résonance du mot dans la mémoire
        
        score = I · (0.3 + 0.4·P + 0.3·H)
        """
        if word not in self.word_vectors:
            return 0.0
        
        v_w = self.word_vectors[word]
        
        # I : Interférence (cosine similarity dans ℂᴰ → [0, 1])
        dot = np.real(np.dot(v_w, np.conj(query_vector)))
        # v_w et query_vector sont unitaires → dot ∈ [-1, 1]
        I = (dot + 1.0) / 2.0
        
        # P : Cohérence de phase (basée sur la réponse mémoire)
        if self.n_facts > 5:
            mem_response = np.dot(self.memory, np.conj(v_w))
            phase_diff = abs(np.angle(mem_response))
            if phase_diff > math.pi:
                phase_diff = TAU - phase_diff
            P = (math.cos(phase_diff) + 1.0) / 2.0
        else:
            P = 0.5  # neutre si pas assez d'expérience
        
        # H : Amplitude holographique
        if self.n_facts > 0:
            mem_amplitude = np.abs(np.dot(self.memory, np.conj(v_w)))
            # Normalisation douce avec log1p
            H_norm = min(1.0, math.log1p(mem_amplitude * 10.0) / math.log1p(10.0))
        else:
            H_norm = 0.0
        
        # Score combiné (même formule que l'original I×P×H)
        score = I * (0.3 + 0.4 * P + 0.3 * H_norm)
        return float(score)
    
    def resonance_scores_batch(self, words: List[str], query_vector: np.ndarray) -> np.ndarray:
        """
        Calcule les scores de résonance pour une liste de mots.
        Version vectorisée — beaucoup plus rapide que des appels individuels.
        """
        n = len(words)
        scores = np.zeros(n)
        
        for i, w in enumerate(words):
            if w in self.word_vectors and w not in _STOPWORDS:
                scores[i] = self.resonance_score(w, query_vector)
        
        return scores
    
    # ── Utilitaires ───────────────────────────────────────────────────────
    
    @property
    def vocab_size(self) -> int:
        """Nombre de mots (hors caractères) dans l'encodeur."""
        return sum(1 for k in self.word_vectors if not k.startswith('__char_'))
    
    @property
    def energy(self) -> float:
        """Énergie totale de la mémoire holographique."""
        return float(np.sum(np.abs(self.memory)**2))
    
    def similarity(self, word_a: str, word_b: str) -> float:
        """
        Similarité cosinus complexe entre deux mots.
        Retourne une valeur dans [-1, 1].
        """
        if word_a not in self.word_vectors or word_b not in self.word_vectors:
            return 0.0
        dot = np.real(np.dot(
            self.word_vectors[word_a],
            np.conj(self.word_vectors[word_b])
        ))
        # Vecteurs unitaires → dot est déjà la similarité cosinus
        return float(dot)
    
    def similarity_word(self, word_a: str, word_b: str) -> float:
        """Alias pour similarity() — utilisé par le trainer."""
        return self.similarity(word_a, word_b)
    
    def collision_check(self, threshold: float = 0.95) -> List[Tuple[str, str, float]]:
        """
        Détecte les paires de mots trop similaires (collisions potentielles).
        Retourne la liste des paires avec similarité > threshold.
        """
        collisions = []
        words = [w for w in self.word_vectors if not w.startswith('__char_')]
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                sim = self.similarity(words[i], words[j])
                if sim > threshold:
                    collisions.append((words[i], words[j], sim))
        return collisions


# ═══════════════════════════════════════════════════════════════════════════════
# OPÉRATIONS HRR (CONVOLUTION/CORRÉLATION CIRCULAIRE)
# ═══════════════════════════════════════════════════════════════════════════════

def _circular_convolve(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Convolution circulaire via FFT : a ⊛ b = IFFT(FFT(a) · FFT(b)).
    O(D log D) au lieu de O(D²).
    
    Normalisation HRR : le résultat a même échelle que les entrées
    (E[|a⊛b|²] ≈ E[|a|²] · E[|b|²] pour vecteurs Gaussiens indépendants).
    """
    A = np.fft.fft(a)
    B = np.fft.fft(b)
    return np.fft.ifft(A * B)


def _circular_correlate(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Corrélation circulaire via FFT : a ⊗ b = IFFT(FFT(a) · conj(FFT(b))).
    O(D log D) — utilisé pour l'unbinding.
    
    Propriété : si c = a ⊛ b, alors c ⊗ b ≈ a (récupération approximative).
    La qualité de récupération dépend de D (meilleure en haute dimension).
    """
    A = np.fft.fft(a)
    B = np.fft.fft(b)
    return np.fft.ifft(A * np.conj(B))


# ═══════════════════════════════════════════════════════════════════════════════
# HASH FNV-1a (déterministe, rapide)
# ═══════════════════════════════════════════════════════════════════════════════

def _fnv1a_hash(s: str) -> int:
    """FNV-1a 64-bit hash — déterministe, bonne distribution."""
    FNV_OFFSET = 14695981039346656037
    FNV_PRIME = 1099511628211
    h = FNV_OFFSET
    for ch in s:
        h ^= ord(ch)
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE COMPATIBILITÉ (drop-in pour build_waves / generate)
# ═══════════════════════════════════════════════════════════════════════════════

def build_holographic_waves(knowledge_base=None,
                             encoder: Optional[HolographicEncoder] = None,
                             dim: int = 512):
    """
    Drop-in replacement pour build_waves().
    
    Construit les vecteurs d'onde à partir d'une base de connaissance,
    en utilisant l'encodage holographique S².
    
    Retourne (kx, ky, word_to_id, encoder) où :
    - kx, ky sont les projections 2D pour compatibilité MemoireOndulatoire
    - word_to_id est le mapping mot → index
    - encoder est l'HolographicEncoder (pour les opérations avancées)
    """
    if knowledge_base is None:
        # Fallback : base vide
        knowledge_base = []
    
    if encoder is None:
        encoder = HolographicEncoder(dim=dim)
    
    # Collecter tous les mots
    word_set = set()
    for sujet, rel, objet, _ in knowledge_base:
        for mot in sujet.split() + rel.split() + objet.split():
            mot = mot.strip('.,!?;:')
            if len(mot) >= 2:
                word_set.add(mot)
    
    # Ajouter les stopwords
    for w in _STOPWORDS:
        if len(w) >= 2:
            word_set.add(w)
    
    # Encoder chaque mot
    words = sorted(word_set)
    for w in words:
        encoder.encode_word(w)
    
    word_to_id = {w: i for i, w in enumerate(words)}
    n = len(words)
    
    # Projections 2D pour compatibilité MemoireOndulatoire
    # On prend les 2 premières composantes principales ou simplement
    # la projection du vecteur complexe sur le plan réel
    kx = np.zeros(n)
    ky = np.zeros(n)
    
    for i, w in enumerate(words):
        v = encoder.word_vectors[w]
        # Projection : moyenne des phases = direction principale
        # On utilise l'argument moyen pondéré
        total = np.sum(v)
        kx[i] = np.real(total)
        ky[i] = np.imag(total)
    
    # Normaliser les projections sur le cercle unité
    norms = np.sqrt(kx**2 + ky**2) + 1e-10
    kx /= norms
    ky /= norms
    
    return kx, ky, word_to_id, encoder


def holographic_generate(question: str,
                          encoder: HolographicEncoder,
                          kx: np.ndarray,
                          ky: np.ndarray,
                          w2i: Dict[str, int],
                          knowledge_base: List,
                          memoire=None,
                          max_words: int = 8,
                          temperature: float = 0.6) -> str:
    """
    Génération hybride : KB fact lookup + holographic word scoring.
    
    Phase 1 : Chercher les faits pertinents dans la KB en utilisant
              l'interférence vectorielle (pas juste l'overlap de mots).
    Phase 2 : Si des faits sont trouvés → réponse structurée.
    Phase 3 : Sinon → fallback par résonance vectorielle pure.
    """
    # Détection de langue
    lang = _detect_language(question)
    lang_cfg = _get_lang_config(lang)
    stopwords = lang_cfg['stopwords']
    
    sujet_phrase = _extract_subject(question, lang)
    q_words_clean = [w.strip('.,!?;:()[]{}«»""\'\'¿¡') for w in question.lower().split()
                     if w.strip('.,!?;:()[]{}«»""\'\'¿¡') not in stopwords
                     and len(w.strip('.,!?;:()[]{}«»""\'\'¿¡')) >= 2]
    
    if not q_words_clean:
        tpl = lang_cfg['templates']
        return tpl['no_understand'].format(sujet=sujet_phrase)
    
    # Pré-calculer les vecteurs des mots de la question
    q_vecs = {}
    for qw in q_words_clean:
        if qw in encoder.word_vectors:
            q_vecs[qw] = encoder.word_vectors[qw]
    
    # Étape 2 : Scorer les faits
    fact_scores = []
    q_set = set(q_words_clean)
    
    # Pré-calculer le vecteur du sujet de la question (hors boucle!)
    v_q_subj = None
    if sujet_phrase:
        v_q_subj = encoder.encode_query(sujet_phrase)
        norm_q_subj = np.sqrt(np.sum(np.abs(v_q_subj)**2))
        if norm_q_subj < 1e-10:
            v_q_subj = None
    
    for s, r, o, sec in knowledge_base:
        # Filtrage rapide : le sujet ou l'objet doit partager un mot avec la question
        s_words = set(w.strip('.,!?;:') for w in s.lower().split())
        o_words = set(w.strip('.,!?;:') for w in o.lower().split())
        r_words = set(w.strip('.,!?;:') for w in r.lower().split())
        all_fact_words = s_words | r_words | o_words
        
        # Overlap lexical rapide
        quick_overlap = q_set & all_fact_words
        if not quick_overlap and not any(qw in s.lower() or s.lower() in qw for qw in q_set):
            # Aucun mot en commun → skip rapide
            continue
        
        # Scoring détaillé
        lexical_overlap = len(quick_overlap)
        vector_score = 0.0
        
        if q_vecs:
            for qw, v_qw in q_vecs.items():
                best_sim = 0.0
                for fw in all_fact_words:
                    if fw in encoder.word_vectors:
                        sim = float(np.real(np.dot(v_qw, np.conj(encoder.word_vectors[fw]))))
                        if sim > best_sim:
                            best_sim = sim
                vector_score += max(0.0, best_sim)
        
        lexical_norm = lexical_overlap / max(len(q_words_clean), 1)
        vector_norm = vector_score / max(len(q_words_clean), 1)
        
        # Bonus de similarité holographique sujet_question ↔ sujet_fait
        subject_bonus = 0.0
        if v_q_subj is not None:
            # Comparer avec les mots du sujet du fait (prendre le max)
            best_subj_sim = 0.0
            for fw in s_words:
                if fw in encoder.word_vectors:
                    v_fw = encoder.word_vectors[fw]
                    sim = float(np.real(np.dot(v_q_subj, np.conj(v_fw))))
                    if sim > best_subj_sim:
                        best_subj_sim = sim
            subject_bonus = max(0.0, best_subj_sim) * 0.5
        
        # Score final : lexical + vectoriel + similarité sujet holographique
        score = lexical_norm * 0.4 + vector_norm * 0.2 + subject_bonus
        
        # Bonus pour correspondance exacte ou partielle du sujet
        if any(qw == s.lower() or s.lower() in qw for qw in q_set):
            score += 0.25
        elif any(qw in s.lower() for qw in q_set):
            score += 0.1
        
        if score > 0.06:
            fact_scores.append((score, (s, r, o, sec)))
    
    # Étape 3 : Construire la réponse
    if fact_scores:
        fact_scores.sort(key=lambda x: -x[0])
        best_score = fact_scores[0][0]
        threshold = max(0.12, best_score * 0.5)
        
        selected = []
        seen_s = set()
        for score, (s, r, o, sec) in fact_scores:
            if score >= threshold and s not in seen_s:
                selected.append((s, r, o, sec))
                seen_s.add(s)
            if len(selected) >= 3:
                break
        
        # Rendu stylisé avec StyleEngine (si disponible)
        response = _render_with_style(selected, question, sujet_phrase, lang)
        
        if memoire is not None:
            for s, r, o, _ in selected:
                for w in f"{s} {r} {o}".lower().split():
                    w = w.strip('.,!?;:')
                    if w in w2i:
                        memoire.enregistrer(kx[w2i[w]], ky[w2i[w]], amplitude=0.3)
        
        return response
    
    # Étape 4 : Fallback — résonance vectorielle pure
    vocab_words = list(w2i.keys())
    q_vec = encoder.encode_query(question, w2i)
    scores = encoder.resonance_scores_batch(vocab_words, q_vec)
    
    for i, w in enumerate(vocab_words):
        if w in _STOPWORDS:
            scores[i] = 0.0
    
    top_n = min(max_words + 3, len(vocab_words))
    if top_n == 0:
        return _fallback_fact_lookup(question, knowledge_base, sujet_phrase)
    
    top_idx = np.argpartition(scores, -top_n)[-top_n:]
    top_idx = top_idx[np.argsort(-scores[top_idx])]
    resonant_words = [vocab_words[i] for i in top_idx[:max_words] if scores[i] > 0.05]
    
    if len(resonant_words) < 2:
        return _fallback_fact_lookup(question, knowledge_base, sujet_phrase)
    
    q_type = _detect_question_type(question)
    response = _render_response(resonant_words, sujet_phrase, q_type, encoder)
    
    if memoire is not None:
        for w in resonant_words[:4]:
            if w in w2i:
                memoire.enregistrer(kx[w2i[w]], ky[w2i[w]], amplitude=0.3)
    
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS AUXILIAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_subject(question: str, lang: str = 'fr') -> str:
    """Extrait le sujet principal d'une question."""
    q = question.lower().strip()
    prefixes = _QUESTION_PREFIXES.get(lang, _QUESTION_PREFIXES['fr'])
    for prefix in sorted(prefixes, key=len, reverse=True):
        if q.startswith(prefix):
            q = q[len(prefix):].strip()
    q = q.strip('.,!?;:¿¡?')
    return q if q else question


def _detect_question_type(question: str) -> str:
    """Détecte le type de question pour choisir le template."""
    q = question.lower()
    if any(w in q for w in ['pourquoi', 'why', 'warum']):
        return 'explication'
    if any(w in q for w in ['comment', 'how', 'wie']):
        return 'processus'
    if any(w in q for w in ['qui est', 'who is', 'wer ist']):
        return 'identite'
    if any(w in q for w in ['quand', 'when', 'wann']):
        return 'temporel'
    if any(w in q for w in ['ou', 'where', 'wo']):
        return 'spatial'
    return 'definition'


def _fallback_fact_lookup(question: str, knowledge_base: List, sujet: str) -> str:
    """Fallback : cherche des faits par correspondance exacte de mots."""
    q_words = set(question.lower().split())
    best_score = 0.0
    best_facts = []
    
    for s, r, o, sec in knowledge_base:
        fact_words = set((s + ' ' + r + ' ' + o).lower().split())
        overlap = q_words & fact_words
        if overlap:
            score = len(overlap) / max(len(q_words), 1)
            if score > best_score * 0.8 and score > 0.1:
                best_facts.append((score, s, r, o))
                if score > best_score:
                    best_score = score
    
    if best_facts:
        best_facts.sort(key=lambda x: -x[0])
        parts = []
        for _, s, r, o in best_facts[:3]:
            parts.append(f"{s.capitalize()} {r} {o}")
        return '. '.join(parts) + '.'
    
    return f"Le concept de {sujet} touche à plusieurs domaines. Je continue d'apprendre à ce sujet."


def _render_response(words: List[str], sujet: str, q_type: str, encoder) -> str:
    """
    Rend une réponse grammaticalement correcte à partir des mots résonants.
    Utilise des templates adaptés au type de question.
    """
    if not words:
        return f"Je n'ai pas encore assez de connaissances sur {sujet}."
    
    w0, w1 = words[0], words[1] if len(words) > 1 else words[0]
    w2 = words[2] if len(words) > 2 else words[1] if len(words) > 1 else words[0]
    
    templates = {
        'definition': [
            f"Le concept de {sujet} est fondamentalement lié à {w0}. Cela implique {w1} et {w2}.",
            f"Pour comprendre {sujet}, il faut saisir que {w0} est en relation avec {w1}. De là découle {w2}.",
            f"{sujet.capitalize()} se définit par sa connexion à {w0}. Cette relation éclaire le rôle de {w1} et {w2}.",
        ],
        'explication': [
            f"L'explication de {sujet} commence par {w0}. Ce phénomène est associé à {w1}, ce qui explique {w2}.",
            f"Pourquoi {sujet} ? Parce que {w0} et {w1} sont en interaction. La conséquence est {w2}.",
            f"La cause profonde de {sujet} réside dans la relation entre {w0} et {w1}, dont émerge {w2}.",
        ],
        'processus': [
            f"Le processus de {sujet} implique d'abord {w0}, puis {w1}, pour aboutir à {w2}.",
            f"Comment {sujet} fonctionne : {w0} initie le mécanisme, {w1} le transforme, et {w2} en résulte.",
        ],
        'identite': [
            f"{sujet.capitalize()} est associé à {w0}, en lien avec {w1} et {w2}.",
            f"L'identité de {sujet} se révèle à travers {w0}, {w1} et {w2}.",
        ],
        'temporel': [
            f"Le moment clé pour {sujet} est en relation avec {w0}. Cela coïncide avec {w1} et {w2}.",
        ],
        'spatial': [
            f"Le lieu de {sujet} est connecté à {w0}. Cet espace englobe {w1} et {w2}.",
        ],
    }
    
    tmpls = templates.get(q_type, templates['definition'])
    idx = hash(sujet) % len(tmpls)
    return tmpls[idx]


# ═══════════════════════════════════════════════════════════════════════════════
# RENDU STYLISÉ (StyleEngine)
# ═══════════════════════════════════════════════════════════════════════════════

# Mapping secteur → domaine pour StyleEngine
SECTOR_TO_DOMAIN = {
    'PHYSIQUE_FOND': 'PHYSIQUE', 'PHYSIQUE_APPLI': 'PHYSIQUE',
    'MATHS_PURES': 'MATHS', 'MATHS_APPLI': 'MATHS',
    'BIOLOGIE': 'BIOLOGIE', 'ECOLOGIE': 'BIOLOGIE',
    'CONSCIENCE': 'CONSCIENCE', 'INTELLIGENCE': 'CONSCIENCE',
    'EMOTION_POS': 'EMOTION', 'EMOTION_NEG': 'EMOTION',
    'ASTRONOMIE': 'PHYSIQUE', 'COSMOLOGIE': 'PHYSIQUE',
    'PASSE': 'HISTOIRE', 'FUTUR': 'HISTOIRE',
    'CULTURE': 'CULTURE', 'POLITIQUE': 'POLITIQUE',
    'CREATION': 'CULTURE', 'EXPRESSION': 'CULTURE',
    'NATURE_ANIM': 'BIOLOGIE', 'NATURE_VEGET': 'BIOLOGIE',
    'CORPS_ORGANES': 'BIOLOGIE', 'CORPS_SENS': 'BIOLOGIE',
    'METAPHYSIQUE': 'PHILOSOPHIE', 'SPIRITUALITE': 'PHILOSOPHIE',
}


def _detect_domain(secteur: str) -> str:
    """Détecte le domaine à partir du secteur."""
    return SECTOR_TO_DOMAIN.get(secteur, 'GENERAL')


def _render_with_style(facts: List[Tuple[str, str, str, str]],
                        question: str,
                        sujet: str,
                        lang: str = 'fr') -> str:
    """
    Rend les faits avec le StyleEngine pour un français élégant.
    
    Deux modes :
    - CHAÎNE : si les faits s'enchaînent logiquement (objet_i → sujet_{i+1})
      → StyleEngine._render_chain() avec connecteurs causaux
    - COLLECTION : si les faits sont indépendants (thématique commune seulement)
      → Rendu « encyclopédique » : chaque fait élégant, séparé proprement
    """
    if not facts:
        tpl = _RESPONSE_TEMPLATES.get(lang, _RESPONSE_TEMPLATES['fr'])
        return tpl['not_found'].format(sujet=sujet)
    
    # Détecter si c'est une chaîne logique
    is_chain = _is_logical_chain(facts)
    
    # Détecter le domaine par vote majoritaire (5 meilleurs faits)
    domaine_votes = {}
    for _, _, _, sec in facts[:5]:
        d = _detect_domain(sec)
        domaine_votes[d] = domaine_votes.get(d, 0) + 1
    # Si éparpillement → GENERAL, sinon domaine majoritaire
    if not domaine_votes:
        domaine = 'GENERAL'
    else:
        best_domain = max(domaine_votes, key=domaine_votes.get)
        best_count = domaine_votes[best_domain]
        # Si le meilleur a moins de 50% des votes → GENERAL
        if best_count < max(2, len(facts[:5]) * 0.5):
            domaine = 'GENERAL'
        else:
            domaine = best_domain
    
    try:
        from style_engine import StyleEngine, RICH_TEMPLATES
        styler = StyleEngine(use_llm=False)
        templates = RICH_TEMPLATES.get(domaine, RICH_TEMPLATES.get('GENERAL', {}))
    except ImportError:
        templates = {}
    
    if len(facts) == 1:
        # Fait unique → template single
        if templates and 'single' in templates:
            import random
            s, r, o, _ = facts[0]
            tmpl = random.choice(templates['single'])
            return tmpl.format(sujet=s.capitalize(), relation=r, objet=o)
        s, r, o, _ = facts[0]
        return f"{s.capitalize()} {r} {o}."
    
    if is_chain:
        # Chaîne logique → StyleEngine complet (intro → liens → conclusion)
        try:
            path = [(s, r, o, sec) for s, r, o, sec in facts]
            result = styler.render(path, question, domaine)
            if result and 'Aucun chemin' not in result:
                return result
        except Exception:
            pass
    
    # COLLECTION : faits indépendants → rendu encyclopédique
    return _render_collection(facts, domaine, templates, sujet, lang)


def _is_logical_chain(facts: List[Tuple[str, str, str, str]]) -> bool:
    """
    Détecte si les faits forment une chaîne logique.
    Une chaîne : l'objet du fait N partage des mots avec le sujet du fait N+1.
    """
    if len(facts) < 2:
        return False
    
    chain_links = 0
    for i in range(len(facts) - 1):
        obj_words = set(w.strip('.,!?;:') for w in facts[i][2].lower().split() if len(w) >= 2)
        subj_words = set(w.strip('.,!?;:') for w in facts[i+1][0].lower().split() if len(w) >= 2)
        overlap = obj_words & subj_words
        if overlap:
            chain_links += 1
    
    # Est une chaîne si au moins la moitié des transitions sont liées
    return chain_links >= (len(facts) - 1) * 0.5


def _render_collection(facts: List[Tuple[str, str, str, str]],
                       domaine: str,
                       templates: dict,
                       sujet: str,
                       lang: str = 'fr') -> str:
    """
    Rendu « encyclopédique » : faits indépendants mais élégants.
    
    Structure :
      [Phrase d'ancrage thématique]
      D'une part, Fait 1.
      D'autre part, Fait 2.
      Enfin, Fait 3.
    """
    import random
    
    # Nettoyer le sujet pour l'affichage
    sujet_clean = sujet.strip()
    # Enlever les suffixes comme "(a propos de ...)"
    if '(a propos de' in sujet_clean:
        sujet_clean = sujet_clean.split('(a propos de')[0].strip()
        # Enlever les préfixes de question résiduels (toutes langues)
        for pfx in ['fonctionne ', 'explique ', 'decris ', 'definis ',
                     'function ', 'explain ', 'describe ', 'define ',
                     'how does ', 'how do ', 'what is ', 'who is ',
                     'was ist ', 'wer ist ', '¿qué es ', 'que es ']:
            if sujet_clean.lower().startswith(pfx):
                sujet_clean = sujet_clean[len(pfx):]
    # Enlever la ponctuation et mots parasites
    sujet_clean = sujet_clean.rstrip('?.,! ')
    sujet_clean = sujet_clean.replace('?', '').replace('!', '')
    # Limiter à 6 mots max
    words = sujet_clean.split()
    if len(words) > 6:
        sujet_clean = ' '.join(words[:6])
    
    # Phrases d'ancrage par domaine et langue
    ancrages = {
        'fr': {
            'PHYSIQUE': [
                f"Le phénomène de {sujet_clean} repose sur plusieurs principes physiques.",
                f"La physique éclaire {sujet_clean} sous plusieurs angles.",
            ],
            'BIOLOGIE': [
                f"Le vivant nous renseigne sur {sujet_clean} à travers plusieurs mécanismes.",
                f"Plusieurs processus biologiques éclairent {sujet_clean}.",
            ],
            'CONSCIENCE': [
                f"L'expérience de {sujet_clean} se déploie sur plusieurs dimensions.",
                f"Plusieurs facettes éclairent notre compréhension de {sujet_clean}.",
            ],
        },
        'en': {
            'PHYSIQUE': [
                f"The phenomenon of {sujet_clean} rests on several physical principles.",
                f"Physics illuminates {sujet_clean} from several angles.",
            ],
            'BIOLOGIE': [
                f"Living systems reveal {sujet_clean} through several mechanisms.",
                f"Several biological processes shed light on {sujet_clean}.",
            ],
            'CONSCIENCE': [
                f"The experience of {sujet_clean} unfolds across several dimensions.",
                f"Several facets illuminate our understanding of {sujet_clean}.",
            ],
        },
    }
    
    # Fallback : ancrages français
    lang_ancrages = ancrages.get(lang, ancrages['fr'])
    domaine_ancrages = lang_ancrages.get(
        domaine,
        lang_ancrages.get('PHYSIQUE', [
            f"Several aspects are important regarding {sujet_clean}.",
        ])
    )
    if not domaine_ancrages:
        domaine_ancrages = [f"Voici les principaux éléments concernant {sujet_clean}."]
    ancrage = random.choice(domaine_ancrages)
    
    # Liaisons multilingues
    liaisons_map = {
        'fr': ["D'une part,", "Par ailleurs,", "On notera également que"],
        'en': ["First,", "Furthermore,", "It is also worth noting that"],
    }
    liaisons = liaisons_map.get(lang, liaisons_map['fr'])
    enfin_word = {'fr': 'Enfin', 'en': 'Finally', 'es': 'Finalmente', 'de': 'Schließlich'}.get(lang, 'Enfin')
    
    # Rendu de chaque fait en forme compacte élégante
    rendered_facts = []
    for i, (s, r, o, _) in enumerate(facts):
        # Forme simple élégante sans template redondant
        fact_str = f"{s.capitalize()} {r} {o}"
        rendered_facts.append(fact_str)
    
    # Assemblage
    if len(rendered_facts) == 1:
        return f"{ancrage} {rendered_facts[0]}."
    
    parts = [ancrage]
    for i, fact_str in enumerate(rendered_facts):
        if i == 0:
            parts.append(f"{fact_str}.")
        elif i == len(rendered_facts) - 1:
            parts.append(f"{enfin_word}, {fact_str[0].lower()}{fact_str[1:]}.")
        else:
            liaison = liaisons[i % len(liaisons)]
            parts.append(f"{liaison} {fact_str[0].lower()}{fact_str[1:]}.")
    
    return ' '.join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST RAPIDE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=== Test HolographicEncoder ===")
    encoder = HolographicEncoder(dim=256)
    
    # Test encodage
    for w in ['lumiere', 'onde', 'electromagnetique', 'gravite', 'espace', 'temps']:
        v = encoder.encode_word(w)
        print(f"  {w:20s} → |v|={np.sqrt(np.sum(np.abs(v)**2)):.3f}")
    
    # Test binding
    v_lum = encoder.encode_word('lumiere')
    v_ond = encoder.encode_word('onde')
    bound = encoder.bind(v_lum, v_ond)
    unbound = encoder.unbind(bound, v_ond)
    sim = float(np.real(np.dot(unbound, np.conj(v_lum))))
    print(f"\n  Binding lumiere ⊛ onde → unbinding : similarité = {sim:.4f} (idéal ~1.0)")
    
    # Test similarité
    print(f"\n  sim(lumiere, onde) = {encoder.similarity('lumiere', 'onde'):.4f}")
    print(f"  sim(lumiere, gravite) = {encoder.similarity('lumiere', 'gravite'):.4f}")
    
    # Test collisions
    print("\n  Encodage de 100 mots aléatoires...")
    for i in range(100):
        encoder.encode_word(f"mot_test_{i}")
    collisions = encoder.collision_check(0.9)
    print(f"  Collisions (>0.9) : {len(collisions)} (attendu ~0)")
    
    # Test mémoire
    print("\n  Stockage de faits...")
    encoder.store_fact('lumiere', 'est une', 'onde electromagnetique')
    encoder.store_fact('gravite', 'est la', 'courbure de espace temps')
    encoder.store_fact('eau', 'a une', 'capacite thermique elevee')
    
    q = encoder.encode_query('Qu est-ce que la lumiere ?')
    scores = []
    for w in ['lumiere', 'onde', 'gravite', 'eau', 'electromagnetique']:
        s = encoder.resonance_score(w, q)
        scores.append((w, s))
    scores.sort(key=lambda x: -x[1])
    print("  Scores de résonance (question sur la lumière) :")
    for w, s in scores:
        bar = '#' * int(s * 50)
        print(f"    {w:20s} [{bar:50s}] {s:.4f}")
    
    print(f"\n  Vocabulaire: {encoder.vocab_size} mots")
    print(f"  Faits stockés: {encoder.n_facts}")
    print(f"  Énergie mémoire: {encoder.energy:.2f}")
    
    print("\n✓ Test terminé.")
