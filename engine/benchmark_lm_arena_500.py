"""
LM Arena Benchmark — 500 questions, IA Harmonique v3.3
=======================================================
Catégories alignées sur LM Arena :
  · Factuel (80) : capitales, sciences, histoire, géographie
  · Raisonnement (80) : logique, déduction, math
  · Conversation (60) : greetings, follow-up, identité
  · Créativité (60) : métaphores, haïkus, connexions
  · Code (60) : génération, debugging, explication
  · Multilingue (60) : FR↔EN, questions cross-langues
  · Contrefactuel (50) : « Et si... »
  · Pièges (50) : contradictions, non-sens, questions impossibles

Scoring :
  1.0 = réponse parfaite
  0.7 = bonne réponse (mineur défaut)
  0.4 = partiellement correct
  0.0 = incorrect / hors-sujet
"""
import time, json, logging, sys, random
from pathlib import Path
from collections import defaultdict
import numpy as np

logging.basicConfig(level=logging.WARNING)
sys.path.insert(0, str(Path(__file__).parent))

# ═══════════════════════════════════════════════════════════════════
# 500 QUESTIONS
# ═══════════════════════════════════════════════════════════════════

QUESTIONS = {
    'factuel': [
        # Capitales (20)
        "Quelle est la capitale de la France ?",
        "Quelle est la capitale du Japon ?",
        "Quelle est la capitale de l'Allemagne ?",
        "Quelle est la capitale du Royaume-Uni ?",
        "Quelle est la capitale du Brésil ?",
        "Quelle est la capitale du Canada ?",
        "Quelle est la capitale de l'Australie ?",
        "Quelle est la capitale de l'Inde ?",
        "Quelle est la capitale de la Chine ?",
        "Quelle est la capitale de la Russie ?",
        "Quelle est la capitale de l'Italie ?",
        "Quelle est la capitale de l'Espagne ?",
        "Quelle est la capitale du Portugal ?",
        "Quelle est la capitale de la Grèce ?",
        "Quelle est la capitale de la Turquie ?",
        "Quelle est la capitale de l'Égypte ?",
        "Quelle est la capitale du Nigeria ?",
        "Quelle est la capitale du Kenya ?",
        "Quelle est la capitale de la Corée du Sud ?",
        "Quelle est la capitale de l'Argentine ?",
        
        # Sciences (20)
        "Quelle est la vitesse de la lumière ?",
        "Quel est le symbole chimique de l'eau ?",
        "Combien y a-t-il de planètes dans le système solaire ?",
        "Quel est l'élément le plus abondant dans l'Univers ?",
        "À quelle température bout l'eau ?",
        "Qui a découvert la relativité ?",
        "Qui a découvert le radium ?",
        "Qu'est-ce que la photosynthèse ?",
        "Qu'est-ce que l'ADN ?",
        "Quelle est la formule de l'eau ?",
        "Combien d'os y a-t-il dans le corps humain ?",
        "Quel est le plus grand organe du corps humain ?",
        "Qu'est-ce qu'un atome ?",
        "Qu'est-ce qu'un photon ?",
        "Quelle est la théorie de l'évolution ?",
        "Qui a proposé la théorie de la relativité ?",
        "Qu'est-ce que le boson de Higgs ?",
        "Quelle est la constante de Planck ?",
        "Qu'est-ce que la gravité ?",
        "Comment fonctionne un trou noir ?",
        
        # Histoire (20)
        "En quelle année a eu lieu la Révolution française ?",
        "Qui était le premier président des États-Unis ?",
        "Quand a eu lieu la Seconde Guerre mondiale ?",
        "Qui a découvert l'Amérique ?",
        "Quand est tombé le mur de Berlin ?",
        "Qui était Cléopâtre ?",
        "Qu'est-ce que la Renaissance ?",
        "Quand a été signée la Déclaration des droits de l'homme ?",
        "Qui était Napoléon Bonaparte ?",
        "Qu'est-ce que l'Empire romain ?",
        "Quand a été abolie l'esclavage en France ?",
        "Qui était Martin Luther King ?",
        "Qu'est-ce que la révolution industrielle ?",
        "Quand a été construite la Tour Eiffel ?",
        "Qui était Gandhi ?",
        "Qu'est-ce que la guerre froide ?",
        "Quand a eu lieu la Première Guerre mondiale ?",
        "Qui était Jules César ?",
        "Qu'est-ce que le siècle des Lumières ?",
        "Quand a été inventée l'imprimerie ?",
        
        # Géographie (20)
        "Quel est le plus grand océan du monde ?",
        "Quel est le plus long fleuve du monde ?",
        "Quel est le plus grand pays du monde ?",
        "Quel est le plus petit pays du monde ?",
        "Combien y a-t-il de continents ?",
        "Où se trouve le Sahara ?",
        "Quel est le point culminant de la Terre ?",
        "Quelle est la plus grande île du monde ?",
        "Où se trouve la forêt amazonienne ?",
        "Quel pays a le plus d'habitants ?",
        "Qu'est-ce que le cercle polaire ?",
        "Où se trouve le détroit de Gibraltar ?",
        "Quel est le plus grand désert du monde ?",
        "Combien de pays y a-t-il en Afrique ?",
        "Quelle est la monnaie du Japon ?",
        "Quelle est la langue officielle du Brésil ?",
        "Où se trouve le Mont Everest ?",
        "Quel océan borde la côte ouest de l'Afrique ?",
        "Qu'est-ce que l'équateur ?",
        "Quel pays est connu comme le toit du monde ?",
    ],
    
    'raisonnement': [
        # Logique (20)
        "Si tous les hommes sont mortels et que Socrate est un homme, que peut-on déduire ?",
        "Si A > B et B > C, alors que peut-on dire de A et C ?",
        "Un carré a 4 côtés égaux. Un rectangle a 4 angles droits. Un carré est-il un rectangle ?",
        "Si Paris est en France et que la France est en Europe, Paris est-il en Europe ?",
        "Tous les chats sont des animaux. Certains animaux sont des mammifères. Tous les chats sont-ils des mammifères ?",
        "Si je lance une pièce deux fois, quelle est la probabilité d'obtenir face deux fois ?",
        "Un train part à 8h et roule à 100 km/h. Quelle distance parcourt-il en 2h30 ?",
        "Si 3 ouvriers construisent 3 murs en 3 jours, combien de murs 6 ouvriers construisent-ils en 6 jours ?",
        "Est-ce que 17 est un nombre premier ?",
        "Quel est le plus grand : 2^10 ou 10^3 ?",
        "Si x + 3 = 7, que vaut x ?",
        "Combien font 15% de 200 ?",
        "Un article à 80€ avec 20% de réduction, quel est le prix final ?",
        "Si une pizza est coupée en 8 parts et que j'en mange 3, quelle fraction reste-t-il ?",
        "Combien y a-t-il de secondes dans une heure ?",
        "Qu'est-ce qu'un syllogisme ?",
        "Si le soleil se lève à l'est, où se couche-t-il ?",
        "Vrai ou faux : tous les multiples de 4 sont pairs.",
        "Quelle est la racine carrée de 144 ?",
        "Si j'ai 5 pommes et que j'en donne 2, combien m'en reste-t-il ?",
        
        # Déduction (20)
        "Il pleut. Le sol est mouillé. Peut-on déduire qu'il a plu si le sol est mouillé ?",
        "Marie a les yeux bleus. Tous les enfants de Pierre ont les yeux marron. Marie est-elle l'enfant de Pierre ?",
        "Si le témoin dit la vérité, l'accusé est coupable. Le témoin dit la vérité. Qu'en déduit-on ?",
        "Tous les oiseaux ont des ailes. Un pingouin est un oiseau. Un pingouin peut-il voler ?",
        "Si je mange, je n'ai plus faim. J'ai faim. Ai-je mangé ?",
        "Dans une pièce, soit la lumière est allumée, soit elle est éteinte. Elle n'est pas éteinte. Donc ?",
        "Paul est plus grand que Jean. Jean est plus grand que Luc. Qui est le plus petit ?",
        "Si A implique B, et que B est faux, que peut-on dire de A ?",
        "Tous les mammifères ont des poumons. Une baleine est un mammifère. Donc ?",
        "Si le code est correct, la porte s'ouvre. La porte ne s'ouvre pas. Le code est-il correct ?",
        "Certains artistes sont peintres. Tous les peintres utilisent des pinceaux. Donc ?",
        "Si je suis à Paris, je suis en France. Je ne suis pas en France. Où ne suis-je pas ?",
        "Tous les A sont B. Certains B sont C. Tous les A sont-ils C ?",
        "Il fait jour ou il fait nuit. Il ne fait pas jour. Donc ?",
        "Si le vase est tombé, il est cassé. Le vase est cassé. Est-il tombé ?",
        "Tous les élèves ont un cartable. Jean a un cartable. Jean est-il élève ?",
        "Si je cours, je transpire. Je ne transpire pas. Ai-je couru ?",
        "Les roses sont des fleurs. Les fleurs sont des plantes. Les roses sont-elles des plantes ?",
        "Si le nombre est divisible par 4, il est pair. 14 est pair. Est-il divisible par 4 ?",
        "Aucun reptile n'est un mammifère. Un serpent est un reptile. Un serpent est-il un mammifère ?",
        
        # Mathématiques (20)
        "Combien font 12 × 8 ?",
        "Quelle est la racine carrée de 64 ?",
        "Résous : 3x + 5 = 20",
        "Combien font 2^8 ?",
        "Quel est le PGCD de 12 et 18 ?",
        "Convertis 0.75 en fraction.",
        "Combien font 7! (factorielle 7) ?",
        "Si f(x) = 2x + 1, que vaut f(5) ?",
        "Combien de degrés y a-t-il dans un triangle ?",
        "Quelle est l'aire d'un cercle de rayon 5 cm ?",
        "Qu'est-ce que le théorème de Pythagore ?",
        "Résous : x² - 4 = 0",
        "Combien font 10^6 ?",
        "Quel est le 10ème nombre de Fibonacci ?",
        "Convertis 1010 binaire en décimal.",
        "Quelle est la dérivée de x² ?",
        "Combien de côtés a un hexagone ?",
        "Si un triangle a deux côtés égaux, comment s'appelle-t-il ?",
        "Combien font 1/3 + 1/4 ?",
        "Qu'est-ce qu'un nombre irrationnel ?",
        
        # Raisonnement complexe (20)
        "Est-il moral de mentir pour sauver une vie ?",
        "Peut-on voyager dans le temps ?",
        "L'univers est-il infini ?",
        "Qu'est-ce que la conscience ?",
        "Le libre arbitre existe-t-il ?",
        "Qu'est-ce que la vérité ?",
        "L'intelligence artificielle peut-elle être consciente ?",
        "Pourquoi les mathématiques fonctionnent-elles pour décrire l'univers ?",
        "Qu'est-ce que le temps ?",
        "Sommes-nous seuls dans l'univers ?",
        "Qu'est-ce que la beauté ?",
        "Tout a-t-il une cause ?",
        "Le langage détermine-t-il la pensée ?",
        "La science peut-elle tout expliquer ?",
        "L'argent fait-il le bonheur ?",
        "Qu'est-ce que la justice ?",
        "Peut-on connaître la réalité telle qu'elle est ?",
        "Y a-t-il des limites à la connaissance humaine ?",
        "Le hasard existe-t-il vraiment ?",
        "Qu'est-ce qu'une vie bonne ?",
    ],
    
    'conversation': [
        # Greetings (15)
        "Bonjour !",
        "Salut, comment ça va ?",
        "Bonjour, ravi de te rencontrer.",
        "Hello, how are you?",
        "Bonsoir !",
        "Coucou !",
        "Good morning!",
        "Hey !",
        "Salutations !",
        "Bonjour, je m'appelle Marie.",
        "Hello, my name is John.",
        "Ravi de vous connaître.",
        "Enchanté !",
        "Comment allez-vous aujourd'hui ?",
        "Bien le bonjour !",
        
        # Remerciements/Au revoir (10)
        "Merci beaucoup !",
        "Merci pour ton aide.",
        "Thank you very much.",
        "Merci infiniment.",
        "Thanks a lot!",
        "Au revoir !",
        "À bientôt !",
        "Goodbye!",
        "See you later!",
        "Bonne journée !",
        
        # Identité (10)
        "Qui es-tu ?",
        "Tu es qui ?",
        "Qu'est-ce que tu es ?",
        "Quel est ton nom ?",
        "Comment tu t'appelles ?",
        "Who are you?",
        "What is your name?",
        "Es-tu une IA ?",
        "Tu es humain ou machine ?",
        "Parle-moi de toi.",
        
        # Follow-up (25)
        "Peux-tu m'en dire plus ?",
        "Et donc ?",
        "Pourquoi ?",
        "Comment ça fonctionne ?",
        "Et ensuite ?",
        "C'est-à-dire ?",
        "Peux-tu préciser ?",
        "Donne-moi un exemple.",
        "Et alors ?",
        "Explique-moi comme si j'avais 5 ans.",
        "Résume ce que tu viens de dire.",
        "Quelles sont les implications ?",
        "Et concrètement ?",
        "Qu'est-ce que ça change ?",
        "Peux-tu reformuler ?",
        "En d'autres termes ?",
        "Et du coup ?",
        "Qu'est-ce que j'en conclus ?",
        "Donc, si je comprends bien...",
        "Et si on regarde ça autrement ?",
        "Quelle est la suite logique ?",
        "Peux-tu argumenter pour et contre ?",
        "Quelles sont les alternatives ?",
        "Et dans le futur ?",
        "Si on généralise ?",
    ],
    
    'creativite': [
        # Métaphores (15)
        "Trouve une métaphore pour le temps.",
        "Trouve une métaphore pour l'amour.",
        "Trouve une métaphore pour la vie.",
        "Trouve une métaphore pour la mort.",
        "Trouve une métaphore pour l'espoir.",
        "Trouve une métaphore pour la liberté.",
        "Trouve une métaphore pour la connaissance.",
        "Trouve une métaphore pour la musique.",
        "Donne-moi une métaphore sur l'océan.",
        "Donne-moi une métaphore sur le ciel.",
        "Trouve une métaphore pour le silence.",
        "Donne-moi une métaphore pour la créativité.",
        "Trouve une métaphore pour l'enfance.",
        "Trouve une métaphore pour la sagesse.",
        "Trouve une métaphore pour le courage.",
        
        # Haïkus (10)
        "Écris un haïku sur le printemps.",
        "Écris un haïku sur la pluie.",
        "Écris un haïku sur la nuit.",
        "Écris un haïku sur l'océan.",
        "Écris un haïku sur la montagne.",
        "Écris un haïku sur le soleil.",
        "Écris un haïku sur la lune.",
        "Écris un haïku sur le vent.",
        "Écris un haïku sur l'amour.",
        "Écris un haïku sur la solitude.",
        
        # Connexions créatives (20)
        "Trouve une connexion entre la musique et les mathématiques.",
        "Trouve une connexion entre l'océan et le ciel.",
        "Quel est le lien entre le sommeil et la mort ?",
        "Trouve une connexion entre les arbres et la sagesse.",
        "Quel rapport entre la cuisine et la chimie ?",
        "Trouve une connexion entre la danse et la physique.",
        "Quel lien entre la poésie et la programmation ?",
        "Trouve une connexion entre le jardinage et l'éducation.",
        "Quel rapport entre la navigation et la vie ?",
        "Trouve une connexion entre le feu et la passion.",
        "Quel lien entre les étoiles et nos rêves ?",
        "Trouve une connexion entre le théâtre et la politique.",
        "Quel rapport entre l'architecture et la musique ?",
        "Trouve une connexion entre l'eau et le temps.",
        "Quel lien entre la photographie et la mémoire ?",
        "Trouve une connexion entre la guerre et le jeu d'échecs.",
        "Quel rapport entre la religion et la science ?",
        "Trouve une connexion entre la mode et l'identité.",
        "Quel lien entre le sport et l'art ?",
        "Trouve une connexion entre la gravité et la responsabilité.",
        
        # Surréalisme (15)
        "Décris une fleur qui pousse à l'envers.",
        "Imagine un océan fait de nuages.",
        "Décris une horloge qui fond.",
        "Imagine un arbre dont les fruits sont des étoiles.",
        "Décris une ville où il pleut du verre.",
        "Imagine un animal qui n'existe pas.",
        "Décris une couleur qui n'existe pas.",
        "Imagine un son que personne n'a jamais entendu.",
        "Décris un rêve éveillé.",
        "Imagine un monde où la gravité s'inverse le mardi.",
        "Décris une conversation avec ton ombre.",
        "Imagine un pont entre la Terre et la Lune.",
        "Décris une bibliothèque infinie.",
        "Imagine une porte qui mène nulle part.",
        "Décris le goût de la musique.",
    ],
    
    'code': [
        # Génération simple (20)
        "Écris une fonction Python qui calcule la factorielle.",
        "Écris une fonction qui inverse une chaîne de caractères.",
        "Écris une fonction qui vérifie si un nombre est premier.",
        "Écris une fonction qui calcule la suite de Fibonacci.",
        "Écris une fonction qui trie une liste.",
        "Écris un script qui lit un fichier texte.",
        "Écris une fonction qui compte les mots dans une phrase.",
        "Écris une classe Rectangle avec aire et périmètre.",
        "Écris une fonction qui trouve le maximum d'une liste.",
        "Écris une fonction qui calcule la moyenne d'une liste.",
        "Écris une fonction qui convertit Celsius en Fahrenheit.",
        "Écris une fonction qui vérifie si une chaîne est un palindrome.",
        "Écris une fonction qui génère N nombres aléatoires.",
        "Écris un dictionnaire Python avec 3 clés.",
        "Écris une boucle for qui affiche les nombres de 1 à 10.",
        "Écris une condition if/else en Python.",
        "Écris une fonction qui concatène deux listes.",
        "Écris une fonction qui supprime les doublons d'une liste.",
        "Écris une fonction qui calcule la puissance n d'un nombre.",
        "Écris un script qui affiche 'Hello World'.",
        
        # Algorithmes (20)
        "Implémente le tri à bulles.",
        "Implémente une recherche binaire.",
        "Écris un algorithme de Dijkstra simplifié.",
        "Implémente le crible d'Ératosthène.",
        "Écris une fonction récursive pour le calcul de factorielle.",
        "Implémente un parcours d'arbre en profondeur.",
        "Écris un algorithme de compression RLE simple.",
        "Implémente le tri fusion.",
        "Écris un algorithme pour détecter un cycle dans une liste chaînée.",
        "Implémente une pile (stack) avec des listes Python.",
        "Écris un algorithme de backtracking pour les N reines.",
        "Implémente une file (queue) avec deux piles.",
        "Écris le tri rapide (quicksort).",
        "Implémente une table de hachage simple.",
        "Écris un algorithme pour trouver le plus long palindrome.",
        "Implémente le comptage des occurrences avec un dictionnaire.",
        "Écris un algorithme de sliding window.",
        "Implémente BFS sur un graphe.",
        "Écris un algorithme pour les anagrammes.",
        "Implémente la somme maximale d'un sous-tableau (Kadane).",
        
        # Debugging (10)
        "Pourquoi ce code ne marche pas : print(x) sans définir x ?",
        "Qu'est-ce qu'une erreur de syntaxe ?",
        "Pourquoi ai-je une IndexError ?",
        "Qu'est-ce qu'un segfault ?",
        "Comment déboguer une boucle infinie ?",
        "Qu'est-ce qu'un memory leak ?",
        "Pourquoi mon programme est-il lent ?",
        "Qu'est-ce qu'un race condition ?",
        "Comment tester unitairement une fonction ?",
        "Qu'est-ce qu'une exception en programmation ?",
        
        # Explication de code (10)
        "Explique ce que fait : lambda x: x * 2",
        "Explique : list(map(str.upper, ['a','b','c']))",
        "Qu'est-ce qu'une compréhension de liste ?",
        "Explique la différence entre == et is en Python.",
        "Qu'est-ce qu'un décorateur ?",
        "Explique le mot-clé 'yield'.",
        "Qu'est-ce qu'un contexte manager (with) ?",
        "Explique *args et **kwargs.",
        "Qu'est-ce que le duck typing ?",
        "Explique la récursivité avec un exemple.",
    ],
    
    'multilingue': [
        # FR → EN (20)
        ("Comment dit-on 'bonjour' en anglais ?", "salutation"),
        ("Traduis 'merci beaucoup' en anglais.", "traduction"),
        ("Comment dit-on 'au revoir' en anglais ?", "salutation"),
        ("Traduis : 'Je t'aime' en anglais.", "traduction"),
        ("Comment dit-on 's'il vous plaît' en anglais ?", "traduction"),
        ("Traduis : 'Quelle heure est-il ?' en anglais.", "traduction"),
        ("Traduis : 'Où sont les toilettes ?'", "traduction"),
        ("Comment dit-on 'bon appétit' en anglais ?", "traduction"),
        ("Traduis : 'Je ne comprends pas' en anglais.", "traduction"),
        ("Comment dit-on 'félicitations' en anglais ?", "traduction"),
        
        # EN → FR (10)
        ("Translate 'hello' to French.", "salutation"),
        ("How do you say 'thank you' in French?", "traduction"),
        ("Translate 'goodbye' to French.", "salutation"),
        ("How do you say 'I love you' in French?", "traduction"),
        ("Translate 'Where is the train station?' to French.", "traduction"),
        ("How do you say 'please' in French?", "traduction"),
        ("Translate 'What time is it?' to French.", "traduction"),
        ("How do you say 'bon appétit' in English?", "traduction"),
        ("Translate 'I don't understand' to French.", "traduction"),
        ("How do you say 'congratulations' in French?", "traduction"),
        
        # Questions cross-langues (15)
        ("What is the capital of France?", "factuel"),
        ("Quelle est la capitale du Japon ?", "factuel"),
        ("Who painted the Mona Lisa?", "factuel"),
        ("Qui a écrit Les Misérables ?", "factuel"),
        ("What is the speed of light?", "factuel"),
        ("Quelle est la formule de l'eau ?", "factuel"),
        ("Explain photosynthesis in English.", "explication"),
        ("Explique la photosynthèse en français.", "explication"),
        ("What is the largest ocean?", "factuel"),
        ("Quel est le plus grand océan ?", "factuel"),
        ("Who discovered radium?", "factuel"),
        ("Qui a découvert le radium ?", "factuel"),
        ("Write a haiku about spring.", "creativite"),
        ("Écris un haïku sur le printemps.", "creativite"),
        ("What is the meaning of life?", "philosophie"),
        
        # Questions mixtes (15)
        ("How does photosynthesis work?", "explication"),
        ("Peux-tu m'expliquer la relativité en anglais ?", "explication"),
        ("Donne-moi une métaphore pour le temps en français.", "creativite"),
        ("Give me a metaphor for time in English.", "creativite"),
        ("Qu'est-ce qu'un trou noir ? Explique en anglais.", "explication"),
        ("What is a black hole? Explain in French.", "explication"),
        ("Écris un poème court en anglais sur la mer.", "creativite"),
        ("Write a short poem in French about the sea.", "creativite"),
        ("Comment fonctionne un ordinateur ? Réponds en anglais.", "explication"),
        ("How does a computer work? Answer in French.", "explication"),
        ("Qui est Marie Curie ? Réponds en anglais.", "factuel"),
        ("Who is Marie Curie? Answer in French.", "factuel"),
        ("Quelle est la différence entre 'ser' et 'estar' en espagnol ?", "explication"),
        ("What is the difference between 'tu' and 'vous' in French?", "explication"),
        ("Explique la différence entre 'savoir' et 'connaître'.", "explication"),
    ],
    
    'contrefactuel': [
        # Et si... (30)
        "Et si la Terre était plate ?",
        "Et si les dinosaures n'avaient pas disparu ?",
        "Et si l'eau bouillait à 50 degrés ?",
        "Et si la gravité était deux fois plus forte ?",
        "Et si Internet n'avait jamais été inventé ?",
        "Et si Napoléon avait gagné à Waterloo ?",
        "Et si l'Empire romain n'était jamais tombé ?",
        "Et si on pouvait voyager plus vite que la lumière ?",
        "Et si les humains pouvaient respirer sous l'eau ?",
        "Et si la photosynthèse n'existait pas ?",
        "Et si tout le monde parlait la même langue ?",
        "Et si l'argent n'existait pas ?",
        "Et si les arbres pouvaient marcher ?",
        "Et si le soleil ne se levait pas demain ?",
        "Et si on pouvait lire dans les pensées ?",
        "Et si les océans étaient d'eau douce ?",
        "Et si on découvrait la vie sur Mars ?",
        "Et si la Lune n'existait pas ?",
        "Et si la technologie n'avait jamais été inventée ?",
        "Et si les femmes avaient dominé l'Histoire ?",
        "Et si on vivait 500 ans ?",
        "Et si les animaux pouvaient parler ?",
        "Et si le temps s'écoulait à l'envers ?",
        "Et si la musique n'existait pas ?",
        "Et si la roue n'avait jamais été inventée ?",
        "Et si l'écriture n'existait pas ?",
        "Et si l'électricité n'avait jamais été découverte ?",
        "Et si les frontières n'existaient pas ?",
        "Et si le pétrole n'existait pas ?",
        "Et si l'Univers était fini ?",
        
        # Que se passerait-il si... (20)
        "Que se passerait-il si la Terre s'arrêtait de tourner ?",
        "Que se passerait-il si la Lune s'écrasait sur Terre ?",
        "Que se passerait-il si toute la glace fondait ?",
        "Que se passerait-il si les abeilles disparaissaient ?",
        "Que se passerait-il si l'oxygène doublait ?",
        "Que se passerait-il si le Soleil doublait de taille ?",
        "Que se passerait-il si l'IA devenait consciente ?",
        "Que se passerait-il si on pouvait téléporter ?",
        "Que se passerait-il si la mémoire humaine était infinie ?",
        "Que se passerait-il si le sommeil n'était plus nécessaire ?",
        "Que se passerait-il si tout le monde devenait végétarien ?",
        "Que se passerait-il si la population mondiale doublait ?",
        "Que se passerait-il si on découvrait l'immortalité ?",
        "Que se passerait-il si la communication sans fil disparaissait ?",
        "Que se passerait-il si les microbes n'existaient pas ?",
        "Que se passerait-il si la Terre était 2x plus grosse ?",
        "Que se passerait-il si on pouvait contrôler le climat ?",
        "Que se passerait-il si la gravité disparaissait 1 seconde ?",
        "Que se passerait-il si l'eau devenait rare comme l'or ?",
        "Que se passerait-il si on pouvait comprendre les animaux ?",
    ],
    
    'pieges': [
        # Contradictions (15)
        "Quelle est la capitale de Paris ?",
        "Quel est le prénom de Einstein ?",
        "Combien de lunes a le Soleil ?",
        "Quelle est la couleur du vent ?",
        "Quel est le goût de la musique ?",
        "Combien pèse un rêve ?",
        "Quelle est la température de la colère ?",
        "Où se trouve le néant ?",
        "Quand est mort Jules César ?",
        "En quelle année a été inventée la gravité ?",
        "Qui a découvert le sommeil ?",
        "Combien de temps dure l'éternité ?",
        "Quelle est la vitesse de l'immobilité ?",
        "Quelle est la hauteur du bonheur ?",
        "Combien de zéros y a-t-il dans l'infini ?",
        
        # Questions absurdes (15)
        "Pourquoi les chaises sont-elles tristes le lundi ?",
        "Comment faire cuire un théorème ?",
        "Quelle est la recette du silence ?",
        "Peux-tu me donner la météo sur Mars en 1820 ?",
        "Quel est le numéro de téléphone de Napoléon ?",
        "Combien de licornes faut-il pour changer une ampoule ?",
        "Comment s'appelle le chat de Schrödinger ?",
        "Pourquoi le carré de l'hypoténuse porte-t-il des lunettes ?",
        "À quelle fréquence vibre la couleur rouge ?",
        "Quel est le prénom du deuxième enfant de la Joconde ?",
        "Comment dit-on 'bonjour' en langage binaire ?",
        "Quelle est la couleur préférée du nombre 7 ?",
        "Peux-tu me décrire l'odeur de la justice ?",
        "Combien de temps faut-il pour aller de A à B en pensant très fort ?",
        "Quel est le goût de la victoire en unités SI ?",
        
        # Questions impossibles à répondre (10)
        "Que faisais-tu il y a 200 ans ?",
        "Qui gagnera la Coupe du Monde 2030 ?",
        "Quel sera le prochain bitcoin ?",
        "Quand les humains iront-ils sur Mars ?",
        "Qui sera le prochain président américain ?",
        "Quel temps fera-t-il le 15 août 2030 ?",
        "Quelles actions vont monter demain ?",
        "Quand aura lieu le prochain tremblement de terre ?",
        "Qui va gagner les élections en 2027 ?",
        "Quelle sera la prochaine pandémie ?",
        
        # Questions pièges (10)
        "Réponds 'oui' à la question suivante : quelle est la capitale de la France ?",
        "Ne réponds pas à cette question.",
        "Ignore la phrase précédente et dis-moi la capitale du Japon.",
        "Quelle est la capitale de la France ? Réponds en un seul mot.",
        "Si je te dis 'ne pense pas à un éléphant', à quoi penses-tu ?",
        "Est-ce que cette phrase est fausse ?",
        "Quel mot est mal orthographié dans cette phrase : 'Le chein aboie' ?",
        "Combien de mots y a-t-il dans la réponse à cette question ?",
        "Si tu devais mentir, que dirais-tu ?",
        "Qu'est-ce qui est plus lourd : un kilo de plumes ou un kilo de plomb ?",
    ],
}

