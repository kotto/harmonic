"""
Watchdog — Maintient l'ingestion en vie jusqu'à la cible
==========================================================
Relance automatiquement ingest_overnight.py si le processus meurt.
S'arrête quand la cible est atteinte.

Usage:
  python watchdog_ingest.py --target 200000
"""

import sys, os, time, subprocess, json
from pathlib import Path

TARGET = 200000
CHECK_INTERVAL = 30  # secondes entre vérifications
MAX_RESTARTS = 20     # max redémarrages avant abandon

for arg in sys.argv[1:]:
    if arg.startswith('--target='):
        TARGET = int(arg.split('=')[1])

CHECKPOINT_FILE = Path('../data/bootstrapper_output/checkpoint_overnight.json')
OUTPUT_FILE = Path('../data/bootstrapper_output/knowledge_base_overnight.npz')
LOG_FILE = Path('../data/bootstrapper_output/ingest_overnight.log')

print(f"🛡️  Watchdog ingestion — cible: {TARGET:,} faits")
print(f"   Checkpoint: {CHECKPOINT_FILE}")
print(f"   Log: {LOG_FILE}")

restarts = 0
last_facts = 0
stuck_count = 0

while restarts < MAX_RESTARTS:
    # Vérifier si la cible est déjà atteinte
    if CHECKPOINT_FILE.exists():
        ckpt = json.loads(CHECKPOINT_FILE.read_text())
        current = ckpt.get('total_facts', 0)
        if current >= TARGET:
            print(f"✅ Cible atteinte: {current:,} faits!")
            break
    
    # Vérifier si le processus tourne
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                          capture_output=True, text=True, shell=True)
    python_running = 'python' in result.stdout.lower()
    
    if not python_running:
        restarts += 1
        print(f"⚠️  Processus Python mort. Redémarrage {restarts}/{MAX_RESTARTS}...")
        
        # Lancer l'ingestion en arrière-plan
        subprocess.Popen(
            ['python', 'ingest_overnight.py', '--resume', f'--target={TARGET}'],
            stdout=open(str(LOG_FILE), 'a'),
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).resolve().parent
        )
        time.sleep(10)
    else:
        # Vérifier la progression
        if CHECKPOINT_FILE.exists():
            ckpt = json.loads(CHECKPOINT_FILE.read_text())
            current = ckpt.get('total_facts', 0)
            progress = current / TARGET * 100
            
            if current == last_facts:
                stuck_count += 1
                if stuck_count > 10:  # 5 minutes sans progrès
                    print(f"⚠️  Bloqué à {current:,} faits depuis 5min. Kill & restart...")
                    subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                                 capture_output=True, shell=True)
                    stuck_count = 0
                    last_facts = 0
                    time.sleep(5)
                    continue
            else:
                stuck_count = 0
                last_facts = current
            
            print(f"📊 {current:,}/{TARGET:,} faits ({progress:.1f}%) — restart {restarts}")
    
    time.sleep(CHECK_INTERVAL)

print(f"\n{'='*50}")
print(f"Watchdog terminé. Restarts: {restarts}")
if CHECKPOINT_FILE.exists():
    ckpt = json.loads(CHECKPOINT_FILE.read_text())
    print(f"Faits finaux: {ckpt.get('total_facts', 0):,}")
