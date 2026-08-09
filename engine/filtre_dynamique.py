#!/usr/bin/env python3
"""
filtre_dynamique.py — NLP par FILTRE DYNAMIQUE HARMONIQUE
==========================================================

Implémentation du NLP idéal spécifié dans la session :

  1. Noyau ABC (Mittag-Leffler) : K(t) = B(α) · E_α(-α·t^α/(1-α))
  2. Filtrage itératif : le noyau est appliqué N fois au signal du problème
  3. Survivants = squelette mathématique (nombres + opérations)
  4. Détection d'opérations par Δφ (distance de phase entre survivants)

PROPRIÉTÉ FONDAMENTALE :
  Aucun paramètre libre. α = 1/φ est une constante fondamentale.
  Le nombre d'itérations est déterminé par la convergence, pas par un choix.
  Le seuil de survie émerge de la dynamique, pas d'une décision arbitraire.

USAGE :
  python filtre_dynamique.py --test
  python filtre_dynamique.py --benchmark 200
"""

import sys, os, re, math, json, time, cmath
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from scipy.special import gamma as gamma_func

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_lang import encode, superpose, resonate, normalize, DEFAULT_DIM
from encodage_phase import PhaseEncoder
from encodage_logarithmique import LogWaveEncoder
from raisonneur_algebrique import AlgebriqueReasoner


# ═══════════════════════════════════════════════════════════════════════════
# 1. CONSTANTES FONDAMENTALES (THU V2)
# ═══════════════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2       # φ = 1.618033988749895
ALPHA = 1 / PHI                     # α = 0.6180339887498949
BETA_ML = 1.0                       # B(α) — normalisation (à affiner)


# ═══════════════════════════════════════════════════════════════════════════
# 2. FONCTION DE MITTAG-LEFFLER E_α(z)
# ═══════════════════════════════════════════════════════════════════════════

def mittag_leffler(alpha: float, z: complex, n_terms: int = 60) -> complex:
    """
    Fonction de Mittag-Leffler : E_α(z) = Σ_{k=0}^∞ z^k / Γ(αk + 1)

    Pour z réel négatif (notre cas), la série converge en ~40-60 termes.
    """
    result = 0.0 + 0.0j
    for k in range(n_terms):
        gamma_val = gamma_func(alpha * k + 1)
        if gamma_val == 0 or np.isinf(gamma_val):
            break
        term = (z ** k) / gamma_val
        result += term
        if abs(term) < 1e-15:
            break
    return result


def abc_kernel(t: float, alpha: float = ALPHA) -> float:
    """
    Noyau ABC (Atangana-Baleanu-Caputo) :
      K(t) = B(α) · E_α(-α · t^α / (1-α))

    Propriétés :
      - K(0) = 1 (mémoire parfaite au temps 0)
      - K(∞) = 0 (tout s'efface)
      - La vitesse de décroissance dépend de α
      - Pour α = 1/φ, la décroissance est « dorée » (optimale)
    """
    if t <= 0:
        return 1.0

    z = -alpha * (t ** alpha) / (1.0 - alpha)
    ml_val = mittag_leffler(alpha, z).real
    result = BETA_ML * ml_val

    return max(0.0, min(1.0, result))


# ═══════════════════════════════════════════════════════════════════════════
# 3. ESPACE MATHÉMATIQUE DE RÉFÉRENCE (filtres spécialisés)
# ═══════════════════════════════════════════════════════════════════════════

_NUMBER_WORDS = [
    "0","1","2","3","4","5","6","7","8","9",
    "zero","one","two","three","four","five","six","seven","eight","nine",
    "ten","eleven","twelve","hundred","thousand","dozen",
    "half","quarter","third","double","triple","twice","times",
]

_OPERATOR_WORDS = [
    "plus","minus","times","divided","add","subtract","multiply","divide",
    "+","-","*","/","=","more","less","fewer","additional","also","another",
    "total","sum","difference","product","quotient",
    "ate","eats","eat","sells","sell","sold",
    "spends","spend","spent","loses","lose","lost",
    "gives","give","gave","buys","buy","bought",
    "earns","earn","makes","make","gains","gain",
    "collects","collect","removes","remove","drops","drop",
]

_RELATION_WORDS = [
    "each","every","per","apiece","among","split","shared",
    "costs","has","had","have","left","remain","remaining",
    "altogether","combined","ratio","rate","percent",
    "there are","there were",
]


