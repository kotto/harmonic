#!/usr/bin/env python3
"""
dataset_transvertical.py — Génération d'exemples transvertiaux
=================================================================

PRINCIPE (transverticalité) :
  La même structure d'opérations se manifeste dans tous les domaines.
  Apprendre le geste SUB une fois (maths) = le posséder en droit, médecine,
  logique. Le nombre de manifestations LINGUISTIQUES d'un geste est fini.

  Ce générateur prend des gabarits d'opérations et les "traduit" dans
  chaque domaine avec son vocabulaire propre → le modèle apprend les
  primitives universelles, pas les combinaisons.

STRUCTURE :
  chaque exemple = (texte transvertial, ops cibles au format codec)

USAGE :
  python dataset_transvertical.py  → génère data/transvertical_train.jsonl
"""

import json, random
from typing import List, Dict

# ═══════════════════════════════════════════════════════════════════════════
# VOCABULAIRE TRANSVERTIAL : chaque geste logique, dans chaque domaine
# ═══════════════════════════════════════════════════════════════════════════

# (op, domaine) → liste de motifs linguistiques (verbes/expressions)
MOTIFS = {
    # ── SUB : diminution d'une quantité / exclusion d'une hypothèse ──
    ('SUB', 'maths'):    ["gives away", "loses", "spends", "removes", "sells"],
    ('SUB', 'droit'):    ["deducts", "excludes from the contract", "subtracts from the claim", "waives"],
    ('SUB', 'medecine'): ["the fever drops by", "the patient loses", "the count decreases by"],
    ('SUB', 'logique'):  ["is not the case", "excludes", "contradicts"],
    # ── ADD : augmentation / accumulation ──
    ('ADD', 'maths'):    ["buys", "gains", "adds", "receives", "earns"],
    ('ADD', 'droit'):    ["adds to the settlement", "includes", "compensates", "adds damages"],
    ('ADD', 'medecine'): ["gains weight", "the count increases by", "the heart rate rises by"],
    ('ADD', 'logique'):  ["and additionally", "combined with", "together with"],
    # ── MUL : multiplication / amplification ──
    ('MUL', 'maths'):    ["each has", "times", "per", "for every", "doubles", "triples"],
    ('MUL', 'droit'):    ["for each violation", "multiplied by the penalty", "per article"],
    ('MUL', 'medecine'): ["per dose", "for each kilogram", "per day"],
    ('MUL', 'logique'):  ["for every instance", "in all cases"],
    # ── DIV : division / normalisation ──
    ('DIV', 'maths'):    ["split among", "divided by", "per person", "each of"],
    ('DIV', 'droit'):    ["divided among the heirs", "shared between parties", "apportioned"],
    ('DIV', 'medecine'): ["per patient", "divided in doses", "per session"],
    ('DIV', 'logique'):  ["applies to each", "distributed over"],
}

# Contexte de phrase par domaine
CONTEXTES = {
    'maths':    "In a shop, John",
    'droit':    "In the settlement, the defendant",
    'medecine': "In the hospital, the patient",
    'logique':  "In the argument, the proposition",
}

# Noms par domaine pour les entités
NOMS = {
    'maths':    ['apples', 'books', 'marbles', 'dollars', 'candies'],
    'droit':    ['damages', 'penalties', 'clauses', 'claims', 'fees'],
    'medecine': ['milliliters', 'beats', 'milligrams', 'degrees', 'units'],
    'logique':  ['premises', 'inferences', 'propositions', 'cases', 'instances'],
}


# ═══════════════════════════════════════════════════════════════════════════
# GABARITS D'OPÉRATIONS (structures universelles)
# ═══════════════════════════════════════════════════════════════════════════

def gabarits():
    """Retourne des séquences d'ops génériques à traduire."""
    # Structure 1 : INIT + SUB (simple diminution)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'SUBTRACT', 'value': 'B'}]
    # Structure 2 : INIT + ADD (simple augmentation)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'ADD', 'value': 'B'}]
    # Structure 3 : INIT + MUL (multiplication)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'}]
    # Structure 4 : INIT + DIV (division)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'DIVIDE', 'divisor': 'B'}]
    # Structure 5 : INIT + MUL + SUB (achat et perte)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'SUBTRACT', 'value': 'C'}]
    # Structure 6 : INIT + ADD + MUL (cumul multiplié)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'ADD', 'value': 'B'},
           {'op': 'MULTIPLY', 'multiplier': 'C'}]
    # Structure 7 : INIT + SUB + DIV (partage après perte)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'SUBTRACT', 'value': 'B'},
           {'op': 'DIVIDE', 'divisor': 'C'}]


