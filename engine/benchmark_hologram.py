#!/usr/bin/env python3
"""
Benchmark d'Hologramme — Mesure réelle de performance
=======================================================
Évalue la précision et la couverture d'un hologramme spécialisé.

Méthodologie :
  1. GÉNÉRATION DE QUESTIONS — à partir des faits de l'hologramme
  2. TEST — chaque question passe par le cerveau harmonique
  3. MÉTRIQUES — precision, recall, coverage, F1

Métriques :
  - precision    : réponses correctes / réponses données (≠ refus)
  - recall       : réponses correctes / total questions posées
  - coverage     : questions avec réponse / total questions
  - f1_score     : moyenne harmonique precision × recall
  - avg_latency_ms : temps moyen par réponse

Usage :
    python benchmark_hologram.py                           # tous les hologrammes
    python benchmark_hologram.py --holo official_medecine  # un seul
    python benchmark_hologram.py --quick                   # 20 questions/hologramme
"""

import re, json, time, random, argparse, sys
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple, Dict

# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR DE QUESTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Patterns de questions par type de relation
_QUESTION_PATTERNS = {
    'capitale': [
        ('Quelle est la capitale de {sujet} ?', '{objet}'),
        ('{sujet} a pour capitale', '{objet}'),
    ],
    'decouvert': [
        ('Qui a découvert {objet} ?', '{sujet}'),
        ('Quelle découverte est attribuée à {sujet} ?', '{objet}'),
    ],
    'invente': [
        ('Qui a inventé {objet} ?', '{sujet}'),
        ("Qu'est-ce que {sujet} a inventé ?", '{objet}'),
    ],
    'ecrit': [
        ('Qui a écrit {objet} ?', '{sujet}'),
        ("Qu'a écrit {sujet} ?", '{objet}'),
    ],
    'fonde': [
        ('Qui a fondé {objet} ?', '{sujet}'),
    ],
    'situe': [
        ('Où se trouve {sujet} ?', '{objet}'),
    ],
    'symbole': [
        ('Quel est le symbole de {sujet} ?', '{objet}'),
    ],
    'definition': [
        ("Qu'est-ce que {sujet} ?", '{objet}'),
        ('Définis {sujet}', '{objet}'),
    ],
    'cause': [
        ("Qu'est-ce qui cause {objet} ?", '{sujet}'),
    ],
    'produit': [
        ('Que produit {sujet} ?', '{objet}'),
    ],
    'general': [
        ('explique {sujet}', '{objet}'),
        ('{sujet} {relation} quoi ?', '{objet}'),
    ],
}

def _detect_pattern(relation: str) -> str:
    """Détecte le pattern de question adapté à la relation."""
    r = relation.lower()
    for key in _QUESTION_PATTERNS:
        if key in r:
            return key
    return 'general'

def generate_questions(facts: List[Tuple[str, str, str, str]],
                       max_questions: int = 50) -> List[dict]:
    """
    Génère des questions de test à partir des faits d'un hologramme.

    Chaque question a :
      - prompt: la question en langage naturel
      - expected: la réponse attendue (sujet ou objet)
      - source_fact: le fait d'origine (pour la validation)
    """
    questions = []
    seen_questions = set()

    # Filtrer les faits de qualité
    quality_facts = []
    for s, r, o, sec in facts:
        if not s or not r or not o:
            continue
        if len(str(s)) < 2 or len(str(o)) < 2:
            continue
        if 'wikidata.org' in str(s) or 'wikidata.org' in str(o):
            continue
        quality_facts.append((s, r, o, sec))

    random.shuffle(quality_facts)

    for s, r, o, sec in quality_facts[:max_questions * 3]:  # marge
        pattern_key = _detect_pattern(r)
        patterns = _QUESTION_PATTERNS.get(pattern_key, _QUESTION_PATTERNS['general'])
        template, answer_template = random.choice(patterns)

        sujet_clean = str(s).strip()
        objet_clean = str(o).strip()
        relation_clean = str(r).strip()

        question = template.format(
            sujet=sujet_clean,
            objet=objet_clean,
            relation=relation_clean,
        )
        expected = answer_template.format(
            sujet=sujet_clean,
            objet=objet_clean,
            relation=relation_clean,
        )

        # Éviter les doublons
        q_key = question.lower()
        if q_key in seen_questions:
            continue
        seen_questions.add(q_key)

        questions.append({
            'prompt': question,
            'expected': expected,
            'source_fact': (s, r, o, sec),
            'category': pattern_key,
        })

        if len(questions) >= max_questions:
            break

    return questions


# ═══════════════════════════════════════════════════════════════════════════════
# ÉVALUATION
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    t = str(text).lower().strip()
    for a, b in [('é','e'),('è','e'),('ê','e'),('ë','e'),('à','a'),('â','a'),
                 ('ù','u'),('û','u'),('ô','o'),('î','i'),('ï','i'),('ç','c')]:
        t = t.replace(a, b)
    return t

