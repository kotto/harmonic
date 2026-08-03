#!/usr/bin/env python3
"""
completion_queue.py — Les questions réelles pilotent la complétion
====================================================================

Le chaînon final de la garantie « toutes sortes de questions » : quand
une question utilisateur reste SANS RÉPONSE (refus calibré ou confiance
faible), elle est enregistrée — sujet + facette probable (« quels sont
les symptomes de X ? » → facette symptomes). Dès qu'un sujet accumule
assez de manques, la COMPLÉTION se déclenche en arrière-plan : ingestion
massive ciblée sur les facettes manquantes, couverture recalculée et
écrite au registre. L'usage pilote la connaissance.

File persistée : data/completion_queue.json
  { sujet: { facette: count } }
"""

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional

# Seuil : une facette est « à compléter » après ce nombre de questions
# restées sans réponse ; un sujet déclenche la complétion à ce total
FACET_TRIGGER = 2
SUBJECT_TRIGGER = 3

_QUEUE_PATH = Path(__file__).resolve().parent / 'data' / 'completion_queue.json'
_lock = threading.Lock()


def _load() -> Dict[str, Dict[str, int]]:
    try:
        if _QUEUE_PATH.exists():
            return json.loads(_QUEUE_PATH.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {}


def _save(queue: Dict[str, Dict[str, int]]):
    try:
        _QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=1),
                               encoding='utf-8')
    except Exception:
        pass


def register_miss(question: str, sujet: str, facet: Optional[str] = None) -> Dict:
    """
    Enregistre une question restée sans réponse.

    Returns:
        {'sujet', 'facette', 'count', 'triggered': bool}
    """
    try:
        from facet_coverage import detect_facet
    except Exception:
        detect_facet = None
    facet = facet or (detect_facet(question) if detect_facet else 'definition')
    with _lock:
        queue = _load()
        entry = queue.setdefault(sujet, {})
        entry[facet] = entry.get(facet, 0) + 1
        _save(queue)
    count = entry[facet]
    total = sum(entry.values())
    triggered = (count >= FACET_TRIGGER or total >= SUBJECT_TRIGGER)
    return {'sujet': sujet, 'facette': facet, 'count': count,
            'total': total, 'triggered': triggered}


def missing_sujets(min_total: int = SUBJECT_TRIGGER) -> List[str]:
    """Sujets dont la file dépasse le seuil (à compléter)."""
    queue = _load()
    return [s for s, facets in queue.items() if sum(facets.values()) >= min_total]


def pop_priority(limit: int = 1) -> List[Dict]:
    """
    Sujets à compléter (les plus demandés d'abord) — les extrait de la
    file et retourne leurs facettes manquantes ciblées.
    """
    with _lock:
        queue = _load()
        ranked = sorted(queue.items(), key=lambda kv: -sum(kv[1].values()))
        picked = []
        for sujet, facets in ranked[:limit]:
            del queue[sujet]
            picked.append({'sujet': sujet, 'facettes': list(facets.keys())})
        _save(queue)
    return picked


def status() -> Dict:
    queue = _load()
    return {'total_sujets': len(queue),
            'attente': {s: sum(f.values()) for s, f in queue.items()}}


def complete_in_background(store, sujet: str,
                          facettes: List[str], language: str = 'fr',
                          spec=None):
    """
    Complétion en arrière-plan (thread daemon) : ingestion massive ciblée
    sur les facettes demandées, couverture recalculée au registre.
    """
    def _run():
        import logging
        log = logging.getLogger(__name__)
        log.info(f"🌱 Complétion démarrée: {sujet} (facettes: {facettes})")
        try:
            sp = spec   # évite l'UnboundLocalError de la closure (assignation)
            if sp is None:
                from specialize_holograms import HologramSpecializer
                sp = HologramSpecializer(store)
            holo_id = f'personal_{sujet}'
            if holo_id not in store._registry:
                # Le sujet n'a pas d'hologramme : le créer (seed + massive)
                # allow_thin : un sujet ABSENT du corpus (leptospirose) a un
                # seed vide — l'ingestion web le remplit juste après.
                res = sp.build([sujet], language=language, massive=True,
                               allow_thin=True)
                if 'error' in res:
                    log.error(f"⚠ Complétion {sujet}: {res['error']}")
                    return
                holo_id = res['holo_id']
            from facet_coverage import (coverage_queries, coverage_score)
            cov = coverage_score(store, holo_id, sujet)
            queries = coverage_queries(sujet, cov.get('manquantes', []))
            # Cibler d'abord les facettes demandées par l'utilisateur
            log.info(f"🌱 Complétion {sujet}: {len(queries)} requêtes "
                     f"(facettes demandées: {facettes})")
            mass = sp.massive_ingest(holo_id, [sujet], language,
                                     variant_queries=queries)
            cov2 = coverage_score(store, holo_id, sujet)
            meta = store._registry.get(holo_id)
            if meta is not None:
                meta.coverage = cov2.get('couverture', 0.0)
                meta.coverage_facets = cov2.get('manquantes', [])
                store._save_registry()
            log.info(f"🌱 Complétion {sujet}: +{mass.get('added', 0)} faits, "
                     f"couverture {cov2.get('couverture', 0):.0%}")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'⚠ Complétion {sujet}: {e}')
    threading.Thread(target=_run, daemon=True).start()
