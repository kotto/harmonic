#!/bin/bash
# Script de deploiement simple

INSTANCE_IP="54.81.62.140"
SSH_USER="ubuntu"
SSH_KEY="C:\Users\maatc/.ssh\qwen35-keypair.pem"
DEPLOY_DIR="/home/ubuntu/deepseek-harmonic-v2-real"

echo "Deploiement sur EC2..."
echo "Instance: $INSTANCE_IP"
echo "Repertoire: $DEPLOY_DIR"

# Tester la connexion SSH
echo "Test connexion SSH..."
ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SSH_USER@$INSTANCE_IP" "echo 'Connexion SSH OK' && hostname"

if [ $? -eq 0 ]; then
    echo "Connexion SSH etablie"
    
    # Creer le repertoire de deploiement
    echo "Creation repertoire..."
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$INSTANCE_IP" "sudo mkdir -p $DEPLOY_DIR && sudo chown ubuntu:ubuntu $DEPLOY_DIR"
    
    # Copier les fichiers
    echo "Copie fichiers..."
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no deploy_temp/* "$SSH_USER@$INSTANCE_IP:$DEPLOY_DIR/"
    
    # Installer les dependances
    echo "Installation dependances..."
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$INSTANCE_IP" "cd $DEPLOY_DIR && pip3 install fastapi uvicorn pydantic"
    
    # Demarrer l'application
    echo "Demarrage application..."
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$INSTANCE_IP" "cd $DEPLOY_DIR && nohup python3 deepseek_api_real.py > app.log 2>&1 &"
    
    echo "Deploiement termine!"
    echo "API disponible sur: http://$INSTANCE_IP:8000"
    echo "Health check: http://$INSTANCE_IP:8000/health"
    
else
    echo "Erreur connexion SSH"
    exit 1
fi
