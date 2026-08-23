#!/usr/bin/env python3
# wsgi.py — Render entry point for KA Server
# 
# Gunicorn command: gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
#
# This file is needed because python -m ka_server.app does NOT work:
#   __init__.py does `from .app import create_app` which imports app.py as a module,
#   making __name__ != "__main__", so the `if __name__ == "__main__": app.run()` block
#   never executes → Flask has no routes → 404 everywhere.
#
# With this file, gunicorn loads the app via the create_app() factory directly.

import sys
import os

# Ensure engine/ is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ka_server import create_app

# Create the Flask app (factory pattern)
app = create_app()

# Expose for gunicorn
# gunicorn wsgi:app