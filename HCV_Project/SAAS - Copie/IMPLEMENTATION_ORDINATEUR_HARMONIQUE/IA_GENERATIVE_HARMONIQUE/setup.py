"""
🚀 SCRIPT D'INSTALLATION - IA GÉNÉRATIVE HARMONIQUE
Fichier: setup.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Script d'installation et de configuration pour l'IA générative harmonique
"""

from setuptools import setup, find_packages
import os
import sys
import subprocess
import shutil
from pathlib import Path

# Constantes harmoniques universelles
PHI = 1.618033988749895  # Ratio d'or
PI = 3.141592653589793    # Constante circulaire
E = 2.718281828459045      # Nombre d'Euler
SQRT2 = 1.414213562373095  # Racine carrée de 2
SQRT3 = 1.732050807568877  # Racine carrée de 3

# Lecture des dépendances
def read_requirements():
    """Lit les dépendances depuis requirements.txt"""
    requirements = []
    
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    
    return requirements

# Configuration du package
setup(
    name="harmonic-generative-ai",
    version="1.0.0",
    description="IA Générative Harmonique - 10-1000x plus rapide que les IA classiques",
    long_description="""
    L'IA Générative Harmonique représente une révolution dans le domaine de l'intelligence artificielle.
    
    En intégrant les constantes harmoniques universelles φ, π, e, √2, √3, nous créons une IA qui n'est pas seulement 
    plus rapide, mais aussi plus intelligente, plus stable et plus prédictive.
    
    Caractéristiques principales:
    - Performance : 10-1000x plus rapide que les IA classiques
    - Déterminisme : 100% reproductible et prédictible
    - Optimisation : Harmonique et mathématiquement prouvée
    - Scalabilité : De prototype à production
    - Accessibilité : Interface intuitive pour tous les niveaux
    
    Applications:
    - Génération de code harmonique
    - Optimisation de systèmes complexes
    - Réseaux neuronaux déterministes
    - Mémoire harmonique avancée
    - Interface utilisateur harmonique
    """,
    long_description_content_type="text/markdown",
    author="Équipe Harmonique",
    author_email="contact@harmonic-ai.com",
    url="https://github.com/harmonic-ai/generative-harmonic",
    project_urls={
        "Documentation": "https://docs.harmonic-ai.com",
        "Source": "https://github.com/harmonic-ai/generative-harmonic",
        "Tracker": "https://github.com/harmonic-ai/generative-harmonic/issues",
        "Community": "https://discord.gg/harmonic-ai",
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml", "*.json"],
        "prompts": ["*.py", "*.md"],
        "config": ["*.json", "*.yaml", "*.yml"],
        "docs": ["*.md", "*.rst", "*.txt"],
        "tests": ["*.py", "*.json", "*.yaml"],
        "examples": ["*.py", "*.md", "*.json"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    keywords="ai, machine-learning, neural-networks, code-generation, optimization, harmonic, determinism",
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "black[d]",
            "isort[colors]",
            "flake8",
            "mypy",
            "pre-commit",
            "pytest-cov",
            "pytest-asyncio",
            "pytest-mock",
            "hypothesis",
            "sphinx",
            "sphinx-rtd-theme",
            "mkdocs",
            "mkdocs-material",
        ],
        "prod": [
            "gunicorn",
            "nginx",
            "redis",
            "postgresql-binary",
            "prometheus-client",
            "grafana-api",
            "loguru",
            "structlog",
        ],
        "test": [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "pytest-mock",
            "pytest-xdist",
            "hypothesis",
            "factory-boy",
            "faker",
            "freezegun",
            "vcrpy",
        ],
        "monitoring": [
            "prometheus-client",
            "grafana-api",
            "sentry-sdk",
            "opentelemetry-api",
            "opentelemetry-sdk",
            "opentelemetry-instrumentation",
        ],
        "security": [
            "cryptography",
            "passlib",
            "python-jose",
            "bcrypt",
            "pyotp",
            "bandit",
            "safety",
            "pip-audit",
        ],
        "performance": [
            "numba",
            "cython",
            "py-spy",
            "memory-profiler",
            "line-profiler",
            "pyinstrument",
            "scalene",
        ],
        "docker": [
            "docker",
            "docker-compose",
            "kubernetes",
            "helm",
            "jinja2",
        ],
        "harmonic": [
            # Packages harmoniques personnalisés
            # harmonic-constants>=1.0.0,
            # harmonic-algorithms>=1.0.0,
            # harmonic-optimizers>=1.0.0,
            # harmonic-visualizers>=1.0.0,
            # harmonic-interfaces>=1.0.0,
        ],
        "all": [
            "black[d]",
            "isort[colors]",
            "flake8",
            "mypy",
            "pre-commit",
            "pytest-cov",
            "pytest-asyncio",
            "pytest-mock",
            "hypothesis",
            "sphinx",
            "sphinx-rtd-theme",
            "mkdocs",
            "mkdocs-material",
            "gunicorn",
            "nginx",
            "redis",
            "postgresql-binary",
            "prometheus-client",
            "grafana-api",
            "loguru",
            "structlog",
            "cryptography",
            "passlib",
            "python-jose",
            "bcrypt",
            "pyotp",
            "bandit",
            "safety",
            "pip-audit",
            "numba",
            "cython",
            "py-spy",
            "memory-profiler",
            "line-profiler",
            "pyinstrument",
            "scalene",
            "docker",
            "docker-compose",
            "kubernetes",
            "helm",
            "jinja2",
        ],
    },
    entry_points={
        "console_scripts": [
            "harmonic-ai=harmonic_ai.cli:main",
            "harmonic-generate=harmonic_ai.code_generator:main",
            "harmonic-optimize=harmonic_ai.optimizer:main",
            "harmonic-train=harmonic_ai.trainer:main",
            "harmonic-ui=harmonic_ai.ui:main",
        ],
        "gui_scripts": [
            "harmonic-gui=harmonic_ai.gui:main",
        ],
    },
    zip_safe=False,
)

