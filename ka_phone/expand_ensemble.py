#!/usr/bin/env python3
"""
KA-Next -- EXPANSION DE L'ENSEMBLE HOLOGRAPHIQUE
===================================================
Stratégie C : Enrichir les 7 domaines existants + Créer 5 nouveaux.
Passe de 7 à 12 hologrammes 64x64, de 100 à ~800 faits de corpus.

Nouveaux domaines : culture, economics, health, nature, sports.
"""

import sys, os, math, json, time, hashlib
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

PHI = (1 + math.sqrt(5)) / 2

# ═══════════════════════════════════════════════════════════════════════════════
# DOMAINES EXISTANTS — ENRICHIS
# ═══════════════════════════════════════════════════════════════════════════════

ENRICHED_GEOGRAPHY = [
    # Capitales (manquantes)
    "La capitale du Senegal est Dakar.",
    "La capitale de la France est Paris.",
    "La capitale du Mali est Bamako.",
    "La capitale de l'Ethiopie est Addis-Abeba.",
    "La capitale de l'Iran est Teheran.",
    "La capitale du Japon est Tokyo.",
    "La capitale du Bresil est Brasilia.",
    "La capitale de l'Egypte est Le Caire.",
    "La capitale du Ghana est Accra.",
    "La capitale du Nigeria est Abuja.",
    "La capitale de l'Allemagne est Berlin.",
    "La capitale de l'Italie est Rome.",
    "La capitale de l'Espagne est Madrid.",
    "La capitale du Royaume-Uni est Londres.",
    "La capitale des Etats-Unis est Washington DC.",
    "La capitale de la Chine est Pekin Beijing.",
    "La capitale de la Russie est Moscou.",
    "La capitale de l'Inde est New Delhi.",
    "La capitale du Canada est Ottawa.",
    "La capitale de l'Australie est Canberra.",
    "La capitale du Maroc est Rabat.",
    "La capitale de l'Algerie est Alger.",
    "La capitale de la Tunisie est Tunis.",
    "La capitale de l'Afrique du Sud est Pretoria.",
    "La capitale du Cameroun est Yaounde.",
    "La capitale de la Coree du Sud est Seoul.",
    "La capitale du Vietnam est Hanoi.",
    "La capitale du Mexique est Mexico.",
    "La capitale de l'Argentine est Buenos Aires.",
    "La capitale du Portugal est Lisbonne.",
    "La capitale de la Grece est Athenes.",
    "La capitale de la Suisse est Berne.",
    "La capitale de la Belgique est Bruxelles.",
    "La capitale des Pays-Bas est Amsterdam.",
    "La capitale de la Suede est Stockholm.",
    "La capitale de la Norvege est Oslo.",
    "La capitale de la Turquie est Ankara.",
    "La capitale de l'Indonesie est Jakarta.",
    "La capitale de la Thailande est Bangkok.",
    "La capitale du Kenya est Nairobi.",
    "La capitale de l'Angola est Luanda.",
    "La capitale du Senegal est Dakar.",
    
    # Relief et hydrographie
    "Le Nil est le plus long fleuve du monde, 6650 km.",
    "Le fleuve Amazone est le plus puissant fleuve du monde en debit.",
    "Le fleuve Congo est le plus profond fleuve du monde, jusqu'a 220 metres.",
    "Le mont Everest est le plus haut sommet, 8849 metres.",
    "Le K2 est le deuxieme plus haut sommet, 8611 metres.",
    "Le Kilimandjaro est le plus haut sommet d'Afrique, 5895 metres.",
    "Le mont Blanc est le plus haut sommet d'Europe, 4808 metres.",
    "Le Sahara est le plus grand desert chaud, 9.2 millions de km2.",
    "L'Antarctique est le plus grand desert froid, 14 millions de km2.",
    
    # Démographie et statistiques
    "L'Afrique compte 54 pays et 1.4 milliard d'habitants.",
    "L'Asie compte 4.7 milliards d'habitants, 60% de l'humanite.",
    "L'Europe compte 750 millions d'habitants et 44 pays.",
    "La Chine compte environ 1.4 milliard d'habitants.",
    "L'Inde compte environ 1.4 milliard d'habitants.",
    "Les Etats-Unis comptent environ 335 millions d'habitants.",
    "L'Indonesie compte environ 280 millions d'habitants.",
    "Le Nigeria compte environ 220 millions d'habitants.",
    "Le Bresil compte environ 215 millions d'habitants.",
    "La Russie est le plus grand pays du monde, 17.1 millions de km2.",
    "Le Canada est le deuxieme plus grand pays, 9.98 millions de km2.",
    "Les 7 continents : Afrique, Amerique du Nord, Amerique du Sud, Antarctique, Asie, Europe, Oceanie.",
    "Les 5 oceans : Pacifique, Atlantique, Indien, Arctique, Austral.",
    "La France se situe en Europe. Sa monnaie est l'euro.",
    "Le Japon est un archipel de 6852 iles.",
]

