#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assembleur de Phrases — Grammaire Générative Appliquée
========================================================
Inspiré de l'apprentissage du langage chez l'enfant :
- Structures grammaticales abstraites (slots vides)
- Remplissage dynamique à partir des faits extraits
- 50 règles de transformation (pas de réseau de neurones)
- Post-traitement grammatical complet

Une phrase est une structure à slots :
  [DÉTERMINANT] [SUJET] [VERBE] [COMPLÉMENT] [CONNECTEUR] [CONtexte].

Le système apprend à remplir ces slots à partir des faits bruts
du moteur de recherche, puis post-traite le résultat pour
produire un français naturel et fluide.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import re

# ================================
# ANALYSEUR SYNTAXIQUE DE FAIT
# ================================

class AnalyseurFait:
    """
    Extrait les composants syntaxiques d'un fait brut :
    - sujet   : de quoi parle le fait
    - verbe   : action ou relation
    - valeur  : mesure, quantité, découverte
    - contexte: date, personne, lieu associé
    """

    # Patterns verbe-valeur
    PATTERNS_VERBE_VALEUR = [
        (r'^(.+?)\s+(est|vaut|égale?|a pour valeur|correspond à|désigne|consiste en|fonctionne ainsi)\s+(.+)$', 'definition'),
        (r'^(.+?)\s+(a\s+(?:découvert|inventé|publié|formulé|introduit|mis en évidence|proposé))\s+(.+)$', 'decouverte'),
        (r'^(.+?)\s+(s\'est produit|a eu lieu|a débuté|a commencé|date|remonte)\s+(.+)$', 'evenement'),
        (r'^(.+?)\s*:\s*(.+)$', 'definition_courte'),
    ]

    def analyser(self, fait_brut: str) -> dict:
        """
        Analyse un fait brut et retourne ses composants syntaxiques.

        Returns:
            {
                'sujet': str,
                'verbe': str,
                'valeur': str,
                'personne': str|None,
                'date': str|None,
                'type': str  # 'definition', 'decouverte', 'evenement', 'definition_courte'
            }
        """
        fait = fait_brut.strip().rstrip('.')
        resultat = {
            'sujet': '',
            'verbe': 'est',
            'valeur': '',
            'personne': None,
            'date': None,
            'type': 'definition',
        }

        # Essayer chaque pattern
        for pattern, type_fait in self.PATTERNS_VERBE_VALEUR:
            m = re.match(pattern, fait, re.IGNORECASE)
            if m:
                sujet = m.group(1).strip()
                groupes = m.groups()
                if len(groupes) >= 3:
                    verbe = groupes[1].strip().lower()
                    valeur = groupes[2].strip()
                else:
                    # Pattern à 2 groupes (definition_courte)
                    verbe = 'est'
                    valeur = groupes[1].strip()

                # Normaliser le sujet (première lettre majuscule)
                sujet = sujet[0].upper() + sujet[1:] if sujet else sujet

                resultat['sujet'] = sujet
                resultat['verbe'] = self._normaliser_verbe(verbe)
                resultat['valeur'] = valeur
                resultat['type'] = type_fait

                # Extraire la date si présente dans la valeur
                date = self._extraire_date(valeur)
                if date:
                    resultat['date'] = date
                    # Nettoyer la date de la valeur
                    resultat['valeur'] = self._nettoyer_date(valeur, date)

                # Extraire une personne si présente dans la valeur
                personne = self._extraire_personne(valeur)
                if personne:
                    resultat['personne'] = personne

                break

        if not resultat['sujet']:
            # Fallback : utiliser le fait entier comme valeur
            resultat['sujet'] = self._extraire_sujet_par_defaut(fait)
            resultat['valeur'] = fait

        # S'assurer que la valeur finit par un point
        if resultat['valeur'] and resultat['valeur'][-1] not in '.!?':
            resultat['valeur'] += '.'

        return resultat

    def _normaliser_verbe(self, verbe: str) -> str:
        """Normalise le verbe pour une forme plus naturelle."""
        normalisations = {
            'est': 'est',
            'vaut': 'vaut',
            'égale': 'vaut',
            'est égal à': 'vaut',
            'a pour valeur': 'a pour valeur',
            'correspond à': 'correspond à',
            'désigne': 'désigne',
            'consiste en': 'consiste en',
            'fonctionne ainsi': 'fonctionne ainsi',
            's\'est produit': 's\'est produit',
            'a eu lieu': 'a eu lieu',
            'a débuté': 'a débuté',
            'a commencé': 'a commencé',
            'date': 'date de',
            'remonte': 'remonte à',
        }
        return normalisations.get(verbe, verbe)

    def _extraire_date(self, texte: str) -> str:
        """Extrait une année d'un texte."""
        m = re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\b', texte)
        return m.group(1) if m else None

    def _nettoyer_date(self, texte: str, date: str) -> str:
        """Retire la date du texte de valeur."""
        # Patterns de date à nettoyer
        texte = re.sub(r'\s*(?:en|En)\s+' + date + r'\s*', ' ', texte)
        texte = re.sub(r'\s*\(?' + date + r'\)?\s*', ' ', texte)
        return texte.strip()

    def _extraire_personne(self, texte: str) -> str:
        """Extrait un nom de personne d'un texte."""
        scientifiques = [
            'Einstein', 'Newton', 'Planck', 'Darwin', 'Curie', 'Pasteur',
            'Galilée', 'Kepler', 'Maxwell', 'Bohr', 'Heisenberg', 'Feynman',
            'Hawking', 'Tesla', 'Edison', 'Marconi', 'Mendeleïev', 'Lavoisier',
            'Lemaître', 'Hubble', 'Watson', 'Crick', 'Franklin', 'Wegener',
            'Boltzmann', 'Hahn', 'Strassmann', 'Higgs', 'Schrödinger',
        ]
        for sci in scientifiques:
            if sci.lower() in texte.lower():
                return sci
        return None

    def _extraire_sujet_par_defaut(self, texte: str) -> str:
        """Extrait un sujet par défaut (premiers mots avant un verbe)."""
        mots = texte.split()
        if len(mots) <= 3:
            return texte
        # Prendre les 3-4 premiers mots comme sujet
        sujet = ' '.join(mots[:min(4, len(mots))])
        return sujet[0].upper() + sujet[1:] if sujet else "Ce sujet"


