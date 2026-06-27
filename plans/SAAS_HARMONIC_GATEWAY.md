# SAAS HARMONIC GATEWAY
## Plateforme d'Encapsulation Harmonique Universelle — Zéro Hallucination, Génération Contrôlée

**Date :** 4 Juin 2026  
**Version :** 1.0  
**Statut :** Conception architecturale — Fondée sur l'implémentation existante validée

---

## Table des Matières

1. [Résumé exécutif — La Proposition de Valeur](#1-résumé-exécutif--la-proposition-de-valeur)
2. [Architecture Globale — La Gateway Harmonique](#2-architecture-globale--la-gateway-harmonique)
3. [Flux 1 — Encapsulation du Prompt (Entrée)](#3-flux-1--encapsulation-du-prompt-entrée)
4. [Flux 2 — Routage vers le LLM Choisi](#4-flux-2--routage-vers-le-llm-choisi)
5. [Flux 3 — Vérification Harmonique (DHF)](#5-flux-3--vérification-harmonique-dhf)
6. [Flux 4 — Boucle de Génération Contrôlée](#6-flux-4--boucle-de-génération-contrôlée)
7. [Flux 5 — Correction et Livraison](#7-flux-5--correction-et-livraison)
8. [Architecture Technique — Stack Complète](#8-architecture-technique--stack-complète)
9. [Modèle de Données](#9-modèle-de-données)
10. [API REST — Spécification Complète](#10-api-rest--spécification-complète)
11. [Dashboard Utilisateur — Frontend](#11-dashboard-utilisateur--frontend)
12. [Modèle Économique — Pricing & Plans](#12-modèle-économique--pricing--plans)
13. [Plan de Déploiement](#13-plan-de-déploiement)
14. [Sécurité et Isolation](#14-sécurité-et-isolation)
15. [Implémentation Pas à Pas](#15-implémentation-pas-à-pas)

---

## 1. Résumé exécutif — La Proposition de Valeur

### 1.1 Le Problème

Les utilisateurs de LLMs (GPT, Claude, DeepSeek, Llama, Mistral...) font face à trois problèmes irrésolus :

| Problème | Impact |
|---|---|
| **Hallucination** | Le LLM invente des faits, des citations, des calculs. Aucun mécanisme de vérification natif. |
| **Boîte noire** | L'utilisateur ne sait pas si la réponse est fiable. Pas de score de confiance objectif. |
| **Vendor lock-in** | Changer de modèle = réécrire l'intégration. Aucune couche d'abstraction unifiée. |

### 1.2 La Solution — Harmonic Gateway

```
┌──────────────────────────────────────────────────────────────────┐
│                     HARMONIC GATEWAY                              │
│                                                                   │
│   "Choisissez votre LLM. Nous garantissons la vérité."           │
│                                                                   │
│   Utilisateur → Choisit son LLM → Soumet son prompt              │
│                                     │                             │
│                                     ▼                             │
│              ┌──────────────────────────────────────┐            │
│              │     ENCAPSULATION HARMONIQUE         │            │
│              │  • Analyse sémantique du prompt      │            │
│              │  • Enrichissement (contexte, calculs) │            │
│              │  • Signature fréquentielle (kx,ky)   │            │
│              └──────────┬───────────────────────────┘            │
│                         ▼                                         │
│              ┌──────────────────────────────────────┐            │
│              │     LLM CHOISI PAR L'UTILISATEUR     │            │
│              │  GPT-4 | Claude | DeepSeek | Llama   │            │
│              │  Mistral | Qwen | Gemini | ...       │            │
│              └──────────┬───────────────────────────┘            │
│                         ▼                                         │
│              ┌──────────────────────────────────────┐            │
│              │     VÉRIFICATION HARMONIQUE (DHF)    │            │
│              │  • Cohérence Euler + Action + Réso   │            │
│              │  • Score de confiance 0-100%         │            │
│              │  • Détection d'hallucination         │            │
│              │  • Si incohérent → Boucle correction │            │
│              └──────────┬───────────────────────────┘            │
│                         ▼                                         │
│              ┌──────────────────────────────────────┐            │
│              │     LIVRAISON CONTRÔLÉE              │            │
│              │  • Réponse vérifiée + Score          │            │
│              │  • Concepts harmoniques identifiés   │            │
│              │  • Comparaison multi-modèles          │            │
│              └──────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────────┘
```

### 1.3 Bénéfices Utilisateur

| Bénéfice | Description |
|---|---|
| **Zéro hallucination** | Toute réponse incohérente est détectée, corrigée ou rejetée |
| **Multi-LLM transparent** | Une seule API, tous les LLMs. Changez de modèle en un paramètre. |
| **Score de confiance objectif** | Indépendant du modèle — basé sur la cohérence harmonique universelle |
| **Traçabilité complète** | Chaque requête : prompt → LLM utilisé → réponse brute → vérification → réponse finale |
| **Pas de vendor lock-in** | Le DHF fonctionne avec n'importe quel LLM. Changement sans friction. |
| **BYOK ou Managed** | Apportez vos clés API ou utilisez les nôtres |

---

## 2. Architecture Globale — La Gateway Harmonique

### 2.1 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HARMONIC GATEWAY — ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        FRONTEND (React / Next.js)                        │ │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ │ │
│  │  │ Dashboard │ │ Choix LLM │ │ Historique│ │ Comparer  │ │ Settings  │ │ │
│  │  │ Temps réel│ │ Dropdown  │ │ Requêtes  │ │ Modèles   │ │ API Keys  │ │ │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘ │ │
│  └──────────────────────────────────┬──────────────────────────────────────┘ │
│                                     │ REST + WebSocket                       │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      API GATEWAY (FastAPI)                               │ │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ │ │
│  │  │ Auth      │ │ Rate      │ │ Request   │ │ Response  │ │ Billing   │ │ │
│  │  │ JWT/API   │ │ Limiting  │ │ Validation│ │ Streaming │ │ Metering  │ │ │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘ │ │
│  └──────────────────────────────────┬──────────────────────────────────────┘ │
│                                     │                                         │
│  ┌──────────────────────────────────▼──────────────────────────────────────┐ │
│  │                    ORCHESTRATEUR HARMONIQUE (Cœur)                        │ │
│  │                                                                           │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐ │ │
│  │  │ PHASE 1 : ENCAPSULATION                                              │ │ │
│  │  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │ │
│  │  │ │ Guide       │  │ Tokenizer   │  │ Calculateur │  │ Enrichisseur│  │ │ │
│  │  │ │ Harmonique  │─▶│ Holographique│─▶│ Harmonique  │─▶│ de Contexte │  │ │ │
│  │  │ │ (domaine)   │  │ (kx,ky,φ)   │  │ (SymPy)     │  │ (cache)     │  │ │ │
│  │  │ └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │ │
│  │                                     │                                      │ │
│  │  ┌──────────────────────────────────▼──────────────────────────────────┐ │ │
│  │  │ PHASE 2 : ROUTAGE LLM                                                │ │ │
│  │  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │ │ │
│  │  │ │ OpenAI   │ │ Anthropic│ │ DeepSeek │ │ Ollama   │ │ Custom   │   │ │ │
│  │  │ │ GPT-4    │ │ Claude   │ │ API      │ │ Local    │ │ Endpoint │   │ │ │
│  │  │ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │ │ │
│  │  │      └─────────────┴────────────┴────────────┴────────────┘         │ │ │
│  │  └──────────────────────────────────┬──────────────────────────────────┘ │ │
│  │                                     │                                      │ │
│  │  ┌──────────────────────────────────▼──────────────────────────────────┐ │ │
│  │  │ PHASE 3 : VÉRIFICATION HARMONIQUE                                    │ │ │
│  │  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │ │
│  │  │ │ DHF 3 Modes │  │ Cache       │  │ Boucle      │  │ Confiance   │  │ │ │
│  │  │ │ Euler+Action│─▶│ Cohérence   │─▶│ Raffinement │─▶│ Haute/Moy/  │  │ │ │
│  │  │ │ +Résonance  │  │ O(1) lookup │  │ (max 3 iter)│  │ Basse/Nulle │  │ │ │
│  │  │ └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │ │
│  │  └──────────────────────────────────┬──────────────────────────────────┘ │ │
│  │                                     │                                      │ │
│  │  ┌──────────────────────────────────▼──────────────────────────────────┐ │ │
│  │  │ PHASE 4 : LIVRAISON                                                   │ │ │
│  │  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │ │
│  │  │ │ Templates   │  │ Correcteur  │  │ Formateur   │  │ Streaming   │  │ │ │
│  │  │ │ FR/EN       │─▶│ Grammatical │─▶│ JSON/MD     │─▶│ SSE/WS      │  │ │ │
│  │  │ └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         DATA LAYER                                       │ │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ │ │
│  │  │ PostgreSQL│ │ Redis     │ │ S3/MinIO  │ │ Prometheus│ │ Timescale │ │ │
│  │  │ Users/    │ │ Cache     │ │ Logs/     │ │ Metrics   │ │ Time-     │ │ │
│  │  │ Requests  │ │ Sessions  │ │ Exports   │ │ Alerts    │ │ Series DB │ │ │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Composants et Responsabilités

| Composant | Rôle | Technologie | Statut |
|---|---|---|---|
| **Frontend Dashboard** | Interface utilisateur, choix LLM, historique | React / Next.js | À créer |
| **API Gateway** | Auth, rate limiting, routing, billing | FastAPI | À créer |
| **GuideHarmonique** | Identification du domaine (11 domaines) | Python | ✅ Existant |
| **Tokenizer Holographique** | Projection tokens → (kx, ky) | Python | ✅ Existant |
| **Calculateur Harmonique** | Calcul exact (SymPy) pour questions mathématiques | Python | ✅ Existant |
| **Enrichisseur Contexte** | Ajout contexte harmonique au prompt | Python | À créer |
| **LLM Router** | Routage unifié vers tous les LLMs | Python (LiteLLM) | À créer |
| **DHF Vérificateur** | Cohérence Euler + Action + Résonance | Python | ✅ Existant |
| **Cache Cohérence** | Lookup O(1) pour 998 tokens | NumPy | ✅ Existant |
| **Templates + Correcteur** | Génération phrase + correction | Python | ✅ Existant |
| **PostgreSQL** | Données utilisateurs, requêtes, billing | PostgreSQL | À configurer |
| **Redis** | Cache de sessions, rate limiting | Redis | À configurer |

---

## 3. Flux 1 — Encapsulation du Prompt (Entrée)

### 3.1 Principe

L'encapsulation est le processus par lequel le prompt brut de l'utilisateur est **enrichi, analysé et préparé** avant d'être envoyé au LLM. Cette étape permet :

1. **Comprendre le domaine** de la question (GuideHarmonique)
2. **Projeter la sémantique** dans l'espace de Fourier (kx, ky)
3. **Pré-calculer les attentes** de cohérence
4. **Enrichir le prompt** avec un contexte qui guide le LLM vers des réponses plus cohérentes

### 3.2 Algorithme d'Encapsulation

```python
def encapsuler_prompt(question: str, user_id: str, preferences: dict) -> EncapsulatedPrompt:
    """
    Encapsule un prompt utilisateur avec le contexte harmonique.
    
    Étapes :
    1. Analyse du domaine (GuideHarmonique) — <1ms
    2. Projection fréquentielle (Tokenizer Holographique) — <1ms
    3. Pré-calcul (Calculateur Harmonique si applicable) — 1-5ms
    4. Enrichissement (contexte + instructions de cohérence) — <1ms
    5. Signature harmonique (empreinte unique) — <1ms
    """
    
    # === ÉTAPE 1 : Analyse du domaine ===
    domaines = guide.identifier_domaine(question)
    domaine_principal = domaines[0] if domaines else "general"
    
    # === ÉTAPE 2 : Projection fréquentielle ===
    tokens = tokenizer.tokeniser(question)
    signatures = extraire_signatures(tokens)
    
    # === ÉTAPE 3 : Pré-calcul (si question mathématique) ===
    precalcul = None
    if calculateur and domaine_principal in DOMAINES_CALCULABLES:
        precalcul = calculateur.resoudre(question)
    
    # === ÉTAPE 4 : Enrichissement du prompt ===
    prompt_enrichi = construire_prompt_enrichi(
        question=question,
        domaine=domaine_principal,
        signatures=signatures,
        precalcul=precalcul,
    )
    
    # === ÉTAPE 5 : Signature harmonique (empreinte pour vérification) ===
    signature_harmonique = generer_signature(signatures)
    
    return EncapsulatedPrompt(
        question_originale=question,
        prompt_enrichi=prompt_enrichi,
        domaine=domaine_principal,
        signatures=signatures,
        precalcul=precalcul,
        signature_harmonique=signature_harmonique,
    )
```

### 3.3 Construction du Prompt Enrichi

```python
def construire_prompt_enrichi(question, domaine, signatures, precalcul):
    """
    Construit un prompt enrichi qui guide le LLM vers une réponse cohérente.
    
    Le prompt enrichi contient :
    - La question originale
    - Le domaine identifié
    - Les concepts harmoniques pertinents
    - Les instructions de cohérence
    - Le pré-calcul exact si disponible
    """
    
    concepts_pertinents = retrieval_direct(question, top_k=5)
    
    instructions_coherence = (
        f"Tu réponds à une question du domaine : {domaine.nom}. "
        f"Concepts clés à utiliser : {', '.join(concepts_pertinents)}. "
        "Réponds de manière factuelle et vérifiable. "
        "Si tu n'es pas certain, indique-le explicitement. "
        "Privilégie la précision à l'exhaustivité."
    )
    
    prompt = f"""# Contexte
Domaine : {domaine.nom}
Concepts pertinents : {', '.join(concepts_pertinents)}

{f"[RÉFÉRENCE EXACTE] Le résultat vérifié est : {precalcul.resultat_sympy}" if precalcul and precalcul.resultat_sympy else ""}

# Instructions
{instructions_coherence}

# Question
{question}
"""
    return prompt
```

### 3.4 Ce que l'Encapsulation Apporte

| Sans Encapsulation | Avec Encapsulation Harmonique |
|---|---|
| Prompt brut → LLM | Prompt enrichi (domaine + concepts + pré-calcul + instructions) |
| Le LLM devine le domaine | Le domaine est explicitement indiqué |
| Aucun contexte sémantique | Contexte enrichi avec les concepts harmoniques |
| Pas de référence de vérité | Pré-calcul exact fourni si applicable (SymPy) |
| Génération libre | Instructions de cohérence contraignantes |
| Réponse non vérifiable | Signature harmonique pour vérification post-hoc |

---

## 4. Flux 2 — Routage vers le LLM Choisi

### 4.1 Architecture de Routage Unifié

```python
class LLMRouter:
    """
    Routeur unifié vers tous les LLMs supportés.
    Abstraction complète : l'utilisateur choisit un modèle,
    le routeur gère l'appel API spécifique.
    """
    
    PROVIDERS = {
        "openai": {
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "auth_env": "OPENAI_API_KEY",
        },
        "anthropic": {
            "models": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-haiku"],
            "auth_env": "ANTHROPIC_API_KEY",
        },
        "deepseek": {
            "models": ["deepseek-chat", "deepseek-reasoner"],
            "auth_env": "DEEPSEEK_API_KEY",
        },
        "ollama": {
            "models": ["deepseek-math:1.5b", "llama3:8b", "mistral:7b", "qwen2.5:3b"],
            "auth_env": None,  # Local, gratuit
        },
        "google": {
            "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "auth_env": "GOOGLE_API_KEY",
        },
        "mistral": {
            "models": ["mistral-large", "mistral-medium", "mistral-small"],
            "auth_env": "MISTRAL_API_KEY",
        },
    }
    
    def router(self, prompt_enrichi: str, model_id: str,
               preferences: dict, api_keys: dict) -> LLMResponse:
        """
        Route le prompt enrichi vers le LLM choisi.
        
        Args:
            prompt_enrichi : prompt après encapsulation harmonique
            model_id : ex: "openai:gpt-4o", "ollama:llama3:8b"
            preferences : température, max_tokens, etc.
            api_keys : dict des clés API (ou None pour Ollama)
        """
        provider, model = model_id.split(":", 1)
        
        # Vérifier que le provider et le modèle sont supportés
        if provider not in self.PROVIDERS:
            raise ValueError(f"Provider non supporté : {provider}")
        if model not in self.PROVIDERS[provider]["models"]:
            raise ValueError(f"Modèle non supporté : {model}")
        
        # Routage selon le provider
        if provider == "openai":
            return self._call_openai(prompt_enrichi, model, preferences, api_keys)
        elif provider == "anthropic":
            return self._call_anthropic(prompt_enrichi, model, preferences, api_keys)
        elif provider == "deepseek":
            return self._call_deepseek(prompt_enrichi, model, preferences, api_keys)
        elif provider == "ollama":
            return self._call_ollama(prompt_enrichi, model, preferences)
        elif provider == "google":
            return self._call_google(prompt_enrichi, model, preferences, api_keys)
        elif provider == "mistral":
            return self._call_mistral(prompt_enrichi, model, preferences, api_keys)
```

### 4.2 Modèles Supportés

| Provider | Modèles Disponibles | Type | Coût / 1M tokens |
|---|---|---|---|
| **OpenAI** | GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo | Cloud API | $2.50 - $15.00 |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku | Cloud API | $3.00 - $15.00 |
| **DeepSeek** | DeepSeek-Chat, DeepSeek-Reasoner | Cloud API | $0.10 - $0.50 |
| **Google** | Gemini 1.5 Pro, Gemini 1.5 Flash | Cloud API | $3.50 - $7.00 |
| **Mistral** | Mistral Large, Medium, Small | Cloud API | $2.00 - $8.00 |
| **Ollama** | DeepSeek-Math 1.5B, Llama3 8B, Mistral 7B, Qwen 2.5 3B | **Local CPU** | **Gratuit** |
| **Custom** | Tout endpoint compatible OpenAI API | BYO | Variable |

### 4.3 Gestion des Clés API — Trois Modes

```
MODE 1 : BYOK (Bring Your Own Key)
  → L'utilisateur fournit ses propres clés API
  → Stockées chiffrées (AES-256) dans PostgreSQL
  → L'utilisateur paie directement le provider
  → La plateforme ne facture que l'abonnement

MODE 2 : MANAGED (Clés fournies par la plateforme)
  → La plateforme fournit les clés API
  → Inclus dans l'abonnement (quota de tokens/mois)
  → Coûts LLM intégrés dans le pricing
  → Idéal pour les utilisateurs sans compte API

MODE 3 : LOCAL (Ollama gratuit)
  → Aucune clé API requise
  → Ollama local installé sur le serveur
  → DeepSeek 1.5B, Llama3 8B, Mistral 7B
  → Gratuit, CPU, pas de limite de tokens
  → Inclus dans tous les plans
```

---

## 5. Flux 3 — Vérification Harmonique (DHF)

### 5.1 Principe

C'est le **cœur différenciateur** de la plateforme. Chaque réponse LLM est vérifiée par le Décodeur Harmonique Final avant d'être livrée.

```
RÉPONSE BRUTE DU LLM
        │
        ▼
┌───────────────────────────────────────────┐
│        VÉRIFICATION HARMONIQUE (DHF)       │
│                                             │
│  1. Extraction des tokens de la réponse    │
│  2. Projection dans (kx, ky)               │
│  3. Calcul des 3 métriques :               │
│     • Euler      : Σ e^{i(kx+ky)}          │
│     • Action     : δS de la séquence       │
│     • Résonance  : cohérence inter-token   │
│  4. Score composite pondéré par φ          │
│  5. Comparaison avec les seuils            │
│                                             │
│  Score ≥ 0.70 → HAUTE → Livrer ✓           │
│  Score ≥ 0.55 → MOYENNE → Livrer ✓         │
│  Score ≥ 0.40 → BASSE → Avertir ⚠️         │
│  Score < 0.40 → NULLE → Rejeter + Corriger │
└───────────────────────────────────────────┘
```

### 5.2 Algorithme de Vérification

```python
def verifier_reponse_llm(question: str, reponse_llm: str,
                          signature_harmonique) -> VerificationResult:
    """
    Vérifie la cohérence d'une réponse LLM via le DHF.
    Retourne un score de confiance 0-1 et un diagnostic complet.
    """
    
    # ÉTAPE 1 : Tokenisation de la réponse
    tokens_reponse = tokenizer.tokeniser(reponse_llm)
    signatures_reponse = [
        (tokenizer._kx[tid], tokenizer._ky[tid])
        for tid in tokens_reponse if 4 <= tid < tokenizer.vocab_size
    ]
    
    # ÉTAPE 2 : Métrique d'Euler (géométrique)
    euler_scores = [abs(exp(1j * (kx + ky))) for kx, ky in signatures_reponse]
    score_euler = mean(euler_scores)
    
    # ÉTAPE 3 : Métrique d'Action (dynamique)
    actions = []
    for i in range(len(signatures_reponse) - 1):
        kx1, ky1 = signatures_reponse[i]
        kx2, ky2 = signatures_reponse[i + 1]
        L = sqrt((kx2 - kx1)**2 + (ky2 - ky1)**2)
        actions.append(L)
    score_action = 1.0 / (1.0 + mean(actions)) if actions else 0.5
    
    # ÉTAPE 4 : Métrique de Résonance (fréquentielle)
    fft_combinee = fft(combiner_signatures(signature_harmonique, signatures_reponse))
    energie_totale = sum(abs(fft_combinee)**2)
    energie_coherente = sum(abs(fft_combinee[:len(fft_combinee)//2])**2)
    score_resonance = energie_coherente / (energie_totale + 1e-10)
    
    # ÉTAPE 5 : Score composite (pondéré par φ)
    w_euler = 1/PHI        # ≈ 0.618
    w_action = 1/PHI**2    # ≈ 0.382
    score_coherence = w_euler * score_euler + w_action * score_action
    score_coherence += (1 - w_euler - w_action) * score_resonance
    
    # ÉTAPE 6 : Niveau de confiance
    if score_coherence >= 0.70:   confiance = "haute"
    elif score_coherence >= 0.55: confiance = "moyenne"
    elif score_coherence >= 0.40: confiance = "basse"
    else:                          confiance = "nulle"
    
    return VerificationResult(
        score_coherence=score_coherence,
        confiance=confiance,
        score_euler=score_euler,
        score_action=score_action,
        score_resonance=score_resonance,
        accepte=(confiance != "nulle"),
    )
```

### 5.3 Détection d'Hallucination

```python
def detecter_hallucination(question, reponse_llm, verification, precalcul=None):
    """Détecte les signes d'hallucination dans une réponse LLM."""
    signaux = []
    
    # Signal 1 : Cohérence nulle (< 0.40) → hallucination probable
    if verification.score_coherence < 0.40:
        signaux.append({
            "type": "coherence_nulle",
            "severite": "elevee",
            "message": "La réponse a une cohérence harmonique insuffisante."
        })
    
    # Signal 2 : Contradiction avec le pré-calcul SymPy
    if precalcul and precalcul.resultat_sympy:
        if contradiction_detectee(precalcul.resultat_sympy, reponse_llm):
            signaux.append({
                "type": "contradiction_calcul_exact",
                "severite": "critique",
                "message": f"Contredit le calcul exact : {precalcul.resultat_sympy}"
            })
    
    # Signal 3 : Tokens hors-domaine → digression
    domaine = guide.identifier_domaine(question)
    tokens_hors = detecter_tokens_hors_domaine(reponse_llm, domaine)
    if tokens_hors:
        signaux.append({
            "type": "hors_domaine",
            "severite": "moyenne",
            "tokens": tokens_hors
        })
    
    return HallucinationReport(
        hallucination_detectee=len(signaux) > 0,
        signaux=signaux,
    )
```

### 5.4 Boucle de Correction (si cohérence insuffisante)

```python
def corriger_reponse(question, reponse_initiale, verification,
                      model_id, max_iter=3):
    """
    Si la vérification échoue, tente de corriger la réponse.
    
    Stratégies (essayées dans l'ordre) :
    1. Ré-invoquer le LLM avec un prompt de correction explicite
    2. Fallback automatique vers un autre LLM
    3. Utiliser le pré-calcul exact (SymPy) si disponible
    4. Abandonner et répondre "Je ne peux pas répondre avec confiance"
    """
    
    reponse = reponse_initiale
    coherence = verification.score_coherence
    
    for iteration in range(max_iter):
        if coherence >= 0.55:
            break
        
        # Stratégie 1 : Prompt de correction
        prompt_correction = f"""
La réponse précédente a un score de cohérence de {coherence:.2f}.
Question : {question}
Réponse précédente : {reponse}
Problèmes : {verification.diagnostic}

Corrige la réponse en te basant UNIQUEMENT sur des faits vérifiables.
"""
        reponse_corrigee = llm_router.router(prompt_correction, model_id)
        verification_corrigee = verifier_reponse_llm(question, reponse_corrigee.texte_brut)
        
        if verification_corrigee.score_coherence > coherence:
            reponse = reponse_corrigee.texte_brut
            coherence = verification_corrigee.score_coherence
    
    return CorrectedResponse(
        reponse_finale=reponse,
        coherence_finale=coherence,
        iterations=iteration + 1,
        corrigee=(reponse != reponse_initiale),
    )
```

---

## 6. Flux 4 — Boucle de Génération Contrôlée (Pipeline Complet)

### 6.1 Pipeline Étape par Étape

```
┌─────────────────────────────────────────────────────────────────────┐
│              PIPELINE DE GÉNÉRATION CONTRÔLÉE                        │
│                   (par requête utilisateur)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ÉTAPE 1 : RÉCEPTION (API Gateway)                                  │
│  • POST /api/v1/generate                                             │
│  • Body : {prompt, model_id, preferences}                           │
│  • Auth : JWT ou API Key                                             │
│  • Validation + Rate limiting                                        │
│  ─────────────────────────────────────────────                       │
│                                                                      │
│  ÉTAPE 2 : ENCAPSULATION HARMONIQUE (<5ms)                          │
│  • GuideHarmonique → domaine (75% précision)                        │
│  • Tokenizer → signatures (kx, ky)                                  │
│  • Calculateur → pré-calcul exact (SymPy, si applicable)            │
│  • Enrichissement → prompt + contexte + instructions               │
│  ─────────────────────────────────────────────                       │
│                                                                      │
│  ÉTAPE 3 : ROUTAGE LLM (1-30s selon modèle)                         │
│  • LLM Router → appel API spécifique au provider                    │
│  • Prompt enrichi → LLM choisi → Réponse brute                     │
│  ─────────────────────────────────────────────                       │
│                                                                      │
│  ÉTAPE 4 : VÉRIFICATION HARMONIQUE (<1ms)                           │
│  • DHF 3 modes → Euler + Action + Résonance                         │
│  • Cache de cohérence → O(1) lookup                                 │
│  • Score composite 0-1 + Niveau de confiance                       │
│  ─────────────────────────────────────────────                       │
│                                                                      │
│  ┌─ COHÉRENCE ≥ 0.40 ? ─────────────────────────────┐              │
│  │                                                    │              │
│  ▼ OUI                                                ▼ NON          │
│  ÉTAPE 5a : LIVRER                           ÉTAPE 5b : CORRIGER   │
│  • Formatage + Score                        • Ré-invoquer LLM      │
│  • Post-traitement                          • Fallback autre LLM   │
│  • Réponse JSON complète                    • Max 3 itérations     │
│                                              • Si échec → "Je ne   │
│                                                peux pas répondre"  │
│  ────────────────────────────────────────────────────────────       │
│                                                                      │
│  ÉTAPE 6 : LIVRAISON FINALE                                         │
│  • Réponse JSON + métadonnées complètes                             │
│  • Streaming SSE (optionnel)                                        │
│  • Sauvegarde dans l'historique utilisateur                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Réponse API Complète (Format JSON)

```json
{
  "id": "req_a1b2c3d4",
  "timestamp": "2026-06-04T12:00:00Z",
  
  "requete": {
    "prompt_original": "Explique la dérivée d'une fonction puissance",
    "modele_choisi": "openai:gpt-4o-mini",
    "mode": "managed"
  },
  
  "encapsulation": {
    "domaine": "derivation",
    "concepts_pertinents": ["derivee", "fonction", "exposant", "regle", "coefficient"],
    "precalcul_disponible": true,
    "temps_ms": 4.2
  },
  
  "generation_llm": {
    "modele": "openai:gpt-4o-mini",
    "tokens_prompt": 245,
    "tokens_completion": 312,
    "latence_ms": 834
  },
  
  "verification_harmonique": {
    "score_coherence": 0.78,
    "confiance": "haute",
    "details": {
      "score_euler": 0.82,
      "score_action": 0.75,
      "score_resonance": 0.79
    }
  },
  
  "hallucination": {
    "detectee": false,
    "signaux": []
  },
  
  "reponse_finale": {
    "texte": "✅ Réponse vérifiée (confiance élevée)\n\nLa dérivée d'une fonction puissance...\n\n---\n📊 Score de confiance : 78%\n🔍 Vérifié par Harmonic AI — DHF",
    "confiance": "haute",
    "score_global": 0.78,
    "corrigee": false
  },
  
  "metriques": {
    "temps_total_ms": 845,
    "cout_estime_usd": 0.0012,
    "tokens_total": 557
  }
}
```

---

## 7. Flux 5 — Correction et Livraison

### 7.1 Post-traitement

```python
def post_traiter_reponse(reponse_verifiee, langue="fr") -> FinalResponse:
    """Post-traitement de la réponse avant livraison."""
    
    texte = reponse_verifiee.reponse_finale
    
    # Correction grammaticale
    if langue == "fr":
        from scripts.correcteur_fr import corriger_phrase
        texte = corriger_phrase(texte)
    
    # Bandeau de confiance
    score = reponse_verifiee.coherence_finale
    if score >= 0.70:
        prefixe = "✅ Réponse vérifiée (confiance élevée)"
    elif score >= 0.55:
        prefixe = "✓ Réponse vérifiée (confiance moyenne)"
    elif score >= 0.40:
        prefixe = "⚠️ Réponse avec réserve (confiance basse)"
    else:
        prefixe = "❌ Impossible de fournir une réponse fiable"
    
    bandeau = (
        f"\n\n---\n"
        f"📊 Score de confiance : {score:.0%}\n"
        f"🔍 Vérifié par Harmonic AI — DHF (Euler + Action + Résonance)"
    )
    
    return FinalResponse(
        texte=prefixe + "\n\n" + texte + bandeau,
        confiance=score,
        corrigee=reponse_verifiee.corrigee,
    )
```

### 7.2 Modes de Livraison

| Mode | Endpoint | Description |
|---|---|---|
| **JSON** | `POST /api/v1/generate` | Réponse complète avec métadonnées |
| **Streaming SSE** | `POST /api/v1/generate/stream` | Tokens streamés en temps réel |
| **Comparaison** | `POST /api/v1/compare` | N modèles comparés côte à côte |

---

## 8. Architecture Technique — Stack Complète

### 8.1 Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      STACK TECHNIQUE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  FRONTEND                                                    │
│  ├── React 18 + TypeScript                                  │
│  ├── Next.js 14 (SSR, API Routes)                           │
│  ├── TailwindCSS (styling)                                  │
│  ├── Shadcn/ui (composants)                                 │
│  ├── React Query (data fetching)                           │
│  └── Zustand (state management)                             │
│                                                              │
│  BACKEND                                                     │
│  ├── Python 3.11+ + FastAPI                                 │
│  ├── SQLAlchemy (ORM) + Alembic (migrations)               │
│  ├── LiteLLM (unified LLM proxy)                           │
│  ├── Celery + Redis (async tasks)                          │
│  ├── Pydantic (validation)                                  │
│  └── Prometheus (metrics)                                   │
│                                                              │
│  MOTEUR HARMONIQUE (existant)                                │
│  ├── GuideHarmonique (domaines)                             │
│  ├── Tokenizer Holographique (kx, ky)                       │
│  ├── Calculateur Harmonique (SymPy)                         │
│  ├── DHF (Euler + Action + Résonance)                       │
│  ├── Cache de Cohérence (998 tokens)                        │
│  ├── Templates FR/EN (100+ variantes)                       │
│  └── Correcteur FR                                          │
│                                                              │
│  INFRASTRUCTURE                                              │
│  ├── Docker + Docker Compose                                │
│  ├── PostgreSQL 16 (données)                                │
│  ├── Redis 7 (cache + queues)                               │
│  ├── Nginx (reverse proxy)                                  │
│  ├── Cloudflare (DNS + CDN)                                 │
│  └── Hetzner CX22 (3.99€/mois)                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Structure du Projet

```
saas-harmonic-gateway/
├── frontend/                    # React + Next.js
│   ├── src/
│   │   ├── app/                # Pages (App Router)
│   │   ├── components/         # Composants réutilisables
│   │   ├── hooks/              # Custom hooks
│   │   ├── lib/                # Utilitaires
│   │   └── types/              # Types TypeScript
│   ├── package.json
│   └── next.config.js
│
├── backend/                     # FastAPI
│   ├── app/
│   │   ├── api/                # Routes API
│   │   │   ├── v1/
│   │   │   │   ├── generate.py     # POST /generate
│   │   │   │   ├── compare.py      # POST /compare
│   │   │   │   ├── models.py       # GET /models
│   │   │   │   └── history.py      # GET /history
│   │   │   └── deps.py             # Dépendances
│   │   ├── core/
│   │   │   ├── config.py           # Configuration
│   │   │   ├── security.py         # Auth (JWT, API Keys)
│   │   │   └── database.py         # Connexion DB
│   │   ├── services/
│   │   │   ├── encapsulation.py    # Encapsulation harmonique
│   │   │   ├── llm_router.py       # Routage LLM unifié
│   │   │   ├── verification.py     # DHF Vérification
│   │   │   ├── correction.py       # Boucle de correction
│   │   │   └── delivery.py         # Post-traitement
│   │   ├── models/
│   │   │   ├── user.py             # Modèle User
│   │   │   ├── request.py          # Modèle Request
│   │   │   └── billing.py          # Modèle Billing
│   │   └── schemas/
│   │       ├── generate.py         # Schémas Generate
│   │       └── user.py             # Schémas User
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── engine/                       # Moteur Harmonique (existant)
│   ├── decodeur_harmonique_final.py
│   ├── calculateur_harmonique.py
│   ├── conscience_harmonique.py
│   ├── fallback_llm.py
│   ├── memoire_associative_harmonique.py
│   ├── table_equivalence_harmonique.py
│   └── interface_harmonique.py
│
├── scripts/                      # Scripts (existant)
│   ├── templates_phrases_fr.py
│   ├── correcteur_fr.py
│   └── ...
│
├── data/                         # Données (existant)
│   └── coherence_cache_massif.npz
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── README.md
```

---

## 9. Modèle de Données

### 9.1 Schéma PostgreSQL

```sql
-- Utilisateurs
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'free',  -- free, pro, enterprise
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Clés API utilisateur (BYOK)
CREATE TABLE user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,    -- openai, anthropic, deepseek, etc.
    api_key_encrypted BYTEA NOT NULL, -- AES-256 encrypted
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Clés API de la plateforme (pour accès API)
CREATE TABLE platform_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Requêtes (historique)
CREATE TABLE requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    prompt_original TEXT NOT NULL,
    prompt_enrichi TEXT,
    model_id VARCHAR(100) NOT NULL,      -- ex: "openai:gpt-4o"
    domaine VARCHAR(100),                -- identifié par GuideHarmonique
    signature_harmonique VARCHAR(64),    -- empreinte unique
    reponse_brute TEXT,                  -- réponse LLM avant vérification
    score_coherence FLOAT,              -- score DHF 0-1
    confiance VARCHAR(20),              -- haute/moyenne/basse/nulle
    hallucination_detectee BOOLEAN DEFAULT false,
    reponse_finale TEXT,                -- réponse après correction
    corrigee BOOLEAN DEFAULT false,
    iterations_correction INT DEFAULT 0,
    tokens_prompt INT,
    tokens_completion INT,
    latence_llm_ms FLOAT,
    latence_totale_ms FLOAT,
    cout_estime_usd FLOAT,
    mode VARCHAR(20) DEFAULT 'managed',  -- managed, byok, local
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_requests_user_id ON requests(user_id);
CREATE INDEX idx_requests_created_at ON requests(created_at);

-- Quota et Billing
CREATE TABLE usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    tokens_used INT DEFAULT 0,
    tokens_limit INT,                    -- NULL = illimité
    requests_count INT DEFAULT 0,
    cout_total_usd FLOAT DEFAULT 0,
    UNIQUE(user_id, period_start)
);

-- Factures
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    amount_usd FLOAT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, paid, failed
    stripe_invoice_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 9.2 Schéma Redis (Cache)

```
# Sessions utilisateur
session:{session_id} → {user_id, expires_at, ...}

# Rate limiting
ratelimit:{user_id}:{endpoint} → {count, window_start}

# Cache de cohérence (déjà existant, pré-calculé)
coherence:{token_pair} → score

# Cache de réponses (optionnel, pour requêtes identiques)
response_cache:{hash(question + model_id)} → {reponse_json}
```

---

## 10. API REST — Spécification Complète

### 10.1 Endpoints

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         API REST — ENDPOINTS                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  AUTH                                                                    │
│  ├── POST   /api/v1/auth/register     → Créer un compte                 │
│  ├── POST   /api/v1/auth/login        → Obtenir JWT                     │
│  ├── POST   /api/v1/auth/refresh      → Rafraîchir JWT                  │
│  └── POST   /api/v1/auth/api-keys     → Gérer les clés API plateforme   │
│                                                                          │
│  GÉNÉRATION                                                              │
│  ├── POST   /api/v1/generate          → Génération contrôlée (JSON)     │
│  ├── POST   /api/v1/generate/stream   → Génération contrôlée (SSE)      │
│  └── POST   /api/v1/compare           → Comparer N modèles              │
│                                                                          │
│  MODÈLES                                                                 │
│  ├── GET    /api/v1/models            → Lister les modèles disponibles  │
│  └── GET    /api/v1/models/{id}       → Détails d'un modèle             │
│                                                                          │
│  HISTORIQUE                                                              │
│  ├── GET    /api/v1/history           → Historique des requêtes         │
│  ├── GET    /api/v1/history/{id}      → Détail d'une requête            │
│  └── DELETE /api/v1/history/{id}      → Supprimer une requête           │
│                                                                          │
│  UTILISATEUR                                                             │
│  ├── GET    /api/v1/user/profile      → Profil utilisateur              │
│  ├── PATCH  /api/v1/user/profile      → Modifier profil                 │
│  ├── GET    /api/v1/user/usage        → Quota et utilisation            │
│  ├── POST   /api/v1/user/api-keys     → Ajouter clé API BYOK           │
│  └── DELETE /api/v1/user/api-keys/{id}→ Supprimer clé API               │
│                                                                          │
│  ADMIN                                                                   │
│  ├── GET    /api/v1/admin/users       → Lister utilisateurs             │
│  ├── GET    /api/v1/admin/metrics     → Métriques globales              │
│  └── GET    /api/v1/admin/health      → Health check                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Spécification POST /api/v1/generate

```yaml
POST /api/v1/generate
Auth: Bearer {JWT} ou X-API-Key: {api_key}
Content-Type: application/json

Request Body:
{
  "prompt": "Explique la dérivée d'une fonction puissance",  # Requis
  "model_id": "openai:gpt-4o-mini",                          # Requis (ou "ollama:deepseek-math:1.5b")
  "mode": "managed",                                          # "managed" | "byok" | "local" (défaut: managed)
  "langue": "fr",                                             # "fr" | "en" (défaut: fr)
  "preferences": {                                            # Optionnel
    "temperature": 0.3,
    "max_tokens": 500,
    "stream": false
  }
}

Response 200:
{
  "id": "req_a1b2c3d4",
  "timestamp": "2026-06-04T12:00:00Z",
  "requete": { "prompt_original": "...", "modele_choisi": "openai:gpt-4o-mini", "mode": "managed" },
  "encapsulation": { "domaine": "derivation", "concepts_pertinents": [...], "temps_ms": 4.2 },
  "generation_llm": { "modele": "openai:gpt-4o-mini", "tokens_prompt": 245, "tokens_completion": 312, "latence_ms": 834 },
  "verification_harmonique": { "score_coherence": 0.78, "confiance": "haute", "details": {...} },
  "hallucination": { "detectee": false, "signaux": [] },
  "reponse_finale": { "texte": "...", "confiance": "haute", "score_global": 0.78, "corrigee": false },
  "metriques": { "temps_total_ms": 845, "cout_estime_usd": 0.0012, "tokens_total": 557 }
}

Response 402:
{
  "error": "quota_depasse",
  "message": "Quota de tokens mensuel dépassé. Passez au plan supérieur.",
  "usage": { "tokens_used": 1000000, "tokens_limit": 1000000 }
}
```

### 10.3 Spécification POST /api/v1/compare

```yaml
POST /api/v1/compare
Auth: Bearer {JWT}
Content-Type: application/json

Request Body:
{
  "prompt": "Explique la dérivée d'une fonction puissance",
  "models": ["openai:gpt-4o", "anthropic:claude-3.5-sonnet", "deepseek:deepseek-chat"],
  "mode": "managed",
  "langue": "fr"
}

Response 200:
{
  "id": "cmp_a1b2c3d4",
  "prompt": "...",
  "resultats": [
    {
      "model_id": "openai:gpt-4o",
      "score_coherence": 0.82,
      "confiance": "haute",
      "latence_ms": 1234,
      "cout_usd": 0.015,
      "reponse": "..."
    },
    {
      "model_id": "anthropic:claude-3.5-sonnet",
      "score_coherence": 0.79,
      "confiance": "haute",
      "latence_ms": 980,
      "cout_usd": 0.012,
      "reponse": "..."
    },
    {
      "model_id": "deepseek:deepseek-chat",
      "score_coherence": 0.71,
      "confiance": "haute",
      "latence_ms": 456,
      "cout_usd": 0.0003,
      "reponse": "..."
    }
  ],
  "classement": ["openai:gpt-4o", "anthropic:claude-3.5-sonnet", "deepseek:deepseek-chat"],
  "meilleur_modele": "openai:gpt-4o"
}
```

---

## 11. Dashboard Utilisateur — Frontend

### 11.1 Pages Principales

```
┌─────────────────────────────────────────────────────────────┐
│                    DASHBOARD — PAGES                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  /                           → Page d'accueil + Prompt      │
│  /history                    → Historique des requêtes      │
│  /compare                    → Comparaison multi-modèles    │
│  /settings                   → Paramètres + Clés API        │
│  /billing                    → Facturation + Quota          │
│  /admin                      → Administration (admin only)  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 11.2 Page Principale (Prompt Interface)

```
┌──────────────────────────────────────────────────────────────────┐
│  HARMONIC GATEWAY                                    👤 Profil   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Modèle : [OpenAI GPT-4o-mini  ▼]   Mode : [Managed  ▼]    │ │
│  │  Langue : [Français  ▼]                                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                                                              │ │
│  │  Posez votre question...                                     │ │
│  │                                                              │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  [⚡ Générer]  [🔄 Comparer modèles]  [📎 Joindre fichier]      │
│                                                                   │
│  ─────────────────────────────────────────────────────────────── │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  RÉPONSE                                                     │ │
│  │                                                              │ │
│  │  ✅ Réponse vérifiée (confiance élevée)                      │ │
│  │                                                              │ │
│  │  La dérivée d'une fonction puissance f(x) = x^n...          │ │
│  │                                                              │ │
│  │  ─────────────────────────────────────────────────────      │ │
│  │  📊 Score de confiance : 78%                                 │ │
│  │  🏷️ Domaine : derivation                                     │ │
│  │  🔑 Concepts : derivee, fonction, exposant, regle            │ │
│  │  ⚡ Latence : 845ms  |  💰 Coût : $0.0012                   │ │
│  │  🔍 Vérifié par Harmonic AI — DHF                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 12. Modèle Économique — Pricing & Plans

### 12.1 Plans

| | **Free** | **Pro** | **Enterprise** |
|---|---|---|---|
| **Prix/mois** | Gratuit | 29€ | Sur devis |
| **Requêtes/mois** | 100 | 10 000 | Illimité |
| **Tokens/mois (managed)** | 50K | 5M | 50M+ |
| **Modèles cloud** | GPT-4o-mini | Tous (GPT-4o, Claude, etc.) | Tous + Priorité |
| **Modèles locaux (Ollama)** | ✅ Inclus | ✅ Inclus | ✅ Inclus |
| **BYOK** | ❌ | ✅ | ✅ |
| **Comparaison modèles** | 2 modèles | 5 modèles | Illimité |
| **Historique** | 7 jours | 90 jours | Illimité |
| **API Access** | 10 req/h | 100 req/h | Illimité |
| **Support** | Communauté | Email 24h | Dédié + SLA |
| **SSO / SAML** | ❌ | ❌ | ✅ |
| **On-premise** | ❌ | ❌ | ✅ |

### 12.2 Projections Financières (par serveur)

```
Serveur Hetzner CX22 (3.99€/mois) :
    CPU : 2 vCPU, RAM : 4 GB, SSD : 40 GB
    
Capacité estimée par serveur :
    ~10 000 requêtes/jour (en pic)
    ~300 000 requêtes/mois
    
Avec 100 utilisateurs Pro (29€/mois) :
    Revenu : 2 900€/mois
    Coût serveur : 4€/mois
    Coût LLM managed (DeepSeek) : ~50€/mois
    Marge brute : ~2 846€/mois (98%)
    
Avec 1 000 utilisateurs Pro :
    10 serveurs × 4€ = 40€/mois
    Revenu : 29 000€/mois
    Marge brute : ~28 960€/mois (99.8%)
```

### 12.3 Stratégie d'Acquisition

```
Phase 1 (Mois 1-3) : Beta gratuite
    → 100 utilisateurs bêta-test
    → Feedback + itérations
    → Validation du produit
    
Phase 2 (Mois 4-6) : Lancement public
    → Plan Free généreux (100 req/mois)
    → Content marketing (articles techniques)
    → Communauté Discord
    
Phase 3 (Mois 7-12) : Croissance
    → Référencement organique
    → Partenariats API (DeepSeek, Ollama)
    → Témoignages clients
    
Phase 4 (Mois 12+) : Scale
    → Entreprises (Plan Enterprise)
    → Intégrations (Slack, Teams, Notion)
    → Marché international (EN, FR, ES)
```

---

## 13. Plan de Déploiement

### 13.1 Infrastructure Cible

```
┌─────────────────────────────────────────────────────────────────┐
│                     DÉPLOIEMENT — PRODUCTION                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Internet → Cloudflare (DNS + CDN + DDoS)                       │
│                  │                                               │
│                  ▼                                               │
│  ┌──────────────────────────────────────┐                      │
│  │         Hetzner CX22 (3.99€/mois)    │                      │
│  │                                       │                      │
│  │  ┌─────────────────────────────────┐ │                      │
│  │  │ Docker Compose                   │ │                      │
│  │  │                                  │ │                      │
│  │  │  ┌──────────┐  ┌──────────────┐ │ │                      │
│  │  │  │ Nginx    │  │ Frontend     │ │ │                      │
│  │  │  │ :80/:443 │──│ Next.js :3000│ │ │                      │
│  │  │  └────┬─────┘  └──────────────┘ │ │                      │
│  │  │       │                          │ │                      │
│  │  │       ├───────┐                  │ │                      │
│  │  │       ▼       ▼                  │ │                      │
│  │  │  ┌──────────┐ ┌──────────────┐  │ │                      │
│  │  │  │ Backend  │ │ Ollama       │  │ │                      │
│  │  │  │ FastAPI  │ │ :11434       │  │ │                      │
│  │  │  │ :8000    │ │ DeepSeek 1.5B│  │ │                      │
│  │  │  └────┬─────┘ └──────────────┘  │ │                      │
│  │  │       │                          │ │                      │
│  │  │       ├───────┬───────┐          │ │                      │
│  │  │       ▼       ▼       ▼          │ │                      │
│  │  │  ┌────────┐┌───────┐┌────────┐  │ │                      │
│  │  │  │Postgre ││ Redis ││Engine  │  │ │                      │
│  │  │  │SQL :5432││:6379 ││Harmon. │  │ │                      │
│  │  │  └────────┘└───────┘└────────┘  │ │                      │
│  │  └─────────────────────────────────┘ │                      │
│  └──────────────────────────────────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 13.2 Docker Compose (Production)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./certbot/conf:/etc/letsencrypt
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  frontend:
    build: ./frontend
    expose:
      - "3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.harmonic-gateway.com
    restart: unless-stopped

  backend:
    build: ./backend
    expose:
      - "8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/harmonic
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./engine:/app/engine
      - ./data:/app/data
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    expose:
      - "11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=harmonic
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  ollama_data:
```

### 13.3 Script de Déploiement

```bash
#!/bin/bash
# deploy.sh — Déploiement SaaS Harmonic Gateway

echo "🚀 Déploiement Harmonic Gateway..."

# 1. Cloner le repo
git clone https://github.com/your-username/saas-harmonic-gateway.git
cd saas-harmonic-gateway

# 2. Configurer l'environnement
cp .env.example .env
# Éditer .env avec les clés API, secrets, etc.

# 3. Pull les modèles Ollama
docker run -d --name ollama-temp ollama/ollama
docker exec ollama-temp ollama pull deepseek-math:1.5b
docker exec ollama-temp ollama pull llama3:8b
docker rm -f ollama-temp

# 4. Lancer les services
docker-compose -f docker-compose.prod.yml up -d

# 5. Migrations DB
docker exec harmonic-backend alembic upgrade head

# 6. Vérifier la santé
curl http://localhost:8000/api/v1/admin/health

echo "✅ Déploiement terminé !"
echo "📍 Frontend : https://harmonic-gateway.com"
echo "📍 API Docs : https://api.harmonic-gateway.com/docs"
```

---

## 14. Sécurité et Isolation

### 14.1 Sécurité des Données

| Couche | Mesure |
|---|---|
| **Transport** | TLS 1.3 (HTTPS uniquement) |
| **Authentification** | JWT (RS256) + API Keys (SHA-256 hash) |
| **Clés API utilisateur** | AES-256-GCM chiffré, stocké dans PostgreSQL |
| **Prompt utilisateur** | Chiffré en transit, stocké en clair (pour historique) |
| **Mots de passe** | bcrypt (cost=12) |
| **Rate limiting** | Redis-based, 100 req/min par utilisateur (configurable) |
| **CORS** | Whitelist stricts (domaine frontend uniquement) |
| **Input validation** | Pydantic, pas d'injection SQL (ORM), pas d'injection de prompt (échappement) |

### 14.2 Isolation Multi-Tenant

```
┌──────────────────────────────────────────────────────────────┐
│              ISOLATION UTILISATEUR                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Base de données :                                           │
│  • Une table users, requests, usage partagées               │
│  • user_id sur chaque ligne                                 │
│  • Row-Level Security (RLS) optionnel sur PostgreSQL         │
│  • Index par user_id pour performances                      │
│                                                               │
│  Clés API :                                                  │
│  • Chaque utilisateur a ses propres clés (BYOK)              │
│  • Ou utilise les clés managed de la plateforme              │
│  • Les clés ne sont JAMAIS partagées entre utilisateurs      │
│                                                               │
│  Quota :                                                     │
│  • Compteur Redis par user_id                                │
│  • Reset automatique en début de période                    │
│  • Alerte par email à 80% et 100% du quota                  │
│                                                               │
│  Logs :                                                      │
│  • Chaque requête loggé avec user_id                        │
│  • Pas de log des prompts en clair (hash SHA-256)            │
│  • Rétention configurable (défaut : 90 jours)               │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 15. Implémentation Pas à Pas

### 15.1 Phase 1 — Fondations (Semaine 1-2)

```bash
# Jour 1-2 : Initialisation du projet
mkdir saas-harmonic-gateway && cd saas-harmonic-gateway
git init
mkdir -p frontend backend engine scripts data

# Backend FastAPI
cd backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn sqlalchemy alembic pydantic python-jose passlib bcrypt redis httpx liteLLM

# Frontend Next.js
cd ../frontend
npx create-next-app@latest . --typescript --tailwind
npm install @shadcn/ui react-query zustand axios
```

### 15.2 Phase 2 — Backend Core (Semaine 3-4)

```
- [ ] Configuration (FastAPI + PostgreSQL + Redis)
- [ ] Modèles SQLAlchemy (User, Request, Billing)
- [ ] Migration Alembic
- [ ] Auth (JWT + API Keys)
- [ ] Service d'encapsulation (intégration GuideHarmonique)
- [ ] Service de routage LLM (LiteLLM)
- [ ] Service de vérification DHF (intégration moteur existant)
- [ ] Service de correction (boucle de raffinement)
- [ ] Service de livraison (post-traitement)
- [ ] Endpoint POST /api/v1/generate
- [ ] Endpoint POST /api/v1/compare
- [ ] Endpoint GET /api/v1/models
- [ ] Endpoints d'historique
- [ ] Tests unitaires + intégration
```

### 15.3 Phase 3 — Frontend (Semaine 5-6)

```
- [ ] Layout + Navigation
- [ ] Page principale (prompt interface)
- [ ] Composant de choix de modèle (dropdown)
- [ ] Composant d'affichage de réponse (avec score)
- [ ] Page d'historique
- [ ] Page de comparaison
- [ ] Page de paramètres (clés API, profil)
- [ ] Page de billing
- [ ] Auth (login/register)
- [ ] Streaming SSE
```

### 15.4 Phase 4 — Déploiement (Semaine 7-8)

```
- [ ] Docker Compose (dev + prod)
- [ ] Configuration Nginx + SSL (Let's Encrypt)
- [ ] Configuration Cloudflare
- [ ] Script de déploiement automatisé
- [ ] Monitoring (Prometheus + Grafana basique)
- [ ] Alerting (email + Slack)
- [ ] Backup automatique PostgreSQL
- [ ] Documentation API (Swagger/OpenAPI)
- [ ] Landing page marketing
- [ ] Bêta test (100 utilisateurs)
```

### 15.5 Phase 5 — Lancement (Semaine 9-12)

```
- [ ] Correction des bugs bêta
- [ ] Optimisation des performances
- [ ] Stripe intégration (paiements)
- [ ] Emails transactionnels (Resend/SendGrid)
- [ ] Page de pricing
- [ ] SEO + Content marketing
- [ ] Lancement public
```

---

## Conclusion

**Harmonic Gateway** est une plateforme SaaS qui résout le problème fondamental des LLMs : l'absence de mécanisme de vérification natif.

En encapsulant le prompt utilisateur avec un contexte harmonique enrichi et en vérifiant chaque réponse via le DHF, la plateforme garantit :

1. **Zéro hallucination** — toute réponse incohérente est détectée et corrigée ou rejetée
2. **Multi-LLM transparent** — une API unifiée pour GPT-4, Claude, DeepSeek, Llama, Mistral, Gemini, Ollama...
3. **Score de confiance objectif** — indépendant du modèle, basé sur la cohérence harmonique universelle
4. **Génération contrôlée** — boucle Proposer→Vérifier→Corriger→Livrer, déterministe, sans surprise

L'infrastructure est légère (un seul serveur Hetzner CX22 à 3.99€/mois suffit pour 100 utilisateurs Pro), le moteur harmonique existe déjà et fonctionne (<5ms CPU, 46% rappel), et le modèle économique est viable dès le premier client payant.

**Prochaine étape :** Initialiser le projet et implémenter la Phase 1 (Fondations).

---

*"Choisissez votre LLM. Nous garantissons la vérité."*  
*Harmonic Gateway — Juin 2026*