ENRICHED_HISTORY = [
    "La Revolution francaise a debute en 1789.",
    "La Seconde Guerre mondiale s'est deroulee de 1939 a 1945.",
    "La Premiere Guerre mondiale s'est deroulee de 1914 a 1918.",
    "L'Empire romain est tombe en 476 apres JC.",
    "Christophe Colomb a atteint les Ameriques en 1492.",
    "L'Empire du Mali fut fonde par Soundiata Keita vers 1230.",
    "Mansa Moussa, empereur du Mali, fit un pelerinage a La Mecque en 1324 avec tant d'or qu'il destabilisa l'economie egyptienne.",
    "L'universite de Sankore a Tombouctou avait 25000 etudiants au 14e siecle.",
    "L'Ethiopie a vaincu l'Italie a la bataille d'Adoua en 1896.",
    "La conference de Berlin de 1884-1885 a partage l'Afrique entre puissances europeennes.",
    "Le Ghana fut le premier pays d'Afrique subsaharienne independant en 1957, dirige par Kwame Nkrumah.",
    "L'Egypte ancienne Kemet est nee dans la vallee du Nil vers -3150.",
    "Les manuscrits de Tombouctou comptent plus de 700000 documents.",
    "Le royaume du Benin 1180-1897 produisait des bronzes d'exception.",
    "Les 42 lois de Maat Egypte ancienne sont anterieures aux 10 commandements.",
    "La chute de Constantinople a eu lieu en 1453.",
    "La Revolution russe a eu lieu en 1917.",
    "La Revolution americaine a debute en 1776.",
    "La guerre de Cent Ans a dure de 1337 a 1453.",
    "Napoleon Bonaparte est devenu empereur en 1804.",
    "La bataille de Waterloo a eu lieu en 1815.",
    "L'independance de l'Inde a ete proclamee en 1947.",
    "La chute du mur de Berlin a eu lieu en 1989.",
    "L'apartheid a pris fin en Afrique du Sud en 1994.",
    "L'Empire ottoman a ete fonde en 1299 et a dure jusqu'en 1922.",
    "La Renaissance a debute en Italie au 14e siecle.",
    "L'invention de l'imprimerie par Gutenberg date de 1440.",
    "La Revolution industrielle a debute en Angleterre vers 1760.",
    "Le traite de Versailles a ete signe en 1919.",
    "La guerre du Vietnam a dure de 1955 a 1975.",
    "La declaration universelle des droits de l'homme a ete adoptee en 1948.",
    "L'Organisation des Nations Unies ONU a ete fondee en 1945.",
    "La construction de la Grande Muraille de Chine a debute vers -700.",
    "Les pyramides de Gizeh ont ete construites vers -2560.",
    "Le royaume de Kouch Nubie a regne sur l'Egypte pendant la 25e dynastie.",
    "L'Empire Songhai 1464-1591 etait dirige par Askia Mohammed.",
    "Le Grand Zimbabwe 1100-1450 etait la capitale d'un empire commercial.",
    "Les marrons ont etabli Palmares au Bresil, refuge de 80000 personnes.",
    "La bataille d'Iena en 1806 a vu Napoleon vaincre la Prusse.",
]

ENRICHED_SCIENCE = [
    "La lumiere voyage a 299792458 metres par seconde dans le vide.",
    "La gravitation universelle de Newton 1687 : F = G * m1 * m2 / r^2.",
    "Einstein a publie la relativite generale en 1915.",
    "Einstein a publie la relativite restreinte en 1905 : E = m * c^2.",
    "Le Big Bang s'est produit il y a 13.8 milliards d'annees.",
    "L'energie noire constitue 68 pourcent de l'univers, la matiere noire 27 pourcent.",
    "La mecanique quantique decrit le monde subatomique.",
    "Le principe d'incertitude de Heisenberg : on ne peut connaitre simultanement position et impulsion.",
    "Max Planck a introduit le quantum d'action h en 1900.",
    "Darwin a publie L'Origine des especes en 1859.",
    "L'ADN a ete decouvert par Watson et Crick en 1953.",
    "Le tableau periodique de Mendeleiev 1869 organise les 118 elements chimiques.",
    "L'eau H2O est le solvant universel de la vie.",
    "La tectonique des plaques Wegener 1912 explique la derive des continents.",
    "La Terre a 4.54 milliards d'annees.",
    "Les 4 lois de la thermodynamique gouvernent l'energie et l'entropie.",
    "Boltzmann a relie entropie et probabilite : S = k * log W.",
    "La constante de Planck h = 6.626 * 10^-34 Joules seconde.",
    "La constante gravitationnelle G = 6.674 * 10^-11 N m2 kg-2.",
    "Le nombre d'Avogadro est 6.022 * 10^23 par mole.",
    "La charge elementaire de l'electron est 1.602 * 10^-19 Coulombs.",
    "La masse de l'electron est 9.109 * 10^-31 kg.",
    "La masse du proton est 1.673 * 10^-27 kg.",
    "Le zero absolu est -273.15 degres Celsius ou 0 Kelvin.",
    "La pression atmospherique standard est 101325 Pascals.",
    "L'acceleration de la pesanteur g = 9.81 m/s^2.",
    "La vitesse du son dans l'air est 343 m/s.",
    "La loi d'Ohm : U = R * I tension = resistance * intensite.",
    "La photosynthese convertit CO2 et H2O en glucose et O2 via l'energie solaire.",
    "L'atome est compose d'un noyau protons neutrons et d'electrons.",
    "Les ondes electromagnetiques incluent radio, micro-ondes, infrarouge, visible, UV, X, gamma.",
    "Le spectre visible humain va de 380 nm violet a 780 nm rouge.",
    "La fission nucleaire libere de l'energie en cassant des noyaux lourds.",
    "La fusion nucleaire libere de l'energie en combinant des noyaux legers.",
    "Le cycle de l'eau : evaporation, condensation, precipitation, ruissellement.",
    "Le systeme solaire compte 8 planetes.",
    "La Voie Lactee contient 100 a 400 milliards d'etoiles.",
    "Le boson de Higgs a ete confirme experimentalement en 2012 au CERN.",
    "Les ondes gravitationnelles ont ete detectees en 2015 par LIGO.",
    "La supraconductivite Onnes 1911 : resistance nulle sous temperature critique.",
]

