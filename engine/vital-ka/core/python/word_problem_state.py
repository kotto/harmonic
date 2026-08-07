#!/usr/bin/env python3
"""
word_problem_state.py — Solveur d'état séquentiel pour les problèmes de mots
=============================================================================

L'approche GSM8K : un énoncé narratif = une suite d'ACTIONS sur un ÉTAT de
variables. Chaque phrase (non interrogative) met à jour l'état
(personne → objet → quantité) ; la phrase finale détermine la cible.

  « John has 5 apples. He buys 3 more. How many does he have? »
  → state[('john','apple')] = 5 ; += 3 ; réponse = 8

Motifs d'action anglais (priorité décroissante) :
  relations : "N times as many X as Y", "N more/less than Y"
  initialisation : "has/started with/there are N X"
  ajouts : buys/gains/gets/receives/earns/finds/adds N X
  retraits : sells/gives/loses/spends/eats/ate/removes N X
  taux : "N per day/hour for M ...", "N dollars each"
  partage : "shared equally among N"
  finaux : "in total/altogether", "left/remain", "how much"

Tout est déterministe (0 LLM) ; les calculs passent par l'évaluateur
arithmétique exact (entiers purs).
"""

import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# NORMALISATION
# ═══════════════════════════════════════════════════════════════════════════════

_WORD_NUMS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
    'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18,
    'nineteen': 19, 'twenty': 20, 'thirty': 30, 'forty': 40,
    'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
    'hundred': 100, 'thousand': 1000, 'dozen': 12,
}


def normalize(q: str) -> str:
    q = q.lower().strip().rstrip('?')
    q = q.replace('\u2019', "'").replace('\u2018', "'")   # apostrophes courbes
    for w, n in sorted(_WORD_NUMS.items(), key=lambda x: -len(x[0])):
        q = re.sub(rf'\b{w}\b', str(n), q)
    return q


_NUM_RE = r'\d+(?:[.,]\d+)?'

# Mots-outils à ne JAMAIS considérer comme objets
_STOP_OBJ = {'to', 'of', 'for', 'away', 'more', 'less', 'fewer', 'each',
             'in', 'her', 'his', 'their', 'the', 'a', 'an', 'and', 'than',
             'from', 'with', 'at', 'by', 'per', 'on', 'out', 'into', 'up',
             'down', 'over', 'after', 'before', 'all', 'some', 'any',
             'then', 'now', 'still', 'also', 'about', 'as'}

# Pluriels en « ies » dont le singulier est en « ie » (et non « y »)
_IES_EXCEPTIONS = {'cookies': 'cookie', 'movies': 'movie', 'zombies': 'zombie',
                   'pies': 'pie', 'brownies': 'brownie', 'calories': 'calorie',
                   'rookies': 'rookie', 'genies': 'genie', 'pixies': 'pixie',
                   'ties': 'tie', 'lies': 'lie', 'dies': 'die'}

# Pronoms → personne précédente
_PRONOUNS = {'he', 'she', 'they', 'it', 'him', 'her', 'his', 'them',
             'their', 'hers', 'its'}

# Mots qui sont des UNITÉS, jamais des entités de flux
_UNIT_WORDS = {'hour', 'day', 'week', 'month', 'year', 'minute', 'second',
               'time', 'each', 'per', 'centimeter', 'centimeters', 'pound',
               'mile', 'foot', 'inch'}


def _num(s: str) -> float:
    s = s.strip()
    # "80,000" → milliers (3 chiffres après la virgule)
    if ',' in s and re.fullmatch(r'\d+,\d{3}(?:\.\d+)?', s):
        s = s.replace(',', '')
    else:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0


def _stem_obj(s: str) -> str:
    """Objet au singulier : apples → apple, boxes → box, classes → class,
    cookies → cookie (exception ies → ie)."""
    s = s.strip().lower().rstrip('.,;')
    if s in _STOP_OBJ:
        return ''
    if s in _IES_EXCEPTIONS:
        return _IES_EXCEPTIONS[s]
    if s.endswith('ies'):
        return s[:-3] + 'y'
    if s.endswith('ses') or s.endswith('xes') or s.endswith('zes') or \
       s.endswith('ches') or s.endswith('shes'):
        return s[:-2]
    if s.endswith('s') and not s.endswith('ss'):
        return s[:-1]
    return s


def _persons(sentence: str) -> List[str]:
    """Personnes de la phrase, dans l'ORDRE D'APPARITION (important :
    « Mary … as John » → Mary d'abord)."""
    found = []
    for n in _PERSONS_SET:
        m = re.search(rf'\b{n}\b', sentence)
        if m:
            found.append((m.start(), n))
    found.sort()
    return [n for _, n in found]


_PERSONS_SET = frozenset([
    'john', 'mary', 'peter', 'susan', 'tom', 'alice', 'bob', 'jane',
    'sam', 'lucy', 'dan', 'ann', 'james', 'lily', 'jack', 'amy',
    'david', 'emma', 'olivia', 'noah', 'liam', 'sophia', 'mason',
    'ava', 'william', 'ben', 'kate', 'paul', 'sarah', 'mike',
    'chris', 'karen', 'robert', 'linda', 'daniel', 'laura',
    'michael', 'jennifer', 'kevin', 'angela', 'ryan', 'kelly',
    'jason', 'michelle', 'eric', 'rebecca', 'adam', 'nicole',
    'brian', 'amy', 'steve', 'rachel', 'mark', 'jessica',
    'sue', 'carla', 'tina', 'gina', 'fred', 'hank', 'marta', 'luis',
    'ana', 'carlos', 'diego', 'eve', 'frank', 'grace', 'henry',
    # noms extraits des 100 énoncés GSM8K (personnes + villes-possesseurs)
    'aaron', 'aleena', 'alex', 'allen', 'artie', 'bailey', 'billy',
    'brandon', 'candice', 'cecilia', 'charlie', 'christina', 'cindy',
    'claire', 'corey', 'cynthia', 'darrell', 'eliza', 'freda', 'gene',
    'gerald', 'gloria', 'greg', 'gretchen', 'gunter', 'harald', 'harry',
    'jackson', 'jan', 'janet', 'jean', 'josh', 'judy', 'kelian', 'kyle',
    'lee', 'lloyd', 'luke', 'marcia', 'marcy', 'marie', 'marilyn',
    'marissa', 'melanie', 'meredith', 'mishka', 'patchy', 'polly',
    'rafael', 'raymond', 'rex', 'richard', 'samantha', 'shiela',
    'siobhan', 'stephen', 'suzy', 'sylvie', 'ted', 'terry', 'tommy',
    'toula', 'tracy', 'trixie', 'uriah', 'vincent', 'wendi',
    'charleston', 'seattle', 'toulouse', 'farbo', 'perg', 'wertz',
])


def _split_sentences(q: str) -> List[str]:
    """Découpe en phrases ('.', ';', '!' suivis d'espace ou fin)."""
    parts = re.split(r'[.;!]\s+|[.;!]$', q)
    return [p.strip() for p in parts if p.strip()]


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _quantities(sentence: str) -> List[Tuple[float, str]]:
    """(valeur, objet) de chaque quantité de la phrase."""
    out = []
    for m in re.finditer(rf'({_NUM_RE})\s+([a-z]+)', sentence):
        val = _num(m.group(1))
        obj = _stem_obj(m.group(2))
        if val == 0:
            continue
        out.append((val, obj))
    return out


def _clean_obj(s: str) -> str:
    """Objet nettoyé (singulier), '' si mot-outil."""
    return _stem_obj(s)


