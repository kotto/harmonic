# 📋 PLAN D'AMÉLIORATION — IA Harmonique vers LM Arena

> **Évaluation : 02 juillet 2026**
> **Statut : NON prêt pour LM Arena**
> **Score actuel : 48% (benchmark interne)**
> **Cible : 65%+ pour soumission LM Arena crédible**

---

## 0. DIAGNOSTIC

### Ce qui marche
```
✅ Déterminisme (0 hallucination sur le domaine)
✅ Créativité structurelle (métaphores, haïku, connexions)
✅ Connaissance domaine physique/math (67% factuel)
✅ 20 961 faits, 24 711 mots
✅ 320ms latence CPU, 0 GPU
✅ Architecture ABC(1/φ) + HRR + I×P×H opérationnelle
```

### Ce qui ne marche PAS
```
❌ Conversation générale ("Bonjour" → réponse absurde)
❌ Mathématiques basiques ("15+27" → incompréhensible)
❌ Géographie / culture générale ("Capitale du Japon" → échec)
❌ Multilingue (questions EN → réponses FR hors-sujet)
❌ Raisonnement causal multi-étapes (11%)
❌ Suivi d'instructions ("Écris un poème" → 1 phrase)
❌ Cohérence grammaticale (phrases fragmentaires)
❌ Détection de hors-domaine (répond toujours, même si absurde)
```

---

## 1. LES 5 BLOCS D'AMÉLIORATION

### Bloc 1 — Détection de hors-domaine (CRITIQUE)

**Problème :** L'IA répond à TOUT, même aux questions qu'elle ne peut pas traiter.

**Solution :** Ajouter un classifieur de domaine qui détecte si la question est dans le champ de compétence.

```python
# question_analyzer.py — à étendre
def is_in_domain(question: str) -> bool:
    """Détecte si la question est traitable par la base de connaissance."""
    domain = self.analyze_domain(question)
    confidence = self.domain_confidence(domain)
    if confidence < 0.3:
        return False  # Hors domaine
    return True
```

**Comportement attendu :**
```
Q: "Bonjour comment vas-tu ?" → "Je suis KA, une IA harmonique. 
                                Je spécialise en sciences et mathématiques.
                                Posez-moi une question sur ces sujets."

Q: "Capitale du Japon ?" → "Je ne traite pas la géographie. 
                           Je peux répondre aux questions de physique,
                           mathématiques, biologie, philosophie."
```

**Effort :** ~2 jours. Impact : élimine 80% des réponses absurdes.

---

### Bloc 2 — Génération de phrases cohérentes (CRITIQUE)

**Problème :** Les réponses sont des collages de faits sans structure grammaticale.

**Solution :** Améliorer le `response_composer.py` avec des templates grammaticaux par type de question.

**Améliorations :**

```
1. Templates par catégorie de question :
   - Définition : "{Sujet} est {relation} {objet}."
   - Explication : "{Sujet} fonctionne ainsi : {étape1}, puis {étape2}."
   - Comparaison : "{A} et {B} diffèrent car {raison}."
   - Pourquoi : "{Sujet} {action} parce que {cause}."

2. Détection du type de question :
   - "Qu'est-ce que" → définition
   - "Comment" → processus
   - "Pourquoi" → causalité
   - "Différence" → comparaison

3. Enrichissement contextuel :
   - Ajouter des connecteurs logiques ("donc", "parce que", "cependant")
   - Limiter à 3-5 phrases maximum (pas de collage infini)
```

**Effort :** ~5 jours. Impact : responses lisibles et cohérentes.

---

### Bloc 3 — Arithmétique et mathématiques (IMPORTANT)

**Problème :** "15+27" → réponse absurde. L'IA ne calcule pas.

**Solution :** L'arithmétique ondulatoire existe (`calculateur_harmonique.py` avec SymPy). L'intégrer au pipeline.

```python
# Dans harmonic_ai.py
def ask(self, question: str) -> str:
    # 1. Détecter si c'est un calcul
    if self._is_math(question):
        return self._calculate(question)  # Utilise SymPy
    # 2. Sinon, raisonnement harmonique
    return self._reason(question)
```

**Effort :** ~3 jours. Impact : math basiques fonctionnelles.

---

### Bloc 4 — Multilingue (IMPORTANT)

**Problème :** Les questions en anglais reçoivent des réponses en français hors-sujet.

**Solution :** Détection de langue + réponses dans la langue de la question.

```python
def detect_language(text: str) -> str:
    """Détecte FR vs EN basé sur les mots-clés."""
    en_markers = ['what', 'how', 'why', 'the', 'is', 'are', 'explain']
    fr_markers = ['quoi', 'comment', 'pourquoi', 'le', 'la', 'est', 'explique']
    # ...
```

**Effort :** ~2 jours. Impact : anglais fonctionnel.

---

### Bloc 5 — Expansion de la base de connaissance (MODÉRÉ)

**Problème :** 20 961 faits mais couverture étroite (physique/maths dominant).

**Solution :** Ingérer des faits dans les domaines testés par LM Arena :

