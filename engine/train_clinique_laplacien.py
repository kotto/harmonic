"""
🌊 TRAIN LAPLACIEN SÉMANTIQUE — Corpus MULTI-DOMAINE (60K+ faits)
===================================================================
Version 2 : charge TOUS les domaines médicaux pour enrichir les
co-occurrences et créer un plongement sémantique de qualité.

Le problème du CLINIQUE seul : 60K faits mais seulement 49 sujets uniques.
→ Les phrases générées sont trop répétitives.
→ Le PPMI capture surtout les mots-outils ("patient", "présente").

SOLUTION : charger les 15 domaines, créer des phrases à co-occurrence
DIRECTE entre maladies et symptômes, et entraîner le Laplacien sur
ce vocabulaire médical riche (~2000+ maladies, ~5000+ symptômes).

PRINCIPE :
  Pour chaque fait (maladie, présente_symptôme, symptôme) :
    1. Phrase simple : "MALADIE symptôme SYMPTOME"
       → co-occurrence DIRECTE entre MALADIE et SYMPTOME
    2. Phrase enrichie : "La MALADIE se manifeste par SYMPTOME"
       → contexte naturel
    3. Phrase agrégée : "Les symptômes de MALADIE incluent S1, S2, S3"
       → co-occurrence multiple

  PPMI capture alors :
    PMI(maladie, symptôme) élevé si co-occurrence fréquente
    → θ(maladie) ≈ θ(symptôme) sur S¹
    → retrieval holographique devient PRÉCIS

Auteur : THU — Univers-Holistique
Date   : 2026-08-23
"""

import sys, os, math, time, json, re, gc
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
import numpy as np

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

_ENGINE_DIR = Path(__file__).resolve().parent  # engine/

FACTS_DIR = _ENGINE_DIR / "vital-ka" / "data" / "medical_holograms"
OUTPUT_DIR = _ENGINE_DIR / "vital-ka" / "data"
FULL_OUTPUT = OUTPUT_DIR / "semantic_clinique_full.json"

# Hyperparamètres
DIM = 512
WINDOW_SIZE = 8          # fenêtre élargie pour capturer maladie↔symptôme
MIN_FREQ = 1             # inclure même les mots rares (symptômes uniques)
MAX_VOCAB = 10000        # plus grand vocabulaire
K_COMPONENTS = 32        # 16 phases sémantiques par mot (haute résolution)

# Source du corpus
ENRICHED_CORPUS_PATH = OUTPUT_DIR / "corpus_medical_enrichi.json"

PHI = (1 + math.sqrt(5)) / 2
TAU = 2.0 * math.pi
GOLDEN_ENTROPY = math.log(PHI) * (2.0 + PHI) / math.log(2.0)

# Domaines à charger (tous)
DOMAINS_TO_LOAD = [
    "CHRONIQUES", "CLINIQUE", "GENERAL", "MALADIES",
    "MERE_ENFANT", "MNT", "NUTRITION", "PALUDISME",
    "PEDIATRIE", "PHARMACIE", "PHYTOTHERAPIE", "SANTE_MENTALE",
    "URGENCES", "VACCINATION", "VIH_TB",
]


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 1 : CHARGEMENT MULTI-DOMAINE
# ═══════════════════════════════════════════════════════════════════

def load_all_domains(facts_dir: Path, domains: List[str]) -> Dict[str, List[dict]]:
    """Charge tous les faits de tous les domaines."""
    all_facts = {}
    total = 0
    
    for domain in domains:
        path = facts_dir / f"{domain}_facts.json"
        if not path.exists():
            print(f"   ⚠️  {domain} : fichier introuvable")
            continue
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_facts[domain] = data
        total += len(data)
        print(f"   📂 {domain:<20s} : {len(data):>6,} faits")
    
    print(f"   ✅ Total : {total:,} faits dans {len(all_facts)} domaines")
    return all_facts


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 2 : CONVERSION EN PHRASES À CO-OCCURRENCE DIRECTE
# ═══════════════════════════════════════════════════════════════════

