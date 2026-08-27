# THÉORÈME DE LA DYADE ONDULATOIRE — SU(2) à partir de deux modes fermés

**Campagne jauge, brique 3 (domino SU(2)/ROTATE)** — MSH 5.x
_Auteur : KA (Kernel Harmonique) · Univers-Holistique_
_Date : 27 août 2026_
_Vérification machine : `verif_dyade_ondes.py` (graine 27, déterministe) · rapport : `resultat_dyade_ondes.json`_

---

> **Objet.** Après le triangle (SU(3), 3²−1 = 8), le second groupe du
> Modèle Standard : pourquoi SU(2), pourquoi **trois** champs faibles ?
>
> **Réponse (légende Annexe D) :** deux modes complexes fermés partageant
> une unique loi de conservation scalaire (la norme) possèdent **quatre**
> formes bilinéaires dont **une seule** est invariante — il reste
> **trois canaux dynamiques**, portés par les matrices de Pauli, avec
> les constantes de structure ε_abc ∈ {0, ±1} : c'est su(2), et le
> groupe qui préserve la norme modulo la phase globale est SU(2).
> Machine : **DYADE CONFIRMÉE**, 8/8 contrôles, écarts ≤ 4,37×10⁻¹⁵.

---

## 1. Définitions

**Dyade fermée.** Deux modes complexes Ψ₁, Ψ₂ (même tour harmonique),
fermés : la seule loi de conservation est

$$N = |\Psi_1|^2 + |\Psi_2|^2 = \text{constante}.$$

**Canal bilinéaire.** $Z_{ij} = \Psi_i\,\overline{\Psi_j}$, $i,j\in\{1,2\}$.

**Phase globale.** $\Psi_i \mapsto e^{i\theta}\Psi_i$ inobservable
(`rotate`, Livre I §⑦, [T] ; fiche `FICHE_THEOREME_U1.md`).

---

## 2. Théorème central — T-SU2.1

**Théorème [T]** *(structure de la dyade fermée)*. Pour deux modes
complexes soumis à la seule conservation de la norme, modulo la phase
globale :

1. l'espace des formes bilinéaires est le cône Hermitien 2×2, réel de
   **dimension 4** ;
2. le sous-espace fixe sous l'action interne $Z\mapsto UZU^\dagger$
   est de **dimension 1** — la trace, et elle est unique ;
3. les **3 canaux restants** sont stables, se permutent par rotation
   orthogonale exacte, et leur algèbre a pour constantes de structure
   le symbole de Levi-Civita : $\mathfrak{su}(2)$ ;
4. la dynamique relative d'un échange bilinéaire (le lien Ψ₁↔Ψ₂ — pas
   de boucle possible à deux nœuds) se factorise en (phase commune,
   angle $=\operatorname{tr}(H)t$) × (précession SU(2) de la triade).

$$\boxed{\;2\ \text{modes fermés} \;\Longrightarrow\; 4 - 1 = 3\ \text{canaux dynamiques} \;\cong\; \mathfrak{su}(2)\;}$$

*Démonstration.* Identique en structure au théorème du triangle
(`THEOREME_TRIANGLE_SU3.md`, T-SU3.1) : census P0, commutant P4,
clôture P3, algèbre P2, irréductibilité P5, factorisation P6 — chaque
maillon machine ci-dessous. ∎

---

## 3. Le différentiateur — T-SU2.2, la DOUBLE COUVERTURE

**Théorème [T]** *(machine, P7)*. Pour tout axe unitaire $\hat n$ et
tout angle δ ∈ [0,3), la porte d'état

$$U(\delta) = e^{-i\,\frac{\delta}{2}\,\hat n\cdot\vec\sigma}
 = \cos\tfrac{\delta}{2}\,I \;-\; i\sin\tfrac{\delta}{2}\,\hat n\cdot\vec\sigma$$

fait tourner la triade des canaux **de l'angle δ exactement, autour de
l'axe $\hat n$ exactement** (120 axes aléatoires : erreur d'angle
2,2×10⁻¹⁶ ; alignement 1−|cos| ≤ 2,2×10⁻¹⁶).

