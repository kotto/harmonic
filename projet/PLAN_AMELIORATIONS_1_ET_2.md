# PLAN : Options 1 et 2 combinées

## Option 1 : Analyseurs linguistiques (remplace les heuristiques)
**Fichier** : `AnalyseurLinguistique` dans `harmonic_unconscious.py`

Les 9 dimensions actuelles sont remplacées par des métriques linguistiques réelles :
- **phi** → Type-Token Ratio (TTR) + Moving Average TTR
- **alpha** → Longueur moyenne des mots + distribution (skewness)
- **reasoning** → Densité de subordination (marqueurs logiques : "donc", "car", "parce que")
- **creativity** → Indice de surprise lexicale (mots rares + néologismes)
- **math** → Fréquence de chiffres + symboles mathématiques + formules
- **factual** → Densité d'entités nommées (capitales, noms propres) + stop words
- **code** → Patterns syntaxiques code (indentation, structures de contrôle)
- **emotion** → Lexique émotionnel élargi (ANEW, NRC) + ponctuation expressive
- **temporal** → Variance de longueur de phrase + marqueurs temporels

## Option 2 : Générateur PhiInverse (remplace la concaténation)

**Pipeline de génération** :
```
Prompt → AnalyseurLinguistique → Signature 9D
                                    ↓
                              Fusion 16D
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            Résonance mémoire               Projection 16D→7D
                    ↓                               ↓
        Connaissances similaires       PhiInverseDecoder
                    ↓                               ↓
        Contexte harmonique            Logits sur vocabulaire
                    ↓                               ↓
            ←── Fusion contexte + logits ──→
                            ↓
                    Token sampling
                            ↓
                  Nouveau texte généré
```

## Implémentation

### Nouveaux composants :

1. `AnalyseurLinguistique` (remplace `ProjecteurSemantiqueDirect`)
   - Tokenizer simple (moins de 100 lignes)
   - Métriques linguistiques basées sur règles (0 paramètre)
   - Détection de patterns (entités, émotions, syntaxes)

2. `PhiInverseGenerator` (nouveau)
   - Embedding harmonique PHI (cos + décroissance)
   - Mapping 16D ↔ 7D (projection linéaire fixe PHI)
   - PhiInverseDecoder (intégrale ABC inverse)
   - Sampling (top-k, top-p, température)
   - Cache de contexte harmonique

3. `HarmonicGenerator` (orchestrateur)
   - Reçoit un prompt
   - Calcule la signature via AnalyseurLinguistique
   - Trouve les connaissances les plus résonantes
   - Génère token par token avec PhiInverse
   - Certification SHA256 de la séquence complète
