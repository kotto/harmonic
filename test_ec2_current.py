#!/usr/bin/env python3
"""
Test de connectivité EC2 actuelle - version sans Unicode
"""

import requests
import socket
import sys

def test_current_ec2():
    """Tester la connectivité actuelle à l'instance EC2"""
    
    ip = "54.81.62.140"
    ports = [8000, 8080, 80, 443]
    
    print(f"Test de connectivité vers {ip}")
    print("=" * 60)
    
    results = {}
    
    # Test de ping (connectivité réseau)
    print("1. Test de ping réseau...")
    try:
        socket.setdefaulttimeout(3)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((ip, 22))  # Port SSH
        if result == 0:
            print("   [OK] Connectivité réseau OK")
            results["network"] = True
        else:
            print("   [ERREUR] Connectivité réseau échouée")
            results["network"] = False
    except Exception as e:
        print(f"   [ERREUR] {e}")
        results["network"] = False
    
    # Test des ports HTTP
    print("\n2. Test des ports HTTP...")
    for port in ports:
        try:
            url = f"http://{ip}:{port}/health"
            print(f"   Port {port}: ", end="")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"[OK] HTTP {response.status_code}")
                print(f"     Response: {response.text[:100]}...")
                results[f"port_{port}"] = True
                results[f"port_{port}_response"] = response.text
            else:
                print(f"[ERREUR] HTTP {response.status_code}")
                results[f"port_{port}"] = False
        except requests.exceptions.Timeout:
            print(f"[TIMEOUT]")
            results[f"port_{port}"] = False
        except requests.exceptions.ConnectionError:
            print(f"[CONNECTION REFUSED]")
            results[f"port_{port}"] = False
        except Exception as e:
            print(f"[ERREUR] {e}")
            results[f"port_{port}"] = False
    
    # Test du port SSH
    print("\n3. Test du port SSH (22)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, 22))
        if result == 0:
            print("   [OK] Port SSH ouvert")
            results["ssh_port"] = True
        else:
            print("   [ERREUR] Port SSH fermé")
            results["ssh_port"] = False
    except Exception as e:
        print(f"   [ERREUR] {e}")
        results["ssh_port"] = False
    
    return results

def test_api_response():
    """Tester la réponse de l'API pour déterminer si c'est mock ou réel"""
    
    ip = "54.81.62.140"
    port = 8000
    
    print("\n4. Test de l'API /generate...")
    print("-" * 40)
    
    test_prompts = [
        "What is the capital of France?",
        "Write a simple Python function",
        "Explain quantum computing"
    ]
    
    api_results = []
    
    for prompt in test_prompts:
        try:
            url = f"http://{ip}:{port}/generate"
            payload = {
                "prompt": prompt,
                "max_tokens": 100
            }
            
            print(f"   Prompt: '{prompt[:30]}...'")
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                generated_text = data.get("generated_text", "")
                
                # Analyser si c'est mock ou réel
                is_mock = "generated response for:" in generated_text.lower() or "mock" in generated_text.lower()
                
                if is_mock:
                    print(f"     [MOCK] Réponse détectée")
                else:
                    print(f"     [REAL] Réponse réelle")
                
                api_results.append({
                    "prompt": prompt,
                    "response": generated_text[:100] + "..." if len(generated_text) > 100 else generated_text,
                    "is_mock": is_mock,
                    "status": "mock" if is_mock else "real"
                })
            else:
                print(f"     [ERREUR] HTTP {response.status_code}")
                api_results.append({
                    "prompt": prompt,
                    "error": f"HTTP {response.status_code}",
                    "status": "error"
                })
                
        except Exception as e:
            print(f"     [ERREUR] {e}")
            api_results.append({
                "prompt": prompt,
                "error": str(e),
                "status": "error"
            })
    
    return api_results

def main():
    """Fonction principale"""
    
    print("ETAT ACTUEL DE L'INSTANCE EC2 - DEEPSEEK HARMONIC V2")
    print("=" * 80)
    
    # Tester la connectivité
    connectivity_results = test_current_ec2()
    
    # Tester l'API
    api_results = test_api_response()
    
    # Analyser les résultats
    print("\n" + "=" * 80)
    print("ANALYSE DES RESULTATS")
    print("=" * 80)
    
    # Connectivité réseau
    if connectivity_results.get("network"):
        print("[OK] Connectivité réseau: L'instance est accessible")
    else:
        print("[ERREUR] Connectivité réseau: L'instance n'est pas accessible")
    
    # Ports HTTP
    http_ports = [p for p in [8000, 8080, 80, 443] if connectivity_results.get(f"port_{p}")]
    if http_ports:
        print(f"[OK] Ports HTTP ouverts: {http_ports}")
    else:
        print("[ERREUR] Aucun port HTTP ouvert")
    
    # Port SSH
    if connectivity_results.get("ssh_port"):
        print("[OK] Port SSH (22) ouvert")
    else:
        print("[ERREUR] Port SSH (22) fermé")
    
    # Analyse de l'API
    print("\nANALYSE DE L'API:")
    mock_count = sum(1 for r in api_results if r.get("status") == "mock")
    real_count = sum(1 for r in api_results if r.get("status") == "real")
    error_count = sum(1 for r in api_results if r.get("status") == "error")
    
    print(f"  Tests mock: {mock_count}")
    print(f"  Tests real: {real_count}")
    print(f"  Tests erreur: {error_count}")
    
    if real_count > 0:
        print("\n[CONCLUSION] L'API retourne des réponses REELLES")
        print("  L'instance EC2 fonctionne correctement")
        print("  Prochaine étape: Exécuter les tests LM Arena complets")
    elif mock_count > 0:
        print("\n[CONCLUSION] L'API retourne des réponses MOCK")
        print("  L'instance EC2 fonctionne mais avec des réponses simulées")
        print("  Prochaine étape: Déployer la version réelle de l'API")
    else:
        print("\n[CONCLUSION] Impossible de tester l'API")
        print("  Vérifier la connectivité et les permissions")
    
    # Recommandations
    print("\n" + "=" * 80)
    print("RECOMMANDATIONS")
    print("=" * 80)
    
    if connectivity_results.get("ssh_port"):
        print("1. Le port SSH est ouvert - vous pouvez essayer de vous connecter:")
        print(f"   ssh -i C:\\Users\\maatc\\.ssh\\deepseek_ec2 ubuntu@{ip}")
        print("\n2. Si SSH échoue, vérifier:")
        print("   - La clé SSH est correcte")
        print("   - L'utilisateur (essayer 'ec2-user' au lieu de 'ubuntu')")
        print("   - Les permissions de la clé")
    else:
        print("1. Le port SSH est fermé - vérifier:")
        print("   - Les groupes de sécurité AWS")
        print("   - Les règles entrantes pour le port 22")
    
    if http_ports:
        print(f"\n2. L'API est accessible sur le port {http_ports[0]}")
        print(f"   URL: http://{ip}:{http_ports[0]}/generate")
    
    print("\n3. Pour déployer la version locale:")
    print("   - Utiliser SCP ou SFTP si SSH fonctionne")
    print("   - Sinon, utiliser AWS Systems Manager (SSM)")
    print("   - Ou redémarrer avec User Data script")
    
    return {
        "connectivity": connectivity_results,
        "api": api_results
    }

if __name__ == "__main__":
    main()