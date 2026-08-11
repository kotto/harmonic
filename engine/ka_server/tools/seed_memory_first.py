#!/usr/bin/env python3
"""
seed_memory_first.py — LE CORPUS KA DANS LA MÉMOIRE (avec provenance)
=====================================================================
Charge la connaissance médicale de KA (data/vital_ka_*.json — 14 fichiers,
sources déclarées : WHO/ICRC, ATLS, AHA BLS 2024, OMS…) dans la mémoire
memory-first : chaque condition devient un FAIT (nom → conduite) avec sa
SOURCE — le chat répond « mémoire d'abord », jamais de fabrication.

Usage :
    python -m ka_server.tools.seed_memory_first            # tout le corpus
    python -m ka_server.tools.seed_memory_first --max 30   # sous-ensemble (tests)
"""

import argparse
import glob
import json
import sys
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

from ka_server.services.memory_first import stats as mf_stats  # noqa: E402
from ka_server.services.memory_first import store_fact  # noqa: E402

ANSWER_MAX = 200  # la réponse = le début de la conduite (tronqué proprement)


def _short(text: str, limit: int = ANSWER_MAX) -> str:
    """Résumé fidèle : le début du texte, coupé à la dernière phrase complète."""
    text = ' '.join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    last = max(cut.rfind('.'), cut.rfind('!'), cut.rfind(';'))
    return cut[:last + 1] if last > limit // 2 else cut + '…'


def _items(container) -> list:
    """Normalise conditions/pathologies/maladies — dict (clé → données) ou list."""
    if isinstance(container, dict):
        items = []
        for key, val in container.items():
            if isinstance(val, dict):
                item = dict(val)
                item.setdefault('nom', item.get('nom') or key)
                items.append(item)
            else:
                items.append({'nom': key, 'conduite': val})
        return items
    return list(container or [])


def _extract(item: dict) -> tuple:
    """(nom, conduite_résumé) — robuste aux structures variées du corpus."""
    nom = str(item.get('nom') or '').strip()
    conduite = item.get('conduite') or item.get('description') or ''
    if isinstance(conduite, dict):
        conduite = ' '.join(str(v) for v in conduite.values())
    conduite = _short(conduite)
    if not nom or not conduite:
        return None
    return (nom, conduite)


def seed(max_items: int | None = None) -> dict:
    """Charge le corpus dans la mémoire memory-first. Retourne le bilan."""
    files = sorted(glob.glob(str(_ENGINE_DIR / 'data' / 'vital_ka_*.json')))
    total = 0
    by_source = {}
    for f in files:
        try:
            d = json.loads(Path(f).read_text(encoding='utf-8'))
        except Exception:
            continue
        source = str(d.get('source') or Path(f).stem.replace('vital_ka_', 'KA '))
        # les conteneurs de contenu, dans l'ordre de richesse
        for key in ('conditions', 'pathologies', 'maladies', 'etapes'):
            if key not in d:
                continue
            for item in _items(d[key]):
                extracted = _extract(item)
                if extracted is None:
                    continue
                nom, conduite = extracted
                store_fact(nom, 'conduite', conduite, source=source)
                total += 1
                by_source[source] = by_source.get(source, 0) + 1
                if max_items and total >= max_items:
                    return _report(total, by_source, files)
    return _report(total, by_source, files)


def _report(total, by_source, files):
    return {'files': len(files), 'facts': total,
            'sources': by_source,
            'mechanism': 'apprentissage O(1) — un fait = une onde',
            'honesty': 'la réponse = le début de la conduite (tronqué) ; '
                       'la source complète est dans data/vital_ka_*.json'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Corpus KA → mémoire memory-first')
    parser.add_argument('--max', type=int, default=None,
                        help='Nombre max de faits (tests)')
    args = parser.parse_args()
    before = mf_stats()['facts']
    report = seed(max_items=args.max)
    after = mf_stats()['facts']
    print(f"✅ Corpus KA chargé : {report['facts']} faits "
          f"({before} → {after} en mémoire)")
    for src, n in sorted(report['sources'].items(), key=lambda x: -x[1]):
        print(f"   {src:30s} : {n}")
    print(f"   fichiers : {report['files']} · mécanisme : {report['mechanism']}")