# ================================
# STRUCTURES GRAMMATICALES
# ================================

class StructuresGrammaticales:
    """
    Structures de phrases abstraites (slots à remplir).
    Inspirées des structures que l'enfant acquiert naturellement.
    """

    STRUCTURES = {
        'definition': [
            "{sujet} {verbe} {valeur}",
            "{sujet} {verbe} {valeur}",
            "On appelle {sujet_article} {valeur}",
        ],
        'decouverte': [
            "{sujet} {verbe} {valeur}",
            "C'est {sujet} qui {verbe} {valeur}",
            "On doit la découverte de {valeur_courte} à {sujet}",
        ],
        'evenement': [
            "{sujet} {verbe} {valeur}",
            "{sujet} {verbe} {valeur}",
            "L'événement {sujet} {verbe} {valeur}",
        ],
        'avec_contexte': [
            "{phrase_principale}. {contexte_avec_sujet}",
            "{phrase_principale}. {contexte_simple}",
            "{phrase_principale}. À noter que {contexte_minuscule}",
        ],
    }

    CONNECTEURS_CONTEXTE = [
        "Par ailleurs, {contexte_minuscule}",
        "De plus, {contexte_minuscule}",
        "Cette valeur a été {contexte_passif}",
    ]

    def choisir_structure(self, type_fait: str, a_contexte: bool = False) -> str:
        """Choisit une structure adaptée au type de fait."""
        import random
        if a_contexte:
            return random.choice(self.STRUCTURES['avec_contexte'])
        return random.choice(self.STRUCTURES.get(type_fait, self.STRUCTURES['definition']))


# ================================
# ASSEMBLEUR DE PHRASES
# ================================

