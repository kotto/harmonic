#!/usr/bin/env python3
"""
Wave Styler — Synthèse Rédactionnelle Ondulatoire
===================================================
Ferme le « gap stylistique » entre ULM et les LLMs.

PRINCIPE :
  Les faits bruts (sujet, relation, objet) sont des ψ_facts.
  Une belle phrase est un ψ_phrase = Σ ψ_facts ⊛ ψ_structure.
  
  La sélection de structure est guidée par :
    1. RÉSONANCE avec ψ_question (registre adapté)
    2. QUADRATURE DE PHASE (anti-répétition)
    3. SUPERPOSITION (fusion des faits, pas liste)
    4. COHÉRENCE (pronoms, anaphores)

OPÉRATIONS :
  Au lieu de "Sujet relation objet. De plus, Sujet2 relation2 objet2."
  → "Le/La [sujet], [subordonnée], [verbe] [objet]. [Pronom] [suite]."

USAGE :
  from wave_styler import WaveStyler
  styler = WaveStyler(encoder)
  reponse = styler.render(facts, question)
"""

import math
import random
import re
import numpy as np
from typing import List, Tuple, Optional

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════
# BASES LINGUISTIQUES (déterministes, pas apprises)
# ═══════════════════════════════════════════════════════════════════

# Pronoms sujets pour éviter la répétition
_PRONOUNS = {
    'il': 'il', 'elle': 'elle', 'ils': 'ils', 'elles': 'elles',
    'ce': 'ce', 'cela': 'cela', 'ce dernier': 'ce dernier',
    'cette dernière': 'cette dernière',
}

# Articles définis (accord genre/nombre)
_ARTICLES = {
    'le': 'le', 'la': 'la', 'les': 'les', "l'": "l'",
}

# Prépositions de lieu/temps pour les subordonnées
_PREPOSITIONS = [
    'qui', 'que', 'dont', 'auquel', 'duquel',
    'dans lequel', 'par lequel', 'pour lequel',
]

# Connecteurs logiques enrichis (classés par fonction)
_CONNECTORS = {
    'addition': [
        "De plus, ", "Par ailleurs, ", "Également, ",
        "Il convient aussi de noter que ", "À cela s'ajoute le fait que ",
    ],
    'consequence': [
        "Il en résulte que ", "Par conséquent, ", "Ainsi, ",
        "De là découle que ", "Ce qui implique que ",
    ],
    'opposition': [
        "Cependant, ", "Néanmoins, ", "En revanche, ",
        "Toutefois, ", "Pourtant, ",
    ],
    'precision': [
        "Plus précisément, ", "En d'autres termes, ", "Concrètement, ",
        "C'est-à-dire que ", "À savoir : ",
    ],
    'conclusion': [
        "En définitive, ", "Pour résumer, ", "En somme, ",
        "Finalement, ", "Au total, ",
    ],
}

# ═══════════════════════════════════════════════════════════════════
# CORRECTIONS ORTHOGRAPHIQUES (accentuation automatique)
# ═══════════════════════════════════════════════════════════════════

