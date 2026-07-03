"""
Domain Detector & Conversation Handler
=======================================
Detecte le type de question et route vers le bon traitement.
Ajoute la detection hors-domaine, conversation, calcul, et langue.

Usage: from domain_detector import detect_question_type, handle_greeting, is_math
"""

import re
import os

# ─── CONVERSATION / SALUTATIONS ───────────────────────────────

_GREETING_PATTERNS = [
    r'^(bonjour|salut|coucou|hello|hi|hey|yo)\b',
    r'^(bonsoir|good morning|good evening|good afternoon)\b',
    r'\b(comment ca va|comment vas-tu|comment allez-vous|ca va|ca roule)\b',
    r'\b(how are you|how\'s it going|what\'s up)\b',
    r'^(merci|thanks|thank you)\b',
    r'^(au revoir|bye|a plus|a bientot|goodbye|see you)\b',
    r'^(bien et toi|bien et vous|good and you)\b',
    r'^(de rien|je t en prie|you\'re welcome)\b',
    r'^(salut a toi|salutations|greetings)\b',
]

_GREETING_RESPONSES_FR = [
    "Bonjour. Je suis KA, une IA harmonique. Mon domaine d'expertise couvre les sciences, les mathématiques et la philosophie. Posez-moi une question sur ces sujets !",
    "Salut. KA à votre service. Je peux répondre à vos questions en physique, mathématiques, biologie, et bien d'autres domaines scientifiques. Que voulez-vous savoir ?",
    "Bonjour. Je suis spécialisé en sciences et raisonnement harmonique. N'hésitez pas à me poser une question précise.",
]

_GREETING_RESPONSES_EN = [
    "Hello. I'm KA, a harmonic AI. My expertise covers sciences, mathematics, and philosophy. Ask me a question on these topics!",
    "Hi there. KA at your service. I can answer questions on physics, mathematics, biology, and philosophy. What would you like to know?",
    "Greetings. I specialize in scientific reasoning and harmonic analysis. Feel free to ask me a specific question.",
]

_MERCY_RESPONSES_FR = [
    "De rien. N'hésitez pas si vous avez une autre question scientifique.",
    "Je vous en prie. À votre service pour toute question de science ou de raisonnement.",
    "Avec plaisir. Que puis-je vous expliquer d'autre ?",
]

_BYE_RESPONSES_FR = [
    "Au revoir. Bonne continuation dans votre exploration de la connaissance.",
    "À bientôt. Revenez avec vos questions scientifiques.",
    "Au revoir. L'univers est ondulatoire — gardez cela en tête !",
]

# ─── MATH / CALCUL ────────────────────────────────────────────

_MATH_PATTERNS = [
    # Français
    r'\b(\d+)\s*\+\s*(\d+)\b',              r'\b(\d+)\s*-\s*(\d+)\b',
    r'\b(\d+)\s*[×x\*X]\s*(\d+)\b',         r'\b(\d+)\s*/\s*(\d+)\b',
    r'\b(\d+)\s*fois\s*(\d+)\b',             r'\b(\d+)\s*multipli[eé] par\s*(\d+)\b',
    r'\b(\d+)\s*divis[eé] par\s*(\d+)\b',    r'\bcombien font\b',
    r'\bcombien fait\b',
    r'\bcalcule\b',                           r'\bcalcul de\b',
    r'\bracine carr?ée de\b',                 r'\bracine de\b',
    r'\bpuissance\b',                         r'\bau carr?é\b',
    r'\b(?:dérivée|derivee|integrale|intégrale)\b',
    r'\béquation\b',                          r'\brésoudre\b',
    r'x\s*\^?\s*2\s*=',                       r'\bsquare root of\b',
    r'\bsqrt\b',                              r'\bwhat is\s+\d+\s*[\+\-\×\*/]',
    r'\b\d+\s*percent\s*(?:of)?\b',           r'\b\d+\s*%\s*(?:of)?\b',
    r'\b\d+\s*km/h\b',                        r'\bmph\b',
    r'\b\d+\s*per\s*cent\b',                  r'\bfois\s*\d+\b',
    r'\b\d+\s*fois\b',                        r'\bdivisé par\b',
    r'\bdivis[eé] par\b',                     r'\b\d+\s*divis\b',
    r'\bspeed\b',                             r'\bvelocity\b',
    r'\b\d+\s*times\b',                       r'\bsquared\b',
    r'\b\d+\s*squared\b',                     r'\bcubed\b',
    r'\b\d+\s*cubed\b',                       r'\bmultiplied by\b',
    r'\b\d+\s*multipli[eé] par\b',
    r'\bfois\s*\d+\b',                        r'\b\d+\s*fois\b',
    r'\bdivisé par\b',                        r'\bmultiplié par\b',
    # Anglais
    r'\bwhat is\s+\d+\s*[\+\-\×\*/]\s*\d+\b',
    r'\bcalculate\b',                         r'\bcompute\b',
    r'\bwhat does\s+\d+\s*[\+\-\×\*/]\s*\d+\s+equal\b',
    r'\bderivative\b',                        r'\bintegral\b',
    r'\bsquare root\b',                       r'\bpower of\b',
    r'\b\d+\s*times\s*\d+\b',                r'\btimes\s*\d+\b',
]

