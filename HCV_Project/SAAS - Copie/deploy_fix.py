#!/usr/bin/env python3
"""
Déploiement de la correction middleware + handler
"""

import subprocess
import sys

def backup_original():
    """Backup du fichier original"""
    cmd = [
        "aws", "ssm", "send-command",
        "--instance-ids", "i-0716d7805ca2c22e9",
        "--document-name", "AWS-RunShellScript",
        "--parameters", "commands=[\"cp /opt/connective-ai/PARALLEL_MULTI_MODAL_AGGREGATION.py /opt/connective-ai/PARALLEL_MULTI_MODAL_AGGREGATION.py.backup\"]"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Backup créé")
        else:
            print(f"❌ Erreur backup: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur backup: {e}")
        return False
    
    return True

def upload_fix():
    """Uploader le fichier corrigé"""
    cmd = [
        "aws", "s3", "cp",
        "f:\\SAAS - Copie\\middleware_logging_fix.py",
        "s3://deepseek-models-326095712935/fix/middleware_logging_fix.py"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Fichier corrigé uploadé")
        else:
            print(f"❌ Erreur upload: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur upload: {e}")
        return False
    
    return True

def apply_fix():
    """Appliquer la correction sur l'instance"""
    cmd = [
        "aws", "ssm", "send-command",
        "--instance-ids", "i-0716d7805ca2c22e9",
        "--document-name", "AWS-RunShellScript",
        "--parameters", "commands=[\"cd /opt/connective-ai && aws s3 cp s3://deepseek-models-326095712935/fix/middleware_logging_fix.py ./middleware_logging_fix.py && python3 -c \\\"import middleware_logging_fix; print('Fix imported successfully')\\\" && sudo systemctl restart connective-ai-boost\"]"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Correction appliquée, service redémarré")
            print("📊 Résultat:", result.stdout)
        else:
            print(f"❌ Erreur application: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur application: {e}")
        return False
    
    return True

def test_fix():
    """Tester la correction"""
    cmd = [
        "aws", "ssm", "send-command",
        "--instance-ids", "i-0716d7805ca2c22e9",
        "--document-name", "AWS-RunShellScript",
        "--parameters", "commands=[\"sleep 5 && curl -v -X POST http://localhost:8000/generate -H Content-Type: application/json -d '{\\\"prompt\\\":\\\"test_fix\\\"}' --max-time 10\"]"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Test de correction lancé")
            print("📊 Résultat:", result.stdout)
        else:
            print(f"❌ Erreur test: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Déploiement de la correction middleware + handler...")
    
    if backup_original():
        print("\n📦 Upload de la correction...")
        if upload_fix():
            print("\n🔧 Application de la correction...")
            if apply_fix():
                print("\n🧪 Test de la correction...")
                test_fix()
                print("\n✅ Déploiement terminé!")
            else:
                print("\n❌ Échec application")
                sys.exit(1)
        else:
            print("\n❌ Échec upload")
            sys.exit(1)
    else:
        print("\n❌ Échec backup")
        sys.exit(1)
