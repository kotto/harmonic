"""
🌊 massive_ingest.py — Ingestion massive nocturne en hologrammes séparés
========================================================================
Ingère 358 090 faits (knowledge_base_enriched.npz) répartis en ~14 hologrammes
séparés par SECTEUR. Robuste, reprenable, avec journal de progression.

Secteur → hologramme :
  HISTOIRE/PASSE            → kb_histoire          (~73,611)
  ECONOMIE                  → kb_economie          (~41,793)
  MATHS_PURES               → kb_maths             (~34,456)
  GEOGRAPHIE + pays/villes  → kb_geographie        (~29,196+)
  ASTRONOMIE/COSMOLOGIE     → kb_astronomie        (~19,603)
  CODE                      → kb_code              (~12,443)
  CULTURE/EXPRESSION/CREATION → kb_culture         (~5,584)
  BIOLOGIE/CORPS_ORGANES    → kb_biologie          (~1,554)
  PHYSIQUE_* / sciences     → kb_physique          (~1,121)
  SPIRITUALITE/CONSCIENCE   → kb_spiritualite      (~1,526)
  POLITIQUE                 → kb_politique         (~1,129)
  ECOLOGIE                  → kb_ecologie          (~277)
  technologie_complete      → kb_technologie       (~255)
  GENERAL/CROSS_DOMAIN/DISTILL/rest → kb_general   (~121,774)

Propriétés :
  - Encodage wave-native ℂ⁵¹² (binding HRR + superposition)
  - Dédoublonnage global cross-hologramme
  - Reprenable : saute les hologrammes déjà dans le registre
  - Journal : data/ingestion_log.txt + sortie console

Usage :
  python ka_server/services/massive_ingest.py            # build all
  python ka_server/services/massive_ingest.py --list     # lister sans builder
"""

import logging
import re
import sys
import time
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ENGINE_DIR))
sys.path.insert(0, str(_ENGINE_DIR / 'vital-ka' / 'core' / 'python'))

from hologram_store import HologramStore, _GLOBAL_DEDUP, _circular_convolve  # noqa: E402
from holographic_encoder import HolographicEncoder  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SOURCE_NPZ = _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'knowledge_base_enriched.npz'
LOG_FILE = _ENGINE_DIR / 'data' / 'ingestion_log.txt'

# Mapping secteur → hologramme. Chaque entrée = (holo_id, nom, icône, liste de secteurs)
HOLOGRAM_GROUPS = [
    ('kb_histoire',    'Histoire & Civilisations', '📜', ['HISTOIRE', 'PASSE']),
    ('kb_economie',    'Économie & Finance',       '💰', ['ECONOMIE']),
    ('kb_maths',       'Mathématiques',            '📐', ['MATHS_PURES']),
    ('kb_geographie',  'Géographie',               '🌍', ['GEOGRAPHIE']),
    ('kb_astronomie',  'Astronomie & Espace',      '🪐', ['ASTRONOMIE', 'COSMOLOGIE']),
    ('kb_code',        'Programmation & Code',     '💻', ['CODE']),
    ('kb_culture',     'Art & Culture',            '🎨', ['CULTURE', 'EXPRESSION', 'CREATION']),
    ('kb_biologie',    'Biologie & Corps',         '🧬', ['BIOLOGIE', 'CORPS_ORGANES']),
    ('kb_physique',    'Physique',                 '⚛️', ['PHYSIQUE_FOND', 'PHYSIQUE_APPLI', 'sciences_complete']),
    ('kb_spiritualite','Spiritualité & Conscience','🧘', ['SPIRITUALITE', 'CONSCIENCE']),
    ('kb_politique',   'Politique',                '🏛️', ['POLITIQUE']),
    ('kb_ecologie',    'Écologie',                 '🌱', ['ECOLOGIE']),
    ('kb_technologie', 'Technologie',              '🔧', ['technologie_complete']),
    ('kb_general',     'Général & Divers',         '📚', ['GENERAL', 'CROSS_DOMAIN', 'DISTILL']),
]

