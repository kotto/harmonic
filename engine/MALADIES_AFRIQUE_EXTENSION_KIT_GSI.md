# 🦟 MALADIES SPÉCIFIQUES À L'AFRIQUE — EXTENSION DU KIT GSI

## Signatures harmoniques, algorithmes de détection et protocoles de surveillance

---

> **Principe :** Le kit GSI ne diagnostique pas une maladie spécifique (le diagnostic nécessite un laboratoire). Il détecte la **signature harmonique du stress physiologique** que chaque maladie provoque, permet un **tri précoce** (qui référer ? quand ?), et **suit la réponse au traitement** — exactement ce dont les systèmes de santé à ressources limitées ont besoin.

---

## I. LES MALADIES CIBLES ET LEURS SIGNATURES HARMONIQUES

### 1.1 Paludisme (malaria)

**Le problème :** 234 millions de cas/an, 593 000 décès — 95 % en Afrique. Le pic de transmission, la résistance aux antipaludéens, le retard de diagnostic tuent.

**La signature harmonique :**

| Marqueur | Comportement | Fenêtre |
|----------|--------------|---------|
| **T° cyclique** | Fièvre toutes les 48 h (P. falciparum) ou 72 h (P. vivax/malariae) | Détecté par mesure répétée |
| **T° élevée** | > 38 °C en crise | δ₅ élevé |
| **S/D** | Anémie → diminution S/D | δ₁ élevé |
| **LF/HF** | Dysfonction autonome | δ₂ élevé |
| **GSI** | > 0,10 pendant la crise | Élevé |

**Algorithme « Paludisme » :**
```
Mesure GSI 2×/jour pendant 3 jours
SI T° > 38,0 °C ET GSI > 0,10
ET cycle thermique de 48 h détecté
ALORS : Référer pour test rapide (TDR paludisme)
```

**Test rapide complémentaire :** TDR (Test de Diagnostic Rapide) à 0,50 € — le kit inclut la procédure, le GSI oriente qui tester et quand.

### 1.2 Tuberculose (TB)

**Le problème :** 10,6 millions de cas/an, 1,6 million de décès — l'Afrique représente 25 % des cas. Le diagnostic est souvent tardif.

**La signature harmonique :**

| Marqueur | Comportement | Fenêtre |
|----------|--------------|---------|
| **T° vespérale** | Fièvre légère le soir (37,5-38,5 °C) | δ₅ modéré |
| **I/E** | Respiration altérée (toux, dyspnée) | δ₃ élevé |
| **S/D** | Cachexie, atteinte cardiaque | δ₁ modéré |
| **GSI** | > 0,08 persistant | Chronique |

**Algorithme « Tuberculose » :**
```
Mesure GSI hebdomadaire pendant 1 mois
SI T° vespérale > 37,5 °C persistante (> 2 semaines)
ET I/E < 0,55
ET GSI > 0,08
ALORS : Référer pour crachat (Genexpert)
```

### 1.3 Drépanocytose (sickle cell disease)

**Le problème :** 300 000 naissances/an en Afrique. Les crises vaso-occlusives sont douloureuses et mal suivies.

**La signature harmonique :**

| Marqueur | Comportement | Fenêtre |
|----------|--------------|---------|
| **S/D** | Altéré pendant les crises | δ₁ élevé |
| **LF/HF** | Stress douloureux → dominance sympathique | δ₂ élevé |
| **T°** | Fièvre pendant les crises | δ₅ élevé |
| **GSI** | Augmente avant la crise (prédiction) | Précoce |

**Algorithme « Crise drépanocytaire » :**
```
Suivi GSI hebdomadaire en période calme
SI GSI augmente de 0,04 par rapport à la baseline
ET LF/HF > 2,0
ET douleur déclarée (échelle EVA)
ALORS : Alerte crise, consultation rapide
```

### 1.4 Méningite

**Le problème :** La ceinture de la méningite (Sahel) connaît des épidémies. La prise en charge doit être immédiate (< 24 h).

**La signature harmonique :**

| Marqueur | Comportement | Fenêtre |
|----------|--------------|---------|
| **T°** | Fièvre élevée > 39 °C | δ₅ très élevé |
| **β/α** | Neurologique altéré | δ₄ élevé |
| **S/D** | État de choc | δ₁ élevé |
| **GSI** | > 0,15 | Critique |

**Algorithme « Méningite » :**
```
Mesure GSI à l'admission
SI T° > 39 °C
ET β/α < 1,3 (neurologique)
ET raideur de nuque déclarée
ALORS : URGENCE — référer immédiatement (ponction lombaire)
```

### 1.5 Fièvres hémorragiques (Ebola, Lassa, fièvre jaune)

