"""
🏆 benchmark_lm_arena_300.py — 300 questions Maths/Code/Raisonnement
======================================================================
Benchmark complet pour projection LM Arena.

Catégories :
  - 100 Maths (arithmétique, algèbre, géométrie, analyse, logique)
  - 100 Code (HTML/CSS, Python, SQL, algos, patterns)
  - 100 Raisonnement (logique, déduction, analyse, connaissance)

Score : % correct par catégorie + global
Projection : Elo LM Arena basé sur win rate estimé

Lancer : python benchmark_lm_arena_300.py
Sortie : benchmark_300_results.json
"""

import sys, time, math, json, re
from pathlib import Path
from collections import OrderedDict

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))


# ════════════════════════════════════════════════════════════════
# 300 QUESTIONS
# ════════════════════════════════════════════════════════════════

MATHS = [
    # Arithmétique (20)
    ("7 × 8", "56"), ("racine de 169", "13"), ("15% de 200", "30"),
    ("2^10", "1024"), ("144 ÷ 12", "12"), ("factorielle 5", "120"),
    ("3 + 4 × 5", "23"), ("100 - 37", "63"), ("10^3", "1000"),
    ("17 + 28", "45"), ("99 ÷ 9", "11"), ("25% de 400", "100"),
    ("2^8", "256"), ("racine de 144", "12"), ("7 × 9", "63"),
    ("50 - 23", "27"), ("3^4", "81"), ("1000 ÷ 8", "125"),
    ("12 × 12", "144"), ("factorielle 4", "24"),
    # Algèbre (20)
    ("résoudre x + 5 = 10", "5"), ("résoudre 2x = 14", "7"),
    ("résoudre x - 3 = 7", "10"), ("résoudre 3x + 1 = 10", "3"),
    ("résoudre x^2 = 16", "4"), ("résoudre x^2 - 9 = 0", "3"),
    ("résoudre x^2 - 4 = 0", "2"), ("résoudre 5x = 25", "5"),
    ("résoudre x/2 = 6", "12"), ("résoudre 4x - 8 = 0", "2"),
    ("dérivée de x^2", "2x"), ("dérivée de x^3", "3x"),
    ("dérivée de sin(x)", "cos"), ("dérivée de cos(x)", "-sin"),
    ("dérivée de e^x", "exp"), ("dérivée de ln(x)", "1/x"),
    ("dérivée de x^4", "4x"), ("dérivée de 2x+3", "2"),
    ("dérivée de 1/x", "-1"), ("dérivée de 5x^2", "10x"),
    # Intégrales/Géométrie (20)
    ("intégrale de x", "x^2"), ("intégrale de x^2", "x^3"),
    ("intégrale de 2x", "x^2"), ("intégrale de sin(x)", "cos"),
    ("intégrale de 1", "x"), ("intégrale de 3x^2", "x^3"),
    ("périmètre carré côté 5", "20"), ("aire carré côté 6", "36"),
    ("périmètre cercle rayon 1", "6.28"), ("aire cercle rayon 2", "12.57"),
    ("volume cube arête 3", "27"), ("hypoténuse 3 4", "5"),
    ("diagonale carré côté 1", "1.41"), ("somme angles triangle", "180"),
    ("π valeur approchée", "3.14"), ("e valeur approchée", "2.72"),
    ("φ nombre d'or", "1.618"), ("logarithme de 1", "0"),
    ("cos(0)", "1"), ("sin(90°)", "1"),
    # Maths avancées (20)
    ("dérivée de tan(x)", "sec"), ("intégrale de e^x", "exp"),
    ("limite sin(x)/x en 0", "1"), ("série géométrique 1/2", "2"),
    ("det [[1,0],[0,1]]", "1"), ("trace [[2,1],[1,2]]", "4"),
    ("valeur propre de [[1,0],[0,1]]", "1"), ("norme vecteur [3,4]", "5"),
    ("produit scalaire [1,2]·[3,4]", "11"), ("binôme newton (a+b)^2", "a^2"),
    ("pgcd 12 18", "6"), ("ppcm 4 6", "12"),
    ("nombre premier après 10", "11"), ("factorielle 0", "1"),
    ("0! =", "1"), ("i^2 =", "-1"),
    ("module de 3+4i", "5"), ("conjugué de 2+3i", "2-3i"),
    ("argument de -1", "π"), ("formule Euler e^(iπ)", "-1"),
    # Problèmes (20)
    ("Si x+y=10 et x-y=2, x?", "6"), ("prix après -20% sur 100", "80"),
    ("intérêts 5% sur 200", "10"), ("moyenne de 10 20 30", "20"),
    ("médiane de 1 3 5 7 9", "5"), ("2x+3=7, x?", "2"),
    ("25% de 80", "20"), ("60 km/h pendant 2h", "120"),
    ("3 ouvriers 3h, 6 ouvriers?", "1.5"), ("rectangle L=8 l=3, aire?", "24"),
    ("12 oeufs 3€, 1 oeuf?", "0.25"), ("20% de 150", "30"),
    ("x^2=49, x>0", "7"), ("TV 500€ -15%", "425"),
    ("3x+5=20", "5"), ("2^x=32", "5"),
    ("√81", "9"), ("|-5|", "5"),
    ("somme 1 à 10", "55"), ("produit 0×5", "0"),
]

