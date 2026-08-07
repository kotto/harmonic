"""
Wikidata Real Ingestion — Enrichissement Massif du KB Harmonique
==================================================================
Utilise SPARQL pour extraire des connaissances structurées de Wikidata
et les ingérer dans le ShardedKB.

CATÉGORIES (25 — haute qualité, haute densité) :
  ORIGINALES (8) :
    1. Pays + capitales + populations + superficies + continents
    2. Éléments chimiques + numéros atomiques + symboles + masses
    3. Scientifiques + découvertes + dates
    4. Artistes + œuvres majeures
    5. Monuments + localisations + dates de construction
    6. Espèces biologiques + classifications
    7. Prix Nobel + lauréats
    8. Langues + pays + nombre de locuteurs

  EXTENSION SANTÉ (4) :
    9.  Maladies + symptômes + traitements
    10. Médicaments + principes actifs + fabricants
    11. Anatomie humaine + organes + systèmes
    12. Vaccins + maladies ciblées + découvreurs

  EXTENSION GÉOGRAPHIE (2) :
    13. Villes + pays + populations + coordonnées
    14. Fleuves + longueurs + pays traversés

  EXTENSION SCIENCES (3) :
    15. Planètes + étoiles + constellations + découvreurs
    16. Particules physiques + forces + médiateurs
    17. Théorèmes + mathématiciens + domaines

  EXTENSION CULTURE (3) :
    18. Philosophes + concepts + écoles
    19. Inventions + inventeurs + dates
    20. Sports + records + athlètes

  EXTENSION ÉCONOMIE/SOCIÉTÉ (3) :
    21. Entreprises + secteurs + fondateurs + sièges
    22. Universités + fondation + pays
    23. Organisations internationales + membres + sièges

  EXTENSION NATURE (2) :
    24. Écosystèmes + biomes + caractéristiques
    25. Aliments + nutriments + origines

OBJECTIF : 100K+ faits réels de très haute qualité (sectorisés, bilingues).
"""

import json, time, urllib.request, urllib.parse, urllib.error, sys, logging
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "HarmonicAI/3.3 (https://github.com/kotto/harmonic; research)"
BATCH_SIZE = 10000

# ═══════════════════════════════════════════════════════════════════════════════
# REQUÊTES SPARQL — 8 catégories
# ═══════════════════════════════════════════════════════════════════════════════

