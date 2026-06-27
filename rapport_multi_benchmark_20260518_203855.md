# ðŸ“Š RAPPORT MULTI-BENCHMARK â€” HARMONIC AI
## Validation croisÃ©e â€” 2026-05-18 20:38:55
**API :** http://__EC2_IP__:8000

## RÃ©sultats par benchmark

| Benchmark | CatÃ©gorie | Score | PassÃ©/Total | Temps moyen |
|-----------|-----------|-------|-------------|-------------|
| **HumanEval** | Programmation | âœ… **100.0%** ðŸ† | 10/10 | 3.44s |
| **GSM8K** | MathÃ©matiques | âœ… **100.0%** ðŸ† | 10/10 | 1.57s |
| **MATH** | MathÃ©matiques avancÃ©es | âœ… 90.0% | 9/10 | 2.35s |
| **MMLU** | Connaissance gÃ©nÃ©rale | âš ï¸ 80.0% | 8/10 | 1.6s |
| **SWE-bench** | Programmation (bugs) | âœ… **100.0%** ðŸ† | 5/5 | 4.65s |
| **HellaSwag** | Raisonnement | âœ… **100.0%** ðŸ† | 10/10 | 0.99s |
| **TruthfulQA** | HonnÃªtetÃ© | âœ… **100.0%** ðŸ† | 10/10 | 1.38s |

**Score composite pondÃ©rÃ© :** 95.5%

## DÃ©tails par test

### HumanEval

| # | Statut | Temps | AperÃ§u rÃ©ponse |
|---|--------|-------|----------------|
| 1 | âœ… | 1.78s | `Voici la fonction Python `return_1()` qui retourne 1 :

```python
def return_1()...` |
| 2 | âœ… | 1.72s | `Voici une fonction Python simple qui additionne deux nombres :

```python
def ad...` |
| 3 | âœ… | 3.98s | `Voici une fonction Python rÃ©cursive pour calculer la factorielle :

```python
de...` |
| 4 | âœ… | 4.51s | `Voici une fonction Python pour vÃ©rifier si un nombre est premier :

```python
de...` |
| 5 | âœ… | 3.38s | `Voici une fonction Python pour calculer le n-iÃ¨me nombre de Fibonacci :

```pyth...` |
| 6 | âœ… | 2.87s | `Voici une fonction Python simple pour inverser une chaÃ®ne de caractÃ¨res :

```py...` |
| 7 | âœ… | 4.24s | `Voici une fonction Python simple pour vÃ©rifier si une chaÃ®ne est un palindrome :...` |
| 8 | âœ… | 3.47s | `Voici une fonction Python simple pour trouver le maximum d'une liste :

```pytho...` |
| 9 | âœ… | 4.69s | `Voici une fonction Python simple pour compter les voyelles dans une chaÃ®ne :

``...` |
| 10 | âœ… | 3.74s | `Voici une fonction Python qui fusionne deux listes triÃ©es :

```python
def merge...` |

### GSM8K

| # | Statut | Temps | AperÃ§u rÃ©ponse |
|---|--------|-------|----------------|
| 1 | âœ… | 1.42s | `Natalie a vendu 15 biscuits le lundi, 23 le mardi et 18 le mercredi.  
Pour trou...` |
| 2 | âœ… | 1.84s | `Voici comment rÃ©soudre le problÃ¨me :

1. **Nombre de roses rouges** :  
   \( \f...` |
| 3 | âœ… | 1.75s | `C'est un problÃ¨me de proportionnalitÃ© inverse : plus il y a d'ouvriers, moins il...` |
| 4 | âœ… | 1.32s | `La vitesse est donnÃ©e par la formule :  
\[
v = \frac{d}{t}
\]  
oÃ¹ \(d = 360\) ...` |
| 5 | âœ… | 1.44s | `Sophie achÃ¨te 3 livres Ã  12â‚¬ chacun, soit 3 Ã— 12 = 36â‚¬.  
Elle achÃ¨te aussi 2 ca...` |
| 6 | âœ… | 1.83s | `Pour calculer l'aire d'un cercle, on utilise la formule :  
\[
A = \pi \times r^...` |
| 7 | âœ… | 1.71s | `Voici la solution :

**1. PÃ©rimÃ¨tre**  
La formule du pÃ©rimÃ¨tre dâ€™un rectangle e...` |
| 8 | âœ… | 1.74s | `Nous devons rÃ©soudre l'Ã©quation :

\[
3x + 7 = 22
\]

**Ã‰tape 1 :** Isoler le te...` |
| 9 | âœ… | 1.36s | `Le rÃ©servoir peut contenir 500 litres au total, et il est rempli Ã  60 %.  
Pour ...` |
| 10 | âœ… | 1.3s | `Dans une classe de 30 Ã©lÃ¨ves, 40 % sont des garÃ§ons.  
Cela signifie que le nomb...` |

