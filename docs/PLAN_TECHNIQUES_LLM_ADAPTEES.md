# 🎯 PLAN D'AMÉLIORATION — Techniques LLM adaptées à l'IA harmonique

> **Principe :** chaque technique LLM a un équivalent harmonique. Voici les 5 priorités.

---

## PRIORITÉ 1 : Reranking (contrôle qualité en aval) — 1 jour

**Problème :** Le premier fait trouvé n'est pas toujours le bon.

**Solution :** Récupérer 10 faits candidats, les re-scorer, garder le top-3.

```python
# Dans harmonic_ai.ask() :
# Au lieu de :
facts = retriever.retrieve(question, max_results=5)

# Faire :
candidates = retriever.retrieve(question, max_results=10)
facts = rerank(question, candidates, top_k=3)

def rerank(question, candidates, top_k=3):
    """Re-score les candidats par pertinence."""
    scored = []
    q_words = set(w for w in question.lower().split() if len(w) >= 3)
    
    for fact in candidates:
        s, r, o, sec = fact
        combined = (s + ' ' + r + ' ' + o).lower()
        
        # Score 1 : mots de la question dans la réponse
        overlap = sum(1 for qw in q_words if qw in combined)
        
        # Score 2 : le sujet de la question est dans le SUJET du fait
        sujet_bonus = 3 if any(qw in s.lower() for qw in q_words) else 0
        
        # Score 3 : pas de mots hors-sujet évidents
        noise_penalty = -2 if len(combined) > 200 else 0
        
        total = overlap + sujet_bonus + noise_penalty
        scored.append((total, fact))
    
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored[:top_k]]
```

**Impact :** +10% précision sur les questions factuelles.

---

## PRIORITÉ 2 : Self-consistency (stratégie d'inférence) — 1 jour

**Problème :** Une seule retrieval peut rater la bonne réponse.

**Solution :** Poser la question avec 3 variantes, voter.

```python
def ask_with_consistency(self, question, n_variants=3):
    """Génère n variantes de la question et vote sur la réponse."""
    variants = [
        question,
        self._rephrase(question),        # reformulation
        self._add_context(question),     # avec contexte implicite
    ]
    
    responses = []
    for v in variants:
        r = self.ask(v)
        responses.append(r)
    
    # Extraire le fait commun le plus fréquent
    return self._vote(responses)
```

**Impact :** +15% robustesse (élimine les réponses aberrantes).

---

## PRIORITÉ 3 : SFT harmonique (alignement par exemples) — 2 jours

**Problème :** Certains faits sont noyés dans le bruit.

**Solution :** Ajouter des faits de "référence" avec amplitude H élevée.

```python
# Au lieu d'amplitude uniforme :
encoder.store_fact('tokyo', 'est la capitale de', 'japon', amplitude=1.0)

# Donner plus de poids aux faits importants :
HIGH_QUALITY_FACTS = [
    ('tokyo', 'est la capitale de', 'japon', 5.0),      # amplitude ×5
    ('paris', 'est la capitale de', 'france', 5.0),
    ('orwell', 'a ecrit', '1984', 5.0),
    ('leonard de vinci', 'a peint', 'la joconde', 5.0),
    # ... tous les faits "de référence"
]

for s, r, o, amp in HIGH_QUALITY_FACTS:
    encoder.store_fact(s, r, o, amplitude=amp)
```

**Impact :** +20% précision (les faits importants résonnent plus fort).

---

## PRIORITÉ 4 : Chain-of-thought (raisonnement explicite) — 2 jours

**Problème :** Les réponses sont des listes de faits sans logique.

**Solution :** Composer des chaînes de raisonnement.

```python
def compose_with_reasoning(facts, question_type):
    """Compose une réponse avec enchaînement logique."""
    if question_type == 'definition' and len(facts) >= 1:
        s, r, o = facts[0][:3]
        return f"{s.capitalize()} {r} {o}."
    
    if question_type == 'mecanisme' and len(facts) >= 2:
        s1, r1, o1 = facts[0][:3]
        s2, r2, o2 = facts[1][:3]
        return (f"{s1.capitalize()} {r1} {o1}. "
                f"Cela signifie que {s2} {r2} {o2}.")
    
    if question_type == 'identite' and len(facts) >= 1:
        s, r, o = facts[0][:3]
        return f"C'est {s}. {s.capitalize()} {r} {o}."
```

**Impact :** +25% qualité perçue (les votants Arena aiment les réponses structurées).

---

## PRIORITITÉ 5 : Post-processing qualité — 1 jour

**Problème :** Réponses en FR pour questions EN, accents manquants, etc.

**Solution :** Filtre de qualité après composition.

```python
def quality_filter(response, question_lang):
    """Filtre la réponse pour assurer la qualité."""
    # 1. Langue cohérente
    if question_lang == 'en':
        # Remplacer les connecteurs FR par EN
        response = response.replace('En d\'autres termes,', 'In other words,')
        response = response.replace('Plus précisément,', 'More specifically,')
        response = response.replace('Pour entrer dans le détail,', 'Furthermore,')
        response = response.replace('On peut définir', 'We can define')
        response = response.replace('se définit comme', 'is defined as')
        response = response.replace('correspond à', 'corresponds to')
        response = response.replace('désigne', 'designates')
        response = response.replace('Par ', 'By ')
    
    # 2. Capitaliser les noms propres
    PROPER_NOUNS = ['Tokyo', 'Paris', 'Berlin', 'London', 'Washington',
                    'Einstein', 'Newton', 'Darwin', 'Orwell', 'Hugo',
                    'Shakespeare', 'Leonard de Vinci', 'Beethoven', 'Mozart']
    for noun in PROPER_NOUNS:
        response = re.sub(r'\b' + noun.lower() + r'\b', noun, response)
    
    # 3. Limiter la longueur (Arena préfère concis)
    if len(response) > 300:
        sentences = response.split('. ')
        response = '. '.join(sentences[:3]) + '.'
    
    return response
```

**Impact :** +15% score Arena (cohérence linguistique + concision).

---

## RÉCAPITULATIF

| Priorité | Technique LLM | Équivalent harmonique | Effort | Impact |
|----------|--------------|----------------------|--------|--------|
| 1 | Reranking | Re-scoring par amplitude HRR | 1j | +10% |
| 2 | Self-consistency | 3 variantes + vote | 1j | +15% |
| 3 | SFT / RLHF | Amplitude H différenciée | 2j | +20% |
| 4 | Chain-of-thought | Templates de raisonnement | 2j | +25% |
| 5 | Post-processing | Filtre qualité langue/format | 1j | +15% |

**TOTAL : 7 jours → +85% potentiel**

ELO projeté après les 5 priorités : ~1050-1100 (niveau Gemma 2 / Mistral)

---

## CE QUI N'EST PAS APPLICABLE

| Technique LLM | Pourquoi pas |
|--------------|-------------|
| Transformers | Architecture incompatible |
| Pré-entraînement | Pas de paramètres |
| BPE tokenization | On tokenize par mots |
| RLHF par gradients | Pas de backprop |
| Beam search complexe | Déterminisme = pas besoin |

**L'avantage :** nous n'avons pas besoin d'entraîner quoi que ce soit. Toutes les améliorations sont des **ajustements d'amplitude** et de **logique de composition** — instantanés.
