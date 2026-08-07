"""
KB Extension Massive — Géographie + Histoire + Culture
========================================================
Génère 800+ faits pour la couverture généraliste LM Arena.
Sans LLM — données factuelles standards.

Usage:
    from kb_massive_extension import extend_all
    extend_all(model)
"""

import math

# ═══════════════════════════════════════════════════════════════════
# 1. CAPITALES DU MONDE (200 pays)
# ═══════════════════════════════════════════════════════════════════

CAPITALES = [
    # Afrique
    ("alger", "est la capitale de", "l Algerie", "GEOGRAPHIE"),
    ("luanda", "est la capitale de", "l Angola", "GEOGRAPHIE"),
    ("porto-novo", "est la capitale du", "Benin", "GEOGRAPHIE"),
    ("gaborone", "est la capitale du", "Botswana", "GEOGRAPHIE"),
    ("ouagadougou", "est la capitale du", "Burkina Faso", "GEOGRAPHIE"),
    ("bujumbura", "est la capitale du", "Burundi", "GEOGRAPHIE"),
    ("yaounde", "est la capitale du", "Cameroun", "GEOGRAPHIE"),
    ("praia", "est la capitale du", "Cap-Vert", "GEOGRAPHIE"),
    ("bangui", "est la capitale de la", "Republique centrafricaine", "GEOGRAPHIE"),
    ("ndjamena", "est la capitale du", "Tchad", "GEOGRAPHIE"),
    ("moroni", "est la capitale des", "Comores", "GEOGRAPHIE"),
    ("kinshasa", "est la capitale de la", "RDC", "GEOGRAPHIE"),
    ("brazzaville", "est la capitale du", "Congo", "GEOGRAPHIE"),
    ("yamoussoukro", "est la capitale de la", "Cote d Ivoire", "GEOGRAPHIE"),
    ("djibouti", "est la capitale de", "Djibouti", "GEOGRAPHIE"),
    ("le caire", "est la capitale de", "l Egypte", "GEOGRAPHIE"),
    ("malabo", "est la capitale de la", "Guinee equatoriale", "GEOGRAPHIE"),
    ("asmara", "est la capitale de", "l Erythree", "GEOGRAPHIE"),
    ("addis-abeba", "est la capitale de", "l Ethiopie", "GEOGRAPHIE"),
    ("libreville", "est la capitale du", "Gabon", "GEOGRAPHIE"),
    ("banjul", "est la capitale de la", "Gambie", "GEOGRAPHIE"),
    ("accra", "est la capitale du", "Ghana", "GEOGRAPHIE"),
    ("conakry", "est la capitale de la", "Guinee", "GEOGRAPHIE"),
    ("bissau", "est la capitale de la", "Guinee-Bissau", "GEOGRAPHIE"),
    ("nairobi", "est la capitale du", "Kenya", "GEOGRAPHIE"),
    ("maseru", "est la capitale du", "Lesotho", "GEOGRAPHIE"),
    ("monrovia", "est la capitale du", "Liberia", "GEOGRAPHIE"),
    ("tripoli", "est la capitale de la", "Libye", "GEOGRAPHIE"),
    ("antananarivo", "est la capitale de", "Madagascar", "GEOGRAPHIE"),
    ("lilongwe", "est la capitale du", "Malawi", "GEOGRAPHIE"),
    ("bamako", "est la capitale du", "Mali", "GEOGRAPHIE"),
    ("nouakchott", "est la capitale de la", "Mauritanie", "GEOGRAPHIE"),
    ("port-louis", "est la capitale de", "l ile Maurice", "GEOGRAPHIE"),
    ("rabat", "est la capitale du", "Maroc", "GEOGRAPHIE"),
    ("maputo", "est la capitale du", "Mozambique", "GEOGRAPHIE"),
    ("windhoek", "est la capitale de la", "Namibie", "GEOGRAPHIE"),
    ("niamey", "est la capitale du", "Niger", "GEOGRAPHIE"),
    ("abuja", "est la capitale du", "Nigeria", "GEOGRAPHIE"),
    ("kigali", "est la capitale du", "Rwanda", "GEOGRAPHIE"),
    ("dakar", "est la capitale du", "Senegal", "GEOGRAPHIE"),
    ("freetown", "est la capitale de la", "Sierra Leone", "GEOGRAPHIE"),
    ("mogadiscio", "est la capitale de la", "Somalie", "GEOGRAPHIE"),
    ("pretoria", "est la capitale de", "l Afrique du Sud", "GEOGRAPHIE"),
    ("juba", "est la capitale du", "Soudan du Sud", "GEOGRAPHIE"),
    ("khartoum", "est la capitale du", "Soudan", "GEOGRAPHIE"),
    ("mbabane", "est la capitale de", "l Eswatini", "GEOGRAPHIE"),
    ("dodoma", "est la capitale de la", "Tanzanie", "GEOGRAPHIE"),
    ("lome", "est la capitale du", "Togo", "GEOGRAPHIE"),
    ("tunis", "est la capitale de la", "Tunisie", "GEOGRAPHIE"),
    ("kampala", "est la capitale de", "l Ouganda", "GEOGRAPHIE"),
    ("lusaka", "est la capitale de la", "Zambie", "GEOGRAPHIE"),
    ("harare", "est la capitale du", "Zimbabwe", "GEOGRAPHIE"),
    
    # Amériques
    ("ottawa", "est la capitale du", "Canada", "GEOGRAPHIE"),
    ("washington", "est la capitale des", "Etats-Unis", "GEOGRAPHIE"),
    ("mexico", "est la capitale du", "Mexique", "GEOGRAPHIE"),
    ("guatemala", "est la capitale du", "Guatemala", "GEOGRAPHIE"),
    ("tegucigalpa", "est la capitale du", "Honduras", "GEOGRAPHIE"),
    ("san salvador", "est la capitale du", "Salvador", "GEOGRAPHIE"),
    ("managua", "est la capitale du", "Nicaragua", "GEOGRAPHIE"),
    ("san jose", "est la capitale du", "Costa Rica", "GEOGRAPHIE"),
    ("panama", "est la capitale du", "Panama", "GEOGRAPHIE"),
    ("la havane", "est la capitale de", "Cuba", "GEOGRAPHIE"),
    ("port-au-prince", "est la capitale de", "Haiti", "GEOGRAPHIE"),
    ("saint-domingue", "est la capitale de la", "Republique dominicaine", "GEOGRAPHIE"),
    ("kingston", "est la capitale de la", "Jamaique", "GEOGRAPHIE"),
    ("bogota", "est la capitale de la", "Colombie", "GEOGRAPHIE"),
    ("caracas", "est la capitale du", "Venezuela", "GEOGRAPHIE"),
    ("quito", "est la capitale de", "l Equateur", "GEOGRAPHIE"),
    ("lima", "est la capitale du", "Perou", "GEOGRAPHIE"),
    ("la paz", "est la capitale de la", "Bolivie", "GEOGRAPHIE"),
    ("santiago", "est la capitale du", "Chili", "GEOGRAPHIE"),
    ("buenos aires", "est la capitale de", "l Argentine", "GEOGRAPHIE"),
    ("montevideo", "est la capitale de", "l Uruguay", "GEOGRAPHIE"),
    ("asuncion", "est la capitale du", "Paraguay", "GEOGRAPHIE"),
    ("brasilia", "est la capitale du", "Bresil", "GEOGRAPHIE"),
    
    # Asie
    ("tokyo", "est la capitale du", "Japon", "GEOGRAPHIE"),
    ("pekin", "est la capitale de la", "Chine", "GEOGRAPHIE"),
    ("seoul", "est la capitale de la", "Coree du Sud", "GEOGRAPHIE"),
    ("pyongyang", "est la capitale de la", "Coree du Nord", "GEOGRAPHIE"),
    ("hanoi", "est la capitale du", "Vietnam", "GEOGRAPHIE"),
    ("bangkok", "est la capitale de la", "Thailande", "GEOGRAPHIE"),
    ("phnom penh", "est la capitale du", "Cambodge", "GEOGRAPHIE"),
    ("vientiane", "est la capitale du", "Laos", "GEOGRAPHIE"),
    ("rangoun", "est la capitale de la", "Birmanie", "GEOGRAPHIE"),
    ("kuala lumpur", "est la capitale de la", "Malaisie", "GEOGRAPHIE"),
    ("singapour", "est la capitale de", "Singapour", "GEOGRAPHIE"),
    ("jakarta", "est la capitale de", "l Indonesie", "GEOGRAPHIE"),
    ("manille", "est la capitale des", "Philippines", "GEOGRAPHIE"),
    ("new delhi", "est la capitale de", "l Inde", "GEOGRAPHIE"),
    ("islamabad", "est la capitale du", "Pakistan", "GEOGRAPHIE"),
    ("dacca", "est la capitale du", "Bangladesh", "GEOGRAPHIE"),
    ("katmandou", "est la capitale du", "Nepal", "GEOGRAPHIE"),
    ("colombo", "est la capitale du", "Sri Lanka", "GEOGRAPHIE"),
    ("kaboul", "est la capitale de", "l Afghanistan", "GEOGRAPHIE"),
    ("teheran", "est la capitale de", "l Iran", "GEOGRAPHIE"),
    ("bagdad", "est la capitale de", "l Irak", "GEOGRAPHIE"),
    ("riyad", "est la capitale de", "l Arabie saoudite", "GEOGRAPHIE"),
    ("sanaa", "est la capitale du", "Yemen", "GEOGRAPHIE"),
    ("mascate", "est la capitale de", "l Oman", "GEOGRAPHIE"),
    ("abou dhabi", "est la capitale des", "Emirats arabes unis", "GEOGRAPHIE"),
    ("doha", "est la capitale du", "Qatar", "GEOGRAPHIE"),
    ("koweit", "est la capitale du", "Koweit", "GEOGRAPHIE"),
    ("manama", "est la capitale de", "Bahrein", "GEOGRAPHIE"),
    ("damas", "est la capitale de la", "Syrie", "GEOGRAPHIE"),
    ("beyrouth", "est la capitale du", "Liban", "GEOGRAPHIE"),
    ("amman", "est la capitale de la", "Jordanie", "GEOGRAPHIE"),
    ("jerusalem", "est la capitale de", "Israel", "GEOGRAPHIE"),
    ("ankara", "est la capitale de la", "Turquie", "GEOGRAPHIE"),
    ("tbilissi", "est la capitale de la", "Georgie", "GEOGRAPHIE"),
    ("bakou", "est la capitale de", "l Azerbaidjan", "GEOGRAPHIE"),
    ("erevan", "est la capitale de", "l Armenie", "GEOGRAPHIE"),
    ("oulan-bator", "est la capitale de la", "Mongolie", "GEOGRAPHIE"),
    ("taipei", "est la capitale de", "Taiwan", "GEOGRAPHIE"),
    
    # Europe
    ("paris", "est la capitale de la", "France", "GEOGRAPHIE"),
    ("londres", "est la capitale du", "Royaume-Uni", "GEOGRAPHIE"),
    ("berlin", "est la capitale de", "l Allemagne", "GEOGRAPHIE"),
    ("rome", "est la capitale de", "l Italie", "GEOGRAPHIE"),
    ("madrid", "est la capitale de", "l Espagne", "GEOGRAPHIE"),
    ("lisbonne", "est la capitale du", "Portugal", "GEOGRAPHIE"),
    ("bruxelles", "est la capitale de la", "Belgique", "GEOGRAPHIE"),
    ("amsterdam", "est la capitale des", "Pays-Bas", "GEOGRAPHIE"),
    ("vienne", "est la capitale de", "l Autriche", "GEOGRAPHIE"),
    ("berne", "est la capitale de la", "Suisse", "GEOGRAPHIE"),
    ("varsovie", "est la capitale de la", "Pologne", "GEOGRAPHIE"),
    ("prague", "est la capitale de la", "Republique tcheque", "GEOGRAPHIE"),
    ("bratislava", "est la capitale de la", "Slovaquie", "GEOGRAPHIE"),
    ("budapest", "est la capitale de la", "Hongrie", "GEOGRAPHIE"),
    ("bucarest", "est la capitale de la", "Roumanie", "GEOGRAPHIE"),
    ("sofia", "est la capitale de la", "Bulgarie", "GEOGRAPHIE"),
    ("athenes", "est la capitale de la", "Grece", "GEOGRAPHIE"),
    ("stockholm", "est la capitale de la", "Suede", "GEOGRAPHIE"),
    ("oslo", "est la capitale de la", "Norvege", "GEOGRAPHIE"),
    ("copenhague", "est la capitale du", "Danemark", "GEOGRAPHIE"),
    ("helsinki", "est la capitale de la", "Finlande", "GEOGRAPHIE"),
    ("reykjavik", "est la capitale de", "l Islande", "GEOGRAPHIE"),
    ("dublin", "est la capitale de", "l Irlande", "GEOGRAPHIE"),
    ("moscou", "est la capitale de la", "Russie", "GEOGRAPHIE"),
    ("kiev", "est la capitale de", "l Ukraine", "GEOGRAPHIE"),
    ("minsk", "est la capitale de la", "Bielorussie", "GEOGRAPHIE"),
    ("vilnius", "est la capitale de la", "Lituanie", "GEOGRAPHIE"),
    ("riga", "est la capitale de la", "Lettonie", "GEOGRAPHIE"),
    ("tallinn", "est la capitale de", "l Estonie", "GEOGRAPHIE"),
    ("zagreb", "est la capitale de la", "Croatie", "GEOGRAPHIE"),
    ("belgrade", "est la capitale de la", "Serbie", "GEOGRAPHIE"),
    ("sarajevo", "est la capitale de la", "Bosnie-Herzegovine", "GEOGRAPHIE"),
    ("ljubljana", "est la capitale de la", "Slovenie", "GEOGRAPHIE"),
    ("podgorica", "est la capitale du", "Montenegro", "GEOGRAPHIE"),
    ("skopje", "est la capitale de la", "Macedoine du Nord", "GEOGRAPHIE"),
    ("tirana", "est la capitale de", "l Albanie", "GEOGRAPHIE"),
    ("pristina", "est la capitale du", "Kosovo", "GEOGRAPHIE"),
    ("nicosie", "est la capitale de", "Chypre", "GEOGRAPHIE"),
    ("la valette", "est la capitale de", "Malte", "GEOGRAPHIE"),
    ("luxembourg", "est la capitale du", "Luxembourg", "GEOGRAPHIE"),
    ("monaco", "est la capitale de", "Monaco", "GEOGRAPHIE"),
    ("saint-marin", "est la capitale de", "Saint-Marin", "GEOGRAPHIE"),
    ("vaduz", "est la capitale du", "Liechtenstein", "GEOGRAPHIE"),
    ("andorre-la-vieille", "est la capitale de", "l Andorre", "GEOGRAPHIE"),
    
    # Océanie
    ("canberra", "est la capitale de", "l Australie", "GEOGRAPHIE"),
    ("wellington", "est la capitale de la", "Nouvelle-Zelande", "GEOGRAPHIE"),
    ("port-moresby", "est la capitale de la", "Papouasie-Nouvelle-Guinee", "GEOGRAPHIE"),
    ("suva", "est la capitale des", "Fidji", "GEOGRAPHIE"),
]

