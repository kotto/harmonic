"""
Intent Router — Routeur unifié d'intention
===========================================
Détecte le type de question et route vers le bon moteur.

  Question → intent_router → {math | code_frontend | code_algo | kb | conversation}
                               ↓
                    Dispatch vers le bon moteur
"""

import re
from typing import Optional, Tuple, Dict

# Mots-clés mathématiques (FR + EN)
MATH_KEYWORDS = frozenset([
    # Calcul symbolique
    'dérivée', 'dérivé', 'derivative', 'diff', 'd/dx',
    'intégrale', 'integrál', 'integral', 'intégration', 'primitive',
    'limite', 'limit', 'tend vers', 'as x approaches',
    'résoudre', 'résous', 'solve', 'trouver x',
    'matrice', 'matrix', 'déterminant', 'determinant', 'eigenvalue', 'valeur propre',
    'équation', 'equation', 'polynôme', 'polynomial',
    'factoriser', 'factor', 'développer', 'expand',
    'simplifier', 'simplify', 'réduire',
    'série de taylor', 'taylor series', 'développement limité',
    'fonction', 'cosinus', 'sinus', 'tangente', 'logarithme', 'exponentielle',
    'théorème', 'theorem', 'preuve', 'proof', 'démontrer',
    'nombre premier', 'prime number',
    'probabilité', 'probability', 'espérance', 'variance', 'écart-type',
    'aire', 'surface', 'périmètre', 'volume',
    'produit scalaire', 'dot product', 'vecteur', 'vector',
    # Arithmétique
    'calculer', 'compute', 'combien', 'calcule',
    'racine', 'sqrt', 'square root', 'carrée', 'carré', 'carre', 'cube',
    'puissance', 'power', 'exponent', 'exposant',
    'factorielle', 'factorial',
    'pourcent', 'pourcentage', 'percent', '%',
    'fois', 'multiplié', 'multiplier', 'divisé', 'diviser',
    'addition', 'additionner', 'soustraction', 'soustraire',
    'plus', 'moins', 'divise',
    # Motifs numériques (détection de pattern)
    'km/h', 'm/s', '€', 'euros', 'dollars',
])

# Mots-clés raisonnement (FR + EN)
REASONING_KEYWORDS = frozenset([
    'si', 'alors', 'donc', 'déduire', 'déduis', 'deduire', 'deduis',
    'syllogisme', 'prémisse', 'premisse', 'premise',
    'conclusion', 'raisonnement', 'reasoning',
    'logique', 'logic', 'inférence', 'inference',
    'tous les', 'tout les', 'chaque', 'aucun', 'certains',
    'est un', 'sont des', 'fait partie',
    'modus ponens', 'modus tollens',
    'contraposée', 'contraposee', 'reciproque',
    'vrai ou faux', 'vrai/faux', 'true/false',
    'que peut-on', 'que peut on', 'qu\'est-ce qu\'on',
    'peut-on conclure', 'peut on conclure',
    'est-il vrai', 'est il vrai',
    'prouver', 'démontrer', 'demonter', 'montrer que',
    'supposons', 'hypothèse', 'hypothese',
    'implique', 'entraîne', 'entraine',
    'contradiction', 'paradoxe',
    'nécessairement', 'obligatoirement', 'forcement',
    'analogie', 'analogue', 'similaire à',
])

# Mots-clés code frontend
CODE_FRONTEND_KEYWORDS = frozenset([
    'react', 'vue', 'angular', 'svelte', 'solid',
    'css', 'scss', 'sass', 'tailwind', 'bootstrap',
    'html', 'jsx', 'tsx', 'sfc',
    'composant', 'component', 'widget',
    'flexbox', 'grid', 'responsive', 'media query',
    'dark mode', 'thème', 'theme',
    'hook', 'usestate', 'useeffect', 'usecontext',
    'pinia', 'vuex', 'redux', 'context api',
    'props', 'v-model', 'v-for', 'slot',
    'formulaire', 'form', 'modal', 'dialog',
    'navbar', 'sidebar', 'card', 'button', 'input',
    'vite', 'webpack', 'rollup', 'esbuild',
    'darkmode', 'animation css', 'transition',
])

