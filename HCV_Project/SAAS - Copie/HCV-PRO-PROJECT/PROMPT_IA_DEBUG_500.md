# 🌊 PROMPT IA EXPERT - DEBUG ERREUR 500 PERSISTANTE

---

## 🎯 **PROMPT SPÉCIFIQUE POUR DEBUGGING EXPERT**

### **📋 Contexte technique complet**
```
J'ai un système FastAPI avec 5 modèles AI en parallèle. J'ai appliqué une solution IA expert pour corriger une erreur 500 dans le mode parallèle, mais l'erreur persiste dans les deux modes.

Situation actuelle:
✅ Health Check: 200 OK - Service fonctionne
✅ Service: Actif (PID 29250)
✅ Architecture: 5 modèles chargés
✅ Solution IA: MODEL_CONFIG + validation + fallback appliquée
✅ Syntaxe: Python compile correctement (import OK)
❌ Endpoint /generate: 500 dans les deux modes (simple et parallèle)
❌ Logs: Pas de stack trace visible
❌ Debug: Erreur silencieuse

Code appliqué avec succès:
```python
# Configuration modèles
MODEL_CONFIG = [
    ("harmonic_core", {"content": "", "confidence": 0.1, "weight": 0.1}),
    ("deepseek", {"content": "", "confidence": 0.1, "weight": 0.1}),
    ("qwen", {"content": "", "confidence": 0.1, "weight": 0.1}),
    ("mixtral", {"content": "", "confidence": 0.1, "weight": 0.1}),
    ("sdxl", {"content": "", "confidence": 0.1, "weight": 0.1}),
]
MIN_HEALTHY_RATIO = 0.5

raw_results = await asyncio.gather(*tasks, return_exceptions=True)
validated_results = []
success_count = 0

for raw, (name, default) in zip(raw_results, MODEL_CONFIG):
    if isinstance(raw, Exception):
        logger.error(f"Model {name} failed: {type(raw).__name__}: {raw}")
        validated_results.append(default.copy())
    else:
        validated_results.append(raw)
        success_count += 1

healthy_ratio = success_count / len(MODEL_CONFIG)
if healthy_ratio < MIN_HEALTHY_RATIO:
    logger.warning(f"Only {success_count}/{len(MODEL_CONFIG)} models healthy - fallback simple mode")
    return await self.harmonic_core.generate_response(prompt)

core_resp, deepseek_resp, qwen_resp, mixtral_resp, sdxl_resp = validated_results

total_weight = sum(r["weight"] for r in validated_results)
if total_weight <= 0:
    return await self.harmonic_core.generate_response(prompt)

aggregate_confidence = (
    core_resp["confidence"] * core_resp["weight"] +
    deepseek_resp["confidence"] * deepseek_resp["weight"] +
    qwen_resp["confidence"] * qwen_resp["weight"] +
    mixtral_resp["confidence"] * mixtral_resp["weight"] +
    sdxl_resp["confidence"] * sdxl_resp["weight"]
) / total_weight

logger.info(f"Parallel aggregation OK: {success_count}/{len(MODEL_CONFIG)} models, confidence={aggregate_confidence:.3f}")
```

Problème: L'erreur 500 persiste malgré cette solution. Les logs ne montrent aucune erreur. Le service répond correctement au health check mais échoue sur /generate.
```

### **📋 Demande d'aide expert**
```
J'ai besoin d'aide pour diagnostiquer une erreur 500 silencieuse dans un système FastAPI. 

Situation:
- Health check fonctionne (200 OK)
- 5 modèles chargés avec succès
- Solution IA expert appliquée (validation + fallback)
- Python compile correctement
- Mais /generate retourne 500 dans les deux modes
- Aucune stack trace dans les logs

Hypothèses possibles:
1. Erreur Pydantic: Validation des modèles de requête/réponse
2. Erreur import: Module manquant ou chemin incorrect
3. Erreur logique: Problème dans la logique de génération
4. Erreur réseau: Problème avec les modèles externes
5. Erreur config: Configuration manquante ou invalide
6. Erreur async: Problème avec asyncio ou les coroutines
7. Erreur mémoire: Problème d'allocation ou de garbage collection
8. Erreur timeout: Timeout silencieux des modèles externes

Pouvez-vous m'aider à:
1. Identifier la cause probable de cette erreur 500 silencieuse
2. Fournir une stratégie de debugging systématique
3. Proposer des solutions spécifiques pour chaque hypothèse
4. Donner du code pour ajouter un logging détaillé
5. Suggérer des tests pour isoler le problème
```

