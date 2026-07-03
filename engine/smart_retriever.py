"""
Smart Retriever — Recherche de faits intelligente
==================================================
Corrige les problèmes de retrieval identifiés :
1. Synonymes (Mona Lisa = Joconde, Moon = Lune)
2. Filtrage des nombres (200 ne matche pas 2001)
3. Meilleur ranking (prioriser le sujet exact)
4. Math étendue (pourcentages, vitesses, équations)
5. Détection de la langue pour le matching

Usage: from smart_retriever import smart_retrieve, smart_math, expand_query
"""

import re
import math as pymath

# ═══════════════════════════════════════════════════════════════════
# 1. DICTIONNAIRE DE SYNONYMES
# ═══════════════════════════════════════════════════════════════════

SYNONYMS = {
    # Art / Culture
    'mona lisa': 'joconde',
    'joconde': 'mona lisa',
    'davinci': 'leonard de vinci',
    'da vinci': 'leonard de vinci',
    'leonardo': 'leonard de vinci',
    'shakespeare': 'shakespeare',
    'william shakespeare': 'shakespeare',
    # Géographie
    'moon': 'lune',
    'earth': 'terre',
    'sun': 'soleil',
    'mars': 'mars',
    'usa': 'etats unis',
    'us': 'etats unis',
    'america': 'etats unis',
    'uk': 'royaume uni',
    'britain': 'royaume uni',
    'great britain': 'royaume uni',
    # Concepts
    'gravity': 'gravite',
    'light': 'lumiere',
    'water': 'eau',
    'fire': 'feu',
    'air': 'air',
    'dna': 'adn',
    'atom': 'atome',
    'cell': 'cellule',
    'brain': 'cerveau',
    'heart': 'coeur',
    'blood': 'sang',
    'energy': 'energie',
    'force': 'force',
    'mass': 'masse',
    'speed': 'vitesse',
    'time': 'temps',
    'space': 'espace',
    'wave': 'onde',
    'particle': 'particule',
    'electron': 'electron',
    'photon': 'photon',
    'proton': 'proton',
    'neutron': 'neutron',
    'neuron': 'neurone',
    'plant': 'plante',
    'animal': 'animal',
    'human': 'humain',
    'life': 'vie',
    'death': 'mort',
    'love': 'amour',
    'happiness': 'bonheur',
    'sadness': 'tristesse',
    'fear': 'peur',
    'anger': 'colere',
    # Verbes
    'painted': 'a peint',
    'painted by': 'peint par',
    'wrote': 'a ecrit',
    'written by': 'ecrit par',
    'discovered': 'a decouvert',
    'invented': 'a invente',
    'created': 'a cree',
    'founded': 'a fonde',
    'composed': 'a compose',
    'built': 'a construit',
    'designed': 'a dessine',
    'is the capital of': 'est la capitale de',
    'is the capital': 'est la capitale',
    'capital of': 'capitale de',
    'largest': 'plus grand',
    'biggest': 'plus grand',
    'highest': 'plus haut',
    'longest': 'plus long',
    'smallest': 'plus petit',
    'fastest': 'plus rapide',
    'oldest': 'plus ancien',
}

def expand_query(question: str) -> list:
    """
    Expand une question en variantes synonymes.
    Retourne une liste de variantes à rechercher.
    """
    q_lower = question.lower().strip()
    variants = [q_lower]
    
    # Appliquer les synonymes
    for syn_en, syn_fr in SYNONYMS.items():
        if syn_en in q_lower and syn_en != syn_fr:
            variant = q_lower.replace(syn_en, syn_fr)
            if variant not in variants:
                variants.append(variant)
    
    # Inversement : FR → EN
    for syn_en, syn_fr in SYNONYMS.items():
        if syn_fr in q_lower and syn_en != syn_fr:
            variant = q_lower.replace(syn_fr, syn_en)
            if variant not in variants:
                variants.append(variant)
    
    return variants


# ═══════════════════════════════════════════════════════════════════
# 2. FILTRAGE DES NOMBRES
# ═══════════════════════════════════════════════════════════════════

def is_number_collision(query_word: str, fact_word: str) -> bool:
    """
    Détecte si un mot-numéro dans la question matche accidentellement
    un nombre différent dans un fait.
    Ex: "200" ne devrait pas matcher "2001"
    """
    # Si les deux sont des nombres
    try:
        q_num = int(query_word)
        f_num = int(fact_word)
        return q_num != f_num  # collision si nombres différents
    except ValueError:
        return False


# ═══════════════════════════════════════════════════════════════════
# 3. SMART RETRIEVE — recherche de faits intelligente
# ═══════════════════════════════════════════════════════════════════

