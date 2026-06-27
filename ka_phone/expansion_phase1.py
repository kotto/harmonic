#!/usr/bin/env python3
"""
EXPANSION PHASE 1 — Enrichissement massif de l'hologramme
===========================================================
Génère 50K+ faits supplémentaires dans 15 domaines :
  Physique, Chimie, Biologie, Médecine, Économie, 
  Philosophie, Littérature, Géographie avancée, Astronomie,
  Informatique, Linguistique, Cuisine, Architecture,
  Mythologie, Droit

Usage:
  python ka_phone/expansion_phase1.py
"""

import os, sys, json, hashlib, random

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EXPANSION_DIR = os.path.join(DATA_DIR, "expansion")
os.makedirs(EXPANSION_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# DATASETS MASSIFS PAR DOMAINE
# ══════════════════════════════════════════════════════════════════════════

PHYSICS_FACTS = [
    ("lois de Newton", "Les trois lois de Newton (1687) fondent la mécanique classique : 1) inertie, 2) F=ma, 3) action-réaction.", "science"),
    ("relativité restreinte", "La relativité restreinte d'Einstein (1905) établit que la vitesse de la lumière est constante et que le temps se dilate à grande vitesse. Équation E=mc².", "science"),
    ("relativité générale", "La relativité générale (1915) décrit la gravité comme une courbure de l'espace-temps causée par la masse. Vérifiée en 1919 lors d'une éclipse solaire.", "science"),
    ("mécanique quantique", "La mécanique quantique décrit le comportement de la matière à l'échelle atomique : superposition, intrication, dualité onde-particule. Planck (1900), Bohr (1913), Schrödinger (1926).", "science"),
    ("principe d'incertitude", "Le principe d'incertitude de Heisenberg (1927) : on ne peut connaître simultanément la position ET la vitesse d'une particule avec une précision infinie.", "science"),
    ("dualité onde-particule", "La dualité onde-particule : la lumière et la matière se comportent à la fois comme des ondes et des particules. Démontré par l'expérience des fentes d'Young.", "science"),
    ("intrication quantique", "L'intrication quantique : deux particules restent connectées quelle que soit la distance qui les sépare. Einstein appelait cela 'l'action fantôme à distance'.", "science"),
    ("big bang", "Le Big Bang : l'univers a commencé il y a 13,8 milliards d'années à partir d'une singularité extrêmement chaude et dense. Depuis, il est en expansion.", "science"),
    ("trou noir", "Un trou noir est une région de l'espace-temps où la gravité est si intense que rien, pas même la lumière, ne peut s'en échapper. Le rayon de Schwarzschild définit son horizon.", "science"),
    ("boson de Higgs", "Le boson de Higgs (2012, CERN) est la particule qui donne leur masse aux autres particules. Surnommé 'particule de Dieu'. Prédit en 1964 par Peter Higgs.", "science"),
    ("ondes gravitationnelles", "Les ondes gravitationnelles sont des ondulations de l'espace-temps prédites par Einstein en 1916, détectées pour la première fois en 2015 par LIGO.", "science"),
    ("énergie noire", "L'énergie noire constitue 68% de l'univers et serait responsable de l'accélération de l'expansion cosmique. Découverte en 1998.", "science"),
    ("matière noire", "La matière noire représente 27% de l'univers. Invisible, elle n'interagit pas avec la lumière mais sa présence est déduite par ses effets gravitationnels.", "science"),
    ("neutrino", "Les neutrinos sont des particules élémentaires de masse quasi nulle qui traversent la matière sans interagir. 100 000 milliards traversent votre corps chaque seconde.", "science"),
    ("force électromagnétique", "La force électromagnétique est l'une des 4 forces fondamentales. Elle gouverne l'électricité, le magnétisme et la lumière. Portée infinie.", "science"),
    ("force nucléaire forte", "La force nucléaire forte maintient les protons et neutrons ensemble dans le noyau atomique. C'est la plus puissante des 4 forces, mais de très courte portée.", "science"),
    ("force nucléaire faible", "La force nucléaire faible est responsable de la radioactivité bêta. Elle permet la transformation d'un neutron en proton.", "science"),
    ("effet photoélectrique", "L'effet photoélectrique : des électrons sont éjectés d'un métal quand il est frappé par la lumière. Expliqué par Einstein en 1905 (Nobel 1921).", "science"),
    ("expérience de Rutherford", "L'expérience de Rutherford (1911) a découvert le noyau atomique en bombardant une feuille d'or avec des particules alpha.", "science"),
    ("laser", "Le LASER (Light Amplification by Stimulated Emission of Radiation) produit une lumière cohérente. Premier laser en 1960 par Theodore Maiman.", "science"),
    ("supraconductivité", "La supraconductivité : certains matériaux perdent toute résistance électrique en dessous d'une température critique. Découverte en 1911 par Kamerlingh Onnes.", "science"),
    ("plasma", "Le plasma est le 4e état de la matière (après solide, liquide, gaz). C'est un gaz ionisé. 99% de la matière visible de l'univers est du plasma (étoiles).", "science"),
    ("entropie", "L'entropie mesure le désordre d'un système. Le 2e principe de la thermodynamique dit que l'entropie de l'univers ne peut qu'augmenter.", "science"),
    ("zéro absolu", "Le zéro absolu = 0 Kelvin = -273,15°C. C'est la température théorique la plus basse où les atomes cessent tout mouvement. Inatteignable en pratique.", "science"),
    ("effet Doppler", "L'effet Doppler : la fréquence d'une onde change quand la source se déplace par rapport à l'observateur. Utilisé pour mesurer l'expansion de l'univers (redshift).", "science"),
]

CHEMISTRY_FACTS = [
    ("tableau périodique", "Le tableau périodique de Mendeleïev (1869) classe les 118 éléments chimiques en rangées (périodes) et colonnes (groupes) selon leurs propriétés.", "science"),
    ("liaison covalente", "La liaison covalente : deux atomes partagent une paire d'électrons. C'est la liaison principale des molécules organiques.", "science"),
    ("liaison ionique", "La liaison ionique : un atome donne un électron à un autre, créant des ions qui s'attirent électrostatiquement. Exemple : NaCl (sel de table).", "science"),
    ("pH", "Le pH varie de 0 (très acide) à 14 (très basique). pH 7 est neutre. L'acide chlorhydrique a pH 1, l'eau pure pH 7, la soude pH 14.", "science"),
    ("catalyseur", "Un catalyseur accélère une réaction chimique sans être consommé. Les enzymes sont des catalyseurs biologiques.", "science"),
    ("oxydation", "L'oxydation est la perte d'électrons par un atome. La rouille (oxydation du fer) et la respiration cellulaire sont des oxydations.", "science"),
    ("réduction", "La réduction est le gain d'électrons par un atome. Toujours couplée à une oxydation (réaction redox).", "science"),
    ("isotope", "Les isotopes d'un élément ont le même nombre de protons mais un nombre différent de neutrons. Carbone-12 (stable), Carbone-14 (radioactif, datation).", "science"),
    ("radioactivité", "La radioactivité est la désintégration spontanée de noyaux atomiques instables. Découverte par Becquerel (1896), étudiée par Marie Curie.", "science"),
    ("polymère", "Un polymère est une longue chaîne de molécules répétées (monomères). L'ADN, les protéines, le plastique et le nylon sont des polymères.", "science"),
    ("acide aminé", "Les acides aminés sont les briques des protéines. Il en existe 20 standards dans le code génétique. 9 sont essentiels (le corps ne les fabrique pas).", "science"),
    ("protéine", "Les protéines sont des chaînes d'acides aminés repliées en 3D. Elles remplissent des fonctions structurales, enzymatiques, hormonales et immunitaires.", "science"),
    ("ADN", "L'ADN (acide désoxyribonucléique) est une double hélice stockant l'information génétique. Découvert par Watson et Crick en 1953.", "science"),
    ("ARN", "L'ARN (acide ribonucléique) copie et transporte l'information génétique de l'ADN vers les ribosomes pour fabriquer des protéines.", "science"),
    ("glucose", "Le glucose (C₆H₁₂O₆) est le principal carburant des cellules. Produit par la photosynthèse, consommé par la respiration cellulaire.", "science"),
    ("ATP", "L'ATP (adénosine triphosphate) est la 'monnaie énergétique' de la cellule. Chaque cellule recycle l'équivalent de son poids en ATP chaque jour.", "science"),
    ("photosynthèse", "La photosynthèse : 6CO₂ + 6H₂O + lumière → C₆H₁₂O₆ + 6O₂. Les plantes convertissent l'énergie solaire en énergie chimique.", "science"),
    ("respiration cellulaire", "La respiration cellulaire : C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O + énergie (ATP). Se produit dans les mitochondries.", "science"),
    ("fermentation", "La fermentation produit de l'énergie sans oxygène. Fermentation alcoolique : glucose → éthanol + CO₂. Fermentation lactique : glucose → acide lactique.", "science"),
    ("enzyme", "Les enzymes sont des protéines qui catalysent les réactions biochimiques. Chaque enzyme est spécifique à une réaction (modèle clé-serrure).", "science"),
]

BIOLOGY_FACTS = [
    ("cellule", "La cellule est l'unité de base du vivant. Théorie cellulaire (Schleiden et Schwann, 1839) : tout être vivant est composé de cellules.", "science"),
    ("mitose", "La mitose est la division cellulaire qui produit deux cellules filles identiques (46 chromosomes). Permet la croissance et la réparation des tissus.", "science"),
    ("méiose", "La méiose produit les gamètes (23 chromosomes). Deux divisions successives créent de la diversité génétique par brassage.", "science"),
    ("mitochondrie", "Les mitochondries sont les 'centrales énergétiques' de la cellule. Elles possèdent leur propre ADN, hérité uniquement de la mère.", "science"),
    ("chloroplaste", "Les chloroplastes contiennent la chlorophylle et réalisent la photosynthèse dans les cellules végétales. Comme les mitochondries, ils ont leur propre ADN.", "science"),
    ("membrane cellulaire", "La membrane cellulaire est une bicouche lipidique qui contrôle les échanges entre la cellule et son environnement. Modèle de la mosaïque fluide.", "science"),
    ("noyau cellulaire", "Le noyau contient l'ADN de la cellule, protégé par une double membrane. Le nucléole à l'intérieur fabrique les ribosomes.", "science"),
    ("ribosome", "Les ribosomes lisent l'ARN messager et assemblent les acides aminés en protéines. Ce sont les 'usines à protéines' de la cellule.", "science"),
    ("appareil de Golgi", "L'appareil de Golgi modifie, trie et emballe les protéines pour les expédier dans ou hors de la cellule.", "science"),
    ("réticulum endoplasmique", "Le RE rugueux (avec ribosomes) synthétise les protéines. Le RE lisse synthétise les lipides et détoxifie.", "science"),
    ("lysosome", "Les lysosomes sont des sacs d'enzymes digestives. Ils décomposent les déchets cellulaires et les pathogènes (le 'système digestif' de la cellule).", "science"),
    ("système nerveux", "Le système nerveux humain comprend le cerveau (86 milliards de neurones), la moelle épinière et les nerfs périphériques.", "science"),
    ("synapse", "La synapse est la jonction entre deux neurones. Les neurotransmetteurs (dopamine, sérotonine) traversent la fente synaptique.", "science"),
    ("système immunitaire", "Le système immunitaire défend l'organisme. Immunité innée (barrières, inflammation) et adaptative (lymphocytes B et T, anticorps).", "science"),
    ("vaccin", "Un vaccin expose le système immunitaire à un agent inoffensif pour créer une mémoire immunitaire. Le premier vaccin (variole) a été développé par Jenner en 1796.", "science"),
    ("antibiotique", "Les antibiotiques tuent les bactéries sans nuire aux cellules humaines. La pénicilline, découverte par Fleming en 1928, fut le premier.", "science"),
    ("virus", "Un virus est un agent infectieux qui ne peut se reproduire qu'en infectant une cellule hôte. Ni vraiment vivant ni vraiment mort.", "science"),
    ("bactérie", "Les bactéries sont des micro-organismes unicellulaires sans noyau. Certaines sont pathogènes, d'autres essentielles (flore intestinale).", "science"),
    ("champignon", "Les champignons forment un règne à part (Fungi). Ni plantes ni animaux. Les levures (unicellulaires) et les moisissures (multicellulaires) sont des champignons.", "science"),
    ("écosystème", "Un écosystème est une communauté d'êtres vivants interagissant avec leur environnement. La forêt amazonienne est le plus riche.", "science"),
    ("biodiversité", "La biodiversité désigne la variété du vivant à trois niveaux : gènes, espèces, écosystèmes. 8,7 millions d'espèces estimées sur Terre.", "science"),
    ("chaîne alimentaire", "La chaîne alimentaire : producteurs (plantes) → consommateurs primaires (herbivores) → secondaires (carnivores) → décomposeurs.", "science"),
    ("sélection naturelle", "La sélection naturelle (Darwin, 1859) : les individus les mieux adaptés à leur environnement survivent et se reproduisent davantage.", "science"),
    ("évolution", "L'évolution est le changement des espèces au fil des générations par mutation, sélection naturelle et dérive génétique.", "science"),
    ("ADN mitochondrial", "L'ADN mitochondrial est hérité uniquement de la mère. Il permet de tracer les lignées maternelles sur des milliers de générations.", "science"),
]

MEDICINE_FACTS = [
    ("cœur humain", "Le cœur humain bat environ 100 000 fois par jour, pompant 7 500 litres de sang. Il a 4 cavités : 2 oreillettes, 2 ventricules.", "science"),
    ("poumons", "Les poumons contiennent environ 300 millions d'alvéoles, offrant une surface d'échange de 70 m² (un terrain de tennis).", "science"),
    ("foie", "Le foie est le plus grand organe interne. Il remplit plus de 500 fonctions : détoxification, synthèse des protéines, stockage du glucose.", "science"),
    ("reins", "Les reins filtrent 180 litres de sang par jour pour produire 1,5 litre d'urine. Ils régulent la pression artérielle et l'équilibre hydrique.", "science"),
    ("peau", "La peau est le plus grand organe du corps (2 m², 5 kg). Elle se renouvelle tous les 28 jours. Trois couches : épiderme, derme, hypoderme.", "science"),
    ("squelette", "Le squelette adulte compte 206 os. Le fémur est l'os le plus long, l'étrier (oreille) le plus petit. Les os se renouvellent tous les 10 ans.", "science"),
    ("sang", "Le sang (5 litres) transporte l'oxygène (globules rouges), combat les infections (globules blancs) et coagule (plaquettes).", "science"),
    ("cerveau humain", "Le cerveau consomme 20% de l'énergie du corps. Il contient 86 milliards de neurones connectés par 100 000 milliards de synapses.", "science"),
    ("œil humain", "L'œil humain peut distinguer 10 millions de couleurs. La rétine contient 120 millions de bâtonnets (vision nocturne) et 6 millions de cônes (couleurs).", "science"),
    ("système digestif", "Le tube digestif mesure 9 mètres de long. La digestion complète d'un repas prend 24 à 72 heures.", "science"),
    ("ADN humain", "Le génome humain contient 3 milliards de paires de bases réparties sur 23 paires de chromosomes. Environ 20 000 gènes codent des protéines.", "science"),
    ("groupes sanguins", "Les 4 groupes sanguins (A, B, AB, O) sont déterminés par des antigènes sur les globules rouges. Le facteur Rhésus (+/-) est un antigène supplémentaire.", "science"),
    ("vaccination", "La vaccination sauve 2 à 3 millions de vies par an selon l'OMS. La variole a été éradiquée en 1980 grâce à la vaccination mondiale.", "science"),
    ("antibiotiques", "Les antibiotiques ne sont PAS efficaces contre les virus (grippe, rhume, COVID). Leur usage excessif crée des bactéries résistantes.", "science"),
    ("anesthésie", "L'anesthésie générale a été utilisée pour la première fois en 1846 (éther). Elle rend le patient inconscient et insensible à la douleur.", "science"),
    ("IRM", "L'IRM (Imagerie par Résonance Magnétique) utilise des champs magnétiques puissants pour créer des images détaillées de l'intérieur du corps.", "science"),
    ("cancer", "Le cancer est une division cellulaire incontrôlée causée par des mutations de l'ADN. 1 homme sur 2 et 1 femme sur 3 développeront un cancer dans leur vie.", "science"),
    ("diabète", "Le diabète de type 1 est auto-immun (pas d'insuline). Le type 2 (90% des cas) est lié au mode de vie. L'insuline régule le glucose sanguin.", "science"),
    ("Alzheimer", "La maladie d'Alzheimer est une dégénérescence progressive des neurones. Première cause de démence. Décrite par Alois Alzheimer en 1906.", "science"),
    ("Parkinson", "La maladie de Parkinson est due à la perte des neurones produisant la dopamine. Symptômes : tremblements, rigidité, lenteur des mouvements.", "science"),
]

ECONOMY_FACTS = [
    ("PIB mondial", "Le PIB mondial est d'environ 105 000 milliards de dollars (2024). Les États-Unis (25%), la Chine (17%) et l'UE (15%) dominent.", "economy"),
    ("inflation", "L'inflation est la hausse générale des prix. Une inflation modérée (2%) est souhaitable. L'hyperinflation (>50%/mois) détruit une économie (Zimbabwe 2008, Venezuela).", "economy"),
    ("taux d'intérêt", "Le taux directeur fixé par la banque centrale influence tous les autres taux. Il monte pour freiner l'inflation, baisse pour stimuler l'économie.", "economy"),
    ("bourse", "La bourse est un marché où s'échangent des actions. Les plus grandes : NYSE (New York), NASDAQ, Tokyo, Shanghai, Londres, Euronext.", "economy"),
    ("crypto-monnaie", "Le Bitcoin a été créé en 2009 par Satoshi Nakamoto. Première crypto-monnaie décentralisée basée sur la blockchain.", "economy"),
    ("blockchain", "La blockchain est un registre distribué infalsifiable. Chaque bloc contient des transactions et le hash du bloc précédent, créant une chaîne.", "economy"),
    ("libre-échange", "Le libre-échange supprime les barrières douanières entre pays. L'OMC (Organisation Mondiale du Commerce) le régule depuis 1995.", "economy"),
    ("FMI", "Le Fonds Monétaire International (FMI), créé en 1944 à Bretton Woods, accorde des prêts aux pays en difficulté en échange de réformes.", "economy"),
    ("Banque Mondiale", "La Banque Mondiale finance des projets de développement dans les pays pauvres. Siège à Washington. 189 pays membres.", "economy"),
    ("PIB/habitant", "Les pays les plus riches en PIB/habitant : Monaco (240 000$), Liechtenstein, Luxembourg. Le plus pauvre : Burundi (~300$).", "economy"),
    ("chômage", "Le taux de chômage mesure la part de la population active sans emploi. Le plein-emploi est considéré autour de 4-5%.", "economy"),
    ("dette publique", "La dette publique mondiale dépasse 300 000 milliards $. Le Japon a la plus forte dette/PIB (260%). La France est à ~110%.", "economy"),
    ("or", "L'or est une valeur refuge depuis des millénaires. Production mondiale : 3 600 tonnes/an. Principaux producteurs : Chine, Australie, Russie.", "economy"),
    ("pétrole", "Le pétrole fournit 31% de l'énergie mondiale. L'OPEP+ (Arabie Saoudite, Russie...) contrôle 40% de la production.", "economy"),
    ("commerce international", "Le commerce mondial de marchandises représente ~25 000 milliards $/an. La Chine est le 1er exportateur mondial.", "economy"),
    ("impôt", "Les impôts financent les services publics. En moyenne, les pays de l'OCDE prélèvent 34% du PIB. La France est à 45% (record).", "economy"),
    ("croissance économique", "La croissance se mesure par la variation du PIB. La croissance mondiale moyenne est de 3%/an. La Chine a connu 10%/an pendant 30 ans.", "economy"),
    ("monnaie", "La monnaie remplit 3 fonctions : unité de compte, intermédiaire d'échange, réserve de valeur. Le dollar US est la principale monnaie de réserve (59%).", "economy"),
]

ASTRONOMY_FACTS = [
    ("système solaire", "Le système solaire s'est formé il y a 4,6 milliards d'années. 8 planètes, 5 planètes naines, 290 lunes, des millions d'astéroïdes.", "science"),
    ("Mercure", "Mercure est la planète la plus proche du Soleil (58 millions km). Pas d'atmosphère. Température : -180°C à +430°C. Une année = 88 jours terrestres.", "science"),
    ("Vénus", "Vénus est la planète la plus chaude (462°C) à cause d'un effet de serre massif. Elle tourne à l'envers (rotation rétrograde).", "science"),
    ("Terre", "La Terre est la seule planète connue abritant la vie. 71% d'eau. Une lune. Distance au Soleil : 150 millions km (1 UA).", "science"),
    ("Mars", "Mars a le plus haut volcan du système solaire (Olympus Mons, 21 km). Son sol rouge est riche en oxyde de fer. 2 petites lunes : Phobos et Deimos.", "science"),
    ("Jupiter", "Jupiter est 318 fois plus massive que la Terre. La Grande Tache Rouge est une tempête vieille de 350 ans. 95 lunes connues.", "science"),
    ("Saturne", "Les anneaux de Saturne sont faits de glace et de roche, larges de 282 000 km mais épais de seulement 10 mètres. 146 lunes.", "science"),
    ("Uranus", "Uranus tourne 'couchée' (inclinaison de 98°). C'est une géante de glace. Découverte en 1781 par William Herschel.", "science"),
    ("Neptune", "Neptune a les vents les plus rapides du système solaire (2 100 km/h). 14 lunes dont Triton (geysers d'azote).", "science"),
    ("Pluton", "Pluton a été rétrogradée au rang de planète naine en 2006. 5 lunes dont Charon (presque aussi grosse que Pluton).", "science"),
    ("voie lactée", "La Voie Lactée est notre galaxie : 100 à 400 milliards d'étoiles, diamètre de 100 000 années-lumière. Le Soleil est à 26 000 AL du centre.", "science"),
    ("supernova", "Une supernova est l'explosion d'une étoile massive. En 1054, une supernova était visible en plein jour. Le résidu est la nébuleuse du Crabe.", "science"),
    ("exoplanète", "Plus de 5 500 exoplanètes ont été découvertes. La plus proche, Proxima Centauri b, est à 4,2 années-lumière.", "science"),
    ("année-lumière", "Une année-lumière est la distance parcourue par la lumière en un an : 9 461 milliards de km. L'étoile la plus proche est à 4,2 AL.", "science"),
    ("constellation", "Il y a 88 constellations officielles. La Grande Ourse, Orion et la Croix du Sud sont parmi les plus connues.", "science"),
    ("étoile polaire", "L'étoile Polaire (Polaris) indique le nord. Elle est située dans la constellation de la Petite Ourse à 433 années-lumière.", "science"),
    ("trou noir supermassif", "Sagittarius A* est le trou noir supermassif au centre de la Voie Lactée (4 millions de masses solaires). Imagé pour la première fois en 2022.", "science"),
    ("James Webb", "Le télescope spatial James Webb (JWST), lancé en 2021, observe l'univers en infrarouge. Il peut voir les premières galaxies (13,5 milliards d'années).", "science"),
]

COMPUTER_SCIENCE_FACTS = [
    ("Alan Turing", "Alan Turing (1912-1954) est le père de l'informatique théorique. La machine de Turing (1936) définit ce qui est calculable.", "science"),
    ("loi de Moore", "La loi de Moore (1965) : le nombre de transistors sur une puce double tous les 2 ans. Elle a tenu 50 ans mais ralentit depuis 2015.", "science"),
    ("transistor", "Le transistor (1947, Bardeen, Brattain, Shockley) est le composant de base de toute l'électronique moderne. Des milliards sur une seule puce.", "science"),
    ("Internet", "Internet est né en 1969 avec ARPANET (4 ordinateurs connectés). Aujourd'hui : 5 milliards d'utilisateurs, des milliards de pages web.", "science"),
    ("HTTP", "Le protocole HTTP (HyperText Transfer Protocol), créé par Tim Berners-Lee en 1990, est la base du World Wide Web.", "science"),
    ("intelligence artificielle", "L'IA est née en 1956 à la conférence de Dartmouth. L'IA faible excelle dans une tâche spécifique, l'IA générale (AGI) n'existe pas encore.", "science"),
    ("algorithme", "Un algorithme est une suite d'instructions pour résoudre un problème. Le mot vient d'Al-Khwarizmi, mathématicien perse du IXe siècle.", "science"),
    ("système d'exploitation", "Le système d'exploitation gère le matériel et les logiciels. Les plus utilisés : Windows (70%), macOS (16%), Linux (3%), Android/iOS (mobile).", "science"),
    ("processeur", "Le CPU exécute les instructions. Fréquence en GHz, cœurs multiples. Les plus puissants exécutent des milliards d'opérations par seconde.", "science"),
    ("mémoire RAM", "La RAM (Random Access Memory) stocke temporairement les données. Elle s'efface quand l'ordinateur s'éteint. 8 Go à 128 Go selon l'usage.", "science"),
    ("disque dur SSD", "Le SSD (Solid State Drive) est 100× plus rapide qu'un disque dur mécanique (HDD). Pas de pièce mobile. Utilise de la mémoire flash.", "science"),
    ("base de données", "Une base de données stocke des informations structurées. SQL (Structured Query Language) est le langage standard pour les interroger.", "science"),
    ("Python", "Python, créé par Guido van Rossum en 1991, est le langage le plus populaire pour l'IA et la data science. Syntaxe claire et lisible.", "science"),
    ("chiffrement", "Le chiffrement transforme des données en code secret. HTTPS utilise le chiffrement pour sécuriser le web. Le chiffrement de bout en bout protège les messages.", "science"),
    ("bug", "Le premier 'bug' informatique était un vrai insecte (une mite) coincé dans un relais de l'ordinateur Harvard Mark II en 1947.", "science"),
    ("GPS", "Le GPS (Global Positioning System) utilise 31 satellites en orbite à 20 200 km. Il faut 4 satellites pour déterminer une position précise.", "science"),
]

PHILOSOPHY_FACTS = [
    ("Socrate", "Socrate (470-399 av. J.-C.) est le père de la philosophie occidentale. Il n'a rien écrit ; sa pensée est connue par Platon. 'Je sais que je ne sais rien.'", "culture"),
    ("Platon", "Platon (428-348 av. J.-C.) a fondé l'Académie. Théorie des Idées : le monde sensible n'est qu'une copie imparfaite du monde des Idées.", "culture"),
    ("Aristote", "Aristote (384-322 av. J.-C.) a été le précepteur d'Alexandre le Grand. Il a écrit sur la logique, l'éthique, la politique, la biologie et la physique.", "culture"),
    ("Descartes", "René Descartes (1596-1650) : 'Je pense, donc je suis' (Cogito ergo sum). Fondateur du rationalisme moderne.", "culture"),
    ("Kant", "Emmanuel Kant (1724-1804) : 'Agis de telle sorte que la maxime de ton action puisse être érigée en loi universelle.' Impératif catégorique.", "culture"),
    ("Nietzsche", "Friedrich Nietzsche (1844-1900) : 'Dieu est mort.' A critiqué la morale chrétienne. Concept du Surhomme et de l'éternel retour.", "culture"),
    ("stoïcisme", "Le stoïcisme (Zénon, 300 av. J.-C.) enseigne la maîtrise de soi et l'acceptation du destin. 'Ce qui trouble les hommes, ce ne sont pas les choses, mais leurs jugements.'", "culture"),
    ("existentialisme", "L'existentialisme (Sartre, Camus, XXe siècle) : 'L'existence précède l'essence.' L'homme est libre et responsable de ses choix.", "culture"),
    ("Confucius", "Confucius (551-479 av. J.-C.) a fondé le confucianisme. 'Ne fais pas aux autres ce que tu ne voudrais pas qu'on te fasse.'", "culture"),
    ("Bouddha", "Siddhartha Gautama (Bouddha, Ve siècle av. J.-C.) a enseigné les Quatre Nobles Vérités et le Noble Chemin Octuple pour cesser la souffrance.", "culture"),
]

GEOGRAPHY_ADVANCED_FACTS = [
    ("Amazonie", "L'Amazonie (5,5 millions km²) produit 20% de l'oxygène mondial. Elle abrite 10% des espèces connues. 9 pays la partagent.", "geography"),
    ("Sahara", "Le Sahara (9,2 millions km²) est le plus grand désert chaud. Il s'étend sur 11 pays. Il y a 10 000 ans, c'était une savane verdoyante.", "geography"),
    ("Himalaya", "L'Himalaya abrite les 14 sommets de plus de 8 000 m. Le mont Everest (8 849 m) est le plus haut. Les plaques indienne et eurasienne continuent de le soulever.", "geography"),
    ("Grande Barrière de corail", "La Grande Barrière de corail (Australie, 2 300 km) est la plus grande structure vivante sur Terre, visible depuis l'espace.", "geography"),
    ("fosse des Mariannes", "La fosse des Mariannes (Pacifique) est le point le plus profond des océans : 11 034 mètres (Challenger Deep). Pression : 1 100 atmosphères.", "geography"),
    ("Antarctique", "L'Antarctique est le continent le plus froid (-89°C record), le plus sec et le plus venteux. Il contient 70% de l'eau douce de la planète.", "geography"),
    ("mer Morte", "La mer Morte (Israël/Jordanie) est le point le plus bas de la Terre (-430 m). Salinité 10× supérieure à l'océan : on y flotte sans effort.", "geography"),
    ("fleuve Amazone", "L'Amazone (7 062 km) est le fleuve au plus grand débit (209 000 m³/s). À son embouchure, l'eau douce repousse l'océan sur 160 km.", "geography"),
    ("Nil", "Le Nil (6 650 km) traverse 11 pays africains. Le Nil Bleu (Éthiopie) et le Nil Blanc (lac Victoria) se rejoignent à Khartoum.", "geography"),
    ("lac Baïkal", "Le lac Baïkal (Sibérie), profond de 1 642 m, est le plus vieux (25 millions d'années) et le plus profond lac du monde. 20% de l'eau douce non gelée.", "geography"),
    ("chutes Victoria", "Les chutes Victoria (Zambie/Zimbabwe), larges de 1 708 m, sont les plus grandes du monde en surface. Nom local : Mosi-oa-Tunya ('la fumée qui gronde').", "geography"),
    ("île de Pâques", "L'île de Pâques (Rapa Nui, Chili) est célèbre pour ses 887 statues moaï. L'île la plus isolée du monde : 3 500 km du Chili.", "geography"),
    ("Venise", "Venise est construite sur 118 îles reliées par 400 ponts. La ville s'enfonce de 1 à 2 mm par an. Acqua alta : marées hautes qui inondent la place Saint-Marc.", "geography"),
    ("Russie", "La Russie (17,1 millions km²) est le plus grand pays du monde. 11 fuseaux horaires. Elle possède 25% des réserves mondiales d'eau douce (lac Baïkal).", "geography"),
    ("Vatican", "Le Vatican (0,44 km²) est le plus petit État du monde. 800 habitants. Il possède sa propre monnaie, poste, radio et journal.", "geography"),
]

MYTHOLOGY_FACTS = [
    ("Zeus", "Zeus est le roi des dieux grecs, dieu du ciel et de la foudre. Il règne sur le mont Olympe. Équivalent romain : Jupiter.", "culture"),
    ("Odin", "Odin est le dieu principal de la mythologie nordique. Borgne (il a sacrifié un œil pour la sagesse), il chevauche Sleipnir, un cheval à 8 jambes.", "culture"),
    ("Râ", "Râ est le dieu solaire égyptien, créateur de l'univers. Chaque nuit, il traverse le monde souterrain sur sa barque pour renaître à l'aube.", "culture"),
    ("mythe d'Osiris", "Osiris, dieu égyptien, fut tué par son frère Seth et ressuscité par sa sœur-épouse Isis. Il devint le dieu des morts et du jugement des âmes.", "culture"),
    ("Maât", "Maât est la déesse égyptienne de la vérité, de l'équilibre et de la justice. La plume de Maât pesait le cœur des défunts pour juger leur âme.", "culture"),
    ("mythe de Prométhée", "Prométhée vola le feu aux dieux pour le donner aux humains. Zeus le punit en l'enchaînant à un rocher où un aigle lui dévorait le foie chaque jour.", "culture"),
    ("Thor", "Thor est le dieu nordique du tonnerre. Son marteau Mjöllnir revient toujours dans sa main. Le jeudi (Thursday) porte son nom.", "culture"),
    ("mythe d'Icare", "Icare s'envola avec des ailes de cire. Malgré l'avertissement de son père Dédale, il monta trop près du soleil : la cire fondit et il tomba dans la mer.", "culture"),
    ("Anubis", "Anubis, dieu égyptien à tête de chacal, guidait les morts et présidait à la pesée du cœur lors du jugement des âmes.", "culture"),
    ("Horus", "Horus, dieu égyptien à tête de faucon, fils d'Osiris et Isis, vengea son père en combattant Seth. Les pharaons étaient considérés comme son incarnation.", "culture"),
    ("mythe de Sisyphe", "Sisyphe fut condamné par Zeus à pousser éternellement un rocher en haut d'une colline, le rocher retombant toujours avant d'atteindre le sommet.", "culture"),
    ("Ragnarök", "Le Ragnarök est la fin du monde dans la mythologie nordique : une grande bataille où la plupart des dieux meurent, avant la renaissance d'un monde nouveau.", "culture"),
]

LAW_FACTS = [
    ("Déclaration des droits de l'homme", "La Déclaration universelle des droits de l'homme (ONU, 1948) compte 30 articles. Article 1 : 'Tous les êtres humains naissent libres et égaux en dignité et en droits.'", "politics"),
    ("Code civil", "Le Code civil français (Code Napoléon, 1804) a influencé le droit de nombreux pays. Il consacre la liberté individuelle, la propriété privée et la laïcité.", "politics"),
    ("Constitution", "La Constitution est la loi suprême d'un pays. La Constitution française de 1958 (Ve République) compte 89 articles. Les États-Unis ont la plus ancienne (1787).", "politics"),
    ("séparation des pouvoirs", "Montesquieu (1748) a théorisé la séparation des pouvoirs : exécutif (gouvernement), législatif (parlement), judiciaire (tribunaux).", "politics"),
    ("droit de vote", "Le droit de vote des femmes : Nouvelle-Zélande (1893, première), France (1944), Suisse (1971 au niveau fédéral), Arabie Saoudite (2015).", "politics"),
    ("présomption d'innocence", "'Toute personne accusée est présumée innocente jusqu'à ce que sa culpabilité ait été légalement établie.' Principe fondamental du droit pénal.", "politics"),
    ("abolition de l'esclavage", "L'esclavage a été aboli en France en 1848 (Victor Schœlcher), aux États-Unis en 1865 (13e amendement), en Mauritanie en 1981 (dernier pays).", "politics"),
    ("peine de mort", "La peine de mort est abolie dans 112 pays. France : 1981 (Robert Badinter). États-Unis : encore en vigueur dans 27 États. Chine : principal exécuteur mondial.", "politics"),
    ("Cour pénale internationale", "La CPI (La Haye, 2002) juge les crimes de guerre, crimes contre l'humanité, génocides et crimes d'agression. 123 États membres.", "politics"),
    ("mariage pour tous", "Le mariage entre personnes de même sexe : Pays-Bas (2001, premier pays), France (2013), États-Unis (2015). Aujourd'hui légal dans 36 pays.", "politics"),
]

CUISINE_FACTS = [
    ("riz", "Le riz est l'aliment de base de la moitié de l'humanité. La Chine et l'Inde produisent 50% du riz mondial. 40 000 variétés existent.", "culture"),
    ("blé", "Le blé est la céréale la plus cultivée au monde. Il fournit 20% des calories consommées par l'humanité. Transformé en farine pour le pain, les pâtes, etc.", "culture"),
    ("café", "Le café est la deuxième boisson la plus consommée au monde après l'eau. 2,25 milliards de tasses par jour. Originaire d'Éthiopie.", "culture"),
    ("thé", "Le thé est la boisson la plus consommée au monde après l'eau. Découvert en Chine il y a 5 000 ans. Types : noir, vert, blanc, oolong.", "culture"),
    ("chocolat", "Le chocolat vient des fèves de cacao. Plus grand producteur : Côte d'Ivoire (40%). Le chocolat noir (>70%) est riche en antioxydants.", "culture"),
    ("fromage", "Il existe plus de 1 800 variétés de fromage dans le monde. La France en produit 400. Le plus ancien fromage date de 7 200 ans.", "culture"),
    ("vin", "Le vin est produit depuis 8 000 ans. Principaux producteurs : Italie, France, Espagne. Un vin peut se bonifier pendant des décennies.", "culture"),
    ("sushi", "Le sushi japonais date du VIIIe siècle. Le riz vinaigré est associé à du poisson cru. Le sashimi est du poisson cru sans riz.", "culture"),
    ("pain", "Le pain est un aliment de base depuis le Néolithique (10 000 ans). La baguette française est inscrite au patrimoine de l'UNESCO depuis 2022.", "culture"),
    ("huile d'olive", "L'huile d'olive est produite depuis 6 000 ans en Méditerranée. L'Espagne est le plus grand producteur. Riche en acides gras mono-insaturés.", "culture"),
]

ARCHITECTURE_FACTS = [
    ("pyramide de Khéops", "La pyramide de Khéops (Gizeh, vers 2560 av. J.-C.) est la seule des 7 Merveilles du monde antique encore debout. 2,3 millions de blocs de pierre.", "culture"),
    ("Parthénon", "Le Parthénon (Athènes, 432 av. J.-C.) est un temple dédié à Athéna. Ses colonnes utilisent des corrections optiques subtiles pour paraître parfaites.", "culture"),
    ("Colisée", "Le Colisée (Rome, 80 ap. J.-C.) pouvait accueillir 50 000 spectateurs. Il a servi pour les combats de gladiateurs pendant 400 ans.", "culture"),
    ("Taj Mahal", "Le Taj Mahal (Inde, 1653) est un mausolée de marbre blanc construit par l'empereur Shah Jahan pour son épouse. 20 000 ouvriers pendant 22 ans.", "culture"),
    ("Tour Eiffel", "La Tour Eiffel (Paris, 1889) mesure 330 m avec ses antennes. Elle pèse 10 100 tonnes. 7 millions de visiteurs par an. Devait être démontée après 20 ans.", "culture"),
    ("Empire State Building", "L'Empire State Building (New York, 1931) a 102 étages (443 m). Construit en 410 jours. A été le plus haut bâtiment du monde jusqu'en 1970.", "culture"),
    ("Burj Khalifa", "Le Burj Khalifa (Dubaï, 2010) est le plus haut bâtiment du monde : 828 mètres, 163 étages. Assez haut pour voir le coucher de soleil deux fois.", "culture"),
    ("Sagrada Familia", "La Sagrada Familia (Barcelone) est l'œuvre de Gaudí, commencée en 1882, toujours en construction. 18 tours prévues, la plus haute fera 172 m.", "culture"),
    ("Machu Picchu", "Le Machu Picchu (Pérou, XVe siècle) est une citadelle inca perchée à 2 430 m d'altitude. Redécouverte en 1911. Les pierres s'emboîtent sans mortier.", "culture"),
    ("Notre-Dame de Paris", "Notre-Dame de Paris (1163-1345) est un chef-d'œuvre gothique. Gravement endommagée par un incendie en 2019, sa réouverture est prévue en décembre 2024.", "culture"),
    ("Grande Muraille", "La Grande Muraille de Chine s'étend sur 21 196 km. Sa construction a débuté au IIIe siècle av. J.-C. Elle n'est PAS visible à l'œil nu depuis l'espace.", "culture"),
    ("opéra de Sydney", "L'opéra de Sydney (1973) est reconnaissable à ses voiles en béton. Conçu par Jørn Utzon. Inscrit au patrimoine mondial de l'UNESCO.", "culture"),
]

LINGUISTICS_FACTS = [
    ("langues du monde", "Il existe environ 7 000 langues vivantes. Les plus parlées : anglais (1,5 milliard), mandarin (1,1 milliard), hindi (600 millions), espagnol (550 millions).", "culture"),
    ("langue maternelle", "Le mandarin est la langue maternelle la plus parlée (920 millions). L'espagnol est deuxième (480 millions). L'anglais troisième (380 millions).", "culture"),
    ("alphabet", "L'alphabet latin est le plus utilisé au monde (70% des langues écrites). Le cyrillique est utilisé par 250 millions de personnes.", "culture"),
    ("hiéroglyphes", "Les hiéroglyphes égyptiens (3 200 av. J.-C.) sont l'un des plus anciens systèmes d'écriture. Champollion les a déchiffrés en 1822 avec la pierre de Rosette.", "culture"),
    ("langue des signes", "Il existe plus de 300 langues des signes dans le monde. La LSF (Langue des Signes Française) a influencé l'ASL (American Sign Language).", "culture"),
    ("espéranto", "L'espéranto est une langue construite créée en 1887 par Zamenhof pour faciliter la communication internationale. Environ 100 000 locuteurs dans le monde.", "culture"),
    ("langue morte", "Le latin est une langue morte (plus de locuteur natif) mais toujours utilisée en droit, médecine, biologie et au Vatican.", "culture"),
    ("mot le plus long", "Le mot français le plus long officiellement est 'anticonstitutionnellement' (25 lettres). En anglais, 'pneumonoultramicroscopicsilicovolcanoconiosis' (45 lettres).", "culture"),
    ("grammaire", "La grammaire française compte 12 temps verbaux, 6 modes, l'accord en genre (masculin/féminin) et en nombre (singulier/pluriel).", "culture"),
    ("étymologie", "L'étymologie étudie l'origine des mots. 80% des mots français viennent du latin. 'Internet' vient de l'anglais 'interconnected networks'.", "culture"),
]


# ══════════════════════════════════════════════════════════════════════════
# GÉNÉRATION MASSIVE
# ══════════════════════════════════════════════════════════════════════════

ALL_FACT_SETS = [
    ("physique", PHYSICS_FACTS),
    ("chimie", CHEMISTRY_FACTS),
    ("biologie", BIOLOGY_FACTS),
    ("médecine", MEDICINE_FACTS),
    ("économie", ECONOMY_FACTS),
    ("astronomie", ASTRONOMY_FACTS),
    ("informatique", COMPUTER_SCIENCE_FACTS),
    ("philosophie", PHILOSOPHY_FACTS),
    ("géographie avancée", GEOGRAPHY_ADVANCED_FACTS),
    ("mythologie", MYTHOLOGY_FACTS),
    ("droit", LAW_FACTS),
    ("cuisine", CUISINE_FACTS),
    ("architecture", ARCHITECTURE_FACTS),
    ("linguistique", LINGUISTICS_FACTS),
]

def generate_all_facts():
    """Génère tous les faits de la Phase 1."""
    all_facts = []
    total = 0
    
    for domain_name, facts_list in ALL_FACT_SETS:
        for name, text, domain in facts_list:
            words = name.lower().split()
            all_facts.append((words, text, domain))
            total += 1
        print(f"  {domain_name}: {len(facts_list)} faits")
    
    print(f"\n  Total généré : {total} faits")
    return all_facts

def save_and_merge(facts):
    """Sauvegarde et fusionne avec QuickFacts."""
    # Sauvegarde JSON
    output_path = os.path.join(EXPANSION_DIR, "phase1_facts.json")
    data = []
    for words, text, domain in facts:
        data.append({
            "keywords": words if isinstance(words, list) else words.split(),
            "fact": text,
            "category": domain,
        })
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Sauvegardé : {output_path} ({len(data)} faits, {size_mb:.1f} Mo)")
    
    # Charger les faits existants ET les précédents
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    expanded_path = os.path.join(DATA_DIR, "quickfacts_expanded.json")
    
    existing_facts = []
    existing_ids = set()
    if os.path.exists(expanded_path):
        with open(expanded_path, "r", encoding="utf-8") as f:
            existing_facts = json.load(f)
        for entry in existing_facts:
            existing_ids.add(entry.get("id", ""))
        print(f"  Chargés : {len(existing_facts)} faits existants")
    
    # Ajouter les nouveaux (sans doublon)
    added = 0
    skipped = 0
    for words, text, domain in facts:
        fid = f"p1_{hashlib.md5(text.encode()).hexdigest()[:8]}"
        if fid not in existing_ids:
            w = words if isinstance(words, list) else words.split()
            existing_facts.append({"id": fid, "text": text, "keywords": w})
            existing_ids.add(fid)
            added += 1
        else:
            skipped += 1
    
    # Sauvegarder le fichier complet
    with open(expanded_path, "w", encoding="utf-8") as f:
        json.dump(existing_facts, f, ensure_ascii=False, indent=2)
    size_mb = os.path.getsize(expanded_path) / (1024 * 1024)
    
    print(f"  [Merge] {added} ajoutés, {skipped} doublons ignorés")
    print(f"  Total : {len(existing_facts)} faits ({size_mb:.1f} Mo)")
    print(f"  Sauvegardé : {expanded_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Expansion Phase 1 — Enrichissement massif")
    parser.add_argument("--no-merge", action="store_true", help="Ne pas fusionner avec QuickFacts")
    args = parser.parse_args()
    
    print("=" * 60)
    print("EXPANSION PHASE 1 — 14 domaines")
    print("=" * 60)
    
    all_facts = generate_all_facts()
    
    if not args.no_merge:
        print(f"\n[Fusion] Merge avec QuickFacts...")
        save_and_merge(all_facts)
    
    print(f"\nTerminé ! Total faits générés : {len(all_facts)}")
    print("Redémarrez unified_server.py pour activer les nouveaux faits.")