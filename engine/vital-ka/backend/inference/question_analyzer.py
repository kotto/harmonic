"""
Question Analyzer — Compréhension de l'intention utilisateur
=============================================================
Analyse une question pour extraire :
  - type : définition, mécanisme, comparaison, identité, procédure, factualité
  - sujet_central : le concept clé (pas juste un strip de préfixe)
  - profondeur : courte (1 phrase) vs détaillée (paragraphe)
  - angle : ce que l'utilisateur cherche vraiment à comprendre

Ce module remplace le _extract_subject() simpliste de harmonic_model.py.
Il ne dépend d'aucun LLM — purement analytique.

Usage :
  from question_analyzer import analyze_question
  intent = analyze_question("pourquoi le ciel est bleu")
  print(intent.type)        # 'mecanisme'
  print(intent.sujet)       # 'ciel'
  print(intent.profondeur)  # 'detaillee'
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURE DE RÉSULTAT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class QuestionIntent:
    """Intention extraite d'une question utilisateur."""
    type: str = 'definition'          # definition|mecanisme|comparaison|identite|procedure|factualite|conversation
    sujet: str = ''                   # concept central nettoyé
    sujet_brut: str = ''              # sujet avant nettoyage
    mots_cles: List[str] = field(default_factory=list)  # mots significatifs extraits
    profondeur: str = 'standard'      # courte|standard|detaillee
    angle: str = ''                   # ce que l'utilisateur veut vraiment savoir
    langue: str = 'fr'                # fr|en|autre
    est_question: bool = True         # False si c'est une affirmation/conversation
    original: str = ''                # question originale


# ═══════════════════════════════════════════════════════════════════════════════
# LEXIQUES
# ═══════════════════════════════════════════════════════════════════════════════

# Mots-outils à ignorer pour l'extraction du sujet
_STOPWORDS_FR = {
    'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'd', 'l',
    'et', 'est', 'sont', 'a', 'ont', 'au', 'aux', 'ce', 'cet', 'cette', 'ces',
    'que', 'qui', 'quoi', 'dont', 'où', 'ou', 'ne', 'pas', 'ni',
    'dans', 'sur', 'sous', 'pour', 'par', 'avec', 'sans', 'vers', 'chez',
    'mais', 'donc', 'or', 'car', 'aussi', 'puis', 'ensuite',
    'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses',
    'notre', 'votre', 'leur', 'leurs',
    'plus', 'moins', 'très', 'trop', 'aussi', 'encore', 'déjà',
    'tu', 'vous', 'nous', 'on', 'il', 'elle', 'ils', 'elles',
    # Verbes questionnants (traités séparément)
    'explique', 'expliques', 'expliquer', 'expliquez',
    'decris', 'decrire', 'decris', 'decrivez',
    'parle', 'parles', 'parler', 'parlez',
    'donne', 'donnes', 'donner', 'donnez',
    'dit', 'dis', 'dire',
    'fait', 'fais', 'faire',
    'peux', 'peut', 'peuvent', 'puis', 'pouvez', 'pouvoir',
    'veux', 'veut', 'vouloir', 'voudrais', 'voudrait',
    'sais', 'sait', 'savoir', 'connais', 'connaitre',
}

_STOPWORDS_EN = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'can', 'shall',
    'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from',
    'it', 'its', 'and', 'or', 'not', 'but', 'if', 'so', 'as', 'than',
    'that', 'this', 'these', 'those', 'which', 'who', 'whom', 'whose',
    'i', 'you', 'he', 'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'my', 'your', 'his', 'our', 'their',
    'more', 'less', 'very', 'too', 'also', 'still', 'already',
    'explain', 'describe', 'tell', 'give', 'say', 'make',
    'can', 'could', 'would', 'should', 'may', 'might',
    'want', 'know', 'think', 'feel',
}

