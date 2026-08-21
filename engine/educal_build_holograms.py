"""
📚 educal_build_holograms.py — Hologrammes EDUCAL KA par discipline
====================================================================
Construit les hologrammes wave-native du domaine éducation (jumeau
de train_medical_holograms.py / build_official_holograms pour VITAL KA).

Hologrammes produits dans data/hologram_store/ (+ registre) :
  - official_education      : socle éducation (toutes matières)
  - edu_mathematiques       : algèbre, géométrie, arithmétique
  - edu_langues             : grammaire, vocabulaire, littérature
  - edu_sciences            : physique, chimie, SVT scolaire
  - edu_histoire_geo        : chronologies, civilisations, géographie
  - edu_philosophie         : penseurs, logique, éthique
  - edu_culture_civique     : institutions, droit, citoyenneté
  - edu_competences         : apprendre à apprendre (mémoire, méthode)

Sources de faits :
  1. community_KA Expander_education.npz (50K faits éducation)
  2. data/kb_enriched/shard_0000.npz (faits éducation du KB enrichi)
  3. domain_seeds.generate_education_facts() (faits interconnectés)
  4. educal_units.all_unit_facts() (les leçons s'ancrent dans la mémoire)

Pipeline identique au store officiel : filtrage → dédoublonnage global →
binding HRR (ψ = ψ_s ⊛ ψ_r ⊛ ψ_o) → mémoire H = Σ ψ_fait → NPZ + registre.

Lancer : python educal_build_holograms.py [--max-facts N] [--only official_education]
"""

import sys, time, json, random
from pathlib import Path
from collections import Counter
from typing import List, Tuple, Optional

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

import numpy as np

from hologram_store import HologramStore, OFFICIAL_DOMAINS
from domain_seeds import generate_education_facts
import educal_units

STORE_DIR = _ENGINE_DIR / 'data' / 'hologram_store'
COMMUNITY_EDU = STORE_DIR / 'community_KA Expander_education.npz'
KB_ENRICHED = _ENGINE_DIR / 'data' / 'kb_enriched' / 'shard_0000.npz'

# Secteurs & mots-clés du domaine éducation (aligné sur OFFICIAL_DOMAINS)
EDU_SECTORS = set(OFFICIAL_DOMAINS['education']['sectors'])
EDU_KEYWORDS = set(OFFICIAL_DOMAINS['education']['keywords'])

# ════════════════════════════════════════════════════════════════
# SOUS-DOMAINES (disciplines scolaires)
# ════════════════════════════════════════════════════════════════