# ─── DOMAINES ──────────────────────────────────────────────────

_DOMAIN_KEYWORDS = {
    'physique': ['physique', 'lumiere', 'electron', 'photon', 'atome', 'onde',
                 'gravite', 'relativite', 'einstein', 'newton', 'energie',
                 'electromagnetisme', 'quantique', 'particule', 'noyau',
                 'force', 'masse', 'acceleration', 'thermodynamique',
                 'mecanique', 'optique', 'resonance', 'frequence',
                 'physics', 'light', 'electron', 'photon', 'atom', 'wave',
                 'gravity', 'relativity', 'einstein', 'energy', 'quantum',
                 'electromagnetic', 'particle', 'nucleus', 'force'],
    'mathematiques': ['math', 'nombre', 'equation', 'geometrie', 'algebre',
                      'calcul', 'fonction', 'derivee', 'integrale', 'pi',
                      'phi', 'nombre dor', 'fibonacci', 'trigonometrie',
                      'statistique', 'probabilite', 'vecteur', 'matrice',
                      'mathematics', 'number', 'equation', 'geometry',
                      'algebra', 'calculus', 'function', 'trigonometry',
                      'probability', 'vector', 'matrix', 'fibonacci'],
    'biologie': ['biologie', 'cellule', 'adn', 'dna', 'proteine', 'enzyme',
                 'coeur', 'cardiaque', 'cerveau', 'neurone', 'photosynthese',
                 'respiration', 'mitose', 'meiose', 'evolution', 'darwin',
                 'espece', 'organe', 'tissu', 'sang', 'plante', 'animal',
                 'biology', 'cell', 'dna', 'protein', 'enzyme', 'heart',
                 'cardiac', 'brain', 'neuron', 'photosynthesis',
                 'respiration', 'mitosis', 'evolution', 'species'],
    'philosophie': ['philosophie', 'conscience', 'pensee', 'ame', 'esprit',
                    'ethique', 'morale', 'verite', 'realite', 'existence',
                    'dieu', 'metaphysique', 'logique', 'raison',
                    'philosophy', 'consciousness', 'mind', 'soul', 'ethics',
                    'truth', 'reality', 'existence', 'god', 'metaphysics'],
    'culture': ['musique', 'art', 'peinture', 'litterature', 'poesie',
                'histoire', 'geographie', 'capitale', 'pays', 'continent',
                'langue', 'francais', 'anglais', 'culture', 'tradition',
                'religion', 'spiritualite', 'meditation',
                'music', 'art', 'painting', 'literature', 'poetry',
                'history', 'geography', 'capital', 'country', 'continent',
                'language', 'french', 'english', 'culture', 'religion'],
}

# Questions hors-domaine typiques
_OUT_OF_DOMAIN_PATTERNS = [
    r'\b(?:meteo|météo|temperature|temps qu.il fait|pleut|neige|il fait)\b',
    r'\b(?:recette|cuisine|cook|cooking)\b',
    r'\b(?:code|debug|programme|python|javascript|programming|function)\b',
    r'\b(?:actualite|news|breaking|derniere|récent)\b',
    r'\b(?:blague|joke|humour|rigolo|funny)\b',
]

_OUT_OF_DOMAIN_RESPONSES = {
    'meteo': "Je ne peux pas consulter la météo. Mon expertise porte sur les sciences fondamentales et le raisonnement. Pour la météo, consultez un service spécialisé.",
    'cuisine': "Je ne connais pas de recettes. Mon domaine couvre la physique, les mathématiques, la biologie et la philosophie.",
    'code': "Je ne suis pas un assistant de programmation. Mon architecture est ondulatoire, pas neuronale. Je peux vous expliquer les principes scientifiques derrière l'informatique.",
    'actualite': "Je ne suis pas connecté à l'actualité. Je traite de connaissances fondamentales, pas d'événements récents.",
    'blague': "Je ne raconte pas de blagues, mais je peux vous parler des principes physiques de l'humour — ou vous écrire un haïku !",
}

