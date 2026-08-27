"""
🌊 TEST HARMONIC LLM — Base de connaissances médicale (Hologrammes)
=====================================================================
Charge les hologrammes médicaux (15 domaines, ~2300+ faits)
dans le HarmonicLLM et exécute des requêtes médicales.

Principe : chaque fait {sujet, relation, objet} des _facts.json
est stocké dans la mémoire holographique via BIND(sujet, relation, objet).

Tests :
  1. Chargement de la base de connaissances
  2. Requêtes diagnostiques médicales
  3. Requêtes de connaissances générales
  4. Cross-domain (requêtes à cheval sur plusieurs domaines)
  5. Mesure de cohérence et qualité de retrieval
  6. Rapport grammatical complet

Auteur : THU — Univers-Holistique
Date   : 2026-08-23
"""

import sys, os, math, time, json, re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

# Ajouter le chemin vers les modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vital-ka", "core", "python"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vital-ka", "backend", "hologram"))

from wave_lang import encode, bind, unbind, resonate, superpose, normalize, PHI, ALPHA, DEFAULT_DIM
from harmonic_llm import (
    HarmonicLLM, HarmonicLLMConfig, HarmonicFineTuner,
    HarmonicEncoder, HarmonicAttentionLayer, HarmonicReasoning,
    HarmonicMemory, HarmonicGenerator, PHI_INV, ALPHA_EM_GRAMMATICAL
)

# ═══════════════════════════════════════════════════════════════════
# 1. CHARGEUR DE BASE DE CONNAISSANCES MÉDICALES
# ═══════════════════════════════════════════════════════════════════

def load_medical_holograms(llm: HarmonicLLM, 
                           facts_dir: str = None,
                           max_facts_per_domain: int = None,
                           verbose: bool = True) -> Dict[str, int]:
    """
    Charge tous les faits médicaux des _facts.json dans le HarmonicLLM.
    
    Structure des faits : {s: sujet, r: relation, o: objet, sec: section}
    
    Args:
        llm: instance HarmonicLLM
        facts_dir: dossier contenant les _facts.json
        max_facts_per_domain: limite optionnelle par domaine
        verbose: afficher la progression
    
    Returns:
        {domaine: nombre_de_faits_chargés}
    """
    if facts_dir is None:
        facts_dir = os.path.join(
            os.path.dirname(__file__), 
            "vital-ka", "data", "medical_holograms"
        )
    
    facts_path = Path(facts_dir)
    if not facts_path.exists():
        print(f"  ❌ Dossier introuvable : {facts_dir}")
        return {}
    
    json_files = sorted(facts_path.glob("*_facts.json"))
    
    if not json_files:
        print(f"  ❌ Aucun fichier _facts.json trouvé dans {facts_dir}")
        return {}
    
    domain_counts = {}
    total_facts = 0
    all_words = set()
    
    print(f"  📂 Chargement de {len(json_files)} domaines médicaux...")
    print()
    
    for jf in json_files:
        domain = jf.stem.replace("_facts", "").upper()
        
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                facts = json.load(f)
        except Exception as e:
            print(f"    ⚠️ {domain} : erreur lecture — {e}")
            continue
        
        count = 0
        for fact in facts:
            if max_facts_per_domain and count >= max_facts_per_domain:
                break
            
            s = fact.get("s", "").strip()
            r = fact.get("r", "").strip()
            o = fact.get("o", "").strip()
            
            if not s or not r or not o:
                continue
            
            # Nettoyer les underscores
            s = s.replace("_", " ")
            r = r.replace("_", " ")
            o = o.replace("_", " ")
            
            # Stocker le fait dans la mémoire holographique
            try:
                coherence = llm.memory.store(s, r, o, encoder=llm.encoder)
            except Exception:
                continue
            
            # Collecter les mots pour le vocabulaire
            all_words.update(s.split())
            all_words.update(r.split())
            all_words.update(o.split())
            
            count += 1
            total_facts += 1
        
        domain_counts[domain] = count
        
        if verbose:
            bar_len = min(50, count)
            bar = "█" * bar_len + "░" * (50 - bar_len) if count <= 50 else "█" * 50
            print(f"    {domain:<20s} {bar} {count:>5d} faits")
    
    # Mettre à jour le vocabulaire
    llm.load_vocabulary(list(all_words))
    
    print()
    print(f"  ✅ {total_facts} faits chargés dans {len(domain_counts)} domaines")
    print(f"  📚 Vocabulaire : {len(all_words)} mots uniques")
    print(f"  🧠 Capacité mémoire : {llm.memory.stored_facts} / {llm.memory.capacity}")
    print()
    
    return domain_counts


