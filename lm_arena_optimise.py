"""
Tests LM Arena optimisÃ©s pour connexion internet instable
MÃ©canismes de rÃ©essai et sauvegarde incrÃ©mentale
"""

import requests
import time
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class LM_Arena_Optimise:
    """
    Classe pour exÃ©cuter des tests LM Arena avec gestion des connexions instables
    """
    
    def __init__(self, base_url: str = "http://localhost:8001", max_retries: int = 3):
        """
        Initialiser le testeur
        
        Args:
            base_url: URL de base de l'API (local ou AWS)
            max_retries: Nombre maximum de tentatives par test
        """
        self.base_url = base_url
        self.max_retries = max_retries
        self.results_file = "lm_arena_results_partial.json"
        self.backup_dir = "test_backups"
        
        # CrÃ©er le rÃ©pertoire de sauvegarde
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Charger les rÃ©sultats existants
        self.results = self.load_existing_results()
        
        print(f"ðŸ”§ Testeur LM Arena initialisÃ©")
        print(f"   URL: {self.base_url}")
        print(f"   RÃ©essais max: {self.max_retries}")
        print(f"   RÃ©sultats existants: {len(self.results)} tests")
    
    def load_existing_results(self) -> List[Dict]:
        """
        Charger les rÃ©sultats existants depuis le fichier
        """
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r') as f:
                    data = json.load(f)
                    return data.get("results", [])
            except Exception as e:
                print(f"âš ï¸ Erreur chargement rÃ©sultats: {e}")
                return []
        return []
    
    def test_with_retry(self, prompt: str, max_tokens: int = 100, 
                       timeout: int = 5) -> Dict:
        """
        ExÃ©cuter un test avec mÃ©canisme de rÃ©essai
        
        Args:
            prompt: Prompt Ã  tester
            max_tokens: Nombre maximum de tokens Ã  gÃ©nÃ©rer
            timeout: Timeout en secondes par tentative
            
        Returns:
            Dictionnaire avec la rÃ©ponse ou l'erreur
        """
        for attempt in range(self.max_retries):
            try:
                print(f"  Tentative {attempt+1}/{self.max_retries}...")
                
                response = requests.post(
                    f"{self.base_url}/generate",
                    json={
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                        "temperature": 0.0,
                        "verified_mode": False
                    },
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  âœ“ RÃ©ussite (temps: {result.get('response_time_ms', 0)}ms)")
                    return {
                        "success": True,
                        "data": result,
                        "attempts": attempt + 1
                    }
                else:
                    print(f"  âŒ Code HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"  â±ï¸ Timeout (tentative {attempt+1})")
                
            except requests.exceptions.ConnectionError:
                print(f"  ðŸ”Œ Erreur connexion (tentative {attempt+1})")
                
            except Exception as e:
                print(f"  âš ï¸ Erreur: {e}")
            
            # Pause avant la prochaine tentative
            if attempt < self.max_retries - 1:
                time.sleep(2)
        
        # Toutes les tentatives ont Ã©chouÃ©
        return {
            "success": False,
            "error": f"Ã‰chec aprÃ¨s {self.max_retries} tentatives",
            "attempts": self.max_retries
        }
    
    def run_tests_graduels(self, tests: List[Dict], batch_size: int = 3) -> List[Dict]:
        """
        ExÃ©cuter les tests par petits lots
        
        Args:
            tests: Liste des tests Ã  exÃ©cuter
            batch_size: Nombre de tests par lot
            
        Returns:
            Liste des rÃ©sultats complets
        """
        print(f"ðŸ§ª DÃ©but des tests graduels")
        print(f"   Total tests: {len(tests)}")
        print(f"   Taille lot: {batch_size}")
        print("-" * 50)
        
        all_results = self.results.copy()
        tests_executes = len(all_results)
        
        # Filtrer les tests dÃ©jÃ  exÃ©cutÃ©s
        pending_tests = tests[tests_executes:]
        
        if not pending_tests:
            print("âœ… Tous les tests sont dÃ©jÃ  terminÃ©s")
            return all_results
        
        print(f"ðŸ“‹ Tests en attente: {len(pending_tests)}")
        
        # ExÃ©cuter par lots
        for i in range(0, len(pending_tests), batch_size):
            batch = pending_tests[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(pending_tests) + batch_size - 1) // batch_size
            
            print(f"\nðŸ“¦ Lot {batch_num}/{total_batches} ({len(batch)} tests)")
            print("-" * 40)
            
            for test in batch:
                print(f"\nðŸ” Test: '{test['name']}'")
                print(f"   Prompt: {test['prompt'][:60]}...")
                
                result = self.test_with_retry(
                    prompt=test["prompt"],
                    max_tokens=test.get("max_tokens", 100)
                )
                
                # Enregistrer le rÃ©sultat
                test_result = {
                    "test_name": test["name"],
                    "prompt": test["prompt"],
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                    "batch": batch_num
                }
                
                all_results.append(test_result)
                
                # Sauvegarder aprÃ¨s chaque test
                self.save_partial_results(all_results)
                
                # CrÃ©er une sauvegarde supplÃ©mentaire
                self.create_backup()
            
            # Pause entre les lots (plus longue si connexion instable)
            if batch_num < total_batches:
                pause_time = 10
                print(f"\nâ¸ï¸  Pause de {pause_time} secondes avant le prochain lot...")
                time.sleep(pause_time)
        
        print("\n" + "=" * 50)
        print("âœ… TESTS TERMINÃ‰S")
        print(f"   Total rÃ©sultats: {len(all_results)}")
        print(f"   Fichier: {self.results_file}")
        print("=" * 50)
        
        return all_results
    
    def save_partial_results(self, results: List[Dict]):
        """
        Sauvegarder les rÃ©sultats partiels
        
        Args:
            results: Liste des rÃ©sultats Ã  sauvegarder
        """
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(results),
                "results": results,
                "summary": self.generate_summary(results)
            }
            
            with open(self.results_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Sauvegarde supplÃ©mentaire avec horodatage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.backup_dir}/results_{timestamp}.json"
            
            with open(backup_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"âš ï¸ Erreur sauvegarde rÃ©sultats: {e}")
    
    def create_backup(self):
        """
        CrÃ©er une sauvegarde supplÃ©mentaire du fichier de rÃ©sultats
        """
        try:
            if os.path.exists(self.results_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                backup_file = f"{self.backup_dir}/emergency_backup_{timestamp}.json"
                
                import shutil
                shutil.copy2(self.results_file, backup_file)
                
        except Exception as e:
            print(f"âš ï¸ Erreur crÃ©ation backup: {e}")
    
    def generate_summary(self, results: List[Dict]) -> Dict:
        """
        GÃ©nÃ©rer un rÃ©sumÃ© des rÃ©sultats
        
        Args:
            results: Liste des rÃ©sultats
            
        Returns:
            Dictionnaire avec le rÃ©sumÃ©
        """
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.get("result", {}).get("success", False))
        failed_tests = total_tests - successful_tests
        
        # Calculer le temps moyen de rÃ©ponse
        response_times = []
        for r in results:
            result_data = r.get("result", {})
            if result_data.get("success"):
                data = result_data.get("data", {})
                rt = data.get("response_time_ms", 0)
                if rt > 0:
                    response_times.append(rt)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": round(successful_tests / total_tests * 100, 2) if total_tests > 0 else 0,
            "avg_response_time_ms": round(avg_response_time, 2),
            "timestamp": datetime.now().isoformat()
        }
    
    def print_summary(self):
        """
        Afficher un rÃ©sumÃ© des rÃ©sultats
        """
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r') as f:
                data = json.load(f)
                summary = data.get("summary", {})
                
                print("\n" + "ðŸ“Š RÃ‰SUMÃ‰ DES TESTS " + "="*40)
                print(f"   Tests totaux: {summary.get('total_tests', 0)}")
                print(f"   Tests rÃ©ussis: {summary.get('successful_tests', 0)}")
                print(f"   Tests Ã©chouÃ©s: {summary.get('failed_tests', 0)}")
                print(f"   Taux de rÃ©ussite: {summary.get('success_rate', 0)}%")
                print(f"   Temps rÃ©ponse moyen: {summary.get('avg_response_time_ms', 0)}ms")
                print("="*60)
        else:
            print("âš ï¸ Aucun rÃ©sultat trouvÃ©")

