#!/usr/bin/env python3
"""
EXPÉRIENCE FALSIFIABLE — Validation de l'encodage harmonique φ
==============================================================
Question : L'encodage φ capture-t-il la sémantique ?

Protocole :
  1. Dataset de paires étiquetées (proches vs éloignées)
  2. 4 méthodes comparées :
     - Similarité de caractères (baseline naïve)
     - Embedding φ 1D (ordonnancement spectral sur 1 phase)
     - Embedding φ kD (ordonnancement spectral sur 16 phases)
     - FastText brut (référence upper-bound)
  3. Métrique : corrélation de Spearman avec le gold standard humain

Si φ-kD > caractères : l'encodage harmonique capture un signal sémantique
Si φ-kD ≈ FastText  : VALIDATION FORTE de la théorie
Si φ-kD < caractères : l'encodage φ n'apporte rien
"""
import sys, time, json, math
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1.0 / PHI
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# DATASET — Paires étiquetées (gold standard sémantique)
# ═══════════════════════════════════════════════════════════════════════════════
# Score humain : 1.0 = synonyme/très proche, 0.5 = apparenté, 0.0 = sans rapport

DATASET = [
    # ── Paires très proches (score = 1.0) ──
    ("homme", "femme", 1.0),
    ("roi", "reine", 1.0),
    ("fils", "fille", 1.0),
    ("pere", "mere", 1.0),
    ("frere", "soeur", 1.0),
    ("chat", "chien", 1.0),
    ("cheval", "ane", 1.0),
    ("joie", "bonheur", 1.0),
    ("tristesse", "chagrin", 1.0),
    ("peur", "effroi", 1.0),
    ("grand", "petit", 1.0),
    ("haut", "bas", 1.0),
    ("long", "court", 1.0),
    ("fort", "faible", 1.0),
    ("chaud", "froid", 1.0),
    ("rapide", "lent", 1.0),
    ("clair", "obscur", 1.0),
    ("beau", "laid", 1.0),
    ("vrai", "faux", 1.0),
    ("bon", "mauvais", 1.0),
    ("jour", "nuit", 1.0),
    ("soleil", "lune", 1.0),
    ("ete", "hiver", 1.0),
    ("printemps", "automne", 1.0),
    ("amour", "passion", 1.0),
    ("guerre", "paix", 1.0),
    ("vie", "mort", 1.0),
    ("naissance", "deces", 1.0),

    # ── Paires apparentées (score = 0.5) ──
    ("maison", "ville", 0.5),
    ("livre", "ecole", 0.5),
    ("pain", "farine", 0.5),
    ("medecin", "hopital", 0.5),
    ("juge", "tribunal", 0.5),
    ("peintre", "tableau", 0.5),
    ("musicien", "instrument", 0.5),
    ("temps", "heure", 0.5),
    ("argent", "prix", 0.5),
    ("travail", "metier", 0.5),
    ("esprit", "pensee", 0.5),
    ("corps", "sante", 0.5),
    ("terre", "jardin", 0.5),
    ("mer", "bateau", 0.5),
    ("ciel", "nuage", 0.5),
    ("arbre", "foret", 0.5),

    # ── Paires sans rapport (score = 0.0) ──
    ("guerre", "philosophie", 0.0),
    ("sang", "silence", 0.0),
    ("mort", "joie", 0.0),
    ("fer", "liberte", 0.0),
    ("calcul", "reve", 0.0),
    ("terre", "esprit", 0.0),
    ("guerre", "poesie", 0.0),
    ("sang", "logique", 0.0),
    ("ombre", "mathematique", 0.0),
    ("vent", "justice", 0.0),
    ("pierre", "musique", 0.0),
    ("eau", "honneur", 0.0),
    ("feu", "tristesse", 0.0),
    ("or", "sagesse", 0.0),
    ("fer", "beaute", 0.0),
]


# ═══════════════════════════════════════════════════════════════════════════════
# MÉTHODES
# ═══════════════════════════════════════════════════════════════════════════════

def similarite_caracteres(a, b):
    """Baseline : similarité de trigrammes de caractères."""
    if a == b:
        return 1.0
    ta = {f"_{a}"[i:i+3] for i in range(len(f"_{a}_")-2)}
    tb = {f"_{b}"[i:i+3] for i in range(len(f"_{b}_")-2)}
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / max(union, 1)


def charger_fasttext():
    """Charge FastText comme référence sémantique et source d'embedding."""
    from gensim.models import FastText
    model = FastText.load('ka_knowledge_base/fasttext_model.bin')
    return model


def similarite_fasttext(model, a, b):
    """Référence upper-bound : FastText brut."""
    if a not in model.wv or b not in model.wv:
        return 0.0
    return float(model.wv.similarity(a, b))


