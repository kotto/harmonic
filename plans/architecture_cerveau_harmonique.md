# Plan d'Architecture — Cerveau Harmonique SOPC

## Vue d'ensemble

```mermaid
graph TB
    subgraph "cerveau_harmonique_v1/"
        direction TB
        
        subgraph "engine/ — Moteur Breveté"
            ABC[abc_kernel.py<br/>Noyau ABC]
            SOPC[sopc_core.py<br/>SOPC complet]
            SIG[signatures_9d.py<br/>Signatures 9D]
            HE[harmonic_engine.py<br/>Résonances cognitives]
            HC[hologram_connector.py<br/>Connecteur hologramme]
            LLM[llm/<br/>Routeur multi-providers]
            SEM[semantic/<br/>Embeddings 9D+512D+RAG]
            MEM[memory/<br/>Mémoire ABC]
            MM[multimodal/<br/>Analyse image/audio/vidéo]
            API[api/<br/>API REST FastAPI]
        end
        
        subgraph "core/ — Infrastructure"
            ORCH[orchestrator.py<br/>Boucle de contrôle]
            ROUT[router.py<br/>Routeur hologramme vs LLM]
            HM[holographic_memory.py<br/>Interface buffer 32 Ko]
            LLMF[llm_fallback.py<br/>SmolLM2 GGUF CPU]
            DET[determinism.py<br/>Ancrage anti-hallucination]
            DS[data_stream.py<br/>Streaming une passe]
            MET[metrics.py<br/>Métriques optionnelles]
            MOD[modalities/<br/>texte + image/audio/video]
            PROP[proprietary/operators.py<br/>FFT + ABC]
        end
        
        SCR[scripts/<br/>CLI: train, chat, evaluate]
        TST[tests/<br/>pytest]
        CFG[config.yaml]
    end
    
    %% Relations internes engine/
    ABC --> SOPC
    SOPC --> SIG
    SOPC --> HE
    SOPC --> HC
    HE --> LLM
    HE --> SEM
    HE --> MEM
    HE --> MM
    
    %% Relations infrastructure → engine
    HM --> SOPC
    HM --> SIG
    HM --> ABC
    PROP --> ABC
    PROP --> SOPC
    ORCH --> ROUT
    ORCH --> HM
    ORCH --> LLMF
    ORCH --> DET
    ORCH --> DS
    ROUT --> HM
    ROUT --> LLMF
    LLMF --> DET
    
    %% Scripts
    SCR --> ORCH
    SCR --> HM
    SCR --> DS
    TST --> core/
    TST --> engine/
```

---

## Pipeline de données — Flux complet

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant CLI as scripts/chat.py
    participant O as orchestrator.py
    participant R as router.py
    participant HM as holographic_memory.py
    participant SOPC as engine/sopc_core.py
    participant ABC as engine/abc_kernel.py
    participant SIG as engine/signatures_9d.py
    participant LLM as engine/llm/ + llm_fallback.py
    
    U->>CLI: saisie texte
    CLI->>O: respond(input)
    O->>O: preprocess() [déterminisme]
    O->>HM: retrieve(query_latent)
    
    Note over HM,SOPC: ZONE BREVETÉE
    
    HM->>SOPC: estimate_signature_from_activations()
    HM->>SIG: compute_signature_9d()
    SIG-->>HM: signature 9D
    SOPC-->>HM: sparse activations
    
    HM-->>O: (réponse, confiance)
    
    O->>R: route(confidence)
    
    alt confiance >= seuil 0.6
        R-->>O: réponse hologramme
    else confiance < seuil
        R->>LLM: generate(prompt)
        LLM-->>O: réponse LLM
    end
    
    O->>O: postprocess() [déterministe]
    O-->>CLI: réponse finale
    CLI-->>U: affichage
```

---

## Pipeline SOPC — Cœur mathématique

```mermaid
flowchart LR
    IN[Entrée texte] --> TOK[Tokenisation]
    TOK --> S9D[Signature 9D]
    S9D --> SL[Seuil Lloyd<br/>N_qubits = S + log₂1/ε]
    SL --> SR[Sparse Read<br/>WTA local + sigmoid φ²]
    SR --> PA[Prédicteur ABC pur<br/>0 paramètre, 0 divergence]
    PA --> FD[Dérivée fractionnaire ABC<br/>D^α_t = ABCα·K0·εt + ΣKτ·εt-τ]
    FD --> PG[Phase Gate ABC<br/>ω₀ = φ, θ = ω₀/φ, γ = ω₀·φ]
    PG --> ES[Estimation signature 9D]
    ES --> OUT[Sortie texte]
    
    style SL fill:#f96,stroke:#333
    style PA fill:#9cf,stroke:#333
    style FD fill:#9cf,stroke:#333
    style PG fill:#9cf,stroke:#333
```

---

## Pipeline d'entraînement (une passe)

```mermaid
flowchart LR
    DATA[Source de données<br/>~1 To] --> ST[stream_chunks<br/>data_stream.py]
    ST --> FIT[fit<br/>holographic_memory.py]
    FIT --> SP[sparse_read<br/>sopc_core.py]
    SP --> BUF[Buffer 32 Ko<br/>buffer_32k.bin]
    
    style BUF fill:#9f9,stroke:#333
