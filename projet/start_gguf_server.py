#!/usr/bin/env python3
"""
Lanceur du Serveur GGUF Harmonique
======================================
Demarre le proxy GGUF harmonique (engine/llm/gguf_harmonizer.py) 
en mode serveur API compatible OpenAI.

Recherche automatiquement les modeles .gguf sur le disque E:\.

Usage:
    python start_gguf_server.py                         # Auto-detection du meilleur modele
    python start_gguf_server.py --model 9b              # Filtre par nom
    python start_gguf_server.py --model-path "E:\...\model.gguf"
    python start_gguf_server.py --port 8081 --no-gpu
    python start_gguf_server.py --list-models
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gguf-server")

GGUF_SEARCH_PATHS = [
    r"E:\QWEN35_DEEPSEEK_TEST\models",
    r"E:\TELECHARGEMENT-18-20AOUT",
    r"E:\QWEN35_DEEPSEEK_TEST\huggingface_cache\models--Qwen--Qwen2.5-1.5B-Instruct-GGUF\snapshots",
    r"E:\QWEN35_DEEPSEEK_TEST\model_cache",
    r"E:\Kimi-K2.5\model\.cache\huggingface\download",
    r"E:\Nouveau dossier\LM Studio\resources\app\.webpack\bin\bundled-models",
]

def _scan_gguf_directory(base_path: str, models: dict):
    if not os.path.exists(base_path):
        return
    try:
        for entry in os.scandir(base_path):
            try:
                if entry.is_dir(follow_symlinks=False):
                    _scan_gguf_directory(entry.path, models)
                elif entry.is_file(follow_symlinks=False):
                    f = entry.name
                    if f.endswith(".gguf") and not f.endswith(".lock"):
                        full_path = entry.path
                        try:
                            size_gb = os.path.getsize(full_path) / (1024**3)
                        except OSError:
                            continue
                        display_name = (f.replace("-Instruct-Q4_K_M.gguf", "")
                                        .replace("-q4_k_m.gguf", "")
                                        .replace("-q4.gguf", "")
                                        .replace("-BF16.gguf", "")
                                        .replace("-Flash", "")
                                        .replace(".gguf", ""))
                        fam = "unknown"
                        for pattern, label in [("1.5B", "light"), ("1.5b", "light"),
                                                ("9B", "medium"), ("9b", "medium"),
                                                ("14B", "medium"),
                                                ("32B", "large"), ("67B", "large"),
                                                ("K2.5", "large")]:
                            if pattern in f:
                                fam = label
                                break
                        if display_name not in models:
                            models[display_name] = {
                                "path": full_path,
                                "size_gb": round(size_gb, 1),
                                "family": fam,
                                "filename": f,
                            }
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass

def find_all_gguf_models() -> dict:
    models = {}
    for base_path in GGUF_SEARCH_PATHS:
        _scan_gguf_directory(base_path, models)
    return models

def list_models():
    models = find_all_gguf_models()
    if not models:
        print("\n  Aucun modele GGUF trouve.")
        print("  Le serveur demarrera en MODE DEMO.")
        return
    sorted_models = sorted(models.items(), key=lambda x: x[1]["size_gb"])
    print("\n  " + "=" * 60)
    print("  MODELES GGUF DISPONIBLES SUR E:\\")
    print("  " + "=" * 60)
    for name, info in sorted_models:
        print(f"  [OK] {name:<40s} {info['size_gb']:>6.1f} Go  ({info['family']})")
    print(f"\n  Total: {len(models)} modele(s)")
    print("  Pour lancer: python start_gguf_server.py --model <nom>\n")

def find_best_model(prefer: str = None) -> str:
    models = find_all_gguf_models()
    if not models:
        return None
    if prefer:
        filtered = {}
        p = prefer.lower()
        for name, info in models.items():
            if p in name.lower() or p in info["filename"].lower() or p in info["family"]:
                filtered[name] = info
        if filtered:
            items = sorted(filtered.items(), key=lambda x: x[1]["size_gb"])
            best_name, best_info = items[-1]
            print(f"  [OK] Modele selectionne: {best_name} ({best_info['size_gb']} Go)")
            return best_info["path"]
    items = sorted(models.items(), key=lambda x: x[1]["size_gb"])
    best_name, best_info = items[-1]
    print(f"  [OK] Meilleur modele trouve: {best_name} ({best_info['size_gb']} Go)")
    return best_info["path"]

def main():
    parser = argparse.ArgumentParser(description="Serveur GGUF Harmonique")
    parser.add_argument("--model-path", type=str, default=None)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--no-gpu", action="store_true")
    parser.add_argument("--gpu-layers", type=int, default=-1)
    parser.add_argument("--no-resonance", action="store_true")
    parser.add_argument("--no-memory", action="store_true")
    parser.add_argument("--ctx", type=int, default=8192)
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--alias", type=str, default=None)
    args = parser.parse_args()
    if args.list_models:
        list_models()
        return
    model_path = args.model_path
    if not model_path:
        model_path = find_best_model(prefer=args.model)
    if not model_path:
        print("\n  [WARN] Aucun modele GGUF trouve. Demarrage en MODE DEMO.\n")
        model_path = ""
    else:
        size_gb = Path(model_path).stat().st_size / (1024**3)
        print(f"  [OK] Fichier: {Path(model_path).name} ({size_gb:.1f} Go)")
    alias = args.alias
    if not alias and model_path:
        alias = Path(model_path).stem
        for suffix in ["-q4_k_m", "-q4", "-BF16", "-Flash", "-Instruct"]:
            alias = alias.replace(suffix, "")
    if not alias:
        alias = "harmonic-gguf"
    gpu_layers = 0 if args.no_gpu else args.gpu_layers
    print()
    print("=" * 60)
    print("  DEMARRAGE DU SERVEUR GGUF HARMONIQUE")
    print("=" * 60)
    print(f"  Modele:     {Path(model_path).name if model_path else 'Mode demo'}")
    print(f"  Alias:      {alias}")
    print(f"  Port:       {args.port}")
    print(f"  Hote:       {args.host}")
    print(f"  GPU layers: {gpu_layers if not args.no_gpu else '0 (CPU)'}")
    print(f"  Contexte:   {args.ctx}")
    print(f"  Resonance:  {'Non' if args.no_resonance else 'Oui'}")
    print(f"  Memoire:    {'Non' if args.no_memory else 'Oui'}")
    print()
    print("  Endpoints API:")
    print("    POST /v1/chat/completions  - Chat avec resonance")
    print("    GET  /health               - Sante")
    print("    GET  /harmonic/signature    - Signature 9D")
    print("    GET  /stats                 - Stats harmoniques")
    print()
    print("  Compatible: curl, OpenAI SDK, LangChain, LlamaIndex")
    print()
    print("=" * 60)
    print()
    from engine.llm.gguf_harmonizer import (GGUFHarmonicProxy, GGUFHarmonicProxyConfig)
    config = GGUFHarmonicProxyConfig(
        model_path=model_path,
        model_alias=alias,
        n_ctx=args.ctx,
        n_gpu_layers=gpu_layers,
        resonance_strength=0.0 if args.no_resonance else 0.7,
        use_memory=not args.no_memory,
    )
    proxy = GGUFHarmonicProxy(config)
    try:
        proxy.run_server(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n  Serveur arrete.")
    except Exception as e:
        logger.error(f"Erreur serveur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
