#!/usr/bin/env python3
"""BATCH 3: 428->500 math rules, 550->1000 quick facts"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

MATH_RULES = r"""
            {"name":"factorial_growth","pattern":r"(?:factorial growth|n!.*exponential|stirling)", "compute":lambda m:"n! grows faster than a^n for any fixed a, but slower than n^n. log(n!) = n log n - n + O(log n).","domain":"calculus","confidence":0.87},
            {"name":"lhopital_example","pattern":r"(?:l.hopital|l.hospital).*(?:example|limit.*0/0)", "compute":lambda m:"Example: lim(x->0) sin(x)/x = lim cos(x)/1 = 1. Also: lim(x->inf) x/e^x = lim 1/e^x = 0.","domain":"calculus","confidence":0.89},
            {"name":"sandwich_theorem","pattern":r"(?:sandwich|squeeze|pinching).*(?:theorem|limit)", "compute":lambda m:"Squeeze Theorem: If g(x) <= f(x) <= h(x) and lim g = lim h = L, then lim f = L. Used for sin(x)/x.","domain":"calculus","confidence":0.87},
            {"name":"monotone_convergence","pattern":r"(?:monotone convergence|bounded.*monotone|increasing.*bounded)", "compute":lambda m:"Monotone Convergence Theorem: Bounded monotone sequences converge. If increasing & bounded above -> converges to supremum.","domain":"calculus","confidence":0.88},
            {"name":"dominated_convergence","pattern":r"(?:dominated convergence|lebesgue.*DCT)", "compute":lambda m:"Dominated Convergence Theorem: If |f_n| <= g and g integrable, then lim integral f_n = integral lim f_n (Lebesgue).","domain":"calculus","confidence":0.82},
            {"name":"fatou_lemma","pattern":r"(?:fatou lemma|liminf.*integral|integral.*liminf)", "compute":lambda m:"Fatou's Lemma: integral(liminf f_n) <= liminf(integral f_n). Used with DCT and MCT.","domain":"calculus","confidence":0.81},
            {"name":"fubini_theorem","pattern":r"(?:fubini|iterated.*integral.*order|change order.*integration)", "compute":lambda m:"Fubini's Theorem: Double integral = iterated integral in either order, if integral of absolute value is finite.","domain":"calculus","confidence":0.84},
            {"name":"convolution","pattern":r"(?:convolution|f\*g|convolution integral)", "compute":lambda m:"Convolution: (f*g)(t) = integral f(tau)g(t-tau) dtau. Used in signal processing, probability (sum of independent RVs), and CNN.","domain":"calculus","confidence":0.83},
            {"name":"laplace_transform_table","pattern":r"(?:laplace.*table|L.*1|L.*t|L.*t\\^n|L.*sin|L.*cos)", "compute":lambda m:"Laplace table: L{1}=1/s, L{t}=1/s^2, L{t^n}=n!/s^(n+1), L{sin(at)}=a/(s^2+a^2), L{cos(at)}=s/(s^2+a^2), L{e^(at)}=1/(s-a).","domain":"calculus","confidence":0.86},
            {"name":"inverse_laplace","pattern":r"(?:inverse laplace|partial fraction.*laplace|L\\^-1)", "compute":lambda m:"Inverse Laplace: Use table + partial fractions + convolution. L^{-1}{F(s)G(s)} = f*g (convolution).","domain":"calculus","confidence":0.84},
            {"name":"z_transform","pattern":r"(?:z.transform|discrete.*laplace|difference equation.*z)", "compute":lambda m:"Z-transform: X(z) = sum x[n] z^(-n). Used for discrete-time signals. Analogous to Laplace for continuous.","domain":"calculus","confidence":0.82},
            {"name":"heat_eq_solution","pattern":r"(?:heat equation|diffusion)\s*(?:solution|solve)", "compute":lambda m:"1D heat: u(x,t) = (1/sqrt(4pi*alpha*t)) integral f(y) exp(-(x-y)^2/(4*alpha*t)) dy. Gaussian smoothing.","domain":"calculus","confidence":0.82},
            {"name":"wave_eq_solution","pattern":r"(?:wave equation|d.alembert)\s*(?:solution|solve)", "compute":lambda m:"1D wave: u(x,t) = (f(x-ct) + f(x+ct))/2 + (1/2c)integral_{x-ct}^{x+ct} g(s)ds.","domain":"calculus","confidence":0.82},
            {"name":"central_limit_example","pattern":r"(?:central limit|CLT).*(?:example|coin|dice|normal)", "compute":lambda m:"CLT Example: Sum of 100 dice rolls approx N(350, 291.67). Standardized: z=(sum-350)/sqrt(291.67).","domain":"probability","confidence":0.88},
            {"name":"law_large_numbers","pattern":r"(?:law of large numbers|LLN|sample.*mean.*converges|weak.*law|strong.*law)", "compute":lambda m:"Weak LLN: sample mean -> population mean in probability. Strong LLN: sample mean -> population mean almost surely.","domain":"probability","confidence":0.87},
            {"name":"moment_method","pattern":r"(?:method of moments|moment estimator|MOM)", "compute":lambda m:"Method of Moments: Equate sample moments to theoretical moments. For Normal: mean = xbar, variance = s^2.","domain":"probability","confidence":0.85},
            {"name":"maximum_likelihood","pattern":r"(?:maximum likelihood|MLE|likelihood function|maximize.*likelihood)", "compute":lambda m:"MLE: Choose parameter theta that maximizes P(data|theta). For Normal: mu_MLE = xbar, sigma^2_MLE = (1/n)sum(x_i-xbar)^2.","domain":"probability","confidence":0.86},
            {"name":"fisher_information","pattern":r"(?:fisher information|Cramer.Rao|cram\u00e9r.rao|information matrix)", "compute":lambda m:"Fisher Information I(theta) = -E[d^2/dtheta^2 log L]. Cramer-Rao: Var(estimator) >= 1/I(theta).","domain":"probability","confidence":0.83},
            {"name":"wald_test","pattern":r"(?:wald test|wald statistic|hypothesis.*wald)", "compute":lambda m:"Wald test: W = (theta_hat - theta_0)^2 / Var(theta_hat). Asymptotically chi-squared.","domain":"probability","confidence":0.82},
            {"name":"likelihood_ratio_test","pattern":r"(?:likelihood ratio|LRT|lambda.*likelihood)", "compute":lambda m:"LRT: lambda = 2(log L_alt - log L_null). Under H0, lambda ~ chi-squared. More powerful than Wald in many cases.","domain":"probability","confidence":0.82},
            {"name":"type1_type2_error","pattern":r"(?:type(?:-|\s)1 error|type(?:-|\s)2 error|false positive|false negative|alpha.*beta.*test)", "compute":lambda m:"Type I error (alpha): Reject H0 when true. Type II error (beta): Accept H0 when false. Power = 1-beta.","domain":"probability","confidence":0.88},
            {"name":"p_value","pattern":r"(?:p.value|p value|statistical significance|p<|p <)", "compute":lambda m:"p-value: Probability of observing results as extreme as observed, assuming H0 true. If p < alpha, reject H0.","domain":"probability","confidence":0.87},
            {"name":"bonferroni_correction","pattern":r"(?:bonferroni|multiple comparisons|multiple testing)", "compute":lambda m:"Bonferroni correction: For m tests, use alpha/m significance level. Controls family-wise error rate. Very conservative.","domain":"probability","confidence":0.85},
            {"name":"ols_regression","pattern":r"(?:OLS|ordinary least squares|beta.*hat.*X^T.*X|linear model.*estimate)", "compute":lambda m:"OLS: beta_hat = (X^T X)^(-1) X^T y. Minimizes sum of squared residuals. Unbiased, minimum variance among linear estimators (BLUE).","domain":"probability","confidence":0.86},
            {"name":"r_squared","pattern":r"(?:R.squared|R\\(2\\)|coefficient of determination|goodness of fit.*regression)", "compute":lambda m:"R^2 = 1 - SS_residual/SS_total. Proportion of variance explained by the model. Range [0,1]. Higher = better fit.","domain":"probability","confidence":0.87},
            {"name":"logistic_regression","pattern":r"(?:logistic regression|logit|odds ratio|binary.*outcome)", "compute":lambda m:"Logistic regression: P(Y=1) = 1/(1+e^(-X*beta)). Used for binary outcomes. Odds ratio = exp(beta_i).","domain":"probability","confidence":0.84},
            {"name":"kernel_density","pattern":r"(?:kernel density|KDE|smooth.*histogram|density estimation)", "compute":lambda m:"KDE: f_hat(x) = (1/nh) sum K((x-x_i)/h). Smooths data into continuous density estimate. Bandwidth h controls smoothness.","domain":"probability","confidence":0.83},
            {"name":"bootstrap","pattern":r"(?:bootstrap|resampling|sample.*with.*replacement)", "compute":lambda m:"Bootstrap: Resample with replacement from original data to estimate sampling distribution. Non-parametric, versatile.","domain":"probability","confidence":0.84},
            {"name":"svm_concept","pattern":r"(?:SVM|support vector machine|maximum margin|hyperplane.*separate)", "compute":lambda m:"SVM: Finds optimal hyperplane maximizing margin between classes. Uses kernel trick for non-linear separation (RBF, polynomial).","domain":"algebra","confidence":0.83},
            {"name":"pca","pattern":r"(?:PCA|principal component|dimensionality reduction|eigenvectors.*covariance)", "compute":lambda m:"PCA: Eigenvectors of covariance matrix give principal components. First PC captures maximum variance. Used for dimensionality reduction.","domain":"algebra","confidence":0.84},
            {"name":"singular_value_decomp","pattern":r"(?:SVD|singular value|A=U.*Sigma.*V|matrix decomposition)", "compute":lambda m:"SVD: A = U*Sigma*V^T. U,V orthogonal, Sigma diagonal. Used in PCA, pseudoinverse, low-rank approximation.","domain":"algebra","confidence":0.85},
            {"name":"qr_decomposition","pattern":r"(?:QR decomposition|Gram.Schmidt|orthogonalization)", "compute":lambda m:"QR: A = QR where Q is orthogonal and R is upper triangular. Used for solving linear systems and eigenvalue algorithms.","domain":"algebra","confidence":0.84},
            {"name":"lu_decomposition","pattern":r"(?:LU decomposition|lower.upper|gaussian elimination)", "compute":lambda m:"LU: A = LU where L is lower triangular and U is upper triangular. Used for efficient solving of Ax=b, det(A), inverse.","domain":"algebra","confidence":0.85},
            {"name":"cholesky","pattern":r"(?:cholesky|cholesky decomposition|LL\\^T|positive definite.*decomposition)", "compute":lambda m:"Cholesky: For symmetric positive definite A, A = LL^T with L lower triangular. Faster than LU for SPD matrices.","domain":"algebra","confidence":0.84},
            {"name":"power_iteration","pattern":r"(?:power iteration|power method|largest eigenvalue|dominant eigenvector)", "compute":lambda m:"Power iteration: x_{k+1} = A x_k / ||A x_k||. Converges to dominant eigenvector. Rayleigh quotient gives eigenvalue.","domain":"algebra","confidence":0.83},
            {"name":"gauss_seidel","pattern":r"(?:gauss.seidel|iterative linear solver|successive over.relaxation)", "compute":lambda m:"Gauss-Seidel: Iterative method for Ax=b. Uses most recent values. Converges for diagonally dominant or SPD matrices.","domain":"algebra","confidence":0.83},
            {"name":"condition_number","pattern":r"(?:condition number|ill.conditioned|well.conditioned|kappa\\(A\\)|cond\\(A\\))", "compute":lambda m:"Condition number kappa(A) = ||A|| * ||A^(-1)|| = sigma_max/sigma_min. Large kappa = ill-conditioned, sensitive to errors.","domain":"algebra","confidence":0.84},
            {"name":"norm_equivalence","pattern":r"(?:norm equivalence|L1.*L2.*Linf|equivalence.*norms)", "compute":lambda m:"All norms on finite-dimensional spaces are equivalent. ||x||_inf <= ||x||_2 <= sqrt(n)*||x||_inf.","domain":"algebra","confidence":0.83},
            {"name":"hadamard_product","pattern":r"(?:hadamard product|element.wise.*multiplication|A.*circle.*B)", "compute":lambda m:"Hadamard product (A O B): element-wise multiplication. (A O B)_{ij} = A_{ij} B_{ij}. Different from matrix multiplication.","domain":"algebra","confidence":0.85},
            {"name":"kronecker_product","pattern":r"(?:kronecker product|A.*otimes.*B|tensor product.*matrices)", "compute":lambda m:"Kronecker product: A ox B = [a_ij * B] block matrix. Used for linear systems with tensor structure.","domain":"algebra","confidence":0.83},