# Secteurs géographiques par préfixe (pays_monde_*, villes_monde_*, nature_complete, divers_complete)
_GEO_PREFIXES = ('pays_monde_', 'villes_monde_', 'nature_complete', 'divers_complete')


def _clean_token(t: str) -> str:
    """Nettoie un token : retire guillemets/ponctuation et espaces superflus."""
    t = str(t).strip()
    t = t.strip('"\'«»“”')
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def sector_to_group(sector: str) -> int:
    """Retourne l'index du groupe hologramme pour un secteur donné."""
    sec = str(sector).strip().upper()
    # 1. Correspondance exacte
    for i, (_, _, _, sectors) in enumerate(HOLOGRAM_GROUPS):
        if sec in [s.upper() for s in sectors]:
            return i
    # 2. Préfixes géographiques
    if sec.startswith(_GEO_PREFIXES):
        for i, (holo_id, _, _, _) in enumerate(HOLOGRAM_GROUPS):
            if holo_id == 'kb_geographie':
                return i
    # 3. Default → general
    for i, (holo_id, _, _, _) in enumerate(HOLOGRAM_GROUPS):
        if holo_id == 'kb_general':
            return i
    return len(HOLOGRAM_GROUPS) - 1


def load_enriched_facts() -> np.ndarray:
    """Charge les faits enrichis (358k) en liste de (s, r, o, secteur)."""
    data = np.load(str(SOURCE_NPZ), allow_pickle=True)
    subjects = data['subjects']
    relations = data['relations']
    objects = data['objects']
    sectors = data['sectors']

    facts = []
    n = len(subjects)
    for i in range(n):
        facts.append((
            _clean_token(subjects[i]),
            _clean_token(relations[i]),
            _clean_token(objects[i]),
            str(sectors[i]).strip(),
        ))
    return facts


def build_hologram(store: HologramStore, holo_id: str, name: str, icon: str,
                   facts: list) -> dict:
    """Construit un hologramme wave-native à partir de faits (s, r, o, secteur)."""
    from hologram_store import HologramMeta

    # Dédoublonner + encoder + binding
    word_set = set()
    for s, r, o, _ in facts:
        for w in s.split() + r.split() + o.split():
            w = w.strip('.,!?;:()[]{}«»""\'\'¿¡')
            if len(w) >= 2:
                word_set.add(w)
    for w in word_set:
        store._encoder.encode_word(w)

    canonical = []
    psi_facts = []
    for s, r, o, sec in facts:
        if not s or not r or not o:
            continue
        canon = _GLOBAL_DEDUP.get_or_register(s, r, o, sec)
        if canon != (s, r, o, sec):
            continue  # doublon cross-hologramme
        canonical.append(canon)
        psi_s = store._encoder.encode_word(s)
        psi_r = store._encoder.encode_word(r)
        psi_o = store._encoder.encode_word(o)
        psi_fact = _circular_convolve(_circular_convolve(psi_s, psi_r), psi_o)
        psi_facts.append(psi_fact)

    if not psi_facts:
        return {'holo_id': holo_id, 'facts_count': 0, 'status': 'empty'}

    hologram_memory = np.sum(psi_facts, axis=0)
    hologram_memory = hologram_memory / np.sqrt(len(psi_facts))

    # Sauvegarde NPZ
    holo_path = store.store_dir / f'{holo_id}.npz'
    np.savez_compressed(str(holo_path),
        subjects=np.array([f[0] for f in canonical], dtype=object),
        relations=np.array([f[1] for f in canonical], dtype=object),
        objects=np.array([f[2] for f in canonical], dtype=object),
        sectors=np.array([f[3] for f in canonical], dtype=object),
        psi_subjects=np.array([store._encoder.encode_word(f[0]) for f in canonical], dtype=np.complex64),
        psi_relations=np.array([store._encoder.encode_word(f[1]) for f in canonical], dtype=np.complex64),
        psi_objects=np.array([store._encoder.encode_word(f[2]) for f in canonical], dtype=np.complex64),
        hologram_memory=hologram_memory.astype(np.complex64),
        amplitudes=np.ones(len(canonical), dtype=np.float32),
        version=2, kb_hash='massive_v1', domain=holo_id, created_at=time.time(),
    )

    # Registre
    from collections import Counter
    subj_count = Counter(str(f[0]).lower() for f in canonical)
    top_concepts = [s for s, _ in subj_count.most_common(8)]
    size_kb = holo_path.stat().st_size / 1024
    meta = HologramMeta(
        id=holo_id, name=name, domain=holo_id, icon=icon,
        description=f'Ingestion massive — {name}',
        facts_count=len(canonical),
        sectors=list(set(f[3] for f in canonical)),
        author='KA', type='official', created_at=time.time(),
        top_concepts=top_concepts, quality_score=0.0, benchmark_questions=0,
        version=2, kb_hash='massive_v1',
    )
    meta._size_kb = size_kb
    store._registry[holo_id] = meta
    store._save_registry()

    return {
        'holo_id': holo_id, 'facts_count': len(canonical),
        'size_mb': round(size_kb / 1024, 1), 'top_concepts': top_concepts,
        'status': 'built',
    }


