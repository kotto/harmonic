"""
🌊 TRAINER V2 — Semantic Wave Medical (4 améliorations)
=========================================================
V1 → séparation +0.07. Objectif V2 → +0.20.

AMÉLIORATIONS :
  1. PONDÉRATION par type de relation (symptôme ×3, traitement ×2...)
  2. NÉGATIFS STRUCTURÉS par domaine (pas aléatoires)
  3. DEUX PHASES : petits domaines riches → CLINIQUE (poids réduit)
  4. PLUS D'ÉPOQUES (300) avec cosine decay + early stopping

Auteur : THU — Univers-Holistique
Date   : 2026-08-24
"""

import sys, os, math, time, json, pickle, re
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set, Optional
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "vital-ka" / "core" / "python"))
from semantic_wave_embedding import SemanticWaveEmbedding, base_encode

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════

FACTS_DIR = Path(__file__).resolve().parent / "vital-ka" / "data" / "medical_holograms"
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "semantic_wave_embedding_medical_v2.pkl"
DIM = 512
PHASE1_EPOCHS = 200   # Petits domaines riches
PHASE2_EPOCHS = 300   # Tous domaines
LR_INIT = 0.05
MIN_PAIR_FREQ = 2

ALL_DOMAINS = [
    "CHRONIQUES", "CLINIQUE", "GENERAL", "MALADIES",
    "MERE_ENFANT", "MNT", "NUTRITION", "PALUDISME",
    "PEDIATRIE", "PHARMACIE", "PHYTOTHERAPIE", "SANTE_MENTALE",
    "URGENCES", "VACCINATION", "VIH_TB",
]

# Petits domaines riches (variété sémantique forte)
RICH_DOMAINS = [
    "PALUDISME", "VIH_TB", "MALADIES", "PHARMACIE", "URGENCES",
    "MERE_ENFANT", "PEDIATRIE", "NUTRITION", "CHRONIQUES",
]

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

# Poids par type de relation (amélioration 1)
RELATION_WEIGHTS = {
    'présente_symptôme': 5.0, 'presente_symptome': 5.0, 'symptome': 5.0,
    'traitement': 3.0, 'traite': 3.0, 'dose': 2.0, 'posologie': 2.0,
    'diagnostic': 3.0, 'prévention': 3.0, 'prevention': 3.0,
    'complication': 3.0, 'urgence': 4.0, 'contre': 2.0, 'indication': 2.0,
}


def clean_word(w: str) -> str:
    w = w.strip().lower().replace('_', ' ')
    w = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', w)
    return re.sub(r'\s+', ' ', w).strip()


# ═══════════════════════════════════════════════════════════════════
# CHARGEMENT — paire pondérées + groupées par domaine
# ═══════════════════════════════════════════════════════════════════

def load_weighted_pairs() -> Tuple[Dict[str, List[Tuple[str, str, float]]], 
                                     Dict[str, int], Dict[str, Set[str]]]:
    """
    Charge les paires avec pondération et groupement par domaine.
    
    Returns:
        domain_pairs: {domaine: [(a, b, poids), ...]}
        word_freq: {mot: fréquence}
        domain_vocab: {domaine: set(mots)}
    """
    domain_pairs = defaultdict(list)
    word_freq = Counter()
    domain_vocab = defaultdict(set)
    
    for domain in ALL_DOMAINS:
        path = FACTS_DIR / f"{domain}_facts.json"
        if not path.exists():
            continue
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for fact in data:
            s = clean_word(str(fact.get('s', '')))
            r = clean_word(str(fact.get('r', '')))
            o = clean_word(str(fact.get('o', '')))
            
            if not s or not o or len(s) < 2 or len(o) < 2:
                continue
            
            # Poids par relation (amélioration 1)
            r_key = r.lower().replace(' ', '_')
            weight = 1.0
            for rel_key, w in RELATION_WEIGHTS.items():
                if rel_key in r_key:
                    weight = w
                    break
            
            s_words = [w for w in s.split() if w not in STOPWORDS and len(w) >= 2]
            o_words = [w for w in o.split() if w not in STOPWORDS and len(w) >= 2]
            
            for w in s_words:
                word_freq[w] += 1
                domain_vocab[domain].add(w)
            for w in o_words:
                word_freq[w] += 1
                domain_vocab[domain].add(w)
            
            for sw in s_words:
                for ow in o_words:
                    domain_pairs[domain].append((sw, ow, weight))
        
        print(f"   📂 {domain:<20s} : {len(domain_pairs[domain]):>8,} paires pondérées")
    
    total = sum(len(v) for v in domain_pairs.values())
    print(f"   ✅ Total : {total:,} paires dans {len(domain_pairs)} domaines")
    return domain_pairs, word_freq, domain_vocab