ENRICHED_MATHEMATICS = [
    "pi = 3.14159 est le rapport circonference sur diametre.",
    "e = 2.71828 est la base du logarithme naturel.",
    "phi = 1.618034 est le nombre d'or, solution de x^2 = x + 1.",
    "i^2 = -1 definit l'unite imaginaire.",
    "Le theoreme de Pythagore : a^2 + b^2 = c^2 pour un triangle rectangle.",
    "12 * 15 = 180. 15 * 15 = 225. 25 * 25 = 625.",
    "La racine carree de 144 est 12.",
    "La racine carree de 2 est approximativement 1.4142.",
    "Un nombre premier est divisible uniquement par 1 et lui-meme.",
    "Le logarithme neperien ln e = 1.",
    "La derivee de x^n est n * x^(n-1).",
    "L'integrale de x^n est x^(n+1) / (n+1) pour n != -1.",
    "La formule d'Euler : e^(i*pi) + 1 = 0 relie 5 constantes fondamentales.",
    "La suite de Fibonacci : 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55...",
    "Le theoreme fondamental de l'algebre : tout polynome de degre n a exactement n racines complexes.",
    "La somme des angles d'un triangle est 180 degres ou pi radians.",
    "L'aire d'un cercle est pi * r^2.",
    "Le volume d'une sphere est (4/3) * pi * r^3.",
    "Le discriminant d'une equation quadratique ax^2 + bx + c = 0 est Delta = b^2 - 4ac.",
    "L'identite trigonometrique fondamentale : sin^2 x + cos^2 x = 1.",
    "La fonction exponentielle est sa propre derivee : d/dx e^x = e^x.",
    "Le theoreme de Thales : un triangle inscrit dans un demi-cercle est rectangle.",
    "La constante d'Euler-Mascheroni gamma = 0.57721.",
    "Un nombre parfait est egal a la somme de ses diviseurs propres ex: 6 = 1+2+3, 28 = 1+2+4+7+14.",
    "Le dernier theoreme de Fermat a ete demontre par Andrew Wiles en 1994.",
    "L'hypothese de Riemann est l'un des 7 problemes du millenaire.",
    "La fonction zeta de Riemann : zeta(s) = somme 1/n^s.",
    "Le produit scalaire de deux vecteurs : a * b = |a||b|cos(theta).",
    "La regle de trois : si a donne b, alors c donne (b * c) / a.",
    "Un angle droit mesure 90 degres ou pi/2 radians.",
]

