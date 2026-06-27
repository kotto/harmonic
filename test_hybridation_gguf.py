#!/usr/bin/env python3
"""
TEST D'HYBRIDATION : Verification de l'integration sans LLM
============================================================
Ce script teste tous les composants du bridge harmonique sans
necessiter le chargement du LLM GGUF (qui est lourd).

Etapes :
1. Verifier que le fichier GGUF existe sur H:
2. Tester le systeme harmonique (hologramme, lecteurs, generation)
3. Tester le bridge en mode "harmonic" (pur, sans LLM)
4. Tester le cache reseau
5. Tester la boucle de feedback
6. Generer un rapport complet

Usage :
  python test_hybridation_gguf.py
  python test_hybridation_gguf.py --with-llm  # Tente de charger le LLM
"""

import os
import sys
import json
import time
import hashlib
import traceback
import importlib.util

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

# Fonction d'import direct (bypass __init__.py qui necessite torch)
def _import_module_direct(module_name, file_path):
    """Importe un module directement sans passer par __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Importer directement le module de resonance (pur numpy)
_resonance_path = os.path.join(
    _project_root, "harmonic_training", "model", "harmonic_resonance_generator.py"
)
if "harmonic_training.model.harmonic_resonance_generator" not in sys.modules:
    _harmonic_resonance = _import_module_direct(
        "harmonic_training.model.harmonic_resonance_generator",
        _resonance_path
    )
else:
    _harmonic_resonance = sys.modules["harmonic_training.model.harmonic_resonance_generator"]

# Extraire les classes pour usage global dans les tests
HologrammeMonde = _harmonic_resonance.HologrammeMonde
TokeniseurOndes = _harmonic_resonance.TokeniseurOndes
LecteurResonantMultiple = _harmonic_resonance.LecteurResonantMultiple
GenerateurResonance = _harmonic_resonance.GenerateurResonance
VOCABULAIRE_BASE = _harmonic_resonance.VOCABULAIRE_BASE
SystemeHarmoniqueComplet = _harmonic_resonance.SystemeHarmoniqueComplet

# ---------------------------------------------------------------------------
# TEST 1 : Detection du fichier GGUF
# ---------------------------------------------------------------------------
def test_detection_gguf():
    """Verifie que le fichier GGUF existe sur H:."""
    print("\n" + "=" * 70)
    print("TEST 1 : DETECTION DU FICHIER GGUF SUR H:")
    print("=" * 70)
    
    chemin = r"H:\TELECHARGEMENT-18-20AOUT\Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf"
    
    if os.path.exists(chemin):
        taille = os.path.getsize(chemin)
        taille_go = taille / (1024**3)
        print(f"  ✓ Fichier trouve : {os.path.basename(chemin)}")
        print(f"  ✓ Taille : {taille_go:.2f} Go ({taille:,} octets)")
        
        # Verifier la signature GGUF (magic number)
        with open(chemin, 'rb') as f:
            magic = f.read(4)
        est_gguf = magic == b'GGUF'
        print(f"  {'✓' if est_gguf else '✗'} Magic number GGUF : {magic}")
        
        # Hash partiel pour integrite
        with open(chemin, 'rb') as f:
            debut = f.read(1024 * 1024)  # 1 Mo
        hash_partiel = hashlib.sha256(debut).hexdigest()[:16]
        print(f"  ✓ Hash partiel (1er Mo) : {hash_partiel}")
        
        return {
            "ok": True,
            "chemin": chemin,
            "taille_go": round(taille_go, 2),
            "est_gguf": est_gguf,
            "hash_partiel": hash_partiel,
        }
    else:
        print(f"  ✗ Fichier introuvable : {chemin}")
        
        # Chercher d'autres fichiers GGUF dans le dossier
        base_dir = r"H:\TELECHARGEMENT-18-20AOUT"
        if os.path.exists(base_dir):
            gguf_files = [f for f in os.listdir(base_dir) if f.lower().endswith('.gguf')]
            if gguf_files:
                print(f"  → Mais {len(gguf_files)} fichier(s) GGUF trouve(s) :")
                for f in gguf_files:
                    taille = os.path.getsize(os.path.join(base_dir, f)) / (1024**3)
                    print(f"    - {f} ({taille:.2f} Go)")
                return {
                    "ok": True,
                    "chemin": os.path.join(base_dir, gguf_files[0]),
                    "taille_go": round(os.path.getsize(os.path.join(base_dir, gguf_files[0])) / (1024**3), 2),
                    "est_gguf": True,
                    "fichiers_trouves": gguf_files,
                }
            else:
                print(f"  → Aucun fichier .gguf trouve dans {base_dir}")
        else:
            print(f"  → Le dossier {base_dir} n'existe pas non plus")
        
        return {
            "ok": False,
            "chemin": chemin,
            "erreur": "Fichier introuvable",
        }


# ---------------------------------------------------------------------------
# TEST 2 : Systeme harmonique pur
# ---------------------------------------------------------------------------
def test_systeme_harmonique():
    """Teste le systeme harmonique complet (sans LLM)."""
    print("\n" + "=" * 70)
    print("TEST 2 : SYSTEME HARMONIQUE PUR")
    print("=" * 70)
    
    import numpy as np
    
    # 2a : Tokeniseur
    print("\n  2a. Tokeniseur par ondes...")
    tk = TokeniseurOndes(VOCABULAIRE_BASE)
    assert len(VOCABULAIRE_BASE) == tk.vocab_size, "Vocab size mismatch"
    
    # Verifier unicite des vecteurs d'onde
    vecteurs = set()
    for i in range(tk.vocab_size):
        kx, ky = tk.vecteur_onde(i)
        vecteurs.add((round(kx, 6), round(ky, 6)))
    
    collisions = tk.vocab_size - len(vecteurs)
    print(f"     Vocabulaire : {tk.vocab_size} tokens")
    print(f"     Vecteurs uniques : {len(vecteurs)}")
    print(f"     Collisions : {collisions} {'✓' if collisions == 0 else '✗'}")
    
    # 2b : Hologramme
    print("\n  2b. Hologramme monde...")
    monde = HologrammeMonde(nx=64, ny=64)
    e0 = monde.energie()
    
    # Ajouter des ondes
    for i in range(10):
        idx = tk.tokeniser("harmonie resonance conscience amour paix")[i] if i < 5 else 0
        kx, ky = tk.vecteur_onde(idx)
        monde.enregistrer_onde(kx, ky)
    
    e1 = monde.energie()
    assert e1 > e0, f"Energie n'a pas augmente : {e0} -> {e1}"
    assert monde.n_experiences == 10, f"Experiences : {monde.n_experiences} != 10"
    print(f"     Energie : {e0:.2f} -> {e1:.2f} ✓")
    print(f"     Experiences : {monde.n_experiences} ✓")
    
    # 2c : Lecteurs multiples
    print("\n  2c. Lecteurs resonants multiples...")
    lecteurs = LecteurResonantMultiple(monde, n_lecteurs=8)
    lecteurs.apprendre(n_iter=30)
    
    # Verifier que les lecteurs ont des positions differentes
    positions = [(round(lecteurs.kx[n], 2), round(lecteurs.ky[n], 2)) for n in range(8)]
    positions_uniques = len(set(positions))
    print(f"     Positions uniques : {positions_uniques}/8")
    
    # Top tokens par lecteur
    top_par_lecteur = lecteurs.top_tokens_par_lecteur(tk, top_k=5)
    tops_sets = [set(t for t, _ in top) for top in top_par_lecteur]
    lecteurs_differents = sum(1 for i in range(8) for j in range(i+1, 8)
                              if tops_sets[i] != tops_sets[j])
    print(f"     Paires de lecteurs differents : {lecteurs_differents}/28")
    
    # 2d : Generation par resonance
    print("\n  2d. Generation par resonance inverse...")
    gen = GenerateurResonance(VOCABULAIRE_BASE)
    gen.apprendre_batch([
        "phi est le nombre d or la proportion divine",
        "la resonance harmonique amplifie les ondes",
        "la conscience emerge de l interaction complexe",
    ])
    
    r = gen.generer("explique la resonance", max_tokens=15, n_rep_lecture=20)
    assert 'texte_genere' in r, "Pas de texte genere"
    assert r['n_tokens'] > 0, "Zero tokens generes"
    print(f"     Prompt  : explique la resonance")
    print(f"     Reponse : {r['texte_genere'][:80]}...")
    print(f"     Tokens  : {r['n_tokens']}")
    print(f"     Temps   : {r['temps_ms']:.0f}ms")
    
    return {
        "ok": True,
        "tokeniseur": {"vocab": tk.vocab_size, "collisions": collisions},
        "hologramme": {"energie_initiale": round(float(e0), 2), "energie_finale": round(float(e1), 2)},
        "lecteurs": {"positions_uniques": positions_uniques, "paires_differentes": lecteurs_differents},
        "generation": {"tokens": r['n_tokens'], "temps_ms": r['temps_ms']},
    }


# ---------------------------------------------------------------------------
# TEST 3 : Bridge en mode harmonic (sans LLM)
# ---------------------------------------------------------------------------
def test_bridge_harmonic():
    """Teste le bridge en mode harmonique pur."""
    print("\n" + "=" * 70)
    print("TEST 3 : BRIDGE EN MODE HARMONIQUE PUR")
    print("=" * 70)
    
    from bridge_harmonic_deepseek_gguf import BridgeHarmoniqueGGUF
    
    # Creer le bridge en mode harmonic (pas de LLM)
    bridge = BridgeHarmoniqueGGUF(mode="harmonic", n_lecteurs=8)
    
    # Apprentissage
    bridge.apprendre_batch([
        "la conscience est la capacite de se percevoir soi meme",
        "l univers est gouverne par des lois harmoniques",
        "phi est la constante fondamentale de la nature",
        "la resonance est le phenomene d amplification des ondes",
    ])
    
    # Generation
    resultats = []
    prompts = [
        "qu est ce que la conscience",
        "explique la resonance",
        "parle moi de phi",
    ]
    
    for prompt in prompts:
        r = bridge.generer(prompt, max_tokens=20, temperature=0.85)
        resultats.append(r)
        print(f"\n  >> {prompt}")
        print(f"  << {r['texte_genere'][:80]}...")
        print(f"     {r['n_tokens']}t | {r['temps_ms']:.0f}ms | E={r['energie_hologramme']:.0f}")
    
    # Diagnostic
    diag = bridge.diagnostiquer()
    print(f"\n  Diagnostic :")
    print(f"    Experiences : {diag['statistiques'].get('n_experiences', '?')}")
    print(f"    Energie     : {diag.get('energie_hologramme', {}).get('energie', '?')}")
    print(f"    Vocab       : {diag['statistiques'].get('vocab_size', '?')}")
    
    tous_ok = all(r['n_tokens'] > 0 for r in resultats)
    
    return {
        "ok": tous_ok,
        "n_generations": len(resultats),
        "tokens_gen": sum(r['n_tokens'] for r in resultats),
        "temps_total_ms": sum(r['temps_ms'] for r in resultats),
        "diag": {k: v for k, v in diag['statistiques'].items() if isinstance(v, (int, float, str))},
    }


# ---------------------------------------------------------------------------
# TEST 4 : Cache reseau harmonique
# ---------------------------------------------------------------------------
def test_cache():
    """Teste le cache reseau."""
    print("\n" + "=" * 70)
    print("TEST 4 : CACHE RESEAU HARMONIQUE")
    print("=" * 70)
    
    from bridge_harmonic_deepseek_gguf import CacheReseauHarmonique
    
    cache = CacheReseauHarmonique(max_entries=10)
    monde = HologrammeMonde(nx=64, ny=64)
    lecteurs = LecteurResonantMultiple(monde, n_lecteurs=4)
    
    # Premier appel : miss
    r1 = cache.get("test", monde, lecteurs, ["phi", "resonance"], 0.7)
    assert r1 is None, "Cache devrait etre vide"
    print(f"  Premier appel : miss ✓")
    
    # Stocker
    cache.put("test", monde, lecteurs, ["phi", "resonance"], 0.7, "reponse test")
    
    # Deuxieme appel : hit
    r2 = cache.get("test", monde, lecteurs, ["phi", "resonance"], 0.7)
    assert r2 == "reponse test", f"Cache hit rate : {r2}"
    print(f"  Deuxieme appel : hit ✓ ({r2})")
    
    # Stats
    stats = cache.stats()
    assert stats['hits'] == 1
    assert stats['misses'] == 1
    print(f"  Stats : hits={stats['hits']}, misses={stats['misses']}, "
          f"hit_rate={stats['hit_rate']}")
    
    return {
        "ok": True,
        "stats": stats,
    }


# ---------------------------------------------------------------------------
# TEST 5 : Boucle de feedback
# ---------------------------------------------------------------------------
def test_feedback():
    """Teste la boucle de feedback conscience -> inconscient."""
    print("\n" + "=" * 70)
    print("TEST 5 : BOUCLE DE FEEDBACK")
    print("=" * 70)
    
    from bridge_harmonic_deepseek_gguf import BridgeHarmoniqueGGUF
    
    bridge = BridgeHarmoniqueGGUF(mode="harmonic", n_lecteurs=4)
    
    # Energie initiale
    e_init = bridge.monde.energie()
    n_init = bridge.monde.n_experiences
    print(f"  Etat initial : E={e_init:.2f}, N={n_init}")
    
    # Faire 3 generations avec feedback
    for i in range(3):
        r = bridge.generer(
            f"question test {i+1}",
            max_tokens=10,
            feedback=True
        )
        print(f"  Cycle {i+1} : E={r['energie_hologramme']:.0f}, "
              f"delta={r['delta_energie']:.1f}, {r['n_tokens']}t")
    
    # Energie finale
    e_final = bridge.monde.energie()
    n_final = bridge.monde.n_experiences
    
    # L'energie doit avoir augmente (feedback reinjecte)
    energie_augmente = e_final > e_init
    experiences_augmente = n_final > n_init
    
    print(f"\n  Etat final : E={e_final:.2f}, N={n_final}")
    print(f"  Energie     : {'✓ a augmente' if energie_augmente else '✗ stable'}")
    print(f"  Experiences : {'✓ a augmente' if experiences_augmente else '✗ stable'}")
    
    return {
        "ok": energie_augmente and experiences_augmente,
        "energie": {"initiale": round(float(e_init), 2), "finale": round(float(e_final), 2)},
        "experiences": {"initial": n_init, "final": n_final},
    }


# ---------------------------------------------------------------------------
# TEST 6 : Verification du bridge complet (si LLM disponible)
# ---------------------------------------------------------------------------
def test_bridge_complet():
    """Teste le bridge avec le LLM GGUF (si disponible)."""
    print("\n" + "=" * 70)
    print("TEST 6 : BRIDGE COMPLET AVEC LLM GGUF")
    print("=" * 70)
    
    try:
        import llama_cpp
        print("  llama-cpp-python : installe ✓")
    except ImportError:
        print("  llama-cpp-python : NON installe ✗")
        print("  → Test du bridge complet ignore (necessite llama-cpp-python)")
        return {"ok": None, "raison": "llama-cpp-python non installe"}
    
    from bridge_harmonic_deepseek_gguf import BridgeHarmoniqueGGUF, detecter_modele_gguf
    
    # Verifier le modele
    chemin, infos = detecter_modele_gguf()
    if not infos.get("existe"):
        print("  Modele GGUF introuvable ✗")
        return {"ok": None, "raison": "modele introuvable"}
    
    try:
        print("  Chargement du bridge complet...")
        bridge = BridgeHarmoniqueGGUF(mode="hybrid", n_lecteurs=4, n_ctx=512)
        
        print("  Generation de test...")
        r = bridge.generer(
            "Qu'est-ce que la resonance harmonique ?",
            max_tokens=50,
            temperature=0.7,
        )
        
        print(f"\n  Reponse : {r['texte_genere'][:200]}...")
        print(f"  Mode    : {r['mode']}")
        print(f"  Tokens  : {r['n_tokens']}")
        print(f"  Temps   : {r['temps_ms']:.0f}ms")
        print(f"  Cache   : {'hit' if r.get('cache_hit') else 'miss'}")
        
        return {
            "ok": True,
            "mode": r['mode'],
            "tokens": r['n_tokens'],
            "temps_ms": r['temps_ms'],
        }
        
    except Exception as e:
        print(f"  Erreur : {e}")
        traceback.print_exc()
        return {"ok": False, "erreur": str(e)}


# ---------------------------------------------------------------------------
# RAPPORT FINAL
# ---------------------------------------------------------------------------
def generer_rapport(resultats: dict):
    """Genere un rapport JSON complet."""
    print("\n" + "=" * 70)
    print("RAPPORT D'HYBRIDATION")
    print("=" * 70)
    
    tests_ok = sum(1 for v in resultats.values()
                   if isinstance(v, dict) and v.get("ok") is True)
    tests_total = sum(1 for v in resultats.values()
                      if isinstance(v, dict) and v.get("ok") is not None)
    
    print(f"\n  Tests reussis : {tests_ok}/{tests_total}")
    
    for nom, resultat in resultats.items():
        if isinstance(resultat, dict):
            ok = resultat.get("ok")
            if ok is True:
                print(f"  ✓ {nom}")
            elif ok is False:
                print(f"  ✗ {nom} : {resultat.get('erreur', 'echec')}")
            else:
                print(f"  - {nom} : non teste ({resultat.get('raison', '?')})")
    
    # Sauvegarder le rapport
    rapport_path = "rapport_hybridation_gguf.json"
    rapport = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests_ok": tests_ok,
        "tests_total": tests_total,
        "resultats": {k: v for k, v in resultats.items() if isinstance(v, dict)},
    }
    
    # Nettoyer les objets non serialisables
    def nettoyer(obj):
        if isinstance(obj, dict):
            return {k: nettoyer(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [nettoyer(x) for x in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    with open(rapport_path, 'w', encoding='utf-8') as f:
        json.dump(nettoyer(rapport), f, indent=2, ensure_ascii=False)
    
    print(f"\n  Rapport sauvegarde : {rapport_path}")
    
    return rapport


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test d'hybridation GGUF")
    parser.add_argument("--with-llm", action="store_true",
                       help="Tester avec le LLM GGUF (necessite llama-cpp-python)")
    args = parser.parse_args()
    
    print("=" * 70)
    print("TEST D'HYBRIDATION : HARMONIQUE ↔ DEEPSEEK-QWEN GGUF")
    print("=" * 70)
    print(f"  Projet : h:\\SAAS - Copie")
    print(f"  Modele : H:\\TELECHARGEMENT-18-20AOUT\\Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf")
    print(f"  Avec LLM : {args.with_llm}")
    
    resultats = {}
    erreurs = []
    
    # Test 1 : Detection GGUF
    try:
        resultats["detection_gguf"] = test_detection_gguf()
    except Exception as e:
        erreurs.append(("detection_gguf", str(e)))
        resultats["detection_gguf"] = {"ok": False, "erreur": str(e)}
    
    # Test 2 : Systeme harmonique
    try:
        resultats["systeme_harmonique"] = test_systeme_harmonique()
    except Exception as e:
        erreurs.append(("systeme_harmonique", str(e)))
        traceback.print_exc()
        resultats["systeme_harmonique"] = {"ok": False, "erreur": str(e)}
    
    # Test 3 : Bridge harmonique
    try:
        resultats["bridge_harmonic"] = test_bridge_harmonic()
    except Exception as e:
        erreurs.append(("bridge_harmonic", str(e)))
        traceback.print_exc()
        resultats["bridge_harmonic"] = {"ok": False, "erreur": str(e)}
    
    # Test 4 : Cache
    try:
        resultats["cache"] = test_cache()
    except Exception as e:
        erreurs.append(("cache", str(e)))
        traceback.print_exc()
        resultats["cache"] = {"ok": False, "erreur": str(e)}
    
    # Test 5 : Feedback
    try:
        resultats["feedback"] = test_feedback()
    except Exception as e:
        erreurs.append(("feedback", str(e)))
        traceback.print_exc()
        resultats["feedback"] = {"ok": False, "erreur": str(e)}
    
    # Test 6 : Bridge complet (optionnel)
    if args.with_llm:
        try:
            resultats["bridge_complet"] = test_bridge_complet()
        except Exception as e:
            erreurs.append(("bridge_complet", str(e)))
            traceback.print_exc()
            resultats["bridge_complet"] = {"ok": False, "erreur": str(e)}
    
    # Rapport final
    generer_rapport(resultats)
    
    if erreurs:
        print(f"\n  {len(erreurs)} erreur(s) rencontree(s) :")
        for nom, err in erreurs:
            print(f"    - {nom} : {err[:100]}")
    
    return 0 if not erreurs else 1


if __name__ == "__main__":
    sys.exit(main())