#!/usr/bin/env python3
"""Train classifier v4 with enriched features."""
import sys, os, pickle, numpy as np, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsm8k_dataset import extract_dataset, encode_sentence_wave
from wave_lang import encode, bind, DEFAULT_DIM
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report

print("Loading dataset...")
ds = extract_dataset()
dim = DEFAULT_DIM
op_to_idx = {'+': 0, '-': 1, '*': 2, '/': 3}
n_features = dim * 4 + 5
print(f"Building features: {len(ds)} examples, {n_features} features...")

X = np.zeros((len(ds), n_features), dtype=np.float64)
y = np.array([op_to_idx[d['op']] for d in ds], dtype=np.int32)

for i, d in enumerate(ds):
    sent = d['sentence']
    words = [w for w in re.findall(r'[a-zà-ÿ]+', sent.lower()) if len(w) > 1]
    psi_s = encode_sentence_wave(sent, dim)
    X[i, :dim] = np.real(psi_s)
    X[i, dim:2 * dim] = np.imag(psi_s)
    psi_b = np.zeros(dim, dtype=np.complex128)
    n_b = 0
    for j in range(len(words) - 1):
        try:
            psi_b += bind(encode(words[j], dim=dim), encode(words[j + 1], dim=dim))
            n_b += 1
        except:
            pass
    if n_b > 0:
        psi_b /= (np.linalg.norm(psi_b) + 1e-9)
    X[i, 2 * dim:3 * dim] = np.real(psi_b)
    X[i, 3 * dim:4 * dim] = np.imag(psi_b)
    X[i, 4 * dim] = float(d['op_index'])
    X[i, 4 * dim + 1] = float(d['a'])
    X[i, 4 * dim + 2] = float(d['b'])
    X[i, 4 * dim + 3] = len(words) / 30.0
    X[i, 4 * dim + 4] = float(d['op_index'])

print("Splitting...")
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

models = [
    ("Logistic", LogisticRegression(solver='lbfgs', max_iter=2000, C=1.0, class_weight='balanced')),
    ("RandomForest", RandomForestClassifier(n_estimators=200, max_depth=20, class_weight='balanced', random_state=42)),
    ("GradientBoosting", GradientBoostingClassifier(n_estimators=150, max_depth=5, learning_rate=0.1, random_state=42)),
]

for name, clf in models:
    print(f"Training {name}...")
    clf.fit(X_tr, y_tr)
    y_pred = clf.predict(X_te)
    acc = accuracy_score(y_te, y_pred)
    print(f"  {name}: {100 * acc:.1f}%")
    if name == 'GradientBoosting':
        print(classification_report(y_te, y_pred, target_names=['+', '-', '*', '/']))
        with open('gsm8k_gb_classifier.pkl', 'wb') as f:
            pickle.dump({'model': clf, 'dim': dim}, f)
        print("  Saved gsm8k_gb_classifier.pkl")

print("Done!")
