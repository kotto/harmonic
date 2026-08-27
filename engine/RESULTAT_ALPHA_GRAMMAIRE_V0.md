# RÉSULTAT MACHINE — ASSAUT « GRAMMAIRE ONDULATOIRE » SUR α (V0)

**Date d'exécution** : 27/08/2026, 22:44 (mtime dépôt 22:16 — C0a vérifié)
**Dépôt** : `DEPOT_ALPHA_GRAMMAIRE_V0.md` (27/08/2026, antérieur au script — le script n'existait pas au dépôt)
**Script** : `verif_alpha_grammaire.py` (transcription fidèle du dépôt)
**JSON** : `resultat_alpha_grammaire.json` (239 lectures, toutes rapportées)
**Transcript** : `sortie_grammaire.txt`

---

## 1. Verdict

```
ALPHA_HORS_GRAMMAIRE_STATIQUE [F] — exit 1
```

**0 hit sur 218 lectures de verdict** (0 à 2,355×10⁻⁷ comme à 1×10⁻⁴).
Conformément à la ligne V3 du dépôt §4, pré-enregistrée avant exécution :
la frontière est consignée et **la formule 5-facteurs est reclassée
coïncidence de compression** — elle reste une ancre de maintenance (contrôle C4),
elle n'est plus une feuille de route.

## 2. Contrôles bloquants — 8/8 OK

| # | Contrôle | Résultat |
|---|----------|----------|
| C0a | dépôt antérieur à l'exécution | mtime 22:16:20 < exécution 22:44:22 |
| C0b | φ² = φ+1 | 0.00e+00 |
| C1 | forme close noyau vs intégration directe | **2.00e-12** (σ=1), 4.91e-13 (σ=2) — barre 1e-8 |
| C2 | c₂ = 1/Γ(2/φ+1) = 0,889630375 | écart 2.85e-10 |
| C3 | ancre CODATA 2022 | 137,035999177 |
| C4 | maintenance d'ancre 5-facteurs | 1/T0 = 137,036031356428 ; écart ancre 3.12e-12 ; écart CODATA **2.348e-7** (= précision du corpus, justifie TOL_HIT_PLUS) |
| C5 | témoin négatif vertex | 0/15 hits, meilleur (b, π⁴) = **97,5115** reproduit exactement |
| C6 | unicité | aucun hit → non applicable |

Le REFUTE est donc un verdict **de fond**, pas un accident de pipeline :
le témoin négatif s'est comporté exactement comme déposé, et l'identité
du noyau est certifiée deux ordres de grandeur sous la barre.

## 3. Ce que la machine a vu

### Famille A — témoin négatif (15 lectures)
0/15 à 1e-4, meilleure lecture (b, π⁴) = 97,511479 — **identique à la valeur
déposée** (97,5115, facteur de manqué 1,4053). Pipeline sain.

### Famille B — normes intégrales D_p (8 candidats)
Convergence démontrée machine avant verdict (dépôt §3) :

| p | D_p (domaine étendu) | Stabilité | Statut |
|---|---------------------|-----------|--------|
| 1 | 25,34 → 18,98 → 12,61 (croissance ≈ 20/π par doublement) | 2.5e-1 | **divergent** (log-linéaire à ∞) |
| 2 | 0,54518249 | 3.6e-7 | **CONVERGE** |
| 3 | 175 → 3262 → 60374 | 9.5e-1 | **divergent** (en ω^{p(1/φ²−1)} à 0) |
| 4 | 1,3e8 → 5e12 → 1,9e17 | 1.0 | **divergent** |

Candidats admissibles : **{D₂, 1/D₂} = {0,545182 ; 1,834248}** — écarts
99,6 % et 98,7 %. **α n'est pas une norme intégrale de la ligne.**
Les 6 candidats divergents sont consignés sans réclamation.

### Famille C — chaîne dérivationnelle (216 lectures)
Meilleure lecture toutes routes confondues :

```
C2 (produit) : α⁻¹_cand = 1/(α_W · α_S · φ⁰ · e^{1/φ}) = 136,995209
écart = 2,977×10⁻⁴   (facteur 1,00030)
```

Puis chute immédiate : 1,25e-2 (C1, mêmes jauges), 4,6e-2, 6,1e-2…
Le près-manqué e^{1/φ} **confirme** le verdict négatif de l'assaut produit
K* de la session précédente (2,98e-4) : il reste à un facteur 420 de la
barre d'admission. Rien dans les 12 jauges φ^e ni les 9 témoins ne ferme
l'écart.

## 4. Découverte technique collatérale (F-C1)

Le contrôle C1 a mis au jour un **plancher d'annulation catastrophe** dans
l'évaluation flottante de la série E_α(−x) : pour x ≈ 8 (termes ~10¹⁰ se
compensant vers ~0,056), la série double précision est fausse de **1,2×10⁻³
en valeur absolue (2 % relatif)**. C'est pourquoi l'assaut vertex avait
enregistré 1,11e-8 (σ=1) sur son contrôle Laplace : ce n'était pas de la
quadrature, c'était ce plancher, pesé par e^{−σt}. Le présent script
l'élimine (Decimal 50 chiffres, mêmes pièces, même grille) : écart tombé à
2,0×10⁻¹². **Toute réutilisation future de E_alpha_neg en flottant doit
passer par cette évaluation haute précision.**

## 5. Portée exacte du verdict

- **Ce qui tombe** : l'hypothèse que α soit une *lecture statique* de la
  grammaire V0 — ni norme intégrale (B), ni lecture de chaîne à jauges et
  témoins gelés (C), ni relecture du registre vertex (A).
- **Ce qui reste debout** : E2 (scène), E1a (Ĥ = ℏω₀n̂), E1b (masse,
  κ = 0,427511045, 22/22), α_W = 1/30 exact, la famille T* (24/24), et la
  formule 5-facteurs **comme ancre** (C4 la maintient à 3,1e-12).
- **Ce qui s'ouvre** : la grammaire *dynamique* — la tripartition mémoire
  (α_W oublie / α_EM porte / α_S est), l'exposant 5 de la formule, E1c.
  Le statique a dit non ; le dynamique n'a pas encore été interrogé.

## 6. Reproductibilité

```bash
python verif_alpha_grammaire.py   # exit 1 attendu ([F])
```
Déterministe : aucune graine, aucun thread, séries tronquées à |cₙ| < 1e-18
(décroissance superfactorielle), Simpson h = 0,002, B = 1 canonique.
Le dépôt `DEPOT_ALPHA_GRAMMAIRE_V0.md` reste scellé (non modifié).

---

*Conformément au dépôt §7.4, les documents d'ancrage (`DERIVATION_ALPHA_EM.md`,
`MODELE_STANDARD_HARMONIQUE.md`) n'ont pas été modifiés avant le verdict —
la mise à jour des registres ne consigne que le résultat.*