"""

FACTS_DATA = {
    "capitals": [
        ("R\u00e9publique Dominicaine","Saint-Domingue"),("Honduras","Tegucigalpa"),("Guatemala","Guatemala"),
        ("Nicaragua","Managua"),("Costa Rica","San Jos\u00e9"),("Panama","Panama"),
        ("Jama\u00efque","Kingston"),("Ha\u00efti","Port-au-Prince"),("R\u00e9publique Tch\u00e8que","Prague"),
        ("Slovaquie","Bratislava"),("Slov\u00e9nie","Ljubljana"),("Croatie","Zagreb"),
        ("Serbie","Belgrade"),("Bulgarie","Sofia"),("Roumanie","Bucarest"),
        ("Moldavie","Chi\u015fin\u0103u"),("Ukraine","Kiev"),("Bi\u00e9lorussie","Minsk"),
        ("Lituanie","Vilnius"),("Lettonie","Riga"),("Estonie","Tallinn"),
        ("Finlande","Helsinki"),("Su\u00e8de","Stockholm"),("Norv\u00e8ge","Oslo"),
        ("Danemark","Copenhague"),("Islande","Reykjavik"),("Irlande","Dublin"),
        ("Portugal","Lisbonne"),("Gr\u00e8ce","Ath\u00e8nes"),("Chypre","Nicosie"),
        ("Malte","La Valette"),("Luxembourg","Luxembourg"),("Monaco","Monaco"),
        ("Saint-Marin","Saint-Marin"),("Andorre","Andorre-la-Vieille"),
        ("Liechtenstein","Vaduz"),("Suisse","Berne"),("Autriche","Vienne"),
        ("Hongrie","Budapest"),("Pologne","Varsovie"),("Albanie","Tirana"),
        ("Mac\u00e9doine du Nord","Skopje"),("Mont\u00e9n\u00e9gro","Podgorica"),
        ("Bosnie-Herz\u00e9govine","Sarajevo"),("Kosovo","Pristina"),
        ("Arm\u00e9nie","Erevan"),("Azerba\u00efdjan","Bakou"),("G\u00e9orgie","Tbilissi"),
        ("Kazakhstan","Astana"),("Ouzb\u00e9kistan","Tachkent"),("Turkm\u00e9nistan","Achgabat"),
        ("Kirghizistan","Bichkek"),("Tadjikistan","Douchanb\u00e9"),
        ("Mongolie","Oulan-Bator"),("N\u00e9pal","Katmandou"),("Bhoutan","Thimphou"),
        ("Bangladesh","Dhaka"),("Myanmar","Naypyidaw"),("Tha\u00eflande","Bangkok"),
        ("Laos","Vientiane"),("Cambodge","Phnom Penh"),("Vietnam","Hano\u00ef"),
        ("Malaisie","Kuala Lumpur"),("Singapour","Singapour"),("Indon\u00e9sie","Jakarta"),
        ("Philippines","Manille"),("Timor oriental","Dili"),
        ("Papouasie-Nouvelle-Guin\u00e9e","Port Moresby"),("Fidji","Suva"),
        ("Nouvelle-Z\u00e9lande","Wellington"),("Australie","Canberra"),
    ],
    "history": [
        "La Guerre de Cent Ans (1337-1453) opposa la France et l'Angleterre.",
        "La Peste Noire (1347-1351) tua environ un tiers de la population europ\u00e9enne.",
        "L'invention de l'imprimerie par Gutenberg (vers 1440) r\u00e9volutionna la diffusion du savoir.",
        "La chute de Constantinople (1453) marqua la fin de l'Empire byzantin.",
        "La Reconquista espagnole s'acheva en 1492 avec la prise de Grenade.",
        "Le trait\u00e9 de Tordesillas (1494) partagea le Nouveau Monde entre Espagne et Portugal.",
        "La R\u00e9forme protestante d\u00e9buta avec les 95 th\u00e8ses de Luther (1517).",
        "Le Concile de Trente (1545-1563) lan\u00e7a la Contre-R\u00e9forme catholique.",
        "L'Invincible Armada espagnole fut vaincue par l'Angleterre en 1588.",
        "L'\u00e9dit de Nantes (1598) accorda la libert\u00e9 religieuse aux protestants fran\u00e7ais.",
        "La guerre de Trente Ans (1618-1648) d\u00e9vasta le Saint-Empire germanique.",
        "Le trait\u00e9 de Westphalie (1648) \u00e9tablit le principe de souverainet\u00e9 des \u00c9tats.",
        "La r\u00e9vocation de l'\u00e9dit de Nantes (1685) poussa les huguenots \u00e0 l'exil.",
        "Le si\u00e8cle des Lumi\u00e8res (XVIIIe) promut la raison, la science et les droits humains.",
        "La D\u00e9claration d'ind\u00e9pendance des \u00c9tats-Unis fut sign\u00e9e le 4 juillet 1776.",
        "La R\u00e9volution fran\u00e7aise (1789) abolit les privil\u00e8ges f\u00e9odaux et proclama les droits de l'homme.",
        "La D\u00e9claration des droits de l'homme et du citoyen date du 26 ao\u00fbt 1789.",
        "L'exp\u00e9dition de Lewis et Clark (1804-1806) explora l'Ouest am\u00e9ricain.",
        "Les guerres d'ind\u00e9pendance hispano-am\u00e9ricaines (1808-1826) lib\u00e9r\u00e8rent l'Am\u00e9rique latine.",
        "Le Congr\u00e8s de Vienne (1815) r\u00e9organisa l'Europe apr\u00e8s Napol\u00e9on.",
        "L'abolition de l'esclavage dans l'Empire britannique date de 1833.",
        "Le Printemps des peuples (1848) vit des r\u00e9volutions dans toute l'Europe.",
        "La Commune de Paris (1871) fut une exp\u00e9rience de gouvernement ouvrier.",
        "L'unification allemande fut proclam\u00e9e \u00e0 Versailles en 1871.",
        "La guerre hispano-am\u00e9ricaine (1898) marqua l'\u00e9mergence des \u00c9tats-Unis comme puissance.",
        "La r\u00e9volte des Boxers (1900) en Chine fut une r\u00e9action contre l'influence \u00e9trang\u00e8re.",
        "La guerre russo-japonaise (1904-1905) vit la premi\u00e8re victoire asiatique sur une puissance europ\u00e9enne.",
        "Le naufrage du Titanic eut lieu le 15 avril 1912.",
        "L'assassinat de l'archiduc Fran\u00e7ois-Ferdinand \u00e0 Sarajevo (28 juin 1914) d\u00e9clencha la Premi\u00e8re Guerre mondiale.",
        "Le g\u00e9nocide arm\u00e9nien (1915-1916) fit environ 1,5 million de victimes.",
        "La bataille de Verdun (1916) fut la plus longue de la Premi\u00e8re Guerre mondiale (300 jours).",
        "La r\u00e9volution russe de f\u00e9vrier 1917 renversa le tsar Nicolas II.",
        "La r\u00e9volution d'Octobre 1917 porta les bolcheviks au pouvoir en Russie.",
        "L'armistice du 11 novembre 1918 mit fin aux combats de la Premi\u00e8re Guerre mondiale.",
        "Le trait\u00e9 de Versailles (1919) imposa des conditions tr\u00e8s dures \u00e0 l'Allemagne.",
        "La guerre d'ind\u00e9pendance turque (1919-1923) aboutit \u00e0 la cr\u00e9ation de la Turquie moderne.",
        "La marche sur Rome (1922) porta Mussolini au pouvoir en Italie.",
        "L'URSS fut officiellement cr\u00e9\u00e9e le 30 d\u00e9cembre 1922.",
        "La crise de 1929 (krach de Wall Street) d\u00e9clencha la Grande D\u00e9pression.",
        "Hitler devint chancelier d'Allemagne le 30 janvier 1933.",
        "La guerre civile espagnole (1936-1939) opposa r\u00e9publicains et nationalistes.",
        "Les accords de Munich (1938) c\u00e9d\u00e8rent les Sud\u00e8tes \u00e0 l'Allemagne nazie.",
        "L'invasion de la Pologne (1er septembre 1939) d\u00e9clencha la Seconde Guerre mondiale.",
        "La bataille d'Angleterre (1940) fut la premi\u00e8re d\u00e9faite a\u00e9rienne de l'Allemagne nazie.",
        "L'invasion de l'URSS (op\u00e9ration Barbarossa, 22 juin 1941) rompit le pacte germano-sovi\u00e9tique.",
        "Le g\u00e9nocide des Juifs d'Europe (Shoah/Holocauste) fit environ 6 millions de victimes.",
        "La bataille de Stalingrad (1942-1943) fut le tournant de la guerre sur le front de l'Est.",
        "La conf\u00e9rence de Yalta (f\u00e9vrier 1945) d\u00e9cida du sort de l'Europe d'apr\u00e8s-guerre.",
        "La capitulation allemande (8 mai 1945) mit fin \u00e0 la guerre en Europe.",
        "La Charte des Nations Unies fut sign\u00e9e le 26 juin 1945 \u00e0 San Francisco.",
    ],
    "science": [
        "La th\u00e9orie de la relativit\u00e9 g\u00e9n\u00e9rale (Einstein, 1915) pr\u00e9dit les ondes gravitationnelles, d\u00e9tect\u00e9es en 2015 (LIGO).",
        "Le boson de Higgs, pr\u00e9dit en 1964, fut d\u00e9couvert au CERN en 2012.",
        "Le fond diffus cosmologique (Penzias et Wilson, 1965) est la plus ancienne lumi\u00e8re de l'univers.",
        "La constante cosmologique (Einstein, 1917) explique l'acc\u00e9l\u00e9ration de l'expansion de l'univers.",
        "La th\u00e9orie du Big Bang (Lema\u00eetre, 1927) d\u00e9crit l'origine de l'univers \u00e0 partir d'une singularit\u00e9.",
        "La nucl\u00e9osynth\u00e8se primordiale a produit H, He et Li dans les premi\u00e8res minutes de l'univers.",
        "L'inflation cosmique (Guth, 1980) explique l'homog\u00e9n\u00e9it\u00e9 et la platitude de l'univers.",
        "Le mod\u00e8le standard de la physique des particules d\u00e9crit 17 particules fondamentales.",
        "Les neutrinos ont une masse tr\u00e8s faible mais non nulle (oscillation des neutrinos, 1998).",
        "L'intrication quantique (Einstein-Podolsky-Rosen, 1935) permet la t\u00e9l\u00e9portation quantique.",
        "Le principe d'incertitude de Heisenberg (1927) : on ne peut conna\u00eetre simultan\u00e9ment position et impulsion.",
        "L'\u00e9quation de Schr\u00f6dinger (1925) d\u00e9crit l'\u00e9volution temporelle d'un syst\u00e8me quantique.",
        "La dualit\u00e9 onde-particule (de Broglie, 1924) : toute particule a aussi un comportement ondulatoire.",
        "L'effet tunnel quantique permet aux particules de traverser des barri\u00e8res \u00e9nerg\u00e9tiques.",
        "La supraconductivit\u00e9 (Onnes, 1911) : certains mat\u00e9riaux ont une r\u00e9sistance nulle en dessous d'une temp\u00e9rature critique.",
        "La fission nucl\u00e9aire (Hahn et Strassmann, 1938) lib\u00e8re de l'\u00e9nergie en brisant des noyaux lourds.",
        "La fusion nucl\u00e9aire alimente les \u00e9toiles en fusionnant des noyaux l\u00e9gers en noyaux plus lourds.",
        "Les quasars sont des noyaux galactiques actifs aliment\u00e9s par des trous noirs supermassifs.",
        "La mati\u00e8re noire (Zwicky, 1933) expliquerait la rotation anormale des galaxies.",
        "L'\u00e9nergie noire (1998) expliquerait l'acc\u00e9l\u00e9ration de l'expansion cosmique.",
    ],
    "health": [
        "L'OMS recommande 150 minutes d'activit\u00e9 physique mod\u00e9r\u00e9e par semaine pour les adultes.",
        "La vitamine D est synth\u00e9tis\u00e9e par la peau sous l'effet du soleil. Une carence peut causer fatigue et d\u00e9pression.",
        "Le diab\u00e8te de type 1 est auto-immun ; le type 2 est li\u00e9 au mode de vie (80-90% des cas).",
        "L'hypertension (>140/90 mmHg) touche 1 adulte sur 3 dans le monde.",
        "Le cholest\u00e9rol LDL ('mauvais') favorise les plaques d'ath\u00e9romes dans les art\u00e8res.",
        "L'AVC (accident vasculaire c\u00e9r\u00e9bral) est la 2e cause de mortalit\u00e9 dans le monde.",
        "Un AVC isch\u00e9mique (80% des cas) est caus\u00e9 par un caillot bloquant une art\u00e8re c\u00e9r\u00e9brale.",
        "Les signes d'un AVC : visage affaiss\u00e9, bras qui ne se l\u00e8ve pas, parole trouble (VITE).",
        "La d\u00e9pression touche environ 280 millions de personnes dans le monde (OMS).",
        "La th\u00e9rapie cognitivo-comportementale (TCC) est un traitement efficace de la d\u00e9pression et de l'anxi\u00e9t\u00e9.",
        "Le burn-out (syndrome d'\u00e9puisement professionnel) est reconnu par l'OMS depuis 2019.",
        "Les om\u00e9ga-3 (poissons gras, noix, graines de lin) sont b\u00e9n\u00e9fiques pour le c\u0153ur et le cerveau.",
        "La s\u00e9dentarit\u00e9 est le 4e facteur de risque de mortalit\u00e9 dans le monde (OMS).",
        "Le tabagisme est la premi\u00e8re cause de mortalit\u00e9 \u00e9vitable (8 millions de morts/an).",
        "L'alcool est un canc\u00e9rog\u00e8ne du groupe 1 (comme l'amiante et le tabac), selon le CIRC.",
    ],
    "tech": [
        "Le premier microprocesseur commercial fut l'Intel 4004 (1971), avec 2300 transistors.",
        "La loi de Moore (Gordon Moore, 1965) pr\u00e9dit le doublement des transistors tous les 2 ans.",
        "Le protocole TCP/IP (1974) est la base d'Internet. Vint Cerf et Bob Kahn en sont les p\u00e8res.",
        "Le World Wide Web fut invent\u00e9 au CERN par Tim Berners-Lee en 1989.",
        "Le premier navigateur web graphique, Mosaic, fut lanc\u00e9 en 1993.",
        "Google fut fond\u00e9 en 1998 par Larry Page et Sergey Brin \u00e0 Stanford.",
        "L'iPhone d'Apple (2007) r\u00e9volutionna l'industrie du smartphone.",
        "Le cloud computing (AWS lanc\u00e9 en 2006) permet d'acc\u00e9der \u00e0 des serveurs \u00e0 distance.",
        "Bitcoin, la premi\u00e8re cryptomonnaie, fut cr\u00e9\u00e9 en 2009 par Satoshi Nakamoto.",
        "L'Internet des objets (IoT) connecte des milliards d'appareils \u00e0 Internet.",
        "La 5G (d\u00e9ploy\u00e9e en 2019) offre des d\u00e9bits jusqu'\u00e0 20 Gbps et une latence < 1ms.",
        "L'informatique quantique utilise des qubits (superposition) pour r\u00e9soudre certains probl\u00e8mes exponentiellement plus vite.",
        "Les transformers (Vaswani et al., 2017) utilisent l'auto-attention et sont \u00e0 la base de GPT, BERT, Claude.",
        "GPT-3 (OpenAI, 2020) comptait 175 milliards de param\u00e8tres.",
        "AlphaFold (DeepMind, 2020) a r\u00e9solu le probl\u00e8me du repliement des prot\u00e9ines.",
    ],
    "sports": [
        "Les Jeux Olympiques modernes furent relanc\u00e9s en 1896 \u00e0 Ath\u00e8nes par Pierre de Coubertin.",
        "Le premier marathon olympique (1896) fut remport\u00e9 par le Grec Spyridon Louis.",
        "La Coupe du Monde de football a \u00e9t\u00e9 cr\u00e9\u00e9e en 1930. L'Uruguay fut le premier vainqueur.",
        "Le Br\u00e9sil a remport\u00e9 5 Coupes du Monde (1958, 1962, 1970, 1994, 2002).",
        "Lionel Messi a remport\u00e9 8 Ballons d'Or (record).",
        "Cristiano Ronaldo a marqu\u00e9 plus de 900 buts en carri\u00e8re.",
        "Usain Bolt d\u00e9tient les records du monde du 100m (9.58s) et du 200m (19.19s).",
        "Michael Phelps a remport\u00e9 23 m\u00e9dailles d'or olympiques (natation).",
        "Le Tour de France compte 21 \u00e9tapes sur 3 semaines. Record de victoires : 5 (Jacques Anquetil, Eddy Merckx, Bernard Hinault, Miguel Indurain).",
        "Serena Williams a remport\u00e9 23 titres du Grand Chelem en simple.",
        "Le Super Bowl est l'\u00e9v\u00e9nement sportif le plus regard\u00e9 aux \u00c9tats-Unis.",
    ],
}

def generate_facts():
    facts = []
    for cat, items in FACTS_DATA.items():
        for i, item in enumerate(items):
            if cat == "capitals":
                country, capital = item
                text = f"La capitale de {country} est {capital}."
                facts.append((f"cap_{country.lower().replace(' ','_')}", text, ["capitale", country.lower(), capital.lower()]))
            elif cat == "history":
                facts.append((f"hist_{i}", item, ["histoire", item.split()[0].lower()]))
            elif cat == "science":
                facts.append((f"sci_{i}", item, ["science", item.split()[0].lower()]))
            elif cat == "health":
                facts.append((f"health_{i}", item, ["sante", item.split()[0].lower()]))
            elif cat == "tech":
                facts.append((f"tech_{i}", item, ["technologie", item.split()[0].lower()]))
            elif cat == "sports":
                facts.append((f"sport_{i}", item, ["sport", item.split()[0].lower()]))
    return facts

def main():
    # Math rules
    kb_file = os.path.join(HERE, '..', 'lm_arena', 'parametric_kb.py')
    with open(kb_file, 'r', encoding='utf-8') as f:
        content = f.read()
    last_bracket = content.rfind('        ]')
    if last_bracket > 0:
        content = content[:last_bracket] + MATH_RULES + content[last_bracket:]
        with open(kb_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Math rules appended")
    
    # Quick facts
    facts = generate_facts()
    print(f"Generated {len(facts)} facts")
    
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
        print(f"Appended {len(fact_lines)} facts")
    
    print("Done.")

if __name__ == "__main__":
    main()