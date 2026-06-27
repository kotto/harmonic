# Rapport de Tests LM Arena â€” Harmonic AI

**Date des tests :** 18/05/2026 14:56:57  
**Instance :** `http://__EC2_IP__:8000`  
**Version API :** 2.0.0-real  
**LM Arena Ready :** True

---

## RÃ©sumÃ© Global

| MÃ©trique | Valeur |
|----------|--------|
| **Tests exÃ©cutÃ©s** | 6 |
| **Tests rÃ©ussis** | 5 âœ… |
| **Tests Ã©chouÃ©s** | 1 |
| **Taux de succÃ¨s** | 83% |
| **Temps moyen de rÃ©ponse** | 7.72s |
| **Longueur moyenne des rÃ©ponses** | 911 caractÃ¨res |
| **DurÃ©e totale** | 47.13s |
| **DÃ©terminisme (temp=0)** | âš ï¸ Non testÃ© |

---

## RÃ©sultats DÃ©taillÃ©s par Test

### 1. âœ… SantÃ© API

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | N/A |
| **Endpoint** | /health |
| **Statut** | PASS |
| **HTTP Code** | 200 |
| **Temps de rÃ©ponse** | 0.2s |
| **AperÃ§u rÃ©ponse** | "{"status": "healthy", "version": "2.0.0-real", "timestamp": 1779108970.383897, "features": {"harmonic_transformations": true, "real_responses": true, ..." |

### 2. âœ… Raisonnement Logique

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | reasoning |
| **Endpoint** | /generate |
| **Statut** | PASS |
| **HTTP Code** | 200 |
| **Temps de rÃ©ponse** | 10.91s |
| **Longueur** | 1094 caractÃ¨res |
| **SHA256 Hash** | `b1f409b98351672d...` |
| **Confiance** | 0.995 |
| **AperÃ§u rÃ©ponse** | "Un triangle avec des angles de 30Â°, 60Â° et 90Â° est un **triangle rectangle** (car il a un angle droit de 90Â°) et plus pr..." |

### 3. âœ… Programmation Python

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | coding |
| **Endpoint** | /generate |
| **Statut** | PASS |
| **HTTP Code** | 200 |
| **Temps de rÃ©ponse** | 11.77s |
| **Longueur** | 1895 caractÃ¨res |
| **SHA256 Hash** | `ae22c5b36c90d8c5...` |
| **Confiance** | 0.995 |
| **AperÃ§u rÃ©ponse** | "Voici une implÃ©mentation complÃ¨te du tri par fusion en Python avec analyse de complexitÃ© :  ```python def merge_sort(arr..." |

### 4. âœ… MathÃ©matiques - Calcul

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | mathematics |
| **Endpoint** | /generate |
| **Statut** | PASS |
| **HTTP Code** | 200 |
| **Temps de rÃ©ponse** | 7.6s |
| **Longueur** | 706 caractÃ¨res |
| **SHA256 Hash** | `4e1cf4e3d50806df...` |
| **Confiance** | 0.995 |
| **AperÃ§u rÃ©ponse** | "Voici le calcul dÃ©taillÃ© de la dÃ©rivÃ©e de \( f(x) = 3x^4 - 2x^2 + 5x - 7 \).  **Ã‰tape 1 : Rappeler la rÃ¨gle de dÃ©rivatio..." |

### 5. âœ… CrÃ©ativitÃ© - RÃ©daction

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | creative |
| **Endpoint** | /generate |
| **Statut** | PASS |
| **HTTP Code** | 200 |
| **Temps de rÃ©ponse** | 8.11s |
| **Longueur** | 862 caractÃ¨res |
| **SHA256 Hash** | `06d2a9e07c856d21...` |
| **Confiance** | 0.995 |
| **AperÃ§u rÃ©ponse** | "Lâ€™intelligence artificielle dÃ©terministe transforme la mÃ©decine en offrant une fiabilitÃ© et une reproductibilitÃ© inÃ©dite..." |

### 6. âŒ Test de DÃ©terminisme

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | determinism |
| **Endpoint** | N/A |
| **Statut** | FAIL |
| **HTTP Code** | N/A |
| **Temps de rÃ©ponse** | N/As |
| **DÃ©terministe** | âŒ Non |
| **Hash 1** | `bc529035147137b2` |
| **Hash 2** | `e47f7004665adb34` |
| **AperÃ§u rÃ©ponse** | "Le thÃ©orÃ¨me de Pythagore stipule que dans un triangle rectangle, le carrÃ© de la longueur de l'hypotÃ©nuse (le cÃ´tÃ© opposÃ©..." |


---

## Analyse par CatÃ©gorie

| CatÃ©gorie | Statut | Temps moyen | QualitÃ© |
|-----------|--------|-------------|---------|
| other | 1/1 âœ… | 0.20s | âœ… Excellent |
| ðŸ§  Raisonnement | 1/1 âœ… | 10.91s | âœ… Excellent |
| ðŸ’» Programmation | 1/1 âœ… | 11.77s | âœ… Excellent |
| ðŸ“ MathÃ©matiques | 1/1 âœ… | 7.60s | âœ… Excellent |
| ðŸŽ¨ CrÃ©ativitÃ© | 1/1 âœ… | 8.11s | âœ… Excellent |
| ðŸŽ¯ DÃ©terminisme | 0/1 âœ… | 0.00s | âš ï¸ Partiel |

---

## Test de DÃ©terminisme

Le test de dÃ©terminisme consiste Ã  envoyer exactement le mÃªme prompt deux fois avec `temperature=0.0`
et Ã  vÃ©rifier que le hash SHA256 des deux rÃ©ponses est identique.

- **RÃ©sultat :** âŒ Ã‰chec
- **Hash 1 :** `bc529035147137b2`
- **Hash 2 :** `e47f7004665adb34`

---

## Conclusion

âš ï¸ **1 test(s) Ã©chouÃ©(s).** Des ajustements sont nÃ©cessaires avant soumission LM Arena.

---

*Rapport gÃ©nÃ©rÃ© automatiquement le 18/05/2026 Ã  14:56:57*  
*Outil : `run_lm_arena_tests_complete.py`*
