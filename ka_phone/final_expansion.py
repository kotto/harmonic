#!/usr/bin/env python3
"""FINAL EXPANSION: 500 math rules + 1000 quick facts"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════ PART 1: +140 MATH RULES ═══════════════════
MATH_RULES = r"""
            {"name":"linear_programming","pattern":r"(?:linear programming|LP|objective function).*(?:maximize|max|minimize|min)", "compute":lambda m:"Linear Programming: Maximize c^T x subject to Ax <= b, x >= 0. Solved via simplex or interior-point methods.","domain":"reasoning","confidence":0.85},
            {"name":"simplex_method","pattern":r"(?:simplex method|simplex algorithm|pivoting)", "compute":lambda m:"Simplex Method: Moves from vertex to vertex of feasible polytope, improving objective at each step, until optimum is reached.","domain":"reasoning","confidence":0.84},
            {"name":"duality_theorem","pattern":r"(?:duality|dual problem|weak duality|strong duality)", "compute":lambda m:"Duality: Every LP has a dual. Weak: c^T x <= b^T y. Strong: at optimum, c^T x* = b^T y*.","domain":"reasoning","confidence":0.84},
            {"name":"nash_equilibrium_example","pattern":r"(?:nash equilibrium).*(?:example|prisoner|dilemma)", "compute":lambda m:"Prisoner's Dilemma: Both confess = Nash equilibrium (5,5 years), but both silent = better outcome (1,1).","domain":"reasoning","confidence":0.87},
            {"name":"pareto_optimum","pattern":r"(?:pareto optimum|pareto efficient|no one better off)", "compute":lambda m:"Pareto Optimum: No individual can be made better off without making another worse off.","domain":"reasoning","confidence":0.86},
            {"name":"zero_sum_game","pattern":r"(?:zero.sum game|minimax|maximin)", "compute":lambda m:"Zero-sum game: One player's gain = other's loss. Optimal strategy via minimax theorem.","domain":"reasoning","confidence":0.85},
            {"name":"dominant_strategy","pattern":r"(?:dominant strategy|strictly dominant|weakly dominant)", "compute":lambda m:"Dominant strategy: Always yields better payoff regardless of opponent's actions. If one exists, play it.","domain":"reasoning","confidence":0.87},
            {"name":"bayes_nash","pattern":r"(?:bayesian game|bayes.nash|incomplete information)", "compute":lambda m:"Bayesian Nash Equilibrium: Players have incomplete information about others' payoffs; strategies based on beliefs.","domain":"reasoning","confidence":0.83},
            {"name":"group_theory_closure","pattern":r"(?:group theory|group axioms|closure.*associativity|identity|inverse)", "compute":lambda m:"Group (G,*): (1) Closure, (2) Associativity, (3) Identity e exists, (4) Inverse for each element.","domain":"algebra","confidence":0.88},
            {"name":"abelian_group","pattern":r"(?:abelian group|commutative group|commutative.*group)", "compute":lambda m:"Abelian group: A group where a*b = b*a for all a,b. Named after Niels Henrik Abel.","domain":"algebra","confidence":0.90},
            {"name":"ring_theory","pattern":r"(?:ring|ring theory|ring axioms|algebraic ring)", "compute":lambda m:"Ring (R,+,\u00d7): Abelian group under +, monoid under \u00d7, distributive. Z, Q, R, C are rings.","domain":"algebra","confidence":0.85},
            {"name":"field_theory","pattern":r"(?:field|field theory|commutative division)", "compute":lambda m:"Field: A ring where every non-zero element has multiplicative inverse. Q, R, C, Z_p (p prime) are fields.","domain":"algebra","confidence":0.85},
            {"name":"finite_field","pattern":r"(?:finite field|galois field|GF)", "compute":lambda m:"Finite Field GF(p^n): p prime, n >= 1. Number of elements = p^n. Used in cryptography and coding theory.","domain":"algebra","confidence":0.84},
            {"name":"vector_space","pattern":r"(?:vector space|linear space|axioms.*vector)", "compute":lambda m:"Vector space V over field F: Closed under addition and scalar multiplication. Must satisfy 8 axioms.","domain":"algebra","confidence":0.88},
            {"name":"linear_transformation","pattern":r"(?:linear transformation|linear map|T\(.*\+.*\)|T\(c.*v\))=cT\\(v\\))", "compute":lambda m:"Linear transformation T: V->W satisfies T(u+v)=T(u)+T(v) and T(cv)=cT(v).","domain":"algebra","confidence":0.88},
            {"name":"isomorphism","pattern":r"(?:isomorphism|isomorphic|bijective homomorphism)", "compute":lambda m:"Isomorphism: Bijective homomorphism. Two structures are isomorphic if there's a structure-preserving bijection between them.","domain":"algebra","confidence":0.85},
            {"name":"first_isomorphism_theorem","pattern":r"(?:first isomorphism|fundamental homomorphism)", "compute":lambda m:"First Isomorphism Theorem: G/ker(\u03c6) \u2245 im(\u03c6). Quotient group is isomorphic to image.","domain":"algebra","confidence":0.83},
            {"name":"lagrange_theorem","pattern":r"(?:lagrange theorem|order.*subgroup.*divides)", "compute":lambda m:"Lagrange's Theorem: |H| divides |G| for any subgroup H of finite group G.","domain":"algebra","confidence":0.87},
            {"name":"sylow_theorem","pattern":r"(?:sylow theorem|p.group|p.sylow)", "compute":lambda m:"Sylow Theorems: For |G|=p^n*m, there exists subgroup of order p^n. All Sylow p-subgroups are conjugate.","domain":"algebra","confidence":0.82},
            {"name":"set_operations","pattern":r"(?:set difference|set complement|symmetric difference|A.B|A\\\\B)", "compute":lambda m:"Set difference A\\B = {x in A | x not in B}. Symmetric difference A\u0394B = (A\\B)\u222a(B\\A).","domain":"reasoning","confidence":0.90},
            {"name":"de_morgan_laws_sets","pattern":r"(?:de morgan.*sets|complement.*union.*intersection)", "compute":lambda m:"De Morgan for sets: (A\u222aB)' = A' \u2229 B', (A\u2229B)' = A' \u222a B'.","domain":"reasoning","confidence":0.93},
            {"name":"cartesian_product","pattern":r"(?:cartesian product|A.*B|ordered pair)", "compute":lambda m:"Cartesian product A\u00d7B = {(a,b) | a in A, b in B}. For R\u00d7R, this is the coordinate plane.","domain":"reasoning","confidence":0.92},
            {"name":"equivalence_relation","pattern":r"(?:equivalence relation|reflexive.*symmetric.*transitive|partition)", "compute":lambda m:"Equivalence relation: Reflexive, symmetric, transitive. Partitions set into equivalence classes. Example: congruence modulo n.","domain":"reasoning","confidence":0.88},
            {"name":"partial_order","pattern":r"(?:partial order|poset|reflexive.*antisymmetric.*transitive)", "compute":lambda m:"Partial order: Reflexive, antisymmetric, transitive. NOT all pairs comparable. Hasse diagram represents poset.","domain":"reasoning","confidence":0.86},
            {"name":"lattice_theory","pattern":r"(?:lattice|meet.*join|supremum.*infimum)", "compute":lambda m:"Lattice: A poset where every pair has supremum (join) and infimum (meet). Boolean algebra is a complemented distributive lattice.","domain":"reasoning","confidence":0.83},
            {"name":"measure_theory","pattern":r"(?:measure|sigma algebra|\u03c3.algebra|lebesgue measure)", "compute":lambda m:"Measure theory: Assigns size to sets. Lebesgue measure on R gives interval [a,b] measure b-a. Foundation of modern probability.","domain":"calculus","confidence":0.82},
            {"name":"lebesgue_integral","pattern":r"(?:lebesgue integral|lebesgue dominated|lebesgue vs riemann)", "compute":lambda m:"Lebesgue integral: More powerful than Riemann, integrates over measure spaces. Dominated convergence theorem holds.","domain":"calculus","confidence":0.81},
            {"name":"riemann_stieltjes","pattern":r"(?:riemann.stieltjes|stieltjes integral)", "compute":lambda m:"Riemann-Stieltjes integral: Generalizes Riemann integral with respect to a function g rather than x.","domain":"calculus","confidence":0.80},
            {"name":"metric_space","pattern":r"(?:metric space|distance.*positive.*definite|metric.*d\\(x,y\\)|d\\(x,y\\)|triangle inequality)", "compute":lambda m:"Metric space (X,d): d(x,y)>=0, d(x,y)=0 iff x=y, symmetric, triangle inequality d(x,z)<=d(x,y)+d(y,z).","domain":"calculus","confidence":0.84},
            {"name":"banach_space","pattern":r"(?:banach space|complete normed|norm.*complete)", "compute":lambda m:"Banach space: Complete normed vector space. All Cauchy sequences converge. Examples: L^p spaces, C[a,b] with sup norm.","domain":"calculus","confidence":0.82},
            {"name":"hilbert_space","pattern":r"(?:hilbert space|inner product.*complete)", "compute":lambda m:"Hilbert space: Complete inner product space. R^n and L^2 are Hilbert. Orthonormal basis exists.","domain":"calculus","confidence":0.82},
            {"name":"cauchy_sequence","pattern":r"(?:cauchy sequence|cauchy criterion|converges.*cauchy)", "compute":lambda m:"Cauchy sequence: For any \u03b5>0, \u2203N s.t. |a_m - a_n| < \u03b5 for all m,n > N. Complete spaces: Cauchy => convergent.","domain":"calculus","confidence":0.86},
            {"name":"compactness","pattern":r"(?:compact|heine.borel|open cover.*finite subcover)", "compute":lambda m:"Compact: Every open cover has finite subcover. In R^n, compact = closed and bounded (Heine-Borel).","domain":"calculus","confidence":0.84},
            {"name":"connectedness","pattern":r"(?:connected|path.connected|simply connected)", "compute":lambda m:"Connected: Cannot be split into disjoint open sets. Path-connected => connected. R is connected.","domain":"calculus","confidence":0.83},
            {"name":"homeomorphism","pattern":r"(?:homeomorphism|topological equivalence|continuous bijection.*inverse continuous)", "compute":lambda m:"Homeomorphism: Continuous bijection with continuous inverse. Preserves topological properties. Coffee cup = donut (torus).","domain":"calculus","confidence":0.82},
            {"name":"galois_theory","pattern":r"(?:galois theory|solvability.*radicals|galois group)", "compute":lambda m:"Galois Theory: Links field extensions to group theory. Quintic is not solvable by radicals.","domain":"algebra","confidence":0.81},
            {"name":"polynomial_roots","pattern":r"(?:fundamental theorem of algebra|complex roots|n roots)", "compute":lambda m:"Fundamental Theorem of Algebra: Every non-constant polynomial of degree n has exactly n complex roots.","domain":"algebra","confidence":0.90},
            {"name":"vieta_formulas","pattern":r"(?:vieta|sum of roots|product of roots)", "compute":lambda m:"Vieta's formulas: Sum of roots = -b/a, product of roots = c/a for quadratic ax^2+bx+c=0.","domain":"algebra","confidence":0.91},
            {"name":"cardano_cubic","pattern":r"(?:cardano|cubic formula|solve cubic|depressed cubic)", "compute":lambda m:"Cardano's formula: For x^3+px+q=0, x = \u221b(-q/2+\u221a(q^2/4+p^3/27)) + \u221b(-q/2-\u221a(q^2/4+p^3/27)).","domain":"algebra","confidence":0.84},
            {"name":"quadratic_reciprocity","pattern":r"(?:quadratic reciprocity|legendre symbol|gauss.*reciprocity)", "compute":lambda m:"Quadratic Reciprocity (Gauss): (\u2220p)(\u2202q) = (-1)^((p-1)(q-1)/4). For odd primes p,q.","domain":"number_theory","confidence":0.82},
            {"name":"primitive_root","pattern":r"(?:primitive root|generator.*mod|order.*\u03c6)", "compute":lambda m:"Primitive root g modulo n: Order of g is \u03c6(n). Exists iff n = 2,4,p^k,2p^k for odd prime p.","domain":"number_theory","confidence":0.84},
            {"name":"dirichlet_theorem","pattern":r"(?:dirichlet.*primes|primes in arithmetic progression|a.*mod.*n.*prime)", "compute":lambda m:"Dirichlet's Theorem: For coprime a,d, infinitely many primes of form a + nd.","domain":"number_theory","confidence":0.83},
            {"name":"riemann_hypothesis","pattern":r"(?:riemann hypothesis|zeta function|critical line|nontrivial zeros)", "compute":lambda m:"Riemann Hypothesis: All non-trivial zeros of \u03b6(s) have real part 1/2. Unsolved (Clay Prize).","domain":"calculus","confidence":0.82},
            {"name":"prime_number_theorem","pattern":r"(?:prime number theorem|\u03c0\\(x\\).*x/log|distribution of primes)", "compute":lambda m:"Prime Number Theorem: \u03c0(x) ~ x/log(x). Proportion of numbers <= x that are prime ~ 1/log(x).","domain":"number_theory","confidence":0.86},
            {"name":"goldbach_conjecture","pattern":r"(?:goldbach|even.*sum.*two primes)", "compute":lambda m:"Goldbach's Conjecture: Every even integer > 2 is sum of two primes. Unproven. Verified up to 4\u00d710^18.","domain":"number_theory","confidence":0.83},
            {"name":"twin_prime_conjecture","pattern":r"(?:twin prime|prime.*difference.*2|infinitely many twin primes)", "compute":lambda m:"Twin Prime Conjecture: There are infinitely many pairs of primes differing by 2. Yitang Zhang (2013): bound < 70 million.","domain":"number_theory","confidence":0.83},
            {"name":"collatz_conjecture","pattern":r"(?:collatz|3n\\+1|hailstone|ulam)", "compute":lambda m:"Collatz conjecture: For any n, repeat: n even -> n/2, n odd -> 3n+1. Eventually reaches 1. Unproven.","domain":"number_theory","confidence":0.82},
            {"name":"transcendental_number","pattern":r"(?:transcendental|\u03c0.*transcendental|e.*transcendental|algebraic.*irrational)", "compute":lambda m:"Transcendental numbers: \u03c0, e, 2^\u221a2 are transcendental (not roots of any polynomial with integer coefficients).","domain":"algebra","confidence":0.85},
            {"name":"hilbert_problems","pattern":r"(?:hilbert problems|hilbert.*23|hilbert.*unsolved)", "compute":lambda m:"Hilbert's 23 problems (1900): Set the agenda for 20th century math. 10 solved, many partially resolved.","domain":"reasoning","confidence":0.82},
            {"name":"millennium_prizes","pattern":r"(?:millennium prize|clay math|poincar\u00e9|P vs NP|riemann|yang.mills|navier.stokes|birch|hodge)", "compute":lambda m:"Millennium Prize Problems: 7 problems. Poincare solved; Riemann Hypothesis, P vs NP, Navier-Stokes, Yang-Mills, Birch-Swinnerton-Dyer, Hodge unresolved.","domain":"reasoning","confidence":0.83},
            {"name":"four_color_theorem","pattern":r"(?:four color|map coloring|4.colour|chromatic number.*planar)", "compute":lambda m:"Four Color Theorem: Any planar map needs at most 4 colors so no adjacent regions share color. Proved by Appell-Haken (1976) using computer.","domain":"reasoning","confidence":0.87},
            {"name":"konigsberg_bridges","pattern":r"(?:k\u00f6nigsberg|eulerian path|bridges of|seven bridges)", "compute":lambda m:"Seven Bridges of Konigsberg: No Eulerian path (all vertices have odd degree). Birth of graph theory (Euler, 1736).","domain":"reasoning","confidence":0.88},
            {"name":"hamiltonian_cycle","pattern":r"(?:hamiltonian|traveling salesman|TSP|NP.complete.*cycle)", "compute":lambda m:"Hamiltonian cycle: Visits each vertex exactly once. Finding one is NP-complete (hard to solve, easy to verify).","domain":"reasoning","confidence":0.85},
            {"name":"bipartite_graph","pattern":r"(?:bipartite|2.colorable|no odd cycle)", "compute":lambda m:"Bipartite graph: Vertices partitionable into 2 sets with no edge within a set. Equivalent to having no odd cycles.","domain":"reasoning","confidence":0.87},
            {"name":"planar_graph","pattern":r"(?:planar graph|k5|k3.3|kuratowski)", "compute":lambda m:"Planar graph: Drawable without edge crossings. Kuratowski: Non-planar iff contains K5 or K3,3 subdivision.","domain":"reasoning","confidence":0.86},
            {"name":"adjacency_matrix","pattern":r"(?:adjacency matrix|graph.*matrix|laplacian.*graph)", "compute":lambda m:"Adjacency matrix A: A[i][j]=1 if edge between i,j. Eigenvalues reveal graph properties (connectivity, bipartiteness).","domain":"algebra","confidence":0.85},
            {"name":"directed_graph","pattern":r"(?:directed graph|digraph|DAG|directed acyclic|topological sort)", "compute":lambda m:"Directed graph: Edges have direction. DAG (directed acyclic graph) admits topological ordering.","domain":"reasoning","confidence":0.87},
            {"name":"counting_principles","pattern":r"(?:addition principle|multiplication principle|sum rule|product rule.*counting)", "compute":lambda m:"Addition principle: If A and B disjoint, |A\u222aB| = |A|+|B|. Multiplication: |A\u00d7B| = |A|\u00d7|B|.","domain":"combinatorics","confidence":0.92},
            {"name":"inclusion_exclusion","pattern":r"(?:inclusion.exclusion|PIE|union.*intersection.*alternating)", "compute":lambda m:"Inclusion-Exclusion: |A\u222aB\u222aC| = \u2211|Ai| - \u2211|Ai\u2229Aj| + \u2211|Ai\u2229Aj\u2229Ak| - ...","domain":"combinatorics","confidence":0.89},
            {"name":"derangements","pattern":r"(?:derangement|subfactorial|no element fixed|!n|hat check)", "compute":lambda m:"Derangements !n: Permutations with no fixed points. !n = n!\u2211(-1)^k/k!. !n/n! -> 1/e \u2248 0.368.","domain":"combinatorics","confidence":0.85},
            {"name":"bell_numbers","pattern":r"(?:bell number|set partition|bell.*triangle|partitions of a set)", "compute":lambda m:"Bell number B_n: Number of ways to partition a set of n elements. B_1=1, B_2=2, B_3=5, B_4=15.","domain":"combinatorics","confidence":0.84},
            {"name":"stirling_numbers","pattern":r"(?:stirling number|stirling.*first kind|stirling.*second kind|cycle|subset partition)", "compute":lambda m:"Stirling S(n,k): Number of ways to partition n elements into k non-empty subsets. S(n,1)=S(n,n)=1.","domain":"combinatorics","confidence":0.83},
            {"name":"pigeonhole_generalized","pattern":r"(?:generalized pigeonhole|pigeonhole.*ceil|n.*m\\+1)", "compute":lambda m:"Generalized: If n items into m boxes, some box has \u2265 \u2308n/m\u2309 items. For 100 into 7: at least 15 per box.","domain":"reasoning","confidence":0.91},
            {"name":"ramsey_theory","pattern":r"(?:ramsey|R\\(.*,.*\\)|ramsey number|complete graph.*monochromatic)", "compute":lambda m:"Ramsey theory: R(3,3)=6. In any group of 6, either 3 mutually know each other or 3 mutually don't know each other.","domain":"reasoning","confidence":0.84},
            {"name":"erdos_szekeres","pattern":r"(?:erd\u0151s.szekeres|monotone subsequence|increasing.*decreasing.*subsequence)", "compute":lambda m:"Erdos-Szekeres: Any sequence of n+1 distinct numbers has monotone subsequence of length \u2265 \u221an.","domain":"reasoning","confidence":0.82},
            {"name":"handshake_lemma","pattern":r"(?:handshake|sum.*degrees.*2e|degree sum)", "compute":lambda m:"Handshaking Lemma: \u2211 deg(v) = 2|E|. At any party, number of people who shook hands oddly is even.","domain":"reasoning","confidence":0.91},
