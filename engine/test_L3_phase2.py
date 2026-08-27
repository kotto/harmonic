"""
TEST L3 — PHASE 2 : Analyse discriminante
==========================================
Teste si les canaux de couplage ont une structure ONDULATOIRE
qui dépasse le simple bruit pseudo-aléatoire de encode().

Tests :
  1. CLUSTERING  — les canaux d'un même boson sont-ils plus proches
                   entre eux qu'avec des canaux d'un autre boson ?
  2. SPECTRE     — le spectre de Fourier d'un canal montre-t-il
                   une structure différente du bruit blanc ?
  3. ROBUSTESSE  — si on change le label (ex. "photon_coulomb" →
                   "photon_COULOMB"), le résultat change-t-il ?
  4. STABILITÉ   — sur 50 seeds différentes, le rang reste-t-il K=n+D ?

Auteur : THU — Univers-Holistique
Date   : 2026-08-23
"""

import sys, os, math, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vital-ka", "core", "python"))
from wave_lang import encode, bind, resonate, diffract, spectrum, PHI, ALPHA, clear_encode_cache

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════

DIM = 512
TOLERANCE = 1e-6
N_TRIALS = 50  # pour test de stabilité
N_BRUIT = 200  # pour baseline


PHOTON_MODES = [
    "photon_helicite_+1_transverse_electrique",
    "photon_helicite_-1_transverse_magnetique",
    "photon_longitudinal_virtuel_hors_couche",
    "photon_coulomb_instantane_scalaire",
    "photon_echange_croise_fermion_antifermion",
]

SCALAR_MODES = [
    "scalaire_mode_spatial_x",
    "scalaire_mode_spatial_y",
    "scalaire_mode_spatial_z",
    "scalaire_mode_temporel",
]

GRAVITON_MODES = [
    "graviton_helicite_+2",
    "graviton_helicite_-2",
    "graviton_mode_vectoriel_x",
    "graviton_mode_vectoriel_y",
    "graviton_mode_vectoriel_z",
    "graviton_mode_scalaire",
]

ELECTRON_LABEL = "electron_spin_1/2_fermion_Dirac_masse_me"


# ═══════════════════════════════════════════════════════════════════
# OUTILS
# ═══════════════════════════════════════════════════════════════════

def build_vertices(boson_modes, electron_label=ELECTRON_LABEL):
    """Construit les vertex ψ_e ⊛ ψ_boson pour chaque mode."""
    psi_e = encode(electron_label, dim=DIM)
    return [bind(psi_e, encode(m, dim=DIM)) for m in boson_modes]


def pairwise_resonance(vectors):
    """Matrice de résonance (Gram) entre vecteurs."""
    n = len(vectors)
    R = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            R[i, j] = resonate(vectors[i], vectors[j])
    return R


def off_diagonal_stats(R):
    """Moyenne et écart-type des éléments hors-diagonaux (valeur absolue)."""
    n = R.shape[0]
    vals = []
    for i in range(n):
        for j in range(i+1, n):
            vals.append(abs(R[i, j]))
    return np.mean(vals), np.std(vals)


def count_rank(R, tol=TOLERANCE):
    """Nombre de valeurs propres > tolérance."""
    ev = np.sort(np.linalg.eigvalsh(R))[::-1]
    return int(np.sum(ev > tol)), ev


def random_baseline(n_vecs, n_trials=N_BRUIT):
    """Distribution du |hors-diag| pour n_vecs vecteurs aléatoires."""
    off_means = []
    off_stds = []
    for t in range(n_trials):
        labels = [f"BASELINE_TRIAL_{t}_{k}" for k in range(n_vecs)]
        vecs = [encode(l, dim=DIM) for l in labels]
        R = pairwise_resonance(vecs)
        m, s = off_diagonal_stats(R)
        off_means.append(m)
        off_stds.append(s)
    return np.mean(off_means), np.std(off_means), np.mean(off_stds), np.std(off_stds)