def log_progress(msg: str):
    """Écrit une ligne de progression dans le journal ET la console."""
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def main():
    logging.basicConfig(level=logging.WARNING, format='%(message)s')

    if '--list' in sys.argv:
        store = HologramStore()
        for h in store.list_holograms():
            print(f"  {h.get('id', '?'):28s} {h.get('facts_count', 0):>7,} faits")
        return

    log_progress("=" * 70)
    log_progress("🚀 INGESTION MASSIVE — DÉMARRAGE")
    log_progress("=" * 70)

    store = HologramStore()

    # Reprenable : hologrammes déjà construits
    existing = {h['id'] for h in store.list_holograms()}
    log_progress(f"Hologrammes déjà présents : {len(existing)}")

    # Chargement des faits
    t0 = time.time()
    facts = load_enriched_facts()
    log_progress(f"📦 {len(facts):,} faits chargés en {time.time()-t0:.1f}s")

    # Regrouper par secteur
    t0 = time.time()
    groups = [[] for _ in HOLOGRAM_GROUPS]
    for s, r, o, sec in facts:
        gi = sector_to_group(sec)
        groups[gi].append((s, r, o, sec))
    log_progress(f"🔀 Regroupement par secteur en {time.time()-t0:.1f}s")
    for i, (holo_id, name, icon, _) in enumerate(HOLOGRAM_GROUPS):
        log_progress(f"    {icon} {holo_id:20s} {len(groups[i]):>7,} faits")

    # Construction séquentielle (robuste : un échec n'arrête pas la nuit)
    log_progress("")
    log_progress("🏗️  Construction des hologrammes...")
    built_count = 0
    total_facts_built = 0
    t_start_all = time.time()

    for i, (holo_id, name, icon, _) in enumerate(HOLOGRAM_GROUPS):
        if holo_id in existing:
            log_progress(f"  ⏭️  {holo_id}: déjà construit, ignoré")
            continue
        if not groups[i]:
            log_progress(f"  ⏭️  {holo_id}: 0 fait, ignoré")
            continue

        t0 = time.time()
        try:
            r = build_hologram(store, holo_id, name, icon, groups[i])
            dt = time.time() - t0
            if r['status'] == 'built':
                built_count += 1
                total_facts_built += r['facts_count']
                log_progress(f"  ✅ {icon} {holo_id:20s} {r['facts_count']:>7,} faits "
                             f"({r['size_mb']} Mo) en {dt:.1f}s — "
                             f"top: {', '.join(r['top_concepts'][:3])}")
            else:
                log_progress(f"  ⚠️  {holo_id}: {r['status']}")
        except Exception as e:
            log_progress(f"  ❌ {holo_id}: ERREUR {e}")
            continue

    elapsed = time.time() - t_start_all
    log_progress("")
    log_progress("=" * 70)
    log_progress(f"🏁 INGESTION TERMINÉE — {built_count} hologrammes, "
                 f"{total_facts_built:,} faits, {elapsed:.0f}s")
    log_progress("=" * 70)


if __name__ == '__main__':
    main()
