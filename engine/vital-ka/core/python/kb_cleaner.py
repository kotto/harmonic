"""
KB Cleaner — Nettoyage et reclassification de la base de connaissance
======================================================================
Reclassifie les faits GENERAL avec detect_sector() v2 (word boundaries).
Dédoublonne les triplets identiques. Filtre les faits trop courts ou
manifestement triviaux.

Usage :
  python kb_cleaner.py                    # nettoie la KB 50K
  python kb_cleaner.py --input data/bootstrapper_output/knowledge_base_50k.npz
  python kb_cleaner.py --output data/bootstrapper_output/knowledge_base_cleaned.npz
"""

import sys, os, re, time, json, argparse
from pathlib import Path
from collections import Counter
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

from bootstrapper import detect_sector, SECTOR_KEYWORDS


# ═══════════════════════════════════════════════════════════════════════════════
# FILTRES
# ═══════════════════════════════════════════════════════════════════════════════

# Mots-outils / faits triviaux à filtrer
_TRIVIAL_RELATIONS = {
    'located in', 'is located in', 'contains', 'has', 'had', 'used',
    'is a', 'is an', 'was a', 'were', 'are',
    'includes', 'including', 'include', 'consists of',
    'named', 'called', 'known as',
    'such as', 'like',
}

_STOP_SUBJECTS = {
    'he', 'she', 'they', 'it', 'this', 'that', 'these', 'those',
    'one', 'two', 'three', 'first', 'second',
    'a', 'b', 'c', 'd', 'e', 'f', 'g',
    'also', 'later', 'however', 'thus', 'therefore',
    'various', 'several', 'many', 'some', 'other',
    'part', 'parts', 'form', 'forms', 'type', 'types',
    'number', 'numbers', 'list', 'lists',
    'example', 'examples', 'case', 'cases',
    'member', 'members', 'group', 'groups',
    'year', 'years', 'time',
}

# Patterns de bruit Wikipedia
_NOISE_PATTERNS = [
    r'^[0-9]+$',           # Nombres purs
    r'^[a-z]$',            # Lettre unique
    r'^\d{4}\s*$',         # Année seule (ex: "1905")
    r'^\d{1,2}\s*$',       # Petit nombre
    r'^\d{4}-\d{2}$',      # Date
    r'^\d{2}/\d{2}/\d{4}$',# Date format xx/xx/xxxx
]


def is_noise(sujet: str, relation: str, objet: str) -> bool:
    """Détermine si un fait est du bruit à filtrer."""
    s = sujet.lower().strip()
    o = objet.lower().strip()

    # Sujet trop court
    if len(s) < 2:
        return True

    # Objet trop court
    if len(o) < 3:
        return True

    # Sujet dans la liste stop
    if s in _STOP_SUBJECTS:
        return True

    # Patterns de bruit
    for pat in _NOISE_PATTERNS:
        if re.match(pat, s) or re.match(pat, o):
            return True

    # Fait trop court (pas informatif)
    if len(sujet) + len(objet) < 8:
        return True

    # Objet = sujet (boucle triviale)
    if s == o:
        return True

    return False


def deduplicate(facts: list) -> list:
    """Dédoublonne les faits par (sujet, relation, objet)."""
    seen = set()
    unique = []
    for s, r, o, sec in facts:
        key = (s.strip().lower(), r.strip().lower(), o.strip().lower())
        if key not in seen:
            seen.add(key)
            unique.append((s.strip(), r.strip(), o.strip(), sec))
    return unique


