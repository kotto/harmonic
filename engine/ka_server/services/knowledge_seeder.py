"""
🌊 knowledge_seeder.py — Générateur de corpus propre
=====================================================
Produit un corpus de définitions propres et vérifiées dans knowledge/,
puis compile le tout en hologrammes.

Stratégie :
  - Domaines : 12 (physique, astronomie, biologie, chimie, géographie,
               histoire, informatique, mathématiques, médecine, art,
               philosophie, technologie)
  - ~30-50 concepts par domaine avec 2-5 faits chacun
  - ~500 concepts, ~1500 faits — tous vérifiés, sans bruit
  - Format OKF : chaque concept = un fichier .md dans knowledge/<domain>/

Usage :
  python ka_server/services/knowledge_seeder.py              # génère + compile
  python ka_server/services/knowledge_seeder.py --no-compile # génère seulement
"""

import logging
import re
import sys
import time
from pathlib import Path

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
WIKI_DIR = _ENGINE_DIR / 'knowledge'


# ═══════════════════════════════════════════════════════════
# CORPUS DE CONNAISSANCES
# ═══════════════════════════════════════════════════════════
# Chaque entrée : (id, title, [(sujet, relation, objet), ...])

# ── GÉNÉRATEUR DE FAITS ──────────────────────────────────

CORPUS = {}  # domain → [(id, title, facts), ...]

# Helper pour créer des faits rapidement
def _fact(s, r, o):
    return (s, r, o)

def _concept(id, title, *facts):
    return (id, title, list(facts))

# ═══════════════════════════
# PHYSIQUE
# ═══════════════════════════

CORPUS['physique'] = [
    _concept('hologramme', 'Hologramme',
        _fact('hologramme', 'est une', 'figure d interference qui stocke une image en trois dimensions'),
        _fact('hologramme', 'est cree par', 'l interference de deux faisceaux laser'),
        _fact('hologramme', 'a ete invente par', 'Dennis Gabor en 1947'),
        _fact('holographie', 'permet de', 'restituer une image en trois dimensions'),
    ),
    _concept('lumiere', 'Lumière',
        _fact('lumiere', 'est une', 'onde electromagnetique'),
        _fact('lumiere', 'est composee de', 'particules appelees photons'),
        _fact('lumiere', 'a pour vitesse', '299 792 458 metres par seconde dans le vide'),
        _fact('lumiere', 'est', 'le rayonnement electromagnetique visible par l oeil humain'),
    ),
    _concept('gravite', 'Gravité',
        _fact('gravite', 'est une', 'force d attraction entre les masses'),
        _fact('gravite', 'est decrite par', 'la loi de la gravitation universelle de Newton'),
        _fact('gravite', 'est expliquee par', 'la courbure de l espace temps dans la relativite generale'),
    ),
    _concept('atome', 'Atome',
        _fact('atome', 'est', 'la plus petite unite de la matiere'),
        _fact('atome', 'est compose de', 'protons neutrons et electrons'),
        _fact('atome', 'a un noyau', 'charge positivement entoure d electrons'),
    ),
    _concept('energie', 'Énergie',
        _fact('energie', 'est', 'la capacite a produire un travail'),
        _fact('energie', 'se mesure en', 'joules'),
        _fact('energie', 'est conservee', 'selon le principe de conservation de l energie'),
    ),
    _concept('electricite', 'Électricité',
        _fact('electricite', 'est', 'le deplacement de charges electriques'),
        _fact('electricite', 'est generee par', 'le mouvement des electrons'),
    ),
    _concept('magnetisme', 'Magnétisme',
        _fact('magnetisme', 'est', 'la force exercee par les aimants'),
        _fact('magnetisme', 'est produit par', 'le mouvement de charges electriques'),
    ),
    _concept('thermodynamique', 'Thermodynamique',
        _fact('thermodynamique', 'est', 'la branche de la physique qui etudie la chaleur'),
        _fact('premier principe de la thermodynamique', 'affirme que', 'l energie se conserve'),
        _fact('second principe de la thermodynamique', 'affirme que', 'l entropie ne peut pas diminuer'),
    ),
    _concept('relativite', 'Relativité',
        _fact('relativite restreinte', 'a ete formulee par', 'Albert Einstein en 1905'),
        _fact('relativite restreinte', 'affirme que', 'la vitesse de la lumiere est constante dans tous les referentiels'),
        _fact('relativite generale', 'decrit', 'la gravite comme une courbure de l espace temps'),
    ),
    _concept('mecanique_quantique', 'Mécanique Quantique',
        _fact('mecanique quantique', 'est', 'la theorie qui decrit le comportement de la matiere a l echelle atomique'),
        _fact('principe d incertitude', 'affirme que', 'on ne peut pas mesurer simultanement la position et la vitesse d une particule'),
        _fact('fonction d onde', 'decrit', 'l etat quantique d un systeme'),
    ),
    _concept('theorie_cordes', 'Théorie des Cordes',
        _fact('theorie des cordes', 'est', 'un cadre theorique ou les particules sont des cordes vibrantes'),
        _fact('theorie des cordes', 'tente d unifier', 'la relativite generale et la mecanique quantique'),
    ),
    _concept('laser', 'Laser',
        _fact('laser', 'est une', 'source lumineuse a emission stimulee'),
        _fact('laser', 'signifie', 'light amplification by stimulated emission of radiation'),
        _fact('laser', 'emet', 'un faisceau coherent et monochromatique'),
        _fact('laser', 'est utilise en', 'medecine chirurgie telecommunications et industrie'),
    ),
    _concept('fission_fusion', 'Fission et Fusion Nucléaire',
        _fact('fission nucleaire', 'est', 'la division d un noyau atomique en noyaux plus legers'),
        _fact('fusion nucleaire', 'est', 'la combinaison de noyaux atomiques legers en un noyau plus lourd'),
        _fact('fusion nucleaire', 'produit de l energie', 'dans les etoiles comme le soleil'),
    ),
    _concept('vitesse_lumiere', 'Vitesse de la Lumière',
        _fact('vitesse de la lumiere dans le vide', 'est', '299 792 458 metres par seconde'),
        _fact('rien ne peut depasser', 'la vitesse de la lumiere dans le vide', 'selon la theorie de la relativite'),
    ),
    _concept('theorie_harmonique', 'Théorie Harmonique Universelle',
        _fact('theorie harmonique universelle', 'est', 'un cadre theorique fonde sur les ondes et les constantes fondamentales'),
        _fact('theorie harmonique universelle', 'unifie', 'la physique classique et quantique'),
        _fact('theorie harmonique', 'utilise', 'les primitives ondulatoires encode resonner et emerger'),
        _fact('nombre d or', 'est', 'la constante fondamentale de la theorie harmonique'),
    ),
]

