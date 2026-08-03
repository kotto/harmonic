#!/usr/bin/env python3
"""
enterprise_completion.py — Chaînon D Enterprise : les questions réelles
pilotent la complétion des départements
=====================================================================

Quand une question reste sans réponse (gate anti-hallucination), elle est
enregistrée (completion_queue.register_miss). Dès que les seuils sont
atteints (facette manquée 2×, sujet 3×), la COMPLÉTION se déclenche en
arrière-plan : le département est enrichi —

  1. texte du sujet (Wikipedia, stdlib urllib — réseau du VPS client),
  2. réponses aux questions des facettes manquantes (coverage_queries),
  3. corpus hors-ligne (SEED_CORPUS de l'onboarding) si réseau absent,
  4. déduplication avec les faits déjà présents.

La couverture est recalculée après chaque complétion et un rapport est
écrit dans data/completion_reports.json (visible au dashboard).
L'usage pilote la connaissance — l'auto-apprentissage est réel.
"""

import json
import logging
import re
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

_REPORTS_PATH = Path(__file__).resolve().parent / 'data' / 'completion_reports.json'
_MAX_REPORTS = 20
_HTTP_TIMEOUT = 5
_WIKI_UA = 'KA-Enterprise/4.1 (IA ondulatoire; contact: admin@entreprise.fr)'


# ═══════════════════════════════════════════════════════════════════════════════
# SOURCES DE COMPLÉTION
# ═══════════════════════════════════════════════════════════════════════════════

def _http_json(url: str) -> Optional[dict]:
    """GET JSON avec timeout court — jamais bloquant (thread daemon)."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': _WIKI_UA})
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception:
        return None


def wikipedia_text(query: str, lang: str = 'fr') -> str:
    """
    Extrait Wikipedia pour une requête (recherche → titre → résumé).
    Retourne '' si le réseau est indisponible ou rien trouvé.
    """
    q = (query or '').strip()
    if not q:
        return ''
    search = _http_json(
        f'https://{lang}.wikipedia.org/w/api.php?action=query&list=search'
        f'&srsearch={urllib.parse.quote(q)}&srlimit=1&format=json')
    if not search or not search.get('query', {}).get('search'):
        return ''
    title = search['query']['search'][0]['title']
    summary = _http_json(
        f'https://{lang}.wikipedia.org/api/rest_v1/page/summary/'
        f'{urllib.parse.quote(title)}')
    if not summary:
        return ''
    text = (summary.get('extract') or '').strip()
    return re.sub(r'\s+', ' ', text)


def _corpus_fallback(sujet: str) -> str:
    """Corpus hors-ligne des sujets canoniques (onboarding)."""
    try:
        from enterprise_onboard import SEED_CORPUS
        return SEED_CORPUS.get(sujet.lower().strip(), '')
    except Exception:
        return ''


# ═══════════════════════════════════════════════════════════════════════════════
# RAPPORTS
# ═══════════════════════════════════════════════════════════════════════════════

def _save_report(report: Dict) -> None:
    try:
        reports = _load_reports()
        reports.insert(0, report)
        del reports[_MAX_REPORTS:]
        _REPORTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _REPORTS_PATH.write_text(json.dumps(reports, ensure_ascii=False, indent=1),
                                 encoding='utf-8')
    except Exception:
        pass


def _load_reports() -> List[Dict]:
    try:
        if _REPORTS_PATH.exists():
            return json.loads(_REPORTS_PATH.read_text(encoding='utf-8'))
    except Exception:
        pass
    return []


def recent_reports(limit: int = 5) -> List[Dict]:
    return _load_reports()[:limit]


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLÉTION
# ═══════════════════════════════════════════════════════════════════════════════

def should_register_miss(result) -> bool:
    """
    Décide si une réponse doit être enregistrée comme « manque » pour le
    chaînon D : refus calibré (« Je ne trouve pas… ») ou confiance faible
    (< 0.4). Une réponse ancrée (même moyenne) n'encombre pas la file.
    """
    low = (result.answer or '').lower()
    if 'je ne trouve pas' in low or 'aucune information' in low:
        return True
    return float(result.confidence) < 0.4


def _existing(engine, department_id: str) -> str:
    """Texte des faits déjà présents (déduplication des ré-ingestions)."""
    return ' '.join(f.text for f in engine.facts.get(department_id, []))


def complete_department(engine, department_id: str, sujet: str,
                        facettes: Optional[List[str]] = None,
                        language: str = 'fr',
                        max_facettes: int = 3) -> Dict:
    """
    Complète un département (synchrone) : texte du sujet + questions des
    facettes manquantes, dédupliqués, ingérés ; couverture recalculée ;
    rapport écrit. Retourne le rapport.
    """
    dept = engine.departments.get(department_id)
    if not dept:
        return {'error': f'Département inconnu: {department_id}'}

    from facet_coverage import coverage_texts, coverage_queries
    faits = engine.facts.get(department_id, [])
    cov_before = coverage_texts([f.text for f in faits], sujet)

    # 1. Texte du sujet : Wikipedia d'abord, corpus hors-ligne sinon
    sujet_text = wikipedia_text(sujet, language)
    source = 'wikipedia'
    if len(sujet_text) < 150:
        sujet_text = _corpus_fallback(sujet)
        source = 'corpus_hors_ligne'

    extra: List[str] = []
    if len(sujet_text) >= 80:
        extra.append(sujet_text)

    # 2. Questions des facettes manquantes (demandées par l'usage + couverture)
    manquantes = list(dict.fromkeys((facettes or []) +
                                    cov_before.get('manquantes', [])))[:max_facettes]
    for facet in manquantes:
        for q in coverage_queries(sujet, [facet])[:2]:
            text = wikipedia_text(q, language)
            if len(text) >= 80:
                extra.append(f'— {facet} : {text}')

    # 3. Déduplication avec les faits déjà présents
    existing = _existing(engine, department_id)
    chunks = [t for t in extra if t and t[:120] not in existing]
    if not chunks:
        return {'department_id': department_id, 'sujet': sujet,
                'source': source, 'facts_ajoutes': 0,
                'facts_total': len(faits),
                'couverture_avant': round(cov_before.get('couverture', 0.0), 3),
                'couverture_apres': round(cov_before.get('couverture', 0.0), 3),
                'facettes_manquantes': cov_before.get('manquantes', []),
                'deja_complet': True}

    count = engine.ingest_text(department_id, '\n'.join(chunks),
                               source=f'completion_{source}')
    cov_after = coverage_texts(
        [f.text for f in engine.facts.get(department_id, [])], sujet)

    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'department_id': department_id,
        'sujet': sujet,
        'source': source,
        'facettes_ciblees': manquantes,
        'facts_ajoutes': count,
        'facts_total': len(engine.facts.get(department_id, [])),
        'couverture_avant': round(cov_before.get('couverture', 0.0), 3),
        'couverture_apres': round(cov_after.get('couverture', 0.0), 3),
        'facettes_manquantes': cov_after.get('manquantes', []),
    }
    _save_report(report)
    log.info(f"🌱 Complétion « {sujet} » [{source}] : +{count} faits, "
             f"couverture {report['couverture_avant']:.0%} → "
             f"{report['couverture_apres']:.0%}")
    return report


def complete_department_background(engine, department_id: str, sujet: str,
                                   facettes: Optional[List[str]] = None,
                                   language: str = 'fr') -> None:
    """Complétion en arrière-plan (thread daemon) — non bloquante."""
    def _run():
        try:
            complete_department(engine, department_id, sujet,
                                facettes=facettes, language=language)
        except Exception as e:
            log.error(f'⚠ Complétion « {sujet} »: {e}')
    threading.Thread(target=_run, daemon=True).start()


def run_pending(engine, limit: int = 3) -> Dict:
    """
    Traite les sujets en attente (file de complétion) : retrouve le
    département par nom, lance la complétion en arrière-plan.
    """
    try:
        from completion_queue import pop_priority
        pending = pop_priority(limit=limit)
    except Exception as e:
        return {'error': f'File: {e}', 'lances': 0}
    lances = 0
    for item in pending:
        sujet = item['sujet']
        dept = next((d for d in engine.departments.values()
                     if d.name.lower() == sujet.lower()), None)
        if dept is None:
            continue
        complete_department_background(engine, dept.id, dept.name,
                                       facettes=item.get('facettes'))
        lances += 1
    return {'lances': lances, 'sujets': [i['sujet'] for i in pending]}


def status() -> Dict:
    """État du chaînon D : file d'attente + derniers rapports de complétion."""
    try:
        from completion_queue import status as queue_status
        file = queue_status()
    except Exception:
        file = {}
    return {'file': file, 'rapports': recent_reports(3)}


