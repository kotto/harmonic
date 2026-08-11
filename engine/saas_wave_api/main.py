"""
main — Harmonic Compute API (service SaaS de calcul harmonique)
================================================================
Démarrage :
    uvicorn saas_wave_api.main:app --host 0.0.0.0 --port 8000

Docs : http://localhost:8000/docs · Playground : http://localhost:8000/
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import __version__
from .routers import auth, memory, meta, wave

# Noyau hybride (arithmétique émergente) : racine engine sur le path
_ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

app = FastAPI(
    title='Harmonic Compute — calcul harmonique (quantum-like)',
    description=(
        'Machine de Hilbert déterministe : les 13 primitives du langage '
        'ondulatoire (ℂ⁵¹², ‖ψ‖ = 1) — superposition, binding, résonance, '
        'interférence, diffraction, émergence. Mêmes opérations que la '
        'cinématique quantique, sans le hasard. '
        'Honnêteté : émulateur harmonique — pas un ordinateur quantique matériel.'
    ),
    version=__version__,
    contact={'name': 'Univers-Holistique (Kotto Alain)'},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(meta.router)
app.include_router(wave.router)
app.include_router(memory.router)
app.include_router(auth.router)

_PLAYGROUND = Path(__file__).resolve().parent / 'static' / 'playground.html'


@app.get('/', include_in_schema=False)
def landing():
    """Playground interactif (page unique)."""
    return FileResponse(_PLAYGROUND)
