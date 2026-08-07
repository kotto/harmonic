"""
KA Server — Service Web Retriever
==================================
Wrapper autour de WebRetriever pour recherche web.
"""

import logging
from typing import Optional, List, Dict, Any

log = logging.getLogger(__name__)

_WEB_RETRIEVER = None


def init_web_retriever() -> bool:
    """Initialise le Web Retriever."""
    global _WEB_RETRIEVER
    
    try:
        from web_retriever import WebRetriever
        _WEB_RETRIEVER = WebRetriever()
        log.info("  🌐 Web Retriever initialisé")
        return True
    except Exception as e:
        log.warning(f"  🌐 Web Retriever non disponible: {e}")
        return False


def get_web_retriever():
    return _WEB_RETRIEVER


def is_web_retriever_available() -> bool:
    return _WEB_RETRIEVER is not None


# ── API unifiée ─────────────────────────────────────────────────────────────

def search(query: str, max_results: int = 10, source: str = 'auto') -> List[Dict]:
    """Recherche web unifiée."""
    if not _WEB_RETRIEVER:
        return []
    
    try:
        return _WEB_RETRIEVER.search(query, max_results=max_results)
    except Exception as e:
        log.error(f"Web search failed: {e}")
        return []


def fetch(url: str) -> Optional[Dict]:
    """Récupère le contenu d'une URL."""
    if not _WEB_RETRIEVER:
        return None
    
    try:
        if hasattr(_WEB_RETRIEVER, 'fetch'):
            return _WEB_RETRIEVER.fetch(url)
    except Exception as e:
        log.error(f"Web fetch failed: {e}")
    return None


def search_and_fetch(query: str, max_results: int = 5) -> List[Dict]:
    """Recherche et récupère le contenu complet."""
    results = search(query, max_results)
    
    enriched = []
    for r in results:
        url = r.get('url')
        if url:
            content = fetch(url)
            if content:
                r['full_content'] = content.get('content', '')
        enriched.append(r)
    
    return enriched


# ── Classe wrapper pour compatibilité ───────────────────────────────────────

class WebRetrieverWrapper:
    """Wrapper pour compatibilité routes."""
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        return search(query, max_results)
    
    def fetch(self, url: str) -> Optional[Dict]:
        return fetch(url)
    
    def search_and_fetch(self, query: str, max_results: int = 5) -> List[Dict]:
        return search_and_fetch(query, max_results)
    
    def is_available(self) -> bool:
        return is_web_retriever_available()


def get_web_retriever_wrapper() -> WebRetrieverWrapper:
    return WebRetrieverWrapper()