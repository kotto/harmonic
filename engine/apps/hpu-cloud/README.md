# ☁️ HPU Cloud — API de Calcul Harmonique

## Description
API de l'Ordinateur Harmonique V2. H-Bit, mémoire dorée, inférence par résonance.
Zéro hallucination, zéro GPU, zéro paramètre libre.

## Fonctionnalités
- **H-Bit Core** : calcul vectoriel par interférence (encode, resonate, bind, superpose, interfere)
- **Golden Memory** : apprentissage holographique en 3-5 répétitions
- **Wave Inference** : inférence avec refus calibré
- **GSM8K** : raisonnement mathématique 99.2%
- **Particules** : 18 classées, 30 prédites
- **Éléments** : 118 éléments chimiques

## Démarrage

### Manuel
```bash
cd engine/
python server_hpu_cloud.py
```

### Docker
```bash
docker compose -f docker-compose.hpu.yml up -d
```

## Accès
- Interface : http://localhost:9100
- API : http://localhost:9100/health
- Docs : http://localhost:9100/docs

## API
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| /health | GET | État du service |
| /api/v1/status | GET | Statut HPU |
| /api/v1/theorems | GET | 6 théorèmes |
| /api/v1/particles | GET | Particules |
| /api/v1/elements | GET | Éléments |
| /api/v1/gsm8k | GET | Maths |
| /api/v1/hbit | POST | Calcul H-Bit |
| /api/v1/memory/store | POST | Apprentissage |
| /api/v1/memory/recall | POST | Rappel |
| /api/v1/infer | POST | Inférence |

## Fichiers
- `engine/server_hpu_cloud.py` — Serveur
- `engine/hpu_v2_complet.py` — HPU Core
- `engine/hpu_v2.py` — HPU léger
- `engine/saas_interface.html` — Interface SaaS
- `engine/GUIDE_HPU_CLOUD.md` — Guide complet

## Statut
✅ Production — Testé et validé