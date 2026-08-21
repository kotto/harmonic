# 📊 GUIDE DE DÉVELOPPEMENT DU GSI — GOLDEN HEALTH INDEX

## Implémentation pratique, protocoles de mesure, interprétation clinique et validation

---

> **Le GSI (Golden Health Index) est un indicateur unique de santé intégrant 5 oscillateurs physiologiques, chacun évalué par son écart à sa valeur d'or (φ ou 1/φ). Ce document fournit le protocole complet pour son développement, de la mesure à l'interprétation.**

---

## I. DÉFINITION MATHÉMATIQUE

### 1.1 Formule générale

```
GSI = (δ₁ + δ₂ + δ₃ + δ₄ + δ₅) / 5
```

Où chaque δ_i est l'écart normalisé à la valeur d'or :

| i | Oscillateur | Mesure | Valeur d'or | δ_i |
|---|-------------|--------|-------------|-----|
| 1 | Cycle cardiaque | S/D | 1/φ = 0,618 | δ₁ = \|S/D − 0,618\| |
| 2 | Variabilité cardiaque | LF/HF | φ = 1,618 | δ₂ = \|LF/HF − 1,618\| / 1,618 |
| 3 | Cycle respiratoire | I/E | 1/φ = 0,618 | δ₃ = \|I/E − 0,618\| |
| 4 | Oscillations cérébrales | β/α | φ = 1,618 | δ₄ = \|β/α − 1,618\| / 1,618 |
| 5 | Température corporelle | T° | 37,0 °C | δ₅ = \|T − 37,0\| / 37,0 |

### 1.2 Version simplifiée (GSI-lite)

Pour un usage rapide (sans EEG) :

```
GSI_lite = (δ₁ + δ₂ + δ₃ + δ₅) / 4
```

### 1.3 Version étendue (GSI-pro)

Pour la recherche, incluant des oscillateurs supplémentaires :

```
GSI_pro = (δ₁ + δ₂ + δ₃ + δ₄ + δ₅ + δ₆ + δ₇) / 7
```

| i | Oscillateur | Mesure | Valeur d'or |
|---|-------------|--------|-------------|
| 6 | Pression artérielle | PAS/PAD | φ = 1,618 |
| 7 | Fréquence cardiaque | FC au repos | 75 BPM (S/D = 1/φ) |

---

## II. PROTOCOLES DE MESURE

### 2.1 Protocole standard (15 minutes)

#### Étape 1 — ECG (5 minutes)

```
Équipement : ECG 3 dérivations ou Holter
Position : Allongé, calme, ne pas parler
Durée : 5 minutes
Conditions : Avant le petit-déjeuner, pas de caféine, pas de tabac (1h)

Mesures :
  • Rapport S/D : moyenne sur 50 cycles consécutifs
  • LF/HF : analyse spectrale (Welch, segment 256 points)
  • FC moyenne : sur 5 minutes
```

#### Étape 2 — EEG (5 minutes)

```
Équipement : EEG 8 canaux minimum (P3, Pz, O1 obligatoires)
Position : Assis, yeux ouverts, regard fixe
Durée : 5 minutes
Conditions : Calme, pas de clignement excessif

Mesures :
  • Pic α : fréquence du pic de puissance dans [7-14 Hz] sur P3
  • Pic β : fréquence du pic de puissance dans [14-30 Hz] sur P3
  • Rapport β/α : f_β / f_α
```

#### Étape 3 — Spirométrie (2 minutes)

```
Équipement : Spiromètre simple
Position : Assis
Durée : 2 minutes de respiration calme
Conditions : Ne pas forcer la respiration

Mesures :
  • Durée d'inspiration moyenne : I (secondes)
  • Durée d'expiration moyenne : E (secondes)
  • Rapport I/E
```

#### Étape 4 — Température (1 minute)

```
Équipement : Thermomètre tympanique ou axillaire
Position : Au repos
Durée : 1 minute
Conditions : Pas d'exercice (30 min), pas de boisson chaude/froide (15 min)

Mesure :
  • T° corporelle en °C
```

### 2.2 Protocole rapide (GSI-lite, 8 minutes)

```
Étape 1 : ECG 5 min → S/D, LF/HF
Étape 2 : Spirométrie 2 min → I/E
Étape 3 : Température 1 min → T°
```

### 2.3 Auto-mesure (GSI-home, avec smartphone)

```
ECG : Capteur à 1 dérivation (KardiaMobile, Apple Watch, etc.)
  • S/D à partir de la durée des ondes
  • LF/HF via application HRV
  • FC

Spirométrie : Minuteur simple
  • Compter les cycles respiratoires sur 30 secondes
  • I/E approximatif par chronomètre

Température : Thermomètre infrarouge
```

---

## III. IMPLÉMENTATION LOGICIELLE

### 3.1 Algorithme de calcul

