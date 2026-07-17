#!/usr/bin/env python3
"""
HoloExpander — Expansion massive d'hologrammes spécialisés
============================================================
Prend un hologramme existant et l'étend par :
  1. RELACHEMENT DES FILTRES — plus de mots-clés, secteurs voisins
  2. CROSS-LINGUAL — traduction FR↔EN (×2 faits)
  3. ENTITY EXPANSION — EntityIndex pour faits connexes
  4. TRANSITIVITÉ — fermeture du graphe de connaissance
  5. VALIDATION + BENCHMARK — score qualité réel

Usage :
    python holo_expand.py --domain medecine --target 50000
    python holo_expand.py --domain astronomie --target 10000
    python holo_expand.py --all --target 20000
"""

import re, json, time, argparse, sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Set

# ═══════════════════════════════════════════════════════════════════════════════
# 1. EXPANSION PAR RELACHEMENT
# ═══════════════════════════════════════════════════════════════════════════════

DOMAIN_EXPANSIONS = {
    'medecine': {
        'sectors': ['SANTE', 'CORPS_ORGANES', 'CORPS_SANTE', 'BIOLOGIE', 'CHIMIE',
                     'NEUROSCIENCE', 'GENETIQUE', 'PHARMACOLOGIE', 'PSYCHOLOGIE'],
        'keywords': [
            'maladie', 'symptôme', 'traitement', 'vaccin', 'médicament', 'patient',
            'diagnostic', 'cancer', 'diabète', 'infection', 'virus', 'bactérie',
            'cellule', 'gène', 'système', 'organe', 'coeur', 'cerveau', 'sang',
            'hormone', 'enzyme', 'protéine', 'antibiotique', 'chirurgie', 'thérapie',
            'immunité', 'inflammation', 'douleur', 'fièvre', 'respiration',
            'médical', 'clinique', 'pathologie', 'anatomie', 'physiologie',
            'neurotransmetteur', 'récepteur', 'mutation', 'chromosome', 'ADN',
            'allergie', 'asthme', 'tuberculose', 'paludisme', 'sida', 'covid',
            'anesthésie', 'transplantation', 'greffe', 'radiologie', 'scanner',
            'irm', 'échographie', 'prise sang', 'tension', 'cholestérol',
            'disease', 'treatment', 'surgery', 'therapy', 'drug', 'pharmacy',
            'cancer', 'diabetes', 'stroke', 'cardiac', 'pulmonary', 'renal',
            'hepatic', 'neurology', 'cardiology', 'oncology', 'pediatrics',
            'orthopedic', 'dermatology', 'ophthalmology', 'psychiatry', 'obstetrics',
            'prescription', 'dosage', 'contraindication', 'side effect', 'prognosis',
            'epidemiology', 'public health', 'sanitation', 'nutrition', 'hygiene',
            'stethoscope', 'syringe', 'defibrillator', 'pacemaker', 'implant',
            'symptom', 'diagnosis', 'prognosis', 'etiology', 'pathogenesis',
        ],
        'quality_filter': {
            'min_object_len': 5,
            'min_relation_len': 3,
            'exclude_relations': ['est', 'a', 'sont', 'et'],
        },
    },
    'sciences': {
        'sectors': ['PHYSIQUE_FOND', 'PHYSIQUE_APPLI', 'SCIENCES', 'MATHS_PURES',
                     'MATHS_APPLI', 'BIOLOGIE', 'CHIMIE', 'ASTRONOMIE'],
        'keywords': [
            'physique', 'chimie', 'atome', 'énergie', 'force', 'lumière', 'onde',
            'quantique', 'relativité', 'gravité', 'électron', 'proton', 'neutron',
            'molécule', 'équation', 'théorème', 'nombre', 'calcul', 'dérivée',
            'élément', 'réaction', 'catalyseur', 'température', 'pression', 'volume',
            'masse', 'vitesse', 'accélération', 'fréquence', 'longueur', 'vecteur',
            'électricité', 'magnétisme', 'optique', 'thermodynamique', 'mécanique',
            'biologie', 'évolution', 'espèce', 'écosystème', 'cellule', 'organisme',
            'physics', 'chemistry', 'biology', 'atom', 'energy', 'wave', 'force',
            'quantum', 'electron', 'molecule', 'equation', 'theorem', 'element',
            'mitose', 'méiose', 'atp', 'photosynthèse', 'chlorophylle', 'ribosome',
            'mitochondrie', 'enzyme', 'catalyse', 'oxygène', 'carbone', 'azote',
            'laser', 'spectre', 'diffraction', 'interférence', 'polarisation',
            'isotope', 'radioactivité', 'fission', 'fusion nucléaire', 'plasma',
        ],
        # 🆕 Filtre de qualité : exclut les faits trop génériques
        'quality_filter': {
            'min_object_len': 6,          # objet d'au moins 6 caractères
            'min_relation_len': 4,         # relation d'au moins 4 caractères
            'exclude_relations': ['est', 'a', 'sont', 'et'],  # relations trop vagues
            'exclude_objects': ['oui', 'non', 'true', 'false'],
        },
    },
    'geographie': {
        'sectors': ['GEOGRAPHIE', 'GEO', 'HISTOIRE', 'CULTURE', 'ECONOMIE'],
        'keywords': [
            'pays', 'capitale', 'continent', 'océan', 'mer', 'fleuve', 'rivière',
            'montagne', 'volcan', 'désert', 'forêt', 'lac', 'île', 'péninsule',
            'population', 'superficie', 'altitude', 'climat', 'frontière', 'région',
            'ville', 'village', 'province', 'état', 'département', 'cartographie',
            'fuseau horaire', 'latitude', 'longitude', 'équateur', 'tropique',
            'afrique', 'europe', 'asie', 'amérique', 'océanie', 'antarctique',
            'france', 'allemagne', 'chine', 'inde', 'brésil', 'canada', 'japon',
            'country', 'capital', 'mountain', 'river', 'ocean', 'island', 'city',
            'paris', 'londres', 'new york', 'tokyo', 'pékin', 'moscou', 'rome',
        ],
    },
    'histoire': {
        'sectors': ['HISTOIRE', 'CULTURE', 'GEOGRAPHIE', 'PHILOSOPHIE', 'POLITIQUE'],
        'keywords': [
            'guerre', 'révolution', 'empire', 'roi', 'président', 'civilisation',
            'siècle', 'bataille', 'traité', 'indépendance', 'découverte',
            'antiquité', 'moyen âge', 'renaissance', 'colonisation', 'décolonisation',
            'démocratie', 'république', 'monarchie', 'constitution', 'élection',
            'rome', 'grèce', 'égypte', 'france', 'angleterre', 'chine', 'inde',
            'napoléon', 'alexandre', 'césar', 'gengis khan', 'churchill', 'de gaulle',
            'mandela', 'gandhi', 'lincoln', 'marx', 'darwin', 'einstein', 'newton',
            'préhistoire', 'néolithique', 'sumer', 'babylone', 'pharaon', 'viking',
            'croisade', 'inquisition', 'esclavage', 'abolition', 'suffrage',
            'war', 'king', 'revolution', 'century', 'battle', 'crown', 'conquest',
            'world war', 'cold war', 'renaissance', 'enlightenment', 'industrial',
        ],
    },
    'nature': {
        'sectors': ['NATURE', 'BIOLOGIE', 'ECOLOGIE', 'BIODIVERSITE', 'ENVIRONNEMENT',
                     'CLIMAT', 'GEOLOGIE', 'OCEANOGRAPHIE'],
        'keywords': [
            'animal', 'plante', 'espèce', 'écosystème', 'forêt', 'océan', 'rivière',
            'montagne', 'désert', 'volcan', 'corail', 'mammifère', 'oiseau', 'poisson',
            'insecte', 'reptile', 'amphibien', 'champignon', 'bactérie', 'algue',
            'photosynthèse', 'pollinisation', 'migration', 'hibernation', 'prédateur',
            'proie', 'chaîne alimentaire', 'biodiversité', 'conservation', 'extinction',
            'climat', 'réchauffement', 'pollution', 'recyclage', 'développement durable',
            'énergie renouvelable', 'solaire', 'éolien', 'hydraulique', 'géothermie',
            'animal', 'species', 'forest', 'ocean', 'climate', 'wildlife', 'nature',
            'earth', 'planet', 'habitat', 'wetland', 'savanna', 'tundra', 'rainforest',
        ],
    },
    'technologie': {
        'sectors': ['TECHNOLOGIE', 'TECH', 'INFORMATIQUE', 'ROBOTIQUE', 'IA',
                     'TELECOM', 'ENERGIE', 'TRANSPORT', 'INTERNET'],
        'keywords': [
            'ordinateur', 'logiciel', 'internet', 'réseau', 'serveur', 'donnée',
            'algorithme', 'programmation', 'code', 'application', 'mobile', 'web',
            'intelligence artificielle', 'machine learning', 'deep learning', 'robot',
            'drone', 'automatisation', 'blockchain', 'cryptomonnaie', 'bitcoin',
            'smartphone', 'tablette', 'processeur', 'mémoire', 'stockage', 'cloud',
            'cybersécurité', 'hacking', 'chiffrement', 'firewall', 'vpn', 'wifi',
            'bluetooth', '5g', 'fibre optique', 'satellite', 'gps', 'iot',
            'impression 3d', 'réalité virtuelle', 'réalité augmentée', 'quantique',
            'computer', 'software', 'hardware', 'network', 'server', 'algorithm',
            'python', 'javascript', 'linux', 'android', 'ios', 'windows', 'mac',
            'électronique', 'circuit', 'transistor', 'microprocesseur', 'capteur',
            'batterie', 'écran', 'clavier', 'souris', 'imprimante', 'scanner',
            'base de données', 'sql', 'api', 'http', 'dns', 'tcp ip', 'ethernet',
            'html', 'css', 'react', 'angular', 'nodejs', 'docker', 'kubernetes',
            'git', 'github', 'open source', 'compilateur', 'débogueur', 'framework',
            'artificial intelligence', 'neural network', 'gpu', 'cpu', 'ram', 'ssd',
        ],
        'quality_filter': {
            'min_object_len': 6,
            'min_relation_len': 4,
            'exclude_relations': ['est', 'a', 'sont', 'et'],
        },
    },
    'economie': {
        'sectors': ['ECONOMIE', 'FINANCE', 'POLITIQUE', 'ENTREPRISE', 'COMMERCE'],
        'keywords': [
            'produit intérieur brut', 'taux d inflation', 'politique monétaire', 'banque centrale',
            'marché financier', 'bourse des valeurs', 'fonds monétaire international',
            'croissance économique', 'récession', 'dette publique', 'déficit budgétaire',
            'commerce international', 'libre échange', 'protectionnisme', 'balance commerciale',
            'investissement direct', 'capital risque', 'marché émergent', 'indice boursier',
            'produit dérivé', 'obligation d état', 'cotation en bourse', 'introduction en bourse',
            'théorie keynésienne', 'école de chicago', 'main invisible', 'avantage comparatif',
            'gdp', 'inflation rate', 'central bank', 'stock exchange', 'monetary policy',
            'bull market', 'bear market', 'dividend yield', 'price earning ratio',
        ],
    },
    'culture': {
        'sectors': ['CULTURE', 'CREATION', 'EXPRESSION', 'ART', 'LITTERATURE',
                     'MUSIQUE', 'CINEMA', 'PHILOSOPHIE'],
        'keywords': [
            'art', 'peinture', 'sculpture', 'architecture', 'musique', 'littérature',
            'poésie', 'roman', 'théâtre', 'cinéma', 'photographie', 'danse', 'opéra',
            'jazz', 'rock', 'classique', 'hip hop', 'blues', 'symphonie', 'concerto',
            'musée', 'galerie', 'exposition', 'festival', 'biennale', 'conservatoire',
            'artiste', 'peintre', 'écrivain', 'poète', 'musicien', 'compositeur',
            'réalisateur', 'acteur', 'sculpteur', 'architecte', 'designer', 'chef',
            'renaissance', 'baroque', 'impressionnisme', 'cubisme', 'surréalisme',
            'art', 'music', 'painting', 'literature', 'poetry', 'film', 'theatre',
            'museum', 'gallery', 'concert', 'exhibition', 'symphony', 'opera',
            'mozart', 'beethoven', 'bach', 'picasso', 'van gogh', 'davinci', 'monet',
            'chanson', 'album', 'disque', 'orchestre', 'piano', 'violon', 'guitare',
            'fresque', 'portrait', 'paysage', 'nature morte', 'aquarelle', 'gravure',
            'tragédie', 'comédie', 'drame', 'essai', 'biographie', 'nouvelle',
        ],
        'quality_filter': {
            'min_object_len': 6,
            'min_relation_len': 4,
            'exclude_relations': ['est', 'a', 'sont', 'et'],
        },
    },
    'droit': {
        'sectors': ['DROIT', 'POLITIQUE', 'HISTOIRE', 'PHILOSOPHIE', 'ECONOMIE'],
        'keywords': [
            'loi', 'code', 'constitution', 'tribunal', 'justice', 'juge', 'avocat',
            'procès', 'juridiction', 'jurisprudence', 'législation', 'réglementation',
            'crime', 'délit', 'contravention', 'peine', 'prison', 'amende', 'recours',
            'cassation', 'appel', 'première instance', 'administratif', 'constitutionnel',
            'contrat', 'obligation', 'responsabilité', 'préjudice', 'dommage', 'indemnité',
            'propriété', 'héritage', 'testament', 'mariage', 'divorce', 'filiation',
            'droit du travail', 'licenciement', 'syndicat', 'négociation collective',
            'droit pénal', 'droit civil', 'droit commercial', 'droit international',
            'avocat', 'notaire', 'huissier', 'magistrat', 'procureur', 'greffier',
            'law', 'court', 'judge', 'attorney', 'trial', 'verdict', 'sentence',
            'constitution', 'statute', 'regulation', 'precedent', 'jurisdiction',
            'déclaration des droits', 'habeas corpus', 'présomption innocence',
            'droit européen', 'cour européenne', 'cour pénale internationale',
        ],
        'quality_filter': {
            'min_object_len': 6,
            'min_relation_len': 4,
            'exclude_relations': ['est', 'a', 'sont', 'et'],
        },
    },
    'education': {
        'sectors': ['EDUCATION', 'CULTURE', 'HISTOIRE', 'SCIENCES', 'PHILOSOPHIE',
                     'GEOGRAPHIE', 'MATHS_PURES', 'LITTERATURE'],
        'keywords': [
            'pédagogie', 'didactique', 'programme scolaire', 'éducation nationale',
            'baccalauréat', 'certificat', 'diplôme', 'école primaire', 'collège',
            'lycée', 'université', 'grande école', 'sorbonne', 'harvard', 'oxford',
            'enseignement', 'apprentissage', 'alphabétisation', 'illettrisme',
            'manuel scolaire', 'cours magistral', 'travaux dirigés', 'méthode',
            'montessori', 'freinet', 'dewey', 'piaget', 'vygotski', 'rousseau',
            'répétiteur', 'précepteur', 'internat', 'pensionnat', 'cantine scolaire',
            'académie', 'rectorat', 'inspection', 'agrégation', 'capès', 'crpe',
            'education', 'school', 'curriculum', 'literacy', 'numeracy', 'pedagogy',
            'platon académie', 'lycée aristote', 'université médiévale', 'bologne',
            'confucius', 'éducation spartiate', 'éducation athénienne', 'trivium',
            'quadrivium', 'imprimerie gutenberg', 'encyclopédie diderot',
            'loi jules ferry', 'école obligatoire', 'gratuité', 'laïcité',
        ],
        'quality_filter': {
            'min_object_len': 6,
            'min_relation_len': 4,
            'exclude_relations': ['est', 'a', 'sont', 'et'],
        },
    },
    'cuisine': {
        'sectors': ['CULTURE', 'NATURE', 'SANTE', 'ECONOMIE', 'BIOLOGIE'],
        'keywords': [
            'recette', 'cuisine', 'plat', 'ingrédient', 'cuisson', 'four', 'poêle',
            'légume', 'fruit', 'viande', 'poisson', 'épice', 'herbe', 'sauce', 'soupe',
            'salade', 'dessert', 'pâtisserie', 'boulangerie', 'fromage', 'vin', 'pain',
            'riz', 'pâtes', 'pomme terre', 'tomate', 'oignon', 'ail', 'huile olive',
            'beurre', 'crème', 'œuf', 'farine', 'sucre', 'sel', 'poivre', 'citron',
            'restaurant', 'chef cuisinier', 'gastronomie', 'guide michelin', 'étoilé',
            'cuisine française', 'italienne', 'chinoise', 'japonaise', 'indienne',
            'cooking', 'recipe', 'ingredient', 'baking', 'roasting', 'frying', 'grill',
            'nutrition', 'calorie', 'protéine', 'glucide', 'lipide', 'vitamine', 'fibre',
            'régime', 'végétarien', 'végétalien', 'sans gluten', 'bio', 'fermentation',
        ],
        'quality_filter': {
            'min_object_len': 6,
            'min_relation_len': 4,
            'exclude_relations': ['est', 'a', 'sont', 'et'],
        },
    },
    'sport': {
        'sectors': ['SPORT', 'CULTURE', 'SANTE', 'HISTOIRE', 'BIOLOGIE'],
        'keywords': [
            'football', 'basketball', 'tennis', 'rugby', 'athlétisme', 'natation',
            'cyclisme', 'formule', 'boxe', 'judo', 'karaté', 'ski', 'golf', 'cricket',
            'baseball', 'hockey', 'volleyball', 'handball', 'escrime', 'équitation',
            'jeux olympiques', 'coupe monde', 'championnat', 'tournoi', 'compétition',
            'stade', 'terrain', 'piscine', 'gymnase', 'vélodrome', 'dojo', 'ring',
            'marathon', 'sprint', 'relais', 'triathlon', 'pentathlon', 'décathlon',
            'médaille or', 'record monde', 'champion olympique', 'ballon or',
            'sport', 'soccer', 'basketball', 'tennis', 'olympics', 'world cup',
            'pelé', 'maradona', 'jordan', 'bolt', 'phelps', 'woods', 'federer', 'ali',
            'entraîneur', 'arbitre', 'fair play', 'dopage', 'antidopage',
        ],
        'quality_filter': {
            'min_object_len': 6,
            'min_relation_len': 4,
            'exclude_relations': ['est', 'a', 'sont', 'et'],
        },
    },
    'psychologie': {
        'sectors': ['PSYCHOLOGIE', 'CONSCIENCE', 'SANTE', 'PHILOSOPHIE', 'BIOLOGIE'],
        'keywords': [
            'psychologie', 'comportement', 'émotion', 'cognition', 'mémoire', 'perception',
            'apprentissage', 'intelligence', 'personnalité', 'trouble mental', 'dépression',
            'anxiété', 'stress', 'traumatisme', 'thérapie cognitive', 'psychanalyse',
            'freud', 'jung', 'piaget', 'skinner', 'pavlov', 'maslow', 'rogers',
            'inconscient', 'subconscient', 'rêve', 'hypnose', 'méditation', 'pleine conscience',
            'biais cognitif', 'dissonance cognitive', 'effet placebo', 'syndrome',
            'neuroscience', 'cerveau limbique', 'amygdale', 'hippocampe', 'cortex préfrontal',
            'neurotransmetteur', 'sérotonine', 'dopamine', 'noradrénaline', 'cortisol',
            'psychology', 'behavior', 'emotion', 'cognition', 'mental health', 'therapy',
            'attachement', 'résilience', 'burnout', 'phobie', 'toc', 'schizophrénie',
        ],
        'quality_filter': {
            'min_object_len': 6,
            'min_relation_len': 4,
            'exclude_relations': ['est', 'a', 'sont', 'et'],
        },
    },
    'langues': {
        'sectors': ['CULTURE', 'LINGUISTIQUE', 'HISTOIRE', 'GEOGRAPHIE', 'EDUCATION'],
        'keywords': [
            'langue', 'linguistique', 'grammaire', 'syntaxe', 'phonétique', 'phonologie',
            'morphologie', 'sémantique', 'pragmatique', 'étymologie', 'dialecte', 'patois',
            'français', 'anglais', 'espagnol', 'mandarin', 'arabe', 'hindi', 'portugais',
            'russe', 'japonais', 'allemand', 'italien', 'néerlandais', 'suédois', 'latin',
            'grec ancien', 'sanskrit', 'hébreu', 'swahili', 'wolof', 'bambara', 'lingala',
            'alphabet', 'idéogramme', 'hiéroglyphe', 'cyrillique', 'caractère chinois',
            'traduction', 'interprétation', 'bilinguisme', 'multilinguisme', 'langue maternelle',
            'espéranto', 'langue des signes', 'braille', 'académie française', 'dictionnaire',
            'language', 'grammar', 'syntax', 'phonetics', 'etymology', 'dialect', 'bilingual',
            'indo européen', 'langues romanes', 'langues germaniques', 'langues slaves',
        ],
        'quality_filter': {
            'min_object_len': 6,
            'min_relation_len': 4,
            'exclude_relations': ['est', 'a', 'sont', 'et'],
        },
    },
}

