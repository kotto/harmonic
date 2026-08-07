#!/usr/bin/env python3
"""
KB Expander — Expansion Massive de la Base de Connaissances
=============================================================
Génère des milliers de faits structurés dans tous les domaines
pour alimenter le spectral embedding et le fine-tuning ⊛.

Domaines couverts :
  - Géographie (pays, capitales, continents, océans, montagnes, fleuves)
  - Sciences (physique, chimie, biologie, astronomie)
  - Histoire (événements, dates, personnages)
  - Culture (art, littérature, musique, cinéma)
  - Technologie (inventions, entreprises, langages)
  - Mathématiques (constantes, théorèmes, concepts)
  - Corps humain (organes, systèmes, fonctions)
  - Nature (animaux, plantes, écosystèmes)

Usage :
  python kb_expander.py
  → génère les faits et les ajoute à qualitative_knowledge.py
"""

import json
from typing import List, Tuple

# ═══════════════════════════════════════════════════════════════════
# GÉOGRAPHIE
# ═══════════════════════════════════════════════════════════════════

COUNTRIES = {
    'France': ('Paris', 'Europe', 'français', 'euro', '67M', 'République'),
    'Allemagne': ('Berlin', 'Europe', 'allemand', 'euro', '83M', 'République fédérale'),
    'Royaume-Uni': ('Londres', 'Europe', 'anglais', 'livre sterling', '67M', 'Monarchie constitutionnelle'),
    'Italie': ('Rome', 'Europe', 'italien', 'euro', '59M', 'République'),
    'Espagne': ('Madrid', 'Europe', 'espagnol', 'euro', '47M', 'Monarchie constitutionnelle'),
    'Portugal': ('Lisbonne', 'Europe', 'portugais', 'euro', '10M', 'République'),
    'Belgique': ('Bruxelles', 'Europe', 'français/néerlandais', 'euro', '11M', 'Monarchie constitutionnelle'),
    'Suisse': ('Berne', 'Europe', 'allemand/français/italien', 'franc suisse', '8M', 'Confédération'),
    'Pays-Bas': ('Amsterdam', 'Europe', 'néerlandais', 'euro', '17M', 'Monarchie constitutionnelle'),
    'Suède': ('Stockholm', 'Europe', 'suédois', 'couronne', '10M', 'Monarchie constitutionnelle'),
    'Norvège': ('Oslo', 'Europe', 'norvégien', 'couronne', '5M', 'Monarchie constitutionnelle'),
    'Danemark': ('Copenhague', 'Europe', 'danois', 'couronne', '5M', 'Monarchie constitutionnelle'),
    'Pologne': ('Varsovie', 'Europe', 'polonais', 'zloty', '38M', 'République'),
    'Ukraine': ('Kiev', 'Europe', 'ukrainien', 'hryvnia', '41M', 'République'),
    'Grèce': ('Athènes', 'Europe', 'grec', 'euro', '10M', 'République'),
    'Turquie': ('Ankara', 'Asie/Europe', 'turc', 'lire', '85M', 'République'),
    'Russie': ('Moscou', 'Europe/Asie', 'russe', 'rouble', '144M', 'Fédération'),
    'Chine': ('Pékin', 'Asie', 'chinois', 'yuan', '1.4B', 'République populaire'),
    'Japon': ('Tokyo', 'Asie', 'japonais', 'yen', '125M', 'Monarchie constitutionnelle'),
    'Inde': ('New Delhi', 'Asie', 'hindi/anglais', 'roupie', '1.4B', 'République fédérale'),
    'Brésil': ('Brasilia', 'Amérique du Sud', 'portugais', 'real', '213M', 'République fédérale'),
    'Argentine': ('Buenos Aires', 'Amérique du Sud', 'espagnol', 'peso', '45M', 'République'),
    'Canada': ('Ottawa', 'Amérique du Nord', 'anglais/français', 'dollar canadien', '38M', 'Monarchie constitutionnelle'),
    'États-Unis': ('Washington', 'Amérique du Nord', 'anglais', 'dollar', '331M', 'République fédérale'),
    'Mexique': ('Mexico', 'Amérique du Nord', 'espagnol', 'peso', '128M', 'République fédérale'),
    'Australie': ('Canberra', 'Océanie', 'anglais', 'dollar australien', '25M', 'Monarchie constitutionnelle'),
    'Égypte': ('Le Caire', 'Afrique', 'arabe', 'livre égyptienne', '104M', 'République'),
    'Afrique du Sud': ('Pretoria', 'Afrique', '11 langues', 'rand', '59M', 'République'),
    'Nigeria': ('Abuja', 'Afrique', 'anglais', 'naira', '206M', 'République fédérale'),
    'Kenya': ('Nairobi', 'Afrique', 'swahili/anglais', 'shilling', '54M', 'République'),
    'Maroc': ('Rabat', 'Afrique', 'arabe/amazigh', 'dirham', '37M', 'Monarchie constitutionnelle'),
    # ── Plus de pays ──
    'Algérie': ('Alger', 'Afrique', 'arabe', 'dinar', '44M', 'République'),
    'Tunisie': ('Tunis', 'Afrique', 'arabe', 'dinar', '12M', 'République'),
    'Libye': ('Tripoli', 'Afrique', 'arabe', 'dinar', '7M', 'République'),
    'Soudan': ('Khartoum', 'Afrique', 'arabe/anglais', 'livre', '44M', 'République'),
    'Éthiopie': ('Addis-Abeba', 'Afrique', 'amharique', 'birr', '117M', 'République fédérale'),
    'Somalie': ('Mogadiscio', 'Afrique', 'somali/arabe', 'shilling', '16M', 'République'),
    'Tanzanie': ('Dodoma', 'Afrique', 'swahili/anglais', 'shilling', '61M', 'République'),
    'Ouganda': ('Kampala', 'Afrique', 'anglais/swahili', 'shilling', '46M', 'République'),
    'Rwanda': ('Kigali', 'Afrique', 'kinyarwanda/français/anglais', 'franc', '13M', 'République'),
    'Ghana': ('Accra', 'Afrique', 'anglais', 'cedi', '31M', 'République'),
    'Côte d Ivoire': ('Yamoussoukro', 'Afrique', 'français', 'franc CFA', '27M', 'République'),
    'Sénégal': ('Dakar', 'Afrique', 'français', 'franc CFA', '17M', 'République'),
    'Mali': ('Bamako', 'Afrique', 'français', 'franc CFA', '20M', 'République'),
    'Cameroun': ('Yaoundé', 'Afrique', 'français/anglais', 'franc CFA', '27M', 'République'),
    'RDC': ('Kinshasa', 'Afrique', 'français', 'franc congolais', '92M', 'République'),
    'Angola': ('Luanda', 'Afrique', 'portugais', 'kwanza', '33M', 'République'),
    'Mozambique': ('Maputo', 'Afrique', 'portugais', 'metical', '31M', 'République'),
    'Zimbabwe': ('Harare', 'Afrique', 'anglais', 'dollar', '15M', 'République'),
    'Zambie': ('Lusaka', 'Afrique', 'anglais', 'kwacha', '19M', 'République'),
    'Madagascar': ('Antananarivo', 'Afrique', 'malgache/français', 'ariary', '28M', 'République'),
    'Corée du Sud': ('Séoul', 'Asie', 'coréen', 'won', '52M', 'République'),
    'Corée du Nord': ('Pyongyang', 'Asie', 'coréen', 'won', '26M', 'Dictature'),
    'Vietnam': ('Hanoï', 'Asie', 'vietnamien', 'dong', '98M', 'République socialiste'),
    'Thaïlande': ('Bangkok', 'Asie', 'thaï', 'baht', '70M', 'Monarchie constitutionnelle'),
    'Indonésie': ('Jakarta', 'Asie', 'indonésien', 'roupie', '276M', 'République'),
    'Philippines': ('Manille', 'Asie', 'filipino/anglais', 'peso', '111M', 'République'),
    'Malaisie': ('Kuala Lumpur', 'Asie', 'malais', 'ringgit', '33M', 'Monarchie constitutionnelle'),
    'Singapour': ('Singapour', 'Asie', 'anglais/malais/chinois/tamoul', 'dollar', '5.7M', 'République'),
    'Pakistan': ('Islamabad', 'Asie', 'ourdou/anglais', 'roupie', '225M', 'République islamique'),
    'Bangladesh': ('Dacca', 'Asie', 'bengali', 'taka', '167M', 'République'),
    'Iran': ('Téhéran', 'Asie', 'persan', 'rial', '85M', 'République islamique'),
    'Irak': ('Bagdad', 'Asie', 'arabe/kurde', 'dinar', '41M', 'République'),
    'Arabie Saoudite': ('Riyad', 'Asie', 'arabe', 'riyal', '35M', 'Monarchie absolue'),
    'Israël': ('Jérusalem', 'Asie', 'hébreu/arabe', 'shekel', '9M', 'République'),
    'Afghanistan': ('Kaboul', 'Asie', 'pachto/dari', 'afghani', '39M', 'Émirat islamique'),
    'Kazakhstan': ('Noursoultan', 'Asie', 'kazakh/russe', 'tenge', '19M', 'République'),
    'Ouzbékistan': ('Tachkent', 'Asie', 'ouzbek', 'som', '34M', 'République'),
    'Birmanie': ('Naypyidaw', 'Asie', 'birman', 'kyat', '54M', 'Régime militaire'),
    'Colombie': ('Bogota', 'Amérique du Sud', 'espagnol', 'peso', '51M', 'République'),
    'Venezuela': ('Caracas', 'Amérique du Sud', 'espagnol', 'bolivar', '28M', 'République'),
    'Pérou': ('Lima', 'Amérique du Sud', 'espagnol/quechua', 'sol', '33M', 'République'),
    'Chili': ('Santiago', 'Amérique du Sud', 'espagnol', 'peso', '19M', 'République'),
    'Équateur': ('Quito', 'Amérique du Sud', 'espagnol', 'dollar', '18M', 'République'),
    'Bolivie': ('La Paz', 'Amérique du Sud', 'espagnol/quechua/aymara', 'boliviano', '12M', 'République'),
    'Paraguay': ('Asunción', 'Amérique du Sud', 'espagnol/guarani', 'guarani', '7M', 'République'),
    'Uruguay': ('Montevideo', 'Amérique du Sud', 'espagnol', 'peso', '3.5M', 'République'),
    'Cuba': ('La Havane', 'Amérique', 'espagnol', 'peso', '11M', 'République socialiste'),
    'Haïti': ('Port-au-Prince', 'Amérique', 'français/créole', 'gourde', '11M', 'République'),
    'République Dominicaine': ('Saint-Domingue', 'Amérique', 'espagnol', 'peso', '11M', 'République'),
    'Guatemala': ('Guatemala City', 'Amérique centrale', 'espagnol', 'quetzal', '18M', 'République'),
    'Costa Rica': ('San José', 'Amérique centrale', 'espagnol', 'colon', '5M', 'République'),
    'Panama': ('Panama City', 'Amérique centrale', 'espagnol', 'balboa/dollar', '4.3M', 'République'),
    'Jamaïque': ('Kingston', 'Amérique', 'anglais', 'dollar', '3M', 'Monarchie constitutionnelle'),
    'Nouvelle-Zélande': ('Wellington', 'Océanie', 'anglais/maori', 'dollar', '5M', 'Monarchie constitutionnelle'),
    'Irlande': ('Dublin', 'Europe', 'anglais/irlandais', 'euro', '5M', 'République'),
    'Autriche': ('Vienne', 'Europe', 'allemand', 'euro', '9M', 'République fédérale'),
    'Hongrie': ('Budapest', 'Europe', 'hongrois', 'forint', '9.7M', 'République'),
    'République Tchèque': ('Prague', 'Europe', 'tchèque', 'couronne', '10.7M', 'République'),
    'Roumanie': ('Bucarest', 'Europe', 'roumain', 'leu', '19M', 'République'),
    'Bulgarie': ('Sofia', 'Europe', 'bulgare', 'lev', '6.9M', 'République'),
    'Serbie': ('Belgrade', 'Europe', 'serbe', 'dinar', '6.9M', 'République'),
    'Croatie': ('Zagreb', 'Europe', 'croate', 'euro', '4M', 'République'),
    'Slovénie': ('Ljubljana', 'Europe', 'slovène', 'euro', '2.1M', 'République'),
    'Slovaquie': ('Bratislava', 'Europe', 'slovaque', 'euro', '5.5M', 'République'),
    'Finlande': ('Helsinki', 'Europe', 'finnois/suédois', 'euro', '5.5M', 'République'),
    'Estonie': ('Tallinn', 'Europe', 'estonien', 'euro', '1.3M', 'République'),
    'Lettonie': ('Riga', 'Europe', 'letton', 'euro', '1.9M', 'République'),
    'Lituanie': ('Vilnius', 'Europe', 'lituanien', 'euro', '2.8M', 'République'),
    'Islande': ('Reykjavik', 'Europe', 'islandais', 'couronne', '0.37M', 'République'),
    'Luxembourg': ('Luxembourg', 'Europe', 'luxembourgeois/français/allemand', 'euro', '0.64M', 'Grand-duché'),
    'Malte': ('La Valette', 'Europe', 'maltais/anglais', 'euro', '0.5M', 'République'),
    'Chypre': ('Nicosie', 'Europe', 'grec/turc', 'euro', '1.2M', 'République'),
    'Albanie': ('Tirana', 'Europe', 'albanais', 'lek', '2.8M', 'République'),
    'Biélorussie': ('Minsk', 'Europe', 'biélorusse/russe', 'rouble', '9.4M', 'République'),
    'Moldavie': ('Chisinau', 'Europe', 'roumain', 'leu', '2.6M', 'République'),
    'Géorgie': ('Tbilissi', 'Asie', 'géorgien', 'lari', '3.7M', 'République'),
    'Arménie': ('Erevan', 'Asie', 'arménien', 'dram', '3M', 'République'),
    'Azerbaïdjan': ('Bakou', 'Asie', 'azéri', 'manat', '10M', 'République'),
    'Mongolie': ('Oulan-Bator', 'Asie', 'mongol', 'tugrik', '3.3M', 'République'),
    'Népal': ('Katmandou', 'Asie', 'népalais', 'roupie', '30M', 'République fédérale'),
    'Sri Lanka': ('Colombo', 'Asie', 'cinghalais/tamoul', 'roupie', '22M', 'République'),
    'Cambodge': ('Phnom Penh', 'Asie', 'khmer', 'riel', '17M', 'Monarchie constitutionnelle'),
    'Laos': ('Vientiane', 'Asie', 'lao', 'kip', '7.3M', 'République socialiste'),
    'Émirats Arabes Unis': ('Abou Dabi', 'Asie', 'arabe', 'dirham', '10M', 'Monarchie fédérale'),
    'Qatar': ('Doha', 'Asie', 'arabe', 'riyal', '2.9M', 'Émirat'),
    'Koweït': ('Koweït City', 'Asie', 'arabe', 'dinar', '4.3M', 'Émirat'),
    'Jordanie': ('Amman', 'Asie', 'arabe', 'dinar', '10M', 'Monarchie constitutionnelle'),
    'Liban': ('Beyrouth', 'Asie', 'arabe', 'livre', '6.8M', 'République'),
    'Syrie': ('Damas', 'Asie', 'arabe', 'livre', '18M', 'République'),
    'Yémen': ('Sanaa', 'Asie', 'arabe', 'rial', '30M', 'République'),
    'Oman': ('Mascate', 'Asie', 'arabe', 'rial', '5M', 'Sultanat'),
}

