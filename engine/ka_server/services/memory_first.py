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
# L'ancrage LEXICAL est la récupération (déterministe — le fait existe) ;
# la résonance est la CONFIDENCE RAPPORTÉE (sa variabilité par entité est
# la frontière publiée F6, « le spectre s'apprend »). Le seuil gate donc
# seulement les anti-résonances FORTES (score < −0,05) — un fait connu
# n'est pas refusé à cause de la variabilité de l'encodeur.
DEFAULT_REFUSAL_THRESHOLD = float(os.environ.get('KA_REFUSAL_THRESHOLD', -0.05))

_lock = threading.Lock()
_memory: HolographicMemory | None = None
_facts: list = []          # [{'sujet','relation','objet','source'}]
_vocabulary: list = []     # les entités connues (sujets + objets)


def _data_dir() -> Path:
    """Répertoire de persistance. ATTENTION : Path('') = Path('.') — tester
    la chaîne AVANT de convertir (sinon, écriture dans le CWD)."""
    raw = os.environ.get('KA_SAAS_WAVE_DIR', '')
    return Path(raw) if raw else _ENGINE_DIR / 'data' / 'saas_wave'


def _persist():
    path = _data_dir() / 'memory_first.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_facts, ensure_ascii=False, indent=1), encoding='utf-8')


def _ensure_memory_unlocked():
    """Initialise + restaure la mémoire — À APPELER avec _lock tenu
    (jamais de re-entrée : le verrou n'est pas réentrant)."""
    global _memory
    if _memory is None:
        _memory = HolographicMemory(dim=DIM)
        _restore()


def _get_memory() -> HolographicMemory:
    with _lock:
        _ensure_memory_unlocked()
        return _memory


def _restore():
    """Restaure les faits persistés — À APPELER avec _lock tenu (jamais de
    re-entrée : le verrou n'est pas réentrant, un appel imbriqué = deadlock)."""
    path = _data_dir() / 'memory_first.json'
    if not path.exists():
        return
    try:
        for f in json.loads(path.read_text(encoding='utf-8')):
            _store_unlocked(f['sujet'], f['relation'], f['objet'], f.get('source', ''))
        _persist()  # une seule écriture finale, pas 91
    except Exception:
        pass


def _store_unlocked(sujet: str, relation: str, objet: str, source: str = ''):
    """Stocke un fait — À APPELER avec _lock tenu (interne, pas de re-entrée)."""
    _memory.store(encode(sujet, dim=DIM), encode(relation, dim=DIM),
                  encode(objet, dim=DIM))
    _facts.append({'sujet': sujet, 'relation': relation, 'objet': objet,
                   'source': source})
    for w in (sujet, objet):
        if w not in _vocabulary:
            _vocabulary.append(w)
    _persist()


def store_fact(sujet: str, relation: str, objet: str, source: str = ''):
    """Stocke un fait avec sa provenance (source)."""
    with _lock:
        _ensure_memory_unlocked()
        _store_unlocked(sujet, relation, objet, source)


def _normalize(text: str) -> str:
    """Minuscules + sans accents — le matcher médical tolère « hémorragie »."""
    import unicodedata
    return unicodedata.normalize('NFD', text.lower()) \
        .encode('ascii', 'ignore').decode('ascii')


def _match_entities(query: str) -> list:
    """Le pont sémantique LEXICAL : les entités du vocabulaire liées à la
    requête — dans les DEUX sens (la requête dans l'entité « paludisme »,
    ou l'entité dans la requête « quel est le traitement du paludisme »).
    Déterministe, exact, zéro sémantique (X3)."""
    q = _normalize(query)
    return [w for w in _vocabulary
            if _normalize(w) in q or q in _normalize(w)]


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


