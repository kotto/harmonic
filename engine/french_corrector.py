#!/usr/bin/env python3
"""
french_corrector.py — Correcteur harmonique de prose française
================================================================

Pipeline DÉTERMINISTE de correction grammaticale, syntaxique et
typographique (0 LLM, ~ms, local). L'idée : le plus difficile — produire
du texte VRAI — est fait par le gate M4 ; la forme est un problème
mécanique traité par des règles linguistiques.

CONTRAT DE VÉRACITÉ : le correcteur ne modifie JAMAIS le contenu
sémantique — uniquement les mots fonctionnels (articles, prépositions,
auxiliaires, terminaisons de participe, élisions, majuscules). Il peut
ajouter « le », « une », « du » — jamais un nom, un verbe, un adjectif.

Passes (dans l'ordre) :
  1. accents + élisions + apostrophes          (lexique ~200 mots)
  2. contractions de/à + article               (de le → du, a le → au…)
  3. participe passé après être                (« est cause par » → « est
     causé par », accordé au genre du sujet)
  4. accord sujet-verbe 3e personne            (« traitement des
     complications permettent » → « permet »)
  5. articles manquants                        (« Paludisme est parasitose »
     → « Le paludisme est une parasitose »)
  6. capitalisation + typographie française
"""

import re

# ═══════════════════════════════════════════════════════════════════════════════
# 0. LEXIQUES
# ═══════════════════════════════════════════════════════════════════════════════

# Genre des noms courants (médical/scientifique) — 'm' masculin, 'f' féminin
GENDER = {
    # Médecine
    'diabete': 'm', 'paludisme': 'm', 'traitement': 'm', 'terme': 'm',
    'sang': 'm', 'glucose': 'm', 'virus': 'm', 'vaccin': 'm', 'moustique': 'm',
    'parasite': 'm', 'cancer': 'm', 'symptome': 'm', 'medicament': 'm',
    'taux': 'm', 'risque': 'm', 'cerveau': 'm', 'coeur': 'm', 'foie': 'm',
    'rein': 'm', 'poumon': 'm', 'muscle': 'm', 'os': 'm', 'pancreas': 'm',
    'cholesterol': 'm', 'glucagon': 'm', 'sucre': 'm', 'glucose': 'm',
    'insuline': 'f', 'maladie': 'f', 'deficience': 'f', 'resistance': 'f',
    'glycemie': 'f', 'infection': 'f', 'vaccination': 'f', 'parasitose': 'f',
    'transmission': 'f', 'proliferation': 'f', 'cellule': 'f', 'membrane': 'f',
    'mitochondrie': 'f', 'proteine': 'f', 'hormone': 'f', 'artere': 'f',
    'veine': 'f', 'peau': 'f', 'sante': 'f', 'anemie': 'f', 'therapie': 'f',
    'epidemie': 'f', 'pandemie': 'f', 'hepatite': 'f', 'tuberculose': 'f',
    'grippe': 'f', 'hypertension': 'f', 'pression': 'f', 'vaccination': 'f',
    'immunite': 'f', 'secretion': 'f', 'synthese': 'f', 'photosynthese': 'f',
    'energie': 'f', 'matiere': 'f', 'lumiere': 'f', 'supernova': 'f',
    'gravite': 'f', 'temperature': 'f', 'planete': 'f', 'etoile': 'f',
    'espece': 'f', 'duree': 'f', 'longevite': 'f', 'reponse': 'f',
    'etude': 'f', 'experience': 'f', 'hypothese': 'f', 'these': 'f',
    'consequence': 'f', 'regeneration': 'f', 'secretion': 'f',
    'mortalite': 'f', 'morbidite': 'f', 'chimiotherapie': 'f',
    'radiotherapie': 'f', 'immunotherapie': 'f', 'adrenaline': 'f',
    'thyroide': 'f', 'prothese': 'f', 'greffe': 'f', 'transplantation': 'f',
    'dialyse': 'f', 'oxygenation': 'f', 'circulation': 'f', 'coagulation': 'f',
    'digestion': 'f', 'respiration': 'f', 'vision': 'f', 'audition': 'f',
    'prevention': 'f', 'depistage': 'm', 'medecine': 'f', 'physiologie': 'f',
    'anatomie': 'f', 'biologie': 'f', 'genetique': 'f', 'physique': 'f',
    'chimie': 'f', 'astronomie': 'f', 'philosophie': 'f', 'psychologie': 'f',
    'histoire': 'f', 'geographie': 'f', 'economie': 'f', 'musique': 'f',
    'latin': 'm', 'globe': 'm', 'monde': 'm', 'univers': 'm', 'systeme': 'm',
    'mecanisme': 'm', 'processus': 'm', 'modele': 'm', 'probleme': 'm',
    'element': 'm', 'phenomene': 'm', 'principe': 'm', 'concept': 'm',
    'corps': 'm', 'membre': 'm', 'organe': 'm', 'tissu': 'm', 'gene': 'm',
    'chromosome': 'm', 'noyau': 'm', 'niveau': 'm', 'developpement': 'm',
    'vieillissement': 'm', 'metabolisme': 'm', 'glucose': 'm',
}

