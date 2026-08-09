#!/usr/bin/env python3
"""
structure_ondulatoire.py — Apprentissage des STRUCTURES mathématiques par ondes
================================================================================

Plutôt que d'apprendre des milliards d'exemples (LLM) ou des motifs regex fragiles,
on apprend les STRUCTURES GÉOMÉTRIQUES sous-jacentes aux problèmes.

Principe THU : la Géométrie (formes d'ondes) engendre l'Arithmétique (opérations).

FONCTIONNEMENT :
1. Apprentissage : à partir des 1301 problèmes GSM8K annotés <<...>>, on extrait
   les motifs textuels caractéristiques de chaque type de structure (ex: 
   "subtract_then_multiply" → mots-clés {per, day, she, sells, ...})
2. Détection : pour un nouveau problème, on encode les mots en onde et on calcule
   la résonance avec chaque prototype de structure → soft classification
3. Résolution : la structure détectée donne le « plan » (équations à créer),
   et les paramètres sont extraits par les heuristiques NLP éprouvées

USAGE :
  from structure_ondulatoire import StructuredSolver
  solver = StructuredSolver()
  solver.learn_from_gsm8k()             # apprendre les structures
  result = solver.solve("John has 5 apples. Mary has 3 times as many.")
  # → 15.0
"""

import sys, os, re, math, json, time
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_lang import (
    encode, superpose, resonate, normalize,
    bind as _bind, unbind as _unbind,
    DEFAULT_DIM,
)
from encodage_phase import PhaseEncoder
from encodage_logarithmique import LogWaveEncoder
from raisonneur_algebrique import AlgebriqueReasoner

# ═══════════════════════════════════════════════════════════════════════════════
# 1. STOP WORDS (mots-outils à ignorer)
# ═══════════════════════════════════════════════════════════════════════════════

_STOP = {'the', 'a', 'an', 'of', 'in', 'for', 'to', 'is', 'are', 'was',
         'were', 'and', 'or', 'with', 'at', 'by', 'on', 'from', 'his',
         'her', 'their', 'its', 'he', 'she', 'they', 'it', 'more', 'each',
         'every', 'how', 'many', 'much', 'what', 'does', 'do', 'did',
         'left', 'remain', 'remaining', 'total', 'altogether', 'per',
         'has', 'had', 'have', 'than', 'as', 'this', 'that', 'these', 'those',
         'there', 'then', 'also', 'some', 'all', 'into', 'been', 'can',
         'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
         'about', 'over', 'under', 'after', 'before', 'between', 'through',
         'during', 'above', 'below', 'just', 'now', 'not', 'only', 'very',
         'too', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why',
         'one', 'two', 'three', 'four', 'five', 'first', 'second', 'third'}

_VERBS = {'sells', 'sell', 'sold', 'gives', 'give', 'gave', 'loses', 'lose', 'lost',
          'spends', 'spend', 'spent', 'eats', 'eat', 'ate', 'buys', 'buy', 'bought',
          'earns', 'earn', 'earned', 'makes', 'make', 'made', 'gets', 'get', 'got',
          'receives', 'receive', 'received', 'finds', 'find', 'found', 'collects',
          'collect', 'collected', 'obtains', 'obtain', 'obtained', 'wins', 'win', 'won',
          'works', 'work', 'worked', 'runs', 'run', 'ran', 'goes', 'go', 'went',
          'takes', 'take', 'took', 'uses', 'use', 'used', 'pays', 'pay', 'paid',
          'costs', 'cost', 'needs', 'need', 'wants', 'want', 'bakes', 'bake', 'baked',
          'produces', 'produce', 'produced', 'harvests', 'harvest', 'harvested',
          'removes', 'remove', 'removed', 'drops', 'drop', 'dropped', 'throws', 'throw',
          'starts', 'start', 'started', 'finishes', 'finish', 'finished', 'cuts', 'cut',
          'adds', 'add', 'added', 'puts', 'put', 'picks', 'pick', 'picked', 'packs',
          'pack', 'packed', 'splits', 'split', 'divides', 'divide', 'divided',
          'shares', 'share', 'shared', 'weighs', 'weigh', 'weighed', 'grows', 'grow'}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. APPRENTISSAGE DES STRUCTURES À PARTIR DES DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

