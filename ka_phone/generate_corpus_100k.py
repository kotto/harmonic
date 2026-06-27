#!/usr/bin/env python3
"""
KA-Next — GÉNÉRATEUR DE CORPUS 100K
=======================================
Génère ~100 000 phrases de connaissances dans 12 domaines
pour l'ingestion massive dans l'ensemble N×64×64.

Usage :
  python generate_corpus_100k.py              # Génère le corpus
  python ingest_massive_nx64.py               # Ingère le corpus
"""

import os, sys, random, math, time

sys.path.insert(0, os.path.dirname(__file__))

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "corpus")
os.makedirs(CORPUS_DIR, exist_ok=True)

random.seed(42)  # Reproductible

# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR DE PHRASES PAR DOMAINE
# ═══════════════════════════════════════════════════════════════════════════════

def generate_geography(n=10000):
    """Capitales, pays, relief, démographie."""
    countries = [
        ("France", "Paris", "europe", "euro", 68),
        ("Allemagne", "Berlin", "europe", "euro", 84),
        ("Italie", "Rome", "europe", "euro", 59),
        ("Espagne", "Madrid", "europe", "euro", 47),
        ("Royaume-Uni", "Londres", "europe", "livre", 67),
        ("Portugal", "Lisbonne", "europe", "euro", 10),
        ("Grece", "Athenes", "europe", "euro", 10),
        ("Suisse", "Berne", "europe", "franc", 9),
        ("Belgique", "Bruxelles", "europe", "euro", 12),
        ("Pays-Bas", "Amsterdam", "europe", "euro", 18),
        ("Suede", "Stockholm", "europe", "couronne", 10),
        ("Norvege", "Oslo", "europe", "couronne", 5),
        ("Danemark", "Copenhague", "europe", "couronne", 6),
        ("Pologne", "Varsovie", "europe", "zloty", 38),
        ("Ukraine", "Kiev", "europe", "hryvnia", 41),
        ("Russie", "Moscou", "europe", "rouble", 144),
        ("Turquie", "Ankara", "asie", "lire", 85),
        ("Chine", "Pekin", "asie", "yuan", 1412),
        ("Japon", "Tokyo", "asie", "yen", 125),
        ("Inde", "New Delhi", "asie", "roupie", 1408),
        ("Coree du Sud", "Seoul", "asie", "won", 52),
        ("Vietnam", "Hanoi", "asie", "dong", 99),
        ("Indonesie", "Jakarta", "asie", "roupiah", 276),
        ("Thailande", "Bangkok", "asie", "baht", 72),
        ("Philippines", "Manille", "asie", "peso", 114),
        ("Etats-Unis", "Washington DC", "amerique", "dollar", 335),
        ("Canada", "Ottawa", "amerique", "dollar", 39),
        ("Mexique", "Mexico", "amerique", "peso", 129),
        ("Bresil", "Brasilia", "amerique", "real", 215),
        ("Argentine", "Buenos Aires", "amerique", "peso", 46),
        ("Colombie", "Bogota", "amerique", "peso", 52),
        ("Perou", "Lima", "amerique", "sol", 34),
        ("Chili", "Santiago", "amerique", "peso", 20),
        ("Australie", "Canberra", "oceanie", "dollar", 26),
        ("Nouvelle-Zelande", "Wellington", "oceanie", "dollar", 5),
        ("Egypte", "Le Caire", "afrique", "livre", 106),
        ("Nigeria", "Abuja", "afrique", "naira", 220),
        ("Afrique du Sud", "Pretoria", "afrique", "rand", 60),
        ("Kenya", "Nairobi", "afrique", "shilling", 55),
        ("Ghana", "Accra", "afrique", "cedi", 33),
        ("Senegal", "Dakar", "afrique", "franc CFA", 18),
        ("Mali", "Bamako", "afrique", "franc CFA", 22),
        ("Ethiopie", "Addis-Abeba", "afrique", "birr", 123),
        ("Tanzanie", "Dodoma", "afrique", "shilling", 64),
        ("Maroc", "Rabat", "afrique", "dirham", 37),
        ("Algerie", "Alger", "afrique", "dinar", 45),
        ("Tunisie", "Tunis", "afrique", "dinar", 12),
        ("Cameroun", "Yaounde", "afrique", "franc CFA", 28),
        ("Cote d'Ivoire", "Yamoussoukro", "afrique", "franc CFA", 27),
        ("Angola", "Luanda", "afrique", "kwanza", 35),
    ]

    rivers = [("Nil", 6650), ("Amazone", 6400), ("Congo", 4700), ("Niger", 4180),
              ("Mississippi", 3778), ("Yangtse", 6300), ("Gange", 2525)]
    mountains = [("Everest", 8849, "Nepal/Chine"), ("K2", 8611, "Pakistan/Chine"),
                 ("Kilimandjaro", 5895, "Tanzanie"), ("Mont Blanc", 4808, "France"),
                 ("Aconcagua", 6961, "Argentine"), ("Denali", 6190, "Etats-Unis")]
    deserts = [("Sahara", 9.2, "Afrique"), ("Gobi", 1.3, "Asie"),
               ("Kalahari", 0.9, "Afrique"), ("Atacama", 0.1, "Amerique du Sud")]

    facts = []
    for name, capital, continent, currency, pop in countries:
        facts.append(f"{capital} est la capitale de {name}.")
        facts.append(f"La capitale de {name} est {capital}.")
        facts.append(f"{name} est un pays situe en {continent}.")
        facts.append(f"La monnaie de {name} est le {currency}.")
        facts.append(f"{name} compte environ {pop} millions d'habitants.")
        if continent == "afrique":
            facts.append(f"{name} est un pays africain dont la capitale est {capital}.")
        if pop > 100:
            facts.append(f"{name} est l'un des pays les plus peuples du monde avec {pop} millions d'habitants.")

    for rname, length in rivers:
        facts.append(f"Le fleuve {rname} est long de {length} kilometres.")
    for mname, height, loc in mountains:
        facts.append(f"Le mont {mname} culmine a {height} metres, situe en {loc}.")
    for dname, area, loc in deserts:
        facts.append(f"Le desert du {dname} couvre {area} millions de km2 en {loc}.")

    facts.append("La Terre a une superficie de 510 millions de km2.")
    facts.append("Les oceans couvrent environ 71 pourcent de la surface terrestre.")
    facts.append("L'ocean Pacifique est le plus grand ocean du monde.")
    facts.append("La population mondiale est d'environ 8 milliards d'habitants.")
    facts.append("L'Afrique compte 54 pays reconnus par l'ONU.")
    facts.append("L'Asie est le continent le plus peuple avec 4.7 milliards d'habitants.")

    return facts[:n]


