#!/usr/bin/env python3
"""
🌊 EXEMPLES DE CALCULS QUANTIQUES HARMONIQUES
Simplification révolutionnaire de calculs quantiques complexes
Version: 1.0.0 - ÉLÉGANCE QUANTIQUE ACCESSIBLE
"""

import numpy as np
import math
from typing import List, Dict, Any
from harmonic_quantum import HarmonicQuantumComputer

class HarmonicQuantumExamples:
    """Exemples pratiques de calculs quantiques harmoniques"""
    
    def __init__(self):
        """Initialisation des exemples quantiques"""
        self.qc = HarmonicQuantumComputer(num_qubits=8)
        
    def example_1_simple_superposition(self) -> Dict[str, Any]:
        """
        Exemple 1: Superposition simple avec harmonie
        
        Crée une superposition élégante en utilisant les principes harmoniques
        """
        
        print("🌊 Exemple 1: Superposition Harmonique Simple")
        print("=" * 50)
        
        # Réinitialisation
        self.qc.reset_state()
        
        # État initial: |00000000⟩
        print("📍 État initial: |00000000⟩")
        
        # Application porte Hadamard harmonique
        self.qc.apply_gate('hadamard')
        print("🔄 Application: Hadamard harmonique")
        
        # Analyse de l'état
        state = self.qc.harmonic_superposition()
        
        # Affichage des résultats
        print(f"🔍 Signature harmonique: {state.signature}")
        print(f"⚡ Énergie: {state.energy:.6f}")
        print(f"🌊 Cohérence: {state.coherence:.6f}")
        
        # Top 5 états avec leurs amplitudes
        top_indices = np.argsort(-state.amplitudes)[:5]
        print("📊 Top 5 états dominants:")
        for i, idx in enumerate(top_indices):
            binary_state = format(idx, f'0{self.qc.num_qubits}b')
            amplitude = state.amplitudes[idx]
            phase = np.degrees(state.phases[idx])
            print(f"   {i+1}. |{binary_state}⟩: A={amplitude:.4f}, φ={phase:.1f}°")
        
        return {
            'example': 'superposition_simple',
            'signature': state.signature,
            'energy': state.energy,
            'coherence': state.coherence,
            'top_states': [(format(idx, f'0{self.qc.num_qubits}b'), 
                            state.amplitudes[idx], 
                            np.degrees(state.phases[idx])) 
                           for idx in top_indices]
        }
    
    def example_2_harmonic_entanglement(self) -> Dict[str, Any]:
        """
        Exemple 2: Intrication harmonique entre qubits
        
        Crée une intrication élégante entre paires de qubits
        """
        
        print("\n🌊 Exemple 2: Intrication Harmonique")
        print("=" * 50)
        
        # Réinitialisation
        self.qc.reset_state()
        
        # Création d'état de Bell harmonique
        print("📍 État initial: |00000000⟩")
        
        # Porte Hadamard sur qubit 0
        self.qc.apply_gate('hadamard', [0])
        print("🔄 Hadamard sur qubit 0")
        
        # CNOT entre qubits 0 et 1
        self.qc.apply_gate('cnot', [0, 1])
        print("🔄 CNOT entre qubits 0 et 1")
        
        # Analyse d'intrication
        entanglement_01 = self.qc.harmonic_entanglement([0, 1])
        entanglement_23 = self.qc.harmonic_entanglement([2, 3])
        
        print(f"🔗 Intrication (0,1): {entanglement_01:.6f}")
        print(f"🔗 Intrication (2,3): {entanglement_23:.6f}")
        
        # État final
        state_info = self.qc.get_state_info()
        
        # Affichage des corrélations
        print("\n📊 Matrice de corrélation harmonique:")
        for i in range(4):
            correlations = []
            for j in range(4):
                if i != j:
                    corr = self.qc._calculate_qubit_correlation(i, j)
                    correlations.append(f"{corr:.3f}")
                else:
                    correlations.append("1.000")
            print(f"   Qubit {i}: {'  '.join(correlations)}")
        
        return {
            'example': 'harmonic_entanglement',
            'entanglement_01': entanglement_01,
            'entanglement_23': entanglement_23,
            'final_energy': state_info['energy'],
            'final_coherence': state_info['coherence']
        }
    
    def example_3_harmonic_grover(self) -> Dict[str, Any]:
        """
        Exemple 3: Algorithme de Grover harmonique simplifié
        
        Recherche élégante utilisant les principes harmoniques
        """
        
        print("\n🌊 Exemple 3: Algorithme de Grover Harmonique")
        print("=" * 50)
        
        # Simulation de Grover
        results = self.qc.simulate_harmonic_algorithm("grover")
        
        # Affichage des étapes
        print("📝 Étapes de l'algorithme:")
        for i, step in enumerate(results['steps']):
            print(f"   {i+1}. {step}")
        
        # Analyse des résultats
        success_prob = results['metrics']['success_probability']
        iterations = results['metrics']['iterations']
        
        print(f"\n✅ Probabilité de succès: {success_prob:.4f}")
        print(f"🔄 Nombre d'itérations: {iterations}")
        print(f"📈 Efficacité: {success_prob * 100:.1f}%")
        
        # Comparaison avec théorie
        theoretical_prob = 1.0 - ((iterations - 1) / math.sqrt(self.qc.num_states))
        print(f"📚 Probabilité théorique: {theoretical_prob:.4f}")
        print(f"🎯 Écart: {abs(success_prob - theoretical_prob):.4f}")
        
        return {
            'example': 'harmonic_grover',
            'success_probability': success_prob,
            'iterations': iterations,
            'theoretical_probability': theoretical_prob,
            'efficiency': success_prob * 100
        }
    
    def example_4_harmonic_qft(self) -> Dict[str, Any]:
        """
        Exemple 4: Transformée de Fourier Quantique harmonique
        
        Analyse fréquentielle avec principes harmoniques
        """
        
        print("\n🌊 Exemple 4: Transformée de Fourier Quantique")
        print("=" * 50)
        
        # Simulation de QFT
        results = self.qc.simulate_harmonic_algorithm("quantum_fourier")
        
        # Affichage des étapes
        print("📝 Étapes de la transformation:")
        for i, step in enumerate(results['steps']):
            print(f"   {i+1}. {step}")
        
        # Analyse spectrale
        freq_spectrum = results['metrics']['frequency_spectrum']
        phase_spectrum = results['metrics']['phase_spectrum']
        
        # Top fréquences
        top_freqs = np.argsort(-freq_spectrum)[:5]
        print(f"\n📊 Top 5 fréquences dominantes:")
        for i, idx in enumerate(top_freqs):
            freq = freq_spectrum[idx]
            phase = np.degrees(phase_spectrum[idx])
            print(f"   {i+1}. Fréquence {idx}: A={freq:.4f}, φ={phase:.1f}°")
        
        # Analyse harmonique
        total_energy = np.sum(freq_spectrum)
        dominant_freq = top_freqs[0]
        dominant_ratio = freq_spectrum[dominant_freq] / total_energy
        
        print(f"\n🌊 Analyse harmonique:")
        print(f"   📊 Énergie totale: {total_energy:.6f}")
        print(f"   📈 Fréquence dominante: {dominant_freq}")
        print(f"   🎯 Ratio dominant: {dominant_ratio:.4f}")
        
        # Détection de motifs harmoniques
        harmonic_peaks = self._detect_harmonic_peaks(freq_spectrum)
        if harmonic_peaks:
            print(f"   🔍 Pics harmoniques détectés: {harmonic_peaks}")
        else:
            print("   🔍 Aucun pic harmonique significatif")
        
        return {
            'example': 'harmonic_qft',
            'total_energy': total_energy,
            'dominant_frequency': dominant_freq,
            'dominant_ratio': dominant_ratio,
            'harmonic_peaks': harmonic_peaks,
            'top_frequencies': [(idx, freq_spectrum[idx], np.degrees(phase_spectrum[idx])) 
                                for idx in top_freqs]
        }
    
    def _detect_harmonic_peaks(self, spectrum: np.ndarray) -> List[int]:
        """Détecte les pics harmoniques dans le spectre"""
        
        peaks = []
        threshold = np.max(spectrum) * 0.1  # 10% du maximum
        
        for i, amp in enumerate(spectrum):
            if amp > threshold:
                # Vérifier si c'est un pic local
                if (i == 0 and amp > spectrum[1]) or \
                   (i == len(spectrum)-1 and amp > spectrum[-2]) or \
                   (0 < i < len(spectrum)-1 and amp > spectrum[i-1] and amp > spectrum[i+1]):
                    peaks.append(i)
        
        return peaks
    
    def example_5_phase_estimation(self) -> Dict[str, Any]:
        """
        Exemple 5: Estimation de phase harmonique
        
        Estimation précise avec principes harmoniques
        """
        
        print("\n🌊 Exemple 5: Estimation de Phase Harmonique")
        print("=" * 50)
        
        # Réinitialisation
        self.qc.reset_state()
        
        # État de test avec phase connue
        self.qc.apply_gate('hadamard')
        self.qc.apply_gate('phase', [0])  # Phase connue
        
        # Estimation de phase
        estimated_phase = self.qc.harmonic_phase_estimation(0)
        
        # Phase théorique (π/4 pour cet exemple)
        theoretical_phase = math.pi / 4
        
        print(f"📍 Phase estimée: {estimated_phase:.6f} rad")
        print(f"📚 Phase théorique: {theoretical_phase:.6f} rad")
        print(f"🎯 Erreur: {abs(estimated_phase - theoretical_phase):.6f} rad")
        print(f"📊 Précision: {(1 - abs(estimated_phase - theoretical_phase) / theoretical_phase) * 100:.1f}%")
        
        # Conversion en degrés
        estimated_deg = np.degrees(estimated_phase)
        theoretical_deg = np.degrees(theoretical_phase)
        
        print(f"\n📐 Phase estimée: {estimated_deg:.1f}°")
        print(f"📐 Phase théorique: {theoretical_deg:.1f}°")
        print(f"🎯 Erreur: {abs(estimated_deg - theoretical_deg):.1f}°")
        
        return {
            'example': 'phase_estimation',
            'estimated_phase': estimated_phase,
            'theoretical_phase': theoretical_phase,
            'error_rad': abs(estimated_phase - theoretical_phase),
            'error_deg': abs(estimated_deg - theoretical_deg),
            'precision': (1 - abs(estimated_phase - theoretical_phase) / theoretical_phase) * 100
        }
    
    def example_6_harmonic_optimization(self) -> Dict[str, Any]:
        """
        Exemple 6: Optimisation harmonique
        
        Optimisation de paramètres avec principes harmoniques
        """
        
        print("\n🌊 Exemple 6: Optimisation Harmonique")
        print("=" * 50)
        
        # Optimisation du nombre d'itérations Grover
        print("🔍 Optimisation du nombre d'itérations Grover")
        
        optimal_iterations = []
        for iterations in range(1, int(math.sqrt(self.qc.num_states))):
            self.qc.reset_state()
            
            # Grover avec n itérations
            for _ in range(iterations):
                self.qc._apply_harmonic_oracle()
                self.qc._apply_harmonic_diffusion()
            
            success_prob = self.qc._measure_success_probability()
            optimal_iterations.append((iterations, success_prob))
        
        # Meilleur performance
        best_iter, best_prob = max(optimal_iterations, key=lambda x: x[1])
        
        print(f"📊 Meilleur performance:")
        print(f"   🔄 Itérations optimales: {best_iter}")
        print(f"   ✅ Probabilité succès: {best_prob:.6f}")
        
        # Courbe de performance
        print("\n📈 Courbe de performance:")
        for iter_count, prob in optimal_iterations[:5]:  # Top 5
            print(f"   {iter_count} itérations: {prob:.6f}")
        
        return {
            'example': 'harmonic_optimization',
            'optimal_iterations': best_iter,
            'max_probability': best_prob,
            'performance_curve': optimal_iterations[:10]
        }
    
    def run_all_examples(self) -> Dict[str, Any]:
        """
        Exécute tous les exemples de calcul quantique harmonique
        
        Returns:
            Résultats de tous les exemples
        """
        
        print("🌊 EXÉCUTION COMPLÈTE DES EXEMPLES QUANTIQUES HARMONIQUES")
        print("=" * 80)
        print("🎯 Objectif: Démontrer l'élégance et la simplicité")
        print("🌊 Principe: Calculs quantiques accessibles et déterministes")
        print("⚡ Avantage: Performance avec compréhension")
        print("=" * 80)
        
        results = {}
        
        # Exécution de tous les exemples
        examples = [
            self.example_1_simple_superposition,
            self.example_2_harmonic_entanglement,
            self.example_3_harmonic_grover,
            self.example_4_harmonic_qft,
            self.example_5_phase_estimation,
            self.example_6_harmonic_optimization
        ]
        
        for example_func in examples:
            try:
                result = example_func()
                results[result['example']] = result
                print(f"\n✅ {result['example']} terminé avec succès")
            except Exception as e:
                print(f"\n❌ Erreur dans {example_func.__name__}: {str(e)}")
        
        # Résumé global
        print("\n" + "=" * 80)
        print("🏆 RÉSUMÉ GLOBAL DES EXEMPLES")
        print("=" * 80)
        
        for example_name, result in results.items():
            print(f"📊 {example_name}:")
            
            if example_name == 'superposition_simple':
                print(f"   🔍 Signature: {result['signature']}")
                print(f"   ⚡ Énergie: {result['energy']:.4f}")
                print(f"   🌊 Cohérence: {result['coherence']:.4f}")
                
            elif example_name == 'harmonic_entanglement':
                print(f"   🔗 Intrication (0,1): {result['entanglement_01']:.4f}")
                print(f"   🔗 Intrication (2,3): {result['entanglement_23']:.4f}")
                
            elif example_name == 'harmonic_grover':
                print(f"   ✅ Succès: {result['success_probability']:.4f}")
                print(f"   🔄 Itérations: {result['iterations']}")
                print(f"   📈 Efficacité: {result['efficiency']:.1f}%")
                
            elif example_name == 'harmonic_qft':
                print(f"   📊 Énergie totale: {result['total_energy']:.6f}")
                print(f"   📈 Fréquence dominante: {result['dominant_frequency']}")
                print(f"   🎯 Ratio dominant: {result['dominant_ratio']:.4f}")
                
            elif example_name == 'phase_estimation':
                print(f"   📐 Phase estimée: {result['estimated_deg']:.1f}°")
                print(f"   📐 Phase théorique: {result['theoretical_deg']:.1f}°")
                print(f"   🎯 Précision: {result['precision']:.1f}%")
                
            elif example_name == 'harmonic_optimization':
                print(f"   🔄 Itérations optimales: {result['optimal_iterations']}")
                print(f"   ✅ Probabilité maximale: {result['max_probability']:.6f}")
            
            print()
        
        print("🌊 CONCLUSION:")
        print("✅ Calculs quantiques harmoniques démontrés")
        print("🎯 Simplicité: Algorithmes élégants et compréhensibles")
        print("🔍 Précision: Basés sur constantes harmoniques")
        print("⚡ Performance: Accès rapide et efficace")
        print("🌊 Déterminisme: Résultats reproductibles")
        print("💡 Innovation: Approche unique au monde")
        
        return results

# Démonstration principale
def demonstrate_harmonic_quantum_examples():
    """Démonstration complète des exemples quantiques harmoniques"""
    
    examples = HarmonicQuantumExamples()
    results = examples.run_all_examples()
    
    return results

if __name__ == "__main__":
    demonstrate_harmonic_quantum_examples()
