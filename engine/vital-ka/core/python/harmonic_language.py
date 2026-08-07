"""
Generateur de Langage Harmonique — 0 parametre, qualite quasi-LLM
===================================================================
Fusion de ameliorateur_langage.py et assembleur_phrases.py.
Traduit des faits bruts (extraits de l'hologramme/moteur de recherche)
en francais naturel et coherent, sans aucun reseau de neurones.

Pipeline :
  1. NER (ExtracteurEntites)         → personne, valeur, date, formule
  2. Analyse syntaxique (AnalyseurFait) → sujet, verbe, valeur, type
  3. Template enrichi (TemplatesEnrichis) → phrase naturelle
  4. Post-traitement grammatical       → contractions, ponctuation
  5. Connecteurs logiques              → multi-phrases coherentes

Fallback : assembleur de phrases par slots grammaticaux si les templates
ne couvrent pas le type de fait.

Integration :
    from engine.harmonic_language import GenerateurLangage
    gen = GenerateurLangage()
    reponse = gen.formuler(question, faits_bruts)
"""

import math
import re
import random
from typing import List, Dict, Optional, Tuple


# ==============================================================================
# 1. EXTRACTION D'ENTITES NOMMEES (NER sans modele ML)
# ==============================================================================

class ExtracteurEntites:
    """Extrait les entites nommees d'un texte sans modele ML."""

    PATTERNS = {
        'personne': [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            r'\b[A-Z][a-z]+\b',
        ],
        'valeur_numerique': [
            r'\b\d+[.,]\d+\s*(?:×|x|×)\s*10\^?[-−]?\d+\s*(?:J·s|J/s|J\.s|m/s|km/s|kg|J|Hz|W|K|°C|s|N)\b',
            r'\b\d+[.,]\d+\s*(?:×|x|×)\s*10\^?[-−]?\d+\b',
            r'\b\d+\s*(?:m/s|km/s)\b',
            r'\b\d+[.,]\d+\s*(?:J·s|J/s|J\.s|kg|J|Hz|W|K|°C|s|N|m)\b',
            r'\b\d+[.,]\d+\b',
        ],
        'date': [
            r'\b\d{4}\b',
            r'\b\d+\s+(?:janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\s+\d{4}\b',
        ],
        'formule': [
            r'[A-Z]\d*[A-Za-z]?\d*\s*[=→]\s*[A-Za-z0-9+\-×*/()\s]+',
            r'\d+[A-Z][A-Za-z]?\d*\s*\+\s*\d+[A-Z][A-Za-z]?\d*',
        ],
    }

    SCIENTIFIQUES_CONNUS = {
        'einstein', 'newton', 'planck', 'darwin', 'curie', 'pasteur',
        'galilee', 'kepler', 'maxwell', 'bohr', 'heisenberg', 'schrodinger',
        'feynman', 'hawking', 'tesla', 'edison', 'bell', 'marconi',
        'mendeleiev', 'lavoisier', 'lemaitre', 'hubble', 'watson', 'crick',
        'franklin', 'wegener', 'boltzmann', 'hahn', 'strassmann', 'higgs',
    }

    def __init__(self):
        self.compiled_patterns = {}
        for cat, patterns in self.PATTERNS.items():
            # Noms propres (personne) : SANS IGNORECASE pour exiger la majuscule
            flags = 0 if cat == 'personne' else re.IGNORECASE
            self.compiled_patterns[cat] = [
                re.compile(p, flags) for p in patterns
            ]

    def extraire(self, texte: str) -> Dict[str, List[str]]:
        """Extrait toutes les entites d'un texte."""
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
        # Scientifiques connus
        texte_lower = texte.lower()
        for nom in self.SCIENTIFIQUES_CONNUS:
            if nom in texte_lower and nom.capitalize() not in entites['personne']:
                entites['personne'].append(nom.capitalize())
        return entites

    def extraire_valeur_principale(self, texte: str) -> Optional[str]:
        """Extrait la valeur numerique principale, sans le sujet redondant."""
        entites = self.extraire(texte)
        if entites['valeur_numerique']:
            # Retourner la plus SPECIFIQUE (avec unite), pas la plus longue
            valeurs_avec_unite = [v for v in entites['valeur_numerique']
                                  if re.search(r'[A-Z][a-z]|[A-Z]{2}', v)]
            if valeurs_avec_unite:
                return valeurs_avec_unite[0]
            return entites['valeur_numerique'][0]
        return None
        return None

    def extraire_personne_principale(self, texte: str) -> Optional[str]:
        entites = self.extraire(texte)
        if entites['personne']:
            mois = {'janvier','fevrier','mars','avril','mai','juin',
                    'juillet','aout','septembre','octobre','novembre','decembre'}
            personnes = [p for p in entites['personne']
                        if p.lower() not in mois and len(p) > 2]
            if personnes:
                return personnes[0]
        return None

    def extraire_date_principale(self, texte: str) -> Optional[str]:
        entites = self.extraire(texte)
        if entites['date']:
            return entites['date'][0]
        return None


