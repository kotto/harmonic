#!/usr/bin/env python3
"""
EXPÉRIENCE FALSIFIABLE v2 — Validation encodage φ
==================================================
Version corrigée : utilise GloVe-100 pré-entraîné (400K mots, qualité validée)
au lieu du FastText local défectueux.

Question : L'encodage φ capture-t-il la sémantique AUSSI BIEN que GloVe ?
"""
import sys, time, json, math
import numpy as np
import gensim.downloader as api

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1.0 / PHI
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# DATASET — WordSim-353 style (paires anglaises étiquetées)
# Score : 1.0 = synonyme, 0.5 = apparenté, 0.0 = sans rapport
# ═══════════════════════════════════════════════════════════════════════════════
DATASET = [
    # Très proches (1.0)
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

    # Apparentés (0.5)
    ("house","city",0.5),("book","school",0.5),("bread","wheat",0.5),
    ("doctor","hospital",0.5),("judge","court",0.5),("painter","art",0.5),
    ("musician","instrument",0.5),("time","clock",0.5),("money","price",0.5),
    ("work","job",0.5),("mind","thought",0.5),("body","health",0.5),
    ("tree","forest",0.5),("sea","ship",0.5),("sky","cloud",0.5),
    ("computer","software",0.5),("phone","call",0.5),
    ("water","river",0.5),("fire","smoke",0.5),("king","crown",0.5),

    # Sans rapport (0.0)
    ("war","philosophy",0.0),("blood","silence",0.0),("death","joy",0.0),
    ("iron","freedom",0.0),("calculation","dream",0.0),("earth","spirit",0.0),
    ("war","poetry",0.0),("blood","logic",0.0),("shadow","math",0.0),
    ("wind","justice",0.0),("stone","music",0.0),("water","honor",0.0),
    ("fire","sadness",0.0),("gold","wisdom",0.0),("iron","beauty",0.0),
    ("king","tomato",0.0),("man","galaxy",0.0),("cat","mathematics",0.0),
    ("dog","philosophy",0.0),("sun","boredom",0.0),
]


def similarite_caracteres(a, b):
    if a == b: return 1.0
    ta = {f"_{a}"[i:i+3] for i in range(len(f"_{a}_")-2)}
    tb = {f"_{b}"[i:i+3] for i in range(len(f"_{b}_")-2)}
    return len(ta & tb) / max(len(ta | tb), 1)


def ordonnancement_spectral(emb_matrix, k):
    N = emb_matrix.shape[0]
    norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True) + 1e-10
    normed = emb_matrix / norms
    S = np.maximum(normed @ normed.T, 0)
    D = np.diag(S.sum(axis=1) + 1e-10)
    D_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(D)))
    L = np.eye(N) - D_inv_sqrt @ S @ D_inv_sqrt
    eigvals, eigvecs = np.linalg.eigh(L)
    coords = eigvecs[:, 1:k+1]
    phases = np.zeros((N, k))
    for d in range(k):
        c = coords[:, d]
        phases[:, d] = TAU * (c - c.min()) / (c.max() - c.min() + 1e-10)
    return phases


def embedding_phi(phases, dim=128):
    N, k = phases.shape if phases.ndim == 2 else (len(phases), 1)
    if phases.ndim == 1:
        phases = phases.reshape(-1, 1)
    ds = np.arange(dim, dtype=np.float64)
    emb = np.zeros((N, dim))
    for i in range(N):
        total = np.zeros(dim)
        for d in range(k):
            total += phases[i, d] * ds * PHI / dim * (PHI ** (-d))
        emb[i] = np.cos(total) * np.exp(-ds * ALPHA / dim)
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    return emb / norms


def spearman(x, y):
    n = len(x)
    if n < 3: return 0.0
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1])


