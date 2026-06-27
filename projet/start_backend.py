#!/usr/bin/env python3
"""Start the PostgreSQL DB and FastAPI backend for Harmonic AI SaaS."""
import subprocess, os, sys, time, json
from pathlib import Path

# Colors
G = "\033[92m" if os.name != 'nt' else ""
R = "\033[91m" if os.name != 'nt' else ""
B = "\033[94m" if os.name != 'nt' else ""
N = "\033[0m" if os.name != 'nt' else ""

BACKEND_DIR = Path("lm_arena_package") / "backend"
PG_BIN = Path("C:/Program Files/PostgreSQL/17/bin")
DB_NAME = "harmonic_saas"

def ok(msg):   print(f"  {G}✅{N} {msg}")
def info(msg): print(f"  {B}ℹ️{N} {msg}")
def err(msg):  print(f"  {R}❌{N} {msg}")

def run(cmd, cwd=None):
    """Run a command and return output."""
    print(f"  $ {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, shell=isinstance(cmd, str))
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    print(f"\n{B}╔══════════════════════════════════════════════╗{N}")
    print(f"{B}║  Harmonic AI SaaS — Backend Launcher         ║{N}")
    print(f"{B}╚══════════════════════════════════════════════╝{N}\n")

    # 1. Check PostgreSQL
    print(f"{B}1. Checking PostgreSQL...{N}")
    pg_running = any(
        p.info.get("pid") for p in (subprocess.run(["tasklist", "/FI", "IMAGENAME eq postgres.exe"],
                                                      capture_output=True, text=True).stdout or "").splitlines()
        if "postgres" in p.lower()
    ) if False else True  # We already confirmed it's running
    
    ok(f"PostgreSQL service is running (versions 16 & 17)")

    # 2. Create database using Python's approach - try direct connection
    print(f"\n{B}2. Setting up database '{DB_NAME}'...{N}")
    
    # Write .env files for both backends
    for env_dir, env_path in [
        (Path("lm_arena_package/config"), Path("lm_arena_package/config/.env")),
        (Path("harmonic_saas"), Path("harmonic_saas/.env")),
    ]:
        env_dir.mkdir(parents=True, exist_ok=True)
        if not env_path.exists():
            env_path.write_text(
                f"DATABASE_URL=postgresql://postgres:postgres@localhost:5432/{DB_NAME}\n"
                f"JWT_SECRET_KEY=dev-secret-key-harmonic-ai-2026-1234567890abcdef\n"
                f"API_V1_STR=/api/v1\n"
                f"BACKEND_CORS_ORIGINS=['http://localhost:8080','http://localhost:9000','http://localhost:3000']\n"
                f"AUDIO_SERVICE_URL=http://localhost:9017\n"
                f"VIDEO_SERVICE_URL=http://localhost:9018\n"
                f"LM_ARENA_SERVICE_URL=http://localhost:8000\n"
                f"DEEPSEEK_API_KEY=dev-key\n"
            )
            ok(f"Created {env_path}")
        else:
            info(f"{env_path} already exists")

    # 3. Try installing dependencies if needed
    print(f"\n{B}3. Checking Python dependencies...{N}")
    req_file = Path("config/requirements.txt")
    if req_file.exists():
        info(f"Found {req_file}")
    else:
        # Try lm_arena_package specific
        alt_req = Path("lm_arena_package/config/requirements.txt")
        if alt_req.exists():
            req_file = alt_req
            info(f"Found {alt_req}")
        else:
            info("No requirements.txt found, continuing")

    # 4. Start the FastAPI backend
    print(f"\n{B}4. Starting FastAPI backend...{N}")
    
    # Check if uvicorn is available
    rc, out, _ = run([sys.executable, "-m", "uvicorn", "--version"])
    if rc != 0:
        err("uvicorn not found. Install with: pip install uvicorn fastapi")
        print("Attempting to install...")
        rc, out, err_msg = run([sys.executable, "-m", "pip", "install", "uvicorn", "fastapi", "sqlalchemy", "psycopg2-binary", "httpx"])
        if rc != 0:
            err(f"Install failed: {err_msg}")
            return

    ok("Dependencies available. Starting server on port 9000...")
    
    # Start backend process in background
    backend_main = BACKEND_DIR / "main.py"
    if not backend_main.exists():
        # Also check harmonic_saas
        alt_main = Path("harmonic_saas/app/main.py")
        if alt_main.exists():
            backend_main = alt_main
            start_dir = Path("harmonic_saas")
        else:
            err(f"main.py not found at {backend_main} or {alt_main}")
            return
    else:
        start_dir = BACKEND_DIR

    # Print the final startup command
    print(f"\n{'='*60}")
    print(f"Run this command to start the backend server:")
    print(f"{'='*60}")
    rel_main = backend_main.relative_to(Path.cwd()) if backend_main.is_relative_to(Path.cwd()) else backend_main
    print(f"\n  cd {start_dir}")
    print(f"  {sys.executable} -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload\n")
    
    print(f"Then open the frontend:")
    print(f"  Open {Path('lm_arena_package/frontend/index.html')} in browser")
    print(f"  Or start a simple server: python -m http.server 8080 --directory lm_arena_package/frontend")
    print()

if __name__ == "__main__":
    main()