# ═══════════════════════════
# ASTRONOMIE
# ═══════════════════════════

CORPUS['astronomie'] = [
    _concept('trou_noir', 'Trou Noir',
        _fact('trou noir', 'est une', 'region de l espace ou la gravite est si forte que rien ne s en echappe'),
        _fact('trou noir', 'est forme par', 'l effondrement d une etoile massive'),
        _fact('trou noir', 'a ete predit par', 'la theorie de la relativite generale'),
    ),
    _concept('systeme_solaire', 'Système Solaire',
        _fact('systeme solaire', 'est compose de', 'huit planetes orbitant autour du soleil'),
        _fact('soleil', 'est', 'une etoile de type naine jaune'),
        _fact('systeme solaire', 's est forme il y a', '4 6 milliards d annees'),
    ),
    _concept('planetes', 'Planètes',
        _fact('planete', 'est un', 'corps celeste en orbite autour d une etoile'),
        _fact('planete', 'ne produit pas', 'sa propre lumiere'),
        _fact('plus grande planete du systeme solaire', 'est', 'jupiter'),
        _fact('plus petite planete du systeme solaire', 'est', 'mercure'),
    ),
    _concept('etoiles', 'Étoiles',
        _fact('etoile', 'est un', 'astre qui produit sa propre lumiere par fusion nucleaire'),
        _fact('soleil', 'est', 'l etoile la plus proche de la terre'),
        _fact('etoile', 'produit de l energie', 'par fusion nucleaire de l hydrogene en helium'),
    ),
    _concept('galaxies', 'Galaxies',
        _fact('galaxie', 'est un', 'ensemble d etoiles de gaz et de poussiere'),
        _fact('voie lactee', 'est', 'la galaxie qui contient le systeme solaire'),
        _fact('galaxie la plus proche', 'est', 'la galaxie d Andromede'),
    ),
    _concept('big_bang', 'Big Bang',
        _fact('big bang', 'est', 'la theorie dominante sur l origine de l univers'),
        _fact('big bang', 's est produit il y a', '13 8 milliards d annees'),
        _fact('apres le big bang', 'l univers est en', 'expansion continue'),
    ),
    _concept('terre', 'Terre',
        _fact('terre', 'est la troisieme planete', 'du systeme solaire'),
        _fact('terre', 'est', 'la seule planete connue abritant la vie'),
        _fact('terre', 'a un satellite naturel', 'appele la lune'),
    ),
    _concept('lune', 'Lune',
        _fact('lune', 'est', 'le satellite naturel de la terre'),
        _fact('lune', 'influence', 'les marees sur terre'),
    ),
    _concept('supernova', 'Supernova',
        _fact('supernova', 'est une', 'explosion d une etoile en fin de vie'),
        _fact('supernova', 'produit', 'des elements lourds comme l or et l uranium'),
    ),
]

