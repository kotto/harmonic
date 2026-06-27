"""
🚀 QUICK START - IA GÉNÉRATIVE HARMONIQUE
Fichier: quick_start.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Guide de démarrage rapide pour l'IA générative harmonique
"""

import sys
import os
import numpy as np
from pathlib import Path

# Ajout du chemin du projet aux imports
sys.path.append(str(Path(__file__).parent.parent))

# Import des modules harmoniques
try:
    from harmonic_neural_network import HarmonicNeuralNetwork, ActivationType, OptimizationType
    from harmonic_code_generator import HarmonicCodeGenerator
    from harmonic_memory_system import HarmonicMemorySystem, MemoryConfig, MemoryType, MemoryPriority
    from harmonic_optimization_engine import HarmonicOptimizationEngine, OptimizationConfig, OptimizationTarget, OptimizationType as OptType
    from harmonic_user_interface import HarmonicUI, UIConfig, ThemeType, UIType
    from prompts.claude_code_prompts import ClaudeCodeHarmonicEngine
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Assurez-vous que vous êtes dans le bon répertoire ou que les modules sont installés.")
    sys.exit(1)

# Constantes harmoniques universelles
PHI = 1.618033988749895  # Ratio d'or
PI = 3.141592653589793    # Constante circulaire
E = 2.718281828459045      # Nombre d'Euler
SQRT2 = 1.414213562373095  # Racine carrée de 2
SQRT3 = 1.732050807568877  # Racine carrée de 3

def print_header():
    """Affiche l'en-tête"""
    
    print("🌊" * 60)
    print("🚀 IA GÉNÉRATIVE HARMONIQUE - QUICK START")
    print("🌊" * 60)
    print(f"φ (phi) = {PHI}")
    print(f"π (pi) = {PI}")
    print(f"e = {E}")
    print(f"√2 = {SQRT2}")
    print(f"√3 = {SQRT3}")
    print("🌊" * 60)

def example_1_neural_network():
    """
    Exemple 1: Réseau neuronal harmonique
    """
    
    print("\n🧠 Exemple 1: Réseau Neuronal Harmonique")
    print("=" * 50)
    
    # Création du réseau
    network = HarmonicNeuralNetwork(
        layers=[128, 64, 32],
        activation=ActivationType.HARMONIC_SIGMOID,
        optimization=OptimizationType.PHI_ADAM
    )
    
    # Données d'exemple
    X = np.random.randn(100, 128)
    y = np.random.randn(100, 32)
    
    # Entraînement
    print("🎯 Entraînement du réseau neuronal...")
    results = network.train_harmonic(X, y, epochs=20, learning_rate=0.01)
    
    # Affichage des résultats
    print(f"✅ Entraînement terminé:")
    print(f"   Temps: {results['training_time']:.2f}s")
    print(f"   Perte finale: {results['final_loss']:.6f}")
    print(f"   Score harmonique: {results['metrics']['harmonic_score']:.3f}")
    print(f"   Itérations: {results['training_history'][-1]['epoch']}")
    
    # Test de prédiction
    test_input = np.random.randn(5, 128)
    prediction = network.predict(test_input)
    
    print(f"🔮 Prédiction sur données de test: {prediction.shape}")
    print(f"   Exemple de prédiction: {prediction[0][:3]}")
    
    return network

