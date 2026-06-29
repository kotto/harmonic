"""
Training Loop — Relance automatique toutes les 2 heures
=========================================================
Execute train_continue.py par cycles de ~2h, sauvegarde les checkpoints.
Reprend automatiquement depuis le dernier checkpoint.

Lancer :
    python train_loop.py
    # ou avec nohup : nohup python train_loop.py > train_loop.log 2>&1 &
"""

import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime

ENGINE_DIR = Path(__file__).resolve().parent  # engine/
OUTPUT_DIR = ENGINE_DIR.parent / "data" / "training_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_TIME = 110       # minutes par cycle (~2h avec marge)
TOTAL_CYCLES = 6     # 6 cycles = ~12h
SLEEP_BETWEEN = 30   # secondes entre cycles


def run_cycle(cycle: int) -> int:
    """Execute un cycle d'entrainement."""
    print(f"\n{'='*60}")
    print(f"CYCLE {cycle}/{TOTAL_CYCLES} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    cmd = [
        sys.executable,
        str(ENGINE_DIR / "train_continue.py"),
        "--steps", "99999",
        "--batch_size", "2",
        "--seq_len", "64",
        "--save_every", "50",
        "--max_time", str(MAX_TIME),
        "--skip_calibration",
    ]

    result = subprocess.run(cmd, cwd=str(ENGINE_DIR))
    return result.returncode


def main():
    log_file = OUTPUT_DIR / "training_loop.log"

    with open(log_file, "a") as log:
        log.write(f"\n{'='*60}\n")
        log.write(f"TRAINING LOOP STARTED — {datetime.now()}\n")
        log.write(f"  Cycles: {TOTAL_CYCLES} x {MAX_TIME}min\n")
        log.write(f"  Output: {OUTPUT_DIR}\n")
        log.write(f"{'='*60}\n")

    for cycle in range(1, TOTAL_CYCLES + 1):
        rc = run_cycle(cycle)

        with open(log_file, "a") as log:
            log.write(f"Cycle {cycle}: rc={rc} — {datetime.now()}\n")

        # Vérifier les checkpoints
        ckpts = sorted(OUTPUT_DIR.glob("checkpoint_step_*.pt"))
        if ckpts:
            latest = max(ckpts, key=lambda p: p.stat().st_mtime)
            print(f"  Latest checkpoint: {latest.name} ({latest.stat().st_size/1e6:.0f} MB)")

        if cycle < TOTAL_CYCLES:
            print(f"  Sleeping {SLEEP_BETWEEN}s before next cycle...")
            time.sleep(SLEEP_BETWEEN)

    with open(log_file, "a") as log:
        log.write(f"\nTRAINING LOOP COMPLETE — {datetime.now()}\n")

    print(f"\n{'='*60}")
    print(f"TRAINING LOOP COMPLETE — {datetime.now()}")
    print(f"  Checkpoints: {OUTPUT_DIR}")
    ckpts = sorted(OUTPUT_DIR.glob("checkpoint_step_*.pt"))
    print(f"  Total checkpoints: {len(ckpts)}")
    if ckpts:
        print(f"  Latest: {max(ckpts, key=lambda p: p.stat().st_mtime).name}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
