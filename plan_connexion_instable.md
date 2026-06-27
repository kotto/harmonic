# 🔧 PLAN D'ACTION - CONNEXION INTERNET INSTABLE

## 📅 Date : 15 Mai 2026
## 🎯 Objectif : Adapter le workflow Harmonic AI pour une connexion internet instable

---

## 🎯 **DIAGNOSTIC**

### **Problème identifié :** Connexion internet instable
### **Impact :** Timeouts sur les connexions AWS, tests LM Arena intermittents
### **Bonne nouvelle :** L'infrastructure AWS fonctionne probablement correctement

---

## 🚀 **STRATÉGIE RECOMMANDÉE**

### **1. Mode de travail hybride**
- **Local** : Développement et tests locaux
- **Cloud** : Déploiement et benchmarks AWS
- **Synchronisation** : Scripts de sauvegarde/restauration

### **2. Tests adaptés**
- **Tests courts** : Limiter la durée des tests
- **Retry automatique** : Mécanisme de réessai
- **Sauvegarde résultats** : Enregistrement progressif

### **3. Déploiement optimisé**
- **Build local** : Préparation locale
- **Upload optimisé** : Transfert par morceaux
- **Validation incrémentale** : Vérification étape par étape

---

## 📋 **PLAN D'ACTION DÉTAILLÉ**

### **ÉTAPE 1 : CONFIGURATION LOCALE**

#### **1.1 Environnement de développement local**
```bash
# Créer un environnement Python virtuel
python -m venv venv_harmonic
.\venv_harmonic\Scripts\activate

# Installer les dépendances minimales
pip install fastapi uvicorn requests pydantic
```

#### **1.2 API locale de démonstration**
```python
# Fichier : api_local_demo.py
from fastapi import FastAPI
from pydantic import BaseModel
import json

app = FastAPI(title="Harmonic AI Local Demo")

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 100

@app.post("/generate")
async def generate(request: GenerationRequest):
    # Réponse de démonstration locale
    demo_response = {
        "text": f"[DEMO LOCAL] Réponse pour: {request.prompt[:50]}...",
        "tokens_generated": min(100, request.max_tokens),
        "deterministic": True,
        "response_id": "demo_local_12345"
    }
    return demo_response

@app.get("/health")
async def health():
    return {"status": "healthy", "mode": "local_demo"}
```

#### **1.3 Lancement local**
```bash
# Démarrer l'API locale
uvicorn api_local_demo:app --host 0.0.0.0 --port 8001

# Tester localement
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test local", "max_tokens": 50}'
```

### **ÉTAPE 2 : TESTS ADAPTÉS**

#### **2.1 Tests LM Arena optimisés**
```python
# Fichier : lm_arena_optimise.py
import requests
import time
import json
from datetime import datetime

class LM_Arena_Optimise:
    def __init__(self, base_url="http://localhost:8001", max_retries=3):
        self.base_url = base_url
        self.max_retries = max_retries
        self.results_file = "lm_arena_results_partial.json"
        
    def test_with_retry(self, prompt, max_tokens=100):
        """Test avec mécanisme de réessai"""
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/generate",
                    json={"prompt": prompt, "max_tokens": max_tokens},
                    timeout=5  # Timeout court
                )
                return response.json()
            except requests.exceptions.Timeout:
                print(f"Timeout attempt {attempt+1}/{self.max_retries}")
                time.sleep(2)  # Pause avant réessai
            except Exception as e:
                print(f"Erreur: {e}")
                break
        return {"error": "Échec après réessais"}
    
    def run_tests_graduels(self, tests, batch_size=3):
        """Exécuter les tests par petits lots"""
        results = []
        
        for i in range(0, len(tests), batch_size):
            batch = tests[i:i+batch_size]
            print(f"Lot {i//batch_size + 1}: {len(batch)} tests")
            
            for test in batch:
                result = self.test_with_retry(test["prompt"], test.get("max_tokens", 100))
                results.append({
                    "test": test["name"],
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Sauvegarder après chaque test
                self.save_partial_results(results)
                print(f"  ✓ Test '{test['name']}' terminé")
            
            # Pause entre les lots
            time.sleep(5)
        
        return results
    
    def save_partial_results(self, results):
        """Sauvegarder les résultats partiels"""
        with open(self.results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(results),
                "results": results
            }, f, indent=2)
```

