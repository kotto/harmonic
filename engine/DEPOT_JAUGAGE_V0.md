# DÉPÔT JAUGAGE V0 — jauger localement le noyau U(1) : le prix du rephasage modulé

| | |
|---|---|
| **Projet** | THU/MSH 5.x — campagne jauge, verrou résiduel L3 |
| **Date de dépôt** | 28/08/2026 — **écrit avant tout script** (contrôle C0a : mtime dépôt < mtime exécution) |
| **Statut** | DÉPÔT FERMÉ — familles, barres et échelle de verdicts gelées ci-dessous |
| **Script prévu** | `verif_jaugage_v0.py` — **interdit d'exister avant ce dépôt** |
| **Sortie** | `resultat_jaugage_v0.json` — toutes les lectures, y compris les quasi-échecs |

**Amont** :
- `FICHE_THEOREME_U1.md` §5.1 — critère de clôture [F] : « dériver la liberté locale et la contrepartie de champ depuis l'invariance du noyau K̂ sous rephasage modulé » (ligne §4 corrigée le 28/08 : la dérivation statique de α est tombée, le verrou passe ici).
- `EXPLORATION_MEMOIRE_COUPLAGES.md` §7 — [OBS] 28/08 : facteur sans nom 1,8324104 voisin de 1/D₂ = 1,8342482 à 1,0×10⁻³ (consigné, aucune revendication).
- `GENERALISATION_D1PHI_GAUGE_5_DOMAINES.md` — D^{1/φ}[Ψ] = G[Ψ] **prouvé** pour la gravitation spin-2 à 1e-15 : le mécanisme « mémoire = contrainte spatiale » existe déjà ; ce dépôt en attaque la face de phase U(1).
- `DEPOT_ALPHA_GRAMMAIRE_V0.md` / `RESULTAT_ALPHA_GRAMMAIRE_V0.md` — gabarit protocolaire, famille D_p, justification de TOL_HIT_PLUS = 2,355×10⁻⁷.

---

## §0. Objet

Le 27/08, la campagne jauge a établi [T] le théorème structurel : *N modes complexes fermés partageant UNE loi de conservation scalaire ⟹ N²−1 canaux dynamiques ≅ su(N)* (dyade 8/8 ≤ 4,37e-15 ; triangle 7/7 ≤ 8,12e-15). Ce théorème produit l'**algèbre** de jauge, pas son **jaugage** : ni la liberté locale ψ ↦ e^{iα(x)}ψ, ni la contrepartie de champ, ni le couplage.

Le présent dépôt attaque les dimensions **D1 (localisation)** et **D2 (la force)** du trou cartographié le 28/08, au niveau V0 :

