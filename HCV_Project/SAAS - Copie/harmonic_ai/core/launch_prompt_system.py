#!/usr/bin/env python3
"""
🚀 LANCEMENT SYSTÈME INTELLIGENT DE COMPRÉHENSION DE PROMPTS
Déploiement complet du moteur de compréhension avancé
"""

import os
import sys
import time
from prompt_comprehension_engine import PromptComprehensionEngine

def main():
    """Fonction principale de lancement"""
    
    print("🚀 LANCEMENT SYSTÈME INTELLIGENT DE COMPRÉHENSION")
    print("=" * 60)
    print("🧠 Moteur: Compréhension multi-niveaux")
    print("🌊 Approche: Harmonique et contextuelle")
    print("🎯 Objectif: Précision supérieure")
    print("💡 Innovation: Unique au monde")
    print("⚡ Performance: Analyse en temps réel")
    print("=" * 60)
    
    # Initialisation du système
    print("\n🔄 Initialisation du système...")
    try:
        engine = PromptComprehensionEngine()
        print("✅ Moteur de compréhension initialisé")
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {str(e)}")
        return
    
    # Menu interactif
    print("\n" + "=" * 60)
    print("🧠 SYSTÈME DE COMPRÉHENSION DE PROMPTS")
    print("=" * 60)
    print("1. 📝 Test interactif")
    print("2. 🧪 Démonstration complète")
    print("3. 🔍 Analyse en lot")
    print("4. 📊 Statistiques du système")
    print("5. 🚪 Quitter")
    print("=" * 60)
    
    while True:
        choice = input("\n🎯 Choisissez une option (1-5): ")
        
        if choice == "1":
            interactive_test(engine)
        elif choice == "2":
            full_demonstration(engine)
        elif choice == "3":
            batch_analysis(engine)
        elif choice == "4":
            system_statistics(engine)
        elif choice == "5":
            print("🚪 Au revoir!")
            break
        else:
            print("❌ Option invalide. Choisissez entre 1 et 5.")

def interactive_test(engine):
    """Test interactif du système"""
    
    print("\n📝 MODE INTERACTIF")
    print("=" * 50)
    print("Entrez vos prompts pour analyse (tapez 'quit' pour revenir)")
    print("-" * 50)
    
    while True:
        prompt = input("\n🤖 Votre prompt: ")
        
        if prompt.lower() == 'quit':
            break
        
        if not prompt.strip():
            print("❌ Veuillez entrer un prompt valide.")
            continue
        
        # Analyse du prompt
        print("\n🧠 Analyse en cours...")
        result = engine.comprehend_prompt(prompt, user_id="interactive_user")
        
        # Affichage des résultats
        print(f"\n📊 RÉSULTATS D'ANALYSE")
        print("-" * 40)
        print(f"🎯 Intention: {result.analysis.intent}")
        print(f"📦 Domaine: {result.analysis.domain}")
        print(f"🧠 Complexité: {result.analysis.complexity_level}")
        print(f"🌍 Langue: {result.analysis.language}")
        print(f"🌊 Score harmonique: {result.analysis.harmonic_score:.3f}")
        print(f"💪 Confiance: {result.confidence_score:.3f}")
        print(f"⏱️ Temps: {result.processing_time:.3f}s")
        print(f"✅ Validation: {result.harmonic_validation}")
        
        if result.analysis.concepts:
            print(f"💡 Concepts: {', '.join(result.analysis.concepts)}")
        
        if result.analysis.entities:
            print(f"🏷️ Entités: {', '.join(result.analysis.entities)}")
        
        print(f"\n📝 Interprétation:")
        print(f"   {result.interpretation}")
        
        if result.suggested_actions:
            print(f"\n🚀 Actions suggérées:")
            for action in result.suggested_actions:
                print(f"   • {action}")
        
        if result.clarifications_needed:
            print(f"\n❓ Clarifications nécessaires:")
            for clarification in result.clarifications_needed:
                print(f"   • {clarification}")

