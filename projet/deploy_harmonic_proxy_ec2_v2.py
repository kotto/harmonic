#!/usr/bin/env python3
"""
DEPLOIEMENT PROXY HARMONIQUE SUR EC2 (V2 - Python pur)
=========================================================
Utilise boto3 et paramiko pour deployer sans dependance SCP/SSH externe.

Usage:
    python deploy_harmonic_proxy_ec2_v2.py --deploy
    python deploy_harmonic_proxy_ec2_v2.py --status
"""

import os, sys, json, time, io, tarfile, argparse
from typing import Optional

# Configuration
AWS_REGION = "us-east-1"
INSTANCE_ID = "i-0716d7805ca2c22e9"
EC2_DNS = "ec2-__EC2_IP__.compute-1.amazonaws.com"
EC2_IP = "__EC2_IP__"
KEY_NAME = "qwen35-keypair"
KEY_PATH = os.path.expanduser(f"~/.ssh/{KEY_NAME}.pem")
REMOTE_DIR = "/home/ubuntu/harmonic-proxy"
LOCAL_PORT = 8080
REMOTE_PORT = 8080

FILES_TO_DEPLOY = [
    "harmonic_aws_surgery.py",
    "harmonic_training/model/harmonic_attention.py",
    "harmonic_training/model/abc_kernel.py",
    "harmonic_training/model/__init__.py",
    "harmonic_training/config/training_config.py",
    ".env",
]

REQUIREMENTS = """fastapi==0.104.1
uvicorn==0.24.0
torch>=2.0.0
numpy>=1.24.0
requests>=2.31.0
pydantic>=2.0.0
python-dotenv>=1.0.0
boto3>=1.28.0
"""

START_SCRIPT = """#!/bin/bash
cd {remote_dir}
export $(grep -v '^#' .env | xargs)
pip install -r requirements.txt
nohup python harmonic_aws_surgery.py --mode serve --port {port} > harmonic-proxy.log 2>&1 &
echo "Proxy harmonique demarre sur le port {port}"
"""


def check_dependencies():
    """Verifie les dependances Python."""
    missing = []
    try:
        import boto3
    except ImportError:
        missing.append("boto3")
    try:
        import paramiko
    except ImportError:
        missing.append("paramiko")
    
    if missing:
        print(f"[INFO] Installation des dependances manquantes: {', '.join(missing)}")
        for pkg in missing:
            os.system(f"pip install {pkg} -q")
        print("[OK] Dependances installees")
    
    return True


def create_deployment_package() -> bytes:
    """Cree une archive tar.gz en memoire."""
    buf = io.BytesIO()
    
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        # Ajouter les fichiers du projet
        for filepath in FILES_TO_DEPLOY:
            if os.path.exists(filepath):
                tar.add(filepath, arcname=filepath)
                print(f"  [OK] {filepath}")
            else:
                print(f"  [WARN] {filepath} non trouve")
        
        # Ajouter requirements.txt
        req_info = tarfile.TarInfo(name="requirements.txt")
        req_data = REQUIREMENTS.encode()
        req_info.size = len(req_data)
        tar.addfile(req_info, io.BytesIO(req_data))
        
        # Ajouter le script de demarrage
        start_content = START_SCRIPT.format(remote_dir=REMOTE_DIR, port=REMOTE_PORT)
        start_info = tarfile.TarInfo(name="start.sh")
        start_data = start_content.encode()
        start_info.size = len(start_data)
        start_info.mode = 0o755
        tar.addfile(start_info, io.BytesIO(start_data))
    
    buf.seek(0)
    return buf.read()


def deploy_via_boto3():
    """Deploie via AWS Systems Manager (SSM) ou User Data."""
    try:
        import boto3
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=AWS_REGION
        )
        ssm = session.client("ssm")
        
        # Verifier si SSM est disponible
        try:
            response = ssm.send_command(
                InstanceIds=[INSTANCE_ID],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": ["echo 'SSM OK'"]},
                TimeoutSeconds=30,
            )
            command_id = response["Command"]["CommandId"]
            time.sleep(3)
            
            output = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=INSTANCE_ID,
            )
            if output["Status"] == "Success":
                print("[OK] SSM Agent disponible sur l'instance")
                return deploy_via_ssm(ssm)
        except Exception as e:
            print(f"[INFO] SSM non disponible: {e}")
        
        # Fallback: utiliser User Data
        print("[INFO] Utilisation du User Data pour le deploiement...")
        return deploy_via_user_data(session)
        
    except Exception as e:
        print(f"[ERREUR] Deploiement boto3: {e}")
        return False