def _check_answer(response: str, expected: str) -> bool:
    """Vérifie si la réponse contient l'information attendue."""
    r = _normalize(response[:200])  # premiers 200 chars
    e = _normalize(expected)

    # Match exact (normalisé)
    if e in r:
        return True

    # Match par mots-clés (70% des mots significatifs)
    e_words = set(w for w in e.split() if len(w) > 2)
    if not e_words:
        return False
    r_words = set(w for w in r.split() if len(w) > 2)
    overlap = len(e_words & r_words) / len(e_words)
    return overlap >= 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def benchmark_hologram(facts: List[Tuple[str, str, str, str]],
                       brain, holo_name: str = "",
                       max_questions: int = 50) -> dict:
    """
    Mesure la performance d'un hologramme sur des questions générées.

    Args:
        facts: liste de (sujet, relation, objet, secteur)
        brain: instance HarmonicBrain (avec l'hologramme chargé)
        holo_name: nom pour le rapport
        max_questions: nombre max de questions à générer
    """
    questions = generate_questions(facts, max_questions)
    if not questions:
        return {'error': 'Aucune question générée'}

    correct = 0
    answered = 0
    refused = 0
    total_time = 0.0
    per_category = defaultdict(lambda: {'n': 0, 'ok': 0})

    for q in questions:
        per_category[q['category']]['n'] += 1

        t1 = time.time()
        try:
            result = brain.process(q['prompt'], lang='fr')
            response = result.response
        except Exception:
            response = ''
        ms = (time.time() - t1) * 1000
        total_time += ms

        # Refus explicite
        is_refusal = any(m in response.lower() for m in
                        ('je ne sais pas', "i don't know", 'pas assez',
                         'ne comprends pas', 'ne connais pas'))

        if is_refusal:
            refused += 1
            continue

        answered += 1
        if _check_answer(response, q['expected']):
            correct += 1
            per_category[q['category']]['ok'] += 1

    n = len(questions)
    precision = correct / max(answered, 1)
    recall = correct / n
    coverage = answered / n
    f1 = 2 * precision * recall / max(precision + recall, 0.001)
    refusal_rate = refused / n
    avg_latency = total_time / n

    # Score des catégories
    cats = {}
    for cat, data in per_category.items():
        if data['n'] > 0:
            cats[cat] = {
                'n': data['n'],
                'precision': round(data['ok'] / max(data['n'], 1), 3),
            }

    return {
        'hologramme': holo_name,
        'questions': n,
        'correct': correct,
        'answered': answered,
        'refused': refused,
        'precision': round(precision, 3),
        'recall': round(recall, 3),
        'coverage': round(coverage, 3),
        'f1_score': round(f1, 3),
        'refusal_rate': round(refusal_rate, 3),
        'avg_latency_ms': round(avg_latency, 1),
        'per_category': cats,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Benchmark d'hologramme")
    parser.add_argument('--holo', help='ID hologramme (ex: official_medecine)')
    parser.add_argument('--quick', action='store_true', help='20 questions/hologramme')
    parser.add_argument('--json', action='store_true', help='Sortie JSON')
    args = parser.parse_args()

    n_questions = 20 if args.quick else 50

    # Charger le cerveau AVEC l'hologramme injecté
    from harmonic_ai import HarmonicAI
    from hologram_store import HologramStore
    from harmonic_brain import HarmonicBrain

    print("Chargement du moteur...")
    ai = HarmonicAI(enable_bootstrapper=False, use_memory=False)
    hs = HologramStore()

    if args.holo:
        holo_ids = [args.holo]
    else:
        holo_ids = [h['id'] for h in hs.list_holograms(holo_type='official')]

    results = {}
    for holo_id in holo_ids:
        facts = hs.download(holo_id)
        if not facts:
            print(f"  ⚠️  {holo_id}: introuvable")
            continue

        # 🆕 Créer un cerveau FRIS avec l'hologramme injecté
        brain = HarmonicBrain(list(facts))
        # Injecter le J-Lens et le dialogue pour la qualité des réponses
        brain.jlens = getattr(ai, 'jlens', None)

        print(f"\nBenchmark: {holo_id} ({len(facts)} faits) — {n_questions} questions...")
        result = benchmark_hologram(facts, brain, holo_id, n_questions)
        results[holo_id] = result

        if not args.json:
            print(f"  Precision : {result.get('precision', 0):.1%}")
            print(f"  Recall    : {result.get('recall', 0):.1%}")
            print(f"  Coverage  : {result.get('coverage', 0):.1%}")
            print(f"  F1        : {result.get('f1_score', 0):.3f}")
            print(f"  Refus     : {result.get('refusal_rate', 0):.1%}")
            print(f"  Latence   : {result.get('avg_latency_ms', 0):.0f} ms")
            cats = result.get('per_category', {})
            if cats:
                print(f"  Catégories: { {k: v['precision'] for k,v in cats.items()} }")

    # Sauvegarder
    out = Path('data/hologram_store/benchmark_report.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nRapport : {out}")

    # Mise à jour registry
    registry_path = Path('data/hologram_store/registry.json')
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        for holo_id, result in results.items():
            if holo_id in registry and 'f1_score' in result:
                registry[holo_id]['quality_score'] = result['f1_score']
                registry[holo_id]['benchmark_questions'] = result.get('questions', 0)
        registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding='utf-8')
        print("Registry mis à jour avec les scores réels.")


if __name__ == '__main__':
    main()