# Noms terminant par s/x MAIS singuliers (pour l'accord nombre)
_SINGULAR_S = {'pancreas', 'os', 'corps', 'virus', 'sang', 'taux', 'cholesterol',
               'glucose', 'latin', 'univers', 'processus', 'sucre', 'temps',
               'cancer', 'diabete', 'paludisme', 'traitement', 'symptome'}

# Paires verbe singulier / pluriel (3e personne)
VERB_PAIRS = {
    'est': 'sont', 'etait': 'etaient', 'permet': 'permettent',
    'cause': 'causent', 'provoque': 'provoquent', 'produit': 'produisent',
    'regule': 'regulent', 'contient': 'contiennent', 'augmente': 'augmentent',
    'diminue': 'diminuent', 'entraine': 'entrainent', 'protege': 'protegent',
    'transporte': 'transportent', 'secrete': 'secretent',
    'synthetise': 'synthetisent', 'neutralise': 'neutralisent',
    'favorise': 'favorisent', 'reduit': 'reduisent', 'libere': 'liberent',
    'stimule': 'stimulent', 'bloque': 'bloquent', 'agit': 'agissent',
    'intervient': 'interviennent', 'depend': 'dependent',
    'resulte': 'resultent', 'devient': 'deviennent',
    'survient': 'surviennent', 'touche': 'touchent', 'atteint': 'atteignent',
    'affecte': 'affectent', 'evite': 'evitent', 'recommande': 'recommandent',
    'utilise': 'utilisent', 'administre': 'administrent',
    'prescrit': 'prescrivent', 'mesure': 'mesurent', 'detecte': 'detectent',
    'diagnostique': 'diagnostiquent', 'classifie': 'classifient',
    'traite': 'traitent', 'observe': 'observent', 'etudie': 'etudient',
    'decrit': 'decrivent', 'definit': 'definissent', 'explique': 'expliquent',
    'montre': 'montrent', 'indique': 'indiquent', 'suggere': 'suggerent',
    'confirme': 'confirment', 'demontre': 'demontrent', 'reste': 'restent',
    'existe': 'existent', 'apparait': 'apparaissent', 'disparait': 'disparaissent',
    'joue': 'jouent', 'agit': 'agissent', 'fonctionne': 'fonctionnent',
    'empeche': 'empechent', 'evite': 'evitent', 'protege': 'protegent',
}

