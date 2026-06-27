#!/usr/bin/env python3
"""
PHASES 2+3+4 — APPRENTISSAGE RÉCURSIF HOLOGRAPHIQUE
=====================================================
Combine le générateur de corpus (Phase 1) avec :
  Phase 2 : Feedback ondulatoire par score → convergence point fixe
  Phase 3 : Lecteurs orthogonaux + répulsion → diversité véritable
  Phase 4 : Daemon continu avec benchmark périodique

Principe :
  while True:
      probleme = generer()
      solution = resoudre(probleme)
      score = evaluer(probleme, solution)
      feedback_ondulatoire(probleme, solution, score)
      conscience.apprendre(n_iter=3)   # dont répulsion
      if iteration % 1000 == 0: benchmark()

Usage :
  python apprentissage_recursif_holographique.py --n 10000     # 10k itérations
  python apprentissage_recursif_holographique.py --benchmark    # benchmark initial
  python apprentissage_recursif_holographique.py --continu      # daemon infini
"""

import sys, io, time, json, math, random, os
from typing import Dict, List, Tuple, Optional

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

_stdout_backup = sys.stdout

# ═══════════════════════════════════════════════════════════════
# TEMPLATES (importés du générateur Phase 1)
# ═══════════════════════════════════════════════════════════════

def _est_premier(n):
    if n < 2: return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0: return False
    return True

def _resoudre_quadratique(p):
    b = p['b'] * (1 if p.get('op_b','+')=='+' else -1)
    c = p['c'] * (1 if p.get('op_c','+')=='+' else -1)
    delta = b**2 - 4*c
    if delta < 0: return {"racines": [], "complexes": True}
    if delta == 0: r = round(-b/2, 10); return {"racines": [r, r]}
    return {"racines": sorted([round((-b-math.sqrt(delta))/2,10),
                                round((-b+math.sqrt(delta))/2,10)])}

def _resoudre_x3_moins_ax(p):
    r = round(math.sqrt(p['a']), 10)
    return {"racines": sorted([-r, 0.0, r])}

