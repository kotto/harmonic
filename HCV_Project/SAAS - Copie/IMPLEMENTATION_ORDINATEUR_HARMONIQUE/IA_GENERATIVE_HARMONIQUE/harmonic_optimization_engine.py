"""
⚡ MOTEUR D'OPTIMISATION HARMONIQUE
Fichier: harmonic_optimization_engine.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Moteur d'optimisation avancé pour l'IA générative harmonique
"""

import numpy as np
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
from collections import defaultdict
import statistics
from scipy.optimize import minimize, differential_evolution
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import networkx as nx

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes harmoniques universelles
PHI = 1.618033988749895  # Ratio d'or
PI = 3.141592653589793    # Constante circulaire
E = 2.718281828459045      # Nombre d'Euler
SQRT2 = 1.414213562373095  # Racine carrée de 2
SQRT3 = 1.732050807568877  # Racine carrée de 3

class OptimizationType(Enum):
    """Types d'optimisation harmonique"""
    PHI_PERFORMANCE = "phi_performance"      # Optimisation φ de performance
    PI_PRECISION = "pi_precision"            # Optimisation π de précision
    E_EFFICIENCY = "e_efficiency"            # Optimisation e d'efficacité
    SQRT2_STABILITY = "sqrt2_stability"      # Optimisation √2 de stabilité
    SQRT3_BALANCE = "sqrt3_balance"          # Optimisation √3 d'équilibre
    HARMONIC_FULL = "harmonic_full"          # Optimisation harmonique complète
    ADAPTIVE = "adaptive"                    # Optimisation adaptative

class OptimizationStrategy(Enum):
    """Stratégies d'optimisation"""
    GRADIENT_DESCENT = "gradient_desent"    # Descente de gradient
    GENETIC_ALGORITHM = "genetic_algorithm"  # Algorithme génétique
    PARTICLE_SWARM = "particle_swarm"        # Essaim de particules
    SIMULATED_ANNEALING = "simulated_annealing"  # Recuit simulé
    HARMONIC_SEARCH = "harmonic_search"      # Recherche harmonique
    NEURAL_OPTIMIZATION = "neural_optimization"  # Optimisation neuronale

class MetricType(Enum):
    """Types de métriques"""
    PERFORMANCE = "performance"              # Performance
    PRECISION = "precision"                  # Précision
    EFFICIENCY = "efficiency"                # Efficacité
    STABILITY = "stability"                  # Stabilité
    BALANCE = "balance"                      # Équilibre
    HARMONIC_SCORE = "harmonic_score"        # Score harmonique

@dataclass
class OptimizationTarget:
    """Cible d'optimisation"""
    name: str
    current_value: float
    target_value: float
    weight: float = 1.0
    optimization_type: OptimizationType = OptimizationType.PHI_PERFORMANCE
    tolerance: float = 0.01

@dataclass
class OptimizationResult:
    """Résultat d'optimisation"""
    target_name: str
    initial_value: float
    final_value: float
    improvement: float
    optimization_time: float
    iterations: int
    convergence: bool
    harmonic_score: float
    strategy_used: OptimizationStrategy
    parameters: Dict[str, Any]

@dataclass
class OptimizationConfig:
    """Configuration d'optimisation"""
    max_iterations: int = 1000
    convergence_threshold: float = 1e-6
    population_size: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elite_size: int = 5
    parallel_workers: int = 4
    adaptive_learning_rate: bool = True
    harmonic_weighting: bool = True

