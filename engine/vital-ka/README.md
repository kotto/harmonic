# Vital KA — Écosystème Médical Harmonique v2.1.0

> **Application mobile offline-first** pour le diagnostic médical assisté par IA, la télémédecine et la gestion de santé communautaire. Basée sur la **Théorie Harmonique** (onde C⁵¹², résonance spectrale, compression HCV).

---

## 📦 Structure du Projet

```
vital-ka/
├── apps/              # 10 applications HTML (web, patient, médecins, pharmacien, labo, diaspora, admin, launcher, solidarité, sphère)
├── android/           # Projet Capacitor 7 (com.vitalka.app, minSdk 24, targetSdk 35, JDK 21)
├── backend/           # 9 serveurs Python par domaine (voice, phone, hologram, enterprise, hwat, training, inference, sonic, serve)
├── core/
│   ├── js/            # 30 modules ES6 vanilla (source de vérité pour l'app mobile)
│   └── python/        # 180+ modules Python (harmonic AI, wave compiler, knowledge bases, training)
├── data/              # Données embarquées (hologram_bundle.json 3.8 Mo + 13 domaines médicaux + 13 bases pathologiques)
├── docs/              # Documentation complète (50+ .md + pitches HTML + architecture Mermaid)
└── archive/           # Anciens fichiers de test et animations
```

---

## 🚀 Démarrage Rapide — Application Mobile (Android)

### Prérequis
- **Node.js** ≥ 18
- **JDK 21** (requis pour Capacitor 7 / Gradle 8.11)
- **Android SDK** (API 35) + Build Tools
- **Gradle** 8.11+ (inclus via wrapper)

### Build Complet

```bash
cd vital-ka/android

# 1. Installer les dépendances Node (premier build uniquement)
npm install

# 2. Synchroniser les assets web → www/ (copie core/js, data, fonts, HTML)
node scripts/sync-assets.mjs

# 3. Copier www/ vers le projet Android (Capacitor)
npx cap copy

# 4. Build APK debug
./android/gradlew assembleDebug

# 5. APK généré : android/app/build/outputs/apk/debug/app-debug.apk (~6.14 Mo)
```

### Lancer sur émulateur / device

```bash
# Option A : Via Capacitor (lance l'émulateur si nécessaire)
npx cap run android

# Option B : Directement avec adb
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n com.vitalka.app/.MainActivity
```

---

## 🌐 Applications Web (10 apps — dossier `apps/`)

| App | Fichier | Description |
|-----|---------|-------------|
| **Vital Ka** | `web/vital_ka.html` | App principale — Diagnostic IA + Télémédecine + Wallet |
| **Patient** | `patient/ka_patient.html` | Dossier patient, QR partage, histórico, rappels |
| **Médecins** | `medecins/ka_medecins.html` | Portail médecins — Ordonnances, labo, téléconsultation |
| **Pharmacien** | `pharmacien/ka_pharmacien.html` | Scan QR ordonnance, interactions, substitution |
| **Laboratoire** | `labo/ka_laboratoire.html` | Résultats auto-envoyés patient/médecin |
| **Diaspora Shop** | `diaspora/ka_diaspora_shop.html` | E-commerce multi-devises (MoMo, carte, AML) |
| **Admin** | `admin/ka_admin.html` | Administration système |
| **Launcher** | `launcher/ka_launcher.html` | Raccourcis / point d'entrée |
| **Solidarité** | `solidarite/ka_solidarite.html` | Santé communautaire, alertes |
| **Sphère 3D** | `sphere/ka_sphere.html` | Visualisation 3D harmonique |

> **Note** : Les apps web utilisent les modules `core/js/` directement. Pour tester : servir `apps/web/` avec un serveur local (`npx serve` ou `python -m http.server`).

---

## 🧠 Core JavaScript — 30 Modules (`core/js/`)

