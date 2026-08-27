"""
🌊 knowledge_holograms.py — Constructeur d'hologrammes de connaissances
========================================================================
Construit des hologrammes de connaissances (wave-native) à partir du
corpus source (data/kb_enriched/shard_0000.npz) en filtrant par MOTS-CLÉS
(les secteurs du shard étant tous « GENERAL », le filtrage par secteur
échoue).

Chaque hologramme = domaine de connaissance encodé en ℂ⁵¹² :
  1. Charger les faits sources (sujet, relation, objet)
  2. Filtrer par mots-clés du domaine
  3. Dédoublonner (cross-domaine)
  4. Encoder ψ_s ⊛ ψ_r ⊛ ψ_o (binding HRR)
  5. Construire la mémoire holographique H = Σ ψ_fait
  6. Sauvegarder NPZ + registre
  7. Rappel testé par résonance

Usage :
    python ka_server/services/knowledge_holograms.py          # build + test
    python ka_server/services/knowledge_holograms.py --list   # lister

Auteur : Équipe KA — Univers-Holistique
Date   : 2026-08-25
"""

import logging
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ENGINE_DIR))

from hologram_store import HologramStore, _GLOBAL_DEDUP, _circular_convolve  # noqa: E402
from holographic_encoder import HolographicEncoder  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAINES DE CONNAISSANCE (mots-clés français — le shard est francophone)
# ═══════════════════════════════════════════════════════════════════════════════

