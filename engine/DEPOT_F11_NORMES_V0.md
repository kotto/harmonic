# F11 NORMES V0 — L² survivant du filtre α→1 ; α=1/φ : la phase survit, pas la norme

**Verdict : `F11_NORMES_V0_C_H1_PRELIMINAIRE` — exit 0 (5/5 contrôles)**
**Date : 1er septembre 2026**
**Script : `verif_f11_normes_v0.py`** (mpmath dps=80, seeds fixes 7/11/13)
**JSON : `resultat_f11_normes_thu_v0.json`**
**Référence : `FRONTIERE_F11_HILBERT.md` (Voie 1, critère C-H1), `MEMOIRE_SCIENTIFIQUE_THU.md` (F11)**

---

## 0. La question (issue du dialogue)

> « L'espace de Hilbert est-il le seul survivant de l'espace vectoriel THU ? »

La formulation exacte que ce dépôt fige :

> **L² est le seul survivant du filtre α→1 ; à α=1/φ, ce qui survit n'est plus
> la norme mais la phase — Hilbert reste l'arène.**

Ce dépôt est la **première évidence machine du critère C-H1** de F11 (norme L²
*privilégiée*). Il n'est **pas** C-H2 (unicité universelle) : un probe fini
n'est pas un théorème. F11 reste **ouverte**.

---

## 1. Dispositif

