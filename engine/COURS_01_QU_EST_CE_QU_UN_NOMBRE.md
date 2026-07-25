# 🌊 COURS N°1 — Qu'est-ce qu'un nombre ?

**Mathématiques Ondulatoires — Leçon inaugurale**
**Niveau : Débutant (12-16 ans)**
**Prérequis : Aucun. Juste savoir observer.**

---

> *« Avant ce cours, tu pensais que les nombres étaient des symboles sur
> du papier. Après ce cours, tu sauras qu'ils sont des ondes qui vibrent.
> Et que tout vibre. Y compris toi. »*

---

## 1. L'expérience qui change tout

Prends une corde. Attache une extrémité à un mur. Secoue l'autre extrémité.

Tu vois une **vague** qui se propage. Cette vague a trois propriétés :

1. **Sa hauteur** — jusqu'où elle monte et descend. C'est l'**amplitude**.
2. **Sa position** — où elle est sur la corde à un instant donné. C'est la **phase**.
3. **Sa vitesse** — combien de vagues passent par seconde. C'est la **fréquence**.

> **Règle n°1 : Tout dans l'univers a une amplitude, une phase, et une fréquence.
> Même les nombres. Même toi. Même cette phrase.**

Maintenant, prenons deux vagues sur la même corde. Que se passe-t-il ?

- Si elles arrivent **en même temps** (phases alignées) → elles s'additionnent. La vague est plus haute.
- Si elles arrivent **décalées** (phases opposées) → elles s'annulent. La corde ne bouge plus.

C'est l'**interférence**. Et c'est le seul calcul que l'univers sait faire.

> **Règle n°2 : L'univers ne calcule pas avec des + et des −.
> Il superpose des ondes. L'addition EST une interférence.**

---

## 2. Le nombre 5 n'existe pas

Arrête-toi un instant. Regarde le symbole : **5**.

Tu as appris que c'est un « nombre ». Que ça vaut « cinq ». Que $2+3=5$,
que $10/2=5$, que $\sqrt{25}=5$.

Mais **5** n'est qu'un symbole. Un gribouillis d'encre sur du papier.
Ce n'est pas ça, la réalité de « cinq ».

La réalité de « cinq », c'est une **onde**. Une vibration qui a une
certaine amplitude (5 unités) et une certaine phase (que nous allons
apprendre à lire).

```
Le symbole 5           La réalité : 5·e^{iφ}
    │                       │
    ▼                       ▼
  ┌─────┐             ┌──────────────────┐
  │  5  │             │  Amplitude = 5   │
  │     │             │  Phase     = ?    │
  └─────┘             │  Fréquence = ?    │
  Un dessin            └──────────────────┘
                       Une vibration réelle
```

> **Règle n°3 : Un « nombre » n'est pas un symbole. C'est une onde
> complexe $\psi = A \cdot e^{i\varphi}$. L'amplitude $A$ dit « combien ».
> La phase $\varphi$ dit « quand/où ». La fréquence dit « à quel rythme ».**

### Exercice 1.1

Ferme les yeux. Imagine une vague. Elle a une amplitude de 5 et une phase de 0°.
Maintenant, imagine la même vague mais avec une phase de 180°.
Quelle est la différence ?

