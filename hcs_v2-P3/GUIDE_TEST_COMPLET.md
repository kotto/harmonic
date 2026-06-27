# 🧪 Guide de Test Complet - Système HCS

## Testez Tout le Système Étape par Étape

---

## 📋 ÉTAPE 1: Test des Modules Core (Compression)

### 1.1 Test du K-Factor Engine
```bash
python -c "from core.k_factor_engine import KFactorEngine; import numpy as np; e = KFactorEngine(0.02); img = np.random.rand(480,640,3).astype(np.float32); c,m = e.compress_image(img); print(f'K-Factor OK - Ratio: {m[\"actual_ratio\"]:.1f}:1')"
```

**Résultat attendu :** `Ratio: ~35-50:1`

### 1.2 Test du WebP Optimizer
```bash
python -c "from core.webp_optimizer import WebPOptimizer; import numpy as np; w = WebPOptimizer(95); img = (np.random.rand(480,640,3)*255).astype(np.uint8); d,m = w.optimize_image(img); print(f'WebP OK - Ratio: {m[\"compression_ratio\"]:.1f}:1')"
```

**Résultat attendu :** `Ratio: ~30-100:1`

### 1.3 Test du Hybrid Compressor (Complet)
```bash
python -c "from core.hybrid_compressor import HybridCompressor; import numpy as np; h = HybridCompressor(0.02, 95); img = np.random.rand(480,640,3).astype(np.float32); d,m = h.compress_image(img); print(f'Hybrid OK - Ratio: {m[\"hybrid_ratio\"]:.1f}:1, FPS: {m[\"fps_estimate\"]:.1f}')"
```

**Résultat attendu :** `Ratio: ~200-1000:1, FPS: ~20-40`

---

## 📋 ÉTAPE 2: Test des Métriques Complètes

### 2.1 Lancer le script de test complet
```bash
python test_compression_metrics.py
```

**Ce que ça teste :**
- ✅ K-Factor Engine sur 4 résolutions
- ✅ WebP Optimizer sur 5 types de contenu
- ✅ Hybrid Compressor avec benchmark
- ✅ Video Parameter Optimizer

**Résultat :** Fichier `compression_test_results.json` généré

---

## 📋 ÉTAPE 3: Test de la Stratégie PRO

### 3.1 Afficher les presets disponibles
```bash
python pro_compression_strategy.py
```

**Résultat attendu :** Affichage des 4 presets (MASTER, BROADCAST, STREAMING, ARCHIVE)

### 3.2 Tester la compression avec un preset
```python
# Créer un fichier test_pro.py
from pro_compression_strategy import ProVideoCompressionStrategy, ProQualityPreset
import numpy as np

# Test avec preset BROADCAST
strategy = ProVideoCompressionStrategy(ProQualityPreset.BROADCAST)
print(f"Config: K={strategy.config.k_factor}, WebP={strategy.config.webp_quality}")
print(f"Description: {strategy.config.description}")
print("[OK] Stratégie PRO fonctionne!")
```

Exécuter :
```bash
python test_pro.py
```

---

## 📋 ÉTAPE 4: Test du Système Interactif

### 4.1 Mode automatique (déjà testé)
```bash
python interactive_auto_demo.py
```

**Résultat :** Profil généré et sauvegardé dans `profile_broadcast_auto.json`

### 4.2 Mode interactif (manuel)
```bash
python interactive_compression_system.py
```

**Suivre les instructions :**
1. Choisir mode (Assisté ou Expert)
2. Répondre aux 4 questions (si mode assisté)
3. Confirmer le profil généré
4. Sauvegarder le profil

---

## 📋 ÉTAPE 5: Test avec une Vidéo Réelle

### 5.1 Préparer une vidéo de test
```bash
# Si vous avez une vidéo, sinon créez-en une avec OpenCV
python -c "
import cv2
import numpy as np

# Créer une vidéo de test
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('test_video.mp4', fourcc, 30.0, (640, 480))

for i in range(90):  # 3 secondes
    frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, f'Frame {i}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    out.write(frame)

out.release()
print('Vidéo test_video.mp4 créée (3 sec, 640x480)')
"
```

### 5.2 Compresser la vidéo
```python
# Créer compress_test.py
from pro_compression_strategy import ProVideoCompressionStrategy, ProQualityPreset

strategy = ProVideoCompressionStrategy(ProQualityPreset.BROADCAST)
result = strategy.compress_video_pro('test_video.mp4')

print(f"\n=== RÉSULTATS ===")
print(f"Ratio: {result['compression']['ratio']:.1f}:1")
print(f"Qualité: {result['compression']['quality_score']:.3f}")
print(f"Standard respecté: {result['compression']['meets_standard']}")
print(f"Paramètres utilisés: K={result['compression']['parameters']['k_factor']}")
```

