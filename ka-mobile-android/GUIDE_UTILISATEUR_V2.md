# GUIDE UTILISATEUR — KA MOBILE V2

> **Version** 2.0 — PROTOCLE HARMONIQUE  
> **KA** — SYSTÈME D'INTENTION PERSONNELLE · HUD CYAN / AMBRE

---

## TABLE DES MATIÈRES

```
01  BIENVENUE DANS KA
02  PREMIERS PAS — ONBOARDING & DÉMO
03  NAVIGATION HUD
04  ACCUEIL — SPHÈRE & INTENTIONS
05  MESSAGES — ASSISTANT RÉSONANT
06  MÉMOIRE — ALBUMS & SOUVENIRS
07  PANNEAU HIÉROGLYPHE — 10 ESPACES AVANCÉS
   07.1  SANTÉ — DIAGNOSTIC HARMONIQUE
   07.2  VITAL KA — INDICE SOCIAL
   07.3  DÉCISION — ANALYSE COMPARATIVE
   07.4  HOLOGRAMMES — MODULES DE SAVOIR
   07.5  CODE & MATHS — CALCUL & ALGORITHMES
   07.6  ESPACE DISQUE — COMPRESSION HCV2
   07.7  PRÉPARER — BRIEFING RÉUNION
   07.8  VOYAGE — PLANIFICATION
   07.9  RELATION — PROFIL CONTACT
   07.10 CAPTURE — ENREGISTREMENT D'INTENTION
08  CAMÉRA — CAPTURE OPTIQUE
09  APPEL — INTERFACE VOCALE
10  ARCHITECTURE TECHNIQUE
11  FOIRE AUX QUESTIONS
```

---

## 01 — BIENVENUE DANS KA

```
╔══════════════════════════════════════════╗
║  KA MOBILE V2                            ║
║  SYSTÈME D'INTENTION PERSONNELLE         ║
║  THÉORIE HARMONIQUE UNIVERSELLE          ║
╚══════════════════════════════════════════╝
```

**KA** est votre intelligence personnelle de bord — 100% locale, zéro cloud, zéro GPU. Elle opère sur trois moteurs synchronisés :

| MODULE | FONCTION | LATENCE |
|--------|----------|---------|
| **KA HYBRID** | Moteur déterministe — 20 pathologies, 14 urgences, 20 concepts, 14 FAQ | 0,03 ms |
| **HARMONIC v3** | Calcul par émergence de phase — `sₙ = exp(i·α·n)` | O(1) |
| **HCV2** | Codec compressif — ratio 213× bit-exact | 49 s/frame 4K |

### CHARTE VISUELLE

| TOKEN | VALEUR | USAGE |
|-------|--------|-------|
| `bg.void` | `#030303` | Fond d'écran |
| `accent.cyan` | `#00F2FF` | Bordures HUD, icônes, graphiques |
| `accent.amber` | `#FFB300` | Panneau hiéroglyphe, accents sacrés |
| `surface` | `rgba(0,242,255,0.04)` | Cartes / modules |
| `text.primary` | `#00F2FF` | Titres glow |
| `text.muted` | `rgba(0,242,255,0.55)` | Labels, stats |

```
  ┌─────────────────────────────────────┐
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  bg.void #030303
  │  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐   │
  │  │  TITRE CYAN    ⚡ AMBRE      │   │  Bordures 1px cyan + glow
  │  │  ┌──────────┐ ┌──────────┐  │   │
  │  │  │ MODULE   │ │ MODULE   │  │   │  Coins angulaires
  │  │  │ surface  │ │ surface  │  │   │
  │  │  └──────────┘ └──────────┘  │   │
  │  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘   │
  └─────────────────────────────────────┘
```

---

## 02 — PREMIERS PAS — ONBOARDING & DÉMO

### INITIALISATION

Au premier démarrage, le protocole **KA DEMO** se déploie en trois phases :

