#!/usr/bin/env python3
"""
context_wave.py — Attention contextuelle ondulatoire (ψ_ctx)
================================================================

Correspondance (D) : un LLM conditionne chaque token sur TOUT le contexte ;
l'équivalent harmonique est une SUPERPOSITION ψ_ctx des tours précédents,
avec décroissance ABC (les tours récents pèsent plus — PHI_INV^(i·0.3)).

Trois usages :
  1. SUIVI ANAPHORIQUE — « Et le type 2 ? » après une réponse sur le
     diabète : le message seul n'a pas de mots significatifs ; le SUJET
     vient du contexte (resolve_subject) et enrichit la requête du rappel
     M4 (les faits du holo diabete résonnent).
  2. SUJET DE PROSE — le sujet de la réponse (« Pour comprendre le
     diabète... ») est résolu depuis le contexte, pas depuis la question
     anaphorique.
  3. COHÉRENCE DE PHASE — un seed dérivé du contexte (hash) module le
     choix des connecteurs : la même question après un contexte différent
     produit une surface différente, en cohérence avec l'historique.

Contrat inchangé : le contexte ne fournit JAMAIS de contenu non vérifié —
il fournit des mots de requête (le gate M4 vérifie toujours) et des seeds
de phase (la forme).
"""

import hashlib
import re
from typing import Dict, List, Optional, Tuple

PHI = 1.618033988749895
PHI_INV = PHI - 1.0

# Marqueurs de question de suivi (anaphores) — « Et le type 2 ? »
_FOLLOWUP_MARKERS = [
    'et le', 'et la', 'et les', 'et l', 'et un', 'et une', 'et si', 'et comment',
    'et pourquoi', 'et qu', 'et quel', 'et quelle', 'et quels', 'et quelles',
    'et donc', 'et alors', 'et apres', 'et ensuite', 'et lui', 'et elle',
    'et eux', 'mais', 'sinon', 'justement', 'd accord', 'd accord mais',
    'qu en est il', 'qu en est-il', 'et pour', 'et dans', 'et en', 'et sur',
    'pareil', 'lui aussi', 'elle aussi', 'et oui', 'et non', 'ok et',
    'oui et', 'et la difference', 'et la différence', 'et le role',
    'et le role de', 'et son', 'et sa', 'et ses', 'et leur',
]

# Préfixes de question (pour extraire le sujet du message)
_QUESTION_PREFIXES_FR = [
    'qu est ce que', 'qu est-ce que', 'qu est ce qu', 'qu est-ce qu',
    'qu est ce qui', 'qu est ce', 'qu est', 'qui a invente', 'qui a cree',
    'qui a decouvert', 'qui a', 'qui est', 'explique moi', 'explique',
    'expliquez', 'pourquoi', 'comment', 'decris', 'definis', 'donne moi',
    'parle moi de', 'parle moi', 'dis moi', 'quelle est', 'que signifie',
    'que veut dire', 'que sait on de', 'que sais tu sur', 'que sais tu de',
    'c est quoi', 'et le', 'et la', 'et les', 'et l', 'et un',
    'et une', 'et ses', 'et son', 'et sa', 'et leur', 'et qu',
    'et quel', 'et quelle', 'et comment', 'et pourquoi', 'et si',
    'mais', 'sinon', 'justement', 'qu en est il', 'qu en est-il',
]

# Mots sans valeur pour le sujet (« est », « que »...)
_NON_SUBJECT = {
    'est', 'sont', 'que', 'qui', 'quoi', 'dont', 'avec', 'dans', 'pour',
    'sur', 'sous', 'chez', 'vers', 'entre', 'mais', 'donc', 'or', 'ni',
    'car', 'et', 'ou', 'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de',
    'se', 'ce', 'cette', 'ces', 'il', 'elle', 'ils', 'elles', 'on', 'ca',
    'comment', 'pourquoi', 'quand', 'combien', 'quel', 'quelle', 'quels',
    'quelles', 'peut', 'peuvent', 'doit', 'doivent', 'a', 'au', 'aux', 'en',
    'y', 'son', 'sa', 'ses', 'leur', 'leurs', 'cela', 'ceci', 'tout',
    'tous', 'toute', 'toutes', 'aussi', 'bien', 'plus', 'moins', 'tres',
    'pas', 'ne', 'si', 'sinon', 'dans', 'apres', 'avant', 'pendant', 'parce',
}


def _words(text: str) -> List[str]:
    return re.findall(r"[a-zàâäéèêëîïôöùûüç]{3,}", text.lower())


def is_followup(message: str, history: Optional[List[Dict]] = None) -> bool:
    """
    Vrai si le message est une question de SUITE (anaphore) : marqueur de
    suivi (« et le type 2 ? ») OU message SANS AUCUN mot significatif
    alors que l'historique existe (« sinon ? »). Une question normale
    (« Qu est-ce que la lumiere ? » — 1 mot significatif) n'est PAS un
    suivi.
    """
    m = message.strip().lower()
    if not m:
        return False
    meaningful = [w for w in _words(m) if w not in _NON_SUBJECT]
    for marker in _FOLLOWUP_MARKERS:
        if m.startswith(marker):
            return True
    if history and not meaningful:
        return True
    return False