# Tests essentiels (rapides)
TESTS_ESSENTIELS = [
    {
        "name": "health_check",
        "prompt": "Test de santÃ© de l'API",
        "max_tokens": 50
    },
    {
        "name": "simple_math",
        "prompt": "2 + 2 =",
        "max_tokens": 30
    },
    {
        "name": "basic_reasoning",
        "prompt": "Si il pleut, je prends un parapluie. Il pleut. Que fais-je?",
        "max_tokens": 80
    },
    {
        "name": "python_code",
        "prompt": "Ã‰crire une fonction Python qui calcule la factorielle d'un nombre",
        "max_tokens": 120
    },
    {
        "name": "harmonic_ai_info",
        "prompt": "Qu'est-ce que Harmonic AI et quels sont ses avantages?",
        "max_tokens": 150
    },
    {
        "name": "determinism_explanation",
        "prompt": "Explique le dÃ©terminisme en intelligence artificielle",
        "max_tokens": 100
    },
    {
        "name": "zero_hallucination",
        "prompt": "Comment Harmonic AI garantit-il zÃ©ro hallucination?",
        "max_tokens": 120
    },
    {
        "name": "lm_arena_advantage",
        "prompt": "Pourquoi Harmonic AI serait-il bien classÃ© sur LM Arena?",
        "max_tokens": 130
    },
    {
        "name": "technical_specs",
        "prompt": "Quelles sont les spÃ©cifications techniques du modÃ¨le Qwen3.5-DeepSeek-V4?",
        "max_tokens": 140
    },
    {
        "name": "use_cases",
        "prompt": "Donne des exemples d'utilisation de Harmonic AI dans diffÃ©rents secteurs",
        "max_tokens": 160
    }
]