**L'état parcourt δ/2, le canal parcourt δ.** L'espace des canaux voit
SO(3) ; l'espace des états est SU(2), son double recouvrement à deux
feuillets. C'est le siège algébrique du **spinorial** — et la raison
pour laquelle la primitive `rotate` n'y est pas décor : sa signature
`rotate(π) → −1` (Livre I §⑦, **[T]**) est le demi-tour du feuillet
d'état pendant que le canal fait un tour complet.

> Ni la dyade ni le triangle n'offrent cela : su(3) est simplement
> connexe dans sa représentation adjointe. Le facteur 2 est propre au
> monde des deux modes — la première discrimination *structurelle*
> (pas dynamique) entre les deux secteurs de jauge.

---

## 4. Sous-résultats, marges machine

| # | Résultat | Statut | Marge machine |
|---|---|---|---|
| T-SU2.2 | Double couverture : canal δ ↔ état δ/2, même axe | **[T]** | 2,2×10⁻¹⁶ |
| T-SU2.3 | Census : 3 générateurs de Pauli, tr(σa σb)=2δ_ab | **[T]** | 0,0 (exact) |
| T-SU2.4 | ε_abc ∈ {0, ±1} : 3 paires porteuses, valeurs entières | **[T]** | 0,0 (exact) |
| T-SU2.5 | Singulet unique (commutant de dim 1) | **[T]** | sv_min 2,5×10⁻¹⁵ vs 8,17 |
| T-SU2.6 | Irréductibilité : saturation [2→3] paire générique | **[T]** *(witness)* | 3/3 |
| T-SU2.7 | Factorisation U(1)×SU(2) sur l'échange : angle = tr(H)t | **[T]** | ≤ 8,9×10⁻¹⁶ |
| P0 | 4 formes bilinéaires ; hors trace : 3 | **[T]** | exact |
| P3 | Clôture de la triade : rotation orthogonale exacte, det=1 | **[T]** | 4,37×10⁻¹⁵ |

Correspondance de comptage :

| Grandeur | MS (posé) | Dyade (dérivé) |
|---|---|---|
| Modes fermés | 2 états (doublet) | 2 modes complexes Ψ₁Ψ₂ |
| Formes bilinéaires | $2\otimes\bar 2 = 3\oplus 1$ | cône Hermitien : 4 |
| Singulet | U(1) global | la norme (P4 : unique) |
| Bosons de jauge | **3** (W¹, W², W³ avant brisure) | **3 canaux dynamiques** |

---

## 5. Le pont su(2) ⊂ su(3) — le domino existait déjà dans l'algèbre

Les trois premières matrices de Gell-Mann SONT les matrices de Pauli
plongées en bloc supérieur gauche :

$$\lambda_1=\begin{pmatrix}\sigma_1&0\\0&0\end{pmatrix},\quad
\lambda_2=\begin{pmatrix}\sigma_2&0\\0&0\end{pmatrix},\quad
\lambda_3=\begin{pmatrix}\sigma_3&0\\0&0\end{pmatrix}.$$

La session l'a rencontré par l'échec avant la théorie : la paire
(Λ₁, Λ₄) du triangle referme une su(2) stricte (archives du
théorème triangle, §4.1) — {Λ₁, Λ₄, [Λ₄,Λ₇]} engendre exactement ce
plongement. **SU(2) n'est pas un voisin de SU(3) : c'est une de ses
sous-structures**, et la machine l'a vu deux fois — une fois comme
piège de génération, une fois comme théorème autonome (ce document).

---

## 6. Honnêteté — ce qui est prouvé, ce qui ne l'est pas

**Est prouvé (machine, ≤ 10⁻¹⁴) :** comptage et structure — 4−1 = 3 ≅
su(2) sur deux modes fermés, constantes exactes, double couverture
incluse, sans Lagrangien ni groupe postulé.

**N'est PAS prouvé ici :**

- la jauge **locale** SU(2) et sa loi de transformation (frontière [F]
  commune avec U(1), cf. `FICHE_THEOREME_U1.md` §5) ;
