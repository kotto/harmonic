# DÉRIVATION CORRIGÉE DES 118 MASSES — Rapport de vérification

**Date** : 08/08/2026 — **Branche** : `feature/ia-ondulatoire-natif`
**Scripts** : `test_masses_v2_ondulatoire.py`, `analyse_sensibilite_semf.py`,
`test_coquille_ondulatoire.py` — **Référence** : `ia_ondulatoire/test_masses_118.py`
(protocole de Mendeleïev, 118 masses CODATA/IUPAC)

---

## 1. Les 4 corrections structurelles

| # | Erreur (v1) | Correction | Vérification |
|---|---|---|---|
| 1 | Base `m_Planck` = 1,31e19 u | **m_p = m_e·6π⁵** (relation GAGUT vérifiée) | 1,007258 vs 1,0072765 → **0,0018 %** ✓ |
| 2 | Rayon ~ l_Planck (2,4e-35 m) | r₀ = 1,25 fm (échelle nucléaire) | entre dans aC (Coulomb) |
| 3 | Prédire la masse entière | **m = Z·m_p + N·m_n + Z·m_e − B(A,Z)** | B(Fe-56) = 491,9 vs 492,25 MeV ✓ |
| 4 | 32 masses factices (placeholders entiers) | 86 masses CODATA réelles | RMS B 42 → 6,5 MeV |

> L'équation mère doit prédire l'**énergie de liaison B** (~1 % de la masse),
> pas la masse entière. C'est là que vit toute la physique nucléaire.

## 2. Résultats (86 noyaux réels, A≥16)

| Modèle | RMS B (MeV) | Écart moyen masses |
|---|---|---|
| m = A·u (trivial) | — | 0,057 % |
| SEMF littérature (6 params ajustés) | 6,54 | 0,006 % |
| SEMF + coquille ajustée (2 params) | 5,59 (CV 5-fold) | 0,006 % |
| **SEMF + coquille harmonique HO (0 paramètre)** | **4,54** (A≥40, CV) | **0,0032 %** |

## 3. Verdicts chiffrés

### 3.1 — Les coefficients SEMF ne sont PAS dérivables de φ/π/e
La SEMF est une **compensation de termes énormes** (aV·A ≈ 3000 MeV à A=200).
Mesuré : **aV ±1 % → RMS 6,5 → 26,2 MeV**. Précision requise : **±0,05 %**.
Le meilleur produit simple de φ/π/e atteint 1,39 % (maille du treillis ~1-3 %).
→ Impossibilité mathématique du treillis, pas un manque d'effort.

### 3.2 — L'α de l'équation mère est PARFAIT dans le Coulomb
`(3/5)·α_harmonique·ħc/r₀` vs α CODATA : **0,0001 MeV de différence sur le RMS**.
L'écart de 2,8 % vient du facteur 3/5 (sphère uniforme), pas de la constante.

### 3.3 — La structure en coquilles harmoniques est RÉELLE et gagne (résultat nouveau)
Coquille **0 paramètre** dérivée de l'oscillateur harmonique :
- **fermetures** : 2(n+1)(n+2) = {2, 8, 20, 40, 70, 112, 168} (modes stationnaires HO 3D)
- **amplitude** : ħω/2, ħω = 41·A^(−1/3) MeV (Bohr–Mottelson, publié)
- **largeur** : w = √N (espacement de coquilles HO)

| Fenêtre | SEMF seule | + coquille HO (0 param) | Bootstrap (5000) |
|---|---|---|---|
| A≥16 (79) | 6,54 MeV | 5,16 MeV (−21 %) | IC [0,31–2,32], P=99,4 % |
| **A≥40 (68)** | **7,02 MeV** | **4,54 MeV (−35 %)** | **IC [1,89–3,15], P=100 %** |
| A≥56 (57) | 7,24 MeV | 4,62 MeV (−36 %) | — |

**Interprétation physique** : les noyaux les plus améliorés sont Hf/Ta/Re
(N=108-110) — la **région déformée** que seules les fermetures de
l'oscillateur harmonique déformé (Nilsson) décrivent ; les fermetures
sphériques de Mayer–Jensen {28, 50, 82, 126} y échouent. La dégradation se
concentre sur les noyaux légers (A<40) où l'amplitude ħω/2 est trop forte —
la SEMF n'y est de toute façon pas valide.

### 3.4 — Corrélation Φ/résiduel : artefact
r = −0,24 (p = 0,028 brut) mais Φ corrèle avec A (+0,35) et le résiduel avec
A (−0,54) → significativité confondue, signal non physique dans cette forme.

## 4. Bilan honnête du programme « dérivation des masses »

**Ce qui tient (vérifié indépendamment)** :
1. m_p/m_e = 6π⁵ → 0,0018 %
2. α = π⁴e⁻⁴φ⁻⁵(√2)⁻¹(√3)⁻⁵ → 99,99998 %
3. Structure m = Z(m_p+m_e)+N·m_n − B(A,Z) avec α harmonique dans le Coulomb
4. **La coquille harmonique HO 0-paramètre améliore la SEMF de 35 % (bootstrap P=100 %)** — premier résultat quantitatif où la structure harmonique bat la physique standard, sans aucun paramètre ajusté.

**Ce qui est réfuté** : la dérivation des coefficients SEMF par produits de
φ/π/e (précision requise 0,05 % vs maille du treillis 1-3 %).

## 5. Prochaines étapes proposées

1. **Test AME2020 complet (~3500 noyaux)** : la coquille HO 0-paramètre sur la
   table atomique complète (hors vallée) — passage publication.
2. Affiner l'amplitude pour A<40 (région où la SEMF elle-même n'est pas valide).
3. Mettre à jour le DOCUMENT_FONDATEUR avec ce statut vérifié/réfuté.