_ACCENTS_MAP = {
    # Uniquement les mots sans accent → avec accent (pas de règle ' a ')
    'deja': 'déjà', 'tres': 'très', 'pres': 'près', 'apres': 'après', 'des': 'dès',
    'lumiere': 'lumière', 'oxygene': 'oxygène', 'energie': 'énergie',
    'theorie': 'théorie', 'theories': 'théories',
    'systeme': 'système', 'systemes': 'systèmes',
    'phenomene': 'phénomène', 'phenomenes': 'phénomènes',
    'electricite': 'électricité', 'electrique': 'électrique',
    'electromagnetique': 'électromagnétique',
    'electron': 'électron', 'electrons': 'électrons',
    'emission': 'émission', 'element': 'élément', 'elements': 'éléments',
    'reaction': 'réaction', 'reactions': 'réactions',
    'equation': 'équation', 'equations': 'équations',
    'evolution': 'évolution', 'revolution': 'révolution',
    'cree': 'crée', 'creee': 'créée', 'crees': 'créés',
    'croit': 'croît', 'decroit': 'décroît',
    'interet': 'intérêt', 'interets': 'intérêts',
    'molecule': 'molécule', 'molecules': 'molécules',
    'nucleaire': 'nucléaire', 'nucleaires': 'nucléaires',
    'atome': 'atome', 'atomes': 'atomes',
    'mathematique': 'mathématique', 'mathematiques': 'mathématiques',
    'biologique': 'biologique', 'chimique': 'chimique',
    'physique': 'physique', 'logique': 'logique',
    'realite': 'réalité', 'realites': 'réalités',
    'etre': 'être', 'etat': 'état', 'etats': 'états',
    'etape': 'étape', 'etapes': 'étapes',
    'probleme': 'problème', 'problemes': 'problèmes',
    'reponse': 'réponse', 'reponses': 'réponses',
    'meme': 'même', 'memes': 'mêmes',
    'principe': 'principe', 'principes': 'principes',
    'experience': 'expérience', 'experiences': 'expériences',
    'developpe': 'développe', 'developpee': 'développée',
    'developpement': 'développement',
    'genetique': 'génétique', 'genetiques': 'génétiques',
    'acide': 'acide', 'acides': 'acides',
    'desoxyribonucleique': 'désoxyribonucléique',
    'mecanisme': 'mécanisme', 'mecanismes': 'mécanismes',
    'mecanique': 'mécanique',
    'ecologie': 'écologie', 'economie': 'économie',
    'ethique': 'éthique', 'esthetique': 'esthétique',
    'strategie': 'stratégie', 'strategies': 'stratégies',
    'categorie': 'catégorie', 'categories': 'catégories',
    'definition': 'définition', 'definitions': 'définitions',
    'premiere': 'première', 'deuxieme': 'deuxième', 'troisieme': 'troisième',
    'different': 'différent', 'differents': 'différents', 'differente': 'différente',
    'consequence': 'conséquence', 'consequences': 'conséquences',
    'interference': 'interférence', 'interferences': 'interférences',
    'resonance': 'résonance', 'resonances': 'résonances',
    'coherence': 'cohérence', 'emerge': 'émerge', 'emergent': 'émergent',
    'elegant': 'élégant', 'elegante': 'élégante',
    'intermediaire': 'intermédiaire', 'intermediaires': 'intermédiaires',
    'temperature': 'température', 'temperatures': 'températures',
    'matiere': 'matière', 'matieres': 'matières',
    'particule': 'particule', 'particules': 'particules',
    'frequence': 'fréquence', 'frequences': 'fréquences',
    'onde': 'onde', 'ondes': 'ondes',
    'espece': 'espèce', 'especes': 'espèces',
    'extremite': 'extrémité', 'extremites': 'extrémités',
    'equilibre': 'équilibre', 'equilibres': 'équilibres',
    'regulierement': 'régulièrement',
    'particulierement': 'particulièrement',
    'egalement': 'également',
    'tres': 'très', 'pres': 'près', 'apres': 'après', 'des': 'dès',
}

def apply_accents(text: str) -> str:
    """Applique les corrections d'accents à un texte."""
    result = text
    for k, v in _ACCENTS_MAP.items():
        result = result.replace(k, v)
    # Correction des apostrophes cassées (avec espace avant)
    result = re.sub(r'\bl a\b', "l'a", result)
    result = re.sub(r'\bd un\b', "d'un", result)
    result = re.sub(r'\bs est\b', "s'est", result)
    result = re.sub(r'\bn a\b', "n'a", result)
    result = re.sub(r'\bc est\b', "c'est", result)
    return result


# ═══════════════════════════════════════════════════════════════════
# LE STYLER ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════