def facts_to_rich_sentences(all_facts: Dict[str, List[dict]], 
                            max_facts_per_domain: int = None) -> List[str]:
    """
    Convertit les faits en phrases OPTIMISÉES pour la co-occurrence
    directe entre maladies et symptômes.
    
    Stratégie : créer des phrases où le NOM de la maladie et le NOM
    du symptôme apparaissent ENSEMBLE, sans mots-outils qui diluent
    le signal PPMI.
    """
    sentences = []
    seen = set()
    
    # Phrases de liaison — volontairement courtes pour maximiser
    # la co-occurrence directe maladie↔symptôme
    linkers = [
        "{s} symptôme {o}",
        "{s} {o}",
        "{o} dans {s}",
        "symptôme de {s} est {o}",
        "{s} cause {o}",
        "{s} provoque {o}",
        "{s} se manifeste par {o}",
        "{s} traitement {o}",
        "{s} diagnostic {o}",
        "{s} prévention {o}",
        "médicament {s} indication {o}",
        "médicament {s} dose {o}",
        "médicament {s} contre indication {o}",
        "{s} complication {o}",
        "{s} signe gravité {o}",
        "{s} population risque {o}",
    ]
    
    # Par domaine
    for domain, facts in all_facts.items():
        if max_facts_per_domain and len(facts) > max_facts_per_domain:
            facts = facts[:max_facts_per_domain]
        
        # Regrouper par sujet
        by_subject = defaultdict(list)
        for fact in facts:
            s = str(fact.get('s', '')).strip().replace('_', ' ')
            r = str(fact.get('r', '')).strip().replace('_', ' ')
            o = str(fact.get('o', '')).strip().replace('_', ' ')
            
            if not s or not o:
                continue
            
            # Nettoyer : enlever les underscores, normaliser
            s_clean = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', s).strip()
            o_clean = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', o).strip()
            
            if len(s_clean) < 2 or len(o_clean) < 2:
                continue
            
            by_subject[s_clean.lower()].append((s_clean, r, o_clean))
        
        # Générer les phrases
        for subject, fact_list in by_subject.items():
            symptoms = list(set(o for _, _, o in fact_list))
            
            # Pour chaque symptôme : phrase de co-occurrence directe
            for i, (s, r, o) in enumerate(fact_list[:20]):  # max 20 par sujet
                template = linkers[i % len(linkers)]
                try:
                    sent = template.format(s=s, o=o)
                except (KeyError, ValueError):
                    sent = f"{s} {o}"
                
                sent_lower = sent.lower().strip()
                if sent_lower not in seen:
                    sentences.append(sent)
                    seen.add(sent_lower)
            
            # Phrase agrégée (co-occurrence MULTIPLE)
            if len(symptoms) >= 3:
                for chunk_start in range(0, len(symptoms), 5):
                    chunk = symptoms[chunk_start:chunk_start+5]
                    if len(chunk) >= 2:
                        s_rep = fact_list[0][0]
                        agg = f"les symptômes de {s_rep} incluent {' '.join(chunk)}"
                        agg_lower = agg.lower().strip()
                        if agg_lower not in seen:
                            sentences.append(agg)
                            seen.add(agg_lower)
    
    # Compter les sujets uniques
    all_subjects = set()
    for facts in all_facts.values():
        for fact in facts:
            s = str(fact.get('s', '')).strip().lower().replace('_', ' ')
            all_subjects.add(s)
    print(f"   Sujets uniques (tous domaines) : {len(all_subjects)}")
    print(f"   Phrases générées : {len(sentences):,}")
    
    # Afficher quelques exemples
    print(f"   Exemples :")
    for s in sentences[:8]:
        print(f"     • {s[:100]}")
    
    return sentences


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 3 : TOKENISATION (minimale — garder tous les mots)
# ═══════════════════════════════════════════════════════════════════