# ═══════════════════════════════════════════════════════════════════
# 2. CONTINENTS, OCEANS, FLEUVES, MONTAGNES
# ═══════════════════════════════════════════════════════════════════

GEOGRAPHIE_PHYSIQUE = [
    # Continents
    ("l Afrique", "est le", "deuxieme plus grand continent", "GEOGRAPHIE"),
    ("l Asie", "est le", "plus grand continent", "GEOGRAPHIE"),
    ("l Europe", "est le", "continent de 750 millions d habitants", "GEOGRAPHIE"),
    ("l Amerique du Nord", "comprend", "le Canada, les Etats-Unis et le Mexique", "GEOGRAPHIE"),
    ("l Amerique du Sud", "est traversee par", "la foret amazonienne", "GEOGRAPHIE"),
    ("l Oceanie", "est composee de", "l Australie et des iles du Pacifique", "GEOGRAPHIE"),
    ("l Antarctique", "est le continent", "le plus froid et le plus sec", "GEOGRAPHIE"),
    
    # Océans
    ("l ocean Pacifique", "est le plus grand", "ocean du monde", "GEOGRAPHIE"),
    ("l ocean Atlantique", "separe", "l Amerique de l Europe et l Afrique", "GEOGRAPHIE"),
    ("l ocean Indien", "est situe entre", "l Afrique, l Asie et l Australie", "GEOGRAPHIE"),
    ("l ocean Arctique", "entoure", "le pole Nord", "GEOGRAPHIE"),
    
    # Fleuves
    ("le Nil", "est le plus long", "fleuve du monde", "GEOGRAPHIE"),
    ("l Amazone", "est le fleuve", "au plus grand debit", "GEOGRAPHIE"),
    ("le Mississippi", "traverse", "les Etats-Unis du nord au sud", "GEOGRAPHIE"),
    ("le Yangtse", "est le plus long", "fleuve de Chine", "GEOGRAPHIE"),
    ("le Danube", "traverse", "10 pays europeens", "GEOGRAPHIE"),
    ("le Rhin", "traverse", "l Allemagne et les Pays-Bas", "GEOGRAPHIE"),
    ("la Seine", "traverse", "Paris", "GEOGRAPHIE"),
    ("la Tamise", "traverse", "Londres", "GEOGRAPHIE"),
    ("le Gange", "est un fleuve sacre", "en Inde", "GEOGRAPHIE"),
    ("le Tigre et l Euphrate", "ont vu naitre", "la civilisation mesopotamienne", "GEOGRAPHIE"),
    
    # Montagnes
    ("l Everest", "est le plus haut", "sommet du monde", "GEOGRAPHIE"),
    ("l Everest", "culmine a", "8848 metres", "GEOGRAPHIE"),
    ("le K2", "est le deuxieme", "plus haut sommet du monde", "GEOGRAPHIE"),
    ("le Mont Blanc", "est le plus haut", "sommet des Alpes", "GEOGRAPHIE"),
    ("les Alpes", "traversent", "la France, la Suisse, l Italie et l Autriche", "GEOGRAPHIE"),
    ("les Andes", "sont la plus longue", "chaine de montagnes du monde", "GEOGRAPHIE"),
    ("l Himalaya", "abrite les plus hauts", "sommets du monde", "GEOGRAPHIE"),
    ("le Kilimandjaro", "est le plus haut", "sommet d Afrique", "GEOGRAPHIE"),
    
    # Déserts
    ("le Sahara", "est le plus grand", "desert chaud du monde", "GEOGRAPHIE"),
    ("le Sahara", "est situe en", "Afrique du Nord", "GEOGRAPHIE"),
    ("le desert d Atacama", "est le plus", "aride du monde", "GEOGRAPHIE"),
    ("le desert de Gobi", "est situe en", "Asie centrale", "GEOGRAPHIE"),
    ("l Antarctique", "est le plus grand", "desert froid du monde", "GEOGRAPHIE"),
]

