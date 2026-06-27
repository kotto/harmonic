# 🧪 Guide Complet des Tests - H.264 → HCV16

## 🚀 Tests Rapides (5 minutes)

### 1. **Test POC Complet** ⭐ RECOMMANDÉ
```bash
cd h264_hcv16_recompression
python validate_poc.py
```
**Résultat attendu:** 100% tests réussis, ratio moyen ~1.20×

### 2. **Test Processeur Production**
```bash
cd h264_hcv16_production
python test_simple_processor.py
```
**Résultat attendu:** 86% tests réussis, performance 2.5 jobs/s

---

## 🔬 Tests Détaillés par Composant

### **A. Tests Algorithmes de Détection**

#### Test Détection Artefacts
```bash
cd h264_hcv16_recompression
python tests/test_h264_analysis.py
```

**Ce qui est testé:**
- Détection blocking artifacts (8×8, 16×16)
- Analyse motion residuals
- Quantization noise detection
- Temporal patterns analysis

**Résultats attendus:**
```
Tests exécutés: 6
Tests réussis: 6 (100%)
Ratio moyen: 1.187×
Économie moyenne: 18.7%
```

#### Test Démonstration Interactive
```bash
cd h264_hcv16_recompression
python examples/demo_recompression.py
```

**Options disponibles:**
1. Démonstration automatique
2. Démonstration interactive (recommandé)

### **B. Tests Processeur Production**

#### Test Fonctionnalités Core
```bash
cd h264_hcv16_production
python simple_test.py
```

#### Test Processeur Complet
```bash
cd h264_hcv16_production
python test_simple_processor.py
```

**Fonctionnalités testées:**
- Cycle de vie processeur
- Traitement jobs individuels
- Traitement jobs multiples
- Gestion d'erreurs
- Configuration
- Performance

---

## 🎯 Tests avec Fichiers Réels

### **Test avec Votre Fichier Vidéo**

#### 1. Préparation
```bash
# Copier votre fichier vidéo dans le dossier
cp /chemin/vers/votre/video.mp4 h264_hcv16_production/

# Ou utiliser un fichier existant
ls *.mp4  # Vérifier fichiers disponibles
```

#### 2. Test Simple avec Processeur
```bash
cd h264_hcv16_production
python core/simple_processor.py votre_video.mp4 output_compressed.hcv16
```

**Résultat attendu:**
```
🚀 Processeur Production H.264 → HCV16 (Simplifié)
Job soumis: h264_hcv16_xxxxx
Statut: processing
Statut: completed
✅ Succès: 1.120× en 2.3s
```

#### 3. Test avec Analyse Détaillée
```python
# Créer test_custom.py
import sys
sys.path.append('h264_hcv16_recompression/src')

from h264_analyzer import H264Analyzer

# Analyse votre fichier
analyzer = H264Analyzer()
results = analyzer.analyze_file("votre_video.mp4", max_frames=50)

# Affichage rapport
print(analyzer.generate_report())
```

---

## 📊 Tests de Performance

### **Test Charge (Multiple Fichiers)**

#### Créer Script de Test
```python
# test_batch.py
import os
import time
from h264_hcv16_production.core.simple_processor import SimpleProductionProcessor

processor = SimpleProductionProcessor()
processor.start()

# Liste vos fichiers
video_files = [f for f in os.listdir('.') if f.endswith('.mp4')]

job_ids = []
start_time = time.time()

# Soumission batch
for video_file in video_files:
    output_file = video_file.replace('.mp4', '_compressed.hcv16')
    job_id = processor.submit_job(video_file, output_file)
    job_ids.append(job_id)
    print(f"Job soumis: {job_id}")

# Monitoring
while True:
    stats = processor.get_statistics()
    print(f"Progress: {stats['jobs_processed']}/{len(job_ids)} jobs")
    
    if stats['jobs_processed'] >= len(job_ids):
        break
    time.sleep(2)

# Résultats
processing_time = time.time() - start_time
final_stats = processor.get_statistics()

print(f"\n📈 RÉSULTATS BATCH:")
print(f"Fichiers traités: {final_stats['jobs_processed']}")
print(f"Temps total: {processing_time:.1f}s")
print(f"Ratio moyen: {final_stats['avg_compression_ratio']:.3f}×")
print(f"Économies totales: {final_stats['total_savings_mb']:.1f}MB")

processor.stop()
```

```bash
python test_batch.py
```

---

## 🔧 Tests de Configuration

### **Test Configuration Personnalisée**

