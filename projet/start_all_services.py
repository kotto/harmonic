#!/usr/bin/env python3
"""
Lanceur Unifié — SAAS Harmonique + GGUF Proxy
================================================
Démarre les services SAAS et GGUF en parallèle pour un pipeline complet.

Architecture:
    User → SAAS API (port 9000) → GGUF Proxy (port 8080) → Modèle GGUF (LLM)
                                     ↓
                             Résonance 9D + Mémoire ABC

Usage:
    python start_all_services.py                          # GGUF auto + SAAS
    python start_all_services.py --model 9b               # Forcer un modèle
    python start_all_services.py --no-gguf                # SAAS seul
    python start_all_services.py --no-saas                # GGUF seul
    python start_all_services.py --list-models            # Voir les modèles
"""

import os
import sys
import time
import signal
import subprocess
import argparse
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("launcher")

ROOT_DIR = Path(__file__).parent


def print_banner():
    print()
    print("  +" + "=" * 50 + "+")
    print("  |       HARMONIC AI - PIPELINE COMPLET                |")
    print("  |   GGUF Harmonique + API SAAS + Resonance 9D        |")
    print("  +" + "=" * 50 + "+")
    print()
    print("  Nombre d'or phi = 1.618033988749895")
    print("  Dimensions: 9D (phi, alpha, reasoning, creative, math, factual, code, emotion, temporal)")
    print("  Memoire: ABC (Atangana-Baleanu, ordre 1/phi)")
    print()


def run_gguf_server(model_filter: str = None, port: int = 8080,
                    no_gpu: bool = False):
    """Lance le serveur GGUF harmonique dans un sous-processus."""
    cmd = [
        sys.executable,
        str(ROOT_DIR / "start_gguf_server.py"),
        "--port", str(port),
    ]
    if model_filter:
        cmd.extend(["--model", model_filter])
    if no_gpu:
        cmd.append("--no-gpu")
    
    logger.info(f"Démarrage du proxy GGUF (port {port})...")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    return process


def run_saas_backend(port: int = 9000):
    """Lance le backend SAAS dans un sous-processus."""
    env = os.environ.copy()
    env["GGUF_SERVICE_URL"] = "http://localhost:8080"
    
    cmd = [
        sys.executable,
        str(ROOT_DIR / "harmonic_saas" / "run_backend.py"),
    ]
    
    logger.info(f"Démarrage du backend SAAS (port {port})...")
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    return process


def list_available_gguf_models():
    """Liste les modèles GGUF disponibles."""
    from start_gguf_server import find_all_gguf_models, list_models
    list_models()


def main():
    parser = argparse.ArgumentParser(
        description="Lanceur unifié SAAS Harmonique + GGUF"
    )
    parser.add_argument("--model", type=str, default=None,
                        help="Filtre modèle GGUF ('9b', '1.5b', 'deepseek')")
    parser.add_argument("--gguf-port", type=int, default=8080)
    parser.add_argument("--saas-port", type=int, default=9000)
    parser.add_argument("--no-gguf", action="store_true",
                        help="Démarrer uniquement le SAAS")
    parser.add_argument("--no-saas", action="store_true",
                        help="Démarrer uniquement le GGUF")
    parser.add_argument("--no-gpu", action="store_true",
                        help="CPU only pour GGUF")
    parser.add_argument("--list-models", action="store_true",
                        help="Lister les modèles GGUF disponibles")
    
    args = parser.parse_args()
    
    if args.list_models:
        list_available_gguf_models()
        # Lister aussi les modèles téléchargeables
        try:
            from download_gguf_models import list_models as list_downloadable
            list_downloadable()
        except ImportError:
            pass
        return
    
    print_banner()
    
    processes = []
    
    try:
        # 1. Démarrer le proxy GGUF
        if not args.no_gguf:
            gguf_proc = run_gguf_server(
                model_filter=args.model,
                port=args.gguf_port,
                no_gpu=args.no_gpu,
            )
            processes.append(("GGUF", gguf_proc))
            logger.info(f"  OK Proxy GGUF demarre (PID: {gguf_proc.pid})")
            # Laisser le temps au GGUF de charger
            if args.model:
                time.sleep(2)
        
        # 2. Démarrer le backend SAAS
        if not args.no_saas:
            saas_proc = run_saas_backend(port=args.saas_port)
            processes.append(("SAAS", saas_proc))
            logger.info(f"  OK Backend SAAS demarre (PID: {saas_proc.pid})")
        
        if not processes:
            logger.warning("Aucun service à démarrer. Utilisez --help.")
            return
        
        print()
        print("  " + "=" * 50)
        print("  PIPELINE HARMONIQUE ACTIF")
        print("  " + "=" * 50)
        print()
        
        if not args.no_gguf:
            print(f"  Proxy GGUF      -> http://localhost:{args.gguf_port}")
            print(f"    Chat           -> POST /v1/chat/completions")
            print(f"    Sante          -> GET  /health")
            print(f"    Signature 9D   -> GET  /harmonic/signature")
            print()
        
        if not args.no_saas:
            print(f"  API SAAS         -> http://localhost:{args.saas_port}")
            print(f"    Chat public    -> POST /api/chat/public")
            print(f"    Documentation  -> http://localhost:{args.saas_port}/docs")
            print()
        
        print(f"  Flux: User -> SAAS:{args.saas_port} -> GGUF:{args.gguf_port} -> LLM")
        print(f"  Resonance 9D: OK | Memoire ABC: OK | phi = 1.618")
        print()
        print(f"  Appuyez sur Ctrl+C pour arrêter tous les services.")
        print()
        
        # Surveiller les logs
        while True:
            for name, proc in processes:
                if proc.poll() is not None:
                    logger.error(f"  [ERREUR] {name} arrêté (code: {proc.returncode})")
                    # Lire les dernières lignes
                    try:
                        stdout, _ = proc.communicate(timeout=2)
                        for line in stdout.split('\n')[-5:]:
                            if line.strip():
                                print(f"    {line.strip()}")
                    except:
                        pass
                    return
            
            # Afficher les logs
            for name, proc in processes:
                try:
                    line = proc.stdout.readline()
                    if line:
                        line = line.rstrip()
                        if any(w in line.lower() for w in ['error', 'traceback', 'exception']):
                            print(f"  [{name}] !! {line}")
                        elif 'info' in line.lower() or 'démarrage' in line.lower():
                            print(f"  [{name}] {line}")
                except:
                    pass
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n  Arrêt des services...")
        for name, proc in processes:
            logger.info(f"  Arrêt de {name} (PID: {proc.pid})...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("  OK Tous les services arretes.")


if __name__ == "__main__":
    main()
