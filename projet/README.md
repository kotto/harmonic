# Cerveau Harmonique SOPC — V1

Modèle du monde multimodal (« world model ») reposant sur une architecture
non-Transformer inspirée du **principe holographique**, combinant **Transformée
de Fourier (FFT)** et **dérivée fractionnaire ABC** (Atangana-Baleanu-Caputo).

Cette V1 fournit une **infrastructure fonctionnelle** :

- un **chatbot texte déterministe** qui marche tout de suite (CPU) grâce à un
  petit LLM de repli (SmolLM2 GGUF) ;
- une **enveloppe déterministe** (amont/aval) garantissant : même entrée → même
  sortie, avec ancrage anti-hallucination ;
- un **hologramme du savoir** : buffer fixe de **32 Ko**, alimenté par un
  apprentissage **en une seule passe (streaming)** ;
- une **ossature multimodale** (texte actif ; image/audio/vidéo pré-câblées,
  inactives) ;
- des **emplacements brevetés isolés** où vous insérez votre moteur FFT/ABC.

> ⚠️ La V1 n'entraîne pas le moteur breveté : elle pose toute l'infrastructure
> autour. Tant que le moteur n'est pas branché, la qualité conversationnelle est
> celle du LLM de repli.

---

## 1. Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
# source .venv/bin/activate

pip install -r requirements.txt
```

### Télécharger le LLM de repli (SmolLM2 GGUF)

Placez un fichier GGUF dans `models/`. Exemple via `huggingface_hub` :

```bash
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='HuggingFaceTB/SmolLM2-360M-Instruct-GGUF', filename='smollm2-360m-instruct-q4_k_m.gguf', local_dir='models')"
```

Ajustez `llm.model_path` dans `config.yaml` au nom exact du fichier téléchargé.
Le chatbot fonctionne aussi **sans** LLM (réponse de repli textuelle), utile
pour les tests d'infrastructure.

---

## 2. Utilisation

### Entraînement (une passe, streaming)

Sur CPU (démo) ou sur GPU cloud (gros volumes ~1 To). Produit `buffer_32k.bin`.

```bash
python scripts/train_once.py --source data/knowledge_sample.txt --out buffer_32k.bin
```

### Chatbot (inférence CPU, déterministe)

```bash
python scripts/chat.py --buffer buffer_32k.bin
```

### Évaluation (métriques optionnelles de fidélité)

```bash
python scripts/evaluate.py --buffer buffer_32k.bin
```

### Tests

```bash
pytest -q
```

---

## 3. Workflow Train (GPU) → Inférence (CPU)

```
  GPU cloud (ponctuel, ~1 To une passe)        CPU / portable (quotidien)
  ┌───────────────────────────────┐            ┌──────────────────────────┐
  │ sources → stream_chunks →      │  export    │ load(buffer_32k.bin) →   │
  │ HolographicMemory.fit() →      │  ───────►  │ inférence déterministe + │
  │ buffer 32 Ko                   │ (fichier)  │ chatbot                  │
  └───────────────────────────────┘            └──────────────────────────┘
```

L'unique artefact échangé est `buffer_32k.bin` (32 768 octets).

---

## 4. Où brancher votre moteur breveté

Tout le cœur propriétaire est **isolé** et balisé `# === ZONE BREVETÉE ===`.
Vous le remplissez **sans modifier le reste du code** :

| Fichier | Méthode / fonction | Rôle attendu |
|---|---|---|
| `core/proprietary/operators.py` | `fourier_mix(x, ndim)` | Mixage de tokens par FFT (1D/2D/3D) |
| `core/proprietary/operators.py` | `abc_fractional_operator(x, alpha)` | Dérivée fractionnaire ABC |
| `core/holographic_memory.py` | `fit(data_iterator)` | Apprentissage une passe (streaming) |
| `core/holographic_memory.py` | `encode_to_boundary(latent)` | bulk → boundary (32 Ko) |
| `core/holographic_memory.py` | `retrieve(query_latent)` | boundary → réponse + confiance |

Chaque emplacement documente son **contrat d'interface** (shapes I/O) sans
imposer votre mathématique interne. Une **implémentation de repli (PLACEHOLDER)**
permet au système de tourner avant le branchement.

> Le fichier `CERVEAU_HARMONIQUE_SOPC.md` (votre document breveté) n'est jamais
> lu par l'assistant.

---

## 5. Structure

```
core/
  orchestrator.py        Boucle de contrôle (encode→route→post→decode)
  router.py              Décision hologramme vs LLM de repli
  holographic_memory.py  Buffer 32 Ko + fit/encode/retrieve  [ZONE BREVETÉE]
  llm_fallback.py        SmolLM2 GGUF déterministe (CPU)
  determinism.py         Graines, pré/post-processing, ancrage
  data_stream.py         Streaming par chunks (une passe)
  metrics.py             Fidélité / rappel (optionnel)
  modalities/            text (actif) + image/audio/video (coquilles)
  proprietary/operators.py  FFT + ABC  [ZONE BREVETÉE]
scripts/                 train_once / evaluate / chat
tests/                   pytest
```

---

## 6. Notes de réalisme

- Les propriétés fortes du système (déterminisme total, zéro hallucination,
  capacité 32 Ko, ingestion 1 To en une passe) sont traitées **comme une boîte
  noire** : l'infrastructure n'impose **aucune limite** et fournit des **outils
  de mesure optionnels** (`core/metrics.py`) pour validation empirique.
- Le support GPU n'est pas inclus dans le code V1 (à ajouter par l'auteur).