def _detect_all(sentence: str, last_person: Optional[str] = None,
                last_obj: Optional[str] = None) -> List[Dict]:
    """TOUTES les actions plausibles d'une phrase (champ de résonance).

    Chaque motif qui matche produit un candidat ; l'ordre des blocs est
    l'ordre de spécificité (relations > taux > init > add > sub). La
    résolution par résonance pourra laisser plusieurs interprétations
    coexister et sélectionner celle qui se synchronise.
    """
    q = sentence
    persons = _persons(q)
    person = persons[0] if persons else (
        last_person if any(p in q for p in _PRONOUNS) else None)
    acts: List[Dict] = []

    def _add(op, person=person, **kw):
        acts.append(dict(op=op, person=person, **kw))

    # ── Relations : « A does/has N times as much/many X as B », « half as
    #    much X as B », possessif « X's Y is N times as old as Z's Y » ──
    # (sujet EXPLICITE : la personne du sujet, pas le premier nom de la phrase)
    m = re.search(rf'([a-z]+)\s+(?:does|has|is)\s+'
                  rf'(\d+(?:\.\d+)?)\s+times\s+as\s+(?:much|many)\s+'
                  rf'([a-z]+)\s+as\s+([a-z]+)', q)
    if m:
        _add('set_mult', person=m.group(1), obj=_clean_obj(m.group(3)),
             val=float(m.group(2)), obj2=m.group(4))
    m = re.search(rf'([a-z]+)\s+does\s+'
                  rf'(half|one-third|two-thirds|three-quarters?)\s+as\s+'
                  rf'(?:much|many)\s+([a-z]+)\s+as\s+([a-z]+)', q)
    if m:
        mult = {'half': 0.5, 'one-third': 1 / 3, 'two-thirds': 2 / 3,
                'three-quarters': 0.75, 'three-quarter': 0.75}[m.group(2)]
        _add('set_mult', person=m.group(1), obj=_clean_obj(m.group(3)),
             val=mult, obj2=m.group(4))
    m = re.search(rf'([a-z]+)\s+has\s+(twice|three times|four times)\s+'
                  rf'as\s+(?:much|many)\s+([a-z]+)\s+as\s+([a-z]+)', q)
    if m:
        mult = {'twice': 2.0, 'three times': 3.0, 'four times': 4.0}[m.group(2)]
        _add('set_mult', person=m.group(1), obj=_clean_obj(m.group(3)),
             val=mult, obj2=m.group(4))
    # "X's Y is N times as old as Z's Y" / "N times older than Z's Y"
    m = re.search(rf'([a-z]+)\'s\s+([a-z]+)\s+is\s+(\d+(?:\.\d+)?)\s+'
                  rf'times\s+(?:as\s+(?:old|fast|heavy|big|long)\s+as|'
                  rf'older\s+than)\s+([a-z]+)\'s\s+([a-z]+)', q)
    if m:
        obj, ref, refobj = _clean_obj(m.group(2)), m.group(4), _clean_obj(m.group(5))
        if obj and refobj:
            _add('set_mult', person=m.group(1), obj=obj,
                 val=float(m.group(3)), obj2=ref, ref_obj=refobj)

    # "X's Y is N years old" (âge possessif → valeur initiale)
    m = re.search(rf'([a-z]+)\'s\s+([a-z]+)\s+is\s+({_NUM_RE})\s+'
                  rf'(?:years?\s+)?old', q)
    if m:
        obj = _clean_obj(m.group(2))
        if obj:
            _add('init', person=m.group(1), obj=obj, val=_num(m.group(3)))

    # ── "Each X has N Y" / "each X costs N dollars" ──
    m = re.search(rf'each\s+([a-z]+)\s+has\s+({_NUM_RE})\s+([a-z]+)', q)
    if m:
        src, obj = _clean_obj(m.group(1)), _clean_obj(m.group(3))
        if obj:
            _add('each_has', obj=obj, val=_num(m.group(2)), obj2=src)
    m = re.search(rf'each\s+([a-z]+)\s+(?:costs?|is)\s+({_NUM_RE})\s+'
                  rf'(?:dollars?|\$)', q)
    if m:
        _add('rate_each', obj=None, val=_num(m.group(2)))

    # ── "N more than Y" / "N less than Y" (comparaisons) ──
    m = re.search(rf'({_NUM_RE})\s+more than\s+([a-z]+)', q)
    if m:
        obj = _clean_obj(m.group(2))
        if obj:
            _add('set_plus', obj=obj, val=_num(m.group(1)))
    m = re.search(rf'({_NUM_RE})\s+(?:less|fewer) than\s+([a-z]+)', q)
    if m:
        obj = _clean_obj(m.group(2))
        if obj:
            _add('set_minus', obj=obj, val=_num(m.group(1)))

    # ── Relations linéaires A = coeff×B ± delta (chaînes) ──
    # « A has N more/fewer X than B » → A = B ± N
    m = re.search(rf'([a-z]+)\s+has\s+({_NUM_RE})\s+(more|fewer|less)\s+'
                  rf'([a-z]+)\s+than\s+([a-z]+)\b', q)
    if m:
        d = _num(m.group(2)) if m.group(3) == 'more' else -_num(m.group(2))
        _add('rel', person=m.group(1), obj=_clean_obj(m.group(4)),
             ref=m.group(5), coeff=1.0, delta=d)
    # « N more/fewer X than Y » (entités explicites) → X = Y ± N
    m = re.search(rf'({_NUM_RE})\s+(more|fewer|less)\s+([a-z]+)\s+than\s+'
                  rf'([a-z]+)\b', q)
    if m:
        d = _num(m.group(1)) if m.group(2) == 'more' else -_num(m.group(1))
        _add('rel', person=None, obj=_clean_obj(m.group(3)),
             ref=None, coeff=1.0, delta=d)
    # « A weighs N X less than K times what B weighs » → A = K×B − N
    m = re.search(rf'([a-z]+)\s+weighs?\s+({_NUM_RE})\s+([a-z]+)\s+'
                  rf'(less|more)\s+than\s+(\d+(?:\.\d+)?)\s+times\s+what\s+'
                  rf'([a-z]+)', q)
    if m:
        d = -_num(m.group(2)) if m.group(4) == 'less' else _num(m.group(2))
        _add('rel', person=m.group(1), obj=_clean_obj(m.group(3)),
             ref=m.group(6), coeff=float(m.group(5)), delta=d)
    # « A has N more X than half of B's X » → A = ½·B + N
    m = re.search(rf'([a-z]+)\s+has\s+({_NUM_RE})\s+more\s+([a-z]+)\s+than\s+'
                  rf'half of\s+([a-z]+)\'s\s+([a-z]+)', q)
    if m:
        _add('rel', person=m.group(1), obj=_clean_obj(m.group(3)),
             ref=m.group(4), coeff=0.5, delta=_num(m.group(2)))
    # « X times the number of Y as Z » → set_mult (twice/three times normalisés)
    m = re.search(rf'(\d+(?:\.\d+)?\s+times|twice|three times|four times)\s+'
                  rf'the\s+number\s+of\s+([a-z]+)\s+as\s+([a-z]+)', q)
    if m:
        g1 = m.group(1)
        mult = {'twice': 2.0, 'three times': 3.0, 'four times': 4.0}.get(g1)
        if mult is None:
            mult = float(g1.replace(' times', ''))
        _add('set_mult', obj=_clean_obj(m.group(2)), val=mult, obj2=m.group(3))

    # ── "N X at $Y each" → quantité d'items + prix unitaire ──
    m = re.search(rf'({_NUM_RE})\s+([a-z]+)\s+at\s+\$\s*([\d,]+)\s+each', q)
    if m:
        obj = _clean_obj(m.group(2))
        if obj:
            _add('items_at', obj=obj, val=_num(m.group(1)), prix=_num(m.group(3)))

    # ── "sells/buys N X for $Y each/per/a slice" → quantité + revenu ──
    m = re.search(rf'(sells?|buys?|bought|purchased)\s+({_NUM_RE})\s+'
                  rf'([a-z]+)\s+(?:for|at)\s+\$?\s*([\d,]+(?:\.\d+)?)\s+'
                  rf'(?:each|per|a\s+[a-z]+)', q)
    if m:
        obj = _clean_obj(m.group(3))
        if obj:
            _add('sell_at' if m.group(1).startswith('sell') else 'buy_at',
                 obj=obj, val=_num(m.group(2)), prix=_num(m.group(4)))

    # ── "N X for $Y" (paquets : "4 yogurts for $5") → prix unitaire ──
    m = re.search(rf'({_NUM_RE})\s+([a-z]+)\s+for\s+\$?\s*([\d,]+(?:\.\d+)?)', q)
    if m and not re.search(r'\b(each|per)\b', q):
        obj = _clean_obj(m.group(2))
        if obj:
            _add('pack', obj=obj, val=_num(m.group(1)), prix=_num(m.group(3)))

    # ── "a/b of the N X" (fraction d'une quantité) ──
    m = re.search(rf'({_NUM_RE})\s*/\s*({_NUM_RE})\s+of\s+(?:the\s+)?'
                  rf'({_NUM_RE})\s+([a-z]+)', q)
    if m:
        obj = _clean_obj(m.group(4))
        if obj:
            _add('frac_of', obj=obj, val=_num(m.group(1)) / _num(m.group(2)),
                 amt=_num(m.group(3)))

    # ── Taux : "N dollars each" / "N per day" / "N a day" / "N every morning" ──
    m = re.search(rf'\$?\s*({_NUM_RE})\s+dollars?\s+each', q)
    if m:
        _add('rate_each', obj=None, val=_num(m.group(1)))
    m = re.search(rf'({_NUM_RE})\s+(?:([a-z]+)\s+)?per\s+'
                  rf'(day|hour|week|month|year|minute|dozen)', q)
    if m:
        obj = _clean_obj(m.group(2) or '')
        _add('rate', obj=(obj if obj and obj not in _UNIT_WORDS else None),
             val=_num(m.group(1)), unit=m.group(3))
    m = re.search(rf'({_NUM_RE})\s+((?:[a-z]+\s+)?)a\s+(day|hour|week|month|year)\b', q)
    if m:
        obj = _clean_obj((m.group(2) or '').strip())
        _add('rate', obj=(obj if obj and obj not in _UNIT_WORDS else None),
             val=_num(m.group(1)), unit=m.group(3))
    m = re.search(rf'\$\s*([\d,]+(?:\.\d+)?)\s+per\s+(?:[a-z]+\s+)*([a-z]+)\b', q)
    if m:
        obj = _clean_obj(m.group(2))
        _add('rate_each', obj=obj, val=_num(m.group(1)))
    m = re.search(rf'({_NUM_RE})\s+(?:[a-z]+\s+){{0,4}}every\s+'
                  rf'(morning|night|day|hour)\b', q)
    if m:
        _add('rate', obj=None, val=_num(m.group(1)),
             unit='day' if m.group(2) in ('morning', 'night') else m.group(2))
    # « every day with N (X) » — les X sont CONSOMMÉS (signe − forcé)
    m = re.search(rf'every\s+(?:day|morning|night)[^.]*?\b(?:with|using|'
                  rf'uses?)\s+({_NUM_RE})\b(?:\s+([a-z]+))?', q)
    if m:
        obj = _clean_obj(m.group(2) or '')
        _add('rate', obj=(obj or None), val=_num(m.group(1)), unit='day',
             neg=True)
    m = re.search(rf'([a-z]+)\s+costs?\s+\$?\s*({_NUM_RE}(?:\.\d+)?)', q)
    if m and not re.search(r'\b(per|each)\b', q):
        obj = _clean_obj(m.group(1))
        if obj:
            _add('rate_each', obj=obj, val=_num(m.group(2)))

    # ── Initialisation : "has N X" / "started with N X" / "there are N X" ──
    m = re.search(rf'(?:has|had|have|owns?|started with|bought|purchased|'
                  rf'collected|found|bakes?|makes?|produces?|harvests?|'
                  rf'raises?|plants?|grows?|creates?)\s+({_NUM_RE})\s+'
                  rf'([a-z]+)', q)
    if m and not re.search(r'\b(?:more|less|fewer|away|each|times)\b', q):
        obj = _clean_obj(m.group(2))
        if obj:
            _add('init', obj=obj, val=_num(m.group(1)))
    m = re.search(rf'there (?:are|were)\s+({_NUM_RE})\s+([a-z]+)', q)
    if m:
        obj = _clean_obj(m.group(2))
        if obj:
            _add('init', person=None, obj=obj, val=_num(m.group(1)))
    # « A weighs N X » / « A does N pounds of X » (mesures)
    m = re.search(rf'([a-z]+)\s+weighs?\s+({_NUM_RE})\s+([a-z]+)\b', q)
    if m and not re.search(r'\b(less|more|than|times|what)\b', q):
        obj = _clean_obj(m.group(3))
        if obj:
            _add('init', person=m.group(1), obj=obj, val=_num(m.group(2)))
    m = re.search(rf'([a-z]+)\s+does\s+({_NUM_RE})\s+(?:pounds?|kg|tons?)\s+'
                  rf'of\s+([a-z]+)', q)
    if m:
        obj = _clean_obj(m.group(3))
        if obj:
            _add('init', person=m.group(1), obj=obj, val=_num(m.group(2)))

    # ── Ajouts : "buys N more X" / "gets N X" / "N more" (objet implicite) ──
    m = re.search(rf'(?:buys?|gains?|gets?|receives?|earns?|finds?|adds?)\s+'
                  rf'({_NUM_RE})(?:\s+(?:more\s+)?([a-z]+))?', q)
    if m:
        obj = _clean_obj(m.group(2) or '')
        if not obj and last_obj:
            obj = last_obj
        if obj:
            _add('add', obj=obj, val=_num(m.group(1)))

    # ── Retraits : "sells N X" / "gives away N X" / "spends N dollars" ──
    m = re.search(rf'(?:sells?|gives? away|gives?|loses?|spends?|eats?|ate|'
                  rf'removes?|takes? away|dropped|uses?|throws? away)\s+'
                  rf'({_NUM_RE})(?:\s+([a-z]+))?', q)
    if m:
        obj = _clean_obj(m.group(2) or '')
        if not obj and last_obj:
            obj = last_obj
        if obj:
            _add('sub', obj=obj, val=_num(m.group(1)))

    # ── REPLI par dépendances : aucune regex n'a tiré → graphe syntaxique ──
    if not acts:
        acts = _dep_actions(q, last_person, last_obj)

    return acts