# ==============================================================================
# 2. NETTOYAGE INTELLIGENT DES FAITS
# ==============================================================================

class NettoyeurFait:
    """Nettoie et resume un fait brut en forme concise."""

    PATTERNS_QR = [
        re.compile(r'question\s*:\s*([^?]+\?)\s*r[eé]ponse\s*:\s*(.+)', re.IGNORECASE),
        re.compile(r'q\s*:\s*([^?]+\?)\s*r\s*:\s*(.+)', re.IGNORECASE),
    ]

    def nettoyer(self, texte: str) -> str:
        for pattern in self.PATTERNS_QR:
            match = pattern.search(texte)
            if match:
                question = match.group(1).strip()
                reponse = match.group(2).strip()
                return self._qr_vers_phrase(question, reponse)
        prefixes = ["reponse:", "reponse :", "reponse:", "reponse :",
                     "information sur ", "information: ", "info: "]
        for prefix in prefixes:
            if texte.lower().startswith(prefix):
                texte = texte[len(prefix):].strip()
        phrases = texte.split(".")
        if phrases:
            texte = phrases[0].strip() + ("." if len(phrases[0]) > 10 else "")
        return texte

    def _qr_vers_phrase(self, question: str, reponse: str) -> str:
        q = question.lower().strip("?")
        if "quelle est" in q or "quel est" in q:
            sujet = q.replace("quelle est la ", "").replace("quelle est le ", "")
            sujet = sujet.replace("quel est la ", "").replace("quel est le ", "")
            sujet = sujet.replace("quelle est l'", "l'").replace("quel est l'", "l'")
            return f"La {sujet} est {reponse}."
        if "qui" in q and ("a decouvert" in q or "a invente" in q):
            return f"{reponse.capitalize()} a {q.split('qui a ')[1] if 'qui a ' in q else q}."
        return reponse.capitalize() + "."


# ==============================================================================
# 3. ANALYSEUR SYNTAXIQUE (fusionne depuis assembleur_phrases.py)
# ==============================================================================