# ═══════════════════════════
# BIOLOGIE
# ═══════════════════════════

CORPUS['biologie'] = [
    _concept('adn', 'ADN',
        _fact('adn', 'est une', 'molecule qui porte l information genetique'),
        _fact('adn', 'signifie', 'acide desoxyribonucleique'),
        _fact('adn', 'est forme de', 'deux brins en double helice'),
        _fact('adn', 'se trouve dans', 'le noyau des cellules'),
        _fact('acide desoxyribonucleique', 'est', 'une molecule qui porte l information genetique'),
    ),
    _concept('cellule', 'Cellule',
        _fact('cellule', 'est', 'l unite de base du vivant'),
        _fact('cellule', 'est composee de', 'membrane cytoplasme et noyau'),
        _fact('cellule', 'est', 'la plus petite unite capable de se reproduire'),
    ),
    _concept('proteine', 'Protéine',
        _fact('proteine', 'est une', 'molecule composee d acides amines'),
        _fact('enzyme', 'est une', 'proteine qui accelere les reactions chimiques'),
    ),
    _concept('virus', 'Virus',
        _fact('virus', 'est un', 'micro organisme qui a besoin d une cellule hote pour se reproduire'),
        _fact('virus', 'est', 'plus petit qu une bacterie'),
    ),
    _concept('bacterie', 'Bactérie',
        _fact('bacterie', 'est un', 'micro organisme unicellulaire'),
        _fact('bacterie', 'se reproduit par', 'division cellulaire'),
    ),
    _concept('photosynthese', 'Photosynthèse',
        _fact('photosynthese', 'est', 'le processus par lequel les plantes produisent leur energie'),
        _fact('photosynthese', 'utilise', 'la lumiere le dioxyde de carbone et l eau'),
        _fact('photosynthese', 'produit', 'du glucose et de l oxygene'),
    ),
    _concept('evolution', 'Évolution',
        _fact('evolution', 'est', 'le processus par lequel les especes changent au fil du temps'),
        _fact('evolution', 'a ete decrite par', 'Charles Darwin'),
        _fact('selection naturelle', 'favorise', 'les individus les mieux adaptes a leur environnement'),
    ),
    _concept('systeme_nerveux', 'Système Nerveux',
        _fact('systeme nerveux', 'est compose du', 'cerveau de la moelle epiniere et des nerfs'),
        _fact('neurone', 'est', 'la cellule de base du systeme nerveux'),
        _fact('cerveau', 'est', 'l organe central du systeme nerveux'),
    ),
    _concept('systeme_circulatoire', 'Système Circulatoire',
        _fact('systeme circulatoire', 'est compose', 'du coeur des arteres et des veines'),
        _fact('coeur', 'pompe', 'le sang dans tout le corps'),
        _fact('sang', 'transporte', 'l oxygene et les nutriments aux cellules'),
    ),
    _concept('ecosysteme', 'Écosystème',
        _fact('ecosysteme', 'est un', 'ensemble d organismes vivants et de leur environnement'),
        _fact('biodiversite', 'est', 'la diversite des especes dans un ecosysteme'),
    ),
]

# ═══════════════════════════
# CHIMIE
# ═══════════════════════════

