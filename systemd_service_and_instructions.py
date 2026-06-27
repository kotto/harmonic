#!/usr/bin/env python3
"""
Service systemd et instructions détaillées pour DeepSeek API sur EC2
"""

def generate_systemd_service():
    """Génère le fichier de service systemd"""
    
    service_content = """[Unit]
Description=DeepSeek Harmonic V2 Real API
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=ubuntu
WorkingDirectory=/opt/deepseek
Environment="PATH=/opt/deepseek/venv/bin"
ExecStart=/opt/deepseek/venv/bin/python /opt/deepseek/api.py

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=deepseek-api

[Install]
WantedBy=multi-user.target
"""
    
    return service_content

def generate_quick_deploy_script():
    """Génère un script de déploiement rapide"""
    
    script = """#!/bin/bash
# Script de déploiement rapide pour DeepSeek API sur EC2
# À exécuter sur l'instance EC2

echo "=== DEPLOIEMENT DEEPSEEK HARMONIC V2 ==="

# 1. Mise à jour système
echo "1. Mise à jour du système..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. Installation Python
echo "2. Installation de Python..."
sudo apt-get install -y python3 python3-pip python3-venv

# 3. Création du répertoire
echo "3. Création du répertoire /opt/deepseek..."
sudo mkdir -p /opt/deepseek
sudo chown -R ubuntu:ubuntu /opt/deepseek
cd /opt/deepseek

# 4. Environnement virtuel
echo "4. Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# 5. Installation dépendances
echo "5. Installation des dépendances..."
pip install --upgrade pip
pip install fastapi uvicorn pydantic

# 6. Copie de l'API
echo "6. Copie du fichier API..."
# Le fichier api.py doit être créé manuellement ou copié via SCP

# 7. Service systemd
echo "7. Configuration du service systemd..."
sudo tee /etc/systemd/system/deepseek-api.service > /dev/null << 'EOF'
[Unit]
Description=DeepSeek Harmonic V2 Real API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/deepseek
Environment="PATH=/opt/deepseek/venv/bin"
ExecStart=/opt/deepseek/venv/bin/python /opt/deepseek/api.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 8. Activation du service
echo "8. Activation du service..."
sudo systemctl daemon-reload
sudo systemctl enable deepseek-api
sudo systemctl start deepseek-api

# 9. Vérification
echo "9. Vérification..."
sleep 2
sudo systemctl status deepseek-api --no-pager

echo "=== DEPLOIEMENT TERMINE ==="
echo "Testez l'API avec: curl http://localhost:8000/health"
"""
    
    return script

def generate_step_by_step_instructions():
    """Génère des instructions étape par étape"""
    
    steps = []
    
    steps.append("=" * 70)
    steps.append("INSTRUCTIONS ETAPE PAR ETAPE POUR DEPLOIEMENT EC2")
    steps.append("=" * 70)
    steps.append("")
    steps.append("ETAPE 1: Se connecter à l'instance EC2")
    steps.append("   - Utiliser EC2 Instance Connect")
    steps.append("   - Adresse: 172.31.45.211 (actuelle)")
    steps.append("   - Utilisateur: ubuntu")
    steps.append("")
    steps.append("ETAPE 2: Préparer le système")
    steps.append("   Commande: sudo apt-get update && sudo apt-get upgrade -y")
    steps.append("")
    steps.append("ETAPE 3: Installer Python")
    steps.append("   Commande: sudo apt-get install -y python3 python3-pip python3-venv")
    steps.append("")
    steps.append("ETAPE 4: Créer le répertoire")
    steps.append("   Commandes:")
    steps.append("   sudo mkdir -p /opt/deepseek")
    steps.append("   sudo chown -R ubuntu:ubuntu /opt/deepseek")
    steps.append("   cd /opt/deepseek")
    steps.append("")
    steps.append("ETAPE 5: Créer l'environnement virtuel")
    steps.append("   Commandes:")
    steps.append("   python3 -m venv venv")
    steps.append("   source venv/bin/activate")
    steps.append("")
    steps.append("ETAPE 6: Installer les dépendances")
    steps.append("   Commandes:")
    steps.append("   pip install --upgrade pip")
    steps.append("   pip install fastapi uvicorn pydantic")
    steps.append("")
    steps.append("ETAPE 7: Créer le fichier API")
    steps.append("   Commande: nano api.py")
    steps.append("   Copier le contenu de deepseek_api_real_final.py")
    steps.append("   Ou utiliser: cat > api.py << 'EOF' ... EOF")
    steps.append("")
    steps.append("ETAPE 8: Créer le service systemd")
    steps.append("   Commande: sudo nano /etc/systemd/system/deepseek-api.service")
    steps.append("   Copier ce contenu:")
    steps.append("")
    steps.append("   [Unit]")
    steps.append("   Description=DeepSeek Harmonic V2 Real API")
    steps.append("   After=network.target")
    steps.append("")
    steps.append("   [Service]")
    steps.append("   Type=simple")
    steps.append("   User=ubuntu")
    steps.append("   WorkingDirectory=/opt/deepseek")
    steps.append("   Environment=\"PATH=/opt/deepseek/venv/bin\"")
    steps.append("   ExecStart=/opt/deepseek/venv/bin/python /opt/deepseek/api.py")
    steps.append("   Restart=always")
    steps.append("")
    steps.append("   [Install]")
    steps.append("   WantedBy=multi-user.target")
    steps.append("")
    steps.append("ETAPE 9: Activer et démarrer le service")
    steps.append("   Commandes:")
    steps.append("   sudo systemctl daemon-reload")
    steps.append("   sudo systemctl enable deepseek-api")
    steps.append("   sudo systemctl start deepseek-api")
    steps.append("")
    steps.append("ETAPE 10: Vérifier")
    steps.append("   Commandes:")
    steps.append("   sudo systemctl status deepseek-api")
    steps.append("   curl http://localhost:8000/health")
    steps.append("   curl -X POST http://localhost:8000/generate \\")
    steps.append("     -H \"Content-Type: application/json\" \\")
    steps.append("     -d '{\"prompt\": \"Test API\"}'")
    steps.append("")
    steps.append("ETAPE 11: Configurer le firewall")
    steps.append("   Commandes:")
    steps.append("   sudo ufw allow 8000")
    steps.append("   sudo ufw status")
    steps.append("")
    steps.append("ETAPE 12: Tester depuis l'extérieur")
    steps.append("   Récupérer l'IP publique:")
    steps.append("   curl -s ifconfig.me")
    steps.append("   Tester avec:")
    steps.append("   curl -X POST http://<IP_PUBLIQUE>:8000/generate \\")
    steps.append("     -H \"Content-Type: application/json\" \\")
    steps.append("     -d '{\"prompt\": \"Test LM Arena\"}'")
    steps.append("")
    steps.append("=" * 70)
    
    return steps

