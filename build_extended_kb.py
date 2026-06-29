# Script to build the extended knowledge base
# Run once to generate the KNOWLEDGE_BASE for qualitative_knowledge.py

facts = []

# ================================================================
# PHYSIQUE_FOND (0-15°) — ondes, forces, lumière, énergie, résonance
# ================================================================
physique_fond = [
    ("lumiere", "est une", "onde electromagnetique"),
    ("lumiere", "se deplace a", "300000 km/s dans le vide"),
    ("lumiere", "est composee de", "photons"),
    ("lumiere", "se reflechit sur", "les surfaces polies"),
    ("lumiere", "se refracte dans", "l eau et le verre"),
    ("lumiere", "se decompose en", "un spectre de couleurs"),
    ("photons", "sont", "les particules de lumiere"),
    ("photons", "n ont pas de", "masse"),
    ("photons", "transportent", "l energie lumineuse"),
    ("onde", "transporte", "energie sans matiere"),
    ("onde", "est", "une perturbation qui se propage"),
    ("onde", "a une", "frequence et une longueur d onde"),
    ("onde", "peut etre", "transversale ou longitudinale"),
    ("frequence", "mesure", "le nombre d oscillations par seconde"),
    ("frequence", "est", "l inverse de la periode"),
    ("frequence", "se mesure en", "Hertz"),
    ("resonance", "amplifie", "ondes de meme frequence"),
    ("resonance", "est", "le phenomene d amplification par accord de phase"),
    ("resonance", "peut detruire", "un pont si la frequence correspond"),
    ("interference", "est", "la superposition de deux ondes"),
    ("interference", "peut etre", "constructive ou destructive"),
    ("diffraction", "est", "la deviation d une onde par un obstacle"),
    ("reflexion", "est", "le rebond d une onde sur une surface"),
    ("refraction", "est", "le changement de direction d une onde"),
    ("energie", "se conserve", "dans un systeme isole"),
    ("energie", "existe sous", "plusieurs formes"),
    ("energie", "ne peut etre", "ni creee ni detruite"),
    ("force", "est", "une action modifiant le mouvement"),
    ("force", "se mesure en", "Newtons"),
    ("newton", "a decouvert", "les lois du mouvement"),
    ("newton", "a formule", "la loi de la gravitation universelle"),
    ("gravite", "est", "la courbure de l espace temps"),
    ("gravite", "attire", "toute masse vers toute autre masse"),
    ("gravite", "est", "la plus faible des forces fondamentales"),
    ("einstein", "a decouvert", "la relativite"),
    ("einstein", "a formule", "E egal mc deux"),
    ("einstein", "a predit", "les ondes gravitationnelles"),
    ("relativite", "decrit", "la gravitation comme courbure de l espace"),
    ("relativite", "unifie", "espace et temps"),
    ("relativite", "predit", "trous noirs et ondes gravitationnelles"),
    ("relativite", "a ete verifiee par", "l eclipse de 1919"),
    ("maxwell", "a unifie", "electricite et magnetisme"),
    ("maxwell", "a predit", "les ondes electromagnetiques"),
    ("electromagnetisme", "decrit", "l interaction entre charges electriques"),
    ("electromagnetisme", "est", "une des quatre forces fondamentales"),
    ("planck", "a introduit", "le quantum d action"),
    ("planck", "a decouvert", "la constante de Planck"),
    ("bohr", "a propose", "le modele atomique"),
    ("schrodinger", "a formule", "l equation d onde"),
    ("heisenberg", "a enonce", "le principe d incertitude"),
]
for s, r, o in physique_fond:
    facts.append((s, r, o, "PHYSIQUE_FOND"))

# ================================================================
# PHYSIQUE_APPLI (15-30°) — matière, atomes, applications
# ================================================================
physique_appli = [
    ("atome", "est compose de", "noyau et electrons"),
    ("atome", "est", "la plus petite unite d un element"),
    ("electron", "orbite", "autour du noyau"),
    ("electron", "est", "une particule elementaire"),
    ("electron", "a une charge", "negative"),
    ("proton", "est", "une particule du noyau atomique"),
    ("proton", "a une charge", "positive"),
    ("neutron", "est", "une particule du noyau sans charge"),
    ("noyau", "contient", "protons et neutrons"),
    ("noyau", "est", "tres dense"),
    ("quark", "est", "un constituant elementaire des protons"),
    ("quark", "existe en", "six saveurs differentes"),
    ("molecule", "est", "un assemblage d atomes"),
    ("molecule", "est liee par", "des liaisons chimiques"),
    ("isotope", "est", "un atome avec un nombre different de neutrons"),
    ("radioactivite", "est", "la desintegration de noyaux instables"),
    ("curie", "a decouvert", "la radioactivite"),
    ("curie", "a isole", "le radium et le polonium"),
    ("fission", "est", "la division d un noyau lourd"),
    ("fusion", "est", "la combinaison de noyaux legers"),
    ("fusion", "alimente", "le soleil et les etoiles"),
    ("laser", "produit", "lumiere coherente"),
    ("laser", "est utilise pour", "la chirurgie et les telecommunications"),
    ("aimant", "cree", "un champ magnetique"),
    ("aimant", "a deux poles", "nord et sud"),
    ("batterie", "stocke", "energie chimique"),
    ("batterie", "produit", "courant electrique"),
    ("moteur", "transforme", "energie en mouvement"),
    ("generateur", "transforme", "mouvement en electricite"),
    ("internet", "connecte", "les ordinateurs du monde"),
    ("internet", "utilise", "le protocole TCP IP"),
    ("ordinateur", "traite", "information binaire"),
    ("ordinateur", "est compose de", "processeur et memoire"),
    ("transistor", "est", "le composant de base des circuits"),
    ("transistor", "amplifie ou bloque", "le courant electrique"),
    ("supraconducteur", "conduit", "electricite sans resistance"),
    ("supraconducteur", "necessite", "de tres basses temperatures"),
    ("laser", "signifie", "amplification de lumiere par emission stimulee"),
    ("hologramme", "est", "une image tridimensionnelle par interference"),
    ("hologramme", "utilise", "la lumiere laser"),
    ("fibre optique", "transmet", "la lumiere sur de longues distances"),
    ("fibre optique", "utilise", "la reflexion totale interne"),
    ("radar", "detecte", "les objets par reflexion d ondes"),
    ("radar", "utilise", "des ondes radio"),
    ("sonar", "detecte", "les objets sous l eau par ondes sonores"),
    ("ecran", "affiche", "des images par pixels lumineux"),
    ("carte graphique", "calcule", "les images pour l affichage"),
]
for s, r, o in physique_appli:
    facts.append((s, r, o, "PHYSIQUE_APPLI"))

