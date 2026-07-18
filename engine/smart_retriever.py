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
    # ── CODE / TECH ──
    # Langages & runtimes
    'js': 'javascript',
    'ts': 'typescript',
    'py': 'python',
    'golang': 'go',
    'rustlang': 'rust',
    'cpp': 'c++',
    'es6': 'javascript',
    'ecmascript': 'javascript',
    'v8': 'javascript engine',
    # Frameworks
    'reactjs': 'react',
    'nodejs': 'node.js',
    'nextjs': 'next.js',
    'next': 'next.js',
    'nuxtjs': 'nuxt',
    'vuejs': 'vue',
    'sveltekit': 'svelte',
    # Databases
    'postgres': 'postgresql',
    'mongo': 'mongodb',
    'mariadb': 'mysql',
    'db': 'database',
    'dbms': 'database',
    'rdbms': 'relational database',
    # DevOps
    'k8s': 'kubernetes',
    'k3s': 'kubernetes',
    'cicd': 'ci/cd',
    'dev ops': 'devops',
    # Concepts
    'ml': 'machine learning',
    'dl': 'deep learning',
    'nlp': 'natural language processing',
    'cv': 'computer vision',
    'rl': 'reinforcement learning',
    'oop': 'programmation orientee objet',
    'orm': 'object relational mapping',
    'crud': 'create read update delete',
    'mvc': 'model view controller',
    'spa': 'single page application',
    'ssr': 'server side rendering',
    'ssg': 'static site generation',
    'cdn': 'content delivery network',
    'dom': 'document object model',
    'pwa': 'progressive web app',
    'wasm': 'webassembly',
    'jwt': 'json web token',
    'grpc': 'google remote procedure call',
    'ioc': 'inversion of control',
    'di': 'dependency injection',
    'tdd': 'test driven development',
    'ci': 'continuous integration',
    'cd': 'continuous deployment',
    'vm': 'virtual machine',
    'iaas': 'infrastructure as a service',
    'paas': 'platform as a service',
    'saas': 'software as a service',
    'faas': 'function as a service',
    # Infrastructure
    'ec2': 'aws',
    's3': 'aws',
    'lambda': 'aws lambda',
    'cloudfront': 'aws',
    'rds': 'relational database service',
    'eks': 'kubernetes',
    'gke': 'kubernetes',
    'aks': 'kubernetes',
    # Méthodes
    'agile': 'methodologie agile',
    'scrum': 'methodologie agile',
    'kanban': 'methodologie agile',
    'waterfall': 'cycle en cascade',
    # Common code terms EN→FR
    'bug': 'bogue',
    'debug': 'deboguer',
    'compiler': 'compiler',
    'deploy': 'deploiement',
    'framework': 'cadriciel',
    'library': 'bibliotheque',
    'array': 'tableau',
    'string': 'chaine de caracteres',
    'loop': 'boucle',
    'function': 'fonction',
    'variable': 'variable',
    'class': 'classe',
    'object': 'objet',
    'inheritance': 'heritage',
    'polymorphism': 'polymorphisme',
    'interface': 'interface',
    'abstract': 'abstrait',
    'async': 'asynchrone',
    'await': 'attendre',
    'promise': 'promesse',
    'callback': 'rappel',
    'thread': 'fil execution',
    'process': 'processus',
    'memory': 'memoire',
    'cache': 'cache',
    'query': 'requete',
    'index': 'index',
    'token': 'jeton',
    'encryption': 'chiffrement',
    'hash': 'hachage',
    'protocol': 'protocole',
    'request': 'requete',
    'response': 'reponse',
    'header': 'entete',
    'body': 'corps',
    'endpoint': 'point acces',
    'middleware': 'intergiciel',
    'plugin': 'greffon',
    'module': 'module',
    'package': 'paquet',
    'dependency': 'dependance',
    'frontend': 'interface utilisateur',
    'backend': 'serveur',
    'fullstack': 'developpement complet',
    'devops': 'developpement operations',
    'api': 'interface programmation',
    'sdk': 'kit developpement',
    'cli': 'ligne de commande',
    'gui': 'interface graphique',
    'ui': 'interface utilisateur',
    'ux': 'experience utilisateur',
    # Programmation concepts EN↔FR
    'programmation orientee objet': 'oop',
    'poo': 'oop',
    'object oriented programming': 'oop',
    'microservice': 'microservices',
    'micro service': 'microservices',
    'api rest': 'rest',
    'rest api': 'rest',
    'restful': 'rest',
    'ci cd': 'ci/cd',
    'continuous integration': 'ci/cd',
    'integration continue': 'ci/cd',
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
    
    # Racine carrée — sqrt(N) avec parenthèses
    m = re.search(r'sqrt\s*\(\s*(\d+(?:\.\d+)?)\s*\)', q)
    if m:
        n = float(m.group(1))
        root = pymath.sqrt(n)
        if root == int(root):
            return f"√{int(n)} = {int(root)}"
        return f"√{int(n)} = {root:.4f}"

    # Racine carrée — square root of N, racine carrée de N
    m = re.search(r'(?:square root of|sqrt\s*(?:of\s*)?|racine carr[eé]e?\s*(?:de\s+|d\')?\s*)(\d+)', q)
    if m:
        n = float(m.group(1))
        root = pymath.sqrt(n)
        if root == int(root):
            return f"√{int(n)} = {int(root)}"
        return f"√{int(n)} = {root:.4f}"

    # Équation simple : résoudre x + a = b
    m = re.search(r'r[éeé]soudre\s+x\s*\+\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        x = b - a
        return f"x + {int(a)} = {int(b)} → x = {int(x)}" if x == int(x) else f"x + {a} = {b} → x = {x:.4f}"

    # Équation simple : résoudre x - a = b
    m = re.search(r'r[éeé]soudre\s+x\s*-\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        x = b + a
        return f"x - {int(a)} = {int(b)} → x = {int(x)}" if x == int(x) else f"x - {a} = {b} → x = {x:.4f}"

    # Équation simple : résoudre a*x = b (ou ax = b)
    m = re.search(r'r[éeé]soudre\s+(\d+(?:\.\d+)?)\s*[\*x×]?\s*x\s*=\s*(\d+(?:\.\d+)?)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if a != 0:
            x = b / a
            return f"{int(a)}x = {int(b)} → x = {int(x)}" if x == int(x) else f"{a}x = {b} → x = {x:.4f}"

    # Équation simple : résoudre a*x + b = c (ou ax + b = c)
    m = re.search(r'r[éeé]soudre\s+(\d+(?:\.\d+)?)\s*[\*x×]?\s*x\s*\+\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)', q)
    if m:
        a, b, c = float(m.group(1)), float(m.group(2)), float(m.group(3))
        if a != 0:
            x = (c - b) / a
            return f"{int(a)}x + {int(b)} = {int(c)} → x = {int(x)}" if x == int(x) else f"{a}x + {b} = {c} → x = {x:.4f}"

    # Équation simple : résoudre a*x - b = c (ou ax - b = c) — le pattern manquant !
    m = re.search(r'r[éeé]soudre\s+(\d+(?:\.\d+)?)\s*[\*x×]?\s*x\s*-\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)', q)
    if m:
        a, b, c = float(m.group(1)), float(m.group(2)), float(m.group(3))
        if a != 0:
            x = (c + b) / a
            return f"{int(a)}x - {int(b)} = {int(c)} → x = {int(x)}" if x == int(x) else f"{a}x - {b} = {c} → x = {x:.4f}"

    # Équation simple : résoudre a*x - b = 0 (cas spécial fréquent)
    m = re.search(r'r[éeé]soudre\s+(\d+(?:\.\d+)?)\s*[\*x×]?\s*x\s*-\s*(\d+(?:\.\d+)?)\s*=\s*0', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if a != 0:
            x = b / a
            return f"{int(a)}x - {int(b)} = 0 → x = {int(x)}" if x == int(x) else f"{a}x - {b} = 0 → x = {x:.4f}"

    # 🆕 PUISSANCES — 2^8, 10^6, 2^10
    m = re.search(r'(\d+(?:\.\d+)?)\s*\^\s*(\d+(?:\.\d+)?)', q)
    if m:
        base, exp = float(m.group(1)), float(m.group(2))
        result = base ** exp
        if result == int(result) and result < 1e15:
            return f"{int(base)}^{int(exp)} = {int(result)}"
        return f"{base}^{exp} = {result:.4f}"

    # 🆕 TRIGONOMÉTRIE — sin, cos, tan
    for fn_name, fn in [('sin', pymath.sin), ('cos', pymath.cos), ('tan', pymath.tan)]:
        m = re.search(rf'{fn_name}\s*\(\s*(\d+(?:\.\d+)?)\s*(?:°|deg|degr[ée]s?)?\s*\)', q)
        if m:
            val = float(m.group(1))
            # Si pas de ° explicite mais valeur ≤ 360, supposer degrés
            is_deg = '°' in q or 'deg' in q or 'degr' in q or val > 2 * pymath.pi
            if is_deg and val <= 360:
                val = pymath.radians(val)
            result = fn(val)
            result = round(result, 4)
            if abs(result) < 0.0001: result = 0.0
            if abs(result - round(result)) < 0.0001: result = round(result)
            return f"{fn_name}({m.group(1)}°) = {result}"

    # 🆕 DÉRIVÉES — dérivée de x^N, sin, cos, exp, ln
    m = re.search(r'd[éeé]riv[ée]e?\s*(?:de\s+)?(\d*\s*x(?:\s*\^\s*\d+)?|sin\s*\(\s*x\s*\)|cos\s*\(\s*x\s*\)|e\^x|ln\s*\(\s*x\s*\)|tan\s*\(\s*x\s*\))', q)
    if m:
        expr = m.group(1).replace(' ', '')
        if expr in ('x', '1x'): return "dérivée de x = 1"
        m2 = re.match(r'(\d*)x\^(\d+)', expr)
        if m2:
            coeff = int(m2.group(1)) if m2.group(1) else 1
            power = int(m2.group(2))
            return f"dérivée de {coeff}x^{power} = {coeff*power}x^{power-1}"
        if expr == 'sin(x)': return "dérivée de sin(x) = cos(x)"
        if expr == 'cos(x)': return "dérivée de cos(x) = -sin(x)"
        if expr == 'e^x': return "dérivée de e^x = e^x"
        if expr == 'ln(x)': return "dérivée de ln(x) = 1/x"
        if expr == 'tan(x)': return "dérivée de tan(x) = sec²(x)"

    # 🆕 INTÉGRALES — intégrale de X dx
    m = re.search(r'int[éeé]grale?\s*(?:de\s+)?(.+?)\s*dx\s*$', q)
    if m:
        expr = m.group(1).strip().replace(' ', '')
        if expr in ('1', '1dx', 'dx'): return "∫ 1 dx = x + C"
        m2 = re.match(r'(\d*)x\^?(\d*)', expr)
        if m2:
            coeff = int(m2.group(1)) if m2.group(1) else 1
            power = int(m2.group(2)) if m2.group(2) else 1
            new_coeff = coeff // (power + 1) if coeff % (power + 1) == 0 else f"{coeff}/{power+1}"
            return f"∫ {coeff}x^{power} dx = {new_coeff}x^{power+1} + C" if power > 0 else f"∫ {coeff} dx = {coeff}x + C"
        if 'sin(x)' in expr or 'sinx' in expr: return "∫ sin(x) dx = -cos(x) + C"
        if 'cos(x)' in expr or 'cosx' in expr: return "∫ cos(x) dx = sin(x) + C"
        if 'e^x' in expr: return "∫ e^x dx = e^x + C"
        if '1/x' in expr: return "∫ 1/x dx = ln|x| + C"

    # 🆕 LIMITES — limite de X quand x → Y
    m = re.search(r'limite\s*(?:de\s+)?(.+?)\s*(?:quand\s+)?x\s*(?:tend\s+vers|->|→)\s*(.+?)(?:$|\s*$)', q)
    if m:
        expr, target = m.group(1).strip(), m.group(2).strip()
        if '1/x' in expr and ('infini' in target or '∞' in target or 'infinity' in target):
            return "limite de 1/x quand x→∞ = 0"
        if 'sin(x)/x' in expr and '0' in target:
            return "limite de sin(x)/x quand x→0 = 1"
        if 'x^2' in expr and '0' in target:
            return "limite de x² quand x→0 = 0"

    # 🆕 GÉOMÉTRIE — versions ultra-simples : mot-clé + nombre
    # "périmètre d un carré de côté 5", "aire du cercle de rayon 2", etc.

    m = re.search(r'p[éeé]rim[èe]tre.*?(\d+(?:\.\d+)?)', q)
    if m:
        n = float(m.group(1))
        if 'carré' in q or 'carre' in q: return f"périmètre du carré = {int(4*n)}"
        if 'cercle' in q: return f"périmètre du cercle = {2*pymath.pi*n:.2f}"
        if 'rectangle' in q: return f"périmètre = {int(2*n)} (côté donné)"

    m = re.search(r'aire.*?(\d+(?:\.\d+)?)', q)
    if m:
        n = float(m.group(1))
        if 'carré' in q or 'carre' in q: return f"aire du carré = {int(n*n)}"
        if 'cercle' in q: return f"aire du cercle = {pymath.pi*n*n:.2f}"
        if 'rectangle' in q:
            m2 = re.search(r'(\d+(?:\.\d+)?)\s*(?:par|x|×|et)\s*(\d+(?:\.\d+)?)', q)
            if m2:
                a, b = float(m2.group(1)), float(m2.group(2))
                return f"aire du rectangle = {int(a*b)}"

    m = re.search(r'volume.*?(\d+(?:\.\d+)?)', q)
    if m:
        n = float(m.group(1))
        if 'cube' in q: return f"volume du cube = {int(n**3)}"
        if 'sphère' in q or 'sphere' in q: return f"volume de la sphère = {4/3*pymath.pi*n**3:.3f}"

    m = re.search(r'surface.*?(\d+(?:\.\d+)?)', q)
    if m:
        n = float(m.group(1))
        if 'sphère' in q or 'sphere' in q: return f"surface de la sphère = {4*pymath.pi*n*n:.3f}"

    m = re.search(r'hypot[ée]nuse.*?(\d+(?:\.\d+)?).*?(\d+(?:\.\d+)?)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        h = pymath.sqrt(a*a + b*b)
        return f"hypoténuse = {int(h)}" if h == int(h) else f"hypoténuse = {h:.2f}"

    m = re.search(r'(?:pythagore|pythagoras).*?(\d+(?:\.\d+)?).*?(\d+(?:\.\d+)?)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        h = pymath.sqrt(a*a + b*b)
        return f"Pythagore: hypoténuse = {int(h)}" if h == int(h) else f"Pythagore: hypoténuse = {h:.2f}"

    m = re.search(r'diagonale.*?(\d+(?:\.\d+)?)', q)
    if m:
        n = float(m.group(1))
        d = n * pymath.sqrt(2) if 'carré' in q or 'carre' in q else n
        return f"diagonale = {d:.3f}"

    m = re.search(r'distance.*?(\d+(?:\.\d+)?).*?(\d+(?:\.\d+)?).*?(\d+(?:\.\d+)?).*?(\d+(?:\.\d+)?)', q)
    if m:
        x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
        d = pymath.sqrt((x2-x1)**2 + (y2-y1)**2)
        return f"distance = {int(d)}" if d == int(d) else f"distance = {d:.2f}"

    m = re.search(r'th[ée]or[èe]me\s*(?:de\s+)?pythagore\s*:?\s*(\d+(?:\.\d+)?)\s*(\d+(?:\.\d+)?)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        h = pymath.sqrt(a*a + b*b)
        return f"Pythagore: {int(a)}² + {int(b)}² = {int(h)}², hypoténuse = {int(h)}" if h == int(h) else f"Pythagore: hypoténuse = {h:.2f}"

    # 🆕 DIAGONALE rectangle — √(a²+b²), AVANT la diagonale carré (a√2)
    m = re.search(r'diagonale.*?rectangle.*?(\d+(?:\.\d+)?)\s*(?:par|x|×|et)\s*(\d+(?:\.\d+)?)', q)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        d = pymath.sqrt(a*a + b*b)
        return f"diagonale du rectangle = {int(d)}" if d == int(d) else f"diagonale du rectangle = {d:.3f}"

    m = re.search(r'diagonale\s*(?:d[\"u]un?)\s*(?:carr[éeé])\s*(?:de\s+c[ôo]t[éeé]\s*)?(\d+(?:\.\d+)?)', q)
    if m:
        n = float(m.group(1))
        d = n * pymath.sqrt(2)
        return f"diagonale du carré de côté {int(n)} = {d:.3f}"

    m = re.search(r'distance\s*(?:entre|from)\s*\(?(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\)?\s*(?:and|et|to)\s*\(?(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\)?', q)
    if m:
        x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
        d = pymath.sqrt((x2-x1)**2 + (y2-y1)**2)
        return f"distance = {int(d)}" if d == int(d) else f"distance = {d:.2f}"

    # 🆕 STATISTIQUES — moyenne, médiane, mode, écart-type, somme, produit
    m = re.search(r'moyenne\s*(?:de\s+|des?\s+)?([\d\s,;]+)', q)
    if m:
        nums = [float(x) for x in re.findall(r'\d+', m.group(1))]
        if nums:
            avg = sum(nums) / len(nums)
            return f"moyenne = {int(avg)}" if avg == int(avg) else f"moyenne = {avg:.2f}"

    m = re.search(r'm[éeé]diane\s*(?:de\s+|des?\s+)?([\d\s,;]+)', q)
    if m:
        nums = sorted([float(x) for x in re.findall(r'\d+', m.group(1))])
        if nums:
            n = len(nums)
            med = nums[n//2] if n % 2 == 1 else (nums[n//2-1] + nums[n//2]) / 2
            return f"médiane = {int(med)}" if med == int(med) else f"médiane = {med:.2f}"

    m = re.search(r'mode\s*(?:de\s+|des?\s+)?([\d\s,;]+)', q)
    if m:
        from collections import Counter
        nums = [int(x) for x in re.findall(r'\d+', m.group(1))]
        if nums:
            c = Counter(nums)
            mode_val = c.most_common(1)[0][0]
            return f"mode = {mode_val}"

    m = re.search(r'(?:somme|sum)\s*(?:de\s+|des?\s+)?(\d+)\s*(?:à|to|a)\s*(\d+)', q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        total = (a + b) * (b - a + 1) // 2
        return f"somme de {a} à {b} = {total}"

    m = re.search(r'produit\s*(?:de\s+|des?\s+)?(\d+)\s*(?:à|to|a)\s*(\d+)', q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        prod = 1
        for i in range(a, b+1): prod *= i
        return f"produit de {a} à {b} = {prod}"

    m = re.search(r'[ée]cart[- ]type\s*(?:de\s+|des?\s+)?([\d\s,;]+)', q)
    if m:
        nums = [float(x) for x in re.findall(r'\d+', m.group(1))]
        if nums:
            mean = sum(nums) / len(nums)
            var = sum((x - mean)**2 for x in nums) / len(nums)
            std = pymath.sqrt(var)
            return f"écart-type = {std:.2f}"

    # 🆕 CONVERSIONS — degrés ↔ radians
    m = re.search(r'conversion\s*(?:de\s+)?(\d+(?:\.\d+)?)\s*(?:degr[ée]s?|deg)\s*(?:en|vers|to)\s*radians?', q)
    if m:
        deg = float(m.group(1))
        rad = pymath.radians(deg)
        return f"{int(deg)}° = {rad:.3f} rad"

    m = re.search(r'conversion\s*(?:de\s+)?(?:pi|π)\s*radians?\s*(?:en|vers|to)\s*degr[ée]s?', q)
    if m:
        return "π radians = 180°"

    # 🆕 FACTORIELLE
    m = re.search(r'factorielle\s*(?:de\s+)?(\d+)', q)
    if m:
        n = int(m.group(1))
        if n > 100: return None
        import math as _math
        result = _math.factorial(n)
        return f"{n}! = {result}"

    # 🆕 OPÉRATIONS CHAÎNÉES — 3*4*5, 1+2+3+4+5 (AVANT les patterns simples !)
    m = re.search(r'(\d+)\s*[\*×xX]\s*(\d+)\s*[\*×xX]\s*(\d+)', q)
    if m:
        a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{a} × {b} × {c} = {a * b * c}"

    m = re.search(r'(\d+)\s*\+\s*(\d+)\s*\+\s*(\d+)\s*\+\s*(\d+)\s*\+\s*(\d+)', q)
    if m:
        nums = [int(m.group(i)) for i in range(1, 6)]
        return ' + '.join(str(n) for n in nums) + f" = {sum(nums)}"

    # 🆕 DÉRIVÉE de constante — ax → a (sans ^)
    m = re.search(r'd[éeé]riv[ée]e?\s*(?:de\s+)?(\d+)\s*x\b', q)
    if m:
        a = int(m.group(1))
        return f"dérivée de {a}x = {a}"

    # 🆕 INTÉGRALE de constante — a dx → ax + C (sans ^)
    m = re.search(r'int[éeé]grale?\s*(?:de\s+)?(\d+)\s*dx', q)
    if m:
        a = int(m.group(1))
        if a == 0: return "∫ 0 dx = C"
        return f"∫ {a} dx = {a}x + C"

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

    # 🆕 FACTORISATION x^2 - N → (x+√N)(x-√N) — AVANT la soustraction !
    m = re.search(r'factoris(?:er?|ation)\s*x\s*(?:\^|²)\s*(\d+)\s*-\s*(\d+)', q)
    if m:
        exp_n, n = int(m.group(1)), int(m.group(2))
        if exp_n == 2:
            root = int(pymath.sqrt(n))
            if root * root == n:
                return f"x² - {n} = (x + {root})(x - {root})"
            return f"x² - {n} = (x + √{n})(x - √{n})"

    # 🆕 RÉSOUDRE x^2 = N — AVANT la soustraction
    m = re.search(r'r[éeé]soudre\s*x\s*(?:\^|²)\s*(\d+)\s*=\s*(\d+)', q)
    if m:
        exp_n, n = int(m.group(1)), int(m.group(2))
        if exp_n == 2:
            root = int(pymath.sqrt(n))
            if root * root == n:
                return f"x² = {n} → x = ±{root}"
            return f"x² = {n} → x = ±{pymath.sqrt(n):.4f}"

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
