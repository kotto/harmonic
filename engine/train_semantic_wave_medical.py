"""
🌊 TRAIN SEMANTIC WAVE — 62K paires médicales
===============================================
Entraîne le SemanticWaveEmbedding sur les 62 356 faits médicaux
des 15 domaines. Chaque triplet (s, r, o) → paire d'attraction (s, o).

PRINCIPE : Si « paludisme » et « fièvre » apparaissent ensemble dans
un fait, ils sont sémantiquement liés. L'apprentissage direct dans ℂ⁵¹²
rapproche leurs ψ.

SORTIE : semantic_wave_embedding_medical.pkl (~5 Mo)

Auteur : THU — Univers-Holistique
Date   : 2026-08-23
"""

import sys, os, math, time, json, pickle, re
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set
import numpy as np

# Ajouter le chemin aux modules
sys.path.insert(0, str(Path(__file__).resolve().parent / "vital-ka" / "core" / "python"))
from semantic_wave_embedding import SemanticWaveEmbedding, base_encode

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════

FACTS_DIR = Path(__file__).resolve().parent / "vital-ka" / "data" / "medical_holograms"
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "semantic_wave_embedding_medical.pkl"
DIM = 512
EPOCHS = 150
LR = 0.03
MIN_PAIR_FREQ = 2  # fréquence minimale pour inclure un mot

ALL_DOMAINS = [
    "CHRONIQUES", "CLINIQUE", "GENERAL", "MALADIES",
    "MERE_ENFANT", "MNT", "NUTRITION", "PALUDISME",
    "PEDIATRIE", "PHARMACIE", "PHYTOTHERAPIE", "SANTE_MENTALE",
    "URGENCES", "VACCINATION", "VIH_TB",
]

# Stopwords à exclure (mots-outils qui n'apportent pas de sémantique)
STOPWORDS = {
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
    'au', 'aux', 'en', 'pour', 'avec', 'sur', 'est', 'sont', 'ce',
    'cette', 'dans', 'à', 'a', 'que', 'qui', 'pas', 'ne', 'plus',
    'tout', 'tous', 'il', 'elle', 'ils', 'elles', 'nous', 'vous',
    'son', 'sa', 'ses', 'leur', 'leurs', 'mon', 'ma', 'mes',
    'the', 'is', 'are', 'of', 'in', 'on', 'at', 'to', 'for',
    'kg', 'mg', 'ml', 'g', 'j', 'h', 'min', 'si', 'd', 'l',
    'oui', 'non', 'true', 'false', 'none', 'pas', 'peut',
}


def clean_word(w: str) -> str:
    """Nettoie un mot/terme médical."""
    w = w.strip().lower()
    w = w.replace('_', ' ')
    w = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', w)
    w = re.sub(r'\s+', ' ', w).strip()
    return w


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 1 : CHARGEMENT ET EXTRACTION DES PAIRES
# ═══════════════════════════════════════════════════════════════════

def load_all_facts_and_pairs() -> Tuple[List[Tuple[str, str]], Dict[str, int]]:
    """Charge tous les faits et extrait les paires (sujet, objet)."""
    all_pairs = []
    word_freq = Counter()
    
    for domain in ALL_DOMAINS:
        path = FACTS_DIR / f"{domain}_facts.json"
        if not path.exists():
            continue
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        domain_pairs = 0
        for fact in data:
            s = str(fact.get('s', '')).strip()
            o = str(fact.get('o', '')).strip()
            
            s = clean_word(s)
            o = clean_word(o)
            
            if not s or not o or len(s) < 2 or len(o) < 2:
                continue
            
            # Compter les mots
            for w in s.split():
                if w not in STOPWORDS and len(w) >= 2:
                    word_freq[w] += 1
            for w in o.split():
                if w not in STOPWORDS and len(w) >= 2:
                    word_freq[w] += 1
            
            # Pour les sujets/objets multi-mots : créer des paires mot à mot
            # pour enrichir les co-occurrences
            s_words = [w for w in s.split() if w not in STOPWORDS and len(w) >= 2]
            o_words = [w for w in o.split() if w not in STOPWORDS and len(w) >= 2]
            
            for sw in s_words:
                for ow in o_words:
                    all_pairs.append((sw, ow))
                    domain_pairs += 1
        
        print(f"   📂 {domain:<20s} : {len(data):>6,} faits → {domain_pairs:>8,} paires")
    
    # Dédupliquer
    unique_pairs = list(set(all_pairs))
    print(f"\n   📊 Total paires brutes : {len(all_pairs):,}")
    print(f"   📊 Paires uniques      : {len(unique_pairs):,}")
    print(f"   📊 Mots uniques        : {len(word_freq):,}")
    
    return unique_pairs, word_freq


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 2 : ENRICHISSEMENT — Paires inversées + paires par co-occurrence
# ═══════════════════════════════════════════════════════════════════

