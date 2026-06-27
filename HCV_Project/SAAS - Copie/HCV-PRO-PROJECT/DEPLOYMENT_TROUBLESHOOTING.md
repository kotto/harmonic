# 🌊 DÉPLOIEMENT TROUBLESHOOTING

---

## ❌ **PROBLÈMES IDENTIFIÉS**

### **📋 Logs de votre session**
```yaml
❌ cd /home/ec2-user/HCV-PRO-PROJECT: Not a directory
❌ PARALLEL_MULTI_MODAL_AGGREGATION.py: No such file
❌ uvicorn.service: Unit not found
❌ curl localhost:8000/health: Pas de réponse
```

### **📋 Diagnostic**
```yaml
🔍 Problème 1: Mauvais répertoire de travail
🔍 Problème 2: Fichiers non présents sur EC2
🔍 Problème 3: Service uvicorn non configuré
🔍 Problème 4: Application non démarrée
```

---

## 🔍 **DIAGNOSTIC COMPLET**

### **📋 Étape 1: Trouver les fichiers**
```bash
# Où sont les fichiers ?
find /home -name "*PARALLEL*" 2>/dev/null
find /home -name "*.py" | grep -i parallel 2>/dev/null
ls -la /home/ec2-user/
pwd  # Voir où vous êtes
```

### **📋 Étape 2: Vérifier la structure**
```bash
# Lister le contenu
ls -la
ls -la /home/ec2-user/
find /home -name "*.py" | head -10
```

### **📋 Étape 3: Vérifier les services**
```bash
# Services actifs
sudo systemctl list-units --type=service --state=running | grep -i uvicorn
sudo systemctl list-units --type=service | grep -i python

# Processus actifs
ps aux | grep -i uvicorn
ps aux | grep -i python
```

---

## 🚀 **SOLUTIONS POSSIBLES**

### **📋 Scénario A: Fichiers dans autre répertoire**
```bash
# Chercher les fichiers
find /home -name "PARALLEL_MULTI_MODAL_AGGREGATION.py" 2>/dev/null

# Si trouvé dans /home/ec2-user/HCV-PRO-PROJECT/HCV-PRO-PROJECT
cd /home/ec2-user/HCV-PRO-PROJECT/HCV-PRO-PROJECT

# Continuer le déploiement
cp PARALLEL_MULTI_MODAL_AGGREGATION.py PARALLEL_MULTI_MODAL_AGGREGATION_backup.py
cp PARALLEL_MULTI_MODAL_AGGREGATION_FIXED.py PARALLEL_MULTI_MODAL_AGGREGATION.py
```

### **📋 Scénario B: Fichiers à transférer**
```bash
# Si les fichiers ne sont pas sur l'instance
# Il faut les transférer depuis votre machine locale

# Option 1: SFTP (si disponible)
sftp -i votre-key.pem ec2-user@54.166.179.141
put PARALLEL_MULTI_MODAL_AGGREGATION_FIXED.py /home/ec2-user/
exit

# Option 2: Copier-coller contenu dans nano
nano PARALLEL_MULTI_MODAL_AGGREGATION.py
# Coller le contenu du fichier FIXED
# Ctrl+X, Y, Enter pour sauvegarder
```

### **📋 Scénario C: Service non configuré**
```bash
# Créer le service uvicorn
sudo nano /etc/systemd/system/uvicorn.service

# Contenu du fichier:
[Unit]
Description=Uvicorn FastAPI Server
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user
Environment="PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ec2-user/.local/bin/uvicorn PARALLEL_MULTI_MODAL_AGGREGATION:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

# Sauvegarder et activer
sudo systemctl daemon-reload
sudo systemctl enable uvicorn
sudo systemctl start uvicorn
```

---

## 🛠️ **PLAN D'ACTION IMMÉDIAT**

### **📋 Diagnostic rapide**
```bash
# 1. Où suis-je ?
pwd
ls -la

# 2. Chercher les fichiers
find /home -name "*PARALLEL*" 2>/dev/null

# 3. Vérifier les processus
ps aux | grep -i uvicorn
ps aux | grep -i python

# 4. Vérifier les ports
netstat -tlnp | grep 8000
```

### **📋 Si fichiers trouvés**
```bash
# Se déplacer au bon endroit
cd /répertoire/trouvé

# Déployer
cp PARALLEL_MULTI_MODAL_AGGREGATION.py PARALLEL_MULTI_MODAL_AGGREGATION_backup.py
cp PARALLEL_MULTI_MODAL_AGGREGATION_FIXED.py PARALLEL_MULTI_MODAL_AGGREGATION.py

# Démarrer service
python3 PARALLEL_MULTI_MODAL_AGGREGATION.py
```

### **📋 Si fichiers NON trouvés**
```bash
# Créer le fichier directement
nano PARALLEL_MULTI_MODAL_AGGREGATION.py

# Copier le contenu depuis DEBUG_DASHBOARD.html ou depuis votre machine locale
# Ou créer une version simplifiée pour tester
```

---

## 🧪 **TEST ALTERNATIF**

### **📋 Version simplifiée pour test rapide**
```python
# Créer un fichier test_simple.py
nano test_simple.py

# Contenu:
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Test simple - Timeout fix working"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/generate")
async def generate(request: dict):
    return {
        "content": "Test response - working",
        "confidence": 0.95,
        "processing_time": 0.1
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Démarrer
python3 test_simple.py
```

---

## 📊 **VALIDATION**

### **📋 Après démarrage**
```bash
# Test 1: Health
curl http://localhost:8000/health

# Test 2: Generate
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","use_parallel":true}'

# Test 3: Dashboard
# Actualiser DEBUG_DASHBOARD.html
```

---

## 🌊 **CONCLUSION**

### **📋 Problèmes identifiés**
```yaml
❌ Répertoire: Mauvais chemin
❌ Fichiers: Non présents sur EC2
❌ Service: Non configuré
❌ Application: Non démarrée
```

### **📋 Solutions proposées**
```yaml
🔍 Diagnostic: Trouver les fichiers
🛠️ Déploiement: Transférer ou créer
🚀 Service: Configurer uvicorn
🧪 Test: Version simplifiée
```

### **📋 Prochaine action**
```yaml
1. 🔍 Exécuter: Commandes diagnostic
2. 📋 Reporter: Résultats trouvés
3. 🚀 Déployer: Solution appropriée
4. ✅ Valider: Avec dashboard
```

---

**Status: 🟡 DÉPLOIEMENT BLOQUÉ - DIAGNOSTIC REQUIS**

**Fichiers non trouvés sur EC2. Diagnostic et transfert requis avant déploiement.**
