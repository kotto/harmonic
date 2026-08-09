#!/usr/bin/env python3
"""
train_minilm_operations.py — Entraîne MiniLM à mapper phrase → opération mathématique
========================================================================================

Contrairement au classifieur v4 (44.1% sur des mots isolés), celui-ci apprend
le mapping SÉMANTIQUE : phrase complète → type d'opération.

Dataset : 1101 problèmes d'entraînement GSM8K
Alignement : opération <<...>> → phrase source (proportionnel)
Modèle : MiniLM (384-dim) + Régression Logistique

SORTIE : minilm_operations.pkl (classifieur + scaler)
"""

import sys, os, re, json, time, pickle
import numpy as np
from collections import Counter, defaultdict
from typing import List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════════════════════════════════════
# 1. CHARGEMENT DES DONNÉES + ALIGNEMENT
# ═══════════════════════════════════════════════════════════════════════════

def extraire_operations(answer: str) -> List[Tuple[str, float, float, float]]:
    """Extrait les opérations <<a op b = c>>."""
    ops = re.findall(r'<<(.*?)>>', answer)
    results = []
    for op in ops:
        nums = [float(x) for x in re.findall(r'[\d.]+', op.strip())]
        symbols = re.findall(r'[+\-*/]', op.strip())
        current = nums[0] if nums else 0
        for i, sym in enumerate(symbols):
            if i + 1 < len(nums):
                b = nums[i + 1]
                if sym == '+': new_val = current + b
                elif sym == '-': new_val = current - b
                elif sym == '*': new_val = current * b
                elif sym == '/': new_val = current / b if b != 0 else 0
                else: new_val = current
                results.append((sym, current, b, new_val))
                current = new_val
    return results


def classer_operation(op_symbol: str, phrase: str) -> str:
    """Classe l'opération en type d'action."""
    pl = phrase.lower()

    if 'times as many' in pl or 'times as much' in pl: return 'TIMES_AS_MANY'
    if 'twice' in pl or 'double' in pl or 'triple' in pl: return 'TIMES_AS_MANY'
    if ('each' in pl or 'every' in pl) and ('has' in pl or 'have' in pl or 'costs' in pl): return 'CROSS_MULT'
    if 'earns' in pl and 'per' in pl: return 'RATE'
    if 'per hour' in pl or 'per day' in pl: return 'RATE'
    if 'split' in pl or 'divided' in pl or 'among' in pl: return 'PARTITION'
    if 'there are' in pl or 'there were' in pl: return 'THERE_ARE'
    if 'are sold' in pl: return 'ARE_SOLD'
    if 'gave' in pl and 'to' in pl: return 'GAVE_TO'
    if 'cut into' in pl: return 'CUT_INTO'
    if 'works' in pl and ('hour' in pl or 'day' in pl): return 'DURATION'

    if op_symbol == '+': return 'GAIN'
    elif op_symbol == '-': return 'LOSE'
    elif op_symbol == '*': return 'MULT'
    elif op_symbol == '/': return 'DIV'

    return 'HAS'


def aligner_phrase(operations: List, sentences: List[str], op_idx: int, total: int) -> Optional[str]:
    """Aligne une opération avec sa phrase source (mapping proportionnel)."""
    if not sentences: return None
    numeric_sents = [(i, s) for i, s in enumerate(sentences) if re.search(r'\d', s)]
    if not numeric_sents: return None
    ratio = (op_idx + 0.5) / total
    idx = min(len(numeric_sents) - 1, int(ratio * len(numeric_sents)))
    return numeric_sents[idx][1]