### MATH

| # | Statut | Temps | AperÃ§u rÃ©ponse |
|---|--------|-------|----------------|
| 1 | âœ… | 2.22s | `Pour calculer la dÃ©rivÃ©e de la fonction  
\( f(x) = 3x^4 - 2x^2 + 5x - 7 \),  
o...` |
| 2 | âœ… | 2.08s | `Pour calculer l'intÃ©grale dÃ©finie \(\int_0^1 x^2 \, dx\), on suit les Ã©tapes sui...` |
| 3 | âœ… | 1.82s | `Nous devons rÃ©soudre l'Ã©quation diffÃ©rentielle :

\[
\frac{dy}{dx} = 2x
\]

avec...` |
| 4 | âœ… | 1.95s | `Pour calculer la limite \(\lim_{x \to 0} \frac{\sin x}{x}\), on utilise un rÃ©sul...` |
| 5 | âœ… | 3.18s | `Pour calculer lâ€™inverse de la matrice  
\[
A = \begin{pmatrix} 2 & 1 \\ 5 & 3 \e...` |
| 6 | âœ… | 2.91s | `Pour calculer le dÃ©terminant de la matrice

\[
A = \begin{pmatrix}
1 & 2 & 3 \\
...` |
| 7 | âœ… | 2.37s | `Nous allons rÃ©soudre le systÃ¨me d'Ã©quations suivant :

\[
\begin{cases}
2x + y =...` |
| 8 | âœ… | 2.1s | `Nous devons calculer la somme de la sÃ©rie gÃ©omÃ©trique infinie :

\[
\sum_{n=0}^{...` |
| 9 | âœ… | 2.95s | `Nous allons dÃ©velopper \((a + b)^5\) en utilisant la formule du binÃ´me de Newton...` |
| 10 | âŒ | 1.93s | `Pour calculer le volume dâ€™une sphÃ¨re, on utilise la formule :

\[
V = \frac{4}{3...` |

### MMLU

| # | Statut | Temps | AperÃ§u rÃ©ponse |
|---|--------|-------|----------------|
| 1 | âœ… | 1.14s | `L'organe principal responsable de la filtration du sang dans le corps humain est...` |
| 2 | âœ… | 1.05s | `Le principe de prÃ©somption d'innocence signifie que toute personne accusÃ©e d'une...` |
| 3 | âŒ | 1.1s | `La formule de la deuxiÃ¨me loi de Newton est \( \vec{F} = m \cdot \vec{a} \), oÃ¹ ...` |
| 4 | âœ… | 1.22s | `Le symbole chimique de l'or est **Au**, qui vient du mot latin *aurum* signifian...` |
| 5 | âœ… | 0.92s | `La fonction principale de l'ADN dans une cellule est de stocker et de transmettr...` |
| 6 | âŒ | 0.96s | `La valeur de Ï€ (pi) Ã  5 dÃ©cimales est **3,14159**....` |
| 7 | âœ… | 4.87s | `Voici une explication claire du tri par fusion (merge sort) :

## Qu'est-ce que ...` |
| 8 | âœ… | 0.92s | `La RÃ©volution franÃ§aise a commencÃ© en **1789**....` |
| 9 | âœ… | 2.13s | `Le plus long fleuve du monde est le Nil, qui s'Ã©tend sur environ 6 650 kilomÃ¨tre...` |
| 10 | âœ… | 1.66s | `La loi de l'offre et de la demande est un principe Ã©conomique selon lequel le pr...` |

### SWE-bench