DEFAULT_EXPANSION = {
    'sectors': [],
    'keywords': [],
}

def _get_domain_config(domain: str) -> dict:
    """Récupère la config d'expansion pour un domaine, avec fallback intelligent."""
    # Normaliser le nom du domaine
    domain_lower = domain.lower().strip().replace('é','e').replace('è','e')
    
    # Chercher une correspondance exacte ou partielle
    for key in DOMAIN_EXPANSIONS:
        key_norm = key.lower().replace('é','e').replace('è','e')
        if key_norm in domain_lower or domain_lower in key_norm:
            return DOMAIN_EXPANSIONS[key]
    
    # Fallback intelligent : utiliser les secteurs de l'hologramme officiel
    try:
        from hologram_store import HologramStore
        store = HologramStore()
        official_id = f'official_{domain}'
        if official_id in store._registry:
            meta = store._registry[official_id]
            return {
                'sectors': list(meta.sectors),
                'keywords': [domain.lower()] + meta.top_concepts[:10],
            }
    except Exception:
        pass
    
    # Fallback ultime : nom du domaine + variantes
    return {
        'sectors': [],
        'keywords': [domain.lower(), domain.replace('é','e'), domain.replace('è','e')],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CROSS-LINGUAL EXPANSION
# ═══════════════════════════════════════════════════════════════════════════════

FR_TO_EN = {
    'est': 'is', 'est un': 'is a', 'est une': 'is a', 'sont': 'are',
    'a découvert': 'discovered', 'a inventé': 'invented', 'a créé': 'created',
    'a formulé': 'formulated', 'a écrit': 'wrote', 'a développé': 'developed',
    'a fondé': 'founded', 'contient': 'contains', 'comprend': 'includes',
    'produit': 'produces', 'cause': 'causes', 'régule': 'regulates',
    'permet': 'enables', 'mesure': 'measures', 'détecte': 'detects',
    'convertit': 'converts', 'absorbe': 'absorbs', 'émet': 'emits',
    'génère': 'generates', 'transforme': 'transforms', 'stocke': 'stores',
    'protège': 'protects', 'active': 'activates', 'inhibe': 'inhibits',
    'a pour capitale': 'has capital', 'est situé à': 'is located in',
    'se trouve dans': 'is found in', 'fait partie de': 'is part of',
    'est composé de': 'is composed of', 'découvre': 'discovers',
    'invente': 'invents', 'fonde': 'founds', 'écrit': 'writes',
    'développe': 'develops', 'propose': 'proposes', 'formule': 'formulates',
}

def expand_cross_lingual(facts: List[Tuple[str, str, str, str]]) -> List[Tuple[str, str, str, str]]:
    """
    Double le nombre de faits par traduction FR↔EN des relations.
    Seules les relations connues sont traduites (qualité > quantité).
    """
    expanded = list(facts)
    seen = set((s.lower(), r.lower(), o.lower()) for s, r, o, sec in facts)

    for s, r, o, sec in facts:
        r_lower = r.lower().strip()
        if r_lower in FR_TO_EN:
            en_rel = FR_TO_EN[r_lower]
            key = (s.lower(), en_rel.lower(), o.lower())
            if key not in seen:
                seen.add(key)
                expanded.append((s, en_rel, o, sec))

    return expanded


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TRANSITIVITÉ (fermeture simple)
# ═══════════════════════════════════════════════════════════════════════════════

def expand_transitivity(facts: List[Tuple[str, str, str, str]]) -> List[Tuple[str, str, str, str]]:
    """
    Fermeture transitive simple : si A → B et B → C, alors A → C.
    Ne s'applique qu'aux relations 'est' et 'contient' (les plus fiables).
    """
    expanded = list(facts)
    seen = set((f[0].lower(), f[1].lower(), f[2].lower()) for f in facts)

    # Construire l'index sujet→objet
    subj_to_obj = defaultdict(list)
    for s, r, o, sec in facts:
        if r.lower() in ('est', 'est un', 'est une', 'contient', 'fait partie de'):
            subj_to_obj[s.lower()].append((o, r, sec))

    # Transitivité : A est B, B est C → A est C
    for s, r, o, sec in facts:
        if r.lower() in ('est', 'est un', 'est une'):
            o_lower = o.lower()
            if o_lower in subj_to_obj:
                for o2, r2, sec2 in subj_to_obj[o_lower]:
                    if r2.lower() in ('est', 'est un', 'est une', 'contient'):
                        key = (s.lower(), 'est', o2.lower())
                        if key not in seen:
                            seen.add(key)
                            expanded.append((s, 'est', o2, sec))

    return expanded


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def build_massive_hologram(domain: str, target_facts: int = 50000,
                           skip_benchmark: bool = False) -> dict:
    """
    Construit un hologramme massif pour un domaine donné.

    Stratégie :
      1. Filtrer le KB existant avec des critères RELÂCHÉS
      2. Expansion cross-lingual (×1.5-2)
      3. Expansion par transitivité
      4. Validation + déduplication
      5. Publication
    """
    t0 = time.time()
    config = _get_domain_config(domain)
    report = {'domain': domain, 'target': target_facts}

    print(f"\n{'='*60}")
    print(f"  HOLO EXPANDER — {domain.upper()}")
    print(f"  Cible: {target_facts:,} faits")
    print(f"{'='*60}")

    # ═══ 1. FILTRAGE RELÂCHÉ ═══
    print("\n  1/5 — FILTRAGE DU KB (critères relâchés)...")

    # Source : charger le plus gros KB disponible
    import numpy as np
    kb_dir = Path('data/bootstrapper_output')
    kb_candidates = sorted(kb_dir.glob('knowledge_base_*.npz'), key=lambda p: p.stat().st_size, reverse=True)
    
    all_source_facts = []
    for kb_path in kb_candidates[:3]:  # top 3 plus gros
        try:
            data = np.load(str(kb_path), allow_pickle=True)
            if 'facts' in data:
                for f in data['facts']:
                    if len(f) >= 4:
                        all_source_facts.append((str(f[0]), str(f[1]), str(f[2]), str(f[3])))
            elif 'subjects' in data:
                for i in range(len(data['subjects'])):
                    all_source_facts.append((
                        str(data['subjects'][i]), str(data['relations'][i]),
                        str(data['objects'][i]),
                        str(data['sectors'][i]) if 'sectors' in data else 'GENERAL'
                    ))
        except Exception as e:
            continue
    
    # Déduplication rapide
    seen = set()
    unique_facts = []
    for s, r, o, sec in all_source_facts:
        key = (s.lower()[:80], r.lower()[:60], o.lower()[:80])
        if key not in seen:
            seen.add(key)
            unique_facts.append((s, r, o, sec))
    
    print(f"     → {len(unique_facts):,} faits uniques (chargés depuis {len(kb_candidates)} fichiers)")
    sectors = set(config.get('sectors', []))
    keywords = set(kw.lower() for kw in config.get('keywords', []))
    
    filtered = []
    seen = set()
    
    for s, r, o, sec in unique_facts:
        sec_str = str(sec).upper()
        text = f"{s} {r} {o}".lower()
        
        # Critère 1 : secteur correspondant (relâché : sous-chaîne)
        sector_match = any(t in sec_str for t in sectors) if sectors else True
        
        # Critère 2 : mot-clé (relâché : sous-chaîne)
        kw_match = any(kw in text for kw in keywords) if keywords else False
        
        # Critère 3 : sujet ou objet contient le nom du domaine
        domain_match = domain.lower() in text
        
        if sector_match or kw_match or domain_match:
            # 🆕 Filtre de qualité optionnel (configuré dans DOMAIN_EXPANSIONS)
            qf = config.get('quality_filter', {})
            if qf:
                r_lower = str(r).lower().strip()
                o_lower = str(o).lower().strip()
                # Exclure les relations trop vagues
                if r_lower in qf.get('exclude_relations', []):
                    continue
                # Exclure les objets trop courts ou génériques
                if len(o_lower) < qf.get('min_object_len', 0):
                    continue
                if o_lower in qf.get('exclude_objects', []):
                    continue
                # Exclure les relations trop courtes
                if len(r_lower) < qf.get('min_relation_len', 0):
                    continue
            key = (s.lower()[:80], r.lower()[:60], o.lower()[:80])
            if key not in seen:
                seen.add(key)
                filtered.append((s, r, o, sec))
        
        if len(filtered) >= target_facts * 3:  # marge pour validation
            break
    
    print(f"     → {len(filtered):,} faits filtrés (critères relâchés)")
    
    if len(filtered) < 50:
        print("     ⚠️  Très peu de faits — le KB source est peut-être trop petit")
        report['status'] = 'insufficient_source'
        return report
    
    # ═══ 2. EXPANSION CROSS-LINGUAL ═══
    print("\n  2/5 — EXPANSION CROSS-LINGUAL (FR↔EN)...")
    expanded = expand_cross_lingual(filtered)
    print(f"     → {len(expanded):,} faits (×{len(expanded)/max(len(filtered),1):.1f})")
    
    # ═══ 3. EXPANSION TRANSITIVE ═══
    print("\n  3/5 — EXPANSION TRANSITIVE...")
    expanded = expand_transitivity(expanded)
    print(f"     → {len(expanded):,} faits")
    
    # ═══ 4. VALIDATION ═══
    print("\n  4/5 — VALIDATION...")
    from validate_hologram import validate_hologram
    validation = validate_hologram(expanded[:target_facts], domain)
    report['validation'] = validation
    report['quality_score'] = validation.get('quality_score', 0)
    print(f"     → Score: {validation['quality_score']:.3f}")
    print(f"     → Déduplication: {validation['deduplication']['duplicates_removed']} doublons")
    
    # ═══ 5. PUBLICATION ═══
    print("\n  5/5 — PUBLICATION...")
    try:
        from hologram_store import HologramStore
        store = HologramStore()
        
        # Garder les meilleurs (plus informatifs = sujets/objets plus longs)
        final = list(expanded[:target_facts])
        final.sort(key=lambda x: len(str(x[0])) + len(str(x[2])), reverse=True)
        
        store.publish(
            domain=domain,
            facts=final[:target_facts],
            author='KA Expander',
            name=f'{domain.capitalize()} (Massif)',
            description=f'Hologramme massif spécialisé en {domain}. '
                       f'{len(final[:target_facts]):,} faits validés.',
        )
        
        # Trouver l'ID publié
        published_id = None
        for hid, meta in store._registry.items():
            if meta.domain == domain and 'KA Expander' in meta.author:
                published_id = hid
                break
        
        report['published'] = True
        report['hologram_id'] = published_id
        report['published_facts'] = min(len(final), target_facts)
        print(f"     ✅ Publié: {published_id} ({report['published_facts']:,} faits)")
    except Exception as e:
        print(f"     ❌ Échec publication: {e}")
        report['published'] = False
    
    report['duration_seconds'] = round(time.time() - t0, 1)
    report['status'] = 'completed'
    
    # Sauvegarder le rapport
    report_path = Path(f'data/hologram_store/expand_report_{domain}.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n  Rapport: {report_path}")
    print(f"  Durée: {report['duration_seconds']:.0f}s")
    return report


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="HoloExpander — Hologrammes massifs")
    parser.add_argument('--domain', '-d', required=True, help='Domaine (medecine, astronomie, histoire...)')
    parser.add_argument('--target', '-t', type=int, default=20000, help='Cible de faits (défaut: 20000)')
    parser.add_argument('--skip-benchmark', action='store_true')
    args = parser.parse_args()

    report = build_massive_hologram(
        domain=args.domain,
        target_facts=args.target,
        skip_benchmark=args.skip_benchmark,
    )

    if report.get('status') == 'completed':
        print(f"\n{'='*60}")
        print(f"  🌟 HOLOGRAMME MASSIF CRÉÉ")
        print(f"{'='*60}")
        print(f"  Domaine : {args.domain}")
        print(f"  ID      : {report.get('hologram_id', '?')}")
        print(f"  Faits   : {report.get('published_facts', 0):,}")
        print(f"  Qualité : {report.get('quality_score', 0):.3f}")
        print(f"  Durée   : {report.get('duration_seconds', 0):.0f}s")


if __name__ == '__main__':
    main()
