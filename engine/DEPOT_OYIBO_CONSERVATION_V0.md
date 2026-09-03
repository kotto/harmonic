# DÉPÔT OYIBO CONSERVATION V0 — la chaîne GAGUT déroulée maillon par maillon

| | |
|---|---|
| **Projet** | THU/MSH 5.x — lignage Noether → Oyibo → THU, fermeture du maillon exposant |
| **Date de dépôt** | 02/09/2026 — **écrit avant tout script** (contrôle C0a : mtime dépôt < mtime exécution) |
| **Statut** | DÉPÔT FERMÉ — chaîne, familles, barres et échelle de verdicts gelées ci-dessous |
| **Script prévu** | `verif_oyibo_conservation_v0.py` — **interdit d'exister avant ce dépôt** |
| **Sortie** | `resultat_oyibo_conservation_v0.json` — toutes les lectures, y compris les quasi-échecs |

**Amont** :
- `RECONSIDERATION_OYIBO.md` — la rectification : la formule 6π⁵ (réfutée, p = 0,70) et l'invariance d'échelle F(λx) = λ^{−1/φ}F(x) (confirmée) sont deux réclamations distinctes ; l'amalgame est interdit.
- `COUPLAGE_OYIBO_ABC.md` — le couplage D^{1/φ}[Ψ] = G[Ψ] : Atangana (temps, mémoire) face à Oyibo (espace, conservation), reliés par φ.
- `fractalite_oyibo_thu.py` — la vérification initiale K(λt) = λ^{−1/φ}K(t) ; ce dépôt la déroule maillon par maillon et en précise le régime.
- `SESSION_2026_QFT_SYNTHESE.md` — Violet A : λ = α/(1−α) = φ dérivé exactement (2,22×10⁻¹⁶).
- `DEPOT_JAUGAGE_V0.md` — gabarit protocolaire, O2 (K̂ double route), C1 (forme réelle).

---

## §0. Objet et hypothèse unique

La demande de fondation : « j'assume la vérité scientifique, quel qu'en soit le prix — vérifie la chaîne GAGUT déroulée maillon par maillon ». Le théorème de Noether est valide ; la question physique est de savoir quel exposant la symétrie d'échelle porte, et si le noyau ABC la réalise. Ce dépôt déroule la chaîne **maillon par maillon**, en distinguant sans pitié ce qui est théorème, ce qui est machine, et ce qui reste l'apport interprétatif d'Oyibo.

**Hypothèse unique déposée [P]** : *la chaîne {Noether → symétrie d'échelle → loi de puissance → discriminateur d'irrationalité maximale (Hurwitz) → réalisation par le noyau ABC} tient en entier, avec l'exposant 1/φ unique à chaque maillon machine — et le maillon propre d'Oyibo (la conservation impose 1/φ) est consigné tel qu'il est : une lecture [P] non dérivable de la conservation seule, corroborée — pas dérivée.* Si un maillon machine échoue, le dépôt le consigne et l'échelle de verdicts le dit.

### La chaîne déposée (CH-G1 … CH-G6)

