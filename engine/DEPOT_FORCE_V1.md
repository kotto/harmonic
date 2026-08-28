# DÉPÔT FORCE V1 — la forme close de la force G* (diffusion fréquentielle du noyau)

**Date de dépôt** : 28/08/2026 (après CHSH V0, verdict V+ — commit a7e02f8)
**Statut** : dépôt FERMÉ. Écrit AVANT tout script (contrôle C0a). Aucune barre, lecture ou verdict modifiable après exécution (I5).

---

## §0 — Hypothèse falsifiable [H]

Le jaugage V0 a mesuré la force du rephasage modulé **G\* = 0,32328801** (0/16 noms fermés, verdict V3 « force sans nom »). Le dépôt V1 pose l'hypothèse suivante, sans paramètre libre :

> **[H]** Le défaut de commutation D(α, ψ) du noyau K̂ n'est pas un nombre orphelin : c'est **exactement la diffusion fréquentielle du noyau sous la modulation** — la décomposition de Jacobi–Anger `e^{ia·cos(kx)} = Σₙ iⁿ Jₙ(a)·e^{inkx}` (identité ponctuelle, exacte) croise l'action diagonale du noyau (C4 du jaugage : K̂[e^{iωx}] = K̂(ω)·e^{iωx} à 1e-15 sur les bins) pour donner la **forme close ex ante** :
>
> **χ(ω₀, a, k) = √( Σ_{n≥1} Jₙ(a)² · ( |K̂(ω₀+nk) − K̂(ω₀)|² + |K̂(ω₀−nk)−K̂(ω₀)|² ) ) / ( a · |K̂(ω₀)| )**
>
> fréquences **signées sur la grille** (branche principale, K̂(−ω) = conj(K̂(ω))), troncature |n| ≤ 11 (J₁₂(0,1) ≈ 5×10⁻²⁵, invisible). Le défait D = χ·a.

Trois conséquences déposées ex ante (chacune falsifiable, aucune sauvetable) :

1. **C1–La forme** : pour les 17 lectures de la famille A (§2), |χ_machine − χ_pred|/χ_pred ≤ 1e-9. La dérive de linéarité A3 du V0 (barre 5 % au doublement a = 0,1 → 0,2) devient une **prédiction exacte** : χ(0,2,1) est prédit par la même forme close, courbure de Bessel comprise.
2. **C2–La reproduction** : χ_pred(1, 0.1, 1) = G\* registre = 0,3232880100102466 à 1e-8 près (relatif).
3. **C3–La station** : argmax de χ sur la grille fermée des 14 porteurs = **ω₀ = 1,0** (le porteur de référence du V0 est le porteur du maximum du défaut). Si 0,8 ou 1,3 gagne → divergence consignée, verdict V2.

Si (1) échoue sur une seule lecture : **REFUTE exit 1** — le défaut n'est PAS la diffusion fréquentielle du noyau, la forme close est fausse. Aucun sauvetage (ajustement de troncature, de branche ou de barre interdit).

## §1 — Objets fermés