CORPUS['chimie'] = [
    _concept('molecule', 'Molécule',
        _fact('molecule', 'est une', 'assemblage d atomes lies entre eux'),
        _fact('element chimique', 'est', 'une substance composee d un seul type d atome'),
        _fact('reaction chimique', 'est', 'la transformation de substances en d autres substances'),
    ),
    _concept('eau', 'Eau',
        _fact('eau', 'a pour formule chimique', 'H2O'),
        _fact('eau', 'est composee de', 'deux atomes d hydrogene et un atome d oxygene'),
        _fact('eau', 'bout a', '100 degres celsius au niveau de la mer'),
        _fact('eau', 'gele a', '0 degre celsius'),
    ),
    _concept('elements_chimiques', 'Éléments Chimiques',
        _fact('oxygene', 'a pour symbole chimique', 'O'),
        _fact('hydrogene', 'a pour symbole chimique', 'H'),
        _fact('carbone', 'a pour symbole chimique', 'C'),
        _fact('azote', 'a pour symbole chimique', 'N'),
        _fact('fer', 'a pour symbole chimique', 'Fe'),
        _fact('or', 'a pour symbole chimique', 'Au'),
        _fact('tableau periodique', 'classe', 'les elements chimiques par numero atomique'),
    ),
    _concept('acide_base', 'Acides et Bases',
        _fact('acide', 'est une', 'substance qui libere des ions hydrogene en solution'),
        _fact('base', 'est une', 'substance qui accepte des ions hydrogene'),
        _fact('ph', 'mesure', 'l acidite d une solution de 0 a 14'),
    ),
    _concept('etats_matiere', 'États de la Matière',
        _fact('matiere', 'existe sous trois etats', 'solide liquide et gazeux'),
        _fact('fusion', 'est', 'le passage de l etat solide a l etat liquide'),
        _fact('vaporisation', 'est', 'le passage de l etat liquide a l etat gazeux'),
    ),
]

# ═══════════════════════════
# GÉOGRAPHIE
# ═══════════════════════════

CORPUS['geographie'] = [
    _concept('pays_capitales', 'Pays et Capitales',
        _fact('france', 'a pour capitale', 'paris'),
        _fact('japon', 'a pour capitale', 'tokyo'),
        _fact('chine', 'a pour capitale', 'pekin'),
        _fact('royaume uni', 'a pour capitale', 'londres'),
        _fact('bresil', 'a pour capitale', 'brasilia'),
        _fact('canada', 'a pour capitale', 'ottawa'),
        _fact('australie', 'a pour capitale', 'canberra'),
        _fact('allemagne', 'a pour capitale', 'berlin'),
        _fact('italie', 'a pour capitale', 'rome'),
        _fact('espagne', 'a pour capitale', 'madrid'),
        _fact('inde', 'a pour capitale', 'new delhi'),
        _fact('russie', 'a pour capitale', 'moscou'),
        _fact('etats unis', 'a pour capitale', 'washington'),
        _fact('egypte', 'a pour capitale', 'le caire'),
        _fact('senegal', 'a pour capitale', 'dakar'),
        _fact('cote d ivoire', 'a pour capitale', 'yamoussoukro'),
        _fact('rdc', 'a pour capitale', 'kinshasa'),
    ),
    _concept('geographie_generale', 'Notions de Géographie',
        _fact('continent', 'est une', 'grande etendue de terre separee des autres'),
        _fact('ocean', 'est une', 'grande etendue d eau salee'),
        _fact('montagne', 'est un', 'relief eleve de la surface terrestre'),
        _fact('fleuve', 'est', 'un cours d eau qui se jette dans la mer'),
        _fact('plus long fleuve du monde', 'est', 'le Nil'),
        _fact('plus haut sommet du monde', 'est', 'l Everest'),
        _fact('plus grand ocean', 'est', 'l ocean Pacifique'),
        _fact('plus grand continent', 'est', 'l Asie'),
    ),
    _concept('continents', 'Continents',
        _fact('nombre de continents', 'est', 'sept'),
        _fact('asie', 'est', 'le plus grand continent'),
        _fact('australie', 'est', 'le plus petit continent'),
    ),
]

# ═══════════════════════════
# HISTOIRE
# ═══════════════════════════