- Dynamique THU : ψ(t) = V · E_{1/φ}(−iΛt^{1/φ}) · V†ψ₀ (décomposition spectrale
  d'un H hermitien **mélangeur** 6×6, gaussien, seeds fixes).
- Filtre α→1 : évolution unitaire e^{−iHt} (forme close exacte).
- Mémoire : α = 1/φ = 0.618033988749895, série de Mittag-Leffler en
  **termes directs** zⁿ/Γ(αn+1), mpmath dps=80 (float64 insuffisant : annulation
  catastrophique dès |z| ≈ 15).
- Normes rivales testées : L¹, L², L⁴, L^∞ ; t ∈ [0.05, 6.0], 100 points.
- Mesure : max_t | ‖ψ(t)‖_p / ‖ψ(t₀)‖_p − 1 |.

---

## 2. Contrôles (nombres déposés, recalculables)

| C | Contrôle | Résultat | Seuil | Statut |
|---|---|---|---|---|
| **C1** | Sanity Mittag-Leffler : E₁(1)=e, E_{½}(−1)=e·erfc(1) | err = **0.000e+00** (80 chiffres) ; décroissance 0.3498 > 0.0874 > 0.0427 | err < 1e-40, strictement décroissante | ✅ |
| **C2** | **Filtre α→1 : L² conservée machine-exact** (3 seeds) | worst = **4.44e-16** | < 1e-14 | ✅ |
| **C3** | **Sélection non vide** : les rivales dévient (min sur 3 seeds) | min(L¹,L⁴,L^∞) = **7.606e-02** (jusqu'à 3.43e-01) | > 0.05 | ✅ |
| **C4** | **α=1/φ : AUCUNE norme conservée** (mémoire = système ouvert) | min sur toutes normes = **6.723e-01** | > 0.3 | ✅ |
| **C5** | **α=1/φ : contraction L²** — \|E_α(−iy)\| ≤ 1 sur grille dense (240 pts, y ≤ 12) et ‖ψ(t)‖₂ ≤ ‖ψ₀‖₂ le long des trajectoires | max\|E\|−1 = **0.000e+00** ; max ratio−1 = **0.000e+00** | ≤ 1e-12 | ✅ |

**Lecture** :
- **C2 vs C3** : au filtre unitaire (α→1), L² est conservée à 4.44e-16 pendant
  que ses rivales dévient de 7.6% à 34% — la sélection n'est ni vide ni truquée
  (le H mélangeur redistribue réellement l'amplitude entre composantes).
- **C4** : à α=1/φ, même L² n'est plus conservée (déviation ≥ 67%) — cohérent
  avec le théorème déposé (`DEPOT_HAMILTONIEN_ABC_THU_V0`) : le poids (iω)^α
  est non-hermitien, la mémoire est un **système ouvert**.
- **C5** : mais la mémoire n'amplifie jamais — \|E_α(−iy)\| ≤ 1 ∀y (contraction
  L² exacte sur la grille). C'est le même prix que celui déposé en CHSH THU V0
  (« la mémoire amortit l'intrication au prix déposé »), maintenant démontré
  comme contraction de norme : **la mémoire amortit, n'amplifie pas.**

---

## 3. Portée F11 — ce qui est établi, ce qui ne l'est pas

| Critère F11 | Statut |
|---|---|
| **C-H1** (L² *préliminaire*) | ✅ **première évidence machine** — sur la famille L^p {1, 2, 4, ∞}, 3 seeds, fenêtre t ∈ [0.05, 6] |
| **C-H2** (L² *unique* parmi toutes les normes) | ❌ non établi — exige le **théorème** : Jordan–von Neumann (loi du parallélogramme ⟺ norme hilbertienne) + réversibilité/symétrie (Wigner–Bargmann) |
| **C-H3** (théorème spectral sans postuler Hilbert) | ❌ non abordé — Voie 3 de `FRONTIERE_F11_HILBERT.md` |

**Falsifiabilité** (héritée de F11) : si une norme non-hilbertienne (ex. Banach
non-Hilbert) se révèle conservée par le filtre α→1 dans une classe élargie,
C-H1 est **réfutée** et ce dépôt le consignera.

**Rappel anti-transitivité** (cf. discussion) : « Schrödinger ⊢ depuis l'équation
mère » et « Schrödinger présuppose Hilbert » n'impliquent PAS « équation mère ⊢
Hilbert » — la présupposition (⊨) n'est pas la dérivabilité (⊢) ; croire le
contraire rendrait la preuve circulaire (Hilbert entre à l'étape 4 de la chaîne).
C-H3 est la seule route non circulaire, et elle reste ouverte.

---

## 4. Leçons consignées (mise au point — 4 défauts attrapés par la machine)

1. **H diagonal = piège trivial** : une évolution en phases pures conserve
   *toutes* les normes L^p — la sélection exige un **mélangeur** (H non diagonal).
   Premier probe invalide, refait.
2. **Récurrence Mittag-Leffler décalée d'indice** : z/(αn+1) au lieu de z/n
   pour α=1 → (e^z−1)/z, une AUTRE fonction, silencieusement. Détecté par la
   violation de l'unitarité L² (déviation 0.725 impossible).
3. **Produit de gammas** : récurrence multiplicative term·z/Γ(αk+1) divise par
   Γ à CHAQUE pas au lieu de calculer zⁿ/Γ(αn+1) — détecté par déviations
   1e3–1e7 (garbage), corrigé en **termes directs** + sanity sur formes closes.
4. **float64 insuffisant à α=1/φ** : annulation catastrophique (termes ~10³³
   contre somme O(1)) → **mpmath dps=80 obligatoire** ; sanity E₁(1)=e et
   E_{½}(−1)=e·erfc(1) déposées à 0.000e+00.

*(+ un `IndentationError` sur un return tuple multi-lignes — attrapé à la
compilation, consigné pour l'exemple.)*

---

## 5. En une phrase

> **Le filtre α→1 élimine toutes les normes L^p sauf L² (4.44e-16 contre
> 7.6–34%) ; à α=1/φ aucune norme ne survit mais la mémoire contracte L² sans
> jamais amplifier (0.000e+00) — Hilbert est l'arène sélectionnée par la limite
> sans mémoire, et la phase y est le seul survivant de la mémoire.**

---

*Références : `FRONTIERE_F11_HILBERT.md` (énoncé F11, Voie 1, C-H1/C-H2/C-H3) ;
`DERIVATION_SCHRODINGER_FRACTIONNAIRE.md` (chaîne mère→Schrödinger, α→1) ;
`DEPOT_HAMILTONIEN_ABC_THU_V0.md` (non-hermiticité, système ouvert) ;
`DEPOT_COHERENCE_KMS_THU_V1.md` (phase θ=πα/2, réversibilité G_mem·e^{−iθ}=G₀) ;
`DEPOT_CHSH_THU_V0.md` (la mémoire amortit au prix déposé).*

*— FIN — verdict F11_NORMES_V0_C_H1_PRELIMINAIRE, exit 0, 5/5.*