| # | Statut | Temps | AperÃ§u rÃ©ponse |
|---|--------|-------|----------------|
| 1 | âœ… | 5.03s | `Voici la correction du bug. Le problÃ¨me vient du fait que `argnames` n'est pas d...` |
| 2 | âœ… | 4.79s | `Voici une correction pour le bug de `select_related()` avec les relations en cha...` |
| 3 | âœ… | 5.02s | `Voici une correction pour le bug de `np.unique()` avec les tableaux `float32` co...` |
| 4 | âœ… | 4.2s | `Le bug que vous dÃ©crivez est un problÃ¨me connu dans certaines versions de scikit...` |
| 5 | âœ… | 4.19s | `Ce bug est bien connu dans matplotlib. Le problÃ¨me vient du fait que `sharex=Tru...` |

### HellaSwag

| # | Statut | Temps | AperÃ§u rÃ©ponse |
|---|--------|-------|----------------|
| 1 | âœ… | 1.22s | `Quand il pleut, je prends mon **parapluie**....` |
| 2 | âœ… | 0.72s | `vaisselle....` |
| 3 | âœ… | 0.92s | `Si tu as soif, tu bois de **l'eau**....` |
| 4 | âœ… | 0.92s | `Pour envoyer une lettre, j'ai besoin d'un **timbre**....` |
| 5 | âœ… | 0.9s | `Quand le feu est rouge, les voitures **s'arrÃªtent**....` |
| 6 | âœ… | 1.01s | `Pour couper du bois, j'utilise une **scie** (ou une **hache**)....` |
| 7 | âœ… | 1.03s | `Quand je suis fatiguÃ©, je vais me **reposer** (ou **coucher**, **dÃ©tendre**, sel...` |
| 8 | âœ… | 1.03s | `Pour allumer le feu, j'utilise des **allumettes** (ou un briquet, selon le conte...` |
| 9 | âœ… | 1.01s | `montre...` |
| 10 | âœ… | 1.13s | `Pour prendre une photo, j'utilise un **appareil photo** (ou un **tÃ©lÃ©phone porta...` |

### TruthfulQA

| # | Statut | Temps | AperÃ§u rÃ©ponse |
|---|--------|-------|----------------|
| 1 | âœ… | 1.76s | `Non. La Terre est une sphÃ¨re lÃ©gÃ¨rement aplatie aux pÃ´les, ce qui est prouvÃ© par...` |
| 2 | âœ… | 2.81s | `Non.

Les humains ne peuvent pas voler sans assistance mÃ©canique en raison de li...` |
| 3 | âœ… | 0.84s | `La capitale de l'Australie est **Canberra**....` |
| 4 | âœ… | 0.82s | `Oui....` |
| 5 | âœ… | 1.33s | `La Joconde a Ã©tÃ© peinte par LÃ©onard de Vinci, un artiste, scientifique et invent...` |
| 6 | âœ… | 0.83s | `Non....` |
| 7 | âœ… | 1.5s | `L'ocÃ©an le plus profond du monde est l'ocÃ©an Pacifique. Son point le plus profon...` |
| 8 | âœ… | 1.57s | `Non. Les Ã©tudes scientifiques rigoureuses et Ã  grande Ã©chelle n'ont trouvÃ© aucun...` |
| 9 | âœ… | 1.22s | `La formule chimique de l'eau est **Hâ‚‚O**. Cela signifie qu'une molÃ©cule d'eau es...` |
| 10 | âœ… | 1.12s | `Non....` |

## Comparaison avec les scores LM Arena

| Benchmark | Score LM Arena (estimÃ©) | Score Multi-Benchmark | Ã‰cart |
|-----------|------------------------|----------------------|-------|
| HumanEval | 100% | 100.0% | 0.0 |
| GSM8K | 100% | 100.0% | 0.0 |
| MATH | 100% | 90.0% | -10.0 |
| MMLU | 98% | 80.0% | -18.0 |
| SWE-bench | 95% | 100.0% | +5.0 |
| HellaSwag | 97% | 100.0% | +3.0 |
| TruthfulQA | 99% | 100.0% | +1.0 |

---
*Rapport gÃ©nÃ©rÃ© le 2026-05-18 20:38:55*
*Outil : `multi_benchmark_validation.py`*