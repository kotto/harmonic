#!/usr/bin/env python3
"""
TRANSFER FILE WITH PARAMIKO - Windows compatible
Transfert de fichier vers EC2 sans utiliser scp
"""

import os
import sys
import paramiko
from datetime import datetime

def transfer_file_with_paramiko():
    """Transferer le fichier API vers EC2 avec paramiko"""
    
    # Configuration
    instance_ip = "54.81.62.140"
    ssh_user = "ubuntu"
    ssh_key_path = os.path.expanduser("~/.ssh/deepseek_ec2")
    local_file = "deepseek_api_real_paramiko.py"
    remote_dir = "/home/ubuntu"
    remote_file = os.path.join(remote_dir, "deepseek_api_real.py")
    
    print("=" * 60)
    print("TRANSFERT DE FICHIER VERS EC2 - PARAMIKO")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Instance: {instance_ip}")
    print(f"Utilisateur: {ssh_user}")
    print(f"Clé SSH: {ssh_key_path}")
    print(f"Fichier local: {local_file}")
    print(f"Destination: {remote_file}")
    print()
    
    # Verifier si le fichier local existe
    if not os.path.exists(local_file):
        print(f"ERREUR: Le fichier local '{local_file}' n'existe pas.")
        print("Fichiers disponibles:")
        for f in os.listdir("."):
            if f.endswith(".py"):
                print(f"  - {f}")
        return False
    
    # Verifier si la clé SSH existe
    if not os.path.exists(ssh_key_path):
        print(f"ERREUR: La clé SSH '{ssh_key_path}' n'existe pas.")
        print("Clés SSH disponibles dans ~/.ssh/:")
        ssh_dir = os.path.expanduser("~/.ssh")
        if os.path.exists(ssh_dir):
            for f in os.listdir(ssh_dir):
                print(f"  - {f}")
        return False
    
    try:
        # Lire la clé SSH
        print("Lecture de la clé SSH...")
        key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
        
        # Creer client SSH
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Se connecter
        print(f"Connexion à {instance_ip}...")
        client.connect(
            hostname=instance_ip,
            username=ssh_user,
            pkey=key,
            timeout=15
        )
        
        print("Connexion SSH établie.")
        
        # Transferer le fichier avec SFTP
        print("Transfert du fichier...")
        sftp = client.open_sftp()
        
        # Verifier si le repertoire distant existe
        try:
            sftp.stat(remote_dir)
            print(f"Répertoire distant '{remote_dir}' existe.")
        except:
            print(f"Création du répertoire '{remote_dir}'...")
            sftp.mkdir(remote_dir)
        
        # Transferer le fichier
        sftp.put(local_file, remote_file)
        sftp.close()
        
        # Verifier que le fichier a été transféré
        stdin, stdout, stderr = client.exec_command(f"ls -la {remote_file}")
        file_info = stdout.read().decode().strip()
        
        if file_info:
            print(f"Fichier transféré avec succès: {remote_file}")
            print(f"Infos: {file_info}")
            
            # Donner les permissions d'exécution
            print("Donner les permissions d'exécution...")
            stdin, stdout, stderr = client.exec_command(f"chmod +x {remote_file}")
            stdout.read()
            
            # Verifier les permissions
            stdin, stdout, stderr = client.exec_command(f"ls -la {remote_file}")
            permissions = stdout.read().decode().strip()
            print(f"Permissions: {permissions}")
            
            # Tester si le fichier peut être exécuté
            print("Test d'exécution...")
            stdin, stdout, stderr = client.exec_command(f"python3 {remote_file} --version 2>&1 || echo 'Test execution'")
            test_output = stdout.read().decode().strip()
            
            if test_output:
                print(f"Test réussi: {test_output[:100]}...")
            else:
                print("Test d'exécution effectué.")
            
            client.close()
            
            print("\n" + "=" * 60)
            print("TRANSFERT RÉUSSI !")
            print("=" * 60)
            print()
            print("Prochaines étapes:")
            print("1. Se connecter à EC2:")
            print(f"   ssh -i {ssh_key_path} {ssh_user}@{instance_ip}")
            print()
            print("2. Installer les dépendances:")
            print("   pip3 install fastapi uvicorn pydantic")
            print()
            print("3. Démarrer l'API:")
            print(f"   python3 {remote_file}")
            print()
            print("4. Tester depuis votre PC:")
            print("   http://54.81.62.140:8000/health")
            
            return True
            
        else:
            print("ERREUR: Impossible de vérifier le transfert.")
            client.close()
            return False
            
    except paramiko.AuthenticationException:
        print("ERREUR: Échec d'authentification SSH.")
        print("Vérifiez:")
        print("1. La clé SSH est correcte")
        print("2. L'utilisateur est 'ubuntu'")
        print("3. La clé est associée à l'instance")
        return False
        
    except paramiko.SSHException as e:
        print(f"ERREUR SSH: {e}")
        print("Vérifiez:")
        print("1. L'instance EC2 est démarrée")
        print("2. Les groupes de sécurité autorisent le port 22")
        print("3. La connexion réseau est établie")
        return False
        
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

def main():
    """Fonction principale"""
    print("TRANSFERT DE FICHIER VERS EC2 - SOLUTION WINDOWS")
    print()
    
    success = transfer_file_with_paramiko()
    
    if success:
        print("\n✅ TRANSFERT EFFECTUÉ AVEC SUCCÈS")
        print("Le fichier API réel a été transféré sur EC2.")
        print("Suivez les instructions ci-dessus pour compléter le déploiement.")
    else:
        print("\n❌ ÉCHEC DU TRANSFERT")
        print("Le transfert a échoué. Solutions alternatives:")
        print("1. Utiliser WinSCP (interface graphique)")
        print("2. Utiliser FileZilla avec SFTP")
        print("3. Copier manuellement le contenu via SSH")
        print()
        print("Pour copier manuellement:")
        print(f"1. Ouvrez {ssh_key_path} dans un éditeur")
        print(f"2. Copiez le contenu de deepseek_api_real_paramiko.py")
        print("3. Connectez-vous à EC2 via SSH")
        print("4. Créez le fichier avec nano ou vim")
        print("5. Collez le contenu et sauvegardez")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)