# Préfixes de questions (ordre = du plus long au plus court pour match greed)
_PREFIXES_FR = [
    # Mécanisme / explication
    'pourquoi est-ce que', 'comment est-ce que',
    'pourquoi le', 'pourquoi la', 'pourquoi les', 'pourquoi l',
    'comment le', 'comment la', 'comment les', 'comment l',
    'comment fonctionne', 'comment marchent', 'comment marche',
    'pourquoi', 'comment',
    # Définition
    "qu'est-ce que", "qu'est ce que", 'quest-ce que', 'c est quoi',
    "qu'est-ce qu'il", 'c quoi', 'que veut dire', 'que signifie',
    'definis', 'definir', 'definition de', 'definition du', 'definition de la',
    "qu'est-ce que c'est", 'c est quoi',
    'qu est ce que', 'qu est ce qu',
    # Identité
    'qui a decouvert', 'qui a invente', 'qui a cree', 'qui a fonde',
    'qui a ecrit', 'qui a compose', 'qui a dessine',
    'qui est', 'qui etait', 'qui sont',
    # Temporel
    'quand est-ce que', 'quand le', 'quand la', 'quand',
    # Spatial
    'ou se trouve', 'ou est', 'ou sont', 'ou',
    # Procédure
    'comment faire pour', 'comment on fait', 'etapes pour',
    'comment puis-je', 'comment je peux',
    # Demandes générales
    'explique moi', 'expliquez moi', 'explique', 'expliquez',
    'parle moi de', 'parlez moi de', 'parle de', 'parlez de', 'parle',
    'decris moi', 'decris', 'decrivez',
    'donne moi', 'donnez moi',
    'dis moi', 'dites moi',
    'montre moi', 'montrez moi',
    # Importance / valeur
    'donne un exemple de', 'donne un exemple d', 'donne des exemples de', 'donne des exemples',
    # Comparaison
    'quelle est la difference entre', 'quel est la difference entre',
    'difference entre', 'compare',
]

_PREFIXES_EN = [
    'why does', 'why do', 'why is', 'why are', 'why',
    'how does', 'how do', 'how is', 'how are', 'how to', 'how',
    'what is', 'what are', "what's", 'whats',
    'what does', 'what do', 'what can',
    'who is', 'who was', 'who are', 'who discovered', 'who invented', 'who created',
    'when did', 'when was', 'when',
    'where is', 'where are', 'where',
    'explain', 'describe', 'tell me about', 'tell me',
    'define', 'give me', 'show me',
    'what is the difference between', 'difference between', 'compare',
    'what is a', 'what is an', 'what is the',
]


# ═══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DE LANGUE
# ═══════════════════════════════════════════════════════════════════════════════

_MOTS_FR = {'le', 'la', 'les', 'est', 'une', 'des', 'pourquoi', 'comment',
            'qu', 'que', 'qui', 'dans', 'avec', 'pour', 'sur', 'par',
            'explique', 'decris', 'parle', 'donne'}

_MOTS_EN = {'the', 'is', 'are', 'what', 'how', 'why', 'who', 'when', 'where',
            'explain', 'describe', 'tell', 'define', 'which'}


def _detect_language(text: str) -> str:
    """Détecte la langue (fr ou en) par comptage de mots-outils."""
    words = set(text.lower().split())
    fr_count = len(words & _MOTS_FR)
    en_count = len(words & _MOTS_EN)
    if en_count > fr_count:
        return 'en'
    return 'fr'