**Le problème :** Létalité élevée, détection précoce critique pour l'isolement.

**La signature harmonique :**

| Marqueur | Comportement | Fenêtre |
|----------|--------------|---------|
| **T°** | Fièvre brutale > 38,5 °C | δ₅ très élevé |
| **S/D** | État de choc hémorragique | δ₁ très élevé |
| **GSI** | > 0,15 | Critique |

**Algorithme « Fièvre hémorragique » :**
```
Mesure GSI à l'admission
SI T° > 38,5 °C ET GSI > 0,15
ET antécédent de contact (épidémie)
ALORS : Isolement immédiat, alerte épidémiologique
```

### 1.6 Dengue

**Le problème :** Extension rapide, les formes graves (hémorragiques) doivent être identifiées tôt.

**La signature harmonique :**

| Marqueur | Comportement | Fenêtre |
|----------|--------------|---------|
| **T°** | Fièvre, puis phase de fuite plasmatique | δ₅ |
| **S/D** | Hypotension à la phase critique (J4-J6) | δ₁ |
| **GSI** | Élevé pendant la fièvre, pic à la phase critique | Suivi |

**Algorithme « Dengue » :**
```
Mesure GSI 2×/jour pendant la fièvre
SI T° descend à J4 (fin de fièvre)
ET S/D diminue (fuite plasmatique)
ET GSI augmente malgré la baisse de T°
ALORS : Phase critique — hospitalisation
```

### 1.7 Malnutrition

**Le problème :** 250 millions d'enfants en retard de croissance en Afrique.

**La signature harmonique :**

| Marqueur | Comportement | Fenêtre |
|----------|--------------|---------|
| **S/D** | Cœur affaibli (anémie) | δ₁ élevé |
| **T°** | Hypothermie possible (< 36 °C) | δ₅ |
| **β/α** | Développement neurologique altéré | δ₄ |
| **GSI** | Élevé en malnutrition sévère | Suivi |

**Algorithme « Malnutrition » :**
```
Mesure GSI lors des consultations de suivi (mères-enfants)
SI GSI > 0,10 chez un enfant
ET périmètre brachial < 125 mm (MUAC)
ALORS : Programme nutritionnel intensif
```

---

## II. EXTENSION DU KIT — LES AJOUTS SPÉCIFIQUES

### 2.1 Module « Tri et Référence » (ajout logiciel)

L'application GSI intègre un **module de tri** qui interprète le GSI en contexte épidémiologique :

```
Sélection de la maladie suspectée (contexte local)
  → Paludisme (saison des pluies)
  → Tuberculose (toux chronique)
  → Méningite (épidémie)
  → Dengue (épidémie)
  → Fièvre hémorragique (contact)

L'application affiche :
  → Probabilité harmonique de la maladie
  → Seuil de référence (qui tester ?)
  → Test complémentaire recommandé (TDR, Genexpert, PL)
  → Urgence (24 h ? immédiate ?)
```

### 2.2 Module « Fièvre cyclique » (ajout logiciel)

Détection automatique des cycles thermiques (paludisme) :

```
Mesure T° 2×/jour pendant 3 jours
Analyse de la périodicité (FFT ou autocorrélation)
Si pic à 48 h ou 72 h → suspicion paludisme
Rappel automatique pour les mesures
```

### 2.3 Accessoires complémentaires (ajout matériel)

| Accessoire | Coût | Usage |
|-----------|------|-------|
| TDR paludisme (10 tests) | 5 € | Confirmation rapide |
| TDR dengue (5 tests) | 5 € | Confirmation rapide |
| Thermomètre supplémentaire (pour suivi 2×/j) | 10 € | Fièvre cyclique |
| Pèse-bébé (balance portative) | 15 € | Malnutrition |
| Ruban MUAC (circonférence brachiale) | 2 € | Malnutrition |
| **Total ajouts** | **37 €** | |

### 2.4 Coût total du kit étendu

```
Kit GSI de base : 580 €
Module tri (logiciel) : 0 €
Module fièvre cyclique (logiciel) : 0 €
Accessoires maladies : 37 €
**Kit GSI-Africa étendu : 617 €**
```

---

## III. VALIDATION CLINIQUE SPÉCIFIQUE AUX MALADIES

### 3.1 Protocole « Signatures harmoniques des maladies africaines »

**Population :** n = 1 000 patients (500 cas confirmés + 500 témoins)

| Maladie | n cas | Site de recrutement |
|---------|-------|---------------------|
| Paludisme (TDR+) | 150 | Centre de santé (zone endémique) |
| Tuberculose (Genexpert+) | 100 | Centre TB |
| Drépanocytose (confirmée) | 100 | Centre de référence |
| Méningite (PL+) | 50 | Hôpital |
| Dengue (TDR+) | 50 | Zone épidémique |
| Malnutrition (MUAC < 125) | 50 | Centre nutritionnel |

