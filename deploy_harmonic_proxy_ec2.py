#!/usr/bin/env python3
"""
DEPLOIEMENT DU PROXY HARMONIQUE SUR EC2
=========================================
Deploie le proxy harmonique sur une instance AWS EC2.

Usage:
    python deploy_harmonic_proxy_ec2.py --check       # Verifier l'instance EC2
    python deploy_harmonic_proxy_ec2.py --deploy      # Deployer le proxy
    python deploy_harmonic_proxy_ec2.py --status      # Statut du deploiement
"""

import os, sys, json, time, subprocess, argparse
from typing import Optional, Dict, Any

# Configuration AWS
AWS_REGION = "us-east-1"
AWS_ACCESS_KEY = "AKIAUX3GRWKTZEPOJOFI"
AWS_SECRET_KEY = "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"

# Fichiers a deployer
DEPLOY_FILES = [
    "harmonic_aws_surgery.py",
    "harmonic_training/model/harmonic_attention.py",
    "harmonic_training/model/abc_kernel.py",
    "harmonic_training/model/__init__.py",
    "harmonic_training/config/training_config.py",
    ".env",
    "requirements.txt",
]

REQUIREMENTS = """fastapi==0.104.1
uvicorn==0.24.0
torch>=2.0.0
numpy>=1.24.0
requests>=2.31.0
pydantic>=2.0.0
python-dotenv>=1.0.0
"""