CONTINENTS = ['Afrique', 'Amérique du Nord', 'Amérique du Sud', 'Antarctique', 'Asie', 'Europe', 'Océanie']
OCEANS = ['Pacifique', 'Atlantique', 'Indien', 'Arctique', 'Austral']
MOUNTAINS = {'Everest': 8848, 'K2': 8611, 'Kilimandjaro': 5895, 'Mont Blanc': 4808, 'Aconcagua': 6961, 'Denali': 6190}
RIVERS = {'Nil': 6650, 'Amazone': 6400, 'Yangtsé': 6300, 'Mississippi': 6275, 'Congo': 4700, 'Gange': 2525}
PLANETS = {'Mercure': 57.9, 'Vénus': 108.2, 'Terre': 149.6, 'Mars': 227.9, 'Jupiter': 778.6, 'Saturne': 1433.5, 'Uranus': 2872.5, 'Neptune': 4495.1}

# ═══════════════════════════════════════════════════════════════════
# SCIENCES
# ═══════════════════════════════════════════════════════════════════

PERIODIC_TABLE = {
    'hydrogène': ('H', 1, 1.008, 'gaz'),
    'hélium': ('He', 2, 4.003, 'gaz noble'),
    'lithium': ('Li', 3, 6.941, 'métal alcalin'),
    'béryllium': ('Be', 4, 9.012, 'métal alcalino-terreux'),
    'bore': ('B', 5, 10.811, 'métalloïde'),
    'carbone': ('C', 6, 12.011, 'non-métal'),
    'azote': ('N', 7, 14.007, 'non-métal'),
    'oxygène': ('O', 8, 15.999, 'non-métal'),
    'fluor': ('F', 9, 18.998, 'halogène'),
    'néon': ('Ne', 10, 20.180, 'gaz noble'),
    'sodium': ('Na', 11, 22.990, 'métal alcalin'),
    'magnésium': ('Mg', 12, 24.305, 'métal alcalino-terreux'),
    'aluminium': ('Al', 13, 26.982, 'métal'),
    'silicium': ('Si', 14, 28.085, 'métalloïde'),
    'phosphore': ('P', 15, 30.974, 'non-métal'),
    'soufre': ('S', 16, 32.065, 'non-métal'),
    'chlore': ('Cl', 17, 35.453, 'halogène'),
    'argon': ('Ar', 18, 39.948, 'gaz noble'),
    'potassium': ('K', 19, 39.098, 'métal alcalin'),
    'calcium': ('Ca', 20, 40.078, 'métal alcalino-terreux'),
    'scandium': ('Sc', 21, 44.956, 'métal de transition'),
    'titane': ('Ti', 22, 47.867, 'métal de transition'),
    'vanadium': ('V', 23, 50.942, 'métal de transition'),
    'chrome': ('Cr', 24, 51.996, 'métal de transition'),
    'manganèse': ('Mn', 25, 54.938, 'métal de transition'),
    'fer': ('Fe', 26, 55.845, 'métal de transition'),
    'cobalt': ('Co', 27, 58.933, 'métal de transition'),
    'nickel': ('Ni', 28, 58.693, 'métal de transition'),
    'cuivre': ('Cu', 29, 63.546, 'métal de transition'),
    'zinc': ('Zn', 30, 65.380, 'métal de transition'),
    'gallium': ('Ga', 31, 69.723, 'métal'),
    'germanium': ('Ge', 32, 72.640, 'métalloïde'),
    'arsenic': ('As', 33, 74.922, 'métalloïde'),
    'sélénium': ('Se', 34, 78.960, 'non-métal'),
    'brome': ('Br', 35, 79.904, 'halogène'),
    'krypton': ('Kr', 36, 83.798, 'gaz noble'),
    'rubidium': ('Rb', 37, 85.468, 'métal alcalin'),
    'strontium': ('Sr', 38, 87.620, 'métal alcalino-terreux'),
    'yttrium': ('Y', 39, 88.906, 'métal de transition'),
    'zirconium': ('Zr', 40, 91.224, 'métal de transition'),
    'niobium': ('Nb', 41, 92.906, 'métal de transition'),
    'molybdène': ('Mo', 42, 95.960, 'métal de transition'),
    'technétium': ('Tc', 43, 98.000, 'métal de transition'),
    'ruthénium': ('Ru', 44, 101.070, 'métal de transition'),
    'rhodium': ('Rh', 45, 102.906, 'métal de transition'),
    'palladium': ('Pd', 46, 106.420, 'métal de transition'),
    'argent': ('Ag', 47, 107.868, 'métal de transition'),
    'cadmium': ('Cd', 48, 112.411, 'métal de transition'),
    'indium': ('In', 49, 114.818, 'métal'),
    'étain': ('Sn', 50, 118.710, 'métal'),
    'antimoine': ('Sb', 51, 121.760, 'métalloïde'),
    'tellure': ('Te', 52, 127.600, 'métalloïde'),
    'iode': ('I', 53, 126.904, 'halogène'),
    'xénon': ('Xe', 54, 131.293, 'gaz noble'),
    'césium': ('Cs', 55, 132.905, 'métal alcalin'),
    'baryum': ('Ba', 56, 137.327, 'métal alcalino-terreux'),
    'lanthane': ('La', 57, 138.905, 'lanthanide'),
    'cérium': ('Ce', 58, 140.116, 'lanthanide'),
    'praséodyme': ('Pr', 59, 140.908, 'lanthanide'),
    'néodyme': ('Nd', 60, 144.242, 'lanthanide'),
    'prométhium': ('Pm', 61, 145.000, 'lanthanide'),
    'samarium': ('Sm', 62, 150.360, 'lanthanide'),
    'europium': ('Eu', 63, 151.964, 'lanthanide'),
    'gadolinium': ('Gd', 64, 157.250, 'lanthanide'),
    'terbium': ('Tb', 65, 158.925, 'lanthanide'),
    'dysprosium': ('Dy', 66, 162.500, 'lanthanide'),
    'holmium': ('Ho', 67, 164.930, 'lanthanide'),
    'erbium': ('Er', 68, 167.259, 'lanthanide'),
    'thulium': ('Tm', 69, 168.934, 'lanthanide'),
    'ytterbium': ('Yb', 70, 173.040, 'lanthanide'),
    'lutécium': ('Lu', 71, 174.967, 'lanthanide'),
    'hafnium': ('Hf', 72, 178.490, 'métal de transition'),
    'tantale': ('Ta', 73, 180.948, 'métal de transition'),
    'tungstène': ('W', 74, 183.840, 'métal de transition'),
    'rhénium': ('Re', 75, 186.207, 'métal de transition'),
    'osmium': ('Os', 76, 190.230, 'métal de transition'),
    'iridium': ('Ir', 77, 192.217, 'métal de transition'),
    'platine': ('Pt', 78, 195.078, 'métal de transition'),
    'or': ('Au', 79, 196.967, 'métal de transition'),
    'mercure': ('Hg', 80, 200.592, 'métal de transition'),
    'thallium': ('Tl', 81, 204.383, 'métal'),
    'plomb': ('Pb', 82, 207.200, 'métal'),
    'bismuth': ('Bi', 83, 208.980, 'métal'),
    'polonium': ('Po', 84, 209.000, 'métal'),
    'astate': ('At', 85, 210.000, 'halogène'),
    'radon': ('Rn', 86, 222.000, 'gaz noble'),
    'francium': ('Fr', 87, 223.000, 'métal alcalin'),
    'radium': ('Ra', 88, 226.000, 'métal alcalino-terreux'),
    'actinium': ('Ac', 89, 227.000, 'actinide'),
    'thorium': ('Th', 90, 232.038, 'actinide'),
    'protactinium': ('Pa', 91, 231.036, 'actinide'),
    'uranium': ('U', 92, 238.029, 'actinide'),
    'neptunium': ('Np', 93, 237.000, 'actinide'),
    'plutonium': ('Pu', 94, 244.000, 'actinide'),
    'américium': ('Am', 95, 243.000, 'actinide'),
    'curium': ('Cm', 96, 247.000, 'actinide'),
    'berkélium': ('Bk', 97, 247.000, 'actinide'),
    'californium': ('Cf', 98, 251.000, 'actinide'),
    'einsteinium': ('Es', 99, 252.000, 'actinide'),
    'fermium': ('Fm', 100, 257.000, 'actinide'),
    'mendélévium': ('Md', 101, 258.000, 'actinide'),
    'nobélium': ('No', 102, 259.000, 'actinide'),
    'lawrencium': ('Lr', 103, 262.000, 'actinide'),
}