# Verbe → participe passé (forme accentuée) pour « être + participe + par »
PARTICIPES = {
    'cause': 'causé', 'causent': 'causé', 'utilise': 'utilisé',
    'utilisent': 'utilisé', 'lie': 'lié', 'lies': 'lié', 'liee': 'liée',
    'associe': 'associé', 'associee': 'associée',
    'caracterise': 'caractérisé', 'caracterisee': 'caractérisée',
    'regule': 'régulé', 'regulent': 'régulé',
    'secrete': 'sécrété', 'secretent': 'sécrété',
    'protege': 'protégé', 'protegent': 'protégé',
    'produit': 'produit', 'produisent': 'produit',
    'transmet': 'transmis', 'transmettent': 'transmis',
    'decouvre': 'découvert', 'decouvrent': 'découvert',
    'invente': 'inventé', 'inventent': 'inventé',
    'detecte': 'détecté', 'detectent': 'détecté',
    'traite': 'traité', 'traitent': 'traité',
    'diagnostique': 'diagnostiqué', 'diagnostiquent': 'diagnostiqué',
    'observe': 'observé', 'observent': 'observé',
    'etudie': 'étudié', 'etudient': 'étudié',
    'transporte': 'transporté', 'transportent': 'transporté',
    'synthetise': 'synthétisé', 'synthetisent': 'synthétisé',
    'detoxifie': 'détoxifié', 'detoxifient': 'détoxifié',
    'neutralise': 'neutralisé', 'neutralisent': 'neutralisé',
    'favorise': 'favorisé', 'favorisent': 'favorisé',
    'libere': 'libéré', 'liberent': 'libéré',
    'stimule': 'stimulé', 'stimulent': 'stimulé',
    'bloque': 'bloqué', 'bloquent': 'bloqué',
    'administre': 'administré', 'administrent': 'administré',
    'prescrit': 'prescrit', 'prescrivent': 'prescrit',
    'compose': 'composé', 'composent': 'composé',
    'forme': 'formé', 'forment': 'formé',
    'constitue': 'constitué', 'constituent': 'constitué',
    'divise': 'divisé', 'divisent': 'divisé',
    'entraine': 'entraîné', 'entrainent': 'entraîné',
    'augmente': 'augmenté', 'augmentent': 'augmenté',
    'reduit': 'réduit', 'reduisent': 'réduit',
    'empeche': 'empêché', 'empechent': 'empêché',
    'elimine': 'éliminé', 'eliminent': 'éliminé',
    'absorbe': 'absorbé', 'absorbent': 'absorbé',
    'digere': 'digéré', 'digerent': 'digéré',
    'filtre': 'filtré', 'filtrent': 'filtré',
    'purifie': 'purifié', 'purifient': 'purifié',
    'mesure': 'mesuré', 'mesurent': 'mesuré',
    'definit': 'défini', 'definissent': 'défini',
    'realise': 'réalisé', 'realisent': 'réalisé',
    'influence': 'influencé', 'influencent': 'influencé',
}

# Partitifs : « de » reste sans article après ces noms (« un excès DE glucose »)
_PARTITIF_PRECEDERS = {
    'exces', 'taux', 'manque', 'deficit', 'absence', 'dose', 'quantite',
    'litre', 'gramme', 'kilo', 'million', 'milliard', 'centaine', 'paire',
    'groupe', 'forme', 'type', 'modele', 'niveau', 'molécule', 'molecule',
}

# Mots fonctionnels (jamais traités comme sujet/nom)
_FUNCTION_WORDS = {
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'd', 'l', 'au', 'aux',
    'a', 'à', 'en', 'dans', 'par', 'pour', 'avec', 'sur', 'sous', 'chez',
    'vers', 'entre', 'pendant', 'avant', 'apres', 'depuis', 'sans', 'selon',
    'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car', 'que', 'qui', 'dont', 'se',
    'ce', 'ces', 'cette', 'son', 'sa', 'ses', 'leur', 'leurs', 'notre', 'nos',
    'votre', 'vos', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'il', 'elle', 'ils',
    'elles', 'on', 'nous', 'vous', 'je', 'tu', 'y', 'en', 'ne', 'pas', 'plus',
    'tres', 'tout', 'tous', 'toute', 'toutes', 'aussi', 'bien', 'ainsi',
    'cela', 'ceci', 'cette', 'chacun', 'chaque', 'certains', 'certaines',
    'nombreux', 'nombreuses', 'plusieurs', 'autres', 'autre', 'meme', 'memes',
    'comme', 'comment', 'quand', 'pourquoi', 'ou', 'apres', 'pres', 'loin',
    'proche', 'dans', 'hors', 'voici', 'voila', 'c est', 'qu est',
}

# ═══════════════════════════════════════════════════════════════════════════════
# 1. ACCENTS + ÉLISIONS
# ═══════════════════════════════════════════════════════════════════════════════

