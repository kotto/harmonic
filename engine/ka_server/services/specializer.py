"""
KA Server — Service Specializer (Domain Specialization)
========================================================
Wrapper autour de DomainSpecializer et OptimizedSpecializer.
"""

import logging
from typing import Optional, List, Dict, Any

log = logging.getLogger(__name__)

_DOMAIN_SPECIALIZER = None
_OPTIMIZED_SPECIALIZER = None


def init_specializer(brain=None, web_retriever=None) -> bool:
    """Initialise les spécialiseurs."""
    global _DOMAIN_SPECIALIZER, _OPTIMIZED_SPECIALIZER
    
    ok = False
    
    # DomainSpecializer (standard)
    try:
        from domain_specializer import DomainSpecializer
        _DOMAIN_SPECIALIZER = DomainSpecializer(brain=brain, web_retriever=web_retriever)
        log.info("  🎯 Domain Specializer initialisé")
        ok = True
    except Exception as e:
        log.warning(f"  🎯 Domain Specializer non disponible: {e}")
    
    # OptimizedSpecializer (v2, plus performant)
    try:
        from specialize_optimized import OptimizedSpecializer
        _OPTIMIZED_SPECIALIZER = OptimizedSpecializer(web_retriever=web_retriever, brain=brain)
        log.info("  🎯 Optimized Specializer initialisé")
        ok = True
    except Exception as e:
        log.warning(f"  🎯 Optimized Specializer non disponible: {e}")
    
    return ok


def get_specializer():
    return _DOMAIN_SPECIALIZER


def get_optimized_specializer():
    return _OPTIMIZED_SPECIALIZER


def is_specializer_available() -> bool:
    return _DOMAIN_SPECIALIZER is not None or _OPTIMIZED_SPECIALIZER is not None


# ── API unifiée ─────────────────────────────────────────────────────────────

def specialize(domain: str, user_kbs: List = None, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Spécialise un domaine (API unifiée).
    
    Args:
        domain: Nom du domaine (ex: 'cardiologie', 'python', 'droit_travail')
        user_kbs: Liste de KBs utilisateur à intégrer
        force_refresh: Forcer la recréation
    
    Returns:
        Dict avec résultat
    """
    # Essayer OptimizedSpecializer en premier
    if _OPTIMIZED_SPECIALIZER:
        try:
            return _OPTIMIZED_SPECIALIZER.specialize(domain, user_kbs=user_kbs)
        except Exception as e:
            log.warning(f"Optimized specialize failed: {e}")
    
    # Fallback DomainSpecializer
    if _DOMAIN_SPECIALIZER:
        try:
            return _DOMAIN_SPECIALIZER.specialize(domain, user_kbs=user_kbs)
        except Exception as e:
            log.warning(f"Standard specialize failed: {e}")
    
    return {
        'success': False,
        'domain': domain,
        'error': 'Aucun spécialiseur disponible',
    }


def detect_specialize_intent(message: str) -> Optional[str]:
    """Détecte si un message demande une spécialisation."""
    try:
        from domain_specializer import detect_specialize_intent
        return detect_specialize_intent(message)
    except Exception:
        pass
    
    # Fallback regex
    import re
    patterns = [
        r'sp[eé]cialise[- ]moi\s+(?:sur|en|de|pour)\s+(.+)',
        r'cr[ée]e[- ]moi un hologramme\s+(?:sur|de)\s+(.+)',
        r'deviens expert\s+(?:sur|en|de)\s+(.+)',
        r'apprends[- ]moi\s+(.+)',
    ]
    for pat in patterns:
        match = re.search(pat, message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def load_user_kbs_for_brain(brain, user_id: str) -> List:
    """Charge les KBs utilisateur pour le brain."""
    try:
        from domain_specializer import load_user_kbs_for_brain
        return load_user_kbs_for_brain(brain, user_id)
    except Exception:
        return []


# ── Classe wrapper pour compatibilité ───────────────────────────────────────

class SpecializerWrapper:
    """Wrapper unifié pour les routes."""
    
    def specialize(self, domain: str, user_kbs: List = None, force_refresh: bool = False) -> Dict:
        return specialize(domain, user_kbs, force_refresh)
    
    def detect_intent(self, message: str) -> Optional[str]:
        return detect_specialize_intent(message)
    
    def is_available(self) -> bool:
        return is_specializer_available()


def get_specializer_wrapper() -> SpecializerWrapper:
    return SpecializerWrapper()