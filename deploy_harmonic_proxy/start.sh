#!/bin/bash
# Demarrage du proxy harmonique sur EC2
cd /home/ubuntu/harmonic-proxy

# Charger les variables d'environnement
export $(grep -v '^#' .env | xargs)

# Installer les dependances
pip install -r requirements.txt

# Lancer le serveur
python harmonic_aws_surgery.py --mode serve --port 8080
