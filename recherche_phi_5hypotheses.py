#!/usr/bin/env python3
"""
RECHERCHE : φ peut-il dépasser SVD brute ?
==========================================
5 hypothèses testées. Objectif : trouver UNE configuration où φ > SVD.

Hypothèses :
  H1 : φ ancré sur la fréquence lexicale (Zipf)
  H2 : φ ancré sur la polysémie (nombre de sens)
  H3 : Similarité par INTERFÉRENCE (pas cosinus)
  H4 : Multi-échelles φ (φ, φ², φ³ comme harmoniques)
  H5 : Binding/unbinding HRR (opérations circulant dans φ-espace)

Si UNE de ces hypothèses dépasse SVD-16 brute (0.734), la théorie φ a un avantage.
"""
import sys, time, json, math
import numpy as np
import gensim.downloader as api
from collections import Counter

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

def svd_baseline(emb_ft, k=16):
    """SVD tronquée (référence à battre)."""
    U, S, Vt = np.linalg.svd(emb_ft, full_matrices=False)
    emb = U[:, :k] * S[:k]
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    return emb / norms

def cos_sim(emb, i, j):
    return float(emb[i] @ emb[j])

# ═══════════════════════════════════════════════════════════════════════════════
# HYPOTHÈSES
# ═══════════════════════════════════════════════════════════════════════════════

def H1_phi_frequence(emb_ft, mots, model, k=16, dim=128):
    """
    H1 : Ancre la phase φ sur la FRÉQUENCE lexicale (loi de Zipf).
    
    Hypothèse : les mots fréquents et les mots rares occupent des positions
    différentes dans le spectre φ. La fréquence est une propriété physique
    mesurable du langage.
    
    Phase = rank_du_mot × φ (loi de Zipf : freq ∝ 1/rank)
    + Composante sémantique (SVD)
    """
    N = len(mots)
    
    # Rank par fréquence dans GloVe (index = ordre par fréquence décroissante)
    freq_rank = np.array([model.key_to_index.get(m, N) for m in mots], dtype=float)
    freq_rank = freq_rank / max(freq_rank.max(), 1)  # normaliser [0,1]
    
    # Phase sémantique (SVD)
    U, S, Vt = np.linalg.svd(emb_ft, full_matrices=False)
    coords = U[:, 1:k+1]
    
    # Combiner : phase = sémantique × φ + fréquence × φ²
    phases = np.zeros((N, k))
    for d in range(k):
        c = coords[:, d]
        c_norm = TAU * (c - c.min()) / (c.max() - c.min() + 1e-10)
        # Modulation par fréquence : φ ajoute un décalage dépendant de Zipf
        phases[:, d] = c_norm + freq_rank * TAU * PHI ** (-d-1)
    
    # Embedding φ
    ds = np.arange(dim, dtype=np.float64)
    emb = np.zeros((N, dim))
    for i in range(N):
        total = np.zeros(dim)
        for d in range(k):
            total += phases[i, d] * ds * PHI / dim * (PHI ** (-d))
        emb[i] = np.cos(total) * np.exp(-ds * ALPHA / dim)
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    return emb / norms


def H2_phi_polsemie(emb_ft, mots, model, k=16, dim=128):
    """
    H2 : Ancre l'amplitude φ sur la POLYSÉMIE.
    
    Hypothèse : les mots polysémiques (plusieurs sens) ont une amplitude
    plus grande car ils interfèrent avec plus de contextes.
    
    Polysémie approximée par : variance des similarités avec tous les autres mots.
    """
    N = len(mots)
    norms = np.linalg.norm(emb_ft, axis=1, keepdims=True) + 1e-10
    normed = emb_ft / norms
    S = normed @ normed.T  # [N, N]
    
    # Polysémie = variance des similarités (mots polysémiques → variance élevée)
    polsemie = S.var(axis=1)  # [N]
    polsemie = (polsemie - polsemie.min()) / (polsemie.max() - polsemie.min() + 1e-10)
    
    # Phase sémantique (SVD)
    U, _, _ = np.linalg.svd(emb_ft, full_matrices=False)
    coords = U[:, 1:k+1]
    phases = np.zeros((N, k))
    for d in range(k):
        c = coords[:, d]
        phases[:, d] = TAU * (c - c.min()) / (c.max() - c.min() + 1e-10)
    
    # Embedding : amplitude modulée par polysémie
    ds = np.arange(dim, dtype=np.float64)
    emb = np.zeros((N, dim))
    for i in range(N):
        total = np.zeros(dim)
        for d in range(k):
            total += phases[i, d] * ds * PHI / dim * (PHI ** (-d))
        # Amplitude = polysémie (mots polysémiques → vecteur plus long)
        amp = np.exp(-ds * ALPHA / dim) * (1.0 + polsemie[i] * PHI)
        emb[i] = np.cos(total) * amp
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    return emb / norms


