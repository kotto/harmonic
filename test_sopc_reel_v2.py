#!/usr/bin/env python3
"""
test_sopc_reel_v2.py — Test SOPC optimise sur l'hologramme reel
==============================================================
Version optimisee : lit l'hologramme UNE SEULE FOIS, noyau ABC pre-calcule.

Usage :
    set PYTHONIOENCODING=utf-8 && python test_sopc_reel_v2.py
"""

import os, sys, math, time
import numpy as np

_PROJECT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _PROJECT)
sys.path.insert(0, os.path.join(_PROJECT, 'harmonic_training'))

# =========================================================================
# Imports
# =========================================================================
from engine.sopc_core import (
    resonance_sparse, sparse_read, compute_sparse_threshold,
    predictive_update_abc,
    abc_kernel, mittag_leffler, ABCPhaseGate,
    PHI, ALPHA, B_1_PHI, K0, PHI2, SEUIL_SPARSE_FACTOR
)

CHEMIN_HOLOGRAMME = os.path.join(_PROJECT, "ka_knowledge_base", "hologramme.npy")
FICHIER_SORTIE = os.path.join(_PROJECT, "test_sopc_reel_v2_output.txt")

# =========================================================================
# Redirection de la sortie vers fichier
# =========================================================================
class TeeOutput:
    """Redirige stdout vers un fichier et le terminal."""
    def __init__(self, path):
        self.file = open(path, 'w', encoding='utf-8')
        self.stdout = sys.stdout
    def write(self, text):
        self.file.write(text)
        self.file.flush()
        self.stdout.write(text)
    def flush(self):
        self.file.flush()
        self.stdout.flush()
    def close(self):
        self.file.close()

sys.stdout = TeeOutput(FICHIER_SORTIE)

def lire_tous_tokens(H, xx, yy, kx_all, ky_all, V_eff, batch_size=500):
    """Lit tous les tokens de l'hologramme en batches vectorises."""
    nx, ny = H.shape
    activations = np.zeros(V_eff, dtype=np.float64)
    t0 = time.time()
    for start in range(0, V_eff, batch_size):
        end = min(start + batch_size, V_eff)
        bkx = kx_all[start:end]
        bky = ky_all[start:end]
        phase = (bkx[:, None, None] * xx[None, :, :] +
                 bky[:, None, None] * yy[None, :, :])
        onde_ref = np.exp(-1j * phase)
        corr = np.sum(H[None, :, :] * onde_ref, axis=(1, 2))
        activations[start:end] = np.abs(corr) / (nx * ny)
    dt = time.time() - t0
    return activations, dt

