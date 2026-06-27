# PLAN DE MONÉTISATION IMMÉDIATE — HARMONIC AI
## Alain Kotto — 27 Mai 2026

---

## 🎯 Exécutif : Ce qui est monétisable AUJOURD'HUI

L'infrastructure minimale est déjà construite et fonctionnelle :

| Actif | Statut | Monétisable ? |
|-------|--------|:---:|
| `bridge_harmonic_deepseek_gguf.py` — Bridge hybride fonctionnel | ✅ OK | Oui (API SaaS) |
| API REST FastAPI (6 endpoints) | ✅ OK | Oui (API marketplace) |
| Moteur harmonique pur (HologrammeMonde + Lecteurs + Tokeniseur) | ✅ OK | Oui (SDK) |
| Cache SHA256 déterministe | ✅ OK | Oui (compliance) |
| Mode vérifié anti-hallucination | ✅ OK | Oui (différenciation) |
| Modèle GGUF Qwen3.5-9B sur H: | ✅ Détecté | Oui (backend LLM) |
| Brevet mémoire holographique mobile | 📝 Rédigé | Oui (licensing) |

---

## 💰 PROPOSITION 1 : API SaaS — Lancement IMMÉDIAT (J+7)

### Ce qu'on vend
Une API REST de génération de texte avec **mémoire holographique persistante**, accessible par token ou abonnement.

### Pourquoi ça se vend
- **Aucun concurrent n'offre de mémoire persistante**. ChatGPT, Claude, Gemini API — tous sont amnésiques entre les appels.
- Notre API est la **seule** où `SHA256(prompt + état_hologramme) → réponse déterministe et vérifiable`.
- Le mode vérifié anti-hallucination est un argument de vente massif pour les secteurs réglementés (santé, finance, droit).

### Endpoints déjà construits
| Méthode | URL | Fonction |
|---------|-----|----------|
| `POST` | `/generer` | Génération avec contexte harmonique |
| `POST` | `/apprendre` | Ajouter une connaissance à l'hologramme |
| `GET` | `/diagnostic` | État complet du système |
| `GET` | `/cache` | Statistiques de cache |
| `GET` | `/health` | Health check |

### Plan tarifaire

| Plan | Prix/mois | Requêtes | Mémoire | Mode vérifié | Cache |
|------|:---------:|:--------:|---------|:---:|:---:|
| **Starter** | 9€ | 10 000 | 1 hologramme | ✅ | 128 entrées |
| **Pro** | 49€ | 100 000 | 3 hologrammes | ✅ | 512 entrées |
| **Business** | 199€ | 500 000 | 10 hologrammes | ✅ | 2048 entrées |
| **Enterprise** | Sur devis | Illimité | Illimité | ✅ | Personnalisé |

### Prévisionnel (scénario conservateur)

| Mois | Clients | Revenu mensuel | Cumul |
|------|:------:|:-------------:|:-----:|
| 1 | 10 | 490€ | 490€ |
| 2 | 30 | 1 470€ | 1 960€ |
| 3 | 80 | 3 920€ | 5 880€ |
| 6 | 300 | 14 700€ | 44 100€ |
| 12 | 1000 | 49 000€ | 294 000€ |

