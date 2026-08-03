"""
Connecteur ABC pour le Moteur de Résonance Harmonique
======================================================
REMPLACE jepa_connector.py — migration JEPA → ABC (Atangana-Baleanu-Caputo).

Intègre le prédicteur par NOYAU ABC PUR (sopc_core.predictive_update_abc)
dans le pipeline d'inférence pour prédire l'évolution des signatures 9D.

Pourquoi le noyau ABC remplace JEPA :
  - JEPA (réseau neuronal) : 650+ paramètres aléatoirement initialisés,
    peut diverger, prédictions stochastico-dépendantes.
  - NOYAU ABC : ZERO paramètre. Prédiction = moyenne pondérée par le noyau
    de mémoire non-locale K(t) = B(α)·E_α(-α·t^α/(1-α)).
    DETERMINISTE par construction → pas d'hallucination possible.

Propriétés conservées par rapport à JEPA :
  - Prédit la prochaine signature 9D à partir de l'historique
  - Anticipation de la direction thématique de la conversation
  - Détection de changements de contexte (topic shift)
  - Boost de résonance basé sur les prédictions
  - MÊME INTERFACE publique que JEPAConnector (remplacement drop-in)

Usage:
    from engine.abc_predictor_connector import ABCPredictorConnector
    connector = ABCPredictorConnector()
    connector.load_or_init()
    connector.add_signature(signature_9d)
    prediction = connector.predict(horizon=3)

Référence : sopc_core.py (docstring) — "remplace JEPA".
"""

import os
import sys
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)

# Constantes harmoniques (identiques à abc_kernel.py / sopc_core.py)
PHI = 1.618033988749895
ALPHA = 1.0 / PHI  # 0.618033988749895

# Import robuste de sopc_core (supporte exécution directe et import package)
try:
    from .sopc_core import predictive_update_abc
except ImportError:
    try:
        from engine.sopc_core import predictive_update_abc
    except ImportError:
        # Fallback exécution directe : même dossier
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from sopc_core import predictive_update_abc


# ============================================================================
# RÉSULTAT DE PRÉDICTION (même forme que JEPAPrediction)
# ============================================================================

@dataclass
class ABCPrediction:
    """
    Résultat d'une prédiction par noyau ABC.

    Interface identique à JEPAPrediction pour assurer la compatibilité
    avec le code consommateur (harmonic_engine.chat()).
    """
    signature_predite: np.ndarray        # [9] signature prédite par le noyau ABC
    signature_actuelle: np.ndarray       # [9] signature actuelle
    resonance: float                     # Score de résonance [0, 1]
    topic_shift: float                   # Probabilité de changement de sujet [0, 1]
    horizon: int                         # Nombre de pas prédits
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


# ============================================================================
# CONNECTEUR ABC POUR LE MOTEUR HARMONIQUE
# ============================================================================