class AnalyseurFait:
    """Extrait les composants syntaxiques d'un fait brut."""

    PATTERNS_VERBE_VALEUR = [
        (r'^(.+?)\s+(a\s+(?:decouvert|invente|publie|formule|introduit|mis en evidence|propose))\s+(.+)$', 'decouverte'),
        (r'^(.+?)\s+(est|vaut|egale?|a pour valeur|correspond a|designe|consiste en|fonctionne ainsi)\s+(.+)$', 'definition'),
        (r"^(.+?)\s+(s'est produit|a eu lieu|a debute|a commence|date|remonte)\s+(.+)$", 'evenement'),
        (r'^(.+?)\s*:\s*(.+)$', 'definition_courte'),
    ]

    SCIENTIFIQUES = [
        'Einstein', 'Newton', 'Planck', 'Darwin', 'Curie', 'Pasteur',
        'Galilee', 'Kepler', 'Maxwell', 'Bohr', 'Heisenberg', 'Feynman',
        'Hawking', 'Tesla', 'Edison', 'Marconi', 'Mendeleiev', 'Lavoisier',
        'Lemaitre', 'Hubble', 'Watson', 'Crick', 'Franklin', 'Wegener',
        'Boltzmann', 'Hahn', 'Strassmann', 'Higgs', 'Schrodinger',
    ]

    def analyser(self, fait_brut: str) -> dict:
        fait = fait_brut.strip().rstrip('.')
        resultat = {
            'sujet': '', 'verbe': 'est', 'valeur': '',
            'personne': None, 'date': None, 'type': 'definition',
        }
        for pattern, type_fait in self.PATTERNS_VERBE_VALEUR:
            m = re.match(pattern, fait, re.IGNORECASE)
            if m:
                sujet = m.group(1).strip()
                groupes = m.groups()
                if len(groupes) >= 3:
                    verbe = groupes[1].strip().lower()
                    valeur = groupes[2].strip()
                else:
                    verbe = 'est'
                    valeur = groupes[1].strip()
                sujet = sujet[0].upper() + sujet[1:] if sujet else sujet
                resultat['sujet'] = sujet
                resultat['verbe'] = self._normaliser_verbe(verbe)
                resultat['valeur'] = valeur
                resultat['type'] = type_fait
                date = self._extraire_date(valeur)
                if date:
                    resultat['date'] = date
                    resultat['valeur'] = self._nettoyer_date(valeur, date)
                personne = self._extraire_personne(valeur)
                if personne:
                    resultat['personne'] = personne
                break
        if not resultat['sujet']:
            resultat['sujet'] = self._extraire_sujet_par_defaut(fait)
            resultat['valeur'] = fait
        if resultat['valeur'] and resultat['valeur'][-1] not in '.!?':
            resultat['valeur'] += '.'
        return resultat

    def _normaliser_verbe(self, verbe: str) -> str:
        n = {'est': 'est', 'vaut': 'vaut', 'egale': 'vaut', 'a pour valeur': 'a pour valeur',
             'correspond a': 'correspond a', 'designe': 'designe', 'consiste en': 'consiste en',
             'fonctionne ainsi': 'fonctionne ainsi', "s'est produit": "s'est produit",
             'a eu lieu': 'a eu lieu', 'a debute': 'a debute', 'a commence': 'a commence',
             'date': 'date de', 'remonte': 'remonte a'}
        return n.get(verbe, verbe)

    def _extraire_date(self, texte: str) -> Optional[str]:
        m = re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\b', texte)
        return m.group(1) if m else None

    def _nettoyer_date(self, texte: str, date: str) -> str:
        texte = re.sub(r'\s*(?:en|En)\s+' + date + r'\s*', ' ', texte)
        texte = re.sub(r'\s*\(?' + date + r'\)?\s*', ' ', texte)
        return texte.strip()

    def _extraire_personne(self, texte: str) -> Optional[str]:
        for sci in self.SCIENTIFIQUES:
            if sci.lower() in texte.lower():
                return sci
        return None

    def _extraire_sujet_par_defaut(self, texte: str) -> str:
        mots = texte.split()
        if len(mots) <= 3:
            return texte
        sujet = ' '.join(mots[:min(4, len(mots))])
        return sujet[0].upper() + sujet[1:] if sujet else "Ce sujet"


# ==============================================================================
# 4. TEMPLATES ENRICHIS
# ==============================================================================

