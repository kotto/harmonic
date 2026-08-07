"""
KA Server — Middleware Métriques & Logging
===========================================
Métriques requêtes, latence, rate limiting, logging structuré.
"""

import time
import logging
import os
from collections import defaultdict
from flask import request, g

log = logging.getLogger(__name__)

# ── Stockage métriques en mémoire ────────────────────────────────────────────
_METRICS = {
    'requests': defaultdict(int),       # endpoint → count
    'errors': defaultdict(int),         # endpoint → error count
    'latency_sum': defaultdict(float),  # endpoint → total latency ms
    'latency_count': defaultdict(int),  # endpoint → count for avg
    'harmonic_count': 0,
    'llm_count': 0,
    'last_requests': [],                # (endpoint, latency_ms, status, timestamp)
    'hourly': defaultdict(int),         # heure (epoch//3600) → count (séries temporelles)
    'daily': defaultdict(int),          # jour (epoch//86400) → count
    'hourly_errors': defaultdict(int),  # heure → erreurs
}
_MAX_LAST_REQUESTS = 1000

# ── Rate Limiting ────────────────────────────────────────────────────────────
_RATE_LIMIT_WINDOW = 60     # secondes
_RATE_LIMIT_MAX = 30        # requêtes max par fenêtre
_rate_limit_store = defaultdict(list)  # IP → [timestamps]
# Proxy de confiance (optionnel) : si défini, X-Forwarded-For n'est lu que
# lorsque le pair direct est ce proxy. Sinon on utilise request.remote_addr
# (empêche le spoofing de l'en-tête pour contourner le rate limit).
_TRUSTED_PROXY = os.environ.get('KA_TRUSTED_PROXY', '').strip()
_last_purged = [0.0]  # horodatage de la dernière purge des IP inactives


def _check_rate_limit(ip: str, max_requests: int = None, window: int = None) -> bool:
    """Retourne True si la limite est dépassée."""
    max_req = max_requests or _RATE_LIMIT_MAX
    win = window or _RATE_LIMIT_WINDOW
    now = time.time()
    window_start = now - win
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if t > window_start]
    _rate_limit_store[ip].append(now)

    # Purge des IP inactives pour éviter la croissance mémoire illimitée
    if len(_rate_limit_store) > 1024 and _last_purged[0] + 60 < now:
        _last_purged[0] = now
        for stale_ip in [k for k, v in _rate_limit_store.items() if not v or max(v) <= window_start]:
            del _rate_limit_store[stale_ip]

    return len(_rate_limit_store[ip]) > max_req


def _get_client_ip() -> str:
    """Récupère l'IP client (X-Forwarded-For uniquement derrière un proxy de confiance)."""
    if _TRUSTED_PROXY and request.remote_addr == _TRUSTED_PROXY:
        return request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()
    return request.remote_addr or 'unknown'


def register_metrics_middleware(app):
    """Enregistre les middleware de métriques et logging."""
    
    @app.before_request
    def _before_request():
        g._start_time = time.time()
        g._client_ip = _get_client_ip()
        
        # Rate limiting global (configurable par produit)
        if hasattr(app, 'ka_services') and app.ka_services.get('config'):
            config = app.ka_services['config']
            if config.get('rate_limit_enabled', True):
                max_req = config.get('rate_limit_max', 30)
                if _check_rate_limit(g._client_ip, max_requests=max_req):
                    from flask import jsonify
                    return jsonify({
                        'error': 'Trop de requêtes. Réessayez dans une minute.',
                        'retry_after_s': _RATE_LIMIT_WINDOW
                    }), 429

    @app.after_request
    def _after_request(response):
        endpoint = request.endpoint or 'unknown'
        latency_ms = (time.time() - getattr(g, '_start_time', time.time())) * 1000
        
        _METRICS['requests'][endpoint] += 1
        _METRICS['latency_sum'][endpoint] += latency_ms
        _METRICS['latency_count'][endpoint] += 1
        
        if response.status_code >= 400:
            _METRICS['errors'][endpoint] += 1
        
        _METRICS['last_requests'].append({
            'endpoint': endpoint,
            'latency_ms': round(latency_ms, 1),
            'status': response.status_code,
            'time': time.time(),
            'ip': getattr(g, '_client_ip', 'unknown')
        })
        if len(_METRICS['last_requests']) > _MAX_LAST_REQUESTS:
            _METRICS['last_requests'] = _METRICS['last_requests'][-_MAX_LAST_REQUESTS:]
        
        # Séries temporelles (heures et jours depuis le démarrage)
        _METRICS['hourly'][int(time.time() // 3600)] += 1
        _METRICS['daily'][int(time.time() // 86400)] += 1
        if response.status_code >= 400:
            _METRICS['hourly_errors'][int(time.time() // 3600)] += 1
        
        log.info(f"{request.method} {request.path} → {response.status_code} ({latency_ms:.0f}ms)")
        return response
    
    # Exposer métriques pour endpoint /api/metrics
    app.ka_metrics = _METRICS
    app.ka_rate_limit_store = _rate_limit_store


def get_metrics() -> dict:
    """Retourne les métriques agrégées."""
    avg_latency = {}
    for ep in _METRICS['latency_sum']:
        count = _METRICS['latency_count'][ep]
        if count > 0:
            avg_latency[ep] = round(_METRICS['latency_sum'][ep] / count, 1)
    
    return {
        'requests_total': sum(_METRICS['requests'].values()),
        'requests_by_endpoint': dict(_METRICS['requests']),
        'errors_by_endpoint': dict(_METRICS['errors']),
        'avg_latency_ms': avg_latency,
        'harmonic_count': _METRICS['harmonic_count'],
        'llm_count': _METRICS['llm_count'],
        'last_requests': _METRICS['last_requests'][-20:],
        'rate_limit_tracked_ips': len(_rate_limit_store),
    }


def increment_harmonic():
    _METRICS['harmonic_count'] += 1


def increment_llm():
    _METRICS['llm_count'] += 1

def get_usage_timeseries(days: int = 7, hours: int = 24) -> dict:
    """
    Séries temporelles d'usage pour les graphiques de la console :
      • hourly  : appels par heure (et erreurs) sur les `hours` dernières heures
      • daily   : appels par jour sur les `days` derniers jours
      • by_endpoint : répartition par endpoint (top 10)
    """
    import datetime as _dt
    now = time.time()

    def _fill(bucket_key, buckets, span):
        out = []
        for k in range(buckets - 1, -1, -1):
            ts = int(now // span) - k
            out.append({
                'label': _dt.datetime.fromtimestamp(ts * span).strftime(
                    '%H:%M' if span == 3600 else '%d/%m'),
                'count': _METRICS['hourly'].get(ts, 0) if span == 3600 else _METRICS['daily'].get(ts, 0),
                'errors': _METRICS['hourly_errors'].get(ts, 0) if span == 3600 else 0,
            })
        return out

    # Répartition par endpoint (depuis les requêtes récentes + compteurs)
    by_ep = sorted(_METRICS['requests'].items(), key=lambda x: -x[1])[:10]

    return {
        'hourly': _fill('hourly', hours, 3600),
        'daily': _fill('daily', days, 86400),
        'by_endpoint': [{'endpoint': ep, 'count': c} for ep, c in by_ep],
        'avg_latency_ms': round(
            sum(_METRICS['latency_sum'].values()) / max(1, sum(_METRICS['latency_count'].values())), 1),
        'uptime_hours': round((now - _METRICS.get('_started', now)) / 3600, 1) if _METRICS.get('_started') else None,
    }
