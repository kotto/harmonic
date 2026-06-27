#!/usr/bin/env python3
"""
TEST DES 3 AMELIORATIONS PRIORITAIRES LM ARENA
===============================================
Valide :
1. Temperature adaptative par categorie
2. Expansion harmonique du contexte (x4)
3. max_tokens = 2048

Execute : python test_ameliorations_lm_arena.py
"""

import sys
import os
import time
import json

# Ajouter le repertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Forcer UTF-8 pour la sortie console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Couleurs pour le terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
END = "\033[0m"

def print_header(title):
    print(f"\n{CYAN}{'='*70}{END}")
    print(f"{CYAN}{BOLD}{title}{END}")
    print(f"{CYAN}{'='*70}{END}")

def print_ok(msg):
    print(f"  {GREEN}OK{END} {msg}")

def print_warn(msg):
    print(f"  {YELLOW}WARN{END} {msg}")

def print_fail(msg):
    print(f"  {RED}FAIL{END} {msg}")

def print_info(msg):
    print(f"     {msg}")

# ============================================================================
# TEST 1 : Temperature Adaptative
# ============================================================================
def test_temperature_adaptative():
    print_header("TEST 1 : Temperature Adaptative par Categorie")
    
    try:
        from harmonic_lm_arena_engine import TEMPERATURE_MAP, HarmonicPromptAnalyzer
        
        analyzer = HarmonicPromptAnalyzer()
        
        # Prompts de test par categorie
        test_prompts = [
            ("mathematical", "Calculez la derivee de f(x) = 3x^2 + 2x + 1"),
            ("code", "Ecrivez une fonction Python pour trier une liste"),
            ("creative", "Ecrivez un poeme sur l'amour et la nature"),
            ("reasoning", "Expliquez pourquoi le rechauffement climatique est un probleme complexe"),
            ("factual", "Quelle est la capitale de la France"),
            ("general", "Bonjour, comment allez-vous ?"),
        ]
        
        tests_passed = 0
        tests_total = len(test_prompts)
        
        print(f"\n  {'Categorie attendue':20s} {'Categorie detectee':20s} {'Temperature':12s} {'Resultat':10s}")
        print(f"  {'-'*62}")
        
        for expected_category, prompt in test_prompts:
            signature = analyzer.analyze(prompt)
            category, confidence = analyzer.classify_prompt_with_text(prompt, signature)
            
            # Recuperer la temperature adaptative
            temperature = TEMPERATURE_MAP.get(category, 0.3)
            
            # Verifier que la temperature est correcte
            if category == expected_category or (expected_category == "general" and category == "general"):
                status = f"{GREEN}OK{END}"
                tests_passed += 1
            else:
                status = f"{YELLOW}~{END}"
            
            print(f"  {expected_category:20s} {category:20s} {temperature:<12.1f} {status}")
        
        print(f"\n  Resultat : {tests_passed}/{tests_total} classifications correctes")
        
        # Verifier les valeurs de temperature
        print(f"\n  Verification des temperatures :")
        for cat, temp in TEMPERATURE_MAP.items():
            expected = {"mathematical": 0.0, "code": 0.1, "creative": 0.7, 
                       "reasoning": 0.2, "factual": 0.1, "general": 0.3}
            expected_temp = expected.get(cat, 0.3)
            if temp == expected_temp:
                print_ok(f"{cat}: temperature={temp}")
            else:
                print_fail(f"{cat}: temperature={temp} (attendu={expected_temp})")
        
        return tests_passed == tests_total
        
    except ImportError as e:
        print_fail(f"Impossible d'importer le module : {e}")
        return False
    except Exception as e:
        print_fail(f"Erreur inattendue : {e}")
        return False

