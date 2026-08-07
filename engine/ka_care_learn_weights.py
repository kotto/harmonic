"""
KA Care — Optimisation des Poids de Features par Pathologie
=============================================================
Apprend les poids optimaux des 33 features médicales pour chaque
pathologie, en maximisant l'AUC via descente de gradient stochastique.

Méthode : Régression logistique par pathologie (one-vs-rest)
  - Entrée : vecteur de features du patient (33 dimensions)
  - Sortie : probabilité de la pathologie
  - Apprentissage : 500 cas, 25 pathologies
  - Objectif : top-1 accuracy > 70%, top-3 > 90%
"""

import sys, os, json, math, random
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ka_care import encode, resonance, MEDICAL_FEATURES, SYMPTOM_FEATURES
from ka_care_validation import generate_phase1_dataset

F = MEDICAL_FEATURES  # 33 features


def symptoms_to_feature_vector(symptoms: str) -> np.ndarray:
    """Convertit des symptômes en vecteur de features normalisé."""
    words = symptoms.lower().replace(",", " ").replace(";", " ").split()
    vec = np.zeros(len(F))
    
    for w in words:
        w = w.strip()
        if not w:
            continue
        feats = SYMPTOM_FEATURES.get(w, {})
        for feat_name, weight in feats.items():
            if feat_name in F:
                idx = F.index(feat_name)
                vec[idx] += weight
    
    # Normaliser
    norm = np.sqrt(np.sum(vec ** 2)) + 1e-10
    return vec / norm


class PerDiseaseLogisticRegression:
    """Régression logistique one-vs-rest par pathologie."""
    
    def __init__(self, n_features: int, learning_rate: float = 0.01):
        self.n_features = n_features
        self.lr = learning_rate
        self.weights: Dict[str, np.ndarray] = {}  # disease → weight vector
        self.bias: Dict[str, float] = {}           # disease → bias
    
    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))
    
    def fit(
        self,
        disease: str,
        X: np.ndarray,       # [n_samples, n_features]
        y: np.ndarray,       # [n_samples] 0/1
        epochs: int = 100,
    ):
        """Apprend les poids pour une pathologie."""
        n = len(X)
        w = np.zeros(self.n_features)
        b = 0.0
        
        for epoch in range(epochs):
            # SGD
            idx = np.random.permutation(n)
            total_loss = 0.0
            
            for i in idx:
                xi = X[i]
                yi = y[i]
                
                # Forward
                z = np.dot(w, xi) + b
                y_pred = self.sigmoid(np.array([z]))[0]
                
                # Loss (binary cross-entropy)
                eps = 1e-10
                loss = -(yi * math.log(y_pred + eps) + (1 - yi) * math.log(1 - y_pred + eps))
                total_loss += loss
                
                # Backward
                error = y_pred - yi
                w -= self.lr * error * xi
                b -= self.lr * error
            
            # Annealing
            if epoch % 20 == 19:
                self.lr *= 0.8
        
        self.weights[disease] = w
        self.bias[disease] = b
    
    def predict_proba(self, disease: str, X: np.ndarray) -> np.ndarray:
        """Prédit la probabilité pour une pathologie."""
        w = self.weights.get(disease, np.zeros(self.n_features))
        b = self.bias.get(disease, 0.0)
        z = np.dot(X, w) + b
        return self.sigmoid(z)
    
    def predict_all(self, X: np.ndarray) -> List[Dict[str, float]]:
        """Prédit les scores pour toutes les pathologies."""
        results = []
        for i in range(len(X)):
            scores = {}
            for disease in self.weights:
                scores[disease] = float(self.predict_proba(disease, X[i:i+1])[0])
            results.append(scores)
        return results


