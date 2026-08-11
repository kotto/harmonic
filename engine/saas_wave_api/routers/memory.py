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
