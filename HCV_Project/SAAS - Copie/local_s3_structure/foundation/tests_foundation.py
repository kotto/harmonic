#!/usr/bin/env python3
"""
TESTS HARMONIC FOUNDATION - VALIDATION RIGOUREUSE
100% PASS OBLIGATOIRE AVANT PRODUCTION
Version: 1.0.0 - TESTS COMPLETS
"""

import unittest
import math
import numpy as np
from harmonic_foundation import (
    FOUNDATION, 
    HarmonicConstants, 
    SacredFrequency,
    HarmonicMatrix,
    HarmonicFoundation
)

class TestHarmonicFoundation(unittest.TestCase):
    """
    Tests complets de la foundation - JAMAIS MODIFIER
    Validation rigoureuse de l'immuabilité
    """
    
    def setUp(self):
        """Setup pour chaque test"""
        self.foundation = FOUNDATION
        self.constants = self.foundation.constants
        self.frequency = self.foundation.frequency
    
    def test_constants_values(self):
        """Test valeurs constantes harmoniques - CRITIQUE"""
        print("\n🧪 Test constantes harmoniques...")
        
        # Test PHI avec haute précision
        self.assertAlmostEqual(
            self.constants.PHI, 
            1.618033988749895, 
            places=15,
            msg="PHI valeur incorrecte"
        )
        
        # Test PI avec haute précision
        self.assertAlmostEqual(
            self.constants.PI, 
            3.141592653589793, 
            places=15,
            msg="PI valeur incorrecte"
        )
        
        # Test EULER avec haute précision
        self.assertAlmostEqual(
            self.constants.EULER, 
            2.718281828459045, 
            places=15,
            msg="EULER valeur incorrecte"
        )
        
        print("✅ Constantes harmoniques validées")
    
    def test_sacred_frequency(self):
        """Test fréquence sacrée - CRITIQUE"""
        print("\n🧪 Test fréquence sacrée...")
        
        # Test fréquence 432Hz
        self.assertEqual(
            self.frequency.FREQUENCY, 
            432.0, 
            msg="Fréquence sacrée incorrecte"
        )
        
        # Test correction phase π/4
        expected_phase = math.pi / 4
        self.assertAlmostEqual(
            self.frequency.PHASE_CORRECTION, 
            expected_phase, 
            places=15,
            msg="Correction phase incorrecte"
        )
        
        print("✅ Fréquence sacrée validée")
    
    def test_resonance_matrix(self):
        """Test matrice de résonance - CRITIQUE"""
        print("\n🧪 Test matrice résonance...")
        
        matrix = self.foundation.resonance_matrix
        
        # Test dimensions
        self.assertEqual(
            matrix.shape, 
            (64, 64), 
            msg="Dimensions matrice incorrectes"
        )
        
        # Test bornes (sinus = [-1, 1])
        max_val = np.max(np.abs(matrix))
        self.assertLessEqual(
            max_val, 
            1.0, 
            msg="Matrice non bornée par sinus"
        )
        
        print("✅ Matrice résonance validée")
    
    def test_harmonics(self):
        """Test harmoniques fondamentales - CRITIQUE"""
        print("\n🧪 Test harmoniques fondamentales...")
        
        harmonics = self.foundation.get_harmonics()
        
        # Test nombre d'harmoniques
        self.assertEqual(
            len(harmonics), 
            5, 
            msg="Nombre d'harmoniques incorrect"
        )
        
        # Test valeurs spécifiques
        self.assertEqual(
            harmonics[0], 
            432.0, 
            msg="Harmonique fondamentale incorrecte"
        )
        
        self.assertEqual(
            harmonics[1], 
            864.0, 
            msg="Harmonique 2x incorrecte"
        )
        
        print("✅ Harmoniques fondamentales validées")
    
    def test_phase_correction(self):
        """Test correction phase - CRITIQUE"""
        print("\n🧪 Test correction phase...")
        
        # Test phase = 0
        phase_0 = 0.0
        corrected_0 = self.foundation.apply_phase_correction(phase_0)
        expected_0 = math.pi / 4
        self.assertAlmostEqual(
            corrected_0, 
            expected_0, 
            places=15,
            msg="Correction phase 0 incorrecte"
        )
        
        print("✅ Correction phase validée")
    
    def test_foundation_info(self):
        """Test informations foundation - CRITIQUE"""
        print("\n🧪 Test informations foundation...")
        
        info = self.foundation.get_foundation_info()
        
        # Test structure
        self.assertIsInstance(
            info, 
            dict, 
            msg="Info doit être dict"
        )
        
        # Test version
        self.assertEqual(
            info["version"], 
            "1.0.0", 
            msg="Version incorrecte"
        )
        
        # Test status
        self.assertEqual(
            info["status"], 
            "IMMUTABLE", 
            msg="Status incorrect"
        )
        
        print("✅ Informations foundation validées")

def run_comprehensive_validation():
    """Exécuter validation complète foundation"""
    print("🌊 VALIDATION COMPLÈTE HARMONIC FOUNDATION")
    print("=" * 80)
    print("📋 Tests: 100% couverture obligatoire")
    print("🚨 Règle: Foundation immuable après validation")
    print("=" * 80)
    
    # Créer suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestHarmonicFoundation))
    
    # Exécuter tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Résultat
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ TOUS LES TESTS PASSÉS - FOUNDATION VALIDÉE")
        print("🚀 PRÊTE POUR PRODUCTION")
        print("🌊 STATUT: IMMUABLE - NE PLUS MODIFIER")
        return True
    else:
        print("❌ TESTS ÉCHOUÉS - CORRECTIONS REQUISES")
        print(f"❌ Échecs: {len(result.failures)}")
        print(f"❌ Erreurs: {len(result.errors)}")
        return False

if __name__ == "__main__":
    success = run_comprehensive_validation()
    exit(0 if success else 1)
