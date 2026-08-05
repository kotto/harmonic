"""
KA Server — Application Factory
================================
Crée et configure l'application Flask avec toutes les routes,
middleware et services selon la configuration produit active.
"""

import sys
import os
import logging
import logging.handlers
from pathlib import Path
from flask import Flask
from flask_cors import CORS

# Ajouter le répertoire racine au path
_ENGINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ENGINE_DIR))

# Configuration produit
try:
    from ka_config import get_active_config, PRODUCTS
    _KA_CONFIG = get_active_config()
except Exception:
    _KA_CONFIG = None

# Version locale pour éviter import circulaire
__version__ = '4.0.0'

# ── Logging structuré (avec rotation : 5 × 10 Mo) ───────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            'ka_server.log', maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def create_app(config_override: dict = None) -> Flask:
    """
    Factory pattern pour créer l'app Flask.
    
    Args:
        config_override: Dict optionnel pour surcharger la config (tests)
    
    Returns:
        Flask app configurée
    """
    app = Flask(__name__)
    
    # Configuration CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
        }
    })
    
    # Config par défaut
    app.config.update({
        'MAX_CONTENT_LENGTH': 100 * 1024 * 1024,  # 100MB max upload
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': False,
        # Config produit active — lue par ka_server/services (init_services)
        'KA_CONFIG': _KA_CONFIG,
    })
    
    # Surcharge config si fournie
    if config_override:
        app.config.update(config_override)
    
    # ── Enregistrer middleware ──────────────────────────────────────────────
    from ka_server.middleware.metrics import register_metrics_middleware
    from ka_server.middleware.auth import register_auth_middleware
    
    register_metrics_middleware(app)
    register_auth_middleware(app)
    
    # ── Initialiser services ────────────────────────────────────────────────
    from ka_server.services import init_services
    services = init_services(app)
    app.ka_services = services
    
    # ── Enregistrer routes ──────────────────────────────────────────────────
    from ka_server.routes import register_routes
    register_routes(app, services)
    
    # ── Health check racine ─────────────────────────────────────────────────
    @app.route('/')
    def index():
        return {
            'name': _KA_CONFIG.name if _KA_CONFIG else 'KA Server',
            'version': _KA_CONFIG.version if _KA_CONFIG else '4.0.0',
            'product': _KA_CONFIG.product if _KA_CONFIG else 'mobile',
            'status': 'running',
            'endpoints': '/api/health pour health check'
        }
    
    # ── Sites publics (KA Corporation & KA Fondation) ───────────────────────
    from flask import send_from_directory
    _SITES_DIR = Path(__file__).resolve().parent / 'static'
    
    @app.route('/corporation')
    def site_corporation():
        return send_from_directory(_SITES_DIR, 'corporation.html')
    
    @app.route('/fondation')
    def site_fondation():
        return send_from_directory(_SITES_DIR, 'fondation.html')
    
    # Versions anglaises
    @app.route('/en/corporation')
    def site_corporation_en():
        return send_from_directory(_SITES_DIR, 'corporation_en.html')
    
    @app.route('/en/fondation')
    def site_fondation_en():
        return send_from_directory(_SITES_DIR, 'fondation_en.html')
    
    @app.route('/enterprise')
    def site_enterprise():
        """Console d'administration KA Enterprise (PC-first)."""
        return send_from_directory(_SITES_DIR, 'enterprise.html')
    
    log.info("=" * 55)
    log.info(f"  KA Server v{__version__} — {(_KA_CONFIG.name if _KA_CONFIG else 'KA')}")
    log.info(f"  Produit: {(_KA_CONFIG.product if _KA_CONFIG else 'mobile')}")
    log.info("=" * 55)
    
    return app


# ── Point d'entrée direct ──────────────────────────────────────────────────
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='KA Server')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--host', type=str, default='0.0.0.0')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--product', type=str, default='mobile',
                       choices=['mobile', 'pc', 'enterprise'])
    args = parser.parse_args()
    
    # Définir produit avant création app
    if args.product:
        os.environ['KA_PRODUCT'] = args.product
        from ka_config import get_config, set_active_config
        set_active_config(get_config(args.product))
    
    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)