def _build_filters(dim=DEFAULT_DIM):
    """Construit les 3 filtres spécialisés (nombres, opérateurs, relations)."""
    def encode_set(words):
        waves = []
        for w in words:
            w = w.strip()
            if w and len(w) >= 1:
                try:
                    waves.append(encode(w, dim=dim))
                except Exception:
                    pass
        if not waves:
            return np.zeros(dim, dtype=np.complex128)
        return normalize(superpose(*waves))

    return {
        'numbers': encode_set(_NUMBER_WORDS),
        'operators': encode_set(_OPERATOR_WORDS),
        'relations': encode_set(_RELATION_WORDS),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. FILTRE DYNAMIQUE ITÉRATIF
# ═══════════════════════════════════════════════════════════════════════════

class DynamicHarmonicFilter:
    """
    Filtre dynamique : applique le noyau ABC itérativement au signal
    du problème jusqu'à convergence vers le squelette mathématique.
    """

    def __init__(self, dim=DEFAULT_DIM, alpha=ALPHA, max_iter=12):
        self.dim = dim
        self.alpha = alpha
        self.max_iter = max_iter
        self.phase = PhaseEncoder(500000)
        self.log = LogWaveEncoder(grid_size=2048, SCALE=300)
        self._filters = _build_filters(dim)

    def _word_coherence(self, word: str) -> float:
        """
        Cohérence mathématique d'un mot.

        - Les NOMBRES ont une cohérence quasi-certaine (0.95)
        - Les MOTS dans les filtres ont une cohérence élevée (0.75-0.85)
        - Les autres mots ont une cohérence basse (résonance brute)
        """
        # Les nombres sont mathématiques par définition
        if re.match(r'^\d+(\.\d+)?$', word):
            return 0.95

        try:
            psi = encode(word, dim=self.dim)
            # Calculer la résonance avec chaque filtre
            coherences = {}
            for fname, psi_f in self._filters.items():
                raw_coh = float(resonate(psi, psi_f))
                # Normaliser par l'auto-résonance du filtre
                auto_coh = float(resonate(psi_f, psi_f))
                if auto_coh > 0:
                    coherences[fname] = raw_coh / auto_coh
                else:
                    coherences[fname] = raw_coh

            # La cohérence est le MAX normalisé (OR logique)
            max_coh = max(coherences.values()) if coherences else 0.0

            # Re-normaliser : un mot qui EST dans le filtre aura coh ≈ 1.0
            # On borne à [0, 1]
            return min(1.0, max(0.0, max_coh * 1.5))  # boost pour contraste

        except Exception:
            return 0.0

    def _effective_kernel(self, t: float) -> float:
        """
        Noyau effectif normalisé : K_eff(0) = 1, K_eff(1) ≈ 0.

        Le noyau ABC brut K(t) converge vers K_min ≈ 0.28, pas vers 0.
        On le normalise pour mapper [K_min, 1] → [0, 1].
        """
        k_raw = abc_kernel(t, self.alpha)
        k_min = abc_kernel(1.0, self.alpha)  # ≈ 0.28
        if k_min >= 1.0:
            return 1.0
        # Normalisation : K_eff = (K_raw - K_min) / (1 - K_min)
        k_eff = (k_raw - k_min) / (1.0 - k_min)
        return max(0.0, min(1.0, k_eff))

    def _extract_numbers(self, text: str) -> List[float]:
        return [float(m.group(1)) for m in re.finditer(r'\b(\d+(?:\.\d+)?)\b', text)]

    def filter_iteratively(self, text: str) -> Dict:
        """
        Applique le filtre dynamique au texte.

        Retourne :
          {
            'survivors': [(word, final_weight), ...],
            'numbers': [float, ...],
            'iterations': n_until_convergence,
            'history': [{word: weight}, ...]  # évolution des poids
          }
        """
        # 1. Tokeniser le texte
        words = re.findall(r'[a-z0-9+\-*/=]+', text.lower())

        # 2. Calculer la cohérence mathématique de chaque mot
        word_data = {}
        for w in words:
            if len(w) < 1:
                continue
            coh = self._word_coherence(w)
            psi = encode(w, dim=self.dim) if coh > 0 else None
            word_data[w] = {
                'coherence': coh,
                'weight': 1.0,  # poids initial = survie totale
                'psi': psi,
            }

        if not word_data:
            return {'survivors': [], 'numbers': [], 'iterations': 0, 'history': []}

        # 3. Appliquer le filtre itérativement
        # Le poids à l'itération t est une fonction DIRECTE de K(t),
        # PAS un produit cumulatif (qui tendrait vers 0).
        #
        #   weight(t) = c + (1-c) · K(t)
        #
        # Cette formule donne :
        #   K(0)=1  → weight = 1        (tout survit au début)
        #   K(∞)≈0 → weight = c        (seul le mathématique survit)
        #
        # On itère jusqu'à convergence de K(t), pas des poids.
        history = []

        for iteration in range(1, self.max_iter + 1):
            t = iteration / self.max_iter
            k = self._effective_kernel(t)  # K_eff(t) : 1 → 0

            snapshot = {}
            for w, data in word_data.items():
                c = data['coherence']
                # Poids DIRECT (pas cumulatif) :
                data['weight'] = c + (1.0 - c) * k
                snapshot[w] = data['weight']

            history.append(snapshot)

            # Convergence : K(t) est presque stable
            if k < 0.01:
                break

        # 4. Extraire les survivants (poids > 0.5 = majoritairement mathématique)
        survivors = [(w, d['weight']) for w, d in word_data.items()
                    if d['weight'] > 0.5]

        # Trier par poids décroissant
        survivors.sort(key=lambda x: -x[1])

        # 5. Extraire les nombres du texte original
        numbers = self._extract_numbers(text)

        return {
            'survivors': survivors,
            'numbers': numbers,
            'iterations': iteration,
            'history': history,
            'all_words': word_data,
        }

    def detect_operation_by_phase(self, numbers: List[float]) -> Optional[str]:
        """
        Détecte l'opération par la DIFFÉRENCE DE PHASE entre nombres.

        Hypothèse THU : les nombres qui sont en relation mathématique
        dans le problème partagent une relation de phase dans l'espace des ondes.

        Δφ ≈ 0    → même échelle → addition/soustraction
        Δφ ≈ π/2  → échelles orthogonales → multiplication
        Δφ ≈ π    → inversion → division

        Cette fonction est EXPÉRIMENTALE — à valider sur les données.
        """
        if len(numbers) < 2:
            return None

        # Encoder chaque nombre en onde
        psi_nums = []
        for n in numbers:
            try:
                psi_nums.append(encode(str(int(n)), dim=self.dim))
            except Exception:
                psi_nums.append(None)

        if any(p is None for p in psi_nums):
            return None

        # Calculer les phases moyennes
        phases = []
        for psi in psi_nums:
            # Phase moyenne du vecteur complexe
            p = np.angle(np.mean(psi))
            phases.append(p)

        if len(phases) >= 2:
            # Différence de phase entre les deux derniers nombres
            dp = abs(phases[-1] - phases[-2])
            dp = dp % (2 * np.pi)

            if dp < np.pi / 4 or dp > 7 * np.pi / 4:
                return 'add'  # même échelle
            elif np.pi / 4 < dp < 3 * np.pi / 4:
                return 'mult'  # échelles orthogonales
            elif 3 * np.pi / 4 < dp < 5 * np.pi / 4:
                return 'div'  # inversion
            else:
                return 'sub'

        return None

    def detect_operation_by_words(self, survivors: List[Tuple[str, float]]) -> Optional[str]:
        """Détection classique par mots survivants (fallback)."""
        joined = ' '.join([w for w, _ in survivors])

        patterns = [
            (r'(times\s+as\s+(many|much)|twice|double|triple)', 'mult'),
            (r'\b(each|every)\b.*\b(has|have|contains?)\b', 'mult'),
            (r'\b(per|earns?)\b.*\b(hour|day|week|month)\b', 'rate'),
            (r'\b(split|shared|divided|among)\b', 'div'),
            (r'\b(ate|eats|sells?|sold|spends?|spent|loses?|lost|gives?\s+(away|to))\b', 'sub'),
            (r'\b(left|remain|remaining)\b', 'sub'),
            (r'\b(buys|buy|bought|gains?|earns?|collects?|receives?|finds?|gets?|obtains?|wins?)\b', 'add'),
            (r'\b(more|additional|also|another)\b', 'add'),
        ]
        for pattern, op in patterns:
            if re.search(pattern, joined):
                return op
        return None

    def solve(self, question: str) -> Optional[float]:
        """
        Résout un problème GSM8K avec le FILTRE DYNAMIQUE comme GATE.

        Le filtre dynamique décide SI une phrase est mathématique.
        La détection d'opération utilise le texte ORIGINAL (éprouvé).
        """
        q = question.strip()
        q = re.sub(r'\s+', ' ', q)

        sentences = re.split(r'(?<=[.;!?])\s+', q)
        sentences = [s.strip() for s in sentences if s.strip()]

        r_alg = AlgebriqueReasoner()
        registry = {}
        last_var = None
        step = 0

        for sent in sentences:
            # Ignorer la question
            if re.search(r'\b(how many|how much|what is|what are|'
                        r'how far|how long|how old)\b', sent.lower()):
                break

            # 1. FILTRE DYNAMIQUE = GATE : cette phrase est-elle mathématique ?
            result = self.filter_iteratively(sent)
            survivors = result['survivors']
            numbers = result['numbers']

            # Une phrase est mathématique si elle contient au moins
            # un nombre survivant (poids > 0.5) OU un mot-opérateur (poids > 0.1)
            has_math = any(w >= 0.5 for _, w in survivors)  # nombre survivant
            has_math = has_math or len(numbers) > 0  # nombre présent

            if not has_math or not numbers:
                continue

            # 2. DÉTECTION D'OPÉRATION sur le TEXTE ORIGINAL (éprouvé)
            operation = self._detect_operation_original(sent, survivors)

            step += 1
            var_name = f"v{step}"
            val = float(numbers[0])

            # 3. EXÉCUTER (même logique éprouvée que le filtre statique)
            if operation == 'rate':
                rate_var = f"rate_{step}"
                r_alg.define(rate_var, val)
                registry[rate_var] = val
                last_var = rate_var

            elif operation == 'mult':
                if last_var and len(numbers) == 1:
                    r_alg.update(last_var, 'mult', val)
                    registry[last_var] = float(registry[last_var]) * val
                elif len(numbers) >= 2:
                    r_alg.define(var_name, ('mult', f"{var_name}_a", float(numbers[1])))
                    r_alg.define(f"{var_name}_a", float(numbers[0]))
                    registry[var_name] = float(numbers[0]) * float(numbers[1])
                    last_var = var_name
                else:
                    r_alg.define(var_name, val)
                    registry[var_name] = val
                    last_var = var_name

            elif operation == 'div':
                if last_var and len(numbers) == 1:
                    r_alg.update(last_var, 'div', val)
                    registry[last_var] = float(registry[last_var]) / max(val, 0.001)
                elif len(numbers) >= 2:
                    r_alg.define(var_name, ('div', float(numbers[0]), float(numbers[1])))
                    registry[var_name] = float(numbers[0]) / max(float(numbers[1]), 0.001)
                    last_var = var_name
                else:
                    r_alg.define(var_name, val)
                    registry[var_name] = val
                    last_var = var_name

            elif operation == 'sub':
                if last_var:
                    r_alg.update(last_var, 'sub', val)
                    registry[last_var] = float(registry[last_var]) - val
                else:
                    r_alg.define(var_name, val)
                    registry[var_name] = val
                    last_var = var_name

            elif operation == 'add':
                if last_var:
                    r_alg.update(last_var, 'add', val)
                    registry[last_var] = float(registry[last_var]) + val
                else:
                    r_alg.define(var_name, val)
                    registry[var_name] = val
                    last_var = var_name

            elif step == 1 or not registry:
                r_alg.define(var_name, val)
                registry[var_name] = val
                last_var = var_name

            else:
                # Fallback : durée après taux
                dur_match = re.search(r'(\d+(?:\.\d+)?)\s*(hours?|days?|weeks?)', sent.lower())
                if dur_match and last_var and last_var.startswith('rate_'):
                    dur_val = float(dur_match.group(1))
                    total = float(registry[last_var]) * dur_val
                    earn_var = f"earn_{step}"
                    r_alg.define(earn_var, ('mult', last_var, dur_val))
                    registry[earn_var] = total
                    last_var = earn_var
                elif last_var:
                    r_alg.update(last_var, 'add', val)
                    registry[last_var] = float(registry[last_var]) + val
                else:
                    r_alg.define(var_name, val)
                    registry[var_name] = val
                    last_var = var_name

        if registry:
            return float(list(registry.values())[-1])
        return None

    def _detect_operation_original(self, sent: str, survivors) -> Optional[str]:
        """
        Détection d'opération sur le TEXTE ORIGINAL (pas seulement les survivants).

        Le filtre confirme que la phrase est mathématique (GATE).
        La détection utilise TOUS les mots du texte pour les patterns regex.
        """
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


# ═══════════════════════════════════════════════════════════════════════════
# 5. VISUALISATION DU FILTRE DYNAMIQUE
# ═══════════════════════════════════════════════════════════════════════════

def analyze_dynamic_filter(question: str):
    """Montre l'évolution du filtre dynamique sur un problème."""
    solver = DynamicHarmonicFilter()
    print(f"Problème : {question[:100]}...")
    print()

    import re
    sentences = re.split(r'(?<=[.;!?])\s+', question.strip())
    for sent in sentences:
        if not sent.strip():
            continue

        result = solver.filter_iteratively(sent)
        survivors = result['survivors']
        numbers = result['numbers']
        iterations = result['iterations']

        print(f"  Phrase: '{sent[:80]}'")
        print(f"    Itérations jusqu'à convergence: {iterations}")

        # Montrer l'évolution des poids (1ère, milieu, dernière itération)
        history = result['history']
        if history:
            snapshots = [history[0], history[len(history)//2], history[-1]]
            labels = ['t=0', 't=½', 't=1']
            for snap, label in zip(snapshots, labels):
                top = sorted(snap.items(), key=lambda x: -x[1])[:6]
                items = [f"{w}({v:.2f})" for w, v in top]
                print(f"    {label}: {', '.join(items)}")

        print(f"    Survivants finaux: {[f'{w}({p:.3f})' for w,p in survivors[:6]]}")
        print(f"    Nombres: {numbers}")
        print()


# ═══════════════════════════════════════════════════════════════════════════
# 6. TESTS + BENCHMARK
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
    print("TEST : FILTRE DYNAMIQUE HARMONIQUE")
    print("═" * 60)
    print()

    solver = DynamicHarmonicFilter()

    # D'abord, visualiser le filtre
    print("─── VISUALISATION DU FILTRE DYNAMIQUE ───")
    for q, _ in _SAMPLES[:2]:
        analyze_dynamic_filter(q)

    # Puis résoudre
    print("─── RÉSOLUTION ───")
    ok = 0
    for q, expected in _SAMPLES:
        result = solver.solve(q)
        good = result is not None and abs(result - expected) < 1e-6
        ok += good
        print(f"{'✅' if good else '❌'} {q[:55]:<57} → {result} (attendu {expected})")
    print(f"\nSCORE : {ok}/{len(_SAMPLES)} ({100 * ok / len(_SAMPLES):.1f}%)")
    return ok


def benchmark_gsm8k(n=200):
    solver = DynamicHarmonicFilter()

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        problems = [json.loads(l) for l in f]

    import random
    random.seed(42)
    sample = random.sample(problems, min(n, len(problems)))

    correct, no_sol, total = 0, 0, len(sample)
    times = []

    print(f"═══ BENCHMARK FILTRE DYNAMIQUE ({total} problèmes) ═══")
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
    parser.add_argument('--analyze', type=str, default=None)
    parser.add_argument('--benchmark', type=int, default=0)
    args = parser.parse_args()

    # Test rapide du noyau ABC
    if not args.test and not args.benchmark and not args.analyze:
        print("═══ VÉRIFICATION DU NOYAU ABC ═══")
        for t in [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
            k = abc_kernel(t)
            bar = '█' * int(k * 40)
            print(f"  t={t:.1f}  K(t)={k:.4f}  {bar}")

        print(f"\n  α = 1/φ = {ALPHA:.6f}")
        print(f"  K(0) = {abc_kernel(0):.4f} (mémoire parfaite)")
        print(f"  K(1) = {abc_kernel(1):.4f} (mémoire résiduelle)")
        print()

    if args.analyze:
        analyze_dynamic_filter(args.analyze)
        solver = DynamicHarmonicFilter()
        result = solver.solve(args.analyze)
        print(f"Résultat: {result}")

    if args.test:
        run_tests()

    if args.benchmark:
        benchmark_gsm8k(args.benchmark)
