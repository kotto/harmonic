"""
Batch Ingestion — DeepSeek → Harmonic Model (7000 textes)
===========================================================
Execute l'ingestion massive du corpus Wikipedia via DeepSeek.
Sauvegarde la base regulierement. Reprend en cas d'interruption.

Usage: python batch_ingest.py
"""

import os, sys, time, json, re
from pathlib import Path
import numpy as np

# Config — la clé API doit être définie dans l'environnement
_DEEPSEEK_KEY = os.getenv('DEEPSEEK_API_KEY')
if _DEEPSEEK_KEY:
    os.environ['DEEPSEEK_API_KEY'] = _DEEPSEEK_KEY
else:
    print("⚠️  DEEPSEEK_API_KEY non définie. Exportez-la avant d'exécuter ce script.")
    print("   export DEEPSEEK_API_KEY=sk-...")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bootstrapper import HarmonicBootstrapper, extract_triples_llm

CORPUS_DIR = Path('../data/corpus')
OUTPUT_DIR = Path('../data/bootstrapper_output')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_EVERY = 500  # sauvegarde tous les 500 textes
RATE_LIMIT = 0.3  # secondes entre appels

def main():
    # Charger corpus
    texts = []
    for path in sorted(CORPUS_DIR.glob('wiki_*.txt')):
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if 50 < len(line) < 300:
                    texts.append(line)
    print(f'Corpus: {len(texts)} textes')
    
    # Initialiser
    boot = HarmonicBootstrapper(use_memory=True)
    
    # Charger checkpoint si existe
    checkpoint_file = OUTPUT_DIR / 'checkpoint.json'
    start_idx = 0
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            ckpt = json.load(f)
            start_idx = ckpt.get('processed', 0)
            # Charger la base sauvegardee
            kb_file = OUTPUT_DIR / 'knowledge_base.npz'
            if kb_file.exists():
                facts = list(np.load(kb_file, allow_pickle=True)['facts'])
                for s, r, o, sec in facts:
                    if (s, r, o, sec) not in boot.model.knowledge_base:
                        boot.model.knowledge_base.append((s, r, o, sec))
                boot.model.kx, boot.model.ky, boot.model.w2i = __import__('harmonic_model').build_waves(boot.model.knowledge_base)
        print(f'Resume from {start_idx} (base: {len(boot.model.knowledge_base)} faits)')
    
    # Ingestion
    total_triples = 0
    errors = 0
    t0 = time.time()
    
    for i in range(start_idx, len(texts)):
        text = texts[i]
        try:
            triples = extract_triples_llm(text)
            for s, r, o, sec in triples:
                if len(s) >= 2 and len(o) >= 5:
                    boot.model.learn(s, r, o, sec)
                    total_triples += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f'  Error {i}: {e}')
        
        # Progression
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            rate = (i + 1 - start_idx) / elapsed
            remaining = (len(texts) - i - 1) / rate / 60
            print(f'  [{i+1}/{len(texts)}] {total_triples}t | '
                  f'{rate:.1f} txt/s | {remaining:.0f}min rest | '
                  f'base={len(boot.model.knowledge_base)} | err={errors}')
        
        # Checkpoint
        if (i + 1) % CHECKPOINT_EVERY == 0:
            # Sauvegarder la base
            facts_array = np.array(boot.model.knowledge_base, dtype=object)
            np.savez(str(OUTPUT_DIR / 'knowledge_base.npz'), facts=facts_array)
            # Sauvegarder le checkpoint
            with open(checkpoint_file, 'w') as f:
                json.dump({'processed': i + 1, 'triples': total_triples, 'errors': errors}, f)
            print(f'  [Checkpoint saved at {i+1}]')
        
        time.sleep(RATE_LIMIT)
    
    # Final
    elapsed = time.time() - t0
    print(f'\n{"="*60}')
    print(f'INGESTION COMPLETE')
    print(f'  Textes: {len(texts)}')
    print(f'  Triples: {total_triples}')
    print(f'  Erreurs: {errors}')
    print(f'  Duree: {elapsed/60:.0f}min')
    print(f'  Base finale: {len(boot.model.knowledge_base)} faits')
    print(f'  Vocabulaire: {boot.model.vocabulary_size} mots')
    print(f'{"="*60}')
    
    # Sauvegarde finale
    facts_array = np.array(boot.model.knowledge_base, dtype=object)
    np.savez(str(OUTPUT_DIR / 'knowledge_base_final.npz'), facts=facts_array)
    print(f'Base sauvegardee: {OUTPUT_DIR / "knowledge_base_final.npz"}')

if __name__ == '__main__':
    main()