def detect_language(text: str) -> str:
    """Détecte la langue d'une question (fr, en, ou autre)."""
    text_lower = text.lower().strip()
    en_markers = ['what', 'how', 'why', 'who', 'when', 'where', 'which',
                  'the', 'is', 'are', 'does', 'do', 'can', 'could',
                  'explain', 'describe', 'define', 'calculate',
                  'tell me', 'show me', 'give me',
                  'hello', 'hi', 'hey', 'thanks', 'please', 'would', 'its']
    fr_markers = ['quoi', 'comment', 'pourquoi', 'qui', 'quand', 'où', 'quel',
                  'quelle', 'quels', 'quelles', 'que', 'est-ce',
                  'explique', 'décris', 'définis', 'calcule',
                  'dis-moi', 'montre-moi', 'donne-moi',
                  'bonjour', 'salut', 'merci', 'svp', 'sil vous plait',
                  'bonsoir', 'coucou', 'je', 'tu', 'vous', 'nous']
    
    en_score = sum(1 for m in en_markers if m in text_lower)
    fr_score = sum(1 for m in fr_markers if m in text_lower)
    
    if en_score > fr_score:
        return 'en'
    if fr_score > en_score:
        return 'fr'
    # Default: check common English words
    common_en = ['the', 'is', 'of', 'and', 'what', 'who', 'when', 'where']
    common_fr = ['le', 'la', 'les', 'des', 'une', 'est', 'dans', 'pour']
    en_s = sum(1 for w in common_en if w in text_lower.split())
    fr_s = sum(1 for w in common_fr if w in text_lower.split())
    return 'en' if en_s >= fr_s else 'fr'

def detect_question_type(question: str) -> dict:
    """
    Détecte le type de question.
    Retourne un dict avec les clés: is_greeting, is_math, is_out_of_domain,
    is_in_domain, out_category, language, is_identity.
    """
    result = {
        'is_greeting': False,
        'is_math': False,
        'is_out_of_domain': False,
        'is_in_domain': False,
        'out_category': None,
        'language': 'fr',
        'is_identity': False,
        'is_bye': False,
        'is_mercy': False,
    }
    
    q_lower = question.lower().strip()
    result['language'] = detect_language(question)
    
    # Identité (qui es-tu, qu'est-ce que tu es)
    identity_patterns = [
        r'\b(?:qui es[- ]?tu|qui es[- ]?vous|tu es qui|vous etes qui)\b',
        r'\b(?:qu[ei] est[- ]?ce que tu es|ton nom|ton identite)\b',
        r'\b(?:comment tu t[ \']appelles|comment vous appelez[- ]?vous)\b',
        r'\b(?:what are you|who are you|what is your name)\b',
        r'\b(?:es[- ]?tu une ia|es[- ]?tu un robot)\b',
        r'\b(?:tu es quoi|vous etes quoi)\b',
    ]
    for p in identity_patterns:
        if re.search(p, q_lower):
            result['is_identity'] = True
            return result
    
    # Salutations
    for p in _GREETING_PATTERNS:
        if re.search(p, q_lower):
            result['is_greeting'] = True
            if any(w in q_lower for w in ['merci', 'thanks', 'thank']):
                result['is_mercy'] = True
            if any(w in q_lower for w in ['au revoir', 'bye', 'a plus', 'goodbye', 'salut']):
                result['is_bye'] = True
            return result
    
    # Math
    for p in _MATH_PATTERNS:
        if re.search(p, q_lower):
            result['is_math'] = True
            return result
    
    # Hors-domaine
    for key, pattern in [('meteo', r'meteo|météo|temperature|pleut|neige'),
                         ('cuisine', r'recette|cuisine|cook|cooking'),
                         ('code', r'\bcode\b|\bdebug\b|python|javascript|programming'),
                         ('actualite', r'actualite|news|breaking|dernière|récent'),
                         ('blague', r'blague|joke|humour|rigolo|funny')]:
        if re.search(pattern, q_lower):
            result['is_out_of_domain'] = True
            result['out_category'] = key
            return result
    
    # Dans le domaine
    q_words = set(q_lower.split())
    domain_score = 0
    for domain_keywords in _DOMAIN_KEYWORDS.values():
        for kw in domain_keywords:
            if kw in q_lower:
                domain_score += 1
    if domain_score > 0:
        result['is_in_domain'] = True
    
    return result

def handle_greeting(is_mercy: bool = False, is_bye: bool = False, lang: str = 'fr') -> str:
    """Retourne une réponse adaptée à la salutation."""
    import random
    if is_mercy:
        if lang == 'en':
            return random.choice(["You're welcome. Feel free to ask another science question.", "You're welcome. Ask me anything about science or geography!"])
        pool = _MERCY_RESPONSES_FR
        return random.choice(pool)
    if is_bye:
        if lang == 'en':
            return random.choice(["Goodbye. Come back with your science questions!", "See you later. Keep exploring!"])
        pool = _BYE_RESPONSES_FR
        return random.choice(pool)
    if lang == 'en':
        try:
            from en_templates import GREETING_EN
            return random.choice(GREETING_EN)
        except ImportError:
            return random.choice(_GREETING_RESPONSES_EN)
    pool = _GREETING_RESPONSES_FR if lang == 'fr' else _GREETING_RESPONSES_EN
    return random.choice(pool)

