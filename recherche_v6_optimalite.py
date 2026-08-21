#!/usr/bin/env python3
"""
RECHERCHE v6 — LE TEST DÉCISIF
================================
Question : α = 1/φ ≈ 0.618 est-il l'ordre fractionnaire OPTIMAL ?

Si OUI → validation directe de la théorie harmonique.
Si NON → 1/φ n'est pas spécial, un autre ordre est meilleur.

Protocole :
  - Tester 17 ordres α ∈ {0.1, 0.2, ..., 0.9}
  - Pour chaque α : ABC spectral smoothing + φ embedding
  - Mesurer Spearman à plusieurs niveaux de bruit
  - Trouver l'α optimal et vérifier si c'est 1/φ

RIGUEUR :
  - 5 graines aléatoires différentes → moyenne + écart-type
  - Aucune triche possible : on scanne TOUS les α, pas juste 1/φ
"""
import sys, time, json, math
import numpy as np
sys.path.insert(0, 'engine')
from abc_kernel import abc_kernel_np, mittag_leffler, ALPHA, B_1_PHI, PHI

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

def cos_sim_mat(emb):
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    n = emb / norms
    return n @ n.T

def score_from_coords(coords, dataset, m2i, humain):
    norms = np.linalg.norm(coords, axis=1, keepdims=True) + 1e-10
    emb = coords / norms
    scores = [float(emb[m2i[a]] @ emb[m2i[b]]) for a,b,_ in dataset]
    return spearman(humain, scores)

# ═══ ABC SPECTRAL SMOOTHING (paramétré par α) ═══

def abc_spectral_smooth(emb_noise, alpha):
    """
    Lissage ABC dans l'espace des mots, avec ordre fractionnaire alpha.
    
    Trie les mots par ordre spectral, applique le noyau ABC(alpha).
    """
    N, D = emb_noise.shape
    
    S = np.maximum(cos_sim_mat(emb_noise), 0)
    deg = S.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    order = np.argsort(eigvecs[:, 1])
    inv_order = np.argsort(order)
    
    # Noyau ABC avec l'ordre alpha
    kernel_len = min(N, 50)
    kernel = abc_kernel_np(kernel_len, alpha=alpha)
    
    emb_ordered = emb_noise[order]
    emb_smoothed = np.zeros_like(emb_ordered)
    half = kernel_len // 2
    
    for i in range(N):
        total = np.zeros(D)
        weight_sum = 0.0
        for j in range(max(0, i-half), min(N, i+half+1)):
            dist = abs(i-j)
            w = kernel[dist] if dist < kernel_len else 0
            total += w * emb_ordered[j]
            weight_sum += w
        emb_smoothed[i] = total / max(weight_sum, 1e-10)
    
    return emb_smoothed[inv_order]

def phi_embedding(emb, k=16, dim=128):
    """Embedding φ 16D."""
    N = emb.shape[0]
    S = np.maximum(cos_sim_mat(emb), 0)
    deg = S.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    coords = eigvecs[:, 1:k+1]
    phases = np.zeros((N, k))
    for d in range(k):
        c = coords[:, d]
        phases[:, d] = TAU * (c - c.min()) / (c.max() - c.min() + 1e-10)
    ds = np.arange(dim, dtype=np.float64)
    emb_out = np.zeros((N, dim))
    for i in range(N):
        total = np.zeros(dim)
        for d in range(k):
            total += phases[i, d] * ds * PHI / dim * (PHI ** (-d))
        emb_out[i] = np.cos(total) * np.exp(-ds * (1.0/PHI) / dim)
    return emb_out