# ═══════════════════════════════════════════════════════════════════
# NÉGATIFS STRUCTURÉS (amélioration 2)
# ═══════════════════════════════════════════════════════════════════

def build_structured_negatives(domain_vocab: Dict[str, Set[str]], 
                               all_words: List[str]) -> Dict[str, List[str]]:
    """
    Pour chaque mot, sélectionne des négatifs dans d'AUTRES domaines.
    
    Un négatif structuré = un mot qui n'apparaît JAMAIS dans
    le même domaine que le mot cible.
    """
    word_to_domains = defaultdict(set)
    for domain, words in domain_vocab.items():
        for w in words:
            word_to_domains[w].add(domain)
    
    # Pour chaque mot, collecter les candidats négatifs (autres domaines)
    negatives = {}
    words_list = sorted(all_words)
    
    for word in words_list:
        word_domains = word_to_domains.get(word, set())
        # Négatifs = mots qui ne partagent AUCUN domaine avec ce mot
        neg_candidates = []
        for other in words_list:
            if other == word:
                continue
            other_domains = word_to_domains.get(other, set())
            if not (word_domains & other_domains):
                neg_candidates.append(other)
        
        if neg_candidates:
            negatives[word] = neg_candidates
        else:
            # Fallback : tous les autres mots
            negatives[word] = [w for w in words_list if w != word]
    
    return negatives


# ═══════════════════════════════════════════════════════════════════
# ENTRAÎNEMENT EN DEUX PHASES (amélioration 3)
# ═══════════════════════════════════════════════════════════════════

def train_two_phase(swe: SemanticWaveEmbedding,
                    domain_pairs: Dict[str, List[Tuple[str, str, float]]],
                    word_freq: Dict[str, int],
                    negatives: Dict[str, List[str]],
                    all_terms: Set[str]):
    """Entraînement en deux phases avec négatifs structurés."""
    
    # Initialiser tous les ψ
    for term in all_terms:
        swe._init_psi(term)
    
    # ── PHASE 1 : Petits domaines riches ──
    print(f"\n{'─'*60}")
    print(f"  PHASE 1 — Domaines riches ({len(RICH_DOMAINS)} domaines)")
    print(f"  {PHASE1_EPOCHS} époques, lr={LR_INIT}")
    print(f"{'─'*60}")
    
    phase1_pairs = []
    for domain in RICH_DOMAINS:
        phase1_pairs.extend(domain_pairs.get(domain, []))
    phase1_pairs.extend([(b, a, w) for a, b, w in phase1_pairs])  # symétrie
    phase1_pairs = list(set(phase1_pairs))
    
    _train_epochs(swe, phase1_pairs, negatives, all_terms,
                  epochs=PHASE1_EPOCHS, lr=LR_INIT, tag="[P1]")
    
    # ── PHASE 2 : Tous domaines (CLINIQUE avec poids réduit) ──
    print(f"\n{'─'*60}")
    print(f"  PHASE 2 — Tous domaines (CLINIQUE poids ×0.3)")
    print(f"  {PHASE2_EPOCHS} époques, lr={LR_INIT * 0.3}")
    print(f"{'─'*60}")
    
    all_pairs_weighted = []
    for domain, pairs in domain_pairs.items():
        for a, b, w in pairs:
            if domain == "CLINIQUE":
                all_pairs_weighted.append((a, b, w * 0.3))
            else:
                all_pairs_weighted.append((a, b, w))
    all_pairs_weighted.extend([(b, a, w) for a, b, w in all_pairs_weighted])
    all_pairs_weighted = list(set(all_pairs_weighted))
    
    _train_epochs(swe, all_pairs_weighted, negatives, all_terms,
                  epochs=PHASE2_EPOCHS, lr=LR_INIT * 0.3, tag="[P2]")


