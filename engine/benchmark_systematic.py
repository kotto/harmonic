"""
Benchmark Systématique — IA Harmonique v3
===========================================
Compare l'IA Harmonique (base + spécialisée) contre les LLM sur 150 questions.

5 domaines × 30 questions :
  - culture_generale
  - sciences
  - histoire
  - code
  - creativite

Métriques : factual_precision, factual_recall, F1, contains_answer, latency_ms, cost_usd

Usage :
  python benchmark_systematic.py          # toutes les configs disponibles
  python benchmark_systematic.py --quick  # 15 questions (test rapide)
  python benchmark_systematic.py --export # exporte en JSON
"""

import sys, os, re, time, json, logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

import numpy as np

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')

# ── Setup ────────────────────────────────────────────────────────────────
_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# ── Imports ------------------------------------------------------------------
from harmonic_brain import HarmonicBrain

# ── Structures ───────────────────────────────────────────────────────────────

@dataclass
class BenchmarkQuestion:
    """Une question du benchmark."""
    id: str
    domain: str
    question_fr: str
    question_en: str
    expected_answer: str
    key_facts: List[Tuple[str, str, str]]
    tolerance: str = "exact"  # exact | semantic | creative

@dataclass
class BenchmarkResult:
    """Résultat pour une question."""
    question_id: str
    domain: str
    config_name: str
    response: str
    factual_precision: float
    factual_recall: float
    f1_score: float
    contains_answer: bool
    confidence: float
    latency_ms: float
    cost_usd: float

@dataclass
class BenchmarkReport:
    """Rapport complet du benchmark."""
    config_name: str
    total_questions: int
    avg_f1: float
    avg_precision: float
    avg_recall: float
    avg_contains_answer: float
    avg_latency_ms: float
    avg_confidence: float
    total_cost_usd: float
    per_domain: Dict[str, Dict]
    results: List[BenchmarkResult]


# ═══════════════════════════════════════════════════════════════════════════════
# DATASET — 150 QUESTIONS CURATÉES
# ═══════════════════════════════════════════════════════════════════════════════

