"""
KA Server — Service Harmonic AI
================================
Wrapper autour de HarmonicAI, HarmonicBrain, et composants associés.
Gestion du cycle de vie, cache, et interface unifiée.
"""

import sys
import os
import logging
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

log = logging.getLogger(__name__)

# État global des services
_harmonic_ai = None
_brain = None
_hwat_bridge = None
_web_retriever = None
_specializer = None
_optimized_specializer = None
_hologram_store = None
_personal_holograms = {}
_wave_poet = None
_enterprise_ingestor = None
_gate_encoder = None
_HWAT_AVAILABLE = False
_SPECIALIZER_AVAILABLE = False
_ENTERPRISE_AVAILABLE = False
_HAS_PERSONAL = False


def init_harmonic_ai(facts: List[Tuple], config: dict = None) -> 'HarmonicAI':
    """Initialise l'IA Harmonique avec les faits fournis."""
    global _harmonic_ai, _brain
    
    try:
        from harmonic_ai import HarmonicAI
        
        fast_mode = config.get('ai_fast_mode', True) if config else True
        use_memory = config.get('use_memory', True) if config else True
        
        _harmonic_ai = HarmonicAI(
            use_memory=use_memory,
            enable_bootstrapper=False,
            fast_mode=fast_mode
        )
        
        # Injecter les faits si fournis
        if facts and hasattr(_harmonic_ai, '_brain') and _harmonic_ai._brain:
            _brain = _harmonic_ai._brain
            # Les faits sont déjà chargés dans HarmonicAI via son init
        
        log.info(f"  🧠 HarmonicAI initialisé (fast_mode={fast_mode})")
        return _harmonic_ai
        
    except Exception as e:
        log.error(f"  ❌ Erreur initialisation HarmonicAI: {e}")
        # Fallback minimal
        from harmonic_brain import HarmonicBrain
        _brain = HarmonicBrain(facts[:100] if facts else [], dim=64, use_holographic=False)
        return None


def get_harmonic_ai():
    """Retourne l'instance HarmonicAI."""
    return _harmonic_ai


def get_brain():
    """Retourne l'instance HarmonicBrain."""
    global _brain
    if _brain is None and _harmonic_ai:
        _brain = _harmonic_ai._get_brain() if hasattr(_harmonic_ai, '_get_brain') else None
    return _brain


def init_hwat_bridge() -> bool:
    """Initialise le bridge HWAT (nouveau modèle harmonique)."""
    global _hwat_bridge, _HWAT_AVAILABLE
    
    try:
        from hwat_bridge import HwatBridge
        _hwat_bridge = HwatBridge(auto_load=True)
        _HWAT_AVAILABLE = _hwat_bridge.is_available
        if _HWAT_AVAILABLE:
            info = _hwat_bridge.info()
            log.info(f"  🌊 HWAT connecté: {info['params']:,} params, dim={info['dim']}, blocs={info['blocks']}")
        return _HWAT_AVAILABLE
    except Exception as e:
        log.warning(f"  🌊 HWAT non disponible: {e}")
        _HWAT_AVAILABLE = False
        return False


def get_hwat_bridge():
    return _hwat_bridge if _HWAT_AVAILABLE else None


def is_hwat_available() -> bool:
    return _HWAT_AVAILABLE


def init_web_retriever() -> bool:
    """Initialise le Web Retriever."""
    global _web_retriever
    
    try:
        from web_retriever import WebRetriever
        _web_retriever = WebRetriever()
        log.info("  🌐 Web Retriever connecté")
        return True
    except Exception as e:
        log.warning(f"  🌐 Web Retriever non disponible: {e}")
        return False


def get_web_retriever():
    return _web_retriever