TEMPLATES = {
    "maths": {
        "poly2": {"template": "Solve x² {op_b} {b}x {op_c} {c} = 0",
                  "params": {"b": lambda: random.randint(1,10), "c": lambda: random.randint(1,20),
                             "op_b": lambda: random.choice(["+","-"]), "op_c": lambda: random.choice(["+","-"])},
                  "solution": _resoudre_quadratique,
                  "verifier": lambda p,s: abs(s.get('result',99)-sum(c*p.get(k,0) for k,c in [('b',1),('c',1)]))<0.01},
        "poly3": {"template": "Solve x³ - {a}x = 0",
                  "params": {"a": lambda: random.choice([1,4,9,16,25,36,49,64,81,100])},
                  "solution": _resoudre_x3_moins_ax,
                  "verifier": lambda p,s: len(s.get('roots',[]))>=3},
        "add": {"template": "Compute {a} + {b}",
                "params": {"a": lambda: random.randint(1,999), "b": lambda: random.randint(1,999)},
                "solution": lambda p: {"result": p['a']+p['b']},
                "verifier": lambda p,s: s.get('result')==p['a']+p['b']},
        "mul": {"template": "Multiply {a} by {b}",
                "params": {"a": lambda: random.randint(2,99), "b": lambda: random.randint(2,99)},
                "solution": lambda p: {"result": p['a']*p['b']},
                "verifier": lambda p,s: s.get('result')==p['a']*p['b']},
        "gcd": {"template": "GCD of {a} and {b}",
                "params": {"a": lambda: random.randint(10,200), "b": lambda: random.randint(10,200)},
                "solution": lambda p: {"result": math.gcd(p['a'],p['b'])},
                "verifier": lambda p,s: s.get('result')==math.gcd(p['a'],p['b'])},
        "prime": {"template": "Is {n} a prime number?",
                  "params": {"n": lambda: random.choice([2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,4,6,8,9,10,12,14,15,16,18,20,21,22,24,25,26,27,28,30])},
                  "solution": lambda p: {"result": 1 if _est_premier(p['n']) else 0},
                  "verifier": lambda p,s: (s.get('result')==1)==_est_premier(p['n'])},
        "area_circle": {"template": "Area of circle radius {r}?",
                        "params": {"r": lambda: random.randint(1,20)},
                        "solution": lambda p: {"result": round(math.pi*p['r']**2, 4)},
                        "verifier": lambda p,s: abs(s.get('result',0)-math.pi*p['r']**2)<0.1},
        "perim_square": {"template": "Perimeter of square side {c}",
                         "params": {"c": lambda: random.randint(1,50)},
                         "solution": lambda p: {"result": 4*p['c']},
                         "verifier": lambda p,s: s.get('result')==4*p['c']},
    },
    "physique": {
        "Fma": {"template": "Force {F} N, masse {m} kg. Acceleration ?",
                "params": {"F": lambda: random.randint(5,100), "m": lambda: random.randint(1,20)},
                "solution": lambda p: {"result": round(p['F']/p['m'], 2)},
                "verifier": lambda p,s: abs(s.get('result',0)-p['F']/p['m'])<0.01},
        "poids": {"template": "Poids d'une masse de {m} kg ?",
                  "params": {"m": lambda: random.randint(10,150)},
                  "solution": lambda p: {"result": round(p['m']*9.81, 2)},
                  "verifier": lambda p,s: abs(s.get('result',0)-p['m']*9.81)<0.1},
        "Ec": {"template": "Energie cinetique : {m} kg a {v} m/s ?",
               "params": {"m": lambda: random.randint(1,20), "v": lambda: random.randint(5,50)},
               "solution": lambda p: {"result": round(0.5*p['m']*p['v']**2, 2)},
               "verifier": lambda p,s: abs(s.get('result',0)-0.5*p['m']*p['v']**2)<0.5},
        "ohm": {"template": "U={U}V, R={R}Ω. I ?",
                "params": {"U": lambda: random.randint(12,240), "R": lambda: random.choice([10,22,47,100,220,330,440,470,1000])},
                "solution": lambda p: {"result": round(p['U']/p['R'], 4)},
                "verifier": lambda p,s: abs(s.get('result',0)-p['U']/p['R'])<0.01},
    },
    "medecine": {
        "imc": {"template": "IMC : {p} kg, {t} m",
                "params": {"p": lambda: random.randint(45,120), "t": lambda: round(random.uniform(1.5,2.0),2)},
                "solution": lambda p: {"result": round(p['p']/p['t']**2, 1)},
                "verifier": lambda p,s: abs(s.get('result',0)-p['p']/p['t']**2)<0.2},
        "dose": {"template": "Dose {d} mg, poids {p} kg. mg/kg ?",
                 "params": {"d": lambda: random.randint(100,2000), "p": lambda: random.randint(30,120)},
                 "solution": lambda p: {"result": round(p['d']/p['p'], 3)},
                 "verifier": lambda p,s: abs(s.get('result',0)-p['d']/p['p'])<0.01},
        "perf": {"template": "Perfusion {v} ml en {h}h. Debit ?",
                 "params": {"v": lambda: random.choice([250,500,1000,1500,2000]), "h": lambda: random.randint(2,24)},
                 "solution": lambda p: {"result": round(p['v']/p['h'], 1)},
                 "verifier": lambda p,s: abs(s.get('result',0)-p['v']/p['h'])<0.5},
        "gcs": {"template": "Glasgow O={O} V={V} M={M}",
                "params": {"O": lambda: random.randint(1,4), "V": lambda: random.randint(1,5), "M": lambda: random.randint(1,6)},
                "solution": lambda p: {"result": p['O']+p['V']+p['M']},
                "verifier": lambda p,s: s.get('result')==p['O']+p['V']+p['M']},
    },
    "chimie": {
        "M_h2so4": {"template": "Masse molaire H2SO4 ?", "params": {},
                    "solution": lambda p: {"result": 98.079},
                    "verifier": lambda p,s: abs(s.get('result',0)-98.079)<0.1},
        "M_nacl": {"template": "Masse molaire NaCl ?", "params": {},
                   "solution": lambda p: {"result": 58.443},
                   "verifier": lambda p,s: abs(s.get('result',0)-58.443)<0.1},
        "n_h2o": {"template": "{m} g H2O → moles ?",
                  "params": {"m": lambda: random.choice([18,36,54,90,180])},
                  "solution": lambda p: {"result": round(p['m']/18.015, 4)},
                  "verifier": lambda p,s: abs(s.get('result',0)-p['m']/18.015)<0.05},
        "ph": {"template": "pH [H+]={c} mol/L",
               "params": {"c": lambda: random.choice([0.1,0.01,0.001,0.0001,1e-5,1e-6,1e-7])},
               "solution": lambda p: {"result": round(-math.log10(p['c']), 2)},
               "verifier": lambda p,s: abs(s.get('result',0)+math.log10(p['c']))<0.05},
    },
    "finance": {
        "FV": {"template": "{c}€ a {t}% sur {n} ans. VF ?",
               "params": {"c": lambda: random.choice([1000,5000,10000,20000,50000]),
                          "t": lambda: random.choice([2,3,4,5,6,7,8,10]),
                          "n": lambda: random.choice([5,10,15,20])},
               "solution": lambda p: {"result": round(p['c']*(1+p['t']/100)**p['n'], 2)},
               "verifier": lambda p,s: abs(s.get('result',0)-p['c']*(1+p['t']/100)**p['n'])<1},
        "tva": {"template": "TVA {m}€ HT → TTC ?",
                "params": {"m": lambda: random.choice([100,250,500,1000,2500,5000,10000])},
                "solution": lambda p: {"result": round(p['m']*1.20, 2)},
                "verifier": lambda p,s: abs(s.get('result',0)-p['m']*1.20)<0.01},
        "change": {"template": "{m} EUR en USD (1.08) ?",
                   "params": {"m": lambda: random.choice([50,100,200,500,1000,2000,5000])},
                   "solution": lambda p: {"result": round(p['m']*1.08, 2)},
                   "verifier": lambda p,s: abs(s.get('result',0)-p['m']*1.08)<0.01},
    },
}