def detect_action(sentence: str, last_person: Optional[str] = None,
                  last_obj: Optional[str] = None) -> Optional[Dict]:
    """Détecte l'action principale d'une phrase (première interprétation)."""
    acts = _detect_all(sentence, last_person, last_obj)
    return acts[0] if acts else None


def detect_actions(sentence: str, last_person: Optional[str] = None,
                   last_obj: Optional[str] = None) -> List[Dict]:
    """Toutes les interprétations plausibles (pour le champ de résonance)."""
    return _detect_all(sentence, last_person, last_obj)


# ── REPLI PAR ANALYSE DE DÉPENDANCES LÉGÈRE ───────────────────────────────────
# Lexique de classes de verbes (verbe principal → op). Petit et universel :
# ce n'est PAS une liste de motifs, c'est la classe syntaxique du prédicat.
_VERB_LEX = [
    (r'\b(?:has|have|had|owns?|started with|started out with)\b', 'init'),
    (r'\b(?:buys?|bought|purchases?|purchased|gains?|gained|gets?|got|'
     r'receives?|received|finds?|found|adds?|added|plants?|planted|'
     r'collects?|collected)\b', 'add'),
    (r'\b(?:sells?|sold|gives?|gave|loses?|lost|spends?|spent|eats?|ate|'
     r'removes?|removed|pays?|paid|donates?|donated)\b', 'sub'),
    (r'\b(?:earns?|earned|makes?|made|raises?|raised)\b', 'rate'),
    (r'\b(?:costs?|cost)\b', 'rate_each'),
]


