#!/usr/bin/env python3
"""
Tester différentes méthodes de connexion SSH sur Windows
"""

import os
import sys
import subprocess
import tempfile

def test_powershell_ssh():
    """Tester SSH via PowerShell"""
    
    print("\n1. TEST SSH VIA POWERSHELL")
    print("=" * 60)
    
    # Commande PowerShell pour SSH
    ps_script = """
    $ErrorActionPreference = "Stop"
    
    # Chemins des clés
    $keyPath = "C:\\Users\\maatc\\.ssh\\deepseek_ec2"
    $hostname = "54.81.62.140"
    
    # Tester différents utilisateurs
    $users = @("ubuntu", "ec2-user", "admin", "root")
    
    foreach ($user in $users) {
        Write-Host "`nTest avec utilisateur: $user" -ForegroundColor Cyan
        
        $sshCommand = "ssh -i `"$keyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o PasswordAuthentication=no -o BatchMode=yes ${user}@${hostname} 'echo SSH_SUCCESS'"
        
        try {
            $result = Invoke-Expression $sshCommand
            Write-Host "  [SUCCES] Connexion établie avec $user" -ForegroundColor Green
            Write-Host "  Sortie: $result" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "  [ERREUR] Échec avec $user" -ForegroundColor Red
            Write-Host "  Détails: $_" -ForegroundColor Yellow
        }
    }
    
    return $false
    """
    
    try:
        # Écrire le script PowerShell dans un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
            f.write(ps_script)
            ps_file = f.name
        
        # Exécuter le script PowerShell
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Code de retour: {result.returncode}")
        print(f"Sortie:\n{result.stdout}")
        
        if result.returncode == 0:
            print("[SUCCES] PowerShell SSH testé")
            return True
        else:
            print(f"[ERREUR] PowerShell SSH échoué: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[ERREUR] Exception: {e}")
        return False
    finally:
        # Nettoyer le fichier temporaire
        if 'ps_file' in locals() and os.path.exists(ps_file):
            os.unlink(ps_file)