```
PHASE 1 ⚡ ÉMERGENCE ARITHMÉTIQUE
  → Passez en mode Avion
  → Saisissez : 987654 × 123456
  → KA calcule sans addition binaire — résultat : 121 924 295 424

PHASE 2 🫀 PPG CAMÉRA
  → Placez votre visage dans le cadre HUD
  → KA mesure votre fréquence cardiaque par photopléthysmographie
  → Affichage BPM avec halo cyan pulsé

PHASE 3 🚀 ACTIVATION
  → Profil harmonique initialisé
  → 0 GPU · 0 cloud · 100% hors-ligne
  → Appuyez sur COMMENCER
```

### SÉLECTION D'INTENTIONS

L'écran d'onboarding vous invite à choisir **16 domaines de connaissance** (Santé, Sciences, Cuisine, Astronomie, Musique, Technologies…) ou à définir une intention personnalisée. Ces domaines alimentent la matrice de résonance de KA.

> `KA > USER > INTENTIONS > INITIALISÉES`

### RÉINITIALISATION

`Paramètres Android > Applications > KA > Stockage > Effacer données`

---

## 03 — NAVIGATION HUD

La barre de navigation inférieure suit le protocole HUD :

```
┌────────────────────────────────────────────┐
│                                            │
│              [ ZONE D'INTENTION ]          │
│                                            │
├────────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  │
│  │ACCUEIL│  │MESSAGES│  │MÉMOIRE│  │ PLUS │  │
│  │  🏠   │  │  💬   │  │  🧠   │  │  ⋮   │  │
│  └──────┘  └──────┘  └──────┘  └──────┘  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
└────────────────────────────────────────────┘
```

| ONGLET | CHEMIN | FONCTION |
|--------|--------|----------|
| **ACCUEIL** | `/` | Sphère KA + 4 intentions rapides |
| **MESSAGES** | `/messages` | Terminal conversationnel |
| **MÉMOIRE** | `/memory` | Archives visuelles |
| **PLUS** | — | Panneau hiéroglyphe — 10 espaces |

### ÉCRANS PLEIN ÉCRAN (NAVIGATION MASQUÉE)

| ÉCRAN | CHEMIN |
|-------|--------|
| 📞 Appel | `/call` |
| 📸 Caméra | `/camera` |
| ⚡ Démo | `/demo` |
| 🎯 Onboarding | `/onboarding` |

### PANNEAU HIÉROGLYPHE

Le bouton **PLUS** (⋮) déploie un panneau coulissant aux accents ambre, révélant 10 modules avancés :

```
┌──────────────────────────────────────┐
│  ┌─────────┐  ┌─────────┐           │
│  │ 📋      │  │ ✈️      │  AMBRE    │
│  │ PRÉPARER│  │ VOYAGE  │  ACCENT   │
│  │ réunion │  │ Tokyo   │  SACRÉ    │
│  └─────────┘  └─────────┘           │
│  ┌─────────┐  ┌─────────┐           │
│  │ 👤      │  │ 💡      │           │
│  │ RELATION│  │ IDÉE    │           │
│  │ Sophie  │  │ Capture │           │
│  └─────────┘  └─────────┘           │
│  ┌─────────┐  ┌─────────┐           │
│  │ ⚖️      │  │ 🫀      │           │
│  │ DÉCISION│  │ SANTÉ   │           │
│  └─────────┘  └─────────┘           │
│  ┌─────────┐  ┌─────────┐           │
│  │ 💾      │  │ 🧠      │           │
│  │ STOCKAGE│  │ HOLO-   │           │
│  │ HCV2    │  │ GRAMMES │           │
│  └─────────┘  └─────────┘           │
│  ┌─────────┐  ┌─────────┐           │
│  │ 💻      │  │ 🌍      │           │
│  │ CODE    │  │ VITAL KA│           │
│  │ & MATHS │  │ GSI     │           │
│  └─────────┘  └─────────┘           │
└──────────────────────────────────────┘
```

---

## 04 — ACCUEIL — SPHÈRE & INTENTIONS