def main():
    print("="*70)
    print("  EXPÉRIENCE FALSIFIABLE v2 — φ vs GloVe (référence validée)")
    print("="*70)
    print()
    print("[1] Chargement GloVe-100 (400K mots)...")
    t0 = time.time()
    model = api.load('glove-wiki-gigaword-100')
    print(f"    Chargé en {time.time()-t0:.1f}s — {len(model)} mots")
    
    dataset = [(a,b,s) for a,b,s in DATASET if a in model and b in model]
    print(f"    Dataset : {len(dataset)} paires (sur {len(DATASET)})")
    
    mots = sorted(set(a for a,_,_ in dataset) | set(b for _,b,_ in dataset))
    print(f"    Mots uniques : {len(mots)}")
    emb_ft = np.array([model[w] for w in mots], dtype=np.float64)
    m2i = {m:i for i,m in enumerate(mots)}
    humain = [s for _,_,s in dataset]
    
    print()
    print("[2] Calcul des méthodes...")
    
    # 1. Caractères
    s_char = [similarite_caracteres(a,b) for a,b,_ in dataset]
    
    # 2. GloVe brut (référence)
    s_glove = [float(model.similarity(a,b)) for a,b,_ in dataset]
    
    # 3-5. φ à différentes dimensions
    results = {}
    for k in [1, 4, 16, 32, 64]:
        phases = ordonnancement_spectral(emb_ft, k=k)
        emb = embedding_phi(phases, dim=128)
        s_phi = [float(emb[m2i[a]] @ emb[m2i[b]]) for a,b,_ in dataset]
        results[f'φ {k}D'] = s_phi
    
    print()
    print("="*70)
    print("  RÉSULTATS — Spearman vs gold standard humain")
    print("="*70)
    print(f"{'Méthode':<25} {'Spearman':>10} {'Proches':>9} {'Éloign.':>9} {'Écart':>8}")
    print("-"*65)
    
    def show(name, scores):
        rho = spearman(humain, scores)
        mp = np.mean([scores[i] for i,(_,_,s) in enumerate(dataset) if s>=0.9])
        me = np.mean([scores[i] for i,(_,_,s) in enumerate(dataset) if s<=0.1])
        bar = '█'*int(max(0,rho)*40)
        print(f"{name:<25} {rho:>10.3f} {mp:>9.3f} {me:>9.3f} {mp-me:>+8.3f}  {bar}")
        return rho
    
    rho_char = show("Caractères", s_char)
    rhos_phi = {}
    for name, scores in results.items():
        rhos_phi[name] = show(name, scores)
    rho_glove = show("GloVe-100 (référence)", s_glove)
    
    print()
    print("-"*65)
    print("  ANALYSE :")
    print("-"*65)
    best_phi = max(rhos_phi.values())
    best_phi_name = max(rhos_phi, key=rhos_phi.get)
    print(f"  Meilleur φ       : {best_phi_name} = {best_phi:.3f}")
    print(f"  GloVe référence  : {rho_glove:.3f}")
    print(f"  Caractères       : {rho_char:.3f}")
    print(f"  Ratio φ/GloVe    : {best_phi/max(rho_glove,0.01):.0%}")
    print()
    if best_phi > rho_char * 1.5:
        print("  ✅ L'encodage φ capture SIGNIFICATIVEMENT plus de sémantique")
        print("     que la baseline de caractères.")
    else:
        print("  ❌ L'encodage φ n'apporte pas d'amélioration notable.")
    if best_phi > rho_glove * 0.8:
        print("  🎯 APPROCHE GloVe — validation forte de la théorie !")
    elif best_phi > rho_glove * 0.5:
        print("  ⚠️ Signal partiel : φ capture 50-80% du signal GloVe.")
    
    out = {'glove_spearman': rho_glove, 'best_phi': best_phi, 'best_phi_name': best_phi_name,
           'ratio': best_phi/max(rho_glove,0.01), 'char_spearman': rho_char,
           'all_phi': rhos_phi}
    with open('experience_phi_v2.json','w') as f:
        json.dump(out, f, indent=2)

if __name__=='__main__':
    main()