def test_wsl_ssh():
    """Tester SSH via WSL (Windows Subsystem for Linux)"""
    
    print("\n2. TEST SSH VIA WSL")
    print("=" * 60)
    
    # Vérifier si WSL est installé
    try:
        result = subprocess.run(
            ["wsl", "--list", "--verbose"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("[INFO] WSL n'est pas installé ou non configuré")
            print("Pour installer WSL:")
            print("  1. Ouvrir PowerShell en tant qu'administrateur")
            print("  2. Exécuter: wsl --install")
            print("  3. Redémarrer l'ordinateur")
            return False
        
        print("[INFO] WSL est installé")
        print(f"Sortie WSL:\n{result.stdout}")
        
        # Copier la clé SSH dans WSL
        windows_key = r"C:\Users\maatc\.ssh\deepseek_ec2"
        
        # Commande WSL pour tester SSH
        wsl_script = f"""
        # Copier la clé depuis Windows
        mkdir -p ~/.ssh
        chmod 700 ~/.ssh
        
        # Convertir le chemin Windows vers WSL
        key_path=$(wslpath '{windows_key}')
        
        if [ -f "$key_path" ]; then
            cp "$key_path" ~/.ssh/deepseek_ec2
            chmod 600 ~/.ssh/deepseek_ec2
            echo "Clé copiée dans WSL"
        else
            echo "Clé non trouvée: $key_path"
            exit 1
        fi
        
        # Tester la connexion SSH
        users=("ubuntu" "ec2-user" "admin" "root")
        hostname="54.81.62.140"
        
        for user in "${{users[@]}}"; do
            echo ""
            echo "Test avec utilisateur: $user"
            
            if ssh -i ~/.ssh/deepseek_ec2 \
                -o StrictHostKeyChecking=no \
                -o ConnectTimeout=10 \
                -o PasswordAuthentication=no \
                -o BatchMode=yes \
                "$user@$hostname" "echo SSH_SUCCESS_WSL"; then
                echo "  [SUCCES] Connexion WSL établie avec $user"
                exit 0
            else
                echo "  [ERREUR] Échec WSL avec $user"
            fi
        done
        
        exit 1
        """
        
        # Écrire le script dans un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(wsl_script)
            script_file = f.name
        
        # Exécuter via WSL
        cmd = ["wsl", "bash", script_file]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Code de retour WSL: {result.returncode}")
        print(f"Sortie WSL:\n{result.stdout}")
        
        if result.returncode == 0:
            print("[SUCCES] Connexion SSH via WSL établie")
            return True
        else:
            print(f"[ERREUR] WSL SSH échoué: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[ERREUR] Exception WSL: {e}")
        return False

def test_putty_ssh():
    """Tester SSH via PuTTY"""
    
    print("\n3. TEST SSH VIA PUTTY")
    print("=" * 60)
    
    # Vérifier si PuTTY est installé
    putty_paths = [
        r"C:\Program Files\PuTTY\putty.exe",
        r"C:\Program Files (x86)\PuTTY\putty.exe"
    ]
    
    putty_path = None
    for path in putty_paths:
        if os.path.exists(path):
            putty_path = path
            break
    
    if not putty_path:
        print("[INFO] PuTTY n'est pas installé")
        print("Pour installer PuTTY:")
        print("  1. Télécharger depuis: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html")
        print("  2. Installer avec l'option 'PuTTY' et 'Pageant'")
        return False
    
    print(f"[INFO] PuTTY trouvé: {putty_path}")
    
    # Convertir la clé OpenSSH vers PPK si nécessaire
    openssh_key = r"C:\Users\maatc\.ssh\deepseek_ec2"
    puttygen_path = putty_path.replace("putty.exe", "puttygen.exe")
    
    if os.path.exists(puttygen_path):
        print("[INFO] Tentative de conversion de clé avec puttygen...")
        
        # Créer un fichier PPK temporaire
        ppk_file = os.path.join(tempfile.gettempdir(), "deepseek_ec2.ppk")
        
        try:
            cmd = [
                puttygen_path,
                openssh_key,
                "-O", "private",
                "-o", ppk_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(ppk_file):
                print(f"[SUCCES] Clé convertie en PPK: {ppk_file}")
                
                # Générer la commande PuTTY
                putty_cmd = f'"{putty_path}" -ssh -i "{ppk_file}" -load "deepseek_test"'
                
                print("\nCommande PuTTY générée:")
                print(f"  {putty_cmd}")
                print("\nConfiguration manuelle PuTTY:")
                print("  1. Ouvrir PuTTY")
                print("  2. Dans 'Host Name': ubuntu@54.81.62.140")
                print("  3. Dans Connection > SSH > Auth:")
                print("     • Cocher 'Allow agent forwarding'")
                print("     • Dans 'Private key file for authentication':")
                print(f"       {ppk_file}")
                print("  4. Dans Session:")
                print("     • Entrer un nom dans 'Saved Sessions'")
                print("     • Cliquer 'Save'")
                print("  5. Cliquer 'Open'")
                
                return True
            else:
                print(f"[ERREUR] puttygen échoué: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[ERREUR] Exception puttygen: {e}")
            return False
    else:
        print("[INFO] puttygen.exe non trouvé")
        return False

def test_aws_systems_manager():
    """Tester AWS Systems Manager (SSM) comme alternative"""
    
    print("\n4. TEST AWS SYSTEMS MANAGER (SSM)")
    print("=" * 60)
    
    # Vérifier si AWS CLI est installé
    try:
        result = subprocess.run(
            ["aws", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("[INFO] AWS CLI n'est pas installé")
            print("Pour installer AWS CLI:")
            print("  1. Télécharger depuis: https://aws.amazon.com/cli/")
            print("  2. Exécuter le programme d'installation")
            print("  3. Configurer avec: aws configure")
            return False
        
        print(f"[INFO] AWS CLI installé: {result.stdout.strip()}")
        
        # Vérifier la configuration AWS
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("[ERREUR] AWS non configuré ou permissions insuffisantes")
            print(f"Détails: {result.stderr}")
            return False
        
        print("[SUCCES] AWS CLI configuré")
        print(f"Identité: {result.stdout}")
        
        # Vérifier si l'instance a SSM activé
        print("\nVérification de l'instance EC2...")
        
        # D'abord, obtenir l'ID d'instance depuis l'IP
        instance_id = None
        
        # Essayer de trouver l'instance par IP publique
        cmd = [
            "aws", "ec2", "describe-instances",
            "--filters", f"Name=ip-address,Values=54.81.62.140",
            "--query", "Reservations[].Instances[].InstanceId",
            "--output", "text",
            "--region", "us-east-1"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0 and result.stdout.strip():
            instance_id = result.stdout.strip()
            print(f"[SUCCES] Instance trouvée: {instance_id}")
        else:
            print("[INFO] Instance non trouvée par IP, essayer par nom...")
            
            # Essayer par nom d'instance
            cmd = [
                "aws", "ec2", "describe-instances",
                "--filters", "Name=tag:Name,Values=DeepSeek-Harmonic-V2",
                "--query", "Reservations[].Instances[].InstanceId",
                "--output", "text",
                "--region", "us-east-1"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and result.stdout.strip():
                instance_id = result.stdout.strip()
                print(f"[SUCCES] Instance trouvée par nom: {instance_id}")
            else:
                print("[ERREUR] Instance non trouvée")
                return False
        
        # Vérifier si SSM est activé sur l'instance
        print(f"\nVérification SSM pour l'instance: {instance_id}")
        
        cmd = [
            "aws", "ssm", "describe-instance-information",
            "--filters", f"Key=InstanceIds,Values={instance_id}",
            "--query", "InstanceInformationList[].PingStatus",
            "--output", "text",
            "--region", "us-east-1"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0 and result.stdout.strip():
            ping_status = result.stdout.strip()
            print(f"[SUCCES] SSM status: {ping_status}")
            
            if ping_status == "Online":
                print("\n[SUCCES] L'instance est accessible via SSM!")
                print("\nCommandes SSM disponibles:")
                print(f"  1. Exécuter une commande:")
                print(f"     aws ssm send-command \\")
                print(f"       --instance-ids {instance_id} \\")
                print(f"       --document-name \"AWS-RunShellScript\" \\")
                print(f"       --parameters 'commands=[\"echo Hello from SSM\"]' \\")
                print(f"       --region us-east-1")
                
                print(f"\n  2. Démarrer une session interactive:")
                print(f"     aws ssm start-session --target {instance_id} --region us-east-1")
                
                return True
            else:
                print(f"[INFO] SSM status: {ping_status} (instance peut être arrêtée)")
                return False
        else:
            print("[INFO] SSM non activé sur cette instance")
            print("\nPour activer SSM:")
            print("  1. Vérifier que l'instance a le rôle IAM 'AmazonSSMManagedInstanceCore'")
            print("  2. Vérifier que l'agent SSM est installé sur l'instance")
            print("  3. Redémarrer l'instance si nécessaire")
            return False
            
    except Exception as e:
        print(f"[ERREUR] Exception AWS: {e}")
        return False

def test_port_connectivity():
    """Tester la connectivité des ports"""
    
    print("\n5. TEST CONNECTIVITE DES PORTS")
    print("=" * 60)
    
    hostname = "54.81.62.140"
    ports_to_test = [22, 80, 8000, 8080, 443]
    
    print(f"Test de connectivité vers {hostname}:")
    
    for port in ports_to_test:
        try:
            # Utiliser PowerShell pour tester la connexion TCP
            ps_script = f"""
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $result = $tcpClient.BeginConnect("{hostname}", {port}, $null, $null)
            $success = $result.AsyncWaitHandle.WaitOne(3000, $false)
            
            if ($success) {{
                $tcpClient.EndConnect($result)
                Write-Host "  Port {port}: OUVERT" -ForegroundColor Green
                $tcpClient.Close()
            }} else {{
                Write-Host "  Port {port}: FERME ou TIMEOUT" -ForegroundColor Red
            }}
            """
            
            cmd = ["powershell", "-Command", ps_script]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            print(f"  Port {port}: {result.stdout.strip()}")
            
        except Exception as e:
            print(f"  Port {port}: ERREUR - {e}")
    
    return True

def main():
    """Fonction principale"""
    
    print("TEST DES ALTERNATIVES SSH SUR WINDOWS")
    print("=" * 80)
    
    # Tester la connectivité des ports d'abord
    test_port_connectivity()
    
    # Tester différentes méthodes
    methods = [
        ("PowerShell SSH", test_powershell_ssh),
        ("WSL SSH", test_wsl_ssh),
        ("PuTTY SSH", test_putty_ssh),
        ("AWS Systems Manager", test_aws_systems_manager)
    ]
    
    successful_methods = []
    
    for method_name, test_function in methods:
        try:
            print(f"\n{'='*80}")
            print(f"METHODE: {method_name}")
            print(f"{'='*80}")
            
            if test_function():
                successful_methods.append(method_name)
                
        except Exception as e:
            print(f"[ERREUR] Test {method_name} échoué: {e}")
    
    # Résumé
    print(f"\n{'='*80}")
    print("RÉSUMÉ DES TESTS")
    print(f"{'='*80}")
    
    if successful_methods:
        print(f"[SUCCES] {len(successful_methods)} méthode(s) fonctionnelle(s):")
        for method in successful_methods:
            print(f"  • {method}")
        
        print("\nRecommandations:")
        if "AWS Systems Manager" in successful_methods:
            print("  1. Utiliser AWS Systems Manager (SSM) - méthode la plus fiable")
            print("     Pas besoin de clés SSH, gestion centralisée AWS")
        elif "PuTTY SSH" in successful_methods:
            print("  1. Utiliser PuTTY avec la clé PPK convertie")
            print("     Interface graphique, gestion de sessions")
        elif "WSL SSH" in successful_methods:
            print("  1. Utiliser WSL pour les commandes SSH Linux")
            print("     Environnement Linux natif sur Windows")
        else:
            print("  1. Utiliser PowerShell SSH avec les paramètres de débogage")
        
    else:
        print("[ERREUR] Aucune méthode SSH ne fonctionne")
        print("\nSolutions urgentes:")
        print("  1. Vérifier les groupes de sécurité AWS:")
        print("     • Port 22 (SSH) doit être ouvert depuis votre IP")
        print("     • Vérifier les règles entrantes dans le groupe de sécurité")
        print("  2. Regénérer une paire de clés dans AWS Console")
        print("  3. Redémarrer l'instance EC2")
        print("  4. Contacter le support AWS si le problème persiste")
    
    return successful_methods

if __name__ == "__main__":
    main()