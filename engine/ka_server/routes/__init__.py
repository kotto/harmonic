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
from .harmonic import register_harmonic_routes
from .wave import register_wave_routes
from .memory_first import register_memory_first_routes
from .demo_public import register_demo_public_routes
from .sonic_id import register_sonic_id_routes
from .compress_dashboard import register_compress_dashboard_routes
from .tools import register_tools_routes
from .banking import register_banking_routes


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
    
    # Routes Harmonic AI v3 (intelligence ondulatoire unifiée)
    register_harmonic_routes(app, services)
    
    # Routes Wave Compute — SaaS de calcul harmonique (clé API + quota)
    register_wave_routes(app, services)
    
    # Routes Memory-First — l'architecture memory-first (provenance + refus)
    register_memory_first_routes(app, services)
    
# Routes Démo Publique — la preuve en ligne (sans authentification)
    register_demo_public_routes(app, services)

    # Routes Sonic ID — empreinte sonore pseudo-aléatoire par identifiant
    register_sonic_id_routes(app, services)

    # Routes Dashboard Compression — historique & stats Ψ Compress
    register_compress_dashboard_routes(app, services)

    # Routes Agent (peuvent nécessiter auth selon config)
    register_agent_routes(app, services)
    
    # Routes Tools — analyse document, traduction, idées
    register_tools_routes(app, services)
    
    # Routes Banking — émission UM / conversion CFA (Ecobank)
    register_banking_routes(app, services)
    
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
    'register_harmonic_routes',
    'register_wave_routes',
    'register_memory_first_routes',
    'register_demo_public_routes',
    'register_banking_routes',
]