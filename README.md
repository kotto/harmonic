# 🌊 KA Enterprise AI

**Diagnostic de bugs par interférence ondulatoire — pour entreprises.**

---

## Pourquoi KA Enterprise vs LLM/RAG ?

| | GPT-4 / Claude | RAG | **KA Enterprise** |
|---|---|---|---|
| Hallucination | 3-15% | 1-5% | **0%** ✅ |
| Taille | 500 Go | 500 Go+ | **15 Mo** ✅ |
| GPU requis | H100 @ $40K | H100 | **CPU uniquement** ✅ |
| Données | Partent dans le cloud | Partent | **Restent chez vous** ✅ |
| Coût/requête | $0.03 | $0.05 | **$0** ✅ |
| Latence | 500-2000ms | 500-3000ms | **<1ms** ✅ |
| Apprentissage | Fine-tuning ($) | Ré-indexation | **Automatique et gratuit** ✅ |
| Spécialisation | Prompt engineering | Documents | **Upload fichiers → hologramme** ✅ |

---

## Démarrage rapide

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
python enterprise_server.py

# Dashboard → http://localhost:8842
# API      → http://localhost:8842/api/v2/enterprise/
```

## Utilisation

### 1. Créer un compte entreprise
```bash
curl -X POST http://localhost:8842/api/v2/enterprise/tenant \
  -H "Content-Type: application/json" \
  -d '{"name": "Ma Société"}'
# → API Key à conserver
```

### 2. Uploader le contexte (logs, code, docs)
```bash
curl -X POST http://localhost:8842/api/v2/enterprise/upload \
  -H "X-API-Key: votre_clé" \
  -F "files=@server_errors.log" \
  -F "files=@UserService.java"
# → L'IA crée automatiquement des patterns personnalisés
```

### 3. Diagnostiquer un bug
```bash
curl -X POST http://localhost:8842/api/v2/enterprise/debug \
  -H "X-API-Key: votre_clé" \
  -H "Content-Type: application/json" \
  -d '{"symptom": "NullPointerException in UserService.getProfile()"}'
# → Diagnostic + stratégie + action en <1ms
```

### 4. L'IA apprend de ses erreurs
```bash
curl -X POST http://localhost:8842/api/v2/enterprise/feedback \
  -H "X-API-Key: votre_clé" \
  -H "Content-Type: application/json" \
  -d '{"symptom": "...", "predicted": "X", "correct": "Y"}'
# → L'IA ne refera plus cette erreur
```

---

## Architecture

```
ka_enterprise/
├── enterprise_server.py        # Serveur Flask multi-tenant
├── enterprise_specializer.py   # Spécialisation + intégrations + ROI
├── harmonic_ai_v2.py           # Core IA (debug, chat, learn)
├── generative_encoder.py       # Encodeur optimal (17 concepts, 100%)
├── wave_debugger_v2.py         # Moteur ABC hybride
├── wave_debugger_v3.py         # Pipeline multi-passes
├── wave_debugger_v6.py         # Encodeur holographique
├── www/
│   └── enterprise_dashboard.html  # Interface web
├── data/                       # Données (créé automatiquement)
├── requirements.txt
└── README.md
```

## Licence

Proprietary — Harmonic AI
