"""
Apprentissage Récursif par Résonance — Boucle d'Auto-Amélioration pour Harmonic AI v2
=====================================================================================
Permet à Harmonic AI de s'améliorer en écoutant ses propres interactions.
Le système observe la cohérence et la résonance de ses réponses, détecte
les patterns de faiblesse, et ajuste ses paramètres de génération.

Principe : comme une corde de guitare qui, en vibrant, ajuste sa propre tension
par résonance avec la caisse, Harmonic AI ajuste ses seuils et poids en fonction
de la qualité spectrale de ses sorties.

Architecture :
1. InteractionCollector — collecte les interactions (Q, R, scores)
2. WeaknessDetector — détecte les patterns de faiblesse récurrents
3. ResonanceOptimizer — ajuste les paramètres (seuils, poids) par résonance
4. MetaLearningLoop — boucle principale d'apprentissage récursif

Intégration :
    from engine.recursive_learner import MetaLearningLoop
    learner = MetaLearningLoop()
    learner.record_interaction(question, response, validation_result)
    if learner.should_optimize():
        adjustments = learner.optimize()
"""
import math
import time
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
import numpy as np

# =========================================================================
# CONSTANTES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI

# Seuils d'apprentissage
LEARNING_WINDOW = 50         # Nombre d'interactions avant optimisation
MIN_IMPROVEMENT = 0.02       # Amélioration minimale pour conserver un ajustement
MAX_ADJUSTMENT = 0.15        # Ajustement maximal par itération (éviter les oscillations)
DECAY_FACTOR = PHI_INV       # Facteur de décroissance des poids d'apprentissage

# Paramètres ajustables
ADJUSTABLE_PARAMS = [
    'coherence_threshold',    # Seuil de cohérence pour validation
    'resonance_threshold',    # Seuil de résonance
    'knowledge_threshold',    # Seuil de support factuel
    'creativity_boost',       # Boost de créativité dans la génération
    'factual_weight',         # Poids de l'extraction factuelle
    'emotional_sensitivity',  # Sensibilité émotionnelle
    'response_length_factor', # Facteur de longueur de réponse
]


# =========================================================================
# STRUCTURES DE DONNÉES
# =========================================================================

@dataclass
class InteractionRecord:
    """Enregistrement d'une interaction Q-R."""
    timestamp: float
    question: str
    response: str
    question_signature: np.ndarray       # [9]
    response_signature: np.ndarray       # [9]
    coherence_score: float
    resonance_score: float
    knowledge_score: float
    overall_score: float
    was_valid: bool
    num_retries: int
    approach_used: str


@dataclass
class WeaknessPattern:
    """Pattern de faiblesse détecté."""
    type: str                          # 'low_coherence', 'low_resonance', 'hallucination', etc.
    frequency: float                    # Fréquence d'apparition (0-1)
    avg_score: float                    # Score moyen associé
    trend: str                         # 'improving', 'stable', 'degrading'
    affected_dimensions: List[str]     # Dimensions affectées
    recommended_adjustment: Dict[str, float]  # Ajustements recommandés


@dataclass
class OptimizationResult:
    """Résultat d'une optimisation."""
    iteration: int
    params_before: Dict[str, float]
    params_after: Dict[str, float]
    improvements: Dict[str, float]
    overall_improvement: float
    weaknesses_addressed: List[str]


# =========================================================================
# COLLECTEUR D'INTERACTIONS
# =========================================================================

