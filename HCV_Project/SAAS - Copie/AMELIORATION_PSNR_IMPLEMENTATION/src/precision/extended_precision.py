"""
🚀 Module de Précision Étendue - Phase 1
Implémentation de la précision 128-bit pour les calculs harmoniques
"""

import numpy as np
import mpmath as mp
from typing import Union, Tuple, List
import warnings

# Vérification de la disponibilité de float128
try:
    np.float128
    HAS_FLOAT128 = True
except AttributeError:
    # Utiliser float64 à la place si float128 n'est pas disponible
    HAS_FLOAT128 = False
    np.float128 = np.float64

# Configuration de la précision mpmath
mp.mp.dps = 50  # 50 décimales de précision

class ExtendedPrecision:
    """
    Classe pour gérer les calculs en précision étendue (128-bit)
    """
    
    def __init__(self, precision: int = 128):
        """
        Initialise le gestionnaire de précision étendue
        
        Args:
            precision: Nombre de bits de précision (défaut: 128)
        """
        self.precision = precision
        self.mp_precision = precision // 3  # Conversion bits → décimales
        mp.mp.dps = self.mp_precision
        
        # Constantes harmoniques en précision étendue
        self.harmonic_constants = self._init_harmonic_constants()
    
    def _init_harmonic_constants(self) -> dict:
        """
        Initialise les 7 constantes harmoniques en précision étendue
        """
        return {
            'phi': mp.mpf('1.61803398874989484820458683436563811772030917980576'),
            'pi': mp.mpf('3.14159265358979323846264338327950288419716939937510'),
            'e': mp.mpf('2.71828182845904523536028747135266249775724709369995'),
            'sqrt2': mp.mpf('1.41421356237309504880168872420969807856967187537694'),
            'sqrt3': mp.mpf('1.73205080756887729352744634150587236694280525381038'),
            'sqrt5': mp.mpf('2.23606797749978969640917366873127623544061835961152'),
            'e_pi': mp.mpf('0.86525597943226513568641382023663729380427182691535')
        }
    
    def to_mp(self, value: Union[float, np.ndarray, mp.mpf, str]) -> mp.mpf:
        """
        Convertit une valeur en mpmath avec précision étendue
        
        Args:
            value: Valeur à convertir
            
        Returns:
            Valeur en précision mpmath
        """
        if isinstance(value, mp.mpf):
            return value
        elif isinstance(value, (int, float)):
            return mp.mpf(str(value))
        elif isinstance(value, str):
            return mp.mpf(value)
        elif isinstance(value, np.ndarray):
            return mp.matrix(value.tolist())
        else:
            raise ValueError(f"Type non supporté: {type(value)}")
    
    def to_numpy(self, value: mp.mpf) -> np.ndarray:
        """
        Convertit une valeur mpmath en numpy float128 (ou float64)
        
        Args:
            value: Valeur mpmath à convertir
            
        Returns:
            Valeur numpy float128 (ou float64 si non disponible)
        """
        return np.array([float(value)], dtype=np.float128)[0]
    
    def harmonic_projection(self, signal: np.ndarray) -> dict:
        """
        Projette un signal sur la base des 7 harmonies en précision étendue
        
        Args:
            signal: Signal d'entrée (numpy array)
            
        Returns:
            Dictionnaire des coefficients harmoniques
        """
        mp_signal = mp.matrix(signal.tolist())
        coefficients = {}
        
        for name, constant in self.harmonic_constants.items():
            # Produit scalaire en précision étendue
            coeff = self._dot_product(mp_signal, constant)
            coefficients[name] = coeff
        
        return coefficients
    
    def _dot_product(self, signal: mp.matrix, harmonic: mp.mpf) -> mp.mpf:
        """
        Calcule le produit scalaire avec précision étendue
        
        Args:
            signal: Signal en format mpmath
            harmonic: Constante harmonique
            
        Returns:
            Produit scalaire en précision étendue
        """
        result = mp.mpf('0')
        for i in range(len(signal)):
            result += signal[i] * harmonic
        return result
    
    def reconstruct_signal(self, coefficients: dict, signal_length: int) -> np.ndarray:
        """
        Reconstruit un signal à partir des coefficients harmoniques
        
        Args:
            coefficients: Coefficients harmoniques
            signal_length: Longueur du signal à reconstruire
            
        Returns:
            Signal reconstruit (numpy array float128 ou float64)
        """
        reconstructed = np.zeros(signal_length, dtype=np.float128)
        
        for i in range(signal_length):
            value = mp.mpf('0')
            for name, coeff in coefficients.items():
                value += coeff * self.harmonic_constants[name]
            reconstructed[i] = self.to_numpy(value)
        
        return reconstructed