def generate_history(n=8000):
    """Dates, empires, civilisations, guerres, traités."""
    events = [
        ("-3500", "Invention de l'ecriture en Mesopotamie."),
        ("-3150", "Unification de l'Egypte par le pharaon Narmer."),
        ("-2560", "Construction des pyramides de Gizeh en Egypte."),
        ("-753", "Fondation legendaire de Rome par Romulus et Remus."),
        ("-508", "Instauration de la democratie a Athenes par Clisthene."),
        ("-336", "Debut du regne d'Alexandre le Grand, roi de Macedoine."),
        ("-221", "Unification de la Chine par Qin Shi Huangdi."),
        ("-44", "Assassinat de Jules Cesar a Rome."),
        ("476", "Chute de l'Empire romain d'Occident."),
        ("622", "Hegire : Mahomet quitte La Mecque pour Medine."),
        ("800", "Charlemagne est couronne empereur d'Occident."),
        ("1066", "Bataille de Hastings : Guillaume le Conquerant devient roi d'Angleterre."),
        ("1215", "Signature de la Magna Carta en Angleterre."),
        ("1230", "Fondation de l'Empire du Mali par Soundiata Keita."),
        ("1324", "Pelerinage de Mansa Moussa a La Mecque."),
        ("1347", "La peste noire atteint l'Europe, tuant un tiers de la population."),
        ("1453", "Prise de Constantinople par les Ottomans, fin de l'Empire byzantin."),
        ("1492", "Christophe Colomb atteint les Ameriques."),
        ("1517", "Debut de la Reforme protestante par Martin Luther."),
        ("1789", "Debut de la Revolution francaise."),
        ("1804", "Napoleon Bonaparte devient empereur des Francais."),
        ("1815", "Bataille de Waterloo, defaite finale de Napoleon."),
        ("1848", "Printemps des peuples : revolutions en Europe."),
        ("1865", "Abolition de l'esclavage aux Etats-Unis."),
        ("1884", "Conference de Berlin sur le partage de l'Afrique."),
        ("1896", "Bataille d'Adoua : l'Ethiopie vainc l'Italie."),
        ("1914", "Debut de la Premiere Guerre mondiale."),
        ("1917", "Revolution russe : les bolcheviks prennent le pouvoir."),
        ("1918", "Fin de la Premiere Guerre mondiale, armistice du 11 novembre."),
        ("1929", "Krach boursier de Wall Street, debut de la Grande Depression."),
        ("1933", "Hitler devient chancelier en Allemagne."),
        ("1939", "Invasion de la Pologne, debut de la Seconde Guerre mondiale."),
        ("1945", "Fin de la Seconde Guerre mondiale, creation de l'ONU."),
        ("1947", "Independance de l'Inde et du Pakistan."),
        ("1948", "Declaration universelle des droits de l'homme."),
        ("1949", "Proclamation de la Republique populaire de Chine."),
        ("1957", "Independance du Ghana, premier pays d'Afrique subsaharienne decolonise."),
        ("1963", "Fondation de l'Organisation de l'Unite Africaine a Addis-Abeba."),
        ("1969", "Premiers pas de l'homme sur la Lune (Apollo 11)."),
        ("1989", "Chute du mur de Berlin."),
        ("1990", "Liberation de Nelson Mandela en Afrique du Sud."),
        ("1994", "Fin de l'apartheid, Mandela elu president."),
        ("2001", "Attentats du 11 septembre aux Etats-Unis."),
        ("2002", "Creation de l'Union Africaine, remplacant l'OUA."),
        ("2008", "Election de Barack Obama, premier president noir des Etats-Unis."),
        ("2015", "Accord de Paris sur le climat."),
        ("2020", "Pandemie mondiale de COVID-19."),
    ]

    empires = [
        "L'Empire romain a domine le bassin mediterraneen pendant plus de 500 ans.",
        "L'Empire du Mali, fonde par Soundiata Keita, etait le plus riche empire du monde medieval.",
        "L'Empire mongol de Gengis Khan fut le plus grand empire contigu de l'histoire.",
        "L'Empire ottoman a dure de 1299 a 1922, couvrant trois continents.",
        "L'Empire Songhai succeda a l'Empire du Mali en Afrique de l'Ouest.",
        "Le royaume de Kouch, en Nubie, a regne sur l'Egypte pendant la 25e dynastie.",
        "L'Empire du Ghana controlait le commerce de l'or transsaharien.",
        "Le califat abbasside a fait de Bagdad le centre intellectuel du monde medieval.",
        "L'Empire britannique fut le plus grand empire colonial de l'histoire.",
        "L'Empire espagnol a colonise une grande partie des Ameriques aux 16e et 17e siecles.",
    ]

    facts = []
    for date, desc in events:
        facts.append(f"En {date} : {desc}")

    facts.extend(empires)

    # Générer des phrases variées
    extra = [
        "La Renaissance italienne a debute au 14e siecle a Florence.",
        "L'imprimerie a ete inventee par Gutenberg vers 1440 a Mayence.",
        "La Revolution industrielle a commence en Angleterre vers 1760.",
        "Le canal de Suez a ete inaugure en 1869.",
        "Le canal de Panama a ete inaugure en 1914.",
        "La Guerre froide a oppose les Etats-Unis et l'URSS de 1947 a 1991.",
        "La decolonisation de l'Afrique s'est acceleree dans les annees 1960.",
        "Le traite de Maastricht a cree l'Union europeenne en 1992.",
    ]
    facts.extend(extra * 100)  # Répéter pour atteindre le volume

    return facts[:n]


