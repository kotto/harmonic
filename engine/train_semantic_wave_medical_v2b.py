"""
🌊 TRAINER V2b — Warm-start V1 + époques rapides
=================================================
Charge le modèle V1 (16.8 Mo, 1906 termes, séparation +0.07)
et ajoute 200 époques rapides avec pondération + négatifs aléatoires.

Objectif : passer de +0.07 à +0.15+ de séparation.

Auteur : THU — Univers-Holistique
Date   : 2026-08-24
"""

import sys, os, math, time, json, pickle, re
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "vital-ka" / "core" / "python"))
from semantic_wave_embedding import SemanticWaveEmbedding, base_encode

FACTS_DIR = Path(__file__).resolve().parent / "vital-ka" / "data" / "medical_holograms"
V1_PATH = Path(__file__).resolve().parent / "data" / "semantic_wave_embedding_medical.pkl"
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "semantic_wave_embedding_medical_v2b.pkl"
DIM = 512
EPOCHS = 200
LR = 0.01

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
    'son', 'sa', 'ses', 'leur', 'leurs', 'mon', 'ma', 'mes',
    'kg', 'mg', 'ml', 'g', 'j', 'h', 'min', 'si', 'd', 'l',
    'oui', 'non', 'true', 'false', 'none', 'pas', 'peut',
}

RELATION_WEIGHTS = {
    'présente_symptôme': 5.0, 'presente_symptome': 5.0, 'symptome': 5.0,
    'traitement': 3.0, 'dose': 2.0, 'diagnostic': 3.0, 'prévention': 3.0,
    'complication': 3.0, 'urgence': 4.0,
}

def clean_word(w):
    w = w.strip().lower().replace('_', ' ')
    w = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', w)
    return re.sub(r'\s+', ' ', w).strip()

# ═══════════════════════════════════════════════════════════════════
# CHARGEMENT RAPIDE
# ═══════════════════════════════════════════════════════════════════

def load_weighted_pairs_fast():
    """Charge les paires pondérées (sans groupement par domaine)."""
    pairs_positive = []
    pairs_negative_by_domain = defaultdict(list)
    word_freq = Counter()
    
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
            
            for sw in s_words:
                word_freq[sw] += 1
            for ow in o_words:
                word_freq[ow] += 1
            
            for sw in s_words:
                for ow in o_words:
                    pairs_positive.append((sw, ow, weight))
                    pairs_negative_by_domain[domain].append(sw)

    return pairs_positive, pairs_negative_by_domain, word_freq