def init_specializer() -> bool:
    """Initialise les spécialiseurs de domaine."""
    global _specializer, _optimized_specializer, _SPECIALIZER_AVAILABLE
    
    brain = get_brain()
    web_retriever = get_web_retriever()
    
    try:
        from domain_specializer import DomainSpecializer, detect_specialize_intent, load_user_kbs_for_brain
        _specializer = DomainSpecializer(brain=brain, web_retriever=web_retriever)
        _SPECIALIZER_AVAILABLE = True
        log.info("  🎯 Domain Specializer actif")
    except Exception as e:
        log.warning(f"  🎯 Domain Specializer non disponible: {e}")
    
    try:
        from specialize_optimized import OptimizedSpecializer
        _optimized_specializer = OptimizedSpecializer(web_retriever=web_retriever, brain=brain)
        log.info("  🎯 Optimized Specializer actif")
    except Exception as e:
        log.warning(f"  🎯 Optimized Specializer non disponible: {e}")
    
    return _SPECIALIZER_AVAILABLE


def get_specializer():
    return _specializer


def get_optimized_specializer():
    return _optimized_specializer


def is_specializer_available() -> bool:
    return _SPECIALIZER_AVAILABLE


def init_hologram_store() -> bool:
    """Initialise le Hologram Store."""
    global _hologram_store, _gate_encoder, _HAS_PERSONAL
    
    try:
        from hologram_store import HologramStore
        _hologram_store = HologramStore()
        n_holo = len(_hologram_store.list_holograms())
        log.info(f"  📦 Hologram Store actif ({n_holo} hologrammes)")
    except Exception as e:
        log.warning(f"  📦 Hologram Store non disponible: {e}")
    
    try:
        from personal_hologram import PersonalHologram
        _HAS_PERSONAL = True
        log.info("  🧠 PersonalHologram disponible")
    except ImportError:
        _HAS_PERSONAL = False
    
    return _hologram_store is not None


def get_hologram_store():
    return _hologram_store


def get_personal_hologram(user_id: str):
    """Récupère ou crée un PersonalHologram pour un utilisateur."""
    global _personal_holograms
    if not _HAS_PERSONAL:
        return None
    if user_id not in _personal_holograms:
        try:
            from personal_hologram import PersonalHologram
            _personal_holograms[user_id] = PersonalHologram(user_id)
        except Exception:
            return None
    return _personal_holograms[user_id]


def init_wave_poet() -> bool:
    """Initialise le Wave Poet."""
    global _wave_poet
    
    try:
        from wave_poetry import WavePoet
        _wave_poet = WavePoet()
        log.info(f"  🌊 Wave Poet actif ({_wave_poet.stats()['poetic_vocabulary']} mots)")
        return True
    except Exception as e:
        log.warning(f"  🌊 Wave Poet non disponible: {e}")
        return False


def get_wave_poet():
    return _wave_poet


def init_enterprise_ingestor() -> bool:
    """Initialise l'Enterprise Ingestor."""
    global _enterprise_ingestor, _ENTERPRISE_AVAILABLE
    
    brain = get_brain()
    if not brain:
        return False
    
    try:
        from enterprise_ingest import EnterpriseIngestor
        _enterprise_ingestor = EnterpriseIngestor(brain=brain)
        _ENTERPRISE_AVAILABLE = True
        log.info("  🏢 Enterprise Ingestor actif")
        return True
    except Exception as e:
        log.warning(f"  🏢 Enterprise Ingestor non disponible: {e}")
        return False


def get_enterprise_ingestor():
    return _enterprise_ingestor


def is_enterprise_available() -> bool:
    return _ENTERPRISE_AVAILABLE


def get_gate_encoder():
    """Encodeur paresseux pour le gate de résonance."""
    global _gate_encoder
    if _gate_encoder is None:
        try:
            from holographic_encoder import HolographicEncoder
            _gate_encoder = HolographicEncoder()
        except Exception:
            pass
    return _gate_encoder


# ── Helpers pour le rappel holographique M4 ─────────────────────────────────

import re
import math

_STOPWORDS = set()
_TRANSVERSAL = {
    'symptomes', 'symptome', 'signes', 'signe', 'causes', 'cause',
    'provoque', 'traitement', 'traite', 'traiter', 'transmis', 'transmet',
    'transmission', 'prevention', 'prevenir', 'diagnostic',
    'diagnostique', 'histoire', 'types', 'type', 'role', 'mecanisme',
    'fonctionne', 'frequence', 'repandu', 'repandue', 'eviter', 'evite',
    'protege', 'proteger', 'effets', 'effet', 'douleurs', 'douleur',
    'fievre', 'maladie', 'maladies', 'comment', 'pourquoi', 'quand',
    'quel', 'quelle', 'quels', 'quelles', 'combien', 'definition',
    'definir', 'explique', 'expliquer', 'signifie', 'difference',
    'differences', 'exemple', 'exemples', 'consequence', 'consequences',
    'complication', 'complications',
}

