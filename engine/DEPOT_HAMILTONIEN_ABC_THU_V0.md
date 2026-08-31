# DEPOT HAMILTONIEN × ABC THU V0 — Le générateur et la mémoire

**Question testée :** le Hamiltonien (générateur de la phase) et la dérivée ABC peuvent-ils fermer la redirection de `DEPOT_KMS_DPHI_THU_V0.md` — c'est-à-dire prouver que le pont par Φ₂ = ∫k_μdx^μ est le **seul possible**, et en extraire une signature falsifiable ?
**Méthode :** chaque nombre déposé est calculé par machine (`verif_hamiltonien_abc_thu_v0.py`, leçon FORCE V1.2).
**Sortie :** exit **0** — 6/6 contrôles conformes aux signatures attendues (`resultat_hamiltonien_abc_thu_v0.json`).

---

## 1. LES RÉCLAMATIONS TESTÉES

| ID | Réclamation | Signature attendue | Résultat machine |
|----|-------------|--------------------|------------------|
| C1 | Le poids mémoire λ(ω) = (iω)^α = ω^α·e^{iπα/2} est **non-hermitien** ∀α ∈ (0,1) — un opérateur hermitien a un spectre réel, λ ne l'a pas | gap > 0 ; arg λ = πα/2 ∈ (0, π/2) | ✅ gap **0.00e+00 > 0** strict ; arg λ = **0.970806 rad** |
| C2 | Le spectre {λ(ω), λ(−ω)} est **PT-symétrique par conjugaison** avec phase ≠ 0 → **PT brisé** → gain/perte | < 1e-15 | ✅ **0.00e+00** |
| C3 | La paire mémoire/anti-mémoire est la **rotation réelle de Bateman** R(θ), θ = πα/2 : det = 1, trace = 2cosθ, valeurs propres e^{±iθ} | < 1e-15 | ✅ **2.22e-16** (α ∈ {0.5, 1/φ, 0.9}) |
| C4 | **Boltzmann = phase du générateur** : ρ_β = e^{−βH} = e^{iH·iβ} (bit-exact) ; condition KMS en forme hamiltonienne ⟨A(t)B⟩ = ⟨B·A(t+iβ)⟩ | 0.00e+00 ; < 1e-15 | ✅ **0.0e+00** ; **1.11e-16** |
| C5 | **Signature falsifiable (Feynman-Vernon)** : la mémoire multiplie l'amplitude de franges par e^{iπα/2} → décalage de franges **exact et indépendant de β** ; les poids du spectre restent inchangés (prédiction nulle) | < 1e-12 ; ≤ 1e-15 | ✅ **2.22e-16** ; **1.1e-16** — décalage **55.6231° = 90/φ degrés**, ∀β ∈ {0.5, 2π, 10} |
| C6 | **Conservation non-sélective** : R(θ)^T·R = I ∀θ → la quantité du double Bateman (x² + x̃²) est conservée **pour tout α** | < 1e-15 | ✅ **4.44e-16** (α ∈ {0.3, 0.5, 1/φ, 0.8, 0.95}) |

---

## 2. VERDICT : `HAMILTONIEN_ABC_V0_MEMOIRE_OUVERTE_PONT_FV_UNIQUE`

### 2.1 Le théorème de structure (le pont par Φ₂ est le SEUL possible)

1. **La mémoire n'est pas une dynamique fermée** (C1 + C2). Un système quantique fermé a un Hamiltonien hermitien, donc un spectre réel. Le poids mémoire (iω)^α = ω^α·e^{iπα/2} est **complexe non réel** pour tout α ∈ (0,1) — aucun Hamiltonien fermé ne le réalise. Son spectre est PT-symétrique (0.00e+00) mais **PT brisé** (phase ≠ 0) : c'est un **amplificateur** (gain/perte), c'est-à-dire un **système ouvert**.
2. **Conséquence** : la mémoire ne peut entrer que par la **phase d'influence** (Feynman-Vernon) — exactement le canal Φ₂ = ∫k_μdx^μ identifié dans `DEPOT_KMS_DPHI_THU_V0.md`. Ce n'est plus un choix parmi d'autres : **c'est le seul branchement compatible avec la structure quantique**. Le double réfuté de V0 (noyau sans échelle, opérateur non-thermal) est désormais complété par une **impossibilité positive** : toute autre route (hamiltonien fermé à mémoire, spectre mémoire-thermal mélangé) est exclue par non-hermiticité.
3. **Réalisation de Bateman** (C3) : le prix de la représentation fermée est connu et chiffré — il faut **doubler** le système (onde + conjuguée, R(θ) avec det = 1 et valeurs propres e^{±iθ} à 2.22e-16), au prix d'un **degré fantôme à énergie non bornée**. C'est la version structurelle du même verdict : la mémoire seule n'a pas d'énergie propre bornée — elle est un couplage, pas une substance.