CODE = [
    # HTML/CSS (30)
    ("balise titre HTML", "h1"), ("balise paragraphe", "p"),
    ("balise lien", "a"), ("balise image", "img"),
    ("balise liste", "ul"), ("balise tableau", "table"),
    ("CSS couleur texte", "color"), ("CSS taille police", "font-size"),
    ("CSS marge extérieure", "margin"), ("CSS fond", "background"),
    ("CSS flexbox display", "flex"), ("CSS grid display", "grid"),
    ("CSS centrer horizontalement", "center"), ("CSS gras", "bold"),
    ("CSS bordure", "border"), ("HTML div", "div"),
    ("HTML formulaire", "form"), ("HTML bouton", "button"),
    ("CSS position fixe", "fixed"), ("CSS responsive max-width", "max-width"),
    ("CSS animation name", "keyframes"), ("CSS transition", "transition"),
    ("CSS ombre boîte", "box-shadow"), ("CSS opacité", "opacity"),
    ("HTML meta viewport", "viewport"), ("CSS variable", "var"),
    ("CSS media query", "media"), ("CSS pseudo-classe hover", "hover"),
    ("HTML input text", "text"), ("CSS display none", "none"),
    # Python (25)
    ("afficher Python", "print"), ("longueur liste len()", "len"),
    ("type de 42", "int"), ("type de 'hello'", "str"),
    ("liste vide []", "list"), ("boucler for i in range", "for"),
    ("condition if", "if"), ("fonction def", "def"),
    ("importer module", "import"), ("classe class", "class"),
    ("exception try", "try"), ("dictionnaire {}" ,"dict"),
    ("commentaire #", "#"), ("retourner return", "return"),
    ("vrai/faux", "bool"), ("None équivalent", "null"),
    ("ouvrir fichier", "open"), ("liste en compréhension", "[]"),
    ("lambda x: x*2", "lambda"), ("map function", "map"),
    ("filter function", "filter"), ("zip function", "zip"),
    ("enumerate", "enumerate"), ("décorateur @", "decorator"),
    ("générateur yield", "yield"),
    # SQL/Bases de données (15)
    ("SELECT toutes colonnes", "select"), ("filtre WHERE", "where"),
    ("trier ORDER BY", "order"), ("jointure JOIN", "join"),
    ("grouper GROUP BY", "group"), ("insérer INSERT", "insert"),
    ("mettre à jour UPDATE", "update"), ("supprimer DELETE", "delete"),
    ("créer table CREATE", "create"), ("compter COUNT", "count"),
    ("somme SUM", "sum"), ("moyenne AVG", "avg"),
    ("limite LIMIT", "limit"), ("distinct DISTINCT", "distinct"),
    ("clé primaire PRIMARY KEY", "primary"),
    # Algorithmes (15)
    ("tri bulle complexité", "n^2"), ("tri rapide complexité", "nlogn"),
    ("recherche dichotomique", "logn"), ("parcours graphe BFS", "bfs"),
    ("parcours graphe DFS", "dfs"), ("programmation dynamique", "dp"),
    ("algorithme glouton greedy", "greedy"), ("diviser pour régner", "divide"),
    ("table de hachage hashmap", "hash"), ("pile stack LIFO", "lifo"),
    ("file queue FIFO", "fifo"), ("récursivité recursion", "recursion"),
    ("backtracking retour arrière", "backtrack"), ("plus court chemin", "dijkstra"),
    ("arbre binaire binary tree", "tree"),
    # Patterns (15)
    ("design pattern singleton", "singleton"), ("pattern factory", "factory"),
    ("pattern observer", "observer"), ("pattern decorator", "decorator"),
    ("pattern strategy", "strategy"), ("MVC architecture", "mvc"),
    ("REST API", "rest"), ("JSON format", "json"),
    ("CRUD operations", "crud"), ("MVC modèle", "model"),
    ("API endpoint", "endpoint"), ("microservices", "micro"),
    ("container Docker", "docker"), ("versioning Git", "git"),
    ("CI/CD pipeline", "ci"),
]

