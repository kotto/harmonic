#!/usr/bin/env python3
"""
🔧 PRÉPARATION CONNEXION SSH - DEEPSEEK HARMONIC V2
Script pour résoudre les problèmes de connexion SSH vers EC2
"""

import os
import sys
import subprocess
from pathlib import Path
import stat
import time

class SSHConnectionFixer:
    """Corrige les problèmes de connexion SSH"""
    
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
        
    def find_ssh_key(self) -> bool:
        """Recherche une clé SSH valide"""
        print("🔍 Recherche de clés SSH...")
        
        # Chercher dans le répertoire courant
        for key in self.possible_keys:
            if Path(key).exists():
                print(f"  ✅ Clé trouvée dans répertoire courant: {key}")
                self.found_key = Path(key)
                return True
        
        # Chercher dans ~/.ssh
        ssh_dir = Path.home() / ".ssh"
        if ssh_dir.exists():
            for key in self.possible_keys:
                key_path = ssh_dir / key
                if key_path.exists():
                    print(f"  ✅ Clé trouvée dans ~/.ssh: {key}")
                    self.found_key = key_path
                    return True
        
        print("❌ Aucune clé SSH trouvée")
        return False
    
    def fix_key_permissions(self) -> bool:
        """Corrige les permissions de la clé SSH"""
        if not self.found_key:
            print("❌ Aucune clé à corriger")
            return False
        
        print(f"🔧 Correction des permissions pour: {self.found_key}")
        
        try:
            # Windows: pas besoin de chmod, mais vérifier l'existence
            if sys.platform == "win32":
                if not self.found_key.exists():
                    print(f"❌ Fichier non trouvé: {self.found_key}")
                    return False
                
                # Sur Windows, les permissions sont différentes
                print(f"  ✅ Clé accessible sur Windows: {self.found_key}")
                return True
            else:
                # Linux/Mac: corriger les permissions
                self.found_key.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600
                print(f"  ✅ Permissions corrigées: 600")
                return True
                
        except Exception as e:
            print(f"❌ Erreur correction permissions: {e}")
            return False
    
    def test_ssh_connection(self) -> bool:
        """Teste la connexion SSH"""
        if not self.found_key:
            print("❌ Aucune clé SSH disponible")
            return False
        
        print(f"🔗 Test de connexion SSH vers {self.instance_ip}...")
        
        # Construire la commande SSH
        if sys.platform == "win32":
            # Windows: utiliser ssh.exe
            ssh_cmd = [
                "ssh.exe",
                "-i", str(self.found_key),
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                f"{self.ssh_user}@{self.instance_ip}",
                "echo '✅ Connexion SSH réussie' && hostname"
            ]
        else:
            # Linux/Mac
            ssh_cmd = [
                "ssh",
                "-i", str(self.found_key),
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                f"{self.ssh_user}@{self.instance_ip}",
                "echo '✅ Connexion SSH réussie' && hostname"
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
                print(f"✅ Connexion SSH réussie!")
                print(f"  Sortie: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ Échec connexion SSH")
                print(f"  Erreur: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Timeout - L'instance ne répond pas")
            return False
        except FileNotFoundError:
            print("❌ SSH non trouvé. Installez OpenSSH:")
            if sys.platform == "win32":
                print("  • Windows: 'Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0'")
            else:
                print("  • Linux: 'sudo apt install openssh-client'")
                print("  • Mac: SSH est déjà installé")
            return False
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return False
    
    def check_instance_status(self) -> bool:
        """Vérifie le statut de l'instance EC2"""
        print("📊 Vérification du statut de l'instance...")
        
        # Essayer différentes méthodes
        methods = [
            self._check_with_ping,
            self._check_with_telnet,
            self._check_with_nmap
        ]
        
        for method in methods:
            if method():
                return True
        
        return False
    
    def _check_with_ping(self) -> bool:
        """Vérifie avec ping"""
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
                print(f"  ✅ Ping réussi vers {self.instance_ip}")
                return True
            else:
                print(f"  ❌ Ping échoué vers {self.instance_ip}")
                return False
                
        except:
            return False
    
    def _check_with_telnet(self) -> bool:
        """Vérifie avec telnet (port 22)"""
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
                print(f"  ✅ Port 22 (SSH) ouvert sur {self.instance_ip}")
                return True
            else:
                print(f"  ❌ Port 22 fermé sur {self.instance_ip}")
                return False
                
        except:
            return False
    
    def _check_with_nmap(self) -> bool:
        """Vérifie avec nmap si disponible"""
        try:
            # Vérifier si nmap est installé
            subprocess.run(["nmap", "--version"], capture_output=True, check=True)
            
            cmd = ["nmap", "-p", "22", "-Pn", self.instance_ip]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if "22/tcp open" in result.stdout:
                print(f"  ✅ Nmap: Port SSH ouvert")
                return True
            else:
                print(f"  ❌ Nmap: Port SSH fermé")
                return False
                
        except:
            return False
    
    def generate_ssh_config(self) -> str:
        """Génère un fichier de configuration SSH"""
        if not self.found_key:
            return "# Aucune clé SSH trouvée"
        
        config = f"""# Configuration SSH pour DeepSeek Harmonic V2
Host deepseek-harmonic-v2
    HostName {self.instance_ip}
    User {self.ssh_user}
    IdentityFile {self.found_key}
    StrictHostKeyChecking no
    ConnectTimeout 10
    ServerAliveInterval 60
    ServerAliveCountMax 3
    
# Commandes utiles
# ssh deepseek-harmonic-v2
# scp -r local_folder deepseek-harmonic-v2:remote_path/
"""
        return config
    
    def create_ssh_script(self) -> Path:
        """Crée un script SSH simplifié"""
        script_content = f"""#!/bin/bash
# Script SSH pour DeepSeek Harmonic V2

INSTANCE_IP="{self.instance_ip}"
SSH_USER="{self.ssh_user}"
SSH_KEY="{self.found_key}"

echo "🚀 Connexion à DeepSeek Harmonic V2..."
echo "IP: $INSTANCE_IP"
echo "Utilisateur: $SSH_USER"
echo "Clé: $SSH_KEY"

# Test de connexion
echo "🔍 Test de connexion..."
ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SSH_USER@$INSTANCE_IP" "echo '✅ Connexion réussie' && hostname"

if [ $? -eq 0 ]; then
    echo "✅ Connexion SSH établie"
    
    # Options
    echo ""
    echo "📋 Options disponibles:"
    echo "1. Se connecter en SSH"
    echo "2. Vérifier le statut de l'application"
    echo "3. Voir les logs"
    echo "4. Redémarrer le service"
    echo "5. Copier des fichiers"
    
    read -p "Choisir une option (1-5): " choice
    
    case $choice in
        1)
            echo "🔗 Connexion SSH..."
            ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$INSTANCE_IP"
            ;;
        2)
            echo "📊 Statut de l'application..."
            ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$INSTANCE_IP" "curl -s http://localhost:8000/health"
            ;;
        3)
            echo "📝 Logs du service..."
            ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$INSTANCE_IP" "sudo journalctl -u deepseek-harmonic-v2 -n 20"
            ;;
        4)
            echo "🔄 Redémarrage du service..."
            ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$INSTANCE_IP" "sudo systemctl restart deepseek-harmonic-v2"
            echo "Service redémarré"
            ;;
        5)
            read -p "Fichier local à copier: " local_file
            read -p "Chemin distant: " remote_path
            echo "📤 Copie de $local_file vers $remote_path..."
            scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$local_file" "$SSH_USER@$INSTANCE_IP:$remote_path"
            ;;
        *)
            echo "❌ Option invalide"
            ;;
    esac
    
else
    echo "❌ Échec de la connexion SSH"
    exit 1
fi
"""
        
        script_path = Path("connect_deepseek.sh")
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        if sys.platform != "win32":
            script_path.chmod(0o755)
        
        return script_path

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔧 PRÉPARATION CONNEXION SSH - DEEPSEEK HARMONIC V2")
    print("=" * 60)
    
    fixer = SSHConnectionFixer()
    
    # Étape 1: Trouver une clé SSH
    print("\n📋 ÉTAPE 1: RECHERCHE CLÉ SSH")
    print("-" * 30)
    
    if not fixer.find_ssh_key():
        print("\n💡 Solutions:")
        print("1. Téléchargez la clé depuis AWS Console")
        print("2. Placez-la dans le répertoire courant")
        print("3. Nommez-la 'qwen35-keypair.pem' ou 'deepseek_ec2'")
        return False
    
    # Étape 2: Corriger les permissions
    print("\n📋 ÉTAPE 2: CORRECTION PERMISSIONS")
    print("-" * 30)
    
    fixer.fix_key_permissions()
    
    # Étape 3: Vérifier l'instance
    print("\n📋 ÉTAPE 3: VÉRIFICATION INSTANCE")
    print("-" * 30)
    
    if not fixer.check_instance_status():
        print("⚠️ L'instance semble inaccessible")
        print("💡 Vérifiez:")
        print("  • L'instance est-elle démarrée?")
        print("  • Le groupe de sécurité autorise-t-il SSH (port 22)?")
        print("  • L'adresse IP est-elle correcte?")
    
    # Étape 4: Tester SSH
    print("\n📋 ÉTAPE 4: TEST CONNEXION SSH")
    print("-" * 30)
    
    if fixer.test_ssh_connection():
        print("\n✅ Connexion SSH prête!")
    else:
        print("\n❌ Problème de connexion SSH")
        print("💡 Dépannage:")
        print("  1. Vérifiez que l'instance EC2 est en état 'running'")
        print("  2. Vérifiez les groupes de sécurité (autoriser port 22)")
        print("  3. Vérifiez le nom d'utilisateur (ubuntu pour Ubuntu AMI)")
        print("  4. Regénérez la paire de clés si nécessaire")
    
    # Étape 5: Générer la configuration
    print("\n📋 ÉTAPE 5: CONFIGURATION SSH")
    print("-" * 30)
    
    ssh_config = fixer.generate_ssh_config()
    print("📄 Configuration SSH générée:")
    print(ssh_config)
    
    # Sauvegarder la configuration
    config_path = Path("deepseek_ssh_config.txt")
    with open(config_path, 'w') as f:
        f.write(ssh_config)
    print(f"  💾 Sauvegardé dans: {config_path}")
    
    # Étape 6: Créer un script de connexion
    print("\n📋 ÉTAPE 6: SCRIPT DE CONNEXION")
    print("-" * 30)
    
    script_path = fixer.create_ssh_script()
    print(f"📜 Script de connexion créé: {script_path}")
    
    # Instructions finales
    print("\n" + "=" * 60)
    print("🎯 PRÉPARATION TERMINÉE")
    print("=" * 60)
    
    print("\n📋 Instructions pour utiliser SSH:")
    
    if sys.platform == "win32":
        print("1. Ouvrez PowerShell ou CMD")
        print(f"2. Connectez-vous: ssh -i {fixer.found_key} ubuntu@{fixer.instance_ip}")
        print("3. Ou utilisez le script: .\\connect_deepseek.sh")
    else:
        print("1. Rendez le script exécutable: chmod +x connect_deepseek.sh")
        print("2. Exécutez: ./connect_deepseek.sh")
        print(f"3. Ou connectez directement: ssh -i {fixer.found_key} ubuntu@{fixer.instance_ip}")
    
    print("\n🔧 Commandes utiles sur l'instance:")
    print("  • Vérifier l'application: curl http://localhost:8000/health")
    print("  • Voir les logs: sudo journalctl -u deepseek-harmonic-v2 -f")
    print("  • Redémarrer: sudo systemctl restart deepseek-harmonic-v2")
    print("  • Statut: sudo systemctl status deepseek-harmonic-v2")
    
    print("\n✅ La connexion SSH est maintenant configurée.")
    print("   Vous pouvez déployer la version locale avec deploy_local_to_ec2.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)