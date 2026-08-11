"""
core.engine — le moteur : wave_lang.py (machine de Hilbert déterministe)
=======================================================================
Sérialisation ψ ↔ JSON + mémoire holographique persistante (singleton).
"""

import json
import sys
import threading
from pathlib import Path

import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
_WAVE_DIR = _ENGINE_DIR / 'vital-ka' / 'core' / 'python'
if str(_WAVE_DIR) not in sys.path:
    sys.path.insert(0, str(_WAVE_DIR))

from wave_lang import (  # noqa: E402
    HolographicMemory, bind, decode, diffract, emerge, encode, filter_wave,
    interfere, normalize, phase_shift, resonate, rotate, stats, superpose,
    unbind,
)

DIM = 512  # ℂ⁵¹² — limite de Bekenstein

_mem_lock = threading.Lock()
_memory: HolographicMemory | None = None
_fact_log: list = []


def data_dir() -> Path:
    """Répertoire de persistance (surchargeable par KA_SAAS_WAVE_DIR — tests)."""
    override = Path(__import__('os').environ.get('KA_SAAS_WAVE_DIR', ''))
    return override if str(override) else _ENGINE_DIR / 'data' / 'saas_wave'


# ── Sérialisation ────────────────────────────────────────────────────────────

def wave_to_json(psi) -> dict:
    psi = np.asarray(psi, dtype=np.complex128)
    return {
        'dim': int(psi.shape[0]),
        'norm': float(np.linalg.norm(psi)),
        'energy': float(np.sum(np.abs(psi) ** 2)),
        'vec': [[float(v.real), float(v.imag)] for v in psi],
    }


def wave_from_json(data: dict) -> np.ndarray:
    vec = data['vec']
    return np.array([complex(a, b) for a, b in vec], dtype=np.complex128)


def resolve(item):
    """str → encode ; dict {"vec": ...} → onde sérialisée."""
    if isinstance(item, str):
        return encode(item, dim=DIM)
    if isinstance(item, dict) and 'vec' in item:
        return wave_from_json(item)
    raise ValueError("entrée invalide — attendu un texte (encodé) ou un ψ sérialisé")


def summary(psi) -> dict:
    psi = np.asarray(psi, dtype=np.complex128)
    return {'dim': int(psi.shape[0]), 'norm': float(np.linalg.norm(psi)),
            'energy': float(np.sum(np.abs(psi) ** 2))}


# ── Mémoire holographique persistante ────────────────────────────────────────

def get_memory() -> HolographicMemory:
    global _memory, _fact_log
    with _mem_lock:
        if _memory is None:
            _memory = HolographicMemory(dim=DIM)
            path = data_dir() / 'memory.json'
            if path.exists():
                try:
                    for f in json.loads(path.read_text(encoding='utf-8')):
                        if len(f) == 3:
                            _memory.store(encode(f[0], dim=DIM),
                                          encode(f[1], dim=DIM),
                                          encode(f[2], dim=DIM))
                            _fact_log.append(list(f))
                except Exception:
                    pass
        return _memory


def memory_store(facts: list) -> dict:
    mem = get_memory()
    stored = 0
    for f in facts:
        if len(f) < 3:
            continue
        try:
            mem.store(encode(f[0], dim=DIM), encode(f[1], dim=DIM),
                      encode(f[2], dim=DIM))
            _fact_log.append([str(f[0]), str(f[1]), str(f[2])])
            stored += 1
        except Exception:
            continue
    path = data_dir() / 'memory.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_fact_log, ensure_ascii=False, indent=1),
                    encoding='utf-8')
    return {'stored': stored, 'total_facts': mem.n_facts,
            'energy': round(mem.energy, 6)}


def memory_query(query: str, top_k: int = 5) -> dict:
    mem = get_memory()
    psi_q = encode(query, dim=DIM)
    scores = mem.query_scores(psi_q)
    return {
        'query': query,
        'results': [{'fact_index': i, 'resonance': round(s, 6)}
                    for i, s in scores[:top_k]],
        'total_facts': mem.n_facts,
    }
