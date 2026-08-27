"""
🌊 concepts_corpus.py — Corpus de définitions curées (concepts de base)
========================================================================
Le shard Wikidata (shard_0000.npz) ne contient PAS de définitions — uniquement
des données géographiques/organisationnelles. Ce module fournit un corpus
curé de concepts fondamentaux au format (sujet, relation, objet), prêt à être
encodé en hologramme wave-native.

Chaque concept = 2 à 5 faits (définition + propriétés clés), rédigés en
français, vérifiés, sans accent (le pipeline wave normalise les accents).

Usage :
    from ka_server.services.concepts_corpus import CONCEPTS
    # CONCEPTS = { 'physique': [(sujet, relation, objet), ...], ... }
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CORPUS DE DÉFINITIONS — organisé par domaine
# ═══════════════════════════════════════════════════════════════════════════════

CONCEPTS = {
    'physique': [
        # Hologramme (le concept clé du projet)
        ('hologramme', 'est une', 'figure d interference qui stocke une image en trois dimensions'),
        ('hologramme', 'est cree par', 'l interference de deux faisceaux laser'),
        ('hologramme', 'a ete invente par', 'Dennis Gabor en 1947'),
        ('holographie', 'est utilisee pour', 'le stockage optique de donnees en trois dimensions'),
        ('holographie', 'permet de', 'restituer une image en trois dimensions'),
        # Lumière
        ('lumiere', 'est une', 'onde electromagnetique'),
        ('lumiere', 'est composee de', 'particules appelees photons'),
        ('lumiere', 'a pour vitesse', '299 792 458 metres par seconde dans le vide'),
        ('lumiere', 'est', 'le rayonnement electromagnetique visible par l oeil humain'),
        # Gravité
        ('gravite', 'est une', 'force d attraction entre les masses'),
        ('gravite', 'est decrite par', 'la loi de la gravitation universelle de Newton'),
        ('gravite', 'est expliquee par', 'la courbure de l espace temps dans la relativite generale'),
        # Atome
        ('atome', 'est', 'la plus petite unite de la matiere'),
        ('atome', 'est compose de', 'protons neutrons et electrons'),
        ('atome', 'a un noyau', 'charge positivement entoure d electrons'),
        # Énergie
        ('energie', 'est', 'la capacite a produire un travail'),
        ('energie', 'se mesure en', 'joules'),
        ('energie', 'est conservee', 'selon le principe de conservation de l energie'),
        # Électricité
        ('electricite', 'est', 'le deplacement de charges electriques'),
        ('electricite', 'est generee par', 'le mouvement des electrons'),
        # Magnétisme
        ('magnetisme', 'est', 'la force exercee par les aimants'),
    ],
    'astronomie': [
        ('trou noir', 'est une', 'region de l espace ou la gravite est si forte que rien ne s en echappe'),
        ('trou noir', 'est forme par', 'l effondrement d une etoile massive'),
        ('trou noir', 'a ete predit par', 'la theorie de la relativite generale'),
        # Système solaire
        ('systeme solaire', 'est compose de', 'huit planetes orbitant autour du soleil'),
        ('systeme solaire', 'contient', 'le soleil les planetes et leurs satellites'),
        # Planète / étoile / galaxie
        ('planete', 'est un', 'corps celeste en orbite autour d une etoile'),
        ('planete', 'ne produit pas', 'sa propre lumiere'),
        ('etoile', 'est un', 'astre qui produit sa propre lumiere'),
        ('etoile', 'produit de l energie', 'par fusion nucleaire'),
        ('galaxie', 'est un', 'ensemble d etoiles de gaz et de poussiere'),
        ('voie lactee', 'est', 'la galaxie qui contient le systeme solaire'),
    ],
    'biologie': [
        ('adn', 'est une', 'molecule qui porte l information genetique'),
        ('adn', 'signifie', 'acide desoxyribonucleique'),
        ('adn', 'se trouve dans', 'le noyau des cellules'),
        ('adn', 'est forme de', 'deux brins en double helice'),
        # Cellule
        ('cellule', 'est', 'l unite de base du vivant'),
        ('cellule', 'est composee de', 'membrane cytoplasme et noyau'),
        ('cellule', 'est', 'la plus petite unite capable de se reproduire'),
        # Protéine / enzyme
        ('proteine', 'est une', 'molecule composee d acides amines'),
        ('enzyme', 'est une', 'proteine qui accelere les reactions chimiques'),
        # Virus / bactérie
        ('virus', 'est un', 'micro organisme qui a besoin d une cellule hote pour se reproduire'),
        ('bacterie', 'est un', 'micro organisme unicellulaire'),
        # Photosynthèse
        ('photosynthese', 'est', 'le processus par lequel les plantes produisent leur energie'),
        ('photosynthese', 'utilise', 'la lumiere le dioxyde de carbone et l eau'),
    ],
    'informatique': [
        ('ordinateur', 'est une', 'machine de traitement de l information'),
        ('ordinateur', 'execute', 'des programmes stockes en memoire'),
        ('ordinateur', 'est compose de', 'processeur memoire et peripheriques'),
        # Algorithme
        ('algorithme', 'est une', 'suite finie d instructions pour resoudre un probleme'),
        ('algorithme', 'est', 'la base de la programmation informatique'),
        # Internet
        ('internet', 'est', 'un reseau mondial d ordinateurs interconnectes'),
        ('internet', 'utilise', 'le protocole de communication'),
        # Programmation / langage
        ('programme', 'est une', 'sequence d instructions executees par un ordinateur'),
        ('langage de programmation', 'est', 'un langage formel pour ecrire des programmes'),
        # Intelligence artificielle
        ('intelligence artificielle', 'est', 'la capacite d une machine a simuler des capacites cognitives'),
        ('intelligence artificielle', 'est fondee sur', 'des algorithmes d apprentissage'),
    ],
    'geographie': [
        ('pays', 'est un', 'territoire delimite par des frontieres'),
        ('pays', 'a une', 'capitale qui est sa ville principale'),
        ('capitale', 'est', 'la ville principale d un pays'),
        ('continent', 'est une', 'grande etendue de terre separee des autres'),
        ('ocean', 'est une', 'grande etendue d eau salee'),
        ('montagne', 'est un', 'relief eleve de la surface terrestre'),
        ('fleuve', 'est', 'un cours d eau qui se jette dans la mer'),
    ],
    'chimie': [
        ('molecule', 'est une', 'assemblage d atomes lies entre eux'),
        ('element chimique', 'est', 'une substance composee d un seul type d atome'),
        ('reaction chimique', 'est', 'la transformation de substances en d autres substances'),
        ('oxygene', 'a pour symbole chimique', 'O'),
        ('hydrogene', 'a pour symbole chimique', 'H'),
        ('carbone', 'a pour symbole chimique', 'C'),
        ('eau', 'a pour formule chimique', 'H2O'),
    ],
    'mathematiques': [
        ('nombre premier', 'est', 'un entier divisible seulement par 1 et par lui meme'),
        ('nombre d or', 'est', 'une proportion approximativement egale a 1.618'),
        ('nombre d or', 'est note', 'par la lettre grecque phi'),
        ('nombre d or', 'apparait dans', 'la nature l art et l architecture'),
        ('pi', 'est', 'le rapport entre la circonference et le diametre d un cercle'),
        ('pi', 'est approximativement egal a', '3.14159'),
    ],
    'medecine': [
        ('infection', 'est', 'l invasion d un organisme par des micro organismes'),
        ('vaccin', 'est une', 'substance qui stimule l immunite contre une maladie'),
        ('diabete', 'est une', 'maladie caracterisee par un taux de sucre eleve dans le sang'),
        ('symptome', 'est', 'un signe observable d une maladie'),
        ('diagnostic', 'est', 'l identification d une maladie'),
    ],
}


def all_triplets() -> list:
    """Aplatit le corpus en liste plate de triplets + domaine."""
    out = []
    for domain, facts in CONCEPTS.items():
        for s, r, o in facts:
            out.append((domain, s, r, o))
    return out


def stats() -> dict:
    """Statistiques du corpus."""
    return {
        'domains': len(CONCEPTS),
        'concepts': sum(len(f) for f in CONCEPTS.values()),
        'per_domain': {d: len(f) for d, f in CONCEPTS.items()},
    }


if __name__ == '__main__':
    s = stats()
    print(f"Concepts: {s['concepts']} dans {s['domains']} domaines")
    for d, n in s['per_domain'].items():
        print(f"  {d:15s} {n:>3d} faits")