_ACCENT_MAP = {
    # Médecine — diabète & métabolisme
    'diabete': 'diabète', 'diabetes': 'diabète', 'glycemie': 'glycémie',
    'hyperglycemie': 'hyperglycémie', 'hypoglycemie': 'hypoglycémie',
    'exces': 'excès', 'deficience': 'déficience', 'deficiences': 'déficiences',
    'resistance': 'résistance', 'resistances': 'résistances',
    'caracterisee': 'caractérisée', 'caracterise': 'caractérise',
    'caracterisees': 'caractérisées', 'caracterises': 'caractérisés',
    'utilisee': 'utilisée', 'utilisees': 'utilisées', 'utilise': 'utilisé',
    'utilises': 'utilisés', 'elevee': 'élevée', 'eleve': 'élevé',
    'eleves': 'élevés', 'arterielle': 'artérielle', 'arteriel': 'artériel',
    'arteriels': 'artériels', 'arterielles': 'artérielles',
    'sante': 'santé', 'anemie': 'anémie', 'anemies': 'anémies',
    'medecine': 'médecine', 'medicale': 'médicale', 'medicaux': 'médicaux',
    'medicament': 'médicament', 'medicaments': 'médicaments',
    'hopital': 'hôpital', 'hopitaux': 'hôpitaux', 'symptome': 'symptôme',
    'symptomes': 'symptômes', 'therapie': 'thérapie', 'therapies': 'thérapies',
    'chimiotherapie': 'chimiothérapie', 'radiotherapie': 'radiothérapie',
    'immunotherapie': 'immunothérapie', 'prothese': 'prothèse',
    'protheses': 'prothèses', 'epidemie': 'épidémie', 'epidemies': 'épidémies',
    'pandemie': 'pandémie', 'mortalite': 'mortalité', 'morbidite': 'morbidité',
    'deces': 'décès', 'hepatite': 'hépatite', 'depistage': 'dépistage',
    'prevention': 'prévention', 'prevenir': 'prévenir', 'eviter': 'éviter',
    'consequence': 'conséquence', 'consequences': 'conséquences',
    'sequelle': 'séquelle', 'sequelles': 'séquelles',
    # Biologie
    'proliferation': 'prolifération', 'regeneration': 'régénération',
    'longevite': 'longévité', 'duree': 'durée', 'precoce': 'précoce',
    'detoxifie': 'détoxifie', 'detoxifient': 'détoxifient',
    'synthetise': 'synthétise', 'synthetisent': 'synthétisent',
    'synthese': 'synthèse', 'photosynthese': 'photosynthèse',
    'energie': 'énergie', 'energetique': 'énergétique', 'oxygene': 'oxygène',
    'secrete': 'sécrète', 'secretent': 'sécrètent', 'secretes': 'sécrétées',
    'secretion': 'sécrétion', 'adrenaline': 'adrénaline',
    'thyroide': 'thyroïde', 'immunite': 'immunité', 'genetique': 'génétique',
    'genetiques': 'génétiques', 'proteine': 'protéine', 'proteines': 'protéines',
    'artere': 'artère', 'arteres': 'artères', 'alveole': 'alvéole',
    'alveoles': 'alvéoles', 'oesophage': 'œsophage',
    'degenerative': 'dégénérative', 'degenerescence': 'dégénérescence',
    'anopheles': 'anophèles',
    # Sciences
    'etoile': 'étoile', 'etoiles': 'étoiles', 'planete': 'planète',
    'planetes': 'planètes', 'exoplanete': 'exoplanète', 'lumiere': 'lumière',
    'residu': 'résidu', 'residus': 'résidus', 'matiere': 'matière',
    'gravite': 'gravité', 'mecanique': 'mécanique', 'mecaniques': 'mécaniques',
    'electron': 'électron', 'electrons': 'électrons',
    'nucleaire': 'nucléaire', 'nucleaires': 'nucléaires',
    'celeste': 'céleste', 'celestes': 'célestes',
    'temperature': 'température', 'temperatures': 'températures',
    'espece': 'espèce', 'especes': 'espèces', 'atmosphere': 'atmosphère',
    # Général
    'etre': 'être', 'etat': 'état', 'etats': 'états', 'etape': 'étape',
    'etapes': 'étapes', 'probleme': 'problème', 'problemes': 'problèmes',
    'reponse': 'réponse', 'reponses': 'réponses', 'meme': 'même',
    'memes': 'mêmes', 'apres': 'après', 'pres': 'près', 'tres': 'très',
    'deja': 'déjà', 'premiere': 'première', 'premieres': 'premières',
    'derniere': 'dernière', 'generale': 'générale', 'element': 'élément',
    'elements': 'éléments', 'mecanisme': 'mécanisme', 'mecanismes': 'mécanismes',
    'modele': 'modèle', 'modeles': 'modèles', 'resultats': 'résultats',
    'resultat': 'résultat', 'etude': 'étude', 'etudes': 'études',
    'experience': 'expérience', 'experiences': 'expériences',
    'hypothese': 'hypothèse', 'hypotheses': 'hypothèses', 'these': 'thèse',
    'theses': 'thèses', 'critere': 'critère', 'criteres': 'critères',
    'numero': 'numéro', 'regule': 'régule', 'regulent': 'régulent',
    'regulee': 'régulée', 'regulation': 'régulation', 'protege': 'protège',
    'protegent': 'protègent', 'protegee': 'protégée', 'liberee': 'libérée',
    'conserve': 'conservé', 'conservee': 'conservée',
    'precision': 'précision', 'etabli': 'établi', 'etablie': 'établie',
    'etablis': 'établis', 'etablit': 'établit',
}

