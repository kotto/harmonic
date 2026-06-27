#!/usr/bin/env python3
"""
Script to create English versions of French documentation files in the docs/ directory.
"""

import os
import re
from pathlib import Path

# Translation mapping for common terms
TRANSLATIONS = {
    # Document titles and headers
    "Dashboard SaaS complet": "Complete SaaS Dashboard",
    "pour l'intégration avec": "for integration with",
    "technologies harmoniques": "harmonic technologies",
    "Fonctionnalités": "Features",
    "Génération de réponses": "Response generation",
    "Mode vérifié": "Verified mode",
    "Déterminisme garanti": "Guaranteed determinism",
    "Optimisation LM Arena": "LM Arena optimization",
    "Traitement Audio Harmonique": "Harmonic Audio Processing",
    "Traitement Vidéo Harmonique": "Harmonic Video Processing",
    "Gestion SaaS": "SaaS Management",
    "Architecture": "Architecture",
    "Dépendances": "Dependencies",
    "Démarrage rapide": "Quick Start",
    "Configuration": "Configuration",
    "Monitoring": "Monitoring",
    "Sécurité": "Security",
    "Déploiement": "Deployment",
    "Documentation": "Documentation",
    "Support": "Support",
    "Licence": "License",
    
    # Common phrases
    "avec citations": "with citations",
    "et abstention structurée": "and structured abstention",
    "cache LRU": "LRU cache",
    "paramètres spécifiques": "specific parameters",
    "Restauration audio complète": "Complete audio restoration",
    "Amélioration spatiale 3D immersive": "Immersive 3D spatial enhancement",
    "Clarté et netteté optimale": "Optimal clarity and sharpness",
    "Plage dynamique étendue": "Extended dynamic range",
    "Upscaling 4K avec clarté optimale": "4K upscaling with optimal clarity",
    "Masterisation 8K professionnelle": "Professional 8K mastering",
    "Conversion HDR avancée": "Advanced HDR conversion",
    "Génération de frames intermédiaires": "Intermediate frame generation",
    "Génération de films continus": "Continuous movie generation",
    "Authentification JWT": "JWT Authentication",
    "avec refresh tokens": "with refresh tokens",
    "Abonnements": "Subscriptions",
    "Facturation intégration Stripe": "Stripe Billing Integration",
    "API Keys avec permissions granulaires": "API Keys with granular permissions",
    "Prometheus + Grafana": "Prometheus + Grafana",
    
    # Technical terms
    "Backend FastAPI": "FastAPI Backend",
    "Endpoints API": "API Endpoints",
    "Configuration, sécurité, base de données": "Configuration, security, database",
    "Modèles SQLAlchemy": "SQLAlchemy Models",
    "Schémas Pydantic": "Pydantic Schemas",
    "Services métier": "Business Services",
    "Tâches Celery asynchrones": "Celery Async Tasks",
    "Interface utilisateur": "User Interface",
    "Orchestration Docker": "Docker Orchestration",
    "Image Docker API": "API Docker Image",
    "Dépendances Python": "Python Dependencies",
    
    # LM Arena specific
    "Guide Complet LM Arena": "Complete LM Arena Guide",
    "Table des Matières": "Table of Contents",
    "Introduction à LM Arena": "Introduction to LM Arena",
    "Qu'est-ce que LM Arena ?": "What is LM Arena?",
    "préférence humaine": "human preference",
    "qualité perçue": "perceived quality",
    "utilisateurs humains": "human users",
    "benchmarks traditionnels": "traditional benchmarks",
    "métriques techniques": "technical metrics",
    
    # Quick Start specific
    "Guide de démarrage rapide": "Quick Start Guide",
    "en 5 minutes": "in 5 minutes",
    "étapes simples": "simple steps",
    "prérequis": "prerequisites",
    "installation": "installation",
    "configuration": "configuration",
    "démarrage": "startup",
    "vérification": "verification",
    
    # Checklist specific
    "Checklist de validation finale": "Final Validation Checklist",
    "étapes de validation": "validation steps",
    "vérifications": "checks",
    "tests": "tests",
    "configuration système": "system configuration",
    "services en cours d'exécution": "running services",
    "connectivité réseau": "network connectivity",
    "performances": "performance",
    "sécurité": "security",
    "documentation": "documentation",
    
    # AWS Deployment specific
    "Guide de déploiement AWS": "AWS Deployment Guide",
    "étapes de déploiement": "deployment steps",
    "configuration AWS": "AWS configuration",
    "services AWS": "AWS services",
    "EC2 instances": "EC2 instances",
    "S3 buckets": "S3 buckets",
    "Lambda functions": "Lambda functions",
    "IAM roles": "IAM roles",
    "Security Groups": "Security Groups",
    "VPC configuration": "VPC configuration",
}

