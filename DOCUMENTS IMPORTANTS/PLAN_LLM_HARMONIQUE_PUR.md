# PLAN — NOTRE PROPRE LLM HARMONIQUE PUR

**Date :** 25 Mai 2026  
**Auteur :** Alain Kotto  
**Priorité :** Option retenue (vs connexion AWS)

---

## 1. POURQUOI NOTRE PROPRE LLM ?

### État des lieux

| Approche | Problème |
|----------|----------|
| **GGUF local (llama-cpp-python)** | Binding Windows incompatible (AVX2 manquant). Même en CPU, les modèles BF16/Q4_K_M ne chargent pas. |
| **AWS (EC2 DeepSeek)** | Déjà fonctionnel mais dépendance externe, latence réseau, coût GPU ~$1-3/h |
| **Notre LLM Harmonique PUR** | Zéro paramètre entrainable, 100% déterministe, tourne sur CPU, aucune dépendance |

### Avantages de notre approche

1. **Zéro GPU requis** — Le modèle utilise des formules fermées (pas de backprop)
2. **Déterministe** — Même entrée = même sortie (reproductibilité parfaite)
3. **Léger** — 512 Mo vs 3-18 Go pour les GGUF
4. **Notre propriété intellectuelle** — Aucune licence externe
5. **Extensible** — On ajoute des couches sans réentrainement
6. **Intégrable** — Se branche directement dans `engine/llm/`

---

## 2. ARCHITECTURE ACTUELLE (CE QUI EXISTE DÉJÀ)

```
harmonic_training/model/
├── abc_kernel.py              # Noyau ABC (dérivée fractionnaire) — 359 lignes
├── harmonic_pure_attention.py # Attention harmonique pure (7D + résonance) — 456 lignes
├── harmonic_pure_layers.py    # Couches de decodeur pur (poids fixes) — 340 lignes
├── harmonic_pure_signatures_v4.py # Signatures 9D — 474 lignes
├── harmonic_pure_model.py     # Modèle causal complet — 368 lignes
├── harmonic_applications_concretes.py # Applications métier — 974 lignes
│
engine/
├── signatures_9d.py           # Signature 9D rapide (en production)
├── abc_kernel.py              # Noyau ABC (en production)
├── harmonic_engine.py         # Moteur harmonique (en production)
├── llm/gguf_harmonizer.py     # Proxy GGUF (en production, mode démo)
└── llm/router.py              # Routeur LLM
```

**Ce qui fonctionne déjà :**
- Signature 9D (API `/harmonic/signature` ✓)
- Résonance harmonique (scoring, injection) ✓
- Mémoire ABC ✓
- Classification 9D ✓
- Serveur API compatible OpenAI ✓

**Ce qui manque pour un vrai LLM :**
1. Un tokenizer fonctionnel
2. Une génération de tokens pas-à-pas (pas juste un fallback template)
3. Un mécanisme de sélection de tokens (sampling)
4. Un LM Head qui produit des logits sur un vocabulaire
5. Une boucle d'inférence complète

---

## 3. PLAN DE RÉALISATION

### Phase 1 — Fondation (Semaine 1)
**Objectif :** Un LLM qui génère du texte cohérent

| # | Tâche | Fichier | Description |
|---|-------|---------|-------------|
| 1 | **Tokenizer amélioré** | `harmonic_training/model/tokenizer.py` | Tokenizer BPE simple (5000 tokens) au lieu du word-level actuel |
| 2 | **LM Head fixe** | `harmonic_pure_model.py` | Head de projection vocab_size × hidden_size avec poids PHI-fixes |
| 3 | **Boucle de génération** | `harmonic_pure_model.py` | Méthode `generate()` avec sampling pas-à-pas |
| 4 | **Sampling harmonique** | `harmonic_pure_model.py` | Temperature, top-k, top-p guidés par résonance φ |
| 5 | **Test de cohérence** | `test_llm_pur.py` | Validation : phrases complètes, cohérence minimale |