def generate_troubleshooting_guide():
    """Génère un guide de dépannage"""
    
    guide = []
    
    guide.append("=" * 70)
    guide.append("GUIDE DE DEPANNAGE - DEEPSEEK API EC2")
    guide.append("=" * 70)
    guide.append("")
    guide.append("PROBLEME 1: Service deepseek-api non trouvé")
    guide.append("   Solution: Créer le service systemd")
    guide.append("   sudo nano /etc/systemd/system/deepseek-api.service")
    guide.append("   (voir contenu ci-dessus)")
    guide.append("")
    guide.append("PROBLEME 2: Permission denied sur /opt/deepseek")
    guide.append("   Solution: Changer les permissions")
    guide.append("   sudo chown -R ubuntu:ubuntu /opt/deepseek")
    guide.append("")
    guide.append("PROBLEME 3: Port 8000 non accessible")
    guide.append("   Solution: Configurer le firewall")
    guide.append("   sudo ufw allow 8000")
    guide.append("   sudo ufw enable")
    guide.append("")
    guide.append("PROBLEME 4: API ne démarre pas")
    guide.append("   Vérifier les logs:")
    guide.append("   sudo journalctl -u deepseek-api -f")
    guide.append("   sudo systemctl status deepseek-api")
    guide.append("")
    guide.append("PROBLEME 5: Dépendances manquantes")
    guide.append("   Réinstaller dans l'environnement virtuel:")
    guide.append("   cd /opt/deepseek")
    guide.append("   source venv/bin/activate")
    guide.append("   pip install fastapi uvicorn pydantic")
    guide.append("")
    guide.append("PROBLEME 6: Connexion SSH échouée")
    guide.append("   Vérifier:")
    guide.append("   1. Clé SSH correcte")
    guide.append("   2. Groupe de sécurité (port 22 ouvert)")
    guide.append("   3. Utilisateur correct (ubuntu)")
    guide.append("")
    guide.append("COMMANDES UTILES:")
    guide.append("   Vérifier le service: sudo systemctl status deepseek-api")
    guide.append("   Redémarrer: sudo systemctl restart deepseek-api")
    guide.append("   Voir les logs: sudo journalctl -u deepseek-api -f")
    guide.append("   Tester l'API: curl http://localhost:8000/health")
    guide.append("   IP publique: curl -s ifconfig.me")
    guide.append("")
    guide.append("=" * 70)
    
    return guide

def main():
    """Fonction principale"""
    
    print("=" * 70)
    print("CONFIGURATION COMPLETE POUR DEEPSEEK API SUR EC2")
    print("=" * 70)
    print()
    
    print("1. SERVICE SYSTEMD:")
    print("-" * 40)
    print(generate_systemd_service())
    
    print("\n2. SCRIPT DE DEPLOIEMENT RAPIDE:")
    print("-" * 40)
    print(generate_quick_deploy_script())
    
    print("\n3. INSTRUCTIONS ETAPE PAR ETAPE:")
    print("-" * 40)
    steps = generate_step_by_step_instructions()
    for step in steps:
        print(step)
    
    print("\n4. GUIDE DE DEPANNAGE:")
    print("-" * 40)
    troubleshooting = generate_troubleshooting_guide()
    for line in troubleshooting:
        print(line)
    
    print()
    print("=" * 70)
    print("RESUME DES ACTIONS:")
    print("1. Se connecter à EC2 (172.31.45.211)")
    print("2. Exécuter les commandes étape par étape")
    print("3. Vérifier avec: curl http://localhost:8000/health")
    print("4. Tester avec LM Arena")
    print("=" * 70)

if __name__ == "__main__":
    main()