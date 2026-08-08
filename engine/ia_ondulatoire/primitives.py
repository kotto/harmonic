# -*- coding: utf-8 -*-
"""
primitives.py — Les 13 primitives universelles du langage ondulatoire.

Implémentation from scratch, conforme au DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md
(§2 fondements mathématiques, §5 les 13 primitives, §10.1 validations).

Espace : ℂ⁵¹² (limite de Bekenstein) — vecteurs d'onde toujours normalisés (‖ψ‖ = 1).
Encodage : FNV-1a × φ-spacing (déterministe, même entité → même ψ sur toute machine).
Binding : convolution circulaire (HRR, Plate 1995).
Mémoire : noyau fractionnaire ABC avec α = 1/φ ≈ 0.618.

API — ENCODE → MANIPULER → DÉCODER :
    ψ = encode("lumiere")                     # monde → ψ
    mots = decode(ψ, vocabulaire)             # ψ → monde (plus proche voisin)
    c = bind(a, b) ; a' = unbind(c, b)        # lier / délier
    h = superpose(ψ1, ψ2)                     # mémoire holographique
    s = resonate(ψ1, ψ2)                      # similarité ∈ [-1, 1]
    mem = HolographicMemory() ; mem.store(...) ; faits = mem.interroger(ψ_q)
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

# ────────────────────────────────────────────────────────────────────────
# Constantes fondamentales
# ────────────────────────────────────────────────────────────────────────

PHI: float = (1.0 + math.sqrt(5.0)) / 2.0          # φ ≈ 1.618033988749895
DEFAULT_DIM: int = 512                              # ℂ⁵¹² — limite de Bekenstein
_MASK64: int = (1 << 64) - 1
_CACHE_ENCODE: Dict[Tuple[str, int], "Wave"] = {}


# ────────────────────────────────────────────────────────────────────────
# Types
# ────────────────────────────────────────────────────────────────────────

Wave = np.ndarray          # np.complex128[dim], ‖ψ‖ = 1
Scalar = float             # résonance ∈ [-1, 1]


# ────────────────────────────────────────────────────────────────────────
# 0. Hachage FNV-1a (fondement de l'encode déterministe)
# ────────────────────────────────────────────────────────────────────────

def fnv1a(texte: str) -> int:
    """Hash FNV-1a 64-bit — déterministe, rapide, sans collision pratique (~40k mots)."""
    h = 0xCBF29CE484222325
    for octet in texte.encode("utf-8"):
        h ^= octet
        h = (h * 0x100000001B3) & _MASK64
    return h


def _splitmix64(z: int) -> int:
    """Mélangeur déterministe 64-bit (utilisé comme générateur par dimension)."""
    z = (z + 0x9E3779B97F4A7C15) & _MASK64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK64
    return z ^ (z >> 31)


# ────────────────────────────────────────────────────────────────────────
# 1. ENCODE — monde → ψ   (§5.2.1)
#    Déterministe : FNV-1a(entity) × φ-spacing → ψ ∈ ℂ⁵¹², ‖ψ‖ = 1
# ────────────────────────────────────────────────────────────────────────

def encode(entite: str, dim: int = DEFAULT_DIM, use_cache: bool = True) -> Wave:
    """Encode une entité discrète en vecteur d'onde unitaire.

    Construction : phase_k = 2π · frac(k·φ + u_k), où u_k est un bruit
    déterministe dérivé du hash FNV-1a de l'entité (splitmix64). Le squelette
    φ-espacé (Three-Gap Theorem, Sós 1958) minimise l'énergie de Riesz entre
    concepts ; le bruit par dimension rend deux entités distinctes quasi-orthogonales.
    Vectorisé (numpy uint64) : ~190 000 encodages/s — requis pour les 62 k faits médicaux.
    """
    if use_cache:
        cle = (entite, dim)
        psi = _CACHE_ENCODE.get(cle)
        if psi is not None:
            return psi
    h = fnv1a(entite)
    k = np.arange(dim, dtype=np.uint64)
    z = (h ^ (k * np.uint64(0x100000001B3))) & np.uint64(_MASK64)
    z = (z + np.uint64(0x9E3779B97F4A7C15)) & np.uint64(_MASK64)
    z = ((z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)) & np.uint64(_MASK64)
    z = ((z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)) & np.uint64(_MASK64)
    z = z ^ (z >> np.uint64(31))
    u = (z & np.uint64((1 << 48) - 1)).astype(np.float64) / float(1 << 48)   # u ∈ [0, 1)
    phases = 2.0 * math.pi * np.fmod(k.astype(np.float64) * PHI + u, 1.0)
    psi = np.exp(1j * phases)                                # |ψ_k| = 1 → ‖ψ‖ = √512
    psi = psi / np.linalg.norm(psi)                          # projection unité
    if use_cache:
        _CACHE_ENCODE[cle] = psi
    return psi


def encode_many(entites: Sequence[str], dim: int = DEFAULT_DIM) -> Dict[str, Wave]:
    """Pré-encode une liste d'entités (construction d'un vocabulaire)."""
    return {e: encode(e, dim) for e in entites}


# ────────────────────────────────────────────────────────────────────────
# 2. DÉCODE — ψ → monde   (§5.2.2)
#    Plus proche voisin dans le vocabulaire par résonance.
# ────────────────────────────────────────────────────────────────────────

def decode(psi: Wave, vocabulaire: Dict[str, Wave] = None, top_k: int = 5) -> List[Tuple[str, float]]:
    """Décode un vecteur d'onde vers les entités du vocabulaire les plus résonantes.

    Retourne [(entité, score ∈ [-1, 1])] trié par score décroissant.
    """
    if vocabulaire is None or not vocabulaire:
        return []
    if not isinstance(psi, np.ndarray) or psi.ndim != 1:
        return []
    scores = [(mot, float(resonate(psi, psi_v))) for mot, psi_v in vocabulaire.items()]
    scores.sort(key=lambda t: -t[1])
    return scores[:top_k]


# ────────────────────────────────────────────────────────────────────────
# 3/4. BIND / UNBIND — lier / délier (§5.2.3-4)
#      Convolution circulaire (HRR, Plate 1995) : O(D log D) via FFT.
# ────────────────────────────────────────────────────────────────────────

def bind(psi_a: Wave, psi_b: Wave) -> Wave:
    """Lie deux concepts : bind(a, b) = IFFT(FFT(a) × FFT(b)). Réversible, commutatif."""
    c = np.fft.ifft(np.fft.fft(psi_a) * np.fft.fft(psi_b))
    return normalize(c)


def unbind(psi_c: Wave, psi_b: Wave) -> Wave:
    """Délie : unbind(bind(a, b), b) ≈ a (récupération approximative)."""
    a = np.fft.ifft(np.fft.fft(psi_c) * np.conj(np.fft.fft(psi_b)))
    return normalize(a)


def bind_many(*psis: Wave) -> Wave:
    """Lie n concepts en un seul fait : bind(bind(a, b), c)… Complexité O(D log D)."""
    if not psis:
        raise ValueError("bind_many : au moins un vecteur requis")
    resultat = psis[0]
    for psi in psis[1:]:
        resultat = bind(resultat, psi)
    return resultat


# ────────────────────────────────────────────────────────────────────────
# 5. SUPERPOSE — additionner des ondes (§5.2.5)
#    L'opération fondamentale de l'holographie : la mémoire H = Σ ψ_fait.
# ────────────────────────────────────────────────────────────────────────

def superpose(*psis: Wave, weights: Optional[Sequence[float]] = None) -> Wave:
    """Additionne des ondes (mémoire holographique). Linéaire, commutative, associative."""
    if not psis:
        raise ValueError("superpose : au moins un vecteur requis")
    if weights is None:
        somme = np.sum(np.stack(psis), axis=0)
    else:
        if len(weights) != len(psis):
            raise ValueError("superpose : weights et psis de tailles différentes")
        somme = np.sum(np.stack(psis) * np.asarray(weights, dtype=np.float64)[:, None], axis=0)
    return normalize(somme)


# ────────────────────────────────────────────────────────────────────────
# 6. RESONATE — mesurer la cohérence (§5.2.6)
#    Cosinus complexe normalisé ∈ [-1, 1] : +1 identiques, 0 orthogonaux, -1 opposés.
# ────────────────────────────────────────────────────────────────────────

def resonate(psi_a: Wave, psi_b: Wave) -> Scalar:
    """resonate(a, b) = Re(⟨a|b⟩) / (‖a‖·‖b‖). Attention et retrieval."""
    na = float(np.linalg.norm(psi_a))
    nb = float(np.linalg.norm(psi_b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.real(np.vdot(psi_a, psi_b) / (na * nb)))


def coherence(psi_a: Wave, psi_b: Wave) -> float:
    """Similarité non-directionnelle |resonate(a, b)| ∈ [0, 1]."""
    return abs(resonate(psi_a, psi_b))


# ────────────────────────────────────────────────────────────────────────
# 7. ROTATE — changer de perspective (§5.2.7) — groupe U(1), préserve ‖ψ‖
# ────────────────────────────────────────────────────────────────────────

def rotate(psi: Wave, angle: float) -> Wave:
    """rotate(ψ, θ) = ψ · e^{iθ}. Perspective : position, émotion, style."""
    return psi * np.exp(1j * angle)


# ────────────────────────────────────────────────────────────────────────
# 8. NORMALIZE — projeter sur le cercle unité (§5.2.8)
# ────────────────────────────────────────────────────────────────────────

def normalize(psi: Wave) -> Wave:
    """Projection sur le cercle unité. Toute primitive retourne un ψ normalisé."""
    n = float(np.linalg.norm(psi))
    if n < 1e-12:
        return psi * 0.0 + 1.0 / math.sqrt(psi.size)
    return psi / n


# ────────────────────────────────────────────────────────────────────────
# 9. INTERFERE — interférence contrôlée (§5.2.9) — primitive de créativité
# ────────────────────────────────────────────────────────────────────────

def interfere(psi_a: Wave, psi_b: Wave, epsilon: float = 0.15) -> Wave:
    """interfere(a, b, ε) = normalize(a + ε·b).
    ε ≈ 0.1 connexion subtile · 0.5 mélange équilibré · > 1.0 : b domine."""
    return normalize(psi_a + epsilon * psi_b)


# ────────────────────────────────────────────────────────────────────────
# 10. DIFFRACT — analyse spectrale (§5.2.10) — dualité temps-fréquence (Gabor)
# ────────────────────────────────────────────────────────────────────────

def diffract(psi: Wave, inverse: bool = False) -> Wave:
    """diffract(ψ) = FFT(ψ) ; diffract(ψ, inverse=True) = IFFT(ψ).
    Retourne le spectre brut (non normalisé) pour préserver la bijection FFT/IFFT."""
    if inverse:
        return np.fft.ifft(psi)
    return np.fft.fft(psi)


# ────────────────────────────────────────────────────────────────────────
# 11. FILTER — filtrage spectral (§5.2.11) — FFT → masque → IFFT
# ────────────────────────────────────────────────────────────────────────

def filter_wave(psi: Wave, mode: str = "low", cutoff: float = 32.0,
                cutoff_bas: Optional[float] = None, cutoff_haut: Optional[float] = None) -> Wave:
    """Passe-bas / passe-haut / passe-bande dans le domaine fréquentiel.
    mode ∈ {'low', 'high', 'band'} ; cutoff = fréquence de coupure (bins FFT)."""
    dim = psi.size
    spec = np.fft.fft(psi)
    masque = np.ones(dim, dtype=np.complex128)
    freqs = np.fft.fftfreq(dim, d=1.0) * dim
    if mode == "low":
        masque[np.abs(freqs) > cutoff] = 0.0
    elif mode == "high":
        masque[np.abs(freqs) < cutoff] = 0.0
    elif mode == "band":
        if cutoff_bas is None or cutoff_haut is None:
            raise ValueError("filter band : cutoff_bas et cutoff_haut requis")
        masque[np.abs(freqs) < cutoff_bas] = 0.0
        masque[np.abs(freqs) > cutoff_haut] = 0.0
    else:
        raise ValueError(f"filter : mode inconnu '{mode}'")
    return normalize(np.fft.ifft(spec * masque))


# ────────────────────────────────────────────────────────────────────────
# 12. PHASE_SHIFT — décalage par dimension (§5.2.12)
# ────────────────────────────────────────────────────────────────────────

def phase_shift(psi: Wave, decalage: Union[float, Sequence[float]]) -> Wave:
    """Scalaire → équivalent à rotate ; vecteur → chaque dimension reçoit son décalage."""
    if np.isscalar(decalage):
        return psi * np.exp(1j * float(decalage))
    d = np.asarray(decalage, dtype=np.float64)
    if d.size != psi.size:
        raise ValueError("phase_shift : vecteur de décalage de mauvaise dimension")
    return psi * np.exp(1j * d)


# ────────────────────────────────────────────────────────────────────────
# 13. EMERGE — émergence par cohérence (§5.2.13)
#     Pondère par cohérence mutuelle : le tout diffère de la somme des parties.
# ────────────────────────────────────────────────────────────────────────

def emerge(*psis: Wave, temperature: float = 0.5) -> Wave:
    """emerge(ψ₁…ψₙ, temperature) = Σ wᵢ·ψᵢ avec wᵢ ∝ exp(centralitéᵢ / temperature).
    Les concepts qui résonnent le plus entre eux contribuent davantage."""
    if not psis:
        raise ValueError("emerge : au moins un vecteur requis")
    matrice = np.ones((len(psis), len(psis)))
    for i in range(len(psis)):
        for j in range(len(psis)):
            if i != j:
                matrice[i, j] = abs(resonate(psis[i], psis[j]))
    centralite = matrice.sum(axis=1)                       # cohérence mutuelle brute
    temp = max(temperature, 1e-6)
    w = np.exp(centralite / temp)
    w = w / w.sum()
    somme = np.sum(np.stack(psis) * w[:, None], axis=0)
    return normalize(somme)


# ────────────────────────────────────────────────────────────────────────
# Primitives avancées (§5.3)
# ────────────────────────────────────────────────────────────────────────

def oppose(psi_a: Wave, psi_b: Wave) -> Wave:
    """Contraste, tension dialectique : a − b."""
    return normalize(psi_a - psi_b)


def amplify(psi: Wave, composante: Wave, boost: float = 3.0) -> Wave:
    """Faire émerger l'invisible : ψ + boost·composante."""
    return normalize(psi + boost * composante)


