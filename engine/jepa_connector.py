"""
[DEPRECATED] Connecteur JEPA — REMPLACE par engine.abc_predictor_connector
============================================================================
Ce module est OBSOLETE depuis la migration JEPA → ABC (juin 2026).

Le predicteur JEPA (reseau neuronal ~650 parametres) a ete remplace par
le predicteur par noyau ABC pur (engine.sopc_core.predictive_update_abc,
engine.abc_predictor_connector.ABCPredictorConnector).

Raisons du remplacement :
  - Noyau ABC : 0 parametre, deterministe, ne peut pas diverger.
  - JEPA       : ~650 parametres, stochastique, divergence possible.
  - Le noyau ABC EST le predicteur naturel des signatures harmoniques
    (moyenne ponderee par K(t) = B(alpha)·E_alpha(-alpha·t^alpha/(1-alpha))).

Migration :
    AVANT : from engine.jepa_connector import JEPAConnector
            conn = JEPAConnector(max_history=32)
            conn.load_or_init()
            conn.add_signature(sig)
            pred = conn.predict(horizon=3)

    APRES : from engine.abc_predictor_connector import ABCPredictorConnector
            conn = ABCPredictorConnector(max_history=32)
            conn.load_or_init()
            conn.add_signature(sig)
            pred = conn.predict(horizon=3)

Ce fichier est conserve pour reference uniquement.
"""

import os
import sys
import math
import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

import warnings
warnings.warn(
    "jepa_connector.py est DEPRECATED. Utilisez abc_predictor_connector.py a la place.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger(__name__)

# Chemins
HARMONIC_TRAINING_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'harmonic_training'
)
if HARMONIC_TRAINING_DIR not in sys.path:
    sys.path.insert(0, HARMONIC_TRAINING_DIR)

# Constantes harmoniques
PHI = 1.618033988749895
ALPHA = 1.0 / PHI  # 0.618033988749895


# ============================================================================
# COEUR JEPA (copie locale autonome pour éviter les imports fragiles)
# ============================================================================

class ABCKernelJEPA:
    """Noyau ABC fixe pour mémoire temporelle."""
    
    def __init__(self, kernel_size: int = 5):
        self.kernel_size = kernel_size
        self.weights = self._compute()
    
    def _compute(self) -> np.ndarray:
        t = np.arange(self.kernel_size, dtype=np.float32)
        weights = np.exp(-ALPHA * t) * np.cos(PHI * t)
        weights = weights / (weights.sum() + 1e-8)
        return weights
    
    def apply(self, values: np.ndarray) -> np.ndarray:
        """Applique la pondération ABC à une séquence [seq, dim]."""
        k = min(self.kernel_size, values.shape[0])
        w = self.weights[-k:]
        return (values[-k:] * w.reshape(-1, 1)).sum(axis=0)


