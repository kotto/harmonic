#!/usr/bin/env python3
"""
Harmonic Classifier
===================
Module de classification partage entre le moteur de resonance harmonique
et le generateur de contenu harmonique.

Centralise la detection de categorie des prompts pour eviter la duplication
de code entre harmonic_lm_arena_engine.py et harmonic_content_generator.py.

Auteur : Harmonic AI Research
Date : 24/05/2026
"""

import re
from typing import Tuple, Optional


# ----------------------------------------------------------------------------
# CONSTANTES DE CLASSIFICATION
# ----------------------------------------------------------------------------

# Mots-cles de detection par categorie
CATEGORY_KEYWORDS = {
    "factual": [
        "what is", "who is", "where is", "when did", "when was",
        "capital of", "inventor", "father of", "year of",
        "speed of", "population", "largest", "highest", "longest",
        "chemical", "atomic", "boiling", "freezing", "definition",
        "define", "describe", "list", "what are", "what was",
    ],
    "reasoning": [
        "explain", "why", "how does", "how do", "how can",
        "reason", "analyze", "analyse", "difference between",
        "compare", "contrast", "what if", "what would",
        "explain why", "explain how", "cause", "effect",
        "implication", "consequence", "argument", "debate",
    ],
    "mathematical": [
        "solve", "calculate", "equation", "math", "=",
        "+", "-", "*", "/", "x^", "integral", "derivative",
        "function f(", "graph", "matrix", "vector",
        "probability", "statistic", "theorem", "proof",
        "algebra", "geometry", "trigonometry",
    ],
    "creative": [
        "write a poem", "write a story", "write an essay",
        "creative", "poem", "story about", "imagine",
        "compose", "song", "lyrics", "create a",
        "invent", "design a", "draw", "paint",
        "metaphor", "analogy", "narrative", "tale",
        "fiction", "fantasy", "dream", "vision",
    ],
    "code": [
        "function", "code", "python", "javascript",
        "program", "algorithm", "implement", "class",
        "def ", "import", "api", "endpoint", "route",
        "database", "sql", "html", "css", "react",
        "debug", "error", "bug", "compile",
        "git", "docker", "deploy", "server",
    ],
}

# Salutations generales (categorie "general")
GREETING_PATTERNS = [
    r'\bbonjour\b', r'\bsalut\b', r'\bhello\b', r'\bhi\b',
    r'\bbonsoir\b', r'\bbon matin\b', r'\bbonne journee\b',
    r'\bca va\b', r'\bcomment allez\b', r'\bcomment vas\b',
    r'\benchante\b', r'\bhey\b', r'\bcoucou\b',
    r'\bgood morning\b', r'\bgood evening\b', r'\bgood afternoon\b',
    r'\bhow are you\b', r'\bhow do you do\b', r'\bnice to meet\b',
]


def detect_category(prompt: str) -> str:
    """
    Detecte la categorie d'un prompt automatiquement.
    
    Args:
        prompt: Le texte du prompt utilisateur
        
    Returns:
        str: La categorie detectee ("factual", "reasoning", "mathematical",
             "creative", "code", ou "general")
    """
    prompt_lower = prompt.lower().strip()
    
    # Verifier d'abord les salutations generales
    for gp in GREETING_PATTERNS:
        if re.search(gp, prompt_lower):
            words = prompt_lower.split()
            if len(words) <= 5:
                return "general"
    
    # Parcourir les categories par ordre de specificite
    # (les plus specifiques en premier)
    category_order = ["mathematical", "code", "creative", "reasoning", "factual"]
    
    for category in category_order:
        keywords = CATEGORY_KEYWORDS.get(category, [])
        for kw in keywords:
            if kw in prompt_lower:
                return category
    
    return "general"


def detect_category_with_confidence(prompt: str) -> Tuple[str, float]:
    """
    Detecte la categorie d'un prompt avec un score de confiance.
    
    Args:
        prompt: Le texte du prompt utilisateur
        
    Returns:
        Tuple[str, float]: (categorie, score_de_confiance)
    """
    prompt_lower = prompt.lower().strip()
    words = prompt_lower.split()
    word_count = len(words)
    
    if word_count == 0:
        return ("general", 0.0)
    
    # Verifier les salutations generales
    for gp in GREETING_PATTERNS:
        if re.search(gp, prompt_lower):
            if word_count <= 5:
                return ("general", 0.0)
    
    # Compter les matches par categorie
    scores = {}
    total_matches = 0
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        match_count = 0
        for kw in keywords:
            if kw in prompt_lower:
                match_count += 1
        scores[category] = match_count
        total_matches += match_count
    
    if total_matches == 0:
        return ("general", 0.0)
    
    # Calculer le score normalise
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category] / max(total_matches, 1)
    
    # Ajuster par la longueur du prompt
    # (plus le prompt est long, plus la confiance est elevee)
    length_factor = min(1.0, word_count / 20.0)
    confidence = best_score * (0.5 + 0.5 * length_factor)
    
    if confidence < 0.15:
        return ("general", confidence)
    
    return (best_category, min(1.0, confidence))


def is_greeting(prompt: str) -> bool:
    """
    Verifie si un prompt est une simple salutation.
    
    Args:
        prompt: Le texte du prompt utilisateur
        
    Returns:
        bool: True si le prompt est une salutation
    """
    prompt_lower = prompt.lower().strip()
    words = prompt_lower.split()
    
    if len(words) > 8:
        return False
    
    for gp in GREETING_PATTERNS:
        if re.search(gp, prompt_lower):
            return True
    
    return False


# ----------------------------------------------------------------------------
# TEST RAPIDE
# ----------------------------------------------------------------------------

def test_classifier():
    """Teste le classifieur harmonique."""
    print("=" * 60)
    print("TEST : Harmonic Classifier")
    print("=" * 60)
    
    test_prompts = [
        ("What is the capital of France?", "factual"),
        ("Explain the theory of relativity", "reasoning"),
        ("Solve 2x + 5 = 15", "mathematical"),
        ("Write a poem about the ocean", "creative"),
        ("Write a Python function to sort a list", "code"),
        ("Hello, how are you?", "general"),
        ("Bonjour, comment allez-vous ?", "general"),
        ("Calculate 15% of 340", "mathematical"),
        ("Why is the sky blue?", "reasoning"),
        ("Who invented the telephone?", "factual"),
    ]
    
    passed = 0
    for prompt, expected in test_prompts:
        detected = detect_category(prompt)
        confidence = detect_category_with_confidence(prompt)
        status = "OK" if detected == expected else "X"
        if detected == expected:
            passed += 1
        print(f"  {status} [{detected}] (conf: {confidence[1]:.2f}) -> {prompt[:50]}")
    
    print(f"\nResultat : {passed}/{len(test_prompts)} tests passes")
    print("=" * 60)


if __name__ == "__main__":
    test_classifier()
