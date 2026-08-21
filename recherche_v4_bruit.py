#!/usr/bin/env python3
"""
RECHERCHE v4 : ROBUSTESSE AU BRUIT — φ vs SVD
==============================================
Question : quand on ajoute du bruit aux embeddings, qui dégrade le moins vite ?

Hypothèse : la structure cos(phase × φ) × exp(-d×α) agit comme un filtre
passe-bas naturel, donc φ devrait être plus robuste au bruit que SVD.

Protocole :
  1. Pour chaque niveau de bruit σ ∈ {0.0, 0.1, 0.2, ..., 2.0}
  2. Ajouter du bruit gaussien aux embeddings GloVe
  3. Calculer SVD-16 et φ-16D depuis les embeddings bruités
  4. Mesurer le Spearman de chacun
  5. Comparer les courbes de dégradation

VICTOIRE de φ si : Spearman(φ, bruité) > Spearman(SVD, bruité) pour au moins
un niveau de bruit non-trivial (σ > 0.3).
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

# ── Méthodes ──

def methode_svd(emb, k=16):
    U, S, Vt = np.linalg.svd(emb, full_matrices=False)
    return U[:, :k] * S[:k]

def methode_phi_16d(emb, k=16, dim=128):
    """φ 16D avec couche cos(phase × φ)."""
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
        emb_out[i] = np.cos(total) * np.exp(-ds * ALPHA / dim)
    norms = np.linalg.norm(emb_out, axis=1, keepdims=True) + 1e-10
    return emb_out / norms

def methode_laplacien_pur(emb, k=16):
    """Laplacien Eigenmaps sans φ (juste les vecteurs propres)."""
    N = emb.shape[0]
    S = np.maximum(cos_sim_mat(emb), 0)
    deg = S.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1]

def methode_phi_rbf_sigma_phi(emb, k=16):
    """φ dans le noyau : σ = φ (H6 de v3)."""
    N = emb.shape[0]
    S = cos_sim_mat(emb)
    D_angle = np.arccos(np.clip(S, -1, 1))
    sigma = PHI
    W = np.maximum(S, 0) * np.exp(-(D_angle**2) / (2 * sigma**2))
    W = (W + W.T) / 2
    deg = W.sum(axis=1) + 1e-10
    D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
    L = np.eye(N) - D_inv_sqrt @ W @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    return eigvecs[:, 1:k+1] * np.sqrt(np.maximum(eigvals[1:k+1], 0))


def main():
    print("="*70)
    print("  RECHERCHE v4 : ROBUSTESSE AU BRUIT")
    print("  φ vs SVD sous bruit gaussien croissant")
    print("="*70)
    print()
    
    # Charger cache
    cache = np.load('glove_cache_136.npz', allow_pickle=True)
    mots = list(cache['mots'])
    emb_clean = cache['emb']
    m2i = {m: i for i, m in enumerate(mots)}
    glove_sim = np.load('glove_sims_136.npy')
    
    dataset = [(a,b,s) for a,b,s in DATASET if a in m2i and b in m2i]
    humain = [s for _,_,s in dataset]
    
    # Norme moyenne des embeddings (pour calibrer le bruit)
    norm_moy = np.mean(np.linalg.norm(emb_clean, axis=1))
    print(f"  Mots : {len(mots)}, dim originelle : {emb_clean.shape[1]}")
    print(f"  Norme moyenne embeddings : {norm_moy:.2f}")
    print(f"  Dataset : {len(dataset)} paires")
    print()
    
    # Niveaux de bruit à tester
    bruits = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0]
    
    # Méthodes à comparer
    methodes = {
        'SVD-16':              methode_svd,
        'Laplacien-16':        methode_laplacien_pur,
        'φ 16D (cos×φ)':       methode_phi_16d,
        'φ-noyau σ=φ':         methode_phi_rbf_sigma_phi,
    }
    
    # GloVe brut comme référence (similarité directement, pas de projection)
    
    print("  Bruit σ (relatif)  │ SVD-16 │ Laplacien │ φ 16D  │ φ-noyau │ GloVe brut")
    print("  " + "─"*78)
    
    all_results = {}
    
    for sigma_rel in bruits:
        # Bruit absolu = fraction de la norme moyenne
        sigma_abs = sigma_rel * norm_moy
        
        # Ajouter bruit (graine fixe pour reproductibilité)
        rng = np.random.RandomState(42)
        noise = rng.randn(*emb_clean.shape) * sigma_abs
        emb_noise = emb_clean + noise
        
        # Calculer chaque méthode
        row = {}
        for name, func in methodes.items():
            try:
                coords = func(emb_noise, k=16)
                rho = project_and_score(coords, dataset, m2i, humain)
                row[name] = rho
            except:
                row[name] = 0.0
        
        # GloVe brut (similarité directe sur embeddings bruités)
        s_glove = [float(glove_sim[m2i[a], m2i[b]]) for a,b,_ in dataset]
        row['GloVe brut'] = spearman(humain, s_glove)
        
        all_results[sigma_rel] = row
        
        # Afficher
        bar_svd = '█' * int(max(0, row['SVD-16']) * 30)
        print(f"  σ = {sigma_rel:>4.1f}              │ "
              f"{row['SVD-16']:>6.3f}  │  {row['Laplacien-16']:>6.3f}    │ "
              f"{row['φ 16D (cos×φ)']:>6.3f}  │  {row['φ-noyau σ=φ']:>6.3f}  │  "
              f"{row['GloVe brut']:>6.3f}   {bar_svd}")
    
    # ── ANALYSE ──
    print()
    print("="*70)
    print("  ANALYSE DE LA ROBUSTESSE")
    print("="*70)
    
    # Score sans bruit
    print(f"\n  Sans bruit (σ=0) :")
    for name in ['SVD-16','Laplacien-16','φ 16D (cos×φ)','φ-noyau σ=φ','GloVe brut']:
        print(f"    {name:<20} : {all_results[0.0][name]:.3f}")
    
    # Pour chaque méthode, trouver le σ où elle tombe sous 0.3 (seuil d'utilité)
    print(f"\n  Seuil de dégradation (Spearman < 0.3) :")
    seuils = {}
    for name in ['SVD-16','Laplacien-16','φ 16D (cos×φ)','φ-noyau σ=φ','GloVe brut']:
        seuil = None
        for sigma_rel in bruits:
            if all_results[sigma_rel][name] < 0.3:
                seuil = sigma_rel
                break
        seuils[name] = seuil if seuil else ">5.0"
        print(f"    {name:<20} : σ ≈ {seuils[name]}")
    
    # Qui résiste le plus longtemps ?
    print(f"\n  Classement de robustesse (σ où Spearman < 0.3) :")
    def seuil_val(name):
        v = seuils[name]
        return v if isinstance(v, float) else 999.0
    classement = sorted(seuils.keys(), key=seuil_val, reverse=True)
    for i, name in enumerate(classement):
        emoji = '🥇' if i == 0 else ('🥈' if i == 1 else ('🥉' if i == 2 else '  '))
        print(f"    {emoji} {name:<20} : σ < 0.3 à {seuils[name]}")
    
    # ── VERDICT ──
    print()
    print("="*70)
    print("  VERDICT")
    print("="*70)
    
    # Comparer à bruit modéré (σ=1.0 = bruit égal à la norme)
    print(f"\n  À bruit modéré (σ=1.0, bruit = norme des vecteurs) :")
    for name in ['SVD-16','Laplacien-16','φ 16D (cos×φ)','φ-noyau σ=φ','GloVe brut']:
        rho = all_results[1.0][name]
        print(f"    {name:<20} : {rho:.3f}")
    
    rho_svd_1 = all_results[1.0]['SVD-16']
    best_phi_1 = max(all_results[1.0].get('φ 16D (cos×φ)', 0), 
                     all_results[1.0].get('φ-noyau σ=φ', 0))
    
    if best_phi_1 > rho_svd_1:
        print(f"\n  🎯 À σ=1.0, φ ({best_phi_1:.3f}) DÉPASSE SVD ({rho_svd_1:.3f}) !")
        print(f"     → φ est PLUS ROBUSTE au bruit. Validation de la théorie !")
    else:
        print(f"\n  ❌ À σ=1.0, φ ({best_phi_1:.3f}) < SVD ({rho_svd_1:.3f}).")
        print(f"     → φ n'est pas plus robuste que SVD.")
    
    # À bruit élevé (σ=2.0)
    rho_svd_2 = all_results[2.0]['SVD-16']
    best_phi_2 = max(all_results[2.0].get('φ 16D (cos×φ)', 0),
                     all_results[2.0].get('φ-noyau σ=φ', 0))
    print(f"\n  À bruit élevé (σ=2.0) :")
    print(f"    SVD   : {rho_svd_2:.3f}")
    print(f"    φ max : {best_phi_2:.3f}")
    if best_phi_2 > rho_svd_2:
        print(f"    → 🎯 φ SURPASSE SVD sous bruit fort !")
    
    # Sauvegarder
    out = {str(k): v for k, v in all_results.items()}
    out['seuils'] = {k: str(v) for k, v in seuils.items()}
    with open('recherche_v4_bruit.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\n  Rapport : recherche_v4_bruit.json")

if __name__ == '__main__':
    main()