def main():
    print("="*75)
    print("  RECHERCHE v6 — LE TEST DÉCISIF")
    print("  α = 1/φ est-il l'ordre fractionnaire OPTIMAL ?")
    print("="*75)
    print()
    
    cache = np.load('glove_cache_136.npz', allow_pickle=True)
    mots = list(cache['mots'])
    emb_clean = cache['emb']
    m2i = {m: i for i, m in enumerate(mots)}
    
    dataset = [(a,b,s) for a,b,s in DATASET if a in m2i and b in m2i]
    humain = [s for _,_,s in dataset]
    norm_moy = np.mean(np.linalg.norm(emb_clean, axis=1))
    print(f"  {len(mots)} mots, {len(dataset)} paires, norme moy = {norm_moy:.2f}")
    print(f"  1/φ = {1.0/PHI:.6f}")
    print()
    
    # Ordres à tester (17 valeurs, équiréparties + 1/φ précis)
    alphas = [0.10, 0.20, 0.30, 0.40, 0.45, 0.50, 0.55, 0.58, 0.60, 
              1.0/PHI,  # 0.6180339887...
              0.64, 0.66, 0.70, 0.75, 0.80, 0.85, 0.90]
    
    # Niveaux de bruit
    bruits = [0.0, 0.3, 0.5, 1.0, 2.0]
    
    # 5 graines pour la moyenne
    seeds = [42, 123, 456, 789, 2024]
    
    print(f"  Ordres testés : {len(alphas)}")
    print(f"  Niveaux de bruit : {len(bruits)}")
    print(f"  Grainesses aléatoires : {len(seeds)}")
    print(f"  Total calculs : {len(alphas) * len(bruits) * len(seeds)}")
    print()
    
    # Structure de résultats : results[alpha][sigma] = [rho1, rho2, ...]
    results = {alpha: {sigma: [] for sigma in bruits} for alpha in alphas}
    
    t_total = time.time()
    
    for sigma_rel in bruits:
        sigma_abs = sigma_rel * norm_moy
        
        for seed in seeds:
            rng = np.random.RandomState(seed)
            emb_noise = emb_clean + rng.randn(*emb_clean.shape) * sigma_abs
            
            for alpha in alphas:
                # ABC smoothing + φ embedding
                emb_smoothed = abc_spectral_smooth(emb_noise, alpha=alpha)
                emb_phi = phi_embedding(emb_smoothed)
                rho = score_from_coords(emb_phi, dataset, m2i, humain)
                results[alpha][sigma_rel].append(rho)
        
        print(f"  σ={sigma_rel:.1f} fait ({(time.time()-t_total):.0f}s)")
    
    # ═══ ANALYSE ═══
    print()
    print("="*75)
    print("  RÉSULTATS — Spearman moyen (±écart-type) par α et σ")
    print("="*75)
    
    # Pour chaque niveau de bruit, trouver le meilleur α
    print()
    for sigma_rel in bruits:
        print(f"  ── σ = {sigma_rel:.1f} ──")
        print(f"  {'α':>8} │ {'Spearman':>10} │ {'± std':>8} │ Barre")
        print(f"  {'─'*8}─┼{'─'*12}┼{'─'*10}┼{'─'*30}")
        
        best_alpha = None
        best_rho = -999
        rhos_at_sigma = []
        
        for alpha in alphas:
            vals = results[alpha][sigma_rel]
            mean_rho = np.mean(vals)
            std_rho = np.std(vals)
            rhos_at_sigma.append((alpha, mean_rho, std_rho))
            
            if mean_rho > best_rho:
                best_rho = mean_rho
                best_alpha = alpha
            
            # Marquer 1/φ
            marker = ' ◄ 1/φ' if abs(alpha - 1.0/PHI) < 0.001 else ''
            bar = '█' * int(max(0, mean_rho) * 40)
            print(f"  {alpha:>8.4f} │ {mean_rho:>10.4f} │ {std_rho:>8.4f} │ {bar}{marker}")
        
        # Meilleur α
        print()
        is_phi = abs(best_alpha - 1.0/PHI) < 0.001
        emoji = '🎯' if is_phi else '⚠️'
        print(f"  {emoji} OPTIMAL : α = {best_alpha:.4f} (Spearman = {best_rho:.4f})")
        if is_phi:
            print(f"     → 1/φ EST L'OPTIMAL ! Validation de la théorie !")
        else:
            ecart = abs(best_alpha - 1.0/PHI)
            print(f"     → 1/φ = {1.0/PHI:.4f} n'est PAS optimal (écart = {ecart:.3f})")
        
        # Top-3
        rhos_sorted = sorted(rhos_at_sigma, key=lambda x: -x[1])
        print(f"     Top-3 : α={rhos_sorted[0][0]:.3f} ({rhos_sorted[0][1]:.3f}), "
              f"α={rhos_sorted[1][0]:.3f} ({rhos_sorted[1][1]:.3f}), "
              f"α={rhos_sorted[2][0]:.3f} ({rhos_sorted[2][1]:.3f})")
        print()
    
    # ═══ BILAN GLOBAL ═══
    print("="*75)
    print("  BILAN GLOBAL — α optimal à chaque niveau de bruit")
    print("="*75)
    print()
    print(f"  {'σ':>5} │ {'α optimal':>10} │ {'Spearman':>10} │ {'1/φ = ?':>10} │ Verdict")
    print(f"  {'─'*5}─┼{'─'*12}┼{'─'*12}┼{'─'*12}┼{'─'*20}")
    
    phi_wins = 0
    total_tests = 0
    
    for sigma_rel in bruits:
        best_alpha = max(alphas, key=lambda a: np.mean(results[a][sigma_rel]))
        best_rho = np.mean(results[best_alpha][sigma_rel])
        phi_rho = np.mean(results[1.0/PHI][sigma_rel])
        
        is_optimal = abs(best_alpha - 1.0/PHI) < 0.001
        total_tests += 1
        if is_optimal:
            phi_wins += 1
        
        verdict = '🎯 1/φ OPTIMAL' if is_optimal else f'α={best_alpha:.2f} meilleur'
        diff = phi_rho - best_rho
        print(f"  {sigma_rel:>5.1f} │ {best_alpha:>10.4f} │ {best_rho:>10.4f} │ "
              f"{phi_rho:>10.4f} │ {verdict}")
    
    print()
    print(f"  1/φ optimal dans {phi_wins}/{total_tests} cas")
    
    # Score global (moyenne sur tous les σ)
    print()
    print("  Score global (moyenne sur tous les σ) :")
    global_scores = []
    for alpha in alphas:
        global_mean = np.mean([np.mean(results[alpha][s]) for s in bruits])
        global_scores.append((alpha, global_mean))
        marker = ' ◄ 1/φ' if abs(alpha - 1.0/PHI) < 0.001 else ''
        bar = '█' * int(max(0, global_mean) * 40)
        print(f"    α = {alpha:.4f} : {global_mean:.4f} {bar}{marker}")
    
    global_scores.sort(key=lambda x: -x[1])
    best_global = global_scores[0]
    is_phi_global = abs(best_global[0] - 1.0/PHI) < 0.001
    
    print()
    if is_phi_global:
        print(f"  🎯🎯🎯 1/φ EST L'OPTIMAL GLOBAL !")
        print(f"     α = {best_global[0]:.6f} (1/φ = {1.0/PHI:.6f})")
        print(f"     Spearman moyen = {best_global[1]:.4f}")
        print(f"     → VALIDATION DIRECTE DE LA THÉORIE HARMONIQUE")
    else:
        print(f"  ❌ 1/φ n'est pas l'optimal global.")
        print(f"     Optimal : α = {best_global[0]:.4f} (Spearman {best_global[1]:.4f})")
        phi_global = [g for g in global_scores if abs(g[0] - 1.0/PHI) < 0.001]
        if phi_global:
            print(f"     1/φ     : α = {phi_global[0][0]:.4f} (Spearman {phi_global[0][1]:.4f})")
            ecart = phi_global[0][1] - best_global[1]
            print(f"     Écart   : {ecart:+.4f}")
    
    # Sauvegarder
    out = {}
    for alpha in alphas:
        out[f'alpha_{alpha:.4f}'] = {str(s): results[alpha][s] for s in bruits}
    out['metadata'] = {
        'alphas_tested': alphas,
        'bruits': bruits,
        'seeds': seeds,
        '1_over_phi': 1.0/PHI,
        'phi_wins': phi_wins,
        'total_tests': total_tests,
        'optimal_global': best_global[0],
        'is_phi_optimal': is_phi_global,
    }
    with open('recherche_v6_optimalite.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\n  Rapport : recherche_v6_optimalite.json")

if __name__ == '__main__':
    main()