# ═══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DU TYPE DE QUESTION
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_type(question: str, lang: str) -> str:
    """Détecte le type de question."""
    q = question.lower().strip()

    if lang == 'en':
        if any(w in q for w in ['why']):
            return 'mecanisme'
        if any(w in q for w in ['how to', 'how do', 'how does', 'how can']):
            return 'procedure'
        if any(w in q for w in ['how']):
            return 'mecanisme'
        if any(w in q for w in ['who is', 'who was', 'who discovered', 'who invented']):
            return 'identite'
        if any(w in q for w in ['when', 'what year']):
            return 'factualite'
        if any(w in q for w in ['where']):
            return 'factualite'
        if any(w in q for w in ['difference between', 'compare', 'versus', 'vs']):
            return 'comparaison'
        if any(w in q for w in ['what is', 'what are', "what's", 'define']):
            return 'definition'
        return 'definition'

    # Exemple / illustration
    if any(w in q for w in ['donne un exemple', 'donner un exemple', 'exemple de',
                            'illustre', 'illustrer', 'give an example']):
        return 'comparaison'  # réutilisé pour les exemples

    # Importance
    if any(w in q for w in ['pourquoi est-ce important', 'pourquoi est important',
                            'en quoi est important', 'quelle est l importance',
                            'why is important', 'why is it important']):
        return 'importance'

    # Français
    # Importance (avant pourquoi/comment génériques pour capturer "pourquoi X est important")
    if any(w in q for w in ['pourquoi est-ce important', 'pourquoi est important',
                            'en quoi est important', 'quelle est l importance',
                            'est important', 'est essentiel', 'est crucial',
                            'est si important', 'est si essentiel']):
        return 'importance'

    if 'pourquoi' in q:
        return 'mecanisme'
    if any(w in q for w in ['comment faire', 'comment on fait', 'etapes', 'comment puis']):
        return 'procedure'
    if 'comment' in q:
        return 'mecanisme'
    if any(w in q for w in ['qui a decouvert', 'qui a invente', 'qui a cree',
                            'qui a fonde', 'qui a ecrit', 'qui a compose',
                            'qui est', 'qui etait']):
        return 'identite'
    if 'quand' in q:
        return 'factualite'
    if any(w in q for w in ['ou se trouve', 'ou est', 'ou sont']):
        return 'factualite'
    if any(w in q for w in ['difference entre', 'compare']):
        return 'comparaison'
    if any(w in q for w in ["qu'est-ce que", "qu est ce que", "c'est quoi",
                            "c est quoi", 'que veut dire', 'que signifie',
                            'definis', 'qu est-ce qu', "qu'est-ce qu"]):
        return 'definition'

    # Si pas de marqueur interrogatif → c'est peut-être conversationnel
    if not any(w in q for w in ['?', 'explique', 'decris', 'parle', 'donne',
                                 'dis', 'quel', 'quelle', 'quels', 'quelles']):
        return 'conversation'

    return 'definition'


# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION DU SUJET CENTRAL
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_subject(question: str, lang: str, q_type: str) -> tuple:
    """
    Extrait le sujet central de la question.
    Retourne (sujet_nettoye, sujet_brut, mots_cles).
    """
    q = question.lower().strip()

    # 1. Retirer les préfixes connus (du plus long au plus court)
    prefixes = _PREFIXES_FR if lang == 'fr' else _PREFIXES_EN
    for prefix in sorted(prefixes, key=len, reverse=True):
        if q.startswith(prefix):
            q = q[len(prefix):].strip()
            break

    # 2. Retirer la ponctuation finale
    q = q.strip('?.,!;:¿¡')

    sujet_brut = q

    # 3. Retirer les articles initiaux (pour le sujet nettoyé)
    sujet_clean = q
    for art in ['le ', 'la ', "l'", 'l ', 'les ', 'un ', 'une ', 'des ', 'du ',
                'the ', 'a ', 'an ']:
        if sujet_clean.startswith(art):
            sujet_clean = sujet_clean[len(art):]
            break
    sujet_clean = sujet_clean.strip()

    # 4. Extraire les mots-clés significatifs
    stopwords = _STOPWORDS_FR if lang == 'fr' else _STOPWORDS_EN
    words = [w.strip('.,!?;:()[]{}«»""\'\'') for w in q.split()]
    mots_cles = [w for w in words if len(w) >= 2 and w not in stopwords]

    # 5. Nettoyer le sujet pour affichage (sans article)
    sujet = sujet_clean

    return sujet, sujet_brut, mots_cles