def creer_dataset(train_problems: List[dict]) -> List[dict]:
    """
    Crée le dataset : phrase → opération.

    Retourne [{"sentence": ..., "operation": ..., "value": ...}, ...]
    """
    dataset = []
    skipped = 0

    for p in train_problems:
        question = p.get('question', '')
        answer = p.get('answer', '')

        ops = extraire_operations(answer)
        if not ops:
            skipped += 1
            continue

        sentences = re.split(r'(?<=[.;!?])\s+', question.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        total = len(ops)
        for i, (sym, a, b, result) in enumerate(ops):
            phrase = aligner_phrase(ops, sentences, i, total)
            if phrase is None:
                continue

            op_type = classer_operation(sym, phrase)

            dataset.append({
                "sentence": phrase,
                "operation": op_type,
                "value": b,  # l'opérande
            })

    print(f"  Dataset : {len(dataset)} paires phrase→opération")
    print(f"  Problèmes sans opérations : {skipped}")

    # Distribution
    counter = Counter(d['operation'] for d in dataset)
    print(f"  Distribution :")
    for op, count in counter.most_common():
        print(f"    {op:<20s} : {count:>4d}")

    return dataset


# ═══════════════════════════════════════════════════════════════════════════
# 2. ENCODAGE MINILM
# ═══════════════════════════════════════════════════════════════════════════

_minilm = None

def get_minilm():
    global _minilm
    if _minilm is None:
        from sentence_transformers import SentenceTransformer
        print("  Chargement MiniLM...")
        _minilm = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("  ✓ MiniLM chargé")
    return _minilm


def encoder_phrases(phrases: List[str], batch_size: int = 32) -> np.ndarray:
    """Encode une liste de phrases en vecteurs MiniLM (384-dim)."""
    model = get_minilm()
    embeddings = model.encode(phrases, batch_size=batch_size, show_progress_bar=True)
    return embeddings


# ═══════════════════════════════════════════════════════════════════════════
# 3. ENTRAÎNEMENT DU CLASSIFIEUR
# ═══════════════════════════════════════════════════════════════════════════

def entrainer_classifieur(dataset: List[dict]) -> dict:
    """
    Entraîne une régression logistique sur les embeddings MiniLM.

    Retourne {"classifier": ..., "scaler": ..., "classes": [...], "accuracy": ...}
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score

    print("\n  Encodage des phrases avec MiniLM...")
    phrases = [d['sentence'] for d in dataset]
    labels = [d['operation'] for d in dataset]
    X = encoder_phrases(phrases)
    y = np.array(labels)

    print(f"  X shape: {X.shape}, y shape: {y.shape}")

    # Normaliser
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Entraîner
    print("\n  Entraînement Régression Logistique...")
    t0 = time.time()
    clf = LogisticRegression(
        max_iter=500,
        C=1.0,
        class_weight='balanced',
    )
    clf.fit(X_scaled, y)
    dt = time.time() - t0

    # Accuracy
    train_acc = clf.score(X_scaled, y)
    cv_scores = cross_val_score(clf, X_scaled, y, cv=5)
    cv_acc = np.mean(cv_scores)

    print(f"  Entraînement : {dt:.1f}s")
    print(f"  Accuracy train : {100*train_acc:.1f}%")
    print(f"  Accuracy CV 5  : {100*cv_acc:.1f}% (±{100*np.std(cv_scores):.1f}%)")

    # Matrice de confusion simplifiée
    from sklearn.metrics import classification_report
    y_pred = clf.predict(X_scaled)
    print(f"\n  Rapport par classe :")
    print(classification_report(y, y_pred, digits=2))

    return {
        "classifier": clf,
        "scaler": scaler,
        "classes": list(clf.classes_),
        "train_accuracy": train_acc,
        "cv_accuracy": cv_acc,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. SAUVEGARDE + TEST RAPIDE
# ═══════════════════════════════════════════════════════════════════════════

def sauvegarder_modele(modele: dict, path: str = None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'minilm_operations.pkl')
    with open(path, 'wb') as f:
        pickle.dump(modele, f)
    print(f"\n  Modèle sauvegardé : {path}")


def test_rapide(modele: dict):
    """Test sur quelques phrases."""
    clf = modele['classifier']
    scaler = modele['scaler']
    model = get_minilm()

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
    ]

    print("\n  Test rapide :")
    for t in tests:
        emb = model.encode([t])[0]
        emb_scaled = scaler.transform([emb])
        pred = clf.predict(emb_scaled)[0]
        probs = clf.predict_proba(emb_scaled)[0]
        conf = max(probs)
        print(f"    {t:<45s} → {pred:<15s} (conf={conf:.2f})")


# ═══════════════════════════════════════════════════════════════════════════
# 5. MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═══ ENTRAÎNEMENT MINILM : PHRASE → OPÉRATION ═══\n")

    # Charger les données
    from structure_retrieval import StructuredRetrieval
    print("Chargement des données...")
    sr = StructuredRetrieval()
    sr.split_and_index()
    train = sr._train_problems
    print(f"  Train : {len(train)} problèmes\n")

    # Créer le dataset
    print("Création du dataset phrase→opération...")
    dataset = creer_dataset(train)

    # Entraîner
    modele = entrainer_classifieur(dataset)

    # Sauvegarder
    sauvegarder_modele(modele)

    # Test rapide
    test_rapide(modele)

    print("\n═══ TERMINÉ ═══")
