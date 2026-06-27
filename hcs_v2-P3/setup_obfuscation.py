#!/usr/bin/env python3
"""
Script d'obfuscation pour protéger le code HCS V2 avant déploiement AWS
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def install_obfuscator():
    """Installation des outils d'obfuscation"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyarmor"])
        print("PyArmor installe avec succes")
        return True
    except subprocess.CalledProcessError:
        print("Erreur installation PyArmor")
        return False

def obfuscate_core_modules():
    """Obfuscation des modules critiques"""
    core_modules = [
        "core/k_factor_engine.py",
        "core/webp_optimizer.py", 
        "core/hybrid_compressor.py",
        "core/harmonic_constants.py",
        "core/harmonic_analyzer.py"
    ]
    
    for module in core_modules:
        if os.path.exists(module):
            print(f"Obfuscation de {module}...")
            try:
                subprocess.run([
                    "pyarmor", "gen", 
                    "--output", "dist",
                    "--restrict", "0",
                    "--wrap-mode", "1",
                    module
                ], check=True)
                print(f"{module} obfusque")
            except subprocess.CalledProcessError as e:
                print(f"Erreur obfuscation {module}: {e}")
                return False
    
    return True

def create_production_structure():
    """Creation de la structure production"""
    dirs_to_create = [
        "production/api",
        "production/core",
        "production/frontend",
        "production/config",
        "production/utils"
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Crée: {dir_path}")

def copy_protected_files():
    """Copie des fichiers protégés vers production"""
    
    # Fichiers à copier (non obfusqués)
    public_files = {
        "api/server_production.py": "production/api/",
        "frontend/": "production/frontend/",
        "requirements.txt": "production/",
        "README.md": "production/",
        "config/": "production/config/"
    }
    
    for src, dst in public_files.items():
        if os.path.exists(src):
            if os.path.isdir(src):
                shutil.copytree(src, dst + os.path.basename(src), dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            print(f"Copie: {src} -> {dst}")

def create_env_files():
    """Creation des fichiers environnement sécurisés"""
    
    # .env production
    env_content = """
# HCS V2 Production Environment
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this-in-production
K_FACTOR=0.02
WEBP_QUALITY=95
MAX_FILE_SIZE=104857600
ALLOWED_ORIGINS=https://yourdomain.com
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET=your-s3-bucket
CLOUDFRONT_DOMAIN=your-cloudfront-domain.cloudfront.net
"""
    
    with open("production/.env", "w") as f:
        f.write(env_content)
    print("Fichier .env créé")

def create_dockerfile():
    """Creation du Dockerfile production"""
    dockerfile_content = """
FROM python:3.9-slim

# Configuration securite
RUN adduser --disabled-password --gecos '' appuser
WORKDIR /app

# Installation dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie code obfusqué
COPY dist/ ./dist/
COPY api/ ./api/
COPY frontend/ ./frontend/
COPY config/ ./config/

# Permissions sécurisées
RUN chown -R appuser:appuser /app
USER appuser

# Port sécurisé
EXPOSE 8000

# Commande production
CMD ["python", "api/server_production.py"]
"""
    
    with open("production/Dockerfile", "w") as f:
        f.write(dockerfile_content)
    print("Dockerfile production créé")

def create_aws_deployment_script():
    """Script de déploiement AWS sécurisé"""
    script_content = """#!/bin/bash
# Déploiement AWS HCS V2 Production

echo "Déploiement HCS V2 sur AWS..."

# Configuration AWS
aws configure set region us-east-1

# Build et push Docker
echo "Build Docker..."
docker build -t hcs-v2:latest production/

echo "Tag AWS ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker tag hcs-v2:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hcs-v2:latest

echo "Push ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hcs-v2:latest

# Déploiement ECS
echo "Déploiement ECS..."
aws ecs update-service --cluster hcs-cluster --service hcs-service --force-new-deployment

echo "Déploiement terminé!"
"""
    
    with open("production/deploy_aws.sh", "w") as f:
        f.write(script_content)
    os.chmod("production/deploy_aws.sh", 0o755)
    print("Script déploiement AWS créé")

def create_server_production():
    """Serveur production sécurisé"""
    server_content = '''#!/usr/bin/env python3
"""
HCS V2 Production Server - Version sécurisée pour AWS
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configuration logging sécurisée
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/hcs.log')
    ]
)
logger = logging.getLogger(__name__)

# Variables environnement
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
K_FACTOR = float(os.getenv('K_FACTOR', '0.02'))
WEBP_QUALITY = int(os.getenv('WEBP_QUALITY', '95'))
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '104857600'))
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')

# Initialisation FastAPI
app = FastAPI(
    title="HCS V2 Production API",
    description="Harmonic Compression System - Production Ready",
    version="2.0.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None
)

# CORS sécurisé
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Import des modules obfusqués
try:
    from dist.core.k_factor_engine import KFactorEngine
    from dist.core.webp_optimizer import WebPOptimizer
    from dist.core.hybrid_compressor import HybridCompressor
    logger.info("Modules obfusqués chargés")
except ImportError as e:
    logger.error(f"Erreur import modules: {e}")
    raise

# Health check
@app.get("/health")
async def health_check():
    """Health check pour AWS Load Balancer"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": int(time.time())
    }

# Root endpoint
@app.get("/")
async def root():
    """Endpoint racine production"""
    return {
        "name": "HCS V2 Production",
        "status": "operational",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info",
        access_log=True
    )
'''
    
    with open("production/api/server_production.py", "w") as f:
        f.write(server_content)
    print("Serveur production créé")

def main():
    """Processus complet de protection"""
    print("DEBUT PROTECTION CODE HCS V2")
    print("=" * 50)
    
    # 1. Installation outils
    if not install_obfuscator():
        return False
    
    # 2. Structure production
    create_production_structure()
    
    # 3. Obfuscation modules critiques
    if not obfuscate_core_modules():
        return False
    
    # 4. Copie fichiers
    copy_protected_files()
    
    # 5. Fichiers environnement
    create_env_files()
    create_dockerfile()
    create_aws_deployment_script()
    create_server_production()
    
    print("=" * 50)
    print("PROTECTION TERMINEE")
    print("Code protege dans: production/")
    print("Pret pour deploiement AWS")
    print("Cles a configurer: production/.env")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