def example_2_code_generation():
    """
    Exemple 2: Génération de code harmonique
    """
    
    print("\n🚀 Exemple 2: Génération de Code Harmonique")
    print("=" * 50)
    
    # Création du générateur
    generator = HarmonicCodeGenerator()
    
    # Configuration des requirements
    from harmonic_code_generator import CodeRequirements
    
    requirements = CodeRequirements(
        service_name="QuantiqueHarmonique",
        description="Service de calcul quantique harmonique",
        endpoints=[
            {
                "method": "POST",
                "path": "/factorization",
                "description": "Factorisation harmonique",
                "rateLimit": 100
            },
            {
                "method": "GET",
                "path": "/",
                "description": "Récupère tous les calculs"
            }
        ],
        database_schema={
            "table": "quantique_jobs",
            "fields": ["id", "name", "description", "result", "status"]
        },
        business_logic=[
            "Optimisation φ des calculs",
            "Précision π des résultats",
            "Efficacité e des processus"
        ],
        validation_rules=[
            "Nom requis",
            "Valeur numérique",
            "Statut valide"
        ]
    )
    
    # Génération du code
    print("🎯 Génération du code harmonique...")
    generated_files = generator.generate_full_application(requirements, "./generated/quantique")
    
    # Affichage des résultats
    print(f"✅ Code généré: {len(generated_files)} fichiers")
    
    for file_type, file_path in generated_files.items():
        print(f"   {file_type}: {file_path}")
        
        # Affichage d'un extrait du code généré
        if file_type == "controller":
            with open(file_path, 'r') as f:
                content = f.read()
                print(f"   Extrait: {content[:200]}...")
    
    return generator

def example_3_memory_system():
    """
    Exemple 3: Système de mémoire harmonique
    """
    
    print("\n🧠 Exemple 3: Système de Mémoire Harmonique")
    print("=" * 50)
    
    # Configuration de la mémoire
    config = MemoryConfig(
        max_entries=1000,
        max_working_memory=20,
        cache_size=100,
        persistence_enabled=False,  # Désactivé pour l'exemple
        sqlite_enabled=False
    )
    
    # Création du système de mémoire
    memory = HarmonicMemorySystem(config)
    
    # Stockage d'exemples
    print("💾 Stockage d'exemples harmoniques...")
    
    examples = [
        ("Calcul quantique φ-optimisé", MemoryType.PROCEDURAL, MemoryPriority.HIGH, ["quantique", "phi", "optimization"]),
        ("Précision π des calculs", MemoryType.SEMANTIC, MemoryPriority.HIGH, ["precision", "pi", "math"]),
        ("Efficacité e des processus", MemoryType.PROCEDURAL, MemoryPriority.MEDIUM, ["efficiency", "e", "process"]),
        ("Stabilité √2 du système", MemoryType.LONG_TERM, MemoryPriority.CRITICAL, ["stability", "sqrt2", "system"]),
        ("Équilibre √3 harmonique", MemoryType.EPISODIC, MemoryPriority.MEDIUM, ["balance", "sqrt3", "harmony"])
    ]
    
    entry_ids = []
    
    for content, mem_type, priority, tags in examples:
        entry_id = memory.store(
            content=content,
            memory_type=mem_type,
            priority=priority,
            tags=tags
        )
        entry_ids.append(entry_id)
    
    print(f"✅ {len(entry_ids)} entrées stockées")
    
    # Récupération et recherche
    print("\n🔍 Récupération et recherche...")
    
    # Recherche par tag
    phi_results = memory.retrieve("phi", limit=3)
    print(f"📊 Résultats pour 'phi': {len(phi_results)}")
    
    for result in phi_results:
        print(f"   {result.id}: {str(result.content)[:50]}...")
    
    # Recherche par type
    semantic_results = memory.retrieve("", MemoryType.SEMANTIC, limit=3)
    print(f"📊 Résultats sémantiques: {len(semantic_results)}")
    
    for result in semantic_results:
        print(f"   {result.id}: {str(result.content)[:50]}...")
    
    # Statistiques
    stats = memory.get_statistics()
    print(f"\n📊 Statistiques de la mémoire:")
    print(f"   Total entrées: {stats['total_entries']}")
    print(f"   Score harmonique moyen: {stats['average_harmonic_score']:.3f}")
    print(f"   Utilisation mémoire travail: {stats['working_memory_usage']:.2%}")
    print(f"   Utilisation cache: {stats['cache_usage']:.2%}")
    
    return memory

