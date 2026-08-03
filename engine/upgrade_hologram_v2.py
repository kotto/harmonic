#!/usr/bin/env python3
"""
upgrade_hologram_v2.py — Migration hologramme v1 (psies 64D) → v2 (wave-native)
================================================================================

Les hologrammes communautaires v1 (psies_real/psies_imag, sans mémoire
holographique) ne peuvent pas faire de rappel ondulatoire H ⊗ ψ_query.
Cette migration ajoute les clés v2 (hologram_memory, psi_subjects,
psi_relations, psi_objects) en CONSERVANT les clés v1 (rétrocompatibilité
avec les scripts de build).

Pour le hologramme médical communautaire, on applique le même filtre
sectoriel/mots-clés que purify_holograms.py (whitelist médicale stricte)
pour ne pas faire entrer le bruit généraliste (faits juridiques anglais,
« canis lupus → bacteria »...) dans le pipeline de chat.

Usage:
    python upgrade_hologram_v2.py --holo "community_KA Expander_medecine"
"""

import sys
import json
import time
import logging
import argparse
from pathlib import Path
from collections import Counter

import numpy as np

# Setup
_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

from hologram_store import HologramStore, STORE_DIR, HOLOGRAM_FORMAT_VERSION
from holographic_encoder import HolographicEncoder, _circular_convolve
from purify_holograms import deduplicate_facts

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def clean_text(t: str) -> str:
    """Nettoie les artefacts de l'expander (numéros de bullet, **markdown**)."""
    import re
    t = str(t).strip()
    t = re.sub(r'^\d+\.\s*', '', t)          # "40. **...**"
    t = re.sub(r'\*\*', '', t)                # markdown bold
    t = re.sub(r'\s{2,}', ' ', t)             # espaces multiples
    return t.strip()


# Faits médicaux FRANÇAIS curés (le corpus communautaire est très anglophone :
# « diabetes is caused by insulin deficiency » — or l'utilisateur KA Mobile
# pose ses questions en français, et le plongement appris ne relie pas
# diabete ↔ diabetes, sim = -0.02). Ces faits ancrent lexicalement les
# requêtes françaises fréquentes.
CURATED_FR_FACTS = [
    ('diabete', 'est', 'une maladie chronique caracterisee par un exces de glucose dans le sang', 'SANTE'),
    ('diabete de type 1', 'est cause par', 'une deficience en insuline', 'SANTE'),
    ('diabete de type 2', 'est cause par', 'une resistance a l insuline', 'SANTE'),
    ('insuline', 'est utilisee pour', 'traiter le diabete', 'SANTE'),
    ('hypertension', 'est', 'une pression arterielle anormalement elevee', 'SANTE'),
    ('hypertension', 'augmente', 'le risque de maladies cardiovasculaires', 'SANTE'),
    ('paludisme', 'est transmis par', 'les moustiques anopheles', 'SANTE'),
    ('vaccin', 'est', 'une preparation qui entraine l immunite contre une maladie', 'SANTE'),
    ('antibiotique', 'est', 'un medicament qui tue les bacteries', 'SANTE'),
    ('cholesterol', 'est', 'une graisse indispensable aux cellules mais dangereuse en exces', 'SANTE'),
    ('grippe', 'est', 'une infection virale respiratoire saisonniere', 'SANTE'),
    ('anemie', 'est', 'une diminution du nombre de globules rouges', 'SANTE'),
]