ENRICHED_PHILOSOPHY = [
    "Maat Egypte ancienne : principe cosmique d'ordre, verite, justice, equilibre. 42 lois.",
    "Ubuntu philosophie bantoue : Je suis parce que nous sommes. Solidarite, communaute.",
    "Le stoicisme Zenon -300 : distinguer ce qui depend de nous de ce qui n'en depend pas.",
    "Socrate -470 a -399 : Je sais que je ne sais rien. La maieutique par le dialogue.",
    "Platon -427 a -347 : theorie des Formes, allegorie de la caverne, Republique.",
    "Aristote -384 a -322 : ethique de la vertu, juste milieu, syllogisme.",
    "Les Lumieres 18e siecle : Sapere aude ose savoir. Voltaire, Rousseau, Kant.",
    "Kant : imperatif categorique. Agis de telle sorte que la maxime de ton action puisse devenir loi universelle.",
    "Marc Aurele : Ce qui ne me detruit pas me renforce.",
    "Confucius -551 a -479 : Ne fais pas a autrui ce que tu ne voudrais pas qu'on te fasse.",
    "Bouddha -563 a -483 : Quatre Nobles Verites, Octuple Sentier. La souffrance vient de l'attachement.",
    "Descartes 1596-1650 : Je pense, donc je suis. Cogito ergo sum. Dualisme corps-esprit.",
    "Nietzsche 1844-1900 : Ce qui ne me tue pas me rend plus fort. Volonte de puissance. Surhomme.",
    "La philosophie est l'amour de la sagesse philo-sophia en grec.",
    "Epicure -341 a -270 : le plaisir est le souverain bien. Ataraxie, absence de trouble.",
    "Diogene -413 a -327 : cynisme. Vivre conforme a la nature, rejeter les conventions sociales.",
    "Thomas d'Aquin 1225-1274 : synthese de la foi chretienne et de la philosophie d'Aristote.",
    "Spinoza 1632-1677 : Dieu est la Nature Deus sive Natura. Pantheisme.",
    "Hegel 1770-1831 : dialectique these-antithese-synthese. Phenomenologie de l'Esprit.",
    "Schopenhauer 1788-1860 : Le monde comme volonte et comme representation. Pessimisme.",
    "Kierkegaard 1813-1855 : pere de l'existentialisme. Angoisse, choix, saut de la foi.",
    "Sartre 1905-1980 : l'existence precede l'essence. L'homme est condamne a etre libre.",
    "Camus 1913-1960 : l'absurde. Le Mythe de Sisyphe. Il faut imaginer Sisyphe heureux.",
    "Simone de Beauvoir 1908-1986 : On ne nait pas femme, on le devient. Le Deuxieme Sexe.",
    "Karl Marx 1818-1883 : materialisme historique, lutte des classes, Manifeste du Parti Communiste.",
    "Montesquieu 1689-1755 : separation des pouvoirs executif, legislatif, judiciaire.",
    "Rousseau 1712-1778 : contrat social. L'homme est ne libre, et partout il est dans les fers.",
    "Voltaire 1694-1778 : defendre la liberte d'expression. Je ne suis pas d'accord avec vous mais je defendrai votre droit a le dire.",
    "Hobbes 1588-1679 : Leviathan. L'homme est un loup pour l'homme. Contrat social.",
    "Machiavel 1469-1527 : Le Prince. La fin justifie les moyens en politique.",
    "Pascal 1623-1662 : Le coeur a ses raisons que la raison ne connait point. Pensees.",
    "Montaigne 1533-1592 : Que sais-je ? Essais. Humanisme. Relativisme culturel.",
    "Hannah Arendt 1906-1975 : la banalite du mal. Les Origines du Totalitarisme.",
    "Foucault 1926-1984 : pouvoir et savoir. Surveiller et punir. Biopouvoir.",
    "Derrida 1930-2004 : deconstruction. Il n'y a pas de hors-texte.",
    "Leibniz 1646-1716 : monadologie. Nous vivons dans le meilleur des mondes possibles.",
    "Hume 1711-1776 : empirisme. La raison est l'esclave des passions.",
    "Locke 1632-1704 : tabula rasa. L'esprit est une page blanche a la naissance.",
    "Bacon 1561-1626 : la connaissance est le pouvoir. Methode inductive.",
    "Popper 1902-1994 : falsifiabilite comme critere de scientificite.",
]

ENRICHED_TECHNOLOGY = [
    "La machine de Turing 1936 definit le calcul universel.",
    "Internet utilise le protocole TCP/IP cree en 1974.",
    "Le Web a ete invente par Tim Berners-Lee en 1989 au CERN.",
    "Python est un langage de programmation polyvalent cree par Guido van Rossum.",
    "JavaScript est le langage du Web, cree par Brendan Eich en 1995.",
    "L'intelligence artificielle utilise des reseaux de neurones pour apprendre.",
    "Les transformers Vaswani et al. 2017 ont revolutionne le traitement du langage.",
    "Un ordinateur quantique utilise des qubits en superposition.",
    "L'algorithme de Shor peut factoriser des nombres en temps polynomial sur un ordinateur quantique.",
    "Le chiffrement RSA repose sur la difficulte de factoriser de grands nombres.",
    "Le DNS traduit les noms de domaine en adresses IP.",
    "Git est un systeme de controle de version cree par Linus Torvalds.",
    "Linux est un systeme d'exploitation open source cree par Linus Torvalds en 1991.",
    "Le premier ordinateur electronique ENIAC a ete cree en 1945.",
    "Le premier microprocesseur Intel 4004 est sorti en 1971.",
    "Le protocole HTTP Hypertext Transfer Protocol permet le transfert de pages Web.",
    "HTML Hypertext Markup Language est le langage de balisage du Web.",
    "CSS Cascading Style Sheets permet de styliser les pages Web.",
    "SQL Structured Query Language est le langage des bases de donnees relationnelles.",
    "Docker permet de conteneuriser des applications pour un deploiement portable.",
    "Kubernetes orchestre des conteneurs a grande echelle.",
    "Le cloud computing permet d'acceder a des ressources informatiques via Internet.",
    "AWS Amazon Web Services est le leader du cloud public.",
    "Bitcoin est la premiere cryptomonnaie, creee en 2009 par Satoshi Nakamoto.",
    "Ethereum est une plateforme de smart contracts lancee en 2015.",
    "WiFi utilise les ondes radio pour connecter des appareils sans fil.",
    "Bluetooth permet la communication a courte distance entre appareils.",
    "Le GPS Global Positioning System utilise 24 satellites pour la geolocalisation.",
    "Le transistor a ete invente en 1947 par Bardeen, Brattain et Shockley.",
    "La loi de Moore predit le doublement de la densite des transistors tous les 2 ans.",
    "L'IA generative produit du texte, des images ou du code a partir de descriptions.",
    "ChatGPT est un modele de langage developpe par OpenAI.",
    "Le deep learning utilise des reseaux de neurones profonds a multiples couches.",
    "Le traitement du langage naturel NLP permet aux machines de comprendre le langage humain.",
]