KNOWLEDGE_DOMAINS = {
    'geographie': {
        'name': 'Géographie & Pays',
        'icon': '🌍',
        'keywords': [
            'pays', 'capitale', 'population', 'continent', 'superficie',
            'coordonnées', 'situé', 'fleuve', 'montagne', 'ville',
            'frontière', 'région', 'territoire', 'géographie',
            'a pour capitale', 'a une population', 'a une superficie',
            'est situé en', 'est situé à', 'est situé sur',
        ],
        'benchmark': [
            "capitale de la France",
            "population de la Chine",
            "plus grand pays d'Afrique",
            "capitale du Japon",
        ],
    },
    'astronomie': {
        'name': 'Astronomie & Espace',
        'icon': '🪐',
        'keywords': [
            'planète', 'étoile', 'galaxie', 'soleil', 'lune', 'système solaire',
            'trou noir', 'comète', 'astéroïde', 'orbite',
            'constellation', 'satellite', 'cosmologie',
            'a pour satellite', 'a été découvert en', 'a été découvert par',
            'astronome', 'planétaire',
        ],
        'benchmark': [
            "combien de planètes dans le système solaire",
            "quelle est la plus grande planète",
            "qu'est-ce qu'un trou noir",
        ],
    },
    'informatique': {
        'name': 'Informatique & Technologie',
        'icon': '💻',
        'keywords': [
            'ordinateur', 'algorithme', 'logiciel', 'internet',
            'réseau', 'programme', 'langage', 'programmation',
            'numérique', 'informatique', 'logiciel', 'navigateur',
            'système d\'exploitation', 'code source', 'base de données',
            'intelligence artificielle', 'robot', 'puce', 'microprocesseur',
        ],
        'benchmark': [
            "qui a inventé l'ordinateur",
            "qu'est-ce qu'un algorithme",
            "langages de programmation",
        ],
    },
    'physique': {
        'name': 'Physique',
        'icon': '⚛️',
        'keywords': [
            'lumière', 'atome', 'énergie', 'quantique', 'électron',
            'gravité', 'relativité', 'physique',
            'masse atomique', 'vitesse de la lumière', 'électricité',
            'magnétique', 'optique', 'photon', 'particule',
            'hologramme', 'holographie', 'mécanique quantique',
            'nombre atomique', 'symbole chimique',
        ],
        'benchmark': [
            "c'est quoi un hologramme",
            "qu'est-ce que la lumière",
            "vitesse de la lumière",
        ],
    },
    'chimie': {
        'name': 'Chimie',
        'icon': '🧪',
        'keywords': [
            'molécule', 'élément', 'réaction', 'acide', 'atome', 'composé',
            'métal', 'gaz', 'chimie', 'numéro atomique', 'symbole chimique',
            'oxygène', 'hydrogène', 'carbone', 'substance', 'élément chimique',
            'masse atomique',
        ],
        'benchmark': [
            "symbole chimique de l'oxygène",
            "qu'est-ce qu'une molécule",
        ],
    },
    'biologie': {
        'name': 'Biologie',
        'icon': '🧬',
        'keywords': [
            'cellule', 'gène', 'adn', 'protéine', 'enzyme', 'organisme',
            'bactérie', 'virus', 'biologie', 'espèce', 'animal', 'plante',
            'organe', 'tissu', 'métabolisme', 'photosynthèse',
            'appartient à la famille', 'contient le nutriment',
        ],
        'benchmark': [
            "qu'est-ce que l'ADN",
            "qu'est-ce qu'une cellule",
        ],
    },
    'medecine': {
        'name': 'Médecine & Santé',
        'icon': '🏥',
        'keywords': [
            'maladie', 'symptôme', 'traitement', 'vaccin', 'infection',
            'diagnostic', 'organe', 'médicament', 'pathologie', 'santé',
            'principeActif', 'spécialité', 'conduite', 'anasarque',
            'virus', 'bactérie', 'cancer', 'diabète', 'endocrinologie',
            'pédiatrie', 'cardiologie', 'toxique', 'toxicité',
        ],
        'benchmark': [
            "symptômes du diabète",
            "qu'est-ce qu'une infection",
        ],
    },
    'histoire': {
        'name': 'Histoire & Civilisations',
        'icon': '📜',
        'keywords': [
            'histoire', 'guerre', 'révolution', 'empire', 'roi', 'siècle',
            'civilisation', 'traité', 'bataille', 'dynastie', 'fondé',
            'a été fondé en', 'date de', 'philosophe', 'peintre',
            'écrivain', 'poète', 'mouvement', 'école', 'sculpteur',
            'architecte', 'compositeur',
        ],
        'benchmark': [
            "date de la Révolution française",
            "qui était Léonard de Vinci",
        ],
    },
    'culture': {
        'name': 'Art & Culture',
        'icon': '🎨',
        'keywords': [
            'art', 'musique', 'littérature', 'peinture', 'cinéma',
            'théâtre', 'poésie', 'sculpture', 'danse', 'œuvre', 'artiste',
            'peintre', 'écrivain', 'poète', 'compositeur',
            'appartient au mouvement', 'appartient à l\'école',
        ],
        'benchmark': [
            "auteur des Misérables",
            "mouvements artistiques",
        ],
    },
    'langues': {
        'name': 'Langues',
        'icon': '🗣️',
        'keywords': [
            'langue', 'langage', 'locuteur', 'dialecte', 'linguistique',
            'a pour nombre de locuteurs', 'est originaire de',
        ],
        'benchmark': [
            "nombre de locuteurs du français",
        ],
    },
}


def load_source_facts() -> List[Tuple[str, str, str, str]]:
    """Charge les faits sources depuis le shard enrichi."""
    shard = _ENGINE_DIR / 'data' / 'kb_enriched' / 'shard_0000.npz'
    if not shard.exists():
        log.warning(f"Shard source introuvable: {shard}")
        return []

    data = np.load(str(shard), allow_pickle=True)
    # ⚠️ Extraire les tableaux UNE SEULE FOIS : chaque accès data['x']
    # re-décompresse l'array depuis le NPZ (coût O(fichier) par accès).
    subjects = data['subjects']
    relations = data['relations']
    objects = data['objects']
    sectors = data['sectors'] if 'sectors' in data else None

    facts = []
    n = len(subjects)
    for i in range(n):
        facts.append((
            str(subjects[i]),
            str(relations[i]),
            str(objects[i]),
            str(sectors[i]) if sectors is not None else 'GENERAL',
        ))
    return facts


def _keyword_match(text_lower: str, keyword_lower: str) -> bool:
    """
    Matching tolérant d'un mot-clé :
    - Mots simples (sans espace) → frontières de mot (évite « trou » → « Touro »,
      « univers » → « université », « donnée » → « coordonnées »)
    - Expressions (avec espace) → sous-chaîne (ex : « a pour capitale »)
    """
    if ' ' in keyword_lower:
        return keyword_lower in text_lower
    # Mot simple : frontière de mot regex (les accents ne sont pas des frontières
    # \w en français, donc on inclut explicitement les caractères accentués)
    return bool(re.search(
        r'(?<![a-z0-9àâäéèêëîïôöùûüçœæ])' + re.escape(keyword_lower) +
        r'(?![a-z0-9àâäéèêëîïôöùûüçœæ])', text_lower))