# ═══════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR TRANSVERTIAL
# ═══════════════════════════════════════════════════════════════════════════

def generer_exemple(ops_template: List[Dict], domaine: str,
                    valeurs: Dict[str, float]) -> Dict[str, str]:
    """Traduit un gabarit d'ops dans un domaine avec des valeurs concrètes."""
    contexte = CONTEXTES[domaine]
    noms = NOMS[domaine]
    phrases = [contexte]

    for op in ops_template:
        op_name = op['op']
        if op_name == 'INIT':
            val = valeurs['A']
            nom = random.choice(noms)
            phrases.append(f"has {val} {nom}")
        elif op_name == 'SUBTRACT':
            motif = random.choice(MOTIFS[('SUB', domaine)])
            val = valeurs['B']
            nom = random.choice(noms)
            phrases.append(f"{motif} {val} {nom}")
        elif op_name == 'ADD':
            motif = random.choice(MOTIFS[('ADD', domaine)])
            val = valeurs['B']
            nom = random.choice(noms)
            phrases.append(f"{motif} {val} {nom}")
        elif op_name == 'MULTIPLY':
            motif = random.choice(MOTIFS[('MUL', domaine)])
            val = valeurs['B']
            nom = random.choice(noms)
            phrases.append(f"{motif} {val} {nom}")
        elif op_name == 'DIVIDE':
            motif = random.choice(MOTIFS[('DIV', domaine)])
            val = valeurs['B']
            nom = random.choice(noms)
            phrases.append(f"{motif} {val} {nom}")

    texte = ', '.join(phrases) + '.'

    # Convertir les ops en cible texte (avec valeurs réelles)
    cible_parts = []
    for op in ops_template:
        op_name = op['op']
        if op_name == 'INIT':
            cible_parts.append(f"INIT({valeurs['A']})")
        elif op_name == 'SUBTRACT':
            cible_parts.append(f"SUB({valeurs['B']})")
        elif op_name == 'ADD':
            cible_parts.append(f"ADD({valeurs['B']})")
        elif op_name == 'MULTIPLY':
            cible_parts.append(f"MUL({valeurs['B']})")
        elif op_name == 'DIVIDE':
            cible_parts.append(f"DIV({valeurs['B']})")

    return {'input': texte, 'target': ' '.join(cible_parts)}


def generer_dataset(n_exemples: int = 5000, seed: int = 42):
    """Génère un dataset transvertical complet."""
    random.seed(seed)
    domaines = ['maths', 'droit', 'medecine', 'logique']
    gabarits_liste = list(gabarits())
    exemples = []

    for _ in range(n_exemples):
        g = random.choice(gabarits_liste)
        domaine = random.choice(domaines)
        # Valeurs aléatoires (A, B, C éventuellement)
        vals = {'A': random.randint(1, 50), 'B': random.randint(1, 10)}
        if len(g) > 2:
            vals['C'] = random.randint(1, 10)
        ex = generer_exemple(g, domaine, vals)
        exemples.append(ex)

    return exemples


def verifier_transvertical():
    """Démontre que la même structure d'ops donne des textes dans tous les domaines."""
    print("═══ TRANSVERTIALITÉ : UN GESTE, 4 DOMAINES ═══\n")
    gab = [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'SUBTRACT', 'value': 'C'}]
    vals = {'A': 20, 'B': 2, 'C': 4}

    for domaine in ['maths', 'droit', 'medecine', 'logique']:
        ex = generer_exemple(gab, domaine, vals)
        print(f"  {domaine.upper():<10s} : {ex['input']}")
        print(f"              → {ex['target']}")
    print("\n  MÊME structure INIT(20) MUL(2) SUB(4) dans les 4 domaines.")


if __name__ == '__main__':
    verifier_transvertical()
    exemples = generer_dataset(5000)
    with open('data/transvertical_train.jsonl', 'w', encoding='utf-8') as f:
        for ex in exemples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    print(f"\n✓ Dataset transvertical généré : {len(exemples)} exemples")
    print("  → data/transvertical_train.jsonl")