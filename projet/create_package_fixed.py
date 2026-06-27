#!/usr/bin/env python3
"""
Script pour créer la structure complète du package LM Arena
"""

import os
import sys

# Configurer l'encodage UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def create_structure():
    """Crée la structure complète du package LM Arena"""
    
    # Dossier racine du package
    package_root = os.path.join(os.getcwd(), "lm_arena_package")
    
    # Structure des dossiers
    structure = [
        # Backend
        os.path.join(package_root, "backend", "api"),
        os.path.join(package_root, "backend", "core"),
        os.path.join(package_root, "backend", "models"),
        os.path.join(package_root, "backend", "schemas"),
        os.path.join(package_root, "backend", "services"),
        os.path.join(package_root, "backend", "tasks"),
        
        # Frontend
        os.path.join(package_root, "frontend", "static"),
        os.path.join(package_root, "frontend", "templates"),
        
        # Scripts
        os.path.join(package_root, "scripts", "deployment"),
        os.path.join(package_root, "scripts", "monitoring"),
        os.path.join(package_root, "scripts", "testing"),
        
        # Documentation
        os.path.join(package_root, "docs", "api"),
        os.path.join(package_root, "docs", "guides"),
        os.path.join(package_root, "docs", "reference"),
        
        # Tests
        os.path.join(package_root, "tests", "integration"),
        os.path.join(package_root, "tests", "performance"),
        os.path.join(package_root, "tests", "unit"),
        
        # Configuration
        os.path.join(package_root, "config", "environments"),
        os.path.join(package_root, "config", "secrets"),
        
        # AWS
        os.path.join(package_root, "aws", "ec2"),
        os.path.join(package_root, "aws", "lambda"),
        os.path.join(package_root, "aws", "s3"),
        
        # Monitoring
        os.path.join(package_root, "monitoring", "alerts"),
        os.path.join(package_root, "monitoring", "dashboards"),
        os.path.join(package_root, "monitoring", "metrics"),
    ]
    
    # Créer les dossiers
    for directory in structure:
        os.makedirs(directory, exist_ok=True)
        print(f"[+] Créé : {directory}")
    
    # Créer les fichiers essentiels
    essential_files = [
        # Documentation
        (os.path.join(package_root, "README.md"), "# Package LM Arena - Harmonic AI\n\nPackage complet pour l'intégration et la participation à LM Arena."),
        (os.path.join(package_root, "INSTALL.md"), "# Installation du Package LM Arena\n\nGuide d'installation complet."),
        (os.path.join(package_root, "DEPLOYMENT.md"), "# Déploiement du Package LM Arena\n\nGuide de déploiement étape par étape."),
        
        # Configuration
        (os.path.join(package_root, "config", ".env.example"), "# Variables d'environnement\nAPI_KEY=your_api_key_here\nLM_ARENA_URL=https://arena.lmsys.org"),
        (os.path.join(package_root, "config", "environments", "development.yaml"), "environment: development\ndebug: true"),
        (os.path.join(package_root, "config", "environments", "production.yaml"), "environment: production\ndebug: false"),
        
        # Backend - fichiers vides pour structure
        (os.path.join(package_root, "backend", "__init__.py"), ""),
        (os.path.join(package_root, "backend", "api", "__init__.py"), ""),
        (os.path.join(package_root, "backend", "core", "__init__.py"), ""),
        (os.path.join(package_root, "backend", "models", "__init__.py"), ""),
        (os.path.join(package_root, "backend", "schemas", "__init__.py"), ""),
        (os.path.join(package_root, "backend", "services", "__init__.py"), ""),
        (os.path.join(package_root, "backend", "tasks", "__init__.py"), ""),
        
        # Frontend
        (os.path.join(package_root, "frontend", "index.html"), "<!DOCTYPE html>\n<html>\n<head>\n    <title>LM Arena Dashboard</title>\n</head>\n<body>\n    <h1>LM Arena Dashboard</h1>\n</body>\n</html>"),
        
        # Scripts
        (os.path.join(package_root, "scripts", "install.sh"), "#!/bin/bash\n# Script d'installation Linux/macOS"),
        (os.path.join(package_root, "scripts", "install_windows.ps1"), "# Script d'installation PowerShell pour Windows"),
        (os.path.join(package_root, "scripts", "start.sh"), "#!/bin/bash\n# Script de démarrage principal"),
        (os.path.join(package_root, "scripts", "stop.sh"), "#!/bin/bash\n# Script d'arrêt"),
        
        # Tests
        (os.path.join(package_root, "tests", "__init__.py"), ""),
        (os.path.join(package_root, "tests", "test_integration.py"), "# Tests d'intégration"),
        
        # AWS
        (os.path.join(package_root, "aws", "ec2", "setup.sh"), "# Script de configuration EC2"),
        (os.path.join(package_root, "aws", "lambda", "handler.py"), "# Handler Lambda"),
        
        # Monitoring
        (os.path.join(package_root, "monitoring", "metrics", "prometheus.yml"), "# Configuration Prometheus"),
    ]
    
    # Créer les fichiers
    for file_path, content in essential_files:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[+] Créé : {file_path}")
    
    print(f"\n✅ Structure créée avec succès dans : {package_root}")
    print(f"📁 Nombre de dossiers créés : {len(structure)}")
    print(f"📄 Nombre de fichiers créés : {len(essential_files)}")

if __name__ == "__main__":
    print("=" * 50)
    print("  Création de la structure du package LM Arena")
    print("  Harmonic AI - L'IA Community-Proof")
    print("=" * 50)
    print()
    
    try:
        create_structure()
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")
        sys.exit(1)