def translate_text(text):
    """Translate French text to English using the translation mapping."""
    for french, english in TRANSLATIONS.items():
        text = text.replace(french, english)
    
    # Additional pattern-based translations
    text = re.sub(r'(\d+) minutes', r'\1 minutes', text)
    text = re.sub(r'(\d+) étapes', r'\1 steps', text)
    text = re.sub(r'Option (\d+):', r'Option \1:', text)
    
    return text

def create_english_version(french_file_path):
    """Create an English version of a French documentation file."""
    french_path = Path(french_file_path)
    
    # Skip if already English version or not a markdown file
    if not french_path.suffix == '.md':
        return
    
    # Read French content
    with open(french_path, 'r', encoding='utf-8') as f:
        french_content = f.read()
    
    # Translate content
    english_content = translate_text(french_content)
    
    # Create English file path
    if french_path.name.endswith('_FR.md'):
        # Remove _FR suffix for English version
        english_name = french_path.name.replace('_FR.md', '.md')
        english_path = french_path.parent / english_name
    else:
        # Rename French file with _FR suffix
        french_fr_path = french_path.parent / french_path.name.replace('.md', '_FR.md')
        os.rename(french_path, french_fr_path)
        english_path = french_path
    
    # Write English content
    with open(english_path, 'w', encoding='utf-8') as f:
        f.write(english_content)
    
    print(f"Created English version: {english_path.name}")
    if french_path != english_path:
        print(f"  French version renamed to: {french_fr_path.name}")

def process_docs_directory(docs_root):
    """Process all documentation files in the docs directory."""
    docs_root = Path(docs_root)
    
    # Find all markdown files
    md_files = list(docs_root.rglob('*.md'))
    
    print(f"Found {len(md_files)} markdown files in {docs_root}")
    
    # Process each file
    for md_file in md_files:
        # Skip if already processed (contains _FR or _EN)
        if '_FR' in md_file.name or '_EN' in md_file.name:
            continue
        
        # Check if file appears to be in French
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read(500)  # Read first 500 chars
        
        # Simple French detection (common French words)
        french_indicators = ['pour', 'avec', 'dans', 'est', 'sont', 'que', 'les', 'des', 'une', 'un']
        french_word_count = sum(1 for word in french_indicators if word in content.lower())
        
        if french_word_count >= 3:
            print(f"Processing French file: {md_file.relative_to(docs_root)}")
            create_english_version(md_file)

def main():
    """Main function."""
    # Get the docs directory path
    current_dir = Path(__file__).parent
    docs_dir = current_dir / 'docs'
    
    if not docs_dir.exists():
        print(f"Docs directory not found: {docs_dir}")
        return
    
    print("Creating English versions of French documentation...")
    print("=" * 60)
    
    process_docs_directory(docs_dir)
    
    print("=" * 60)
    print("Done! English documentation created.")
    print("\nNote: This is a basic translation. Please review and refine the English content.")

if __name__ == '__main__':
    main()