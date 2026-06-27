# 🌊 PROBLÈME CRITIQUE SSM PARSING

---

## 🚨 **DIAGNOSTIC DU PROBLÈME**

### **📋 Erreur systématique**
```yaml
❌ Erreur: Error parsing parameter '--parameters'
❌ Cause: JSON parsing échoue systématiquement
🔍 Pattern: Même erreur répétitive
🛠️ Impact: Impossible d'exécuter toute commande SSM
```

### **📋 Commande testée**
```bash
aws ssm send-command --instance-ids i-0716d7805ca2c22e9 --document-name "AWS-RunShellScript" --parameters '["cd /opt/connective-ai","cp PARALLEL_MULTI_MODAL_AGGREGATION.py PARALLEL_MULTI_MODAL_AGGREGATION_before_debug.py"]'
```

### **📋 Erreur retournée**
```yaml
❌ Message: Error parsing parameter '--parameters'
❌ Détail: Invalid JSON
❌ Pattern: Répéte à chaque tentative
🚨 Blocage: Total des opérations SSM
```

---

## 🔍 **ANALYSE TECHNIQUE**

### **📋 Causes possibles**
```yaml
🔍 Hypothèse 1: Caractères spéciaux invisibles
🔍 Hypothèse 2: Échappement JSON incorrect
🔍 Hypothèse 3: Problème encoding UTF-8
🔍 Hypothèse 4: Version AWS CLI incompatible
🔍 Hypothèse 5: Format parameters obsolète
```

### **📋 Éléments suspects**
```yaml
❌ Underscores: PARALLEL_MULTI_MODAL_AGGREGATION.py
❌ Longueur: Nom de fichier très long
❌ Pattern: Répétition exacte de l'erreur
🔍 Environnement: Possible problème shell/CLI
```

---

## 🛠️ **SOLUTIONS ALTERNATIVES**

### **📋 Option 1: Session Manager (Recommandé)**
```bash
# Utiliser AWS Session Manager directement
aws ssm start-session --target i-0716d7805ca2c22e9

# Puis exécuter les commandes directement
cd /opt/connective-ai
cp PARALLEL_MULTI_MODAL_AGGREGATION.py PARALLEL_MULTI_MODAL_AGGREGATION_before_debug.py
sudo systemctl stop connective-ai-boost
```

### **📋 Option 2: Fichier script distant**
```bash
# Créer script sur S3 puis l'exécuter
aws s3 cp debug_script.sh s3://bucket/debug_script.sh
aws ssm send-command --instance-ids i-0716d7805ca2c22e9 --document-name "AWS-RunShellScript" --parameters '["bash /tmp/debug_script.sh"]'
```

### **📋 Option 3: CLI direct avec --cli-input-json**
```bash
# Format JSON explicite
aws ssm send-command \
  --instance-ids i-0716d7805ca2c22e9 \
  --document-name "AWS-RunShellScript" \
  --cli-input-json '{"parameters": ["cd /opt/connective-ai","cp PARALLEL_MULTI_MODAL_AGGREGATION.py PARALLEL_MULTI_MODAL_AGGREGATION_before_debug.py"]}'
```

### **📋 Option 4: Simplification extrême**
```bash
# Commande minimale
aws ssm send-command --instance-ids i-0716d7805ca2c22e9 --document-name "AWS-RunShellScript" --parameters '["pwd"]'
```

---

## 🎯 **PLAN D'ACTION IMMÉDIAT**

### **📋 Test diagnostic**
```yaml
1. 🔍 Tester commande simple (pwd)
2. 📊 Vérifier si parsing fonctionne
3. 🛠️ Identifier le problème exact
4. ⚡ Appliquer solution adaptée
```

### **📋 Approche recommandée**
```yaml
🥇 Session Manager: Plus fiable et direct
🥈 CLI JSON: Si session manager échoue
🥉 Script distant: Alternative robuste
🏃 Simplification: Dernière option
```

---

## 🌊 **STATUS CRITIQUE**

### **📋 Impact sur le debug**
```yaml
🚨 Blocage total: Impossible d'exécuter commands SSM
❌ Debug suspendu: Plus d'accès à l'instance
⏱️ Timeline: Indéterminée
🎯 Objectif: Résolution accès SSM
```

### **📋 Problème sous-jacent**
```yaml
🔍 Technique: Parsing JSON SSM
🛠️ Environnement: Possible corruption CLI
📋 Configuration: À vérifier
⚡ Urgence: Maximale
```

---

## 🎯 **RECOMMANDATION FINALE**

### **📋 Action immédiate**
```yaml
🚨 Priorité 1: Session Manager
aws ssm start-session --target i-0716d7805ca2c22e9

🚨 Priorité 2: Diagnostic CLI
aws --version
aws configure list

🚨 Priorité 3: Test commande simple
aws ssm send-command --instance-ids i-0716d7805ca2c22e9 --document-name "AWS-RunShellScript" --parameters '["pwd"]'
```

---

## 🌊 **CONCLUSION**

### **📋 Situation critique**
```yaml
🚨 SSM parsing: Complètement bloqué
❌ Commandes: Aucune ne passe
🛠️ Debug: Suspendu
⏱️ Résolution: Requise immédiatement
```

### **📋 Issue technique**
```yaml
🔍 Problème: JSON parsing systématique
🛠️ Cause: Inconnue (encoding/format)
🎯 Solution: Alternative d'accès requise
⚡ Action: Session Manager recommandée
```

---

**Status: 🚨 BLOCAGE SSM TOTAL - ALTERNATIVE D'ACCÈS REQUISE**

**Le parsing JSON échoue systématiquement. Session Manager est la solution recommandée pour reprendre le contrôle.**
