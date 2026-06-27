#!/usr/bin/env python3
"""
Téléchargeur de modèles GGUF pour Harmonic AI
==============================================
Télécharge les modèles GGUF depuis HuggingFace pour utilisation
avec le GGUFHarmonicProxy (engine/llm/gguf_harmonizer.py).

Usage:
    python download_gguf_models.py --list          # Liste des modèles disponibles
    python download_gguf_models.py --download all  # Télécharge tout
    python download_gguf_models.py --download qwen # Télécharge Qwen uniquement
"""

import os
import sys
import json
import time
import hashlib
import argparse
from pathlib import Path

# Répertoire de stockage des modèles
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Liste des modèles GGUF supportés
AVAILABLE_MODELS = {
    "qwen3.5-32b": {
        "url": "https://huggingface.co/Qwen/Qwen3.5-32B-GGUF/resolve/main/qwen3.5-32b-q4_k_m.gguf",
        "filename": "qwen3.5-32b-q4_k_m.gguf",
        "size_gb": 20.5,
        "ram_gb": 24,
        "description": "Qwen3.5-32B-Instruct (Q4_K_M) — Meilleur rapport qualité/ressources",
        "alias": "qwen3.5-32b",
    },
    "qwen3.5-14b": {
        "url": "https://huggingface.co/Qwen/Qwen3.5-14B-GGUF/resolve/main/qwen3.5-14b-q4_k_m.gguf",
        "filename": "qwen3.5-14b-q4_k_m.gguf",
        "size_gb": 8.5,
        "ram_gb": 12,
        "description": "Qwen3.5-14B-Instruct (Q4_K_M) — Bon équilibre vitesse/qualité",
        "alias": "qwen3.5-14b",
    },
    "qwen3.5-7b": {
        "url": "https://huggingface.co/Qwen/Qwen3.5-7B-GGUF/resolve/main/qwen3.5-7b-q4_k_m.gguf",
        "filename": "qwen3.5-7b-q4_k_m.gguf",
        "size_gb": 4.5,
        "ram_gb": 8,
        "description": "Qwen3.5-7B-Instruct (Q4_K_M) — Léger, rapide, idéal pour GPU limité",
        "alias": "qwen3.5-7b",
    },
    "deepseek-v3-67b": {
        "url": "https://huggingface.co/DeepSeek/DeepSeek-V3-GGUF/resolve/main/deepseek-v3-67b-q4_k_m.gguf",
        "filename": "deepseek-v3-67b-q4_k_m.gguf",
        "size_gb": 38.0,
        "ram_gb": 48,
        "description": "DeepSeek-V3-67B-Instruct (Q4_K_M) — Le plus puissant, nécessite GPU 48Go+",
        "alias": "deepseek-v3-67b",
    },
    "deepseek-v3-24b": {
        "url": "https://huggingface.co/DeepSeek/DeepSeek-V3-GGUF/resolve/main/deepseek-v3-24b-q4_k_m.gguf",
        "filename": "deepseek-v3-24b-q4_k_m.gguf",
        "size_gb": 14.0,
        "ram_gb": 16,
        "description": "DeepSeek-V3-24B-Instruct (Q4_K_M) — Excellent rapport performance/ressources",
        "alias": "deepseek-v3-24b",
    },
    "deepseek-r1-14b": {
        "url": "https://huggingface.co/DeepSeek/DeepSeek-R1-GGUF/resolve/main/deepseek-r1-14b-q4_k_m.gguf",
        "filename": "deepseek-r1-14b-q4_k_m.gguf",
        "size_gb": 8.0,
        "ram_gb": 12,
        "description": "DeepSeek-R1-14B (Q4_K_M) — Raisonnement renforcé",
        "alias": "deepseek-r1-14b",
    },
    "phi-3.5-mini": {
        "url": "https://huggingface.co/microsoft/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-q4.gguf",
        "filename": "phi-3.5-mini-instruct-q4.gguf",
        "size_gb": 2.5,
        "ram_gb": 4,
        "description": "Phi-3.5-mini (Q4) — Ultra-léger, tourne sur Raspberry Pi 5",
        "alias": "phi-3.5-mini",
    },
}

