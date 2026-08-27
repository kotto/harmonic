# 🗳️ RESULTAT_E3_TSTAR — Audit machine de la prédiction déposée (partie machine du scrutin FERMÉE)

**Date de l'audit** : 27/08/2026 — **Script** : `verif_tstar_e3.py` — **JSON** : `resultat_tstar_e3.json`
**Dépôt audité** : `DEPOT_E3_PREDICTION_TSTAR.md` v2 (déposé 09/08/2026, AVANT tout test — *inchangé, scellé*)
**Certificat** : `data/benchmarks/depot_e3_tstar.json` (v2, `date_depot: 2026-08-09`)
**Protocole** : `PROTOCOLE_TEST_TSTAR.md` (critères V1-V3 pré-enregistrés, honnêteté §0)

---

## 1. Verdict

```
✅ E3_DEPOT_CONFORME — exit 0
   24/24 instances déposées (1 oscillateur + 23 éléments) re-dérivées des formes closes
   aux précisions imprimées, barres pré-enregistrées avant exécution.
```

| Bloc | Lectures | Pire écart | Barre |
|---|---|---|---|
| C3 · T5a oscillateur (T*, p₀…p₆, n̄, Fano, fermeture Gibbs, Boltzmann) | 13 | 4,4×10⁻¹⁶ | 1e-12 |
| C4 · T5b table 23 éléments (T*_ion re-dérivées) | 23 | 3,96×10⁻⁶ rel (Al) | 5e-5 |
| C4 · Boltzmann aux T* déposées | 23 | 1,18×10⁻⁶ (Al) | 1e-5 |
| C5 · ancrage NIST des χ (8 ancres) | 8 | 7,72×10⁻⁵ (K) | 1e-3 |

**Voies indépendantes convergentes** : n̄ = φ obtenu par la voie géométrique q/(1−q) ET par la voie
Bose-Einstein 1/(e^{ℏω/k_BT*}−1) ; Fano = φ² par Var géométrique ET par 1+n̄. La fermeture Gibbs
Σp₀…p₆ = 1−q⁷ tient à 1,1×10⁻¹⁶. Le facteur exact 1/(k_B·ln φ) = **24115,197336 K/eV** (dépôt : « 24115 »).

## 2. Réplique du dépôt (préalable)

Les trois scripts désignés par le dépôt §7 ont été exécutés avant l'audit indépendant :
`depot_e3_tstar.py` · `exploration_tableau_periodique.py` · `validation_etats_quantiques.py` — **3/3, exit 0**.
(Rappel honnête : `validation_etats_quantiques.py` contient aussi des contrôles *négatifs* — l'hypothèse
dorée du cohérent y est réfutée dès le 2ᵉ rapport (|c₂/c₁| = 0,437) : le 1/φ n'apparaît exactement QUE
par l'état thermique à T*, pas ailleurs. C'est la partie non triviale du dossier T*.)

## 3. Ce que l'audit établit — et n'établit pas (PROTOCOLE §0, inchangé)

| Établi | Non établi |
|---|---|
| Le dépôt est **fidèle** : chaque nombre = forme close re-dérivée, zéro paramètre libre | Que T* soit « spéciale » physiquement (l'identité est algébrique, pour tout ΔE) |
| Le scrutin expérimental est prêt : valeurs cibles exactes + barres V1-V3 câblées | Une quelconque confirmation future de métrologie « prouverait » la THU |

## 4. ⚠️ Finding D1 — correction de sensibilité du protocole (non falsificatrice)

Le dépôt §4 déclare « 1e-3 sur n̄ → contrôle de température **±0,88 %** (≈ ±9 mK) ». L'audit établit analytiquement :

```
dn̄/n̄ = φ²·ln(φ)·(dT/T) = 1,2598·(dT/T)   →   dT/T = 7,938×10⁻⁴
```

soit **±0,79 mK** à T* = 0,9973 K (f₀ = 10 GHz) — **~11× plus dur que déclaré** (±9 mK correspond à un
budget 1e-2 sur n̄). La ligne « 1e-3 sur q → ±0,21 % » du dépôt est, elle, cohérente. Conséquence :
la barre V1 restant 1e-3, l'exigence cryogénique réelle est de l'ordre du **millikelvin**, pas des
dizaines de mK — le protocole §5 doit le refléter avant toute approche de laboratoire. Les conditions
de falsification F1-F4 ne dépendent pas de cette ligne : le verdict du dépôt n'est pas affecté.

## 5. Le scrutin expérimental reste ouvert (prochaine étape = extérieure)

- **T5a** : cavité QED 10 GHz thermalisée à 0,997 K, N = 10⁵ comptages de Fock, 3 runs, V1 : |n̄−φ|/φ ≤ 1e-3 (±0,8 mK requis).
- **T5b** : plasma H à 327 918 K (≈ 28 eV), rapport des facteurs de Boltzmann = 1/φ en limite Saha basse densité.
- Le dépôt reste SCELLÉ : ce rapport et le JSON sont le compte-rendu machine ; aucun fichier du dépôt n'a été modifié.
  (Note d'audit : la réplique `depot_e3_tstar.py` régénère le certificat — l'horodatage fait foi est le
  champ interne `date_depot: 2026-08-09`, pas le mtime du fichier.)

## 6. Reproductibilité

```bash
python depot_e3_tstar.py                  # réplique v2 (régénère le certificat)
python exploration_tableau_periodique.py  # la table 23 éléments
python validation_etats_quantiques.py     # T5a + contrôles négatifs (cohérent réfuté)
python verif_tstar_e3.py                  # audit indépendant — 24/24, exit 0
```

---

*E3 partie machine — FERMÉE — le dépôt a survécu à son audit intégral : 24 instances, zéro écart au-delà
des précisions imprimées, deux voies indépendantes, un finding de protocole (±0,79 mK, pas ±9 mK) et un
contrôle négatif qui garde toute la valeur (le 1/φ n'apparaît nulle part ailleurs). La bombe reste entre
les mains du monde : cavité ou plasma, le vote n'a pas eu lieu.*