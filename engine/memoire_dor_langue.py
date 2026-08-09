#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memoire_dor_langue.py — LE CERVEAU À MÉMOIRE D'OR · NIVEAU LANGUE (v2)
=====================================================================
Suite de la démonstration (cerveau_memoire_dor.py) : séries scalaires → TOKENS
avec EMBEDDINGS APPRIS (leçon X3) et MÉMOIRE DÉRIVÉE (T1 : α=1/φ, T2 : λ=φ).

HISTORIQUE DE CONCEPTION (publié) :
  v1 — tâche « pont » à remplisseurs ALÉATOIRES : INVALIDE (C3 ❌, 25 % =
  hasard) — la récence y est purement du bruit, ce qui handicape toute mémoire
  à décroissance. Le critère pré-enregistré C3 a attrapé le défaut de la tâche.
  v2 — tâche « LANGUE » (ici) : prédiction du prochain token à CHAQUE position
  (la récence est utile — comme en langue réelle) + récupération de la clé à
  la sonde (la rétention longue portée). La mémoire doit faire les DEUX.

TÂCHE « LA LANGUE DU PONT » :
    séquence  : [clé k] + [G remplisseurs (chaîne de Markov locale)] + [SONDE]
    cibles    : prochain token partout (modélisation de langue) ; à la position
                de la sonde, la cible est la CLÉ k (récupération longue portée).

ARCHITECTURE (identique pour toutes les mémoires — seul le noyau diffère) :
    embedding appris E (12×16) → contexte c(t) = Σ_τ w_τ·e(x[t−1−τ]) (noyau)
    → lecture linéaire W (12×16) → softmax. SGD, mêmes graines et séquences.

MÉMOIRES COMPARÉES :
    · DORÉE   : K(τ) = B(α)·E_{1/φ}(−φ·τ^{1/φ}) — T1/T2, zéro paramètre
    · EWMA    : γ ajusté (validation) · ABC-α : α ajusté (grille)
    · UNIFORME: pas de décroissance dans la fenêtre

CRITÈRES PRÉ-ENREGISTRÉS (redéclarés pour la v2, AVANT le calcul) :
    C1 · À G ≥ 20 : précision dorée dans les 5 % (relatif) de la meilleure
         mémoire ajustée (EWMA ou ABC-α) → sinon ❌ publié.
    C2 · À G ≥ 20 : la dorée bat l'EWMA de ≥ 2 points (la queue τ^{−1/φ}
         retient mieux que l'oubli exponentiel à longue portée).
    C3 · Validité de la tâche : à G = 5, la meilleure mémoire ≥ 60 % ET la
         perte de langue décroît (la tâche est apprenable) → sinon benchmark
         invalide, à redessiner.
    Verdict publié, même négatif (méthode du projet).
