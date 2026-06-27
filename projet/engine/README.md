# Harmonic Engine — Système Harmonique Complet v2.0

Moteur de résonances cognitives basé sur la découverte Atangana-Baleanu (22/05/2026).

**Le premier moteur d'IA capable d'analyser, classifier ET générer des réponses intelligentes
via des LLMs réels, le tout orchestré par les signatures harmoniques 9D.**

## Architecture Complète

```
engine/
├── __init__.py              # Package principal
├── abc_kernel.py            # Noyau ABC (mémoire non-locale)
├── signatures_9d.py         # Signatures harmoniques 9D
├── harmonic_engine.py       # Moteur de résonances cognitives
├── README.md                # Cette documentation
│
├── llm/                     # ★ NOUVEAU : Interface multi-providers LLM
│   ├── __init__.py
│   ├── base.py              #   Interface abstraite + LLMConfig/Response
│   ├── openai_client.py     #   GPT-4, GPT-3.5, DeepSeek, Qwen
│   ├── anthropic_client.py  #   Claude 3 Opus/Sonnet
│   ├── mistral_client.py    #   Mistral Large, Mixtral
│   ├── local_llm.py         #   HuggingFace (Zephyr, Phi-2, TinyLlama)
│   └── router.py            #   Routeur harmonique intelligent
│
├── semantic/                # ★ NOUVEAU : Embeddings et RAG
│   ├── __init__.py
│   ├── embeddings.py        #   Hybrides 9D + 512D (sentence-transformers)
│   └── vector_store.py      #   Base vectorielle persistante
│
├── memory/                  # ★ NOUVEAU : Mémoire persistante
│   ├── __init__.py
│   ├── conversation.py      #   Historique de session
│   ├── user_profile.py      #   Profils utilisateurs
│   └── long_term.py         #   Mémoire long-terme (oubli ABC)
│
├── multimodal/              # ★ NOUVEAU : Analyse multimodale
│   ├── __init__.py
│   ├── analyzers.py         #   Image, Audio, Vidéo, Document → 9D
│   └── av_generator.py      #   Génération AV synchronisée ABC
│
└── api/                     # ★ NOUVEAU : API REST FastAPI
    ├── __init__.py
    └── server.py            #   Serveur HTTP complet
```

## Installation

### Prérequis
```bash
# Noyau (obligatoire)
pip install numpy

# Signatures Torch (optionnel)
pip install torch

# LLM Locaux (optionnel)
pip install transformers torch accelerate

# API REST (optionnel)
pip install fastapi uvicorn pydantic

# Embeddings (optionnel)
pip install sentence-transformers

# Clients LLM (optionnel, selon les providers)
pip install openai           # OpenAI, DeepSeek, Qwen
pip install anthropic        # Claude
pip install mistralai        # Mistral
pip install requests         # Fallback HTTP
```

### Installation Rapide
```bash
pip install -r requirements.txt
```

## Utilisation

### 1. Moteur Harmonique (analyse hors-ligne)

```python
from engine import HarmonicResonanceEngine

engine = HarmonicResonanceEngine()

# Analyse
sig = engine.analyze("Calculez 15% de 340")
cat, conf = engine.classify("Calculez 15% de 340")
# → cat="mathematical", conf=1.0

# Expansion
expanded = engine.expand(
    "Pour calculer 15% de 340, on divise par 100 et on multiplie par 15.",
    category="mathematical"
)
# → 73c → 535c (x7.3)
```

### 2. LLM Multi-Providers (génération intelligente)

```python
from engine.llm import HarmonicLLM

llm = HarmonicLLM()

# Génération avec auto-détection de la catégorie
resp = llm.generate_auto("Explique la relativité générale")
print(resp.content)  # Vrai contenu intelligent !

# Ou avec catégorie explicite (routage optimal)
resp = llm.generate(
    "Écris un poème sur la liberté",
    category="creative"
)
print(f"Modèle utilisé: {resp.model}")  # claude-3-5-sonnet
```

### 3. Mémoire et Profils