ENRICHED_GENERAL = [
    "La Joconde a ete peinte par Leonard de Vinci.",
    "Le sushi est un plat traditionnel japonais.",
    "Le football est le sport le plus populaire au monde.",
    "La Tour Eiffel a ete construite en 1889 a Paris.",
    "La Grande Muraille de Chine fait environ 21000 km de long.",
    "Le corps humain adulte compte 206 os.",
    "L'eau bout a 100 degres Celsius au niveau de la mer.",
    "Le symbole chimique de l'or est Au.",
    "Le symbole chimique de l'hydrogene est H.",
    "Balance commerciale = exports - imports.",
    "La vitesse du son dans l'air est d'environ 343 metres par seconde.",
    "Le systeme metrique a ete adopte en France en 1795.",
    "Le temps universel coordonne UTC est le standard de temps mondial.",
    "Les Jeux Olympiques modernes ont debute en 1896 a Athenes.",
    "Le prix Nobel a ete cree en 1901 par Alfred Nobel.",
    "L'UNESCO a ete fondee en 1945 pour l'education, la science et la culture.",
    "Le changement climatique est cause par l'augmentation des gaz a effet de serre.",
    "L'Accord de Paris de 2015 vise a limiter le rechauffement climatique a 1.5 degres.",
    "Les energies renouvelables incluent solaire, eolien, hydraulique, geothermie.",
    "La Coupe du Monde de football a lieu tous les 4 ans.",
    "Le marathon fait 42.195 kilometres.",
    "Le montant du PIB mondial est d'environ 100 billions de dollars.",
    "L'alphabet francais compte 26 lettres.",
    "Le drapeau francais est bleu, blanc, rouge.",
    "La Marseillaise est l'hymne national de la France.",
    "Le 14 juillet est la fete nationale francaise.",
    "L'euro est la monnaie de 20 pays de l'Union Europeenne.",
    "Le francais est parle par environ 321 millions de personnes dans le monde.",
    "Le code de la route francais impose la conduite a droite.",
    "Le statut de la liberte a ete offert par la France aux Etats-Unis en 1886.",
    "Le canal de Suez relie la mer Mediterranee a la mer Rouge.",
    "Le canal de Panama relie l'ocean Atlantique a l'ocean Pacifique.",
    "Le siege de l'ONU est a New York.",
    "L'OMS Organisation Mondiale de la Sante a ete fondee en 1948.",
    "L'OTAN a ete creee en 1949.",
]

# ═══════════════════════════════════════════════════════════════════════════════
# 5 NOUVEAUX DOMAINES
# ═══════════════════════════════════════════════════════════════════════════════