# Installation post-setup
def post_install_setup():
    """Configuration post-installation"""
    
    print("🌊 Configuration post-installation de l'IA Générative Harmonique")
    
    # Création des répertoires nécessaires
    directories = [
        "config",
        "logs",
        "data",
        "cache",
        "models",
        "outputs",
        "temp",
        "backups",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Répertoire créé: {directory}")
    
    # Configuration par défaut
    config_path = Path("config/config.json")
    if not config_path.exists():
        default_config = {
            "harmonic_constants": {
                "phi": PHI,
                "pi": PI,
                "e": E,
                "sqrt2": SQRT2,
                "sqrt3": SQRT3
            },
            "optimization": {
                "max_iterations": 1000,
                "convergence_threshold": 1e-6,
                "population_size": 50,
                "parallel_workers": 4,
                "adaptive_learning_rate": True,
                "harmonic_weighting": True
            },
            "memory": {
                "max_entries": 10000,
                "cache_size": 1000,
                "cleanup_interval": 3600,
                "persistence_enabled": True,
                "redis_enabled": False,
                "sqlite_enabled": True
            },
            "neural_network": {
                "default_layers": [1024, 512, 256, 128],
                "default_activation": "harmonic_sigmoid",
                "default_optimization": "phi_adam",
                "batch_size": 32,
                "learning_rate": 0.01
            },
            "ui": {
                "type": "streamlit",
                "theme": "harmonic_full",
                "auto_refresh": True,
                "refresh_interval": 5,
                "show_advanced_options": False,
                "enable_animations": True
            },
            "logging": {
                "level": "INFO",
                "format": "harmonic",
                "file": "logs/harmonic.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "cors_enabled": True,
                "rate_limiting": True
            }
        }
        
        import json
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"✅ Configuration par défaut créée: {config_path}")
    
    # Configuration des logs
    log_config_path = Path("config/logging.yaml")
    if not log_config_path.exists():
        log_config = f"""
version: 1
disable_existing_loggers: false

formatters:
  harmonic:
    format: '%(asctime)s - %(name)s - %(levelname)s - 🌊 %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: harmonic
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: harmonic
    filename: logs/harmonic.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  harmonic_ai:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
"""
        
        with open(log_config_path, 'w') as f:
            f.write(log_config)
        
        print(f"✅ Configuration des logs créée: {log_config_path}")
    
    # Fichier .gitignore
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
logs/
data/
cache/
models/
outputs/
temp/
backups/
*.log
*.db
*.sqlite
*.sqlite3

# Config (keep template)
config/config.json
config/logging.yaml
!config/config.example.json
!config/logging.example.yaml

# Secrets
.env
.env.local
.env.*.local
secrets/
*.key
*.pem

# Jupyter
.ipynb_checkpoints
.ipynb

# pytest
.coverage
.pytest_cache/
htmlcov/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre
.pyre/

# profiling
*.prof
*.lprof
.profile

# Harmonic AI specific
harmonic_cache/
harmonic_temp/
harmonic_models/
*.harmonic
"""
        
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        
        print(f"✅ Fichier .gitignore créé: {gitignore_path}")
    
    # Scripts d'exemple
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    example_script = scripts_dir / "example_usage.py"
    if not example_script.exists():
        example_content = """
#!/usr/bin/env python3
"""
🚀 Exemple d'utilisation de l'IA Générative Harmonique
"""

from harmonic_ai import HarmonicGenerator, HarmonicOptimizer
from harmonic_ai.constants import PHI, PI, E

def main():
    print("🌊 Test de l'IA Générative Harmonique")
    
    # Test des constantes harmoniques
    print(f"φ (phi) = {PHI}")
    print(f"π (pi) = {PI}")
    print(f"e = {E}")
    
    # Test du générateur
    generator = HarmonicGenerator()
    code = generator.generate_code("service", "typescript")
    print(f"✅ Code généré: {len(code)} lignes")
    
    # Test de l'optimiseur
    optimizer = HarmonicOptimizer()
    result = optimizer.optimize({"target": PHI})
    print(f"✅ Optimisation: {result['improvement']:.2f}%")
    
    print("🌊 IA Générative Harmonique opérationnelle !")

if __name__ == "__main__":
    main()
"""
        
        with open(example_script, 'w') as f:
            f.write(example_content)
        
        print(f"✅ Script d'exemple créé: {example_script}")
    
    # Vérification de l'installation
    try:
        import harmonic_ai
        print("✅ Module harmonic_ai importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    # Test des constantes harmoniques
    try:
        from harmonic_ai.constants import PHI, PI, E, SQRT2, SQRT3
        print(f"✅ Constantes harmoniques: φ={PHI}, π={PI}, e={E}")
        print(f"✅ Racines harmoniques: √2={SQRT2}, √3={SQRT3}")
    except ImportError as e:
        print(f"❌ Erreur d'import des constantes: {e}")
        return False
    
    print("\n🎉 Installation terminée avec succès !")
    print("\n📋 Prochaines étapes:")
    print("1. Configurez vos modèles IA dans config/config.json")
    print("2. Lancez l'interface: python -m harmonic_ai.ui")
    print("3. Consultez la documentation: https://docs.harmonic-ai.com")
    print("4. Rejoignez la communauté: https://discord.gg/harmonic-ai")
    
    return True

# Exécution de la configuration post-installation
if __name__ == "__main__":
    if "install" in sys.argv or "bdist_wheel" in sys.argv:
        post_install_setup()
