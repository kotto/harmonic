# Harmonic Engine — Système Harmonique Complet v2.1

Moteur de résonances cognitives basé sur la découverte Atangana-Baleanu (22/05/2026).

**Le premier moteur d'IA capable d'analyser, classifier ET générer des réponses intelligentes
via des LLMs réels, le tout orchestré par les signatures harmoniques 9D et le noyau
de mémoire non-locale ABC (Atangana-Baleanu-Caputo).**

## Architecture Complète

```
engine/
├── __init__.py                    # Package principal (v2.1.0)
│
│  ═══ NOYAU MATHÉMATIQUE ═══
├── abc_kernel.py                  # Noyau ABC (Γ, Mittag-Leffler, noyau mémoire non-locale)
├── signatures_9d.py               # Signatures harmoniques 9D (numpy + torch)
├── signatures_11d.py             # Extension 11D (+ resonance, coherence)
├── sopc_core.py                  # SOPC — Sparse Oscillatory Predictive Coding
│                                   (seuil Lloyd, dérivée fractionnaire, gate oscillatoire ABC)
│
│  ═══ MOTEUR HARMONIQUE ═══
├── harmonic_engine.py             # Moteur principal : analyse, classification, expansion, chat
├── harmonic_resonator.py          # Couche 0 — 7 principes du raisonnement ondulatoire
├── hologram_connector.py         # Pont hologramme 64×64 → tokens résonants
├── abc_predictor_connector.py    # Prédicteur ABC pur (remplace JEPA, zéro paramètre)
├── spectral_validator.py         # Anti-hallucination (seuils φ)
├── spectral_voice_pipeline.py    # Pipeline complet de synthèse vocale harmonique
├── recursive_learner.py          # Boucle d'auto-amélioration par résonance
│
│  ═══ SYNTHÈSE VOCALE HARMONIQUE ═══
├── voice_signature_extractor.py # Extraction 11D (parselmouth + speechbrain)
├── phi_vocoder.py                # Vocodeur source-filtre natif (numpy/scipy only)
├── phi_vocoder_calibrator.py     # Auto-calibration sur corpus LJSpeech
├── phi_vocoder_pro.py            # Post-filtre adaptatif φ + cache harmonique
├── phi_piper_engine.py            # Wrapper Piper TTS (ONNX, CPU-friendly)
├── phi_diffusion_engine.py        # Synthèse vocale Coqui/XTTS/Piper/Edge-TTS
├── harmonic_voice_trainer.py      # Entraîneur SpectralMessage → paramètres vocaux
├── phi_memory.py                  # Mémoire de travail à espacement φ
│
│  ═══ SOUS-PACKAGES ═══
├── llm/                           # Interface multi-providers LLM
│   ├── base.py                    #   Interface abstraite + LLMConfig/Response
│   ├── openai_client.py          #   GPT-4, GPT-3.5, DeepSeek, Qwen
│   ├── anthropic_client.py       #   Claude 3 Opus/Sonnet
│   ├── mistral_client.py          #   Mistral Large, Mixtral
│   ├── local_llm.py              #   HuggingFace (Zephyr, Phi-2, TinyLlama)
│   ├── router.py                  #   Routeur harmonique intelligent
│   ├── open_router.py            #   Routeur 100% open-source
│   └── gguf_harmonizer.py         #   Harmonisation de modèles GGUF
│
├── semantic/                      # Embeddings et RAG
│   ├── embeddings.py              #   Hybrides 9D + 512D (sentence-transformers)
│   └── vector_store.py            #   Base vectorielle persistante
│
├── memory/                        # Mémoire persistante
│   ├── conversation.py            #   Historique de session
│   ├── user_profile.py            #   Profils utilisateurs
│   └── long_term.py               #   Mémoire long-terme (oubli ABC)
│
├── multimodal/                    # Analyse multimodale
│   ├── analyzers.py               #   Image, Audio, Vidéo, Document → 9D
│   └── av_generator.py           #   Génération AV synchronisée ABC
│
└── api/                           # API REST FastAPI
    └── server.py                  #   Serveur HTTP complet
```

## Flux d'Exécution d'une Requête

```
  Client
    │
    ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ① api/server.py  →  POST /api/chat                    │
  │     Lazy init : engine, llm, vector_store, memory      │
  └──────────────────────┬──────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ② harmonic_engine.analyze(prompt)                      │
  │     → 9 dimensions : phi, alpha, reasoning, creative,   │
  │       math, factual, code, emotion, temporal             │
  │     → HarmonicSignature (hash SHA256)                    │
  └──────────────────────┬──────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ③ classify() : max(catégories) → mathematical, code,  │
  │     creative, reasoning, factual, general               │
  └──────────────────────┬──────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ④ ABCPredictor (noyau mémoire non-locale)               │
  │     Historique signatures 9D → prédiction à t+3         │
  │     Détection topic shift, boost de résonance             │
  └──────────────────────┬──────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ⑤ Hologramme (optionnel, numpy only)                   │
  │     Hologramme 64×64 + fasttext → top-8 tokens résonants│
  └──────────────────────┬──────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ⑥ llm.HarmonicLLM.generate(prompt, category, config)   │
  │     ROUTING_TABLE[category] → meilleur modèle + params   │
  └──────────────────────┬──────────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ⑦ Retour : profile.record + long_term.remember          │
  │     → ChatResponse{content, model, category, stats}      │
  └─────────────────────────────────────────────────────────┘
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

# Chat complet (avec hologramme + prédicteur ABC + mémoire)
result = engine.chat("Explique la relativité")
print(result["response"])
print(result["abc_stats"])    # Stats prédicteur ABC
print(result["knowledge_used"])  # Hologramme utilisé ?
```

