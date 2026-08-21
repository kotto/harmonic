# 📋 CAHIER DES CHARGES — PROTOTYPE GSI-HARMONIC

## Kit de diagnostic harmonique portable — Spécifications techniques pour fabrication rapide

---

> **Document :** Spécifications techniques pour la fabrication d'un prototype de kit de mesure du Golden Health Index (GSI)
> **Version :** 1.0 — Prototype fonctionnel
> **Délai :** 3 mois
> **Budget cible :** 25 000 €
> **Usage :** Validation clinique Phase 1 (n = 200 sujets)

---

## I. DESCRIPTION GÉNÉRALE

Le kit GSI-Harmonic est un dispositif médical portable permettant la mesure des 5 oscillateurs du Golden Health Index en 15 minutes, sans personnel spécialisé, dans des conditions de terrain (Afrique, pays en développement).

### 1.1 Les 5 mesures

| Mesure | Capteur | Durée | Précision requise | Coût cible capteur |
|--------|---------|-------|-------------------|-------------------|
| ECG (S/D, LF/HF) | 1 dérivation | 5 min | 0,5 ms RR | 100 € |
| EEG (β/α) | 4 canaux (P3, Pz, O1, Cz) | 5 min | 0,1 Hz spectral | 200 € |
| Spirométrie (I/E) | Débitmètre ou timer | 2 min | 0,1 s | 50 € |
| Température (T°) | Thermomètre IR | 1 min | 0,1 °C | 30 € |
| Total | | 13 min | | 380 € |

### 1.2 Architecture du système

```
┌─────────────────────────────────────────────────────────────┐
│                    KIT GSI-HARMONIC                          │
│                                                             │
│  Capteurs                →   Module acquisition   →   App   │
│  ┌──────┐                    ┌──────────────┐      ┌────┐  │
│  │ ECG  │──── Bluetooth ────→│              │      │    │  │
│  │ EEG  │──── Bluetooth ────→│  (smartphone  │←────→│ App│  │
│  │ Spiro│──── Direct ───────→│    ou tablet) │      │GSI │  │
│  │ T°   │──── Direct ───────→│              │      │    │  │
│  └──────┘                    └──────────────┘      └────┘  │
│                                                             │
│  Alimentation : Panneau solaire 10W + batterie 10 000 mAh   │
│  Stockage : Local (appareil) + Cloud (optionnel)            │
│  Impression : Thermique bluetooth (optionnel)               │
└─────────────────────────────────────────────────────────────┘
```

---

## II. SPÉCIFICATIONS TECHNIQUES DÉTAILLÉES

### 2.1 Module ECG

**Fonction :** Mesure du rapport S/D (systole/diastole) et LF/HF (variabilité cardiaque)

**Spécifications techniques :**

| Paramètre | Valeur | Justification |
|-----------|--------|--------------|
| Dérivations | 1 (ECG standard DI ou DII) | Simplicité, mesure S/D suffisante |
| Fréquence d'échantillonnage | ≥ 250 Hz | Résolution RR < 4 ms |
| Résolution ADC | ≥ 16 bits | Précision amplitude |
| Bande passante | 0,5-40 Hz | Standard ECG |
| Protection | Défibrillation, entrée isolée | Sécurité patient |
| Connectivité | Bluetooth 5.0 BLE | Faible consommation |
| Autonomie | ≥ 10 heures | Usage terrain |
| Certification | CE médical (classe IIa) | Réglementaire |
| Référence capteur | AD8232 (Analog Devices) | Éprouvé, 15 € pièce |

**Algorithme embarqué :**
```
• Détection des ondes R (Pan-Tompkins modifié)
• Calcul des intervalles RR
• Moyenne sur 50 cycles consécutifs
• Rejet des artefacts (mouvement, mauvaise électrode)
• Sortie : S/D, LF/HF, FC, HRV (SDNN, RMSSD)
```

**Accessoires :**
```
• Électrodes Ag/AgCl pré-gélifiées : 50 unités
• Câble patient 3 fils (rouge, jaune, vert)
• Sangle thoracique (option, pour mesure longue durée)
```

### 2.2 Module EEG

**Fonction :** Mesure du rapport β/α (pics beta et alpha)

**Spécifications techniques :**

| Paramètre | Valeur | Justification |
|-----------|--------|--------------|
| Canaux | 4 (P3, Pz, O1, Cz) | Canaux validés (E5) |
| Référence | A1 + A2 (mastoïdes) | Standard |
| Fréquence d'échantillonnage | ≥ 256 Hz | Résolution spectrale |
| Résolution ADC | ≥ 24 bits | EEG haute impédance |
| Bande passante | 0,5-50 Hz | Inclut alpha (8-13) et beta (13-30) |
| Bruit | < 1 µV RMS | Signal EEG de qualité |
| Connectivité | Bluetooth 5.0 BLE | Faible consommation |
| Autonomie | ≥ 8 heures | Usage terrain |
| Certification | CE médical (classe IIa) | Réglementaire |
| Référence module | OpenBCI Ganglion | 4 canaux, 499 € |

