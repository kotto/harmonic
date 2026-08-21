# 🎓 EDU-KA Mobile (Android)

Application mobile du projet **EDUCAL KA** — éducation numérique harmonique.
Jumeau pédagogique de `ka-mobile-android` (Vital KA / KA) : même shell Capacitor,
même écran de connexion, mais l'app consomme les routes éducatives du moteur.

## Consommation (routes du moteur KA — port 8765)

| Écran | Route |
|---|---|
| Catalogue des unités | `GET /api/educal/units` |
| Leçon complète | `GET /api/educal/unit/<unit_id>` |
| Quiz + correction + diagnostic | `POST /api/educal/quiz/submit` |
| Carnet d'apprentissage | `GET /api/educal/progress/<user_id>` |
| Tuteur de maths (déterministe) | `POST /api/educal/exercise/generate` |
| **Transfert d'unité** (comme une unité médicale) | `POST /api/educal/unit/<id>/hologram` → `GET /api/store/download/<holo>` → `POST /api/store/load` |

## Structure

```
educal-mobile-android/
├── capacitor.config.json   # appId com.educalka.app, appName EDU-KA
├── www/
│   ├── index.html          # écran de connexion (généré)
│   └── educal_index.html   # l'application (catalogue, leçon, quiz, progression, tuteur)
└── scripts/
    ├── sync-assets.mjs     # génère www/ (connexion + manifest)
    └── build-apk.mjs       # sync-assets → cap → gradlew
```

## Build

```bash
npm install
node scripts/build-apk.mjs        # génère android/ + APK debug
# ou manuellement :
npx cap add android && npx cap sync android
cd android && gradlew assembleDebug
```

## Prérequis serveur

- `ka_server.py` (port 8765) avec le domaine `education` construit :
  `python educal_build_holograms.py`
- Les 6 unités d'exemple dans `data/educal_units/` (déjà fournies)

## Transfert d'unité (le geste clé)

Depuis la leçon, bouton **« 📦 Transférer l'unité »** :
1. Construit l'hologramme `unit_<id>.npz` (faits + ψ) côté serveur
2. Télécharge les faits + mémoire holographique (format polaire)
3. Injecte H dans le cerveau actif (`brain.store(H, amplitude=2.0)`)

→ L'unité devient interrogable en langage naturel sur l'appareil cible,
exactement comme les unités médicales de Vital KA.