# ═══════════════════════════════════════════════════════════════════
# 3. HISTOIRE (dates clés, événements, personnages)
# ═══════════════════════════════════════════════════════════════════

HISTOIRE = [
    # Antiquité
    ("l Empire romain", "s est effondre en", "476 apres JC", "HISTOIRE"),
    ("Jules Cesar", "a ete assassine en", "44 avant JC", "HISTOIRE"),
    ("Alexandre le Grand", "est mort en", "323 avant JC", "HISTOIRE"),
    ("la Grece antique", "a invente", "la democratie", "HISTOIRE"),
    ("Athenes", "etait la cite principale", "de la Grece antique", "HISTOIRE"),
    ("Sparte", "etait une cite", "militaire grecque", "HISTOIRE"),
    ("les pyramides d Egypte", "ont ete construites", "il y a plus de 4500 ans", "HISTOIRE"),
    ("Cleopatre", "etait la derniere", "reine d Egypte", "HISTOIRE"),
    ("Socrate", "a ete condamne a mort", "en 399 avant JC", "HISTOIRE"),
    ("Platon", "a fonde", "l Academie", "HISTOIRE"),
    ("Aristote", "fut le precepteur", "d Alexandre le Grand", "HISTOIRE"),
    ("Confucius", "etait un philosophe", "chinois du 6e siecle av JC", "HISTOIRE"),
    ("Bouddha", "a vecu au", "5e siecle avant JC", "HISTOIRE"),
    ("l Empire perse", "a ete fonde par", "Cyrus le Grand", "HISTOIRE"),
    ("Carthage", "a ete detruite par", "Rome en 146 av JC", "HISTOIRE"),
    ("Hannibal", "a traverse les Alpes", "avec des elephants", "HISTOIRE"),
    
    # Moyen Âge
    ("Charlemagne", "a ete couronne empereur en", "800", "HISTOIRE"),
    ("la bataille de Hastings", "a eu lieu en", "1066", "HISTOIRE"),
    ("les croisades", "ont debute en", "1095", "HISTOIRE"),
    ("Gengis Khan", "a fonde", "l Empire mongol", "HISTOIRE"),
    ("Marco Polo", "a voyage en", "Chine au 13e siecle", "HISTOIRE"),
    ("la peste noire", "a tue", "un tiers de la population europeenne", "HISTOIRE"),
    ("Jeanne d Arc", "a ete brulee en", "1431", "HISTOIRE"),
    ("Gutenberg", "a invente l imprimerie", "vers 1440", "HISTOIRE"),
    ("la chute de Constantinople", "a eu lieu en", "1453", "HISTOIRE"),
    ("Christophe Colomb", "a atteint l Amerique en", "1492", "HISTOIRE"),
    
    # Renaissance et époque moderne
    ("Leonard de Vinci", "a peint", "la Joconde", "HISTOIRE"),
    ("Michel-Ange", "a peint", "la chapelle Sixtine", "HISTOIRE"),
    ("Copernic", "a propose", "l heliocentrisme", "HISTOIRE"),
    ("Galilee", "a perfectionne", "la lunette astronomique", "HISTOIRE"),
    ("Martin Luther", "a lance la Reforme en", "1517", "HISTOIRE"),
    ("Henri VIII", "a fonde", "l Eglise anglicane", "HISTOIRE"),
    ("Louis XIV", "etait le", "Roi Soleil", "HISTOIRE"),
    ("Louis XIV", "a regne de", "1643 a 1715", "HISTOIRE"),
    ("le chateau de Versailles", "a ete construit sous", "Louis XIV", "HISTOIRE"),
    ("la Revolution francaise", "a debute en", "1789", "HISTOIRE"),
    ("Louis XVI", "a ete execute en", "1793", "HISTOIRE"),
    ("Napoleon Bonaparte", "est devenu empereur en", "1804", "HISTOIRE"),
    ("Napoleon", "a ete vaincu a", "Waterloo en 1815", "HISTOIRE"),
    ("l independance des Etats-Unis", "a ete declaree en", "1776", "HISTOIRE"),
    ("George Washington", "fut le premier president", "des Etats-Unis", "HISTOIRE"),
    ("la guerre de Secession", "a eu lieu de", "1861 a 1865", "HISTOIRE"),
    ("Abraham Lincoln", "a aboli", "l esclavage aux Etats-Unis", "HISTOIRE"),
    
    # 20e siècle
    ("la Premiere Guerre mondiale", "a commence en", "1914", "HISTOIRE"),
    ("la Premiere Guerre mondiale", "s est terminee en", "1918", "HISTOIRE"),
    ("la Revolution russe", "a eu lieu en", "1917", "HISTOIRE"),
    ("Lenine", "a dirige", "la Revolution russe", "HISTOIRE"),
    ("la Seconde Guerre mondiale", "a commence en", "1939", "HISTOIRE"),
    ("la Seconde Guerre mondiale", "s est terminee en", "1945", "HISTOIRE"),
    ("le debarquement de Normandie", "a eu lieu le", "6 juin 1944", "HISTOIRE"),
    ("Hiroshima", "a ete frappee par une bombe atomique", "le 6 aout 1945", "HISTOIRE"),
    ("l ONU", "a ete fondee en", "1945", "HISTOIRE"),
    ("la guerre froide", "a oppose", "les Etats-Unis et l URSS", "HISTOIRE"),
    ("le mur de Berlin", "est tombe en", "1989", "HISTOIRE"),
    ("l URSS", "s est effondree en", "1991", "HISTOIRE"),
    ("l homme", "a marche sur la Lune en", "1969", "HISTOIRE"),
    ("Neil Armstrong", "fut le premier homme", "sur la Lune", "HISTOIRE"),
    ("John F Kennedy", "a ete assassine en", "1963", "HISTOIRE"),
    ("Martin Luther King", "a ete assassine en", "1968", "HISTOIRE"),
    ("Nelson Mandela", "est devenu president", "d Afrique du Sud en 1994", "HISTOIRE"),
    ("Nelson Mandela", "a passe 27 ans", "en prison", "HISTOIRE"),
    ("la decolonisation", "a marque", "les annees 1950-1970", "HISTOIRE"),
    ("l Inde", "est devenue independante en", "1947", "HISTOIRE"),
    ("Gandhi", "a mene la lutte non-violente", "pour l independance de l Inde", "HISTOIRE"),
    ("Gandhi", "a ete assassine en", "1948", "HISTOIRE"),
    ("Mao Zedong", "a fonde", "la Republique populaire de Chine en 1949", "HISTOIRE"),
    ("la guerre du Vietnam", "a dure de", "1955 a 1975", "HISTOIRE"),
    ("le traite de Maastricht", "a cree l Union europeenne", "en 1992", "HISTOIRE"),
    ("l euro", "est entre en circulation en", "2002", "HISTOIRE"),
    
    # Sciences et découvertes
    ("Isaac Newton", "a publie les", "Principia Mathematica en 1687", "HISTOIRE"),
    ("Charles Darwin", "a publie", "l Origine des especes en 1859", "HISTOIRE"),
    ("Albert Einstein", "a publie la relativite restreinte en", "1905", "HISTOIRE"),
    ("Albert Einstein", "a publie la relativite generale en", "1915", "HISTOIRE"),
    ("Marie Curie", "a recu le prix Nobel de physique en", "1903", "HISTOIRE"),
    ("Marie Curie", "a recu le prix Nobel de chimie en", "1911", "HISTOIRE"),
    ("Louis Pasteur", "a developpe le vaccin", "contre la rage en 1885", "HISTOIRE"),
    ("Alexander Fleming", "a decouvert la penicilline en", "1928", "HISTOIRE"),
    ("James Watson et Francis Crick", "ont decouvert la structure", "de l ADN en 1953", "HISTOIRE"),
    ("Alan Turing", "a invente", "la machine de Turing", "HISTOIRE"),
    ("Tim Berners-Lee", "a invente le", "World Wide Web en 1989", "HISTOIRE"),
    ("Rosalind Franklin", "a contribue a la decouverte", "de la structure de l ADN", "HISTOIRE"),
]

