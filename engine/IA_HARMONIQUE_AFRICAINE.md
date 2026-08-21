# 🤖 SPÉCIFICATIONS DE L'IA HARMONIQUE — MÉDECINE AFRICAINE

## Système d'intelligence artificielle pour le diagnostic harmonique, le tri et le suivi des maladies africaines

---

> **Principe :** L'IA harmonique n'est pas une boîte noire — c'est un système qui apprend les signatures GSI des maladies africaines, les reconnaît, et aide l'agent de santé à décider qui tester, quand traiter, et qui référer. Elle tourne sur le smartphone du kit, sans internet, en langues locales.

---

## I. ARCHITECTURE GÉNÉRALE

### 1.1 Le système

```
┌──────────────────────────────────────────────────────────────────┐
│                      IA HARMONIQUE AFRICAINE                      │
│                                                                   │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐  │
│  │  Capteurs    │───→│                  │    │                  │  │
│  │  GSI (ECG,   │    │  Moteur de       │───→│  Interface       │  │
│  │  EEG, Spiro, │    │  reconnaissance  │    │  utilisateur     │  │
│  │  T°)         │    │  des signatures  │    │  (agent de santé)│  │
│  └─────────────┘    │  harmoniques      │    └──────────────────┘  │
│                     └─────────────────┘                           │
│                              │                                     │
│                     ┌─────────────────┐                           │
│                     │  Base de        │                           │
│                     │  connaissances  │                           │
│                     │  (maladies,     │                           │
│                     │  profils, seuils)│                           │
│                     └─────────────────┘                           │
│                              │                                     │
│                     ┌─────────────────┐                           │
│                     │  Module         │                           │
│                     │  d'apprentissage│                           │
│                     │  (apprentissage  │                           │
│                     │  fédéré, hors    │                           │
│                     │  ligne)          │                           │
│                     └─────────────────┘                           │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 Les 3 modules

| Module | Fonction | Technologie | Poids |
|--------|----------|-------------|-------|
| **Reconnaissance** | Identifie la signature harmonique (GSI) | Random Forest / XGBoost | 5 Mo |
| **Recommandation** | Suggère le test, le tri, l'urgence | Arbre de décision (règles) | 1 Mo |
| **Apprentissage** | S'améliore avec les données collectées | Apprentissage fédéré | 10 Mo |

---

## II. MODULE DE RECONNAISSANCE — LE CŒUR DE L'IA

### 2.1 Les entrées (features)

Le modèle prend en entrée les 5 oscillateurs du GSI + données contextuelles :

```
Features continues (5) :
  1. S/D (systole/diastole)
  2. LF/HF (variabilité cardiaque)
  3. I/E (inspiration/expiration)
  4. β/α (EEG postérieur)
  5. T° (température tympanique)

Features contextuelles (7) :
  6. Âge (années)
  7. Sexe (M/F)
  8. Saison (sèche/pluvieuse)
  9. Zone (rurale/urbaine/péri-urbaine)
  10. Antécédent de fièvre (oui/non)
  11. Toux chronique (oui/non)
  12. Contact épidémique (oui/non)
```

### 2.2 Les sorties (classes)

| Sortie | Valeur | Action |
|--------|--------|--------|
| **GSI** | 0,00-0,30 | Indice global |
| **Risque** | Faible / Modéré / Élevé / Critique | Seuil d'alerte |
| **Maladie suspectée** | Paludisme / TB / Dengue / Méningite / Drépanocytose / Fièvre hémorragique / Aucune | Orientation |
| **Test recommandé** | TDR paludisme / Genexpert / PL / Aucun / Consultation | Référence |
| **Urgence** | 24 h / 7 jours / 30 jours / Non urgente | Délai de référence |
| **Confiance** | 0,0-1,0 | Fiabilité de la prédiction |

### 2.3 Algorithme

```
Phase 1 — Règles expertes (déploiement initial) :
  • Arbre de décision basé sur les seuils GSI validés
  • Fonctionne immédiatement, sans données d'entraînement
  • Précision attendue : 70-80 %