EDU_SUBDOMAINS = {
    'edu_mathematiques': {
        'name': 'Mathématiques scolaires',
        'keywords': ['nombre', 'calcul', 'fraction', 'équation', 'géométrie',
                     'théorème', 'addition', 'multiplication', 'division', 'algèbre',
                     'fonction', 'probabilité', 'dérivée', 'intégrale', 'mathématique',
                     'arithmétique', 'axiome', 'angle', 'triangle', 'carré', 'somme',
                     'soustraction', 'pourcentage', 'distance', 'vitesse', 'mesure',
                     'entier', 'décimal', 'aire', 'périmètre', 'volume', 'racine'],
        'icon': '🔢', 'sectors': ['MATHS_PURES', 'MATHS_APPLI', 'SCIENCES'],
    },
    'edu_langues': {
        'name': 'Langues & Littérature',
        'keywords': ['grammaire', 'verbe', 'conjugaison', 'vocabulaire', 'orthographe',
                     'lecture', 'écriture', 'poésie', 'roman', 'langue', 'mot', 'phrase',
                     'synonyme', 'alphabet', 'littérature', 'écrivain', 'anglais',
                     'français', 'auteur', 'œuvre', 'traduction', 'étymologie'],
        'icon': '📖', 'sectors': ['LITTERATURE', 'LANGUES', 'CULTURE'],
    },
    'edu_sciences': {
        'name': 'Sciences scolaires',
        'keywords': ['physique', 'chimie', 'atome', 'molécule', 'énergie', 'force',
                     'onde', 'lumière', 'cellule', 'organisme', 'vivant', 'réaction',
                     'électricité', 'matière', 'écosystème', 'biologie', 'photosynthèse',
                     'circuit', 'gravité', 'température', 'masse', 'pression'],
        'icon': '🔬', 'sectors': ['SCIENCES', 'PHYSIQUE_FOND', 'PHYSIQUE_APPLI', 'BIOLOGIE'],
    },
    'edu_histoire_geo': {
        'name': 'Histoire & Géographie',
        'keywords': ['histoire', 'révolution', 'guerre', 'roi', 'empire', 'civilisation',
                     'bataille', 'traité', 'dynastie', 'capitale', 'pays', 'continent',
                     'fleuve', 'montagne', 'frontière', 'siècle', 'colonisation',
                     'république', 'royaume', 'empire romain', 'moyen âge'],
        'icon': '🌍', 'sectors': ['HISTOIRE', 'HIST', 'PASSE', 'GEOGRAPHIE', 'GEO'],
    },
    'edu_philosophie': {
        'name': 'Philosophie & Logique',
        'keywords': ['philosophie', 'penseur', 'logique', 'raison', 'éthique',
                     'argumentation', 'sagesse', 'connaissance', 'vérité', 'morale',
                     'existentialisme', 'platon', 'aristote', 'kant', 'socrate',
                     'descartes', 'nietzsche', 'conscience', 'liberté', 'doute'],
        'icon': '💭', 'sectors': ['PHILOSOPHIE', 'INTELLIGENCE'],
    },
    'edu_culture_civique': {
        'name': 'Culture civique & Droit',
        'keywords': ['citoyen', 'république', 'institutions', 'droit', 'loi', 'élection',
                     'constitution', 'justice', 'démocratie', 'devoir', 'état',
                     'gouvernement', 'parlement', 'vote', 'liberté d', 'laïcité'],
        'icon': '🏛️', 'sectors': ['CULTURE', 'DROIT', 'EDUCATION'],
    },
    'edu_competences': {
        'name': 'Apprendre à apprendre',
        'keywords': ['apprendre', 'mémoire', 'méthode', 'réviser', 'attention',
                     'concentration', 'motivation', 'pédagogie', 'étude', 'exercice',
                     'compétence', 'élève', 'professeur', 'apprentissage', 'mémorisation',
                     'répétition', 'cours', 'devoir', 'révision', 'compréhension'],
        'icon': '🧠', 'sectors': ['EDUCATION', 'INTELLIGENCE'],
    },
}


# ════════════════════════════════════════════════════════════════
# CHARGEMENT DES SOURCES
# ════════════════════════════════════════════════════════════════

def _clean_fact(fact: Tuple) -> Optional[Tuple]:
    """Filtre de qualité : garde les triplets lisibles et utiles."""
    s, r, o, sec = str(fact[0]).strip(), str(fact[1]).strip(), str(fact[2]).strip(), str(fact[3]).strip()
    if not s or not r or not o:
        return None
    if len(s) > 200 or len(o) > 200 or len(r) > 100:
        return None
    if len(s) < 2 or len(o) < 2:
        return None
    # Rejette les fragments type "her educational and social exploits"
    if s.islower() and s.count(' ') >= 5 and s[0].isalpha():
        return None
    return (s, r, o, sec.upper() if sec else 'EDUCATION')


