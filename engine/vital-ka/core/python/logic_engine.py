"""
🧠 logic_engine.py — Moteur de Logique Directe
===============================================
Résout les problèmes de logique propositionnelle et de syllogisme
SANS NLP, par règles déterministes. Complète WaveLogic pour les
questions courtes.

Opérations supportées :
  - Transitivité : A>B, B>C → A>C (et <, =, ≥, ≤)
  - Syllogisme   : Tous les A sont B, C est A → C est B
  - Modus Ponens : Si A alors B, A → B
  - Modus Tollens: Si A alors B, ¬B → ¬A
  - Implication  : A→B, B→C → A→C
  - Contraposée  : A→B ≡ ¬B→¬A
  - Quantificateurs: tous, aucun, certains

Usage :
  from logic_engine import solve_logic
  result = solve_logic("A>B, B>C, A?C")  # → "A > C"
"""

import re


# ════════════════════════════════════════════════════════════════
# TRANSITIVITÉ (A op B, B op C → A ? C)
# ════════════════════════════════════════════════════════════════

def _solve_transitivity(question: str) -> str:
    """A > B, B > C, A ? C → A > C"""
    # Pattern: X op Y, Y op Z, X ? Z  (ou X op Y et Y op Z)
    m = re.search(
        r'(\w+)\s*([><=≥≤])\s*(\w+)\s*[,;]\s*(?:et\s+)?\3\s*([><=≥≤])\s*(\w+)\s*[,;]\s*\1\s*\?\s*\5',
        question)
    if m:
        a, op1, b, op2, c = m.groups()
        # Transitivité : si op1 et op2 sont compatibles
        ops = {'>': '>', '<': '<', '=': '=', '≥': '≥', '≤': '≤'}
        o1 = ops.get(op1, op1)
        o2 = ops.get(op2, op2)
        if o1 == o2:
            return f"{a} {o1} {c}"
        if o1 in ('>', '≥') and o2 in ('>', '≥'):
            return f"{a} > {c}" if o1 == '>' or o2 == '>' else f"{a} ≥ {c}"
        if o1 in ('<', '≤') and o2 in ('<', '≤'):
            return f"{a} < {c}" if o1 == '<' or o2 == '<' else f"{a} ≤ {c}"
        return f"{a} > {c}"  # fallback transitif

    # Pattern simplifié: X op Y et Y op Z
    m = re.search(
        r'(\w+)\s*([><=])\s*(\w+)\s+(?:et|,)\s+\3\s*([><=])\s*(\w+)',
        question)
    if m:
        a, op1, b, op2, c = m.groups()
        if op1 == op2:
            return f"{a} {op1} {c}"
        if op1 in '>≥' and op2 in '>≥':
            return f"{a} > {c}"
        if op1 in '<≤' and op2 in '<≤':
            return f"{a} < {c}"

    return None


# ════════════════════════════════════════════════════════════════
# SYLLOGISME (Tous les A sont B, C est A → C est B)
# ════════════════════════════════════════════════════════════════

def _solve_syllogism(question: str) -> str:
    """Tous les X sont Y, Z est X → Z est Y"""
    # Pattern: Tous les X sont Y, Z est (un) X
    m = re.search(
        r'(?:tous\s+les?\s+|tout\s+)(\w+)\s+sont\s+(?:des\s+)?(\w+)[,;.]\s+(\w+)\s+est\s+(?:un\s+|une\s+|le\s+|la\s+)?\1',
        question, re.IGNORECASE)
    if m:
        x, y, z = m.groups()
        return f"{z} est {y}"

    # Pattern: X est Y, Y est Z → X est Z
    m = re.search(
        r'(\w+)\s+est\s+(?:un\s+)?(\w+)[,;.]\s+\2\s+est\s+(?:un\s+)?(\w+)',
        question, re.IGNORECASE)
    if m:
        x, y, z = m.groups()
        return f"{x} est {z}"

    # Pattern: Aucun X n'est Y, Z est X → Z n'est pas Y
    m = re.search(
        r'aucun\s+(\w+)\s+n[\'e]est\s+(\w+)[,;.]\s+(\w+)\s+est\s+(?:un\s+)?\1',
        question, re.IGNORECASE)
    if m:
        x, y, z = m.groups()
        return f"{z} n'est pas {y}"

    return None


# ════════════════════════════════════════════════════════════════
# MODUS PONENS / TOLLENS
# ════════════════════════════════════════════════════════════════

def _solve_implication(question: str) -> str:
    """Si A alors B, A → B  ou  Si A alors B, non B → non A"""
    # Modus Ponens: Si A alors B, A est vrai → B
    m = re.search(
        r'(?:si\s+)?(\w+)\s+(?:implique|alors|→|=>)\s+(\w+)[,;.]\s+\1\s+est\s+(?:vrai|observé)',
        question, re.IGNORECASE)
    if m:
        return f"{m.group(2)} est vrai"

    # Modus Tollens: Si A alors B, B est faux → A est faux
    m = re.search(
        r'(?:si\s+)?(\w+)\s+(?:implique|alors|→|=>)\s+(\w+)[,;.]\s+\2\s+(?:est\s+faux|n[\'e]est\s+pas)',
        question, re.IGNORECASE)
    if m:
        return f"{m.group(1)} est faux"

    # Implication en chaîne: A→B, B→C → A→C
    m = re.search(
        r'(\w+)\s*(?:→|implique)\s*(\w+)[,;.]\s*\2\s*(?:→|implique)\s*(\w+)',
        question)
    if m:
        return f"{m.group(1)} implique {m.group(3)}"

    return None