# Téléchargeur simple avec reprise
def download_model(model_key: str, progress_callback=None):
    """Télécharge un modèle GGUF depuis HuggingFace."""
    model_info = AVAILABLE_MODELS.get(model_key)
    if not model_info:
        print(f"[ERREUR] Modèle '{model_key}' inconnu. Utilisez --list pour voir les disponibles.")
        return False
    
    filepath = MODELS_DIR / model_info["filename"]
    
    # Vérifier si déjà téléchargé
    if filepath.exists():
        size_gb = filepath.stat().st_size / (1024**3)
        print(f"  [OK] {model_info['filename']} déjà présent ({size_gb:.1f} Go)")
        return True
    
    print(f"\n  Téléchargement de {model_info['filename']}...")
    print(f"  Taille: {model_info['size_gb']:.1f} Go | RAM requise: {model_info['ram_gb']} Go")
    print(f"  Depuis: {model_info['url']}")
    print()
    
    try:
        import urllib.request
        
        def report(block_count, block_size, total_size):
            downloaded = block_count * block_size / (1024**3)
            total = total_size / (1024**3) if total_size > 0 else model_info["size_gb"]
            pct = min(100, block_count * block_size / total_size * 100) if total_size > 0 else 0
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            sys.stdout.write(f"\r    [{bar}] {downloaded:.1f}/{total:.1f} Go ({pct:.0f}%)")
            sys.stdout.flush()
            if progress_callback:
                progress_callback(pct)
        
        # Téléchargement avec urllib (progressif)
        urllib.request.urlretrieve(model_info["url"], filepath, reporthook=report)
        print(f"\n  ✓ Téléchargement terminé !")
        
        # Vérification
        actual_gb = filepath.stat().st_size / (1024**3)
        print(f"  Fichier: {filepath}")
        print(f"  Taille réelle: {actual_gb:.1f} Go")
        
        # Créer un fichier de métadonnées
        meta = {
            "model": model_key,
            "alias": model_info["alias"],
            "filename": model_info["filename"],
            "size_gb": actual_gb,
            "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "n_ctx": 8192,
                "n_gpu_layers": -1,
                "resonance_strength": 0.7,
            }
        }
        meta_path = filepath.with_suffix(".meta.json")
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"\n  [ERREUR] Échec du téléchargement: {e}")
        if filepath.exists():
            filepath.unlink()  # Nettoyer fichier partiel
        return False


def list_models():
    """Affiche la liste des modèles disponibles."""
    print(f"\n  {'='*60}")
    print(f"  MODÈLES GGUF DISPONIBLES")
    print(f"  {'='*60}")
    print(f"  Répertoire: {MODELS_DIR}")
    print()
    
    for key, info in AVAILABLE_MODELS.items():
        filepath = MODELS_DIR / info["filename"]
        status = "✓" if filepath.exists() else " "
        size_display = f"{filepath.stat().st_size/(1024**3):.1f} Go" if filepath.exists() else f"{info['size_gb']:.1f} Go"
        
        print(f"  [{status}] {key:<20s} {size_display:<8s} — {info['description']}")
    
    print()
    print(f"  Pour télécharger: python download_gguf_models.py --download <nom>")


def main():
    parser = argparse.ArgumentParser(
        description="Téléchargeur de modèles GGUF pour Harmonic AI"
    )
    parser.add_argument("--list", action="store_true", help="Liste des modèles disponibles")
    parser.add_argument("--download", type=str, default="",
                        help="Nom du modèle à télécharger (ou 'all' pour tout)")
    parser.add_argument("--path", type=str, default=str(MODELS_DIR),
                        help="Répertoire de destination")
    
    args = parser.parse_args()
    
    global MODELS_DIR
    MODELS_DIR = Path(args.path)
    MODELS_DIR.mkdir(exist_ok=True)
    
    print(f"\n  {'='*60}")
    print(f"  TÉLÉCHARGEUR DE MODÈLES GGUF — Harmonic AI")
    print(f"  {'='*60}")
    
    if args.list:
        list_models()
        return
    
    if args.download:
        if args.download == "all":
            print(f"  Téléchargement de TOUS les modèles...")
            success = 0
            for key in AVAILABLE_MODELS:
                if download_model(key):
                    success += 1
            print(f"\n  {success}/{len(AVAILABLE_MODELS)} modèles téléchargés.")
        elif args.download in AVAILABLE_MODELS:
            download_model(args.download)
        else:
            # Téléchargement par alias ou sous-chaîne
            found = [k for k, v in AVAILABLE_MODELS.items() 
                    if args.download in k or args.download in v["alias"]]
            if found:
                for key in found:
                    download_model(key)
            else:
                print(f"  [ERREUR] Aucun modèle correspondant à '{args.download}'")
                print(f"  Utilisez --list pour voir les modèles disponibles.")
        return
    
    # Mode interactif
    list_models()
    key = input("\n  Modèle à télécharger (ou 'all', 'q':quitter): ").strip().lower()
    if key and key != 'q':
        if key == 'all':
            for k in AVAILABLE_MODELS:
                download_model(k)
        elif key in AVAILABLE_MODELS:
            download_model(key)
        else:
            found = [k for k in AVAILABLE_MODELS if key in k]
            if found:
                for k in found:
                    download_model(k)
            else:
                print(f"  Modèle '{key}' inconnu.")


if __name__ == "__main__":
    main()
