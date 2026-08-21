#!/usr/bin/env python3
"""
dataset_transvertical_v2.py — Générateur transvertical enrichi
=================================================================

Version 2 : 25+ gabarits, 7 domaines, 10-20 motifs par opération,
           pourcentages, taux, fractions, comparaisons, chaînes longues.

PRINCIPE : la même structure d'opérations se manifeste dans tous les
domaines avec le vocabulaire approprié. Le modèle apprend les gestes
universels une fois pour toutes.

USAGE :
  python dataset_transvertical_v2.py  → génère data/transvertical_v2_train.jsonl
"""

import json, random
from typing import List, Dict, Optional

random.seed(42)

# ═══════════════════════════════════════════════════════════════════════════
# VOCABULAIRE ÉTENDU (10-20 motifs par opération × domaine)
# ═══════════════════════════════════════════════════════════════════════════

MOTIFS = {
    # ── INIT : établir une quantité de départ ──
    ('INIT', 'maths'):    ["has", "starts with", "begins with", "buys", "collects", "receives", "is given", "picks", "finds", "owns"],
    ('INIT', 'droit'):    ["files", "claims", "demands", "seeks", "requests", "is awarded", "receives", "holds", "possesses", "asserts"],
    ('INIT', 'medecine'): ["presents with", "has", "weighs", "measures", "shows", "exhibits", "reports", "complains of", "is diagnosed with", "has a history of"],
    ('INIT', 'logique'):  ["assumes", "posits", "states", "hypothesizes", "defines", "proposes", "asserts", "claims", "premises", "postulates"],
    ('INIT', 'eco'):      ["invests", "spends", "budgets", "allocates", "earns", "reports", "projects", "requires", "holds", "values at"],
    ('INIT', 'physique'): ["measures", "records", "observes", "calculates", "reads", "detects", "emits", "contains", "releases", "generates"],
    ('INIT', 'quotidien'):["has", "buys", "prepares", "makes", "bakes", "cooks", "grows", "raises", "builds", "paints"],
    
    # ── SUB : diminution / soustraction ──
    ('SUB', 'maths'):    ["gives away", "loses", "spends", "sells", "removes", "eats", "breaks", "drops", "lends", "throws away", "donates", "consumes", "uses", "pays", "wastes"],
    ('SUB', 'droit'):    ["deducts", "excludes", "subtracts from the claim", "waives", "reduces by", "lowers by", "decreases by", "discounts", "writes off", "forfeits"],
    ('SUB', 'medecine'): ["the fever drops by", "the patient loses", "the count decreases by", "the level falls by", "symptoms improve by", "inflammation reduces by", "the dose decreases by", "the tumor shrinks by", "blood pressure drops by", "weight decreases by"],
    ('SUB', 'logique'):  ["is not the case", "excludes", "contradicts", "negates", "refutes", "undermines", "invalidates", "falsifies", "disproves", "opposes"],
    ('SUB', 'eco'):      ["loses", "spends", "incurs", "pays", "depreciates by", "writes off", "suffers a loss of", "expenses", "costs", "reduces by"],
    ('SUB', 'physique'): ["loses", "dissipates", "decays by", "decreases by", "cools by", "slows by", "drops by", "absorbs", "radiates", "discharges"],
    ('SUB', 'quotidien'):["gives away", "eats", "drinks", "uses", "spends", "breaks", "loses", "forgets", "burns", "donates"],
    
    # ── ADD : augmentation / accumulation ──
    ('ADD', 'maths'):    ["buys", "gains", "finds", "receives", "earns", "collects", "picks up", "adds", "gets", "acquires", "gathers", "harvests", "wins", "inherits", "discovers"],
    ('ADD', 'droit'):    ["adds to the settlement", "includes", "compensates", "adds damages", "awards additional", "grants", "imposes", "adds a penalty of", "supplements", "incorporates"],
    ('ADD', 'medecine'): ["gains weight", "the count increases by", "the heart rate rises by", "symptoms worsen by", "fever increases by", "inflammation increases by", "the dose increases by", "blood pressure rises by", "the tumor grows by", "weight increases by"],
    ('ADD', 'logique'):  ["and additionally", "combined with", "together with", "in conjunction with", "alongside", "furthermore", "moreover", "in addition", "also", "plus"],
    ('ADD', 'eco'):      ["earns", "gains", "receives", "adds", "accrues", "generates revenue of", "collects", "accumulates", "secures funding of", "realizes a gain of"],
    ('ADD', 'physique'): ["gains", "absorbs", "increases by", "accumulates", "stores", "charges", "heats up by", "speeds up by", "rises by", "expands by"],
    ('ADD', 'quotidien'):["buys", "finds", "receives", "adds", "picks up", "gathers", "collects", "grows", "harvests", "bakes more"],
    
    # ── MUL : multiplication / amplification ──
    ('MUL', 'maths'):    ["each has", "times", "per", "for every", "twice", "three times", "each of the", "every", "apiece", "doubles", "triples", "multiplied by", "per person", "each", "per container"],
    ('MUL', 'droit'):    ["for each violation", "multiplied by the penalty", "per article", "for every instance", "per defendant", "each offense carries", "per claim", "times the penalty", "per violation", "for each count"],
    ('MUL', 'medecine'): ["per dose", "for each kilogram", "per day", "per patient", "per session", "for every hour", "per treatment", "times the dosage", "per administration", "for each symptom"],
    ('MUL', 'logique'):  ["for every instance", "in all cases", "for each", "applies to all", "universally", "for any", "per case", "each time", "whenever", "under all conditions"],
    ('MUL', 'eco'):      ["times the rate", "per unit", "for each item", "per share", "each unit costs", "per transaction", "per employee", "for each sale", "per customer", "times the price"],
    ('MUL', 'physique'): ["per second", "per meter", "per kilogram", "per hour", "per unit volume", "per degree", "per mole", "per watt", "per square meter", "per liter"],
    ('MUL', 'quotidien'):["each", "per", "for every", "per person", "each of the", "every", "apiece", "per container", "doubles", "triples"],
    
    # ── DIV : division / normalisation / partage ──
    ('DIV', 'maths'):    ["split among", "divided by", "per person", "each of", "shared between", "divided equally", "split between", "each gets", "per", "half of", "quarter of", "third of", "percent of"],
    ('DIV', 'droit'):    ["divided among the heirs", "shared between parties", "apportioned", "split between plaintiffs", "divided equally among", "per capita", "distributed among", "allocated between", "shared among", "divided by the number of"],
    ('DIV', 'medecine'): ["per patient", "divided in doses", "per session", "split into", "divided by body weight", "per kilogram", "per administration", "per treatment", "half of patients", "quarter of the dose"],
    ('DIV', 'logique'):  ["applies to each", "distributed over", "divided among", "per instance", "for each case", "half of", "third of", "each of the", "per proposition", "for every element"],
    ('DIV', 'eco'):      ["divided among", "per share", "per unit", "split between", "each investor gets", "per partner", "divided by the number of", "per employee", "per capita", "apportioned among"],
    ('DIV', 'physique'): ["per unit", "per meter", "per kilogram", "divided by", "per second", "per hour", "per degree", "per mole", "per liter", "per square meter"],
    ('DIV', 'quotidien'):["split among", "divided by", "per person", "each of", "shared between", "each gets", "half of", "quarter of", "per", "divided equally"],
}