def enrich_pairs(pairs: List[Tuple[str, str]], 
                 word_freq: Dict[str, int]) -> List[Tuple[str, str]]:
    """
    Enrichit les paires d'entraînement.
    
    1. Paires inversées (symétrie)
    2. Paires de mots qui co-occurrent avec le même sujet (similarité de 2e ordre)
    """
    enriched = list(pairs)
    
    # 1. Inverser (symétrie : si A↔B est une paire, B↔A aussi)
    for a, b in pairs:
        enriched.append((b, a))
    
    # 2. Co-occurrence de 2e ordre : deux objets du même sujet sont liés
    print("   📊 Enrichissement par co-occurrence de 2e ordre...")
    subject_to_objects = defaultdict(set)
    for a, b in pairs:
        subject_to_objects[a].add(b)
    
    second_order = set()
    for subject, objects in subject_to_objects.items():
        objs = list(objects)
        if len(objs) > 1 and len(objs) <= 30:  # pas trop large
            for i in range(len(objs)):
                for j in range(i+1, len(objs)):
                    second_order.add((objs[i], objs[j]))
                    second_order.add((objs[j], objs[i]))
    
    enriched.extend(second_order)
    print(f"   📊 Paires 2e ordre : {len(second_order):,}")
    
    # Dédupliquer
    enriched = list(set(enriched))
    print(f"   📊 Total enrichi   : {len(enriched):,} paires")
    
    return enriched


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 3 : ENTRAÎNEMENT
# ═══════════════════════════════════════════════════════════════════

def train_medical_embedding(pairs: List[Tuple[str, str]], 
                            word_freq: Dict[str, int]):
    """Entraîne le SemanticWaveEmbedding sur les paires médicales."""
    
    # Filtrer les mots trop rares
    valid_words = {w for w, c in word_freq.items() if c >= MIN_PAIR_FREQ}
    filtered_pairs = [(a, b) for a, b in pairs 
                      if a in valid_words and b in valid_words]
    
    all_terms = set()
    for a, b in filtered_pairs:
        all_terms.add(a)
        all_terms.add(b)
    
    print(f"\n   📊 Mots valides (freq ≥ {MIN_PAIR_FREQ}) : {len(valid_words):,}")
    print(f"   📊 Termes dans les paires : {len(all_terms):,}")
    print(f"   📊 Paires filtrées : {len(filtered_pairs):,}")
    
    # Limiter si trop de paires (mémoire)
    if len(filtered_pairs) > 200000:
        np.random.seed(42)
        idxs = np.random.choice(len(filtered_pairs), 200000, replace=False)
        filtered_pairs = [filtered_pairs[i] for i in idxs]
        print(f"   ⚠️  Limité à {len(filtered_pairs):,} paires (mémoire)")
    
    print(f"\n   🏋️ Entraînement ({EPOCHS} époques, lr={LR})...")
    print(f"   {'═'*50}")
    
    t0 = time.time()
    
    # Créer et entraîner
    swe = SemanticWaveEmbedding(dim=DIM, lr=LR)
    
    # Pré-initialiser tous les termes
    for term in all_terms:
        swe._init_psi(term)
    
    losses = swe.train(
        filtered_pairs,
        epochs=EPOCHS,
        batch_size=256,
        verbose=True,
    )
    
    train_time = time.time() - t0
    print(f"   {'═'*50}")
    print(f"   ⏱️  Temps d'entraînement : {train_time:.1f}s ({train_time/60:.1f}min)")
    print(f"   📉 Loss initiale : {losses[0]:.4f}")
    print(f"   📉 Loss finale   : {losses[-1]:.4f}")
    print(f"   📉 Réduction     : {(1 - losses[-1]/losses[0])*100:.1f}%")
    
    return swe, filtered_pairs, all_terms


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 4 : TEST
# ═══════════════════════════════════════════════════════════════════

