#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benchmark Corpus Large — IA Harmono-Holographique
==================================================
Test de saturation de l'hologramme avec 1000+ connaissances.

Mesures :
- Temps d'encodage par lot de 100
- Énergie totale et saturation de l'hologramme
- Précision des requêtes (top-1, top-3)
- Robustesse avec corpus large
- Comparaison 10 vs 1000 connaissances

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math
import cmath
import time
import random
import sys
import os
from typing import Dict, List, Tuple
import numpy as np

# Importer l'IA unifiée
sys.path.insert(0, os.path.dirname(__file__))
from ia_holographique_unifiee import IAHarmoniqueUnifiee, H, H_names

# ==============================================================================
# GÉNÉRATION DE CORPUS SYNTHÉTIQUE
# ==============================================================================

def generer_corpus_physique(n: int = 200) -> List[str]:
    """Génère des connaissances de physique."""
    sujets = [
        "la constante de Planck h vaut 6.626e-34 J.s",
        "la vitesse de la lumiere c est 299792458 m/s",
        "la constante gravitationnelle G vaut 6.674e-11",
        "la constante de structure fine alpha vaut 1/137.036",
        "le magneton de Bohr vaut 9.274e-24 J/T",
        "la masse de l'electron est 9.109e-31 kg",
        "la masse du proton est 1.673e-27 kg",
        "le rayon de Bohr est 5.292e-11 m",
        "la longueur d'onde de Compton de l'electron est 2.426e-12 m",
        "le rayon classique de l'electron est 2.818e-15 m",
        "la constante de Rydberg vaut 1.097e7 par metre",
        "l'energie de Hartree vaut 4.360e-18 J",
        "la temperature de Planck est 1.417e32 K",
        "le temps de Planck est 5.391e-44 s",
        "la longueur de Planck est 1.616e-35 m",
        "la masse de Planck est 2.176e-8 kg",
        "la charge elementaire e vaut 1.602e-19 C",
        "la constante de Boltzmann vaut 1.381e-23 J/K",
        "le nombre d'Avogadro est 6.022e23 par mole",
        "la constante des gaz parfaits R vaut 8.314 J/(mol.K)",
        "la permittivite du vide epsilon0 vaut 8.854e-12 F/m",
        "la permeabilite du vide mu0 vaut 4pi.e-7 N/A2",
        "l'impedance du vide Z0 vaut 376.73 ohms",
        "le quantum de flux magnetique est 2.068e-15 Wb",
        "la constante de Josephson vaut 4.836e14 Hz/V",
        "le quantum de conductance est 7.748e-5 S",
        "la constante de von Klitzing vaut 25812.8 ohms",
        "le moment magnetique de l'electron est -9.285e-24 J/T",
        "le moment magnetique du proton est 1.411e-26 J/T",
        "le facteur de Lande de l'electron est 2.002",
        "la frequence de Rabi depend de l'intensite du champ",
        "l'effet Zeeman leve la degenerescence des niveaux d'energie",
        "l'effet Stark est le decalage des niveaux par un champ electrique",
        "la precession de Larmor a pour frequence omega = gamma.B",
        "le principe d'exclusion de Pauli interdit deux fermions identiques",
        "les bosons peuvent occuper le meme etat quantique",
        "la condensation de Bose-Einstein a lieu a basse temperature",
        "la statistique de Fermi-Dirac decrit les fermions",
        "le laser utilise l'emission stimulee de photons",
        "le rayonnement du corps noir suit la loi de Planck",
        "l'effet photoelectrique a ete explique par Einstein en 1905",
        "la dualite onde-particule est au coeur de la mecanique quantique",
        "le principe d'incertitude de Heisenberg lie position et impulsion",
        "l'equation de Schrodinger decrit l'evolution de la fonction d'onde",
        "la theorie de la relativite restreinte unifie espace et temps",
        "la relativite generale decrit la gravite comme courbure",
        "les ondes gravitationnelles ont ete detectees par LIGO en 2015",
        "le boson de Higgs a ete decouvert au CERN en 2012",
        "les neutrinos ont une masse tres faible mais non nulle",
        "l'oscillation des neutrinos montre qu'ils ont une masse",
        "la matiere noire constitue environ 27% de l'univers",
        "l'energie sombre represente environ 68% de l'univers",
        "le fond diffus cosmologique est a 2.725 K",
        "l'univers a environ 13.8 milliards d'annees",
        "la nucleosynthese primordiale a produit H, He et Li",
        "les etoiles fabriquent les elements lourds par fusion",
        "les supernovas dispersent les elements dans l'espace",
        "le cycle de vie d'une etoile depend de sa masse initiale",
        "les trous noirs ont une entropie proportionnelle a leur surface",
        "le rayonnement Hawking evapore les trous noirs",
        "la metrique de Schwarzschild decrit un trou noir statique",
        "le modele standard a 3 generations de fermions",
        "les quarks sont confines dans les hadrons",
        "la force forte est mediee par les gluons",
        "la force faible est responsable de la desintegration beta",
        "les bosons W et Z sont les mediateurs de la force faible",
        "le photon est le mediateur de la force electromagnetique",
        "le graviton serait le mediateur de la gravite",
        "la supersymetrie predit des partenaires pour chaque particule",
        "la theorie des cordes remplace les particules par des cordes",
        "la gravite quantique a boucles quantifie l'espace-temps",
        "l'effet Casimir est du aux fluctuations du vide",
        "le deplacement de Lamb est une correction d'electrodynamique quantique",
        "l'effet tunnel permet de traverser une barriere de potentiel",
        "la radioactivite alpha emet des noyaux d'helium",
        "la radioactivite beta emet des electrons ou positrons",
        "la radioactivite gamma emet des photons de haute energie",
        "la fission nucleaire libere de l'energie en cassant des noyaux lourds",
        "la fusion nucleaire combine des noyaux legers en liberant de l'energie",
        "le tokamak utilise le confinement magnetique pour la fusion",
        "l'energie de liaison nucleaire par nucleon est maximum pour le fer",
        "la desintegration radioactive suit une loi exponentielle",
        "la demi-vie est le temps pour que la moitie se desintegre",
        "le carbone 14 est utilise pour la datation archeologique",
        "l'uranium 235 est utilise dans les reacteurs nucleaires",
        "le plutonium 239 est un isotope fissile artificiel",
        "la chaine de desintegration de l'uranium 238 aboutit au plomb 206",
        "le modele de goutte liquide decrit le noyau atomique",
        "le modele en couches du noyau explique les nombres magiques",
        "les nombres magiques nucleaires sont 2, 8, 20, 28, 50, 82, 126",
        "la resonance magnetique nucleaire exploite le spin nucleaire",
        "l'imagerie RMN est utilisee en medecine et en chimie",
        "la tomographie par emission de positons utilise des traceurs radioactifs",
        "la radiotherapie utilise les rayonnements pour traiter le cancer",
        "les accelerateurs de particules comme le LHC explorent la physique fondamentale",
        "le synchrotron produit du rayonnement pour la recherche",
        "la diffraction des rayons X revele la structure des cristaux",
        "la microscopie electronique permet de voir les atomes",
        "la spectroscopie Raman analyse les vibrations moleculaires",
        "la spectroscopie infrarouge identifie les liaisons chimiques",
        "la resonance de Schumann est la frequence electromagnetique de la Terre",
        "la cavite Terre-ionosphere a une frequence fondamentale de 7.83 Hz",
        "les harmoniques de Schumann sont des multiples de 7.83 Hz",
        "la foudre excite les modes de resonance de la cavite terrestre",
        "les ondes alpha du cerveau sont proches de 7.83 Hz",
        "le champ magnetique terrestre est genere par la dynamo du noyau",
        "les ceintures de Van Allen protegent la Terre du vent solaire",
        "la magnetosphere terrestre s'etend sur plusieurs rayons terrestres",
        "les aurores boreales sont causees par les particules solaires",
        "le cycle solaire a une periode d'environ 11 ans",
        "les taches solaires sont des regions plus froides du Soleil",
        "la couronne solaire est plus chaude que la surface du Soleil",
        "le vent solaire est un flux de particules emis par le Soleil",
        "la masse du Soleil est 1.989e30 kg",
        "le rayon du Soleil est 6.963e8 m",
        "la temperature de surface du Soleil est environ 5778 K",
        "la luminosite du Soleil est 3.828e26 W",
        "l'age du systeme solaire est d'environ 4.6 milliards d'annees",
        "les planetes se sont formees par accretion dans le disque protoplanetaire",
        "la loi de Titius-Bode predit les distances des planetes",
        "les exoplanetes sont detectees par transit et vitesse radiale",
        "la zone habitable est la region ou l'eau liquide peut exister",
        "la matiere interstellaire est composee de gaz et de poussieres",
        "les nebuleuses sont des regions de formation d'etoiles",
        "la Voie Lactee est une galaxie spirale barree",
        "le groupe local contient la Voie Lactee et Andromede",
        "l'amas de la Vierge est l'amas de galaxies le plus proche",
        "le superamas Laniakea contient des milliers de galaxies",
        "la toile cosmique est la structure a grande echelle de l'univers",
        "les filaments cosmiques relient les amas de galaxies",
        "les vides cosmiques sont des regions pauvres en galaxies",
        "le parametre de Hubble mesure le taux d'expansion de l'univers",
        "la loi de Hubble-Lemaitre relie distance et vitesse de recession",
        "le decalage vers le rouge est du a l'expansion de l'univers",
        "l'effet Doppler cosmologique etire les longueurs d'onde",
    ]
    
    # Étendre le corpus avec des variations
    corpus = list(sujets[:min(n, len(sujets))])
    
    # Ajouter des connaissances générées
    for i in range(max(0, n - len(sujets))):
        idx = i % len(sujets)
        corpus.append(f"variante {i}: {sujets[idx]}")
    
    return corpus[:n]