# Contextes
CONTEXTES = {
    'maths':    ['In a shop,', 'At the market,', 'In a classroom,', 'During a sale,', 'In a warehouse,', 'On a farm,', 'In a bakery,', 'At a store,', 'During a game,', 'In a contest,'],
    'droit':    ['In the settlement,', 'Under the contract,', 'In the lawsuit,', 'Per the agreement,', 'In the dispute,', 'Under the statute,', 'In the case,', 'Under the regulation,', 'In the arbitration,', 'At the hearing,'],
    'medecine': ['In the hospital,', 'At the clinic,', 'During treatment,', 'In the study,', 'At the pharmacy,', 'In the ICU,', 'During surgery,', 'In the ward,', 'At the ER,', 'During recovery,'],
    'logique':  ['In the argument,', 'In the proof,', 'In the deduction,', 'In the reasoning,', 'In the syllogism,', 'In the analysis,', 'In the demonstration,', 'In the inference,', 'In the derivation,', 'In the conclusion,'],
    'eco':      ['In Q1,', 'In the fiscal year,', 'In the quarterly report,', 'During the audit,', 'In the budget,', 'In the annual report,', 'During the merger,', 'In the earnings call,', 'In the prospectus,', 'During the acquisition,'],
    'physique': ['In the experiment,', 'During the reaction,', 'In the system,', 'At the lab,', 'In the field,', 'During the test,', 'In the simulation,', 'At the observatory,', 'In the circuit,', 'During the measurement,'],
    'quotidien':['At home,', 'In the kitchen,', 'In the garden,', 'At the park,', 'During the party,', 'At the restaurant,', 'In the garage,', 'In the backyard,', 'At the beach,', 'During the picnic,'],
}

