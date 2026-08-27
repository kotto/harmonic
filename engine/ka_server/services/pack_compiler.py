"""
🌊 pack_compiler.py — Compilation des packs depuis knowledge_base_50k
====================================================================
Utilise la base de 51 000 faits propres et sectorisés (knowledge_base_50k)
pour générer les packs de connaissance. Pas besoin du LLM Oracle.

Pour chaque secteur, on crée un hologramme dédié. Les secteurs sont
mappés vers les packs définis dans pack_generator.py.

Usage :
  python ka_server/services/pack_compiler.py            # compile tous les packs
  python ka_server/services/pack_compiler.py --list     # lister les packs seulement
  python ka_server/services/pack_compiler.py --pack physique  # pack spécifique
"""

import logging
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ENGINE_DIR))
sys.path.insert(0, str(_ENGINE_DIR / 'vital-ka' / 'core' / 'python'))

WIKI_DIR = _ENGINE_DIR / 'knowledge'
SOURCE_NPZ = _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'knowledge_base_50k.npz'
PACKS_META_DIR = _ENGINE_DIR / 'data' / 'packs'

# Mapping secteur → pack_id
SECTOR_MAP = {
    'PHYSIQUE_FOND': 'physique', 'PHYSIQUE_APPLI': 'physique',
    'ASTRONOMIE': 'astronomie', 'COSMOLOGIE': 'astronomie',
    'BIOLOGIE': 'biologie',
    'CORPS_ORGANES': 'biologie', 'NATURE_ANIM': 'biologie', 'NATURE_VEGET': 'biologie',
    'MATHS_PURES': 'mathematiques', 'MATHS_APPLI': 'mathematiques',
    'CULTURE': 'art', 'CREATION': 'art', 'EXPRESSION': 'art',
    'MUSIQUE': 'art', 'LITTERATURE': 'art',
    'HISTOIRE': 'histoire', 'PASSE': 'histoire',
    'GEOGRAPHIE': 'geographie',
    'SPIRITUALITE': 'religion', 'CONSCIENCE': 'religion', 'METAPHYSIQUE': 'religion',
    'POLITIQUE': 'economie',
    'FUTUR': 'technologie',
    'ECOLOGIE': 'ecologie',
    'INTELLIGENCE': 'psychologie', 'EMOTION_POS': 'psychologie', 'EMOTION_NEG': 'psychologie',
    'LINGUISTIQUE': 'linguistique',
}

# Icônes par pack
PACK_ICONS = {
    'physique': '⚛️', 'astronomie': '🪐', 'biologie': '🧬',
    'mathematiques': '📐', 'art': '🎨', 'histoire': '📜',
    'geographie': '🌍', 'religion': '🕊️', 'economie': '💰',
    'technologie': '🔧', 'ecologie': '🌱', 'psychologie': '🧘',
    'linguistique': '🗣️',
}


def load_and_filter():
    """Charge les faits et les regroupe par pack."""
    if not SOURCE_NPZ.exists():
        log.error(f"Source introuvable: {SOURCE_NPZ}")
        return {}

    data = np.load(str(SOURCE_NPZ), allow_pickle=True)
    all_facts = data['facts']

    packs = defaultdict(list)

    for f in all_facts:
        sector = str(f[3]).strip()
        pack_id = SECTOR_MAP.get(sector)
        if not pack_id:
            continue

        s, r, o = str(f[0]).strip(), str(f[1]).strip(), str(f[2]).strip()

        # Normalisation : minuscules, sans accents
        import unicodedata
        s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('ascii').lower()
        r = unicodedata.normalize('NFD', r).encode('ascii', 'ignore').decode('ascii').lower()
        o = unicodedata.normalize('NFD', o).encode('ascii', 'ignore').decode('ascii').lower()

        # Nettoyer : supprimer les guillemets, normaliser espaces
        s = re.sub(r'[\"\'«»""]', '', s).strip()
        r = re.sub(r'[\"\'«»""]', '', r).strip()
        o = re.sub(r'[\"\'«»""]', '', o).strip()

        if len(s) < 2 or len(r) < 2 or len(o) < 2:
            continue
        if len(s) > 80 or len(o) > 120:
            continue

        packs[pack_id].append((s, r, o, sector))

    return packs


