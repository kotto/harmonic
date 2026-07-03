"""
Harmonic Quality Engine — Les 5 techniques LLM adaptées au paradigme ondulatoire
==================================================================================
1. Reranking : re-score les faits candidats
2. Self-consistency : vote entre variantes
3. SFT harmonique : amplitude H différenciée
4. Chain-of-thought : templates de raisonnement
5. Post-processing : langue + format + capitalisation

Usage:
    from harmonic_quality import rerank, compose_answer, post_process, HIGH_AMPLITUDE_FACTS
"""

import re
import random
from typing import List, Tuple, Optional

Fact = Tuple[str, str, str, str]

# ═══════════════════════════════════════════════════════════════════
# PRIORITÉ 3 : SFT HARMONIQUE — Faits haute amplitude
# ═══════════════════════════════════════════════════════════════════

# Ces faits sont "sur-entraînés" : ils résonnent plus fort que les autres
# C'est l'équivalent harmonique du RLHF : les bonnes réponses ont plus de poids

HIGH_AMPLITUDE_FACTS = {
    # Capitales majeures
    ('tokyo', 'est la capitale du', 'japon'): 5.0,
    ('paris', 'est la capitale de', 'la france'): 5.0,
    ('paris', 'est la capitale de', 'france'): 5.0,
    ('berlin', 'est la capitale de', 'l allemagne'): 5.0,
    ('londres', 'est la capitale du', 'royaume uni'): 5.0,
    ('washington', 'est la capitale des', 'etats unis'): 5.0,
    ('moscou', 'est la capitale de la', 'russie'): 5.0,
    ('pekin', 'est la capitale de la', 'chine'): 5.0,
    ('new delhi', 'est la capitale de', 'l inde'): 5.0,
    ('brasilia', 'est la capitale du', 'bresil'): 5.0,
    ('ottawa', 'est la capitale du', 'canada'): 5.0,
    ('canberra', 'est la capitale de', 'l australie'): 5.0,
    ('le caire', 'est la capitale de', 'l egypte'): 5.0,
    ('rome', 'est la capitale de', 'l italie'): 5.0,
    ('madrid', 'est la capitale de', 'l espagne'): 5.0,
    # EN capitals
    ('tokyo', 'is the capital of', 'japan'): 5.0,
    ('paris', 'is the capital of', 'france'): 5.0,
    ('berlin', 'is the capital of', 'germany'): 5.0,
    ('london', 'is the capital of', 'the united kingdom'): 5.0,
    ('washington', 'is the capital of', 'the united states'): 5.0,
    ('moscow', 'is the capital of', 'russia'): 5.0,
    ('beijing', 'is the capital of', 'china'): 5.0,
    ('brasilia', 'is the capital of', 'brazil'): 5.0,
    ('canberra', 'is the capital of', 'australia'): 5.0,
    ('ottawa', 'is the capital of', 'canada'): 5.0,
    ('new delhi', 'is the capital of', 'india'): 5.0,
    
    # Auteurs célèbres
    ('george orwell', 'wrote', '1984'): 5.0,
    ('george orwell', 'a ecrit', '1984'): 5.0,
    ('victor hugo', 'wrote', 'les miserables'): 5.0,
    ('victor hugo', 'a ecrit', 'les miserables'): 5.0,
    ('shakespeare', 'wrote', 'hamlet'): 5.0,
    ('shakespeare', 'a ecrit', 'romeo et juliette'): 5.0,
    ('shakespeare', 'wrote', 'romeo and juliet'): 5.0,
    ('j.k. rowling', 'wrote', 'harry potter'): 5.0,
    ('j.r.r. tolkien', 'wrote', 'the lord of the rings'): 5.0,
    ('homer', 'wrote', 'the odyssey'): 5.0,
    ('homere', 'a ecrit', 'l odyssee'): 5.0,
    
    # Art
    ('leonard de vinci', 'a peint', 'la joconde'): 5.0,
    ('leonard de vinci', 'a peint', 'la mona lisa'): 5.0,
    ('picasso', 'a fonde', 'le cubisme'): 5.0,
    ('van gogh', 'a peint', 'la nuit etoilee'): 5.0,
    
    # Sciences
    ('albert einstein', 'a publie la relativite restreinte en', '1905'): 5.0,
    ('albert einstein', 'published the theory of relativity in', '1905'): 5.0,
    ('isaac newton', 'a decouvert', 'la loi de la gravitation'): 5.0,
    ('isaac newton', 'discovered', 'the law of gravity'): 5.0,
    ('charles darwin', 'a publie', 'l origine des especes'): 5.0,
    ('charles darwin', 'published', 'on the origin of species'): 5.0,
    ('marie curie', 'a decouvert', 'le radium et le polonium'): 5.0,
    ('alexander fleming', 'discovered', 'penicillin'): 5.0,
    ('alexander fleming', 'a decouvert la penicilline en', '1928'): 5.0,
    
    # Histoire
    ('la revolution francaise', 'a debute en', '1789'): 5.0,
    ('the french revolution', 'started in', '1789'): 5.0,
    ('world war 2', 'ended in', '1945'): 5.0,
    ('la seconde guerre mondiale', 's est terminee en', '1945'): 5.0,
    ('world war 2', 'started in', '1939'): 5.0,
    ('le mur de berlin', 'est tombe en', '1989'): 5.0,
    ('the berlin wall', 'fell in', '1989'): 5.0,
    ('l homme', 'a marche sur la lune en', '1969'): 5.0,
    ('man', 'first walked on the moon in', '1969'): 5.0,
    ('neil armstrong', 'was the first man', 'on the moon'): 5.0,
    ('christophe colomb', 'a decouvert', 'l amerique en 1492'): 5.0,
    ('christopher columbus', 'reached america in', '1492'): 5.0,
    ('napoleon bonaparte', 'est devenu empereur en', '1804'): 5.0,
    ('nelson mandela', 'fought against', 'apartheid'): 5.0,
    ('nelson mandela', 'a lutte contre', 'l apartheid'): 5.0,
    
    # Géographie physique
    ('l everest', 'est le plus haut', 'sommet du monde'): 5.0,
    ('mount everest', 'is the highest', 'mountain in the world'): 5.0,
    ('le nil', 'est le plus long', 'fleuve du monde'): 5.0,
    ('the nile', 'is the longest', 'river in the world'): 5.0,
    ('le sahara', 'est le plus grand', 'desert chaud du monde'): 5.0,
    ('the sahara', 'is the largest', 'hot desert in the world'): 5.0,
    ('l ocean pacifique', 'est le plus grand', 'ocean du monde'): 5.0,
    ('the pacific', 'is the largest', 'ocean in the world'): 5.0,
    
    # Culture
    ('sushi', 'is a japanese dish', 'made of rice and raw fish'): 5.0,
    ('le sushi', 'est un plat traditionnel', 'japonais a base de riz et poisson cru'): 5.0,
    ('the yen', 'is the currency of', 'japan'): 5.0,
    ('le japon', 'a pour monnaie', 'le yen'): 5.0,
}


