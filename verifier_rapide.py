#!/usr/bin/env python3
"""
VÃ©rification rapide du modÃ¨le sur AWS
"""

import requests
import time
import os

def test_connection():
    print("=== VÃ‰RIFICATION RAPIDE AWS HARMONIC AI ===")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Instance: __EC2_IP__:8000")
    print()
    
    # Test health endpoint
    print("1. Test endpoint /health")
    try:
        response = requests.get("http://__EC2_IP__:8000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   âœ… Health check rÃ©ussi")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Version: {data.get('version', 'N/A')}")
            
            # VÃ©rifier les features
            if 'features' in data:
                print(f"   Features:")
                for key, value in data['features'].items():
                    print(f"     {key}: {value}")
        else:
            print(f"   âŒ Health check Ã©chouÃ©: HTTP {response.status_code}")
    except Exception as e:
        print(f"   âŒ Erreur de connexion: {e}")
    
    print()
    
    # Demander au modÃ¨le de s'identifier
    print("2. Identification du modÃ¨le")
    prompt = "Quel modÃ¨le d'IA es-tu ? Donne ton nom complet, ta version, et tes spÃ©cifications techniques."
    
    try:
        payload = {
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.0,
            "arena_mode": True
        }
        
        response = requests.post(
            "http://__EC2_IP__:8000/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   âœ… RÃ©ponse reÃ§ue")
            print(f"   Version API: {data.get('version', 'N/A')}")
            
            if 'backend_used' in data:
                print(f"   Backend utilisÃ©: {data['backend_used']}")
            
            # Afficher un extrait
            content = data.get('content', '')
            if content:
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"   Extrait: {preview}")
                
                # Analyser pour identifier le modÃ¨le
                content_lower = content.lower()
                
                if 'qwen' in content_lower and 'deepseek' in content_lower and 'v4' in content_lower and 'flash' in content_lower:
                    print(f"   ðŸ” MODÃˆLE IDENTIFIÃ‰: Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf")
                    print(f"   Architecture: Hybrid MoE avec 384 experts")
                    print(f"   Taille: 17.9 GB")
                    print(f"   Performance base estimÃ©e: 1460+ points LM Arena")
                elif 'deepseek' in content_lower and 'v3.2' in content_lower:
                    print(f"   ðŸ” MODÃˆLE IDENTIFIÃ‰: DeepSeek v3.2")
                    print(f"   âš ï¸  ATTENTION: Ce n'est pas le modÃ¨le hybrid Qwen-DeepSeek-V4")
                elif 'deepseek' in content_lower and 'v4' in content_lower:
                    print(f"   ðŸ” MODÃˆLE IDENTIFIÃ‰: DeepSeek V4 (version non-hybrid)")
                else:
                    print(f"   ðŸ” MODÃˆLE: Impossible d'identifier prÃ©cisÃ©ment")
                    print(f"   Contenu: {content[:100]}...")
        else:
            print(f"   âŒ Ã‰chec de la requÃªte: HTTP {response.status_code}")
            print(f"   Erreur: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"   âŒ Timeout: Le modÃ¨le ne rÃ©pond pas dans les 30 secondes")
    except requests.exceptions.ConnectionError:
        print(f"   âŒ Erreur de connexion: Impossible de joindre l'API")
    except Exception as e:
        print(f"   âŒ Erreur inattendue: {e}")
    
    print()
    
    # Tester une requÃªte simple
    print("3. Test de requÃªte simple")
    simple_prompt = "Quelle est la capitale de la France ?"
    
    try:
        payload = {
            "prompt": simple_prompt,
            "max_tokens": 100,
            "temperature": 0.0
        }
        
        start_time = time.time()
        response = requests.post(
            "http://__EC2_IP__:8000/generate",
            json=payload,
            timeout=15
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            content = data.get('content', '')
            print(f"   âœ… RÃ©ponse reÃ§ue en {end_time - start_time:.2f}s")
            print(f"   RÃ©ponse: {content[:150]}...")
            
            # VÃ©rifier la qualitÃ© de la rÃ©ponse
            if 'paris' in content.lower():
                print(f"   âœ… RÃ©ponse correcte (mentionne Paris)")
            else:
                print(f"   âš ï¸  RÃ©ponse ne mentionne pas explicitement Paris")
        else:
            print(f"   âŒ Ã‰chec: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   âŒ Erreur: {e}")
    
    print()
    
    # Conclusion
    print("=== CONCLUSION ===")
    
    # VÃ©rifier les fichiers locaux pour comprendre la configuration
    print("Analyse des fichiers locaux:")
    
    api_files = [
        "deepseek_api_real_final.py",
        "deepseek_api_deepseek_backend.py",
        "DEEPSEEK_V4_HARMONIC_FINAL.py"
    ]
    
    for file in api_files:
        if os.path.exists(file):
            print(f"  ðŸ“„ {file} - PrÃ©sent")
            
            # Lire les premiÃ¨res lignes pour identifier le modÃ¨le
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    first_lines = [f.readline().strip() for _ in range(5)]
                    
                # Chercher des rÃ©fÃ©rences au modÃ¨le
                for line in first_lines:
                    line_lower = line.lower()
                    if 'qwen' in line_lower or 'deepseek' in line_lower:
                        print(f"    â†’ {line[:80]}...")
            except:
                print(f"    â†’ Erreur de lecture")
        else:
            print(f"  âŒ {file} - Absent")
    
    print()
    print("=== RECOMMANDATIONS ===")
    print("1. VÃ©rifier manuellement sur l'instance AWS:")
    print("   ssh -i ~/.ssh/deepseek_ec2 ec2-user@__EC2_IP__")
    print()
    print("2. Examiner le fichier API:")
    print("   cat /opt/deepseek/api.py | grep -i model")
    print()
    print("3. Consulter les logs:")
    print("   sudo journalctl -u deepseek-api | tail -50")
    print()
    print("4. Mettre Ã  jour la documentation avec les informations rÃ©elles")
    print()
    print(f"VÃ©rification terminÃ©e Ã  {time.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    test_connection()