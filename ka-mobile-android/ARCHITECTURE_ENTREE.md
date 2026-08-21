# 🏛️ ARCHITECTURE_ENTREE — L'ordre du projet KA Mobile v2 (Intent OS)

**Architecture hybride : React 18 + Vite + TypeScript + Tailwind CSS + Capacitor**
**Branche** : `memory-first-hybride`
**Mise à jour** : 12/08/2026

---

## 1. Architecture générale

```
ka-mobile-android/
│
├── src/                          # ★ NOUVELLE SOURCE (React + TypeScript)
│   ├── main.tsx                  # Entry point React
│   ├── App.tsx                   # Routeur + shell principal
│   ├── vite-env.d.ts
│   ├── styles/
│   │   └── globals.css           # Tailwind directives + design tokens
│   ├── components/
│   │   ├── ui/                   # Composants atomiques
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Pill.tsx
│   │   │   ├── Stat.tsx
│   │   │   └── Insight.tsx
│   │   ├── layout/
│   │   │   ├── DeviceFrame.tsx   # Cadre téléphone 375×812
│   │   │   ├── BottomNav.tsx     # Navigation 4 onglets
│   │   │   ├── SpaceHeader.tsx   # En-tête avec retour
│   │   │   └── MorePanel.tsx     # Panneau latéral
│   │   ├── keyboard/
│   │   │   └── ...               # Clavier AZERTY (intégré dans MessagesScreen)
│   │   └── chat/
│   │       └── ...               # Composants chat
│   ├── screens/                  # 1 composant = 1 espace
│   │   ├── HomeScreen.tsx        # Accueil
│   │   ├── MessagesScreen.tsx    # Chat + clavier
│   │   ├── CallScreen.tsx        # Appel
│   │   ├── MemoryScreen.tsx      # Mémoire
│   │   ├── PrepareScreen.tsx     # Préparation réunion
│   │   ├── JourneyScreen.tsx     # Voyage
│   │   ├── RelationScreen.tsx    # Relations
│   │   ├── CaptureScreen.tsx     # Capture d'idée
│   │   ├── DecideScreen.tsx      # Aide à la décision
│   │   ├── HealthScreen.tsx      # Santé (à migrer)
│   │   ├── StorageScreen.tsx     # Compression HCV (à migrer)
│   │   └── ...
│   ├── services/
│   │   ├── api.ts                # Client Axios + React Query
│   │   ├── hybrid.ts             # Wrapper ka_hybrid.js (TODO)
│   │   ├── native.ts             # Wrapper ka_native.js (TODO)
│   │   └── voice.ts              # Wrapper vital_ka_voice.js (TODO)
│   ├── hooks/
│   │   └── useApi.ts             # Hook statut serveur
│   └── types/
│       └── index.ts              # Types TypeScript
│
├── www/                          # ★ SOURCE DE VÉRITÉ (build Vite + legacy)
│   ├── index.html                # Généré par Vite (app React)
│   ├── ka_index.html             # Legacy vanilla JS (conservé)
│   ├── assets/                   # Bundles Vite
│   ├── ka_hybrid.js              # Legacy (inchangé)
│   ├── ka_native.js              # Legacy (inchangé)
│   ├── harmonic_v3.js            # Legacy (inchangé)
│   └── ...
│
├── index.html                    # ★ ENTRÉE Vite (src → www/)
├── vite.config.ts                # Configuration Vite
├── tsconfig.json                 # TypeScript config
├── tailwind.config.js            # Tailwind + tokens KA v2
├── postcss.config.js             # PostCSS
├── capacitor.config.json         # Capacitor (webDir = www)
├── android/                      # Projet Android natif (inchangé)
├── ios/                          # Projet iOS natif (inchangé)
├── ka-actions/                   # Plugin natif (inchangé)
└── package.json                  # Dépendances unifiées
```

## 2. La règle d'or — LA SOURCE DE VÉRITÉ

**On édite dans `src/`** (React + TypeScript).
**Le build Vite écrit dans `www/`** (le `webDir` de Capacitor).
**Les fichiers legacy dans `www/`** sont conservés pour la rétrocompatibilité.

| Fichier | Rôle | État |
|---------|------|------|
| `index.html` | Entry point Vite | ✅ Généré dans www/ |
| `ka_index.html` | Legacy vanilla (accès direct) | ✅ Conservé |
| `android/app/src/main/assets/public/` | Copie Android | ⚡ `npx cap sync` |
| `ios/App/App/public/` | Copie iOS | ⚡ `npx cap sync` |

## 3. Procédure de build

```bash
# Développement (HMR)
npm run dev

# Build production
npm run build

# Build + sync Capacitor
npm run sync:android
npm run sync:ios

# Build APK complet
npm run apk
```

## 4. Design System v2 (Intent OS)

### Tokens Tailwind

| Token | Hex | Usage |
|-------|-----|-------|
| `soul` | `#9b94ff` | Primaire, spiritualité |
| `soul-light` | `#c4bfff` | Texte soul clair |
| `life` | `#4de8ae` | Santé, appel, succès |
| `wisdom` | `#f5cc6a` | Voyage, sagesse |
| `rose` | `#f2a8c4` | Relations, amour |
| `sky` | `#96c8f5` | Décision, logique |
| `coral` | `#f07040` | Attention, alertes |
| `void` | `#0e0e1a` | Fond principal |

### Améliorations v1 → v2

| Élément | v1 | v2 |
|---------|----|----|
| Fond void | `#07070f` | `#0e0e1a` (+35% lum.) |
| Gradient | `#1e1630` | `#2a2048` (+25% lum.) |
| Verre (glass) | .04 opacity | .07 (×1.75) |
| Bordures | .06 | .10 (×1.67) |
| Soul | `#8b83ff` | `#9b94ff` (+8%) |
| Life | `#3ddba0` | `#4de8ae` (+10%) |

## 5. Routing

React Router 6 avec les routes suivantes :

| Path | Screen | Nav |
|------|--------|-----|
| `/` | HomeScreen | Accueil |
| `/messages` | MessagesScreen | Messages |
| `/call` | CallScreen | Cachée |
| `/memory` | MemoryScreen | Mémoire |
| `/prepare` | PrepareScreen | Plus |
| `/journey` | JourneyScreen | Plus |
| `/relation` | RelationScreen | Plus |
| `/capture` | CaptureScreen | Plus |
| `/decide` | DecideScreen | Plus |
| `/health` | HealthScreen | Plus (future) |
| `/storage` | StorageScreen | Plus (future) |

## 6. Migration progressive

Les écrans legacy dans `www/ka_index.html` continuent de fonctionner.
Les nouveaux écrans React remplacent progressivement les anciens.

**Modules JS legacy conservés** (encapsulés comme services) :
- `ka_hybrid.js` → `src/services/hybrid.ts`
- `ka_native.js` → `src/services/native.ts`
- `harmonic_v3.js` → `src/services/harmonic.ts`
- `ka_hcv.js` → `src/services/hcv.ts`
- `vital_ka_voice.js` → `src/services/voice.ts`

---

*Document d'ordre — FIN — La source est `src/`, le build va dans `www/`, Capacitor sync propage.*