#### **2.2 Tests courts prioritaires**
```python
# Tests essentiels (rapides)
tests_essentiels = [
    {"name": "health_check", "prompt": "Test santé"},
    {"name": "simple_math", "prompt": "2+2="},
    {"name": "short_reasoning", "prompt": "Si il pleut, je prends un parapluie. Il pleut. Que fais-je?"},
    {"name": "basic_code", "prompt": "Python: print('hello')"},
]
```

### **ÉTAPE 3 : SYNCHRONISATION INTELLIGENTE**

#### **3.1 Script de sauvegarde locale**
```python
# Fichier : backup_local.py
import shutil
import os
import json
from datetime import datetime

class BackupManager:
    def __init__(self, backup_dir="backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def backup_results(self, results_file):
        """Sauvegarder les résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.backup_dir}/results_{timestamp}.json"
        
        if os.path.exists(results_file):
            shutil.copy2(results_file, backup_file)
            print(f"Backup créé: {backup_file}")
            return backup_file
        return None
    
    def restore_latest(self, target_file):
        """Restaurer la dernière sauvegarde"""
        backups = sorted([f for f in os.listdir(self.backup_dir) 
                         if f.startswith("results_")])
        
        if backups:
            latest = backups[-1]
            shutil.copy2(f"{self.backup_dir}/{latest}", target_file)
            print(f"Restauré: {latest} -> {target_file}")
            return True
        return False
```

#### **3.2 Transfert par morceaux**
```python
# Fichier : transfert_par_morceaux.py
import requests
import os
import json

class ChunkedTransfer:
    def __init__(self, chunk_size=1024*1024):  # 1MB par morceau
        self.chunk_size = chunk_size
    
    def upload_large_file(self, file_path, upload_url, chunk_callback=None):
        """Upload d'un gros fichier par morceaux"""
        file_size = os.path.getsize(file_path)
        chunks = (file_size + self.chunk_size - 1) // self.chunk_size
        
        with open(file_path, 'rb') as f:
            for i in range(chunks):
                chunk = f.read(self.chunk_size)
                
                # Essayer plusieurs fois par morceau
                for attempt in range(3):
                    try:
                        response = requests.post(
                            upload_url,
                            files={'chunk': chunk},
                            data={'chunk_index': i, 'total_chunks': chunks},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            if chunk_callback:
                                chunk_callback(i+1, chunks)
                            break
                        else:
                            print(f"Échec morceau {i+1}, tentative {attempt+1}")
                    except Exception as e:
                        print(f"Erreur morceau {i+1}: {e}")
                        time.sleep(2)
```

### **ÉTAPE 4 : VALIDATION INCRÉMENTALE**

#### **4.1 Vérification étape par étape**
```python
# Fichier : validation_incrementale.py
import time
import json

class IncrementalValidation:
    def __init__(self, checkpoints_file="checkpoints.json"):
        self.checkpoints_file = checkpoints_file
        self.checkpoints = self.load_checkpoints()
    
    def load_checkpoints(self):
        """Charger les points de contrôle"""
        if os.path.exists(self.checkpoints_file):
            with open(self.checkpoints_file, 'r') as f:
                return json.load(f)
        return {"completed": [], "pending": []}
    
    def mark_completed(self, checkpoint_name):
        """Marquer un point de contrôle comme terminé"""
        if checkpoint_name in self.checkpoints["pending"]:
            self.checkpoints["pending"].remove(checkpoint_name)
        self.checkpoints["completed"].append({
            "name": checkpoint_name,
            "timestamp": time.time()
        })
        self.save_checkpoints()
        print(f"✓ Point de contrôle '{checkpoint_name}' terminé")
    
    def add_pending(self, checkpoint_name):
        """Ajouter un point de contrôle en attente"""
        if checkpoint_name not in self.checkpoints["pending"]:
            self.checkpoints["pending"].append(checkpoint_name)
            self.save_checkpoints()
    
    def save_checkpoints(self):
        """Sauvegarder les points de contrôle"""
        with open(self.checkpoints_file, 'w') as f:
            json.dump(self.checkpoints, f, indent=2)
```

