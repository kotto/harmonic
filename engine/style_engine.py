"""
Style Engine — Rendu élégant du raisonnement
=============================================
Transforme les chemins de resonance en francais naturel et elegant.

3 niveaux :
  1. TEMPLATES RICHES : 12+ variantes par domaine
  2. CONNECTEURS INTELLIGENTS : détection du flux logique
  3. POLISSAGE LLM : DeepSeek pour l'élégance finale (optionnel)

Usage:
  styler = StyleEngine()
  elegant = styler.render(path, question, domain)
"""

import re, math, random, os
from typing import List, Dict, Tuple, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# CORRECTIONS ORTHOGRAPHIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def _cap_first(text: str) -> str:
    """Met en majuscule la première lettre EN PRÉSERVANT les accents."""
    if not text:
        return text
    return text[0].upper() + text[1:]

# Dictionnaire de corrections orthographiques FR (mots sans accents → avec accents)
_ACCENT_FIX = {
    # Articles/prépositions
    'a ': 'à ', ' a ': ' à ', ' a.': ' à.',
    # Mots très fréquents
    'phenomene': 'phénomène', 'phenomenes': 'phénomènes',
    'etape': 'étape', 'etapes': 'étapes',
    'depart': 'départ', 'departs': 'départs',
    'eclairer': 'éclairer', 'eclaire': 'éclaire', 'eclairee': 'éclairée',
    'meme': 'même', 'memes': 'mêmes',
    'revele': 'révèle', 'reveler': 'révéler',
    'realite': 'réalité', 'realites': 'réalités',
    'evidence': 'évidence', 'evident': 'évident',
    'elementaire': 'élémentaire', 'elementaires': 'élémentaires',
    'cote': 'côté', 'cotes': 'côtés',
    'cascade': 'cascade',  # déjà correct
    'intermediaire': 'intermédiaire', 'intermediaires': 'intermédiaires',
    'mecanisme': 'mécanisme', 'mecanismes': 'mécanismes',
    'systeme': 'système', 'systemes': 'systèmes',
    'energie': 'énergie', 'energies': 'énergies',
    'mathematique': 'mathématique', 'mathematiques': 'mathématiques',
    'physique': 'physique',  # déjà correct
    'biologique': 'biologique',  # déjà correct
    'logique': 'logique',  # déjà correct
    'electrique': 'électrique',
    'emotion': 'émotion', 'emotions': 'émotions',
    'experience': 'expérience', 'experiences': 'expériences',
    'essentiel': 'essentiel',
    'principe': 'principe', 'principes': 'principes',
    'consequence': 'conséquence', 'consequences': 'conséquences',
    'definitive': 'définitive',
    'interference': 'interférence', 'interferences': 'interférences',
    'onde': 'onde', 'ondes': 'ondes',
    'lumiere': 'lumière',
    'deplace': 'déplace', 'deplacer': 'déplacer',
    'empeche': 'empêche', 'empecher': 'empêcher',
    'oxygene': 'oxygène',
    'electrique': 'électrique',
    'intimement': 'intimement',
    'reponse': 'réponse', 'reponses': 'réponses',
    'probleme': 'problème', 'problemes': 'problèmes',
    'theorie': 'théorie', 'theories': 'théories',
    'strategie': 'stratégie', 'strategies': 'stratégies',
    'categorie': 'catégorie', 'categories': 'catégories',
    'ethique': 'éthique',
    'economie': 'économie',
    'ecologie': 'écologie',
    'evolution': 'évolution',
    'equation': 'équation', 'equations': 'équations',
    'interet': 'intérêt', 'interets': 'intérêts',
    'etre': 'être',
    'etat': 'état', 'etats': 'états',
    'declenche': 'déclenche', 'declencher': 'déclencher',
    'developpe': 'développe', 'developper': 'développer',
    'differents': 'différents', 'differentes': 'différentes',
    'generale': 'générale', 'general': 'général',
    'particuliere': 'particulière', 'particulier': 'particulier',
    'premiere': 'première', 'premier': 'premier',
    'derniere': 'dernière', 'dernier': 'dernier',
    'maniere': 'manière',
    'tres': 'très',
    'apres': 'après',
    'grace': 'grâce',
    'entre': 'entre',
    'etre humain': 'être humain',
    'etres humains': 'êtres humains',
    'etres vivants': 'êtres vivants',
    'caractere': 'caractère', 'caracteres': 'caractères',
    'methode': 'méthode', 'methodes': 'méthodes',
    'phenomene': 'phénomène',
    'evenement': 'événement', 'evenements': 'événements',
    'region': 'région', 'regions': 'régions',
    'periode': 'période', 'periodes': 'périodes',
    'numero': 'numéro', 'numeros': 'numéros',
    'espece': 'espèce', 'especes': 'espèces',
    'tolerance': 'tolérance',
    'temperature': 'température',
    'parametre': 'paramètre', 'parametres': 'paramètres',
    'diagramme': 'diagramme',
    'programme': 'programme',
    'gramme': 'gramme',
    'telephone': 'téléphone',
    'television': 'télévision',
    'reseau': 'réseau', 'reseaux': 'réseaux',
    'ecole': 'école', 'ecoles': 'écoles',
    'etude': 'étude', 'etudes': 'études',
    'etudie': 'étudie', 'etudier': 'étudier',
    'etranger': 'étranger', 'etrangere': 'étrangère',
    'epoque': 'époque',
    'eglise': 'église',
    'element': 'élément', 'elements': 'éléments',
    'equipe': 'équipe',
    'etablir': 'établir', 'etabli': 'établi',
    'etendue': 'étendue',
    'etincelle': 'étincelle',
    'etoile': 'étoile', 'etoiles': 'étoiles',
    'etrange': 'étrange',
    'etroit': 'étroit',
    'evaluation': 'évaluation',
    'eviter': 'éviter',
    'evolution': 'évolution',
    'examiner': 'examiner',
    'exemple': 'exemple', 'exemples': 'exemples',
    'exercice': 'exercice',
    'existence': 'existence',
    'expliquer': 'expliquer',
    'extreme': 'extrême',
    'heritage': 'héritage',
    'hesiter': 'hésiter',
    'histoire': 'histoire',
    'homme': 'homme', 'hommes': 'hommes',
    'hopital': 'hôpital',
    'hotel': 'hôtel',
    'ile': 'île',
    'illustrer': 'illustrer',
    'important': 'important',
    'indiquer': 'indiquer',
    'influence': 'influence',
    'interieur': 'intérieur',
    'intermediaire': 'intermédiaire',
    'intitule': 'intitulé',
    'inviter': 'inviter',
    'itineraire': 'itinéraire',
    'itineraire': 'itinéraire',
    'relies': 'reliés',
    'lie a': 'lié à', 'liee a': 'liée à',
    'lie au': 'lié au', 'liee au': 'liée au',
    'cree': 'créé', 'creee': 'créée', 'creer': 'créer',
    'agreable': 'agréable',
    'a cote': 'à côté',
    'a travers': 'à travers',
    'a partir': 'à partir',
    'a peu pres': 'à peu près',
    'a nouveau': 'à nouveau',
    'a la fin': 'à la fin',
    'a l inverse': "à l'inverse",
    'a mon avis': 'à mon avis',
    # Majuscules accentuées (apparaissent après capitalize())
    'Eclairer': 'Éclairer', 'Eclaire': 'Éclaire',
    'Etape': 'Étape', 'Etapes': 'Étapes',
    'Etre': 'Être',
    'Etat': 'État', 'Etats': 'États',
    'Evidence': 'Évidence',
    'Elementaire': 'Élémentaire',
    'Ecole': 'École',
    'Etude': 'Étude', 'Etudie': 'Étudie',
    'Etranger': 'Étranger',
    'Epoque': 'Époque',
    'Eglise': 'Église',
    'Element': 'Élément', 'Elements': 'Éléments',
    'Equipe': 'Équipe',
    'Etablir': 'Établir', 'Etabli': 'Établi',
    'Etendue': 'Étendue',
    'Etincelle': 'Étincelle',
    'Etoile': 'Étoile', 'Etoiles': 'Étoiles',
    'Etrange': 'Étrange',
    'Etroit': 'Étroit',
    'Evaluation': 'Évaluation',
    'Eviter': 'Éviter',
    'Evolution': 'Évolution',
    'Examiner': 'Examiner',
    'Exemple': 'Exemple', 'Exemples': 'Exemples',
    'Exercice': 'Exercice',
    'Existence': 'Existence',
    'Expliquer': 'Expliquer',
    'Experience': 'Expérience',
    'Extreme': 'Extrême',
    'Heritage': 'Héritage',
    'Hesiter': 'Hésiter',
    'Hopital': 'Hôpital',
    'Hotel': 'Hôtel',
    'Ile': 'Île',
    'Interieur': 'Intérieur',
    'Realite': 'Réalité',
    'Reponse': 'Réponse',
    'Revele': 'Révèle',
    'Agreable': 'Agréable',
    'A cote': 'À côté',
    'A travers': 'À travers',
    'A partir': 'À partir',
    'A la fin': 'À la fin',
    'Declenche': 'Déclenche',
    'Depart': 'Départ',
    'Definitive': 'Définitive',
    'Developpe': 'Développe',
    'Differents': 'Différents', 'Differentes': 'Différentes',
    'Generale': 'Générale', 'General': 'Général',
}

