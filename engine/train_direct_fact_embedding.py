"""
🌊 DIRECT FACT EMBEDDING — Sémantique sans PPMI
=================================================
Construit le plongement sémantique DIRECTEMENT à partir des triplets
(sujet, relation, objet), sans passer par PPMI ni templates.

PRINCIPE : Les faits SONT les relations sémantiques. Pas besoin de
les noyer dans du texte pour que PPMI les « découvre » — on les
connaît déjà explicitement.

MÉTHODE :
  1. Matrice de co-occurrence directe : cooc[s][o] += 1 pour chaque fait
  2. SVD sur cette matrice → phases S¹
  3. Les maladies et leurs symptômes sont naturellement PROCHES en phase

POURQUOI C'EST SUPÉRIEUR À PPMI :
  - PPMI : « paludisme » et « fièvre » doivent co-occurrent dans des
    phrases variées pour que la similarité émerge → nécessite un
    corpus énorme et varié
  - Direct : le triplet (paludisme, présente_symptôme, fièvre) est
    une relation EXPLICITE → cooc[paludisme][fièvre] += 1 directement
  - Aucun bruit de template, aucun mot-outil, signal PUR

RÉSULTAT ATTENDU :
  SNR > 10 (vs 5.1 pour PPMI)
  Précision > 60% sur les paires maladie↔symptôme

Auteur : THU — Univers-Holistique
Date   : 2026-08-23
"""

import sys, os, math, time, json, re
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import svds

_ENGINE_DIR = Path(__file__).resolve().parent
FACTS_DIR = _ENGINE_DIR / "vital-ka" / "data" / "medical_holograms"
OUTPUT_DIR = _ENGINE_DIR / "vital-ka" / "data"
FULL_OUTPUT = OUTPUT_DIR / "semantic_clinique_full.json"

ALL_DOMAINS = [
    "CHRONIQUES", "CLINIQUE", "GENERAL", "MALADIES",
    "MERE_ENFANT", "MNT", "NUTRITION", "PALUDISME",
    "PEDIATRIE", "PHARMACIE", "PHYTOTHERAPIE", "SANTE_MENTALE",
    "URGENCES", "VACCINATION", "VIH_TB",
]

PHI = (1 + math.sqrt(5)) / 2
TAU = 2.0 * math.pi
GOLDEN_ENTROPY = math.log(PHI) * (2.0 + PHI) / math.log(2.0)

DIM = 512
K_COMPONENTS = 32
MAX_FACTS = 50000


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 1 : MATRICE DE CO-OCCURRENCE DIRECTE
# ═══════════════════════════════════════════════════════════════════

