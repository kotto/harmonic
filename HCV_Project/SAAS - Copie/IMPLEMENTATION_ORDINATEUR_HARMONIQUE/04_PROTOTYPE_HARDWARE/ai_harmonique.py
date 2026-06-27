"""
🤖 AI-HARMONIC - Intelligence Artificielle Harmonique
Fichier: ai_harmonique.py
Auteur: Équipe Harmonique
Date: 28 avril 2026
Description: Implémentation des algorithmes d'IA optimisés avec les constantes harmoniques
"""

import numpy as np
import time
import logging
from typing import List, Tuple, Dict, Any, Optional, Callable
from dataclasses import dataclass
from classique_harmonique import ClassicalHarmonicComputer, PHI, PI, E

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AIMetrics:
    """Métriques d'IA harmonique"""
    accuracy: float
    loss: float
    training_time: float
    inference_time: float
    convergence_epoch: int
    harmonic_factor: float

class HarmonicNeuralNetwork:
    """
    Réseau neuronal harmonique
    """
    
    def __init__(self, harmonic_computer: ClassicalHarmonicComputer):
        self.computer = harmonic_computer
        self.phi_optimization = PHI
        self.pi_optimization = PI
        self.e_optimization = E
        
        # Paramètres harmoniques
        self.weights = []
        self.biases = []
        self.activations = []
        
        logger.info("HarmonicNeuralNetwork initialisé")
    
    def harmonic_sigmoid(self, x: np.ndarray) -> np.ndarray:
        """
        Fonction d'activation sigmoïde harmonique
        
        Args:
            x: Vecteur d'entrée
            
        Returns:
            Activation sigmoïde harmonique
        """
        # σ_H(x) = 1 / (1 + exp(-φ × x / π))
        return 1.0 / (1.0 + np.exp(-self.phi_optimization * x / self.pi_optimization))
    
    def harmonic_sigmoid_derivative(self, x: np.ndarray) -> np.ndarray:
        """
        Dérivée de la sigmoïde harmonique
        
        Args:
            x: Vecteur d'entrée
            
        Returns:
            Dérivée de la sigmoïde harmonique
        """
        s = self.harmonic_sigmoid(x)
        return (self.phi_optimization / self.pi_optimization) * s * (1 - s)
    
    def harmonic_relu(self, x: np.ndarray) -> np.ndarray:
        """
        Fonction d'activation ReLU harmonique
        
        Args:
            x: Vecteur d'entrée
            
        Returns:
            Activation ReLU harmonique
        """
        return np.maximum(0, x * self.phi_optimization)
    
    def harmonic_relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """
        Dérivée de la ReLU harmonique
        
        Args:
            x: Vecteur d'entrée
            
        Returns:
            Dérivée de la ReLU harmonique
        """
        return np.where(x > 0, self.phi_optimization, 0)
    
    def harmonic_tanh(self, x: np.ndarray) -> np.ndarray:
        """
        Fonction d'activation tanh harmonique
        
        Args:
            x: Vecteur d'entrée
            
        Returns:
            Activation tanh harmonique
        """
        return np.tanh(x * self.phi_optimization / self.pi_optimization)
    
    def harmonic_tanh_derivative(self, x: np.ndarray) -> np.ndarray:
        """
        Dérivée de la tanh harmonique
        
        Args:
            x: Vecteur d'entrée
            
        Returns:
            Dérivée de la tanh harmonique
        """
        t = self.harmonic_tanh(x)
        return (self.phi_optimization / self.pi_optimization) * (1 - t * t)
    
    def initialize_weights_harmonique(self, layer_sizes: List[int]) -> None:
        """
        Initialisation harmonique des poids
        
        Args:
            layer_sizes: Tailles des couches
        """
        self.weights = []
        self.biases = []
        
        for i in range(len(layer_sizes) - 1):
            # Initialisation harmonique
            n_in = layer_sizes[i]
            n_out = layer_sizes[i + 1]
            
            # Poids harmoniques : distribution φ
            W = np.random.randn(n_in, n_out) * np.sqrt(2.0 / (n_in + n_out)) / self.phi_optimization
            b = np.zeros((1, n_out)) / self.pi_optimization
            
            self.weights.append(W)
            self.biases.append(b)
        
        logger.info(f"Poids harmoniques initialisés pour {len(layer_sizes)} couches")
    
    def forward_harmonique(self, X: np.ndarray) -> np.ndarray:
        """
        Propagation avant harmonique
        
        Args:
            X: Données d'entrée
            
        Returns:
            Sortie du réseau
        """
        self.activations = [X]
        
        for i, (W, b) in enumerate(zip(self.weights, self.biases)):
            Z = np.dot(self.activations[-1], W) + b
            
            # Activation harmonique
            if i == len(self.weights) - 1:
                # Couche de sortie : sigmoïde
                A = self.harmonic_sigmoid(Z)
            else:
                # Couches cachées : tanh
                A = self.harmonic_tanh(Z)
            
            self.activations.append(A)
        
        return self.activations[-1]
    
    def backward_harmonique(self, X: np.ndarray, y: np.ndarray, learning_rate: float) -> float:
        """
        Rétropropagation harmonique
        
        Args:
            X: Données d'entrée
            y: Étiquettes
            learning_rate: Taux d'apprentissage
            
        Returns:
            Perte
        """
        m = X.shape[0]
        
        # Propagation avant
        output = self.forward_harmonique(X)
        
        # Calcul de la perte harmonique
        loss = -np.mean(y * np.log(output + 1e-10) + (1 - y) * np.log(1 - output + 1e-10))
        
        # Rétropropagation
        dZ = output - y
        
        for i in reversed(range(len(self.weights))):
            dA_prev = np.dot(dZ, self.weights[i].T)
            
            # Gradient harmonique
            if i == len(self.weights) - 1:
                # Dérivée sigmoïde
                dZ = dA_prev * self.harmonic_sigmoid_derivative(self.activations[i + 1])
            else:
                # Dérivée tanh
                dZ = dA_prev * self.harmonic_tanh_derivative(self.activations[i + 1])
            
            # Correction des dimensions
            dZ = dZ.reshape(self.activations[i].shape[0], -1)
            
            # Mise à jour harmonique des poids
            dW = np.dot(self.activations[i].T, dZ) / m
            db = np.sum(dZ, axis=0, keepdims=True) / m
            
            # Optimisation harmonique du taux d'apprentissage
            lr_h = learning_rate * (1 + self.phi_optimization / (i + 1)) * np.exp(-i / self.pi_optimization)
            
            self.weights[i] -= lr_h * dW
            self.biases[i] -= lr_h * db
        
        return loss
    
    def train_harmonique(self, X: np.ndarray, y: np.ndarray, epochs: int = 1000, 
                        learning_rate: float = 0.01, verbose: bool = True) -> AIMetrics:
        """
        Entraînement harmonique du réseau
        
        Args:
            X: Données d'entraînement
            y: Étiquettes
            epochs: Nombre d'époques
            learning_rate: Taux d'apprentissage
            verbose: Affichage de la progression
            
        Returns:
            Métriques d'entraînement
        """
        start_time = time.time()
        
        losses = []
        convergence_epoch = 0
        prev_loss = float('inf')
        
        for epoch in range(epochs):
            loss = self.backward_harmonique(X, y, learning_rate)
            losses.append(loss)
            
            # Critère de convergence harmonique
            if abs(prev_loss - loss) < 1e-6 and convergence_epoch == 0:
                convergence_epoch = epoch
            
            prev_loss = loss
            
            if verbose and epoch % 100 == 0:
                logger.info(f"Époque {epoch}: Perte = {loss:.6f}")
        
        training_time = time.time() - start_time
        
        # Calcul de l'accuracy
        predictions = self.predict_harmonique(X)
        accuracy = np.mean((predictions > 0.5) == y)
        
        # Temps d'inférence
        inference_start = time.time()
        _ = self.predict_harmonique(X)
        inference_time = time.time() - inference_start
        
        # Facteur harmonique
        harmonic_factor = np.mean(losses) * self.phi_optimization / self.pi_optimization
        
        logger.info(f"Entraînement harmonique terminé: {epochs} époques en {training_time:.4f}s")
        
        return AIMetrics(
            accuracy=accuracy,
            loss=losses[-1],
            training_time=training_time,
            inference_time=inference_time,
            convergence_epoch=convergence_epoch,
            harmonic_factor=harmonic_factor
        )
    
    def predict_harmonique(self, X: np.ndarray) -> np.ndarray:
        """
        Prédiction harmonique
        
        Args:
            X: Données d'entrée
            
        Returns:
            Prédictions
        """
        return self.forward_harmonique(X)