# ═══════════════════════════════════════════════════════════════════
# 4. CULTURE GÉNÉRALE
# ═══════════════════════════════════════════════════════════════════

CULTURE = [
    # Littérature mondiale
    ("Homere", "a ecrit", "l Odyssee", "LITTERATURE"),
    ("Homere", "a ecrit", "l Iliade", "LITTERATURE"),
    ("Dante", "a ecrit", "la Divine Comedie", "LITTERATURE"),
    ("Cervantes", "a ecrit", "Don Quichotte", "LITTERATURE"),
    ("Shakespeare", "a ecrit", "Hamlet", "LITTERATURE"),
    ("Shakespeare", "a ecrit", "Romeo et Juliette", "LITTERATURE"),
    ("Moliere", "a ecrit", "le Tartuffe", "LITTERATURE"),
    ("Moliere", "a ecrit", "l Avare", "LITTERATURE"),
    ("Victor Hugo", "a ecrit", "Notre-Dame de Paris", "LITTERATURE"),
    ("Fiodor Dostoievski", "a ecrit", "Crime et Chatiment", "LITTERATURE"),
    ("Leo Tolstoi", "a ecrit", "Guerre et Paix", "LITTERATURE"),
    ("Jane Austen", "a ecrit", "Orgueil et Prejuges", "LITTERATURE"),
    ("George Orwell", "a ecrit", "1984", "LITTERATURE"),
    ("George Orwell", "a ecrit", "la Ferme des animaux", "LITTERATURE"),
    ("Albert Camus", "a ecrit", "l Etranger", "LITTERATURE"),
    ("Marcel Proust", "a ecrit", "A la recherche du temps perdu", "LITTERATURE"),
    ("J.R.R. Tolkien", "a ecrit", "le Seigneur des Anneaux", "LITTERATURE"),
    ("J.K. Rowling", "a ecrit", "Harry Potter", "LITTERATURE"),
    ("Gabriel Garcia Marquez", "a ecrit", "Cent ans de solitude", "LITTERATURE"),
    ("Hemingway", "a ecrit", "le Vieil Homme et la Mer", "LITTERATURE"),
    ("Voltaire", "a ecrit", "Candide", "LITTERATURE"),
    ("Emile Zola", "a ecrit", "Germinal", "LITTERATURE"),
    ("Gustave Flaubert", "a ecrit", "Madame Bovary", "LITTERATURE"),
    ("Stendhal", "a ecrit", "le Rouge et le Noir", "LITTERATURE"),
    ("Charles Baudelaire", "a ecrit", "les Fleurs du mal", "LITTERATURE"),
    ("Arthur Rimbaud", "a ecrit", "le Bateau ivre", "LITTERATURE"),
    ("Madame de La Fayette", "a ecrit", "la Princesse de Cleves", "LITTERATURE"),
    ("Sartre", "a ecrit", "la Nausee", "LITTERATURE"),
    ("Simone de Beauvoir", "a ecrit", "le Deuxieme Sexe", "LITTERATURE"),
    ("Marguerite Duras", "a ecrit", "l Amant", "LITTERATURE"),
    
    # Art
    ("Picasso", "a fonde le", "cubisme", "ART"),
    ("Picasso", "a peint", "Guernica", "ART"),
    ("Van Gogh", "a peint", "la Nuit etoilee", "ART"),
    ("Van Gogh", "a peint", "les Tournesols", "ART"),
    ("Monet", "a peint", "les Nympheas", "ART"),
    ("Rembrandt", "a peint", "la Ronde de nuit", "ART"),
    ("Edvard Munch", "a peint", "le Cri", "ART"),
    ("Salvador Dali", "etait un peintre", "surrealiste", "ART"),
    ("Andy Warhol", "etait une figure du", "pop art", "ART"),
    ("le Louvre", "est le plus grand", "musee du monde", "ART"),
    ("la Joconde", "est exposee au", "musee du Louvre", "ART"),
    
    # Musique
    ("Mozart", "a compose", "la Flute enchantee", "MUSIQUE"),
    ("Mozart", "a compose", "le Requiem", "MUSIQUE"),
    ("Beethoven", "a compose", "la 9e symphonie", "MUSIQUE"),
    ("Beethoven", "a compose", "la 5e symphonie", "MUSIQUE"),
    ("Bach", "a compose", "l Art de la fugue", "MUSIQUE"),
    ("Vivaldi", "a compose", "les Quatre Saisons", "MUSIQUE"),
    ("Chopin", "a compose des", "nocturnes pour piano", "MUSIQUE"),
    ("Tchaikovski", "a compose", "le Lac des cygnes", "MUSIQUE"),
    ("Stravinski", "a compose", "le Sacre du printemps", "MUSIQUE"),
    ("les Beatles", "etaient un groupe de rock", "britannique des annees 1960", "MUSIQUE"),
    ("Elvis Presley", "etait surnomme", "le King du rock and roll", "MUSIQUE"),
    ("Michael Jackson", "etait surnomme", "le King de la pop", "MUSIQUE"),
    ("Bob Marley", "a popularise", "le reggae dans le monde", "MUSIQUE"),
    
    # Philosophie
    ("Descartes", "a enonce", "je pense donc je suis", "PHILOSOPHIE"),
    ("Kant", "a ecrit", "la Critique de la raison pure", "PHILOSOPHIE"),
    ("Nietzsche", "a proclame", "Dieu est mort", "PHILOSOPHIE"),
    ("Platon", "a ecrit", "la Republique", "PHILOSOPHIE"),
    ("Aristote", "a ecrit", "l Ethique a Nicomaque", "PHILOSOPHIE"),
    ("Rousseau", "a ecrit", "le Contrat social", "PHILOSOPHIE"),
    ("Montesquieu", "a theorise", "la separation des pouvoirs", "PHILOSOPHIE"),
    ("Karl Marx", "a ecrit", "le Capital", "PHILOSOPHIE"),
    ("Simone Weil", "etait une philosophe", "francaise du 20e siecle", "PHILOSOPHIE"),
    ("Hannah Arendt", "a analyse", "les origines du totalitarisme", "PHILOSOPHIE"),
    
    # Divers culture générale
    ("le francais", "est une langue", "romane", "CULTURE_G"),
    ("l anglais", "est une langue", "germanique", "CULTURE_G"),
    ("le mandarin", "est la langue la plus", "parlee dans le monde", "CULTURE_G"),
    ("l esperanto", "est une langue", "construite internationale", "CULTURE_G"),
    ("les Jeux Olympiques", "ont ete ressuscites en", "1896 par Pierre de Coubertin", "CULTURE_G"),
    ("le premier JO moderne", "a eu lieu a", "Athenes", "CULTURE_G"),
    ("la coupe du monde de football", "a lieu tous les", "4 ans", "CULTURE_G"),
    ("le Bresil", "a gagne le plus de", "coupes du monde de football", "CULTURE_G"),
    ("le Tour de France", "est une course cycliste", "creee en 1903", "CULTURE_G"),
    ("le drapeau francais", "est", "bleu blanc rouge", "CULTURE_G"),
    ("le drapeau japonais", "represente", "un disque rouge sur fond blanc", "CULTURE_G"),
    ("le kimono", "est un vetement traditionnel", "japonais", "CULTURE_G"),
    ("le sushi", "est un plat traditionnel", "japonais a base de riz et poisson cru", "CULTURE_G"),
    ("la pizza", "est originaire de", "Naples en Italie", "CULTURE_G"),
    ("le croissant", "est une viennoiserie", "d origine autrichienne", "CULTURE_G"),
    ("le champagne", "est un vin petillant produit", "dans la region de Champagne", "CULTURE_G"),
]

