"""
Bridge — Intègre le moteur mathématique LM Arena dans le HarmonicBrain.
Appelé avant le retrieval KB pour intercepter les questions mathématiques.
"""
import sys, os, re, math

# Ajouter le dossier lm_arena au path
_LM_ARENA_DIR = os.path.join(os.path.dirname(__file__), '..', 'lm_arena')
if _LM_ARENA_DIR not in sys.path:
    sys.path.insert(0, _LM_ARENA_DIR)

# Cache du moteur mathématique (import paresseux)
_MATH_ENGINE = None

def _get_math_engine():
    """Charge le moteur mathématique une seule fois."""
    global _MATH_ENGINE
    if _MATH_ENGINE is None:
        try:
            # Ajouter aussi le projet cerveau_harmonique_v1 au path
            projet_dir = os.path.join(os.path.dirname(__file__), '..', 'projet', 'cerveau_harmonique_v1')
            if projet_dir not in sys.path:
                sys.path.insert(0, projet_dir)
            
            from harmonic_math_engine import HarmonicMathEngine
            _MATH_ENGINE = HarmonicMathEngine()
            print("  🧮 Moteur mathématique LM Arena chargé")
        except ImportError as e:
            print(f"  ⚠️ Moteur mathématique non disponible: {e}")
            _MATH_ENGINE = False
    return _MATH_ENGINE if _MATH_ENGINE is not False else None

# ═══════════════════════════════════════════════════════════════
# MICRO-CALCULATEUR ÉTENDU (fusionné avec patterns LM Arena)
# ═══════════════════════════════════════════════════════════════

def try_math_solve(question: str, lang: str = 'fr') -> str:
    """
    Tente de résoudre une question mathématique.
    Combine le micro-calculateur local + le moteur LM Arena.
    Retourne la réponse ou None si pas une question mathématique.
    """
    # Niveau 1 : Micro-calculateur (ultra-rapide, patterns simples)
    result = _try_simple_calc(question, lang)
    if result:
        return result
    
    # Niveau 2 : Moteur mathématique LM Arena (algèbre, géométrie, trigonométrie, etc.)
    engine = _get_math_engine()
    if engine:
        try:
            # Le moteur LM Arena a besoin d'une analyse préalable
            analysis = _quick_analyze(question)
            if analysis.get('math_score', 0) > 0.3:
                result = engine.solve(question, analysis)
                if result and result.get('confidence', 0) > 0.55:
                    return _format_math_response(result, lang)
        except Exception:
            pass
    
    return None

