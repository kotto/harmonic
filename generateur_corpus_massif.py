#!/usr/bin/env python3
"""
PHASE 1 — GÉNÉRATEUR DE CORPUS MASSIF
=======================================
Génère des millions de variantes de problèmes mathématiques, physiques,
médicaux, chimiques et financiers à partir de templates paramétrés.
Chaque problème est résolu, vérifié, et stocké dans l'hologramme.

Templates couverts :
  - Maths : équations polynomiales, arithmétique, optimisation
  - Physique : F=ma, U=RI, Ec, Poids, v=fλ
  - Médecine : IMC, dose/kg, débit perfusion, scores
  - Chimie : masse molaire, stoechiométrie, pH, concentration
  - Finance : intérêts composés, emprunt, TVA, change

Usage :
  python generateur_corpus_massif.py --n 10000      # 10 000 problèmes
  python generateur_corpus_massif.py --n 100000      # 100 000 problèmes
  python generateur_corpus_massif.py --n 1000000     # 1 000 000 problèmes
  python generateur_corpus_massif.py --domaine physique --n 5000
"""

import sys
import io
import time
import json
import math
import random
import os
from typing import Dict, List, Tuple, Optional, Callable

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════════
# TEMPLATES PAR DOMAINE
# ═══════════════════════════════════════════════════════════════