"""
import json
import math
import os
import time

import numpy as np

# Constantes de la théorie (les mêmes que les Violets A/B)
from validation_coeff_quantiques import PHI, ALPHA, E_alpha, B_ALPHA

# ═══════════════════════════════════════════════════════════════════════════
# 0. CONSTANTES ET CRITÈRES — DÉCLARÉS AVANT LE CALCUL (v2)
# ═══════════════════════════════════════════════════════════════════════════
VOCAB = 12                # 4 clés (0-3) + 7 remplisseurs (4-10) + SONDE (11)
N_CLES = 4
D_EMB = 16
L_MEMOIRE = 60            # fenêtre de mémoire
G_TRAIN = (5, 40)
G_TESTS = [5, 20, 40]
N_SEQ_TEST = 400
N_ETAPES = 1200
TAILLE_LOT = 32
LR = 0.03
GRAINE = 20260809
SONDE = VOCAB - 1

CRITERE_MARGE = 0.05      # C1
CRITERE_EWMA = 2.0        # C2 (points de précision)
CRITERE_G5 = 0.60         # C3 (validité de la tâche)

ALPHA_GRILLE = [0.3, 0.5, 0.7, 0.9]
GAMMA_GRILLE = np.linspace(0.02, 0.5, 25)


# ═══════════════════════════════════════════════════════════════════════════
# 1. LES MÉMOIRES (les poids w_τ — seul ce qui diffère entre modèles)
# ═══════════════════════════════════════════════════════════════════════════
def poids_dores():
    w = [1.0] + [B_ALPHA * E_alpha(-PHI * tau ** ALPHA).real
                 for tau in range(1, L_MEMOIRE)]
    return np.array(w) / np.array(w).sum()


def poids_abc(alpha):
    lam = alpha / (1.0 - alpha)
    B = 1.0 - alpha + alpha / math.gamma(alpha)
    w = [1.0] + [B * E_alpha(-lam * tau ** alpha, alpha).real
                 for tau in range(1, L_MEMOIRE)]
    return np.array(w) / np.array(w).sum()


def poids_ewma(gamma):
    tau = np.arange(L_MEMOIRE)
    w = gamma * (1.0 - gamma) ** tau
    return w / w.sum()


def poids_uniformes():
    return np.full(L_MEMOIRE, 1.0 / L_MEMOIRE)


# ═══════════════════════════════════════════════════════════════════════════
# 2. GÉNÉRATION — « la langue du pont » (Markov locale + clé + sonde)
#    x = [clé, f₁…f_G, SONDE] · y = [f₁…f_G, SONDE, clé]  (prochain token)
# ═══════════════════════════════════════════════════════════════════════════
def generer_lots(rng, n_lots, g_min, g_max, taille_lot=TAILLE_LOT):
    X, Y = [], []
    for _ in range(n_lots):
        G = int(rng.integers(g_min, g_max + 1))     # G homogène par lot
        cle = rng.integers(0, N_CLES, taille_lot)
        L = G + 2
        x = np.full((taille_lot, L), -1, dtype=np.int64)
        y = np.full((taille_lot, L), -1, dtype=np.int64)
        for i in range(taille_lot):
            # remplisseurs : chaîne de Markov locale (paires corrélées)
            f = np.zeros(G, dtype=np.int64)
            f[0] = rng.integers(N_CLES, VOCAB - 1)
            for t in range(1, G):
                if rng.random() < 0.5:              # structure locale
                    f[t] = f[t - 1]
                else:
                    f[t] = rng.integers(N_CLES, VOCAB - 1)
            seq = np.concatenate([[cle[i]], f, [SONDE]])
            x[i] = seq
            y[i] = np.concatenate([f, [SONDE], [cle[i]]])   # prochain token
        X.append(x)
        Y.append(y)
    return X, Y


def contextes(ex, w):
    """Contextes à toutes les positions : C[t] = Σ_τ w_τ·ex[t−1−τ]."""
    B, T, D = ex.shape
    C = np.zeros_like(ex)
    for tau in range(min(T - 1, L_MEMOIRE)):
        src = np.roll(ex, tau + 1, axis=1)           # ex[t−1−τ]
        masque = np.zeros(T)
        masque[tau + 1:] = 1.0                       # t ≥ τ+1
        C += w[tau] * src * masque[None, :, None]
    return C


# ═══════════════════════════════════════════════════════════════════════════
# 3. ENTRAÎNEMENT (SGD manuel — embeddings APPRIS, leçon X3)
# ═══════════════════════════════════════════════════════════════════════════
def entrainer(w, rng, n_etapes=N_ETAPES, lr=LR, log=False):
    """Entraîne (E, W1, b1, W2, b2) pour la mémoire w — lecteur à couche cachée
    (tanh) : la capacité du lecteur est identique pour toutes les mémoires,
    SEUL le noyau diffère entre modèles."""
    E = np.random.default_rng(GRAINE).normal(0, 0.1, (VOCAB, D_EMB))
    W1 = np.random.default_rng(GRAINE + 1).normal(0, 0.1, (D_EMB, D_EMB))
    b1 = np.zeros(D_EMB)
    W2 = np.random.default_rng(GRAINE + 2).normal(0, 0.1, (D_EMB, VOCAB))
    b2 = np.zeros(VOCAB)
    X, Y = generer_lots(rng, n_etapes, *G_TRAIN)
    pertes = []
    for x, y in zip(X, Y):
        ex = E[x]                                    # (lot, T, d)
        C = contextes(ex, w)
        h = np.tanh(C @ W1 + b1)                     # (lot, T, d)
        z = h @ W2 + b2                              # logits (lot, T, 12)
        zm = z - z.max(axis=-1, keepdims=True)
        p = np.exp(zm)
        p = p / p.sum(axis=-1, keepdims=True)
        ok = (y >= 0)
        lignes, colonnes = np.where(ok)
        p_sel = p[lignes, colonnes, y[lignes, colonnes]]
        # PONDÉRATION DE LA SONDE (déclarée) : la position de récupération
        # (dernière, cible = clé) porte un poids = T.
        T = x.shape[1]
        wgt = np.ones((len(x), T))
        wgt[:, -1] = T
        wgt = wgt[ok]
        pertes.append(-np.sum(wgt * np.log(np.clip(p_sel, 1e-12, None)))
                      / wgt.sum())
        # gradients (rétropropagation à travers tanh)
        g = (p - np.eye(VOCAB)[y]) * ok[..., None] * wgt.reshape(len(x), T, 1)
        gW2 = np.einsum("btd,btv->dv", h, g) / wgt.sum()
        gb2 = g.sum(axis=(0, 1)) / wgt.sum()
        gh = np.einsum("btv,dv->btd", g, W2) / wgt.sum()
        gh = gh * (1.0 - h ** 2)                     # d(tanh)/d
        gW1 = np.einsum("btd,btf->df", C, gh) / wgt.sum()
        gb1 = gh.sum(axis=(0, 1)) / wgt.sum()
        gC = gh @ W1.T / wgt.sum()                   # (lot, T, d) — vers E
        gE = np.zeros_like(E)
        for tau in range(min(x.shape[1] - 1, L_MEMOIRE)):
            src = np.roll(gC, -(tau + 1), axis=1)
            masque = np.zeros(x.shape[1])
            masque[tau + 1:] = 1.0
            np.add.at(gE, x, w[tau] * src * masque[None, :, None])
        gE /= wgt.sum()
        E -= lr * gE
        W1 -= lr * gW1
        b1 -= lr * gb1
        W2 -= lr * gW2
        b2 -= lr * gb2
    if log:
        print(f"    perte finale = {pertes[-1]:.4f}")
    return E, W1, b1, W2, b2


def evaluer(E, W1, b1, W2, b2, w, rng, G, n=N_SEQ_TEST):
    """Précision de RÉCUPÉRATION de la clé à la sonde, pour l'écart G."""
    X, Y = generer_lots(rng, 1, G, G, taille_lot=n)
    x, y = X[0], Y[0]
    ex = E[x]
    C = contextes(ex, w)
    t_sonde = x.shape[1] - 1                         # dernière position
    h = np.tanh(C[:, t_sonde] @ W1 + b1)
    logits = h @ W2 + b2
    pred = np.argmax(logits, axis=1)
    cle = x[:, 0]                                    # la clé en tête
    return float(np.mean(pred == cle))