def check_aws_cli() -> bool:
    """Verifie que AWS CLI est installe."""
    try:
        result = subprocess.run(["aws", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"[OK] AWS CLI: {result.stdout.strip()}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    print("[ERREUR] AWS CLI non trouve")
    return False


def configure_aws_cli():
    """Configure AWS CLI avec les credentials."""
    cmds = [
        f"aws configure set aws_access_key_id {AWS_ACCESS_KEY}",
        f"aws configure set aws_secret_access_key {AWS_SECRET_KEY}",
        f"aws configure set region {AWS_REGION}",
    ]
    for cmd in cmds:
        subprocess.run(cmd, shell=True, capture_output=True)
    print("[OK] AWS CLI configure")


def check_ec2_instances() -> list:
    """Liste les instances EC2 disponibles."""
    try:
        result = subprocess.run(
            ["aws", "ec2", "describe-instances", 
             "--query", "Reservations[].Instances[].[InstanceId,State.Name,InstanceType,PublicDnsName,PublicIpAddress]",
             "--output", "json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            instances = json.loads(result.stdout)
            if instances:
                print(f"\n[OK] {len(instances)} instance(s) EC2 trouvee(s):")
                for inst in instances:
                    inst_id, state, inst_type, dns, ip = inst
                    print(f"  - {inst_id} ({state}) | {inst_type} | DNS: {dns or 'N/A'} | IP: {ip or 'N/A'}")
                return instances
            else:
                print("[INFO] Aucune instance EC2 trouvee")
        else:
            print(f"[ERREUR] AWS CLI: {result.stderr[:200]}")
    except Exception as e:
        print(f"[ERREUR] {e}")
    return []


def create_requirements():
    """Cree le fichier requirements.txt."""
    with open("requirements.txt", "w") as f:
        f.write(REQUIREMENTS)
    print("[OK] requirements.txt cree")


def prepare_deployment_package() -> str:
    """Prepare le package de deploiement."""
    import shutil
    import tempfile
    
    pkg_dir = "deploy_harmonic_proxy"
    os.makedirs(pkg_dir, exist_ok=True)
    
    # Copier les fichiers
    for filepath in DEPLOY_FILES:
        src = filepath
        dst = os.path.join(pkg_dir, filepath)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  [OK] {filepath}")
        else:
            print(f"  [WARN] {filepath} non trouve")
    
    # Creer le script de demarrage
    start_script = """#!/bin/bash
# Demarrage du proxy harmonique sur EC2
cd /home/ubuntu/harmonic-proxy

# Charger les variables d'environnement
export $(grep -v '^#' .env | xargs)

# Installer les dependances
pip install -r requirements.txt

# Lancer le serveur
python harmonic_aws_surgery.py --mode serve --port 8080
"""
    with open(os.path.join(pkg_dir, "start.sh"), "w") as f:
        f.write(start_script)
    os.chmod(os.path.join(pkg_dir, "start.sh"), 0o755)
    
    print(f"\n[OK] Package pret: {pkg_dir}/")
    return pkg_dir


def deploy_to_ec2(instance_dns: str, key_pair: str = "qwen35-keypair"):
    """Deploie le proxy sur une instance EC2 via SCP/SSH."""
    import shutil
    
    pkg_dir = prepare_deployment_package()
    
    # Creer l'archive
    archive_name = "harmonic-proxy.tar.gz"
    subprocess.run(
        f"tar -czf {archive_name} -C {pkg_dir} .",
        shell=True, capture_output=True
    )
    
    # Copier sur EC2
    print(f"\n[INFO] Copie vers {instance_dns}...")
    scp_cmd = f"scp -i ~/.ssh/{key_pair}.pem -o StrictHostKeyChecking=no {archive_name} ubuntu@{instance_dns}:~/"
    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=60)
    
    if result.returncode != 0:
        print(f"[ERREUR] SCP: {result.stderr[:200]}")
        return False
    
    # Deployer sur EC2
    print(f"\n[INFO] Deploiement sur {instance_dns}...")
    ssh_cmd = (
        f"ssh -i ~/.ssh/{key_pair}.pem -o StrictHostKeyChecking=no ubuntu@{instance_dns} "
        f"\"mkdir -p ~/harmonic-proxy && "
        f"tar -xzf ~/harmonic-proxy.tar.gz -C ~/harmonic-proxy && "
        f"cd ~/harmonic-proxy && "
        f"chmod +x start.sh && "
        f"nohup ./start.sh > harmonic-proxy.log 2>&1 &"
        f"\""
    )
    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=120)
    
    if result.returncode == 0:
        print(f"[OK] Proxy harmonique deploye sur {instance_dns}")
        print(f"[INFO] API: http://{instance_dns}:8080/v1/chat/completions")
        print(f"[INFO] Health: http://{instance_dns}:8080/health")
        return True
    else:
        print(f"[ERREUR] SSH: {result.stderr[:200]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Deploiement proxy harmonique EC2")
    parser.add_argument("--check", action="store_true", help="Verifier les instances EC2")
    parser.add_argument("--deploy", action="store_true", help="Deployer le proxy")
    parser.add_argument("--status", action="store_true", help="Statut du deploiement")
    parser.add_argument("--dns", type=str, default="", help="DNS de l'instance EC2")
    parser.add_argument("--key", type=str, default="qwen35-keypair", help="Nom de la key pair")
    
    args = parser.parse_args()
    
    if args.check:
        if not check_aws_cli():
            configure_aws_cli()
        check_ec2_instances()
    
    elif args.deploy:
        create_requirements()
        
        if args.dns:
            deploy_to_ec2(args.dns, args.key)
        else:
            # Chercher automatiquement
            if not check_aws_cli():
                configure_aws_cli()
            instances = check_ec2_instances()
            
            if instances:
                # Prendre la premiere instance running
                for inst in instances:
                    inst_id, state, inst_type, dns, ip = inst
                    if state == "running" and dns:
                        print(f"\n[INFO] Deploiement sur {inst_id} ({dns})...")
                        deploy_to_ec2(dns, args.key)
                        break
                else:
                    print("[ERREUR] Aucune instance running trouvee")
            else:
                print("[ERREUR] Aucune instance EC2 trouvee")
    
    elif args.status:
        if not check_aws_cli():
            configure_aws_cli()
        instances = check_ec2_instances()
        
        if instances:
            for inst in instances:
                inst_id, state, inst_type, dns, ip = inst
                if state == "running" and dns:
                    # Tester le proxy
                    try:
                        import requests
                        r = requests.get(f"http://{dns}:8080/health", timeout=5)
                        if r.status_code == 200:
                            print(f"\n[OK] Proxy harmonique actif sur {dns}:8080")
                            print(f"  Reponse: {r.json()}")
                        else:
                            print(f"\n[WARN] Proxy sur {dns}:8080 repond avec code {r.status_code}")
                    except Exception as e:
                        print(f"\n[INFO] Proxy sur {dns}:8080 non accessible: {e}")
    
    else:
        parser.print_help()
        print("\nExemples:")
        print("  python deploy_harmonic_proxy_ec2.py --check")
        print("  python deploy_harmonic_proxy_ec2.py --deploy --dns ec2-xxx.compute.amazonaws.com")
        print("  python deploy_harmonic_proxy_ec2.py --status")


if __name__ == "__main__":
    main()