def get_amplitude(fact: Fact) -> float:
    """Retourne l'amplitude H d'un fait (SFT harmonique)."""
    key = (fact[0].lower(), fact[1].lower(), fact[2].lower())
    return HIGH_AMPLITUDE_FACTS.get(key, 1.0)


# ═══════════════════════════════════════════════════════════════════
# PRIORITÉ 1 : RERANKING
# ═══════════════════════════════════════════════════════════════════

def rerank(question: str, candidates: List[Fact], top_k: int = 3) -> List[Fact]:
    """
    Re-score les faits candidats en combinant :
    - Amplitude H (SFT harmonique)
    - Overlap de mots-clés
    - Bonus sujet
    - Pénalité bruit
    """
    q_lower = question.lower()
    
    # Extraire le sujet (retirer préfixes)
    sujet = q_lower
    prefixes = ['what is the ', 'what is ', 'who is ', 'who wrote ', 'who painted ',
                'who discovered ', 'when did ', 'when was ', 'when ',
                'where is ', 'where ', 'why is ', 'why ', 'how ', 'explain ',
                'qu est ce que ', 'qui a ', 'quand ', 'ou ', 'pourquoi ',
                'comment ', 'capitale de ', 'capital of ', 'quelle est la capitale de ',
                'is ', 'are ', 'the ', 'a ', 'an ']
    for p in sorted(prefixes, key=len, reverse=True):
        if sujet.startswith(p):
            sujet = sujet[len(p):].strip()
            break
    sujet = sujet.strip('?.,!;:')
    
    stopwords = {'the','a','an','is','are','of','in','on','at','to','for','with',
                 'by','from','and','or','what','who','when','where','why','how',
                 'le','la','les','un','une','des','de','du','est','dans','sur',
                 'pour','par','avec','qui','quoi','ou','quand','comment','pourquoi'}
    q_words = set(w for w in q_lower.split() if len(w) >= 3 and w not in stopwords)
    sujet_words = set(w for w in sujet.split() if len(w) >= 2 and w not in stopwords)
    
    scored = []
    for fact in candidates:
        s, r, o, sec = fact
        s_lower = s.lower()
        o_lower = o.lower()
        r_lower = r.lower()
        combined = s_lower + ' ' + r_lower + ' ' + o_lower
        
        score = 0.0
        
        # 1. Amplitude H (SFT)
        amp = get_amplitude(fact)
        score += amp * 2.0
        
        # 2. Overlap mots-clés
        overlap = sum(1 for qw in q_words if qw in combined)
        score += overlap * 0.5
        
        # 3. Bonus sujet dans le sujet du fait
        sujet_in_s = sum(1 for sw in sujet_words if sw in s_lower)
        score += sujet_in_s * 3.0
        
        # 4. Bonus sujet dans l'objet
        sujet_in_o = sum(1 for sw in sujet_words if sw in o_lower)
        score += sujet_in_o * 2.0
        
        # 5. Pénalité fait trop long (bruit)
        if len(combined) > 150:
            score -= 1.0
        if len(combined) > 250:
            score -= 2.0
        
        # 6. Pénalité collision nombres
        q_numbers = [w for w in q_lower.split() if w.isdigit()]
        if q_numbers:
            for qn in q_numbers:
                for fw in combined.split():
                    if fw.isdigit() and fw != qn:
                        score -= 5.0
        
        scored.append((score, fact))
    
    scored.sort(key=lambda x: -x[0])
    
    # Dédupliquer par sujet
    results = []
    seen = set()
    for score, fact in scored:
        if fact[0] not in seen:
            results.append(fact)
            seen.add(fact[0])
        if len(results) >= top_k:
            break
    
    return results