def tokenize_minimal(sentences: List[str]) -> List[List[str]]:
    """
    Tokenisation avec filtrage des mots de template.
    
    Les templates introduisent des mots-outils qui co-occurrent avec TOUT
    et diluent le signal PPMI : « clinique », « tableau », « cadre », « faut »...
    On les filtre AGRESSIVEMENT pour ne garder que le contenu médical.
    """
    # Stopwords + mots de template (haute fréquence, zéro valeur médicale)
    stopwords = {
        'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
        'au', 'aux', 'en', 'pour', 'avec', 'sur', 'est', 'sont',
        'dans', 'à', 'a', 'que', 'qui', 'par', 'pas', 'ne', 'plus',
        'ce', 'cette', 'son', 'sa', 'ses', 'leur', 'leurs',
        'il', 'elle', 'ils', 'elles', 'nous', 'vous',
    }
    
    # Mots de template génériques — apparaissent dans des centaines de phrases
    # différentes et diluent le signal maladie↔symptôme
    template_words = {
        'clinique', 'concernant', 'faut', 'cadre', 'tableau', 'si',
        'conduite', 'face', 'rappel', 'information', 'point', 'clé',
        'essentiel', 'noter', 'savoir', 'pratique', 'diagnostic',
        'traitement', 'prévention', 'symptôme', 'symptômes',
        'patient', 'maladie', 'maladies', 'cas', 'fait',
        'recommandé', 'recommandation', 'indiqué', 'efficace',
        'important', 'importante', 'permettre', 'permis',
        'reposer', 'comprendre', 'inclure', 'inclut',
        'nécessaire', 'nécessite', 'doit', 'peut', 'être',
        'avoir', 'faire', 'dire', 'aller', 'venir',
        'tous', 'tout', 'toute', 'toutes', 'chaque',
        'aussi', 'très', 'bien', 'plus', 'moins',
        'souvent', 'parfois', 'toujours', 'jamais',
        'général', 'généralement', 'habituellement',
        'typique', 'typiquement', 'classique', 'classiquement',
        'principal', 'principalement', 'essentiellement',
        'notamment', 'particulier', 'particulièrement',
        'possible', 'probable', 'probablement',
        'fréquent', 'fréquemment', 'rare', 'rarement',
        'sévère', 'sévèrement', 'grave', 'gravement',
        'aigu', 'aiguë', 'chronique', 'chroniquement',
        'première', 'deuxième', 'troisième', 'dernier',
        'récent', 'ancien', 'nouveau', 'vieil',
    }
    
    tokenized = []
    for sent in sentences:
        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", sent.lower())
        tokens = [t for t in tokens if t not in stopwords and t not in template_words and len(t) >= 2]
        if len(tokens) >= 2:
            tokenized.append(tokens)
    
    return tokenized


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 4 : PPMI SPARSE (optimisé)
# ═══════════════════════════════════════════════════════════════════

