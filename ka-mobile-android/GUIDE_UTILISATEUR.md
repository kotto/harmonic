# Guide Utilisateur — KA Mobile

> **Version** 1.0 — 13 août 2026  
> **KA** — Votre intelligence personnelle, locale et harmonique

---

## Table des matières

1. [Bienvenue dans KA](#1-bienvenue-dans-ka)
2. [Premiers pas : Onboarding et Démo](#2-premiers-pas--onboarding-et-démo)
3. [Navigation principale](#3-navigation-principale)
4. [Accueil — Le tableau de bord](#4-accueil--le-tableau-de-bord)
5. [Messages — L'assistant conversationnel](#5-messages--lassistant-conversationnel)
6. [Mémoire — Albums et souvenirs](#6-mémoire--albums-et-souvenirs)
7. [Plus — Les 10 espaces avancés](#7-plus--les-10-espaces-avancés)
   - [7.1 Santé — Diagnostic harmonique](#71-santé--diagnostic-harmonique)
   - [7.2 Vital Ka — Santé sociale](#72-vital-ka--santé-sociale)
   - [7.3 Décision — Aide à la décision](#73-décision--aide-à-la-décision)
   - [7.4 Hologrammes — Savoirs spécialisés](#74-hologrammes--savoirs-spécialisés)
   - [7.5 Code & Maths — Calculs et algorithmes](#75-code--maths--calculs-et-algorithmes)
   - [7.6 Espace disque — Analyse et compression](#76-espace-disque--analyse-et-compression)
   - [7.7 Préparer — Briefing de réunion](#77-préparer--briefing-de-réunion)
   - [7.8 Voyage — Planification de voyage](#78-voyage--planification-de-voyage)
   - [7.9 Relation — Gestion de contact](#79-relation--gestion-de-contact)
   - [7.10 Capture — Capture d'idée](#710-capture--capture-didée)
8. [Caméra — Photos et vidéos](#8-caméra--photos-et-vidéos)
9. [Appel — Interface téléphonique](#9-appel--interface-téléphonique)
10. [Fonctionnement technique](#10-fonctionnement-technique)
11. [Foire aux questions](#11-foire-aux-questions)

---

## 1. Bienvenue dans KA

**KA** est votre intelligence personnelle qui fonctionne **100% en local** — sans GPU, sans cloud, sans abonnement. Elle combine :

- **Un moteur d'IA déterministe** (KA Hybrid) capable de répondre à vos questions sur la santé, les concepts, les calculs, les urgences, en français comme en anglais.
- **Un cœur arithmétique émergent** (Harmonic v3) qui calcule par synchronisation de phase, sans addition binaire.
- **Un codec de compression** (HCV2) qui réduit vos photos, fichiers et messages jusqu'à **200×** avec une qualité parfaite.
- **Une intelligence sociale** qui analyse vos relations, vos dépenses, vos voyages et vous aide à décider.

L'interface utilise le thème **Deep Ocean** : un fond `#000508` avec des accents teal/cyan (`#2dd4bf`) et des effets de verre dépoli.

---

## 2. Premiers pas — Onboarding et Démo

### Premier lancement

Lorsque vous ouvrez KA pour la première fois :

1. **Écran de démonstration** — Une mini-démo vous présente deux prouesses techniques :
   - **⚡ Émergence arithmétique** : tapez `987654 × 123456` en mode Avion pour voir KA calculer sans addition binaire.
   - **🫀 PPG Caméra** : placez votre doigt ou visage devant la caméra pour mesurer votre fréquence cardiaque.
   - Après la démo, appuyez sur **🚀 Commencer**.

2. **Écran d'onboarding** — Sélectionnez vos **centres d'intérêt** parmi 16 domaines (Santé, Sciences, Cuisine, Musique, Technologie, etc.) ou ajoutez un domaine personnalisé. Ces centres d'intérêt permettent à KA de personnaliser ses réponses.

> 💡 **Conseil :** Plus vous sélectionnez de domaines, plus KA pourra vous fournir des réponses pertinentes.

### Réinitialisation

Pour revoir l'onboarding, effacez les données de l'application dans les paramètres Android ou supprimez la clé `ka_user` du stockage local.

---

## 3. Navigation principale

La navigation se compose d'une **barre inférieure** avec trois onglets principaux et un bouton **Plus** :

| Icône | Onglet | Chemin | Description |
|-------|--------|--------|-------------|
| 🏠 | **Accueil** | `/` | Tableau de bord, sphère KA, actions rapides |
| 💬 | **Messages** | `/messages` | Chat avec l'assistant KA |
| 🧠 | **Mémoire** | `/memory` | Albums photos et souvenirs |
| ⋮ | **Plus** | — | Panneau des 10 espaces avancés |

Certains écrans sont en **plein écran** (pas de barre de navigation) :
- 📞 **Appel** — Interface d'appel téléphonique
- 📸 **Caméra** — Prise de photos et vidéos
- ⚡ **Démo** — Démonstration interactive
- 🎯 **Onboarding** — Configuration initiale

### Le panneau Plus

Le bouton **Plus** (⋮) ouvre un panneau coulissant avec 10 espaces supplémentaires :

| Emoji | Espace | Chemin | Utilité |
|-------|--------|--------|---------|
| 📋 | Préparer | `/prepare` | Briefing de réunion |
| ✈️ | Voyage | `/journey` | Itinéraire de voyage |
| 👤 | Relation | `/relation` | Profil de contact |
| 💡 | Idée | `/capture` | Capture d'idée vocale |
| ⚖️ | Décision | `/decide` | Analyse de décision |
| 🫀 | Santé | `/health` | Diagnostic harmonique |
| 💾 | Espace disque | `/storage` | Compression HCV2 |
| 🧠 | Hologrammes | `/hologram` | Modules de savoir |
| 💻 | Code & Maths | `/code` | Calculs et code |
| 🌍 | Vital Ka | `/vitalka` | Santé sociale GSI |

---

## 4. Accueil — Le tableau de bord

L'écran d'accueil présente :

- **La sphère KA** — Une animation harmonique au centre. Un tap prolongé vous amène à l'assistant Messages.
- **4 actions rapides** :
  - 💬 **Messages** — Ouvre le chat
  - 🫀 **Santé** — Accès au diagnostic
  - 💾 **Stockage** — Compression de fichiers
  - 🧠 **Hologrammes** — Savoirs spécialisés

En bas se trouve la barre de navigation principale.

---

## 5. Messages — L'assistant conversationnel

### Principe

KA utilise un pipeline de réponse à 5 étages :

1. **Harmonic (local)** — Tentative de calcul arithmétique par émergence de phase
2. **KA Hybrid (local)** — Moteur déterministe avec 20 pathologies, 14 urgences, 20 concepts, 14 FAQ, 3 identités, 3 refus
3. **Serveur (si connecté)** — API `/api/chat` avec timeout de 5 secondes
4. **KA Hybrid (re-test)** — Nouvelle tentative si le serveur a renvoyé un refus
5. **Réponse simulée** — Dernier recours si tout échoue

### Que pouvez-vous demander ?

- **Identité** : « Qui es-tu ? », « What are you? »
- **Pathologies** : « Définis le diabète », « C'est quoi le VIH ? », « Explain malaria »
- **Urgences** : « Que faire en cas de crise cardiaque ? », « Brûlure grave → conduite à tenir »
- **Symptômes** : « J'ai mal à la tête et de la fièvre » (KA propose des causes)
- **Concepts** : « C'est quoi la résonance ? », « Définis l'entropie »
- **Calculs** : « 2+2 », « 15% de 200 », « sqrt(144) »
- **FAQ** : « À quoi sert KA ? », « Comment ça marche ? », « Es-tu connecté à Internet ? »
- **Anglais** : « What is diabetes? », « Define resonance », « Emergency: heart attack »

### Formats de réponse

KA indique la **confiance** de sa réponse avec des badges :

| Badge | Signification |
|-------|---------------|
| ✅ | Connaissance certaine (pathologie, concept, FAQ) |
| ⚠️ | Urgence — conseil non médical, appelez les secours |
| 🤖 | Réponse du serveur distant |
| 🔢 | Calcul validé |
| 💡 | Inférence par résonance |

### Fonctionnalités de l'écran

- **Champ de texte** — Tapez votre question (support multi-lignes)
- **Suggestions** — 6 cartes de suggestions rapides (santé, urgences, calculs, etc.)
- **Grille de questions** — 9 questions pré-écrites classées par thème
- **Persistance** — L'historique des messages est sauvegardé automatiquement
- **Synthèse vocale** — KA peut répondre à voix haute (bouton 🔊)

---

## 6. Mémoire — Albums et souvenirs

L'espace **Mémoire** vous permet de revivre vos souvenirs :

- **Photos** — Grille de 4 photos avec compteur
- **Pills** — Tags : nombre de photos, messages, lieu
- **Dernier message** — Affiché dans une carte Insight
- **Chronologie** — Ligne temporelle des événements (dates, lieux)
- **Actions** — Créer un album, Partager

> 💡 **Conseil :** Les photos que vous prenez avec la **Caméra** apparaissent ici.

---

## 7. Plus — Les 10 espaces avancés

### 7.1 Santé — Diagnostic harmonique

L'écran de santé combine plusieurs outils :

#### 📸 PPG Caméra
Mesurez votre **fréquence cardiaque** (BPM) via la caméra :
1. Appuyez sur « Mesurer FC par caméra (PPG) »
2. Placez votre visage dans le cadre ou votre doigt sur l'objectif
3. Restez immobile 3 secondes
4. La fréquence s'affiche (60-90 BPM simulé)

#### 🫁 Assistance respiratoire harmonique
3 profils de respiration guidée :

| Profil | Inspiration | Expiration | Effet |
|--------|-------------|------------|-------|
| 🌊 Résonance | 5 s | 5 s | Cohérence φ (0,1 Hz) |
| 😌 Relaxation | 4 s | 8 s | Calme profond |
| ⚡ Énergie | 6 s | 4 s | Vitalité |

La bille pulsée vous guide visuellement. Activez l'option **Voix** pour un guidage audio.

#### 🔬 Diagnostic
1. Saisissez vos **symptômes** (ex: « palpitations, anxiete, insomnie »)
2. Remplissez les **constantes** : FC, température, tension (sys/dia), SpO₂, âge
3. Appuyez sur **Diagnostiquer**
4. KA analyse et signale les anomalies avec des recommandations

---

### 7.2 Vital Ka — Santé sociale

> ⚠️ **Écran non encore implémenté** — L'icône « Vital Ka » dans le panneau Plus pointe vers cet écran, qui affiche l'intégration GSI (Golden Health Index) combinant 5 oscillateurs physiologiques.

Le **Golden Health Index (GSI)** combine :
- **S/D** — Ratio systolique/diastolique
- **LF/HF** — Balance sympathique/parasympathique
- **I/E** — Ratio inspiration/expiration
- **β/α** — Ratio ondes cérébrales
- **T°** — Température corporelle

Tous sont comparés au **nombre d'or φ = 1,618**. Score 0-100, visualisé sous forme de radar.

---

### 7.3 Décision — Aide à la décision

KA analyse une situation concrète avec des données chiffrées. Exemple intégré : **« Changer de voiture ? »**

- **Coût / an** — Carte avec variation vs année précédente
- **Kilométrage** — Carte avec âge du véhicule
- **Insight KA** — Ce que KA observe de la situation
- **Comparaison** — 3 options avec barres de coût :
  1. ✅ Garder la voiture actuelle
  2. ⭐ Occasion récente (conseillé)
  3. 💰 Sans voiture
- **Actions** — Explorer les occasions, Analyser sans voiture

---

### 7.4 Hologrammes — Savoirs spécialisés

Les **Hologrammes** sont des modules de connaissance téléchargeables :

| Hologramme | Catégorie | Taille | Pré-installé |
|------------|-----------|--------|:------------:|
| 🏥 Médecine Générale | Santé | 4,2 Mo | ✅ |
| 📐 Mathématiques | Sciences | 2,1 Mo | ✅ |
| 🌌 Astronomie | Sciences | 6,8 Mo | — |
| 🍳 Cuisine & Nutrition | Quotidien | 3,4 Mo | — |
| ⚖️ Droit & Législation | Société | 8,5 Mo | — |
| 🎵 Musique & Harmonie | Arts | 5,1 Mo | — |
| 💻 Technologies | Sciences | 7,3 Mo | — |
| 🧠 Psychologie | Santé | 4,9 Mo | — |

**Fonctionnalités :**
- Filtres : Tous / Installés / Disponibles
- **Hologramme personnalisé** : Tapez un domaine qui vous intéresse (ex: « nutrition ») → KA crée un module dédié
- Installation en un clic

---

### 7.5 Code & Maths — Calculs et algorithmes

#### 🧮 Calculatrice
- Opérations : `+`, `-`, `×`, `÷`, `sqrt()`, `% de`
- Validation par touche **=** ou touche **Entrée**
- Résultat en grand format

#### 💻 Générateur de code
Demandez des extraits de code en langage naturel :
- « une fonction factorielle en python »
- « tri à bulles »
- « API Flask »
- « palindrome »
- « regex email »
- « CSV Reader »

Le code est affiché dans une zone style IDE (fond sombre, police mono).

---

### 7.6 Espace disque — Analyse et compression

> ⚠️ **Écran d'analyse de stockage** — Utilise le codec **HCV2** pour compresser vos fichiers.

L'écran affiche la capacité de compression de KA selon un pipeline à **3 niveaux** :

1. **Serveur** — Compression via le backend API (meilleur ratio, nécessite connexion)
2. **WASM** — Compression via le codec WebAssembly intégré (rapide, local)
3. **Estimation MIME** — Estimation par type de fichier (instantané)

**Performances mesurées (HCV2)** :
- Compression dictionnaire : **213×** (bit-exact, 8/8)
- Compression vidéo : **8,4×** avec GOP et sélecteur 3 modes (56,9 dB, 4K native)
- Mémoire bornée : 4K à 49 s/frame

---

### 7.7 Préparer — Briefing de réunion

KA vous prépare pour une réunion importante :

- **Participants** — Avatars avec initiales et noms
- **Briefing KA** — Ce que KA a observé avant la réunion
- **Ordre du jour** — Points avec marqueurs de sensibilité (⚠️ point sensible)
- **Actions** — Partager le briefing, Ouvrir le document

---

### 7.8 Voyage — Planification de voyage

Exemple intégré : **Tokyo, 8-15 octobre**

- **Météo** — Température et conditions
- **Vol** — Aéroports, prix indicatif
- **Itinéraire** — Chronologie jour par jour avec lieux et activités
- **Traduction** — Indicateur de traduction automatique activée
- **Action** — Tout réserver, Modifier

---

### 7.9 Relation — Gestion de contact

Profil d'une relation (exemple : Sophie, amie proche depuis 2019) :

- **Stats** : appels, messages, photos, voyages
- **Insight KA** — Analyse du rythme de communication (« Vous n'avez pas parlé depuis 9 jours… »)
- **Souvenirs partagés** — Photos communes
- **Dernier message** — Affiché dans une carte
- **Actions** — Appeler, Écrire

---

### 7.10 Capture — Capture d'idée

Un espace pour capturer une idée vocale :

- **Microphone** — Animation de pulsation harmonique
- **Visualisation d'ondes** — 18 barres animées simulant la voix
- **Transcription** — Ce que KA a entendu (ex: idée d'application anti-gaspillage)
- **Structuration** — Tags : Concept, Cible, Lié à
- **Actions** — Développer l'idée, Classer

---

## 8. Caméra — Photos et vidéos

KA intègre une caméra complète :

- **Mode** : Photo (prise unique)
- **Flash** et **selfie** non encore supportés
- **Galerie** : Les 12 dernières photos sont conservées dans le stockage local
- **Compression** : Les photos sont automatiquement compressées via HCV2 (perte minimale)

**Utilisation :**
1. Appuyez sur « Ouvrir la caméra »
2. Cadrez et appuyez sur le bouton blanc
3. La photo apparaît dans la galerie
4. Tap long sur une photo → suppression

---

## 9. Appel — Interface téléphonique

KA propose une interface d'appel élégante :

- **Avatar** — Initiale du contact avec halo pulsé
- **Timer** — Compteur d'appel (format MM:SS)
- **Visualisation d'ondes** — 22 barres animées représentant l'audio
- **Contrôles** : Sourdine, Haut-parleur, Clavier
- **Raccrocher** — Bouton rouge ✕

> 💡 L'écran Appel est accessible depuis l'écran **Relation** (bouton « Appeler »).

---

## 10. Fonctionnement technique

### Architecture

```
┌─────────────────────────────────────────────┐
│                 KA Mobile                    │
│  ┌───────────────────────────────────────┐  │
│  │         React 18 + TypeScript         │  │
│  │         Vite 5 · Tailwind 3           │  │
│  ├──────────┬──────────┬────────────────┤  │
│  │  KA Hybrid│ Harmonic │   HCV2 Codec  │  │
│  │  (local)  │  v3 (IA) │   (WASM)      │  │
│  ├──────────┴──────────┴────────────────┤  │
│  │          Capacitor 7.6.8             │  │
│  │  (Android · notifications · BLE ·    │  │
│  │   actions natives · compression ZIP) │  │
│  └───────────────────────────────────────┘  │
│           │                           │
│     ┌─────┘                           └─────┐
│     ▼                                       ▼
│  Serveur API (port 8765)          Appareil Android
│  /api/chat · /api/hcv2            Caméra · Micro · Stockage
└─────────────────────────────────────────────┘
```

### Intelligence artificielle

| Moteur | Technologie | Réponse | Usage |
|--------|-------------|---------|-------|
| **KA Hybrid** | FNV-1a hashing + Kuramoto résonance | 0,03 ms | Identité, FAQ, pathologies, urgences |
| **Harmonic v3** | PhaseEncoder `s_n = exp(i·α·n)` | O(1) | Calculs arithmétiques par synchronisation |
| **Serveur** | API REST | 5 s max | Réponses enrichies (si connecté) |

### Compression HCV2

| Format | Type | Ratio | Qualité |
|--------|------|-------|---------|
| HCVH | Hybride | ~50× | Élevée |
| HCVM | Modal | ~80× | Très élevée |
| HHD2 | Dictionnaire | ~213× | Bit-exact (8/8) |
| HHDC | Full | ~200× | Ajustable |

### Technologies utilisées

- **Frontend** : React 18.3.1 · TypeScript · Vite 5.4.21 · Tailwind 3.4.4 · React Router 6.26
- **Mobile** : Capacitor 7.6.8 (13 plugins)
- **IA locale** : KA Hybrid (40 KB) · Harmonic v3 (9 KB) — zéro dépendance externe
- **Compression** : HCV2 (WASM — décodeur 47 KB, encodeur 58 KB)
- **API** : Proxy `/api` → `localhost:8765`
- **Synthèse vocale** : Web Speech API + serveur Piper optionnel
- **Bluetooth** : BLE pour capteurs de santé (compatible Capacitor 7)

---

## 11. Foire aux questions

### ❓ KA a-t-elle besoin d'Internet ?

**Non.** Le cœur de KA (questions, identité, pathologies, concepts, FAQ, calculs) fonctionne **100% hors-ligne**. Seules les fonctionnalités avancées (réponses serveur enrichies, compression HCV2 serveur, synthèse vocale Piper) nécessitent une connexion.

### ❓ Mes données sont-elles envoyées quelque part ?

**Non.** Tout le traitement local reste sur votre appareil. L'historique des messages est stocké dans le stockage local de votre navigateur/téléphone et n'est jamais transmis sans votre consentement.

### ❓ Comment réinitialiser KA ?

Effacez les données de l'application dans les paramètres Android (Paramètres → Applications → KA → Stockage → Effacer données). Au prochain lancement, l'onboarding réapparaîtra.

### ❓ La caméra PPG est-elle médicale ?

**Non.** La mesure de fréquence cardiaque par caméra est une **simulation** et ne doit pas être utilisée à des fins médicales. Consultez toujours un professionnel de santé.

### ❓ Puis-je ajouter mes propres connaissances ?

Oui ! Dans l'écran **Hologrammes**, utilisez le champ « Vos centres d'intérêt » pour créer un hologramme personnalisé sur un sujet de votre choix.

### ❓ KA est-elle disponible sur iOS ?

Actuellement, KA est développée pour **Android** via Capacitor. Une version iOS pourrait être envisagée ultérieurement.

### ❓ Comment signaler un bug ou proposer une amélioration ?

Contactez l'équipe Univers-Holistique via les canaux habituels ou ouvrez une issue sur le dépôt du projet.

---

© 2026 Univers-Holistique — KA Mobile. Construit avec la Théorie Harmonique Universelle.