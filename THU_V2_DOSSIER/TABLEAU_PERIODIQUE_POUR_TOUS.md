# 🧪 LE TABLEAU PÉRIODIQUE — LE PROCESSUS DE REMPLISSAGE

## Comment 118 éléments sortent d'une seule règle — expliqué à tout le monde

**Auteur :** Alain Kotto — Univers-Holistique, Paris
**Théorie :** Théorie de l'Univers Harmonique (THU V2)
**Date :** 9 août 2026

---

> *« Le tableau périodique n'est pas une liste apprise par cœur. C'est un immeuble rempli selon une règle unique — et les 118 éléments qui existent sont ceux que la nature n'a pas éliminés. »*

Ce document explique, sans aucune formule intimidante, comment la THU **génère** le tableau périodique : quelles sont les « pièces » de l'immeuble, dans quel ordre on les remplit, pourquoi les périodes ont leurs tailles (2, 8, 8, 18, 18, 32, 32), et pourquoi les gaz nobles sont les survivants.

---

## 1. L'image de départ : un immeuble à électrons

Autour de chaque noyau d'atome, les électrons s'organisent comme les habitants d'un **immeuble** :

```
ETAGE 7  ──────────────── 32 places (2 + 14 + 10 + 6)
ETAGE 6  ──────────────── 32 places
ETAGE 5  ──────────────── 18 places
ETAGE 4  ──────────────── 18 places
ETAGE 3  ──────────────── 8 places
ETAGE 2  ──────────────── 8 places
ETAGE 1  ──────────────── 2 places
```

**Les étages sont les « périodes » du tableau.** Les nombres de places — 2, 8, 8, 18, 18, 32, 32 — sont les **tailles des lignes du tableau périodique** : ligne 1 = 2 éléments (H, He), ligne 2 = 8 éléments, … ligne 7 = 32 éléments. **2 + 8 + 8 + 18 + 18 + 32 + 32 = 118.** Exactement les 118 éléments connus.

**La grande question :** pourquoi ces tailles-là et pas d'autres ? Réponse : elles ne sont pas choisies — elles sont **calculables** à partir de simples nombres entiers.

---

## 2. Les matériaux de construction : uniquement des entiers

La THU ne postule rien. Elle utilise les **quatre numéros quantiques** — quatre nombres entiers qui décrivent chaque place possible d'un électron :

| Numéro | Nom | Ce qu'il décrit | Valeurs |
|---|---|---|---|
| **n** | Principal | L'étage (la distance au noyau) | 1, 2, 3, 4, 5, 6, 7… |
| **l** | Azimutal | La forme de la pièce | 0 = s, 1 = p, 2 = d, 3 = f |
| **m** | Magnétique | L'orientation de la pièce dans l'espace | −l … 0 … +l |
| **s** | Spin | Les deux sens de rotation de l'électron | +½, −½ |

Rien que des entiers. **Aucune constante physique, aucun paramètre ajusté** — le tableau périodique sort de la « brique comptage » de l'équation mère.

---

## 3. Combien de places dans chaque pièce ? (le calcul des capacités)

Chaque pièce de forme donnée a une capacité calculable :

```
CAPACITÉ d'une sous-couche = 2 × (2l + 1)

l = 0  →  s  →  2 × 1 = 2 places    (1 orientation × 2 spins)
l = 1  →  p  →  2 × 3 = 6 places    (3 orientations × 2 spins)
l = 2  →  d  →  2 × 5 = 10 places   (5 orientations × 2 spins)
l = 3  →  f  →  2 × 7 = 14 places   (7 orientations × 2 spins)
```

**Le « 2 » vient du spin** (l'électron tourne dans deux sens). **Le « 2l+1 » vient des orientations** (une pièce en forme d'haltère peut pointer dans 3 directions : gauche, droite, avant — une pièce en forme de trèfle dans 5, etc.).

Additionnons les étages :

```
Étage 1 : s        → 2 places            → période 1 = 2 éléments
Étage 2 : s + p    → 2 + 6 = 8 places    → période 2 = 8 éléments
Étage 3 : s + p    → 8 places            → période 3 = 8 éléments
Étage 4 : s+d+p    → 2+10+6 = 18 places  → période 4 = 18 éléments
Étage 5 : s+d+p    → 18 places           → période 5 = 18 éléments
Étage 6 : s+f+d+p  → 2+14+10+6 = 32      → période 6 = 32 éléments
Étage 7 : s+f+d+p  → 32 places           → période 7 = 32 éléments
```

**2 + 8 + 8 + 18 + 18 + 32 + 32 = 118.** Les tailles des lignes du tableau périodique sont **dérivées** — pas apprises par cœur.

---

## 4. La règle d'ascenseur : dans quel ordre remplit-on ? (Madelung)

Maintenant la question délicate : **dans quel ordre les électrons s'installent-ils ?**

