# 🎓 EDUCAL KA — Admin Server

Serveur d'administration de l'écosystème **EDUCAL KA** (éducation numérique harmonique).
Jumeau pédagogique de `vital-ka/admin-server` — mêmes patterns, mêmes routes métier.

**Port : 8001** · FastAPI · SQLite local (PostgreSQL en prod) · JWT

## Routage métier (miroir de VITAL KA)

| VITAL KA (santé) | EDUCAL KA (éducation) | Routes |
|---|---|---|
| `auth` (médecins) | `auth` (élèves, professeurs, parents, admin) | `/api/v1/auth/register\|login\|me` |
| `doctors` | `teachers` (matières, écoles, validation) | `/api/v1/teachers` |
| `records` (dossiers) | `learners` (carnet d'apprentissage) | `/api/v1/learners/*` |
| `versions` (contenu) | `curriculum` (programme + versionnage des unités) | `/api/v1/curriculum/*` |
| `teleconsult` | `tutoring` (sessions élève-professeur) | `/api/v1/tutoring/sessions` |
| `admin` | `admin` (stats établissement) | `/api/v1/admin/stats` |

## Démarrage

```bash
cd educal-ka/admin-server
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8001
```

## Synchronisation du programme (clé du jumeau)

```bash
# Importe le catalogue des unités éducatives du moteur KA
# (détecte engine/ automatiquement, lit data/educal_units/)
curl -X POST http://localhost:8001/api/v1/curriculum/sync \
     -H "Authorization: Bearer <token prof/admin>"
```

Toute unité modifiée côté moteur est **versionnée** (version+1) ici —
même mécanique que le versionnage des contenus médicaux de VITAL KA.

## Boucle complète

1. Le moteur KA (`ka_server.py:8765`) sert les unités : `/api/educal/units`, `/api/educal/quiz/submit`, `/api/educal/exercise/generate`
2. L'admin server (8001) gère l'établissement : comptes, professeurs, carnets des élèves, programme, tutorat
3. Le carnet élève vit des deux côtés : `data/educal_progress/` (moteur) + `learners` (établissement) — synchronisés via `/learners/progress/sync`

## Configuration

Copier `.env.example` → `.env` (clé JWT à changer en production).