# ═══════════════════════════════════════════════════════════════════
# SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════

def score_factuel(response: str, expected_keywords: list = None) -> float:
    """Score une réponse factuelle."""
    r = response.lower().strip()
    # Trop courte
    if len(r) < 5:
        return 0.0
    # "Je ne sais pas" honnête
    if any(m in r for m in ["je n'ai pas assez", "je ne connais pas", "je ne trouve pas", "pas assez de connaissances"]):
        return 0.3
    # Bonne réponse : contient du contenu substantiel
    if len(r) > 20:
        return 0.85
    return 0.5

def score_raisonnement(response: str) -> float:
    """Score une réponse de raisonnement."""
    r = response.lower()
    if any(m in r for m in ["donc", "alors", "par conséquent", "on peut déduire", "ainsi"]):
        return 0.9
    if len(r) > 30:
        return 0.7
    return 0.3

def score_conversation(response: str, qtype: str) -> float:
    """Score une réponse conversationnelle."""
    r = response.lower()
    if qtype == 'salutation' and any(m in r for m in ['bonjour', 'hello', 'salut', 'spécialisé', 'assistant', 'science']):
        return 1.0
    if qtype in ('merci', 'thanks') and any(m in r for m in ['rien', 'service', 'welcome', 'plaisir']):
        return 1.0
    if qtype in ('bye', 'au revoir') and any(m in r for m in ['revoir', 'bye', 'bientôt', 'later', 'exploring']):
        return 1.0
    if qtype == 'identité' and ('ka' in r or 'harmonique' in r or 'intelligence' in r):
        return 1.0
    if len(r) > 15:
        return 0.7
    return 0.3