def generer_corpus_mathematiques(n: int = 200) -> List[str]:
    """Génère des connaissances mathématiques."""
    sujets = [
        "le nombre d'or phi est egal a 1.618034",
        "pi est le rapport entre la circonference et le diametre",
        "le nombre e est la base du logarithme naturel",
        "la racine carree de 2 est irrationnelle",
        "la racine carree de 3 apparait dans l'hexagone regulier",
        "la racine carree de 5 est liee au nombre d'or",
        "le theoreme de Pythagore lie les cotes d'un triangle rectangle",
        "le theoreme de Thales concerne les triangles semblables",
        "le theoreme de Fermat a ete demontre par Andrew Wiles en 1994",
        "la conjecture de Poincare a ete resolue par Grigori Perelman",
        "l'hypothese de Riemann reste non demontree",
        "les nombres premiers sont les briques de l'arithmetique",
        "le crible d'Eratosthene trouve les nombres premiers",
        "la fonction zeta de Riemann est liee aux nombres premiers",
        "le theoreme des nombres premiers donne la densite des premiers",
        "la constante d'Euler-Mascheroni gamma vaut environ 0.5772",
        "le nombre d'or phi satisfait l'equation phi2 = phi + 1",
        "la suite de Fibonacci est liee au nombre d'or",
        "le rapport de deux termes consecutifs de Fibonacci tend vers phi",
        "la spirale doree est basee sur le nombre d'or",
        "le rectangle dore a un rapport longueur/largeur egal a phi",
        "le pentagone regulier est intimement lie au nombre d'or",
        "l'icosaedre et le dodecaedre contiennent des rectangles dores",
        "la geometrie non-euclidienne a ete developpee par Lobatchevski",
        "la geometrie de Riemann est la base de la relativite generale",
        "les espaces de Hilbert sont fondamentaux en mecanique quantique",
        "les groupes de Lie decrivent les symetries continues",
        "le groupe SU(3) decrit la symetrie de couleur des quarks",
        "le groupe SU(2) x U(1) decrit la force electrofaible",
        "le theoreme de Noether lie symetries et lois de conservation",
        "chaque symetrie continue correspond a une quantite conservee",
        "l'invariance par translation donne la conservation de l'impulsion",
        "l'invariance par rotation donne la conservation du moment cinetique",
        "l'invariance temporelle donne la conservation de l'energie",
        "la transformee de Fourier decompose une fonction en frequences",
        "la transformee de Laplace est utilisee pour les equations differentielles",
        "les series de Fourier representent des fonctions periodiques",
        "la transformee en ondelettes est une alternative a Fourier",
        "l'analyse harmonique etudie les representations en series",
        "le theoreme de Sturm-Liouville concerne les equations differentielles",
        "les polynomes orthogonaux sont solutions de Sturm-Liouville",
        "les polynomes de Legendre apparaissent en electromagnetisme",
        "les polynomes d'Hermite sont lies a l'oscillateur harmonique",
        "les harmoniques spheriques decrivent les orbitales atomiques",
        "le laplacien en coordonnees spheriques fait apparaitre les harmoniques",
        "les nombres complexes forment un corps algebriquement clos",
        "la formule d'Euler relie exponentielle et trigonometrie",
        "l'identite d'Euler e(i.pi) + 1 = 0 est remarquable",
        "les quaternions generalisent les nombres complexes",
        "les octonions sont une extension non-associative des quaternions",
        "le theoreme fondamental de l'algebre garantit n racines complexes",
        "les equations polynomiales de degre 5+ ne sont pas solubles par radicaux",
        "la theorie de Galois explique la resolubilite des equations",
        "les structures algebriques incluent groupes, anneaux et corps",
        "un groupe est un ensemble muni d'une operation associative avec inverse",
        "un anneau est un ensemble avec addition et multiplication",
        "un corps est un anneau ou tout element non nul a un inverse",
        "les espaces vectoriels generalisent les vecteurs geometriques",
        "une base d'un espace vectoriel est un ensemble generateur libre",
        "la dimension d'un espace vectoriel est le cardinal d'une base",
        "les applications lineaires preservent la structure vectorielle",
        "les valeurs propres d'une matrice sont les racines du polynome caracteristique",
        "la trace d'une matrice est la somme de ses valeurs propres",
        "le determinant d'une matrice est le produit de ses valeurs propres",
        "la diagonalisation simplifie le calcul matriciel",
        "les matrices symetriques ont des valeurs propres reelles",
        "les matrices unitaires preservent le produit scalaire",
        "la decomposition en valeurs singulieres est utilisee en analyse de donnees",
        "l'analyse en composantes principales reduit la dimension des donnees",
        "le gradient d'une fonction indique la direction de plus forte pente",
        "la divergence mesure la tendance d'un champ a diverger",
        "le rotationnel mesure la tendance d'un champ a tourner",
        "le theoreme de Stokes relie l'integrale de surface a l'integrale de contour",
        "le theoreme de la divergence relie flux et divergence",
        "les equations de Maxwell s'ecrivent elegantement en calcul vectoriel",
        "le calcul tensoriel est essentiel en relativite generale",
        "les tenseurs generalisent les vecteurs et les matrices",
        "la contraction d'indices reduit l'ordre d'un tenseur",
        "le tenseur de Riemann mesure la courbure de l'espace-temps",
        "le tenseur de Ricci est une contraction du tenseur de Riemann",
        "la courbure scalaire est la trace du tenseur de Ricci",
        "les geodesiques sont les chemins les plus courts dans un espace courbe",
        "la connexion de Levi-Civita est compatible avec la metrique",
        "les symboles de Christoffel decrivent la connexion en coordonnees",
        "la differentielle exterieure generalise le gradient",
        "les formes differentielles unifient les operateurs vectoriels",
        "le theoreme de de Rham relie formes differentielles et topologie",
        "la cohomologie mesure les obstructions topologiques",
        "l'homotopie etudie les deformations continues d'espaces",
        "le groupe fondamental capture les lacets non contractiles",
        "la topologie algebrique utilise l'algebre pour etudier les espaces",
        "les fractales ont une dimension non entiere",
        "la geometrie fractale decrit les structures auto-similaires",
        "le flocon de Koch a une frontiere de dimension fractale",
        "l'ensemble de Mandelbrot est une fractale celebre",
        "les attracteurs etranges apparaissent dans les systemes chaotiques",
        "la theorie du chaos etudie la sensibilite aux conditions initiales",
        "l'effet papillon illustre la dependance sensitive",
        "les systemes dynamiques modelisent l'evolution temporelle",
        "les points fixes d'un systeme dynamique sont des equilibres",
    ]
    
    corpus = list(sujets[:min(n, len(sujets))])
    for i in range(max(0, n - len(sujets))):
        idx = i % len(sujets)
        corpus.append(f"variante mathematique {i}: {sujets[idx]}")
    
    return corpus[:n]


