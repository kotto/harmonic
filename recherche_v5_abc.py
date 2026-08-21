#!/usr/bin/env python3
"""
RECHERCHE v5 : DÉRIVÉE FRACTIONNAIRE ABC POUR STABILISER φ
==========================================================
Hypothèse : appliquer le noyau ABC (ordre α=1/φ) comme opérateur de
régularisation AVANT la décomposition spectrale devrait :
  1. Améliorer la robustesse au bruit de φ
  2. Stabiliser le comportement chaotique à bruit fort
  3. Étendre la zone où φ > SVD

Le noyau ABC (Mittag-Leffler, décroissance en loi de puissance) agit
comme un lisseur non-local qui préserve mieux la structure que les
noyaux gaussiens (décroissance exponentielle).

Protocole :
  - Appliquer ABC aux embeddings bruités (filtrage spectral 1D)
  - Comparer : SVD brute vs SVD+ABC vs φ vs φ+ABC
  - Mesurer sur la courbe de bruit complète (σ=0 à 3.0)
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

def score(coords, dataset, m2i, humain):
    norms = np.linalg.norm(coords, axis=1, keepdims=True) + 1e-10
    emb = coords / norms
    scores = [float(emb[m2i[a]] @ emb[m2i[b]]) for a,b,_ in dataset]
    return spearman(humain, scores)

# ═══ OPÉRATEUR ABC COMME RÉGULARISATEUR ═══

def abc_denoise(emb_noise, strength=1.0):
    """
    Applique le noyau ABC comme filtre de débruitage.
    
    Le noyau ABC agit dans l'espace spectral : on fait la FFT de chaque
    dimension, on multiplie par le noyau ABC (passe-bas), puis IFFT.
    
    Le noyau ABC a une décroissance en loi de puissance t^(-α-1) qui
    préserve mieux les structures à longue portée qu'un gaussien.
    """
    N, D = emb_noise.shape
    
    # Noyau ABC 1D de longueur D (une dimension de l'embedding)
    kernel = abc_kernel_np(D, alpha=ALPHA)  # [D], somme=1
    kernel = kernel * strength
    
    # Appliquer le filtre ABC dans l'espace spectral de chaque mot
    # FFT le long des dimensions (pas des mots)
    emb_filtered = np.zeros_like(emb_noise)
    for i in range(N):
        # FFT 1D de l'embedding du mot i
        fft_emb = np.fft.fft(emb_noise[i])
        # Masque ABC : les basses fréquences passent, les hautes sont atténuées
        freqs = np.fft.fftfreq(D)
        freq_order = np.argsort(np.abs(freqs))  # ordre croissant de fréquence
        mask = np.zeros(D)
        mask[freq_order] = kernel[:D] * D  # appliquer le noyau ABC
        emb_filtered[i] = np.real(np.fft.ifft(fft_emb * mask))
    
    return emb_filtered

def abc_spectral_smooth(emb_noise, alpha=ALPHA):
    """
    Lissage ABC dans l'espace des MOTS (pas des dimensions).
    
    Trie les mots par similarité, applique le noyau ABC le long
    de cet ordre. Le noyau non-local mélange les mots proches.
    """
    N, D = emb_noise.shape
    
    # Ordre spectral des mots (tri par premier vecteur propre)
    S = np.maximum(cos_sim_mat(emb_noise), 0)
    deg = S.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    order = np.argsort(eigvecs[:, 1])
    inv_order = np.argsort(order)
    
    # Noyau ABC
    kernel = abc_kernel_np(min(N, 50), alpha=alpha)
    
    # Appliquer le noyau le long de l'ordre spectral
    emb_ordered = emb_noise[order]
    emb_smoothed = np.zeros_like(emb_ordered)
    half = len(kernel) // 2
    
    for i in range(N):
        total = np.zeros(D)
        weight_sum = 0
        for j in range(max(0, i-half), min(N, i+half+1)):
            w = kernel[abs(i-j)] if abs(i-j) < len(kernel) else 0
            total += w * emb_ordered[j]
            weight_sum += w
        emb_smoothed[i] = total / max(weight_sum, 1e-10)
    
    return emb_smoothed[inv_order]

# ═══ MÉTHODES À COMPARER ═══

def svd16(emb):
    U, S, Vt = np.linalg.svd(emb, full_matrices=False)
    return U[:, :16] * S[:16]

def phi16d(emb, dim=128):
    N = emb.shape[0]
    S = np.maximum(cos_sim_mat(emb), 0)
    deg = S.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    coords = eigvecs[:, 1:17]
    phases = np.zeros((N, 16))
    for d in range(16):
        c = coords[:, d]
        phases[:, d] = TAU * (c - c.min()) / (c.max() - c.min() + 1e-10)
    ds = np.arange(dim, dtype=np.float64)
    emb_out = np.zeros((N, dim))
    for i in range(N):
        total = np.zeros(dim)
        for d in range(16):
            total += phases[i, d] * ds * PHI / dim * (PHI ** (-d))
        emb_out[i] = np.cos(total) * np.exp(-ds * (1.0/PHI) / dim)
    return emb_out

def main():
    print("="*70)
    print("  RECHERCHE v5 : ABC + φ sous bruit")
    print("  La dérivée fractionnaire stabilise-t-elle φ ?")
    print("="*70)
    print()
    
    cache = np.load('glove_cache_136.npz', allow_pickle=True)
    mots = list(cache['mots'])
    emb_clean = cache['emb']
    m2i = {m: i for i, m in enumerate(mots)}
    
    dataset = [(a,b,s) for a,b,s in DATASET if a in m2i and b in m2i]
    humain = [s for _,_,s in dataset]
    norm_moy = np.mean(np.linalg.norm(emb_clean, axis=1))
    print(f"  {len(mots)} mots, dataset {len(dataset)} paires")
    print(f"  α = 1/φ = {ALPHA:.6f}")
    print(f"  B(α) = {B_1_PHI:.6f}")
    
    # Vérifier le noyau ABC
    kernel = abc_kernel_np(20, alpha=ALPHA)
    print(f"  Noyau ABC (20 pts) : somme={kernel.sum():.4f}, décroissance exponentielle")
    print(f"    K[0]={kernel[0]:.4f}, K[5]={kernel[5]:.4f}, K[10]={kernel[10]:.4f}, K[15]={kernel[15]:.6f}")
    print()
    
    bruits = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]
    
    methodes = ['SVD-16', 'SVD+ABC', 'φ 16D', 'φ+ABC', 'ABC-lissé']
    
    print(f"{'σ':>5} │ {'SVD-16':>7} │ {'SVD+ABC':>7} │ {'φ 16D':>7} │ {'φ+ABC':>7} │ {'ABC-lis':>7} │ Gagnant")
    print("─"*72)
    
    all_results = {}
    
    for sigma_rel in bruits:
        sigma_abs = sigma_rel * norm_moy
        rng = np.random.RandomState(42)
        emb_noise = emb_clean + rng.randn(*emb_clean.shape) * sigma_abs
        
        # ABC denoising
        emb_abc = abc_denoise(emb_noise, strength=1.0)
        
        # ABC spectral smoothing
        emb_abc_sp = abc_spectral_smooth(emb_noise)
        
        row = {}
        row['SVD-16'] = score(svd16(emb_noise), dataset, m2i, humain)
        row['SVD+ABC'] = score(svd16(emb_abc), dataset, m2i, humain)
        row['φ 16D'] = score(phi16d(emb_noise), dataset, m2i, humain)
        row['φ+ABC'] = score(phi16d(emb_abc), dataset, m2i, humain)
        row['ABC-lissé'] = score(phi16d(emb_abc_sp), dataset, m2i, humain)
        
        all_results[sigma_rel] = row
        
        best = max(row, key=row.get)
        print(f"{sigma_rel:>5.1f} │ {row['SVD-16']:>7.3f} │ {row['SVD+ABC']:>7.3f} │ "
              f"{row['φ 16D']:>7.3f} │ {row['φ+ABC']:>7.3f} │ {row['ABC-lissé']:>7.3f} │ {best}")
    
    # ── ANALYSE ──
    print()
    print("="*70)
    print("  ANALYSE")
    print("="*70)
    
    # ABC aide-t-il SVD ?
    print()
    print("  1. ABC aide-t-il SVD ?")
    for sigma in [0.0, 0.3, 0.5, 1.0, 2.0]:
        gain = all_results[sigma]['SVD+ABC'] - all_results[sigma]['SVD-16']
        print(f"     σ={sigma:.1f} : SVD={all_results[sigma]['SVD-16']:.3f} → "
              f"SVD+ABC={all_results[sigma]['SVD+ABC']:.3f} ({gain:+.3f})")
    
    # ABC aide-t-il φ ?
    print()
    print("  2. ABC aide-t-il φ ?")
    for sigma in [0.0, 0.3, 0.5, 1.0, 2.0]:
        gain = all_results[sigma]['φ+ABC'] - all_results[sigma]['φ 16D']
        print(f"     σ={sigma:.1f} : φ={all_results[sigma]['φ 16D']:.3f} → "
              f"φ+ABC={all_results[sigma]['φ+ABC']:.3f} ({gain:+.3f})")
    
    # ABC-lissé (spectral) ?
    print()
    print("  3. ABC-lissé spectral ?")
    for sigma in [0.0, 0.3, 0.5, 1.0, 2.0]:
        gain = all_results[sigma]['ABC-lissé'] - all_results[sigma]['φ 16D']
        print(f"     σ={sigma:.1f} : φ={all_results[sigma]['φ 16D']:.3f} → "
              f"ABC-lissé={all_results[sigma]['ABC-lissé']:.3f} ({gain:+.3f})")
    
    # φ+ABC dépasse-t-il SVD ?
    print()
    print("  4. φ+ABC dépasse-t-il SVD brute ?")
    wins = 0
    for sigma in bruits:
        if all_results[sigma]['φ+ABC'] > all_results[sigma]['SVD-16']:
            wins += 1
            print(f"     σ={sigma:.1f} : φ+ABC ({all_results[sigma]['φ+ABC']:.3f}) "
                  f"> SVD ({all_results[sigma]['SVD-16']:.3f}) ✅")
    if wins == 0:
        print("     ❌ Jamais")
    
    # Stabilité
    print()
    print("  5. STABILITÉ de φ+ABC (plus de valeurs négatives ?)")
    n_neg_phi = sum(1 for s in bruits if all_results[s]['φ 16D'] < 0)
    n_neg_phi_abc = sum(1 for s in bruits if all_results[s]['φ+ABC'] < 0)
    print(f"     φ sans ABC   : {n_neg_phi} valeurs négatives sur {len(bruits)}")
    print(f"     φ avec ABC   : {n_neg_phi_abc} valeurs négatives sur {len(bruits)}")
    if n_neg_phi_abc < n_neg_phi:
        print(f"     ✅ ABC a STABILISÉ φ (−{n_neg_phi - n_neg_phi_abc} inversions)")
    elif n_neg_phi_abc == 0 and n_neg_phi > 0:
        print(f"     🎯 ABC a COMPLÈTEMENT ÉLIMINÉ les instabilités !")
    
    # Sauver
    out = {str(k): v for k, v in all_results.items()}
    out['metadata'] = {'alpha': ALPHA, 'B_alpha': B_1_PHI, 'n_mots': len(mots)}
    with open('recherche_v5_abc.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\n  Rapport : recherche_v5_abc.json")

if __name__ == '__main__':
    main()
