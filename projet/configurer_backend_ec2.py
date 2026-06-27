#!/usr/bin/env python3
"""
CONFIGURATION DU BACKEND EC2 POUR LE PROXY HARMONIQUE
=======================================================
Configure le proxy local pour utiliser l'instance EC2 comme backend.

Ce script:
1. Verifie que l'instance EC2 est running
2. Configure le .env pour le mode backend
3. Redemarre le proxy local avec le backend EC2

Usage:
    python configurer_backend_ec2.py
"""

import os, sys, json, time, subprocess, socket
from datetime import datetime

# Configuration
INSTANCE_ID = "i-0716d7805ca2c22e9"
EC2_DNS = "ec2-__EC2_IP__.compute-1.amazonaws.com"
EC2_IP = "__EC2_IP__"
LOCAL_PORT = 8080
REMOTE_PORT = 8080

ENV_PATH = ".env"
ENV_BACKUP = ".env.backup"

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


def check_ec2_status():
    """Verifie le statut de l'instance EC2."""
    header("VERIFICATION DE L'INSTANCE EC2")
    
    try:
        result = subprocess.run(
            ["aws", "ec2", "describe-instances",
             "--instance-ids", INSTANCE_ID,
             "--query", "Reservations[].Instances[].[InstanceId,State.Name,PublicDnsName,PublicIpAddress]",
             "--output", "json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            instances = json.loads(result.stdout)
            if instances:
                inst = instances[0]
                inst_id, state, dns, ip = inst
                if state == "running":
                    ok(f"Instance {inst_id} est RUNNING")
                    info(f"  DNS: {dns}")
                    info(f"  IP: {ip}")
                    return True
                else:
                    warn(f"Instance {inst_id} est {state.upper()}")
                    return False
        else:
            err(f"AWS CLI: {result.stderr[:200]}")
    except Exception as e:
        err(f"Erreur: {e}")
    return False


def check_port_open(host, port, timeout=5):
    """Verifie si un port est ouvert."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def configure_env_for_backend():
    """Configure le .env pour utiliser le backend EC2."""
    header("CONFIGURATION DU BACKEND")
    
    if not os.path.exists(ENV_PATH):
        err(f"Fichier {ENV_PATH} non trouve")
        return False
    
    # Sauvegarder
    with open(ENV_PATH) as f:
        original = f.read()
    
    with open(ENV_BACKUP, "w") as f:
        f.write(original)
    ok(f"Sauvegarde creee: {ENV_BACKUP}")
    
    # Lire et modifier
    lines = original.split("\n")
    new_lines = []
    backend_configured = False
    
    for line in lines:
        if line.startswith("BACKEND_BASE_URL="):
            new_lines.append(f"BACKEND_BASE_URL=http://{EC2_DNS}:{REMOTE_PORT}/v1")
            backend_configured = True
        elif line.startswith("GENERATION_MODE="):
            new_lines.append("GENERATION_MODE=backend")
        elif line.startswith("# BACKEND_BASE_URL="):
            new_lines.append(f"BACKEND_BASE_URL=http://{EC2_DNS}:{REMOTE_PORT}/v1")
            backend_configured = True
        else:
            new_lines.append(line)
    
    if not backend_configured:
        new_lines.append(f"\n# Backend EC2 configure le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        new_lines.append(f"BACKEND_BASE_URL=http://{EC2_DNS}:{REMOTE_PORT}/v1")
    
    with open(ENV_PATH, "w") as f:
        f.write("\n".join(new_lines))
    
    ok(f"BACKEND_BASE_URL configure: http://{EC2_DNS}:{REMOTE_PORT}/v1")
    ok("GENERATION_MODE=backend")
    
    return True


def restart_proxy():
    """Redemarre le proxy local."""
    header("REDEMARRAGE DU PROXY")
    
    # Verifier si le proxy tourne
    if check_port_open("localhost", LOCAL_PORT):
        info("Proxy actif, arret en cours...")
        # Trouver et tuer le processus
        try:
            result = subprocess.run(
                'wmic process where "commandline like \'%harmonic_aws_surgery%\'" get processid 2>&1',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line.isdigit():
                        subprocess.run(f"taskkill /F /PID {line}", shell=True, capture_output=True)
                        ok(f"Processus {line} arrete")
        except:
            pass
        time.sleep(2)
    
    # Demarrer le proxy
    info("Demarrage du proxy avec backend EC2...")
    subprocess.Popen(
        ["python", "harmonic_aws_surgery.py", "--mode", "serve", "--port", str(LOCAL_PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    
    # Attendre
    time.sleep(3)
    
    if check_port_open("localhost", LOCAL_PORT):
        ok(f"Proxy redemarre sur le port {LOCAL_PORT}")
        return True
    else:
        err("Proxy n'a pas demarre")
        return False


def test_backend_connection():
    """Teste la connexion au backend EC2."""
    header("TEST DE CONNEXION AU BACKEND")
    
    try:
        import requests
        
        # Tester le backend directement
        info(f"Test du backend EC2: http://{EC2_DNS}:{REMOTE_PORT}/health")
        try:
            r = requests.get(f"http://{EC2_DNS}:{REMOTE_PORT}/health", timeout=10)
            if r.status_code == 200:
                ok(f"Backend EC2 accessible: {r.json()}")
            else:
                warn(f"Backend EC2 repond HTTP {r.status_code}")
        except requests.exceptions.ConnectionError:
            warn(f"Backend EC2 non accessible (port {REMOTE_PORT} ferme)")
            info("  Le proxy fonctionnera en mode local uniquement")
        
        # Tester le proxy local
        info("Test du proxy local...")
        r = requests.get(f"http://localhost:{LOCAL_PORT}/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            ok(f"Proxy local actif")
            info(f"  Backend configure: {data.get('backend_configured', False)}")
            info(f"  Resonance active: {data.get('resonance_active', False)}")
            
            # Tester l'API
            r2 = requests.post(
                f"http://localhost:{LOCAL_PORT}/v1/chat/completions",
                json={
                    "model": "harmonic-proxy",
                    "messages": [{"role": "user", "content": "Dis bonjour"}],
                    "max_tokens": 30,
                },
                timeout=10
            )
            if r2.status_code == 200:
                data2 = r2.json()
                content = data2.get("choices", [{}])[0].get("message", {}).get("content", "")
                harmonic = data2.get("harmonic_analysis", {})
                ok(f"API fonctionnelle")
                info(f"  Resonance: {harmonic.get('resonance', 0):.4f}")
                info(f"  Reponse: {content[:60]}...")
            else:
                warn(f"API HTTP {r2.status_code}")
        
    except Exception as e:
        err(f"Erreur: {e}")


def show_summary():
    """Affiche le resume de la configuration."""
    header("RESUME DE LA CONFIGURATION")
    
    print(f"""
  Proxy local:     http://localhost:{LOCAL_PORT}
  Backend EC2:     http://{EC2_DNS}:{REMOTE_PORT}
  Instance:        {INSTANCE_ID}
  Mode:            {'BACKEND' if os.path.exists(ENV_PATH) and 'BACKEND_BASE_URL' in open(ENV_PATH).read() else 'LOCAL'}
  
  Commandes utiles:
    - Voir les logs:     curl http://localhost:{LOCAL_PORT}/health
    - Tester l'API:      curl -X POST http://localhost:{LOCAL_PORT}/v1/chat/completions \\
                           -H \"Content-Type: application/json\" \\
                           -d '{{\"model\":\"harmonic-proxy\",\"messages\":[{{\"role\":\"user\",\"content\":\"Bonjour\"}}]}}'
    - Stats:             curl http://localhost:{LOCAL_PORT}/stats
    - Restaurer .env:    copy {ENV_BACKUP} {ENV_PATH}
""")


def main():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}CONFIGURATION BACKEND EC2 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    
    # Etape 1: Verifier EC2
    ec2_ok = check_ec2_status()
    
    # Etape 2: Configurer .env
    if ec2_ok:
        configure_env_for_backend()
    else:
        warn("Instance EC2 non disponible, configuration en mode local")
    
    # Etape 3: Redemarrer le proxy
    restart_proxy()
    
    # Etape 4: Tester
    test_backend_connection()
    
    # Resume
    show_summary()
    
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}CONFIGURATION TERMINEE{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