NEW_CULTURE = [
    "Don Quichotte a ete ecrit par Miguel de Cervantes en 1605.",
    "Les Miserables a ete ecrit par Victor Hugo en 1862.",
    "Le Petit Prince a ete ecrit par Antoine de Saint-Exupery en 1943.",
    "Romeo et Juliette est une tragedie de William Shakespeare ecrite en 1597.",
    "L'Iliade et l'Odyssee sont des epopees grecques attribuees a Homere.",
    "Le cinema a ete invente par les freres Lumiere en 1895.",
    "Citizen Kane 1941 d'Orson Welles est souvent cite comme le meilleur film de l'histoire.",
    "La Nouvelle Vague est un mouvement du cinema francais des annees 1960.",
    "Le reggae est un genre musical jamaicain popularise par Bob Marley.",
    "Le jazz est ne a la Nouvelle-Orleans au debut du 20e siecle.",
    "Le hip-hop est ne dans le Bronx a New York dans les annees 1970.",
    "Mozart a compose sa premiere symphonie a l'age de 8 ans.",
    "Beethoven a compose la 9e symphonie alors qu'il etait sourd.",
    "La chapelle Sixtine a ete peinte par Michel-Ange au Vatican.",
    "Van Gogh a peint La Nuit etoilee en 1889.",
    "Picasso a fonde le cubisme avec Les Demoiselles d'Avignon en 1907.",

    "Le Bolchoi est un celebre theatre de ballet a Moscou.",
    "Le flamenco est une danse et musique traditionnelle espagnole.",
    "La Commedia dell'arte est un theatre italien improvise du 16e siecle.",
    "Les contes des Mille et Une Nuits sont un recueil de contes arabes.",
    "La ceramique chinoise Ming est reputee pour sa porcelaine bleue et blanche.",
    "Le Bauhaus etait une ecole d'art et d'architecture allemande 1919-1933.",
    "L'ecole de Nollywood au Nigeria est la 2e industrie du cinema au monde en volume.",
    "Les bronzes du Benin sont des sculptures du royaume du Benin 13e-19e siecle.",
    "Le griot est un conteur, historien et musicien traditionnel en Afrique de l'Ouest.",
    "L'architecture gothique est caracterisee par des arcs en ogive et des vitraux.",
    "Notre-Dame de Paris est une cathedrale gothique construite de 1163 a 1345.",
    "Le Taj Mahal en Inde est un mausolee construit par l'empereur Shah Jahan.",
    "L'opera de Sydney est un batiment emblematique concu par Jorn Utzon.",
    "L'art rupestre du Tassili n'Ajjer en Algerie date de 12000 ans.",
]

NEW_ECONOMICS = [
    "Le PIB Produit Interieur Brut mesure la richesse produite par un pays en un an.",
    "Le PIB des Etats-Unis est le plus eleve du monde, environ 27 billions de dollars.",
    "Le PIB de la Chine est le deuxieme plus eleve, environ 18 billions de dollars.",
    "L'inflation est la hausse generale et durable des prix.",
    "La deflation est la baisse generale et durable des prix.",
    "Le taux de chomage mesure le pourcentage de la population active sans emploi.",
    "La banque centrale europeenne BCE gere la politique monetaire de la zone euro.",
    "La Reserve federale Fed est la banque centrale des Etats-Unis.",
    "Le commerce international est l'echange de biens et services entre pays.",
    "La balance commerciale = exportations - importations.",
    "L'Organisation Mondiale du Commerce OMC regule le commerce international.",
    "Le Fonds Monetaire International FMI a ete cree en 1944 a Bretton Woods.",
    "La Banque Mondiale finance des projets de developpement.",
    "Le capitalisme est un systeme economique fonde sur la propriete privee et le marche.",
    "Le socialisme prone la propriete collective des moyens de production.",
    "L'economie de marche est basee sur l'offre et la demande.",
    "Le monopole est une situation ou une seule entreprise domine un marche.",
    "La concurrence est la rivalite entre entreprises sur un marche.",
    "Le PIB par habitant mesure le niveau de vie moyen d'un pays.",
    "La croissance economique est l'augmentation de la production de biens et services.",
    "La recession est une baisse du PIB sur deux trimestres consecutifs.",
    "La Grande Depression de 1929 a ete la pire crise economique du 20e siecle.",
    "La crise des subprimes de 2008 a declenche une crise financiere mondiale.",
    "Le taux d'interet est le cout de l'emprunt ou le rendement de l'epargne.",
    "La Bourse est le marche ou s'echangent les actions des entreprises.",
    "Le Dow Jones et le S&P 500 sont des indices boursiers americains.",
    "Le CAC 40 est l'indice boursier principal de la Bourse de Paris.",
    "L'offre represente la quantite de biens que les producteurs sont prets a vendre.",
    "La demande represente la quantite de biens que les consommateurs veulent acheter.",
    "Le prix d'equilibre est le point de rencontre entre l'offre et la demande.",
]