def filter_by_keywords(facts: List[Tuple[str, str, str, str]],
                       keywords: List[str]) -> List[Tuple[str, str, str, str]]:
    """Filtre les faits dont le texte contient au moins un mot-clé."""
    kw_lower = [k.lower() for k in keywords]
    filtered = []
    for s, r, o, sec in facts:
        text = f"{s} {r} {o}".lower()
        if any(_keyword_match(text, k) for k in kw_lower):
            filtered.append((s, r, o, sec))
    return filtered


def build_knowledge_hologram(store: HologramStore, domain_id: str,
                             domain_info: dict, facts: List[Tuple]) -> dict:
    """
    Construit un hologramme wave-native pour un domaine filtré par mots-clés.
    """
    holo_id = f'knowledge_{domain_id}'

    # Vérifier si déjà construit et à jour
    existing = store.list_holograms()
    existing_ids = {h['id'] for h in existing}
    if holo_id in existing_ids:
        # Recenser (mise à jour) — on reconstruit pour être sûr
        pass

    # Dédoublonner + encoder + binding
    word_set = set()
    for s, r, o, _ in facts:
        for w in s.split() + r.split() + o.split():
            w = w.strip('.,!?;:()[]{}«»""\'\'¿¡')
            if len(w) >= 2:
                word_set.add(w)
    for w in word_set:
        store._encoder.encode_word(w)

    canonical_facts = []
    psi_facts = []
    for s, r, o, sec in facts:
        canon = _GLOBAL_DEDUP.get_or_register(s, r, o, sec)
        if canon != (s, r, o, sec):
            continue  # doublon cross-domaine
        canonical_facts.append(canon)
        psi_s = store._encoder.encode_word(s)
        psi_r = store._encoder.encode_word(r)
        psi_o = store._encoder.encode_word(o)
        psi_fact = _circular_convolve(_circular_convolve(psi_s, psi_r), psi_o)
        psi_facts.append(psi_fact)

    if not psi_facts:
        return {'domain': domain_id, 'facts_count': 0, 'status': 'empty'}

    # Mémoire holographique H = Σ ψ_fait
    hologram_memory = np.sum(psi_facts, axis=0)
    hologram_memory = hologram_memory / np.sqrt(len(psi_facts))

    # Sauvegarder NPZ
    holo_path = store.store_dir / f'{holo_id}.npz'
    subjects = np.array([f[0] for f in canonical_facts], dtype=object)
    relations = np.array([f[1] for f in canonical_facts], dtype=object)
    objects = np.array([f[2] for f in canonical_facts], dtype=object)
    sectors_arr = np.array([f[3] for f in canonical_facts], dtype=object)
    psi_subjects = np.array([store._encoder.encode_word(f[0]) for f in canonical_facts], dtype=np.complex128)
    psi_relations = np.array([store._encoder.encode_word(f[1]) for f in canonical_facts], dtype=np.complex128)
    psi_objects = np.array([store._encoder.encode_word(f[2]) for f in canonical_facts], dtype=np.complex128)

    np.savez_compressed(str(holo_path),
        subjects=subjects, relations=relations, objects=objects, sectors=sectors_arr,
        psi_subjects=psi_subjects, psi_relations=psi_relations, psi_objects=psi_objects,
        hologram_memory=hologram_memory,
        amplitudes=np.ones(len(canonical_facts), dtype=np.float32),
        version=2, kb_hash='knowledge_v1', domain=domain_id, created_at=time.time(),
    )

    # Registre
    from hologram_store import HologramMeta
    subj_count = Counter(str(f[0]).lower() for f in canonical_facts)
    top_concepts = [s for s, _ in subj_count.most_common(8)]
    size_kb = holo_path.stat().st_size / 1024
    meta = HologramMeta(
        id=holo_id, name=domain_info['name'], domain=domain_id,
        icon=domain_info['icon'], description=f"Connaissances {domain_info['name']}",
        facts_count=len(canonical_facts), sectors=list(set(f[3] for f in canonical_facts)),
        author='KA', type='official', created_at=time.time(),
        top_concepts=top_concepts, quality_score=0.0, benchmark_questions=len(domain_info.get('benchmark', [])),
        version=2, kb_hash='knowledge_v1',
    )
    meta._size_kb = size_kb
    store._registry[holo_id] = meta
    store._save_registry()

    return {
        'domain': domain_id, 'holo_id': holo_id,
        'facts_count': len(canonical_facts), 'size_kb': round(size_kb, 1),
        'top_concepts': top_concepts, 'status': 'built',
    }


