"""routers.memory — mémoire holographique persistante."""

from fastapi import APIRouter, Body, Depends, HTTPException

from ..core import engine
from ..core.keys import require_key

router = APIRouter(prefix='/v1/memory', tags=['memory'],
                   dependencies=[Depends(require_key)])


@router.post('/store')
def store(body: dict = Body(...)):
    facts = body.get('facts') or []
    if not facts:
        raise HTTPException(status_code=400, detail={
            'error': 'Aucun fait [[sujet, relation, objet]]', 'code': 'EMPTY_FACTS'})
    return engine.memory_store(facts)


@router.post('/query')
def query(body: dict = Body(...)):
    q = (body.get('query') or '').strip()
    if not q:
        raise HTTPException(status_code=400, detail={'error': 'Requête vide',
                                                     'code': 'EMPTY_QUERY'})
    return engine.memory_query(q, top_k=int(body.get('top_k', 5)))


@router.get('/stats')
def stats():
    mem = engine.get_memory()
    return {'facts': mem.n_facts, 'energy': round(mem.energy, 6),
            'mechanism': 'H = Σ ψ_fait — superposition, pas d\'écrasement',
            'forget': 'noyau ABC (α = 1/φ) — t^{−0,618}'}


@router.post('/ask')
def ask(body: dict = Body(...)):
    """LE RAG DÉTERMINISTE (memory-first) : question → résonance → réponse
    avec provenance, ou refus structurel — la machine ne fabrique jamais."""
    from ka_server.services.memory_first import ask as mf_ask
    q = (body.get('query') or '').strip()
    if not q:
        raise HTTPException(status_code=400, detail={'error': 'Requête vide',
                                                     'code': 'EMPTY_QUERY'})
    return mf_ask(q, threshold=body.get('threshold'))


@router.post('/store_with_source')
def store_with_source(body: dict = Body(...)):
    """Stocke des faits avec leur SOURCE (la provenance du RAG déterministe)."""
    from ka_server.services.memory_first import store_fact
    facts = body.get('facts') or []
    stored = 0
    for f in facts:
        if len(f) < 3:
            continue
        store_fact(str(f[0]), str(f[1]), str(f[2]),
                   source=str(f[3]) if len(f) > 3 else '')
        stored += 1
    return {'stored': stored,
            'mechanism': 'apprentissage O(1) — un fait = une onde',
            'honesty': 'la provenance est stockée — chaque réponse pointe son fait'}