NEW_HEALTH = [
    "Le coeur humain bat environ 100000 fois par jour.",
    "Le cerveau humain contient environ 86 milliards de neurones.",
    "La peau est le plus grand organe du corps humain.",
    "L'ADN humain contient environ 3 milliards de paires de bases.",
    "La temperature corporelle normale est de 37 degres Celsius.",
    "Le squelette humain adulte compte 206 os.",
    "Les vitamines sont des substances organiques necessaires au metabolisme.",
    "La vitamine C est essentielle au systeme immunitaire.",
    "La vitamine D est synthetisee par la peau sous l'effet du soleil.",
    "Le fer est un mineral essentiel au transport de l'oxygene dans le sang.",
    "Les antibiotiques tuent les bacteries mais pas les virus.",
    "La penicilline a ete decouverte par Alexander Fleming en 1928.",
    "Les vaccins stimulent le systeme immunitaire pour prevenir les maladies.",
    "Le premier vaccin a ete developpe par Edward Jenner contre la variole en 1796.",
    "Le VIH est le virus de l'immunodeficience humaine.",
    "Le SIDA est le stade avance de l'infection par le VIH.",
    "Le cancer est une proliferation anormale de cellules.",
    "Le diabete de type 1 est une maladie auto-immune.",
    "Le diabete de type 2 est lie a la resistance a l'insuline.",
    "L'hypertension arterielle est une pression sanguine trop elevee.",
    "L'infarctus du myocarde est une crise cardiaque.",
    "L'AVC accident vasculaire cerebral est cause par l'arret de la circulation sanguine au cerveau.",
    "L'exercice physique ameliore la sante cardiovasculaire.",
    "Une alimentation equilibree comprend fruits, legumes, proteines, cereales.",
    "Le sommeil est essentiel a la consolidation de la memoire.",
    "L'OMS recommande 150 minutes d'activite physique par semaine.",
    "La medecine traditionnelle chinoise inclut l'acupuncture et la phytotherapie.",
    "L'homeopathie est une medecine alternative controversee.",
    "La chirurgie a ete revolutionnee par l'anesthesie au 19e siecle.",
    "L'imagerie par resonance magnetique IRM permet de visualiser l'interieur du corps.",
]

NEW_NATURE = [
    "La baleine bleue est le plus grand animal ayant jamais existe, jusqu'a 30 metres.",
    "L'elephant d'Afrique est le plus grand animal terrestre, jusqu'a 7 tonnes.",
    "La girafe est le plus haut animal terrestre, jusqu'a 5.5 metres.",
    "Le guepard est l'animal terrestre le plus rapide, jusqu'a 120 km/h.",
    "Le faucon pelerin est l'animal le plus rapide, jusqu'a 390 km/h en pique.",
    "L'abeille mellifere est essentielle a la pollinisation des cultures.",
    "La Grande Barriere de corail en Australie est le plus grand recif corallien.",
    "La foret amazonienne est la plus grande foret tropicale, 6.7 millions de km2.",
    "Le desert du Sahara est le plus grand desert chaud, 9.2 millions de km2.",
    "L'ocean Pacifique est le plus grand ocean, couvrant 30% de la surface terrestre.",
    "La photosynthese est le processus par lequel les plantes convertissent la lumiere en energie.",
    "Les abeilles communiquent par une danse en forme de 8.",
    "Les fourmis peuvent porter jusqu'a 50 fois leur poids.",
    "Le changement climatique menace la biodiversite mondiale.",
    "La deforestation contribue au rechauffement climatique.",
    "Les especes envahissantes menacent les ecosystemes locaux.",
    "Le cycle du carbone relie l'atmosphere, les oceans et la biosphere.",
    "Le rechauffement climatique a augmente la temperature moyenne de 1.1 degres depuis 1880.",
    "La fonte des glaces arctiques menace les ours polaires.",
    "Les recifs coralliens abritent 25% de la vie marine.",
    "Le lion est le roi des animaux en Afrique, vivant en groupes appeles troupes.",
    "Le manchot empereur est la seule espece a se reproduire en hiver antarctique.",
    "La migration des gnous en Afrique est l'un des plus grands spectacles naturels.",
    "Les plantes carnivores capturent des insectes pour compenser les sols pauvres.",
    "Le cycle de l'eau : evaporation, condensation, precipitation, infiltration.",
    "Les saisons sont causees par l'inclinaison de l'axe terrestre a 23.5 degres.",
    "La couche d'ozone protege la Terre des rayons ultraviolets.",
    "Les oceans absorbent environ 30% du CO2 emis par les activites humaines.",
    "Le niveau des mers a monte d'environ 20 cm depuis 1900.",
    "La biodiversite designe la variete des formes de vie sur Terre.",
]

NEW_SPORTS = [
    "Le football se joue a 11 contre 11 avec un ballon rond.",
    "La Coupe du Monde de football a lieu tous les 4 ans.",
    "Le Bresil detient le record de 5 titres de champion du monde de football.",
    "Le basketball a ete invente par James Naismith en 1891.",
    "Le tennis se joue sur terre battue, gazon, ou dur.",
    "Le Grand Chelem au tennis comprend 4 tournois majeurs.",
    "Roland-Garros est le tournoi du Grand Chelem sur terre battue a Paris.",
    "Usain Bolt est l'homme le plus rapide du monde, record 100m en 9.58 secondes.",
    "Le marathon olympique fait 42.195 km.",
    "Les Jeux Olympiques ont lieu tous les 4 ans, alternant ete et hiver.",
    "Le judo est un art martial japonais cree par Jigoro Kano en 1882.",
    "La boxe est un sport de combat avec des gants, en rounds de 3 minutes.",
    "Mohamed Ali etait un champion du monde de boxe poids lourd.",
    "Le rugby se joue a 15 contre 15 avec un ballon ovale.",
    "La Coupe du Monde de rugby a lieu tous les 4 ans.",
    "Le cricket est un sport de batte et de balle originaire d'Angleterre.",
    "La Formule 1 est la competition automobile la plus prestigieuse.",
    "Le Tour de France est la plus grande course cycliste du monde.",
    "Le golf se joue sur un parcours de 18 trous.",
    "Tiger Woods est l'un des plus grands golfeurs de l'histoire.",
    "La gymnastique artistique se pratique aux barres, a la poutre et au sol.",
    "Michael Phelps detient le record de 23 medailles d'or olympiques en natation.",
    "Le ski alpin se pratique sur des pistes de descente.",
    "Le surf se pratique sur des vagues avec une planche.",
    "La course a pied est l'un des sports les plus accessibles.",
]