```
╔══════════════════════════════════════╗
║  [ SPHÈRE KA ]                       ║
║  ──  RÉSONANCE HARMONIQUE  ──       ║
║                                      ║
║       ◉  ← pulsation φ              ║
║                                      ║
║  ┌──────┐ ┌──────┐ ┌──────┐ ┌────┐ ║
║  │ 💬   │ │ 🫀   │ │ 💾  │ │ 🧠 │ ║
║  │ CHAT │ │ SANTÉ│ │ HCV2│ │HOLO│ ║
║  └──────┘ └──────┘ └──────┘ └────┘ ║
╚══════════════════════════════════════╝
```

- **Sphère centrale** : animation harmonique pulsant au rythme de φ (1,618). Tap prolongé → ouvre le terminal Messages.
- **4 intentions rapides** : icônes néon cyan sur fond `rgba(0,242,255,0.04)` — bordures 1px, coins angulaires.

---

## 05 — MESSAGES — ASSISTANT RÉSONANT

```
╔══════════════════════════════════════════╗
║  TERMINAL CONVERSATIONNEL    v2.0       ║
║  ──────────────────────────────────────  ║
║                                          ║
║  [UTILISATEUR]  ♡  [KA]  →  5 ÉTAGES   ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ ÉTAGE 1 : HARMONIC (local)        │  ║
║  │ ÉTAGE 2 : KA HYBRID (déterministe)│  ║
║  │ ÉTAGE 3 : ⚡ SERVEUR (5s timeout)  │  ║
║  │ ÉTAGE 4 : KA HYBRID (re-test)     │  ║
║  │ ÉTAGE 5 : RÉPONSE SIMULÉE         │  ║
║  └────────────────────────────────────┘  ║
╚══════════════════════════════════════════╝
```

### DOMAINES DE QUESTION

| CATÉGORIE | EXEMPLES | BADGE |
|-----------|----------|-------|
| **IDENTITÉ** | « Qui es-tu ? » · « What are you? » | — |
| **PATHOLOGIES** | « Définis le diabète » · « C'est quoi le VIH ? » | ✅ |
| **URGENCES** | « Crise cardiaque → conduite à tenir » | ⚠️ |
| **SYMPTÔMES** | « J'ai mal à la tête et de la fièvre » | 💡 |
| **CONCEPTS** | « C'est quoi la résonance ? » · « Définis l'entropie » | ✅ |
| **CALCULS** | « 2+2 » · « 15% de 200 » · « sqrt(144) » | 🔢 |
| **FAQ** | « À quoi sert KA ? » · « Es-tu connecté à Internet ? » | ✅ |
| **ANGLAIS** | « What is diabetes? » · « Emergency: heart attack » | ✅ |

### BADGES DE CONFIANCE

```
 ✅ CONNAISSANCE CERTAINE    ⚠️ URGENCE (appelez les secours)
 🤖 RÉPONSE SERVEUR          🔢 CALCUL VALIDÉ
 💡 INFÉRENCE RÉSONANCE
```

### FONCTIONS

| ÉLÉMENT | DESCRIPTION |
|----------|-------------|
| Champ de saisie | Texte multi-lignes, bordures cyan 1px |
| 6 suggestions | Intentions rapides avec emoji |
| Grille 9 questions | 3×3 classées par thème |
| Persistance | Historique sauvegardé dans `localStorage` |
| Synthèse vocale | Bouton 🔊 — voix Web Speech API + Piper |

---

## 06 — MÉMOIRE — ALBUMS & SOUVENIRS

