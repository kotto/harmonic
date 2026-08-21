# 🌊 Harmonic HPU Cloud — Guide d'utilisation complet

**Version 2.0 — 14 août 2026**

---

## 1. Démarrage rapide

### 1.1 Lancer le serveur

```bash
cd engine/
python server_hpu_cloud.py
```

Le serveur démarre sur `http://localhost:9100` avec :
- Interface SaaS : `http://localhost:9100/`
- Documentation Swagger : `http://localhost:9100/docs`
- Santé : `http://localhost:9100/health`

### 1.2 Vérifier que tout fonctionne

```bash
curl http://localhost:9100/health
```

Réponse attendue :
```json
{"status":"ok","version":"2.0","hpu_state":{...},"phi":1.618033988749895}
```

---

## 2. Architecture du service

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT                             │
│  curl / Python / JavaScript / Interface SaaS         │
└────────────────────────┬────────────────────────────┘
                         │ HTTP/WS
┌────────────────────────▼────────────────────────────┐
│              HPU CLOUD API (FastAPI)                 │
│  port 9100                                          │
│  /health /api/v1/status /api/v1/theorems             │
│  /api/v1/particles /api/v1/elements /api/v1/gsm8k   │
│  /api/v1/hbit /api/v1/memory /api/v1/infer          │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│              HPU CORE (émulateur V2)                 │
│  hpu_v2_complet.py                                  │
│  3 couches : interférence, mémoire, résonance        │
│  Zéro paramètre — tout dérivé de φ                   │
└─────────────────────────────────────────────────────┘
```

---

## 3. Guide des endpoints

### 3.1 GET /health — État du service

```bash
curl http://localhost:9100/health
```

Retourne : version, statut HPU, valeurs du noyau doré K(0), K(1), K(5), φ, théorèmes.

### 3.2 GET /api/v1/status — Statut détaillé

```bash
curl http://localhost:9100/api/v1/status
```

Retourne : uptime, nombre de patterns en mémoire, statistiques d'apprentissage.

### 3.3 GET /api/v1/theorems — Les 6 théorèmes THU

```bash
curl http://localhost:9100/api/v1/theorems
```

Retourne : T1-T6 avec formules et précisions, et la liste des 9 frontières.

### 3.4 GET /api/v1/particles — Tableau périodique des particules

```bash
curl http://localhost:9100/api/v1/particles
```

Retourne : 18 particules classées avec type, itération k, masse, facteur f.
Prédit : 30 particules supplémentaires.

### 3.5 GET /api/v1/elements — Tableau périodique des éléments

```bash
curl http://localhost:9100/api/v1/elements
curl http://localhost:9100/api/v1/elements?z=6
```

Retourne : 118 éléments chimiques.

### 3.6 GET /api/v1/gsm8k — Raisonnement mathématique

```bash
curl "http://localhost:9100/api/v1/gsm8k?probleme=2+%2B+2"
curl "http://localhost:9100/api/v1/gsm8k?probleme=15+*+3"
```

Retourne : réponse et confiance.

### 3.7 POST /api/v1/hbit — Calcul H-Bit

```bash
curl -X POST http://localhost:9100/api/v1/hbit \
  -H 'Content-Type: application/json' \
  -d '{"operation":"encode","a":"concept"}'
```

Opérations supportées :
| Opération | Description | Paramètres |
|-----------|-------------|------------|
| `encode` | Encoder un concept en H-Bit | `a`: nom du concept |
| `resonate` | Mesure de similarité | `a`, `b`: deux concepts |
| `bind` | Composition de concepts | `a`, `b`: deux concepts |
| `superpose` | Addition harmonique | `a`, `b`: deux concepts |
| `interfere` | Interférence créative | `a`, `b`, `epsilon` (0.15 par défaut) |

### 3.8 POST /api/v1/memory/store — Apprentissage

```bash
curl -X POST http://localhost:9100/api/v1/memory/store \
  -H 'Content-Type: application/json' \
  -d '{"concept":"chat","iterations":5}'
```

L'apprentissage se fait en 3-5 répétitions (seuil dérivé : K(0)+K(1)+K(2) ≈ 1.19).

### 3.9 POST /api/v1/memory/recall — Rappel par résonance

```bash
curl -X POST http://localhost:9100/api/v1/memory/recall \
  -H 'Content-Type: application/json' \
  -d '{"question":"chat"}'
```

Retourne le concept le plus proche + score de confiance. Refus si confiance < seuil.

### 3.10 POST /api/v1/infer — Inférence avec refus calibré

```bash
curl -X POST http://localhost:9100/api/v1/infer \
  -H 'Content-Type: application/json' \
  -d '{"question":"Quelle est la masse de l\'électron ?"}'
```

Zéro hallucination : si la confiance est insuffisante, le service REFUSE de répondre.

---

## 4. Interface SaaS

L'interface web est disponible à `http://localhost:9100/` :

### 4.1 Dashboard
Visualisation des services disponibles :
- 🧠 H-Bit Core ($0.001/10K ops)
- 💾 Golden Memory ($0.01/concept/mois)
- 🔍 Wave Inference ($0.001/query)
- 🎵 HCV Compression ($0.01/GB)
- 🔬 HarmoFold ($0.10/protéine)
- 🧮 GSM8K API ($0.001/problème)
- ⚡ NP Solver ($0.05/problème)
- 📊 Periodic Table (Gratuit)

