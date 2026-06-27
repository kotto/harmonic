#!/usr/bin/env python3
"""
Script pour organiser les fichiers existants dans la structure du package LM Arena
"""

import os
import shutil
import sys
from pathlib import Path

# Configurer l'encodage UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def organize_files():
    """Organise les fichiers existants dans la structure du package"""
    
    # Dossier racine du package
    package_root = Path("lm_arena_package")
    
    # Dossier source principal
    source_root = Path(".")
    
    # Mappage des fichiers source -> destination package
    file_mapping = {
        # Backend - API
        "harmonic_saas/app/api/v1/api.py": "backend/api/api.py",
        "harmonic_saas/app/api/v1/endpoints/chat.py": "backend/api/chat.py",
        "harmonic_saas/app/services/lm_arena_integration.py": "backend/services/lm_arena_integration.py",
        
        # Backend - Core
        "harmonic_saas/app/core/config.py": "backend/core/config.py",
        "harmonic_saas/app/core/database.py": "backend/core/database.py",
        "harmonic_saas/app/core/logging.py": "backend/core/logging.py",
        "harmonic_saas/app/core/security.py": "backend/core/security.py",
        
        # Backend - Models
        "harmonic_saas/app/models/__init__.py": "backend/models/__init__.py",
        "harmonic_saas/app/models/user.py": "backend/models/user.py",
        "harmonic_saas/app/models/api_key.py": "backend/models/api_key.py",
        "harmonic_saas/app/models/usage.py": "backend/models/usage.py",
        
        # Backend - Schemas
        "harmonic_saas/app/schemas/__init__.py": "backend/schemas/__init__.py",
        "harmonic_saas/app/schemas/chat.py": "backend/schemas/chat.py",
        "harmonic_saas/app/schemas/user.py": "backend/schemas/user.py",
        
        # Backend - Tasks
        "harmonic_saas/app/tasks/audio_tasks.py": "backend/tasks/audio_tasks.py",
        "harmonic_saas/app/tasks/video_tasks.py": "backend/tasks/video_tasks.py",
        
        # Frontend
        "harmonic_saas/frontend/index.html": "frontend/index.html",
        "harmonic_saas/frontend/app.js": "frontend/app.js",
        "harmonic_saas/frontend/config.js": "frontend/config.js",
        
        # Scripts
        "lm_arena_package/scripts/install.sh": "scripts/install.sh",
        "lm_arena_package/scripts/install_windows.ps1": "scripts/install_windows.ps1",
        "lm_arena_package/scripts/start.sh": "scripts/start.sh",
        "lm_arena_package/scripts/stop.sh": "scripts/stop.sh",
        
        # Documentation
        "harmonic_saas/LM_ARENA_GUIDE.md": "docs/guides/lm_arena_guide.md",
        "harmonic_saas/README.md": "docs/guides/saas_readme.md",
        "harmonic_saas/QUICK_START.md": "docs/guides/quick_start.md",
        "harmonic_saas/FINAL_CHECKLIST.md": "docs/guides/final_checklist.md",
        "harmonic_saas/deploy_aws.md": "docs/guides/deploy_aws.md",
        
        # Tests
        "harmonic_saas/test_lm_arena_integration.py": "tests/integration/test_lm_arena_integration.py",
        "lm_arena_test_final.py": "tests/performance/lm_arena_test_final.py",
        "lm_arena_comprehensive_test.py": "tests/performance/lm_arena_comprehensive_test.py",
        "detailed_lm_arena_test.py": "tests/performance/detailed_lm_arena_test.py",
        
        # Configuration
        "harmonic_saas/requirements.txt": "config/requirements.txt",
        "harmonic_saas/docker-compose.yml": "config/docker-compose.yml",
        "harmonic_saas/Dockerfile": "config/Dockerfile",
        
        # AWS
        "harmonic_saas/check_aws_services.py": "aws/ec2/check_aws_services.py",
        "deploy_qwen_aws.ps1": "aws/ec2/deploy_qwen_aws.ps1",
        "deploy_qwen_aws.sh": "aws/ec2/deploy_qwen_aws.sh",
        "aws_audit_cleanup.py": "aws/cleanup/aws_audit_cleanup.py",
        
        # Monitoring
        "harmonic_saas/app/core/logging.py": "monitoring/logging_config.py",
        
        # Fichiers essentiels pour LM Arena
        "deepseek_api_real_final.py": "backend/services/deepseek_api.py",
        "deepseek_api_deepseek_backend.py": "backend/services/deepseek_backend.py",
        "benchmark_verified_mode.py": "tests/performance/benchmark_verified_mode.py",
        "benchmark_verified_mode_dataset.json": "tests/data/benchmark_dataset.json",
        
        # Scripts de démarrage
        "harmonic_saas/start_harmonic_services.bat": "scripts/windows/start_harmonic_services.bat",
        "harmonic_saas/run_final_check.bat": "scripts/windows/run_final_check.bat",
        
        # Documentation technique
        "ANALYSE_ANTI_MENSONGES_HARMONIC_AI.md": "docs/reference/anti_mensonges.md",
        "BREVET_FINAL_ALAIN_KOTTO.md": "docs/reference/brevet.md",
        "IA_COMMUNITY_PROOF.md": "docs/reference/community_proof.md",
        "MONETISATION_IMMEDIATE_HARMONIC_AI.md": "docs/reference/monetisation.md",
        "PLAN_INVESTISSEURS_HARMONIC_AI.md": "docs/reference/investisseurs.md",
        
        # Rapports et analyses
        "analyse_comparative_lm_arena.md": "docs/analysis/comparative_analysis.md",
        "rapport_lm_arena_direct.md": "docs/analysis/direct_report.md",
        "comparaison_modeles_recents_lm_arena.md": "docs/analysis/model_comparison.md",
        
        # Fichiers de configuration AWS
        "aws_protection_plan_simple.json": "aws/security/protection_plan.json",
        "aws_security_protection_plan.py": "aws/security/security_plan.py",
    }
    
    # Fichiers à copier avec traitement spécial
    special_files = {
        # Fichiers de test LM Arena
        "lm_arena_package/tests/performance/lm_arena_test.py": "tests/performance/lm_arena_test.py",
        "lm_arena_package/tests/integration/test_lm_arena.py": "tests/integration/test_lm_arena.py",
        
        # Fichiers de configuration
        "lm_arena_package/config/.env.example": "config/.env.example",
        "lm_arena_package/config/environments/development.yaml": "config/environments/development.yaml",
        "lm_arena_package/config/environments/production.yaml": "config/environments/production.yaml",
        
        # Fichiers AWS
        "lm_arena_package/aws/ec2/setup.sh": "aws/ec2/setup.sh",
        "lm_arena_package/aws/lambda/handler.py": "aws/lambda/handler.py",
        
        # Fichiers de monitoring
        "lm_arena_package/monitoring/metrics/prometheus.yml": "monitoring/metrics/prometheus.yml",
    }
    
    print("=" * 60)
    print("  Organisation des fichiers dans le package LM Arena")
    print("  Harmonic AI - L'IA Community-Proof")
    print("=" * 60)
    print()
    
    # Compter les fichiers organisés
    organized_count = 0
    skipped_count = 0
    
    # Organiser les fichiers du mapping principal
    for source_path_str, dest_path_str in file_mapping.items():
        source_path = Path(source_path_str)
        dest_path = package_root / dest_path_str
        
        if source_path.exists():
            # Créer le dossier parent si nécessaire
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copier le fichier
            shutil.copy2(source_path, dest_path)
            print(f"[+] Organisé : {source_path} → {dest_path}")
            organized_count += 1
        else:
            print(f"[-] Non trouvé : {source_path}")
            skipped_count += 1
    
    # Copier les fichiers spéciaux (déjà dans la structure)
    for source_path_str, dest_path_str in special_files.items():
        source_path = Path(source_path_str)
        dest_path = package_root / dest_path_str
        
        if source_path.exists():
            # Créer le dossier parent si nécessaire
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copier le fichier
            shutil.copy2(source_path, dest_path)
            print(f"[+] Copié : {source_path} → {dest_path}")
            organized_count += 1
    
    # Créer des fichiers de configuration supplémentaires
    create_additional_files(package_root)
    
    print()
    print("=" * 60)
    print(f"✅ Organisation terminée !")
    print(f"📄 Fichiers organisés : {organized_count}")
    print(f"📄 Fichiers non trouvés : {skipped_count}")
    print(f"📁 Package disponible dans : {package_root}")
    print("=" * 60)