class InteractionCollector:
    """Collecte et stocke les interactions pour analyse."""
    
    def __init__(self, max_history: int = 500):
        self.interactions: deque = deque(maxlen=max_history)
        self.daily_stats: Dict[str, List[float]] = defaultdict(list)
        self.peak_scores: deque = deque(maxlen=100)  # Meilleurs scores
    
    def record(self, question: str, response: str,
               question_signature: np.ndarray,
               response_signature: np.ndarray,
               validation_result,
               num_retries: int = 0,
               approach_used: str = ""):
        """Enregistre une interaction."""
        record = InteractionRecord(
            timestamp=time.time(),
            question=question,
            response=response,
            question_signature=question_signature,
            response_signature=response_signature,
            coherence_score=validation_result.coherence_score,
            resonance_score=validation_result.resonance_score,
            knowledge_score=validation_result.knowledge_score,
            overall_score=validation_result.overall_score,
            was_valid=validation_result.is_valid,
            num_retries=num_retries,
            approach_used=approach_used,
        )
        self.interactions.append(record)
        
        # Mettre à jour les stats quotidiennes
        day = time.strftime('%Y-%m-%d')
        self.daily_stats[f'{day}_overall'].append(validation_result.overall_score)
        self.daily_stats[f'{day}_coherence'].append(validation_result.coherence_score)
        
        # Garder trace des meilleurs scores
        if validation_result.is_valid:
            self.peak_scores.append(validation_result.overall_score)
    
    def get_recent(self, n: int = 100) -> List[InteractionRecord]:
        """Récupère les N interactions les plus récentes."""
        return list(self.interactions)[-n:]
    
    def get_average_scores(self, window: int = 50) -> Dict[str, float]:
        """Calcule les scores moyens sur la fenêtre récente."""
        recent = self.get_recent(window)
        if not recent:
            return {}
        
        return {
            'overall': np.mean([r.overall_score for r in recent]),
            'coherence': np.mean([r.coherence_score for r in recent]),
            'resonance': np.mean([r.resonance_score for r in recent]),
            'knowledge': np.mean([r.knowledge_score for r in recent]),
            'validity_rate': np.mean([1.0 if r.was_valid else 0.0 for r in recent]),
        }
    
    def get_score_trend(self, window: int = 100) -> str:
        """Détermine la tendance des scores."""
        recent = self.get_recent(window)
        if len(recent) < 20:
            return 'insufficient_data'
        
        # Diviser en deux moitiés
        mid = len(recent) // 2
        first_half = np.mean([r.overall_score for r in recent[:mid]])
        second_half = np.mean([r.overall_score for r in recent[mid:]])
        
        diff = second_half - first_half
        if diff > 0.03:
            return 'improving'
        elif diff < -0.03:
            return 'degrading'
        else:
            return 'stable'


# =========================================================================
# DÉTECTEUR DE FAIBLESSES
# =========================================================================

class WeaknessDetector:
    """Détecte les patterns de faiblesse dans les interactions."""
    
    def __init__(self):
        self.detected_patterns: List[WeaknessPattern] = []
    
    def analyze(self, interactions: List[InteractionRecord]) -> List[WeaknessPattern]:
        """
        Analyse les interactions pour détecter les faiblesses récurrentes.
        
        Returns:
            Liste de WeaknessPattern détectés
        """
        patterns = []
        
        if len(interactions) < 10:
            return patterns
        
        # 1. Détecter faible cohérence
        low_coherence = [r for r in interactions if r.coherence_score < PHI_INV * 0.8]
        if len(low_coherence) > len(interactions) * 0.2:
            patterns.append(WeaknessPattern(
                type='low_coherence',
                frequency=len(low_coherence) / len(interactions),
                avg_score=np.mean([r.coherence_score for r in low_coherence]),
                trend='stable',
                affected_dimensions=['coherence'],
                recommended_adjustment={'coherence_threshold': -0.05},
            ))
        
        # 2. Détecter faible résonance
        low_resonance = [r for r in interactions if r.resonance_score < 0.45]
        if len(low_resonance) > len(interactions) * 0.25:
            pattern = WeaknessPattern(
                type='low_resonance',
                frequency=len(low_resonance) / len(interactions),
                avg_score=np.mean([r.resonance_score for r in low_resonance]),
                trend='stable',
                affected_dimensions=['resonance', 'context'],
                recommended_adjustment={'resonance_threshold': -0.03},
            )
            
            # Vérifier si lié à des approches spécifiques
            approaches = [r.approach_used for r in low_resonance]
            if approaches:
                most_common = max(set(approaches), key=approaches.count)
                pattern.affected_dimensions.append(f'approach_{most_common}')
            
            patterns.append(pattern)
        
        # 3. Détecter hallucinations récurrentes
        hallucinations = [r for r in interactions
                         if not r.was_valid and r.num_retries >= 2]
        if len(hallucinations) > len(interactions) * 0.1:
            patterns.append(WeaknessPattern(
                type='recurrent_hallucination',
                frequency=len(hallucinations) / len(interactions),
                avg_score=np.mean([r.overall_score for r in hallucinations]),
                trend='stable',
                affected_dimensions=['knowledge', 'coherence'],
                recommended_adjustment={
                    'knowledge_threshold': +0.05,
                    'coherence_threshold': +0.03,
                },
            ))
        
        # 4. Détecter dégradation temporelle
        if len(interactions) >= 30:
            first_10 = interactions[:10]
            last_10 = interactions[-10:]
            first_avg = np.mean([r.overall_score for r in first_10])
            last_avg = np.mean([r.overall_score for r in last_10])
            
            if last_avg < first_avg - 0.05:
                patterns.append(WeaknessPattern(
                    type='score_degradation',
                    frequency=1.0,
                    avg_score=last_avg,
                    trend='degrading',
                    affected_dimensions=['all'],
                    recommended_adjustment={
                        'coherence_threshold': +0.02,
                        'resonance_threshold': +0.02,
                        'creativity_boost': +0.05,  # Plus de variété
                    },
                ))
        
        # 5. Détecter sur-optimisation (scores trop uniformes = manque de diversité)
        scores = [r.overall_score for r in interactions[-30:]]
        if len(scores) >= 20:
            score_std = np.std(scores)
            if score_std < 0.05:  # Trop peu de variation
                patterns.append(WeaknessPattern(
                    type='low_diversity',
                    frequency=1.0,
                    avg_score=np.mean(scores),
                    trend='stable',
                    affected_dimensions=['creativity', 'diversity'],
                    recommended_adjustment={
                        'creativity_boost': +0.1,
                        'response_length_factor': +0.1,
                    },
                ))
        
        self.detected_patterns.extend(patterns)
        if len(self.detected_patterns) > 20:
            self.detected_patterns = self.detected_patterns[-20:]
        
        return patterns
    
    def get_persistent_weaknesses(self, min_occurrences: int = 3) -> List[str]:
        """
        Identifie les faiblesses qui persistent sur plusieurs cycles d'analyse.
        """
        if len(self.detected_patterns) < min_occurrences:
            return []
        
        type_counts = defaultdict(int)
        for p in self.detected_patterns:
            type_counts[p.type] += 1
        
        return [t for t, c in type_counts.items() if c >= min_occurrences]