def build_direct_cooc_matrix(all_facts: List[dict]) -> Tuple:
    """
    Construit la matrice de co-occurrence DIRECTE sujet↔objet.
    
    Pour chaque fait (s, r, o) : cooc[s][o] += 1
    Pour les relations « présente_symptôme » : cooc[s][o] += 3 (poids ×3)
    
    C'est la matrice qu'on aurait voulu que PPMI découvre — mais au lieu
    de la déduire de co-occurrences textuelles, on la construit directement.
    """
    print("   Construction de la matrice de co-occurrence directe...")
    
    # Collecter tous les sujets et objets uniques
    subjects = set()
    objects = set()
    relation_counts = Counter()
    
    for fact in all_facts[:MAX_FACTS]:
        s = str(fact.get('s', '')).strip().lower().replace('_', ' ')
        o = str(fact.get('o', '')).strip().lower().replace('_', ' ')
        r = str(fact.get('r', '')).strip().lower()
        
        s = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', s).strip()
        o = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', o).strip()
        
        if len(s) > 2 and len(o) > 2:
            subjects.add(s)
            objects.add(o)
            relation_counts[r] += 1
    
    # Fusionner sujets et objets en un vocabulaire unique
    all_terms = sorted(subjects | objects)
    vocab = {w: i for i, w in enumerate(all_terms)}
    N = len(vocab)
    
    print(f"   Sujets uniques  : {len(subjects)}")
    print(f"   Objets uniques  : {len(objects)}")
    print(f"   Vocabulaire     : {N} termes")
    print(f"   Top relations   : {relation_counts.most_common(5)}")
    
    # Construire la matrice sparse
    cooc = lil_matrix((N, N), dtype=np.float64)
    
    for fact in all_facts[:MAX_FACTS]:
        s = str(fact.get('s', '')).strip().lower().replace('_', ' ')
        o = str(fact.get('o', '')).strip().lower().replace('_', ' ')
        r = str(fact.get('r', '')).strip().lower()
        
        s = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', s).strip()
        o = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', o).strip()
        
        if s not in vocab or o not in vocab:
            continue
        
        i, j = vocab[s], vocab[o]
        
        # Poids selon le type de relation
        if 'symptôme' in r or 'symptome' in r or 'présente' in r or 'presente' in r:
            weight = 3.0  # Relation forte : symptôme
        elif 'traitement' in r or 'traite' in r or 'dose' in r:
            weight = 2.0  # Relation moyenne : traitement
        elif 'complication' in r or 'diagnostic' in r or 'urgence' in r:
            weight = 2.0
        else:
            weight = 1.0  # Relation faible
        
        cooc[i, j] += weight
        cooc[j, i] += weight * 0.5  # Symétrie partielle (l'objet → sujet est moins fort)
    
    # Symétriser complètement pour SVD
    C = cooc.tocsr()
    C = (C + C.T) / 2
    
    nnz = C.nnz
    sparsity = 1.0 - nnz / (N * N)
    print(f"   Matrice : {N}×{N}, {nnz:,} non-zéros ({sparsity:.2%} sparse)")
    
    return C, vocab, all_terms


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 2 : SVD DIRECT → PHASES S¹
# ═══════════════════════════════════════════════════════════════════

def direct_svd_phases(C, vocab: Dict[str, int], k: int = 32) -> dict:
    """
    SVD sur la matrice de co-occurrence directe.
    
    Pas de PPMI, pas de log, pas de normalisation complexe.
    Juste SVD sur les comptages bruts pondérés.
    
    Pourquoi ça marche :
      - Si « paludisme » et « fièvre » co-occurrent dans 10 faits,
        la ligne de « paludisme » et la colonne de « fièvre » sont corrélées
      - SVD capture cette corrélation dans les premières composantes
      - Les phases de « paludisme » et « fièvre » sont PROCHES
    """
    t0 = time.time()
    N = len(vocab)
    k_actual = min(k, N - 2)
    
    print(f"\n🔬 SVD DIRECT (k={k_actual}) sur matrice {N}×{N}...")
    
    U, S, Vt = svds(C, k=k_actual, which='LM')
    idx = np.argsort(S)[::-1]
    S = S[idx]
    U = U[:, idx]
    
    print(f"   σ₁={S[0]:.1f}, σ₂={S[1]:.1f}, σ₃={S[2]:.1f}")
    if len(S) >= 4:
        print(f"   σ₄={S[3]:.1f}, ..., σₖ={S[-1]:.1f}")
    print(f"   σ₁/σₖ = {S[0]/S[-1]:.1f}")
    print(f"   ⏱️  Temps SVD : {time.time() - t0:.1f}s")
    
    # Phases
    inv_vocab = {i: w for w, i in vocab.items()}
    n_phases = k_actual // 2
    phases_per_word = []
    word_list = []
    
    for i in range(N):
        vec = U[i, :]
        word_phases = []
        for j in range(n_phases):
            theta = math.atan2(vec[2*j+1], vec[2*j]) % TAU
            word_phases.append(theta)
        phases_per_word.append(word_phases)
        word_list.append(inv_vocab[i])
    
    all_p0 = [p[0] for p in phases_per_word]
    hist, _ = np.histogram(all_p0, bins=24, range=(0, TAU))
    print(f"   Distribution phases : min={hist.min()}, max={hist.max()}, σ={np.std(hist):.1f}")
    
    return {
        'words': word_list,
        'phases': phases_per_word,
        'singular_values': S.tolist(),
        'n_phases': n_phases,
        'k_components': k_actual,
    }


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 3 : TEST DE QUALITÉ
# ═══════════════════════════════════════════════════════════════════