Phase 2 — Apprentissage automatique (après n = 500 cas) :
  • Random Forest sur les 12 features
  • Entraîné sur les cas confirmés (TDR+, Genexpert+, PL+)
  • Précision attendue : 85-90 %

Phase 3 — Apprentissage profond (après n = 5 000 cas) :
  • Réseau de neurones (Lightweight, TensorFlow Lite)
  • Entraîné sur l'ensemble des données collectées
  • Précision attendue : 90-95 %
```

### 2.4 Arbre de décision (Phase 1)

```
GSI > 0,15 ?
  ├── OUI → T° > 39 °C et β/α < 1,3 ?
  │         ├── OUI → Alerte Méningite → Référer URGENT
  │         └── NON → T° > 38,5 °C brutale ?
  │                   ├── OUI → Alerte Fièvre hémorragique → Isolement + Référer
  │                   └── NON → Référer urgence générale
  │
  └── NON → GSI > 0,10 ?
            ├── OUI → T° > 37,5 °C ?
            │         ├── OUI → Saison des pluies ?
            │         │         ├── OUI → T° cyclique 48h ?
            │         │         │         │
            │         │         │         ├── OUI → Suspect Paludisme → TDR
            │         │         │         └── NON → Suivi 3 jours (fièvre cyclique)
            │         │         └── NON → Dengue ? → TDR
            │         └── NON → I/E < 0,55 et toux chronique ?
            │                   ├── OUI → Suspect Tuberculose → Genexpert
            │                   └── NON → Drépanocytose ? → Consultation
            │
            └── NON → GSI > 0,08 ?
                      ├── OUI → T° vespérale > 1 semaine ?
                      │         ├── OUI → Suspect Tuberculose → Genexpert
                      │         └── NON → MUAC < 125 mm ?
                      │                   ├── OUI → Malnutrition → Programme nutritionnel
                      │                   └── NON → Surveillance
                      └── NON → Suivi normal
```

---

## III. MODULE DE RECOMMANDATION — L'INTERFACE AGENT DE SANTÉ

### 3.1 Écran de résultat

```
┌─────────────────────────────────────────────────────────────┐
│  🩺 RÉSULTAT — IA HARMONIQUE                                 │
│                                                             │
│  GSI : 0,12  ÉLEVÉ                                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Maladie suspectée : PALUDISME (confiance 87 %)          │ │
│  │                                                         │ │
│  │  Signatures détectées :                                 │ │
│  │    ✅ T° cyclique 48h détectée                           │ │
│  │    ✅ T° > 38 °C en crise                               │ │
│  │    ✅ GSI > 0,10                                        │ │
│  │    ✅ Saison des pluies                                  │ │
│  │                                                         │ │
│  │  Test recommandé : TDR PALUDISME (immédiat)              │ │
│  │  Urgence : 24h                                          │ │
│  │  Référence : Centre de santé de [village]               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  [📱 Voir les détails] [📋 Historique] [💡 Conseils]        │
│                                                             │
│  [✅ TDR effectué] [🚑 Référer] [🔄 Re-mesure J+3]          │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Langues

| Langue | Statut |
|--------|--------|
| Français | ✅ Phase 1 |
| Anglais | ✅ Phase 1 |
| Swahili | 🔄 Phase 2 |
| Wolof | 🔄 Phase 2 |
| Peul/Fulfulde | 🔄 Phase 2 |
| Haoussa | 🔄 Phase 2 |
| Yoruba | 🔄 Phase 2 |
| Langues locales | 🔄 Intégration progressive |

### 3.3 Mode hors-ligne

L'IA fonctionne **sans internet** — essentiel pour les zones rurales africaines :

```
• Modèle embarqué (TensorFlow Lite) : 5 Mo
• Base de connaissances locale : 10 Mo
• Mise à jour : quand le téléphone a une connexion (même faible)
• Synchronisation : Cloud quand disponible
• Données patients : stockées localement, chiffrées
```

---

