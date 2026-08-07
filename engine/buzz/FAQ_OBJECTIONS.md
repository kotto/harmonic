# 🛡️ FAQ & OBJECTIONS — Les questions qui tuent, et nos réponses

> Principe : nous donnons la critique avant qu'elle ne soit trouvée.
> Chaque réponse est courte, factuelle, et ne conteste jamais une mesure.

## 1 · « 33 questions, c'est minuscule — et c'est un benchmark maison ? »

**Réponse** : le dataset est **public et fixé dans le code** — n'importe
qui peut l'ouvrir, le modifier, l'étendre. Le script interroge les LLM
adverses avec la même méthodologie (mêmes questions, même vérification
exacte). Rien n'est caché : c'est le contraire d'un benchmark maison
fermé. Et l'étendons : le principe (calcul exact prouvé par exécution)
vaut pour n'importe quel calcul — le défi public en ligne le démontre.

## 2 · « Que donne GSM8K officiel ? »

**Réponse** : 1,6 % pass@1 sur les 1319 problèmes officiels — nous le
publions nous-mêmes. Nous ne faisons pas de raisonnement génératif, et
nous ne le prétendons pas. Ce que GSM8K prouve chez nous, c'est le
**langage** : 99,2 % des réponses GSM8K s'expriment comme une chaîne
d'opérations exécutées exactement. La construction de la chaîne pour un
problème non vu est notre chantier de recherche — le rapport complet est
public (PLAN_GSM8K.md).

## 3 · « HumanEval à 100 %, c'est de la triche : les solutions sont en mémoire »

**Réponse** : les solutions canoniques HumanEval (licence MIT) sont dans
une mémoire **lisible et vérifiée par exécution** — c'est exactement la
thèse : générer = rappeler + vérifier. Un LLM a « mémorisé » les patterns
dans des poids opaques ; notre mémoire est transparente, chaque réponse
est prouvée par l'exécution des tests officiels. Nous ne présentons pas
ça comme de la génération — nous le présentons comme la démonstration
que la récupération vérifiée remplace la génération opaque.

## 4 · « C'est une calculatrice, pas une IA »

**Réponse** : le calcul exact n'est qu'une brique. La même architecture
répond sur les données privées d'une entreprise (avec confiance et
sources), produit des Excel et des documents rédigés, s'intègre via MCP,
et s'enrichit des questions réelles. Le calcul est à l'IA ce que le
moteur est à la voiture : indispensable, mais pas la voiture.

## 5 · « Pourquoi pas sur LM Arena ? »

**Réponse** : LM Arena mesure la génération sur des conversations
ouvertes — notre catégorie est la **certitude** : réponse ancrée,
refus calibré, déterminisme. Nous publions notre propre classement
(comparatif certitude, 0 hallucination) et le défi public en ligne —
chacun peut tester.

## 6 · « L'IA ne sait pas écrire un poème / débattre — c'est limité »

**Réponse** : oui, et c'est un choix. Nous ne faisons pas de créativité
— nous faisons de la **vérité sur vos données**. Pour une entreprise,
la question n'est pas « sait-il inventer ? » mais « peut-on lui faire
confiance ? ». C'est le produit.

## 7 · « Vos autres benchmarks (100 % maths) sont faux ? »

**Réponse** : ils sont **vrais mais internes** : des jeux de questions
calibrés sur nos capacités, utiles au développement. Nous ne les
diffusons pas comme preuves publiques. Les preuves publiques sont dans
PREUVES.md — toutes reproductibles.

## 8 · « 0 hallucination, vraiment ? »

**Réponse** : structurellement, oui : l'IA ne répond que par
récupération/exécution de ce qui a été ingéré, et le gate refuse quand
la résonance est insuffisante. Mesuré : 5/5 refus hors corpus, 0
hallucination. Ce que nous ne garantissons pas : la qualité de ce qui
a été ingéré (un document faux reste faux) — nous affichons confiance
et sources pour que l'utilisateur juge.

## 9 · « Et si on veut du raisonnement créatif ? »

**Réponse** : connectez un LLM à nos données via MCP — notre rôle est
de fournir la couche de vérité (données privées, ancrées, sourcées) ;
le LLM apporte la fluidité. Les deux se complètent : c'est l'architecture
hybride que nous recommandons à ceux qui en ont besoin.

## 10 · « C'est français, souverain ? »

**Réponse** : tout tourne sur le VPS de l'entreprise, aucun appel à un
modèle tiers, aucune donnée ne sort. 0 GPU, 0 dépendance cloud. C'est
l'IA de vos données, chez vous.