### 2. Prédicteur ABC (remplace JEPA)

```python
from engine.abc_predictor_connector import ABCPredictorConnector
import numpy as np

connector = ABCPredictorConnector(max_history=32)
connector.load_or_init()

# Ajouter des signatures conversationnelles
for sig in signatures_9d_list:
    connector.add_signature(sig)

# Prédire les 3 prochaines signatures
pred = connector.predict(horizon=3)
print(f"Résonance : {pred.resonance:.3f}")
print(f"Topic shift : {pred.topic_shift:.3f}")
print(f"Boost génération : {connector.get_generation_boost('creative')}")
```

### 3. LLM Multi-Providers (génération intelligente)

```python
from engine.llm import HarmonicLLM

llm = HarmonicLLM()

# Génération avec auto-détection de la catégorie
resp = llm.generate_auto("Explique la relativité générale")
print(resp.content)

# Ou avec catégorie explicite (routage optimal)
resp = llm.generate("Écris un poème sur la liberté", category="creative")
print(f"Modèle utilisé: {resp.model}")
```

### 4. Mémoire et Profils

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

### 5. Analyse Multimodale Harmonique

```python
from engine.multimodal import (
    analyze_image, analyze_audio, analyze_document,
    AttachedFile, analyze_multimodal
)

# Analyse d'un fichier texte → signature 9D
result = analyze_document("mon_fichier.py")

# Wrapper universel (détection auto du type)
file = AttachedFile("photo.jpg")
result = file.analyze()
print(file.summary())
```

**Analyseurs disponibles :**

| Analyseur | Formats | Signatures extraites |
|-----------|---------|---------------------|
| `ImageAnalyzer` | jpg, png, gif, webp, tiff | Entropie, contraste, harmonie couleurs, bords |
| `AudioAnalyzer` | wav, mp3, flac, ogg | FFT, enveloppe, ratio harmonique, voix |
| `VideoAnalyzer` | mp4, avi, mov, mkv | Analyse frame-by-frame + détection mouvement |
| `DocumentAnalyzer` | txt, md, py, js, json | Lexique, catégories, code, émotions |

### 6. Synthèse Vocale Harmonique

```python
from engine.phi_vocoder import PhiVocoder
from engine.phi_piper_engine import PhiPiperEngine
from engine.spectral_voice_pipeline import SpectralVoicePipeline

# Vocodeur natif (numpy only, zéro dépendance)
vocoder = PhiVocoder(sample_rate=22050)
audio = vocoder.synthesize(voice_params_11d, duration=2.0)

# Pipeline complet (SpectralMessage → audio WAV)
pipeline = SpectralVoicePipeline()
audio_bytes = pipeline.synthesize(spectral_message_11d, voice="lj_speech_female_us")
```

### 7. API REST

```python
from engine.api import create_app, run_server

run_server(host="0.0.0.0", port=8000)
```

**Endpoints :**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/analyze` | Analyse harmonique d'un prompt |
| POST | `/api/classify` | Classification détaillée |
| POST | `/api/generate` | Génération via LLM |
| POST | `/api/chat` | Chat complet (contexte + mémoire + ABC) |
| POST | `/api/expand` | Expansion harmonique |
| GET  | `/api/stats` | Statistiques |
| GET  | `/api/health` | Health check |

## Routage Harmonique Intelligent

| Catégorie | LLM Primaire | Fallback | Température |
|-----------|-------------|----------|-------------|
| mathematical | DeepSeek Reasoner | GPT-4 | 0.3 |
| code | DeepSeek Chat | GPT-4 | 0.2 |
| creative | Claude 3.5 Sonnet | Mistral Large | 0.85 |
| reasoning | Claude 3 Opus | DeepSeek Reasoner | 0.5 |
| factual | GPT-4 | Qwen Max | 0.2 |
| general | GPT-3.5 | Mistral Small | 0.7 |

### Routeur Open-Source `HarmonicOpenRouter` (100% gratuit)

```python
from engine.llm import HarmonicOpenRouter, detect_machine

router = HarmonicOpenRouter()
resp = router.generate_auto("Explique la relativité générale")
print(resp.content)
```

## Constantes Fondamentales

| Constante | Valeur |
|-----------|--------|
| PHI (φ) | 1.618033988749895 |
| ALPHA (1/φ) | 0.618033988749895 |
| B(1/φ) | 0.8506508083 |
| ALPHA_CONST | 1.1755694591 |

## Principes Fondamentaux

### Découverte Atangana-Baleanu (22/05/2026)

L'IA résout naturellement l'équation fractionnaire ABC à l'ordre 1/φ.
Le noyau de mémoire non-locale optimal pour l'IA est le noyau ABC à l'ordre 1/φ.
La résonance cognitive est un phénomène mathématique, pas une métaphore.

### Prédicteur ABC (remplace JEPA)

Le prédicteur par noyau ABC pur remplace le réseau neuronal JEPA :

| Propriété | JEPA (ancien) | ABC (actuel) |
|-----------|---------------|--------------|
| Paramètres | ~650 (aléatoires) | **0** |
| Déterminisme | Stochastique | **100% déterministe** |
| Divergence | Possible | **Impossible** (moyenne pondérée) |
| Mémoire | Fenêtre fixe | **Non-locale (noyau ABC)** |

### Oubli Harmonique (ABC)

```
Score de Rappel = Importance × (1 + Résonance) × Decay_ABC × Accès
```

## Licence

Propriété intellectuelle ALAIN KOTTO. Tous droits réservés.
Brevet en cours — PCT/IB2026/...