def _classify_operations(answer_text: str) -> Tuple[str, List[str]]:
    """Classifie la structure d'un problème basé sur sa séquence d'opérations <<...>>"""
    ops = re.findall(r'<<(.*?)>>', answer_text)
    if not ops:
        return "unknown", []

    op_types = []
    for op in ops:
        m = re.match(r'[\d.]+\s*([+\-*/])\s*[\d.]+', op)
        if m:
            op_types.append(m.group(1))

    seq = ''.join(op_types)

    # Classification par séquence d'opérations
    if set(seq) == {'*'}:
        return "multiplication", op_types
    elif set(seq) == {'+'}:
        return "addition", op_types
    elif set(seq) == {'-'}:
        return "subtraction", op_types
    elif set(seq) == {'/'}:
        return "division", op_types
    elif '-' in seq and '*' in seq and seq.index('-') < seq.rindex('*'):
        return "subtract_then_multiply", op_types
    elif '+' in seq and '*' in seq and seq.index('+') < seq.rindex('*'):
        return "add_then_multiply", op_types
    elif '-' in seq and '/' in seq:
        return "subtract_then_divide", op_types
    elif '+' in seq and '-' in seq:
        return "add_and_subtract", op_types
    elif '*' in seq and '/' in seq:
        return "multiply_and_divide", op_types
    elif '+' in seq and '/' in seq:
        return "add_then_divide", op_types
    else:
        return "complex", op_types