QUERIES = {
    # 1. Pays + capitales + populations + superficies + continents (~200 pays × 4 propriétés = 800 faits)
    'countries': """
        SELECT ?pays ?paysLabel ?capitale ?capitaleLabel ?population ?superficie ?continent ?continentLabel
        WHERE {
          ?pays wdt:P31 wd:Q3624078.  # État souverain
          OPTIONAL { ?pays wdt:P36 ?capitale. }
          OPTIONAL { ?pays wdt:P1082 ?population. }
          OPTIONAL { ?pays wdt:P2046 ?superficie. }
          OPTIONAL { ?pays wdt:P30 ?continent. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 300
    """,
    
    # 2. Éléments chimiques (~120 éléments × 5 propriétés = 600 faits)
    'chemical_elements': """
        SELECT ?element ?elementLabel ?numero ?symbole ?masse ?decouvreur ?decouvreurLabel ?annee
        WHERE {
          ?element wdt:P31 wd:Q11344.  # élément chimique
          OPTIONAL { ?element wdt:P1086 ?numero. }
          OPTIONAL { ?element wdt:P246 ?symbole. }
          OPTIONAL { ?element wdt:P2067 ?masse. }
          OPTIONAL { ?element wdt:P61 ?decouvreur. }
          OPTIONAL { ?element wdt:P575 ?annee. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 150
    """,
    
    # 3. Scientifiques + découvertes (~5000 faits) — LIMIT réduit pour éviter timeout
    'scientists': """
        SELECT ?personne ?personneLabel ?decouverte ?decouverteLabel ?dateNaissance ?dateMort ?pays ?paysLabel
        WHERE {
          ?personne wdt:P106 wd:Q1650915.
          ?personne wdt:P800 ?decouverte.   # seulement ceux avec découverte connue
          OPTIONAL { ?personne wdt:P569 ?dateNaissance. }
          OPTIONAL { ?personne wdt:P570 ?dateMort. }
          OPTIONAL { ?personne wdt:P27 ?pays. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 500
    """,
    
    # 4. Artistes + œuvres majeures (~3000 faits)
    'artists': """
        SELECT ?artiste ?artisteLabel ?oeuvre ?oeuvreLabel ?dateNaissance ?dateMort ?mouvement ?mouvementLabel
        WHERE {
          ?artiste wdt:P106 wd:Q483501.  # artiste
          OPTIONAL { ?artiste wdt:P800 ?oeuvre. }
          OPTIONAL { ?artiste wdt:P569 ?dateNaissance. }
          OPTIONAL { ?artiste wdt:P570 ?dateMort. }
          OPTIONAL { ?artiste wdt:P135 ?mouvement. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 2000
    """,
    
    # 5. Monuments + localisations (~5000 faits)
    'monuments': """
        SELECT ?monument ?monumentLabel ?pays ?paysLabel ?ville ?villeLabel ?dateConstruction ?hauteur
        WHERE {
          ?monument wdt:P31 wd:Q4989906.  # monument
          OPTIONAL { ?monument wdt:P17 ?pays. }
          OPTIONAL { ?monument wdt:P131 ?ville. }
          OPTIONAL { ?monument wdt:P571 ?dateConstruction. }
          OPTIONAL { ?monument wdt:P2048 ?hauteur. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 3000
    """,
    
    # 6. Espèces biologiques (~5000 faits)
    'species': """
        SELECT ?espece ?especeLabel ?genre ?genreLabel ?famille ?familleLabel ?ordre ?ordreLabel ?decouvreur ?decouvreurLabel
        WHERE {
          ?espece wdt:P105 wd:Q7432.  # espèce
          OPTIONAL { ?espece wdt:P171 ?genre. }
          OPTIONAL { ?espece wdt:P177 ?famille. }
          OPTIONAL { ?espece wdt:P178 ?ordre. }
          OPTIONAL { ?espece wdt:P61 ?decouvreur. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 3000
    """,
    
    # 7. Prix Nobel + lauréats (~2000 faits)
    'nobel': """
        SELECT ?laureat ?laureatLabel ?prix ?prixLabel ?annee ?motivation
        WHERE {
          ?laureat wdt:P166 wd:Q7191.  # Prix Nobel
          OPTIONAL { ?laureat wdt:P166 ?prix. }
          OPTIONAL { ?laureat wdt:P585 ?annee. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 2000
    """,
    
    # 8. Langues + pays (~1000 faits)
    'languages': """
        SELECT ?langue ?langueLabel ?pays ?paysLabel ?locuteurs ?famille ?familleLabel
        WHERE {
          ?langue wdt:P31 wd:Q34770.  # langue
          OPTIONAL { ?langue wdt:P17 ?pays. }
          OPTIONAL { ?langue wdt:P1098 ?locuteurs. }
          OPTIONAL { ?langue wdt:P279 ?famille. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 1000
    """,

    # ═══ EXTENSION SANTÉ (4 catégories) ═══

    # 9. Maladies + symptômes + traitements (~8000 faits)
    'diseases': """
        SELECT ?maladie ?maladieLabel ?symptome ?symptomeLabel ?traitement ?traitementLabel ?specialite ?specialiteLabel
        WHERE {
          ?maladie wdt:P31 wd:Q12136.  # maladie
          OPTIONAL { ?maladie wdt:P780 ?symptome. }
          OPTIONAL { ?maladie wdt:P2176 ?traitement. }
          OPTIONAL { ?maladie wdt:P1995 ?specialite. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 4000
    """,

    # 10. Médicaments + principes actifs + fabricants (~5000 faits)
    'medications': """
        SELECT ?medicament ?medicamentLabel ?principeActif ?principeActifLabel ?fabricant ?fabricantLabel ?voieAdmin ?voieAdminLabel
        WHERE {
          ?medicament wdt:P31 wd:Q12140.  # médicament
          OPTIONAL { ?medicament wdt:P3780 ?principeActif. }
          OPTIONAL { ?medicament wdt:P176 ?fabricant. }
          OPTIONAL { ?medicament wdt:P636 ?voieAdmin. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 3000
    """,

    # 11. Anatomie humaine (~4000 faits)
    'anatomy': """
        SELECT ?organe ?organeLabel ?systeme ?systemeLabel ?fonction ?fonctionLabel ?localisation ?localisationLabel
        WHERE {
          ?organe wdt:P31 wd:Q712378.  # structure anatomique
          OPTIONAL { ?organe wdt:P279 ?systeme. }   # sous-classe de (système)
          OPTIONAL { ?organe wdt:P366 ?fonction. }   # utilisation/fonction
          OPTIONAL { ?organe wdt:P276 ?localisation. } # localisation
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 2500
    """,

    # 12. Vaccins + maladies ciblées + découvreurs (~2000 faits)
    'vaccines': """
        SELECT ?vaccin ?vaccinLabel ?maladieCible ?maladieCibleLabel ?decouvreur ?decouvreurLabel ?annee
        WHERE {
          ?vaccin wdt:P31 wd:Q134808.  # vaccin
          OPTIONAL { ?vaccin wdt:P2175 ?maladieCible. }
          OPTIONAL { ?vaccin wdt:P61 ?decouvreur. }
          OPTIONAL { ?vaccin wdt:P575 ?annee. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 1000
    """,

    # ═══ EXTENSION GÉOGRAPHIE (2 catégories) ═══

    # 13. Villes + pays + populations (~15000 faits)
    'cities': """
        SELECT ?ville ?villeLabel ?pays ?paysLabel ?population ?superficie ?coordonnees
        WHERE {
          ?ville wdt:P31 wd:Q515.  # ville
          OPTIONAL { ?ville wdt:P17 ?pays. }
          OPTIONAL { ?ville wdt:P1082 ?population. }
          OPTIONAL { ?ville wdt:P2046 ?superficie. }
          OPTIONAL { ?ville wdt:P625 ?coordonnees. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 5000
    """,

    # 14. Fleuves + longueurs + pays traversés (~2000 faits)
    'rivers': """
        SELECT ?fleuve ?fleuveLabel ?longueur ?pays ?paysLabel ?embouchure ?embouchureLabel
        WHERE {
          ?fleuve wdt:P31 wd:Q4022.  # rivière/fleuve
          OPTIONAL { ?fleuve wdt:P2043 ?longueur. }
          OPTIONAL { ?fleuve wdt:P17 ?pays. }
          OPTIONAL { ?fleuve wdt:P403 ?embouchure. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 2000
    """,

    # ═══ EXTENSION SCIENCES (3 catégories) ═══

    # 15. Planètes + étoiles + découvreurs (~2000 faits)
    'astronomy': """
        SELECT ?corps ?corpsLabel ?type ?typeLabel ?decouvreur ?decouvreurLabel ?annee ?distance
        WHERE {
          { ?corps wdt:P31 wd:Q634. } UNION { ?corps wdt:P31 wd:Q523. }  # planète ou étoile
          OPTIONAL { ?corps wdt:P61 ?decouvreur. }
          OPTIONAL { ?corps wdt:P575 ?annee. }
          OPTIONAL { ?corps wdt:P2583 ?distance. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 1500
    """,

    # 16. Particules physiques + forces (~1000 faits)
    'particles': """
        SELECT ?particule ?particuleLabel ?type ?typeLabel ?force ?forceLabel ?masse ?charge
        WHERE {
          { ?particule wdt:P31 wd:Q6181. } UNION { ?particule wdt:P31 wd:Q66205. }  # particule ou particule élémentaire
          OPTIONAL { ?particule wdt:P2067 ?masse. }
          OPTIONAL { ?particule wdt:P246 ?charge. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 500
    """,

    # 17. Théorèmes + mathématiciens + domaines (~2000 faits)
    'theorems': """
        SELECT ?theoreme ?theoremeLabel ?mathématicien ?mathématicienLabel ?domaine ?domaineLabel ?annee
        WHERE {
          ?theoreme wdt:P31 wd:Q65943.  # théorème
          OPTIONAL { ?theoreme wdt:P61 ?mathématicien. }
          OPTIONAL { ?theoreme wdt:P101 ?domaine. }
          OPTIONAL { ?theoreme wdt:P575 ?annee. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 1000
    """,

    # ═══ EXTENSION CULTURE (3 catégories) ═══

    # 18. Philosophes + concepts + écoles (~3000 faits)
    'philosophers': """
        SELECT ?philosophe ?philosopheLabel ?concept ?conceptLabel ?ecole ?ecoleLabel ?dateNaissance ?dateMort
        WHERE {
          ?philosophe wdt:P106 wd:Q4964182.  # philosophe
          OPTIONAL { ?philosophe wdt:P800 ?concept. }
          OPTIONAL { ?philosophe wdt:P135 ?ecole. }
          OPTIONAL { ?philosophe wdt:P569 ?dateNaissance. }
          OPTIONAL { ?philosophe wdt:P570 ?dateMort. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 1500
    """,

    # 19. Inventions + inventeurs + dates (~4000 faits)
    'inventions': """
        SELECT ?invention ?inventionLabel ?inventeur ?inventeurLabel ?date ?pays ?paysLabel
        WHERE {
          ?invention wdt:P31 wd:Q1429755.  # invention
          OPTIONAL { ?invention wdt:P61 ?inventeur. }
          OPTIONAL { ?invention wdt:P575 ?date. }
          OPTIONAL { ?invention wdt:P17 ?pays. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 2000
    """,

    # 20. Sports + records + athlètes (~5000 faits)
    'sports': """
        SELECT ?sport ?sportLabel ?athlete ?athleteLabel ?record ?recordLabel ?paysOrigine ?paysOrigineLabel
        WHERE {
          ?sport wdt:P31 wd:Q31629.  # sport
          OPTIONAL { ?sport wdt:P2410 ?athlete. }  # pratiqué par
          OPTIONAL { ?sport wdt:P3000 ?record. }    # record
          OPTIONAL { ?sport wdt:P495 ?paysOrigine. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 2500
    """,

    # ═══ EXTENSION ÉCONOMIE/SOCIÉTÉ (3 catégories) ═══

    # 21. Entreprises + secteurs + fondateurs (~5000 faits)
    'companies': """
        SELECT ?entreprise ?entrepriseLabel ?secteur ?secteurLabel ?fondateur ?fondateurLabel ?siege ?siegeLabel ?creation
        WHERE {
          ?entreprise wdt:P31 wd:Q4830453.  # entreprise
          OPTIONAL { ?entreprise wdt:P452 ?secteur. }
          OPTIONAL { ?entreprise wdt:P112 ?fondateur. }
          OPTIONAL { ?entreprise wdt:P159 ?siege. }
          OPTIONAL { ?entreprise wdt:P571 ?creation. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 3000
    """,

    # 22. Universités + fondation + pays (~3000 faits)
    'universities': """
        SELECT ?universite ?universiteLabel ?pays ?paysLabel ?fondation ?ville ?villeLabel ?type ?typeLabel
        WHERE {
          ?universite wdt:P31 wd:Q3918.  # université
          OPTIONAL { ?universite wdt:P17 ?pays. }
          OPTIONAL { ?universite wdt:P571 ?fondation. }
          OPTIONAL { ?universite wdt:P131 ?ville. }
          OPTIONAL { ?universite wdt:P31 ?type. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 2000
    """,

    # 23. Organisations internationales (~2000 faits)
    'organizations': """
        SELECT ?organisation ?organisationLabel ?type ?typeLabel ?siege ?siegeLabel ?fondation ?membres
        WHERE {
          ?organisation wdt:P31 wd:Q484652.  # organisation internationale
          OPTIONAL { ?organisation wdt:P31 ?type. }
          OPTIONAL { ?organisation wdt:P159 ?siege. }
          OPTIONAL { ?organisation wdt:P571 ?fondation. }
          OPTIONAL { ?organisation wdt:P2124 ?membres. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 1500
    """,

    # ═══ EXTENSION NATURE (2 catégories) ═══

    # 24. Écosystèmes + biomes (~3000 faits)
    'ecosystems': """
        SELECT ?ecosysteme ?ecosystemeLabel ?type ?typeLabel ?localisation ?localisationLabel ?superficie ?especesCles ?especesClesLabel
        WHERE {
          ?ecosysteme wdt:P31 wd:Q37813.  # écosystème
          OPTIONAL { ?ecosysteme wdt:P31 ?type. }
          OPTIONAL { ?ecosysteme wdt:P276 ?localisation. }
          OPTIONAL { ?ecosysteme wdt:P2046 ?superficie. }
          OPTIONAL { ?ecosysteme wdt:P225 ?especesCles. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 1500
    """,

    # 25. Aliments + nutriments + origines (~3000 faits)
    'foods': """
        SELECT ?aliment ?alimentLabel ?nutriment ?nutrimentLabel ?origine ?origineLabel ?type ?typeLabel
        WHERE {
          ?aliment wdt:P31 wd:Q2095.  # aliment
          OPTIONAL { ?aliment wdt:P495 ?origine. }
          OPTIONAL { ?aliment wdt:P527 ?nutriment. }  # a pour partie (nutriment)
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 2000
    """,
}