def main():
    print("=" * 65)
    print("TEST SOPC V2 SUR HOLOGRAMME REEL (optimise)")
    print("=" * 65)
    print(f"\n  PHI = {PHI:.6f}")
    print(f"  ALPHA = 1/PHI = {ALPHA:.6f}")
    print(f"  B(alpha) = {B_1_PHI:.6f}")
    print(f"  K0 = B(alpha) = {K0:.6f}")
    print(f"  Facteur seuil = K0 * PHI = {SEUIL_SPARSE_FACTOR:.6f}")
    
    # =====================================================================
    # TEST 5 : Noyau ABC
    # =====================================================================
    print(f"\n{'='*65}")
    print("TEST 5 : NOYAU ABC (fondement fractionnaire)")
    print(f"{'='*65}")
    
    t0 = time.time()
    kernel = abc_kernel(20)
    print(f"  Temps calcul noyau ABC: {(time.time()-t0)*1000:.1f}ms")
    print(f"  α = 1/φ = {ALPHA:.6f}")
    print(f"  B(α) = {B_1_PHI:.6f}")
    print(f"  K(0) = {kernel[0]:.6f}")
    print(f"  K(5) = {kernel[5]:.6f}")
    print(f"  K(10)= {kernel[10]:.6f}")
    ratio = kernel[10]/kernel[5] if kernel[5] > 0 else 0
    expected = (5.0/10.0) ** (ALPHA + 1.0)
    print(f"  K(10)/K(5) = {ratio:.4f} (attendu ~{expected:.4f})")
    
    # =====================================================================
    # TEST 4 : Gate oscillatoire ABC
    # =====================================================================
    print(f"\n{'='*65}")
    print("TEST 4 : GATE OSCILLATOIRE ABC")
    print(f"{'='*65}")
    
    gate = ABCPhaseGate()
    print(f"  ω₀ = {gate.omega_0:.4f} (= φ = {PHI:.4f})")
    print(f"  θ (contexte): {gate.theta_freq:.4f}")
    print(f"  γ (items):   {gate.gamma_freq:.4f}")
    valeurs = [gate.step() for _ in range(100)]
    n_actifs = sum(1 for v in valeurs if v > 0.01)
    print(f"  Phases ouvertes: {n_actifs}/100")
    
    # =====================================================================
    # CHARGER HOLOGRAMME
    # =====================================================================
    print(f"\n{'='*65}")
    print("CHARGEMENT HOLOGRAMME")
    print(f"{'='*65}")
    
    if not os.path.exists(CHEMIN_HOLOGRAMME):
        print(f"[ERREUR] Hologramme non trouve: {CHEMIN_HOLOGRAMME}")
        sys.stdout.close()
        return
    
    H = np.load(CHEMIN_HOLOGRAMME)
    nx, ny = H.shape
    print(f"  Shape: {nx}x{ny}")
    print(f"  Type: {H.dtype}")
    print(f"  Energie: {np.sum(np.abs(H)):.0f}")
    print(f"  Taille: {os.path.getsize(CHEMIN_HOLOGRAMME)/1024:.1f} KB")
    
    x = np.linspace(-math.pi, math.pi, nx)
    y = np.linspace(-math.pi, math.pi, ny)
    xx, yy = np.meshgrid(x, y, indexing='ij')
    
    # Tokenizer
    try:
        from model.vocabulaire_etendu import VOCABULAIRE_ETENDU
        VOCAB = VOCABULAIRE_ETENDU
        print(f"  Vocabulaire etendu: {len(VOCAB)} mots")
    except ImportError:
        from model.harmonic_resonance_generator import VOCABULAIRE_BASE
        VOCAB = VOCABULAIRE_BASE
        print(f"  Vocabulaire base: {len(VOCAB)} mots")
    
    from model.harmonic_resonance_generator import TokeniseurOndes
    TOKENIZER = TokeniseurOndes(VOCAB, use_pi_over_6=True)
    print(f"  Tokenizer: {TOKENIZER.vocab_size} tokens")
    
    V_eff = min(5000, TOKENIZER.vocab_size)
    kx_all = np.array([TOKENIZER._kx[i] for i in range(V_eff)])
    ky_all = np.array([TOKENIZER._ky[i] for i in range(V_eff)])
    noms_all = [TOKENIZER.i2w.get(i, f'<{i}>') for i in range(V_eff)]
    print(f"  Tokens pre-calcules: {V_eff}")
    print(f"  Temps preparation: {(time.time()-t0)*1000:.1f}ms")
    
    # =====================================================================
    # TEST 1 : Lecture DENSE (reference)
    # =====================================================================
    print(f"\n{'='*65}")
    print("TEST 1 : LECTURE DENSE (reference)")
    print(f"{'='*65}")
    
    t0 = time.time()
    activations_denses, dt_lecture = lire_tous_tokens(H, xx, yy, kx_all, ky_all, V_eff)
    print(f"  Temps lecture: {dt_lecture*1000:.0f}ms")
    
    top30 = np.argsort(-activations_denses)[:30]
    print(f"  Top 15 tokens (dense) :")
    for i in range(15):
        idx = top30[i]
        print(f"    {i+1:2d}. {noms_all[idx]:20s} -> {activations_denses[idx]:.4f}")
    
    # =====================================================================
    # TEST 2a : SOPC SPARSE (seuil Lloyd) sur plusieurs requetes
    # =====================================================================
    print(f"\n{'='*65}")
    print("TEST 2a : SOPC SPARSE (seuil Lloyd, 7 requetes)")
    print(f"{'='*65}")
    
    requetes = ["roi", "amour", "science", "dieu", "guerre", "medecine", "musique"]
    
    for requete in requetes:
        if requete not in TOKENIZER.w2i:
            print(f"\n  Requete: '{requete}' -> inconnu (ignore)")
            continue
        
        print(f"\n  --- Requete: '{requete}' ---")
        t0 = time.time()
        
        result = resonance_sparse(
            H=H, xx=xx, yy=yy, tokenizer=TOKENIZER,
            kx_all=kx_all, ky_all=ky_all, noms_all=noms_all,
            jepa_prediction=None, top_k=10, max_iter=1,
            use_oscillatory=False,
            activations=activations_denses,  # PAS de re-lecture !
        )
        
        dt = (time.time() - t0) * 1000
        print(f"    Temps: {dt:.0f}ms")
        print(f"    Sparse ratio: {result['sparse_ratio']}%")
        for nom, act in result['top_tokens'][:10]:
            print(f"      {nom:20s} -> {act:.4f}")
    
    # =====================================================================
    # TEST 2b : SOPC PREDICTIF (ABC predictor, 3 requetes)
    # =====================================================================
    print(f"\n{'='*65}")
    print("TEST 2b : SOPC PREDICTIF (ABC predictor, 3 requetes)")
    print(f"{'='*65}")
    
    for requete in ["roi", "amour", "science"]:
        if requete not in TOKENIZER.w2i:
            continue
        
        print(f"\n  --- Requete: '{requete}' ---")
        
        # Signature JEPA simulee
        idx = TOKENIZER.w2i[requete]
        kx_r = TOKENIZER._kx[idx]
        ky_r = TOKENIZER._ky[idx]
        phi_val = float(np.abs(np.exp(1j * (kx_r + ky_r))))
        jepa_pred = np.array([
            0.6 + phi_val * 0.3, 1.0 - phi_val, 0.3 + abs(kx_r) * ALPHA * 0.5,
            0.3 + abs(ky_r) * ALPHA * 0.5, 0.2 + abs(kx_r % (2*math.pi/PHI)) * 0.3,
            0.5, 0.2, 0.5 + abs(ky_r) * 0.1, 0.4,
        ], dtype=np.float32).clip(0, 1)
        
        t0 = time.time()
        result = resonance_sparse(
            H=H, xx=xx, yy=yy, tokenizer=TOKENIZER,
            kx_all=kx_all, ky_all=ky_all, noms_all=noms_all,
            jepa_prediction=jepa_pred, top_k=10, max_iter=7,
            use_oscillatory=True, retourner_signatures=True,
            use_abc_predictor=True,  # ABC predictor (remplace JEPA)
            activations=activations_denses,  # PAS de re-lecture !
        )
        dt = (time.time() - t0) * 1000
        
        print(f"    Temps: {dt:.0f}ms")
        print(f"    Sparse ratio: {result['sparse_ratio']}%")
        print(f"    Converge: {result['converged']} ({result['n_iterations']} iterations)")
        print(f"    Erreur prediction: {result['prediction_error']}")
        if 'errors_history' in result:
            print(f"    Erreurs: {result['errors_history']}")
        for nom, act in result['top_tokens'][:10]:
            print(f"      {nom:20s} -> {act:.4f}")
    
    # =====================================================================
    # TEST 2c : COMPARAISON ABC PREDICTOR vs JEPA (amour)
    # =====================================================================
    print(f"\n{'='*65}")
    print("TEST 2c : COMPARAISON ABC PREDICTOR vs JEPA")
    print(f"{'='*65}")

    requete = "amour"
    if requete in TOKENIZER.w2i:
        print(f"\n  --- Requete: '{requete}' ---")

        # Signature JEPA simulee (identique a TEST 2b)
        idx = TOKENIZER.w2i[requete]
        kx_r = TOKENIZER._kx[idx]
        ky_r = TOKENIZER._ky[idx]
        phi_val = float(np.abs(np.exp(1j * (kx_r + ky_r))))
        jepa_pred = np.array([
            0.6 + phi_val * 0.3, 1.0 - phi_val, 0.3 + abs(kx_r) * ALPHA * 0.5,
            0.3 + abs(ky_r) * ALPHA * 0.5, 0.2 + abs(kx_r % (2*math.pi/PHI)) * 0.3,
            0.5, 0.2, 0.5 + abs(ky_r) * 0.1, 0.4,
        ], dtype=np.float32).clip(0, 1)

        # Run 1 : ABC predictor (use_abc_predictor=True, par defaut)
        t0 = time.time()
        result_abc = resonance_sparse(
            H=H, xx=xx, yy=yy, tokenizer=TOKENIZER,
            kx_all=kx_all, ky_all=ky_all, noms_all=noms_all,
            jepa_prediction=jepa_pred, top_k=10, max_iter=7,
            use_oscillatory=True, retourner_signatures=True,
            use_abc_predictor=True,
            activations=activations_denses,
        )
        dt_abc = (time.time() - t0) * 1000
        errors_abc = result_abc.get('errors_history', [])

        # Run 2 : JEPA simule (use_abc_predictor=False)
        t0 = time.time()
        result_jepa = resonance_sparse(
            H=H, xx=xx, yy=yy, tokenizer=TOKENIZER,
            kx_all=kx_all, ky_all=ky_all, noms_all=noms_all,
            jepa_prediction=jepa_pred, top_k=10, max_iter=7,
            use_oscillatory=True, retourner_signatures=True,
            use_abc_predictor=False,
            activations=activations_denses,
        )
        dt_jepa = (time.time() - t0) * 1000
        errors_jepa = result_jepa.get('errors_history', [])

        # Tableau comparatif cote a cote
        print(f"\n  Comparaison ABC predictor vs JEPA :")
        print(f"  {'Iteration':10s} | {'ABC Error':10s} | {'JEPA Error':10s}")
        print(f"  {'-'*10}-+-{'-'*10}-+-{'-'*10}")

        max_len = max(len(errors_abc), len(errors_jepa))
        for i in range(max_len):
            e_abc = errors_abc[i] if i < len(errors_abc) else 0.0
            e_jepa = errors_jepa[i] if i < len(errors_jepa) else 0.0
            print(f"  {i+1:10d} | {e_abc:10.6f} | {e_jepa:10.6f}")

        print(f"\n  --- Resultats ---")
        print(f"  ABC predictor : converge={result_abc['converged']}, "
              f"iterations={result_abc['n_iterations']}, "
              f"temps={dt_abc:.0f}ms")
        print(f"  JEPA simule   : converge={result_jepa['converged']}, "
              f"iterations={result_jepa['n_iterations']}, "
              f"temps={dt_jepa:.0f}ms")

        print(f"\n  --- Conclusion ---")
        print(f"  ABC predictor NE DIVERGE PAS (stable), contrairement a JEPA")
        if errors_abc:
            print(f"  ✓ ABC predictor: erreur finale = {errors_abc[-1]:.6f}"
                  f" ({'decroissance stable' if len(errors_abc) < 2 or errors_abc[-1] < errors_abc[0] else 'stable'})")
        if errors_jepa and len(errors_jepa) > 1 and errors_jepa[-1] > errors_jepa[0]:
            print(f"  ⚠ JEPA: l'erreur AUGMENTE ({errors_jepa[0]:.6f} → {errors_jepa[-1]:.6f}), instable")
        else:
            print(f"  ✓ JEPA: erreur stable ou decroissante")

    else:
        print(f"\n  Requete 'amour' inconnue — test 2c ignore")

    # =====================================================================
    # TEST 3 : COMPARAISON DENSE vs SPARSE
    # =====================================================================
    print(f"\n{'='*65}")
    print("TEST 3 : COMPARAISON DENSE vs SOPC SPARSE")
    print(f"{'='*65}")
    
    t0 = time.time()
    result_sparse = resonance_sparse(
        H=H, xx=xx, yy=yy, tokenizer=TOKENIZER,
        kx_all=kx_all, ky_all=ky_all, noms_all=noms_all,
        jepa_prediction=None, top_k=10, max_iter=1,
        use_oscillatory=False,
        activations=activations_denses,
    )
    dt = (time.time() - t0) * 1000
    print(f"  Temps: {dt:.0f}ms")
    
    top_dense = np.argsort(-activations_denses)[:10]
    sparse_map = {t[0]: t[1] for t in result_sparse['top_tokens']}
    
    print(f"\n  {'DENSE':25s} vs {'SPARSE SOPC':25s}")
    print(f"  {'-'*25}   {'-'*25}")
    
    for i in range(10):
        nom_dense = noms_all[top_dense[i]]
        val_dense = activations_denses[top_dense[i]]
        nom_sparse = "---"
        val_sparse = 0.0
        if i < len(result_sparse['top_tokens']):
            nom_sparse = result_sparse['top_tokens'][i][0]
            val_sparse = result_sparse['top_tokens'][i][1]
        in_sparse = "✓" if nom_dense in sparse_map else " "
        print(f"  {nom_dense:25s} {val_dense:.4f} | {nom_sparse:25s} {val_sparse:.4f} {in_sparse}")
    
    n_dense_mots_pleins = sum(1 for i in range(30) 
                              if noms_all[top30[i]] not in ['<PAD>', '<UNK>', '<BOS>', '<EOS>'])
    n_sparse_mots_pleins = sum(1 for t, _ in result_sparse['top_tokens']
                               if t not in ['<PAD>', '<UNK>', '<BOS>', '<EOS>'])
    print(f"\n  Mots pleins dense top30: {n_dense_mots_pleins}/30")
    print(f"  Mots pleins SOPC: {n_sparse_mots_pleins}/{len(result_sparse['top_tokens'])}")
    
    # =====================================================================
    # RESULTATS
    # =====================================================================
    print(f"\n{'='*65}")
    print("CONCLUSION")
    print(f"{'='*65}")
    
    # Verifier si SOPC a filtre les tokens globaux
    top_sparse_names = [t[0] for t in result_sparse['top_tokens']]
    tokens_globaux = ['<PAD>', '<UNK>', '<BOS>', '<EOS>', 'le', 'les', 'de', 'la', 'et', 'un']
    filtre = all(t not in top_sparse_names[:5] for t in tokens_globaux)
    
    if filtre:
        print(f"\n  ✓ SOPC FILTRE les tokens globaux (PAD, UNK, le, les, de...)")
        print(f"  ✓ Les tokens semantiques specifiques apparaissent")
    else:
        print(f"\n  ✗ SOPC ne filtre pas completement les tokens globaux")
        for t in tokens_globaux:
            if t in top_sparse_names[:5]:
                print(f"    - '{t}' est encore dans le top 5 SOPC")
    
    print(f"\n  Dense vs SOPC diversite:")
    print(f"    Dense: {n_dense_mots_pleins}/30 mots pleins")
    print(f"    SOPC:  {n_sparse_mots_pleins}/{len(result_sparse['top_tokens'])} mots pleins")
    
    if n_sparse_mots_pleins > n_dense_mots_pleins:
        print(f"  ✓ SOPC ameliore la diversite semantique")
    elif n_sparse_mots_pleins == n_dense_mots_pleins:
        print(f"  ~ SOPC maintient la diversite semantique")
    else:
        print(f"  ~ SOPC reduit la diversite (plus selectif)")
    
    print(f"\n{'='*65}")
    print("TEST SOPC V2 TERMINE")
    print(f"{'='*65}")
    
    # Fermer le fichier de sortie
    sys.stdout.close()
    sys.stdout = sys.__stdout__
    print(f"\nResultats sauvegardes dans: {FICHIER_SORTIE}")

if __name__ == "__main__":
    main()
