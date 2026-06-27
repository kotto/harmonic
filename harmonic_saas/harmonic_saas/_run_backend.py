"""Script simple pour lancer le backend"""
import os
import sys
import subprocess

# Le backend est dans f:\SAAS - Copie\harmonic_saas
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Configurer les variables d'environnement
env = os.environ.copy()
env["PYTHONPATH"] = backend_dir
env["DATABASE_URL"] = "sqlite:///./harmonic_saas.db"
env["JWT_SECRET_KEY"] = "dev-secret-key-harmonic-ai-2026"
env["BACKEND_CORS_ORIGINS"] = '["http://localhost:8080","http://localhost:3000","http://localhost:9000"]'
env["ENVIRONMENT"] = "development"

print("=" * 60)
print("  Harmonic AI SaaS Backend")
print("=" * 60)
print(f"  Backend dir: {backend_dir}")
print(f"  API: http://localhost:9000")
print(f"  Docs: http://localhost:9000/docs")
print("=" * 60)

# Lancer uvicorn avec subprocess
cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000", "--log-level", "info"]
process = subprocess.Popen(cmd, cwd=backend_dir, env=env)
process.wait()