| Module | Rôle |
|--------|------|
| `vital_ka_config.js` | Configuration centralisée (API, features, mode natif) |
| `vital_ka_native.js` | Adaptateur Capacitor ↔ STT/TTS natif |
| `vital_ka_hologram.js` | Encodeur C⁵¹² — résonance spectrale |
| `vital_ka_knowledge.js` | Phytothérapie + base de connaissance résonance |
| `vital_ka_voice.js` | TTS Tiered : Edge (cloud) → Piper (local) → Web Speech API |
| `vital_ka_stt.js` | STT hybride : Web Speech API + plugin natif Android |
| `vital_ka_dialogue.js` | Orchestration conversation multi-tours |
| `vital_ka_conversation.js` | Mémoire contextuelle + résumé |
| `vital_ka_ble.js` | BLE vitals (SpO₂, TA, température) |
| `vital_ka_ai.js` | KACareAI local (TF.js) + fallback hybride backend |
| `vital_ka_app.js` | Logique métier principale (diagnostic, routing) |
| `ka_core.js` | Moteur diagnostic — 41 pathologies, scoring pondéré |
| `ka_secure.js` | AES-GCM 256 + PIN SHA-256 + stockage chiffré |
| `ka_bridge.js` | Transfert sécurisé Patient ↔ Médecin ↔ Labo |
| `ka_hcv.js` | Compression Delta-H (harmonique) |
| `ka_hologram_router.js` | Routeur spectral — 15 domaines / 62K faits |
| `ka_network.js` | Détection réseau + P2P WebRTC |
| `ka_platform.js` | Abstraction Capacitor (FS, Share, Haptics, etc.) |
| `ka_telemedecine.js` | WebRTC + HCV temps réel (audio/video compressé) |
| `ka_wallet.js` | Portefeuille UM multi-devises (XOF, EUR, USD, BTC) |
| `ka_care_voice.js` | Voix médicale spécialisée |
| `seed_doctors_demo.js` | Données démo médecins |

---

## 🐍 Backends Python (`backend/`)

Chaque backend est un serveur indépendant (port par défaut) :

| Backend | Port | Description |
|---------|------|-------------|
| **voice** | 8420 | Piper TTS haute qualité (phi_piper_engine, phi_vocoder) |
| **phone** | 8421 | Unified Server — IA voix harmonique (XTTS, speech orchestrator) |
| **hologram** | — | Routeur Python, builder bundle, connector |
| **enterprise** | — | Core entreprise, extensions, server |
| **hwat** | — | HWAT (Harmonic Wave Audio Transform) |
| **training** | — | Scripts d'entraînement modèles harmoniques |
| **inference** | 8010 | Serveur d'inférence hologrammes / Ka Server |
| **sonic** | — | Ka Sonic — audio processing |
| **serve** | — | Serveur générique Ka |

### Lancer un backend

```bash
# Exemple : Backend Voice (Piper TTS)
cd vital-ka/backend/voice
python ka_voice_server.py  # → http://localhost:8420

# Exemple : Backend Phone (IA voix complète)
cd vital-ka/backend/phone
python unified_server.py   # → http://localhost:8421

# Exemple : Serveur d'inférence hologrammes
cd vital-ka/backend/inference
python inference_server.py # → http://localhost:8010
```

> Les backends sont **optionnels** : l'app mobile fonctionne 100% offline avec les modèles locaux (TF.js, Web Speech API). Les backends apportent : TTS Piper qualité studio, IA voix avancée, inférence lourde.

---

## 📊 Données Embarquées (`data/`)

| Fichier | Taille | Contenu |
|---------|--------|---------|
| `hologram_bundle.json` | 3.8 Mo | 15 domaines médicaux, 62K faits, scores normalisés 0-1 |
| `enrichissements.json` | 98 Ko | Enrichissements transversaux |
| `medical_holograms/` | ~80 Mo | 13 domaines (.pt tenseurs + _facts.json) + `router.json` |
| `vital_ka_*.json` (13) | ~200 Ko | Bases pathologiques spécialisées |
| `vital_ka_features.json` | 2 Ko | Features du moteur diagnostic |

