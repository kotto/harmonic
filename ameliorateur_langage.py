#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Améliorateur de Langage Harmonique
====================================
Améliorations incrémentales pour atteindre une qualité de langage
proche des LLM, tout en gardant 0 paramètre entraînable.

Améliorations :
1. Extraction d'entités nommées (NER sans modèle)
2. Nettoyage intelligent des faits bruts
3. Résolution d'anaphore basique
4. Templates enrichis avec meilleure qualité
5. Post-traitement grammatical (accords)
6. Connecteurs logiques entre faits multiples
7. Reformulation naturelle par substitution

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, re, random
from typing import List, Tuple, Dict, Optional
from collections import Counter

# ==============================================================================
# 1. EXTRACTION D'ENTITÉS NOMMÉES (NER sans modèle)
# ==============================================================================

class ExtracteurEntites:
    """
    Extrait les entités nommées d'un texte sans modèle ML.
    Utilise des règles basées sur les majuscules, les patterns,
    et les connaissances du domaine.
    """
    
    # Patterns pour les types d'entités
    PATTERNS = {
        'personne': [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Prénom Nom
            r'\b[A-Z][a-z]+\b',                 # Nom simple (Einstein, Newton)
        ],
        'valeur_numerique': [
            r'\b\d+[.,]\d+\s*(?:×|x|×)\s*10\^?[-−]?\d+\s*(?:J·s|J/s|J\.s|m/s|km/s|kg|J|Hz|W|K|°C|s|N)\b',  # 6.626×10⁻³⁴ J·s
            r'\b\d+[.,]\d+\s*(?:×|x|×)\s*10\^?[-−]?\d+\b',  # 6.626×10⁻³⁴
            r'\b\d+\s*(?:m/s|km/s)\b',                        # 299 792 458 m/s
            r'\b\d+[.,]\d+\s*(?:J·s|J/s|J\.s|kg|J|Hz|W|K|°C|s|N|m)\b',  # 6.626 J·s
            r'\b\d+[.,]\d+\b',                                    # 299.792
        ],
        'date': [
            r'\b\d{4}\b',                       # 1905, 2024
            r'\b\d+\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b',
        ],
        'formule': [
            r'[A-Z]\d*[A-Za-z]?\d*\s*[=→]\s*[A-Za-z0-9+\-×*/()\s]+',  # E=mc²
            r'\d+[A-Z][A-Za-z]?\d*\s*\+\s*\d+[A-Z][A-Za-z]?\d*',       # 6CO₂ + 6H₂O
        ],
    }
    
    # Noms de scientifiques connus (pour compléter le NER)
    SCIENTIFIQUES_CONNUS = {
        'einstein', 'newton', 'planck', 'darwin', 'curie', 'pasteur',
        'galilée', 'kepler', 'maxwell', 'bohr', 'heisenberg', 'schrödinger',
        'feynman', 'hawking', 'tesla', 'edison', 'bell', 'marconi',
        'mendeleïev', 'lavoisier', 'lemaître', 'hubble', 'watson', 'crick',
        'franklin', 'wegener', 'boltzmann', 'hahn', 'strassmann', 'zwic',
    }
    
    def __init__(self):
        self.compiled_patterns = {
            cat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cat, patterns in self.PATTERNS.items()
        }
    
    def extraire(self, texte: str) -> Dict[str, List[str]]:
        """
        Extrait toutes les entités d'un texte.
        
        Returns:
            Dict avec catégories 'personne', 'valeur_numerique', 'date', 'formule'
        """
        entites = {cat: [] for cat in self.PATTERNS}
        
        for cat, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(texte)
                for m in matches:
                    if isinstance(m, tuple):
                        m = m[0]
                    m = m.strip()
                    if m and m not in entites[cat]:
                        entites[cat].append(m)
        
        # Ajouter les scientifiques connus
        texte_lower = texte.lower()
        for nom in self.SCIENTIFIQUES_CONNUS:
            if nom in texte_lower and nom.capitalize() not in entites['personne']:
                entites['personne'].append(nom.capitalize())
        
        return entites
    
    def extraire_valeur_principale(self, texte: str) -> Optional[str]:
        """Extrait la valeur numérique principale d'un texte."""
        entites = self.extraire(texte)
        if entites['valeur_numerique']:
            # Retourner la plus longue (la plus précise)
            return max(entites['valeur_numerique'], key=len)
        return None
    
    def extraire_personne_principale(self, texte: str) -> Optional[str]:
        """Extrait le scientifique principal d'un texte."""
        entites = self.extraire(texte)
        if entites['personne']:
            # Filtrer les noms de mois et mots communs
            mois = {'janvier','février','mars','avril','mai','juin',
                    'juillet','août','septembre','octobre','novembre','décembre'}
            personnes = [p for p in entites['personne']
                        if p.lower() not in mois and len(p) > 2]
            if personnes:
                return personnes[0]
        return None
    
    def extraire_date_principale(self, texte: str) -> Optional[str]:
        """Extrait la date principale d'un texte."""
        entites = self.extraire(texte)
        if entites['date']:
            return entites['date'][0]
        return None