# ═══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DE LA PROFONDEUR ATTENDUE
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_profondeur(question: str, q_type: str, mots_cles: list) -> str:
    """Détermine si l'utilisateur veut une réponse courte ou détaillée."""
    q = question.lower()

    # Demande explicite de brièveté
    if any(w in q for w in ['brievement', 'en bref', 'en resume', 'rapidement',
                            'en une phrase', 'simplement', 'simplement',
                            'briefly', 'in short', 'quickly']):
        return 'courte'

    # Demande explicite de détail
    if any(w in q for w in ['en detail', 'detaille', 'precisement', 'profondement',
                            'completement', 'totalement', 'explique bien',
                            'in detail', 'detailed', 'thoroughly']):
        return 'detaillee'

    # Selon le type
    if q_type == 'factualite':
        return 'courte'
    if q_type == 'identite':
        return 'courte'
    if q_type in ('mecanisme', 'importance'):
        return 'detaillee'  # "pourquoi/comment" et "pourquoi important" → explication détaillée
    if q_type == 'definition':
        return 'standard'
    if q_type == 'comparaison':
        return 'detaillee'
    if q_type == 'procedure':
        return 'detaillee'
    if q_type == 'conversation':
        return 'courte'

    # Par défaut selon la longueur de la question
    if len(mots_cles) <= 2:
        return 'courte'
    return 'standard'


# ═══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DE L'ANGLE
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_angle(q_type: str, mots_cles: list, sujet: str) -> str:
    """Détermine l'angle de la réponse attendue."""
    if q_type == 'definition':
        return f"definir {sujet}"
    if q_type == 'mecanisme':
        return f"expliquer le mecanisme de {sujet}"
    if q_type == 'identite':
        return f"identifier qui est associe a {sujet}"
    if q_type == 'comparaison':
        return f"comparer {sujet}"
    if q_type == 'procedure':
        return f"detailer les etapes pour {sujet}"
    if q_type == 'factualite':
        return f"donner le fait precis sur {sujet}"
    if q_type == 'conversation':
        return f"repondre naturellement a propos de {sujet}"
    return f"expliquer {sujet}"


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_question(question: str) -> QuestionIntent:
    """
    Analyse complète d'une question utilisateur.

    Args:
        question: texte brut de la question

    Returns:
        QuestionIntent avec type, sujet, profondeur, angle, mots_cles

    Usage:
        intent = analyze_question("pourquoi le ciel est bleu ?")
        # intent.type = 'mecanisme'
        # intent.sujet = 'ciel est bleu'
        # intent.profondeur = 'detaillee'
    """
    question = question.strip()
    lang = _detect_language(question)
    q_type = _detect_type(question, lang)
    sujet, sujet_brut, mots_cles = _extract_subject(question, lang, q_type)
    profondeur = _detect_profondeur(question, q_type, mots_cles)
    angle = _detect_angle(q_type, mots_cles, sujet)

    est_question = (q_type != 'conversation' and
                    ('?' in question or
                     any(question.lower().startswith(p) for p in
                         ['pourquoi', 'comment', 'qu', 'qui', 'ou ', 'quand',
                          'explique', 'decris', 'parle', 'donne',
                          'what', 'how', 'why', 'who', 'when', 'where'])))

    return QuestionIntent(
        type=q_type,
        sujet=sujet,
        sujet_brut=sujet_brut,
        mots_cles=mots_cles,
        profondeur=profondeur,
        angle=angle,
        langue=lang,
        est_question=est_question,
        original=question,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    print("=" * 60)
    print("QUESTION ANALYZER — Démo")
    print("=" * 60)

    tests = [
        "explique la lumiere",
        "qu'est-ce que la conscience ?",
        "pourquoi le ciel est bleu ?",
        "comment fonctionne la photosynthese ?",
        "qui a decouvert la relativite ?",
        "quelle est la difference entre onde et particule ?",
        "comment faire pour apprendre vite ?",
        "quand einstein a-t-il publie la relativite ?",
        "parle moi de l'amour",
        "bonjour comment ca va ?",
        "what is light ?",
        "how does gravity work ?",
        "who discovered penicillin ?",
    ]

    for q in tests:
        intent = analyze_question(q)
        print(f"\n>> {q}")
        print(f"   type={intent.type}  sujet='{intent.sujet}'  prof={intent.profondeur}")
        print(f"   mots_cles={intent.mots_cles}")
        print(f"   angle='{intent.angle}'")


if __name__ == '__main__':
    demo()
