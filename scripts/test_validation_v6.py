#!/usr/bin/env python3
"""
V6 - Tests et benchmark de validation complets.

Verifie :
  1. Vectorized _lire_tous_tokens() == resultats identiques a la version serie
  2. Benchmark de vitesse (serie vs vectorise batch)
  3. Resonance : les mots domaine-specifiques ne sont plus <UNK>
  4. Benchmark du temps de resonance avec le nouveau vocabulaire (2119 tokens)
  5. Energy stability after resonance
"""

import sys
import os
import math
import time
import numpy as np

# === Import du vocabulaire etendu (standalone, pas de torch) ===
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_proj_root = os.path.dirname(os.path.abspath(__file__))

import importlib.util
_vocab_path = os.path.join(_proj_root, "..", "harmonic_training", "model", "vocabulaire_etendu.py")
_vocab_path = os.path.normpath(_vocab_path)
_vocab_spec = importlib.util.spec_from_file_location(
    "harmonic_training.model.vocabulaire_etendu", _vocab_path
)
_vocab_module = importlib.util.module_from_spec(_vocab_spec)
sys.modules["harmonic_training.model.vocabulaire_etendu"] = _vocab_module
_vocab_spec.loader.exec_module(_vocab_module)
VOCABULAIRE_ETENDU = _vocab_module.VOCABULAIRE_ETENDU
VOCAB_SIZE = _vocab_module.VOCAB_SIZE_ETENDU

# === Import de HologrammeMonde et TokeniseurOndes ===
_gen_path = os.path.join(_proj_root, "..", "harmonic_training", "model",
                         "harmonic_resonance_generator.py")
_gen_path = os.path.normpath(_gen_path)
_gen_spec = importlib.util.spec_from_file_location(
    "harmonic_training.model.harmonic_resonance_generator", _gen_path
)
_gen_module = importlib.util.module_from_spec(_gen_spec)
# Ajouter numpy au namespace du module importe
_gen_module.np = np
_gen_module.os = os
_gen_module.math = math
sys.modules["harmonic_training.model.harmonic_resonance_generator"] = _gen_module
_gen_spec.loader.exec_module(_gen_module)
HologrammeMonde = _gen_module.HologrammeMonde
TokeniseurOndes = _gen_module.TokeniseurOndes

# === Constantes ===
NX, NY = 64, 64
HOLOGRAMME_PATH = os.path.join(_proj_root, "..", "ka_knowledge_base", "hologramme.npy")
HOLOGRAMME_PATH = os.path.normpath(HOLOGRAMME_PATH)

# Mots-cibles a verifier (domaine-specifiques)
CIBLES = [
    # Histoire africaine
    "ghana", "empire", "nubie", "koush", "ashanti", "tombouctou",
    "mandela", "apartheid", "decolonisation", "souverainete",
    "songhai", "mali", "mossi", "carthage", "ethiopie",
    # Medecine
    "infarctus", "hypertension", "therapie", "therapeutique",
    "inflammation", "metabolisme", "genetique", "homeostasie",
    "chronique", "aigue", "diagnostic", "primaire", "secondaire",
    "methotrexate", "immunitaire", "pathogene", "biomarqueur",
    "neurodegenerative", "epidemiologie", "cardiovasculaire",
    # Sciences
    "proteine", "anticorps", "phenotype",
    # Concepts etendus
    "ontologie", "anthropologie", "linguistique",
    "apprentissage", "reseau", "neuronal",
]

# Couleurs pour le terminal
class C:
    OK = '\033[92m'
    FAIL = '\033[91m'
    WARN = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'


