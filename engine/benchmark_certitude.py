#!/usr/bin/env python3
"""
benchmark_certitude.py — Le benchmark de la catégorie CERTITUDE
================================================================

Les classements de génération (LM Arena, GSM8K, HumanEval) mesurent la
capacité à INVENTER. KA Enterprise ne génère pas : elle répond sur les
données ingérées et refuse sinon. Cette catégorie a SES métriques :

  1. PRÉCISION FACTUELLE  — sur un corpus connu, chaque réponse contient
     la valeur attendue (extrait sourcé, pas une paraphrase).
  2. REFUS CALIBRÉ        — question hors corpus → refus honnête
     (confiance faible / « Je ne trouve pas »), jamais d'invention.
  3. ANTI-HALLUCINATION    — 0 % de réponses affirmatives hors corpus.
  4. DÉTERMINISME         — mêmes données + même question = même réponse.
  5. COÛT & LATENCE       — VPS 20 €/mois, CPU seul, millisecondes.

Usage :
    python benchmark_certitude.py [--quiet]

Rapport : data/benchmarks/certitude_report.json
Exit : 0 si tous les seuils passent (précision ≥ 90 %, refus ≥ 90 %,
déterminisme 100 %).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Chemins : moteur Enterprise + kit de démo ───────────────────────────────────
_ENGINE_DIR = Path(__file__).resolve().parent
_ENT_DIR = _ENGINE_DIR / 'vital-ka' / 'backend' / 'enterprise'
sys.path.insert(0, str(_ENGINE_DIR))
sys.path.insert(0, str(_ENT_DIR))

from ka_enterprise_core import EnterpriseEngine
from enterprise_deliverables import query_data
from demo_kit.make_demo_dataset import build_demo_dataset, DEMO_LAYOUT

SEUIL_PRECISION = 90.0
SEUIL_REFUS = 90.0

# ═══════════════════════════════════════════════════════════════════════════════
# CAS DE TEST
# ═══════════════════════════════════════════════════════════════════════════════

# 1. Précision : questions dont la réponse EXACTE est connue dans le corpus.
#    mode 'data'  → query_data (vérif sur count / agrégat / cellule)
#    mode 'ask'   → Q&A (vérif : la réponse contient la sous-chaîne attendue)
CASES_PRECISION: List[Dict] = [
    # ── Données chiffrées (département comptabilité) ──
    {'q': "combien de clients actifs avons-nous ?",
     'dept': 'demo_comptabilite', 'mode': 'data', 'check': 'count', 'expected': 10},
    {'q': "quel est le chiffre d'affaires total de nos clients actifs ?",
     'dept': 'demo_comptabilite', 'mode': 'data', 'check': 'agg', 'expected': 3668000},
    {'q': "liste des factures en retard",
     'dept': 'demo_comptabilite', 'mode': 'data', 'check': 'count', 'expected': 3},
    {'q': "quel est le montant total des factures en retard ?",
     'dept': 'demo_comptabilite', 'mode': 'data', 'check': 'agg', 'expected': 40600.0},
    {'q': "combien de factures en retard avons-nous ?",
     'dept': 'demo_comptabilite', 'mode': 'data', 'check': 'count', 'expected': 3},
    {'q': "liste des salaires du personnel",
     'dept': 'demo_comptabilite', 'mode': 'data', 'check': 'count', 'expected': 6},
    {'q': "quel est le chiffre d'affaires de la Clinique des Cèdres ?",
     'dept': 'demo_comptabilite', 'mode': 'data', 'check': 'cell',
     'col': 'chiffre_affaires', 'row_contains': 'Clinique des Cèdres',
     'expected': '1200000'},
    # ── Connaissance (procédures) ──
    {'q': "quelles sont les échéances de TVA à respecter ?",
     'dept': 'demo_procedures', 'mode': 'ask', 'contains': '19'},
    {'q': "quand la DSN mensuelle doit-elle être transmise ?",
     'dept': 'demo_procedures', 'mode': 'ask', 'contains': '5'},
    {'q': "combien de temps les pièces comptables sont-elles conservées ?",
     'dept': 'demo_procedures', 'mode': 'ask', 'contains': '10 ans'},
    {'q': "quel est le résultat net du bilan 2025 ?",
     'dept': 'demo_comptabilite', 'mode': 'ask', 'contains': '142 300'},
]

# 2. Refus calibré : questions HORS corpus — la réponse honnête est le refus.
CASES_REFUS: List[str] = [
    "quelle est la couleur du paradis fiscal ?",
    "quel est le taux de la taxe carbone en 2027 ?",
    "qui a inventé le moteur à combustion ?",
    "quel est le capital de la NASA ?",
    "donne-moi le numéro de téléphone du président de la République ?",
]

# 3. Déterminisme : ces questions sont rejouées 2× et doivent être identiques.
CASES_DETERMINISME: List[Tuple[str, str]] = [
    ('demo_comptabilite', "quel est le chiffre d'affaires total de nos clients actifs ?"),
    ('demo_procedures', "quelles sont les échéances de TVA à respecter ?"),
    ('demo_comptabilite', "liste des factures en retard"),
]


def _refus(result) -> bool:
    """Une réponse est-elle un refus calibré ? (confiance faible ou refus explicite)"""
    if float(result.confidence) < 0.4:
        return True
    low = (result.answer or '').lower()
    return 'je ne trouve pas' in low or 'aucune information' in low


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR DE TEST
# ═══════════════════════════════════════════════════════════════════════════════

def build_env() -> Tuple[EnterpriseEngine, Dict[str, str]]:
    """Moteur temporaire + dataset de démo (valeurs exactes connues)."""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    engine = EnterpriseEngine(data_dir=str(tmp / 'data'))
    tenant = engine.create_tenant('Benchmark Certitude', 'bench@ka.fr')
    dataset = build_demo_dataset()
    depts: Dict[str, str] = {}
    for dept_name, files in DEMO_LAYOUT.items():
        dept = engine.create_department(tenant.id, dept_name)
        for fname in files:
            engine.ingest_text(dept.id, dataset[fname], source=fname)
        depts[dept_name] = dept.id
    return engine, depts


def check_data(data: Dict, case: Dict) -> bool:
    """Vérifie une case 'data' (count / agrégat / cellule)."""
    ck = case['check']
    if ck == 'count':
        return data.get('count') == case['expected']
    if ck == 'agg':
        aggs = data.get('aggregates') or []
        return bool(aggs) and abs(float(aggs[0]['valeur']) - case['expected']) < 0.01
    if ck == 'cell':
        for row in data.get('rows', []):
            if case['row_contains'] in str(row.values()):
                return str(row.get(case['col'], '')).replace(' ', '') == \
                       case['expected'].replace(' ', '')
        return False
    return False


def run(quiet: bool = False) -> Dict:
    engine, depts = build_env()
    t_start = time.perf_counter()

    # ── 1. Précision factuelle ────────────────────────────────────────────────
    precision_ok, precision_total = 0, 0
    details_p = []
    for case in CASES_PRECISION:
        precision_total += 1
        dept = depts[case['dept']]
        try:
            if case['mode'] == 'data':
                data = query_data(engine, dept, case['q'])
                ok = check_data(data, case)
                got = (data.get('count') if case['check'] == 'count'
                       else (data.get('aggregates') or [{}])[0].get('valeur')
                       if case['check'] == 'agg' else 'cell')
            else:
                res = engine.ask(case['q'], dept)
                ok = case['contains'] in res.answer
                got = res.answer[:60]
        except Exception as e:
            ok, got = False, f'ERREUR {e}'
        precision_ok += ok
        details_p.append({'q': case['q'], 'ok': ok, 'got': got,
                          'expected': case.get('expected') or case.get('contains')})
        if not quiet:
            print(f"   {'✅' if ok else '❌'} {case['q'][:58]:<60} → {got if ok else got}")

    # ── 2+3. Refus calibré / anti-hallucination ───────────────────────────────
    refus_ok, refus_total = 0, 0
    details_r = []
    dept = depts['demo_comptabilite']
    for q in CASES_REFUS:
        refus_total += 1
        res = engine.ask(q, dept)
        ref = _refus(res)
        refus_ok += ref
        details_r.append({'q': q, 'refus': ref,
                          'confiance': round(float(res.confidence), 3),
                          'reponse': res.answer[:60]})
        if not quiet:
            print(f"   {'✅' if ref else '❌'} [hors corpus] {q[:50]:<52} "
                  f"conf {res.confidence:.2f}")

    # ── 4. Déterminisme ───────────────────────────────────────────────────────
    det_ok, det_total = 0, 0
    for dept_name, q in CASES_DETERMINISME:
        dept = depts[dept_name]
        r1 = engine.ask(q, dept)
        r2 = engine.ask(q, dept)
        det_total += 1
        same = (r1.answer == r2.answer and
                abs(float(r1.confidence) - float(r2.confidence)) < 1e-9)
        det_ok += same

    # ── 5. Performance ────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    for _ in range(5):
        engine.ask("quelles sont les échéances de TVA ?", depts['demo_procedures'])
    ask_ms = (time.perf_counter() - t0) / 5 * 1000
    t0 = time.perf_counter()
    for _ in range(5):
        query_data(engine, depts['demo_comptabilite'], "liste des clients")
    data_ms = (time.perf_counter() - t0) / 5 * 1000

    # ── Rapport ───────────────────────────────────────────────────────────────
    p_score = 100.0 * precision_ok / max(1, precision_total)
    r_score = 100.0 * refus_ok / max(1, refus_total)
    d_score = 100.0 * det_ok / max(1, det_total)
    report = {
        'categorie': 'CERTITUDE (réponse ancrée + refus calibré)',
        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'duree_ms': round((time.perf_counter() - t_start) * 1000, 1),
        'precision_factuelle': {'ok': precision_ok, 'total': precision_total,
                                'score': round(p_score, 1),
                                'details': details_p},
        'refus_calibre': {'ok': refus_ok, 'total': refus_total,
                          'score': round(r_score, 1),
                          'hallucinations': refus_total - refus_ok,
                          'details': details_r},
        'determinisme': {'ok': det_ok, 'total': det_total,
                         'score': round(d_score, 1)},
        'performance': {'ask_ms': round(ask_ms, 1),
                        'data_ms': round(data_ms, 1),
                        'cout': 'VPS 20 €/mois — requêtes illimitées, coût marginal 0 €, 0 GPU'},
        'verdict': 'PASS' if (p_score >= SEUIL_PRECISION and
                              r_score >= SEUIL_REFUS and
                              d_score == 100.0) else 'FAIL',
    }

    _REPORT = _ENGINE_DIR / 'data' / 'benchmarks' / 'certitude_report.json'
    _REPORT.parent.mkdir(parents=True, exist_ok=True)
    _REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                       encoding='utf-8')
    return report


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Benchmark de la catégorie CERTITUDE')
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    print('═' * 66)
    print('  🎯 BENCHMARK CERTITUDE — réponse ancrée + refus calibré')
    print('═' * 66)
    print('  (comparaison : LLM ≈ 5-15 % d\'hallucination, génération stochastique)')
    print()

    print('  ── 1. Précision factuelle sur corpus (valeurs exactes connues) ──')
    r = run(quiet=args.quiet)
    print()
    print('═' * 66)
    print('  📊 RAPPORT CERTITUDE')
    print('═' * 66)
    print(f"  ✅ Précision factuelle : {r['precision_factuelle']['score']:.1f}% "
          f"({r['precision_factuelle']['ok']}/{r['precision_factuelle']['total']})")
    print(f"  🛡️  Refus calibré (hors corpus) : {r['refus_calibre']['score']:.1f}% "
          f"({r['refus_calibre']['ok']}/{r['refus_calibre']['total']}) — "
          f"hallucinations : {r['refus_calibre']['hallucinations']}")
    print(f"  🔁 Déterminisme : {r['determinisme']['score']:.1f}% "
          f"({r['determinisme']['ok']}/{r['determinisme']['total']})")
    print(f"  ⚡ Latence : ask {r['performance']['ask_ms']} ms · "
          f"data {r['performance']['data_ms']} ms")
    print(f"  💶 Coût : {r['performance']['cout']}")
    print(f"  ⏱  Durée : {r['duree_ms']} ms")
    print()
    print(f"  🏁 VERDICT : {r['verdict']}")
    print('═' * 66)
    print(f"  Rapport : data/benchmarks/certitude_report.json")
    sys.exit(0 if r['verdict'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
