# LM Arena — Harmonic AI Submission

> **Catégories : Mathématiques & Raisonnement**
>
> Moteur harmonique SOPC (Sparse Oscillatory Predictive Coding) avec fallback intelligent. Déterministe, sans hallucination, 0 paramètre appris.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     LM ARENA SERVER                          │
│                                                              │
│  Requête → HarmonicMathEngine.analyze()                      │
│                │                                             │
│         confiance ≥ seuil ?                                  │
│         ┌──────┴──────┐                                      │
│         │ OUI         │ NON                                  │
│         ▼             ▼                                      │
│   solve()        FallbackRouter.generate()                   │
│   (déterministe)  (Ollama / API / mock)                      │
│         │             │                                      │
│         └──────┬──────┘                                      │
│                ▼                                             │
│         Réponse + confidence + métadonnées                   │
└──────────────────────────────────────────────────────────────┘
```

## Fichiers

| Fichier | Rôle |
|---|---|
| `server.py` | API FastAPI (endpoints `/health`, `/generate`, `/benchmark`) |
| `harmonic_math_engine.py` | Moteur harmonique : analyse, résolution, raisonnement |
| `fallback_router.py` | Routeur fallback : Ollama → API → mock |
| `benchmark_math.py` | Benchmark interne (10 math + 5 reasoning) |
| `config.yaml` | Configuration (seuils, modes, constantes) |
| `requirements.txt` | Dépendances Python |

## Installation

```bash
cd lm_arena
pip install -r requirements.txt
```

## Utilisation

### Démarrer le serveur

```bash
python server.py --port 8000
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Génération

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the derivative of x^2?", "max_tokens": 256}'
```

### Benchmark

```bash
# Via l'API
curl -X POST http://localhost:8000/benchmark \
  -H "Content-Type: application/json" \
  -d '{"category": "math", "num_samples": 10}'

# En ligne de commande
python benchmark_math.py
```

## Configuration du Fallback

Par défaut, le fallback est en mode `mock` (toujours disponible).

### Mode Ollama (local)

```bash
export HARMONIC_FALLBACK_MODE=ollama
export OLLAMA_MODEL=deepseek-math-1.5b:latest
python server.py
```

### Mode API externe

```bash
export HARMONIC_FALLBACK_MODE=api
export HARMONIC_API_ENDPOINT=https://api.openai.com/v1/chat/completions
export HARMONIC_API_KEY=sk-...
python server.py
```

## Métriques

| Métrique | Description |
|---|---|
| `confidence` | Score de confiance harmonique (0-1) |
| `source` | `"harmonic"` (déterministe) ou `"fallback"` (LLM) |
| `harmonic_ratio` | % de requêtes résolues sans fallback |
| `accuracy` | % de réponses correctes (benchmark) |

## Principe

Basé sur le **Cerveau Harmonique SOPC V1** et la **Théorie Harmonique de l'Univers** :

- 7 constantes fondamentales (π, φ, e, √2, √3, √5, i)
- Dérivée fractionnaire ABC d'ordre α = 1/φ
- Buffer holographique 32 Ko
- 0 paramètre appris, 0 hallucination, streaming une passe

*Documentation complète : `plans/THEORIE_HARMONIQUE_UNIVERS_FONDEMENTS.md`*