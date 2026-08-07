"""
KA Server — Routes Health
==========================
Endpoints de santé et diagnostic système.
"""

import logging
import sys
import platform
from flask import request, jsonify, g

log = logging.getLogger(__name__)


def register_health_routes(app, services):
    """Enregistre les routes de health check."""
    
    @app.route('/api/health', methods=['GET'])
    def api_health():
        """Health check basique."""
        return jsonify({
            'status': 'healthy',
            'service': 'ka-server',
            'version': '4.0.0'
        })
    
    @app.route('/api/health/detailed', methods=['GET'])
    def api_health_detailed():
        """Health check détaillé avec status services."""
        config = services.get('config', {})
        
        # Vérifier services
        services_status = {}
        
        # Harmonic AI
        ai = services.get('harmonic_ai')
        brain = services.get('brain')
        services_status['harmonic_ai'] = 'ok' if (ai or brain) else 'unavailable'
        
        # HWAT
        hwat = services.get('hwat_bridge')
        services_status['hwat'] = 'ok' if (hwat and services.get('hwat_available')) else 'unavailable'
        
        # HCV Codec
        hcv = services.get('hcv_codec')
        if hcv:
            hcv_status = hcv.get_hcv_status()
            services_status['hcv_codec'] = 'ok' if (hcv_status['wasm_ready'] or hcv_status['server_available']) else 'fallback_only'
        else:
            services_status['hcv_codec'] = 'unavailable'
        
        # Voice Engine
        voice = services.get('voice_engine')
        services_status['voice_engine'] = 'ok' if voice else 'unavailable'
        
        # Hologram Store
        holo = services.get('hologram_store')
        services_status['hologram_store'] = 'ok' if holo else 'unavailable'
        
        # Web Retriever
        web = services.get('web_retriever')
        services_status['web_retriever'] = 'ok' if web else 'unavailable'
        
        # Specializer
        spec = services.get('specializer')
        services_status['specializer'] = 'ok' if spec else 'unavailable'
        
        # Enterprise
        ent = services.get('enterprise_ingestor')
        services_status['enterprise'] = 'ok' if ent else 'unavailable'
        
        # Déterminer santé globale
        critical_services = ['harmonic_ai', 'hcv_codec']
        unhealthy = [s for s in critical_services if services_status.get(s) == 'unavailable']
        
        overall = 'healthy' if not unhealthy else 'degraded' if len(unhealthy) < 2 else 'unhealthy'
        
        return jsonify({
            'status': overall,
            'service': 'ka-server',
            'version': '4.0.0',
            'product': config.get('product', 'mobile') if config else 'mobile',
            'services': services_status,
            'python_version': sys.version.split()[0],
            'platform': platform.platform(),
        })
    
    @app.route('/api/health/live', methods=['GET'])
    def api_health_live():
        """Liveness probe (Kubernetes)."""
        return jsonify({'status': 'alive'}), 200
    
    @app.route('/api/health/ready', methods=['GET'])
    def api_health_ready():
        """Readiness probe (Kubernetes)."""
        # Vérifier services critiques
        ai = services.get('harmonic_ai')
        brain = services.get('brain')
        
        if not ai and not brain:
            return jsonify({
                'status': 'not_ready',
                'reason': 'Harmonic AI not initialized'
            }), 503
        
        return jsonify({'status': 'ready'}), 200
    
    @app.route('/api/health/services', methods=['GET'])
    def api_health_services():
        """Status détaillé de chaque service."""
        return jsonify({
            'harmonic_ai': _check_harmonic_ai(services),
            'hcv_codec': _check_hcv(services),
            'voice_engine': _check_voice(services),
            'hologram_store': _check_hologram_store(services),
            'specializer': _check_specializer(services),
            'web_retriever': _check_web_retriever(services),
            'enterprise': _check_enterprise(services),
        })


def _check_harmonic_ai(services):
    ai = services.get('harmonic_ai')
    brain = services.get('brain')
    hwat = services.get('hwat_bridge')
    return {
        'harmonic_ai': 'ok' if ai else 'unavailable',
        'brain': 'ok' if brain else 'unavailable',
        'hwat': 'ok' if (hwat and services.get('hwat_available')) else 'unavailable',
    }


def _check_hcv(services):
    hcv = services.get('hcv_codec')
    if hcv:
        return hcv.get_hcv_status()
    return {'wasm_ready': False, 'server_available': False, 'fallback': 'pillow'}


def _check_voice(services):
    voice = services.get('voice_engine')
    return {
        'available': voice is not None,
        'tts': 'piper' if voice else None,
        'stt': 'vosk' if voice else None,
    }


def _check_hologram_store(services):
    holo = services.get('hologram_store')
    if holo:
        try:
            holos = holo.list_holograms()
            return {
                'available': True,
                'count': len(holos),
                'holograms': [h['id'] for h in holos[:10]]
            }
        except Exception:
            pass
    return {'available': False, 'count': 0}


def _check_specializer(services):
    spec = services.get('specializer')
    opt_spec = services.get('optimized_specializer')
    return {
        'domain_specializer': 'ok' if spec else 'unavailable',
        'optimized_specializer': 'ok' if opt_spec else 'unavailable',
    }


def _check_web_retriever(services):
    web = services.get('web_retriever')
    return {'available': web is not None}


def _check_enterprise(services):
    ent = services.get('enterprise_ingestor')
    return {'available': ent is not None}