# ═══════════════════════════════════════════════════════════════════
def test_medical_similarity(swe):
    related_pairs = [
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
    unrelated_pairs = [
        ("paludisme", "chaise"), ("fièvre", "voiture"),
        ("cœur", "table"), ("asthme", "nuage"),
        ("vaccin", "téléphone"), ("diabète", "bureau"),
        ("cancer", "fenêtre"), ("grossesse", "ordinateur"),
        ("douleur", "stylo"), ("antibiotique", "ciel"),
    ]
    
    related_sims, unrelated_sims = [], []
    for a, b in related_pairs:
        try:
            related_sims.append(swe.similarity(a, b))
        except Exception:
            pass
    for a, b in unrelated_pairs:
        try:
            unrelated_sims.append(swe.similarity(a, b))
        except Exception:
            pass
    
    avg_rel = np.mean(related_sims)
    avg_unrel = np.mean(unrelated_sims)
    sep = avg_rel - avg_unrel
    n_ok = sum(1 for s in related_sims if s > 0.55)
    
    print(f"  Similarité liés     = {avg_rel:.4f}")
    print(f"  Similarité non liés = {avg_unrel:.4f}")
    print(f"  Séparation Δ        = {sep:+.4f}")
    print(f"  Liés OK (>0.55)     = {n_ok}/{len(related_sims)}")
    print(f"  {'✅' if sep > 0.12 else '⚠️' if sep > 0.08 else '❌'} "
          f"{'EXCELLENT' if sep > 0.20 else 'BON' if sep > 0.12 else 'CORRECT' if sep > 0.08 else 'INSUFFISANT'}")
    
    return {'avg_related': avg_rel, 'avg_unrelated': avg_unrel,
            'separation': sep, 'n_rel_ok': n_ok, 'n_rel_total': len(related_sims)}

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t_total = time.time()
    
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  TRAINER V2b — Warm-start V1 + 200 époques rapides         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # 1. Charger V1
    print(f"\n📂 Chargement du modèle V1...")
    swe = SemanticWaveEmbedding.load(str(V1_PATH))
    print(f"   ✅ {swe.vocab_size} termes, séparation V1 = +0.07")
    
    # 2. Charger paires pondérées
    print(f"\n📊 Chargement des paires pondérées...")
    pairs_positive, pairs_negative_by_domain, word_freq = load_weighted_pairs_fast()
    
    # Filtrer aux mots connus par V1
    valid_words = set(swe._psi.keys())
    pairs_filtered = [(a, b, w) for a, b, w in pairs_positive 
                      if a in valid_words and b in valid_words]
    pairs_filtered = list(set(pairs_filtered))  # dédupliquer
    np.random.shuffle(pairs_filtered)
    
    print(f"   ✅ {len(pairs_filtered):,} paires valides (dans vocab V1)")
    
    # 3. Entraînement rapide (négatifs aléatoires)
    print(f"\n🏋️ Entraînement ({EPOCHS} époques, lr={LR})...")
    n_pairs = len(pairs_filtered)
    words_list = sorted(valid_words)
    swe.lr = LR
    
    for epoch in range(EPOCHS):
        epoch_loss = 0.0
        np.random.shuffle(pairs_filtered)
        batch_size = 512
        
        for batch_start in range(0, n_pairs, batch_size):
            batch = pairs_filtered[batch_start:batch_start + batch_size]
            batch_gradients = defaultdict(lambda: np.zeros(DIM, dtype=np.complex128))
            batch_loss = 0.0
            
            for a, b, weight in batch:
                if a not in swe._psi or b not in swe._psi:
                    continue
                
                psi_a = swe._psi[a]
                psi_b = swe._psi[b]
                
                # Attraction pondérée
                diff = psi_a - psi_b
                dist_sq = np.sum(np.abs(diff) ** 2)
                attraction = weight * dist_sq
                
                grad_a = 2.0 * weight * diff
                grad_b = -2.0 * weight * diff
                batch_gradients[a] += grad_a
                batch_gradients[b] += grad_b
                batch_loss += attraction
                
                # Répulsion rapide (négatif aléatoire)
                c = words_list[np.random.randint(len(words_list))]
                if c in (a, b):
                    continue
                if c not in swe._psi:
                    swe._init_psi(c)
                
                psi_c = swe._psi[c]
                diff_ac = psi_a - psi_c
                dist_ac = np.sqrt(np.sum(np.abs(diff_ac) ** 2))
                
                margin = 0.7
                if dist_ac < margin:
                    repulsion = (margin - dist_ac) ** 2
                    lambda_rep = 0.05 * weight
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
        
        if epoch % 20 == 0:
            print(f"    Epoch {epoch:3d}/{EPOCHS}: loss = {avg_loss:.6f}, lr = {swe.lr:.5f}")
    
    print(f"    ✅ Entraînement terminé ({time.time() - t_total:.1f}s)")
    
    # 4. Test
    print(f"\n{'═'*70}")
    print("  🧪 TEST V2b")
    print("═" * 70)
    results = test_medical_similarity(swe)
    
    # 5. Sauvegarde
    print(f"\n💾 Sauvegarde...")
    swe.save(str(OUTPUT_PATH))
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"   {OUTPUT_PATH.name} ({size_mb:.1f} Mo)")
    print(f"\n⏱️  Temps total : {time.time() - t_total:.1f}s ({(time.time()-t_total)/60:.1f}min)")
    print(f"   Δ V1 → V2b : {results['separation'] - 0.074:+0.4f}")