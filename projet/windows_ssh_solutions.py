#!/usr/bin/env python3
"""
Solutions SSH pour Windows - Guide étape par étape
"""

import os
import sys
import subprocess

def display_solutions():
    """Afficher les solutions SSH pour Windows"""
    
    print("=" * 80)
    print("SOLUTIONS SSH POUR WINDOWS")
    print("=" * 80)
    print()
    
    print("PROBLÈME: 'ssh' n'est pas reconnu dans PowerShell")
    print("SOLUTIONS DISPONIBLES:")
    print()
    
    print("OPTION 1: Installer OpenSSH Client (Recommandé)")
    print("-" * 40)
    print("1. Ouvrir PowerShell en administrateur")
    print("2. Exécuter cette commande:")
    print("   Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0")
    print("3. Redémarrer PowerShell")
    print("4. Tester: ssh -V")
    print()
    
    print("OPTION 2: Utiliser le chemin complet")
    print("-" * 40)
    print("SSH est peut-être déjà installé mais pas dans le PATH")
    print("Essayer ces commandes:")
    print()
    print("Méthode A: Avec chemin complet")
    print(r'  C:\Windows\System32\OpenSSH\ssh.exe -i C:\Users\maatc\.ssh\deepseek_ec2 ubuntu@54.81.62.140')
    print()
    print("Méthode B: Ajouter au PATH temporairement")
    print(r'  $env:Path += ";C:\Windows\System32\OpenSSH"')
    print(r'  ssh -i C:\Users\maatc\.ssh\deepseek_ec2 ubuntu@54.81.62.140')
    print()
    
    print("OPTION 3: Utiliser PuTTY (Alternative populaire)")
    print("-" * 40)
    print("1. Télécharger PuTTY: https://www.putty.org/")
    print("2. Télécharger PuTTYgen (pour convertir les clés)")
    print("3. Convertir la clé .pem en .ppk:")
    print("   - Ouvrir PuTTYgen")
    print("   - Load > Sélectionner deepseek_ec2")
    print("   - Save private key > deepseek_ec2.ppk")
    print("4. Ouvrir PuTTY:")
    print("   - Host: 54.81.62.140")
    print("   - Port: 22")
    print("   - Connection > SSH > Auth > Browse > sélectionner .ppk")
    print("   - Open")
    print()
    
    print("OPTION 4: Windows Subsystem for Linux (WSL)")
    print("-" * 40)
    print("1. Installer WSL:")
    print("   wsl --install")
    print("2. Ouvrir Ubuntu")
    print("3. Copier la clé dans WSL:")
    print(r'   cp /mnt/c/Users/maatc/.ssh/deepseek_ec2 ~/.ssh/')
    print("4. Utiliser SSH normalement:")
    print("   ssh -i ~/.ssh/deepseek_ec2 ubuntu@54.81.62.140")
    print()
    
    print("=" * 80)
    print("COMMANDES DE TEST")
    print("=" * 80)
    print()
    
    print("Pour vérifier si SSH est installé:")
    print("1. Vérifier le fichier:")
    print(r'   Test-Path C:\Windows\System32\OpenSSH\ssh.exe')
    print()
    print("2. Vérifier les fonctionnalités Windows:")
    print("   Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'")
    print()
    print("3. Si SSH est installé mais pas reconnu:")
    print(r'   & "C:\Windows\System32\OpenSSH\ssh.exe" -V')
    print()
    
    print("=" * 80)
    print("SOLUTION RAPIDE POUR VOUS")
    print("=" * 80)
    print()
    
    print("Essayez d'abord cette commande dans PowerShell Admin:")
    print("-" * 60)
    print(r'& "C:\Windows\System32\OpenSSH\ssh.exe" -i C:\Users\maatc\.ssh\deepseek_ec2 ubuntu@54.81.62.140')
    print("-" * 60)
    print()
    
    print("Si ça ne marche pas, installez OpenSSH:")
    print("-" * 60)
    print("Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0")
    print("-" * 60)
    print()
    
    print("Instructions détaillées:")
    print("1. Ouvrir PowerShell en administrateur")
    print("2. Copier-coller la commande d'installation")
    print("3. Attendre l'installation (peut prendre 1-2 minutes)")
    print("4. Redémarrer PowerShell")
    print("5. Tester: ssh -V")
    print("6. Se connecter à EC2")
    print()

def check_ssh_installation():
    """Vérifier l'installation SSH"""
    
    print("\nVÉRIFICATION DE L'INSTALLATION SSH...")
    print("-" * 40)
    
    # Vérifier le fichier ssh.exe
    ssh_path = r"C:\Windows\System32\OpenSSH\ssh.exe"
    
    if os.path.exists(ssh_path):
        print(f"[OK] SSH.exe trouvé: {ssh_path}")
        
        # Vérifier la version
        try:
            result = subprocess.run(
                [ssh_path, "-V"],
                capture_output=True,
                text=True,
                timeout=5
            )
            print(f"   Version: {result.stderr.strip()}")
        except:
            print("   Impossible d'obtenir la version")
    else:
        print("[ERREUR] SSH.exe non trouvé")
        print("   SSH n'est pas installé ou est dans un autre emplacement")
    
    # Vérifier via PowerShell
    print("\nVérification via PowerShell...")
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Command ssh -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("[OK] SSH disponible via PowerShell")
        else:
            print("[ERREUR] SSH non disponible via PowerShell")
            
    except Exception as e:
        print(f"[ERREUR] {e}")

def main():
    """Fonction principale"""
    
    display_solutions()
    check_ssh_installation()
    
    print("\n" + "=" * 80)
    print("ACTION REQUISE:")
    print("=" * 80)
    print()
    print("1. Ouvrez PowerShell en administrateur")
    print("2. Essayez la commande avec le chemin complet:")
    print(r'   & "C:\Windows\System32\OpenSSH\ssh.exe" -i C:\Users\maatc\.ssh\deepseek_ec2 ubuntu@54.81.62.140')
    print()
    print("3. Si ça ne marche pas, installez OpenSSH:")
    print("   Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0")
    print()
    print("4. Revenez ici une fois connecté à EC2")
    print()

if __name__ == "__main__":
    main()