# ═══════════════════════════════════════════════════════════════════════════════
# PARSING SPARQL → TRIPLETS
# ═══════════════════════════════════════════════════════════════════════════════

PROPERTY_SECTORS = {
    # Géographie
    'P36': 'GEOGRAPHIE', 'P1082': 'GEOGRAPHIE', 'P2046': 'GEOGRAPHIE',
    'P30': 'GEOGRAPHIE', 'P17': 'GEOGRAPHIE', 'P131': 'GEOGRAPHIE',
    'P625': 'GEOGRAPHIE', 'P2048': 'GEOGRAPHIE', 'P27': 'GEOGRAPHIE',
    'P2043': 'GEOGRAPHIE', 'P403': 'GEOGRAPHIE',
    # Sciences
    'P1086': 'SCIENCES', 'P246': 'SCIENCES', 'P2067': 'SCIENCES',
    'P800': 'SCIENCES', 'P61': 'SCIENCES', 'P828': 'SCIENCES',
    'P101': 'SCIENCES', 'P2583': 'SCIENCES',
    # Histoire
    'P569': 'HISTOIRE', 'P570': 'HISTOIRE', 'P571': 'HISTOIRE',
    'P575': 'HISTOIRE', 'P585': 'HISTOIRE',
    # Culture
    'P166': 'CULTURE', 'P135': 'CULTURE', 'P1098': 'CULTURE',
    'P495': 'CULTURE',
    # Biologie/Santé
    'P171': 'BIOLOGIE', 'P177': 'BIOLOGIE', 'P178': 'BIOLOGIE',
    'P105': 'BIOLOGIE', 'P780': 'SANTE', 'P2176': 'SANTE',
    'P1995': 'SANTE', 'P3780': 'SANTE', 'P636': 'SANTE',
    'P2175': 'SANTE', 'P366': 'BIOLOGIE', 'P276': 'BIOLOGIE',
    # Corps/Anatomie
    'P279': 'BIOLOGIE',
    # Général
    'P106': 'GENERAL', 'P31': 'GENERAL', 'P452': 'ECONOMIE',
    # Société
    'P112': 'ECONOMIE', 'P159': 'ECONOMIE', 'P2124': 'POLITIQUE',
    # Nature
    'P225': 'BIOLOGIE', 'P527': 'BIOLOGIE',
    # Sport
    'P2410': 'CULTURE', 'P3000': 'CULTURE',
}

