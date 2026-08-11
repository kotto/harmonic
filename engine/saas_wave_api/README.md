# 🌊 Harmonic Compute — Service SaaS de calcul harmonique (quantum-like)

**Machine de Hilbert déterministe** : les 13 primitives du langage ondulatoire
(ℂ⁵¹², ‖ψ‖ = 1) exposées en REST — les mêmes opérations que la cinématique
quantique (superposition, unitaires, résonance, FFT), **sans le hasard** :
100 % déterministe, traçable, reproductible.

> Honnêteté : émulateur harmonique — pas un ordinateur quantique matériel.
> La dérivation complète (E1) reste une porte ouverte. Les coefficients de
> l'équation mère ne sont pas {φ, π, e} (X1).

## Démarrage

```bash
pip install -r saas_wave_api/requirements.txt
uvicorn saas_wave_api.main:app --host 0.0.0.0 --port 8000
```

- Playground interactif : http://localhost:8000/
- Documentation OpenAPI : http://localhost:8000/docs

## Premier appel

```bash
# 1 · Créer une clé API (plan free — 100 req/j)
curl -X POST http://localhost:8000/v1/auth/register \
     -H 'Content-Type: application/json' -d '{"email": "vous@exemple.com"}'
# → {"api_key": "hwu_..."}

# 2 · État du moteur (public)
curl http://localhost:8000/v1/meta/status

# 3 · Encoder un concept (clé requise)
curl -X POST http://localhost:8000/v1/wave/encode \
     -H 'X-API-Key: hwu_...' -H 'Content-Type: application/json' \
     -d '{"entity": "lumiere"}'
```

## Endpoints

| Groupe | Endpoints |
|---|---|
| `meta` | `/v1/meta/status` (public) · `/v1/meta/benchmark` |
| `wave` | `/v1/wave/encode` · `decode` · `bind` · `unbind` · `superpose` · `resonate` · `rotate` · `interfere` · `diffract` · `filter` · `phase_shift` · `emerge` · `solve` |
| `memory` | `/v1/memory/store` · `query` · `stats` |
| `auth` | `/v1/auth/register` (free) — pro/enterprise : `python -m ka_server.tools.wave_keys create email --plan pro` |

## SDK Python (zéro dépendance)

```python
from saas_wave_api.sdk.wave_client import WaveClient

client = WaveClient(base_url='http://localhost:8000', api_key='hwu_...')
client.register('vous@exemple.com')          # → crée une clé free
client.encode('lumiere')                     # → ψ (dim, norme, vecteur)
client.resonate('chat', 'chat')              # → 1.0 (identité)
client.memory_store([['lumiere', 'est une', 'onde electromagnetique']])
client.memory_query('Qu\'est-ce que la lumiere ?')
```

## Plans

| Plan | Quota journalier | Usage |
|---|---|---|
| **free** | 100 req/j | Découverte, éducation, prototypes |
| **pro** | 5 000 req/j | Production, intégration |
| **enterprise** | 50 000 req/j | On-premise, SLA, données privées |

## Vérification

```bash
python -m pytest saas_wave_api/tests -q        # API FastAPI
python -m pytest ka_server/tests/test_wave_api.py -q   # MVP Flask (14 tests)
```

Références : `DOCUMENT_FONDATEUR_EMERGENCE_QUANTIQUE.md` · `HPU_V2_FONDATIONS.md`
