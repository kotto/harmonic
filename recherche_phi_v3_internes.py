#!/usr/bin/env python3
"""
RECHERCHE v3 : φ À L'INTÉRIEUR du calcul spectral
==================================================
Les expériences précédentes ont montré que la couche cos(φ×d) ajoutée APRÈS
SVD ne fait que dégrader. Cette fois, on intègre φ DANS la construction du
Laplacien / du noyau d'affinité, pour voir si la structure φ change
véritablement la géométrie de l'espace sémantique.

6 nouvelles hypothèses :
  H6  : Noyau d'affinité φ-pondéré (W_φ = W × exp(-d²/σ²) avec σ = φ)
  H7  : Sélection fibonnacienne des valeurs propres (indices 1,2,3,5,8,13...)
  H8  : Laplacien anisotrope φ (décroissance D^(-φ) au lieu de D^(-1/2))
  H9  : Noyau RBF φ-modulé (plusieurs σ = φ, φ², φ³ en parallèle)
  H10 : Affinage itératif φ (renforcer les frontières de clusters)
  H11 : Métrique φ-distance (distance cosinus × sin(φ × angle))

Si UNE de ces hypothèses dépasse SVD-16 brute (0.734), φ a un avantage réel.
"""
import sys, time, json, math
import numpy as np
import gensim.downloader as api

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1.0 / PHI
TAU = 2.0 * math.pi

DATASET = [
    ("king","queen",1.0),("man","woman",1.0),("boy","girl",1.0),
    ("father","mother",1.0),("brother","sister",1.0),
    ("cat","dog",1.0),("horse","cow",1.0),("lion","tiger",1.0),
    ("car","truck",1.0),("boat","ship",1.0),("plane","aircraft",1.0),
    ("happy","sad",1.0),("love","hate",1.0),("good","bad",1.0),
    ("big","small",1.0),("tall","short",1.0),("fast","slow",1.0),
    ("hot","cold",1.0),("light","dark",1.0),("strong","weak",1.0),
    ("day","night",1.0),("sun","moon",1.0),("summer","winter",1.0),
    ("spring","autumn",1.0),("life","death",1.0),("war","peace",1.0),
    ("rich","poor",1.0),("old","young",1.0),("clean","dirty",1.0),
    ("easy","hard",1.0),("safe","dangerous",1.0),
    ("doctor","nurse",1.0),("teacher","student",1.0),
    ("buy","sell",1.0),("win","lose",1.0),("open","close",1.0),
    ("house","city",0.5),("book","school",0.5),("bread","wheat",0.5),
    ("doctor","hospital",0.5),("judge","court",0.5),("painter","art",0.5),
    ("musician","instrument",0.5),("time","clock",0.5),("money","price",0.5),
    ("work","job",0.5),("mind","thought",0.5),("body","health",0.5),
    ("tree","forest",0.5),("sea","ship",0.5),("sky","cloud",0.5),
    ("computer","software",0.5),("phone","call",0.5),
    ("water","river",0.5),("fire","smoke",0.5),("king","crown",0.5),
    ("war","philosophy",0.0),("blood","silence",0.0),("death","joy",0.0),
    ("iron","freedom",0.0),("calculation","dream",0.0),("earth","spirit",0.0),
    ("war","poetry",0.0),("blood","logic",0.0),("shadow","math",0.0),
    ("wind","justice",0.0),("stone","music",0.0),("water","honor",0.0),
    ("fire","sadness",0.0),("gold","wisdom",0.0),("iron","beauty",0.0),
    ("king","tomato",0.0),("man","galaxy",0.0),("cat","mathematics",0.0),
    ("dog","philosophy",0.0),("sun","boredom",0.0),
]

def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1])

def cos_sim_mat(emb_ft):
    norms = np.linalg.norm(emb_ft, axis=1, keepdims=True) + 1e-10
    n = emb_ft / norms
    return n @ n.T