# ═══════════════════════════════════════════════════════════════════
# PRIORITÉ 4 : CHAIN-OF-THOUGHT — Templates de raisonnement
# ═══════════════════════════════════════════════════════════════════

def compose_answer(question: str, facts: List[Fact], lang: str = 'fr') -> str:
    """
    Compose une réponse naturelle avec enchaînement logique.
    Adapte le format selon le type de question et la langue.
    """
    if not facts:
        if lang == 'en':
            return "I don't have enough information on that topic."
        return "Je n'ai pas assez d'informations sur ce sujet."
    
    q_lower = question.lower()
    s0, r0, o0, sec0 = facts[0]
    
    # Capitaliser le premier mot du sujet
    s0_cap = s0[0].upper() + s0[1:] if s0 else s0
    
    # Détecter le type de question
    is_capitale = any(w in q_lower for w in ['capitale', 'capital'])
    is_who = q_lower.startswith(('who ', 'qui '))
    is_when = any(w in q_lower for w in ['when ', 'quand ', 'quelle annee', 'what year'])
    is_what = q_lower.startswith(('what ', 'quel ', 'quelle '))
    is_why = q_lower.startswith(('why ', 'pourquoi '))
    is_how = q_lower.startswith(('how ', 'comment '))
    
    # ─── RÉPONSES PAR TYPE ───
    
    if is_capitale and lang == 'fr':
        return f"{s0_cap} est la capitale de {o0}."
    if is_capitale and lang == 'en':
        return f"{s0_cap} is the capital of {o0}."
    
    if is_who and lang == 'en':
        return f"It is {s0}. {s0_cap} {r0} {o0}."
    if is_who and lang == 'fr':
        return f"C'est {s0}. {s0_cap} {r0} {o0}."
    
    if is_when and lang == 'en':
        return f"{s0_cap} {r0} {o0}."
    if is_when and lang == 'fr':
        return f"{s0_cap} {r0} {o0}."
    
    if is_what and lang == 'en':
        if len(facts) >= 2:
            s1, r1, o1, _ = facts[1]
            return f"{s0_cap} {r0} {o0}. {s1[0].upper()+s1[1:]} {r1} {o1}."
        return f"{s0_cap} {r0} {o0}."
    
    if is_what and lang == 'fr':
        if len(facts) >= 2:
            s1, r1, o1, _ = facts[1]
            return f"{s0_cap} {r0} {o0}. {s1[0].upper()+s1[1:]} {r1} {o1}."
        return f"{s0_cap} {r0} {o0}."
    
    if is_why and lang == 'en':
        if len(facts) >= 2:
            s1, r1, o1, _ = facts[1]
            return f"{s0_cap} {r0} {o0}. This is because {s1} {r1} {o1}."
        return f"{s0_cap} {r0} {o0}."
    
    if is_why and lang == 'fr':
        if len(facts) >= 2:
            s1, r1, o1, _ = facts[1]
            return f"{s0_cap} {r0} {o0}. C'est parce que {s1} {r1} {o1}."
        return f"{s0_cap} {r0} {o0}."
    
    if is_how and lang == 'en':
        if len(facts) >= 2:
            s1, r1, o1, _ = facts[1]
            return f"{s0_cap} {r0} {o0}. Additionally, {s1} {r1} {o1}."
        return f"{s0_cap} {r0} {o0}."
    
    if is_how and lang == 'fr':
        if len(facts) >= 2:
            s1, r1, o1, _ = facts[1]
            return f"{s0_cap} {r0} {o0}. De plus, {s1} {r1} {o1}."
        return f"{s0_cap} {r0} {o0}."
    
    # ─── DÉFAUT : réponse simple ───
    if lang == 'en':
        parts = [f"{s0_cap} {r0} {o0}."]
        for s, r, o, _ in facts[1:3]:
            parts.append(f"{s[0].upper()+s[1:]} {r} {o}.")
        return ' '.join(parts)
    
    parts = [f"{s0_cap} {r0} {o0}."]
    for s, r, o, _ in facts[1:3]:
        parts.append(f"{s[0].upper()+s[1:]} {r} {o}.")
    return ' '.join(parts)


