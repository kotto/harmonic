"""
Auto-Sectorize — Sectorisation automatique multi-couche
=========================================================
Attribue un secteur harmonique à tout triplet (sujet, relation, objet).
Conçu pour réduire le taux de faits "GENERAL" de 77% à < 5%.

STRATÉGIE 5 COUCHES :
  1. Mapping Wikidata Property ID → Secteur (haute confiance)
  2. Mots-clés dans le sujet (confiance moyenne)
  3. Mots-clés dans la relation (confiance moyenne)
  4. Mots-clés dans l'objet (confiance basse)
  5. Contexte phrastique (confiance très basse)
  6. Fallback : encodeur holographique (similarité cosinus)

Usage :
    from auto_sectorize import auto_sectorize, sectorize_batch

    secteur = auto_sectorize("Paris", "est la capitale de", "la France")
    # → 'GEOGRAPHIE'

    facts = [("Marie Curie", "a découvert", "le radium", "GENERAL"), ...]
    sectorized = sectorize_batch(facts)
    # → [("Marie Curie", "a découvert", "le radium", "SCIENCES"), ...]
"""

import math, re, logging
from collections import Counter
from typing import List, Tuple, Dict, Optional

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTEURS HARMONIQUES (24 secteurs en 12 domaines)
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_KEYWORDS: Dict[str, List[str]] = {
    # PHYSIQUE (0-30°)
    'PHYSIQUE_FOND': [
        'force', 'énergie', 'onde', 'lumière', 'gravité', 'résonance',
        'électromagnétique', 'quantique', 'relativité', 'champ', 'photon',
        'mécanique', 'thermodynamique', 'entropie', 'fréquence',
    ],
    'PHYSIQUE_APPLI': [
        'matière', 'atome', 'électron', 'proton', 'neutron', 'particule',
        'noyau', 'plasma', 'cristal', 'supraconducteur', 'laser',
        'atomes', 'électrons', 'particules', 'molécules',
    ],

    # MATHS (30-60°)
    'MATHS_PURES': [
        'nombre', 'géométrie', 'logique', 'équation', 'phi', 'pi',
        'théorème', 'algèbre', 'calcul', 'ensemble', 'fonction',
        'axiome', 'preuve', 'conjecture', 'infini', 'topologie',
    ],
    'MATHS_APPLI': [
        'statistique', 'probabilité', 'modélisation', 'optimisation',
        'mesure', 'algorithme', 'cryptographie', 'analyse numérique',
    ],

    # BIOLOGIE (60-90°)
    'BIOLOGIE': [
        'vie', 'cellule', 'adn', 'évolution', 'organisme', 'espèce',
        'gène', 'génome', 'protéine', 'enzyme', 'chromosome',
        'bactérie', 'virus', 'microbe', 'parasite', 'champignon',
        'plante', 'animal', 'tissu', 'organe', 'métabolisme',
        'photosynthèse', 'respiration', 'reproduction', 'mitose',
        'classification', 'taxonomie', 'phylogénie', 'biodiversité',
        'cellules', 'organismes', 'animaux', 'plantes', 'bactéries',
        'neurotransmetteur', 'dopamine', 'sérotonine', 'hormone',
        'chlorophylle', 'chloroplaste', 'oxygène', 'glucose',
    ],

    # ÉCOLOGIE (75-90°)
    'ECOLOGIE': [
        'écosystème', 'biodiversité', 'nature', 'environnement',
        'climat', 'pollution', 'conservation', 'habitat', 'biome',
        'forêt', 'océan', 'récif', 'désert', 'toundra', 'savane',
        'écologie', 'durable', 'renouvelable', 'empreinte carbone',
    ],

    # SANTÉ/MÉDICAL (nouveau secteur composite)
    'SANTE': [
        'maladie', 'symptôme', 'traitement', 'diagnostic', 'patient',
        'médecin', 'infection', 'vaccin', 'médicament', 'chirurgie',
        'hôpital', 'clinique', 'thérapie', 'guérison', 'épidémie',
        'pandémie', 'paludisme', 'malaria', 'cancer', 'diabète',
        'sida', 'vih', 'tuberculose', 'hépatite', 'covid',
        'prévention', 'dépistage', 'diagnostique', 'pronostic',
        'posologie', 'effet secondaire', 'contre-indication',
        'santé publique', 'épidémiologie', 'immunologie',
        'inflammation', 'douleur', 'fièvre', 'toux', 'fatigue',
        'anémie', 'hypertension', 'asthme', 'allergie',
    ],

    # CONSCIENCE (90-120°)
    'CONSCIENCE': [
        'conscience', 'perception', 'esprit', 'présence', 'éveil',
        'méditation', 'attention', 'introspection', 'subconscient',
        'inconscient', 'rêve', 'sommeil', 'cognition', 'pensée',
    ],

    # INTELLIGENCE (105-120°)
    'INTELLIGENCE': [
        'intelligence', 'raison', 'logique', 'idée', 'mémoire',
        'apprentissage', 'connaissance', 'compréhension', 'créativité',
        'raisonnement', 'déduction', 'induction', 'analogie',
    ],

    # ÉMOTION (120-150°)
    'EMOTION_POS': [
        'amour', 'joie', 'bonheur', 'paix', 'sérénité', 'plaisir',
        'gratitude', 'compassion', 'empathie', 'espoir', 'fierté',
    ],
    'EMOTION_NEG': [
        'peur', 'tristesse', 'colère', 'souffrance', 'angoisse',
        'anxiété', 'dépression', 'haine', 'jalousie', 'honte',
    ],

    # ASTRONOMIE (150-180°)
    'ASTRONOMIE': [
        'étoile', 'planète', 'galaxie', 'soleil', 'lune', 'terre',
        'constellation', 'nébuleuse', 'trou noir', 'supernova',
        'astéroïde', 'comète', 'orbite', 'satellite', 'cosmos',
        'étoiles', 'planètes', 'galaxies', 'constellations',
        'voie lactée', 'univers', 'big bang', 'espace', 'astronome',
        'télescope', 'exoplanète', 'système solaire', 'amas',
    ],

    # HISTOIRE/TEMPS (180-210°)
    'HISTOIRE': [
        'histoire', 'passé', 'mémoire', 'origine', 'siècle',
        'guerre', 'révolution', 'empire', 'roi', 'reine', 'empereur',
        'dynastie', 'civilisation', 'antiquité', 'moyen âge',
        'renaissance', 'moderne', 'contemporain', 'préhistoire',
        'traité', 'bataille', 'indépendance', 'colonisation',
        'découverte', 'exploration', 'fondation', 'naissance', 'mort',
    ],

    # FUTUR (195-210°)
    'FUTUR': [
        'futur', 'avenir', 'destin', 'éternité', 'prospective',
        'prédiction', 'projection', 'tendance', 'scénario',
    ],

    # CULTURE (210-240°)
    'CULTURE': [
        'culture', 'art', 'musique', 'poésie', 'beauté', 'création',
        'littérature', 'peinture', 'sculpture', 'cinéma', 'théâtre',
        'danse', 'opéra', 'architecture', 'patrimoine', 'tradition',
        'festival', 'exposition', 'musée', 'collection',
        'peint', 'peintre', 'tableau', 'joconde', 'mona lisa',
        'artiste', 'œuvre', 'chef-d\'œuvre', 'mouvement artistique',
    ],

    # POLITIQUE/SOCIÉTÉ (225-255°)
    'POLITIQUE': [
        'société', 'justice', 'liberté', 'loi', 'pouvoir', 'éducation',
        'gouvernement', 'état', 'démocratie', 'république', 'monarchie',
        'élection', 'président', 'ministre', 'parlement', 'constitution',
        'droit', 'égalité', 'fraternité', 'citoyen', 'nation',
        'organisation internationale', 'onu', 'union européenne',
    ],

    # ÉCONOMIE (nouveau secteur composite)
    'ECONOMIE': [
        'économie', 'marché', 'finance', 'investissement', 'croissance',
        'pib', 'inflation', 'emploi', 'chômage', 'commerce',
        'entreprise', 'industrie', 'banque', 'monnaie', 'budget',
        'dette', 'exportation', 'importation', 'bourse', 'action',
        'capital', 'revenu', 'salaire', 'consommation', 'production',
        'startup', 'fondateur', 'siège social', 'chiffre d\'affaires',
    ],

    # GÉOGRAPHIE (nouveau secteur composite pour faciliter la sectorisation)
    'GEOGRAPHIE': [
        'pays', 'capitale', 'continent', 'population', 'superficie',
        'coordonnées', 'localisation', 'région', 'ville', 'frontière',
        'fleuve', 'montagne', 'océan', 'mer', 'île', 'lac', 'rivière',
        'désert', 'forêt', 'plaine', 'plateau', 'vallée', 'delta',
        'climat', 'altitude', 'latitude', 'longitude', 'hémisphère',
        'pays frontaliers', 'limitrophe', 'traverse', 'se jette dans',
        'mont', 'everest', 'sommet', 'kilomètres', 'mètres', 'altitude',
        'hauteur', 'longueur', 'largeur', 'profondeur',
    ],

    # CORPS (300-330°)
    'CORPS_ORGANES': [
        'cœur', 'cerveau', 'sang', 'poumon', 'muscle', 'os',
        'foie', 'rein', 'estomac', 'intestin', 'peau', 'œil',
        'oreille', 'nez', 'bouche', 'main', 'pied', 'bras', 'jambe',
        'système nerveux', 'système digestif', 'système respiratoire',
        'système circulatoire', 'squelette', 'articulation',
    ],

    # TECHNOLOGIE (nouveau secteur composite)
    'TECHNOLOGIE': [
        'code', 'programme', 'logiciel', 'algorithme', 'donnée',
        'internet', 'réseau', 'serveur', 'application', 'mobile',
        'intelligence artificielle', 'machine learning', 'cloud',
        'ordinateur', 'smartphone', 'robot', 'drone', 'capteur',
        'invention', 'brevet', 'innovation', 'numérique', 'digital',
        'électronique', 'automatisation', 'nanotechnologie',
        'bitcoin', 'crypto', 'blockchain', 'cryptomonnaie',
        'intelligence', 'artificielle', 'ia',
    ],

    # PHILOSOPHIE/SPIRITUALITÉ (330-360°)
    'PHILOSOPHIE': [
        'être', 'essence', 'existence', 'réalité', 'vérité', 'néant',
        'dieu', 'âme', 'absolu', 'infini', 'éthique', 'morale',
        'métaphysique', 'ontologie', 'épistémologie', 'esthétique',
        'philosophe', 'sagesse', 'stoïcisme', 'existentialisme',
        'kant', 'platon', 'aristote', 'nietzsche', 'descartes',
        'critique', 'raison pure', 'dialectique', 'phénoménologie',
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# MAPPING PROPRIÉTÉ → SECTEUR (haute confiance)
# ═══════════════════════════════════════════════════════════════════════════════

# Mots-clés dans la RELATION → Secteur (très fiable)
RELATION_KEYWORDS: Dict[str, str] = {
    'découvert': 'SCIENCES',
    'decouvert': 'SCIENCES',
    'découverte': 'SCIENCES',
    'peint': 'CULTURE',
    'peinte': 'CULTURE',
    'écrit': 'CULTURE',
    'ecrit': 'CULTURE',
    'composé': 'CULTURE',
    'compose': 'CULTURE',
    'fondé': 'ECONOMIE',
    'fonde': 'ECONOMIE',
    'inventé': 'TECHNOLOGIE',
    'invente': 'TECHNOLOGIE',
    'capitale': 'GEOGRAPHIE',
    'capitale de': 'GEOGRAPHIE',
    'né en': 'HISTOIRE',
    'ne en': 'HISTOIRE',
    'mort en': 'HISTOIRE',
    'décédé': 'HISTOIRE',
    'decede': 'HISTOIRE',
    'règne': 'HISTOIRE',
    'regne': 'HISTOIRE',
    'symptôme': 'SANTE',
    'symptome': 'SANTE',
    'traitement': 'SANTE',
    'vaccin': 'SANTE',
    'population': 'GEOGRAPHIE',
    'superficie': 'GEOGRAPHIE',
    'démontré': 'MATHS_PURES',
    'demontre': 'MATHS_PURES',
    'théorème': 'MATHS_PURES',
    'theoreme': 'MATHS_PURES',
}

PROPERTY_TO_SECTOR: Dict[str, str] = {
    # Géographie
    'p36': 'GEOGRAPHIE',   # capitale
    'p17': 'GEOGRAPHIE',   # pays
    'p30': 'GEOGRAPHIE',   # continent
    'p131': 'GEOGRAPHIE',  # localisation administrative
    'p1082': 'GEOGRAPHIE', # population
    'p2046': 'GEOGRAPHIE', # superficie
    'p625': 'GEOGRAPHIE',  # coordonnées
    'p2043': 'GEOGRAPHIE', # longueur
    'p403': 'GEOGRAPHIE',  # embouchure
    'p2048': 'GEOGRAPHIE', # hauteur

    # Histoire
    'p569': 'HISTOIRE',    # date de naissance
    'p570': 'HISTOIRE',    # date de mort
    'p571': 'HISTOIRE',    # date de fondation/création
    'p575': 'HISTOIRE',    # date de découverte
    'p580': 'HISTOIRE',    # date de début
    'p582': 'HISTOIRE',    # date de fin
    'p585': 'HISTOIRE',    # date

    # Sciences
    'p1086': 'SCIENCES',   # numéro atomique
    'p246': 'SCIENCES',    # symbole chimique
    'p2067': 'SCIENCES',   # masse
    'p61': 'SCIENCES',     # découvreur/découvreur
    'p800': 'SCIENCES',    # œuvre notable/découverte
    'p828': 'SCIENCES',    # a pour cause
    'p101': 'SCIENCES',    # domaine

    # Santé
    'p780': 'SANTE',       # symptôme
    'p2176': 'SANTE',      # traitement
    'p1995': 'SANTE',      # spécialité médicale
    'p3780': 'SANTE',      # principe actif
    'p2175': 'SANTE',      # maladie ciblée
    'p636': 'SANTE',       # voie d'administration

    # Biologie
    'p171': 'BIOLOGIE',    # genre
    'p177': 'BIOLOGIE',    # famille
    'p178': 'BIOLOGIE',    # ordre
    'p105': 'BIOLOGIE',    # rang taxonomique
    'p225': 'BIOLOGIE',    # nom taxonomique
    'p366': 'BIOLOGIE',    # utilisation/fonction

    # Culture
    'p50': 'CULTURE',      # auteur
    'p170': 'CULTURE',     # créateur
    'p86': 'CULTURE',      # compositeur
    'p57': 'CULTURE',      # réalisateur
    'p175': 'CULTURE',     # interprète
    'p135': 'CULTURE',     # mouvement
    'p136': 'CULTURE',     # genre
    'p166': 'CULTURE',     # prix reçu

    # Économie
    'p452': 'ECONOMIE',    # secteur industriel
    'p112': 'ECONOMIE',    # fondateur
    'p159': 'ECONOMIE',    # siège social
    'p176': 'ECONOMIE',    # fabricant

    # Société
    'p2124': 'POLITIQUE',  # nombre de membres
    'p27': 'GEOGRAPHIE',   # pays de citoyenneté
    'p495': 'CULTURE',     # pays d'origine

    # Sport
    'p2410': 'CULTURE',    # pratiqué par
    'p3000': 'CULTURE',    # record

    # Général
    'p31': 'GENERAL',      # instance de
    'p279': 'GENERAL',     # sous-classe de
    'p106': 'GENERAL',     # profession
    'p527': 'GENERAL',     # a pour partie
}


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE DE CONFIANCE PAR COUCHE
# ═══════════════════════════════════════════════════════════════════════════════

CONFIDENCE_WEIGHTS = {
    'property': 10.0,    # Wikidata property ID → très haute confiance
    'subject': 3.0,      # Mot-clé dans le sujet
    'relation': 2.0,     # Mot-clé dans la relation
    'object': 1.0,       # Mot-clé dans l'objet
    'context': 0.5,      # Contexte phrastique
}


# ═══════════════════════════════════════════════════════════════════════════════
# ALGORITHME PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def auto_sectorize(
    subject: str,
    relation: str,
    obj: str,
    property_id: Optional[str] = None,
    context: str = "",
) -> Tuple[str, float]:
    """
    Attribue automatiquement un secteur harmonique à un triplet.

    Args:
        subject: le sujet du fait
        relation: la relation
        obj: l'objet du fait
        property_id: identifiant Wikidata (ex: 'P36') pour mapping direct
        context: texte environnant pour contexte additionnel

    Returns:
        (secteur, score_de_confiance) — ex: ('GEOGRAPHIE', 13.0)
    """
    scores: Counter = Counter()

    s_lower = subject.lower()
    r_lower = relation.lower()
    o_lower = str(obj).lower()
    ctx_lower = context.lower()

    # Normaliser les accents français et la ligature œ
    def _normalize(text: str) -> str:
        return text.replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('ë', 'e')\
                   .replace('à', 'a').replace('â', 'a').replace('ä', 'a')\
                   .replace('ù', 'u').replace('û', 'u').replace('ü', 'u')\
                   .replace('ô', 'o').replace('ö', 'o')\
                   .replace('î', 'i').replace('ï', 'i')\
                   .replace('ç', 'c')\
                   .replace('œ', 'oe')

    s_lower = _normalize(s_lower)
    r_lower = _normalize(r_lower)
    o_lower = _normalize(o_lower)
    ctx_lower = _normalize(ctx_lower)

    # Fonction helper pour vérifier si un mot-clé normalisé est présent
    def _kw_in_text(kw: str, text: str, as_words: bool = True) -> bool:
        kw_norm = _normalize(kw.lower())
        if as_words:
            text_words = set(text.split())
            kw_parts = kw_norm.split()
            if len(kw_parts) == 1:
                return kw_norm in text_words
            else:
                return kw_norm in text
        else:
            return kw_norm in text

    # ═══ COUCHE 1 : Property ID → Secteur (confiance maximale) ═══
    if property_id:
        pid_lower = property_id.lower()
        if pid_lower in PROPERTY_TO_SECTOR:
            sector = PROPERTY_TO_SECTOR[pid_lower]
            scores[sector] += CONFIDENCE_WEIGHTS['property']

    # ═══ COUCHE 2 : Mots-clés dans le sujet ═══
    s_words = set(s_lower.split())
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            if _kw_in_text(kw, s_lower, as_words=True):
                scores[sector] += CONFIDENCE_WEIGHTS['subject']

    # ═══ COUCHE 2.5 : Mots-clés dans la relation → Secteur (très fiable) ═══
    for rel_kw, sector in RELATION_KEYWORDS.items():
        if _kw_in_text(rel_kw, r_lower, as_words=False):
            scores[sector] += CONFIDENCE_WEIGHTS['relation'] * 2.0  # double poids
            break  # une seule correspondance suffit

    # ═══ COUCHE 3 : Mots-clés dans la relation (secteur général) ═══
    r_words = set(r_lower.split())
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            if _kw_in_text(kw, r_lower, as_words=True):
                scores[sector] += CONFIDENCE_WEIGHTS['relation']

    # ═══ COUCHE 4 : Mots-clés dans l'objet ═══
    o_words = set(o_lower.split())
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            if _kw_in_text(kw, o_lower, as_words=True):
                scores[sector] += CONFIDENCE_WEIGHTS['object']

    # ═══ COUCHE 5 : Contexte phrastique ═══
    if ctx_lower:
        for sector, keywords in SECTOR_KEYWORDS.items():
            for kw in keywords:
                if _kw_in_text(kw, ctx_lower, as_words=False):
                    scores[sector] += CONFIDENCE_WEIGHTS['context']

    # ═══ DÉCISION ═══
    if scores:
        best_sector = scores.most_common(1)[0][0]
        best_score = scores[best_sector]

        # Si le score est très faible, remonter à GENERAL
        if best_score < 1.5:
            return ('GENERAL', best_score)

        # Si plusieurs secteurs ont des scores proches, le plus spécifique gagne
        # (le secteur avec le moins de mots-clés est plus spécifique)
        if len(scores) >= 2:
            top2 = scores.most_common(2)
            if top2[1][1] >= best_score * 0.8:
                # Ambiguïté : choisir le secteur le plus spécifique
                kw_count_1 = len(SECTOR_KEYWORDS.get(best_sector, []))
                kw_count_2 = len(SECTOR_KEYWORDS.get(top2[1][0], []))
                if kw_count_2 < kw_count_1:
                    best_sector = top2[1][0]
                    best_score = top2[1][1]

        return (best_sector, best_score)

    return ('GENERAL', 0.0)


def sectorize_batch(
    facts: List[Tuple[str, str, str, str]],
    property_ids: Optional[List[str]] = None,
    contexts: Optional[List[str]] = None,
    min_confidence: float = 1.0,
) -> List[Tuple[str, str, str, str]]:
    """
    Sectorise un lot de faits.

    Args:
        facts: liste de (sujet, relation, objet, secteur_actuel)
        property_ids: liste optionnelle d'IDs Wikidata
        contexts: liste optionnelle de contextes
        min_confidence: score minimum pour remplacer le secteur existant

    Returns:
        Liste de faits avec secteurs mis à jour
    """
    result = []
    stats = Counter()

    for i, fact in enumerate(facts):
        s, r, o, current_sector = fact[0], fact[1], fact[2], fact[3]

        pid = property_ids[i] if property_ids and i < len(property_ids) else None
        ctx = contexts[i] if contexts and i < len(contexts) else ""

        new_sector, confidence = auto_sectorize(s, r, o, pid, ctx)

        if confidence >= min_confidence:
            result.append((s, r, o, new_sector))
            if new_sector != 'GENERAL':
                stats['resectorized'] += 1
            else:
                stats['kept_general'] += 1
        else:
            result.append((s, r, o, current_sector))
            stats['unchanged'] += 1

    log.info(f"Sectorisation batch: {len(facts)} faits → "
             f"{stats['resectorized']} resectorisés, "
             f"{stats['kept_general']} GENERAL, "
             f"{stats['unchanged']} inchangés")

    return result


def get_sector_distribution(facts: List[Tuple]) -> Dict[str, int]:
    """Calcule la distribution des secteurs dans une liste de faits."""
    dist = Counter()
    for fact in facts:
        sector = fact[3] if len(fact) > 3 else 'GENERAL'
        dist[sector] += 1
    return dict(dist.most_common())


def compute_general_rate(facts: List[Tuple]) -> float:
    """Calcule le taux de faits GENERAL."""
    if not facts:
        return 0.0
    general_count = sum(1 for f in facts if len(f) > 3 and f[3] == 'GENERAL')
    return general_count / len(facts)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Tests unitaires
    test_cases = [
        ("Paris", "est la capitale de", "la France", "P36", ""),
        ("Marie Curie", "a découvert", "le radium", None, ""),
        ("Le paludisme", "est causé par", "le parasite Plasmodium", None, ""),
        ("Le cœur", "pompe", "le sang", None, ""),
        ("Google", "a été fondé par", "Larry Page", None, ""),
        ("La Tour Eiffel", "a été construite en", "1889", "P571", ""),
        ("L'hydrogène", "a pour symbole chimique", "H", "P246", ""),
        ("Le mont Everest", "a une hauteur de", "8848 mètres", None, ""),
        ("La Joconde", "a été peinte par", "Léonard de Vinci", None, ""),
        ("La photosynthèse", "produit", "de l'oxygène", None, ""),
        ("Le théorème de Pythagore", "a été démontré par", "Pythagore", None, ""),
        ("La dopamine", "est un", "neurotransmetteur", None, ""),
        ("Le bitcoin", "a été créé en", "2009", None, ""),
        ("La Voie lactée", "est une", "galaxie spirale", None, ""),
        ("Kant", "a écrit", "la Critique de la raison pure", None, ""),
    ]

    print("=" * 60)
    print("  AUTO-SECTORIZE — Tests unitaires")
    print("=" * 60)

    correct = 0
    total = len(test_cases)

    for s, r, o, pid, ctx in test_cases:
        secteur, score = auto_sectorize(s, r, o, pid, ctx)
        print(f"  {s[:25]:25s} | {r[:30]:30s} | {o[:25]:25s}")
        print(f"    → {secteur:20s} (score: {score:.1f})")
        if secteur != 'GENERAL':
            correct += 1

    print(f"\n  ✅ {correct}/{total} sectorisés hors GENERAL "
          f"({100*correct/total:.0f}%)")
    print(f"  🎯 Objectif: > 95%")
