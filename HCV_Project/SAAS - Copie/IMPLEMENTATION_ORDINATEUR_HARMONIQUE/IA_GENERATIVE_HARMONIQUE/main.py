"""
🚀 POINT D'ENTRÉE PRINCIPAL - IA GÉNÉRATIVE HARMONIQUE
Fichier: main.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Point d'entrée principal pour l'IA générative harmonique
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - 🌊 %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Constantes harmoniques universelles
PHI = 1.618033988749895  # Ratio d'or
PI = 3.141592653589793    # Constante circulaire
E = 2.718281828459045      # Nombre d'Euler
SQRT2 = 1.414213562373095  # Racine carrée de 2
SQRT3 = 1.732050807568877  # Racine carrée de 3

# Import des modules harmoniques
try:
    from harmonic_neural_network import HarmonicNeuralNetwork, ActivationType, OptimizationType
    from harmonic_code_generator import HarmonicCodeGenerator
    from harmonic_memory_system import HarmonicMemorySystem, MemoryConfig, MemoryType
    from harmonic_optimization_engine import HarmonicOptimizationEngine, OptimizationConfig, OptimizationTarget
    from harmonic_user_interface import HarmonicUI, UIConfig, ThemeType, UIType
    from prompts.deterministic_ai_prompts import DeterministicPromptEngine
    from prompts.claude_code_prompts import ClaudeCodeHarmonicEngine
    from prompts.openai_codex_prompts import OpenAICodexHarmonicEngine
    from prompts.gemma_4_prompts import Gemma4HarmonicEngine
except ImportError as e:
    logger.error(f"❌ Erreur d'import des modules harmoniques: {e}")
    sys.exit(1)

class HarmonicAI:
    """
    Classe principale de l'IA Générative Harmonique
    Orchestre tous les composants harmoniques
    """
    
    def __init__(self):
        """Initialisation de l'IA Harmonique"""
        
        logger.info("🌊 Initialisation de l'IA Générative Harmonique")
        
        # Affichage des constantes harmoniques
        logger.info(f"φ (phi) = {PHI}")
        logger.info(f"π (pi) = {PI}")
        logger.info(f"e = {E}")
        logger.info(f"√2 = {SQRT2}")
        logger.info(f"√3 = {SQRT3}")
        
        # Initialisation des composants
        self._init_components()
        
        # État du système
        self.state = {
            'initialized': True,
            'active_sessions': 0,
            'total_operations': 0,
            'start_time': None
        }
        
        logger.info("✅ IA Générative Harmonique initialisée avec succès")
    
    def _init_components(self):
        """Initialise tous les composants harmoniques"""
        
        try:
            # Configuration de la mémoire
            memory_config = MemoryConfig(
                max_entries=10000,
                max_working_memory=100,
                cache_size=1000,
                cleanup_interval=3600,
                persistence_enabled=True,
                sqlite_enabled=True,
                redis_enabled=False
            )
            
            # Initialisation des composants
            self.memory_system = HarmonicMemorySystem(memory_config)
            
            # Configuration de l'optimisation
            optimization_config = OptimizationConfig(
                max_iterations=1000,
                convergence_threshold=1e-6,
                population_size=50,
                parallel_workers=4,
                adaptive_learning_rate=True,
                harmonic_weighting=True
            )
            
            self.optimization_engine = HarmonicOptimizationEngine(optimization_config)
            
            # Initialisation des générateurs
            self.code_generator = HarmonicCodeGenerator()
            
            # Initialisation des moteurs de prompts
            self.deterministic_engine = DeterministicPromptEngine()
            self.claude_engine = ClaudeCodeHarmonicEngine()
            self.openai_engine = OpenAICodexHarmonicEngine()
            self.gemma_engine = Gemma4HarmonicEngine()
            
            # Configuration de l'interface
            ui_config = UIConfig(
                ui_type=UIType.STREAMLIT,
                theme=ThemeType.HARMONIC_FULL,
                auto_refresh=True,
                refresh_interval=5,
                show_advanced_options=False,
                enable_animations=True
            )
            
            self.ui = HarmonicUI(ui_config)
            
            logger.info("✅ Tous les composants harmoniques initialisés")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation des composants: {e}")
            raise
    
    def generate_code(self, language: str, service_type: str, framework: str, 
                     service_name: str, **kwargs) -> str:
        """
        Génère du code harmonique
        
        Args:
            language: Langage de programmation
            service_type: Type de service
            framework: Framework utilisé
            service_name: Nom du service
            **kwargs: Paramètres additionnels
            
        Returns:
            Code généré
        """
        
        logger.info(f"🚀 Génération de code harmonique: {service_name}")
        
        try:
            # Configuration des requirements
            from harmonic_code_generator import CodeRequirements
            
            requirements = CodeRequirements(
                service_name=service_name,
                description=f"Service {service_type} harmonique",
                endpoints=kwargs.get('endpoints', []),
                database_schema=kwargs.get('database_schema', {}),
                business_logic=kwargs.get('business_logic', []),
                validation_rules=kwargs.get('validation_rules', []),
                authentication=kwargs.get('authentication', True),
                authorization=kwargs.get('authorization', []),
                caching=kwargs.get('caching', True),
                monitoring=kwargs.get('monitoring', True),
                testing=kwargs.get('testing', True),
                documentation=kwargs.get('documentation', True)
            )
            
            # Génération du code
            generated_files = self.code_generator.generate_full_application(
                requirements, 
                kwargs.get('output_dir', './generated')
            )
            
            self.state['total_operations'] += 1
            
            logger.info(f"✅ Code généré: {len(generated_files)} fichiers")
            
            return list(generated_files.values())[0] if generated_files else ""
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération de code: {e}")
            raise
    
    def optimize_system(self, targets: list, strategy: Optional[str] = None) -> dict:
        """
        Optimise le système harmonique
        
        Args:
            targets: Liste des cibles d'optimisation
            strategy: Stratégie d'optimisation
            
        Returns:
            Résultats d'optimisation
        """
        
        logger.info(f"⚡ Optimisation harmonique: {len(targets)} cibles")
        
        try:
            # Conversion des cibles
            optimization_targets = []
            for target in targets:
                if isinstance(target, dict):
                    opt_target = OptimizationTarget(
                        name=target.get('name', 'target'),
                        current_value=target.get('current_value', 1.0),
                        target_value=target.get('target_value', PHI),
                        weight=target.get('weight', 1.0),
                        optimization_type=target.get('optimization_type', 'phi_performance')
                    )
                else:
                    opt_target = OptimizationTarget(
                        name=str(target),
                        current_value=1.0,
                        target_value=PHI,
                        weight=1.0
                    )
                optimization_targets.append(opt_target)
            
            # Optimisation
            result = self.optimization_engine.optimize_targets(optimization_targets)
            
            self.state['total_operations'] += 1
            
            logger.info(f"✅ Optimisation terminée: {result.improvement:.2f}% d'amélioration")
            
            return {
                'improvement': result.improvement,
                'harmonic_score': result.harmonic_score,
                'iterations': result.iterations,
                'convergence': result.convergence,
                'time': result.optimization_time
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'optimisation: {e}")
            raise
    
    def train_neural_network(self, data, layers: Optional[list] = None, 
                           epochs: int = 100, learning_rate: float = 0.01) -> dict:
        """
        Entraîne un réseau neuronal harmonique
        
        Args:
            data: Données d'entraînement
            layers: Architecture du réseau
            epochs: Nombre d'époques
            learning_rate: Taux d'apprentissage
            
        Returns:
            Métriques d'entraînement
        """
        
        logger.info(f"🧠 Entraînement du réseau neuronal harmonique")
        
        try:
            # Configuration du réseau
            if layers is None:
                layers = [1024, 512, 256, 128]
            
            network = HarmonicNeuralNetwork(
                layers=layers,
                activation=ActivationType.HARMONIC_SIGMOID,
                optimization=OptimizationType.PHI_ADAM
            )
            
            # Entraînement
            import numpy as np
            
            X = np.array(data.get('X', []))
            y = np.array(data.get('y', []))
            
            results = network.train_harmonic(X, y, epochs=epochs, learning_rate=learning_rate)
            
            self.state['total_operations'] += 1
            
            logger.info(f"✅ Entraînement terminé: {results['training_time']:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'entraînement: {e}")
            raise
    
    def store_memory(self, content, memory_type: str = "episodic", 
                    priority: str = "medium", **kwargs) -> str:
        """
        Stocke une entrée dans la mémoire harmonique
        
        Args:
            content: Contenu à stocker
            memory_type: Type de mémoire
            priority: Priorité
            **kwargs: Paramètres additionnels
            
        Returns:
            ID de l'entrée stockée
        """
        
        logger.info(f"🧠 Stockage en mémoire: {memory_type}")
        
        try:
            # Conversion des types
            mem_type = MemoryType(memory_type.lower())
            mem_priority = MemoryPriority(priority.lower())
            
            # Stockage
            entry_id = self.memory_system.store(
                content=content,
                memory_type=mem_type,
                priority=mem_priority,
                context=kwargs.get('context'),
                tags=kwargs.get('tags')
            )
            
            self.state['total_operations'] += 1
            
            logger.info(f"✅ Entrée stockée: {entry_id}")
            
            return entry_id
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du stockage: {e}")
            raise
    
    def retrieve_memory(self, query, memory_type: Optional[str] = None, 
                        limit: int = 10) -> list:
        """
        Récupère des entrées de la mémoire
        
        Args:
            query: Requête
            memory_type: Type de mémoire (optionnel)
            limit: Limite de résultats
            
        Returns:
            Entrées récupérées
        """
        
        logger.info(f"🔍 Récupération mémoire: {memory_type}")
        
        try:
            # Conversion du type
            mem_type = None
            if memory_type:
                mem_type = MemoryType(memory_type.lower())
            
            # Récupération
            from harmonic_memory_system import RetrievalStrategy
            
            results = self.memory_system.retrieve(
                query=query,
                memory_type=mem_type,
                strategy=RetrievalStrategy.HARMONIC_RELEVANCE,
                limit=limit
            )
            
            logger.info(f"✅ {len(results)} entrées récupérées")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération: {e}")
            raise
    
    def generate_with_prompt(self, prompt_type: str, model: str, **kwargs) -> str:
        """
        Génère du contenu avec un prompt déterministe
        
        Args:
            prompt_type: Type de prompt
            model: Modèle IA à utiliser
            **kwargs: Paramètres du prompt
            
        Returns:
            Contenu généré
        """
        
        logger.info(f"🤖 Génération avec prompt: {prompt_type} - {model}")
        
        try:
            # Sélection du moteur
            if model.lower() == "claude":
                engine = self.claude_engine
                prompt_name = f"{prompt_type}_generation"
            elif model.lower() == "openai":
                engine = self.openai_engine
                prompt_name = f"harmonic_{prompt_type}"
            elif model.lower() == "gemma":
                engine = self.gemma_engine
                prompt_name = f"{prompt_type}_generation"
            else:
                engine = self.deterministic_engine
                prompt_name = prompt_type
            
            # Exécution du prompt
            result = engine.execute_prompt(prompt_name, kwargs)
            
            self.state['total_operations'] += 1
            
            logger.info(f"✅ Génération terminée: {result['execution_time']:.2f}s")
            
            return result['processed_response']
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération: {e}")
            raise
    
    def launch_ui(self, ui_type: Optional[str] = None, port: int = 8501):
        """
        Lance l'interface utilisateur
        
        Args:
            ui_type: Type d'interface (optionnel)
            port: Port de l'interface
        """
        
        logger.info(f"🎨 Lancement de l'interface: {ui_type or 'streamlit'}")
        
        try:
            # Configuration de l'interface
            if ui_type:
                ui_config = UIConfig(ui_type=UIType(ui_type.lower()))
                self.ui = HarmonicUI(ui_config)
            
            # Lancement
            self.ui.run()
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du lancement de l'interface: {e}")
            raise
    
    def get_statistics(self) -> dict:
        """
        Récupère les statistiques du système
        
        Returns:
            Statistiques complètes
        """
        
        try:
            stats = {
                'state': self.state,
                'memory': self.memory_system.get_statistics(),
                'optimization': self.optimization_engine.get_optimization_report(),
                'harmonic_constants': {
                    'phi': PHI,
                    'pi': PI,
                    'e': E,
                    'sqrt2': SQRT2,
                    'sqrt3': SQRT3
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des statistiques: {e}")
            raise
    
    def run_interactive_mode(self):
        """Mode interactif"""
        
        print("🌊 IA Générative Harmonique - Mode Interactif")
        print("=" * 50)
        print("Commandes disponibles:")
        print("  generate - Générer du code harmonique")
        print("  optimize - Optimiser le système")
        print("  train - Entraîner un réseau neuronal")
        print("  memory - Gérer la mémoire")
        print("  prompt - Générer avec un prompt")
        print("  stats - Afficher les statistiques")
        print("  ui - Lancer l'interface")
        print("  help - Afficher l'aide")
        print("  exit - Quitter")
        print("=" * 50)
        
        while True:
            try:
                command = input("\n🌊 harmonic> ").strip().lower()
                
                if command == "exit" or command == "quit":
                    print("👋 Au revoir !")
                    break
                
                elif command == "help":
                    self._show_help()
                
                elif command == "stats":
                    stats = self.get_statistics()
                    print("\n📊 Statistiques:")
                    print(f"  Opérations totales: {stats['state']['total_operations']}")
                    print(f"  Sessions actives: {stats['state']['active_sessions']}")
                    print(f"  Entrées mémoire: {stats['memory']['total_entries']}")
                    print(f"  Score harmonique moyen: {stats['memory']['average_harmonic_score']:.3f}")
                
                elif command == "generate":
                    self._interactive_generate()
                
                elif command == "optimize":
                    self._interactive_optimize()
                
                elif command == "train":
                    self._interactive_train()
                
                elif command == "memory":
                    self._interactive_memory()
                
                elif command == "prompt":
                    self._interactive_prompt()
                
                elif command == "ui":
                    self.launch_ui()
                
                else:
                    print(f"❌ Commande inconnue: {command}")
                    print("Tapez 'help' pour l'aide")
                
            except KeyboardInterrupt:
                print("\n👋 Au revoir !")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def _show_help(self):
        """Affiche l'aide"""
        
        print("\n📖 Aide - IA Générative Harmonique")
        print("=" * 50)
        print("Commandes:")
        print("")
        print("🚀 generate - Générer du code harmonique")
        print("  Usage: generate")
        print("  Génère un service TypeScript harmonique")
        print("")
        print("⚡ optimize - Optimise le système")
        print("  Usage: optimize")
        print("  Optimise les constantes harmoniques")
        print("")
        print("🧠 train - Entraîne un réseau neuronal")
        print("  Usage: train")
        print("  Entraîne un réseau neuronal harmonique")
        print("")
        print("🧠 memory - Gère la mémoire")
        print("  Usage: memory")
        print("  Stocke et récupère des informations")
        print("")
        print("🤖 prompt - Génère avec un prompt")
        print("  Usage: prompt")
        print("  Génère du contenu avec des prompts déterministes")
        print("")
        print("📊 stats - Affiche les statistiques")
        print("  Usage: stats")
        print("  Affiche les statistiques du système")
        print("")
        print("🎨 ui - Lance l'interface")
        print("  Usage: ui")
        print("  Lance l'interface utilisateur")
        print("")
        print("❓ help - Affiche cette aide")
        print("  Usage: help")
        print("")
        print("👋 exit - Quitte le programme")
        print("  Usage: exit")
        print("=" * 50)
    
    def _interactive_generate(self):
        """Mode interactif de génération"""
        
        print("\n🚀 Génération de Code Harmonique")
        
        language = input("Langage (typescript/python/javascript): ").strip() or "typescript"
        service_type = input("Type de service (quantique/ia/finance/scientific): ").strip() or "quantique"
        framework = input("Framework (nestjs/express/fastapi): ").strip() or "nestjs"
        service_name = input("Nom du service: ").strip() or "HarmonicService"
        
        try:
            generated_code = self.generate_code(language, service_type, framework, service_name)
            print(f"\n✅ Code généré ({len(generated_code)} caractères):")
            print("-" * 50)
            print(generated_code[:500] + "..." if len(generated_code) > 500 else generated_code)
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    def _interactive_optimize(self):
        """Mode interactif d'optimisation"""
        
        print("\n⚡ Optimisation Harmonique")
        
        targets = []
        
        while True:
            target_name = input("Nom de la cible (ou 'fin'): ").strip()
            if target_name.lower() == 'fin':
                break
            
            current_value = float(input("Valeur actuelle: ").strip() or 1.0)
            target_value = float(input("Valeur cible: ").strip() or PHI)
            weight = float(input("Poids (0-1): ").strip() or 1.0)
            
            targets.append({
                'name': target_name,
                'current_value': current_value,
                'target_value': target_value,
                'weight': weight
            })
        
        if targets:
            try:
                result = self.optimize_system(targets)
                print(f"\n✅ Optimisation terminée:")
                print(f"  Amélioration: {result['improvement']:.2f}%")
                print(f"  Score harmonique: {result['harmonic_score']:.3f}")
                print(f"  Itérations: {result['iterations']}")
                print(f"  Temps: {result['time']:.2f}s")
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def _interactive_train(self):
        """Mode interactif d'entraînement"""
        
        print("\n🧠 Entraînement de Réseau Neuronal Harmonique")
        
        layers_input = input("Architecture (ex: 1024,512,256,128): ").strip()
        epochs = int(input("Nombre d'époques: ").strip() or 100)
        learning_rate = float(input("Taux d'apprentissage: ").strip() or 0.01)
        
        layers = [int(x.strip()) for x in layers_input.split(',')] if layers_input else [1024, 512, 256, 128]
        
        try:
            # Simulation de données
            import numpy as np
            data = {
                'X': np.random.randn(1000, layers[0]),
                'y': np.random.randn(1000, layers[-1])
            }
            
            results = self.train_neural_network(data, layers, epochs, learning_rate)
            
            print(f"\n✅ Entraînement terminé:")
            print(f"  Temps: {results['training_time']:.2f}s")
            print(f"  Perte finale: {results['final_loss']:.6f}")
            print(f"  Score harmonique: {results['metrics']['harmonic_score']:.3f}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    def _interactive_memory(self):
        """Mode interactif de mémoire"""
        
        print("\n🧠 Gestion de Mémoire Harmonique")
        
        action = input("Action (store/retrieve/stats): ").strip().lower()
        
        if action == "store":
            content = input("Contenu à stocker: ").strip()
            memory_type = input("Type de mémoire (episodic/semantic/procedural): ").strip() or "episodic"
            priority = input("Priorité (critical/high/medium/low/temporary): ").strip() or "medium"
            
            try:
                entry_id = self.store_memory(content, memory_type, priority)
                print(f"✅ Entrée stockée: {entry_id}")
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
        elif action == "retrieve":
            query = input("Requête: ").strip()
            memory_type = input("Type de mémoire (optionnel): ").strip() or ""
            limit = int(input("Limite de résultats: ").strip() or 10)
            
            try:
                results = self.retrieve_memory(query, memory_type if memory_type else None, limit)
                
                print(f"\n✅ {len(results)} entrées trouvées:")
                for i, result in enumerate(results[:5]):
                    print(f"  {i+1}. {result.id}: {str(result.content)[:50]}...")
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
        elif action == "stats":
            try:
                stats = self.memory_system.get_statistics()
                print(f"\n📊 Statistiques de la Mémoire:")
                print(f"  Total entrées: {stats['total_entries']}")
                print(f"  Score harmonique moyen: {stats['average_harmonic_score']:.3f}")
                print(f"  Utilisation mémoire travail: {stats['working_memory_usage']:.2%}")
                print(f"  Utilisation cache: {stats['cache_usage']:.2%}")
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
        else:
            print("❌ Action inconnue")
    
    def _interactive_prompt(self):
        """Mode interactif de prompt"""
        
        print("\n🤖 Génération avec Prompt Déterministe")
        
        prompt_type = input("Type de prompt (code/optimization/debugging/architecture): ").strip() or "code"
        model = input("Modèle (claude/openai/gemma): ").strip() or "claude"
        
        try:
            result = self.generate_with_prompt(prompt_type, model)
            print(f"\n✅ Génération terminée:")
            print("-" * 50)
            print(result[:500] + "..." if len(result) > 500 else result)
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    def close(self):
        """Ferme l'IA Harmonique"""
        
        try:
            # Fermeture des composants
            if hasattr(self, 'memory_system'):
                self.memory_system.close()
            
            if hasattr(self, 'optimization_engine'):
                self.optimization_engine.close()
            
            if hasattr(self, 'ui'):
                self.ui.close()
            
            logger.info("🌊 IA Générative Harmonique fermée")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la fermeture: {e}")

def main():
    """Point d'entrée principal"""
    
    parser = argparse.ArgumentParser(description="IA Générative Harmonique")
    parser.add_argument("--mode", choices=["interactive", "ui", "generate", "optimize", "train"], 
                       default="interactive", help="Mode de fonctionnement")
    parser.add_argument("--ui-type", choices=["streamlit", "dash", "jupyter"], 
                       default="streamlit", help="Type d'interface")
    parser.add_argument("--port", type=int, default=8501, help="Port pour l'interface web")
    parser.add_argument("--config", help="Fichier de configuration")
    parser.add_argument("--verbose", action="store_true", help="Mode verbeux")
    
    args = parser.parse_args()
    
    # Configuration du logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialisation de l'IA Harmonique
        ai = HarmonicAI()
        
        if args.mode == "interactive":
            ai.run_interactive_mode()
        
        elif args.mode == "ui":
            ai.launch_ui(args.ui_type, args.port)
        
        elif args.mode == "generate":
            # Génération rapide
            code = ai.generate_code("typescript", "quantique", "nestjs", "HarmonicService")
            print("✅ Code généré avec succès")
        
        elif args.mode == "optimize":
            # Optimisation rapide
            targets = [{"name": "phi_optimization", "target_value": PHI}]
            result = ai.optimize_system(targets)
            print(f"✅ Optimisation terminée: {result['improvement']:.2f}%")
        
        elif args.mode == "train":
            # Entraînement rapide
            import numpy as np
            data = {"X": np.random.randn(100, 1024), "y": np.random.randn(100, 128)}
            results = ai.train_neural_network(data, epochs=10)
            print(f"✅ Entraînement terminé: {results['training_time']:.2f}s")
        
        # Fermeture
        ai.close()
        
    except KeyboardInterrupt:
        print("\n👋 Interruption utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
