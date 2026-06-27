# 🏗️ Architecture des Serveurs KA Phone

## Serveur Canonique

| Fichier | Port | Endpoint | Rôle |
|---------|:----:|----------|------|
| **`unified_server.py`** | **8420** | `/api/ask` | **Serveur canonique** — Pipeline complet (~30 modules) |

**Démarrage canonique :**
```bash
cd ka_phone && python unified_server.py
# → http://localhost:8420
```

---

## Serveurs Legacy (conservés pour référence)

| Fichier | Port | Endpoint | Rôle |
|---------|:----:|----------|------|
| `ka_phone_server.py` | 8900 | `/api/chat` | v3 — Qwen 2.5-3B GGUF + MGH bigrammes + Hologramme |
| `ka_phone_harmonic_server.py` | 8900 | `/api/chat` | v4 — Moteur Harmonique + Calculateur SymPy + DeepSeek fallback |
| `ka_phone_unified_server.py` | 8900 | `/api/chat` | v5 — Fusion v3 (Qwen+MGH) + v4 (Harmonique+Calculateur) |
| `light_server.py` | 8420 | `/api/ask` | Version allégée — ParametricKB + FrequencyReasoner uniquement |

**Note importante :** Ces serveurs utilisent le port 8900 avec `/api/chat`. Ils sont **conservés pour référence et tests isolés** mais ne sont pas le serveur de production.

---

## Pipeline de Réponse (unified_server.py)

```
Question entrante
    │
    ├─ 0. InputSanitizer — normaliser le prompt (accents, synonymes)
    ├─ 1. IntentRouter — détecter commandes, rappels, salutations
    ├─ 2. PhoneActions — exécuter actions téléphone (si commande)
    ├─ 3. Rappels — gérer les reminders
    ├─ 4. Salutations — gérer les greetings contextuels
    │
    ├─ 5. AI Engine (question/réponse) :
    │   ├─ 5a. MaatGuard — vérifier éthique AVANT
    │   ├─ 5b. DomainRouter — classifier le domaine (11 domaines)
    │   ├─ 5c. NewsService — actualités
    │   ├─ 5d. QuantumCreativeWriter — poèmes, histoires (bypass créatif)
    │   ├─ 5e. WaveResonanceEngine — résonance ondulatoire
    │   ├─ 5f. QuickFacts — faits rapides (<1ms, 1000+ faits)
    │   ├─ 5g. ParametricKB — règles mathématiques (50+ règles)
    │   ├─ 5h. FrequencyReasoner — raisonnement par fréquence
    │   ├─ 5i. KnowledgeBase — hologramme, SOPC, concepts KA
    │   ├─ 5j. QA Matcher — 50K+ paires question/réponse
    │   ├─ 5k. Translator — traduction EN↔FR
    │   ├─ 5l. MedicalResonator — diagnostic ondulatoire
    │   ├─ 5m. HybridWriter — écriture avec templates
    │   └─ 5n. Fallback — réponse polie si rien n'a matché
    │
    ├─ 6. MaatGuard — réviser la réponse APRÈS
    ├─ 7. FeedbackLearner — apprendre des interactions
    ├─ 8. ConsciousnessController — vérifier cohérence finale
    │
    └─ Réponse finale
```

---

## Comparaison des Serveurs

| Fonctionnalité | `unified_server` (canonique) | `ka_phone_server` (legacy v3) | `ka_phone_harmonic` (legacy v4) | `light_server` |
|----------------|:---:|:---:|:---:|:---:|
| QuickFacts | ✅ | ❌ | ❌ | ❌ |
| ParametricKB | ✅ | ❌ | ❌ | ✅ |
| DomainRouter (11 domaines) | ✅ | ❌ | ✅ | ❌ |
| MaatGuard (éthique) | ✅ | ❌ | ❌ | ❌ |
| WaveResonance | ✅ | ❌ | ❌ | ❌ |
| Qwen LLM local | ❌ | ✅ | ❌ | ❌ |
| MGH bigrammes | ❌ | ✅ | ❌ | ❌ |
| Moteur Harmonique | ❌ | ❌ | ✅ | ❌ |
| Calculateur SymPy | ❌ | ❌ | ✅ | ❌ |
| DeepSeek fallback | ❌ | ❌ | ✅ | ❌ |
| Translator EN↔FR | ✅ | ❌ | ❌ | ❌ |
| Medical Resonator | ✅ | ❌ | ❌ | ❌ |
| Quantum Creative | ✅ | ❌ | ❌ | ❌ |
| Speech STT/TTS | ✅ | ❌ | ❌ | ❌ |
| News Service | ✅ | ❌ | ❌ | ❌ |
| Feedback Learner | ✅ | ❌ | ❌ | ❌ |
| Consciousness Control | ✅ | ❌ | ❌ | ❌ |
| **Nombre de modules** | **~30** | **3** | **5** | **2** |

---

## Points d'Entrée UI

| UI | Fichier | Appel API | Compatible canonique ? |
|----|---------|-----------|:---:|
| Chat overlay | `index.html` → `www/ka-ui-new.js` | `/api/ask` (port 8420) | ✅ Oui |
| App complète | `www/app.html` | `/api/ask` (port 8420) | ✅ Oui |
| Home | `www/home.html` | (interface uniquement) | ✅ Oui |
| Lockscreen | `www/lockscreen.html` | (interface uniquement) | ✅ Oui |

---

*Documentation générée le 9 Juin 2026 — Standardisation de l'architecture*