if __name__ == '__main__':
    # Démonstration / test autonome
    import sys
    from ka_enterprise_core import EnterpriseEngine
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    eng = EnterpriseEngine(data_dir=str(tmp / 'data'))
    t = eng.create_tenant('Démo', 'demo@d.fr')
    d = eng.create_department(t.id, 'pharmacologie')
    # Département volontairement pauvre : 2 faits seulement
    eng.ingest_text(d.id, 'La pharmacologie etudie les medicaments.', source='seed')

    from completion_queue import register_miss
    # L'usage : 3 questions sans réponse sur le sujet → seuil sujet atteint
    for q in ['quels sont les effets secondaires ?',
              'comment agit la pharmacologie ?',
              'quelles sont les contre-indications ?']:
        m = register_miss(q, sujet='pharmacologie')
        print(f"miss « {q[:40]} » → {m['total']}/3")

    print('\n→ lancement de la complétion (Wikipedia ou corpus hors-ligne)…')
    r = complete_department(eng, d.id, 'pharmacologie',
                            facettes=[m['facette']])
    print(f"rapport : +{r['facts_ajoutes']} faits ({r['source']}), "
          f"couverture {r['couverture_avant']:.0%} → {r['couverture_apres']:.0%}")

    # La même question répond-elle mieux ?
    res = eng.ask('quels sont les effets secondaires ?', d.id)
    print(f"après complétion — confiance : {res.confidence:.2f} "
          f"| {res.answer[:80]}…")
    assert r['facts_ajoutes'] > 0, 'complétion vide'
    print('\n✅ CHAÎNON D ENTERPRISE OK')