# ═══════════════════════════════════════════════════════════════════
# 5. AUTO-EXTENSION
# ═══════════════════════════════════════════════════════════════════

# English facts for LM Arena (most important 100)
EN_FACTS = [
    # Capitals EN
    ("paris", "is the capital of", "France", "GEOGRAPHY"),
    ("london", "is the capital of", "the United Kingdom", "GEOGRAPHY"),
    ("berlin", "is the capital of", "Germany", "GEOGRAPHY"),
    ("rome", "is the capital of", "Italy", "GEOGRAPHY"),
    ("madrid", "is the capital of", "Spain", "GEOGRAPHY"),
    ("tokyo", "is the capital of", "Japan", "GEOGRAPHY"),
    ("beijing", "is the capital of", "China", "GEOGRAPHY"),
    ("moscow", "is the capital of", "Russia", "GEOGRAPHY"),
    ("washington", "is the capital of", "the United States", "GEOGRAPHY"),
    ("ottawa", "is the capital of", "Canada", "GEOGRAPHY"),
    ("brasilia", "is the capital of", "Brazil", "GEOGRAPHY"),
    ("canberra", "is the capital of", "Australia", "GEOGRAPHY"),
    ("new delhi", "is the capital of", "India", "GEOGRAPHY"),
    ("cairo", "is the capital of", "Egypt", "GEOGRAPHY"),
    ("athens", "is the capital of", "Greece", "GEOGRAPHY"),
    ("vienna", "is the capital of", "Austria", "GEOGRAPHY"),
    ("stockholm", "is the capital of", "Sweden", "GEOGRAPHY"),
    ("oslo", "is the capital of", "Norway", "GEOGRAPHY"),
    ("helsinki", "is the capital of", "Finland", "GEOGRAPHY"),
    ("warsaw", "is the capital of", "Poland", "GEOGRAPHY"),
    ("lisbon", "is the capital of", "Portugal", "GEOGRAPHY"),
    ("brussels", "is the capital of", "Belgium", "GEOGRAPHY"),
    ("amsterdam", "is the capital of", "the Netherlands", "GEOGRAPHY"),
    ("seoul", "is the capital of", "South Korea", "GEOGRAPHY"),
    ("bangkok", "is the capital of", "Thailand", "GEOGRAPHY"),
    ("hanoi", "is the capital of", "Vietnam", "GEOGRAPHY"),
    ("jakarta", "is the capital of", "Indonesia", "GEOGRAPHY"),
    ("manila", "is the capital of", "the Philippines", "GEOGRAPHY"),
    ("tehran", "is the capital of", "Iran", "GEOGRAPHY"),
    ("baghdad", "is the capital of", "Iraq", "GEOGRAPHY"),
    ("ankara", "is the capital of", "Turkey", "GEOGRAPHY"),
    ("buenos aires", "is the capital of", "Argentina", "GEOGRAPHY"),
    ("santiago", "is the capital of", "Chile", "GEOGRAPHY"),
    ("lima", "is the capital of", "Peru", "GEOGRAPHY"),
    ("bogota", "is the capital of", "Colombia", "GEOGRAPHY"),
    ("mexico city", "is the capital of", "Mexico", "GEOGRAPHY"),
    ("dublin", "is the capital of", "Ireland", "GEOGRAPHY"),
    ("copenhagen", "is the capital of", "Denmark", "GEOGRAPHY"),
    ("prague", "is the capital of", "the Czech Republic", "GEOGRAPHY"),
    ("budapest", "is the capital of", "Hungary", "GEOGRAPHY"),
    
    # Geography EN
    ("the Nile", "is the longest", "river in the world", "GEOGRAPHY"),
    ("the Amazon", "is the river with", "the largest water flow", "GEOGRAPHY"),
    ("Mount Everest", "is the highest", "mountain in the world", "GEOGRAPHY"),
    ("the Sahara", "is the largest", "hot desert in the world", "GEOGRAPHY"),
    ("the Pacific", "is the largest", "ocean in the world", "GEOGRAPHY"),
    ("Africa", "is the", "second largest continent", "GEOGRAPHY"),
    ("Asia", "is the", "largest continent", "GEOGRAPHY"),
    
    # History EN
    ("the French Revolution", "started in", "1789", "HISTORY"),
    ("World War 2", "ended in", "1945", "HISTORY"),
    ("World War 2", "started in", "1939", "HISTORY"),
    ("World War 1", "ended in", "1918", "HISTORY"),
    ("the Berlin Wall", "fell in", "1989", "HISTORY"),
    ("man", "first walked on the Moon in", "1969", "HISTORY"),
    ("Neil Armstrong", "was the first man", "on the Moon", "HISTORY"),
    ("Alexander Fleming", "discovered", "penicillin", "HISTORY"),
    ("penicillin", "was discovered in", "1928", "HISTORY"),
    ("Albert Einstein", "published the theory of relativity in", "1905", "HISTORY"),
    ("Charles Darwin", "published", "On the Origin of Species", "HISTORY"),
    ("Christopher Columbus", "reached America in", "1492", "HISTORY"),
    ("Isaac Newton", "discovered", "the law of gravity", "HISTORY"),
    ("Marie Curie", "discovered", "radium and polonium", "HISTORY"),
    ("Martin Luther King", "fought for", "civil rights", "HISTORY"),
    ("Nelson Mandela", "fought against", "apartheid", "HISTORY"),
    ("Mahatma Gandhi", "led", "the non-violent independence movement in India", "HISTORY"),
    
    # Literature EN
    ("Shakespeare", "wrote", "Hamlet", "LITERATURE"),
    ("Shakespeare", "wrote", "Romeo and Juliet", "LITERATURE"),
    ("George Orwell", "wrote", "1984", "LITERATURE"),
    ("George Orwell", "wrote", "Animal Farm", "LITERATURE"),
    ("Victor Hugo", "wrote", "Les Miserables", "LITERATURE"),
    ("Homer", "wrote", "the Odyssey", "LITERATURE"),
    ("Dante", "wrote", "the Divine Comedy", "LITERATURE"),
    ("Jane Austen", "wrote", "Pride and Prejudice", "LITERATURE"),
    ("Fyodor Dostoevsky", "wrote", "Crime and Punishment", "LITERATURE"),
    ("Leo Tolstoy", "wrote", "War and Peace", "LITERATURE"),
    ("J.R.R. Tolkien", "wrote", "The Lord of the Rings", "LITERATURE"),
    ("J.K. Rowling", "wrote", "Harry Potter", "LITERATURE"),
    ("Ernest Hemingway", "wrote", "The Old Man and the Sea", "LITERATURE"),
    
    # Culture EN
    ("the yen", "is the currency of", "Japan", "CULTURE"),
    ("the euro", "is the currency of", "France", "CULTURE"),
    ("the dollar", "is the currency of", "the United States", "CULTURE"),
    ("the pound", "is the currency of", "the United Kingdom", "CULTURE"),
    ("Portuguese", "is spoken in", "Brazil", "CULTURE"),
    ("Spanish", "is spoken in", "Mexico", "CULTURE"),
    ("sushi", "is a Japanese dish", "made of rice and raw fish", "CULTURE"),
    ("the speed of light", "is approximately", "300000 kilometers per second", "SCIENCE"),
    ("DNA", "carries", "genetic information", "SCIENCE"),
    ("water", "freezes at", "0 degrees Celsius", "SCIENCE"),
    ("water", "boils at", "100 degrees Celsius", "SCIENCE"),
    ("photosynthesis", "converts", "sunlight into chemical energy in plants", "SCIENCE"),
    ("the Earth", "orbits around", "the Sun", "SCIENCE"),
    ("the Moon", "orbits around", "the Earth", "SCIENCE"),
    ("Mars", "is known as", "the Red Planet", "SCIENCE"),
    ("Jupiter", "is the largest", "planet in the solar system", "SCIENCE"),
]

ALL_FACTS = CAPITALES + GEOGRAPHIE_PHYSIQUE + HISTOIRE + CULTURE + EN_FACTS

def extend_all(model):
    """Ajoute tous les faits (FR + EN) au modèle."""
    added = 0
    for fact in ALL_FACTS:
        if fact not in model.knowledge_base:
            model.knowledge_base.append(fact)
            added += 1
    if added > 0:
        from harmonic_model import build_waves
        model.kx, model.ky, model.w2i = build_waves(model.knowledge_base)
    return added

if __name__ == '__main__':
    print(f"Total faits disponibles : {len(ALL_FACTS)}")
    print(f"  Capitales : {len(CAPITALES)}")
    print(f"  Géographie physique : {len(GEOGRAPHIE_PHYSIQUE)}")
    print(f"  Histoire : {len(HISTOIRE)}")
    print(f"  Culture : {len(CULTURE)}")