# ==============================================================================
# 2. NETTOYAGE INTELLIGENT DES FAITS
# ==============================================================================

class NettoyeurFait:
    """
    Nettoie et résume un fait brut en une forme concise.
    
    Exemple :
    Entrée : "Question: Quelle est la capitale de la France ?  Reponse: paris"
    Sortie : "Paris est la capitale de la France"
    """
    
    # Patterns Q/R à nettoyer
    PATTERNS_QR = [
        re.compile(r'question\s*:\s*([^?]+\?)\s*r[eé]ponse\s*:\s*(.+)', re.IGNORECASE),
        re.compile(r'q\s*:\s*([^?]+\?)\s*r\s*:\s*(.+)', re.IGNORECASE),
    ]
    
    # Mots inutiles à supprimer
    MOTS_VIDES = {'le', 'la', 'les', 'des', 'une', 'un', 'de', 'du', 'et', 'est',
                  'en', 'au', 'aux', 'pour', 'par', 'sur', 'dans', 'avec', 'sans'}
    
    def nettoyer(self, texte: str) -> str:
        """Nettoie un fait brut."""
        # 1. Détecter et nettoyer le format Q/R
        for pattern in self.PATTERNS_QR:
            match = pattern.search(texte)
            if match:
                question = match.group(1).strip()
                reponse = match.group(2).strip()
                # Reformuler en phrase déclarative
                return self._qr_vers_phrase(question, reponse)
        
        # 2. Nettoyer les préfixes communs
        prefixes = [
            "reponse:", "réponse:", "reponse :", "réponse :",
            "information sur ", "information: ", "info: ",
        ]
        for prefix in prefixes:
            if texte.lower().startswith(prefix):
                texte = texte[len(prefix):].strip()
        
        # 3. Garder la première phrase (la plus informative)
        phrases = texte.split(".")
        if phrases:
            texte = phrases[0].strip() + ("." if len(phrases[0]) > 10 else "")
        
        return texte
    
    def _qr_vers_phrase(self, question: str, reponse: str) -> str:
        """Convertit une paire Q/R en phrase déclarative."""
        # Cas : "Quelle est la capitale de X ?" → "La capitale de X est Y"
        q = question.lower().strip("?")
        
        if "quelle est" in q or "quel est" in q:
            sujet = q.replace("quelle est la ", "").replace("quelle est le ", "")
            sujet = sujet.replace("quel est la ", "").replace("quel est le ", "")
            sujet = sujet.replace("quelle est l'", "l'").replace("quel est l'", "l'")
            return f"La {sujet} est {reponse}."
        
        if "qui" in q and ("a découvert" in q or "a inventé" in q):
            return f"{reponse.capitalize()} a {q.split('qui a ')[1] if 'qui a ' in q else q}."
        
        # Fallback
        return reponse.capitalize() + "."


# ==============================================================================
# 3. RÉSOLUTION D'ANAPHORE BASIQUE
# ==============================================================================

