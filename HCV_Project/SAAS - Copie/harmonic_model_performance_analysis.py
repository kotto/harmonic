#!/usr/bin/env python3
"""
🔍 ANALYSE PERFORMANCE MODÈLE HARMONIQUE
Diagnostic complet des problèmes de performance
"""

import json
import time
import traceback
from pathlib import Path
from datetime import datetime

class HarmonicModelPerformanceAnalyzer:
    """Analyseur de performance du modèle harmonique"""
    
    def __init__(self):
        print("🔍 ANALYSE PERFORMANCE MODÈLE HARMONIQUE")
        print("=" * 60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "analysis": {},
            "issues": [],
            "recommendations": []
        }
    
    def test_harmonic_api_functionality(self):
        """Tester la fonctionnalité de l'API harmonique"""
        print("\n🧪 TEST FONCTIONNALITÉ API HARMONIQUE...")
        
        try:
            # Importer et tester l'API harmonique
            import sys
            sys.path.append('.')
            
            # Tenter d'importer le module principal
            try:
                from final_deepseek_solution import DeepSeekHarmonicIntelligence, UniversalConstantCalculator
                print("   ✅ Importation réussie")
                
                # Tester le calculateur de constantes
                calculator = UniversalConstantCalculator()
                
                # Tester quelques constantes
                speed_of_light = calculator.calculate_speed_of_light()
                planck_constant = calculator.calculate_planck_constant()
                gravitational_constant = calculator.calculate_gravitational_constant()
                
                constant_tests = {
                    "speed_of_light": speed_of_light,
                    "planck_constant": planck_constant,
                    "gravitational_constant": gravitational_constant
                }
                
                print(f"   📊 Vitesse lumière: {speed_of_light}")
                print(f"   📊 Constante Planck: {planck_constant}")
                print(f"   📊 Constante G: {gravitational_constant}")
                
                # Vérifier si les valeurs sont réalistes
                issues = []
                
                if abs(speed_of_light - 299792458) > 1000:
                    issues.append("Vitesse lumière incorrecte")
                
                if abs(planck_constant - 6.626e-34) > 1e-33:
                    issues.append("Constante Planck incorrecte")
                
                if abs(gravitational_constant - 6.674e-11) > 1e-10:
                    issues.append("Constante gravitationnelle incorrecte")
                
                if issues:
                    print(f"   ❌ Problèmes constantes: {issues}")
                    return {"import_success": True, "constant_issues": issues}
                else:
                    print("   ✅ Constantes calculées correctement")
                    return {"import_success": True, "constant_issues": []}
                
            except ImportError as e:
                print(f"   ❌ Erreur importation: {e}")
                return {"import_success": False, "error": str(e)}
                
        except Exception as e:
            print(f"   ❌ Erreur test API: {e}")
            return {"import_success": False, "error": str(e)}
    
    def test_model_generation(self):
        """Tester la génération du modèle"""
        print("\n🤖 TEST GÉNÉRATION MODÈLE...")
        
        try:
            from final_deepseek_solution import DeepSeekHarmonicIntelligence
            
            # Créer une instance du modèle
            model = DeepSeekHarmonicIntelligence()
            
            # Tester la génération
            test_prompts = [
                "Quelle est la vitesse de la lumière?",
                "Calcule la constante de Planck",
                "Explique la théorie harmonique",
                "Résous 2+2=?"
            ]
            
            generation_results = []
            
            for i, prompt in enumerate(test_prompts):
                try:
                    print(f"   📝 Test {i+1}: {prompt}")
                    
                    start_time = time.time()
                    response = model.generate(prompt)
                    end_time = time.time()
                    
                    generation_time = end_time - start_time
                    
                    # Analyser la réponse
                    response_length = len(response)
                    has_content = response_length > 10
                    is_coherent = any(word in response.lower() for word in ["lumière", "vitesse", "constante", "théorie"])
                    
                    result = {
                        "prompt": prompt,
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "generation_time": generation_time,
                        "response_length": response_length,
                        "has_content": has_content,
                        "is_coherent": is_coherent
                    }
                    
                    generation_results.append(result)
                    
                    print(f"      ⏱️  Temps: {generation_time:.2f}s")
                    print(f"      📊 Longueur: {response_length}")
                    print(f"      📝 Réponse: {result['response']}")
                    
                    if not has_content:
                        print("      ⚠️  Réponse vide ou trop courte")
                    
                    if not is_coherent:
                        print("      ⚠️  Réponse incohérente")
                    
                except Exception as e:
                    print(f"      ❌ Erreur génération: {e}")
                    generation_results.append({
                        "prompt": prompt,
                        "error": str(e),
                        "generation_time": 0,
                        "response_length": 0,
                        "has_content": False,
                        "is_coherent": False
                    })
            
            # Analyser les résultats
            successful_generations = [r for r in generation_results if "error" not in r]
            avg_generation_time = sum(r["generation_time"] for r in successful_generations) / len(successful_generations) if successful_generations else 0
            
            analysis = {
                "total_tests": len(test_prompts),
                "successful": len(successful_generations),
                "failed": len(generation_results) - len(successful_generations),
                "avg_generation_time": avg_generation_time,
                "results": generation_results
            }
            
            print(f"   📊 Succès: {len(successful_generations)}/{len(test_prompts)}")
            print(f"   📊 Temps moyen: {avg_generation_time:.2f}s")
            
            return analysis
            
        except Exception as e:
            print(f"   ❌ Erreur test génération: {e}")
            return {"error": str(e)}
    
    def test_fastapi_endpoints(self):
        """Tester les endpoints FastAPI"""
        print("\n🌐 TEST ENDPOINTS FASTAPI...")
        
        try:
            import requests
            import threading
            import time
            
            # Importer et lancer l'API
            from final_deepseek_solution import app
            
            # Lancer l'API dans un thread séparé
            def run_app():
                import uvicorn
                uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
            
            # Démarrer le serveur
            server_thread = threading.Thread(target=run_app, daemon=True)
            server_thread.start()
            
            # Attendre que le serveur démarre
            time.sleep(3)
            
            # Tester les endpoints
            endpoints = [
                {"name": "Health", "url": "http://127.0.0.1:8000/health", "method": "GET"},
                {"name": "Info", "url": "http://127.0.0.1:8000/info", "method": "GET"},
                {"name": "Constants", "url": "http://127.0.0.1:8000/constants", "method": "GET"},
                {"name": "Generate", "url": "http://127.0.0.1:8000/generate", "method": "POST", "data": {"prompt": "Test prompt"}}
            ]
            
            endpoint_results = []
            
            for endpoint in endpoints:
                try:
                    print(f"   🔍 Test {endpoint['name']}: {endpoint['url']}")
                    
                    start_time = time.time()
                    
                    if endpoint["method"] == "GET":
                        response = requests.get(endpoint["url"], timeout=10)
                    else:
                        response = requests.post(endpoint["url"], json=endpoint["data"], timeout=10)
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    result = {
                        "name": endpoint["name"],
                        "url": endpoint["url"],
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "success": response.status_code == 200,
                        "content_length": len(response.content)
                    }
                    
                    endpoint_results.append(result)
                    
                    print(f"      ✅ Status: {response.status_code}")
                    print(f"      ⏱️  Temps: {response_time:.2f}s")
                    print(f"      📊 Taille: {len(response.content)} bytes")
                    
                    if response.status_code != 200:
                        print(f"      ❌ Erreur: {response.text[:200]}")
                    
                except Exception as e:
                    print(f"      ❌ Erreur endpoint: {e}")
                    endpoint_results.append({
                        "name": endpoint["name"],
                        "url": endpoint["url"],
                        "error": str(e),
                        "success": False
                    })
            
            # Analyser les résultats
            successful_endpoints = [r for r in endpoint_results if r.get("success", False)]
            
            analysis = {
                "total_endpoints": len(endpoints),
                "successful": len(successful_endpoints),
                "failed": len(endpoint_results) - len(successful_endpoints),
                "results": endpoint_results
            }
            
            print(f"   📊 Endpoints réussis: {len(successful_endpoints)}/{len(endpoints)}")
            
            return analysis
            
        except Exception as e:
            print(f"   ❌ Erreur test endpoints: {e}")
            return {"error": str(e)}
    
    def analyze_code_quality(self):
        """Analyser la qualité du code"""
        print("\n📋 ANALYSE QUALITÉ CODE...")
        
        try:
            # Analyser le fichier principal
            main_file = Path("final_deepseek_solution.py")
            
            if not main_file.exists():
                print("   ❌ Fichier principal introuvable")
                return {"error": "Fichier principal introuvable"}
            
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Métriques de qualité
            lines = content.split('\n')
            total_lines = len(lines)
            code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            comment_lines = len([l for l in lines if l.strip().startswith('#')])
            empty_lines = total_lines - code_lines - comment_lines
            
            # Vérifier les imports
            imports = []
            for line in lines:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    imports.append(line.strip())
            
            # Vérifier les classes et fonctions
            classes = []
            functions = []
            
            for line in lines:
                if line.strip().startswith('class '):
                    classes.append(line.strip())
                elif line.strip().startswith('def '):
                    functions.append(line.strip())
            
            # Vérifier les erreurs potentielles
            potential_issues = []
            
            if 'TODO' in content:
                potential_issues.append("Code contient des TODO")
            
            if 'FIXME' in content:
                potential_issues.append("Code contient des FIXME")
            
            if 'print(' in content and 'logging' not in content:
                potential_issues.append("Utilisation de print au lieu de logging")
            
            if 'except:' in content and 'except Exception' not in content:
                potential_issues.append("Except trop large")
            
            quality_analysis = {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "empty_lines": empty_lines,
                "imports_count": len(imports),
                "classes_count": len(classes),
                "functions_count": len(functions),
                "imports": imports[:10],
                "classes": classes,
                "functions": functions[:10],
                "potential_issues": potential_issues
            }
            
            print(f"   📊 Lignes totales: {total_lines}")
            print(f"   📊 Lignes de code: {code_lines}")
            print(f"   📊 Lignes de commentaire: {comment_lines}")
            print(f"   📊 Imports: {len(imports)}")
            print(f"   📊 Classes: {len(classes)}")
            print(f"   📊 Fonctions: {len(functions)}")
            
            if potential_issues:
                print(f"   ⚠️  Problèmes potentiels: {potential_issues}")
            
            return quality_analysis
            
        except Exception as e:
            print(f"   ❌ Erreur analyse qualité: {e}")
            return {"error": str(e)}
    
    def identify_performance_issues(self):
        """Identifier les problèmes de performance"""
        print("\n🔍 IDENTIFICATION PROBLÈMES PERFORMANCE...")
        
        issues = []
        
        # Analyser les résultats des tests
        api_test = self.results["analysis"].get("api_functionality", {})
        generation_test = self.results["analysis"].get("model_generation", {})
        endpoint_test = self.results["analysis"].get("fastapi_endpoints", {})
        code_quality = self.results["analysis"].get("code_quality", {})
        
        # Problèmes d'API
        if not api_test.get("import_success", False):
            issues.append({
                "type": "import_error",
                "severity": "critical",
                "description": "Impossible d'importer l'API harmonique",
                "solution": "Vérifier les dépendances et le code"
            })
        
        if api_test.get("constant_issues"):
            issues.append({
                "type": "constant_calculation",
                "severity": "high",
                "description": "Calcul des constantes incorrect",
                "solution": "Corriger les formules de calcul"
            })
        
        # Problèmes de génération
        if generation_test.get("failed", 0) > 0:
            issues.append({
                "type": "generation_failure",
                "severity": "high",
                "description": f"{generation_test.get('failed', 0)} générations échouées",
                "solution": "Déboguer la fonction de génération"
            })
        
        if generation_test.get("avg_generation_time", 0) > 5:
            issues.append({
                "type": "slow_generation",
                "severity": "medium",
                "description": f"Génération trop lente: {generation_test.get('avg_generation_time', 0):.2f}s",
                "solution": "Optimiser l'algorithme de génération"
            })
        
        # Problèmes d'endpoints
        if endpoint_test.get("failed", 0) > 0:
            issues.append({
                "type": "endpoint_failure",
                "severity": "high",
                "description": f"{endpoint_test.get('failed', 0)} endpoints échoués",
                "solution": "Corriger les endpoints FastAPI"
            })
        
        # Problèmes de code
        if code_quality.get("potential_issues"):
            for issue in code_quality["potential_issues"]:
                issues.append({
                    "type": "code_quality",
                    "severity": "medium",
                    "description": f"Qualité code: {issue}",
                    "solution": "Améliorer la qualité du code"
                })
        
        self.results["issues"] = issues
        
        print(f"   📊 Problèmes identifiés: {len(issues)}")
        
        for i, issue in enumerate(issues):
            print(f"   {i+1}. [{issue['severity'].upper()}] {issue['description']}")
            print(f"      💡 Solution: {issue['solution']}")
        
        return issues
    
    def generate_recommendations(self):
        """Générer les recommandations"""
        print("\n💡 GÉNÉRATION RECOMMANDATIONS...")
        
        issues = self.results["issues"]
        recommendations = []
        
        # Recommandations basées sur les problèmes
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        high_issues = [i for i in issues if i["severity"] == "high"]
        medium_issues = [i for i in issues if i["severity"] == "medium"]
        
        if critical_issues:
            recommendations.append("🚨 URGENT: Corriger les problèmes critiques avant toute chose")
            for issue in critical_issues:
                recommendations.append(f"   • {issue['solution']}")
        
        if high_issues:
            recommendations.append("⚠️  PRIORITAIRE: Corriger les problèmes majeurs")
            for issue in high_issues:
                recommendations.append(f"   • {issue['solution']}")
        
        if medium_issues:
            recommendations.append("📝 AMÉLIORATION: Corriger les problèmes mineurs")
            for issue in medium_issues:
                recommendations.append(f"   • {issue['solution']}")
        
        # Recommandations générales
        if not issues:
            recommendations.append("✅ Aucun problème détecté - Le modèle semble fonctionnel")
        else:
            recommendations.append("🔄 TESTER: Après corrections, relancer les tests complets")
            recommendations.append("📊 MONITORER: Surveiller les performances en continu")
            recommendations.append("📚 DOCUMENTER: Documenter les corrections apportées")
        
        self.results["recommendations"] = recommendations
        
        print(f"   📊 Recommandations générées: {len(recommendations)}")
        
        for recommendation in recommendations:
            print(f"   {recommendation}")
        
        return recommendations
    
    def save_analysis_report(self):
        """Sauvegarder le rapport d'analyse"""
        print("\n📄 SAUVEGARDE RAPPORT D'ANALYSE...")
        
        report_file = Path("harmonic_model_performance_analysis.json")
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"✅ Rapport sauvegardé: {report_file.absolute()}")
        return report_file
    
    def run_complete_analysis(self):
        """Exécuter l'analyse complète"""
        print("🚀 DÉMARRAGE ANALYSE PERFORMANCE COMPLÈTE...")
        
        # 1. Tester la fonctionnalité de l'API
        self.results["analysis"]["api_functionality"] = self.test_harmonic_api_functionality()
        
        # 2. Tester la génération du modèle
        self.results["analysis"]["model_generation"] = self.test_model_generation()
        
        # 3. Tester les endpoints FastAPI
        self.results["analysis"]["fastapi_endpoints"] = self.test_fastapi_endpoints()
        
        # 4. Analyser la qualité du code
        self.results["analysis"]["code_quality"] = self.analyze_code_quality()
        
        # 5. Identifier les problèmes de performance
        self.identify_performance_issues()
        
        # 6. Générer les recommandations
        self.generate_recommendations()
        
        # 7. Sauvegarder le rapport
        report_file = self.save_analysis_report()
        
        print("\n🏆 ANALYSE TERMINÉE!")
        print(f"📄 Rapport complet: {report_file}")
        
        # Afficher le résumé
        issues = self.results["issues"]
        recommendations = self.results["recommendations"]
        
        print("\n🎯 RÉSUMÉ PERFORMANCE:")
        print("=" * 50)
        
        if not issues:
            print("✅ Aucun problème de performance détecté")
            print("🚀 Le modèle harmonique fonctionne correctement")
        else:
            print(f"❌ {len(issues)} problèmes de performance détectés")
            
            critical_count = len([i for i in issues if i["severity"] == "critical"])
            high_count = len([i for i in issues if i["severity"] == "high"])
            medium_count = len([i for i in issues if i["severity"] == "medium"])
            
            print(f"   🚨 Critiques: {critical_count}")
            print(f"   ⚠️  Majeurs: {high_count}")
            print(f"   📝 Mineurs: {medium_count}")
        
        print("\n💡 ACTIONS RECOMMANDÉES:")
        print("=" * 50)
        
        for recommendation in recommendations[:5]:  # Limiter à 5 recommandations
            print(f"   {recommendation}")
        
        return len(issues) == 0  # Retourne True si aucun problème

if __name__ == "__main__":
    analyzer = HarmonicModelPerformanceAnalyzer()
    success = analyzer.run_complete_analysis()
    
    if success:
        print("\n🌊 MODÈLE HARMONIQUE PERFORMANT!")
        print("✅ Prêt pour LM Arena")
    else:
        print("\n❌ MODÈLE HARMONIQUE NÉCESSITE DES CORRECTIONS")
        print("🔧 Appliquer les recommandations du rapport")
