#!/usr/bin/env python3
"""Script de démarrage du backend et frontend pour le développement"""
import os
import sys
import subprocess
import time
import signal
import atexit

# Configuration
BACKEND_PORT = 9000
FRONTEND_PORT = 8080
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BACKEND_DIR, "frontend")

# Variables d'environnement
os.environ["DATABASE_URL"] = "sqlite:///./harmonic_saas.db"
os.environ["JWT_SECRET_KEY"] = "dev-secret-key-harmonic-ai-2026"
os.environ["BACKEND_CORS_ORIGINS"] = '["http://localhost:8080","http://localhost:3000","http://localhost:9000"]'
os.environ["ENVIRONMENT"] = "development"

processes = []

def cleanup():
    """Nettoie les processus au shutdown"""
    print("\n🛑 Arrêt des services...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except:
                p.kill()
    print("✅ Services arrêtés")

atexit.register(cleanup)
signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

def main():
    print("=" * 60)
    print("  Harmonic AI SaaS - Mode Développement")
    print("=" * 60)
    
    # 1. Démarrer le backend
    print("\n🚀 Démarrage du backend sur http://localhost:{}".format(BACKEND_PORT))
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(BACKEND_PORT),
        "--reload",
        "--log-level", "info"
    ]
    p_backend = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    processes.append(p_backend)
    
    # 2. Démarrer le frontend
    print("🚀 Démarrage du frontend sur http://localhost:{}".format(FRONTEND_PORT))
    frontend_cmd = [
        sys.executable, "-m", "http.server", str(FRONTEND_PORT),
        "--directory", FRONTEND_DIR
    ]
    p_frontend = subprocess.Popen(
        frontend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    processes.append(p_frontend)
    
    # Attendre que le backend soit prêt
    print("\n⏳ Attente du démarrage du backend...")
    time.sleep(3)
    
    # Vérifier que le backend répond
    import urllib.request
    import json
    try:
        r = urllib.request.urlopen(f"http://localhost:{BACKEND_PORT}/health", timeout=5)
        data = json.loads(r.read())
        print(f"✅ Backend prêt - Status: {data.get('status', 'OK')}")
    except Exception as e:
        print(f"⚠️  Backend non accessible: {e}")
        print("   Vérifiez les logs ci-dessous...")
    
    print("\n" + "=" * 60)
    print("  Services disponibles :")
    print(f"  📡 API Backend : http://localhost:{BACKEND_PORT}")
    print(f"  📡 API Docs   : http://localhost:{BACKEND_PORT}/docs")
    print(f"  🌐 Frontend   : http://localhost:{FRONTEND_PORT}")
    print("=" * 60)
    print("\n📋 Logs backend (Ctrl+C pour arrêter) :\n")
    
    # Afficher les logs du backend
    try:
        for line in p_backend.stdout:
            print(f"[BACKEND] {line}", end="")
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
