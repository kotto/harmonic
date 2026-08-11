"""routers.wave — les 13 primitives du langage ondulatoire en REST."""

import numpy as np
from fastapi import APIRouter, Body, Depends, HTTPException

from ..core import engine
from ..core.keys import require_key

router = APIRouter(prefix='/v1/wave', tags=['wave'], dependencies=[Depends(require_key)])


def _resolve_or_400(item):
    try:
        return engine.resolve(item)
    except Exception as e:
        raise HTTPException(status_code=400, detail={'error': str(e),
                                                     'code': 'BAD_WAVE'})


@router.post('/encode')
def encode(entity: str = Body(..., embed=True)):
    if not entity.strip():
        raise HTTPException(status_code=400, detail={'error': 'Entité vide',
                                                     'code': 'EMPTY_ENTITY'})
    psi = engine.encode(entity, dim=engine.DIM)
    return {'entity': entity, 'wave': engine.wave_to_json(psi),
            'stats': engine.stats(psi)}


@router.post('/decode')
def decode(body: dict = Body(...)):
    try:
        psi = engine.resolve(body.get('wave') or body.get('entity'))
    except Exception as e:
        raise HTTPException(status_code=400, detail={'error': str(e),
                                                     'code': 'BAD_WAVE'})
    vocabulary = body.get('vocabulary') or []
    vocab = {v: engine.encode(v, dim=engine.DIM) for v in vocabulary} if vocabulary else None
    results = engine.decode(psi, vocabulary=vocab, top_k=int(body.get('top_k', 5)))
    return {'decoded': [{'entity': w, 'score': round(s, 6)} for w, s in results]}


@router.post('/bind')
def bind(body: dict = Body(...)):
    a, b = _resolve_or_400(body.get('a')), _resolve_or_400(body.get('b'))
    psi = engine.bind(a, b)
    return {'wave': engine.wave_to_json(psi), 'summary': engine.summary(psi)}


@router.post('/unbind')
def unbind(body: dict = Body(...)):
    c = _resolve_or_400(body.get('c') or body.get('a'))
    b = _resolve_or_400(body.get('b'))
    psi = engine.unbind(c, b)
    return {'wave': engine.wave_to_json(psi), 'summary': engine.summary(psi)}


@router.post('/superpose')
def superpose(body: dict = Body(...)):
    items = body.get('items') or []
    if not items:
        raise HTTPException(status_code=400, detail={'error': 'Aucun item',
                                                     'code': 'EMPTY_ITEMS'})
    psis = [_resolve_or_400(i) for i in items]
    weights = body.get('weights')
    psi = engine.superpose(*psis, weights=weights) if weights else engine.superpose(*psis)
    return {'wave': engine.wave_to_json(psi), 'count': len(psis),
            'summary': engine.summary(psi)}


@router.post('/resonate')
def resonate(body: dict = Body(...)):
    a, b = _resolve_or_400(body.get('a')), _resolve_or_400(body.get('b'))
    s = float(engine.resonate(a, b))
    return {'resonance': round(s, 6),
            'interpretation': ('identique' if abs(s - 1.0) < 1e-9
                               else 'orthogonal' if abs(s) < 1e-9
                               else 'partiel' if s > 0.3 else 'faible')}


@router.post('/rotate')
def rotate(body: dict = Body(...)):
    a = _resolve_or_400(body.get('a'))
    psi = engine.rotate(a, float(body.get('angle', 0.0)))
    return {'wave': engine.wave_to_json(psi), 'summary': engine.summary(psi)}


@router.post('/interfere')
def interfere(body: dict = Body(...)):
    a, b = _resolve_or_400(body.get('a')), _resolve_or_400(body.get('b'))
    psi = engine.interfere(a, b, epsilon=float(body.get('epsilon', 0.15)))
    return {'wave': engine.wave_to_json(psi), 'summary': engine.summary(psi)}


@router.post('/diffract')
def diffract(body: dict = Body(...)):
    a = _resolve_or_400(body.get('a'))
    psi = engine.diffract(a, inverse=bool(body.get('inverse', False)))
    return {'wave': engine.wave_to_json(psi), 'summary': engine.summary(psi)}


@router.post('/filter')
def filter_wave(body: dict = Body(...)):
    a = _resolve_or_400(body.get('a'))
    mode = body.get('mode', 'lowpass')
    cutoff = float(body.get('cutoff', 0.5))
    spec = np.fft.fft(a)
    n = len(spec)
    idx = int(cutoff * n)
    if mode == 'lowpass':
        spec[idx:] = 0
    elif mode == 'highpass':
        spec[:idx] = 0
    else:
        raise HTTPException(status_code=400, detail={
            'error': "mode ∈ {lowpass, highpass}", 'code': 'BAD_FILTER_MODE'})
    psi = engine.normalize(np.fft.ifft(spec))
    return {'wave': engine.wave_to_json(psi), 'mode': mode, 'cutoff': cutoff,
            'summary': engine.summary(psi)}


@router.post('/phase_shift')
def phase_shift(body: dict = Body(...)):
    a = _resolve_or_400(body.get('a'))
    psi = engine.phase_shift(a, float(body.get('shift', 0.0)))
    return {'wave': engine.wave_to_json(psi), 'summary': engine.summary(psi)}


@router.post('/emerge')
def emerge(body: dict = Body(...)):
    items = body.get('items') or []
    if not items:
        raise HTTPException(status_code=400, detail={'error': 'Aucun item',
                                                     'code': 'EMPTY_ITEMS'})
    psis = [_resolve_or_400(i) for i in items]
    psi = engine.emerge(*psis, temperature=float(body.get('temperature', 0.5)))
    return {'wave': engine.wave_to_json(psi), 'summary': engine.summary(psi)}


@router.post('/solve')
def solve(body: dict = Body(...)):
    expression = (body.get('expression') or '').strip()
    if not expression:
        raise HTTPException(status_code=400, detail={'error': 'Expression vide',
                                                     'code': 'EMPTY_EXPRESSION'})
    try:
        from ka_server.services.harmonic_v3 import get_harmonic_v3
        engine_h = get_harmonic_v3()
    except Exception:
        engine_h = None
    if engine_h is None:
        raise HTTPException(status_code=503, detail={
            'error': 'Moteur d\'arithmétique indisponible (noyau hybride)',
            'code': 'ENGINE_UNAVAILABLE'})
    return {'expression': expression, 'result': engine_h.solve(expression),
            'method': 'émergence ondulatoire (Ψ_a·Ψ_b = Ψ_{a+b})'}
