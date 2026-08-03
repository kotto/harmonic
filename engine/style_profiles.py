#!/usr/bin/env python3
"""
style_profiles.py — Voix ondulatoires par hologramme (style = motif de phase)
=============================================================================

Correspondance ondulatoire (TRADUCTION_ONDULATOIRE_LLM.md §7.2) :
    LLM : LoRA / fine-tuning style → un adaptateur de poids par style
    Harmonique : un style_profile = OPÉRATEUR déterministe (templates +
    connecteurs + registre + motif de phase) — PAS d'entraînement.

Un LLM classique génère style+contenu ensemble (le style émerge de la
distribution apprise). Ici le style est une VOIX appliquée aux faits
vérifiés par le gate M4 : opener → faits reliés par les connecteurs du
profil → closer. La précision est intacte (jamais un mot hors des faits),
la voix est spécifique à l'hologramme élu.

Chaque profil :
  - name / registre (formel|courant|familier)
  - openers / closers  (templates avec {sujet})
  - connectors        (entre faits — style du domaine)
  - single            (structure d'un fait isolé)
  - section_intro / section_dev / section_conclusion  (multi-paragraphes)
"""

import re

# ═══════════════════════════════════════════════════════════════════════════════
# PROFILS DE VOIX (par domaine d'hologramme)
# ═══════════════════════════════════════════════════════════════════════════════

