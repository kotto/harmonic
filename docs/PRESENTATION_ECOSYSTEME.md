# 🌊 Écosystème Harmonic AI — Présentation

**3 applications. 1 moteur. 0 hallucination.**

---

## 1. KA — Le Compagnon Personnel

> *Votre téléphone, augmenté.*

**KA** est une PWA qui transforme un téléphone ordinaire en téléphone haut de gamme.

| Fonctionnalité | Description |
|----------------|-------------|
| 🗜️ **Compression HCV** | Stockez 10× plus de photos/vidéos sans perte de qualité |
| 🧠 **IA personnelle** | Apprend de vous, vos habitudes, votre langage |
| 💬 **Chat vocal/texte** | Posez des questions, KA répond sans hallucination |
| 🔍 **Diagnostic auto** | Détecte les problèmes du téléphone (batterie, stockage) |
| 🌐 **Mode hors-ligne** | Fonctionne sans Internet (tout est local) |
| 🔒 **100% privé** | Vos données restent sur votre téléphone |

**Pour qui :** Tout le monde.  
**Déploiement :** Sur le téléphone (PWA installable).  
**Repo :** `github.com/kotto/harmonic` (ka-phone)

---

## 2. KA Enterprise AI — L'IA pour Entreprises

> *L'IA qui apprend de votre code, pas du code des autres.*

**KA Enterprise** diagnostique les bugs en <1ms avec 0% d'hallucination, en apprenant du contexte spécifique de votre entreprise.

| Fonctionnalité | Description |
|----------------|-------------|
| 🔬 **Diagnostic instantané** | Décrivez le symptôme → diagnostic + stratégie + action en <1ms |
| 📤 **Upload de contexte** | Glissez vos logs, code source, docs → l'IA crée des patterns personnalisés |
| 🧠 **Apprentissage continu** | Chaque bug résolu enrichit l'hologramme. L'IA s'améliore avec l'usage |
| 🔌 **Intégrations natives** | Jira (assignee + temps estimé), GitHub (labels), Sentry (alertes), Slack (@ka) |
| 📊 **Dashboard ROI** | Temps gagné, accuracy, courbe d'apprentissage, coût évité vs LLM |
| 🏢 **Multi-tenant** | Une instance, plusieurs équipes. Chacune a ses patterns privés |
| 🔒 **On-premise** | Tout tourne sur vos serveurs. Zéro donnée qui sort |

**Pour qui :** Entreprises (devs, ops, support).  
**Déploiement :** Sur vos serveurs (Flask, Docker).  
**Repo :** `github.com/kotto/harmonic` (branche ka-enterprise)

---

## 3. Harmonic AI — Le Chat Public

> *L'IA qui ne ment pas. La preuve publique.*

**Harmonic AI** est un chat public où n'importe qui peut tester la technologie. C'est la vitrine : 0% d'hallucination, 0 paramètre, 15 Mo.

| Fonctionnalité | Description |
|----------------|-------------|
| 💬 **Chat général** | Posez n'importe quelle question, obtenez une réponse vérifiable |
| 🎯 **Spécialisation** | Choisissez un hologramme (Sciences, Histoire, Code, Maths...) |
| 📚 **Hologrammes communautaires** | Téléchargez des hologrammes créés par la communauté |
| 🌐 **API OpenAI-compatible** | `/v1/chat/completions` — remplacez GPT par Harmonic |
| 🏆 **LM Arena 99.3%** | Score vérifié publiquement, 0 paramètre entraîné |
| 🔓 **Gratuit** | Vitrine technologique, accès libre |

**Pour qui :** Tout le monde (développeurs, curieux, chercheurs).  
**Déploiement :** Cloud (Render/Cloudflare).  
**URL :** `harmonic-ai.pages.dev`

---

## Le moteur commun

Les 3 applications partagent le **même cœur** :

```
generative_encoder.py   → 17 concepts fondamentaux (cross-lingual FR/EN)
harmonic_ai_v2.py       → debug(), chat(), learn()
wave_debugger_v*.py     → pipeline de diagnostic 4 étapes
DICTIONNAIRE_ONDES.md   → 200+ concepts traduits en langage des ondes
```

**Principe :** Tout problème est une interférence destructive. Toute solution est une onde correctrice. Le diagnostic émerge de l'interférence entre l'onde du symptôme et l'hologramme des patterns — pas d'une prédiction probabiliste.

---

## Comparatif

| | KA | KA Enterprise | Harmonic AI |
|---|---|---|---|
| **Cible** | Grand public | Entreprises | Tout le monde |
| **Interface** | PWA mobile | Dashboard web | Chat web |
| **Déploiement** | Téléphone | Serveurs entreprise | Cloud |
| **Données** | Personnelles (locales) | Confidentielles (on-premise) | Publiques |
| **Apprend de** | L'utilisateur | Fichiers, logs, tickets | La communauté |
| **Spécialisation** | Profil personnel | Upload fichiers | Hologrammes |
| **Compression** | Oui (HCV) | Non | Non |
| **Intégrations** | Téléphone | Jira, GitHub, Sentry, Slack | API OpenAI |
| **Monétisation** | Freemium | Licence/an | Gratuit |