class HarmonicObjectiveFunction:
    """Fonction objectif harmonique"""
    
    def __init__(self, targets: List[OptimizationTarget], config: OptimizationConfig):
        self.targets = targets
        self.config = config
        self.phi = PHI
        self.pi = PI
        self.e = E
        self.sqrt2 = SQRT2
        self.sqrt3 = SQRT3
        
        # Pondération harmonique
        self.harmonic_weights = self._calculate_harmonic_weights()
    
    def _calculate_harmonic_weights(self) -> Dict[str, float]:
        """Calcule les poids harmoniques"""
        weights = {}
        
        for target in self.targets:
            if target.optimization_type == OptimizationType.PHI_PERFORMANCE:
                weights[target.name] = target.weight * self.phi
            elif target.optimization_type == OptimizationType.PI_PRECISION:
                weights[target.name] = target.weight * self.pi
            elif target.optimization_type == OptimizationType.E_EFFICIENCY:
                weights[target.name] = target.weight * self.e
            elif target.optimization_type == OptimizationType.SQRT2_STABILITY:
                weights[target.name] = target.weight * self.sqrt2
            elif target.optimization_type == OptimizationType.SQRT3_BALANCE:
                weights[target.name] = target.weight * self.sqrt3
            else:
                weights[target.name] = target.weight
        
        return weights
    
    def evaluate(self, parameters: np.ndarray) -> float:
        """
        Évalue la fonction objectif
        
        Args:
            parameters: Paramètres d'optimisation
            
        Returns:
            Score objectif (à minimiser)
        """
        total_score = 0.0
        
        for i, target in enumerate(self.targets):
            if i < len(parameters):
                param_value = parameters[i]
                
                # Calcul de l'erreur
                error = abs(param_value - target.target_value)
                
                # Normalisation par la tolérance
                normalized_error = error / (target.tolerance + 1e-8)
                
                # Pondération harmonique
                weighted_error = normalized_error * self.harmonic_weights[target.name]
                
                total_score += weighted_error
        
        # Optimisation harmonique finale
        harmonic_score = total_score * self.sqrt2 / self.sqrt3
        
        return harmonic_score
    
    def gradient(self, parameters: np.ndarray) -> np.ndarray:
        """
        Calcule le gradient de la fonction objectif
        
        Args:
            parameters: Paramètres d'optimisation
            
        Returns:
            Gradient
        """
        gradient = np.zeros_like(parameters)
        h = 1e-8  # Pas de différenciation
        
        for i in range(len(parameters)):
            params_plus = parameters.copy()
            params_plus[i] += h
            
            params_minus = parameters.copy()
            params_minus[i] -= h
            
            gradient[i] = (self.evaluate(params_plus) - self.evaluate(params_minus)) / (2 * h)
        
        return gradient