def test_medical_similarity(swe: SemanticWaveEmbedding):
    """Teste la similarité sémantique sur des paires médicales."""
    print(f"\n{'═'*70}")
    print("  🧪 TEST — Similarité Sémantique Médicale")
    print("═" * 70)
    
    # Paires qui DOIVENT être proches (même sujet)
    related_pairs = [
        ("paludisme", "fièvre"),
        ("paludisme", "frissons"),
        ("paludisme", "artésunate"),
        ("paludisme", "quinine"),
        ("paludisme", "moustiquaire"),
        ("anémie", "pâleur"),
        ("anémie", "fer"),
        ("pneumonie", "toux"),
        ("pneumonie", "dyspnée"),
        ("diabète", "glycémie"),
        ("diabète", "insuline"),
        ("hypertension", "tension"),
        ("tuberculose", "toux"),
        ("asthme", "dyspnée"),
        ("asthme", "inhalateur"),
        ("épilepsie", "convulsion"),
        ("VIH", "antirétroviral"),
        ("paludisme", "anophèle"),
        ("douleur", "paracétamol"),
        ("douleur", "morphine"),
        ("infection", "antibiotique"),
        ("vaccin", "immunité"),
        ("cœur", "cardiaque"),
        ("cœur", "infarctus"),
        ("grossesse", "accouchement"),
        ("enfant", "pédiatrie"),
        ("cancer", "chimiothérapie"),
        ("dépression", "antidépresseur"),
        ("obésité", "diabète"),
        ("tabac", "cancer"),
    ]
    
    # Paires qui NE DOIVENT PAS être proches (domaines différents)
    unrelated_pairs = [
        ("paludisme", "chaise"),
        ("fièvre", "voiture"),
        ("cœur", "table"),
        ("asthme", "nuage"),
        ("vaccin", "téléphone"),
        ("diabète", "bureau"),
        ("cancer", "fenêtre"),
        ("grossesse", "ordinateur"),
        ("douleur", "stylo"),
        ("antibiotique", "ciel"),
    ]
    
    # Paires identiques (doivent être ~1.0)
    identity_pairs = [
        ("paludisme", "paludisme"),
        ("fièvre", "fièvre"),
        ("douleur", "douleur"),
    ]
    
    print(f"\n  📊 Paires LIÉES (doivent être > 0.6) :")
    print(f"  {'Paire':<35s} {'Sim':>8s} {'OK':>5s}")
    print(f"  {'─'*35} {'─'*8} {'─'*5}")
    
    related_sims = []
    for a, b in related_pairs:
        try:
            sim = swe.similarity(a, b)
            related_sims.append(sim)
            ok = sim > 0.55
            print(f"  {a+' ↔ '+b:<35s} {sim:>8.4f} {'✅' if ok else '❌':>5s}")
        except Exception:
            print(f"  {a+' ↔ '+b:<35s} {'N/A':>8s} {'—':>5s}")
    
    print(f"\n  📊 Paires NON LIÉES (doivent être < 0.55) :")
    print(f"  {'Paire':<35s} {'Sim':>8s} {'OK':>5s}")
    print(f"  {'─'*35} {'─'*8} {'─'*5}")
    
    unrelated_sims = []
    for a, b in unrelated_pairs:
        try:
            sim = swe.similarity(a, b)
            unrelated_sims.append(sim)
            ok = sim < 0.55
            print(f"  {a+' ↔ '+b:<35s} {sim:>8.4f} {'✅' if ok else '❌':>5s}")
        except Exception:
            print(f"  {a+' ↔ '+b:<35s} {'N/A':>8s} {'—':>5s}")
    
    print(f"\n  📊 Paires IDENTIQUES (doivent être ~1.0) :")
    for a, b in identity_pairs:
        try:
            sim = swe.similarity(a, b)
            print(f"  {a+' ↔ '+b:<35s} {sim:>8.4f}")
        except Exception:
            print(f"  {a+' ↔ '+b:<35s} {'N/A':>8s}")
    
    # Statistiques
    avg_rel = np.mean(related_sims) if related_sims else 0
    avg_unrel = np.mean(unrelated_sims) if unrelated_sims else 0
    separation = avg_rel - avg_unrel
    
    n_rel_correct = sum(1 for s in related_sims if s > 0.55)
    n_unrel_correct = sum(1 for s in unrelated_sims if s < 0.55)
    
    print(f"\n  📊 STATISTIQUES :")
    print(f"     Similarité moyenne (liés)     : {avg_rel:.4f}")
    print(f"     Similarité moyenne (non liés) : {avg_unrel:.4f}")
    print(f"     Séparation (Δ)                : {separation:+.4f}")
    print(f"     Précision paires liées        : {n_rel_correct}/{len(related_sims)}")
    print(f"     Précision paires non liées    : {n_unrel_correct}/{len(unrelated_sims)}")
    
    quality = "✅ EXCELLENT" if separation > 0.2 and n_rel_correct > len(related_sims)*0.7 \
         else "⚠️ CORRECT" if separation > 0.1 \
         else "❌ INSUFFISANT"
    
    print(f"     VERDICT                       : {quality}")
    
    return {
        'avg_related': avg_rel,
        'avg_unrelated': avg_unrel,
        'separation': separation,
        'n_related_correct': n_rel_correct,
        'n_related_total': len(related_sims),
        'n_unrelated_correct': n_unrel_correct,
        'n_unrelated_total': len(unrelated_sims),
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t_total = time.time()
    
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🌊 TRAINER — Semantic Wave Medical Embedding              ║")
    print("║  62K faits → paires (sujet, objet) → ψ ∈ ℂ⁵¹²             ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # 1. Chargement
    print("═" * 70)
    print("  ÉTAPE 1 — Extraction des paires (sujet, objet)")
    print("═" * 70)
    pairs, word_freq = load_all_facts_and_pairs()
    
    # 2. Enrichissement
    print(f"\n{'═'*70}")
    print("  ÉTAPE 2 — Enrichissement (inversion + 2e ordre)")
    print("═" * 70)
    pairs = enrich_pairs(pairs, word_freq)
    
    # 3. Entraînement
    print(f"\n{'═'*70}")
    print("  ÉTAPE 3 — Entraînement SemanticWaveEmbedding")
    print("═" * 70)
    swe, filtered_pairs, all_terms = train_medical_embedding(pairs, word_freq)
    
    # 4. Test
    results = test_medical_similarity(swe)
    
    # 5. Sauvegarde
    print(f"\n{'═'*70}")
    print("  ÉTAPE 4 — Sauvegarde")
    print("═" * 70)
    swe.save(str(OUTPUT_PATH))
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"   💾 Sauvegardé : {OUTPUT_PATH}")
    print(f"   📦 Taille     : {size_mb:.1f} Mo")
    print(f"   📊 Vocabulaire : {swe.vocab_size} termes")
    
    # 6. Bilan
    print(f"\n{'═'*70}")
    print("  ✅ BILAN FINAL")
    print("═" * 70)
    print(f"""
  Paires d'entraînement : {len(filtered_pairs):,}
  Vocabulaire           : {swe.vocab_size:,} termes
  Époques               : {EPOCHS}
  Temps total           : {time.time() - t_total:.1f}s ({(time.time() - t_total)/60:.1f}min)
  
  Similarité liés       : {results['avg_related']:.4f}
  Similarité non liés   : {results['avg_unrelated']:.4f}
  Séparation            : {results['separation']:+.4f}
  
  📁 Fichier             : {OUTPUT_PATH}
""")