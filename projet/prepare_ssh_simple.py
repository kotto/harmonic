#!/usr/bin/env python3
"""
PREPARATION CONNEXION SSH - DEEPSEEK HARMONIC V2
Script pour resoudre les problemes de connexion SSH vers EC2
"""

import os
import sys
import subprocess
from pathlib import Path
import time

class SSHConnectionFixer:
    """Corrige les problemes de connexion SSH"""
    
    def __init__(self):
        self.instance_ip = "54.81.62.140"
        self.ssh_user = "ubuntu"
        self.possible_keys = [
            "qwen35-keypair.pem",
            "deepseek_ec2",
            "deep.pem",
            "id_rsa",
            "id_ed25519"
        ]
        self.found_key = None
        
    def find_ssh_key(self):
        """Recherche une cle SSH valide"""
        print("Recherche de cles SSH...")
        
        # Chercher dans le repertoire courant
        for key in self.possible_keys:
            if Path(key).exists():
                print(f"  CLE TROUVEE dans repertoire courant: {key}")
                self.found_key = Path(key)
                return True
        
        # Chercher dans ~/.ssh
        ssh_dir = Path.home() / ".ssh"
        if ssh_dir.exists():
            for key in self.possible_keys:
                key_path = ssh_dir / key
                if key_path.exists():
                    print(f"  CLE TROUVEE dans ~/.ssh: {key}")
                    self.found_key = key_path
                    return True
        
        print("AUCUNE CLE SSH TROUVEE")
        return False
    
    def test_ssh_connection(self):
        """Teste la connexion SSH"""
        if not self.found_key:
            print("AUCUNE CLE SSH DISPONIBLE")
            return False
        
        print(f"Test de connexion SSH vers {self.instance_ip}...")
        
        # Construire la commande SSH
        if sys.platform == "win32":
            # Windows: utiliser ssh.exe
            ssh_cmd = [
                "ssh.exe",
                "-i", str(self.found_key),
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                f"{self.ssh_user}@{self.instance_ip}",
                "echo 'CONNEXION SSH REUSSIE' && hostname"
            ]
        else:
            # Linux/Mac
            ssh_cmd = [
                "ssh",
                "-i", str(self.found_key),
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                f"{self.ssh_user}@{self.instance_ip}",
                "echo 'CONNEXION SSH REUSSIE' && hostname"
            ]
        
        try:
            print(f"  Commande: {' '.join(ssh_cmd[:6])}...")
            
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if result.returncode == 0:
                print(f"CONNEXION SSH REUSSIE!")
                print(f"  Sortie: {result.stdout.strip()}")
                return True
            else:
                print(f"ECHEC CONNEXION SSH")
                print(f"  Erreur: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            print("TIMEOUT - L'instance ne repond pas")
            return False
        except FileNotFoundError:
            print("SSH NON TROUVE. Installez OpenSSH:")
            if sys.platform == "win32":
                print("  Windows: 'Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0'")
            else:
                print("  Linux: 'sudo apt install openssh-client'")
                print("  Mac: SSH est deja installe")
            return False
        except Exception as e:
            print(f"ERREUR INATTENDUE: {e}")
            return False
    
    def check_instance_status(self):
        """Verifie le statut de l'instance EC2"""
        print("Verification du statut de l'instance...")
        
        # Essayer differentes methodes
        methods = [
            self._check_with_ping,
            self._check_with_telnet
        ]
        
        for method in methods:
            if method():
                return True
        
        return False
    
    def _check_with_ping(self):
        """Verifie avec ping"""
        try:
            if sys.platform == "win32":
                cmd = ["ping", "-n", "3", "-w", "2000", self.instance_ip]
            else:
                cmd = ["ping", "-c", "3", "-W", "2", self.instance_ip]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"  PING REUSSI vers {self.instance_ip}")
                return True
            else:
                print(f"  PING ECHOUE vers {self.instance_ip}")
                return False
                
        except:
            return False
    
    def _check_with_telnet(self):
        """Verifie avec telnet (port 22)"""
        try:
            if sys.platform == "win32":
                # Windows: utiliser Test-NetConnection
                cmd = ["powershell", "-Command", f"Test-NetConnection -ComputerName {self.instance_ip} -Port 22"]
            else:
                # Linux/Mac: utiliser nc (netcat)
                cmd = ["nc", "-z", "-w", "3", self.instance_ip, "22"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"  PORT 22 (SSH) OUVERT sur {self.instance_ip}")
                return True
            else:
                print(f"  PORT 22 FERME sur {self.instance_ip}")
                return False
                
        except:
            return False

def main():
    """Fonction principale"""
    print("=" * 60)
    print("PREPARATION CONNEXION SSH - DEEPSEEK HARMONIC V2")
    print("=" * 60)
    
    fixer = SSHConnectionFixer()
    
    # Etape 1: Trouver une cle SSH
    print("\nETAPE 1: RECHERCHE CLE SSH")
    print("-" * 30)
    
    if not fixer.find_ssh_key():
        print("\nSOLUTIONS:")
        print("1. Telechargez la cle depuis AWS Console")
        print("2. Placez-la dans le repertoire courant")
        print("3. Nommez-la 'qwen35-keypair.pem' ou 'deepseek_ec2'")
        return False
    
    # Etape 2: Verifier l'instance
    print("\nETAPE 2: VERIFICATION INSTANCE")
    print("-" * 30)
    
    if not fixer.check_instance_status():
        print("L'instance semble inaccessible")
        print("VERIFIEZ:")
        print("  - L'instance est-elle demarree?")
        print("  - Le groupe de securite autorise-t-il SSH (port 22)?")
        print("  - L'adresse IP est-elle correcte?")
    
    # Etape 3: Tester SSH
    print("\nETAPE 3: TEST CONNEXION SSH")
    print("-" * 30)
    
    if fixer.test_ssh_connection():
        print("\nCONNEXION SSH PRETE!")
    else:
        print("\nPROBLEME DE CONNEXION SSH")
        print("DEPANNAGE:")
        print("  1. Verifiez que l'instance EC2 est en etat 'running'")
        print("  2. Verifiez les groupes de securite (autoriser port 22)")
        print("  3. Verifiez le nom d'utilisateur (ubuntu pour Ubuntu AMI)")
        print("  4. Regenerer la paire de cles si necessaire")
    
    # Instructions finales
    print("\n" + "=" * 60)
    print("PREPARATION TERMINEE")
    print("=" * 60)
    
    print("\nInstructions pour utiliser SSH:")
    
    if sys.platform == "win32":
        print("1. Ouvrez PowerShell ou CMD")
        print(f"2. Connectez-vous: ssh -i {fixer.found_key} ubuntu@{fixer.instance_ip}")
    else:
        print(f"1. Connectez directement: ssh -i {fixer.found_key} ubuntu@{fixer.instance_ip}")
    
    print("\nCommandes utiles sur l'instance:")
    print("  - Verifier l'application: curl http://localhost:8000/health")
    print("  - Voir les logs: sudo journalctl -u deepseek-harmonic-v2 -f")
    print("  - Redemarrer: sudo systemctl restart deepseek-harmonic-v2")
    print("  - Statut: sudo systemctl status deepseek-harmonic-v2")
    
    print("\nLa connexion SSH est maintenant configuree.")
    print("Vous pouvez deployer la version locale avec deploy_local_to_ec2.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nINTERROMPU PAR L'UTILISATEUR")
        sys.exit(1)
    except Exception as e:
        print(f"\nERREUR: {e}")
        sys.exit(1)