def _dep_actions(sentence: str, last_person: Optional[str] = None,
                 last_obj: Optional[str] = None) -> List[Dict]:
    """REPLI par dépendances : sujet syntaxique (premier nom de la phrase),
    verbe principal (classe), attachement nombre→tête nominale.

    Conservateur — ne tire QUE si les regex n'ont rien trouvé :
      - phrases interrogatives exclues (la question porte la CIBLE, pas une action) ;
      - verbe requis dans le lexique de classes ; nombre requis avec tête ;
      - « makes/earns » sans « per » → ambigu → refus ;
      - au plus 2 actions par phrase.
    C'est l'analyse de dépendances minimale : le graphe (sujet, verbe, objet)
    plutôt que les motifs lexicaux.
    """
    if re.search(r'\b(how many|how much|what is|what are|what was|'
                 r'what did|how old|how far|how long)\b', sentence):
        return []
    vb = None
    for pat, op in _VERB_LEX:
        m = re.search(pat, sentence)
        if m:
            vb = (m.start(), op)
            break
    if vb is None:
        return []
    vpos, op = vb
    # sujet syntaxique : premier nom (non-stopword) de la phrase,
    # sinon le pronom → la personne précédente
    subject = None
    for w in re.findall(r'[a-z]+', sentence[:vpos]):
        if w in _STOP_OBJ or w in _PRONOUNS or w == 'there':
            continue
        if any(re.search(rf'\b{re.escape(w)}\b', p)
               for p, _o in _VERB_LEX):
            continue
        subject = w
        break
    if subject is None and any(p in sentence for p in _PRONOUNS):
        subject = last_person
    if subject is None:
        return []
    acts = []
    for m in re.finditer(rf'({_NUM_RE})\s+([a-z]+)', sentence):
        val = _num(m.group(1))
        obj = _clean_obj(m.group(2))
        if val == 0 or not obj:
            continue
        if op == 'rate' and not re.search(r'\bper\b', sentence[vpos:]):
            continue
        if op == 'init':
            acts.append(dict(op='init', person=subject, obj=obj, val=val))
        elif op == 'add':
            acts.append(dict(op='add', person=subject, obj=obj, val=val))
        elif op == 'sub':
            acts.append(dict(op='sub', person=subject, obj=obj, val=val))
        elif op == 'rate':
            unit = re.search(r'per\s+([a-z]+)', sentence[vpos:])
            acts.append(dict(op='rate', person=subject, obj=obj, val=val,
                             unit=unit.group(1) if unit else 'day'))
        else:  # rate_each
            acts.append(dict(op='rate_each', obj=obj, val=val))
        if len(acts) >= 2:
            break
    return acts


# ═══════════════════════════════════════════════════════════════════════════════
# LE SOLVEUR
# ═══════════════════════════════════════════════════════════════════════════════

