"""
Wikidata Connector — Ingestion massive de connaissances structurées
====================================================================
Deux modes :
  1. DUMP : lecture d'un dump Wikidata JSON (un objet par ligne)
  2. API  : fetch entités via l'API REST Wikidata (gratuit, limité)
  3. SYNTH : génération synthétique réaliste pour tests à l'échelle

Extrait des triplets de haute qualité :
  · (sujet, propriété, valeur, secteur)
  · Labels humains (pas des Q-ids)
  · Secteurs mappés automatiquement (géographie, sciences, histoire...)

Usage :
    from wikidata_connector import WikidataConnector, generate_synthetic_facts
    
    # Mode dump
    conn = WikidataConnector(kb)
    conn.ingest_dump('data/wikidata_dump.json')
    
    # Mode API (fetch 1000 entités)
    conn.ingest_api(max_entities=1000)
    
    # Mode synthétique (10M faits pour test)
    generator = generate_synthetic_facts(count=1_000_000)
    kb.ingest_batch(generator)
"""

import json
import math
import os
import re
import time
import logging
import urllib.request
import urllib.parse
import urllib.error
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Iterator

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# MAPPING PROPRIÉTÉS WIKIDATA → SECTEURS HARMONIQUES
# ═══════════════════════════════════════════════════════════════════════════════

PROPERTY_SECTOR_MAP = {
    # Géographie
    'P17': 'GEOGRAPHIE',   # pays
    'P36': 'GEOGRAPHIE',   # capitale
    'P30': 'GEOGRAPHIE',   # continent
    'P2046': 'GEOGRAPHIE', # superficie
    'P1082': 'GEOGRAPHIE', # population
    'P625': 'GEOGRAPHIE',  # coordonnées
    'P131': 'GEOGRAPHIE',  # localisation administrative
    'P1376': 'GEOGRAPHIE', # capitale de
    'P190': 'GEOGRAPHIE',  # jumelage
    'P47': 'GEOGRAPHIE',   # frontière avec
    
    # Histoire
    'P569': 'HISTOIRE',    # date de naissance
    'P570': 'HISTOIRE',    # date de mort
    'P571': 'HISTOIRE',    # date de fondation/création
    'P580': 'HISTOIRE',    # date de début
    'P582': 'HISTOIRE',    # date de fin
    'P585': 'HISTOIRE',    # date
    'P27': 'HISTOIRE',     # pays de citoyenneté
    
    # Sciences
    'P2067': 'SCIENCES',   # masse
    'P2054': 'SCIENCES',   # densité
    'P2076': 'SCIENCES',   # température
    'P1086': 'SCIENCES',   # nombre atomique
    'P246': 'SCIENCES',    # symbole chimique
    'P61': 'SCIENCES',     # découvreur
    'P828': 'SCIENCES',    # a pour cause
    
    # Culture/Création
    'P50': 'CREATION',     # auteur
    'P170': 'CREATION',    # créateur
    'P86': 'CULTURE',      # compositeur
    'P57': 'CULTURE',      # réalisateur
    'P175': 'CULTURE',     # interprète
    'P136': 'CULTURE',     # genre
    'P495': 'CULTURE',     # pays d'origine
    
    # Structure
    'P31': 'GENERAL',      # instance de
    'P279': 'GENERAL',     # sous-classe de
    'P361': 'GENERAL',     # partie de
    'P527': 'GENERAL',     # a pour partie
    'P155': 'GENERAL',     # suit
    'P156': 'GENERAL',     # suivi par
}

