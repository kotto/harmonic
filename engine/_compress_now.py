"""Force une passe de compression immédiate."""
import os, sys
from pathlib import Path

# Ensure module root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ka_background_compress import get_ghost

g = get_ghost()

# Migrer stats si elles utilisent encore old basename keys
updated = False
for key in list(g._stats['compressed'].keys()):
    sep_found = '/' in key or '\\' in key
    if not sep_found:
        old_val = g._stats['compressed'].pop(key)
        for root, _, files in os.walk(g.trash_dir):
            if key in files:
                rel = os.path.relpath(os.path.join(root, key), g.trash_dir)
                g._stats['compressed'][rel] = old_val
                updated = True
                break
if updated:
    g._save_stats()
    print('Stats migrées')

n = g.compress_now()
s = g.stats()
print(f'Compressés cette passe: {n}')
print(f'Total fichiers compressés: {s["files_count"]}')
remaining = sum(1 for f in Path(g.watch_dir).rglob('*') if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png'))
print(f'Fichiers restants: {remaining}')
print(f'Économie: {s["total_original_fmt"]} -> {s["total_compressed_fmt"]} ({s["total_saved_fmt"]} libérés)')