def load_community_facts(max_per_sector: int = 1500) -> List[Tuple]:
    """Faits du hologramme communautaire éducation (50K), équilibrés par secteur."""
    if not COMMUNITY_EDU.exists():
        print(f"  ⚠ {COMMUNITY_EDU.name} absent")
        return []
    data = np.load(str(COMMUNITY_EDU), allow_pickle=True)
    raw = [(str(s), str(r), str(o), str(sec))
           for s, r, o, sec in zip(data['subjects'], data['relations'],
                                   data['objects'], data['sectors'])]
    # Équilibrage par secteur (les MATHS_PURES dominent 28K/50K)
    by_sector: dict = {}
    for f in raw:
        f = _clean_fact(f)
        if f:
            by_sector.setdefault(f[3], []).append(f)
    selected = []
    for sec, facts in by_sector.items():
        random.Random(42 + len(sec)).shuffle(facts)
        selected.extend(facts[:max_per_sector])
    print(f"  📄 community_KA Expander_education.npz → {len(selected):,} faits "
          f"(équilibrés, {len(by_sector)} secteurs)")
    return selected


def load_kb_enriched_education(max_facts: int = 2000) -> List[Tuple]:
    """Faits éducation du KB enrichi (filtrage secteurs + mots-clés)."""
    if not KB_ENRICHED.exists():
        print(f"  ⚠ {KB_ENRICHED.name} absent")
        return []
    data = np.load(str(KB_ENRICHED), allow_pickle=True)
    facts = []
    seen = set()
    for s, r, o, sec in zip(data['subjects'], data['relations'],
                            data['objects'], data['sectors']):
        f = _clean_fact((s, r, o, sec))
        if not f:
            continue
        text = f"{f[0]} {f[1]} {f[2]}".lower()
        if f[3] in EDU_SECTORS or any(kw in text for kw in EDU_KEYWORDS):
            key = (f[0].lower()[:60], f[1].lower()[:60], f[2].lower()[:80])
            if key not in seen:
                seen.add(key)
                facts.append(f)
        if len(facts) >= max_facts:
            break
    print(f"  📄 kb_enriched → {len(facts):,} faits éducation")
    return facts


def load_all_sources(max_per_sector: int = 1500, kb_max: int = 2000) -> List[Tuple]:
    """Toutes les sources de faits éducation, dédupliquées."""
    all_facts = []
    all_facts += load_community_facts(max_per_sector=max_per_sector)
    all_facts += load_kb_enriched_education(max_facts=kb_max)
    all_facts += generate_education_facts()
    all_facts += educal_units.all_unit_facts()

    # Dédoublonnage global
    seen = set()
    unique = []
    for f in all_facts:
        key = (f[0].lower()[:60], f[1].lower()[:60], f[2].lower()[:80])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    print(f"  📚 TOTAL : {len(unique):,} faits éducation uniques")
    return unique


# ════════════════════════════════════════════════════════════════
# HASH DE VERSIONNAGE
# ════════════════════════════════════════════════════════════════

def compute_kb_hash() -> str:
    import hashlib
    hasher = hashlib.sha256()
    for p in (COMMUNITY_EDU, KB_ENRICHED, _ENGINE_DIR / 'educal_units.py',
              _ENGINE_DIR / 'domain_seeds.py'):
        if p.exists():
            hasher.update(str(p.stat().st_mtime).encode())
            hasher.update(str(p.stat().st_size).encode())
    # Les unités éducatives contribuent aussi (leurs faits entrent dans H)
    for u in educal_units.list_units():
        p = educal_units.UNITS_DIR / f"{u['id']}.json"
        if p.exists():
            hasher.update(str(p.stat().st_mtime).encode())
    return hasher.hexdigest()[:16]


# ════════════════════════════════════════════════════════════════
# CONSTRUCTION
# ════════════════════════════════════════════════════════════════

def filter_by_subdomain(facts: List[Tuple], sub: dict, max_facts: int = 3000) -> List[Tuple]:
    """Filtre les faits d'une discipline (secteurs + mots-clés)."""
    sectors = set(sub.get('sectors', EDU_SECTORS))
    keywords = sub['keywords']
    kept = []
    for f in facts:
        text = f"{f[0]} {f[1]} {f[2]}".lower()
        if f[3] in sectors or any(kw in text for kw in keywords):
            kept.append(f)
    random.Random(7).shuffle(kept)
    return kept[:max_facts]