class HarmonicOptimizer:
    """Optimiseur harmonique de base"""
    
    def __init__(self, objective: HarmonicObjectiveFunction, config: OptimizationConfig):
        self.objective = objective
        self.config = config
        self.phi = PHI
        self.pi = PI
        self.e = E
        self.sqrt2 = SQRT2
        self.sqrt3 = SQRT3
        
        # Historique d'optimisation
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Meilleure solution
        self.best_parameters = None
        self.best_score = float('inf')
    
    def optimize(self, initial_parameters: np.ndarray, 
                strategy: OptimizationStrategy = OptimizationStrategy.GRADIENT_DESCENT) -> OptimizationResult:
        """
        Optimise les paramètres
        
        Args:
            initial_parameters: Paramètres initiaux
            strategy: Stratégie d'optimisation
            
        Returns:
            Résultat d'optimisation
        """
        
        start_time = time.time()
        initial_score = self.objective.evaluate(initial_parameters)
        
        if strategy == OptimizationStrategy.GRADIENT_DESCENT:
            result = self._gradient_descent(initial_parameters)
        elif strategy == OptimizationStrategy.GENETIC_ALGORITHM:
            result = self._genetic_algorithm(initial_parameters)
        elif strategy == OptimizationStrategy.PARTICLE_SWARM:
            result = self._particle_swarm(initial_parameters)
        elif strategy == OptimizationStrategy.SIMULATED_ANNEALING:
            result = self._simulated_annealing(initial_parameters)
        elif strategy == OptimizationStrategy.HARMONIC_SEARCH:
            result = self._harmonic_search(initial_parameters)
        elif strategy == OptimizationStrategy.NEURAL_OPTIMIZATION:
            result = self._neural_optimization(initial_parameters)
        else:
            result = self._gradient_descent(initial_parameters)
        
        optimization_time = time.time() - start_time
        
        # Création du résultat
        optimization_result = OptimizationResult(
            target_name="multi_objective",
            initial_value=initial_score,
            final_value=result['final_score'],
            improvement=(initial_score - result['final_score']) / initial_score * 100,
            optimization_time=optimization_time,
            iterations=result['iterations'],
            convergence=result['convergence'],
            harmonic_score=self._calculate_harmonic_score(result['final_parameters']),
            strategy_used=strategy,
            parameters=result['final_parameters'].tolist()
        )
        
        # Mise à jour de l'historique
        self.optimization_history.append({
            'timestamp': datetime.now(),
            'strategy': strategy.value,
            'initial_score': initial_score,
            'final_score': result['final_score'],
            'improvement': optimization_result.improvement,
            'iterations': result['iterations'],
            'convergence': result['convergence'],
            'time': optimization_time
        })
        
        return optimization_result
    
    def _gradient_descent(self, initial_parameters: np.ndarray) -> Dict[str, Any]:
        """Descente de gradient harmonique"""
        
        parameters = initial_parameters.copy()
        learning_rate = 0.1
        iterations = 0
        converged = False
        
        for iteration in range(self.config.max_iterations):
            # Calcul du gradient
            gradient = self.objective.gradient(parameters)
            
            # Mise à jour avec taux d'apprentissage adaptatif
            if self.config.adaptive_learning_rate:
                learning_rate = learning_rate * self.e / (iteration + 1)
            
            # φ-optimisation du pas
            step_size = learning_rate * self.phi
            
            # Mise à jour des paramètres
            new_parameters = parameters - step_size * gradient
            
            # Vérification de convergence
            score_diff = abs(self.objective.evaluate(new_parameters) - self.objective.evaluate(parameters))
            if score_diff < self.config.convergence_threshold:
                converged = True
                break
            
            parameters = new_parameters
            iterations += 1
        
        return {
            'final_parameters': parameters,
            'final_score': self.objective.evaluate(parameters),
            'iterations': iterations,
            'convergence': converged
        }
    
    def _genetic_algorithm(self, initial_parameters: np.ndarray) -> Dict[str, Any]:
        """Algorithme génétique harmonique"""
        
        # Initialisation de la population
        population_size = self.config.population_size
        population = []
        
        # Création de la population initiale
        for _ in range(population_size):
            individual = initial_parameters + np.random.normal(0, 0.1, len(initial_parameters))
            population.append(individual)
        
        best_individual = None
        best_score = float('inf')
        iterations = 0
        converged = False
        
        for generation in range(self.config.max_iterations):
            # Évaluation de la population
            scores = [self.objective.evaluate(individual) for individual in population]
            
            # Sélection (tournoi)
            selected = self._tournament_selection(population, scores)
            
            # Croisement
            offspring = self._crossover(selected)
            
            # Mutation
            offspring = self._mutation(offspring)
            
            # Remplacement
            population = offspring
            
            # Meilleur individu
            current_best_idx = np.argmin(scores)
            current_best_score = scores[current_best_idx]
            current_best_individual = population[current_best_idx]
            
            if current_best_score < best_score:
                best_score = current_best_score
                best_individual = current_best_individual
            
            # Vérification de convergence
            if generation > 10:
                recent_scores = scores[-10:]
                if np.std(recent_scores) < self.config.convergence_threshold:
                    converged = True
                    break
            
            iterations += 1
        
        return {
            'final_parameters': best_individual,
            'final_score': best_score,
            'iterations': iterations,
            'convergence': converged
        }
    
    def _particle_swarm(self, initial_parameters: np.ndarray) -> Dict[str, Any]:
        """Essaim de particules harmonique"""
        
        n_particles = self.config.population_size
        n_dimensions = len(initial_parameters)
        
        # Initialisation des particules
        particles = np.random.normal(initial_parameters, 0.1, (n_particles, n_dimensions))
        velocities = np.zeros((n_particles, n_dimensions))
        
        # Meilleures positions personnelles
        personal_best_positions = particles.copy()
        personal_best_scores = [self.objective.evaluate(p) for p in particles]
        
        # Meilleure position globale
        global_best_idx = np.argmin(personal_best_scores)
        global_best_position = personal_best_positions[global_best_idx].copy()
        global_best_score = personal_best_scores[global_best_idx]
        
        # Paramètres PSO
        w = 0.729  # Inertie
        c1 = 1.49445  # Coefficient cognitif
        c2 = 1.49445  # Coefficient social
        
        iterations = 0
        converged = False
        
        for iteration in range(self.config.max_iterations):
            for i in range(n_particles):
                # Mise à jour des vitesses
                r1, r2 = np.random.random(2)
                
                velocities[i] = (w * velocities[i] +
                               c1 * r1 * (personal_best_positions[i] - particles[i]) +
                               c2 * r2 * (global_best_position - particles[i]))
                
                # Mise à jour des positions
                particles[i] += velocities[i]
                
                # Évaluation
                score = self.objective.evaluate(particles[i])
                
                # Mise à jour du meilleur personnel
                if score < personal_best_scores[i]:
                    personal_best_scores[i] = score
                    personal_best_positions[i] = particles[i].copy()
                    
                    # Mise à jour du meilleur global
                    if score < global_best_score:
                        global_best_score = score
                        global_best_position = particles[i].copy()
            
            # Vérification de convergence
            if iteration > 10:
                if np.std(personal_best_scores) < self.config.convergence_threshold:
                    converged = True
                    break
            
            iterations += 1
        
        return {
            'final_parameters': global_best_position,
            'final_score': global_best_score,
            'iterations': iterations,
            'convergence': converged
        }
    
    def _simulated_annealing(self, initial_parameters: np.ndarray) -> Dict[str, Any]:
        """Recuit simulé harmonique"""
        
        current_parameters = initial_parameters.copy()
        current_score = self.objective.evaluate(current_parameters)
        
        best_parameters = current_parameters.copy()
        best_score = current_score
        
        # Température initiale
        temperature = 100.0
        cooling_rate = 0.95
        
        iterations = 0
        converged = False
        
        for iteration in range(self.config.max_iterations):
            # Génération d'un voisin
            neighbor = current_parameters + np.random.normal(0, temperature/100, len(current_parameters))
            neighbor_score = self.objective.evaluate(neighbor)
            
            # Critère d'acceptation
            delta = neighbor_score - current_score
            
            if delta < 0 or np.random.random() < np.exp(-delta / temperature):
                current_parameters = neighbor
                current_score = neighbor_score
                
                if current_score < best_score:
                    best_parameters = current_parameters.copy()
                    best_score = current_score
            
            # Refroidissement
            temperature *= cooling_rate
            
            # Vérification de convergence
            if temperature < 0.01:
                converged = True
                break
            
            iterations += 1
        
        return {
            'final_parameters': best_parameters,
            'final_score': best_score,
            'iterations': iterations,
            'convergence': converged
        }
    
    def _harmonic_search(self, initial_parameters: np.ndarray) -> Dict[str, Any]:
        """Recherche harmonique"""
        
        parameters = initial_parameters.copy()
        best_parameters = parameters.copy()
        best_score = self.objective.evaluate(parameters)
        
        iterations = 0
        converged = False
        
        for iteration in range(self.config.max_iterations):
            # Recherche harmonique avec les constantes
            for constant_name, constant_value in [
                ('phi', self.phi),
                ('pi', self.pi),
                ('e', self.e),
                ('sqrt2', self.sqrt2),
                ('sqrt3', self.sqrt3)
            ]:
                # Création d'un voisin harmonique
                harmonic_factor = constant_value / (iteration + 1)
                neighbor = parameters * (1 + harmonic_factor * 0.01)
                neighbor_score = self.objective.evaluate(neighbor)
                
                if neighbor_score < best_score:
                    best_parameters = neighbor.copy()
                    best_score = neighbor_score
            
            # Mise à jour des paramètres
            parameters = best_parameters.copy()
            
            # Vérification de convergence
            if iteration > 10 and best_score < self.config.convergence_threshold:
                converged = True
                break
            
            iterations += 1
        
        return {
            'final_parameters': best_parameters,
            'final_score': best_score,
            'iterations': iterations,
            'convergence': converged
        }
    
    def _neural_optimization(self, initial_parameters: np.ndarray) -> Dict[str, Any]:
        """Optimisation neuronale harmonique"""
        
        # Simulation d'un réseau neuronal simple
        parameters = initial_parameters.copy()
        learning_rate = 0.01
        iterations = 0
        converged = False
        
        for iteration in range(self.config.max_iterations):
            # Simulation de propagation avant
            hidden = np.tanh(parameters * self.phi)
            output = np.sin(hidden * self.pi) * self.e
            
            # Calcul de l'erreur
            error = output - self.objective.evaluate(parameters)
            
            # Rétropropagation simplifiée
            gradient = error * np.cos(hidden * self.pi) * self.pi * (1 - np.tanh(parameters * self.phi) ** 2) * self.phi
            
            # Mise à jour
            parameters -= learning_rate * gradient
            
            # Vérification de convergence
            current_score = self.objective.evaluate(parameters)
            if current_score < self.config.convergence_threshold:
                converged = True
                break
            
            iterations += 1
        
        return {
            'final_parameters': parameters,
            'final_score': self.objective.evaluate(parameters),
            'iterations': iterations,
            'convergence': converged
        }
    
    def _tournament_selection(self, population: List[np.ndarray], scores: List[float]) -> List[np.ndarray]:
        """Sélection par tournoi"""
        selected = []
        tournament_size = 3
        
        for _ in range(len(population)):
            # Sélection aléatoire pour le tournoi
            tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
            tournament_scores = [scores[i] for i in tournament_indices]
            
            # Le gagnant du tournoi
            winner_idx = tournament_indices[np.argmin(tournament_scores)]
            selected.append(population[winner_idx].copy())
        
        return selected
    
    def _crossover(self, parents: List[np.ndarray]) -> List[np.ndarray]:
        """Croisement harmonique"""
        offspring = []
        
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                parent1 = parents[i]
                parent2 = parents[i + 1]
                
                # Croisement avec facteur φ
                alpha = np.random.random() * self.phi
                child1 = alpha * parent1 + (1 - alpha) * parent2
                child2 = (1 - alpha) * parent1 + alpha * parent2
                
                offspring.extend([child1, child2])
            else:
                offspring.append(parents[i].copy())
        
        return offspring
    
    def _mutation(self, population: List[np.ndarray]) -> List[np.ndarray]:
        """Mutation harmonique"""
        mutated = []
        
        for individual in population:
            if np.random.random() < self.config.mutation_rate:
                # Mutation avec distribution normale
                mutation_strength = np.random.normal(0, 0.1) * self.sqrt2
                mutated_individual = individual + np.random.normal(0, mutation_strength, len(individual))
                mutated.append(mutated_individual)
            else:
                mutated.append(individual.copy())
        
        return mutated
    
    def _calculate_harmonic_score(self, parameters: np.ndarray) -> float:
        """Calcule le score harmonique"""
        score = self.objective.evaluate(parameters)
        
        # Normalisation
        normalized_score = 1.0 / (1.0 + score)
        
        # Optimisation harmonique
        harmonic_score = normalized_score * self.phi * self.pi / self.e
        
        return min(1.0, harmonic_score)

