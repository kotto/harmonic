#!/usr/bin/env python3
"""
pipeline_mesure.py — Architecture validée par les mesures
==========================================================

Les 3 piliers (mesurés, pas supposés) :

  1. NOYAU DORÉ (GATE)    — α=1/φ, K_eff(t): 1→0
     Élimine le bruit. Ne discrimine pas le contenu.
     Validé T1/T2 série.        [filtre_dynamique.py]

  2. REPRÉSENTATION APPRISE   — MiniLM 384-dim
     Capture la sémantique. L'encode FNV-1a est le paramètre.
     Validé : 36.3% baseline.  [sentence-transformers]

  3. HRR (RELATIONS)          — bind/unbind/superpose/resonate
     Grammaire de liens entité↔objet↔valeur.
     Validé P1.3bis.           [raisonneur_ondulatoire.py]

Exclusions publiées (réfutées par les mesures) :
  X1 · Le noyau distingue nombres/mots → FAUX (P1.1 + frontière langue)
  X2 · Δφ encode les opérations        → FAUX (TEST 2, contrôle validé)
  X3 · « Zéro paramètre »              → FAUX (l'encode EST le paramètre)

USAGE :
  python pipeline_mesure.py --test
  python pipeline_mesure.py --benchmark 200
"""

import sys, os, re, json, time, pickle
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_lang import encode, superpose, resonate, normalize, DEFAULT_DIM
from encodage_phase import PhaseEncoder
from encodage_logarithmique import LogWaveEncoder
from raisonneur_algebrique import AlgebriqueReasoner
from raisonneur_ondulatoire import (
    OndulatoireReasoner, _extract_numbers, _STOP, MOTS_ACTION
)
from filtre_dynamique import DynamicHarmonicFilter, abc_kernel, ALPHA


# ═══════════════════════════════════════════════════════════════════════════
# 1. CHARgement MINILM (représentation apprise)
# ═══════════════════════════════════════════════════════════════════════════

_minilm_model = None
_minilm_tokenizer = None
_minilm_classifier = None
_minilm_scaler = None

# Verbes d'action pour la classification
_ACTION_VERBS = {
    'add': ['buys', 'buy', 'bought', 'gains', 'gain', 'earns', 'earn',
            'collects', 'collect', 'receives', 'receive', 'finds', 'find',
            'gets', 'get', 'wins', 'win', 'more', 'additional', 'also',
            'another', 'gave', 'gives', 'give', 'adds', 'add'],
    'sub': ['sells', 'sell', 'sold', 'spends', 'spend', 'spent',
            'loses', 'lose', 'lost', 'eats', 'eat', 'ate',
            'removes', 'remove', 'left', 'remain', 'remaining',
            'gives away', 'takes away'],
    'mult': ['times', 'twice', 'double', 'triple', 'each', 'every',
             'per', 'apiece', 'multiply', 'product'],
    'div': ['split', 'shared', 'divided', 'among', 'quotient',
            'each group', 'per person', 'per student'],
}


def _load_minilm():
    """Charge MiniLM (paresseux, une seule fois)."""
    global _minilm_model, _minilm_tokenizer

    if _minilm_model is not None:
        return

    try:
        from sentence_transformers import SentenceTransformer
        model_name = 'sentence-transformers/all-MiniLM-L6-v2'
        print(f"  Chargement MiniLM ({model_name})...")
        _minilm_model = SentenceTransformer(model_name)
        _minilm_tokenizer = None  # SentenceTransformer gère tout
        print(f"  ✓ MiniLM chargé")
    except ImportError:
        print("  ⚠ sentence-transformers non installé — fallback FNV-1a")
        _minilm_model = False
    except Exception as e:
        print(f"  ⚠ Erreur chargement MiniLM: {e} — fallback FNV-1a")
        _minilm_model = False


def _load_classifier():
    """Charge le classifieur d'opérations (MiniLM → op)."""
    global _minilm_classifier, _minilm_scaler

    if _minilm_classifier is not None:
        return

    classifier_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'gsm8k_minilm_classifier.pkl')

    if os.path.exists(classifier_path):
        try:
            with open(classifier_path, 'rb') as f:
                data = pickle.load(f)
            _minilm_classifier = data.get('classifier')
            _minilm_scaler = data.get('scaler')
            print(f"  ✓ Classifieur MiniLM chargé (36.3% baseline)")
        except Exception:
            _minilm_classifier = None
    else:
        _minilm_classifier = None