def example_4_optimization():
    """
    Exemple 4: Optimisation harmonique
    """
    
    print("\n⚡ Exemple 4: Optimisation Harmonique")
    print("=" * 50)
    
    # Configuration de l'optimisation
    config = OptimizationConfig(
        max_iterations=50,  # Réduit pour l'exemple
        population_size=10,
        parallel_workers=2,
        adaptive_learning_rate=True,
        harmonic_weighting=True
    )
    
    # Création du moteur d'optimisation
    optimizer = HarmonicOptimizationEngine(config)
    
    # Définition des cibles d'optimisation
    targets = [
        OptimizationTarget(
            name="performance_phi",
            current_value=1.0,
            target_value=PHI,  # 1.618...
            optimization_type=OptType.PHI_PERFORMANCE,
            weight=1.0
        ),
        OptimizationTarget(
            name="precision_pi",
            current_value=3.0,
            target_value=PI,  # 3.14159...
            optimization_type=OptType.PI_PRECISION,
            weight=0.8
        ),
        OptimizationTarget(
            name="efficiency_e",
            current_value=2.5,
            target_value=E,   # 2.718...
            optimization_type=OptType.E_EFFICIENCY,
            weight=0.6
        )
    ]
    
    # Optimisation
    print("🎯 Optimisation des cibles harmoniques...")
    result = optimizer.optimize_targets(targets)
    
    # Affichage des résultats
    print(f"✅ Optimisation terminée:")
    print(f"   Amélioration: {result.improvement:.2f}%")
    print(f"   Score harmonique: {result.harmonic_score:.3f}")
    print(f"   Itérations: {result.iterations}")
    print(f"   Temps: {result.optimization_time:.2f}s")
    print(f"   Convergence: {result.convergence}")
    print(f"   Stratégie: {result.strategy_used.value}")
    
    # Détails des paramètres optimisés
    print(f"\n📊 Paramètres optimisés:")
    for i, param in enumerate(result.parameters):
        print(f"   Paramètre {i+1}: {param:.6f}")
    
    return optimizer

def example_5_prompt_generation():
    """
    Exemple 5: Génération avec prompts déterministes
    """
    
    print("\n🤖 Exemple 5: Génération avec Prompts Déterministes")
    print("=" * 50)
    
    # Test du moteur Claude
    print("🧠 Test du moteur Claude Code...")
    claude_engine = ClaudeCodeHarmonicEngine()
    
    # Variables pour le prompt
    variables = {
        'language': 'typescript',
        'service_name': 'PromptTest',
        'framework': 'nestjs',
        'service_type': 'prompt',
        'performance_target': 'high',
        'precision_target': 'maximum'
    }
    
    # Exécution du prompt
    result = claude_engine.execute_claude_prompt('harmonic_code_generation', variables)
    
    # Affichage des résultats
    print(f"✅ Génération Claude terminée:")
    print(f"   Temps: {result['execution_time']:.2f}s")
    print(f"   Score de déterminisme: {result['metrics']['determinism_score']:.3f}")
    print(f"   Score harmonique: {result['metrics']['harmonic_score']:.3f}")
    print(f"   Score de qualité: {result['metrics']['quality_score']:.3f}")
    
    # Affichage du code généré
    print(f"\n📝 Code généré:")
    print("-" * 50)
    print(result['processed_response'][:500] + "..." if len(result['processed_response']) > 500 else result['processed_response'])
    print("-" * 50)
    
    return result

