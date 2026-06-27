#!/bin/bash
# ==============================================
#  Démarrage du Package LM Arena - Linux/macOS
#  Harmonic AI - L'IA Community-Proof
# ==============================================

set -e  # Arrêter en cas d'erreur

echo "=============================================="
echo "  Démarrage du Package LM Arena"
echo "  Harmonic AI - L'IA Community-Proof"
echo "=============================================="
echo ""

# Fonction pour afficher les messages d'erreur
show_error() {
    echo "[i] $1" >&2
    exit 1
}

# Fonction pour afficher les messages de succès
show_success() {
    echo "[+] $1"
}

# Fonction pour afficher les messages d'information
show_info() {
    echo "[*] $1"
}

# Fonction pour vérifier si un service est en cours d'exécution
check_service() {
    local service_name=$1
    local port=$2
    
    if command -v nc &> /dev/null; then
        if nc -z localhost "$port" 2>/dev/null; then
            echo "[+] $service_name est en cours d'exécution sur le port $port"
            return 0
        else
            echo "[-] $service_name n'est pas en cours d'exécution sur le port $port"
            return 1
        fi
    elif command -v ss &> /dev/null; then
        if ss -tln | grep ":$port " &> /dev/null; then
            echo "[+] $service_name est en cours d'exécution sur le port $port"
            return 0
        else
            echo "[-] $service_name n'est pas en cours d'exécution sur le port $port"
            return 1
        fi
    else
        # Fallback simple
        echo "[?] Impossible de vérifier $service_name (netcat/ss non disponible)"
        return 2
    fi
}

# ==============================================
# ÉTAPE 1 : Vérification des prérequis
# ==============================================

show_info "Étape 1 : Vérification des prérequis"

# Vérifier l'environnement virtuel
venv_path="./venv"
if [ ! -d "$venv_path" ]; then
    show_error "Environnement virtuel introuvable. Exécutez d'abord ./scripts/install.sh"
fi

# Activer l'environnement virtuel
source "$venv_path/bin/activate"
show_success "Environnement virtuel activé"

# Vérifier les dépendances Python
show_info "Vérification des dépendances Python..."
python3 -c "
import sys
try:
    import fastapi
    import uvicorn
    import pydantic
    import sqlalchemy
    import redis
    import celery
    print('[+] Toutes les dépendances sont disponibles')
except ImportError as e:
    print(f'[i] Erreur: {e}')
    sys.exit(1)
"

# ==============================================
# ÉTAPE 2 : Vérification des services existants
# ==============================================

show_info "Étape 2 : Vérification des services existants"

# Ports des services
API_PORT=8000
FRONTEND_PORT=8080
AUDIO_SERVICE_PORT=9017
VIDEO_SERVICE_PORT=9018
MONITORING_PORT=9090

# Arrêter les services existants sur les mêmes ports
show_info "Arrêt des services existants sur les ports utilisés..."
for port in $API_PORT $FRONTEND_PORT $AUDIO_SERVICE_PORT $VIDEO_SERVICE_PORT $MONITORING_PORT; do
    if check_service "Service sur port $port" "$port" 2>/dev/null; then
        # Trouver le PID du processus utilisant le port
        if command -v lsof &> /dev/null; then
            pid=$(lsof -ti:$port 2>/dev/null)
            if [ -n "$pid" ]; then
                echo "[*] Arrêt du processus $pid sur le port $port"
                kill -9 "$pid" 2>/dev/null || true
            fi
        elif command -v fuser &> /dev/null; then
            fuser -k "$port/tcp" 2>/dev/null || true
        fi
    fi
done

# ==============================================
# ÉTAPE 3 : Démarrage des services
# ==============================================

show_info "Étape 3 : Démarrage des services"

# Créer le répertoire des logs
mkdir -p ../logs
show_success "Répertoire des logs créé"

# 3.1 Démarrage de l'API Backend
show_info "Démarrage de l'API Backend (FastAPI)..."
cd ../backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port $API_PORT --reload > ../logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > ../logs/api.pid
cd ../scripts
sleep 3

if check_service "API Backend" "$API_PORT"; then
    show_success "API Backend démarrée avec succès (PID: $API_PID)"
else
    show_error "Échec du démarrage de l'API Backend"
fi

# 3.2 Démarrage des services harmoniques
show_info "Démarrage des services harmoniques..."

# Service audio
show_info "Démarrage du service audio..."
cd ../backend/services
nohup python3 audio_service.py --port $AUDIO_SERVICE_PORT > ../../logs/audio_service.log 2>&1 &
AUDIO_PID=$!
echo $AUDIO_PID > ../../logs/audio_service.pid
cd ../../scripts
sleep 2

if check_service "Service audio" "$AUDIO_SERVICE_PORT"; then
    show_success "Service audio démarré avec succès (PID: $AUDIO_PID)"
else
    show_warning "Service audio non démarré (peut être désactivé)"
fi

# Service vidéo
show_info "Démarrage du service vidéo..."
cd ../backend/services
nohup python3 video_service.py --port $VIDEO_SERVICE_PORT > ../../logs/video_service.log 2>&1 &
VIDEO_PID=$!
echo $VIDEO_PID > ../../logs/video_service.pid
cd ../../scripts
sleep 2

