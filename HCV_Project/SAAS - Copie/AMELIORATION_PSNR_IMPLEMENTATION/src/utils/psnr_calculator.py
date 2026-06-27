"""
📊 Calculateur PSNR Avancé - Phase 1
Module spécialisé pour le calcul précis du PSNR avec validation
"""

import numpy as np
from typing import Tuple, Optional, Dict
import warnings

# Import conditionnel de scipy
try:
    from scipy import signal
    from scipy.stats import entropy
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    # Créer des fonctions de remplacement
    def signal(*args, **kwargs):
        raise NotImplementedError("scipy non disponible")
    
    def entropy(*args, **kwargs):
        raise NotImplementedError("scipy non disponible")


class PSNRCalculator:
    """
    Calculateur PSNR avancé avec validation et métriques complémentaires
    """
    
    def __init__(self, max_value: Optional[float] = None):
        """
        Initialise le calculateur PSNR
        
        Args:
            max_value: Valeur maximale du signal (auto-détection si None)
        """
        self.max_value = max_value
        self.validation_stats = {}
    
    def calculate_psnr(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """
        Calcule le PSNR avec validation complète
        
        Args:
            original: Signal original
            reconstructed: Signal reconstruit
            
        Returns:
            Valeur PSNR en dB
        """
        # Validation des entrées
        self._validate_inputs(original, reconstructed)
        
        # Détection automatique du max_value si nécessaire
        if self.max_value is None:
            self.max_value = self._detect_max_value(original)
        
        # Calcul du MSE avec précision étendue
        mse = self._calculate_mse_extended(original, reconstructed)
        
        # Gestion du cas parfait
        if mse == 0:
            return float('inf')
        
        # Calcul PSNR avec formule étendue
        psnr = self._calculate_psnr_extended(mse)
        
        # Validation du résultat
        self._validate_psnr_result(psnr, mse)
        
        return psnr
    
    def _validate_inputs(self, original: np.ndarray, reconstructed: np.ndarray):
        """
        Valide les signaux d'entrée
        
        Args:
            original: Signal original
            reconstructed: Signal reconstruit
        """
        if not isinstance(original, np.ndarray) or not isinstance(reconstructed, np.ndarray):
            raise ValueError("Les signaux doivent être des numpy arrays")
        
        if original.shape != reconstructed.shape:
            raise ValueError(f"Formes incompatibles: {original.shape} vs {reconstructed.shape}")
        
        if original.size == 0:
            raise ValueError("Les signaux ne peuvent pas être vides")
        
        # Vérification des valeurs infinies ou NaN
        if np.any(np.isinf(original)) or np.any(np.isnan(original)):
            raise ValueError("Le signal original contient des valeurs infinies ou NaN")
        
        if np.any(np.isinf(reconstructed)) or np.any(np.isnan(reconstructed)):
            raise ValueError("Le signal reconstruit contient des valeurs infinies ou NaN")
    
    def _detect_max_value(self, signal: np.ndarray) -> float:
        """
        Détecte automatiquement la valeur maximale appropriée
        
        Args:
            signal: Signal d'entrée
            
        Returns:
            Valeur maximale détectée
        """
        signal_max = np.max(np.abs(signal))
        signal_min = np.min(signal)
        
        # Détection du type de signal
        if signal_min >= 0 and signal_max <= 255:
            return 255.0  # Image 8-bit
        elif signal_min >= 0 and signal_max <= 1.0:
            return 1.0  # Signal normalisé
        elif signal_min >= -1.0 and signal_max <= 1.0:
            return 1.0  # Signal centré normalisé
        else:
            return signal_max  # Utiliser le max du signal
    
    def _calculate_mse_extended(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """
        Calcule le MSE avec précision étendue
        
        Args:
            original: Signal original
            reconstructed: Signal reconstruit
            
        Returns:
            MSE calculé avec haute précision
        """
        # Conversion en float128 pour la précision
        orig = original.astype(np.float128)
        recon = reconstructed.astype(np.float128)
        
        # Calcul MSE avec compensation d'erreur
        diff = orig - recon
        squared_diff = diff * diff
        
        # Utilisation de Kahan summation pour la précision
        mse = self._kahan_summation(squared_diff) / len(squared_diff)
        
        return float(mse)
    
    def _kahan_summation(self, values: np.ndarray) -> np.float128:
        """
        Sommation de Kahan pour une précision maximale
        
        Args:
            values: Valeurs à sommer
            
        Returns:
            Somme précise
        """
        sum_val = np.float128(0.0)
        compensation = np.float128(0.0)
        
        for value in values:
            y = value - compensation
            t = sum_val + y
            compensation = (t - sum_val) - y
            sum_val = t
        
        return sum_val
    
    def _calculate_psnr_extended(self, mse: float) -> float:
        """
        Calcule le PSNR avec formule étendue
        
        Args:
            mse: Mean Squared Error
            
        Returns:
            PSNR en dB
        """
        if mse == 0:
            return float('inf')
        
        # Formule PSNR standard avec log10
        psnr = 20 * np.log10(self.max_value / np.sqrt(mse))
        
        return psnr
    
    def _validate_psnr_result(self, psnr: float, mse: float):
        """
        Valide le résultat PSNR
        
        Args:
            psnr: Valeur PSNR calculée
            mse: MSE correspondant
        """
        # Validation des bornes
        if psnr < 0:
            warnings.warn(f"PSNR négatif inhabituel: {psnr:.2f} dB")
        
        if psnr > 100 and psnr != float('inf'):
            warnings.warn(f"PSNR très élevé: {psnr:.2f} dB")
        
        # Stockage des statistiques
        self.validation_stats = {
            'psnr': psnr,
            'mse': mse,
            'max_value': self.max_value,
            'valid': True
        }
    
    def calculate_psnr_harmonic(self, original: np.ndarray, reconstructed: np.ndarray) -> Dict:
        """
        Calcule le PSNR avec métriques harmoniques spécifiques
        
        Args:
            original: Signal original
            reconstructed: Signal reconstruit
            
        Returns:
            Dictionnaire avec PSNR et métriques harmoniques
        """
        # PSNR standard
        psnr = self.calculate_psnr(original, reconstructed)
        
        # Métriques harmoniques additionnelles
        harmonic_metrics = self._calculate_harmonic_metrics(original, reconstructed)
        
        return {
            'psnr': psnr,
            'psnr_db': psnr,
            'mse': self.validation_stats.get('mse', 0),
            'max_value': self.max_value,
            'harmonic_metrics': harmonic_metrics,
            'quality_level': self._determine_quality_level(psnr)
        }
    
    def _calculate_harmonic_metrics(self, original: np.ndarray, reconstructed: np.ndarray) -> Dict:
        """
        Calcule des métriques spécifiques à l'harmonie
        
        Args:
            original: Signal original
            reconstructed: Signal reconstruit
            
        Returns:
            Métriques harmoniques
        """
        # Analyse spectrale
        orig_fft = np.fft.fft(original)
        recon_fft = np.fft.fft(reconstructed)
        
        # Erreur spectrale
        spectral_error = np.mean(np.abs(orig_fft - recon_fft))
        
        # Corrélation spectrale
        try:
            spectral_correlation = np.corrcoef(
                np.abs(orig_fft), 
                np.abs(recon_fft)
            )[0, 1]
        except:
            # En cas d'erreur, utiliser une corrélation simplifiée
            spectral_correlation = np.corrcoef(orig_fft.flatten(), recon_fft.flatten())[0, 1]
        
        # Entropie relative (implémentation simplifiée si scipy non disponible)
        try:
            orig_hist, _ = np.histogram(original, bins=256, density=True)
            recon_hist, _ = np.histogram(reconstructed, bins=256, density=True)
            
            # Éviter les zéros pour l'entropie
            orig_hist = orig_hist + 1e-10
            recon_hist = recon_hist + 1e-10
            
            if HAS_SCIPY:
                relative_entropy = entropy(orig_hist, recon_hist)
            else:
                # Implémentation simple de l'entropie relative
                relative_entropy = -np.sum(orig_hist * np.log(recon_hist / orig_hist))
        except:
            relative_entropy = 0.0
        
        return {
            'spectral_error': float(spectral_error),
            'spectral_correlation': float(spectral_correlation),
            'relative_entropy': float(relative_entropy),
            'harmonic_fidelity': float(spectral_correlation * (1 / (1 + relative_entropy)))
        }
    
    def _determine_quality_level(self, psnr: float) -> str:
        """
        Détermine le niveau de qualité basé sur le PSNR
        
        Args:
            psnr: Valeur PSNR
            
        Returns:
            Niveau de qualité
        """
        if psnr == float('inf'):
            return "Parfait"
        elif psnr >= 90:
            return "Quasi-parfait"
        elif psnr >= 80:
            return "Excellent"
        elif psnr >= 70:
            return "Très bon"
        elif psnr >= 60:
            return "Bon"
        elif psnr >= 50:
            return "Acceptable"
        elif psnr >= 40:
            "Médiocre"
        else:
            return "Pauvre"
    
    def batch_calculate_psnr(self, originals: list, reconstructed_list: list) -> list:
        """
        Calcule le PSNR pour plusieurs paires de signaux
        
        Args:
            originals: Liste des signaux originaux
            reconstructed_list: Liste des signaux reconstruits
            
        Returns:
            Liste des résultats PSNR
        """
        if len(originals) != len(reconstructed_list):
            raise ValueError("Les listes doivent avoir la même longueur")
        
        results = []
        for i, (orig, recon) in enumerate(zip(originals, reconstructed_list)):
            try:
                psnr_result = self.calculate_psnr_harmonic(orig, recon)
                psnr_result['index'] = i
                results.append(psnr_result)
            except Exception as e:
                warnings.warn(f"Erreur dans le calcul PSNR #{i}: {e}")
                results.append({
                    'index': i,
                    'psnr': np.nan,
                    'error': str(e)
                })
        
        return results
    
    def generate_psnr_report(self, results: list) -> str:
        """
        Génère un rapport détaillé des résultats PSNR
        
        Args:
            results: Liste des résultats PSNR
            
        Returns:
            Rapport formaté
        """
        if not results:
            return "Aucun résultat à rapporter"
        
        # Statistiques
        valid_results = [r for r in results if 'psnr' in r and not np.isnan(r['psnr'])]
        
        if not valid_results:
            return "Aucun résultat valide à rapporter"
        
        psnr_values = [r['psnr'] for r in valid_results]
        
        mean_psnr = np.mean(psnr_values)
        std_psnr = np.std(psnr_values)
        min_psnr = np.min(psnr_values)
        max_psnr = np.max(psnr_values)
        
        # Distribution des niveaux de qualité
        quality_levels = [r.get('quality_level', 'Inconnu') for r in valid_results]
        quality_distribution = {}
        for level in quality_levels:
            quality_distribution[level] = quality_distribution.get(level, 0) + 1
        
        # Génération du rapport
        report = f"""
📊 RAPPORT PSNR DÉTAILLÉ
{'='*50}

Statistiques générales:
- Nombre d'échantillons: {len(valid_results)}
- PSNR moyen: {mean_psnr:.2f} dB
- Écart-type PSNR: {std_psnr:.2f} dB
- PSNR minimum: {min_psnr:.2f} dB
- PSNR maximum: {max_psnr:.2f} dB

Distribution des niveaux de qualité:
"""
        
        for level, count in sorted(quality_distribution.items()):
            percentage = (count / len(valid_results)) * 100
            report += f"- {level}: {count} ({percentage:.1f}%)\n"
        
        # Métriques harmoniques moyennes
        if 'harmonic_metrics' in valid_results[0]:
            report += "\nMétriques harmoniques moyennes:\n"
            
            harmonic_keys = valid_results[0]['harmonic_metrics'].keys()
            for key in harmonic_keys:
                values = [r['harmonic_metrics'][key] for r in valid_results 
                          if 'harmonic_metrics' in r and key in r['harmonic_metrics']]
                if values:
                    mean_val = np.mean(values)
                    report += f"- {key}: {mean_val:.4f}\n"
        
        report += f"\n{'='*50}\n"
        
        return report


if __name__ == "__main__":
    # Test du calculateur PSNR
    print("📊 Test du calculateur PSNR avancé")
    
    # Initialisation
    calculator = PSNRCalculator()
    
    # Signal de test
    np.random.seed(42)
    original = np.random.randn(1000).astype(np.float64) * 100
    
    # Signal reconstruit avec erreur contrôlée
    noise_level = 1.0
    reconstructed = original + np.random.randn(1000) * noise_level
    
    print(f"📊 Signal de test: {len(original)} échantillons")
    print(f"🔊 Niveau de bruit: {noise_level}")
    
    # Calcul PSNR
    psnr_result = calculator.calculate_psnr_harmonic(original, reconstructed)
    
    print(f"📈 Résultats PSNR:")
    print(f"   PSNR: {psnr_result['psnr']:.2f} dB")
    print(f"   MSE: {psnr_result['mse']:.6f}")
    print(f"   Qualité: {psnr_result['quality_level']}")
    
    print(f"🌊 Métriques harmoniques:")
    for key, value in psnr_result['harmonic_metrics'].items():
        print(f"   {key}: {value:.4f}")
    
    # Test batch
    originals = [original] * 5
    reconstructed_list = [
        original + np.random.randn(1000) * level
        for level in [0.1, 0.5, 1.0, 2.0, 5.0]
    ]
    
    batch_results = calculator.batch_calculate_psnr(originals, reconstructed_list)
    
    print(f"\n📊 Résultats batch:")
    for result in batch_results:
        if 'psnr' in result:
            print(f"   Échantillon {result['index']}: {result['psnr']:.2f} dB ({result['quality_level']})")
    
    # Rapport détaillé
    report = calculator.generate_psnr_report(batch_results)
    print(f"\n{report}")
    
    print("🎯 Calculateur PSNR opérationnel!")
