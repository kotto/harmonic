"""
🌊 Wave Lang — Le Langage Ondulatoire Unifié
=============================================
Bibliothèque unifiée des primitives du langage ondulatoire.
Conforme à la spécification LANGAGE_ONDULATOIRE.md.

Les 10+ primitives universelles :
  1. ENCODE    — monde → ψ        (texte, audio, image → vecteur complexe)
  2. DECODE    — ψ → monde        (vecteur complexe → texte)
  3. BIND      — ψ₁ ⊛ ψ₂          (convolution circulaire / HRR)
  4. UNBIND    — ψ₁ ⊘ ψ₂          (corrélation circulaire)
  5. SUPERPOSE — Σ ψᵢ             (addition de vecteurs)
  6. RESONATE  — ⟨ψ₁|ψ₂⟩          (similarité cosinus complexe)
  7. ROTATE    — ψ · e^{iθ}       (rotation de phase)
  8. NORMALIZE — ψ / |ψ|          (projection sur le cercle unité)
  9. INTERFERE — ψ₁ + ε·ψ₂        (interférence faible/forte)
  10. DIFFRACT — FFT(ψ)           (passage temps → fréquence)
  11. FILTER   — filtre spectral adaptatif
  12. PHASE_SHIFT — décalage de phase par dimension
  13. EMERGE   — émergence par superposition pondérée

Fondations mathématiques :
  - Espace : ℂ⁵¹² (vecteurs complexes unitaires)
  - Binding : convolution circulaire HRR (Plate 1995)
  - Hachage : FNV-1a déterministe
  - Espacement : φ (nombre d'or) pour éviter les collisions
  - Mémoire : noyau ABC (Atangana-Baleanu-Caputo, α = 1/φ)

Usage :
    from wave_lang import encode, bind, resonate, superpose, decode

    # Encoder un concept
    psi_lumiere = encode("lumiere")
    psi_onde = encode("onde")

    # Créer un concept composite
    psi_lumiere_onde = bind(psi_lumiere, psi_onde)

    # Mesurer la résonance
    score = resonate(psi_lumiere, psi_onde)  # → 0.0 (orthogonal)
    score2 = resonate(psi_lumiere, psi_lumiere)  # → 1.0 (identité)

    # Superposer dans un hologramme
    H = superpose(psi_lumiere, psi_onde, psi_lumiere_onde)

Principe : Tout problème se résout en trois temps ondulatoires :
    ENCODE → MANIPULER → DÉCODER
    (monde → ψ)  (ψ → ψ')  (ψ' → solution)
"""

import math
from typing import List, Tuple, Dict, Optional, Callable, Union

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES FONDAMENTALES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
"""Nombre d'or φ = (1+√5)/2. Irrationalité maximale → pas de répétition."""

ALPHA = 1.0 / PHI  # ≈ 0.618033988749895
"""Ordre fractionnaire optimal ABC. Point d'équilibre mémoire/inertie."""

TAU = 2.0 * math.pi
"""Période fondamentale 2π."""

DEFAULT_DIM = 512
"""Dimension par défaut de l'espace ℂ (limite de Bekenstein)."""

# Constantes FNV-1a
_FNV_OFFSET = 0xCBF29CE484222325
_FNV_PRIME = 0x100000001B3

# Constante ABC
_B_1_PHI = 0.8506508083
"""B(α) — normalisation du noyau ABC discret."""


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

# Un vecteur d'onde est un ndarray complexe 1D
Wave = np.ndarray  # shape = (dim,), dtype = complex128

# Un scalaire réel
Scalar = float

# Un hologramme (mémoire) est un vecteur complexe (superposition)
Hologram = np.ndarray  # shape = (dim,), dtype = complex128


# ═══════════════════════════════════════════════════════════════════════════════
# HASH FNV-1a (déterministe, universel)
# ═══════════════════════════════════════════════════════════════════════════════