def build_all_knowledge_holograms(store: HologramStore = None) -> List[dict]:
    """Construit tous les hologrammes de connaissances."""
    store = store or HologramStore()
    facts = load_source_facts()
    if not facts:
        log.error("Aucun fait source chargé")
        return []

    log.info(f"📦 {len(facts):,} faits sources chargés")

    results = []
    for domain_id, domain_info in KNOWLEDGE_DOMAINS.items():
        t0 = time.time()
        filtered = filter_by_keywords(facts, domain_info['keywords'])
        if len(filtered) < 10:
            log.info(f"  ⏭️ {domain_id}: seulement {len(filtered)} faits (seuil 10)")
            results.append({'domain': domain_id, 'facts_count': len(filtered),
                            'status': 'skipped (trop peu)'})
            continue

        r = build_knowledge_hologram(store, domain_id, domain_info, filtered)
        dt = time.time() - t0
        r['build_s'] = round(dt, 1)
        log.info(f"  {domain_info['icon']} {domain_id}: {r['facts_count']:,} faits "
                 f"({r['size_kb']} KB, {dt:.1f}s)")
        results.append(r)

    return results


def build_concepts_hologram(store: HologramStore = None) -> dict:
    """
    Construit l'hologramme des DÉFINITIONS (concepts de base) à partir du
    corpus curé `concepts_corpus.py` — car le shard Wikidata n'a pas de
    définitions.
    """
    from ka_server.services.concepts_corpus import CONCEPTS, all_triplets

    store = store or HologramStore()
    holo_id = 'knowledge_concepts'

    # Encodage des mots
    word_set = set()
    for domain, s, r, o in all_triplets():
        for w in s.split() + r.split() + o.split():
            w = w.strip('.,!?;:()[]{}«»""\'\'¿¡')
            if len(w) >= 2:
                word_set.add(w)
    for w in word_set:
        store._encoder.encode_word(w)

    # Binding + hologramme
    psi_facts = []
    for domain, s, r, o in all_triplets():
        psi_s = store._encoder.encode_word(s)
        psi_r = store._encoder.encode_word(r)
        psi_o = store._encoder.encode_word(o)
        psi_fact = _circular_convolve(_circular_convolve(psi_s, psi_r), psi_o)
        psi_facts.append(psi_fact)

    hologram_memory = np.sum(psi_facts, axis=0)
    hologram_memory = hologram_memory / np.sqrt(len(psi_facts))

    # Sauvegarde NPZ
    triplets = all_triplets()
    domains = np.array([t[0] for t in triplets], dtype=object)
    subjects = np.array([t[1] for t in triplets], dtype=object)
    relations = np.array([t[2] for t in triplets], dtype=object)
    objects = np.array([t[3] for t in triplets], dtype=object)

    holo_path = store.store_dir / f'{holo_id}.npz'
    np.savez_compressed(str(holo_path),
        domains=domains, subjects=subjects, relations=relations, objects=objects,
        hologram_memory=hologram_memory,
        amplitudes=np.ones(len(triplets), dtype=np.float32),
        version=2, kb_hash='concepts_v1', domain='concepts', created_at=time.time(),
    )

    # Registre
    from hologram_store import HologramMeta
    size_kb = holo_path.stat().st_size / 1024
    meta = HologramMeta(
        id=holo_id, name='Concepts & Définitions', domain='concepts',
        icon='📖', description='Définitions curées des concepts fondamentaux',
        facts_count=len(triplets), sectors=list(set(domains)),
        author='KA', type='official', created_at=time.time(),
        top_concepts=sorted(set(str(s) for _, s, _, _ in triplets))[:8],
        quality_score=0.0, benchmark_questions=0,
        version=2, kb_hash='concepts_v1',
    )
    meta._size_kb = size_kb
    store._registry[holo_id] = meta
    store._save_registry()

    return {
        'domain': 'concepts', 'holo_id': holo_id,
        'facts_count': len(triplets), 'size_kb': round(size_kb, 1),
        'top_concepts': [str(s) for _, s, _, _ in triplets[:8]],
        'status': 'built',
    }


