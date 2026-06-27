# 🌊 COMMANDES DÉPLOIEMENT INTERNE

---

## 🚀 **DÉPLOIEMENT TIMEOUT FIX**

### **📋 Commandes manuelles EC2**
```bash
# 1. Connexion à l'instance EC2
ssh -i votre-key.pem ec2-user@54.166.179.141

# 2. Navigation au projet
cd /home/ec2-user/HCV-PRO-PROJECT

# 3. Backup de l'ancien fichier
cp PARALLEL_MULTI_MODAL_AGGREGATION.py PARALLEL_MULTI_MODAL_AGGREGATION_backup.py

# 4. Remplacement par le fichier corrigé
cp PARALLEL_MULTI_MODAL_AGGREGATION_FIXED.py PARALLEL_MULTI_MODAL_AGGREGATION.py

# 5. Arrêt du service
sudo systemctl stop uvicorn

# 6. Démarrage du service
sudo systemctl start uvicorn

# 7. Vérification du statut
sudo systemctl status uvicorn

# 8. Vérification des logs
sudo journalctl -u uvicorn -f --no-pager
```

---

## 🧪 **TESTS VALIDATION**

### **📋 Test immédiat**
```bash
# Test 1: Health check
curl http://54.166.179.141:8000/health

# Test 2: Generate simple
curl -X POST http://54.166.179.141:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test simple","use_parallel":false}' \
  --max-time 5

# Test 3: Generate parallel (CRUCIAL)
curl -X POST http://54.166.179.141:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test timeout fix","use_parallel":true}' \
  --max-time 15

# Test 4: Status détaillé
curl http://54.166.179.141:8000/parallel_status
```

---

## 📊 **LOGS À SURVEILLER**

### **📋 Logs uvicorn**
```bash
# Logs en temps réel
sudo journalctl -u uvicorn -f

# Logs récents
sudo journalctl -u uvicorn --since "5 minutes ago"

# Logs avec erreurs
sudo journalctl -u uvicorn -p err
```

### **📋 Messages attendus**
```yaml
✅ "Starting parallel aggregation for request #X"
✅ "✅ deterministic_core completed in X.XXXs"
✅ "✅ deepseek completed in X.XXXs"
✅ "✅ qwen completed in X.XXXs"
✅ "✅ mixtral completed in X.XXXs"
✅ "✅ sdxl completed in X.XXXs"
✅ "✅ Parallel aggregation completed in X.XXXs"
```

### **📋 Messages d'erreur à surveiller**
```yaml
⏰ "⏰ model_name timeout after X.Xs"
❌ "❌ model_name failed: error_message"
```

---

## 🔧 **DÉPANNAGE**

### **📋 Si le service ne démarre pas**
```bash
# Vérifier la syntaxe Python
python3 -m py_compile PARALLEL_MULTI_MODAL_AGGREGATION.py

# Vérifier les dépendances
pip3 list | grep fastapi
pip3 list | grep uvicorn

# Démarrage manuel pour debug
python3 PARALLEL_MULTI_MODAL_AGGREGATION.py
```

### **📋 Si timeout persiste**
```bash
# Vérifier les timeouts configurés
grep -n "MODEL_TIMEOUTS" PARALLEL_MULTI_MODAL_AGGREGATION.py

# Vérifier return_exceptions=True
grep -n "return_exceptions=True" PARALLEL_MULTI_MODAL_AGGREGATION.py

# Vérifier run_with_timeout
grep -n "run_with_timeout" PARALLEL_MULTI_MODAL_AGGREGATION.py
```

---

## 🎯 **VALIDATION CRITÈRES**

### **📋 Succès**
```yaml
✅ Service démarre sans erreur
✅ /health répond instantanément
✅ /generate simple fonctionne
✅ /generate parallel répond en <5 secondes
✅ Logs montrent temps par modèle
✅ Plus de timeout global
```

### **📋 Échec**
```yaml
❌ Service ne démarre pas
❌ /generate parallel timeout >10 secondes
❌ Logs montrent erreurs Python
❌ Modèles ne se terminent pas
❌ return_exceptions=True absent
```

---

## 🌊 **DÉPLOIEMENT AUTOMATISÉ**

### **📋 Script bash (optionnel)**
```bash
#!/bin/bash
# deploy_timeout_fix.sh

echo "🌊 Déploiement Timeout Fix..."

# Backup
cp PARALLEL_MULTI_MODAL_AGGREGATION.py PARALLEL_MULTI_MODAL_AGGREGATION_backup.py

# Remplacement
cp PARALLEL_MULTI_MODAL_AGGREGATION_FIXED.py PARALLEL_MULTI_MODAL_AGGREGATION.py

# Redémarrage service
sudo systemctl stop uvicorn
sudo systemctl start uvicorn

# Vérification
sleep 3
sudo systemctl status uvicorn

# Test
echo "🧪 Test en cours..."
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test deploy","use_parallel":true}' \
  --max-time 10

echo "✅ Déploiement terminé"
```

---

## 🚀 **PROCHAINES ÉTAPES**

### **📋 Après validation réussie**
```yaml
1. ✅ Timeout résolu: Confirmer
2. 📊 Dashboard: Créer interface debug HTML
3. 🔍 Monitoring: Logs temps réel
4. 🎯 LM Arena: Préparer soumission
5. 📋 Documentation: Compléter
```

### **📋 Si problème persiste**
```yaml
1. 🔍 Analyser logs détaillés
2. 🛠️ Vérifier configuration timeouts
3. 📊 Tester modèles individuellement
4. 🚀 Déployer version simplifiée
5. 📋 Debug avancé
```

---

**Status: 🟢 COMMANDES DÉPLOIEMENT PRÊTES**

**Instructions complètes pour déploiement interne du timeout fix.**