def parse_sparql_bindings(data: dict, query_name: str) -> List[Tuple[str, str, str, str]]:
    """Parse les résultats SPARQL en triplets (sujet, relation, objet, secteur).
    
    Stratégie corrigée :
    - Utilise TOUJOURS les Labels pour sujets et objets quand disponibles
    - Ignore les champs dont la valeur est une URI Wikidata sans Label
    - Filtre les Q-IDs (labels qui sont des identifiants bruts)
    """
    triples = []
    bindings = data.get('results', {}).get('bindings', [])
    
    def _is_uri(val: str) -> bool:
        return 'wikidata.org/entity/' in val or 'wikidata.org/prop/' in val
    
    def _is_qid(val: str) -> bool:
        """Détecte les Q-IDs bruts (ex: 'Q25413366')"""
        import re
        return bool(re.match(r'^Q\d+$', val.strip()))
    
    for b in bindings:
        # Construire le label_map : nom_base → label_humain
        label_map = {}
        for k in b:
            if k.endswith('Label') and not k.startswith('_'):
                base_name = k.replace('Label', '')
                label_val = b[k].get('value', '')
                # Ignorer les Q-IDs comme labels (Wikidata bug)
                if label_val and not _is_qid(label_val) and not _is_uri(label_val):
                    label_map[base_name] = label_val
        
        # Trouver le sujet (premier Label valide)
        sujet = None
        sujet_key = None
        sujet_base = None
        
        for k in b:
            if k.endswith('Label') and not k.startswith('_'):
                base = k.replace('Label', '')
                if base in label_map:
                    sujet = label_map[base]
                    sujet_key = k
                    sujet_base = base
                    break
        
        if not sujet:
            continue
        
        # Pour chaque champ NON-Label, créer un fait
        for key in b:
            if key == sujet_key or key.endswith('Label') or key.startswith('_'):
                continue
            if key == sujet_base:
                continue
            
            val = b[key].get('value', '')
            if not val or len(str(val)) < 1:
                continue
            
            # Déterminer l'objet : préférer le Label, sinon valeur brute
            if key in label_map:
                objet = label_map[key]
            else:
                # Pas de Label → si c'est un nombre/date, le garder ; si URI, ignorer
                str_val = str(val)
                if _is_uri(str_val):
                    continue  # URI sans Label → inutilisable
                if _is_qid(str_val):
                    continue  # Q-ID → inutilisable
                objet = str_val
            
            # Vérification finale de l'objet
            if _is_uri(str(objet)) or _is_qid(str(objet)):
                continue
            if str(objet).lower().strip()[:30] == sujet.lower().strip()[:30]:
                continue  # tautologie
            
            # Déterminer la relation et le secteur
            prop_name = key.replace('_', ' ')
            relation = prop_name
            
            secteur = 'GENERAL'
            for pid, sec in PROPERTY_SECTORS.items():
                if pid.lower() in key.lower():
                    secteur = sec
                    break
            
            # Traduire les relations courantes
            relation_map = {
                # Géographie
                'capitale': 'a pour capitale',
                'population': 'a une population de',
                'superficie': 'a une superficie de',
                'continent': 'est situé sur le continent',
                'hauteur': 'a une hauteur de',
                'ville': 'est situé à',
                'pays': 'est situé en',
                'longueur': 'a une longueur de',
                'embouchure': 'a pour embouchure',
                'coordonnees': 'a pour coordonnées',
                # Sciences
                'numero': 'a pour numéro atomique',
                'symbole': 'a pour symbole chimique',
                'masse': 'a une masse atomique de',
                'decouvreur': 'a été découvert par',
                'annee': 'a été découvert en',
                'dateNaissance': 'est né en',
                'dateMort': 'est mort en',
                'dateConstruction': 'a été construit en',
                'date': 'date de',
                'distance': 'a une distance de',
                'charge': 'a une charge de',
                # Art/Culture
                'oeuvre': 'a créé',
                'mouvement': 'appartient au mouvement',
                'prix': 'a reçu le prix',
                'locuteurs': 'a pour nombre de locuteurs',
                'fondation': 'a été fondé en',
                'creation': 'a été créé en',
                # Biologie
                'genre': 'appartient au genre',
                'famille': 'appartient à la famille',
                'ordre': 'appartient à l\'ordre',
                # Santé
                'symptome': 'a pour symptôme',
                'traitement': 'a pour traitement',
                'specialite': 'relève de la spécialité',
                'principeActif': 'a pour principe actif',
                'fabricant': 'est fabriqué par',
                'voieAdmin': 's\'administre par voie',
                'maladieCible': 'cible la maladie',
                'systeme': 'appartient au système',
                'fonction': 'a pour fonction',
                'localisation': 'est localisé dans',
                # Société
                'secteur': 'opère dans le secteur',
                'fondateur': 'a été fondé par',
                'siege': 'a son siège à',
                'membres': 'a pour nombre de membres',
                # Divers
                'inventeur': 'a été inventé par',
                'concept': 'a développé le concept',
                'ecole': 'appartient à l\'école',
                'domaine': 'appartient au domaine',
                'mathematicien': 'a été démontré par',
                'athlete': 'est pratiqué par',
                'record': 'a pour record',
                'paysOrigine': 'est originaire de',
                'type': 'est de type',
                'origine': 'est originaire de',
                'nutriment': 'contient le nutriment',
                'especesCles': 'abrite l\'espèce clé',
                'philosophe': 'a été pensé par',
            }
            
            for kw, rel in relation_map.items():
                if kw in key.lower():
                    relation = rel
                    break
            
            triples.append((sujet, relation, str(val), secteur))
    
    return triples