class WaveStyler:
    """
    Transforme des faits bruts en français naturel et élégant.
    
    Stratégie :
      1. Détecter le registre de la question (formel/courant/familier)
      2. Pour chaque fait, choisir la meilleure structure
      3. Fusionner les faits connexes (superposition)
      4. Utiliser des pronoms pour la fluidité
      5. Appliquer les accents
    """

    def __init__(self, encoder=None):
        self.encoder = encoder
        self._last_structures = []  # anti-répétition
        self._used_pronouns = set()

    # ─── REGISTRE ───────────────────────────────────────────────

    def detect_register(self, question: str) -> str:
        """
        Détecte le registre de la question.
        Returns: 'formel', 'courant', ou 'familier'
        """
        q = question.lower().strip()
        
        familier = ['c est quoi', 'ca', 'ça', 'truc', 'machin', 'ouais',
                      'genre', 'quoi', 'dis moi', 'donne moi']
        formel = ['définissez', 'expliquez', 'décrivez', 'analysez',
                   'comparez', 'énumérez', 'détaillez',
                   'pourriez-vous', 'veuillez', 'auriez-vous',
                   'define', 'explain', 'describe', 'analyze', 'compare']
        
        score_familier = sum(1 for w in familier if w in q)
        score_formel = sum(1 for w in formel if w in q)
        
        if score_formel > score_familier:
            return 'formel'
        if score_familier > 0:
            return 'familier'
        return 'courant'

    # ─── STRUCTURES ─────────────────────────────────────────────

    STRUCTURES = {
        'formel': {
            'simple': [
                "Il convient de noter que {s} {r} {o}.",
                "On notera que {s} {r} {o}.",
                "Rappelons que {s} {r} {o}.",
            ],
            'subordonnee': [
                "{s_cap}, qui {r} {o}, constitue un élément fondamental.",
                "{s_cap}, dont on sait qu'il {r} {o}, mérite attention.",
                "Le fait que {s} {r} {o} est établi.",
            ],
            'connecteur': _CONNECTORS['addition'] + _CONNECTORS['precision'],
        },
        'courant': {
            'simple': [
                "{S} {r} {o}.",
                "{S} a la particularité de {r} {o}.",
                "On peut dire que {s} {r} {o}.",
            ],
            'subordonnee': [
                "{S}, qui {r} {o}, joue un rôle clé.",
                "{S}, dont la fonction est de {r} {o}, est essentiel.",
            ],
            'connecteur': _CONNECTORS['addition'],
        },
        'familier': {
            'simple': [
                "{S} {r} {o}.",
                "En gros, {s} {r} {o}.",
                "Pour faire simple : {s} {r} {o}.",
            ],
            'subordonnee': [
                "{S}, c'est ce qui {r} {o}.",
            ],
            'connecteur': ["Et puis, ", "Aussi, ", "En plus, "],
        },
    }

    # ─── RENDU PRINCIPAL ────────────────────────────────────────

    def render(self, facts: List[Tuple[str, str, str, str]],
               question: str = "", lang: str = 'fr',
               style: str = 'auto', personality: str = 'ka') -> str:
        """
        Transforme une liste de faits en réponse naturelle.

        Args:
            facts: liste de (sujet, relation, objet, secteur)
            question: question originale (pour adapter le registre)
            lang: 'fr' ou 'en'
            style: "auto"|"concise"|"elegant"|"pedagogique"|"chaleureux"
            personality: "ka"|"savant"|"vulgarisateur"|"poete"
        """
        if not facts:
            sujet = question.strip('?.,!;: ')[:80]
            return (f"Je n'ai pas assez d'éléments sur « {sujet} » "
                    f"pour répondre avec confiance.")

        # Déterminer le registre : style explicite > détection auto
        if style != 'auto':
            register = {'concise': 'courant', 'elegant': 'formel', 
                        'pedagogique': 'courant', 'chaleureux': 'familier'}.get(style, 'courant')
        else:
            register = self.detect_register(question) if question else 'courant'
        
        structures = self.STRUCTURES.get(lang, self.STRUCTURES['courant'])

        # Appliquer la personnalité via le choix des connecteurs
        personality_prefix = {
            'ka': '',  # neutre, chaleureux
            'savant': '',  # précis, citations
            'vulgarisateur': 'En termes simples, ',
            'poete': '',  # métaphores
        }.get(personality, '')
        if register not in self.STRUCTURES:
            register = 'courant'
        structures = self.STRUCTURES[register]

        parts = []
        last_subject = ""

        for i, (s, r, o, sec) in enumerate(facts):
            S = s[0].upper() + s[1:] if s else s
            s_lower = s.lower() if s else s

            # Premier fait : structure complète
            if i == 0:
                # 50% chance d'utiliser une subordonnée si le fait s'y prête
                if len(s) > 3 and len(o) > 3 and random.random() < 0.5:
                    template = random.choice(structures.get('subordonnée',
                                            structures['simple']))
                else:
                    template = random.choice(structures['simple'])

                rendered = template.format(s=s_lower, S=S, s_cap=S, r=r, o=o)
                parts.append(rendered)
                last_subject = s_lower

            # Faits suivants : connecteur + pronom ou répétition
            else:
                connectors = structures.get('connecteur', _CONNECTORS['addition'])
                
                # Éviter de répéter le même connecteur
                available = [c for c in connectors if c not in self._last_structures[-3:]]
                if not available:
                    available = connectors
                connector = random.choice(available)
                self._last_structures.append(connector)
                if len(self._last_structures) > 10:
                    self._last_structures = self._last_structures[-5:]

                # Décider : pronom ou répétition ?
                if s_lower == last_subject:
                    # Même sujet → utiliser un pronom
                    pronoun = 'elle' if s_lower.endswith('e') else 'il'
                    rendered = f"{connector}{pronoun} {r} {o}."
                else:
                    # Sujet différent → utiliser le sujet normal
                    template = random.choice(structures['simple'])
                    rendered = f"{connector}{template.format(s=s_lower, s_cap=s_cap, r=r, o=o)}"
                    # Enlever le connecteur en double si le template en a déjà
                    if connector in rendered:
                        rendered = rendered.replace(connector, '', 1)

                parts.append(rendered)
                last_subject = s_lower

        # Assembler
        text = ' '.join(parts)

        # Appliquer la personnalité
        if personality_prefix:
            # Ajouter le préfixe de personnalité au début
            text = personality_prefix + text[0].lower() + text[1:]

        # Appliquer le style
        if style == 'concise':
            # Garder seulement la première phrase
            sentences = re.split(r'(?<=[.!?])\s+', text)
            text = sentences[0] if sentences else text
        elif style == 'pedagogique':
            # Ajouter une explication si un seul fait
            if len(facts) == 1:
                text += " C'est un concept important à retenir."
        elif style == 'chaleureux':
            # Terminer par une note personnelle
            if not text.endswith('?'):
                text = text.rstrip('.') + '. Je reste à votre écoute pour approfondir.'

        # Appliquer les accents
        text = apply_accents(text)

        # Nettoyer les artefacts
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s([.,!?;:])', r'\1', text)
        text = text.replace(' .', '.').replace(' ,', ',')

        return text


# ═══════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════

def demo():
    """Démonstration du WaveStyler."""
    print("=" * 60)
    print("WAVE STYLER — Synthèse Rédactionnelle Ondulatoire")
    print("=" * 60)

    styler = WaveStyler()

    test_facts = [
        ("la photosynthèse", "produit", "de l'oxygène", "BIOLOGIE"),
        ("la photosynthèse", "utilise", "la lumière du soleil", "BIOLOGIE"),
        ("la photosynthèse", "est", "le processus par lequel les plantes convertissent la lumière en énergie", "BIOLOGIE"),
    ]

    test_questions = [
        "explique la photosynthèse",
        "c'est quoi la photosynthèse ?",
        "Définissez la photosynthèse et ses implications.",
    ]

    for q in test_questions:
        print(f"\nQ: {q}")
        result = styler.render(test_facts, q)
        print(f"R: {result}")


if __name__ == '__main__':
    demo()