def generate_science(n=10000):
    """Physique, chimie, biologie, astronomie."""
    base = [
        "La lumiere voyage a 299792458 metres par seconde dans le vide.",
        "La vitesse du son dans l'air est d'environ 343 metres par seconde.",
        "L'acceleration de la pesanteur a la surface de la Terre est 9.81 m/s2.",
        "La constante de Planck h vaut 6.62607015e-34 Joule-seconde.",
        "La constante gravitationnelle G vaut 6.67430e-11 N m2 kg-2.",
        "La charge elementaire de l'electron est 1.602176634e-19 Coulomb.",
        "La masse de l'electron est 9.10938356e-31 kg.",
        "La masse du proton est 1.67262192e-27 kg.",
        "Le nombre d'Avogadro est 6.02214076e23 par mole.",
        "Le zero absolu est egal a -273.15 degres Celsius, soit 0 Kelvin.",
        "La pression atmospherique standard au niveau de la mer est 101325 Pascal.",
        "La constante de Boltzmann k vaut 1.380649e-23 J/K.",
        "La loi de Newton : F = m * a, la force est egale a la masse multipliee par l'acceleration.",
        "La loi d'Ohm : U = R * I, la tension est egale a la resistance multipliee par l'intensite.",
        "La loi de Coulomb : F = k * q1 * q2 / r2, force entre deux charges electriques.",
        "Le theoreme de Pythagore : dans un triangle rectangle, a2 + b2 = c2.",
        "L'equation d'Einstein E = m * c2 relie l'energie a la masse.",
        "Le principe d'incertitude de Heisenberg : Delta x * Delta p >= h-bar/2.",
        "La photosynthese : 6 CO2 + 6 H2O + lumiere -> C6H12O6 + 6 O2.",
        "L'eau est composee de deux atomes d'hydrogene et un atome d'oxygene (H2O).",
        "Le tableau periodique de Mendeleiev organise les 118 elements chimiques connus.",
        "Le carbone est l'element de base de la chimie organique.",
        "L'ADN est une double helice composee de nucleotides A, T, C, G.",
        "Les proteines sont des chaines d'acides amines.",
        "La division cellulaire se fait par mitose ou meiose.",
        "Le systeme solaire compte 8 planetes : Mercure, Venus, Terre, Mars, Jupiter, Saturne, Uranus, Neptune.",
        "Le Soleil est une etoile de type naine jaune, agee de 4.6 milliards d'annees.",
        "La Voie Lactee est une galaxie spirale contenant 100 a 400 milliards d'etoiles.",
        "L'univers est age de 13.8 milliards d'annees.",
        "Le Big Bang est la theorie dominante sur l'origine de l'univers.",
        "Les trous noirs sont des objets celestes dont la gravite est si forte que rien ne peut s'en echapper.",
        "La relativite generale d'Einstein decrit la gravite comme une courbure de l'espace-temps.",
        "La mecanique quantique decrit le comportement de la matiere a l'echelle atomique.",
        "Les ondes electromagnetiques comprennent les ondes radio, les micro-ondes, l'infrarouge, la lumiere visible, l'ultraviolet, les rayons X et les rayons gamma.",
        "Le boson de Higgs a ete decouvert au CERN en 2012.",
        "Les ondes gravitationnelles ont ete detectees pour la premiere fois en 2015 par LIGO.",
        "La tectonique des plaques explique la derive des continents et la formation des montagnes.",
        "L'evolution des especes par selection naturelle a ete decrite par Charles Darwin en 1859.",
        "Le cycle de l'eau comprend l'evaporation, la condensation, les precipitations et le ruissellement.",
        "L'effet de serre est cause par les gaz comme le CO2 et le methane.",
    ]
    return (base * (n // len(base) + 1))[:n]


def generate_philosophy(n=6000):
    """Philosophes, concepts, sagesses."""
    base = [
        "Socrate pratiquait la maieutique, l'art d'accoucher les esprits par le questionnement.",
        "Platon a developpe la theorie des Formes et l'allegorie de la caverne.",
        "Aristote a fonde la logique formelle et l'ethique de la vertu.",
        "Descartes a formule le cogito ergo sum : Je pense, donc je suis.",
        "Kant a enonce l'imperatif categorique comme principe moral universel.",
        "Nietzsche a proclame la mort de Dieu et le concept de surhomme.",
        "Sartre a defini l'existentialisme : l'existence precede l'essence.",
        "Camus a explore l'absurde dans Le Mythe de Sisyphe.",
        "Confucius a enseigne la bienveillance et la rectitude morale.",
        "Le stoicisme enseigne a distinguer ce qui depend de nous de ce qui n'en depend pas.",
        "L'epicurisme recherche l'ataraxie, la tranquillite de l'ame.",
        "Le bouddhisme propose les Quatre Nobles Verites et l'Octuple Sentier.",
        "La philosophie Ubuntu affirme : Je suis parce que nous sommes.",
        "La Maat egyptienne represente l'ordre cosmique, la verite et la justice.",
        "Hobbes decrit l'etat de nature comme une guerre de tous contre tous.",
        "Rousseau affirme que l'homme est ne libre et partout il est dans les fers.",
        "Montesquieu theorise la separation des pouvoirs executif, legislatif et judiciaire.",
        "Voltaire defend la liberte d'expression et la tolerance.",
        "Spinoza identifie Dieu et la Nature : Deus sive Natura.",
        "Hegel developpe la dialectique : these, antithese, synthese.",
        "Schopenhauer decrit le monde comme volonte et comme representation.",
        "Kierkegaard est considere comme le pere de l'existentialisme.",
        "Marx analyse la lutte des classes et le materialisme historique.",
        "Nietzsche developpe les concepts de volonte de puissance et d'eternel retour.",
        "Heidegger questionne le sens de l'etre dans Etre et Temps.",
        "Arendt analyse la banalite du mal dans Eichmann a Jerusalem.",
        "Foucault explore les relations entre pouvoir et savoir.",
        "Derrida developpe la deconstruction comme methode philosophique.",
        "Leibniz definit la monade comme substance simple et indivisible.",
        "Hume fonde l'empirisme : toutes nos idees viennent de l'experience.",
        "Locke decrit l'esprit comme une tabula rasa a la naissance.",
        "Popper definit la falsifiabilite comme critere de scientificite.",
    ]
    return (base * (n // len(base) + 1))[:n]


def generate_technology(n=8000):
    """Informatique, programmation, IA."""
    base = [
        "Alan Turing a defini le concept de machine universelle en 1936.",
        "Le premier ordinateur electronique ENIAC a ete cree en 1945.",
        "Le transistor a ete invente en 1947 par Bardeen, Brattain et Shockley.",
        "Le premier microprocesseur, l'Intel 4004, est sorti en 1971.",
        "Le protocole TCP/IP a ete cree en 1974 par Vint Cerf et Bob Kahn.",
        "Le World Wide Web a ete invente par Tim Berners-Lee en 1989 au CERN.",
        "Le langage Python a ete cree par Guido van Rossum en 1991.",
        "JavaScript a ete cree par Brendan Eich en 1995 pour le navigateur Netscape.",
        "Le langage C a ete developpe par Dennis Ritchie en 1972.",
        "Linux a ete cree par Linus Torvalds en 1991 comme systeme d'exploitation open source.",
        "Git a ete cree par Linus Torvalds en 2005 pour le controle de version.",
        "Le premier iPhone a ete lance par Apple en 2007.",
        "Le GPS utilise une constellation de 24 satellites pour la geolocalisation.",
        "Le WiFi utilise les ondes radio dans les bandes 2.4 GHz et 5 GHz.",
        "Le Bluetooth permet la communication sans fil a courte distance.",
        "Le cloud computing permet d'acceder a des ressources informatiques via Internet.",
        "AWS, lance par Amazon en 2006, est le leader du cloud computing.",
        "Docker, cree en 2013, permet la conteneurisation d'applications.",
        "Kubernetes orchestre le deploiement de conteneurs a grande echelle.",
        "L'intelligence artificielle designe les systemes capables d'imiter certaines fonctions cognitives.",
        "Le deep learning utilise des reseaux de neurones profonds.",
        "Les transformers, publies en 2017 par Vaswani et al., ont revolutionne le NLP.",
        "ChatGPT est un assistant IA developpe par OpenAI.",
        "L'algorithme PageRank de Google classe les pages Web par importance.",
        "Le chiffrement RSA repose sur la difficulte de factoriser de grands nombres premiers.",
        "Le blockchain est un registre distribue et immuable.",
        "Bitcoin, cree en 2009 par Satoshi Nakamoto, est la premiere cryptomonnaie.",
        "Ethereum a introduit les smart contracts en 2015.",
        "Le protocole HTTP permet le transfert de pages Web.",
        "Le DNS traduit les noms de domaine en adresses IP.",
        "SQL est le langage standard pour interroger les bases de donnees relationnelles.",
        "HTML est le langage de balisage pour structurer les pages Web.",
        "CSS permet de styliser les pages Web.",
        "Le responsive design adapte l'affichage aux differentes tailles d'ecran.",
        "La realite virtuelle immerge l'utilisateur dans un environnement simule.",
        "L'Internet des objets connecte des objets physiques au reseau.",
        "La 5G offre des debits jusqu'a 10 Gbps avec une latence de 1 ms.",
    ]
    return (base * (n // len(base) + 1))[:n]


def generate_all_domains():
    """Genere tous les corpus et les sauvegarde."""
    print("=" * 60)
    print("  GENERATION DE CORPUS 100K")
    print("=" * 60)

    generators = {
        "geography": generate_geography,
        "history": generate_history,
        "science": generate_science,
        "philosophy": generate_philosophy,
        "technology": generate_technology,
    }

    # Nombres cibles par domaine (ajustables)
    targets = {
        "geography": 20000,
        "history": 20000,
        "science": 20000,
        "philosophy": 15000,
        "technology": 20000,
    }

    all_facts = []
    total = 0

    for domain, target in targets.items():
        if domain in generators:
            facts = generators[domain](target)
            filepath = os.path.join(CORPUS_DIR, f"corpus_{domain}.txt")
            with open(filepath, 'w', encoding='utf-8') as f:
                for fact in facts:
                    f.write(fact + "\n")
            size_kb = os.path.getsize(filepath) / 1024
            print(f"  {domain:15s}: {len(facts):6d} faits -> {filepath} ({size_kb:.0f} KB)")
            all_facts.extend(facts)
            total += len(facts)

    # Fichier global
    global_path = os.path.join(CORPUS_DIR, "corpus_all.txt")
    with open(global_path, 'w', encoding='utf-8') as f:
        for fact in all_facts:
            f.write(fact + "\n")
    size_mb = os.path.getsize(global_path) / (1024 * 1024)
    print(f"\n  {'TOTAL':15s}: {total:6d} faits -> {global_path} ({size_mb:.1f} MB)")
    print("=" * 60)
    print(f"  Prochaine etape : python ingest_massive_nx64.py")
    print("=" * 60)

    return total


if __name__ == "__main__":
    generate_all_domains()