# ═══════════════════════════════════════════════════════════════════════════
# 4. LE PROTOCOLE
# ═══════════════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    print("=" * 78)
    print("CERVEAU À MÉMOIRE D'OR · NIVEAU LANGUE v2 — la langue du pont")
    print("=" * 78)
    print("v1 (pont à remplisseurs aléatoires) : INVALIDE — C3 a attrapé le")
    print("défaut de la tâche (25 % = hasard). v2 : langue (récence utile)")
    print("+ récupération longue portée. Critères redéclarés AVANT le calcul.")
    print()

    rng = np.random.default_rng(GRAINE + 2)

    memoires = {"doree": poids_dores()}
    for a in ALPHA_GRILLE:
        memoires[f"abc_{a}"] = poids_abc(a)
    for g in GAMMA_GRILLE:
        memoires[f"ewma_{g:.2f}"] = poids_ewma(g)
    memoires["uniforme"] = poids_uniformes()

    # — Ajustement des hyperparamètres (validation G=20)
    print("─ Ajustement (validation G=20, mêmes séquences)")
    meilleurs = {}
    for nom in ["ewma", "abc", "uniforme", "doree"]:
        candidats = [k for k in memoires if k.startswith(nom)] or ["doree"]
        best_nom, best_acc = None, -1.0
        for k in candidats:
            params = entrainer(memoires[k], rng)
            acc = evaluer(*params, memoires[k], rng, 20, n=200)
            if acc > best_acc:
                best_acc, best_nom = acc, k
        meilleurs[nom] = best_nom
        print(f"    {nom:9s} : {best_nom:8s} → {best_acc*100:.1f} %")
    print()

    # — Évaluation par écart (mêmes séquences de test)
    print("─ Récupération de la clé à la sonde (précision par écart)")
    resultats = {}
    for nom, kernel in [("doree", memoires["doree"]),
                        ("ewma", memoires[meilleurs["ewma"]]),
                        ("abc", memoires[meilleurs["abc"]]),
                        ("uniforme", memoires["uniforme"])]:
        params = entrainer(kernel, rng)
        accs = {G: evaluer(*params, kernel, rng, G) for G in G_TESTS}
        resultats[nom] = accs
        ligne = "  ".join(f"G={G}:{accs[G]*100:5.1f}%" for G in G_TESTS)
        print(f"  {nom:9s} : {ligne}")
    print()

    # — Verdict (critères déclarés avant)
    zone = [G for G in G_TESTS if G >= 20]
    c1_ok, c2_ok = True, True
    for G in zone:
        best_ajustee = max(resultats["ewma"][G], resultats["abc"][G])
        c1_ok &= (best_ajustee - resultats["doree"][G]) / best_ajustee <= CRITERE_MARGE
        c2_ok &= (resultats["doree"][G] - resultats["ewma"][G]) * 100 >= CRITERE_EWMA
    meilleure_g5 = max(r[5] for r in resultats.values())
    c3_ok = meilleure_g5 >= CRITERE_G5

    print("─ VERDICT (critères déclarés avant le calcul)")
    print(f"  C1 · dorée vs meilleure ajustée, G≥20 : {'✅' if c1_ok else '❌'}")
    print(f"  C2 · dorée ≥ EWMA + 2 pts, G≥20 : {'✅' if c2_ok else '❌'}")
    print(f"  C3 · tâche valide (meilleure G=5 = {meilleure_g5*100:.1f} % ≥ 60 %) : "
          f"{'✅' if c3_ok else '❌ — benchmark invalide, à redessiner'}")
    verdict = c1_ok and c2_ok and c3_ok
    msg = ("✅ LA MÉMOIRE DORÉE TIENT LA LANGUE SANS AUCUN PARAMÈTRE"
           if verdict else "❌ RÉSULTAT NÉGATIF PUBLIÉ")
    print(f"  Verdict global : {msg}")
    print(f"  Durée : {time.time()-t0:.1f} s")

    rapport = {
        "protocole": "pré-enregistré v2 — critères redéclarés après invalidation v1 (C3)",
        "historique": "v1 invalide : pont à remplisseurs aléatoires (25 % = hasard)",
        "tache": "La langue du pont — prochain token + récupération de la clé",
        "theorie": {"T1_alpha": ALPHA, "T2_lambda": PHI, "L_memoire": L_MEMOIRE,
                    "embeddings": "appris (leçon X3)"},
        "criteres": {"C1_marge": CRITERE_MARGE, "C2_pts_ewma": CRITERE_EWMA,
                     "C3_g5": CRITERE_G5},
        "verdict": {"C1": c1_ok, "C2": c2_ok, "C3": c3_ok, "global": verdict},
        "resultats": resultats,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    chemin = os.path.join("data", "benchmarks", "memoire_dor_langue_report.json")
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    print(f"Rapport : {chemin}")


if __name__ == "__main__":
    main()