def _train_epochs(swe: SemanticWaveEmbedding, pairs: List[Tuple],
                  negatives: Dict[str, List[str]], all_terms: Set[str],
                  epochs: int, lr: float, tag: str = ""):
    """Boucle d'entraînement avec cosine decay + négatifs structurés."""
    
    n_pairs = len(pairs)
    all_terms_list = list(all_terms)
    swe.lr = lr
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        np.random.shuffle(pairs)
        batch_size = 256
        
        for batch_start in range(0, n_pairs, batch_size):
            batch = pairs[batch_start:batch_start + batch_size]
            batch_gradients = defaultdict(lambda: np.zeros(DIM, dtype=np.complex128))
            batch_loss = 0.0
            
            for a, b, weight in batch:
                a, b = a.strip(), b.strip()
                if a not in swe._psi or b not in swe._psi:
                    continue
                
                psi_a = swe._psi[a]
                psi_b = swe._psi[b]
                
                # 1. Attraction pondérée
                diff = psi_a - psi_b
                dist_sq = np.sum(np.abs(diff) ** 2)
                attraction = weight * dist_sq
                
                grad_a = 2.0 * weight * diff
                grad_b = -2.0 * weight * diff
                batch_gradients[a] += grad_a
                batch_gradients[b] += grad_b
                batch_loss += attraction
                
                # 2. Négatif structuré (amélioration 2)
                if a in negatives and negatives[a]:
                    c = negatives[a][np.random.randint(len(negatives[a]))]
                    if c not in swe._psi:
                        swe._init_psi(c)
                    
                    psi_c = swe._psi[c]
                    diff_ac = psi_a - psi_c
                    dist_ac = np.sqrt(np.sum(np.abs(diff_ac) ** 2))
                    
                    margin = 0.7
                    if dist_ac < margin:
                        repulsion = (margin - dist_ac) ** 2
                        lambda_rep = 0.1 * weight  # proportionnel au poids
                        batch_loss += lambda_rep * repulsion
                        
                        if dist_ac > 1e-10:
                            grad_rep = -lambda_rep * 2.0 * (margin - dist_ac) * diff_ac / dist_ac
                            batch_gradients[a] += grad_rep
                            batch_gradients[c] -= grad_rep
            
            # Appliquer gradients
            for word, grad in batch_gradients.items():
                swe._psi[word] -= swe.lr * grad / len(batch)
                norm = np.sqrt(np.sum(np.abs(swe._psi[word]) ** 2))
                if norm > 3.0:
                    swe._psi[word] = swe._psi[word] / norm * 2.0
            
            epoch_loss += batch_loss
        
        avg_loss = epoch_loss / max(n_pairs, 1)
        swe._semantic_psi.clear()
        
        # Cosine decay (amélioration 4)
        swe.lr = lr * 0.5 * (1.0 + math.cos(math.pi * epoch / epochs))
        
        if epoch % 20 == 0:
            print(f"    {tag} Epoch {epoch:3d}/{epochs}: loss = {avg_loss:.6f}, lr = {swe.lr:.5f}")
    
    swe.trained = True


# ═══════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════