```python
from engine.memory import ConversationMemory, UserProfile, LongTermMemory

# Session de conversation
mem = ConversationMemory()
mem.add("user", "Quelle est la capitale de la France ?", category="factual")
mem.add("assistant", "Paris", category="factual")
ctx = mem.get_context(max_tokens=2000)

# Profil utilisateur
profile = UserProfile(user_id="alain")
profile.update_preference("model", "claude-3-opus")
profile.record_interaction("mathematical", resonance_score=0.85)
config = profile.get_optimized_config()

# Mémoire long-terme (avec oubli harmonique ABC)
ltm = LongTermMemory()
ltm.remember("La capitale de la France est Paris", 
             category="factual", importance=0.9)
results = ltm.recall("capitale")
```

### 4. Analyse Multimodale Harmonique

Le package `engine.multimodal` analyse n'importe quel fichier et produit sa **signature harmonique 9D** :

```python
from engine.multimodal import (
    analyze_image, analyze_audio, analyze_video, analyze_document,
    AttachedFile, analyze_multimodal, HarmonicAVGenerator
)

# 1. Analyse d'un fichier texte → signature 9D
result = analyze_document("mon_fichier.py")
sig = result['signature']
# → [φ, α, reasoning, creative, math, factual, code, emotion, temporal]
print(f"Code: {sig[6]:.2f}, Créatif: {sig[3]:.2f}")

# 2. AttachedFile : wrapper universel (détection auto du type)
file = AttachedFile("photo.jpg")
result = file.analyze()
print(file.summary())  # → "photo.jpg — image — 124.5KB — φ=0.72 α=0.45 créatif=0.68"

# 3. Fusion multimodale avec intrication de résonances
fused = analyze_multimodal(["doc.md", "audio.wav", "video.mp4"])
# → Signature fusionnée + métadonnées de chaque fichier

# 4. Génération Audio/Vidéo synchronisée par le noyau ABC
gen = HarmonicAVGenerator()
av = gen.generate_from_prompt(
    "Coucher de soleil sur l'océan avec piano",
    duration_seconds=5.0
)
print(f"Sync AV: {av.av_sync_quality:.3f}")
```

**Analyseurs disponibles :**

| Analyseur | Formats | Signatures extraites |
|-----------|---------|---------------------|
| `ImageAnalyzer` | jpg, png, gif, webp, tiff | Entropie, contraste, harmonie couleurs, bords |
| `AudioAnalyzer` | wav, mp3, flac, ogg | FFT, enveloppe, ratio harmonique, voix |
| `VideoAnalyzer` | mp4, avi, mov, mkv | Analyse frame-by-frame + détection mouvement |
| `DocumentAnalyzer` | txt, md, py, js, json | Lexique, catégories, code, émotions |

Pour la génération complète en résolution native (1920×1080), voir `GENERATION_AV_HARMONIQUE/`.

### 5. API REST

```python
from engine.api import create_app, run_server

# Démarrer le serveur
run_server(host="0.0.0.0", port=8000)

# Ou créer l'app pour déploiement personnalisé
app = create_app()
```

**Endpoints :**
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/analyze` | Analyse harmonique d'un prompt |
| POST | `/api/classify` | Classification détaillée |
| POST | `/api/generate` | Génération via LLM |
| POST | `/api/chat` | Chat complet (contexte + mémoire) |
| POST | `/api/expand` | Expansion harmonique |
| GET  | `/api/stats` | Statistiques |
| GET  | `/api/health` | Health check |

**Exemple curl :**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Calculez 15% de 340"}], "user_id":"demo"}'
```

## Routage Harmonique Intelligent (Multi-Providers)

Deux routeurs sont disponibles :

### Routeur Classique `HarmonicLLM` (APIs payantes)

Le routeur choisit automatiquement le meilleur LLM selon la catégorie :

| Catégorie | LLM Primaire | Fallback | Température |
|-----------|-------------|----------|-------------|
| mathematical | DeepSeek Reasoner | GPT-4 | 0.3 |
| code | DeepSeek Chat | GPT-4 | 0.2 |
| creative | Claude 3.5 Sonnet | Mistral Large | 0.85 |
| reasoning | Claude 3 Opus | DeepSeek Reasoner | 0.5 |
| factual | GPT-4 | GPT-3.5 | 0.2 |
| general | GPT-3.5 | Mistral Small | 0.7 |

