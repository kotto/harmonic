# Guide de Test Simple - HCV PRO Mobile

## 🚀 Test Rapide en 5 Étapes

### Prérequis
- Python 3.11+ installé
- Environnement virtuel créé
- Accès au dossier `HCV-PRO-PROJECT/mobile`

---

## Étape 1: Installation des Dépendances

```bash
# Navigation vers le projet
cd "f:/SAAS - Copie/HCV-PRO-PROJECT/mobile"

# Création de l'environnement virtuel (si non existant)
python -m venv venv

# Activation de l'environnement
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt
```

### Vérification rapide
```bash
# Vérifier que les modules principaux sont installés
python -c "import psutil; print('✅ psutil OK')"
python -c "import aiohttp; print('✅ aiohttp OK')"
python -c "import cv2; print('✅ OpenCV OK')"
```

---

## Étape 2: Test du Service Hermes

```bash
# Lancer le test d'intégration Hermes
python test_hermes_integration.py
```

**Résultat attendu :**
```
🚀 Test d'intégration HCV PRO + Hermes
=====================================
--- Import Hermes ---
✅ Hermes integration importée avec succès
⚠️ OpenClaw Integration est déprécié. Utilisez Hermes Integration à la place.
✅ Compatibilité rétrograde OpenClaw -> Hermes fonctionnelle

--- Service Hermes ---
🪶 HermesService démarré (métriques système).
✅ Service Hermes démarré
✅ Métriques obtenues: {'active_handles': 0, 'cpu_percent': 0.0, ...}
🪶 HermesService arrêté.

--- Dépendances ---
✅ Hermes agent trouvé dans requirements.txt

📊 RÉSUMÉ DES TESTS
✅ PASS - Import Hermes
✅ PASS - Service Hermes
❌ FAIL - Intégration HCV + Hermes (attendu - codecs manquants)
✅ PASS - Dépendances

📈 Résultat: 3/4 tests passés
🎉 L'intégration Hermes est fonctionnelle!
```

---

## Étape 3: Test de Gemma 4 Multimodal

```bash
# Test du module multimodal
python gemma_multimodal.py
```

**Résultat attendu :**
```
✅ Gemma 4 Multimodal
✅ Analyse photos et vidéos en local
✅ Aucune donnée ne sort du téléphone
✅ Service démarré
✅ Analyse automatique en arrière plan
```

**Test de recherche :**
```python
# Dans un terminal Python
from gemma_multimodal import gemma_search

# Tester la recherche
results = gemma_search("montagne")
print(f"Fichiers trouvés: {results}")
```

---

## Étape 4: Test de Gemma 4 Orchestrator

```bash
# Test de l'orchestrateur
python gemma_orchestrator.py
```

**Résultat attendu :**
```
✅ Gemma 4 Orchestrator
✅ Phase 3 - Intelligence
✅ Orchestrateur démarré
✅ Prend les décisions automatiquement
✅ Ne pose jamais aucune question
```

**Test de décision :**
```python
# Dans un terminal Python
from gemma_orchestrator import gemma_decide

# Tester une décision
decision = gemma_decide("/path/to/photo.jpg")
print(f"Décision: {decision}")
# Résultat attendu: {'profile': 'balanced', 'retention_days': 30, 'should_upscale': True}
```

---

## Étape 5: Test du Bridge Server

```bash
# Démarrer le serveur de pont
python bridge_server.py
```

**Résultat attendu :**
```
🚀 HCV PRO - Bridge Server
====================================
📱 Bridge WebSocket démarré sur ws://localhost:8765
🔍 Surveillance des fichiers activée
🤖 Services IA initialisés
✅ Serveur prêt pour les connexions
```

**Test WebSocket :**
```javascript
// Dans un navigateur (console F12)
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    console.log('✅ Connecté au bridge server');
    ws.send(JSON.stringify({
        action: 'test_connection',
        timestamp: Date.now()
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📨 Message reçu:', data);
};
```

---

## 🧪 Tests Complémentaires

### Test de Compression Manuel

```python
# Créer un fichier de test simple
import cv2
import numpy as np

# Créer une image test
image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
cv2.imwrite('test_image.jpg', image)

# Tester la compression (si les codecs sont disponibles)
try:
    from hcv_openclaw_integration import HCVHermesIntegration
    
    config = {
        'device_id': 'test_device',
        'hermes_config_path': '~/.hermes',
        'hermes_workspace': './test_workspace',
        'device_info': {'ram_gb': 8, 'storage_gb': 256, 'cpu_cores': 8}
    }
    
    integration = HCVHermesIntegration(config)
    print("✅ Intégration HCV créée avec succès")
    
except ImportError as e:
    print(f"⚠️ Intégration HCV non disponible (attendu): {e}")
```