**Algorithme embarqué :**
```
• Welch periodogramme (segments 4 s, recouvrement 50 %)
• Détection du pic alpha dans [7-14 Hz] (P3, Pz, O1)
• Détection du pic beta dans [13-30 Hz] (P3, Pz, O1)
• Calcul du rapport β/α pour chaque canal
• Moyenne sur les 3 canaux
• Rejet des artefacts (clignement, mouvement)
```

**Accessoires :**
```
• Casque EEG 4 canaux (sec ou humide)
• Électrodes Ag/AgCl pour EEG (50 unités)
• Gel conducteur (tube 100 ml)
• Ruban à mesurer pour placement 10-20
```

### 2.3 Module Spirométrie

**Fonction :** Mesure du rapport I/E (inspiration/expiration)

**Option A — Débitmètre électronique (recommandé) :**

| Paramètre | Valeur |
|-----------|--------|
| Capteur | Débitmètre à turbine ou pression différentielle |
| Plage de débit | 0,1-15 L/s |
| Précision | ± 3 % |
| Connectivité | USB-C ou Bluetooth |
| Autonomie | ≥ 100 heures |
| Référence | MLX90316 (turbine) ou MPXV7002 (pression) |
| Coût | 50 € pièce |

**Option B — Timer manuel (simplifié, pour prototype rapide) :**

```
• Application mobile avec chronomètre visuel
• L'utilisateur appuie sur « Inspir » et « Expir »
• L'application calcule I/E sur 10 cycles
• Précision : 0,1 s
• Coût : 0 € (intégré dans l'application)
```

**Algorithme :**
```
• Détection du début de l'inspiration
• Détection du début de l'expiration
• Durée I et E sur 10 cycles consécutifs
• Rejet des cycles aberrants (> 2 écarts-types)
• Sortie : I/E moyen, FR (fréquence respiratoire)
```

### 2.4 Module Température

**Fonction :** Mesure de la température corporelle

| Paramètre | Valeur |
|-----------|--------|
| Type | Thermomètre infrarouge tympanique |
| Plage | 34-42 °C |
| Précision | ± 0,1 °C |
| Temps de mesure | < 1 s |
| Connectivité | Bluetooth ou intégré app |
| Référence | MLX90614 (infrarouge) |
| Coût | 30 € pièce |

### 2.5 Module Application

**Fonction :** Interface utilisateur, calcul du GSI, stockage, export

**Spécifications logicielles :**

| Module | Technologie | Fonction |
|--------|-------------|----------|
| OS | Android 11+ / iOS 15+ | Multiplateforme |
| Framework | Flutter 3.x | Développement rapide |
| Base de données | SQLite locale | Hors-ligne |
| Sync | Cloud (Firebase) | Optionnel |
| Bluetooth | BLE (Bluetooth Low Energy) | Capteurs |
| Export | PDF, CSV, JSON | Dossier patient |

**Écrans :**

```
Écran 1 — Accueil
  • Nouvelle mesure (bouton principal)
  • Historique des mesures (liste chronologique)
  • Profil patient (nom, âge, sexe, région)
  • Paramètres (langue, unités, Bluetooth)

Écran 2 — Mesure
  • Guide pas à pas (5 étapes)
  • Timer pour chaque étape
  • Visualisation temps réel (ECG, EEG)
  • Validation automatique de la qualité

Écran 3 — Résultat
  • GSI total (chiffre + couleur)
  • Diagramme radar des 5 oscillateurs
  • Écarts individuels (δ₁ à δ₅)
  • Interprétation (vert/jaune/rouge)
  • Conseils personnalisés

Écran 4 — Suivi
  • Courbe d'évolution du GSI
  • Comparaison des mesures
  • Alertes (GSI > 0,10)
  • Export PDF
```

**Langues :**
```
• Français
• Anglais
• Swahili (optionnel Phase 2)
• Wolof (optionnel Phase 2)
```

### 2.6 Module Alimentation

| Composant | Spécification |
|-----------|--------------|
| Panneau solaire | 10W, pliable, 12V |
| Batterie | 10 000 mAh, 5V/2A USB |
| Autonomie | 3 jours de terrain (10 mesures/jour) |
| Protection | IP54 (résistant poussière, éclaboussures) |

---

## III. INTÉGRATION — LE KIT COMPLET

### 3.1 Contenu du kit