def run_local_demo_tests():
    """
    ExÃ©cuter les tests en mode dÃ©monstration local
    """
    print("ðŸš€ DÃ©marrage tests LM Arena en mode local")
    print("=" * 60)
    
    # Initialiser le testeur avec l'API locale
    tester = LM_Arena_Optimise(
        base_url="http://localhost:8001",
        max_retries=3
    )
    
    # ExÃ©cuter les tests par lots de 2
    results = tester.run_tests_graduels(TESTS_ESSENTIELS, batch_size=2)
    
    # Afficher le rÃ©sumÃ©
    tester.print_summary()
    
    return results

def run_aws_tests():
    """
    ExÃ©cuter les tests sur l'instance AWS (si connexion stable)
    """
    print("ðŸŒ DÃ©marrage tests LM Arena sur AWS")
    print("=" * 60)
    
    # Initialiser le testeur avec l'API AWS
    tester = LM_Arena_Optimise(
        base_url="http://__EC2_IP__:8000",
        max_retries=5  # Plus de rÃ©essais pour AWS
    )
    
    # ExÃ©cuter les tests par lots de 1 (plus prudent pour AWS)
    results = tester.run_tests_graduels(TESTS_ESSENTIELS, batch_size=1)
    
    # Afficher le rÃ©sumÃ©
    tester.print_summary()
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Tests LM Arena optimisÃ©s")
    parser.add_argument("--mode", choices=["local", "aws"], default="local",
                       help="Mode de test (local ou aws)")
    parser.add_argument("--batch", type=int, default=2,
                       help="Taille des lots de tests")
    
    args = parser.parse_args()
    
    if args.mode == "local":
        print("ðŸ”§ Mode: DÃ©monstration local (connexion instable)")
        run_local_demo_tests()
    else:
        print("ðŸŒ Mode: AWS (nÃ©cessite connexion stable)")
        run_aws_tests()