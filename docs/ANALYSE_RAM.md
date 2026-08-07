# 📊 Analyse RAM — Pourquoi le KB 358K échoue

**Date : 21 Juillet 2026**

---

## Profil mémoire (KB 110K qui fonctionne)

| Composant | RAM | % |
|-----------|-----|---|
| **KB facts (list Python)** | 37 MB | 46% |
| **HarmonicBrain** | 44 MB | 54% |
| Hologram Store | 0.1 MB | <1% |
| **TOTAL** | **81 MB** | 100% |

---

## Pourquoi 37 MB pour 110K faits ?

```
np.load('merged_v3.npz')
  → décompresse le fichier (1.7 MB → ~15 MB numpy)
  
list(data['facts'])
  → convertit le numpy array en liste Python
  → chaque tuple Python = ~56 bytes d'overhead
  → chaque string Python = ~49 bytes d'overhead
  → 110,307 × 4 strings × (49 overhead + 16 contenu) = ~28 MB
  → + 110,307 tuples × 56 = ~6 MB
  → Total : ~37 MB
```

---

## Projection KB 358K

```
KB facts : 37 × (358/110) = 120 MB
HarmonicBrain         =  44 MB (fixe)
Total estimé          = 164 MB

+ spectral phases     = ~5 MB
+ learned embedding   = ~5 MB
+ 26 hologrammes      = ~10 MB
+ autres modules      = ~10 MB
─────────────────────────────────
TOTAL                 ≈ 194 MB

Dépasse probablement la limite mémoire de l'environnement (≈128-256 MB).
```

---

## Solutions

| Solution | Effort | Impact |
|----------|--------|--------|
| **Garder le KB en numpy array** (pas de `list()`) | Faible | -28 MB |
| **Utiliser le KB 300K sectorisé** (13 MB compressé, déjà numpy) | Faible | KB plus riche que 110K |
| **Lazy loading** (charger à la demande) | Moyen | -80% RAM |
| **KB compact** : fusionner les faits similaires | Moyen | -30% |
| **Déployer sur serveur avec 512 MB+** | Nul | Plus de limite |

---

## Action immédiate

```python
# Au lieu de :
facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]

# Faire :
facts = data['facts']  # Garder le numpy array, pas de conversion Python
```

**Gain : ~28 MB (35% de la RAM KB). Le 358K passerait de 120→92 MB.**