Exécuter :
```bash
python compress_test.py
```

---

## 📋 ÉTAPE 6: Test Complet Automatisé

### 6.1 Créer un script de test global
```python
# test_complet_hcs.py
#!/usr/bin/env python3
print("="*70)
print("TEST COMPLET DU SYSTÈME HCS")
print("="*70)

# Test 1: Modules core
print("\n[1/5] Test modules core...")
try:
    from core.k_factor_engine import KFactorEngine
    from core.webp_optimizer import WebPOptimizer
    from core.hybrid_compressor import HybridCompressor
    print("   [OK] Imports réussis")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 2: Stratégie PRO
print("\n[2/5] Test stratégie PRO...")
try:
    from pro_compression_strategy import ProVideoCompressionStrategy, ProQualityPreset
    strategy = ProVideoCompressionStrategy(ProQualityPreset.BROADCAST)
    print(f"   [OK] Config: K={strategy.config.k_factor}, WebP={strategy.config.webp_quality}")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 3: Système interactif
print("\n[3/5] Test système interactif...")
try:
    from interactive_compression_system import CompressionProfile
    profile = CompressionProfile(
        name="Test", usage_type="broadcast", priority="balanced",
        k_factor=0.012, webp_quality=88, temporal_weight=0.8,
        quality_threshold=0.88, expected_ratio="100:1",
        description="Test", expert_mode=False
    )
    print(f"   [OK] Profil créé: {profile.name}")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 4: Compression image
print("\n[4/5] Test compression image...")
try:
    import numpy as np
    from core.hybrid_compressor import HybridCompressor
    compressor = HybridCompressor(0.02, 95)
    img = np.random.rand(480, 640, 3).astype(np.float32)
    data, meta = compressor.compress_image(img)
    print(f"   [OK] Ratio: {meta['hybrid_ratio']:.1f}:1, FPS: {meta['fps_estimate']:.1f}")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 5: Métriques
print("\n[5/5] Test métriques...")
try:
    stats = compressor.get_stats()
    print(f"   [OK] Total traité: {stats['total_processed']}")
    print(f"   [OK] Ratio moyen: {stats['total_hybrid_ratio']:.1f}:1")
except Exception as e:
    print(f"   [FAIL] {e}")

print("\n" + "="*70)
print("TEST COMPLET TERMINÉ")
print("="*70)
```

Exécuter :
```bash
python test_complet_hcs.py
```

---

## 📊 Tableau de Validation

| Test | Commande | Résultat Attendu | Statut |
|------|----------|------------------|--------|
| K-Factor | `python -c "from core.k_factor_engine..."` | Ratio ~35-50:1 | ⬜ |
| WebP | `python -c "from core.webp_optimizer..."` | Ratio ~30-100:1 | ⬜ |
| Hybrid | `python -c "from core.hybrid_compressor..."` | Ratio ~200-1000:1 | ⬜ |
| Métriques | `python test_compression_metrics.py` | JSON généré | ⬜ |
| PRO | `python pro_compression_strategy.py` | 4 presets affichés | ⬜ |
| Interactif Auto | `python interactive_auto_demo.py` | Profil sauvegardé | ⬜ |
| Interactif | `python interactive_compression_system.py` | 4 questions | ⬜ |
| Vidéo | `python compress_test.py` | Compression OK | ⬜ |
| Complet | `python test_complet_hcs.py` | Tous [OK] | ⬜ |

---

## 🔍 En Cas de Problème

### Erreur "Module not found"
```bash
# Ajouter le répertoire au PYTHONPATH
set PYTHONPATH=f:\FINAL\DEFINITIF\hcs_v2-P3;%PYTHONPATH%
```

### Erreur Unicode (Windows)
```python
# Au début de chaque script
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
```

### Erreur de dépendances
```bash
pip install numpy pillow opencv-python scipy
```

---

## ✅ Checklist Finale

- [ ] Test K-Factor Engine OK
- [ ] Test WebP Optimizer OK
- [ ] Test Hybrid Compressor OK
- [ ] Test Métriques OK
- [ ] Test Stratégie PRO OK
- [ ] Test Système Interactif OK
- [ ] Test Vidéo réelle OK
- [ ] Rapport de test généré

**Tous les tests passés = Système HCS 100% opérationnel !** 🎉