STYLE_PROFILES = {
    'medecine': {
        'name': 'Précision clinique',
        'registre': 'formel',
        'openers': [
            "Sur le plan médical, voici ce qu'il faut retenir :",
            "Les données médicales établies indiquent ceci :",
            "En médecine, la précision du fait est primordiale :",
        ],
        'connectors': [
            "Cliniquement, ",
            "Sur le plan physiologique, ",
            "Les études indiquent que ",
            "Il est établi que ",
            "À ce sujet, ",
        ],
        'closers': [
            " Telle est la position médicale documentée.",
            " Voilà l'essentiel du tableau clinique.",
        ],
        'single': [
            "{S} {r} {o}.",
            "Il faut savoir que {s} {r} {o}.",
        ],
        'section_intro': [
            "Pour comprendre {sujet}, commençons par un fait clinique fondamental :",
        ],
        'section_dev': [
            "Le mécanisme se précise :",
            "Approfondissons :",
        ],
        'section_conclusion': [
            "En conclusion, le tableau clinique de {sujet} repose sur ces faits établis.",
        ],
    },
    'sciences': {
        'name': 'Rigueur scientifique',
        'registre': 'formel',
        'openers': [
            "Le point scientifique est le suivant :",
            "D'un point de vue scientifique :",
            "Les faits établis par la recherche indiquent :",
        ],
        'connectors': [
            "Ceci implique que ",
            "Par voie de conséquence, ",
            "La physique nous enseigne que ",
            "Il résulte de ces observations que ",
        ],
        'closers': [
            " Telle est la conclusion des observations.",
            " C'est ce que l'expérience confirme.",
        ],
        'single': [
            "{S} {r} {o}.",
            "On observe que {s} {r} {o}.",
        ],
        'section_intro': [
            "Pour aborder {sujet}, partons d'une observation première :",
        ],
        'section_dev': [
            "Le raisonnement se déploie :",
            "Les mécanismes en jeu :",
        ],
        'section_conclusion': [
            "En synthèse, {sujet} s'explique par l'enchaînement de ces faits.",
        ],
    },
    'histoire': {
        'name': 'Narration historique',
        'registre': 'courant',
        'openers': [
            "L'histoire nous apprend que :",
            "Retournons dans le passé :",
            "Les faits historiques sont clairs :",
        ],
        'connectors': [
            "Ensuite, ",
            "À cette époque, ",
            "Plus tard, ",
            "Les chroniques rapportent que ",
        ],
        'closers': [
            " C'est ainsi que l'histoire s'est écrite.",
            " Voilà ce que retient la mémoire collective.",
        ],
        'single': [
            "{S} {r} {o}.",
            "Les archives nous disent que {s} {r} {o}.",
        ],
        'section_intro': [
            "Pour comprendre {sujet}, il faut remonter le fil du temps :",
        ],
        'section_dev': [
            "Le récit se poursuit :",
            "Dans la continuité des événements, ",
        ],
        'section_conclusion': [
            "Au terme de ce parcours historique, {sujet} se comprend par cette chaîne d'événements.",
        ],
    },
    'philosophie': {
        'name': 'Contemplation philosophique',
        'registre': 'courant',
        'openers': [
            "La pensée se pose ainsi :",
            "Considérons cette question avec soin :",
            "La philosophie éclaire ce point :",
        ],
        'connectors': [
            "Or, ",
            "Il faut alors considérer que ",
            "Cela conduit la réflexion vers ",
            "La raison nous montre que ",
        ],
        'closers': [
            " Telle est la lumière que la raison apporte.",
            " C'est là l'enseignement que la pensée en retire.",
        ],
        'single': [
            "{S} {r} {o}.",
            "On peut affirmer que {s} {r} {o}.",
        ],
        'section_intro': [
            "Abordons {sujet} par une première méditation :",
        ],
        'section_dev': [
            "La réflexion s'approfondit :",
            "Considérons maintenant ",
        ],
        'section_conclusion': [
            "En dernière analyse, {sujet} se révèle à travers ces considérations.",
        ],
    },
    'art': {
        'name': 'Sensibilité artistique',
        'registre': 'courant',
        'openers': [
            "L'art nous parle ainsi :",
            "Du point de vue de la création :",
            "La sensibilité artistique retient ceci :",
        ],
        'connectors': [
            "Et l'œuvre continue : ",
            "La création enchaîne : ",
            "L'inspiration nous mène à ",
            "Sous ce rapport, ",
        ],
        'closers': [
            " C'est la trace que l'art laisse.",
            " Voilà ce que l'émotion retient.",
        ],
        'single': [
            "{S} {r} {o}.",
            "L'œuvre nous dit que {s} {r} {o}.",
        ],
        'section_intro': [
            "Pour goûter {sujet}, commençons par une première sensation :",
        ],
        'section_dev': [
            "La beauté se déploie :",
            "Les formes s'enchaînent : ",
        ],
        'section_conclusion': [
            "Au final, {sujet} se donne à voir dans l'unité de ces traits.",
        ],
    },
    'sport': {
        'name': 'Dynamique sportive',
        'registre': 'courant',
        'openers': [
            "Côté sport, retenons ceci :",
            "Sur le terrain des faits :",
            "La performance se résume ainsi :",
        ],
        'connectors': [
            "Ensuite, ",
            "Dans l'effort, ",
            "Les performances montrent que ",
        ],
        'closers': [
            " Voilà l'essentiel de la performance.",
            " C'est ce que le sport nous apprend.",
        ],
        'single': [
            "{S} {r} {o}.",
            "Sur le plan sportif, {s} {r} {o}.",
        ],
        'section_intro': [
            "Pour entrer dans {sujet}, un premier fait :",
        ],
        'section_dev': [
            "L'action s'intensifie :",
            "Dans la continuité, ",
        ],
        'section_conclusion': [
            "En conclusion sportive, {sujet} tient en ces faits.",
        ],
    },
    'general': {
        'name': 'Clarté harmonique',
        'registre': 'courant',
        'openers': [
            "Voici l'essentiel :",
            "Pour faire simple :",
            "Le point central est le suivant :",
        ],
        'connectors': [
            "De plus, ",
            "Par ailleurs, ",
            "En particulier, ",
            "Ensuite, ",
        ],
        'closers': [
            " Voilà l'essentiel.",
            " C'est l'essentiel à retenir.",
        ],
        'single': [
            "{S} {r} {o}.",
            "Il faut savoir que {s} {r} {o}.",
        ],
        'section_intro': [
            "Pour comprendre {sujet}, commençons par l'essentiel :",
        ],
        'section_dev': [
            "Approfondissons :",
            "Ensuite, ",
        ],
        'section_conclusion': [
            "En résumé, {sujet} repose sur ces points essentiels.",
        ],
    },
}

# Mapping secteur → profil de voix (résolution automatique par hologramme)
SECTOR_TO_PROFILE = {
    'SANTE': 'medecine', 'CORPS_SANTE': 'medecine', 'CORPS_ORGANES': 'medecine',
    'BIOLOGIE': 'sciences', 'PHYSIQUE_FOND': 'sciences', 'PHYSIQUE_APPLI': 'sciences',
    'MATHS_PURES': 'sciences', 'MATHS_APPLI': 'sciences', 'ASTRONOMIE': 'sciences',
    'COSMOLOGIE': 'sciences', 'ECOLOGIE': 'sciences', 'NATURE_VEGET': 'sciences',
    'NATURE_ANIM': 'sciences', 'TECHNOLOGIE': 'sciences',
    'PASSE': 'histoire', 'FUTUR': 'histoire', 'HISTOIRE': 'histoire',
    'METAPHYSIQUE': 'philosophie', 'SPIRITUALITE': 'philosophie',
    'CONSCIENCE': 'philosophie', 'INTELLIGENCE': 'philosophie',
    'CREATION': 'art', 'EXPRESSION': 'art', 'CULTURE': 'art',
    'EMOTION_POS': 'art', 'EMOTION_NEG': 'art',
    'SPORT': 'sport', 'CORPS_SENS': 'sport',
}