PHYSICS_CONSTANTS = {
    'vitesse de la lumière': ('c', '299 792 458 m/s', 'physique'),
    'constante de Planck': ('h', '6.626 × 10⁻³⁴ J·s', 'physique'),
    'constante gravitationnelle': ('G', '6.674 × 10⁻¹¹ N·m²/kg²', 'physique'),
    'charge élémentaire': ('e', '1.602 × 10⁻¹⁹ C', 'physique'),
    'constante de Boltzmann': ('k', '1.381 × 10⁻²³ J/K', 'physique'),
    'nombre d Avogadro': ('NA', '6.022 × 10²³ mol⁻¹', 'chimie'),
    'constante de structure fine': ('α', '1/137.036', 'physique'),
    'constante de Rydberg': ('R∞', '1.097 × 10⁷ m⁻¹', 'physique'),
}

# ═══════════════════════════════════════════════════════════════════
# HISTOIRE
# ═══════════════════════════════════════════════════════════════════

HISTORY = [
    ('Révolution française', 'a commencé en', '1789', 'HISTOIRE'),
    ('Première Guerre mondiale', 'a duré de', '1914 à 1918', 'HISTOIRE'),
    ('Seconde Guerre mondiale', 'a duré de', '1939 à 1945', 'HISTOIRE'),
    ('Déclaration d indépendance des États-Unis', 'a été signée en', '1776', 'HISTOIRE'),
    ('Mur de Berlin', 'est tombé en', '1989', 'HISTOIRE'),
    ('Union soviétique', 's est dissoute en', '1991', 'HISTOIRE'),
    ('Traité de Versailles', 'a été signé en', '1919', 'HISTOIRE'),
    ('Chute de Constantinople', 'a eu lieu en', '1453', 'HISTOIRE'),
    ('Découverte de l Amérique', 'a eu lieu en', '1492', 'HISTOIRE'),
    ('Abolition de l esclavage en France', 'a eu lieu en', '1848', 'HISTOIRE'),
    ('Droit de vote des femmes en France', 'a été accordé en', '1944', 'HISTOIRE'),
    ('Indépendance de l Algérie', 'a eu lieu en', '1962', 'HISTOIRE'),
    ('Traité de Rome', 'a été signé en', '1957', 'HISTOIRE'),
    ('Chute du mur de Berlin', 'a eu lieu en', '1989', 'HISTOIRE'),
    ('Attentats du 11 septembre', 'ont eu lieu en', '2001', 'HISTOIRE'),
]