```

---

## Dépendances entre modules

```mermaid
graph TD
    subgraph "Noyau mathématique fondamental"
        A[abc_kernel.py]
        A --> |gamma_lanczos| G[Fonction Γ]
        A --> |mittag_leffler| ML[E_αz]
        A --> |abc_kernel_np| K[Noyau Kτ]
    end
    
    subgraph "Algorithme SOPC"
        S[sopc_core.py]
        S --> |compute_sparse_threshold| LL[Seuil Lloyd]
        S --> |sparse_read| SPR[Sparse pipeline]
        S --> |predictive_update_abc| PA[Prédicteur ABC]
        S --> |fractional_derivative_update| FD[Dérivée fractionnaire]
        S --> |ABCPhaseGate| PG[Gate oscillatoire]
        S --> |resonance_sparse| RS[Pipeline complet]
    end
    
    subgraph "Signatures"
        SG[signatures_9d.py]
        SG --> |compute_phi_np| PHI[Dimension φ]
        SG --> |compute_alpha_np| ALP[Dimension α]
        SG --> |compute_reasoning_np| REA[Raisonnement]
        SG --> |compute_creativity_np| CRE[Ccréativité]
        SG --> |compute_math_np| MAT[Math]
        SG --> |compute_factual_np| FAC[Factuel]
        SG --> |compute_code_np| COD[Code]
        SG --> |compute_emotion_np| EMO[Émotion]
        SG --> |compute_temporal_np| TEMP[Temporal]
    end
    
    subgraph "Infrastructure"
        HM[holographic_memory.py]
        HM --> |fit| FIT[Apprentissage]
        HM --> |encode_to_boundary| ENC[Encodage]
        HM --> |retrieve| RET[Récupération]
    end
    
    A --> S
    S --> SG
    S --> HM
    SG --> HM
```

---

## Roadmap — Prochaines étapes

### Phase 1 : Validation immédiate
```mermaid
gantt
    title Phase 1 — Validation
    dateFormat  YYYY-MM-DD
    section Tests
    Lancer pytest                     :a1, 1d
    Vérifier imports engine/          :a2, 1d
    section Package
    Créer setup.py + pyproject.toml   :b1, 1d
    pip install -e .                  :b2, 1d
    section Chatbot
    Tester chat.py end-to-end         :c1, 2d
    Tracer buffer 32 Ko              :c2, 1d
```

### Phase 2 : Connexion réelle
```mermaid
gantt
    title Phase 2 — Connexion
    dateFormat  YYYY-MM-DD
    section Hologramme
    Connecter ka_knowledge_base/hologramme.npy  :d1, 3d
    Valider résonance réelle                     :d2, 2d
    section LLM
    Intégrer engine/llm/router.py comme fallback  :e1, 2d
    Tester OpenAI/Anthropic/Mistral              :e2, 2d
    section Multimodal
    Activer image via engine/multimodal/          :f1, 2d
    Activer audio                                :f2, 2d
    Activer vidéo                                :f3, 2d
```

### Phase 3 : Production
```mermaid
gantt
    title Phase 3 — Production
    dateFormat  YYYY-MM-DD
    section API
    Exposer engine/api/server.py          :g1, 2d
    Documentation Swagger                 :g2, 1d
    section Déploiement
    Dockerfile + docker-compose           :h1, 2d
    Tests d'intégration                   :h2, 2d
    section Monitoring
    Métriques de performance              :i1, 2d
    Logs structurés                       :i2, 1d
```

---

## Composants clés et leurs responsabilités

| Composant | Fichier | Responsabilité | Dépend vers |
|---|---|---|---|
| **Noyau ABC** | `engine/abc_kernel.py` | Mittag-Leffler, Gamma Lanczos, noyau Kτ | — |
| **SOPC** | `engine/sopc_core.py` | Seuil Lloyd, sparse read, prédicteur ABC, dérivée fractionnaire, gate φ, résonance | `abc_kernel` |
| **Signatures 9D** | `engine/signatures_9d.py` | Extraction des 9 dimensions cognitives | — |
| **Mémoire holographique** | `core/holographic_memory.py` | Buffer 32 Ko, fit/encode/retrieve | `sopc_core`, `signatures_9d`, `abc_kernel` |
| **Routeur** | `core/router.py` | Décision hologramme vs LLM selon confiance | `holographic_memory` |
| **Orchestrateur** | `core/orchestrator.py` | Boucle encode→route→post→decode | `router`, `holographic_memory`, `llm_fallback` |
| **Déterminisme** | `core/determinism.py` | Graines fixes, pré/post-processing, ancrage | — |
| **Streaming** | `core/data_stream.py` | Itérateur de chunks, une passe | — |
| **LLM Fallback** | `core/llm_fallback.py` | SmolLM2 GGUF CPU, décodage déterministe | `determinism` |
| **Opérateurs** | `core/proprietary/operators.py` | Pont FFT+ABC vers engine/ | `abc_kernel`, `sopc_core` |
| **LLM Router** | `engine/llm/router.py` | Multi-providers LLM | — |
| **Embeddings** | `engine/semantic/embeddings.py` | Hybrides 9D + 512D | `signatures_9d` |
| **Mémoire ABC** | `engine/memory/long_term.py` | Oubli basé sur le noyau ABC | `abc_kernel` |
| **Multimodal** | `engine/multimodal/analyzers.py` | Image/audio/vidéo → signature 9D | `signatures_9d` |
| **API** | `engine/api/server.py` | REST FastAPI | Tout le moteur |