class AssembleurPhrases:
    """
    Transforme des faits bruts en français naturel par assemblage de structures.
    """

    def __init__(self):
        self.analyseur = AnalyseurFait()
        self.structures = StructuresGrammaticales()

    def assembler(self, faits_bruts: list) -> str:
        """
        Assemble une liste de faits en une réponse fluide.

        Args:
            faits_bruts: liste de strings (faits du moteur TF-IDF)

        Returns:
            Texte en langage naturel
        """
        if not faits_bruts:
            return "Je ne dispose pas d'assez d'informations pour répondre."

        # Analyser les faits
        analyses = []
        faits_vus = set()
        for f in faits_bruts:
            f_nettoye = self._nettoyer_fait(f)
            if f_nettoye and f_nettoye not in faits_vus:
                analyse = self.analyseur.analyser(f_nettoye)
                analyses.append(analyse)
                faits_vus.add(f_nettoye)
                if len(analyses) >= 3:
                    break

        if not analyses:
            return "Aucune information exploitable."

        # Construire la phrase principale
        principale = analyses[0]
        phrase = self._construire_phrase(principale)

        # Ajouter le contexte (fait secondaire) si pertinent
        if len(analyses) > 1:
            contexte = self._construire_contexte(phrase, analyses[1], principale)
            if contexte and contexte != phrase:
                phrase = contexte

        # Post-traitement
        phrase = self._post_traitement(phrase)

        return phrase

    def _nettoyer_fait(self, texte: str) -> str:
        """Nettoie un fait brut."""
        texte = texte.strip()
        # Artefacts Q/R
        m = re.search(r'(?:question|q)\s*:\s*(.+?)\s*(?:reponse|r[eé]ponse|r)\s*:\s*(.+)', texte, re.IGNORECASE)
        if m:
            return m.group(2).strip().capitalize()
        # Préfixes
        for pfx in ['reponse:', 'réponse:', 'reponse :', 'réponse :', 'information sur ']:
            if texte.lower().startswith(pfx):
                texte = texte[len(pfx):].strip()
        # Garder la première phrase
        parts = re.split(r'(?<!\d)\.(?!\d)', texte)
        if parts and len(parts[0].strip()) > 10:
            texte = parts[0].strip()
        return texte

    def _construire_phrase(self, analyse: dict) -> str:
        """Construit une phrase à partir d'une analyse syntaxique."""
        sujet = analyse['sujet']
        verbe = analyse['verbe']
        valeur = analyse['valeur']

        # Préparer les variantes du sujet
        sujet_article = self._avec_article(sujet)
        valeur_courte = valeur[:80] + ('...' if len(valeur) > 80 else '')

        # Construire la phrase
        phrase = f"{sujet} {verbe} {valeur}"

        # Si le sujet est vide ou redondant avec la valeur, simplifier
        if sujet.lower() in valeur.lower()[:len(sujet)]:
            phrase = valeur

        return phrase

    def _construire_contexte(self, phrase_principale: str, analyse: dict, principale: dict) -> str:
        """Ajoute un contexte naturel à la phrase principale."""
        sujet_ctx = analyse['sujet']
        verbe_ctx = analyse['verbe']
        valeur_ctx = analyse['valeur']

        if not valeur_ctx:
            return phrase_principale

        # Éviter les redondances
        if valeur_ctx[:40] in phrase_principale[:len(phrase_principale)//2]:
            return phrase_principale

        # Éviter les doublons exacts
        if valeur_ctx.rstrip('.') == principale['valeur'].rstrip('.'):
            return phrase_principale

        # Construire la phrase de contexte (éviter redondance si valeur contient déjà le sujet)
        if valeur_ctx.lower().startswith(sujet_ctx.lower()[:len(sujet_ctx)]):
            contexte_phrase = valeur_ctx
        else:
            contexte_phrase = f"{sujet_ctx} {verbe_ctx} {valeur_ctx}"

        # Minuscule pour le connecteur
        contexte_minuscule = contexte_phrase[0].lower() + contexte_phrase[1:]

        # Connecteur
        import random
        connecteurs = [
            f"Par ailleurs, {contexte_minuscule}",
            f"De plus, {contexte_minuscule}",
            f"En outre, {contexte_minuscule}",
        ]

        return f"{phrase_principale.rstrip('.')}. {random.choice(connecteurs)}"

    def _avec_article(self, sujet: str) -> str:
        """Ajoute l'article approprié au sujet."""
        if sujet[0].lower() in 'aeéèêhiouâîôû':
            return f"l'{sujet[0].lower()}{sujet[1:]}" if sujet[0].isupper() else f"l'{sujet}"
        if sujet[0].isupper():
            return f"le {sujet[0].lower()}{sujet[1:]}"
        return f"le {sujet}"

    def _post_traitement(self, texte: str) -> str:
        """Applique les corrections grammaticales finales."""
        # Contractions
        texte = re.sub(r'\b(le|la)\s+([aeéèêhiouâîôûAEÉÈÊHIOUÂÎÔÛ])', r"l'\2", texte)
        texte = texte.replace('de le ', 'du ')
        texte = texte.replace('de les ', 'des ')
        texte = texte.replace('à le ', 'au ')
        texte = texte.replace('à les ', 'aux ')
        texte = texte.replace('ce est ', "c'est ")
        texte = texte.replace('que il ', "qu'il ")
        texte = texte.replace('que elle ', "qu'elle ")
        texte = texte.replace('si il ', "s'il ")
        texte = texte.replace('ne est ', "n'est ")

        # Nettoyage des espaces et ponctuation
        texte = re.sub(r'\s{2,}', ' ', texte)
        texte = re.sub(r'\s+([.,;:!?])', r'\1', texte)
        texte = re.sub(r'([.,;:!?])([^\s\d])', r'\1 \2', texte)

        # Pas de double ponctuation
        texte = texte.replace('..', '.').replace('.,', '.')

        # Majuscule en début
        texte = texte.strip()
        if texte and texte[0].islower():
            texte = texte[0].upper() + texte[1:]

        # Point final
        if texte and texte[-1] not in '.!?':
            texte += '.'

        return texte


# ================================
# TEST
# ================================
def demo():
    print("=" * 70)
    print("ASSEMBLEUR DE PHRASES — Grammaire Générative")
    print("=" * 70)
    print()

    assembleur = AssembleurPhrases()

    tests = [
        {
            'nom': 'Constante de Planck',
            'faits': [
                "La constante de Planck h = 6.626 * 10^-34 Joules seconde.",
                "Max Planck a introduit le quantum d'action en 1900.",
            ],
        },
        {
            'nom': 'Relativité',
            'faits': [
                "Einstein a publié la relativité restreinte en 1905 (E=mc²) et la relativité générale en 1915.",
                "La relativité générale décrit la gravité comme courbure de l'espace-temps.",
            ],
        },
        {
            'nom': 'Photosynthèse',
            'faits': [
                "La photosynthèse : 6 CO₂ + 6 H₂O + lumière → C₆H₁₂O₆ + 6 O₂.",
                "Les plantes convertissent l'énergie solaire en énergie chimique.",
            ],
        },
        {
            'nom': 'Big Bang',
            'faits': [
                "Le Big Bang s'est produit il y a 13.8 milliards d'années.",
                "La théorie du Big Bang (Lemaître, 1927) décrit l'origine de l'univers.",
            ],
        },
        {
            'nom': 'Einstein',
            'faits': [
                "Albert Einstein (1879-1955) était un physicien théoricien.",
                "Il a reçu le prix Nobel de physique en 1921 pour l'effet photoélectrique.",
            ],
        },
    ]

    for test in tests:
        print(f"  [{test['nom']}]")
        for f in test['faits']:
            print(f"    Fait : {f[:100]}...")
        resultat = assembleur.assembler(test['faits'])
        print(f"    → {resultat}")
        print()

    print("=" * 70)
    print("✅ TERMINÉ")
    print("=" * 70)


if __name__ == "__main__":
    demo()