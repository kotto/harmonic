# Vital Ka — Version Android (APK)

Ce dossier contient le **wrapper natif Android** de l'application web Vital Ka,
construit avec **Capacitor 7**. L'app web existante (HTML/JS/CSS dans `engine/`)
est empaquetée telle quelle dans une WebView, avec deux ponts natifs :

- **TTS** : voix système Android (`speechSynthesis` → moteur TTS du téléphone)
- **STT** : reconnaissance vocale native via le plugin
  `@capacitor-community/speech-recognition` (Google SpeechRecognizer, fr-FR)

L'app web **n'est pas dupliquée** : une seule base de code dans `engine/`, et le
script `sync-assets.mjs` copie les fichiers nécessaires dans `www/` à chaque
reconstruction. Le code JS détecte `window.Capacitor` à l'exécution et bascule
en « mode natif » sans toucher au comportement PC/PWA.

---

## 1. Pré-requis

| Outil | Version testée | Rôle |
|---|---|---|
| Node.js | 22.x | Exécute le sync + la CLI Capacitor |
| Java JDK | **21** (Temurin / OpenJDK 21) | Build Gradle Android |
| Android SDK | Platform 35, Build-tools 35.0.0 | Compilation APK |
| Python | 3.x | (optionnel) uniquement pour la version PC/Piper |

> ⚠️ **JDK 21 obligatoire pour `JAVA_HOME`.** Capacitor 7 compile avec le niveau
> de source Java 21 ; un JDK 17 (par défaut sous Android Studio) provoque
> `error: invalid source release: 21`. Avant de builder, vérifier :
> ```bash
> "$JAVA_HOME/bin/javac" -version   # doit afficher 21.x
> ```
> Si besoin, redéfinir pour la session :
> ```bash
> export JAVA_HOME="/c/.../chemin/vers/jdk-21"
> ```

Vérifier le SDK :
```bash
echo $ANDROID_HOME          # doit pointer vers E:\Android\Sdk (ou équiv.)
ls $ANDROID_HOME/platforms  # doit contenir android-35
```

Si `android-35` manque :
```bash
yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager \
  "platforms;android-35" "build-tools;35.0.0"
```

`android/local.properties` contient `sdk.dir=E:\\Android\\Sdk` (à adapter si
votre SDK est ailleurs). **Ne pas committer ce fichier** (déjà dans `.gitignore`).

---

## 2. Reconstruire l'APK après une modif JS/HTML/CSS

Toute modification se fait **dans `engine/`** (la source), pas dans `www/`.
Ensuite :

```bash
cd vital-ka-android
npm run apk        # = sync assets + cap sync + gradlew assembleDebug
```

Étapes détaillées (équivalent manuel) :

```bash
# 1. Recopier les assets web mis à jour vers www/
npm run assets

# 2. Synchroniser Capacitor (copie www/ + plugins vers android/)
npx cap sync android

# 3. Compiler l'APK debug
cd android && ./gradlew assembleDebug
```

L'APK est produit dans :
```
android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 3. Installer sur un téléphone

### Option A — câble USB (recommandé)

1. Activer le **Mode développeur** sur le téléphone
   (Paramètres → À propos → taper 7× sur « Numéro de build »).
2. Activer le **Débogage USB** dans Options développeur.
3. Brancher le téléphone, accepter la boîte « Autoriser le débogage USB ».
4. Vérifier la détection :
   ```bash
   $ANDROID_HOME/platform-tools/adb devices
   # doit lister un appareil (pas "unauthorized")
   ```
5. Installer :
   ```bash
   $ANDROID_HOME/platform-tools/adb install -r \
     android/app/build/outputs/apk/debug/app-debug.apk
   ```

### Option B — copie manuelle du fichier

Copier `app-debug.apk` sur le téléphone (USB, Drive, etc.), puis l'ouvrir depuis
le gestionnaire de fichiers. Il faut autoriser « **Installer des applications
de sources inconnues** » pour le gestionnaire de fichiers.

---

## 4. Différences PC ↔ Android

| Fonctionnalité | PC (PWA + serveurs Python) | Android (APK natif) |
|---|---|---|
| **Voix (TTS)** | Piper neuronal offline (6 voix FR, serveur `:8420`) | Voix système Android (moteur TTS Google) |
| **Reconnaissance vocale (STT)** | Web Speech API (Chrome) | Plugin natif SpeechRecognizer (Google) |
| **Sélecteur de voix Piper** | Actif (6 voix) | Désactivé — voix = système Android |
| **Badge serveur vocal** | « Voix neurale » / « Voix navigateur » | « Voix native » |
| **Données (41 pathologies, 89 plantes…)** | Chargées via serveur `:8765` | Embarquées dans l'APK (offline) |
| **Bridge médecin↔patient** | Réseau WiFi + copier-coller QR | Copier-coller (pas de serveur local) |
| **Téléconsultation WebRTC** | Réseau local | Possible (permissions CAMÉRA + MICRO) |

### Préparation du téléphone pour une voix/STT français

1. **TTS français** : Paramètres → Langue & saisie → Synthèse vocale →
   installer une voix française (Google fait l'offre par défaut).
2. **STT hors-ligne** : Paramètres → Langue & saisie → Reconnaissance vocale
   Google → Pack de reconnaissance *français (France)* à télécharger
   (sinon le STT nécessite Internet).

---

## 5. Signature pour le Play Store (release)

L'APK debug **ne peut pas être publié** sur le Play Store. Procédure de
signature :

```bash
# 1. Générer un keystore (UNE FOIS — garder ce fichier en lieu sûr !)
keytool -genkey -v -keystore vitalka.keystore \
  -alias vitalka -keyalg RSA -keysize 2048 -validity 10000

