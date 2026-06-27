#!/usr/bin/env python3
"""
test_sopc_reel.py — Test SOPC sur l'hologramme reel
====================================================
Charge ka_knowledge_base/hologramme.npy et compare :
  - Lecture DENSE (methode actuelle)
  - Lecture SOPC SPARSE (nouvelle methode)
  - Boucle predictive avec JEPA (si disponible)

Usage :
    set PYTHONIOENCODING=utf-8 && python test_sopc_reel.py
"""

import os
import sys
import math
import time
import numpy as np

# Ajouter les chemins
_PROJECT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _PROJECT)
sys.path.insert(0, os.path.join(_PROJECT, 'harmonic_training'))

# =========================================================================
# Imports SOPC
# =========================================================================
try:
    from engine.sopc_core import (
        resonance_sparse, sparse_read, compute_sparse_threshold,
        abc_kernel, mittag_leffler, ABCPhaseGate,
        PHI, ALPHA, B_1_PHI, K0, SEUIL_SPARSE_FACTOR
    )
    SOPC_OK = True
except ImportError as e:
    print(f"[ERREUR] Import SOPC echoue : {e}")
    SOPC_OK = False

# =========================================================================
# Imports hologramme
# =========================================================================
CHEMIN_HOLOGRAMME = os.path.join(_PROJECT, "ka_knowledge_base", "hologramme.npy")

# Importer le tokenizer
try:
    from model.vocabulaire_etendu import VOCABULAIRE_ETENDU
    VOCAB = VOCABULAIRE_ETENDU
    print(f"  [OK] Vocabulaire etendu : {len(VOCAB)} mots")
except ImportError:
    try:
        from model.harmonic_resonance_generator import VOCABULAIRE_BASE, TokeniseurOndes
        VOCAB = VOCABULAIRE_BASE
        print(f"  [INFO] Vocabulaire de base : {len(VOCAB)} mots")
    except ImportError as e:
        print(f"[ERREUR] Impossible de charger le vocabulaire : {e}")
        sys.exit(1)

try:
    from model.harmonic_resonance_generator import TokeniseurOndes
    TOKENIZER = TokeniseurOndes(VOCAB, use_pi_over_6=True)
    print(f"  [OK] Tokenizer cree : {TOKENIZER.vocab_size} tokens")
except Exception as e:
    print(f"[ERREUR] Tokenizer : {e}")
    sys.exit(1)


# =========================================================================
# Fonctions de test
# =========================================================================

def charger_hologramme():
    """Charge l'hologramme et prepare les donnees."""
    if not os.path.exists(CHEMIN_HOLOGRAMME):
        print(f"[ERREUR] Hologramme non trouve : {CHEMIN_HOLOGRAMME}")
        return None, None, None, None, None
    
    H = np.load(CHEMIN_HOLOGRAMME)
    print(f"\n{'='*65}")
    print(f"HOLOGRAMME CHARGE")
    print(f"{'='*65}")
    print(f"  Shape: {H.shape[0]}x{H.shape[1]}")
    print(f"  Type: {H.dtype}")
    print(f"  Energie totale: {np.sum(np.abs(H)):.0f}")
    print(f"  Taille: {os.path.getsize(CHEMIN_HOLOGRAMME)/1024:.1f} KB")
    
    nx, ny = H.shape
    x = np.linspace(-math.pi, math.pi, nx)
    y = np.linspace(-math.pi, math.pi, ny)
    xx, yy = np.meshgrid(x, y, indexing='ij')
    
    # Pre-calcul des kx, ky pour tous les tokens
    V_eff = min(5000, TOKENIZER.vocab_size)
    kx_all = np.array([TOKENIZER._kx[i] for i in range(V_eff)])
    ky_all = np.array([TOKENIZER._ky[i] for i in range(V_eff)])
    noms_all = [TOKENIZER.i2w.get(i, f'<{i}>') for i in range(V_eff)]
    
    print(f"  Tokens pre-calcules: {V_eff}")
    
    return H, xx, yy, (kx_all, ky_all, noms_all, V_eff)