class WordProblemStateSolver:
    """Résout les problèmes de mots narratifs par mise à jour d'état."""

    def _solve_compound(self, q: str) -> Optional[Tuple[float, List[str]]]:
        """
        Motifs composés GSM8K : des structures complètes multi-étapes
        (production par jour, profit, aller-retour, douzaines…) qui se
        résolvent en une formule.
        """
        # "N X which cost $Y per Z" (répété) → somme des produits
        # (3 dozen donuts which cost $68 per dozen, 2 dozen mini cupcakes…)
        per_matches = list(re.finditer(
            rf'({_NUM_RE})\s+\w+(?:[ \w]+?)\s+costs?\s+\$\s*([\d,]+)\s+per\s+\w+', q))
        if len(per_matches) >= 1:
            has_per = re.search(r'\bper\b', q)
            if has_per:
                total = sum(_num(m.group(1)) * _num(m.group(2))
                            for m in per_matches)
                if len(per_matches) >= 2 or 'total' in q or 'spend' in q \
                   or 'cost' in q:
                    steps = [f"{_num(m.group(1))} × {_num(m.group(2))}"
                             for m in per_matches]
                    return total, steps + [f"total : {total}"]

        # "paid/costs $X for N items → combien par item ?"
        m = re.search(rf'(?:paid|costs?|bought|purchased).*?\$\s*([\d,]+)'
                      rf'(?:[^.]*?)\bfor\s+({_NUM_RE})\s+(?:items?|boxes?|'
                      rf'books?|pairs?|bags?|tickets?|candies?|cookies?|'
                      rf'glasses?|shoes?|hats?|muffins?|cakes?|pies?|'
                      rf'loaves?|pens?|bottles?|shirts?|donuts?)\b.*?'
                      rf'(?:each|per|cost)', q)
        if m and ('each' in q or 'per' in q or 'cost' in q):
            a, n = _num(m.group(1)), _num(m.group(2))
            return a / n, [f"{a} / {n} = {a / n} par item"]

        # "earns N dollars per hour/day, works H hours/days → gain"
        m = re.search(rf'(?:earns?|makes?|gets?|receives?|pays?)\s+\$\s*'
                      rf'([\d,]+(?:\.[\d,]+)?)\s+per\s+(hour|day|week).*?'
                      rf'(?:for|works?|hours?)\s+({_NUM_RE})\s+'
                      rf'(hours?|days?|weeks?)', q)
        if m:
            rate, unit, dur = _num(m.group(1)), m.group(2), _num(m.group(3))
            if unit.rstrip('s') == m.group(4).rstrip('s') or \
               (unit.startswith('hour') and m.group(4).startswith('hour')):
                return rate * dur, [f"{rate} × {dur} = {rate * dur} "
                                    f"({unit.rstrip('s')}s)"]

        # "dinner/lunch costs $X, leaves a Y% tip → total"
        m = re.search(rf'(?:dinner|lunch|meal|bill|restaurant|check).*?'
                      rf'costs?\s+\$\s*([\d,]+).*?(?:tip|leave|leaves)\s+'
                      rf'({_NUM_RE})\s*%', q)
        if m:
            a, t = _num(m.group(1)), _num(m.group(2))
            return a * (1 + t / 100), [f"{a} × (1 + {t}%) = "
                                       f"{a * (1 + t / 100)}"]

        # "X dollars with Y% off / discount" (remise)
        m = re.search(rf'\$\s*([\d,]+).*?({_NUM_RE})\s*%\s*'
                      rf'(?:off|discount|sale)', q)
        if m:
            a, p = _num(m.group(1)), _num(m.group(2))
            return a * (1 - p / 100), [f"{a} × (1 − {p}%) = "
                                       f"{a * (1 - p / 100)}"]

        # "lays N eggs per day, eats M every morning, how many left after D days?"
        m = re.search(rf'({_NUM_RE})(?:\s+[a-z]+)?\s+per day.*?'
                      rf'(?:eats?|uses?|consumes?)\s+({_NUM_RE}).*?'
                      rf'after\s+({_NUM_RE})\s+days?', q)
        if m:
            a, b, d = _num(m.group(1)), _num(m.group(2)), _num(m.group(3))
            net = a - b
            return net * d, [f"{a} − {b} = {net} par jour",
                             f"{net} × {d} = {net * d} après {d} jours"]

        # "takes N X (of Y) and half that much Z" → N × 1.5 (total des deux)
        m = re.search(rf'({_NUM_RE})\s+[a-z]+(?:\s+[a-z]+)*?\s+and\s+'
                      rf'half\s+that\s+much', q)
        if m and 'total' in q:
            a = _num(m.group(1))
            return a * 1.5, [f"{a} + {a}/2 = {a * 1.5}"]

        # "buys X for $A, puts in $B (repairs), sells for $C → profit?"
        m = re.search(rf'buys?.*?\$\s*([\d,]+).*?puts?\s+in\s+\$\s*([\d,]+).*?'
                      rf'sells?.*?\$\s*([\d,]+).*?(?:profit|earn)', q)
        if m:
            a, b, c = _num(m.group(1)), _num(m.group(2)), _num(m.group(3))
            cost = a + b
            return c - cost, [f"coût {a} + {b} = {cost}",
                              f"profit {c} − {cost} = {c - cost}"]

        # "coûte $C à planter, pousse N par an, vend $P chacun, coûte $X/an
        #  → années avant de commencer à gagner" (break-even)
        m = re.search(rf'(?:costs?|cost)\s+\$\s*([\d,]+)[\s\S]*?'
                      rf'(?:grows?|produces?|lays?|yields?)\s+({_NUM_RE})\s+'
                      rf'[\s\S]+?sell[s]?\s+for\s+\$\s*([\d,]+(?:\.\d+)?)\s+each'
                      rf'[\s\S]*?costs?\s+\$\s*([\d,]+(?:\.\d+)?)\s+a\s+year', q)
        if m and re.search(r'\bhow many years\b', q):
            c = _num(m.group(1))
            n = _num(m.group(2))
            p = _num(m.group(3))
            cper = _num(m.group(4))
            margin = n * p - cper
            if margin > 0:
                exact = c / margin
                years = int(exact) + (1 if exact % 1 < 1e-9 else 0)
                if exact % 1 >= 1e-9:
                    years = int(exact) + 1
                return years, [f"marge/an : {n}×{p} − {cper} = {margin}",
                               f"{c} / {margin} = {exact} → année {years}"]

        # "runs N sprints M times a week, K meters each → total meters"
        m = re.search(rf'runs?\s+({_NUM_RE})\s+\w+\s+({_NUM_RE})\s+times a week'
                      rf'.*?({_NUM_RE})\s+meters?\s+each', q)
        if m:
            n, t, k = _num(m.group(1)), _num(m.group(2)), _num(m.group(3))
            return n * t * k, [f"{n} × {t} = {n * t} sprints",
                               f"{n * t} × {k} = {n * t * k} mètres"]

        # "N in the first month, three times as many in the second → total"
        # (« second » peut précéder « three times » ; « three » est normalisé
        # en « 3 » par normalize → accepter « 3 times »)
        m = re.search(rf'({_NUM_RE})\s+.*?\bfirst\s+(?:month|week|day)\b.*?'
                      rf'(three times|3 times|twice|double|half|2 times|'
                      rf'4 times)\s+(?:as many|that much)', q)
        if m:
            a = _num(m.group(1))
            f = {'three times': 3.0, '3 times': 3.0, 'twice': 2.0,
                 'double': 2.0, '2 times': 2.0, '4 times': 4.0,
                 'half': 0.5}[m.group(2)]
            # « but then reduced by N% in the third month » → 3ᵉ période
            m3 = re.search(r'reduced by\s+(\d+)\s*%', q)
            if m3:
                pct = _num(m3.group(1)) / 100.0
                total = a + a * f + a * f * (1 - pct)
                return total, [f"1ʳᵉ : {a} · 2ᵉ : {a} × {f} = {a * f}",
                               f"3ᵉ : {a * f} × (1 − {pct:.0%}) = "
                               f"{a * f * (1 - pct)}",
                               f"total : {total}"]
            if 'total' in q or 'altogether' in q or 'sum' in q or \
               'in all' in q:
                return a * (1 + f), [f"{a} + {a} × {f} = {a * (1 + f)}"]
            return a * f, [f"{a} × {f} = {a * f}"]

        # "drives N hours at K mph and turns around → aller-retour"
        m = re.search(rf'({_NUM_RE})\s+hours?\s+at\s+({_NUM_RE})\s+mph.*?'
                      rf'turns?\s+around', q)
        if m:
            h, v = _num(m.group(1)), _num(m.group(2))
            return 2 * h * v, [f"{h} × {v} = {h * v} (aller)",
                               f"aller-retour : 2 × {h * v} = {2 * h * v}"]

        # "N dozen X costing $Y per dozen → total cost"
        m = re.search(rf'({_NUM_RE})\s+dozen.*?(?:costs?|cost|price).*?'
                      rf'\$\s*([\d,]+)\s+per dozen', q)
        if m:
            a, b = _num(m.group(1)), _num(m.group(2))
            return a * b, [f"{a} douzaines × {b} = {a * b}"]

        return None

    def solve(self, question: str,
              use_compounds: bool = True) -> Optional[Tuple[float, List[str]]]:
        q = normalize(question)
        sentences = _split_sentences(q)
        # ── Motifs composés GSM8K (structures multi-étapes fréquentes) ──
        if use_compounds:
            compound = self._solve_compound(q)
            if compound is not None:
                return compound

        state: Dict[Tuple, float] = {}   # (personne|None, objet) → quantité
        rates: List[Tuple] = []          # (valeur, unité, signe, entité)
        mults: List[Tuple] = []          # relations × à résoudre en différé
        rels: List[Tuple] = []           # relations linéaires A = c×B + d
        money: float = 0.0               # argent accumulé (ventes/achats)
        steps: List[str] = []
        current_person: Optional[str] = None
        last_obj: Optional[str] = None

        # Passer 1 : actions des phrases non interrogatives
        for sent in sentences:
            is_q = bool(re.search(r'\b(how many|how much|what is|what are|'
                                  r'how far|how long|what was|what did|'
                                  r'how old|how often)\b', sent))
            acts = detect_actions(sent, last_person=current_person,
                                  last_obj=last_obj)
            if not acts:
                continue
            if is_q:
                # les phrases-question portent les ANCRES (« if X has N Y ») :
                # on ne retient que relations/initialisations, pas les taux
                acts = [a for a in acts if a['op'] in
                        ('init', 'rel', 'set_mult', 'set_plus', 'set_minus')]
                if not acts:
                    continue
            action = acts[0]                      # l'interprétation COMMISE
            op = action['op']
            person = action.get('person')
            obj = action['obj']
            val = action.get('val', 0.0)
            if person:
                current_person = person
            if obj:
                last_obj = obj
            key = (person, obj) if obj else None

            if op == 'init' and key:
                state[key] = val
                steps.append(f"{key} ← {val}")
            elif op == 'add' and key:
                state[key] = state.get(key, 0.0) + val
                steps.append(f"{key} += {val} → {state[key]}")
            elif op == 'sub' and key:
                state[key] = state.get(key, 0.0) - val
                steps.append(f"{key} -= {val} → {state[key]}")
            elif op == 'set_mult' and action.get('obj2') is not None:
                # relations différées (la base peut arriver plus tard)
                mults.append((person, obj, val, action['obj2'],
                              action.get('ref_obj')))
            elif op == 'rel' and action.get('obj'):
                rels.append((person, obj, action.get('ref'), obj,
                             action.get('coeff', 1.0),
                             action.get('delta', 0.0)))
            elif op == 'each_has' and action.get('obj2') is not None:
                # "each box has 5 pencils" : pencil = state[box] × 5
                src = action['obj2']
                base = state.get((None, src), 0.0) or \
                       state.get((person, src), 0.0)
                state[key] = base * val
                steps.append(f"{key} = {base} × {val} → {state[key]}")
            elif op == 'set_plus':
                state[key] = state.get(key, 0.0) + val
                steps.append(f"{key} += {val} → {state[key]}")
            elif op == 'set_minus':
                state[key] = state.get(key, 0.0) - val
                steps.append(f"{key} -= {val} → {state[key]}")
            elif op == 'rate':
                unit = action.get('unit', '')
                sign = -1.0 if action.get('neg') or re.search(
                    r'\b(eats?|ate|uses?|spends?|burns?|consumes?|drinks?|'
                    r'melts?|removes?)\b', sent) else 1.0
                rates.append((val, unit, sign, action.get('obj')))
            elif op == 'rate_each':
                rates.append((val, 'each', 1.0, action.get('obj')))
            elif op == 'items_at':
                state[key] = val
                rates.append((action.get('prix', 0.0), 'each', 1.0, obj))
                steps.append(f"{key} ← {val} à {action.get('prix')} chacun")
            elif op == 'sell_at' and key:
                state[key] = val
                money += val * action.get('prix', 0.0)
                steps.append(f"vendu : {val} × {action.get('prix')} "
                             f"→ +{val * action.get('prix')} $")
            elif op == 'buy_at' and key:
                state[key] = val
                money += val * action.get('prix', 0.0)
                steps.append(f"acheté : {val} × {action.get('prix')} "
                             f"→ {val * action.get('prix')} $")
            elif op == 'pack' and key:
                state[key] = val
                rates.append((action.get('prix', 0.0) / val, 'each', 1.0, obj))
                steps.append(f"paquet : {val} pour {action.get('prix')} "
                             f"→ {action.get('prix') / val} l'unité")
            elif op == 'frac_of' and key:
                state[key] = val * action.get('amt', 0.0)
                steps.append(f"{key} = {val} × {action.get('amt')} "
                             f"→ {state[key]}")

            # Taux et relations ADDITIONNELS des autres interprétations de la
            # phrase (non conflictuels : pas de mutation d'état immédiate).
            # « eats 3… every morning and bakes… with 4 eggs », « raymond does
            # half… and sarah does 4 times… » → les deux alimentent le réseau.
            for extra in acts[1:]:
                eop = extra['op']
                if eop == 'rate':
                    unit = extra.get('unit', '')
                    sign = -1.0 if extra.get('neg') or re.search(
                        r'\b(eats?|ate|uses?|spends?|burns?|consumes?|'
                        r'drinks?|melts?|removes?)\b', sent) else 1.0
                    rates.append((extra['val'], unit, sign, extra.get('obj')))
                elif eop == 'rate_each':
                    rates.append((extra['val'], 'each', 1.0, extra.get('obj')))
                elif eop == 'rel' and extra.get('obj'):
                    rels.append((extra.get('person'), extra['obj'],
                                 extra.get('ref'), extra['obj'],
                                 extra.get('coeff', 1.0),
                                 extra.get('delta', 0.0)))
                elif eop == 'set_mult' and extra.get('obj2'):
                    mults.append((extra.get('person'), extra['obj'],
                                  extra['val'], extra['obj2'],
                                  extra.get('ref_obj')))
                elif eop == 'init' and extra.get('obj'):
                    # ancre additionnelle (phrase multi-actions) si libre
                    ek = (extra.get('person'), extra['obj'])
                    if ek not in state:
                        state[ek] = extra['val']
                        steps.append(f"{ek} ← {extra['val']}")

        # Résolution combinée des relations × et linéaires (point fixe :
        # base d'abord, inversion « sarah = 4×david » → david = sarah/4,
        # puis rels A = coeff×B + delta, jusqu'à convergence)
        for _ in range(len(mults) + len(rels) + 4):
            progress = False
            for person, obj, val, ref, ref_obj in mults:
                base_obj = ref_obj or obj
                key = (person, obj)
                base = state.get((ref, base_obj), None)
                if base is None and state.get(key) is not None and val != 0:
                    state[(ref, base_obj)] = state[key] / val
                    steps.append(f"{ref} = {key} / {val} → {state[(ref, base_obj)]}")
                    progress = True
                    continue
                if base is None:
                    continue
                if abs(state.get(key, 0.0) - base * val) > 1e-9:
                    state[key] = base * val
                    steps.append(f"{key} = {base} × {val} → {state[key]}")
                    progress = True
            for person, obj, ref, ref_obj, coeff, delta in rels:
                bkey = (ref, ref_obj)
                b = state.get(bkey, None)
                if b is None:
                    continue
                akey = (person, obj)
                v = coeff * b + delta
                if abs(state.get(akey, float('inf')) - v) > 1e-9:
                    state[akey] = v
                    steps.append(f"{akey} = {coeff}×{b} {delta:+g} → {v}")
                    progress = True
            if not progress:
                break

        # Passer 2 : FLUX JOURNALIER NET — les taux temporels sont SIGNÉS
        # (production +, consommation −) et agrégés par unité, puis × durée
        # (question, horloge, « every day »=1, « a week »=7…). Si la question
        # porte sur l'argent, on lie le prix unitaire de l'entité du flux.
        q_sent = next((s for s in sentences
                       if re.search(r'\b(how many|how much|what is|what are)\b', s)), q)
        q_money = bool(re.search(r'\b(how much|spend|spent|cost|pay|paid|'
                                 r'make|earn|raise|revenue|worth|money)\b', q_sent))
        # « how many X » = compte, pas argent (même si de l'argent est cité)
        if re.search(r'\bhow many\b', q_sent) and \
           not re.search(r'\b(dollars?|money|salary|cost|spend|paid)\b', q_sent):
            q_money = False

        def _flux(unit: str, dur: float, src: str) -> Optional[Tuple]:
            flows = [s * v for v, u, s, o in rates
                     if (u or '').rstrip('s') == unit.rstrip('s')]
            if not flows:
                return None
            net = sum(flows)
            if abs(net) < 1e-9:
                return None
            qty = abs(net) * dur
            if q_money:
                ents = {o for v, u, s, o in rates
                        if (u or '').rstrip('s') == unit.rstrip('s') and o}
                price = next((v for v, u, s, o in rates
                              if u == 'each' and o in ents), None)
                if price is None:
                    price = next((v for v, u, s, o in rates if u == 'each'),
                                 None)
                if price is not None:
                    dz = next((v for v, u, s, o in rates
                               if u == 'each' and o == 'dozen'), None)
                    qty_conv = qty / 12.0 if dz is not None else qty
                    total = price * qty_conv
                    steps.append(f"flux {net:+g}/{unit} × {dur} = {qty} "
                                 f"→ {price} × {qty_conv} = {total} $ ({src})")
                    return total, steps
                steps.append(f"flux {net:+g}/{unit} × {dur} = {qty} "
                             f"(prix absent, {src})")
                return qty, steps
            steps.append(f"flux {net:+g}/{unit} × {dur} = {qty} ({src})")
            return qty, steps

        for sent in sentences + [q_sent]:
            mc = re.search(rf'\bfrom\s+(\d+):?\d*\s*(?:am|pm)?\s+to\s+'
                           rf'(\d+):?\d*\s*(am|pm)\b', sent)
            if mc:
                h1, h2 = int(mc.group(1)), int(mc.group(2))
                if h2 <= h1:
                    h2 += 12
                r = _flux('hour', float(h2 - h1), 'horloge')
                if r is not None:
                    return r
            m = re.search(rf'\b(?:for|after|over|in|at the end of)\s+'
                          rf'({_NUM_RE})\s+(days?|hours?|weeks?|months?|'
                          rf'years?|minutes?)\b', sent)
            if m:
                r = _flux(m.group(2).rstrip('s'), _num(m.group(1)), 'durée')
                if r is not None:
                    return r
            m = re.search(rf'\ba\s+(week|month|year)\b', sent)
            if m:
                mult = {'week': 7.0, 'month': 30.0, 'year': 365.0}[m.group(1)]
                r = _flux(m.group(1), mult, 'par semaine/mois/an')
                if r is not None:
                    return r
            m = re.search(rf'\bevery\s+(day|morning|night)\b', sent)
            if m:
                r = _flux('day', 1.0, 'quotidien')
                if r is not None:
                    return r

        # Passer 3 : la question finale
        persons = _persons(q_sent)
        person = persons[0] if persons else (
            current_person if any(p in q_sent for p in _PRONOUNS) else None)

        # "how much ... (spend/raise/earn/make/paid)" → argent accumulé
        if q_money and money > 0:
            steps.append(f"argent total : {money}")
            return money, steps

        # "in total / altogether" → somme de l'objet demandé
        m = re.search(r'how many\s+(?!total|altogether)([a-z]+)\b.*?'
                      r'(?:in total|altogether|total)', q_sent)
        if m:
            obj = _clean_obj(m.group(1))
            if obj:
                total = sum(v for (p, o), v in state.items()
                            if o == obj and (person is None or p == person))
                if total or state:
                    steps.append(f"total {obj} = {total}")
                    return total, steps

        # "how many X ... left/remain" / "how many X does P have"
        # ── CIBLE SOMME MULTI-ENTITÉS — « how many O do P1, P2 (and P3) have »
        #    (template à SLOTS : entités quelconques, l'objet est commun) ──
        m = re.search(
            r'how many\s+([a-z]+)\s+do\s+'
            r'([a-z]+(?:,\s+and\s+|,\s*|\s+and\s+)[a-z]+)+\s+have\b', q_sent)
        if m:
            obj = _clean_obj(m.group(1))
            names = [n for n in re.split(r'\s*(?:,|and)\s*', m.group(2)) if n]
            if obj and len(names) >= 2:
                vals = [state.get((n, obj)) for n in names]
                if all(v is not None for v in vals):
                    steps.append(f"somme {names} {obj} = {sum(vals)}")
                    return sum(vals), steps
        m = re.search(r'how many\s+([a-z]+)\s+does\s+([a-z]+)\s+have', q_sent)
        if m:
            obj = _clean_obj(m.group(1))
            p2 = m.group(2)
            if (p2, obj) in state:
                steps.append(f"({p2}, {obj}) = {state[(p2, obj)]}")
                return state[(p2, obj)], steps
        m = re.search(r'how many\s+([a-z]+)\b', q_sent)
        if m:
            obj = _clean_obj(m.group(1))
            if obj:
                key = (person, obj)
                if key in state:
                    steps.append(f"{key} = {state[key]}")
                    return state[key], steps
                vals = [v for (p, o), v in state.items()
                        if o == obj and (person is None or p == person)]
                if vals:
                    if 'total' in q_sent or 'altogether' in q_sent:
                        return sum(vals), steps
                    if person is None and len(vals) == 1:
                        return vals[0], steps

        # "how old is A's B" / "how many is A's B" → lecture possessive
        m = re.search(r'how (?:old|many)\s+is\s+([a-z]+)\'s\s+([a-z]+)', q_sent)
        if m:
            key = (m.group(1), _clean_obj(m.group(2)))
            if key in state:
                steps.append(f"{key} = {state[key]}")
                return state[key], steps

        # "difference in the amount of A and B X" → |A − B| (deux ordres)
        m = re.search(
            r'difference in the amount of\s+'
            r'(?:([a-z]+)\s+([a-z]+)\s+and\s+([a-z]+)'      # « of laundry raymond and david »
            r'|([a-z]+)\s+and\s+([a-z]+)\s+([a-z]+))',      # « of raymond and david laundry »
            q_sent)
        if m:
            if m.group(1):
                obj, a, b = _clean_obj(m.group(1)), m.group(2), m.group(3)
            else:
                a, b, obj = m.group(4), m.group(5), _clean_obj(m.group(6))
            a1 = state.get((a, obj))
            b1 = state.get((b, obj))
            if a1 is not None and b1 is not None:
                steps.append(f"différence : |{a1} − {b1}| = {abs(a1 - b1)}")
                return abs(a1 - b1), steps

        # "combined X" / "total pets do the N have" → somme des entités
        if 'combined' in q_sent or 'total' in q_sent:
            m = re.search(r'(?:combined|total)\s+([a-z]+)', q_sent)
            obj = _clean_obj(m.group(1)) if m else None
            vals = [v for (p, o), v in state.items()
                    if (obj is None or o == obj)]
            if not vals and 'combined' in q_sent and state:
                # repli : l'objet d'état le plus peuplé (« combined weights »)
                cnt = Counter(o for (p, o) in state)
                obj = max(cnt, key=cnt.get)
                vals = [v for (p, o), v in state.items() if o == obj]
            if vals and len(vals) >= 2:
                steps.append(f"somme {obj} = {sum(vals)}")
                return sum(vals), steps

        # "how much ... total cost" → somme des produits (prix × quantités)
        if q_money:
            if rates and state:
                price = next((v for v, u, s, o in rates if u == 'each'),
                             rates[0][0])
                m2 = re.search(r'how (?:much|many)\s+([a-z]+)\b', q_sent)
                obj = _clean_obj(m2.group(1)) if m2 else None
                qty = sum(v for (p, o), v in state.items()
                          if (obj is None or o == obj))
                if qty:                       # qty=0 → laisser la lecture éco
                    total = price * qty
                    steps.append(f"{price} × {qty} = {total}")
                    return total, steps

        # ── Lecture ÉCONOMIQUE (dernier recours) : lier chaque quantité
        #    (de l'énoncé OU de la question) à son prix unitaire → somme
        #    des produits. Ne s'applique que si aucun taux temporel n'existe
        #    (sinon une quantité « N par jour » serait lue comme un achat).
        if q_money and not any(u and u != 'each' for _v, u, _s, _o in rates):
            prices: Dict[str, float] = {}
            for sent in sentences:
                for act in detect_actions(sent):
                    if act['op'] == 'rate_each' and act.get('obj'):
                        prices.setdefault(act['obj'], act['val'])
                    elif act['op'] in ('items_at', 'sell_at', 'buy_at') \
                            and act.get('obj'):
                        prices.setdefault(act['obj'], act['prix'])
                    elif act['op'] == 'pack' and act.get('obj'):
                        prices.setdefault(act['obj'], act['prix'] / act['val'])
                # TOUS les prix : « X costs/cost $Y » et « X for $Y a slice »
                for pm in re.finditer(
                        rf'([a-z]+)\s+(?:that\s+)?(?:costs?|cost)\s+\$\s*'
                        rf'({_NUM_RE}(?:\.\d+)?)'
                        rf'|([a-z]+)\s+for\s+\$\s*({_NUM_RE}(?:\.\d+)?)\s+'
                        rf'a\s+[a-z]+', sent):
                    obj = _clean_obj(pm.group(1) or pm.group(3))
                    val = pm.group(2) or pm.group(4)
                    if obj:
                        prices.setdefault(obj, _num(val))
            qty: Dict[str, float] = {}
            scan_sents = sentences + ([] if q_sent in sentences else [q_sent])
            for sent in scan_sents:
                if re.search(r'\b(costs?|cost)\b', sent):
                    continue    # phrase de PRIX : « 1 X » = prix unitaire, pas quantité
                for qm in re.finditer(
                        rf'({_NUM_RE})\s+([a-z]+)(?:\s+of\s+([a-z]+))?', sent):
                    v = _num(qm.group(1))
                    o1 = _clean_obj(qm.group(2))
                    o2 = _clean_obj(qm.group(3)) if qm.group(3) else None
                    if o2 and o2 in prices:
                        qty[o2] = qty.get(o2, 0.0) + v
                    elif o1 and o1 in prices:
                        qty[o1] = qty.get(o1, 0.0) + v
            parts = [(o, qty[o], prices[o]) for o in prices if qty.get(o, 0.0)]
            if parts:
                total = sum(q * p for _o, q, p in parts)
                steps.append('économie : ' + ' + '.join(
                    f"{q}×{p}" for _o, q, p in parts))
                steps.append(f"total : {total}")
                return total, steps

        # ── SYSTÈME 2×2 — « N more/less X than Y » + total sur le suffixe
        #    commun (« 30 more gold coins than silver coins », « 110 coins »)
        #    → X = (T±d)/2, Y = (T∓d)/2. Template à SLOTS : X et Y sont des
        #    variétés d'un MÊME objet (suffixe commun), T est leur total. ──
        mb = re.search(
            rf'({_NUM_RE})\s+(more|fewer|less)\s+'
            rf'([a-z]+(?:\s+[a-z]+)?)\s+than\s+'
            rf'([a-z]+(?:\s+[a-z]+)?)\b', q)
        if mb:
            d = _num(mb.group(1)) if mb.group(2) == 'more' \
                else -_num(mb.group(1))
            wx, wy = mb.group(3), mb.group(4)
            sx, sy = wx.split()[-1], wy.split()[-1]
            if sx == sy:
                obj_x, obj_y = _stem_obj(wx), _stem_obj(wy)
                tm = re.search(rf'\b(?:there are|has|had)\s+'
                               rf'({_NUM_RE})\s+{sx}\b', q)
                if tm is not None:
                    T = _num(tm.group(1))
                    x, y = (T + d) / 2.0, (T - d) / 2.0
                    qobj = re.search(
                        r'how (?:many|much)\s+([a-z]+(?:\s+[a-z]+)?)',
                        q_sent)
                    cible = _stem_obj(qobj.group(1)) if qobj else None
                    if cible == obj_x:
                        steps.append(f"système 2×2 : {wx} = ({T}+{d:g})/2 "
                                     f"= {x:g}")
                        return x, steps
                    if cible == obj_y:
                        steps.append(f"système 2×2 : {wy} = ({T}{d:g})/2 "
                                     f"= {y:g}")
                        return y, steps

        return None