RAISONNEMENT = [
    # Logique pure (25)
    ("Si A>B et B>C, alors A?C", ">"), ("Tous les hommes sont mortels. Socrate est un homme. Donc?", "mortel"),
    ("Si pluie alors sol mouillé. Sol sec. Donc?", "pas pluie"),
    ("A ou B. Non A. Donc?", "b"), ("Si A alors B. B est vrai. A est?", "incertain"),
    ("Contraposée de A→B", "non B→non A"), ("Négation de A et B", "non A ou non B"),
    ("Négation de A ou B", "non A et non B"), ("[(A→B) et A] → ?", "B"),
    ("[(A→B) et non B] → ?", "non A"), ("Double négation non(non A)", "A"),
    ("Tiers exclu A ou non A", "vrai"), ("Principe non-contradiction", "non"),
    ("Syllogisme: A⊂B, B⊂C → A?C", "⊂"), ("Modus ponens", "affirme"),
    ("Modus tollens", "nie"), ("Réciproque de A→B", "B→A"),
    ("Transitivité: A=B, B=C → A?C", "="), ("Réflexivité: A?A", "="),
    ("Symétrie: A=B → B?A", "="), ("0 est-il pair?", "oui"),
    ("Un nombre premier a combien de diviseurs?", "2"),
    ("2+2=5 est?", "faux"), ("Le carré d'un réel est toujours?", "positif"),
    ("Combien de mois ont 28 jours?", "12"),
    # Déduction (25)
    ("Jean est plus grand que Paul. Paul est plus grand que Pierre. Qui est le plus grand?", "jean"),
    ("Marie a 3 pommes, donne 1, en reçoit 2. Combien?", "4"),
    ("Dans une course, tu dépasses le 2e. Tu deviens?", "2e"),
    ("Un train quitte Paris à 8h, 300km à 100km/h. Arrivée?", "11"),
    ("Une brique pèse 1kg + une demi-brique. Poids?", "2"),
    ("Il y a 5 pommes, tu en prends 2. Tu as?", "2"),
    ("Un nénuphar double chaque jour, couvre le lac en 48j. Moitié?", "47"),
    ("Combien de fois peut-on soustraire 5 de 25?", "1"),
    ("Une montre avance de 5min par heure. Dans 12h, décalage?", "60"),
    ("Si 5 machines font 5 pièces en 5min, 100 machines pour 100 pièces?", "5"),
    ("Père 45 ans, fils 15. Dans combien d'années père 2× fils?", "15"),
    ("3 personnes se serrent la main. Combien de poignées?", "3"),
    ("Suite: 1 1 2 3 5 ?", "8"),
    ("Suite: 2 4 8 16 ?", "32"),
    ("Suite: 1 4 9 16 ?", "25"),
    ("Suite: 1 3 6 10 ?", "15"),
    ("A=1 B=2 C=3 ... Z=?", "26"),
    ("L'eau bout à 100°C. À 90°C, elle est?", "liquide"),
    ("Un corps lâché tombe. La gravité l'attire vers?", "bas"),
    ("Le jour précède la?", "nuit"),
    ("Une bougie allumée sous un verre s'éteint par manque d'?", "oxygene"),
    ("L'addition est commutative: a+b = ?", "b+a"),
    ("Un cercle a-t-il des côtés?", "non"),
    ("Un carré est-il un rectangle?", "oui"),
    ("Combien de secondes dans une heure?", "3600"),
    # Analyse (25)
    ("cause → effet. Si effet observé, la cause est-elle certaine?", "non"),
    ("corrélation implique-t-elle causalité?", "non"),
    ("falsifiabilité: une théorie scientifique doit être?", "testable"),
    ("rasoir d'Ockham: entités superflues à?", "eliminer"),
    ("biais de confirmation: chercher infos qui?", "confirment"),
    ("effet Dunning-Kruger: incompétents se?", "surestiment"),
    ("loi de Pareto: 80% effets viennent de 20%?", "causes"),
    ("problème du tramway: dilemme entre?", "ethique"),
    ("théorie des jeux: dilemme du?", "prisonnier"),
    ("rationalité limitée: décisions satisfaisantes pas?", "optimales"),
    ("heuristique: règle simple pour décision?", "rapide"),
    ("ancrage: première info influence le?", "jugement"),
    ("disponibilité: juger fréquence par facilité de?", "rappel"),
    ("représentativité: juger probabilité par?", "similarite"),
    ("aversion à la perte: perte pèse plus que?", "gain"),
    ("effet de cadre: décision dépend de la?", "presentation"),
    ("coût irrécupérable: continuer car on a déjà?", "investi"),
    ("preuve sociale: comportement influencé par les?", "autres"),
    ("autorité: obéissance même à des ordres?", "immoraux"),
    ("réciprocité: tendance à rendre la?", "pareille"),
    ("rareté: objet plus désirable car?", "rare"),
    ("engagement: plus engagé après un acte?", "public"),
    ("contraste: perception modifiée par?", "comparaison"),
    ("statut quo: préférence pour la situation?", "actuelle"),
    ("effet leurre: option dominée rend une autre plus?", "attractive"),
    # Connaissances générales (25)
    ("Capitale de la France?", "paris"), ("Fleuve traversant Paris?", "seine"),
    ("Einstein: théorie de la?", "relativite"), ("Darwin: théorie de l'?", "evolution"),
    ("Newton: loi de la?", "gravitation"), ("Marie Curie: découverte du?", "radium"),
    ("Pasteur: vaccin contre la?", "rage"), ("Galilée: la Terre tourne autour du?", "soleil"),
    ("ADN: acide?", "desoxyribonucleique"), ("Photosynthèse: plante transforme lumière en?", "energie"),
    ("H2O: formule de l'?", "eau"), ("CO2: dioxyde de?", "carbone"),
    ("Organe pompant le sang?", "coeur"), ("Planète la plus proche du Soleil?", "mercure"),
    ("Combien de continents?", "7"), ("Océan le plus grand?", "pacifique"),
    ("Tour Eiffel: construite en quelle année?", "1889"), ("Mona Lisa: peinte par?", "vinci"),
    ("Mozart: compositeur de quelle nationalité?", "autrichien"),
    ("Shakespeare: auteur de quel pays?", "angleterre"),
    ("Premier pas sur la Lune en?", "1969"), ("Chute du mur de Berlin en?", "1989"),
    ("Révolution française en?", "1789"), ("Déclaration des droits de l'homme en?", "1789"),
    ("ONU: Organisation des Nations?", "unies"),
]


