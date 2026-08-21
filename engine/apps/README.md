# 🌊 HPU Applications — Applications finalisées

**8 applications prêtes au déploiement. Chacune dans son dossier avec documentation et démarrage automatisé.**

---

## Structure

```
apps/
├── theme.css              ← Thème harmonique partagé
├── README.md              ← Ce fichier
│
├── hpu-cloud/             ← ☁️ API de calcul harmonique
│   ├── README.md
│   └── start.bat
│
├── hcv-compression/       ← 🎵 Codec audio/vidéo
│   ├── README.md
│   └── start.bat
│
├── harmonic-ai/           ← 🧠 IA ondulatoire
│   ├── README.md
│   └── start.bat
│
├── ka-care/               ← 🏥 Médecine harmonique
│   ├── README.md
│   └── start.bat
│
├── harmofold/             ← 🔬 Repliement de protéines
│   ├── README.md
│   └── start.bat
│
├── periodic-table/        ← 📊 Tableau périodique THU
│   ├── README.md
│   └── start.bat
│
├── gsm8k/                 ← 🧮 Raisonnement mathématique
│   ├── README.md
│   └── start.bat
│
└── wave-voice/            ← 🎤 Synthèse vocale
    ├── README.md
    └── start.bat
```

## Thème

Toutes les applications partagent le **même thème harmonique** (`theme.css`) — style unique, identité visuelle cohérente. Couleur d'accent dorée (`#C9A84C`) pour toutes les applications.

## Démarrage

Chaque application a son propre `start.bat` avec menu interactif.

Pour lancer l'application principale :
```bash
cd engine/apps/hpu-cloud
start.bat
```

## Dépendances

Toutes les applications partagent le même runtime Python 3.11+ et les dépendances du dossier `engine/`.

## Statut global

```
✅ HPU Cloud      — Production
✅ HCV Compression — Production
✅ Harmonic AI     — Production
🔬 KA Care        — Beta
🔬 HarmoFold      — Preview
✅ Periodic Table — Production
✅ GSM8K          — Production
✅ Wave Voice     — Production
```