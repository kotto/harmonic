#!/usr/bin/env python3
"""
Demo Interactive - Prompt Learning System
========================================

Démonstration interactive du système d'apprentissage par prompt
avec compression harmonique et IA déterministe.

Auteur: HCV PRO Team
Date: 27 avril 2026
"""

import time
import json
import os
from datetime import datetime
from prompt_learning_system import PromptLearningSystem

class PromptLearningDemo:
    """Démonstration interactive du système"""
    
    def __init__(self):
        self.system = PromptLearningSystem("demo_harmonic_knowledge.db")
        self.demo_user_id = "demo_user"
        
        # Scénarios de démonstration
        self.demo_scenarios = [
            {
                "name": "Assistant Personnel",
                "description": "L'IA apprend vos habitudes quotidiennes",
                "prompts": [
                    "Organise ma journée de travail demain",
                    "Rappelle-moi d'appeler le client à 14h",
                    "Quels sont mes rendez-vous cette semaine ?",
                    "Prépare une liste de courses pour demain",
                    "Envoie un email à l'équipe pour la réunion"
                ]
            },
            {
                "name": "Apprentissage Contextuel",
                "description": "L'IA s'adapte au contexte et à l'heure",
                "prompts": [
                    ("Bon café ce matin", {"time": "morning", "location": "home"}),
                    ("Réunion importante cet après-midi", {"time": "afternoon", "location": "office"}),
                    ("Film ce soir ?", {"time": "evening", "location": "home"}),
                    ("Sport demain matin", {"time": "night", "location": "home"})
                ]
            },
            {
                "name": "Évolution de la Personnalisation",
                "description": "L'IA devient plus intelligente avec le temps",
                "prompts": [
                    "Aide-moi",
                    "Aide-moi pour le travail",
                    "Aide-moi à organiser mes tâches professionnelles",
                    "Aide-moi à prioriser mes projets urgents avant la réunion client"
                ]
            }
        ]
    
    def run_interactive_demo(self):
        """Démonstration interactive complète"""
        
        print("🧠 DÉMONSTRATION INTERACTIVE - IA PERSONNELLE DÉTERMINISTE")
        print("=" * 70)
        print("Basée sur la compression harmonique et l'apprentissage par prompt")
        print("=" * 70)
        
        while True:
            print("\n📋 MENU DÉMONSTRATION:")
            print("1. Assistant Personnel - Apprentissage des habitudes")
            print("2. Apprentissage Contextuel - Adaptation temps/lieu")
            print("3. Évolution Personnalisation - De simple à expert")
            print("4. Mode Libre - Testez vos propres prompts")
            print("5. Métriques d'Apprentissage")
            print("6. Performance Technique")
            print("7. Quitter")
            
            choice = input("\n🎯 Choisissez une démonstration (1-7): ").strip()
            
            if choice == "1":
                self.demo_personal_assistant()
            elif choice == "2":
                self.demo_contextual_learning()
            elif choice == "3":
                self.demo_personalization_evolution()
            elif choice == "4":
                self.demo_free_mode()
            elif choice == "5":
                self.show_learning_metrics()
            elif choice == "6":
                self.show_technical_performance()
            elif choice == "7":
                print("\n👋 Merci d'avoir testé l'IA personnelle déterministe!")
                break
            else:
                print("❌ Choix invalide. Réessayez.")
    
    def demo_personal_assistant(self):
        """Démonstration assistant personnel"""
        
        print("\n🤖 DÉMO 1: ASSISTANT PERSONNEL")
        print("=" * 50)
        print("L'IA apprend progressivement vos habitudes quotidiennes...")
        print("-" * 50)
        
        scenario = self.demo_scenarios[0]
        context = {"location": "home", "device_type": "mobile", "connectivity": "wifi"}
        user_state = {"user_id": self.demo_user_id, "success_rate": 0.8}
        
        for i, prompt in enumerate(scenario["prompts"], 1):
            print(f"\n📝 Prompt {i}: \"{prompt}\"")
            print("-" * 40)
            
            # Traitement du prompt
            result = self.system.process_user_prompt(prompt, context, user_state)
            
            if result['success']:
                print(f"✅ Réponse: {result['response']}")
                print(f"⚡ Temps: {result['processing_time']*1000:.1f}ms")
                print(f"🗜️ Compression: {result['compression_ratio']:.1f}x")
                print(f"🧠 Patterns appris: {result['learning_result']['patterns_learned']}")
                
                # Détails des métadonnées
                metadata = result['metadata']
                print(f"📊 Intent: {metadata['intent_type']} | Domaine: {metadata['domain']} | Complexité: {metadata['complexity']}")
                print(f"🎵 Harmonique: {metadata['harmonic_pattern']} | Résonance: {metadata['resonance_score']:.2f}")
            else:
                print(f"❌ Erreur: {result['error']}")
            
            input("\nAppuyez sur Entrée pour continuer...")
        
        print("\n🎉 L'IA a appris vos habitudes d'assistant personnel!")
    
    def demo_contextual_learning(self):
        """Démonstration apprentissage contextuel"""
        
        print("\n🌍 DÉMO 2: APPRENTISSAGE CONTEXTUEL")
        print("=" * 50)
        print("L'IA s'adapte au contexte temps/lieu...")
        print("-" * 50)
        
        scenario = self.demo_scenarios[1]
        user_state = {"user_id": self.demo_user_id, "success_rate": 0.9}
        
        for i, (prompt, context_info) in enumerate(scenario["prompts"], 1):
            print(f"\n📝 Prompt {i}: \"{prompt}\"")
            print(f"📍 Contexte: {context_info}")
            print("-" * 40)
            
            # Construction du contexte
            context = {
                "location": context_info["location"],
                "device_type": "mobile",
                "connectivity": "wifi",
                "time_of_day": context_info["time"]
            }
            
            # Traitement
            result = self.system.process_user_prompt(prompt, context, user_state)
            
            if result['success']:
                print(f"✅ Réponse: {result['response']}")
                print(f"⏰ Heure détectée: {result['metadata']['time_of_day']}")
                print(f"📍 Lieu détecté: {result['metadata']['location']}")
                print(f"🎯 Urgence: {result['metadata']['urgency']}")
                print(f"🧠 Ton émotionnel: {result['metadata']['emotional_tone']}")
            else:
                print(f"❌ Erreur: {result['error']}")
            
            input("\nAppuyez sur Entrée pour continuer...")
        
        print("\n🎉 L'IA a appris à s'adapter au contexte!")
    
    def demo_personalization_evolution(self):
        """Démonstration évolution de la personnalisation"""
        
        print("\n📈 DÉMO 3: ÉVOLUTION DE LA PERSONNALISATION")
        print("=" * 50)
        print("L'IA devient plus intelligente avec le temps...")
        print("-" * 50)
        
        scenario = self.demo_scenarios[2]
        context = {"location": "office", "device_type": "mobile", "connectivity": "wifi"}
        user_state = {"user_id": self.demo_user_id, "success_rate": 0.8}
        
        initial_metrics = self.system.get_learning_metrics(self.demo_user_id)
        initial_patterns = initial_metrics.get('total_patterns_learned', 0)
        
        for i, prompt in enumerate(scenario["prompts"], 1):
            print(f"\n📝 Étape {i}: \"{prompt}\"")
            print(f"🧠 Complexité: {'Simple' if i <= 2 else 'Élevée'}")
            print("-" * 40)
            
            # Traitement
            result = self.system.process_user_prompt(prompt, context, user_state)
            
            if result['success']:
                print(f"✅ Réponse: {result['response']}")
                print(f"🎯 Complexité détectée: {result['metadata']['complexity']}")
                print(f"📊 Longueur de réponse prédite: {result['metadata'].get('response_length', 'N/A')}")
                
                # Métriques d'évolution
                current_metrics = self.system.get_learning_metrics(self.demo_user_id)
                patterns_learned = current_metrics.get('total_patterns_learned', 0)
                
                if patterns_learned > initial_patterns:
                    print(f"🚀 Nouveaux patterns appris: {patterns_learned - initial_patterns}")
                    initial_patterns = patterns_learned
            else:
                print(f"❌ Erreur: {result['error']}")
            
            input("\nAppuyez sur Entrée pour continuer...")
        
        print("\n🎉 L'IA a évolué de simple à expert!")
    
    def demo_free_mode(self):
        """Mode libre pour tester des prompts personnalisés"""
        
        print("\n🎮 DÉMO 4: MODE LIBRE")
        print("=" * 50)
        print("Testez vos propres prompts avec l'IA personnelle...")
        print("-" * 50)
        
        context = {
            "location": "demo",
            "device_type": "mobile", 
            "connectivity": "wifi",
            "battery_level": 0.8
        }
        user_state = {"user_id": self.demo_user_id, "success_rate": 0.85}
        
        while True:
            prompt = input("\n💬 Entrez votre prompt (ou 'retour' pour revenir au menu): ").strip()
            
            if prompt.lower() == 'retour':
                break
            
            if not prompt:
                print("❌ Veuillez entrer un prompt valide.")
                continue
            
            print("\n🔄 Traitement en cours...")
            
            # Traitement
            result = self.system.process_user_prompt(prompt, context, user_state)
            
            if result['success']:
                print(f"\n✅ Réponse: {result['response']}")
                print(f"⚡ Performance: {result['processing_time']*1000:.1f}ms")
                print(f"🗜️ Compression: {result['compression_ratio']:.1f}x")
                
                # Analyse détaillée
                metadata = result['metadata']
                print(f"\n📊 ANALYSE DÉTAILLÉE:")
                print(f"   • Intent: {metadata['intent_type']}")
                print(f"   • Domaine: {metadata['domain']}")
                print(f"   • Complexité: {metadata['complexity']}")
                print(f"   • Urgence: {metadata['urgency']}")
                print(f"   • Ton: {metadata['emotional_tone']}")
                print(f"   • Pattern: {metadata['pattern_match']}")
                print(f"   • Harmonique: {metadata['harmonic_pattern']}")
                print(f"   • Résonance: {metadata['resonance_score']:.2f}")
            else:
                print(f"❌ Erreur: {result['error']}")
    
    def show_learning_metrics(self):
        """Affiche les métriques d'apprentissage"""
        
        print("\n📊 MÉTRIQUES D'APPRENTISSAGE")
        print("=" * 50)
        
        metrics = self.system.get_learning_metrics(self.demo_user_id)
        
        if metrics:
            print(f"📈 Statistiques d'apprentissage:")
            print(f"   • Prompts traités: {metrics.get('total_prompts_processed', 0)}")
            print(f"   • Taux de succès: {metrics.get('success_rate', 0):.1%}")
            print(f"   • Temps moyen: {metrics.get('avg_response_time', 0)*1000:.1f}ms")
            print(f"   • Patterns appris: {metrics.get('total_patterns_learned', 0)}")
            print(f"   • Prompts stockés: {metrics.get('total_prompts_stored', 0)}")
            print(f"   • Efficacité: {metrics.get('learning_efficiency', 0):.2f}")
            
            if metrics.get('last_updated'):
                last_update = datetime.fromtimestamp(metrics['last_updated'])
                print(f"   • Dernière mise à jour: {last_update.strftime('%H:%M:%S')}")
        else:
            print("❌ Aucune métrique disponible. Commencez par traiter quelques prompts!")
        
        print("\n💡 Interprétation:")
        if metrics.get('total_patterns_learned', 0) > 5:
            print("🎉 L'IA a bien appris vos habitudes!")
        elif metrics.get('total_patterns_learned', 0) > 0:
            print("📚 L'IA commence à apprendre vos préférences.")
        else:
            print("🔰 L'IA est prête à apprendre de vos interactions.")
    
    def show_technical_performance(self):
        """Affiche les performances techniques"""
        
        print("\n⚡ PERFORMANCE TECHNIQUE")
        print("=" * 50)
        
        # Test de performance
        test_prompts = [
            "Test rapide",
            "Test de performance avec un texte un peu plus long",
            "Test complexe pour vérifier la robustesse du système avec beaucoup de détails"
        ]
        
        context = {"location": "performance_test", "device_type": "mobile"}
        user_state = {"user_id": "perf_test"}
        
        print("🧪 Tests de performance en cours...")
        
        total_time = 0
        total_compression = 0
        successful_tests = 0
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n📝 Test {i}: {len(prompt)} caractères")
            
            start_time = time.time()
            result = self.system.process_user_prompt(prompt, context, user_state)
            test_time = time.time() - start_time
            
            if result['success']:
                print(f"✅ Succès: {result['processing_time']*1000:.1f}ms")
                print(f"🗜️ Compression: {result['compression_ratio']:.1f}x")
                print(f"🧠 Patterns: {result['learning_result']['patterns_learned']}")
                
                total_time += result['processing_time']
                total_compression += result['compression_ratio']
                successful_tests += 1
            else:
                print(f"❌ Échec: {result['error']}")
        
        if successful_tests > 0:
            avg_time = (total_time / successful_tests) * 1000
            avg_compression = total_compression / successful_tests
            
            print(f"\n📊 RÉSULTATS TECHNIQUES:")
            print(f"   • Tests réussis: {successful_tests}/{len(test_prompts)}")
            print(f"   • Temps moyen: {avg_time:.1f}ms")
            print(f"   • Compression moyenne: {avg_compression:.1f}x")
            print(f"   • Performance: {'🚀 Excellente' if avg_time < 50 else '⚡ Bonne' if avg_time < 100 else '🐌 Améliorable'}")
            
            print(f"\n🎯 OBJECTIFS VS RÉALITÉ:")
            print(f"   • Objectif temps: <50ms {'✅' if avg_time < 50 else '❌'}")
            print(f"   • Objectif compression: >10x {'✅' if avg_compression > 10 else '❌'}")
            print(f"   • Objectif succès: 100% {'✅' if successful_tests == len(test_prompts) else '❌'}")
        
        print("\n💡 Architecture technique:")
        print("   • Compression harmonique O(N log N)")
        print("   • Déterminisme mathématique")
        print("   • Base de connaissance locale")
        print("   • Apprentissage continu")
    
    def cleanup(self):
        """Nettoyage des fichiers de démo"""
        try:
            if os.path.exists("demo_harmonic_knowledge.db"):
                os.remove("demo_harmonic_knowledge.db")
                print("🧹 Fichiers de démo nettoyés")
        except Exception as e:
            print(f"⚠️ Erreur nettoyage: {e}")

def main():
    """Point d'entrée principal de la démo"""
    
    demo = PromptLearningDemo()
    
    try:
        demo.run_interactive_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
    finally:
        demo.cleanup()

if __name__ == "__main__":
    main()
