"""
🤖 GEMMA 4 HARMONIC INTEGRATION - SETUP
Fichier: setup.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Installation et configuration de Gemma 4 Harmonique
"""

from setuptools import setup, find_packages
import os

# Lecture des dépendances
def read_requirements():
    """Lit les dépendances depuis requirements.txt"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_path, 'r') as f:
        requirements = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                requirements.append(line)
        return requirements

# Lecture du README
def read_readme():
    """Lit le README"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README_GEMMA4.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Gemma 4 Harmonic Integration - AI générative optimisée avec les constantes harmoniques"

# Configuration du setup
setup(
    name="gemma4-harmonic",
    version="1.0.0",
    author="Équipe Harmonique",
    author_email="contact@harmonic-ai.com",
    description="Intégration de Gemma 4 avec optimisation harmonique",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/harmonic-ai/gemma4-harmonic",
    project_urls={
        "Bug Tracker": "https://github.com/harmonic-ai/gemma4-harmonic/issues",
        "Documentation": "https://github.com/harmonic-ai/gemma4-harmonic/wiki",
        "Source Code": "https://github.com/harmonic-ai/gemma4-harmonic",
    },
    packages=find_packages(),
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
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "gpu": [
            "torch-audio>=2.0.0",
            "torchvision>=0.15.0",
        ],
        "monitoring": [
            "psutil>=5.9.0",
            "GPUtil>=1.4.0",
            "tensorboard>=2.13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gemma4-harmonic=ai_models.gemma4_harmonic_integration:main",
            "gemma4-generate=ai_models.gemma4_harmonic_integration:generate_code_cli",
        ],
    },
    include_package_data=True,
    package_data={
        "ai_models": [
            "templates/*.py",
            "configs/*.json",
            "data/*.txt",
        ],
    },
    keywords=[
        "artificial intelligence",
        "machine learning",
        "code generation",
        "gemma",
        "harmonic optimization",
        "transformers",
        "pytorch",
        "nlp",
        "llm",
    ],
    zip_safe=False,
)