NOMS = {
    'maths':    ['apples', 'books', 'marbles', 'dollars', 'candies', 'pencils', 'oranges', 'tickets', 'stamps', 'cards'],
    'droit':    ['damages', 'penalties', 'clauses', 'claims', 'fees', 'fines', 'settlements', 'restitutions', 'sanctions', 'compensations'],
    'medecine': ['milliliters', 'beats', 'milligrams', 'degrees', 'units', 'cells', 'drops', 'liters', 'grams', 'doses'],
    'logique':  ['premises', 'inferences', 'propositions', 'cases', 'instances', 'arguments', 'deductions', 'conclusions', 'hypotheses', 'proofs'],
    'eco':      ['dollars', 'euros', 'shares', 'bonds', 'assets', 'liabilities', 'revenues', 'costs', 'profits', 'dividends'],
    'physique': ['meters', 'seconds', 'grams', 'liters', 'joules', 'watts', 'volts', 'amperes', 'newtons', 'pascals'],
    'quotidien':['apples', 'cookies', 'cups', 'eggs', 'flowers', 'liters', 'meters', 'tickets', 'books', 'slices'],
}

# Articles indéfinis pour les noms
ARTICLES = {
    'apples': 'des', 'books': 'des', 'marbles': 'des', 'dollars': 'des', 'candies': 'des',
    'pencils': 'des', 'oranges': 'des', 'tickets': 'des', 'stamps': 'des', 'cards': 'des',
    'cookies': 'des', 'cups': 'des', 'eggs': 'des', 'flowers': 'des', 'liters': 'des',
    'meters': 'des', 'slices': 'des', 'euros': 'des', 'shares': 'des', 'bonds': 'des',
    'assets': 'des', 'liabilities': 'des', 'revenues': 'des', 'costs': 'des', 'profits': 'des',
    'dividends': 'des', 'damages': 'des', 'penalties': 'des', 'clauses': 'des', 'claims': 'des',
    'fees': 'des', 'fines': 'des', 'settlements': 'des', 'restitutions': 'des', 'sanctions': 'des',
    'milliliters': 'des', 'beats': 'des', 'milligrams': 'des', 'degrees': 'des', 'units': 'des',
    'cells': 'des', 'drops': 'des', 'liters': 'des', 'grams': 'des', 'doses': 'des',
    'premises': 'des', 'inferences': 'des', 'propositions': 'des', 'cases': 'des', 'instances': 'des',
    'arguments': 'des', 'deductions': 'des', 'conclusions': 'des', 'hypotheses': 'des', 'proofs': 'des',
    'seconds': 'des', 'joules': 'des', 'watts': 'des', 'volts': 'des', 'amperes': 'des', 'newtons': 'des', 'pascals': 'des',
    'compensations': 'des', 'doses': 'des', 'sanctions': 'des', 'rest': 'le', 'others': 'les',
}


# ═══════════════════════════════════════════════════════════════════════════
# GABARITS D'OPÉRATIONS ÉTENDUS (25+)
# ═══════════════════════════════════════════════════════════════════════════

