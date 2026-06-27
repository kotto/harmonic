#!/usr/bin/env python3
"""
Test de connectivité EC2 - Version simple sans caractères spéciaux
"""

import requests
import socket
import sys

def test_connectivity():
    """Tester la connectivité à l'instance EC2"""
    
    ip = "54.81.62.140"
    ports = [8000, 8080, 80]
    
    print(f"Test de connectivité vers {ip}")
    print("=" * 60)
    
    # Test de ping (connectivité réseau)
    print("1. Test de ping réseau...")
    try:
        socket.setdefaulttimeout(3)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((ip, 22))  # Port SSH
        if result == 0:
            print("   [OK] Connectivité réseau OK")
        else:
            print("   [ERREUR] Connectivité réseau échouée")
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    # Test des ports HTTP
    print("\n2. Test des ports HTTP...")
    for port in ports:
        try:
            url = f"http://{ip}:{port}/health"
            print(f"   Port {port}: ", end="")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"[OK] HTTP {response.status_code}")
                print(f"     Response: {response.json()}")
                return True, port
            else:
                print(f"[ERREUR] HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"[TIMEOUT]")
        except requests.exceptions.ConnectionError:
            print(f"[CONNECTION REFUSED]")
        except Exception as e:
            print(f"[ERREUR] {e}")
    
    # Test du port SSH
    print("\n3. Test du port SSH (22)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, 22))
        if result == 0:
            print("   [OK] Port SSH ouvert")
            return False, 22  # SSH ouvert mais pas d'API HTTP
        else:
            print("   [ERREUR] Port SSH fermé")
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    return False, None

def main():
    """Fonction principale"""
    
    print("TEST DE CONNECTIVITE EC2 - DEEPSEEK HARMONIC V2")
    print("=" * 60)
    
    api_accessible, port = test_connectivity()
    
    print("\n" + "=" * 60)
    print("CONCLUSION:")
    
    if api_accessible:
        print(f"[OK] API accessible sur http://54.81.62.140:{port}")
        print("  L'instance EC2 est démarrée et l'API répond")
        print("\nProchaine étape: Tester si l'API retourne des réponses réelles")
    elif port == 22:
        print("[OK] Port SSH ouvert mais API HTTP non accessible")
        print("  L'instance EC2 est démarrée mais l'API ne tourne pas")
        print("\nProchaine étape: Déployer l'API réelle via SSH")
    else:
        print("[ERREUR] Instance EC2 non accessible")
        print("  L'instance est peut-être arrêtée ou les ports sont fermés")
        print("\nProchaine étape: Démarrer l'instance EC2 via AWS Console")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()