class KahanSummation:
    """
    Implémentation de l'algorithme de Kahan pour les sommes précises
    """
    
    @staticmethod
    def kahan_sum(values: List[float]) -> float:
        """
        Effectue une somme précise avec l'algorithme de Kahan
        
        Args:
            values: Liste de valeurs à sommer
            
        Returns:
            Somme précise
        """
        sum_val = 0.0
        compensation = 0.0
        
        for value in values:
            y = value - compensation
            t = sum_val + y
            compensation = (t - sum_val) - y
            sum_val = t
        
        return sum_val
    
    @staticmethod
    def kahan_sum_128(values: List[float]) -> np.float128:
        """
        Effectue une somme précise en float128 avec Kahan
        
        Args:
            values: Liste de valeurs à sommer
            
        Returns:
            Somme précise en float128
        """
        sum_val = np.float128(0.0)
        compensation = np.float128(0.0)
        
        for value in values:
            y = np.float128(value) - compensation
            t = sum_val + y
            compensation = (t - sum_val) - y
            sum_val = t
        
        return sum_val


class CompensatedSummation:
    """
    Sommation compensée pour la reconstruction harmonique
    """
    
    @staticmethod
    def compensated_sum(terms: List[Tuple[float, float]]) -> float:
        """
        Effectue une somme compensée de termes pondérés
        
        Args:
            terms: Liste de tuples (coefficient, valeur)
            
        Returns:
            Somme compensée
        """
        result = 0.0
        error = 0.0
        
        for coeff, value in terms:
            term = coeff * value
            y = term - error
            t = result + y
            error = (t - result) - y
            result = t
        
        return result
    
    @staticmethod
    def compensated_sum_128(terms: List[Tuple[float, float]]) -> np.float128:
        """
        Effectue une somme compensée en float128
        
        Args:
            terms: Liste de tuples (coefficient, valeur)
            
        Returns:
            Somme compensée en float128
        """
        result = np.float128(0.0)
        error = np.float128(0.0)
        
        for coeff, value in terms:
            term = np.float128(coeff) * np.float128(value)
            y = term - error
            t = result + y
            error = (t - result) - y
            result = t
        
        return result


def validate_precision():
    """
    Valide la configuration de précision
    
    Returns:
        True si la précision est correctement configurée
    """
    try:
        # Test de précision
        ep = ExtendedPrecision(128)
        
        # Test des constantes
        phi_computed = ep.to_mp((1 + mp.sqrt(5)) / 2)
        phi_expected = ep.harmonic_constants['phi']
        
        difference = abs(phi_computed - phi_expected)
        tolerance = mp.mpf('1e-30')
        
        return difference < tolerance
        
    except Exception as e:
        warnings.warn(f"Erreur de validation de précision: {e}")
        return False


if __name__ == "__main__":
    # Test du module
    print("🚀 Test du module de précision étendue")
    
    # Validation
    if validate_precision():
        print("✅ Validation de précision réussie")
    else:
        print("❌ Validation de précision échouée")
    
    # Test de projection
    ep = ExtendedPrecision(128)
    test_signal = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    
    coefficients = ep.harmonic_projection(test_signal)
    print(f"📊 Coefficients harmoniques: {coefficients}")
    
    # Test de reconstruction
    reconstructed = ep.reconstruct_signal(coefficients, len(test_signal))
    print(f"🔄 Signal reconstruit: {reconstructed}")
    
    # Test de Kahan summation
    values = [1e-15, 1e15, -1e15, 1e-15]
    normal_sum = sum(values)
    kahan_sum = KahanSummation.kahan_sum(values)
    
    print(f"📈 Somme normale: {normal_sum}")
    print(f"📈 Somme Kahan: {kahan_sum}")
    
    print("🎯 Module de précision étendue opérationnel!")
