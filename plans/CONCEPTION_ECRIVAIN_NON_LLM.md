# Concevoir Notre Propre "Écrivain" — Sans LLM

> **Peut-on remplacer DeepSeek par un reformulateur local, léger, sans dépendance externe ?**
>
> Oui. Et c'est plus simple qu'on ne le croit. Voici l'analyse complète, de la plus simple à la plus sophistiquée.

---

## Table des Matières

1. [De Quoi l'Écrivain a-t-il VRAIMENT Besoin ?](#1-de-quoi-lécrivain-a-t-il-vraiment-besoin-)
2. [Approche 1 : Templates NLG (la plus simple)](#2-approche-1--templates-nlg-la-plus-simple)
3. [Approche 2 : Moteur de Règles Grammaticales](#3-approche-2--moteur-de-règles-grammaticales)
4. [Approche 3 : Modèle N-Gramme + Dictionnaire de Style](#4-approche-3--modèle-n-gramme--dictionnaire-de-style)
5. [Approche 4 : Petit Encodeur-Décodeur (T5-like local)](#5-approche-4--petit-encodeur-décodeur-t5-like-local)
6. [Approche 5 : Ollama Local (SmolLM2)](#6-approche-5--ollama-local-smollm2)
7. [Comparaison des Approches](#7-comparaison-des-approches)
8. [Recommandation : L'Approche Hybride](#8-recommandation--lapproche-hybride)

---

## 1. De Quoi l'Écrivain a-t-il VRAIMENT Besoin ?

Avant de concevoir un écrivain, définissons précisément sa tâche.

### Ce qu'il reçoit en entrée

Une **réponse factuelle brute** provenant de notre base de connaissances. Exemple :

```
Entrée brute : "The derivative of x^2 with respect to x is 2x.
This follows from the power rule: d/dx(x^n) = n*x^(n-1) with n=2."
```

### Ce qu'il doit produire en sortie

La **même information**, mais formulée de manière fluide, conversationnelle, dans la langue souhaitée :

```
Sortie souhaitée : "La dérivée de x² est 2x.
Cela suit la règle de puissance : d/dx(x^n) = n·x^(n-1).
Ici n=2, donc la dérivée est 2·x^(2-1) = 2x."
```

### Ce que l'écrivain n'a PAS besoin de faire

- ❌ **Comprendre** le sens profond du texte
- ❌ **Raisonner** sur les mathématiques
- ❌ **Générer** du contenu nouveau
- ❌ **Vérifier** l'exactitude des faits (c'est déjà fait)

### Ce que l'écrivain doit SEULEMENT faire

- ✅ **Détecter** les éléments clés (nombres, formules, termes techniques)
- ✅ **Réorganiser** la structure de la phrase
- ✅ **Traduire** si nécessaire (anglais → français)
- ✅ **Adapter** le registre (formel → conversationnel)
- ✅ **Injecter** le contexte de la conversation

**La tâche est radicalement plus simple que la génération de texte.** On n'a pas besoin d'un LLM. On a besoin d'un **reformulateur spécialisé**.

---

## 2. Approche 1 : Templates NLG (la plus simple)

### Principe

Pour chaque type de réponse, on écrit un **template** (un modèle de phrase) avec des **trous** (placeholders) que l'on remplit avec les valeurs spécifiques.

### Exemple concret

```python
# Template pour les réponses de type "dérivée"
TEMPLATE_DERIVATIVE = {
    "fr": "{fonction} se dérive en {resultat}. Cela suit la règle {regle} : {formule_regle}. Ici, {parametre}, donc {calcul}.",
    "en": "The derivative of {fonction} is {resultat}. This follows from {regle}: {formule_regle}. With {parametre}, we get {calcul}.",
}

# Template pour les réponses de type "arithmétique"
TEMPLATE_ARITHMETIC = {
    "fr": "{a} {operation} {b} = {resultat}.",
    "en": "{a} {operation} {b} = {resultat}.",
}

# Template pour "conversation"
TEMPLATE_CONVERSATION = {
    "fr": "Pour répondre à votre question sur {domaine} : {reponse}",
    "en": "Regarding your question about {domaine}: {reponse}",
}
```

### Moteur de templating

```python
import re

class TemplateWriter:
    """Reformuleur par templates — zéro dépendance externe."""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def reformuler(self, raw_answer: str, domain: str, langue: str = "fr", 
                   contexte: str = "") -> str:
        # 1. Extraire les valeurs des placeholders depuis la réponse brute
        valeurs = self._extraire_valeurs(raw_answer, domain)
        
        # 2. Choisir le template approprié
        template = self.templates.get(domain, self.templates["general"])[langue]
        
        # 3. Remplir le template
        resultat = template.format(**valeurs)
        
        # 4. Ajouter le contexte si présent
        if contexte:
            resultat = f"({contexte}) {resultat}"
        
        return resultat
    
    def _extraire_valeurs(self, raw: str, domain: str) -> dict:
        """Extrait les valeurs depuis le texte brut."""
        valeurs = {}
        
        if domain == "calculus":
            # Pattern : "The derivative of X is Y"
            m = re.search(r'derivative of (.+?) is (.+?)[\.\n]', raw, re.IGNORECASE)
            if m:
                valeurs["fonction"] = m.group(1).strip()
                valeurs["resultat"] = m.group(2).strip()
            # Pattern : "power rule: d/dx(x^n) = n*x^(n-1)"
            m = re.search(r'(?:power rule|règle)[:\s]*(.+)', raw, re.IGNORECASE)
            if m:
                valeurs["formule_regle"] = m.group(1).strip()
                valeurs["regle"] = "la règle de puissance"
            # Extraire n
            m = re.search(r'n\s*=\s*(\d+)', raw)
            if m:
                valeurs["parametre"] = f"n={m.group(1)}"
                valeurs["calcul"] = f"{m.group(1)}·x^({int(m.group(1))-1})"
        
        elif domain == "arithmetic":
            m = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)\s*=\s*(\d+)', raw)
            if m:
                valeurs["a"] = m.group(1)
                valeurs["operation"] = m.group(2)
                valeurs["b"] = m.group(3)
                valeurs["resultat"] = m.group(4)
        
        return valeurs
```

### Avantages et limites

| ✅ Avantages | ❌ Limites |
|---|---|
| Zéro dépendance externe | Nécessite un template par type de réponse |
| < 1 ms par requête | Moins flexible que le LLM |
| 100% déterministe | La qualité dépend de la qualité des templates |
| Aucun risque d'hallucination | Ne peut pas improviser une formulation totalement nouvelle |
| Facile à maintenir et déboguer | |

### Pour 80% des cas, c'est suffisant.

La plupart de nos réponses suivent des patterns prévisibles : "X est Y", "Le résultat est Z", "Pour calculer X, on fait Y". Pour ces cas, un template fait parfaitement l'affaire.

---

## 3. Approche 2 : Moteur de Règles Grammaticales

### Principe

Un peu plus sophistiqué que les templates : on analyse la structure grammaticale de la réponse brute, et on applique des **règles de transformation** pour la rendre plus fluide.

### Règles de transformation

```python
REGLES_TRANSFORMATION = [
    # Règle 1 : Remplacer les formulations passives par des actives
    ("is given by", "="),
    ("can be calculated as", "="),
    ("is equal to", "="),
    
    # Règle 2 : Simplifier les introductions
    ("The derivative of (.+?) with respect to (.+?) is", r"d/d\2(\1) ="),
    ("The integral of (.+?) with respect to (.+?) is", r"∫\1 d\2 ="),
    
    # Règle 3 : Adapter le registre (anglais → formules)
    ("square root of", "√"),
    ("pi", "π"),
    ("times", "×"),
    
    # Règle 4 : Injecter le contexte conversationnel
    ("^", "Comme vous me l'avez demandé, "),  # Si contexte présent
]
```

### Exemple de transformation

```
ENTRÉE : "The derivative of x^2 with respect to x is 2x.
         This follows from the power rule: 
         the derivative of x^n is n times x^(n-1) with n=2."

TRANSFORMATION :
  1. Appliquer règle 2 : "d/dx(x^2) = 2x."
  2. Simplifier "n times" → "n ×"
  3. Injecter contexte : "Comme vous me l'avez demandé, d/dx(x^2) = 2x."
  
SORTIE : "Comme vous me l'avez demandé, d/dx(x^2) = 2x.
         Cela suit la règle de puissance : d/dx(x^n) = n × x^(n-1), avec n=2."
```

### Avantages et limites

| ✅ Avantages | ❌ Limites |
|---|---|
| Plus flexible que les templates | Nécessite des règles pour chaque pattern |
| Pas besoin de templates par domaine | Peut produire des formulations maladroites si la règle est mal appliquée |
| Facile à étendre (ajouter une règle) | La traduction automatique (EN→FR) est difficile sans dictionnaire |

---

## 4. Approche 3 : Modèle N-Gramme + Dictionnaire de Style

### Principe

On entraîne un **modèle de langue n-gramme** (bigramme ou trigramme) sur un corpus de réponses mathématiques bien écrites. Ce modèle apprend les **séquences de mots probables** dans le domaine mathématique.

Ensuite, pour reformuler une réponse brute :
1. On extrait les éléments **invariants** (nombres, formules, termes techniques)
2. On laisse le modèle n-gramme **compléter** les transitions entre ces éléments avec un langage fluide

### Ce qu'est un n-gramme (simplement)

Un **bigramme** est une paire de mots consécutifs : ("la", "dérivée"), ("dérivée", "de"), ("de", "x²").

Un **trigramme** est un triplet : ("la", "dérivée", "de"), ("dérivée", "de", "x²").

Le modèle compte combien de fois chaque séquence apparaît dans le corpus d'entraînement. Pour générer du texte, il choisit le mot suivant le plus probable étant donné les 2 (ou 3) mots précédents.

### Exemple d'entraînement

```python
corpus = [
    "La dérivée de x² est 2x. Cela suit la règle de puissance.",
    "La dérivée de sin(x) est cos(x). C'est une dérivée trigonométrique.",
    "Pour calculer l'intégrale de x, on utilise la règle de puissance.",
    "Le résultat de 2 + 2 est 4.",
    # ... 1000+ exemples de réponses bien formulées
]

# Modèle trigramme
modele = TrigramModel()
modele.train(corpus)

# Reformulation
reponse_brute = "derivative of x^3 is 3x^2"
elements = extraire_invariants(reponse_brute)  # → ["x^3", "3x^2"]
texte = modele.completer(elements, contexte="calculus")
# → "La dérivée de x³ est 3x². Cela suit la règle de puissance."
```

### Avantages et limites

| ✅ Avantages | ❌ Limites |
|---|---|
| Pas de deep learning, purement statistique | Qualité dépend de la taille et qualité du corpus |
| Rapide (< 1 ms) | Peut produire des séquences grammaticalement incorrectes |
| Apprentissage automatique (pas de règles manuelles) | Ne "comprend" pas le sens — juste les statistiques de co-occurrence |
| Poids du modèle très faible (< 10 Mo) | |

---

## 5. Approche 4 : Petit Encodeur-Décodeur (T5-like local)

### Principe

On utilise un **petit modèle de traduction automatique** (type T5-small, ~60 millions de paramètres) fine-tuné spécifiquement sur la tâche de reformulation mathématique. Ce n'est pas un LLM — c'est un modèle spécialisé et léger.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PETIT ENCODEUR-DÉCODEUR                           │
│                                                                      │
│  Entrée (brute) : "The derivative of x^2 is 2x. Power rule."       │
│       │                                                              │
│       ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  ENCODEUR (Transformer 6 couches, ~30M params)           │       │
│  │  → Convertit le texte en représentation vectorielle      │       │
│  └──────────────────────────────────────────────────────────┘       │
│       │                                                              │
│       ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  DÉCODEUR (Transformer 6 couches, ~30M params)           │       │
│  │  → Génère le texte reformulé mot à mot                   │       │
│  └──────────────────────────────────────────────────────────┘       │
│       │                                                              │
│       ▼                                                              │
│  Sortie (reformulée) : "La dérivée de x² est 2x.                    │
│                         Règle de puissance : d/dx(x^n)=n·x^(n-1)." │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Fine-tuning

On entraîne ce modèle sur des **paires (réponse brute, réponse reformulée)** :

```python
donnees_entrainement = [
    ("derivative of x^2 is 2x", "La dérivée de x² est 2x."),
    ("integral of x is x^2/2 + C", "L'intégrale de x est x²/2 + C."),
    ("2 + 2 = 4", "2 + 2 = 4."),
    # ... 5000+ paires
]
```

### Avantages et limites

| ✅ Avantages | ❌ Limites |
|---|---|
| Qualité de reformulation proche d'un LLM | Nécessite un corpus d'entraînement de paires (brut → reformulé) |
| 100% local, pas de dépendance externe | Fine-tuning = quelques heures de GPU une seule fois |
| Modèle léger (~200 Mo) | Qualité dépend de la diversité du corpus d'entraînement |
| Inférence en < 50ms sur CPU | Peut halluciner si mal entraîné (mais on vérifie après) |
| Apprentissage automatique des patterns | |

---

## 6. Approche 5 : Ollama Local (SmolLM2)

### Principe

On utilise un **tout petit LLM** (360 millions de paramètres) via Ollama en local. C'est techniquement un LLM, mais il est si petit qu'il tourne sur CPU en < 100ms, sans connexion internet.

### Configuration

```bash
# Installation unique
ollama pull smollm2:360m

# Inférence locale
ollama run smollm2:360m "Reformule en français : The derivative of x^2 is 2x"
```

### Avantages et limites

| ✅ Avantages | ❌ Limites |
|---|---|
| Qualité de reformulation excellente | Plus lourd que les approches précédentes (~2 Go) |
| Installation triviale (1 commande) | Reste un LLM, donc risque d'hallucination (faible mais non nul) |
| Support multilingue natif | Dépendance à Ollama (logiciel externe) |
| Inférence < 200ms sur CPU | Pas totalement "maison" |

---

## 7. Comparaison des Approches

| Critère | Templates | Règles | N-Gramme | T5-Small | Ollama SmolLM2 | DeepSeek API |
|---|---|---|---|---|---|---|
| **Qualité du texte** | 🟡 Moyen | 🟡 Moyen | 🟡 Moyen-Bon | 🟢 Bon | 🟢 Très Bon | 🟢 Excellent |
| **Risque hallucination** | 🟢 0% | 🟢 0% | 🟡 Très faible | 🟡 Faible | 🟡 Faible | 🟡 Faible |
| **Dépendance externe** | 🟢 Aucune | 🟢 Aucune | 🟢 Aucune | 🟢 Aucune | 🟡 Ollama | 🔴 API |
| **Temps de développement** | 🟢 2-3 jours | 🟢 3-5 jours | 🟡 1-2 semaines | 🟡 2-4 semaines | 🟢 1 jour | 🟢 1 jour |
| **Maintenance** | 🟢 Très facile | 🟢 Facile | 🟡 Moyenne | 🟡 Moyenne | 🟢 Facile | 🟢 Aucune |
| **Latence** | 🟢 < 1ms | 🟢 < 1ms | 🟢 < 5ms | 🟢 < 50ms | 🟢 < 200ms | 🔴 2-3s |
| **Coût** | 🟢 Gratuit | 🟢 Gratuit | 🟢 Gratuit | 🟢 Gratuit | 🟢 Gratuit | 🔴 ~0.01€/req |
| **Flexibilité** | 🔴 Faible | 🟡 Moyenne | 🟡 Moyenne | 🟢 Bonne | 🟢 Bonne | 🟢 Excellente |
| **Poids** | < 10 Ko | < 50 Ko | < 10 Mo | ~200 Mo | ~2 Go | 0 (cloud) |

---

## 8. Recommandation : L'Approche Hybride

La meilleure stratégie est de **combiner** plusieurs approches pour couvrir tous les cas :

```
┌─────────────────────────────────────────────────────────────────────┐
│               ÉCRIVAIN HYBRIDE (Recommandation)                      │
│                                                                      │
│  Réponse brute                                                       │
│       │                                                              │
│       ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ Niveau 1 : TEMPLATES (80% des cas)                       │       │
│  │ • Détection du type de réponse (dérivée, arithmétique,   │       │
│  │   géométrie, définition...)                               │       │
│  │ • Si un template existe → reformulation instantanée      │       │
│  │ • Latence : < 1ms, 0% hallucination                      │       │
│  └──────────────────────────────────────────────────────────┘       │
│       │ (si pas de template)                                         │
│       ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ Niveau 2 : RÈGLES GRAMMATICALES (15% des cas)            │       │
│  │ • Application de règles de transformation                 │       │
│  │ • Simplification, traduction basique, restructuration    │       │
│  │ • Latence : < 1ms, 0% hallucination                      │       │
│  └──────────────────────────────────────────────────────────┘       │
│       │ (si le résultat n'est pas satisfaisant)                      │
│       ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ Niveau 3 : T5-SMALL LOCAL (4% des cas)                   │       │
│  │ • Modèle encodeur-décodeur fine-tuné                      │       │
│  │ • Qualité proche LLM, 100% local                          │       │
│  │ • Latence : < 50ms                                        │       │
│  └──────────────────────────────────────────────────────────┘       │
│       │ (si absolument nécessaire)                                   │
│       ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ Niveau 4 : FALLBACK API (1% des cas)                     │       │
│  │ • DeepSeek API pour les cas vraiment hors norme          │       │
│  │ • Latence : 2-3s                                          │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Plan de mise en œuvre

| Phase | Contenu | Durée | Résultat |
|---|---|---|---|
| **Phase 1** | Templates pour les 10 types de réponses les plus fréquents | 2-3 jours | 80% des réponses reformulées localement en < 1ms |
| **Phase 2** | Règles grammaticales + dictionnaire EN→FR mathématique | 1 semaine | 95% des réponses reformulées localement |
| **Phase 3** | Fine-tuning T5-small sur paires (brut, reformulé) | 2-3 semaines | 99% des réponses reformulées localement |
| **Phase 4** | DeepSeek API en fallback pour les 1% restants | 1 jour | 100% couvert |

### Ce qu'on gagne

| | Aujourd'hui (DeepSeek API) | Après Phase 3 |
|---|---|---|
| **Dépendance externe** | Oui | **Non** (99% local) |
| **Latence moyenne** | 2-3 secondes | **< 1 ms** (80%), < 50ms (19%) |
| **Coût par requête** | ~0.01€ | **0€** |
| **Disponibilité** | Internet requis | **Fonctionne offline** |
| **Hallucination** | Très faible (vérifié) | **0%** (templates + règles), très faible (T5) |

---

## Conclusion

**Oui, on peut parfaitement concevoir notre propre écrivain sans LLM.**

La tâche de reformulation est **radicalement plus simple** que la génération de texte. On n'a pas besoin de "comprendre" les mathématiques — juste de savoir bien écrire.

L'approche recommandée est **hybride** :
1. **Templates** pour le quotidien (80% des cas, < 1ms, 0% hallucination)
2. **Règles** pour la flexibilité (15% des cas)
3. **T5-small** pour les cas complexes (4% des cas)
4. **API DeepSeek** en filet de sécurité ultime (1% des cas)

Le résultat : un écrivain **100% local, gratuit, instantané, et sans hallucination** pour l'essentiel des requêtes — avec la qualité d'un LLM quand c'est vraiment nécessaire.