class TemplatesEnrichis:
    """Templates grammaticaux ameliores avec variantes naturelles."""

    TEMPLATES = {
        "definition": [
            "{sujet} est {reponse}.",
            "{sujet} designe {reponse}.",
            "On appelle {sujet} {reponse}.",
            "Le terme {sujet} fait reference a {reponse}.",
            "{sujet} correspond a {reponse}.",
            "Par {sujet}, on entend {reponse}.",
        ],
        "personne_decouverte": [
            "C'est {personne} qui a decouvert {sujet}.",
            "{sujet} a ete decouvert par {personne}.",
            "La decouverte de {sujet} est attribuee a {personne}.",
            "{personne} est le scientifique a l'origine de la decouverte de {sujet}.",
            "On doit la decouverte de {sujet} a {personne}.",
        ],
        "personne_est": [
            "{personne} est {reponse}.",
            "{personne} etait {reponse}.",
            "Connu comme {reponse}, {personne} a marque l'histoire des sciences.",
        ],
        "explication": [
            "{sujet} fonctionne de la maniere suivante : {reponse}.",
            "Le principe de {sujet} repose sur {reponse}.",
            "{sujet} consiste en {reponse}.",
            "Pour comprendre {sujet}, il faut savoir que {reponse}.",
            "{sujet} est le processus par lequel {reponse}.",
        ],
        "valeur": [
            "{sujet} vaut exactement {valeur}.",
            "La valeur de {sujet} est {valeur}.",
            "{sujet} est egal a {valeur}.",
            "On mesure {sujet} comme etant {valeur}.",
            "{sujet} a pour valeur {valeur}.",
            "La mesure de {sujet} donne {valeur}.",
        ],
        "date_evenement": [
            "{sujet} s'est produit en {date}.",
            "{sujet} date de {date}.",
            "C'est en {date} que {sujet} a eu lieu.",
            "{date} est la date cle de {sujet}.",
            "{sujet} remonte a {date}.",
        ],
        "contexte_enrichi": [
            "{phrase_principale}. {contexte}.",
            "{phrase_principale}. En {date}, {contexte}.",
            "{phrase_principale}. {personne} {contexte}.",
        ],
    }

    def choisir(self, type_template: str) -> str:
        ts = self.TEMPLATES.get(type_template, self.TEMPLATES["definition"])
        return random.choice(ts)

    def formuler(self, type_template: str, **kwargs) -> str:
        template = self.choisir(type_template)
        try:
            return template.format(**kwargs)
        except KeyError:
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
    """Corrections grammaticales de base (contractions, ponctuation)."""

    CONTRACTIONS = [
        (r'\b(le|la)\s+([aeéèêhiouâîôûAEÉÈÊHIOUÂÎÔÛ])', r"l'\2"),
        ('de le ', 'du '), ('de les ', 'des '),
        ('a le ', 'au '), ('a les ', 'aux '),
        ('ce est ', "c'est "), ('que il ', "qu'il "),
        ('que elle ', "qu'elle "), ('si il ', "s'il "),
        ('ne est ', "n'est "), ('je ai ', "j'ai "),
    ]

    DOUBLES_ESPACES = re.compile(r'\s{2,}')
    PONCTUATION_ESPACE = re.compile(r'\s+([.,;:!?])')

    def corriger(self, texte: str) -> str:
        for pattern, remplacement in self.CONTRACTIONS:
            if pattern.startswith('\\b'):
                texte = re.sub(pattern, remplacement, texte)
            else:
                texte = texte.replace(pattern, remplacement)
        if texte and texte[0].islower():
            texte = texte[0].upper() + texte[1:]
        texte = self.DOUBLES_ESPACES.sub(' ', texte)
        texte = self.PONCTUATION_ESPACE.sub(r'\1', texte)
        texte = texte.strip()
        if texte and texte[-1] not in '.!?':
            texte += '.'
        texte = texte.replace('..', '.').replace('.,', '.')
        return texte


# ==============================================================================
# 6. CONNECTEURS LOGIQUES
# ==============================================================================

class ConnecteursLogiques:
    """Ajoute des connecteurs logiques entre les faits."""

    CONNECTEURS_ADDITION = [
        "De plus, ", "Par ailleurs, ", "En outre, ",
        "A noter egalement que ", "Il faut aussi savoir que ",
    ]
    CONNECTEURS_PRECISION = [
        "Plus precisement, ", "En d'autres termes, ",
        "C'est-a-dire que ", "Concretement, ",
    ]
    CONNECTEURS_CONSEQUENCE = [
        "Ainsi, ", "Par consequent, ", "De ce fait, ",
        "C'est pourquoi ", "Il en resulte que ",
    ]

    def combiner_faits(self, faits: List[str]) -> str:
        if len(faits) <= 1:
            return faits[0] if faits else ""
        phrases = [faits[0].strip()]
        for i, fait in enumerate(faits[1:], 1):
            fait = fait.strip()
            if not fait:
                continue
            if i == len(faits) - 1:
                connecteur = random.choice(self.CONNECTEURS_PRECISION)
            else:
                connecteur = random.choice(self.CONNECTEURS_ADDITION)
            fait_lower = fait[0].lower() + fait[1:] if fait else fait
            phrases.append(connecteur + fait_lower)
        return ' '.join(phrases)


