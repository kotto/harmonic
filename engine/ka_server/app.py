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
__version__ = '4.2.0'

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
    """Factory pattern pour créer l'app Flask.
    
    Relit la config active au moment de la création (pas à l'import) :
    `--product enterprise` doit charger les faits et la config enterprise.
    
    Args:
        config_override: Dict optionnel pour surcharger la config (tests)
    
    Returns:
        Flask app configurée
    """
    global _KA_CONFIG
    try:
        from ka_config import get_active_config as _get_active
        _KA_CONFIG = _get_active()
    except Exception:
        _KA_CONFIG = None

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
    
    # ── Lancer le service de compression fantôme (GhostCompressor) ────────────
    try:
        from ka_background_compress import start_ghost
        start_ghost()
    except Exception as e:
        app.logger.warning(f'GhostCompressor not available: {e}')
    
    def _find_www_dir() -> Path:
        """Localise ka-mobile-android/www/ (racine du repo ou sous-dossier engine/)."""
        here = Path(__file__).resolve()
        for candidate in (here.parent.parent / 'ka-mobile-android',
                          here.parent.parent.parent / 'ka-mobile-android'):
            if (candidate / 'www').is_dir():
                return candidate / 'www'
        return here.parent.parent.parent / 'ka-mobile-android' / 'www'
    
    # ── Health check racine / point d'entrée de l'app mobile ────────────────
    @app.route('/')
    def index():
        """Le point d'entrée de l'app KA Mobile (server.url: http://10.0.2.2:8765).
        L'app vit dans ka-mobile-android/www/ (webDir Capacitor) — la source.
        Repli : le JSON de santé si le shell est absent."""
        _WWW_DIR = _find_www_dir()
        if (_WWW_DIR / 'ka_index.html').exists():
            from flask import send_from_directory
            return send_from_directory(str(_WWW_DIR), 'ka_index.html')
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
    
    # ── Vital KA — Applications métier (frontends embarqués) ──
    @app.route('/vital/')
    def vital_launcher():
        return send_from_directory(_SITES_DIR / 'vital', 'launcher.html')
    
    @app.route('/vital/medecin')
    def vital_medecin():
        return send_from_directory(_SITES_DIR / 'vital', 'medecin.html')
    
    @app.route('/vital/patient')
    def vital_patient():
        return send_from_directory(_SITES_DIR / 'vital', 'patient.html')
    
    @app.route('/vital/pharmacien')
    def vital_pharmacien():
        return send_from_directory(_SITES_DIR / 'vital', 'pharmacien.html')
    
    @app.route('/vital/diaspora')
    def vital_diaspora():
        return send_from_directory(_SITES_DIR / 'vital', 'diaspora.html')
    
    @app.route('/vital/solidarite')
    def vital_solidarite():
        return send_from_directory(_SITES_DIR / 'vital', 'solidarite.html')
    
    @app.route('/vital/teleconsult')
    def vital_teleconsult():
        return send_from_directory(_SITES_DIR / 'vital', 'teleconsult.html')
    
    # ── API Vital KA — Proxy vers admin-server Oracle ──
    @app.route('/api/v1/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
    @app.route('/api/v1/', defaults={'subpath': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
    def vital_api_proxy(subpath):
        """Relaye les appels /api/v1/* vers l'admin-server Vital KA.
        Par défaut : localhost:8000 (Oracle Docker). Configurable via VITAL_API_URL.
        Lorsque Render relaie vers Oracle : définir VITAL_API_URL=http://158.178.215.219:8000
        """
        import requests as http_requests
        from flask import request as flask_req
        
        ORACLE_ADMIN = os.environ.get('VITAL_API_URL', 'http://127.0.0.1:8000')
        url = f'{ORACLE_ADMIN}/{subpath}' if subpath else ORACLE_ADMIN
        url += f'?{flask_req.query_string.decode()}' if flask_req.query_string else ''
        
        headers = {k: v for k, v in flask_req.headers if k.lower() not in ('host', 'content-length')}
        method = flask_req.method
        
        try:
            resp = http_requests.request(
                method, url,
                headers=headers,
                data=flask_req.get_data(),
                timeout=60,
            )
            from flask import Response
            return Response(
                resp.content,
                status=resp.status_code,
                headers={k: v for k, v in resp.headers.items() if k.lower() not in ('transfer-encoding', 'content-encoding', 'content-length')},
            )
        except Exception as e:
            app.logger.warning(f'Vital API proxy error: {e}')
            from flask import jsonify
            return jsonify({'error': 'Proxy error', 'detail': str(e)}), 502
    
    # ── Assets de l'app mobile (www/) — repli vers les routes du site ──
    @app.route('/<path:filename>')
    def app_asset(filename):
        """Sert les assets de l'app (www/ka_*.js, sw.js, icons…) — si le
        fichier n'existe pas dans www/, repli 404 → les routes du site
        (corporation, fondation…) continuent de fonctionner."""
        _WWW_DIR = _find_www_dir()
        from flask import abort
        target = _WWW_DIR / filename
        if target.is_file():
            from flask import send_from_directory
            return send_from_directory(str(_WWW_DIR), filename)
        abort(404)
    
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
        """Landing page publique KA Enterprise (Post-RAG) — vend avant de connecter.
        Les contenus (manifesto, compare, pricing) viennent des endpoints
        publics /api/v2/enterprise/* — une seule source de vérité."""
        return send_from_directory(_SITES_DIR, 'enterprise_landing.html')

    @app.route('/enterprise/console')
    def site_enterprise_console():
        """Console d'administration KA Enterprise (PC-first, clé API requise)."""
        return send_from_directory(_SITES_DIR, 'enterprise.html')

    @app.route('/wave')
    def site_wave_playground():
        """Playground du service SaaS de calcul harmonique (/api/wave/*)."""
        return send_from_directory(_SITES_DIR, 'wave_playground.html')

    @app.route('/sonic-id')
    def site_sonic_id():
        """Démo interactive d'empreinte sonore — chaque identifiant génère un son unique."""
        return send_from_directory(_SITES_DIR, 'sonic_id.html')

    @app.route('/harmonic-ai')
    def site_harmonic_ai():
        """Site institutionnel HARMONIC AI — la société, la technologie, les preuves."""
        return send_from_directory(_SITES_DIR, 'harmonic_ai.html')

    @app.route('/compress')
    def site_compress():
        """Ψ Compress — compression HCV ×213 sans perte. Service en ligne + API."""
        return send_from_directory(_SITES_DIR, 'compress.html')

    @app.route('/compress/console')
    def site_compress_console():
        """Console utilisateur Ψ Compress — upload, historique, stats, graphique."""
        return send_from_directory(_SITES_DIR, 'compress_console.html')

    @app.route('/care')
    def site_care():
        """KA Care — diagnostic IA pour l'Afrique. Hors-ligne, zéro hallucination."""
        return send_from_directory(_SITES_DIR, 'care.html')

    @app.route('/demo')
    def site_demo_public():
        """Démo publique en ligne — sans clé, sans inscription."""
        return send_from_directory(_SITES_DIR, 'demo_public.html')

    @app.route('/blog')
    def site_blog_index():
        """Index des articles de blog HARMONIC AI."""
        return send_from_directory(_SITES_DIR, 'blog.html')

    @app.route('/blog/post-rag-architecture')
    def site_blog_postrag():
        """Article : Architecture IA Enterprise — l'article vs HARMONIC AI."""
        return send_from_directory(_SITES_DIR, 'blog_post_rag_architecture.html')

    @app.route('/brand/<path:filename>')
    def brand_asset(filename):
        """Assets de marque (logos SVG du système HARMONIC AI) — disque argent
        brossé + symbole gravé par produit (ka, psi, wave, enterprise, care)."""
        return send_from_directory(_SITES_DIR / 'brand', filename)

    @app.route('/img/<path:filename>')
    def site_img(filename):
        """Images statiques des sites (démo, captures…)."""
        return send_from_directory(_SITES_DIR / 'img', filename)
    
    # ── Téléchargement (distribution sans store) ──
    @app.route('/download')
    def site_download():
        """Page de téléchargement KA Mobile & Vital Ka (PWA + APK, QR codes)."""
        return send_from_directory(_SITES_DIR, 'download.html')
    
    _APK_PATH = _find_www_dir().parent / 'android' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'
    
    @app.route('/apk')
    def serve_apk():
        """Téléchargement direct de l'APK Android (dernier build)."""
        if not _APK_PATH.exists():
            return {'error': 'APK non disponible — relancer le build'}, 503
        return send_from_directory(
            str(_APK_PATH.parent), _APK_PATH.name,
            mimetype='application/vnd.android.package-archive',
            as_attachment=True, download_name='ka-mobile.apk'
        )
    
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