| # | Objet | Valeur fermée |
|---|---|---|
| O1 | φ, α = 1/φ | φ = (1+√5)/2 ; α = 0,6180339887… |
| O2 | Noyau K̂ | K̂(ω) = φ/((iω)^α + φ), branche principale, K̂(0) = 1, deux routes (complexe / réelle développée) |
| O3 | Treillis | N = 512, L = 20π, Δω = 0,1, Nyquist = 25,6 (tous modes sur bins entiers) |
| O4 | Registre (16) | D₂ = 0,54518249 ; \|K̃(½)\|² = 0,4011522499939087 ; impédance = 2,492819122951908 ; φ, φ², 1/φ, √5, 2φ, 2, 5, 1/5 ; F₁₀ = 55 ; L₁₀ = 123 ; e^{±1/φ} ; ancre 137,036031356 ; 1/ancre ; facteur [OBS] 1,8324104102898406 |
| O5 | Norme | ‖ψ‖² = Σ\|ψₙ\|²/N (Parseval, unitaire) |
| O6 | Porteurs (famille A) | grille Fermat-de-Fibonacci × 0,1 ∪ passages V0 : **{0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.3, 2.0, 2.1, 3.4, 5.5, 8.9, 10.0, 14.4}** (bins 1,2,3,5,8,10,13,20,21,34,55,89,100,144) — 14 porteurs, tous ≤ 14,4 ; no-wrap vérifié : max \|ω₀ ± 11\| = 25,4 ≤ Nyquist 25,6 |
| O7 | Bessel | Jₙ(a) par série Jₙ(a) = Σ_{m≥0} (−1)ᵐ (a/2)^{2m+n} / (m!(m+n)!) |
| O8 | Barres | TOL_FORME = 1e-9 (relatif, famille A) · TOL_GSTAR = 1e-8 · TOL_HIT = 1e-4 · TOL_HIT_PLUS = 2,355e-7 · TOL_U1 = 1e-9 · TOL_C0B = 1e-15 · TOL_C = 1e-12 |
| O9 | **G\* (17ᵉ objet)** | **G\* = 0,3232880100102466** (jaugage V0, 28/08, lecture χ(1, 0.1, 1) ; statut : mesuré — la présente campagne teste sa forme) |
| O10 | Références de modulation | a ∈ {0.1, 0.2}, k ∈ {0.5, 1.0, 2.0} — fermés, bins entiers |

## §2 — Familles