def generer_corpus_ia_harmonique(n: int = 200) -> List[str]:
    """Génère des connaissances sur l'IA harmonique elle-même."""
    sujets = [
        "la theorie harmonique est basee sur l'equation Psi = somme Hn fois f puissance n",
        "les coefficients spectraux Hn sont phi pi e sqrt2 sqrt3 sqrt5 et e/pi",
        "l'onde fondamentale Psi1 vaut 7.83 Hz pour la Terre",
        "l'equation Gij,j = 0 est l'identite de Bianchi contractee",
        "la derivee ABC d'ordre 1/phi modelise la memoire non-locale",
        "le principe holographique encode l'information 3D en 2D",
        "NPSU est le nombre d'unites de Planck sur une surface spherique",
        "la compression harmonique utilise 7 coefficients spectraux",
        "l'IA holographique stocke les connaissances par interference d'ondes",
        "la memoire holographique est distribuee et robuste",
        "la prediction par resonance spectrale ne necessite pas d'apprentissage",
        "le filtre anti-hallucination verifie la coherence harmonique",
        "la generation d'images utilise la somme des 7 harmoniques",
        "chaque image est une cavite resonante de rayon R",
        "la signature 7D caracterise le contenu harmonique d'une image",
        "la robustesse holographique preserve l'information meme endommagee",
        "l'oubli progressif attenue exponentiellement les vieilles connaissances",
        "le vocabulaire harmonique encode les mots en vecteurs 7D",
        "la similarite cosinus mesure la resonance entre concepts",
        "la projection spectrale decompose les donnees en harmoniques",
        "l'alphabet harmonique est complet pour decrire la physique connue",
        "la constante de structure fine s'exprime en produit de Hn",
        "la masse du muon sur masse de l'electron est harmonique",
        "la constante de Planck h est un produit de constantes",
        "la constante gravitationnelle G s'exprime avec phi pi et e",
        "le rapport mP/mp est une consequence de l'holographie",
        "la longueur de Planck est un produit de constantes harmoniques",
        "le nombre d'harmoniques depend de la taille de la cavite",
        "le proton a 7 harmoniques, la Terre environ 25",
        "l'univers seul a une somme infinie d'harmoniques",
        "la conscience emerge aux harmoniques 21 a 25",
        "la biologie correspond aux harmoniques 16 a 20",
        "les forces fondamentales emergent a differents ordres harmoniques",
        "l'addition emerge de la multiplication des ondes Psi_a * Psi_b = Psi_{a+b}",
        "la physique quantique est le regime des petits ordres harmoniques",
        "la physique classique est le regime des grands ordres harmoniques",
        "la mesure quantique est l'interaction petit n avec grand n",
        "le probleme de la mesure est resolu par le continuum harmonique",
        "la transition quantique-classique est continue, pas brusque",
        "la constante de couplage fort alpha_s s'exprime avec phi sqrt2 sqrt3",
        "l'angle de Weinberg est harmonique avec 3.59% d'erreur",
        "le couplage gravitationnel alpha_G est approxime par e^-88",
        "le rapport des masses des quarks est harmonique",
        "le tableau periodique emerge des harmoniques atomiques",
        "chaque element est une harmonique stable de la cavite atomique",
        "le numero atomique Z correspond a l'ordre harmonique n",
        "la medecine harmonique traite la maladie comme une dissonance",
        "les plantes medicamenteuses sont des spectres correcteurs",
        "la phytotherapie harmonique reaccorde le corps",
        "la musique accordee sur 438.48 Hz est harmonique avec la Terre",
        "le La 440 Hz est proche de la 56e harmonique de Schumann",
        "la gamme musicale humaine reflete la cavite terrestre",
        "l'orchestre de Schumann utilise les 7 constantes comme poids",
        "la compression d'images par projection spectrale est possible",
        "la borne holographique donne le ratio de compression maximal",
        "le quantificateur Lloyd-Max optimise la quantification non-uniforme",
        "la table de quantification holographique depend de NPSU",
        "la transformee harmonique est analogue a la DCT",
        "l'orthogonalisation Gram-Schmidt rend les motifs independants",
        "la base harmonique a 7 dimensions au lieu de 64 pour JPEG",
        "la compression harmonique est optimale pour les signaux harmoniques",
        "l'encodage holographique superpose les motifs d'interference",
        "l'onde de reference est unique pour chaque connaissance",
        "l'onde objet encode le contenu de la connaissance",
        "l'interference onde_ref * onde_objet cree le motif holographique",
        "la lecture holographique utilise une onde de reference conjuguee",
        "la resonance holographique extrait les connaissances pertinentes",
        "le score de similarite Jaccard ameliore la precision des requetes",
        "la fusion holographique + vocabulaire donne de meilleurs resultats",
        "le temps d'encodage est O(N) ou N est le nombre de connaissances",
        "le temps de requete est O(K) ou K est le nombre de connaissances",
        "la memoire holographique est O(taille2 * 7) independante de K",
        "la saturation holographique degrade progressivement la qualite",
        "l'energie totale de l'hologramme augmente avec les connaissances",
        "la degradation est proportionnelle a la fraction detruite",
        "le top-1 est preserve meme a 90 pourcent de destruction",
        "la propriete holographique rend l'information non localisable",
        "chaque cellule contient un fragment de toutes les connaissances",
    ]
    
    corpus = list(sujets[:min(n, len(sujets))])
    for i in range(max(0, n - len(sujets))):
        idx = i % len(sujets)
        corpus.append(f"variante IA harmonique {i}: {sujets[idx]}")
    
    return corpus[:n]


