import os, shutil, json
from pathlib import Path

MEDIA = Path("ka_mobile_media")
TRASH = Path("ka_mobile_trash")
STATS = Path("ka_mobile_stats.json")

# 1. Restore all trash back to media
for root, _, files in os.walk(str(TRASH)):
    for f in files:
        src = os.path.join(root, f)
        rel = os.path.relpath(src, str(TRASH))
        dst = os.path.join(str(MEDIA), rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            shutil.move(src, dst)

# 2. Delete all .hcvm/.hcv2
for f in list(MEDIA.rglob("*.hcvm")) + list(MEDIA.rglob("*.hcv2")):
    f.unlink()

# 3. Fresh stats
json.dump({
    "compressed": {},
    "total_original_bytes": 0,
    "total_compressed_bytes": 0,
    "files_count": 0,
    "first_run": "2026-08-21T12:30:00",
    "last_run": None
}, open(str(STATS), "w"), indent=2)

# Count
jpg_count = sum(1 for f in MEDIA.rglob("*") if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png'))
total_size = sum(f.stat().st_size for f in MEDIA.rglob("*") if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png'))
print("STATS", json.dumps({"jpg": jpg_count, "size_mb": round(total_size/1024/1024, 1), "trash_restored": True}, indent=2))