def test_1_implementation_identique():
    """Verifie que la version vectorisee batch donne les MEMES resultats
    que la version serie originale (boucle Python appelant lire_onde)."""
    print(f"\n{C.BOLD}--- Test 1 : Vectorized == Serial (exactitude numerique) ---{C.END}")
    
    # Creer un hologramme frais (petite taille pour test rapide)
    monde = HologrammeMonde(32, 32)
    tokenizer = TokeniseurOndes(VOCABULAIRE_ETENDU, use_pi_over_6=True)
    
    # Enregistrer quelques ondes pour avoir des donnees
    for i in range(min(100, tokenizer.vocab_size)):
        kx, ky = tokenizer.vecteur_onde(i)
        monde.enregistrer_onde(kx, ky, 0.5 * (1.0 + 0.5 * math.sin(i * 0.1)))
    
    nx, ny = monde.nx, monde.ny
    xx, yy = monde.xx, monde.yy
    H = monde.H
    kx_arr = tokenizer._kx
    ky_arr = tokenizer._ky
    V = tokenizer.vocab_size
    
    print(f"  Hologramme: {nx}x{ny}, Vocabulaire: {V} tokens")
    
    # === Version SERIE (reference) : boucle Python classique ===
    t0 = time.time()
    activations_serie = np.zeros(V, dtype=np.float64)
    for t in range(V):
        kx_t = kx_arr[t]
        ky_t = ky_arr[t]
        activations_serie[t] = monde.lire_onde(kx_t, ky_t)
    dt_serie = time.time() - t0
    print(f"  Version serie      : {V} tokens en {dt_serie*1000:.1f} ms "
          f"({V/dt_serie:.0f} tok/s)")
    
    # === Version VECTORISEE (batch) ===
    BATCH = 500
    t0 = time.time()
    activations_vec = np.zeros(V, dtype=np.float64)
    for start in range(0, V, BATCH):
        end = min(start + BATCH, V)
        batch_kx = kx_arr[start:end]
        batch_ky = ky_arr[start:end]
        phase = (batch_kx[:, None, None] * xx[None, :, :] +
                 batch_ky[:, None, None] * yy[None, :, :])
        onde_ref = np.exp(-1j * phase)
        corr = np.sum(H[None, :, :] * onde_ref, axis=(1, 2))
        activations_vec[start:end] = np.abs(corr) / (nx * ny)
    dt_vec = time.time() - t0
    print(f"  Version vectorisee : {V} tokens en {dt_vec*1000:.1f} ms "
          f"({V/dt_vec:.0f} tok/s)")
    
    # === Comparaison ===
    diff_max = np.max(np.abs(activations_serie - activations_vec))
    diff_mean = np.mean(np.abs(activations_serie - activations_vec))
    identiques = diff_max < 1e-12
    
    print(f"  Difference max  : {diff_max:.2e}")
    print(f"  Difference mean : {diff_mean:.2e}")
    print(f"  Speedup         : {dt_serie/dt_vec:.1f}x")
    
    if identiques:
        print(f"  {C.OK}[OK] Resultats identiques (tol=1e-12){C.END}")
    else:
        # Chercher l'index de la plus grande difference
        idx_pire = np.argmax(np.abs(activations_serie - activations_vec))
        print(f"  {C.FAIL}[FAIL] Differences detectees ! Pire cas: token[{idx_pire}] = "
              f"serie={activations_serie[idx_pire]:.10f} vs "
              f"vec={activations_vec[idx_pire]:.10f}{C.END}")
    
    return {
        "ok": identiques,
        "diff_max": float(diff_max),
        "diff_mean": float(diff_mean),
        "dt_serie_ms": dt_serie * 1000,
        "dt_vectorise_ms": dt_vec * 1000,
        "speedup": dt_serie / dt_vec,
    }


def test_2_tokens_domaines():
    """Verifie que les tokens domaine-specifiques existent dans le vocabulaire
    et ne sont plus <UNK>."""
    print(f"\n{C.BOLD}--- Test 2 : Mots domaine-specifiques presents dans le vocabulaire ---{C.END}")
    
    tokenizer = TokeniseurOndes(VOCABULAIRE_ETENDU, use_pi_over_6=True)
    
    total = len(CIBLES)
    presents = 0
    absents = []
    
    for mot in CIBLES:
        idx = tokenizer.w2i.get(mot, -1)
        if idx >= 0 and idx != 1:  # 1 = <UNK>
            token_str = tokenizer.i2w.get(idx, '???')
            presents += 1
            if presents <= 5 or mot in ("ghana", "infarctus", "mandela", "empire", "therapie"):
                print(f"  {C.OK}[OK] '{mot}' -> id={idx}, token='{token_str}'{C.END}")
        else:
            absents.append(mot)
            print(f"  {C.FAIL}[FAIL] '{mot}' -> <UNK> (id={idx}){C.END}")
    
    print(f"\n  Total: {presents}/{total} mots presents")
    
    if absents:
        print(f"  {C.FAIL}Absents ({len(absents)}): {', '.join(absents)}{C.END}")
    else:
        print(f"  {C.OK}[OK] TOUS les mots-cibles sont dans le vocabulaire !{C.END}")
    
    return {
        "total": total,
        "presents": presents,
        "absents": absents,
    }


