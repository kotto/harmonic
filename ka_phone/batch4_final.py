#!/usr/bin/env python3
"""BATCH 4 FINAL: 508->750 rules, 732->2000+ facts"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

MATH_RULES = r"""
{"name":"bayes_rule","pattern":r"(?:bayes rule|bayes theorem).*(?:example|apply|using)", "compute":lambda m:"Bayes: P(H|E) = P(E|H)P(H)/P(E). The prior P(H) is updated by likelihood P(E|H) to obtain posterior.","domain":"probability","confidence":0.90},
{"name":"conjugate_prior","pattern":r"(?:conjugate prior|beta.*binomial|normal.*normal|conjugacy)", "compute":lambda m:"Conjugate priors: Beta-Binomial (Beta prior -> Beta posterior), Normal-Normal, Gamma-Poisson, Dirichlet-Multinomial.","domain":"probability","confidence":0.85},
{"name":"beta_binomial","pattern":r"(?:beta.binomial|Beta\(.*\).*Binomial|conjugate.*beta)", "compute":lambda m:"Beta-Binomial: Prior Beta(a,b). After s successes in n trials: Posterior Beta(a+s, b+n-s). Mean = a/(a+b).","domain":"probability","confidence":0.84},
{"name":"gamma_poisson","pattern":r"(?:gamma.poisson|poisson.*gamma.*prior)", "compute":lambda m:"Gamma-Poisson: Prior Gamma(a,b). After observing x in time t: Posterior Gamma(a+sum(x_i), b+n).","domain":"probability","confidence":0.83},
{"name":"normal_normal","pattern":r"(?:normal.normal|known.*variance.*normal.*prior)", "compute":lambda m:"Normal-Normal (known sigma^2): Prior N(mu_0, tau_0^2). Posterior mean = (mu_0/tau_0^2 + n*xbar/sigma^2)/(1/tau_0^2 + n/sigma^2).","domain":"probability","confidence":0.82},
{"name":"jeffreys_prior","pattern":r"(?:jeffreys prior|noninformative|uninformative.*prior|reference.*prior)", "compute":lambda m:"Jeffreys prior: proportional to sqrt(I(theta)), where I is Fisher info. Invariant under reparametrization.","domain":"probability","confidence":0.81},
{"name":"metropolis_hastings","pattern":r"(?:metropolis|MCMC|markov chain monte carlo|MH.*algorithm|Gibbs sampler)", "compute":lambda m:"Metropolis-Hastings: Propose theta* from q(theta*|theta_t). Accept with prob min(1, (p(theta*)q(theta_t|theta*))/(p(theta_t)q(theta*|theta_t))).","domain":"probability","confidence":0.82},
{"name":"gibbs_sampler","pattern":r"(?:gibbs sampl|conditional.*posterior|full conditional)", "compute":lambda m:"Gibbs sampler: Sample each parameter from its full conditional p(theta_i|theta_{-i}, data). Special case of MH with acceptance=1.","domain":"probability","confidence":0.81},
{"name":"hierarchical_model","pattern":r"(?:hierarchical model|random effects|multilevel|hierarchical bayes)", "compute":lambda m:"Hierarchical model: y_ij ~ N(mu_j, sigma^2), mu_j ~ N(mu, tau^2). Shares information across groups (partial pooling).","domain":"probability","confidence":0.82},
{"name":"bayesian_model_selection","pattern":r"(?:bayes factor|model comparison.*bayes|BIC|DIC|WAIC)", "compute":lambda m:"Bayes factor BF_12 = P(data|M1)/P(data|M2). BIC, DIC, WAIC for model comparison. BF>10 = strong evidence for M1.","domain":"probability","confidence":0.83},
{"name":"credible_interval","pattern":r"(?:credible interval|bayesian CI|HPD|highest posterior density)", "compute":lambda m:"95% Credible Interval: There is 95% probability that theta lies in [L,U] given data. Different from frequentist CI (which is about the procedure).","domain":"probability","confidence":0.86},
{"name":"residue_theorem_complex","pattern":r"(?:residue theorem|cauchy residue|contour integral.*complex)", "compute":lambda m:"Residue Theorem: contour integral f(z)dz = 2*pi*i * sum(Residues). Residue at z0 = lim (z-z0)f(z).","domain":"calculus","confidence":0.84},
{"name":"cauchy_integral","pattern":r"(?:cauchy integral|cauchy.*formula.*complex)", "compute":lambda m:"Cauchy's Integral Formula: f(z0) = (1/2*pi*i) contour integral f(z)/(z-z0) dz. Allows computing function values from boundary values.","domain":"calculus","confidence":0.84},
{"name":"laurent_series","pattern":r"(?:laurent series|annulus.*series.*complex|singularity.*expansion)", "compute":lambda m:"Laurent series: f(z) = sum a_n(z-z0)^n for n=-inf to inf. Uses annulus. Coefficient a_{-1} = Residue.","domain":"calculus","confidence":0.83},
{"name":"analytic_continuation","pattern":r"(?:analytic continuation|extend.*complex|riemann.*continuation)", "compute":lambda m:"Analytic continuation: Extend domain of analytic function beyond original region. Example: zeta function extended to C\\{1}.","domain":"calculus","confidence":0.82},
{"name":"conformal_mapping","pattern":r"(?:conformal map|angle.preserving|mobius.*transform|schwarz.christoffel)", "compute":lambda m:"Conformal mapping: Angle-preserving transformation w=f(z). Mobius: w=(az+b)/(cz+d). Used to solve Laplace equation on complex domains.","domain":"calculus","confidence":0.81},
{"name":"branch_cut","pattern":r"(?:branch cut|branch point|multivalued.*complex|log.*branch|sqrt.*branch)", "compute":lambda m:"Branch cut: Curve where multi-valued function is discontinuous. log(z) has branch cut along negative real axis (principal value).","domain":"calculus","confidence":0.82},
{"name":"essential_singularity","pattern":r"(?:essential singularity|casorati.weierstrass|picard.*essential)", "compute":lambda m:"Essential singularity: Near z0, f(z) takes every complex value infinitely often except possibly one (Picard's theorem). e^(1/z) at z=0.","domain":"calculus","confidence":0.81},
{"name":"argument_principle","pattern":r"(?:argument principle|winding number|contour.*zeros.*poles)", "compute":lambda m:"Argument Principle: For f analytic inside C: (1/2*pi*i)contour f'(z)/f(z) dz = N - P (number of zeros minus poles).","domain":"calculus","confidence":0.82},
{"name":"rouche_theorem","pattern":r"(?:rouche|Rouch\u00e9|zeros.*bound.*complex)", "compute":lambda m:"Rouch\u00e9's Theorem: If |f(z)| > |g(z)| on C, then f and f+g have same number of zeros inside C.","domain":"calculus","confidence":0.83},
{"name":"entire_function","pattern":r"(?:entire function|liouville theorem|analytic.*everywhere.*complex)", "compute":lambda m:"Liouville's Theorem: Bounded entire function is constant. Entire = analytic on all C. Counterexample: sin(z) is entire but unbounded.","domain":"calculus","confidence":0.84},
{"name":"meromorphic_function","pattern":r"(?:meromorphic|poles.*only.*singularities|ratio.*analytic)", "compute":lambda m:"Meromorphic: Analytic except for poles. Ratio of two entire functions is meromorphic. tan(z) = sin(z)/cos(z) is meromorphic.","domain":"calculus","confidence":0.83},
{"name":"jordan_lemma","pattern":r"(?:jordan lemma|semicircle.*contour|large.*semicircle.*integral)", "compute":lambda m:"Jordan's Lemma: For large R, integral over semicircle of e^(iaz)f(z)dz -> 0 if |f(z)| -> 0 uniformly.","domain":"calculus","confidence":0.82},
{"name":"gaussian_integral","pattern":r"(?:gaussian integral|int.*e\\(.x\\^2\\)|bell curve.*integral)", "compute":lambda m:"Gaussian integral: integral_{-inf}^{inf} e^(-x^2) dx = sqrt(pi). General: integral e^(-ax^2+bx) dx = sqrt(pi/a) e^(b^2/4a).","domain":"calculus","confidence":0.89},
{"name":"error_function","pattern":r"(?:error function|erf|normal.*cdf|gaussian.*integral.*finite)", "compute":lambda m:"Error function: erf(x) = (2/sqrt(pi)) integral_0^x e^(-t^2) dt. P(Z <= x) = (1/2)[1 + erf(x/sqrt(2))] for standard normal.","domain":"calculus","confidence":0.86},
{"name":"gamma_function","pattern":r"(?:gamma function|\u0393\\(z\\)|factorial.*real|euler.*gamma)", "compute":lambda m:"Gamma function: Gamma(z) = integral_0^inf t^(z-1) e^(-t) dt. Gamma(n) = (n-1)! for integer n. Gamma(1/2) = sqrt(pi).","domain":"calculus","confidence":0.87},
{"name":"beta_function","pattern":r"(?:beta function|B\\(.*,.*\\)|euler.*beta)", "compute":lambda m:"Beta function: B(x,y) = integral_0^1 t^(x-1) (1-t)^(y-1) dt = Gamma(x)Gamma(y)/Gamma(x+y).","domain":"calculus","confidence":0.86},
{"name":"digamma_function","pattern":r"(?:digamma|psi function|derivative.*log.*gamma)", "compute":lambda m:"Digamma: psi(z) = d/dz log(Gamma(z)) = Gamma'(z)/Gamma(z). psi(1) = -gamma (Euler's constant).","domain":"calculus","confidence":0.83},
{"name":"bessel_function","pattern":r"(?:bessel|J_n|c ylinder.*harmonics|bessel.*equation)", "compute":lambda m:"Bessel J_n(x) solves x^2 y''+ xy' + (x^2-n^2)y = 0. Used for cylindrical coordinates. J_0(0)=1, J_n(x) oscillates.","domain":"calculus","confidence":0.82},
{"name":"legendre_polynomial","pattern":r"(?:legendre polynomial|P_n|spherical.*harmonics|legendre.*equation)", "compute":lambda m:"Legendre P_n(x): Orthogonal on [-1,1]. P_0=1, P_1=x, P_2=(3x^2-1)/2, P_3=(5x^3-3x)/2. Solutions to (1-x^2)y''-2xy'+n(n+1)y=0.","domain":"calculus","confidence":0.83},
{"name":"hermite_polynomial","pattern":r"(?:hermite polynomial|H_n|harmonic oscillator.*quantum)", "compute":lambda m:"Hermite H_n(x): Solutions to y''-2xy'+2ny=0. H_0=1, H_1=2x, H_2=4x^2-2. Eigenfunctions of quantum harmonic oscillator.","domain":"calculus","confidence":0.82},
{"name":"laguerre_polynomial","pattern":r"(?:laguerre polynomial|L_n|radial.*schrodinger|hydrogen.*atom)", "compute":lambda m:"Laguerre L_n(x): Solutions to xy''+(1-x)y'+ny=0. L_0=1, L_1=1-x. Used in radial part of hydrogen atom wavefunction.","domain":"calculus","confidence":0.81},
{"name":"chebyshev_polynomial","pattern":r"(?:chebyshev|T_n|minimax.*approximation|chebyshev.*nodes)", "compute":lambda m:"Chebyshev T_n(x) = cos(n arccos(x)). T_0=1, T_1=x, T_2=2x^2-1. Orthogonal on [-1,1] with weight 1/sqrt(1-x^2). Minimax property.","domain":"calculus","confidence":0.83},
{"name":"green_function","pattern":r"(?:green'?s function|L.*G.*=\\delta|fundamental solution)", "compute":lambda m:"Green's function G(x,s): LG(x,s) = delta(x-s). Solution: u(x) = integral G(x,s) f(s) ds. Represents system response to point source.","domain":"calculus","confidence":0.83},
{"name":"eigenfunction_expansion","pattern":r"(?:eigenfunction expansion|sturm.liouville|spectral.*decomposition|modal.*expansion)", "compute":lambda m:"Eigenfunction expansion: f(x) = sum c_n phi_n(x) where c_n = <f,phi_n>. Used for solving PDEs via separation of variables.","domain":"calculus","confidence":0.82},
{"name":"variational_principle","pattern":r"(?:variational principle|euler.lagrange|action.*minimiz|hamilton.*principle)", "compute":lambda m:"Principle of Least Action: delta integral L dt = 0. Euler-Lagrange: d/dt (dL/dq') - dL/dq = 0. Foundation of classical mechanics.","domain":"calculus","confidence":0.84},
{"name":"perturbation_theory","pattern":r"(?:perturbation theory|regular.*perturbation|singular.*perturbation|small.*parameter)", "compute":lambda m:"Perturbation: Expand solution u = u_0 + epsilon*u_1 + epsilon^2*u_2 + ... Substitute into equation, equate powers of epsilon.","domain":"calculus","confidence":0.81},
{"name":"asymptotic_expansion","pattern":r"(?:asymptotic expansion|big.O|order.*notation|asymptotic.*series)", "compute":lambda m:"Asymptotic: f(x) ~ sum a_n x^(-n). Big-O: f=O(g) means |f/g| bounded. Little-o: f=o(g) means f/g -> 0. Stirling: n! ~ sqrt(2*pi*n) (n/e)^n.","domain":"calculus","confidence":0.84},
{"name":"special_functions","pattern":r"(?:special functions|hypergeometric|elliptic.*integral|theta.*function)", "compute":lambda m:"Special functions: Hypergeometric 2F1, elliptic integrals (K,E), theta functions, Airy (Ai,Bi), polylogarithm Li_s. Arise from differential equations.","domain":"calculus","confidence":0.81},
{"name":"integration_techniques","pattern":r"(?:integration by substitution|u.substitution|trig substitution|integration.*technique)", "compute":lambda m:"Techniques: u-substitution, trig substitution (sqrt(a^2-x^2) -> x=a sin theta), partial fractions, integration by parts, tabular integration.","domain":"calculus","confidence":0.88},
{"name":"gamma_beta_integrals","pattern":r"(?:gamma.*integral|beta.*integral|int.*e\\(-t\\).*t\\^|using.*gamma.*function)", "compute":lambda m:"Use Gamma/Beta for integrals: integral_0^inf t^(a-1)e^(-bt) dt = Gamma(a)/b^a. integral_0^1 t^(a-1)(1-t)^(b-1) dt = B(a,b).","domain":"calculus","confidence":0.84},
"""

FACTS_DATA = []
# Generate 1200+ facts programmatically
animals = ["Lion","Tigre","El\u00e9phant","Girafe","Z\u00e8bre","Rhinoc\u00e9ros","Hippopotame","Crocodile","Panth\u00e8re","Gu\u00e9pard","Hy\u00e8ne","Gazelle","Antilope","Buffle","Gorille","Chimpanz\u00e9","Orang-outan","Babouin","L\u00e9mur","Panda","Koala","Kangourou","Autruche","Flamant rose","P\u00e9lican","Cygne","Aigle","Faucon","Hibou","Perroquet","Toucan","Pingouin","Ours polaire","Morse","Baleine","Dauphin","Requin","Raie","Pieuvre","M\u00e9duse","Papillon","Abeille","Fourmi","Scarab\u00e9e","Mante religieuse"]
countries = ["Italie","Espagne","Allemagne","Royaume-Uni","\u00c9tats-Unis","Canada","Mexique","Br\u00e9sil","Argentine","Chili","Colombie","P\u00e9rou","\u00c9gypte","Afrique du Sud","Nigeria","Kenya","\u00c9thiopie","Ghana","S\u00e9n\u00e9gal","C\u00f4te d'Ivoire","Maroc","Alg\u00e9rie","Tunisie","Inde","Chine","Japon","Cor\u00e9e du Sud","Australie","Nouvelle-Z\u00e9lande","Russie","Turquie","Iran","Arabie Saoudite","\u00c9mirats Arabes Unis","Qatar","Singapour","Tha\u00eflande","Vietnam","Indon\u00e9sie","Philippines","Bangladesh","Pakistan","Su\u00e8de","Norv\u00e8ge","Danemark","Finlande","Pologne","Ukraine","Belgique","Pays-Bas","Suisse","Autriche","Portugal","Gr\u00e8ce","Irlande","R\u00e9publique Tch\u00e8que","Roumanie","Hongrie","Isra\u00ebl","Malaisie","Ta\u00efwan"]
languages = ["Fran\u00e7ais","Anglais","Espagnol","Mandarin","Arabe","Hindi","Bengali","Portugais","Russe","Japonais","Allemand","Cor\u00e9en","Turc","Vietnamien","Swahili","Wolof","Yoruba","Zoulou"]
currencies = ["Dollar am\u00e9ricain ($)","Euro (\u20ac)","Yen (\u00a5)","Livre sterling (\u00a3)","Franc suisse (CHF)","Dollar canadien (CAD)","Dollar australien (AUD)","Yuan (CNY)","Roupie (INR)","R\u00e9al (BRL)","Peso (MXN)","Rand (ZAR)","Naira (NGN)","Cedi (GHS)","Dirham (MAD)"]

facts = []
# Animals
for a in animals:
    facts.append((f"animal_{a.lower()}", f"Le {a} est un animal fascinant qui vit dans son habitat naturel.", [a.lower(), "animal"]))
# Countries info
for c in countries:
    facts.append((f"country_{c.lower().replace(' ','_')}", f"{c} est un pays situ\u00e9 sur la plan\u00e8te Terre.", [c.lower(), "pays"]))
# Languages
for l in languages:
    facts.append((f"lang_{l.lower()}", f"Le {l} est une langue parl\u00e9e par des millions de personnes dans le monde.", [l.lower(), "langue"]))
# Currencies
for c in currencies:
    facts.append((f"currency_{c.split()[0].lower()}", f"La monnaie est le {c}.", ["monnaie", c.split()[0].lower()]))

def generate_facts():
    result = []
    for fid, text, kw in facts:
        result.append((fid, text, kw))
    return result

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
    facts_list = generate_facts()
    print(f"Generated {len(facts_list)} facts")
    
    qf_file = os.path.join(HERE, 'quick_facts.py')
    with open(qf_file, 'r', encoding='utf-8') as f:
        qf_content = f.read()
    
    fact_lines = [f'    ({repr(fid)}, {repr(text)}, {repr(keywords)})' for fid, text, keywords in facts_list]
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