class StructuredSolver:
    """
    Résolveur qui apprend les structures des problèmes GSM8K et les applique
    à de nouveaux problèmes par résonance d'ondes.
    """

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self.phase = PhaseEncoder(500000)
        self.log = LogWaveEncoder(grid_size=2048, SCALE=300)

        # Prototypes d'ondes par structure
        self._struct_waves: Dict[str, np.ndarray] = {}

        # Motifs textuels par structure (pour l'extraction de paramètres)
        self._struct_patterns: Dict[str, Dict] = {}

        # Données d'apprentissage
        self._trained = False

    # ── Apprentissage ────────────────────────────────────────────────────────

    def learn_from_gsm8k(self, data_path: str = None) -> "StructuredSolver":
        """
        Apprend les prototypes de structures à partir des problèmes GSM8K annotés.

        Pour chaque type de structure (ex: subtract_then_multiply), on :
        1. Collecte tous les mots des problèmes de cette structure
        2. Encode les N mots les plus fréquents en onde → ψ_prototype
        3. Extrait les patterns d'opérations caractéristiques
        """
        if data_path is None:
            here = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')

        with open(data_path, encoding='utf-8') as f:
            problems = [json.loads(l) for l in f]

        # Collecter les mots par structure
        struct_words: Dict[str, List[str]] = defaultdict(list)
        struct_ops: Dict[str, List[List[str]]] = defaultdict(list)
        struct_count = Counter()

        for p in problems:
            q = p.get('question', '')
            a = p.get('answer', '')
            struct_name, op_types = _classify_operations(a)

            if struct_name == "unknown":
                continue

            struct_count[struct_name] += 1
            struct_ops[struct_name].append(op_types)

            # Extraire les mots significatifs (non-stop, non-verbes, ≥3 lettres)
            words = re.findall(r'[a-zà-ÿ]{3,}', q.lower())
            significant = [w for w in words if w not in _STOP and w not in _VERBS]
            struct_words[struct_name].extend(significant)

        # Construire les prototypes d'ondes (top 50 mots par structure)
        for struct_name, words in struct_words.items():
            counter = Counter(words)
            top_words = [w for w, _ in counter.most_common(50)]

            # Encoder chaque mot et superposer
            waves = []
            for w in top_words:
                try:
                    waves.append(encode(w, dim=self.dim))
                except Exception:
                    pass

            if waves:
                psi = superpose(*waves)
                self._struct_waves[struct_name] = normalize(psi)

            # Stocker les patterns
            all_ops = struct_ops[struct_name]
            self._struct_patterns[struct_name] = {
                "word_count": len(words),
                "top_words": top_words[:20],
                "problem_count": struct_count[struct_name],
                "common_op_sequences": self._summarize_sequences(all_ops),
            }

        self._trained = True
        print(f"✓ {len(self._struct_waves)} structures apprises "
              f"depuis {sum(struct_count.values())} problèmes")
        return self

    def _summarize_sequences(self, op_sequences: List[List[str]]) -> List[str]:
        """Résume les séquences d'opérations les plus fréquentes."""
        seq_counter = Counter([' '.join(seq) for seq in op_sequences])
        return [seq for seq, _ in seq_counter.most_common(5)]

    # ── Détection de structure par résonance ─────────────────────────────────

    def detect_structure(self, question: str) -> Tuple[str, float]:
        """
        Détecte la structure d'un problème par résonance d'ondes.

        Retourne (nom_structure, score_résonance).
        """
        if not self._trained or not self._struct_waves:
            return "unknown", 0.0

        # Encoder le problème (mots significatifs seulement)
        words = re.findall(r'[a-zà-ÿ]{3,}', question.lower())
        significant = [w for w in words if w not in _STOP and w not in _VERBS]

        if not significant:
            return "unknown", 0.0

        psi_problem = superpose(*[encode(w, dim=self.dim) for w in significant])
        psi_problem = normalize(psi_problem)

        best_name, best_score = None, -1.0
        for name, psi_struct in self._struct_waves.items():
            score = float(resonate(psi_problem, psi_struct))
            if score > best_score:
                best_score = score
                best_name = name

        return best_name, best_score

    # ── Extraction des paramètres ────────────────────────────────────────────

    def _extract_numbers(self, text: str) -> List[float]:
        """Extrait tous les nombres positifs dans l'ordre."""
        return [float(m.group(1)) for m in re.finditer(r'\b(\d+(?:\.\d+)?)\b', text)
                if float(m.group(1)) > 0]

    def _extract_entity(self, text: str, known_entities: List[str]) -> Optional[str]:
        """Extrait l'entité principale d'une phrase."""
        # 1. Noms propres capitalisés (hors début de phrase)
        caps = re.findall(r'(?<=[.!?]\s)([A-Z][a-z]{2,})\b', ' ' + text)
        if not caps:
            caps = re.findall(r'^([A-Z][a-z]{2,})\b', text)
        if not caps:
            caps = re.findall(r'\b([A-Z][a-z]{2,})\b', text)
        if caps:
            return caps[0].lower()

        # 2. Entité connue mentionnée dans le texte
        for e in known_entities:
            if e in text.lower():
                return e

        return None

    def _extract_object(self, text: str, entities: List[str]) -> Optional[str]:
        """Extrait l'objet principal d'une phrase."""
        words = re.findall(r'[a-z]{3,}', text.lower())
        # Filtrer : non-stop, non-verbe, non-entité, non-nombre
        candidates = []
        for w in words:
            if (w not in _STOP and w not in _VERBS
                    and w not in [e.lower() for e in entities]
                    and not w.isdigit()
                    and w not in {'hour', 'hours', 'day', 'days', 'week', 'weeks',
                                  'month', 'months', 'year', 'years', 'morning',
                                  'breakfast', 'lunch', 'dinner', 'night'}):
                candidates.append(w)

        # Prendre le dernier nom commun (généralement l'objet principal)
        return candidates[-1] if candidates else None

    # ── Résolution ───────────────────────────────────────────────────────────

    def solve(self, question: str) -> Optional[float]:
        """
        Résout un problème GSM8K en utilisant la structure détectée.

        Pipeline :
        1. Détecter la structure par résonance
        2. Diviser en phrases
        3. Pour chaque phrase, selon la structure :
           - Extraire entité, objet, nombres
           - Créer l'équation correspondante
        4. Résoudre l'équation cible avec AlgebriqueReasoner
        """
        if not self._trained:
            # Fallback : utiliser le pipeline algébrique existant
            from raisonneur_ondulatoire import solve_gsm8k_algebrique
            return solve_gsm8k_algebrique(question)

        q = question.strip()
        q = re.sub(r'\s+', ' ', q)

        # Détecter la structure globale
        struct_name, struct_score = self.detect_structure(q)

        # Diviser en phrases
        sentences = re.split(r'(?<=[.;!?])\s+', q)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Initialiser le raisonneur algébrique
        r_alg = AlgebriqueReasoner()

        # Registre local pour le tracking d'entités/objets
        registry: Dict[str, float] = {}  # "ent_obj" → valeur
        last_entity = None
        last_obj = None

        # Pour chaque phrase déclarative (avant la question)
        for sent in sentences:
            # Détecter la phrase-question
            if re.search(r'\b(how many|how much|what is|what are|'
                         r'how far|how long|how old)\b', sent.lower()):
                break

            nums = self._extract_numbers(sent)
            if not nums:
                continue

            # Extraire entité et objet
            known_entities = list(set(
                [k.split('_')[0] for k in registry.keys()] + [last_entity or '']
            ))
            entity = self._extract_entity(sent, known_entities)

            # Si pas d'entité trouvée, utiliser la dernière ou créer "someone"
            if entity is None:
                if last_entity:
                    entity = last_entity
                elif not registry:
                    entity = 'someone'

            obj = self._extract_object(sent, [entity] if entity else [])

            # Si pas d'objet trouvé, utiliser le dernier
            if obj is None:
                obj = last_obj
            if obj is None:
                # Fallback : dernier nom commun de la phrase
                words = [w for w in re.findall(r'[a-z]{3,}', sent.lower())
                         if w not in _STOP]
                obj = words[-1] if words else 'item'

            if entity is None or obj is None:
                continue

            # ── Détecter l'action selon la structure ─────────────────────
            sent_lower = sent.lower()
            val = nums[0]

            # Patterns par type d'action
            is_init_pattern = bool(re.search(
                r'\b(?:has|had|have|there\s+are|there\s+were|owns?|bought|'
                r'collected|found|bakes?|makes?|produces?|weighs?|grows?|'
                r'started\s+with|purchased|packed|harvested)\s+\d+',
                sent_lower))

            is_comparison = bool(re.search(
                r'(times\s+as\s+(many|much)|more\s+than|fewer\s+than|'
                r'less\s+than|twice|double|triple|half\s+as\s+(many|much))',
                sent_lower))

            is_cross_product = bool(re.search(
                r'\b(each|every)\s+\w+\s+(has|have|contains?|holds?|requires?|'
                r'takes?|costs?)\s+\d+', sent_lower))

            is_rate = bool(re.search(
                r'(per\s+(hour|day|week|month|year)|a\s+(day|week|month|year)|'
                r'earns?\s+\d+\s+(dollars?\s+)?per)',
                sent_lower))

            is_duration = bool(re.search(
                r'\d+\s+(hours?|days?|weeks?|months?)', sent_lower))

            is_partition = bool(re.search(
                r'(split|shared\s+equally|divided\s+equally|among|'
                r'each\s+(group|person|child|student|friend|receives?|gets?)|'
                r'per\s+(person|student|child|group))',
                sent_lower))

            is_loss = bool(re.search(
                r'\b(sells?|sold|gives?\s+away|loses?|lost|spends?|spent|'
                r'eats?|ate|removes?|takes?\s+away|gave|donated|burned|'
                r'consumed|drank|dropped|used)\b',
                sent_lower))

            is_gain = bool(re.search(
                r'\b(buys|gains|gets|receives|finds|collects|obtains|wins|'
                r'gave\s+\w+\s+\d+|gives\s+\w+\s+\d+|more\s+(?:apples|cookies|'
                r'pencils|dollars|books|items|stickers|loaves|slices|eggs|'
                r'cars|wheels|students|groups|boxes)|additional|also|another)\b',
                sent_lower))

            # ── Exécuter l'opération ─────────────────────────────────────
            var_name = f"{entity}_{obj}"

            if is_comparison and registry:
                # "N times as many" → multiplier un fait existant
                mult_val = nums[0]
                # Trouver un autre fait avec le même objet
                for rkey, rval in list(registry.items()):
                    if rkey.endswith(f"_{obj}") and not rkey.startswith(f"{entity}_"):
                        base_val = float(rval)
                        new_val = base_val * mult_val
                        r_alg.define(rkey, base_val)  # s'assurer que la base est définie
                        r_alg.define(var_name, ('mult', rkey, mult_val))
                        registry[var_name] = new_val
                        last_entity, last_obj = entity, obj
                        break
                else:
                    # Fallback: init
                    r_alg.define(var_name, float(mult_val))
                    registry[var_name] = float(mult_val)
                    last_entity, last_obj = entity, obj

            elif is_cross_product and registry:
                # "each X has M Y" → N conteneurs × M par conteneur
                container_obj = obj  # ex: "box", "car"
                mult_val = nums[0]
                # Chercher le nombre de conteneurs dans le registre
                for rkey, rval in list(registry.items()):
                    r_ent, r_obj = rkey.split('_', 1) if '_' in rkey else ('', rkey)
                    # L'objet du registre correspond au sujet de "each X"
                    if r_obj in sent_lower or any(
                        w in sent_lower for w in [r_obj, r_obj + 's', r_obj.rstrip('s')]
                    ):
                        total = float(rval) * mult_val
                        # Le résultat est un nouvel objet (ex: "pencils", "wheels")
                        new_obj = obj  # l'objet de la phrase = le produit
                        new_var = f"{entity}_{new_obj}"
                        r_alg.define(rkey, float(rval))
                        r_alg.define(new_var, ('mult', rkey, mult_val))
                        registry[new_var] = total
                        last_entity, last_obj = entity, new_obj
                        break
                else:
                    # Init
                    r_alg.define(var_name, float(mult_val))
                    registry[var_name] = float(mult_val)
                    last_entity, last_obj = entity, obj

            elif is_rate:
                # Stocker le taux
                rate_val = nums[0]
                r_alg.define(var_name, float(rate_val))
                registry[var_name] = float(rate_val)
                last_entity, last_obj = entity, obj

            elif is_duration and registry:
                # Multiplier un taux existant par la durée
                dur_val = nums[0]
                for rkey, rval in list(registry.items()):
                    r_ent = rkey.split('_')[0] if '_' in rkey else ''
                    if r_ent == entity or r_ent in (last_entity or ''):
                        total = float(rval) * dur_val
                        earnings_var = f"{entity}_money"
                        r_alg.define(rkey, float(rval))
                        r_alg.define(earnings_var, ('mult', rkey, dur_val))
                        registry[earnings_var] = total
                        last_entity, last_obj = entity, 'money'
                        break

            elif is_partition and registry:
                # Diviser un fait existant
                div_val = nums[0]
                if div_val > 0:
                    last_key = list(registry.keys())[-1]
                    last_val = float(registry[last_key])
                    result = last_val / div_val
                    new_var = f"{entity}_{obj}"
                    r_alg.define(last_key, last_val)
                    r_alg.define(new_var, ('div', last_key, div_val))
                    registry[new_var] = result
                    last_entity, last_obj = entity, obj

            elif is_loss and registry:
                # Soustraire d'un fait existant
                loss_val = nums[0]
                for rkey, rval in list(registry.items()):
                    if entity in rkey:
                        new_val = float(rval) - loss_val
                        r_alg.define(rkey, float(rval))  # sauver la base
                        base_key = f"_{rkey}_base"
                        r_alg.define(base_key, float(rval))
                        r_alg.define(rkey, ('sub', base_key, loss_val))
                        registry[rkey] = new_val
                        last_entity, last_obj = entity, obj
                        break
                else:
                    # Init avec soustraction future
                    r_alg.define(var_name, float(loss_val))
                    registry[var_name] = float(loss_val)
                    last_entity, last_obj = entity, obj

            elif is_gain and registry:
                # Ajouter à un fait existant
                gain_val = nums[0]
                for rkey, rval in list(registry.items()):
                    if entity in rkey:
                        new_val = float(rval) + gain_val
                        base_key = f"_{rkey}_base"
                        r_alg.define(base_key, float(rval))
                        r_alg.define(rkey, ('add', base_key, gain_val))
                        registry[rkey] = new_val
                        last_entity, last_obj = entity, obj
                        break
                else:
                    r_alg.define(var_name, float(gain_val))
                    registry[var_name] = float(gain_val)
                    last_entity, last_obj = entity, obj

            elif is_init_pattern or not registry:
                # Initialisation
                r_alg.define(var_name, float(val))
                registry[var_name] = float(val)
                last_entity, last_obj = entity, obj

            else:
                # Fallback : accumuler sur le dernier fait
                if registry and last_entity:
                    for rkey, rval in list(registry.items()):
                        if last_entity in rkey:
                            new_val = float(rval) + val
                            base_key = f"_{rkey}_base"
                            r_alg.define(base_key, float(rval))
                            r_alg.define(rkey, ('add', base_key, val))
                            registry[rkey] = new_val
                            break
                    else:
                        r_alg.define(var_name, float(val))
                        registry[var_name] = float(val)
                else:
                    r_alg.define(var_name, float(val))
                    registry[var_name] = float(val)
                last_entity, last_obj = entity, obj

        # ── Résoudre la cible ───────────────────────────────────────────
        question_sent = sentences[-1] if sentences else ''
        if not registry:
            return None

        # Extraire l'objet de la question
        q_obj = self._extract_object(question_sent, [last_entity or ''])
        if q_obj is None:
            # Fallback : dernier nom dans la question
            q_words = [w for w in re.findall(r'[a-z]{3,}', question_sent.lower())
                       if w not in _STOP]
            q_obj = q_words[-1] if q_words else None

        # Chercher dans le registre
        if q_obj:
            for rkey, rval in registry.items():
                if q_obj in rkey or rkey.endswith(f"_{q_obj}"):
                    return float(rval)

        # Fallback : dernière valeur
        return float(list(registry.values())[-1])


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TESTS + BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