# Mots-clés code algorithmique
CODE_ALGO_KEYWORDS = frozenset([
    'fonction', 'function', 'algorithme', 'algorithm',
    'python', 'javascript', 'typescript', 'java', 'rust', 'go', 'c++', 'sql',
    'tri', 'sort', 'recherche', 'search', 'binary search',
    'liste chaînée', 'linked list', 'arbre', 'tree', 'graphe', 'graph',
    'récursion', 'recursion', 'recursive',
    'hashtable', 'hash map', 'pile', 'stack', 'file', 'queue',
    'pointeur', 'pointer', 'classe', 'class', 'objet', 'object',
    'api', 'endpoint', 'rest', 'graphql',
    'regex', 'parsing', 'serialize', 'deserialize',
    'fizzbuzz', 'fibonacci', 'palindrome',
    'écris du code', 'code en', 'génère', 'génère un',
    'script', 'débug', 'debug', 'bug', 'fix',
])


def _kw_match(kw: str, q: str) -> bool:
    """
    Mot-clé court (≤3 lettres, sans espace) → frontière de mot :
    « si » ne doit pas matcher « hypertenSIon ».
    Mots longs et phrases → sous-chaîne (suffisamment discriminant).
    """
    if len(kw) <= 3 and ' ' not in kw:
        return re.search(rf'\b{re.escape(kw)}\b', q) is not None
    return kw in q


def detect_intent(question: str) -> Dict:
    """
    Détecte l'intention principale de la question.

    Returns:
        Dictionnaire avec:
          - intent: 'math' | 'code_frontend' | 'code_algo' | 'kb' | 'conversation'
          - confidence: 0-1
          - detected_keywords: liste des mots-clés trouvés
          - frontend_template: nom du template frontend (si applicable)
    """
    q = question.lower()

    # Compter les matchs par catégorie
    math_hits = sum(1 for kw in MATH_KEYWORDS if _kw_match(kw, q))
    fe_hits = sum(1 for kw in CODE_FRONTEND_KEYWORDS if _kw_match(kw, q))
    algo_hits = sum(1 for kw in CODE_ALGO_KEYWORDS if _kw_match(kw, q))

    detected = []
    for kw in MATH_KEYWORDS:
        if _kw_match(kw, q): detected.append(kw)
    for kw in CODE_FRONTEND_KEYWORDS:
        if _kw_match(kw, q): detected.append(kw)
    for kw in CODE_ALGO_KEYWORDS:
        if _kw_match(kw, q): detected.append(kw)

    # Détection raisonnement
    reason_hits = 0
    reason_detected = []
    for kw in REASONING_KEYWORDS:
        if _kw_match(kw, q):
            reason_hits += 1
            reason_detected.append(kw)

    # Décider
    scores = {
        'math': math_hits,
        'code_frontend': fe_hits,
        'code_algo': algo_hits,
        'reasoning': reason_hits,
    }

    # Détection arithmétique par pattern numérique (fallback)
    if math_hits == 0:
        # Chercher des patterns numériques: X + Y, X - Y, X * Y, X / Y, X^Y
        if re.search(r'\d+\s*[\+\-\*/×\^]\s*\d+', q):
            math_hits = 1
            scores['math'] = 1
        # Pourcentage: X% de Y
        elif re.search(r'\d+\s*%', q):
            math_hits = 1
            scores['math'] = 1
        # Puissance: X^Y, X**Y
        elif re.search(r'\d+\s*\^', q):
            math_hits = 1
            scores['math'] = 1

    best = max(scores, key=scores.get)
    best_score = scores[best]

    result = {
        'intent': best if best_score > 0 else 'kb',
        'confidence': min(1.0, best_score / 3.0),
        'detected_keywords': detected[:10] + reason_detected[:5],
        'reason_hits': reason_hits,
        'math_hits': math_hits,
        'code_frontend': fe_hits,
        'code_algo': algo_hits,
    }

    # Détection de template frontend spécifique
    if best == 'code_frontend' or fe_hits > 0:
        try:
            from frontend_templates import detect_frontend_intent
            fe_result = detect_frontend_intent(question)
            if fe_result:
                result['frontend_template'] = fe_result[0]
                result['frontend_language'] = fe_result[1]
        except ImportError:
            pass

    # Cas spécial: salutation
    if any(w in q for w in ['bonjour', 'salut', 'hello', 'merci', 'au revoir']):
        result['intent'] = 'conversation'

    return result