# ================================================================
# MATHS_PURES (30-45°) — nombres, géométrie, logique
# ================================================================
maths_pures = [
    ("phi", "est le", "nombre d or"),
    ("phi", "vaut", "1.618 environ"),
    ("phi", "est", "la proportion divine"),
    ("phi", "apparait dans", "la suite de Fibonacci"),
    ("phi", "est", "le nombre le plus irrationnel"),
    ("pi", "est le", "rapport cercle diametre"),
    ("pi", "vaut", "3.14159 environ"),
    ("pi", "est", "un nombre transcendant"),
    ("e", "est", "la base du logarithme naturel"),
    ("e", "vaut", "2.718 environ"),
    ("e", "est", "la limite de un plus un sur n puissance n"),
    ("zero", "represente", "le neant"),
    ("zero", "est", "l element neutre de l addition"),
    ("zero", "a ete invente par", "les mathematiciens indiens"),
    ("infini", "represente", "l illimite"),
    ("infini", "est", "ce qui n a pas de fin"),
    ("infini", "existe en", "plusieurs tailles selon Cantor"),
    ("nombre", "est", "une abstraction representant une quantite"),
    ("nombre premier", "est", "divisible seulement par un et lui meme"),
    ("nombre premier", "est", "infini selon Euclide"),
    ("nombre complexe", "a", "une partie reelle et une partie imaginaire"),
    ("i", "est", "la racine carree de moins un"),
    ("addition", "est", "l operation fondamentale"),
    ("soustraction", "est", "l inverse de l addition"),
    ("multiplication", "est", "l addition repetee"),
    ("division", "est", "l inverse de la multiplication"),
    ("fraction", "represente", "une partie d un tout"),
    ("geometrie", "etudie", "les formes et l espace"),
    ("geometrie", "est", "la mesure de la terre"),
    ("triangle", "a", "trois cotes et trois angles"),
    ("triangle", "a une somme d angles de", "180 degres"),
    ("cercle", "est", "l ensemble des points equidistants d un centre"),
    ("sphere", "est", "l ensemble des points equidistants dans l espace"),
    ("polygone", "est", "une figure fermee a plusieurs cotes"),
    ("fractale", "est", "une forme autorepetee a toutes les echelles"),
    ("fractale", "a une", "dimension non entiere"),
    ("fractale", "decrit", "les cotes, les choux et les nuages"),
    ("logique", "est", "l art du raisonnement juste"),
    ("logique", "repose sur", "le principe de non contradiction"),
    ("logique", "utilise", "des propositions et des connecteurs"),
    ("theoreme", "est", "une proposition demontrable"),
    ("axiome", "est", "une proposition admise sans demonstration"),
    ("godel", "a demontre", "l incompletude des mathematiques"),
    ("equation", "exprime", "l egalite entre deux expressions"),
    ("equation", "a une", "ou plusieurs inconnues"),
    ("algebre", "utilise", "des lettres pour representer des nombres"),
    ("algebre", "a ete developpee par", "Al Khwarizmi"),
    ("trigonometrie", "etudie", "les relations entre angles et longueurs"),
    ("sinus", "est le rapport", "cote oppose sur hypotenuse"),
    ("cosinus", "est le rapport", "cote adjacent sur hypotenuse"),
]
for s, r, o in maths_pures:
    facts.append((s, r, o, "MATHS_PURES"))

# ================================================================
# GENERATE THE FILE
# ================================================================
output = "KNOWLEDGE_BASE = [\n"
for s, r, o, sec in facts:
    output += f'    ("{s}", "{r}", "{o}", "{sec}"),\n'
output += "]\n"

with open("E:/SAAS - Copie/engine/_extended_kb.py", "w", encoding="utf-8") as f:
    f.write(output)

print(f"Generated {len(facts)} facts")
print("Now continuing with remaining sectors...")