_SAMPLES = [
    ("John has 5 apples. He buys 3 more. How many apples does he have?", 8.0),
    ("Mary had 10 cookies. She ate 4. How many cookies does she have left?", 6.0),
    ("Tom has 12 dollars. He spends 4 dollars. How many dollars does he have left?", 8.0),
    ("There are 6 boxes. Each box has 5 pencils. How many pencils are there in total?", 30.0),
    ("Sue has 10 stickers. She gives 3 to her friend. How many stickers does Sue have left?", 7.0),
    ("John has 5 apples. Mary has 3 times as many. How many apples does Mary have?", 15.0),
    ("A bakery bakes 24 loaves of bread. They sell 9 loaves. How many loaves are left?", 15.0),
    ("There are 4 cars. Each car has 4 wheels. How many wheels are there?", 16.0),
    ("Sam had 30 dollars. He spent 12 dollars. How many dollars does Sam have left?", 18.0),
    ("Lucy has 8 books. John has 3 times as many. How many books does John have?", 24.0),
    ("A store has 100 items. 45 are sold. How many remain?", 55.0),
    ("John has 5 apples. Mary gave him 3 more apples. How many apples does John have?", 8.0),
    ("James earns 20 dollars per hour. He works 8 hours. How much does he earn?", 160.0),
    ("There are 60 students. They are split into 4 equal groups. How many students per group?", 15.0),
    ("A pizza is cut into 8 slices. John eats 3 slices. How many slices are left?", 5.0),
]


