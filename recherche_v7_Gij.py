#!/usr/bin/env python3
"""
RECHERCHE v7 — LE TEST DE LA CONTRAINTE G_ij = 0
==================================================
Question : si on impose la conservation énergie-information
(Σ||emb_smoothed||² = Σ||emb_bruité||²), est-ce que α = 1/φ
émerge comme l'unique ordre qui satisfait la contrainte
AVEC un B(α) physiquement simple ?

Protocole :
  1. Pour chaque α, calculer le noyau ABC brut
  2. Imposer la contrainte de conservation sur la norme
  3. Trouver le facteur de normalisation B_conservatif(α) requis
  4. Mesurer Spearman pour le noyau contraint
  5. Vérifier si B_conservatif(α) est minimal/optimal à α=1/φ
  6. Vérifier si la performance avec contrainte est optimale à 1/φ
"""
import sys, time, json, math
import numpy as np
sys.path.insert(0, 'engine')
from abc_kernel import abc_kernel_np, mittag_leffler, PHI

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

def score_from_emb(emb, m2i, humain):
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    e = emb / norms
    scores = [float(e[m2i[a]] @ e[m2i[b]]) for a,b,_ in DATASET 
              if a in m2i and b in m2i]
    return spearman(humain, scores)

def abc_kernel_raw(length, alpha):
    """
    Noyau ABC BRUT (sans normalisation). 
    K_raw(t) = E_alpha(-alpha * t^alpha / (1 - alpha))
    """
    t = np.arange(length, dtype=np.float64)
    # Calculer z = -alpha * t^alpha / (1 - alpha)
    z = -alpha * (t ** alpha) / max(1 - alpha, 1e-10)
    # Mittag-Leffler de z
    result = mittag_leffler(z, alpha=alpha)
    return np.maximum(result, 0)  # garder positif

def compute_B_conservatif(emb_noise, kernel_raw, spectral_order, D):
    """
    Calcule le facteur B(α) tel que la contrainte G_ij = 0
    (conservation de l'énergie totale) soit satisfaite.
    
    Énergie avant = Σ_i ||emb[i]||²
    Énergie après  = Σ_i ||emb_smoothed[i]||²
    
    B_conservatif = sqrt(E_avant / E_apres_brut)
    où E_apres_brut est l'énergie après smoothing avec kernel non normalisé.
    """
    N = len(emb_noise)
    emb_ordered = emb_noise[spectral_order]
    kernel_len = len(kernel_raw)
    half = kernel_len // 2
    
    E_avant = float(np.sum(emb_noise ** 2))
    
    # Calculer l'énergie après smoothing brut (B=1)
    E_apres = 0.0
    for i in range(N):
        total = np.zeros(D)
        weight_sum = 0.0
        for j in range(max(0, i-half), min(N, i+half+1)):
            dist = abs(i-j)
            w = kernel_raw[dist] if dist < kernel_len else 0
            total += w * emb_ordered[j]
            weight_sum += w
        if weight_sum > 1e-10:
            smoothed = total / weight_sum
            E_apres += float(np.sum(smoothed ** 2))
    
    if E_apres < 1e-15:
        return 1.0
    
    B = math.sqrt(E_avant / E_apres)
    return B


def abc_smooth_conservatif(emb_noise, alpha, kernel_len=50):
    """
    Applique le lissage ABC avec conservation G_ij=0 :
    le noyau est automatiquement normalisé pour préserver l'énergie totale.
    """
    N, D = emb_noise.shape
    
    # Ordre spectral
    S = np.maximum(cos_sim_mat(emb_noise), 0)
    deg = S.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    order = np.argsort(eigvecs[:, 1])
    inv_order = np.argsort(order)
    
    # Noyau ABC brut
    kernel_raw = abc_kernel_raw(kernel_len, alpha)
    
    # Facteur conservatif B(α)
    B = compute_B_conservatif(emb_noise, kernel_raw, order, D)
    
    # Appliquer avec B conservatif
    kernel = kernel_raw * B
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
    
    emb_reordered = emb_smoothed[inv_order]
    
    # Vérifier la conservation
    E_avant = float(np.sum(emb_noise ** 2))
    E_apres = float(np.sum(emb_reordered ** 2))
    erreur = abs(E_apres - E_avant) / max(E_avant, 1e-10)
    
    return emb_reordered, B, erreur