def example_6_user_interface():
    """
    Exemple 6: Interface utilisateur harmonique
    """
    
    print("\n🎨 Exemple 6: Interface Utilisateur Harmonique")
    print("=" * 50)
    
    # Configuration de l'interface
    config = UIConfig(
        ui_type=UIType.JUPYTER_NOTEBOOK,  # Pour l'exemple
        theme=ThemeType.HARMONIC_FULL,
        auto_refresh=False,
        show_advanced_options=False
    )
    
    # Création de l'interface
    ui = HarmonicUI(config)
    
    # Test des visualisations
    print("📊 Test des visualisations harmoniques...")
    
    # Données de test pour les graphiques
    import pandas as pd
    
    timestamps = pd.date_range(start='2024-01-01', periods=10, freq='H')
    phi_data = [PHI + 0.1 * np.sin(i) for i in range(10)]
    pi_data = [PI + 0.01 * np.cos(i) for i in range(10)]
    e_data = [E + 0.2 * np.sin(i/2) for i in range(10)]
    
    metrics_data = {
        'timestamps': timestamps.tolist(),
        'phi_performance': phi_data,
        'pi_precision': pi_data,
        'e_efficiency': e_data,
        'harmonic_score': [0.973 + 0.05 * np.cos(i/3) for i in range(10)]
    }
    
    # Création des visualisations
    print("📈 Tableau de bord de performance...")
    fig1 = ui.visualizer.create_performance_dashboard(metrics_data)
    
    print("🎯 Graphique radar harmonique...")
    scores = {
        'phi_performance': 0.95,
        'pi_precision': 0.92,
        'e_efficiency': 0.88,
        'sqrt2_stability': 0.96,
        'sqrt3_balance': 0.91
    }
    fig2 = ui.visualizer.create_harmonic_radar(scores)
    
    print("📈 Progression d'optimisation...")
    iterations = list(range(1, 51))
    progress_scores = [0.5 + 0.4 * (1 - np.exp(-i/20)) for i in iterations]
    fig3 = ui.visualizer.create_optimization_progress(iterations, progress_scores)
    
    print("✅ Visualisations créées")
    print(f"   Tableau de bord: {len(fig1.data)} traces")
    print(f"   Graphique radar: {len(fig2.data)} traces")
    print(f"   Progression: {len(fig3.data)} points")
    
    # Test des thèmes
    print("\n🎨 Test des thèmes harmoniques...")
    
    themes_to_test = [
        ThemeType.PHI_GOLDEN,
        ThemeType.PI_CIRCULAR,
        ThemeType.E_EXPONENTIAL,
        ThemeType.SQRT2_STABLE,
        ThemeType.SQRT3_BALANCED
    ]
    
    for theme in themes_to_test:
        ui.theme = HarmonicTheme(theme)
        print(f"   {theme.value}: {ui.theme.colors['primary']}")
    
    return ui

def example_7_integration():
    """
    Exemple 7: Intégration complète
    """
    
    print("\n🔄 Exemple 7: Intégration Complète")
    print("=" * 50)
    
    # Initialisation de tous les composants
    print("🔧 Initialisation des composants harmoniques...")
    
    # Configuration
    memory_config = MemoryConfig(max_entries=100, persistence_enabled=False)
    optimization_config = OptimizationConfig(max_iterations=20, population_size=5)
    
    # Création des composants
    memory = HarmonicMemorySystem(memory_config)
    optimizer = HarmonicOptimizationEngine(optimization_config)
    network = HarmonicNeuralNetwork(layers=[32, 16, 8])
    generator = HarmonicCodeGenerator()
    
    print("✅ Composants initialisés")
    
    # Workflow intégré
    print("\n🔄 Workflow intégré harmonique...")
    
    # 1. Stockage de la connaissance initiale
    knowledge = [
        "Les constantes harmoniques φ, π, e, √2, √3 sont universelles",
        "φ optimise la performance de 61.8%",
        "π améliore la précision de 31.4%",
        "e augmente l'efficacité de 171.8%",
        "√2 stabilise les calculs",
        "√3 équilibre les systèmes"
    ]
    
    for i, knowledge_item in enumerate(knowledge):
        memory.store(
            content=knowledge_item,
            memory_type=MemoryType.SEMANTIC,
            priority=MemoryPriority.HIGH,
            tags=["knowledge", f"item_{i+1}"]
        )
    
    # 2. Optimisation des paramètres harmoniques
    targets = [
        OptimizationTarget("knowledge_phi", 1.0, PHI, OptType.PHI_PERFORMANCE),
        OptimizationTarget("knowledge_pi", 1.0, PI, OptType.PI_PRECISION),
        OptimizationTarget("knowledge_e", 1.0, E, OptType.E_EFFICIENCY)
    ]
    
    opt_result = optimizer.optimize_targets(targets)
    
    # 3. Entraînement sur la connaissance
    X = np.random.randn(50, 32)
    y = np.array([[1.0 if "φ" in item else 0.0 for item in knowledge] for _ in range(50)])
    
    train_result = network.train_harmonic(X, y, epochs=10)
    
    # 4. Génération de code basé sur la connaissance
    from harmonic_code_generator import CodeRequirements
    
    requirements = CodeRequirements(
        service_name="KnowledgeService",
        description="Service basé sur la connaissance harmonique",
        endpoints=[],
        database_schema={},
        business_logic=knowledge,
        validation_rules=[]
    )
    
    # Mock de la génération
    generated_code = """
    @Injectable()
    export class KnowledgeService {
      private readonly phi = {PHI};
      private readonly pi = {PI};
      private readonly e = {e};
      
      processKnowledge(input: any): any {
        // Application des constantes harmoniques
        phi_result = input * this.phi;
        pi_result = Math.sin(this.pi * phi_result);
        e_result = Math.exp(this.e * pi_result);
        
        return e_result;
      }
    }
    """
    
    # 5. Stockage du résultat
    result_id = memory.store(
        content=generated_code,
        memory_type=MemoryType.PROCEDURAL,
        priority=MemoryPriority.HIGH,
        tags=["generated", "knowledge", "service"]
    )
    
    # Affichage des résultats
    print(f"✅ Workflow intégré terminé:")
    print(f"   Connaissance stockée: {len(knowledge)} items")
    print(f"   Optimisation: {opt_result.improvement:.2f}% d'amélioration")
    print(f"   Entraînement: {train_result['training_time']:.2f}s")
    print(f"   Code généré: {len(generated_code)} caractères")
    print(f"   Résultat stocké: {result_id}")
    
    # Récupération et validation
    print("\n🔍 Validation de l'intégration...")
    
    retrieved = memory.retrieve("knowledge", limit=5)
    print(f"   Connaissance récupérée: {len(retrieved)} items")
    
    stats = memory.get_statistics()
    print(f"   Score harmonique moyen: {stats['average_harmonic_score']:.3f}")
    
    print("\n🎉 Intégration harmonique complète réussie !")
    
    return {
        'memory': memory,
        'optimizer': optimizer,
        'network': network,
        'generator': generator,
        'results': {
            'optimization': opt_result,
            'training': train_result,
            'code': generated_code,
            'result_id': result_id
        }
    }