*(Réponse : la première commence par monter. La seconde commence par descendre.
Le symbole « 5 » ne capture pas cette différence. L'onde, si.)*

---

## 3. L'onde s'écrit $\psi = A \cdot e^{i\varphi}$

C'est la **seule formule** dont tu auras besoin pour tout ce cours.
Apprends-la par cœur. Pas comme une formule — comme une vérité.

$$\boxed{\psi = A \cdot e^{i\varphi}}$$

- **$\psi$** (prononce « psi ») : c'est le nom de l'onde. Comme $x$ est le nom d'une inconnue.
- **$A$** : l'amplitude. Un nombre réel positif. Combien d'énergie dans la vague.
- **$e^{i\varphi}$** : la phase. C'est la partie qui dit « où et quand ».
- **$\varphi$** : l'angle de phase, en radians (0 à $2\pi$).

### Pourquoi $e^{i\varphi}$ ?

Parce que c'est la façon la plus pure de représenter une rotation.
$e^{i\varphi}$ est un point sur le cercle unité. Quand $\varphi$ varie,
le point tourne. C'est une **horloge**.

```
     φ = 90° (π/2)
         ↑
         │ i
    ─────┼─────→ φ = 0° (1)
         │
         ↓
     φ = 270° (-i)
```

> **Règle n°4 : La phase $\varphi$ est une horloge. Chaque onde a sa propre
> horloge interne. Quand deux horloges sont synchronisées (même $\varphi$),
> les ondes sont « en phase ». Quand elles sont opposées, elles s'annulent.**

### Exercice 1.2

Combien vaut $\psi$ si $A = 1$ et $\varphi = 0$ ?
Combien vaut $\psi$ si $A = 1$ et $\varphi = \pi$ ?

*(Réponse : $1 \cdot e^{i·0} = 1$ et $1 \cdot e^{i\pi} = -1$. La célèbre
identité d'Euler $e^{i\pi} + 1 = 0$ n'est rien d'autre que :
« une onde de phase $\pi$ ajoutée à une onde de phase $0$ donne zéro ».
C'est de l'interférence, pas des mathématiques.)*

---

## 4. Additionner des ondes, c'est additionner des réalités

Quand tu additionnes $2 + 3 = 5$, tu fais en réalité :

$$\psi_2 \oplus \psi_3 = \psi_{(2+3)}$$

Mais attention : $\oplus$ n'est pas $+$ ! L'addition classique $+$ suppose
que les phases sont alignées (même $\varphi$). L'addition ondulatoire $\oplus$
tient compte DES phases :

$$\psi_2 = 2 \cdot e^{i\varphi_2}\quad \psi_3 = 3 \cdot e^{i\varphi_3}$$

Si $\varphi_2 = \varphi_3$ → $\psi_2 \oplus \psi_3 = 5 \cdot e^{i\varphi}$ (comme $2+3=5$)
Si $\varphi_2 = \varphi_3 + \pi$ → $\psi_2 \oplus \psi_3 = 1 \cdot e^{i\varphi_3}$ (interférence destructive !)

> **Règle n°5 : $2+3=5$ n'est vrai QUE si les phases sont alignées.
> Si $2$ et $3$ sont déphasés de 180°, leur somme n'est pas $5$ — c'est $1$.
> L'arithmétique classique suppose implicitement que tout est en phase.**

### Exercice 1.3

Calcule $\psi_2 \oplus \psi_3$ quand $\varphi_2 = 0$ et $\varphi_3 = \pi/2$ (90°).

*(Aide : $2 \cdot e^{i0} = 2$, $3 \cdot e^{i\pi/2} = 3i$. La somme est $2 + 3i$.
L'amplitude résultante est $\sqrt{2^2 + 3^2} = \sqrt{13} \approx 3.6$,
pas $5$ !)*

---

## 5. La table de multiplication des ondes

Tu connais la table de multiplication :

$$2 \times 3 = 6$$

Mais qu'est-ce que ça veut dire, vraiment ?

Multiplier deux ondes, c'est multiplier leurs amplitudes ET additionner leurs phases :

$$\psi_2 \otimes \psi_3 = (2 \cdot 3) \cdot e^{i(\varphi_2 + \varphi_3)} = 6 \cdot e^{i(\varphi_2 + \varphi_3)}$$

> **Règle n°6 : Multiplier, c'est amplifier ET tourner.**
> $2 \times 3 = 6$ ne capture que l'amplitude. La phase aussi a changé :
> elle a tourné de $\varphi_2 + \varphi_3$.

### Exercice 1.4

Si $\psi_2 = 2 \cdot e^{i\pi/4}$ (45°) et $\psi_3 = 3 \cdot e^{i\pi/4}$,
que vaut $\psi_2 \otimes \psi_3$ ?

*(Réponse : $6 \cdot e^{i\pi/2}$. L'amplitude a doublé-triplé. La phase a
tourné de 45°+45° = 90°. Le résultat pointe vers le haut !)*

---

## 6. Le zéro n'est pas « rien »

En mathématiques classiques, $0$ signifie « rien ». Mais en réalité physique,
le **vrai zéro** est une onde d'amplitude nulle :

$$\psi_0 = 0 \cdot e^{i\varphi}$$

Son amplitude est nulle, donc elle ne transporte aucune énergie. MAIS sa
phase $\varphi$ peut être n'importe quoi — et c'est important !

Deux ondes identiques mais déphasées de $\pi$ (180°) s'annulent. Leur
somme n'est pas « zéro » — c'est le **silence**. Et le silence n'est pas
l'absence de son. C'est l'interférence parfaite de deux sons opposés.

> **Règle n°7 : Le zéro physique est une interférence destructive.
> Ce n'est pas « rien » — c'est « deux choses qui s'annulent parfaitement ».**

---

## 7. Récapitulatif des 7 règles

| Règle | Énoncé |
|---|---|
| **1** | Tout a une amplitude, une phase, une fréquence |
| **2** | L'univers superpose des ondes. L'addition EST une interférence |
| **3** | Un nombre n'est pas un symbole. C'est $\psi = A \cdot e^{i\varphi}$ |
| **4** | La phase $\varphi$ est une horloge interne |
| **5** | $2+3=5$ n'est vrai que si les phases sont alignées |
| **6** | Multiplier = amplifier l'amplitude ET additionner les phases |
| **7** | Le zéro n'est pas « rien » — c'est l'interférence destructive |

---

## 8. Devoir à la maison

### Question 1 — L'onde de ton âge

Tu as 12 ans (ou 15, ou 45 — peu importe). Écris ton âge sous forme d'onde :

$$\psi_{\text{mon âge}} = \text{?} \cdot e^{i·\text{?}}$$

Choisis une amplitude (ton âge) et une phase (ce que tu veux — l'angle
qui te semble juste pour représenter où tu en es dans ta vie).

### Question 2 — L'interférence des contraires

Imagine deux ondes : $\psi_{\text{joie}} = 10 \cdot e^{i·0}$ et
$\psi_{\text{tristesse}} = 10 \cdot e^{i\pi}$. Calcule leur somme.
Que remarques-tu ? Qu'est-ce que ça t'apprend sur les émotions ?

### Question 3 — La corde de l'univers

Trouve un objet chez toi qui vibre (une corde de guitare, un élastique,
l'eau dans un verre). Observe les vagues. Peux-tu identifier l'amplitude ?
La fréquence ? La phase ? Pourquoi la vague finit-elle par s'arrêter ?

---

## 9. Pour la prochaine fois

Nous apprendrons à **interférer** — c'est-à-dire à mesurer à quel point
deux ondes sont « d'accord ». C'est la base de tout : la logique,
l'intelligence, et même l'amour.

> *« La physique a mis 3000 ans pour comprendre que la lumière est une onde.
> Les mathématiques viennent de le découvrir pour les nombres.
> Tu fais partie de la première génération qui apprend ça dès le début. »*

---

**Cours n°1 — Mathématiques Ondulatoires**
**Prochain cours : L'interférence, ou comment deux idées s'additionnent**
