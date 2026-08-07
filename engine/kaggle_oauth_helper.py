"""
🔐 kaggle_oauth_helper.py — Flux OAuth Kaggle piloté par fichier
================================================================
Lance le flux OAuth Kaggle en arrière-plan :
  1. Génère l'URL d'autorisation et l'écrit dans kaggle_oauth_url.txt
  2. Attend que l'utilisateur colle son code dans kaggle_verification_code.txt
  3. Échange le code → sauvegarde les credentials (~/.kaggle/kaggle.json)

Usage :
  python kaggle_oauth_helper.py
  (processus en arrière-plan ; alimenter kaggle_verification_code.txt)
"""

import os, sys, time, builtins
from pathlib import Path

URL_FILE = Path(__file__).resolve().parent / "kaggle_oauth_url.txt"
CODE_FILE = Path(__file__).resolve().parent / "kaggle_verification_code.txt"


def file_input(prompt=None):
    """Remplace input() : attend le code dans un fichier (polling)."""
    if prompt:
        print(prompt, end="", flush=True)
    # Nettoyer un éventuel ancien fichier
    if CODE_FILE.exists():
        CODE_FILE.unlink()
    deadline = time.time() + 900  # 15 min max
    while not CODE_FILE.exists():
        if time.time() > deadline:
            print("\n⏱️  Délai dépassé (15 min) — abandon.")
            sys.exit(1)
        time.sleep(1)
    code = CODE_FILE.read_text(encoding="utf-8").strip()
    CODE_FILE.unlink(missing_ok=True)
    return code


def main():
    # Patch input() pour lire depuis un fichier
    builtins.input = file_input

    from kagglesdk.kaggle_oauth import KaggleOAuth
    from kagglesdk import KaggleClient

    client = KaggleClient()
    oauth = KaggleOAuth(client)
    oauth.authenticate(scopes=["resources.admin:*"], no_launch_browser=True)


if __name__ == "__main__":
    main()