### Test des Métriques Système

```python
# Test des métriques avec Hermes
from hermes_integration import HermesService

service = HermesService()
service.start()

# Obtenir les métriques
stats = service.get_stats()
print("📊 Métriques système:")
print(f"   CPU: {stats['cpu_percent']}%")
print(f"   RAM: {stats['ram_used_mb']}/{stats['ram_total_mb']} MB")
print(f"   Handles: {stats['active_handles']}")

service.stop()
```

### Test de File d'Attente

```python
# Test de la file d'attente de traitement
from gemma_multimodal import gemma_multimodal_init, gemma_analyze

# Démarrer le service
gemma_multimodal_init()

# Ajouter des fichiers à analyser
test_files = ['test1.jpg', 'test2.png', 'test3.mp4']
for file in test_files:
    gemma_analyze(file)
    print(f"📁 {file} ajouté à la file d'attente")

# Le traitement se fait en arrière-plan
print("⏳ Analyse en cours...")
```

---

## 🔍 Dépannage Rapide

### Problèmes Courants

#### 1. ImportError: Module non trouvé
```bash
# Solution: Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall
```

#### 2. Permission denied (Windows)
```bash
# Solution: Exécuter en tant qu'administrateur
# ou désactiver temporairement l'antivirus
```

#### 3. Port déjà utilisé
```bash
# Solution: Changer de port dans bridge_server.py
# ou tuer le processus existant
netstat -ano | findstr :8765
taskkill /PID <PID> /F
```

#### 4. Mémoire insuffisante
```bash
# Solution: Fermer d'autres applications
# ou utiliser un profil plus léger
```

### Vérifications Rapides

```bash
# Vérifier Python
python --version

# Vérifier les modules clés
python -c "import sys; print(sys.version)"

# Vérifier l'environnement
pip list | grep -E "(aiohttp|opencv|psutil)"

# Vérifier les fichiers de test
ls -la *.py
```

---

## 📊 Critères de Succès

### ✅ Tests Réussis Si:

1. **Hermes Service** démarre et retourne des métriques
2. **Gemma Multimodal** s'initialise sans erreur
3. **Gemma Orchestrator** prend des décisions
4. **Bridge Server** écoute sur le port WebSocket
5. **Aucun crash** majeur pendant 5 minutes

### ⚠️ Avertissements Acceptables:

- Messages de dépréciation OpenClaw → Hermes
- ImportErrors pour les codecs HCV (attendu)
- Warnings de ressources système

### ❌ Échecs à Corriger:

- ImportError sur les modules de base
- Impossible de démarrer les services IA
- Crash du bridge server
- Erreurs de mémoire critique

---

## 🚀 Test Complet Automatisé

```bash
# Script de test complet
python -c "
import subprocess
import sys

tests = [
    ('Hermes Integration', 'python test_hermes_integration.py'),
    ('Gemma Multimodal', 'python gemma_multimodal.py'),
    ('Gemma Orchestrator', 'python gemma_orchestrator.py'),
]

for name, cmd in tests:
    print(f'🧪 Test: {name}')
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f'✅ {name} - OK')
        else:
            print(f'❌ {name} - ERROR: {result.stderr}')
    except Exception as e:
        print(f'⚠️ {name} - TIMEOUT: {e}')
"
```

---

## 📞 Support

Si vous rencontrez des problèmes :

1. **Vérifiez les logs** : Chaque service affiche des messages détaillés
2. **Testez par étapes** : Lancez chaque service individuellement
3. **Vérifiez les ressources** : CPU, RAM, espace disque disponible
4. **Consultez la documentation** : `HERMES_MIGRATION_SUMMARY.md`

---

## 🎉 Conclusion

Après ces tests simples, vous devriez avoir :

- ✅ **Hermes Agent** fonctionnel
- ✅ **Gemma 4 IA** opérationnelle  
- ✅ **Bridge Server** prêt
- ✅ **Architecture** validée

L'application est prête pour le développement et les tests avancés ! 🚀

---

*Guide de test créé le 27 avril 2026 - Version 1.0*
