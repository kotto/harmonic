"""
KA CARE — Application de Santé Communautaire
=============================================

Pour agents de santé communautaire dans les zones sous-équipées.

Usage :
  pip install flask flask-cors
  python ka_care.py
  
Ou utiliser le script de démarrage :
  ./start.sh   (Linux/Mac)
  start.bat    (Windows)

Prérequis :
  Python 3.8+
  Flask
  flask-cors
"""

import os
import sys

# Vérifier les dépendances
try:
    from flask import Flask
    from flask_cors import CORS
except ImportError:
    print("=" * 50)
    print("  Dépendances manquantes. Installation...")
    print("=" * 50)
    os.system(f"{sys.executable} -m pip install flask flask-cors")
    print()
    print("Installation terminée. Redémarrez l'application.")
    sys.exit(0)

# Lancer le serveur
if __name__ == '__main__':
    import subprocess
    server_path = os.path.join(os.path.dirname(__file__), 'ka_care.py')
    subprocess.run([sys.executable, server_path])