# Voix explicites pour les hologrammes personnels spécialisés
INTEREST_TO_PROFILE = {
    'diabete': 'medecine', 'cancer': 'medecine', 'paludisme': 'medecine',
    'coeur': 'medecine', 'sang': 'medecine', 'vaccin': 'medecine',
    'grippe': 'medecine', 'hypertension': 'medecine', 'anemie': 'medecine',
    'nutrition': 'medecine', 'alimentation': 'medecine', 'antibiotique': 'medecine',
    'biologie': 'sciences', 'physique': 'sciences', 'mathematiques': 'sciences',
    'astronomie': 'sciences', 'ecologie': 'sciences', 'technologie': 'sciences',
    'histoire': 'histoire', 'philosophie': 'philosophie', 'psychologie': 'philosophie',
    'cerveau': 'sciences', 'musique': 'art', 'sport': 'sport',
    'informatique': 'sciences', 'economie': 'sciences', 'droit': 'histoire',
    'geographie': 'histoire',
}

DEFAULT_PROFILE = 'general'


def resolve_profile(holo_meta) -> str:
    """
    Voix d'un hologramme : style explicite (meta.style) sinon résolution
    par intérêt (personal_*) puis par secteurs dominants.
    """
    style = getattr(holo_meta, 'style', None)
    if style and style != 'auto' and style in STYLE_PROFILES:
        return style
    holo_id = getattr(holo_meta, 'id', '') or ''
    # Intérêt explicite des hologrammes personnels
    for interest, profile in INTEREST_TO_PROFILE.items():
        if interest in holo_id.lower():
            return profile
    # Secteurs dominants du registre
    sectors = getattr(holo_meta, 'sectors', None) or []
    votes = {}
    for sec in sectors:
        p = SECTOR_TO_PROFILE.get(str(sec).upper())
        if p:
            votes[p] = votes.get(p, 0) + 1
    if votes:
        return max(votes, key=votes.get)
    return DEFAULT_PROFILE


def get_profile(holo_meta) -> dict:
    return STYLE_PROFILES.get(resolve_profile(holo_meta), STYLE_PROFILES[DEFAULT_PROFILE])


# ═══════════════════════════════════════════════════════════════════════════════
# RENDU ONDULATOIRE — faits vérifiés → prose stylée
# ═══════════════════════════════════════════════════════════════════════════════

def _capitalize(t: str) -> str:
    t = t.strip()
    return t[0].upper() + t[1:] if t else t


def _fact_str(fact) -> str:
    s, r, o = str(fact[0]).strip(), str(fact[1]).strip(), str(fact[2]).strip()
    # Nettoyage des artefacts (« 40. **titre** », « (source: ... »)
    s = re.sub(r'^\d+\.\s*\**\s*', '', s)
    o = re.sub(r'\s*\(source:.*$', '', o)
    return s, r, o


def _is_logical_chain(facts, min_links: float = 0.5) -> bool:
    """Chaîne si l'objet d'un fait partage un mot avec le sujet du suivant."""
    if len(facts) < 2:
        return False
    links = 0
    for i in range(len(facts) - 1):
        o_words = set(re.findall(r"[a-zàâäéèêëîïôöùûüç]{3,}", str(facts[i][2]).lower()))
        s_words = set(re.findall(r"[a-zàâäéèêëîïôöùûüç]{3,}", str(facts[i + 1][0]).lower()))
        if o_words & s_words:
            links += 1
    return links >= (len(facts) - 1) * min_links