def deploy_via_ssm(ssm):
    """Deploie via SSM SendCommand."""
    package_data = create_deployment_package()
    import base64
    b64_data = base64.b64encode(package_data).decode()
    
    commands = [
        f"mkdir -p {REMOTE_DIR}",
        f"cd {REMOTE_DIR}",
        f"echo '{b64_data}' | base64 -d | tar -xzf -",
        "chmod +x start.sh",
        "pkill -f harmonic_aws_surgery || true",
        "nohup ./start.sh > deploy.log 2>&1 &",
        "sleep 3",
        "curl -s http://localhost:{port}/health".format(port=REMOTE_PORT),
    ]
    
    response = ssm.send_command(
        InstanceIds=[INSTANCE_ID],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": commands},
        TimeoutSeconds=120,
    )
    
    command_id = response["Command"]["CommandId"]
    print(f"[INFO] Commande SSM envoyee: {command_id}")
    
    # Attendre le resultat
    for i in range(10):
        time.sleep(5)
        try:
            output = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=INSTANCE_ID,
            )
            status = output["Status"]
            if status == "Success":
                print(f"[OK] Deploiement SSM reussi!")
                if "StandardOutputContent" in output:
                    print(f"  Sortie: {output['StandardOutputContent'][:500]}")
                return True
            elif status == "Failed":
                print(f"[ERREUR] SSM: {output.get('StandardErrorContent', '')[:300]}")
                return False
            print(f"[INFO] Attente SSM... ({status})")
        except:
            pass
    
    return False


def deploy_via_user_data(session):
    """Deploie en modifiant le User Data de l'instance."""
    ec2 = session.client("ec2")
    
    # Creer le script de demarrage
    startup_script = f"""#!/bin/bash
cd /home/ubuntu
mkdir -p {REMOTE_DIR}
cd {REMOTE_DIR}

# Installer les dependances
pip install -r requirements.txt

# Lancer le proxy
nohup python harmonic_aws_surgery.py --mode serve --port {REMOTE_PORT} > harmonic-proxy.log 2>&1 &
echo "Proxy demarre"
"""
    
    # Arreter l'instance, modifier User Data, redemarrer
    print("[INFO] Arret de l'instance pour modification...")
    ec2.stop_instances(InstanceIds=[INSTANCE_ID])
    
    waiter = ec2.get_waiter("instance_stopped")
    waiter.wait(InstanceIds=[INSTANCE_ID])
    print("[OK] Instance arretee")
    
    # Modifier User Data
    ec2.modify_instance_attribute(
        InstanceId=INSTANCE_ID,
        UserData={"Value": startup_script}
    )
    print("[OK] User Data modifie")
    
    # Redemarrer
    ec2.start_instances(InstanceIds=[INSTANCE_ID])
    print("[INFO] Redemarrage de l'instance...")
    
    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[INSTANCE_ID])
    print("[OK] Instance running")
    
    # Attendre que le proxy soit pret
    print("[INFO] Attente du proxy (30s)...")
    time.sleep(30)
    
    return True


def deploy_via_paramiko():
    """Deploie via SSH avec paramiko."""
    try:
        import paramiko
    except ImportError:
        print("[ERREUR] paramiko non installe")
        return False
    
    if not os.path.exists(KEY_PATH):
        print(f"[ERREUR] Cle SSH non trouvee: {KEY_PATH}")
        return False
    
    print(f"[INFO] Connexion SSH a {EC2_DNS}...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=EC2_DNS,
            username="ubuntu",
            key_filename=KEY_PATH,
            timeout=15,
        )
        print("[OK] Connexion SSH etablie")
        
        # Creer le repertoire distant
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {REMOTE_DIR}")
        stdout.channel.recv_exit_status()
        
        # Transferer les fichiers via SFTP
        sftp = ssh.open_sftp()
        
        for filepath in FILES_TO_DEPLOY:
            if os.path.exists(filepath):
                remote_path = f"{REMOTE_DIR}/{filepath}"
                remote_dir = os.path.dirname(remote_path)
                ssh.exec_command(f"mkdir -p {remote_dir}")
                sftp.put(filepath, remote_path)
                print(f"  [OK] {filepath}")
        
        # Requirements
        with sftp.open(f"{REMOTE_DIR}/requirements.txt", "w") as f:
            f.write(REQUIREMENTS)
        print("  [OK] requirements.txt")
        
        # Script de demarrage
        start_content = START_SCRIPT.format(remote_dir=REMOTE_DIR, port=REMOTE_PORT)
        with sftp.open(f"{REMOTE_DIR}/start.sh", "w") as f:
            f.write(start_content)
        ssh.exec_command(f"chmod +x {REMOTE_DIR}/start.sh")
        print("  [OK] start.sh")
        
        sftp.close()
        
        # Installer les dependances et lancer
        print("[INFO] Installation des dependances sur EC2...")
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {REMOTE_DIR} && pip install -r requirements.txt 2>&1 | tail -5"
        )
        print(stdout.read().decode()[:300])
        
        # Lancer le proxy
        print("[INFO] Demarrage du proxy harmonique...")
        ssh.exec_command(
            f"cd {REMOTE_DIR} && nohup python harmonic_aws_surgery.py --mode serve --port {REMOTE_PORT} > harmonic-proxy.log 2>&1 &"
        )
        
        time.sleep(3)
        
        # Verifier
        stdin, stdout, stderr = ssh.exec_command(f"curl -s http://localhost:{REMOTE_PORT}/health")
        result = stdout.read().decode()
        
        if result:
            print(f"[OK] Proxy harmonique actif sur EC2!")
            print(f"  Reponse: {result[:200]}")
        else:
            # Verifier les logs
            stdin, stdout, stderr = ssh.exec_command(f"tail -20 {REMOTE_DIR}/harmonic-proxy.log")
            logs = stdout.read().decode()
            print(f"[WARN] Proxy peut ne pas etre pret. Logs:\n{logs[:500]}")
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"[ERREUR] SSH: {e}")
        return False


