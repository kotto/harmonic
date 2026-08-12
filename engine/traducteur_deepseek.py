#!/usr/bin/env python3
"""
traducteur_deepseek.py — DeepSeek traduit, THU exécute
=======================================================

Architecture modulaire : le LLM est le TRADUCTEUR (langage naturel → opérations).
Le noyau THU est l'EXÉCUTEUR (opérations → résultat).
Aucun calcul fait par le LLM — juste la traduction.

FORMAT DE SORTIE ATTENDU :
  INIT(entity="john", object="apples", value=5)
  ADD(entity="john", value=3)
  SUBTRACT(entity="mary", value=4)
  MULTIPLY(entity="john", multiplier=3)
  CROSS_MULT(container="box", per_unit=5, product="pencils")
  RATE(entity="james", rate=20)
  DURATION(duration=8)
  DIVIDE(divisor=4)
  QUERY(entity="mary", object="apples")
"""

import sys, os, re, json, time, requests
import numpy as np
from typing import Optional, List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compilateur_thu import MemoireHolographique


# ═══════════════════════════════════════════════════════════════════════════
# 1. CLIENT DEEPSEEK
# ═══════════════════════════════════════════════════════════════════════════

def _load_api_key() -> str:
    """Charge la clé API DeepSeek depuis .env"""
    here = os.path.dirname(os.path.abspath(__file__))
    env_paths = [
        os.path.join(here, '.env'),
        os.path.join(os.path.dirname(here), '.env'),
    ]
    for p in env_paths:
        if os.path.exists(p):
            with open(p, 'r') as f:
                for line in f:
                    if line.startswith('DEEPSEEK_API_KEY='):
                        return line.split('=', 1)[1].strip()
    return os.environ.get('DEEPSEEK_API_KEY', '')


