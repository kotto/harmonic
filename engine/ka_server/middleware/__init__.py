"""
KA Server — Middleware Package
===============================
"""

from .metrics import register_metrics_middleware, get_metrics, increment_harmonic, increment_llm
from .auth import register_auth_middleware, require_auth, require_api_key, add_api_key, remove_api_key, validate_api_key, get_audit_log

__all__ = [
    'register_metrics_middleware',
    'get_metrics',
    'increment_harmonic',
    'increment_llm',
    'register_auth_middleware',
    'require_auth',
    'require_api_key',
    'add_api_key',
    'remove_api_key',
    'validate_api_key',
    'get_audit_log',
]