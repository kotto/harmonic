"""
KA Server — Routes Package
==========================
Enregistre toutes les routes API par domaine.
"""

from .chat import register_chat_routes
from .media import register_media_routes
from .agent import register_agent_routes
from .enterprise import register_enterprise_routes
from .health import register_health_routes
from .store import register_store_routes
from .voice import register_voice_routes
from .code import register_code_routes
from .specialize import register_specialize_routes
from .system import register_system_routes


def register_routes(app, services):
    """
    Enregistre toutes les routes sur l'application Flask.
    
    Args:
        app: Instance Flask
        services: Dict des services initialisés
    """
    # Routes publiques (sans auth)
    register_health_routes(app, services)
    register_system_routes(app, services)
    
    # Routes API principales
    register_chat_routes(app, services)
    register_media_routes(app, services)
    register_voice_routes(app, services)
    register_code_routes(app, services)
    register_specialize_routes(app, services)
    register_store_routes(app, services)
    
    # Routes Enterprise (nécessitent API key)
    register_enterprise_routes(app, services)
    
    # Routes Agent (peuvent nécessiter auth selon config)
    register_agent_routes(app, services)
    
    # Log résumé
    import logging
    log = logging.getLogger(__name__)
    rules = [r.rule for r in app.url_map.iter_rules() if r.rule.startswith('/api/')]
    log.info(f"  🛣️  Routes enregistrées: {len(rules)} endpoints API")


__all__ = [
    'register_routes',
    'register_chat_routes',
    'register_media_routes',
    'register_agent_routes',
    'register_enterprise_routes',
    'register_health_routes',
    'register_store_routes',
    'register_voice_routes',
    'register_code_routes',
    'register_specialize_routes',
    'register_system_routes',
]