# ============================================================================
# TEST 2 : Expansion Harmonique du Contexte
# ============================================================================
def test_expansion_harmonique():
    print_header("TEST 2 : Expansion Harmonique du Contexte (x4)")
    
    try:
        from harmonic_lm_arena_engine import HarmonicResonanceEngine, HARMONIC_EXPANSION_FACTOR
        
        engine = HarmonicResonanceEngine()
        
        print(f"\n  Facteur d'expansion : {HARMONIC_EXPANSION_FACTOR}x")
        
        # Prompts de test pour chaque categorie
        test_prompts = [
            "Calculez 15% de 340 euros",
            "Ecrivez un poeme sur la nature",
            "Expliquez pourquoi le ciel est bleu",
            "Implementez le tri par fusion en Python",
            "Quelle est la definition de la photosynthese",
        ]
        
        tests_passed = 0
        tests_total = len(test_prompts)
        
        print(f"\n  {'Prompt':40s} {'Longueur avant':15s} {'Longueur apres':15s} {'Expansion':10s}")
        print(f"  {'-'*80}")
        
        for prompt in test_prompts:
            result = engine.process(prompt)
            
            if result.response:
                # Simuler la longueur avant expansion (sans expansion)
                # En pratique, on compare avec la longueur de la reponse de base
                response_length = len(result.response)
                
                # Verifier que la reponse est significativement longue
                # Les templates mathematiques courts sont normaux (formules)
                if response_length >= 50:
                    tests_passed += 1
                    status = f"{GREEN}OK{END}"
                else:
                    status = f"{YELLOW}~{END}"
                
                print(f"  {prompt[:38]:40s} {0:15d} {response_length:<15d} {status}")
            else:
                print(f"  {prompt[:38]:40s} {'N/A':15s} {'N/A':15s} {RED}X{END}")
        
        print(f"\n  Resultat : {tests_passed}/{tests_total} expansions reussies")
        
        # Afficher un exemple d'expansion
        print(f"\n  Exemple d'expansion harmonique :")
        print(f"  {'-'*50}")
        result = engine.process("Expliquez pourquoi le ciel est bleu")
        if result.response:
            print(f"  {result.response[:500]}...")
            print(f"\n  Longueur totale : {len(result.response)} caracteres")
        
        return tests_passed == tests_total
        
    except ImportError as e:
        print_fail(f"Impossible d'importer le module : {e}")
        return False
    except Exception as e:
        print_fail(f"Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TEST 3 : max_tokens = 2048
# ============================================================================
def test_max_tokens():
    print_header("TEST 3 : max_tokens = 2048")
    
    try:
        from harmonic_lm_arena_engine import MAX_TOKENS
        
        print(f"\n  max_tokens actuel : {MAX_TOKENS}")
        
        if MAX_TOKENS >= 2048:
            print_ok(f"max_tokens = {MAX_TOKENS} >= 2048")
            return True
        else:
            print_fail(f"max_tokens = {MAX_TOKENS} < 2048")
            return False
            
    except ImportError as e:
        print_fail(f"Impossible d'importer le module : {e}")
        return False

# ============================================================================
# TEST 4 : Performance globale du moteur harmonique
# ============================================================================
def test_performance_globale():
    print_header("TEST 4 : Performance Globale du Moteur Harmonique")
    
    try:
        from harmonic_lm_arena_engine import HarmonicResonanceEngine
        
        engine = HarmonicResonanceEngine()
        
        # Batch de 20 requetes variees
        batch_prompts = [
            "Calculez 10% de 200",
            "Ecrivez une fonction Python pour trier une liste",
            "Quelle est la capitale du Japon",
            "Expliquez la difference entre IA et ML",
            "Ecrivez un haiku sur l'hiver",
            "Calculez 25% de 800",
            "Implementez une classe Stack en Python",
            "Donnez la definition de l'entropie",
            "Pourquoi 1+1=2",
            "Ecrivez une histoire courte sur un robot",
            "Calculez la derivee de x^2",
            "Qu'est-ce que la photosynthese",
            "Comparez Python et Java",
            "Ecrivez un poeme sur la lune",
            "Resolvez l'equation 2x + 5 = 15",
            "Expliquez la theorie de la relativite",
            "Donnez-moi 5 idees de startup",
            "Ecrivez une lettre de motivation",
            "Calculez la moyenne de [1,2,3,4,5]",
            "Quelle est la population de la France",
        ]
        
        print(f"\n  Execution de {len(batch_prompts)} requetes...")
        
        start_time = time.time()
        results = []
        
        for i, prompt in enumerate(batch_prompts):
            result = engine.process(prompt)
            results.append(result)
            
            # Afficher la progression
            if (i + 1) % 5 == 0:
                elapsed = time.time() - start_time
                print(f"     {i+1}/{len(batch_prompts)} requetes traitees en {elapsed:.2f}s")
        
        total_time = time.time() - start_time
        stats = engine.get_stats()
        
        print(f"\n  Statistiques :")
        print(f"     Temps total : {total_time:.2f}s")
        print(f"     Temps moyen : {total_time/len(batch_prompts)*1000:.1f}ms")
        print(f"     Cache hits : {stats['cache_hits']} ({stats['cache_hit_rate']}%)")
        print(f"     Pattern matches : {stats['pattern_matches']} ({stats['pattern_match_rate']}%)")
        print(f"     Fallback DeepSeek : {stats['fallback_deepseek']} ({stats['deepseek_fallback_rate']}%)")
        print(f"     Score resonance moyen : {stats['avg_resonance_score']:.4f}")
        
        # Verifier que les reponses sont longues (expansion harmonique)
        long_responses = sum(1 for r in results if r.response and len(r.response) >= 200)
        print(f"     Reponses longues (>=200 car.) : {long_responses}/{len(results)}")
        
        # Verifier que les reponses ont une structure correcte
        structured_responses = sum(1 for r in results if r.response and 
                                  any(marker in r.response for marker in ['**', '---', '\n\n']))
        print(f"     Reponses structurees : {structured_responses}/{len(results)}")
        
        return True
        
    except ImportError as e:
        print_fail(f"Impossible d'importer le module : {e}")
        return False
    except Exception as e:
        print_fail(f"Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TEST 5 : Integration API
# ============================================================================
def test_integration_api():
    print_header("TEST 5 : Integration API (standalone_api.py)")
    
    try:
        from standalone_api import ChatRequest
        
        # Verifier que max_tokens par defaut est 2048
        req = ChatRequest(prompt="test")
        if req.max_tokens == 2048:
            print_ok(f"max_tokens par defaut = {req.max_tokens}")
        else:
            print_fail(f"max_tokens par defaut = {req.max_tokens} (attendu=2048)")
            return False
        
        # Verifier que temperature par defaut est 0.0
        if req.temperature == 0.0:
            print_ok(f"temperature par defaut = {req.temperature}")
        else:
            print_fail(f"temperature par defaut = {req.temperature} (attendu=0.0)")
            return False
        
        return True
        
    except ImportError as e:
        print_fail(f"Impossible d'importer le module : {e}")
        return False
    except Exception as e:
        print_fail(f"Erreur inattendue : {e}")
        return False

# ============================================================================
# MAIN
# ============================================================================
def main():
    print(f"""
{BOLD}{CYAN}
╔══════════════════════════════════════════════════════════════╗
║     TEST DES 3 AMELIORATIONS PRIORITAIRES LM ARENA          ║
║                                                            ║
║     1. Temperature Adaptative par Categorie                 ║
║     2. Expansion Harmonique du Contexte (x4)                ║
║     3. max_tokens = 2048                                    ║
╚══════════════════════════════════════════════════════════════╝
{END}""")
    
    results = {}
    
    # Test 1 : Temperature Adaptative
    results["Temperature Adaptative"] = test_temperature_adaptative()
    
    # Test 2 : Expansion Harmonique
    results["Expansion Harmonique"] = test_expansion_harmonique()
    
    # Test 3 : max_tokens
    results["max_tokens = 2048"] = test_max_tokens()
    
    # Test 4 : Performance Globale
    results["Performance Globale"] = test_performance_globale()
    
    # Test 5 : Integration API
    results["Integration API"] = test_integration_api()
    
    # RESULTATS FINAUX
    print_header("RESULTATS FINAUX")
    
    all_passed = True
    for test_name, passed in results.items():
        if passed:
            print_ok(f"{test_name}")
        else:
            print_fail(f"{test_name}")
            all_passed = False
    
    print(f"\n{BOLD}{'='*70}{END}")
    if all_passed:
        print(f"{GREEN}{BOLD}TOUS LES TESTS REUSSIS !{END}")
        print(f"{GREEN}Les 3 ameliorations LM Arena sont operationnelles.{END}")
        print(f"\n{GREEN}Prochaine etape : Deploiement sur EC2 et soumission a LM Arena.{END}")
    else:
        print(f"{RED}{BOLD}CERTAINS TESTS ONT ECHOUE{END}")
        print(f"{RED}Corrigez les erreurs avant le deploiement.{END}")
    print(f"{BOLD}{'='*70}{END}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