def smart_retrieve(question: str, knowledge_base: list, max_results: int = 5) -> list:
    """
    Recherche intelligente de faits dans la base de connaissance.
    
    Améliorations vs _retrieve_facts :
    1. Expansion par synonymes
    2. Filtrage des collisions de nombres
    3. Scoring multi-critères (sujet, objet, relation, mots-clés)
    4. Boost pour les matchs exacts
    5. Pénalité pour les matchs partiels trompeurs
    """
    q_lower = question.lower().strip()
    
    # Extraire le sujet central (enlever préfixes de question)
    sujet = q_lower
    for prefix in ['what is the ', 'what is a ', 'what is ', 'what are ',
                   'who is ', 'who was ', 'who wrote ', 'who painted ',
                   'who discovered ', 'who invented ', 'who created ',
                   'who founded ', 'who composed ',
                   'when did ', 'when was ', 'when ',
                   'where is ', 'where are ', 'where ',
                   'why is ', 'why does ', 'why do ', 'why ',
                   'how does ', 'how do ', 'how ',
                   'explain ', 'describe ', 'define ',
                   'tell me about ', 'can you help me understand ',
                   'qu est ce que ', "qu'est ce que ",
                   'qui a ecrit ', 'qui a peint ', 'qui a decouvert ',
                   'qui a invente ', 'qui a cree ', 'qui a fonde ',
                   'qui a compose ', 'qui est ', 'qui etait ',
                   'quand ', 'ou ', 'pourquoi ', 'comment ',
                   'explique ', 'definis ', 'parle de ',
                   'quelle est la capitale de ', 'quel est la capitale de ',
                   'capitale de ', 'capital of ',
                   'name three ', 'name ', 'list ',
                   'is ', 'are ', 'the ', 'a ', 'an ']:
        if sujet.startswith(prefix):
            sujet = sujet[len(prefix):].strip()
            break
    sujet = sujet.strip('?.,!;:')
    
    # Mots-clés significatifs (sans stopwords)
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'of', 'in',
                 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'and', 'or',
                 'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du',
                 'est', 'sont', 'dans', 'sur', 'pour', 'par', 'avec',
                 'what', 'who', 'when', 'where', 'why', 'how',
                 'qui', 'quoi', 'ou', 'quand', 'comment', 'pourquoi',
                 'et', 'the', 'it', 'that', 'this', 'its',
                 'has', 'have', 'had', 'do', 'does', 'did'}
    q_words = [w.strip('.,!?;:()[]{}""\'') for w in q_lower.split()]
    q_keywords = [w for w in q_words if len(w) >= 3 and w not in stopwords]
    
    # Expansion par synonymes
    variants = expand_query(question)
    all_sujets = set()
    for v in variants:
        v_clean = v
        for prefix in ['what is the ', 'what is ', 'who ', 'when ', 'where ',
                       'why ', 'how ', 'explain ', 'capital of ',
                       'capitale de ', 'qu est ce que ', 'qui a ']:
            if v_clean.startswith(prefix):
                v_clean = v_clean[len(prefix):].strip()
                break
        v_clean = v_clean.strip('?.,!;:')
        if v_clean:
            all_sujets.add(v_clean)
    
    # Synonymes du sujet
    syn_targets = set()
    for s in all_sujets:
        for syn_key, syn_val in SYNONYMS.items():
            if syn_key in s:
                syn_targets.add(syn_val)
            if syn_val in s:
                syn_targets.add(syn_key)
    
    # Relation keywords (capitale, ecrit, peint, decouvert...)
    rel_keywords = set()
    rel_patterns = ['capitale', 'capital', 'ecrit', 'wrote', 'ecrite',
                    'peint', 'painted', 'decouvert', 'discovered',
                    'invente', 'invented', 'cree', 'created',
                    'fonde', 'founded', 'compose', 'composed',
                    'construit', 'built', 'concu', 'designed',
                    'ecrit par', 'written by', 'peint par',
                    'est la capitale', 'is the capital',
                    'auteur', 'author', 'inventeur', 'inventor',
                    'plus grand', 'largest', 'plus long', 'longest',
                    'plus haut', 'highest']
    for rp in rel_patterns:
        if rp in q_lower:
            rel_keywords.add(rp)
    
    # ═══ SCORING ═══
    scored = []
    
    for s, r, o, sec in knowledge_base:
        s_lower = s.lower().strip()
        o_lower = o.lower()
        r_lower = r.lower()
        score = 0
        
        # 1. MATCH EXACT SUJET (score maximal)
        for sj in all_sujets:
            if s_lower == sj:
                score += 20
                break
            # Sujet du fait contient le sujet de la question comme mot complet
            elif sj in s_lower.split():
                score += 12
                break
        
        # 2. SYNONYMES DU SUJET
        for syn in syn_targets:
            if syn in s_lower or syn in o_lower:
                score += 10
                break
        
        # 3. SUJET DANS L'OBJET (capitale du Japon → objet contient "japon")
        for sj in all_sujets:
            sj_words = [w for w in sj.split() if len(w) >= 3]
            for sw in sj_words:
                if sw in o_lower:
                    score += 6
                    break
        
        # 4. MOTS-CLÉS dans l'objet
        for kw in q_keywords:
            if len(kw) < 3:
                continue
            if kw in o_lower:
                score += 4
            elif kw in s_lower:
                score += 3
            elif kw in r_lower:
                score += 2
        
        # 5. RELATION KEYWORD
        for rk in rel_keywords:
            if rk in r_lower:
                score += 15
                break
            if rk in s_lower:
                score += 8
        
        # 6. FILTRAGE DES COLLISIONS DE NOMBRES
        # Si la question contient un nombre, vérifier qu'il matche exactement
        q_numbers = [w for w in q_words if w.isdigit()]
        if q_numbers:
            for qn in q_numbers:
                # Vérifier que le nombre n'apparaît pas comme préfixe d'un autre nombre
                for fw in (s_lower + ' ' + o_lower).split():
                    if fw.isdigit() and fw != qn:
                        score -= 5  # pénalité
                    elif qn in fw and fw != qn and len(fw) > len(qn):
                        score -= 8  # forte pénalité (200 matche 2001)
        
        # 7. PÉNALITÉ POUR LES FAITS HORS-SUJET
        # Si aucun mot-clé ne matche, pénaliser
        if score == 0:
            continue
        
        # 8. BOOST POUR LES FAITS DE BON SECTEUR
        if any(kw in sec.lower() for kw in q_keywords if len(kw) >= 4):
            score += 2
        
        if score >= 3:
            scored.append((score, (s, r, o, sec)))
    
    # Trier par score décroissant
    scored.sort(key=lambda x: -x[0])
    
    # Dédupliquer par sujet
    results = []
    seen_sujets = set()
    for score, fact in scored:
        if fact[0] not in seen_sujets:
            results.append(fact)
            seen_sujets.add(fact[0])
        if len(results) >= max_results:
            break
    
    return results