### 4.2 API Playground
Onglet "API Playground" — interface interactive pour tester tous les endpoints :
1. Sélectionner un endpoint dans la liste déroulante
2. Remplir les paramètres
3. Cliquer sur "Exécuter"
4. La réponse JSON s'affiche en temps réel

### 4.3 Pricing
4 plans tarifaires : Free, Pro ($29/mois), Enterprise ($299/mois), HPC (sur devis).

### 4.4 Documentation
Documentation complète avec exemples curl pour chaque endpoint.

---

## 5. Exemples d'utilisation

### 5.1 Python

```python
import requests, json

API = "http://localhost:9100"

# Santé
r = requests.get(f"{API}/health")
print(r.json())

# H-Bit : encoder un concept
r = requests.post(f"{API}/api/v1/hbit", 
    json={"operation": "encode", "a": "électron"})
print(r.json())

# Apprentissage
r = requests.post(f"{API}/api/v1/memory/store",
    json={"concept": "chat", "iterations": 5})
print(r.json())

# Inférence
r = requests.post(f"{API}/api/v1/infer",
    json={"question": "Quelle est la masse de l'électron ?"})
print(r.json())

# Particules
r = requests.get(f"{API}/api/v1/particles")
print(f"{r.json()['total']} particules classées")

# GSM8K
r = requests.get(f"{API}/api/v1/gsm8k", 
    params={"probleme": "15 + 27"})
print(r.json())
```

### 5.2 JavaScript

```javascript
const API = 'http://localhost:9100';

// Santé
fetch(`${API}/health`)
  .then(r => r.json())
  .then(console.log);

// H-Bit
fetch(`${API}/api/v1/hbit`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({operation: 'encode', a: 'concept'})
}).then(r => r.json()).then(console.log);

// Particules
fetch(`${API}/api/v1/particles`)
  .then(r => r.json())
  .then(data => console.log(`${data.total} particules`));
```

### 5.3 curl

```bash
# Santé
curl http://localhost:9100/health | jq .

# Particules
curl http://localhost:9100/api/v1/particles | jq '.particules[] | {nom, type, masse_eV}'

# Théorèmes
curl http://localhost:9100/api/v1/theorems | jq '.theoremes[] | {id, nom, precision}'

# Apprentissage
curl -X POST http://localhost:9100/api/v1/memory/store \
  -H 'Content-Type: application/json' \
  -d '{"concept":"physique harmonique","iterations":5}'

# Inférence
curl -X POST http://localhost:9100/api/v1/infer \
  -H 'Content-Type: application/json' \
  -d '{"question":"Quel est le théorème T6 ?"}'
```

---

## 6. Vérification des liens

Tous les endpoints ont été vérifiés fonctionnels :

```
✅ GET  /                                        → 200 (23 916 bytes)  Page d'accueil SaaS
✅ GET  /health                                  → 200 (472 bytes)     État du service
✅ GET  /api/v1/status                           → 200 (147 bytes)     Statut HPU
✅ GET  /api/v1/theorems                         → 200 (856 bytes)     6 théorèmes
✅ GET  /api/v1/particles                        → 200 (1 449 bytes)   18 particules
✅ GET  /api/v1/elements                         → 200 (403 bytes)     118 éléments
✅ GET  /api/v1/gsm8k?probleme=2+2               → 200 (52 bytes)      Raisonnement
✅ POST /api/v1/hbit                             → 200 (308 bytes)     Calcul H-Bit
✅ POST /api/v1/memory/store                     → 200 (50 bytes)      Apprentissage
✅ POST /api/v1/memory/recall                    → 200 (80 bytes)      Rappel
✅ POST /api/v1/infer                            → 200 (80 bytes)      Inférence
✅ GET  /docs                                    → 200 (950 bytes)     Swagger UI
```

---

## 7. Structure des fichiers

```
engine/
├── server_hpu_cloud.py        ← Serveur API (FastAPI, port 9100)
├── saas_interface.html        ← Interface SaaS complète
├── hpu_v2_complet.py          ← HPU V2 émulateur (3 couches)
├── hpu_v2.py                  ← HPU V2 léger
├── wave_math.py               ← Arithmétique ondulatoire
├── wave_lang.py               ← Langage ondulatoire (13 primitives)
├── wave_code_generator.py     ← Génération de code
├── wave_reasoning.py          ← Raisonnement par résonance
├── Dockerfile.hpu             ← Container Docker
├── docker-compose.hpu.yml     ← Infrastructure complète
├── index.html                 ← Site vitrine
├── THEORIE_HARMONIQUE_UNIVERSELLE.md  ← Document fondateur
├── TABLEAU_PERIODIQUE_PARTICULES_THU.md ← Particules
├── THEOREME_T6_MODULO7.md     ← Théorème T6
└── data/benchmarks/           ← 12 rapports de piste
```

---

## 8. Dépannage

| Problème | Cause | Solution |
|----------|-------|----------|
| `Connection refused` | Serveur non démarré | `python server_hpu_cloud.py` |
| `Port 9100 already in use` | Ancienne instance | `taskkill /F /PID <PID>` |
| `500 Internal Server Error` | Erreur mémoire | Vérifier `hpu_v2_complet.py` |
| `422 Unprocessable Entity` | Payload invalide | Vérifier le format JSON |
| Interface lente | Premier chargement | Attendre le démarrage du HPU |

---

> **« Une seule équation. Zéro paramètre libre. Toute la matière. »**
> 
> D^{1/φ}[Ψ] = G[Ψ] — φ = 1.618033988749895
> 
> 14 août 2026 — T6 modulo 7 · E1b fermé · F5 fermé · Carte des particules