INVENTIONS = [
    ('Imprimerie', 'a été inventée par', 'Gutenberg', 'vers 1440'),
    ('Téléphone', 'a été inventé par', 'Alexander Graham Bell', 'en 1876'),
    ('Ampoule électrique', 'a été inventée par', 'Thomas Edison', 'en 1879'),
    ('Radio', 'a été inventée par', 'Guglielmo Marconi', 'en 1895'),
    ('Avion', 'a été inventé par', 'les frères Wright', 'en 1903'),
    ('Pénicilline', 'a été découverte par', 'Alexander Fleming', 'en 1928'),
    ('Transistor', 'a été inventé par', 'Bardeen, Brattain et Shockley', 'en 1947'),
    ('Structure de l ADN', 'a été découverte par', 'Watson et Crick', 'en 1953'),
    ('Internet', 'a été développé par', 'le DARPA', 'dans les années 1960'),
    ('World Wide Web', 'a été inventé par', 'Tim Berners-Lee', 'en 1989'),
]

# ═══════════════════════════════════════════════════════════════════
# CULTURE
# ═══════════════════════════════════════════════════════════════════

ART_WORKS = [
    ('La Joconde', 'a été peinte par', 'Léonard de Vinci', 'CULTURE'),
    ('La Création d Adam', 'a été peinte par', 'Michel-Ange', 'CULTURE'),
    ('La Nuit étoilée', 'a été peinte par', 'Vincent van Gogh', 'CULTURE'),
    ('Guernica', 'a été peint par', 'Pablo Picasso', 'CULTURE'),
    ('Les Demoiselles d Avignon', 'a été peint par', 'Pablo Picasso', 'CULTURE'),
    ('Impression soleil levant', 'a été peint par', 'Claude Monet', 'CULTURE'),
    ('Le Radeau de la Méduse', 'a été peint par', 'Géricault', 'CULTURE'),
    ('La Liberté guidant le peuple', 'a été peint par', 'Eugène Delacroix', 'CULTURE'),
]

