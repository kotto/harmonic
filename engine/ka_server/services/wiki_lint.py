"""
🌊 wiki_lint.py — Lint automatique du wiki de connaissances
============================================================
Analyse le wiki OKF pour détecter :
  - Contradictions : deux faits avec même sujet + relation opposée
  - Orphelins : concepts sans lien entrant
  - Couverture : domaines trop peu fournis, concepts isolés
  - Sources manquantes : champ `source:` pointant vers un fichier raw/ inexistant
  - Santé : score global de cohérence

Usage :
  from ka_server.services.wiki_lint import lint_wiki
  report = lint_wiki()
"""

import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
WIKI_DIR = _ENGINE_DIR / 'knowledge'
RAW_DIR = WIKI_DIR / 'raw'

# Relations d'opposition sémantique
_OPPOSITE_RELATIONS = {
    'est': 'n\'est pas',
    'est une': 'n\'est pas une',
    'est un': 'n\'est pas un',
    'a': 'n\'a pas',
    'contient': 'ne contient pas',
    'cause': 'ne cause pas',
    'permet': 'empêche',
    'affirme': 'contredit',
    'est causé par': 'empêche',
    'utilise': 'n\'utilise pas',
    'augmente': 'diminue',
    'accélère': 'ralentit',
    'active': 'désactive',
}

# Seuils de couverture
_MIN_CONCEPTS_PER_DOMAIN = 2
_MIN_FACTS_PER_CONCEPT = 1
_MAX_SCORE = 100.0