def render_facts(facts, question: str = '', profile: dict = None,
                 depth: str = 'standard', personality: str = 'ka') -> str:
    """
    Rendu stylé des faits vérifiés (voie M4).

    depth:
      'court'     — 1-3 faits, phrases simples
      'standard'  — chaîne logique (si détectée) ou collection connectée
      'détaillé'  — multi-paragraphes (intro / développement / conclusion)

    Le style est un OPÉRATEUR : aucun mot n'est ajouté hors des faits.
    """
    import random
    profile = profile or STYLE_PROFILES[DEFAULT_PROFILE]
    facts = [f for f in facts if str(f[0]).strip()][:6]
    if not facts:
        return ''

    sujet = question.strip(' ?.!')[:60] if question else str(facts[0][0])[:40]

    # Nettoyer les faits
    clean = []
    for f in facts:
        s, r, o = _fact_str(f)
        if s:
            clean.append((s, r, o))

    def _render_single(fact) -> str:
        s, r, o = fact
        tpl = random.choice(profile['single'])
        return tpl.format(S=_capitalize(s), s=s, r=r, o=o.rstrip('.'))

    def _plain(fact) -> str:
        """Fait en forme simple — la voix est portée par le connecteur."""
        s, r, o = fact
        return f"{_capitalize(s)} {r} {o.rstrip('.')}."

    def _conn(role: str = 'connectors') -> str:
        """Connecteur du profil, formaté (espace propre)."""
        return random.choice(profile.get(role, profile['connectors'])).strip()

    # ── COURT : phrases simples ───────────────────────────────────────────
    if depth == 'court':
        return ' '.join(_render_single(f) for f in clean[:3])

    # ── DÉTAILLÉ : multi-paragraphes (intro / dev / conclusion) ───────────
    if depth == 'détaillé' and len(clean) >= 3:
        half = max(1, len(clean) // 2)
        p1, p2 = clean[:half], clean[half:]
        para1 = _conn('section_intro').format(sujet=sujet) + ' ' + _render_single(p1[0])
        for f in p1[1:]:
            para1 += ' ' + _conn() + ' ' + _plain(f)[0].lower() + _plain(f)[1:]
        para2 = _conn('section_dev').format(sujet=sujet) + ' '
        para2 += ' '.join(_conn() + ' ' + _plain(f)[0].lower() + _plain(f)[1:] for f in p2)
        para3 = _conn('section_conclusion').format(sujet=sujet)
        return '\n\n'.join([para1, para2, para3])

    # ── STANDARD : chaîne logique ou collection connectée ─────────────────
    if len(clean) == 1:
        return _render_single(clean[0])

    opener = _conn('openers').format(sujet=sujet)
    if _is_logical_chain(clean):
        # Chaîne : connecteurs causaux du profil entre faits
        parts = [opener + ' ' + _render_single(clean[0])]
        for f in clean[1:]:
            parts.append(_conn() + ' ' + _plain(f)[0].lower() + _plain(f)[1:])
        text = ' '.join(parts)
    else:
        # Collection : connecteurs du profil entre faits
        parts = [opener + ' ' + _render_single(clean[0])]
        for f in clean[1:]:
            parts.append(_conn() + ' ' + _plain(f)[0].lower() + _plain(f)[1:])
        text = ' '.join(parts)

    closer = random.choice(profile['closers'])
    if text and not text.rstrip().endswith(('!', '?', '…')):
        text = text.rstrip() + closer
    # Nettoyage : points multiples des faits sources (« sang.. » → « sang. »)
    text = re.sub(r'\.{2,}', '.', text)
    return text


def profile_of(holo_meta) -> dict:
    """Convenience : profil de voix d'un hologramme (meta registre)."""
    return get_profile(holo_meta)


if __name__ == '__main__':
    # Test rapide
    import logging
    logging.basicConfig(level=logging.WARNING)
    facts = [
        ('diabete', 'est', 'une maladie chronique caracterisee par un exces de glucose dans le sang', 'SANTE'),
        ('diabete de type 1', 'est cause par', 'une deficience en insuline', 'SANTE'),
        ('diabete de type 2', 'est cause par', 'une resistance a l insuline', 'SANTE'),
        ('insuline', 'est utilisee pour', 'traiter le diabete', 'SANTE'),
    ]
    print("=== STANDARD (médecine) ===")
    print(render_facts(facts, 'Qu est-ce que le diabete ?',
                       STYLE_PROFILES['medecine'], 'standard'))
    print("\n=== DÉTAILLÉ (médecine) ===")
    print(render_facts(facts, 'Qu est-ce que le diabete ?',
                       STYLE_PROFILES['medecine'], 'détaillé'))
    print("\n=== COURT (general) ===")
    print(render_facts(facts[:2], 'diabete', STYLE_PROFILES['general'], 'court'))
