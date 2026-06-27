#!/usr/bin/env python3
"""
Script pour démarrer l'instance EC2 et exécuter les tests LM Arena
"""

import subprocess
import json
import time
import sys
from datetime import datetime

# Configuration
INSTANCE_ID = "i-0716d7805ca2c22e9"  # DeepSeek-Harmonic-V2
INSTANCE_NAME = "DeepSeek-Harmonic-V2"
AWS_REGION = "us-east-1"
API_PORT = 8000  # Basé sur le nom de l'autre instance "port-8000"

def run_aws_command(cmd):
    """Exécuter une commande AWS et retourner le résultat"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)

def start_instance():
    """Démarrer l'instance EC2"""
    print(f"Starting EC2 instance: {INSTANCE_NAME} ({INSTANCE_ID})")
    print("=" * 60)
    
    cmd = f'aws ec2 start-instances --instance-ids {INSTANCE_ID} --region {AWS_REGION}'
    returncode, stdout, stderr = run_aws_command(cmd)
    
    if returncode == 0:
        print("SUCCESS: Instance start command sent")
        
        # Parser la réponse
        try:
            response = json.loads(stdout)
            current_state = response.get("StartingInstances", [{}])[0].get("CurrentState", {}).get("Name", "unknown")
            previous_state = response.get("StartingInstances", [{}])[0].get("PreviousState", {}).get("Name", "unknown")
            
            print(f"  Previous state: {previous_state}")
            print(f"  Current state: {current_state}")
            
            return True
            
        except:
            print(f"  Response: {stdout[:200]}")
            return True
    else:
        print(f"ERROR: Failed to start instance")
        print(f"  Error: {stderr[:200]}")
        return False

def wait_for_instance_running():
    """Attendre que l'instance soit en état running"""
    print("\nWaiting for instance to be running...")
    print("This may take 1-2 minutes")
    
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    check_interval = 10  # Vérifier toutes les 10 secondes
    
    while time.time() - start_time < max_wait_time:
        cmd = f'aws ec2 describe-instances --instance-ids {INSTANCE_ID} --query "Reservations[].Instances[0].State.Name" --output text --region {AWS_REGION}'
        returncode, stdout, stderr = run_aws_command(cmd)
        
        if returncode == 0 and stdout.strip() == "running":
            print(f"SUCCESS: Instance is now running")
            return True
        
        elapsed = int(time.time() - start_time)
        print(f"  Waiting... ({elapsed}s elapsed, state: {stdout.strip() if returncode == 0 else 'error'})")
        time.sleep(check_interval)
    
    print("ERROR: Instance did not reach running state within timeout")
    return False

def get_instance_public_ip():
    """Récupérer l'adresse IP publique de l'instance"""
    print("\nGetting instance public IP address...")
    
    cmd = f'aws ec2 describe-instances --instance-ids {INSTANCE_ID} --query "Reservations[].Instances[0].PublicIpAddress" --output text --region {AWS_REGION}'
    returncode, stdout, stderr = run_aws_command(cmd)
    
    if returncode == 0 and stdout.strip() and stdout.strip() != "None":
        public_ip = stdout.strip()
        print(f"SUCCESS: Public IP address: {public_ip}")
        return public_ip
    else:
        print("ERROR: Could not get public IP address")
        print(f"  Error: {stderr[:200]}")
        return None

def test_connectivity(ip_address):
    """Tester la connectivité à l'instance"""
    print(f"\nTesting connectivity to {ip_address}:{API_PORT}")
    
    endpoints = [
        "/health",
        "/",
        "/api/health",
        "/v1/health"
    ]
    
    for endpoint in endpoints:
        url = f"http://{ip_address}:{API_PORT}{endpoint}"
        
        try:
            # Essayer GET d'abord
            response = requests.get(url, timeout=5)
            print(f"  {endpoint}: HTTP {response.status_code} - {response.text[:50]}")
            
            if response.status_code == 200:
                return url.replace(endpoint, "/generate")
                
        except requests.exceptions.Timeout:
            print(f"  {endpoint}: Timeout")
        except requests.exceptions.ConnectionError:
            print(f"  {endpoint}: Connection refused")
        except Exception as e:
            print(f"  {endpoint}: Error - {str(e)[:50]}")
    
    return None

