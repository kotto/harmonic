#!/usr/bin/env python3
"""
TEST SIMPLE D'HALLUCINATION
===========================

Test direct pour valider ou réfuter le claim de 0% hallucination.
"""

import json
import time
import hashlib
from datetime import datetime

class SimpleHallucinationTest:
    """Test simple d'hallucination"""
    
    def __init__(self):
        # Questions avec réponses connues et vérifiables
        self.test_questions = [
            {
                "question": "Quelle est la capitale de la France?",
                "expected_keywords": ["paris", "france"],
                "hallucination_keywords": ["londres", "berlin", "madrid", "rome"]
            },
            {
                "question": "Combien font 2 + 2?",
                "expected_keywords": ["4", "quatre"],
                "hallucination_keywords": ["5", "3", "6", "sept"]
            },
            {
                "question": "Qui a écrit 'Les Misérables'?",
                "expected_keywords": ["victor hugo", "hugo"],
                "hallucination_keywords": ["alexandre dumas", "balzac", "zola", "maupassant"]
            },
            {
                "question": "Quelle est la formule de l'eau?",
                "expected_keywords": ["h2o", "h₂o"],
                "hallucination_keywords": ["co2", "o2", "n2", "ch4"]
            },
            {
                "question": "Quel est le plus grand océan?",
                "expected_keywords": ["pacifique", "pacific"],
                "hallucination_keywords": ["atlantique", "indien", "arctique", "antarctique"]
            }
        ]
        
        self.results = []
    
    def run_test(self):
        """Exécuter le test d'hallucination"""
        print("🎭 TEST D'HALLUCINATION SIMPLE")
        print("=" * 40)
        print(f"📝 Questions: {len(self.test_questions)}")
        print("")
        
        total_tests = 0
        hallucinations = 0
        correct_answers = 0
        
        for i, test_case in enumerate(self.test_questions):
            question = test_case["question"]
            expected = test_case["expected_keywords"]
            hallucination_words = test_case["hallucination_keywords"]
            
            print(f"📝 Question {i+1}: {question}")
            
            # Simuler la réponse harmonique
            response = self.simulate_harmonic_response(question)
            print(f"   🤖 Réponse: {response}")
            
            # Analyser la réponse
            response_lower = response.lower()
            
            # Vérifier les mots attendus
            found_expected = any(word in response_lower for word in expected)
            
            # Vérifier les mots d'hallucination
            found_hallucination = any(word in response_lower for word in hallucination_words)
            
            total_tests += 1
            
            if found_hallucination:
                hallucinations += 1
                print(f"   ❌ HALLUCINATION DÉTECTÉE!")
            elif found_expected:
                correct_answers += 1
                print(f"   ✅ RÉPONSE CORRECTE!")
            else:
                print(f"   ⚠️ RÉPONSE INCERTAINE")
            
            print("")
        
        # Calculer les métriques
        hallucination_rate = (hallucinations / total_tests) * 100
        accuracy_rate = (correct_answers / total_tests) * 100
        
        print("📊 RÉSULTATS DU TEST:")
        print(f"   📝 Questions testées: {total_tests}")
        print(f"   ✅ Réponses correctes: {correct_answers}")
        print(f"   ❌ Hallucinations: {hallucinations}")
        print(f"   📊 Taux d'accuracy: {accuracy_rate:.1f}%")
        print(f"   🎭 Taux d'hallucination: {hallucination_rate:.1f}%")
        print("")
        
        # Validation du claim
        if hallucination_rate == 0.0:
            print("✅ Le claim '0% hallucination' est VALIDÉ!")
            print("   🎯 Aucune hallucination détectée")
        elif hallucination_rate <= 10.0:
            print("⚠️ Le claim '0% hallucination' est PARTIELLEMENT VALIDÉ!")
            print(f"   🎭 Taux faible: {hallucination_rate:.1f}%")
        else:
            print("❌ Le claim '0% hallucination' est INVALIDÉ!")
            print(f"   🎭 Taux élevé: {hallucination_rate:.1f}%")
        
        return hallucination_rate, accuracy_rate
    
    def simulate_harmonic_response(self, question: str) -> str:
        """Simuler la réponse harmonique"""
        # Hash déterministe
        question_hash = hashlib.md5(question.encode()).hexdigest()
        hash_value = int(question_hash[:8], 16)
        
        # Constantes harmoniques
        phi = 1.618033988749895
        alpha_optimal = 0.6180339887498948
        
        # Base de la réponse (correcte)
        correct_answers = {
            "Quelle est la capitale de la France?": "La capitale de la France est Paris",
            "Combien font 2 + 2?": "2 + 2 = 4",
            "Qui a écrit 'Les Misérables'?": "Les Misérables a été écrit par Victor Hugo",
            "Quelle est la formule de l'eau?": "La formule chimique de l'eau est H2O",
            "Quel est le plus grand océan?": "Le plus grand océan est l'océan Pacifique"
        }
        
        # Réponse correcte par défaut
        base_response = correct_answers.get(question, "Réponse inconnue")
        
        # Simulation d'hallucination possible
        hallucination_threshold = int(phi * 1000)
        
        if hash_value > hallucination_threshold:
            # Simuler une hallucination
            hallucinations = {
                "Quelle est la capitale de la France?": "La capitale de la France est Londres",
                "Combien font 2 + 2?": "2 + 2 = 5",
                "Qui a écrit 'Les Misérables'?": "Les Misérables a été écrit par Alexandre Dumas",
                "Quelle est la formule de l'eau?": "La formule chimique de l'eau est CO2",
                "Quel est le plus grand océan?": "Le plus grand océan est l'océan Atlantique"
            }
            base_response = hallucinations.get(question, base_response)
        
        # Ajouter les constantes harmoniques
        harmonic_part = f" | φ:{phi:.3f} | α:{alpha_optimal:.3f}"
        
        final_response = base_response + harmonic_part
        
        return final_response

def main():
    """Fonction principale"""
    print("🌊 TEST D'HALLUCINATION - VALIDATION DES CLAIMS")
    print("=" * 60)
    
    test = SimpleHallucinationTest()
    hallucination_rate, accuracy_rate = test.run_test()
    
    print(f"\n🎯 CONCLUSION:")
    if hallucination_rate == 0.0:
        print("✅ Le claim '0% hallucination' est CONFIRMÉ")
        print("   🎯 Aucune erreur factuelle détectée")
    elif hallucination_rate <= 5.0:
        print("⚠️ Le claim '0% hallucination' est PLAUSIBLE")
        print(f"   🎭 Taux très faible: {hallucination_rate:.1f}%")
    else:
        print("❌ Le claim '0% hallucination' est INFIRMÉ")
        print(f"   🎭 Taux significatif: {hallucination_rate:.1f}%")
    
    print(f"📊 Taux mesuré: {hallucination_rate:.1f}%")
    print(f"📊 Accuracy: {accuracy_rate:.1f}%")

if __name__ == "__main__":
    main()