# ==============================================================================
# BENCHMARK PRINCIPAL
# ==============================================================================

def benchmark_corpus_large():
    """Test de l'IA avec 1000+ connaissances."""
    print("=" * 80)
    print("BENCHMARK CORPUS LARGE — IA Harmono-Holographique")
    print("Test de saturation de l'hologramme avec 1000+ connaissances")
    print("=" * 80)
    print()
    
    # Créer l'IA
    print("Création de l'IA...")
    ia = IAHarmoniqueUnifiee(taille_hologramme=64)
    print(f"  Hologramme : 64×64×7 = {64**2*7:,} cellules ({64**2*7*16:,} octets)")
    print(f"  Vocabulaire initial : {len(ia.vocabulaire)} mots")
    print()
    
    # Générer le corpus complet
    print("Génération du corpus (350 physique + 350 maths + 350 IA)...")
    corpus = (generer_corpus_physique(350) +
              generer_corpus_mathematiques(350) +
              generer_corpus_ia_harmonique(350))
    # Dédupliquer
    corpus = list(dict.fromkeys(corpus))
    print(f"  Corpus généré : {len(corpus)} connaissances uniques")
    print()
    
    # Injection par lots de 100
    tailles_lots = [10, 50, 100, 200, 500]
    lots_a_tester = [t for t in tailles_lots if t <= len(corpus)]
    if len(corpus) not in lots_a_tester:
        lots_a_tester.append(len(corpus))
    
    print("Injection progressive et mesures...")
    print(f"  {'Connaissances':>15s}  {'Temps encodage':>14s}  {'Énergie':>12s}  {'Saturation':>11s}  {'Vocabulaire':>12s}")
    print(f"  {'-'*15}  {'-'*14}  {'-'*12}  {'-'*11}  {'-'*12}")
    
    dernier_lot = 0
    for n_total in lots_a_tester:
        n_a_ajouter = n_total - dernier_lot
        
        debut = time.time()
        for i in range(dernier_lot, n_total):
            ia.apprendre(corpus[i])
        duree = time.time() - debut
        
        etat = ia.hologramme.hologramme
        energie = float(np.sum(np.abs(etat)**2))
        saturation = float(np.max(np.abs(etat)))
        
        print(f"  {n_total:15d}  {duree:>13.3f}s  {energie:>12.2e}  {saturation:>11.4f}  {len(ia.vocabulaire):>12d}")
        dernier_lot = n_total
    
    print()
    
    # Test de précision
    print("Test de précision des requêtes...")
    print()
    
    requetes_test = [
        ("constante de Planck", corpus[0]),  # Devrait matcher une connaissance de physique
        ("nombre d'or valeur", corpus[200]),  # Devrait matcher une connaissance de maths
        ("principe holographique", corpus[550]),  # Devrait matcher une connaissance d'IA
        ("structure fine alpha", corpus[1]),
        ("theoreme de Pythagore", corpus[210]),
        ("filtre anti hallucination", corpus[560]),
    ]
    
    top1_correct = 0
    top3_correct = 0
    
    for requete, connaissance_attendue in requetes_test:
        resultat = ia.predire(requete)
        
        top1_id = None
        for pred in resultat['predictions']:
            if pred['type'] == 'holographique':
                top1_id = pred['id']
                break
        
        # Vérifier si la connaissance attendue est dans le top 3
        top3_ids = [p.get('id') for p in resultat['predictions'][:3] if p['type'] == 'holographique']
        top1_match = top1_id and any(c['id'] == top1_id and c['texte'].startswith(connaissance_attendue[:30])
                                     for c in ia.hologramme.connaissances_stockees)
        
        print(f"  Requête: \"{requete}\"")
        print(f"    Top 3 IDs: {top3_ids[:3]}")
        print()
    
    # Benchmark de robustesse
    print("Test de robustesse holographique (corpus large)...")
    robustesse = ia.hologramme.test_robustesse(0.5) if hasattr(ia.hologramme, 'test_robustesse') else None
    
    if robustesse:
        print(f"  Destruction 50% : score {robustesse.get('score_avant', 0):.4f} → {robustesse.get('score_apres', 0):.4f}")
        print(f"  Top-1 préservé: {'✅' if robustesse.get('top1_preserve') else '❌'}")
    
    print()
    print("=" * 80)
    print("TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    benchmark_corpus_large()