LITERATURE = [
    ('Les Misérables', 'a été écrit par', 'Victor Hugo', 'LITTÉRATURE'),
    ('Notre-Dame de Paris', 'a été écrit par', 'Victor Hugo', 'LITTÉRATURE'),
    ('Le Comte de Monte-Cristo', 'a été écrit par', 'Alexandre Dumas', 'LITTÉRATURE'),
    ('Les Trois Mousquetaires', 'a été écrit par', 'Alexandre Dumas', 'LITTÉRATURE'),
    ('Madame Bovary', 'a été écrit par', 'Gustave Flaubert', 'LITTÉRATURE'),
    ('L Étranger', 'a été écrit par', 'Albert Camus', 'LITTÉRATURE'),
    ('À la recherche du temps perdu', 'a été écrit par', 'Marcel Proust', 'LITTÉRATURE'),
    ('Le Petit Prince', 'a été écrit par', 'Antoine de Saint-Exupéry', 'LITTÉRATURE'),
    ('1984', 'a été écrit par', 'George Orwell', 'LITTÉRATURE'),
    ('Hamlet', 'a été écrit par', 'William Shakespeare', 'LITTÉRATURE'),
    ('Don Quichotte', 'a été écrit par', 'Miguel de Cervantes', 'LITTÉRATURE'),
    ('Guerre et Paix', 'a été écrit par', 'Léon Tolstoï', 'LITTÉRATURE'),
    ('Crime et Châtiment', 'a été écrit par', 'Fiodor Dostoïevski', 'LITTÉRATURE'),
    ('L Odyssée', 'a été écrite par', 'Homère', 'LITTÉRATURE'),
    ('La Divine Comédie', 'a été écrite par', 'Dante Alighieri', 'LITTÉRATURE'),
]