# ────────────────────────────────────────────────────────────────────────
# Noyau ABC — mémoire fractionnaire (§2.4) — α = 1/φ ≈ 0.618
# ────────────────────────────────────────────────────────────────────────

def _mittag_leffler(z: float, alpha: float, tolerance: float = 1e-10) -> float:
    """E_α(z) = Σ z^k / Γ(αk + 1) — série par récurrence EXACTE.

    terme_k = terme_{k-1} · z · Γ(α(k−1)+1)/Γ(αk+1)
    (CORRIGÉ 08/08/2026 : l'ancienne récurrence « terme *= z/Γ(αk+1) »
    donnait z^k/(Γ(α+1)·Γ(2α+1)·…) au lieu de z^k/Γ(αk+1) — erreur
    jusqu'à ~56 % à z=2, noyau de mémoire non monotone.)

    Les termes croissent jusqu'à k ≈ |z|^{1/α}/α avant de décroître : le nombre
    de termes est adaptatif (sinon la somme tronquée diverge, ex. t = 100)."""
    import math as m
    if abs(z) < 1e-12:
        return 1.0
    max_termes = min(int(2.0 * (abs(z) ** (1.0 / alpha)) / alpha) + 300, 4000)
    terme = 1.0
    total = terme
    for k in range(1, max_termes):
        terme *= z * m.gamma(alpha * (k - 1) + 1.0) / m.gamma(alpha * k + 1.0)
        total += terme
        if abs(terme) < tolerance * max(1.0, abs(total)):
            break
    return total