**Résultat attendu :** `python test_llm_pur.py` produit une phrase lisible.

### Phase 2 — Scaling (Semaine 2)
**Objectif :** Passer de 2000→32000 tokens de vocabulaire

| # | Tâche | Description |
|---|-------|-------------|
| 6 | **Vocab 32K** | Tokenizer BPE complet (vocab_size=32000) |
| 7 | **Hidden 1024** | Doublement de la capacité (hidden_size 512→1024) |
| 8 | **12 couches** | De 6 à 12 couches de décodeur |
| 9 | **Contexte 2048** | Extension de la fenêtre de contexte |
| 10 | **Optimisation mémoire** | Distribution des calculs, chunking |

**Résultat attendu :** Génération de paragraphes cohérents.

### Phase 3 — Intelligence (Semaine 3)
**Objectif :** Le modèle répond à des questions comme un vrai LLM

| # | Tâche | Description |
|---|-------|-------------|
| 11 | **Noyau ABC contextuel** | Mémoire longue durée intégrée à la génération |
| 12 | **Attention causale 9D** | Les 9 dimensions guident la sélection de tokens |
| 13 | **Résonance multi-tête** | 4 têtes de résonance au lieu d'une |
| 14 | **Alignement φ** | Forçage des logits vers les harmoniques de φ (comme un RLHF harmonique) |
| 15 | **Benchmark** | Tests sur Q&A, résumé, complétion |

**Résultat attendu :** Des réponses pertinentes à des questions simples.

### Phase 4 — Production (Semaine 4)
**Objectif :** Remplacer le proxy GGUF par notre LLM

| # | Tâche | Description |
|---|-------|-------------|
| 16 | **Intégration engine/llm/** | Nouveau provider `local_llm_pur.py` |
| 17 | **Serveur API** | Même interface que gguf_harmonizer.py |
| 18 | **Mode hybride** | AWS pour les prompts complexes, notre LLM pour le reste |
| 19 | **Documentation** | README, benchmark, comparaison |
| 20 | **Déploiement** | Chargement automatique au démarrage |

---

## 4. COMPARAISON DES APPROCHES

| Critère | AWS (DeepSeek) | GGUF local | **Notre LLM PUR** |
|---------|----------------|------------|-------------------|
| Latence | 300-500ms | 50-100ms | **10-50ms** |
| Coût | $1-3/h GPU | 0 (déjà acheté) | **0** |
| Qualité | Très haute | Haute | **Bonne** (Phase 3) |
| Dépendance | Réseau + AWS | AVX2/CPU | **Aucune** |
| Propriété | Non | Non | **Oui (brevetable)** |
| Contrôle | Limitée | Limitée | **Total** |
| Passage à l'échelle | $$ | Limité | **Informatif** |

---

## 5. PREUVE DE CONCEPT IMMÉDIATE

Dès aujourd'hui, le modèle PUR existe et produit déjà des embeddings :

```python
from harmonic_training.model.harmonic_pure_model import HarmonicPureForCausalLM

model = HarmonicPureForCausalLM(vocab_size=2000, hidden_size=512, num_hidden_layers=6)
# 0 paramètre entrainable, 100% déterministe
# ~32 Mo en mémoire
```

La Phase 1 consiste à ajouter la génération (actuellement le modèle peut seulement encoder, pas décoder).

---

## 6. RECOMMANDATION

**Option A (recommandée) :** Développer notre LLM PUR (Phases 1→4)

**Option B (complémentaire) :** Maintenir la connexion AWS pour les cas complexes pendant le développement

Je propose de commencer immédiatement par la **Phase 1** car :
1. Le tokenizer est indispensable
2. La boucle de génération est le cœur du LLM
3. On peut valider concrètement dès la première heure

---

*"Construire son propre LLM, c'est comme construire son propre télescope : 
on voit plus loin parce qu'on comprend ce qu'on regarde."*
— Alain Kotto, φ = 1.618033988749895