```
╔══════════════════════════════════════╗
║  KA MEMORY                           ║
║  ─────────────────────────            ║
║                                       ║
║  ROME AVEC SOPHIE                     ║
║  14–17 SEPT 2024 · 4 JOURS           ║
║                                       ║
║  [📷 47] [💬 12] [📍 ROME]           ║
║                                       ║
║  ┌──┐ ┌──┐ ┌──┐ ┌──┐               ║
║  │▐▐│ │▐▐│ │▐▐│ │+44│               ║
║  └──┘ └──┘ └──┘ └──┘               ║
║                                       ║
║  ── CHRONOLOGIE ──                   ║
║  ● COLISÉE — 23 PHOTOS               ║
║  ● MESSAGE ENVOYÉ À MARIE            ║
║  ● TRASTEVERE — DÎNER, 18 PHOTOS    ║
║                                       ║
║  [📷 CRÉER UN ALBUM] [PARTAGER]      ║
╚══════════════════════════════════════╝
```

---

## 07 — PANNEAU HIÉROGLYPHE — 10 ESPACES AVANCÉS

### 07.1 — SANTÉ — DIAGNOSTIC HARMONIQUE

```
╔══════════════════════════════════════════╗
║  KA SANTÉ   DIAGNOSTIC PAR RÉSONANCE    ║
║  ──────────────────────────────────────  ║
║  φ · π · e · √2 · √3 · √5              ║
╚══════════════════════════════════════════╝
```

#### 📸 PPG CAMÉRA — MESURE FRÉquence CARDIAQUE

1. Appuyer sur `MESURER FC PAR CAMÉRA (PPG)`
2. Cadrer le visage dans le réticule HUD
3. Immobilité 3s → affichage BPM avec halo cyan

#### 🫁 RESPIRATION HARMONIQUE

| PROFIL | INSPIRATION | EXPIRATION | FRÉQUENCE | EFFET |
|--------|:-----------:|:----------:|:---------:|-------|
| **🌊 RÉSONANCE** | 5 s | 5 s | 6 cycles/min | Cohérence φ — 0,1 Hz |
| **😌 RELAXATION** | 4 s | 8 s | 5 cycles/min | Calme profond |
| **⚡ ÉNERGIE** | 6 s | 4 s | 6 cycles/min | Vitalité |

La bille pulsée et l'option **VOIX** guident l'exercice.

#### 🔬 DIAGNOSTIC

```
SAISIE ORGANIQUE
  Symptômes : _______________ (séparés par ,)
  ┌─────────┐ ┌─────────┐
  │ FC bpm  │ │ TEMP °C │
  │ [____]  │ │ [____]  │
  ├─────────┤ ├─────────┤
  │ SYS mmHg│ │ DIA mmHg│
  │ [____]  │ │ [____]  │
  ├─────────┤ ├─────────┤
  │ SpO₂ %  │ │ ÂGE     │
  │ [____]  │ │ [____]  │
  └─────────┘ └─────────┘

  [ 🔬 DIAGNOSTIQUER ]
```

Analyse des constantes vs normes harmoniques — rapport avec badges d'anomalie.

---

### 07.2 — VITAL KA — INDICE SOCIAL

> `STATUT : INTÉGRATION GSI — GOLDEN HEALTH INDEX`

Le module **GSI** combine 5 oscillateurs physiologiques calibrés sur φ = 1,618 :

| OSCILLATEUR | RATIO | CIBLE φ |
|-------------|:-----:|:-------:|
| Systolique / Diastolique | S/D | 1,618 |
| Basse fréquence / Haute fréquence | LF/HF | 1,618 |
| Inspiration / Expiration | I/E | 1,618 |
| Onde β / Onde α | β/α | 1,618 |
| Température corporelle | T° | 37,0 °C |

Score 0-100 — visualisation radar cyan.

---

### 07.3 — DÉCISION — ANALYSE COMPARATIVE