def H3_interference_similarity(emb_ft, k=16):
    """
    H3 : Similarité par INTERFÉRENCE (Re⟨ψ_a|ψ_b⟩) au lieu de cosinus.
    
    Hypothèse : la similarité ondulatoire capture la cohérence de phase,
    pas juste la direction. C'est la métrique naturelle de l'espace φ.
    
    Au lieu de faire cos(emb_a, emb_b), on calcule Re(⟨ψ_a|ψ_b⟩)
    où ψ est le vecteur complexe.
    """
    N = len(emb_ft)
    U, S, Vt = np.linalg.svd(emb_ft, full_matrices=False)
    coords = U[:, 1:k+1]  # [N, k] réelles
    
    # Construire vecteurs complexes : ψ = coords + i × coords_perpendiculaire
    # Coords perpendiculaire = dérivée spectrale (différence entre dims consécutives)
    coords_imag = np.zeros_like(coords)
    coords_imag[:, :-1] = np.diff(coords, axis=1)
    coords_imag[:, -1] = coords[:, 0]  # boucler
    
    psi = coords + 1j * coords_imag  # vecteurs complexes [N, k]
    
    # Normaliser
    psi_norm = psi / (np.abs(psi) + 1e-10)
    
    # Matrice d'interférence : Re(⟨ψ_a|ψ_b⟩)
    # = sum_d Re(psi_a[d] * conj(psi_b[d]))
    interference = np.real(psi_norm @ np.conj(psi_norm.T))  # [N, N]
    return interference


