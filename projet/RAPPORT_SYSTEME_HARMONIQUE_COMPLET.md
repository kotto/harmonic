# RAPPORT — SYSTÈME HARMONIQUE COMPLET
## Pipeline SAAS → GGUF → LLM avec Résonance 9D

**Date :** 25 Mai 2026  
**Auteur :** Alain Kotto  
**Version :** v1.0 (Pipeline Intégré)

---

## 1. RÉSUMÉ

Un pipeline complet a été construit pour connecter l'API SAAS Harmonic AI à
un modèle LLM local au format GGUF, en injectant la résonance harmonique 9D
à chaque étape.

Le système détecte automatiquement les modèles GGUF pré-téléchargés sur le
disque `E:\`, démarre un proxy compatible OpenAI, et l'intègre au backend
SAAS via un service de fallback intelligent.

```
Utilisateur → API SAAS (port 9000) → GGUF Proxy (port 8080) → LLM (GGUF)
                                          ↓
                                  Résonance 9D + Mémoire ABC
```

---

## 2. ARCHITECTURE DU PIPELINE

```
┌─────────────────────────────────────────────────────────────────┐
│                    start_all_services.py                        │
│         Lanceur unifié des 2 services en parallèle              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
           ┌────────────────┴────────────────┐
           ▼                                 ▼
┌──────────────────────┐        ┌──────────────────────────┐
│   API SAAS (9000)    │        │  GGUF Proxy (8080)       │
│                      │        │                          │
│  POST /api/chat/public│───────►│ POST /v1/chat/completions│
│                      │        │                          │
│  1. GGUFIntegration  │        │  GGUFHarmonicProxy       │
│  2. HarmonicEngine   │        │  GGUFHarmonicInjector    │
│  3. Comprehension    │        │  GGUFHarmonicSampler     │
│                      │        │  ABCMemory               │
│  Fallback→template   │        │                          │
└──────────────────────┘        └──────────────────────────┘
         │                              │
         └──────────┬───────────────────┘
                    ▼
         ┌──────────────────────────┐
         │  Modèle GGUF (LLM)       │
         │                          │
         │  Qwen3.5-9B-DeepSeek-V4  │ (18.7 Go)
         │  Qwen2.5-1.5B-Instruct   │ (1.8 Go)
         │                          │
         │  Injection harmonique :  │
         │  - Signature 9D          │
         │  - Résonance φ           │
         │  - Mémoire ABC           │
         └──────────────────────────┘