def test_direct_quality(phases_data: dict, all_facts: List[dict]):
    """Test de qualité sémantique sur l'embedding direct."""
    print("\n" + "═" * 70)
    print("  🧪 TEST — Qualité Sémantique (Embedding Direct)")
    print("═" * 70)
    
    word_to_idx = {w: i for i, w in enumerate(phases_data['words'])}
    n_phases = phases_data['n_phases']
    
    def phase_similarity(w1: str, w2: str) -> float:
        i1 = word_to_idx.get(w1)
        i2 = word_to_idx.get(w2)
        if i1 is None or i2 is None:
            return 0.0
        
        total_sim = 0.0
        p1 = phases_data['phases'][i1]
        p2 = phases_data['phases'][i2]
        for j in range(n_phases):
            diff = abs(p1[j] - p2[j])
            diff = min(diff, TAU - diff)
            total_sim += math.cos(diff)
        return total_sim / n_phases
    
    # Collecter les paires vraies (maladie, symptôme)
    true_pairs = []
    for fact in all_facts[:10000]:
        s = str(fact.get('s', '')).strip().lower().replace('_', ' ')
        o = str(fact.get('o', '')).strip().lower().replace('_', ' ')
        s = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', s).strip()
        o = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', o).strip()
        if s in word_to_idx and o in word_to_idx:
            true_pairs.append((s, o))
    
    if len(true_pairs) > 500:
        np.random.seed(42)
        idxs = np.random.choice(len(true_pairs), 500, replace=False)
        true_pairs = [true_pairs[i] for i in idxs]
    
    true_sims = [phase_similarity(s, o) for s, o in true_pairs]
    avg_true = np.mean(true_sims) if true_sims else 0
    
    # Baseline aléatoire
    all_words = list(word_to_idx.keys())
    random_sims = []
    for _ in range(500):
        w1 = np.random.choice(all_words)
        w2 = np.random.choice(all_words)
        if w1 != w2:
            random_sims.append(phase_similarity(w1, w2))
    avg_random = np.mean(random_sims) if random_sims else 0
    
    snr = (avg_true - avg_random) / max(abs(avg_random), 0.01)
    
    print(f"\n   Paires vraies : {len(true_pairs)}")
    print(f"   Similarité vraie   : {avg_true:+.4f}")
    print(f"   Similarité aléatoire : {avg_random:+.4f}")
    print(f"   SNR                 : {snr:+.2f}")
    print(f"   → {'✅ EXCELLENT' if snr > 10 else '✅ BON' if snr > 5 else '⚠️ MODÉRÉ' if snr > 2 else '❌ FAIBLE'}")
    
    # Top paires
    print(f"\n   Top 15 paires les plus similaires :")
    all_pairs_sim = [(s, o, phase_similarity(s, o)) for s, o in true_pairs]
    all_pairs_sim.sort(key=lambda x: -x[2])
    for s, o, sim in all_pairs_sim[:15]:
        print(f"     {s[:30]:<30s} ↔ {o[:30]:<30s} : {sim:+.4f}")
    
    # Précision par maladie
    by_subject = defaultdict(set)
    for fact in all_facts[:10000]:
        s = str(fact.get('s', '')).strip().lower().replace('_', ' ')
        o = str(fact.get('o', '')).strip().lower().replace('_', ' ')
        s = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', s).strip()
        o = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', o).strip()
        if s and o:
            by_subject[s].add(o)
    
    precisions = []
    print(f"\n   Précision par maladie (top-10) :")
    sorted_subjects = sorted(by_subject.items(), key=lambda x: -len(x[1]))
    
    for subject, true_symptoms in sorted_subjects[:12]:
        if len(true_symptoms) < 3 or subject not in word_to_idx:
            continue
        
        candidates = [(w, phase_similarity(subject, w)) for w in word_to_idx if w != subject]
        candidates.sort(key=lambda x: -x[1])
        top_10 = set(w for w, s in candidates[:10])
        
        hits = true_symptoms & top_10
        prec = len(hits) / min(10, len(true_symptoms))
        precisions.append(prec)
        
        print(f"     🏥 {subject[:25]:<25s} ({len(true_symptoms):>3d} sympt) → {len(hits):>2d}/10 hits → {prec:.0%}")
    
    avg_prec = np.mean(precisions) if precisions else 0
    print(f"\n   Précision moyenne : {avg_prec:.1%}")
    
    return avg_true, snr, avg_prec


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 4 : SAUVEGARDE
# ═══════════════════════════════════════════════════════════════════

