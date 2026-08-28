# RÉSULTAT JAUGAGE V0 — la covariance locale est dérivée, la force reste sans nom

| | |
|---|---|
| **Date d'exécution** | 28/08/2026 08:43:30 (dépôt 08:24:38 — C0a ✓, 19 min d'antériorité) |
| **Dépôt** | `DEPOT_JAUGAGE_V0.md` (fermé, non modifié — I5) |
| **Script** | `verif_jaugage_v0.py` (447 lignes, python 3.11.8, numpy 1.26.4) |
| **Journal** | `resultat_jaugage_v0.json` — 36 + 72 + 36 + 3 + 32 + 3 + 5 lectures, toutes consignées |
| **Verdict** | **V3 — COVARIANCE_LOCALE_DERIVEE_FORCE_SANS_NOM — exit 0** |

---

## 1. Contrôles bloquants : 8/8 OK

| # | Contrôle | Résultat |
|---|----------|----------|
| C0a | dépôt antérieur à l'exécution | mtime 08:24:38 < 08:43:30 |
| C0b | φ² = φ+1 | écart 0.0e+00 |
| C1 | K̂ complexe vs forme réelle (grille entière + {½, 1/φ, 1}) | **1.24e-16** — barre 1e-12 |
| C2 | transparence mode ½ : φ+φ⁻¹ = √5 | écart 0.0e+00 → R_tour(½) = 1 |
| C3 | CODATA 2022 | 137.035999177 consignée |
| C4 | ancre 5-facteurs (T0) | 137.036031356428 ; écart 3.12e-12 — **identique au 27/08** |
| C5 | impédance \|K̃(½)\|² double route | 0.4011522499939087 — **reproduction bit-exacte**, écart 0.00e+00 |
| C6 | D₂ réintégrée, route 27/08 | 0.54518249 ; écart registre 3.91e-9 ; stabilité 3.6e-7 — **identique au 27/08** |

## 2. Famille A — le défaut existe, il est gradient-porté, le U(1) est exact

- **A1 (le coût)** : les 36 défauts D(a,k) sont **tous non nuls**, de 1,878×10⁻³ (a=0,1) à 0,7910 (a=5). Le noyau K̂ ne commute PAS avec le rephasage modulé — il y a un prix, mesurable.
- **A2 (le U(1) global)** : dérive max **1,11×10⁻¹⁶** sur les 72 lectures (θ₀ ∈ {π/3, π/2}) — le noyau est aveugle au rephasage constant à la précision machine. Le U(1) résiduel de la fiche U(1) (Maillon 3) est possédé **exactement**.
- **A3 (le gradient)** : dérive au doublement 0,1→0,2 : 6,7×10⁻⁵ (k=0,1) à 5,8×10⁻³ (k=0,5), toutes « 6,7e-3 « la barre 5 %. La réponse est **linéaire dans l'amplitude** : χ(k) := D(0,1,k)/0,1 est une fonction propre du gradient — la structure de compensateur existe.
- **TN-A (discrimination)** : dérive 2→5 : 5,2 % (k=0,1), **50,3 %** (k=1), **61,0 %** (k=10) — le régime non linéaire est détecté, la lecture A3 n'est pas vide.

## 3. Famille B — la force : G* = 0,32328801, aucun nom fermé (0/16)

**G\* = χ_{0,1}(k=1) = 0,32328801** (χ = 0,0323288 divisé par a = 0,1 ; R_tour(½) = 1).

**0 hit sur 16 candidats, 32 lectures.** Meilleurs manqués (tous très au-dessus des barres) :

| Candidat | Écart | Lecture |
|---|---|---|
| \|K̃(½)\|² = 0,4012 | **19,4 %** | G*/c = 0,806 |
| e^{−1/φ} = 0,5390 | 40,0 % | G*/c = 0,600 |
| D₂ = 0,5452 | 40,7 % | G*/c = 0,593 |
| 1/φ = 0,6180 | 47,7 % | G*/c = 0,523 |

**Le [OBS] du §7 de l'exploration est tranché négativement** : 1/D₂ = 1,8342 n'est PAS la force du défaut de commutation (rapport direct 5,67 ; écart inverse 40,7 %). La proximité 1,8324 ↔ 1/D₂ à 1,0×10⁻³ reste vraie **en arithmétique** mais ne porte pas ce mécanisme — à ce niveau V0, c'est une coïncidence non expliquée, comme l'ancre 5-facteurs.

**TN-B (spécificité)** : graines 27/28/29 → G_r = 2,639 / 5,891 / 1,661, tous très loin de G\*, zéro hit commun. Le défaut mesuré est spécifique au gradient simple, pas un artefact de profil.

Lecture brute consignée **sans aucune revendication** (I5-B : aucun candidat ajouté après coup) : φ/G\* = 5,0049. Si un dépôt futur veut tester la pentade, il fera l'objet d'un dépôt daté propre — pas d'une proximité.

## 4. Famille C — running : β_pred = −0,465, consigné sans verdict

| ω₀ | 0,1 | 0,5 | 1 | 2 | 10 |
|---|---|---|---|---|---|
| χ(ω₀) | 0,028676 | 0,028869 | **0,032329** | 0,013401 | 0,003488 |

β_pred (pente ln χ vs ln ω₀) = **−0,4655**. Non-monotonie : maximum local au porteur de référence ω₀ = 1. Sous le dictionnaire D+ (ω↑ ⇔ μ↑, direction attendue par la tripartition) : **désaccord** ; sous D− (ω↑ ⇔ μ↓) : accord. Dictionnaire μ↔ω absent (trou D4) → lecture consignée **sans pouvoir de verdict**, exactement comme déposé.

## 5. Ce que V0 a établi — et ce qu'il n'établit pas

**Établi [T, machine, 8/8 contrôles] :**
1. Le noyau K̂ possède le U(1) global **exact** (1,1×10⁻¹⁶).
2. Le rephasage modulé coûte quelque chose de mesurable, **linéaire dans l'amplitude**, **porté par le gradient** — la structure de compensateur existe (le défaut a la bonne covariance pour être fermé par un champ).
3. La force de ce défaut au porteur de référence est **G\* = 0,32328801** — première force machine du rephasage local, et elle **ne porte aucun des 16 noms fermés** du registre.

**Pas établi (honnêteté, dépôt §6) :**
- Pas de −¼F² : le compensateur dynamique (trou D3) reste ouvert.
- Pas de dictionnaire μ↔ω (trou D4) : β_pred = −0,4655 est un diagnostic, pas un verdict.
- Pas de U(1)_Y, pas d'électrofaible ; strictement U(1) abélien sur un porteur.
- La tripartition α_W/α_EM/α_S reste **[P]** — et perd son candidat-force 1/D₂ pour le canal EM : la question « pourquoi 1,8324 ? » est **toujours ouverte**, le jaugage V0 n'y a pas répondu.
- Le trou D1 est **partiellement fermé** : liberté locale dérivée au sens structurel (U(1) exact + gradient-porté + linéarité), pas au sens dynamique.

Prochaine marche naturelle (si l'utilisateur la souhaite, par dépôt daté) : V1 — étendre le registre des forces (G\* comme 17ᵉ objet fermé, tests de fermeture φ/5, G\*·φ, G\*·D₂…), ou attaquer D3 (le compensateur dynamique : chercher le champ χ(x) qui ferme la covariance au premier ordre).

---

> *Le noyau paie, c'est maintenant mesuré : 0,32328801 par unité de gradient. Mais le prix ne porte encore aucun nom de ses propres registres. Le trou a une structure — il n'a pas de monnaie.*