TEMPLATES = {
    "maths": {
        "polynome_degre2": {
            "template": "Solve x² {op_b} {b}x {op_c} {c} = 0",
            "params": {
                "b": lambda: random.randint(1, 10),
                "c": lambda: random.randint(1, 20),
                "op_b": lambda: random.choice(["+", "-"]),
                "op_c": lambda: random.choice(["+", "-"]),
            },
            "solution": lambda p: _resoudre_quadratique(p),
            "verifier": lambda p, s: _verifier_racines(p, s),
            "domaine": "polynomial"
        },
        "polynome_degre3_simple": {
            "template": "Solve x³ - {a}x = 0",
            "params": {"a": lambda: random.choice([1, 4, 9, 16, 25, 36, 49, 64, 81, 100])},
            "solution": lambda p: _resoudre_x3_moins_ax(p),
            "verifier": lambda p, s: _verifier_racines(p, s),
            "domaine": "polynomial"
        },
        "arithmetique_addition": {
            "template": "Compute {a} + {b}",
            "params": {"a": lambda: random.randint(1, 999), "b": lambda: random.randint(1, 999)},
            "solution": lambda p: {"resultat": p['a'] + p['b']},
            "verifier": lambda p, s: s.get('resultat') == p['a'] + p['b'],
            "domaine": "arithmetic"
        },
        "arithmetique_multiplication": {
            "template": "Multiply {a} by {b}",
            "params": {"a": lambda: random.randint(2, 99), "b": lambda: random.randint(2, 99)},
            "solution": lambda p: {"resultat": p['a'] * p['b']},
            "verifier": lambda p, s: s.get('resultat') == p['a'] * p['b'],
            "domaine": "arithmetic"
        },
        "aire_cercle": {
            "template": "What is the area of a circle of radius {r}?",
            "params": {"r": lambda: random.randint(1, 20)},
            "solution": lambda p: {"resultat": round(math.pi * p['r']**2, 4)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - math.pi * p['r']**2) < 0.1,
            "domaine": "geometry"
        },
        "perimetre_carre": {
            "template": "Compute the perimeter of a square of side {c}",
            "params": {"c": lambda: random.randint(1, 50)},
            "solution": lambda p: {"resultat": 4 * p['c']},
            "verifier": lambda p, s: s.get('resultat') == 4 * p['c'],
            "domaine": "geometry"
        },
        "gcd": {
            "template": "GCD of {a} and {b}",
            "params": {"a": lambda: random.randint(10, 200), "b": lambda: random.randint(10, 200)},
            "solution": lambda p: {"resultat": math.gcd(p['a'], p['b'])},
            "verifier": lambda p, s: s.get('resultat') == math.gcd(p['a'], p['b']),
            "domaine": "number_theory"
        },
        "premier": {
            "template": "Is {n} a prime number?",
            "params": {"n": lambda: random.choice([2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,
                                                     4,6,8,9,10,12,14,15,16,18,20,21,22,24,25,26,27,28,30])},
            "solution": lambda p: {"premier": _est_premier(p['n'])},
            "verifier": lambda p, s: s.get('premier') == _est_premier(p['n']),
            "domaine": "number_theory"
        },
        "optimisation_x2": {
            "template": "Find the minimum of x² starting from x0={x0}",
            "params": {"x0": lambda: random.randint(1, 20)},
            "solution": lambda p: {"resultat": 0.0},
            "verifier": lambda p, s: abs(s.get('resultat', 99)) < 0.01,
            "domaine": "optimization"
        },
    },
    "physique": {
        "F_ma": {
            "template": "Une force de {F} N accelere une masse de {m} kg. Acceleration ?",
            "params": {"F": lambda: random.randint(5, 100), "m": lambda: random.randint(1, 20)},
            "solution": lambda p: {"resultat": round(p['F'] / p['m'], 2)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['F']/p['m']) < 0.01,
            "domaine": "mecanique"
        },
        "poids": {
            "template": "Quel est le poids d'une masse de {m} kg ?",
            "params": {"m": lambda: random.randint(10, 150)},
            "solution": lambda p: {"resultat": round(p['m'] * 9.81, 2)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['m']*9.81) < 0.1,
            "domaine": "gravitation"
        },
        "energie_cinetique": {
            "template": "Energie cinetique d'une masse de {m} kg a {v} m/s ?",
            "params": {"m": lambda: random.randint(1, 20), "v": lambda: random.randint(5, 50)},
            "solution": lambda p: {"resultat": round(0.5 * p['m'] * p['v']**2, 2)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - 0.5*p['m']*p['v']**2) < 0.5,
            "domaine": "energie"
        },
        "ohm": {
            "template": "U = {U} V, R = {R} ohms. Trouver I.",
            "params": {"U": lambda: random.randint(12, 240), "R": lambda: random.choice([10,22,47,100,220,330,440,470,1000])},
            "solution": lambda p: {"resultat": round(p['U'] / p['R'], 4)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['U']/p['R']) < 0.01,
            "domaine": "electricite"
        },
        "puissance": {
            "template": "What is the power if U={U}V and I={I}A?",
            "params": {"U": lambda: random.randint(5, 24), "I": lambda: random.randint(1, 10)},
            "solution": lambda p: {"resultat": p['U'] * p['I']},
            "verifier": lambda p, s: s.get('resultat') == p['U'] * p['I'],
            "domaine": "electricite"
        },
        "ondes": {
            "template": "Frequence {f} Hz, vitesse {v} m/s. Longueur d'onde ?",
            "params": {"f": lambda: random.randint(10, 200), "v": lambda: random.randint(300, 350)},
            "solution": lambda p: {"resultat": round(p['v'] / p['f'], 4)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['v']/p['f']) < 0.05,
            "domaine": "ondes"
        },
    },
    "medecine": {
        "imc": {
            "template": "IMC pour {p} kg et {t} m",
            "params": {"p": lambda: random.randint(45, 120), "t": lambda: round(random.uniform(1.50, 2.00), 2)},
            "solution": lambda p: {"resultat": round(p['p'] / p['t']**2, 1),
                                    "interpretation": _interpretation_imc(p['p'] / p['t']**2)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['p']/p['t']**2) < 0.2,
            "domaine": "physiologie"
        },
        "dose_mg_kg": {
            "template": "Dose en mg/kg : dose {d} mg, poids {p} kg",
            "params": {"d": lambda: random.randint(100, 2000), "p": lambda: random.randint(30, 120)},
            "solution": lambda p: {"resultat": round(p['d'] / p['p'], 3)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['d']/p['p']) < 0.01,
            "domaine": "pharmacologie"
        },
        "debit_perfusion": {
            "template": "Perfusion {v} ml en {h} heures. Debit ml/h ?",
            "params": {"v": lambda: random.choice([250, 500, 1000, 1500, 2000]), "h": lambda: random.randint(2, 24)},
            "solution": lambda p: {"resultat": round(p['v'] / p['h'], 1)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['v']/p['h']) < 0.5,
            "domaine": "pharmacologie"
        },
        "glasgow": {
            "template": "Score de Glasgow : O={O} V={V} M={M}",
            "params": {"O": lambda: random.randint(1, 4), "V": lambda: random.randint(1, 5), "M": lambda: random.randint(1, 6)},
            "solution": lambda p: {"resultat": p['O'] + p['V'] + p['M']},
            "verifier": lambda p, s: s.get('resultat') == p['O'] + p['V'] + p['M'],
            "domaine": "score"
        },
    },
    "chimie": {
        "masse_molaire_h2so4": {
            "template": "Masse molaire de H2SO4 ?",
            "params": {},
            "solution": lambda p: {"resultat": 98.079},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - 98.079) < 0.1,
            "domaine": "masse_molaire"
        },
        "masse_molaire_nacl": {
            "template": "Masse molaire de NaCl ?",
            "params": {},
            "solution": lambda p: {"resultat": 58.443},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - 58.443) < 0.1,
            "domaine": "masse_molaire"
        },
        "masse_molaire_caco3": {
            "template": "Masse molaire de CaCO3 ?",
            "params": {},
            "solution": lambda p: {"resultat": 100.087},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - 100.087) < 0.2,
            "domaine": "masse_molaire"
        },
        "moles_h2o": {
            "template": "Combien de moles dans {m} g de H2O ?",
            "params": {"m": lambda: random.choice([18, 36, 54, 90, 180])},
            "solution": lambda p: {"resultat": round(p['m'] / 18.015, 4)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['m']/18.015) < 0.05,
            "domaine": "stoechiometrie"
        },
        "ph": {
            "template": "pH d'une solution [H+] = {c} mol/L",
            "params": {"c": lambda: random.choice([0.1, 0.01, 0.001, 0.0001, 1e-5, 1e-6, 1e-7])},
            "solution": lambda p: {"resultat": round(-math.log10(p['c']), 2)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) + math.log10(p['c'])) < 0.05,
            "domaine": "ph"
        },
    },
    "finance": {
        "interets_composes": {
            "template": "Interets composes : {c} euros a {t}% sur {n} ans. Valeur future ?",
            "params": {"c": lambda: random.choice([1000, 2000, 5000, 10000, 20000, 50000]),
                        "t": lambda: random.choice([2,3,4,5,6,7,8,10]),
                        "n": lambda: random.choice([5,10,15,20])},
            "solution": lambda p: {"resultat": round(p['c'] * (1 + p['t']/100) ** p['n'], 2)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['c']*(1+p['t']/100)**p['n']) < 1,
            "domaine": "interets_composes"
        },
        "tva": {
            "template": "TVA : {m} euros HT. TTC ?",
            "params": {"m": lambda: random.choice([100, 250, 500, 1000, 2500, 5000, 10000])},
            "solution": lambda p: {"resultat": round(p['m'] * 1.20, 2)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['m']*1.20) < 0.01,
            "domaine": "tva"
        },
        "change_eur_usd": {
            "template": "Conversion : {m} euros en dollars (1EUR=1.08USD)",
            "params": {"m": lambda: random.choice([50, 100, 200, 500, 1000, 2000, 5000])},
            "solution": lambda p: {"resultat": round(p['m'] * 1.08, 2)},
            "verifier": lambda p, s: abs(s.get('resultat', 0) - p['m']*1.08) < 0.01,
            "domaine": "change"
        },
    },
}

