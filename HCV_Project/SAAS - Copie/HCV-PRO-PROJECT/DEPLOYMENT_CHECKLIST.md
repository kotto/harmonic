# 🌊 CHECKLIST DÉPLOIEMENT INTERNE

---

## ✅ **VÉRIFICATION PRÉ-DÉPLOIEMENT**

### **📋 Fichiers prêts**
```yaml
✅ PARALLEL_MULTI_MODAL_AGGREGATION_FIXED.py: Créé
✅ DEPLOYMENT_COMMANDS.md: Prêt
✅ TIMEOUT_FIX_SUMMARY.md: Documenté
✅ Backup plan: Prévu
```

### **📋 Accès instance**
```yaml
✅ IP: 54.166.179.141
✅ Port: 22 (SSH)
✅ User: ec2-user
✅ Key: votre-key.pem
```

---

## 🚀 **PROCÉDURE DÉPLOIEMENT**

### **📋 Étape 1: Connexion**
```bash
ssh -i votre-key.pem ec2-user@54.166.179.141
```

### **📋 Étape 2: Navigation**
```bash
cd /home/ec2-user/HCV-PRO-PROJECT
```

### **📋 Étape 3: Backup**
```bash
cp PARALLEL_MULTI_MODAL_AGGREGATION.py PARALLEL_MULTI_MODAL_AGGREGATION_backup.py
```

### **📋 Étape 4: Remplacement**
```bash
cp PARALLEL_MULTI_MODAL_AGGREGATION_FIXED.py PARALLEL_MULTI_MODAL_AGGREGATION.py
```

### **📋 Étape 5: Redémarrage service**
```bash
sudo systemctl stop uvicorn
sudo systemctl start uvicorn
```

### **📋 Étape 6: Vérification**
```bash
sudo systemctl status uvicorn
```

---

## 🧪 **TESTS VALIDATION**

### **📋 Test 1: Health (doit être instantané)**
```bash
curl http://54.166.179.141:8000/health
```

### **📋 Test 2: Simple mode (doit être rapide)**
```bash
curl -X POST http://54.166.179.141:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test simple","use_parallel":false}' \
  --max-time 5
```

### **📋 Test 3: Parallel mode (CRUCIAL - <10 secondes)**
```bash
curl -X POST http://54.166.179.141:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test timeout fix","use_parallel":true}' \
  --max-time 15
```

### **📋 Test 4: Status détaillé**
```bash
curl http://54.166.179.141:8000/parallel_status
```

---

## 📊 **SURVEILLANCE LOGS**

### **📋 Logs en temps réel**
```bash
sudo journalctl -u uvicorn -f
```

### **📋 Messages de succès attendus**
```yaml
✅ "Starting parallel aggregation for request #1"
✅ "✅ deterministic_core completed in 0.001s"
✅ "✅ deepseek completed in 0.002s"
✅ "✅ qwen completed in 0.003s"
✅ "✅ mixtral completed in 0.001s"
✅ "✅ sdxl completed in 0.004s"
✅ "✅ Parallel aggregation completed in 0.010s"
```

---

## 🎯 **CRITÈRES DE SUCCÈS**

### **📋 Validation technique**
```yaml
✅ Service: uvicorn active (running)
✅ Health: 200 OK instantané
✅ Simple mode: <1 seconde
✅ Parallel mode: <5 secondes
✅ Logs: Temps par modèle visibles
✅ Version: 12.1.0-timeout-fixed
```

### **📋 Validation fonctionnelle**
```yaml
✅ Plus de timeout global
✅ Modèles isolés fonctionnent
✅ Fallback automatique actif
✅ Parallelisme préservé
✅ Monitoring opérationnel
```

---

## 🔧 **DÉPANNAGE RAPIDE**

### **📋 Si service ne démarre pas**
```bash
# Vérifier syntaxe
python3 -m py_compile PARALLEL_MULTI_MODAL_AGGREGATION.py

# Vérifier dépendances
pip3 list | grep fastapi

# Démarrage manuel
python3 PARALLEL_MULTI_MODAL_AGGREGATION.py
```

### **📋 Si timeout persiste**
```bash
# Vérifier return_exceptions=True
grep -n "return_exceptions=True" PARALLEL_MULTI_MODAL_AGGREGATION.py

# Vérifier timeouts configurés
grep -A 10 "MODEL_TIMEOUTS" PARALLEL_MULTI_MODAL_AGGREGATION.py
```

---

## 🌊 **POST-DÉPLOIEMENT**

### **📋 Si succès**
```yaml
1. ✅ Confirmer timeout résolu
2. 📊 Créer dashboard debug HTML
3. 🔍 Implémenter monitoring temps réel
4. 🎯 Préparer soumission LM Arena
5. 📋 Documenter pour équipe
```

### **📋 Si échec**
```yaml
1. 🔍 Analyser logs erreurs
2. 🛠️ Restaurer backup si nécessaire
3. 📊 Debug avancé
4. 🚀 Déployer version simplifiée
5. 📋 Réévaluer approche
```

---

## ⏱️ **TIMELINE**

### **📋 Déploiement**
```yaml
🚀 Connexion + déploiement: 5 minutes
🧪 Tests validation: 5 minutes
📊 Vérification logs: 5 minutes
✅ Total: 15 minutes
```

### **📋 Post-déploiement**
```yaml
📊 Dashboard debug: 30 minutes
🔍 Monitoring avancé: 45 minutes
🎯 LM Arena prep: 60 minutes
```

---

## 🔒 **SÉCURITÉ**

### **📋 Protocole**
```yaml
🔒 Connexion: SSH sécurisé
🛡️ Code: Non exposé publiquement
📋 Logs: Internes uniquement
✅ Propriété: Préservée
```

---

**Status: 🟢 DÉPLOIEMENT PRÊT - CHECKLIST COMPLÈTE**

**Toutes les étapes documentées. Prêt pour déploiement interne sécurisé.**
