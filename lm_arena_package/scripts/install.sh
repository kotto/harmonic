#!/bin/bash
# ==============================================
#  Installation du Package LM Arena - Linux/macOS
#  Harmonic AI - L'IA Community-Proof
# ==============================================

set -e  # Arrêter en cas d'erreur

echo "=============================================="
echo "  Installation du Package LM Arena"
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

# Fonction pour afficher les avertissements
show_warning() {
    echo "[!] $1" >&2
}

# ==============================================
# ÉTAPE 1 : Vérification des prérequis
# ==============================================

show_info "Étape 1 : Vérification des prérequis"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    show_error "Python3 n'est pas installé"
fi

python_version=$(python3 --version 2>&1)
show_success "Python trouvé : $python_version"

# Vérifier pip
if ! command -v pip3 &> /dev/null; then
    show_warning "pip3 n'est pas installé, tentative d'installation..."
    
    # Essayer d'installer pip selon l'OS
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y python3-pip
    elif command -v brew &> /dev/null; then
        # macOS avec Homebrew
        brew install python3
    else
        show_error "Impossible d'installer pip automatiquement"
    fi
fi

pip_version=$(pip3 --version 2>&1 | cut -d' ' -f2)
show_success "pip trouvé : $pip_version"

# Vérifier Git
if ! command -v git &> /dev/null; then
    show_warning "Git n'est pas installé (recommandé pour les mises à jour)"
else
    git_version=$(git --version 2>&1 | cut -d' ' -f3)
    show_success "Git trouvé : $git_version"
fi

# ==============================================
# ÉTAPE 2 : Création de l'environnement virtuel
# ==============================================

show_info "Étape 2 : Création de l'environnement virtuel"

venv_path="./venv"
if [ -d "$venv_path" ]; then
    show_info "Environnement virtuel existant détecté, suppression..."
    rm -rf "$venv_path"
fi

# Créer l'environnement virtuel
python3 -m venv "$venv_path"
if [ $? -ne 0 ]; then
    show_error "Échec de la création de l'environnement virtuel"
fi
show_success "Environnement virtuel créé : $venv_path"

# ==============================================
# ÉTAPE 3 : Activation et installation des dépendances
# ==============================================

show_info "Étape 3 : Activation et installation des dépendances"

# Activer l'environnement virtuel
source "$venv_path/bin/activate"

# Mettre à jour pip
show_info "Mise à jour de pip..."
pip install --upgrade pip
if [ $? -ne 0 ]; then
    show_error "Échec de la mise à jour de pip"
fi
show_success "pip mis à jour avec succès"

# Installer les dépendances
show_info "Installation des dépendances depuis requirements.txt..."
if [ -f "../config/requirements.txt" ]; then
    pip install -r "../config/requirements.txt"
elif [ -f "requirements.txt" ]; then
    pip install -r "requirements.txt"
else
    show_error "Fichier requirements.txt introuvable"
fi

if [ $? -ne 0 ]; then
    show_error "Échec de l'installation des dépendances"
fi
show_success "Dépendances installées avec succès"

# ==============================================
# ÉTAPE 4 : Configuration de l'environnement
# ==============================================

show_info "Étape 4 : Configuration de l'environnement"

# Créer le fichier .env à partir de l'exemple
env_example="../config/.env.example"
env_file="../config/.env"

if [ -f "$env_example" ]; then
    if [ ! -f "$env_file" ]; then
        cp "$env_example" "$env_file"
        show_success "Fichier .env créé à partir de l'exemple"
        
        # Demander à l'utilisateur de configurer les clés API
        echo ""
        echo "⚠️  IMPORTANT : Configurez vos clés API dans le fichier :"
        echo "   $(realpath "$env_file")"
        echo ""
        echo "Variables à configurer :"
        echo "  - API_KEY : Votre clé API pour l'authentification"
        echo "  - DEEPSEEK_API_KEY : Clé pour l'API DeepSeek (optionnel)"
        echo "  - AWS_ACCESS_KEY_ID : Identifiant AWS (pour déploiement)"
        echo "  - AWS_SECRET_ACCESS_KEY : Clé secrète AWS"
        echo ""
    else
        show_info "Fichier .env existe déjà, conservation"
    fi