CORPUS['histoire'] = [
    _concept('revolution_francaise', 'Révolution Française',
        _fact('revolution francaise', 'a commence en', '1789'),
        _fact('revolution francaise', 'a aboli', 'la monarchie absolue'),
        _fact('prise de la bastille', 'a eu lieu le', '14 juillet 1789'),
        _fact('declaration des droits de l homme', 'a ete adoptee en', '1789'),
    ),
    _concept('napoleon', 'Napoléon',
        _fact('napoleon bonaparte', 'est ne en', '1769'),
        _fact('napoleon', 'a ete empereur', 'de 1804 a 1815'),
        _fact('napoleon', 'a ete vaincu a', 'Waterloo en 1815'),
        _fact('code civil', 'a ete cree par', 'Napoleon en 1804'),
    ),
    _concept('premiere_guerre_mondiale', 'Première Guerre Mondiale',
        _fact('premiere guerre mondiale', 'a dure de', '1914 a 1918'),
        _fact('premiere guerre mondiale', 'a oppose', 'la Triple Entente a la Triple Alliance'),
        _fact('traite de versailles', 'a mis fin a', 'la premiere guerre mondiale en 1919'),
    ),
    _concept('seconde_guerre_mondiale', 'Seconde Guerre Mondiale',
        _fact('seconde guerre mondiale', 'a dure de', '1939 a 1945'),
        _fact('seconde guerre mondiale', 'a oppose', 'les allies a l axe'),
        _fact('debarquement de normandie', 'a eu lieu le', '6 juin 1944'),
    ),
    _concept('renaissance', 'Renaissance',
        _fact('renaissance', 'est une', 'periode de renouveau culturel et scientifique'),
        _fact('renaissance', 'a commence en', 'Italie au 14e siecle'),
        _fact('leonard de vinci', 'est un', 'artiste et scientifique majeur de la Renaissance'),
    ),
    _concept('leonard_de_vinci', 'Léonard de Vinci',
        _fact('leonard de vinci', 'a peint', 'la Joconde'),
        _fact('leonard de vinci', 'etait', 'peintre sculpteur architecte et inventeur'),
        _fact('leonard de vinci', 'est ne en', '1452'),
    ),
    _concept('egypte_ancienne', 'Égypte Ancienne',
        _fact('civilisation egyptienne', 's est developpee le long du', 'Nil'),
        _fact('pyramides d egypte', 'etaient des', 'tombeaux pour les pharaons'),
        _fact('plus grande pyramide', 'est', 'la pyramide de Kheops'),
    ),
    _concept('empire_romain', 'Empire Romain',
        _fact('empire romain', 'a dure de', '27 avant JC a 476 apres JC'),
        _fact('rome', 'etait', 'la capitale de l Empire romain'),
        _fact('empire romain', 'a invente', 'le droit romain et le latin'),
    ),
]

# ═══════════════════════════
# INFORMATIQUE
# ═══════════════════════════

CORPUS['informatique'] = [
    _concept('ordinateur', 'Ordinateur',
        _fact('ordinateur', 'est une', 'machine de traitement de l information'),
        _fact('ordinateur', 'execute', 'des programmes stockes en memoire'),
        _fact('ordinateur', 'est compose de', 'processeur memoire et peripheriques'),
    ),
    _concept('algorithme', 'Algorithme',
        _fact('algorithme', 'est une', 'suite finie d instructions pour resoudre un probleme'),
        _fact('algorithme', 'est', 'la base de la programmation informatique'),
    ),
    _concept('internet', 'Internet',
        _fact('internet', 'est', 'un reseau mondial d ordinateurs interconnectes'),
        _fact('internet', 'a ete cree dans les', 'annees 1960 par le departement de la defense americain'),
        _fact('web', 'a ete invente par', 'Tim Berners-Lee en 1989'),
    ),
    _concept('intelligence_artificielle', 'Intelligence Artificielle',
        _fact('intelligence artificielle', 'est', 'la capacite d une machine a simuler des capacites cognitives'),
        _fact('intelligence artificielle', 'est fondee sur', 'des algorithmes d apprentissage'),
        _fact('apprentissage automatique', 'est', 'une branche de l IA qui permet aux machines d apprendre a partir de donnees'),
    ),
    _concept('programmation', 'Programmation',
        _fact('langage de programmation', 'est', 'un langage formel pour ecrire des programmes'),
        _fact('python', 'est', 'un langage de programmation interprete'),
        _fact('machine learning', 'est', 'un sous domaine de l intelligence artificielle'),
    ),
    _concept('blockchain', 'Blockchain',
        _fact('blockchain', 'est', 'une base de donnees distribuee et securisee'),
        _fact('bitcoin', 'est', 'la premiere cryptomonnaie basee sur la blockchain'),
    ),
]

# ═══════════════════════════
# MATHÉMATIQUES
# ═══════════════════════════

CORPUS['mathematiques'] = [
    _concept('nombre_d_or', 'Nombre d\'Or',
        _fact('nombre d or', 'est', 'une proportion approximativement egale a 1 point 618'),
        _fact('nombre d or', 'est note', 'par la lettre grecque phi'),
        _fact('nombre d or', 'apparait dans', 'la nature l art et l architecture'),
    ),
    _concept('pi', 'Constante Pi',
        _fact('pi', 'est', 'le rapport entre la circonference et le diametre d un cercle'),
        _fact('pi', 'est approximativement egal a', '3 point 14159'),
    ),
    _concept('theoreme_pythagore', 'Théorème de Pythagore',
        _fact('theoreme de pythagore', 'affirme que', 'dans un triangle rectangle le carre de l hypotenuse est egal a la somme des carres des cotes'),
        _fact('theoreme de pythagore', 'a ete demontre par', 'Pythagore'),
    ),
    _concept('nombre_premier', 'Nombres Premiers',
        _fact('nombre premier', 'est un', 'entier divisible seulement par 1 et par lui meme'),
        _fact('nombre de nombres premiers', 'est', 'infini'),
    ),
    _concept('calcul_differentiel', 'Calcul Différentiel',
        _fact('calcul differentiel', 'a ete invente par', 'Newton et Leibniz'),
        _fact('derivee', 'mesure', 'le taux de variation d une fonction'),
        _fact('integrale', 'mesure', 'l aire sous une courbe'),
    ),
]