class ResolveurAnaphore:
    """
    Remplace les pronoms et références par leurs antécédents.
    """
    
    REMPLACEMENTS = {
        'il': None, 'elle': None, 'ils': None, 'elles': None,
        'cette': None, 'ce': None, 'cet': None, 'cela': None,
        'celui-ci': None, 'celle-ci': None, 'ceux-ci': None,
    }
    
    def resoudre(self, texte: str, contexte: str) -> str:
        """
        Remplace les pronoms par le sujet principal du contexte.
        
        Pour simplifier : on remplace "il/elle" par le premier nom propre
        ou le sujet principal trouvé dans le contexte.
        """
        from extracteur_entites import ExtracteurEntites
        
        extracteur = ExtracteurEntites()
        
        # Trouver le sujet principal dans le contexte
        sujet = None
        personne = extracteur.extraire_personne_principale(contexte)
        if personne:
            sujet = personne
        
        if not sujet:
            # Chercher le premier nom commun après un article
            match = re.search(r'\b(?:le|la|les|l\')\s+(\w+)', contexte)
            if match:
                sujet = match.group(1)
        
        if sujet:
            # Remplacer les pronoms
            for pronom in ['il', 'elle', 'ils', 'elles']:
                texte = re.sub(r'\b' + pronom + r'\b', sujet, texte, flags=re.IGNORECASE)
        
        return texte


# ==============================================================================
# 4. TEMPLATES ENRICHIS
# ==============================================================================

class TemplatesEnrichis:
    """
    Templates grammaticaux améliorés avec :
    - Plus de variantes naturelles
    - Gestion correcte des entités (personne vs concept)
    - Connecteurs logiques
    """
    
    TEMPLATES = {
        "definition": [
            "{sujet} est {reponse}.",
            "{sujet} désigne {reponse}.",
            "On appelle {sujet} {reponse}.",
            "Le terme {sujet} fait référence à {reponse}.",
            "{sujet} correspond à {reponse}.",
            "Par {sujet}, on entend {reponse}.",
        ],
        "personne_decouverte": [
            "C'est {personne} qui a découvert {sujet}.",
            "{sujet} a été découvert par {personne}.",
            "La découverte de {sujet} est attribuée à {personne}.",
            "{personne} est le scientifique à l'origine de la découverte de {sujet}.",
            "On doit la découverte de {sujet} à {personne}.",
            "{personne} a mis en évidence {sujet}.",
        ],
        "personne_est": [
            "{personne} est {reponse}.",
            "{personne} était {reponse}.",
            "Connu comme {reponse}, {personne} a marqué l'histoire des sciences.",
        ],
        "explication": [
            "{sujet} fonctionne de la manière suivante : {reponse}.",
            "Le principe de {sujet} repose sur {reponse}.",
            "{sujet} consiste en {reponse}.",
            "Pour comprendre {sujet}, il faut savoir que {reponse}.",
            "{sujet} est le processus par lequel {reponse}.",
            "Le mécanisme de {sujet} implique {reponse}.",
        ],
        "valeur": [
            "{sujet} vaut exactement {valeur}.",
            "La valeur de {sujet} est {valeur}.",
            "{sujet} est égal à {valeur}.",
            "On mesure {sujet} comme étant {valeur}.",
            "{sujet} a pour valeur {valeur}.",
            "La mesure de {sujet} donne {valeur}.",
        ],
        "date_evenement": [
            "{sujet} s'est produit en {date}.",
            "{sujet} date de {date}.",
            "C'est en {date} que {sujet} a eu lieu.",
            "{date} est la date clé de {sujet}.",
            "{sujet} remonte à {date}.",
        ],
        "contexte_enrichi": [
            "{phrase_principale}. {contexte}.",
            "{phrase_principale}. En {date}, {contexte}.",
            "{phrase_principale}. {personne} {contexte}.",
        ],
    }
    
    def choisir(self, type_template: str) -> str:
        """Choisit un template aléatoire du type donné."""
        ts = self.TEMPLATES.get(type_template, self.TEMPLATES["definition"])
        return random.choice(ts)
    
    def formuler(self, type_template: str, **kwargs) -> str:
        """Formule une réponse avec le template choisi."""
        template = self.choisir(type_template)
        try:
            return template.format(**kwargs)
        except KeyError:
            # Fallback avec les clés disponibles
            return template.format(
                sujet=kwargs.get('sujet', 'ce sujet'),
                reponse=kwargs.get('reponse', kwargs.get('valeur', 'information indisponible')),
                personne=kwargs.get('personne', 'un scientifique'),
                valeur=kwargs.get('valeur', kwargs.get('reponse', 'valeur inconnue')),
                date=kwargs.get('date', 'une date inconnue'),
                contexte=kwargs.get('contexte', ''),
                phrase_principale=kwargs.get('phrase_principale', ''),
            )