# Mapping noms de propriétés → secteurs (fallback)
SECTOR_KEYWORDS = {
    'GEOGRAPHIE': ['pays', 'capitale', 'continent', 'population', 'superficie',
                   'coordonnées', 'localisation', 'région', 'ville', 'frontière',
                   'fleuve', 'montagne', 'océan', 'mer', 'île', 'lac'],
    'HISTOIRE': ['date', 'naissance', 'mort', 'fondation', 'création', 'siècle',
                 'début', 'fin', 'roi', 'reine', 'empereur', 'guerre', 'traité',
                 'dynastie', 'civilisation', 'ancêtre'],
    'SCIENCES': ['masse', 'température', 'densité', 'découverte', 'formule',
                 'élément', 'atome', 'molécule', 'réaction', 'espèce',
                 'classification', 'génome', 'protéine', 'cellule'],
    'PHYSIQUE_FOND': ['force', 'énergie', 'onde', 'particule', 'champ',
                      'quantique', 'relativité', 'gravité', 'électromagnétique'],
    'CREATION': ['auteur', 'créateur', 'artiste', 'peintre', 'sculpteur',
                 'écrivain', 'œuvre', 'tableau', 'sculpture', 'roman'],
    'CULTURE': ['compositeur', 'réalisateur', 'acteur', 'musicien', 'film',
                'musique', 'chanson', 'album', 'concert', 'festival'],
    'MATHS_PURES': ['nombre', 'théorème', 'équation', 'constante', 'géométrie',
                    'algèbre', 'calcul', 'logique', 'ensemble', 'fonction'],
    'BIOLOGIE': ['espèce', 'genre', 'famille', 'ordre', 'classe', 'règne',
                 'cellule', 'organe', 'tissu', 'enzyme', 'hormone', 'gène'],
    'ECONOMIE': ['PIB', 'monnaie', 'inflation', 'entreprise', 'industrie',
                 'commerce', 'banque', 'marché', 'exportation'],
}