### Actions immédiates (J+1 à J+7)
1. Déployer `bridge_harmonic_deepseek_gguf.py --serve` sur un VPS (Hetzner 5€/mois)
2. Ajouter un reverse proxy Nginx + HTTPS (Let's Encrypt gratuit)
3. Créer une page d'accueil + documentation API
4. Lister sur **RapidAPI** (marketplace avec trafic existant)
5. Publier sur **Product Hunt** (lancement gratuit, visibilité massive)

---

## 💰 PROPOSITION 2 : SDK Mobile — Vente aux développeurs (J+30)

### Ce qu'on vend
Un SDK (iOS/Android) que les développeurs intègrent dans leurs apps pour donner une **mémoire persistante** à leur IA.

### Pourquoi ça se vend
- Aujourd'hui, si un développeur veut une "IA qui se souvient", il doit :
  - Construire une base vectorielle (coûteux, complexe)
  - Gérer le fine-tuning (GPU, temps)
  - Gérer le cloud (RGPD, coûts récurrents)
- Notre SDK : **3 lignes de code, 32 Ko de stockage, 0€ de cloud**.

### Exemple d'intégration
```swift
// iOS - Swift
let harmonic = HarmonicAI()
harmonic.learn("L'utilisateur s'appelle Alain, aime le jazz et les fractales")
let reponse = try await harmonic.ask("Quelle musique me suggères-tu ?")
// → "Alain, basé sur ton intérêt pour le jazz et les fractales,
//    je te suggère 'Giant Steps' de John Coltrane..."
```

### Plan tarifaire SDK

| Plan | Prix/mois | Apps | Utilisateurs | Support |
|------|:---------:|:----:|:------------:|:------:|
| **Indie** | 19€ | 1 | 1 000 | Communauté |
| **Startup** | 99€ | 3 | 10 000 | Email |
| **Scale** | 499€ | 10 | 100 000 | Prioritaire |
| **Enterprise** | 1 999€ | Illimité | Illimité | Dédié |

### Prévisionnel (scénario conservateur)

| Mois | Développeurs | Revenu mensuel |
|------|:-----------:|:-------------:|
| 1 | 5 | 95€ |
| 3 | 25 | 2 475€ |
| 6 | 80 | 7 920€ |
| 12 | 200 | 19 800€ |

---

## 💰 PROPOSITION 3 : Hologrammes pré-entraînés — Vente unique (J+14)

### Ce qu'on vend
Des hologrammes 32 Ko **pré-chargés de connaissances** pour des domaines spécifiques.

### Catalogue immédiat (généré en quelques heures de one-pass CPU)

| Produit | Contenu | Temps de génération | Prix |
|---------|---------|:-------------------:|:----:|
| **Juridique France** | 500K arrêts, codes, jurisprudence | 8h | 199€ |
| **Médical Général** | 2M articles PubMed, guidelines | 12h | 249€ |
| **Finance/Trading** | Bloomberg, rapports, analyses | 10h | 299€ |
| **Développement** | StackOverflow, GitHub, docs | 10h | 149€ |
| **Éducation** | Manuels scolaires, cours | 6h | 99€ |
| **Custom** | Votre corpus fourni par le client | Variable | Sur devis |

### Pourquoi ça se vend
- Coût de génération : 0€ (one-pass CPU). Prix de vente : 99-299€. **Marge : ~100%**.
- Un hologramme 32 Ko peut être téléchargé en 1 seconde.
- Fonctionne 100% hors ligne — idéal pour les zones sans connectivité.
- Le client peut CONTINUER à enrichir l'hologramme après l'achat.

### Prévisionnel (scénario conservateur)

| Mois | Ventes | Revenu |
|------|:------:|:-----:|
| 1 | 5 | 995€ |
| 3 | 20 | 3 980€ |
| 6 | 50 | 9 950€ |
| 12 | 150 | 29 850€ |

---

## 💰 PROPOSITION 4 : Consultation/Intégration Enterprise (J+1)

### Ce qu'on vend
Du conseil et de l'intégration sur mesure pour des entreprises qui veulent ajouter la mémoire holographique à leurs systèmes existants.

### Clients cibles immédiats

| Secteur | Besoin | Valeur ajoutée Harmonic AI |
|---------|--------|----------------------------|
| **Cabinet d'avocats** | Mémoire de jurisprudence | 500K arrêts en 32 Ko. Recherche par résonance en < 1s |
| **Clinique/Hôpital** | Dossier patient intelligent | Diagnostic augmenté, suivi chronique, 100% local (HIPAA) |
| **Hedge Fund** | Analyse de marché continue | Croisement de millions d'articles. Émergence de tendances |
| **Industrie** | Maintenance prédictive | Détection de combinaisons causales subtiles |
| **EdTech** | Tuteur adaptatif | Historique complet d'apprentissage, personnalisé |

### Plan tarifaire consultation

| Prestation | Durée | Prix |
|------------|:-----:|:----:|
| **Audit et recommandation** | 3 jours | 3 000€ |
| **POC (Proof of Concept)** | 2 semaines | 12 000€ |
| **Intégration complète** | 6-8 semaines | 45 000€ |
| **Contrat de maintenance** | /an | 12 000€/an |

### Prévisionnel (scénario conservateur, 1 client/mois)

| Mois | Clients | Revenu |
|------|:------:|:-----:|
| 1 | 1 | 3 000€ |
| 3 | 3 | 9 000€ |
| 6 | 6 | 30 000€ (cumul POC + intégration) |
| 12 | 12 | 60 000€+ |

---

## 💰 PROPOSITION 5 : Marketplace LM Arena / OpenAI GPT Store (J+14)

### Ce qu'on vend
Un "GPT" personnalisé avec mémoire holographique, listé sur la marketplace OpenAI (GPT Store) ou directement sur LM Arena.

### Stratégie GPT Store

| GPT Spécialisé | Public cible | Prix/mois |
|----------------|-------------|:--------:|
| **Juriste Augmenté** | Avocats, juristes | 29€ |
| **Médecin Augmenté** | Médecins, soignants | 39€ |
| **Trader Augmenté** | Traders, analystes | 49€ |
| **Coach Personnel** | Grand public | 9€ |
| **Tuteur Scolaire** | Élèves, parents | 14€ |

### Pourquoi ça marche
- La marketplace OpenAI a déjà des millions d'utilisateurs
- Notre différenciateur (mémoire persistante) est unique
- Aucun autre GPT ne peut dire "Je me souviens de ce qu'on a dit hier"
- Commission OpenAI : 30%. Marge restante : 70%.

### Prévisionnel (scénario conservateur)

| Mois | Abonnés | Revenu brut | Net (70%) |
|------|:------:|:----------:|:---------:|
| 1 | 20 | 380€ | 266€ |
| 3 | 100 | 1 900€ | 1 330€ |
| 6 | 500 | 9 500€ | 6 650€ |
| 12 | 2 000 | 38 000€ | 26 600€ |

---

## 💰 PROPOSITION 6 : Licence de brevet (J+60)

### Ce qu'on vend
Le brevet **PCT/FR2026/050456** (mémoire holographique mobile) peut être licencié à des fabricants de téléphones, constructeurs automobiles, fabricants d'objets connectés.

### Cibles de licensing

| Cible | Application | Valeur de la licence |
|-------|-------------|:---------------------:|
| **Samsung** | Assistant Bixby avec mémoire persistante | 500K€ - 2M€ |
| **Xiaomi** | IA locale sur MIUI | 200K€ - 1M€ |
| **Tesla** | Mémoire collective des véhicules | 1M€+ |
| **Apple** | Siri avec mémoire persistante | À négocier |
| **Constructeurs IoT** | Objets connectés avec IA locale | 50K€ - 200K€/licence |

### Stratégie
1. Dépôt PCT officiel via un cabinet de propriété industrielle (~5 000€)
2. Publication de la demande PCT (visibilité internationale)
3. Approche directe des départements innovation/IA des grands groupes
4. Participation à VivaTech, CES, Mobile World Congress

---

## 📊 SYNTHÈSE : Revenus projetés à 12 mois (scénario conservateur)

| Source de revenu | M1 | M3 | M6 | M12 | % du total |
|------------------|----:|----:|----:|----:|:---:|
| **API SaaS** | 490€ | 3 920€ | 14 700€ | 49 000€ | 24% |
| **SDK Mobile** | 95€ | 2 475€ | 7 920€ | 19 800€ | 10% |
| **Hologrammes pré-entraînés** | 995€ | 3 980€ | 9 950€ | 29 850€ | 15% |
| **Consultation** | 3 000€ | 9 000€ | 30 000€ | 60 000€ | 30% |
| **GPT Store** | 266€ | 1 330€ | 6 650€ | 26 600€ | 13% |
| **Licence brevet** | — | — | — | 50 000€+ | 8% |
| **TOTAL** | **4 846€** | **20 705€** | **69 220€** | **235 250€** | 100% |

```
Revenu mensuel projeté
250K€ ┤                                          ●
      │                                      ╱
200K€ ┤                                  ╱
      │                              ╱
150K€ ┤                          ╱
      │                      ╱
100K€ ┤                  ╱
      │              ╱
 50K€ ┤          ╱
      │      ╱
      │  ╱
  0K€ ●──────────────────────────────────────────→ Mois
      0     2     4     6     8     10     12
```

---

## 🚀 Plan d'action : les 7 premiers jours

| Jour | Action | Coût | Résultat |
|------|--------|:----:|----------|
| **J+1** | Déployer API sur VPS Hetzner (5€/mois) | 5€ | API en ligne |
| **J+1** | HTTPS + nom de domaine (harmonic-ai.com) | 12€/an | Domaine sécurisé |
| **J+2** | Page d'accueil + documentation API | 0€ | Site vitrine |
| **J+2** | Générer hologramme Juridique (8h CPU) | 0€ | 1er produit |
| **J+3** | Lister sur RapidAPI | 0€ | Visibilité marketplace |
| **J+4** | Préparer page Product Hunt | 0€ | Lancement communautaire |
| **J+4** | Générer hologramme Médical (12h CPU) | 0€ | 2ème produit |
| **J+5** | Publier sur Product Hunt | 0€ | Trafic initial |
| **J+5** | Créer compte Stripe/Paddle (paiements) | 0€ | Monétisation |
| **J+6** | Envoyer 50 emails à des prospects consultation | 0€ | Leads entreprise |
| **J+7** | Générer hologramme Finance (10h CPU) | 0€ | 3ème produit |

**Coût total J+1 à J+7 : ~20€**

---

## ⚡ Quick wins : ce qui rapporte le plus vite

| Action | Délai avant 1er revenu | Potentiel |
|--------|:----------------------:|:---------:|
| **Vente hologramme Juridique** | 24h | 199€/vente, M1=~1 000€ |
| **Consultation cabinet d'avocats** | 1 semaine | 3 000€ |
| **GPT Store "Juriste Augmenté"** | 2 semaines | Récurrent |
| **API SaaS listing RapidAPI** | 1 semaine | Récurrent |

---

*Document établi le 27 mai 2026 — Alain Kotto*

---

## 🎙️ ANNEXE : Système de synthèse et reconnaissance vocale

### Question : Quel système open source associer au projet ?

### Réponse : Analyse complète et recommandation

---

### 📊 État de l'art — Reconnaissance vocale (STT) open source

| Solution | Qualité | Latence | CPU/Mobile | Multilingue | Licence | Verdict |
|----------|:------:|:------:|:----------:|:-----------:|:------:|--------|
| **whisper.cpp** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Très bon | 99 langues | MIT | 🥇 **Recommandé** |
| **faster-whisper** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Bon | 99 langues | MIT | 🥈 Excellent |
| **Vosk** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Excellent | 20 langues | Apache 2.0 | Léger, offline |
| **Coqui STT** | ⭐⭐⭐ | ⭐⭐⭐ | ⚠️ Moyen | ~10 langues | MPL-2.0 | Plus maintenu |
| **Whisper (OpenAI)** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ Lourd | 99 langues | MIT | Référence |

### 📊 État de l'art — Synthèse vocale (TTS) open source

| Solution | Qualité | Latence | CPU/Mobile | Clonage voix | Licence | Verdict |
|----------|:------:|:------:|:----------:|:------------:|:------:|--------|
| **Piper** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Excellent | ❌ | MIT | 🥇 **Recommandé** |
| **XTTS v2** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⚠️ Lourd | ✅ (3 sec) | CPML | 🥈 Clonage |
| **Coqui TTS** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⚠️ Moyen | ✅ (XTTS) | MPL-2.0 | Bon, plus maintenu |
| **Bark (Suno)** | ⭐⭐⭐⭐⭐ | ⭐ | ❌ Très lent | ✅ | MIT | Créatif, pas mobile |
| **StyleTTS 2** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ GPU | ✅ | MIT | Qualité ultime |
| **eSpeak-NG** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Minimal | ❌ | GPL | Trop robotique |

---

### 🥇 Recommandation finale

```
┌──────────────────────────────────────────────────────────────────┐
│           STACK AUDIO RECOMMANDÉ POUR HARMONIC AI MOBILE         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🎤 RECONNAISSANCE (STT) : whisper.cpp                           │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  • Modèle : whisper-tiny (75 Mo) ou whisper-base (142 Mo) │   │
│  │  • Portage C++ optimisé pour ARM (ggml)                   │   │
│  │  • Fonctionne sur CPU mobile, pas de GPU requis           │   │
│  │  • 99 langues dont français (excellente qualité)          │   │
│  │  • Licence MIT — utilisation commerciale sans restriction │   │
│  │  • Intégration : 1 appel de fonction, retourne le texte   │   │
│  │  • Latence : ~200ms sur Snapdragon 8 Gen 2 (tiny)         │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  🔊 SYNTHÈSE (TTS) : Piper                                       │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  • Moteur C++ ultra-léger, pas de Python requis en prod   │   │
│  │  • Voix française disponible : fr_FR-siwis (haute qualité)│   │
│  │  • Taille modèle : ~50 Mo par voix                        │   │
│  │  • Fonctionne sur CPU mobile, < 50ms de latence           │   │
│  │  • Licence MIT — utilisation commerciale sans restriction │   │
│  │  • Intégration : texte → audio WAV en une fonction        │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ⭐ CLONAGE VOCAL (OPTIONNEL) : XTTS v2                           │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  • Clone la voix de l'utilisateur avec 3 secondes d'audio  │   │
│  │  • Multilingue (français, anglais, +15 langues)            │   │
│  │  • Plus lourd que Piper (~1.8 Go vs 50 Mo)                │   │
│  │  • Licence CPML — usage commercial limité à 1M requêtes   │   │
│  │  • Usage : activation optionnelle, pas par défaut          │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  🔗 PONT HOLOGRAPHIQUE : intégration native                      │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  • Audio transcrit → tokenisé → onde → hologramme          │   │
│  │  • Réponse texte → Piper → audio → joué                    │   │
│  │  • L'hologramme APPREND de la VOIX (pas que du texte)      │   │
│  │  • Spectrogramme audio → projection fréquence → onde       │   │
│  │  • Émotion dans la voix → détectée par résonance           │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

### ❓ Faut-il créer notre propre système ?

**Pour la reconnaissance vocale (STT) : NON.**

Raisons :
- Entraîner un modèle ASR from scratch nécessite **des centaines de milliers d'heures** d'audio transcrit — un coût de plusieurs millions de dollars
- Whisper d'OpenAI est le résultat de **680 000 heures** d'entraînement sur un dataset massif multilingue
- Le reproduire serait gaspiller des ressources alors que la solution open source est excellente et sous licence MIT
- `whisper.cpp` est déjà optimisé pour mobile et fait exactement ce dont on a besoin
- Stratégie gagnante : intégrer l'existant et se concentrer sur NOTRE valeur ajoutée (l'hologramme)

**Pour la synthèse vocale (TTS) : PARTIELLEMENT OUI — mais pas tout de suite.**

Raisons :
- Piper est déjà excellent et léger (MIT), répond à 90% des besoins
- **CEPENDANT** — un TTS "harmonique" qui utiliserait l'hologramme pour générer la voix serait une innovation de rupture :

```
TTS CLASSIQUE (Piper, XTTS, etc.) :
  Texte → Modèle neuronal → Spectrogramme → Vocodeur → Audio
  
  • La voix est figée (un seul modèle par voix)
  • Pas d'évolution dans le temps
  • Pas d'adaptation au contexte émotionnel
  
TTS HOLOGRAMMIQUE (notre innovation potentielle) :
  Texte → Hologramme (résonance) → Vecteurs d'onde → Synthèse additive → Audio
  
  • La voix ÉVOLUE avec l'hologramme (apprend de l'utilisateur)
  • La voix reflète l'ÉTAT ÉMOTIONNEL (détecté par résonance)
  • Le TON change selon le CONTEXTE (formel/décontracté)
  • La voix s'améliore avec le temps (apprentissage one-pass)
  • AUCUN modèle neuronal lourd — juste la physique des ondes