# ==============================================================================
# 5. POST-TRAITEMENT GRAMMATICAL
# ==============================================================================

class PostTraitementGrammatical:
    """
    Corrections grammaticales de base.
    """
    
    # Accords de base
    ACCORDS = {
        'le ': {'a': "l'a", 'é': "l'é", 'i': "l'i", 'o': "l'o", 'u': "l'u",
                'h': "l'h", 'e': "l'e", 'â': "l'â", 'ê': "l'ê", 'î': "l'î"},
        'la ': {'a': "l'a", 'é': "l'é", 'i': "l'i", 'o': "l'o", 'u': "l'u",
                'h': "l'h", 'e': "l'e", 'â': "l'â", 'ê': "l'ê", 'î': "l'î"},
        'de le': 'du',
        'de les': 'des',
        'à le': 'au',
        'à les': 'aux',
        'ce est': "c'est",
        'que il': "qu'il",
        'que elle': "qu'elle",
        'si il': "s'il",
        'ne est': "n'est",
        'je ai': "j'ai",
    }
    
    DOUBLES_ESPACES = re.compile(r'\s{2,}')
    PONCTUATION_ESPACE = re.compile(r'\s+([.,;:!?])')
    
    def corriger(self, texte: str) -> str:
        """Applique toutes les corrections grammaticales."""
        # 1. Contractions
        for ancien, nouveau in self.ACCORDS.items():
            if isinstance(nouveau, dict):
                # Contractions contextuelles : "le a" -> "l'a"
                for premiere_lettre, contraction in nouveau.items():
                    texte = texte.replace(ancien + premiere_lettre, contraction + premiere_lettre[1:] if len(premiere_lettre) > 1 else contraction)
            else:
                texte = texte.replace(ancien, nouveau)
        
        # 2. Majuscule en début de phrase
        if texte and texte[0].islower():
            texte = texte[0].upper() + texte[1:]
        
        # 3. Nettoyer les doubles espaces
        texte = self.DOUBLES_ESPACES.sub(' ', texte)
        
        # 4. Nettoyer les espaces avant ponctuation
        texte = self.PONCTUATION_ESPACE.sub(r'\1', texte)
        
        # 5. S'assurer qu'il y a un point final
        texte = texte.strip()
        if texte and not texte[-1] in '.!?':
            texte += '.'
        
        # 6. Éviter les double-points
        texte = texte.replace('..', '.')
        
        return texte


# ==============================================================================
# 6. CONNECTEURS LOGIQUES
# ==============================================================================

class ConnecteursLogiques:
    """
    Ajoute des connecteurs logiques entre les faits pour des réponses
    multi-phrases naturelles.
    """
    
    CONNECTEURS_ADDITION = [
        "De plus, ", "Par ailleurs, ", "En outre, ",
        "À noter également que ", "Il faut aussi savoir que ",
    ]
    
    CONNECTEURS_PRECISION = [
        "Plus précisément, ", "En d'autres termes, ",
        "C'est-à-dire que ", "Concrètement, ",
    ]
    
    CONNECTEURS_CONSEQUENCE = [
        "Ainsi, ", "Par conséquent, ", "De ce fait, ",
        "C'est pourquoi ", "Il en résulte que ",
    ]
    
    def combiner_faits(self, faits: List[str]) -> str:
        """
        Combine plusieurs faits en un paragraphe cohérent.
        
        Args:
            faits: liste de phrases factuelles
        
        Returns:
            Paragraphe avec connecteurs logiques
        """
        if len(faits) == 1:
            return faits[0]
        
        phrases = []
        
        # Première phrase : directe
        phrases.append(faits[0].strip())
        
        # Phrases suivantes : avec connecteur
        for i, fait in enumerate(faits[1:], 1):
            fait = fait.strip()
            if not fait:
                continue
            
            # Choisir le type de connecteur selon la position
            if i == 1:
                connecteur = random.choice(self.CONNECTEURS_ADDITION)
            elif i == len(faits) - 1:
                connecteur = random.choice(self.CONNECTEURS_PRECISION)
            else:
                connecteur = random.choice(self.CONNECTEURS_ADDITION)
            
            # Mettre en minuscule la première lettre après le connecteur
            fait_lower = fait[0].lower() + fait[1:] if fait else fait
            phrases.append(connecteur + fait_lower)
        
        return ' '.join(phrases)