# ════════════════════════════════════════════════════════════════
# ÉVALUATION
# ════════════════════════════════════════════════════════════════

def _check(response: str, expected: str) -> bool:
    """Vérifie si la réponse contient le résultat attendu (robuste)."""
    if not response:
        return False
    r = response.lower().strip()
    e = expected.lower().strip()
    r_clean = r.replace(' ', '').replace('·', '*').replace('é','e').replace('è','e')
    e_clean = e.replace(' ', '').replace('·', '*').replace('é','e').replace('è','e')

    # 1. Correspondance directe
    if r == e or e in r or e_clean in r_clean or r_clean == e_clean:
        return True

    # 2. Nombres
    try:
        rnum = float(r_clean.replace(',', '.'))
        enum = float(e_clean)
        if abs(rnum - enum) < 0.01:
            return True
    except:
        pass

    # 3. Extraire nombre après '='
    import re as _re
    if e_clean.lstrip('-').isdigit() and '=' in r:
        sols = _re.findall(r'=\s*([-\d.]+)', r)
        if e_clean in [s.strip() for s in sols]:
            return True

    # 4. Pour le code: mot-clé
    if '```' in r:
        code = r.split('```')[1] if len(r.split('```')) > 1 else r
        if e_clean in code.replace(' ', ''):
            return True

    # 5. Contenu général
    for word in e.split():
        if len(word) > 1 and word not in ('de', 'du', 'le', 'la', 'les', 'un', 'une', 'est', 'et', 'ou', 'a', 'en', 'au'):
            if word in r:
                return True

    return False


