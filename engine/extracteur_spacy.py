#!/usr/bin/env python3
"""
extracteur_spacy.py — Extraction de paramètres par parsing syntaxique (spaCy)
================================================================================

Remplace les heuristiques de position par un parseur de dépendances léger.
Inspiré de Hosseini et al. (2014) "Verb Categorization" pour le lexique verbal.

STACK :
  Phrase → spaCy (dépendances + lemmes)
         → lexique verbal (prior type)
         → classifieur de type (features dépendance + lexique)
         → extracteur conditionné au type (règles par type)
         → résolution de référence (pile de discours)
         → opération structurée

MESURE : accuracy par tuple (phrase, opération), pas juste par problème complet.
"""

import sys, os, re, json, time, math
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════════════════
# 1. LEXIQUE VERBAL (prior d'opération basé sur le verbe principal)
# ═══════════════════════════════════════════════════════════════════════════

# Mapping verbe → type d'opération prioritaire
VERB_LEXICON = {
    # INIT (possession, création, existence)
    'have': 'INIT', 'has': 'INIT', 'had': 'INIT',
    'own': 'INIT', 'owns': 'INIT', 'owned': 'INIT',
    'buy': 'INIT', 'buys': 'INIT', 'bought': 'INIT',
    'collect': 'INIT', 'collects': 'INIT', 'collected': 'INIT',
    'find': 'INIT', 'finds': 'INIT', 'found': 'INIT',
    'bake': 'INIT', 'bakes': 'INIT', 'baked': 'INIT',
    'make': 'INIT', 'makes': 'INIT', 'made': 'INIT',
    'produce': 'INIT', 'produces': 'INIT', 'produced': 'INIT',
    'start': 'INIT', 'starts': 'INIT', 'started': 'INIT',
    'purchase': 'INIT', 'purchases': 'INIT', 'purchased': 'INIT',
    'pack': 'INIT', 'packs': 'INIT', 'packed': 'INIT',
    'grow': 'INIT', 'grows': 'INIT', 'grew': 'INIT',
    'weigh': 'INIT', 'weighs': 'INIT', 'weighed': 'INIT',
    'harvest': 'INIT', 'harvests': 'INIT', 'harvested': 'INIT',
    'be': 'INIT',  # "there are", "there were"
    'cost': 'INIT', 'costs': 'INIT',

    # ADD (gain, acquisition, réception)
    'gain': 'ADD', 'gains': 'ADD', 'gained': 'ADD',
    'get': 'ADD', 'gets': 'ADD', 'got': 'ADD', 'gotten': 'ADD',
    'receive': 'ADD', 'receives': 'ADD', 'received': 'ADD',
    'obtain': 'ADD', 'obtains': 'ADD', 'obtained': 'ADD',
    'win': 'ADD', 'wins': 'ADD', 'won': 'ADD',
    'earn': 'ADD', 'earns': 'ADD', 'earned': 'ADD',
    'add': 'ADD', 'adds': 'ADD', 'added': 'ADD',
    'give': 'ADD', 'gives': 'ADD', 'gave': 'ADD',  # "gave X to Y" → X gains

    # SUBTRACT (perte, consommation, vente, destruction)
    'sell': 'SUBTRACT', 'sells': 'SUBTRACT', 'sold': 'SUBTRACT',
    'eat': 'SUBTRACT', 'eats': 'SUBTRACT', 'ate': 'SUBTRACT',
    'spend': 'SUBTRACT', 'spends': 'SUBTRACT', 'spent': 'SUBTRACT',
    'lose': 'SUBTRACT', 'loses': 'SUBTRACT', 'lost': 'SUBTRACT',
    'remove': 'SUBTRACT', 'removes': 'SUBTRACT', 'removed': 'SUBTRACT',
    'drop': 'SUBTRACT', 'drops': 'SUBTRACT', 'dropped': 'SUBTRACT',
    'consume': 'SUBTRACT', 'consumes': 'SUBTRACT', 'consumed': 'SUBTRACT',
    'drink': 'SUBTRACT', 'drinks': 'SUBTRACT', 'drank': 'SUBTRACT',
    'burn': 'SUBTRACT', 'burns': 'SUBTRACT', 'burned': 'SUBTRACT',
    'donate': 'SUBTRACT', 'donates': 'SUBTRACT', 'donated': 'SUBTRACT',
    'use': 'SUBTRACT', 'uses': 'SUBTRACT', 'used': 'SUBTRACT',
    'take': 'SUBTRACT', 'takes': 'SUBTRACT', 'took': 'SUBTRACT',
    'throw': 'SUBTRACT', 'throws': 'SUBTRACT', 'threw': 'SUBTRACT',
    'leave': 'SUBTRACT', 'leaves': 'SUBTRACT', 'left': 'SUBTRACT',

    # MULTIPLY / CROSS_MULT
    'contain': 'CROSS_MULT', 'contains': 'CROSS_MULT', 'contained': 'CROSS_MULT',
    'hold': 'CROSS_MULT', 'holds': 'CROSS_MULT', 'held': 'CROSS_MULT',
    'require': 'CROSS_MULT', 'requires': 'CROSS_MULT',

    # DURATION
    'work': 'DURATION', 'works': 'DURATION', 'worked': 'DURATION',

    # DIVIDE
    'split': 'DIVIDE', 'splits': 'DIVIDE',
    'divide': 'DIVIDE', 'divides': 'DIVIDE', 'divided': 'DIVIDE',
    'share': 'DIVIDE', 'shares': 'DIVIDE', 'shared': 'DIVIDE',

    # RATE
    'earn': 'RATE', 'earns': 'RATE',
    'cost': 'RATE', 'costs': 'RATE',
}


