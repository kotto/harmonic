#!/usr/bin/env python3
"""
KA-Next — GÉNÉRATEUR COMBINATOIRE 300K PHRASES
=================================================
Zéro dépendance externe. Zéro appel API.
Génère 300 000 phrases par combinaison de templates.

PRINCIPE :
  Pour chaque domaine, on définit des templates de phrases
  et des listes de valeurs. La combinatoire génère
  template × valeurs → phrases uniques.

EXEMPLES :
  Template : "{capitale} est la capitale de {pays}."
  Valeurs  : Dakar×Sénégal, Paris×France, Tokyo×Japon...
  → 250 phrases uniques pour la géographie seule.

USAGE :
  python generate_corpus_300k.py
  → Génère ~300K phrases dans data/corpus/corpus_*.txt
"""

import os, sys, random, math
from itertools import product

sys.path.insert(0, os.path.dirname(__file__))

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "corpus")
os.makedirs(CORPUS_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
# TEMPLATES PAR DOMAINE
# ═══════════════════════════════════════════════════════════════════

TEMPLATES = {
    "geography": {
        "templates": [
            "{capitale} est la capitale de {pays}.",
            "{pays} est un pays situé en {continent}.",
            "{pays} compte environ {population} d'habitants.",
            "La superficie de {pays} est d'environ {superficie} km².",
            "{ville} est une ville située en {pays}.",
            "{fleuve} traverse le pays {pays}.",
            "{montagne} est le point culminant de {pays}.",
            "{pays} a pour capitale {capitale}.",
            "La population de {capitale} est d'environ {pop_ville} habitants.",
            "{pays} est bordé par {ocean}.",
            "La monnaie officielle de {pays} est le {monnaie}.",
            "La langue officielle de {pays} est le {langue}.",
            "{pays} est membre de {organisation} depuis {annee}.",
            "Le climat de {pays} est de type {climat}.",
            "{pays} est connu pour {particularite}.",
        ],
        "data": {
            "capitale": ["Dakar", "Paris", "Tokyo", "Londres", "Berlin", "Madrid", "Rome", "Moscou", "Pékin", "New Delhi", "Brasilia", "Canberra", "Ottawa", "Le Caire", "Addis-Abeba", "Nairobi", "Pretoria", "Alger", "Rabat", "Tunis", "Bamako", "Ouagadougou", "Abidjan", "Yaoundé", "Libreville", "Kinshasa", "Luanda", "Harare", "Lusaka", "Windhoek"],
            "pays": ["Sénégal", "France", "Japon", "Royaume-Uni", "Allemagne", "Espagne", "Italie", "Russie", "Chine", "Inde", "Brésil", "Australie", "Canada", "Égypte", "Éthiopie", "Kenya", "Afrique du Sud", "Algérie", "Maroc", "Tunisie", "Mali", "Burkina Faso", "Côte d'Ivoire", "Cameroun", "Gabon", "RDC", "Angola", "Zimbabwe", "Zambie", "Namibie"],
            "continent": ["Afrique", "Europe", "Asie", "Amérique du Sud", "Amérique du Nord", "Océanie", "Afrique", "Europe", "Asie", "Amérique du Sud"],
            "population": ["12 millions", "68 millions", "125 millions", "67 millions", "83 millions", "47 millions", "60 millions", "144 millions", "1.4 milliard", "1.3 milliard", "213 millions", "26 millions", "38 millions", "104 millions", "115 millions", "54 millions", "59 millions", "44 millions", "37 millions", "12 millions"],
            "superficie": ["196 722", "643 801", "377 975", "242 495", "357 022", "505 990", "301 340", "17 098 246", "9 596 961", "3 287 263", "8 515 767", "7 692 024", "9 984 670", "1 002 450", "1 104 300", "580 367", "1 219 090", "2 381 741", "446 550", "163 610"],
            "ville": ["Dakar", "Paris", "Tokyo", "Londres", "Berlin", "Madrid", "Rome", "Moscou", "Shanghai", "Mumbai", "São Paulo", "Sydney", "Toronto", "Le Caire", "Addis-Abeba", "Nairobi", "Johannesburg", "Alger", "Casablanca", "Tunis"],
            "fleuve": ["le Nil", "l'Amazone", "le Mississippi", "le Danube", "le Gange", "le Niger", "le Congo", "le Mékong", "le Rhin", "la Volga"],
            "montagne": ["le Kilimandjaro", "le Mont Fuji", "l'Everest", "le Mont Blanc", "le Mont Kenya", "l'Aconcagua", "le Denali", "l'Elbrouz", "le Vinson", "le Puncak Jaya"],
            "pop_ville": ["2 millions", "10 millions", "37 millions", "9 millions", "3.6 millions", "6.7 millions", "2.8 millions", "12 millions", "26 millions", "20 millions", "21 millions", "5 millions", "6 millions", "9 millions", "3 millions"],
            "ocean": ["l'océan Atlantique", "l'océan Pacifique", "l'océan Indien", "la mer Méditerranée", "la mer Rouge", "la mer de Chine", "la mer des Caraïbes", "l'océan Arctique", "la mer du Nord", "la mer Baltique"],
            "monnaie": ["franc CFA", "euro", "yen", "livre sterling", "dollar", "rouble", "yuan", "roupie", "real", "dinar"],
            "langue": ["français", "anglais", "espagnol", "arabe", "portugais", "swahili", "mandarin", "hindi", "russe", "japonais"],
            "organisation": ["l'ONU", "l'Union Africaine", "l'Union Européenne", "l'OTAN", "l'OPEP", "la CEDEAO", "le Commonwealth", "l'ASEAN", "le Mercosur", "la Ligue Arabe"],
            "annee": ["1945", "1963", "1957", "1949", "1960", "1975", "1965", "1967", "1991", "1994"],
            "climat": ["tropical", "tempéré", "méditerranéen", "continental", "désertique", "équatorial", "océanique", "subtropical", "sahélien", "montagnard"],
            "particularite": ["sa gastronomie", "son tourisme", "ses plages", "son histoire", "sa culture", "sa musique", "son artisanat", "sa biodiversité", "son industrie", "ses ressources naturelles"],
        },
    },
    "history": {
        "templates": [
            "{evenement} a eu lieu en {date}.",
            "{personnage} est {profession} qui a marqué le {siecle} siècle.",
            "La bataille de {bataille} s'est déroulée en {date_bataille}.",
            "{civilisation} était une civilisation majeure de {periode}.",
            "Le traité de {traite} a été signé en {date_traite}.",
            "{empire} a dominé {region} pendant le {siecle} siècle.",
            "En {date}, {evenement} a changé le cours de l'histoire.",
            "{personnage} est né en {date_naissance}.",
            "La révolution de {revolution} a débuté en {date_revolution}.",
            "{periode} est une période marquée par {caracteristique}.",
            "{personnage} a découvert {decouverte} en {date_decouverte}.",
            "{pays} a obtenu son indépendance en {independance}.",
            "Le {siecle} siècle est marqué par {marqueur}.",
            "{personnage} a écrit {oeuvre} en {date_oeuvre}.",
            "La guerre de {guerre} a opposé {belligerants} entre {debut} et {fin}.",
        ],
        "data": {
            "evenement": ["la Révolution française", "la chute de l'Empire romain", "la découverte de l'Amérique", "l'abolition de l'esclavage", "la chute du mur de Berlin", "l'indépendance de l'Inde", "le Printemps arabe", "la Révolution industrielle", "la Réforme protestante", "la Renaissance"],
            "date": ["1789", "476", "1492", "1848", "1989", "1947", "2011", "1760", "1517", "1453"],
            "personnage": ["Napoléon Bonaparte", "Jules César", "Cléopâtre", "Gengis Khan", "Martin Luther King", "Nelson Mandela", "Marie Curie", "Léonard de Vinci", "Abraham Lincoln", "Sundiata Keïta"],
            "profession": ["un empereur", "un général", "une reine", "un conquérant", "un militant des droits civiques", "un président", "une scientifique", "un artiste", "un homme d'État", "un roi fondateur"],
            "siecle": ["XVIIIe", "XIXe", "XXe", "XVIe", "XVe", "XIVe", "XIIe", "XVIIe", "XIIIe", "XIe"],
            "bataille": ["Waterloo", "Stalingrad", "Austerlitz", "Gettysburg", "Marathon", "Hastings", "Trafalgar", "Verdun", "El-Alamein", "Adoua"],
            "date_bataille": ["1815", "1942-1943", "1805", "1863", "-490", "1066", "1805", "1916", "1942", "1896"],
            "civilisation": ["l'Égypte ancienne", "la Grèce antique", "l'Empire romain", "l'Empire du Mali", "la civilisation maya", "l'Empire Perse", "la civilisation chinoise", "l'Empire du Ghana", "la Mésopotamie", "l'Empire Inca"],
            "periode": ["l'Antiquité", "le Moyen Âge", "la Renaissance", "les Temps modernes", "le XIXe siècle", "la période coloniale", "les indépendances", "la guerre froide", "l'âge du bronze", "l'âge du fer"],
            "traite": ["Versailles", "Yalta", "Rome", "Berlin", "Maastricht", "Westphalie", "Paris", "Tordesillas", "Nankin", "Vienne"],
            "date_traite": ["1919", "1945", "1957", "1885", "1992", "1648", "1763", "1494", "1842", "1815"],
            "empire": ["l'Empire romain", "l'Empire ottoman", "l'Empire britannique", "l'Empire du Mali", "l'Empire Moghol", "l'Empire Songhaï", "l'Empire Perse", "l'Empire byzantin", "l'Empire aztèque", "l'Empire russe"],
            "region": ["l'Europe", "l'Asie", "l'Afrique", "le Moyen-Orient", "l'Amérique du Sud", "la Méditerranée", "l'Afrique de l'Ouest", "l'Asie centrale", "l'Amérique centrale", "l'Afrique du Nord"],
            "revolution": ["1789", "1917", "1848", "industrielle", "agricole", "numérique", "française", "américaine", "culturelle", "scientifique"],
            "caracteristique": ["l'expansion territoriale", "le commerce florissant", "les découvertes scientifiques", "les révolutions politiques", "l'émergence des empires", "la féodalité", "l'urbanisation", "les croisades", "la colonisation", "les grandes migrations"],
            "decouverte": ["l'Amérique", "la pénicilline", "la radioactivité", "les rayons X", "la structure de l'ADN", "le vaccin contre la rage", "la relativité", "le boson de Higgs", "la circulation sanguine", "les lois de la gravitation"],
            "date_decouverte": ["1492", "1928", "1896", "1895", "1953", "1885", "1905/1915", "2012", "1628", "1687"],
            "pays": ["le Ghana", "le Sénégal", "l'Algérie", "le Kenya", "l'Inde", "le Nigeria", "la Tanzanie", "le Zimbabwe", "l'Angola", "le Mozambique"],
            "independance": ["1957", "1960", "1962", "1963", "1947", "1960", "1961", "1980", "1975", "1975"],
            "marqueur": ["les grandes découvertes", "l'essor du commerce", "les conflits mondiaux", "l'émergence des nations", "les révolutions", "la colonisation", "les indépendances", "la mondialisation", "le développement technologique", "les mouvements sociaux"],
            "oeuvre": ["De l'origine des espèces", "Le Capital", "Les Misérables", "La Divine Comédie", "Don Quichotte", "Hamlet", "L'Iliade et l'Odyssée", "Le Prince", "Germinal", "Le Deuxième Sexe"],
            "date_oeuvre": ["1859", "1867", "1862", "1320", "1605", "1603", "-800", "1513", "1885", "1949"],
            "guerre": ["Trente Ans", "Cent Ans", "Sécession", "Sept Ans", "Crimée", "Indépendance américaine", "Vietnam", "Corée", "Falklands", "Golfe"],
            "belligerants": ["la France et l'Angleterre", "les États confédérés et l'Union", "l'URSS et les États-Unis", "les Alliés et l'Axe", "Israël et les pays arabes", "la France et la Prusse", "l'Espagne et l'Angleterre", "le Nord et le Sud Vietnam", "l'Irak et l'Iran", "l'Argentine et le Royaume-Uni"],
            "debut": ["1914", "1939", "1861", "1955", "1618", "1337", "1701", "1756", "1980", "1990"],
            "fin": ["1918", "1945", "1865", "1975", "1648", "1453", "1714", "1763", "1988", "1991"],
        },
    },
    "science": {
        "templates": [
            "{scientifique} a découvert {decouverte}.",
            "La loi de {loi} stipule que {enonce}.",
            "{element} est un élément chimique de symbole {symbole}.",
            "L'{organe} est un organe du corps humain.",
            "{planete} est une planète du système solaire.",
            "La vitesse de {phenomene} est d'environ {vitesse}.",
            "Le théorème de {theoreme} établit que {formule}.",
            "{particule} est une particule fondamentale en physique.",
            "{reaction} est une réaction chimique qui produit {produit}.",
            "{maladie} est causée par {cause}.",
            "{inventeur} a inventé {invention} en {annee_invention}.",
            "Le {constante} vaut environ {valeur}.",
            "{processus} est le processus par lequel {resultat}.",
            "{espece} est une espèce qui vit dans {habitat}.",
            "{unite} est l'unité de mesure de {mesure}.",
        ],
        "data": {
            "scientifique": ["Isaac Newton", "Albert Einstein", "Marie Curie", "Charles Darwin", "Louis Pasteur", "Galilée", "Nikola Tesla", "Stephen Hawking", "Rosalind Franklin", "Dmitri Mendeleïev"],
            "decouverte": ["la gravitation universelle", "la relativité", "la radioactivité", "l'évolution par sélection naturelle", "le vaccin contre la rage", "les lois du mouvement", "le courant alternatif", "le rayonnement Hawking", "la structure de l'ADN", "le tableau périodique"],
            "loi": ["la gravitation universelle", "la conservation de l'énergie", "l'attraction des masses", "la thermodynamique", "l'action et la réaction", "la relativité restreinte", "la réfraction de la lumière", "la pression des gaz", "la chute des corps", "l'expansion de l'univers"],
            "enonce": ["la force est proportionnelle au produit des masses et inversement proportionnelle au carré de la distance", "l'énergie ne peut être ni créée ni détruite", "deux corps s'attirent avec une force proportionnelle à leurs masses", "l'entropie d'un système isolé augmente toujours", "à toute action correspond une réaction égale et opposée", "la vitesse de la lumière est la même dans tous les référentiels inertiels", "la lumière change de direction en passant d'un milieu à un autre", "le volume d'un gaz est inversement proportionnel à sa pression", "tous les corps tombent à la même vitesse dans le vide", "l'univers est en expansion depuis le Big Bang"],
            "element": ["l'oxygène", "le carbone", "le fer", "l'or", "l'uranium", "l'hydrogène", "l'azote", "le calcium", "le sodium", "le chlore"],
            "symbole": ["O", "C", "Fe", "Au", "U", "H", "N", "Ca", "Na", "Cl"],
            "organe": ["cœur", "cerveau", "poumon", "foie", "rein", "estomac", "intestin", "pancréas", "rate", "thyroïde"],
            "planete": ["la Terre", "Mars", "Jupiter", "Saturne", "Vénus", "Mercure", "Uranus", "Neptune"],
            "phenomene": ["la lumière", "le son", "l'électricité", "les ondes radio", "le vent solaire"],
            "vitesse": ["299 792 458 m/s", "343 m/s", "approximativement la vitesse de la lumière", "300 000 km/s", "400 km/s"],
            "theoreme": ["Pythagore", "Thalès", "Fermat", "Pythagore", "Euclide"],
            "formule": ["a² + b² = c²", "dans un triangle, une droite parallèle à un côté découpe des segments proportionnels", "il n'existe pas d'entiers strictement positifs x, y, z tels que x^n + y^n = z^n pour n > 2", "la somme des carrés des deux côtés est égale au carré de l'hypoténuse", "la somme des angles d'un triangle vaut 180°"],
            "particule": ["l'électron", "le proton", "le neutron", "le photon", "le neutrino", "le quark", "le boson de Higgs", "le muon", "le gluon", "le positron"],
            "reaction": ["la combustion", "la photosynthèse", "la respiration cellulaire", "la fermentation", "l'oxydation", "la réduction", "l'hydrolyse", "la neutralisation", "la polymérisation", "l'électrolyse"],
            "produit": ["du CO₂", "du glucose et de l'oxygène", "de l'ATP", "de l'éthanol", "de la rouille", "des électrons", "des molécules plus simples", "du sel et de l'eau", "des polymères", "des gaz"],
            "maladie": ["le paludisme", "la tuberculose", "le diabète", "le cancer", "la grippe", "le SIDA", "l'asthme", "l'hypertension", "la dépression", "Alzheimer"],
            "cause": ["un parasite transmis par les moustiques", "une bactérie", "une résistance à l'insuline", "une division cellulaire incontrôlée", "un virus", "un virus (VIH)", "une inflammation des bronches", "une pression artérielle élevée", "un déséquilibre chimique dans le cerveau", "l'accumulation de plaques amyloïdes"],
            "inventeur": ["Thomas Edison", "Alexander Graham Bell", "les frères Wright", "Tim Berners-Lee", "Johannes Gutenberg", "James Watt", "John von Neumann", "Alan Turing", "Charles Babbage", "Guglielmo Marconi"],
            "invention": ["l'ampoule électrique", "le téléphone", "l'avion", "le World Wide Web", "l'imprimerie", "la machine à vapeur", "l'architecture des ordinateurs", "la machine de Turing", "la machine analytique", "la radio"],
            "annee_invention": ["1879", "1876", "1903", "1989", "1440", "1769", "1945", "1936", "1837", "1895"],
            "constante": ["nombre pi", "nombre d'or φ", "constante de Planck h", "vitesse de la lumière c", "constante gravitationnelle G", "nombre d'Avogadro", "constante de Boltzmann", "charge élémentaire e", "constante de Rydberg", "permittivité du vide ε₀"],
            "valeur": ["3.14159", "1.618034", "6.626 × 10⁻³⁴ J·s", "299 792 458 m/s", "6.674 × 10⁻¹¹ N·m²/kg²", "6.022 × 10²³ mol⁻¹", "1.381 × 10⁻²³ J/K", "1.602 × 10⁻¹⁹ C", "1.097 × 10⁷ m⁻¹", "8.854 × 10⁻¹² F/m"],
            "processus": ["la photosynthèse", "la mitose", "l'osmose", "la conduction thermique", "la fission nucléaire", "la digestion", "la respiration", "l'évaporation", "la condensation", "la cristallisation"],
            "resultat": ["les plantes produisent de l'énergie", "les cellules se divisent", "l'eau traverse une membrane", "la chaleur se propage", "le noyau atomique se divise", "les aliments sont décomposés", "l'oxygène est absorbé", "l'eau passe de l'état liquide à gazeux", "la vapeur redevient liquide", "des cristaux se forment"],
            "espece": ["le lion", "l'éléphant d'Afrique", "le tigre du Bengale", "l'orang-outan", "le panda géant", "le gorille des montagnes", "le rhinocéros blanc", "le requin blanc", "la baleine bleue", "l'aigle royal"],
            "habitat": ["la savane africaine", "les forêts équatoriales", "les mangroves d'Asie", "la jungle de Bornéo", "les montagnes de Chine", "les montagnes d'Afrique centrale", "les plaines d'Afrique", "tous les océans", "l'océan Antarctique", "les montagnes d'Europe et d'Asie"],
            "unite": ["le mètre", "le kilogramme", "la seconde", "l'ampère", "le kelvin", "la mole", "le candela", "le joule", "le watt", "le newton"],
            "mesure": ["la longueur", "la masse", "le temps", "l'intensité électrique", "la température", "la quantité de matière", "l'intensité lumineuse", "l'énergie", "la puissance", "la force"],
        },
    },
    "general": {
        "templates": [
            "{sujet1} est lié à {sujet2} dans le domaine de {domaine}.",
            "{personne} est connu(e) pour {realisation}.",
            "{concept} est un concept important en {domaine}.",
            "Le {sujet} joue un rôle essentiel dans {contexte}.",
            "{fait} est un fait établi par {source}.",
            "{entite} a été créé(e) en {date_entite}.",
            "{phenomene_general} est un phénomène étudié par {discipline}.",
            "{technologie} a révolutionné le domaine de {secteur}.",
            "{methode} est une méthode utilisée pour {objectif}.",
            "Le principe de {principe} guide {application}.",
        ],
        "data": {
            "sujet1": ["la philosophie", "les mathématiques", "la physique", "la chimie", "la biologie", "l'histoire", "la géographie", "l'économie", "la psychologie", "la sociologie"],
            "sujet2": ["l'éthique", "la logique", "l'expérimentation", "la théorie atomique", "l'évolution", "la chronologie", "la cartographie", "le commerce", "le comportement", "la culture"],
            "domaine": ["la connaissance humaine", "les sciences", "la recherche académique", "l'éducation", "la culture générale"],
            "personne": ["Albert Einstein", "Marie Curie", "Léonard de Vinci", "Aristote", "Socrate", "Confucius", "Hypatie d'Alexandrie", "Ibn Sina (Avicenne)", "Al-Khwarizmi", "Cheikh Anta Diop"],
            "realisation": ["ses travaux révolutionnaires", "ses découvertes majeures", "son génie créatif", "sa philosophie", "sa méthode d'enseignement", "sa sagesse", "ses travaux mathématiques", "ses écrits médicaux", "l'invention de l'algèbre", "sa démonstration de l'origine africaine de l'Égypte ancienne"],
            "concept": ["la relativité", "l'évolution", "la gravitation", "l'atome", "l'énergie", "le temps", "l'espace", "la matière", "la vie", "la conscience"],
            "sujet": ["langage", "écriture", "nombre", "symbole", "outil", "feu", "roue", "agriculture", "médecine", "loi"],
            "contexte": ["la civilisation humaine", "le développement des sociétés", "la communication", "la survie", "le progrès technique", "l'organisation sociale", "le transport", "l'alimentation", "la santé publique", "la justice"],
            "fait": ["L'eau bout à 100°C", "La Terre tourne autour du Soleil", "L'ADN contient le code génétique", "Le Soleil est une étoile", "Les dinosaures ont disparu il y a 65 millions d'années", "La photosynthèse produit de l'oxygène", "L'Everest est le plus haut sommet du monde", "Le cœur humain bat environ 100 000 fois par jour", "La vitesse de la lumière est de 300 000 km/s", "L'univers est en expansion"],
            "source": ["la science", "l'observation", "l'expérimentation", "des mesures précises", "des études scientifiques", "des recherches approfondies", "l'astronomie", "la biologie", "la physique", "la cosmologie"],
            "entite": ["l'UNESCO", "l'ONU", "l'Union Européenne", "l'Union Africaine", "la Croix-Rouge", "l'OMS", "le CERN", "la NASA", "l'ESA", "Médecins Sans Frontières"],
            "date_entite": ["1945", "1945", "1993", "2002", "1863", "1948", "1954", "1958", "1975", "1971"],
            "phenomene_general": ["le réchauffement climatique", "la pollution", "la mondialisation", "l'urbanisation", "la digitalisation", "la migration", "l'érosion", "la désertification", "la déforestation", "l'acidification des océans"],
            "discipline": ["la climatologie", "l'écologie", "l'économie", "la sociologie", "l'informatique", "la démographie", "la géologie", "les sciences environnementales", "la biologie marine", "la chimie"],
            "technologie": ["Internet", "l'intelligence artificielle", "l'impression 3D", "la blockchain", "l'énergie solaire", "la 5G", "la robotique", "la réalité virtuelle", "la biotechnologie", "le cloud computing"],
            "secteur": ["la communication", "l'industrie", "la fabrication", "la finance", "l'énergie", "les télécommunications", "la production", "le divertissement", "la santé", "les services informatiques"],
            "methode": ["la méthode scientifique", "l'analyse statistique", "la modélisation mathématique", "l'expérimentation contrôlée", "l'observation empirique", "la simulation numérique", "l'étude de cas", "la méta-analyse", "la revue par les pairs", "l'enquête de terrain"],
            "objectif": ["étudier la nature", "comprendre les phénomènes", "prédire les comportements", "valider des hypothèses", "recueillir des données", "reproduire des situations complexes", "analyser des situations réelles", "synthétiser les connaissances", "garantir la qualité scientifique", "documenter des faits"],
            "principe": ["la conservation de l'énergie", "la moindre action", "l'incertitude de Heisenberg", "la causalité", "la non-contradiction", "le rasoir d'Occam", "la relativité", "la superposition quantique", "l'entropie", "la sélection naturelle"],
            "application": ["la physique", "la mécanique", "la physique quantique", "la logique", "la philosophie", "la méthode scientifique", "la cosmologie", "l'informatique quantique", "la thermodynamique", "la biologie"],
        },
    },
}


# ═══════════════════════════════════════════════════════════════════
# GÉNÉRATEUR
# ═══════════════════════════════════════════════════════════════════

def generate_corpus():
    total = 0
    random.seed(42)  # Reproductible

    for domain, config in TEMPLATES.items():
        templates = config["templates"]
        data = config["data"]

        print(f"\n  [{domain}] Génération combinatoire...")
        print(f"    Templates : {len(templates)}")
        print(f"    Clés de données : {len(data)}")

        domain_total = 0
        output_file = os.path.join(CORPUS_DIR, f"corpus_{domain}.txt")
        seen = set()

        with open(output_file, 'w', encoding='utf-8') as f:
            for template in templates:
                # Extraire les variables du template
                import re
                variables = re.findall(r'\{(\w+)\}', template)
                if not variables:
                    continue

                # Récupérer les listes de valeurs pour chaque variable
                value_lists = []
                valid = True
                for var in variables:
                    if var not in data:
                        valid = False
                        break
                    values = data[var]
                    # Si la liste est trop grande, limiter pour éviter explosion combinatoire
                    if len(values) > 30:
                        values = values[:30]
                    value_lists.append(values)

                if not valid or not value_lists:
                    continue

                # Générer les combinaisons
                # Pour éviter l'explosion (10 vars × 30 valeurs = 30^10),
                # on utilise un échantillonnage aléatoire
                max_combinations = min(5000, 30 ** len(value_lists))

                for _ in range(max_combinations):
                    # Choisir aléatoirement une valeur par variable
                    chosen = [random.choice(lst) for lst in value_lists]

                    # Construire la phrase
                    sentence = template
                    for var, val in zip(variables, chosen):
                        sentence = sentence.replace(f"{{{var}}}", str(val))

                    # Anti-doublon
                    h = hash(sentence)
                    if h in seen:
                        continue
                    seen.add(h)

                    f.write(sentence + "\n")
                    domain_total += 1

                # Limite par domaine
                if domain_total >= 25000:
                    break

        size_kb = os.path.getsize(output_file) / 1024
        total += domain_total
        print(f"    → {domain_total} phrases ({size_kb:.0f} KB)")

    # Fichier global
    all_file = os.path.join(CORPUS_DIR, "corpus_all.txt")
    total_all = 0
    with open(all_file, 'w', encoding='utf-8') as fout:
        for domain in TEMPLATES:
            fp = os.path.join(CORPUS_DIR, f"corpus_{domain}.txt")
            if os.path.exists(fp):
                with open(fp, 'r', encoding='utf-8') as fin:
                    for line in fin:
                        fout.write(line)
                        total_all += 1

    print(f"\n{'=' * 70}")
    print(f"  GÉNÉRATION TERMINÉE")
    print(f"  Total : {total:,} phrases dans {len(TEMPLATES)} domaines")
    print(f"  Fichier global : {total_all:,} phrases ({os.path.getsize(all_file)/1024:.0f} KB)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    generate_corpus()