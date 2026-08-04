"""
KA Server — Services Package
=============================
Initialisation et accès aux services métier.
"""

from .harmonic_ai import (
    init_harmonic_ai, get_harmonic_ai, get_brain,
    init_hwat_bridge, get_hwat_bridge, is_hwat_available,
    init_web_retriever, get_web_retriever,
    init_specializer, get_specializer, get_optimized_specializer, is_specializer_available,
    init_hologram_store, get_hologram_store, get_personal_hologram,
    init_wave_poet, get_wave_poet,
    init_enterprise_ingestor, get_enterprise_ingestor, is_enterprise_available,
    holographic_consensus_recall, is_refusal, is_garbage_answer, is_non_subject,
)
from .hcv_codec import init_hcv_codec, compress_image, upscale_image, analyze_storage, get_hcv_status
from .voice_engine import init_voice_engine, get_voice_engine

log = None


def init_services(app) -> dict:
    """
    Initialise tous les services selon la configuration.
    
    Args:
        app: Instance Flask (pour accéder à config)
    
    Returns:
        Dict des services initialisés
    """
    global log
    import logging
    log = logging.getLogger(__name__)
    
    config = getattr(app, 'config', {})
    ka_config = config.get('KA_CONFIG')
    
    services = {
        'config': ka_config.to_dict() if ka_config and hasattr(ka_config, 'to_dict') else {},
    }
    
    log.info("  🔧 Initialisation services...")
    
    # 1. Harmonic AI (core)
    facts = _load_facts(ka_config)
    harmonic_ai = init_harmonic_ai(facts, services['config'])
    services['harmonic_ai'] = harmonic_ai
    services['brain'] = get_brain()
    
    # 2. HWAT Bridge
    hwat_ok = init_hwat_bridge()
    services['hwat_bridge'] = get_hwat_bridge()
    services['hwat_available'] = hwat_ok
    
    # 3. Web Retriever
    web_ok = init_web_retriever()
    services['web_retriever'] = get_web_retriever()
    
    # 4. Specializers
    spec_ok = init_specializer()
    services['specializer'] = get_specializer()
    services['optimized_specializer'] = get_optimized_specializer()
    
    # 5. Hologram Store
    holo_ok = init_hologram_store()
    services['hologram_store'] = get_hologram_store()
    
    # 6. Wave Poet
    poet_ok = init_wave_poet()
    services['wave_poet'] = get_wave_poet()
    
    # 7. Enterprise Ingestor
    ent_ok = init_enterprise_ingestor()
    services['enterprise_ingestor'] = get_enterprise_ingestor()
    
    # 8. HCV Codec
    hcv_status = init_hcv_codec()
    # Créer wrapper pour interface unifiée
    from .hcv_codec import (
        compress_image as _compress,
        upscale_image as _upscale,
        analyze_storage as _analyze,
        get_hcv_status as _status,
    )
    
    class HCVCodecWrapper:
        def compress_image(self, *args, **kwargs): return _compress(*args, **kwargs)
        def upscale_image(self, *args, **kwargs): return _upscale(*args, **kwargs)
        def analyze_storage(self, *args, **kwargs): return _analyze(*args, **kwargs)
        def get_hcv_status(self): return _status()
    
    services['hcv_codec'] = HCVCodecWrapper()
    
    # 9. Voice Engine
    voice = init_voice_engine()
    services['voice_engine'] = voice
    
    log.info("  ✅ Services initialisés")
    return services


def _load_facts(config) -> list:
    """Charge les faits selon la configuration produit."""
    facts = []
    
    # Faits de base par produit
    if config:
        product = config.get('product', 'mobile')
        
        if product == 'mobile':
            # Faits légers pour mobile
            facts = [
                ('KA', 'est', 'assistant_harmonique', 'system', 1.0),
                ('KA', 'utilise', 'holographic_memory', 'system', 1.0),
                ('KA', 'compresse', 'HCV', 'media', 0.9),
            ]
        elif product == 'pc':
            facts = [
                ('KA', 'est', 'assistant_harmonique', 'system', 1.0),
                ('KA', 'utilise', 'holographic_memory', 'system', 1.0),
                ('KA', 'compresse', 'HCV', 'media', 0.9),
                ('HarmonicAI', 'implémente', 'M4_consensus_recall', 'ai', 0.95),
                ('HCV', 'atteint', 'ratio_35x', 'media', 0.9),
            ]
        elif product == 'enterprise':
            facts = [
                ('KA', 'est', 'plateforme_entreprise', 'system', 1.0),
                ('EnterpriseIngestor', 'ingère', 'documents_massifs', 'enterprise', 0.95),
                ('HologramStore', 'gère', 'hologrammes_spécialisés', 'enterprise', 0.9),
            ]
    
    # Essayer charger depuis fichier si dispo
    try:
        import json
        from pathlib import Path
        facts_path = Path(__file__).resolve().parent.parent.parent / 'hologram_facts.json'
        if facts_path.exists():
            with open(facts_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    facts.extend([tuple(f) for f in loaded])
    except Exception:
        pass
    
    return facts


__all__ = [
    'init_services',
    'init_harmonic_ai', 'get_harmonic_ai', 'get_brain',
    'init_hwat_bridge', 'get_hwat_bridge', 'is_hwat_available',
    'init_web_retriever', 'get_web_retriever',
    'init_specializer', 'get_specializer', 'get_optimized_specializer', 'is_specializer_available',
    'init_hologram_store', 'get_hologram_store', 'get_personal_hologram',
    'init_wave_poet', 'get_wave_poet',
    'init_enterprise_ingestor', 'get_enterprise_ingestor', 'is_enterprise_available',
    'init_hcv_codec', 'compress_image', 'upscale_image', 'analyze_storage', 'get_hcv_status',
    'init_voice_engine', 'get_voice_engine',
    'holographic_consensus_recall', 'is_refusal', 'is_garbage_answer', 'is_non_subject',
]