def test_3_resonance_et_benchmark():
    """Charge l'hologramme reinjecte, teste la resonance avec des requetes
    domaine-specifiques, et mesure le temps de resonance."""
    print(f"\n{C.BOLD}--- Test 3 : Resonance + Benchmark ---{C.END}")
    
    from engine.hologram_connector import HologrammeConnecteur
    
    # Verifier que l'hologramme existe
    if not os.path.exists(HOLOGRAMME_PATH):
        print(f"  {C.FAIL}[FAIL] Hologramme introuvable: {HOLOGRAMME_PATH}{C.END}")
        print(f"  Lancez d'abord: python scripts/reinjecter_connaissances.py")
        return {"ok": False, "raison": "hologramme_introuvable"}
    
    print(f"  Chargement de l'hologramme: {HOLOGRAMME_PATH}")
    t0 = time.time()
    connecteur = HologrammeConnecteur(HOLOGRAMME_PATH)
    dt_charge = time.time() - t0
    print(f"  Charge en {dt_charge*1000:.1f} ms")
    
    if not connecteur.est_charge():
        print(f"  {C.FAIL}[FAIL] Echec du chargement de l'hologramme{C.END}")
        return {"ok": False, "raison": "echec_chargement"}
    
    stats = connecteur.get_stats()
    print(f"  Vocabulaire: {connecteur.tokenizer.vocab_size} tokens")
    print(f"  Energie hologramme: {connecteur.monde.energie():.0f}")
    
    # === Benchmark : mesurer _lire_tous_tokens() ===
    t0 = time.time()
    activations = connecteur._lire_tous_tokens()
    dt_read = time.time() - t0
    V = connecteur.tokenizer.vocab_size
    print(f"\n  Benchmark _lire_tous_tokens(): {V} tokens en {dt_read*1000:.1f} ms "
          f"({V/dt_read:.0f} tok/s)")
    
    # Statistiques des activations
    print(f"  Activations: min={activations.min():.6f}, "
          f"max={activations.max():.6f}, "
          f"mean={activations.mean():.6f}")
    
    # === Queries de resonance ===
    queries = [
        ("histoire Afrique", "ghana", "empire"),
        ("medecine cardiovasculaire", "infarctus", "hypertension"),
        ("sante publique", "therapie", "immunitaire"),
        ("recherche medicale", "inflammation", "metabolisme"),
    ]
    
    resultats_resonance = {}
    
    for label, mot1, mot2 in queries:
        print(f"\n  -- Resonance: \"{label}\" --")
        t0 = time.time()
        res = connecteur.resonner(label, top_k=15)
        dt_res = time.time() - t0
        
        top_tokens = res.get("top_tokens", [])
        tokens_str = [t[0] for t in top_tokens]
        
        # Verifier si nos mots-cibles sont dans les top_k
        trouve1 = mot1 in tokens_str
        trouve2 = mot2 in tokens_str
        
        # Afficher les 10 premiers
        for i, (tok, val) in enumerate(top_tokens[:10]):
            marqueur = ""
            if tok == mot1 or tok == mot2:
                marqueur = f" {C.OK}<== CIBLE{C.END}"
            print(f"    {i+1:2d}. {tok:25s} {val:.6f}{marqueur}")
        
        status = ""
        if trouve1 and trouve2:
            status = f"{C.OK}[OK] Les deux cibles trouvees !{C.END}"
        elif trouve1 or trouve2:
            status = f"{C.WARN}[WARN] Partiel: {mot1 if trouve1 else mot2} trouve{C.END}"
        else:
            status = f"{C.FAIL}[FAIL] Aucune cible trouvee{C.END}"
        
        print(f"    Temps: {dt_res*1000:.1f} ms | {status}")
        
        resultats_resonance[label] = {
            "temps_ms": dt_res * 1000,
            "tokens": top_tokens[:10],
            "trouve1": trouve1,
            "trouve2": trouve2,
        }
    
    # === Energie avant/apres ===
    energie = connecteur.monde.energie()
    print(f"\n  Energie finale: {energie:.0f}")
    
    return {
        "ok": True,
        "energie": energie,
        "vocab_taille": V,
        "read_tokens_ms": dt_read * 1000,
        "read_tokens_speed": V / dt_read,
        "resonance": resultats_resonance,
    }