```
╔══════════════════════════════════════╗
║  KA DÉCIDE                           ║
║  ───────────────────────────          ║
║                                       ║
║  CHANGER DE VOITURE ?                ║
║  BASÉ SUR 14 MOIS DE DONNÉES        ║
║                                       ║
║  ┌──────────────┐ ┌──────────────┐  ║
║  │ COÛT / AN    │ │ KM           │  ║
║  │ 2 340 €      │ │ 142k         │  ║
║  │ +18% vs 2023 │ │ 8 ans · Clio │  ║
║  └──────────────┘ └──────────────┘  ║
║                                       ║
║  CE QUE KA OBSERVE                    ║
║  Deux réparations en 4 mois — 890€. ║
║  L'assurance a augmenté de 15%.     ║
║                                       ║
║  ── COMPARAISON ──                   ║
║  GARDER LA CLIO       ████████╣ 78% ║
║  OCCASION RÉCENTE     ██████████╣100%║
║  SANS VOITURE         ████╣ 36%      ║
║                                       ║
║  [🔍 EXPLORER] [ANALYSER SANS VOIT.] ║
╚══════════════════════════════════════╝
```

---

### 07.4 — HOLOGRAMMES — MODULES DE SAVOIR

Modules de connaissance téléchargeables :

| HOLOGRAMME | CATÉGORIE | TAILLE | STATUT |
|------------|-----------|:------:|:------:|
| 🏥 MÉDECINE GÉNÉRALE | Santé | 4,2 Mo | ✅ INSTALLÉ |
| 📐 MATHÉMATIQUES | Sciences | 2,1 Mo | ✅ INSTALLÉ |
| 🌌 ASTRONOMIE | Sciences | 6,8 Mo | 📥 |
| 🍳 CUISINE & NUTRITION | Quotidien | 3,4 Mo | 📥 |
| ⚖️ DROIT & LÉGISLATION | Société | 8,5 Mo | 📥 |
| 🎵 MUSIQUE & HARMONIE | Arts | 5,1 Mo | 📥 |
| 💻 TECHNOLOGIES | Sciences | 7,3 Mo | 📥 |
| 🧠 PSYCHOLOGIE | Santé | 4,9 Mo | 📥 |

**Fonction HOLOGRAMME PERSONNALISÉ** :
```
INTENTION : _______________ [ CRÉER ]
→ Nouveau module de savoir synthétisé pour « nutrition »
```

Filtres : `[ TOUS ] [ INSTALLÉS ] [ DISPONIBLES ]`

---

### 07.5 — CODE & MATHS — CALCUL & ALGORITHMES

```
╔══════════════════════════════════════╗
║  CODE & MATHS                        ║
║  ────────────────────────             ║
║                                       ║
║  🧮 CALCULATRICE                      ║
║  [____________________] [=]          ║
║                                       ║
║  ┌─────────────────────────────┐     ║
║  │ 144                          │     ║
║  └─────────────────────────────┘     ║
║                                       ║
║  💻 GÉNÉRATEUR DE CODE                ║
║  [____________________] [▶]          ║
║                                       ║
║  ┌─────────────────────────────┐     ║
║  │ def factorielle(n):         │     ║
║  │   if n <= 1: return 1      │     ║
║  │   return n * factorielle(n-1)│    ║
║  └─────────────────────────────┘     ║
║                                       ║
║  [FACTORIELLE] [TRI BULLES] [FLASK] ║
║                                       ║
║  [ FERMER ]                          ║
╚══════════════════════════════════════╝
```

Formats supportés : `+`, `-`, `×`, `÷`, `sqrt()`, `% de`

---

### 07.6 — ESPACE DISQUE — COMPRESSION HCV2

```
╔══════════════════════════════════════╗
║  COMPRESSION HCV2    v2.0           ║
║  ───────────────────────────          ║
║                                       ║
║  PIPELINE 3 NIVEAUX                   ║
║                                       ║
║  NIVEAU 1 : SERVEUR ← API REST       ║
║  NIVEAU 2 : WASM    ← WebAssembly    ║
║  NIVEAU 3 : MIME    ← Estimation     ║
║                                       ║
║  ── PERFORMANCES ──                  ║
║  HHD2 (DICTIONNAIRE)  → 213× bit-exact║
║  HCVM (MODAL)        → ~80×          ║
║  VIDÉO 4K + GOP      → 8,4× (56,9 dB)║
║                                       ║
╚══════════════════════════════════════╝
```