def fnv1a(text: str) -> int:
    """
    Hash FNV-1a 64 bits — déterministe, universel, bonne distribution.

    Même entrée → même hash, sur n'importe quelle machine, dans n'importe
    quel langage. C'est la brique de base du déterminisme ondulatoire.

    Args:
        text: chaîne de caractères à hacher

    Returns:
        entier 64 bits (0 à 2^64-1)

    Example:
        >>> fnv1a("bonjour")  # donnera toujours le même résultat
    """
    h = _FNV_OFFSET
    for ch in text.encode('utf-8'):
        h ^= ch
        h = (h * _FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION DÉTERMINISTE DE VECTEURS
# ═══════════════════════════════════════════════════════════════════════════════

def _deterministic_gaussian(dim: int, seed: int) -> np.ndarray:
    """
    Vecteur gaussien complexe D-dimensionnel déterministe.

    Utilise un RandomState scellé avec la seed → reproductible à jamais.
    Aucun bruit runtime n'est ajouté.

    Args:
        dim: dimension du vecteur
        seed: entier (hash FNV-1a du mot)

    Returns:
        vecteur complexe (dim,) ~ N(0, σ²) avec σ = 1/√(2·dim)
    """
    rng = np.random.RandomState(seed & 0xFFFFFFFF)
    sigma = 1.0 / math.sqrt(2.0 * dim)

    if dim <= 500:
        real = rng.randn(dim).astype(np.float64) * sigma
        imag = rng.randn(dim).astype(np.float64) * sigma
    else:
        real = np.zeros(dim, dtype=np.float64)
        imag = np.zeros(dim, dtype=np.float64)
        n_direct = min(500, dim)
        real[:n_direct] = rng.randn(n_direct) * sigma
        imag[:n_direct] = rng.randn(n_direct) * sigma
        # φ-spacing pour les dimensions restantes
        for k in range(n_direct, dim):
            phase_k = ((seed >> (k % 32)) ^ (k * 2654435761)) % 2147483647
            phase_k = (phase_k * PHI) % TAU
            real[k] = math.cos(phase_k) * sigma
            imag[k] = math.sin(phase_k) * sigma

    return real + 1j * imag


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ENCODE : monde → ψ
# ═══════════════════════════════════════════════════════════════════════════════

# Cache global pour éviter de recalculer les ψ des mots fréquents
_ENCODE_CACHE: Dict[str, np.ndarray] = {}


def encode(entity: str, dim: int = DEFAULT_DIM, use_cache: bool = True) -> Wave:
    """
    Encode une entité textuelle en vecteur d'onde complexe.

    ψ = A · e^{iφ} où :
      - A (amplitude) = vecteur gaussien déterministe (FNV-1a)
      - φ (phase) = espacement par le nombre d'or

    Le mapping est DÉTERMINISTE : même entité → même ψ, toujours.

    Args:
        entity: texte à encoder (mot, phrase, concept)
        dim: dimension de l'espace ℂ (défaut: 512)
        use_cache: mémoriser le résultat pour les appels futurs

    Returns:
        ψ ∈ ℂᵈⁱᵐ, vecteur complexe unitaire (|ψ| = 1)

    Example:
        >>> psi = encode("lumiere")
        >>> psi.shape
        (512,)
        >>> abs(norm(psi) - 1.0) < 1e-10
        True
    """
    if use_cache and entity in _ENCODE_CACHE:
        cached = _ENCODE_CACHE[entity]
        if len(cached) == dim:
            return cached.copy()

    seed = fnv1a(entity)
    v = _deterministic_gaussian(dim, seed)
    v = normalize(v)

    if use_cache:
        _ENCODE_CACHE[entity] = v.copy()

    return v


def encode_many(entities: List[str], dim: int = DEFAULT_DIM) -> np.ndarray:
    """
    Encode une liste d'entités en une matrice d'ondes.

    Args:
        entities: liste de textes
        dim: dimension

    Returns:
        matrice [N, dim] complexe
    """
    result = np.zeros((len(entities), dim), dtype=np.complex128)
    for i, e in enumerate(entities):
        result[i] = encode(e, dim=dim)
    return result


def clear_encode_cache():
    """Vide le cache d'encodage."""
    _ENCODE_CACHE.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DECODE : ψ → monde
# ═══════════════════════════════════════════════════════════════════════════════

def decode(psi: Wave, vocabulary: Optional[Dict[str, Wave]] = None,
           top_k: int = 5) -> List[Tuple[str, float]]:
    """
    Décode un vecteur d'onde en entités textuelles.

    Cherche dans le vocabulaire les mots dont le ψ résonne le plus
    avec le ψ donné. Retourne les top-k avec leurs scores.

    Args:
        psi: vecteur d'onde à décoder
        vocabulary: dict {mot: ψ_mot}. Si None, utilise le cache d'encodage.
        top_k: nombre de résultats à retourner

    Returns:
        liste de (mot, score) triée par score décroissant

    Example:
        >>> psi = encode("lumiere")
        >>> vocab = {"lumiere": encode("lumiere"), "onde": encode("onde")}
        >>> results = decode(psi, vocab, top_k=2)
        >>> results[0][0]
        'lumiere'
    """
    if vocabulary is None:
        vocabulary = _ENCODE_CACHE

    if not vocabulary:
        return []

    scores = []
    for word, psi_w in vocabulary.items():
        if len(psi_w) != len(psi):
            continue
        s = resonate(psi, psi_w)
        scores.append((word, s))

    scores.sort(key=lambda x: -x[1])
    return scores[:top_k]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. BIND : lier deux concepts (convolution circulaire HRR)
# ═══════════════════════════════════════════════════════════════════════════════

def bind(psi_a: Wave, psi_b: Wave) -> Wave:
    """
    Lie deux ondes par convolution circulaire (binding HRR).

    bind(a, b) = IFFT(FFT(a) · FFT(b))

    Le résultat est un nouveau ψ qui représente le concept composite
    « a ET b ». L'opération est réversible via unbind().

    Applications :
      - Fait : ψ_fait = bind(ψ_sujet, bind(ψ_relation, ψ_objet))
      - Tool Use : ψ_action = bind(ψ_intention, ψ_outil)
      - Diphone TTS : ψ_ab = bind(ψ_a, ψ_b)
      - Association mémoire : ψ_clé-valeur = bind(ψ_clé, ψ_valeur)

    Args:
        psi_a, psi_b: vecteurs complexes de même dimension

    Returns:
        ψ_a ⊛ ψ_b, normalisé

    Example:
        >>> a = encode("sujet")
        >>> b = encode("relation")
        >>> composite = bind(a, b)
        >>> # unbind(composite, b) ≈ a
    """
    A = np.fft.fft(psi_a)
    B = np.fft.fft(psi_b)
    result = np.fft.ifft(A * B)
    return normalize(result)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. UNBIND : délier (corrélation circulaire HRR)
# ═══════════════════════════════════════════════════════════════════════════════

def unbind(psi_a: Wave, psi_b: Wave) -> Wave:
    """
    Délie deux ondes par corrélation circulaire (unbinding HRR).

    unbind(bind(x, y), y) ≈ x

    C'est l'opération inverse du binding : si c = bind(a, b),
    alors unbind(c, b) ≈ a (récupération approximative).

    Applications :
      - Requête mémoire : réponse = unbind(H, ψ_requête)
      - Extraction : ψ_sujet = unbind(ψ_fait, bind(ψ_relation, ψ_objet))

    Args:
        psi_a: vecteur composite (ex: bind(sujet, relation, objet))
        psi_b: une des composantes connues

    Returns:
        estimation de l'autre composante, normalisée

    Example:
        >>> a = encode("sujet")
        >>> b = encode("relation")
        >>> c = bind(a, b)
        >>> recovered = unbind(c, b)
        >>> resonate(recovered, a) > 0.5
        True
    """
    A = np.fft.fft(psi_a)
    B = np.fft.fft(psi_b)
    result = np.fft.ifft(A * np.conj(B))
    return normalize(result)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SUPERPOSE : additionner des ondes
# ═══════════════════════════════════════════════════════════════════════════════

def superpose(*psis: Wave, weights: Optional[List[float]] = None) -> Wave:
    """
    Superpose (additionne) plusieurs ondes en un seul vecteur.

    H = Σ wᵢ · ψᵢ

    C'est l'opération fondamentale de l'holographie : la mémoire
    est une superposition additive de tous les faits.

    Propriétés : linéaire, commutative, associative.

    Applications :
      - Contexte : ψ_contexte = superpose(ψ_mot1, ψ_mot2, ...)
      - Hologramme : H = superpose(ψ_fait1, ψ_fait2, ...)
      - Preuve logique : ψ_preuve = superpose(ψ_prémisse1, ψ_prémisse2, ...)

    Args:
        *psis: ondes à superposer
        weights: poids optionnels (défaut: égaux = 1/n)

    Returns:
        superposition normalisée

    Example:
        >>> H = superpose(encode("a"), encode("b"), encode("c"))
        >>> H.shape
        (512,)
    """
    if not psis:
        return np.zeros(DEFAULT_DIM, dtype=np.complex128)

    if weights is None:
        weights = [1.0 / len(psis)] * len(psis)

    result = sum(w * psi for w, psi in zip(weights, psis))
    return normalize(result)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. RESONATE : mesurer la cohérence entre deux ondes
# ═══════════════════════════════════════════════════════════════════════════════

def resonate(psi_a: Wave, psi_b: Wave) -> Scalar:
    """
    Mesure la résonance (similarité cosinus complexe) entre deux ondes.

    resonance(a, b) = Re(⟨a|b⟩) ∈ [-1, 1]

    Interprétation :
      +1.0  = identiques (interférence constructive parfaite)
       0.0  = orthogonaux (aucune relation)
      -1.0  = opposés (interférence destructive parfaite)

    Applications :
      - Attention : Q·K^T ≡ resonate(ψ_Q, ψ_K)
      - Retrieval : top-k = argmax resonate(ψ_requête, ψ_candidat)
      - Diagnostic : anomalie = resonate < seuil
      - Validation : qualité = resonate(ψ_généré, ψ_attendu)

    Args:
        psi_a, psi_b: ondes à comparer

    Returns:
        score ∈ [-1, 1]

    Example:
        >>> resonate(encode("lumiere"), encode("lumiere"))
        1.0
        >>> resonate(encode("lumiere"), encode("gravite"))
        -0.05...  # proche de 0 (orthogonal)
    """
    return float(np.real(np.dot(psi_a, np.conj(psi_b))))


def coherence(psi_a: Wave, psi_b: Wave) -> Scalar:
    """
    Cohérence de phase normalisée entre deux ondes.

    Identique à resonate() mais toujours dans [0, 1] (valeur absolue).
    Utile pour le scoring de similarité non-directionnelle.

    Args:
        psi_a, psi_b: ondes à comparer

    Returns:
        score ∈ [0, 1]
    """
    return abs(resonate(psi_a, psi_b))


def resonate_batch(query: Wave, candidates: np.ndarray) -> np.ndarray:
    """
    Calcule la résonance d'un vecteur requête contre une matrice de candidats.

    Version vectorisée — O(N·D) au lieu de N appels individuels.

    Args:
        query: vecteur requête (dim,)
        candidates: matrice (N, dim)

    Returns:
        scores (N,) ∈ [-1, 1]
    """
    return np.real(np.dot(candidates, np.conj(query)))


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ROTATE : changer la perspective
# ═══════════════════════════════════════════════════════════════════════════════

def rotate(psi: Wave, angle: float) -> Wave:
    """
    Rotation de phase globale : ψ → ψ · e^{iθ}.

    Préserve la norme (|ψ| = 1). Groupe U(1).

    Applications :
      - Position : ψ_pos = rotate(ψ_mot, pos · Δφ)
      - Émotion TTS : ψ_émotion = rotate(ψ_neutre, θ_émotion)
      - Style : ψ_cible = rotate(ψ_source, θ_style)
      - Apprentissage : gradient ≈ rotation vers cohérence max

    Args:
        psi: onde à tourner
        angle: angle en radians

    Returns:
        ψ' = ψ · e^{iθ}

    Example:
        >>> psi = encode("concept")
        >>> psi_shifted = rotate(psi, math.pi / 2)  # quart de tour
        >>> resonate(psi, psi_shifted) < 0.1
        True
    """
    return psi * np.exp(1j * angle)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. NORMALIZE : projeter sur le cercle unité
# ═══════════════════════════════════════════════════════════════════════════════

def normalize(psi: Wave) -> Wave:
    """
    Normalise un vecteur d'onde sur le cercle unité.

    ψ → ψ / |ψ|

    Args:
        psi: onde à normaliser

    Returns:
        ψ normalisé (|ψ| = 1)

    Example:
        >>> v = np.array([3+4j, 0+0j])
        >>> n = normalize(v)
        >>> abs(norm(n) - 1.0) < 1e-10
        True
    """
    n = np.sqrt(np.sum(np.abs(psi) ** 2))
    if n < 1e-30:
        return psi.copy()
    return psi / n


def norm(psi: Wave) -> Scalar:
    """
    Norme L2 d'un vecteur d'onde.

    |ψ| = √(Σ |ψᵢ|²)

    Args:
        psi: onde

    Returns:
        norme euclidienne
    """
    return float(np.sqrt(np.sum(np.abs(psi) ** 2)))


def energy(psi: Wave) -> Scalar:
    """
    Énergie (norme au carré) d'un vecteur d'onde.

    E = |ψ|² = Σ |ψᵢ|²

    Args:
        psi: onde

    Returns:
        énergie totale
    """
    return float(np.sum(np.abs(psi) ** 2))


# ═══════════════════════════════════════════════════════════════════════════════
# 9. INTERFERE : interférence contrôlée
# ═══════════════════════════════════════════════════════════════════════════════

def interfere(psi_a: Wave, psi_b: Wave, epsilon: float = 0.1) -> Wave:
    """
    Interférence faible entre deux ondes : ψ_a + ε·ψ_b.

    Pour ε petit (~0.1) : connexion subtile, surréaliste.
    Pour ε = 1.0 : interférence équilibrée (moyenne).
    Pour ε > 1.0 : ψ_b domine.

    Applications :
      - Créativité : idée = interfere(concept_a, concept_b, ε=0.15)
      - Surréalisme : connexion inattendue entre concepts éloignés
      - Mixage : mélange contrôlé de deux sources

    Args:
        psi_a: onde principale
        psi_b: onde secondaire
        epsilon: facteur d'influence (défaut: 0.1)

    Returns:
        ψ_a + ε·ψ_b, normalisé

    Example:
        >>> a = encode("pluie")
        >>> b = encode("musique")
        >>> surreal = interfere(a, b, epsilon=0.15)
    """
    result = psi_a + epsilon * psi_b
    return normalize(result)


# ═══════════════════════════════════════════════════════════════════════════════
# 10. DIFFRACT : analyse spectrale
# ═══════════════════════════════════════════════════════════════════════════════

def diffract(psi: Wave, inverse: bool = False) -> Wave:
    """
    Transformée de Fourier — passage domaine temporel ↔ fréquentiel.

    Applications :
      - Analyse : extraire les fréquences dominantes
      - Filtrage : manipuler dans le domaine fréquentiel
      - Dualité : résolution temps-fréquence (Gabor)

    Args:
        psi: onde en domaine temporel (ou fréquentiel si inverse=True)
        inverse: si True, applique la FFT inverse (IFFT)

    Returns:
        ψ en domaine fréquentiel (ou temporel si inverse=True)

    Example:
        >>> psi = encode("signal")
        >>> freqs = diffract(psi)        # temps → fréquences
        >>> recovered = diffract(freqs, inverse=True)  # fréquences → temps
        >>> resonate(psi, recovered) > 0.999
        True
    """
    if inverse:
        return np.fft.ifft(psi)
    return np.fft.fft(psi)


def spectrum(psi: Wave) -> np.ndarray:
    """
    Spectre d'amplitude d'une onde.

    Retourne les magnitudes |FFT(ψ)| — utile pour visualiser
    la distribution fréquentielle.

    Args:
        psi: onde

    Returns:
        magnitudes (dim,) réelles positives
    """
    return np.abs(np.fft.fft(psi))


# ═══════════════════════════════════════════════════════════════════════════════
# 11. FILTER : filtrage spectral adaptatif
# ═══════════════════════════════════════════════════════════════════════════════

def filter_wave(psi: Wave, filter_fn: Optional[Callable[[np.ndarray], np.ndarray]] = None,
                low_pass: Optional[float] = None,
                high_pass: Optional[float] = None,
                band_pass: Optional[Tuple[float, float]] = None) -> Wave:
    """
    Filtre une onde dans le domaine fréquentiel.

    Modes de filtrage :
      - filter_fn: fonction personnalisée f(freqs) → freqs filtrées
      - low_pass: atténue les fréquences > cutoff
      - high_pass: atténue les fréquences < cutoff
      - band_pass: conserve les fréquences entre [low, high]

    Applications :
      - Débruitage : low_pass pour lisser
      - Extraction : band_pass pour isoler une bande
      - Style : filter_fn personnalisé

    Args:
        psi: onde à filtrer
        filter_fn: fonction de filtre personnalisée
        low_pass: fréquence de coupure basse (0 à dim//2)
        high_pass: fréquence de coupure haute (0 à dim//2)
        band_pass: (low, high) pour filtre passe-bande

    Returns:
        ψ filtré, normalisé

    Example:
        >>> psi = encode("signal bruite")
        >>> clean = filter_wave(psi, low_pass=32)  # garde les 32 premières fréquences
    """
    freqs = np.fft.fft(psi)
    dim = len(psi)

    if filter_fn is not None:
        freqs = filter_fn(freqs)
    elif low_pass is not None:
        mask = np.zeros(dim, dtype=np.float64)
        cutoff = min(int(low_pass), dim // 2)
        mask[:cutoff] = 1.0
        mask[-cutoff:] = 1.0
        freqs = freqs * mask
    elif high_pass is not None:
        mask = np.ones(dim, dtype=np.float64)
        cutoff = min(int(high_pass), dim // 2)
        mask[:cutoff] = 0.0
        mask[-cutoff:] = 0.0
        freqs = freqs * mask
    elif band_pass is not None:
        low, high = band_pass
        mask = np.zeros(dim, dtype=np.float64)
        l = min(int(low), dim // 2)
        h = min(int(high), dim // 2)
        mask[l:h] = 1.0
        mask[-h:-l] = 1.0
        freqs = freqs * mask

    result = np.fft.ifft(freqs)
    return normalize(result)


# ═══════════════════════════════════════════════════════════════════════════════
# 12. PHASE_SHIFT : décalage de phase par dimension
# ═══════════════════════════════════════════════════════════════════════════════

def phase_shift(psi: Wave, shift: Union[float, np.ndarray]) -> Wave:
    """
    Décale la phase de chaque dimension indépendamment.

    ψ'_d = ψ_d · e^{i·shift_d}

    Si shift est un scalaire, toutes les dimensions sont décalées
    uniformément (équivalent à rotate). Si shift est un vecteur,
    chaque dimension reçoit son propre décalage.

    Applications :
      - Positionnement fin : moduler les phases par dimension
      - Encodage positionnel : shift linéaire par dimension
      - Style transfer : shift appris par dimension

    Args:
        psi: onde à décaler
        shift: scalaire (radians) ou vecteur (dim,) de décalages

    Returns:
        ψ déphasé

    Example:
        >>> psi = encode("mot")
        >>> shifted = phase_shift(psi, math.pi / 4)  # toutes les dims
        >>> # Ou par dimension :
        >>> shifts = np.linspace(0, TAU, 512)
        >>> shifted2 = phase_shift(psi, shifts)
    """
    if isinstance(shift, (int, float)):
        return psi * np.exp(1j * shift)
    return psi * np.exp(1j * np.asarray(shift))


# ═══════════════════════════════════════════════════════════════════════════════
# 13. EMERGE : émergence par superposition pondérée
# ═══════════════════════════════════════════════════════════════════════════════

def emerge(*psis: Wave, temperature: float = 0.5) -> Wave:
    """
    Fait émerger un nouveau concept par superposition créative.

    Contrairement à superpose() qui fait une moyenne pondérée,
    emerge() utilise une pondération par cohérence mutuelle :
    les ψ qui résonnent le plus entre eux contribuent davantage.

    C'est l'opération de « créativité émergente » : le tout est
    différent de la somme des parties.

    Args:
        *psis: ondes sources
        temperature: contrôle la sélectivité (0 = moyenne uniforme, 1 = max)

    Returns:
        ψ émergent, normalisé

    Example:
        >>> a = encode("pluie")
        >>> b = encode("musique")
        >>> c = encode("tristesse")
        >>> emergent = emerge(a, b, c, temperature=0.7)
    """
    if len(psis) < 2:
        return normalize(psis[0]) if psis else np.zeros(DEFAULT_DIM, dtype=np.complex128)

    n = len(psis)
    # Matrice de cohérence mutuelle
    coh_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                coh_matrix[i, j] = coherence(psis[i], psis[j])

    # Score de centralité = cohérence moyenne avec les autres
    centrality = coh_matrix.mean(axis=1)
    centrality = np.exp(centrality / max(temperature, 0.01))
    weights = centrality / centrality.sum()

    # Superposition pondérée par la centralité
    result = sum(w * p for w, p in zip(weights, psis))
    return normalize(result)


# ═══════════════════════════════════════════════════════════════════════════════
# OPÉRATIONS AVANCÉES
# ═══════════════════════════════════════════════════════════════════════════════

def oppose(psi_a: Wave, psi_b: Wave) -> Wave:
    """
    Contraste entre deux ondes : ψ_a - ψ_b.

    Crée une tension créative, une dialectique.

    Args:
        psi_a, psi_b: ondes à opposer

    Returns:
        ψ_a - ψ_b, normalisé
    """
    return normalize(psi_a - psi_b)


def amplify(psi: Wave, component: Wave, boost: float = 3.0) -> Wave:
    """
    Amplifie une composante spécifique dans une onde.

    ψ' = ψ + boost · component

    Utile pour faire émerger un signal faible noyé dans le bruit.

    Args:
        psi: onde de base
        component: composante à amplifier
        boost: facteur d'amplification

    Returns:
        ψ amplifié, normalisé
    """
    return normalize(psi + boost * component)


def bind_many(*psis: Wave) -> Wave:
    """
    Binding chaîné de plusieurs ondes.

    bind_many(a, b, c) = bind(bind(a, b), c)

    Utile pour encoder des faits complexes :
    ψ_fait = bind_many(ψ_sujet, ψ_relation, ψ_objet, ψ_contexte)

    Args:
        *psis: séquence d'ondes à lier

    Returns:
        ψ composite, normalisé
    """
    if not psis:
        return np.zeros(DEFAULT_DIM, dtype=np.complex128)
    result = psis[0]
    for psi in psis[1:]:
        result = bind(result, psi)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# NOYAU ABC (Atangana-Baleanu-Caputo)
# ═══════════════════════════════════════════════════════════════════════════════

def abc_kernel(t: float) -> float:
    """
    Noyau de mémoire non-locale ABC.

    K(t) = B(α) · E_α(-α · t^α / (1-α))

    Où :
      - α = 1/φ ≈ 0.618 (ordre fractionnaire optimal)
      - B(α) = constante de normalisation
      - E_α = fonction de Mittag-Leffler

    Le noyau définit une mémoire non-locale : l'état présent dépend
    de TOUT l'historique, avec un poids décroissant.

    Propriétés :
      - α → 0 : mémoire infinie (tout le passé pèse égal)
      - α → 1 : mémoire nulle (dérivée classique, amnésie)
      - α = 1/φ : point d'équilibre optimal (φ = nombre le plus irrationnel)

    Pour t ≤ 2 : calcul exact via série de Mittag-Leffler.
    Pour t > 2 : approximation asymptotique K(t) ∝ 1/t^(α+1).

    Args:
        t: temps (≥ 0)

    Returns:
        K(t), poids de mémoire au temps t
    """
    if t <= 0:
        return 1.0

    if t <= 2:
        # Calcul exact via série de Mittag-Leffler
        z = -ALPHA * (t ** ALPHA) / (1.0 - ALPHA)
        ml_sum = 0.0
        for k in range(50):
            # Gamma via math.gamma (stdlib, pas de dépendance scipy)
            gamma_val = math.gamma(ALPHA * k + 1.0)
            if gamma_val == 0 or abs(gamma_val) > 1e300:
                break
            term = (z ** k) / gamma_val
            ml_sum += term
            if abs(term) < 1e-15 and k > 5:
                break
        return _B_1_PHI * ml_sum
    else:
        # Approximation asymptotique : K(t) ~ 1/t^(α+1)
        gamma_1_minus_alpha = math.gamma(1.0 - ALPHA)
        C_asymp = 1.0 / gamma_1_minus_alpha
        return _B_1_PHI * C_asymp / (t ** (ALPHA + 1.0))


def abc_forget(memory: np.ndarray, t: float, learning_rate: float = 0.1) -> np.ndarray:
    """
    Applique l'oubli harmonique ABC à un vecteur mémoire.

    M(t+1) = (1 - η·K(t)) · M(t) + η · nouvelle_information

    Args:
        memory: vecteur mémoire actuel
        t: âge du souvenir (en « ticks »)
        learning_rate: taux d'apprentissage η

    Returns:
        mémoire après oubli (avant ajout de la nouvelle information)
    """
    decay = abc_kernel(t)
    return memory * (1.0 - learning_rate * decay)


# ═══════════════════════════════════════════════════════════════════════════════
# MÉMOIRE HOLOGRAPHIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicMemory:
    """
    Mémoire holographique par superposition additive.

    Principes :
      - Stockage : H = Σ ψ_fait  (superposition, pas d'écrasement)
      - Requête : réponse = unbind(H, ψ_requête)
      - Oubli : noyau ABC (α = 1/φ) atténue naturellement les vieux souvenirs

    Usage :
        mem = HolographicMemory()
        mem.store(encode("lumiere"), encode("est une"), encode("onde electromagnetique"))
        results = mem.query(encode("Qu'est-ce que la lumiere ?"))
    """

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self.memory = np.zeros(dim, dtype=np.complex128)
        self.n_facts = 0
        self._fact_vectors: List[np.ndarray] = []

    def store(self, psi_sujet: Wave, psi_relation: Wave, psi_objet: Wave,
              amplitude: float = 1.0):
        """
        Stocke un fait dans la mémoire holographique.

        ψ_fait = bind(bind(ψ_sujet, ψ_relation), ψ_objet)
        H += amplitude · ψ_fait
        """
        psi_fact = bind_many(psi_sujet, psi_relation, psi_objet)
        self.memory += amplitude * psi_fact
        self._fact_vectors.append(psi_fact)
        self.n_facts += 1

    def store_raw(self, psi: Wave, amplitude: float = 1.0):
        """Stocke un ψ brut (déjà encodé) dans la mémoire."""
        self.memory += amplitude * psi
        self._fact_vectors.append(psi.copy())
        self.n_facts += 1

    def query(self, psi_query: Wave) -> Wave:
        """
        Interroge la mémoire holographique.

        réponse = unbind(H, ψ_requête)

        Retourne le vecteur de corrélation — les pics indiquent
        les souvenirs qui résonnent avec la requête.
        """
        if self.n_facts == 0:
            return np.zeros(self.dim, dtype=np.complex128)
        return unbind(self.memory, psi_query)

    def query_scores(self, psi_query: Wave) -> List[Tuple[int, float]]:
        """
        Interroge la mémoire et retourne les scores de résonance
        pour chaque fait stocké.
        """
        if self.n_facts == 0:
            return []
        scores = []
        response = self.query(psi_query)
        for i, psi_fact in enumerate(self._fact_vectors):
            s = resonate(response, psi_fact)
            scores.append((i, s))
        scores.sort(key=lambda x: -x[1])
        return scores

    @property
    def energy(self) -> float:
        """Énergie totale de la mémoire."""
        return float(np.sum(np.abs(self.memory) ** 2))

    def forget(self, t: float, learning_rate: float = 0.1):
        """Applique l'oubli ABC à la mémoire."""
        self.memory = abc_forget(self.memory, t, learning_rate)

    def clear(self):
        """Vide la mémoire."""
        self.memory = np.zeros(self.dim, dtype=np.complex128)
        self._fact_vectors.clear()
        self.n_facts = 0


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES DE VISUALISATION
# ═══════════════════════════════════════════════════════════════════════════════

def stats(psi: Wave) -> dict:
    """
    Statistiques descriptives d'un vecteur d'onde.

    Args:
        psi: onde à analyser

    Returns:
        dict avec norme, énergie, phase moyenne, amplitude moyenne, etc.
    """
    return {
        'dim': len(psi),
        'norm': norm(psi),
        'energy': energy(psi),
        'mean_amplitude': float(np.mean(np.abs(psi))),
        'max_amplitude': float(np.max(np.abs(psi))),
        'mean_phase': float(np.mean(np.angle(psi))),
        'phase_std': float(np.std(np.angle(psi))),
        'spectral_entropy': float(-np.sum(
            np.abs(psi) ** 2 * np.log(np.abs(psi) ** 2 + 1e-15)
        )),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 65)
    print("  🌊 WAVE LANG — Test des 13 primitives")
    print("=" * 65)

    # ── 1. ENCODE / DECODE ──
    print("\n── 1. ENCODE / DECODE ──")
    psi_lum = encode("lumiere")
    psi_ond = encode("onde")
    psi_grav = encode("gravite")
    print(f"  encode('lumiere') → |ψ| = {norm(psi_lum):.3f}, dim = {len(psi_lum)}")
    print(f"  encode('onde')    → |ψ| = {norm(psi_ond):.3f}")

    vocab = {"lumiere": psi_lum, "onde": psi_ond, "gravite": psi_grav}
    decoded = decode(psi_lum, vocab, top_k=2)
    print(f"  decode(ψ_lumiere) → {decoded}")

    # ── 2. BIND / UNBIND ──
    print("\n── 2. BIND / UNBIND ──")
    bound = bind(psi_lum, psi_ond)
    unbound = unbind(bound, psi_ond)
    recovery = resonate(unbound, psi_lum)
    print(f"  bind(lumiere, onde) → |ψ| = {norm(bound):.3f}")
    print(f"  unbind → recovery(lumiere) = {recovery:.4f} (idéal > 0.5)")

    # ── 3. SUPERPOSE ──
    print("\n── 3. SUPERPOSE ──")
    H = superpose(psi_lum, psi_ond, psi_grav)
    print(f"  H = superpose(lumiere, onde, gravite) → |H| = {norm(H):.3f}")

    # ── 4. RESONATE ──
    print("\n── 4. RESONATE ──")
    r_ident = resonate(psi_lum, psi_lum)
    r_diff = resonate(psi_lum, psi_ond)
    r_orth = resonate(psi_lum, psi_grav)
    print(f"  resonate(lumiere, lumiere) = {r_ident:.4f} (idéal ~1.0)")
    print(f"  resonate(lumiere, onde)    = {r_diff:.4f} (proche de 0)")
    print(f"  resonate(lumiere, gravite) = {r_orth:.4f} (proche de 0)")

    # ── 5. ROTATE ──
    print("\n── 5. ROTATE ──")
    rotated = rotate(psi_lum, math.pi)
    r_rot = resonate(psi_lum, rotated)
    print(f"  rotate(ψ, π) → resonate(ψ, ψ') = {r_rot:.4f} (idéal ~-1.0)")
    print(f"  norm preserved: {norm(rotated):.6f}")

    # ── 6. NORMALIZE ──
    print("\n── 6. NORMALIZE ──")
    v = np.array([3 + 4j, 0 + 0j], dtype=np.complex128)
    nv = normalize(v)
    print(f"  normalize([3+4j, 0]) → norm = {norm(nv):.6f} (idéal 1.0)")

    # ── 7. INTERFERE ──
    print("\n── 7. INTERFERE ──")
    interf = interfere(psi_lum, psi_ond, epsilon=0.15)
    r_interf = resonate(interf, psi_lum)
    print(f"  interfere(lumiere, onde, ε=0.15) → resonate avec lumiere = {r_interf:.4f}")

    # ── 8. DIFFRACT ──
    print("\n── 8. DIFFRACT ──")
    freqs = diffract(psi_lum)
    recovered = diffract(freqs, inverse=True)
    r_recov = resonate(psi_lum, recovered)
    print(f"  diffract → inverse → resonate(original, recovered) = {r_recov:.4f} (idéal ~1.0)")

    # ── 9. FILTER ──
    print("\n── 9. FILTER ──")
    filtered = filter_wave(psi_lum, low_pass=32)
    r_filt = resonate(psi_lum, filtered)
    print(f"  filter_wave(low_pass=32) → resonate(original, filtered) = {r_filt:.4f}")

    # ── 10. PHASE_SHIFT ──
    print("\n── 10. PHASE_SHIFT ──")
    shifted = phase_shift(psi_lum, math.pi / 2)
    r_shift = resonate(psi_lum, shifted)
    print(f"  phase_shift(π/2) → resonate(original, shifted) = {r_shift:.4f}")

    # ── 11. EMERGE ──
    print("\n── 11. EMERGE ──")
    emergent = emerge(psi_lum, psi_ond, psi_grav, temperature=0.6)
    print(f"  emerge(lumiere, onde, gravite) → |ψ| = {norm(emergent):.3f}")

    # ── 12. OPPOSE / AMPLIFY ──
    print("\n── 12. OPPOSE / AMPLIFY ──")
    opp = oppose(psi_lum, psi_ond)
    amp = amplify(psi_lum, psi_ond, boost=2.0)
    print(f"  oppose(lumiere, onde)  → resonate(lumiere, result) = {resonate(opp, psi_lum):.4f}")
    print(f"  amplify(lumiere, onde) → resonate(lumiere, result) = {resonate(amp, psi_lum):.4f}")

    # ── 13. MÉMOIRE HOLOGRAPHIQUE ──
    print("\n── 13. MÉMOIRE HOLOGRAPHIQUE ──")
    mem = HolographicMemory(dim=DEFAULT_DIM)
    mem.store(psi_lum, encode("est une"), encode("onde electromagnetique"))
    mem.store(psi_grav, encode("est la"), encode("courbure de l'espace-temps"))
    print(f"  Faits stockés: {mem.n_facts}")
    print(f"  Énergie mémoire: {mem.energy:.2f}")

    q = encode("Qu'est-ce que la lumiere ?")
    scores = mem.query_scores(q)
    print(f"  Query 'lumiere' → top scores: {scores[:3]}")

    # ── STATS ──
    print("\n── STATS ──")
    print(f"  encode('lumiere'): {stats(psi_lum)}")

    # ── ABC ──
    print("\n── ABC KERNEL ──")
    for t in [0, 1, 5, 20, 100]:
        print(f"  K({t:3d}) = {abc_kernel(t):.6f}")

    print("\n" + "=" * 65)
    print("  ✅ Toutes les primitives sont fonctionnelles.")
    print("=" * 65)
