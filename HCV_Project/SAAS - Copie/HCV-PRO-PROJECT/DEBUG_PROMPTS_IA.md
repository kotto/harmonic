# 🌊 PROMPTS D'AIDE AU DÉBOGAGE IA

---

## 🎯 **PROMPTS GÉNÉRAUX**

### **📋 Prompt 1: Erreur 500 Mode Parallèle**
```
J'ai un système multi-modèles avec 5 composants qui fonctionne en mode simple mais retourne "Internal Server Error" en mode parallèle. Le mode simple utilise un générateur harmonique simple, le mode parallèle devrait agréger 5 modèles avec asyncio.gather(). 

Symptômes:
- Health check: 200 OK
- Mode simple: 200 OK avec réponse harmonique
- Mode parallèle: 500 Internal Server Error
- Processus actif et stable

Quelles sont les causes possibles d'une erreur 500 uniquement en mode parallèle avec agrégation asynchrone?
```

### **📋 Prompt 2: Imports et Dépendances**
```
J'ai une application Python/FastAPI qui importe plusieurs modules. Un module spécifique (harmonic_response_generator_simple) manquait au début et causait ModuleNotFoundError. Maintenant l'application démarre mais une fonctionnalité spécifique retourne 500.

Comment diagnostiquer si l'erreur 500 vient d'imports manquants, de dépendances manquantes ou de problèmes de configuration dans une application multi-modèles?
```

### **📋 Prompt 3: AsyncIO et Agrégation**
```
J'ai une fonction qui utilise asyncio.gather() pour exécuter 5 tâches parallèles. En mode simple tout fonctionne, mais en mode parallèle j'obtiens Internal Server Error.

Les 5 tâches sont des appels à différents modèles avec des poids différents (40%, 25%, 15%, 10%, 10%). L'agrégation devrait combiner les résultats avec une pondération harmonique.

Quelles erreurs peuvent survenir avec asyncio.gather() dans un contexte FastAPI qui fonctionneraient en mode synchrone mais pas en mode asynchrone?
```

---

## 🔧 **PROMPTS TECHNIQUES SPÉCIFIQUES**

### **📋 Prompt 4: FastAPI et Mode Parallèle**
```
J'ai une application FastAPI avec un endpoint /generate qui accepte un paramètre "use_parallel". Quand use_parallel=false, tout fonctionne. Quand use_parallel=true, j'obtiens 500.

Le code fait appel à une classe d'agrégation qui utilise asyncio.gather() pour 5 modèles. La réponse devrait être agrégée avec des poids et des bonus.

Comment déboguer une erreur 500 spécifique au mode parallèle dans FastAPI? Quels logs consulter?
```

### **📋 Prompt 5: Configuration Multi-Modèles**
```
J'ai configuré 5 modèles différents avec des poids spécifiques dans un système d'agrégation. Le système fonctionne en mode simple mais échoue en mode parallèle.

La configuration inclut:
- Un modèle core (40%)
- Un modèle S3 local (25%) 
- Un modèle multi-fichiers (15%)
- Un modèle efficient (10%)
- Un modèle révolutionnaire (10%)

Quels problèmes de configuration peuvent causer une erreur 500 uniquement en mode agrégation parallèle?
```

### **📋 Prompt 6: JSON et Parsing**
```
Mon endpoint FastAPI accepte du JSON. Quand j'envoie {"prompt": "test", "use_parallel": false}, ça fonctionne. Quand j'envoie {"prompt": "test", "use_parallel": true}, j'obtiens 500.

Le parsing JSON semble fonctionner car l'endpoint reçoit les données, mais l'erreur survient pendant le traitement.

Comment différencier une erreur de parsing JSON d'une erreur de traitement interne dans FastAPI?
```

---

## 🌐 **PROMPTS RÉSEAU ET ACCÈS**

### **📋 Prompt 7: Accès Externe vs Local**
```
Mon service fonctionne parfaitement en local (localhost:8000) mais n'est pas accessible depuis l'extérieur (IP publique:8000). J'ai vérifié que le port 8000 est ouvert dans le security group.

Le processus écoute sur 0.0.0.0:8000 et le netstat montre le port comme LISTEN.

Quelles autres causes peuvent empêcher l'accès externe quand le service local fonctionne et le security group est correct?
```