| FORMAT | TYPE | RATIO | QUALITÉ |
|--------|------|:-----:|---------|
| **HCVH** | Hybride | ~50× | Élevée |
| **HCVM** | Modal | ~80× | Très élevée |
| **HHD2** | Dictionnaire | **213×** | Bit-exact (8/8) |
| **HHDC** | Full | ~200× | Ajustable |

---

### 07.7 — PRÉPARER — BRIEFING RÉUNION

```
╔══════════════════════════════════════╗
║  KA PREPARE                          ║
║  ──────────────────────               ║
║                                       ║
║  REVUE PRODUIT Q3                     ║
║  DEMAIN · 10H00 — 11H00              ║
║                                       ║
║  PARTICIPANTS                         ║
║  [S] Sophie  [M] Marc  [L] Léa  [+2]║
║                                       ║
║  BRIEFING KA                          ║
║  Sophie a relancé deux fois sur les  ║
║  chiffres de rétention. Marc attend  ║
║  la maquette finale.                 ║
║                                       ║
║  ── ORDRE DU JOUR ──                 ║
║  ● Chiffres de rétention             ║
║  ● Validation budget maquette        ║
║  ● ⚠ Retard livraison               ║
║                                       ║
║  [📤 PARTAGER] [OUVRIR DOC]          ║
╚══════════════════════════════════════╝
```

---

### 07.8 — VOYAGE — PLANIFICATION

```
╔══════════════════════════════════════╗
║  KA JOURNEY                          ║
║  ──────────────────────               ║
║                                       ║
║  TOKYO                               ║
║  8 — 15 OCT · 7 JOURS               ║
║                                       ║
║  ┌──────────────┐ ┌──────────────┐  ║
║  │ MÉTÉO        │ │ VOL          │  ║
║  │ 19° nuageux  │ │ CDG → HND    │  ║
║  │              │ │ dès 612 €    │  ║
║  └──────────────┘ └──────────────┘  ║
║                                       ║
║  ── ITINÉRAIRE ──                    ║
║  ● SHIBUYA · SHINJUKU  Jours 1–2    ║
║  ● KYOTO · EXCURSION   Jours 3–4    ║
║  ● ASAKUSA · RETOUR    Jours 5–7    ║
║                                       ║
║  Traduction japonais ↔ français      ║
║                                       ║
║  [✈ TOUT RÉSERVER] [MODIFIER]        ║
╚══════════════════════════════════════╝
```

---

### 07.9 — RELATION — PROFIL CONTACT

```
╔══════════════════════════════════════╗
║  KA RELATION                         ║
║  ───────────────────────              ║
║                                       ║
║       [S]  ← Halo ambre              ║
║       SOPHIE                          ║
║       AMIE PROCHE · DEPUIS 2019      ║
║                                       ║
║  APPELS  MESSAGES  PHOTOS  VOYAGES   ║
║    23      340      156      4       ║
║                                       ║
║  KA REMARQUE                          ║
║  Vous n'avez pas parlé depuis 9      ║
║  jours — c'est inhabituel. Rythme    ║
║  moyen : tous les 2 jours.           ║
║                                       ║
║  ── SOUVENIRS PARTAGÉS ──           ║
║  [▐▐] [▐▐] [▐▐] [+153]            ║
║                                       ║
║  S : "On garde ce resto en tête !"  ║
║      il y a 9 jours                  ║
║                                       ║
║  [📞 APPELER] [ÉCRIRE]               ║
╚══════════════════════════════════════╝
```

---

### 07.10 — CAPTURE — ENREGISTREMENT D'INTENTION