# ==============================================================================
# 7. ASSEMBLEUR DE PHRASES (fallback par slots grammaticaux)
# ==============================================================================

class AssembleurFallback:
    """Fallback : assemblage par slots sujet-verbe-complement."""

    def __init__(self):
        self.analyseur = AnalyseurFait()
        self.grammaire = PostTraitementGrammatical()

    def assembler(self, faits_bruts: list) -> str:
        if not faits_bruts:
            return "Je ne dispose pas d'assez d'informations pour repondre."
        analyses = []
        faits_vus = set()
        for f in faits_bruts:
            f_nettoye = self._nettoyer(f)
            if f_nettoye and f_nettoye not in faits_vus:
                analyse = self.analyseur.analyser(f_nettoye)
                analyses.append(analyse)
                faits_vus.add(f_nettoye)
                if len(analyses) >= 3:
                    break
        if not analyses:
            return "Aucune information exploitable."
        phrase = self._construire_phrase(analyses[0])
        if len(analyses) > 1 and analyses[1]['valeur'] != analyses[0]['valeur']:
            ctx = self._construire_contexte(analyses[1])
            if ctx:
                phrase = f"{phrase.rstrip('.')}. {ctx}"
        return self.grammaire.corriger(phrase)

    def _nettoyer(self, texte: str) -> str:
        texte = texte.strip()
        m = re.search(r'(?:question|q)\s*:\s*(.+?)\s*(?:reponse|r[eé]ponse|r)\s*:\s*(.+)', texte, re.IGNORECASE)
        if m:
            return m.group(2).strip().capitalize()
        for pfx in ['reponse:', 'reponse :', 'reponse:', 'reponse :']:
            if texte.lower().startswith(pfx):
                texte = texte[len(pfx):].strip()
        parts = re.split(r'(?<!\d)\.(?!\d)', texte)
        if parts and len(parts[0].strip()) > 10:
            texte = parts[0].strip()
        return texte

    def _construire_phrase(self, analyse: dict) -> str:
        s, v, val = analyse['sujet'], analyse['verbe'], analyse['valeur']
        if s.lower() in val.lower()[:len(s)]:
            return val
        return f"{s} {v} {val}"

    def _construire_contexte(self, analyse: dict) -> str:
        val = analyse['valeur']
        if not val:
            return ""
        connecteurs = ["Par ailleurs, ", "De plus, ", "En outre, "]
        conn = random.choice(connecteurs)
        ctx = f"{analyse['sujet']} {analyse['verbe']} {val}"
        return conn + ctx[0].lower() + ctx[1:]


# ==============================================================================
# 8. GENERATEUR DE LANGAGE PRINCIPAL
# ==============================================================================