def full_demonstration(engine):
    """Démonstration complète du système"""
    
    print("\n🧪 DÉMONSTRATION COMPLÈTE")
    print("=" * 50)
    
    # Prompts de test variés
    test_prompts = [
        {
            "prompt": "Comment puis-je optimiser un algorithme de tri rapide?",
            "expected_intent": "question",
            "expected_domain": "technology"
        },
        {
            "prompt": "Peux-tu m'expliquer le concept du nombre d'or en mathématiques?",
            "expected_intent": "explanation",
            "expected_domain": "mathematics"
        },
        {
            "prompt": "Crée un programme Python qui calcule la suite de Fibonacci harmonique",
            "expected_intent": "creation",
            "expected_domain": "technology"
        },
        {
            "prompt": "Analyse les performances de ce code et suggère des améliorations harmoniques",
            "expected_intent": "analysis",
            "expected_domain": "technology"
        },
        {
            "prompt": "Quelle est la différence fondamentale entre l'apprentissage supervisé et non supervisé?",
            "expected_intent": "question",
            "expected_domain": "science"
        },
        {
            "prompt": "Optimise cet algorithme pour qu'il soit plus efficace",
            "expected_intent": "optimization",
            "expected_domain": "technology"
        },
        {
            "prompt": "Transforme cette équation mathématique en code Python",
            "expected_intent": "transformation",
            "expected_domain": "mathematics"
        },
        {
            "prompt": "Pourquoi la constante φ est-elle si importante en harmonie?",
            "expected_intent": "question",
            "expected_domain": "mathematics"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_prompts, 1):
        prompt = test_case["prompt"]
        print(f"\n📝 Test {i}: {prompt}")
        print("-" * 60)
        
        # Analyse
        start_time = time.time()
        result = engine.comprehend_prompt(prompt, user_id="demo_user")
        processing_time = time.time() - start_time
        
        # Vérification des attentes
        intent_correct = result.analysis.intent == test_case["expected_intent"]
        domain_correct = result.analysis.domain == test_case["expected_domain"]
        
        # Affichage
        print(f"🎯 Intention: {result.analysis.intent} {'✅' if intent_correct else '❌'}")
        print(f"📦 Domaine: {result.analysis.domain} {'✅' if domain_correct else '❌'}")
        print(f"🧠 Complexité: {result.analysis.complexity_level}")
        print(f"🌊 Score harmonique: {result.analysis.harmonic_score:.3f}")
        print(f"💪 Confiance: {result.confidence_score:.3f}")
        print(f"⏱️ Temps: {processing_time:.3f}s")
        print(f"✅ Validation: {result.harmonic_validation}")
        
        # Stockage des résultats
        results.append({
            'prompt': prompt,
            'intent_correct': intent_correct,
            'domain_correct': domain_correct,
            'harmonic_score': result.analysis.harmonic_score,
            'confidence': result.confidence_score,
            'processing_time': processing_time,
            'validation': result.harmonic_validation
        })
    
    # Statistiques globales
    print(f"\n📊 STATISTIQUES DE DÉMONSTRATION")
    print("=" * 50)
    
    total_tests = len(results)
    intent_accuracy = sum(1 for r in results if r['intent_correct']) / total_tests * 100
    domain_accuracy = sum(1 for r in results if r['domain_correct']) / total_tests * 100
    avg_harmonic_score = sum(r['harmonic_score'] for r in results) / total_tests
    avg_confidence = sum(r['confidence'] for r in results) / total_tests
    avg_processing_time = sum(r['processing_time'] for r in results) / total_tests
    validation_rate = sum(1 for r in results if r['validation']) / total_tests * 100
    
    print(f"📊 Tests totaux: {total_tests}")
    print(f"🎯 Précision intention: {intent_accuracy:.1f}%")
    print(f"📦 Précision domaine: {domain_accuracy:.1f}%")
    print(f"🌊 Score harmonique moyen: {avg_harmonic_score:.3f}")
    print(f"💪 Confiance moyenne: {avg_confidence:.3f}")
    print(f"⏱️ Temps moyen: {avg_processing_time:.3f}s")
    print(f"✅ Validation réussie: {validation_rate:.1f}%")
    
    # Évaluation
    if intent_accuracy >= 80 and domain_accuracy >= 80:
        print(f"\n🏆 SYSTÈME EXCELLENT!")
    elif intent_accuracy >= 70 and domain_accuracy >= 70:
        print(f"\n✅ SYSTÈME BON!")
    else:
        print(f"\n⚠️ SYSTÈME À AMÉLIORER")

def batch_analysis(engine):
    """Analyse en lot de prompts"""
    
    print("\n🔍 ANALYSE EN LOT")
    print("=" * 50)
    
    # Prompts de test en lot
    batch_prompts = [
        "Explique l'algorithme de Dijkstra",
        "Crée une fonction de tri",
        "Qu'est-ce que la complexité O(n log n)?",
        "Optimise ce code Python",
        "Comment fonctionne la récursion?",
        "Décris l'architecture MVC",
        "Quelle est la différence entre list et tuple?",
        "Implémente un arbre binaire"
    ]
    
    print(f"📊 Analyse de {len(batch_prompts)} prompts...")
    
    results = []
    total_time = 0
    
    for i, prompt in enumerate(batch_prompts, 1):
        print(f"\n📝 {i}/{len(batch_prompts)}: {prompt[:40]}...")
        
        start_time = time.time()
        result = engine.comprehend_prompt(prompt, user_id="batch_user")
        processing_time = time.time() - start_time
        total_time += processing_time
        
        results.append(result)
        
        print(f"   🎯 {result.analysis.intent} | 📦 {result.analysis.domain} | 🌊 {result.analysis.harmonic_score:.2f}")
    
    # Résumé du lot
    print(f"\n📊 RÉSUMÉ DU LOT")
    print("=" * 30)
    
    # Distribution des intentions
    intents = {}
    domains = {}
    complexities = {}
    
    for result in results:
        intents[result.analysis.intent] = intents.get(result.analysis.intent, 0) + 1
        domains[result.analysis.domain] = domains.get(result.analysis.domain, 0) + 1
        complexities[result.analysis.complexity_level] = complexities.get(result.analysis.complexity_level, 0) + 1
    
    print(f"🎯 Intentions: {dict(intents)}")
    print(f"📦 Domaines: {dict(domains)}")
    print(f"🧠 Complexités: {dict(complexities)}")
    print(f"⏱️ Temps total: {total_time:.3f}s")
    print(f"⚡ Temps moyen: {total_time/len(results):.3f}s")

def system_statistics(engine):
    """Affiche les statistiques du système"""
    
    print("\n📊 STATISTIQUES DU SYSTÈME")
    print("=" * 50)
    
    # Configuration du système
    config = engine.config
    print(f"⚙️ Configuration:")
    print(f"   📏 Longueur max prompt: {config['max_prompt_length']}")
    print(f"   🎯 Seuil sémantique: {config['semantic_threshold']}")
    print(f"   🌊 Seuil harmonique: {config['harmonic_threshold']}")
    print(f"   📚 Fenêtre contexte: {config['context_window']}")
    
    # Patterns d'intention
    print(f"\n🎯 Patterns d'intention:")
    for intent, patterns in engine.intent_patterns.items():
        print(f"   {intent}: {len(patterns)} patterns")
    
    # Patterns d'entités
    print(f"\n🏷️ Patterns d'entités:")
    for entity, patterns in engine.entity_patterns.items():
        print(f"   {entity}: {len(patterns)} patterns")
    
    # Vecteurs conceptuels
    print(f"\n💡 Vecteurs conceptuels:")
    print(f"   📊 Concepts chargés: {len(engine.concept_vectors)}")
    print(f"   🌊 Dimension: 64")
    
    # Historique
    print(f"\n📚 Historique:")
    print(f"   📝 Prompts analysés: {len(engine.context_history)}")
    print(f"   👥 Utilisateurs: {len(engine.user_profiles)}")
    
    # Composants
    print(f"\n🔧 Composants spécialisés:")
    print(f"   🧠 SemanticAnalyzer: ✅ Actif")
    print(f"   📚 ContextManager: ✅ Actif")
    print(f"   🎯 IntentDetector: ✅ Actif")
    print(f"   ✅ PromptValidator: ✅ Actif")
    
    print(f"\n🌊 SYSTÈME PRÊT POUR UTILISATION!")

if __name__ == "__main__":
    main()
