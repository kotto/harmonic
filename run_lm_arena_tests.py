#!/usr/bin/env python3
"""
Script pour exÃ©cuter les tests LM Arena depuis le PC
"""

import subprocess
import sys
import os

def run_lm_arena_tests():
    """ExÃ©cuter les tests LM Arena avec l'API distante"""
    
    # URL de l'API sur l'instance EC2
    api_url = "http://__EC2_IP__:8000"
    
    print("=" * 80)
    print("EXÃ‰CUTION DES TESTS LM ARENA")
    print("=" * 80)
    print(f"API URL: {api_url}")
    print("=" * 80)
    
    # ExÃ©cuter le script LM Arena avec l'URL de l'API
    cmd = [sys.executable, "lm_arena_final_simple.py", "--base-url", api_url]
    
    try:
        print(f"ExÃ©cution de la commande: {' '.join(cmd)}")
        print()
        
        # ExÃ©cuter le script
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        # Afficher la sortie
        print(result.stdout)
        
        if result.stderr:
            print("Erreurs:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
        
        print("=" * 80)
        print(f"Code de sortie: {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Erreur lors de l'exÃ©cution: {e}")
        return False

if __name__ == "__main__":
    success = run_lm_arena_tests()
    sys.exit(0 if success else 1)