def generer_gabarits():
    """Retourne 25 séquences d'ops génériques de complexité variable."""
    # 1-4 : Opérations simples
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'SUBTRACT', 'value': 'B'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'ADD', 'value': 'B'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'DIVIDE', 'divisor': 'B'}]
    
    # 5-8 : Deux opérations
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'ADD', 'value': 'B'},
           {'op': 'SUBTRACT', 'value': 'C'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'ADD', 'value': 'C'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'SUBTRACT', 'value': 'C'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'DIVIDE', 'divisor': 'B'},
           {'op': 'MULTIPLY', 'multiplier': 'C'}]
    
    # 9-12 : Trois opérations
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'ADD', 'value': 'C'}, {'op': 'DIVIDE', 'divisor': 'D'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'SUBTRACT', 'value': 'B'},
           {'op': 'MULTIPLY', 'multiplier': 'C'}, {'op': 'SUBTRACT', 'value': 'D'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'ADD', 'value': 'B'},
           {'op': 'ADD', 'value': 'C'}, {'op': 'SUBTRACT', 'value': 'D'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'DIVIDE', 'divisor': 'C'}, {'op': 'MULTIPLY', 'multiplier': 'D'}]
    
    # 13-16 : Pourcentages (fractions)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'}]  # B = 0.6 (60%)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'SUBTRACT', 'value': 'C'}]  # C = A*B (le montant calculé)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'DIVIDE', 'divisor': 'B'},
           {'op': 'MULTIPLY', 'multiplier': 'C'}]  # fraction puis multiplication
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'MULTIPLY', 'multiplier': 'C'}]  # double pourcentage
    
    # 17-19 : Taux et durées
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'RATE', 'rate': 'B'},
           {'op': 'DURATION', 'duration': 'C'}]  # A × B × C
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'RATE', 'rate': 'C'}, {'op': 'DURATION', 'duration': 'D'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'RATE', 'rate': 'B'},
           {'op': 'DURATION', 'duration': 'C'}, {'op': 'ADD', 'value': 'D'}]
    
    # 20-22 : Multi-chain (plusieurs INITs)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'INIT', 'value': 'C'}, {'op': 'SUBTRACT', 'value': 'D'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'SUBTRACT', 'value': 'B'},
           {'op': 'INIT', 'value': 'C'}, {'op': 'ADD', 'value': 'D'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'INIT', 'value': 'C'}, {'op': 'MULTIPLY', 'multiplier': 'D'},
           {'op': 'ADD', 'value': 'E'}]
    
    # 23-25 : Séquences longues (4-5 opérations)
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'SUBTRACT', 'value': 'C'}, {'op': 'DIVIDE', 'divisor': 'D'},
           {'op': 'MULTIPLY', 'multiplier': 'E'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'ADD', 'value': 'B'},
           {'op': 'MULTIPLY', 'multiplier': 'C'}, {'op': 'SUBTRACT', 'value': 'D'},
           {'op': 'DIVIDE', 'divisor': 'E'}]
    yield [{'op': 'INIT', 'value': 'A'}, {'op': 'MULTIPLY', 'multiplier': 'B'},
           {'op': 'ADD', 'value': 'C'}, {'op': 'MULTIPLY', 'multiplier': 'D'},
           {'op': 'SUBTRACT', 'value': 'E'}, {'op': 'DIVIDE', 'divisor': 'F'}]


# ═══════════════════════════════════════════════════════════════════════════
# GÉNÉRATION
# ═══════════════════════════════════════════════════════════════════════════

def choisir_motif(op_name: str, domaine: str) -> str:
    """Choisit un motif linguistique aléatoire pour (op, domaine)."""
    motifs = MOTIFS.get((op_name, domaine), MOTIFS.get((op_name, 'maths'), ['performs']))
    return random.choice(motifs)


def generer_phrase(op: Dict, domaine: str, valeurs: Dict[str, float],
                   noms_utilises: List[str]) -> str:
    """Génère une phrase pour une opération dans un domaine donné."""
    op_name = op['op']
    motif = choisir_motif(op_name, domaine)
    val = valeurs[op['value']] if 'value' in op else valeurs.get(op.get('multiplier') or op.get('divisor') or op.get('rate') or op.get('duration'), 0)
    
    nom = random.choice([n for n in NOMS[domaine] if n not in noms_utilises or random.random() < 0.3])
    if nom not in noms_utilises:
        noms_utilises.append(nom)
    
    # Pour les pourcentages : transformer 0.6 en "60%"
    if op_name in ('MULTIPLY', 'DIVIDE') and val < 1 and val > 0:
        pct = int(val * 100)
        if random.random() < 0.5:
            return f"{pct}% of {nom}"
    
    return f"{motif} {val} {nom}"