def minilm_encode(text: str):
    """Encode un texte avec MiniLM (384-dim) ou fallback FNV-1a."""
    _load_minilm()

    if _minilm_model and _minilm_model is not False:
        emb = _minilm_model.encode([text], show_progress_bar=False)[0]
        return emb.astype(np.float64)
    else:
        # Fallback: encodage FNV-1a
        words = re.findall(r'[a-z0-9]{2,}', text.lower())
        if not words:
            return np.zeros(DEFAULT_DIM, dtype=np.complex128)
        psi = superpose(*[encode(w, dim=DEFAULT_DIM) for w in words])
        # Convertir en réel 384-dim pour compatibilité
        real_part = np.concatenate([psi.real[:192], psi.imag[:192]])
        return real_part.astype(np.float64)


def minilm_classify(text: str) -> Tuple[Optional[str], float]:
    """
    Classifie l'opération d'une phrase avec MiniLM.

    Retourne (opération, confiance).
    """
    _load_minilm()
    _load_classifier()

    emb = minilm_encode(text)

    if _minilm_classifier is not None and _minilm_scaler is not None:
        # Utiliser le classifieur entraîné
        emb_scaled = _minilm_scaler.transform([emb])
        probs = _minilm_classifier.predict_proba(emb_scaled)[0]
        idx = np.argmax(probs)
        classes = _minilm_classifier.classes_
        if idx < len(classes):
            return classes[idx], float(probs[idx])
        return None, 0.0

    else:
        # Fallback: similarité cosinus avec prototypes de verbes
        op_scores = {}
        for op, verbs in _ACTION_VERBS.items():
            if not verbs:
                continue
            proto_embs = [minilm_encode(v) for v in verbs]
            similarities = []
            for pe in proto_embs:
                if np.linalg.norm(emb) > 0 and np.linalg.norm(pe) > 0:
                    sim = np.dot(emb, pe) / (np.linalg.norm(emb) * np.linalg.norm(pe))
                    similarities.append(sim)
            if similarities:
                op_scores[op] = max(similarities)

        if op_scores:
            best_op = max(op_scores, key=op_scores.get)
            return best_op, op_scores[best_op]

        return None, 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 2. PIPELINE MESURÉ
# ═══════════════════════════════════════════════════════════════════════════