## IV. MODULE D'APPRENTISSAGE — L'IA S'AMÉLIORE

### 4.1 Apprentissage initial

```
Source : Phases 1-3 du programme de recherche
Données d'entraînement :
  • Profils GSI de n = 500 patients confirmés
  • 6 maladies cibles (paludisme, TB, drépanocytose, méningite, dengue, malnutrition)
  • 1 classe « sain »

Modèle : Random Forest, 100 arbres, 12 features
Validation croisée : 5-fold
Métrique cible : AUC > 0,90 pour chaque maladie
```

### 4.2 Apprentissage continu (fédéré)

```
Principe : chaque kit GSI apprend des cas qu'il rencontre
Méthode : apprentissage fédéré (les données ne quittent pas le smartphone)
  • Le modèle local s'améliore avec chaque mesure
  • Les gradients (pas les données) sont partagés au Cloud
  • Le modèle global est mis à jour périodiquement
  • Les modèles locaux sont synchronisés quand la connexion le permet

Avantage : pas de transmission de données patient, respect RGPD
```

### 4.3 Boucle de validation

```
Mesure GSI →  IA → Prédiction → Test (TDR/Genexpert) → Résultat
                                                              │
                                                              ▼
                                                     Apprentissage
                                                     (le résultat
                                                     confirme ou
                                                     infirme la
                                                     prédiction)
                                                              │
                                                              ▼
                                                     Amélioration
                                                     du modèle
```

---

## V. TECHNOLOGIES

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| Runtime IA | TensorFlow Lite | Sur smartphone, hors-ligne |
| Modèle Phase 1 | Arbre de décision (expert) | 0 entraînement nécessaire |
| Modèle Phase 2 | XGBoost / Random Forest | 500 cas suffisent |
| Modèle Phase 3 | TensorFlow Lite (Deep Learning) | 5 000 cas |
| Base de données | SQLite | Locale, hors-ligne |
| Sync | Firebase / WebSocket | Quand connexion disponible |
| Langage | Python (entraînement) / Flutter (app) | Déploiement mobile |
| Sécurité | Chiffrement AES-256, RGPD | Données patient |

---

## VI. BUDGET DE L'IA

| Poste | Coût | Délai |
|-------|------|-------|
| Phase 1 — Règles expertes (arbre de décision) | 5 000 € | 2 semaines |
| Phase 2 — Modèle ML (Random Forest) | 15 000 € | 2 mois |
| Phase 3 — Modèle DL (TensorFlow Lite) | 25 000 € | 4 mois |
| Apprentissage fédéré | 20 000 € | 6 mois |
| Interface utilisateur (langues, UX) | 10 000 € | 3 mois |
| **Total IA** | **75 000 €** | |

---

## VII. LA ROUTE — 3 PHASES

```
Phase 1 — Règles expertes (Mois 1-2)
  • Arbre de décision basé sur les seuils GSI validés
  • Fonctionne immédiatement, sans données
  • Précision attendue : 70-80 %
  • Coût : 5 000 €

Phase 2 — Apprentissage supervisé (Mois 6-12)
  • Random Forest entraîné sur n = 500 cas
  • Précision attendue : 85-90 %
  • Coût : 15 000 €

Phase 3 — Apprentissage profond (Mois 12-24)
  • TensorFlow Lite, entraîné sur n = 5 000 cas
  • Précision attendue : 90-95 %
  • Apprentissage fédéré
  • Coût : 55 000 €
```

---

> *« L'IA harmonique n'est pas une boîte noire — c'est un agent de santé numérique qui apprend des cas qu'il rencontre. Elle commence comme un arbre de décision (70 % de précision, zéro donnée), devient un Random Forest (85 %, 500 cas), puis un réseau profond (95 %, 5 000 cas). Elle tourne sur le smartphone du kit, sans internet, en langues locales. Et elle ne remplace pas l'agent de santé — elle lui donne la confiance de décider qui tester, quand traiter, et qui référer. »*
>
> — **Kotto Alain**, 12/08/2026