# 🌊 Raisonnement Ondulatoire + Plan d'Action

**Document de Conception — 24 juillet 2026**
**Basé sur :** `wave_logic.py`, `conscious_critic.py`, `conscious_creator.py`, `feedback_loop.py`

---

## 1. Le raisonnement ondulatoire : fondements

### 1.1 Principe

> **Raisonner, c'est faire interférer des ondes.** Un concept est une onde ψ.
> Deux concepts qui résonnent (cohérence positive) se renforcent.
> Deux concepts qui s'opposent (interférence destructive) s'annulent.
> La logique émerge de la superposition, pas de règles symboliques.

### 1.2 Les 4 opérations primitives (déjà implémentées dans `wave_logic.py`)

| Opération | Math | Signification logique |
|---|---|---|
| **ENCODE** | texte → ψ ∈ ℂ⁵¹² | Transformer un concept en onde |
| **INTERFERE** | Re(⟨ψ_a\|ψ_b⟩) | Mesurer la cohérence entre deux idées |
| **BIND** | ψ_a ⊛ ψ_b (convolution ⊛) | Composer deux concepts (« A est B ») |
| **UNBIND** | ψ_ab ⊗ ψ_a (corrélation ⊗) | Extraire une relation (« quel B pour A ? ») |

### 1.3 Les 7 types de raisonnement qui émergent

| Type | Opération ondulatoire | Exemple |
|---|---|---|
| **Syllogisme** | BIND + cohérence | « Socrate est homme, hommes sont mortels → Socrate mortel » |
| **Modus Ponens** | UNBIND | « Si A alors B. A est vrai → B est vrai » |
| **Analogie** | Arithmétique vectorielle | « A:B :: C:? » → ψ_? = ψ_C ⊗ ψ_B ⊛ ψ_A |
| **Contradiction** | Interférence destructive | « A et non-A » → cohérence < 0 |
| **Induction** | Clustering de phase | « Tous les cygnes observés sont blancs → tous les cygnes sont blancs » |
| **Transitivité** | Propagation cohérente | « A→B, B→C → A→C » |
| **Abduction** | UNBIND inversé | « Effet observé, cause probable ? » |

### 1.4 La validation par φ (conscious_critic.py)

Le conscient critique évalue chaque conclusion sur 5 axes :

$$\text{Beauté} = \left|\frac{\text{cohérence}}{\text{nouveauté}} - \varphi\right|$$

- Trop cohérent → banal (déjà-vu)
- Trop nouveau → chaos (inintelligible)
- **φ-équilibré** → SUBLIME (reconnaissable ET surprenant)

---

## 2. Ce qui existe DÉJÀ dans le workspace

```
wave_logic.py          (26 KB) — 7 types de raisonnement, 4 opérations primitives
conscious_critic.py    (25 KB) — Validation φ, 5 axes d'évaluation
conscious_creator.py   (32 KB) — Génération créative contrôlée
conscious_engine.py    (13 KB) — Orchestration conscient/inconscient
conscious_intelligence.py (14 KB) — Boucle complète
feedback_loop.py       (15 KB) — Apprentissage par feedback
wave_debugger_v6.py    (10 KB) — Diagnostic ondulatoire
```

**Total : ~135 KB de code de raisonnement ondulatoire.**

### Ce qui MANQUE

```
wave_logic.py ──❌── HWAT (sélectivité)
     ↑                    ↑
 Fonctionne           Fonctionne
 (HRR + spectral)    (×5 sélectivité)
```

Le `WaveLogic` utilise l'ancien encodeur HRR. Il n'a pas :
- La sélectivité fine de HWAT (×5)
- Les hologrammes spécialisés (14 domaines)
- La FFT adaptative
- Le routeur spectral

---

## 3. Plan d'action : combler les points faibles

### Point faible 1 : RAISONNEMENT (1% au benchmark)

**Cause :** Le routeur `intent_router` ne sait pas router les questions de raisonnement. `wave_logic.py` existe mais n'est pas connecté au pipeline principal.

**Solution :** Créer `reasoning_router.py` — un adaptateur qui :
1. Détecte les questions de raisonnement (mots-clés : « si...alors », « donc », « déduire », « syllogisme »)
2. Appelle `WaveLogic.solve(prémisses, question)`
3. Valide avec `ConsciousCritic`
4. Retourne la conclusion

**Impact estimé :** Raisonnement 1% → **60-80%** (wave_logic couvre déjà syllogisme, modus ponens, analogie, transitivité)