# ═══════════════════════════════════════════════════════════════════════════
# 2. PARSER spaCy + EXTRACTEUR DE PARAMÈTRES
# ═══════════════════════════════════════════════════════════════════════════

_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        try:
            _nlp = spacy.load('en_core_web_sm')
        except OSError:
            import subprocess
            subprocess.run([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'])
            _nlp = spacy.load('en_core_web_sm')
    return _nlp


@dataclass
class ParsedSentence:
    """Résultat du parsing syntaxique d'une phrase."""
    text: str
    root_verb: Optional[str] = None         # lemme du verbe principal
    nsubj: Optional[str] = None              # sujet (entité)
    dobj: Optional[str] = None               # objet direct
    pobj: Optional[str] = None               # objet prépositionnel
    nummods: List[Tuple[str, str]] = field(default_factory=list)  # (nombre, nom_parent)
    numbers: List[float] = field(default_factory=list)
    signal_words: List[str] = field(default_factory=list)


def parse_sentence(sent: str) -> ParsedSentence:
    """Parse une phrase avec spaCy et extrait les dépendances clés."""
    nlp = get_nlp()
    doc = nlp(sent)

    result = ParsedSentence(text=sent)

    for token in doc:
        # Verbe racine
        if token.dep_ == 'ROOT' and token.pos_ in ('VERB', 'AUX'):
            result.root_verb = token.lemma_.lower()

        # Sujet → entité
        if token.dep_ in ('nsubj', 'nsubjpass'):
            # Prendre le nom propre ou le nom commun
            ent_text = token.text.strip()
            if token.pos_ == 'PROPN':
                result.nsubj = ent_text
            elif result.nsubj is None:
                result.nsubj = ent_text

        # Objet direct
        if token.dep_ == 'dobj':
            result.dobj = token.text.lower()

        # Objet prépositionnel (pour "to X", "as X", "than X")
        if token.dep_ == 'pobj':
            result.pobj = token.text.lower()

        # Modifieurs numériques → (nombre, nom qualifié)
        if token.dep_ == 'nummod':
            head = token.head.text.lower()
            # Ne garder que les vrais nombres (pas "one", "two"...)
            if re.match(r'^\d+(\.\d+)?$', token.text):
                result.nummods.append((token.text, head))

        # Signal words
        if token.lemma_.lower() in ('each', 'every', 'per', 'times',
                                     'twice', 'double', 'triple',
                                     'split', 'divided', 'shared', 'among',
                                     'more', 'less', 'fewer', 'left',
                                     'additional', 'also', 'another'):
            result.signal_words.append(token.lemma_.lower())

    # Extraire tous les nombres
    result.numbers = [float(m.group(1)) for m in re.finditer(
        r'\b(\d+(?:\.\d+)?)\b', sent)]

    # Signal words détectés dans le texte brut (expressions multi-mots,
    # mots que spaCy tokenise mal comme 'times' → 'time')
    raw_lower = sent.lower()
    for phrase, keyword in [
        ('times as many', 'times'), ('times as much', 'times'),
        ('twice', 'twice'), ('double', 'double'), ('triple', 'triple'),
        ('split into', 'split'), ('divided equally', 'divided'),
        ('shared equally', 'shared'), ('cut into', 'cut'),
        ('are sold', 'sold'), ('were sold', 'sold'),
    ]:
        if phrase in raw_lower and keyword not in result.signal_words:
            result.signal_words.append(keyword)

    return result


# Normalisation des noms de types entre l'extracteur et la référence
TYPE_ALIASES = {
    'MULTIPLY': 'MULT',
    'CROSS_MULT': 'MULT',
    'TIMES_AS_MANY': 'MULT',
    'ADD': 'GAIN',
    'SUBTRACT': 'LOSE',
    'DIVIDE': 'DIV',
    'RATE': 'RATE',
    'DURATION': 'MULT',
    'INIT': 'HAS',
}

def normaliser_type(t: str) -> str:
    return TYPE_ALIASES.get(t, t)

def classify_operation(parsed: ParsedSentence, discourse_state: dict) -> str:
    """
    Classifie le type d'opération à partir du parse syntaxique.

    Priorité :
      1. Signal words (force maximale)
      2. Verbe principal (lexique)
      3. Contexte du discours (dernière opération)
    """
    sw = parsed.signal_words

    # 1. Signal words
    if 'times' in sw or 'twice' in sw or 'double' in sw or 'triple' in sw:
        return 'MULTIPLY'
    if 'each' in sw or 'every' in sw:
        return 'CROSS_MULT'
    if 'per' in sw and parsed.root_verb in ('earn', 'earns', 'cost', 'costs', 'make', 'makes'):
        return 'RATE'
    if 'split' in sw or 'divided' in sw or 'shared' in sw or 'among' in sw:
        return 'DIVIDE'
    if 'cut' in sw:
        return 'INIT'  # "cut into N slices" → initialisation
    if 'sold' in sw:
        return 'SUBTRACT'
    if 'left' in sw or 'remain' in sw:
        return 'SUBTRACT'
    if 'more' in sw or 'additional' in sw or 'also' in sw or 'another' in sw:
        return 'ADD'

    # 2. Construction existentielle
    if parsed.root_verb == 'be' and 'there' in parsed.text.lower():
        return 'INIT'

    # 2. Verbe principal
    if parsed.root_verb:
        verb_op = VERB_LEXICON.get(parsed.root_verb)
        if verb_op:
            return verb_op

    # 3. Contexte
    if not discourse_state.get('has_init'):
        return 'INIT'

    return 'ADD'  # fallback


# ═══════════════════════════════════════════════════════════════════════════
# 4. EXTRACTEUR DE PARAMÈTRES CONDITIONNÉ AU TYPE
# ═══════════════════════════════════════════════════════════════════════════

def extract_params(parsed: ParsedSentence, op_type: str,
                   discourse: dict) -> dict:
    """
    Extrait les paramètres selon le type d'opération.

    Chaque type a des RÈGLES SPÉCIFIQUES pour extraire
    entity, object, value, multiplier, etc.
    """
    params = {'type': op_type}

    # ── Résolution d'entité ──
    entity = None
    # 1. Sujet syntaxique (nsubj) — sauf si c'est un nombre (passif : "45 are sold")
    if parsed.nsubj:
        ent = parsed.nsubj.lower()
        # Filtrer les pronoms → utiliser l'entité du discours
        if ent in ('he', 'she', 'they', 'it', 'i', 'we', 'him', 'her', 'them'):
            entity = discourse.get('last_entity')
        # Si le sujet est un nombre, c'est un passif → utiliser last_entity
        elif re.match(r'^\d+(\.\d+)?$', ent):
            entity = discourse.get('last_entity')
        else:
            entity = ent
    # 2. Construction existentielle ("There are N X") → utiliser last_entity
    if entity is None and 'there' in parsed.text.lower():
        entity = discourse.get('last_entity', 'someone')
    # 3. Fallback
    if entity is None:
        entity = discourse.get('last_entity', 'someone')

    params['entity'] = entity

    # ── Résolution d'objet ──
    obj = None
    # 1. Objet direct (dobj) — sauf si c'est un signal word ("more", "many"...)
    if parsed.dobj:
        if parsed.dobj.lower() not in ('more', 'many', 'much', 'fewer', 'less',
                                        'times', 'each', 'every', 'all', 'some'):
            obj = parsed.dobj
    # 2. Premier nummod → le nom modifié est probablement l'objet
    if obj is None and parsed.nummods:
        obj = parsed.nummods[0][1]
    # 3. Objet prépositionnel (pobj) — ex: "split into groups"
    if obj is None and parsed.pobj:
        if parsed.pobj.lower() not in ('hour', 'hours', 'day', 'days', 'week', 'weeks',
                                        'month', 'months', 'year', 'years'):
            obj = parsed.pobj
    # 4. Fallback : dernier objet du discours
    if obj is None:
        obj = discourse.get('last_object')

    params['object'] = obj

    # ── Extraction par type ──
    numbers = parsed.numbers

    if op_type == 'INIT':
        # Premier nombre = valeur
        params['value'] = numbers[0] if numbers else None

    elif op_type == 'ADD':
        # Premier nombre = valeur à ajouter
        params['value'] = numbers[0] if numbers else None

    elif op_type == 'SUBTRACT':
        # Premier nombre = valeur à soustraire
        params['value'] = numbers[0] if numbers else None

    elif op_type == 'MULTIPLY':
        # Premier nombre = multiplicateur (ex: "3 times as many")
        params['multiplier'] = numbers[0] if numbers else None
        # Chercher l'entité de référence (autre entité avec même objet)
        params['reference_entity'] = discourse.get('other_entity')

    elif op_type == 'CROSS_MULT':
        # "Each box has 5 pencils" → container, per_unit, product
        if parsed.nummods and re.match(r'^\d+', parsed.nummods[0][0]):
            params['per_unit'] = float(parsed.nummods[0][0])
            params['product'] = parsed.nummods[0][1]
        params['container'] = parsed.nsubj
        params['container_count'] = discourse.get('container_counts', {}).get(
            (params.get('container') or '').lower())

    elif op_type == 'RATE':
        params['rate'] = numbers[0] if numbers else None

    elif op_type == 'DURATION':
        params['duration'] = numbers[0] if numbers else None
        params['rate_entity'] = entity  # l'entité dont on multiplie le taux

    elif op_type == 'DIVIDE':
        params['divisor'] = numbers[0] if numbers else None

    return params


# ═══════════════════════════════════════════════════════════════════════════
# 5. ÉTAT DE DISCOURS (pile de coréférence)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class DiscourseState:
    """État de discours pour la résolution de coréférence."""
    last_entity: Optional[str] = None
    last_object: Optional[str] = None
    entities: List[str] = field(default_factory=list)       # toutes les entités vues
    objects: Dict[str, float] = field(default_factory=dict)  # objet → dernière valeur
    container_counts: Dict[str, float] = field(default_factory=dict)  # conteneur → compte
    has_init: bool = False

    def update(self, params: dict):
        """Met à jour l'état après une opération."""
        ent = params.get('entity')
        obj = params.get('object')

        if ent and ent not in self.entities:
            self.entities.append(ent)
        if ent:
            self.last_entity = ent
        if obj:
            self.last_object = obj
            val = params.get('value') or params.get('per_unit')
            if val is not None:
                self.objects[obj] = float(val)

        self.has_init = True

        # Si l'opération est THERE_ARE ou CROSS_MULT, stocker le compte du conteneur
        if params['type'] in ('INIT', 'CROSS_MULT'):
            container = params.get('container')
            if container:
                count = params.get('container_count') or params.get('value')
                if count is not None:
                    self.container_counts[container.lower()] = float(count)

    def get_other_entity(self, obj: str, current_entity: str) -> Optional[str]:
        """Trouve une autre entité qui possède le même objet."""
        for e in self.entities:
            if e != current_entity:
                return e
        return None

    def to_dict(self):
        return {
            'last_entity': self.last_entity,
            'last_object': self.last_object,
            'has_init': self.has_init,
            'container_counts': self.container_counts,
            'other_entity': self.get_other_entity(
                self.last_object or '', self.last_entity or ''),
        }


# ═══════════════════════════════════════════════════════════════════════════
# 6. PIPELINE COMPLET : PHRASE → OPÉRATION STRUCTURÉE
# ═══════════════════════════════════════════════════════════════════════════

class SpacyExtractor:
    """Extracteur de paramètres basé sur spaCy + lexique verbal + discours."""

    def __init__(self):
        self.nlp = get_nlp()
        self.discourse = DiscourseState()

    def extract(self, sent: str) -> Optional[dict]:
        """Extrait l'opération structurée d'une phrase."""
        # 1. PARSING
        parsed = parse_sentence(sent)

        # Ignorer les phrases sans nombre
        if not parsed.numbers and not parsed.signal_words:
            return None

        # 2. CLASSIFICATION DU TYPE
        op_type = classify_operation(parsed, self.discourse.to_dict())

        # 3. EXTRACTION DES PARAMÈTRES
        params = extract_params(parsed, op_type, self.discourse.to_dict())

        # 4. MISE À JOUR DU DISCOURS
        self.discourse.update(params)

        return params

    def reset(self):
        self.discourse = DiscourseState()


# ═══════════════════════════════════════════════════════════════════════════
# 7. MESURE PAR TUPLE (accuracy sur paires phrase→opération)
# ═══════════════════════════════════════════════════════════════════════════

def mesurer_accuracy_par_tuple(test_problems: List[dict]) -> dict:
    """
    Mesure l'accuracy PAR TUPLE (phrase, opération), pas par problème.

    Pour chaque phrase de chaque problème, on compare l'opération extraite
    avec l'opération de référence (déduite des annotations <<...>>).
    """
    from extraire_grammaire import (
        extraire_operations, aligner_operation_phrase, classer_operation
    )

    extractor = SpacyExtractor()
    stats = {
        'total_phrases': 0,
        'type_correct': 0,
        'entity_correct': 0,
        'object_correct': 0,
        'value_correct': 0,
        'full_correct': 0,
        'errors': [],
    }

    for p in test_problems:
        question = p.get('question', '')
        answer = p.get('answer', '')

        ops = extraire_operations(answer)
        if not ops:
            continue

        sentences = re.split(r'(?<=[.;!?])\s+', question.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        extractor.reset()
        total_ops = len(ops)

        for i, (sym, a, b, result) in enumerate(ops):
            ref_phrase = aligner_operation_phrase(
                (sym, a, b, result), sentences, i, total_ops)
            if ref_phrase is None:
                continue

            ref_type = classer_operation(sym, a, b, result, ref_phrase)

            # Extraire avec spaCy
            extracted = extractor.extract(ref_phrase)
            if extracted is None:
                stats['total_phrases'] += 1
                continue

            stats['total_phrases'] += 1

            # Comparer le type (normalisé)
            type_ok = (normaliser_type(extracted['type']) == normaliser_type(ref_type))
            if type_ok:
                stats['type_correct'] += 1

            # Vérifier la valeur (premier nombre extrait = opérande)
            extracted_val = (extracted.get('value') or
                           extracted.get('multiplier') or
                           extracted.get('per_unit') or
                           extracted.get('rate') or
                           extracted.get('duration') or
                           extracted.get('divisor'))

            value_ok = (extracted_val is not None and
                       abs(extracted_val - b) < 1e-6)
            if value_ok:
                stats['value_correct'] += 1

            # Vérifier l'entité (comparaison approximative)
            entity_ok = (extracted.get('entity') is not None)
            if entity_ok:
                stats['entity_correct'] += 1

            # Vérifier l'objet
            obj_ok = (extracted.get('object') is not None)
            if obj_ok:
                stats['object_correct'] += 1

            if type_ok and value_ok:
                stats['full_correct'] += 1

            if not type_ok:
                stats['errors'].append({
                    'phrase': ref_phrase[:80],
                    'ref_type': ref_type,
                    'extracted_type': extracted['type'],
                    'ref_value': b,
                    'extracted_value': extracted_val,
                })

    n = stats['total_phrases']
    if n > 0:
        print(f"\n═══ ACCURACY PAR TUPLE (phrase→opération) ═══")
        print(f"  Total phrases évaluées : {n}")
        print(f"  Type d'opération       : {100*stats['type_correct']/n:.1f}%")
        print(f"  Valeur extraite        : {100*stats['value_correct']/n:.1f}%")
        print(f"  Entité présente        : {100*stats['entity_correct']/n:.1f}%")
        print(f"  Objet présent          : {100*stats['object_correct']/n:.1f}%")
        print(f"  Type + Valeur OK       : {100*stats['full_correct']/n:.1f}%")

        # Afficher les erreurs de type les plus fréquentes
        if stats['errors']:
            error_counter = Counter(
                f"{e['ref_type']}→{e['extracted_type']}" for e in stats['errors'])
            print(f"\n  Erreurs de type fréquentes :")
            for err, count in error_counter.most_common(10):
                print(f"    {err:<25s} ×{count}")

    return stats


# ═══════════════════════════════════════════════════════════════════════════
# 8. DÉMO + TEST
# ═══════════════════════════════════════════════════════════════════════════

def demo():
    """Démo sur quelques phrases."""
    print("═══ DÉMO EXTRACTEUR spaCy ═══\n")

    extractor = SpacyExtractor()

    tests = [
        "John has 5 apples.",
        "He buys 3 more.",
        "She ate 4 cookies.",
        "Mary has 3 times as many.",
        "There are 6 boxes.",
        "Each box has 5 pencils.",
        "James earns 20 dollars per hour.",
        "He works 8 hours.",
        "They are split into 4 equal groups.",
        "A pizza is cut into 8 slices.",
        "John eats 3 slices.",
        "45 are sold.",
        "Mary gave him 3 more apples.",
    ]

    for sent in tests:
        parsed = parse_sentence(sent)
        op_type = classify_operation(parsed, extractor.discourse.to_dict())
        params = extract_params(parsed, op_type, extractor.discourse.to_dict())
        extractor.discourse.update(params)

        print(f"  '{sent}'")
        print(f"    nsubj={parsed.nsubj}, dobj={parsed.dobj}, pobj={parsed.pobj}")
        print(f"    root_verb={parsed.root_verb}, nummods={parsed.nummods}")
        print(f"    signal_words={parsed.signal_words}")
        print(f"    → {op_type} : {params}")
        print()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--demo', action='store_true')
    p.add_argument('--measure', action='store_true',
                   help='Mesurer accuracy par tuple sur le test set')
    args = p.parse_args()

    if args.demo or not args.measure:
        demo()

    if args.measure:
        from structure_retrieval import StructuredRetrieval
        print("Chargement du test set...")
        sr = StructuredRetrieval()
        sr.split_and_index()
        mesurer_accuracy_par_tuple(sr._test_problems)