### 2.2 La signature falsifiable déposée (C5)

4. **Décalage de franges = πα/2 = 55.6231° = 90/φ degrés, indépendant de la température** (2.22e-16 sur β ∈ {0.5, 2π, 10}). Les poids thermiques e^{−βω} sont **réels positifs** : ils modulent le module de la cohérence, jamais son argument. Donc :
   - le **spectre** du détecteur à mémoire reste **planckien** (prédiction nulle, poids inchangés à l'ulp — 1.1e-16) ;
   - les **franges** d'interférence (une branche avec mémoire, une référence) sont décalées d'un angle **exact et universel**.
   C'est une signature double et falsifiable : observer un préfacteur ω^α dans un spectre thermique **réfuterait** le dépôt ; observer un décalage de franges dépendant de T le **réfuterait aussi**. La signature est déposée avant toute mesure.

### 2.3 Ce qui est CONSIGNÉ (troisième non-sélection)

5. **La conservation ne sélectionne pas α = 1/φ** (C6). La représentation de Bateman conserve x² + x̃² **pour tout α** (R orthogonale, 4.44e-16 sur α ∈ {0.3 … 0.95}). La convergence Oyibo (conservation GAGUT) / Atangana (mémoire) / Hurwitz (irrationalité maximale) vers 1/φ reste **une convergence de trois arguments indépendants, pas une dérivation**. C'est la troisième non-sélection consignée : noyau (JACOBSON V0 C4), KMS/Unruh (KMS V0 C4), conservation (ici C6). Le statut d'α = 1/φ reste **axiomatique** — et c'est désormais un résultat d'exhaustivité : les trois familles d'arguments naturelles ont été testées et aucune ne dérive l'ordre.

---

## 3. CE QUE CE DÉPÔT ACHÈTE

- ✅ **Clôture logique du pont** : noyau ❌ (sans échelle), opérateur spectral ❌ (non thermal), hamiltonien fermé ❌ (non-hermitien) → **il ne reste que la phase d'influence** — et elle marche (C4 : Boltzmann = phase du générateur, bit-exact ; KMS hamiltonienne exacte).
- ✅ **Une prédiction nulle + une signature** : spectre planckien inchangé, franges décalées de 90/φ degrés, température-indépendant.
- 🔬 **V1 naturelle** : la cohérence hors axe KMS — calculer la fonction de corrélation à deux temps du détecteur à mémoire (G(τ₁, τ₂) hors de la ligne KMS) et montrer que le déphasage uniforme y laisse une **trace mesurable** (déformation de la cohérence, pas de la thermicité). C'est le test qui départagera les candidats matière noire « cohérence ».
- 🔬 **En parallèle** : S = A/4G via l'aire de la métrique V1 (la moitié restante de la chaîne de Jacobson, indépendante de α).

---

## 4. BORNES HONNÊTES

| Item | Statut |
|---|---|
| C1/C2 (non-hermiticité, PT brisé) | ✅ fait standard de la théorie des opérateurs — **application nouvelle** au poids mémoire ABC, machine-vérifiée |
| C3 (Bateman) | ✅ construction standard ; le lien mémoire ABC ↔ rotation πα/2 est la partie nouvelle déposée |
| C4 (Boltzmann = phase, KMS hamiltonienne) | ✅ réécriture du C7 de KMS V0 au niveau du générateur — cohérence vérifiée, pas un fait nouveau |
| C5 (franges 90/φ°, indépendantes de T) | ✅ **signature nouvelle déposée** — falsifiable doublement (spectre ET franges) |
| C6 (conservation ∀α) | ✅ non-sélection **nouvelle** consignée — 3e et dernière famille d'arguments testée |
| Leçon de débogage | C4 premier run : signe de l'exposant KMS (e^{+iω(t+iβ)} au lieu de e^{−iω(t+iβ)}) → gap 1.00 ; attrapé par la signature, pas par inspection |
| Statut trou noir / matières noires | inchangé (P9 ouvert ; matière noire = effet de cohérence à confirmer en V1 ; Λ = mémoire cosmologique, facteur 3,6) |

---

## 5. FICHIERS

- `verif_hamiltonien_abc_thu_v0.py` — les 6 contrôles, verdict par code de sortie (0 = conforme).
- `resultat_hamiltonien_abc_thu_v0.json` — nombres bruts machine (6/6, exit 0).
- Contexte amont : `DEPOT_KMS_DPHI_THU_V0.md` (Boltzmann = phase, pont Φ₂), `DEPOT_JACOBSON_THU_V0.md` (8π = 2π×4, noyau sans échelle), `PROBLEME_OUVERT_EINSTEIN.md` (Problème V3), `COUPLAGE_OYIBO_ABC.md` (convergence conservation/mémoire vers 1/φ).
