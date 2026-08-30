# DEPOT KMS × D^(1/φ) THU V0 — Brancher l'opérateur sur la phase du vide

**Question testée :** l'opérateur D^(1/φ) branché sur la **phase du vide** (cercle KMS à T_U = a/2π) peut-il fournir le pont thermodynamique que le noyau ABC ne peut pas porter ? (piste réorientée après `DEPOT_JACOBSON_THU_V0.md` : le noyau K est **sans échelle**, donc le branchement ne passe pas par une échelle de temps — il doit passer par la phase.)
**Méthode :** chaque nombre déposé est calculé par machine (`verif_kms_dphi_thu_v0.py`, leçon FORCE V1.2).
**Sortie :** exit **0** — 7/7 contrôles conformes aux signatures attendues (`resultat_kms_dphi_thu_v0.json`).

---

## 1. LES RÉCLAMATIONS TESTÉES

| ID | Réclamation | Signature attendue | Résultat machine |
|----|-------------|--------------------|------------------|
| C1 | La périodicité KMS (τ → τ + iβ, β = 2π/a) est **géométrique** : portée par la trajectoire accélérée, absente du vide inertiel ; la période est β **exactement** (pas β/2) | accéléré < 1e-9 ; inertiel ≫ tol | ✅ KMS rel. **1.14e-15** ; inertiel rel. **1.130** ; demi-période : \|G(τ+iβ/2)/G(τ)\| = **0.2136** ≠ 1 |
| C2 | Balance détaillée du détecteur à deux niveaux : Ḟ(ω)/Ḟ(−ω) = e^(−βω) — bain de Planck à T_U = a/2π | < 1e-12 | ✅ **0.00e+00** (bit-exact) |
| C3 | Loi T·R = ħc/(2πk_B) = T_Pl·l_Pl/(2π) — **invariant universel**, trous noirs ET Rindler | < 1e-12 | ✅ **2.22e-16** ; T·R = **3.6445e-04 K·m** ; écart Planck **0.0e+00** |
| C4 | Transparence de D^α : λ(ω) = ω^α·e^{iπα/2} — gain **sans échelle**, déphasage **uniforme**, KMS préservé ∀α ∈ {0.5, 1/φ, 0.9} | loi/phase exactes ; périodicité < 1e-9 | ✅ loi **1.1e-16** ; phase **0.0e+00** ; KMS **9.1e-15** → **α = 1/φ NON sélectionné par Unruh** (consigné) |
| C5 | Aucun β ne rend le spectre fractionnaire ω^{2α} planckien ni boltzmannien (fit section d'or, ancré à ω = 1) | les deux erreurs L2 > 0.10 | ✅ Planck **3.768** ; Boltzmann **0.949** (β* = 0.018) — pont spectral **RÉFUTÉ** |
| C6 | Signature de phase de la mémoire : Δφ_mem = πα/2 = π/(2φ), **uniforme sur tous les modes** ; distincte de l'angle d'or | = π/(2φ) ; écart vs φ² > 0.05 | ✅ **0.970806 rad = 55.6231°** (= 90/φ degrés) ; ratio angle d'or/Δφ = **2.4721** ≠ φ² = 2.6180 (écart 5.6 %) |
| C7 | Le facteur de Boltzmann **EST une phase** : e^{iω·iβ} = e^{−βω} bit-exact ; poids mémoire (ω^α) et poids thermique (e^{−βω}) se **multiplient** sans se mélanger | 0.00e+00 ; ≤ 1e-15 | ✅ **0.0e+00** ; **1.1e-16** (1 ulp) |

---

## 2. VERDICT : `KMS_DPHI_V0_CONFORME_PONT_PHASE_ORDRE_NON_SELECTIONNE`

### 2.1 Ce qui est EXACT et machine-vérifié

1. **Le caractère thermique du vide est géométrique** (C1). Le même vide de Minkowski est périodique en temps imaginaire pour l'observateur accéléré (rel. 1.14e-15) et ne l'est PAS pour l'inertiel (rel. 1.130, cinq ordres au-dessus de la tolérance). Le contre-contrôle de la demi-période (0.2136 ≠ 1) ferme la porte à β/2 : la période KMS est **β = 2π/a exactement**.
2. **La balance détaillée est bit-exacte** (C2, 0.00e+00) : le détecteur à deux niveaux voit Ḟ(ω)/Ḟ(−ω) = e^(−βω) — un bain de Planck à T_U = a/2π. C'est la forme thermique complète, pas une approximation.
3. **T·R est un invariant universel** (C3, 2.22e-16) : T·R = ħc/(2πk_B) = 3.6445e-04 K·m = T_Pl·l_Pl/(2π), identique pour trois trous noirs (r = 2 r_s) et trois points de Rindler. **La température EST la courbure du couplage** — c'est la quantité que la THU doit réconcilier avec sa constante de couplage D^{1/φ}.
4. **Le facteur de Boltzmann est une phase** (C7, bit-exact 0.00e+00) : e^{iω·iβ} = e^{−βω}. La thermicité ne demande **aucune dynamique nouvelle** — elle est la phase Φ₂ = ∫k_μdx^μ évaluée sur le cercle imaginaire τ = iβ. Et les deux poids **se multiplient sans se mélanger** (1 ulp) : gain mémoire ω^α × facteur thermique e^{−βω}, pour TOUT α.

### 2.2 Ce qui est RÉFUTÉ (consigné)

5. **Le pont spectral est réfuté** (C5). Aucun choix de β ne rend ω^{2α} planckien (erreur L2 min 3.768) ni boltzmannien (0.949) — les deux restent deux ordres de grandeur au-dessus du seuil de 0.10. Même verdict structurel que JACOBSON V0, cette fois **côté opérateur** : D^(1/φ) ne fabrique pas de thermicité, il préserve celle qui existe.
6. **La numérologie de l'angle d'or est réfutée** (C6) : angle d'or / Δφ_mem = 2.4721, pas φ² = 2.6180 (écart 5.6 %). La signature de phase de la mémoire est π/(2φ) — elle n'a pas de lien géométrique avec l'angle d'or 2π/φ².

### 2.3 Ce qui est CONSIGNÉ (non-sélection — résultat négatif structurant)

7. **α = 1/φ n'est pas sélectionné par Unruh/KMS** (C4). L'opérateur D^α est transparent pour tout α : gain ω^α sans échelle, déphasage uniforme πα/2 (identique pour tous les modes — c'est précisément pourquoi la balance détaillée de C2 survit à D^α), KMS préservé à 9.1e-15 pour α ∈ {0.5, 1/φ, 0.9}. La thermodynamique des horizons **ne peut pas dériver** l'ordre 1/φ : ce choix reste **axiomatique** (irrationalité maximale, Hurwitz — liminf 0.447209 vs borne 1/√5 = 0.447214, cf. JACOBSON V0 C5). C'est le deuxième échec de dérivation d'α (après le côté noyau) — et il **resserre** le statut d'α : c'est un axiome de stabilité, pas une conséquence thermique.

---

## 3. CE QUE CE DÉPÔT ACHÈTE (la piste reste ouverte, mais déplacée)

Le double réfuté (noyau : JACOBSON V0 ; opérateur : C5 ici) n'est pas une impasse : il **localise** le branchement.

- ✅ **Gagné** : le point de passage exact. Le facteur thermique vit **dans la phase** (C7) ; la mémoire de couplage agit **sur la phase** (déphasage uniforme π/(2φ), C6) ; les deux se composent multiplicativement (C7, split 1 ulp). Le pont THU n'est ni K(t), ni le module de D^(1/φ) — il est dans **Φ₂ = ∫k_μdx^μ** : la mémoire déphase, le vide thermise, et les deux opérations commutent.
- 🔬 **Prochain dépôt (V1)** : formaliser la composition **phase mémoire × phase thermique** — montrer que le déphasage uniforme π/(2φ) laisse invariante la balance détaillée (préfigure par C2+C4) mais **modifie la cohérence** (fonction de corrélation hors axe KMS) : la mémoire agit sur la cohérence, pas sur la thermicité. C'est falsifiable : chercher une violation de balance détaillée induite par D^(1/φ) sur un état NON-KMS.
- 🔬 **En parallèle** : S = A/4G via l'**aire mesurée par la métrique V1** g_μν = Re[(∂_μΨ₁)(∂_νΨ₁)\*] (question laissée ouverte dans `PROBLEME_OUVERT_EINSTEIN.md`, §V3) — l'autre moitié de la chaîne de Jacobson, indépendante du choix de α.

---

## 4. BORNES HONNÊTES

| Item | Statut |
|---|---|
| C1 (KMS géométrique), C2 (balance détaillée), C3 (T·R), C7 (Boltzmann = phase) | ✅ résultats **standards** (KMS/Takagi/Unruh), re-vérifiés machine avec les constantes THU — exacts mais pas nouveaux |
| C4 (non-sélection de α par KMS) | ✅ réfutation **nouvelle** déposée, machine-vérifiée |
| C5 (non-thermalité du spectre fractionnaire) | ✅ réfutation **nouvelle** déposée, machine-vérifiée |
| C6 (signature Δφ_mem = π/(2φ)) | ✅ signature déposée — sa **signification physique** (cohérence vs thermicité) reste à établir en V1 |
| Leçons de débogage consignées | C2 premier run : 3.14e+01 = βω (bug `abs(w)` avant branchement signé → Ḟ(−ω) ≡ Ḟ(ω)) ; C4 premier run : 0/0 à ω = 1 (log 1 = 0, loi de puissance indéfinie). **Deux defects trouvés par la signature attendue, pas par inspection** — la méthode des signatures a travaillé |
| Statut trou noir | inchangé : frontière ouverte (P9, `paradoxes-quantiques.html`) — mais la porte d'entrée est maintenant **doublement chiffrée** : 8π = 2π×4 (JACOBSON V0) et Boltzmann = phase (ici) |

---

## 5. FICHIERS

- `verif_kms_dphi_thu_v0.py` — les 7 contrôles, verdict par code de sortie (0 = conforme).
- `resultat_kms_dphi_thu_v0.json` — nombres bruts machine (7/7, exit 0).
- Contexte amont : `DEPOT_JACOBSON_THU_V0.md` (verdict `JACOBSON_V0_CHAINE_EXACTE_PONT_DIRECT_REFUTE`, piste réorientée vers la phase), `PROBLEME_OUVERT_EINSTEIN.md` (Problème V3), `DERIVATION_TSTAR_IRRATIONNALITE_MAXIMALE.md` (axiome α = 1/φ).
