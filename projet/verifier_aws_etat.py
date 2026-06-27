"""
VÃ©rification de l'Ã©tat de l'instance AWS
"""

import requests
import socket
import time
from datetime import datetime

def test_port(host: str, port: int, timeout: int = 5) -> bool:
    """Tester si un port est ouvert"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def test_health_endpoint(host: str, port: int, timeout: int = 5) -> dict:
    """Tester l'endpoint /health"""
    try:
        url = f"http://{host}:{port}/health"
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": f"Code: {response.status_code}"
            }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_generate_endpoint(host: str, port: int, timeout: int = 10) -> dict:
    """Tester l'endpoint /generate"""
    try:
        url = f"http://{host}:{port}/generate"
        payload = {
            "prompt": "Test de connexion AWS - Quelle est la capitale de la France?",
            "max_tokens": 50,
            "temperature": 0.0,
            "verified_mode": True
        }
        
        response = requests.post(url, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": f"Code: {response.status_code}, Response: {response.text[:200]}"
            }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    """Fonction principale"""
    print("=" * 50)
    print("VERIFICATION DE L'INSTANCE AWS - HARMONIC AI")
    print("=" * 50)
    
    # Configuration
    HOST = "__EC2_IP__"
    PORT = 8000
    
    print(f"Instance AWS: {HOST}:{PORT}")
    print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Test 1: Port SSH (22)
    print("1. Test port SSH (22): ", end="")
    ssh_ok = test_port(HOST, 22, timeout=3)
    if ssh_ok:
        print("ACCESSIBLE")
    else:
        print("INACCESSIBLE")
    
    # Test 2: Port API (8000)
    print("2. Test port API (8000): ", end="")
    api_port_ok = test_port(HOST, PORT, timeout=3)
    if api_port_ok:
        print("ACCESSIBLE")
    else:
        print("INACCESSIBLE")
    
    # Test 3: Endpoint /health
    print("3. Test endpoint /health:")
    health_result = test_health_endpoint(HOST, PORT, timeout=5)
    if health_result["success"]:
        print(f"   Status: {health_result['status_code']} OK")
        data = health_result["data"]
        print(f"   Mode: {data.get('mode', 'N/A')}")
        print(f"   Version: {data.get('version', 'N/A')}")
        print(f"   Status: {data.get('status', 'N/A')}")
    else:
        print(f"   Erreur: {health_result.get('error', 'Unknown error')}")
    
    # Test 4: Endpoint /generate
    print("4. Test endpoint /generate:")
    generate_result = test_generate_endpoint(HOST, PORT, timeout=10)
    if generate_result["success"]:
        print(f"   Status: {generate_result['status_code']} OK")
        data = generate_result["data"]
        print(f"   RÃ©ponse: {data.get('text', 'N/A')[:80]}...")
        print(f"   Response ID: {data.get('response_id', 'N/A')}")
        print(f"   Tokens: {data.get('tokens_generated', 'N/A')}")
    else:
        print(f"   Erreur: {generate_result.get('error', 'Unknown error')}")
    
    # RÃ©sumÃ©
    print()
    print("=" * 50)
    print("RESUME:")
    
    tests = [
        ("SSH (22)", ssh_ok),
        ("API Port (8000)", api_port_ok),
        ("/health", health_result["success"]),
        ("/generate", generate_result["success"])
    ]
    
    success_count = sum(1 for _, ok in tests if ok)
    total_tests = len(tests)
    
    for name, ok in tests:
        status = "[OK]" if ok else "[ERREUR]"
        print(f"  {status} {name}")
    
    print()
    print(f"TOTAL: {success_count}/{total_tests} tests rÃ©ussis")
    
    if success_count == total_tests:
        print("SUCCES: L'instance AWS est pleinement operationnelle !")
    elif success_count >= 2:
        print("ATTENTION: L'instance AWS est partiellement accessible")
    else:
        print("ERREUR: L'instance AWS est inaccessible")
    
    print("=" * 50)

if __name__ == "__main__":
    main()