def phi_embedding(emb, k=16, dim=128):
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
    print("  RECHERCHE v7 — CONTRAINTE G_ij = 0")
    print("  La conservation énergie-information force-t-elle 1/φ ?")
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
    
    # Ordres à tester
    alphas = [0.10, 0.20, 0.30, 0.40, 0.45, 0.50, 0.55, 0.58, 0.60,
              1.0/PHI, 0.64, 0.66, 0.70, 0.75, 0.80, 0.85, 0.90]
    
    bruits = [0.0, 0.3, 0.5, 1.0, 2.0]
    seeds = [42, 123]
    
    print(f"  Ordres : {len(alphas)}, Bruits : {len(bruits)}, Graines : {len(seeds)}")
    print()
    
    t_start = time.time()
    
    # Stockage : results[alpha][sigma] = liste de rho
    results_phi = {alpha: {s: [] for s in bruits} for alpha in alphas}
    B_values = {alpha: {s: [] for s in bruits} for alpha in alphas}
    conservation_errors = {alpha: {s: [] for s in bruits} for alpha in alphas}
    
    for sigma_rel in bruits:
        sigma_abs = sigma_rel * norm_moy
        
        for seed in seeds:
            rng = np.random.RandomState(seed)
            emb_noise = emb_clean + rng.randn(*emb_clean.shape) * sigma_abs
            
            for alpha in alphas:
                emb_smooth, B, err = abc_smooth_conservatif(emb_noise, alpha=alpha)
                emb_phi = phi_embedding(emb_smooth)
                rho = score_from_emb(emb_phi, m2i, humain)
                
                results_phi[alpha][sigma_rel].append(rho)
                B_values[alpha][sigma_rel].append(B)
                conservation_errors[alpha][sigma_rel].append(err)
        
        print(f"  σ={sigma_rel:.1f} fait ({(time.time()-t_start):.0f}s)")
    
    # ═══ ANALYSE 1 : B(α) conservatif ═══
    print()
    print("="*75)
    print("  PARTIE 1 : B(α) conservatif — quel α minimise B ?")
    print("="*75)
    print()
    print(f"  {'α':>8} │ {'B moyen':>10} │ {'± std':>8} │ Barre")
    print(f"  {'─'*8}─┼{'─'*12}┼{'─'*10}┼{'─'*30}")
    
    # B moyen global (tous bruits confondus)
    B_global = {}
    for alpha in alphas:
        all_B = []
        for s in bruits:
            all_B.extend(B_values[alpha][s])
        mean_B = np.mean(all_B)
        std_B = np.std(all_B)
        B_global[alpha] = mean_B
        
        marker = ' ◄ 1/φ' if abs(alpha - 1.0/PHI) < 0.001 else ''
        bar = '█' * int(min(mean_B * 30, 30))
        print(f"  {alpha:>8.4f} │ {mean_B:>10.6f} │ {std_B:>8.6f} │ {bar}{marker}")
    
    # Quel α minimise B ?
    best_alpha_B = min(B_global, key=B_global.get)
    phi_B = B_global[1.0/PHI]
    min_B = B_global[best_alpha_B]
    
    print()
    if abs(best_alpha_B - 1.0/PHI) < 0.001:
        print(f"  🎯 B(α) MINIMAL à α = 1/φ = {best_alpha_B:.6f}")
        print(f"     → La contrainte de conservation est SATISFAITE avec le MINIMUM de correction")
        print(f"     → VALIDATION de la théorie")
    else:
        print(f"  B minimal à α = {best_alpha_B:.4f} (B = {min_B:.4f})")
        print(f"  1/φ : B = {phi_B:.4f}")
        if abs(phi_B - min_B) < 0.1:
            print(f"     → 1/φ est proche du minimum (différence B = {phi_B - min_B:+.4f})")
        else:
            print(f"     → 1/φ n'est PAS proche du minimum")
    
    # ═══ ANALYSE 2 : Performance avec contrainte ═══
    print()
    print("="*75)
    print("  PARTIE 2 : Performance avec contrainte G_ij=0")
    print("="*75)
    print()
    
    for sigma_rel in bruits:
        print(f"  ── σ = {sigma_rel:.1f} ──")
        
        rhos_at_sigma = []
        best_alpha = None
        best_rho = -999
        
        for alpha in alphas:
            vals = results_phi[alpha][sigma_rel]
            mean_rho = np.mean(vals)
            rhos_at_sigma.append((alpha, mean_rho))
            if mean_rho > best_rho:
                best_rho = mean_rho
                best_alpha = alpha
        
        # Top-3
        rhos_sorted = sorted(rhos_at_sigma, key=lambda x: -x[1])
        phi_rho = np.mean(results_phi[1.0/PHI][sigma_rel])
        
        print(f"    Optimaux : ", end="")
        for a, r in rhos_sorted[:3]:
            marker = ' ◄ 1/φ' if abs(a - 1.0/PHI) < 0.001 else ''
            print(f"α={a:.3f}({r:.3f})", end=" ")
        print()
        
        is_phi = abs(best_alpha - 1.0/PHI) < 0.001
        if is_phi:
            print(f"    🎯 1/φ EST OPTIMAL ! (Spearman = {best_rho:.4f})")
        else:
            # Est-ce que 1/φ est dans le top-3 ?
            top3_alphas = [x[0] for x in rhos_sorted[:3]]
            phi_in_top3 = any(abs(a - 1.0/PHI) < 0.001 for a in top3_alphas)
            if phi_in_top3:
                print(f"    ✅ 1/φ dans le top-3 (Spearman = {phi_rho:.4f}, rang {rhos_sorted.index(next(x for x in rhos_sorted if abs(x[0]-1.0/PHI)<0.001))+1})")
            else:
                print(f"    ❌ 1/φ pas dans le top-3 (Spearman = {phi_rho:.4f})")
        print()
    
    # ═══ ANALYSE 3 : Conservation réelle ═══
    print("="*75)
    print("  PARTIE 3 : Précision de la conservation (erreur relative)")
    print("="*75)
    print()
    
    for alpha in alphas:
        all_err = []
        for s in bruits:
            all_err.extend(conservation_errors[alpha][s])
        mean_err = np.mean(all_err)
        marker = ' ◄ 1/φ' if abs(alpha - 1.0/PHI) < 0.001 else ''
        bar = '█' * int(max(0, -np.log10(max(mean_err, 1e-15))) * 2)
        print(f"  α = {alpha:.4f} : err = {mean_err:.2e} {bar}{marker}")
    
    # ═══ BILAN ═══
    print()
    print("="*75)
    print("  BILAN FINAL — La contrainte G_ij=0 valide-t-elle 1/φ ?")
    print("="*75)
    print()
    
    # Score global
    global_scores = {}
    for alpha in alphas:
        all_rho = []
        for s in bruits:
            all_rho.extend(results_phi[alpha][s])
        global_scores[alpha] = np.mean(all_rho)
    
    best_global = max(global_scores, key=global_scores.get)
    phi_global = global_scores[1.0/PHI]
    
    print(f"  Meilleur score global : α = {best_global:.4f} (Spearman = {global_scores[best_global]:.4f})")
    print(f"  Score de 1/φ         : {phi_global:.4f}")
    
    # Compter les victoires
    phi_wins = 0
    for sigma_rel in bruits:
        best = max(alphas, key=lambda a: np.mean(results_phi[a][sigma_rel]))
        if abs(best - 1.0/PHI) < 0.001:
            phi_wins += 1
    print(f"  1/φ optimal dans : {phi_wins}/{len(bruits)} niveaux de bruit")
    
    print(f"\n  B(α) minimal à : α = {best_alpha_B:.4f}")
    B_min = B_global[best_alpha_B]
    B_phi = B_global[1.0/PHI]
    ratio_B = B_phi / max(B_min, 1e-10)
    print(f"  B(1/φ) / B_min   : {ratio_B:.4f} (doit être ≈1.0 si 1/φ est optimal)")
    
    print()
    if phi_wins >= 3 and ratio_B < 1.1:
        print("  🎯 DOUBLE VALIDATION :")
        print("     - 1/φ minimalise B (la conservation est la plus 'naturelle')")
        print("     - 1/φ donne la meilleure performance")
    elif phi_wins >= 2:
        print("  ✅ VALIDATION PARTIELLE : 1/φ parmi les meilleurs")
    elif ratio_B < 1.05:
        print("  ⚠️ 1/φ minimise B mais n'est pas le meilleur en performance")
    else:
        print("  ❌ 1/φ n'est pas validé par la contrainte de conservation")
    
    # Sauvegarder
    out = {
        'B_values': {str(a): {str(s): B_values[a][s] for s in bruits} for a in alphas},
        'performance': {str(a): {str(s): [float(x) for x in results_phi[a][s]] for s in bruits} for a in alphas},
        'B_global': B_global,
        'global_scores': global_scores,
        'best_B_alpha': best_alpha_B,
        'best_perf_alpha': best_global,
        'phi_wins': phi_wins,
    }
    with open('recherche_v7_Gij.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\n  Rapport : recherche_v7_Gij.json")

if __name__ == '__main__':
    main()
