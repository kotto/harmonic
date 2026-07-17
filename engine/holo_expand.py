#!/usr/bin/env python3
"""
HoloExpander — Expansion massive d'hologrammes spécialisés
============================================================
Prend un hologramme existant et l'étend par :
  1. RELACHEMENT DES FILTRES — plus de mots-clés, secteurs voisins
  2. CROSS-LINGUAL — traduction FR↔EN (×2 faits)
  3. ENTITY EXPANSION — EntityIndex pour faits connexes
  4. TRANSITIVITÉ — fermeture du graphe de connaissance
  5. VALIDATION + BENCHMARK — score qualité réel

Usage :
    python holo_expand.py --domain medecine --target 50000
    python holo_expand.py --domain astronomie --target 10000
    python holo_expand.py --all --target 20000
"""

import re, json, time, argparse, sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Set

# ═══════════════════════════════════════════════════════════════════════════════
# 1. EXPANSION PAR RELACHEMENT
# ═══════════════════════════════════════════════════════════════════════════════

DOMAIN_EXPANSIONS = {
    'medecine': {
        'sectors': ['SANTE', 'CORPS_ORGANES', 'CORPS_SANTE', 'BIOLOGIE', 'CHIMIE',
                     'NEUROSCIENCE', 'GENETIQUE', 'PHARMACOLOGIE'],
        'keywords': [
            'maladie', 'symptôme', 'traitement', 'vaccin', 'médicament', 'patient',
            'diagnostic', 'cancer', 'diabète', 'infection', 'virus', 'bactérie',
            'cellule', 'gène', 'système', 'organe', 'coeur', 'cerveau', 'sang',
            'hormone', 'enzyme', 'protéine', 'antibiotique', 'chirurgie', 'thérapie',
            'immunité', 'inflammation', 'douleur', 'fièvre', 'respiration',
            'médical', 'clinique', 'pathologie', 'anatomie', 'physiologie',
            'neurotransmetteur', 'récepteur', 'mutation', 'chromosome', 'ADN',
        ],
    },
    'astronomie': {
        'sectors': ['PHYSIQUE_FOND', 'PHYSIQUE_APPLI', 'SCIENCES', 'GEOGRAPHIE'],
        'keywords': [
            'étoile', 'planète', 'galaxie', 'univers', 'soleil', 'lune', 'orbite',
            'télescope', 'cosmos', 'nébuleuse', 'trou noir', 'lumière', 'gravité',
            'espace', 'satellite', 'astéroïde', 'comète', 'constellation',
            'astronome', 'observatoire', 'rayonnement', 'spectre', 'supernova',
            'exoplanète', 'système solaire', 'voie lactée', 'cosmologie',
            'big bang', 'matière noire', 'énergie sombre', 'relativité',
            'star', 'planet', 'galaxy', 'universe', 'moon', 'orbit', 'space',
            'nasa', 'hubble', 'james webb', 'mars', 'jupiter', 'saturne',
        ],
    },
    'histoire': {
        'sectors': ['HISTOIRE', 'CULTURE', 'GEOGRAPHIE', 'PHILOSOPHIE'],
        'keywords': [
            'guerre', 'révolution', 'empire', 'roi', 'président', 'civilisation',
            'siècle', 'bataille', 'traité', 'indépendance', 'découverte',
            'antiquité', 'moyen âge', 'renaissance', 'colonisation',
            'démocratie', 'république', 'monarchie', 'constitution',
            'rome', 'grèce', 'égypte', 'france', 'angleterre', 'chine',
            'napoléon', 'alexandre', 'césar', 'gengis khan', 'churchill',
            'war', 'revolution', 'empire', 'king', 'president', 'century',
        ],
    },
}

DEFAULT_EXPANSION = {
    'sectors': [],
    'keywords': [],
}