def test_lecture_dense(H, xx, yy, kx_all, ky_all, noms_all, V_eff):
    """Lecture dense (reference — methode actuelle)."""
    print(f"\n{'='*65}")
    print("TEST 1 : LECTURE DENSE (reference)")
    print(f"{'='*65}")
    
    nx, ny = H.shape
    BATCH = 500
    activations = np.zeros(V_eff, dtype=np.float64)
    
    t0 = time.time()
    for start in range(0, V_eff, BATCH):
        end = min(start + BATCH, V_eff)
        bkx = kx_all[start:end]
        bky = ky_all[start:end]
        phase = (bkx[:, None, None] * xx[None, :, :] +
                 bky[:, None, None] * yy[None, :, :])
        onde_ref = np.exp(-1j * phase)
        corr = np.sum(H[None, :, :] * onde_ref, axis=(1, 2))
        activations[start:end] = np.abs(corr) / (nx * ny)
    dt = (time.time() - t0) * 1000
    
    top30 = np.argsort(-activations)[:30]
    print(f"  Temps: {dt:.1f} ms")
    print(f"  Top 15 tokens (dense) :")
    for i in range(15):
        idx = top30[i]
        print(f"    {i+1:2d}. {noms_all[idx]:15s} -> {activations[idx]:.4f}")
    
    return activations


def test_sopc_sparse(H, xx, yy, kx_all, ky_all, noms_all, V_eff, 
                     avec_jepa=False, requetes=None):
    """Test SOPC avec et sans JEPA."""
    print(f"\n{'='*65}")
    mode = "SPARSE (sans JEPA)" if not avec_jepa else "SPARSE + PREDICTIF (avec JEPA)"
    print(f"TEST 2 : SOPC {mode}")
    print(f"{'='*65}")
    
    if requetes is None:
        requetes = ["roi", "amour", "science", "dieu", "guerre", "medecine", "musique"]
    
    for requete in requetes:
        if requete not in TOKENIZER.w2i:
            print(f"\n  Requete: '{requete}' -> inconnu du tokenizer (ignore)")
            continue
        
        # Simulation d'une prediction JEPA si demande
        jepa_pred = None
        if avec_jepa:
            # Signature simulee : on utilise la categorie semantique du mot
            # pour generer une prediction coherente
            idx = TOKENIZER.w2i[requete]
            kx_r = TOKENIZER._kx[idx]
            ky_r = TOKENIZER._ky[idx]
            
            # Estimation grossiere d'une signature depuis (kx, ky)
            phi_val = float(np.abs(np.exp(1j * (kx_r + ky_r))))
            alpha_val = 1.0 - phi_val
            reasoning = min(1.0, abs(kx_r) * ALPHA)
            creativity = min(1.0, abs(ky_r) * ALPHA)
            math_val = min(1.0, abs(kx_r % (2.0 * math.pi / PHI)) * 0.3)
            
            jepa_pred = np.array([
                0.6 + phi_val * 0.3,   # phi
                0.2 + alpha_val * 0.3, # alpha
                0.3 + reasoning * 0.5, # reasoning
                0.3 + creativity * 0.5,# creativity
                0.2 + math_val * 0.5,  # math
                0.5,                    # factual
                0.2,                   # code
                0.5 + abs(ky_r) * 0.1, # emotion
                0.4,                   # temporal
            ], dtype=np.float32)
            jepa_pred = np.clip(jepa_pred, 0.0, 1.0)
        
        result = resonance_sparse(
            H=H, xx=xx, yy=yy, tokenizer=TOKENIZER,
            kx_all=kx_all, ky_all=ky_all, noms_all=noms_all,
            jepa_prediction=jepa_pred,
            requete=requete,
            top_k=10,
            max_iter=7,
            use_oscillatory=avec_jepa,
            retourner_signatures=avec_jepa,
        )
        
        print(f"\n  Requete: '{requete}'")
        print(f"    Mode: {result['mode']}")
        print(f"    Temps: {result['temps_ms']:.1f} ms")
        print(f"    Sparse ratio: {result['sparse_ratio']}%")
        print(f"    Converge: {result['converged']} ({result['n_iterations']} iterations)")
        if avec_jepa:
            print(f"    Erreur prediction: {result['prediction_error']}")
            if 'errors_history' in result:
                print(f"    Historique erreur: {result['errors_history']}")
        print(f"    Tokens SOPC:")
        for nom, act in result['top_tokens'][:8]:
            print(f"      {nom:15s} -> {act:.4f}")
    
    return result