class JEPAPredictorLeger:
    """
    Version ultra-légère du JEPA Predictor.
    ~650 paramètres, pur NumPy, sans dépendance PyTorch pour l'inférence.
    """
    
    def __init__(self, hidden_dim: int = 32):
        self.hidden_dim = hidden_dim
        self.abc = ABCKernelJEPA(kernel_size=5)
        
        # Poids appris (initialisés à PHI)
        self.W_in = np.random.randn(9, hidden_dim).astype(np.float32) * (PHI / np.sqrt(9))
        self.b_in = np.zeros(hidden_dim, dtype=np.float32)
        
        self.W_hidden = np.random.randn(hidden_dim, hidden_dim).astype(np.float32) * (PHI / np.sqrt(hidden_dim))
        self.b_hidden = np.zeros(hidden_dim, dtype=np.float32)
        
        self.W_out = np.random.randn(hidden_dim, 9).astype(np.float32) * (PHI / np.sqrt(hidden_dim))
        self.b_out = np.zeros(9, dtype=np.float32)
    
    def forward(self, signatures: np.ndarray) -> np.ndarray:
        """
        Prédit la prochaine signature.
        
        Args:
            signatures: [seq_len, 9] historique des signatures
            
        Returns:
            pred: [9] signature prédite
        """
        # Agrégation temporelle via ABC
        latent = signatures @ self.W_in + self.b_in  # [seq, hidden]
        h = self.abc.apply(latent)  # [hidden]
        
        # Projection cachée
        h = h @ self.W_hidden + self.b_hidden
        h = np.tanh(h)  # Non-linéarité
        
        # Projection sortie
        pred = h @ self.W_out + self.b_out
        pred = 1.0 / (1.0 + np.exp(-pred))  # Sigmoid → [0, 1]
        
        return pred
    
    def predict_future(self, signatures: np.ndarray, horizon: int = 3) -> np.ndarray:
        """
        Prédit les H prochaines signatures de manière autorégressive.
        
        Args:
            signatures: [seq_len, 9] historique
            horizon: nombre de pas à prédire
            
        Returns:
            futures: [horizon, 9] signatures prédites
        """
        futures = []
        current = signatures.copy()
        
        for _ in range(horizon):
            next_sig = self.forward(current)
            futures.append(next_sig)
            current = np.vstack([current, next_sig.reshape(1, -1)])
            if current.shape[0] > 64:
                current = current[-64:, :]
        
        return np.array(futures)
    
    def resonance_score(self, sig_pred: np.ndarray, sig_actual: np.ndarray) -> float:
        """
        Calcule le score de résonance entre prédiction et réalité.
        
        Args:
            sig_pred: [9] signature prédite
            sig_actual: [9] signature réelle
            
        Returns:
            score: float dans [0, 1] (1 = résonance parfaite)
        """
        pred_norm = sig_pred * PHI
        actual_norm = sig_actual * PHI
        pred_norm = pred_norm / (np.linalg.norm(pred_norm) + 1e-8)
        actual_norm = actual_norm / (np.linalg.norm(actual_norm) + 1e-8)
        
        resonance = float(np.dot(pred_norm, actual_norm))
        return max(0.0, min(1.0, resonance))  # Clamp dans [0, 1]
    
    def get_params(self) -> Dict:
        """Retourne les paramètres sous forme de dictionnaire."""
        return {
            'W_in': self.W_in.tolist(),
            'b_in': self.b_in.tolist(),
            'W_hidden': self.W_hidden.tolist(),
            'b_hidden': self.b_hidden.tolist(),
            'W_out': self.W_out.tolist(),
            'b_out': self.b_out.tolist(),
        }
    
    def set_params(self, params: Dict):
        """Charge les paramètres depuis un dictionnaire."""
        self.W_in = np.array(params['W_in'], dtype=np.float32)
        self.b_in = np.array(params['b_in'], dtype=np.float32)
        self.W_hidden = np.array(params['W_hidden'], dtype=np.float32)
        self.b_hidden = np.array(params['b_hidden'], dtype=np.float32)
        self.W_out = np.array(params['W_out'], dtype=np.float32)
        self.b_out = np.array(params['b_out'], dtype=np.float32)

    def save(self, path: str):
        """Sauvegarde les paramètres."""
        np.savez(path, **self.get_params())
        logger.info(f"JEPA sauvegardé: {path}")
    
    def load(self, path: str):
        """Charge les paramètres."""
        data = np.load(path)
        self.set_params({k: data[k] for k in data.files})
        logger.info(f"JEPA chargé: {path}")


# ============================================================================
# CONNECTEUR JEPA POUR LE MOTEUR HARMONIQUE
# ============================================================================

@dataclass
class JEPAPrediction:
    """Résultat d'une prédiction JEPA."""
    signature_predite: np.ndarray       # [9] signature prédite
    signature_actuelle: np.ndarray      # [9] signature actuelle
    resonance: float                    # Score de résonance [0, 1]
    topic_shift: float                  # Probabilité de changement de sujet [0, 1]
    horizon: int                        # Nombre de pas prédits
    futures: Optional[np.ndarray] = None  # [horizon, 9] prédictions futures
    
    def to_dict(self) -> Dict:
        return {
            'resonance': round(self.resonance, 4),
            'topic_shift': round(self.topic_shift, 4),
            'horizon': self.horizon,
            'signature_predite': [round(v, 4) for v in self.signature_predite.tolist()],
            'signature_actuelle': [round(v, 4) for v in self.signature_actuelle.tolist()],
            'futures': [[round(v, 4) for v in f] for f in self.futures] if self.futures is not None else None,
        }