def abc_kernel(t: float, alpha: float = 1.0 / PHI) -> float:
    """Noyau de mémoire d'Atangana-Baleanu-Caputo, ordre optimal α = 1/φ.
    K(0) = 1 (passé intégralement présent) ; K(t) → 0 (oubli progressif).
    α = 1/φ : point d'équilibre entre inertie (α→0) et amnésie (α→1).

    Calcul : série directe pour x = c·t^α ≤ 8 ; régime asymptotique
    E_α(−x) ≈ 1/(x·Γ(1−α)) au-delà (la série déborde en float64 aux grands t)."""
    if t <= 0.0:
        return 1.0
    c = alpha / (1.0 - alpha)
    x = c * (t ** alpha)
    if x <= 8.0:
        return float(_mittag_leffler(-x, alpha))
    import math as m
    return float(1.0 / (x * m.gamma(1.0 - alpha)))


def abc_forget(memoire: "HolographicMemory", t: float, learning_rate: float = 0.1) -> None:
    """Oubli fractionnaire : applique le noyau ABC aux amplitudes des faits."""
    facteur = 1.0 - learning_rate * (1.0 - abc_kernel(t))
    memoire._amplitudes = [amp * max(facteur, 0.0) for amp in memoire._amplitudes]
    memoire._reconstruire_memoire()