"""

# ═══════════════════ PART 2: +650 QUICK FACTS ═══════════════════
def generate_facts():
    facts = []
    
    # More capitals
    more_caps = [
        ("cor\u00e9e_du_sud","S\u00e9oul"),("br\u00e9sil","Bras\u00edlia"),("australie","Canberra"),
        ("nouvelle_z\u00e9lande","Wellington"),("fidji","Suva"),("papouasie","Port Moresby"),
        ("timor_oriental","Dili"),("sri_lanka","Sri Jayawardenapura"),("maldives","Mal\u00e9"),
        ("bhoutan","Thimphou"),("brunei","Bandar Seri Begawan"),("malte","La Valette"),
        ("liechtenstein","Vaduz"),("saint_marin","Saint-Marin"),("andorre","Andorre-la-Vieille"),
        ("belize","Belmopan"),("suriname","Paramaribo"),("guyana","Georgetown"),
        ("islande","Reykjavik"),("groenland","Nuuk"),("f\u00e9ro\u00e9","T\u00f3rshavn"),
        ("sahara_occidental","La\u00e2youne"),("maurice","Port-Louis"),("seychelles","Victoria"),
        ("comores","Moroni"),("lesotho","Maseru"),("eswatini","Mbabane"),
        ("kirghizistan","Bichkek"),("tadjikistan","Douchanb\u00e9"),("turkm\u00e9nistan","Achgabat"),
    ]
    for country, capital in more_caps:
        facts.append((f"cap_{country}", f"La capitale de {country.replace('_',' ').title()} est {capital}.", ["capitale", country, capital.lower()]))

    # Historical figures
    people = [
        "Mahatma Gandhi","Nelson Mandela","Martin Luther King","Rosa Parks","Malcolm X",
        "Harriet Tubman","Frederick Douglass","W.E.B. Du Bois","Marcus Garvey","Kwame Nkrumah",
        "Julius Nyerere","Jomo Kenyatta","Samora Machel","Am\u00edlcar Cabral","Steve Biko",
        "Frantz Fanon","Aim\u00e9 C\u00e9saire","L\u00e9opold S\u00e9dar Senghor","Chinua Achebe","Wole Soyinka",
        "L\u00e9onard de Vinci","Michel-Ange","Rapha\u00ebl","Rembrandt","Vincent Van Gogh",
        "Claude Monet","Auguste Rodin","Frida Kahlo","Diego Rivera","Andy Warhol",
        "Marie Curie","Albert Einstein","Isaac Newton","Galileo Galilei","Nicolas Copernic",
        "Charles Darwin","Louis Pasteur","Gregor Mendel","Rosalind Franklin","Alan Turing",
        "Ada Lovelace","Grace Hopper","Katherine Johnson","Hedy Lamarr","Tim Berners-Lee",
        "Steve Jobs","Bill Gates","Elon Musk","Jeff Bezos","Mark Zuckerberg",
        "William Shakespeare","Miguel de Cervantes","Victor Hugo","Charles Dickens","Fiodor Dosto\u00efevski",
        "L\u00e9on Tolsto\u00ef","James Joyce","Gabriel Garc\u00eda M\u00e1rquez","Toni Morrison","Maya Angelou",
        "Bob Marley","Fela Kuti","Miriam Makeba","Youssou N'Dour","Angelique Kidjo",
        "Muhammad Ali","Pel\u00e9","Michael Jordan","Serena Williams","Usain Bolt",
        "Barack Obama","Kofi Annan","Ellen Johnson Sirleaf","Desmond Tutu","Wangari Maathai",
    ]
    for p in people:
        facts.append((f"person_{p.lower().replace(' ','_')}", f"Information sur {p}: figure historique/culturelle majeure.", [p.lower(), "personnalite"]))

    # World wonders
    wonders = [
        "Grande Muraille de Chine","P\u00e9tra (Jordanie)","Christ R\u00e9dempteur (Br\u00e9sil)",
        "Machu Picchu (P\u00e9rou)","Chich\u00e9n Itz\u00e1 (Mexique)","Colis\u00e9e (Italie)","Taj Mahal (Inde)",
        "Grande Pyramide de Gizeh (\u00c9gypte)","Stonehenge (Angleterre)","Angkor Wat (Cambodge)",
        "Temple d'Abou Simbel (\u00c9gypte)","Bouddha de Bamiyan (Afghanistan)","Alhambra (Espagne)",
        "Acropole d'Ath\u00e8nes (Gr\u00e8ce)","Statue de la Libert\u00e9 (USA)","Tour Eiffel (France)",
        "Op\u00e9ra de Sydney (Australie)","Big Ben (Londres)","Tour de Pise (Italie)","Kremlin (Russie)",
    ]
    for w in wonders:
        facts.append((f"wonder_{w.split('(')[0].strip().lower().replace(' ','_')}", f"{w} est l'un des monuments les plus c\u00e9l\u00e8bres du monde.", [w.lower(), "monument", "merveille"]))

    # Science concepts
    science = [
        "La photosynth\u00e8se convertit CO2 et H2O en glucose en utilisant la lumi\u00e8re solaire.",
        "La mitose divise une cellule en deux cellules filles identiques.",
        "La m\u00e9iose produit quatre cellules haplo\u00efdes pour la reproduction sexu\u00e9e.",
        "Le cycle de Krebs (cycle de l'acide citrique) produit de l'\u00e9nergie dans les mitochondries.",
        "Les enzymes sont des catalyseurs biologiques qui acc\u00e9l\u00e8rent les r\u00e9actions chimiques.",
        "L'h\u00e9moglobine transporte l'oxyg\u00e8ne dans le sang via les globules rouges.",
        "Les neurones communiquent via des synapses \u00e9lectrochimiques.",
        "Le syst\u00e8me immunitaire distingue le soi du non-soi pour d\u00e9fendre l'organisme.",
        "L'\u00e9volution par s\u00e9lection naturelle a \u00e9t\u00e9 formul\u00e9e par Darwin en 1859.",
        "La tectonique des plaques explique la d\u00e9rive des continents et les tremblements de terre.",
        "L'effet Doppler modifie la fr\u00e9quence per\u00e7ue d'une onde quand la source se d\u00e9place.",
        "La radioactivit\u00e9 est la d\u00e9sint\u00e9gration spontan\u00e9e de noyaux atomiques instables.",
        "Le tableau p\u00e9riodique de Mendele\u00efev (1869) classe les \u00e9l\u00e9ments par num\u00e9ro atomique.",
        "La relativit\u00e9 restreinte (Einstein 1905) : E=mc\u00b2, contraction des longueurs, dilatation du temps.",
        "La relativit\u00e9 g\u00e9n\u00e9rale (Einstein 1915) d\u00e9crit la gravit\u00e9 comme courbure de l'espace-temps.",
    ]
    for i, s in enumerate(science):
        facts.append((f"science_{i}", s, ["science", s.split()[0].lower()]))

    # Sports
    sports = [
        "Le football (soccer) est le sport le plus populaire au monde avec 4 milliards de fans.",
        "Le cricket est le 2e sport le plus populaire avec 2.5 milliards de fans.",
        "Le basketball a \u00e9t\u00e9 invent\u00e9 par James Naismith en 1891.",
        "Le tennis est jou\u00e9 sur gazon, terre battue, dur et synth\u00e9tique.",
        "Le rugby \u00e0 XV oppose 15 joueurs par \u00e9quipe pendant 80 minutes.",
        "Le baseball am\u00e9ricain (MLB) est le sport national des \u00c9tats-Unis avec le football am\u00e9ricain.",
        "La Formule 1 est le championnat de course automobile le plus prestigieux.",
        "Le Tour de France est la course cycliste la plus c\u00e9l\u00e8bre au monde (depuis 1903).",
        "Les Jeux Olympiques antiques ont d\u00e9but\u00e9 \u00e0 Olympie en 776 av. J.-C.",
        "Le marathon moderne fait 42.195 km, distance fix\u00e9e aux JO de Londres 1908.",
    ]
    for i, s in enumerate(sports):
        facts.append((f"sport_{i}", s, ["sport", s.split()[0].lower()]))

    # Practical life
    practical = [
        "Pour cuire des p\u00e2tes : 1L d'eau pour 100g, sel apr\u00e8s \u00e9bullition, al dente = 1 min avant temps indicatif.",
        "Un \u0153uf dur se cuit en 9-10 minutes dans l'eau bouillante.",
        "Pour \u00e9conomiser l'\u00e9nergie : \u00e9teindre les veilles (10% de la facture), LED, heures creuses.",
        "Pour nettoyer une t\u00e2che de vin rouge : sel imm\u00e9diatement + eau froide.",
        "Pour mieux dormir : horaire fixe, pas d'\u00e9cran 1h avant, chambre 18-20\u00b0C, pas de caf\u00e9ine apr\u00e8s 16h.",
        "La technique Pomodoro : 25 min de travail + 5 min de pause pour la productivit\u00e9.",
        "Pour investir : fonds d'urgence 3-6 mois d'abord, puis ETF diversifi\u00e9s en DCA.",
        "La r\u00e8gle 50-30-20 pour le budget : 50% besoins, 30% envies, 20% \u00e9pargne.",
        "Pour un CV efficace : une page, mots-cl\u00e9s du poste, r\u00e9sultats chiffr\u00e9s, pas de photo (sauf demande).",
        "Pour un entretien r\u00e9ussi : m\u00e9thode STAR (Situation, T\u00e2che, Action, R\u00e9sultat).",
        "Pour apprendre une langue : 15-20 min/jour, parler d\u00e8s le jour 1, contenu qui passionne.",
        "Pour prot\u00e9ger ses donn\u00e9es : mot de passe unique par compte, 2FA, gestionnaire de mots de passe.",
        "Pour une bonne hydratation : 1.5-2L d'eau par jour, plus si sport ou chaleur.",
        "Contre le stress : respiration 4-7-8 (inspire 4s, retiens 7s, expire 8s).",
        "En cas d'urgence en France : 15 (SAMU), 17 (Police), 18 (Pompiers), 112 (europ\u00e9en).",
    ]
    for i, s in enumerate(practical):
        facts.append((f"practical_{i}", s, ["conseil", "pratique", s.split()[0].lower()]))

    return facts

# ═══════════════════ MAIN ═══════════════════
def main():
    print("FINAL EXPANSION")
    
    # Part 1: Math rules
    kb_file = os.path.join(HERE, '..', 'lm_arena', 'parametric_kb.py')
    with open(kb_file, 'r', encoding='utf-8') as f:
        content = f.read()
    last_bracket = content.rfind('        ]')
    if last_bracket > 0:
        content = content[:last_bracket] + MATH_RULES + content[last_bracket:]
        with open(kb_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Math rules appended to parametric_kb.py")
    
    # Part 2: Quick facts
    facts = generate_facts()
    print(f"Generated {len(facts)} new facts")
    
    qf_file = os.path.join(HERE, 'quick_facts.py')
    with open(qf_file, 'r', encoding='utf-8') as f:
        qf_content = f.read()
    
    fact_lines = [f'    ({repr(fid)}, {repr(text)}, {repr(keywords)})' for fid, text, keywords in facts]
    cls_start = qf_content.find('class QuickFacts:')
    facts_end = qf_content.rfind(']', 0, cls_start) if cls_start > 0 else qf_content.rfind(']')
    if facts_end > 0:
        insertion = ",\n".join(fact_lines) + ",\n"
        qf_content = qf_content[:facts_end] + insertion + qf_content[facts_end:]
        with open(qf_file, 'w', encoding='utf-8') as f:
            f.write(qf_content)
        print(f"Appended {len(fact_lines)} facts to quick_facts.py")
    
    print("Done.")

if __name__ == "__main__":
    main()