### Domaines Médicaux (13 + router)

```
CHRONIQUES, CLINIQUE, GENERAL, MALADIES, MERE_ENFANT,
MNT, NUTRITION, PALUDISME, PEDIATRIE, PHARMACIE,
PHYTOTHERAPIE, SANTE_MENTALE, URGENCES, VACCINATION, VIH_TB
```

Chaque domaine = fichier `.pt` (tenseurs PyTorch) + `_facts.json` (faits structurés).

---

## 📱 Configuration Android (`android/`)

### `capacitor.config.json`
```json
{
  "appId": "com.vitalka.app",
  "appName": "Vital Ka",
  "webDir": "www",
  "server": { "androidScheme": "https" },
  "android": {
    "buildOptions": { "keystorePath": "release.keystore" },
    "minSdkVersion": 24,
    "targetSdkVersion": 35,
    "compileSdkVersion": 35
  },
  "plugins": {
    "SpeechRecognition": { "locale": "fr-FR" },
    "TextToSpeech": { "locale": "fr-FR" },
    "BluetoothLe": {},
    "LocalNotifications": {}
  }
}
```

### `android/app/build.gradle` (extrait)
```gradle
android {
    namespace 'com.vitalka.app'
    compileSdk 35
    defaultConfig {
        applicationId "com.vitalka.app"
        minSdk 24
        targetSdk 35
        versionCode 210
        versionName "2.1.0"
    }
}
```

### Permissions Android (AndroidManifest.xml)
- `INTERNET`, `ACCESS_NETWORK_STATE` (WebRTC, sync)
- `BLUETOOTH`, `BLUETOOTH_ADMIN`, `BLUETOOTH_CONNECT`, `BLUETOOTH_SCAN` (vitals BLE)
- `RECORD_AUDIO` (STT)
- `CAMERA` (scan QR ordonnance)
- `NFC` (partage dossier patient)
- `VIBRATE` (haptics)
- `FOREGROUND_SERVICE` (télémédecine background)

---

## 🏗️ Architecture — Flux de Données

```
┌─────────────┐     sync-assets.mjs      ┌─────────────┐
│  core/js/   │ ──────────────────────▶  │   www/      │
│  (30 mods)  │                          │  (Capacitor)│
└─────────────┘                          └──────┬──────┘
                                                 │
                        ┌────────────────────────┘
                        ▼
                 ┌─────────────┐     gradlew      ┌─────────────┐
                 │  android/   │ ──────────────▶  │  app-debug  │
                 │  (Gradle)   │                  │   .apk      │
                 └─────────────┘                  │  (6.14 Mo)  │
                                                 └─────────────┘
```

### Mode Offline-First
1. **Tout embarqué** : `hologram_bundle.json` + 13 JSON pathologiques + 30 modules JS dans l'APK
2. **Pas de CDN** : Fonts Inter + Material Symbols en local (`www/fonts/`)
3. **STT/TTS hybride** : Web Speech API (offline Chrome) + plugin natif Android
4. **Sync différée** : Données médecin/patient/labo stockées localement, sync quand réseau dispo

---

## 📚 Documentation (`docs/`)

### Fichiers Clés
| Fichier | Description |
|---------|-------------|
| `README.md` | Ce fichier |
| `ROADMAP.md` | Feuille de route |
| `DEPLOY.md` / `GUIDE_DEPLOIEMENT.md` | Déploiement production |
| `IMPLEMENTATION_STATUS.md` | Statut d'implémentation |
| `PHASE3_INTEGRATION_GUIDE.md` | Intégration Phase 3 |
| `CAHIER_DES_CHARGES_PROJET_COMPLET.md` | Spécifications complètes |
| `HARMONIC_THEORY.md` | Théorie harmonique (onde C⁵¹²) |
| `LIVRE_COMPLET.md` | Livre complet théorie + pratique |