def _clean_subject(question: str) -> str:
    """« Qu est-ce que le diabete ? » → « le diabete »."""
    q = question.strip()
    low = q.lower()
    for pfx in sorted(_QUESTION_PREFIXES_FR, key=len, reverse=True):
        if low.startswith(pfx):
            q = q[len(pfx):].strip()
            break
    q = q.strip(' ?.!:;,')
    return q[:60]


# Mots non-autonomes : « et le TYPE 2 ? » réfère au type 2 DU contexte —
# le sujet se compose : sujet_ctx + message (« diabete » + « type 2 » →
# « diabete type 2 »)
_NON_AUTONOMOUS = {
    'type', 'forme', 'role', 'cas', 'partie', 'difference', 'différence',
    'exemple', 'mecanisme', 'moyen', 'moyens', 'stade', 'etape', 'phase',
    'version', 'modele', 'couleur', 'taille', 'avantage', 'inconvenient',
    'inconvénient', 'avantages', 'inconvenients', 'inconvénients', 'effet',
    'effets', 'cause', 'causes', 'consequence', 'conséquences', 'lien',
    'liens', 'rapport', 'rapports', 'detail', 'details', 'principe',
    'principes', 'objectif', 'objectifs', 'fonction', 'fonctions',
}


def resolve_subject(message: str,
                    history: Optional[List[Dict]] = None) -> Optional[str]:
    """
    Le sujet de la réponse : celui du message s'il est informatif ; sinon
    (anaphore) celui du dernier tour UTILISATEUR. Les mots non-autonomes
    (« type 2 ») se composent avec le sujet du contexte (« diabete type
    2 »). None si rien ne permet de le déterminer.
    """
    subj = _clean_subject(message)
    meaningful = [w for w in _words(subj) if w not in _NON_SUBJECT]
    if meaningful and not is_followup(message, history):
        return subj or None

    # Sujet du contexte : dernier tour utilisateur (les réponses assistant
    # sont longues — leur sujet est leur début, moins fiable)
    ctx_subj = None
    if history:
        for turn in reversed(history):
            if turn.get('role') != 'user':
                continue
            content = str(turn.get('content', '') or '')
            s = _clean_subject(content)
            if [w for w in _words(s) if w not in _NON_SUBJECT]:
                ctx_subj = s
                break

    if not meaningful:
        return ctx_subj or None
    # Mots non-autonomes → composer avec le contexte
    if meaningful and ctx_subj and all(w in _NON_AUTONOMOUS for w in meaningful):
        return f'{ctx_subj} {subj}'.strip() or None
    return subj or None


def encode_history(history: Optional[List[Dict]] = None) -> str:
    """
    Seed de phase contextuel (hash déterministe de l'historique) — les
    connecteurs et la surface varient en cohérence avec le contexte.
    (La vraie superposition ψ est une extension : les ψ des tours sont
    sommés avec décroissance ABC ; le seed en est la projection scalaire
    déterministe, suffisante pour la forme.)
    """
    if not history:
        return ''
    h = hashlib.sha256(repr(history).encode()).digest()
    return h[:8].hex()


def ctx_psi(history: Optional[List[Dict]] = None) -> 'np.ndarray':
    """
    Superposition ondulatoire du contexte : ψ_ctx = Σ ψ(tour)·φ^(-i·0.3).
    Les tours récents pèsent plus (décroissance ABC). Utilisé pour
    résonner avec les faits (requête enrichie).
    """
    if not history:
        return None
    try:
        import numpy as np
        from holographic_encoder import HolographicEncoder
        enc = HolographicEncoder()
        psi = np.zeros(enc.dim, dtype=np.complex128)
        n = len(history)
        for i, turn in enumerate(history):
            content = str(turn.get('content', '') or '')
            if not content:
                continue
            w = PHI_INV ** ((n - 1 - i) * 0.3)   # récent → poids fort
            psi += w * enc.encode_query(content)
        norm = np.sqrt(np.sum(np.abs(psi) ** 2))
        if norm > 1e-12:
            psi /= norm
        return psi
    except Exception:
        return None


if __name__ == '__main__':
    history = [
        {'role': 'user', 'content': 'Qu est-ce que le diabete ?'},
        {'role': 'assistant', 'content': 'Le diabete est une maladie chronique caracterisee par un exces de glucose.'},
    ]
    for q in ['Et le type 2 ?', 'Et l insuline ?', 'Qu est-ce que la lumiere ?', 'sinon ?']:
        print(f'{q!r:30s} followup={is_followup(q, history)} sujet={resolve_subject(q, history)}')
    print('seed contexte:', encode_history(history))