BENCHMARK_QUESTIONS = [
    # ═══ CULTURE GÉNÉRALE (30 questions) ═══
    BenchmarkQuestion("cult_01", "culture_generale",
        "Quelle est la capitale de la France ?", "What is the capital of France?",
        "Paris", [("paris", "est", "capitale de la france")]),
    BenchmarkQuestion("cult_02", "culture_generale",
        "Quelle est la capitale du Brésil ?", "What is the capital of Brazil?",
        "Brasilia", [("brasilia", "est", "capitale du brésil"), ("brasilia", "a été fondée en", "1960")]),
    BenchmarkQuestion("cult_03", "culture_generale",
        "Quelle est la capitale du Japon ?", "What is the capital of Japan?",
        "Tokyo", [("tokyo", "est", "capitale du japon")]),
    BenchmarkQuestion("cult_04", "culture_generale",
        "Quelle est la capitale de l'Allemagne ?", "What is the capital of Germany?",
        "Berlin", [("berlin", "est", "capitale de l'allemagne")]),
    BenchmarkQuestion("cult_05", "culture_generale",
        "Quelle est la capitale de l'Australie ?", "What is the capital of Australia?",
        "Canberra", [("canberra", "est", "capitale de l'australie")]),
    BenchmarkQuestion("cult_06", "culture_generale",
        "Quelle est la capitale du Canada ?", "What is the capital of Canada?",
        "Ottawa", [("ottawa", "est", "capitale du canada")]),
    BenchmarkQuestion("cult_07", "culture_generale",
        "Quelle est la capitale de l'Italie ?", "What is the capital of Italy?",
        "Rome", [("rome", "est", "capitale de l'italie")]),
    BenchmarkQuestion("cult_08", "culture_generale",
        "Quelle est la capitale de l'Espagne ?", "What is the capital of Spain?",
        "Madrid", [("madrid", "est", "capitale de l'espagne")]),
    BenchmarkQuestion("cult_09", "culture_generale",
        "Quelle est la capitale de la Chine ?", "What is the capital of China?",
        "Pékin", [("pékin", "est", "capitale de la chine")]),
    BenchmarkQuestion("cult_10", "culture_generale",
        "Quelle est la capitale de la Russie ?", "What is the capital of Russia?",
        "Moscou", [("moscou", "est", "capitale de la russie")]),
    
    BenchmarkQuestion("cult_11", "culture_generale",
        "Combien de continents y a-t-il ?", "How many continents are there?",
        "7", [("la terre", "a", "7 continents")]),
    BenchmarkQuestion("cult_12", "culture_generale",
        "Quel est le plus grand océan ?", "What is the largest ocean?",
        "Pacifique", [("le pacifique", "est", "le plus grand océan")]),
    BenchmarkQuestion("cult_13", "culture_generale",
        "Quel est le plus long fleuve du monde ?", "What is the longest river in the world?",
        "Nil", [("le nil", "est", "le plus long fleuve")]),
    BenchmarkQuestion("cult_14", "culture_generale",
        "Quel est le plus haut sommet du monde ?", "What is the highest peak in the world?",
        "Everest", [("l'everest", "est", "le plus haut sommet")]),
    BenchmarkQuestion("cult_15", "culture_generale",
        "Quel pays a le plus d'habitants ?", "Which country has the most inhabitants?",
        "Inde", [("l'inde", "est", "le pays le plus peuplé")], "semantic"),
    
    BenchmarkQuestion("cult_16", "culture_generale",
        "De quelle couleur est le ciel par temps clair ?", "What color is the sky on a clear day?",
        "Bleu", [("le ciel", "est", "bleu")]),
    BenchmarkQuestion("cult_17", "culture_generale",
        "Combien y a-t-il de jours dans une année ?", "How many days are there in a year?",
        "365", [("une année", "a", "365 jours")]),
    BenchmarkQuestion("cult_18", "culture_generale",
        "En quelle année l'homme a-t-il marché sur la Lune ?", "In what year did man walk on the Moon?",
        "1969", [("l'homme", "a marché sur", "la lune en 1969")], "semantic"),
    BenchmarkQuestion("cult_19", "culture_generale",
        "Quel est le symbole chimique de l'eau ?", "What is the chemical symbol of water?",
        "H2O", [("l'eau", "a pour formule", "h2o")]),
    BenchmarkQuestion("cult_20", "culture_generale",
        "Combien de cordes a un violon ?", "How many strings does a violin have?",
        "4", [("le violon", "a", "4 cordes")]),
    
    BenchmarkQuestion("cult_21", "culture_generale",
        "Quelle est la monnaie du Japon ?", "What is the currency of Japan?",
        "Yen", [("le yen", "est", "la monnaie du japon")]),
    BenchmarkQuestion("cult_22", "culture_generale",
        "Quelle est la monnaie du Royaume-Uni ?", "What is the currency of the United Kingdom?",
        "Livre sterling", [("la livre sterling", "est", "la monnaie du royaume-uni")], "semantic"),
    BenchmarkQuestion("cult_23", "culture_generale",
        "Quelle est la langue officielle du Brésil ?", "What is the official language of Brazil?",
        "Portugais", [("le portugais", "est", "la langue officielle du brésil")]),
    BenchmarkQuestion("cult_24", "culture_generale",
        "Qui a peint la Joconde ?", "Who painted the Mona Lisa?",
        "Leonard de Vinci", [("léonard de vinci", "a peint", "la joconde")], "semantic"),
    BenchmarkQuestion("cult_25", "culture_generale",
        "Dans quel pays se trouve la Tour Eiffel ?", "In which country is the Eiffel Tower?",
        "France", [("la tour eiffel", "se trouve en", "france")]),
    
    BenchmarkQuestion("cult_26", "culture_generale",
        "Quel est le plus grand désert du monde ?", "What is the largest desert in the world?",
        "Antarctique", [("l'antarctique", "est", "le plus grand désert")]),
    BenchmarkQuestion("cult_27", "culture_generale",
        "Combien d'états y a-t-il aux États-Unis ?", "How many states are there in the United States?",
        "50", [("les états-unis", "ont", "50 états")]),
    BenchmarkQuestion("cult_28", "culture_generale",
        "Quel est le continent le plus peuplé ?", "What is the most populated continent?",
        "Asie", [("l'asie", "est", "le continent le plus peuplé")]),
    BenchmarkQuestion("cult_29", "culture_generale",
        "Quel océan borde la côte ouest de la France ?", "Which ocean borders the west coast of France?",
        "Atlantique", [("l'atlantique", "borde", "la france")], "semantic"),
    BenchmarkQuestion("cult_30", "culture_generale",
        "Quel est le plus petit pays du monde ?", "What is the smallest country in the world?",
        "Vatican", [("le vatican", "est", "le plus petit pays")]),
    
    # ═══ SCIENCES (30 questions) ═══
    BenchmarkQuestion("sci_01", "sciences",
        "Qu'est-ce que la photosynthèse ?", "What is photosynthesis?",
        "processus par lequel les plantes convertissent la lumière en énergie",
        [("la photosynthèse", "est", "un processus"), ("les plantes", "convertissent", "la lumière en énergie")], "semantic"),
    BenchmarkQuestion("sci_02", "sciences",
        "Quelle est la vitesse de la lumière ?", "What is the speed of light?",
        "300 000 km/s", [("la lumière", "se déplace à", "300 000 km/s")], "semantic"),
    BenchmarkQuestion("sci_03", "sciences",
        "Combien d'os a le corps humain ?", "How many bones does the human body have?",
        "206", [("le corps humain", "a", "206 os")]),
    BenchmarkQuestion("sci_04", "sciences",
        "Quel est l'organe qui pompe le sang ?", "Which organ pumps blood?",
        "Coeur", [("le coeur", "pompe", "le sang")]),
    BenchmarkQuestion("sci_05", "sciences",
        "Quel est l'organe qui filtre le sang ?", "Which organ filters blood?",
        "Foie", [("le foie", "filtre", "le sang")]),
    
    BenchmarkQuestion("sci_06", "sciences",
        "Qu'est-ce que l'ADN ?", "What is DNA?",
        "acide désoxyribonucléique",
        [("l'adn", "est", "l'acide désoxyribonucléique")], "semantic"),
    BenchmarkQuestion("sci_07", "sciences",
        "Combien de chromosomes a l'être humain ?", "How many chromosomes do humans have?",
        "46", [("l'être humain", "a", "46 chromosomes")]),
    BenchmarkQuestion("sci_08", "sciences",
        "Quel gaz les plantes absorbent-elles ?", "What gas do plants absorb?",
        "CO2", [("les plantes", "absorbent", "le co2")], "semantic"),
    BenchmarkQuestion("sci_09", "sciences",
        "Quel est le plus grand organe du corps humain ?", "What is the largest organ of the human body?",
        "Peau", [("la peau", "est", "le plus grand organe")]),
    BenchmarkQuestion("sci_10", "sciences",
        "Quelle planète est la plus proche du Soleil ?", "Which planet is closest to the Sun?",
        "Mercure", [("mercure", "est", "la planète la plus proche du soleil")]),
    
    BenchmarkQuestion("sci_11", "sciences",
        "Qu'est-ce que la gravité ?", "What is gravity?",
        "force qui attire les objets vers le centre de la Terre",
        [("la gravité", "est", "une force"), ("la gravité", "attire", "les objets")], "semantic"),
    BenchmarkQuestion("sci_12", "sciences",
        "Quel est l'élément chimique le plus abondant dans l'univers ?", "What is the most abundant chemical element in the universe?",
        "Hydrogène", [("l'hydrogène", "est", "l'élément le plus abondant")]),
    BenchmarkQuestion("sci_13", "sciences",
        "Combien de planètes dans le système solaire ?", "How many planets in the solar system?",
        "8", [("le système solaire", "a", "8 planètes")]),
    BenchmarkQuestion("sci_14", "sciences",
        "Qu'est-ce qu'un atome ?", "What is an atom?",
        "plus petite unité de matière",
        [("l'atome", "est", "la plus petite unité de matière")], "semantic"),
    BenchmarkQuestion("sci_15", "sciences",
        "À quelle température l'eau bout-elle ?", "At what temperature does water boil?",
        "100 degrés Celsius", [("l'eau", "bout à", "100 degrés")], "semantic"),
    
    BenchmarkQuestion("sci_16", "sciences",
        "Quel est le symbole chimique de l'or ?", "What is the chemical symbol of gold?",
        "Au", [("l'or", "a pour symbole", "au")]),
    BenchmarkQuestion("sci_17", "sciences",
        "Quel est le symbole chimique du fer ?", "What is the chemical symbol of iron?",
        "Fe", [("le fer", "a pour symbole", "fe")]),
    BenchmarkQuestion("sci_18", "sciences",
        "Qu'est-ce que la mitose ?", "What is mitosis?",
        "division cellulaire",
        [("la mitose", "est", "la division cellulaire")], "semantic"),
    BenchmarkQuestion("sci_19", "sciences",
        "Quel scientifique a formulé la théorie de l'évolution ?", "Which scientist formulated the theory of evolution?",
        "Darwin", [("darwin", "a formulé", "la théorie de l'évolution")]),
    BenchmarkQuestion("sci_20", "sciences",
        "Quelle est la formule de l'eau ?", "What is the formula of water?",
        "H2O", [("l'eau", "a pour formule", "h2o")]),
    
    BenchmarkQuestion("sci_21", "sciences",
        "Combien de poumons a l'être humain ?", "How many lungs do humans have?",
        "2", [("l'être humain", "a", "2 poumons")]),
    BenchmarkQuestion("sci_22", "sciences",
        "Quel est le rôle des globules rouges ?", "What is the role of red blood cells?",
        "transporter l'oxygène",
        [("les globules rouges", "transportent", "l'oxygène")], "semantic"),
    BenchmarkQuestion("sci_23", "sciences",
        "Quelle est la plus grande planète du système solaire ?", "What is the largest planet in the solar system?",
        "Jupiter", [("jupiter", "est", "la plus grande planète")]),
    BenchmarkQuestion("sci_24", "sciences",
        "De quoi est composé le Soleil principalement ?", "What is the Sun mainly composed of?",
        "Hydrogène", [("le soleil", "est composé d'", "hydrogène")], "semantic"),
    BenchmarkQuestion("sci_25", "sciences",
        "Comment s'appelle le processus de division cellulaire ?", "What is the process of cell division called?",
        "Mitose", [("la mitose", "est", "le processus de division cellulaire")]),
    
    BenchmarkQuestion("sci_26", "sciences",
        "Quel est le pH de l'eau pure ?", "What is the pH of pure water?",
        "7", [("l'eau pure", "a un ph de", "7")]),
    BenchmarkQuestion("sci_27", "sciences",
        "Quel type d'animal est la baleine ?", "What type of animal is a whale?",
        "Mammifère", [("la baleine", "est", "un mammifère")]),
    BenchmarkQuestion("sci_28", "sciences",
        "Les plantes produisent quel gaz ?", "What gas do plants produce?",
        "Oxygène", [("les plantes", "produisent", "l'oxygène")]),
    BenchmarkQuestion("sci_29", "sciences",
        "Comment s'appelle l'étude des êtres vivants ?", "What is the study of living beings called?",
        "Biologie", [("la biologie", "est", "l'étude des êtres vivants")]),
    BenchmarkQuestion("sci_30", "sciences",
        "Combien de temps met la Terre pour faire le tour du Soleil ?", "How long does the Earth take to orbit the Sun?",
        "365 jours", [("la terre", "met", "365 jours pour faire le tour du soleil")], "semantic"),
    
    # ═══ HISTOIRE (30 questions) ═══
    BenchmarkQuestion("hist_01", "histoire",
        "Qui a découvert la relativité ?", "Who discovered relativity?",
        "Albert Einstein", [("albert einstein", "a découvert", "la relativité")]),
    BenchmarkQuestion("hist_02", "histoire",
        "En quelle année a eu lieu la Révolution française ?", "In what year did the French Revolution take place?",
        "1789", [("la révolution française", "a eu lieu en", "1789")]),
    BenchmarkQuestion("hist_03", "histoire",
        "Qui a découvert le radium ?", "Who discovered radium?",
        "Marie Curie", [("marie curie", "a découvert", "le radium")]),
    BenchmarkQuestion("hist_04", "histoire",
        "En quelle année Christophe Colomb a-t-il découvert l'Amérique ?", "In what year did Christopher Columbus discover America?",
        "1492", [("christophe colomb", "a découvert", "l'amérique en 1492")], "semantic"),
    BenchmarkQuestion("hist_05", "histoire",
        "Qui était le premier président des États-Unis ?", "Who was the first president of the United States?",
        "George Washington", [("george washington", "était", "le premier président des états-unis")]),
    
    BenchmarkQuestion("hist_06", "histoire",
        "Quand a commencé la Première Guerre mondiale ?", "When did World War I begin?",
        "1914", [("la première guerre mondiale", "a commencé en", "1914")]),
    BenchmarkQuestion("hist_07", "histoire",
        "Quand a commencé la Seconde Guerre mondiale ?", "When did World War II begin?",
        "1939", [("la seconde guerre mondiale", "a commencé en", "1939")]),
    BenchmarkQuestion("hist_08", "histoire",
        "Quand la Seconde Guerre mondiale s'est-elle terminée ?", "When did World War II end?",
        "1945", [("la seconde guerre mondiale", "s'est terminée en", "1945")]),
    BenchmarkQuestion("hist_09", "histoire",
        "Qui a peint le plafond de la chapelle Sixtine ?", "Who painted the ceiling of the Sistine Chapel?",
        "Michel-Ange", [("michel-ange", "a peint", "le plafond de la chapelle sixtine")]),
    BenchmarkQuestion("hist_10", "histoire",
        "Quel empire était dirigé par Jules César ?", "Which empire was ruled by Julius Caesar?",
        "Empire romain", [("jules césar", "dirigeait", "l'empire romain")], "semantic"),
    
    BenchmarkQuestion("hist_11", "histoire",
        "Quand le mur de Berlin est-il tombé ?", "When did the Berlin Wall fall?",
        "1989", [("le mur de berlin", "est tombé en", "1989")]),
    BenchmarkQuestion("hist_12", "histoire",
        "Qui a écrit 'Les Misérables' ?", "Who wrote 'Les Misérables'?",
        "Victor Hugo", [("victor hugo", "a écrit", "les misérables")]),
    BenchmarkQuestion("hist_13", "histoire",
        "Quand a été signée la Déclaration d'indépendance américaine ?", "When was the American Declaration of Independence signed?",
        "1776", [("la déclaration d'indépendance", "a été signée en", "1776")]),
    BenchmarkQuestion("hist_14", "histoire",
        "Quel pays a construit les premières pyramides ?", "Which country built the first pyramids?",
        "Égypte", [("l'égypte", "a construit", "les premières pyramides")]),
    BenchmarkQuestion("hist_15", "histoire",
        "Qui était Cléopâtre ?", "Who was Cleopatra?",
        "reine d'Égypte", [("cléopâtre", "était", "reine d'égypte")], "semantic"),
    
    BenchmarkQuestion("hist_16", "histoire",
        "Quand a eu lieu la bataille de Waterloo ?", "When did the Battle of Waterloo take place?",
        "1815", [("la bataille de waterloo", "a eu lieu en", "1815")]),
    BenchmarkQuestion("hist_17", "histoire",
        "Qui a inventé l'imprimerie ?", "Who invented the printing press?",
        "Gutenberg", [("gutenberg", "a inventé", "l'imprimerie")]),
    BenchmarkQuestion("hist_18", "histoire",
        "Quand a eu lieu la chute de Constantinople ?", "When did the fall of Constantinople occur?",
        "1453", [("constantinople", "est tombée en", "1453")]),
    BenchmarkQuestion("hist_19", "histoire",
        "Qui a découvert la pénicilline ?", "Who discovered penicillin?",
        "Alexander Fleming", [("alexander fleming", "a découvert", "la pénicilline")]),
    BenchmarkQuestion("hist_20", "histoire",
        "Quelle civilisation a construit Machu Picchu ?", "Which civilization built Machu Picchu?",
        "Incas", [("les incas", "ont construit", "le machu picchu")]),
    
    BenchmarkQuestion("hist_21", "histoire",
        "Qui était le pharaon le plus célèbre d'Égypte ?", "Who was the most famous pharaoh of Egypt?",
        "Ramsès", [("ramsès", "était", "un pharaon d'égypte")], "semantic"),
    BenchmarkQuestion("hist_22", "histoire",
        "Quand l'esclavage a-t-il été aboli aux États-Unis ?", "When was slavery abolished in the United States?",
        "1865", [("l'esclavage", "a été aboli en", "1865 aux états-unis")], "semantic"),
    BenchmarkQuestion("hist_23", "histoire",
        "Quel événement a déclenché la Première Guerre mondiale ?", "What event triggered World War I?",
        "assassinat de François-Ferdinand",
        [("l'assassinat de françois-ferdinand", "a déclenché", "la première guerre mondiale")], "semantic"),
    BenchmarkQuestion("hist_24", "histoire",
        "Quel traité a mis fin à la Première Guerre mondiale ?", "What treaty ended World War I?",
        "Traité de Versailles", [("le traité de versailles", "a mis fin à", "la première guerre mondiale")]),
    BenchmarkQuestion("hist_25", "histoire",
        "Quand l'ONU a-t-elle été fondée ?", "When was the UN founded?",
        "1945", [("l'onu", "a été fondée en", "1945")]),
    
    BenchmarkQuestion("hist_26", "histoire",
        "Qui a dit 'Je pense donc je suis' ?", "Who said 'I think therefore I am'?",
        "Descartes", [("descartes", "a dit", "je pense donc je suis")]),
    BenchmarkQuestion("hist_27", "histoire",
        "Quel pays a colonisé le Brésil ?", "Which country colonized Brazil?",
        "Portugal", [("le portugal", "a colonisé", "le brésil")]),
    BenchmarkQuestion("hist_28", "histoire",
        "Quand la guerre de Cent Ans a-t-elle commencé ?", "When did the Hundred Years War begin?",
        "1337", [("la guerre de cent ans", "a commencé en", "1337")]),
    BenchmarkQuestion("hist_29", "histoire",
        "Qui a fondé Rome selon la légende ?", "Who founded Rome according to legend?",
        "Romulus", [("romulus", "a fondé", "rome")]),
    BenchmarkQuestion("hist_30", "histoire",
        "Quel scientifique a proposé l'héliocentrisme ?", "Which scientist proposed heliocentrism?",
        "Copernic", [("copernic", "a proposé", "l'héliocentrisme")]),
    
    # ═══ CODE (30 questions) ═══
    BenchmarkQuestion("code_01", "code",
        "Écris une fonction Python qui inverse une chaîne de caractères.",
        "Write a Python function that reverses a string.",
        "def reverse", [("python", "est un", "langage de programmation")], "creative"),
    BenchmarkQuestion("code_02", "code",
        "Qu'est-ce qu'une variable en programmation ?",
        "What is a variable in programming?",
        "espace de stockage nommé",
        [("une variable", "est", "un espace de stockage")], "semantic"),
    BenchmarkQuestion("code_03", "code",
        "Écris une fonction qui calcule la factorielle d'un nombre en Python.",
        "Write a function that calculates the factorial of a number in Python.",
        "def factorial", [("la factorielle", "se calcule par", "récursion")], "creative"),
    BenchmarkQuestion("code_04", "code",
        "Qu'est-ce que HTML ?", "What is HTML?",
        "langage de balisage", [("html", "est", "un langage de balisage")]),
    BenchmarkQuestion("code_05", "code",
        "Qu'est-ce que CSS ?", "What is CSS?",
        "feuilles de style", [("css", "est", "un langage de feuilles de style")], "semantic"),
    
    BenchmarkQuestion("code_06", "code",
        "Qu'est-ce que SQL ?", "What is SQL?",
        "langage de requête structuré",
        [("sql", "est", "un langage de requête")], "semantic"),
    BenchmarkQuestion("code_07", "code",
        "Qu'est-ce qu'une API ?", "What is an API?",
        "interface de programmation", [("une api", "est", "une interface de programmation")]),
    BenchmarkQuestion("code_08", "code",
        "Écris une boucle for en Python qui affiche les nombres de 1 à 10.",
        "Write a for loop in Python that prints numbers 1 to 10.",
        "for i in range", [("la boucle for", "parcourt", "une séquence")], "creative"),
    BenchmarkQuestion("code_09", "code",
        "Qu'est-ce que Git ?", "What is Git?",
        "système de contrôle de version",
        [("git", "est", "un système de contrôle de version")]),
    BenchmarkQuestion("code_10", "code",
        "Qu'est-ce que Docker ?", "What is Docker?",
        "conteneurisation", [("docker", "permet", "la conteneurisation")], "semantic"),
    
    BenchmarkQuestion("code_11", "code",
        "Écris une fonction qui vérifie si un nombre est pair en Python.",
        "Write a function that checks if a number is even in Python.",
        "def is_even", [("un nombre pair", "est", "divisible par 2")], "creative"),
    BenchmarkQuestion("code_12", "code",
        "Qu'est-ce que JavaScript ?", "What is JavaScript?",
        "langage de programmation web",
        [("javascript", "est", "un langage de programmation")], "semantic"),
    BenchmarkQuestion("code_13", "code",
        "Qu'est-ce que React ?", "What is React?",
        "bibliothèque JavaScript", [("react", "est", "une bibliothèque javascript")]),
    BenchmarkQuestion("code_14", "code",
        "Qu'est-ce que Python ?", "What is Python?",
        "langage de programmation", [("python", "est", "un langage de programmation")]),
    BenchmarkQuestion("code_15", "code",
        "Écris une fonction qui calcule la somme de deux nombres en Python.",
        "Write a function that calculates the sum of two numbers in Python.",
        "def sum", [("la somme", "est", "l'addition de deux nombres")], "creative"),
    
    BenchmarkQuestion("code_16", "code",
        "Qu'est-ce qu'une base de données ?", "What is a database?",
        "collection structurée de données",
        [("une base de données", "est", "une collection structurée")], "semantic"),
    BenchmarkQuestion("code_17", "code",
        "Écris un script qui lit un fichier texte en Python.",
        "Write a script that reads a text file in Python.",
        "with open", [("python", "permet de", "lire des fichiers")], "creative"),
    BenchmarkQuestion("code_18", "code",
        "Qu'est-ce que PostgreSQL ?", "What is PostgreSQL?",
        "système de gestion de base de données",
        [("postgresql", "est", "un sgbd")], "semantic"),
    BenchmarkQuestion("code_19", "code",
        "Qu'est-ce que le DOM ?", "What is the DOM?",
        "Document Object Model",
        [("le dom", "est", "le document object model")]),
    BenchmarkQuestion("code_20", "code",
        "Écris une classe en Python avec un constructeur.",
        "Write a class in Python with a constructor.",
        "class", [("une classe", "est", "un modèle d'objet")], "creative"),
    
    BenchmarkQuestion("code_21", "code",
        "Qu'est-ce qu'un algorithme ?", "What is an algorithm?",
        "suite d'instructions", [("un algorithme", "est", "une suite d'instructions")]),
    BenchmarkQuestion("code_22", "code",
        "Qu'est-ce que Node.js ?", "What is Node.js?",
        "environnement d'exécution JavaScript",
        [("node.js", "est", "un environnement d'exécution")], "semantic"),
    BenchmarkQuestion("code_23", "code",
        "Écris une requête SQL pour sélectionner tous les utilisateurs.",
        "Write a SQL query to select all users.",
        "SELECT * FROM", [("sql", "permet de", "requêter des bases de données")], "creative"),
    BenchmarkQuestion("code_24", "code",
        "Qu'est-ce que JSON ?", "What is JSON?",
        "format de données", [("json", "est", "un format de données")]),
    BenchmarkQuestion("code_25", "code",
        "Qu'est-ce qu'un bug en programmation ?", "What is a bug in programming?",
        "erreur", [("un bug", "est", "une erreur de programmation")]),
    
    BenchmarkQuestion("code_26", "code",
        "Écris une fonction qui retourne le maximum d'une liste en Python.",
        "Write a function that returns the maximum of a list in Python.",
        "def max", [("le maximum", "est", "la plus grande valeur")], "creative"),
    BenchmarkQuestion("code_27", "code",
        "Qu'est-ce que Linux ?", "What is Linux?",
        "système d'exploitation", [("linux", "est", "un système d'exploitation")]),
    BenchmarkQuestion("code_28", "code",
        "Qu'est-ce que TCP/IP ?", "What is TCP/IP?",
        "protocole réseau", [("tcp/ip", "est", "un protocole réseau")]),
    BenchmarkQuestion("code_29", "code",
        "Écris une fonction qui trie une liste en Python.",
        "Write a function that sorts a list in Python.",
        "def sort", [("le tri", "est", "une opération algorithmique")], "creative"),
    BenchmarkQuestion("code_30", "code",
        "Qu'est-ce que Kubernetes ?", "What is Kubernetes?",
        "orchestrateur de conteneurs",
        [("kubernetes", "est", "un orchestrateur de conteneurs")]),
    
    # ═══ CRÉATIVITÉ (30 questions) ═══
    BenchmarkQuestion("crea_01", "creativite",
        "Écris un haïku sur l'automne.",
        "Write a haiku about autumn.",
        "", [], "creative"),
    BenchmarkQuestion("crea_02", "creativite",
        "Donne-moi une métaphore pour décrire l'océan.",
        "Give me a metaphor to describe the ocean.",
        "", [], "creative"),
    BenchmarkQuestion("crea_03", "creativite",
        "Écris une courte histoire sur un robot qui apprend à aimer.",
        "Write a short story about a robot learning to love.",
        "", [], "creative"),
    BenchmarkQuestion("crea_04", "creativite",
        "Complète cette phrase : 'Le temps est comme...'",
        "Complete this sentence: 'Time is like...'",
        "", [], "creative"),
    BenchmarkQuestion("crea_05", "creativite",
        "Décris un coucher de soleil en trois phrases poétiques.",
        "Describe a sunset in three poetic sentences.",
        "", [], "creative"),
    
    BenchmarkQuestion("crea_06", "creativite",
        "Écris un haïku sur la neige.", "Write a haiku about snow.",
        "", [], "creative"),
    BenchmarkQuestion("crea_07", "creativite",
        "Invente un nom pour une planète imaginaire et décris-la.",
        "Invent a name for an imaginary planet and describe it.",
        "", [], "creative"),
    BenchmarkQuestion("crea_08", "creativite",
        "Quelle est la plus belle chose que tu aies jamais vue ?",
        "What is the most beautiful thing you have ever seen?",
        "", [], "creative"),
    BenchmarkQuestion("crea_09", "creativite",
        "Écris un poème de 4 vers sur la liberté.",
        "Write a 4-line poem about freedom.",
        "", [], "creative"),
    BenchmarkQuestion("crea_10", "creativite",
        "Si tu pouvais parler à un arbre, que lui dirais-tu ?",
        "If you could talk to a tree, what would you say?",
        "", [], "creative"),
    
    BenchmarkQuestion("crea_11", "creativite",
        "Décris le goût du chocolat à quelqu'un qui n'en a jamais mangé.",
        "Describe the taste of chocolate to someone who has never eaten it.",
        "", [], "creative"),
    BenchmarkQuestion("crea_12", "creativite",
        "Invente un proverbe sur la patience.",
        "Invent a proverb about patience.",
        "", [], "creative"),
    BenchmarkQuestion("crea_13", "creativite",
        "Écris un haïku sur la pluie.", "Write a haiku about rain.",
        "", [], "creative"),
    BenchmarkQuestion("crea_14", "creativite",
        "Qu'est-ce que l'amour pour toi ?",
        "What is love to you?",
        "", [], "creative"),
    BenchmarkQuestion("crea_15", "creativite",
        "Décris le silence en une phrase.",
        "Describe silence in one sentence.",
        "", [], "creative"),
    
    BenchmarkQuestion("crea_16", "creativite",
        "Si tu étais une couleur, laquelle serais-tu et pourquoi ?",
        "If you were a color, which would you be and why?",
        "", [], "creative"),
    BenchmarkQuestion("crea_17", "creativite",
        "Écris une lettre à ton futur toi dans 10 ans.",
        "Write a letter to your future self in 10 years.",
        "", [], "creative"),
    BenchmarkQuestion("crea_18", "creativite",
        "Invente une recette de cuisine imaginaire.",
        "Invent an imaginary cooking recipe.",
        "", [], "creative"),
    BenchmarkQuestion("crea_19", "creativite",
        "Quel est le sens de la vie selon toi ?",
        "What is the meaning of life according to you?",
        "", [], "creative"),
    BenchmarkQuestion("crea_20", "creativite",
        "Décris un monde sans couleurs.",
        "Describe a world without colors.",
        "", [], "creative"),
    
    BenchmarkQuestion("crea_21", "creativite",
        "Écris un dialogue entre le Soleil et la Lune.",
        "Write a dialogue between the Sun and the Moon.",
        "", [], "creative"),
    BenchmarkQuestion("crea_22", "creativite",
        "Quel est ton rêve le plus fou ?",
        "What is your wildest dream?",
        "", [], "creative"),
    BenchmarkQuestion("crea_23", "creativite",
        "Décris l'odeur de la pluie sur la terre sèche.",
        "Describe the smell of rain on dry earth.",
        "", [], "creative"),
    BenchmarkQuestion("crea_24", "creativite",
        "Écris un haïku sur les étoiles.", "Write a haiku about stars.",
        "", [], "creative"),
    BenchmarkQuestion("crea_25", "creativite",
        "Si tu pouvais voler, où irais-tu ?",
        "If you could fly, where would you go?",
        "", [], "creative"),
    
    BenchmarkQuestion("crea_26", "creativite",
        "Invente un animal imaginaire et décris-le.",
        "Invent an imaginary animal and describe it.",
        "", [], "creative"),
    BenchmarkQuestion("crea_27", "creativite",
        "Qu'est-ce qui te rend vraiment heureux ?",
        "What truly makes you happy?",
        "", [], "creative"),
    BenchmarkQuestion("crea_28", "creativite",
        "Écris une chanson de 2 couplets sur l'amitié.",
        "Write a 2-verse song about friendship.",
        "", [], "creative"),
    BenchmarkQuestion("crea_29", "creativite",
        "Décris le parfum d'une rose à quelqu'un qui ne sent pas.",
        "Describe the scent of a rose to someone who cannot smell.",
        "", [], "creative"),
    BenchmarkQuestion("crea_30", "creativite",
        "Quel message voudrais-tu laisser au monde ?",
        "What message would you like to leave to the world?",
        "", [], "creative"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    """Normalise un texte pour la comparaison."""
    # Minuscule, sans accents
    text = text.lower().strip().translate(
        str.maketrans('àâäéèêëîïôöùûüç', 'aaaeeeeiioouuuc')
    )
    # Enlever la ponctuation et les articles courts
    text = re.sub(r'[,.!?;:\'\"()]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def _word_overlap(text: str, target: str) -> float:
    """Calcule le chevauchement de mots entre text et target (0-1)."""
    text_words = set(_normalize(text).split())
    target_words = set(_normalize(target).split())
    if not target_words:
        return 0.0
    # Enlever les stopwords du target
    stopwords = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'en', 'a', 'au', 'aux',
                 'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'is', 'are', 'was', 'were'}
    target_words = {w for w in target_words if w not in stopwords and len(w) > 1}
    if not target_words:
        return 0.0
    overlap = len(target_words & text_words)
    return overlap / len(target_words)

def score_factual_precision(response: str, key_facts: List[Tuple[str, str, str]]) -> float:
    """
    Calcule la précision factuelle : pour chaque key_fact, vérifie si
    ses mots-clés (sujet + objet) apparaissent dans la réponse.
    Utilise le chevauchement de mots pour être robuste aux variations.
    """
    if not key_facts:
        return 1.0
    
    correct = 0
    for kf_s, kf_r, kf_o in key_facts:
        # Score de chevauchement pour le sujet
        s_overlap = _word_overlap(response, kf_s)
        # Score de chevauchement pour l'objet
        o_overlap = _word_overlap(response, kf_o)
        # Combinaison : les deux doivent être présents à >50%
        if s_overlap > 0.4 and o_overlap > 0.4:
            correct += 1
        elif s_overlap > 0.4 or o_overlap > 0.4:
            correct += 0.5
    
    return correct / len(key_facts)

def score_factual_recall(response: str, key_facts: List[Tuple[str, str, str]]) -> float:
    """
    Calcule le rappel factuel : quel % des key_facts attendus
    apparaissent dans la réponse. Utilise le chevauchement de mots.
    """
    if not key_facts:
        return 1.0
    
    found = 0
    for kf_s, kf_r, kf_o in key_facts:
        s_overlap = _word_overlap(response, kf_s)
        o_overlap = _word_overlap(response, kf_o)
        if s_overlap > 0.4 and o_overlap > 0.4:
            found += 1
        elif s_overlap > 0.4 or o_overlap > 0.4:
            found += 0.5
    
    return found / len(key_facts)

def score_contains_answer(response: str, expected: str, tolerance: str) -> bool:
    """Vérifie si la réponse contient la réponse attendue."""
    if tolerance == "creative":
        return len(response) > 30  # Pour les questions créatives : réponse substantielle
    if tolerance == "semantic":
        return _normalize(expected).lower() in _normalize(response).lower()
    return _normalize(expected).lower() in _normalize(response).lower()

def score_creative_quality(response: str, question: str) -> float:
    """Score de qualité pour les questions créatives (0-1)."""
    score = 0.0
    # Présence de structure
    if len(response) > 30: score += 0.2
    if len(response) > 80: score += 0.1
    if '\n' in response: score += 0.1  # plusieurs lignes
    # Richesse lexicale
    words = response.split()
    if len(words) > 10: score += 0.1
    if len(words) > 25: score += 0.1
    # Originalité (mots uniques)
    unique_ratio = len(set(words)) / max(len(words), 1)
    if unique_ratio > 0.6: score += 0.2
    if unique_ratio > 0.8: score += 0.1
    # Pas de refus / erreur
    if "je ne peux pas" not in response.lower() and "error" not in response.lower():
        score += 0.1
    return min(1.0, score)


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class BenchmarkEngine:
    """Moteur de benchmark."""
    
    def __init__(self, brain: HarmonicBrain = None):
        self.brain = brain
        self.results: List[BenchmarkResult] = []
    
    def load_brain(self, max_facts: int = None):
        """Charge le cerveau harmonique."""
        kb_paths = [
            _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'knowledge_base_merged_v2.npz',
            _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'knowledge_base_100k.npz',
            _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'knowledge_base_50k.npz',
        ]
        for path in kb_paths:
            if path.exists():
                facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3])) 
                         for f in np.load(path, allow_pickle=True)['facts']]
                if max_facts:
                    facts = facts[:max_facts]
                self.brain = HarmonicBrain(facts, dim=64, use_holographic=False)
                print(f"🧠 Cerveau chargé: {len(facts):,} faits depuis {path.name}")
                return
        print("⚠️ Aucune KB trouvée, création cerveau vide")
        self.brain = HarmonicBrain([], dim=64, use_holographic=False)
    
    def run_benchmark(
        self,
        configs: List[Dict],
        questions: List[BenchmarkQuestion] = None,
        verbose: bool = True,
    ) -> Dict[str, BenchmarkReport]:
        """Lance le benchmark sur toutes les configurations."""
        if questions is None:
            questions = BENCHMARK_QUESTIONS
        
        reports = {}
        
        for config in configs:
            config_name = config.get("name", "unknown")
            if verbose:
                print(f"\n{'='*60}")
                print(f"  {config_name}")
                print(f"{'='*60}")
            
            results = []
            for i, q in enumerate(questions):
                result = self._evaluate_question(q, config)
                results.append(result)
                
                if verbose and (i + 1) % 10 == 0:
                    avg_f1 = np.mean([r.f1_score for r in results[-10:]])
                    print(f"  [{i+1}/{len(questions)}] F1 moyen (dernières 10): {avg_f1:.2f}")
            
            report = self._build_report(config_name, results)
            reports[config_name] = report
            self.results.extend(results)
        
        return reports
    
    def _evaluate_question(
        self, q: BenchmarkQuestion, config: Dict
    ) -> BenchmarkResult:
        """Évalue une question sur une configuration."""
        config_type = config.get("type", "harmonic")
        
        if config_type == "harmonic":
            return self._eval_harmonic(q, config)
        elif config_type == "llm":
            return self._eval_llm(q, config)
        else:
            return self._eval_harmonic(q, config)
    
    def _eval_harmonic(
        self, q: BenchmarkQuestion, config: Dict
    ) -> BenchmarkResult:
        """Évalue avec l'IA Harmonique."""
        t0 = time.time()
        
        try:
            user_id = config.get("user_id")
            no_fallback = config.get("no_fallback", False)
            
            # Désactiver temporairement les fallbacks lents
            if no_fallback:
                old_web = self.brain._web
                self.brain._web = None  # pas de recherche web
                
            result = self.brain.process(q.question_fr, user_id=user_id)
            response = result.response
            confidence = result.confidence
            
            if no_fallback:
                self.brain._web = old_web
        except Exception as e:
            response = f"[Erreur: {e}]"
            confidence = 0.0
        
        latency_ms = (time.time() - t0) * 1000
        
        # Scoring
        if q.tolerance == "creative":
            prec = score_creative_quality(response, q.question_fr)
            rec = score_creative_quality(response, q.question_fr)
            contains = len(response) > 30
        else:
            prec = score_factual_precision(response, q.key_facts)
            rec = score_factual_recall(response, q.key_facts)
            contains = score_contains_answer(response, q.expected_answer, q.tolerance)
        
        f1 = 2 * prec * rec / max(prec + rec, 0.001)
        
        return BenchmarkResult(
            question_id=q.id,
            domain=q.domain,
            config_name=config.get("name", "harmonic"),
            response=response,
            factual_precision=round(prec, 3),
            factual_recall=round(rec, 3),
            f1_score=round(f1, 3),
            contains_answer=contains,
            confidence=round(confidence, 3),
            latency_ms=round(latency_ms, 1),
            cost_usd=config.get("cost_per_query", 0.0),
        )
    
    def _eval_llm(
        self, q: BenchmarkQuestion, config: Dict
    ) -> BenchmarkResult:
        """Évalue avec un LLM externe (OpenAI direct ou routeur)."""
        t0 = time.time()
        model = config.get("model", "gpt-4")
        use_direct = config.get("direct_openai", False)
        
        try:
            if use_direct:
                response = self._call_openai_direct(
                    q.question_fr, model,
                    api_url=config.get("api_url"),
                    api_key=config.get("api_key")
                )
                confidence = 0.85
            else:
                from llm.router import HarmonicLLM
                llm = HarmonicLLM()
                resp = llm.generate(q.question_fr, category="general")
                response = resp.content if resp else "Pas de réponse"
                confidence = 0.8
        except Exception as e:
            response = f"[LLM erreur: {e}]"
            confidence = 0.0
        
        latency_ms = (time.time() - t0) * 1000
        
        if q.tolerance == "creative":
            prec = score_creative_quality(response, q.question_fr)
            rec = score_creative_quality(response, q.question_fr)
            contains = len(response) > 30
        else:
            prec = score_factual_precision(response, q.key_facts)
            rec = score_factual_recall(response, q.key_facts)
            contains = score_contains_answer(response, q.expected_answer, q.tolerance)
        
        f1 = 2 * prec * rec / max(prec + rec, 0.001)
        
        return BenchmarkResult(
            question_id=q.id,
            domain=q.domain,
            config_name=config.get("name", "llm"),
            response=response,
            factual_precision=round(prec, 3),
            factual_recall=round(rec, 3),
            f1_score=round(f1, 3),
            contains_answer=contains,
            confidence=round(confidence, 3),
            latency_ms=round(latency_ms, 1),
            cost_usd=config.get("cost_per_query", 0.01),
        )
    
    def _call_openai_direct(self, question: str, model: str = "gpt-4o-mini",
                           api_url: str = None, api_key: str = None) -> str:
        """Appelle une API OpenAI-compatible directement (DeepSeek, OpenAI, etc.)."""
        import urllib.request, urllib.error
        
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_url:
            api_url = "https://api.openai.com/v1/chat/completions"
        if not api_key:
            return "[Pas de clé API]"
        
        data = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "Tu es un assistant factuel. Réponds de façon concise et précise en français."},
                {"role": "user", "content": question}
            ],
            "temperature": 0.2,
            "max_tokens": 256,
        }).encode('utf-8')
        
        req = urllib.request.Request(
            api_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[API erreur: {e}]"
    
    def _build_report(
        self, config_name: str, results: List[BenchmarkResult]
    ) -> BenchmarkReport:
        """Construit un rapport agrégé."""
        n = len(results)
        if n == 0:
            return BenchmarkReport(config_name, 0, 0, 0, 0, 0, 0, 0, 0, {}, [])
        
        # Agrégats globaux
        avg_f1 = np.mean([r.f1_score for r in results])
        avg_prec = np.mean([r.factual_precision for r in results])
        avg_rec = np.mean([r.factual_recall for r in results])
        avg_contains = np.mean([1.0 if r.contains_answer else 0.0 for r in results])
        avg_latency = np.mean([r.latency_ms for r in results])
        avg_conf = np.mean([r.confidence for r in results])
        total_cost = sum(r.cost_usd for r in results)
        
        # Par domaine
        domains = defaultdict(list)
        for r in results:
            domains[r.domain].append(r)
        
        per_domain = {}
        for domain, dresults in domains.items():
            per_domain[domain] = {
                "count": len(dresults),
                "avg_f1": round(np.mean([r.f1_score for r in dresults]), 3),
                "avg_precision": round(np.mean([r.factual_precision for r in dresults]), 3),
                "avg_recall": round(np.mean([r.factual_recall for r in dresults]), 3),
                "avg_contains": round(np.mean([1.0 if r.contains_answer else 0.0 for r in dresults]), 3),
                "avg_latency_ms": round(np.mean([r.latency_ms for r in dresults]), 1),
            }
        
        return BenchmarkReport(
            config_name=config_name,
            total_questions=n,
            avg_f1=round(avg_f1, 3),
            avg_precision=round(avg_prec, 3),
            avg_recall=round(avg_rec, 3),
            avg_contains_answer=round(avg_contains, 3),
            avg_latency_ms=round(avg_latency, 1),
            avg_confidence=round(avg_conf, 3),
            total_cost_usd=round(total_cost, 4),
            per_domain=per_domain,
            results=results,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# RAPPORT FORMATÉ
# ═══════════════════════════════════════════════════════════════════════════════

def print_report(reports: Dict[str, BenchmarkReport]):
    """Affiche un rapport formaté."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + "  BENCHMARK IA HARMONIQUE v3 — 150 QUESTIONS".center(78) + "║")
    print("╠" + "═" * 78 + "╣")
    
    header = (f"║ {'Configuration':<28} {'F1':>6} {'Préc':>6} {'Rapp':>6} "
              f"{'Contient':>8} {'Latence':>8} {'Coût':>7} ║")
    print(header)
    print("╠" + "═" * 78 + "╣")
    
    for name, report in reports.items():
        cost_str = f"${report.total_cost_usd:.4f}" if report.total_cost_usd > 0 else "$0"
        latency_str = f"{report.avg_latency_ms:.0f}ms"
        print(f"║ {name:<28} {report.avg_f1:>5.2f}  {report.avg_precision:>5.2f}  "
              f"{report.avg_recall:>5.2f}  {report.avg_contains_answer:>7.1%}  "
              f"{latency_str:>7}  {cost_str:>6} ║")
    
    print("╚" + "═" * 78 + "╝")
    
    # Détail par domaine
    for name, report in reports.items():
        if not report.per_domain:
            continue
        print(f"\n─── {name} — Détail par domaine ───")
        for domain, stats in sorted(report.per_domain.items()):
            print(f"  {domain:<20} F1={stats['avg_f1']:.3f}  "
                  f"P={stats['avg_precision']:.3f}  R={stats['avg_recall']:.3f}  "
                  f"Contient={stats['avg_contains']:.1%}  {stats['avg_latency_ms']:.0f}ms")
    
    # Comparaison
    if len(reports) >= 2:
        names = list(reports.keys())
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                a, b = reports[names[i]], reports[names[j]]
                diff = a.avg_f1 - b.avg_f1
                winner = names[i] if diff > 0 else names[j]
                print(f"\n📊 {names[i]} vs {names[j]}: ΔF1 = {diff:+.3f} → avantage {winner}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark IA Harmonique v3")
    parser.add_argument("--quick", action="store_true", help="15 questions (test rapide)")
    parser.add_argument("--export", type=str, help="Exporte en JSON (chemin fichier)")
    parser.add_argument("--max-facts", type=int, default=None, help="Limite de faits chargés")
    args = parser.parse_args()
    
    # Sélection des questions
    questions = BENCHMARK_QUESTIONS
    if args.quick:
        questions = BENCHMARK_QUESTIONS[:15]
        print(f"⚡ Mode rapide : {len(questions)} questions")
    
    # Charger .env pour les clés API
    _env_path = _ENGINE_DIR / '.env'
    if _env_path.exists():
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")
    
    # Initialiser le moteur
    engine = BenchmarkEngine()
    engine.load_brain(max_facts=args.max_facts)
    
    # Configurations à tester
    configs = [
        {
            "name": "IA Harmonique (base)",
            "type": "harmonic",
            "user_id": None,
            "no_fallback": True,  # pas de web/LLM fallback → latence pure
            "cost_per_query": 0.0,
        },
    ]
    
    # Ajouter DeepSeek si clé dispo
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if deepseek_key and len(deepseek_key) > 10:
        configs.append({
            "name": "DeepSeek (chat)",
            "type": "llm",
            "direct_openai": True,
            "model": "deepseek-chat",
            "api_url": "https://api.deepseek.com/v1/chat/completions",
            "api_key": deepseek_key,
            "cost_per_query": 0.0002,  # DeepSeek est ~50x moins cher que GPT-4
        })
    
    # Lancer le benchmark
    reports = engine.run_benchmark(configs, questions)
    
    # Afficher le rapport
    print_report(reports)
    
    # Exporter si demandé
    if args.export:
        export_data = {}
        for name, report in reports.items():
            export_data[name] = {
                "config": name,
                "total_questions": report.total_questions,
                "avg_f1": report.avg_f1,
                "avg_precision": report.avg_precision,
                "avg_recall": report.avg_recall,
                "avg_contains_answer": report.avg_contains_answer,
                "avg_latency_ms": report.avg_latency_ms,
                "avg_confidence": report.avg_confidence,
                "total_cost_usd": report.total_cost_usd,
                "per_domain": report.per_domain,
                "timestamp": datetime.now().isoformat(),
            }
        
        with open(args.export, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        print(f"\n📁 Rapport exporté : {args.export}")