def generer_exemple(ops_template: List[Dict], domaine: str,
                    valeurs: Dict[str, float]) -> Dict[str, str]:
    """Génère un exemple complet texte + ops."""
    contexte = random.choice(CONTEXTES[domaine])
    noms_utilises = []
    phrases = [contexte]

    for op in ops_template:
        op_name = op['op']
        if op_name == 'INIT':
            motif = choisir_motif('INIT', domaine)
            val = valeurs['A']
            nom = random.choice([n for n in NOMS[domaine] if n not in noms_utilises or random.random() < 0.3])
            noms_utilises.append(nom)
            phrases.append(f"{motif} {val} {nom}")
        elif op_name in ('SUBTRACT', 'ADD'):
            op_target = 'SUB' if op_name == 'SUBTRACT' else 'ADD'
            motif = choisir_motif(op_target, domaine)
            var = op.get('value', 'B')
            val = valeurs[var]
            nom = random.choice([n for n in NOMS[domaine] if n not in noms_utilises or random.random() < 0.3])
            noms_utilises.append(nom)
            # Pour les pourcentages
            if random.random() < 0.15 and val < 1:
                pct = int(val * 100)
                phrases.append(f"{pct}% of {nom}")
            else:
                phrases.append(f"{motif} {val} {nom}")
        elif op_name == 'MULTIPLY':
            motif = choisir_motif('MUL', domaine)
            var = op.get('multiplier', 'B')
            val = valeurs[var]
            nom = random.choice([n for n in NOMS[domaine] if n not in noms_utilises or random.random() < 0.3])
            noms_utilises.append(nom)
            if random.random() < 0.25 and val < 1:
                pct = int(val * 100)
                phrases.append(f"{pct}% of {nom}")
            else:
                phrases.append(f"{motif} {val} {nom}")
        elif op_name == 'DIVIDE':
            motif = choisir_motif('DIV', domaine)
            var = op.get('divisor', 'B')
            val = valeurs[var]
            nom = random.choice([n for n in NOMS[domaine] if n not in noms_utilises or random.random() < 0.3])
            noms_utilises.append(nom)
            phrases.append(f"{motif} {val} {nom}")
        elif op_name == 'RATE':
            var = op.get('rate', 'B')
            val = valeurs[var]
            nom = random.choice(NOMS[domaine])
            phrases.append(f"at a rate of {val} per {nom}")
        elif op_name == 'DURATION':
            var = op.get('duration', 'C')
            val = valeurs[var]
            nom = random.choice(['hours', 'days', 'weeks', 'months', 'years'])
            phrases.append(f"for {val} {nom}")

    texte = ', '.join(phrases) + '.'
    
    # Convertir les ops en cible texte
    cible_parts = []
    for op in ops_template:
        op_name = op['op']
        if op_name == 'INIT':
            cible_parts.append(f"INIT({valeurs['A']})")
        elif op_name == 'SUBTRACT':
            var = op.get('value', 'B')
            cible_parts.append(f"SUB({valeurs[var]})")
        elif op_name == 'ADD':
            var = op.get('value', 'B')
            cible_parts.append(f"ADD({valeurs[var]})")
        elif op_name == 'MULTIPLY':
            var = op.get('multiplier', 'B')
            cible_parts.append(f"MUL({valeurs[var]})")
        elif op_name == 'DIVIDE':
            var = op.get('divisor', 'B')
            cible_parts.append(f"DIV({valeurs[var]})")
        elif op_name == 'RATE':
            var = op.get('rate', 'B')
            cible_parts.append(f"MUL({valeurs[var]})")
        elif op_name == 'DURATION':
            var = op.get('duration', 'C')
            cible_parts.append(f"MUL({valeurs[var]})")

    return {'input': texte, 'target': ' '.join(cible_parts)}


def generer_dataset(n_exemples: int = 20000, seed: int = 42):
    """Génère un dataset transvertical enrichi."""
    random.seed(seed)
    domaines = list(MOTIFS.keys())
    domaines_uniques = list(set(d for _, d in domaines))
    domaines_uniques.sort()
    gabarits_liste = list(generer_gabarits())
    exemples = []

    for _ in range(n_exemples):
        g = random.choice(gabarits_liste)
        domaine = random.choice(domaines_uniques)
        # Valeurs aléatoires réalistes
        vals = {'A': random.randint(1, 100)}
        used = ['A']
        for op in g:
            for k in ('value', 'multiplier', 'divisor', 'rate', 'duration'):
                if k in op:
                    v = op[k]
                    if v not in vals:
                        if v == 'B': vals[v] = random.randint(1, 20)
                        elif v == 'C': vals[v] = random.randint(1, 15)
                        elif v == 'D': vals[v] = random.randint(1, 10)
                        elif v == 'E': vals[v] = random.randint(1, 8)
                        elif v == 'F': vals[v] = random.randint(1, 6)
                        used.append(v)
        ex = generer_exemple(g, domaine, vals)
        exemples.append(ex)

    return exemples


if __name__ == '__main__':
    print("═══ GÉNÉRATEUR TRANSVERTICAL V2 ═══\n")
    print("Gabarits : 25 séquences d'opérations")
    print("Domaines : 7 (maths, droit, medecine, logique, eco, physique, quotidien)")
    print("Motifs   : 10-20 expressions par opération × domaine\n")
    
    exemples = generer_dataset(20000)
    with open('data/transvertical_v2_train.jsonl', 'w', encoding='utf-8') as f:
        for ex in exemples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    
    print(f"✓ Dataset généré : {len(exemples)} exemples")
    print(f"  → data/transvertical_v2_train.jsonl")
    
    # Démo
    print("\nExemples :")
    for i in range(0, 20000, 4000):
        print(f"  [{i}] {exemples[i]['input'][:80]}...")
        print(f"      → {exemples[i]['target']}")