# 2. Configurer android/app/build.gradle : décommenter/compléter le bloc
#    signingConfigs.release + référencer-le dans buildTypes.release.

# 3. Build release (demandera le mot de passe du keystore)
cd android && ./gradlew assembleRelease

# 4. APK signé :
#    android/app/build/outputs/apk/release/app-release.apk
```

Voir la doc officielle :
https://developer.android.com/build/building-cmdline#sign_cmdline

---

## 6. Structure du dossier

```
vital-ka-android/
├── package.json              # dépendances Capacitor + scripts npm
├── capacitor.config.json     # appId com.vitalka.app, webDir www
├── scripts/
│   └── sync-assets.mjs       # engine/*.html|js|css|json → www/ (+ fonts offline)
├── assets_src/fonts/         # fonts Google téléchargées une fois (woff2)
├── www/                      # [généré] assets web copiés pour Capacitor
└── android/                  # [généré] projet natif Android (Gradle)
    ├── local.properties      # sdk.dir (NE PAS COMMITTER)
    ├── variables.gradle      # versions SDK (35 par défaut)
    ├── app/src/main/
    │   ├── AndroidManifest.xml   # permissions : INTERNET, RECORD_AUDIO,
    │   │                          CAMERA, MODIFY_AUDIO_SETTINGS, cleartext
    │   ├── assets/public/         # copie de www/ (généré par cap sync)
    │   ├── java/com/vitalka/app/MainActivity.java
    │   │                          # enregistre le plugin SpeechRecognition
    │   └── res/                   # icônes, splash, strings
    └── build.gradle / settings.gradle
```

---

## 7. Dépannage

| Symptôme | Cause / solution |
|---|---|
| `SDK location not found` | Créer/éditer `android/local.properties` avec `sdk.dir=...` |
| `Failed to install the following Android SDK components...` | Lancer `sdkmanager "platforms;android-35" "build-tools;35.0.0"` |
| `error: invalid source release: 21` | `JAVA_HOME` pointe vers un JDK < 21. Le redéfinir vers un JDK 21 (`export JAVA_HOME=...`) |
| Build très long au 1er coup | Normal : télécharge Gradle 8.11 + toutes les dépendances AndroidX (~4–5 min) |
| `app-debug.apk` non produit | Voir la sortie Gradle, souvent un JDK absent ou < 21 |
| STT silencieux sur le téléphone | Vérifier la permission micro (demandée au 1er usage) + qu'une langue de reconnaissance FR est disponible |
| Voix robotique / absente | Installer/activer une voix TTS française dans les paramètres Android |
| Icône = logo Capacitor par défaut | Icônes Vital Ka non générées en v1 ; voir §8 |

---

## 8. (À faire) Icônes et splash Vital Ka

En v1, l'APK utilise l'icône Capacitor par défaut. Pour générer les icônes
depuis `engine/logo2.jpg` (nécessite `sharp`, installé via `@capacitor/assets`) :

```bash
cd vital-ka-android
# 1. Convertir logo2.jpg en vraies PNG sources (1024x1024 min)
#    via GIMP/Photoshop/ImageMagick :
#    convert ../logo2.jpg -resize 1024x1024 assets/icon.png
#    convert ../logo2.jpg -resize 2732x2732 assets/splash.png
# 2. Générer toutes les densités Android
npx @capacitor/assets generate --android
```

---

## 9. Limites connues (v1)

- **Voix ≠ Piper** : sur Android, on utilise le TTS système. Qualité bonne
  mais différente des voix neuronales Piper du PC. Le sélecteur de voix Piper
  reste actif uniquement sur la version PC/web.
- **STT nécessite les Services Google Play** (standard sur tous les téléphones
  Play Store). Pour un appareil sans GMS (Huawei, AOSP pur), il faudrait un
  moteur de reconnaissance alternatif (Vosk, Whisper.cpp) — non inclus en v1.
- **Pas de scan QR caméra** : le transfert médecin↔patient se fait par
  copier-coller du code (comme la PWA actuelle).
- **APK debug** : non signé pour le Play Store (procédure §5).