**Objectif :** Établir les profils GSI caractéristiques de chaque maladie.

### 3.2 Les livrables

| Livrable | Contenu |
|----------|---------|
| **L1** | Profils GSI des 6 maladies cibles |
| **L2** | Courbes ROC par maladie (sensibilité, spécificité) |
| **L3** | Seuils de référence par maladie |
| **L4** | Algorithmes de tri validés |
| **L5** | Protocole de surveillance longitudinale |

### 3.3 Coût de la validation spécifique

```
Phase 3b (maladies africaines) : 150 000 €
  • Coordination : 20 000 €
  • Équipement (kits étendus) : 30 000 €
  • Personnel (médecins, enquêteurs) : 70 000 €
  • Laboratoire (TDR, Genexpert) : 15 000 €
  • Analyse et publication : 15 000 €
```

---

## IV. DÉPLOIEMENT PAR MALADIE — PRIORITÉS

### 4.1 Priorité 1 — Paludisme (impact maximal)

```
Saison des pluies : pic de transmission
Agent de santé communautaire :
  • Mesure GSI 2×/jour en cas de fièvre
  • Détection du cycle 48 h
  • Réfère pour TDR si GSI > 0,10
  • Suivi de la réponse au traitement (J0, J3, J7)

Impact attendu : diagnostic plus précoce,
traitement plus rapide, réduction de la mortalité
```

### 4.2 Priorité 2 — Tuberculose (maladie chronique)

```
Programme DOTS :
  • Mesure GSI à J0, M1, M2, M3, M6
  • Suivi de la normalisation du GSI sous traitement
  • Détection précoce des échecs thérapeutiques

Impact attendu : meilleure observance,
détection précoce des résistances
```

### 4.3 Priorité 3 — Malnutrition (prévention)

```
Programme mères-enfants :
  • Mesure GSI lors des consultations
  • Détection précoce du GSI > 0,10
  • Référence nutritionnelle avant la malnutrition sévère

Impact attendu : prévention de la malnutrition sévère
```

### 4.4 Priorité 4 — Méningite et fièvres hémorragiques (urgence)

```
Pendant les épidémies :
  • Mesure GSI à l'admission
  • Alerte si GSI > 0,15
  • Isolement immédiat si suspicion

Impact attendu : prise en charge plus rapide,
confinement plus efficace
```

---

## V. TABLEAU RÉCAPITULATIF — 7 MALADIES

| Maladie | Signature clé | Seuil GSI | Référence | Coût ajout |
|---------|---------------|-----------|-----------|------------|
| **Paludisme** | T° cyclique 48 h + GSI | > 0,10 | TDR | TDR 0,50 € |
| **Tuberculose** | T° vespérale + I/E bas | > 0,08 | Genexpert | — |
| **Drépanocytose** | GSI + LF/HF + douleur | Augmentation 0,04 | Consultation | — |
| **Méningite** | T° > 39 + β/α < 1,3 | > 0,15 | PL | — |
| **Fièvres hémorragiques** | T° brutale + GSI | > 0,15 | Isolement | — |
| **Dengue** | T° descend + S/D baisse | Suivi | Hospitalisation | TDR |
| **Malnutrition** | GSI + MUAC | > 0,10 | Nutrition | MUAC 2 € |

---

## VI. CONCLUSION — LE KIT COMME OUTIL DE TRI

Le kit GSI-Africa étendu ne remplace pas le laboratoire — il le **précède et l'optimise** :

```
1. Le GSI détecte le stress physiologique (qui est malade ?)
2. L'algorithme oriente (quel test faire ?)
3. Le TDR/Genexpert confirme (quel pathogène ?)
4. Le traitement est administré (quoi ?)
5. Le GSI suit la réponse (le traitement marche-t-il ?)
```

**Dans un système de santé où il y a 2 médecins pour 10 000 habitants, où le laboratoire est à 50 km, où le TDR coûte 0,50 € : le kit GSI-Africa permet à l'agent de santé communautaire de décider QUI doit faire 50 km et QUAND. C'est un outil de tri, de priorisation et de suivi — là où il n'y en avait aucun.**

---

> *« Le paludisme ne tue pas quand il est détecté à temps. La tuberculose ne tue pas quand le traitement est suivi. La malnutrition ne tue pas quand elle est prise en charge tôt. Le problème n'est pas le médicament — c'est la détection. Et la détection, c'est un GSI, un smartphone, et un agent de santé communautaire formé. »*
>
> — **Kotto Alain**, 12/08/2026