L'électricien ne choisit pas — il suit la règle de **Madelung** : on remplit d'abord les pièces les moins chères en énergie, c'est-à-dire celles dont la somme **(étage + forme)** est la plus petite. À somme égale, on prend l'étage le plus bas.

```
ORDRE DE REMPLISSAGE (le fameux ordre de Madelung) :

1s → 2s → 2p → 3s → 3p → 4s → 3d → 4p → 5s → 4d → 5p → 6s → 4f → 5d → 6p → 7s → 5f → 6d → 7p

ou, avec les nombres (n+l, n) :

1s (1) → 2s (2) → 2p (3) → 3s (3) → 3p (4) → 4s (4) → 3d (5) → 4p (5) → 5s (5) → 4d (6) → 5p (6) → 6s (6) → 4f (7) → 5d (7) → 6p (7) → 7s (7) → 5f (8) → 6d (8) → 7p (8)
```

**L'image :** une file d'attente devant l'immeuble. Chaque nouvel électron prend la première pièce libre dans cet ordre. C'est tout.

**Le point amusant :** regardez le détour « 4s → 3d ». L'étage 4 se remplit **avant** que l'étage 3 ne soit fini ! C'est le célèbre « paradoxe » de Madelung — mais il découle simplement de la règle (n+l) : la pièce 4s coûte moins cher que la pièce 3d, donc l'électron passe au 4e étage avant de finir le 3e. Le tableau périodique a exactement cette forme **à cause de ce détour**.

---

## 5. Le remplissage : chaque électron, sa place

Le processus complet, résumé en 3 étapes :

```
ÉTAPE 1 — Les pièces : les sous-couches (n, l) avec leurs capacités
          (s=2, p=6, d=10, f=14) — des entiers, rien d'autre

ÉTAPE 2 — L'ordre : la file de Madelung (n+l, n) — le filtre d'énergie

ÉTAPE 3 — Le remplissage : Z = 1, 2, 3, ..., 118
          chaque nouvel électron → la première pièce libre
          → configuration, étage (période), colonne (groupe)
```

```
Exemples de remplissage :

Z=1  Hydrogène  : 1s¹              (1 électron au 1er étage, pièce s)
Z=2  Hélium     : 1s²              (pièce s pleine → étage 1 COMPLET)
Z=3  Lithium    : 2s¹              (le 3e électron monte au 2e étage)
Z=10 Néon       : 2s²2p⁶           (2e étage complet)
Z=18 Argon      : 3s²3p⁶           (3e étage complet)
Z=26 Fer        : 4s²3d⁶           (le détour Madelung : le 4s se remplit avant le 3d)
Z=118 Oganesson : 7s²5f¹⁴6d¹⁰7p⁶   (tout est plein — fin de la tour)
```

---

## 6. Les gaz nobles : les étages complets — les survivants

Voici le cœur de la lecture THU. Pourquoi l'hélium, le néon, l'argon… sont-ils si spéciaux (ils ne réagissent presque avec rien) ?

**Parce que ce sont les étages COMPLÈTEMENT remplis.** Une fois que la dernière pièce d'un étage est occupée (la sous-couche p complète, s²p⁶), l'immeuble est « fini » — les électrons n'ont envie de partager ni de recevoir quoi que ce soit.

La THU lit ça avec son principe d'élimination (A1) : les configurations qui survivent — qui sont **stables** — sont celles qui ne « cherchent » rien. Les gaz nobles sont les **survivants des couches fermées** :

```
GAZ NOBLES GÉNÉRÉS : Z = 2, 10, 18, 36, 54, 86, 118

Z=2   Hélium    (1s²)
Z=10  Néon      (2s²2p⁶)
Z=18  Argon     (3s²3p⁶)
Z=36  Krypton   (4s²3d¹⁰4p⁶)
Z=54  Xénon     (5s²4d¹⁰5p⁶)
Z=86  Radon     (6s²4f¹⁴5d¹⁰6p⁶)
Z=118 Oganesson (7s²5f¹⁴6d¹⁰7p⁶)
```

**7 sur 7 — vérifié par ordinateur.** Les gaz nobles ne sont pas une liste à mémoriser : ce sont les étages pleins. L'élimination les a laissés survivre.

---

## 7. La vérification — ce qui est exact, ce qui est honnête

### ✅ Ce qui est exact (vérifié par ordinateur, ré-exécuté le 9 août 2026)

| Vérification | Résultat | Statut |
|---|---|---|
| **V1 · Périodes** (les étages) | 118/118 éléments ont le bon étage | ✅ exact |
| **V3 · Gaz nobles** | Les 7 gaz nobles émergent des couches fermées | ✅ exact |
| **Positions** | Le bloc f se place après Ba/La, comme dans le tableau réel | ✅ exact |
| **Tailles des périodes** | 2, 8, 8, 18, 18, 32, 32 — dérivées des capacités | ✅ exact |

### ⚠️ Les 28 « écarts » de groupes — expliqués honnêtement

