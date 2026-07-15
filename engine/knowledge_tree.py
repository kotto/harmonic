"""
Knowledge Tree — Arbre de Connaissance Systématique
=====================================================
Remplace l'approche « faits plats + distillation aléatoire » par un
Arbre de Connaissance structuré où chaque fait a un chemin hiérarchique.

7 Domaines → 35 Sous-domaines → Wikidata SPARQL + Distillation

Usage :
  python knowledge_tree.py --source wikidata  # Faits réels gratuits
  python knowledge_tree.py --source distill   # DeepSeek ciblé
  python knowledge_tree.py --build            # Construire les hologrammes
"""

import json, urllib.request, urllib.parse, time, logging, sys, os, re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))
_ENTERPRISES_DIR = _ENGINE_DIR / "data" / "enterprises"
_USERS_DIR = _ENGINE_DIR / "data" / "users"

# ═══════════════════════════════════════════════════════════════════════════════
# ARBRE DE CONNAISSANCE
# ═══════════════════════════════════════════════════════════════════════════════

KNOWLEDGE_TREE = {
    'sciences': {
        'label': 'Sciences',
        'keywords': ['physique', 'onde', 'force', 'energie', 'gravite', 'quantique',
                     'atome', 'particule', 'relativite', 'chimie', 'element', 'reaction',
                     'biologie', 'cellule', 'adn', 'gene', 'evolution', 'organisme',
                     'astronomie', 'planete', 'etoile', 'galaxie', 'math', 'theoreme'],
        'sub_domains': {
            'physique': {
                'label': 'Physique',
                'keywords': ['physique', 'onde', 'force', 'energie', 'gravite', 'quantique',
                             'relativite', 'electromagnetique', 'thermodynamique', 'mecanique',
                             'optique', 'nucleaire', 'particule', 'vitesse', 'masse'],
                'sparql': [
                    ('elements_particules', 
                     'SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q413. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 100',
                     'physique_fond'),
                    ('forces_fondamentales',
                     'SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q11412. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 50',
                     'physique_fond'),
                ],
                'distill': [
                    ('physique_lois', 'Liste 40 lois et principes de physique avec leur createur. Format: loi | a ete formulee par | scientifique'),
                    ('physique_constantes', 'Liste 30 constantes physiques avec leur valeur. Format: constante | a pour valeur | valeur'),
                ],
            },
            'chimie': {
                'label': 'Chimie',
                'keywords': ['chimie', 'element', 'reaction', 'molecule', 'atome', 'acide',
                             'base', 'metal', 'gaz', 'compose', 'formule', 'symbole'],
                'sparql': [
                    ('elements_chimiques',
                     'SELECT ?item ?itemLabel ?sym WHERE { ?item wdt:P31 wd:Q11344; wdt:P246 ?sym. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 120',
                     'physique_fond'),
                    ('composes_chimiques',
                     'SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q11173. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 100',
                     'physique_fond'),
                ],
                'distill': [
                    ('chimie_reactions', 'Liste 40 reactions chimiques importantes. Format: reaction | produit | resultat'),
                ],
            },
            'biologie': {
                'label': 'Biologie',
                'keywords': ['biologie', 'cellule', 'adn', 'gene', 'proteine', 'organe',
                             'espece', 'evolution', 'organisme', 'photosynthese', 'bacterie'],
                'sparql': [
                    ('especes_biologiques',
                     'SELECT ?item ?itemLabel WHERE { ?item wdt:P105 wd:Q7432. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 200',
                     'biologie'),
                    ('organes_corps',
                     'SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q712378. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 100',
                     'corps_organes'),
                ],
                'distill': [
                    ('biologie_systemes', 'Liste 40 faits de biologie: organes, fonctions, processus. Format: sujet | relation | objet'),
                ],
            },
            'astronomie': {
                'label': 'Astronomie',
                'keywords': ['astronomie', 'planete', 'etoile', 'galaxie', 'soleil', 'lune',
                             'univers', 'cosmos', 'trou noir', 'big bang', 'constellation'],
                'sparql': [
                    ('planetes',
                     'SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q128207. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 50',
                     'astronomie'),
                    ('constellations',
                     'SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q8928. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 50',
                     'astronomie'),
                ],
                'distill': [
                    ('astronomie_faits', 'Liste 30 faits astronomiques. Format: sujet | relation | objet'),
                ],
            },
            'mathematiques': {
                'label': 'Mathématiques',
                'keywords': ['math', 'nombre', 'geometrie', 'algebre', 'theoreme', 'equation',
                             'calcul', 'probabilite', 'statistique', 'logique'],
                'sparql': [],
                'distill': [
                    ('maths_theoremes', 'Liste 30 theoremes mathematiques avec leur auteur. Format: theoreme | a ete demontre par | mathematicien'),
                    ('maths_constantes', 'Liste 25 constantes mathematiques. Format: constante | a pour valeur | valeur'),
                ],
            },
        },
    },
    
    'culture_generale': {
        'label': 'Culture Générale',
        'keywords': ['pays', 'capitale', 'continent', 'ville', 'region', 'montagne', 'fleuve',
                     'ocean', 'mer', 'politique', 'economie', 'langue', 'religion', 'animal'],
        'sub_domains': {
            'geographie': {
                'label': 'Géographie',
                'keywords': ['pays', 'capitale', 'continent', 'ville', 'region', 'montagne',
                             'fleuve', 'ocean', 'mer', 'lac', 'desert', 'ile', 'geographie'],
                'sparql': [
                    ('capitales_pays',
                     'SELECT ?pays ?paysLabel ?capitale ?capitaleLabel WHERE { ?pays wdt:P31 wd:Q3624078; wdt:P36 ?capitale. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 250',
                     'geographie'),
                    ('pays_continents',
                     'SELECT ?pays ?paysLabel ?continent ?continentLabel WHERE { ?pays wdt:P31 wd:Q3624078; wdt:P30 ?continent. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 250',
                     'geographie'),
                    ('pays_populations',
                     'SELECT ?pays ?paysLabel ?pop WHERE { ?pays wdt:P31 wd:Q3624078; wdt:P1082 ?pop. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 250',
                     'geographie'),
                    ('montagnes_altitude',
                     'SELECT ?m ?mLabel ?h WHERE { ?m wdt:P31 wd:Q8502; wdt:P2044 ?h. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 100',
                     'geographie'),
                    ('fleuves_longueur',
                     'SELECT ?r ?rLabel ?l WHERE { ?r wdt:P31 wd:Q4022; wdt:P2043 ?l. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 100',
                     'geographie'),
                    ('villes_monde',
                     'SELECT ?city ?cityLabel ?pop WHERE { ?city wdt:P31 wd:Q515; wdt:P1082 ?pop. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 300',
                     'geographie'),
                ],
                'distill': [
                    ('geographie_climat', 'Liste 30 faits sur les climats du monde. Format: sujet | relation | objet'),
                ],
            },
            'politique': {
                'label': 'Politique',
                'keywords': ['politique', 'democratie', 'president', 'gouvernement', 'etat',
                             'loi', 'justice', 'parlement', 'election', 'dirigeant', 'onu'],
                'sparql': [
                    ('chefs_etat',
                     'SELECT ?person ?personLabel ?country ?countryLabel WHERE { ?person wdt:P39 wd:Q48352; wdt:P27 ?country. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 100',
                     'politique'),
                ],
                'distill': [
                    ('dirigeants_monde', 'Liste 30 dirigeants politiques marquants avec leur pays. Format: dirigeant | a dirige | pays'),
                ],
            },
            'economie': {
                'label': 'Économie',
                'keywords': ['economie', 'monnaie', 'banque', 'marche', 'commerce', 'pib',
                             'inflation', 'entreprise', 'finance', 'croissance'],
                'sparql': [
                    ('monnaies_pays',
                     'SELECT ?pays ?paysLabel ?monnaie ?monnaieLabel WHERE { ?pays wdt:P31 wd:Q3624078; wdt:P38 ?monnaie. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 200',
                     'economie'),
                ],
                'distill': [
                    ('economie_concepts', 'Liste 30 concepts economiques importants. Format: concept | signifie | definition'),
                ],
            },
            'societe': {
                'label': 'Société',
                'keywords': ['langue', 'religion', 'démographie', 'education', 'culture',
                             'population', 'ethnie', 'migration', 'urbanisation'],
                'sparql': [
                    ('langues_officielles',
                     'SELECT ?pays ?paysLabel ?langue ?langueLabel WHERE { ?pays wdt:P31 wd:Q3624078; wdt:P37 ?langue. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 200',
                     'expression'),
                    ('religions_monde',
                     'SELECT ?religion ?religionLabel ?followers WHERE { ?religion wdt:P31 wd:Q9174; wdt:P1099 ?followers. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 50',
                     'spiritualite'),
                ],
                'distill': [],
            },
            'nature': {
                'label': 'Nature',
                'keywords': ['animal', 'plante', 'mammifere', 'oiseau', 'poisson', 'insecte',
                             'arbre', 'fleur', 'ecosysteme', 'biodiversite', 'espece'],
                'sparql': [
                    ('animaux_famille',
                     'SELECT ?animal ?animalLabel ?family ?familyLabel WHERE { ?animal wdt:P31 wd:Q16521; wdt:P177 ?family. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 200',
                     'nature_anim'),
                    ('plantes_famille',
                     'SELECT ?plant ?plantLabel ?family ?familyLabel WHERE { ?plant wdt:P31 wd:Q756; wdt:P177 ?family. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 200',
                     'nature_veget'),
                ],
                'distill': [],
            },
        },
    },
    
    'histoire': {
        'label': 'Histoire',
        'keywords': ['histoire', 'guerre', 'revolution', 'empire', 'roi', 'reine', 'president',
                     'bataille', 'traite', 'decouverte', 'inventeur', 'pharaon', 'civilisation'],
        'sub_domains': {
            'antiquite': {
                'label': 'Antiquité',
                'keywords': ['antiquite', 'egypte', 'grec', 'romain', 'pharaon', 'pyramide',
                             'cesar', 'alexandre', 'platon', 'aristote', 'sparte', 'athenes'],
                'sparql': [],
                'distill': [
                    ('antiquite_faits', 'Liste 40 faits historiques sur l Antiquite (Egypte, Grece, Rome). Format: sujet | relation | objet avec date'),
                ],
            },
            'moyen_age': {
                'label': 'Moyen-Âge / Renaissance',
                'keywords': ['moyen age', 'renaissance', 'feodal', 'chateau', 'croisade',
                             'davinci', 'michelange', 'gutenberg', 'colomb', 'cathedrale'],
                'sparql': [],
                'distill': [
                    ('moyen_age_faits', 'Liste 40 faits sur le Moyen-Age et la Renaissance. Format: sujet | relation | objet avec date'),
                ],
            },
            'epoque_moderne': {
                'label': 'Époque Moderne',
                'keywords': ['revolution', 'industriel', 'napoleon', 'empire', 'colonie',
                             'independance', 'abolition', 'constitution', '18e', '19e'],
                'sparql': [
                    ('evenements_historiques',
                     'SELECT ?event ?eventLabel ?date WHERE { ?event wdt:P31 wd:Q1190554; wdt:P585 ?date. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 300',
                     'passe'),
                ],
                'distill': [
                    ('revolution_francaise', 'Liste 30 faits sur la Revolution francaise. Format: sujet | relation | objet avec date'),
                ],
            },
            'vingtieme_siecle': {
                'label': '20e-21e Siècle',
                'keywords': ['guerre mondiale', 'guerre froide', 'nazisme', 'holocauste',
                             'onu', 'union europeenne', '11 septembre', 'internet', 'nucleaire'],
                'sparql': [
                    ('guerres_mondiales',
                     'SELECT ?war ?warLabel ?start ?end WHERE { ?war wdt:P31 wd:Q103495; wdt:P580 ?start. OPTIONAL { ?war wdt:P582 ?end. } SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 100',
                     'passe'),
                ],
                'distill': [
                    ('vingtieme_faits', 'Liste 40 evenements majeurs du 20e siecle avec leurs dates. Format: evenement | a eu lieu en | annee'),
                ],
            },
        },
    },
    
    'code': {
        'label': 'Code & Technologie',
        'keywords': ['python', 'javascript', 'java', 'html', 'css', 'sql', 'api', 'git',
                     'docker', 'linux', 'algorithme', 'fonction', 'classe', 'framework'],
        'sub_domains': {
            'langages': {
                'label': 'Langages',
                'keywords': ['python', 'javascript', 'java', 'typescript', 'html', 'css',
                             'sql', 'c++', 'rust', 'go', 'ruby', 'php', 'swift'],
                'sparql': [],
                'distill': [
                    ('langages_faits', 'Liste 40 faits sur les langages de programmation. Format: langage | caracteristique | description'),
                ],
            },
            'architecture': {
                'label': 'Architecture & Patterns',
                'keywords': ['api', 'rest', 'graphql', 'mvc', 'microservice', 'design pattern',
                             'singleton', 'factory', 'observer', 'database', 'sql', 'nosql'],
                'sparql': [],
                'distill': [
                    ('architecture_faits', 'Liste 30 faits sur l architecture logicielle. Format: concept | definition | description'),
                ],
            },
            'outils': {
                'label': 'Outils & Infrastructure',
                'keywords': ['git', 'docker', 'kubernetes', 'linux', 'aws', 'azure',
                             'nginx', 'postgresql', 'redis', 'mongodb', 'nodejs', 'react'],
                'sparql': [],
                'distill': [
                    ('outils_faits', 'Liste 30 faits sur les outils de developpement. Format: outil | sert a | usage'),
                ],
            },
        },
    },
    
    'culture_arts': {
        'label': 'Culture & Arts',
        'keywords': ['art', 'peinture', 'musique', 'litterature', 'cinema', 'theatre',
                     'sculpture', 'architecture', 'danse', 'poesie', 'opera'],
        'sub_domains': {
            'arts_visuels': {
                'label': 'Arts Visuels',
                'keywords': ['peinture', 'sculpture', 'architecture', 'artiste', 'peintre',
                             'mona lisa', 'michelange', 'impressionnisme', 'picasso'],
                'sparql': [
                    ('peintres_oeuvres',
                     'SELECT ?painter ?painterLabel ?work ?workLabel WHERE { ?painter wdt:P106 wd:Q1028181. ?work wdt:P170 ?painter. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 300',
                     'culture'),
                    ('monuments_architectes',
                     'SELECT ?building ?buildingLabel ?architect ?architectLabel WHERE { ?building wdt:P84 ?architect. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 200',
                     'culture'),
                ],
                'distill': [],
            },
            'litterature': {
                'label': 'Littérature',
                'keywords': ['litterature', 'ecrivain', 'poete', 'roman', 'poesie', 'auteur',
                             'shakespeare', 'hugo', 'dostoievski', 'prix nobel'],
                'sparql': [
                    ('ecrivains_livres',
                     'SELECT ?writer ?writerLabel ?book ?bookLabel WHERE { ?writer wdt:P106 wd:Q36180. ?book wdt:P50 ?writer. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 300',
                     'culture'),
                ],
                'distill': [
                    ('litterature_mouvements', 'Liste 25 mouvements litteraires avec leur periode. Format: mouvement | a commence en | annee'),
                ],
            },
            'musique': {
                'label': 'Musique',
                'keywords': ['musique', 'compositeur', 'symphonie', 'opera', 'jazz', 'rock',
                             'mozart', 'beethoven', 'bach', 'instrument', 'orchestre'],
                'sparql': [
                    ('compositeurs_oeuvres',
                     'SELECT ?composer ?composerLabel ?work ?workLabel WHERE { ?composer wdt:P106 wd:Q36834. ?work wdt:P86 ?composer. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 200',
                     'culture'),
                ],
                'distill': [
                    ('musique_genres', 'Liste 25 genres musicaux avec leur origine. Format: genre | est originaire de | pays/region'),
                ],
            },
            'cinema': {
                'label': 'Cinéma & Théâtre',
                'keywords': ['cinema', 'film', 'realisateur', 'acteur', 'theatre', 'oscar',
                             'hollywood', 'comedie', 'drame', 'documentaire'],
                'sparql': [
                    ('films_realisateurs',
                     'SELECT ?film ?filmLabel ?director ?directorLabel WHERE { ?film wdt:P31 wd:Q11424; wdt:P57 ?director. SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". } } LIMIT 300',
                     'culture'),
                ],
                'distill': [
                    ('cinema_faits', 'Liste 25 faits sur l histoire du cinema. Format: sujet | relation | objet'),
                ],
            },
        },
    },
    
    'humain': {
        'label': 'Sciences Humaines',
        'keywords': ['philosophie', 'conscience', 'emotion', 'spirituel', 'religion',
                     'psychologie', 'ethique', 'pensee', 'ame', 'meditation'],
        'sub_domains': {
            'philosophie': {
                'label': 'Philosophie',
                'keywords': ['philosophie', 'ethique', 'logique', 'metaphysique', 'platon',
                             'aristote', 'kant', 'nietzsche', 'descartes', 'existentialisme'],
                'sparql': [],
                'distill': [
                    ('philo_courants', 'Liste 25 courants philosophiques avec leur fondateur. Format: courant | a ete fonde par | philosophe'),
                    ('philo_concepts', 'Liste 25 concepts philosophiques. Format: concept | signifie | definition'),
                ],
            },
            'spiritualite': {
                'label': 'Spiritualité',
                'keywords': ['spirituel', 'religion', 'dieu', 'ame', 'foi', 'transcendance',
                             'meditation', 'bouddhisme', 'christianisme', 'islam', 'hindouisme'],
                'sparql': [],
                'distill': [
                    ('spiritualite_faits', 'Liste 30 faits sur les religions et spiritualites du monde. Format: sujet | relation | objet'),
                ],
            },
            'psychologie': {
                'label': 'Psychologie',
                'keywords': ['psychologie', 'emotion', 'comportement', 'cognition', 'freud',
                             'jung', 'inconscient', 'therapie', 'traumatisme', 'bonheur'],
                'sparql': [],
                'distill': [
                    ('psycho_concepts', 'Liste 25 concepts de psychologie. Format: concept | signifie | definition'),
                ],
            },
        },
    },
    
    'corps_sante': {
        'label': 'Corps & Santé',
        'keywords': ['corps', 'coeur', 'sang', 'cerveau', 'organe', 'muscle', 'os',
                     'sante', 'maladie', 'medecin', 'medicament', 'vaccin', 'sport'],
        'sub_domains': {
            'anatomie': {
                'label': 'Anatomie',
                'keywords': ['anatomie', 'organe', 'os', 'muscle', 'coeur', 'cerveau',
                             'poumon', 'foie', 'rein', 'sang', 'nerf', 'systeme'],
                'sparql': [],
                'distill': [
                    ('anatomie_organes', 'Liste 40 organes du corps humain avec leur fonction. Format: organe | fonction | description'),
                    ('anatomie_os', 'Liste 30 os du corps humain. Format: os | se trouve dans | partie du corps'),
                ],
            },
            'medecine': {
                'label': 'Médecine',
                'keywords': ['medecine', 'maladie', 'medicament', 'vaccin', 'virus',
                             'bacterie', 'chirurgie', 'diagnostic', 'traitement', 'cancer'],
                'sparql': [],
                'distill': [
                    ('medecine_maladies', 'Liste 30 maladies avec leur cause. Format: maladie | est causee par | cause'),
                ],
            },
            'sport': {
                'label': 'Sport',
                'keywords': ['sport', 'football', 'tennis', 'natation', 'athletisme',
                             'olympique', 'basket', 'rugby', 'cyclisme', 'formule 1'],
                'sparql': [],
                'distill': [
                    ('sport_faits', 'Liste 30 faits sur les sports et records. Format: sujet | relation | objet'),
                ],
            },
        },
    },
}