### **📋 Contraintes techniques**
```yaml
- Framework: FastAPI avec Python 3.7
- Architecture: 5 modèles AI parallèles
- Logging: logging.basicConfig(level=logging.DEBUG) déjà configuré
- Service: Actif sur port 8000
- Environment: EC2 avec virtual environment
- Models: Harmonic + DeepSeek + Qwen + Mixtral + SDXL
```

---

## 🔧 **SOLUTION DEBUG ATTENDUE**

### **📋 Stratégie de debugging systématique**
```python
# Pattern attendu pour debugging avancé:
import logging
import traceback
from functools import wraps

# 1. Logging exhaustif
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 2. Décorateur de debugging
def debug_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info(f"=== START {func.__name__} ===")
        try:
            result = await func(*args, **kwargs)
            logger.info(f"=== SUCCESS {func.__name__} ===")
            return result
        except Exception as e:
            logger.error(f"=== ERROR {func.__name__} ===")
            logger.error(f"Exception: {type(e).__name__}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Args: {args}")
            logger.error(f"Kwargs: {kwargs}")
            raise
    return wrapper

# 3. Validation Pydantic détaillée
try:
    request_data = GenerationRequest(**payload)
    logger.info(f"Pydantic validation OK: {request_data}")
except ValidationError as e:
    logger.error(f"Pydantic validation failed: {e}")
    raise

# 4. Tests isolés pour chaque composant
# 5. Monitoring mémoire et performance
# 6. Timeout handling explicite
```

---

## 🎯 **QUESTIONS SPÉCIFIQUES POUR L'IA EXPERT**

### **📋 Questions techniques**
1. **Erreur silencieuse**: Comment capturer une erreur 500 qui n'apparaît pas dans les logs?

2. **Debugging FastAPI**: Quelle est la meilleure approche pour debugger les erreurs silencieuses dans FastAPI?

3. **Logging avancé**: Comment configurer un logging qui capture absolument toutes les erreurs?

4. **Validation Pydantic**: Comment diagnostiquer les erreurs de validation silencieuses?

5. **Async debugging**: Comment debugger les erreurs dans les coroutines asyncio?

6. **Memory leaks**: Comment détecter les problèmes de mémoire qui causent des crashes silencieux?

7. **Timeout handling**: Comment implémenter un timeout robuste qui ne cause pas d'erreurs silencieuses?

8. **External dependencies**: Comment tester si les modèles externes répondent correctement?

---

## 🏆 **RÉSULTAT ATTENDU**

### **📋 Code de debugging complet**
```python
# Solution attendue:
# 1. Configuration logging exhaustive
# 2. Décorateurs de debugging pour tous les endpoints
# 3. Validation Pydantic avec logging détaillé
# 4. Tests isolés pour chaque modèle
# 5. Monitoring mémoire et performance
# 6. Timeout handling explicite
# 7. Error boundaries avec stack traces complètes
# 8. Health checks détaillés pour chaque composant
```

### **📋 Stratégie de debugging**
```python
# Approche systématique:
# 1. Isoler le problème (endpoint vs models vs config)
# 2. Tester chaque composant individuellement
# 3. Ajouter du logging progressif
# 4. Utiliser des breakpoints virtuels
# 5. Monitorer les ressources système
# 6. Tester avec payloads différents
# 7. Vérifier les dépendances externes
```

---

## 🎯 **OBJECTIF FINAL**

**Identifier et corriger la cause de l'erreur 500 silencieuse pour permettre le fonctionnement normal des endpoints /generate et garantir le succès à LM Arena.**

---

**🌊 Ce prompt est conçu pour obtenir une solution de debugging expert niveau production pour résoudre l'erreur 500 silencieuse.**