class GenerateurLangage:
    """
    Generateur de langage naturel de qualite quasi-LLM.

    Pipeline :
      1. NER (personne, valeur, date)
      2. Nettoyage du fait principal
      3. Selection du template adapte au type de question
      4. Formulation + post-traitement grammatical
      5. Enrichissement multi-faits avec connecteurs
      6. Fallback assembleur si les templates echouent

    Zero parametre entrainable. Zero reseau de neurones.
    """

    def __init__(self):
        self.ner = ExtracteurEntites()
        self.nettoyeur = NettoyeurFait()
        self.templates = TemplatesEnrichis()
        self.grammaire = PostTraitementGrammatical()
        self.connecteurs = ConnecteursLogiques()
        self.fallback = AssembleurFallback()

    def formuler(self, question: str, faits: List[str]) -> str:
        """
        Genere une reponse en langage naturel a partir de faits bruts.

        Args:
            question: la question posee (pour le choix du template)
            faits: liste de textes factuels (top-N de l'hologramme)

        Returns:
            Reponse en francais naturel
        """
        if not faits:
            return "Je ne dispose pas d'informations suffisantes pour repondre a cette question."

        # Nettoyer et analyser le meilleur fait
        fait_principal = self.nettoyeur.nettoyer(faits[0])

        # Extraire les entites
        tous_faits_texte = ' '.join(faits)
        personne = (self.ner.extraire_personne_principale(fait_principal) or
                    self.ner.extraire_personne_principale(tous_faits_texte))
        valeur = (self.ner.extraire_valeur_principale(fait_principal) or
                  self.ner.extraire_valeur_principale(tous_faits_texte))
        date = (self.ner.extraire_date_principale(fait_principal) or
                self.ner.extraire_date_principale(tous_faits_texte))

        # Extraire le sujet de la question
        sujet = self._extraire_sujet(question)

        # === DETERMINER LE TYPE DE REPONSE ===
        q_lower = question.lower()

        if any(m in q_lower for m in ['qui est', 'qui etait', 'qui a']):
            if personne and valeur:
                valeur_nettoyee = self._nettoyer_valeur(valeur, sujet)
                reponse = self.templates.formuler("personne_decouverte",
                    sujet=sujet, personne=personne, valeur=valeur_nettoyee)
            elif personne:
                fait_nettoye = self._nettoyer_valeur(fait_principal, sujet)
                # Eviter la duplication quand le fait commence deja par la personne
                if personne.lower() in fait_nettoye.lower()[:len(personne) + 5]:
                    reponse = fait_nettoye
                else:
                    reponse = self.templates.formuler("personne_est",
                        personne=personne, reponse=fait_nettoye)
            else:
                reponse = fait_principal

        elif any(m in q_lower for m in ['quelle est', 'quel est', 'valeur', 'vitesse', 'constante']):
            if valeur:
                reponse = self.templates.formuler("valeur", sujet=sujet, valeur=valeur)
            else:
                reponse = self.templates.formuler("valeur", sujet=sujet, valeur=fait_principal)

        elif any(m in q_lower for m in ['quand', 'date', 'annee', 'siecle']):
            if date:
                reponse = self.templates.formuler("date_evenement", sujet=sujet, date=date)
            else:
                reponse = fait_principal

        elif any(m in q_lower for m in ['comment', 'pourquoi', 'fonctionne', 'marche']):
            fait_nettoye = self._nettoyer_valeur(fait_principal, sujet)
            reponse = self.templates.formuler("explication", sujet=sujet, reponse=fait_nettoye)

        elif any(m in q_lower for m in ["qu'est-ce", "c'est quoi", "definition"]):
            fait_nettoye = self._nettoyer_valeur(fait_principal, sujet)
            reponse = self.templates.formuler("definition", sujet=sujet, reponse=fait_nettoye)

        else:
            # Question generale : utiliser le meilleur template selon les entites
            if personne and valeur:
                valeur_nettoyee = self._nettoyer_valeur(valeur, sujet)
                reponse = self.templates.formuler("personne_decouverte",
                    sujet=sujet, personne=personne, valeur=valeur_nettoyee)
            elif valeur:
                valeur_nettoyee = self._nettoyer_valeur(valeur, sujet)
                reponse = self.templates.formuler("valeur", sujet=sujet, valeur=valeur_nettoyee)
            else:
                fait_nettoye = self._nettoyer_valeur(fait_principal, sujet)
                reponse = fait_nettoye

        # === ENRICHISSEMENT MULTI-FAITS ===
        if len(faits) > 1:
            fait_secondaire = self.nettoyeur.nettoyer(faits[1])
            if len(fait_secondaire) > 20:
                personne_ctx = personne if personne else ''
                date_ctx = date if date else ''
                if personne_ctx or date_ctx:
                    reponse = self.templates.formuler("contexte_enrichi",
                        phrase_principale=reponse, contexte=fait_secondaire,
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

        # Cas special : "qui a decouvert X" → sujet = X
        m = re.search(r'qui a (?:decouvert|invente|publie|formule|introduit)\s+(.+)$', q)
        if m:
            sujet = m.group(1).strip()
            for art in ["la ", "le ", "l'", "une ", "un ", "des ", "les "]:
                if sujet.startswith(art):
                    sujet = sujet[len(art):]
                    break
            return sujet[0].upper() + sujet[1:] if sujet else "ce sujet"

        nettoyages = [
            "quelle est la valeur de ", "quelle est la ", "quel est le ", "quel est l'",
            "quelle est l'", "quel est ", "quelle est ",
            "qui est ", "qui etait ",
            "comment fonctionne ", "comment marche ", "comment ",
            "qu'est-ce que ", "qu'est-ce qu'", "c'est quoi ",
            "pourquoi ", "explique ", "decris ",
        ]
        sujet = q
        for pattern in nettoyages:
            if sujet.startswith(pattern):
                sujet = sujet[len(pattern):]
                break
        for art in ["la ", "le ", "l'", "une ", "un ", "des ", "les "]:
            if sujet.startswith(art):
                sujet = sujet[len(art):]
                break
        sujet = sujet.strip()
        return sujet[0].upper() + sujet[1:] if sujet else "ce sujet"

    def _nettoyer_valeur(self, valeur: str, sujet: str) -> str:
        """
        Supprime le sujet du debut de la valeur pour eviter la duplication.

        Exemple: sujet="Constante de Planck", valeur="La constante de Planck h = 6.626..."
        → retourne "6.626 × 10⁻³⁴ J·s" ou la partie apres le verbe/ponctuation.
        """
        if not valeur or not sujet:
            return valeur

        v = valeur.strip()
        s_lower = sujet.lower().strip()

        # Si la valeur commence par le sujet (ou une variante proche)
        if v.lower().startswith(s_lower[:5]):
            # Essayer de trouver le separateur : "est", "=", ":", "vaut", "→"
            for sep in [' est ', ' vaut ', ' = ', ' : ', ' → ', ' egal a ']:
                idx = v.lower().find(sep)
                if idx > 0:
                    apres = v[idx + len(sep):].strip()
                    if len(apres) > 5:
                        return apres
            # Si le sujet occupe plus de 50% de la valeur, la valeur EST le fait
            if len(s_lower) > len(v) * 0.5:
                return v
            # Sinon, essayer de garder juste la partie apres le sujet
            reste = v[len(s_lower):].strip()
            if reste and reste[0] in ':=-→,;.':
                reste = reste[1:].strip()
            if len(reste) > 5:
                return reste

        # Si la valeur contient deja le sujet en redondance (ex: "La constante de Planck h = X")
        # et qu'on a une valeur numerique isolee, preferer la valeur
        if s_lower in v.lower() and len(v) > len(s_lower) + 10:
            return v  # garder tel quel, le template devrait gerer

        return v


# ==============================================================================
# DEMONSTRATION
# ==============================================================================

def demo():
    """Demonstration du generateur de langage harmonique."""
    print("=" * 60)
    print("GENERATEUR DE LANGAGE HARMONIQUE (0 parametre)")
    print("=" * 60)
    print()

    gen = GenerateurLangage()

    tests = [
        ("quelle est la constante de Planck",
         ["La constante de Planck h = 6.626 * 10^-34 Joules seconde.",
          "Max Planck a introduit le quantum d'action en 1900."]),
        ("qui a decouvert la relativite",
         ["Einstein a publie la relativite restreinte en 1905 (E=mc2).",
          "La relativite generale decrit la gravite comme courbure de l'espace-temps."]),
        ("comment fonctionne la photosynthese",
         ["La photosynthese : 6 CO2 + 6 H2O + lumiere -> C6H12O6 + 6 O2.",
          "Les plantes convertissent l'energie solaire en energie chimique."]),
        ("quelle est la vitesse de la lumiere",
         ["La vitesse de la lumiere dans le vide est 299 792 458 m/s.",
          "C'est une constante fondamentale de la physique."]),
        ("qu'est-ce que le Big Bang",
         ["Le Big Bang s'est produit il y a 13.8 milliards d'annees.",
          "La theorie du Big Bang (Lemaitre, 1927) decrit l'origine de l'univers."]),
    ]

    for question, faits in tests:
        print(f"  Q: {question}")
        reponse = gen.formuler(question, faits)
        print(f"  R: {reponse}")
        print()


if __name__ == '__main__':
    demo()