# ═══════════════════════════════════════════════════════════════════
# TEST 1 : CLUSTERING CROSS-n
# ═══════════════════════════════════════════════════════════════════
# Hypothèse : les 5 canaux photon sont plus proches entre eux
# (intra-groupe) qu'avec les canaux scalaires (inter-groupe).
# Si TRUE → structure physique. Si FALSE → bruit aléatoire.

def test_clustering():
    print("═" * 70)
    print("  TEST 1 : CLUSTERING CROSS-n")
    print("═" * 70)
    print()
    print("  Hypothèse : si les canaux ont une structure physique,")
    print("  les vertex d'un même boson devraient être plus proches")
    print("  entre eux (intra) qu'avec ceux d'un autre boson (inter).")
    print()

    v_photon = build_vertices(PHOTON_MODES)
    v_scalar = build_vertices(SCALAR_MODES)
    v_graviton = build_vertices(GRAVITON_MODES)

    # Intra-groupe
    R_photon = pairwise_resonance(v_photon)
    R_scalar = pairwise_resonance(v_scalar)
    R_graviton = pairwise_resonance(v_graviton)

    intra_photon = off_diagonal_stats(R_photon)
    intra_scalar = off_diagonal_stats(R_scalar)
    intra_graviton = off_diagonal_stats(R_graviton)

    # Inter-groupe
    inter_ps = []
    for vp in v_photon:
        for vs in v_scalar:
            inter_ps.append(abs(resonate(vp, vs)))
    inter_pg = []
    for vp in v_photon:
        for vg in v_graviton:
            inter_pg.append(abs(resonate(vp, vg)))
    inter_sg = []
    for vs in v_scalar:
        for vg in v_graviton:
            inter_sg.append(abs(resonate(vs, vg)))

    inter_ps_mean = np.mean(inter_ps)
    inter_pg_mean = np.mean(inter_pg)
    inter_sg_mean = np.mean(inter_sg)

    # Baseline bruit pour 5, 4, 6 vecteurs
    bl5_mean, bl5_std, _, _ = random_baseline(5)
    bl4_mean, bl4_std, _, _ = random_baseline(4)
    bl6_mean, bl6_std, _, _ = random_baseline(6)

    print(f"  {'Groupe':<25s} {'|hors-diag|':>12s} {'Baseline':>12s} {'Δ/σ':>8s}")
    print(f"  {'─'*25} {'─'*12} {'─'*12} {'─'*8}")
    print(f"  {'Photon (5) intra':<25s} {intra_photon[0]:>12.6f} {bl5_mean:>12.6f} {(intra_photon[0]-bl5_mean)/bl5_std:>+8.2f}σ")
    print(f"  {'Scalaire (4) intra':<25s} {intra_scalar[0]:>12.6f} {bl4_mean:>12.6f} {(intra_scalar[0]-bl4_mean)/bl4_std:>+8.2f}σ")
    print(f"  {'Graviton (6) intra':<25s} {intra_graviton[0]:>12.6f} {bl6_mean:>12.6f} {(intra_graviton[0]-bl6_mean)/bl6_std:>+8.2f}σ")
    print(f"  {'Photon↔Scalaire inter':<25s} {inter_ps_mean:>12.6f}")
    print(f"  {'Photon↔Graviton inter':<25s} {inter_pg_mean:>12.6f}")
    print(f"  {'Scalaire↔Graviton inter':<25s} {inter_sg_mean:>12.6f}")
    print()

    # Test : intra < inter ? (attendu si structure)
    intra_ok = (intra_photon[0] < inter_ps_mean and 
                intra_photon[0] < inter_pg_mean and
                intra_scalar[0] < inter_ps_mean and
                intra_scalar[0] < inter_sg_mean and
                intra_graviton[0] < inter_pg_mean and
                intra_graviton[0] < inter_sg_mean)

    if intra_ok:
        print("  ✅ STRUCTURE DÉTECTÉE : les canaux intra-groupe sont")
        print("     plus proches que les canaux inter-groupe.")
        print("     → encode() préserve une structure de similarité")
        print("       au-delà du simple hachage aléatoire.")
    else:
        print("  ❌ PAS DE STRUCTURE : les canaux intra-groupe ne sont pas")
        print("     plus proches que les inter-groupe.")
        print("     → encode() se comporte comme un hachage aléatoire.")
        print("     → Les « canaux » ne sont que des labels distincts.")
    print()

    return intra_ok