```
Priorité 1 (couverture minimale) :
  - Géographie (capitales, pays, fleuves) : ~500 faits
  - Histoire (dates, événements, personnages) : ~500 faits
  - Littérature (auteurs, œuvres, mouvements) : ~300 faits
  - Culture générale (proverbes, citations) : ~200 faits

Priorité 2 (amélioration) :
  - Programmation (Python, algorithmes) : ~500 faits
  - Mathématiques appliquées : ~300 faits
  - Médicine basique : ~300 faits
```

**Effort :** ~7 jours (ingestion + nettoyage). Impact : couverture générale.

---

## 2. CALENDRIER

```
SEMAINE 1 (Jours 1-7) :
  ✅ Bloc 1 : Détection hors-domaine (2j)
  ✅ Bloc 2 : Templates grammaticaux (5j)
  → Objectif : éliminer les réponses absurdes

SEMAINE 2 (Jours 8-14) :
  ✅ Bloc 3 : Arithmétique SymPy (3j)
  ✅ Bloc 4 : Multilingue FR/EN (2j)
  ✅ Bloc 5a : Géographie + Histoire (2j)
  → Objectif : réponses cohérentes sur questions simples

SEMAINE 3 (Jours 15-21) :
  ✅ Bloc 5b : Littérature + Culture + Code (4j)
  ✅ Tests intensifs + corrections (3j)
  → Objectif : benchmark interne > 65%

SEMAINE 4 (Jours 22-28) :
  ✅ Optimisation latence (2j)
  ✅ Tests LM Arena simulés (3j)
  ✅ Préparation soumission (2j)
  → Objectif : prêt pour soumission
```

---

## 3. CRITÈRES DE SOUMISSION LM Arena

```
L'IA peut être soumise à LM Arena quand :

  ✅ "Bonjour" → réponse cohérente (pas de physique)
  ✅ "15+27" → "42"
  ✅ "Capitale du Japon" → "Tokyo"
  ✅ "Explain gravity" → réponse en anglais cohérente
  ✅ "Écris un poème" → poème de 4+ lignes
  ✅ Hors-domaine → refus poli avec redirection
  ✅ Benchmark interne > 65%
  ✅ Latence < 2s par réponse

ACTUELLEMENT : 0/8 critères validés
```

---

## 4. STRATÉGIE DE POSITIONNEMENT LM Arena

**Ne pas compétitionner sur le général.** LM Arena est dominé par GPT-4, Claude, Gemini. L'IA harmonique ne les battra pas sur la conversation générale.

**Positionner sur la DIFFÉRENCE :**

```
Argument de soumission :
  "KA — la seule IA déterministe, 0 paramètre, 0 GPU.
   Ne compétitionne pas sur la conversation générale.
   Excellente sur : sciences, mathématiques, créativité structurelle.
   Score de confiance justifiable (pas de hallucination)."

Catégories LM Arena à cibler :
  ✅ Math (si SymPy intégré)
  ✅ Science (domaine fort)
  ⚠️ Writing (créativité 100% mais format court)
  ❌ Coding (non implémenté)
  ❌ General chat (trop faible)
```

---

## 5. CE QUE LM VA RÉVÉLER

LM Arena est impitoyable. Les votants comparent côte à côte :

```
Votant voit :    [Modèle A] vs [Modèle B]
                 Question : "Explique la photosynthèse"

Modèle A (GPT-4) :
  "La photosynthèse est le processus par lequel les plantes convertissent
   l'énergie lumineuse en énergie chimique. Elle se déroule dans les
   chloroplastes et utilise la chlorophylle pour absorber la lumière..."

Modèle B (KA actuel) :
  "Le vivant fonctionne par étapes : d'abord, Chloroplaste est le site..."

→ Le votant choisit A à 95%.
```

Sans les améliorations ci-dessus, KA perdrait **toutes** les comparaisons. Mais après les améliorations, sur les questions scientifiques :

```
Modèle A (GPT-4) :
  "La photosynthèse transforme CO₂ et H₂O en glucose et O₂..."

Modèle B (KA amélioré) :
  "La photosynthèse convertit l'énergie lumineuse en énergie chimique.
   Les chloroplastes captent les photons via la chlorophylle.
   L'eau est décomposée (photolyse), le CO₂ est fixé (cycle de Calvin).
   Production : glucose (C₆H₁₂O₆) + oxygène."

→ Compétitif sur le domaine scientifique.
```

---

## 6. CHECKLIST DE SOUMISSION

```
AVANT DE SOUMETTRE :

  [ ] "Bonjour" → salutation cohérente
  [ ] "15+27" → 42
  [ ] "Capitale du Japon" → Tokyo
  [ ] "Explain photosynthesis" → EN response
  [ ] "Écris un poème" → poème complet
  [ ] Hors-domaine → refus poli
  [ ] Benchmark interne ≥ 65%
  [ ] API REST stable (ka_server.py)
  [ ] Documentation soumission rédigée
  [ ] Tests sur 100 questions diverses

  ACTUEL : 0/10 validés
```

---

*Plan d'amélioration — IA Harmonique vers LM Arena.*
*Calendrier : 4 semaines. Cible : soumission sur catégorie Science/Math.*