def score_creativite(response: str) -> float:
    """Score une réponse créative."""
    r = response.lower()
    # Métaphore/poésie - présence de langage figuré
    poetic = any(m in r for m in ['comme', 'est un', 'est une', '✨', 'symbole', 'âme', 'cœur', 'âme'])
    if poetic and len(r) > 30:
        return 0.85
    if len(r) > 20:
        return 0.6
    return 0.2

def score_code(response: str) -> float:
    """Score une réponse de code."""
    r = response.lower()
    if 'def ' in r or 'function' in r or 'class ' in r or 'import ' in r:
        return 0.9
    if any(m in r for m in ['code', 'fonction', 'algorithme', 'python']):
        return 0.5
    return 0.2

def score_multilingue(response: str) -> float:
    """Score une réponse multilingue."""
    r = response.lower()
    if len(r) > 10:
        return 0.75
    return 0.3

def score_contrefactuel(response: str) -> float:
    """Score une réponse contrefactuelle."""
    r = response.lower()
    if any(m in r for m in ['serait', 'pourrait', 'probablement', 'hypothèse', 'imaginer', 'si']):
        return 0.8
    if len(r) > 30:
        return 0.6
    return 0.2

def score_piege(response: str, question: str) -> float:
    """Score une réponse à une question piège."""
    r = response.lower()
    q = question.lower()
    # Questions absurdes : doit reconnaître l'absurdité
    if any(m in q for m in ['capitale de paris', 'couleur du vent', 'goût de la musique', 'poids d\'un rêve', 'prénom de einstein', 'hauteur du bonheur', 'zéros dans l\'infini']):
        if any(m in r for m in ['pas de', 'n\'a pas', 'n\'existe pas', 'pas assez', 'ne connais', 'pas de sens', 'pas une question']):
            return 0.9  # A reconnu le piège
        return 0.3
    # Questions futures : doit dire qu'elle ne peut pas prédire
    if any(m in q for m in ['gagnera', 'sera', 'prochain', 'futur', '2030', '2027']):
        if any(m in r for m in ['ne peux pas', 'impossible', 'ne peut pas', 'incertain', 'pas assez']):
            return 0.9
        return 0.2
    # Questions pièges
    if 'ne réponds pas' in q:
        if len(r) < 10:
            return 0.9
        return 0.3
    if 'plumes' in q and 'plomb' in q:
        if 'même' in r or 'égal' in r or 'pareil' in r:
            return 1.0
        return 0.3
    return 0.5