def comparer_dense_vs_sparse(H, xx, yy, kx_all, ky_all, noms_all, V_eff, 
                             activations_denses):
    """Compare les resultats dense vs sparse cote a cote."""
    print(f"\n{'='*65}")
    print("TEST 3 : COMPARAISON DENSE vs SPARSE")
    print(f"{'='*65}")
    
    # SOPC sans JEPA
    result_sparse = resonance_sparse(
        H=H, xx=xx, yy=yy, tokenizer=TOKENIZER,
        kx_all=kx_all, ky_all=ky_all, noms_all=noms_all,
        jepa_prediction=None, top_k=10, use_oscillatory=False,
    )
    
    # Top dense
    top_dense = np.argsort(-activations_denses)[:10]
    
    print(f"\n  {'DENSE':20s} vs {'SPARSE SOPC':20s}")
    print(f"  {'-'*20}   {'-'*20}")
    
    # Mapper les indices sparse par activation
    sparse_map = {t[0]: t[1] for t in result_sparse['top_tokens']}
    
    for i in range(10):
        nom_dense = noms_all[top_dense[i]]
        val_dense = activations_denses[top_dense[i]]
        
        nom_sparse = "---"
        val_sparse = 0.0
        if i < len(result_sparse['top_tokens']):
            nom_sparse = result_sparse['top_tokens'][i][0]
            val_sparse = result_sparse['top_tokens'][i][1]
        
        in_sparse = "✓" if nom_dense in sparse_map else " "
        print(f"  {nom_dense:20s} {val_dense:.4f} | {nom_sparse:20s} {val_sparse:.4f} {in_sparse}")
    
    # Stats de diversite
    n_dense_mots_pleins = sum(1 for i in range(30) 
                              if noms_all[top_dense[i]] not in ['<PAD>', '<UNK>', '<BOS>', '<EOS>'])
    n_sparse_mots_pleins = sum(1 for t, _ in result_sparse['top_tokens']
                               if t not in ['<PAD>', '<UNK>', '<BOS>', '<EOS>'])
    
    print(f"\n  Mots pleins dans top 30 dense: {n_dense_mots_pleins}/30")
    print(f"  Mots pleins dans top SOPC: {n_sparse_mots_pleins}/{len(result_sparse['top_tokens'])}")
    print(f"  Sparse ratio: {result_sparse['sparse_ratio']}%")


def test_oscillatory_gate():
    """Test specifique du gate oscillatoire ABC."""
    print(f"\n{'='*65}")
    print("TEST 4 : GATE OSCILLATOIRE ABC")
    print(f"{'='*65}")
    
    gate = ABCPhaseGate()
    print(f"  Frequence fondamentale ω₀ = α/(1-α) = {gate.omega_0:.4f} (={PHI:.4f} = φ)")
    print(f"  Theta (contexte): ω_θ = ω₀/φ = {gate.theta_freq:.4f}")
    print(f"  Gamma (items):   ω_γ = ω₀·φ = {gate.gamma_freq:.4f}")
    print(f"  Ratio γ/θ = {gate.gamma_freq/gate.theta_freq:.4f} (= φ² = {PHI2:.4f})")
    
    # Simuler 100 pas
    valeurs = []
    for _ in range(100):
        v = gate.step()
        valeurs.append(v)
    
    n_actifs = sum(1 for v in valeurs if v > 0.01)
    print(f"\n  Sur 100 pas : {n_actifs} phases ouvertes (gate > 0.01)")
    print(f"  Taux d'ouverture: {n_actifs}%")
    
    phases = gate.get_phase_stats()
    print(f"  Phase finale: theta={phases['theta_phase']:.4f}, gamma={phases['gamma_phase']:.4f}")
    
    return gate


