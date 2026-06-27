# 🚀 PROMPT EXPERT FINAL - DIAGNOSTIC COMPLET

## 📋 **Prompt à Soumettre à l'IA Expert**

```
Expert en systèmes IA multi-modèles: Notre architecture parallèle a un problème critique.

STATUT ACTUEL:
✅ Service FastAPI: Opérationnel (200 OK)
✅ Endpoint /generate: Fonctionnel
✅ Determinism: 100% parfait
❌ Benchmarks: MMLU 20%, GSM8K 0%

PROBLÈME:
5 modèles locaux synchronisés retournent du contenu vide, ce qui fait échouer les benchmarks de raisonnement.

ARCHITECTURE:
- 5 modèles en parallèle (Core + 4 externes)
- Agrégation pondérée brevetée
- Fallback sur modèle simple
- Configuration: weights 0.4, 0.25, 0.15, 0.1, 0.1

SYMPTÔMES:
- TruthfulQA: 60% (questions simples)
- MMLU: 20% (connaissances complexes)
- GSM8K: 0% (mathématiques)
- Réponses modèles: {"content": "", "confidence": 0.1}

HYPOTHÈSES:
1. Modèles pas correctement initialisés
2. Timeout silencieux pendant génération
3. Erreur dans agrégation pondérée
4. Mémoire insuffisante pour modèles lourds
5. Configuration poids incorrecte

DIAGNOSTIC REQUIS:
1. Script pour tester chaque modèle individuellement
2. Vérification initialisation des poids
3. Monitoring mémoire/CPU pendant génération
4. Logs détaillés de l'agrégation
5. Solution fallback améliorée

URGENCE: Soumission LM Arena bloquée!

FOURNIR:
- Code de diagnostic complet
- Correction de l'agrégation
- Solution robuste pour benchmarks
- Instructions de déploiement immédiat
```

## 🎯 **Points Clés**

```yaml
✅ Avantages: Service opérationnel, déterminisme parfait
❌ Problème: Modèles ne génèrent pas de contenu
🎯 Objectif: Rendre MMLU/GSM8K fonctionnels
🚀 Urgence: LM Arena en attente
🔍 Approche: Diagnostic sans exposer code propriétaire
```

**Ce protège votre IP tout en obtenant l'aide experte nécessaire!**