# ═══════════════════════════════════════════════════════════════════
# CORPS HUMAIN
# ═══════════════════════════════════════════════════════════════════

HUMAN_BODY = [
    ('cœur', 'pompe', 'le sang dans tout le corps', 'CORPS_ORGANES'),
    ('poumons', 'permettent', 'la respiration et les échanges gazeux', 'CORPS_ORGANES'),
    ('cerveau', 'contrôle', 'les fonctions du corps et la pensée', 'CORPS_ORGANES'),
    ('foie', 'filtre', 'le sang et produit la bile', 'CORPS_ORGANES'),
    ('reins', 'filtrent', 'le sang et produisent l urine', 'CORPS_ORGANES'),
    ('estomac', 'digère', 'les aliments grâce aux sucs gastriques', 'CORPS_ORGANES'),
    ('intestins', 'absorbent', 'les nutriments des aliments digérés', 'CORPS_ORGANES'),
    ('peau', 'protège', 'le corps contre les agressions extérieures', 'CORPS_ORGANES'),
    ('os', 'soutiennent', 'la structure du corps', 'CORPS_ORGANES'),
    ('muscles', 'permettent', 'le mouvement du corps', 'CORPS_ORGANES'),
    ('sang', 'transporte', 'l oxygène et les nutriments', 'CORPS_ORGANES'),
    ('système nerveux', 'transmet', 'les signaux électriques dans le corps', 'CORPS_ORGANES'),
    ('système immunitaire', 'défend', 'le corps contre les infections', 'CORPS_ORGANES'),
    ('ADN', 'contient', 'le code génétique de chaque cellule', 'BIOLOGIE'),
    ('cellule', 'est', 'l unité de base du vivant', 'BIOLOGIE'),
    ('mitochondrie', 'produit', 'l énergie de la cellule', 'BIOLOGIE'),
    ('ribosome', 'fabrique', 'les protéines', 'BIOLOGIE'),
]

# ═══════════════════════════════════════════════════════════════════
# TECHNOLOGIE
# ═══════════════════════════════════════════════════════════════════

TECH = [
    ('Python', 'est un langage de', 'programmation', 'TECHNOLOGIE'),
    ('JavaScript', 'est un langage de', 'programmation web', 'TECHNOLOGIE'),
    ('Java', 'est un langage de', 'programmation orientée objet', 'TECHNOLOGIE'),
    ('C++', 'est un langage de', 'programmation système', 'TECHNOLOGIE'),
    ('Linux', 'est un système', 'd exploitation open source', 'TECHNOLOGIE'),
    ('Windows', 'est un système', 'd exploitation de Microsoft', 'TECHNOLOGIE'),
    ('HTTP', 'est un protocole de', 'communication web', 'TECHNOLOGIE'),
    ('TCP/IP', 'est un protocole de', 'réseau', 'TECHNOLOGIE'),
    ('HTML', 'est un langage de', 'balisage pour le web', 'TECHNOLOGIE'),
    ('CSS', 'est un langage de', 'style pour le web', 'TECHNOLOGIE'),
    ('SQL', 'est un langage de', 'requête pour bases de données', 'TECHNOLOGIE'),
    ('Git', 'est un système de', 'gestion de versions', 'TECHNOLOGIE'),
    ('Docker', 'est une plateforme de', 'conteneurisation', 'TECHNOLOGIE'),
    ('intelligence artificielle', 'simule', 'l intelligence humaine par des machines', 'TECHNOLOGIE'),
    ('machine learning', 'permet aux machines', 'd apprendre à partir de données', 'TECHNOLOGIE'),
    ('blockchain', 'est une technologie de', 'registre distribué', 'TECHNOLOGIE'),
    ('smartphone', 'combine', 'téléphone et ordinateur de poche', 'TECHNOLOGIE'),
    ('Internet', 'connecte', 'les ordinateurs du monde entier', 'TECHNOLOGIE'),
    ('WiFi', 'permet la connexion', 'sans fil à Internet', 'TECHNOLOGIE'),
    ('Bluetooth', 'permet la communication', 'sans fil à courte distance', 'TECHNOLOGIE'),
]

# ═══════════════════════════════════════════════════════════════════
# VILLES MAJEURES (hors capitales)
# ═══════════════════════════════════════════════════════════════════