class HarmonicGradientBoosting:
    """
    Gradient Boosting harmonique
    """
    
    def __init__(self, harmonic_computer: ClassicalHarmonicComputer):
        self.computer = harmonic_computer
        self.phi_optimization = PHI
        self.pi_optimization = PI
        
        self.trees = []
        self.learning_rates = []
        
        logger.info("HarmonicGradientBoosting initialisé")
    
    def harmonic_decision_stump(self, X: np.ndarray, y: np.ndarray, residuals: np.ndarray) -> Dict[str, Any]:
        """
        Arbre de décision harmonique (stump)
        
        Args:
            X: Caractéristiques
            y: Étiquettes
            residuals: Résidus
            
        Returns:
            Arbre de décision harmonique
        """
        n_samples, n_features = X.shape
        best_feature = 0
        best_threshold = 0
        best_loss = float('inf')
        
        for feature in range(n_features):
            # Seuils harmoniques basés sur φ
            thresholds = np.unique(X[:, feature])
            phi_thresholds = [t * self.phi_optimization for t in thresholds]
            
            for threshold in phi_thresholds:
                # Division harmonique
                left_mask = X[:, feature] <= threshold
                right_mask = ~left_mask
                
                if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
                    continue
                
                # Prédictions harmoniques
                left_pred = np.mean(residuals[left_mask])
                right_pred = np.mean(residuals[right_mask])
                
                # Calcul de la perte harmonique
                left_loss = np.sum((residuals[left_mask] - left_pred) ** 2)
                right_loss = np.sum((residuals[right_mask] - right_pred) ** 2)
                total_loss = (left_loss + right_loss) / self.phi_optimization
                
                if total_loss < best_loss:
                    best_loss = total_loss
                    best_feature = feature
                    best_threshold = threshold
        
        return {
            'feature': best_feature,
            'threshold': best_threshold,
            'left_value': np.mean(residuals[X[:, best_feature] <= best_threshold]),
            'right_value': np.mean(residuals[X[:, best_feature] > best_threshold])
        }
    
    def fit_harmonique(self, X: np.ndarray, y: np.ndarray, n_estimators: int = 100, 
                      learning_rate: float = 0.1) -> None:
        """
        Entraînement harmonique du Gradient Boosting
        
        Args:
            X: Caractéristiques
            y: Étiquettes
            n_estimators: Nombre d'estimateurs
            learning_rate: Taux d'apprentissage
        """
        # Initialisation harmonique
        predictions = np.full(y.shape, np.mean(y))
        
        for i in range(n_estimators):
            # Calcul des résidus harmoniques
            residuals = y - predictions
            
            # Arbre de décision harmonique
            tree = self.harmonic_decision_stump(X, y, residuals)
            
            # Taux d'apprentissage harmonique
            lr_h = learning_rate * (1 + self.phi_optimization / (i + 1)) * np.exp(-i / self.pi_optimization)
            
            # Mise à jour des prédictions
            for j in range(len(X)):
                if X[j, tree['feature']] <= tree['threshold']:
                    predictions[j] += lr_h * tree['left_value']
                else:
                    predictions[j] += lr_h * tree['right_value']
            
            self.trees.append(tree)
            self.learning_rates.append(lr_h)
            
            if i % 20 == 0:
                logger.info(f"Arbre {i}: Perte = {np.mean((y - predictions) ** 2):.6f}")
        
        logger.info(f"Gradient Boosting harmonique entraîné: {n_estimators} arbres")
    
    def predict_harmonique(self, X: np.ndarray) -> np.ndarray:
        """
        Prédiction harmonique
        
        Args:
            X: Caractéristiques
            
        Returns:
            Prédictions
        """
        predictions = np.full(X.shape[0], 0.0)
        
        for tree, lr in zip(self.trees, self.learning_rates):
            for i in range(len(X)):
                if X[i, tree['feature']] <= tree['threshold']:
                    predictions[i] += lr * tree['left_value']
                else:
                    predictions[i] += lr * tree['right_value']
        
        return predictions