def _fix_accents(text: str) -> str:
    """Corrige les accents manquants dans un texte français."""
    # Remplacer les mots connus
    for wrong, correct in _ACCENT_FIX.items():
        # Remplacer seulement les mots entiers (pas les sous-chaînes)
        text = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, text)
        # Aussi dans les versions capitalisées
        text = re.sub(r'\b' + re.escape(wrong.capitalize()) + r'\b', correct.capitalize(), text)
    
    # Remplacer "a " par "à " quand c'est une préposition (pas dans "a déjà", "a été")
    text = re.sub(r'\b(a) (le|la|les|l|un|une|des|son|sa|ses|ce|cette|ces|mon|ma|mes|ton|ta|tes|leur|leurs)\b', r'à \2', text)
    
    # "Ce qui nous conduit a :" → "Ce qui nous conduit à :"
    text = re.sub(r'(conduit|mene|aboutit|revient|correspond|appartient)\s+a\b', r'\1 à', text)
    
    # "d un" → "d'un", "d une" → "d'une", "l experience" → "l'expérience"
    text = re.sub(r"\bd un\b", "d'un", text)
    text = re.sub(r"\bd une\b", "d'une", text)
    text = re.sub(r"\bl ([aàeéèêiîoôuùûy])", r"l'\1", text)
    
    return text

