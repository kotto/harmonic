"""
Ingestion Massive Nocturne — 50K → 200K+ faits
===============================================
Utilise Claude Haiku pour générer des faits ciblés par domaine.
Checkpoints toutes les 5000 lignes. Reprend en cas d'interruption.

Usage:
  python ingest_overnight.py              # utiliser la KB existante
  python ingest_overnight.py --resume     # reprendre après interruption
  python ingest_overnight.py --target 200000  # cible personnalisée
"""

import sys, os, time, json, random
import numpy as np
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bootstrapper import extract_triples_simple, detect_sector
from prompts_200 import PROMPTS as PROMPTS_200

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Utiliser les 200 prompts spécialisés
DOMAIN_PROMPTS = PROMPTS_200

TARGET_FACTS = 200000
CHECKPOINT_EVERY = 2000
BATCH_SIZE = 30  # faits par prompt LLM
RATE_LIMIT = 0.3  # secondes entre appels
OUTPUT_DIR = Path('../data/bootstrapper_output')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = OUTPUT_DIR / 'checkpoint_overnight.json'
OUTPUT_FILE = OUTPUT_DIR / 'knowledge_base_overnight.npz'

# (les prompts sont maintenant dans prompts_200.py)
# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def load_llm():
    """Charge le client LLM."""
    try:
        from bootstrapper import _LLM_AVAILABLE, _LLM
        if _LLM_AVAILABLE:
            return _LLM
    except Exception:
        pass
    return None


def parse_facts(text, default_sector="GENERAL"):
    """Parse la réponse LLM en liste de faits."""
    facts = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('Voici') or line.startswith('Format'):
            continue
        parts = line.split('|')
        if len(parts) >= 3:
            s = parts[0].strip().lower()
            r = parts[1].strip().lower()
            o = parts[2].strip().lower()
            if len(s) > 1 and len(o) > 2 and len(r) > 1:
                sec = detect_sector(f"{s} {r} {o}")
                if sec == "GENERAL":
                    sec = default_sector
                facts.append((s, r, o, sec))
    return facts


def save_checkpoint(facts, processed, added):
    """Sauvegarde checkpoint + KB partielle."""
    CHECKPOINT_FILE.write_text(json.dumps({
        'processed': processed,
        'total_facts': len(facts),
        'added': added,
        'timestamp': time.time(),
    }))
    np.savez(str(OUTPUT_FILE), facts=np.array(facts, dtype=object))


def main():
    target = TARGET_FACTS
    for arg in sys.argv[1:]:
        if arg.startswith('--target='):
            target = int(arg.split('=')[1])
    
    resume = '--resume' in sys.argv
    
    print("=" * 60)
    print(f"INGESTION MASSIVE NOCTURNE → {target:,} faits")
    print("=" * 60)
    
    # Charger LLM
    llm = load_llm()
    if not llm:
        print("❌ LLM non disponible. Arrêt.")
        return
    print(f"✅ LLM: disponible")
    
    # Charger les faits existants
    kb_path = OUTPUT_DIR / 'knowledge_base_50k.npz'
    if resume and OUTPUT_FILE.exists():
        data = np.load(str(OUTPUT_FILE), allow_pickle=True)
        facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
        print(f"📂 Reprise: {len(facts):,} faits")
    elif kb_path.exists():
        data = np.load(str(kb_path), allow_pickle=True)
        facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
        print(f"📂 Base 50K: {len(facts):,} faits")
    else:
        print("❌ Base 50K introuvable")
        return
    
    existing = set((s, r, o) for s, r, o, _ in facts)
    start_count = len(facts)
    total_added = 0
    processed = 0
    
    # Faire plusieurs passes si nécessaire
    max_passes = 3
    for pass_num in range(max_passes):
        if len(facts) >= target:
            break
        
        print(f"\n{'='*60}")
        print(f"PASSE {pass_num + 1}/{max_passes} — {len(facts):,} / {target:,} faits")
        print(f"{'='*60}")
        
        # Mélanger les prompts pour diversité
        prompts = list(DOMAIN_PROMPTS)
        random.shuffle(prompts)
        
        for sector, prompt in prompts:
            if len(facts) >= target:
                break
            
            try:
                print(f"  {sector}...", end=' ', flush=True)
                resp = llm.generate(prompt, category="factual")
                text = resp.content.strip()
                
                if not text:
                    print("vide")
                    continue
                
                batch = parse_facts(text, sector)
                added = 0
                for s, r, o, sec in batch:
                    if (s, r, o) not in existing:
                        facts.append((s, r, o, sec))
                        existing.add((s, r, o))
                        added += 1
                
                total_added += added
                processed += 1
                
                pct = len(facts) / target * 100
                print(f"+{added} ({len(facts):,} total, {pct:.1f}%)")
                
                # Checkpoint
                if processed % 5 == 0:
                    save_checkpoint(facts, processed, total_added)
                    print(f"    💾 Checkpoint: {len(facts):,} faits")
                
                time.sleep(RATE_LIMIT)
                
            except Exception as e:
                print(f"erreur: {e}")
                time.sleep(2)  # attendre un peu en cas d'erreur
    
    # Sauvegarde finale
    save_checkpoint(facts, processed, total_added)
    
    print(f"\n{'='*60}")
    print(f"TERMINÉ")
    print(f"  Départ: {start_count:,} faits")
    print(f"  Ajoutés: {total_added:,}")
    print(f"  Final: {len(facts):,} faits")
    print(f"  Sauvegardé: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