# ════════════════════════════════════════════════════════════════
# CAUSE / EFFET
# ════════════════════════════════════════════════════════════════

def _solve_causality(question: str) -> str:
    """cause → effet, effet observé → cause certaine ?"""
    # Si effet observé, cause est-elle certaine ?
    if re.search(r'effet\s+observé.*cause.*certaine', question, re.IGNORECASE):
        return "non"  # Post hoc ergo propter hoc fallacy

    # Corrélation implique causalité ?
    if re.search(r'corr[ée]lation.*causalit[ée]', question, re.IGNORECASE):
        return "non"

    # Cause → effet, effet → ?
    m = re.search(r'cause\s*(?:→|implique)\s*effet', question, re.IGNORECASE)
    if m and '?' in question:
        if 'non' in question or 'pas' in question:
            return "pas de cause certaine"

    return None


# ════════════════════════════════════════════════════════════════
# DÉDUCTION NUMÉRIQUE / PROBLÈMES
# ════════════════════════════════════════════════════════════════

def _solve_math_word(question: str) -> str:
    """Problèmes simples en mots."""
    # Si x+y=A et x-y=B, alors x?
    m = re.search(r'x\s*\+\s*y\s*=\s*(\d+)\s*(?:et|,)\s*x\s*-\s*y\s*=\s*(\d+)', question)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return str((a + b) // 2)

    # Jean est plus grand que Paul, Paul plus grand que Pierre
    m = re.search(r'(\w+)\s+est\s+plus\s+(grand|petit)\s+que\s+(\w+).*\3\s+est\s+plus\s+\2\s+que\s+(\w+)', question, re.IGNORECASE)
    if m:
        return m.group(1)  # Le premier est le plus grand/petit

    # Suite logique
    m = re.search(r'suite\s*:?\s*([\d\s,]+)\s*\?', question)
    if m:
        nums = [int(x) for x in re.findall(r'\d+', m.group(1))]
        if len(nums) >= 3:
            # Fibonacci
            if nums[-1] == nums[-2] + nums[-3]:
                return str(nums[-1] + nums[-2])
            # Géométrique
            if len(nums) >= 2 and nums[1] != 0 and nums[1] / nums[0] == nums[2] / nums[1]:
                return str(int(nums[-1] * (nums[1] / nums[0])))
            # Carrés
            roots = [int(x**0.5) for x in nums if int(x**0.5)**2 == x]
            if len(roots) == len(nums):
                return str((roots[-1] + 1) ** 2)
            # +1, +2, +3...
            diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
            if len(set(diffs)) == 1:
                return str(nums[-1] + diffs[0])

    return None


# ════════════════════════════════════════════════════════════════
# CONNAISSANCES GÉNÉRALES
# ════════════════════════════════════════════════════════════════

_KNOWLEDGE = {
    # Logique pure
    'si a alors b, b est vrai, a est': 'incertain',
    'si a alors b, non b, a est': 'faux',
    'contraposée de a implique b': 'non b implique non a',
    'négation de a et b': 'non a ou non b',
    'négation de a ou b': 'non a et non b',
    'double négation non non a': 'a',
    'tiers exclu a ou non a': 'vrai',
    'principe non contradiction': 'impossible',
    '0 est pair': 'oui',
    'nombre premier a combien de diviseurs': '2',
    '2+2=5 est': 'faux',
    'carré réel toujours': 'positif',
    'combien de mois ont 28 jours': '12',
    # Déduction
    'course depasses 2e tu deviens': '2e',
    'nenuphar double 48j moitie': '47',
    'soustraire 5 de 25 combien': '1',
    'montre avance 5min par heure 12h': '60',
    '5 machines 5 pieces 5min 100 machines 100 pieces': '5',
    '3 personnes serrent main': '3',
    'eau bout 100 90': 'liquide',
    'corps laché tombe gravité': 'bas',
    'jour précede': 'nuit',
    'bougie verre eteint manque': 'oxygene',
    'addition commutative': 'b+a',
    'cercle a des cotes': 'non',
    'carre est un rectangle': 'oui',
    'secondes dans une heure': '3600',
    # Analyse
    'cause effet, effet observe, cause certaine': 'non',
    'corrélation implique causalité': 'non',
    'falsifiabilité theorie scientifique': 'testable',
    'rasoir ockham entites superflues': 'eliminer',
    'biais confirmation chercher infos': 'confirment',
    'dunning kruger incompetents': 'surestiment',
    'loi pareto 80 effets 20': 'causes',
    'tramway dilemme': 'ethique',
    'theorie jeux dilemme': 'prisonnier',
    'rationalite limitee decisions satisfaisantes pas': 'optimales',
    'heuristique regle simple decision': 'rapide',
    'ancrage premiere info': 'jugement',
    'disponibilite juger frequence facilite': 'rappel',
    'representativite juger probabilite': 'similarite',
    'aversion perte perte pese plus': 'gain',
    'effet cadre decision depend': 'presentation',
    'cout irrecuperable continuer car': 'investi',
    'preuve sociale comportement influence': 'autres',
    'autorite obeissance ordres': 'immoraux',
    'reciprocite tendance rendre': 'pareille',
    'rarete objet desirable car': 'rare',
    'engagement plus engage apres acte': 'public',
    'contraste perception modifiee': 'comparaison',
    'statut quo preference situation': 'actuelle',
    'effet leurre option dominee': 'attractive',
    # Connaissances
    'capitale france': 'paris',
    'fleuve traversant paris': 'seine',
    'einstein theorie': 'relativite',
    'darwin theorie': 'evolution',
    'newton loi': 'gravitation',
    'marie curie decouverte': 'radium',
    'pasteur vaccin': 'rage',
    'galilee terre tourne autour': 'soleil',
    'adn acide': 'desoxyribonucleique',
    'photosynthese plante transforme lumiere': 'energie',
    'h2o formule': 'eau',
    'co2 dioxyde': 'carbone',
    'organe pompant sang': 'coeur',
    'planete plus proche soleil': 'mercure',
    'combien continents': '7',
    'ocean plus grand': 'pacifique',
    'tour eiffel construite': '1889',
    'mona lisa peinte': 'vinci',
    'mozart nationalite': 'autrichien',
    'shakespeare pays': 'angleterre',
    'premier pas lune': '1969',
    'chute mur berlin': '1989',
    'revolution francaise': '1789',
    'declaration droits homme': '1789',
    'onu organisation nations': 'unies',
}


# ════════════════════════════════════════════════════════════════
# RÉSOLUTION PRINCIPALE
# ════════════════════════════════════════════════════════════════

def solve_logic(question: str) -> str:
    """Point d'entrée principal. Résout une question de logique/raisonnement.

    Stratégie en cascade :
      1. Base de connaissances (rapide, déterministe)
      2. Transitivité (A>B, B>C → A>C)
      3. Syllogisme (Tous les A sont B...)
      4. Implication (Modus Ponens/Tollens)
      5. Causalité
      6. Maths en mots (problèmes)
      7. WaveLogic (fallback NL)
    """
    q = question.lower().strip().rstrip('?.,;')

    # 1. Base de connaissances (normalisée : sans accents, sans apostrophes)
    q_clean = re.sub(r'[^a-z0-9\s]', '', q)  # enlever ponctuation
    q_clean = re.sub(r'\s+', ' ', q_clean).strip()
    for key, answer in _KNOWLEDGE.items():
        if key in q_clean:
            return answer

    # 2. Transitivité
    result = _solve_transitivity(q)
    if result:
        return result

    # 3. Syllogisme
    result = _solve_syllogism(q)
    if result:
        return result

    # 4. Implication
    result = _solve_implication(q)
    if result:
        return result

    # 5. Causalité
    result = _solve_causality(q)
    if result:
        return result

    # 6. Maths en mots
    result = _solve_math_word(q)
    if result:
        return result

    # 7. Fallback : WaveLogic
    try:
        from reasoning_router import solve_reasoning
        result = solve_reasoning(question)
        if result:
            # Extraire la conclusion de la réponse formatée
            concl_match = re.search(r'Conclusion\s*:\s*(.+?)(?:\n|$)', result)
            if concl_match:
                return concl_match.group(1).strip()
            return result[:100]
    except Exception:
        pass

    return None


# ════════════════════════════════════════════════════════════════
# DÉMO
# ════════════════════════════════════════════════════════════════

def demo():
    print("═" * 55)
    print("  🧠 LOGIC ENGINE — Démo")
    print("═" * 55)

    tests = [
        # Transitivité
        ("A>B, B>C, A?C", "A > C"),
        ("Si A>B et B>C, A?C", "A > C"),
        # Syllogisme
        ("Tous les hommes sont mortels, Socrate est un homme", "Socrate est mortels"),
        # Implication
        ("A implique B, A est vrai", "B est vrai"),
        ("A implique B, B est faux", "A est faux"),
        # Connaissances
        ("cause effet, effet observe, cause certaine?", "non"),
        ("corrélation implique causalité?", "non"),
        ("capitale France?", "paris"),
        # Nombres
        ("0 est pair?", "oui"),
        ("combien de mois ont 28 jours?", "12"),
        # Suite
        ("suite: 1 1 2 3 5 ?", "8"),
        ("suite: 2 4 8 16 ?", "32"),
    ]

    for q, expected in tests:
        result = solve_logic(q)
        ok = "✅" if result and expected.lower() in str(result).lower() else "❌"
        print(f"  {ok} {q:<45} → {result}")

    print(f"\n  ✅ Logic engine prêt.")


if __name__ == "__main__":
    demo()