class MeasuredPipeline:
    """
    Pipeline GSM8K fondé sur les 3 piliers mesurés.
    """

    def __init__(self):
        # Pilier 1 : Noyau Doré (GATE)
        self.gate = DynamicHarmonicFilter()

        # Pilier 2 : encodage FNV-1a pour HRR word-level
        self.dim = DEFAULT_DIM

        # Précharger MiniLM
        _load_minilm()

    def _regex_detect(self, sent: str) -> Optional[str]:
        """Détection regex (fallback éprouvé)."""
        text = sent.lower()
        patterns = [
            (r'(times\s+as\s+(many|much)|twice|double|triple)', 'mult'),
            (r'\b(each|every)\b.*\b(has|have|contains?|holds?)\b', 'mult'),
            (r'\b(per|earns?)\b.*\b(hour|day|week|month)\b', 'rate'),
            (r'\b(split|shared\s+equally|divided\s+equally|among)\b', 'div'),
            (r'\b(ate|eats|eat|sells?|sold|spends?|spent|loses?|lost|'
             r'gives?\s+(away|to)|gives?\s+\d+\s+to|removes?|takes?\s+away)\b', 'sub'),
            (r'\b(left|remain|remaining)\b', 'sub'),
            (r'\b(buys|buy|bought|gains?|earns?|collects?|receives?|finds?|'
             r'gets?|obtains?|wins?|gave\s+\w+\s+\d+|gives\s+\w+\s+\d+)\b', 'add'),
            (r'\b(more|additional|also|another)\b', 'add'),
        ]
        for pattern, op in patterns:
            if re.search(pattern, text):
                return op
        return None

    def _resolve_action(self, sent: str, r_hrr: OndulatoireReasoner) -> Tuple[str, float]:
        """
        Résout l'action d'une phrase.

        Ordre : MiniLM (appris) → regex (éprouvé)
        Le noyau doré a déjà GATÉ la phrase (elle est mathématique).
        """
        # 1. MiniLM (représentation apprise)
        op_ml, conf_ml = minilm_classify(sent)
        if op_ml and conf_ml > 0.6:
            return op_ml, conf_ml

        # 2. Regex (fallback éprouvé)
        op_rx = self._regex_detect(sent)
        if op_rx:
            return op_rx, 0.8

        # 3. MiniLM avec confiance basse
        if op_ml:
            return op_ml, conf_ml

        return 'add', 0.3  # fallback ultime

    def solve(self, question: str) -> Optional[float]:
        """
        Résout un problème GSM8K avec le pipeline mesuré.

        1. Noyau Doré → GATE (chaque phrase)
        2. MiniLM → action (si regex échoue)
        3. HRR → tracking entité/objet/valeur
        4. Algebrique → résolution
        """
        q = question.strip()
        q = re.sub(r'\s+', ' ', q)
        sentences = re.split(r'(?<=[.;!?])\s+', q)
        sentences = [s.strip() for s in sentences if s.strip()]

        r_alg = AlgebriqueReasoner()
        r_hrr = OndulatoireReasoner()

        last_entity, last_obj = None, None
        step = 0

        for sent in sentences:
            # QUESTION → break
            if re.search(r'\b(how many|how much|what is|what are|'
                        r'how far|how long|how old)\b', sent.lower()):
                break

            # 1. NOYAU DORÉ : GATE
            filter_result = self.gate.filter_iteratively(sent)
            numbers = filter_result['numbers']
            if not numbers:
                continue

            # 2. RÉSOLUTION ENTITÉ/OBJET (HRR, word-level FNV-1a)
            from raisonneur_ondulatoire import _best_object_from_sentence
            entity, obj = _best_object_from_sentence(sent, r_hrr)
            entity = entity or last_entity
            if entity is None:
                caps = re.findall(r'\b([A-Z][a-z]{2,})\b', sent)
                _pronouns = {'she', 'he', 'they', 'his', 'her', 'their', 'its',
                            'who', 'how', 'what', 'when', 'where', 'there', 'each', 'every'}
                caps = [c for c in caps if c.lower() not in _pronouns]
                if caps:
                    entity = caps[0].lower()
                elif not r_hrr._registry:
                    entity = 'someone'

            if obj is not None and last_obj is not None and obj not in r_hrr.object_names:
                obj = last_obj
            if obj is None and last_obj:
                obj = last_obj
            if obj is None:
                words = [w for w in re.findall(r'[a-z]{3,}', sent.lower()) if w not in _STOP]
                if words:
                    obj = words[-1]

            if entity is None or obj is None:
                continue

            # 3. RÉSOLUTION ACTION (MiniLM → regex)
            # Détecter d'abord les patterns spéciaux (comparaison, cross-mult)
            from raisonneur_ondulatoire import _detect_comparison, _detect_mult_div
            comparison = _detect_comparison(sent, numbers)
            implicit_op = _detect_mult_div(sent)
            rate_mode = bool(re.search(
                r'\b(per\s+(hour|day|week|month)|a\s+(day|week|month)|'
                r'earns?\s+\d+\s+(dollars?\s+)?per)\b', sent.lower()))

            has_init = bool(re.search(
                r'\b(?:has|had|have|there\s+are|there\s+were|owns?|bought|'
                r'collected|found|bakes?|makes?|produces?|started\s+with|'
                r'purchased|packed)\s+\d+', sent.lower()))
            is_init = (not r_hrr._registry or has_init)
            if is_init and (comparison or implicit_op):
                is_init = False

            # Déterminer l'action
            action = None
            comp_val = None

            if comparison:
                action, comp_val = comparison
            elif rate_mode:
                action = 'rate'
            elif implicit_op:
                action = implicit_op
            elif is_init:
                action = 'init'
            else:
                action, _ = self._resolve_action(sent, r_hrr)

            # 4. EXÉCUTER
            step += 1
            var_name = f"{entity}_{obj}"
            val = float(numbers[0])

            # ── VÉRIFICATION PRIORITAIRE : durée après taux ─────
            dur_match = re.search(r'(\d+(?:\.\d+)?)\s*(hours?|days?|weeks?)',
                                 sent.lower())
            duration_handled = False
            if dur_match and not rate_mode:
                dur_val = float(dur_match.group(1))
                for rkey, rval in list(r_alg._equations.items()):
                    if rkey.startswith('rate_'):
                        total = float(rval) * dur_val
                        earn_var = f"{entity}_money"
                        r_alg.define(earn_var, ('mult', rkey, dur_val))
                        r_hrr.learn_fact(entity, 'money', total)
                        last_entity, last_obj = entity, 'money'
                        duration_handled = True
                        break
            if duration_handled:
                continue  # passer à la phrase suivante

            # --- Traitement spécial : comparaison ---
            if comparison:
                if entity and obj:
                    all_ents = set()
                    for e_name in list(r_hrr.entity_names):
                        if e_name in sent.lower():
                            all_ents.add(e_name)
                    other = (all_ents - {entity}).pop() if len(all_ents - {entity}) > 0 else None
                    if other is None:
                        for (k_e, k_o), k_q in list(r_hrr._registry.items()):
                            if k_o == obj and k_e != entity:
                                other = k_e
                                break
                    if other:
                        ref_var = f"{other}_{obj}"
                        if ref_var not in r_alg._equations:
                            base_val = r_hrr.query(other, obj)
                            if base_val is not None:
                                r_alg.define(ref_var, base_val)
                        r_alg.define(var_name, (action, ref_var, comp_val))
                        if ref_var in r_alg._equations:
                            base = r_alg.eval(ref_var)
                            if base is not None:
                                r_hrr.learn_fact(entity, obj, base * comp_val)
                        last_entity, last_obj = entity, obj
                        continue

            # --- Rate ---
            if action == 'rate':
                rate_var = f"rate_{step}"
                r_alg.define(rate_var, val)
                r_hrr.learn_fact(entity, obj, val)
                last_entity, last_obj = entity, obj
                last_var = rate_var  # ← pour la détection de durée
                r_hrr._registry[(entity, 'money')] = val

            # --- Init ---
            elif action == 'init':
                r_alg.define(var_name, val)
                r_hrr.learn_fact(entity, obj, val)
                last_entity, last_obj = entity, obj

            # --- Mult ---
            elif action == 'mult':
                # Cross-mult?
                sent_words = set(re.findall(r'[a-z]{3,}', sent.lower()))
                found_cross = False
                for (k_e, k_o), k_q in list(r_hrr._registry.items()):
                    if k_o in sent_words and k_e != entity:
                        ref_var = f"{k_e}_{k_o}"
                        if ref_var not in r_alg._equations:
                            r_alg.define(ref_var, k_q)
                        r_alg.define(var_name, ('mult', ref_var, val))
                        r_hrr.learn_fact(entity, obj, float(k_q) * val)
                        found_cross = True
                        break
                if not found_cross:
                    if var_name in r_alg._equations:
                        r_alg.update(var_name, 'mult', val)
                        r_hrr.apply_action(entity, obj, 'mult', val)
                    else:
                        r_alg.define(var_name, val)
                        r_hrr.learn_fact(entity, obj, val)
                last_entity, last_obj = entity, obj

            # --- Div ---
            elif action == 'div':
                if var_name in r_alg._equations:
                    r_alg.update(var_name, 'div', val)
                    r_hrr.apply_action(entity, obj, 'div', val)
                else:
                    if len(numbers) >= 2:
                        r_alg.define(var_name, ('div', float(numbers[0]), float(numbers[1])))
                        r_hrr.learn_fact(entity, obj,
                                        float(numbers[0]) / max(float(numbers[1]), 0.001))
                    else:
                        r_alg.define(var_name, val)
                        r_hrr.learn_fact(entity, obj, val)
                last_entity, last_obj = entity, obj

            # --- Sub ---
            elif action == 'sub':
                if var_name in r_alg._equations:
                    r_alg.update(var_name, 'sub', val)
                    r_hrr.apply_action(entity, obj, 'sub', val)
                else:
                    r_alg.define(var_name, val)
                    r_hrr.learn_fact(entity, obj, val)
                last_entity, last_obj = entity, obj

            # --- Add (default) ---
            else:
                if var_name in r_alg._equations:
                    r_alg.update(var_name, 'add', val)
                    r_hrr.apply_action(entity, obj, 'add', val)
                else:
                    r_alg.define(var_name, val)
                    r_hrr.learn_fact(entity, obj, val)
                last_entity, last_obj = entity, obj

        # 5. RÉSOUDRE LA CIBLE
        from raisonneur_ondulatoire import _best_object_from_sentence
        target_entity, target_obj = last_entity, last_obj
        question_sent = sentences[-1] if sentences else ''
        if '?' in question_sent or 'how many' in question_sent.lower():
            q_entity, q_obj = _best_object_from_sentence(question_sent, r_hrr)
            target_entity = q_entity or target_entity
            if q_obj:
                action_verbs_flat = {v for vals in MOTS_ACTION.values() for v in vals}
                extra_verbs = {'earn', 'work', 'make', 'get', 'give', 'take', 'use', 'pay', 'cost'}
                if q_obj.lower() not in action_verbs_flat and q_obj.lower() not in extra_verbs:
                    target_obj = q_obj

        if target_entity and target_obj:
            target_var = f"{target_entity}_{target_obj}"
            result = r_alg.solve(target_var)
            if result is not None:
                return result
            for vn in r_alg._equations:
                if vn.startswith(f"{target_entity}_"):
                    val = r_alg.solve(vn)
                    if val is not None:
                        return val

        if r_alg._equations:
            return r_alg.solve(list(r_alg._equations.keys())[-1])
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 3. TESTS + BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════

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