def build_ppmi_optimized(tokenized: List[List[str]],
                          window: int = 8,
                          min_freq: int = 1,
                          max_vocab: int = 10000) -> Tuple:
    """Version optimisée du PPMI pour grand corpus multi-domaine."""
    from scipy.sparse import lil_matrix, csr_matrix
    
    t0 = time.time()
    
    # 1. Vocabulaire
    word_counts = Counter()
    for tokens in tokenized:
        for w in tokens:
            word_counts[w] += 1
    
    filtered = [(w, c) for w, c in word_counts.items() if c >= min_freq]
    filtered.sort(key=lambda x: -x[1])
    filtered = filtered[:max_vocab]
    
    vocab = {w: i for i, (w, c) in enumerate(filtered)}
    N = len(vocab)
    
    print(f"   Vocabulaire : {N} mots (freq ≥ {min_freq})")
    print(f"   Top 15 : {', '.join(f'{w}({c})' for w, c in filtered[:15])}")
    
    # 2. Co-occurrence sparse
    cooc = lil_matrix((N, N), dtype=np.float64)
    word_freq = np.zeros(N)
    total_pairs = 0
    
    print(f"   Comptage co-occurrences (fenêtre={window})...")
    for si, tokens in enumerate(tokenized):
        if si % 5000 == 0 and si > 0:
            print(f"      {si}/{len(tokenized)} phrases ({si*100//len(tokenized)}%)...")
        
        ids = [vocab[w] for w in tokens if w in vocab]
        for i, center in enumerate(ids):
            word_freq[center] += 1
            start = max(0, i - window)
            end = min(len(ids), i + window + 1)
            for j in range(start, end):
                if j != i:
                    cooc[center, ids[j]] += 1
                    total_pairs += 1
    
    cooc = cooc.tocsr()
    total_pairs = max(total_pairs, 1)
    print(f"   Paires : {total_pairs:,}")
    
    # 3. PPMI
    print(f"   Calcul PPMI...")
    cx = cooc.tocoo()
    rows, cols, vals = cx.row, cx.col, cx.data
    
    freq_prod = word_freq[rows] * word_freq[cols]
    ppmi_vals = np.where(
        freq_prod > 0,
        np.log(np.maximum(vals * N / freq_prod, 1e-10)),
        0.0
    )
    ppmi_vals = np.maximum(ppmi_vals, 0)
    
    W = csr_matrix((ppmi_vals, (rows, cols)), shape=(N, N))
    W = (W + W.T) / 2
    
    nnz = W.nnz
    sparsity = 1.0 - nnz / (N * N)
    print(f"   Matrice PPMI : {N}×{N}, {nnz:,} non-zéros ({sparsity:.1%} sparse)")
    print(f"   ⏱️  Temps : {time.time() - t0:.1f}s")
    
    return W, vocab, word_freq


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 5 : SVD → Phases
# ═══════════════════════════════════════════════════════════════════

def svd_to_phases(W, vocab: Dict[str, int], k: int = 16):
    """SVD → K composantes → K/2 phases S¹ par mot."""
    from scipy.sparse.linalg import svds
    
    t0 = time.time()
    N = len(vocab)
    k_actual = min(k, N - 2)
    
    print(f"\n🔬 SVD (k={k_actual}) sur matrice {N}×{N}...")
    
    U, S, Vt = svds(W, k=k_actual, which='LM')
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
    
    # Distribution
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
# ÉTAPE 6 : TEST DE SIMILARITÉ SÉMANTIQUE
# ═══════════════════════════════════════════════════════════════════