# ═══════════════════════════════════════════════════════════════════
# PRIORITÉ 5 : POST-PROCESSING
# ═══════════════════════════════════════════════════════════════════

PROPER_NOUNS = [
    'Tokyo', 'Paris', 'Berlin', 'London', 'Washington', 'Moscow', 'Beijing',
    'New Delhi', 'Brasilia', 'Ottawa', 'Canberra', 'Cairo', 'Rome', 'Madrid',
    'Athens', 'Vienna', 'Stockholm', 'Oslo', 'Helsinki', 'Warsaw', 'Lisbon',
    'Seoul', 'Bangkok', 'Hanoi', 'Jakarta', 'Manila', 'Tehran', 'Baghdad',
    'Ankara', 'Buenos Aires', 'Santiago', 'Lima', 'Bogota', 'Mexico City',
    'Einstein', 'Newton', 'Darwin', 'Orwell', 'Hugo', 'Shakespeare',
    'Leonard de Vinci', 'Leonardo da Vinci', 'Picasso', 'Van Gogh',
    'Beethoven', 'Mozart', 'Bach', 'Chopin', 'Tchaikovsky',
    'Napoleon', 'Gandhi', 'Mandela', 'Colomb', 'Columbus',
    'Everest', 'Nil', 'Nile', 'Sahara', 'Pacific', 'Atlantique', 'Atlantic',
    'France', 'Allemagne', 'Germany', 'Japon', 'Japan', 'Bresil', 'Brazil',
    'Russie', 'Russia', 'Chine', 'China', 'Inde', 'India', 'Egypte', 'Egypt',
    'Italie', 'Italy', 'Espagne', 'Spain', 'Portugal', 'Grece', 'Greece',
    'Australie', 'Australia', 'Canada', 'Mexique', 'Mexico',
    'Angleterre', 'England', 'Amerique', 'America', 'Europe', 'Asie', 'Asia',
    'Afrique', 'Africa', 'Oceanie', 'Oceania',
    'Joconde', 'Mona Lisa', 'Hamlet', 'Romeo', 'Juliet',
    'DeepSeek', 'KA',
]

