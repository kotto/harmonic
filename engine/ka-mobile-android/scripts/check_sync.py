#!/usr/bin/env python3
"""
check_sync.py — LE CONTRÔLE DE SYNCHRONISATION DE KA MOBILE
============================================================
Compare la source (www/) avec les copies Android et iOS et
rapporte les divergences. Sortie : 0 = tout est synchronisé.

Usage : python scripts/check_sync.py
"""
import filecmp
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WWW = ROOT / 'www'
COPIES = {
    'Android': ROOT / 'android' / 'app' / 'src' / 'main' / 'assets' / 'public',
    'iOS': ROOT / 'ios' / 'App' / 'App' / 'public',
}


def main() -> int:
    problems = 0
    sources = sorted(p for p in WWW.iterdir())
    for name, copy_dir in COPIES.items():
        print(f"── {name} ({copy_dir.relative_to(ROOT)})")
        if not copy_dir.exists():
            print(f"   ❌ copie absente: {copy_dir}")
            problems += 1
            continue
        for src in sources:
            dst = copy_dir / src.name
            if src.is_dir():
                if not dst.is_dir():
                    print(f"   ❌ dossier manquant : {src.name}/")
                    problems += 1
                continue
            if not dst.exists():
                print(f"   ❌ manquant : {src.name}")
                problems += 1
            elif not filecmp.cmp(src, dst, shallow=False):
                print(f"   ⚠️ diffère : {src.name}")
                problems += 1
        # fichiers orphelins dans la copie (absents de la source)
        for dst in sorted(p for p in copy_dir.iterdir() if p.is_file()):
            if not (WWW / dst.name).exists():
                print(f"   🗑️ orphelin dans la copie : {dst.name}")
                problems += 1

    print('─' * 40)
    if problems == 0:
        print('✅ SYNCHRONISÉ — 0 divergence (www/ est la source)')
        return 0
    print(f"❌ {problems} divergence(s) — corriger dans www/ puis resynchroniser")
    return 1


if __name__ == '__main__':
    sys.exit(main())
