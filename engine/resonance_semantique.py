#!/usr/bin/env python3
"""
RÉSONANCE SÉMANTIQUE — Lecture par proximité dans l'espace des fréquences apprises
====================================================================================
Itération 1 de la conception THU V2 (REDEFINITION_IA_V2.md).

Principe :
    La question est une onde excitatrice. Chaque token du vocabulaire est un
    point (kx, ky) dans l'espace de fréquences APPRIS (PPMI / contrastif /
    semantique). La résonance d'un token avec la question = sa proximité
    aux ANCRES (les tokens de la question) : somme de noyaux gaussiens
    pondérés par les amplitudes.

Contraste avec l'ancien chemin :
    - `_scores_equilibre_batch` (decodeur_harmonique_final) cherchait le
      token dont l'onde ANNULE le mieux le résidu (opposition de phase) →
      artefacts hors-sujet (F1 réel = 0,008).
    - La résonance cherche le token qui VIBRE AVEC la question → voisins
      sémantiques dans l'espace appris. C'est le « pattern qui RÉSONNE le
      plus » de la conception.

Statut : vérifié par benchmark (scripts/benchmark_resonance_v2.py).
"""

import numpy as np


def _sigma_adaptatif(kx_t: np.ndarray, ky_t: np.ndarray, seed: int = 0) -> float:
    """Largeur du noyau gaussien : médiane des distances entre tokens distincts.

    Une grande valeur = résonance large (trop de candidats) ; une petite
    valeur = résonance piquée (seuls les voisins immédiats vibrent).
    """
    V = len(kx_t)
    sample = min(V, 400)
    rng = np.random.RandomState(seed)
    idx = rng.choice(V, sample, replace=False)
    dm = np.sqrt(
        (kx_t[idx, None] - kx_t[None, idx]) ** 2
        + (ky_t[idx, None] - ky_t[None, idx]) ** 2
    )
    off = dm[np.triu_indices(sample, 1)]
    off = off[off > 1e-9]
    if len(off) == 0:
        return 0.2
    return float(np.median(off))


def scores_resonance(
    kx_q: np.ndarray,
    ky_q: np.ndarray,
    amp_q: np.ndarray,
    kx_t: np.ndarray,
    ky_t: np.ndarray,
    sigma: float = None,
    mode: str = "max",
) -> tuple:
    """Score de résonance de chaque token avec la signature de la question.

    Args:
        kx_q, ky_q : fréquences des ancres (modes de la question).
        amp_q : amplitudes des ancres (poids de résonance).
        kx_t, ky_t : fréquences de tous les tokens du vocabulaire (V,).
        sigma : largeur du noyau gaussien (None → adaptatif, médiane).
        mode : "max" (chaque ancre émet ses harmoniques — le token retient
            sa meilleure résonance à UNE ancre) ou "somme" (somme pondérée
            sur toutes les ancres). Mesuré : "max" est nettement supérieur
            (F1 0,350 vs 0,290 — les ancres de la question, noyées par la
            somme, réapparaissent dans le top).

    Returns:
        (scores_norm, scores_bruts, sigma, score_confirmation) — scores
        normalisés [0, 1], scores bruts (pondérés par les amplitudes 1/√n),
        sigma, et le score de CONFIRMATION (somme des gaussiennes avec
        amplitudes unitaires — non normalisé par √n) qui sert à la
        calibration du refus : une question dans-corpus a une confirmation
        ~1-4 (plusieurs ancres proches qui se renforcent), une question
        hors-corpus ~0-1,3 (ancres isolées ou absentes).
    """
    V = len(kx_t)
    kx_q = np.asarray(kx_q, dtype=np.float64)
    ky_q = np.asarray(ky_q, dtype=np.float64)
    amp_q = np.asarray(amp_q, dtype=np.float64)

    if len(kx_q) == 0 or len(amp_q) == 0:
        return np.zeros(V), np.zeros(V), 0.0, 0.0

    if sigma is None:
        sigma = _sigma_adaptatif(kx_t, ky_t)

    # Matrice des distances au carré (V, n_ancres)
    d2 = (kx_t[:, None] - kx_q[None, :]) ** 2 + (ky_t[:, None] - ky_q[None, :]) ** 2

    # Noyau gaussien pondéré par les amplitudes des ancres
    w = np.exp(-d2 / (2.0 * sigma * sigma))
    w_pond = w * amp_q[None, :]

    # Score de confirmation : amplitudes unitaires (non normalisées par √n)
    # → la question doit résonner avec PLUSIEURS concepts pour être répondue.
    scores_confirmation = float(w.sum(axis=1).max())

    if mode == "max":
        scores_bruts = w_pond.max(axis=1)
    else:  # "somme" (ancienne formulation)
        scores_bruts = w_pond.sum(axis=1)

    scores_norm = scores_bruts.copy()
    max_s = float(np.max(scores_norm)) if len(scores_norm) else 0.0
    if max_s > 1e-12:
        scores_norm = scores_norm / max_s
    return scores_norm, scores_bruts, sigma, scores_confirmation


def ponderation_idf(amp_q: np.ndarray, freqs: np.ndarray, k: float = 1.5) -> np.ndarray:
    """Pondère les ancres par rareté (IDF doux) : les ancres fréquentes
    (mots génériques) pèsent moins que les ancres spécifiques.

    `poids = 1 / (1 + log(1 + k · freq_norm))` — fréquences normalisées
    par le max du corpus pour rester dans un ordre de grandeur stable.
    """
    amp_q = np.asarray(amp_q, dtype=np.float64)
    freqs = np.asarray(freqs, dtype=np.float64)
    if len(freqs) == 0 or freqs.max() <= 0:
        return amp_q
    f_norm = freqs / freqs.max()
    idf = 1.0 / (1.0 + np.log(1.0 + k * f_norm))
    return amp_q * idf


def renoter_par_coherence(
    scores: np.ndarray,
    tokenizer,
    cache_coh: dict,
    poids_coh: float = 0.25,
) -> np.ndarray:
    """Pondère la résonance par la cohérence calibrée (lecture = amplitude × résonance).

    `score_final = res · (1 - poids_coh + poids_coh · coh)` — la cohérence
    module légèrement ; la résonance reste dominante. Les tokens absents du
    cache reçoivent coh = 0,5 (neutre).
    """
    if cache_coh is None or not cache_coh:
        return scores
    V = len(scores)
    out = scores.copy()
    for tid in range(4, V):
        tok = tokenizer.i2w.get(tid, '')
        if not tok:
            continue
        coh = cache_coh.get(tok, 0.5)
        if coh is None:
            coh = 0.5
        out[tid] *= (1.0 - poids_coh) + poids_coh * float(coh)
    return out
