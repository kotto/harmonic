#!/bin/bash
# Script pour démarrer Connective AI sur EC2

echo "🚀 Démarrage de Connective AI..."
echo "📁 Vérification des fichiers..."

# Vérifier quel fichier FastAPI est le bon
if grep -q "app = FastAPI" /opt/connective-ai/PARALLEL_MULTI_MODAL_AGGREGATION.py; then
    APP_FILE="PARALLEL_MULTI_MODAL_AGGREGATION"
    echo "✅ Utilisation de PARALLEL_MULTI_MODAL_AGGREGATION.py"
elif grep -q "app = FastAPI" /opt/connective-ai/DEEPSEEK_S3_LOCAL_INTEGRATION.py; then
    APP_FILE="DEEPSEEK_S3_LOCAL_INTEGRATION"
    echo "✅ Utilisation de DEEPSEEK_S3_LOCAL_INTEGRATION.py"
else
    echo "❌ Aucun fichier FastAPI valide trouvé"
    exit 1
fi

# Arrêter les processus existants
echo "🛑 Arrêt des processus existants..."
pkill -f uvicorn 2>/dev/null || true
sleep 2

# Démarrer le service
echo "▶️  Démarrage du service..."
cd /opt/connective-ai
source venv/bin/activate

# Démarrer en arrière-plan
nohup uvicorn ${APP_FILE}:app --host 0.0.0.0 --port 8000 > /var/log/connective-ai.log 2>&1 &
UVICORN_PID=$!

echo "✅ Processus démarré avec PID: $UVICORN_PID"
echo "⏳ Attente du démarrage..."
sleep 5

# Vérifier si le service fonctionne
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "🎉 Service démarré avec succès!"
    echo "📊 Logs: /var/log/connective-ai.log"
    echo "🌐 URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
    echo "🔧 Health: http://localhost:8000/api/health"
    echo "⚡ Generate: http://localhost:8000/api/generate"
else
    echo "⚠️  Service démarré mais non accessible"
    echo "📋 Vérification des logs..."
    tail -20 /var/log/connective-ai.log
fi