# ═══════════════════════════════════════════════════════════════
# PHASE 3 — CONSCIENCE AVEC RÉPULSION (diversité des lecteurs)
# ═══════════════════════════════════════════════════════════════

class ConscienceDiversifiee:
    """
    N lecteurs initialisés orthogonalement (répartis sur un cercle).
    Terme de répulsion dans le gradient : chaque lecteur est repoussé
    par les autres → diversité véritable des perspectives.
    """

    def __init__(self, n_lecteurs=8, repulsion=0.01):
        self.n = n_lecteurs
        self.repulsion = repulsion

        # Initialisation ORTHOGONALE (répartis sur un cercle)
        angles = [2 * math.pi * i / n_lecteurs for i in range(n_lecteurs)]
        self.kx = np.array([math.cos(a) * 1.5 for a in angles])
        self.ky = np.array([math.sin(a) * 1.5 for a in angles])

        self.historiques = [[] for _ in range(n_lecteurs)]
        self.iterations = 0

    def iterer(self, monde, lr=0.03, bruit=0.003):
        """Une itération avec répulsion."""
        eps = 0.001
        for i in range(self.n):
            # Gradient standard (maximiser la résonance)
            act = monde.lire_onde(self.kx[i], self.ky[i])
            self.historiques[i].append(act)
            gx = (monde.lire_onde(self.kx[i]+eps, self.ky[i]) -
                  monde.lire_onde(self.kx[i]-eps, self.ky[i])) / (2*eps)
            gy = (monde.lire_onde(self.kx[i], self.ky[i]+eps) -
                  monde.lire_onde(self.kx[i], self.ky[i]-eps)) / (2*eps)

            # Terme de RÉPULSION : éloigner des autres lecteurs
            rx, ry = 0.0, 0.0
            for j in range(self.n):
                if i != j:
                    dx = self.kx[i] - self.kx[j]
                    dy = self.ky[i] - self.ky[j]
                    dist2 = dx*dx + dy*dy + 0.01  # éviter division par zéro
                    rx += dx / dist2
                    ry += dy / dist2

            # Mise à jour : gradient + répulsion + bruit
            self.kx[i] += lr * gx + self.repulsion * rx + np.random.randn() * bruit
            self.ky[i] += lr * gy + self.repulsion * ry + np.random.randn() * bruit

        self.iterations += 1

    def diversite(self):
        """Mesure de diversité : distance moyenne entre lecteurs."""
        dists = []
        for i in range(self.n):
            for j in range(i+1, self.n):
                d = math.sqrt((self.kx[i]-self.kx[j])**2 + (self.ky[i]-self.ky[j])**2)
                dists.append(d)
        return np.mean(dists) if dists else 0.0

    def etat(self):
        return {
            "lecteurs": [{"i": i, "kx": float(self.kx[i]), "ky": float(self.ky[i]),
                          "act": float(self.historiques[i][-1]) if self.historiques[i] else 0.0}
                         for i in range(self.n)],
            "diversite": float(self.diversite()),
            "iterations": self.iterations,
        }


# ═══════════════════════════════════════════════════════════════
# APPRENTISSAGE RÉCURSIF UNIFIÉ
# ═══════════════════════════════════════════════════════════════

