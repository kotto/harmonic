# 🌊 Écosystème Harmonic AI — Architecture des Projets

**Document d'architecture — 20 Juillet 2026**

---

## Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                   ╔═══════════════════════╗                       │
│                   ║   MOTEUR HARMONIQUE   ║                       │
│                   ║   (cœur commun)       ║                       │
│                   ║   generative_encoder  ║                       │
│                   ║   harmonic_ai_v2      ║                       │
│                   ║   wave_debugger       ║                       │
│                   ║   dictionnaire ondes  ║                       │
│                   ╚═══════════════════════╝                       │
│                      ↑              ↑              ↑              │
│                      │              │              │              │
│         ┌────────────┼──────────────┼──────────────┼────────┐    │
│         │            │              │              │        │    │
│         ▼            ▼              ▼              ▼        │    │
│                                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐       │
│  │    KA    │  │ KA ENTERPRISE│  │    HARMONIC AI       │       │
│  │  Phone   │  │     AI       │  │    (ULM public)      │       │
│  └──────────┘  └──────────────┘  └──────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. MOTEUR HARMONIQUE (cœur commun)

**Quoi :** La bibliothèque fondamentale. Tout le monde l'utilise, personne ne la modifie directement.

**Contenu :**
| Fichier | Rôle |
|---------|------|
| `generative_encoder.py` | Encodeur sémantique optimal (17 concepts fondamentaux, cross-lingual FR/EN) |
| `harmonic_ai_v2.py` | Core IA unifié : `debug()`, `chat()`, `learn()` |
| `wave_debugger_v2.py` | Moteur ABC hybride (analytique + correction transitoire) |
| `wave_debugger_v3.py` | Pipeline multi-passes + mémoire holographique |
| `wave_debugger_v6.py` | Encodeur holographique (SVD 110K + spectral) |
| `DICTIONNAIRE_ONDES_UNIVERS.md` | 200+ concepts traduits en langage des ondes |
| `METHODOLOGIE_RESOLUTION_ONDULATOIRE.md` | La méthode en 4 étapes |

**Où :** `engine/` dans le repo `harmonic` (branche `main`)

**Dépendances :** `numpy`, `scipy`

---

## 2. KA — Le Compagnon Personnel

```
┌──────────────────────────────────────────────────────────┐
│  CIBLE       : Grand public (tout utilisateur de phone)  │
│  INTERFACE   : PWA (mobile-first, installable)           │
│  DÉPLOIEMENT : On-device (tourne sur le téléphone)       │
│  DONNÉES     : Personnelles (restent sur l'appareil)     │
│  MONÉTISATION: Freemium (basique gratuit, pro payant)    │
└──────────────────────────────────────────────────────────┘
```

**Objectif :** Augmenter les performances d'un téléphone ordinaire au niveau d'un haut de gamme grâce à :
- **Compression massive** (HCV) — stocker 10× plus de photos/vidéos
- **IA personnelle KA** — apprend de l'utilisateur, l'assiste, devient son double numérique
- **Diagnostic automatique** — détecte les problèmes du téléphone (batterie, stockage, apps)

**Spécificités (≠ moteur commun) :**
| Module | Rôle |
|--------|------|
| `ka_phone_server.py` | Serveur local sur le téléphone |
| `hcv_service.py` | Compression HCV (images, vidéos) |
| `ka_light.py` | Mode hors-ligne, économie batterie |
| `phone_actions.py` | Actions natives (appels, SMS, photos) |
| `user_memory.py` | Mémoire personnelle de l'utilisateur |
| `tts_streaming.py` | Synthèse vocale |
| `www/` | Interface PWA (React-like, mobile-first) |
| `sw.js` | Service Worker (offline, notifications) |