# =========================================================================
# OPTIMISEUR PAR RÉSONANCE
# =========================================================================

class ResonanceOptimizer:
    """
    Optimiseur qui ajuste les paramètres par résonance.
    
    Principe : comme un accordeur de piano qui ajuste la tension des cordes
    jusqu'à ce qu'elles résonnent avec le diapason, cet optimiseur ajuste
    les seuils et poids jusqu'à ce que les scores convergent vers φ⁻¹.
    """
    
    def __init__(self):
        self.params = {
            'coherence_threshold': PHI_INV,        # 0.618
            'resonance_threshold': 0.5,
            'knowledge_threshold': PHI_INV ** 2,   # 0.382
            'creativity_boost': 0.3,
            'factual_weight': 0.5,
            'emotional_sensitivity': 0.5,
            'response_length_factor': 1.0,
        }
        self.optimization_history: List[OptimizationResult] = []
        self.iteration = 0
    
    def optimize(self, weaknesses: List[WeaknessPattern],
                 avg_scores: Dict[str, float]) -> OptimizationResult:
        """
        Calcule les ajustements optimaux basés sur les faiblesses détectées.
        
        L'ajustement est limité par MAX_ADJUSTMENT pour éviter les oscillations
        (principe de stabilité φ : petits pas irréversibles).
        """
        self.iteration += 1
        params_before = self.params.copy()
        
        adjustments = {}
        
        for weakness in weaknesses:
            for param, delta in weakness.recommended_adjustment.items():
                if param in self.params:
                    if param not in adjustments:
                        adjustments[param] = []
                    adjustments[param].append(delta)
        
        # Combiner les ajustements (moyenne pondérée par la fréquence)
        for param, deltas in adjustments.items():
            # Limiter l'ajustement
            avg_delta = np.clip(np.mean(deltas), -MAX_ADJUSTMENT, MAX_ADJUSTMENT)
            
            # Appliquer
            old_val = self.params[param]
            new_val = old_val + avg_delta
            
            # Borner entre 0.1 et 0.9
            new_val = np.clip(new_val, 0.1, 0.9)
            
            # Appliquer la décroissance φ pour éviter les oscillations
            # (chaque ajustement est amorti par φ⁻¹)
            if self.iteration > 1:
                new_val = old_val + (new_val - old_val) * DECAY_FACTOR
            
            self.params[param] = new_val
        
        # Calculer l'amélioration estimée
        improvements = {}
        for param in adjustments:
            old = params_before.get(param, 0.5)
            new = self.params.get(param, 0.5)
            improvements[param] = new - old
        
        result = OptimizationResult(
            iteration=self.iteration,
            params_before=params_before,
            params_after=self.params.copy(),
            improvements=improvements,
            overall_improvement=sum(abs(v) for v in improvements.values()) / max(len(improvements), 1),
            weaknesses_addressed=[w.type for w in weaknesses],
        )
        
        self.optimization_history.append(result)
        if len(self.optimization_history) > 50:
            self.optimization_history = self.optimization_history[-50:]
        
        return result
    
    def get_params(self) -> Dict[str, float]:
        """Retourne les paramètres actuels."""
        return self.params.copy()
    
    def get_convergence_status(self) -> str:
        """
        Vérifie si les paramètres convergent (les ajustements deviennent petits).
        """
        if len(self.optimization_history) < 3:
            return 'exploring'
        
        recent = self.optimization_history[-3:]
        improvements = [r.overall_improvement for r in recent]
        
        if all(i < 0.01 for i in improvements):
            return 'converged'
        elif improvements[-1] < improvements[-2]:
            return 'converging'
        else:
            return 'oscillating'