class WeightedCalibrator:
    """Calibrateur avec poids appris."""
    
    def __init__(self):
        self.model = PerDiseaseLogisticRegression(n_features=len(F))
        self.diseases = set()
    
    def train(self, dataset: List[Tuple[str, str]], epochs: int = 100):
        """Apprend les poids sur le dataset."""
        # Préparer les données
        X = np.array([symptoms_to_feature_vector(s) for s, _ in dataset])
        self.diseases = set(d for _, d in dataset)
        
        print(f"Apprentissage sur {len(dataset)} cas, {len(self.diseases)} pathologies...")
        
        for disease in sorted(self.diseases):
            y = np.array([1.0 if d == disease else 0.0 for _, d in dataset])
            n_pos = int(np.sum(y))
            if n_pos < 3:
                continue  # pas assez de cas
            
            self.model.fit(disease, X, y, epochs=epochs)
        
        print(f"✅ {len(self.model.weights)} pathologies entraînées")
    
    def evaluate(self, test_set: List[Tuple[str, str]]) -> dict:
        """Évalue sur un jeu de test."""
        X_test = np.array([symptoms_to_feature_vector(s) for s, _ in test_set])
        predictions = self.model.predict_all(X_test)
        
        top1_correct = 0
        top3_correct = 0
        n = len(test_set)
        
        for i, (_, true_diag) in enumerate(test_set):
            scores = predictions[i]
            sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
            top3 = [s[0] for s in sorted_scores[:3]]
            
            if sorted_scores[0][0] == true_diag:
                top1_correct += 1
            if true_diag in top3:
                top3_correct += 1
        
        return {
            "top1_accuracy": top1_correct / n if n > 0 else 0,
            "top3_accuracy": top3_correct / n if n > 0 else 0,
            "n_test": n,
        }
    
    def get_top_features(self, disease: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Retourne les features les plus importantes pour une pathologie."""
        if disease not in self.model.weights:
            return []
        w = self.model.weights[disease]
        indices = np.argsort(-np.abs(w))[:top_k]
        return [(F[i], float(w[i])) for i in indices]


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("APPRENTISSAGE DES POIDS DE FEATURES")
    print("=" * 70)
    
    # Phase 1 : Générer le dataset
    print("\n📊 Génération du dataset (500 cas)...")
    dataset = generate_phase1_dataset(500)
    random.seed(42)
    random.shuffle(dataset)
    
    train_set = dataset[:400]
    test_set = dataset[400:500]
    print(f"Train: {len(train_set)}, Test: {len(test_set)}")
    
    # Phase 2 : Apprentissage
    print("\n🧠 Apprentissage des poids...")
    calibrator = WeightedCalibrator()
    calibrator.train(train_set, epochs=100)
    
    # Phase 3 : Évaluation
    print("\n📈 Évaluation...")
    results = calibrator.evaluate(test_set)
    print(f"Top-1 accuracy : {results['top1_accuracy']:.1%}")
    print(f"Top-3 accuracy : {results['top3_accuracy']:.1%}")
    
    # Phase 4 : Features importantes par pathologie
    print("\n🔑 Features clés par pathologie :")
    for disease in sorted(calibrator.model.weights.keys())[:10]:
        top = calibrator.get_top_features(disease, 5)
        features_str = ", ".join([f"{name}({w:+.2f})" for name, w in top])
        print(f"  {disease:30s}: {features_str}")
    
    # Comparaison avant/après
    print("\n📊 Comparaison avant/après :")
    print(f"  Avant (features égales) : top-1 ~43.5%, top-3 ~74.5%")
    print(f"  Après (poids appris)   : top-1 {results['top1_accuracy']:.1%}, top-3 {results['top3_accuracy']:.1%}")
    
    # Sauvegarder les poids
    weights_data = {}
    for disease in calibrator.model.weights:
        w = calibrator.model.weights[disease]
        b = calibrator.model.bias.get(disease, 0.0)
        weights_data[disease] = {
            "weights": {F[i]: float(w[i]) for i in range(len(F)) if abs(w[i]) > 0.01},
            "bias": float(b),
        }
    
    os.makedirs("data", exist_ok=True)
    with open("data/feature_weights.json", "w") as f:
        json.dump(weights_data, f, indent=2)
    print(f"\n✅ Poids sauvegardés : data/feature_weights.json")