def run_lm_arena_tests(api_url):
    """Exécuter les tests LM Arena"""
    print(f"\nRunning LM Arena tests on {api_url}")
    print("=" * 60)
    
    test_cases = [
        {
            "category": "reasoning",
            "prompt": "If a train leaves Paris at 8:00 AM traveling at 120 km/h, and another train leaves Lyon at 9:00 AM traveling at 150 km/h towards Paris, and the distance between Paris and Lyon is 450 km, at what time will they meet?",
        },
        {
            "category": "coding",
            "prompt": "Write a Python function to find the longest palindrome substring in a given string.",
        },
        {
            "category": "mathematics",
            "prompt": "Calculate the integral of x^2 * sin(x) from 0 to pi.",
        },
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\nTest: {test['category']}")
        print(f"Prompt: {test['prompt'][:60]}...")
        
        payload = {
            "prompt": test["prompt"],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        try:
            start = time.time()
            response = requests.post(api_url, json=payload, timeout=30)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                text = data.get("text", data.get("response", data.get("choices", [{}])[0].get("text", "")))
                
                print(f"  Status: OK ({elapsed:.2f}s)")
                print(f"  Response: {text[:80]}...")
                
                results.append({
                    "category": test["category"],
                    "status": "passed",
                    "response_time": elapsed,
                    "response_preview": text[:200]
                })
            else:
                print(f"  Status: FAILED (HTTP {response.status_code})")
                results.append({
                    "category": test["category"],
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text[:100]}"
                })
                
        except requests.exceptions.Timeout:
            print("  Status: TIMEOUT")
            results.append({
                "category": test["category"],
                "status": "timeout",
                "error": "30s timeout"
            })
        except Exception as e:
            print(f"  Status: ERROR ({str(e)[:50]})")
            results.append({
                "category": test["category"],
                "status": "error",
                "error": str(e)[:200]
            })
    
    return results

def main():
    """Fonction principale"""
    print("EC2 INSTANCE START AND LM ARENA TEST")
    print("=" * 60)
    
    # Vérifier si requests est installé
    try:
        import requests
    except ImportError:
        print("ERROR: 'requests' library not installed")
        print("Please install it with: pip install requests")
        return
    
    # Étape 1: Démarrer l'instance
    if not start_instance():
        return
    
    # Étape 2: Attendre que l'instance soit running
    if not wait_for_instance_running():
        return
    
    # Étape 3: Récupérer l'IP publique
    public_ip = get_instance_public_ip()
    if not public_ip:
        return
    
    # Donner un peu de temps supplémentaire pour que les services démarrent
    print("\nWaiting for services to start (30 seconds)...")
    time.sleep(30)
    
    # Étape 4: Tester la connectivité
    print(f"\n" + "=" * 60)
    print("TESTING CONNECTIVITY AND FINDING API ENDPOINT")
    print("=" * 60)
    
    # Tester différents ports possibles
    ports_to_test = [8000, 8080, 80, 5000]
    
    working_url = None
    
    for port in ports_to_test:
        print(f"\nTesting port {port}...")
        
        # Tester quelques endpoints courants
        test_urls = [
            f"http://{public_ip}:{port}/health",
            f"http://{public_ip}:{port}/",
            f"http://{public_ip}:{port}/api/health"
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                print(f"  {url}: HTTP {response.status_code}")
                
                if response.status_code == 200:
                    working_url = url
                    print(f"  FOUND WORKING ENDPOINT: {url}")
                    break
                    
            except:
                pass
        
        if working_url:
            break
    
    if not working_url:
        print("\nERROR: Could not find any working API endpoint")
        print("\nPossible issues:")
        print("1. Service not started on the instance")
        print("2. Wrong port (tried: 8000, 8080, 80, 5000)")
        print("3. Security group blocking access")
        print("\nNext steps:")
        print("1. SSH into instance and check service status")
        print("2. Check security group rules")
        return
    
    # Déterminer l'URL de l'API generate
    if "/health" in working_url:
        api_url = working_url.replace("/health", "/generate")
    elif "/api/health" in working_url:
        api_url = working_url.replace("/api/health", "/api/generate")
    else:
        api_url = working_url + "/generate"
    
    print(f"\nAPI URL for tests: {api_url}")
    
    # Étape 5: Exécuter les tests LM Arena
    print(f"\n" + "=" * 60)
    print("EXECUTING LM ARENA TESTS")
    print("=" * 60)
    
    test_results = run_lm_arena_tests(api_url)
    
    # Afficher le résumé
    print("\n" + "=" * 60)
    print("LM ARENA TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r["status"] == "passed")
    failed = sum(1 for r in test_results if r["status"] == "failed")
    timeout = sum(1 for r in test_results if r["status"] == "timeout")
    errors = sum(1 for r in test_results if r["status"] == "error")
    
    print(f"Total tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Timeout: {timeout}")
    print(f"Errors: {errors}")
    
    # Sauvegarder les résultats
    output_file = f"lm_arena_results_{INSTANCE_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "instance_id": INSTANCE_ID,
            "instance_name": INSTANCE_NAME,
            "public_ip": public_ip,
            "api_url": api_url,
            "results": test_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # Afficher les détails des tests échoués
    if failed > 0 or timeout > 0 or errors > 0:
        print("\nDETAILS OF FAILED TESTS:")
        for result in test_results:
            if result["status"] != "passed":
                print(f"\nCategory: {result['category']}")
                print(f"Status: {result['status']}")
                if "error" in result:
                    print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()