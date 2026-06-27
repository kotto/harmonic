#!/usr/bin/env python3
"""Sync ia_harmonic_number1.py (EN) → ia_harmonique_n1.py (FR)"""
import re

with open('ia_harmonic_number1.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace EN→FR function names, keywords, messages
replacements = [
    ("def extract_numbers_smart(", "def extraire_nombres_intelligents("),
    ("def analyze_problem_en(", "def analyser_probleme_n1("),
    ("def extract_params_domain_en(", "def extraire_params_domaine("),
    ("def extract_poly_coeffs_en(", "def extraire_coeffs_poly_robuste("),
    ("def extract_arithmetic_op_en(", "def extraire_operation_arith_robuste("),
    ("def extract_ode_params_en(", "def extraire_edo_params_robuste("),
    ("def extract_opt_params_en(", "def extraire_opt_params_robuste("),
    ("def extract_geo_params_en(", "def extraire_geo_params_robuste("),
    ("def extract_proba_params_en(", "def extraire_probas_params_robuste("),
    ("def extract_logic_params_en(", "def extraire_logique_params_robuste("),
    ("def extract_number_theory_params_en(", "def extraire_theorie_params_robuste("),
    ("def solve_n1(", "def resoudre_n1("),
    ("def find_roots(", "def trouver_racines("),
    ("def refine_root(", "def affiner_racine("),
    ("def find_complex_roots(", "def trouver_racines_complexes("),
    ("def roots_from_factors(", "def racines_depuis_facteurs("),
    ("def solve_linear_ode(", "def resoudre_edo_lineaire("),
    ("def compute_geometry(", "def calculer_geometrie("),
    ("def compute_probability(", "def calculer_probas("),
    ("def evaluate_logic(", "def evaluer_logique("),
    ("def count_dice_sum_ways(", "def compter_sommes_des("),
    ("def wave_gcd(", "def pgcd_ondulatoire("),
    ("def wave_lcm(", "def ppcm_ondulatoire("),
    ("def is_prime_wave(", "def est_premier_ondulatoire("),
    ("def prime_factors(", "def facteurs_premiers("),
    ("def start_server(", "def lancer_serveur("),
]

# EN keywords → FR keywords
en_kw_start = content.find("KEYWORDS = {")
en_kw_end = content.find("\n}\n", en_kw_start) + 3
fr_keywords = """KEYWORDS = {
    'edo': ["y''","y'",'y"','equation differentielle','edo','y(0)=','derivee seconde','solution de','equa diff'],
    'optimisation': ['minimum','maximum','optimiser','minimiser','maximiser','optimum','trouver le minimum','trouver le maximum','point minimum','point maximum','valeur minimale','valeur maximale'],
    'polynome': ['polynome','equation','racine','resoudre','factoriser','x²','x^2','x³','x^3','degre','quadratique','cubique','trouver les racines','trouver x','resous','solution de'],
    'geometrie': ['aire','perimetre','volume','triangle','cercle','carre','rectangle','sphere','cone','cylindre','pyramide','cote','rayon','diametre','hauteur','largeur','longueur','surface','geometrie','hypotenuse','pythagore','thales'],
    'probas': ['probabilite','probabilites','tirage','de','des','urne','boule','chance','pourcentage','statistique','moyenne','ecart-type','variance','mediane','quartile','loi','binomiale','normale','poisson'],
    'logique': ['logique','proposition','vrai','faux','et','ou','non','implique','equivalence','table de verite','tautologie','contradiction','modus ponens','syllogisme'],
    'arithmetique': ['calculer','addition','multiplication','somme','produit','quotient','difference','divise','fois','+','-','*','/','×','combien','font','donne','vaut','que vaut','que donne','donne','difference entre','ajouter','retrancher','multiplier','diviser','ajoute','retire','fois','multiplie','divise','soustraire','oter','plus','moins'],
    'analyse': ['derivee','deriver','differentielle','tangente','pente','integrale','integrer','aire sous','surface','primitive','limite','tendre','converge','diverge','suite','serie'],
    'theorie_nombres': ['premier','premiers','diviseur','multiple','pgcd','ppcm','congruence','modulo','pair','impair','crible','eratosthene','factoriser','facteur','factorisation','divisibilite','nombre premier','nombres premiers'],
}"""
content = content[:en_kw_start] + fr_keywords + content[en_kw_end:]

# EN strong weights → FR strong weights
en_sw_start = content.find("STRONG_WEIGHTS = {")
en_sw_end = content.find("    }\n", en_sw_start) + 6
fr_strong = """    STRONG_WEIGHTS = {
        'polynome': ['x²','x^2','x³','x^3','x⁴','x^4','polynome','racine','racines','factoriser','degre','quadratique','cubique'],
        'edo': ["y''","y'",'y"','equation differentielle','edo','equa diff'],
        'geometrie': ['aire','perimetre','volume','triangle','cercle','carre','rectangle','sphere','cone','cylindre','pyramide','hypotenuse','pythagore'],
        'theorie_nombres': ['premier','premiers','pgcd','ppcm','congruence','modulo','crible','eratosthene','nombre premier'],
        'optimisation': ['minimum','maximum','optimiser','minimiser','maximiser','optimum'],
        'analyse': ['derivee','integrale','limite','primitive','tendre','converge','diverge'],
        'probas': ['probabilite','probabilites','tirag','urne','boule','statistique','variance','ecart-type','loi'],
        'logique': ['logique','proposition','tautologie','syllogisme','table de verite'],
        'arithmetique': ['calculer','combien','font','donne','vaut','que vaut','que donne'],
    }"""
content = content[:en_sw_start] + fr_strong + content[en_sw_end:]

# Apply bulk text replacements
for old, new in replacements:
    content = content.replace(old, new)

# Fix analyzer return keys: 'domain'→'domaine', 'confidence'→'confiance', 'unknown'→'indetermine'
content = content.replace("best = max(scores, key=scores.get)", "meilleur = max(scores, key=scores.get)")
content = content.replace("confidence = min(scores[best] / 6.0, 1.0)", "confiance = min(scores[meilleur] / 6.0, 1.0)")
content = content.replace("'domain': best", "'domaine': meilleur")
content = content.replace("'confidence': confidence", "'confiance': confiance")
content = content.replace("'domain': 'unknown'", "'domaine': 'indetermine'")
content = content.replace("analysis = analyze_problem_en", "analyse = analyser_probleme_n1")
content = content.replace("d = analysis['domain']; p = analysis['params']", "d = analyse['domaine']; p = analyse['params']")
content = content.replace("'domain': d,", "'domaine': d,")

# Domain keys in keyword dict: polynomial→polynome, arithmetic→arithmetique, etc.
content = content.replace("'polynomial'", "'polynome'")
content = content.replace("'arithmetic'", "'arithmetique'")
content = content.replace("'number_theory'", "'theorie_nombres'")
content = content.replace("'probability'", "'probas'")

# Shape names → FR
content = content.replace("'circle'", "'cercle'")
content = content.replace("'square'", "'carre'")

# Benchmark problems
bench_fr = [
    ("Solve x² + 3x - 4 = 0", "Résoudre x² + 3x - 4 = 0"),
    ("Compute 5 + 7", "Calculer 5 + 7"),
    ("Multiply 6 by 8", "Multiplication de 6 par 8"),
    ("How much is 123 plus 456?", "Combien font 123 plus 456 ?"),
    ("Solve x² - 5x + 6 = 0", "Résoudre x² - 5x + 6 = 0"),
    ("What is 100 divided by 4?", "Que vaut 100 divisé par 4 ?"),
    ("Find the minimum of x²", "Trouver le minimum de x²"),
    ("Solve the equation x³ - 9x = 0", "Résoudre l'équation x³ - 9x = 0"),
    ("Compute the difference between 100 and 37", "Calculer la différence entre 100 et 37"),
    ("Solve x² - 9 = 0", "Résoudre x² - 9 = 0"),
    ("Multiply (-4) by 7", "Multiplication de (-4) par 7"),
    ("What is 7 times 8?", "Combien font 7 fois 8 ?"),
    ("Solve x² - 2x + 1 = 0", "Résoudre x² - 2x + 1 = 0"),
    ("What is 30 divided by 6?", "Que vaut 30 divisé par 6 ?"),
    ("Compute 10 minus 3", "Calculer 10 moins 3"),
    ("Solve (x-1)(x-2)(x-3) = 0", "Résoudre (x-1)(x-2)(x-3) = 0"),
    ("Find the minimum of x² starting from x₀=10", "Trouver le minimum de x² en partant de x₀=10"),
    ("What is the area of a circle of radius 5?", "Quelle est l'aire d'un cercle de rayon 5 ?"),
    ("Is 17 a prime number?", "17 est-il un nombre premier ?"),
    ("GCD of 24 and 36", "PGCD de 24 et 36"),
    ("Solve x² + 1 = 0", "Résoudre x² + 1 = 0"),
    ("Compute the perimeter of a square of side 4", "Calculer le périmètre d'un carré de côté 4"),
    ("What is the probability of getting a sum of 7 with 2 dice?", "Quelle est la probabilité d'obtenir une somme de 7 avec 2 dés ?"),
    ("What is the area of a rectangle of length 6 and width 4?", "Quelle est l'aire d'un rectangle de longueur 6 et largeur 4 ?"),
    ("Is 97 a prime number?", "97 est-il un nombre premier ?"),
    ("Solve x³ - 6x² + 11x - 6 = 0", "Résoudre x³ - 6x² + 11x - 6 = 0"),
    ("Find the LCM of 12 and 18", "Trouver le PPCM de 12 et 18"),
    ("What is the volume of a sphere of radius 3?", "Quel est le volume d'une sphère de rayon 3 ?"),
    ("What is the probability of getting 2 heads in 3 coin flips?", "Quelle est la probabilité d'obtenir 2 faces en 3 lancers de pièce ?"),
    ("Evaluate the truth table for P implies Q", "Évaluer la table de vérité de P implique Q"),
    ("Compute the area of a triangle of side 5", "Calculer l'aire d'un triangle de côté 5"),
    ("Solve x⁴ - 5x² + 4 = 0", "Résoudre x⁴ - 5x² + 4 = 0"),
]
for en_text, fr_text in bench_fr:
    content = content.replace(f'"{en_text}"', f'"{fr_text}"')

# Output messages
content = content.replace("HARMONIC AI #1 v2 — BENCHMARK", "IA HARMONIQUE N°1 v2 — BENCHMARK")
content = content.replace("failures", "échecs")
content = content.replace("Total time", "Temps total")
content = content.replace("Results exported", "Résultats exportés")
content = content.replace("  🌊 HARMONIC AI #1 v2 — Ready for LM Arena", "  🌊 IA HARMONIQUE N°1 v2 — Prête pour LM Arena")
content = content.replace("HARMONIC AI #1", "IA HARMONIQUE N°1")
content = content.replace("Harmonic AI #1", "IA Harmonique N°1")
content = content.replace("is a prime number", "est un nombre premier")
content = content.replace("is NOT prime (factors:", "n'est PAS premier (facteurs :")
content = content.replace("Domain not solvable yet", "Domaine non résoluble")
content = content.replace("Could not extract coefficients", "Impossible d'extraire les coefficients")

# Main block args
content = content.replace("'--server', '-s', type=int, default=None, help='Start API server on given port'",
                          "'--serveur', '-s', type=int, default=None, help='Lancer le serveur API sur le port spécifié'")
content = content.replace("'--extended', '-e', action='store_true', help='Run extended 35-problem benchmark (with new solvers)'",
                          "'--etendu', '-e', action='store_true', help='Lancer le benchmark étendu 35 problèmes'")
content = content.replace("'--problem', '-p', type=str, default=None, help='Solve a problem'",
                          "'--probleme', '-p', type=str, default=None, help='Résoudre un problème'")
content = content.replace("if args.server:", "if args.serveur:")
content = content.replace("elif args.problem:", "elif args.probleme:")
content = content.replace("elif args.extended:", "elif args.etendu:")
content = content.replace("  --server PORT   : Start HTTP API", "  --serveur PORT  : Lancer l'API HTTP")
content = content.replace("  --extended      : Run 35-problem extended benchmark", "  --etendu        : Lancer le benchmark étendu 35 problèmes")
content = content.replace("  --problem TEXT  : Solve a problem", "  --probleme TEXT : Résoudre un problème")
content = content.replace("'model': 'Harmonic AI #1 v2'", "'modele': 'IA Harmonique N°1 v2'")

# Domain names in benchmark display and resolver
content = content.replace("d == 'polynomial':", "d == 'polynome':")
content = content.replace("d == 'optimization':", "d == 'optimisation':")
content = content.replace("d == 'ode':", "d == 'edo':")
content = content.replace("d == 'arithmetic':", "d == 'arithmetique':")
content = content.replace("if d == 'polynomial'", "if d == 'polynome'")
content = content.replace("if d == 'arithmetic'", "if d == 'arithmetique'")
content = content.replace("if d == 'ode'", "if d == 'edo'")
content = content.replace("if d == 'optimization'", "if d == 'optimisation'")
content = content.replace("if d == 'geometry'", "if d == 'geometrie'")
content = content.replace("if d == 'probability'", "if d == 'probas'")
content = content.replace("if d == 'logic'", "if d == 'logique'")
content = content.replace("if d == 'number_theory'", "if d == 'theorie_nombres'")
content = content.replace("d in ('geometry','number_theory','probability','logic')", "d in ('geometrie','theorie_nombres','probas','logique')")

# Geometry shapes extractor → FR
content = content.replace("for s in ['triangle','square','rectangle','sphere','cone','cylinder','pyramid','circle']:",
                          "for f in ['triangle','carre','rectangle','sphere','cone','cylindre','pyramide','cercle']:")
content = content.replace("if s in text.lower():\n            shape = s\n            break",
                          "if f in text.lower():\n            forme = f\n            break")
content = content.replace("shape = params.get('shape',", "forme = params.get('forme',")
content = content.replace("if shape ==", "if forme ==")
content = content.replace("'Shape'", "'Forme'")
content = content.replace("not yet implemented", "non implémentée")

# Geometry keys
content = content.replace("'radius': param", "'rayon': param")
content = content.replace("'side': param", "'cote': param")
content = content.replace("'length': l, 'width': w", "'longueur': l, 'largeur': w")
content = content.replace("'radius': r, 'height': h", "'rayon': r, 'hauteur': h")
content = content.replace("'base_side': s, 'height': h", "'cote_base': s, 'hauteur': h")

# Probability → FR keywords
content = content.replace("['dice','die']", "['de','des']")
content = content.replace("['coin','flip','heads','tails']", "['piece','lancer','face','pile']")
content = content.replace("['card','deck','ace','king','queen','jack','heart','spade','diamond','club']",
                          "['carte','jeu','as','roi','dame','valet','coeur','pique','carreau','trefle']")
content = content.replace("['urn','ball','red','blue','green','white','black','yellow']",
                          "['urne','boule','rouge','bleu','vert','blanc','noir','jaune']")
content = content.replace("for color in ['red','blue','green','white','black','yellow']:",
                          "for couleur in ['rouge','bleu','vert','blanc','noir','jaune']:")
content = content.replace("colors[color]", "couleurs[couleur]")
content = content.replace("params['colors'] = colors", "params['couleurs'] = couleurs")
content = content.replace("'colors': colors", "'couleurs': couleurs")
content = content.replace("colors = params.get('colors', {})", "couleurs = params.get('couleurs', {})")
content = content.replace("sum(colors.values())", "sum(couleurs.values())")
content = content.replace("'total_balls':", "'total_boules':")
content = content.replace("'deck_size': 52", "'taille_jeu': 52")
content = content.replace("math.comb(deck_size,", "math.comb(taille_jeu,")
content = content.replace("'total_combinations':", "'combinaisons_totales':")
content = content.replace("'probability_pct':", "'probabilite_pct':")

# Prime/Factor detection → FR
content = content.replace("if 'prime' in text_lower or 'primes' in text_lower:", "if 'premier' in text_lower or 'premiers' in text_lower:")
content = content.replace("if 'factor' in text_lower or 'factorization' in text_lower:", "if 'factor' in text_lower or 'factorisation' in text_lower:")

# Logic → FR keywords
content = content.replace("['a', 'an', 'the', 'is', 'if', 'then', 'and', 'or', 'not', 'true', 'false',",
                          "['un', 'une', 'le', 'la', 'les', 'est', 'si', 'alors', 'et', 'ou', 'non', 'vrai', 'faux',")
content = content.replace("'P AND Q'", "'P ET Q'")
content = content.replace("'P OR Q'", "'P OU Q'")
content = content.replace("'TAUTOLOGY", "'TAUTOLOGIE")
content = content.replace("'CONTRADICTION", "'CONTRADICTION")
content = content.replace("'CONTINGENT", "'CONTINGENT")
content = content.replace("'property':", "'propriete':")

# Geometry extractor: default shape → forme
content = content.replace("shape = 'cercle'", "forme = 'cercle'")
content = content.replace("result = {'shape': shape", "result = {'forme': forme")
content = content.replace("return {'shape': shape", "return {'forme': forme")

# BENCHMARK variable names
content = content.replace("BENCHMARK_PROBLEMS_V2", "PROBLEMES_BENCHMARK_V2")
content = content.replace("BENCHMARK_PROBLEMS", "PROBLEMES_BENCHMARK")

# Docstring header
content = content.replace("HARMONIC AI #1 — Complete Pipeline for LM Arena (v2 — Bugfixes & Full Solvers)",
                          "IA HARMONIQUE N°1 — Pipeline complet pour LM Arena (v2 — Corrections & Solveurs complets)")
content = content.replace("Corrections applied:", "Corrections appliquées :")
content = content.replace("Bugfixes & Full Solvers", "Corrections & Solveurs complets")

# Write
with open('ia_harmonique_n1.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("FR sync complete → ia_harmonique_n1.py")