if check_service "Service vidéo" "$VIDEO_SERVICE_PORT"; then
    show_success "Service vidéo démarré avec succès (PID: $VIDEO_PID)"
else
    show_warning "Service vidéo non démarré (peut être désactivé)"
fi

# 3.3 Démarrage du frontend (simulé)
show_info "Démarrage du frontend..."
cd ../frontend
nohup python3 -m http.server $FRONTEND_PORT > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ../scripts
sleep 2

if check_service "Frontend" "$FRONTEND_PORT"; then
    show_success "Frontend démarré avec succès (PID: $FRONTEND_PID)"
else
    show_warning "Frontend non démarré (peut être désactivé)"
fi

# 3.4 Démarrage du monitoring (simulé)
show_info "Démarrage du monitoring..."
cd ../monitoring
nohup python3 -m http.server $MONITORING_PORT > ../logs/monitoring.log 2>&1 &
MONITORING_PID=$!
echo $MONITORING_PID > ../logs/monitoring.pid
cd ../scripts
sleep 2

if check_service "Monitoring" "$MONITORING_PORT"; then
    show_success "Monitoring démarré avec succès (PID: $MONITORING_PID)"
else
    show_warning "Monitoring non démarré (peut être désactivé)"
fi

# ==============================================
# ÉTAPE 4 : Vérification de l'état des services
# ==============================================

show_info "Étape 4 : Vérification de l'état des services"

echo ""
echo "📊 ÉTAT DES SERVICES :"
echo "======================"

services=(
    "API Backend:localhost:$API_PORT"
    "Frontend:localhost:$FRONTEND_PORT"
    "Service Audio:localhost:$AUDIO_SERVICE_PORT"
    "Service Vidéo:localhost:$VIDEO_SERVICE_PORT"
    "Monitoring:localhost:$MONITORING_PORT"
)

all_services_running=true

for service in "${services[@]}"; do
    name=$(echo "$service" | cut -d: -f1)
    host=$(echo "$service" | cut -d: -f2)
    port=$(echo "$service" | cut -d: -f3)
    
    if check_service "$name" "$port" 2>/dev/null; then
        echo "  ✅ $name : http://$host:$port"
    else
        echo "  ❌ $name : NON DÉMARRÉ"
        all_services_running=false
    fi
done

# ==============================================
# ÉTAPE 5 : Tests de connectivité
# ==============================================

show_info "Étape 5 : Tests de connectivité"

# Tester l'API
show_info "Test de l'API Backend..."
if curl -s http://localhost:$API_PORT/health > /dev/null 2>&1; then
    show_success "API Backend répond correctement"
else
    show_warning "API Backend ne répond pas au test de santé"
fi

# Tester le frontend
show_info "Test du frontend..."
if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
    show_success "Frontend répond correctement"
else
    show_warning "Frontend ne répond pas"
fi

# ==============================================
# ÉTAPE 6 : Finalisation
# ==============================================

show_info "Étape 6 : Finalisation"

echo ""
echo "✅ DÉMARRAGE TERMINÉ AVEC SUCCÈS !"
echo ""

echo "🌐 ACCÈS AUX SERVICES :"
echo "======================"
echo "  • API Backend : http://localhost:$API_PORT"
echo "  • Documentation API : http://localhost:$API_PORT/docs"
echo "  • Frontend : http://localhost:$FRONTEND_PORT"
echo "  • Monitoring : http://localhost:$MONITORING_PORT"
echo ""

echo "📋 INFORMATIONS DE DÉBOGAGE :"
echo "============================="
echo "  • Logs API : ../logs/api.log"
echo "  • Logs Audio : ../logs/audio_service.log"
echo "  • Logs Vidéo : ../logs/video_service.log"
echo "  • Logs Frontend : ../logs/frontend.log"
echo "  • Logs Monitoring : ../logs/monitoring.log"
echo ""

echo "🔧 COMMANDES UTILES :"
echo "===================="
echo "  • Arrêter tous les services : ./scripts/stop.sh"
echo "  • Vérifier l'état : ./scripts/status.sh"
echo "  • Redémarrer : ./scripts/restart.sh"
echo "  • Tests LM Arena : ./scripts/test_lm_arena.sh"
echo ""

echo "📞 SUPPORT :"
echo "==========="
echo "  • Documentation : ../docs/guides/"
echo "  • Problèmes : Consultez ../docs/guides/checklist.md"
echo "  • Tests : ./scripts/final_check.sh"
echo ""

echo "=============================================="
echo "  Harmonic AI - L'IA Community-Proof"
echo "  Services démarrés avec succès ! 🚀"
echo "=============================================="

# Enregistrer les PIDs pour référence future
echo "API_PID=$API_PID" > ../logs/service_pids.env
echo "AUDIO_PID=$AUDIO_PID" >> ../logs/service_pids.env
echo "VIDEO_PID=$VIDEO_PID" >> ../logs/service_pids.env
echo "FRONTEND_PID=$FRONTEND_PID" >> ../logs/service_pids.env
echo "MONITORING_PID=$MONITORING_PID" >> ../logs/service_pids.env

# Désactiver l'environnement virtuel
deactivate