def run_tests():
    print("═" * 60)
    print("TEST : PIPELINE MESURÉ")
    print("═" * 60)
    print()

    pipeline = MeasuredPipeline()

    ok = 0
    for q, expected in _SAMPLES:
        result = pipeline.solve(q)
        good = result is not None and abs(result - expected) < 1e-6
        ok += good
        print(f"{'✅' if good else '❌'} {q[:55]:<57} → {result} (attendu {expected})")
    print(f"\nSCORE : {ok}/{len(_SAMPLES)} ({100 * ok / len(_SAMPLES):.1f}%)")
    return ok


def benchmark_gsm8k(n=200):
    pipeline = MeasuredPipeline()

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        problems = [json.loads(l) for l in f]

    import random
    random.seed(42)
    sample = random.sample(problems, min(n, len(problems)))

    correct, no_sol, total = 0, 0, len(sample)
    times = []

    print(f"═══ BENCHMARK PIPELINE MESURÉ ({total} problèmes) ═══")
    for i, p in enumerate(sample):
        q = p.get('question', '')
        ans_str = p.get('answer', '')
        expected = None
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
        if m:
            expected = float(m.group(1))

        t0 = time.time()
        result = pipeline.solve(q)
        dt = (time.time() - t0) * 1000
        times.append(dt)

        if result is None:
            no_sol += 1
        elif expected is not None and abs(result - expected) < 1e-6:
            correct += 1

        if (i + 1) % 25 == 0:
            print(f"  {i+1:>4d}/{total} — {correct}/{i+1} "
                  f"({100*correct/(i+1):.1f}%)")

    accuracy = 100 * correct / total if total > 0 else 0
    print(f"\n═══ RÉSULTATS ═══")
    print(f"  Accuracy : {accuracy:.1f}% ({correct}/{total})")
    print(f"  Sans sol.: {no_sol}")
    print(f"  Temps    : {np.mean(times):.1f} ms")
    return accuracy


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--benchmark', type=int, default=0)
    args = parser.parse_args()

    if args.test or not args.benchmark:
        run_tests()

    if args.benchmark:
        benchmark_gsm8k(args.benchmark)
