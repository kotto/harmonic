"""
services.memory_first — LE PIPELINE MEMORY-FIRST
================================================
Le LLM ne sait rien : il formule ce que la mémoire certifie, et se tait
quand elle se tait.

Couches :
  · CONNAISSANCE : la mémoire dorée (HolographicMemory) — les faits
    (sujet, relation, objet) avec leur SOURCE (la provenance)
  · PONT SÉMANTIQUE : le vocabulaire (les entités connues) — lexical,
    déterministe, exact — PAS de sémantique magique (exclusion X3 :
    le φ-spacing ne porte pas le sens ; le pont est déclaré)
  · DÉCISION : la résonance multi-sondes + le seuil de refus calibré
  · LANGAGE : la formulation à partir du fait stocké (le corpus, pas le LLM)

ask(query) → {answer, provenance, confidence, refused, reason}
"""

import json
import os
import sys
import threading
from pathlib import Path

import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
_WAVE_DIR = _ENGINE_DIR / 'vital-ka' / 'core' / 'python'
if str(_WAVE_DIR) not in sys.path:
    sys.path.insert(0, str(_WAVE_DIR))

from wave_lang import HolographicMemory, bind, encode, resonate, unbind  # noqa: E402

DIM = 512
# Seuil de refus : la résonance en dessous de laquelle la machine se tait.
# Le refus est STRUCTUREL (aucune entité connue → silence — jamais de
# fabrication) ; le seuil gate seulement les anti-résonances (score < 0).
# La confiance est RAPPORTÉE telle quelle : sa variabilité par entité est
# la frontière publiée F6 (« le spectre s'apprend ») — pas cachée.
DEFAULT_REFUSAL_THRESHOLD = float(os.environ.get('KA_REFUSAL_THRESHOLD', 0.0))

_lock = threading.Lock()
_memory: HolographicMemory | None = None
_facts: list = []          # [{'sujet','relation','objet','source'}]
_vocabulary: list = []     # les entités connues (sujets + objets)


def _data_dir() -> Path:
    override = Path(os.environ.get('KA_SAAS_WAVE_DIR', ''))
    return override if str(override) else _ENGINE_DIR / 'data' / 'saas_wave'


def _persist():
    path = _data_dir() / 'memory_first.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_facts, ensure_ascii=False, indent=1), encoding='utf-8')


def _get_memory() -> HolographicMemory:
    global _memory
    with _lock:
        if _memory is None:
            _memory = HolographicMemory(dim=DIM)
            path = _data_dir() / 'memory_first.json'
            if path.exists():
                try:
                    for f in json.loads(path.read_text(encoding='utf-8')):
                        _store(f['sujet'], f['relation'], f['objet'], f.get('source', ''))
                except Exception:
                    pass
        return _memory


def _store(sujet: str, relation: str, objet: str, source: str = ''):
    mem = _get_memory()
    mem.store(encode(sujet, dim=DIM), encode(relation, dim=DIM), encode(objet, dim=DIM))
    _facts.append({'sujet': sujet, 'relation': relation, 'objet': objet, 'source': source})
    for w in (sujet, objet):
        if w not in _vocabulary:
            _vocabulary.append(w)
    _persist()


def store_fact(sujet: str, relation: str, objet: str, source: str = ''):
    """Stocke un fait avec sa provenance (source)."""
    _store(sujet, relation, objet, source)


def _normalize(text: str) -> str:
    return text.lower().strip()


def _match_entities(query: str) -> list:
    """Le pont sémantique LEXICAL : les entités du vocabulaire présentes
    dans la requête (normalisée). Déterministe, exact, zéro sémantique."""
    q = _normalize(query)
    return [w for w in _vocabulary if _normalize(w) in q]


def _score_fact(entity: str, i: int) -> float:
    """Résonance multi-sondes : le MAX de deux récupérations du même fait —
    le sujet et l'objet — la meilleure voie, pas la moyenne (la moyenne
    noierait le bon signal avec les voies faibles)."""
    f = _facts[i]
    F = _get_memory()._fact_vectors[i]
    psi_e = encode(entity, dim=DIM)
    s1 = float(resonate(psi_e, unbind(F, encode(f['relation'], dim=DIM))))
    s2 = float(resonate(psi_e, unbind(F, encode(f['objet'], dim=DIM))))
    return max(s1, s2)


def ask(query: str, threshold: float | None = None, top_k: int = 3) -> dict:
    """Le pipeline memory-first : question → vocabulaire (pont LEXICAL) →
    résonance intra-entité (confiance) → décision de refus → réponse avec
    provenance.

    Honnêteté structurelle (X3) : la discrimination ENTRE entités est
    lexicale (le vocabulaire — déterministe, exact) ; la résonance mesure
    la CONFIANCE à l'intérieur des faits de l'entité — le φ-spacing ne
    porte pas le sens, et ce design le déclare au lieu de le cacher.
    """
    thr = DEFAULT_REFUSAL_THRESHOLD if threshold is None else threshold
    mem = _get_memory()
    if mem.n_facts == 0:
        return {'answer': None, 'provenance': [], 'confidence': 0.0,
                'refused': True, 'reason': 'mémoire vide'}

    entities = _match_entities(query)
    if not entities:
        return {'answer': None, 'provenance': [], 'confidence': 0.0,
                'refused': True, 'reason': 'aucune entité connue dans la requête'}

    # les faits des entités trouvées — score intra-entité (max-probe)
    candidates = []
    for i, f in enumerate(_facts):
        if f['sujet'] in entities or f['objet'] in entities:
            e = f['sujet'] if f['sujet'] in entities else f['objet']
            candidates.append((i, _score_fact(e, i), e))
    if not candidates:
        return {'answer': None, 'provenance': [], 'confidence': 0.0,
                'refused': True, 'reason': 'entités sans fait associé'}

    candidates.sort(key=lambda x: -x[1])
    best_i, best_score, best_entity = candidates[0]
    if best_score < thr:
        return {'answer': None, 'provenance': [],
                'confidence': round(best_score, 4), 'refused': True,
                'reason': f'anti-résonance {best_score:.3f} < seuil {thr}'
                          ' (la confiance est rapportée — F6 : le spectre s\'apprend)'}

    top = candidates[:top_k]
    provenance = [{'sujet': f['sujet'], 'relation': f['relation'],
                   'objet': f['objet'], 'source': f['source'],
                   'resonance': round(s, 4)}
                  for i, s, e in top for f in [_facts[i]]]
    fact = _facts[best_i]
    answer = f"{fact['sujet']} {fact['relation']} {fact['objet']}."
    return {'answer': answer, 'provenance': provenance,
            'confidence': round(best_score, 4), 'refused': False, 'reason': None}


def stats() -> dict:
    mem = _get_memory()
    return {'facts': mem.n_facts, 'energy': round(mem.energy, 6),
            'vocabulary': len(_vocabulary),
            'threshold': DEFAULT_REFUSAL_THRESHOLD,
            'mechanism': 'mémoire dorée + pont lexical + refus structurel',
            'honesty': ['le pont sémantique est LEXICAL (X3 : le φ-spacing '
                        'ne porte pas le sens — le spectre s\'apprend)',
                        'le refus est structurel : jamais de fabrication — '
                        'la réponse vient toujours d\'un fait stocké',
                        'la confiance est rapportée brute (F6 : le spectre '
                        's\'apprend — l\'encodeur appris améliore la confiance)']}