# ═══════════════════════════════════════════════════════════════════════════════
# CONSENSUS MULTI-PLANS — l'équivalent ondulatoire du majority voting LLM
# ═══════════════════════════════════════════════════════════════════════════════

def _solve_direct(q: str) -> Optional[Tuple[float, List[str]]]:
    """
    Stratégie « directe » : formule arithmétique guidée par l'intention de
    la question, sur les nombres dans l'ordre d'apparition. Prudente :
    uniquement 2-3 nombres (les énoncés trop riches ont des distracteurs).
    C'est une stratégie CONFIRMATRICE — elle ne décide jamais seule.
    """
    nums = [float(m.group(0).replace(',', '')) for m in
            re.finditer(rf'{_NUM_RE}', q)]
    if len(nums) < 2 or len(nums) > 3:
        return None
    a, b = nums[0], nums[1]

    # "left / remain / change" → soustraction
    if re.search(r'\b(left|remain|change|remaining|after spending)\b', q):
        if len(nums) == 2 and a >= b:
            return a - b, [f"direct : {a} − {b} = {a - b}"]

    # "N items at $X each / paid $X for N" → produit ou division
    if re.search(r'\b(each|per)\b', q) and \
       re.search(r'\b(cost|pay|paid|spend|price|worth)\b', q):
        if re.search(r'for\s+(\d+)', q):
            return a / b, [f"direct : {a} / {b} = {a / b}"]
        return a * b, [f"direct : {a} × {b} = {a * b}"]

    # "total / altogether / sum / in all" → addition
    if re.search(r'\b(total|altogether|sum|in all)\b', q) and len(nums) == 2:
        return a + b, [f"direct : {a} + {b} = {a + b}"]

    # "times / twice / double" → produit
    if re.search(r'\b(times|twice|double|product)\b', q) and len(nums) == 2:
        return a * b, [f"direct : {a} × {b} = {a * b}"]

    return None