**Hypothèse unique déposée [P]** : *le couplage est le prix de la stationnarité locale.* Si le noyau K̂ possède le U(1) global exact (liberté résiduelle de l'unicité de projection, Maillon 3), alors un rephasage **modulé** α(x) coûte quelque chose — ce coût est mesurable, il doit être porté par le gradient de α, et sa force doit être un **nombre fermé du noyau**. Si le coût n'existe pas, ou s'il n'est pas gradient-porté, ou si sa force ne porte aucun nom fermé : le dépôt le consigne et l'échelle de verdicts le dit.

## §1. Objets fermés (hérités, non modifiables) et interdiction I1

- **O1** — α = 1/φ ; φ² = φ+1 ; φ = (1+√5)/2.
- **O2** — Noyau projecteur (fiche U(1), Maillon 3) : **K̂(ω) = φ / ((iω)^α + φ)**, branche principale : arg(iω)^α = +πα/2 si ω>0, −πα/2 si ω<0, K̂(0) = 1. Relation avec le noyau de mémoire validé : K̂ = φ·(iω)^{1−α}·K̃, où **K̃(ω) = (iω)^{α−1} / ((iω)^α + φ)** (route complexe validée 2,8e-17, forme réelle développée validée C3b).
- **O3** — Treillis entier : N = 512, L = 20π, Δω = 2π/L = 0,1 ; grille ω_m = m·Δω si m ≤ N/2, (m−N)·Δω si m > N/2. Tous les modes employés (ω₀ ∈ {0,1 ; 0,5 ; 1 ; 2 ; 10} → bins {1,5,10,20,100} ; k ∈ {0,1 ; 0,5 ; 1 ; 2 ; 5 ; 10} → bins {1,5,10,20,50,100}) tombent sur des bins entiers ; Nyquist 25,6 > max|ω| = 20 : zéro fuite spectrale.
- **O4** — Valeurs fermées de registre : |K̃(½)|² = 0,4011522499939087 ; impédance 1/|K̃(½)|² = 2,492819122951908 ; D₂ = (1/π)∫₀^∞|K̃(ω)|²dω = 0,54518249 (seule norme convergente, p < φ²) ; ancre 137,036031356 ; CODATA 137,035999177.
- **O5** — Norme unitaire (Parseval, axiome U2) : ‖ψ‖² = Σₙ|ψₙ|²/N, DFT unitaire.
- **O6** — Porteur : ψ₀(x) = e^{iω₀x}/√N, ω₀ = 1 (sauf Famille C où ω₀ parcourt O3).
- **O7** — Barres : TOL_HIT = 1×10⁻⁴ ; TOL_HIT_PLUS = 2,355×10⁻⁷ ; TOL_COV = 1×10⁻⁹.

**I1 (interdiction)** — π, e, √2, √3 n'entrent jamais dans la construction des profils ni comme ingrédients littéraux des candidats géométriques. π apparaît uniquement (a) structurellement dans la branche complexe de O2 (déjà validée), (b) dans les angles de test θ₀ ∈ {π/3, π/2} (constantes de test arbitraires — la lecture A2 est exacte pour tout θ₀), (c) dans les témoins de continuité à barre TOL_HIT_PLUS.

## §2. Familles fermées

### Famille A — COVARIANCE (36 profils fermés)

Profils α_{a,k}(x) = a·cos(kx), a ∈ {0,1 ; 0,2 ; 0,5 ; 1 ; 2 ; 5} × k ∈ {0,1 ; 0,5 ; 1 ; 2 ; 5 ; 10} — 36 = 6×6, tous multiples entiers de Δω.

| Lecture | Définition | Barre | Interprétation |
|---|---|---|---|
| **A1** | D(a,k) = ‖K̂[e^{iα_{a,k}}ψ₀] − e^{iα_{a,k}}·K̂[ψ₀]‖ / ‖K̂[ψ₀]‖ — 36 valeurs, **toutes consignées** | (mesure) | Le **coût** du rephasage modulé : ce qu'un compensateur devrait fermer |
| **A2** | Pour θ₀ ∈ {π/3, π/2} : D(a,k ; α+θ₀) = D(a,k) sur les 36 profils | TOL_COV = 1e-9 | Le noyau est **aveugle au rephasage constant** : le défaut n'est porté que par la variation de α. Statut honnête : identité exacte pour tout opérateur linéaire — contrôle de possession du U(1), pas une victoire THU |
| **A3** | χ_a(k) := D(a,k)/a ; dérive au doublement \|χ_{0,2}(k) − χ_{0,1}(k)\| / χ_{0,1}(k) pour les 6 k | ≤ 5 % | La réponse est une **fonction propre du gradient** χ(k) — l'objet-force de la Famille B. Table complète χ_a(k) 6×6 consignée |

**Témoin négatif TN-A (pouvoir discriminant de A3)** — à grande amplitude (doublement 2→5), la dérive |χ₅(k) − χ₂(k)|/χ₂(k) doit **dépasser 5 %** pour au moins 2 des 3 témoins k ∈ {0,1 ; 1 ; 10}. Si le régime non linéaire n'est pas détecté, la lecture A3 est vide → V4.

### Famille B — LA FORCE (registre fermé de 16 candidats, 32 lectures)

**G\*** := χ_{0,1}(k_ref = 1) = D(0,1 ; k=1)/0,1, normalisé par la réponse du spectre de tour au mode ½ : G\* := χ_{0,1}(1) / R_tour(½), où R_tour(½) = 1 par l'identité φ+φ⁻¹ = √5 (contrôle C2). La division est une fermeture, pas un ajustement : elle vaut 1.

Règle de barre : 1×10⁻⁴ pour tout candidat dont l'écriture close n'introduit ni e ni π **littéraux** (la π de la branche complexe du noyau est structurelle, déjà validée — elle ne compte pas) ; 2,355×10⁻⁷ pour les témoins de continuité. Lecture : hit si |G\*/c − 1| ≤ barre **ou** |c/G\* − 1| ≤ barre — 32 lectures, toutes consignées.

| # | Candidat | Valeur | Barre | Provenance |
|---|---|---|---|---|
| 1 | 1/D₂ | 1,8342481982500942 | 1e-4 | registre grammaire 27/08 + [OBS] §7 exploration |
| 2 | D₂ | 0,54518249 | 1e-4 | idem |
| 3 | Impédance 1/\|K̃(½)\|² | 2,492819122951908 | 1e-4 | exploration T2, 27/08 |
| 4 | \|K̃(½)\|² | 0,4011522499939087 | 1e-4 | idem |
| 5 | φ | 1,6180339887 | 1e-4 | O1 |
| 6 | φ² | 2,6180339887 | 1e-4 | O1 |
| 7 | 1/φ | 0,6180339887 | 1e-4 | O1 |
| 8 | √5 | 2,2360679775 | 1e-4 | identité mode ½ |
| 9 | 2φ | 3,2360679775 | 1e-4 | O1 |
| 10 | F₁₀ | 55 | 1e-4 | Fibonacci |
| 11 | L₁₀ | 123 | 1e-4 | Lucas |
| 12 | e^{1/φ} | 1,8552770 | 2,355e-7 | témoin e (résidu T3) |
| 13 | e^{−1/φ} | 0,5390121 | 2,355e-7 | témoin e |
| 14 | Facteur [OBS] 28/08 | 1,8324104102898406 | 2,355e-7 | croisement (α_W/α_EM ÷ impédance ; contient α_EM → e,π en amont). Une coïncidence ici ne vaut PAS identification — l'ancre 5-facteurs est déjà reclassée coïncidence de compression |
| 15 | Ancre 5-facteurs | 137,036031356 | 2,355e-7 | témoin e/π |
| 16 | 1/Ancre | 0,00729735 | 2,355e-7 | témoin e/π |

**Témoin négatif TN-B (spécificité du hit)** — 3 profils aléatoires α_r(x) = Σ_{j=1..4} 0,1·u_j·cos(k_jx + θ_j), graines **27 / 28 / 29** (27 = graine héritée de la campagne jauge), u_j ~ U[1,10], k_j distincts tirés de la grille O3, θ_j ~ U[0,2π). G_r := D_r(0,1)/0,1. Si la Famille B produit un hit sur (c, barre b), alors **au plus 1 des 3 G_r** peut toucher le même c à la même barre. Sinon le hit n'est pas spécifique au gradient simple → V4.

**I5-B** — aucun candidat ne sera ajouté après exécution, y compris si les lectures consignées « suggèrent » un nouveau nom : celui-ci fera l'objet d'un dépôt ultérieur.

### Famille C — RUNNING (diagnostique : puissance de verdict NULLE au V0)

Porteur ω₀ ∈ {0,1 ; 0,5 ; 1 ; 2 ; 10} (bins 1, 5, 10, 20, 100), profil fixe α(x) = 0,1·cos(x) (k_ref = 1). Lecture : χ(ω₀) := D(0,1 ; k=1) au porteur ω₀ (5 valeurs consignées) ; **β_pred** := pente des moindres carrés de ln χ vs ln ω₀ (formule fermée, 5 points).

Dépôt ex ante, sous le dictionnaire **D+** (ω↑ ⇔ μ↑) : la tripartition [P] prédit α_EM criblée ⟹ **signe(β_pred) > 0** et amplitude β_pred ∈ [0,1 ; 2]. Le dictionnaire μ↔ω est **absent** de la théorie (trou D4) — le dictionnaire inverse D− (ω↑ ⇔ μ↓) est également recevable et retournerait le signe.

**Décision protocolaire** : β_pred est consigné et comparé aux deux dictionnaires, mais la Famille C **ne porte aucun verdict** au V0 — ni dans l'échelle §4, ni dans V4. Une réussite sous D+ sera notée comme accord transversal ; un échec sous D+ sera consigné comme échec sous dictionnaire non établi. Aucune revendication quantitative PDG.

## §3. Contrôles bloquants

| # | Contrôle | Barre |
|---|---|---|
| C0a | mtime(`DEPOT_JAUGAGE_V0.md`) < heure d'exécution ; les deux horodatages dans le JSON | — |
| C0b | fermeture algébrique φ² = φ+1 | 1e-15 |
| C1 | K̂ : route complexe (branche principale) vs forme réelle développée \|K̂\|² = φ²/(φ² + 2φcos(πα/2)·ω^α + ω^{2α}) sur la grille O3 entière + points fermés {½, 1/φ, 1} | 1e-12 |
| C2 | transparence du mode ½ : φ + φ⁻¹ − √5 = 0 (identité T2b de l'assaut 27/08) | 1e-12 |
| C3 | CODATA 2022 : α⁻¹ = 137,035999177 consigné et distinct de l'ancre | — |
| C4 | ancre 5-facteurs reproduite depuis sa formule fermée du corpus (statut : coïncidence de compression, ancre maintenue) | 1e-11 rel |
| C5 | impédance : \|K̃(½)\|² = 0,4011522499939087, double route (complexe + réel développé) | 1e-10 |
| C6 | D₂ = 0,54518249 réintégrée : (1/π)∫₀^∞\|K̃(ω)\|²dω, même route de quadrature que le 27/08 (reproductibilité croisée) | 1e-6 |

Règle unique : **UN SEUL contrôle en échec ⟹ V4 REFUTE, exit 1, aucun sauvetage.**

## §4. Échelle de verdicts (gelée avant exécution)

| Verdict | Condition | Sortie |
|---|---|---|
| **V+ — JAUGAGE_COMPLET_CONFIRME** | A2 ✓ et A3 ✓ et hit Famille B ≤ 2,355e-7 | exit 0 |
| **V2 — JAUGAGE_CONFIRME_FORCE_CANDIDATE** | A2 ✓ et A3 ✓ et hit géométrique ≤ 1e-4 (candidats 1–11) | exit 0 |
| **V3 — COVARIANCE_LOCALE_DERIVEE_FORCE_SANS_NOM** | A2 ✓ et A3 ✓ et aucun hit | exit 0 |
| **V4 — REFUTE** | tout contrôle §3 en échec, ou TN-A, ou TN-B | exit 1 |
| **LIBERTE_LOCALE_ABSANTE** | A3 en échec : le défaut n'est pas gradient-porté, la structure de compensateur n'existe pas à ce niveau | exit 1 |

Précision : A2 est une identité de linéarité — son échec est un **impossibilité signal** (aucun opérateur linéaire ne peut l'échouer) et route donc vers V4 (pipeline cassé), pas vers LIBERTE_LOCALE_ABSANTE. La lecture de fond de la D1 est A3 : c'est elle qui peut absenter la liberté locale.

V3 n'est **pas** un jaugage complet : il établit que le défaut de covariance locale existe, est aveugle au rephasage constant, linéaire dans l'amplitude et porté par le mode gradient — la structure de compensateur existe ; sa force reste sans nom.

## §5. Interdictions

- **I1** — π, e, √2, √3 hors construction (cf. §1).
- **I2** — zéro paramètre libre : tout nombre utilisé est dans O1–O7 ou dans les registres fermés §2.
- **I3** — aucune lecture cachée : les 36 D(a,k), les 72 lectures A2, la table χ 6×6, les 32 comparaisons B, les 3 G_r, les 5 χ(ω₀) et β_pred sont **toutes** consignées, y compris les quasi-échecs.
- **I4** — pas de dépassement de revendication : V3 n'est pas −¼F² ; la tripartition α_W/α_EM/α_S reste [P] tant que le jaugage n'est pas fermé ; la Famille C ne dit rien de PDG.
- **I5** — aucune modification du dépôt ni du registre après exécution : les verdicts tombent dans `resultat_jaugage_v0.json`, annexé tel quel.

## §6. Honnêteté — ce que V0 ne prouve pas

1. **Pas de dérivation de −¼F²** : V0 mesure le défaut de covariance locale et son amplitude ; le compensateur dynamique (trou D3) reste ouvert.
2. **Pas de dictionnaire μ↔ω** : la Famille C est diagnostique (trou D4).
3. **Pas de U(1)_Y, pas d'électrofaible** : V0 est strictement U(1) abélien sur un seul porteur complexe.
4. **Pas de pourquoi N=3, N=2** : le théorème structurel du 27/08 ne dit pas pourquoi la nature choisit ces N.
5. **Le [OBS] 1,8324 ↔ 1/D₂ est à 1,0×10⁻³**, facteur 10 au-dessus de la barre : c'est un candidat parmi 16, pas un verdict. Seul le passage machine décide — et un hit à 1e-4 sur le candidat 1/D₂ vaudra « force candidate », pas « force dérivée ».
6. La tripartition mémoire (α_W sans mémoire, α_EM porteur de ligne, α_S mémoire pure) reste une **lecture [P]**.

## §7. Reproductibilité

```
python verif_jaugage_v0.py        # python 3.11.8, win32
```

Paramètres fixés : N = 512, L = 20π (Δω = 0,1), ω₀ = 1 (Familles A/B), k_ref = 1, a_ref = 0,1, graines 27/28/29 (TN-B), DFT unitaire, norme unitaire O5. Bibliothèque libre (numpy autorisé) — toute dérive de convention est bloquée par C1. Sortie : `resultat_jaugage_v0.json` (horodatages C0a, toutes les lectures, verdict, exit code).

---

> *Le noyau sait tourner les phases globales sans y penser. Ce dépôt demande combien il paie quand on le force à tourner localement — et si ce prix porte déjà un nom dans ses propres registres.*