def H4_multi_echelles_phi(emb_ft, k=16, dim=128):
    """
    H4 : Multi-échelles φ (φ, φ², φ³... comme harmoniques musicaux).
    
    Hypothèse : chaque mot vibre à plusieurs fréquences harmoniques.
    Comme une note de musique (fondamentale + harmoniques), le sens
    d'un mot émerge de la superposition de ses harmoniques.
    
    Au lieu d'une seule échelle φ, on utilise φ, φ², φ³, φ⁴...
    """
    N = len(emb_ft)
    U, S, Vt = np.linalg.svd(emb_ft, full_matrices=False)
    coords = U[:, 1:k+1]
    phases = np.zeros((N, k))
    for d in range(k):
        c = coords[:, d]
        phases[:, d] = TAU * (c - c.min()) / (c.max() - c.min() + 1e-10)
    
    # Embedding multi-échelles : chaque dimension = une harmonique différente
    ds = np.arange(dim, dtype=np.float64)
    emb = np.zeros((N, dim))
    for i in range(N):
        # 4 sous-bandes de dim/4, chacune à une harmonique différente
        for band in range(4):
            start = band * (dim // 4)
            end = (band + 1) * (dim // 4)
            sub_ds = ds[start:end] - start
            freq = PHI ** (band + 1)  # φ, φ², φ³, φ⁴
            # Mélanger les k phases dans cette sous-bande
            total = np.zeros(len(sub_ds))
            for d in range(k):
                total += phases[i, d] * sub_ds * freq / len(sub_ds) * (PHI ** (-d))
            emb[i, start:end] = np.cos(total) * np.exp(-sub_ds * ALPHA / len(sub_ds))
    
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    return emb / norms


def H5_binding_unbinding(emb_ft, mots, dataset, m2i, k=16):
    """
    H5 : Test des ANALOGIES par binding/unbinding.
    
    Hypothèse : si l'espace φ est ondulatoire, alors l'arithmétique
    vectorielle doit marcher : king - man + woman ≈ queen.
    
    C'est LE test qui distingue un espace sémantique riche d'une
    simple réduction de dimension.
    
    Opération : convolution circulaire (binding HRR)
    """
    N = len(mots)
    
    # Embedding dense (SVD)
    U, S, Vt = np.linalg.svd(emb_ft, full_matrices=False)
    emb = U[:, :k] * S[:k]  # [N, k]
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    emb = emb / norms
    
    # Test d'analogies classiques
    analogies = [
        ('king','man','woman','queen'),   # king-man+woman = queen
        ('man','boy','girl','woman'),     # man-boy+girl = woman
        ('father','man','woman','mother'),
        ('brother','man','woman','sister'),
    ]
    
    results = []
    for a, b, c, expected in analogies:
        if not all(w in m2i for w in [a,b,c,expected]):
            continue
        # Arithmétique : a - b + c ≈ expected
        target = emb[m2i[a]] - emb[m2i[b]] + emb[m2i[c]]
        target = target / (np.linalg.norm(target) + 1e-10)
        # Top-5 plus proches (en excluant a, b, c)
        sims = emb @ target
        excluded = {m2i[a], m2i[b], m2i[c]}
        order = np.argsort(-sims)
        top5 = [(mots[i], float(sims[i])) for i in order if i not in excluded][:5]
        
        rank = None
        for i, (w, _) in enumerate(top5):
            if w == expected:
                rank = i + 1
                break
        
        results.append({
            'analogy': f'{a}-{b}+{c}=?',
            'expected': expected,
            'top5': top5,
            'rank': rank,
            'correct': rank == 1,
        })
    
    return results


def main():
    print("="*70)
    print("  RECHERCHE : φ peut-il dépasser SVD brute ?")
    print("  5 hypothèses testées")
    print("="*70)
    print()
    
    print("[1] Chargement GloVe-100...")
    t0 = time.time()
    model = api.load('glove-wiki-gigaword-100')
    print(f"    Chargé en {time.time()-t0:.1f}s — {len(model)} mots")
    
    dataset = [(a,b,s) for a,b,s in DATASET if a in model and b in model]
    mots = sorted(set(a for a,_,_ in dataset) | set(b for _,b,_ in dataset))
    emb_ft = np.array([model[w] for w in mots], dtype=np.float64)
    m2i = {m:i for i,m in enumerate(mots)}
    humain = [s for _,_,s in dataset]
    print(f"    Dataset : {len(dataset)} paires, {len(mots)} mots")
    
    # ── Référence : SVD brute ──
    print()
    print("[2] Baseline SVD-16...")
    emb_svd = svd_baseline(emb_ft, k=16)
    s_svd = [cos_sim(emb_svd, m2i[a], m2i[b]) for a,b,_ in dataset]
    rho_svd = spearman(humain, s_svd)
    print(f"    SVD-16 : Spearman = {rho_svd:.3f}  ← CIBLE À BATTRE")
    
    # GloVe brut
    s_glove = [float(model.similarity(a,b)) for a,b,_ in dataset]
    rho_glove = spearman(humain, s_glove)
    print(f"    GloVe  : Spearman = {rho_glove:.3f}")
    
    # ═══ TESTS DES 5 HYPOTHÈSES ═══
    print()
    print("="*70)
    print("  RÉSULTATS DES 5 HYPOTHÈSES")
    print("="*70)
    print(f"{'Hypothèse':<45} {'Spearman':>10} {'vs SVD':>8} {'Verdict':>10}")
    print("-"*75)
    
    results = {'svd_reference': rho_svd, 'glove_reference': rho_glove}
    
    # H1 : Fréquence
    emb_h1 = H1_phi_frequence(emb_ft, mots, model)
    s_h1 = [cos_sim(emb_h1, m2i[a], m2i[b]) for a,b,_ in dataset]
    rho_h1 = spearman(humain, s_h1)
    verdict = '✅ GAGNE' if rho_h1 > rho_svd else '❌ perd'
    print(f"{'H1: φ ancré sur fréquence (Zipf)':<45} {rho_h1:>10.3f} {rho_h1-rho_svd:>+8.3f} {verdict:>10}")
    results['H1_frequence'] = rho_h1
    
    # H2 : Polysémie
    emb_h2 = H2_phi_polsemie(emb_ft, mots, model)
    s_h2 = [cos_sim(emb_h2, m2i[a], m2i[b]) for a,b,_ in dataset]
    rho_h2 = spearman(humain, s_h2)
    verdict = '✅ GAGNE' if rho_h2 > rho_svd else '❌ perd'
    print(f"{'H2: amplitude φ sur polysémie':<45} {rho_h2:>10.3f} {rho_h2-rho_svd:>+8.3f} {verdict:>10}")
    results['H2_polsemie'] = rho_h2
    
    # H3 : Interférence
    interf = H3_interference_similarity(emb_ft, k=16)
    s_h3 = [float(interf[m2i[a], m2i[b]]) for a,b,_ in dataset]
    rho_h3 = spearman(humain, s_h3)
    verdict = '✅ GAGNE' if rho_h3 > rho_svd else '❌ perd'
    print(f"{'H3: similarité par interférence (Re⟨ψ|ψ⟩)':<45} {rho_h3:>10.3f} {rho_h3-rho_svd:>+8.3f} {verdict:>10}")
    results['H3_interference'] = rho_h3
    
    # H4 : Multi-échelles
    emb_h4 = H4_multi_echelles_phi(emb_ft, k=16)
    s_h4 = [cos_sim(emb_h4, m2i[a], m2i[b]) for a,b,_ in dataset]
    rho_h4 = spearman(humain, s_h4)
    verdict = '✅ GAGNE' if rho_h4 > rho_svd else '❌ perd'
    print(f"{'H4: multi-échelles φ (φ,φ²,φ³,φ⁴)':<45} {rho_h4:>10.3f} {rho_h4-rho_svd:>+8.3f} {verdict:>10}")
    results['H4_multi_echelles'] = rho_h4
    
    # H5 : Analogies
    print()
    print("─"*75)
    print("H5 : TEST D'ANALOGIES (binding/unbinding vectoriel)")
    print("─"*75)
    analogy_results = H5_binding_unbinding(emb_ft, mots, dataset, m2i)
    n_correct = sum(1 for r in analogy_results if r['correct'])
    n_total = len(analogy_results)
    print(f"  Analogies correctes (top-1) : {n_correct}/{n_total}")
    for r in analogy_results:
        status = '✅' if r['correct'] else f'❌ (rang {r["rank"]})'
        top3 = ', '.join(f'{w}({s:.2f})' for w,s in r['top5'][:3])
        print(f"  {r['analogy']:25s} attendu={r['expected']:10s} {status}")
        print(f"    top-3: {top3}")
    
    # ── BILAN ──
    print()
    print("="*70)
    print("  BILAN FINAL")
    print("="*70)
    rhos = {'H1': rho_h1, 'H2': rho_h2, 'H3': rho_h3, 'H4': rho_h4}
    best = max(rhos.items(), key=lambda x: x[1])
    print(f"  Meilleure hypothèse : {best[0]} = {best[1]:.3f}")
    print(f"  SVD référence       : {rho_svd:.3f}")
    print(f"  GloVe référence     : {rho_glove:.3f}")
    print()
    if best[1] > rho_svd:
        print(f"  🎯 {best[0]} DÉPASSE SVD de {best[1]-rho_svd:+.3f} !")
        print(f"     → La théorie φ a un avantage mesurable via {best[0]}.")
    else:
        print(f"  ❌ Aucune hypothèse ne dépasse SVD.")
        print(f"     Meilleur écart : {best[1]-rho_svd:+.3f}")
    
    # Analogie
    if n_total > 0:
        acc_analogie = n_correct / n_total
        print(f"  Analogies top-1 : {acc_analogie:.0%} ({n_correct}/{n_total})")
        print(f"  word2vec référence sur analogies : ~50-60%")
        if acc_analogie > 0.5:
            print(f"  🎯 Analogies COMPÉTITIVES avec word2vec !")
    
    results['analogies'] = {'correct': n_correct, 'total': n_total}
    with open('recherche_phi_5hypotheses.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Rapport : recherche_phi_5hypotheses.json")

if __name__ == '__main__':
    main()
