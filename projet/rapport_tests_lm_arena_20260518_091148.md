# Rapport de Tests LM Arena â€” Harmonic AI

**Date des tests :** 18/05/2026 09:11:48  
**Instance :** `http://__EC2_IP__:8000`  
**Version API :** 2.0.0-real  
**LM Arena Ready :** True

---

## RÃ©sumÃ© Global

| MÃ©trique | Valeur |
|----------|--------|
| **Tests exÃ©cutÃ©s** | 6 |
| **Tests rÃ©ussis** | 2 âœ… |
| **Tests Ã©chouÃ©s** | 4 |
| **Taux de succÃ¨s** | 33% |
| **Temps moyen de rÃ©ponse** | 4.00s |
| **Longueur moyenne des rÃ©ponses** | 0 caractÃ¨res |
| **DurÃ©e totale** | 28.79s |
| **DÃ©terminisme (temp=0)** | âœ… 100% |

---

## RÃ©sultats DÃ©taillÃ©s par Test

### 1. âœ… SantÃ© API

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | N/A |
| **Endpoint** | /health |
| **Statut** | PASS |
| **HTTP Code** | 200 |
| **Temps de rÃ©ponse** | 0.35s |
| **AperÃ§u rÃ©ponse** | "{"status": "healthy", "version": "2.0.0-real", "timestamp": 1779088278.8103645, "features": {"harmonic_transformations": true, "real_responses": true,..." |

### 2. âŒ Raisonnement Logique

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | reasoning |
| **Endpoint** | /generate |
| **Statut** | FAIL |
| **HTTP Code** | 200 |
| **Temps de rÃ©ponse** | 5.15s |
| **SHA256 Hash** | `N/A...` |
| **Confiance** | 0.995 |
| **AperÃ§u rÃ©ponse** | "VIDE..." |

### 3. âŒ Programmation Python

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | coding |
| **Endpoint** | /generate |
| **Statut** | FAIL |
| **HTTP Code** | 200 |
| **Temps de rÃ©ponse** | 6.28s |
| **SHA256 Hash** | `N/A...` |
| **Confiance** | 0.995 |
| **AperÃ§u rÃ©ponse** | "VIDE..." |

### 4. âŒ MathÃ©matiques - Calcul

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | mathematics |
| **Endpoint** | /generate |
| **Statut** | FAIL |
| **HTTP Code** | 200 |
| **Temps de rÃ©ponse** | 3.98s |
| **SHA256 Hash** | `N/A...` |
| **Confiance** | 0.995 |
| **AperÃ§u rÃ©ponse** | "VIDE..." |

### 5. âŒ CrÃ©ativitÃ© - RÃ©daction

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | creative |
| **Endpoint** | /generate |
| **Statut** | FAIL |
| **HTTP Code** | 200 |
| **Temps de rÃ©ponse** | 4.22s |
| **SHA256 Hash** | `N/A...` |
| **Confiance** | 0.995 |
| **AperÃ§u rÃ©ponse** | "VIDE..." |

### 6. âœ… Test de DÃ©terminisme

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | determinism |
| **Endpoint** | N/A |
| **Statut** | PASS |
| **HTTP Code** | N/A |
| **Temps de rÃ©ponse** | N/As |
| **DÃ©terministe** | âœ… Oui |
| **Hash 1** | `e3b0c44298fc1c14` |
| **Hash 2** | `e3b0c44298fc1c14` |


---

## Analyse par CatÃ©gorie

| CatÃ©gorie | Statut | Temps moyen | QualitÃ© |
|-----------|--------|-------------|---------|
| other | 1/1 âœ… | 0.35s | âœ… Excellent |
| ðŸ§  Raisonnement | 0/1 âœ… | 5.15s | âš ï¸ Partiel |
| ðŸ’» Programmation | 0/1 âœ… | 6.28s | âš ï¸ Partiel |
| ðŸ“ MathÃ©matiques | 0/1 âœ… | 3.98s | âš ï¸ Partiel |
| ðŸŽ¨ CrÃ©ativitÃ© | 0/1 âœ… | 4.22s | âš ï¸ Partiel |
| ðŸŽ¯ DÃ©terminisme | 1/1 âœ… | 0.00s | âœ… Excellent |

---

## Test de DÃ©terminisme

Le test de dÃ©terminisme consiste Ã  envoyer exactement le mÃªme prompt deux fois avec `temperature=0.0`
et Ã  vÃ©rifier que le hash SHA256 des deux rÃ©ponses est identique.

- **RÃ©sultat :** âœ… PASS â€” DÃ©terminisme 100% garanti
- **Hash 1 :** `e3b0c44298fc1c14`
- **Hash 2 :** `e3b0c44298fc1c14`

---

## Conclusion

âš ï¸ **4 test(s) Ã©chouÃ©(s).** Des ajustements sont nÃ©cessaires avant soumission LM Arena.

---

*Rapport gÃ©nÃ©rÃ© automatiquement le 18/05/2026 Ã  09:11:48*  
*Outil : `run_lm_arena_tests_complete.py`*