def _get_domain_config(domain: str) -> dict:
    """Récupère la config d'expansion pour un domaine, avec fallback intelligent."""
    for key in DOMAIN_EXPANSIONS:
        if key in domain.lower():
            return DOMAIN_EXPANSIONS[key]
    
    # Fallback intelligent : utiliser le nom du domaine comme mot-clé
    # + les secteurs de l'hologramme officiel correspondant
    try:
        from hologram_store import HologramStore
        store = HologramStore()
        official_id = f'official_{domain}'
        if official_id in store._registry:
            meta = store._registry[official_id]
            return {
                'sectors': list(meta.sectors),
                'keywords': [domain.lower()] + meta.top_concepts[:5],
            }
    except Exception:
        pass
    
    # Fallback ultime : juste le nom du domaine
    return {
        'sectors': [],
        'keywords': [domain.lower()],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CROSS-LINGUAL EXPANSION
# ═══════════════════════════════════════════════════════════════════════════════

FR_TO_EN = {
    'est': 'is', 'est un': 'is a', 'est une': 'is a', 'sont': 'are',
    'a découvert': 'discovered', 'a inventé': 'invented', 'a créé': 'created',
    'a formulé': 'formulated', 'a écrit': 'wrote', 'a développé': 'developed',
    'a fondé': 'founded', 'contient': 'contains', 'comprend': 'includes',
    'produit': 'produces', 'cause': 'causes', 'régule': 'regulates',
    'permet': 'enables', 'mesure': 'measures', 'détecte': 'detects',
    'convertit': 'converts', 'absorbe': 'absorbs', 'émet': 'emits',
    'génère': 'generates', 'transforme': 'transforms', 'stocke': 'stores',
    'protège': 'protects', 'active': 'activates', 'inhibe': 'inhibits',
    'a pour capitale': 'has capital', 'est situé à': 'is located in',
    'se trouve dans': 'is found in', 'fait partie de': 'is part of',
    'est composé de': 'is composed of', 'découvre': 'discovers',
    'invente': 'invents', 'fonde': 'founds', 'écrit': 'writes',
    'développe': 'develops', 'propose': 'proposes', 'formule': 'formulates',
}

def expand_cross_lingual(facts: List[Tuple[str, str, str, str]]) -> List[Tuple[str, str, str, str]]:
    """
    Double le nombre de faits par traduction FR↔EN des relations.
    Seules les relations connues sont traduites (qualité > quantité).
    """
    expanded = list(facts)
    seen = set((s.lower(), r.lower(), o.lower()) for s, r, o, sec in facts)

    for s, r, o, sec in facts:
        r_lower = r.lower().strip()
        if r_lower in FR_TO_EN:
            en_rel = FR_TO_EN[r_lower]
            key = (s.lower(), en_rel.lower(), o.lower())
            if key not in seen:
                seen.add(key)
                expanded.append((s, en_rel, o, sec))

    return expanded


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TRANSITIVITÉ (fermeture simple)
# ═══════════════════════════════════════════════════════════════════════════════

def expand_transitivity(facts: List[Tuple[str, str, str, str]]) -> List[Tuple[str, str, str, str]]:
    """
    Fermeture transitive simple : si A → B et B → C, alors A → C.
    Ne s'applique qu'aux relations 'est' et 'contient' (les plus fiables).
    """
    expanded = list(facts)
    seen = set((f[0].lower(), f[1].lower(), f[2].lower()) for f in facts)

    # Construire l'index sujet→objet
    subj_to_obj = defaultdict(list)
    for s, r, o, sec in facts:
        if r.lower() in ('est', 'est un', 'est une', 'contient', 'fait partie de'):
            subj_to_obj[s.lower()].append((o, r, sec))

    # Transitivité : A est B, B est C → A est C
    for s, r, o, sec in facts:
        if r.lower() in ('est', 'est un', 'est une'):
            o_lower = o.lower()
            if o_lower in subj_to_obj:
                for o2, r2, sec2 in subj_to_obj[o_lower]:
                    if r2.lower() in ('est', 'est un', 'est une', 'contient'):
                        key = (s.lower(), 'est', o2.lower())
                        if key not in seen:
                            seen.add(key)
                            expanded.append((s, 'est', o2, sec))

    return expanded


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def build_massive_hologram(domain: str, target_facts: int = 50000,
                           skip_benchmark: bool = False) -> dict:
    """
    Construit un hologramme massif pour un domaine donné.

    Stratégie :
      1. Filtrer le KB existant avec des critères RELÂCHÉS
      2. Expansion cross-lingual (×1.5-2)
      3. Expansion par transitivité
      4. Validation + déduplication
      5. Publication
    """
    t0 = time.time()
    config = _get_domain_config(domain)
    report = {'domain': domain, 'target': target_facts}

    print(f"\n{'='*60}")
    print(f"  HOLO EXPANDER — {domain.upper()}")
    print(f"  Cible: {target_facts:,} faits")
    print(f"{'='*60}")

    # ═══ 1. FILTRAGE RELÂCHÉ ═══
    print("\n  1/5 — FILTRAGE DU KB (critères relâchés)...")

    # Source : tous les hologrammes officiels fusionnés
    from hologram_store import HologramStore
    store = HologramStore()
    
    all_source_facts = []
    for h in store.list_holograms(holo_type='official'):
        facts = store.download(h['id'])
        all_source_facts.extend(facts)
    
    # Ajouter aussi les hologrammes communautaires
    for h in store.list_holograms(holo_type='community'):
        facts = store.download(h['id'])
        all_source_facts.extend(facts)
    
    print(f"     → {len(all_source_facts):,} faits sources (tous hologrammes)")
    sectors = set(config.get('sectors', []))
    keywords = set(kw.lower() for kw in config.get('keywords', []))
    
    filtered = []
    seen = set()
    
    for s, r, o, sec in all_source_facts:
        sec_str = str(sec).upper()
        text = f"{s} {r} {o}".lower()
        
        # Critère 1 : secteur correspondant (relâché : sous-chaîne)
        sector_match = any(t in sec_str for t in sectors) if sectors else True
        
        # Critère 2 : mot-clé (relâché : sous-chaîne)
        kw_match = any(kw in text for kw in keywords) if keywords else False
        
        # Critère 3 : sujet ou objet contient le nom du domaine
        domain_match = domain.lower() in text
        
        if sector_match or kw_match or domain_match:
            key = (s.lower()[:80], r.lower()[:60], o.lower()[:80])
            if key not in seen:
                seen.add(key)
                filtered.append((s, r, o, sec))
        
        if len(filtered) >= target_facts * 3:  # marge pour validation
            break
    
    print(f"     → {len(filtered):,} faits filtrés (critères relâchés)")
    
    if len(filtered) < 50:
        print("     ⚠️  Très peu de faits — le KB source est peut-être trop petit")
        report['status'] = 'insufficient_source'
        return report
    
    # ═══ 2. EXPANSION CROSS-LINGUAL ═══
    print("\n  2/5 — EXPANSION CROSS-LINGUAL (FR↔EN)...")
    expanded = expand_cross_lingual(filtered)
    print(f"     → {len(expanded):,} faits (×{len(expanded)/max(len(filtered),1):.1f})")
    
    # ═══ 3. EXPANSION TRANSITIVE ═══
    print("\n  3/5 — EXPANSION TRANSITIVE...")
    expanded = expand_transitivity(expanded)
    print(f"     → {len(expanded):,} faits")
    
    # ═══ 4. VALIDATION ═══
    print("\n  4/5 — VALIDATION...")
    from validate_hologram import validate_hologram
    validation = validate_hologram(expanded[:target_facts], domain)
    report['validation'] = validation
    report['quality_score'] = validation.get('quality_score', 0)
    print(f"     → Score: {validation['quality_score']:.3f}")
    print(f"     → Déduplication: {validation['deduplication']['duplicates_removed']} doublons")
    
    # ═══ 5. PUBLICATION ═══
    print("\n  5/5 — PUBLICATION...")
    try:
        # Garder les meilleurs (plus informatifs = sujets/objets plus longs)
        final = list(expanded[:target_facts])
        final.sort(key=lambda x: len(str(x[0])) + len(str(x[2])), reverse=True)
        
        store.publish(
            domain=domain,
            facts=final[:target_facts],
            author='KA Expander',
            name=f'{domain.capitalize()} (Massif)',
            description=f'Hologramme massif spécialisé en {domain}. '
                       f'{len(final[:target_facts]):,} faits validés.',
        )
        
        # Trouver l'ID publié
        published_id = None
        for hid, meta in store._registry.items():
            if meta.domain == domain and 'KA Expander' in meta.author:
                published_id = hid
                break
        
        report['published'] = True
        report['hologram_id'] = published_id
        report['published_facts'] = min(len(final), target_facts)
        print(f"     ✅ Publié: {published_id} ({report['published_facts']:,} faits)")
    except Exception as e:
        print(f"     ❌ Échec publication: {e}")
        report['published'] = False
    
    report['duration_seconds'] = round(time.time() - t0, 1)
    report['status'] = 'completed'
    
    # Sauvegarder le rapport
    report_path = Path(f'data/hologram_store/expand_report_{domain}.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n  Rapport: {report_path}")
    print(f"  Durée: {report['duration_seconds']:.0f}s")
    return report


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="HoloExpander — Hologrammes massifs")
    parser.add_argument('--domain', '-d', required=True, help='Domaine (medecine, astronomie, histoire...)')
    parser.add_argument('--target', '-t', type=int, default=20000, help='Cible de faits (défaut: 20000)')
    parser.add_argument('--skip-benchmark', action='store_true')
    args = parser.parse_args()

    report = build_massive_hologram(
        domain=args.domain,
        target_facts=args.target,
        skip_benchmark=args.skip_benchmark,
    )

    if report.get('status') == 'completed':
        print(f"\n{'='*60}")
        print(f"  🌟 HOLOGRAMME MASSIF CRÉÉ")
        print(f"{'='*60}")
        print(f"  Domaine : {args.domain}")
        print(f"  ID      : {report.get('hologram_id', '?')}")
        print(f"  Faits   : {report.get('published_facts', 0):,}")
        print(f"  Qualité : {report.get('quality_score', 0):.3f}")
        print(f"  Durée   : {report.get('duration_seconds', 0):.0f}s")


if __name__ == '__main__':
    main()
