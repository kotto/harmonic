"""
KA Server — Service Docling Harmonique
======================================
Ingestion structurée inspirée de Docling (IBM) : documents bruts →
Documents Harmoniques (sections hiérarchiques, tables, ordre de lecture,
provenance) → hologrammes spécialisés à faits structurels.

Le rappel est STRUCTUREL : une question remonte la hiérarchie (titre de
section = contexte) et rend les tables complètes — pas des chunks plats.
"""

import logging
import threading
from typing import Dict, List, Optional, Any

log = logging.getLogger(__name__)

_ENGINE = None
_DOCUMENTS: Dict[str, Any] = {}     # domain → DocumentHarmonique (cache mémoire)
_LOCK = threading.Lock()


def init_docling_harmonique() -> bool:
    """Charge le moteur docling_harmonique."""
    global _ENGINE
    try:
        import docling_harmonique as _dh
        _ENGINE = _dh
        log.info("  📄 Docling Harmonique actif (ingestion structurée type Docling)")
        return True
    except Exception as e:
        log.warning(f"  📄 Docling Harmonique non disponible: {e}")
        return False


def get_docling_harmonique():
    return _ENGINE


def is_docling_available() -> bool:
    return _ENGINE is not None


# ── API ────────────────────────────────────────────────────────────────────

def ingest_structured(content: str, format: str = 'markdown', domain: str = 'enterprise',
                      category: str = 'enterprise', source: str = 'doc') -> dict:
    """
    Parse un document structuré → hologramme spécialisé à faits structurels.
    Retourne le rapport (sections, items, faits structurels/tables, hologram_id).
    """
    if _ENGINE is None:
        return {'error': 'Docling Harmonique non disponible', 'code': 'DOCLING_UNAVAILABLE'}
    with _LOCK:
        doc = _ENGINE.parse_document(content, format=format, source=source, name=domain)
        store = _get_store()
        info = _ENGINE.build_hologram(doc, store, domain=domain, category=category)
        _DOCUMENTS[domain] = doc
        info['document'] = doc.to_dict()
        info['success'] = True
        return info


def recall_structured(domain: str, query: str, top_k: int = 3) -> list:
    """Rappel structurel sur le document du domaine (sections complètes)."""
    if _ENGINE is None:
        return []
    doc = _DOCUMENTS.get(domain)
    if doc is None:
        return []
    return _ENGINE.recall_structured(doc, query, top_k=top_k)


def list_documents() -> List[dict]:
    """Liste les domaines ingérés (titre, sections, items, faits)."""
    out = []
    for domain, doc in _DOCUMENTS.items():
        out.append({
            'domain': domain,
            'title': doc.metadata.get('title', ''),
            'language': doc.metadata.get('language', ''),
            'source': doc.metadata.get('source', ''),
            'sections': len(doc.sections),
            'items': len(doc.items),
        })
    return out


def get_document_json(domain: str) -> Optional[str]:
    """Export JSON lossless du DocumentHarmonique (format type Docling)."""
    doc = _DOCUMENTS.get(domain)
    if doc is None:
        return None
    return doc.export_json()


def _get_store():
    """Le HologramStore réel (via le service existant, sans import circulaire)."""
    try:
        from ka_server.services.hologram_store import get_hologram_store
        store = get_hologram_store()
        if store is not None:
            return store
    except Exception:
        pass
    return _NullStore()


class _NullStore:
    """Store factice si le HologramStore n'est pas chargé (mode dégradé)."""
    def create_hologram(self, **kw):
        return None

    def add_facts(self, holo_id, facts):
        return None