```
Kit GSI-Harmonic (coût total : 580 €)

┌──────────────────────────────────────────────────────────────┐
│  Valise de transport (IP65, 40×30×15 cm)                     │
│                                                              │
│  1. Module ECG (AD8232) ........................................ 100 €
│  2. Module EEG (OpenBCI Ganglion 4 canaux) ................... 200 €
│  3. Module Spirométrie (MLX90316 turbine) ..................... 50 €
│  4. Module Température (MLX90614 IR) ......................... 30 €
│  5. Smartphone dédié (Android 11, 4 Go RAM, 64 Go) ........... 100 €
│  6. Application GSI pré-installée ........................... 0 €
│  7. Panneau solaire 10W pliable ............................. 20 €
│  8. Batterie 10 000 mAh ..................................... 15 €
│  9. Accessoires (électrodes, câbles, gel) .................. 30 €
│ 10. Manuel d'utilisation illustré ........................... 10 €
│ 11. Fiche de suivi patient (50 unités) ...................... 5 €
│ 12. Stylo GSI (couleur : or) ................................ 0 €
│                                                              │
│  Total matériel : .................................................. 560 €
│  Assemblage et test : ................................................ 20 €
│  Total : ........................................................... 580 €
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Poids et dimensions

| Paramètre | Valeur |
|-----------|--------|
| Poids total | 3,5 kg |
| Dimensions valise | 40×30×15 cm |
| Autonomie batteries | 3 jours terrain |
| Temps d'installation | 5 minutes |
| Temps de mesure | 13 minutes |
| Temps d'interprétation | 2 minutes |

---

## IV. PLAN DE FABRICATION — PROTOTYPE RAPIDE

### 4.1 Étape 1 : Acquisition des composants (Semaine 1-2)

| Composant | Fournisseur | Délai | Coût |
|-----------|-------------|-------|------|
| AD8232 ECG module | SparkFun / Mouser | 1 semaine | 15 € × 3 = 45 € |
| OpenBCI Ganglion | OpenBCI | 2 semaines | 499 € × 2 = 998 € |
| MLX90614 IR | Mouser | 1 semaine | 15 € × 5 = 75 € |
| MLX90316 turbine | Mouser | 1 semaine | 8 € × 5 = 40 € |
| Smartphone (reconditionné) | Back Market | 1 semaine | 100 € × 3 = 300 € |
| Panneau solaire 10W | Amazon | 1 semaine | 20 € × 3 = 60 € |
| Batterie 10 000 mAh | Amazon | 1 semaine | 15 € × 3 = 45 € |
| Valise IP65 | Amazon | 1 semaine | 25 € × 3 = 75 € |
| **Total** | | | **1 638 €** |

### 4.2 Étape 2 : Développement application (Semaine 1-8)

| Module | Développeur | Temps | Coût |
|--------|-------------|-------|------|
| UI/UX | Designer | 2 semaines | 2 000 € |
| Bluetooth ECG | Développeur Flutter | 2 semaines | 2 000 € |
| Bluetooth EEG | Développeur Flutter | 3 semaines | 3 000 € |
| Spirométrie | Développeur Flutter | 1 semaine | 1 000 € |
| Calcul GSI | Développeur Flutter | 1 semaine | 1 000 € |
| Base de données | Développeur Flutter | 1 semaine | 1 000 € |
| Export PDF | Développeur Flutter | 1 semaine | 1 000 € |
| **Total** | | | **11 000 €** |

### 4.3 Étape 3 : Intégration et test (Semaine 6-12)

| Tâche | Responsable | Temps | Coût |
|-------|-------------|-------|------|
| Assemblage des 3 prototypes | Ingénieur biomédical | 2 semaines | 1 000 € |
| Calibration ECG | Ingénieur biomédical | 1 semaine | 500 € |
| Calibration EEG | Ingénieur biomédical | 1 semaine | 500 € |
| Test de fiabilité (test-retest) | Technicien | 3 semaines | 1 500 € |
| Test sur 10 sujets sains | Technicien + médecin | 2 semaines | 2 000 € |
| Correction des bugs | Développeur | 2 semaines | 2 000 € |
| Documentation | Rédacteur technique | 2 semaines | 1 000 € |
| **Total** | | | **8 500 €** |

### 4.4 Budget total prototype

| Poste | Coût |
|-------|------|
| Composants électroniques | 1 638 € |
| Développement application | 11 000 € |
| Intégration et test | 8 500 € |
| Transport et imprévus (10 %) | 2 114 € |
| **Total** | **23 252 €** |

### 4.5 Calendrier

```
Semaine 1-2  : Commande des composants
Semaine 1-8  : Développement application
Semaine 6-7  : Assemblage des 3 prototypes
Semaine 8-9  : Calibration
Semaine 10-12 : Tests de fiabilité
Semaine 12   : Prototype prêt pour Phase 1
```

---

## V. NORMES ET CERTIFICATIONS

### 5.1 Normes applicables

| Norme | Objet | Application |
|-------|-------|-------------|
| IEC 60601-1 | Sécurité électrique des dispositifs médicaux | ECG, EEG |
| IEC 60601-2-25 | Sécurité des électrocardiographes | ECG |
| IEC 60601-2-26 | Sécurité des électroencéphalographes | EEG |
| ISO 10993 | Biocompatibilité des matériaux | Électrodes |
| ISO 14971 | Gestion des risques | Dispositif complet |
| CEI 62304 | Cycle de vie du logiciel | Application GSI |
| RGPD | Protection des données patients | Application GSI |

### 5.2 Certification cible

```
Niveau de risque : Classe IIa (dispositif de diagnostic)
Organisme notifié : À identifier (EMERGO, MDSS, GMED)
Marquage CE : À obtenir pour Phase 2 (normes populationnelles)
Marquage CE simplifié : Possible pour Phase 1 (validation) avec déclaration de conformité constructeur
```

---

## VI. TESTS DE VALIDATION DU PROTOTYPE

### 6.1 Tests de laboratoire

| Test | Protocole | Critère d'acceptation |
|------|-----------|----------------------|
| Précision ECG | Comparaison avec ECG hospitalier (100 cycles) | Erreur RR < 1 ms |
| Précision EEG | Signal de test 10 Hz, 50 µV | Erreur fréquence < 0,05 Hz |
| Précision spirométrie | Volume calibré 3 L | Erreur < 3 % |
| Précision température | Bain thermostaté 37,0 °C | Erreur < 0,1 °C |
| Autonomie | Mesure continue | > 8 heures |
| Robustesse | Chute 1 m sur béton | Aucun dommage |

### 6.2 Tests cliniques (Phase 1)

| Test | Sujets | Critère |
|------|--------|---------|
| Test-retest à 1h | 20 | ICC > 0,80 |
| Test-retest à 1 semaine | 20 | ICC > 0,70 |
| Comparaison ECG hospitalier | 20 | Corrélation > 0,95 |
| Comparaison EEG hospitalier | 10 | Corrélation > 0,90 |
| Acceptabilité utilisateur | 20 | SUS > 70 |

---

## VII. FOURNISSEURS IDENTIFIÉS

| Composant | Fournisseur | Référence | Prix | Délai |
|-----------|-------------|-----------|------|-------|
| Module ECG | SparkFun | AD8232 | 15 € | 1 semaine |
| Module EEG | OpenBCI | Ganglion 4ch | 499 € | 2 semaines |
| Capteur IR | Mouser | MLX90614 | 15 € | 1 semaine |
| Turbine spirométrie | Mouser | MLX90316 | 8 € | 1 semaine |
| Smartphone | Back Market | Android reconditionné | 100 € | 1 semaine |
| Panneau solaire | Amazon | 10W pliable | 20 € | 1 semaine |
| Valise IP65 | Amazon | 40×30×15 cm | 25 € | 1 semaine |
| Électrodes ECG | Amazon | Ag/AgCl pré-gélifiées | 10 €/100 | 1 semaine |
| Gel EEG | Amazon | Électrogel | 15 €/tube | 1 semaine |

---

## VIII. LIVRABLES

| Livrable | Contenu | Date |
|----------|---------|------|
| **L1** | 3 prototypes fonctionnels du kit GSI-Harmonic | Semaine 12 |
| **L2** | Application GSI (Android, APK signé) | Semaine 10 |
| **L3** | Manuel d'utilisation (FR + EN) | Semaine 12 |
| **L4** | Rapport de tests de laboratoire | Semaine 12 |
| **L5** | Code source (GitHub privé, licence Univers-Holistique) | Semaine 12 |
| **L6** | Dossier de conception | Semaine 12 |

---

## IX. ÉQUIPE REQUISE

| Rôle | Compétences | Temps | Coût |
|------|-------------|-------|------|
| Chef de projet | Gestion de projet, biomédical | 3 mois | 5 000 € |
| Développeur Flutter | Mobile, Bluetooth, UI | 2 mois | 6 000 € |
| Ingénieur biomédical | Électronique, capteurs | 2 mois | 5 000 € |
| Technicien de test | Mesures, protocoles | 2 mois | 3 000 € |
| Designer UI/UX | Interfaces, expérience utilisateur | 1 mois | 2 000 € |
| **Total** | | | **21 000 €** |

---

> *« Un prototype en 3 mois, 23 000 €, 3 kits. Pas besoin d'usine — besoin d'un smartphone, d'un capteur ECG à 20 €, et d'une application. La Médecine Harmonique commence par un kit qui tient dans une valise et qui se déploie avec un panneau solaire. »*
>
> — **Kotto Alain**, 12/08/2026