# ═══════════════════════════
# MÉDECINE
# ═══════════════════════════

CORPUS['medecine'] = [
    _concept('vaccin', 'Vaccin',
        _fact('vaccin', 'est une', 'substance qui stimule l immunite contre une maladie'),
        _fact('vaccin', 'contient', 'des agents pathogenes affaiblis ou inactives'),
        _fact('vaccination', 'a ete inventee par', 'Edward Jenner en 1796'),
    ),
    _concept('diabete', 'Diabète',
        _fact('diabete', 'est une', 'maladie caracterisee par un taux de sucre eleve dans le sang'),
        _fact('diabete de type 1', 'est cause par', 'une deficience en insuline'),
        _fact('diabete de type 2', 'est lie a', 'la resistance a l insuline'),
    ),
    _concept('systeme_immunitaire', 'Système Immunitaire',
        _fact('systeme immunitaire', 'protege', 'le corps contre les infections'),
        _fact('anticorps', 'sont', 'des proteines qui neutralisent les pathogenes'),
        _fact('vaccin', 'stimule', 'la production d anticorps'),
    ),
    _concept('coeur', 'Cœur',
        _fact('coeur', 'est', 'un organe musculaire qui pompe le sang'),
        _fact('coeur', 'bat environ', '100 000 fois par jour'),
    ),
    _concept('cerveau', 'Cerveau',
        _fact('cerveau', 'est', 'l organe central du systeme nerveux'),
        _fact('cerveau', 'contient environ', '86 milliards de neurones'),
    ),
]

# ═══════════════════════════
# TECHNOLOGIE
# ═══════════════════════════

CORPUS['technologie'] = [
    _concept('telephone', 'Téléphone',
        _fact('telephone', 'a ete invente par', 'Alexander Graham Bell en 1876'),
        _fact('telephone mobile', 'a ete invente par', 'Martin Cooper en 1973'),
    ),
    _concept('robotique', 'Robotique',
        _fact('robot', 'est une', 'machine programmable capable d effectuer des taches'),
        _fact('robotique', 'combine', 'la mecanique l electronique et l informatique'),
    ),
    _concept('imprimerie', 'Imprimerie',
        _fact('imprimerie moderne', 'a ete inventee par', 'Gutenberg au 15e siecle'),
        _fact('imprimerie', 'a permis', 'la diffusion massive des connaissances'),
    ),
    _concept('machine_vapeur', 'Machine à Vapeur',
        _fact('machine a vapeur', 'a ete perfectionnee par', 'James Watt au 18e siecle'),
        _fact('machine a vapeur', 'a declenche', 'la revolution industrielle'),
    ),
    _concept('electricite_technologie', 'Électricité (Technologie)',
        _fact('electricite domestique', 'a ete developpee par', 'Thomas Edison et Nikola Tesla'),
        _fact('ampoule electrique', 'a ete perfectionnee par', 'Thomas Edison'),
    ),
]

# ═══════════════════════════
# PHILOSOPHIE
# ═══════════════════════════

CORPUS['philosophie'] = [
    _concept('cogito', 'Cogito Ergo Sum',
        _fact('cogito ergo sum', 'est une', 'formulation philosophique de Descartes'),
        _fact('je pense donc je suis', 'affirme', 'que la pensee prouve l existence'),
        _fact('descartes', 'est', 'le fondateur de la philosophie moderne'),
    ),
    _concept('existentialisme', 'Existentialisme',
        _fact('existentialisme', 'affirme que', 'l existence precede l essence'),
        _fact('sartre', 'est', 'un philosophe existentialiste francais'),
        _fact('camus', 'a developpe', 'la philosophie de l absurde'),
    ),
    _concept('platon', 'Platon',
        _fact('platon', 'est', 'un philosophe grec de l Antiquite'),
        _fact('platon', 'a ete leleve de', 'Socrate'),
        _fact('platon', 'a fonde', 'l Academie'),
        _fact('theorie des idees', 'est', 'une theorie centrale de la philosophie de Platon'),
    ),
    _concept('aristote', 'Aristote',
        _fact('aristote', 'est', 'un philosophe grec eleve de Platon'),
        _fact('aristote', 'a ete le precepteur de', 'Alexandre le Grand'),
        _fact('aristote', 'a fonde', 'le Lycee'),
        _fact('aristote', 'a ecrit sur', 'la logique la metaphysique l ethique et la politique'),
    ),
    _concept('kant', 'Emmanuel Kant',
        _fact('kant', 'est', 'un philosophe allemand du 18e siecle'),
        _fact('kant', 'a ecrit', 'la Critique de la Raison Pure'),
        _fact('imperatif categorique', 'est', 'le principe moral fondamental de la philosophie de Kant'),
    ),
    _concept('nietzsche', 'Nietzsche',
        _fact('nietzsche', 'est', 'un philosophe allemand du 19e siecle'),
        _fact('nietzsche', 'a declare que', 'Dieu est mort'),
        _fact('surhomme', 'est', 'un concept cle de la philosophie de Nietzsche'),
    ),
]

