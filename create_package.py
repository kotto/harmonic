#!/usr/bin/env python3
"""
Script pour créer la structure complète du package LM Arena
"""

import os

# Racine du package
package_root = r"F:\SAAS - Copie\lm_arena_package"

# Structure des dossiers
structure = [
    "backend",
    "backend/api",
    "backend/core", 
    "backend/models",
    "backend/schemas",
    "backend/services",
    "backend/tasks",
    "frontend",
    "frontend/static",
    "frontend/templates",
    "scripts",
    "scripts/deployment",
    "scripts/monitoring",
    "scripts/testing",
    "docs",
    "docs/api",
    "docs/guides",
    "docs/reference",
    "tests",
    "tests/integration",
    "tests/performance",
    "tests/unit",
    "config",
    "config/environments",
    "config/secrets",
    "aws",
    "aws/ec2",
    "aws/lambda",
    "aws/s3",
    "monitoring",
    "monitoring/alerts",
    "monitoring/dashboards",
    "monitoring/metrics"
]

print("Création de la structure du package LM Arena...")

# Créer tous les dossiers
for folder in structure:
    full_path = os.path.join(package_root, folder)
    if not os.path.exists(full_path):
        os.makedirs(full_path, exist_ok=True)
        print(f"  ✓ Créé: {folder}")
    else:
        print(f"  ⚠ Existe déjà: {folder}")

print(f"\nStructure créée avec succès !")
print(f"Emplacement: {package_root}")

# Lister les dossiers créés
print("\nDossiers créés:")
for root, dirs, files in os.walk(package_root):
    level = root.replace(package_root, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for d in dirs:
        print(f"{subindent}{d}/")