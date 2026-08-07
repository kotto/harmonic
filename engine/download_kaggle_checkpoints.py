"""
📥 download_kaggle_checkpoints.py — Récupération des checkpoints HWAT-Med
==========================================================================
Télécharge les checkpoints de l'entraînement Kaggle vers le dossier local.

Usage :
  python download_kaggle_checkpoints.py                    # checkpoints finaux
  python download_kaggle_checkpoints.py --all              # checkpoints + logs
  python download_kaggle_checkpoints.py --watch            # surveille + télécharge auto

Prérequis : CLI Kaggle authentifiée (kaggle auth login)
"""

import os, sys, time, json, shutil, argparse
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
KERNEL = "alainclmentkotto/hwat-med-125m-training"
OUTPUT_DIR = ENGINE / "checkpoints" / "hwat_med_125m"
LOG_DIR = ENGINE / "logs" / "kaggle"


def check_kernel_status() -> str:
    """Retourne le statut du kernel Kaggle."""
    import subprocess
    result = subprocess.run(
        ["kaggle", "kernels", "status", KERNEL],
        capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  Erreur status: {result.stderr.strip()[:100]}")
        return "UNKNOWN"
    status = result.stdout.strip().split("has status ")[-1].strip()
    return status


def download_output() -> Path:
    """Télécharge la sortie du kernel (checkpoints zip + log)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    import subprocess
    result = subprocess.run(
        ["kaggle", "kernels", "output", KERNEL, "-p", str(OUTPUT_DIR)],
        capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  Erreur download: {result.stderr.strip()[:200]}")
        return None

    # Extraire les fichiers
    extracted = 0
    for zip_path in OUTPUT_DIR.glob("*.zip"):
        print(f"  📦 Extraction: {zip_path.name}")
        shutil.unpack_archive(str(zip_path), str(OUTPUT_DIR))
        zip_path.unlink()
        extracted += 1

    # Log
    log_file = LOG_DIR / "training.log"
    try:
        shutil.copy(OUTPUT_DIR / f"{KERNEL.split('/')[-1]}.log", log_file)
    except Exception:
        pass

    return OUTPUT_DIR


def list_checkpoints() -> list:
    """Liste les checkpoints .pt téléchargés."""
    if not OUTPUT_DIR.exists():
        return []
    return sorted(OUTPUT_DIR.glob("*.pt"), key=lambda p: p.stat().st_mtime)


def main():
    parser = argparse.ArgumentParser(description="Télécharge les checkpoints Kaggle")
    parser.add_argument("--all", action="store_true", help="Télécharge checkpoints + logs")
    parser.add_argument("--watch", action="store_true",
                        help="Surveille le kernel et télécharge dès que terminé")
    parser.add_argument("--interval", type=int, default=300,
                        help="Intervalle de surveillance en secondes (défaut 300)")
    args = parser.parse_args()

    print("=" * 60)
    print("  📥 Téléchargement des checkpoints HWAT-Med (Kaggle)")
    print("=" * 60)

    if args.watch:
        print(f"\n  👁️  Surveillance du kernel {KERNEL}...")
        print(f"  (intervalle: {args.interval}s — Ctrl+C pour arrêter)\n")
        last_status = ""
        while True:
            status = check_kernel_status()
            if status != last_status:
                print(f"  ⏱️  {time.strftime('%H:%M:%S')} Statut: {status}")
                last_status = status

            if "COMPLETE" in status or "SUCCESS" in status:
                print("\n  ✅ Entraînement terminé ! Téléchargement des checkpoints...")
                download_output()
                print(f"\n  📂 Checkpoints dans: {OUTPUT_DIR}")
                for ck in list_checkpoints():
                    print(f"     • {ck.name} ({ck.stat().st_size/1e6:.1f} MB)")
                break
            elif "ERROR" in status or "CANCEL" in status:
                print("\n  ❌ Le kernel a échoué — téléchargement du log...")
                download_output()
                break

            time.sleep(args.interval)
    else:
        print(f"\n  📡 Statut: {check_kernel_status()}")
        print("\n  📦 Téléchargement...")
        out = download_output()
        if out:
            print(f"  📂 Checkpoints dans: {OUTPUT_DIR}")
            cks = list_checkpoints()
            if cks:
                for ck in cks:
                    print(f"     • {ck.name} ({ck.stat().st_size/1e6:.1f} MB)")
            else:
                print("     (aucun checkpoint .pt pour le moment — l'entraînement continue)")


if __name__ == "__main__":
    main()