def route(question: str) -> Optional[str]:
    """
    Route une question vers le bon moteur et retourne la réponse.

    Returns:
        La réponse, ou None si la question doit aller au cerveau harmonique.
    """
    # 🌊 Normaliser les questions courtes → langage naturel
    original = question
    if len(question.split()) <= 5:
        try:
            from query_normalizer import normalize
            question = normalize(question)
        except Exception:
            pass

    intent = detect_intent(question)

    # 1. MATH → CAS symbolique + micro-calculateur
    if intent['intent'] == 'math' or intent.get('math_hits', 0) > 0:
        try:
            from math_bridge import try_math_solve
            result = try_math_solve(question)
            if result:
                return result
        except Exception:
            pass
        # Fallback pour questions courtes sans mot-clé : tenter le CAS directement
        if len(question.split()) <= 5:
            try:
                from math_bridge import try_math_solve
                result = try_math_solve(question)
                if result and len(result) > 2:
                    return result
            except Exception:
                pass

    # 2. CODE FRONTEND → templates frontend + hologramme CODE
    if intent.get('frontend_template'):
        try:
            from frontend_templates import generate_frontend
            code = generate_frontend(intent['frontend_template'])
            if code:
                lang = intent.get('frontend_language', 'jsx')
                return f"```{lang}\n{code}\n```"
        except Exception:
            pass
    
    # Fallback CODE : chercher dans l'hologramme CODE
    if intent['intent'] in ('code_frontend', 'code_algo') or intent.get('code_frontend', 0) > 0 or intent.get('code_algo', 0) > 0:
        try:
            from hologram_router import HologramRouter
            router = HologramRouter('data/holograms')
            facts = router.retrieve_facts('CODE', question, top_k=3)
            if facts:
                lines = []
                for f in facts:
                    lines.append(f"// {f['sujet'][:60]}")
                    lines.append(f"{f['objet'][:120]}")
                return '\n'.join(lines[:8])
        except Exception:
            pass

    # 3. CODE ALGO → code_generator
    if intent['intent'] == 'code_algo':
        return None

    # 4. RAISONNEMENT → wave_logic + logic_engine
    if intent['intent'] == 'reasoning' or intent.get('reason_hits', 0) > 0:
        # Essayer d'abord le moteur de logique directe (rapide, déterministe)
        try:
            from logic_engine import solve_logic
            result = solve_logic(question)
            if result:
                return result
        except Exception:
            pass
        # Fallback : WaveLogic
        try:
            from reasoning_router import solve_reasoning
            result = solve_reasoning(question)
            if result:
                return result
        except Exception:
            pass

    # 5. KB / conversation → cerveau harmonique
    return None


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

def _test():
    print("=" * 60)
    print("TEST : Intent Router")
    print("=" * 60)

    tests = [
        ("dérivée de x^3 + 2x", "math"),
        ("résoudre x^2 - 5x + 6 = 0", "math"),
        ("intégrale de sin(x)", "math"),
        ("limite de sin(x)/x quand x tend vers 0", "math"),
        ("crée un formulaire React", "code_frontend"),
        ("composant Vue avec script setup", "code_frontend"),
        ("CSS grid responsive", "code_frontend"),
        ("glassmorphism effect", "code_frontend"),
        ("écris une fonction de tri en Python", "code_algo"),
        ("algorithme de recherche binaire", "code_algo"),
        ("qu'est-ce que la photosynthèse", "kb"),
        ("bonjour comment ça va", "conversation"),
        ("qui a écrit Les Misérables", "kb"),
    ]

    correct = 0
    for q, expected in tests:
        result = detect_intent(q)
        intent = result['intent']
        template = result.get('frontend_template', '')
        ok = "✅" if intent == expected else "❌"
        extra = f" → {template}" if template else ""
        print(f"  {ok} '{q[:40]}' → {intent}{extra}")
        if intent == expected:
            correct += 1

    print(f"\n{correct}/{len(tests)} corrects")

    # Test routing
    print("\n─── Routing ───")
    for q in ["dérivée de x^3 + 2x", "crée un composant React modal", "CSS flexbox layout"]:
        result = route(q)
        if result:
            print(f"  '{q}' → {result[:80]}...")
        else:
            print(f"  '{q}' → (delegated to brain)")


if __name__ == '__main__':
    _test()