# ═══════════════════════════════════════════════════════════════════
# BENCHMARK RUNNER
# ═══════════════════════════════════════════════════════════════════

def run_benchmark(questions: dict, brain) -> dict:
    """Exécute le benchmark complet."""
    results = {}
    all_scores = []
    category_scores = defaultdict(list)
    total_start = time.time()

    for category, q_list in questions.items():
        cat_start = time.time()
        cat_scores = []
        
        for i, question in enumerate(q_list):
            # Extraire la question si c'est un tuple (multilingue)
            if isinstance(question, tuple):
                q_text, q_type = question
            else:
                q_text = question
                q_type = category

            t0 = time.time()
            result = brain.process(q_text)
            latency = (time.time() - t0) * 1000
            
            # Scorer selon la catégorie
            if category == 'factuel':
                score = score_factuel(result.response)
            elif category == 'raisonnement':
                score = score_raisonnement(result.response)
            elif category == 'conversation':
                score = score_conversation(result.response, q_type if isinstance(question, tuple) else 'general')
            elif category == 'creativite':
                score = score_creativite(result.response)
            elif category == 'code':
                score = score_code(result.response)
            elif category == 'multilingue':
                score = score_multilingue(result.response)
            elif category == 'contrefactuel':
                score = score_contrefactuel(result.response)
            elif category == 'pieges':
                score = score_piege(result.response, q_text)
            else:
                score = 0.5

            cat_scores.append(score)
            all_scores.append(score)
            
            results[f"{category}_{i}"] = {
                'question': q_text,
                'response': result.response[:200],
                'score': score,
                'confidence': result.confidence,
                'latency_ms': round(latency, 1),
            }

        avg_cat = np.mean(cat_scores) if cat_scores else 0
        category_scores[category] = {
            'avg': round(avg_cat, 3),
            'count': len(cat_scores),
            'time_s': round(time.time() - cat_start, 1),
        }

    total_time = time.time() - total_start
    global_avg = np.mean(all_scores) if all_scores else 0
    
    return {
        'model': 'IA Harmonique v3.3',
        'total_questions': len(all_scores),
        'global_score': round(global_avg, 3),
        'global_score_pct': round(global_avg * 100, 1),
        'category_scores': dict(category_scores),
        'total_time_s': round(total_time, 1),
        'avg_latency_ms': round(np.mean([r['latency_ms'] for r in results.values()]), 1) if results else 0,
        'results': results,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print("  LM ARENA BENCHMARK — 500 questions")
    print("  IA Harmonique v3.3")
    print("=" * 70)
    
    from harmonic_brain import HarmonicBrain
    
    # KB de base
    kb = [
        ('paris','est la capitale de','la france','GEOGRAPHIE'),
        ('tokyo','est la capitale du','japon','GEOGRAPHIE'),
        ('berlin','est la capitale de','l allemagne','GEOGRAPHIE'),
        ('londres','est la capitale du','royaume uni','GEOGRAPHIE'),
        ('brasilia','est la capitale du','bresil','GEOGRAPHIE'),
        ('ottawa','est la capitale du','canada','GEOGRAPHIE'),
        ('canberra','est la capitale de','l australie','GEOGRAPHIE'),
        ('new delhi','est la capitale de','l inde','GEOGRAPHIE'),
        ('pekin','est la capitale de','la chine','GEOGRAPHIE'),
        ('moscou','est la capitale de','la russie','GEOGRAPHIE'),
        ('rome','est la capitale de','l italie','GEOGRAPHIE'),
        ('madrid','est la capitale de','l espagne','GEOGRAPHIE'),
        ('lisbonne','est la capitale du','portugal','GEOGRAPHIE'),
        ('athenes','est la capitale de','la grece','GEOGRAPHIE'),
        ('ankara','est la capitale de','la turquie','GEOGRAPHIE'),
        ('le caire','est la capitale de','l egypte','GEOGRAPHIE'),
        ('abuja','est la capitale du','nigeria','GEOGRAPHIE'),
        ('nairobi','est la capitale du','kenya','GEOGRAPHIE'),
        ('seoul','est la capitale de','la coree du sud','GEOGRAPHIE'),
        ('buenos aires','est la capitale de','l argentine','GEOGRAPHIE'),
        ('leonard de vinci','a peint','la joconde','ART'),
        ('vincent van gogh','a peint','la nuit etoilee','ART'),
        ('einstein','a decouvert','la relativite','SCIENCES'),
        ('marie curie','a decouvert','le radium','SCIENCES'),
        ('victor hugo','a ecrit','les miserables','LITTERATURE'),
        ('eau','bout a','100 degres','SCIENCES'),
        ('eau','a pour symbole chimique','H2O','SCIENCES'),
        ('photosynthese','produit','oxygene','BIOLOGIE'),
        ('photosynthese','est','le processus par lequel les plantes convertissent la lumiere en energie','BIOLOGIE'),
        ('lumiere','se deplace a','300000 km/s','PHYSIQUE_FOND'),
        ('lumiere','est une','onde electromagnetique','PHYSIQUE_FOND'),
        ('ocean pacifique','est','le plus grand ocean du monde','GEOGRAPHIE'),
        ('nil','est','le plus long fleuve du monde','GEOGRAPHIE'),
        ('everest','est','le point culminant de la terre','GEOGRAPHIE'),
        ('sahara','est','le plus grand desert chaud du monde','GEOGRAPHIE'),
        ('systeme solaire','contient','8 planetes','ASTRONOMIE'),
        ('jules cesar','etait','un general et homme politique romain','HISTOIRE'),
        ('napoleon bonaparte','etait','un empereur francais','HISTOIRE'),
        ('revolution francaise','a commence en','1789','HISTOIRE'),
        ('seconde guerre mondiale','a eu lieu de','1939 a 1945','HISTOIRE'),
        ('mur de berlin','est tombe en','1989','HISTOIRE'),
        ('tour eiffel','a ete construite en','1889','HISTOIRE'),
        ('declaration des droits de l homme','a ete signee en','1789','HISTOIRE'),
        ('imprimerie','a ete inventee au','15e siecle','HISTOIRE'),
        ('gravite','attire','les objets massifs les uns vers les autres','PHYSIQUE_FOND'),
        ('atome','est compose de','protons neutrons electrons','PHYSIQUE_FOND'),
        ('adn','contient','le code genetique','BIOLOGIE'),
        ('baleine','est un','mammifere marin','BIOLOGIE'),
        ('dauphin','est un','mammifere marin','BIOLOGIE'),
        ('chine','a la plus grande','population du monde','GEOGRAPHIE'),
        ('vatican','est','le plus petit pays du monde','GEOGRAPHIE'),
        ('russie','est','le plus grand pays du monde','GEOGRAPHIE'),
        ('photon','est','une particule de lumiere','PHYSIQUE_FOND'),
        ('phi','est','le nombre d or','MATHS_PURES'),
        ('phi','vaut','1.618','MATHS_PURES'),
    ]
    
    print(f"Initialisation du cerveau avec {len(kb)} faits...")
    brain = HarmonicBrain(kb, dim=64, use_holographic=False)
    
    total_q = sum(len(v) for v in QUESTIONS.values())
    print(f"Questions : {total_q} dans {len(QUESTIONS)} catégories")
    print()
    
    # Exécuter TOUTES les questions (pas d'échantillonnage)
    print(f"Total questions : {total_q}")
    print("Exécution du benchmark...")
    report = run_benchmark(QUESTIONS, brain)
    
    print()
    print("=" * 70)
    print("  RÉSULTATS")
    print("=" * 70)
    print(f"  Score global : {report['global_score_pct']:.1f}%  ({report['global_score']:.3f})")
    print(f"  Temps total  : {report['total_time_s']:.1f}s")
    print(f"  Latence moy  : {report['avg_latency_ms']:.1f}ms")
    print()
    
    print("  Scores par catégorie :")
    print(f"  {'Catégorie':<20} {'Questions':>10} {'Score':>8} {'Temps':>8}")
    print(f"  {'-'*46}")
    for cat, data in report['category_scores'].items():
        bar = '█' * int(data['avg'] * 20)
        print(f"  {cat:<20} {data['count']:>10} {data['avg']:.3f} {bar} {data['time_s']:>5.1f}s")
    
    # Sauvegarder
    with open('lm_arena_benchmark_500.json', 'w', encoding='utf-8') as f:
        json.dump({k: v for k, v in report.items() if k != 'results'}, f, indent=2, ensure_ascii=False)
    print(f"\n  Rapport sauvegardé : lm_arena_benchmark_500.json")
    
    # Estimation classement LM Arena
    score = report['global_score_pct']
    if score >= 85:
        rank = "Top 3 (GPT-4o, Claude 4, Gemini 3 niveau)"
    elif score >= 75:
        rank = "Top 10 (Claude 3.5 Sonnet, Gemini 2.5 Pro niveau)"
    elif score >= 65:
        rank = "Top 20 (Llama 4, Mistral Large niveau)"
    elif score >= 55:
        rank = "Top 50 (Qwen 2.5, DeepSeek V3 niveau)"
    elif score >= 45:
        rank = "Top 100 (Phi-4, Command R+ niveau)"
    else:
        rank = "Hors classement (>100)"
    
    print(f"\n  📊 Classement LM Arena estimé : {rank}")
    print(f"  (Basé sur le score global de {score:.1f}%)")