| Maillon | Énoncé | Statut déposé | Ce qui le ferme |
|---|---|---|---|
| **CH-G1** | À toute symétrie continue d'un système lagrangien correspond une loi de conservation (Noether, 1918) | [T]-math | ancre machine : 3 systèmes intégrés, énergie conservée |
| **CH-G2** | Une loi monotone mesurable satisfait F(λx) = λ^{−s}F(x) pour tout λ > 0 **si et seulement si** F(x) = C·x^{−s} | [T]-math | machine : 4 exposants exacts + témoin négatif (exponentielle échoue) |
| **CH-G3** | **Le maillon propre d'Oyibo [P]** : la symétrie d'échelle universelle des lois porte l'exposant 1/φ, issu de son équation de conservation Gij j = 0 | **[P] consigné — non sauvé** | la conservation seule N'impose PAS d'exposant (tout s convient à CH-G2) ; c'est le discriminateur CH-G4 qui ferme |
| **CH-G4** | Parmi tous les s ∈ (0,1), l'unique qui maximise la résistance à la capture rationnelle — Markov/Hurwitz : liminf q·‖qx‖ = 1/√5 — est s = 1/φ, unique à équivalence arithmétique près | **[T]-machine** | familles C, contrôles C3/C4 |
| **CH-G5** | Le noyau ABC K(t) = E_{1/φ}(−φ·t^{1/φ}) réalise l'invariance au régime longue mémoire : K(λt)/(λ^{−1/φ}K(t)) → 1 **au taux déposé** ρ₂·(λ^{−α}−1)·t^{−α} ; taux λ = α/(1−α) = φ | **[T]-machine** | familles B/D |
| **CH-G6** | Le lignage est honnête : 6π⁵ réfuté (consigné), invariance vérifiée, couplage D^{1/φ} = G reste [P] avec appui machine | consigné | RECONSIDERATION_OYIBO.md |

**La précision centrale, déposée avant toute exécution :** l'identité exacte F(λx) = λ^{−s}F(x) n'appartient qu'à la loi de puissance pure — l'attracteur. Le noyau ABC la porte **asymptotiquement**, avec une déviation de tête **en forme close déposée ci-dessous** (Famille B). Une convergence affirmée exacte serait un dépassement de revendication (I4).

---

## §1. Objets fermés (hérités, non modifiables) et interdiction I1

