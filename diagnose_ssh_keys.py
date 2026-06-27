#!/usr/bin/env python3
"""
Diagnostic des clés SSH sur Windows
"""

import os
import sys
import subprocess
import stat

def check_ssh_key_format(key_path):
    """Vérifier le format d'une clé SSH"""
    
    print(f"\nAnalyse de la clé: {key_path}")
    print("-" * 60)
    
    if not os.path.exists(key_path):
        print("  [ERREUR] Fichier non trouvé")
        return False
    
    # Vérifier les permissions
    try:
        st = os.stat(key_path)
        mode = st.st_mode
        
        print(f"  Taille: {st.st_size} octets")
        print(f"  Permissions: {oct(mode)[-3:]}")
        
        # Vérifier si le fichier est lisible
        if not (mode & stat.S_IRUSR):
            print("  [ERREUR] Fichier non lisible par l'utilisateur")
            return False
            
    except Exception as e:
        print(f"  [ERREUR] Impossible de lire les permissions: {e}")
        return False
    
    # Lire le contenu de la clé
    try:
        with open(key_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1024)  # Lire les premiers 1024 caractères
        
        print(f"  Début du contenu: {content[:100]}...")
        
        # Analyser le format
        if "-----BEGIN RSA PRIVATE KEY-----" in content:
            print("  Format: RSA PRIVATE KEY (PEM)")
            return True
        elif "-----BEGIN OPENSSH PRIVATE KEY-----" in content:
            print("  Format: OPENSSH PRIVATE KEY")
            return True
        elif "-----BEGIN PRIVATE KEY-----" in content:
            print("  Format: PRIVATE KEY (PKCS#8)")
            return True
        elif "PuTTY-User-Key-File-2" in content:
            print("  Format: PuTTY Private Key (PPK)")
            return True
        else:
            print("  [ERREUR] Format de clé non reconnu")
            print("  Formats supportés par OpenSSH:")
            print("    - RSA PRIVATE KEY (PEM)")
            print("    - OPENSSH PRIVATE KEY")
            print("    - PRIVATE KEY (PKCS#8)")
            return False
            
    except Exception as e:
        print(f"  [ERREUR] Impossible de lire le fichier: {e}")
        return False

