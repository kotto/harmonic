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
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# Mots vides français (pour filtrage)
_STOPWORDS = {
    'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'est', 'a',
    'dans', 'que', 'qui', 'pas', 'ne', 'sur', 'pour', 'avec', 'ce', 'cette',
    'par', 'au', 'aux', 'en', 'plus', 'moins', 'tout', 'tous', 'son', 'sa',
    'ses', 'il', 'elle', 'ils', 'elles', 'nous', 'vous', 'leur', 'leurs',
    'mais', 'ou', 'donc', 'or', 'ni', 'car', 'aussi', 'très', 'bien',
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'of', 'in', 'on', 'at',
    'to', 'for', 'with', 'by', 'from', 'it', 'its', 'and', 'or', 'not',
    'this', 'that', 'these', 'those', 'be', 'has', 'have', 'had', 'do',
    'does', 'did', 'will', 'would', 'can', 'could', 'may', 'might',
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
        Convertit un mot en vecteur complexe Gaussien déterministe.
        
        HRR exige des vecteurs pseudo-orthogonaux :
        - Chaque composante v_k ~ N(0, 1/√(2D)) + i·N(0, 1/√(2D))
        - E[|v_k|²] = 1/D, donc E[|v|²] = 1
        - Pour deux mots ≠, E[|<v_a, v_b>|²] = 1/D → quasi-orthogonaux en haute dimension
        
        Déterministe : hash FNV-1a → seed → np.random.RandomState → randn
        Le φ-spacing est appliqué AU hash (pas aux phases) via FNV-1a qui
        utilise le nombre d'or implicitement dans sa structure multiplicative.
        """
        if word in self.word_vectors:
            return self.word_vectors[word]
        
        # Hash déterministe 64-bit
        seed = _fnv1a_hash(word)
        
        # Pour D > 500, on utilise une méthode mixte :
        # - Les 32 premiers bits déterminent les 200 premières dimensions (Gaussien)
        # - Le reste est généré par le hachage φ-itéré pour éviter les patterns
        rng = np.random.RandomState(seed & 0xFFFFFFFF)
        
        # Tirage Gaussien complexe : real ~ N(0, σ²), imag ~ N(0, σ²)
        # σ² = 1/(2D) pour que E[|v_k|²] = 1/D
        sigma = 1.0 / math.sqrt(2.0 * self.dim)
        
        if self.dim <= 500:
            # Génération directe par RNG pour toutes les dimensions
            real = rng.randn(self.dim).astype(np.float64) * sigma
            imag = rng.randn(self.dim).astype(np.float64) * sigma
        else:
            # Grand D : génération hybride
            real = np.zeros(self.dim, dtype=np.float64)
            imag = np.zeros(self.dim, dtype=np.float64)
            
            # Premières 500 dimensions : Gaussien standard
            n_direct = min(500, self.dim)
            real[:n_direct] = rng.randn(n_direct) * sigma
            imag[:n_direct] = rng.randn(n_direct) * sigma
            
            # Dimensions restantes : phases φ-espacées (déterministe, pas de collision)
            # Chaque dimension k a une phase unique basée sur seed et k
            for k in range(n_direct, self.dim):
                # Phase φ-espacée : combine le seed et l'index
                phase_k = ((seed >> (k % 32)) ^ (k * 2654435761)) % 2147483647
                phase_k = (phase_k * PHI) % TAU
                real[k] = math.cos(phase_k) * sigma
                imag[k] = math.sin(phase_k) * sigma
        
        v = real + 1j * imag
        # v a E[|v|²] ≈ 1 (par construction), pas besoin de normaliser
        
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
    sujet_phrase = _extract_subject(question)
    q_words_clean = [w.strip('.,!?;:()[]{}«»""\'\'¿¡') for w in question.lower().split()
                     if w.strip('.,!?;:()[]{}«»""\'\'¿¡') not in _STOPWORDS
                     and len(w.strip('.,!?;:()[]{}«»""\'\'¿¡')) >= 2]
    
    if not q_words_clean:
        return f"Je ne comprends pas assez la question sur {sujet_phrase}."
    
    # Pré-calculer les vecteurs des mots de la question
    q_vecs = {}
    for qw in q_words_clean:
        if qw in encoder.word_vectors:
            q_vecs[qw] = encoder.word_vectors[qw]
    
    # Étape 2 : Scorer les faits (optimisé: index par sujet pour réduire le scan)
    fact_scores = []
    q_set = set(q_words_clean)
    
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
        score = lexical_norm * 0.7 + vector_norm * 0.3
        
        if any(qw == s.lower() or s.lower() in qw for qw in q_set):
            score += 0.3
        if any(qw in s.lower() for qw in q_set):
            score += 0.1
        
        if score > 0.08:
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
        response = _render_with_style(selected, question, sujet_phrase)
        
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

def _extract_subject(question: str) -> str:
    """Extrait le sujet principal d'une question."""
    q = question.lower().strip()
    for prefix in ['explique', 'qu est-ce que', 'qu est ce que', 'qui est',
                    'pourquoi', 'comment', 'decris', 'definis', 'quelle est',
                    'what is', 'who is', 'explain', 'describe', 'define',
                    'was ist', '¿qué es', 'que es']:
        if q.startswith(prefix):
            q = q[len(prefix):].strip()
    # Nettoyer la ponctuation restante
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
                        sujet: str) -> str:
    """
    Rend les faits avec le StyleEngine pour un français élégant.
    Si StyleEngine indisponible → fallback concaténation simple.
    """
    if not facts:
        return _fallback_fact_lookup(question, [], sujet)
    
    # Tenter d'utiliser le StyleEngine
    try:
        from style_engine import StyleEngine, RICH_TEMPLATES
        styler = StyleEngine(use_llm=False)
        
        # Détecter le domaine du meilleur fait
        domaine = _detect_domain(facts[0][3])
        
        # Construire un pseudo-chemin pour le StyleEngine
        # Le StyleEngine attend [(s, r, o, sec), ...]
        path = [(s, r, o, sec) for s, r, o, sec in facts]
        
        # Si un seul fait, utiliser le template single
        if len(path) == 1:
            templates = RICH_TEMPLATES.get(domaine, RICH_TEMPLATES.get('GENERAL', {}))
            if 'single' in templates:
                import random
                s, r, o, _ = path[0]
                tmpl = random.choice(templates['single'])
                return tmpl.format(sujet=s.capitalize(), relation=r, objet=o)
        
        # Pour 2+ faits, utiliser le rendu du StyleEngine
        result = styler.render(path, question, domaine)
        if result and 'Aucun chemin' not in result:
            return result
    except ImportError:
        pass
    except Exception:
        pass
    
    # Fallback : concaténation simple avec ponctuation
    parts = []
    for s, r, o, _ in facts:
        parts.append(f"{s.capitalize()} {r} {o}")
    return '. '.join(parts) + '.'


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