def ordonnancement_spectral(embedding_matrix, k=1):
    """
    Ordonne les mots par coordonnées spectrales.
    
    embedding_matrix : [N, D] — vecteurs FastText pour N mots
    k : nombre de dimensions spectrales à utiliser
    
    Retourne : matrice [N, k] de phases φ dans [0, 2π]
    """
    N = embedding_matrix.shape[0]
    
    # Similarité cosinus entre mots
    norms = np.linalg.norm(embedding_matrix, axis=1, keepdims=True) + 1e-10
    normalized = embedding_matrix / norms
    S = normalized @ normalized.T  # [N, N] similarité cosinus
    S = np.maximum(S, 0)  # PPMI-like : que les positives
    
    # Laplacien normalisé
    D = np.diag(S.sum(axis=1) + 1e-10)
    D_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(D)))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    
    # k vecteurs propres de plus basse valeur propre (après le trivial)
    eigvals, eigvecs = np.linalg.eigh(L)
    # eigvals triés croissants ; ignorer le premier (trivial ~0)
    coords = eigvecs[:, 1:k+1]  # [N, k]
    
    # Convertir en phases
    if k == 1:
        phases = np.arctan2(np.zeros(N), coords[:, 0]) % TAU  # pas idéal en 1D
        # Mieux : utiliser directement la coordonnée normalisée
        c = coords[:, 0]
        phases = TAU * (c - c.min()) / (c.max() - c.min() + 1e-10)
    else:
        # k phases : une par dimension spectrale
        phases = np.zeros((N, k))
        for d in range(k):
            c = coords[:, d]
            phases[:, d] = TAU * (c - c.min()) / (c.max() - c.min() + 1e-10)
    
    return phases


def embedding_phi_1d(phases_1d, dim=128):
    """Embedding φ à partir d'une phase 1D."""
    N = len(phases_1d)
    ds = np.arange(dim, dtype=np.float32)
    # Chaque mot : vecteur cos(phase × d × φ) décroissant
    emb = np.zeros((N, dim), dtype=np.float32)
    for i in range(N):
        emb[i] = np.cos(phases_1d[i] * ds * PHI / dim) * np.exp(-ds * ALPHA / dim)
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    return emb / norms


def embedding_phi_kd(phases_kd, dim=128):
    """Embedding φ à partir de k phases (k dimensions spectrales)."""
    N, k = phases_kd.shape
    ds = np.arange(dim, dtype=np.float32)
    emb = np.zeros((N, dim), dtype=np.float32)
    for i in range(N):
        # Combiner k phases : cos(Σ_d phase_d × freq × φ)
        total_phase = np.zeros(dim)
        for d in range(k):
            total_phase += phases_kd[i, d] * ds * PHI / dim * (PHI ** (-d))
        emb[i] = np.cos(total_phase) * np.exp(-ds * ALPHA / dim)
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    return emb / norms


def similarite_cosinus(emb, idx_a, idx_b):
    """Similarité cosinus entre deux embeddings."""
    return float(np.dot(emb[idx_a], emb[idx_b]))


def spearman_correlation(x, y):
    """Corrélation de Spearman (sans scipy pour dépendance minimale)."""
    n = len(x)
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    mx, my = rx.mean(), ry.mean()
    sx, sy = rx.std(), ry.std()
    if sx < 1e-10 or sy < 1e-10:
        return 0.0
    return float(np.mean((rx - mx) * (ry - my)) / (sx * sy))


