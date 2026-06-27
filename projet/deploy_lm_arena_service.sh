#!/bin/bash
# 🚀 DÉPLOIEMENT SERVICE LM ARENA COMPLET

echo "🚀 DÉPLOIEMENT SERVICE LM ARENA HARMONIC-MISTRAL"
echo "=================================================="

# Arrêt du service existant
echo "🛑 Arrêt du service existant..."
pkill -f "python.*final_real_fusion" || true
pkill -f "uvicorn" || true

# Téléchargement des fichiers
echo "📥 Téléchargement des fichiers..."
aws s3 cp s3://deepseek-models-326095712935/final/final_real_fusion.py ./
aws s3 cp s3://deepseek-models-326095712935/submission/lm_arena_submission_prep.py ./
aws s3 cp s3://deepseek-models-326095712935/submission/lm_arena_benchmarks.py ./

# Installation dépendances API
echo "📦 Installation dépendances API..."
pip install fastapi uvicorn requests pydantic

# Test du service API
echo "🧪 Test du service API..."
timeout 10 python3 lm_arena_submission_prep.py &
API_PID=$!

sleep 5

# Test de santé
echo "🏥 Test de santé..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Health check failed"

# Test de génération
echo "🔥 Test de génération..."
curl -s -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is the capital of France?"}' | python3 -m json.tool || echo "❌ Generation test failed"

# Arrêt du test
echo "🛑 Arrêt du test..."
kill $API_PID 2>/dev/null || true

# Démarrage du service en production
echo "🚀 Démarrage du service en production..."
nohup python3 lm_arena_submission_prep.py > /tmp/lm_arena_service.log 2>&1 &
SERVICE_PID=$!

echo "✅ Service démarré avec PID: $SERVICE_PID"
echo "📊 Logs: /tmp/lm_arena_service.log"
echo "🌐 API: http://localhost:8000"
echo "📚 Documentation: http://localhost:8000/docs"
echo "🏥 Health: http://localhost:8000/health"

# Attente de démarrage
echo "⏳ Attente de démarrage (10s)..."
sleep 10

# Test final
echo "🧪 Test final de santé..."
HEALTH_CHECK=$(curl -s http://localhost:8000/health)
if [[ $HEALTH_CHECK == *"healthy"* ]]; then
    echo "✅ Service LM Arena prêt!"
    echo "📊 Endpoints disponibles:"
    echo "   - GET /health"
    echo "   - GET /metrics"
    echo "   - POST /generate"
    echo "   - GET /docs"
    echo "   - GET /info"
else
    echo "❌ Erreur de démarrage"
    echo "📋 Logs:"
    tail -20 /tmp/lm_arena_service.log
fi

echo "🎯 Service LM Arena déployé!"
echo "📊 Prochaines étapes:"
echo "   1. Exécuter les benchmarks: python3 lm_arena_benchmarks.py"
echo "   2. Vérifier les scores"
echo "   3. Soumettre à LM Arena"