# ═══════════════════════════════════════════════════════════════════════════════
# FETCH + INGEST
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_sparql(query: str, timeout: int = 60) -> dict:
    """Exécute une requête SPARQL."""
    url = f"{SPARQL_ENDPOINT}?format=json&query={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        log.error(f"SPARQL error: {e}")
        return {}

def ingest_all(kb, target: int = 500_000):
    """Ingère toutes les catégories Wikidata."""
    total = 0
    t0 = time.time()
    
    for name, query in QUERIES.items():
        if total >= target:
            break
        
        log.info(f"📡 SPARQL {name}...")
        
        try:
            data = fetch_sparql(query)
            triples = parse_sparql_bindings(data, name)
            
            if not triples:
                log.warning(f"  ⚠️ 0 triplets pour {name}")
                continue
            
            # Déduplication
            seen = set()
            unique = []
            for s, r, o, sec in triples:
                key = (s.lower().strip()[:60], r.lower().strip()[:60], str(o).lower().strip()[:80])
                if key not in seen:
                    seen.add(key)
                    unique.append((s, r, o, sec))
            
            # Sectorisation automatique (remplace les secteurs GENERAL)
            try:
                from auto_sectorize import sectorize_batch
                unique = sectorize_batch(unique, min_confidence=1.5)
            except ImportError:
                pass
            
            # Ingérer
            kb.ingest_batch(unique)
            total += len(unique)
            
            log.info(f"  ✅ {name}: {len(triples):,} triplets → {len(unique):,} uniques "
                     f"(total: {total:,})")
        
        except Exception as e:
            log.error(f"  ❌ {name}: {e}")
        
        time.sleep(0.3)  # respecter le rate limit
    
    kb.save_all()
    elapsed = time.time() - t0
    log.info(f"🎉 Ingestion terminée: {total:,} faits en {elapsed:.0f}s "
             f"({total/elapsed:.0f}/s)")
    return total

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from kb_scaler import ShardedKB
    
    print("=" * 60)
    print("  WIKIDATA REAL INGESTION")
    print("  Remplace les 500K synthétiques par des vrais faits")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=int, default=500_000)
    parser.add_argument('--shard-dir', type=str, default='data/kb_shards_real')
    args = parser.parse_args()
    
    kb = ShardedKB(shard_dir=args.shard_dir, max_active=3)
    
    total = ingest_all(kb, target=args.target)
    
    print()
    print(f"  ✅ {total:,} faits réels ingérés")
    print(f"  📂 {kb.stats['shards']} shards, ~{kb.stats['estimated_ram_mb']} MB RAM")
    print(f"  📂 {args.shard_dir}")
    
    # Stats par secteur
    sectors = defaultdict(int)
    for shard in kb.shards.values():
        if shard._loaded:
            for f in shard.facts:
                sectors[f.secteur] += 1
        else:
            shard.load()
            for f in shard.facts:
                sectors[f.secteur] += 1
            shard.unload()
    
    print()
    print("  Distribution secteurs :")
    for sec, n in sorted(sectors.items(), key=lambda x: -x[1])[:10]:
        print(f"    {sec}: {n:,}")