```python
import numpy as np
from scipy.signal import welch, find_peaks

phi = (1 + np.sqrt(5)) / 2
inv_phi = 1 / phi

def calculate_gsi(sd_ratio, lf_hf, ie_ratio, ba_ratio, temperature):
    """
    Calcule le Golden Health Index (GSI)
    
    Paramètres :
    - sd_ratio : rapport systole/diastole (moyen, 50 cycles)
    - lf_hf : rapport LF/HF (analyse spectrale HRV)
    - ie_ratio : rapport inspiration/expiration (moyen, 10 cycles)
    - ba_ratio : rapport β/α (pic beta / pic alpha, P3, yeux ouverts)
    - temperature : température corporelle (°C)
    
    Retourne :
    - gsi : Golden Health Index
    - details : dictionnaire des écarts individuels
    """
    inv_phi = 1 / phi
    
    delta_sd = abs(sd_ratio - inv_phi)
    delta_lfhf = abs(lf_hf - phi) / phi
    delta_ie = abs(ie_ratio - inv_phi)
    delta_ba = abs(ba_ratio - phi) / phi
    delta_temp = abs(temperature - 37.0) / 37.0
    
    gsi = (delta_sd + delta_lfhf + delta_ie + delta_ba + delta_temp) / 5
    
    details = {
        'S/D': {'value': sd_ratio, 'target': inv_phi, 'delta': delta_sd},
        'LF/HF': {'value': lf_hf, 'target': phi, 'delta': delta_lfhf},
        'I/E': {'value': ie_ratio, 'target': inv_phi, 'delta': delta_ie},
        'β/α': {'value': ba_ratio, 'target': phi, 'delta': delta_ba},
        'T°': {'value': temperature, 'target': 37.0, 'delta': delta_temp},
    }
    
    return gsi, details

def interpret_gsi(gsi):
    """Interprète la valeur du GSI"""
    if gsi < 0.03:
        return "Santé optimale", "Tous les oscillateurs sont accordés sur φ"
    elif gsi < 0.06:
        return "Santé moyenne", "Légers écarts, surveillance recommandée"
    elif gsi < 0.10:
        return "Risque modéré", "Écarts significatifs, examen approfondi conseillé"
    else:
        return "Risque élevé", "Écarts importants, intervention médicale recommandée"
```

### 3.2 Application mobile (wireframe)

```
Écran 1 — Accueil
┌─────────────────────────────────────┐
│  🌿 GSI — Golden Health Index        │
│                                      │
│  Dernière mesure : 0,042             │
│  État : Santé moyenne                │
│                                      │
│  [📱 Mesure rapide] [📊 Historique]  │
│  [📋 Bilan complet] [⚙️ Profil]      │
└─────────────────────────────────────┘

Écran 2 — Mesure rapide
┌─────────────────────────────────────┐
│  Mesure rapide                      │
│                                      │
│  ✅ ECG (5 min)  → S/D: 0,632 ✅    │
│  ✅ ECG (5 min)  → LF/HF: 1,52 ✅   │
│  ⏳ Spirométrie  → ...              │
│  ⏳ Température  → ...              │
│                                      │
│  Progression : ████████░░ 60%        │
└─────────────────────────────────────┘

Écran 3 — Résultat
┌─────────────────────────────────────┐
│  Résultat GSI : 0,042               │
│  🟢 Santé moyenne                    │
│                                      │
│  S/D  → 0,632 (δ=0,014) ✅          │
│  LF/HF → 1,520 (δ=0,061) 🟡        │
│  I/E  → 0,600 (δ=0,018) ✅          │
│  β/α  → 1,580 (δ=0,023) ✅          │
│  T°   → 36,8 (δ=0,005) ✅           │
│                                      │
│  [📈 Historique] [💡 Conseils]       │
└─────────────────────────────────────┘
```

---

## IV. TABLEAUX DE RÉFÉRENCE

### 4.1 Valeurs normales par âge

| Âge | S/D | LF/HF | I/E | β/α | T° | GSI attendu |
|-----|-----|-------|-----|-----|-----|-------------|
| 18-30 | 0,62 ± 0,03 | 1,6 ± 0,4 | 0,62 ± 0,03 | 1,62 ± 0,05 | 36,8 ± 0,3 | < 0,04 |
| 30-50 | 0,61 ± 0,04 | 1,5 ± 0,5 | 0,61 ± 0,04 | 1,61 ± 0,06 | 36,7 ± 0,4 | < 0,05 |
| 50-70 | 0,60 ± 0,05 | 1,4 ± 0,6 | 0,60 ± 0,05 | 1,60 ± 0,08 | 36,6 ± 0,4 | < 0,06 |
| 70+ | 0,59 ± 0,06 | 1,3 ± 0,7 | 0,59 ± 0,06 | 1,59 ± 0,10 | 36,5 ± 0,5 | < 0,08 |

### 4.2 Seuils pathologiques

