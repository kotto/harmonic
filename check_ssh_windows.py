#!/usr/bin/env python3
"""
Vérifier et installer SSH sur Windows
"""

import os
import sys
import subprocess

def check_ssh_installation():
    """Vérifier si SSH est installé sur Windows"""
    
    print("VERIFICATION SSH WINDOWS")
    print("=" * 60)
    print()
    
    # Méthode 1: Vérifier si ssh.exe existe
    print("1. Vérification de ssh.exe...")
    
    # Chemins possibles pour ssh
    possible_paths = [
        r"C:\Windows\System32\OpenSSH\ssh.exe",
        r"C:\Windows\System32\ssh.exe",
        r"C:\Program Files\OpenSSH\ssh.exe"
    ]
    
    ssh_found = False
    ssh_path = None
    
    for path in possible_paths:
        if os.path.exists(path):
            ssh_found = True
            ssh_path = path
            print(f"   [OK] SSH trouvé: {path}")
            break
    
    if not ssh_found:
        print("   [ERREUR] SSH non trouvé")
    
    # Méthode 2: Vérifier via PowerShell
    print("\n2. Vérification via PowerShell...")
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Command ssh -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("   [OK] SSH disponible via PowerShell")
            print(f"   Sortie: {result.stdout.strip()}")
        else:
            print("   [ERREUR] SSH non disponible via PowerShell")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    # Méthode 3: Vérifier les fonctionnalités Windows
    print("\n3. Vérification des fonctionnalités Windows...")
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 2:
                print("   [INFO] Fonctionnalités OpenSSH:")
                for line in lines[2:]:  # Skip header
                    if "OpenSSH" in line:
                        print(f"   {line.strip()}")
            else:
                print("   [INFO] Aucune fonctionnalité OpenSSH trouvée")
        else:
            print("   [ERREUR] Impossible de vérifier les fonctionnalités")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    print("\n" + "=" * 60)
    print("CONCLUSION ET SOLUTIONS")
    print("=" * 60)
    
    if ssh_found:
        print("[OK] SSH est installé")
        print()
        print("Pour vous connecter à EC2:")
        print("1. Ouvrir PowerShell en administrateur")
        print("2. Exécuter:")
        print(f"   {ssh_path} -i C:\\Users\\maatc\\.ssh\\deepseek_ec2 ubuntu@54.81.62.140")
        print()
        print("Si ça ne marche pas, essayer avec l'autre clé:")
        print(f"   {ssh_path} -i C:\\Users\\maatc\\.ssh\\qwen35-keypair.pem ubuntu@54.81.62.140")
    else:
        print("[ERREUR] SSH n'est pas installé")
        print()
        print("SOLUTIONS:")
        print()
        print("OPTION A: Installer OpenSSH (Recommandé)")
        print("1. Ouvrir PowerShell en administrateur")
        print("2. Exécuter:")
        print("   Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0")
        print("3. Redémarrer PowerShell")
        print()
        print("OPTION B: Utiliser PuTTY")
        print("1. Télécharger PuTTY: https://www.putty.org/")
        print("2. Télécharger PuTTYgen (pour convertir les clés)")
        print("3. Convertir la clé .pem en .ppk avec PuTTYgen")
        print("4. Se connecter avec PuTTY:")
        print("   - Host: 54.81.62.140")
        print("   - Port: 22")
        print("   - Connection > SSH > Auth > Browse > sélectionner .ppk")
        print()
        print("OPTION C: Utiliser WSL (Windows Subsystem for Linux)")
        print("1. Installer WSL: wsl --install")
        print("2. Ouvrir Ubuntu")
        print("3. Copier la clé dans WSL:")
        print("   cp /mnt/c/Users/maatc/.ssh/deepseek_ec2 ~/.ssh/")
        print("4. Utiliser SSH normalement")
    
    print("\n" + "=" * 60)
    print("COMMANDES DE TEST")
    print("=" * 60)
    print()
    print("Pour tester la connexion (une fois SSH installé):")
    print("ssh -i C:\\Users\\maatc\\.ssh\\deepseek_ec2 ubuntu@54.81.62.140 'echo \"Test SSH réussi\"'")
    print()
    print("Si vous obtenez 'Permission denied (publickey)':")
    print("1. Vérifier les permissions de la clé:")
    print("   icacls C:\\Users\\maatc\\.ssh\\deepseek_ec2 /inheritance:r")
    print("   icacls C:\\Users\\maatc\\.ssh\\deepseek_ec2 /grant:r \"%USERNAME%:R\"")
    print("2. Essayer avec l'autre clé")
    print("3. Vérifier que l'instance EC2 est 'running'")
    print()

def main():
    """Fonction principale"""
    check_ssh_installation()

if __name__ == "__main__":
    main()