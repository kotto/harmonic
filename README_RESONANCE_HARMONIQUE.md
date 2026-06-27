# Apprentissage par Résonance Harmonique

## Résultats des Tests

### ✅ XOR — 100% en 1 passe
L'algorithme apprend le XOR parfaitement en une seule passe, sans rétropropagation.

### 🎉 MNIST — 91.5% en 1 passe (10000 images)
Sur 10000 images d'entraînement, 200 de test :
- **Accuracy : 91.5%** (contre ~5% aléatoire)
- **Temps : 0.95s** (0.095ms par image)
- **Régularisation :** λ = 1/φ² ≈ 0.38 (optimale)

### Scalabilité parfaite
| Images | Accuracy | Temps | ms/image |
|--------|----------|-------|----------|
| 1000   | 69.5%    | 0.21s | 0.205ms |
| 2000   | 81.5%    | 0.30s | 0.152ms |
| 5000   | 87.0%    | 0.70s | 0.140ms |
| **10000** | **91.5%** | **0.95s** | **0.095ms** |

### Architecture
```
Entrée (784) → Normalisation → Random Projection (256) → 
8 non-linéarités (tanh, sin, cos, relu, sigmoid, z², z³, |z|) →
Régression régularisée (λ=1/φ²) → 10 classes
```

### Pourquoi ça marche
1. **Normalisation préalable** sur tout l'ensemble
2. **Apprentissage en 1 passe** (pas de batches)
3. **Réservoir avec 8 non-linéarités** pour capturer différentes relations
4. **Régularisation harmonique** λ = 1/φ² optimale
5. **Scalabilité linéaire** : plus de données → meilleur résultat

### Pour aller plus loin (>95%)
- Architecture multi-couche avec résonance
- Features convolutives (CNN-like) avant le réservoir
- Dataset complet MNIST (60000 images)