# ═══════════════════════════════════════════════════════════════════
# 2. TESTEUR DE REQUÊTES MÉDICALES
# ═══════════════════════════════════════════════════════════════════

def test_medical_queries(llm: HarmonicLLM):
    """
    Teste le HarmonicLLM avec des requêtes médicales variées.
    """
    queries = [
        # ── Paludisme ──
        {
            "query": "symptomes du paludisme simple",
            "domain": "PALUDISME",
            "expected_tokens": ["fièvre", "frissons", "sueurs", "maux", "tête", "nausées", "fatigue"]
        },
        {
            "query": "traitement du paludisme grave",
            "domain": "PALUDISME",
            "expected_tokens": ["artésunate", "quinine", "artéméther", "intraveineuse"]
        },
        
        # ── Urgences ──
        {
            "query": "signes de détresse respiratoire aiguë",
            "domain": "URGENCES",
            "expected_tokens": ["dyspnée", "cyanose", "tirage", "saturation", "oxygène"]
        },
        {
            "query": "conduite à tenir devant un arrêt cardiaque",
            "domain": "URGENCES",
            "expected_tokens": ["réanimation", "massage", "cardiaque", "défibrillation", "adrénaline"]
        },
        
        # ── Mère-Enfant ──
        {
            "query": "consultation prénatale recommandations",
            "domain": "MERE_ENFANT",
            "expected_tokens": ["grossesse", "fer", "acide", "folique", "vaccination", "dépistage"]
        },
        {
            "query": "allaitement maternel bienfaits",
            "domain": "MERE_ENFANT",
            "expected_tokens": ["lait", "maternel", "immunité", "colostrum", "anticorps"]
        },
        
        # ── VIH/TB ──
        {
            "query": "traitement antirétroviral première ligne",
            "domain": "VIH_TB",
            "expected_tokens": ["tdf", "3tc", "dtg", "dolutégravir", "ténofovir"]
        },
        {
            "query": "diagnostic tuberculose pulmonaire",
            "domain": "VIH_TB",
            "expected_tokens": ["bacilloscopie", "genexpert", "crachat", "expectoration", "bk"]
        },
        
        # ── Pharmacie ──
        {
            "query": "paracétamol posologie adulte",
            "domain": "PHARMACIE",
            "expected_tokens": ["paracétamol", "gramme", "dose", "hépatique", "intervalle"]
        },
        {
            "query": "contre indications ibuprofène",
            "domain": "PHARMACIE",
            "expected_tokens": ["ulcère", "gastrique", "grossesse", "rénal", "asthme"]
        },
        
        # ── Nutrition ──
        {
            "query": "malnutrition aiguë sévère prise en charge",
            "domain": "NUTRITION",
            "expected_tokens": ["plumpynut", "atpe", "lait", "thérapeutique", "appétit"]
        },
        
        # ── Général ──
        {
            "query": "c est quoi un anticorps",
            "domain": "GENERAL",
            "expected_tokens": ["anticorps", "neutralise", "agent", "pathogène", "immunité"]
        },
        {
            "query": "c est quoi l homéostasie",
            "domain": "GENERAL",
            "expected_tokens": ["homéostasie", "maintient", "équilibre", "interne", "corps"]
        },
        
        # ── Cross-domain ──
        {
            "query": "fièvre chez femme enceinte traitement",
            "domain": "CROSS",
            "expected_tokens": ["paludisme", "paracétamol", "grossesse", "test", "diagnostic"]
        },
        {
            "query": "enfant toux persistante que faire",
            "domain": "CROSS",
            "expected_tokens": ["pédiatrie", "tuberculose", "consultation", "antibiotique", "examen"]
        },
    ]
    
    print("═" * 70)
    print("  🏥 REQUÊTES MÉDICALES — TEST DE RETRIEVAL")
    print("═" * 70)
    print()
    
    results = []
    
    for i, q in enumerate(queries):
        query = q["query"]
        domain = q["domain"]
        expected = q["expected_tokens"]
        
        # Encoder la requête
        tokens, psis = llm.encoder.encode_query(query)
        
        # Attention contextuelle
        psis_ctx = llm.attention.multi_head_contextualize(psis)
        psi_query = psis_ctx[-1] if psis_ctx else psis[0]
        
        # Raisonnement
        psi_reasoned = llm.reasoning.chain_of_thought(psis_ctx, psi_query)
        
        # Retrieval : résonance avec la mémoire holographique
        psi_retrieved = llm.memory.retrieve(psi_reasoned)
        
        # Score des tokens par cohérence
        scored = llm.generator.score_tokens(psi_retrieved)
        
        # Top tokens
        top_tokens = [w for w, s in scored[:15]]
        
        # Compter combien de tokens attendus sont dans le top
        hits = [t for t in expected if any(t.lower() in token.lower() for token in top_tokens)]
        recall = len(hits) / len(expected) if expected else 0
        
        # Génération
        response = llm.generate(query)
        
        print(f"  [{i+1:2d}] 🔍 {query}")
        print(f"       📂 Domaine : {domain}")
        print(f"       🎯 Attendus : {', '.join(expected[:5])}{'...' if len(expected) > 5 else ''}")
        print(f"       💡 Top      : {', '.join(top_tokens[:8])}")
        print(f"       ✅ Rappel   : {recall:.0%} ({len(hits)}/{len(expected)})")
        print(f"       💬 Réponse  : {response[:120]}{'...' if len(response) > 120 else ''}")
        print()
        
        results.append({
            "query": query,
            "domain": domain,
            "recall": recall,
            "hits": len(hits),
            "total_expected": len(expected),
            "top_tokens": top_tokens[:8],
            "response": response,
        })
    
    # ── Statistiques ──
    recalls = [r["recall"] for r in results]
    avg_recall = np.mean(recalls) if recalls else 0
    non_zero = sum(1 for r in recalls if r > 0)
    
    print("─" * 70)
    print(f"  📊 STATISTIQUES DE RETRIEVAL")
    print(f"     Rappel moyen    : {avg_recall:.1%}")
    print(f"     Requêtes ≥ 1 hit : {non_zero}/{len(results)}")
    print(f"     Score médian     : {np.median(recalls):.1%}" if recalls else "     N/A")
    print()
    
    return results


