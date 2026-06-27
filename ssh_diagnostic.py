#!/usr/bin/env python3
"""
Diagnostic SSH pour l'instance EC2 DeepSeek-Harmonic-V2
"""

import subprocess
import os
import time
from datetime import datetime

# Configuration
INSTANCE_IP = "54.81.62.140"
INSTANCE_USER = "ubuntu"
SSH_KEY_PATH = os.path.expanduser("~/.ssh/qwen35-keypair.pem")
SSH_KEY_PATH_ALT = os.path.expanduser("~/.ssh/deepseek_ec2")

def check_ssh_key():
    """Vérifier si la clé SSH existe"""
    print("Checking SSH keys...")
    
    keys_found = []
    
    # Vérifier la clé qwen35-keypair.pem
    if os.path.exists(SSH_KEY_PATH):
        print(f"  Found: {SSH_KEY_PATH}")
        keys_found.append(SSH_KEY_PATH)
        
        # Vérifier les permissions
        try:
            mode = os.stat(SSH_KEY_PATH).st_mode
            if mode & 0o777 != 0o600:
                print(f"  Warning: Incorrect permissions on {SSH_KEY_PATH}")
                print(f"    Current: {oct(mode & 0o777)}")
                print(f"    Should be: 600 (rw-------)")
        except:
            pass
    
    # Vérifier la clé alternative
    if os.path.exists(SSH_KEY_PATH_ALT):
        print(f"  Found: {SSH_KEY_PATH_ALT}")
        keys_found.append(SSH_KEY_PATH_ALT)
    
    if not keys_found:
        print("  ERROR: No SSH keys found")
        print("  Expected keys:")
        print(f"    - {SSH_KEY_PATH}")
        print(f"    - {SSH_KEY_PATH_ALT}")
        return None
    
    return keys_found

def test_ssh_connection(key_path):
    """Tester la connexion SSH avec une clé spécifique"""
    print(f"\nTesting SSH connection with key: {os.path.basename(key_path)}")
    
    # Construire la commande SSH
    ssh_cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        f"{INSTANCE_USER}@{INSTANCE_IP}",
        "echo 'SSH connection successful' && hostname && date"
    ]
    
    try:
        print(f"  Command: ssh -i {os.path.basename(key_path)} {INSTANCE_USER}@{INSTANCE_IP}")
        start_time = time.time()
        
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"  Time: {elapsed_time:.2f}s")
        print(f"  Exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("  SUCCESS: SSH connection established")
            print(f"  Output:\n{result.stdout}")
            return True, result.stdout
        else:
            print(f"  ERROR: SSH connection failed")
            print(f"  Stderr: {result.stderr[:200]}")
            return False, result.stderr
    
    except subprocess.TimeoutExpired:
        print("  ERROR: SSH connection timeout (15s)")
        return False, "timeout"
    except Exception as e:
        print(f"  ERROR: {str(e)[:200]}")
        return False, str(e)

def fix_ssh_permissions(key_path):
    """Corriger les permissions de la clé SSH"""
    print(f"\nFixing SSH key permissions for: {key_path}")
    
    try:
        # Sur Windows, les permissions sont différentes
        if os.name == 'nt':
            print("  Windows detected - using icacls")
            
            # Rendre la clé accessible seulement au propriétaire
            cmd = f'icacls "{key_path}" /inheritance:r /grant:r "%USERNAME%:(R)"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  Permissions fixed with icacls")
            else:
                print(f"  Error fixing permissions: {result.stderr[:200]}")
        
        else:
            # Sur Linux/Mac
            cmd = f"chmod 600 {key_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  Permissions fixed with chmod")
            else:
                print(f"  Error fixing permissions: {result.stderr[:200]}")
        
        return True
    
    except Exception as e:
        print(f"  ERROR fixing permissions: {str(e)[:200]}")
        return False

def diagnose_instance():
    """Diagnostiquer l'instance EC2"""
    print("\n" + "=" * 70)
    print("DIAGNOSING EC2 INSTANCE")
    print("=" * 70)
    
    # Vérifier les clés SSH
    ssh_keys = check_ssh_key()
    
    if not ssh_keys:
        print("\nERROR: Cannot proceed without SSH keys")
        return False
    
    # Tester chaque clé
    successful_connection = False
    connection_output = ""
    
    for key_path in ssh_keys:
        success, output = test_ssh_connection(key_path)
        
        if success:
            successful_connection = True
            connection_output = output
            break
        else:
            # Essayer de corriger les permissions
            if "permissions" in output.lower() or "too open" in output.lower():
                print("  Attempting to fix permissions...")
                if fix_ssh_permissions(key_path):
                    # Réessayer après correction des permissions
                    success, output = test_ssh_connection(key_path)
                    if success:
                        successful_connection = True
                        connection_output = output
                        break
    
    if not successful_connection:
        print("\nERROR: Could not establish SSH connection with any key")
        print("\nPossible solutions:")
        print("1. Verify the correct SSH key is in ~/.ssh/")
        print("2. Check instance security group allows SSH (port 22)")
        print("3. Ensure instance is running")
        print("4. Try different username (ubuntu, ec2-user, admin)")
        return False
    
    # Si la connexion SSH réussit, exécuter des commandes de diagnostic
    print("\n" + "=" * 70)
    print("RUNNING DIAGNOSTIC COMMANDS ON INSTANCE")
    print("=" * 70)
    
    diagnostic_commands = [
        "whoami",
        "pwd",
        "ls -la /opt/",
        "ls -la /opt/qwen35/",
        "systemctl status qwen35.service --no-pager",
        "ps aux | grep -E '(python|uvicorn|qwen)'",
        "netstat -tlnp | grep :8000",
        "cat /opt/qwen35/app/main.py 2>/dev/null | head -50",
        "ls -la /opt/qwen35/model/ 2>/dev/null"
    ]
    
    diagnostic_results = {}
    
    for cmd in diagnostic_commands:
        print(f"\nCommand: {cmd}")
        
        ssh_cmd = [
            "ssh",
            "-i", ssh_keys[0],  # Utiliser la première clé qui a fonctionné
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            f"{INSTANCE_USER}@{INSTANCE_IP}",
            cmd
        ]
        
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"  Output:\n{result.stdout[:500]}")
                diagnostic_results[cmd] = {
                    "success": True,
                    "output": result.stdout[:1000]
                }
            else:
                print(f"  Error (code {result.returncode}): {result.stderr[:200]}")
                diagnostic_results[cmd] = {
                    "success": False,
                    "error": result.stderr[:500]
                }
                
        except subprocess.TimeoutExpired:
            print("  Timeout")
            diagnostic_results[cmd] = {
                "success": False,
                "error": "timeout"
            }
        except Exception as e:
            print(f"  Exception: {str(e)[:200]}")
            diagnostic_results[cmd] = {
                "success": False,
                "error": str(e)[:500]
            }
    
    return diagnostic_results