# ==============================================================================
# GÉNÉRATEUR DE LANGAGE AMÉLIORÉ
# ==============================================================================

class GenerateurLangageAmeliore:
    """
    Générateur de langage de qualité LLM.
    
    Pipeline complet :
    1. Extraction NER (personne, valeur, date)
    2. Nettoyage intelligent du fait
    3. Choix du template adapté au type d'entités
    4. Formulation avec le template
    5. Post-traitement grammatical
    6. Ajout de connecteurs si plusieurs faits
    """
    
    def __init__(self):
        self.ner = ExtracteurEntites()
        self.nettoyeur = NettoyeurFait()
        self.templates = TemplatesEnrichis()
        self.grammaire = PostTraitementGrammatical()
        self.connecteurs = ConnecteursLogiques()
    
    def formuler(self, question: str, faits: List[str]) -> str:
        """
        Génère une réponse de qualité LLM à partir de faits bruts.
        
        Args:
            question: la question posée
            faits: liste de textes factuels (top-3 de l'hologramme)
        
        Returns:
            Réponse en langage naturel
        """
        if not faits:
            return "Je ne dispose pas d'informations suffisantes pour répondre à cette question."
        
        # Nettoyer et analyser le meilleur fait
        fait_principal = self.nettoyeur.nettoyer(faits[0])
        
        # Extraire les entités du fait
        entites_fait = self.ner.extraire(fait_principal)
        personne = self.ner.extraire_personne_principale(fait_principal) or \
                   self.ner.extraire_personne_principale(' '.join(faits))
        valeur = self.ner.extraire_valeur_principale(fait_principal) or \
                 self.ner.extraire_valeur_principale(' '.join(faits))
        date = self.ner.extraire_date_principale(fait_principal) or \
               self.ner.extraire_date_principale(' '.join(faits))
        
        # Extraire le sujet de la question
        sujet = self._extraire_sujet(question)
        
        # === DÉTERMINER LE TYPE DE RÉPONSE ===
        q_lower = question.lower()
        
        # Cas 1 : Question sur une personne
        if any(m in q_lower for m in ['qui est', 'qui était', 'qui a']):
            if personne and valeur:
                reponse = self.templates.formuler("personne_decouverte",
                    sujet=sujet, personne=personne, valeur=valeur)
            elif personne:
                reponse = self.templates.formuler("personne_est",
                    personne=personne, reponse=fait_principal)
            else:
                reponse = fait_principal
        
        # Cas 2 : Question sur une valeur
        elif any(m in q_lower for m in ['quelle est', 'quel est', 'valeur', 'vitesse', 'constante']):
            if valeur:
                reponse = self.templates.formuler("valeur",
                    sujet=sujet, valeur=valeur)
            else:
                reponse = self.templates.formuler("valeur",
                    sujet=sujet, valeur=fait_principal)
        
        # Cas 3 : Question sur un événement/découverte
        elif any(m in q_lower for m in ['quand', 'date', 'année', 'siècle']):
            if date:
                reponse = self.templates.formuler("date_evenement",
                    sujet=sujet, date=date)
            else:
                reponse = fait_principal
        
        # Cas 4 : Question d'explication
        elif any(m in q_lower for m in ['comment', 'pourquoi', 'fonctionne', 'marche']):
            reponse = self.templates.formuler("explication",
                sujet=sujet, reponse=fait_principal)
        
        # Cas 5 : Définition
        elif any(m in q_lower for m in ["qu'est-ce", "c'est quoi", "définition"]):
            reponse = self.templates.formuler("definition",
                sujet=sujet, reponse=fait_principal)
        
        # Cas 6 : Question générale
        else:
            reponse = fait_principal
        
        # === ENRICHISSEMENT MULTI-FAITS ===
        if len(faits) > 1:
            fait_secondaire = self.nettoyeur.nettoyer(faits[1])
            if len(fait_secondaire) > 20:
                # Ajouter un contexte enrichi
                personne_ctx = personne if personne else ''
                date_ctx = date if date else ''
                contexte = fait_secondaire
                
                if personne_ctx or date_ctx:
                    reponse = self.templates.formuler("contexte_enrichi",
                        phrase_principale=reponse, contexte=contexte,
                        personne=personne_ctx, date=date_ctx)
        
        # === POST-TRAITEMENT ===
        reponse = self.grammaire.corriger(reponse)
        
        # === CONNECTEURS POUR FAITS MULTIPLES ===
        if len(faits) > 1:
            autres_faits = [self.nettoyeur.nettoyer(f) for f in faits[1:]]
            autres_faits = [f for f in autres_faits if len(f) > 20 and f != reponse[:len(f)]]
            if autres_faits:
                reponse = self.connecteurs.combiner_faits([reponse] + autres_faits[:1])
        
        return reponse
    
    def _extraire_sujet(self, question: str) -> str:
        """Extrait le sujet principal de la question."""
        q = question.lower()
        
        # Patterns de nettoyage
        nettoyages = [
            "quelle est la valeur de ", "quelle est la ", "quel est le ", "quel est l'",
            "quelle est l'", "quel est ", "quelle est ",
            "qui a découvert ", "qui a inventé ", "qui est ", "qui était ",
            "comment fonctionne ", "comment marche ", "comment ",
            "qu'est-ce que ", "qu'est-ce qu'", "c'est quoi ",
            "pourquoi ", "explique ", "décris ",
        ]
        
        sujet = q
        for pattern in nettoyages:
            if sujet.startswith(pattern):
                sujet = sujet[len(pattern):]
                break
        
        # Nettoyer les articles
        for art in ["la ", "le ", "l'", "une ", "un ", "des ", "les "]:
            if sujet.startswith(art):
                sujet = sujet[len(art):]
                break
        
        sujet = sujet.strip()
        return sujet[0].upper() + sujet[1:] if sujet else "ce sujet"


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
def demo():
    """Démonstration du générateur amélioré."""
    print("=" * 60)
    print("GÉNÉRATEUR DE LANGAGE AMÉLIORÉ (Qualité LLM)")
    print("=" * 60)
    print()
    
    generateur = GenerateurLangageAmeliore()
    
    tests = [
        ("quelle est la constante de Planck",
         ["La constante de Planck h = 6.626×10⁻³⁴ J·s.",
          "Max Planck a introduit le quantum d'action en 1900."]),
        
        ("qui a découvert la relativité",
         ["Einstein a publié la relativité restreinte en 1905 (E=mc²) et la relativité générale en 1915.",
          "La relativité générale décrit la gravité comme courbure de l'espace-temps."]),
        
        ("comment fonctionne la photosynthèse",
         ["La photosynthèse : 6 CO₂ + 6 H₂O + lumière → C₆H₁₂O₆ + 6 O₂.",
          "Les plantes convertissent l'énergie solaire en énergie chimique."]),
        
        ("quelle est la vitesse de la lumière",
         ["La vitesse de la lumière dans le vide est 299 792 458 m/s.",
          "C'est une constante fondamentale de la physique."]),
        
        ("qu'est-ce que le Big Bang",
         ["Le Big Bang s'est produit il y a 13.8 milliards d'années.",
          "La théorie du Big Bang a été proposée par Georges Lemaître en 1927."]),
        
        ("qui est Albert Einstein",
         ["Albert Einstein (1879-1955) était un physicien théoricien.",
          "Il a reçu le prix Nobel de physique en 1921 pour l'effet photoélectrique."]),
    ]
    
    print("Tests de génération :")
    print()
    
    for question, faits in tests:
        print(f"  ❓ {question}")
        reponse = generateur.formuler(question, faits)
        print(f"  💬 {reponse}")
        print()
    
    print("=" * 60)
    print("✅ TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    demo()