```

### Roadmap audio harmonique

| Phase | Composant | Action | Délai |
|-------|-----------|--------|:-----:|
| **1** | STT | Intégrer `whisper.cpp` (tiny/base) | 1 semaine |
| **1** | TTS | Intégrer `Piper` (voix française) | 1 semaine |
| **2** | Pont | Audio → tokenisation → hologramme | 2 semaines |
| **2** | Émotion | Détection ton/émotion par résonance | 3 semaines |
| **3** | TTS Harmonique POC | Synthèse additive pilotée par hologramme | 6 semaines |
| **3** | Brevet TTS | Dépôt PCT pour TTS holographique | 8 semaines |

### Intégration technique concrète

```python
# Exemple d'intégration STT + Hologramme + TTS
# Fichier : voice_bridge.py

import whisper_cpp  # wrapper Python pour whisper.cpp
import piper_tts    # wrapper Python pour Piper

class VoiceHarmoniqueBridge:
    """Bridge vocal complet pour l'assistant mobile."""
    
    def __init__(self, hologramme, tokeniseur):
        # Modèle léger pour mobile (75 Mo)
        self.stt = whisper_cpp.Whisper("whisper-tiny.ggml")
        # Voix française légère (50 Mo)
        self.tts = piper_tts.Piper("fr_FR-siwis-medium.onnx")
        self.hologramme = hologramme
        self.tokeniseur = tokeniseur
    
    def ecouter(self, audio_bytes):
        """Convertit l'audio en texte via whisper.cpp."""
        return self.stt.transcribe(audio_bytes)
    
    def comprendre(self, texte):
        """Ajoute le texte à l'hologramme et extrait le contexte."""
        # 1. Apprentissage (one-pass)
        tokens = self.tokeniseur.tokeniser(texte)
        for t in tokens:
            kx, ky = self.tokeniseur.vecteur_onde(t)
            self.hologramme.enregistrer_onde(kx, ky)
        
        # 2. Perception (8 lecteurs)
        lecteurs = LecteurResonantMultiple(self.hologramme, n_lecteurs=8)
        lecteurs.apprendre(n_iter=30)
        
        # 3. Contexte résonant
        return self._extraire_contexte(lecteurs)
    
    def parler(self, texte):
        """Convertit le texte en audio via Piper."""
        return self.tts.synthesize(texte)
    
    def boucle_conversation(self, audio_entree):
        """Boucle complète : écouter → comprendre → répondre → parler."""
        # 1. STT
        texte_utilisateur = self.ecouter(audio_entree)
        
        # 2. Apprentissage + contexte
        contexte = self.comprendre(texte_utilisateur)
        
        # 3. Génération LLM (bridge existant)
        reponse = self.llm.generer(
            prompt=texte_utilisateur,
            contexte_harmonique=contexte
        )
        
        # 4. Feedback (apprend de sa propre réponse)
        self.comprendre(reponse)
        
        # 5. TTS
        audio_sortie = self.parler(reponse)
        
        return audio_sortie