# =========================================================================
# BOUCLE DE MÉTA-APPRENTISSAGE
# =========================================================================

class MetaLearningLoop:
    """
    Boucle principale d'apprentissage récursif pour Harmonic AI v2.
    
    Orchestre la collecte d'interactions, la détection de faiblesses,
    et l'optimisation des paramètres.
    
    Usage:
        learner = MetaLearningLoop()
        
        # Après chaque interaction :
        learner.record_interaction(question, response, validation_result)
        
        # Périodiquement (toutes les 50 interactions) :
        if learner.should_optimize():
            adjustments = learner.optimize()
            # Appliquer adjustments aux paramètres de génération
            generation_params.update(adjustments)
    """
    
    def __init__(self, learning_window: int = 50):
        self.collector = InteractionCollector()
        self.detector = WeaknessDetector()
        self.optimizer = ResonanceOptimizer()
        self.learning_window = learning_window
        self.interaction_count = 0
        self.last_optimization = 0
        self.optimization_schedule = []  # Historique des moments d'optimisation
    
    def record_interaction(self, question: str, response: str,
                          question_signature: np.ndarray,
                          validation_result,
                          num_retries: int = 0,
                          approach_used: str = ""):
        """Enregistre une interaction et met à jour le compteur."""
        # Calculer la signature de réponse (légère)
        try:
            from engine.spectral_validator import compute_lightweight_signature
            response_sig = compute_lightweight_signature(response)
        except ImportError:
            response_sig = question_signature  # Fallback
        
        self.collector.record(
            question, response,
            question_signature, response_sig,
            validation_result,
            num_retries, approach_used
        )
        self.interaction_count += 1
    
    def should_optimize(self) -> bool:
        """Détermine si une optimisation doit être déclenchée."""
        interactions_since_last = self.interaction_count - self.last_optimization
        
        # Optimiser toutes les N interactions
        if interactions_since_last >= self.learning_window:
            return True
        
        # Optimiser plus tôt si dégradation détectée
        if interactions_since_last >= 20:
            trend = self.collector.get_score_trend(50)
            if trend == 'degrading':
                return True
        
        return False
    
    def optimize(self) -> Tuple[Dict[str, float], OptimizationResult]:
        """
        Exécute un cycle d'optimisation complet.
        
        Returns:
            (paramètres optimisés, résultat d'optimisation)
        """
        # 1. Récupérer les interactions récentes
        interactions = self.collector.get_recent(self.learning_window)
        
        # 2. Calculer les scores moyens
        avg_scores = self.collector.get_average_scores(self.learning_window)
        
        # 3. Détecter les faiblesses
        weaknesses = self.detector.analyze(interactions)
        
        # 4. Optimiser les paramètres
        if weaknesses:
            result = self.optimizer.optimize(weaknesses, avg_scores)
        else:
            # Pas de faiblesse détectée : légère exploration
            dummy_weakness = WeaknessPattern(
                type='exploration',
                frequency=0.1,
                avg_score=avg_scores.get('overall', 0.618),
                trend='stable',
                affected_dimensions=['diversity'],
                recommended_adjustment={'creativity_boost': 0.02},
            )
            result = self.optimizer.optimize([dummy_weakness], avg_scores)
        
        # 5. Mettre à jour l'état
        self.last_optimization = self.interaction_count
        self.optimization_schedule.append({
            'iteration': self.interaction_count,
            'timestamp': time.time(),
            'improvement': result.overall_improvement,
            'weaknesses': result.weaknesses_addressed,
        })
        
        return self.optimizer.get_params(), result
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Génère un rapport de santé du système d'apprentissage.
        """
        avg_scores = self.collector.get_average_scores(50)
        trend = self.collector.get_score_trend(100)
        convergence = self.optimizer.get_convergence_status()
        persistent = self.detector.get_persistent_weaknesses()
        
        # Calculer le taux d'apprentissage effectif
        if len(self.optimization_schedule) >= 2:
            first = self.optimization_schedule[0]
            last = self.optimization_schedule[-1]
            learning_rate = (last.get('improvement', 0) - first.get('improvement', 0)) / len(self.optimization_schedule)
        else:
            learning_rate = 0.0
        
        return {
            'total_interactions': self.interaction_count,
            'optimization_cycles': len(self.optimization_schedule),
            'current_params': self.optimizer.get_params(),
            'avg_scores': avg_scores,
            'score_trend': trend,
            'convergence_status': convergence,
            'persistent_weaknesses': persistent,
            'learning_rate': learning_rate,
            'phi_alignment': abs(avg_scores.get('overall', 0.5) - PHI_INV),
        }
    
    def save_state(self, filepath: str):
        """Sauvegarde l'état de l'apprenant."""
        state = {
            'optimizer_params': self.optimizer.params,
            'optimization_schedule': self.optimization_schedule,
            'interaction_count': self.interaction_count,
            'last_optimization': self.last_optimization,
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filepath: str):
        """Charge l'état de l'apprenant."""
        with open(filepath, 'r') as f:
            state = json.load(f)
        self.optimizer.params = state['optimizer_params']
        self.optimization_schedule = state['optimization_schedule']
        self.interaction_count = state['interaction_count']
        self.last_optimization = state['last_optimization']


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST RECURSIVE LEARNER — Boucle d'Auto-Amélioration")
    print("=" * 60)
    
    # Simuler une session d'apprentissage
    learner = MetaLearningLoop(learning_window=30)
    
    # Simuler des interactions
    np.random.seed(42)
    
    for i in range(100):
        # Simuler une question et une réponse
        question = f"Question simulée {i}"
        response = f"Réponse simulée {i} avec du contenu suffisant pour être cohérent."
        q_sig = np.random.rand(9)
        
        # Simuler un résultat de validation (tendance à s'améliorer)
        base_score = 0.5 + 0.2 * (i / 100)  # Amélioration progressive
        coherence = base_score + np.random.normal(0, 0.1)
        resonance = base_score + np.random.normal(0, 0.1)
        knowledge = base_score + np.random.normal(0, 0.15)
        overall = (coherence * 0.35 + resonance * 0.3 + knowledge * 0.35)
        
        # Simuler un résultat de validation
        from engine.spectral_validator import ValidationResult
        result = ValidationResult(
            is_valid=overall > PHI_INV,
            overall_score=overall,
            coherence_score=coherence,
            resonance_score=resonance,
            knowledge_score=knowledge,
            hallucination_markers=0.8,
            recommendation="TEST",
        )
        
        learner.record_interaction(question, response, q_sig, result,
                                   num_retries=0 if result.is_valid else 1)
        
        # Optimiser périodiquement
        if learner.should_optimize():
            params, opt_result = learner.optimize()
            print(f"\n[Optimisation {len(learner.optimization_schedule)}] "
                  f"Interaction {i+1}")
            print(f"  Faiblesses: {opt_result.weaknesses_addressed}")
            print(f"  Amélioration: {opt_result.overall_improvement:.4f}")
            print(f"  Convergence: {learner.optimizer.get_convergence_status()}")
    
    # Rapport final
    print("\n" + "=" * 60)
    print("RAPPORT DE SANTÉ FINAL")
    print("=" * 60)
    report = learner.get_health_report()
    for key, value in report.items():
        if key == 'current_params':
            print(f"\n  Paramètres optimisés:")
            for p, v in value.items():
                print(f"    {p}: {v:.4f}")
        elif key == 'avg_scores':
            print(f"\n  Scores moyens:")
            for s, v in value.items():
                print(f"    {s}: {v:.4f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✓ Test Recursive Learner réussi!")
    print("=" * 60)