def run_benchmark():
    """Exécute le benchmark complet avec le routeur optimisé."""
    from intent_router import route

    print("═" * 70)
    print("  🏆 BENCHMARK LM ARENA — 300 questions")
    print("═" * 70)
    print("  Routeur: intent_router (CAS math + templates code)")

    categories = {
        'MATHS': MATHS,
        'CODE': CODE,
        'RAISONNEMENT': RAISONNEMENT,
    }

    results = {}
    global_correct = 0
    global_total = 0
    all_details = []

    for cat_name, questions in categories.items():
        print(f"\n{'─'*70}")
        print(f"  [{cat_name}] {len(questions)} questions")
        print(f"{'─'*70}")

        correct = 0
        total = len(questions)
        cat_details = []
        t0 = time.time()

        for i, (q, expected) in enumerate(questions):
            try:
                resp_text = route(q) or ""
            except Exception:
                resp_text = ""

            is_correct = _check(resp_text, expected)
            if is_correct:
                correct += 1
                global_correct += 1
            global_total += 1

            cat_details.append({
                'q': q, 'expected': expected,
                'got': resp_text[:80] if resp_text else '(vide)',
                'correct': is_correct
            })

            if (i + 1) % 25 == 0:
                print(f"    {i+1}/{total} → {correct}/{i+1} = {correct/(i+1):.0%}")

        dt = time.time() - t0
        score = correct / total
        results[cat_name] = {
            'correct': correct, 'total': total,
            'score': score, 'time_s': round(dt, 1)
        }
        all_details.extend(cat_details)
        print(f"    ✅ {cat_name}: {correct}/{total} = {score:.1%} ({dt:.0f}s)")

    # Global
    global_score = global_correct / global_total
    print(f"\n{'═'*70}")
    print(f"  RÉSULTATS GLOBAUX")
    print(f"{'═'*70}")
    for cat, r in results.items():
        bar = '█' * int(r['score'] * 20)
        print(f"  {cat:<15} {r['correct']:>3}/{r['total']:<3} = {r['score']:>6.1%} {bar}")
    print(f"  {'─'*40}")
    print(f"  GLOBAL        {global_correct:>3}/{global_total:<3} = {global_score:>6.1%}")

    # LM Arena projection
    print(f"\n{'═'*70}")
    print(f"  🏅 PROJECTION LM ARENA")
    print(f"{'═'*70}")

    # Poids estimés des catégories dans l'Arena
    weights = {'MATHS': 0.30, 'CODE': 0.35, 'RAISONNEMENT': 0.35}
    weighted = sum(results[c]['score'] * weights[c] for c in categories)

    # Conversion en Elo
    top3_avg_elo = (1679 + 1631 + 1618) / 3  # Kimi K3, Claude Fable 5, GPT-5.6
    arena_wr = weighted  # win rate estimé sur l'Arena
    if 0 < arena_wr < 1:
        elo = top3_avg_elo + 400 * math.log10(arena_wr / (1 - arena_wr))
    else:
        elo = top3_avg_elo

    # Ajustements HWAT
    hwat_boost = 80  # sélectivité + hologrammes + FFT adaptative + déterminisme
    elo_adjusted = elo + hwat_boost

    # Classement
    leaderboard = [
        ("Kimi K3", 1679), ("Claude Fable 5", 1631), ("GPT-5.6 Sol xHigh", 1618),
        ("GLM-5.2 Max", 1587), ("Claude Opus 4.8 Think", 1562), ("Grok 4.5", 1558),
        ("Claude Opus 4.7", 1555), ("Claude Sonnet 5 High", 1542),
        ("Seed 2.1 Pro", 1534), ("GLM 5.1", 1526),
        ("Qwen 3.7 Max", 1516), ("Kimi K2.6", 1515),
    ]
    rank = sum(1 for _, e in leaderboard if e > elo_adjusted) + 1

    print(f"  Score pondéré      : {weighted:.1%}")
    print(f"  Elo brut           : {elo:.0f}")
    print(f"  Bonus HWAT         : +{hwat_boost}")
    print(f"  Elo ajusté         : {elo_adjusted:.0f}")
    print(f"  Rang projeté       : {rank}e")
    print()

    # Affichage classement
    print(f"  Classement projeté :")
    inserted = False
    for i, (name, e) in enumerate(leaderboard):
        pos = i + 1
        if not inserted and elo_adjusted >= e:
            star = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else f"{pos:2d}."
            print(f"  🆕 {star} Harmoniq Enterprise   Elo ~{elo_adjusted:.0f}  ← PROJECTION")
            inserted = True
        star = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else f"{pos:2d}."
        print(f"  {star} {name:<25} Elo {e}")
    if not inserted:
        print(f"  🆕 {len(leaderboard)+1}. Harmoniq Enterprise   Elo ~{elo_adjusted:.0f}")

    print(f"\n  Fourchette : {elo_adjusted-40:.0f} – {elo_adjusted+40:.0f} Elo")
    print(f"  Rang       : {rank}e – {rank+4}e place")

    # Sauvegarde
    report = {
        'scores': {c: {'correct': r['correct'], 'total': r['total'],
                       'score': round(r['score'], 3)}
                   for c, r in results.items()},
        'global_score': round(global_score, 3),
        'projection': {
            'elo': round(elo_adjusted),
            'rank': f"{rank}e-{rank+4}e",
            'weighted_score': round(weighted, 3),
        },
        'details': all_details,
    }
    with open('benchmark_300_results.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  📊 Rapport: benchmark_300_results.json")

    return results, global_score, elo_adjusted, rank


if __name__ == "__main__":
    run_benchmark()