# Mapping tree paths to sector strings
def tree_path_to_sector(domain: str, sub: str) -> str:
    """Convertit un chemin d'arbre en secteur standard."""
    return f"{domain.upper()}_{sub.upper()}"

# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE TREE INGESTOR
# ═══════════════════════════════════════════════════════════════════════════════

SPARQL_URL = 'https://query.wikidata.org/sparql'
UA = 'HarmonicAI/4.0 (KnowledgeTree)'

class KnowledgeTreeIngestor:
    """Peuplement systématique de l'arbre de connaissance."""
    
    def __init__(self):
        self.all_facts: List[Tuple[str, str, str, str]] = []
        self.seen: set = set()
        self.stats: Dict[str, Dict] = {}  # domain/sub → count
    
    def populate_from_wikidata(self) -> int:
        """Peuple tous les nœuds de l'arbre qui ont des queries SPARQL."""
        total = 0
        for domain, dconf in KNOWLEDGE_TREE.items():
            for sub, sconf in dconf['sub_domains'].items():
                for name, query, sector in sconf.get('sparql', []):
                    facts = self._fetch_sparql(query, name, sector)
                    added = self._add_facts(facts, domain, sub)
                    total += added
                    if added > 0:
                        print(f'  ✅ {domain}/{sub}/{name}: +{added} faits')
                time.sleep(0.3)  # poli avec Wikidata
        return total
    
    def _fetch_sparql(self, query: str, name: str, default_sector: str) -> List[Tuple]:
        """Exécute une requête SPARQL et parse les résultats en triplets."""
        url = SPARQL_URL + '?format=json&query=' + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f'  ❌ SPARQL {name}: {e}')
            return []
        
        bindings = data.get('results', {}).get('bindings', [])
        facts = []
        for b in bindings:
            labels = []
            values = []
            for k, v in b.items():
                val = v.get('value', '')
                if 'Label' in k:
                    labels.append(val)
                elif k not in ('item', 'pays', 'city', 'event', 'war', 'm', 'r', 'painter', 'writer', 'composer', 'film', 'building', 'animal', 'plant', 'person', 'religion', 'elem'):
                    values.append(val)
            
            if len(labels) >= 2:
                s, o = labels[0], labels[1]
                r = name.replace('_', ' ')
                if values:
                    r = f'{r} ({values[0]})'
                facts.append((s, r, o, default_sector))
        return facts
    
    def _add_facts(self, facts: List[Tuple], domain: str, sub: str) -> int:
        """Ajoute des faits avec déduplication et comptage par domaine."""
        added = 0
        for s, r, o, sec in facts:
            key = (s.lower().strip(), r.lower().strip(), str(o).lower().strip())
            if key not in self.seen and len(s) > 1 and len(str(o)) > 1:
                self.seen.add(key)
                # Sector = tree path
                tree_sec = tree_path_to_sector(domain, sub)
                self.all_facts.append((s.lower().strip(), r.lower().strip(), str(o).lower().strip(), tree_sec))
                added += 1
        
        if domain not in self.stats:
            self.stats[domain] = {}
        self.stats[domain][sub] = self.stats[domain].get(sub, 0) + added
        return added
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de peuplement."""
        result = {'total': len(self.all_facts), 'domains': {}}
        for domain, subs in self.stats.items():
            result['domains'][domain] = {
                'total': sum(subs.values()),
                'sub_domains': dict(subs),
            }
        return result
    
    def save_npz(self, path: str = None):
        """Sauvegarde les faits en NPZ."""
        if path is None:
            path = str(_ENGINE_DIR / 'data' / 'bootstrapper_output' / 'knowledge_tree.npz')
        facts_array = np.array(self.all_facts, dtype=object)
        np.savez(path, facts=facts_array)
        size_mb = Path(path).stat().st_size / (1024 * 1024)
        print(f'✅ {path}: {len(self.all_facts):,} faits ({size_mb:.1f} MB)')
        return path


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Knowledge Tree — Peuplement systématique')
    parser.add_argument('--source', choices=['wikidata', 'distill', 'all'], default='wikidata',
                       help='Source de peuplement (wikidata=gratuit, distill=DeepSeek)')
    parser.add_argument('--output', type=str, default=None, help='Chemin NPZ de sortie')
    args = parser.parse_args()
    
    ingestor = KnowledgeTreeIngestor()
    
    if args.source in ('wikidata', 'all'):
        print('🌐 Peuplement Wikidata...')
        n = ingestor.populate_from_wikidata()
        print(f'   Total Wikidata: {n} faits')
    
    if args.source in ('distill', 'all'):
        print('🤖 Distillation DeepSeek... (non implémenté dans cette version)')
        print('   Utilisez --source wikidata pour les faits gratuits et vérifiés.')
    
    stats = ingestor.get_stats()
    print(f'\n📊 Statistiques:')
    print(f'   Total: {stats["total"]:,} faits')
    for domain, dstat in stats['domains'].items():
        print(f'   {domain}: {dstat["total"]:,}')
        for sub, count in dstat['sub_domains'].items():
            print(f'      {sub}: {count:,}')
    
    ingestor.save_npz(args.output)
    print('\n✅ Peuplement terminé.')