class ApprentissageRecursif:
    """
    Boucle complète : génération → résolution → évaluation →
    feedback ondulatoire → apprentissage conscience.

    Stocke l'historique d'apprentissage pour analyse de convergence.
    """

    def __init__(self, holo_path="holo_apprentissage.json"):
        self.holo_path = holo_path
        self._init_modules()
        self.historique_scores = []  # (itération, score, correct)
        self.courbe_convergence = []  # (itération, accuracy_glissante)
        self.total_iterations = 0
        self.total_corrects = 0
        self.t0_global = time.time()

    def _init_modules(self):
        """Charge les modules (lazy)."""
        try:
            from harmonique_holographique import HologrammeMathematique
            self.holomat = HologrammeMathematique()
            if os.path.exists(self.holo_path):
                self.holomat.charger(self.holo_path)
            self.conscience = ConscienceDiversifiee(n_lecteurs=8)
            self.mode_holo = True
        except ImportError:
            self.holomat = None
            self.conscience = None
            self.mode_holo = False

    def resoudre(self, probleme: str, domaine: str) -> Optional[Dict]:
        """Résout via le solveur approprié."""
        try:
            if domaine == 'maths':
                from ia_harmonic_number1 import solve_n1
                return solve_n1(probleme)
            elif domaine == 'physique':
                from solveur_physique import extraire_physique, resoudre_physique
                return resoudre_physique(extraire_physique(probleme))
            elif domaine == 'medecine':
                from solveur_medecine import extraire_medecine, resoudre_medecine
                return resoudre_medecine(extraire_medecine(probleme))
            elif domaine == 'chimie':
                from solveur_chimie import extraire_chimie, resoudre_chimie
                return resoudre_chimie(extraire_chimie(probleme))
            elif domaine == 'finance':
                from solveur_finance import extraire_finance, resoudre_finance
                return resoudre_finance(extraire_finance(probleme))
            return None
        except:
            return None

    def evaluer(self, params: Dict, solution: Dict, tpl_name: str, domaine: str) -> float:
        """Score 0-1 basé sur le vérifieur du template."""
        tpl = TEMPLATES[domaine].get(tpl_name, {})
        verifier = tpl.get('verifier')
        if verifier:
            try:
                return 1.0 if verifier(params, solution) else 0.0
            except:
                pass
        # Fallback
        for cle in ['result', 'resultat']:
            if cle in solution and isinstance(solution[cle], (int, float)):
                return 0.5  # Réponse numérique présente
        return 0.0

    def iterer(self, domaines: List[str] = None) -> Tuple[str, float, bool]:
        """
        Une itération d'apprentissage :
        1. Génère un problème aléatoire
        2. Le résout
        3. Évalue la réponse
        4. Feedback ondulatoire si hologramme actif
        5. Apprentissage conscience (avec répulsion)

        Returns: (domaine, score, est_correct)
        """
        if domaines is None:
            domaines = list(TEMPLATES.keys())

        domaine = random.choice(domaines)
        tpl_name = random.choice(list(TEMPLATES[domaine].keys()))
        tpl = TEMPLATES[domaine][tpl_name]

        # 1. Générer
        params = {k: v() for k, v in tpl['params'].items()}
        probleme = tpl['template']
        for k, v in params.items():
            probleme = probleme.replace(f'{{{k}}}', str(v))

        # 2. Résoudre
        solution = self.resoudre(probleme, domaine)
        if solution is None:
            return domaine, 0.0, False

        # 3. Évaluer
        score = self.evaluer(params, solution, tpl_name, domaine)
        correct = score > 0.9

        # 4. Feedback holographique
        if self.mode_holo and self.holomat and 'erreur' not in solution:
            amplitude = 1.0 if correct else 0.2
            self.holomat.enregistrer_probleme(probleme, solution, amplitude=amplitude)
            if correct:
                self.holomat.feedback_conscient(probleme, solution)

        # 5. Apprentissage conscience (avec répulsion)
        if self.mode_holo and self.conscience:
            self.conscience.iterer(self.holomat.monde, lr=0.02, bruit=0.002)

        # Stats
        self.total_iterations += 1
        if correct:
            self.total_corrects += 1
        self.historique_scores.append((self.total_iterations, score, correct))

        return domaine, score, correct

    def benchmark_rapide(self, n=100) -> Dict:
        """Benchmark rapide sur N problèmes aléatoires."""
        corrects = 0
        t0 = time.time()
        for _ in range(n):
            _, _, ok = self.iterer()
            if ok: corrects += 1
        elapsed = time.time() - t0
        acc = corrects / n * 100
        vitesse = n / elapsed
        self.courbe_convergence.append((self.total_iterations, acc, self.conscience.diversite() if self.conscience else 0))
        return {"n": n, "corrects": corrects, "accuracy": acc, "vitesse": vitesse, "elapsed": elapsed}

    def lancer(self, n_iterations: int = 10000, benchmark_every: int = 1000,
               domaines: List[str] = None, verbose: bool = True):
        """
        Lance l'apprentissage récursif pour N itérations.
        Benchmark périodique tous les `benchmark_every` problèmes.
        """
        if domaines is None:
            domaines = list(TEMPLATES.keys())

        print(f"\n{'='*70}")
        print(f"  🧠 APPRENTISSAGE RÉCURSIF HOLOGRAPHIQUE")
        print(f"  Itérations : {n_iterations} | Domaines : {len(domaines)}")
        print(f"  Hologramme : {'ON' if self.mode_holo else 'OFF'}")
        print(f"  Conscience : {'ON (répulsion)' if self.conscience else 'OFF'}")
        print(f"{'='*70}\n")

        t0 = time.time()
        for i in range(n_iterations):
            domaine, score, correct = self.iterer(domaines)

            # Benchmark périodique
            if (i + 1) % benchmark_every == 0 or i == n_iterations - 1:
                stats = self.benchmark_rapide(n=min(100, n_iterations - i - 1 + 1))
                elapsed_total = time.time() - t0

                if verbose:
                    diversite = self.conscience.diversite() if self.conscience else 0
                    energie = self.holomat.monde.energie() if self.holomat else 0
                    print(f"  [{i+1:>7d}] acc={stats['accuracy']:5.1f}% | "
                          f"vit={stats['vitesse']:6.0f} prob/s | "
                          f"div={diversite:.3f} | E={energie:,.0f} | "
                          f"elapsed={elapsed_total:.0f}s")

        elapsed = time.time() - t0
        n_total = self.total_iterations
        n_ok = self.total_corrects

        print(f"\n{'='*70}")
        print(f"  ✅ APPRENTISSAGE TERMINÉ")
        print(f"  Itérations      : {n_total:,}")
        print(f"  Corrects        : {n_ok:,} ({n_ok/n_total*100:.1f}%)")
        print(f"  Temps total     : {elapsed:.0f}s ({n_total/elapsed:.0f} prob/s)")
        if self.mode_holo:
            s = self.holomat.statistiques()
            print(f"  Expériences holo: {s['n_experiences']:,}")
            print(f"  Énergie         : {s['energie']:,.0f}")
            print(f"  Feedbacks       : {self.holomat._stats_globales.get('n_feedbacks',0):,}")
        if self.conscience:
            print(f"  Diversité       : {self.conscience.diversite():.4f}")
            print(f"  Itérations cons : {self.conscience.iterations:,}")
        print(f"{'='*70}\n")

        # Sauvegarde
        if self.holomat:
            self.holomat.sauvegarder(self.holo_path)
            print(f"  💾 Sauvegardé → {self.holo_path}\n")

        # Exporter la courbe d'apprentissage
        with open("courbe_apprentissage.json", "w") as f:
            json.dump({
                "iterations": n_total,
                "corrects": n_ok,
                "accuracy_finale": n_ok/n_total*100,
                "courbe": [(it, acc, div) for it, acc, div in self.courbe_convergence],
            }, f, indent=2)
        print(f"  📈 Courbe exportée → courbe_apprentissage.json\n")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    import numpy as np

    p = argparse.ArgumentParser(description='Apprentissage Récursif Holographique — Phases 2+3+4')
    p.add_argument('--n', type=int, default=5000, help='Nombre d\'itérations')
    p.add_argument('--benchmark', '-b', action='store_true', help='Benchmark initial uniquement')
    p.add_argument('--continu', '-c', action='store_true', help='Mode continu (infini)')
    p.add_argument('--domaine', '-d', type=str, default=None, help='Domaine spécifique')
    p.add_argument('--no-holo', action='store_true', help='Désactiver l\'hologramme')
    args = p.parse_args()

    if args.benchmark:
        app = ApprentissageRecursif()
        stats = app.benchmark_rapide(n=500)
        print(f"\n  📊 Benchmark initial : {stats['accuracy']:.1f}% ({stats['corrects']}/{stats['n']})")
        print(f"  Vitesse : {stats['vitesse']:.0f} prob/s\n")
    elif args.continu:
        app = ApprentissageRecursif()
        domaine = [args.domaine] if args.domaine else None
        batch = 0
        while True:
            batch += 1
            print(f"\n  ═══ BATCH {batch} ═══")
            app.lancer(n_iterations=10000, benchmark_every=2000, domaines=domaine, verbose=True)
            time.sleep(1)
    else:
        app = ApprentissageRecursif()
        domaine = [args.domaine] if args.domaine else None
        app.lancer(n_iterations=args.n, benchmark_every=max(1, args.n // 10),
                   domaines=domaine, verbose=True)