_ACCENT_KEYS = sorted(_ACCENT_MAP, key=len, reverse=True)
_ACCENT_RE = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in _ACCENT_KEYS) + r')\b')

_APOSTROPHE_FIXES = [
    ('qu est ce', "qu'est-ce"), ('qu est-ce', "qu'est-ce"),
    ('qu il', "qu'il"), ('qu elle', "qu'elle"), ('qu on', "qu'on"),
    ('qu est', "qu'est"), ('c est', "c'est"), ('n est', "n'est"),
    ('s est', "s'est"), ('j ai', "j'ai"), ('j en', "j'en"),
    ('d une', "d'une"), ('d un', "d'un"), ('l a', "l'a"),
    ('l est', "l'est"), ('l on', "l'on"),
    ('a la', 'à la'), ('a un', 'à un'), ('a une', 'à une'),
]

_VOWEL = 'aeiouyhàâäéèêëîïôöùûü'  # pour les élisions


def _restore_accents(text: str) -> str:
    """Accents (frontière de mot) + apostrophes + élisions françaises."""
    text = _ACCENT_RE.sub(lambda m: _ACCENT_MAP[m.group(1)], text)
    for k, v in _APOSTROPHE_FIXES:
        text = re.sub(rf'\b{re.escape(k)}\b', v, text)
    # « a l insuline » → « à l'insuline » (l'apostrophe consomme l'espace)
    text = re.sub(r"\ba l\s+(?=[a-zàâäéèêëîïôöùûüç])", "à l'", text)
    # « que + voyelle » → « qu' + voyelle »
    text = re.sub(rf"\bque ([{_VOWEL}])", r"qu'\1", text)
    # « de + voyelle » → « d' + voyelle » (de insuline → d'insuline)
    text = re.sub(rf"\bde ([{_VOWEL}])", r"d'\1", text)
    return text


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CONTRACTIONS de/à + article
# ═══════════════════════════════════════════════════════════════════════════════

def _fix_contractions(text: str) -> str:
    text = re.sub(r'\bde le\b', 'du', text)
    text = re.sub(r'\bde les\b', 'des', text)
    text = re.sub(r'\ba le\b', 'au', text)
    text = re.sub(r'\ba les\b', 'aux', text)
    # Partitifs protégés : « un excès DE glucose » — placeholder temporaire
    part_pat = re.compile(
        r'\b(?:' + '|'.join(sorted(_PARTITIF_PRECEDERS, key=len, reverse=True))
        + r')\s+de\s+(?=[a-zàâäéèêëîïôöùûüç])')
    text = part_pat.sub(lambda m: m.group(0).replace(' de ', ' DE_PART '), text)
    # « de + nom masculin connu » → « du + nom » (de latin → du latin)
    for noun in sorted(GENDER, key=len, reverse=True):
        if GENDER[noun] == 'm':
            text = re.sub(rf'\bde {re.escape(noun)}\b', f'du {noun}', text)
    # « a + nom » → « au/à la » (a paludisme → au paludisme)
    for noun in sorted(GENDER, key=len, reverse=True):
        if GENDER[noun] == 'm':
            text = re.sub(rf'\ba {re.escape(noun)}\b', f'au {noun}', text)
        elif GENDER[noun] == 'f':
            text = re.sub(rf'\ba {re.escape(noun)}\b', f'à la {noun}', text)
    # Restauration des partitifs
    text = text.replace(' DE_PART ', ' de ')
    return text


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PARTICIPE PASSÉ APRÈS « ÊTRE »
# ═══════════════════════════════════════════════════════════════════════════════