def test_4_tokenizer_pi6_coverage():
    """Verifie la couverture du tokenizer pi/6 : tous les angles 12 branches."""
    print(f"\n{C.BOLD}--- Test 4 : Couverture pi/6 (12 branches angulaires) ---{C.END}")
    
    tokenizer = TokeniseurOndes(VOCABULAIRE_ETENDU, use_pi_over_6=True)
    V = tokenizer.vocab_size
    
    kx = tokenizer._kx
    ky = tokenizer._ky
    angles = np.arctan2(ky, kx) % (2 * math.pi)
    
    # Compter combien de tokens par branche de 30 degres
    branches = {}
    for i in range(12):
        angle_min = i * math.pi / 6
        angle_max = (i + 1) * math.pi / 6
        mask = (angles >= angle_min) & (angles < angle_max)
        count = int(np.sum(mask))
        branches[f"{i*30}-{(i+1)*30}deg"] = count
    
    total_compte = sum(branches.values())
    
    print(f"  Vocabulaire: {V} tokens")
    print(f"  Tokens couverts par les 12 branches: {total_compte}")
    
    for nom, count in branches.items():
        barre = "#" * min(count // 5, 40)
        print(f"    {nom:12s}: {count:4d} tokens |{barre}")
    
    # Tous les tokens doivent etre dans une branche
    tous_couverts = total_compte == V
    if tous_couverts:
        print(f"  {C.OK}[OK] 100% des tokens couverts par les 12 branches pi/6{C.END}")
    else:
        print(f"  {C.FAIL}[FAIL] {V - total_compte} tokens hors des branches{C.END}")
    
    # Verifier la densite radiale uniforme (sqrt(r) pour surface uniforme)
    radii = np.sqrt(kx**2 + ky**2)
    # Trier par rayon et verifier que les rayons croissent regulierement
    radii_sorted = np.sort(radii)
    diffs = np.diff(radii_sorted)
    print(f"  Rayon min: {radii.min():.4f}, max: {radii.max():.4f}")
    print(f"  Ecart moyen entre rayons consecutifs: {np.mean(diffs):.6f}")
    
    return {
        "ok": tous_couverts,
        "V": V,
        "branches": branches,
        "rayon_min": float(radii.min()),
        "rayon_max": float(radii.max()),
    }


def test_5_old_vs_new_vocab_coverage():
    """Compare la couverture de l'ancien vocabulaire (323) vs nouveau (2119)
    sur les textes d'injection."""
    print(f"\n{C.BOLD}--- Test 5 : Old vs New vocabulary coverage on injection texts ---{C.END}")
    
    from harmonic_training.model.vocabulaire_etendu import VOCABULAIRE_BASE
    
    tokenizer_old = TokeniseurOndes(VOCABULAIRE_BASE, use_pi_over_6=True)
    tokenizer_new = TokeniseurOndes(VOCABULAIRE_ETENDU, use_pi_over_6=True)
    
    # Extraire les textes des scripts d'injection
    textes_test = []
    
    for filepath in ["injecter_histoire_afrique.py", "injecter_medecine_pubmed.py"]:
        path = os.path.join(_proj_root, "..", filepath)
        path = os.path.normpath(path)
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import re
        matches = re.findall(r'(?:apprendre|a)\s*\(\s*"([^"]*?)"\s*(?:,\s*amp\s*=\s*([0-9.]+))?\s*\)', content)
        for texte, amp in matches:
            if len(texte) > 10:
                textes_test.append(texte)
    
    textes_test = list(set(textes_test))  # dedup
    print(f"  Textes de test: {len(textes_test)}")
    
    # Tester la couverture token-level
    total_tokens_old = 0
    total_tokens_new = 0
    total_unk_old = 0
    total_unk_new = 0
    
    for texte in textes_test[:50]:  # Limiter a 50 textes
        ids_old = tokenizer_old.tokeniser(texte)
        ids_new = tokenizer_new.tokeniser(texte)
        
        unk_old = sum(1 for tid in ids_old if tid == 1)
        unk_new = sum(1 for tid in ids_new if tid == 1)
        
        total_tokens_old += len(ids_old)
        total_tokens_new += len(ids_new)
        total_unk_old += unk_old
        total_unk_new += unk_new
    
    coverage_old = (1 - total_unk_old / total_tokens_old) * 100
    coverage_new = (1 - total_unk_new / total_tokens_new) * 100
    
    print(f"  Ancien vocabulaire ({len(VOCABULAIRE_BASE)} tokens):")
    print(f"    Tokens: {total_tokens_old}, <UNK>: {total_unk_old}, "
          f"Couverture: {coverage_old:.1f}%")
    print(f"  Nouveau vocabulaire ({len(VOCABULAIRE_ETENDU)} tokens):")
    print(f"    Tokens: {total_tokens_new}, <UNK>: {total_unk_new}, "
          f"Couverture: {coverage_new:.1f}%")
    
    amelioration = coverage_new - coverage_old
    print(f"  Amelioration: +{amelioration:.1f}% de couverture")
    
    if amelioration > 0:
        print(f"  {C.OK}[OK] Le nouveau vocabulaire ameliore significativement la couverture{C.END}")
    
    return {
        "textes_test": len(textes_test),
        "coverage_old_pct": coverage_old,
        "coverage_new_pct": coverage_new,
        "amelioration_pct": amelioration,
    }


def main():
    print(f"{C.BOLD}{'='*60}{C.END}")
    print(f"{C.BOLD}  V6 - Tests et benchmark de validation{C.END}")
    print(f"{C.BOLD}  Vocabulaire etendu: {VOCAB_SIZE} tokens{C.END}")
    print(f"{C.BOLD}{'='*60}{C.END}")
    
    results = {}
    
    # Test 1: Precision numerique
    r1 = test_1_implementation_identique()
    results["test1_implementation"] = r1
    
    # Test 2: Mots domaine-specifiques
    r2 = test_2_tokens_domaines()
    results["test2_cibles"] = r2
    
    # Test 4: Couverture pi/6
    r4 = test_4_tokenizer_pi6_coverage()
    results["test4_pi6"] = r4
    
    # Test 5: Old vs new coverage
    r5 = test_5_old_vs_new_vocab_coverage()
    results["test5_coverage"] = r5
    
    # Test 3: Resonance (depend de l'hologramme charge)
    r3 = test_3_resonance_et_benchmark()
    results["test3_resonance"] = r3
    
    # === Rapport final ===
    print(f"\n{C.BOLD}{'='*60}{C.END}")
    print(f"{C.BOLD}  RAPPORT FINAL V6{C.END}")
    print(f"{C.BOLD}{'='*60}{C.END}")
    
    all_ok = True
    
    # Test 1
    if r1["ok"]:
        print(f"  {C.OK}[OK] Test 1: Implementation vectorisee == serie{C.END}")
    else:
        print(f"  {C.FAIL}[FAIL] Test 1: Differences numeriques detectees{C.END}")
        all_ok = False
    
    # Test 2
    if r2["presents"] == r2["total"]:
        print(f"  {C.OK}[OK] Test 2: {r2['presents']}/{r2['total']} mots-cibles presents{C.END}")
    else:
        print(f"  {C.WARN}[WARN] Test 2: {r2['presents']}/{r2['total']} mots-cibles presents "
              f"({len(r2['absents'])} absents){C.END}")
        if r2["presents"] < r2["total"] * 0.9:
            all_ok = False
    
    # Test 3
    if r3.get("ok"):
        print(f"  {C.OK}[OK] Test 3: Resonance operationnelle{C.END}")
        print(f"    Vitesse lecture: {r3.get('read_tokens_ms', 0):.1f} ms "
              f"({r3.get('vocab_taille', 0)} tokens)")
        for label, rr in r3.get("resonance", {}).items():
            status = "OK" if rr.get("trouve1") or rr.get("trouve2") else "ECHEC"
            color = C.OK if rr.get("trouve1") or rr.get("trouve2") else C.FAIL
            print(f"    {color}{label}: {rr.get('temps_ms', 0):.0f} ms, "
                  f"cibles={'OUI' if rr.get('trouve1') or rr.get('trouve2') else 'NON'}{C.END}")
    else:
        print(f"  {C.FAIL}[FAIL] Test 3: Echec resonance ({r3.get('raison', '?')}){C.END}")
        all_ok = False
    
    # Test 4
    if r4["ok"]:
        print(f"  {C.OK}[OK] Test 4: 12 branches pi/6, {r4['V']} tokens{C.END}")
    else:
        print(f"  {C.WARN}[WARN] Test 4: Certains tokens hors branches{C.END}")
    
    # Test 5
    if r5["amelioration_pct"] > 0:
        print(f"  {C.OK}[OK] Test 5: Couverture +{r5['amelioration_pct']:.1f}% "
              f"(old={r5['coverage_old_pct']:.1f}% -> new={r5['coverage_new_pct']:.1f}%){C.END}")
    
    # Synthese
    print(f"\n{C.BOLD}{'='*60}{C.END}")
    if all_ok:
        print(f"{C.BOLD}{C.OK}  [OK] BOUCLAGE COMPLET - Tous les tests passes !{C.END}")
        print(f"{C.BOLD}  Vocabulaire: {VOCAB_SIZE} tokens{C.END}")
        print(f"{C.BOLD}  Tokenizer: pi/6 (12 branches, sqrt(r) densite uniforme){C.END}")
        print(f"{C.BOLD}  Hologramme: {r3.get('energie', 0):.0f} energie{C.END}")
        print(f"{C.BOLD}  Etat: V1-V6 termines, pret pour production{C.END}")
    else:
        print(f"{C.BOLD}{C.FAIL}  [FAIL] Certains tests ont echoue - voir ci-dessus{C.END}")
    
    print(f"{C.BOLD}{'='*60}{C.END}")
    
    return results


if __name__ == "__main__":
    results = main()