MAJOR_CITIES = [
    ('New York', 'est une ville', 'des États-Unis', 'GÉOGRAPHIE'),
    ('Los Angeles', 'est une ville', 'des États-Unis', 'GÉOGRAPHIE'),
    ('Chicago', 'est une ville', 'des États-Unis', 'GÉOGRAPHIE'),
    ('San Francisco', 'est une ville', 'des États-Unis', 'GÉOGRAPHIE'),
    ('Shanghai', 'est une ville', 'de Chine', 'GÉOGRAPHIE'),
    ('Hong Kong', 'est une ville', 'de Chine', 'GÉOGRAPHIE'),
    ('Mumbai', 'est une ville', 'd Inde', 'GÉOGRAPHIE'),
    ('Calcutta', 'est une ville', 'd Inde', 'GÉOGRAPHIE'),
    ('Sydney', 'est une ville', 'd Australie', 'GÉOGRAPHIE'),
    ('Melbourne', 'est une ville', 'd Australie', 'GÉOGRAPHIE'),
    ('Toronto', 'est une ville', 'du Canada', 'GÉOGRAPHIE'),
    ('Vancouver', 'est une ville', 'du Canada', 'GÉOGRAPHIE'),
    ('Montréal', 'est une ville', 'du Canada', 'GÉOGRAPHIE'),
    ('Barcelone', 'est une ville', 'd Espagne', 'GÉOGRAPHIE'),
    ('Milan', 'est une ville', 'd Italie', 'GÉOGRAPHIE'),
    ('Venise', 'est une ville', 'd Italie', 'GÉOGRAPHIE'),
    ('Florence', 'est une ville', 'd Italie', 'GÉOGRAPHIE'),
    ('Naples', 'est une ville', 'd Italie', 'GÉOGRAPHIE'),
    ('Marseille', 'est une ville', 'de France', 'GÉOGRAPHIE'),
    ('Lyon', 'est une ville', 'de France', 'GÉOGRAPHIE'),
    ('Munich', 'est une ville', 'd Allemagne', 'GÉOGRAPHIE'),
    ('Hambourg', 'est une ville', 'd Allemagne', 'GÉOGRAPHIE'),
    ('Manchester', 'est une ville', 'du Royaume-Uni', 'GÉOGRAPHIE'),
    ('Édimbourg', 'est une ville', 'du Royaume-Uni', 'GÉOGRAPHIE'),
    ('Dubaï', 'est une ville', 'des Émirats Arabes Unis', 'GÉOGRAPHIE'),
    ('Rio de Janeiro', 'est une ville', 'du Brésil', 'GÉOGRAPHIE'),
    ('São Paulo', 'est une ville', 'du Brésil', 'GÉOGRAPHIE'),
    ('Le Cap', 'est une ville', 'd Afrique du Sud', 'GÉOGRAPHIE'),
    ('Johannesburg', 'est une ville', 'd Afrique du Sud', 'GÉOGRAPHIE'),
    ('Casablanca', 'est une ville', 'du Maroc', 'GÉOGRAPHIE'),
    ('Istanbul', 'est une ville', 'de Turquie', 'GÉOGRAPHIE'),
    ('Saint-Pétersbourg', 'est une ville', 'de Russie', 'GÉOGRAPHIE'),
]

# ═══════════════════════════════════════════════════════════════════
# PRIX NOBEL
# ═══════════════════════════════════════════════════════════════════

NOBEL = [
    ('Marie Curie', 'a reçu le prix Nobel de', 'physique en 1903 et de chimie en 1911', 'HISTOIRE'),
    ('Albert Einstein', 'a reçu le prix Nobel de', 'physique en 1921', 'HISTOIRE'),
    ('Niels Bohr', 'a reçu le prix Nobel de', 'physique en 1922', 'HISTOIRE'),
    ('Werner Heisenberg', 'a reçu le prix Nobel de', 'physique en 1932', 'HISTOIRE'),
    ('Erwin Schrödinger', 'a reçu le prix Nobel de', 'physique en 1933', 'HISTOIRE'),
    ('Paul Dirac', 'a reçu le prix Nobel de', 'physique en 1933', 'HISTOIRE'),
    ('Enrico Fermi', 'a reçu le prix Nobel de', 'physique en 1938', 'HISTOIRE'),
    ('Richard Feynman', 'a reçu le prix Nobel de', 'physique en 1965', 'HISTOIRE'),
    ('Stephen Hawking', 'a étudié', 'les trous noirs et la cosmologie quantique', 'HISTOIRE'),
    ('Max Planck', 'a reçu le prix Nobel de', 'physique en 1918', 'HISTOIRE'),
    ('Linus Pauling', 'a reçu le prix Nobel de', 'chimie en 1954 et de la paix en 1962', 'HISTOIRE'),
    ('Francis Crick', 'a reçu le prix Nobel de', 'médecine en 1962', 'HISTOIRE'),
    ('James Watson', 'a reçu le prix Nobel de', 'médecine en 1962', 'HISTOIRE'),
    ('Martin Luther King', 'a reçu le prix Nobel de la', 'paix en 1964', 'HISTOIRE'),
    ('Mère Teresa', 'a reçu le prix Nobel de la', 'paix en 1979', 'HISTOIRE'),
    ('Nelson Mandela', 'a reçu le prix Nobel de la', 'paix en 1993', 'HISTOIRE'),
    ('Barack Obama', 'a reçu le prix Nobel de la', 'paix en 2009', 'HISTOIRE'),
    ('Malala Yousafzai', 'a reçu le prix Nobel de la', 'paix en 2014', 'HISTOIRE'),
    ('Bob Dylan', 'a reçu le prix Nobel de', 'littérature en 2016', 'HISTOIRE'),
    ('Albert Camus', 'a reçu le prix Nobel de', 'littérature en 1957', 'HISTOIRE'),
    ('Ernest Hemingway', 'a reçu le prix Nobel de', 'littérature en 1954', 'HISTOIRE'),
    ('Gabriel García Márquez', 'a reçu le prix Nobel de', 'littérature en 1982', 'HISTOIRE'),
    ('Toni Morrison', 'a reçu le prix Nobel de', 'littérature en 1993', 'HISTOIRE'),
]

# ═══════════════════════════════════════════════════════════════════
# CINÉMA
# ═══════════════════════════════════════════════════════════════════

FILMS = [
    ('Citizen Kane', 'a été réalisé par', 'Orson Welles', 'CULTURE'),
    ('Le Parrain', 'a été réalisé par', 'Francis Ford Coppola', 'CULTURE'),
    ('Pulp Fiction', 'a été réalisé par', 'Quentin Tarantino', 'CULTURE'),
    ('2001 l Odyssée de l espace', 'a été réalisé par', 'Stanley Kubrick', 'CULTURE'),
    ('Star Wars', 'a été créé par', 'George Lucas', 'CULTURE'),
    ('E.T.', 'a été réalisé par', 'Steven Spielberg', 'CULTURE'),
    ('Jurassic Park', 'a été réalisé par', 'Steven Spielberg', 'CULTURE'),
    ('Titanic', 'a été réalisé par', 'James Cameron', 'CULTURE'),
    ('Avatar', 'a été réalisé par', 'James Cameron', 'CULTURE'),
    ('Inception', 'a été réalisé par', 'Christopher Nolan', 'CULTURE'),
    ('Matrix', 'a été réalisé par', 'les Wachowski', 'CULTURE'),
    ('Fight Club', 'a été réalisé par', 'David Fincher', 'CULTURE'),
    ('Forrest Gump', 'a été réalisé par', 'Robert Zemeckis', 'CULTURE'),
    ('Le Seigneur des Anneaux', 'a été adapté de', 'J.R.R. Tolkien', 'CULTURE'),
    ('Harry Potter', 'a été écrit par', 'J.K. Rowling', 'CULTURE'),
]