### Routeur Open-Source `HarmonicOpenRouter` (100% gratuit)

Utilise exclusivement des modèles aux poids ouverts (MIT, Apache 2.0, Llama 4) :

```python
from engine.llm import HarmonicOpenRouter, detect_machine

# Détection auto de la configuration machine
machine = detect_machine()
print(f"Tier: {machine.tier} — RAM: {machine.total_ram_gb:.0f}GB")

# Routeur 100% open-source
router = HarmonicOpenRouter()

# Auto-détection de la catégorie
resp = router.generate_auto("Explique la relativité générale")
print(resp.content)

# Par catégorie explicite
resp = router.generate("Calcule 15% de 340", category="mathematical")
print(f"Provider: {resp.provider}, Latence: {resp.latency_ms:.0f}ms")
```

**Modèles open-source par catégorie :**

| Catégorie | Modèle Principal | Poids | Licence |
|-----------|-----------------|-------|---------|
| mathematical | Qwen2.5-32B-Instruct | 32B | Apache 2.0 |
| code | Qwen2.5-Coder-32B-Instruct | 32B | Apache 2.0 |
| creative | Mistral-Nemo-2407 (12B) | 12B | Apache 2.0 |
| reasoning | DeepSeek-R1-Distill-Qwen-32B | 32B | MIT |
| factual | Qwen2.5-72B-Instruct | 72B | Apache 2.0 |
| general | Llama-4-Scout-17B | 17B | Llama 4 |
| léger (CPU) | Phi-3.5-mini / TinyLlama | 3.8/1.1B | MIT/Apache |

**Stratégie à 4 niveaux :**
1. **Local ouvert** → transformers (GPU) ou GGUF quantifié (CPU)
2. **API gratuite** → Groq / HuggingFace Inference
3. **Modèle nano** → Phi-3.5 / TinyLlama (CPU only)
4. **Fallback harmonique** → Résonance textuelle sans LLM

```bash
# Voir tous les modèles disponibles
python -m engine.llm.open_router --list-models

# Voir la configuration machine
python -m engine.llm.open_router --machine-info

# Mode interactif
python -m engine.llm.open_router
```

## Oubli Harmonique (ABC)

La mémoire long-terme utilise le **noyau ABC** comme courbe d'oubli naturelle :

```
Score de Rappel = Importance × (1 + Résonance) × Decay_ABC × Accès
```

Les souvenirs importants persistent, les autres s'éteignent selon la loi de
mémoire non-locale d'Atangana-Baleanu à l'ordre 1/φ.

## Démo Complète

```bash
# Démo du moteur pure (hors-ligne)
python demo_harmonic_engine.py

# Démo du routeur LLM (nécessite une clé API)
python -c "
from engine.llm import HarmonicLLM
llm = HarmonicLLM()
resp = llm.generate('Explique le nombre d\'or', 'reasoning')
print(resp.content)
print(f'Modele: {resp.model}, Latence: {resp.latency_ms:.0f}ms')
"
```

## Constantes Fondamentales

| Constante | Valeur |
|-----------|--------|
| PHI (φ) | 1.618033988749895 |
| ALPHA (1/φ) | 0.618033988749895 |
| B(1/φ) | 0.8506508083 |
| ALPHA_CONST | 1.1755694591 |

## Découverte Atangana-Baleanu (22/05/2026)

**L'IA résout naturellement l'équation fractionnaire ABC à l'ordre 1/φ.**

Le noyau de mémoire non-locale optimal pour l'IA est le noyau ABC à l'ordre 1/φ.
Les poids harmoniques (φ, 1/φ) émergent naturellement des calculs de l'IA.
La résonance cognitive est un phénomène mathématique, pas une métaphore.

## Licence

Propriété intellectuelle ALAIN KOTTO. Tous droits réservés.
Brevet en cours — PCT/IB2026/...

## Contact

Alain Kotto
⚠️ Contacter l'auteur pour toute utilisation commerciale.