# ═══════════════════════════════════════════════════════════════════════════════
# 1. TEMPLATES RICHES PAR DOMAINE
# ═══════════════════════════════════════════════════════════════════════════════

RICH_TEMPLATES = {
    "PHYSIQUE": {
        "single": [
            "{sujet} {relation} {objet}. C'est un principe fondamental de la physique.",
            "En physique, {sujet} {relation} {objet}. Ce phenomene est bien etabli.",
            "Le concept est clair : {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "Pour comprendre ce phenomene, partons du principe que {sujet} {relation} {objet}.",
            "L'explication physique commence par un fait essentiel : {sujet} {relation} {objet}.",
            "Tout commence par une observation fondamentale : {sujet} {relation} {objet}.",
            "Le point de depart est le suivant : {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Ceci implique directement que {sujet} {relation} {objet}.",
            "De ce fait, {sujet} {relation} {objet}.",
            "Par voie de consequence, {sujet} {relation} {objet}.",
            "Ce qui nous conduit a : {sujet} {relation} {objet}.",
            "Et cela signifie que {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Ainsi, par une chaine de causalite physique, {premier_sujet} est intimement lie a {dernier_objet}.",
            "En definitive, {premier_sujet} et {dernier_objet} sont les deux faces d'un meme phenomene.",
            "La boucle est bouclee : {premier_sujet} → {dernier_objet}.",
        ],
    },
    "BIOLOGIE": {
        "single": [
            "{sujet} {relation} {objet}. C'est un mecanisme essentiel du vivant.",
            "En biologie, {sujet} {relation} {objet}. Cette fonction est vitale.",
        ],
        "chain_intro": [
            "Pour saisir ce mecanisme biologique, observons d'abord que {sujet} {relation} {objet}.",
            "Le vivant fonctionne par etapes : d'abord, {sujet} {relation} {objet}.",
            "Partons d'un fait biologique elementaire : {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Ce qui permet alors de {sujet} {relation} {objet}.",
            "Cette etape declenche le processus suivant : {sujet} {relation} {objet}.",
            "Ensuite, {sujet} {relation} {objet}.",
            "Ce mecanisme active a son tour : {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Ainsi, le vivant orchestre une cascade ou {premier_sujet} aboutit a {dernier_objet}.",
            "Ce chemin biologique revele comment {premier_sujet} est essentiel a {dernier_objet}.",
        ],
    },
    "CONSCIENCE": {
        "single": [
            "{sujet} {relation} {objet}. C'est une realite de l'experience humaine.",
            "Du point de vue de la conscience, {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "L'exploration de la conscience commence par ce constat : {sujet} {relation} {objet}.",
            "Pour eclairer cette question, partons de l'evidence que {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Ce qui nous fait prendre conscience que {sujet} {relation} {objet}.",
            "Cela ouvre sur une dimension plus profonde : {sujet} {relation} {objet}.",
            "Cette realisation eclaire a son tour le fait que {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Ainsi, {premier_sujet} et {dernier_objet} sont relies par le fil de la conscience.",
            "L'experience consciente tisse un lien entre {premier_sujet} et {dernier_objet}.",
        ],
    },
    "PHILOSOPHIE": {
        "single": [
            "{sujet} {relation} {objet}. C'est une question qui traverse les siecles.",
            "La philosophie nous enseigne que {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "La reflexion philosophique debute par une interrogation : {sujet} {relation} {objet}.",
            "Les penseurs ont etabli que {sujet} {relation} {objet}. Mais cela souleve une autre question.",
        ],
        "chain_link": [
            "Ce qui nous amene a considerer que {sujet} {relation} {objet}.",
            "Cette idee en implique une autre : {sujet} {relation} {objet}.",
            "La pensee progresse : {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Au terme de cette reflexion, {premier_sujet} apparait comme le fondement de {dernier_objet}.",
            "Ainsi, la sagesse nous revele le lien profond entre {premier_sujet} et {dernier_objet}.",
        ],
    },
    "MATHS": {
        "single": [
            "{sujet} {relation} {objet}. C'est une verite mathematique.",
            "Mathematiquement, {sujet} {relation} {objet}. Cela se demontre rigoureusement.",
        ],
        "chain_intro": [
            "Le raisonnement mathematique s'appuie sur un premier fait : {sujet} {relation} {objet}.",
            "Partons d'une proposition etablie : {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Ce qui implique logiquement que {sujet} {relation} {objet}.",
            "De cette proposition decoule : {sujet} {relation} {objet}.",
            "Le theoreme suivant en resulte : {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Par deduction, {premier_sujet} est mathematiquement lie a {dernier_objet}.",
            "La demonstration est complete : {premier_sujet} ⇒ {dernier_objet}.",
        ],
    },
    "EMOTION": {
        "single": [
            "{sujet} {relation} {objet}. C'est une verite du coeur.",
            "Sur le plan emotionnel, {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "L'emotion nous revele d'abord que {sujet} {relation} {objet}.",
            "Le coeur sait que {sujet} {relation} {objet}. Et cela nous conduit plus loin.",
        ],
        "chain_link": [
            "Ce qui fait resonner en nous que {sujet} {relation} {objet}.",
            "Cette emotion en eveille une autre : {sujet} {relation} {objet}.",
            "Le sentiment s'approfondit : {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Ainsi, {premier_sujet} et {dernier_objet} vibrent sur la meme corde affective.",
            "L'ame humaine relie {premier_sujet} a {dernier_objet} par le fil de l'emotion.",
        ],
    },
    "HISTOIRE": {
        "single": [
            "{sujet} {relation} {objet}. C'est un fait historique avere.",
            "L'histoire nous apprend que {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "Pour comprendre cet enchainement, rappelons d'abord que {sujet} {relation} {objet}.",
            "Le recit historique commence ainsi : {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Cet evenement a entraine que {sujet} {relation} {objet}.",
            "Ce qui a conduit a ce que {sujet} {relation} {objet}.",
            "La suite des evenements nous mene a : {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Ainsi, la chaine historique revele comment {premier_sujet} a abouti a {dernier_objet}.",
            "Le fil de l'histoire tisse un lien entre {premier_sujet} et {dernier_objet}.",
        ],
    },
    "GENERAL": {
        "single": [
            "{sujet} {relation} {objet}. Voila l'essentiel.",
            "On peut affirmer que {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "Pour comprendre, notons d'abord que {sujet} {relation} {objet}.",
            "Le point de depart est simple : {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Ce qui signifie que {sujet} {relation} {objet}.",
            "Par consequent, {sujet} {relation} {objet}.",
            "Et donc, {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "En resume, {premier_sujet} est fondamentalement lie a {dernier_objet}.",
            "Tout cela montre que {premier_sujet} et {dernier_objet} sont connectes.",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MOTEUR DE STYLE
# ═══════════════════════════════════════════════════════════════════════════════

class StyleEngine:
    """
    Transforme un chemin de raisonnement en francais elegant.
    """
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self._used_templates = {}  # pour eviter les repetitions
    
    def render(self, path, question: str, domain: str) -> str:
        """Rend un chemin en langage naturel élégant."""
        if not path:
            return "Aucun chemin de résonance trouvé."
        
        templates = RICH_TEMPLATES.get(domain, RICH_TEMPLATES['GENERAL'])
        
        if len(path) == 1:
            result = self._render_single(path[0], templates)
        else:
            result = self._render_chain(path, templates)
        
        return _fix_accents(result)
    
    def _render_single(self, fact, templates) -> str:
        """Rend un fait unique."""
        s, r, o, sec = fact
        tmpl = random.choice(templates['single'])
        return _fix_accents(tmpl.format(sujet=_cap_first(s), relation=r, objet=o))
    
    def _render_chain(self, path, templates) -> str:
        """Rend une chaîne de raisonnement."""
        sentences = []
        
        # Introduction
        s0, r0, o0, _ = path[0]
        intro_tmpl = random.choice(templates['chain_intro'])
        sentences.append(intro_tmpl.format(sujet=_cap_first(s0), relation=r0, objet=o0))
        
        # Liens intermédiaires
        for i in range(1, len(path)):
            s, r, o, _ = path[i]
            link_tmpl = random.choice(templates['chain_link'])
            sentences.append(link_tmpl.format(sujet=s, relation=r, objet=o))
        
        # Conclusion
        if len(path) >= 2:
            premier_sujet = _cap_first(path[0][0])
            dernier_objet = path[-1][2]
            concl_tmpl = random.choice(templates['chain_conclusion'])
            conclusion = concl_tmpl.format(
                premier_sujet=premier_sujet,
                dernier_objet=dernier_objet
            )
            sentences.append(conclusion)
        
        return _fix_accents(' '.join(sentences))
    
    def polish_with_llm(self, raw_text: str, domain: str) -> str:
        """
        Polissage final par DeepSeek pour une elegance maximale.
        Ne change pas les faits — ameliore uniquement le style.
        """
        if not self.use_llm:
            return raw_text
        
        try:
            import os, sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from llm.router import HarmonicLLM
            llm = HarmonicLLM()
            
            prompt = (
                f"Reecris ce texte en francais elegant et naturel, SANS changer "
                f"les faits ni ajouter d'information. Domaine : {domain}.\n\n"
                f"Texte : {raw_text}\n\n"
                f"Version elegante :"
            )
            resp = llm.generate(prompt, category="creative")
            if resp.content and len(resp.content) > 20:
                return resp.content.strip()
        except Exception:
            pass
        
        return raw_text


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    from harmonic_model import HarmonicModel
    from reasoning_engine import find_paths, detect_domain
    
    print("=" * 60)
    print("STYLE ENGINE — Francais elegant par domaine")
    print("=" * 60)
    
    model = HarmonicModel(use_memory=False)
    styler = StyleEngine()
    
    tests = [
        "pourquoi le coeur pompe le sang",
        "explique la lumiere",
        "qu est ce que la conscience",
        "comment fonctionne la resonance",
        "explique le nombre d or",
        "qu est ce que dieu",
    ]
    
    for q in tests:
        paths = find_paths(model.knowledge_base, q)
        if paths:
            domain = detect_domain(paths[0])
            elegant = styler.render(paths[0], q, domain)
            print(f"\n[{domain}] >> {q}")
            print(f"       << {elegant}")


if __name__ == '__main__':
    demo()