def handle_identity(lang: str = 'fr') -> str:
    """Réponse à une question d'identité."""
    if lang == 'en':
        try:
            from en_templates import IDENTITY_EN
            return IDENTITY_EN
        except ImportError:
            pass
    return (
        "Je suis KA (Knowledge Amplifier), une intelligence artificielle harmonique. "
        "Contrairement aux LLMs comme GPT-4, je n'utilise ni réseau de neurones, "
        "ni GPU, ni backpropagation. Mon architecture est fondée sur le principe "
        "ondulatoire : toute connaissance est une onde, tout raisonnement est une "
        "interférence. Je fonctionne avec 0 paramètre entraîné, 0 hallucination, "
        "et un déterminisme total (même question → même réponse). "
        "Mon domaine d'expertise couvre les sciences fondamentales, "
        "les mathématiques, la biologie et la philosophie."
    )

def handle_out_of_domain(category: str, lang: str = 'fr') -> str:
    """Réponse polie pour question hors-domaine."""
    if lang == 'en':
        try:
            from en_templates import OUT_OF_DOMAIN_EN, DEFAULT_OUT_EN
            return OUT_OF_DOMAIN_EN.get(category, DEFAULT_OUT_EN)
        except ImportError:
            return DEFAULT_OUT_EN
    default = (
        "Je ne traite pas ce type de question. Mon expertise couvre la physique, "
        "les mathématiques, la biologie, la philosophie et les sciences fondamentales. "
        "Posez-moi une question sur l'un de ces sujets !"
    )
    return _OUT_OF_DOMAIN_RESPONSES.get(category, default)

def solve_math(question: str) -> str:
    """Résout une question mathématique simple."""
    import re, math as pymath
    
    # Équation x^2 = N ou "What is the square root of N"
    m = re.search(r'(?:square root of|sqrt\s*(?:of\s*)?|racine carr[eé]e?\s+(?:de\s+|d\')?\s*)(\d+)', question)
    if m:
        a = float(m.group(1))
        sa = pymath.sqrt(a)
        if sa == int(sa): return f"√{int(a)} = {int(sa)}"
        return f"√{int(a)} = {sa:.4f}"
    
    m = re.search(r'x\s*\^?\s*2\s*=\s*(\d+)', question)
    if m:
        a = int(m.group(1))
        sa = pymath.sqrt(a)
        if sa == int(sa): return f"x² = {a}, donc x = ±{int(sa)}"
        return f"x² = {a}, x = ±{sa:.4f}"
    
    # "divisé par"
    m = re.search(r'(\d+)\s*divis[eé]\s*par\s*(\d+)', question)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if b != 0:
            if a % b == 0: return f"{int(a)} ÷ {int(b)} = {int(a/b)}"
            return f"{int(a)} / {int(b)} = {a/b:.2f}"
        return "Division par zéro impossible."
    
    # "fois"
    m = re.search(r'(\d+)\s*fois\s*(\d+)', question)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f"{a} × {b} = {a * b}"
    
    # Addition
    m = re.search(r'(\d+)\s*\+\s*(\d+)', question)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f"{a} + {b} = {a + b}"
    
    # Multiplication symboles
    m = re.search(r'(\d+)\s*[×x\*X]\s*(\d+)', question)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f"{a} × {b} = {a * b}"
    
    # Soustraction
    m = re.search(r'(\d+)\s*-\s*(\d+)', question)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f"{a} - {b} = {a - b}"
    
    # Division
    m = re.search(r'(\d+)\s*/\s*(\d+)', question)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if b != 0:
            if a % b == 0: return f"{int(a)} / {int(b)} = {int(a/b)}"
            return f"{int(a)} / {int(b)} = {a/b:.2f}"
        return "Division par zéro impossible."
    
    # Au carré / au cube
    m = re.search(r'(\d+)\s+au\s+(carr[eé]|cube)', question)
    if m:
        a = int(m.group(1))
        exp = 2 if 'carr' in m.group(2) else 3
        return f"{a}^{exp} = {a**exp}"
    
    m = re.search(r'(\d+)\s*²', question)
    if m: return f"{m.group(1)}² = {int(m.group(1))**2}"
    
    # Racine carrée
    m = re.search(r'racine\s+carr[eé]e?\s+(?:de\s+|d\')?\s*(\d+)', question)
    if m:
        a = float(m.group(1))
        return f"√{m.group(1)} = {pymath.sqrt(a):.4f}"
    
    return None  # Pas un calcul simple, laisser le pipeline normal
