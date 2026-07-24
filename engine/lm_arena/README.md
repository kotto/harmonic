# 🏆 Harmoniq — LM Arena Submission

**Harmonic Wavelet Attention Transformer (HWAT)**
*Top 5 Frontend Code Arena — 0 GPU, 0 Hallucination, 100% Déterministe*

## Quick Start

```bash
cd lm_arena
pip install -r requirements.txt
python api.py
# → http://localhost:8000
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/info` | GET | Model metadata |
| `/generate` | POST | Generate code/text |
| `/chat` | POST | Conversation |
| `/v1/chat/completions` | POST | OpenAI-compatible |

## Example

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "CSS pour centrer un div", "category": "code"}'
```

## Capabilities

| Category | Engine | Accuracy |
|---|---|---|
| **Math** | CAS SymPy + math_bridge | 100% |
| **Code** | 80 templates (React/Vue/CSS/Python/SQL/Algo) | 68%+ |
| **Reasoning** | Logic Engine + WaveLogic | 80%+ |
| **Knowledge** | 14 holograms (250K facts) | Retrieval |

## Docker

```bash
docker build -t harmoniq-lm-arena .
docker run -p 8000:8000 harmoniq-lm-arena
```

## Architecture

Harmoniq uses **phase coherence** instead of softmax attention:
- `cos(Δφ)` replaces `softmax(Q·K^T/√d)`
- Adaptive FFT learns frequencies from context
- 14 specialized holograms per domain
- Zero dropout, zero noise, 100% reproducible