# ═══════════════════════════════════════════════════════════════════════════════
# WIKIDATA CONNECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class WikidataConnector:
    """Connecteur Wikidata — dump JSON, API REST, ou synthétique."""

    def __init__(self, kb=None, timeout: int = 15):
        self.kb = kb
        self.timeout = timeout
        self.stats = {'ingested': 0, 'skipped': 0, 'errors': 0}

    # ── MODE DUMP ──────────────────────────────────────────────────────────

    def ingest_dump(self, dump_path: str, max_lines: int = None) -> int:
        """
        Ingère un dump Wikidata JSON (un objet JSON par ligne).

        Format attendu (extrait de wikidata dumps) :
          {"itemLabel": "Paris", "propertyLabel": "pays", "valueLabel": "France"}
          {"itemLabel": "Paris", "propertyLabel": "population", "valueLabel": "2161000"}
        """
        path = Path(dump_path)
        if not path.exists():
            log.warning(f"Dump introuvable: {dump_path}")
            return 0

        log.info(f"Ingestion dump Wikidata: {dump_path}")
        t0 = time.time()
        count = 0

        with open(path, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f):
                if max_lines and line_no >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    triples = self._extract_triples(obj)
                    for s, r, o, sec in triples:
                        if self.kb:
                            self.kb.ingest(s, r, o, sec)
                        count += 1
                except (json.JSONDecodeError, KeyError):
                    self.stats['skipped'] += 1
                    continue

                if (line_no + 1) % 100000 == 0:
                    elapsed = time.time() - t0
                    rate = count / elapsed if elapsed > 0 else 0
                    log.info(f"Dump: {line_no+1:,} lignes → {count:,} faits "
                             f"({rate:.0f} faits/s)")

        if self.kb:
            self.kb.save_all()

        elapsed = time.time() - t0
        log.info(f"Dump terminé: {count:,} faits en {elapsed:.0f}s "
                 f"({count/elapsed:.0f} faits/s)")
        return count

    def _extract_triples(self, obj: dict) -> List[Tuple[str, str, str, str]]:
        """Extrait les triplets d'un objet Wikidata (format dump simplifié)."""
        triples = []
        item = obj.get('itemLabel', '').strip()
        if not item or len(item) < 2:
            return triples

        prop = obj.get('propertyLabel', '').strip()
        value = obj.get('valueLabel', '').strip()
        prop_id = obj.get('propertyID', '')

        if prop and value:
            # Déterminer le secteur
            secteur = self._map_to_sector(prop_id, prop)
            triples.append((item, prop.lower(), value, secteur))

        # Champs additionnels courants
        for field, relation, default_sector in [
            ('instanceOfLabel', 'est une instance de', 'GENERAL'),
            ('subclassOfLabel', 'est une sous-classe de', 'GENERAL'),
            ('countryLabel', 'est situé en', 'GEOGRAPHIE'),
            ('continentLabel', 'est situé sur le continent', 'GEOGRAPHIE'),
            ('capitalLabel', 'a pour capitale', 'GEOGRAPHIE'),
            ('inceptionLabel', 'a été créé en', 'HISTOIRE'),
            ('discovererLabel', 'a été découvert par', 'SCIENCES'),
            ('creatorLabel', 'a été créé par', 'CREATION'),
            ('authorLabel', 'a pour auteur', 'CREATION'),
            ('composerLabel', 'a été composé par', 'CULTURE'),
        ]:
            val = obj.get(field, '').strip()
            if val and len(val) > 1:
                triples.append((item, relation, val, default_sector))

        return triples

    def _map_to_sector(self, prop_id: str, prop_label: str) -> str:
        """Mappe une propriété Wikidata vers un secteur harmonique."""
        # D'abord par ID
        if prop_id and prop_id in PROPERTY_SECTOR_MAP:
            return PROPERTY_SECTOR_MAP[prop_id]

        # Ensuite par mots-clés dans le label
        prop_lower = prop_label.lower()
        for secteur, keywords in SECTOR_KEYWORDS.items():
            for kw in keywords:
                if kw in prop_lower:
                    return secteur

        return 'GENERAL'

    # ── MODE API ───────────────────────────────────────────────────────────

    def ingest_api(self, max_entities: int = 1000, batch_size: int = 50) -> int:
        """
        Ingère des entités via l'API Wikidata REST.

        Limité à ~50 requêtes/min (rate limit Wikidata).
        """
        log.info(f"Ingestion API Wikidata: max {max_entities} entités")
        count = 0

        # Liste d'entités importantes à ingérer
        important_ids = self._get_important_entity_ids()[:max_entities]

        for i, qid in enumerate(important_ids):
            if i % batch_size == 0 and i > 0:
                time.sleep(1.5)  # respecter le rate limit

            triples = self._fetch_entity(qid)
            for s, r, o, sec in triples:
                if self.kb:
                    self.kb.ingest(s, r, o, sec)
                count += 1

            if (i + 1) % 100 == 0:
                log.info(f"API: {i+1}/{len(important_ids)} entités → {count} faits")

        if self.kb:
            self.kb.save_all()
        return count

    def _fetch_entity(self, qid: str) -> List[Tuple[str, str, str, str]]:
        """Fetch une entité Wikidata via l'API REST."""
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "HarmonicAI/3.2 (research)"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            self.stats['errors'] += 1
            return []

        triples = []
        entity_data = data.get('entities', {}).get(qid, {})
        labels = entity_data.get('labels', {})
        item_label = labels.get('fr', {}).get('value') or labels.get('en', {}).get('value', qid)
        claims = entity_data.get('claims', {})

        for prop_id, claim_list in claims.items():
            # Récupérer le label de la propriété
            prop_label = self._get_property_label(data, prop_id)
            if not prop_label:
                continue

            for claim in claim_list:
                mainsnak = claim.get('mainsnak', {})
                if mainsnak.get('snaktype') != 'value':
                    continue
                datavalue = mainsnak.get('datavalue', {})
                value = datavalue.get('value', {})

                # Extraire la valeur selon le type
                if isinstance(value, dict):
                    # Lien vers une autre entité
                    if 'id' in value:
                        target_qid = value['id']
                        target_label = self._get_entity_label(data, target_qid)
                        if target_label:
                            secteur = self._map_to_sector(prop_id, prop_label)
                            triples.append((item_label, prop_label.lower(), target_label, secteur))
                    # Quantité
                    elif 'amount' in value:
                        amount = value['amount']
                        unit = value.get('unit', '').split('/')[-1]
                        val_str = f"{amount} {unit}" if unit else amount
                        secteur = self._map_to_sector(prop_id, prop_label)
                        triples.append((item_label, prop_label.lower(), val_str, secteur))
                    # Time
                    elif 'time' in value:
                        time_val = value['time'].lstrip('+').split('T')[0]
                        if time_val and time_val != '0000-00-00':
                            secteur = self._map_to_sector(prop_id, prop_label)
                            triples.append((item_label, prop_label.lower(), time_val, secteur))
                elif isinstance(value, str):
                    secteur = self._map_to_sector(prop_id, prop_label)
                    triples.append((item_label, prop_label.lower(), value, secteur))

        return triples

    def _get_property_label(self, data: dict, prop_id: str) -> Optional[str]:
        """Récupère le label d'une propriété Wikidata."""
        prop_data = data.get('entities', {}).get(prop_id, {})
        labels = prop_data.get('labels', {})
        return labels.get('fr', {}).get('value') or labels.get('en', {}).get('value')

    def _get_entity_label(self, data: dict, qid: str) -> Optional[str]:
        """Récupère le label d'une entité Wikidata."""
        entity = data.get('entities', {}).get(qid, {})
        labels = entity.get('labels', {})
        return labels.get('fr', {}).get('value') or labels.get('en', {}).get('value')

    def _get_important_entity_ids(self) -> List[str]:
        """Liste d'entités Wikidata importantes (Q-IDs)."""
        return [
            # Pays
            'Q142', 'Q30', 'Q17', 'Q155', 'Q145', 'Q183', 'Q38', 'Q183',
            'Q148', 'Q16', 'Q39', 'Q40', 'Q43', 'Q77', 'Q79', 'Q96',
            'Q114', 'Q115', 'Q116', 'Q117', 'Q118', 'Q119',
            # Villes
            'Q90', 'Q1490', 'Q84', 'Q64', 'Q72', 'Q1741', 'Q61', 'Q62',
            'Q174', 'Q65', 'Q71', 'Q649', 'Q85', 'Q87', 'Q89',
            # Scientifiques
            'Q937', 'Q868', 'Q764', 'Q710', 'Q528', 'Q7251', 'Q5582',
            'Q41568', 'Q2283', 'Q1545',
            # Œuvres
            'Q12418', 'Q40362', 'Q12511', 'Q185268', 'Q41415',
            # Concepts
            'Q1', 'Q2', 'Q3', 'Q5', 'Q7', 'Q9', 'Q10', 'Q15', 'Q19', 'Q21',
            'Q22', 'Q23', 'Q24', 'Q25', 'Q26', 'Q27', 'Q28', 'Q29',
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR SYNTHÉTIQUE — Test à l'échelle (1M - 10M faits)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_synthetic_facts(count: int = 1_000_000,
                             seed: int = 42) -> Iterator[Tuple[str, str, str, str]]:
    """
    Générateur de faits synthétiques réalistes pour tests à l'échelle.

    Produit des triplets variés simulant un dump Wikidata :
      · Pays → capitales, populations, superficies
      · Villes → pays, fondation, monuments
      · Personnes → naissance, profession, œuvres
      · Éléments chimiques → propriétés
      · Espèces → classification
      · Universités, entreprises, découvertes...

    Usage :
        from kb_scaler import ShardedKB
        kb = ShardedKB()
        kb.ingest_batch(list(generate_synthetic_facts(5_000_000)))
    """
    import random
    rng = random.Random(seed)
    
    # Templates de faits réalistes
    countries = [
        'France', 'Japon', 'Brésil', 'Kenya', 'Canada', 'Australie',
        'Inde', 'Allemagne', 'Égypte', 'Pérou', 'Nigeria', 'Corée du Sud',
        'Italie', 'Espagne', 'Portugal', 'Grèce', 'Turquie', 'Iran',
        'Thaïlande', 'Vietnam', 'Mexique', 'Argentine', 'Colombie', 'Chili',
        'Maroc', 'Sénégal', 'Côte d\'Ivoire', 'Ghana', 'Éthiopie', 'Tanzanie',
        'Norvège', 'Suède', 'Finlande', 'Danemark', 'Pologne', 'Ukraine',
        'Roumanie', 'Hongrie', 'Autriche', 'Suisse', 'Belgique', 'Pays-Bas',
    ]
    
    cities = [
        'Paris', 'Tokyo', 'Brasilia', 'Nairobi', 'Ottawa', 'Sydney',
        'New Delhi', 'Berlin', 'Le Caire', 'Lima', 'Abuja', 'Séoul',
        'Rome', 'Madrid', 'Lisbonne', 'Athènes', 'Ankara', 'Téhéran',
        'Bangkok', 'Hanoi', 'Mexico', 'Buenos Aires', 'Bogota', 'Santiago',
        'Rabat', 'Dakar', 'Abidjan', 'Accra', 'Addis-Abeba', 'Dodoma',
    ]
    
    scientists = [
        'Albert Einstein', 'Marie Curie', 'Isaac Newton', 'Galileo Galilei',
        'Charles Darwin', 'Nikola Tesla', 'Louis Pasteur', 'Ada Lovelace',
        'Alan Turing', 'Rosalind Franklin', 'Stephen Hawking', 'Richard Feynman',
        'Niels Bohr', 'Max Planck', 'Gregor Mendel', 'Barbara McClintock',
        'Carl Sagan', 'Jane Goodall', 'Katherine Johnson', 'Chien-Shiung Wu',
    ]
    
    artists = [
        'Leonard de Vinci', 'Michel-Ange', 'Vincent van Gogh', 'Pablo Picasso',
        'Frida Kahlo', 'Claude Monet', 'Rembrandt', 'Salvador Dali',
        'Georgia O\'Keeffe', 'Hokusai', 'Diego Rivera', 'Henri Matisse',
    ]
    
    elements = [
        ('Hydrogène', 'H', 1, 1.008), ('Hélium', 'He', 2, 4.003),
        ('Lithium', 'Li', 3, 6.941), ('Béryllium', 'Be', 4, 9.012),
        ('Bore', 'B', 5, 10.81), ('Carbone', 'C', 6, 12.01),
        ('Azote', 'N', 7, 14.01), ('Oxygène', 'O', 8, 16.00),
        ('Fluor', 'F', 9, 19.00), ('Néon', 'Ne', 10, 20.18),
        ('Sodium', 'Na', 11, 22.99), ('Magnésium', 'Mg', 12, 24.31),
        ('Aluminium', 'Al', 13, 26.98), ('Silicium', 'Si', 14, 28.09),
        ('Phosphore', 'P', 15, 30.97), ('Soufre', 'S', 16, 32.07),
        ('Chlore', 'Cl', 17, 35.45), ('Argon', 'Ar', 18, 39.95),
        ('Potassium', 'K', 19, 39.10), ('Calcium', 'Ca', 20, 40.08),
        ('Fer', 'Fe', 26, 55.85), ('Cuivre', 'Cu', 29, 63.55),
        ('Argent', 'Ag', 47, 107.9), ('Or', 'Au', 79, 197.0),
        ('Mercure', 'Hg', 80, 200.6), ('Plomb', 'Pb', 82, 207.2),
        ('Uranium', 'U', 92, 238.0), ('Plutonium', 'Pu', 94, 244.0),
    ]
    
    sectors = [
        'GEOGRAPHIE', 'HISTOIRE', 'SCIENCES', 'PHYSIQUE_FOND',
        'CREATION', 'CULTURE', 'MATHS_PURES', 'BIOLOGIE',
        'ECONOMIE', 'POLITIQUE', 'SPIRITUALITE', 'GENERAL',
    ]
    
    relations_by_sector = {
        'GEOGRAPHIE': [
            'est la capitale de', 'est situé en', 'a une population de',
            'a une superficie de', 'est traversé par', 'partage une frontière avec',
            'est bordé par', 'a pour langue officielle', 'a pour monnaie',
            'se trouve sur le continent', 'est jumelé avec',
        ],
        'HISTOIRE': [
            'a été fondé en', 'a eu lieu en', 'a régné de', 'a été découvert en',
            'a été construit en', 'est mort en', 'a commencé en', 'a pris fin en',
            'a été signé en', 'a déclaré l\'indépendance en',
        ],
        'SCIENCES': [
            'a découvert', 'a pour numéro atomique', 'a pour symbole',
            'a une masse atomique de', 'appartient à la famille des',
            'a pour point de fusion', 'a pour point d\'ébullition',
            'a été synthétisé en', 'est classé comme',
        ],
        'PHYSIQUE_FOND': [
            'a pour vitesse', 'a pour masse', 'a pour charge',
            'est soumis à la force de', 'obéit à la loi de',
            'est décrit par l\'équation de', 'a une énergie de',
        ],
        'CREATION': [
            'a peint', 'a sculpté', 'a écrit', 'a composé',
            'a réalisé', 'a conçu', 'a inventé', 'a créé',
        ],
        'CULTURE': [
            'est l\'auteur de', 'a joué dans', 'a enregistré', 'a publié',
            'a reçu le prix', 'est connu pour', 'a influencé',
        ],
        'MATHS_PURES': [
            'est égal à', 'vaut approximativement', 'est solution de',
            'peut être factorisé en', 'appartient à l\'ensemble',
            'converge vers', 'tend vers',
        ],
        'BIOLOGIE': [
            'appartient au genre', 'est de la famille des', 'a pour habitat',
            'se nourrit de', 'a une espérance de vie de', 'pond',
            'est pollinisé par', 'produit',
        ],
        'ECONOMIE': [
            'a un PIB de', 'a pour partenaire commercial', 'exporte',
            'importe', 'a un taux de chômage de', 'a pour indice de développement',
        ],
    }

    generated = 0
    while generated < count:
        # Choisir un type de fait aléatoirement
        fact_type = rng.random()
        
        if fact_type < 0.20:  # Géographie — pays/villes
            country = rng.choice(countries)
            city = rng.choice(cities)
            rel = rng.choice(relations_by_sector['GEOGRAPHIE'])
            if 'capitale' in rel:
                yield (city, rel, country, 'GEOGRAPHIE')
            elif 'population' in rel:
                pop = rng.randint(50000, 50_000_000)
                yield (city, rel, f"{pop:,} habitants", 'GEOGRAPHIE')
            elif 'superficie' in rel:
                area = rng.randint(50, 10_000_000)
                yield (country, rel, f"{area:,} km²", 'GEOGRAPHIE')
            else:
                yield (country, rel, rng.choice(countries), 'GEOGRAPHIE')
                
        elif fact_type < 0.35:  # Sciences — éléments
            elem, symb, num, mass = rng.choice(elements)
            subrel = rng.choice([
                ('a pour numéro atomique', str(num), 'SCIENCES'),
                ('a pour symbole', symb, 'SCIENCES'),
                ('a une masse atomique de', str(mass), 'SCIENCES'),
            ])
            yield (elem, subrel[0], subrel[1], subrel[2])
            
        elif fact_type < 0.50:  # Histoire
            person = rng.choice(scientists + artists)
            country = rng.choice(countries)
            year = rng.randint(1200, 2025)
            rel = rng.choice(relations_by_sector['HISTOIRE'])
            if 'mort' in rel or 'né' in rel:
                yield (person, rel, str(year), 'HISTOIRE')
            else:
                yield (rng.choice(countries), rel, str(year), 'HISTOIRE')
                
        elif fact_type < 0.65:  # Création/Culture
            artist = rng.choice(artists)
            works = [
                'La Joconde', 'La Nuit étoilée', 'Guernica', 'Les Demoiselles d\'Avignon',
                'Le Penseur', 'David', 'La Création d\'Adam', 'Le Cri',
                'Les Tournesols', 'La Persistance de la mémoire', 'American Gothic',
            ]
            rel = rng.choice(relations_by_sector['CREATION'])
            yield (artist, rel, rng.choice(works), 'CREATION')
            
        elif fact_type < 0.80:  # Biologie
            species = rng.choice([
                'Homo sapiens', 'Panthera leo', 'Canis lupus', 'Felis catus',
                'Equus caballus', 'Bos taurus', 'Gallus gallus', 'Apis mellifera',
                'Quercus robur', 'Triticum aestivum', 'Oryza sativa', 'Zea mays',
            ])
            rel = rng.choice(relations_by_sector['BIOLOGIE'])
            yield (species, rel, rng.choice(['Mammalia', 'Aves', 'Insecta', 'Plantae',
                   'Chordata', 'Arthropoda', 'Fungi', 'Bacteria']), 'BIOLOGIE')
            
        elif fact_type < 0.90:  # Maths
            const = rng.choice([
                'pi', 'phi', 'e', 'racine de 2', 'racine de 3', 'logarithme de 2',
                'constante de Planck', 'constante de Boltzmann', 'vitesse de la lumière',
            ])
            yield (const, 'vaut approximativement', f"{rng.random()*10:.6f}", 'MATHS_PURES')
            
        else:  # Général/Économie
            country = rng.choice(countries)
            yield (country, 'a un indice de développement de',
                   f"{rng.uniform(0.3, 0.95):.3f}", 'ECONOMIE')
        
        generated += 1
        
        # Ajouter 2-3 faits supplémentaires par entité (relations denses)
        if rng.random() < 0.3 and generated < count:
            country = rng.choice(countries)
            yield (country, 'fait partie de', rng.choice(['ONU', 'UNESCO', 'OMC', 'OTAN',
                   'Union Européenne', 'Union Africaine', 'ASEAN', 'Mercosur']), 'POLITIQUE')
            generated += 1


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("  WIKIDATA CONNECTOR — Test")
    print("=" * 60)

    # Test 1: Générateur synthétique
    print("\n── Test 1: Générateur synthétique (100K faits) ──")
    t0 = time.time()
    sample = list(generate_synthetic_facts(100_000))
    elapsed = time.time() - t0
    print(f"  {len(sample):,} faits générés en {elapsed:.1f}s")
    
    # Afficher quelques exemples
    print("  Exemples :")
    for i, (s, r, o, sec) in enumerate(sample[:5]):
        print(f"    {s} → {r} → {o} [{sec}]")

    # Distribution des secteurs
    from collections import Counter
    sector_dist = Counter(sec for _, _, _, sec in sample)
    print("\n  Distribution secteurs :")
    for sec, cnt in sector_dist.most_common(10):
        print(f"    {sec}: {cnt:,} ({100*cnt/len(sample):.1f}%)")

    # Test 2: Ingestion dans ShardedKB
    print("\n── Test 2: Ingestion dans ShardedKB ──")
    from kb_scaler import ShardedKB
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        kb = ShardedKB(shard_dir=tmpdir, max_active=2)
        t0 = time.time()
        kb.ingest_batch(sample)
        elapsed = time.time() - t0
        print(f"  {len(sample):,} faits ingérés en {elapsed:.1f}s "
              f"({len(sample)/elapsed:.0f} faits/s)")
        print(f"  Stats: {kb.stats}")

        # Test retrieval
        results = kb.retrieve("France", top_k=3)
        print(f"\n  Retrieval 'France': {len(results)} résultats")
        for f in results[:3]:
            print(f"    {f.sujet} → {f.relation} → {f.objet}")

    print("\n✅ Tests Wikidata Connector terminés")