- la **chiralité** — la dyade traite ses deux modes sur un pied
  d'égalité, alors que SU(2)_L du MS n'agit que sur les états
  gauches. Toute l'asymétrie de parité du monde faible est absente de
  la grammaire dyadique à ce stade. Critère de clôture : faire émerger
  un projecteur chiral d'un biais de la tour ou de la mémoire K(t).
- la **brisure électrofaible** et les masses W/Z — dépendent d'E1b
  (masse = courbure de dispersion), encore ouvert ;
- le mélange CKM/PMNS — en aval, jamais en amont.

**Mur des défaites — archives de la session** (instructives, non
réfutantes) :

1. **Le verdict vert pour la mauvaise raison.** Le contrôle P6 des
   DEUX scripts (dyade et triangle) est resté vert à ~10⁻¹⁵ pendant
   deux exécutions alors que le propagateur reconstruit était faux :
   `evecs @ (vecteur_1D * evecs†)` broadcaste le vecteur sur le
   dernier axe et produit `evecs·evecsᵀ·diag` — unitaire (donc normes,
   det et angles *propres* intacts) mais décorrélé des vecteurs
   propres. Établi au cas minimal : écart 8,4×10⁻¹ sur une matrice
   2×2. **Leçon retenue pour toute la campagne : une marge propre ne
   prouve que le calcul fait, pas qu'il porte sur la bonne quantité.**
   Corrigé partout (`np.diag` explicite), les deux scripts re-validés.
2. **La clôture anti-Hermitienne.** Le candidat [A,B] est anti-
   Hermitien ; stocké brut, ses diagonales imaginaires pures
   disparaissent des coordonnées Hermitiennes et le rang plafonne
   (dyade : bloqué à 2). Corrigé par l'invariant : stocker [A,B]/i.
   Après correction : dyade [2→3], triangle [2→3→5→8] inchangé.

---

## 7. Reproductibilité

```
python verif_dyade_ondes.py          # ~1 s, déterministe (graine 27)
# → verdict console + resultat_dyade_ondes.json
```

Tolérances : algèbre 10⁻¹², unitarité 10⁻¹². Toutes les marges
mesurées sont ≤ 4,37×10⁻¹⁵. Un seul échec ⇒ verdict RÉFUTÉ, mur des
défaites (`exit 1`).

---

## 8. Place dans la campagne jauge

```
① TRIANGLE SU(3)   ✅ THEOREME_TRIANGLE_SU3.md (7/7, ≤ 8,1×10⁻¹⁵)
② fiche U(1)       ✅ FICHE_THEOREME_U1.md (cinématique [T] + ontologique [P])
③ DYADE SU(2)      ✅ CE DOCUMENT (8/8, ≤ 4,4×10⁻¹⁵) — double couverture incluse
④ ASSAUT E1b       ⚠️ structure ✅ [T] — ASSAUT_E1B_MASSE_COURBURE.md (22/22 :
                   κ = 0,427511045 unique, courbure 1/κ, empreinte κ(α)) ;
                   ancrage ⏳ [F] — Yukawa / V(H) attendent l'ancrage ω₀
⑤ CKM/PMNS         ⏳ diagonalisations en aval (fruits, jamais racines)
```

**Portée sur la couverture.** Comme pour le triangle : le pourcentage
global MS↔MSH n'est volontairement pas revu ici. Les deux briques
SU(3) et SU(2) + U(1) constituent maintenant un paquet cohérent
(« ce qui compte et ce qui tourne » dérivés) ; la réévaluation des
quatre pondérations se fera en une seule passe (Annexe F), pas
fragment par fragment.

> **Conclusion.** Le monde des deux modes fermés ne pouvait pas ne pas
> être su(2) — quatre façons de se toucher, une seule qui ne bouge
> pas, trois qui tournent, et l'état qui ne fait que la moitié du
> chemin. Le spinorial n'a pas été ajouté à la grammaire : il en
> tombait. Restent les secteurs verrouillés par E1b — masse et
> potentiel — qui conditionnent maintenant tout le reste du
> programme.