def main():
    parser = argparse.ArgumentParser(description='Migrate v1 → v2 hologram')
    parser.add_argument('--holo', default='community_KA Expander_medecine',
                        help='Hologram ID to upgrade')
    args = parser.parse_args()

    store = HologramStore()
    holo_path = STORE_DIR / f'{args.holo}.npz'
    if not holo_path.exists():
        log.error(f"Introuvable: {holo_path}")
        sys.exit(1)

    data = np.load(str(holo_path), allow_pickle=True)
    facts = list(zip(data['subjects'].tolist(),
                     data['relations'].tolist(),
                     data['objects'].tolist(),
                     data['sectors'].tolist()))
    log.info(f"🔍 {args.holo}: {len(facts)} faits v1, keys={list(data.keys())}")

    # 1. Nettoyage texte (les secteurs v1 sont trop incohérents pour un
    #    whitelist — « MATHS_PURES » pour un fait sur le cancer — donc on
    #    garde TOUS les faits ; la qualité est filtrée à l'usage par le
    #    gate M4 + le filtre d'affichage, pas à la construction).
    cleaned = [(clean_text(s), clean_text(r), clean_text(o), sec)
               for s, r, o, sec in facts]
    cleaned = [(s, r, o, sec) for s, r, o, sec in cleaned if s or o]
    log.info(f"🧹 Après nettoyage: {len(cleaned)} faits")

    # 2. Dédoublonnage (exact uniquement — les doublons FR/EN sont gardés)
    canonical = deduplicate_facts(cleaned)
    log.info(f"♻️  Après dédoublonnage: {len(canonical)} faits")

    # 3. Faits français curés (ancres lexicales FR pour les requêtes mobiles)
    curated = [(s, r, o, sec) for s, r, o, sec in CURATED_FR_FACTS
               if (s, r, o) not in {(f[0], f[1], f[2]) for f in canonical}]
    canonical = canonical + curated
    log.info(f"➕ {len(curated)} faits français curés ajoutés → {len(canonical)}")
    if not canonical:
        log.error("Aucun fait conservé — abandon")
        sys.exit(1)

    # 4. Encodage ψ (composants = phrases, comme purify_holograms)
    encoder = HolographicEncoder()
    word_set = set()
    for s, r, o, _ in canonical:
        for w in s.split() + r.split() + o.split():
            w = w.strip('.,!?;:')
            if len(w) >= 2:
                word_set.add(w)
    for w in word_set:
        encoder.encode_word(w)

    psi_subjects = []
    psi_relations = []
    psi_objects = []
    psi_facts = []
    for s, r, o, _ in canonical:
        ps = encoder.encode_word(s)
        pr = encoder.encode_word(r)
        po = encoder.encode_word(o)
        psi_subjects.append(ps)
        psi_relations.append(pr)
        psi_objects.append(po)
        psi_facts.append(_circular_convolve(_circular_convolve(ps, pr), po))

    hologram_memory = np.sum(psi_facts, axis=0) / np.sqrt(len(psi_facts))

    # 5. Sauvegarde : clés v1 CONSERVÉES + clés v2 ajoutées
    out = {}
    for k in data.keys():
        out[k] = data[k]
    out['subjects'] = np.array([f[0] for f in canonical], dtype=object)
    out['relations'] = np.array([f[1] for f in canonical], dtype=object)
    out['objects'] = np.array([f[2] for f in canonical], dtype=object)
    out['sectors'] = np.array([f[3] for f in canonical], dtype=object)
    out['amplitudes'] = np.ones(len(canonical), dtype=np.float32)
    out['hologram_memory'] = hologram_memory.astype(np.complex64)
    out['psi_subjects'] = np.array(psi_subjects, dtype=np.complex64)
    out['psi_relations'] = np.array(psi_relations, dtype=np.complex64)
    out['psi_objects'] = np.array(psi_objects, dtype=np.complex64)
    out['version'] = HOLOGRAM_FORMAT_VERSION
    out['kb_hash'] = 'v2_upgrade'
    out['domain'] = 'medecine'
    out['created_at'] = time.time()

    np.savez_compressed(str(holo_path), **out)
    log.info(f"💾 Sauvé v2: {holo_path} ({len(canonical)} faits, "
             f"ψ {hologram_memory.shape})")

    # 6. Registre : version + facts_count à jour
    meta = store._registry.get(args.holo)
    if meta:
        meta.version = HOLOGRAM_FORMAT_VERSION
        meta.facts_count = len(canonical)
        meta.kb_hash = 'v2_upgrade'
        store._save_registry()
        log.info(f"📝 Registre mis à jour: {args.holo} → version 2, "
                 f"{len(canonical)} faits")

    # Échantillon des faits conservés
    subj_count = Counter(str(f[0]).lower() for f in canonical)
    log.info(f"🏷️  Top sujets: {[s for s, _ in subj_count.most_common(10)]}")


if __name__ == '__main__':
    main()