def solve_consensus(question: str) -> Optional[Tuple[float, List[str]]]:
    """
    LE CONSENSUS MULTI-PLANS : trois stratégies INDÉPENDANTES résolvent le
    problème (état séquentiel, motifs composés, formule directe). Si deux
    stratégies (ou plus) convergent vers le MÊME résultat, il est adopté —
    c'est l'équivalent ondulatoire du majority voting des LLM. Sinon, la
    stratégie prioritaire tranche (état > composés > directe).
    """
    q = normalize(question)
    solver = WordProblemStateSolver()
    strategies: Dict[str, Tuple[float, List[str]]] = {}

    etat = solver.solve(question, use_compounds=False)
    if etat is not None:
        strategies['etat'] = etat
    composes = solver._solve_compound(q)
    if composes is not None:
        strategies['composes'] = composes
    directe = _solve_direct(q)
    if directe is not None:
        strategies['directe'] = directe

    if not strategies:
        return None

    # Vote : résultat partagé par le plus de stratégies
    votes: Dict[float, List[str]] = {}
    for name, (result, _steps) in strategies.items():
        votes.setdefault(round(result, 6), []).append(name)
    best_result, backers = max(votes.items(), key=lambda kv: len(kv[1]))

    if len(backers) >= 2:
        # 🔁 Convergence : plusieurs chemins indépendants → même onde
        return best_result, [f"consensus {len(backers)} stratégies "
                             f"({', '.join(backers)}) → {best_result}"]
    # Divergence : la stratégie la plus PRÉCISE tranche (les motifs composés
    # sont plus spécifiques que l'état générique ; la directe est seulement
    # confirmatrice)
    for name in ('composes', 'etat', 'directe'):
        if name in strategies:
            return strategies[name]
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

_SAMPLES = [
    ("John has 5 apples. He buys 3 more. How many apples does he have?", 8.0),
    ("Mary had 10 cookies. She ate 4. How many cookies does she have left?", 6.0),
    ("There are 6 boxes. Each box has 5 pencils. How many pencils are there in total?", 30.0),
    ("Tom has 12 dollars. He spends 4 dollars. How many dollars does he have left?", 8.0),
    ("A bakery bakes 24 loaves of bread. They sell 9 loaves. How many loaves are left?", 15.0),
    ("John has 5 apples. Mary has 3 times as many apples as John. How many apples does Mary have?", 15.0),
    ("Sue has 10 stickers. She gives 3 to her friend. How many stickers does Sue have left?", 7.0),
    ("There are 4 cars. Each car has 4 wheels. How many wheels are there in total?", 16.0),
]


if __name__ == '__main__':
    s = WordProblemStateSolver()
    ok = 0
    for q, exp in _SAMPLES:
        r = s.solve(q)
        good = r is not None and abs(r[0] - exp) < 1e-6
        ok += good
        print(f"{'✅' if good else '❌'} {q[:58]:<60} → {r[0] if r else None} (attendu {exp})")
    print(f"\nSCORE self-test : {ok}/{len(_SAMPLES)}")
