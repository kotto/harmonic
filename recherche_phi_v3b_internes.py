#!/usr/bin/env python3
"""
RECHERCHE v3b : φ À L'INTÉRIEUR — version avec cache local
===========================================================
Évite de recharger GloVe (MemoryError). Sauve les embeddings des
136 mots du dataset dans un .npz, puis recharge instantanément.
"""
import sys, time, json, math
import numpy as np

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

CACHE_PATH = "glove_cache_136.npz"
GLOVE_SIM_CACHE = "glove_sims_136.npy"

def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1])

def cos_sim_mat(emb_ft):
    norms = np.linalg.norm(emb_ft, axis=1, keepdims=True) + 1e-10
    n = emb_ft / norms
    return n @ n.T

def project_and_score(coords, dataset, m2i, humain):
    norms = np.linalg.norm(coords, axis=1, keepdims=True) + 1e-10
    emb = coords / norms
    scores = [float(emb[m2i[a]] @ emb[m2i[b]]) for a,b,_ in dataset]
    return spearman(humain, scores)

def load_or_cache():
    """Charge GloVe ou utilise le cache local."""
    mots = sorted(set(a for a,_,_ in DATASET) | set(b for _,b,_ in DATASET))
    
    cache = np.load(CACHE_PATH, allow_pickle=True)
    mots_cached = list(cache['mots'])
    emb_ft = cache['emb']
    
    # similarités GloVe brute (cache séparé)
    glove_sim = np.load(GLOVE_SIM_CACHE)
    m2i = {m: i for i, m in enumerate(mots_cached)}
    
    # Filtrer le dataset aux mots disponibles
    dataset = [(a, b, s) for a, b, s in DATASET if a in m2i and b in m2i]
    humain = [s for _, _, s in dataset]
    s_glove = [float(glove_sim[m2i[a], m2i[b]]) for a, b, _ in dataset]
    
    return mots_cached, emb_ft, m2i, dataset, humain, s_glove


# ═══ HYPOTHÈSES ═══

def svd_reference(emb_ft, k=16):
    U, S, Vt = np.linalg.svd(emb_ft, full_matrices=False)
    return U[:, :k] * S[:k]

def H6_phi_kernel(emb_ft, k=16):
    N = emb_ft.shape[0]
    S = cos_sim_mat(emb_ft)
    D_angle = np.arccos(np.clip(S, -1, 1))
    sigma = PHI
    W_phi = np.maximum(S, 0) * np.exp(-(D_angle**2) / (2 * sigma**2))
    W_phi = (W_phi + W_phi.T) / 2
    deg = W_phi.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ W_phi @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1] * np.sqrt(np.maximum(eigvals[1:k+1], 0))

def H7_fibonacci_eigenvalues(emb_ft, k=16):
    S = np.maximum(cos_sim_mat(emb_ft), 0)
    N = S.shape[0]
    deg = S.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    fib = [1, 2]
    while fib[-1] < N // 2 and len(fib) < k:
        fib.append(fib[-1] + fib[-2])
    fib = fib[:k]
    fib = [min(f, N-2) for f in fib]
    coords = np.zeros((N, k))
    for i, idx in enumerate(fib):
        coords[:, i] = eigvecs[:, idx] * np.sqrt(max(eigvals[idx], 0))
    return coords

def H8_anisotropic_phi(emb_ft, k=16):
    S = np.maximum(cos_sim_mat(emb_ft), 0)
    W_phi = np.power(np.maximum(S, 0), PHI)
    W_phi = (W_phi + W_phi.T) / 2
    deg = W_phi.sum(axis=1) + 1e-10
    D_inv_phi = np.diag(np.power(deg, -PHI/2))
    L = np.eye(S.shape[0]) - D_inv_phi @ W_phi @ D_inv_phi
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1] * np.sqrt(np.maximum(eigvals[1:k+1], 0))

def H9_rbf_phi_multiband(emb_ft, k=16):
    N = emb_ft.shape[0]
    S = cos_sim_mat(emb_ft)
    D_angle = np.arccos(np.clip(S, -1, 1))
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
    N = emb_ft.shape[0]
    S = np.maximum(cos_sim_mat(emb_ft), 0)
    for iteration in range(n_iter):
        deg = S.sum(axis=1) + 1e-10
        D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
        L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
        eigvals, eigvecs = np.linalg.eigh(L)
        coords = eigvecs[:, 1:k+1]
        norms = np.linalg.norm(coords, axis=1, keepdims=True) + 1e-10
        emb_n = coords / norms
        sim_spectral = emb_n @ emb_n.T
        threshold = 1.0 / (PHI**2)
        S = S * np.where(sim_spectral > threshold, PHI, 1.0/PHI)
        S = (S + S.T) / 2
    deg = S.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1] * np.sqrt(np.maximum(eigvals[1:k+1], 0))

def H11_phi_metric_distance(emb_ft, k=16):
    N = emb_ft.shape[0]
    S = cos_sim_mat(emb_ft)
    angle = np.arccos(np.clip(S, -1, 1))
    d_phi = angle * (1 + np.sin(PHI * angle))
    W = np.exp(-d_phi**2 / 2)
    baseline = np.exp(-angle**2 / 2)
    W = np.maximum(W - baseline, 0)
    W = (W + W.T) / 2
    deg = W.sum(axis=1) + 1e-10
    if (deg < 1e-8).any():
        deg = deg + 1e-6
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ W @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1] * np.sqrt(np.maximum(eigvals[1:k+1], 0))


def main():
    print("="*70)
    print("  RECHERCHE v3b : φ À L'INTÉRIEUR (cache local)")
    print("="*70)
    print()
    
    mots, emb_ft, m2i, dataset, humain, s_glove = load_or_cache()
    print(f"  {len(dataset)} paires, {len(mots)} mots (depuis cache)")
    
    # Références
    coords_svd = svd_reference(emb_ft, k=16)
    rho_svd = project_and_score(coords_svd, dataset, m2i, humain)
    rho_glove = spearman(humain, s_glove)
    print(f"  SVD-16   : {rho_svd:.3f}  ← CIBLE")
    print(f"  GloVe    : {rho_glove:.3f}")
    print()
    
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
    
    print()
    print("="*70)
    if winner:
        print(f"  🎯 GAGNANT : {winner[0]}")
        print(f"     Spearman = {winner[1]:.3f} (vs SVD {rho_svd:.3f}, +{winner[2]:.3f})")
        if winner[1] > rho_glove:
            print(f"     → DÉPASSE GloVe brut ({rho_glove:.3f}) !")
    else:
        best = max((v for k, v in results.items() if k not in ('svd','glove') and v is not None), default=0)
        print(f"  ❌ Aucune hypothèse ne dépasse SVD ({rho_svd:.3f}).")
        print(f"     Meilleur : {best:.3f} (écart {best-rho_svd:+.3f})")
    
    with open('recherche_phi_v3b.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    main()