```
╔══════════════════════════════════════╗
║  KA CAPTURE                          ║
║  ───────────────────────              ║
║                                       ║
║       ◉  ← Microphone actif          ║
║       ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ ← Ondes     ║
║                                       ║
║  CE QUE KA A ENTENDU                  ║
║  "Une appli qui propose une recette  ║
║  en fonction de ce qui reste dans    ║
║  le frigo, avec une photo plutôt     ║
║  qu'une liste"                       ║
║                                       ║
║  STRUCTURÉ EN                         ║
║  [CONCEPT] Reconnaissance d'ingréd.  ║
║  [CIBLE]   Anti-gaspillage           ║
║  [LIÉ À]   2 idées similaires        ║
║                                       ║
║  [→ DÉVELOPPER] [CLASSER]            ║
╚══════════════════════════════════════╝
```

---

## 08 — CAMÉRA — CAPTURE OPTIQUE

```
╔══════════════════════════════════════╗
║  KA CAMÉRA                           ║
║  ───────────────────────              ║
║                                       ║
║  ┌────────────────────────────────┐  ║
║  │        ░░ VISEUR ░░            │  ║
║  │        ┌──┐                    │  ║
║  │        │  │ ← Réticule HUD    │  ║
║  │        └──┘                    │  ║
║  │                                │  ║
║  └────────────────────────────────┘  ║
║                                       ║
║           [ ⏺ ]                      ║
║                                       ║
║  ── GALERIE ──  3 MÉDIAS             ║
║  [IMG] [IMG] [IMG] [✚]              ║
║                                       ║
╚══════════════════════════════════════╝
```

- **Mode** : Photo (prise unique)
- **Viseur** : Réticule HUD cyan, overlay de cadrage
- **Stockage** : 12 dernières photos en cache local
- **Compression** : Encodage automatique via pipeline HCV2

---

## 09 — APPEL — INTERFACE VOCALE

```
╔══════════════════════════════════════╗
║  KA CALL                             ║
║  ───────────────────────              ║
║                                       ║
║        ◉  ← Halo pulsé cyan          ║
║        SOPHIE                         ║
║        APPEL EN COURS                 ║
║        03:42                          ║
║                                       ║
║  ▄▄ ▄▄▄ ▄▄▄▄ ▄▄ ▄▄▄ ▄▄▄▄ ▄▄       ║
║  ← Visualisation d'ondes vocales     ║
║                                       ║
║  [🔇]  [🔊]  [⌨]                    ║
║  MUET   HP    CLAVIER                 ║
║                                       ║
║         [ ✕ ]  ← Raccrocher          ║
║                                       ║
╚══════════════════════════════════════╝
```

Accès : depuis l'écran **Relation** (`/relation`) → bouton `APPELER`.

---

## 10 — ARCHITECTURE TECHNIQUE

