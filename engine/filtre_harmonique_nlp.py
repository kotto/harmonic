#!/usr/bin/env python3
"""
filtre_harmonique_nlp.py — NLP par FILTRE (élimination), pas par EXTRACTION (choix)
====================================================================================

Principe THU V2 (Refondation 09/08/2026) :
  "La nature ne choisit pas : elle élimine. Les constantes ne sont pas des
   préférences de l'univers — ce sont les survivants de ses filtres."

Application au NLP GSM8K :
  Au lieu d'extraire entité, objet, action par des heuristiques fragiles,
  on applique un FILTRE HARMONIQUE au problème encodé en onde.
  
  Seules les fréquences mathématiquement cohérentes SURVIVENT.
  Les mots narratifs ("John", "pommes", "acheter") sont ÉLIMINÉS.
  
  Ce qui survit = la structure mathématique pure (nombres + relations).

ALGORITHME :
  1. Encoder chaque mot du problème en onde
  2. Créer un « espace de référence mathématique » ψ_math :
     - ψ_nombres = superpose(encode("0"), encode("1"), ..., encode("9"))
     - ψ_opérations = superpose(encode("+"), encode("-"), encode("*"), encode("/"))
     - ψ_relations = superpose(encode("each"), encode("per"), encode("times"), ...)
  3. Pour chaque mot : calculer cohérence(ψ_mot, ψ_math)
  4. FILTRER : ne garder que les mots avec cohérence > seuil
  5. Ce qui survit → analyser pour extraire les nombres et l'opération
  6. Exécuter avec le moteur algébrique

USAGE :
  python filtre_harmonique_nlp.py --test
  python filtre_harmonique_nlp.py --benchmark 200
"""

import sys, os, re, math, json, time
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_lang import encode, superpose, resonate, normalize, DEFAULT_DIM
from encodage_phase import PhaseEncoder
from encodage_logarithmique import LogWaveEncoder
from raisonneur_algebrique import AlgebriqueReasoner
from structure_ondulatoire import StructuredSolver, _STOP, _VERBS


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ESPACE DE RÉFÉRENCE MATHÉMATIQUE (le « filtre »)
# ═══════════════════════════════════════════════════════════════════════════════

# Mots qui définissent l'espace mathématique
_NUMBER_WORDS = [
    # Chiffres individuels (les nombres multi-chiffres sont traités
    # par décomposition digitale, pas par correspondance de chaîne)
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    # Mots-nombres
    "zero", "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve",
    "hundred", "thousand", "dozen", "half", "quarter", "third",
    "double", "triple", "twice", "times",
]

_OPERATOR_WORDS = [
    "plus", "minus", "times", "divided", "add", "subtract", "multiply",
    "divide", "+", "-", "*", "/", "=",
    "more", "less", "fewer", "additional", "also", "another",
    "total", "sum", "difference", "product", "quotient",
    # Verbes d'action mathématique (pour qu'ils SURVIVENT au filtre)
    "ate", "eats", "eat", "sells", "sell", "sold",
    "spends", "spend", "spent", "loses", "lose", "lost",
    "gives", "give", "gave", "buys", "buy", "bought",
    "earns", "earn", "makes", "make",
    "gains", "gain", "collects", "collect",
    "removes", "remove", "drops", "drop",
]

_RELATION_WORDS = [
    "each", "every", "per", "apiece", "among", "split", "shared",
    "costs", "has", "had", "have", "left", "remain", "remaining",
    "altogether", "combined", "ratio", "rate", "percent",
    "as many", "as much", "more than", "less than",
    "there are", "there were",
]

# Mots purement narratifs (À ÉLIMINER) — on ne les met PAS dans le filtre
# pour que le filtre les rejette naturellement