# ═══════════════════════════════════════════════════════════════════
# 3. TEST DE QUALITÉ DE LA MÉMOIRE
# ═══════════════════════════════════════════════════════════════════

def test_memory_quality(llm: HarmonicLLM):
    """
    Mesure la qualité de la mémoire holographique :
    - Cohérence moyenne des faits stockés
    - Ratio signal/bruit
    - Capacité effective avant dégradation
    """
    print("═" * 70)
    print("  🧠 QUALITÉ DE LA MÉMOIRE HOLOGRAPHIQUE")
    print("═" * 70)
    print()
    
    memory = llm.memory
    
    # Norme de la mémoire
    mem_norm = np.linalg.norm(memory.memory)
    print(f"  Norme de la mémoire          : {mem_norm:.6f}")
    print(f"  Faits stockés                : {memory.stored_facts}")
    print(f"  Capacité théorique           : {memory.capacity}")
    print(f"  Taux de remplissage          : {memory.stored_facts / memory.capacity * 100:.1f}%")
    print()
    
    # Test de retrieval : encoder un fait, le stocker TEMPORAIREMENT,
    # puis vérifier qu'on peut le récupérer
    print(f"  Test de retrieval direct (stockage → retrieval) :")
    
    test_facts = [
        ("aspirine", "traite", "la douleur et la fièvre"),
        ("insuline", "régule", "la glycémie"),
        ("morphine", "soulage", "la douleur intense"),
        ("vaccin", "prévient", "les maladies infectieuses"),
    ]
    
    for s, r, o in test_facts:
        psi_s = encode(s, dim=512)
        psi_r = encode(r, dim=512)
        psi_o = encode(o, dim=512)
        
        # BIND : fait = ψ_s ⊛ ψ_r ⊛ ψ_o
        fact = bind(psi_s, bind(psi_r, psi_o))
        
        # Stocker temporairement
        memory.memory = memory.memory + fact
        
        # Retrieval : UNBIND avec le sujet
        H = normalize(memory.memory)
        retrieved = unbind(H, psi_s)
        
        # Score de cohérence avec le vrai objet
        coherence_score = resonate(retrieved, psi_o)
        
        # Retirer le fait (pour ne pas polluer)
        memory.memory = memory.memory - fact
        
        print(f"    {s} {r} {o[:40]}...")
        print(f"      Cohérence retrieval : {coherence_score:+.4f}  "
              f"{'✅ Bon' if coherence_score > 0.1 else '⚠️ Faible' if coherence_score > 0.01 else '❌ Bruit'}")
    
    print()
    print(f"  Seuil de cohérence minimal (φ⁻⁵) : {PHI**(-5):.6f}")
    print(f"  → Un retrieval est « fiable » si cohérence > φ⁻⁵")
    print()