def project_and_score(coords, dataset, m2i, humain):
    """Projette coords [N,k] → embeddings normalisés → Spearman."""
    norms = np.linalg.norm(coords, axis=1, keepdims=True) + 1e-10
    emb = coords / norms
    scores = [float(emb[m2i[a]] @ emb[m2i[b]]) for a,b,_ in dataset]
    return spearman(humain, scores)

# ═══════════════════════════════════════════════════════════════════════════════
# HYPOTHÈSES — φ À L'INTÉRIEUR
# ═══════════════════════════════════════════════════════════════════════════════

def svd_reference(emb_ft, k=16):
    """SVD tronquée brute (référence)."""
    U, S, Vt = np.linalg.svd(emb_ft, full_matrices=False)
    return U[:, :k] * S[:k]

def H6_phi_kernel(emb_ft, k=16):
    """
    H6 : Noyau d'affinité φ-pondéré.
    
    Au lieu de W = cos(a,b), on utilise W_φ = cos(a,b) × exp(-d²/σ²)
    avec σ = φ (bande passante dorée). Les mots trop éloignés sont
    atténués, créant un graphe de voisinage plus local.
    """
    N = emb_ft.shape[0]
    S = cos_sim_mat(emb_ft)
    # Distance = arccos(similarité)
    D_angle = np.arccos(np.clip(S, -1, 1))
    # Noyau gaussien avec σ = φ radians (~92°)
    sigma = PHI
    W_phi = np.maximum(S, 0) * np.exp(-(D_angle**2) / (2 * sigma**2))
    W_phi = (W_phi + W_phi.T) / 2
    
    # Laplacien normalisé
    deg = W_phi.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ W_phi @ D_inv_sqrt
    
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1] * np.sqrt(np.maximum(eigvals[1:k+1], 0))

def H7_fibonacci_eigenvalues(emb_ft, k=16):
    """
    H7 : Sélection fibonnacienne des valeurs propres.
    
    Au lieu de prendre les k premières valeurs propres (1..k),
    on prend les indices de Fibonacci : 1,2,3,5,8,13,21,34...
    
    Hypothèse : les harmoniques naturelles du graphe sémantique
    suivent la séquence de Fibonacci (qui découle de φ).
    """
    S = np.maximum(cos_sim_mat(emb_ft), 0)
    N = S.shape[0]
    deg = S.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    
    eigvals, eigvecs = np.linalg.eigh(L)
    # Indices de Fibonacci (1-indexed)
    fib = [1, 2]
    while fib[-1] < N // 2 and len(fib) < k:
        fib.append(fib[-1] + fib[-2])
    fib = fib[:k]
    fib = [min(f, N-2) for f in fib]  # sécurité
    
    coords = np.zeros((N, k))
    for i, idx in enumerate(fib):
        coords[:, i] = eigvecs[:, idx] * np.sqrt(max(eigvals[idx], 0))
    return coords

def H8_anisotropic_phi(emb_ft, k=16):
    """
    H8 : Laplacien anisotrope φ.
    
    Au lieu de D^(-1/2) W D^(-1/2), on utilise D^(-φ/2) W^φ D^(-φ/2).
    L'exposant φ (≈1.618) rend la normalisation plus agressive sur
    les hubs (mots très connectés), réduisant leur influence dominante.
    """
    S = np.maximum(cos_sim_mat(emb_ft), 0)
    W_phi = np.power(np.maximum(S, 0), PHI)  # W^φ
    W_phi = (W_phi + W_phi.T) / 2
    
    deg = W_phi.sum(axis=1) + 1e-10
    # D^(-φ/2) au lieu de D^(-1/2)
    D_inv_phi = np.diag(np.power(deg, -PHI/2))
    L = np.eye(S.shape[0]) - D_inv_phi @ W_phi @ D_inv_phi
    
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1] * np.sqrt(np.maximum(eigvals[1:k+1], 0))

