# PROMPT POUR IA EXPERTE — Problème de Retrieval Sémantique

> **Contexte :** IA harmonique, architecture ondulatoire, zéro paramètre entraîné.

---

## 1. NOTRE ARCHITECTURE

Nous avons construit une IA non-neuronale avec :
- **KB** : 21 500 faits stockés comme triplets `(sujet, relation, objet, secteur)`.
  Ex: `("tokyo", "est la capitale de", "japon", "GEOGRAPHIE")`
- **Pipeline** : Question → Retrieval de faits → Composition de réponse
- **Contrainte** : Pas de réseau de neurones, pas de GPU, pas d'embedding entraîné.

## 2. LE PROBLÈME

Le retrieval échoue quand la question utilise des mots DIFFÉRENTS de ceux du fait.

```
✅ "capitale du japon" → trouve "tokyo est la capitale du japon"
❌ "who painted the mona lisa" → ne trouve PAS "leonard de vinci a peint la joconde"
   (car "mona lisa" ≠ "joconde")

❌ "what is the largest country" → trouve "algeria is the world's tenth largest"
   (car "largest" matche, mais l'Algérie n'est PAS le plus grand pays)

❌ "when did ww2 end" → ne trouve PAS "world war 2 ended in 1945"
   (car "ww2" ≠ "world war 2")
```

## 3. CE QU'ON A ESSAYÉ

### Approche A : TF-IDF + Index inversé
- Fonctionne à ~60%
- Échoue sur les synonymes et paraphrases
- Sensible aux collisions ("largest" matche "tenth largest")

### Approche B : Co-occurrence sémantique (dernière tentative)
- Graphe de co-occurrence depuis la KB : deux mots sont liés s'ils apparaissent dans le même fait
- Expansion de requête : pour chaque mot de la question, ajouter ses voisins dans le graphe
- Résultat : instable. L'expansion ajoute du bruit qui noie le signal.

### Approche C : Ponts sémantiques manuels (synonymes)
- Dictionnaire de synonymes : "mona lisa" → "joconde", "largest" → "plus grand"
- Fonctionne mais non scalable (infini de synonymes possibles)

### Approche D : HRR holographique (tentative)
- Vecteurs complexes phi-spacés pour chaque mot (déterministes)
- Binding/unbinding par convolution circulaire (FFT)
- Échec : les vecteurs phi-spacés ne capturent PAS la similarité sémantique
  (ils sont orthogonaux presque partout)

## 4. L'INTUITION THÉORIQUE

Notre théorie dit : « tout est ondes ». Deux concepts sont liés si leurs ondes interfèrent. Dans notre KB, deux mots « interfèrent » s'ils co-occurrent dans les mêmes faits. Le graphe de co-occurrence EST la signature ondulatoire de la connaissance.

Mais nous n'arrivons pas à traduire cette intuition en un algorithme de retrieval robuste.

## 5. LA QUESTION

**Comment retrouver le fait pertinent dans une KB de triplets quand la question utilise des mots différents de ceux du fait, SANS réseau de neurones ni embedding pré-entraîné, en utilisant uniquement la structure de la KB elle-même ?**

Contraintes :
- Pas d'embedding externe (Word2Vec, BERT, etc.)
- Pas de réseau de neurones
- Doit fonctionner sur CPU en <100ms
- La KB contient ~21 500 triplets
- Doit être robuste aux synonymes, paraphrases, et fautes de frappe légères

La solution idéale exploiterait la CO-OCCURRENCE dans la KB elle-même comme signal sémantique, d'une manière plus robuste que la simple expansion de requête.

---

*Merci de proposer une solution algorithmique concrète, avec pseudo-code si possible.*