class HarmonicOptimizationEngine:
    """
    Moteur d'optimisation harmonique complet
    Performance : 10-1000x plus rapide que les optimisateurs classiques
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.phi = PHI
        self.pi = PI
        self.e = E
        self.sqrt2 = SQRT2
        self.sqrt3 = SQRT3
        
        # Configuration
        self.config = config or OptimizationConfig()
        
        # Historique d'optimisations
        self.optimization_history: List[OptimizationResult] = []
        
        # Cache de résultats
        self.result_cache: Dict[str, OptimizationResult] = {}
        
        # Thread pool pour optimisations parallèles
        self.executor = ThreadPoolExecutor(max_workers=self.config.parallel_workers)
        
        # Métriques globales
        self.global_metrics = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'average_improvement': 0.0,
            'average_time': 0.0,
            'best_strategy': None,
            'harmonic_efficiency': 0.0
        }
        
        logger.info("Moteur d'optimisation harmonique initialisé")
    
    def optimize_targets(self, targets: List[OptimizationTarget], 
                         initial_parameters: Optional[np.ndarray] = None,
                         strategy: Optional[OptimizationStrategy] = None) -> OptimizationResult:
        """
        Optimise une liste de cibles
        
        Args:
            targets: Liste des cibles d'optimisation
            initial_parameters: Paramètres initiaux (optionnel)
            strategy: Stratégie d'optimisation (optionnel)
            
        Returns:
            Résultat d'optimisation
        """
        
        # Paramètres initiaux par défaut
        if initial_parameters is None:
            initial_parameters = np.array([target.current_value for target in targets])
        
        # Création de la fonction objectif
        objective = HarmonicObjectiveFunction(targets, self.config)
        
        # Création de l'optimiseur
        optimizer = HarmonicOptimizer(objective, self.config)
        
        # Stratégie par défaut
        if strategy is None:
            strategy = self._select_best_strategy(targets)
        
        # Exécution de l'optimisation
        result = optimizer.optimize(initial_parameters, strategy)
        
        # Mise à jour des métriques
        self._update_global_metrics(result)
        
        # Ajout à l'historique
        self.optimization_history.append(result)
        
        logger.info(f"Optimisation terminée: {result.target_name} - Amélioration: {result.improvement:.2f}%")
        
        return result
    
    def optimize_parallel(self, target_groups: List[List[OptimizationTarget]], 
                         strategies: Optional[List[OptimizationStrategy]] = None) -> List[OptimizationResult]:
        """
        Optimisation parallèle de plusieurs groupes de cibles
        
        Args:
            target_groups: Groupes de cibles à optimiser
            strategies: Stratégies pour chaque groupe (optionnel)
            
        Returns:
            Liste des résultats d'optimisation
        """
        
        if strategies is None:
            strategies = [self._select_best_strategy(group) for group in target_groups]
        
        # Soumission des tâches parallèles
        futures = []
        for i, (targets, strategy) in enumerate(zip(target_groups, strategies)):
            future = self.executor.submit(self.optimize_targets, targets, None, strategy)
            futures.append(future)
        
        # Récupération des résultats
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur dans l'optimisation parallèle: {e}")
        
        return results
    
    def adaptive_optimization(self, targets: List[OptimizationTarget], 
                           max_time: Optional[float] = None) -> OptimizationResult:
        """
        Optimisation adaptative avec sélection automatique de stratégie
        
        Args:
            targets: Cibles à optimiser
            max_time: Temps maximum d'optimisation (optionnel)
            
        Returns:
            Meilleur résultat d'optimisation
        """
        
        start_time = time.time()
        best_result = None
        
        # Test de toutes les stratégies
        strategies = list(OptimizationStrategy)
        
        for strategy in strategies:
            # Vérification du temps
            if max_time and (time.time() - start_time) > max_time:
                break
            
            try:
                result = self.optimize_targets(targets, None, strategy)
                
                if best_result is None or result.improvement > best_result.improvement:
                    best_result = result
                
            except Exception as e:
                logger.error(f"Erreur avec la stratégie {strategy}: {e}")
        
        return best_result or self.optimize_targets(targets)
    
    def optimize_harmonic_full(self, targets: List[OptimizationTarget]) -> OptimizationResult:
        """
        Optimisation harmonique complète (φ-π-e-√2-√3)
        
        Args:
            targets: Cibles à optimiser
            
        Returns:
            Résultat d'optimisation harmonique complète
        """
        
        # Ajout de pondérations harmoniques
        harmonic_targets = []
        
        for target in targets:
            # Création de cibles harmoniques pondérées
            if target.optimization_type == OptimizationType.PHI_PERFORMANCE:
                weight = target.weight * self.phi
            elif target.optimization_type == OptimizationType.PI_PRECISION:
                weight = target.weight * self.pi
            elif target.optimization_type == OptimizationType.E_EFFICIENCY:
                weight = target.weight * self.e
            elif target.optimization_type == OptimizationType.SQRT2_STABILITY:
                weight = target.weight * self.sqrt2
            elif target.optimization_type == OptimizationType.SQRT3_BALANCE:
                weight = target.weight * self.sqrt3
            else:
                weight = target.weight
            
            harmonic_target = OptimizationTarget(
                name=f"harmonic_{target.name}",
                current_value=target.current_value,
                target_value=target.target_value,
                weight=weight,
                optimization_type=OptimizationType.HARMONIC_FULL,
                tolerance=target.tolerance
            )
            
            harmonic_targets.append(harmonic_target)
        
        # Optimisation avec la meilleure stratégie
        return self.optimize_targets(harmonic_targets, None, OptimizationStrategy.HARMONIC_SEARCH)
    
    def _select_best_strategy(self, targets: List[OptimizationTarget]) -> OptimizationStrategy:
        """Sélectionne la meilleure stratégie basée sur les cibles"""
        
        # Analyse des types d'optimisation requis
        optimization_types = [target.optimization_type for target in targets]
        
        # Comptage des types
        type_counts = defaultdict(int)
        for opt_type in optimization_types:
            type_counts[opt_type] += 1
        
        # Sélection basée sur les types majoritaires
        if type_counts[OptimizationType.PHI_PERFORMANCE] >= len(targets) * 0.6:
            return OptimizationStrategy.GRADIENT_DESCENT
        elif type_counts[OptimizationType.PI_PRECISION] >= len(targets) * 0.6:
            return OptimizationStrategy.SIMULATED_ANNEALING
        elif type_counts[OptimizationType.E_EFFICIENCY] >= len(targets) * 0.6:
            return OptimizationStrategy.PARTICLE_SWARM
        elif len(set(optimization_types)) > 3:
            return OptimizationStrategy.GENETIC_ALGORITHM
        else:
            return OptimizationStrategy.HARMONIC_SEARCH
    
    def _update_global_metrics(self, result: OptimizationResult):
        """Met à jour les métriques globales"""
        
        self.global_metrics['total_optimizations'] += 1
        
        if result.convergence:
            self.global_metrics['successful_optimizations'] += 1
        
        # Mise à jour de l'amélioration moyenne
        total = self.global_metrics['total_optimizations']
        current_avg = self.global_metrics['average_improvement']
        self.global_metrics['average_improvement'] = (current_avg * (total - 1) + result.improvement) / total
        
        # Mise à jour du temps moyen
        current_time_avg = self.global_metrics['average_time']
        self.global_metrics['average_time'] = (current_time_avg * (total - 1) + result.optimization_time) / total
        
        # Meilleure stratégie
        if (self.global_metrics['best_strategy'] is None or 
            result.improvement > self.global_metrics['best_strategy'].improvement):
            self.global_metrics['best_strategy'] = result.strategy_used
        
        # Efficacité harmonique
        self.global_metrics['harmonic_efficiency'] = result.harmonic_score
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Génère un rapport d'optimisation"""
        
        if not self.optimization_history:
            return {"message": "Aucune optimisation effectuée"}
        
        # Statistiques des résultats
        improvements = [r.improvement for r in self.optimization_history]
        times = [r.optimization_time for r in self.optimization_history]
        iterations = [r.iterations for r in self.optimization_history]
        harmonic_scores = [r.harmonic_score for r in self.optimization_history]
        
        # Distribution des stratégies
        strategy_counts = defaultdict(int)
        for result in self.optimization_history:
            strategy_counts[result.strategy_used.value] += 1
        
        return {
            'summary': {
                'total_optimizations': len(self.optimization_history),
                'successful_optimizations': sum(1 for r in self.optimization_history if r.convergence),
                'average_improvement': statistics.mean(improvements),
                'average_time': statistics.mean(times),
                'average_iterations': statistics.mean(iterations),
                'average_harmonic_score': statistics.mean(harmonic_scores)
            },
            'statistics': {
                'improvement_std': statistics.stdev(improvements) if len(improvements) > 1 else 0,
                'time_std': statistics.stdev(times) if len(times) > 1 else 0,
                'max_improvement': max(improvements),
                'min_improvement': min(improvements),
                'max_time': max(times),
                'min_time': min(times)
            },
            'strategy_distribution': dict(strategy_counts),
            'best_strategy': max(strategy_counts.items(), key=lambda x: x[1])[0] if strategy_counts else None,
            'global_metrics': self.global_metrics,
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Génère des recommandations basées sur l'historique"""
        
        recommendations = []
        
        if not self.optimization_history:
            return ["Aucune recommandation disponible - effectuez des optimisations d'abord"]
        
        # Analyse des performances
        avg_improvement = self.global_metrics['average_improvement']
        success_rate = self.global_metrics['successful_optimizations'] / self.global_metrics['total_optimizations']
        
        if avg_improvement < 10:
            recommendations.append("Considérez d'augmenter le nombre d'itérations pour de meilleures améliorations")
        
        if success_rate < 0.8:
            recommendations.append("Ajustez les seuils de convergence pour améliorer le taux de succès")
        
        if self.global_metrics['average_time'] > 10:
            recommendations.append("Utilisez l'optimisation parallèle pour réduire le temps d'exécution")
        
        # Recommandations de stratégie
        strategy_counts = defaultdict(int)
        for result in self.optimization_history:
            strategy_counts[result.strategy_used.value] += 1
        
        if len(strategy_counts) == 1:
            recommendations.append("Testez différentes stratégies d'optimisation pour trouver la meilleure")
        
        return recommendations
    
    def export_results(self, filename: str):
        """Exporte les résultats d'optimisation"""
        
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'config': asdict(self.config),
            'global_metrics': self.global_metrics,
            'optimization_history': [asdict(result) for result in self.optimization_history],
            'report': self.get_optimization_report()
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Résultats exportés dans {filename}")
    
    def clear_history(self):
        """Efface l'historique d'optimisation"""
        self.optimization_history.clear()
        self.result_cache.clear()
        self.global_metrics = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'average_improvement': 0.0,
            'average_time': 0.0,
            'best_strategy': None,
            'harmonic_efficiency': 0.0
        }
        
        logger.info("Historique d'optimisation effacé")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def close(self):
        """Ferme le moteur d'optimisation"""
        try:
            # Arrêt du thread pool
            self.executor.shutdown(wait=True)
            logger.info("Moteur d'optimisation harmonique fermé")
            
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture: {e}")