def check_status():
    """Verifie le statut du proxy sur EC2."""
    print(f"\n[INFO] Verification du proxy sur {EC2_DNS}:{REMOTE_PORT}...")
    
    try:
        import requests
        r = requests.get(f"http://{EC2_DNS}:{REMOTE_PORT}/health", timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"[OK] Proxy harmonique actif sur EC2!")
            print(f"  Uptime: {data.get('uptime_seconds', '?')}s")
            print(f"  Requetes: {data.get('total_requests', 0)}")
            print(f"  Erreurs: {data.get('errors', 0)}")
            print(f"  Resonance: {data.get('resonance_active', False)}")
            return True
        else:
            print(f"[WARN] Reponse HTTP {r.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"[INFO] Proxy non accessible sur {EC2_DNS}:{REMOTE_PORT}")
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    # Verifier via SSH
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=EC2_DNS, username="ubuntu", key_filename=KEY_PATH, timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command(f"cat {REMOTE_DIR}/harmonic-proxy.log 2>/dev/null || echo 'LOG_NOT_FOUND'")
        logs = stdout.read().decode()
        print(f"  Logs: {logs[:300]}")
        
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep harmonic_aws_surgery | grep -v grep")
        proc = stdout.read().decode()
        if proc:
            print(f"  Processus: {proc[:200]}")
        else:
            print("  Processus: NON TROUVE")
        
        ssh.close()
    except Exception as e:
        print(f"  SSH: {e}")
    
    return False


def main():
    parser = argparse.ArgumentParser(description="Deploiement proxy harmonique EC2 v2")
    parser.add_argument("--deploy", action="store_true", help="Deployer le proxy")
    parser.add_argument("--status", action="store_true", help="Verifier le statut")
    parser.add_argument("--method", choices=["auto", "ssh", "ssm", "userdata"], default="auto",
                       help="Methode de deploiement")
    
    args = parser.parse_args()
    
    if args.status:
        check_status()
        return
    
    if args.deploy:
        check_dependencies()
        
        method = args.method
        
        if method == "auto":
            # Essayer SSH d'abord, puis SSM, puis User Data
            if deploy_via_paramiko():
                print("\n[SUCCES] Deploiement via SSH reussi!")
            elif deploy_via_boto3():
                print("\n[SUCCES] Deploiement via AWS reussi!")
            else:
                print("\n[ECHEC] Toutes les methodes de deploiement ont echoue")
                print("  Solutions:")
                print(f"  1. Verifier que la cle SSH existe: {KEY_PATH}")
                print(f"  2. Verifier que l'instance est accessible: {EC2_DNS}")
                print(f"  3. Installer OpenSSH: https://docs.microsoft.com/fr-fr/windows-server/administration/openssh/openssh_install_firstuse")
        elif method == "ssh":
            deploy_via_paramiko()
        elif method == "ssm":
            deploy_via_boto3()
        elif method == "userdata":
            import boto3
            session = boto3.Session(region_name=AWS_REGION)
            deploy_via_user_data(session)
    else:
        parser.print_help()
        print("\nExemples:")
        print("  python deploy_harmonic_proxy_ec2_v2.py --deploy")
        print("  python deploy_harmonic_proxy_ec2_v2.py --deploy --method ssh")
        print("  python deploy_harmonic_proxy_ec2_v2.py --status")


if __name__ == "__main__":
    main()
