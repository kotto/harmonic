#!/usr/bin/env python3
"""
Validateur d'Hologramme — Pipeline de qualité automatisé
==========================================================
Nettoie et évalue un hologramme avant publication.

Étapes :
  1. DÉDUPLICATION      — faits identiques ou quasi-identiques
  2. CONTRADICTIONS     — "A est B" vs "A n'est pas B" ou "A est C" mutuellement exclusif
  3. COHÉRENCE          — sujets bien formés, relations variées, objets pertinents
  4. SCORE DE QUALITÉ   — agrégation pondérée → 0.0–1.0

Usage :
    python validate_hologram.py                           # tous les hologrammes
    python validate_hologram.py --holo official_medecine  # un seul
    python validate_hologram.py --fix                     # corrige automatiquement
"""

import re, json, math, argparse, sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Tuple, Dict, Set

# ═══════════════════════════════════════════════════════════════════════════════
# NORMALISATION
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    """Normalise un texte pour comparaison fuzzy."""
    t = text.lower().strip()
    for a, b in [('é','e'),('è','e'),('ê','e'),('ë','e'),('à','a'),('â','a'),
                 ('ù','u'),('û','u'),('ô','o'),('î','i'),('ï','i'),('ç','c'),
                 ('œ','oe'),('É','e'),('È','e'),('Ê','e'),('À','a')]:
        t = t.replace(a, b)
    t = re.sub(r'[^a-z0-9 ]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def _fact_key(s: str, r: str, o: str) -> str:
    """Clé unique normalisée pour un fait."""
    return f"{_normalize(s)}|{_normalize(r)[:60]}|{_normalize(o)}"

# ═══════════════════════════════════════════════════════════════════════════════
# 1. DÉDUPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def deduplicate(facts: List[Tuple[str, str, str, str]]) -> dict:
    """
    Détecte les doublons (exacts et fuzzy).

    Returns:
        {duplicates_removed: N, unique_facts: N, duplicate_pairs: [(a,b), ...], score: 0-1}
    """
    seen_exact = set()
    seen_fuzzy = {}  # normalized_key → (index, original)
    duplicates = []
    unique = []

    for i, (s, r, o, sec) in enumerate(facts):
        # Skip URIs and empty
        if 'wikidata.org' in str(s) or 'wikidata.org' in str(o):
            continue
        if not s or not r or not o:
            continue

        exact_key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
        fuzzy_key = _fact_key(s, r, o)

        # Exact duplicate
        if exact_key in seen_exact:
            duplicates.append((facts[i], "exact"))
            continue

        # Fuzzy duplicate (normalisé identique)
        if fuzzy_key in seen_fuzzy:
            duplicates.append((facts[i], "fuzzy"))
            continue

        seen_exact.add(exact_key)
        seen_fuzzy[fuzzy_key] = i
        unique.append(facts[i])

    dup_score = 1.0 - (len(duplicates) / max(len(facts), 1))
    return {
        'total_input': len(facts),
        'duplicates_removed': len(duplicates),
        'unique_facts': len(unique),
        'score': round(dup_score, 3),
        'unique': unique,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CONTRADICTIONS
# ═══════════════════════════════════════════════════════════════════════════════

_NEGATION_WORDS = {'pas', 'ne pas', 'non', "n'est pas", 'nest pas',
                   'aucun', 'jamais', 'sans', 'ni'}
_MUTUALLY_EXCLUSIVE = {
    ('vivant', 'mort'), ('vrai', 'faux'), ('chaud', 'froid'),
    ('grand', 'petit'), ('toujours', 'jamais'), ('tous', 'aucun'),
    ('possible', 'impossible'), ('animal', 'plante'), ('naturel', 'artificiel'),
}

def detect_contradictions(facts: List[Tuple[str, str, str, str]]) -> dict:
    """
    Détecte les contradictions entre faits.
    Pattern : si un sujet a deux objets mutuellement exclusifs.
    """
    subject_objects = defaultdict(list)  # sujet_normalisé → [(objet, index)]

    for i, (s, r, o, sec) in enumerate(facts):
        sn = _normalize(s)
        on = _normalize(o)
        subject_objects[sn].append((on, i))

    contradictions = []
    for sujet, obj_list in subject_objects.items():
        if len(obj_list) < 2:
            continue
        objs = [o for o, _ in obj_list]
        # Vérifier paires mutuellement exclusives
        for i in range(len(objs)):
            for j in range(i+1, len(objs)):
                pair = (objs[i], objs[j])
                rev = (objs[j], objs[i])
                if pair in _MUTUALLY_EXCLUSIVE or rev in _MUTUALLY_EXCLUSIVE:
                    contradictions.append({
                        'sujet': sujet,
                        'o1': objs[i], 'o2': objs[j],
                        'type': 'mutually_exclusive',
                    })

    score = 1.0 - (len(contradictions) / max(len(facts) * 0.01, 1))
    return {
        'contradictions_found': len(contradictions),
        'contradictions': contradictions[:10],
        'score': round(min(1.0, score), 3),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. COHÉRENCE
# ═══════════════════════════════════════════════════════════════════════════════

_RELATION_QUALITY = {
    'est': 0.3, 'a': 0.3, 'sont': 0.3, 'fait': 0.3,  # pauvres
    'cause': 0.7, 'implique': 0.7, 'permet': 0.7, 'nécessite': 0.8,
    'découvert': 1.0, 'inventé': 1.0, 'fondé': 1.0, 'écrit': 1.0,
    'contient': 0.8, 'produit': 0.8, 'régule': 0.9, 'maintient': 0.8,
    'capitale de': 1.0, 'situé à': 0.9, 'composé de': 0.8,
}

def check_coherence(facts: List[Tuple[str, str, str, str]]) -> dict:
    """
    Vérifie la cohérence structurelle des faits.
    - Relations variées (pas que 'est', 'a')
    - Sujets bien formés (pas de nombres seuls, pas d'URIs)
    - Objets informatifs (pas juste 'oui'/'non')
    """
    relations = Counter()
    bad_subjects = 0
    bad_objects = 0
    total = len(facts)

    for s, r, o, sec in facts:
        relations[r.lower().strip()] += 1

        # Sujets mal formés
        sn = str(s).strip()
        if len(sn) < 2 or sn.isdigit() or sn in (' ', '', 'None', 'nan'):
            bad_subjects += 1

        # Objets peu informatifs
        on = str(o).strip()
        if len(on) < 2 or on.lower() in ('oui', 'non', 'true', 'false', '0', '1', 'none'):
            bad_objects += 1

    # Score de diversité des relations
    unique_rels = len(relations)
    rel_variety = min(1.0, unique_rels / max(total * 0.1, 1))

    # Score de qualité des relations
    total_rel_score = sum(
        _RELATION_QUALITY.get(rel, 0.5) * count
        for rel, count in relations.items()
    )
    rel_quality = total_rel_score / max(total, 1)

    # Score global de cohérence
    bad_ratio = (bad_subjects + bad_objects) / max(total * 2, 1)
    score = (rel_variety * 0.3 + rel_quality * 0.4 + (1 - bad_ratio) * 0.3)

    return {
        'total_facts': total,
        'unique_relations': unique_rels,
        'top_relations': relations.most_common(5),
        'bad_subjects': bad_subjects,
        'bad_objects': bad_objects,
        'rel_variety': round(rel_variety, 3),
        'rel_quality': round(rel_quality, 3),
        'score': round(score, 3),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SCORE GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════

def validate_hologram(facts: List[Tuple[str, str, str, str]],
                      holo_name: str = "") -> dict:
    """
    Pipeline complet de validation d'un hologramme.
    Retourne un rapport détaillé avec score global.
    """
    if not facts:
        return {'error': 'Aucun fait à valider', 'quality_score': 0.0}

    # 1. Déduplication
    dedup_result = deduplicate(facts)
    unique_facts = dedup_result['unique']

    # 2. Contradictions
    contr_result = detect_contradictions(unique_facts)

    # 3. Cohérence
    coh_result = check_coherence(unique_facts)

    # 4. Score global pondéré
    quality_score = (
        dedup_result['score'] * 0.25 +
        contr_result['score'] * 0.30 +
        coh_result['score'] * 0.25 +
        min(1.0, len(unique_facts) / 1000) * 0.20  # bonus volume
    )

    return {
        'hologramme': holo_name,
        'quality_score': round(quality_score, 3),
        'deduplication': {
            'total': dedup_result['total_input'],
            'duplicates_removed': dedup_result['duplicates_removed'],
            'unique_remaining': dedup_result['unique_facts'],
            'score': dedup_result['score'],
        },
        'contradictions': {
            'found': contr_result['contradictions_found'],
            'examples': contr_result['contradictions'][:5],
            'score': contr_result['score'],
        },
        'coherence': coh_result,
        'verdict': _verdict(quality_score),
        'recommendations': _recommendations(dedup_result, contr_result, coh_result),
    }


def _verdict(score: float) -> str:
    if score >= 0.90: return "🌟 Excellent — prêt pour publication"
    if score >= 0.75: return "✅ Bon — publiable avec corrections mineures"
    if score >= 0.60: return "⚠️ Moyen — nécessite nettoyage avant publication"
    return "❌ Faible — reconstruction recommandée"


def _recommendations(dedup: dict, contr: dict, coh: dict) -> List[str]:
    recs = []
    if dedup['score'] < 0.90:
        recs.append(f"🔧 {dedup['duplicates_removed']} doublons à supprimer")
    if contr['score'] < 0.95:
        recs.append(f"⚠️ {contr['contradictions_found']} contradictions détectées")
    if coh['score'] < 0.70:
        recs.append("📝 Diversifier les relations (trop de 'est'/'a')")
    if coh['bad_subjects'] > 0:
        recs.append(f"🧹 {coh['bad_subjects']} sujets mal formés à nettoyer")
    if not recs:
        recs.append("✅ Aucun problème détecté")
    return recs


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Validateur de qualité d'hologramme")
    parser.add_argument('--holo', help='ID hologramme spécifique (ex: official_medecine)')
    parser.add_argument('--json', action='store_true', help='Sortie JSON uniquement')
    parser.add_argument('--fix', action='store_true', help='Corriger automatiquement (dédup)')
    args = parser.parse_args()

    from hologram_store import HologramStore
    hs = HologramStore()

    if args.holo:
        holo_ids = [args.holo]
    else:
        holo_ids = [h['id'] for h in hs.list_holograms(holo_type='official')]

    results = {}
    for holo_id in holo_ids:
        facts = hs.download(holo_id)
        if not facts:
            print(f"  ⚠️  {holo_id}: introuvable ou vide")
            continue

        result = validate_hologram(facts, holo_id)
        results[holo_id] = result

        if args.fix:
            # Appliquer la déduplication automatiquement
            unique = deduplicate(facts)['unique']
            # Re-publier (écrase l'ancien)
            meta = hs.download_metadata(holo_id)
            if meta:
                hs.publish(
                    domain=meta.get('domain', 'general'),
                    facts=unique,
                    author='KA (auto-fix)',
                    name=meta.get('name', holo_id),
                    description=meta.get('description', ''),
                )
                result['fixed'] = True

        if not args.json:
            print(f"\n{'='*60}")
            print(f"  {holo_id}")
            print(f"{'='*60}")
            print(f"  Qualité    : {result['quality_score']:.3f} — {result['verdict']}")
            print(f"  Faits      : {result['deduplication']['total']} → "
                  f"{result['deduplication']['unique_remaining']} uniques "
                  f"(-{result['deduplication']['duplicates_removed']} doublons)")
            print(f"  Relations  : {result['coherence']['unique_relations']} types, "
                  f"qualité moyenne {result['coherence']['rel_quality']:.2f}")
            for rec in result['recommendations']:
                print(f"  {rec}")

    # Sauvegarder le rapport
    out_path = Path('data/hologram_store/validation_report.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nRapport sauvegardé : {out_path}")

    # Mettre à jour le registry avec les vrais scores
    if not args.holo:
        try:
            registry_path = Path('data/hologram_store/registry.json')
            if registry_path.exists():
                registry = json.loads(registry_path.read_text(encoding='utf-8'))
                for holo_id, result in results.items():
                    if holo_id in registry:
                        registry[holo_id]['quality_score'] = result['quality_score']
                registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding='utf-8')
                print("Registry mis à jour avec les scores réels.")
        except Exception as e:
            print(f"Registry update skipped: {e}")


if __name__ == '__main__':
    main()