```
┌─────────────────────────────────────────────────────────────┐
│                    KA MOBILE V2                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   COUCHE PRÉSENTATION                 │  │
│  │         React 18 · TypeScript · Tailwind 3            │  │
│  │         Vite 5 · React Router 6 · HUD Theme          │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                    MOTEURS IA                         │  │
│  │  ┌────────────────┐ ┌────────────────┐               │  │
│  │  │  KA HYBRID     │ │  HARMONIC v3  │               │  │
│  │  │  FNV-1a hash   │ │  PhaseEncoder │               │  │
│  │  │  Kuramoto      │ │  sₙ=exp(i·α·n)│               │  │
│  │  │  0,03 ms       │ │  O(1)         │               │  │
│  │  └────────────────┘ └────────────────┘               │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                  COMPRESSION                          │  │
│  │  HCV2 · WASM · Serveur · 3 niveaux · 213× bit-exact │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │               COUCHE MOBILE (Capacitor 7.6.8)        │  │
│  │  Android · BLE · Appels · SMS · Contacts · Stockage  │  │
│  │  Caméra · WiFi · Batterie · Compression ZIP natif   │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                │
│              ┌────────────┴────────────┐                   │
│              ▼                         ▼                   │
│  ┌─────────────────┐      ┌──────────────────────┐        │
│  │  SERVEUR API    │      │  APPAREIL ANDROID     │        │
│  │  localhost:8765 │      │  Cam · Mic · BLE · FS │        │
│  └─────────────────┘      └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### SPÉCIFICATIONS

| COMPOSANT | TECHNOLOGIE | VERSION |
|-----------|-------------|:-------:|
| Framework | React + TypeScript | 18.3.1 |
| Bundler | Vite | 5.4.21 |
| Styles | Tailwind CSS | 3.4.4 |
| Routeur | React Router | 6.26 |
| Mobile | Capacier | 7.6.8 |
| IA locale | KA Hybrid | 40 KB |
| IA émergente | Harmonic v3 | 9 KB |
| Compression | HCV2 WASM | 47+58 KB |
| Stockage | localStorage | illimité |

### PERFORMANCES IA

| MOTEUR | TECHNOLOGIE | LATENCE | USAGE |
|--------|-------------|:-------:|-------|
| **KA Hybrid** | FNV-1a + Kuramoto | **0,03 ms** | Identité, pathologies, FAQ, urgences |
| **Harmonic v3** | PhaseEncoder | **O(1)** | Calculs arithmétiques |
| **Serveur** | API REST | < 5 s | Réponses enrichies (optionnel) |

### PERFORMANCES COMPRESSION HCV2

| FORMAT | TYPE | RATIO | QUALITÉ |
|--------|------|:-----:|---------|
| **HHD2** | Dictionnaire | **213×** | Bit-exact (8/8) |
| **HHDC** | Full | ~200× | Ajustable |
| **HCVM** | Modal | ~80× | Très élevée |
| **HCVH** | Hybride | ~50× | Élevée |
| **VIDÉO 4K** | GOP + MC_RESIDUAL | **8,4×** | 56,9 dB |

---

## 11 — FOIRE AUX QUESTIONS

```
╔══════════════════════════════════════════════════════════════╗
║  FAQ — FOIRE AUX QUESTIONS                                  ║
║  ─────────────────────────────────────────────              ║
╚══════════════════════════════════════════════════════════════╝
```

### ❓ KA A-T-ELLE BESOIN D'INTERNET ?

**Non.** Le noyau (questions, identité, pathologies, concepts, FAQ, calculs) opère **100% hors-ligne**. Seules les fonctionnalités avancées (réponses serveur, compression HCV2 distante, synthèse vocale Piper) nécessitent une connexion.

### ❓ MES DONNÉES SONT-ELLES TRANSMISES ?

**Non.** Tout traitement local reste sur l'appareil. L'historique des messages est stocké dans le stockage local et n'est jamais transmis sans consentement explicite.

### ❓ COMMENT RÉINITIALISER KA ?

```
Paramètres Android > Applications > KA > Stockage > Effacer données
```

### ❓ LA CAMÉRA PPG EST-ELLE MÉDICALE ?

**Non.** La mesure de fréquence cardiaque par caméra est une **simulation**. Consultez un professionnel de santé pour tout diagnostic.

### ❓ PUIS-JE AJOUTER MES PROPRES CONNAISSANCES ?

Oui. Dans l'écran **HOLOGRAMMES**, utilisez le champ d'intention personnalisé pour créer un module dédié à un sujet de votre choix.

### ❓ KA EST-ELLE DISPONIBLE SUR iOS ?

Actuellement, KA est déployée sur **Android** via Capacitor. Une version iOS est à l'étude.

### ❓ COMMENT SIGNALER UN BUG ?

```
CANAL : Univers-Holistique
PROTOCOLE : Issue tracker / Contact direct
```

---

```
╔══════════════════════════════════════════════════════════════╗
║  © 2026 UNIVERS-HOLISTIQUE                                 ║
║  KA MOBILE V2 — SYSTÈME D'INTENTION PERSONNELLE            ║
║  CONSTRUIT AVEC LA THÉORIE HARMONIQUE UNIVERSELLE          ║
║  bg.void #030303 · accent.cyan #00F2FF · accent.amber #FFB300 ║
╚══════════════════════════════════════════════════════════════╝
```