def generate_report(diagnostic_results):
    """Générer un rapport de diagnostic"""
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC REPORT - DEEPSEEK-HARMONIC-V2")
    print("=" * 70)
    
    if not diagnostic_results:
        print("ERROR: No diagnostic results available")
        return
    
    # Analyser les résultats
    print("\nANALYSIS:")
    print("-" * 70)
    
    # Vérifier le service
    service_status = None
    for cmd, result in diagnostic_results.items():
        if "systemctl status" in cmd and result["success"]:
            output = result["output"]
            if "active (running)" in output:
                service_status = "running"
            elif "inactive" in output:
                service_status = "stopped"
            elif "failed" in output:
                service_status = "failed"
    
    if service_status == "running":
        print("✓ Service qwen35.service is running")
    elif service_status == "stopped":
        print("⚠ Service qwen35.service is stopped")
    elif service_status == "failed":
        print("✗ Service qwen35.service has failed")
    else:
        print("? Service status unknown")
    
    # Vérifier le port
    port_listening = False
    for cmd, result in diagnostic_results.items():
        if "netstat" in cmd and result["success"]:
            if ":8000" in result["output"]:
                port_listening = True
    
    if port_listening:
        print("✓ Port 8000 is listening")
    else:
        print("⚠ Port 8000 is not listening")
    
    # Vérifier les fichiers de modèle
    model_files = False
    for cmd, result in diagnostic_results.items():
        if "model/" in cmd and result["success"]:
            if "total" in result["output"].lower() or any(ext in result["output"] for ext in [".bin", ".pt", ".pth", ".safetensors"]):
                model_files = True
    
    if model_files:
        print("✓ Model files found")
    else:
        print("⚠ No model files found")
    
    # Recommandations
    print("\nRECOMMENDATIONS:")
    print("-" * 70)
    
    if service_status != "running":
        print("1. Start the service:")
        print("   sudo systemctl start qwen35.service")
    
    if not port_listening and service_status == "running":
        print("2. Check service configuration and logs:")
        print("   sudo journalctl -u qwen35.service -f")
    
    if not model_files:
        print("3. Download model files:")
        print("   Check /opt/qwen35/model/ directory")
    
    # Si tout semble OK mais l'API retourne des mocks
    if service_status == "running" and port_listening:
        print("\n4. The service is running but returning mock responses.")
        print("   Possible solutions:")
        print("   a. Check if the model is properly loaded")
        print("   b. Review the API code in /opt/qwen35/app/main.py")
        print("   c. Restart the service: sudo systemctl restart qwen35.service")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("-" * 70)
    
    print("1. SSH into the instance:")
    print(f"   ssh -i ~/.ssh/qwen35-keypair.pem ubuntu@54.81.62.140")
    
    print("\n2. Check service logs:")
    print("   sudo journalctl -u qwen35.service -f")
    
    print("\n3. Test API locally:")
    print("   curl http://localhost:8000/generate \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"prompt\":\"Test\",\"max_tokens\":50}'")
    
    print("\n4. If mock responses continue, check:")
    print("   - Model loading in /opt/qwen35/app/main.py")
    print("   - Configuration files")
    print("   - Disk space and memory usage")

def main():
    """Fonction principale"""
    
    print("SSH DIAGNOSTIC FOR EC2 INSTANCE")
    print("=" * 70)
    print(f"Instance: DeepSeek-Harmonic-V2")
    print(f"IP Address: {INSTANCE_IP}")
    print(f"Username: {INSTANCE_USER}")
    print("=" * 70)
    
    # Diagnostiquer l'instance
    diagnostic_results = diagnose_instance()
    
    if diagnostic_results:
        # Générer le rapport
        generate_report(diagnostic_results)
        
        # Sauvegarder les résultats
        output_file = f"ssh_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "instance_ip": INSTANCE_IP,
            "instance_user": INSTANCE_USER,
            "ssh_key_used": "~/.ssh/qwen35-keypair.pem",
            "diagnostic_results": diagnostic_results
        }
        
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nReport saved to: {output_file}")
    else:
        print("\nERROR: Diagnostic failed")
        print("\nManual steps required:")
        print("1. Verify SSH key exists: ~/.ssh/qwen35-keypair.pem")
        print("2. Check instance security group allows SSH")
        print("3. Ensure instance is running in AWS Console")

if __name__ == "__main__":
    main()