def test_semantic_quality(phases_data: dict, all_facts: dict):
    """
    Test de qualité sémantique : pour chaque maladie fréquente,
    vérifier que ses vrais symptômes sont proches en phase.
    """
    print("\n" + "═" * 70)
    print("  🧪 TEST — Qualité Sémantique")
    print("═" * 70)
    
    word_to_idx = {w: i for i, w in enumerate(phases_data['words'])}
    n_phases = phases_data['n_phases']
    
    def phase_similarity(w1: str, w2: str) -> float:
        """Similarité moyenne sur les n_phases bandes ∈ [-1, 1]."""
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
            # Convertir distance en similarité : sim = cos(diff)
            total_sim += math.cos(diff)
        return total_sim / n_phases
    
    # Collecter toutes les paires (maladie, symptôme) réelles
    true_pairs = []
    for domain, facts in all_facts.items():
        for fact in facts[:5000]:
            s = str(fact.get('s', '')).strip().lower().replace('_', ' ')
            o = str(fact.get('o', '')).strip().lower().replace('_', ' ')
            if s and o and s in word_to_idx and o in word_to_idx:
                true_pairs.append((s, o))
    
    # Échantillonner 500 paires pour le test
    if len(true_pairs) > 500:
        np.random.seed(42)
        idxs = np.random.choice(len(true_pairs), 500, replace=False)
        true_pairs = [true_pairs[i] for i in idxs]
    
    # Mesurer la similarité des vraies paires
    true_sims = [phase_similarity(s, o) for s, o in true_pairs]
    avg_true_sim = np.mean(true_sims) if true_sims else 0
    
    # Mesurer la similarité de paires ALÉATOIRES (baseline)
    all_words = list(word_to_idx.keys())
    random_sims = []
    for _ in range(min(500, len(true_pairs))):
        w1 = np.random.choice(all_words)
        w2 = np.random.choice(all_words)
        if w1 != w2:
            random_sims.append(phase_similarity(w1, w2))
    avg_random_sim = np.mean(random_sims) if random_sims else 0
    
    # Ratio signal/bruit
    snr = (avg_true_sim - avg_random_sim) / max(abs(avg_random_sim), 0.01)
    
    print(f"\n   Paires vraies (maladie↔symptôme) : {len(true_pairs)}")
    print(f"   Similarité moyenne vraie   : {avg_true_sim:+.4f}")
    print(f"   Similarité moyenne aléatoire : {avg_random_sim:+.4f}")
    print(f"   Ratio signal/bruit          : {snr:+.2f}")
    print(f"   → {'✅ BON' if snr > 2.0 else '⚠️ MODÉRÉ' if snr > 0.5 else '❌ FAIBLE'}")
    
    # Top paires les plus similaires
    print(f"\n   Top 10 paires les plus similaires :")
    all_pairs_sim = [(s, o, phase_similarity(s, o)) 
                     for s, o in true_pairs]
    all_pairs_sim.sort(key=lambda x: -x[2])
    for s, o, sim in all_pairs_sim[:10]:
        print(f"     {s:<30s} ↔ {o:<30s} : {sim:+.4f}")
    
    # Exemples spécifiques
    print(f"\n   Exemples par maladie :")
    test_diseases = ['paludisme', 'anémie', 'pneumonie', 'diabète', 'hypertension',
                     'tuberculose', 'asthme', 'drépanocytose', 'épiglottite']
    for disease in test_diseases:
        if disease not in word_to_idx:
            continue
        
        # Vrais symptômes
        true_symptoms = set()
        for domain, facts in all_facts.items():
            for fact in facts[:2000]:
                s = str(fact.get('s', '')).strip().lower().replace('_', ' ')
                o = str(fact.get('o', '')).strip().lower().replace('_', ' ')
                if disease in s and o in word_to_idx:
                    true_symptoms.add(o)
        
        if not true_symptoms:
            continue
        
        # Top-10 mots les plus proches de la maladie
        candidates = [(w, phase_similarity(disease, w)) 
                      for w in word_to_idx if w != disease]
        candidates.sort(key=lambda x: -x[1])
        top_10 = [w for w, s in candidates[:10]]
        
        hits = true_symptoms & set(top_10)
        prec = len(hits) / min(10, len(true_symptoms))
        
        print(f"     🏥 {disease} ({len(true_symptoms)} symptômes)")
        print(f"        Top-10 proches : {', '.join(top_10[:6])}")
        print(f"        Hits : {len(hits)} → précision {prec:.0%}")
    
    return avg_true_sim, snr


# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 7 : SAUVEGARDE
# ═══════════════════════════════════════════════════════════════════

