#!/usr/bin/env python3
"""
Script pour uploader le benchmark corrigé et l'exécuter
"""

import subprocess
import sys

def upload_file():
    """Uploader le fichier corrigé sur l'instance"""
    cmd = [
        "aws", "s3", "cp", 
        "f:\\SAAS - Copie\\HCV-PRO-PROJECT\\DETERMINISTIC_AI_BENCHMARK_TESTS.py",
        "s3://deepseek-models-326095712935/benchmark/DETERMINISTIC_AI_BENCHMARK_TESTS.py"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Fichier uploadé avec succès sur S3")
        else:
            print(f"❌ Erreur upload: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur upload: {e}")
        return False
    
    return True

def test_on_instance():
    """Tester le benchmark sur l'instance"""
    cmd = [
        "aws", "ssm", "send-command",
        "--instance-ids", "i-0716d7805ca2c22e9",
        "--document-name", "AWS-RunShellScript",
        "--parameters", "commands=[\"cd /opt/connective-ai && python3 DETERMINISTIC_AI_BENCHMARK_TESTS.py\"]"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Benchmark lancé sur l'instance")
            print("📊 Résultat:", result.stdout)
        else:
            print(f"❌ Erreur benchmark: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur benchmark: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Déploiement et test des benchmarks corrigés...")
    
    if upload_file():
        print("\n🔄 Lancement du benchmark sur l'instance...")
        test_on_instance()
    else:
        print("\n❌ Échec de l'upload")
        sys.exit(1)