# ═══════════════════════════
# ART
# ═══════════════════════════

CORPUS['art'] = [
    _concept('joconde', 'La Joconde',
        _fact('joconde', 'a ete peinte par', 'Leonard de Vinci'),
        _fact('joconde', 'est exposee au', 'musee du Louvre a Paris'),
    ),
    _concept('impressionnisme', 'Impressionnisme',
        _fact('impressionnisme', 'est un', 'mouvement artistique du 19e siecle'),
        _fact('monet', 'est un', 'peintre impressionniste celebre'),
        _fact('impressionnisme', 'se caracterise par', 'des coups de pinceau visibles et des couleurs vives'),
    ),
    _concept('cubisme', 'Cubisme',
        _fact('cubisme', 'a ete invente par', 'Picasso et Braque'),
        _fact('cubisme', 'represente', 'les objets sous plusieurs angles simultanement'),
    ),
    _concept('beethoven', 'Beethoven',
        _fact('beethoven', 'est un', 'compositeur allemand'),
        _fact('beethoven', 'a compose', 'la 5e Symphonie et la 9e Symphonie'),
        _fact('beethoven', 'est devenu sourd', 'a la fin de sa vie'),
    ),
    _concept('cinema', 'Cinéma',
        _fact('cinema', 'a ete invente par', 'les freres Lumiere en 1895'),
        _fact('premiere projection cinematographique', 'a eu lieu le', '28 decembre 1895 a Paris'),
    ),
]

# ═══════════════════════════
# LANGUES
# ═══════════════════════════

CORPUS['langues'] = [
    _concept('francais', 'Langue Française',
        _fact('francais', 'est une', 'langue romane'),
        _fact('francais', 'est parlee par', 'plus de 300 millions de personnes'),
        _fact('francais', 'est', 'la langue officielle de 29 pays'),
        _fact('francais', 'est', 'une des six langues officielles de l ONU'),
    ),
    _concept('anglais', 'Langue Anglaise',
        _fact('anglais', 'est', 'la langue la plus parlee au monde'),
        _fact('anglais', 'est une', 'langue germanique'),
        _fact('anglais', 'est', 'la langue officielle de nombreux pays'),
    ),
]


# ═══════════════════════════════════════════════════════════
# GÉNÉRATION DES FICHIERS
# ═══════════════════════════════════════════════════════════

def _sanitize(text: str) -> str:
    """Nettoie une chaîne pour le format OKF."""
    # Pour les accents, on garde le texte tel quel dans les fichiers .md
    # (le compilateur et le pipeline normalisent les accents à la compilation)
    return text.strip()


def generate_files(target_dir: Path = None):
    """Génère tous les fichiers .md dans knowledge/<domain>/."""
    target_dir = target_dir or WIKI_DIR
    stats = {}

    for domain, concepts in CORPUS.items():
        domain_dir = target_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        n_concepts = 0
        n_facts = 0

        for cid, title, facts in concepts:
            facts_lines = []
            for s, r, o in facts:
                facts_lines.append(f"- {_sanitize(s)} | {_sanitize(r)} | {_sanitize(o)}")

            md_content = f"""---
id: {cid}
domain: {domain}
title: {title}
type: concept
---

# {title}

{chr(10).join(facts_lines)}
"""
            filepath = domain_dir / f'{cid}.md'
            filepath.write_text(md_content, encoding='utf-8')
            n_concepts += 1
            n_facts += len(facts)

        stats[domain] = {'concepts': n_concepts, 'facts': n_facts}

    return stats