def H9_rbf_phi_multiband(emb_ft, k=16):
    """
    H9 : Noyau RBF multi-bandes φ.
    
    Combinaison de plusieurs noyaux gaussiens avec σ = φ, φ², φ³...
    Comme un filtre multi-échelles : capture les structures locales
    ET globales simultanément.
    """
    N = emb_ft.shape[0]
    S = cos_sim_mat(emb_ft)
    D_angle = np.arccos(np.clip(S, -1, 1))
    
    # Multi-bandes : σ ∈ {φ, φ², φ³, φ⁴}
    W_multi = np.zeros((N, N))
    for i, sigma in enumerate([PHI, PHI**2, PHI**3, PHI**4]):
        W_multi += np.exp(-(D_angle**2) / (2 * sigma**2)) / (i + 1)
    W_multi /= 4
    W_multi = (W_multi + W_multi.T) / 2
    
    deg = W_multi.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ W_multi @ D_inv_sqrt
    
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1] * np.sqrt(np.maximum(eigvals[1:k+1], 0))

def H10_iterative_phi_refinement(emb_ft, k=16, n_iter=3):
    """
    H10 : Affinage itératif φ.
    
    On fait la décomposition spectrale, puis on identifie les "frontières"
    entre clusters (mots avec interférence destructive) et on les renforce.
    Itératif : à chaque passe, la structure φ-affinée devient plus nette.
    """
    N = emb_ft.shape[0]
    S = np.maximum(cos_sim_mat(emb_ft), 0)
    
    for iteration in range(n_iter):
        deg = S.sum(axis=1) + 1e-10
        D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
        L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
        eigvals, eigvecs = np.linalg.eigh(L)
        coords = eigvecs[:, 1:k+1]
        
        # Mesurer la cohérence φ de chaque paire
        norms = np.linalg.norm(coords, axis=1, keepdims=True) + 1e-10
        emb_n = coords / norms
        sim_spectral = emb_n @ emb_n.T
        
        # Renforcer les paires cohérentes, affaiblir les frontières
        # Seuil φ : les paires au-dessus de 1/φ² sont des "clusters"
        threshold = 1.0 / (PHI**2)  # ≈ 0.382
        S = S * np.where(sim_spectral > threshold, PHI, 1.0/PHI)
        S = (S + S.T) / 2
    
    # Dernière décomposition
    deg = S.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1] * np.sqrt(np.maximum(eigvals[1:k+1], 0))

def H11_phi_metric_distance(emb_ft, k=16):
    """
    H11 : Métrique de distance φ.
    
    Au lieu de W = cos(a,b), on définit une métrique φ-dépendante :
      d_φ(a,b) = arccos(cos(a,b)) × (1 + sin(φ × arccos(cos(a,b))))
    
    La sinusoïde φ-module crée des "vallées" de similarité à des angles
    précis (multiples de π/φ), potentiellement alignés avec des
    structures sémantiques naturelles.
    """
    N = emb_ft.shape[0]
    S = cos_sim_mat(emb_ft)
    angle = np.arccos(np.clip(S, -1, 1))
    # Distance φ-modulée
    d_phi = angle * (1 + np.sin(PHI * angle))
    # Convertir en affinité
    W = np.exp(-d_phi**2 / (2 * 1.0))
    W = np.maximum(W - np.exp(-angle**2 / 2), 0)  # garder seulement le surplus φ
    W = (W + W.T) / 2
    
    deg = W.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ W @ D_inv_sqrt
    
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1] * np.sqrt(np.maximum(eigvals[1:k+1], 0))


