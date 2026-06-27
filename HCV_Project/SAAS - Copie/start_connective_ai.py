#!/usr/bin/env python3
"""
Script pour démarrer le service Connective AI
"""

import subprocess
import sys
import os

def check_service():
    """Vérifie si le service est en cours d'exécution"""
    try:
        result = subprocess.run(['curl', '-s', 'http://localhost:8000/api/health'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Service déjà en cours d'exécution")
            return True
    except:
        pass
    return False

def start_service():
    """Démarre le service FastAPI"""
    print("🚀 Démarrage du service Connective AI...")
    
    # Vérifier quel fichier est le bon
    files_to_check = [
        '/opt/connective-ai/PARALLEL_MULTI_MODAL_AGGREGATION.py',
        '/opt/connective-ai/DEEPSEEK_S3_LOCAL_INTEGRATION.py'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"📁 Fichier trouvé: {file_path}")
            # Vérifier si c'est un fichier FastAPI
            try:
                with open(file_path, 'r') as f:
                    content = f.read(500)
                    if 'app = FastAPI' in content:
                        print(f"✅ Fichier FastAPI identifié: {os.path.basename(file_path)}")
                        return file_path
            except:
                continue
    
    print("❌ Aucun fichier FastAPI valide trouvé")
    return None

def main():
    if check_service():
        return
    
    app_file = start_service()
    if not app_file:
        print("❌ Impossible de démarrer le service")
        sys.exit(1)
    
    # Démarrer le service
    app_name = os.path.basename(app_file).replace('.py', '')
    cmd = [
        'python3', '-m', 'uvicorn', 
        f'{app_name}:app',
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload'
    ]
    
    print(f"▶️  Commande: {' '.join(cmd)}")
    print("📝 Le service démarre...")
    
    # Exécuter en arrière-plan
    try:
        import subprocess
        process = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        print(f"✅ Service démarré avec PID: {process.pid}")
        print("🔍 Vérification du statut...")
        
        # Attendre un peu et vérifier
        import time
        time.sleep(3)
        
        if check_service():
            print("🎉 Service Connective AI démarré avec succès!")
            print("🌐 URL: http://localhost:8000")
            print("📊 Health: http://localhost:8000/api/health")
            print("⚡ Generate: http://localhost:8000/api/generate")
        else:
            print("⚠️  Service démarré mais non accessible")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == '__main__':
    main()