def test_recall(store: HologramStore, queries: List[Tuple[str, str]]) -> None:
    """Teste le rappel holographique sur des questions représentatives."""
    print("\n" + "=" * 72)
    print("  🔮 TEST RAPPEL HOLOGRAPHIQUE")
    print("=" * 72)

    for holo_id, query in queries:
        results = store.recall(holo_id, query, top_k=3)
        print(f"\n  ❓ [{holo_id}] « {query} »")
        if not results:
            print("     → ∅ (aucun fait rappelé)")
            continue
        for s, r, o, sec, score in results:
            print(f"     [{score:.3f}] {str(s)[:40]} | {str(r)[:28]} | {str(o)[:45]}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   🧠 CONSTRUCTEUR D'HOLOGRAMMES DE CONNAISSANCES              ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    store = HologramStore()

    # Construction
    print("\n[1] Construction des hologrammes...")
    results = build_all_knowledge_holograms(store)

    print("\n[2] Résumé des hologrammes créés :")
    total_facts = 0
    for r in results:
        if r.get('status') == 'built':
            total_facts += r['facts_count']
            print(f"  {r.get('holo_id', ''):30s} {r['facts_count']:>6,} faits "
                  f"({r['size_kb']} KB) — top: {', '.join(r['top_concepts'][:3])}")
        else:
            print(f"  {r.get('domain', ''):30s} {r.get('status', '')}")

    print(f"\n  TOTAL : {total_facts:,} faits dans {sum(1 for r in results if r.get('status')=='built')} hologrammes")

    # Construction de l'hologramme des DÉFINITIONS
    print("\n[1bis] Construction de l'hologramme des DÉFINITIONS (concepts curés)...")
    cr = build_concepts_hologram(store)
    print(f"  📖 {cr['holo_id']}: {cr['facts_count']} faits ({cr['size_kb']} KB)")
    print(f"     top: {', '.join(cr['top_concepts'][:6])}")

    # Test rappel
    test_queries = [
        ('knowledge_physique', "c'est quoi un hologramme"),
        ('knowledge_physique', "qu'est-ce que la lumière"),
        ('knowledge_astronomie', "qu'est-ce qu'un trou noir"),
        ('knowledge_geographie', "capitale de la France"),
        ('knowledge_informatique', "qui a inventé l'ordinateur"),
        ('knowledge_histoire', "qui était Léonard de Vinci"),
        ('knowledge_biologie', "qu'est-ce que l'ADN"),
        ('knowledge_medecine', "symptômes du diabète"),
    ]
    test_recall(store, test_queries)

    # Test rappel des DÉFINITIONS (hologramme concepts)
    concept_queries = [
        ('knowledge_concepts', "c'est quoi un hologramme"),
        ('knowledge_concepts', "qu'est-ce que la lumière"),
        ('knowledge_concepts', "qu'est-ce que l'ADN"),
        ('knowledge_concepts', "qu'est-ce qu'un trou noir"),
        ('knowledge_concepts', "qu'est-ce qu'un ordinateur"),
        ('knowledge_concepts', "qu'est-ce qu'un algorithme"),
        ('knowledge_concepts', "qu'est-ce que la gravité"),
        ('knowledge_concepts', "qu'est-ce qu'une cellule"),
    ]
    test_recall(store, concept_queries)

    # Stats globales
    print("\n" + "=" * 72)
    print("  📊 STATS DU STORE")
    print("=" * 72)
    for k, v in store.stats().items():
        print(f"  {k}: {v}")

    print("\n✅ Construction terminée.")


if __name__ == '__main__':
    main()
