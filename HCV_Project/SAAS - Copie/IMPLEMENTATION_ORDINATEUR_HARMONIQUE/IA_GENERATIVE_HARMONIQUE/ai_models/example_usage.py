"""
🚀 GEMMA 4 HARMONIC INTEGRATION - EXEMPLES D'UTILISATION
Fichier: example_usage.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Exemples pratiques d'utilisation de Gemma 4 Harmonique
"""

import torch
import time
import json
from pathlib import Path

# Import des modules
from gemma4_harmonic_integration import (
    Gemma4HarmonicConfig,
    Gemma4HarmonicModel,
    Gemma4HarmonicCodeGenerator
)

# Constantes harmoniques
PHI = 1.618033988749895
PI = 3.141592653589793
E = 2.718281828459045
SQRT2 = 1.414213562373095
SQRT3 = 1.732050807568877

def example_basic_generation():
    """Exemple 1: Génération de base"""
    print("🚀 Exemple 1: Génération de base")
    print("-" * 50)
    
    # Configuration
    config = Gemma4HarmonicConfig(
        model_name="google/gemma-4-7b-it",
        device="cuda" if torch.cuda.is_available() else "cpu",
        harmonic_optimization=True,
        max_length=512
    )
    
    try:
        # Initialisation
        model = Gemma4HarmonicModel(config)
        
        # Génération
        prompt = "🌊 Écris une fonction Python qui calcule le ratio d'or"
        print(f"💭 Prompt: {prompt}")
        
        start_time = time.time()
        result = model.generate_harmonic(prompt, max_new_tokens=200)
        generation_time = time.time() - start_time
        
        print(f"✅ Résultat généré en {generation_time:.2f}s:")
        print(f"📝 {result}")
        print(f"📊 Score harmonique: {model._calculate_harmonic_score(model.generate_harmonic(prompt, max_new_tokens=50)):.3f}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("💡 Assurez-vous d'avoir installé les dépendances: pip install transformers torch")

def example_code_generation():
    """Exemple 2: Génération de code"""
    print("\n🚀 Exemple 2: Génération de code")
    print("-" * 50)
    
    # Configuration
    config = Gemma4HarmonicConfig(
        model_name="google/gemma-4-7b-it",
        device="cuda" if torch.cuda.is_available() else "cpu",
        harmonic_optimization=True,
        max_length=1024
    )
    
    try:
        # Générateur de code
        code_generator = Gemma4HarmonicCodeGenerator(config)
        
        # Génération TypeScript
        print("📝 Génération TypeScript:")
        ts_code = code_generator.generate_code(
            language='typescript',
            entity_type='controller',
            entity_name='ProductController',
            requirements='API REST pour la gestion des produits avec CRUD complet'
        )
        print(ts_code)
        
        print("\n📝 Génération Python:")
        py_code = code_generator.generate_code(
            language='python',
            entity_type='service',
            entity_name='CalculationService',
            requirements='Service de calcul avec optimisation harmonique'
        )
        print(py_code)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def example_full_application():
    """Exemple 3: Génération d'application complète"""
    print("\n🚀 Exemple 3: Génération d'application complète")
    print("-" * 50)
    
    # Configuration
    config = Gemma4HarmonicConfig(
        model_name="google/gemma-4-7b-it",
        device="cuda" if torch.cuda.is_available() else "cpu",
        harmonic_optimization=True,
        max_length=2048
    )
    
    try:
        # Générateur de code
        code_generator = Gemma4HarmonicCodeGenerator(config)
        
        # Requirements pour une application e-commerce
        app_requirements = {
            'controllers': [
                {
                    'name': 'ProductController',
                    'requirements': 'Gestion des produits avec recherche, filtrage et pagination'
                },
                {
                    'name': 'UserController',
                    'requirements': 'Gestion des utilisateurs avec authentification et profils'
                },
                {
                    'name': 'OrderController',
                    'requirements': 'Gestion des commandes avec calcul des totaux et taxes'
                }
            ],
            'services': [
                {
                    'name': 'ProductService',
                    'requirements': 'Logique métier pour les produits avec gestion des stocks'
                },
                {
                    'name': 'UserService',
                    'requirements': 'Logique métier pour les utilisateurs avec validation'
                },
                {
                    'name': 'OrderService',
                    'requirements': 'Logique métier pour les commandes avec intégration paiement'
                }
            ]
        }
        
        # Génération
        print("🏗️ Génération de l'application e-commerce...")
        generated_files = code_generator.generate_full_application(app_requirements)
        
        # Affichage des résultats
        print(f"✅ Application générée: {len(generated_files)} fichiers")
        for filename, content in generated_files.items():
            print(f"   📁 {filename}: {len(content)} caractères")
        
        # Sauvegarde des fichiers
        output_dir = Path("./generated_app")
        output_dir.mkdir(exist_ok=True)
        
        for filename, content in generated_files.items():
            file_path = output_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"💾 Fichiers sauvegardés dans: {output_dir}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def example_fine_tuning():
    """Exemple 4: Fine-tuning harmonique"""
    print("\n🚀 Exemple 4: Fine-tuning harmonique")
    print("-" * 50)
    
    # Configuration
    config = Gemma4HarmonicConfig(
        model_name="google/gemma-4-7b-it",
        device="cuda" if torch.cuda.is_available() else "cpu",
        harmonic_optimization=True,
        max_length=512
    )
    
    try:
        # Dataset d'exemple pour le fine-tuning
        dataset = [
            {
                'input': 'Crée une fonction Python pour calculer le ratio d\'or',
                'target': '''
def calculate_golden_ratio():
    """Calcule le ratio d'or harmonique"""
    phi = 1.618033988749895
    return phi

# Calcul harmonique
result = calculate_golden_ratio()
print(f"Ratio d'or: {result}")
                '''
            },
            {
                'input': 'Génère un controller TypeScript pour les utilisateurs',
                'target': '''
// Controller harmonique pour les utilisateurs
import { Controller, Get, Post, Put, Delete } from '@nestjs/common';

@Controller('users')
export class UserController {
    @Get()
    async findAll() {
        return [];
    }
    
    @Post()
    async create() {
        return {};
    }
}
                '''
            }
        ]
        
        # Initialisation du modèle
        model = Gemma4HarmonicModel(config)
        
        # Fine-tuning
        print("🎯 Démarrage du fine-tuning harmonique...")
        model.fine_tune_harmonic(
            dataset=dataset,
            epochs=1,  # 1 epoch pour l'exemple
            learning_rate=1e-5
        )
        
        # Test après fine-tuning
        prompt = "🌊 Crée une fonction harmonique"
        result = model.generate_harmonic(prompt, max_new_tokens=100)
        
        print(f"✅ Fine-tuning terminé")
        print(f"📝 Résultat: {result}")
        
        # Sauvegarde du modèle fine-tuné
        model.save_harmonic_model("./models/gemma4-harmonic-finetuned")
        print("💾 Modèle sauvegardé")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def example_performance_benchmark():
    """Exemple 5: Benchmark de performance"""
    print("\n🚀 Exemple 5: Benchmark de performance")
    print("-" * 50)
    
    # Configuration
    config = Gemma4HarmonicConfig(
        model_name="google/gemma-4-7b-it",
        device="cuda" if torch.cuda.is_available() else "cpu",
        harmonic_optimization=True,
        max_length=512
    )
    
    try:
        # Initialisation
        model = Gemma4HarmonicModel(config)
        
        # Prompts de test
        test_prompts = [
            "🌊 Génère une fonction Python simple",
            "🚀 Crée un controller TypeScript",
            "🧠 Écris un service Python",
            "📊 Génère une classe de données",
            "🔧 Crée un utilitaire de calcul"
        ]
        
        # Benchmark
        results = []
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"📝 Test {i}/{len(test_prompts)}: {prompt}")
            
            # Génération
            start_time = time.time()
            result = model.generate_harmonic(prompt, max_new_tokens=100)
            end_time = time.time()
            
            # Métriques
            generation_time = end_time - start_time
            tokens_generated = len(result.split())
            tokens_per_second = tokens_generated / generation_time
            
            # Score harmonique
            harmonic_score = model._calculate_harmonic_score(
                model.generate_harmonic(prompt, max_new_tokens=50)
            )
            
            results.append({
                'prompt': prompt,
                'generation_time': generation_time,
                'tokens_generated': tokens_generated,
                'tokens_per_second': tokens_per_second,
                'harmonic_score': harmonic_score
            })
            
            print(f"   ⏱️ Temps: {generation_time:.2f}s")
            print(f"   🚀 Vitesse: {tokens_per_second:.1f} tokens/s")
            print(f"   📊 Score: {harmonic_score:.3f}")
        
        # Résumé
        print("\n📊 Résumé du benchmark:")
        avg_time = sum(r['generation_time'] for r in results) / len(results)
        avg_speed = sum(r['tokens_per_second'] for r in results) / len(results)
        avg_score = sum(r['harmonic_score'] for r in results) / len(results)
        
        print(f"   ⏱️ Temps moyen: {avg_time:.2f}s")
        print(f"   🚀 Vitesse moyenne: {avg_speed:.1f} tokens/s")
        print(f"   📊 Score moyen: {avg_score:.3f}")
        
        # Sauvegarde des résultats
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("💾 Résultats sauvegardés dans benchmark_results.json")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def example_harmonic_analysis():
    """Exemple 6: Analyse harmonique"""
    print("\n🚀 Exemple 6: Analyse harmonique")
    print("-" * 50)
    
    # Configuration
    config = Gemma4HarmonicConfig(
        model_name="google/gemma-4-7b-it",
        device="cuda" if torch.cuda.is_available() else "cpu",
        harmonic_optimization=True,
        max_length=512
    )
    
    try:
        # Initialisation
        model = Gemma4HarmonicModel(config)
        
        # Test avec différentes constantes
        prompts = [
            f"🌊 Génère du code avec optimisation φ ({PHI})",
            f"📊 Génère du code avec précision π ({PI})",
            f"🚀 Génère du code avec efficacité e ({E})",
            f"🔧 Génère du code avec stabilité √2 ({SQRT2})",
            f"⚖️ Génère du code avec équilibre √3 ({SQRT3})"
        ]
        
        harmonic_scores = {}
        
        for prompt in prompts:
            print(f"💭 {prompt}")
            
            # Génération
            result = model.generate_harmonic(prompt, max_new_tokens=100)
            
            # Analyse harmonique
            score = model._calculate_harmonic_score(
                model.generate_harmonic(prompt, max_new_tokens=50)
            )
            
            # Extraction de la constante
            if "φ" in prompt or "PHI" in prompt:
                harmonic_scores['phi'] = score
            elif "π" in prompt or "PI" in prompt:
                harmonic_scores['pi'] = score
            elif "e" in prompt or "E" in prompt:
                harmonic_scores['e'] = score
            elif "√2" in prompt or "SQRT2" in prompt:
                harmonic_scores['sqrt2'] = score
            elif "√3" in prompt or "SQRT3" in prompt:
                harmonic_scores['sqrt3'] = score
            
            print(f"   📊 Score: {score:.3f}")
        
        # Analyse des résultats
        print("\n📊 Analyse harmonique:")
        for constant, score in harmonic_scores.items():
            print(f"   {constant.upper()}: {score:.3f}")
        
        # Vérification de l'optimisation
        phi_optimized = harmonic_scores.get('phi', 0) > harmonic_scores.get('pi', 0)
        pi_optimized = harmonic_scores.get('pi', 0) > harmonic_scores.get('e', 0)
        
        print(f"\n✅ Optimisation φ: {'Oui' if phi_optimized else 'Non'}")
        print(f"✅ Optimisation π: {'Oui' if pi_optimized else 'Non'}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Fonction principale avec menu interactif"""
    print("🤖 GEMMA 4 HARMONIC INTEGRATION - EXEMPLES")
    print("=" * 60)
    print("Choisissez un exemple à exécuter:")
    print("1. Génération de base")
    print("2. Génération de code")
    print("3. Génération d'application complète")
    print("4. Fine-tuning harmonique")
    print("5. Benchmark de performance")
    print("6. Analyse harmonique")
    print("7. Exécuter tous les exemples")
    print("0. Quitter")
    
    while True:
        try:
            choice = input("\n🎯 Votre choix (0-7): ").strip()
            
            if choice == "0":
                print("👋 Au revoir!")
                break
            elif choice == "1":
                example_basic_generation()
            elif choice == "2":
                example_code_generation()
            elif choice == "3":
                example_full_application()
            elif choice == "4":
                example_fine_tuning()
            elif choice == "5":
                example_performance_benchmark()
            elif choice == "6":
                example_harmonic_analysis()
            elif choice == "7":
                print("🚀 Exécution de tous les exemples...")
                example_basic_generation()
                example_code_generation()
                example_full_application()
                example_fine_tuning()
                example_performance_benchmark()
                example_harmonic_analysis()
                print("✅ Tous les exemples exécutés!")
            else:
                print("❌ Choix invalide. Réessayez.")
                
        except KeyboardInterrupt:
            print("\n👋 Interruption. Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