def save_encoder(phases_data: dict, output_path: Path, stats: dict):
    """Sauvegarde l'encodeur complet."""
    output = {
        'version': '3.0',
        'date': '2026-08-23',
        'corpus': f"Multi-domaine médical ({stats.get('n_domains', 0)} domaines, {stats.get('n_facts', 0):,} faits)",
        'dim': DIM,
        'window_size': WINDOW_SIZE,
        'min_freq': MIN_FREQ,
        'max_vocab': MAX_VOCAB,
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
    print("║  🌊 LAPLACIEN SÉMANTIQUE — CORPUS ENRICHI ×10              ║")
    print("║  PPMI → SVD → phases S¹ (32 composantes, 16 phases/mot)    ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\n  📐 Entropie dorée S(φ) = {GOLDEN_ENTROPY:.6f} bits\n")
    
    # 1. Chargement — utiliser le corpus enrichi si disponible
    print("═" * 70)
    print("  ÉTAPE 1 — Chargement du corpus")
    print("═" * 70)
    
    if ENRICHED_CORPUS_PATH.exists():
        print(f"   📂 Corpus enrichi trouvé : {ENRICHED_CORPUS_PATH.name}")
        with open(ENRICHED_CORPUS_PATH, 'r', encoding='utf-8') as f:
            corpus_data = json.load(f)
        
        total_facts = corpus_data['sources']['facts']
        n_domains = corpus_data['sources']['domains']
        
        # Re-tokeniser avec le nouveau filtre (mots de template exclus)
        raw_sentences = corpus_data['sentences']
        tokenized = tokenize_minimal(raw_sentences)
        
        print(f"   ✅ Phrases tokenisées : {len(tokenized):,}")
        print(f"   ✅ Faits sources      : {total_facts:,}")
        print(f"   ✅ Domaines           : {n_domains}")
        
        # Charger les faits originaux pour le test de similarité
        all_facts = load_all_domains(FACTS_DIR, DOMAINS_TO_LOAD)
    else:
        print("   ⚠️  Corpus enrichi non trouvé — fallback sur les faits bruts")
        all_facts = load_all_domains(FACTS_DIR, DOMAINS_TO_LOAD)
        total_facts = sum(len(v) for v in all_facts.values())
        n_domains = len(all_facts)
        
        sentences = facts_to_rich_sentences(all_facts)
        tokenized = tokenize_minimal(sentences)
    
    total_tokens = sum(len(t) for t in tokenized)
    print(f"   Tokens/phrase : {total_tokens/max(1,len(tokenized)):.1f}")
    
    # 2. PPMI
    print(f"\n{'═'*70}")
    print("  ÉTAPE 2 — PPMI (Positive Pointwise Mutual Information)")
    print("═" * 70)
    try:
        W, vocab, word_freq = build_ppmi_optimized(tokenized, WINDOW_SIZE, MIN_FREQ, MAX_VOCAB)
    except Exception as e:
        print(f"  ⚠️  Erreur : {e} → fallback")
        W, vocab, word_freq = build_ppmi_optimized(tokenized, 5, 2, 5000)
    
    if len(vocab) < 10:
        print("  ❌ Vocabulaire trop petit — arrêt")
        sys.exit(1)
    
    # 3. SVD + Phases (K=32 → 16 phases/mot)
    print(f"\n{'═'*70}")
    print("  ÉTAPE 3 — SVD (k=32) → Phases S¹ (16/mot)")
    print("═" * 70)
    phases_data = svd_to_phases(W, vocab, k=K_COMPONENTS)
    
    # 4. Test
    avg_sim, snr = test_semantic_quality(phases_data, all_facts)
    
    # 5. Sauvegarde
    print(f"\n{'═'*70}")
    print("  ÉTAPE 4 — Sauvegarde")
    print("═" * 70)
    stats = {
        'n_domains': n_domains,
        'n_facts': total_facts,
        'n_phrases': len(tokenized),
        'n_tokens': total_tokens,
        'vocab_size': len(vocab),
        'avg_true_similarity': float(avg_sim),
        'snr': float(snr),
    }
    save_encoder(phases_data, FULL_OUTPUT, stats)
    
    # 6. Bilan
    print(f"\n{'═'*70}")
    print("  ✅ BILAN FINAL")
    print("═" * 70)
    print(f"""
  Corpus            : {'ENRICHI (25K phrases)' if ENRICHED_CORPUS_PATH.exists() else 'BRUT (facts only)'}
  Domaines          : {n_domains}
  Faits             : {total_facts:,}
  Phrases           : {len(tokenized):,}
  Vocabulaire       : {len(vocab):,} mots
  Composantes SVD   : {phases_data['k_components']}
  Phases/mot        : {phases_data['n_phases']}
  Similarité vraie  : {avg_sim:+.4f}
  SNR               : {snr:+.2f}
  Temps total       : {time.time() - t_total:.1f}s ({(time.time() - t_total)/60:.1f}min)
  
  📁 Fichier        : {FULL_OUTPUT}
  
  {'✅ PRÊT' if snr > 5.0 else '⚠️  SNR modéré' if snr > 2.0 else '❌ Insuffisant'}
""")