# ═══════════════════════════════════════════════════════════════════
# TEST 2 : SPECTRE — bruit blanc ou structure ?
# ═══════════════════════════════════════════════════════════════════
# L'hypothèse de L3 prédit que les canaux ont des signatures
# spectrales distinctes. On teste si le spectre s'écarte du bruit
# blanc (distribution χ² attendue pour des vecteurs gaussiens).

def test_spectral():
    print("═" * 70)
    print("  TEST 2 : ANALYSE SPECTRALE")
    print("═" * 70)
    print()
    print("  Hypothèse : un canal physique a une signature spectrale")
    print("  distincte du bruit blanc. On mesure l'autocorrélation")
    print("  du spectre pour détecter une éventuelle structure.")
    print()

    v_photon = build_vertices(PHOTON_MODES)
    
    ac_signals = []
    for i, v in enumerate(v_photon):
        spec = spectrum(v)
        # Autocorrélation du spectre (détecte les périodicités)
        spec_centered = spec - np.mean(spec)
        autocorr = np.correlate(spec_centered, spec_centered, mode='full')
        autocorr = autocorr[len(autocorr)//2:]  # partie positive
        autocorr = autocorr / autocorr[0]  # normaliser
        ac_signals.append(autocorr)

    # Baseline : autocorrélation de spectres aléatoires
    n_baseline = 100
    ac_baselines = []
    for t in range(n_baseline):
        v = encode(f"BASELINE_SPECTRE_{t}", dim=DIM)
        spec = spectrum(v)
        spec_centered = spec - np.mean(spec)
        autocorr = np.correlate(spec_centered, spec_centered, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        autocorr = autocorr / autocorr[0]
        ac_baselines.append(autocorr)

    # Comparer le lag-1
    lag1_signal = np.mean([ac[1] for ac in ac_signals])
    lag1_baseline = np.mean([ac[1] for ac in ac_baselines])
    lag1_baseline_std = np.std([ac[1] for ac in ac_baselines])

    print(f"  Autocorrélation lag-1 du spectre :")
    print(f"    Canaux photon : {lag1_signal:.6f}")
    print(f"    Bruit baseline : {lag1_baseline:.6f} ± {lag1_baseline_std:.6f}")
    print(f"    Écart : {(lag1_signal - lag1_baseline) / lag1_baseline_std:+.2f}σ")
    print()

    # Test de blancheur : test de Ljung-Box sur les 20 premiers lags
    from scipy import stats as sp_stats
    
    # Pour chaque spectre de canal, test de blancheur
    lb_pvalues = []
    for ac in ac_signals:
        # Statistique Q de Ljung-Box simplifiée
        n = len(ac)
        ac_vals = ac[1:21]  # lags 1 à 20
        Q = n * (n + 2) * np.sum(ac_vals**2 / (n - np.arange(1, 21)))
        p = 1 - sp_stats.chi2.cdf(Q, 20)
        lb_pvalues.append(p)

    # Même chose pour les baselines
    lb_pvalues_bl = []
    for ac in ac_baselines[:len(ac_signals)]:
        n = len(ac)
        ac_vals = ac[1:21]
        Q = n * (n + 2) * np.sum(ac_vals**2 / (n - np.arange(1, 21)))
        p = 1 - sp_stats.chi2.cdf(Q, 20)
        lb_pvalues_bl.append(p)

    mean_p_signal = np.mean(lb_pvalues)
    mean_p_bl = np.mean(lb_pvalues_bl)

    print(f"  Test de blancheur spectrale (Ljung-Box, 20 lags) :")
    print(f"    p-values moyennes — signal : {mean_p_signal:.4f}  |  bruit : {mean_p_bl:.4f}")
    print(f"    (p > 0.05 → spectre compatible avec un bruit blanc)")
    print()

    if mean_p_signal > 0.05:
        print("  ⚠️  Les spectres des canaux photon sont compatibles avec")
        print("     un bruit blanc. Aucune structure spectrale détectée.")
        print("     → encode() + bind() produit des spectres plats.")
        print("     → La « signature spectrale » d'un canal n'est pas")
        print("       distincte du bruit dans cette implémentation.")
    else:
        print("  ✅ Structure spectrale détectée ! Les canaux ne sont")
        print("     pas du bruit blanc pur.")

    return mean_p_signal > 0.05  # True si compatible bruit blanc


# ═══════════════════════════════════════════════════════════════════
# TEST 3 : STABILITÉ — sur N seeds, K = n+D toujours ?
# ═══════════════════════════════════════════════════════════════════

def test_stability():
    print("═" * 70)
    print(f"  TEST 3 : STABILITÉ SUR {N_TRIALS} SEEDS")
    print("═" * 70)
    print()

    all_ranks = {"photon": [], "scalaire": [], "graviton": []}

    for t in range(N_TRIALS):
        # Forcer des labels différents pour éviter le cache
        suffix = f"_TRIAL_{t}"
        
        psi_e = encode(ELECTRON_LABEL + suffix, dim=DIM)
        
        # Photon
        vertices_p = [bind(psi_e, encode(m + suffix, dim=DIM)) for m in PHOTON_MODES]
        R = pairwise_resonance(vertices_p)
        K, _ = count_rank(R)
        all_ranks["photon"].append(K)

        # Scalaire
        vertices_s = [bind(psi_e, encode(m + suffix, dim=DIM)) for m in SCALAR_MODES]
        R = pairwise_resonance(vertices_s)
        K, _ = count_rank(R)
        all_ranks["scalaire"].append(K)

        # Graviton
        vertices_g = [bind(psi_e, encode(m + suffix, dim=DIM)) for m in GRAVITON_MODES]
        R = pairwise_resonance(vertices_g)
        K, _ = count_rank(R)
        all_ranks["graviton"].append(K)
        
        clear_encode_cache()

    print(f"  {'Boson':<15s} {'K attendu':>10s} {'K moyen':>10s} {'K min':>8s} {'K max':>8s} {'Stable':>8s}")
    print(f"  {'─'*15} {'─'*10} {'─'*10} {'─'*8} {'─'*8} {'─'*8}")
    
    stable_all = True
    for name, expected, ranks in [("Photon", 5, all_ranks["photon"]),
                                    ("Scalaire", 4, all_ranks["scalaire"]),
                                    ("Graviton", 6, all_ranks["graviton"])]:
        arr = np.array(ranks)
        stable = np.all(arr == expected)
        stable_all = stable_all and stable
        status = "✅" if stable else "❌"
        print(f"  {status} {name:<13s} {expected:>10d} {arr.mean():>10.1f} {arr.min():>8d} {arr.max():>8d} {'OUI' if stable else 'NON':>8s}")
    
    print()
    if stable_all:
        print(f"  ✅ Sur {N_TRIALS} seeds, K = n+D est STABLE.")
        print("     La dimensionalité des canaux ne dépend pas de la seed.")
    else:
        print(f"  ❌ Instabilité détectée : K fluctue selon la seed.")
    
    return stable_all


# ═══════════════════════════════════════════════════════════════════
# TEST 4 : TEST DE PERMUTATION — label arbitraire ?
# ═══════════════════════════════════════════════════════════════════
# Si les canaux sont de vraies structures physiques, changer
# l'ordre ou la casse des labels ne devrait PAS changer le rang.
# On vérifie.

def test_permutation():
    print("═" * 70)
    print("  TEST 4 : ROBUSTESSE AUX LABELS")
    print("═" * 70)
    print()

    psi_e = encode(ELECTRON_LABEL, dim=DIM)

    # Labels originaux
    v_orig = build_vertices(PHOTON_MODES)
    R_orig = pairwise_resonance(v_orig)
    K_orig, ev_orig = count_rank(R_orig)

    # Labels permutés (mêmes modes, ordre différent)
    permuted = PHOTON_MODES.copy()
    np.random.seed(123)
    np.random.shuffle(permuted)
    v_perm = [bind(psi_e, encode(m, dim=DIM)) for m in permuted]
    R_perm = pairwise_resonance(v_perm)
    K_perm, ev_perm = count_rank(R_perm)

    # Labels en majuscule
    upper = [m.upper() for m in PHOTON_MODES]
    v_upper = [bind(psi_e, encode(m, dim=DIM)) for m in upper]
    R_upper = pairwise_resonance(v_upper)
    K_upper, ev_upper = count_rank(R_upper)

    print(f"  Originaux     : K = {K_orig}, v.p. = {np.array2string(ev_orig, precision=4)}")
    print(f"  Permutés      : K = {K_perm}, v.p. = {np.array2string(ev_perm, precision=4)}")
    print(f"  Majuscules    : K = {K_upper}, v.p. = {np.array2string(ev_upper, precision=4)}")
    print()

    if K_orig == K_perm == K_upper == 5:
        print("  ✅ Le rang K=5 est robuste aux changements de labels.")
        print("     Mais ceci est ATTENDU car encode() produit des")
        print("     vecteurs distincts pour des labels distincts.")
    else:
        print("  ❌ Le rang dépend du label ! Anomalie.")
    
    return K_orig == K_perm == K_upper == 5


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t0 = time.time()
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  TEST L3 — PHASE 2 : ANALYSE DISCRIMINANTE                  ║")
    print("║  « Les canaux ont-ils une structure au-delà du bruit ? »    ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"  Dimension : {DIM}")
    print(f"  PHI       : {PHI:.15f}")
    print(f"  ALPHA     : {ALPHA:.15f}")
    print()

    t1 = test_clustering()
    t2 = test_spectral()
    t3 = test_stability()
    t4 = test_permutation()

    print("═" * 70)
    print("  SYNTHÈSE")
    print("═" * 70)
    print()
    print(f"  Test 1 (clustering)  : {'✅ STRUCTURE' if t1 else '❌ BRUIT'} — les canaux intra-groupe sont-ils plus proches ?")
    print(f"  Test 2 (spectre)     : {'⚠️ BRUIT BLANC' if t2 else '✅ STRUCTURE'} — les spectres sont-ils structurés ?")
    print(f"  Test 3 (stabilité)   : {'✅ STABLE' if t3 else '❌ INSTABLE'} — K = n+D est-il stable sur {N_TRIALS} seeds ?")
    print(f"  Test 4 (permutation) : {'✅ ROBUSTE' if t4 else '❌ FRAGILE'} — le rang dépend-il du label ?")
    print()
    
    if t1:
        print("  → Le test de clustering suggère que les canaux d'un même")
        print("    boson ont une proximité structurelle dans ℂ⁵¹².")
        print("    Ceci est un indice EN FAVEUR de L3 : encode() capture")
        print("    une similarité sémantique au-delà du hachage aléatoire.")
    else:
        print("  → Aucune structure n'est détectée au-delà du bruit.")
        print("    Les « canaux » sont indistinguables de labels aléatoires.")
        print("    L3 ne peut pas être testé avec encode() seul — il faut")
        print("    une implémentation physique du vertex QED + noyau ABC.")
    
    if t2:
        print("  → Les spectres sont compatibles avec du bruit blanc.")
        print("    C'est attendu pour des vecteurs gaussiens i.i.d.")
        print("    (le spectre d'un vecteur gaussien ~ Rayleigh, pas blanc,")
        print("    mais l'autocorrélation est celle d'un bruit blanc).")
    
    print()
    print(f"  Temps : {time.time() - t0:.2f}s")
    print()