**Apprentissage :**
- Apprend des habitudes de l'utilisateur (mots, contacts, lieux)
- Spécialisation automatique au profil (langue, centres d'intérêt)
- Hologramme personnel stocké localement

**Repo :** `github.com/kotto/ka-phone`

---

## 3. KA Enterprise AI — L'IA pour Entreprises

```
┌──────────────────────────────────────────────────────────┐
│  CIBLE       : Entreprises (devs, ops, support)          │
│  INTERFACE   : Dashboard web + API REST                  │
│  DÉPLOIEMENT : On-premise (serveur de l'entreprise)      │
│  DONNÉES     : Codebase, logs, tickets (confidentielles) │
│  MONÉTISATION: Licence annuelle par tenant                │
└──────────────────────────────────────────────────────────┘
```

**Objectif :** Diagnostiquer les bugs et incidents en <1ms avec 0% d'hallucination, en apprenant du contexte spécifique de l'entreprise.

**Spécificités (≠ moteur commun) :**
| Module | Rôle |
|--------|------|
| `enterprise_server.py` | Serveur Flask multi-tenant + upload fichiers |
| `enterprise_specializer.py` | Spécialisation auto (ingestion codebase → patterns) |
| Intégrations | Jira, GitHub, Sentry, Slack |
| `enterprise_dashboard.html` | Interface web drag-and-drop |
| ROI Dashboard | Temps gagné, accuracy, courbe d'apprentissage |

**Apprentissage :**
- Upload de fichiers (logs, code, docs) → création auto de patterns
- Feedback correctif → l'IA ne refera plus l'erreur
- Patterns personnalisés par tenant

**Repo :** `github.com/kotto/ka-enterprise-ai` (branche `ka-enterprise` du repo `harmonic`)

---

## 4. Harmonic AI — L'ULM (Chat Public Universel)

```
┌──────────────────────────────────────────────────────────┐
│  CIBLE       : Tout le monde (développeurs, curieux)     │
│  INTERFACE   : Chat web public                           │
│  DÉPLOIEMENT : Cloud (Render/Cloudflare)                 │
│  DONNÉES     : Publiques (FAQ, documentation, forums)    │
│  MONÉTISATION: Gratuit (vitrine technologique)           │
└──────────────────────────────────────────────────────────┘
```

**Objectif :** Démontrer la technologie. Un chat public où n'importe qui peut poser une question et obtenir une réponse sans hallucination. Les utilisateurs créent et partagent des hologrammes spécialisés.

**Spécificités (≠ moteur commun) :**
| Module | Rôle |
|--------|------|
| `ka_server.py` | Serveur public (Flask, API OpenAI-compatible) |
| `domain_router.py` | Routage vers le bon hologramme |
| `hologram_store.py` | Registre central des hologrammes téléchargeables |
| `hologram_connector.py` | Téléchargement + activation d'hologrammes |
| `ka_web_complete.html` | Interface chat publique |

**Apprentissage :**
- Hologrammes spécialisés créés par la communauté (ex: "hologramme Python", "hologramme React")
- Les utilisateurs enrichissent les hologrammes en posant des questions
- Système de feedback communautaire

**Repo :** `github.com/kotto/harmonic` (branche `main`)

---

## Tableau comparatif

```
┌──────────────────────────────────────────────────────────────────┐
│                  KA            KA ENTERPRISE     HARMONIC AI     │
│ ───────────────────────────────────────────────────────────────  │
│ CIBLE           Grand public   Entreprises       Tout le monde   │
│ INTERFACE       PWA mobile     Dashboard web     Chat web        │
│ DÉPLOIEMENT     On-device      On-premise        Cloud           │
│ DONNÉES         Personnelles   Confidentielles   Publiques       │
│ SPÉCIALISATION  Profil user    Upload fichiers   Hologrammes     │
│ APPRENTISSAGE   Habitudes      Feedback          Communauté      │
│ COMPRESSION     Oui (HCV)      Non               Non             │
│ MULTI-TENANT    Non            Oui               Non             │
│ INTÉGRATIONS    Téléphone      Jira/GitHub/      Aucune          │
│                                Sentry/Slack                      │
│ MONÉTISATION    Freemium       Licence/an        Gratuit         │
│ REPO            ka-phone       ka-enterprise-ai  harmonic        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Flux de données

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  MOTEUR HARMONIQUE (engine/)                                     │
│  ┌────────────────────────────────────────────────────────┐      │
│  │ generative_encoder.py  ← 17 concepts fondamentaux      │      │
│  │ harmonic_ai_v2.py      ← debug(), chat(), learn()      │      │
│  │ DICTIONNAIRE_ONDES.md  ← 200+ concepts traduits        │      │
│  └──────────────┬─────────────────────────────────────────┘      │
│                 │ importé par                                     │
│     ┌───────────┼───────────┐                                     │
│     ▼           ▼           ▼                                     │
│  KA (phone)  Enterprise   Harmonic AI                            │
│  ┌──────┐   ┌────────┐   ┌────────┐                              │
│  │PWA   │   │Flask   │   │Flask   │                              │
│  │local │   │server  │   │cloud   │                              │
│  └──────┘   └────────┘   └────────┘                              │
│     │           │           │                                     │
│     ▼           ▼           ▼                                     │
│  Hologramme  Hologramme  Hologrammes                             │
│  personnel   entreprise  communautaires                           │
│  (local)     (on-prem)  (cloud)                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Prochaines étapes

1. **Extraire le moteur commun** dans `engine/` proprement (déjà fait)
2. **Créer le repo `ka-phone`** dédié avec PWA + compression
3. **Créer le repo `ka-enterprise-ai`** dédié (extraire de la branche)
4. **Nettoyer `harmonic`** pour ne garder que le moteur + chat public
5. **Standardiser les imports** pour que chaque projet importe le moteur comme dépendance