def main():
    args = sys.argv[1:]
    max_per_sector = 1500
    kb_max = 2000
    only = None
    skip_subs = False
    i = 0
    while i < len(args):
        if args[i] == '--max-facts' and i + 1 < len(args):
            max_per_sector = int(args[i + 1]); i += 2
        elif args[i] == '--kb-max' and i + 1 < len(args):
            kb_max = int(args[i + 1]); i += 2
        elif args[i] == '--only' and i + 1 < len(args):
            only = args[i + 1]; i += 2
        elif args[i] == '--skip-subs':
            skip_subs = True; i += 1
        else:
            i += 1

    print("═" * 65)
    print("  📚 EDUCAL KA — HOLOGRAMMES ÉDUCATIFS WAVE-NATIVE")
    print("═" * 65)

    store = HologramStore()
    kb_hash = compute_kb_hash()
    print(f"  🔑 KB hash: {kb_hash}")
    all_facts = load_all_sources(max_per_sector=max_per_sector, kb_max=kb_max)

    t0_total = time.time()

    # 1. Hologramme officiel éducation
    if only in (None, 'official_education'):
        print(f"\n🎯 official_education ({OFFICIAL_DOMAINS['education']['name']})")
        store._build_one_hologram('education', OFFICIAL_DOMAINS['education'],
                                  all_facts, kb_hash)

    # 2. Sous-hologrammes par discipline
    if not skip_subs and only in (None, 'subs'):
        for holo_id, sub in EDU_SUBDOMAINS.items():
            if only and only not in ('subs', holo_id):
                continue
            if only not in (None, 'subs', holo_id):
                continue
            sub_facts = filter_by_subdomain(all_facts, sub)
            if not sub_facts:
                print(f"  ⚠ {holo_id}: 0 faits — ignoré")
                continue
            domain_info = {
                'name': sub['name'],
                'icon': sub['icon'],
                'sectors': sub['sectors'],
                'keywords': sub['keywords'],
                'description': f"{sub['name']} — EDUCAL KA",
                'benchmark_questions': OFFICIAL_DOMAINS['education']['benchmark_questions'],
            }
            print(f"\n🎯 {holo_id} ({sub['name']}) — {len(sub_facts):,} faits filtrés")
            store._build_one_hologram('education', domain_info, sub_facts,
                                      kb_hash, holo_id=holo_id)

    dt = time.time() - t0_total
    print(f"\n{'═'*65}")
    print(f"  ⏱️ Durée totale : {dt:.0f}s")
    print(f"{'═'*65}")

    # Validation : rappel sur les hologrammes construits
    print("\n🧪 VALIDATION PAR RÉSONANCE (H ⊗ ψ_question) :")
    checks = [
        ('official_education', "Qu'est-ce que la pédagogie Montessori ?"),
        ('edu_mathematiques', "Qu'est-ce qu'une fraction ?"),
        ('edu_histoire_geo', "Révolution française"),
        ('edu_competences', "Comment fonctionne la mémoire ?"),
        ('edu_langues', "Grammaire française"),
        ('edu_sciences', "Qu'est-ce que la photosynthèse ?"),
    ]
    for holo_id, q in checks:
        try:
            res = store.recall(holo_id, q, top_k=3)
            top = ' | '.join(f"{s} {r} {o}" for s, r, o, _, _ in res[:3])
            print(f"  • {holo_id:<22s} '{q[:35]}' → {top[:110]}")
        except Exception as e:
            print(f"  • {holo_id:<22s} ERR: {e}")

    print("\n✅ Hologrammes éducatifs prêts dans data/hologram_store/")
    print("   Transférables via : GET /api/store/download/<holo_id> + POST /api/store/load")


if __name__ == '__main__':
    main()
