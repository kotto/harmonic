"""Test d'import de l'application"""
import os
os.environ["DATABASE_URL"] = "sqlite:///./harmonic_saas.db"
os.environ["JWT_SECRET_KEY"] = "dev-secret-key-harmonic-ai-2026"
os.environ["BACKEND_CORS_ORIGINS"] = '["http://localhost:8080","http://localhost:3000","http://localhost:9000"]'

try:
    from app.main import app
    print("OK - App imported successfully")
    print(f"App title: {app.title}")
    print(f"Routes: {len(app.routes)}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