else
    show_warning "Fichier .env.example introuvable, création manuelle nécessaire"
fi

# ==============================================
# ÉTAPE 5 : Initialisation de la base de données
# ==============================================

show_info "Étape 5 : Initialisation de la base de données"

# Vérifier si Docker est disponible pour la base de données
docker_available=false
if command -v docker &> /dev/null; then
    docker_version=$(docker --version 2>&1 | cut -d' ' -f3 | tr -d ',')
    show_success "Docker trouvé : $docker_version"
    docker_available=true
else
    show_warning "Docker non disponible, base de données locale recommandée"
fi

if [ "$docker_available" = true ]; then
    show_info "Démarrage des services avec Docker Compose..."
    
    docker_compose_file="../config/docker-compose.yml"
    if [ -f "$docker_compose_file" ]; then
        # Démarrer les services en arrière-plan
        docker-compose -f "$docker_compose_file" up -d
        if [ $? -ne 0 ]; then
            show_warning "Échec du démarrage Docker Compose, vérification manuelle nécessaire"
        else
            show_success "Services Docker démarrés avec succès"
            
            # Attendre que les services soient prêts
            show_info "Attente de la disponibilité des services..."
            sleep 10
        fi
    else
        show_warning "Fichier docker-compose.yml introuvable"
    fi
fi

# ==============================================
# ÉTAPE 6 : Vérification de l'installation
# ==============================================

show_info "Étape 6 : Vérification de l'installation"

# Vérifier les imports Python
show_info "Vérification des imports Python..."
cat > test_imports.py << 'EOF'
import sys
sys.path.insert(0, '../backend')

try:
    import fastapi
    import uvicorn
    import pydantic
    import sqlalchemy
    import redis
    import celery
    print("SUCCESS: Toutes les dépendances sont importables")
except ImportError as e:
    print(f"ERROR: Import échoué: {e}")
    sys.exit(1)
EOF

python3 test_imports.py
if [ $? -ne 0 ]; then
    show_error "Échec des imports Python"
fi
rm -f test_imports.py
show_success "Toutes les dépendances Python sont importables"

# ==============================================
# ÉTAPE 7 : Finalisation
# ==============================================

show_info "Étape 7 : Finalisation"

echo ""
echo "✅ INSTALLATION TERMINÉE AVEC SUCCÈS !"
echo ""

echo "📋 RÉSUMÉ DE L'INSTALLATION :"
echo "  • Python : $(echo $python_version | cut -d' ' -f2)"
echo "  • Environnement virtuel : $venv_path"
echo "  • Dépendances : Installées avec succès"
if [ "$docker_available" = true ]; then
    echo "  • Services Docker : Démarrés"
fi
echo ""

echo "🚀 POUR DÉMARRER LES SERVICES :"
echo "  1. Exécutez : ./scripts/start.sh"
echo "  2. Ou exécutez : ./scripts/start_all.sh"
echo ""

echo "🌐 ACCÈS AUX SERVICES :"
echo "  • API Backend : http://localhost:8000"
echo "  • Documentation API : http://localhost:8000/docs"
echo "  • Frontend : http://localhost:8080"
echo "  • Monitoring : http://localhost:9090"
echo ""

echo "🔧 CONFIGURATION MANUELLE :"
echo "  • Modifiez le fichier .env pour configurer vos clés API"
echo "  • Consultez docs/guides/ pour la documentation complète"
echo ""

echo "📞 SUPPORT :"
echo "  • Documentation : docs/guides/"
echo "  • Tests : ./scripts/final_check.sh"
echo "  • Problèmes : Consultez docs/guides/checklist.md"
echo ""

echo "=============================================="
echo "  Harmonic AI - L'IA Community-Proof"
echo "  Prêt pour LM Arena ! 🏆"
echo "=============================================="

# Désactiver l'environnement virtuel
deactivate