def main():
    """Fonction principale"""
    
    print_header()
    
    print("\n📋 Choisissez un exemple à exécuter:")
    print("1. 🧠 Réseau neuronal harmonique")
    print("2. 🚀 Génération de code harmonique")
    print("3. 🧠 Système de mémoire harmonique")
    print("4. ⚡ Optimisation harmonique")
    print("5. 🤖 Génération avec prompts déterministes")
    print("6. 🎨 Interface utilisateur harmonique")
    print("7. 🔄 Intégration complète")
    print("8. 📊 Tous les exemples")
    
    choice = input("\n🎯 Votre choix (1-8): ").strip()
    
    try:
        if choice == "1":
            network = example_1_neural_network()
        elif choice == "2":
            generator = example_2_code_generation()
        elif choice == "3":
            memory = example_3_memory_system()
        elif choice == "4":
            optimizer = example_4_optimization()
        elif choice == "5":
            result = example_5_prompt_generation()
        elif choice == "6":
            ui = example_6_user_interface()
        elif choice == "7":
            integration = example_7_integration()
        elif choice == "8":
            # Exécution de tous les exemples
            print("\n🚀 Exécution de tous les exemples...")
            
            network = example_1_neural_network()
            generator = example_2_code_generation()
            memory = example_3_memory_system()
            optimizer = example_4_optimization()
            result = example_5_prompt_generation()
            ui = example_6_user_interface()
            integration = example_7_integration()
            
            print("\n🎉 Tous les exemples exécutés avec succès !")
        else:
            print("❌ Choix invalide. Veuillez choisir entre 1 et 8.")
            
    except KeyboardInterrupt:
        print("\n👋 Interruption utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🌊 Merci d'avoir testé l'IA Générative Harmonique !")
    print("📚 Pour plus d'informations, consultez la documentation complète.")
    print("🌐 Rejoignez la communauté Discord: https://discord.gg/harmonic-ai")

if __name__ == "__main__":
    main()