def write_concept(domain: str, concept_id: str, title: str, facts: list) -> Path:
    """Écrit un concept en .md dans knowledge/<domain>/."""
    domain_dir = WIKI_DIR / domain
    domain_dir.mkdir(parents=True, exist_ok=True)

    facts_lines = [f"- {s} | {r} | {o}" for s, r, o, _ in facts]
    md_content = f"""---
id: {concept_id}
domain: {domain}
title: {title}
type: concept
---

# {title}

{chr(10).join(facts_lines)}
"""
    filepath = domain_dir / f"{concept_id}.md"
    filepath.write_text(md_content, encoding='utf-8')
    return filepath


def compile_pack(pack_id: str, facts: list) -> dict:
    """Compile un pack complet : faits → concepts → .md → hologramme."""
    # Regrouper les faits par sujet (concept)
    from collections import Counter
    by_subject = defaultdict(list)
    for s, r, o, sec in facts:
        by_subject[s].append((s, r, o, sec))

    # Ne garder que les sujets avec au moins 2 faits
    # (pour que le rappel soit significatif)
    # et limiter à ~200 concepts par pack
    n_concepts = 0
    n_files = 0

    for subject, subject_facts in sorted(by_subject.items(), key=lambda x: -len(x[1])):
        if len(subject_facts) < 2:
            continue
        if n_concepts >= 200:
            break

        # ID du concept
        cid = re.sub(r'[^a-z0-9_]', '_', subject.lower())[:50]
        cid = re.sub(r'_+', '_', cid).strip('_')
        if not cid or len(cid) < 2:
            continue

        # Titre
        title = subject.capitalize() if subject else 'Concept'

        # Écrire le fichier
        write_concept(pack_id, cid, title, subject_facts)
        n_concepts += 1
        n_files += 1

    # Compiler via okf_compiler
    if n_files > 0:
        from ka_server.services.okf_compiler import compile_wiki
        report = compile_wiki(action=f'pack_compile|{pack_id}')
        facts_compiled = sum(r['facts'] for r in report['results'].values())
    else:
        report = {'results': {}}
        facts_compiled = 0

    return {
        'pack_id': pack_id,
        'concepts': n_concepts,
        'facts_compiled': facts_compiled,
    }


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    if '--list' in sys.argv:
        packs = load_and_filter()
        print(f"\n📦 PACKS DISPONIBLES ({len(packs)} packs)\n")
        for pid, facts in sorted(packs.items(), key=lambda x: -len(x[1])):
            icon = PACK_ICONS.get(pid, '📦')
            # Compter les sujets uniques
            subjects = set(f[0] for f in facts)
            print(f"  {icon} {pid:20s} {len(facts):>5,} faits, {len(subjects):>4} sujets")
        return

    packs = load_and_filter()
    if not packs:
        print("❌ Aucun fait trouvé dans la source.")
        return

    pack_target = None
    if '--pack' in sys.argv:
        idx = sys.argv.index('--pack')
        pack_target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ''

    results = []
    for pid, facts in sorted(packs.items(), key=lambda x: -len(x[1])):
        if pack_target and pid != pack_target:
            continue

        icon = PACK_ICONS.get(pid, '📦')
        print(f"\n📦 {icon} {pid}...", flush=True)
        t0 = time.time()
        r = compile_pack(pid, facts)
        dt = time.time() - t0
        print(f"   ✅ {r['concepts']} concepts, {r['facts_compiled']} faits compilés en {dt:.1f}s",
              flush=True)
        results.append(r)

    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ")
    print(f"{'='*60}")
    total_concepts = sum(r['concepts'] for r in results)
    total_facts = sum(r['facts_compiled'] for r in results)
    for r in results:
        icon = PACK_ICONS.get(r['pack_id'], '📦')
        print(f"  {icon} {r['pack_id']:20s} {r['concepts']:>4d} concepts")
    print(f"  {'─'*40}")
    print(f"  TOTAL{'':20s} {total_concepts:>4d} concepts, {total_facts} faits compilés")

    if not pack_target:
        print(f"\n📋 Tous les packs sont compilés.")
        print(f"📂 knowledge/<pack>/  →  fichiers .md")
        print(f"💾 Hologrammes : okf_<pack>.npz")


if __name__ == '__main__':
    main()