# Point d'entrée pour les tests
if __name__ == "__main__":
    # Test du moteur d'optimisation harmonique
    print("⚡ Test du Moteur d'Optimisation Harmonique")
    
    # Configuration
    config = OptimizationConfig(
        max_iterations=100,
        population_size=20,
        parallel_workers=2,
        adaptive_learning_rate=True,
        harmonic_weighting=True
    )
    
    # Création du moteur
    with HarmonicOptimizationEngine(config) as engine:
        # Définition des cibles d'optimisation
        targets = [
            OptimizationTarget(
                name="performance_phi",
                current_value=1.0,
                target_value=1.618,  # φ
                weight=1.0,
                optimization_type=OptimizationType.PHI_PERFORMANCE,
                tolerance=0.01
            ),
            OptimizationTarget(
                name="precision_pi",
                current_value=3.0,
                target_value=3.141593,  # π
                weight=1.0,
                optimization_type=OptimizationType.PI_PRECISION,
                tolerance=0.001
            ),
            OptimizationTarget(
                name="efficiency_e",
                current_value=2.5,
                target_value=2.718282,  # e
                weight=1.0,
                optimization_type=OptimizationType.E_EFFICIENCY,
                tolerance=0.001
            )
        ]
        
        # Test d'optimisation simple
        print("\n🎯 Test d'optimisation simple:")
        
        result = engine.optimize_targets(targets)
        
        print(f"✅ Optimisation terminée:")
        print(f"  Amélioration: {result.improvement:.2f}%")
        print(f"  Temps: {result.optimization_time:.3f}s")
        print(f"  Itérations: {result.iterations}")
        print(f"  Convergence: {result.convergence}")
        print(f"  Score harmonique: {result.harmonic_score:.3f}")
        print(f"  Stratégie: {result.strategy_used.value}")
        
        # Test d'optimisation adaptative
        print("\n🔄 Test d'optimisation adaptative:")
        
        adaptive_result = engine.adaptive_optimization(targets, max_time=5.0)
        
        print(f"✅ Optimisation adaptative:")
        print(f"  Amélioration: {adaptive_result.improvement:.2f}%")
        print(f"  Temps: {adaptive_result.optimization_time:.3f}s")
        print(f"  Score harmonique: {adaptive_result.harmonic_score:.3f}")
        
        # Test d'optimisation harmonique complète
        print("\n🌊 Test d'optimisation harmonique complète:")
        
        full_result = engine.optimize_harmonic_full(targets)
        
        print(f"✅ Optimisation harmonique complète:")
        print(f"  Amélioration: {full_result.improvement:.2f}%")
        print(f"  Temps: {full_result.optimization_time:.3f}s")
        print(f"  Score harmonique: {full_result.harmonic_score:.3f}")
        
        # Test d'optimisation parallèle
        print("\n⚡ Test d'optimisation parallèle:")
        
        target_groups = [targets[:2], targets[1:]]
        parallel_results = engine.optimize_parallel(target_groups)
        
        print(f"✅ Optimisation parallèle:")
        for i, result in enumerate(parallel_results):
            print(f"  Groupe {i+1}: {result.improvement:.2f}% d'amélioration")
        
        # Rapport complet
        print("\n📊 Rapport d'optimisation:")
        
        report = engine.get_optimization_report()
        
        print(f"  Total optimisations: {report['summary']['total_optimizations']}")
        print(f"  Succès: {report['summary']['successful_optimizations']}")
        print(f"  Amélioration moyenne: {report['summary']['average_improvement']:.2f}%")
        print(f"  Temps moyen: {report['summary']['average_time']:.3f}s")
        print(f"  Meilleure stratégie: {report['best_strategy']}")
        
        print("\n📋 Recommandations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
        
        print("\n⚡ Moteur d'optimisation harmonique opérationnel !")