---

## 🎯 **WORKFLOW RECOMMANDÉ**

### **Phase 1 : Développement local (connexion instable)**
```
1. Activer l'environnement virtuel
2. Démarrer l'API locale (port 8001)
3. Développer et tester localement
4. Sauvegarder les résultats localement
```

### **Phase 2 : Synchronisation (connexion stable momentanée)**
```
1. Vérifier la stabilité de la connexion
2. Synchroniser avec AWS (petits lots)
3. Valider étape par étape
4. Sauvegarder les points de contrôle
```

### **Phase 3 : Validation finale (connexion stable)**
```
1. Exécuter les tests complets
2. Valider les performances
3. Générer le rapport final
4. Préparer la soumission LM Arena
```

---

## 🔧 **OUTILS CRÉÉS**

### **1. API locale de démonstration**
- `api_local_demo.py` : API FastAPI locale
- Fonctionne sans connexion internet
- Simule les réponses de Harmonic AI

### **2. Tests optimisés**
- `lm_arena_optimise.py` : Tests avec réessai
- `tests_essentiels` : Tests courts prioritaires
- Mécanisme de sauvegarde incrémentale

### **3. Gestion de sauvegarde**
- `backup_local.py` : Sauvegarde/restauration
- `transfert_par_morceaux.py` : Transfert robuste
- `validation_incrementale.py` : Validation étape par étape

---

## 📊 **RECOMMANDATIONS PRATIQUES**

### **1. Travail hors ligne**
- Développer les fonctionnalités localement
- Tester avec l'API locale
- Préparer les scripts de déploiement

### **2. Synchronisation intelligente**
- Attendre les moments de connexion stable
- Synchroniser par petits lots
- Valider après chaque lot

### **3. Gestion des erreurs**
- Enregistrer les erreurs localement
- Reprendre là où ça s'est arrêté
- Sauvegarder les progrès régulièrement

---

## 🚀 **ACTION IMMÉDIATE**

### **1. Démarrer l'environnement local**
```bash
# Activer l'environnement virtuel
.\venv_harmonic\Scripts\activate

# Démarrer l'API locale
python api_local_demo.py
```

### **2. Exécuter les tests locaux**
```bash
# Tester l'API locale
python -c "import requests; r = requests.post('http://localhost:8001/generate', json={'prompt': 'test'}); print(r.json())"
```

### **3. Préparer la synchronisation**
```bash
# Créer les sauvegardes locales
python backup_local.py
```

---

## 📞 **SUPPORT ET DÉPANNAGE**

### **Problèmes courants et solutions :**

#### **1. Connexion perdue pendant les tests**
```
Solution : 
- Les résultats sont sauvegardés après chaque test
- Reprendre là où ça s'est arrêté
- Utiliser le mécanisme de réessai
```

#### **2. Upload interrompu**
```
Solution :
- Transfert par morceaux
- Reprise sur interruption
- Validation incrémentale
```

#### **3. Validation incomplète**
```
Solution :
- Points de contrôle
- Sauvegarde progressive
- Reprise sélective
```

---

## 🎯 **CONCLUSION**

### **✅ Avantages de cette approche :**

1. **Indépendance** : Travail possible sans connexion stable
2. **Robustesse** : Mécanismes de réessai et sauvegarde
3. **Efficacité** : Synchronisation optimisée
4. **Fiabilité** : Validation incrémentale

### **📋 Prochaines étapes :**

1. **Configurer l'environnement local**
2. **Développer les fonctionnalités localement**
3. **Synchroniser avec AWS lors des moments stables**
4. **Valider les performances complètes**

### **🚀 Action recommandée maintenant :**

```bash
# 1. Créer l'environnement virtuel
python -m venv venv_harmonic

# 2. Activer l'environnement
.\venv_harmonic\Scripts\activate

# 3. Installer les dépendances minimales
pip install fastapi uvicorn requests pydantic

# 4. Démarrer l'API locale
python api_local_demo.py
```

**Avec cette approche, vous pouvez continuer à développer et tester Harmonic AI même avec une connexion internet instable !**