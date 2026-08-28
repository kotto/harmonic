# FICHE THÉORÈME — U(1) : LA LIBERTÉ RÉSIDUELLE DE LA PROJECTION

**Campagne jauge, brique 2** — MSH 5.x
_Auteur : KA (Kernel Harmonique) · Univers-Holistique_
_Date : 27 août 2026_

---

> **Objet.** Le Modèle Standard pose $SU(3)\times SU(2)\times U(1)$.
> La brique la plus petite du groupe est U(1) — le cercle des phases.
> Question falsifiable : **d'où vient le cercle ?**
>
> **Réponse de la THU :** il n'est pas postulé. Il apparaît **deux fois,
> par deux chemins indépendants** — une fois comme droit élémentaire de
> la grammaire (cinématique, **[T]**), une fois comme échec d'unicité de
> la projection ontologique (théorème du Maillon 3, **[P]**). Les deux
> jambes se joignent dans le découplage U(1)×SU(3) prouvé machine
> (`verif_triangle_ondes.py`, contrôle P6).

---

## 1. Vue d'ensemble : deux jambes

| Jambe | Contenu | Sources | Statut |
|---|---|---|---|
| **Cinématique** | rotation de phase = droit élémentaire du langage ; 512 générateurs indépendants sur ℂ⁵¹² | Livre I §⑦, I.6, I.8 | **[T]** |
| **Ontologique** | l'unicité de la projection ne tient qu'*modulo* $e^{i\theta}$ ; cette liberté **est** la jauge | Maillon 3 (§6, §7) | **[P]** |

---

## 2. Première jambe — cinématique (statut [T])

Trois faits structurels du Livre I, tous vérifiés machine :

1. **`rotate`** (primitive ⑦) : $\mathrm{rotate}(\psi,\theta)=\psi\cdot e^{i\theta}$
   — évolution unitaire d'un état stationnaire. Vérification :
   rotation de π → résonance −1,000 (**[T]**).
2. **Conservation de la norme** : `rotate` préserve $\|\psi\|$ (I.6, **[T]**)
   — le cercle agit sans coût d'information.
3. **`phase_shift` vectoriel** = **512 générateurs U(1) indépendants**
   (I.8, **[T]** — structurel).

Le point 3 est le plus important et le plus sobrement énoncé : sur
l'espace d'états ℂ⁵¹², composer les rotations de phase composante par
composante produit un **tore maximal**

$$T^{512} \;=\; U(1)^{512} \;\subset\; U(\mathbb{C}^{512}).$$

La grammaire contient donc, *de droit*, un stock de symétries de cercle
— chaque mode porte le sien. C'est le germe interne dont hériteront les
structures de jauge ; le théorème du triangle
(`THEOREME_TRIANGLE_SU3.md`) montre précisément comment l'action
commune se sépare en un U(1) global facteurisant hors de l'octet
SU(3).

---

## 3. Seconde jambe — ontologique : l'échec d'unicité (statut [P])

**Théorème d'unicité de la projection (Maillon 3, §6).** Soit Π une
application linéaire compatible avec les cinq conditions naturelles :

**(U1)** compatibilité avec le seuil doré · **(U2)** isométrie de
Parseval · **(U3)** stationnarité (commutation aux translations) ·
**(U4)** causalité/complète monotonie · **(U5)** stabilité dorée
$c^2+c=1$.

Alors Π est unique — **à une phase globale près** :

$$\psi(x,t)=\frac{1}{\sqrt{2\pi}}\int \hat K(x-x')\,\phi_O(x',t)\,dx',
\qquad \hat K(\omega)=\frac{\phi}{(i\omega)^{1/\phi}+\phi}
\quad\text{modulo } \psi\mapsto e^{i\theta}\psi.$$

La marche décisive est l'étape 5 : (U2) fixe le **module** du masque ;
la **phase relative des modes reste libre** — et aucune autre liberté
ne survit. Chaque ingrédient isolé est un théorème classique **[T]**
(Eckart-Young ; unicité de $c=1/\phi$ ; multiplicateur de Fourier ;
Mittag-Leffler) ; leur assemblage en tant qu'axiomatique (U1)-(U5)
garde le statut **[P]**.

**Identification (Maillon 3, §7).** La mécanique quantique possède
exactement la même symétrie : la phase globale de ψ n'est pas
observable.