class JEPAConnector:
    """
    Connecteur JEPA pour le HarmonicResonanceEngine.
    
    Maintient un historique des signatures 9D et utilise le JEPA
    pour prédire l'évolution du contexte conversationnel.
    """
    
    def __init__(self, max_history: int = 32, hidden_dim: int = 32):
        self.max_history = max_history
        self.hidden_dim = hidden_dim
        
        # Historique des signatures [n, 9]
        self.signature_history: List[np.ndarray] = []
        
        # Dernière prédiction
        self.last_prediction: Optional[JEPAPrediction] = None
        
        # Prédicteur JEPA
        self.predictor = JEPAPredictorLeger(hidden_dim=hidden_dim)
        self._initialized = False
        
        # Stats
        self.stats = {
            'total_predictions': 0,
            'avg_resonance': 0.0,
            'topic_shifts_detected': 0,
            'history_size': 0,
        }
    
    def load_or_init(self, path: Optional[str] = None):
        """
        Charge un prédicteur JEPA pré-entraîné ou en initialise un nouveau.
        
        Args:
            path: Chemin vers un fichier .npz de paramètres pré-entraînés
        """
        if path and os.path.exists(path):
            try:
                self.predictor.load(path)
                logger.info(f"JEPA chargé depuis: {path}")
            except Exception as e:
                logger.warning(f"Échec chargement JEPA ({e}), initialisation neuve")
        else:
            logger.info("JEPA: nouvelle initialisation (paramètres PHI)")
        
        self._initialized = True
    
    def add_signature(self, signature: np.ndarray):
        """
        Ajoute une signature à l'historique.
        
        Args:
            signature: [9] signature 9D
        """
        self.signature_history.append(signature.copy())
        if len(self.signature_history) > self.max_history:
            self.signature_history.pop(0)
        self.stats['history_size'] = len(self.signature_history)
    
    def predict(self, horizon: int = 3) -> Optional[JEPAPrediction]:
        """
        Prédit l'évolution des signatures.
        
        Args:
            horizon: Nombre de pas à prédire
            
        Returns:
            JEPAPrediction ou None si historique insuffisant
        """
        if len(self.signature_history) < 3:
            return None
        
        # Convertir en numpy array [seq, 9]
        history = np.array(self.signature_history)
        current_sig = history[-1]
        
        # Prédiction
        pred_sig = self.predictor.forward(history)
        futures = self.predictor.predict_future(history, horizon=horizon)
        
        # Score de résonance
        resonance = self.predictor.resonance_score(pred_sig, current_sig)
        
        # Détection de changement de sujet
        # Si la prédiction s'éloigne beaucoup de la réalité → topic shift
        topic_shift = 1.0 - resonance
        
        # Stats
        self.stats['total_predictions'] += 1
        n = self.stats['total_predictions']
        self.stats['avg_resonance'] = (
            (self.stats['avg_resonance'] * (n - 1) + resonance) / n
        )
        if topic_shift > 0.5:
            self.stats['topic_shifts_detected'] += 1
        
        pred = JEPAPrediction(
            signature_predite=pred_sig,
            signature_actuelle=current_sig,
            resonance=resonance,
            topic_shift=topic_shift,
            horizon=horizon,
            futures=futures,
        )
        
        self.last_prediction = pred
        return pred
    
    def get_generation_boost(self, category: str) -> float:
        """
        Calcule un boost de génération basé sur la prédiction JEPA.
        
        Le boost est plus élevé quand :
        - La résonance est forte (conversation cohérente)
        - La prédiction indique une direction claire
        
        Args:
            category: Catégorie actuelle (math, code, créatif, etc.)
            
        Returns:
            boost: Facteur multiplicatif [0.8, 1.5]
        """
        if self.last_prediction is None:
            return 1.0
        
        r = self.last_prediction.resonance
        
        # Résonance forte → direction claire → boost
        if r > 0.8:
            return 1.3
        elif r > 0.6:
            return 1.1
        elif r > 0.4:
            return 1.0
        else:
            return 0.9  # Faible résonance → réduire la confiance
    
    def get_attention_bias(self) -> Optional[np.ndarray]:
        """
        Calcule un biais d'attention basé sur la prédiction future.
        
        Returns:
            bias: [9] ou None si pas de prédiction
        """
        if self.last_prediction is None or self.last_prediction.futures is None:
            return None
        
        # Moyenne des prédictions futures comme biais
        future_mean = self.last_prediction.futures.mean(axis=0)
        
        # Amplifier par la résonance
        bias = future_mean * self.last_prediction.resonance
        return bias
    
    def reset(self):
        """Réinitialise l'historique."""
        self.signature_history = []
        self.last_prediction = None
        self.stats['history_size'] = 0
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du connecteur."""
        return {
            **self.stats,
            'initialized': self._initialized,
            'has_prediction': self.last_prediction is not None,
            'last_resonance': round(self.last_prediction.resonance, 4) if self.last_prediction else None,
            'last_topic_shift': round(self.last_prediction.topic_shift, 4) if self.last_prediction else None,
        }


# ============================================================================
# DÉMO & TESTS
# ============================================================================

def demo_jepa_connector():
    """Démo du connecteur JEPA avec signatures simulées."""
    print("=" * 60)
    print("DÉMO : CONNECTEUR JEPA")
    print("=" * 60)
    
    # 1. Initialiser
    connector = JEPAConnector(max_history=16)
    connector.load_or_init()  # Nouvelle initialisation
    print(f"\n[1] JEPA initialisé ({connector.hidden_dim} hidden dim)")
    
    # 2. Simuler des signatures cohérentes (mathématiques)
    print("\n[2] Simulation de signatures mathématiques...")
    for i in range(10):
        # Signature simulée : phi élevé, alpha moyen, math élevé
        sig = np.array([
            0.7 + 0.1 * np.sin(i * 0.5),  # phi
            0.5 + 0.1 * np.cos(i * 0.3),  # alpha
            0.6 + 0.05 * np.sin(i * 0.7), # reasoning
            0.3 + 0.1 * np.cos(i * 0.4),  # creativity
            0.8 + 0.1 * np.sin(i * 0.2),  # math
            0.5 + 0.05 * np.cos(i * 0.6), # factual
            0.2 + 0.1 * np.sin(i * 0.8),  # code
            0.3 + 0.05 * np.cos(i * 0.5), # emotion
            0.4 + 0.1 * np.sin(i * 0.3),  # temporal
        ], dtype=np.float32)
        connector.add_signature(sig)
    
    # 3. Prédire
    print("\n[3] Prédiction JEPA...")
    pred = connector.predict(horizon=3)
    if pred:
        print(f"\n  Signature actuelle :  [{', '.join(f'{v:.3f}' for v in pred.signature_actuelle)}]")
        print(f"  Signature prédite :   [{', '.join(f'{v:.3f}' for v in pred.signature_predite)}]")
        print(f"  Résonance :           {pred.resonance:.4f}")
        print(f"  Topic shift :         {pred.topic_shift:.4f}")
        print(f"  Boost génération :    {connector.get_generation_boost('math'):.2f}")
        
        if pred.futures is not None:
            print(f"\n  Prédictions futures ({pred.horizon} pas) :")
            for i, f in enumerate(pred.futures):
                print(f"    t+{i+1}: [{', '.join(f'{v:.3f}' for v in f)}]")
    
    # 4. Simuler un changement de sujet brusque
    print("\n[4] Simulation d'un changement de sujet (code)...")
    for i in range(5):
        sig = np.array([
            0.3 + 0.1 * np.sin(i * 0.5),  # phi (faible)
            0.4 + 0.1 * np.cos(i * 0.3),  # alpha
            0.5 + 0.05 * np.sin(i * 0.7), # reasoning
            0.3 + 0.1 * np.cos(i * 0.4),  # creativity
            0.2 + 0.1 * np.sin(i * 0.2),  # math (faible)
            0.5 + 0.05 * np.cos(i * 0.6), # factual
            0.9 + 0.1 * np.sin(i * 0.8),  # code (élevé!)
            0.3 + 0.05 * np.cos(i * 0.5), # emotion
            0.4 + 0.1 * np.sin(i * 0.3),  # temporal
        ], dtype=np.float32)
        connector.add_signature(sig)
    
    # 5. Prédire après le shift
    print("\n[5] Prédiction après changement de sujet...")
    pred2 = connector.predict(horizon=2)
    if pred2:
        print(f"\n  Résonance :           {pred2.resonance:.4f}")
        print(f"  Topic shift :         {pred2.topic_shift:.4f}")
        print(f"  Boost génération :    {connector.get_generation_boost('code'):.2f}")
        print(f"  Stats connecteur :    {connector.get_stats()}")
    
    print("\n" + "=" * 60)
    print("DÉMO TERMINÉE")
    print("=" * 60)
    return connector


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    demo_jepa_connector()
