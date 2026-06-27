# 🚀 PHASE 2: AUTOMATISATION PARTIELLE
## Objectif: Intégration OpenClaw + interception fichiers

---

## ✅ PHASE 2 CHECKLIST

| Étape | Description | État |
|---|---|---|
| 1 | Wrapper Python bibliothèque C | ☐ |
| 2 | Module OpenClaw interception fichiers | ☐ |
| 3 | Détection nouveaux fichiers en temps réel | ☐ |
| 4 | Scan automatique médiathèque | ☐ |
| 5 | Service background permanent | ☐ |
| 6 | Interface UI minimaliste | ☐ |
| 7 | Benchmarks batterie | ☐ |

---

## 📋 SPECIFICATIONS PHASE 2

### 🔴 1. Wrapper Python
- Chargement de la bibliothèque `.so` C via `ctypes`
- API Python avec seulement 3 fonctions:
  ```python
  hcv_init()
  hcv_decode(compressed_data, width, height) -> pixels
  hcv_encode(pixels, width, height) -> compressed_data
  ```

### 🔴 2. Interception OpenClaw
- Hook au niveau VFS (Virtual File System)
- Intercepte `open()`, `read()`
- Transparent pour toutes les applications
- Aucune modification système, aucun root nécessaire
- Décode à la volée quand une application demande un fichier HCV

### 🔴 3. Détection automatique
- Écoute `inotify` pour nouveaux fichiers dans DCIM/Camera
- Compression automatique 5s après la fin de l'écriture
- Garde original 30 jours puis suppression automatique

### 🔴 4. Service background
- Démarrage automatique au boot
- Priorité basse pour ne pas impacter les performances
- Wake lock optimisé
- Exécution seulement quand le téléphone est en charge et sur WiFi

### 🔴 5. Interface UI
- 1 seul écran
- 3 chiffres seulement:
  - 🟢 Espace libéré
  - 📊 Ratio moyen
  - ⚡ Fichiers optimisés
- Animations 60fps
- Aucun bouton technique
- Aucun paramètre

---

## ✅ CRITÈRES DE RÉUSSITE PHASE 2
✅ Aucun ralentissement système
✅ Aucune application ne voit la différence
✅ Toutes les applications continuent de fonctionner normalement
✅ Consommation batterie < 1% par 24h
✅ 10000 photos scannées en moins de 10 minutes