def create_additional_files(package_root):
    """Crée des fichiers supplémentaires pour compléter le package"""
    
    # Fichier de configuration principal
    config_content = """# Configuration principale LM Arena Package
# Harmonic AI - L'IA Community-Proof

# Paramètres de l'API
API_HOST = "0.0.0.0"
API_PORT = 8000
API_WORKERS = 4

# Base de données
DATABASE_URL = "postgresql://user:password@localhost/harmonic_ai"
REDIS_URL = "redis://localhost:6379/0"

# Services harmoniques
AUDIO_SERVICE_PORT = 9017
VIDEO_SERVICE_PORT = 9018

# LM Arena
LM_ARENA_API_URL = "https://arena.lmsys.org"
LM_ARENA_TIMEOUT = 30

# Sécurité
JWT_SECRET_KEY = "votre-cle-secrete-jwt"
API_KEY_HEADER = "X-API-Key"
"""
    
    config_path = package_root / "config" / "config.py"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config_content, encoding='utf-8')
    print(f"[+] Créé : {config_path}")
    
    # Fichier de démarrage principal
    main_content = """#!/usr/bin/env python3
"""
    
    main_path = package_root / "backend" / "main.py"
    main_path.write_text(main_content, encoding='utf-8')
    print(f"[+] Créé : {main_path}")
    
    # Fichier requirements complet
    requirements_content = """# Requirements pour LM Arena Package
# Harmonic AI - L'IA Community-Proof

fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
httpx==0.25.1
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.4
flower==2.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiofiles==23.2.1
prometheus-client==0.19.0
structlog==23.2.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
isort==5.12.0
mypy==1.7.0
ruff==0.1.6
"""
    
    requirements_path = package_root / "requirements.txt"
    requirements_path.write_text(requirements_content, encoding='utf-8')
    print(f"[+] Créé : {requirements_path}")
    
    # Fichier docker-compose complet
    docker_compose_content = """version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db/harmonic_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=harmonic_ai
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A backend.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:password@db/harmonic_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs

  flower:
    build: .
    command: celery -A backend.celery_app flower --port=5555
    environment:
      - DATABASE_URL=postgresql://user:password@db/harmonic_ai
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "5555:5555"
    depends_on:
      - celery

volumes:
  postgres_data:
"""
    
    docker_compose_path = package_root / "docker-compose.yml"
    docker_compose_path.write_text(docker_compose_content, encoding='utf-8')
    print(f"[+] Créé : {docker_compose_path}")

if __name__ == "__main__":
    organize_files()