Le générateur attribue une **colonne (groupe)** à chaque élément à partir de ses électrons de valence. Sur 118, 90 correspondent à la convention réelle — et les 28 autres sont **exactement les lanthanides (14) et les actinides (14)**.

Ce n'est pas une erreur de placement : ces éléments sont **au bon étage** (période correcte). C'est une différence de **convention de numérotation** : la règle des électrons de valence dit « groupe 2 », la convention IUPAC les regroupe dans la « colonne 3 » parce qu'ils se ressemblent tous chimiquement.

```
Z=57 La → 64 Gd → 70 Yb : 14 lanthanides → convention groupe 3
Z=89 Ac → 96 Cm → 102 No : 14 actinides → convention groupe 3
```

**En clair :** la THU place correctement les 118 éléments dans leurs étages ; la seule différence porte sur la **numérotation des colonnes** des deux familles du bloc f — une convention, pas une propriété physique. C'est dit, mesuré, publié.

### ⚠️ Les configurations « anomales »

Quelques éléments (Cr, Cu, Mo, Ag, Au…) ne remplissent pas la file d'attente « naïvement » : un électron saute d'une pièce à moitié pleine vers une pièce vide pour obtenir une **stabilité plus grande** (couches à moitié ou entièrement remplies). La THU lit cela comme le **filtre de stabilité qui tranche** : les configurations qui survivent ne sont pas toujours les plus simples — mais les plus stables. L'élimination, à l'œuvre dans le tableau lui-même.

---

## 8. La prédiction : le bloc g — 18 éléments jamais vus

Si l'on prolonge la même règle au-delà de l'étage 7, la file de Madelung continue :

```
8s → 5g → 6f → 7d → 8p ...

La pièce g (l=4) a une capacité : 2 × (2×4 + 1) = 18 places
```

**Prédiction :** après Z=120 (étage 8 rempli en s), les électrons remplissent la pièce **5g** — un nouveau bloc de **18 éléments (Z = 121 à 138)** qui n'a jamais été observé.

```
BLOC g PRÉDIT : Z = 121 à 138 — 18 nouveaux éléments
(vérification : quand le tableau réel ne connaît pas encore ces éléments,
 la THU les annonce — c'est une prédiction falsifiable)
```

---

## 9. Ce que ça prouve — et ce que ça ne prouve pas (honnêteté)

### ✅ Ce que ce fait établit

1. La forme du tableau périodique (118 éléments, 7 périodes, 7 gaz nobles) est **dérivable** à partir de simples entiers et d'une règle de remplissage — pas une liste mémorisée
2. Les tailles des périodes (2, 8, 8, 18, 18, 32, 32) sortent des **capacités des sous-couches** — zéro paramètre ajusté
3. Les gaz nobles émergent naturellement comme **survivants des couches fermées** (A1)
4. La prédiction du bloc g (Z = 121-138) est **testable** : si les éléments 119-120 puis 121+ sont synthétisés, leur chimie dira si la règle tient

### ⚠️ Ce que ce fait n'établit PAS

1. La THU **n'explique pas pourquoi** les capacités sont 2, 6, 10, 14 — elle les prend de la mécanique quantique standard (les nombres quantiques). C'est la **forme** du tableau qui est dérivée, pas la mécanique quantique elle-même
2. La règle de Madelung est prise comme **donnée** — la THU ne la dérive pas de ses axiomes (frontière ouverte)
3. Les écarts de groupes (28 conventions lanthanides/actinides) et les configurations anomales (Cr, Cu…) sont **décrits et lus** par la théorie, pas prédits à l'avance
4. Le bloc g est une **prédiction** — elle doit attendre la synthèse des éléments

---

## 10. Vérifiez vous-même — 30 secondes

Sur n'importe quel ordinateur avec Python :

```bash
python generation_tableau_periodique.py
```

Le programme affiche notamment :

```
V1 · périodes générées = réelles : 118/118
V2 · groupes générés = réels : 90/118 (28 écarts)
V3 · gaz nobles générés : [2, 10, 18, 36, 54, 86, 118] → ✅
```

Et il affiche **la configuration de chaque élément** — vous pouvez vérifier élément par élément, Z=1 jusqu'à Z=118, que le remplissage suit bien la file d'attente. Ce n'est pas une promesse : c'est une commande.

---

## 11. En une phrase

> **Le tableau périodique n'est pas une liste : c'est un immeuble rempli selon une règle unique (la file de Madelung), dont les tailles d'étages sortent de simples entiers, dont les gaz nobles sont les étages pleins, et dont les 118 éléments sont les survivants du filtre de stabilité — avec 18 nouveaux étages supérieurs prédits (bloc g, Z = 121 à 138).**

---

*Théorie de l'Univers Harmonique — Alain Kotto — 9 août 2026*
*Ce document est libre de diffusion — reproduction autorisée avec mention de la source.*