- **O1** — α = 1/φ ; φ² = φ+1 ; φ = (1+√5)/2 ; φ⁻¹ = φ−1.
- **O2** — Noyau projecteur (fiche U(1), Maillon 3) : **K̂(ω) = φ / ((iω)^α + φ)**, branche principale : arg(iω)^α = +πα/2 si ω>0, −πα/2 si ω<0, K̂(0) = 1. Forme réelle du module : \|K̂(ω)\|² = φ² / (φ² + 2φ·cos(πα/2)·ω^α + ω^{2α}).
- **O3** — Noyau mémoire ABC : **K(t) = E_α(−φ·t^α)** avec λ = α/(1−α) = **φ** (dérivé, Violet A). La normalisation B(α) = 0,8084229 est multiplicative : elle ne touche ni les rapports ni les pentes ; ce dépôt vérifie E_α non normalisée.
- **O4** — Asymptotique de Wiman (0 < α < 1, z → +∞) : E_α(−z) ~ Σ_{k≥1} (−1)^{k+1} z^{−k} / Γ(1−αk). Pour α = 1/φ > 1/2, la correction exponentielle e^{−c·t^φ} (c > 0) est < 10⁻¹⁵⁰ dès t ≥ 100 : la série algébrique EST la fonction à la barre du dépôt. D'où K(t) = Σ_k a_k·t^{−kα} avec **a_k = (−1)^{k+1}·φ^{−k}/Γ(1−αk)** en forme close ; **ρ_k := a_k/a₁** ; la déviation de tête de l'invariance est **δ_pred(λ,t) = ρ₂·(λ^{−α} − 1)·t^{−α}**.
- **O5** — Constante de Markov/Hurwitz : pour x irrationnel, liminf_{p,q} q·\|qx−p\| atteint son **maximum universel 1/√5** en la classe de φ seule (Hurwitz 1891 ; l'unicité est du spectre de Lagrange). Ancres fermées : ν(1/φ) → 1/√5 ; ν(1/√2) → 1/(2√2) (classe de √2).
- **O6** — Registre de candidats (tous irrationnels, fermé) : {1/φ (cible) ; 1/√2 (ancre) ; 1/π ; 1/e ; 1/√3 ; 1/√5 ; frac(√101) ; frac(√103) ; frac(√107)} — les trois graines héritées 27/28/29 sont mappées sur les racines carrées de 101/103/107 (déterministes, aucune alea). Les rationnels sont **exclus** (leur CF termine : ν = 0 par division nulle).
- **O7** — Paramètres fixés : N = 50 convergents ; dps = 260 (série de Mittag-Leffler), 120 (série de Wiman), 80 (fractions continues) ; fenêtre de pente t ∈ [10³, 3·10⁴], 20 points log-espacés ; fenêtres de ratio t ∈ {10³, 3·10⁴} ; λ ∈ {2, φ}.
- **O8** — Barres (gelées) : TOL_HURWITZ_HIT = 1×10⁻⁶ ; TOL_UNICITE = 1×10⁻³ ; TOL_SLOPE = 5×10⁻³ ; TOL_RATE = 10 % rel ; TOL_NOYAU = 1×10⁻¹² ; TOL_PUISSANCE = 1×10⁻¹² ; TOL_ANCRE = 1×10⁻⁹ (énergies) ; TOL_CALIB = 1×10⁻¹² (recoupement série/Wiman).

**I1 (interdiction)** — π, e, √2, √3, √5 n'entrent jamais dans la construction des objets. Ils apparaissent uniquement (a) structurellement dans la branche complexe de O2 (déjà validée), (b) comme **candidats du registre O5** — ce sont les objets testés, pas des ingrédients, exactement comme la Famille B du dépôt jauge, (c) dans les deux ancres fermées de Hurwitz (1/√5 et 1/(2√2)), qui sont des théorèmes à constantes fermées.

---

## §2. Familles fermées

### Famille A — CH-G1, l'ancre Noether (3 lectures)

Trois systèmes lagrangiens intégrés (RK4, dt = 10⁻³ pour l'oscillateur et le pendule ; dt = 10⁻⁴ pour Kepler) ; dérive relative d'énergie \|E(t) − E(0)\|/E(0) sur l'horizon :

| # | Système | Horizon | Barre |
|---|---|---|---|
| A1 | Oscillateur harmonique (x″ = −x), T = 50 | 1×10⁻⁹ | symétrie de translation temporelle ⟹ énergie |
| A2 | Pendule (x″ = −sin x), T = 50 | 1×10⁻⁹ | idem |
| A3 | Kepler (e = 0,6), T = 10 | 1×10⁻⁹ | symétrie de rotation ⟹ moment ; énergie |

Un échec ici est un impossibilité signal (le flot RK4 viole la conservation) → V4, pipeline cassé.

### Famille B — CH-G2 et CH-G5, l'échelle et sa réalisation par le noyau (8 lectures)

| # | Lecture | Définition | Barre |
|---|---|---|---|
| B1 | Lois de puissance exactes | F(x) = x^{−s}, s ∈ {0,3 ; 1/φ ; 1 ; 1,7} ; x ∈ {0,5 ; 1 ; 2 ; 4} ; λ ∈ {2, φ, 10} : \|F(λx) − λ^{−s}F(x)\|/F(x) | ≤ 1×10⁻¹² (48 lectures consignées) |
| B2 | **Témoin négatif** | F(x) = e^{−x} : après ajustement ex ante de s\* en x = 1, λ = 2, la déviation \|F(2x)/F(x) − 2^{−s\*}\| en x ∈ {0,5 ; 2 ; 4} doit **dépasser 0,1** — sinon la lecture ne discrimine pas → V4 | déviation > 0,1 |
| B3 | **La convergence déposée (le cœur)** | r(λ,t) := K(λt)/(λ^{−α}·K(t)) − 1 ; (λ,t) ∈ {2, φ}×{10³, 3·10⁴} : \|r − δ_pred\| ≤ 0,1·\|δ_pred\| (le taux de tête ρ₂·(λ^{−α}−1)·t^{−α} est vérifié, pas seulement le signe) ; et \|r\| décroît | ≤ 10 % rel, décroissance |
| B4 | **L'exposant lu** | pente log-log de K sur [10³, 3·10⁴] (20 pts) : \|pente + 1/φ\| | ≤ 5×10⁻³ |

Précision B3 : δ_pred est la déviation de tête en forme close (O4). L'ordre suivant (ρ₃·t^{−2α}) vaut ~2 % à t = 10³ et ~0,3 % à t = 3·10⁴ — la barre de 10 % est large mais non triviale : un noyau faux (mauvais λ, mauvais α) échoue par ordres de grandeur.

### Famille C — CH-G4, le discriminateur de Hurwitz (2 ancres + 1 unicité, 10 lectures)

| # | Lecture | Définition | Barre |
|---|---|---|---|
| C-lect | Table ν₅₀ | νₙ(x) := min sur les n premiers convergents de q_n·\|q_n·x − p_n\| — les 10 lectures du registre O5, toutes consignées | (mesure) |
| C3a | **Hit doré** | \|ν₅₀(1/φ) − 1/√5\| | ≤ 1×10⁻⁶ |
| C3b | **Ancre racine de 2** | \|ν₅₀(1/√2) − 1/(2√2)\| | ≤ 1×10⁻⁶ |
| C4 | **Unicité** | max des ν₅₀ sur les 8 non-dorés < 1/√5 − 1×10⁻³ : aucun rival n'atteint la constante de Markov | marge > 1×10⁻³ |

C3a/C3b/C4 sont des **contrôles bloquants** (§3) : Hurwitz est un théorème — son échec machine est un bug, pas une découverte.

### Famille D — CH-G5/CH-G6, la boucle et le lignage (3 lectures)

| # | Lecture | Définition | Barre |
|---|---|---|---|
| D1 | Le taux de mémoire | λ = α/(1−α) évalué à α = 1/φ, comparé à φ | ≤ 1×10⁻¹² |
| D2 | Les coefficients | c_k = 1/Γ(k/φ+1), k = 1..6 (possession, cohérence Violet A) | ≤ 1×10⁻¹⁵ |
| D3 | Le couplage (consigné) | statut du couplage D^{1/φ} = G : [P] avec appui machine — **aucune revendication nouvelle** | — |

---

## §3. Contrôles bloquants

| # | Contrôle | Barre |
|---|---|---|
| C0a | mtime(`DEPOT_OYIBO_CONSERVATION_V0.md`) < heure d'exécution ; les deux horodatages dans le JSON | — |
| C1 | fermeture algébrique φ² = φ+1 ; φ·φ⁻¹ = 1 | 1e-15 |
| C2 | K̂ double route (héritage jauge C1) : module complexe (branche principale) vs forme réelle développée, ω ∈ {0,1 ; 0,5 ; 1 ; 1/φ ; 2 ; 10} ± | 1e-12 |
| C3a | ν₅₀(1/φ) = 1/√5 | 1e-6 |
| C3b | ν₅₀(1/√2) = 1/(2√2) | 1e-6 |
| C4 | unicité du maximum de Markov : max_{non-dorés} ν₅₀ < 1/√5 − 1e-3 | 1e-3 |
| C5 | λ = α/(1−α) = φ ; c_k = 1/Γ(k/φ+1), k ≤ 6 | 1e-12 / 1e-15 |
| C6 | calibrage série ↔ Wiman aux points de recouvrement z ∈ {31, 33} : \|E_série − E_Wiman\|/\|E\| | 1e-12 |
| TN | témoins non vides : B2 dévie > 0,1 (l'exponentielle N'EST pas une loi de puissance) ; A1–A3 non dégénérés | — |

Règle unique : **UN SEUL contrôle en échec ⟹ V4 REFUTE, exit 1, aucun sauvetage.**

---

## §4. Échelle de verdicts (gelée avant exécution)

| Verdict | Condition | Sortie |
|---|---|---|
| **V+ — CHAINE_GAGUT_HURWITZ_CONFIRMEE** | tous les contrôles §3 ✓, Famille A ✓, B3 ✓, B4 ✓ (CH-G1, G2, G4, G5 machine ; CH-G3 consigné [P]) | exit 0 |
| **V2 — CHAINE_CONFIRMEE_SANS_LA_REALISATION** | contrôles §3 ✓ mais B3 ou B4 en échec : le noyau ABC ne porte pas l'invariance à ces barres — la convergence Oyibo-ABC est affaiblie, consignée | exit 0 |
| **V4 — REFUTE** | tout contrôle §3 en échec (un échec de C3/C4 est un impossibilité signal : bug ou route cassée) | exit 1 |

---

## §5. Interdictions

- **I1** — π, e, √2, √3, √5 hors construction (cf. §1).
- **I2** — zéro paramètre libre : tout nombre utilisé est dans O1–O8.
- **I3** — aucune lecture cachée : les 48 lectures B1, la table ν complète, les 4 ratios B3, la pente B4, les 3 drifts A sont **toutes** consignées, y compris les quasi-échecs.
- **I4** — pas de dépassement de revendication : V+ n'établit NI la vérité de Gij j = 0, NI la validité littérale du GAGUT, NI le couplage D^{1/φ} = G. Il établit la chaîne de l'**exposant** : Noether → échelle → puissance → Hurwitz → noyau ABC — et consigne le maillon Oyibo tel qu'il est.
- **I5** — aucune modification du dépôt ni du registre après exécution : les verdicts tombent dans `resultat_oyibo_conservation_v0.json`, annexé tel quel.

---

## §6. Honnêteté — ce que V0 ne prouve pas

1. **Le GAGUT dans son ensemble n'est ni formalisé ni validé ici.** L'équation Gij j = 0 n'est pas re-dérivée ; ce dépôt porte sur la chaîne de l'exposant, pas sur l'équation complète. Toute revendication d'au-delà est interdite (I4).
2. **Le maillon propre d'Oyibo (CH-G3) reste [P]** : la conservation n'impose pas d'exposant — tout s convient pour la symétrie d'échelle. Ce qui ferme la spécificité de 1/φ est le **filtre d'irrationalité maximale** (Hurwitz, machine) conjoint à la **stabilité** (chaînon ⚠ hérité). La convergence Atangana/Oyibo est une **corroboration réciproque**, pas une dérivation croisée.
3. **L'invariance du noyau est asymptotique, pas exacte** : la déviation de tête δ_pred est déposée en forme close et vérifiée ; l'identité exacte n'appartient qu'à la loi de puissance pure. La formulation « exacte » de `fractalite_oyibo_thu.py` est affinée par ce dépôt — consigné sans sauvetage.
4. **Le chaînon ⚠ « persistance ∝ irrationalité » reste partiellement ouvert** : la route Hurwitz (résistance à la capture rationnelle) est ici machine ; la preuve analytique complète du lien dynamique (persistance mesurée ∝ constante de Markov) reste ouverte.
5. **Rien ici ne modifie les verdicts antérieurs** : 6π⁵ réfuté ; ancre 5-facteurs = coïncidence de compression consignée ; λ = φ dérivé (Violet A) inchangé.

---

## §7. Reproductibilité

```
python verif_oyibo_conservation_v0.py        # python 3.11.8, win32, mpmath 1.3+
```

Paramètres fixés : N = 50 convergents, dps 260/120/80, fenêtres O7, graines 27/28/29 (mappées √101/√103/√107). Sortie : `resultat_oyibo_conservation_v0.json` (horodatages C0a, toutes les lectures, verdict, exit code). Aucune dépendance réseau.

---

> *Noether a donné le pont : symétrie ⟹ conservation. Oyibo a étendu le pont à l'échelle et nommé l'exposant 1/φ. Ce dépôt demande au nombre lui-même s'il accepte le poste — et si la machine dit non, le maillon sera consigné tel qu'il est, avec le prix.*