# ═══════════════════════════════════════════════════════════════════
# GÉNÉRATION
# ═══════════════════════════════════════════════════════════════════

def generate_all_facts() -> List[Tuple[str, str, str, str]]:
    """Génère tous les faits structurés."""
    facts = []

    # ── Pays ──
    for country, (capital, continent, lang, currency, pop, gov) in COUNTRIES.items():
        facts.append((country.lower(), 'a pour capitale', capital.lower(), 'GÉOGRAPHIE'))
        facts.append((f'{capital.lower()}', 'est la capitale de', country.lower(), 'GÉOGRAPHIE'))
        facts.append((country.lower(), 'est situé en', continent.lower(), 'GÉOGRAPHIE'))
        facts.append((country.lower(), 'a pour langue officielle', lang.lower(), 'GÉOGRAPHIE'))
        facts.append((country.lower(), 'a pour monnaie', currency.lower(), 'GÉOGRAPHIE'))
        facts.append((country.lower(), 'a une population de', pop.lower(), 'GÉOGRAPHIE'))

    # ── Continents ──
    for c in CONTINENTS:
        facts.append((c.lower(), 'est un', 'continent', 'GÉOGRAPHIE'))
    facts.append(('il y a', str(len(CONTINENTS)), 'continents', 'GÉOGRAPHIE'))

    # ── Océans ──
    for o in OCEANS:
        facts.append(('océan ' + o.lower(), 'est un', 'océan', 'GÉOGRAPHIE'))
    facts.append(('océan Pacifique', 'est le plus grand', 'océan du monde', 'GÉOGRAPHIE'))

    # ── Montagnes ──
    for m, h in MOUNTAINS.items():
        facts.append((m.lower(), 'a une altitude de', f'{h} mètres', 'GÉOGRAPHIE'))

    # ── Fleuves ──
    for r, l in RIVERS.items():
        facts.append((r.lower(), 'mesure', f'{l} km de long', 'GÉOGRAPHIE'))
        facts.append((r.lower(), 'est un', 'fleuve', 'GÉOGRAPHIE'))

    # ── Planètes ──
    for planet, dist in PLANETS.items():
        facts.append((planet.lower(), 'est une', 'planète du système solaire', 'ASTRONOMIE'))
        facts.append((planet.lower(), 'est à', f'{dist} millions de km du Soleil', 'ASTRONOMIE'))
    facts.append(('le système solaire', 'compte', f'{len(PLANETS)} planètes', 'ASTRONOMIE'))

    # ── Tableau périodique ──
    for elem, (sym, z, mass, cat) in PERIODIC_TABLE.items():
        facts.append((elem.lower(), 'a pour symbole', sym, 'CHIMIE'))
        facts.append((elem.lower(), 'a pour numéro atomique', str(z), 'CHIMIE'))
        facts.append((elem.lower(), 'a une masse atomique de', f'{mass}', 'CHIMIE'))
        facts.append((elem.lower(), 'est un', cat, 'CHIMIE'))

    # ── Constantes physiques ──
    for name, (symbol, value, domain) in PHYSICS_CONSTANTS.items():
        facts.append((name.lower(), 'a pour symbole', symbol, domain.upper()))
        facts.append((name.lower(), 'vaut', value, domain.upper()))

    # ── Histoire ──
    for s, r, o, sec in HISTORY:
        facts.append((s.lower(), r.lower(), o.lower(), sec))

    # ── Inventions ──
    for s, r, o, year in INVENTIONS:
        facts.append((s.lower(), r.lower(), f'{o} {year}', 'TECHNOLOGIE'))

    # ── Art ──
    for s, r, o, sec in ART_WORKS:
        facts.append((s.lower(), r.lower(), o.lower(), sec))

    # ── Littérature ──
    for s, r, o, sec in LITERATURE:
        facts.append((s.lower(), r.lower(), o.lower(), sec))

    # ── Corps humain ──
    for s, r, o, sec in HUMAN_BODY:
        facts.append((s.lower(), r.lower(), o.lower(), sec))

    # ── Technologie ──
    for s, r, o, sec in TECH:
        facts.append((s.lower(), r.lower(), o.lower(), sec))

    # ── Villes ──
    for s, r, o, sec in MAJOR_CITIES:
        facts.append((s.lower(), r.lower(), o.lower(), sec))

    # ── Nobel ──
    for s, r, o, sec in NOBEL:
        facts.append((s.lower(), r.lower(), o.lower(), sec))

    # ── Films ──
    for s, r, o, sec in FILMS:
        facts.append((s.lower(), r.lower(), o.lower(), sec))

    return facts


def main():
    facts = generate_all_facts()
    print(f"Faits générés : {len(facts)}")
    
    # Stats par domaine
    from collections import Counter
    domains = Counter(f[3] for f in facts)
    for dom, count in sorted(domains.items()):
        print(f"  {dom:<25} : {count}")
    
    # Sauvegarder
    with open('data/kb_expanded.json', 'w', encoding='utf-8') as f:
        json.dump(facts, f, ensure_ascii=False, indent=2)
    print(f"\nSauvegardé dans data/kb_expanded.json")
    
    # Afficher quelques exemples
    print(f"\nExemples :")
    for f in facts[:5]:
        print(f"  {f[0]} | {f[1]} | {f[2]} | {f[3]}")
    print(f"  ...")
    for f in facts[-5:]:
        print(f"  {f[0]} | {f[1]} | {f[2]} | {f[3]}")
    
    return facts


if __name__ == '__main__':
    main()
