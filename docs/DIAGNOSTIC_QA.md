# Diagnostic QA — Harmonic Brain v3

## Résumé

21/23 questions passent un test basique, mais **la qualité perçue est médiocre**.
L'utilisateur reçoit des réponses hors sujet, verbeuses, ou imprécises.

---

## 1. Tableau des Échecs — Par Gravité

### 🔴 BLOQUANTS (l'utilisateur reçoit n'importe quoi)

| Question | Réponse actuelle | Problème |
|----------|-----------------|----------|
| qui es tu | "onde est une perturbation" | Mauvais matching lexical |
| comment tu t'appelles | "thymus mature les lymphocytes T" | Aucun fait d'identité trouvé |
| auteur des Misérables | "anneaux de Newton" | Mauvais matching |
| train 100km/h 30min | "berlin a ete divisee par un mur" | Aucun moteur de calcul |
| article 80€ -20% | "isotope a un nombre..." | Aucun moteur de calcul |

### 🟡 MAJEURS (la réponse contient l'info mais mal)

| Question | Réponse actuelle | Problème |
|----------|-----------------|----------|
| nombre d'or | "...nombre est une abstraction... phi est le nombre d'or..." | Info noyée dans 3 phrases |
| combien de continents | "continent est une vaste étendue" | Donne la définition, pas le nombre |
| symbole eau | "Symbole represente autre chose" | Le mot "symbole" matche avant "H2O" |

### 🟢 MINEURS (réponse correcte mais expérience pauvre)

| Problème | Exemple |
|----------|---------|
| Format verbeux | "En premier lieu... De plus... Par ailleurs..." |
| Confiance gonflée | Toutes les réponses ont confiance=1.0 même les fausses |
| Pas de "je ne sais pas" | Le système invente au lieu d'avouer son ignorance |

---

## 2. Causes Racines — Les 5 Problèmes

### Cause 1 : KB trop petite (914 faits)
La KB qualitative intégrée n'a que 914 faits. La KB 50K en a 51 149.
Le taux de couverture est **55× plus faible** que nécessaire.

### Cause 2 : Pas de moteur de calcul
Les questions "combien", "quelle distance", "quel pourcentage" exigent
un calcul numérique. Le cerveau ne fait que du retrieval de faits.

### Cause 3 : Matching purement lexical
"qui es tu" → cherche des faits avec "tu" → ne trouve que "onde est une
perturbation **qui** se propage". Le mot "qui" matche, pas le sens.

### Cause 4 : Format de réponse multi-faits par défaut
Le `_express()` dans harmonic_brain.py rend TOUJOURS 2-3 faits,
même quand un seul suffit. D'où le bavardage.

### Cause 5 : Pas de score de confiance fiable
Les réponses fausses ont la même confiance (0.7-1.0) que les bonnes.
Le système ne SAIT PAS qu'il ne sait pas.

---

## 3. Solutions — Par Priorité

### Solution 1 : Utiliser la KB 50K (IMPACT MAXIMAL)
- Passe de 914 à 51 149 faits → couverture 55×
- Nécessite > 512 Mo RAM → plan Render `starter plus` (1 Go, ~25$/mois)
- Ou : charger un sous-ensemble de 10K faits qui tient dans 512 Mo

### Solution 2 : Micro-moteur de calcul (IMMÉDIAT)
- Intercepter les questions numériques AVANT le retrieval
- Patterns : "combien de X", "Y% de Z", "distance si V et T"
- Utiliser des regex + eval sécurisé
- 50 lignes de code, énorme impact

### Solution 3 : Réponse courte par défaut (IMMÉDIAT)
- Modifier `_express()` : un seul fait si score >> autres
- Ajouter "Je ne sais pas" quand confiance < 0.4
- Supprimer "En premier lieu, De plus, Par ailleurs"

### Solution 4 : Faits d'identité renforcés (IMMÉDIAT)
- Ajouter ("tu es", "KA", "un assistant")
- Ajouter ("comment tu t appelles", "repondre", "KA")

### Solution 5 : Score de confiance réaliste
- Baisser la confiance quand un seul mot match
- Augmenter quand le sujet de la question = sujet du fait
- Afficher "confiance faible" dans la réponse

---

## 4. Impact Estimé

| Solution | Effort | Impact | Coût |
|----------|--------|--------|------|
| KB 50K (10K subset) | 2h | +40% précision | 0€ |
| Micro-calculateur | 1h | Résout 100% des questions numériques | 0€ |
| Réponse courte | 30min | +50% satisfaction utilisateur | 0€ |
| Faits identité | 15min | Résout "qui es-tu" | 0€ |
| Confiance réaliste | 1h | Filtre les mauvaises réponses | 0€ |

**TOTAL : 5h de travail → qualité perçue ×3 à ×5**
