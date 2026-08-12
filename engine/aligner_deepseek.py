#!/usr/bin/env python3
"""
aligner_deepseek.py — Aligne les traductions DeepSeek avec les phrases
=========================================================================
Pour chaque problème, on a :
  - Le texte du problème (N phrases)
  - La traduction DeepSeek (M opérations)
  
On aligne : phrase i → opération i (proportionnellement).
Puis on entraîne un classifieur MiniLM sur (phrase, opération).

Les labels DeepSeek remplacent les annotations <<...>> heuristiques.
Résultat attendu : 58.4% → >70% sur la classification d'opération.
"""

import sys, os, re, json, time, pickle
import numpy as np
from collections import Counter, defaultdict
from typing import List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traducteur_deepseek import parser_operations


# ═══════════════════════════════════════════════════════════════════════════
# 1. ALIGNEMENT PHRASE → OPÉRATION
# ═══════════════════════════════════════════════════════════════════════════

def charger_traductions(path="data/deepseek_distill_train.json"):
    """Charge le dataset de distillation DeepSeek."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, path)
    if not os.path.exists(path):
        print(f"⚠ Dataset non trouvé : {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def aligner_phrases_operations(probleme: str, operations_text: str) -> List[dict]:
    """
    Aligne chaque phrase du problème avec une opération DeepSeek.
    
    Retourne [(phrase, opération_type, params), ...]
    """
    # Découper le problème en phrases
    sentences = re.split(r'(?<=[.;!?])\s+', probleme.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Parser les opérations
    ops = parser_operations(operations_text)
    
    # Filtrer les QUERY (ce sont les questions, pas des actions)
    ops = [op for op in ops if op.get('op') != 'QUERY']
    
    if not ops:
        return []
    
    # Alignement proportionnel : phrase i → opération i (si même nombre)
    # ou mapping proportionnel
    n_phrases = len([s for s in sentences if re.search(r'\d', s)])
    if n_phrases == 0:
        return []
    
    pairs = []
    op_idx = 0
    for sent in sentences:
        if not re.search(r'\d', sent):
            continue  # ignorer les phrases sans nombre
        
        if op_idx < len(ops):
            op = ops[op_idx]
            op_type = op.get('op', '')
            # Normaliser les noms
            op_type = NORMALISER.get(op_type, op_type)
            
            pairs.append({
                "sentence": sent,
                "operation": op_type,
                "params": op,
            })
            op_idx += 1
        else:
            # Plus d'opérations que de phrases → ajouter au dernier
            if pairs:
                pairs[-1]["sentence"] += " " + sent
    
    return pairs


# Normalisation des noms d'opérations
NORMALISER = {
    'INIT': 'HAS',
    'ADD': 'GAIN',
    'SUBTRACT': 'LOSE',
    'MULTIPLY': 'MULT',
    'DIVIDE': 'DIV',
    'CROSS_MULT': 'CROSS_MULT',
    'RATE': 'RATE',
    'DURATION': 'DURATION',
    'FRACTION': 'FRACTION',
    'GAVE_TO': 'GAVE_TO',
    'PARTITION': 'PARTITION',
    'TIMES_AS_MANY': 'TIMES_AS_MANY',
}


def creer_dataset(traductions: List[dict]) -> List[dict]:
    """Crée le dataset (phrase, opération) à partir des traductions DeepSeek."""
    dataset = []
    stats = defaultdict(int)
    
    for item in traductions:
        probleme = item.get('input', '')
        output = item.get('output', '')
        
        if not output.strip():
            continue
        
        pairs = aligner_phrases_operations(probleme, output)
        for p in pairs:
            dataset.append(p)
            stats[p['operation']] += 1
    
    print(f"Dataset : {len(dataset)} paires phrase→opération")
    print(f"Distribution :")
    for op, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {op:<20s} : {count:>4d}")
    
    return dataset


# ═══════════════════════════════════════════════════════════════════════════
# 2. ENTRAÎNEMENT MINILM
# ═══════════════════════════════════════════════════════════════════════════

def entrainer(dataset: List[dict]) -> dict:
    """
    Entraîne une régression logistique sur les embeddings MiniLM.
    Labels : DeepSeek (supervision sémantique).
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    from sentence_transformers import SentenceTransformer
    
    print(f"\nEncodage MiniLM...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    phrases = [d['sentence'] for d in dataset]
    labels = [d['operation'] for d in dataset]
    
    X = model.encode(phrases, batch_size=32, show_progress_bar=True)
    y = np.array(labels)
    
    print(f"X shape: {X.shape}, y shape: {y.shape}")
    
    # Normaliser
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Entraîner
    print(f"Entraînement Régression Logistique...")
    t0 = time.time()
    clf = LogisticRegression(max_iter=500, C=1.0, class_weight='balanced')
    clf.fit(X_scaled, y)
    print(f"  Temps : {time.time()-t0:.1f}s")
    
    # Accuracy
    train_acc = clf.score(X_scaled, y)
    try:
        cv_scores = cross_val_score(clf, X_scaled, y, cv=5)
        cv_acc = np.mean(cv_scores)
        cv_std = np.std(cv_scores)
    except:
        cv_acc, cv_std = 0, 0
    
    print(f"  Accuracy train : {100*train_acc:.1f}%")
    print(f"  Accuracy CV    : {100*cv_acc:.1f}% (±{100*cv_std:.1f}%)")
    
    # Rapport par classe
    from sklearn.metrics import classification_report
    y_pred = clf.predict(X_scaled)
    print(f"\n  Rapport par classe :")
    print(classification_report(y, y_pred, digits=2))
    
    # Test rapide
    print(f"\n  Test rapide :")
    tests = [
        "John has 5 apples.",
        "He buys 3 more.",
        "She ate 4 cookies.",
        "Mary has 3 times as many.",
        "There are 6 boxes.",
        "Each box has 5 pencils.",
        "James earns 20 dollars per hour.",
        "He works 8 hours.",
        "They are split into 4 equal groups.",
        "A pizza is cut into 8 slices.",
        "45 are sold.",
        "Mary gave him 3 more apples.",
        "Sue gives 3 to her friend.",
    ]
    for t in tests:
        emb = model.encode([t])[0]
        s = scaler.transform([emb])
        pred = clf.predict(s)[0]
        prob = clf.predict_proba(s)[0]
        conf = max(prob)
        print(f"    {t:<45s} → {pred:<15s} (conf={conf:.2f})")
    
    return {
        "classifier": clf,
        "scaler": scaler,
        "classes": list(clf.classes_),
        "train_accuracy": train_acc,
        "cv_accuracy": cv_acc,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═══ ALIGNEMENT DEEPSEEK → PHRASE → OPÉRATION ═══\n")
    
    # Charger les traductions
    traductions = charger_traductions()
    if not traductions:
        sys.exit(1)
    
    print(f"Traductions chargées : {len(traductions)}")
    
    # Créer le dataset
    dataset = creer_dataset(traductions)
    
    # Entraîner
    modele = entrainer(dataset)
    
    # Sauvegarder
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'minilm_deepseek.pkl')
    with open(out_path, 'wb') as f:
        pickle.dump(modele, f)
    print(f"\n✓ Modèle sauvegardé : {out_path}")