# ═══════════════════════════════════════════════════════════════════
# 4. MATH ÉTENDUE
# ═══════════════════════════════════════════════════════════════════

def smart_math(question: str) -> str:
    """
    Résout des problèmes mathématiques variés :
    - Arithmétique de base (+, -, ×, ÷)
    - Pourcentages
    - Vitesse/distance/temps
    - Équations simples (x² = N)
    - Racines carrées
    """
    q = question.lower().strip()
    
    # Pourcentage
    m = re.search(r'(\d+)\s*(?:percent|%|pourcent|pour\s*cent)\s*(?:of|de)\s*(\d+)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        result = a / 100 * b
        if result == int(result):
            return f"{int(a)}% of {int(b)} = {int(result)}"
        return f"{int(a)}% of {int(b)} = {result}"
    
    # Vitesse / distance / temps
    m = re.search(r'(\d+(?:\.\d+)?)\s*km/h.*?(\d+(?:\.\d+)?)\s*(?:hours?|heures?|h)\b', q)
    if m:
        speed, time = float(m.group(1)), float(m.group(2))
        dist = speed * time
        return f"{speed} km/h × {time}h = {dist} km"
    
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:mph|miles?.?per.?hour).*?(\d+(?:\.\d+)?)\s*(?:hours?|h)\b', q)
    if m:
        speed, time = float(m.group(1)), float(m.group(2))
        dist = speed * time
        return f"{speed} mph × {time}h = {dist} miles"
    
    # x² = N
    m = re.search(r'x\s*(?:\^|squared?|au\s*carr)[ée]?\s*(?:=|equals?|est)\s*(\d+)', q)
    if m:
        n = int(m.group(1))
        root = pymath.sqrt(n)
        if root == int(root):
            return f"x² = {n}, so x = ±{int(root)}"
        return f"x² = {n}, so x = ±{root:.4f}"
    
    # Racine carrée
    m = re.search(r'(?:square root of|sqrt\s*(?:of\s*)?|racine carr[eé]e?\s*(?:de\s+|d\')?\s*)(\d+)', q)
    if m:
        n = float(m.group(1))
        root = pymath.sqrt(n)
        if root == int(root):
            return f"√{int(n)} = {int(root)}"
        return f"√{int(n)} = {root:.4f}"
    
    # "divisé par"
    m = re.search(r'(\d+)\s*divis[eé]\s*par\s*(\d+)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if b != 0:
            if a % b == 0: return f"{int(a)} ÷ {int(b)} = {int(a/b)}"
            return f"{int(a)} / {int(b)} = {a/b:.2f}"
    
    # "fois" / multiplication
    m = re.search(r'(\d+)\s*fois\s*(\d+)', q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f"{a} × {b} = {a * b}"
    
    m = re.search(r'(\d+)\s*times\s*(\d+)', q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f"{a} × {b} = {a * b}"
    
    # Division
    m = re.search(r'(\d+)\s*/\s*(\d+)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if b != 0:
            if a % b == 0: return f"{int(a)} / {int(b)} = {int(a/b)}"
            return f"{int(a)} / {int(b)} = {a/b:.2f}"
    
    # Addition
    m = re.search(r'(\d+)\s*\+\s*(\d+)', q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f"{a} + {b} = {a + b}"
    
    # Multiplication symboles
    m = re.search(r'(\d+)\s*[×x\*X]\s*(\d+)', q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f"{a} × {b} = {a * b}"
    
    # Soustraction
    m = re.search(r'(\d+)\s*-\s*(\d+)', q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f"{a} - {b} = {a - b}"
    
    # "What is N" (juste un nombre)
    m = re.search(r'what is (\d+(?:\.\d+)?)\s*$', q)
    if m:
        return f"{m.group(1)}"
    
    return None