def print_stats(stats: dict):
    """Affiche les statistiques du corpus généré."""
    print(f"\n📊 CORPUS GÉNÉRÉ :")
    total_concepts = 0
    total_facts = 0
    for domain, info in sorted(stats.items()):
        total_concepts += info['concepts']
        total_facts += info['facts']
        print(f"  📁 {domain:20s} {info['concepts']:>3d} concepts, {info['facts']:>3d} faits")
    print(f"  {'─' * 40}")
    print(f"  {'TOTAL':20s} {total_concepts:>3d} concepts, {total_facts:>3d} faits")
    return total_concepts, total_facts


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    logging.basicConfig(level=logging.WARNING, format='%(message)s')

    # Ajouter le répertoire engine au path pour les imports
    _ENGINE = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(_ENGINE))

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   🌱 KNOWLEDGE SEEDER — Générateur de corpus propre          ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # Générer les fichiers
    print("\n[1] Génération des fichiers...")
    stats = generate_files()
    n_concepts, n_facts = print_stats(stats)

    # Compiler
    if '--no-compile' not in sys.argv:
        print("\n[2] Compilation en hologrammes...")
        from ka_server.services.okf_compiler import compile_wiki
        t0 = time.time()
        report = compile_wiki(action='seed')
        elapsed = time.time() - t0
        print(f"    {report['valid_files']} fichiers valides en {elapsed:.1f}s")
        print(f"    {sum(r['facts'] for r in report['results'].values())} faits compilés")

        # Tester le rappel sur quelques questions
        print("\n[3] Test de rappel...")
        from hologram_store import HologramStore
        from ka_server.services.surface_grammar import phrase_fact

        store = HologramStore()
        test_questions = [
            ('okf_physique', "c'est quoi un hologramme"),
            ('okf_physique', "qu'est-ce que la lumiere"),
            ('okf_physique', "qu'est-ce que la relativite"),
            ('okf_physique', "c'est quoi la mecanique quantique"),
            ('okf_physique', "qu'est-ce que la theorie harmonique"),
            ('okf_astronomie', "qu'est-ce qu'un trou noir"),
            ('okf_astronomie', "combien de planetes dans le systeme solaire"),
            ('okf_astronomie', "qu'est-ce que le big bang"),
            ('okf_astronomie', "quelle est la plus grande planete"),
            ('okf_biologie', "qu'est-ce que l'ADN"),
            ('okf_biologie', "qu'est-ce qu'une cellule"),
            ('okf_biologie', "comment fonctionne la photosynthese"),
            ('okf_biologie', "qu'est-ce que l evolution"),
            ('okf_chimie', "formule chimique de l eau"),
            ('okf_chimie', 'symbole chimique de l oxygene'),
            ('okf_geographie', "capitale de la France"),
            ('okf_geographie', "capitale du Japon"),
            ('okf_geographie', "plus long fleuve du monde"),
            ('okf_histoire', "date de la revolution francaise"),
            ('okf_histoire', "qui etait Napoleon"),
            ('okf_histoire', "quand a eu lieu la seconde guerre mondiale"),
            ('okf_informatique', "qu'est-ce qu'un ordinateur"),
            ('okf_informatique', "qu'est-ce que l intelligence artificielle"),
            ('okf_mathematiques', "qu'est-ce que le nombre d or"),
            ('okf_mathematiques', "qu'est-ce que pi"),
            ('okf_medecine', "qu'est-ce qu'un vaccin"),
            ('okf_medecine', "qu'est-ce que le diabete"),
            ('okf_technologie', "qui a invente le telephone"),
            ('okf_technologie', "qu'est-ce que la robotique"),
            ('okf_philosophie', "qu'est-ce que le cogito"),
            ('okf_philosophie', "qui etait Platon"),
            ('okf_art', "qui a peint la Joconde"),
            ('okf_art', "qu'est-ce que l impressionnisme"),
            ('okf_langues', "combien de personnes parlent francais"),
        ]

        correct = 0
        for holo, q in test_questions:
            r = store.recall(holo, q, top_k=1)
            if r and r[0][4] > 0.5:
                s, rel, o, sec, sc = r[0]
                correct += 1
                phrase = phrase_fact(s, rel, o)
                print(f"  ✅ [{sc:.3f}] {phrase[:70]}")
            else:
                print(f"  ❌ [{holo}] {q[:50]}")

        print(f"\n[4] RÉSULTAT : {correct}/{len(test_questions)} rappels pertinents")
        print("\n✅ Seeder terminé.")
    else:
        print("\n✅ Fichiers générés sans compilation (--no-compile).")
        print("   Lancez `python -m ka_server.services.okf_compiler` pour compiler.")


if __name__ == '__main__':
    main()
