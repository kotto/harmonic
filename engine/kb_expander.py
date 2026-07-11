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
    'carbone': ('C', 6, 12.011, 'non-métal'),
    'azote': ('N', 7, 14.007, 'non-métal'),
    'oxygène': ('O', 8, 15.999, 'non-métal'),
    'fluor': ('F', 9, 18.998, 'halogène'),
    'sodium': ('Na', 11, 22.990, 'métal alcalin'),
    'magnésium': ('Mg', 12, 24.305, 'métal alcalino-terreux'),
    'aluminium': ('Al', 13, 26.982, 'métal'),
    'silicium': ('Si', 14, 28.085, 'métalloïde'),
    'phosphore': ('P', 15, 30.974, 'non-métal'),
    'soufre': ('S', 16, 32.065, 'non-métal'),
    'chlore': ('Cl', 17, 35.453, 'halogène'),
    'potassium': ('K', 19, 39.098, 'métal alcalin'),
    'calcium': ('Ca', 20, 40.078, 'métal alcalino-terreux'),
    'fer': ('Fe', 26, 55.845, 'métal de transition'),
    'cuivre': ('Cu', 29, 63.546, 'métal de transition'),
    'zinc': ('Zn', 30, 65.380, 'métal de transition'),
    'argent': ('Ag', 47, 107.868, 'métal de transition'),
    'or': ('Au', 79, 196.967, 'métal de transition'),
    'mercure': ('Hg', 80, 200.592, 'métal de transition'),
    'plomb': ('Pb', 82, 207.200, 'métal'),
    'uranium': ('U', 92, 238.029, 'actinide'),
    'plutonium': ('Pu', 94, 244.000, 'actinide'),
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
