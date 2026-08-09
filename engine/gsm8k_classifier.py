#!/usr/bin/env python3
"""
gsm8k_classifier.py — Classifieur d'opération entraîné sur les ondes GSM8K
===========================================================================
Entraîne un classifieur (régression logistique) qui prédit l'opération
(add/sub/mult/div) à partir de l'encodage ondulatoire d'une phrase.

Le modèle remplace le `resolve_action()` basé sur des regex dans le
pipeline GSM8K du raisonneur ondulatoire.

USAGE :
  python gsm8k_classifier.py --train    # entraîner et sauvegarder le modèle
  python gsm8k_classifier.py --eval     # évaluer la précision
"""

import sys, os, json, pickle
import numpy as np
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsm8k_dataset import extract_dataset, encode_sentence_wave, build_feature_matrix, DEFAULT_DIM

# ═══════════════════════════════════════════════════════════════════════════════
# 1. CLASSIFIEUR ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveClassifier:
    """
    Classifieur linéaire sur les ondes encodées.

    Utilise scikit-learn LogisticRegression (multinomiale, one-vs-rest)
    avec les features = concat(Re(ψ), Im(ψ)) où ψ = superpose(encode(mots)).
    """

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self.model = None
        self.op_names = ['+', '-', '*', '/']

    def train(self, X: np.ndarray, y: np.ndarray):
        """Entraîne le classifieur sur les features X et les labels y."""
        from sklearn.linear_model import LogisticRegression
        self.model = LogisticRegression(
            solver='lbfgs',
            max_iter=2000,
            C=1.0,
            class_weight='balanced',
        )
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prédit les classes (0=+, 1=−, 2=×, 3=÷)."""
        if self.model is None:
            raise RuntimeError("Modèle non entraîné")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Retourne les probabilités par classe."""
        if self.model is None:
            raise RuntimeError("Modèle non entraîné")
        return self.model.predict_proba(X)

    def predict_op(self, sentence: str) -> str:
        """Prédit l'opération pour une phrase donnée (+, -, *, /)."""
        psi = encode_sentence_wave(sentence, dim=self.dim)
        x = np.zeros((1, self.dim * 2), dtype=np.float64)
        x[0, :self.dim] = np.real(psi)
        x[0, self.dim:] = np.imag(psi)
        idx = self.model.predict(x)[0]
        return self.op_names[idx]

    def predict_op_with_confidence(self, sentence: str) -> tuple:
        """Prédit l'opération avec le score de confiance."""
        psi = encode_sentence_wave(sentence, dim=self.dim)
        x = np.zeros((1, self.dim * 2), dtype=np.float64)
        x[0, :self.dim] = np.real(psi)
        x[0, self.dim:] = np.imag(psi)
        probs = self.model.predict_proba(x)[0]
        idx = int(np.argmax(probs))
        return self.op_names[idx], float(probs[idx])

    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump({'dim': self.dim, 'model': self.model}, f)

    @classmethod
    def load(cls, path: str) -> 'WaveClassifier':
        with open(path, 'rb') as f:
            data = pickle.load(f)
        wc = cls(dim=data['dim'])
        wc.model = data['model']
        return wc


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ENTRAÎNEMENT + ÉVALUATION
# ═══════════════════════════════════════════════════════════════════════════════

def train_and_eval():
    print("═══ CLASSIFIEUR ONDULATOIRE GSM8K ═══")

    # Charger le dataset
    print("  Chargement dataset...")
    ds = extract_dataset()
    X, y, meta = build_feature_matrix(ds)
    print(f"  {len(ds)} exemples, {X.shape[1]} features, {len(set(y))} classes")

    # Split train/test (80/20)
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    # Entraîner
    print(f"  Entraînement sur {len(X_train)} exemples...")
    clf = WaveClassifier()
    clf.train(X_train, y_train)

    # Évaluer
    from sklearn.metrics import classification_report, accuracy_score
    y_pred = clf.model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n  Précision : {100 * acc:.1f}%")
    print(f"\n  Rapport :")
    print(classification_report(y_test, y_pred, target_names=clf.op_names))

    # Sauvegarder
    path = os.path.join(os.path.dirname(__file__), 'gsm8k_wave_classifier.pkl')
    clf.save(path)
    print(f"\n  Modèle sauvegardé : {path}")

    # Test manuel sur quelques phrases
    print("\n  Tests manuels :")
    tests = [
        "She sells the remainder at the farmers market daily for $2 per egg",
        "He buys 3 more apples",
        "She ate 4 cookies",
        "Each box has 5 pencils",
        "They are split into 4 equal groups",
        "Mary has 3 times as many apples as John",
        "Janet earns 20 dollars per hour",
    ]
    for t in tests:
        op, conf = clf.predict_op_with_confidence(t)
        print(f"    [{op}] {t[:60]:<60} conf={conf:.2f}")

    return clf


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', action='store_true', help='Entraîner et sauvegarder')
    parser.add_argument('--eval', action='store_true', help='Évaluer seulement')
    args = parser.parse_args()

    if args.train or args.eval:
        train_and_eval()
    else:
        train_and_eval()
