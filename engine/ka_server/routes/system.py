"""
KA Server — Routes System
==========================
Endpoints système: métriques, stats, config, debug.
"""

import logging
from flask import request, jsonify, g

log = logging.getLogger(__name__)


def register_system_routes(app, services):
    """Enregistre les routes système."""
    
    config = services.get('config', {})
    
    @app.route('/api/stats', methods=['GET'])
    def api_stats():
        """Statistiques générales du serveur."""
        # Métriques depuis middleware
        metrics = app.ka_metrics if hasattr(app, 'ka_metrics') else {}
        
        # Services stats
        holo = services.get('hologram_store')
        holo_count = len(holo.list_holograms()) if holo else 0
        
        brain = services.get('brain')
        brain_facts = len(brain.facts) if brain and hasattr(brain, 'facts') else 0
        
        return jsonify({
            'server': {
                'version': '4.0.0',
                'product': config.get('product', 'mobile') if config else 'mobile',
                'uptime_seconds': _get_uptime(),
            },
            'requests': {
                'total': metrics.get('requests_total', 0) if isinstance(metrics, dict) else 0,
                'by_endpoint': metrics.get('requests_by_endpoint', {}) if isinstance(metrics, dict) else {},
                'avg_latency_ms': metrics.get('avg_latency_ms', {}) if isinstance(metrics, dict) else {},
            },
            'ai': {
                'harmonic_requests': metrics.get('harmonic_count', 0) if isinstance(metrics, dict) else 0,
                'llm_requests': metrics.get('llm_count', 0) if isinstance(metrics, dict) else 0,
                'brain_facts': brain_facts,
            },
            'storage': {
                'holograms': holo_count,
            },
            'rate_limiting': {
                'tracked_ips': metrics.get('rate_limit_tracked_ips', 0) if isinstance(metrics, dict) else 0,
            }
        })
    
    @app.route('/api/metrics', methods=['GET'])
    def api_metrics():
        """Métriques détaillées (Prometheus-style)."""
        metrics = app.ka_metrics if hasattr(app, 'ka_metrics') else {}
        
        if not isinstance(metrics, dict):
            return jsonify({'error': 'Metrics not available'}), 503
        
        # Format Prometheus-like
        lines = []
        lines.append('# HELP ka_requests_total Total requests by endpoint')
        lines.append('# TYPE ka_requests_total counter')
        for ep, count in metrics.get('requests_by_endpoint', {}).items():
            lines.append(f'ka_requests_total{{endpoint="{ep}"}} {count}')
        
        lines.append('# HELP ka_request_latency_ms Average latency by endpoint')
        lines.append('# TYPE ka_request_latency_ms gauge')
        for ep, latency in metrics.get('avg_latency_ms', {}).items():
            lines.append(f'ka_request_latency_ms{{endpoint="{ep}"}} {latency}')
        
        lines.append('# HELP ka_harmonic_requests_total Total harmonic AI requests')
        lines.append('# TYPE ka_harmonic_requests_total counter')
        lines.append(f'ka_harmonic_requests_total {metrics.get("harmonic_count", 0)}')
        
        lines.append('# HELP ka_llm_requests_total Total LLM requests')
        lines.append('# TYPE ka_llm_requests_total counter')
        lines.append(f'ka_llm_requests_total {metrics.get("llm_count", 0)}')
        
        return '\n'.join(lines), 200, {'Content-Type': 'text/plain; version=0.0.4'}
    
    @app.route('/api/metrics/json', methods=['GET'])
    def api_metrics_json():
        """Métriques en JSON."""
        metrics = app.ka_metrics if hasattr(app, 'ka_metrics') else {}
        return jsonify(metrics.get_metrics() if hasattr(metrics, 'get_metrics') else metrics)
    
    @app.route('/api/config', methods=['GET'])
    def api_config():
        """Configuration produit pour le frontend."""
        if config:
            return jsonify(config.to_dict() if hasattr(config, 'to_dict') else config)
        return jsonify({
            'product': 'mobile',
            'name': 'KA Mobile',
            'version': '4.0.0',
            'features': {
                'chat': True,
                'voice': True,
                'hcv': True,
                'holograms': True,
                'specialize': True,
                'enterprise': False,
            }
        })
    
    @app.route('/api/debug/info', methods=['GET'])
    def api_debug_info():
        """Info debug (seulement si debug activé)."""
        if not config.get('debug', False) if config else False:
            return jsonify({'error': 'Debug mode not enabled'}), 403
        
        import sys
        import os
        
        return jsonify({
            'python_version': sys.version,
            'platform': sys.platform,
            'cwd': os.getcwd(),
            'env': {k: v for k, v in os.environ.items() if not any(s in k.lower() for s in ['key', 'secret', 'password', 'token'])},
            'sys_path': sys.path[:10],
            'modules_loaded': len(sys.modules),
        })
    
    @app.route('/api/debug/services', methods=['GET'])
    def api_debug_services():
        """Status détaillé des services (debug)."""
        if not config.get('debug', False) if config else False:
            return jsonify({'error': 'Debug mode not enabled'}), 403
        
        return jsonify({
            'harmonic_ai': _service_info(services.get('harmonic_ai'), 'HarmonicAI'),
            'brain': _service_info(services.get('brain'), 'HarmonicBrain'),
            'hwat': _service_info(services.get('hwat_bridge'), 'HWAT Bridge'),
            'hcv_codec': _service_info(services.get('hcv_codec'), 'HCV Codec'),
            'voice_engine': _service_info(services.get('voice_engine'), 'Voice Engine'),
            'hologram_store': _service_info(services.get('hologram_store'), 'Hologram Store'),
            'web_retriever': _service_info(services.get('web_retriever'), 'Web Retriever'),
            'specializer': _service_info(services.get('specializer'), 'Domain Specializer'),
            'optimized_specializer': _service_info(services.get('optimized_specializer'), 'Optimized Specializer'),
            'wave_poet': _service_info(services.get('wave_poet'), 'Wave Poet'),
            'enterprise_ingestor': _service_info(services.get('enterprise_ingestor'), 'Enterprise Ingestor'),
        })
    
    @app.route('/api/debug/memory', methods=['GET'])
    def api_debug_memory():
        """Usage mémoire (debug)."""
        if not config.get('debug', False) if config else False:
            return jsonify({'error': 'Debug mode not enabled'}), 403
        
        import gc
        import sys
        
        gc.collect()
        objects = gc.get_objects()
        type_counts = {}
        for obj in objects:
            t = type(obj).__name__
            type_counts[t] = type_counts.get(t, 0) + 1
        
        top_types = sorted(type_counts.items(), key=lambda x: -x[1])[:20]
        
        return jsonify({
            'total_objects': len(objects),
            'top_types': top_types,
            'gc_counts': gc.get_count(),
            'gc_thresholds': gc.get_threshold(),
        })


def _service_info(service, name):
    """Info basique sur un service."""
    if service is None:
        return {'name': name, 'status': 'unavailable'}
    
    info = {'name': name, 'status': 'ok', 'type': type(service).__name__}
    
    # Essayer d'appeler .info() ou .stats() si dispo
    for method in ['info', 'stats', 'status']:
        if hasattr(service, method):
            try:
                result = getattr(service, method)()
                if isinstance(result, dict):
                    info.update(result)
                break
            except Exception:
                pass
    
    return info


def _get_uptime():
    """Uptime du processus en secondes."""
    try:
        import time
        import os
        return time.time() - os.path.getmtime('/proc/self/stat') if os.path.exists('/proc/self/stat') else 0
    except Exception:
        return 0