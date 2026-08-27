"""
🌊 TRAINER V3 — Focus : top 500 termes, dim=256
================================================
Problème V1/V2 : 1906 termes, 16K paires → signal dilué dans 512D.
Solution : réduire la dimension à 256 + ne garder que les 500 termes
les plus fréquents (ceux qui ont assez de co-occurrences pour bouger).

Objectif : séparation > +0.15

Auteur : THU — Univers-Holistique
Date   : 2026-08-24
"""

import sys, os, math, time, json, pickle, re
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "vital-ka" / "core" / "python"))
from semantic_wave_embedding import SemanticWaveEmbedding

FACTS_DIR = Path(__file__).resolve().parent / "vital-ka" / "data" / "medical_holograms"
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "semantic_wave_embedding_medical_v3.pkl"
DIM = 256
TOP_TERMS = 500
EPOCHS = 250
LR = 0.03

ALL_DOMAINS = [
    "CHRONIQUES", "CLINIQUE", "GENERAL", "MALADIES",
    "MERE_ENFANT", "MNT", "NUTRITION", "PALUDISME",
    "PEDIATRIE", "PHARMACIE", "PHYTOTHERAPIE", "SANTE_MENTALE",
    "URGENCES", "VACCINATION", "VIH_TB",
]

STOPWORDS = {
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
    'au', 'aux', 'en', 'pour', 'avec', 'sur', 'est', 'sont', 'ce',
    'cette', 'dans', 'à', 'a', 'que', 'qui', 'pas', 'ne', 'plus',
    'tout', 'tous', 'il', 'elle', 'ils', 'elles', 'nous', 'vous',
    'son', 'sa', 'ses', 'leur', 'leurs', 'kg', 'mg', 'ml', 'g', 'j', 'h',
    'min', 'si', 'd', 'l', 'oui', 'non', 'true', 'false', 'pas', 'peut',
}

RELATION_WEIGHTS = {
    'présente_symptôme': 5.0, 'presente_symptome': 5.0,
    'traitement': 3.0, 'dose': 2.0, 'diagnostic': 3.0,
    'prévention': 3.0, 'complication': 3.0, 'urgence': 4.0,
}

def clean_word(w):
    w = w.strip().lower().replace('_', ' ')
    w = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', w)
    return re.sub(r'\s+', ' ', w).strip()

# ═══════════════════════════════════════════════════════════════════
def load_and_filter():
    """Charge les paires et ne garde que les top termes."""
    word_freq = Counter()
    raw_pairs = []
    
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
            for w in o_words:
                word_freq[w] += 1
            
            for sw in s_words:
                for ow in o_words:
                    raw_pairs.append((sw, ow, weight))
    
    # Top termes
    top_words = {w for w, c in word_freq.most_common(TOP_TERMS)}
    
    pairs = [(a, b, w) for a, b, w in raw_pairs 
             if a in top_words and b in top_words]
    pairs = list(set(pairs))
    np.random.shuffle(pairs)
    
    print(f"   Mots totaux   : {len(word_freq):,}")
    print(f"   Top {TOP_TERMS} termes : {len(top_words):,}")
    print(f"   Paires brutes : {len(raw_pairs):,}")
    print(f"   Paires filtrées : {len(pairs):,}")
    print(f"   Top 20 termes : {', '.join(f'{w}({c})' for w,c in word_freq.most_common(20))}")
    
    return pairs, top_words, word_freq

# ═══════════════════════════════════════════════════════════════════
def train_focused(swe, pairs, top_words, word_freq):
    """Entraînement avec négatifs aléatoires dans les top termes."""
    
    all_terms = sorted(top_words)
    for term in all_terms:
        swe._init_psi(term)
    
    # Pondération par fréquence (amélioration : mots fréquents bougent plus)
    max_freq = max(word_freq.values())
    term_weight = {w: min(2.0, 0.5 + 1.5 * word_freq[w] / max_freq) 
                   for w in all_terms}
    
    n_pairs = len(pairs)
    swe.lr = LR
    
    for epoch in range(EPOCHS):
        epoch_loss = 0.0
        np.random.shuffle(pairs)
        batch_size = 512
        
        for batch_start in range(0, n_pairs, batch_size):
            batch = pairs[batch_start:batch_start + batch_size]
            batch_gradients = defaultdict(lambda: np.zeros(DIM, dtype=np.complex128))
            batch_loss = 0.0
            
            for a, b, weight in batch:
                if a not in swe._psi or b not in swe._psi:
                    continue
                
                psi_a = swe._psi[a]
                psi_b = swe._psi[b]
                
                # Attraction pondérée (freq × relation)
                tw = term_weight.get(a, 1.0) * term_weight.get(b, 1.0)
                effective_weight = weight * tw
                
                diff = psi_a - psi_b
                dist_sq = np.sum(np.abs(diff) ** 2)
                batch_loss += effective_weight * dist_sq
                
                grad_a = 2.0 * effective_weight * diff
                grad_b = -2.0 * effective_weight * diff
                batch_gradients[a] += grad_a
                batch_gradients[b] += grad_b
                
                # Répulsion (négatif aléatoire)
                c = all_terms[np.random.randint(len(all_terms))]
                if c in (a, b):
                    continue
                if c not in swe._psi:
                    swe._init_psi(c)
                
                psi_c = swe._psi[c]
                diff_ac = psi_a - psi_c
                dist_ac = np.sqrt(np.sum(np.abs(diff_ac) ** 2))
                
                margin = 0.65  # plus strict
                if dist_ac < margin:
                    repulsion = (margin - dist_ac) ** 2
                    lambda_rep = 0.1 * effective_weight
                    batch_loss += lambda_rep * repulsion
                    
                    if dist_ac > 1e-10:
                        grad_rep = -lambda_rep * 2.0 * (margin - dist_ac) * diff_ac / dist_ac
                        batch_gradients[a] += grad_rep
                        batch_gradients[c] -= grad_rep
            
            for word, grad in batch_gradients.items():
                swe._psi[word] -= swe.lr * grad / len(batch)
                norm = np.sqrt(np.sum(np.abs(swe._psi[word]) ** 2))
                if norm > 3.0:
                    swe._psi[word] = swe._psi[word] / norm * 2.0
            
            epoch_loss += batch_loss
        
        avg_loss = epoch_loss / max(n_pairs, 1)
        swe._semantic_psi.clear()
        swe.lr = LR * 0.5 * (1.0 + math.cos(math.pi * epoch / EPOCHS))
        
        if epoch % 25 == 0:
            print(f"    Epoch {epoch:3d}/{EPOCHS}: loss = {avg_loss:.6f}, lr = {swe.lr:.5f}")
    
    swe.trained = True
    return avg_loss

