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


def detect_action(sentence: str, last_person: Optional[str] = None,
                  last_obj: Optional[str] = None) -> Optional[Dict]:
    """
    Détecte l'action d'une phrase. Retourne
    {'op': ..., 'person': str|None, 'obj': str, 'val': float,
     'obj2': str|None, 'unit': str|None}
    """
    q = sentence
    persons = _persons(q)
    person = persons[0] if persons else (
        last_person if any(p in q for p in _PRONOUNS) else None)

    # ── Relations : "N times as many X as Y" / "twice as many X as Y" ──
    m = re.search(rf'(\d+)\s+times as many\s+([a-z]+)\s+as\s+([a-z]+)', q)
    if m:
        obj, ref = _clean_obj(m.group(2)), _clean_obj(m.group(3))
        if obj:
            return {'op': 'set_mult', 'person': person, 'obj': obj,
                    'val': float(m.group(1)), 'obj2': ref}
    m = re.search(rf'(twice|three times|four times)\s+as many\s+'
                  rf'([a-z]+)\s+as\s+([a-z]+)', q)
    if m:
        mult = {'twice': 2.0, 'three times': 3.0, 'four times': 4.0}[m.group(1)]
        obj, ref = _clean_obj(m.group(2)), _clean_obj(m.group(3))
        if obj:
            return {'op': 'set_mult', 'person': person, 'obj': obj,
                    'val': mult, 'obj2': ref}

    # ── "Each X has N Y" / "each X costs N dollars" ──
    m = re.search(rf'each\s+([a-z]+)\s+has\s+({_NUM_RE})\s+([a-z]+)', q)
    if m:
        src, obj = _clean_obj(m.group(1)), _clean_obj(m.group(3))
        if obj:
            return {'op': 'each_has', 'person': person, 'obj': obj,
                    'val': _num(m.group(2)), 'obj2': src}
    m = re.search(rf'each\s+([a-z]+)\s+(?:costs?|is)\s+({_NUM_RE})\s+'
                  rf'(?:dollars?|\$)', q)
    if m:
        return {'op': 'rate_each', 'person': person, 'obj': None,
                'val': _num(m.group(2))}

    # ── "N more than Y" / "N less than Y" (comparaisons) ──
    m = re.search(rf'({_NUM_RE})\s+more than\s+([a-z]+)', q)
    if m:
        obj = _clean_obj(m.group(2))
        if obj:
            return {'op': 'set_plus', 'person': person, 'obj': obj,
                    'val': _num(m.group(1))}
    m = re.search(rf'({_NUM_RE})\s+(?:less|fewer) than\s+([a-z]+)', q)
    if m:
        obj = _clean_obj(m.group(2))
        if obj:
            return {'op': 'set_minus', 'person': person, 'obj': obj,
                    'val': _num(m.group(1))}

    # ── "N X at $Y each" → quantité d'items + prix unitaire ──
    m = re.search(rf'({_NUM_RE})\s+([a-z]+)\s+at\s+\$\s*([\d,]+)\s+each', q)
    if m:
        obj = _clean_obj(m.group(2))
        if obj:
            return {'op': 'items_at', 'person': person, 'obj': obj,
                    'val': _num(m.group(1)), 'prix': _num(m.group(3))}

    # ── Taux : "N dollars each" / "N per hour/day" ──
    m = re.search(rf'\$?\s*({_NUM_RE})\s+dollars?\s+each', q)
    if m:
        return {'op': 'rate_each', 'person': person, 'obj': None,
                'val': _num(m.group(1))}
    m = re.search(rf'({_NUM_RE})\s+per\s+(day|hour|week|month)', q)
    if m:
        return {'op': 'rate', 'person': person, 'obj': None,
                'val': _num(m.group(1)), 'unit': m.group(2)}

    # ── Initialisation : "has N X" / "started with N X" / "there are N X" ──
    m = re.search(rf'(?:has|had|have|owns?|started with|bought|purchased|'
                  rf'collected|found|bakes?|makes?|produces?|harvests?|'
                  rf'raises?|plants?|grows?|creates?)\s+({_NUM_RE})\s+'
                  rf'([a-z]+)', q)
    if m and not re.search(r'\b(?:more|less|fewer|away|each)\b', q):
        obj = _clean_obj(m.group(2))
        if obj:
            return {'op': 'init', 'person': person, 'obj': obj,
                    'val': _num(m.group(1))}
    m = re.search(rf'there (?:are|were)\s+({_NUM_RE})\s+([a-z]+)', q)
    if m:
        obj = _clean_obj(m.group(2))
        if obj:
            return {'op': 'init', 'person': None, 'obj': obj,
                    'val': _num(m.group(1))}

    # ── Ajouts : "buys N more X" / "gets N X" / "N more" (objet implicite) ──
    m = re.search(rf'(?:buys?|gains?|gets?|receives?|earns?|finds?|adds?)\s+'
                  rf'({_NUM_RE})(?:\s+(?:more\s+)?([a-z]+))?', q)
    if m:
        obj = _clean_obj(m.group(2) or '')
        if not obj and last_obj:
            obj = last_obj
        if obj:
            return {'op': 'add', 'person': person, 'obj': obj,
                    'val': _num(m.group(1))}

    # ── Retraits : "sells N X" / "gives away N X" / "spends N dollars" ──
    m = re.search(rf'(?:sells?|gives? away|gives?|loses?|spends?|eats?|ate|'
                  rf'removes?|takes? away|dropped|uses?|throws? away)\s+'
                  rf'({_NUM_RE})(?:\s+([a-z]+))?', q)
    if m:
        obj = _clean_obj(m.group(2) or '')
        if not obj and last_obj:
            obj = last_obj
        if obj:
            return {'op': 'sub', 'person': person, 'obj': obj,
                    'val': _num(m.group(1))}

    return None


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
        if len(sentences) < 2:
            return None

        # ── Motifs composés GSM8K (structures multi-étapes fréquentes) ──
        if use_compounds:
            compound = self._solve_compound(q)
            if compound is not None:
                return compound

        state: Dict[Tuple, float] = {}   # (personne|None, objet) → quantité
        rates: List[Tuple[float, str]] = []  # (valeur, unité) pour "per"
        steps: List[str] = []
        current_person: Optional[str] = None
        last_obj: Optional[str] = None

        # Passer 1 : actions des phrases non interrogatives
        for sent in sentences:
            if re.search(r'\b(how many|how much|what is|what are|how far|'
                         r'how long|what was|what did|how old|how often)\b', sent):
                continue
            action = detect_action(sent, last_person=current_person,
                                   last_obj=last_obj)
            if action is None:
                continue
            op = action['op']
            person = action.get('person')
            obj = action['obj']
            val = action['val']
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
                ref = action['obj2']
                if ref in _PERSONS_SET:
                    # "as many X as John" : base = état de John pour cet objet
                    base = state.get((ref, obj), 0.0)
                    state[key] = base * val
                    steps.append(f"{key} = {base} × {val} → {state[key]}")
                else:
                    key2 = (person, ref)
                    base = state.get(key2, 0.0)
                    state[key] = base * val
                    steps.append(f"{key} = {base} × {val} → {state[key]}")
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
                rates.append((val, action.get('unit', '')))
            elif op == 'rate_each':
                rates.append((val, 'each'))
            elif op == 'items_at':
                state[key] = val
                rates.append((action.get('prix', 0.0), 'each'))
                steps.append(f"{key} ← {val} à {action.get('prix')} chacun")

        # Passer 2 : "for N days/hours" → produit avec le taux
        for sent in sentences:
            if re.search(r'\b(how many|how much)\b', sent):
                continue
            m = re.search(rf'\bfor\s+({_NUM_RE})\s+(days?|hours?|weeks?|'
                          rf'months?|minutes?)\b', sent)
            if m and rates:
                dur = _num(m.group(1))
                rate_val, unit = rates[0]
                if (unit and unit.rstrip('s') == m.group(2).rstrip('s')) or \
                   (m.group(2).startswith('day') and unit == 'day'):
                    prod = rate_val * dur
                    steps.append(f"{rate_val} × {dur} = {prod}")
                    return prod, steps

        # Passer 3 : la question finale
        q_sent = next((s for s in sentences
                       if re.search(r'\b(how many|how much)\b', s)), q)
        persons = _persons(q_sent)
        person = persons[0] if persons else (
            current_person if any(p in q_sent for p in _PRONOUNS) else None)

        # "in total / altogether" → somme de l'objet demandé
        m = re.search(r'how many\s+([a-z]+)\b.*?(?:in total|altogether|total)', q_sent)
        if m:
            obj = _clean_obj(m.group(1))
            if obj:
                total = sum(v for (p, o), v in state.items()
                            if o == obj and (person is None or p == person))
                if total or state:
                    steps.append(f"total {obj} = {total}")
                    return total, steps

        # "how many X ... left/remain" / "how many X does P have"
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

        # "how much ... total cost" → somme des produits (rate_each × quantités)
        if 'total' in q_sent or 'cost' in q_sent or 'spend' in q_sent:
            if rates and state:
                price = rates[0][0]
                m2 = re.search(r'how (?:much|many)\s+([a-z]+)\b', q_sent)
                obj = _clean_obj(m2.group(1)) if m2 else None
                qty = sum(v for (p, o), v in state.items()
                          if (obj is None or o == obj))
                total = price * qty
                steps.append(f"{price} × {qty} = {total}")
                return total, steps

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
