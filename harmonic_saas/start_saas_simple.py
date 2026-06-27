#!/usr/bin/env python3
"""
Harmonic AI SaaS - DÃ©marrage simplifiÃ© (sans Docker)
====================================================
Lance le backend FastAPI avec SQLite et le frontend HTTP.
"""

import subprocess
import sys
import os
import time
import signal
import threading

# Couleurs pour le terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    print(f"""
{Colors.CYAN}{Colors.BOLD}â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘              HARMONIC AI SAAS PLATFORM              â•‘
â•‘           DÃ©marrage simplifiÃ© (sans Docker)          â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•{Colors.ENDC}
    """)

def print_status(service, status, color=Colors.GREEN):
    print(f"{color}[{status}]{Colors.ENDC} {service}")

def run_backend():
    """Lance le backend FastAPI avec SQLite"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Configurer l'environnement pour SQLite
    os.environ["DATABASE_URL"] = "sqlite:///./harmonic_saas.db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["MONGODB_URL"] = "mongodb://localhost:27017/harmonic_saas"
    os.environ["JWT_SECRET_KEY"] = "dev-secret-key-harmonic-ai-2026"
    os.environ["BACKEND_CORS_ORIGINS"] = '["http://localhost:8080","http://localhost:3000","http://localhost:9000"]'
    
    print_status("Backend FastAPI", "DÃ‰MARRAGE...", Colors.WARNING)
    
    # Lancer uvicorn
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]
    
    try:
        process = subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        print_status(f"Backend FastAPI (PID: {process.pid})", "âœ… http://localhost:9000", Colors.GREEN)
        print_status("Documentation API", "âœ… http://localhost:9000/docs", Colors.GREEN)
        process.wait()
    except KeyboardInterrupt:
        print_status("Backend FastAPI", "ARRÃŠT...", Colors.WARNING)
        process.terminate()
    except Exception as e:
        print_status(f"Backend FastAPI: {e}", "ERREUR", Colors.FAIL)

def run_frontend():
    """Lance le frontend HTTP"""
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    
    print_status("Frontend HTTP", "DÃ‰MARRAGE...", Colors.WARNING)
    
    cmd = [sys.executable, "-m", "http.server", "8080", "--directory", frontend_dir]
    
    try:
        process = subprocess.Popen(cmd)
        print_status(f"Frontend (PID: {process.pid})", "âœ… http://localhost:8080", Colors.GREEN)
        process.wait()
    except KeyboardInterrupt:
        print_status("Frontend", "ARRÃŠT...", Colors.WARNING)
        process.terminate()
    except Exception as e:
        print_status(f"Frontend: {e}", "ERREUR", Colors.FAIL)

def main():
    print_banner()
    
    print(f"{Colors.BOLD}Services disponibles :{Colors.ENDC}")
    print(f"  {Colors.CYAN}â€¢{Colors.ENDC} Backend API  : http://localhost:9000")
    print(f"  {Colors.CYAN}â€¢{Colors.ENDC} Documentation : http://localhost:9000/docs")
    print(f"  {Colors.CYAN}â€¢{Colors.ENDC} Frontend      : http://localhost:8080")
    print(f"  {Colors.CYAN}â€¢{Colors.ENDC} MÃ©triques     : http://localhost:9000/metrics")
    print(f"  {Colors.CYAN}â€¢{Colors.ENDC} SantÃ© API     : http://localhost:9000/health")
    print()
    print(f"{Colors.WARNING}âš  Note : PostgreSQL/Redis/MongoDB non requis en mode SQLite{Colors.ENDC}")
    print(f"{Colors.WARNING}âš  Le backend DeepSeek AWS est accessible via http://__EC2_IP__:8000{Colors.ENDC}")
    print()
    print(f"{Colors.BOLD}Appuyez sur Ctrl+C pour arrÃªter tous les services{Colors.ENDC}")
    print("=" * 60)
    
    # Lancer les services dans des threads
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    frontend_thread = threading.Thread(target=run_frontend, daemon=True)
    
    backend_thread.start()
    time.sleep(2)  # Laisser le backend dÃ©marrer
    frontend_thread.start()
    
    try:
        # Garder le thread principal en vie
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print_status("Tous les services", "ARRÃŠT...", Colors.WARNING)
        print(f"{Colors.GREEN}âœ“ Services arrÃªtÃ©s proprement{Colors.ENDC}")
        sys.exit(0)

if __name__ == "__main__":
    main()