def _init_stopwords():
    global _STOPWORDS
    if not _STOPWORDS:
        try:
            from holographic_encoder import _STOPWORDS as HW_STOPWORDS
            _STOPWORDS = set(HW_STOPWORDS)
        except Exception:
            _STOPWORDS = {'est', 'et', 'ou', 'de', 'la', 'le', 'les', 'un', 'une', 'des', 'du', 'au', 'aux', 'que', 'qui', 'ce', 'se', 'sa', 'son', 'sur', 'pour', 'dans', 'avec', 'par', 'sans', 'sous', 'vers', 'chez', 'lors', 'puis', 'donc', 'car', 'mais', 'ou', 'ni', 'or'}

def holographic_consensus_recall(message: str, top_domains: int = 3, top_k: int = 5, w: tuple = (0.35, 0.20, 0.20, 0.15, 0.10)):
    """
    Rappel holographique M4 : score sémantique multi-signaux + consensus.
    Retourne (consensus_facts, best_holo_id) ou ([], None).
    """
    _init_stopwords()
    
    store = get_hologram_store()
    if not store:
        return [], None
    
    holos = store.list_holograms()
    query_words = set(re.findall(r"[a-zàâäéèêëîïôöùûüç]{3,}", message.lower()))
    query_content = query_words - _STOPWORDS
    query_specific = query_content - _TRANSVERSAL
    query_hit_words = query_specific if query_specific else query_content
    n_facts_by_holo = {}
    
    domain_results = []
    for h in holos:
        holo_id = h['id']
        if not store.has_wave_format(holo_id):
            continue
        n_facts_by_holo[holo_id] = int(h.get('facts_count', 1))
        try:
            recalled = store.recall(holo_id, message, top_k=top_k)
        except Exception:
            continue
        if not recalled:
            continue
        
        scores = [r[4] for r in recalled]
        top_score = max(scores)
        mean_score = sum(scores) / len(scores)
        coverage = sum(1 for s in scores if s > 0.02) / max(1, len(scores))
        
        fact_text = ' '.join(f"{r[0]} {r[1]} {r[2]}" for r in recalled).lower()
        fact_words = set(re.findall(r"[a-zàâäéèêëîïôöùûüç]{3,}", fact_text))
        sector_hit = (len(query_hit_words & fact_words) / max(1, len(query_hit_words)))
        
        mass = math.log1p(h.get('facts_count', 1)) / math.log1p(50000)
        
        sem = (w[0] * top_score + w[1] * mean_score + w[2] * coverage
               + w[3] * sector_hit + w[4] * mass)
        
        domain_results.append((holo_id, sem, recalled))
        log.info(f"  🌊 {holo_id}: sem={sem:.4f} (top={top_score:.3f} mean={mean_score:.3f} cov={coverage:.2f} hit={sector_hit:.2f} mass={mass:.2f})")
    
    if not domain_results:
        return [], None
    
    domain_results.sort(key=lambda x: -x[1])
    selected = domain_results[:top_domains]
    
    # Gate de cohérence (zero-hallucination)
    best_sem = selected[0][1]
    best_recall = selected[0][2]
    best_top = max(r[4] for r in best_recall)
    fact_text = ' '.join(f"{r[0]} {r[1]} {r[2]}" for r in best_recall).lower()
    fact_words = set(re.findall(r"[a-zàâäéèêëîïôöùûüç]{3,}", fact_text))
    best_hit = len(query_hit_words & fact_words) / max(1, len(query_hit_words))
    
    # Top spécifique pour gate
    if query_specific:
        try:
            encoder = get_gate_encoder()
            if encoder:
                top_fact = best_recall[0]
                ft = f"{top_fact[0]} {top_fact[1]} {top_fact[2]}"
                ftok = [w for w in re.findall(r"[a-zàâäéèêëîïôöùûüç]{3,}", ft.lower()) if w not in _STOPWORDS]
                best_spec = 0.0
                for sp in query_specific:
                    v_sp = encoder.encode_word(sp)
                    for t in ftok:
                        s_ = float(np.real(np.dot(v_sp, np.conj(encoder.encode_word(t)))))
                        if s_ > best_spec:
                            best_spec = s_
                best_top = best_spec
        except Exception:
            pass
    
    n_best = n_facts_by_holo.get(selected[0][0], 1)
    w_q = max(1, len(query_hit_words))
    noise_floor = math.sqrt(2.0 * math.log(3.0 * n_best * w_q) / 512.0) + 0.10
    gate_threshold = max(0.25, noise_floor)
    
    if best_hit == 0.0 and best_top < gate_threshold:
        log.info(f"  🌊 Consensus rejeté (cohérence insuffisante: hit={best_hit:.2f}, top={best_top:.3f} < {gate_threshold:.3f})")
        return [], None
    
    log.info(f"  🌊 Domaines retenus: {[(d, round(s, 3)) for d, s, _ in selected]}")
    
    # Consensus : fusionner les faits, renforcer ceux qui convergent
    fact_votes = {}
    fact_meta = {}
    for holo_id, sem, recalled in selected:
        for s, r, o, sec, score in recalled:
            key = (s, r, o)
            fact_votes.setdefault(key, []).append(score)
            if key not in fact_meta or sem > fact_meta[key][1]:
                fact_meta[key] = (sec, sem)
    
    consensus = []
    for (s, r, o), votes in fact_votes.items():
        sec, dom_sem = fact_meta[(s, r, o)]
        boost = 1.0 + 0.5 * (len(votes) - 1)
        final = max(votes) * boost * (1.0 + dom_sem)
        consensus.append((s, r, o, sec, final))
    
    consensus.sort(key=lambda x: -x[4])
    log.info(f"🌊 Consensus: {len(consensus)} faits ({sum(1 for v in fact_votes.values() if len(v) > 1)} convergents)")
    
    best_holo_id = selected[0][0] if selected else None
    return consensus[:top_k], best_holo_id


