#!/usr/bin/env python3
"""
Résoudre les problèmes de permissions SSH sur Windows
"""

import os
import subprocess
import sys

def fix_ssh_permissions():
    """Corriger les permissions des clés SSH"""
    
    print("=" * 80)
    print("RÉSOLUTION DES PROBLÈMES DE PERMISSIONS SSH")
    print("=" * 80)
    print()
    
    # Chemins des clés SSH
    key1 = r"C:\Users\maatc\.ssh\deepseek_ec2"
    key2 = r"C:\Users\maatc\.ssh\qwen35-keypair.pem"
    
    print("1. VÉRIFICATION DES CLÉS SSH")
    print("-" * 40)
    
    keys_found = []
    
    for key_path in [key1, key2]:
        if os.path.exists(key_path):
            keys_found.append(key_path)
            print(f"[OK] Clé trouvée: {key_path}")
            
            # Vérifier le format
            try:
                with open(key_path, 'r') as f:
                    first_line = f.readline().strip()
                    if "BEGIN" in first_line and "PRIVATE KEY" in first_line:
                        print(f"   Format: Correct (clé privée)")
                    elif "ssh-rsa" in first_line or "ssh-ed25519" in first_line:
                        print(f"   Format: Clé publique")
                    else:
                        print(f"   Format: Inconnu")
            except Exception as e:
                print(f"   Erreur lecture: {e}")
        else:
            print(f"[ABSENT] {key_path}")
    
    print()
    print("2. CORRECTION DES PERMISSIONS")
    print("-" * 40)
    
    if not keys_found:
        print("[ERREUR] Aucune clé SSH trouvée")
        return False
    
    print("Exécution des commandes de correction...")
    print()
    
    for key_path in keys_found:
        print(f"Correction pour: {key_path}")
        print("-" * 30)
        
        # Commande 1: Supprimer l'héritage
        cmd1 = f'icacls "{key_path}" /inheritance:r'
        print(f"Commande: {cmd1}")
        
        try:
            result = subprocess.run(
                cmd1,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("   [OK] Héritage supprimé")
            else:
                print(f"   [ERREUR] {result.stderr}")
        except Exception as e:
            print(f"   [ERREUR] {e}")
        
        # Commande 2: Donner les permissions à l'utilisateur
        cmd2 = f'icacls "{key_path}" /grant:r "%USERNAME%:R"'
        print(f"Commande: {cmd2}")
        
        try:
            result = subprocess.run(
                cmd2,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("   [OK] Permissions accordées")
            else:
                print(f"   [ERREUR] {result.stderr}")
        except Exception as e:
            print(f"   [ERREUR] {e}")
        
        print()
    
    print("3. COMMANDES DE TEST SSH")
    print("-" * 40)
    print()
    
    ssh_path = r"C:\Windows\System32\OpenSSH\ssh.exe"
    
    # Tester avec la première clé
    print("Test avec deepseek_ec2:")
    test_cmd1 = f'& "{ssh_path}" -i "{key1}" ubuntu@54.81.62.140 "echo Test SSH réussi"'
    print(f"Commande: {test_cmd1}")
    print()
    
    # Tester avec la deuxième clé
    print("Test avec qwen35-keypair.pem:")
    test_cmd2 = f'& "{ssh_path}" -i "{key2}" ubuntu@54.81.62.140 "echo Test SSH réussi"'
    print(f"Commande: {test_cmd2}")
    print()
    
    print("4. SOLUTIONS ALTERNATIVES")
    print("-" * 40)
    print()
    
    print("OPTION A: Vérifier le nom d'utilisateur")
    print("   Par défaut sur EC2 Ubuntu: ubuntu")
    print("   Essayez aussi: ec2-user")
    print()
    
    print("OPTION B: Convertir la clé avec PuTTYgen")
    print("   1. Télécharger PuTTYgen")
    print("   2. Load > Sélectionner la clé .pem")
    print("   3. Save private key > .ppk")
    print("   4. Utiliser PuTTY avec la clé .ppk")
    print()
    
    print("OPTION C: Regénérer la clé SSH")
    print("   1. Sur AWS Console > EC2 > Key Pairs")
    print("   2. Create key pair")
    print("   3. Télécharger la nouvelle clé")
    print("   4. Mettre à jour les permissions")
    print()
    
    print("=" * 80)
    print("INSTRUCTIONS POUR VOUS:")
    print("=" * 80)
    print()
    print("1. Exécutez ces commandes dans PowerShell Admin:")
    print()
    print(f'   icacls "{key1}" /inheritance:r')
    print(f'   icacls "{key1}" /grant:r "%USERNAME%:R"')
    print()
    print("2. Essayez à nouveau la connexion SSH:")
    print()
    print(f'   & "{ssh_path}" -i "{key1}" ubuntu@54.81.62.140')
    print()
    print("3. Si ça ne marche pas, essayez avec l'autre clé:")
    print()
    print(f'   & "{ssh_path}" -i "{key2}" ubuntu@54.81.62.140')
    print()
    print("4. Si les deux clés échouent, essayez avec ec2-user:")
    print()
    print(f'   & "{ssh_path}" -i "{key1}" ec2-user@54.81.62.140')
    print()
    
    return True

def check_key_format():
    """Vérifier le format de la clé"""
    
    print("\nVÉRIFICATION DU FORMAT DE LA CLÉ")
    print("-" * 40)
    
    key_path = r"C:\Users\maatc\.ssh\deepseek_ec2"
    
    if not os.path.exists(key_path):
        print(f"[ERREUR] Clé non trouvée: {key_path}")
        return False
    
    try:
        with open(key_path, 'r') as f:
            content = f.read()
            
        print("Analyse de la clé...")
        
        if "-----BEGIN OPENSSH PRIVATE KEY-----" in content:
            print("   [OK] Format: OpenSSH Private Key")
            return True
        elif "-----BEGIN RSA PRIVATE KEY-----" in content:
            print("   [OK] Format: RSA Private Key (ancien format)")
            print("   [INFO] Peut nécessiter conversion")
            return True
        elif "-----BEGIN PRIVATE KEY-----" in content:
            print("   [OK] Format: PKCS8 Private Key")
            return True
        else:
            print("   [ERREUR] Format de clé non reconnu")
            print("   Premières lignes:")
            for line in content.split('\n')[:5]:
                print(f"   {line}")
            return False
            
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

def main():
    """Fonction principale"""
    
    print("RÉSOLUTION DES PROBLÈMES SSH POUR DÉPLOIEMENT EC2")
    print("=" * 80)
    
    # Vérifier le format de la clé
    if not check_key_format():
        print("\n[ATTENTION] Problème avec le format de la clé")
    
    # Corriger les permissions
    fix_ssh_permissions()
    
    print("\n" + "=" * 80)
    print("PROCHAINES ÉTAPES:")
    print("=" * 80)
    print()
    print("1. Exécutez les commandes de correction des permissions")
    print("2. Essayez à nouveau la connexion SSH")
    print("3. Si ça marche, revenez ici pour les commandes de déploiement")
    print("4. Si ça ne marche pas, essayez PuTTY ou WSL")
    print()

if __name__ == "__main__":
    main()