def main():
    print("="*70)
    print("  RECHERCHE v3 : φ À L'INTÉRIEUR du calcul spectral")
    print("="*70)
    print()
    
    print("[1] Chargement GloVe-100...")
    t0 = time.time()
    model = api.load('glove-wiki-gigaword-100')
    print(f"    {time.time()-t0:.1f}s — {len(model)} mots")
    
    dataset = [(a,b,s) for a,b,s in DATASET if a in model and b in model]
    mots = sorted(set(a for a,_,_ in dataset) | set(b for _,b,_ in dataset))
    emb_ft = np.array([model[w] for w in mots], dtype=np.float64)
    m2i = {m:i for i,m in enumerate(mots)}
    humain = [s for _,_,s in dataset]
    print(f"    {len(dataset)} paires, {len(mots)} mots")
    
    # ── Références ──
    print()
    print("[2] Références...")
    coords_svd = svd_reference(emb_ft, k=16)
    rho_svd = project_and_score(coords_svd, dataset, m2i, humain)
    print(f"    SVD-16 brute   : {rho_svd:.3f}  ← CIBLE")
    
    s_glove = [float(model.similarity(a,b)) for a,b,_ in dataset]
    rho_glove = spearman(humain, s_glove)
    print(f"    GloVe-100 brut : {rho_glove:.3f}")
    
    # ── 6 HYPOTHÈSES ──
    print()
    print("="*70)
    print("  RÉSULTATS — 6 hypothèses φ-internes")
    print("="*70)
    print(f"{'Hypothèse':<50} {'Spearman':>10} {'vs SVD':>8} {'Verdict':>10}")
    print("-"*80)
    
    tests = [
        ("H6: noyau affinité φ (σ=φ)", H6_phi_kernel),
        ("H7: valeurs propres Fibonacci", H7_fibonacci_eigenvalues),
        ("H8: Laplacien anisotrope D^(-φ/2)", H8_anisotropic_phi),
        ("H9: RBF multi-bandes φ,φ²,φ³,φ⁴", H9_rbf_phi_multiband),
        ("H10: affinage itératif φ (3 passes)", H10_iterative_phi_refinement),
        ("H11: métrique distance φ-sinusoïdale", H11_phi_metric_distance),
    ]
    
    results = {'svd': rho_svd, 'glove': rho_glove}
    winner = None
    
    for name, func in tests:
        try:
            t_h = time.time()
            coords = func(emb_ft, k=16)
            rho = project_and_score(coords, dataset, m2i, humain)
            dt = time.time() - t_h
            diff = rho - rho_svd
            verdict = '✅ GAGNE' if diff > 0.005 else ('≈ égal' if abs(diff) <= 0.005 else '❌ perd')
            if diff > 0.005 and (winner is None or rho > winner[1]):
                winner = (name, rho, diff)
            bar = '█' * int(max(0, rho) * 40)
            print(f"{name:<50} {rho:>10.3f} {diff:>+8.3f} {verdict:>10}  {dt:.1f}s  {bar}")
            results[name] = rho
        except Exception as e:
            print(f"{name:<50} ERREUR: {e}")
            results[name] = None
    
    # ── BILAN ──
    print()
    print("="*70)
    print("  BILAN")
    print("="*70)
    if winner:
        print(f"  🎯 GAGNANT : {winner[0]}")
        print(f"     Spearman = {winner[1]:.3f} (vs SVD {rho_svd:.3f}, +{winner[2]:.3f})")
        print(f"     → φ a un avantage RÉEL via cette méthode.")
        # Comparer à GloVe
        if winner[1] > rho_glove:
            print(f"     → Et DÉPASSE GloVe brut ({rho_glove:.3f}) !")
    else:
        best = max((v for k, v in results.items() if k not in ('svd','glove') and v is not None), default=0)
        print(f"  ❌ Aucune hypothèse ne dépasse SVD ({rho_svd:.3f}).")
        print(f"     Meilleur : {best:.3f} (écart {best-rho_svd:+.3f})")
    
    with open('recherche_phi_v3_internes.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Rapport : recherche_phi_v3_internes.json")

if __name__ == '__main__':
    main()