def test_ssh_connection(key_path, username, hostname):
    """Tester une connexion SSH avec une clé spécifique"""
    
    print(f"\nTest de connexion SSH:")
    print(f"  Clé: {key_path}")
    print(f"  Utilisateur: {username}")
    print(f"  Hôte: {hostname}")
    print("-" * 60)
    
    # Construire la commande SSH
    ssh_path = r"C:\Windows\System32\OpenSSH\ssh.exe"
    
    if not os.path.exists(ssh_path):
        print("  [ERREUR] ssh.exe non trouvé")
        return False
    
    cmd = [
        ssh_path,
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        "-o", "PasswordAuthentication=no",
        "-o", "BatchMode=yes",
        f"{username}@{hostname}",
        "echo 'Connexion SSH réussie'"
    ]
    
    try:
        print(f"  Commande: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        print(f"  Code de retour: {result.returncode}")
        print(f"  Sortie standard: {result.stdout}")
        print(f"  Sortie d'erreur: {result.stderr}")
        
        if result.returncode == 0:
            print("  [SUCCES] Connexion SSH établie")
            return True
        else:
            print("  [ERREUR] Connexion SSH échouée")
            return False
            
    except subprocess.TimeoutExpired:
        print("  [ERREUR] Timeout - connexion trop longue")
        return False
    except Exception as e:
        print(f"  [ERREUR] Exception: {e}")
        return False

def fix_ssh_permissions(key_path):
    """Corriger les permissions d'une clé SSH sur Windows"""
    
    print(f"\nCorrection des permissions pour: {key_path}")
    print("-" * 60)
    
    if not os.path.exists(key_path):
        print("  [ERREUR] Fichier non trouvé")
        return False
    
    # Méthode 1: Utiliser icacls (recommandé pour Windows)
    try:
        # Rendre le fichier accessible uniquement à l'utilisateur courant
        cmd = ['icacls', key_path, '/inheritance:r', '/grant:r', f'{os.environ["USERNAME"]}:R']
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("  [SUCCES] Permissions corrigées avec icacls")
            
            # Vérifier les nouvelles permissions
            cmd_check = ['icacls', key_path]
            result_check = subprocess.run(
                cmd_check,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"  Nouvelles permissions:")
            for line in result_check.stdout.split('\n'):
                if key_path in line or ':' in line:
                    print(f"    {line}")
            
            return True
        else:
            print(f"  [ERREUR] icacls a échoué: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  [ERREUR] Exception avec icacls: {e}")
        return False

def convert_key_format(key_path, output_path):
    """Convertir une clé SSH vers un format compatible OpenSSH"""
    
    print(f"\nConversion de clé SSH:")
    print(f"  Source: {key_path}")
    print(f"  Destination: {output_path}")
    print("-" * 60)
    
    if not os.path.exists(key_path):
        print("  [ERREUR] Fichier source non trouvé")
        return False
    
    # Lire le contenu pour déterminer le format
    try:
        with open(key_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"  [ERREUR] Impossible de lire le fichier source: {e}")
        return False
    
    # Vérifier si c'est déjà un format OpenSSH
    if "-----BEGIN OPENSSH PRIVATE KEY-----" in content:
        print("  La clé est déjà au format OpenSSH")
        return True
    
    # Essayer de convertir avec puttygen si disponible
    puttygen_path = r"C:\Program Files\PuTTY\puttygen.exe"
    
    if os.path.exists(puttygen_path) and "PuTTY-User-Key-File-2" in content:
        print("  Conversion PPK vers OpenSSH avec puttygen...")
        
        try:
            cmd = [
                puttygen_path,
                key_path,
                "-O", "private-openssh",
                "-o", output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("  [SUCCES] Clé convertie avec puttygen")
                return True
            else:
                print(f"  [ERREUR] puttygen a échoué: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  [ERREUR] Exception avec puttygen: {e}")
            return False
    else:
        print("  [INFO] puttygen non disponible ou format non PPK")
        print("  Tentative de conversion manuelle...")
        
        # Pour les clés PEM, elles devraient déjà fonctionner avec OpenSSH
        if "-----BEGIN" in content:
            print("  La clé semble être au format PEM")
            print("  OpenSSH devrait la supporter directement")
            
            # Copier le fichier
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  [SUCCES] Clé copiée vers: {output_path}")
                return True
            except Exception as e:
                print(f"  [ERREUR] Impossible de copier la clé: {e}")
                return False
        else:
            print("  [ERREUR] Format de clé non supporté pour conversion")
            return False

def main():
    """Fonction principale"""
    
    print("DIAGNOSTIC DES CLES SSH SUR WINDOWS")
    print("=" * 80)
    
    # Chemins des clés SSH
    ssh_dir = r"C:\Users\maatc\.ssh"
    keys_to_check = [
        os.path.join(ssh_dir, "deepseek_ec2"),
        os.path.join(ssh_dir, "qwen35-keypair.pem")
    ]
    
    # Informations de connexion
    hostname = "54.81.62.140"
    usernames_to_try = ["ubuntu", "ec2-user", "admin", "root"]
    
    # Vérifier chaque clé
    valid_keys = []
    
    for key_path in keys_to_check:
        print(f"\n{'='*80}")
        print(f"CLÉ: {key_path}")
        print(f"{'='*80}")
        
        # Vérifier l'existence
        if not os.path.exists(key_path):
            print(f"[ERREUR] Fichier non trouvé: {key_path}")
            continue
        
        # Vérifier le format
        if not check_ssh_key_format(key_path):
            print("  Tentative de correction...")
            
            # Essayer de convertir la clé
            converted_path = key_path + "_converted"
            if convert_key_format(key_path, converted_path):
                key_path = converted_path
                print(f"  Utilisation de la clé convertie: {key_path}")
            else:
                print("  [ERREUR] Impossible de convertir la clé")
                continue
        
        # Corriger les permissions
        if not fix_ssh_permissions(key_path):
            print("  [AVERTISSEMENT] Impossible de corriger les permissions")
        
        # Tester la connexion avec différents utilisateurs
        for username in usernames_to_try:
            print(f"\n  Test avec utilisateur: {username}")
            
            if test_ssh_connection(key_path, username, hostname):
                print(f"  [SUCCES] Clé valide avec utilisateur: {username}")
                valid_keys.append((key_path, username))
                break
            else:
                print(f"  [ERREUR] Échec avec utilisateur: {username}")
    
    # Résumé
    print(f"\n{'='*80}")
    print("RÉSUMÉ DU DIAGNOSTIC")
    print(f"{'='*80}")
    
    if valid_keys:
        print(f"[SUCCES] {len(valid_keys)} clé(s) valide(s) trouvée(s):")
        for key_path, username in valid_keys:
            print(f"  • Clé: {key_path}")
            print(f"    Utilisateur: {username}")
            print(f"    Commande SSH: ssh -i \"{key_path}\" {username}@{hostname}")
    else:
        print("[ERREUR] Aucune clé valide trouvée")
        print("\nSolutions possibles:")
        print("1. Vérifier que la clé est associée à l'instance EC2 dans AWS Console")
        print("2. Regénérer une nouvelle paire de clés dans AWS Console")
        print("3. Utiliser PuTTY pour convertir la clé au format PPK")
        print("4. Vérifier les groupes de sécurité de l'instance (port 22 ouvert)")
    
    return valid_keys

if __name__ == "__main__":
    main()