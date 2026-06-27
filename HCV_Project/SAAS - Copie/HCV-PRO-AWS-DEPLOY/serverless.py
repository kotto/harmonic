#!/usr/bin/env python3
"""
Serverless handler pour Vercel
Route les requêtes vers les endpoints appropriés
"""

import sys
import os

# Ajouter le dossier codecs au path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'codecs'))

from hcv_pro_server import app

# Vercel serverless function handler
def handler(event, context):
    """Handle incoming requests."""
    return app(event, context)

# Pour développement local
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