def _try_simple_calc(q: str, lang: str) -> str:
    """Micro-calculateur local — opérations simples."""
    q = q.lower().strip()
    
    # === CONSTANTES CONNUES (mot entier, pas substring!) ===
    q_words = set(q.split())
    if 'nombre' in q_words and 'or' in q_words or 'golden' in q_words and 'ratio' in q_words:
        return '1.618.'
    if q.startswith('nombre d or') or q == 'nombre dor':
        return '1.618.'
    if 'pi' in q_words and any(w in q_words for w in ['valeur','approxim','egal','nombre','combien']):
        return '3.141592653589793.'
    if q.startswith('pi ') and len(q) < 20:
        return '3.141592653589793.'
    if 'vitesse' in q_words and 'lumiere' in q_words:
        return '300000 km/s.'
    
    # === PHYSIQUE ===
    # F = ma : "force X N masse Y kg"
    m = re.search(r'force.*?(\d+)\s*n.*?masse.*?(\d+)\s*kg', q)
    if m:
        return f"{float(m.group(1)) / float(m.group(2)):.1f} m/s²."
    
    # U = RI : "U.*220V.*R.*440 ohms" ou "U egal X V R egal Y ohms"
    m = re.search(r'(\d+)\s*v.*?(\d+)\s*(ohm|Ω)', q)
    if m:
        return f"{float(m.group(1)) / float(m.group(2)):.1f} A."
    
    # P = UI : "U X V I Y A" ou "puissance U X I Y"
    m = re.search(r'(\d+)\s*v.*?(\d+)\s*a', q)
    if m:
        return f"{float(m.group(1)) * float(m.group(2)):.0f} W."
    
    # E = ½mv² : "energie cinetique masse X kg vitesse Y m/s"
    m = re.search(r'energie.*?masse.*?(\d+).*?vitesse.*?(\d+)', q)
    if m:
        return f"{0.5 * float(m.group(1)) * float(m.group(2))**2:.0f} J."
    
    # Poids = mg : "poids.*masse.*X kg"
    m = re.search(r'poids.*?masse.*?(\d+)', q)
    if m:
        return f"{float(m.group(1)) * 9.81:.1f} N."
    
    # v = fλ : "frequence X Hz celerite Y m/s longueur onde"
    m = re.search(r'frequence.*?(\d+)\s*hz.*?celerite.*?(\d+)\s*m', q)
    if m:
        f, c = float(m.group(1)), float(m.group(2))
        return f"{c/f:.1f} m."
    m = re.search(r'frequence.*?(\d+).*?vitesse.*?(\d+).*?longueur', q)
    if m:
        f, c = float(m.group(1)), float(m.group(2))
        return f"{c/f:.1f} m."
    
    # === ARITHMÉTIQUE ===
    # Addition : X + Y, X plus Y
    m = re.search(r'(\d+)\s*(\+|plus)\s*(\d+)(?!\s*(%|pourcent|fois|×|\*|x|divise|/))', q)
    if m:
        return f"{float(m.group(1)) + float(m.group(3)):.0f}"
    
    # Soustraction : X - Y, X moins Y
    m = re.search(r'(\d+)\s*(-|moins)\s*(\d+)', q)
    if m:
        return f"{float(m.group(1)) - float(m.group(3)):.0f}"
    m = re.search(r'(\d+)\s*(divise\s*par|/)\s*(\d+)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(3))
        return f"{a/b:.1f}" if a % b != 0 else f"{int(a/b)}"
    
    # Multiplication + addition : X fois Y plus Z, X*Y+Z
    m = re.search(r'(\d+)\s*(fois|×|\*|x)\s*(\d+)\s*(plus|\+)\s*(\d+)', q)
    if m:
        a, b, c = float(m.group(1)), float(m.group(3)), float(m.group(5))
        return f"{a * b + c:.0f}"
    
    # Distance : X km/h (ou km h) pendant Y min/h
    m = re.search(r'(\d+)\s*km[/\s]*h.*?(\d+)\s*(minute|min|heure|h)', q)
    if m:
        v, t, unit = float(m.group(1)), float(m.group(2)), m.group(3)
        d = v * t if unit in ('heure', 'h') else v * t / 60
        return f"{d:.0f} km."
    
    # Pourcentage : X% de Y
    for pat in [r'(\d+)\s*%\s*(de|of|sur)\s*(\d+)', r'(\d+)\s*(%|pourcent|pour cent).*?(\d+)']:
        m = re.search(pat, q)
        if m:
            groups = m.groups()
            if '%' in str(groups[1]) or 'pourcent' in str(groups[1]):
                pct, val = float(groups[0]), float(groups[2])
            else:
                pct, val = float(groups[0]), float(groups[2])
            return f"{pct * val / 100:.1f}"
    
    # Réduction : X€/Y%
    m = re.search(r'(\d+)\s*(€|euros?).*?(\d+)\s*(%|pourcent).*?(reduction|remise|solde)', q)
    if m:
        prix, pct = float(m.group(1)), float(m.group(3))
        return f"{prix * (1 - pct/100):.2f} €."
    
    # Multiplication simple : X fois Y
    m = re.search(r'(\d+)\s*(fois|×|\*|x)\s*(\d+)', q)
    if m:
        return f"{float(m.group(1)) * float(m.group(3)):.0f}"
    
    # Puissance : X^Y, X puissance Y
    m = re.search(r'(\d+)\s*(\^|puissance)\s*(\d+)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(3))
        if b <= 10:
            return f"{a ** b:.0f}"
    
    # Racine carrée (FR + EN)
    for pat in [r'racine\s*carree?\s*(de\s*)?(\d+)', r'sqrt\s*(of\s*)?(\d+)', r'square\s*root\s*(of\s*)?(\d+)']:
        m = re.search(pat, q)
        if m:
            val = float(m.group(2))
            s = math.sqrt(val)
            return f"{int(s)}" if s == int(s) else f"{s:.3f}"
    
    # Carré
    m = re.search(r'(\d+)\s*(au carre|carre)', q)
    if m:
        return f"{float(m.group(1))**2:.0f}"
    
    # Secondes dans X : "secondes dans une heure"
    m = re.search(r'secondes?\s*(dans|en|par)\s*(une|un|1)\s*(heure|jour|annee|an|minute)', q)
    if m:
        unit = m.group(3)
        if unit in ('heure',): return "3600 secondes."
        if unit in ('jour',): return "86400 secondes."
        if unit in ('annee', 'an'): return "31536000 secondes."
        if unit in ('minute',): return "60 secondes."
    
    return None

def _quick_analyze(question: str) -> dict:
    """Analyse rapide pour déterminer si c'est une question mathématique."""
    q = question.lower()
    score = 0.0
    
    # Mots-clés mathématiques
    math_keywords = [
        'calcul', 'resoudre', 'equation', 'derivee', 'integrale', 'limite',
        'factorielle', 'produit', 'somme', 'moyenne', 'pourcentage',
        'aire', 'volume', 'perimetre', 'hypotenuse', 'triangle', 'cercle',
        'angle', 'sinus', 'cosinus', 'tangente', 'logarithme', 'exponentielle',
        'racine', 'puissance', 'polynome', 'matrice', 'vecteur',
        'solve', 'compute', 'evaluate', 'derivative', 'integral',
        r'x\^2', r'x\^n', r'\d+x', '=',
    ]
    for kw in math_keywords:
        if kw in q:
            score += 0.15
    
    # Présence de nombres
    numbers = len(re.findall(r'\d+', q))
    if numbers >= 2:
        score += 0.1 * min(numbers, 5)
    
    # Opérateurs
    if re.search(r'[\+\-\*/\^×]', q):
        score += 0.2
    
    return {'math_score': min(score, 1.0), 'domain': 'math'}

def _format_math_response(result: dict, lang: str) -> str:
    """Formate la réponse du moteur mathématique."""
    answer = result.get('answer', result.get('result', ''))
    if not answer:
        formula = result.get('formula', '')
        if formula:
            return f"{formula}."
        return None
    
    answer = str(answer).strip()
    if not answer.endswith('.') and not answer.endswith(')') and not answer.endswith(']'):
        answer += '.'
    return answer