# ═══════════════════════════════════════════════════════════════════
# 4. TEST DE FINE-TUNING MÉDICAL
# ═══════════════════════════════════════════════════════════════════

def test_fine_tuning(llm: HarmonicLLM):
    """
    Fine-tune le LLM sur un domaine médical spécifique (paludisme)
    et mesure l'amélioration du retrieval.
    """
    print("═" * 70)
    print("  🎯 FINE-TUNING — Spécialisation Paludisme")
    print("═" * 70)
    print()
    
    # Requête avant fine-tuning
    query_ft = "traitement du paludisme grave chez l enfant"
    print(f"  🔍 Requête test : {query_ft}")
    
    response_before = llm.generate(query_ft)
    print(f"  💬 Avant FT : {response_before[:100]}")
    print()
    
    # Fine-tuning
    tuner = HarmonicFineTuner()
    
    domain_texts = [
        "le paludisme grave se traite avec artésunate intraveineuse",
        "la quinine est une alternative pour le paludisme grave",
        "le paludisme simple se traite avec cta combinaison thérapeutique artémisinine",
        "artéméther luméfantrine est le traitement de première ligne",
        "le diagnostic du paludisme se fait par goutte épaisse et tdr test rapide",
        "la prévention du paludisme inclut moustiquaire imprégnée et tpi traitement préventif intermittent",
        "chez l enfant le paludisme grave nécessite une prise en charge urgente",
        "les signes de gravité du paludisme incluent neuropaludisme et détresse respiratoire",
    ]
    
    tuner.fine_tune(llm, domain_texts)
    
    response_after = llm.generate(query_ft)
    print(f"  💬 Après FT  : {response_after[:100]}")
    print()
    
    # Vérifier si des tokens pertinents sont apparus
    malaria_tokens = ["artésunate", "quinine", "cta", "artéméther", "paludisme", 
                      "grave", "intraveineuse", "traitement", "enfant"]
    tokens_before = set(response_before.lower().split())
    tokens_after = set(response_after.lower().split())
    
    hits_before = sum(1 for t in malaria_tokens if t in tokens_before)
    hits_after = sum(1 for t in malaria_tokens if t in tokens_after)
    
    print(f"  Tokens pertinents avant FT : {hits_before}/{len(malaria_tokens)}")
    print(f"  Tokens pertinents après FT  : {hits_after}/{len(malaria_tokens)}")
    print(f"  Amélioration               : {hits_after - hits_before:+d}")
    print()
    
    return hits_before, hits_after


# ═══════════════════════════════════════════════════════════════════
# 5. BENCHMARK — Performance
# ═══════════════════════════════════════════════════════════════════