def _subject_gender(subject: str) -> str:
    """Genre du sujet = genre de son 1er mot de contenu (défaut masculin)."""
    for w in subject.split():
        wc = w.strip('.,;:').lower()
        if wc and wc not in _FUNCTION_WORDS:
            return GENDER.get(wc.rstrip('sx'), GENDER.get(wc, 'm'))
    return 'm'


def _fix_participles(text: str) -> str:
    """« est cause par » → « est causé par » (accordé au genre du sujet)."""
    def _agree(base: str, gender: str) -> str:
        if base.endswith('ee') or gender == 'm':
            return base
        return base + 'e' if not base.endswith('e') else base + 'e'

    def _replace(m):
        subject, etre, verb = m.group(1), m.group(2), m.group(3)
        base = PARTICIPES.get(verb.lower())
        if not base:
            return m.group(0)
        participle = _agree(base, _subject_gender(subject))
        return f'{subject}{etre} {participle} par'

    return re.sub(
        r'((?:\w[\w-]*\s+){0,4}?)\b(est|sont|etait|etaient)\s+(\w+)\s+par\b',
        _replace, text, flags=re.IGNORECASE)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ACCORD SUJET-VERBE (3e personne)
# ═══════════════════════════════════════════════════════════════════════════════

def _is_plural(word: str) -> bool:
    w = word.lower().rstrip('.,')
    if w in _SINGULAR_S:
        return False
    return w.endswith(('s', 'x')) or w in {w2 for w2, _ in []}


def _fix_verb_agreement(text: str) -> str:
    """
    « traitement des complications permettent » → « traitement des
    complications permet » : la tête du sujet = 1er mot de contenu avant
    le verbe (hors prépositions/déterminants).
    """
    pairs = VERB_PAIRS
    plural_to_sing = {v: k for k, v in pairs.items()}
    singular_to_plural = dict(pairs)

    def _replace(m):
        subject, verb = m.group(1), m.group(2)
        v = verb.lower()
        # Tête du sujet : 1er mot de contenu
        words = subject.split()
        head = None
        for w in reversed(words):  # on cherche en partant du verbe… non :
            break
        for w in words:
            wc = w.strip('.,;:')
            if wc and wc.lower() not in _FUNCTION_WORDS:
                head = wc
                break
        if head is None:
            return m.group(0)
        plural = _is_plural(head)
        if plural and v in singular_to_plural:
            return f'{subject}{singular_to_plural[v]}'
        if not plural and v in plural_to_sing:
            return f'{subject}{plural_to_sing[v]}'
        return m.group(0)

    # Sujet = jusqu'à 6 mots avant le verbe, finissant par un espace
    pattern = re.compile(
        r'((?:\w[\w-]*\s+){1,6}?)(\b(?:'
        + '|'.join(sorted(set(VERB_PAIRS.keys()) | set(VERB_PAIRS.values()),
                          key=len, reverse=True))
        + r')\b)(?=\s|,|\.)')
    return pattern.sub(_replace, text)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ARTICLES MANQUANTS
# ═══════════════════════════════════════════════════════════════════════════════

def _article_for(noun: str, indefinite: bool = False) -> str:
    g = GENDER.get(noun.lower().rstrip('sx'), 'm')
    if indefinite:
        return 'une' if g == 'f' else 'un'
    if g == 'f':
        return 'la' if noun[0].lower() not in _VOWEL else "l'"
    return 'le' if noun[0].lower() not in _VOWEL else "l'"