### Architecture Diagrams (`docs/architecture/`)
- `architecture.mmd` — Architecture globale (Mermaid flowchart)
- `file-tree.mmd` — Structure de fichiers complète (ce diagramme)

### Pitches (`docs/pitches/`)
- `business_plan_vital_ka.html` — Business plan
- `cahier_des_charges.html` — Cahier des charges visuel
- `dossier_donateurs_ka_care.html` — Dossier donateurs
- `index.html` — Page d'accueil pitches

---

## 🔧 Développement — Workflow Recommandé

### Modifier le Core JS
```bash
# 1. Éditer les modules dans core/js/
vim core/js/vital_ka_app.js

# 2. Synchroniser vers Android
cd android
node scripts/sync-assets.mjs
npx cap copy

# 3. Rebuild APK
./android/gradlew assembleDebug
```

### Ajouter un Domaine Médical
```bash
# 1. Ajouter fichiers dans data/medical_holograms/
# 2. Régénérer le bundle
cd backend/hologram
python build_hologram_bundle.py

# 3. Sync + rebuild Android
cd ../../android
node scripts/sync-assets.mjs
npx cap copy
./android/gradlew assembleDebug
```

### Test Rapide Web (sans Android)
```bash
cd apps/web
npx serve .  # ou python -m http.server 8080
# Ouvrir http://localhost:3000/vital_ka.html
```

---

## 🧪 Tests

### Tests Unitaires Core JS
```bash
# Navigateur : ouvrir apps/web/vital_ka.html ?test=1
# Ou via Node (si tests configurés)
cd core/js
node --test vital_ka_ai.test.js  # (à créer)
```

### Tests Backend Python
```bash
# Backend hologram
cd backend/hologram
python -m pytest test_hologram_router.py -v

# Backend voice
cd backend/voice
python -m pytest test_tts.py -v

# Benchmarks harmoniques
cd core/python
python benchmark_systematic.py
python benchmark_lm_arena_500.py
```

---

## 📦 Release — APK Production

```bash
cd vital-ka/android

# 1. Sync assets
node scripts/sync-assets.mjs
npx cap copy

# 2. Build Release (nécessite keystore configuré)
./android/gradlew assembleRelease

# 3. APK signé : android/app/build/outputs/apk/release/app-release.apk
# 4. Ou Bundle : ./android/gradlew bundleRelease → .aab pour Play Store
```

### Versioning
- `versionCode` : 210 (2.1.0 → 210)
- `versionName` : "2.1.0"
- Incrémenter dans `android/app/build.gradle` + `capacitor.config.json`

---

## 🔐 Sécurité & Confidentialité

- **Chiffrement local** : AES-GCM 256 bits (Web Crypto API) — clé dérivée PIN SHA-256 + salt
- **Pas de cloud obligatoire** : 100% fonctionnel offline
- **Sync chiffrée** : Protocole bridge Patient↔Médecin↔Labo (E2E)
- **Pas de tracking** : Aucun analytics, aucune télémétrie
- **Permissions minimales** : Juste ce qui est nécessaire (BLE, Camera, Micro, NFC)

---

## 🌍 Internationalisation

- **Langue par défaut** : Français (fr-FR)
- **Locales STT/TTS** : Configurable via `vital_ka_config.js`
- **Devises supportées** : XOF, EUR, USD, BTC, ETH (wallet)

---

## 📄 Licence

Projet privé — UNIVERS-HOLISTIQUE. Tous droits réservés.

---

## 🔗 Liens Utiles

- **Architecture** : `docs/architecture/architecture.mmd` (visualisable sur [Mermaid Live](https://mermaid.live))
- **Structure fichiers** : `docs/architecture/file-tree.mmd`
- **Guide Android** : `android/GUIDE_ANDROID.md`
- **Théorie Harmonique** : `docs/HARMONIC_THEORY.md`
- **Roadmap** : `docs/ROADMAP_HARMONIC_TRANSFORMER_VITAL_KA.md`

---

*Dernière mise à jour : 2026-08-02 — Vital KA v2.1.0*