def reclassify(facts: list, verbose: bool = False) -> tuple:
    """
    Reclassifie les faits avec detect_sector() v2.
    Retourne (faits_reclassifies, stats).
    """
    reclassified = []
    changed = 0
    sector_before = Counter()
    sector_after = Counter()

    for s, r, o, sec in facts:
        sector_before[sec] += 1

        # Ne reclassifier que les GENERAL ou les secteurs non reconnus
        if sec == 'GENERAL' or sec not in SECTOR_KEYWORDS:
            new_sec = detect_sector(f"{s} {r} {o}")
            if new_sec != 'GENERAL' and new_sec != sec:
                changed += 1
                sec = new_sec

        sector_after[sec] += 1
        reclassified.append((s, r, o, sec))

    stats = {
        'total': len(facts),
        'reclassified': changed,
        'reclass_rate': round(changed / max(len(facts), 1) * 100, 1),
        'sector_before': dict(sector_before.most_common(10)),
        'sector_after': dict(sector_after.most_common(10)),
    }
    return reclassified, stats


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def clean_kb(input_path: str, output_path: str = None, verbose: bool = True):
    """
    Nettoie la base de connaissance :
      1. Charge
      2. Dédoublonne
      3. Filtre le bruit
      4. Reclassifie avec detect_sector() v2
      5. Sauvegarde
    """
    if verbose:
        print("=" * 60)
        print("KB CLEANER — Nettoyage + Reclassification")
        print("=" * 60)

    # 1. Charger
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"❌ Fichier introuvable : {input_path}")
        return

    data = np.load(str(input_path), allow_pickle=True)
    facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
    n_original = len(facts)
    if verbose:
        print(f"\n📂 Chargé : {n_original:,} faits")

    # 2. Dédoublonner
    facts = deduplicate(facts)
    n_dedup = len(facts)
    if verbose:
        print(f"🧹 Dédoublonnage : {n_original - n_dedup:,} doublons retirés → {n_dedup:,} uniques")

    # 3. Filtrer le bruit
    filtered = []
    noise_count = 0
    for s, r, o, sec in facts:
        if is_noise(s, r, o):
            noise_count += 1
        else:
            filtered.append((s, r, o, sec))
    n_filtered = len(filtered)
    if verbose:
        print(f"🔇 Bruit filtré   : {noise_count:,} faits triviaux retirés → {n_filtered:,} restants")

    # 4. Reclassifier avec detect_sector() v2
    cleaned, stats = reclassify(filtered, verbose)
    n_final = len(cleaned)
    if verbose:
        print(f"🏷️  Reclassifiés    : {stats['reclassified']:,} GENERAL → secteur spécifique ({stats['reclass_rate']}%)")
        print(f"\n📊 Distribution sectorielle AVANT reclassification (top 10):")
        for sec, count in stats['sector_before'].items():
            bar = '█' * int(count / max(stats['sector_before'].values()) * 30) if stats['sector_before'] else ''
            print(f"   {sec:20s} {count:>8,} {bar}")
        print(f"\n📊 Distribution sectorielle APRÈS (top 10):")
        for sec, count in stats['sector_after'].items():
            bar = '█' * int(count / max(stats['sector_after'].values()) * 30) if stats['sector_after'] else ''
            print(f"   {sec:20s} {count:>8,} {bar}")

    # 5. Sauvegarder
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_cleaned.npz"
    output_path = Path(output_path)

    facts_array = np.array(cleaned, dtype=object)
    np.savez(str(output_path), facts=facts_array)

    if verbose:
        print(f"\n💾 Sauvegardé : {output_path}")
        print(f"   {n_original:,} → {n_final:,} faits (retenus: {n_final/n_original*100:.1f}%)")
        print("=" * 60)

    return cleaned, stats


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nettoie et reclassifie la base de connaissance")
    parser.add_argument('--input', type=str,
                       default='data/bootstrapper_output/knowledge_base_50k.npz',
                       help='Fichier .npz d\'entrée')
    parser.add_argument('--output', type=str, default=None,
                       help='Fichier .npz de sortie (défaut: *_cleaned.npz)')
    parser.add_argument('--quiet', action='store_true', help='Mode silencieux')
    args = parser.parse_args()

    clean_kb(args.input, args.output, verbose=not args.quiet)