def _parse_file(path: Path) -> dict:
    """Parse rapide d'un fichier .md (frontmatter + faits + liens)."""
    text = path.read_text(encoding='utf-8')
    # Frontmatter simplifié
    meta = {}
    fm = re.search(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if fm:
        for line in fm.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip().strip('"\'')
    body = fm.string[fm.end():] if fm else text

    # Faits
    facts = []
    for line in body.splitlines():
        line = line.strip().lstrip('-*•').strip()
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3 and parts[0] and parts[1] and parts[2]:
                facts.append((parts[0], parts[1], parts[2]))

    # Liens sortants [[...]]
    links = re.findall(r'\[\[([^\]]+)\]\]', body)

    return {
        'id': meta.get('id', path.stem),
        'domain': meta.get('domain', path.parent.name),
        'title': meta.get('title', path.stem),
        'source': meta.get('source', ''),
        'facts': facts,
        'links': links,
        'path': path,
    }


def find_contradictions(entries: list) -> list:
    """
    Détecte les contradictions : même sujet, même objet, relation opposée.
    Ex: « lumière est une onde » vs « lumière n'est pas une onde ».
    """
    # Indexer les faits par (sujet, objet)
    by_subj_obj = defaultdict(list)
    for e in entries:
        for s, r, o in e['facts']:
            by_subj_obj[(s.lower(), o.lower())].append((r, e['id'], e['path']))

    contradictions = []
    for (s, o), rels in by_subj_obj.items():
        for i in range(len(rels)):
            for j in range(i + 1, len(rels)):
                r1, id1, p1 = rels[i]
                r2, id2, p2 = rels[j]
                # Vérifier si r1 et r2 sont opposés
                r1_norm = r1.lower().strip()
                r2_norm = r2.lower().strip()
                opposed = False
                for base, opp in _OPPOSITE_RELATIONS.items():
                    if (r1_norm == base and r2_norm == opp) or \
                       (r1_norm == opp and r2_norm == base):
                        opposed = True
                        break
                if opposed:
                    contradictions.append({
                        'sujet': s, 'objet': o,
                        'relation_1': r1, 'fichier_1': p1.name,
                        'relation_2': r2, 'fichier_2': p2.name,
                        'type': 'contradiction',
                    })
    return contradictions


def find_orphans(entries: list) -> list:
    """
    Détecte les concepts orphelins : aucun lien entrant depuis d'autres pages.
    """
    all_ids = {e['id'] for e in entries}
    inbound = defaultdict(int)
    for e in entries:
        for link in e['links']:
            link_id = link.strip().lower()
            if link_id in all_ids:
                inbound[link_id] += 1
            # Chercher aussi dans les faits
            for s, r, o in e['facts']:
                for word in s.split() + o.split():
                    w = word.lower().strip('.,!?;:')
                    if w in all_ids:
                        inbound[w] += 1

    orphans = []
    for e in entries:
        n_in = inbound.get(e['id'], 0)
        if n_in == 0:
            orphans.append({
                'id': e['id'],
                'title': e['title'],
                'domain': e['domain'],
                'path': e['path'].name,
                'type': 'orphelin',
            })
    return orphans


def check_coverage(entries: list) -> list:
    """Analyse la couverture : domaines sous-peuplés, concepts sans faits."""
    issues = []
    by_domain = defaultdict(list)
    for e in entries:
        by_domain[e['domain']].append(e)

    for domain, domain_entries in by_domain.items():
        if len(domain_entries) < _MIN_CONCEPTS_PER_DOMAIN:
            issues.append({
                'domain': domain,
                'concepts': len(domain_entries),
                'min_attendu': _MIN_CONCEPTS_PER_DOMAIN,
                'type': 'couverture_insuffisante',
                'message': f"Domaine '{domain}': {len(domain_entries)} concept(s) "
                           f"(min {_MIN_CONCEPTS_PER_DOMAIN} attendu)",
            })
        for e in domain_entries:
            if len(e['facts']) < _MIN_FACTS_PER_CONCEPT:
                issues.append({
                    'domain': domain,
                    'concept': e['id'],
                    'facts': len(e['facts']),
                    'type': 'peu_de_faits',
                    'message': f"'{e['id']}': {len(e['facts'])} fait(s) "
                               f"(min {_MIN_FACTS_PER_CONCEPT} attendu)",
                })
    return issues


def check_sources(entries: list) -> list:
    """Vérifie que les sources référencées existent dans raw/."""
    issues = []
    if not RAW_DIR.exists():
        issues.append({
            'type': 'raw_manquant',
            'message': "Le dossier raw/ n'existe pas. Créez knowledge/raw/.",
        })
        return issues

    raw_files = {f.stem for f in RAW_DIR.glob('*.md') if f.name != 'README.md'}

    for e in entries:
        if e['source']:
            if e['source'] not in raw_files:
                issues.append({
                    'type': 'source_manquante',
                    'concept': e['id'],
                    'source': e['source'],
                    'message': f"'{e['id']}' référence la source "
                               f"'{e['source']}' introuvable dans raw/",
                })
    return issues


def compute_health_score(entries: list, contradictions: list,
                         orphans: list, issues: list) -> float:
    """Score de santé globale [0, 100]."""
    score = _MAX_SCORE
    # Pénalités
    score -= len(contradictions) * 20  # -20 par contradiction
    # Les orphelins sont normaux dans un wiki sans liens [[explicites]]
    score -= min(len(orphans), 3) * 2   # -2 max si tous les concepts sont orphelins
    score -= len(issues) * 3            # -3 par autre problème
    # Bonus pour la couverture
    by_domain = defaultdict(list)
    for e in entries:
        by_domain[e['domain']].append(e)
    n_domains = len(by_domain)
    if n_domains >= 5:
        score += 5
    if n_domains >= 8:
        score += 5
    # Moyenne de faits par concept
    avg_facts = sum(len(e['facts']) for e in entries) / max(len(entries), 1)
    if avg_facts >= 3:
        score += 5
    return max(0.0, min(_MAX_SCORE, score))


def lint_wiki() -> dict:
    """Exécute l'analyse complète du wiki. Retourne un rapport structuré."""
    md_files = sorted(WIKI_DIR.rglob('*.md'))
    md_files = [f for f in md_files if f.name not in (
        'README.md', 'index.md', 'log.md', '.schema.json')]
    md_files = [f for f in md_files if 'raw' not in f.parts]

    entries = [_parse_file(f) for f in md_files]

    contradictions = find_contradictions(entries)
    orphans = find_orphans(entries)
    coverage = check_coverage(entries)
    sources = check_sources(entries)

    health = compute_health_score(entries, contradictions, orphans,
                                  coverage + sources)

    # Statistiques globales
    by_domain = defaultdict(list)
    total_facts = 0
    for e in entries:
        by_domain[e['domain']].append(e)
        total_facts += len(e['facts'])

    return {
        'health_score': round(health, 1),
        'total_concepts': len(entries),
        'total_facts': total_facts,
        'domains': len(by_domain),
        'contradictions': contradictions,
        'orphans': orphans,
        'coverage_issues': coverage,
        'source_issues': sources,
        'total_issues': len(contradictions) + len(orphans) + len(coverage) + len(sources),
        'per_domain': {
            d: {'concepts': len(e), 'facts': sum(len(x['facts']) for x in e)}
            for d, e in by_domain.items()
        },
    }


def print_report(report: dict):
    """Affiche un rapport de lint lisible."""
    print(f"🏥 SANTÉ DU WIKI : {report['health_score']}/100")
    print(f"   {report['total_concepts']} concepts, {report['total_facts']} faits, "
          f"{report['domains']} domaines, {report['total_issues']} problèmes\n")

    if report['contradictions']:
        print(f"❌ CONTRADICTIONS ({len(report['contradictions'])}) :")
        for c in report['contradictions'][:10]:
            print(f"   « {c['sujet']} {c['relation_1']} {c['objet'][:40]} » ({c['fichier_1']})")
            print(f"       vs  « {c['sujet']} {c['relation_2']} {c['objet'][:40]} » ({c['fichier_2']})")
        if len(report['contradictions']) > 10:
            print(f"   ... et {len(report['contradictions']) - 10} autres")
        print()

    if report['orphans']:
        print(f"👤 CONCEPTS ORPHELINS ({len(report['orphans'])}) :")
        for o in report['orphans'][:10]:
            print(f"   [{o['domain']}] {o['title']} ({o['path']})")
        if len(report['orphans']) > 10:
            print(f"   ... et {len(report['orphans']) - 10} autres")
        print()

    if report['coverage_issues']:
        print(f"📊 COUVERTURE ({len(report['coverage_issues'])}) :")
        for i in report['coverage_issues'][:10]:
            print(f"   {i['message']}")
        print()

    if report['source_issues']:
        print(f"🔗 SOURCES MANQUANTES ({len(report['source_issues'])}) :")
        for i in report['source_issues'][:5]:
            print(f"   {i['message']}")
        print()

    print(f"📊 PAR DOMAINE :")
    for d, info in sorted(report['per_domain'].items()):
        print(f"   {d:20s} {info['concepts']:>3d} concepts, {info['facts']:>4d} faits")


if __name__ == '__main__':
    print_report(lint_wiki())