def _build_math_filter(dim=DEFAULT_DIM):
    """
    Construit TROIS espaces de référence (filtres spécialisés).
    
    Un mot survit s'il résonne avec AU MOINS UN des trois filtres.
    Ça évite la dilution d'un ψ_math unique.
    """
    def encode_set(words):
        waves = []
        for w in words:
            w = w.strip()
            if w and len(w) >= 1:
                try:
                    waves.append(encode(w, dim=dim))
                except Exception:
                    pass
        return normalize(superpose(*waves)) if waves else np.zeros(dim, dtype=np.complex128)

    return {
        'numbers': encode_set(_NUMBER_WORDS),
        'operators': encode_set(_OPERATOR_WORDS),
        'relations': encode_set(_RELATION_WORDS),
    }


class HarmonicFilterSolver:
    """
    Résout les problèmes GSM8K en appliquant un FILTRE harmonique
    plutôt qu'en extrayant des entités/objets/actions.
    """

    def __init__(self, dim=DEFAULT_DIM, threshold=0.03):
        self.dim = dim
        self.threshold = threshold
        self.phase = PhaseEncoder(500000)
        self.log = LogWaveEncoder(grid_size=2048, SCALE=300)

        # Construire les TROIS filtres spécialisés
        self._filters = _build_math_filter(dim)

    def _is_number(self, word: str) -> bool:
        return bool(re.match(r'^\d+(\.\d+)?$', word))

    def _compute_coherence(self, word: str) -> float:
        """
        Calcule la cohérence MAXIMALE d'un mot avec les 3 filtres.
        Un mot est mathématique s'il résonne avec AU MOINS UN filtre.
        """
        if self._is_number(word):
            # Les nombres sont mathématiques par définition
            digit_coherences = []
            for ch in word:
                if ch.isdigit():
                    try:
                        psi_d = encode(ch, dim=self.dim)
                        coh = float(resonate(psi_d, self._filters['numbers']))
                        digit_coherences.append(coh)
                    except Exception:
                        pass
            return max(digit_coherences) if digit_coherences else 1.0

        # Mot textuel : cohérence max avec les 3 filtres (OR logic)
        try:
            psi_w = encode(word, dim=self.dim)
            coherences = []
            for filter_name, psi_f in self._filters.items():
                coh = float(resonate(psi_w, psi_f))
                coherences.append(coh)
            return max(coherences)  # OR : survit si UN filtre match
        except Exception:
            return 0.0

    def filter_words(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Applique le filtre harmonique à un texte.

        RÈGLE : Les NOMBRES survivent TOUJOURS (ce sont des invariants
        mathématiques). Les MOTS survivent s'ils résonnent avec ψ_math.

        Retourne (mots_survivants, mots_éliminés).
        """
        words = re.findall(r'[a-z0-9+\-*/=]+', text.lower())

        survivors = []
        eliminated = []

        for w in words:
            if len(w) < 1:
                continue

            is_num = self._is_number(w)
            coherence = self._compute_coherence(w)

            # Les nombres survivent TOUJOURS (invariants mathématiques)
            if is_num or coherence > self.threshold:
                survivors.append((w, coherence))
            else:
                eliminated.append((w, coherence))

        # Trier par cohérence décroissante
        survivors.sort(key=lambda x: -x[1])

        return ([w for w, _ in survivors], [w for w, _ in eliminated])

    def _extract_numbers_filtered(self, text: str) -> List[float]:
        """Extrait les nombres du texte (méthode classique en fallback)."""
        return [float(m.group(1)) for m in re.finditer(r'\b(\d+(?:\.\d+)?)\b', text)
                if float(m.group(1)) > 0]

    def detect_operation(self, survivor_words: List[str], original_sent: str = None) -> Optional[str]:
        """
        Détecte l'opération à partir des mots survivants ET du texte original.

        Les survivants confirment la pertinence mathématique.
        Le texte ORIGINAL préserve l'ordre des mots pour les patterns regex.
        """
        # Utiliser le texte original pour les patterns (préserve l'ordre)
        text = original_sent.lower() if original_sent else ' '.join(survivor_words)
        joined = ' '.join(survivor_words)

        # Patterns d'opérations (dans l'ordre de priorité)
        patterns = [
            # Multiplication explicite — sur texte original (ordre préservé)
            (r'(times\s+as\s+(many|much)|twice|double|triple)', 'mult', text),
            # Cross-product — sur texte original
            (r'\b(each|every)\b.*\b(has|have|contains?|holds?)\b.*\d', 'mult', text),
            # Taux
            (r'\b(per|earns?)\b.*\b(hour|day|week|month)\b', 'rate', text),
            # Division
            (r'\b(split|shared\s+equally|divided\s+equally|among)\b', 'div', text),
            # Soustraction (verbes de perte)
            (r'\b(ate|eats|eat|sells?|sold|spends?|spent|loses?|lost|'
             r'gives?\s+away|gives?\s+to|removes?|takes?\s+away)\b', 'sub', text),
            # "gives" seul → regarder s'il y a "to" dans la phrase
            (r'\bgives?\b', 'sub', text if ' to ' in text or ' her ' in text or ' him ' in text else ''),
            # Addition (verbes de gain)
            (r'\b(buys|buy|bought|gains?|earns?|collects?|receives?|finds?|'
             r'gets?|obtains?|wins?)\b', 'add', text),
            # "left" → soustraction implicite
            (r'\b(left|remain|remaining)\b', 'sub', text),
            # "more" + contexte → addition
            (r'\b(more|additional|also|another)\b', 'add', text),
        ]

        for pattern, op, target in patterns:
            if target and re.search(pattern, target):
                return op

        return None

    def solve(self, question: str) -> Optional[float]:
        """
        Résout un problème GSM8K en utilisant le FILTRE HARMONIQUE.

        1. Filtrer chaque phrase → ne garder que les mots mathématiques
        2. Les survivants révèlent : nombres + opérations
        3. Construire et exécuter les équations
        """
        q = question.strip()
        q = re.sub(r'\s+', ' ', q)
        sentences = re.split(r'(?<=[.;!?])\s+', q)
        sentences = [s.strip() for s in sentences if s.strip()]

        r_alg = AlgebriqueReasoner()
        registry = {}  # var_name → value
        last_var = None
        step = 0

        for sent in sentences:
            # Ignorer la phrase-question
            if re.search(r'\b(how many|how much|what is|what are|'
                         r'how far|how long|how old)\b', sent.lower()):
                break

            # 1. FILTRER : ne garder que les mots mathématiques
            survivors, eliminated = self.filter_words(sent)

            # 2. Extraire les nombres du texte brut (ils survivent toujours)
            nums = self._extract_numbers_filtered(sent)
            if not nums:
                continue

            # 3. Détecter l'opération à partir des survivants + texte original
            operation = self.detect_operation(survivors, sent)

            # 4. Exécuter l'opération
            step += 1
            var_name = f"v{step}"
            val = float(nums[0])

            # Vérifier d'abord les opérations spécifiques (même au step 1)
            if operation == 'rate':
                # Stocker le taux avec un nom reconnaissable
                rate_var = f"rate_{step}"
                r_alg.define(rate_var, val)
                registry[rate_var] = val
                last_var = rate_var

            elif operation == 'mult':
                if last_var and len(nums) == 1:
                    r_alg.update(last_var, 'mult', val)
                    registry[last_var] = float(registry[last_var]) * val
                elif len(nums) >= 2:
                    v1 = f"{var_name}_a"
                    r_alg.define(v1, float(nums[0]))
                    r_alg.define(var_name, ('mult', v1, float(nums[1])))
                    registry[var_name] = float(nums[0]) * float(nums[1])
                    last_var = var_name
                else:
                    r_alg.define(var_name, val)
                    registry[var_name] = val
                    last_var = var_name

            elif operation == 'div':
                if last_var and len(nums) == 1:
                    r_alg.update(last_var, 'div', val)
                    registry[last_var] = float(registry[last_var]) / max(val, 0.001)
                elif len(nums) >= 2:
                    r_alg.define(var_name, ('div', float(nums[0]), float(nums[1])))
                    registry[var_name] = float(nums[0]) / max(float(nums[1]), 0.001)
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
                # INITIALISATION : premier fait (et pas d'opération spécifique)
                r_alg.define(var_name, val)
                registry[var_name] = val
                last_var = var_name

            else:
                # Opération inconnue → vérifier si c'est une durée après taux
                dur_match = re.search(r'(\d+(?:\.\d+)?)\s*(hours?|days?|weeks?)',
                                     sent.lower())
                if dur_match and registry:
                    dur_val = float(dur_match.group(1))
                    found = False
                    if last_var and last_var.startswith('rate_'):
                        total = float(registry[last_var]) * dur_val
                        earn_var = f"earn_{step}"
                        r_alg.define(earn_var, ('mult', last_var, dur_val))
                        registry[earn_var] = total
                        last_var = earn_var
                        found = True
                    if not found:
                        for rkey, rval in list(registry.items()):
                            if 'rate' in rkey:
                                total = float(rval) * dur_val
                                earn_var = f"earn_{step}"
                                r_alg.define(earn_var, ('mult', rkey, dur_val))
                                registry[earn_var] = total
                                last_var = earn_var
                                found = True
                                break
                    if not found:
                        if last_var:
                            r_alg.update(last_var, 'add', val)
                            registry[last_var] = float(registry[last_var]) + val
                else:
                    if last_var:
                        r_alg.update(last_var, 'add', val)
                        registry[last_var] = float(registry[last_var]) + val
                    else:
                        r_alg.define(var_name, val)
                        registry[var_name] = val
                        last_var = var_name

        # Résoudre : retourner la dernière valeur du registre
        if registry:
            return float(list(registry.values())[-1])
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ANALYSE DU FILTRE (visualisation de ce qui survit)
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_filter(question: str, solver: HarmonicFilterSolver = None):
    """
    Analyse ce que le filtre garde et élimine pour un problème donné.
    """
    if solver is None:
        solver = HarmonicFilterSolver()

    print(f"Problème : {question[:100]}...")
    print()

    sentences = re.split(r'(?<=[.;!?])\s+', question.strip())
    for sent in sentences:
        survivors, eliminated = solver.filter_words(sent)
        print(f"  Phrase: '{sent[:70]}...'")
        print(f"    ✅ Survivants ({len(survivors)}): {survivors[:15]}")
        if eliminated:
            print(f"    ❌ Éliminés  ({len(eliminated)}): {eliminated[:10]}")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TESTS
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


def run_tests():
    print("═" * 60)
    print("TEST : RÉSOLVEUR PAR FILTRE HARMONIQUE")
    print("═" * 60)
    print()

    solver = HarmonicFilterSolver()

    # D'abord, montrer le filtre en action sur 3 exemples
    print("─── ANALYSE DU FILTRE ───")
    for q, _ in _SAMPLES[:3]:
        analyze_filter(q, solver)

    # Puis tester la résolution
    print("─── RÉSOLUTION ───")
    ok = 0
    for q, expected in _SAMPLES:
        result = solver.solve(q)
        good = result is not None and abs(result - expected) < 1e-6
        ok += good
        print(f"{'✅' if good else '❌'} {q[:60]:<62} → {result} (attendu {expected})")
    print(f"\nSCORE : {ok}/{len(_SAMPLES)} ({100 * ok / len(_SAMPLES):.1f}%)")
    return ok


def benchmark_gsm8k(n=200):
    solver = HarmonicFilterSolver()

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        problems = [json.loads(l) for l in f]

    import random
    random.seed(42)
    sample = random.sample(problems, min(n, len(problems)))

    correct, no_sol, total = 0, 0, len(sample)
    times = []

    print(f"═══ BENCHMARK FILTRE HARMONIQUE ({total} problèmes) ═══")
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
    parser.add_argument('--analyze', type=str, default=None,
                       help='Analyser le filtre sur un problème donné')
    parser.add_argument('--benchmark', type=int, default=0)
    args = parser.parse_args()

    if args.analyze:
        solver = HarmonicFilterSolver()
        analyze_filter(args.analyze, solver)
        result = solver.solve(args.analyze)
        print(f"Résultat: {result}")

    elif args.test or not args.benchmark:
        run_tests()

    if args.benchmark:
        benchmark_gsm8k(args.benchmark)
