"""
📝 query_normalizer.py — Normaliseur de requêtes courtes → langage naturel
===========================================================================
Transforme les questions télégraphiques/mots-clés en français naturel
pour le routeur intent_router, qui est conçu pour le langage naturel.

Principe : « 7×8 » → « combien font 7 fois 8 ? »
          « CSS color » → « quelle est la propriété CSS pour la couleur ? »
          « Si A>B, B>C, A?C » → « Si A > B et B > C, que vaut A par rapport à C ? »

Fonctionne par rewriting + expansion contextuelle, SANS LLM.
Intégrable en une ligne dans intent_router.route().

Usage :
  from query_normalizer import normalize
  question_nl = normalize("7×8")  # → "combien font 7 fois 8 ?"
"""

import re


# ════════════════════════════════════════════════════════════════
# RÈGLES DE RÉÉCRITURE
# ════════════════════════════════════════════════════════════════

# Pattern → expansion (dans l'ordre de priorité)
_MATH_PATTERNS = [
    # Opérations arithmétiques : X op Y
    (r'^(-?\d+\.?\d*)\s*([×\*])\s*(-?\d+\.?\d*)$', r'combien font \1 fois \3 ?'),
    (r'^(-?\d+\.?\d*)\s*([\+])\s*(-?\d+\.?\d*)$', r'combien font \1 plus \3 ?'),
    (r'^(-?\d+\.?\d*)\s*([\-])\s*(-?\d+\.?\d*)$', r'combien font \1 moins \3 ?'),
    (r'^(-?\d+\.?\d*)\s*([÷/])\s*(-?\d+\.?\d*)$', r'combien font \1 divisé par \3 ?'),
    (r'^(-?\d+\.?\d*)\s*\^\s*(-?\d+\.?\d*)$', r'combien font \1 puissance \3 ?'),
    # Puissance
    (r'^(\d+)\^(\d+)$', r'combien font \1 puissance \2 ?'),
    # Racine
    (r'^racine\s*(?:carrée?\s*)?(?:de\s*)?(\d+)$', r'quelle est la racine carrée de \1 ?'),
    (r'^√\s*(\d+)$', r'quelle est la racine carrée de \1 ?'),
    # Factorielle
    (r'^factorielle\s*(\d+)$', r'combien font factorielle \1 ?'),
    # Pourcentage
    (r'^(\d+)\s*%\s*(?:de\s*)?(\d+)$', r'combien font \1 pourcent de \2 ?'),
    # Dérivée
    (r'^dérivée?\s+(?:de\s+)?(.+)$', r'quelle est la dérivée de \1 ?'),
    # Intégrale
    (r'^intégrale?\s+(?:de\s+)?(.+)$', r'quelle est l\'intégrale de \1 ?'),
    # Équation
    (r'^résoudre\s+(.+)$', r'résoudre l\'équation \1'),
    # Single number = "que vaut X ?"
    (r'^(-?\d+\.?\d*)$', r'que vaut \1 ?'),
]

_CODE_PATTERNS = [
    # CSS property
    (r'^CSS\s+(.+)$', r'quelle est la propriété CSS \1 ?'),
    (r'^css\s+(.+)$', r'comment utiliser \1 en CSS ?'),
    # HTML tag
    (r'^HTML\s+(.+)$', r'quelle est la balise HTML pour \1 ?'),
    (r'^balise\s+(.+)$', r'quelle est la balise HTML \1 ?'),
    # SQL
    (r'^SQL\s+(.+)$', r'comment écrire \1 en SQL ?'),
    # Python function
    (r'^(afficher|importer|boucler|définir)\s+(.+)$', r'comment \1 \2 en Python ?'),
]