class HarmonicClustering:
    """
    Clustering harmonique
    """
    
    def __init__(self, harmonic_computer: ClassicalHarmonicComputer):
        self.computer = harmonic_computer
        self.phi_optimization = PHI
        self.pi_optimization = PI
        
        logger.info("HarmonicClustering initialisé")
    
    def kmeans_harmonique(self, X: np.ndarray, k: int, max_iter: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        K-Means harmonique
        
        Args:
            X: Données à clusteriser
            k: Nombre de clusters
            max_iter: Nombre maximum d'itérations
            
        Returns:
            Tuple (centroids, labels)
        """
        n_samples, n_features = X.shape
        
        # Initialisation harmonique des centroids
        centroids = X[np.random.choice(n_samples, k, replace=False)]
        centroids = centroids * self.phi_optimization / self.pi_optimization
        
        for iteration in range(max_iter):
            # Assignment harmonique
            distances = np.zeros((n_samples, k))
            for i in range(k):
                # Distance harmonique
                diff = X - centroids[i]
                distances[:, i] = np.sum(diff ** 2, axis=1) * self.phi_optimization
            
            labels = np.argmin(distances, axis=1)
            
            # Update harmonique des centroids
            new_centroids = np.zeros((k, n_features))
            for i in range(k):
                cluster_points = X[labels == i]
                if len(cluster_points) > 0:
                    new_centroids[i] = np.mean(cluster_points, axis=0) * self.phi_optimization / self.pi_optimization
            
            # Convergence harmonique
            if np.all(np.abs(centroids - new_centroids) < 1e-6):
                break
            
            centroids = new_centroids
        
        logger.info(f"K-Means harmonique: {k} clusters en {iteration + 1} itérations")
        
        return centroids, labels
    
    def hierarchical_harmonique(self, X: np.ndarray) -> np.ndarray:
        """
        Clustering hiérarchique harmonique
        
        Args:
            X: Données à clusteriser
            
        Returns:
            Matrice de liaison
        """
        n_samples = X.shape[0]
        
        # Matrice de distances harmoniques
        distances = np.zeros((n_samples, n_samples))
        for i in range(n_samples):
            for j in range(i + 1, n_samples):
                # Distance harmonique
                dist = np.sum((X[i] - X[j]) ** 2) * self.phi_optimization
                distances[i, j] = distances[j, i] = dist
        
        # Clustering hiérarchique harmonique
        linkage_matrix = []
        clusters = [[i] for i in range(n_samples)]
        
        while len(clusters) > 1:
            # Recherche du couple le plus proche
            min_dist = float('inf')
            best_pair = (0, 1)
            
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # Distance entre clusters harmonique
                    cluster_dist = 0
                    for point_i in clusters[i]:
                        for point_j in clusters[j]:
                            cluster_dist += distances[point_i, point_j]
                    
                    cluster_dist /= (len(clusters[i]) * len(clusters[j])) * self.pi_optimization
                    
                    if cluster_dist < min_dist:
                        min_dist = cluster_dist
                        best_pair = (i, j)
            
            # Fusion harmonique
            i, j = best_pair
            new_cluster = clusters[i] + clusters[j]
            
            linkage_matrix.append([clusters[i][0], clusters[j][0], min_dist, len(new_cluster)])
            
            # Mise à jour des clusters
            clusters.pop(max(i, j))
            clusters.pop(min(i, j))
            clusters.append(new_cluster)
        
        logger.info("Clustering hiérarchique harmonique terminé")
        
        return np.array(linkage_matrix)

class HarmonicComputerVision:
    """
    Vision par ordinateur harmonique
    """
    
    def __init__(self, harmonic_computer: ClassicalHarmonicComputer):
        self.computer = harmonic_computer
        self.phi_optimization = PHI
        self.pi_optimization = PI
        
        logger.info("HarmonicComputerVision initialisé")
    
    def harmonic_convolution(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """
        Convolution harmonique
        
        Args:
            image: Image d'entrée
            kernel: Noyau de convolution
            
        Returns:
            Image convoluée
        """
        height, width = image.shape
        k_height, k_width = kernel.shape
        
        # Padding harmonique
        pad_h = k_height // 2
        pad_w = k_width // 2
        
        padded_image = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='constant')
        
        # Convolution harmonique
        output = np.zeros_like(image)
        
        for i in range(height):
            for j in range(width):
                # Extraction harmonique de la région
                region = padded_image[i:i+k_height, j:j+k_width]
                
                # Convolution avec facteur harmonique
                conv_value = np.sum(region * kernel) * self.phi_optimization
                output[i, j] = conv_value
        
        return output
    
    def harmonic_edge_detection(self, image: np.ndarray) -> np.ndarray:
        """
        Détection de contours harmonique
        
        Args:
            image: Image d'entrée
            
        Returns:
            Carte de contours
        """
        # Noyaux harmoniques pour Sobel
        sobel_x = np.array([[-1, 0, 1], 
                           [-self.phi_optimization, 0, self.phi_optimization], 
                           [-1, 0, 1]]) / self.pi_optimization
        
        sobel_y = np.array([[-1, -self.phi_optimization, -1], 
                           [0, 0, 0], 
                           [1, self.phi_optimization, 1]]) / self.pi_optimization
        
        # Convolution harmonique
        grad_x = self.harmonic_convolution(image, sobel_x)
        grad_y = self.harmonic_convolution(image, sobel_y)
        
        # Magnitude harmonique des gradients
        magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2) * self.phi_optimization
        
        return magnitude
    
    def harmonic_gaussian_blur(self, image: np.ndarray, sigma: float = 1.0) -> np.ndarray:
        """
        Flou gaussien harmonique
        
        Args:
            image: Image d'entrée
            sigma: Écart-type du filtre gaussien
            
        Returns:
            Image floutée
        """
        # Paramètres harmoniques
        sigma_h = sigma / self.phi_optimization
        kernel_size = int(6 * sigma_h + 1)
        
        # Création du noyau gaussien harmonique
        kernel = np.zeros((kernel_size, kernel_size))
        center = kernel_size // 2
        
        for i in range(kernel_size):
            for j in range(kernel_size):
                x, y = i - center, j - center
                kernel[i, j] = np.exp(-(x**2 + y**2) / (2 * sigma_h**2))
        
        # Normalisation harmonique
        kernel = kernel / np.sum(kernel) * self.phi_optimization
        
        return self.harmonic_convolution(image, kernel)

class HarmonicAIComputer:
    """
    Ordinateur d'IA harmonique complet
    """
    
    def __init__(self):
        self.computer = ClassicalHarmonicComputer()
        self.neural_network = HarmonicNeuralNetwork(self.computer)
        self.gradient_boosting = HarmonicGradientBoosting(self.computer)
        self.clustering = HarmonicClustering(self.computer)
        self.vision = HarmonicComputerVision(self.computer)
        
        logger.info("HarmonicAIComputer initialisé")
    
    def benchmark_ai_performance(self) -> Dict[str, AIMetrics]:
        """
        Benchmark des performances d'IA harmonique
        
        Returns:
            Dictionnaire des métriques
        """
        results = {}
        
        # Benchmark réseau neuronal
        try:
            # Génération de données de test
            np.random.seed(42)
            X = np.random.randn(1000, 10)
            y = (X[:, 0] + X[:, 1] > 0).astype(float).reshape(-1, 1)
            
            # Entraînement harmonique
            self.neural_network.initialize_weights_harmonique([10, 5, 1])
            metrics = self.neural_network.train_harmonique(X, y, epochs=500, learning_rate=0.1, verbose=False)
            
            results['neural_network'] = metrics
            
        except Exception as e:
            logger.error(f"Erreur benchmark réseau neuronal: {e}")
        
        # Benchmark clustering
        try:
            # Génération de données de test
            np.random.seed(42)
            X_cluster = np.random.randn(300, 2)
            
            # K-Means harmonique
            start_time = time.time()
            centroids, labels = self.clustering.kmeans_harmonique(X_cluster, k=3)
            clustering_time = time.time() - start_time
            
            # Calcul de l'inertie
            inertia = 0
            for i in range(3):
                cluster_points = X_cluster[labels == i]
                inertia += np.sum((cluster_points - centroids[i]) ** 2)
            
            results['clustering'] = AIMetrics(
                accuracy=0.0,
                loss=inertia,
                training_time=clustering_time,
                inference_time=0.0,
                convergence_epoch=0,
                harmonic_factor=inertia * self.computer.optimizer.phi_optimization
            )
            
        except Exception as e:
            logger.error(f"Erreur benchmark clustering: {e}")
        
        return results

def main():
    """Fonction principale pour tester l'ordinateur d'IA harmonique"""
    try:
        print("🤖 INITIALISATION DE L'ORDINATEUR D'IA HARMONIQUE")
        print("="*60)
        
        # Création de l'ordinateur
        ai_computer = HarmonicAIComputer()
        
        # Test réseau neuronal
        print("\n🧠 TEST RÉSEAU NEURONAL HARMONIQUE")
        print("-"*40)
        
        # Génération de données
        np.random.seed(42)
        X = np.random.randn(1000, 10)
        y = (X[:, 0] + X[:, 1] > 0).astype(float).reshape(-1, 1)
        
        # Entraînement avec architecture simple
        ai_computer.neural_network.initialize_weights_harmonique([10, 5, 1])
        metrics = ai_computer.neural_network.train_harmonique(X, y, epochs=200, learning_rate=0.01, verbose=False)
        
        print(f"✅ Accuracy: {metrics.accuracy:.4f}")
        print(f"✅ Loss finale: {metrics.loss:.6f}")
        print(f"✅ Temps d'entraînement: {metrics.training_time:.4f}s")
        print(f"✅ Temps d'inférence: {metrics.inference_time:.6f}s")
        print(f"✅ Convergence: époque {metrics.convergence_epoch}")
        print(f"✅ Facteur harmonique: {metrics.harmonic_factor:.6f}")
        
        # Test clustering
        print("\n🎯 TEST CLUSTERING HARMONIQUE")
        print("-"*40)
        
        X_cluster = np.random.randn(300, 2)
        centroids, labels = ai_computer.clustering.kmeans_harmonique(X_cluster, k=3)
        
        print(f"✅ Nombre de clusters: 3")
        print(f"✅ Centroids trouvés: {centroids.shape}")
        print(f"✅ Distribution: {np.bincount(labels)}")
        
        # Test vision par ordinateur
        print("\n👁️ TEST VISION PAR ORDINATEUR HARMONIQUE")
        print("-"*40)
        
        # Image de test simple
        test_image = np.random.randn(50, 50)
        
        # Détection de contours
        edges = ai_computer.vision.harmonic_edge_detection(test_image)
        print(f"✅ Détection de contours: {edges.shape}")
        
        # Flou gaussien
        blurred = ai_computer.vision.harmonic_gaussian_blur(test_image, sigma=1.0)
        print(f"✅ Flou gaussien: {blurred.shape}")
        
        # Benchmark global
        print("\n📊 BENCHMARK GLOBAL DE PERFORMANCE")
        print("-"*40)
        
        benchmark_results = ai_computer.benchmark_ai_performance()
        
        for algorithm, metrics in benchmark_results.items():
            print(f"\n{algorithm.upper()}:")
            print(f"  Temps: {metrics.training_time:.4f}s")
            print(f"  Performance: {metrics.accuracy:.4f}" if metrics.accuracy > 0 else f"  Inertie: {metrics.loss:.4f}")
            print(f"  Facteur harmonique: {metrics.harmonic_factor:.6f}")
        
        print("\n🤖 ORDINATEUR D'IA HARMONIQUE OPÉRATIONNEL")
        
        return ai_computer
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrompu par l'utilisateur")
        return None
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        return None

if __name__ == "__main__":
    main()