$$\text{jauge U(1) de la QM} \;=\; \text{liberté résiduelle de l'unicité de la projection}$$

Là où la QM *postule* la liberté de phase, la THU la *dérive* comme
résidu. Et l'argument inverse ferme la porte : exiger l'unicité
absolue imposerait une phase absolue — ce qui violerait la
stationnarité (U3), car aucune phase absolue n'est stationnaire.
Statut : **[P]** (coïncidence structurelle, à publier).

---

## 4. Où le cercle devient effectif

| Lieu | Ce qui est montré | Statut |
|---|---|---|
| Découplage machine (triangle, P6) | sur une boucle à 3 modes, la dynamique se factorise exactement en (phase commune $=\mathrm{tr}(H)t$) × (rotation d'octet) ; marges ≤ 8,9×10⁻¹⁶ | **[T]** |
| Couplage EM | $\alpha^{-1}_{MSH}=137{,}036031356$ (5 facteurs) — **ancre de compression** : l'assaut grammaire statique du 27/08 soir a donné **0/218 lectures de verdict** (`DEPOT_ALPHA_GRAMMAIRE_V0.md`, exit 1) ; l'ancre tient à 3,1×10⁻¹² (C4), le mécanisme de dérivation statique est tombé | **[F] statique / ancre** — le verrou L3 passe au jaugage (`DEPOT_JAUGAGE_V0.md`) et à la grammaire dynamique |
| Photon | harmonique de l'interférence électron-proton | **[P]** (pont) |

> **Correction du 28/08/2026.** La ligne « Couplage EM **[T]** — verrou résiduel L3 daté » ci-dessus datait du 27/08 matin, *avant* l'exécution de l'assaut grammaire (`verif_alpha_grammaire.py`, 8/8 contrôles, 0/218, exit 1). La 5-facteurs est reclassée **coïncidence de compression** : ancre maintenue, dérivation statique tombée. Le verrou résiduel L3 est reporté sur le jaugage local — trou cartographié le 28/08 : localisation (rephasage modulé), force (facteur 1,8324, candidat 1/D₂ à 1,0×10⁻³), dynamique du compensateur, dictionnaire μ↔ω.

---

## 5. Honnêteté — frontières explicites

1. **Global ≠ local.** Les jambes 2 et 3 établissent le U(1) *global*
   (phase commune non observable). La structure de jauge *locale* de
   QED ($A_\mu$, loi de transformation locale) n'est pas encore
   dérivée. C'est une frontière ouverte, non une brèche silencieuse :
   **[F]** — critère de clôture : dériver la liberté locale
   $\psi\mapsto e^{i\alpha(x)}\psi$ et la contrepartie de champ
   nécessaire à sa covariance, depuis l'invariance du noyau $\hat K$
   sous rephasage modulé.
2. La jambe ontologique repose sur les axiomes (U1)-(U5) : ils sont
   *naturels*, pas démontrés en bloc — d'où [P], jamais promus sans
   nouvelle preuve.
3. Cette fiche ne s'étend pas à U(1)$_Y$ (hypercharge) ni à son
   mélange avec SU(2)$_L$ — hors périmètre.

---

## 6. Inventaire des statuts (légende Annexe D)

| Résultat | Statut |
|---|---|
| `rotate` = évolution unitaire U(1), préserve la norme | **[T]** |
| `phase_shift` vectoriel = tore maximal $T^{512}\subset U(\mathbb{C}^{512})$ | **[T]** — structurel |
| Unicité de la projection modulo $e^{i\theta}$ | **[P]** (assemblage de [T]) |
| Liberté résiduelle = jauge U(1) de la QM | **[P]** |
| Facteurisation U(1)×SU(3) du triangle | **[T]** — machine (P6) |
| Jauge locale $\alpha(x)$ et $A_\mu$ | **[F]** — critère §5.1 |

---

## 7. Reproductibilité et renvois

- Maillon 3 complet : `thu/documents/MAILLON3_PROJECTION.md`
  (théorème §6, identification §7, statuts §9).
- Grammaire : `thu/documents/MSH_LIVRE_FORMALISME_HARMONIQUE.md`,
  Livre I (primitives ⑦, lignes I.6/I.8).
- Machine partagée : `python verif_triangle_ondes.py` et
  `python verif_dyade_ondes.py` (graine 27) — le contrôle P6 de chacun
  démontre la factorisation (phase commune U(1)) × (octet SU(3) /
  triade SU(2)).
- Compagnons : `THEOREME_TRIANGLE_SU3.md` (brique SU(3)) ·
  `THEOREME_DYADE_SU2.md` (brique SU(2), double couverture incluse).

> **Conclusion.** U(1) n'a jamais eu besoin d'être postulé : il est à
> la fois le droit de rotation du langage et ce qui *reste* quand la
> projection fait tout le reste juste. La campagne jauge possède donc
> sa plus petite brique en propre — reste SU(2), et le domino
> su(2)⊂su(3) observé au passage dans l'algèbre du triangle.
