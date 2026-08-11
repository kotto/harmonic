# 🧠 PLAN GÉNÉRAL D'IMPLÉMENTATION — IA HARMONIQUE V2

**Date** : 09/08/2026 — **Auteur** : Univers-Holistique
**Statut** : Plan d'implémentation — 5 phases, chaque phase = un critère mesurable

---

## Architecture générale

```
┌─────────────────────────────────────────────────────────────────┐
│                     IA HARMONIQUE V2                            │
│                                                                 │
│  ENTRÉE (texte, voix, données)                                  │
│      │                                                          │
│  ┌───▼──────────────────────────────────────────────────────┐   │
│  │ INCONSCIENT — Stockage par répétition                    │   │
│  │ · Noyau doré K(t)=B·E_{1/φ}(−φ·t^{1/φ})                 │   │
│  │ · ZÉRO paramètre ajusté                                  │   │
│  │ · Chaque exposition → trace                              │   │
│  │ · 3-5 répétitions → APPRIS (amplitude > seuil)           │   │
│  │ · Pas de répétition → OUBLI (queue t^{-0.618})           │   │
│  └───┬──────────────────────────────────────────────────────┘   │
│      │  motifs survivants                                       │
│  ┌───▼──────────────────────────────────────────────────────┐   │
│  │ CONSCIENT — Représentations + Résonance                  │   │
│  │ · Embeddings APPRIS (X3 — co-occurrence, PPMI)           │   │
│  │ · Binding HRR (convolution circulaire)                   │   │
│  │ · Résonance : |⟨ψ_q ⋆ ψ_k, ψ_candidat⟩|                 │   │
│  │ · Si résonance > seuil → RÉPONSE                        │   │
│  │ · Sinon → REFUS CALIBRÉ                                  │   │
│  └───┬──────────────────────────────────────────────────────┘   │
│      │                                                          │
│  SORTIE (réponse ou refus, avec confiance)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1 — Noyau d'inconscient (semaine 1)

**Objectif** : Implémenter le stockage par répétition avec le noyau doré.

| Tâche | Détail | Critère |
|---|---|---|
| 1.1 | Implémentation du noyau K(t) avec E_{1/φ} | `E_alpha` existant (Violet A) ✅ |
| 1.2 | Stockage incrémental : chaque token → trace horodatée | `Inconscient.exposer(mot)` ✅ |
| 1.3 | Calcul d'amplitude cumulée avec décroissance | `Inconscient.amplitude(mot)` ✅ |
| 1.4 | Seuil de survie : 3-5 répétitions → APPRIS | Seuil calibré sur corpus |
| 1.5 | Nettoyage : traces sous le seuil d'oubli → suppression | Déjà implémenté ✅ |
| 1.6 | Test : sur un flux de mots, mesurer le taux d'apprentissage | Précision > 80 % après 5 expositions |

**Livrable** : `inconscient.py` — module autonome, zéro paramètre ajusté.

---

## Phase 2 — Représentations conscientes (semaine 2)

**Objectif** : Apprendre les embeddings par co-occurrence (X3).

| Tâche | Détail | Critère |
|---|---|---|
| 2.1 | Collecte de co-occurrences sur le corpus d'entraînement | Fenêtre de ±3 mots |
| 2.2 | Construction de la matrice PPMI (Positive Pointwise Mutual Information) | Déjà dans `holographic_encoder.py` |
| 2.3 | Réduction SVD → embeddings de dimension D=128-256 | Variance expliquée > 60 % |
| 2.4 | Binding HRR pour les relations : `bind(ψ_A, ψ_R) ≈ ψ_B` | Test sur paires connues (capitale, synonyme) |
| 2.5 | Test de résonance : `|⟨ψ_q ⋆ ψ_rel, ψ_candidat⟩|` | Précision > hasard (p < 0,01) sur 100 paires |

**Livrable** : `conscient.py` — module d'embeddings appris + résonance.

---

## Phase 3 — Intégration et refus calibré (semaine 3)

**Objectif** : Connecter les deux couches et implémenter le refus.

| Tâche | Détail | Critère |
|---|---|---|
| 3.1 | Pont inconscient → conscient : les motifs survivants alimentent la résonance | OK si > 0 |
| 3.2 | Seuil de résonance : si max_score < seuil → REFUS | Seuil calibré sur jeu de validation |
| 3.3 | Score de confiance = amplitude_inconscient × score_résonance | Corrélation confiance/précision > 0,7 |
| 3.4 | Courbe de calibration : ECE < 0,15 (comme P1.2) | Mesuré sur 200 questions |
| 3.5 | Test bout-en-bout : question → stockage → résonance → réponse/refus | OK |

**Livrable** : `ia_harmonique_v2.py` — moteur complet intégré.

---

## Phase 4 — Benchmark et protocole (semaine 4)

**Objectif** : Mesurer la performance avec le protocole pré-enregistré.

| Tâche | Détail | Critère |
|---|---|---|
| 4.1 | Corpus de test : 500 paires question→réponse (factuel, arithmétique, synonymes) | Varié |
| 4.2 | Protocole pré-enregistré : critères C1-C3 déclarés avant le test | Document daté |
| 4.3 | C1 : précision > hasard avec p < 0,01 (permutation test) | Test |
| 4.4 | C2 : taux de refus sur hors-domaine > 90 % | Test |
| 4.5 | C3 : paramètres appris < 10 % d'un modèle statistique équivalent | Comparaison |
| 4.6 | Rapport public : verdict, même négatif | Publié |

**Livrable** : `benchmark_ia_v2.py` + rapport JSON.

---

## Phase 5 — Déploiement et itération (semaine 5+)

**Objectif** : Intégrer au cerveau existant, déployer, itérer.

| Tâche | Détail |
|---|---|
| 5.1 | Remplacer le stockage actuel (hologram_store) par l'inconscient doré |
| 5.2 | Brancher le conscient sur les routes API existantes (/api/chat, /api/memorise) |
| 5.3 | Mode « apprentissage continu » : chaque interaction nourrit l'inconscient |
| 5.4 | Interface de visualisation : quels motifs ont survécu ? |
| 5.5 | Tests utilisateurs + calibration itérative du seuil de survie |

---

## Récapitulatif

| Phase | Durée | Paramètres appris | Livrable principal |
|---|---|---|---|
| 1 · Inconscient | Semaine 1 | **0** (noyau dérivé) | `inconscient.py` |
| 2 · Conscient | Semaine 2 | Embeddings (PPMI+SVD) | `conscient.py` |
| 3 · Intégration | Semaine 3 | Seuil de résonance | `ia_harmonique_v2.py` |
| 4 · Benchmark | Semaine 4 | 0 (protocole figé) | Rapport |
| 5 · Déploiement | Semaine 5+ | Itératif | Production |

---

## Ce que la THU V2 apporte à l'IA (rappel)

| Composante | Standard | THU V2 |
|---|---|---|
| Stockage | Poids appris (millions) | Noyau dérivé K(t) (zéro paramètre) |
| Apprentissage | Descente de gradient | Répétition → survie |
| Oubli | Explicite (pénalité) | Queue t^{-0.618} (naturel) |
| Décision | Softmax appris | Résonance + seuil |
| Refus | Post-traitement | Structurel (A1) |

---

*Plan d'implémentation — FIN — chaque phase a un critère mesurable. On commence la Phase 1.*
