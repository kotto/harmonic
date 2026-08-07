"""
WSGI entry point for PythonAnywhere.
Copier ce fichier dans le dossier /home/<username>/mysite/

Sur PythonAnywhere :
  Web tab → Code → WSGI configuration file → pointer vers ce fichier
"""
import sys
import os

# Ajouter le dossier ka_care au path
project_dir = os.path.join(os.path.dirname(__file__), 'ka_care')
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Importer l'app Flask de KA CARE
from ka_care import app as application
