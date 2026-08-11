"""routers.meta — état du moteur + benchmark en direct (public pour /status)."""

import time

import numpy as np
from fastapi import APIRouter, Depends

from ..core import engine
from ..core.keys import PLANS, require_key

router = APIRouter(prefix='/v1/meta', tags=['meta'])


@router.get('/status')
def status():
    mem = engine.get_memory()
    return {
        'service': 'harmonic-compute',
        'version': '1.0.0',
        'status': 'ok',
        'engine': 'wave_lang.py — machine de Hilbert déterministe',
        'space': 'ℂ⁵¹² (limite de Bekenstein)',
        'normalization': '‖ψ‖ = 1 — l\'information est dans la direction',
        'determinism': '100 % — même entrée, même ψ (FNV-1a + φ-spacing)',
        'primitives': ['encode', 'decode', 'bind', 'unbind', 'superpose',
                       'resonate', 'rotate', 'normalize', 'interfere',
                       'diffract', 'filter', 'phase_shift', 'emerge'],
        'memory': {'facts': mem.n_facts, 'energy': round(mem.energy, 6)},
        'plans': PLANS,
        'honesty': [
            'Émulateur harmonique : mêmes opérations que la cinématique '
            'quantique, déterministes — PAS un ordinateur quantique matériel',
            'E1 (dériver Schrödinger/Q depuis l\'équation mère) : porte ouverte',
            'Les coefficients de l\'équation mère ne sont pas {φ, π, e} (X1)',
        ],
    }


@router.get('/benchmark', dependencies=[Depends(require_key)])
def benchmark():
    t0 = time.time()
    psi = engine.encode('test')
    norm_ok = abs(float(np.linalg.norm(psi)) - 1.0) < 1e-9
    self_ok = abs(float(engine.resonate(psi, psi)) - 1.0) < 1e-9
    a, b = engine.encode('alpha'), engine.encode('beta')
    recovery = float(engine.resonate(a, engine.unbind(engine.bind(a, b), b)))
    rot = float(engine.resonate(psi, engine.rotate(psi, np.pi)))
    mem = engine.get_memory()
    mem.store(engine.encode('test_sujet'), engine.encode('test_relation'),
              engine.encode('test_objet'))
    elapsed = (time.time() - t0) * 1000
    return {
        'elapsed_ms': round(elapsed, 2),
        'engine': 'wave_lang.py — ℂ⁵¹²',
        'results': {
            'normalization_‖encode(x)‖=1': {'value': round(float(np.linalg.norm(psi)), 9), 'pass': norm_ok},
            'resonance_identité_⟨a|a⟩=1': {'value': round(float(engine.resonate(psi, psi)), 9), 'pass': self_ok},
            'bind_unbind_recovery': {'value': round(recovery, 6), 'pass': recovery >= 0.7},
            'rotate(ψ,π)→−1': {'value': round(rot, 6), 'pass': abs(rot + 1.0) < 1e-6},
        },
        'note': 'Démos vérifiées en direct — chaque affirmation est une commande.',
    }