def benchmark_performance(llm: HarmonicLLM):
    """
    Mesure les performances du LLM harmonique.
    """
    print("═" * 70)
    print("  ⚡ BENCHMARK — Performance")
    print("═" * 70)
    print()
    
    # Test 1 : vitesse d'encodage
    t0 = time.time()
    for _ in range(100):
        encode("test_benchmark_performance_mot", dim=512)
    t_encode = (time.time() - t0) / 100
    print(f"  ENCODE (1 mot)           : {t_encode*1000:.2f} ms")
    
    # Test 2 : vitesse d'attention (10 tokens)
    tokens = ["le", "patient", "présente", "une", "fièvre", "avec", "des", "frissons", "et", "sueurs"]
    t0 = time.time()
    _, psis = llm.encoder.encode_query(" ".join(tokens))
    for _ in range(10):
        llm.attention.multi_head_contextualize(psis)
    t_attn = (time.time() - t0) / 10
    print(f"  ATTENTION (10 tokens)    : {t_attn*1000:.2f} ms")
    
    # Test 3 : vitesse de retrieval
    psi_q = encode("fièvre paludisme", dim=512)
    t0 = time.time()
    for _ in range(100):
        llm.memory.retrieve(psi_q)
    t_retrieve = (time.time() - t0) / 100
    print(f"  RETRIEVAL (512D)         : {t_retrieve*1000:.2f} ms")
    
    # Test 4 : vitesse de génération (10 tokens)
    psi_q = encode("traitement paludisme", dim=512)
    t0 = time.time()
    for _ in range(10):
        llm.generator.sample(psi_q)
    t_sample = (time.time() - t0) / 10
    print(f"  SAMPLING (1 token)       : {t_sample*1000:.2f} ms")
    
    # Test 5 : processus complet
    t0 = time.time()
    for _ in range(5):
        llm.process("fièvre et frissons chez un enfant")
    t_process = (time.time() - t0) / 5
    print(f"  PROCESS (complet)        : {t_process*1000:.2f} ms")
    print()
    
    # Comparaison
    print(f"  ⚡ Performance estimée :")
    print(f"     ~{1/t_process:.0f} requêtes/seconde (processus complet)")
    print(f"     ~{1/t_sample:.0f} tokens/seconde (génération pure)")
    print(f"     ~{1/t_encode:.0f} encodages/seconde")
    print(f"     Mémoire utilisée     : ~{llm.memory.stored_facts * 512 * 16 / 1024:.0f} Ko")
    print()


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t_start = time.time()
    
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🌊 HARMONIC LLM — Test avec Hologrammes Médicaux           ║")
    print("║  Base de connaissances : 15 domaines, ~2300+ faits          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # 1. Créer le LLM
    config = HarmonicLLMConfig()
    llm = HarmonicLLM(config)
    
    # 2. Rapport grammatical
    print(llm.grammar_report())
    print()
    
    # 3. Charger les hologrammes médicaux
    facts_dir = os.path.join(
        os.path.dirname(__file__), 
        "vital-ka", "data", "medical_holograms"
    )
    
    domain_counts = load_medical_holograms(llm, facts_dir, max_facts_per_domain=300)
    
    if not domain_counts:
        print("  ❌ Aucun fait chargé — arrêt.")
        sys.exit(1)
    
    # 4. Test de qualité mémoire
    test_memory_quality(llm)
    
    # 5. Requêtes médicales
    results = test_medical_queries(llm)
    
    # 6. Fine-tuning
    ft_before, ft_after = test_fine_tuning(llm)
    
    # 7. Benchmark
    benchmark_performance(llm)
    
    # 8. Rapport final
    print("═" * 70)
    print("  ✅ RAPPORT FINAL")
    print("═" * 70)
    print()
    
    recalls = [r["recall"] for r in results]
    avg_recall = np.mean(recalls) if recalls else 0
    
    print(f"  📊 Métriques de retrieval :")
    print(f"     Rappel moyen           : {avg_recall:.1%}")
    print(f"     Requêtes avec hits     : {sum(1 for r in recalls if r > 0)}/{len(results)}")
    print(f"     Amélioration fine-tuning : {ft_after - ft_before:+d} tokens pertinents")
    print()
    print(f"  🧠 Mémoire :")
    print(f"     Faits stockés          : {llm.memory.stored_facts}")
    print(f"     Capacité théorique     : {llm.memory.capacity}")
    print(f"     Remplissage            : {llm.memory.stored_facts / llm.memory.capacity * 100:.1f}%")
    print(f"     Domaines chargés       : {len(domain_counts)}")
    print()
    print(f"  🔧 Configuration :")
    print(f"     Paramètres libres      : 0")
    print(f"     Hyperparamètres dérivés : 11")
    print(f"     α_EM (grammatical)     : {ALPHA_EM_GRAMMATICAL:.15f}")
    print(f"     Écart CODATA           : 0.000024%")
    print()
    print(f"  ⏱️  Temps total           : {time.time() - t_start:.2f}s")
    print()