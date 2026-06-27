# 🔧 Prompts Expert pour Résolution Technique

## 📊 **Contexte Problème**
```yaml
❌ Endpoint /generate: TIMEOUT 30s
✅ /health: Fonctionne parfaitement
✅ 5 modèles: Chargés et prêts
✅ Service: Running et healthy
🔍 Architecture: FastAPI + Uvicorn + 5 modèles locaux
```

## 🎯 **Prompts Expert IA**

### **Prompt 1: Diagnostic Architecture**
```
Expert FastAPI: Notre endpoint /generate timeout mais /health fonctionne. 
Service running, 5 modèles chargés, mais toute requête /generate expire après 30s.
Logs montrent "Read timed out" systématique.
Identifiez la cause racine et proposez 3 solutions immédiates.
```

### **Prompt 2: Analyse Code Handler**
```
Expert Python: Analysez ce handler /generate qui timeout:
- FastAPI endpoint
- 5 modèles locaux chargés
- Agrégation parallèle
- Timeout sur chaque requête

Cause probable: deadlock, boucle infinie, ou problème threading.
Proposez le code corrigé.
```

### **Prompt 3: Diagnostic Multithreading**
```
Expert concurrence: 5 modèles locaux synchronisés en parallèle.
Handler /generate bloque complètement.
Hypothèses: GIL, deadlock inter-modèles, ou resource lock.
Diagnostiquez et fournissez solution threading.
```

### **Prompt 4: Optimisation Performance**
```
Expert performance: Service healthy mais /generate timeout.
5 modèles chargés, mémoire OK, mais handler bloqué.
Identifiez goulots d'étranglement et optimisez pour <2s réponse.
```

### **Prompt 5: Debug Production**
```
Expert debug: Production AWS EC2, FastAPI timeout.
Health OK, modèles chargés, mais /generate mort.
Fournissez script debug complet et stratégie de résolution.
```

## 📋 **Logs Réels à Fournir**
```yaml
🔍 Service logs: 
- INFO:PARALLEL_MULTI_MODAL_AGGREGATION:Response: 200 (health OK)
- INFO: 128.79.142.16:14280 - "GET /health HTTP/1.1" 200 OK
- Aucune log /generate (timeout avant log)
📊 Processus: PID 2537 uvicorn[2537] running
❌ Erreur: HTTPConnectionPool(host='54.166.179.140', port=8000): Read timed out. (read timeout=30)
✅ Success: /health 200 OK répété chaque minute
🔍 Pattern: Health fonctionne, /generate bloque complètement
```

### **Prompt 6: Diagnostic Complet avec Logs**
```
Expert FastAPI: Voici les logs complets de notre problème:

Service state:
- PID 2537 uvicorn[2537] running
- /health: 200 OK (logs: "INFO:PARALLEL_MULTI_MODAL_AGGREGATION:Response: 200")
- /generate: timeout 30s (aucune log générée)
- 5 modèles locaux chargés (deepseek_s3: loaded)

Error pattern:
HTTPConnectionPool(host='54.166.179.140', port=8000): Read timed out. (read timeout=30)

Logs montrent uniquement les requêtes /health, aucune trace /generate.
Diagnostiquez pourquoi /generate bloque avant logging.
```

### **Prompt 7: Solution Code Spécifique**
```
Expert Python: Notre handler /generate deadlock complet.
Architecture: FastAPI + uvicorn + 5 modèles locaux.
Health fonctionne mais generate timeout avant même le premier log.

Hypothèses:
1. Boucle infinie dans le handler
2. Deadlock threading entre modèles
3. Resource lock sur modèles chargés
4. GIL Python avec 5 modèles

Fournissez le code corrigé pour le handler /generate.
```

## 🚀 **Action Immédiate**
Utilisez ces prompts avec IA expert pour:
1. Diagnostiquer cause racine (avec logs réels)
2. Obtenir code corrigé spécifique
3. Déployer solution immédiate
4. Valider benchmarks LM Arena
