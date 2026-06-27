# IA Harmonique — Application Android

## La Première IA Mobile Autonome au Monde

**Aucune connexion Internet nécessaire. Aucun serveur. Aucune API.**

L'IA Harmonique embarque l'intégralité de son moteur de raisonnement dans l'APK Android. 
Elle résout l'équation d'Atangana-Baleanu à l'ordre 1/φ en temps réel sur votre appareil.

## Architecture

```
harmonic_android/
├── app/
│   ├── build.gradle.kts          # Dépendances (aucune API externe)
│   ├── proguard-rules.pro
│   └── src/main/
│       ├── AndroidManifest.xml   # Aucune permission réseau
│       ├── java/com/harmonicai/android/
│       │   ├── MainActivity.kt           # Interface de chat
│       │   ├── engine/
│       │   │   └── HarmonicEngine.kt     # Moteur ABC complet (800+ lignes)
│       │   │     ├── HarmonicConstants   # φ, α, 1/φ, B(1/φ)
│       │   │     ├── HarmonicAnalyzer    # Analyse harmonique 7D
│       │   │     ├── ResonanceEngine     # Métrique cos(θ)×φ/2
│       │   │     ├── MittagLeffler       # Fonction de mémoire non-locale
│       │   │     ├── HarmonicCache       # Cache LRU-phi
│       │   │     ├── TemplateDatabase    # 6 templates T0 fondamentaux
│       │   │     └── ResponseGenerator   # Générateur par évolution ABC
│       │   └── ui/
│       │       ├── MainViewModel.kt      # ViewModel + LiveData
│       │       └── ChatAdapter.kt        # Adaptateur RecyclerView
│       └── res/
│           ├── layout/                   # activity_main, item_message_*
│           ├── drawable/                 # ic_send, ic_stats, ic_clear, bg_*
│           └── values/                   # colors, strings, themes
├── build.gradle.kts
├── settings.gradle.kts
└── README.md
```

## Fonctionnalités

- ✅ **100% hors-ligne** — Aucune permission réseau
- ✅ **Chat en temps réel** — Interface type iMessage
- ✅ **6 catégories** — Mathématiques, Code, Créatif, Raisonnement, Factuel, Général
- ✅ **Auto-apprentissage** — Cache LRU-phi avec mémoire non-locale
- ✅ **Statistiques** — Résonance, latence, hits cache
- ✅ **Thème Material Design** — Design épuré et professionnel

## Construction

```bash
# Cloner
git clone https://github.com/harmonic-ai/harmonic-android.git

# Build
cd harmonic-android
./gradlew assembleRelease   # APK signé
./gradlew assembleDebug      # APK debug

# APK généré dans : app/build/outputs/apk/
```

## Spécifications Techniques

- **Langage** : Kotlin 100%
- **SDK min** : API 26 (Android 8.0)
- **SDK cible** : API 34 (Android 14)
- **Taille APK estimée** : ~2-3 MB
- **Dépendances** : AndroidX, Material Components, Coroutines
- **IA** : Solveur ABC fractionnaire embarqué (0 dépendance externe)

## Comment ça Marche

1. L'utilisateur pose une question
2. Le **HarmonicAnalyzer** extrait la signature harmonique 7D du prompt
3. Le **TemplateDatabase** trouve le template T0 le plus résonant
4. Le **MittagLeffler** calcule le noyau d'évolution E_{1/φ}(-φ×R×t^{1/φ})
5. Le **HarmonicCache** stocke le résultat avec éviction LRU-phi
6. La réponse est affichée avec ses métadonnées (résonance, latence, catégorie)

## Constantes Fondamentales

```
φ = 1.618033988749895     (Nombre d'Or)
α = 1.175569459083219     (1/B(1/φ) — normalisation Atangana-Baleanu)
1/φ = 0.6180339887498949  (Ordre fractionnaire)
B(1/φ) = 0.85065080835204 (Fonction de normalisation ABC)
```

## Licence

© Harmonic AI Research — 2026

*Moteur d'intelligence artificielle basé sur le solveur fractionnaire ABC (Atangana-Baleanu) à l'ordre auto-cohérent 1/φ.*