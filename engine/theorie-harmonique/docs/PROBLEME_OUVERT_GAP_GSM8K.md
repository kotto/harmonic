# PROBLÈME OUVERT : Résolution Spectrale pour Calcul Arithmétique

## CONTEXTE (anonymisé)

Nous avons développé un moteur de calcul arithmétique basé sur une représentation
spectrale des nombres. Le principe est le suivant :

- Chaque nombre n est représenté par un signal s_n(t) = exp(i·φ(n)·t)
- Une opération ♢ entre deux nombres se réduit à une manipulation simple
  des signaux : s_{a♢b} = s_a ♢ s_b
- Le résultat est extrait par analyse spectrale (FFT) du signal produit

Ce moteur N'UTILISE AUCUNE TABLE, aucun fait arithmétique stocké, aucun réseau
de neurones. Tout émerge de la manipulation des signaux.

## PERFORMANCE ACTUELLE

Sur un benchmark standard de 1319 problèmes arithmétiques (type problèmes
mathématiques scolaires, nombres entiers et décimaux, 4 opérations) :

- **Taux de traitement spectral : 94%** (94% des opérations sont résolues
  par la méthode spectrale, sans calcul traditionnel)
- **Précision globale : 77%** (problèmes entièrement corrects)
- **Erreur par opération : ~14%** (912 opérations, 782 correctes)

Un moteur conventionnel (non spectral, avec patterns mémorisés) atteint 91.6%
sur le même benchmark.

## LE GAP : 14.6 POINTS → TROIS PROBLÈMES TECHNIQUES

### Problème 1 — DÉPASSEMENT DE LA BANDE PASSANTE (8 points de gap)

**Situation :** La représentation d'un nombre n utilise une fréquence f(n)
proportionnelle à n. Pour n grand (jusqu'à 200 000), la fréquence dépasse
la fréquence de Nyquist de la grille d'analyse FFT, causant un repliement
spectral (aliasing) qui rend l'extraction incorrecte.

**Question :** Existe-t-il une fonction de représentation f(n) telle que :
- f(a) + f(b) = f(a+b) — préservation de l'opération d'addition
- f(n) reste borné pour tout n — pas de dépassement de bande passante
- f est inversible — on peut retrouver n à partir de f(n)

La solution triviale f(n) = n satisfait (1) mais viole (2).
La solution f(n) = log(n) satisfait (2) mais viole (1) car log(a)+log(b) ≠ log(a+b).

**Pistes envisagées :**
a) Sur-échantillonnage adaptatif (grille FFT plus fine pour les grands nombres)
b) Représentation multi-échelle (décomposition n = q·B + r)
c) Extraction directe de phase sans FFT (θ = f(n)·constante → n = θ/constante)
d) Représentation hybride avec changement de base

**Contrainte :** La solution doit fonctionner pour n ≤ 200 000 avec une grille
d'analyse ≤ 4096 points, en temps < 1 ms par opération.

### Problème 2 — ERREUR DE QUANTIFICATION (3 points de gap)

**Situation :** Pour certaines opérations, on utilise une représentation
f(n) = round(g(n)·S) où g est une fonction non linéaire et S un facteur d'échelle.
L'arrondi à l'entier introduit une erreur de quantification ∼1/(2S).

Pour S=100 : erreur ∼0.5% par opération.
Pour S=1000 : erreur ∼0.05% mais f(n) peut dépasser la bande passante.

Sur des chaînes de 3-5 opérations, l'erreur cumulée peut dépasser le seuil
de tolérance (1%).

**Question :** Comment choisir S de façon adaptative — grand quand n est petit,
petit quand n est grand — pour garantir une erreur cumulée < 1% sur 5 opérations
sans jamais dépasser la bande passante ?

**Pistes envisagées :**
a) S(n) adaptatif : fonction décroissante de n
b) Sur-résolution spectrale (zero-padding FFT)
c) Correction d'erreur a posteriori par estimation de l'erreur de quantification

### Problème 3 — CHAÎNES D'OPÉRATIONS MIXTES (2 points de gap)

**Situation :** Un problème type implique une séquence comme ((a+b)×c)÷d.
L'étape 1 (a+b) utilise la représentation linéaire. Les étapes 2-3 (×c, ÷d)
utilisent la représentation non linéaire. Le résultat intermédiaire de l'étape 1
doit être converti d'une représentation à l'autre, introduisant une erreur.

**Question :** Comment maintenir la cohérence entre deux représentations
spectrales d'un même nombre (l'une optimisée pour +/−, l'autre pour ×/÷)
sans erreur de conversion ?

**Piste envisagée :** Représentation duale — chaque nombre possède simultanément
ses deux représentations spectrales. Les opérations choisissent automatiquement
la représentation appropriée. La conversion n'est nécessaire qu'en fin de chaîne.

### Problème 4 (mineur) — EXPRESSIONS COMPOSÉES (1.5 points)

Certains problèmes du benchmark contiennent des expressions à 3+ termes
(ex: a+b+c) ou des opérations imbriquées qui ne sont pas correctement
décomposées par le parseur actuel (basé sur des regex simples).

## CONTRAINTES GLOBALES

- **Aucune table ni fait stocké** : le principe spectral doit rester le seul mécanisme
- **Déterminisme 100%** : même entrée → même sortie, toujours
- **Temps < 5 ms par opération** : traitement quasi instantané
- **Implémentation CPU pure** : Python + NumPy, pas de GPU
- **Grille d'analyse ≤ 4096 points** : contrainte mémoire/performance

## CE QUE NOUS CHERCHONS

1. Une solution mathématique ou algorithmique au Problème 1 (bande passante)
   qui préserve la propriété d'addition tout en bornant la fréquence.

2. Un schéma de quantification adaptative pour le Problème 2.

3. Une stratégie de propagation sans erreur pour le Problème 3.

4. Toute approche qui permettrait de passer de ~77% à ~91% de précision
   SANS recourir à des tables, des patterns mémorisés, ou de l'apprentissage.

## RÉFÉRENCE

La solution existante (91.6%) utilise une approche par motifs : elle stocke
des squelettes de problèmes similaires et les adapte. Nous cherchons à égaler
cette performance SANS cette mémoire — par la seule manipulation spectrale.