def test_medical_similarity(swe: SemanticWaveEmbedding):
    related_pairs = [
        ("paludisme", "fièvre"), ("paludisme", "frissons"),
        ("paludisme", "artésunate"), ("paludisme", "quinine"),
        ("paludisme", "moustiquaire"), ("anémie", "pâleur"),
        ("anémie", "fer"), ("pneumonie", "toux"),
        ("pneumonie", "dyspnée"), ("diabète", "glycémie"),
        ("diabète", "insuline"), ("hypertension", "tension"),
        ("tuberculose", "toux"), ("asthme", "dyspnée"),
        ("asthme", "inhalateur"), ("épilepsie", "convulsion"),
        ("VIH", "antirétroviral"), ("paludisme", "anophèle"),
        ("douleur", "paracétamol"), ("douleur", "morphine"),
        ("infection", "antibiotique"), ("vaccin", "immunité"),
        ("cœur", "cardiaque"), ("cœur", "infarctus"),
        ("grossesse", "accouchement"), ("enfant", "pédiatrie"),
        ("cancer", "chimiothérapie"), ("dépression", "antidépresseur"),
        ("obésité", "diabète"), ("tabac", "cancer"),
    ]
    
    unrelated_pairs = [
        ("paludisme", "chaise"), ("fièvre", "voiture"),
        ("cœur", "table"), ("asthme", "nuage"),
        ("vaccin", "téléphone"), ("diabète", "bureau"),
        ("cancer", "fenêtre"), ("grossesse", "ordinateur"),
        ("douleur", "stylo"), ("antibiotique", "ciel"),
    ]
    
    print(f"\n{'═'*70}")
    print("  🧪 TEST — Similarité Sémantique Médicale V2")
    print("═" * 70)
    
    related_sims, unrelated_sims = [], []
    
    print(f"\n  📊 Paires LIÉES (objectif > 0.55) :")
    for a, b in related_pairs:
        try:
            sim = swe.similarity(a, b)
            related_sims.append(sim)
            ok = sim > 0.55
            print(f"  {'✅' if ok else '❌'} {a+' ↔ '+b:<40s} {sim:.4f}")
        except Exception:
            pass
    
    print(f"\n  📊 Paires NON LIÉES (objectif < 0.55) :")
    for a, b in unrelated_pairs:
        try:
            sim = swe.similarity(a, b)
            unrelated_sims.append(sim)
            ok = sim < 0.55
            print(f"  {'✅' if ok else '❌'} {a+' ↔ '+b:<40s} {sim:.4f}")
        except Exception:
            pass
    
    avg_rel = np.mean(related_sims) if related_sims else 0
    avg_unrel = np.mean(unrelated_sims) if unrelated_sims else 0
    separation = avg_rel - avg_unrel
    
    n_rel_ok = sum(1 for s in related_sims if s > 0.55)
    n_unrel_ok = sum(1 for s in unrelated_sims if s < 0.55)
    
    print(f"\n  📊 RÉSULTATS V2 :")
    print(f"     Similarité liés     = {avg_rel:.4f}")
    print(f"     Similarité non liés = {avg_unrel:.4f}")
    print(f"     Séparation Δ        = {separation:+.4f}")
    print(f"     Liés OK             = {n_rel_ok}/{len(related_sims)}")
    print(f"     Non liés OK         = {n_unrel_ok}/{len(unrelated_sims)}")
    
    quality = ("✅ EXCELLENT" if separation > 0.20 else
               "⚠️ BON" if separation > 0.12 else
               "⚠️ CORRECT" if separation > 0.08 else "❌ INSUFFISANT")
    print(f"     VERDICT             = {quality}")
    
    return {'avg_related': avg_rel, 'avg_unrelated': avg_unrel,
            'separation': separation, 'n_rel_ok': n_rel_ok,
            'n_rel_total': len(related_sims)}


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t_total = time.time()
    
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🌊 TRAINER V2 — Semantic Wave Medical (4 améliorations)   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # 1. Chargement pondéré
    print(f"\n{'═'*70}")
    print("  ÉTAPE 1 — Chargement pondéré par type de relation")
    print("═" * 70)
    domain_pairs, word_freq, domain_vocab = load_weighted_pairs()
    
    # 2. Filtrer
    valid_words = {w for w, c in word_freq.items() if c >= MIN_PAIR_FREQ}
    for domain in domain_pairs:
        domain_pairs[domain] = [(a, b, w) for a, b, w in domain_pairs[domain]
                                if a in valid_words and b in valid_words]
    
    all_terms = set()
    for pairs in domain_pairs.values():
        for a, b, _ in pairs:
            all_terms.add(a)
            all_terms.add(b)
    
    print(f"   Mots valides : {len(valid_words):,}")
    print(f"   Termes dans paires : {len(all_terms):,}")
    
    # 3. Négatifs structurés
    print(f"\n{'═'*70}")
    print("  ÉTAPE 2 — Négatifs structurés (autres domaines)")
    print("═" * 70)
    negatives = build_structured_negatives(domain_vocab, list(all_terms))
    avg_negs = np.mean([len(v) for v in negatives.values()])
    print(f"   Négatifs structurés pour {len(negatives):,} mots")
    print(f"   Moyenne négatifs/mot : {avg_negs:.0f}")
    
    # 4. Entraînement 2 phases
    print(f"\n{'═'*70}")
    print("  ÉTAPE 3 — Entraînement en 2 phases")
    print("═" * 70)
    
    swe = SemanticWaveEmbedding(dim=DIM, lr=LR_INIT)
    train_two_phase(swe, domain_pairs, word_freq, negatives, all_terms)
    
    # 5. Test
    results = test_medical_similarity(swe)
    
    # 6. Sauvegarde
    print(f"\n{'═'*70}")
    print("  ÉTAPE 4 — Sauvegarde")
    print("═" * 70)
    swe.save(str(OUTPUT_PATH))
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"   💾 {OUTPUT_PATH}")
    print(f"   📦 {size_mb:.1f} Mo | {swe.vocab_size} termes")
    
    # 7. Bilan
    print(f"\n{'═'*70}")
    print("  ✅ BILAN FINAL V2")
    print("═" * 70)
    print(f"""
  Phases               : 2 ({PHASE1_EPOCHS} + {PHASE2_EPOCHS} époques)
  Vocabulaire          : {swe.vocab_size:,} termes
  Négatifs structurés  : {len(negatives):,} mots
  Pondération          : symptôme ×5, traitement ×3, urgence ×4
  CLINIQUE             : poids ×0.3
  Temps total          : {time.time() - t_total:.1f}s ({(time.time() - t_total)/60:.1f}min)
  
  Similarité liés      : {results['avg_related']:.4f}
  Similarité non liés  : {results['avg_unrelated']:.4f}
  Séparation Δ         : {results['separation']:+.4f}
  Liés OK              : {results['n_rel_ok']}/{results['n_rel_total']}
  
  📁 {OUTPUT_PATH}
""")