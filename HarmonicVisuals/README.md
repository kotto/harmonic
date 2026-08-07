# 🎨 HarmonicVisuals — Générateur d'Images et Vidéos Harmonique

> **Génération visuelle basée sur l'architecture ondulatoire ψ. Deux modes : géométrique (interférence) et photoréaliste (dictionnaire de patches). 100% local, 0 GPU, 0€.**

---

## ⚡ Quick Start

```bash
# Installation
pip install numpy pillow scipy flask flask-cors

# Générer une image géométrique
python scripts/generate.py "sunset over mountains" --mode geometric --width 512

# Générer avec upscaling 4K + compression
python scripts/generate.py "forest in autumn" --mode hybrid --upscale 4 --compress

# Générer une vidéo
python scripts/generate.py "city lights" --video --duration 5 --fps 24

# Lancer l'API REST
python api/server.py --port 8800
```

---

## 🏗️ Architecture

```
Prompt → HarmonicEncoder → ψ ∈ ℂ⁵¹²
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       MODE A (Géométrique)           MODE B (Photoréaliste)
       ψ → IFFT 2D → patterns          ψ → HarmonicDatabase → patches réels
              │                               │
              └───────────────┬───────────────┘
                              ▼
                     PhiPostFilter (équilibrage φ)
                              │
                     PhiUpscaler (×2/×4 → 4K)
                              │
                     HCVCompressor (64:1 → ~200 Ko)
                              │
                     ImageHologramStore (ℂ⁵¹²)
```

---

## 📂 Structure du projet

```
HarmonicVisuals/
├── harmonic_visuals.py     ← Moteur principal
├── core/
│   ├── encoder.py           ← Texte → ψ
│   ├── generator_a.py       ← Mode A: IFFT 2D
│   ├── generator_b.py       ← Mode B: Dictionnaire
│   ├── dictionary.py        ← HarmonicDatabase
│   ├── upscaler.py          ← PhiUpscaler ×2/×4
│   ├── compressor.py        ← HCVCompressor 64:1
│   ├── postfilter.py        ← PhiPostFilter
│   └── hologram_store.py    ← Stockage holographique
├── video/
│   └── generator.py         ← Générateur vidéo + interpolation φ
├── api/
│   └── server.py            ← API REST (Flask)
├── scripts/
│   ├── generate.py          ← CLI
│   └── build_dict.py        ← Construction dictionnaire
└── data/                    ← Dictionnaires et sorties
```

---

## 📊 Modes de génération

| | Mode A (Géométrique) | Mode B (Photoréaliste) |
|---|---|---|
| **Source** | Mathématiques pures | Photos réelles |
| **Principe** | ψ → IFFT 2D → interférence | ψ → HarmonicDatabase → retrieval |
| **Données** | Aucune | Corpus d'images requis |
| **Rendu** | Géométrique, textures | Photoréaliste |
| **Vitesse** | ~50ms (512×512) | ~200ms (512×512) |

---

## 🔧 API REST

| Endpoint | Mode | Description |
|---|---|---|
| `POST /api/generate/geometric` | A | Image géométrique |
| `POST /api/generate/realistic` | B | Image photoréaliste |
| `POST /api/generate/hybrid` | A+B | Image hybride |
| `POST /api/generate/video` | A/B | Vidéo |
| `POST /api/pipeline` | A/B/H | Pipeline complet |
| `GET /api/stats` | — | Statistiques |

---

> **HarmonicVisuals** — L'esthétique ondulatoire rencontre le photoréalisme.