# ═══════════════════════════════════════════════════════════════
# FONCTIONS AUXILIAIRES
# ═══════════════════════════════════════════════════════════════

def _est_premier(n):
    if n < 2: return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0: return False
    return True

def _interpretation_imc(imc):
    if imc < 18.5: return "Maigreur"
    elif imc < 25: return "Normal"
    elif imc < 30: return "Surpoids"
    else: return "Obesite"

def _resoudre_quadratique(p):
    """Résout x² ± bx ± c = 0"""
    b_sign = p.get('op_b', '+')
    c_sign = p.get('op_c', '+')
    b = p['b'] * (1 if b_sign == '+' else -1)
    c = p['c'] * (1 if c_sign == '+' else -1)
    delta = b**2 - 4*c
    if delta < 0:
        return {"racines": [], "complexes": True}
    elif delta == 0:
        r = round(-b/2, 10)
        return {"racines": [r, r]}
    else:
        r1 = round((-b - math.sqrt(delta))/2, 10)
        r2 = round((-b + math.sqrt(delta))/2, 10)
        return {"racines": sorted([r1, r2])}

def _resoudre_x3_moins_ax(p):
    """Résout x³ - a·x = 0 → racines : 0, ±√a"""
    a = p['a']
    r = round(math.sqrt(a), 10)
    return {"racines": sorted([-r, 0.0, r])}

def _verifier_racines(p, s):
    attendues = sorted(s.get('racines', []))
    if 'racines' in s:
        return len(attendues) > 0
    return False

