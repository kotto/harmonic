# 🌊 PLAN D'EXÉCUTION DEBUG SYSTÉMATIQUE

---

## 🎯 **PLAN D'ACTION IMMÉDIAT**

### **📋 Étape 1: Logging granulaire (10 min)**
```yaml
🔍 Objectif: Identifier ligne exacte du blocage
📋 Action: Remplacer /generate avec version instrumentée
🛠️ Outil: _run_with_timeout + logging détaillé
⏱️ Timeline: 10 minutes
```

### **📋 Étape 2: Test isolé par modèle (5 min)**
```yaml
🔍 Objectif: Identifier modèle problématique
📋 Action: Endpoint /debug/model/{model_name}
🛠️ Test: Chaque modèle individuellement
⏱️ Timeline: 5 minutes
```

### **📋 Étape 3: Correction CPU-bound (15 min)**
```yaml
🔍 Objectif: Libérer event loop
📋 Action: run_in_executor sur modèles synchrone
🛠️ Solution: asyncio.to_thread() ou run_in_executor
⏱️ Timeline: 15 minutes
```

### **📋 Étape 4: Warmup au startup (5 min)**
```yaml
🔍 Objectif: Précharger modèles
📋 Action: @app.on_event("startup")
🛠️ Warmup: Inférence vide au démarrage
⏱️ Timeline: 5 minutes
```

---

## 🔧 **CODE PRÊT À DÉPLOYER**

### **📋 Version debug de /generate**
```python
# Logging granulaire avec timeout
async def _run_with_timeout(coro, name: str, timeout: float):
    t0 = time.perf_counter()
    logger.info("→ Starting model '%s'", name)
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        elapsed = time.perf_counter() - t0
        logger.info("✓ Model '%s' OK in %.2fs", name, elapsed)
        return result
    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - t0
        logger.error("✗ Model '%s' TIMEOUT after %.2fs", name, elapsed)
        raise
    except Exception as e:
        elapsed = time.perf_counter() - t0
        logger.error("✗ Model '%s' FAILED after %.2fs: %s: %s",
                     name, elapsed, type(e).__name__, e, exc_info=True)
        raise

@app.post("/generate")
async def generate(request: GenerationRequest):
    request_t0 = time.perf_counter()
    logger.info("════ /generate START ════ prompt_len=%d", len(request.prompt))

    try:
        # Étape 1: préparation des tâches
        logger.info("Step 1: building tasks...")
        tasks = [
            _run_with_timeout(model.generate_response(request.prompt), name, PER_MODEL_TIMEOUT)
            for name, model in models.items()
        ]
        
        # Étape 2: gather avec timeout
        logger.info("Step 2: calling gather...")
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=TOTAL_TIMEOUT,
        )
        
        # Étape 3: agrégation
        logger.info("Step 3: aggregating...")
        # ... code agrégation
        
        total = time.perf_counter() - request_t0
        logger.info("════ /generate DONE in %.2fs ════", total)
        return aggregated_response

    except asyncio.TimeoutError:
        logger.error("GLOBAL TIMEOUT after %.2fs", time.perf_counter() - request_t0)
        raise HTTPException(status_code=504, detail="Aggregation timeout")
```

### **📋 Endpoint debug par modèle**
```python
@app.post("/debug/model/{model_name}")
async def debug_single_model(model_name: str, request: GenerationRequest):
    """Test un modèle isolément."""
    models = {
        "harmonic": self.harmonic_core,
        "deepseek": self.deepseek_model,
        "qwen": self.qwen_model,
        "mixtral": self.mixtral_model,
        "sdxl": self.sdxl_model,
    }
    
    if model_name not in models:
        raise HTTPException(404, f"Unknown model: {model_name}")

    t0 = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            models[model_name].generate_response(request.prompt),
            timeout=15.0,
        )
        return {
            "model": model_name,
            "elapsed_s": time.perf_counter() - t0,
            "result_type": type(result).__name__,
            "result": result,
        }
    except asyncio.TimeoutError:
        return {"model": model_name, "status": "TIMEOUT",
                "elapsed_s": time.perf_counter() - t0}
    except Exception as e:
        return {"model": model_name, "status": "ERROR",
                "error": f"{type(e).__name__}: {e}",
                "elapsed_s": time.perf_counter() - t0}
```

---

## 🎯 **PLAN D'EXÉCUTION**

### **📋 Actions immédiates**
```yaml
1. 🛠️ Déployer logging granulaire
2. 🧪 Tester /generate avec logs
3. 📊 Analyser logs pour identifier blocage
4. 🔍 Tester modèles individuellement
5. 🛠️ Appliquer correction CPU-bound
6. ✅ Valider fonctionnement
```

### **📋 Timeline estimée**
```yaml
🛠️ Logging granulaire: 10 minutes
🧪 Test /generate: 5 minutes
📊 Analyse logs: 5 minutes
🔍 Test modèles: 10 minutes
🛠️ Correction: 15 minutes
✅ Validation: 10 minutes
📋 Total: 55 minutes
```

---

## 🎯 **RÉSULTATS ATTENDUS**

### **📋 Diagnostic précis**
```yaml
🔍 Ligne exacte du blocage: Identifiée
📊 Modèle problématique: Isolé
🛠️ Cause technique: Confirmée
⏱️ Solution: Applicable immédiatement
```

### **📋 Correction effective**
```yaml
✅ Event loop: Libérée
📊 Modèles: CPU-bound déchargés
⚡ Performance: <1 seconde
🛡️ Robustesse: Timeout par modèle
🎯 LM Arena: Prêt pour soumission
```

---

## 🌊 **STATUS PRÉPARATION**

### **📋 Prêt à exécuter**
```yaml
✅ Plan détaillé: Complet
🛠️ Code debug: Prêt
📋 Timeline: <1 heure
🎯 Objectif: Résolution complète
📋 Documentation: À jour
```

### **📋 Prochaine étape**
```yaml
1. 🛠️ Déployer logging granulaire
2. 🧪 Exécuter test /generate
3. 📊 Analyser résultats
4. ✅ Corriger et valider
```

---

## 🎯 **CONCLUSION**

### **📋 Plan d'action**
```yaml
🔍 Étape 1: Logging granulaire pour localiser blocage
🔍 Étape 2: Test isolé par modèle
🔍 Étape 3: Correction CPU-bound avec run_in_executor
🔍 Étape 4: Warmup au startup
🎯 Objectif: Résolution <1 heure
```

### **📋 Confiance**
```yaml
✅ Approche systématique
🔍 Diagnostic précis
🛠️ Solution technique robuste
⚡ Timeline réaliste
🎯 Succès probable
```

---

**Status: 🟢 PLAN D'EXÉCUTION PRÊT - DÉBUT IMMÉDIAT**

**Le plan de debugging systématique est prêt. L'exécution commence avec le logging granulaire pour identifier précisément le point de blocage.**