_REASONING_PATTERNS = [
    # Transitivity: A op B, B op C → A ? C
    (r'^(?:si\s+)?(\w+)\s*([><=])\s*(\w+)\s*,?\s*(\w+)\s*([><=])\s*(\w+)\s*,?\s*(\w+)\s*\?\s*(\w+)$',
     r'Si \1 est \2 que \3 et que \4 est \5 que \6, que peut-on déduire sur \7 et \8 ?'),
    # Simple: A op B → A ? C
    (r'^(?:si\s+)?(\w+)\s*([><=])\s*(\w+)\s*,?\s*alors\s+(\w+)\s*\?\s*(\w+)$',
     r'Si \1 est \2 que \3, que vaut \4 par rapport à \5 ?'),
    # Tous les X sont Y
    (r'^tous\s+(.+)$', r'Tous \1. Que peut-on déduire ?'),
    # Implication
    (r'^(\w+)\s*→\s*(\w+)\s*,?\s*(\w+)\s*→\s*(\w+)$', r'Si \1 implique \2 et \3 implique \4, que conclure ?'),
]

_KNOWLEDGE_PATTERNS = [
    # Capitale
    (r'^capitale\s+(?:de\s+)?(.+)$', r'Quelle est la capitale de \1 ?'),
    # Définition
    (r'^(?:qu\'?est[-\s]ce\s+qu[-\s]|c\'?est\s+quoi\s+)(.+)$', r'Qu\'est-ce que \1 ?'),
    # Découverte
    (r'^qui\s+a\s+découvert\s+(.+)$', r'Qui a découvert \1 ?'),
    # Date
    (r'^(?:quand|en\s+quelle\s+année)\s+(.+)$', r'En quelle année \1 ?'),
]


# ════════════════════════════════════════════════════════════════
# NORMALISEUR PRINCIPAL
# ════════════════════════════════════════════════════════════════

def normalize(question: str) -> str:
    """Transforme une question courte en langage naturel.

    Si la question est déjà en langage naturel (longue, avec des mots),
    elle est retournée telle quelle.
    """
    q = question.strip()

    # Si la question est déjà longue → ne pas toucher
    if len(q.split()) >= 5:
        return q

    # Si contient déjà des mots français → ne pas toucher
    french_words = ['combien', 'quelle', 'comment', 'pourquoi', 'qui', 'quand',
                    'résoudre', 'calculer', 'trouver', 'expliquer', 'donne']
    if any(w in q.lower() for w in french_words):
        return q

    # Essayer chaque catégorie de patterns
    for category, patterns in [
        ("math", _MATH_PATTERNS),
        ("code", _CODE_PATTERNS),
        ("reasoning", _REASONING_PATTERNS),
        ("knowledge", _KNOWLEDGE_PATTERNS),
    ]:
        for pattern, replacement in patterns:
            try:
                m = re.match(pattern, q, re.IGNORECASE)
                if m:
                    expanded = m.expand(replacement)
                    return expanded
            except (re.error, IndexError):
                continue  # Skip broken patterns silently

    # Fallback : ajouter un contexte minimal
    if len(q.split()) <= 2:
        return f"explique moi : {q}"

    return q


# ════════════════════════════════════════════════════════════════
# DÉMO
# ════════════════════════════════════════════════════════════════

def demo():
    print("═" * 60)
    print("  📝 QUERY NORMALIZER — Démo")
    print("═" * 60)

    tests = [
        # Maths
        ("7×8", "math"),
        ("2^10", "math"),
        ("√169", "math"),
        ("racine 144", "math"),
        ("15% de 200", "math"),
        ("dérivée de x^2", "math"),
        ("résoudre x+5=10", "math"),
        # Code
        ("CSS color", "code"),
        ("HTML div", "code"),
        ("balise lien", "code"),
        ("SQL SELECT", "code"),
        # Raisonnement
        ("A>B, B>C, A?C", "reasoning"),
        ("A→B, B→C", "reasoning"),
        # Connaissance
        ("capitale France", "knowledge"),
        ("qui a découvert l'Amérique", "knowledge"),
        # Déjà NL (inchangé)
        ("combien font 7 fois 8", "déjà NL"),
    ]

    for q, expected_type in tests:
        result = normalize(q)
        changed = "🔄" if result != q else "✅"
        print(f"  {changed} [{expected_type:<10}] {q:<25} → {result}")

    print(f"\n  ✅ Query normalizer prêt.")


if __name__ == "__main__":
    demo()