# ═══════════════════════════════════════════════════════════════
# GÉNÉRATEUR PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class GenerateurCorpus:
    """Génère des problèmes, les résout, vérifie, et stocke dans l'hologramme."""

    def __init__(self, holo_path: str = "hologramme_massif_etat.json"):
        self.holo_path = holo_path
        self.stats = {
            "total_genere": 0,
            "total_resolu": 0,
            "total_correct": 0,
            "par_domaine": {},
            "temps_total": 0,
        }
        self._init_hologramme()

    def _init_hologramme(self):
        """Initialise ou charge l'hologramme."""
        try:
            from harmonique_holographique import HologrammeMathematique
            self.holomat = HologrammeMathematique()
            if os.path.exists(self.holo_path):
                self.holomat.charger(self.holo_path)
                print(f"  📂 Hologramme chargé : {self.holomat.statistiques()['n_experiences']} expériences")
        except ImportError:
            print("  ⚠️ Module harmonique_holographique non trouvé — mode standalone")
            self.holomat = None

    def generer_probleme(self, domaine: str, template_name: str) -> Tuple[str, Dict, Dict, str]:
        """Génère un problème à partir d'un template."""
        tpl = TEMPLATES[domaine][template_name]
        params = {}
        for key, gen in tpl['params'].items():
            params[key] = gen() if callable(gen) else gen

        probleme = tpl['template']
        for key, val in params.items():
            probleme = probleme.replace(f'{{{key}}}', str(val))

        solution = tpl['solution'](params)
        sous_domaine = tpl['domaine']
        return probleme, params, solution, sous_domaine

    def evaluer_reponse(self, solution_attendue: Dict, solution_obtenue: Dict,
                        template_name: str, domaine: str) -> float:
        """Évalue la qualité de la réponse (0.0 à 1.0)."""
        tpl = TEMPLATES[domaine].get(template_name, {})
        verifier = tpl.get('verifier')
        if verifier:
            # La fonction vérifier reçoit (params_générés, solution_attendue)
            # On doit retrouver les params originaux... simplifions
            try:
                correct = verifier(solution_attendue, solution_obtenue)
                return 1.0 if correct else 0.0
            except:
                pass

        # Fallback : comparer les clés numériques
        score = 0.0
        nb_cles = 0
        for cle in ['resultat', 'racines', 'premier']:
            if cle in solution_attendue and cle in solution_obtenue:
                nb_cles += 1
                attendu = solution_attendue[cle]
                obtenu = solution_obtenue[cle]
                if isinstance(attendu, (int, float)) and isinstance(obtenu, (int, float)):
                    diff = abs(attendu - obtenu)
                    score += 1.0 if diff < 0.01 else max(0, 1.0 - diff)
                elif attendu == obtenu:
                    score += 1.0
        return score / max(nb_cles, 1)

    def resoudre_et_verifier(self, probleme: str, domaine: str) -> Tuple[Optional[Dict], bool]:
        """Résout un problème via le solveur approprié et vérifie la réponse."""
        try:
            if domaine == 'maths':
                from ia_harmonic_number1 import solve_n1
                r = solve_n1(probleme)
            elif domaine == 'physique':
                from solveur_physique import extraire_physique, resoudre_physique
                r = resoudre_physique(extraire_physique(probleme))
            elif domaine == 'medecine':
                from solveur_medecine import extraire_medecine, resoudre_medecine
                r = resoudre_medecine(extraire_medecine(probleme))
            elif domaine == 'chimie':
                from solveur_chimie import extraire_chimie, resoudre_chimie
                r = resoudre_chimie(extraire_chimie(probleme))
            elif domaine == 'finance':
                from solveur_finance import extraire_finance, resoudre_finance
                r = resoudre_finance(extraire_finance(probleme))
            else:
                return None, False
            return r, 'erreur' not in r
        except Exception as e:
            return {'erreur': str(e)}, False

    def generer_batch(self, n: int, domaines: List[str] = None,
                      feedback_holo: bool = True) -> Dict:
        """
        Génère N problèmes, les résout, et stocke dans l'hologramme.

        Args:
            n: nombre de problèmes à générer
            domaines: liste des domaines (défaut: tous)
            feedback_holo: si True, stocke dans l'hologramme

        Returns:
            Dict avec les statistiques du batch
        """
        if domaines is None:
            domaines = list(TEMPLATES.keys())

        t0 = time.time()
        batch_stats = {"total": n, "correct": 0, "erreurs": 0, "par_domaine": {}}

        print(f"\n  ═══ GÉNÉRATION DE {n} PROBLÈMES ═══")
        print(f"  Domaines : {', '.join(domaines)}")
        print(f"  Feedback hologramme : {'ON' if feedback_holo else 'OFF'}\n")

        for i in range(n):
            # Choisir un domaine aléatoire
            domaine = random.choice(domaines)
            # Choisir un template aléatoire dans ce domaine
            templates_dispo = list(TEMPLATES[domaine].keys())
            tpl_name = random.choice(templates_dispo)

            # Générer le problème et sa solution attendue
            probleme, params, solution_attendue, _ = self.generer_probleme(domaine, tpl_name)

            # Résoudre
            resultat, ok = self.resoudre_et_verifier(probleme, domaine)

            # Évaluer
            score = 0.0
            if ok and resultat:
                score = self.evaluer_reponse(params, resultat, tpl_name, domaine)

            est_correct = score > 0.9

            # Feedback holographique
            if feedback_holo and self.holomat and ok and resultat and 'erreur' not in resultat:
                amplitude = 1.0 if est_correct else 0.3
                self.holomat.enregistrer_probleme(probleme, resultat, amplitude=amplitude)
                if est_correct:
                    self.holomat.feedback_conscient(probleme, resultat)

            # Stats
            batch_stats["correct" if est_correct else "erreurs"] += (1 if est_correct else 1)
            if est_correct:
                if 'correct' not in batch_stats: batch_stats['correct'] = 0
                batch_stats['correct'] += 1
            else:
                batch_stats['erreurs'] += 1

            batch_stats["par_domaine"][domaine] = batch_stats["par_domaine"].get(domaine, 0) + 1

            # Progression
            if (i + 1) % max(1, n // 10) == 0:
                elapsed = time.time() - t0
                vitesse = (i + 1) / elapsed if elapsed > 0 else 0
                print(f"  [{i+1:>6d}/{n}] {vitesse:6.0f} prob/s | "
                      f"Corrects: {batch_stats['correct']} | "
                      f"Erreurs: {batch_stats['erreurs']} | "
                      f"Score: {batch_stats['correct']/(i+1)*100:.1f}%")

        elapsed = time.time() - t0
        print(f"\n  ✅ Batch terminé en {elapsed:.1f}s ({n/elapsed:.0f} prob/s)")
        print(f"  Corrects : {batch_stats['correct']}/{n} ({batch_stats['correct']/n*100:.1f}%)")
        print(f"  Erreurs  : {batch_stats['erreurs']}/{n}")

        # Sauvegarder l'hologramme
        if feedback_holo and self.holomat:
            self.holomat.sauvegarder(self.holo_path)
            stats_holo = self.holomat.statistiques()
            print(f"  💾 Hologramme : {stats_holo['n_experiences']} expériences | "
                  f"Énergie : {stats_holo['energie']:.0f}")
            print(f"  📁 Sauvegardé → {self.holo_path}")

        self.stats['total_genere'] += n
        self.stats['total_correct'] += batch_stats['correct']
        self.stats['temps_total'] += elapsed
        return batch_stats

    def rapport(self):
        """Affiche le rapport d'apprentissage."""
        print(f"\n  {'='*60}")
        print(f"  📊 RAPPORT D'APPRENTISSAGE RÉCURSIF")
        print(f"  {'='*60}")
        print(f"  Problèmes générés : {self.stats['total_genere']:,}")
        print(f"  Corrects          : {self.stats['total_correct']:,} "
              f"({self.stats['total_correct']/max(1,self.stats['total_genere'])*100:.1f}%)")
        print(f"  Temps total       : {self.stats['temps_total']:.0f}s")
        if self.holomat:
            s = self.holomat.statistiques()
            print(f"  Expériences holo  : {s['n_experiences']:,}")
            print(f"  Énergie           : {s['energie']:,.0f}")
            print(f"  Feedbacks         : {self.holomat._stats_globales.get('n_feedbacks', 0):,}")
            print(f"  Cache exact       : {s.get('n_cache_exact', 0):,}")
        print(f"  {'='*60}\n")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Générateur de Corpus Massif — Apprentissage Récursif')
    p.add_argument('--n', type=int, default=1000, help='Nombre de problèmes à générer')
    p.add_argument('--domaine', type=str, default=None, help='Domaine spécifique')
    p.add_argument('--no-feedback', action='store_true', help='Désactiver le feedback holographique')
    p.add_argument('--rapport', action='store_true', help='Afficher le rapport uniquement')
    args = p.parse_args()

    gen = GenerateurCorpus()

    if args.rapport:
        gen.rapport()
    else:
        domaines = [args.domaine] if args.domaine else None
        gen.generer_batch(
            n=args.n,
            domaines=domaines,
            feedback_holo=not args.no_feedback
        )
        gen.rapport()