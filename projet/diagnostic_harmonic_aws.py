#!/usr/bin/env python3
"""
DIAGNOSTIC COMPLET DU PROXY HARMONIQUE AWS
============================================
Verifie l'etat de tous les composants et propose des actions.

Usage:
    python diagnostic_harmonic_aws.py
"""

import os, sys, json, time, subprocess
from datetime import datetime

# Couleurs ANSI
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def ok(msg): print(f"  {GREEN}[OK]{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}[WARN]{RESET} {msg}")
def err(msg): print(f"  {RED}[ERR]{RESET} {msg}")
def info(msg): print(f"  {CYAN}[INFO]{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{msg}{RESET}")
def sep(): print(f"  {'-'*50}")


def check_proxy_local():
    """Verifie le proxy harmonique local."""
    header("PROXY HARMONIQUE LOCAL (port 8080)")
    
    try:
        import requests
        r = requests.get("http://localhost:8080/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            ok(f"Proxy actif - uptime: {data.get('uptime_seconds', '?')}s")
            info(f"  Requetes: {data.get('total_requests', 0)}")
            info(f"  Erreurs: {data.get('errors', 0)}")
            info(f"  Resonance active: {data.get('resonance_active', False)}")
            info(f"  Backend configure: {data.get('backend_configured', False)}")
            return True
        else:
            err(f"Reponse HTTP {r.status_code}")
    except requests.exceptions.ConnectionError:
        err("Proxy non accessible sur localhost:8080")
    except Exception as e:
        err(f"Erreur: {e}")
    return False


def check_proxy_api():
    """Teste l'API de chat du proxy."""
    header("API DE CHAT HARMONIQUE")
    
    try:
        import requests
        r = requests.post(
            "http://localhost:8080/v1/chat/completions",
            json={
                "model": "harmonic-proxy",
                "messages": [{"role": "user", "content": "Dis bonjour en 5 mots"}],
                "max_tokens": 50,
            },
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            harmonic = data.get("harmonic_analysis", {})
            ok(f"API repond correctement")
            info(f"  Resonance: {harmonic.get('resonance', 0):.4f}")
            info(f"  Latence: {harmonic.get('latency_ms', 0):.1f}ms")
            info(f"  Reponse: {content[:80]}...")
            return True
        else:
            err(f"API HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        err(f"Erreur API: {e}")
    return False


def check_aws_instances():
    """Verifie les instances EC2."""
    header("INSTANCES AWS EC2")
    
    try:
        result = subprocess.run(
            ["aws", "ec2", "describe-instances",
             "--query", "Reservations[].Instances[].[InstanceId,State.Name,InstanceType,PublicDnsName,PublicIpAddress,LaunchTime]",
             "--output", "json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            instances = json.loads(result.stdout)
            if instances:
                ok(f"{len(instances)} instance(s) trouvee(s)")
                for inst in instances:
                    inst_id, state, inst_type, dns, ip, launch = inst
                    if state == "running":
                        ok(f"{inst_id} ({inst_type}) - {state}")
                        info(f"  DNS: {dns}")
                        info(f"  IP: {ip}")
                        info(f"  Lancement: {launch}")
                    else:
                        warn(f"{inst_id} ({inst_type}) - {state}")
                return instances
            else:
                warn("Aucune instance EC2 trouvee")
        else:
            err(f"AWS CLI: {result.stderr[:200]}")
    except FileNotFoundError:
        err("AWS CLI non installe")
    except Exception as e:
        err(f"Erreur: {e}")
    return []


def check_env_config():
    """Verifie la configuration .env."""
    header("CONFIGURATION (.env)")
    
    env_path = ".env"
    if not os.path.exists(env_path):
        err("Fichier .env non trouve")
        return False
    
    with open(env_path) as f:
        content = f.read()
    
    checks = {
        "GENERATION_MODE": "harmonic" in content,
        "AWS_ACCESS_KEY_ID": "AKIA" in content,
        "AWS_SECRET_ACCESS_KEY": "ektC" in content,
        "AWS_DEFAULT_REGION": "us-east-1" in content,
        "PORT": "8080" in content,
    }
    
    all_ok = True
    for name, status in checks.items():
        if status:
            ok(f"{name} configure")
        else:
            warn(f"{name} non configure")
            all_ok = False
    
    return all_ok


def check_dataset():
    """Verifie le dataset d'entrainement."""
    header("DATASET D'ENTRAINEMENT")
    
    dataset_path = "harmonic_logs/harmonic_dataset.json"
    if os.path.exists(dataset_path):
        with open(dataset_path) as f:
            data = json.load(f)
        ok(f"Dataset trouve: {len(data)} echantillons")
        
        # Stats
        resonances = [e.get("resonance", 0) for e in data]
        if resonances:
            info(f"  Resonance moyenne: {sum(resonances)/len(resonances):.4f}")
            info(f"  Resonance max: {max(resonances):.4f}")
            info(f"  Resonance min: {min(resonances):.4f}")
    else:
        warn("Dataset non trouve")
    
    # Modele entraine
    model_path = "harmonic_logs/adapter_model.npz"
    if os.path.exists(model_path):
        ok(f"Modele entraine trouve: {model_path}")
    else:
        warn("Modele entraine non trouve")


def check_network():
    """Verifie la connectivite reseau."""
    header("CONNECTIVITE RESEAU")
    
    import socket
    
    tests = [
        ("localhost", 8080, "Proxy harmonique local"),
        ("8.8.8.8", 53, "DNS Google"),
    ]
    
    for host, port, name in tests:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                ok(f"{name} ({host}:{port})")
            else:
                warn(f"{name} ({host}:{port}) - non accessible")
        except Exception as e:
            err(f"{name}: {e}")


def check_s3_access():
    """Verifie l'acces aux buckets S3."""
    header("ACCES S3")
    
    buckets = [
        "harmonic-ai-knowledge-base",
        "deepseek-models-326095712935",
    ]
    
    for bucket in buckets:
        try:
            result = subprocess.run(
                ["aws", "s3", "ls", f"s3://{bucket}/", "--max-items", "1"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                ok(f"Bucket S3 accessible: {bucket}")
            else:
                warn(f"Bucket S3 non accessible: {bucket}")
        except Exception as e:
            err(f"Bucket S3 {bucket}: {e}")


def show_summary(results):
    """Affiche le resume."""
    header("RESUME")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Proxy local: {'ACTIF' if results.get('proxy_local') else 'INACTIF'}")
    print(f"  API chat: {'FONCTIONNELLE' if results.get('proxy_api') else 'EN PANNE'}")
    print(f"  Instances EC2: {results.get('ec2_count', 0)}")
    print(f"  Configuration: {'COMPLETE' if results.get('env_ok') else 'INCOMPLETE'}")
    print(f"  Dataset: {results.get('dataset_size', 0)} echantillons")
    
    print(f"\n{BOLD}ACTIONS RECOMMANDEES:{RESET}")
    if not results.get('proxy_local'):
        print(f"  - Lancer: python harmonic_aws_surgery.py --mode serve")
    if results.get('ec2_running'):
        print(f"  - Deployer sur EC2: python deploy_harmonic_proxy_ec2.py --deploy --dns {results.get('ec2_dns', '')}")
    if results.get('dataset_size', 0) < 50:
        print(f"  - Collecter plus de donnees: python train_harmonic_adapter_dataset.py --collect --samples 100")
    print(f"  - Entrainer le modele: python train_harmonic_adapter_dataset.py --train")


def main():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}DIAGNOSTIC HARMONIQUE AWS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    
    results = {}
    
    results['proxy_local'] = check_proxy_local()
    results['proxy_api'] = check_proxy_api()
    instances = check_aws_instances()
    results['ec2_count'] = len(instances)
    results['ec2_running'] = any(i[1] == "running" for i in instances) if instances else False
    results['ec2_dns'] = next((i[3] for i in instances if i[1] == "running"), "")
    results['env_ok'] = check_env_config()
    check_dataset()
    check_network()
    check_s3_access()
    
    # Dataset size
    dataset_path = "harmonic_logs/harmonic_dataset.json"
    if os.path.exists(dataset_path):
        with open(dataset_path) as f:
            results['dataset_size'] = len(json.load(f))
    else:
        results['dataset_size'] = 0
    
    show_summary(results)
    
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}DIAGNOSTIC TERMINE{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