# ═══ LE PONT AGENTIQUE — la mémoire connaît les actions du téléphone ═══════
# KA, assistant personnel : les fonctions agentiques (appeler, SMS, ouvrir,
# compresser…) sont des FAITS — (commande, 'action', 'nom_action') — la
# mémoire les connaît comme le reste ; l'ask() retourne suggested_action
# quand la requête est une commande. Zéro dépendance open-source côté
# serveur (le téléphone exécute via le plugin natif KAActions).

ACTIONS = [
    {'mot': 'appeler', 'action': 'call', 'relation': 'call'},
    {'mot': 'appelle', 'action': 'call', 'relation': 'call'},
    {'mot': 'sms', 'action': 'sms', 'relation': 'sms'},
    {'mot': 'envoie un message', 'action': 'sms', 'relation': 'sms'},
    # ⚡ HCV — la compression phare de KA (serveur hcv_codec : wasm/serveur/fallback)
    {'mot': 'compresse', 'action': 'hcv_compress', 'relation': 'hcv_compress'},
    {'mot': 'compresser', 'action': 'hcv_compress', 'relation': 'hcv_compress'},
    {'mot': 'compression', 'action': 'hcv_compress', 'relation': 'hcv_compress'},
    {'mot': 'optimise', 'action': 'hcv_compress', 'relation': 'hcv_compress'},
    {'mot': 'optimiser', 'action': 'hcv_compress', 'relation': 'hcv_compress'},
    {'mot': 'stockage', 'action': 'hcv_compress', 'relation': 'hcv_compress'},
    {'mot': 'espace disque', 'action': 'diskSpace', 'relation': 'diskSpace'},
    {'mot': 'batterie', 'action': 'battery', 'relation': 'battery'},
    {'mot': 'ouvre', 'action': 'openApp', 'relation': 'openApp'},
    {'mot': 'wifi', 'action': 'wifiInfo', 'relation': 'wifiInfo'},
]

HCV_SOURCE = ('HCV Codec — compression harmonique : photos ~30×, '
              'vidéos ~30×, fichiers ~3× (hcv_codec.py, hybride '
              'wasm/serveur/fallback)')


def detect_action(query: str) -> dict | None:
    """Reconnaît une commande agentique (lexical, déterministe — X3).
    Retourne {action, relation, source} ou None. La compression → HCV,
    la fonction phare de KA."""
    q = _normalize(query)
    for entry in ACTIONS:
        if _normalize(entry['mot']) in q:
            action = entry['action']
            return {'action': action, 'relation': entry['relation'],
                    'source': HCV_SOURCE if action == 'hcv_compress'
                    else 'KA Actions — plugin natif du téléphone'}
    return None


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

    # ⚡ PONT AGENTIQUE : une commande du téléphone (appeler, SMS, HCV…)
    action = detect_action(query)
    if action is not None:
        return {'answer': f"Commande reconnue : {action['action']}.",
                'provenance': [{'sujet': action['relation'], 'relation': 'action',
                                'objet': action['action'],
                                'source': action['source']}],
                'confidence': 1.0, 'refused': False, 'reason': None,
                'suggested_action': action['action']}

    if mem.n_facts == 0:
        return {'answer': None, 'provenance': [], 'confidence': 0.0,
                'refused': True, 'reason': 'mémoire vide',
                'suggested_action': None}

    entities = _match_entities(query)
    if not entities:
        return {'answer': None, 'provenance': [], 'confidence': 0.0,
                'refused': True, 'reason': 'aucune entité connue dans la requête',
                'suggested_action': None}

    # les faits des entités trouvées — score intra-entité (max-probe)
    candidates = []
    for i, f in enumerate(_facts):
        if f['sujet'] in entities or f['objet'] in entities:
            e = f['sujet'] if f['sujet'] in entities else f['objet']
            candidates.append((i, _score_fact(e, i), e))
    if not candidates:
        return {'answer': None, 'provenance': [], 'confidence': 0.0,
                'refused': True, 'reason': 'entités sans fait associé',
                'suggested_action': None}

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
            'confidence': round(best_score, 4), 'refused': False, 'reason': None,
            'suggested_action': None}


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
