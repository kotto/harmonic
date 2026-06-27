# 🌊 Enhanced Harmonic Hybrid AI v2.0 - MVP

## Overview

Enhanced Harmonic Hybrid AI v2.0 est une plateforme d'IA hybride avancée utilisant une architecture **MOE (Mixture of Experts)** avec 4 experts spécialisés et une système de compression **5x** optimisé.

## Architecture

### 🧠 MOE Harmonique (4 Experts Spécialisés)

1. **Mathematical Reasoning** - Calculs, algèbre, géométrie
2. **Logical Deduction** - Raisonnement logique, déduction
3. **Coding Algorithms** - Programmation, algorithmes
4. **Scientific Knowledge** - Physique, chimie, biologie

### 🗜️ HCV PRO Compression (5x)

- **Vector Quantization Harmonique**
- **Knowledge Pruning Intelligente**
- **Weight Sharing Efficace**
- **Harmonic Encoding Sémantique**

### 🚀 API Core

- `/generate` - Génération avec MOE
- `/health` - Monitoring santé système
- `/metrics` - Métriques détaillées
- `/compress` - Compression à la demande

## Installation

```bash
# Cloner le repository
git clone <repository-url>
cd enhanced-harmonic-ai-v2

# Installer les dépendances
pip install -r requirements.txt

# Démarrer l'API
python api_core.py
```

## Documentation API

### Endpoints Principaux

#### `POST /generate`
Génère une réponse utilisant le système MOE.

**Request:**
```json
{
  "prompt": "Calculate 15 + 27",
  "use_compression": false,
  "max_tokens": 1000,
  "temperature": 0.7,
  "top_p": 0.9
}
```

**Response:**
```json
{
  "prompt": "Calculate 15 + 27",
  "response": "Math Solution: 15 + 27 = 42",
  "expert_responses": [...],
  "selected_experts": ["mathematical_reasoning"],
  "processing_time": 0.234,
  "confidence_score": 0.95,
  "tokens_used": 15,
  "model_version": "v2.0-mvp",
  "compression_applied": false,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### `GET /health`
Vérifie l'état de santé du système.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0-MVP",
  "uptime": 3600.0,
  "total_requests": 150,
  "successful_requests": 145,
  "failed_requests": 5,
  "average_response_time": 0.45,
  "experts_status": {...},
  "compression_status": {...},
  "system_resources": {...}
}
```

## Tests et Validation

### Hermes Test Agent

Exécutez les tests automatisés 6 phases:

```bash
python test_validation.py
```

**Phases de Test:**
1. **Syntax Validation** - Validation structure et syntaxe
2. **Semantic Coherence** - Cohérence sémantique des réponses
3. **Performance Benchmarks** - Tests de performance
4. **Robustness Testing** - Tests edge cases
5. **Scalability Testing** - Tests charge et concurrence
6. **Regression Testing** - Tests non-régression

## Performance

### Benchmarks Estimés

| Métrique | Performance Cible |
|----------|-------------------|
| GSM8K | 94-96% |
| MMLU | 90-92% |
| TruthfulQA | 88-90% |
| Coding | 85-87% |
| Reasoning | 91-93% |

### Compression

- **Ratio Cible**: 5x compression
- **Intégrité**: 95%+ préservation
- **Performance**: <1s compression/décompression

## Configuration

### Variables d'Environnement

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# MOE Configuration
MOE_EXPERTS_COUNT=4
MOE_ROUTING_THRESHOLD=0.7

# Compression Configuration
COMPRESSION_TARGET_RATIO=5.0
COMPRESSION_INTEGRITY_THRESHOLD=0.95
```

## Déploiement

### Local Development

```bash
# Démarrer le serveur de développement
python api_core.py

# Accéder à la documentation
# http://localhost:8000/docs
```

### Production

```bash
# Installation production
pip install -r requirements.txt

# Démarrage avec uvicorn
uvicorn api_core:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "api_core:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Architecture Technique

### MOE System

```python
# Exemple d'utilisation
from mvp_moe_experts import MOEOrchestrator

orchestrator = MOEOrchestrator()
result = orchestrator.process_request("Calculate 2 + 2")
print(result['synthesized_response'])
```

### Compression System

```python
# Exemple de compression
from compression_5x import HCVCompression5X

compressor = HCVCompression5X()
result = compressor.compress_expert(expert_data)
print(f"Compression ratio: {result['metrics']['compression_ratio']:.2f}x")
```

## Monitoring

### Métriques Disponibles

- **Requests per minute**
- **Average response time**
- **Success rate**
- **Expert usage distribution**
- **Compression efficiency**
- **System resources**

### Health Checks

- Expert health status
- Compression system integrity
- Memory usage
- Response time monitoring

## Roadmap

### Phase 1 - MVP (Actuel)
- ✅ 4 experts MOE
- ✅ Compression 5x
- ✅ API core
- ✅ Tests automatisés

### Phase 2 - Scale
- 🔄 8 experts MOE
- 🔄 Compression 10x
- 🔄 Monitoring avancé
- 🔄 Load balancing

### Phase 3 - Production
- 📋 Déploiement AWS
- 📋 Monitoring CloudWatch
- 📋 Scalability horizontale
- 📋 API Gateway

## Support

### Documentation
- API Docs: `/docs`
- Redoc: `/redoc`
- Health: `/health`
- Metrics: `/metrics`

### Issues
Pour toute question ou problème, veuillez créer une issue sur le repository GitHub.

## License

MIT License - Voir fichier LICENSE pour plus de détails.

---

**Enhanced Harmonic Hybrid AI v2.0** - *L'avenir de l'IA hybride* 🚀