### **📋 Prompt 8: Timeout et Firewall**
```
J'ai un service sur port 8000 qui timeout depuis l'extérieur mais fonctionne en local. Le security group AWS autorise 0.0.0.0/0 sur le port 8000.

Le service utilise FastAPI avec uvicorn et écoute sur 0.0.0.0:8000.

Quelles configurations réseau ou firewall peuvent causer ce comportement de timeout externe uniquement?
```

---

## 🏗️ **PROMPTS ARCHITECTURE**

### **📋 Prompt 9: Système Multi-Modèles**
```
J'implémente un système qui agrège 5 modèles différents avec des poids spécifiques. Chaque modèle a sa propre classe et méthode de génération. L'agrégation utilise asyncio.gather().

Le système fonctionne en mode simple (un seul modèle) mais échoue en mode parallèle (agrégation des 5).

Quels patterns d'architecture ou problèmes de concurrence peuvent causer ce comportement?
```

### **📋 Prompt 10: Qualité et Enhancement**
```
J'ai un système qui applique 5 couches d'amélioration de qualité sur les réponses. En mode simple, les 5 couches fonctionnent. En mode parallèle, j'ajoute ces couches à une agrégation de 5 modèles et j'obtiens une erreur 500.

Les couches de qualité incluent: structure, cohérence, clarté, richesse, validation finale.

Comment l'ajout de couches de traitement peut-il causer une erreur dans un système d'agrégation parallèle?
```

---

## 🐛 **PROMPTS DÉBOGAGE SPÉCIFIQUE**

### **📋 Prompt 11: Logging et Erreurs**
```
J'ai une erreur 500 dans FastAPI mais les logs ne montrent pas l'erreur détaillée. Le service continue de fonctionner pour les autres requêtes.

Comment activer un logging détaillé pour capturer l'exception complète qui cause l'erreur 500 dans un mode spécifique de mon application?
```

### **📋 Prompt 12: Mémoire et Ressources**
```
Mon application fonctionne avec des requêtes simples mais échoue avec des requêtes complexes qui agrègent 5 modèles. L'erreur est 500 Internal Server Error.

Comment vérifier si l'erreur vient de problèmes de mémoire, de ressources ou de limites système dans une application multi-modèles?
```

---

## 🎯 **PROMPTS DE RÉSOLUTION**

### **📋 Prompt 13: Approche Progressive**
```
J'ai un système avec 5 modèles qui échoue en mode parallèle. Le mode simple fonctionne.

Quelle approche progressive recommandez-vous pour isoler le problème:
1. Tester chaque modèle individuellement en parallèle?
2. Tester l'agrégation avec 2 modèles seulement?
3. Vérifier les imports et dépendances?
4. Examiner la configuration asynchrone?
```

### **📋 Prompt 14: Tests Unitaires**
```
Je veux créer des tests unitaires pour diagnostiquer pourquoi mon mode parallèle échoue mais le mode simple fonctionne.

Quels tests unitaires spécifiques devrais-je créer pour:
1. Tester chaque modèle individuellement
2. Tester l'agrégation progressive
3. Tester la configuration asynchrone
4. Isoler le composant qui cause l'erreur 500
```

---

## 📝 **INSTRUCTIONS UTILISATION**

### **📋 Comment utiliser ces prompts:**
1. **Copiez-collez** le prompt pertinent dans votre IA
2. **Adaptez** si nécessaire avec vos spécificités
3. **Suivez** les recommandations données
4. **Testez** les solutions proposées

### **📋 Ordre recommandé:**
1. Commencer par **Prompt 1** (erreur 500 générale)
2. Continuer avec **Prompt 4** (FastAPI spécifique)
3. Utiliser **Prompt 3** (asyncio/parallel)
4. Essayer **Prompt 7** (accès externe)
5. Finir avec **Prompt 13** (approche progressive)

---

**🌊 Ces prompts sont conçus pour aider à diagnostiquer les problèmes sans révéler les détails technologiques spécifiques de votre système.**