# ────────────────────────────────────────────────────────────────────────
# HolographicMemory — mémoire holographique (§5.2.5, §9.2)
# ────────────────────────────────────────────────────────────────────────

@dataclass
class Fait:
    """Un fait = bind_many(sujet, relation, objet, [contexte]) stocké dans l'hologramme."""
    sujet: str
    relation: str
    objet: str
    secteur: str = ""
    amplitude: float = 1.0
    doc_id: str = ""
    date: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    _psi: Optional[Wave] = field(default=None, repr=False)
    _normaliser: Optional[callable] = field(default=None, repr=False)
    _dim: int = field(default=DEFAULT_DIM, repr=False)

    @property
    def psi(self) -> Wave:
        if self._psi is None:
            n = self._normaliser or (lambda x: x)
            self._psi = bind_many(encode(n(self.sujet), self._dim),
                                  encode(n(self.relation), self._dim),
                                  encode(n(self.objet), self._dim))
        return self._psi

    def texte(self) -> str:
        if self.relation == "":
            return self.sujet
        return f"{self.sujet} {self.relation} {self.objet}"


class HolographicMemory:
    """Superposition additive de faits : H = Σ ψ_fait. Aucun souvenir n'écrase l'autre.

    store(sujet, relation, objet)   — apprendre un fait (BIND_MANY → SUPERPOSE)
    interroger(ψ_q, top_k, seuil)   — QUERY : résonance de chaque fait avec la question
    unbind_raw(ψ_q)                 — QUERY pur : unbind(H, ψ_q) (retrieval holographique)
    oublier(t, lr)                  — oubli fractionnaire ABC
    sauvegarder / charger           — persistance disque (npz)
    """

    def __init__(self, dim: int = DEFAULT_DIM, normaliser: Optional[callable] = None):
        self.dim = dim
        self._normaliser = normaliser
        self._memoire = np.zeros(dim, dtype=np.complex128)
        self._faits: List[Fait] = []
        self._amplitudes: List[float] = []
        self.nb_requetes = 0

    # ── écriture ────────────────────────────────────────────────────────
    def store(self, sujet: str, relation: str, objet: str, secteur: str = "",
              amplitude: float = 1.0, doc_id: str = "") -> Fait:
        """Apprend un fait : ψ_fait = bind_many(ψ_sujet, ψ_relation, ψ_objet) ; H += ψ_fait."""
        fait = Fait(sujet=sujet, relation=relation, objet=objet,
                    secteur=secteur, amplitude=amplitude, doc_id=doc_id,
                    _normaliser=self._normaliser, _dim=self.dim)
        self._faits.append(fait)
        self._amplitudes.append(amplitude)
        self._memoire += fait.psi * amplitude
        return fait

    def store_psi(self, psi: Wave, texte: str, secteur: str = "", amplitude: float = 1.0,
                  doc_id: str = "") -> Fait:
        """Stocke directement un vecteur d'onde (fait pré-calculé ou émergent)."""
        fait = Fait(sujet=texte, relation="", objet="", secteur=secteur,
                    amplitude=amplitude, doc_id=doc_id, _psi=normalize(psi))
        self._faits.append(fait)
        self._amplitudes.append(amplitude)
        self._memoire += normalize(psi) * amplitude
        return fait

    def store_batch(self, triplets, secteur: str = "") -> int:
        """Apprend n faits [(s, r, o), …] d'un coup. Retourne le nombre stocké."""
        n = 0
        for t in triplets:
            if len(t) >= 3:
                self.store(str(t[0]), str(t[1]), str(t[2]), secteur)
                n += 1
        return n

    # ── lecture ─────────────────────────────────────────────────────────
    @property
    def energie(self) -> float:
        """Énergie de la mémoire = norme de la superposition."""
        return float(np.linalg.norm(self._memoire))

    @property
    def nb_faits(self) -> int:
        return len(self._faits)

    def interroger(self, psi_q: Wave, top_k: int = 5, seuil: float = 0.10) -> List[Tuple[Fait, float]]:
        """QUERY : mesure la résonance de la question avec chaque fait, retourne les top-k.
        Chaque score est l'attention <ψ_q | ψ_fait> (interférence constructive/destructive)."""
        self.nb_requetes += 1
        scores = []
        for fait, amp in zip(self._faits, self._amplitudes):
            s = resonate(psi_q, fait.psi) * amp
            if s > seuil:
                scores.append((fait, float(s)))
        scores.sort(key=lambda t: -t[1])
        return scores[:top_k]

    def scores(self, psi_q: Wave) -> List[Tuple[int, float]]:
        """Scores bruts de tous les faits contre la question (diagnostic)."""
        return [(i, float(resonate(psi_q, f.psi) * self._amplitudes[i]))
                for i, f in enumerate(self._faits)]

    def unbind_raw(self, psi_q: Wave) -> Wave:
        """QUERY pur : ψ_r = unbind(H, ψ_q) — le tout de la mémoire résonne avec la question."""
        return unbind(normalize(self._memoire), psi_q)

    def resonance_globale(self, psi_q: Wave) -> float:
        """Résonance de la question avec l'hologramme entier ∈ [-1, 1]."""
        if self.energie < 1e-12:
            return 0.0
        return resonate(psi_q, normalize(self._memoire))

    # ── oubli ───────────────────────────────────────────────────────────
    def oublier(self, t: float = 1.0, learning_rate: float = 0.1) -> None:
        """Oubli fractionnaire ABC : les souvenirs anciens pèsent moins."""
        abc_forget(self, t, learning_rate)

    def _reconstruire_memoire(self) -> None:
        self._memoire = np.zeros(self.dim, dtype=np.complex128)
        for fait, amp in zip(self._faits, self._amplitudes):
            self._memoire += fait.psi * amp

    def vider(self) -> None:
        self._faits.clear()
        self._amplitudes.clear()
        self._memoire = np.zeros(self.dim, dtype=np.complex128)

    # ── persistance ─────────────────────────────────────────────────────
    def sauvegarder(self, chemin: str) -> None:
        """Persiste l'hologramme (faits + vecteurs) au format npz."""
        d = os.path.dirname(chemin)
        if d:
            os.makedirs(d, exist_ok=True)
        faits = np.array([(f.sujet, f.relation, f.objet, f.secteur, f.amplitude, f.doc_id, f.date)
                          for f in self._faits], dtype=object)
        np.savez_compressed(
            chemin,
            dim=np.int64(self.dim),
            memoire_reelle=np.real(self._memoire),
            memoire_imaginaire=np.imag(self._memoire),
            faits=faits,
            nb_requetes=np.int64(self.nb_requetes),
        )

    def charger(self, chemin: str) -> bool:
        """Recharge un hologramme sauvegardé. Retourne False si absent/illisible."""
        if not os.path.exists(chemin):
            return False
        try:
            z = np.load(chemin, allow_pickle=True)
            self.dim = int(z["dim"])
            self._memoire = z["memoire_reelle"].astype(np.complex128) \
                + 1j * z["memoire_imaginaire"].astype(np.complex128)
            self._faits = []
            self._amplitudes = []
            for row in z["faits"]:
                s, r, o, sec, amp, doc, date = row
                self._faits.append(Fait(sujet=str(s), relation=str(r), objet=str(o),
                                        secteur=str(sec), amplitude=float(amp),
                                        doc_id=str(doc), date=str(date),
                                        _normaliser=self._normaliser, _dim=self.dim))
                self._amplitudes.append(float(amp))
            self.nb_requetes = int(z.get("nb_requetes", 0))
            return True
        except Exception:
            return False
