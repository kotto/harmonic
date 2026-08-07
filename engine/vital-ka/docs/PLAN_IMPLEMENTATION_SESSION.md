# 🎯 PLAN D'IMPLÉMENTATION — Session complète

## Récapitulatif des fonctionnalités évoquées (13)

| # | Fonctionnalité | État | Action |
|---|---|---|---|
| 1 | Hologrammes médicaux (15 domaines, 62K faits) | ✅ Fait | — |
| 2 | Routeur spectral (routage auto + seuil 0.15) | ✅ Fait | — |
| 3 | Phrasé naturel (templates relations) | ✅ Fait | — |
| 4 | Enrichissement +158 faits (VACCINATION, PALUDISME...) | ✅ Fait | — |
| 5 | Routage par index lexical (moringa, artemisia...) | ✅ Fait | — |
| 6 | Couverture lexicale (bloque hors-sujets) | ⚠️ JS only | **A. Parité Python** |
| 7 | API : `/hologram/query`, `/health`, `/model/info` | ✅ Fait | — |
| 8 | API : `/diagnose`, `/prescribe`, `/interactions`, `/explain` | ⚠️ Stubs 503 | **B. Brancher hologrammes** |
| 9 | App web KA Care (KA_AI, anti-cache) | ✅ Fait | — |
| 10 | Android offline (bundle 3.7 MB + routeur JS) | ✅ Fait | — |
| 11 | Wallet UM : patient ✅ pharmacien ✅ | ⚠️ Médecin manque | **C. Wallet médecin** |
| 12 | Kaggle 125M + surveillance | ✅ RUNNING | — |
| 13 | Dossier MTN + PDF | ✅ Fait | — |

## 4 actions d'implémentation

### A. Couverture lexicale Python (hologram_router.py + inference_server.py)
- Ajouter la règle de couverture ≥50% des mots dans le vocabulaire médical
- Parité exacte avec le comportement JS testé (football → bloqué, gâteau → bloqué)

### B. Endpoints métier branchés sur les hologrammes
Remplacer les stubs 503 par des réponses **réelles** issues des hologrammes
(le 125M viendra en complément plus tard — l'API doit déjà servir sans lui) :

| Endpoint | Source holographique | Exemple de réponse |
|----------|---------------------|--------------------|
| `/diagnose` | Faits `présente_symptôme` + domaines routés | Top-3 hypothèses avec scores |
| `/prescribe` | Faits `traitement`, `dose_adulte`, `dose_enfant` | Posologies par médicament |
| `/interactions` | Faits `interaction` du domaine PHARMACIE | Paires + sévérité |
| `/explain` | Faits du domaine routé + phrasé naturel | Explication en phrases |

### C. Wallet médecin (ka_medecins.html)
- Ajouter `ka_wallet.js` au fichier
- Écran "Honoraires" : solde + encaisser un paiement patient (QR/ID)
- Conversion UM → CFA/EUR (prestataire convertible)

### D. Interactions pharmacien (ka_pharmacien.html)
- Bouton "Vérifier interactions" avec saisie de 2+ médicaments
- Résultat via `KA_HOLOGRAM.query()` (domaine PHARMACIE)
- Affichage dans le style existant (cards + badges)

## Ordre d'implémentation
1. A (rapide, parité) → 2. B (API complète) → 3. C (wallet médecin) → 4. D (pharmacien) → tests → commit

## Contraintes
- Conserver thème, design et layout existants (CSS `vital_ka.css` / `ka_telemedecine.css`)
- Ne pas casser les flux existants (diagnostic local, wallet patient/pharmacien)
- Source de vérité = `engine/` → sync vers `www/` pour Android