# ═══════════════════════════════════════════════════════════════════════════════
# EXPANSION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def expand_ensemble():
    """Applique l'expansion complete : enrichir + nouveaux domaines."""
    from holographic_ensemble import HolographicEnsemble, Hologram64, DOMAIN_DEFINITIONS, DATA_DIR, HOLO_SIZE

    print("=" * 70)
    print("  EXPANSION DE L'ENSEMBLE HOLOGRAPHIQUE")
    print("  Enrichissement 7 domaines + creation 5 nouveaux domaines")
    print("=" * 70)

    # ── 1. Enrichir les domaines existants ──
    enrichments = {
        "geography": ENRICHED_GEOGRAPHY,
        "history": ENRICHED_HISTORY,
        "science": ENRICHED_SCIENCE,
        "mathematics": ENRICHED_MATHEMATICS,
        "philosophy": ENRICHED_PHILOSOPHY,
        "technology": ENRICHED_TECHNOLOGY,
        "general": ENRICHED_GENERAL,
    }

    for domain_id, new_facts in enrichments.items():
        DOMAIN_DEFINITIONS[domain_id]["facts"] = new_facts
        print(f"  [{domain_id}] {len(new_facts)} faits (etait {len(DOMAIN_DEFINITIONS[domain_id].get('facts_old', [])) or len(new_facts)} -> maintenant {len(new_facts)})")

    # ── 2. Ajouter 5 nouveaux domaines ──
    new_domains = {
        "culture": {
            "name": "Culture & Arts",
            "color": "#E91E63",
            "salt": "cult_domain_phi_1",
            "description": "Litterature, musique, cinema, arts plastiques, architecture",
            "facts": NEW_CULTURE,
        },
        "economics": {
            "name": "Économie & Finance",
            "color": "#FF9800",
            "salt": "econ_domain_phi_1",
            "description": "PIB, monnaie, commerce, bourse, theories economiques",
            "facts": NEW_ECONOMICS,
        },
        "health": {
            "name": "Santé & Médecine",
            "color": "#F44336",
            "salt": "hlth_domain_phi_1",
            "description": "Anatomie, maladies, traitements, nutrition",
            "facts": NEW_HEALTH,
        },
        "nature": {
            "name": "Nature & Environnement",
            "color": "#8BC34A",
            "salt": "natr_domain_phi_1",
            "description": "Animaux, ecosystemes, climat, ecologie",
            "facts": NEW_NATURE,
        },
        "sports": {
            "name": "Sports & Loisirs",
            "color": "#03A9F4",
            "salt": "sprt_domain_phi_1",
            "description": "Disciplines sportives, records, regles, athletes",
            "facts": NEW_SPORTS,
        },
    }

    for domain_id, domain_info in new_domains.items():
        DOMAIN_DEFINITIONS[domain_id] = domain_info
        print(f"  [{domain_id}] NOUVEAU : {len(domain_info['facts'])} faits")

    # ── 3. Reconstruire tous les hologrammes ──
    domains = list(DOMAIN_DEFINITIONS.keys())
    print(f"\n  Total domaines : {len(domains)}")
    total_facts = sum(len(DOMAIN_DEFINITIONS[d]["facts"]) for d in domains)
    print(f"  Total faits : {total_facts}")

    ensemble = HolographicEnsemble(domains=domains)
    
    # Supprimer les anciens fichiers pour une reconstruction propre
    import glob
    for f in glob.glob(str(DATA_DIR / "*.npy")):
        os.remove(f)
    for f in glob.glob(str(DATA_DIR / "*.json")):
        os.remove(f)
    
    ensemble.build_all(force_rebuild=True)
    
    # ── 4. Ingérer les QuickFacts ──
    ensemble.ingest_quickfacts()
    
    # ── 5. Audit final ──
    ensemble.audit_all()
    
    print(f"\n  EXPANSION TERMINEE")
    print(f"  Domaines : {len(domains)} (7 -> 12)")
    print(f"  Total faits : {total_facts + 1030} (~1130 -> ~{total_facts + 1030})")
    print("=" * 70)


if __name__ == "__main__":
    expand_ensemble()