#!/usr/bin/env python3
"""
solveur_minilm_deepseek.py — Solveur MiniLM+DeepSeek labels + THU
====================================================================
Classifieur entraîné sur les 2440 labels DeepSeek (39.1% CV).
Intégré dans le solveur spaCy + THU.
"""
import sys, os, re, json, time, pickle
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extracteur_spacy import SpacySolver, parse_sentence
from compilateur_thu import MemoireHolographique

# ═══════════════════════════════════════════════════════════════════════════
# 1. CHARGEMENT DU CLASSIFIEUR MINILM+DEEPSEEK
# ═══════════════════════════════════════════════════════════════════════════

_model_sb = None
_classifier = None
_scaler = None


def _init_classifier():
    global _model_sb, _classifier, _scaler
    if _classifier is not None:
        return
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'minilm_deepseek.pkl'), 'rb') as f:
        modele = pickle.load(f)
    _classifier = modele['classifier']
    _scaler = modele['scaler']
    from sentence_transformers import SentenceTransformer
    _model_sb = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def classify_minilm_deepseek(sent):
    """Classifie l'opération avec MiniLM+DeepSeek."""
    _init_classifier()
    emb = _model_sb.encode([sent])[0]
    s = _scaler.transform([emb])
    probs = _classifier.predict_proba(s)[0]
    idx = np.argmax(probs)
    return _classifier.classes_[idx], float(probs[idx])


# ═══════════════════════════════════════════════════════════════════════════
# 2. SOLVEUR AVEC CLASSIFIEUR DEEPSEEK
# ═══════════════════════════════════════════════════════════════════════════