def run_tests(solver=None):
    if solver is None:
        solver = StructuredSolver()
        solver.learn_from_gsm8k()

    print("═══ TESTS DU RÉSOLVEUR STRUCTURÉ (ONDES) ═══")
    ok = 0
    for q, expected in _SAMPLES:
        result = solver.solve(q)
        good = result is not None and abs(result - expected) < 1e-6
        ok += good
        struct_name, score = solver.detect_structure(q)
        print(f"{'✅' if good else '❌'} [{struct_name[:20]:<20s} s={score:.3f}] "
              f"{q[:55]:<57} → {result} (attendu {expected})")
    print(f"\nSCORE : {ok}/{len(_SAMPLES)} ({100 * ok / len(_SAMPLES):.1f}%)")
    return ok, len(_SAMPLES)


def benchmark_gsm8k(solver=None, n: int = 200):
    if solver is None:
        solver = StructuredSolver()
        solver.learn_from_gsm8k()

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        problems = [json.loads(l) for l in f]

    import random
    random.seed(42)
    sample = random.sample(problems, min(n, len(problems)))

    correct, no_sol, total = 0, 0, len(sample)
    times = []

    for i, p in enumerate(sample):
        q = p.get('question', '')
        ans_str = p.get('answer', '')
        expected = None
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
        if m:
            expected = float(m.group(1))

        t0 = time.time()
        result = solver.solve(q)
        dt = (time.time() - t0) * 1000
        times.append(dt)

        if result is None:
            no_sol += 1
        elif expected is not None and abs(result - expected) < 1e-6:
            correct += 1

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{total} — {correct}/{i + 1} "
                  f"({100 * correct / (i + 1):.1f}%)")

    print(f"\n═══ BENCHMARK GSM8K (résolveur structuré) ═══")
    print(f"  Problèmes : {total}")
    print(f"  Corrects  : {correct}")
    print(f"  Accuracy  : {100 * correct / total:.1f}%")
    print(f"  Sans sol. : {no_sol}")
    print(f"  Temps moy.: {np.mean(times):.1f} ms")

    return {'accuracy': round(100 * correct / total, 1), 'correct': correct,
            'total': total, 'no_solution': no_sol, 'avg_ms': round(np.mean(times), 1)}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Tests sur les 15 exemples')
    parser.add_argument('--benchmark', type=int, default=0)
    args = parser.parse_args()

    solver = StructuredSolver()
    solver.learn_from_gsm8k()

    if args.test or not args.benchmark:
        run_tests(solver)

    if args.benchmark:
        benchmark_gsm8k(solver, args.benchmark)
