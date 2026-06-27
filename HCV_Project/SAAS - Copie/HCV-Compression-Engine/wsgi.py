#!/usr/bin/env python3
"""
WSGI application pour production
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'server'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'codecs'))

from hcv_pro_server import app

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
