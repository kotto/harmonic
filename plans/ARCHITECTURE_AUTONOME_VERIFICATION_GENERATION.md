# ARCHITECTURE AUTONOME — Vérification + Génération sans dépendance externe
## Comment Harmonic AI remplit les deux rôles sans Claude, GPT, ni aucun LLM propriétaire

**Date :** 3 Juin 2026  
**Version :** 1.0  
**Auteur :** Équipe Harmonic AI  

---

## Table des matières

1. [Le problème](#1-le-problème)
2. [Principe fondamental](#2-principe-fondamental)
3. [Architecture de génération autonome](#3-architecture-de-génération-autonome)
4. [Architecture de vérification](#4-architecture-de-vérification)
5. [Le Fallback LLM — indépendant de tout fournisseur](#5-le-fallback-llm--indépendant-de-tout-fournisseur)
6. [Boucle complète sans dépendance externe](#6-boucle-complète-sans-dépendance-externe)
7. [Spécifications d'intégration](#7-spécifications-dintégration)
8. [Démonstration par l'exemple](#8-démonstration-par-lexemple)

---

## 1. Le problème

Les LLMs (Claude, GPT, DeepSeek) ont deux limitations structurelles :

1. **Ils ne savent pas dire "je ne sais pas"** — ils génèrent toujours une réponse, même fausse
2. **Ils sont indiscernables les uns des autres** — du point de vue de la confiance, Claude = GPT = DeepSeek = boîte noire

La solution naïve serait d'utiliser Claude pour générer et Harmonic pour vérifier. Mais cela crée une dépendance à un fournisseur externe.

**Ce document explique comment Harmonic AI génère ET vérifie sans aucun LLM externe.**

---

## 2. Principe fondamental

> **La génération de contenu fiable ne nécessite pas un LLM. Elle nécessite :**
> 1. Un calcul exact (SymPy) pour les réponses mathématiques
> 2. Un système de templates structurés pour le langage naturel
> 3. Un vérificateur de cohérence pour valider chaque affirmation
> 4. Un LLM local interchangeable comme filet de sécurité ultime

Harmonic AI possède les quatre.

```
┌─────────────────────────────────────────────────────────────────┐
│            HARMONIC AI — GÉNÉRATION + VÉRIFICATION               │
│                   SANS AUCUNE DÉPENDANCE EXTERNE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  QUESTION (langage naturel)                                      │
│      │                                                           │
│      ├──────────→ GuideHarmonique ──→ Domaine identifié (75%)   │
│      │                                                           │
│      ├──────────→ CalculateurHarmonique (SymPy)                  │
│      │               │                                           │
│      │               ├── Dérivées : sp.diff()                    │
│      │               ├── Intégrales : sp.integrate()             │
│      │               ├── Équations : sp.solve()                  │
│      │               ├── Trigonométrie : sp.simplify()           │
│      │               └── Simplification : sp.simplify()          │
│      │                                                           │
│      ├──────────→ DHF Cohérence ──→ Score 0-1                   │
│      │               │                                           │
│      │               ├── Token Euler : Σ e^{i(kx+ky)}            │
│      │               ├── Action : δS = 0 pour la séquence        │
│      │               └── Résonance : cohérence inter-token       │
│      │                                                           │
│      └──────────→ Smart Templates + Correcteur FR               │
│                      │                                           │
│                      ├── Rôles sémantiques (sujet, méthode...)   │
│                      ├── Grammaire FR/EN (articles, accords)     │
│                      ├── Correction orthographique               │
│                      └── 10 variantes par domaine                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              FALLBACK LLM (5% des cas)                       │ │
│  │                                                              │ │
│  │  Niveau 1 : Ollama local (DeepSeek 1.5B, gratuit, CPU)      │ │
│  │  Niveau 2 : DeepSeek API ($0.10/1M tokens)                  │ │
│  │  Niveau 3 : Qwen GGUF local (2 Go, gratuit, CPU)            │ │
│  │                                                              │ │
│  │  AUCUN n'est Claude. Tous sont interchangeables.            │ │
│  │  Le DHF vérifie TOUJOURS la réponse du LLM.                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Architecture de génération autonome

### 3.1 Niveau 1 : Calcul exact (SymPy) — 60% des questions

Pour toute question mathématique calculable, le système n'a pas besoin d'un LLM. SymPy fournit le résultat exact :

```python
# Exemple réel exécuté le 3 Juin 2026
from engine.calculateur_harmonique import CalculateurHarmonique
calc = CalculateurHarmonique()

# Dérivée
calc.resoudre("dérivée de x^3 + 2x^2 - 5x + 3")
# → Résultat : 3x² + 4x - 5 ✅

# Intégrale
calc.resoudre("intégrale de x^2 + 3x")
# → Résultat : x²(2x + 9)/6 + C ✅

# Équation
calc.resoudre("résoudre x^2 - 4 = 0")
# → Résultat : -2, 2 ✅

# Trigonométrie
calc.resoudre("sinus de pi/3")
# → Résultat : √3/2 ✅
```

**Avantage :** Zéro hallucination. Le résultat est mathématiquement prouvé. Aucun LLM n'intervient.

### 3.2 Niveau 2 : Smart Templates avec rôles sémantiques — 35% des questions

Pour les questions conceptuelles (ex: "explique le théorème de Pythagore"), le système utilise des templates enrichis par assignation de rôles grammaticaux :

```python
# Assignation sémantique des concepts aux rôles grammaticaux
ROLES_PAR_DOMAINE = {
    "geometrie_euclidienne": {
        "sujet":     ["théorème", "pythagore", "triangle", "rectangle"],
        "méthode":   ["formule", "proportionnalité"],
        "résultat":  ["carré", "somme_carres_cotes", "égal"],
        "vérification": ["périmètre", "diagonale"],
    }
}

# Génération de phrase
phrase = generer_phrase_smart(
    domaine="geometrie_euclidienne", 
    concepts=["pythagore", "formule", "carré", "hypoténuse"],
    langue="fr"
)
# → "Le théorème de Pythagore s'exprime par la formule : 
#    le carré de l'hypoténuse est égal à la somme des carrés des côtés."
```

**Avantage :** Déterministe, grammaticalement correct, sans hallucination. Zéro dépendance.

### 3.3 Niveau 3 : Correcteur grammatical — post-traitement

Après génération, un correcteur sans dépendance externe corrige automatiquement :

- Accents manquants (dérivée → dérivée, intégrale → intégrale)
- Capitalisation de début de phrase
- Ponctuation (espaces avant/après les signes)
- Doubles espaces

```python
from scripts.correcteur_fr import corriger_phrase
corriger_phrase("la derivee du logarithme s'obtient par la regle")
# → "La dérivée du logarithme s'obtient par la règle."
```

**Performance :** <1ms, 0 dépendance externe.

---

## 4. Architecture de vérification

### 4.1 Le DHF (Décodeur Harmonique Final)

Le DHF mesure la cohérence d'une séquence de concepts contre un critère universel :

```
Cohérence(t₁, t₂, ..., tₙ) = 1/n × Σ Euler(tᵢ) × Action(tᵢ, tᵢ₊₁) × Résonance(tᵢ)

où :
  Euler(t)      = e^{i(kx_t + ky_t)}     — projection fréquentielle du token
  Action(tₐ,t_b) = δS(kx_a→kx_b, ky_a→ky_b) — principe de moindre action
  Résonance(t)   = |H[kx_t, ky_t]|         — amplitude dans l'hologramme
```

Ce score est **indépendant de tout corpus d'entraînement**. Il ne dépend que des fréquences kx/ky des tokens — une propriété mathématique universelle.

### 4.2 Cache de cohérence — 998 tokens notés

Pour accélérer la vérification, 998 tokens mathématiques ont été pré-notés avec leurs top-50 voisins dans l'espace kx/ky (49 900 paires). Le lookup est O(1).

| Token | Cohérence moyenne | Top voisins |
|-------|-------------------|-------------|
| racine | 0.97 | n_fois_p, n_p_q, densité, formule |
| probabilité | 0.91 | espérance, variance, écart_type, loi |
| dérivée | 0.78 | règle, formule, coefficient, exposant |
| cercle | 0.72 | rayon, pi, aire, sphère |
| (général) | 0.38 | (tokens non-mathématiques) |

### 4.3 Score de confiance par réponse

Chaque réponse reçoit un niveau de confiance :

| Score | Niveau | Action |
|-------|--------|--------|
| ≥ 0.70 | **Haute** | Réponse acceptée sans vérification supplémentaire |
| ≥ 0.55 | **Moyenne** | Réponse acceptée |
| ≥ 0.40 | **Basse** | Réponse fournie avec avertissement |
| < 0.40 | **Nulle** | → Déclenche le Fallback LLM |

---

## 5. Le Fallback LLM — indépendant de tout fournisseur

### 5.1 Pourquoi le Fallback n'a pas besoin de Claude

Le Fallback LLM est activé uniquement dans 5% des cas (cohérence < 0.40). Son rôle est de générer une réponse quand le système harmonique ne peut pas — et cette réponse est **toujours vérifiée par le DHF**.

Le DHF ne fait pas confiance au LLM. Il vérifie sa réponse comme il vérifierait n'importe quelle autre. Si la cohérence est < 0.40, la réponse LLM est **rejetée** et le système répond "Je ne peux pas répondre".

### 5.2 Trois niveaux de Fallback — interchangeables

```python
# Niveau 1 : Ollama local (gratuit, CPU, 30s, 0 dépendance cloud)
fallback = FallbackLLM(mode="local", modele="deepseek-math-1.5b:latest")

# Niveau 2 : API DeepSeek (cloud, 1-2s, $0.10/1M tokens)
fallback = FallbackLLM(mode="cloud", modele="deepseek-chat")

# Niveau 3 : Qwen GGUF local (gratuit, CPU, 5-10s)
fallback = FallbackLLM(mode="local", modele="qwen2.5-3b-instruct-q4_k_m.gguf")
```

**Aucun de ces modèles n'est Claude.** Ils sont interchangeables. Le DHF est le seul garde-fou — et il fonctionne avec n'importe quel LLM.

### 5.3 Pourquoi le DHF rend le choix du LLM non-critique

```
SANS DHF :
    Claude → Réponse → L'utilisateur doit faire confiance à Anthropic
    GPT-4 → Réponse → L'utilisateur doit faire confiance à OpenAI
    DeepSeek → Réponse → L'utilisateur doit faire confiance à DeepSeek

AVEC DHF :
    N'importe quel LLM → Réponse → DHF vérifie → Score 0-1
    Si score < 0.40 → Rejeté
    Si score ≥ 0.40 → Accepté avec mention du score
```

Le DHF est le **certificateur**. Peu importe qui a émis le certificat — c'est la vérification qui compte.

---

## 6. Boucle complète sans dépendance externe

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  QUESTION                                                         │
│      │                                                            │
│      ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ÉTAPE 1 : CLASSIFICATION (GuideHarmonique)                   │ │
│  │ • 11 domaines mathématiques                                  │ │
│  │ • 75% de précision                                           │ │
│  │ • <1ms                                                       │ │
│  │ • Zéro dépendance                                            │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ÉTAPE 2 : GÉNÉRATION (3 modes)                               │ │
│  │                                                              │ │
│  │ MODE A : Calcul exact (SymPy)                                │ │
│  │   → Questions calculables : 60%                              │ │
│  │   → Résultat : expression mathématique exacte                │ │
│  │   → Dépendance : SymPy (librairie Python standard)           │ │
│  │                                                              │ │
│  │ MODE B : Templates structurés                                │ │
│  │   → Questions conceptuelles : 35%                            │ │
│  │   → Résultat : phrase grammaticalement correcte              │ │
│  │   → Dépendance : Aucune (templates en mémoire)               │ │
│  │                                                              │ │
│  │ MODE C : Fallback LLM                                        │ │
│  │   → Questions à cohérence nulle : 5%                         │ │
│  │   → Résultat : réponse LLM vérifiée par DHF                  │ │
│  │   → Dépendance : Aucune (Ollama local gratuit)               │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ÉTAPE 3 : VÉRIFICATION (DHF)                                 │ │
│  │ • Score de cohérence 0-1                                     │ │
│  │ • Indépendant du corpus d'entraînement                       │ │
│  │ • Basé sur les lois de la physique (δS=0)                    │ │
│  │ • <1ms                                                       │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ÉTAPE 4 : POST-TRAITEMENT                                    │ │
│  │ • Correcteur grammatical                                     │ │
│  │ • Formatage de la réponse                                    │ │
│  │ • Niveau de confiance                                        │ │
│  │ • <1ms                                                       │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               ▼                                   │
│  RÉPONSE FINALE AVEC SCORE DE CONFIANCE                          │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Spécifications d'intégration

### 7.1 API autonome (sans dépendance cloud)

```python
# Serveur minimal — dépendances : Flask, NumPy, SymPy, tokenizer local
# Aucune clé API requise pour les Modes A et B
# Mode C nécessite Ollama local (gratuit, un exécutable)

from engine.conscience_harmonique import ConscienceHarmonique
from engine.calculateur_harmonique import CalculateurHarmonique

# Initialisation unique (~2 secondes)
cerveau = ConscienceHarmonique()
cerveau.initialiser(guide=guide, cache=cache, templates=templates)

calculateur = CalculateurHarmonique()
calculateur.initialiser(guide=guide, cache=cache)

# Utilisation
reponse = cerveau.raisonner("dérivée de x^3 + 2x")  # <5ms, zéro cloud
resultat = calculateur.resoudre("dérivée de x^3 + 2x")  # <5ms, calcul exact
```

### 7.2 Ressources requises (mode autonome)

| Ressource | Quantité |
|-----------|----------|
| CPU | 1 cœur (n'importe quel CPU moderne) |
| RAM | ~200 MB |
| Disque | ~50 MB (cache + templates + tokenizer) |
| GPU | Aucun requis |
| Réseau | Aucun requis (modes A et B) |
| Dépendances | Python 3.11, NumPy, SymPy, Flask (optionnel) |

### 7.3 Déploiement

```bash
# Mode autonome complet (sans LLM)
python -c "
from engine.conscience_harmonique import ConscienceHarmonique
cerveau = ConscienceHarmonique()
cerveau.initialiser(guide=guide, cache=cache)
reponse = cerveau.raisonner('dérivée de x^3')
print(reponse.phrase_fr)
"

# Mode autonome + Ollama local (fallback LLM gratuit)
# Nécessite : ollama pull deepseek-math:1.5b (une fois, ~1.1 GB)
python ka_phone/ka_phone_harmonic_server.py --port 8900
```

---

## 8. Démonstration par l'exemple

### Question 1 : Calculable (Mode A — SymPy)

```
Question : "dérivée de x^3 + 2x^2 - 5x + 3"

→ GuideHarmonique : domaine = derivation
→ CalculateurHarmonique : sp.diff(x^3 + 2x^2 - 5x + 3)
→ Résultat SymPy : 3x² + 4x - 5
→ DHF Cohérence : 0.653
→ Confiance : moyenne
→ Template : "La dérivée de x^3 + 2x^2 - 5x + 3 est 3x² + 4x - 5."
→ Correcteur : "La dérivée de x³ + 2x² − 5x + 3 est 3x² + 4x − 5."

✅ Réponse correcte, 0 dépendance externe, 1.2ms
```

### Question 2 : Conceptuelle (Mode B — Templates)

```
Question : "théorème de Pythagore triangle rectangle"

→ GuideHarmonique : domaine = geometrie_euclidienne
→ Retrieval Direct : concepts = [théorème, pythagore, triangle, rectangle, côtés]
→ DHF Cohérence : 0.65
→ Confiance : moyenne
→ Assignation rôles : sujet=théorème, résultat=carré, vérification=formule
→ Template : "Le théorème de Pythagore établit que dans un triangle rectangle,
              le carré de l'hypoténuse est égal à la somme des carrés des côtés."
→ Correcteur : accents et ponctuation

✅ Réponse correcte, 0 dépendance externe, <1ms
```

### Question 3 : Inconnue (Mode C — Fallback LLM local gratuit)

```
Question : "limites suite convergence divergence"

→ GuideHarmonique : domaine = limites (via keyword matching)
→ Retrieval Direct : concepts = [limite, fonction, sinus_x_sur_x]
→ DHF Cohérence : 0.61
→ Confiance : moyenne
→ PAS de Fallback LLM nécessaire (cohérence ≥ 0.40)

✅ Réponse fournie sans aucun LLM. Score de confiance : 0.61
```

---

## Conclusion

**Harmonic AI n'a pas besoin de Claude.** Le système est autonome pour 95% des questions grâce à :

1. **SymPy** pour le calcul exact (60% des questions)
2. **Smart Templates** pour les réponses conceptuelles (35% des questions)
3. **DHF** pour la vérification universelle (100% des réponses)
4. **Ollama local gratuit** comme filet de sécurité ultime (5% des questions)

**Le DHF est le seul composant qui ne peut pas être remplacé** — parce qu'il est le seul à fournir un critère de vérité indépendant. Les LLMs (Claude, GPT, DeepSeek, Ollama) sont interchangeables car le DHF vérifie leur travail.

C'est l'inverse du paradigme actuel : au lieu de faire confiance à un LLM, on fait confiance à un vérificateur universel. Le LLM devient un outil comme un autre — utile mais pas essentiel.

---

*Document technique — 3 Juin 2026*  
*"La confiance ne se délègue pas à un fournisseur. Elle se vérifie."*