# ═══════════════════════════════════════════════════════════════════
def test_medical_similarity(swe):
    related = [
        ("paludisme", "fièvre"), ("paludisme", "frissons"),
        ("paludisme", "artésunate"), ("paludisme", "quinine"),
        ("paludisme", "moustiquaire"), ("anémie", "pâleur"),
        ("anémie", "fer"), ("pneumonie", "toux"),
        ("pneumonie", "dyspnée"), ("diabète", "glycémie"),
        ("diabète", "insuline"), ("hypertension", "tension"),
        ("tuberculose", "toux"), ("asthme", "dyspnée"),
        ("asthme", "inhalateur"), ("épilepsie", "convulsion"),
        ("VIH", "antirétroviral"), ("douleur", "paracétamol"),
        ("douleur", "morphine"), ("infection", "antibiotique"),
        ("vaccin", "immunité"), ("cœur", "cardiaque"),
        ("cœur", "infarctus"), ("grossesse", "accouchement"),
        ("enfant", "pédiatrie"), ("cancer", "chimiothérapie"),
        ("dépression", "antidépresseur"), ("obésité", "diabète"),
        ("tabac", "cancer"),
    ]
    unrelated = [
        ("paludisme", "chaise"), ("fièvre", "voiture"),
        ("cœur", "table"), ("asthme", "nuage"),
        ("vaccin", "téléphone"), ("diabète", "bureau"),
        ("cancer", "fenêtre"), ("grossesse", "ordinateur"),
        ("douleur", "stylo"), ("antibiotique", "ciel"),
    ]
    
    rel_sims, unrel_sims = [], []
    for a, b in related:
        try:
            rel_sims.append(swe.similarity(a, b))
        except Exception:
            pass
    for a, b in unrelated:
        try:
            unrel_sims.append(swe.similarity(a, b))
        except Exception:
            pass
    
    avg_rel = np.mean(rel_sims)
    avg_unrel = np.mean(unrel_sims)
    sep = avg_rel - avg_unrel
    n_ok = sum(1 for s in rel_sims if s > 0.55)
    
    print(f"  Similarité liés     = {avg_rel:.4f}")
    print(f"  Similarité non liés = {avg_unrel:.4f}")
    print(f"  Séparation Δ        = {sep:+.4f}")
    print(f"  Liés OK (>0.55)     = {n_ok}/{len(rel_sims)}")
    quality = "✅ BON" if sep > 0.12 else ("⚠️ CORRECT" if sep > 0.08 else "❌ INSUFFISANT")
    print(f"  VERDICT             = {quality}")
    
    return {'avg_related': avg_rel, 'avg_unrelated': avg_unrel,
            'separation': sep, 'n_rel_ok': n_ok, 'n_rel_total': len(rel_sims)}

# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    t_total = time.time()
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print(f"║  TRAINER V3 — Top {TOP_TERMS} termes, dim={DIM}            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    print(f"\n📊 ÉTAPE 1 — Chargement + filtre top {TOP_TERMS}")
    pairs, top_words, word_freq = load_and_filter()
    
    print(f"\n🏋️ ÉTAPE 2 — Entraînement ({EPOCHS} époques, dim={DIM})")
    swe = SemanticWaveEmbedding(dim=DIM, lr=LR)
    final_loss = train_focused(swe, pairs, top_words, word_freq)
    
    print(f"\n🧪 ÉTAPE 3 — Test")
    results = test_medical_similarity(swe)
    
    print(f"\n💾 ÉTAPE 4 — Sauvegarde")
    swe.save(str(OUTPUT_PATH))
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    elapsed = time.time() - t_total
    print(f"   {OUTPUT_PATH.name} ({size_mb:.1f} Mo)")
    print(f"\n⏱️  Temps : {elapsed:.1f}s ({elapsed/60:.1f}min)")
    print(f"   Δ V1 → V3 : {results['separation'] - 0.074:+.4f}")