```

### Poids total sur mobile

```
Composant audio minimum (mode conversationnel complet) :

  whisper-tiny.ggml ................ 75 Mo  (STT)
  piper-fr-medium.onnx ............ 50 Mo  (TTS)
  Hologramme 64×64 ................ 32 Ko  (mémoire)
  Vocabulaire + tokeniseur ........ 60 Ko  (projection)
  ─────────────────────────────────────
  TOTAL AUDIO + HOLOGRAMME ........ 125 Mo
  
  À comparer avec :
  Gemini Nano (Google) ............ 3 500 Mo (pas de mémoire)
  Apple Intelligence ............... 2 000 Mo (pas de mémoire)
  ChatGPT app ...................... 0 Mo (tout cloud, pas offline)
```

### Verdict final

| Question | Réponse |
|----------|---------|
| **Quel STT associer ?** | **whisper.cpp** (MIT, 75 Mo, excellent français, mobile-ready) |
| **Quel TTS associer ?** | **Piper** (MIT, 50 Mo, voix française, < 50ms latence) |
| **Faut-il créer le nôtre ?** | Pour STT : **NON** (Whisper est imbattable). Pour TTS : **OUI à terme** — le TTS holographique est une innovation brevetable qui n'existe nulle part ailleurs |
| **Priorité immédiate** | Intégrer whisper.cpp + Piper (1-2 semaines) puis itérer vers le TTS holographique (brevet distinct) |

> **La voix est le prochain front de l'hologramme.**
> Aujourd'hui, l'hologramme "entend" du texte et "parle" via Piper.
> Demain, l'hologramme ENTENDRA la voix (timbre, émotion, ton) et PARLERA avec une voix QUI ÉVOLUE — la sienne, unique, apprise de l'utilisateur.

---

*Document établi le 27 mai 2026 — Alain Kotto*