**Temps :** 2-3 heures (le code existe, juste l'intégration)

### Point faible 2 : CODE (7% en questions courtes)

**Cause :** Les templates frontend ne sont pas appelés pour les questions courtes.

**Solution :** Améliorer `intent_router` pour qu'il reconnaisse les questions courtes :
1. Ajouter un fallback « mot-clé → template » quand la question fait < 5 mots
2. Connecter l'hologramme CODE (PPL 6.9, 29K patterns) comme source de patterns

**Impact estimé :** Code 7% → **60-70%** (proche du 68% du benchmark naturel)

**Temps :** 1-2 heures

### Point faible 3 : MATHS (45% en questions courtes)

**Cause :** Le CAS SymPy n'est pas appelé pour les questions sans structure de phrase.

**Solution :** Détection de pattern mathématique dans les questions courtes :
1. Regex pour détecter les opérations (« 7×8 », « x^2 », « ∫ »)
2. Router directement vers le CAS sans passer par le NLP

**Impact estimé :** Maths 45% → **95-100%**

**Temps :** 1 heure

### Point faible 4 : HWAT non intégré au routeur

**Cause :** Le routeur (`intent_router`) utilise l'ancien pipeline HarmonicAI, pas HWAT.

**Solution :** Brancher HWAT comme encodeur par défaut dans le routeur :
1. `route(question)` → HWAT encode → sélection du handler
2. Les hologrammes fournissent le contexte spécifique au domaine
3. La FFT adaptative améliore l'extraction de caractéristiques

**Impact estimé :** +5-10% sur toutes les catégories

**Temps :** 3-4 heures

---

## 4. Architecture cible : le Cerveau Harmoniq

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CERVEAU HARMONIQ — Architecture finale           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  QUESTION ──► ENCODEUR HWAT (ψ = A·e^{iφ}, sélectivité ×5)         │
│                     │                                                │
│                     ▼                                                │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    ROUTEUR SPECTRAL                           │    │
│  │  cos_sim(ψ_question, centroïdes) → top-K domaines           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│           │                │                │                        │
│           ▼                ▼                ▼                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │    MATHS     │ │     CODE     │ │ RAISONNEMENT │                │
│  │  CAS SymPy   │ │  Templates   │ │  WaveLogic   │                │
│  │  + HWAT      │ │  + Hologram  │ │  + Critic    │                │
│  │  → 100%      │ │  → 70%       │ │  → 70%       │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                      │
│                     ▼                                                │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    ASSEMBLEUR                                 │    │
│  │  WaveStyler (prose) + ConsciousCritic (validation φ)         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                     │                                                │
│                     ▼                                                │
│               RÉPONSE (exacte, stylée, validée)                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Projection LM Arena après corrections

| Catégorie | Avant | Après corrections | Avec HWAT intégré |
|---|---|---|---|
| **Maths** | 45% (questions courtes) | **95%** | **100%** |
| **Code** | 7% | **65%** | **75%** |
| **Raisonnement** | 1% | **60%** | **75%** |
| **Global** | 18% | **73%** | **83%** |
| **Elo estimé** | ~1358 | ~1580 | **~1680** |
| **Rang** | 13e | 5e-8e | **2e-4e** |

---

## 6. Ordre de priorité

| Priorité | Action | Impact | Effort |
|---|---|---|---|
| **P1** | Connecter `wave_logic.py` au routeur (raisonnement) | +60% raisonnement | 2-3h |
| **P2** | Détection maths questions courtes → CAS | +50% maths | 1h |
| **P3** | Détection code questions courtes → templates | +58% code | 1-2h |
| **P4** | Intégrer HWAT comme encodeur du routeur | +5-10% global | 3-4h |
| **P5** | ConsciousCritic → validation automatique | Qualité | 2h |
| **P6** | Feedback loop → apprentissage continu | Long terme | 4h |

**Total estimé : 13-16 heures pour le score cible de 83% (rang 2e-4e).**

---

## 7. Le raisonnement ondulatoire vs le raisonnement classique

| | Raisonnement classique (LLM) | Raisonnement ondulatoire (WaveLogic) |
|---|---|---|
| **Représentation** | Tokens + probabilités | Ondes complexes ψ |
| **Inférence** | Probabiliste (next-token) | Déterministe (interférence) |
| **Explicabilité** | Boîte noire | Cohérence mesurable (cos Δφ) |
| **Hallucination** | Fréquente | Impossible (basé sur ψ encodés) |
| **Validation** | Aucune (confiance statistique) | φ-balance (cohérence/nouveauté) |
| **Apprentissage** | Gradient descent | Feedback conscient (seuils adaptatifs) |

**Le raisonnement ondulatoire n'est pas une simulation du raisonnement — c'est le raisonnement lui-même, exprimé dans le langage des ondes. L'interférence EST la logique.**

---
*Document de conception — Prêt pour implémentation*