def test_noyau_abc():
    """Verification du noyau ABC."""
    print(f"\n{'='*65}")
    print("TEST 5 : NOYAU ABC (fondement fractionnaire)")
    print(f"{'='*65}")
    
    kernel = abc_kernel(20)
    
    print(f"  α = 1/φ = {ALPHA:.6f}")
    print(f"  B(α) = {B_1_PHI:.6f}")
    print(f"  K(0) = {kernel[0]:.6f}")
    print(f"  K(5) = {kernel[5]:.6f}")
    print(f"  K(10)= {kernel[10]:.6f}")
    
    # Verifier la decroissance en loi de puissance
    ratio = kernel[10] / kernel[5] if kernel[5] > 0 else 0
    expected = (5.0 / 10.0) ** (ALPHA + 1.0)
    print(f"  K(10)/K(5) = {ratio:.4f} (attendu ~{expected:.4f})")
    print(f"  Memoire non-locale: {kernel[10]/kernel[0]*100:.2f}% du poids a t=10")
    print(f"  → Decroissance en loi de puissance (pas exponentielle)")
    print(f"  → C'est ce qui donne la memoire longue au noyau ABC")


# =========================================================================
# MAIN
# =========================================================================

def main():
    print("=" * 65)
    print("TEST SOPC SUR HOLOGRAMME REEL")
    print("=" * 65)
    print(f"\n  PHI = {PHI:.6f}")
    print(f"  ALPHA = 1/PHI = {ALPHA:.6f}")
    print(f"  B(alpha) = {B_1_PHI:.6f}")
    print(f"  K0 = B(alpha) = {K0:.6f}")
    print(f"  Facteur seuil = K0 * PHI = {SEUIL_SPARSE_FACTOR:.6f}")
    print(f"  Seuil coherence = {K0 * 0.1:.6f}")
    
    if not SOPC_OK:
        print("\n[ERREUR] Module SOPC non disponible. Arret.")
        return
    
    # Test 5 : Noyau ABC
    test_noyau_abc()
    
    # Test 4 : Gate oscillatoire
    test_oscillatory_gate()
    
    # Charger l'hologramme
    data = charger_hologramme()
    if data[0] is None:
        return
    
    H, xx, yy, (kx_all, ky_all, noms_all, V_eff) = data
    
    # Test 1 : Lecture dense
    activations_denses = test_lecture_dense(H, xx, yy, kx_all, ky_all, noms_all, V_eff)
    
    # Test 2a : SOPC sparse (sans JEPA)
    test_sopc_sparse(H, xx, yy, kx_all, ky_all, noms_all, V_eff,
                     avec_jepa=False)
    
    # Test 2b : SOPC avec JEPA simule
    test_sopc_sparse(H, xx, yy, kx_all, ky_all, noms_all, V_eff,
                     avec_jepa=True,
                     requetes=["roi", "amour", "science"])
    
    # Test 3 : Comparaison directe
    comparer_dense_vs_sparse(H, xx, yy, kx_all, ky_all, noms_all, V_eff,
                             activations_denses)
    
    print(f"\n{'='*65}")
    print("TEST SOPC TERMINE")
    print("="*65)


if __name__ == "__main__":
    main()