### Famille A — la forme close (17 lectures, verdict-porteuses)
1. **A1 balayage des porteurs** : χ_machine(ω₀, 0.1, 1) sur les 14 porteurs O6 (voie machine : `defaut` du V0, clonée à l'identique) ; χ_pred(ω₀) par la forme close §0 (fréquences signées, troncature 11). Barre : écart relatif ≤ 1e-9 sur CHACUNE des 14 lectures.
2. **A2 la dérive prédite** : χ(1, 0.2, 1) machine vs forme close (Jₙ(0.2)) — barre 1e-9. La dérive V0 de 5 % devient une prédiction exacte.
3. **A3 le gradient prédit** : χ(1, 0.1, 0.5) et χ(1, 0.1, 2.0) machine vs forme close — barre 1e-9 chacune.
4. **A4 G\*** : |χ_pred(1, 0.1, 1) − 0,3232880100102466| ≤ 1e-8.
5. **A5 la station (verdict-porteuse)** : argmax de χ_machine sur la grille O6 = ω₀ = 1,0.

### Famille B — fermeture composée du registre (lecture [OBS], AUCUN pouvoir de verdict)
G\* comme 17ᵉ objet : balayage composé {G\*·c, G\*/c, c/G\*} pour c ∈ O4, confronté aux cibles O4 ∪ {√2, π, e} — toutes les lectures consignées, barres TOL_HIT (1e-4, géométrique) / TOL_HIT_PLUS (2,355e-7, continuité).
- **Tête de liste déposée : φ/5 = 0,323606797…** — attendu **manqué** (écart relatif prédit ≈ 9,86e-4 > 1e-4). Consigné comme quasi-échec honorifique si confirmé.
- **Avertissement comparaisons multiples** : ≈ 1 000 lectures à barre 1e-4 → ~0,1 faux hit attendu. Tout hit est un **[OBS] pour dépôt daté futur**, jamais une revendication de cette campagne (I5-B : aucun candidat ajouté après coup).

### Famille C — diagnostics sans verdict (trou D4 ouvert)
- β_inf (pente ln χ vs ln ω₀, porteurs < 1) et β_sup (porteurs > 1) — consignés, sans verdict (dictionnaire μ↔ω toujours absent).
- Table χ·ω₀ — consignée, sans verdict.
- Lectures asymptotiques éventuelles lues APRÈS coup = diagnostics, jamais des prédictions.

## §3 — Contrôles bloquants (un seul échec ⟹ V4 REFUTE exit 1)

| # | Contrôle | Barre |
|---|---|---|
| C0a | mtime dépôt < exécution | — |
| C0b | φ² = φ+1 | 1e-15 |
| C1 | K̂ double route (complexe vs réelle) sur grille O3 + {½, 1/φ, 1, 2} | 1e-12 |
| C2 | Jₙ double route : série vs récurrence ascendante/descendante (a ∈ {0.1, 0.2}, n ≤ 11) | 1e-12 |
| C3 | Jacobi–Anger PONCTUEL sur le treillis : max \|e^{ia·cos(kx_j)} − Σ_{\|n\|≤11} iⁿJₙ(a)e^{inkx_j}\| pour (a,k) ∈ {(0.1,1), (0.2,1), (0.1,0.5), (0.1,2)} | 1e-12 |
| C4 | action propre du noyau : K̂[e^{iω₀x}] = K̂(ω₀)e^{iω₀x} sur 3 porteurs {0.1, 1.0, 14.4} | 1e-12 |
| C5 | reproduction de la voie V0 : χ_machine(1, 0.1, 1) = G\* registre O9 | 1e-8 |
| C6 | U(1) aveuglement spot : D(α+θ₀) − D(α) sur 2 profils (θ₀ ∈ {π/3, π/2}, a=0.1, k=1, ω₀=1) | 1e-9 |
| C7 | no-wrap consigné : pour chaque lecture famille A, maxₙ \|ω₀+nk\| ≤ 25,6 (sinon la lecture est exclue EX ANTE, jamais wrapée) | — |

## §4 — Verdicts (figés ex ante)

| Verdict | Condition | Sortie |
|---|---|---|
| **V+ — FORCE_FORME_FERMEE** | 17/17 lectures forme ≤ 1e-9 ET G\* reproduit ≤ 1e-8 ET argmax = 1,0 ET contrôles OK | exit 0 |
| **V2 — FORCE_FORME_PARTIELLE** | forme OK partout MAIS argmax ≠ 1,0 (station déplacée, consignée) | exit 0 |
| **V3 — REFUTE_FORCE_SANS_FORME** | au moins une lecture forme > 1e-9 : la diffusion fréquentielle n'est pas le défaut | **exit 1** |
| **V4 — REFUTE** | un contrôle bloquant en échec | **exit 1** |

## §5 — Interdictions (I1–I5)

I1 aucun angle/graine/porteur ajusté après lecture · I2 aucune barre relaxée · I3 toutes les lectures au JSON (y compris quasi-échecs) · I4 aucun lissage/moyennage déguisé · I5 le dépôt n'est plus modifiable.

## §6 — Honnêteté (ce que V1 n'établit pas)

1. La forme close **explique** la force, elle ne la **nomme** pas : dire pourquoi le noyau diffuse ainsi reste la question (la nommée −¼F² / trou D3 reste ouvert).
2. Le balayage composé (famille B) est une exploration criblée : comparaisons multiples, hits = [OBS] sans statut.
3. Le trou D4 (dictionnaire μ↔ω) n'est pas touché : β_inf/β_sup restent des diagnostics.
4. La station argmax = 1,0 est une lecture risquée assumée : 0,8 et 1,3 encadrent 1,0 et χ(0,8) pourrait gagner — si oui, V2, consigné tel quel.
5. La famille A teste le formalisme bancarisé contre une identité dérivable du même formalisme — c'est une porte de cohérence EXACTE (comme CHSH famille A), pas une découverte indépendante ; sa valeur est que l'identité aurait pu être fausse ( FFT vs somme de Bessel, troncature, branches négatives, wrap ).
6. G\* reste une force **machine** : aucune lecture expérimentale n'est revendiquée.

## §7 — Reproductibilité

`python verif_force_v1.py` → `resultat_force_v1.json` (toutes les lectures, y compris les quasi-échecs). Python 3.11.8, numpy 1.26.4, aucun autre dépendance.