# ═══════════════════════════════════════════════════════════════════════════════
# EXPÉRIENCE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  EXPÉRIENCE FALSIFIABLE — Encodage harmonique φ vs sémantique")
    print("=" * 70)
    print()
    
    # Charger FastText
    print("[1] Chargement FastText...")
    model = charger_fasttext()
    print(f"    Vocabulaire : {len(model.wv)} mots, dim={model.wv.vector_size}")
    
    # Filtrer le dataset aux mots connus de FastText
    dataset = [(a, b, s) for a, b, s in DATASET if a in model.wv and b in model.wv]
    print(f"    Dataset     : {len(dataset)} paires exploitables (sur {len(DATASET)})")
    n_proches = sum(1 for _,_,s in dataset if s >= 0.9)
    n_apparentees = sum(1 for _,_,s in dataset if 0.4 < s < 0.9)
    n_eloignees = sum(1 for _,_,s in dataset if s <= 0.1)
    print(f"      - {n_proches} très proches (score ≥ 0.9)")
    print(f"      - {n_apparentees} apparentées (0.4-0.9)")
    print(f"      - {n_eloignees} sans rapport (score ≤ 0.1)")
    
    # Vocabulaire unique du dataset
    mots_uniques = sorted(set(a for a,_,_ in dataset) | set(b for _,b,_ in dataset))
    print(f"    Mots uniques : {len(mots_uniques)}")
    
    # Matrice d'embedding FastText pour ces mots
    emb_ft = np.array([model.wv[m] for m in mots_uniques], dtype=np.float64)
    mot_to_idx = {m: i for i, m in enumerate(mots_uniques)}
    
    # Gold standard
    humain = [s for _,_,s in dataset]
    
    print()
    print("[2] Calcul des 4 méthodes...")
    
    # ── Méthode 1 : Caractères ──
    scores_char = [similarite_caracteres(a, b) for a,b,_ in dataset]
    
    # ── Méthode 2 : FastText brut (référence) ──
    scores_ft = [similarite_fasttext(model, a, b) for a,b,_ in dataset]
    
    # ── Méthode 3 : Embedding φ 1D ──
    print("    Ordonnancement spectral 1D...")
    phases_1d = ordonnancement_spectral(emb_ft, k=1)
    emb_phi_1d = embedding_phi_1d(phases_1d.flatten(), dim=128)
    scores_phi_1d = [similarite_cosinus(emb_phi_1d, mot_to_idx[a], mot_to_idx[b])
                     for a,b,_ in dataset]
    
    # ── Méthode 4 : Embedding φ 16D ──
    print("    Ordonnancement spectral 16D...")
    phases_16d = ordonnancement_spectral(emb_ft, k=16)
    emb_phi_16d = embedding_phi_kd(phases_16d, dim=128)
    scores_phi_16d = [similarite_cosinus(emb_phi_16d, mot_to_idx[a], mot_to_idx[b])
                      for a,b,_ in dataset]
    
    # ── Méthode 5 : Embedding φ 64D (toutes les phases disponibles) ──
    k_max = min(64, len(mots_uniques) - 1)
    print(f"    Ordonnancement spectral {k_max}D...")
    phases_max = ordonnancement_spectral(emb_ft, k=k_max)
    emb_phi_max = embedding_phi_kd(phases_max, dim=128)
    scores_phi_max = [similarite_cosinus(emb_phi_max, mot_to_idx[a], mot_to_idx[b])
                      for a,b,_ in dataset]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RÉSULTATS
    # ═══════════════════════════════════════════════════════════════════════════
    print()
    print("=" * 70)
    print("  RÉSULTATS — Corrélation de Spearman avec gold standard humain")
    print("=" * 70)
    print()
    
    methodes = [
        ("Caractères (baseline naïve)", scores_char),
        ("Embedding φ 1D", scores_phi_1d),
        ("Embedding φ 16D", scores_phi_16d),
        (f"Embedding φ {k_max}D", scores_phi_max),
        ("FastText brut (upper-bound)", scores_ft),
    ]
    
    print(f"{'Méthode':<35} {'Spearman':>10} {'Proches':>10} {'Éloign.':>10} {'Écart':>8}")
    print("-" * 75)
    
    results = {}
    for nom, scores in methodes:
        rho = spearman_correlation(humain, scores)
        # Moyennes par catégorie
        moy_p = np.mean([scores[i] for i,(_,_,s) in enumerate(dataset) if s >= 0.9])
        moy_e = np.mean([scores[i] for i,(_,_,s) in enumerate(dataset) if s <= 0.1])
        ecart = moy_p - moy_e
        results[nom] = {'spearman': rho, 'proches': moy_p, 'eloignees': moy_e, 'ecart': ecart}
        bar = '█' * int(max(0, rho) * 30)
        print(f"{nom:<35} {rho:>10.3f} {moy_p:>10.3f} {moy_e:>10.3f} {ecart:>+8.3f}  {bar}")
    
    print()
    print("-" * 75)
    print("  INTERPRÉTATION :")
    print("-" * 75)
    
    rho_char = results["Caractères (baseline naïve)"]['spearman']
    rho_1d = results["Embedding φ 1D"]['spearman']
    rho_16d = results["Embedding φ 16D"]['spearman']
    rho_max = results[f"Embedding φ {k_max}D"]['spearman']
    rho_ft = results["FastText brut (upper-bound)"]['spearman']
    
    print(f"  φ 1D vs caractères     : {rho_1d:.3f} vs {rho_char:.3f} → "
          f"{'✅ meilleur' if rho_1d > rho_char else '❌ pas meilleur'}")
    print(f"  φ 16D vs caractères    : {rho_16d:.3f} vs {rho_char:.3f} → "
          f"{'✅ meilleur' if rho_16d > rho_char else '❌ pas meilleur'}")
    print(f"  φ {k_max}D vs caractères   : {rho_max:.3f} vs {rho_char:.3f} → "
          f"{'✅ meilleur' if rho_max > rho_char else '❌ pas meilleur'}")
    print(f"  FastText vs caractères : {rho_ft:.3f} vs {rho_char:.3f} → référence")
    print()
    
    ratio_16 = rho_16d / max(rho_ft, 0.01) if rho_ft > 0 else 0
    print(f"  φ 16D capture {ratio_16:.0%} du signal FastText")
    print(f"  word2vec publié obtient ~0.65 sur WordSim-353")
    
    # Sauvegarder
    out = {
        'date': time.strftime('%Y-%m-%d %H:%M'),
        'dataset_size': len(dataset),
        'vocab_size': len(mots_uniques),
        'fasttext_vocab': len(model.wv),
        'fasttext_dim': model.wv.vector_size,
        'results': {k: {kk: round(vv, 4) for kk, vv in v.items()} 
                    for k, v in results.items()},
        'word2vec_reference': 0.65,
    }
    with open('experience_validation_phi.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n  Rapport : experience_validation_phi.json")


if __name__ == '__main__':
    main()