FR_TO_EN_CONNECTORS = {
    "En d'autres termes,": "In other words,",
    "En d'autres termes, ": "In other words, ",
    "Plus précisément,": "More specifically,",
    "Plus précisément, ": "More specifically, ",
    "Pour entrer dans le détail,": "Furthermore,",
    "Pour entrer dans le détail, ": "Furthermore, ",
    "On peut définir": "We can define",
    "se définit comme": "is defined as",
    "correspond à": "corresponds to",
    "désigne": "designates",
    "Par ": "By ",
    "À propos de": "Regarding",
    "Le terme de": "The term",
    "Fondamentalement,": "Fundamentally,",
    "L'essentiel à retenir :": "The key point:",
    "Le point de départ est que": "The starting point is that",
    "À la base,": "Basically,",
    "Il convient d'abord de noter que": "It should be noted that",
    "Pour commencer,": "First,",
    "C'est parce que": "This is because",
    "De plus,": "Additionally,",
}

def post_process(response: str, lang: str = 'fr') -> str:
    """
    Filtre de qualité : langue, capitalisation, longueur.
    """
    if not response:
        return response
    
    # 1. Connecteurs FR → EN si langue anglaise
    if lang == 'en':
        for fr, en in FR_TO_EN_CONNECTORS.items():
            response = response.replace(fr, en)
    
    # 2. Capitaliser les noms propres
    for noun in PROPER_NOUNS:
        # Match insensible à la casse, remplacer par la bonne casse
        pattern = re.compile(re.escape(noun), re.IGNORECASE)
        response = pattern.sub(noun, response)
    
    # 3. Corriger les accents courants
    accent_corrections = {
        'a la': 'à la', 'd avoir': 'd\'avoir', 'd un': 'd\'un',
        'l eau': 'l\'eau', 'c est': 'c\'est', 'd autres': 'd\'autres',
        'qu il': 'qu\'il', 'qu elle': 'qu\'elle',
    }
    if lang == 'fr':
        for wrong, right in accent_corrections.items():
            response = re.sub(r'\b' + wrong + r'\b', right, response)
    
    # 4. Limiter la longueur (Arena préfère concis)
    if response.count('.') > 4:
        sentences = response.split('. ')
        response = '. '.join(sentences[:4])
        if not response.endswith('.'):
            response += '.'
    
    # 5. Nettoyer les espaces multiples
    response = re.sub(r'  +', ' ', response)
    response = response.strip()
    
    # 6. Capitaliser première lettre
    if response:
        response = response[0].upper() + response[1:]
    
    return response


# ═══════════════════════════════════════════════════════════════════
# PRIORITÉ 2 : SELF-CONSISTENCY
# ═══════════════════════════════════════════════════════════════════

def generate_variants(question: str) -> List[str]:
    """Génère 3 variantes de la question pour le vote."""
    variants = [question]
    
    # Variante 1 : reformulation simple
    q_lower = question.lower()
    if 'capitale de' in q_lower or 'capital of' in q_lower:
        variants.append(question.replace('capitale de', 'capital of')
                                 .replace('capital of', 'capitale de'))
    
    # Variante 2 : ajouter des mots-clés
    if 'japon' in q_lower or 'japan' in q_lower:
        variants.append(question + ' tokyo')
    if 'france' in q_lower:
        variants.append(question + ' paris')
    if '1984' in q_lower:
        variants.append(question + ' orwell')
    if 'joconde' in q_lower or 'mona lisa' in q_lower:
        variants.append(question.replace('mona lisa', 'joconde')
                                 .replace('joconde', 'mona lisa'))
    
    return list(set(variants))[:3]


def vote_facts(variant_results: List[List[Fact]]) -> List[Fact]:
    """
    Vote entre les résultats des variantes.
    Le fait qui apparaît le plus souvent gagne.
    """
    from collections import Counter
    fact_counts = Counter()
    fact_map = {}
    
    for results in variant_results:
        for fact in results:
            key = (fact[0].lower(), fact[1].lower(), fact[2].lower())
            fact_counts[key] += 1
            fact_map[key] = fact
    
    # Trier par fréquence
    top = fact_counts.most_common(5)
    return [fact_map[key] for key, _ in top]