def is_refusal(text: str) -> bool:
    """Vrai si la réponse est un refus calibré (anti-hallucination)."""
    t = (text or '').lower()
    return any(m in t for m in [
        'je ne sais pas', "je n'ai pas assez", "je n'ai pas encore",
        'je ne connais pas', "je n'ai pas la réponse",
        "je n'ai pas d'éléments", "je n'ai pas d'information",
        'je ne trouve pas cette information', 'je ne peux pas répondre',
        'je n ai pas encore assez de connaissances',
        'je ne sais pas encore', 'pas encore de connaissance',
    ])


_NON_SUBJECT_HINTS = ['raconte', 'chante', 'dessine', 'ecris', 'ecrit',
                      'fais', 'fait', 'blague', 'poeme', 'poesie', 'chanson',
                      'histoire drôle', 'jeu', 'devinette', 'salutation',
                      'merci', 'bonjour', 'au revoir', 'tu vas bien',
                      'comment ca va', 'qui es tu', 'que sais tu faire']


def is_garbage_answer(question: str, response: str) -> bool:
    """Réponse du cerveau SANS lien avec la question (hallucination)."""
    q_words = set(re.findall(r'[a-zàâäéèêëîïôöùûüç]{4,}', question.lower()))
    try:
        from context_wave import _NON_SUBJECT
        q_words -= _NON_SUBJECT
    except Exception:
        pass
    if not q_words:
        return False
    resp = response.lower()
    first = resp.find('.')
    body = resp[first:] if 0 < first < len(resp) - 20 else resp
    return not any(w in body for w in q_words)


def is_non_subject(sujet: str) -> bool:
    s = sujet.lower()
    if len(s) < 3:
        return True
    return any(h in s for h in _NON_SUBJECT_HINTS)


_SPECIALIZE_RE = re.compile(
    r'^(?:sp[eé]cialise[- ]moi|sp[eé]cialise|cr[ée]e[- ]moi un hologramme|'
    r'cr[ée]e un hologramme|deviens expert)\s+(?:sur|en|de|pour|dans)\s+(.+)',
    re.IGNORECASE)