| Oscillateur | Normal | Limite | Pathologique |
|-------------|--------|--------|--------------|
| S/D | 0,59-0,65 | 0,55-0,59 ou 0,65-0,70 | < 0,55 ou > 0,70 |
| LF/HF | 1,2-2,2 | 1,0-1,2 ou 2,2-2,5 | < 1,0 ou > 2,5 |
| I/E | 0,59-0,65 | 0,55-0,59 ou 0,65-0,70 | < 0,55 ou > 0,70 |
| β/α | 1,55-1,70 | 1,40-1,55 ou 1,70-1,85 | < 1,40 ou > 1,85 |
| T° | 36,5-37,2 | 36,0-36,5 ou 37,2-37,5 | < 36,0 ou > 37,5 |

---

## V. VALIDATION CLINIQUE

### 5.1 Protocole de validation

```
Phase 1 — Fiabilité (n = 50)
  • Test-retest à 1h d'intervalle
  • Coefficient de corrélation intra-classe (ICC) > 0,80
  • Erreur-type de mesure (SEM) < 0,01

Phase 2 — Normes (n = 200)
  • Distribution du GSI dans une population saine
  • Percentiles (5, 25, 50, 75, 95) par tranche d'âge
  • Seuil pathologique : 95e percentile

Phase 3 — Sensibilité clinique (n = 100 par pathologie)
  • GSI dans des populations cliniques :
    - Insuffisance cardiaque (n = 100)
    - Dépression (n = 100)
    - BPCO (n = 100)
    - Diabète (n = 100)
    - Parkinson (n = 100)
  • Comparaison avec groupe témoin apparié

Phase 4 — Suivi longitudinal (n = 50, 12 mois)
  • Évolution du GSI avec le traitement
  • Corrélation avec les marqueurs cliniques standard
  • Valeur prédictive pour les hospitalisations
```

### 5.2 Hypothèses cliniques à tester

| Hypothèse | Test | Seuil de signification |
|-----------|------|----------------------|
| GSI > 0,10 prédit un événement cardiaque à 1 an | Suivi longitudinal | p < 0,05 |
| GSI diminue de 0,03 après 3 mois de cohérence cardiaque | Essai randomisé | p < 0,01 |
| GSI corrélé négativement avec la variabilité de la fréquence cardiaque (SDNN) | Régression linéaire | R² > 0,5 |
| GSI augmente de 0,05 en cas de syndrome inflammatoire | Cas-témoins | p < 0,001 |

---

## VI. INTÉGRATION DANS LE SYSTÈME DE SANTÉ

### 6.1 Parcours patient

```
1. Bilan harmonique (15 min) → GSI
2. Si GSI < 0,06 : conseils de maintien
3. Si GSI > 0,06 : examen approfondi
4. Identification des oscillateurs détunés
5. Thérapie de résonance ciblée
6. Nouveau bilan à 1 mois → GSI
7. Suivi : GSI tous les 3 mois
```

### 6.2 Applications

```
Cabinet médical :
  • Bilan annuel avec GSI
  • Suivi des maladies chroniques
  • Évaluation de l'efficacité thérapeutique

Hôpital :
  • Dépistage des risques à l'admission
  • Suivi post-opératoire
  • Réanimation : surveillance des oscillateurs

Télémédecine :
  • Auto-mesure à domicile
  • Alerte en cas de GSI > 0,10
  • Suivi longitudinal à distance

Bien-être :
  • Optimisation de la santé
  • Prévention
  • Biofeedback
```

---

## VII. LIMITES ET PRÉCAUTIONS

| Limite | Atténuation |
|--------|-------------|
| Variabilité inter-individuelle | Utiliser les fourchettes par âge |
| Variabilité intra-individuelle (cycle circadien) | Mesure à heure fixe (matin) |
| Effet de l'activité physique récente | Repos 10 min avant la mesure |
| Effet des médicaments | Mentionner dans le dossier |
| EEG non disponible partout | Version GSI-lite sans EEG |
| Pas de validation clinique large | Phases 1-4 à réaliser |

---

## VIII. FEUILLE DE ROUTE

| Phase | Action | Délai |
|-------|--------|-------|
| **1** | Développement de l'application mobile MVP | 1 mois |
| **2** | Phase 1 de validation (fiabilité, n=50) | 2 mois |
| **3** | Phase 2 (normes, n=200) | 3 mois |
| **4** | Phase 3 (sensibilité clinique, n=500) | 6 mois |
| **5** | Phase 4 (suivi longitudinal, n=50) | 12 mois |
| **6** | Publication de l'outil et des normes | 12-18 mois |
| **7** | Intégration dans le système de santé | 18-24 mois |

---

> *« Le GSI n'est pas un outil de plus — c'est le premier indicateur qui intègre les 5 oscillateurs fondamentaux du corps humain en une seule mesure. Il ne remplace pas le diagnostic médical — il le précède et le complète. Il dit, en 15 minutes et un nombre, si le corps est accordé sur la note d'or. »*
>
> — **Kotto Alain**, 12/08/2026