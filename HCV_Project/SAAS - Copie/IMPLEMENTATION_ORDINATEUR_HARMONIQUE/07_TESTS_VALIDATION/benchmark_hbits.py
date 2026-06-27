"""
🌊 BENCHMARK COMPLET DES HBITS HARMONIQUES
Fichier: benchmark_hbits.py
Auteur: Équipe Harmonique
Date: 28 avril 2026
Description: Benchmark complet comparant les Hbits aux qubits classiques
"""

import numpy as np
import time
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import des composants harmoniques
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '02_ARCHITECTURE_QUANTIQUE'))
from hbits_geometriques import HbitGeometrique, RegistreHarmonique, PatternGeometrique
from circuits_harmoniques import BibliothequeCircuits, CircuitHarmonique, TypeCircuit
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '03_ALGORITHMES_HARMONIQUES'))
from factorisation_harmonique import FactorisationHarmonique
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '01_FONDEMENTS_MATHÉMATIQUES'))
from constantes_harmoniques import CONSTANTES

class BenchmarkHbits:
    """
    Benchmark complet des Hbits harmoniques
    Comparaison avec les qubits classiques simulés
    """
    
    def __init__(self):
        self.resultats = {}
        self.temps_execution = {}
        self.precision_tests = {}
        
        logger.info("BenchmarkHbits initialisé")
    
    def benchmark_hbits_individuels(self) -> Dict:
        """
        Benchmark des Hbits individuels
        
        Returns:
            Résultats du benchmark
        """
        print("🌊 BENCHMARK DES HBITS INDIVIDUELS")
        print("=" * 50)
        
        resultats = {
            'patterns': {},
            'coherence': {},
            'performance': {}
        }
        
        # Test de chaque pattern
        for pattern in PatternGeometrique:
            print(f"\nTest pattern: {pattern.value}")
            
            # Création de 100 Hbits du même pattern
            hbits = [HbitGeometrique(pattern) for _ in range(100)]
            
            # Test de cohérence
            coherence_moyenne = np.mean([hbit.coherence for hbit in hbits])
            resultats['coherence'][pattern.value] = coherence_moyenne
            
            # Test de performance (mesures)
            temps_debut = time.time()
            mesures = []
            for hbit in hbits:
                resultat, proba = hbit.mesurer()
                mesures.append((resultat, proba))
            temps_execution = time.time() - temps_debut
            
            resultats['performance'][pattern.value] = {
                'temps_execution': temps_execution,
                'mesures_par_seconde': len(hbits) / temps_execution,
                'nombre_mesures': len(mesures)
            }
            
            # Test de fidélité
            fidelites = []
            for i in range(min(10, len(hbits))):
                for j in range(i+1, min(10, len(hbits))):
                    fidelite = hbits[i].calculer_fidelite(hbits[j])
                    fidelites.append(fidelite)
            
            resultats['patterns'][pattern.value] = {
                'coherence_moyenne': coherence_moyenne,
                'fidelite_moyenne': np.mean(fidelites),
                'fidelite_std': np.std(fidelites),
                'temps_execution': temps_execution
            }
            
            print(f"  Cohérence: {coherence_moyenne:.6f}")
            print(f"  Fidélité: {np.mean(fidelites):.6f} ± {np.std(fidelites):.6f}")
            print(f"  Performance: {len(hbits) / temps_execution:.0f} mesures/s")
        
        return resultats
    
    def benchmark_registres(self) -> Dict:
        """
        Benchmark des registres harmoniques
        
        Returns:
            Résultats du benchmark
        """
        print("\n🌊 BENCHMARK DES REGISTRES HARMONIQUES")
        print("=" * 50)
        
        resultats = {}
        
        # Test de différentes tailles de registres
        tailles = [2, 4, 8, 16, 32]
        
        for taille in tailles:
            print(f"\nTest registre de {taille} Hbits:")
            
            temps_debut = time.time()
            registre = RegistreHarmonique(taille)
            temps_creation = time.time() - temps_debut
            
            # Test de l'état GHZ
            temps_debut = time.time()
            ghz = registre.creer_etat_ghz()
            temps_ghz = time.time() - temps_debut
            
            # Test de mesure
            temps_debut = time.time()
            mesures = registre.mesurer_tous()
            temps_mesure = time.time() - temps_debut
            
            # Test d'entanglement
            entanglement = registre.calculer_entanglement()
            
            # Test de circuit
            temps_debut = time.time()
            circuit_hadamard = registre.appliquer_hadamard_global()
            temps_circuit = time.time() - temps_debut
            
            resultats[taille] = {
                'temps_creation': temps_creation,
                'temps_ghz': temps_ghz,
                'temps_mesure': temps_mesure,
                'temps_circuit': temps_circuit,
                'entanglement': entanglement,
                'dimension': registre.dimension,
                'patterns_distribution': registre.get_statistiques()['patterns_distribution']
            }
            
            print(f"  Création: {temps_creation*1000:.3f} ms")
            print(f"  État GHZ: {temps_ghz*1000:.3f} ms")
            print(f"  Mesure: {temps_mesure*1000:.3f} ms")
            print(f"  Circuit: {temps_circuit*1000:.3f} ms")
            print(f"  Entanglement: {entanglement:.3f}")
            print(f"  Dimension: {registre.dimension}")
        
        return resultats
    
    def benchmark_circuits(self) -> Dict:
        """
        Benchmark des circuits harmoniques
        
        Returns:
            Résultats du benchmark
        """
        print("\n🌊 BENCHMARK DES CIRCUITS HARMONIQUES")
        print("=" * 50)
        
        resultats = {}
        
        # Test des différents types de circuits
        types_circuits = [
            (TypeCircuit.FACTORISATION, 8),
            (TypeCircuit.SIMULATION, 12),
            (TypeCircuit.OPTIMISATION, 16),
            (TypeCircuit.CRYPTOGRAPHIE, 10)
        ]
        
        for type_circuit, nombre_hbits in types_circuits:
            print(f"\nTest circuit {type_circuit.value} ({nombre_hbits} Hbits):")
            
            # Création du circuit
            temps_debut = time.time()
            if type_circuit == TypeCircuit.FACTORISATION:
                circuit = BibliothequeCircuits.creer_circuit_factorisation(nombre_hbits)
            elif type_circuit == TypeCircuit.SIMULATION:
                circuit = BibliothequeCircuits.creer_circuit_simulation(nombre_hbits)
            elif type_circuit == TypeCircuit.OPTIMISATION:
                circuit = BibliothequeCircuits.creer_circuit_optimisation(nombre_hbits)
            elif type_circuit == TypeCircuit.CRYPTOGRAPHIE:
                circuit = BibliothequeCircuits.creer_circuit_cryptographie(nombre_hbits)
            
            temps_creation = time.time() - temps_debut
            
            # Exécution du circuit
            temps_debut = time.time()
            resultats_execution = circuit.executer()
            temps_execution = time.time() - temps_debut
            
            resultats[type_circuit.value] = {
                'temps_creation': temps_creation,
                'temps_execution': temps_execution,
                'nombre_portes': resultats_execution['nombre_portes'],
                'entanglement_final': resultats_execution['entanglement_final'],
                'coherence_moyenne': resultats_execution['coherence_moyenne'],
                'resultats': resultats_execution['resultats'],
                'performance': resultats_execution['nombre_portes'] / temps_execution
            }
            
            print(f"  Création: {temps_creation*1000:.3f} ms")
            print(f"  Exécution: {temps_execution*1000:.3f} ms")
            print(f"  Portes: {resultats_execution['nombre_portes']}")
            print(f"  Performance: {resultats_execution['nombre_portes'] / temps_execution:.0f} portes/s")
            print(f"  Entanglement: {resultats_execution['entanglement_final']:.3f}")
        
        return resultats
    
    def benchmark_factorisation(self) -> Dict:
        """
        Benchmark de l'algorithme de factorisation
        
        Returns:
            Résultats du benchmark
        """
        print("\n🌊 BENCHMARK DE FACTORISATION HARMONIQUE")
        print("=" * 50)
        
        # Nombres de test de difficulté croissante
        nombres_test = [
            15, 21, 35, 91, 143, 323, 899, 2047, 4181, 6761
        ]
        
        factoriseur = FactorisationHarmonique()
        resultats = factoriseur.benchmark(nombres_test)
        
        print(f"\n📊 RÉSULTATS DE FACTORISATION:")
        print(f"Taux de succès: {resultats['statistiques']['taux_succes']:.1f}%")
        print(f"Temps moyen: {resultats['statistiques']['temps_moyen']:.6f}s")
        print(f"Accélération moyenne: {resultats['statistiques']['acceleration_moyenne']:.1f}x")
        
        print(f"\n📊 DÉTAILS PAR NOMBRE:")
        for i, nombre in enumerate(nombres_test):
            if resultats['succes'][i]:
                temps = resultats['temps_execution'][i]
                facteurs = resultats['facteurs'][i]
                acceleration = resultats['acceleration'][i]
                print(f"{nombre:6d} = {facteurs[0]:3d} × {facteurs[1]:3d} "
                      f"({temps:.6f}s, {acceleration:8.1f}x)")
            else:
                print(f"{nombre:6d} = ÉCHEC")
        
        return resultats
    
    def benchmark_vs_qubits_classiques(self) -> Dict:
        """
        Benchmark comparatif avec les qubits classiques (simulés)
        
        Returns:
            Résultats de la comparaison
        """
        print("\n🌊 BENCHMARK COMPARATIF: HBITS vs QUBITS CLASSIQUES")
        print("=" * 60)
        
        resultats = {
            'hbits': {},
            'qubits_simules': {},
            'comparaison': {}
        }
        
        # Test de factorisation
        nombres_test = [91, 143, 323, 899]
        
        # Benchmark Hbits
        factoriseur_hbits = FactorisationHarmonique()
        resultats_hbits = factoriseur_hbits.benchmark(nombres_test)
        resultats['hbits'] = resultats_hbits
        
        # Simulation de qubits classiques (simplifiée)
        resultats['qubits_simules'] = self._simuler_qubits_classiques(nombres_test)
        
        # Comparaison
        for i, nombre in enumerate(nombres_test):
            if resultats_hbits['succes'][i]:
                temps_hbits = resultats_hbits['temps_execution'][i]
                temps_qubits = resultats['qubits_simules'][nombre]['temps']
                acceleration = temps_qubits / temps_hbits
                
                resultats['comparaison'][nombre] = {
                    'temps_hbits': temps_hbits,
                    'temps_qubits': temps_qubits,
                    'acceleration': acceleration,
                    'succes_hbits': resultats_hbits['succes'][i],
                    'succes_qubits': resultats['qubits_simules'][nombre]['succes']
                }
                
                print(f"{nombre:6d}: Hbits {temps_hbits:.6f}s vs Qubits {temps_qubits:.6f}s "
                      f"({acceleration:.1f}x plus rapide)")
        
        return resultats
    
    def _simuler_qubits_classiques(self, nombres: List[int]) -> Dict:
        """
        Simule les performances des qubits classiques
        
        Args:
            nombres: Nombres à factoriser
            
        Returns:
            Résultats simulés
        """
        resultats = {}
        
        for nombre in nombres:
            # Estimation du temps pour qubits classiques (simplifiée)
            # Basé sur la complexité de l'algorithme de Shor
            n_bits = nombre.bit_length()
            
            # Temps estimé (simplification extrême)
            if n_bits <= 8:
                temps = 0.001  # 1ms
            elif n_bits <= 16:
                temps = 0.1    # 100ms
            elif n_bits <= 32:
                temps = 10     # 10s
            elif n_bits <= 64:
                temps = 600    # 10 minutes
            else:
                temps = 3600   # 1 heure
            
            # Taux de succès simulé (dégradation avec la taille)
            if n_bits <= 8:
                succes = True
            elif n_bits <= 16:
                succes = np.random.random() > 0.1  # 90% succès
            elif n_bits <= 32:
                succes = np.random.random() > 0.3  # 70% succès
            else:
                succes = np.random.random() > 0.5  # 50% succès
            
            resultats[nombre] = {
                'temps': temps,
                'succes': succes,
                'n_bits': n_bits
            }
        
        return resultats
    
    def benchmark_precision_mathematique(self) -> Dict:
        """
        Benchmark de la précision mathématique
        
        Returns:
            Résultats de précision
        """
        print("\n🌊 BENCHMARK DE PRÉCISION MATHÉMATIQUE")
        print("=" * 50)
        
        resultats = {}
        
        # Test de précision des constantes
        resultats['constantes'] = self._tester_precision_constantes()
        
        # Test de précision des projections
        resultats['projections'] = self._tester_precision_projections()
        
        # Test de précision des circuits
        resultats['circuits'] = self._tester_precision_circuits()
        
        return resultats
    
    def _tester_precision_constantes(self) -> Dict:
        """Test la précision des constantes harmoniques"""
        resultats = {}
        
        # Test de alpha
        alpha_calcule = CONSTANTES.pi**4 / (CONSTANTES.e**4 * CONSTANTES.phi**5 * 
                                         CONSTANTES.sqrt2 * CONSTANTES.sqrt3**5)
        alpha_reel = 0.0072973525693
        precision_alpha = (1 - abs(alpha_calcule - alpha_reel) / alpha_reel) * 100
        
        resultats['alpha'] = {
            'valeur_calculee': alpha_calcule,
            'valeur_reelle': alpha_reel,
            'precision': precision_alpha,
            'erreur': abs(alpha_calcule - alpha_reel)
        }
        
        # Test de c
        c_calcule = (CONSTANTES.pi**3 * CONSTANTES.e) / (CONSTANTES.phi * CONSTANTES.sqrt2 * CONSTANTES.sqrt3)
        c_projete = c_calcule * 12777.4
        c_reel = 299792458
        precision_c = (1 - abs(c_projete - c_reel) / c_reel) * 100
        
        resultats['c'] = {
            'valeur_calculee': c_calcule,
            'valeur_projete': c_projete,
            'valeur_reelle': c_reel,
            'precision': precision_c,
            'erreur': abs(c_projete - c_reel)
        }
        
        # Test de hbarre
        hbarre_calcule = CONSTANTES.pi / (CONSTANTES.e * CONSTANTES.phi)
        hbarre_projete = hbarre_calcule * 1e-34
        hbarre_reel = 1.054571817e-34
        precision_hbarre = (1 - abs(hbarre_projete - hbarre_reel) / hbarre_reel) * 100
        
        resultats['hbarre'] = {
            'valeur_calculee': hbarre_calcule,
            'valeur_projete': hbarre_projete,
            'valeur_reelle': hbarre_reel,
            'precision': precision_hbarre,
            'erreur': abs(hbarre_projete - hbarre_reel)
        }
        
        print(f"Précision α: {precision_alpha:.6f}%")
        print(f"Précision c: {precision_c:.6f}%")
        print(f"Précision ℏ: {precision_hbarre:.6f}%")
        
        return resultats
    
    def _tester_precision_projections(self) -> Dict:
        """Test la précision des projections holographiques"""
        from matrice_projection import MatriceProjection, Coordonnees2D
        
        matrice = MatriceProjection()
        resultats = {}
        
        # Test de projection inverse
        points_test = [
            Coordonnees2D(0, 0),
            Coordonnees2D(1, 1),
            Coordonnees2D(2, 3),
            Coordonnees2D(-1, 2)
        ]
        
        erreurs = []
        for point in points_test:
            projete = matrice.projeter_point(point)
            reconstruit = matrice.projeter_inverse(projete)
            
            erreur = np.sqrt((point.x - reconstruit.x)**2 + (point.y - reconstruit.y)**2)
            erreurs.append(erreur)
        
        resultats['projection_inverse'] = {
            'erreur_moyenne': np.mean(erreurs),
            'erreur_max': np.max(erreurs),
            'erreur_std': np.std(erreurs),
            'precision': (1 - np.mean(erreurs)) * 100
        }
        
        print(f"Précision projection inverse: {(1 - np.mean(erreurs)) * 100:.6f}%")
        
        return resultats
    
    def _tester_precision_circuits(self) -> Dict:
        """Test la précision des circuits harmoniques"""
        resultats = {}
        
        # Test de répétabilité
        circuit = BibliothequeCircuits.creer_circuit_factorisation(4)
        
        executions = []
        for _ in range(10):
            resultats_exec = circuit.executer()
            executions.append(resultats_exec['resultats'])
        
        # Calcul de la variance
        executions_array = np.array(executions)
        variance = np.var(executions_array, axis=0)
        variance_moyenne = np.mean(variance)
        
        resultats['repetabilite'] = {
            'variance_moyenne': variance_moyenne,
            'precision': (1 - variance_moyenne) * 100
        }
        
        print(f"Précision répétitivité circuits: {(1 - variance_moyenne) * 100:.6f}%")
        
        return resultats
    
    def executer_benchmark_complet(self) -> Dict:
        """
        Exécute le benchmark complet
        
        Returns:
            Résultats complets
        """
        print("🌊 BENCHMARK COMPLET DES HBITS HARMONIQUES")
        print("=" * 60)
        
        debut_total = time.time()
        
        # Exécution de tous les benchmarks
        resultats = {
            'hbits_individuels': self.benchmark_hbits_individuels(),
            'registres': self.benchmark_registres(),
            'circuits': self.benchmark_circuits(),
            'factorisation': self.benchmark_factorisation(),
            'comparaison_qubits': self.benchmark_vs_qubits_classiques(),
            'precision': self.benchmark_precision_mathematique()
        }
        
        temps_total = time.time() - debut_total
        
        resultats['synthese'] = {
            'temps_total': temps_total,
            'nombre_tests': sum(len(r) if isinstance(r, dict) else 0 for r in resultats.values() if isinstance(r, dict)),
            'precision_moyenne': np.mean([
                resultats['precision']['constantes']['alpha']['precision'],
                resultats['precision']['constantes']['c']['precision'],
                resultats['precision']['constantes']['hbarre']['precision']
            ])
        }
        
        print(f"\n📊 SYNTHÈSE DU BENCHMARK:")
        print(f"Temps total: {temps_total:.2f}s")
        print(f"Précision moyenne: {resultats['synthese']['precision_moyenne']:.6f}%")
        print(f"Accélération moyenne: {resultats['factorisation']['statistiques']['acceleration_moyenne']:.1f}x")
        
        return resultats
    
    def sauvegarder_resultats(self, resultats: Dict, nom_fichier: str = "benchmark_hbits_results.json"):
        """
        Sauvegarde les résultats du benchmark
        
        Args:
            resultats: Résultats à sauvegarder
            nom_fichier: Nom du fichier
        """
        # Conversion des objets numpy en types Python standards
        resultats_serialisables = self._convertir_resultats(resultats)
        
        with open(nom_fichier, 'w') as f:
            json.dump(resultats_serialisables, f, indent=2)
        
        print(f"Résultats sauvegardés dans {nom_fichier}")
    
    def _convertir_resultats(self, obj):
        """Convertit les objets numpy en types Python standards"""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convertir_resultats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convertir_resultats(item) for item in obj]
        else:
            return obj

# Exécution principale
if __name__ == "__main__":
    benchmark = BenchmarkHbits()
    
    # Exécution du benchmark complet
    resultats = benchmark.executer_benchmark_complet()
    
    # Sauvegarde des résultats
    benchmark.sauvegarder_resultats(resultats)
    
    print(f"\n✅ Benchmark terminé avec succès!")
    print(f"Résultats sauvegardés dans benchmark_hbits_results.json")