#### 1. Créer Configuration Custom
```json
// custom_config.json
{
  "max_workers": 4,
  "batch_size": 5,
  "temp_directory": "./temp_processing",
  "output_quality": 90,
  "max_file_size_mb": 1000,
  "supported_formats": [".mp4", ".avi"],
  "monitoring_interval": 15
}
```

#### 2. Test avec Configuration
```python
from h264_hcv16_production.core.simple_processor import SimpleProductionProcessor

# Test config personnalisée
processor = SimpleProductionProcessor("custom_config.json")
print(f"Workers: {processor.config['max_workers']}")
print(f"Formats supportés: {processor.config['supported_formats']}")
```

---

## 🚨 Tests de Robustesse

### **Test Gestion d'Erreurs**

#### Script Test Erreurs
```python
# test_errors.py
from h264_hcv16_production.core.simple_processor import SimpleProductionProcessor
import tempfile
import os

processor = SimpleProductionProcessor()
processor.start()

print("🧪 Test gestion d'erreurs...")

# 1. Fichier inexistant
try:
    processor.submit_job("inexistant.mp4", "output.hcv16")
    print("❌ Erreur: devrait échouer")
except FileNotFoundError:
    print("✅ Fichier inexistant géré")

# 2. Format non supporté
with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
    f.write(b'test')
    temp_file = f.name

try:
    processor.submit_job(temp_file, "output.hcv16")
    print("❌ Erreur: devrait échouer")
except ValueError:
    print("✅ Format non supporté géré")
finally:
    os.remove(temp_file)

# 3. Fichier trop volumineux
processor.config['max_file_size_mb'] = 0.001  # 1KB max

with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
    f.write(b'x' * 2000)  # 2KB
    temp_file = f.name

try:
    processor.submit_job(temp_file, "output.hcv16")
    print("❌ Erreur: devrait échouer")
except ValueError:
    print("✅ Fichier trop volumineux géré")
finally:
    os.remove(temp_file)

processor.stop()
print("🎉 Tests d'erreurs terminés")
```

---

## 📈 Interprétation des Résultats

### **Métriques Clés à Surveiller**

#### 1. **Ratio de Compression**
```
1.02× = 2% économie (minimum viable)
1.05× = 5% économie (bon)
1.10× = 10% économie (excellent)
1.20× = 20% économie (exceptionnel)
```

#### 2. **Performance**
```
< 100ms = Excellent (analyse seule)
< 2s = Bon (traitement complet simulé)
< 10s = Acceptable (fichier réel)
> 30s = Lent (optimisation nécessaire)
```

#### 3. **Taux de Succès**
```
100% = Parfait
> 90% = Excellent
> 80% = Bon
< 80% = Problématique
```

### **Diagnostic des Problèmes**

#### Si Ratio < 1.02×
- Fichier déjà très optimisé
- Contenu peu compressible
- Algorithmes à ajuster

#### Si Performance Lente
- Réduire max_workers
- Vérifier ressources système
- Optimiser configuration

#### Si Erreurs Fréquentes
- Vérifier formats fichiers
- Contrôler tailles fichiers
- Valider permissions

---

## 🎯 Tests Recommandés par Cas d'Usage

### **Pour Développeur**
1. `python validate_poc.py` (validation complète)
2. `python test_simple_processor.py` (processeur)
3. Tests avec 1-2 fichiers réels

### **Pour Intégrateur**
1. Tests configuration personnalisée
2. Tests batch avec vos fichiers
3. Tests performance charge

### **Pour Production**
1. Tests robustesse complets
2. Tests monitoring
3. Tests failover et recovery

---

## 🚀 Commandes Rapides

```bash
# Test complet en 1 commande
cd h264_hcv16_recompression && python validate_poc.py

# Test production en 1 commande  
cd h264_hcv16_production && python test_simple_processor.py

# Test avec votre fichier
cd h264_hcv16_production && python core/simple_processor.py votre_video.mp4

# Démonstration interactive
cd h264_hcv16_recompression && python examples/demo_recompression.py
```

---

## 📞 Support

Si vous rencontrez des problèmes :

1. **Vérifiez les prérequis:**
   ```bash
   python --version  # Python 3.8+
   pip list | grep opencv  # OpenCV installé
   ```

2. **Logs détaillés:**
   - Tous les tests affichent des logs détaillés
   - Recherchez les messages d'erreur spécifiques

3. **Tests simplifiés:**
   - Commencez par `validate_poc.py`
   - Puis `test_simple_processor.py`
   - Enfin tests avec fichiers réels

**🎯 Le système est conçu pour être testé facilement à tous les niveaux !**