def traduire_deepseek(probleme: str, api_key: str = None) -> Optional[str]:
    """
    Envoie un problème à DeepSeek pour traduction en opérations structurées.

    Retourne la réponse brute (texte des opérations).
    """
    if api_key is None:
        api_key = _load_api_key()

    if not api_key:
        print("⚠ Pas de clé API DeepSeek")
        return None

    prompt = f"""Tu es un traducteur de problèmes mathématiques. Tu dois traduire le problème suivant en une séquence d'opérations structurées. Tu ne fais AUCUN calcul. Tu ne donnes PAS la réponse finale. Tu te contentes de traduire chaque phrase en opération.

OPÉRATIONS DISPONIBLES :
  INIT(entity, object, value)          — "X a N objets" → stocke la valeur initiale
  ADD(entity, value)                    — "X gagne/achète/reçoit N" → ajoute
  SUBTRACT(entity, value)               — "X perd/dépense/vend/donne N" → soustrait
  MULTIPLY(entity, multiplier)          — "X a N fois plus" → multiplie
  CROSS_MULT(container, per_unit, product) — "chaque X a N Y" → conteneur × unité
  RATE(entity, rate)                    — "X gagne N par heure"
  DURATION(duration)                    — "X travaille N heures"
  DIVIDE(divisor)                      — "divisé en N groupes"
  QUERY(entity, object)                 — question posée

RÈGLES :
- entity = qui (john, mary, bakery, _)
- object = quoi (apples, cookies, dollars)
- value/multiplier/rate/duration/divisor = le nombre
- Utilise "_" comme entité pour les objets sans propriétaire

EXEMPLES :

Problème : "John has 5 apples. He buys 3 more. How many apples does he have?"
Opérations :
INIT(entity="john", object="apples", value=5)
ADD(entity="john", value=3)
QUERY(entity="john", object="apples")

Problème : "There are 6 boxes. Each box has 5 pencils. How many pencils are there in total?"
Opérations :
INIT(entity="_", object="boxes", value=6)
CROSS_MULT(container="box", per_unit=5, product="pencils")
QUERY(entity="_", object="pencils")

Problème : "Mary had 10 cookies. She ate 4. How many cookies does she have left?"
Opérations :
INIT(entity="mary", object="cookies", value=10)
SUBTRACT(entity="mary", value=4)
QUERY(entity="mary", object="cookies")

Problème : "James earns 20 dollars per hour. He works 8 hours. How much does he earn?"
Opérations :
RATE(entity="james", rate=20)
DURATION(duration=8)
QUERY(entity="james", object="money")

Maintenant, traduis ce problème (UNIQUEMENT les opérations, une par ligne) :

Problème : "{probleme}"
Opérations :"""

    try:
        resp = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.0,
                'max_tokens': 500,
            },
            timeout=30,
        )
        data = resp.json()
        if 'choices' in data:
            return data['choices'][0]['message']['content']
        else:
            print(f"⚠ Erreur API: {data}")
            return None
    except Exception as e:
        print(f"⚠ Exception: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 2. PARSER OPÉRATIONS → EXÉCUTION THU
# ═══════════════════════════════════════════════════════════════════════════

def parser_operations(texte: str) -> List[dict]:
    """Parse le texte de sortie de DeepSeek en liste d'opérations."""
    ops = []
    for line in texte.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue

        # Supprimer les commentaires inline (// ou <!-- -->)
        line = re.sub(r'//.*', '', line)
        line = re.sub(r'<!--.*?-->', '', line)
        line = line.strip()
        if not line:
            continue

        # Pattern: OPERATION(key="value", ...)
        m = re.match(r'(\w+)\((.*)\)', line)
        if not m:
            continue

        op_name = m.group(1).upper()
        args_str = m.group(2)

        # Parser les arguments key="value"
        params = {}
        for am in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', args_str):
            params[am.group(1)] = am.group(2)
        # Aussi accepter les nombres sans guillemets
        for am in re.finditer(r'(\w+)\s*=\s*([\d.]+)', args_str):
            key = am.group(1)
            if key not in params:
                params[key] = float(am.group(2))

        params['op'] = op_name
        ops.append(params)

    return ops


def executer_operations(ops: List[dict]) -> Optional[float]:
    """Exécute une séquence d'opérations avec le moteur THU."""
    m = MemoireHolographique()
    last_entity = None
    last_object = None
    rate_entity = None
    query_entity = None
    query_object = None

    for op in ops:
        op_name = op.get('op', '')

        if op_name == 'INIT':
            ent = op.get('entity', '_')
            obj = op.get('object', 'item')
            val = float(op.get('value', 0))
            m.apprendre(ent, obj, val)
            last_entity = ent
            last_object = obj

        elif op_name == 'ADD':
            ent = op.get('entity', last_entity or '_')
            val = float(op.get('value', 0))
            obj = last_object or 'item'
            existing = m.interroger(ent, obj)
            if existing is not None:
                m.mettre_a_jour(ent, obj, 'ADD', val)
            else:
                m.apprendre(ent, obj, val)

        elif op_name == 'SUBTRACT':
            ent = op.get('entity', last_entity or '_')
            val = float(op.get('value', 0))
            obj = last_object or 'item'
            existing = m.interroger(ent, obj)
            if existing is not None:
                m.mettre_a_jour(ent, obj, 'SUB', val)
            else:
                m.apprendre(ent, obj, -val)

        elif op_name == 'MULTIPLY':
            ent = op.get('entity', last_entity or '_')
            mult = float(op.get('multiplier', op.get('value', 1)))
            obj = last_object or 'item'
            existing = m.interroger(ent, obj)
            if existing is not None:
                m.mettre_a_jour(ent, obj, 'MULT', mult)
            else:
                # Chercher une autre entité avec le même objet
                for k, v in list(m._values.items()):
                    parts = k.split('|', 1)
                    if len(parts) == 2 and parts[1] == obj and parts[0] != ent:
                        m.apprendre(ent, obj, float(v) * mult)
                        break
                else:
                    m.apprendre(ent, obj, mult)

        elif op_name == 'CROSS_MULT':
            container = op.get('container', '')
            per_unit = float(op.get('per_unit', 0))
            product = op.get('product', '')
            count = None
            # Chercher le compte du conteneur (essayer singulier, pluriel, -es)
            for suffix in ('', 's', 'es'):
                probe = container.rstrip('s') + suffix
                for k, v in m._values.items():
                    parts = k.split('|', 1)
                    if len(parts) == 2 and parts[1] == probe:
                        count = float(v)
                        break
                if count is not None:
                    break
            if count is not None and product:
                m.apprendre('_', product, count * per_unit)
                last_object = product

        elif op_name == 'RATE':
            ent = op.get('entity', '_')
            rate = float(op.get('rate', 0))
            m.apprendre(ent, 'rate', rate)
            rate_entity = ent
            last_entity = ent

        elif op_name == 'DURATION':
            dur = float(op.get('duration', 0))
            ent = rate_entity or last_entity or '_'
            rate = m.interroger(ent, 'rate')
            if rate is not None:
                m.apprendre(ent, 'money', rate * dur)
                last_object = 'money'

        elif op_name == 'DIVIDE':
            div = float(op.get('divisor', 1))
            if div > 0 and m._values:
                first_key = list(m._values.keys())[0]
                parts = first_key.split('|', 1)
                if len(parts) == 2:
                    m.mettre_a_jour(parts[0], parts[1], 'DIV', div)

        elif op_name == 'QUERY':
            query_entity = op.get('entity', last_entity or '_')
            query_object = op.get('object', last_object or '')

    # Résoudre
    if query_entity and query_object:
        result = m.interroger(query_entity, query_object)
        if result is not None:
            return result

    if query_object:
        for k, v in m._values.items():
            parts = k.split('|', 1)
            if len(parts) == 2 and parts[1] == query_object:
                return float(v)

    if m._values:
        return float(list(m._values.values())[-1])

    return None


# ═══════════════════════════════════════════════════════════════════════════
# 3. SOLVEUR COMPLET
# ═══════════════════════════════════════════════════════════════════════════

class DeepSeekSolver:
    """Solveur : DeepSeek traduit → THU exécute."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or _load_api_key()

    def solve(self, probleme: str) -> Optional[float]:
        texte_ops = traduire_deepseek(probleme, self.api_key)
        if texte_ops is None:
            return None
        ops = parser_operations(texte_ops)
        if not ops:
            return None
        return executer_operations(ops)


# ═══════════════════════════════════════════════════════════════════════════
# 4. TESTS + BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════

_SAMPLES = [
    ("John has 5 apples. He buys 3 more. How many apples does he have?", 8.0),
    ("Mary had 10 cookies. She ate 4. How many cookies does she have left?", 6.0),
    ("Tom has 12 dollars. He spends 4 dollars. How many dollars does he have left?", 8.0),
    ("There are 6 boxes. Each box has 5 pencils. How many pencils are there in total?", 30.0),
    ("Sue has 10 stickers. She gives 3 to her friend. How many stickers does Sue have left?", 7.0),
    ("John has 5 apples. Mary has 3 times as many. How many apples does Mary have?", 15.0),
    ("James earns 20 dollars per hour. He works 8 hours. How much does he earn?", 160.0),
]

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--benchmark', type=int, default=0)
    p.add_argument('--problem', type=str, default=None)
    args = p.parse_args()

    if args.problem:
        solver = DeepSeekSolver()
        print(f"Problème : {args.problem}")
        texte = traduire_deepseek(args.problem)
        print(f"DeepSeek →\n{texte}")
        ops = parser_operations(texte) if texte else []
        print(f"Ops : {ops}")
        result = executer_operations(ops) if ops else None
        print(f"Résultat THU : {result}")

    elif args.test:
        print("═══ TEST DEEPSEEK → THU ═══")
        solver = DeepSeekSolver()
        ok = 0
        for q, expected in _SAMPLES:
            result = solver.solve(q)
            good = result is not None and abs(result - expected) < 1e-6
            ok += good
            print(f"  {'✅' if good else '❌'} {q[:52]:<54} → {result} ({expected})")
        print(f"\n  SCORE : {ok}/{len(_SAMPLES)} ({100*ok/len(_SAMPLES):.1f}%)")

    elif args.benchmark:
        from structure_retrieval import StructuredRetrieval
        sr = StructuredRetrieval()
        sr.split_and_index()
        test = sr._test_problems[:args.benchmark]
        solver = DeepSeekSolver()
        correct, no_sol, total = 0, 0, len(test)
        times = []
        print(f"═══ BENCHMARK DEEPSEEK→THU ({total} problèmes) ═══")
        for i, prob in enumerate(test):
            q = prob['question']
            m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', prob['answer'])
            expected = float(m.group(1)) if m else None
            t0 = time.time()
            result = solver.solve(q)
            dt = (time.time()-t0)*1000
            times.append(dt)
            if result is None: no_sol += 1
            elif expected and abs(result-expected) < 1e-6: correct += 1
            if (i+1) % 10 == 0:
                print(f"  {i+1:>4d}/{total} — {correct}/{i+1} ({100*correct/(i+1):.1f}%)")
        acc = 100*correct/total if total > 0 else 0
        print(f"\n═══ RÉSULTATS ═══")
        print(f"  Accuracy : {acc:.1f}% ({correct}/{total})")
        print(f"  Sans sol.: {no_sol}")
        print(f"  Temps moy: {np.mean(times):.1f} ms")

    else:
        # Test rapide sur un problème
        solver = DeepSeekSolver()
        q = "John has 5 apples. He buys 3 more. How many apples does he have?"
        print(f"Test : {q}")
        print(f"Résultat : {solver.solve(q)} (attendu 8)")
