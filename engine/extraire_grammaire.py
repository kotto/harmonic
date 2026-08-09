#!/usr/bin/env python3
"""
extraire_grammaire.py — Data mining grammatical GSM8K
=======================================================

Extrait les règles de grammaire des 1101 problèmes d'entraînement.
Chaque <<op>> annotée est alignée avec sa phrase source,
puis normalisée en règle de grammaire réutilisable.

ALGORITHME :
  1. Pour chaque problème d'entraînement :
     a. Extraire les opérations <<...>> de la réponse
     b. Aligner chaque opération avec une phrase du problème
     c. Normaliser : nombres → <N>, entités → <ENT>, objets → <OBJ>
     d. La phrase normalisée + l'opération = 1 RÈGLE
  2. Regrouper les règles identiques, compter les fréquences
  3. Garder les règles avec fréquence ≥ 2
  4. Générer le code Python des règles

SORTIE : un fichier Python de règles de grammaire à intégrer
         dans le compilateur THU.
"""

import sys, os, re, json, math
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════════════════════════════════════
# 1. CHARGEMENT DES DONNÉES
# ═══════════════════════════════════════════════════════════════════════════

def charger_donnees() -> Tuple[List[dict], List[dict]]:
    """Charge les 1319 problèmes et split train/test."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        problems = [json.loads(l) for l in f]

    # Split train/test
    from structure_retrieval import StructuredRetrieval
    sr = StructuredRetrieval()
    sr.split_and_index()
    return sr._train_problems, sr._test_problems


# ═══════════════════════════════════════════════════════════════════════════
# 2. EXTRACTION DES OPÉRATIONS <<...>>
# ═══════════════════════════════════════════════════════════════════════════

def extraire_operations(answer: str) -> List[Tuple[str, float, float, float]]:
    """
    Extrait les opérations <<a op b = c>> d'une réponse.

    Retourne [(opérateur, a, b, résultat), ...]
    """
    ops = re.findall(r'<<(.*?)>>', answer)
    results = []
    for op in ops:
        clean = op.strip()
        # Décomposer les chaînes : "16-3-4=9" → plusieurs opérations
        nums = [float(x) for x in re.findall(r'[\d.]+', clean)]
        symbols = re.findall(r'[+\-*/]', clean)

        # Calculer les étapes
        current = nums[0] if nums else 0
        for i, sym in enumerate(symbols):
            if i + 1 < len(nums):
                b = nums[i + 1]
                if sym == '+':
                    new_val = current + b
                elif sym == '-':
                    new_val = current - b
                elif sym == '*':
                    new_val = current * b
                elif sym == '/':
                    new_val = current / b if b != 0 else 0
                else:
                    new_val = current
                results.append((sym, current, b, new_val))
                current = new_val

    return results


# ═══════════════════════════════════════════════════════════════════════════
# 3. ALIGNEMENT OPÉRATION → PHRASE
# ═══════════════════════════════════════════════════════════════════════════

def aligner_operation_phrase(
    operation: Tuple[str, float, float, float],
    sentences: List[str],
    op_index: int,
    total_ops: int,
) -> Optional[str]:
    """
    Aligne une opération avec la phrase du problème qui l'a déclenchée.

    Heuristique : la i-ème opération correspond approximativement
    à la i-ème phrase du problème (proportionnellement).
    """
    if not sentences:
        return None

    # Mapping proportionnel : opération i → phrase j
    n_sentences = len([s for s in sentences if re.search(r'\d', s)])
    if n_sentences == 0:
        return None

    # Estimer l'index de la phrase
    ratio = (op_index + 0.5) / total_ops
    sent_idx = int(ratio * n_sentences)
    sent_idx = max(0, min(n_sentences - 1, sent_idx))

    # Trouver la phrase avec nombres correspondante
    numeric_sents = [(i, s) for i, s in enumerate(sentences) if re.search(r'\d', s)]
    if not numeric_sents:
        return None

    if sent_idx < len(numeric_sents):
        return numeric_sents[sent_idx][1]

    return numeric_sents[-1][1]


# ═══════════════════════════════════════════════════════════════════════════
# 4. NORMALISATION (phrase → règle)
# ═══════════════════════════════════════════════════════════════════════════

# Mots à ne pas normaliser (mots-outils mathématiques)
_KEEP_WORDS = {
    'each', 'every', 'per', 'times', 'as', 'many', 'much',
    'more', 'less', 'than', 'fewer', 'left', 'remain', 'remaining',
    'total', 'altogether', 'combined', 'split', 'shared', 'equally',
    'divided', 'among', 'half', 'quarter', 'third', 'twice', 'double',
    'triple', 'dozen', 'hundred', 'thousand', 'percent',
    'has', 'had', 'have', 'there', 'are', 'were', 'is', 'was',
    'sells', 'sell', 'sold', 'buys', 'buy', 'bought',
    'eats', 'eat', 'ate', 'spends', 'spend', 'spent',
    'earns', 'earn', 'makes', 'make', 'gives', 'give', 'gave',
    'costs', 'cost', 'works', 'work',
}

_ENTITY_PATTERN = re.compile(r'\b([A-Z][a-z]{2,})\b')
_NUMBER_PATTERN = re.compile(r'\b(\d+(?:\.\d+)?)\b')

# Compteurs pour les slots
_ent_counter = [0]
_obj_counter = [0]
_num_counter = [0]


def normaliser_phrase(phrase: str) -> str:
    """
    Extrait un MOTIF COURT autour de chaque nombre dans la phrase.

    Au lieu de normaliser la phrase entière (qui perd toute spécificité),
    on extrait une FENÊTRE de ±5 mots autour de chaque nombre,
    puis on normalise cette fenêtre.

    Cela donne des motifs comme :
      "has <N1> <OBJ>" au lieu de "<ENT1> has <N1> <OBJ1> <OBJ2> <OBJ3>..."
    """
    words = phrase.split()
    motifs = []

    for i, w in enumerate(words):
        clean = w.strip('.,;:!?()"\'')
        if re.match(r'^\d+(?:\.\d+)?$', clean):
            # Fenêtre de ±5 mots autour du nombre
            start = max(0, i - 5)
            end = min(len(words), i + 6)
            window = words[start:end]

            # Normaliser la fenêtre
            norm_window = []
            for ww in window:
                cw = ww.strip('.,;:!?()"\'')
                lw = cw.lower()

                if re.match(r'^\d+(?:\.\d+)?$', cw):
                    norm_window.append('<N>')
                elif re.match(r'^[A-Z][a-z]{2,}$', cw) and lw not in ('he','she','they','it','him','her','his','their'):
                    norm_window.append('<ENT>')
                elif lw in _KEEP_WORDS:
                    norm_window.append(lw)
                elif len(lw) >= 3 and lw.isalpha():
                    norm_window.append('<OBJ>')
                else:
                    norm_window.append(lw)

            motif = ' '.join(norm_window)
            motifs.append(motif)

    return ' | '.join(motifs) if motifs else phrase


# ═══════════════════════════════════════════════════════════════════════════
# 5. CLASSIFICATION DE L'OPÉRATION
# ═══════════════════════════════════════════════════════════════════════════

def classer_operation(op_symbol: str, a: float, b: float, result: float,
                     phrase: str) -> str:
    """
    Classe l'opération en type d'action.

    Types : HAS, GAIN, LOSE, MULT, DIV, RATE, COMPARE, PARTITION
    """
    phrase_lower = phrase.lower()

    # Détection de pattern dans la phrase normalisée
    if 'times as many' in phrase_lower or 'times as much' in phrase_lower:
        return 'TIMES_AS_MANY'
    if 'twice' in phrase_lower or 'double' in phrase_lower or 'triple' in phrase_lower:
        return 'TIMES_AS_MANY'
    if 'each' in phrase_lower or 'every' in phrase_lower or 'per' in phrase_lower:
        if 'has' in phrase_lower or 'have' in phrase_lower or 'costs' in phrase_lower:
            return 'CROSS_MULT'
    if 'earns' in phrase_lower and 'per' in phrase_lower:
        return 'RATE'
    if 'per hour' in phrase_lower or 'per day' in phrase_lower:
        return 'RATE'
    if 'split' in phrase_lower or 'divided' in phrase_lower or 'among' in phrase_lower:
        return 'PARTITION'
    if 'there are' in phrase_lower or 'there were' in phrase_lower:
        return 'THERE_ARE'
    if 'are sold' in phrase_lower:
        return 'ARE_SOLD'
    if 'gave' in phrase_lower and 'to' in phrase_lower:
        return 'GAVE_TO'

    # Par symbole
    if op_symbol == '+':
        return 'GAIN'
    elif op_symbol == '-':
        return 'LOSE'
    elif op_symbol == '*':
        return 'MULT'
    elif op_symbol == '/':
        return 'DIV'

    return 'HAS'


# ═══════════════════════════════════════════════════════════════════════════
# 6. EXTRACTION DES RÈGLES (PROGRAMME PRINCIPAL)
# ═══════════════════════════════════════════════════════════════════════════

def extraire_regles(train_problems: List[dict]) -> Dict[str, List[dict]]:
    """
    Extrait les règles de grammaire de tous les problèmes d'entraînement.

    Retourne {type_opération: [{"pattern": ..., "freq": ...}, ...]}
    """
    regles_brutes = defaultdict(list)

    for p in train_problems:
        question = p.get('question', '')
        answer = p.get('answer', '')

        # Extraire les opérations
        operations = extraire_operations(answer)
        if not operations:
            continue

        # Diviser le problème en phrases
        sentences = re.split(r'(?<=[.;!?])\s+', question.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        # Aligner chaque opération avec une phrase
        total = len(operations)
        for i, (op_sym, a, b, result) in enumerate(operations):
            phrase = aligner_operation_phrase((op_sym, a, b, result),
                                              sentences, i, total)
            if phrase is None:
                continue

            # Normaliser la phrase
            pattern = normaliser_phrase(phrase)

            # Classer l'opération
            op_type = classer_operation(op_sym, a, b, result, phrase)

            # Stocker
            regles_brutes[op_type].append({
                "pattern": pattern,
                "op": op_type,
                "freq": 1,
            })

    # Agréger les règles identiques
    regles_finales = {}
    for op_type, regles in regles_brutes.items():
        counter = Counter(r["pattern"] for r in regles)
        aggregated = []
        for pattern, freq in counter.most_common():
            if freq >= 2:  # garder seulement les règles fréquentes
                aggregated.append({
                    "op": op_type,
                    "pattern": pattern,
                    "freq": freq,
                })
        if aggregated:
            regles_finales[op_type] = aggregated

    return regles_finales


# ═══════════════════════════════════════════════════════════════════════════
# 7. GÉNÉRATION DU CODE
# ═══════════════════════════════════════════════════════════════════════════

def generer_code_regles(regles: Dict[str, List[dict]]) -> str:
    """Génère le code Python des règles de grammaire extraites."""
    lines = []
    lines.append("# Règles de grammaire extraites automatiquement des 1101 problèmes GSM8K")
    lines.append(f"# {sum(len(v) for v in regles.values())} motifs uniques (fenêtres autour des nombres)")
    lines.append("")
    lines.append("REGLES_EXTRACTED = [")

    SLOTS_MAP = {
        'HAS': ['ent', 'val', 'obj'],
        'GAIN': ['ent', 'val'],
        'LOSE': ['ent', 'val'],
        'GAVE_TO': ['giver', 'ent', 'val', 'obj'],
        'TIMES_AS_MANY': ['ent', 'mult'],
        'CROSS_MULT': ['container', 'per_unit', 'product'],
        'THERE_ARE': ['count', 'container'],
        'PARTITION': ['groups'],
        'RATE': ['ent', 'rate'],
        'DURATION': ['dur'],
        'ARE_SOLD': ['val'],
        'MULT': ['val'],
        'DIV': ['val'],
        'COMPARE': ['ent', 'mult'],
    }

    for op_type in sorted(regles.keys()):
        for rule in regles[op_type]:
            pattern = rule["pattern"]
            freq = rule["freq"]
            slots = SLOTS_MAP.get(op_type, ['val'])

            # Convertir le motif normalisé en regex
            # <N> → \\d+(?:\\.\\d+)?
            # <ENT> → [A-Z][a-z]+
            # <OBJ> → \\w+
            escaped = re.escape(pattern)
            escaped = escaped.replace(r'<\ N\ >', r'\\d+(?:\\.\\d+)?')
            escaped = escaped.replace(r'<\ ENT\ >', r'[A-Z][a-z]+')
            escaped = escaped.replace(r'<\ OBJ\ >', r'\\w+')

            lines.append(f"    # freq={freq}")
            lines.append(f"    (r'{escaped}', '{op_type}', {slots}),")

    lines.append("]")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# 8. MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═══ DATA MINING GRAMMATICAL GSM8K ═══\n")

    # Charger les données
    print("Chargement des données...")
    train, test = charger_donnees()
    print(f"  Train : {len(train)} problèmes")
    print(f"  Test  : {len(test)} problèmes")

    # Extraire les règles
    print("\nExtraction des règles de grammaire...")
    regles = extraire_regles(train)

    total_regles = sum(len(v) for v in regles.values())
    print(f"  Règles extraites : {total_regles} (fréquence ≥ 2)")
    print(f"  Types d'opérations : {len(regles)}")

    # Afficher les statistiques
    print("\n─── DISTRIBUTION DES RÈGLES ───")
    for op_type in sorted(regles.keys(), key=lambda t: -sum(r['freq'] for r in regles[t])):
        total_freq = sum(r['freq'] for r in regles[op_type])
        n_regles = len(regles[op_type])
        print(f"  {op_type:<20s} : {n_regles:>3d} règles, {total_freq:>4d} occurrences")

    # Afficher les meilleures règles par type
    print("\n─── TOP RÈGLES PAR TYPE ───")
    for op_type in sorted(regles.keys()):
        top = sorted(regles[op_type], key=lambda r: -r['freq'])[:3]
        print(f"\n  [{op_type}]")
        for r in top:
            print(f"    ×{r['freq']:<4d} {r['pattern'][:90]}")

    # Sauvegarder les règles
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'grammaire_extraite.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(regles, f, ensure_ascii=False, indent=2)
    print(f"\nRègles sauvegardées dans {out_path}")

    # Générer le code
    code = generer_code_regles(regles)
    code_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'grammaire_extraite.py')
    with open(code_path, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"Code généré dans {code_path}")
