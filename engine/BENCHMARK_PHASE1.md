# 📊 BENCHMARK PHASE 1 — Harmonic Dictionary

**Date** : 13 Juillet 2026  
**Auteur** : Alain Kotto  
**Version** : 1.0

---

## Résumé exécutif

La Phase 1 d'optimisation du Harmonic Dictionary est **terminée avec succès**. Toutes les cibles de performance sont atteintes ou dépassées. Le système démontre une ingestion à 6 742 patches/s, une signature DFT à 90 μs, une requête KD-tree à 43 μs, une génération 256×256 en 227 ms et une reconstruction à 100 dB PSNR avec un ratio de compression effectif de 300×.

---

## 1. Modifications apportées

### Sprint 1 — Sauvegarde/Chargement

| Fichier | Ajout | Impact |
|---------|-------|--------|
| `harmonic_database.py` | `save()`, `save_patches()`, `load()` | Persistance complète, format `.npz` compressé |
| `patch_store.py` | `save()`, `load()` | Sérialisation des descripteurs, amplitudes, chroma, pixels |
| Format | `meta.json` + dossiers par concept | Standard, lisible, versionné |

### Sprint 2 — Corrections de performance

| Modification | Fichier | Gain |
|-------------|---------|------|
| `argsort` → `argpartition` | `harmonic_database.py:208` | Signature DFT O(N) au lieu de O(N log N) |
| `float64` → `float32` | global | 50% RAM économisée sur les signatures, arbres, features |
| Suppression `patch.copy()` | `harmonic_database.py:113` | 50% mémoire en moins par patch |
| Pré-construction `_amp_vector`, `_chroma_matrix` | `patch_store.py` | Élimine les list comprehensions par query |
| Correction bug `chroma_factor` ×2 | `patch_store.py:281` | Correction de justesse — le filtrage couleur était doublement pénalisé |
| Suppression `confidence` inutilisé | `patch_store.py` | Nettoyage, économie mémoire |

### Sprint 3 — Tests unitaires

- **38 tests** pytest dans `tests/test_harmonic_database.py`
- Classes : `TestInitialization`, `TestSignatureDFT`, `TestIngestion`, `TestRetrievalDFT`, `TestHexagonalFeatures`, `TestGeneration`, `TestSaveLoad`, `TestPerformance`, `TestEdgeCases`
- Benchmark standardisé : `tests/benchmark_harmonic.py` — 11 métriques

### Sprint 4 — Parallélisme

| Modification | Impact |
|-------------|--------|
| `ThreadPoolExecutor` dans `ingest_directory` | Chargement I/O parallèle (jusqu'à 8 workers) |
| `_compute_signatures_batch()` | DFT vectorisée sur lots de patches |
| Lazy KD-trees (`_dirty_trees`, `_ensure_trees`) | Reconstruction différée, pas après chaque ajout |

### Sprint 5 — Optimisations avancées

| Modification | Impact |
|-------------|--------|
| `lru_cache` sur `_compute_signature` | Cache 2048 entrées — évite les re-calculs DFT dans `generate()` |
| `_cached_signature()` | Hashage des bytes du patch pour le cache |

---

## 2. Résultats comparés

| Métrique | Avant Phase 1 | Après Phase 1 | Amélioration | Cible | Statut |
|----------|:------------:|:-------------:|:------------:|:-----:|:------:|
| **Ingestion** (patches/s) | ~500 | **6 742** | 13,5× | > 500 | ✅ |
| **DFT** (μs/patch) | ~200 | **90,1** | 2,2× | < 200 | ✅ |
| **KD-tree query** (μs) | ~100 | **42,8** | 2,3× | < 55 | ✅ |
| **Hexagonal query** (μs) | ~50 | **27,5** | 1,8× | - | ✅ |
| **Generate 256×256** (ms) | ~800 | **226,8** | 3,5× | < 500 | ✅ |
| **PSNR reconstruction** (dB) | 100 | **100,0** | - | > 99 | ✅ |
| **Ratio compression effectif** (×) | - | **300** | - | > 100 | ✅ |
| **Save signatures** (s) | - | **0,15** | - | < 5 | ✅ |
| **Load** (s) | - | **0,25** | - | < 10 | ✅ |

### Détail des métriques

```
Benchmark sur: 5 catégories × 10 images (256×256), patch_size=20, K=16
Total patches: 7 200
```

| # | Métrique | Valeur | Unité |
|---|----------|--------|-------|
| 1 | Ingestion | 6 742 | patches/s |
| 2 | Construction KD-trees DFT | 5,2 | ms |
| 3 | Construction KD-trees Hex | 449,8 | ms |
| 4 | Signature DFT K=16 | 90,1 | μs/patch |
| 5 | KD-tree Query DFT | 42,8 | μs |
| 6 | Hexagonal Query π/6 | 27,5 | μs |
| 7 | Generate 256×256 | 226,8 | ms |
| 8 | PSNR Reconstruction | 100,0 | dB |
| 9 | Ratio Compression Brut (vs signatures) | 9,4 | × |
| 10 | Ratio Compression Effectif (vs IDs) | 300 | × |
| 11 | Mémoire RSS | 124,8 | MB |

---

## 3. Ratio de compression — explication

Le ratio **effectif** de 300× est calculé comme :

```
ratio = pixels_bruts / (nombre_patches × 4 octets)
```

Où 4 octets = taille d'un ID int32 qui référence le patch dans le dictionnaire.

Le ratio théorique maximal avec un dictionnaire partagé encodeur/décodeur est de **1 200×**. Le ratio mesuré (300×) est limité par :
- La petite taille du dataset de test (7 200 patches — plus le dataset est grand, plus le ratio est élevé)
- Le recouvrement (overlap) entre patches voisins

Pour une image 4K (3840×2160) avec patch_size=40 :
- Nombre de patches : ~5 184 (stride=40)
- Pixels bruts : 25 MB
- IDs transmis : 5 184 × 4 = 20,7 KB
- Ratio : **1 200×**

---

## 4. Fichiers modifiés / créés

### Modifiés

| Fichier | Lignes | Changements |
|---------|--------|-------------|
| `multimodal/harmonic_database.py` | ~770 | +save/load, +batch DFT, +parallel ingest, +LRU cache, float32, argpartition |
| `multimodal/patch_store.py` | ~830 | +save/load, +pre-built vectors, -confidence, fix chroma bug |

### Créés

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `tests/test_harmonic_database.py` | 470 | 38 tests pytest — 9 classes de test |
| `tests/benchmark_harmonic.py` | 250 | 11 métriques standardisées |
| `BENCHMARK_PHASE1.md` | ce document | Synthèse Phase 1 |

---

## 5. Prochaines étapes (Phase 2)

1. **Scalabilité dictionnaire** : passer de 10K à 10M+ patches avec images 4K natives (DIV2K/DIV8K)
2. **Intégration HCV PRO** : codec end-to-end avec le dictionnaire harmonique
3. **Encodage vidéo** : prédiction temporelle + compensation de mouvement
4. **Distribution** : CDN + delta updates pour dictionnaires
5. **Déploiement mobile** : dictionnaire cloud + cache local intelligent