class SpacyDeepSeekSolver(SpacySolver):
    """Solveur : spaCy pour les paramètres, MiniLM+DeepSeek pour le type."""

    def solve(self, question):
        q = question.strip()
        q = re.sub(r'\s+', ' ', q)
        sentences = re.split(r'(?<=[.;!?])\s+', q)
        sentences = [s.strip() for s in sentences if s.strip()]

        m = self.m
        self.extractor.reset()
        question_ent, question_obj = None, None

        for sent in sentences:
            if re.search(r'\b(how many|how much|what is|what are|'
                        r'how far|how long|how old)\b', sent.lower()):
                parsed = parse_sentence(sent)
                question_ent = (parsed.nsubj or '').lower()
                q_words = re.findall(r'[a-z]{3,}', sent.lower())
                stop = {'how','many','much','what','does','are','there',
                       'have','has','had','left','remain','per','group','earn'}
                q_objs = [w for w in q_words if w not in stop and not w.isdigit()]
                question_obj = q_objs[-1] if q_objs else None
                continue

            # Classifieur DeepSeek pour le type
            op_ml, conf = classify_minilm_deepseek(sent)

            # Extraction spaCy pour les paramètres
            params = self.extractor.extract(sent)
            if params is None:
                continue

            # Remplacer le type par la prédiction MiniLM (si confiance > 0.4)
            if conf > 0.4:
                params['type'] = op_ml

            op = params['type']
            ent = params.get('entity')
            obj = params.get('object')
            val = (params.get('value') or params.get('multiplier') or
                   params.get('per_unit') or params.get('rate') or
                   params.get('duration') or params.get('divisor'))

            if val is None:
                continue

            _signal_objs = {'more','many','much','fewer','less','times',
                           'each','every','all','some','several'}
            effective_obj = obj
            if obj and obj.lower() in _signal_objs:
                effective_obj = None
            if effective_obj is None:
                effective_obj = self.extractor.discourse.last_object

            if op in ('INIT', 'HAS'):
                if ent and effective_obj:
                    m.apprendre(ent, effective_obj, val)

            elif op in ('ADD', 'GAIN'):
                if ent and effective_obj:
                    existing = m.interroger(ent, effective_obj)
                    if existing is not None:
                        m.mettre_a_jour(ent, effective_obj, 'ADD', val)
                    else:
                        m.apprendre(ent, effective_obj, val)

            elif op in ('SUBTRACT', 'LOSE'):
                if ent and effective_obj:
                    existing = m.interroger(ent, effective_obj)
                    if existing is not None:
                        m.mettre_a_jour(ent, effective_obj, 'SUB', val)
                    else:
                        for k, v in list(m._values.items()):
                            parts = k.split('|', 1)
                            if len(parts) == 2 and parts[1] == effective_obj:
                                m.mettre_a_jour(parts[0], effective_obj, 'SUB', val)
                                break
                        else:
                            m.apprendre(ent, effective_obj, val)

            elif op in ('MULTIPLY', 'MULT', 'TIMES_AS_MANY'):
                if ent and effective_obj:
                    ref_ent = self.extractor.discourse.get_other_entity(effective_obj, ent)
                    if ref_ent:
                        ref_val = m.interroger(ref_ent, effective_obj)
                        if ref_val is not None:
                            m.apprendre(ent, effective_obj, float(ref_val) * val)
                        else:
                            m.apprendre(ent, effective_obj, val)
                    else:
                        existing = m.interroger(ent, effective_obj)
                        if existing is not None:
                            m.mettre_a_jour(ent, effective_obj, 'MULT', val)
                        else:
                            m.apprendre(ent, effective_obj, val)

            elif op == 'CROSS_MULT':
                container = params.get('container') or effective_obj
                per_unit = val
                if per_unit and effective_obj:
                    count = None
                    for suffix in ('', 's', 'es'):
                        probe = (container or '').rstrip('s') + suffix
                        for k, v in m._values.items():
                            parts = k.split('|', 1)
                            if len(parts) == 2 and parts[1] == probe:
                                count = float(v)
                                break
                        if count is not None:
                            break
                    if count is not None:
                        m.apprendre('_', effective_obj, count * per_unit)
                    else:
                        m.apprendre('_', effective_obj, per_unit)

            elif op == 'RATE':
                if ent:
                    m.apprendre(ent, 'rate', val)
                    self._rate_entity = ent

            elif op == 'DURATION':
                rate_ent = ent or self._rate_entity
                if rate_ent:
                    rate = m.interroger(rate_ent, 'rate')
                    if rate is not None:
                        m.apprendre(rate_ent, 'money', rate * val)

            elif op in ('DIVIDE', 'DIV', 'PARTITION'):
                if m._values:
                    first_key = list(m._values.keys())[0]
                    parts = first_key.split('|', 1)
                    if len(parts) == 2:
                        m.mettre_a_jour(parts[0], parts[1], 'DIV', val)

            elif op == 'FRACTION':
                num = params.get('numerator', 2)
                den = params.get('denominator', 5)
                frac = float(num) / float(den) if den else 0.5
                if ent and effective_obj:
                    existing = m.interroger(ent, effective_obj)
                    if existing is not None:
                        m.mettre_a_jour(ent, effective_obj, 'MULT', frac)

        # Résoudre
        ent = question_ent or self.extractor.discourse.last_entity or ''
        obj = question_obj or self.extractor.discourse.last_object or ''

        if ent and obj:
            result = m.interroger(ent, obj)
            if result is not None:
                return result

        if obj:
            for k, v in m._values.items():
                parts = k.split('|', 1)
                if len(parts) == 2 and parts[1] == obj:
                    return float(v)

        if m._values:
            return float(list(m._values.values())[-1])
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


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--benchmark', type=int, default=0)
    args = p.parse_args()

    if args.test or not args.benchmark:
        print("═══ TEST SOLVEUR MiniLM+DeepSeek ═══")
        ok = 0
        for q, expected in _SAMPLES:
            solver = SpacyDeepSeekSolver()
            result = solver.solve(q)
            good = result is not None and abs(result - expected) < 1e-6
            ok += good
            print(f"  {'✅' if good else '❌'} {q[:52]:<54} → {result} ({expected})")
        print(f"\n  SCORE : {ok}/15 ({100*ok/15:.1f}%)")

    if args.benchmark:
        from structure_retrieval import StructuredRetrieval
        sr = StructuredRetrieval()
        sr.split_and_index()
        test = sr._test_problems[:args.benchmark]
        correct, no_sol, total = 0, 0, len(test)
        times = []
        print(f"═══ BENCHMARK MiniLM+DeepSeek ({total} problèmes) ═══")
        for i, p in enumerate(test):
            q = p['question']
            m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', p['answer'])
            expected = float(m.group(1)) if m else None
            solver = SpacyDeepSeekSolver()
            t0 = time.time()
            result = solver.solve(q)
            dt = (time.time()-t0)*1000
            times.append(dt)
            if result is None: no_sol += 1
            elif expected and abs(result-expected) < 1e-6: correct += 1
            if (i+1) % 50 == 0:
                print(f"  {i+1:>4d}/{total} — {correct}/{i+1} ({100*correct/(i+1):.1f}%)")
        acc = 100*correct/total if total > 0 else 0
        print(f"\n═══ RÉSULTATS ═══")
        print(f"  Accuracy : {acc:.1f}% ({correct}/{total})")
        print(f"  Sans sol.: {no_sol}")
        print(f"  Temps    : {np.mean(times):.1f} ms")