def save_encoder(phases_data: dict, output_path: Path, stats: dict):
    output = {
        'version': '4.0',
        'date': '2026-08-23',
        'method': 'Direct Fact Embedding (co-occurrence directe, sans PPMI)',
        'corpus': f"{stats.get('n_facts', 0):,} faits, {stats.get('n_domains', 0)} domaines",
        'dim': DIM,
        'k_components': phases_data['k_components'],
        'n_phases': phases_data['n_phases'],
        'n_words': len(phases_data['words']),
        'golden_entropy_bits': GOLDEN_ENTROPY,
        'singular_values': phases_data['singular_values'],
        'words': phases_data['words'],
        'phases': phases_data['phases'],
        'stats': stats,
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    size_kb = output_path.stat().st_size / 1024
    print(f"\n💾 Sauvegardé : {output_path}")
    print(f"   Taille : {size_kb:.0f} Ko | Mots : {len(phases_data['words'])} | Phases/mot : {phases_data['n_phases']}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t_total = time.time()
    
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🌊 DIRECT FACT EMBEDDING — Sémantique sans PPMI            ║")
    print("║  Co-occurrence directe → SVD → phases S¹                   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # 1. Chargement
    print("═" * 70)
    print("  ÉTAPE 1 — Chargement des faits")
    print("═" * 70)
    
    all_facts = []
    for domain in ALL_DOMAINS:
        path = FACTS_DIR / f"{domain}_facts.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            all_facts.extend(data)
            print(f"   📂 {domain:<20s} : {len(data):>6,} faits")
    
    print(f"   ✅ Total : {len(all_facts):,} faits")
    
    # 2. Matrice de co-occurrence directe
    print(f"\n{'═'*70}")
    print("  ÉTAPE 2 — Matrice de co-occurrence DIRECTE sujet↔objet")
    print("═" * 70)
    C, vocab, all_terms = build_direct_cooc_matrix(all_facts)
    
    # 3. SVD + Phases
    print(f"\n{'═'*70}")
    print("  ÉTAPE 3 — SVD DIRECT → Phases S¹")
    print("═" * 70)
    phases_data = direct_svd_phases(C, vocab, k=K_COMPONENTS)
    
    # 4. Test
    avg_sim, snr, avg_prec = test_direct_quality(phases_data, all_facts)
    
    # 5. Sauvegarde
    print(f"\n{'═'*70}")
    print("  ÉTAPE 4 — Sauvegarde")
    print("═" * 70)
    stats = {
        'n_domains': len(ALL_DOMAINS),
        'n_facts': len(all_facts),
        'n_terms': len(all_terms),
        'avg_true_similarity': float(avg_sim),
        'snr': float(snr),
        'avg_precision': float(avg_prec),
    }
    save_encoder(phases_data, FULL_OUTPUT, stats)
    
    # 6. Bilan
    print(f"\n{'═'*70}")
    print("  ✅ BILAN FINAL")
    print("═" * 70)
    print(f"""
  Méthode           : Co-occurrence DIRECTE (sans PPMI, sans templates)
  Faits             : {len(all_facts):,}
  Vocabulaire       : {len(vocab):,} termes
  Composantes SVD   : {phases_data['k_components']}
  Phases/mot        : {phases_data['n_phases']}
  Similarité vraie  : {avg_sim:+.4f}
  SNR               : {snr:+.2f}
  Précision moyenne : {avg_prec:.1%}
  Temps total       : {time.time() - t_total:.1f}s
  
  📁 Fichier : {FULL_OUTPUT}
  
  {'✅ EMBEDDING PRÊT — SNR > 10' if snr > 10 else '⚠️  SNR > 5 — utilisable' if snr > 5 else '❌ SNR insuffisant'}
""")