class ABCPredictorConnector:
    """
    Connecteur prédictif par noyau ABC pour le HarmonicResonanceEngine.

    REMPLACE DIRECTEMENT JEPAConnector (mêmes signatures de méthodes) :
        - __init__(max_history=32)            [hidden_dim ignoré, conservé pour compat]
        - load_or_init(path=None)
        - add_signature(signature)
        - predict(horizon=3) -> ABCPrediction|None
        - get_generation_boost(category) -> float
        - get_attention_bias() -> np.ndarray|None
        - reset()
        - get_stats() -> dict

    Différences clés avec JEPAConnector :
        1. Aucun poids neuronal — zéro paramètre appris.
        2. load_or_init() ne charge rien (noyau ABC fixe) ; conservé pour compat.
        3. Prédiction 100% déterministe (même entrée → même sortie).
        4. Pas de fichier .npz à gérer.
    """

    def __init__(self, max_history: int = 32, hidden_dim: int = 32):
        """
        Args:
            max_history: taille max de l'historique des signatures (rolling).
            hidden_dim: IGNORÉ (conservé pour compatibilité d'interface avec JEPA).
        """
        self.max_history = max_history
        self.hidden_dim = hidden_dim  # conservé pour compat, inutilisé

        # Historique des signatures [n, 9]
        self.signature_history: List[np.ndarray] = []

        # Dernière prédiction
        self.last_prediction: Optional[ABCPrediction] = None
        self._initialized = False

        # Stats (mêmes clés que JEPAConnector pour compat)
        self.stats = {
            'total_predictions': 0,
            'avg_resonance': 0.0,
            'topic_shifts_detected': 0,
            'history_size': 0,
        }

    def load_or_init(self, path: Optional[str] = None):
        """
        Initialise le connecteur ABC.

        Contrairement à JEPA, il n'y a RIEN à charger : le noyau ABC est
        fixe et calculé à la volée par sopc_core.predictive_update_abc().
        La signature est conservée pour la compatibilité d'interface.

        Args:
            path: Ignoré (noyau ABC sans paramètres). Conservé pour compat.
        """
        # Le noyau ABC n'a pas de paramètres à charger.
        if path:
            logger.info("ABCPredictor: noyau ABC sans paramètre (path ignoré)")
        else:
            logger.info("ABCPredictor: initialisé (noyau ABC pur, 0 paramètre)")

        self._initialized = True

    def add_signature(self, signature: np.ndarray):
        """
        Ajoute une signature 9D à l'historique.

        Args:
            signature: [9] signature 9D observée.
        """
        self.signature_history.append(np.asarray(signature, dtype=np.float32).copy())
        if len(self.signature_history) > self.max_history:
            self.signature_history.pop(0)
        self.stats['history_size'] = len(self.signature_history)

    def predict(self, horizon: int = 3) -> Optional[ABCPrediction]:
        """
        Prédit l'évolution des signatures via le noyau ABC.

        Args:
            horizon: Nombre de pas futurs à prédire.

        Returns:
            ABCPrediction ou None si l'historique est insuffisant (< 3 signatures).
        """
        if len(self.signature_history) < 3:
            return None

        current_sig = self.signature_history[-1].astype(np.float64)

        # Prédiction pas-à-pas : la signature prédite sert de contexte pour
        # la suivante (prédiction autorégressive par noyau ABC).
        futures_list = []
        context = list(self.signature_history)

        for _ in range(horizon):
            pred_sig = predictive_update_abc(context, fenetre_contexte=self.max_history)
            futures_list.append(pred_sig)
            context = context + [pred_sig]

        futures = np.array(futures_list, dtype=np.float32)  # [horizon, 9]
        pred_sig = futures[0]  # signature prédite à t+1

        # Score de résonance : similarité cosinus entre prédiction et réalité.
        resonance = self._resonance_score(pred_sig, current_sig)

        # Détection de topic shift : si la prédiction s'éloigne de la réalité,
        # le contexte a changé.
        topic_shift = 1.0 - resonance

        # Stats
        self.stats['total_predictions'] += 1
        n = self.stats['total_predictions']
        self.stats['avg_resonance'] = (
            (self.stats['avg_resonance'] * (n - 1) + resonance) / n
        )
        if topic_shift > 0.5:
            self.stats['topic_shifts_detected'] += 1

        pred = ABCPrediction(
            signature_predite=pred_sig.astype(np.float32),
            signature_actuelle=current_sig.astype(np.float32),
            resonance=resonance,
            topic_shift=topic_shift,
            horizon=horizon,
            futures=futures,
        )

        self.last_prediction = pred
        return pred

    @staticmethod
    def _resonance_score(sig_pred: np.ndarray, sig_actual: np.ndarray) -> float:
        """
        Similarité cosinus entre prédiction et réalité, normalisée par φ.

        Identique à JEPAPredictorLeger.resonance_score pour conserver
        la même échelle de résonance que l'ancien JEPA.
        """
        pred_norm = sig_pred * PHI
        actual_norm = sig_actual * PHI
        pred_norm = pred_norm / (np.linalg.norm(pred_norm) + 1e-8)
        actual_norm = actual_norm / (np.linalg.norm(actual_norm) + 1e-8)

        resonance = float(np.dot(pred_norm, actual_norm))
        return max(0.0, min(1.0, resonance))  # Clamp dans [0, 1]

    def get_generation_boost(self, category: str) -> float:
        """
        Calcule un boost de génération basé sur la prédiction ABC.

        Logique identique à JEPAConnector : résonance forte → direction
        claire → boost. Aucune dépendance à `category` (conservée pour compat).

        Returns:
            boost: Facteur multiplicatif [0.8, 1.5].
        """
        if self.last_prediction is None:
            return 1.0

        r = self.last_prediction.resonance
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
            bias: [9] ou None si pas de prédiction.
        """
        if self.last_prediction is None or self.last_prediction.futures is None:
            return None

        future_mean = self.last_prediction.futures.mean(axis=0)
        bias = future_mean * self.last_prediction.resonance
        return bias

    def reset(self):
        """Réinitialise l'historique."""
        self.signature_history = []
        self.last_prediction = None
        self.stats['history_size'] = 0

    def get_stats(self) -> Dict:
        """Retourne les statistiques du connecteur (mêmes clés que JEPA)."""
        return {
            **self.stats,
            'initialized': self._initialized,
            'has_prediction': self.last_prediction is not None,
            'last_resonance': round(self.last_prediction.resonance, 4) if self.last_prediction else None,
            'last_topic_shift': round(self.last_prediction.topic_shift, 4) if self.last_prediction else None,
            'predictor': 'abc_kernel',  # info additionnelle
        }


# ============================================================================
# DÉMO & TESTS
# ============================================================================

def demo_abc_predictor():
    """Démonstration du connecteur ABC."""
    print("=" * 70)
    print("DÉMO ABCPredictorConnector (remplace JEPA)")
    print("=" * 70)

    connector = ABCPredictorConnector(max_history=32)
    connector.load_or_init()

    # Simuler une conversation avec dérive thématique progressive
    np.random.seed(42)
    base = np.random.rand(9).astype(np.float32) * 0.3 + 0.3

    print("\n--- Phase 1 : conversation cohérente ---")
    for i in range(5):
        # Signatures proches (faible bruit) → haute résonance
        sig = base + np.random.randn(9).astype(np.float32) * 0.02
        sig = np.clip(sig, 0, 1)
        connector.add_signature(sig)
        pred = connector.predict(horizon=3)
        if pred:
            print(f"  t={i}: resonance={pred.resonance:.3f}  "
                  f"topic_shift={pred.topic_shift:.3f}  "
                  f"boost={connector.get_generation_boost('general'):.2f}")

    print("\n--- Phase 2 : changement de sujet brutal ---")
    nouvelle_base = np.random.rand(9).astype(np.float32) * 0.4 + 0.5
    for i in range(3):
        sig = nouvelle_base + np.random.randn(9).astype(np.float32) * 0.02
        sig = np.clip(sig, 0, 1)
        connector.add_signature(sig)
        pred = connector.predict(horizon=3)
        if pred:
            print(f"  t={i}: resonance={pred.resonance:.3f}  "
                  f"topic_shift={pred.topic_shift:.3f}  "
                  f"boost={connector.get_generation_boost('general'):.2f}")

    print("\n--- Stats finales ---")
    for k, v in connector.get_stats().items():
        print(f"  {k}: {v}")


if __name__ == '__main__':
    demo_abc_predictor()