def _fix_articles(text: str) -> str:
    """Articles manquants en position sujet (début de phrase, après , ou :).

    ⚠️ DOIT tourner AVANT _restore_accents : les clés du lexique sont sans
    accents (« diabete »), le texte non accentué les matche encore.
    """
    nouns = sorted(GENDER, key=len, reverse=True)
    noun_alt = '|'.join(re.escape(n) for n in nouns)

    def _insert(art: str, noun: str) -> str:
        if art.endswith("'"):
            return f'{art}{noun}'
        return f'{art} {noun}'

    def _start(m):
        art = _article_for(m.group(1))
        return _insert(art.capitalize(), m.group(1).lower())

    # a) Début de phrase / après « . ! ? : » : « Paludisme est » → « Le
    #    paludisme est »
    text = re.sub(rf'^({noun_alt})\b', _start, text)
    text = re.sub(rf'(?<=[.!?]\s)({noun_alt})\b', _start, text)
    text = re.sub(rf'(?<=:\s)({noun_alt})\b', _start, text)

    # b) Après virgule ou « que » en position sujet : « , diabete de type 1
    #    est » → « , le diabète de type 1 est » ; « que diabete est » →
    #    « que le diabète est » (1-3 mots entre le nom et le verbe)
    text = re.sub(
        rf'((?:,\s+|\bque\s+))({noun_alt})\b(?=(?:\s+\w+){{1,3}}?\s+(?:est'
        rf'|sont|etait|etaient|permet|permettent|cause|causent|provoque|'
        rf'provoquent|produit|produisent|regule|regulent|contient|contiennent|'
        rf'entraine|entrainent|protege|protegent|transporte|transportent|'
        rf'secrete|secretent|synthetise|synthetisent|neutralise|neutralisent|'
        rf'favorise|favorisent|reduit|reduisent|libere|liberent|devient|'
        rf'deviennent|survient|surviennent|touche|touchent|affecte|affectent|'
        rf'provient|proviennent|indique|indiquent|montre|montrent|explique|'
        rf'expliquent|reste|restent|existe|existent|apparait|apparaissent)\b)',
        lambda m: f'{m.group(1)}{_insert(_article_for(m.group(2)), m.group(2).lower())}',
        text)

    # c) « est/sont + nom nu » → « est un/une + nom » (est parasitose → est
    #    une parasitose)
    def _after_etre(m):
        art = _article_for(m.group(2), indefinite=True)
        return f'{m.group(1)} {_insert(art, m.group(2))}'

    text = re.sub(rf'\b(est|sont)\s+({noun_alt})\b', _after_etre, text)
    return text


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CAPITALISATION + TYPOGRAPHIE
# ═══════════════════════════════════════════════════════════════════════════════

def _fix_capitalization(text: str) -> str:
    """Majuscule en début de phrase et après . ! ?"""
    def _cap(m):
        return m.group(0)[:-1] + m.group(0)[-1].upper()
    text = re.sub(r'(^|[.!?]\s+)([a-zàâäéèêëîïôöùûüç])', _cap, text)
    # Après « : » dans les profils (opener) — majuscule si phrase complète
    text = re.sub(r'(: )([a-zàâäéèêëîïôöùûüç])', lambda m: m.group(0), text)
    return text


def _fix_typography(text: str) -> str:
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\s+', ' ', text)
    # FR : espace AVANT : ; ! ? — jamais avant . et ,
    text = re.sub(r'\s+([,;:!?])', r' \1', text)
    text = re.sub(r'\s+([.,])', r'\1', text)
    # Espace après la ponctuation
    text = re.sub(r'([,.;:!?])(?=\S)', r'\1 ', text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def polish_prose(text: str) -> str:
    """
    Correction complète d'une prose française produite par le système
    harmonique. Déterministe, ~ms, 0 LLM.

    Contrat : seuls les mots fonctionnels sont modifiés/ajoutés — jamais
    le contenu sémantique (un fait reste un fait, mot pour mot).

    Ordre : les passes linguistiques (articles, accord, participe)
    tournent sur le texte BRUT (clés de lexique sans accents), puis la
    restauration des accents et la typographie ferment le pipeline.
    """
    if not text:
        return text
    text = _fix_articles(text)
    text = _fix_contractions(text)
    text = _fix_verb_agreement(text)
    text = _fix_participles(text)
    text = _restore_accents(text)
    text = _fix_capitalization(text)
    text = _fix_typography(text)
    return text


if __name__ == '__main__':
    # Batterie : les défauts RÉELLEMENT observés sur les sorties M4
    tests = [
        # (défaut, corrigé attendu — vérification manuelle)
        "traitement des complications permettent de traiter le diabete",
        "paludisme est parasitose la plus importante et concerne majoritairement les enfants",
        "terme paludisme provient de latin palus",
        "diabete de type 1 est cause par une deficience en insuline",
        "insuline est utilisee pour traiter le diabete",
        "diabete est une maladie chronique caracterisee par un exces de glucose dans le sang",
        "planete orbite autour d une etoile",
        "etoile a neutrons est le residu ultra dense d une supernova",
        "les etudes indiquent que insuline est utilisee pour traiter le diabete",
        "En medecine, la precision du fait est primordiale : diabete est une maladie chronique",
    ]
    for t in tests:
        print(f"IN :  {t}")
        print(f"OUT:  {polish_prose(t)}")
        print()