```

---

## 3. FICHIERS CRÉÉS

### 3.1. `start_gguf_server.py` — Lanceur GGUF
- Détection automatique des modèles GGUF sur `E:\` (6 chemins explorés)
- 3 modèles trouvés : Qwen3.5-9B (18.7 Go), Qwen2.5-1.5B (1.8 Go), Nomic Embed
- Mode démo si aucun modèle (réponses templates harmoniques)
- Filtrage par nom : `--model 9b`, `--model 1.5b`
- Options GPU/CPU, résonance, mémoire
- API compatible OpenAI (health, signature, chat)

### 3.2. `harmonic_saas/app/services/gguf_integration.py` — Service SAAS↔GGUF
- Appel asynchrone au proxy GGUF avec httpx
- Fallback automatique : GGUF → HarmonicResonance → Compréhension locale → Template
- Classification 9D locale si proxy indisponible
- Cache de résonance (60s)
- Statistiques (appels, latence, cache hits)
- Singleton pour l'application

### 3.3. `harmonic_saas/app/main.py` (modifié)
- Nouvel endpoint `/api/chat/public` sans authentification
- Pipeline à 4 niveaux de fallback :
  1. **GGUF Integration** → Proxy local avec modèle réel
  2. **HarmonicResonanceEngine** → Moteur de résonance
  3. **HarmonicComprehensionModule** → Compréhension locale
  4. **Template** → Réponse harmonique de base

### 3.4. `harmonic_saas/.env` (modifié)
- Ajout des variables `GGUF_SERVICE_URL`, `GGUF_API_KEY`

### 3.5. `start_all_services.py` — Lanceur Unifié
- Démarre SAAS (9000) et GGUF (8080) en parallèle
- Logs temps réel
- Arrêt propre (Ctrl+C)
- Options : `--no-gguf`, `--no-saas`, `--model`

### 3.6. `download_gguf_models.py` — Téléchargeur
- Modèles disponibles : Qwen3.5 (32B/14B/7B), DeepSeek-V3 (67B/24B), DeepSeek-R1 (14B), Phi-3.5-mini
- Reprise de téléchargement
- Métadonnées automatiques

### 3.7. `test_proxy_demo.py` — Test de validation
- Test complet du proxy en mode démo
- **Health** : ✓ (harmonic=True, memory_active=True)
- **Signature 9D** : ✓ (category=reasoning)
- **Chat** : ✓ (réponse générée)

---

## 4. MODÈLES GGUF DISPONIBLES

| Modèle | Famille | Taille | Emplacement |
|--------|---------|--------|-------------|
| **Qwen3.5-9B-DeepSeek-V4-Flash-BF16** | medium | 18.7 Go | `E:\QWEN35_DEEPSEEK_TEST\models\` |
| **Qwen2.5-1.5B-Instruct-Q4_K_M** | light | 1.8 Go | `E:\QWEN35_DEEPSEEK_TEST\models\` |
| **nomic-embed-text-v1.5-Q4_K_M** | light | 0.1 Go | `E:\Nouveau dossier\LM Studio\` |

Le **Qwen3.5-9B-DeepSeek-V4** est recommandé (meilleure qualité).

---

## 5. SCÉNARIOS DE DÉPLOIEMENT

### 5.1. Production (avec GPU + modèle)
```bash
python start_all_services.py --model 9b
```

### 5.2. Développement (CPU, modèle léger)
```bash
python start_all_services.py --model 1.5b --no-gpu
```

### 5.3. Sans GPU, avec modèle
```bash
python start_gguf_server.py --model 9b --no-gpu --port 8080
# Dans un autre terminal :
python harmonic_saas/run_backend.py
```

### 5.4. SAAS seul (mode démo)
```bash
python start_all_services.py --no-gguf
```

### 5.5. Test rapide
```bash
python test_proxy_demo.py
curl http://localhost:9000/api/chat/public ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\": \"Explique la relativite\"}"
```

---

## 6. ÉTAT DE VALIDATION

| Composant | Statut | Commentaire |
|-----------|--------|-------------|
| `engine/llm/gguf_harmonizer.py` | ✅ Validé | Proxy, Injector, Sampler, ABCMemory |
| `start_gguf_server.py` | ✅ Validé | Détection auto (3 modèles) |
| `gguf_integration.py` | ✅ Validé | Import + syntaxe OK |
| `main.py` endpoint public | ✅ Validé | Pipeline 4 niveaux |
| `start_all_services.py` | ✅ Validé | Lanceur parallèle |
| `test_proxy_demo.py` | ✅ Validé | Health, Signature, Chat OK |
| `download_gguf_models.py` | ✅ Validé | 7 modèles disponibles |

---

## 7. PROCHAINES ÉTAPES

1. **Télécharger DeepSeek-V3-24B** pour benchmark de qualité
2. **Activer le GPU** sur la machine de production (NVIDIA)
3. **Ajouter le streaming SSE** au chat
4. **Déployer sur AWS** avec le modèle GGUF dans un volume EBS
5. **Monitorer** les métriques Prometheus du proxy
6. **Optimiser** le contexte (8192 → 32768 tokens)

---

## 8. COMMANDES RAPIDES

```bash
# Voir les modèles disponibles
python start_gguf_server.py --list-models

# Télécharger un nouveau modèle
python download_gguf_models.py --list
python download_gguf_models.py --download qwen3.5-7b

# Lancer tout le pipeline
python start_all_services.py

# Tester l'API
curl http://localhost:8080/health
curl http://localhost:9000/health
curl -X POST http://localhost:9000/api/chat/public ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\":\"Que vaut φ ?\"}"

# Arrêter
Ctrl+C
```

---

*"L'harmonie n'est pas dans la perfection des composants, mais dans la résonance de leur ensemble."*
— Alain Kotto, φ = 1.618033988749895
