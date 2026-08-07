"""
KA Server — Service Hologram Store
===================================
Wrapper autour de HologramStore avec starter pack pré-population.
"""

import logging
import json
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

log = logging.getLogger(__name__)

_HOLOGRAM_STORE = None
_STARTER_POPULATED = False
_STARTER_LOCK = threading.Lock()


# Pack de démarrage: 10+ hologrammes essentiels
STARTER_HOLOGRAMS = [
    {
        'id': 'medecine_generale',
        'name': 'Médecine Générale',
        'category': 'health',
        'description': 'Connaissances médicales générales: symptômes, diagnostics, traitements, prévention',
        'tags': ['santé', 'médecine', 'diagnostic', 'soins'],
        'facts_sample': [
            ('fièvre', 'est_symptome_de', 'infection', 'health', 0.9),
            ('hypertension', 'se_traite_par', 'antihypertenseurs', 'health', 0.9),
            ('diabète', 'nécessite', 'contrôle_glycémie', 'health', 0.9),
        ]
    },
    {
        'id': 'programmation_python',
        'name': 'Programmation Python',
        'category': 'tech',
        'description': 'Syntaxe, bibliothèques, patterns, debugging, performance Python',
        'tags': ['python', 'développement', 'programmation', 'code'],
        'facts_sample': [
            ('python', 'utilise', 'indentation', 'tech', 1.0),
            ('asyncio', 'gère', 'concurrence', 'tech', 0.9),
            ('pytest', 'teste', 'code_python', 'tech', 0.9),
        ]
    },
    {
        'id': 'droit_francais',
        'name': 'Droit Français',
        'category': 'legal',
        'description': 'Code civil, pénal, travail, administratif, jurisprudence',
        'tags': ['droit', 'juridique', 'légal', 'france'],
        'facts_sample': [
            ('code_civil', 'règle', 'contrats', 'legal', 0.9),
            ('prudhommes', 'jugent', 'litiges_travail', 'legal', 0.9),
            ('rgpd', 'protège', 'données_personnelles', 'legal', 0.95),
        ]
    },
    {
        'id': 'finance_personnelle',
        'name': 'Finance Personnelle',
        'category': 'finance',
        'description': 'Budget, investissement, épargne, fiscalité, retraite',
        'tags': ['finance', 'argent', 'investissement', 'épargne'],
        'facts_sample': [
            ('livret_a', 'rendement', '3%', 'finance', 0.8),
            ('pea', 'avantage', 'exonération_impôts', 'finance', 0.9),
            ('diversification', 'réduit', 'risque', 'finance', 0.95),
        ]
    },
    {
        'id': 'cuisine_francaise',
        'name': 'Cuisine Française',
        'category': 'lifestyle',
        'description': 'Recettes, techniques, accords mets-vins, gastronomie régionale',
        'tags': ['cuisine', 'recettes', 'gastronomie', 'france'],
        'facts_sample': [
            ('boeuf_bourguignon', 'cuit_dans', 'vin_rouge', 'lifestyle', 0.9),
            ('soufflé', 'nécessite', 'blancs_en_neige', 'lifestyle', 0.9),
            ('fromage', 's\'accorde_avec', 'vin', 'lifestyle', 0.8),
        ]
    },
    {
        'id': 'histoire_france',
        'name': 'Histoire de France',
        'category': 'culture',
        'description': 'Périodes, personnages, événements, dynasties, révolutions',
        'tags': ['histoire', 'france', 'culture', 'général'],
        'facts_sample': [
            ('révolution_française', 'débute', '1789', 'culture', 1.0),
            ('napoléon', 'empereur', '1804', 'culture', 1.0),
            ('jeanne_d\'arc', 'libère', 'orléans', 'culture', 0.95),
        ]
    },
    {
        'id': 'ecologie_environnement',
        'name': 'Écologie & Environnement',
        'category': 'science',
        'description': 'Changement climatique, biodiversité, énergies renouvelables, développement durable',
        'tags': ['écologie', 'environnement', 'climat', 'durable'],
        'facts_sample': [
            ('CO2', 'cause', 'réchauffement', 'science', 0.95),
            ('solaire', 'est', 'renouvelable', 'science', 1.0),
            ('biodiversité', 'mesure', 'santé_écosystème', 'science', 0.9),
        ]
    },
    {
        'id': 'psychologie_base',
        'name': 'Psychologie de Base',
        'category': 'health',
        'description': 'Troubles, thérapies, développement, cognition, comportement',
        'tags': ['psychologie', 'santé_mentale', 'thérapie', 'cerveau'],
        'facts_sample': [
            ('TCC', 'traite', 'anxiété', 'health', 0.9),
            ('dépression', 'symptôme', 'tristesse_persistante', 'health', 0.9),
            ('mémoire', 'types', 'court_long_terme', 'health', 0.8),
        ]
    },
    {
        'id': 'marketing_digital',
        'name': 'Marketing Digital',
        'category': 'business',
        'description': 'SEO, SEA, réseaux sociaux, emailing, analytics, conversion',
        'tags': ['marketing', 'digital', 'business', 'croissance'],
        'facts_sample': [
            ('SEO', 'améliore', 'visibilité', 'business', 0.9),
            ('taux_conversion', 'mesure', 'performance', 'business', 0.9),
            ('retargeting', 'cible', 'visiteurs', 'business', 0.8),
        ]
    },
    {
        'id': 'philosophie_occidentale',
        'name': 'Philosophie Occidentale',
        'category': 'culture',
        'description': 'Auteurs, courants, concepts, éthique, métaphysique, épistémologie',
        'tags': ['philosophie', 'pensée', 'culture', 'sagesse'],
        'facts_sample': [
            ('descartes', 'formule', 'cogito_ergo_sum', 'culture', 1.0),
            ('kant', 'écrit', 'critique_raison_pure', 'culture', 0.9),
            ('existentialisme', 'affirme', 'existence_précède_essence', 'culture', 0.9),
        ]
    },
    {
        'id': 'langue_francaise',
        'name': 'Langue Française',
        'category': 'education',
        'description': 'Grammaire, orthographe, conjugaison, vocabulaire, expressions',
        'tags': ['français', 'langue', 'grammaire', 'orthographe'],
        'facts_sample': [
            ('accord', 'règle', 'sujet_verbe', 'education', 1.0),
            ('subjonctif', 'exprime', 'doute_souhait', 'education', 0.9),
            ('cédille', 'change', 'son_c', 'education', 0.95),
        ]
    },
    {
        'id': 'bricolage_maison',
        'name': 'Bricolage & Maison',
        'category': 'lifestyle',
        'description': 'Outils, réparations, rénovation, plomberie, électricité, déco',
        'tags': ['bricolage', 'maison', 'réparation', 'diy'],
        'facts_sample': [
            ('perceuse', 'perce', 'mur', 'lifestyle', 1.0),
            ('joint_silicone', 'étanchéifie', 'salle_bain', 'lifestyle', 0.9),
            ('disjoncteur', 'protège', 'circuit_électrique', 'lifestyle', 0.95),
        ]
    },
]


def init_hologram_store() -> bool:
    """Initialise le HologramStore avec starter pack."""
    global _HOLOGRAM_STORE, _STARTER_POPULATED
    
    try:
        from hologram_store import HologramStore
        _HOLOGRAM_STORE = HologramStore()
        
        # Pré-peupler si vide
        if not _STARTER_POPULATED:
            _populate_starter_pack()
        
        return True
    except Exception as e:
        log.warning(f"  📦 Hologram Store non disponible: {e}")
        return False


def get_hologram_store():
    return _HOLOGRAM_STORE


def _populate_starter_pack():
    """Pré-peuple le store avec les hologrammes de démarrage."""
    global _STARTER_POPULATED
    
    with _STARTER_LOCK:
        if _STARTER_POPULATED or not _HOLOGRAM_STORE:
            return
        
        try:
            existing = _HOLOGRAM_STORE.list_holograms()
            existing_ids = {h['id'] for h in existing}
            
            for holo_data in STARTER_HOLOGRAMS:
                if holo_data['id'] in existing_ids:
                    continue
                
                # Créer l'hologramme
                _create_starter_hologram(holo_data)
            
            _STARTER_POPULATED = True
            log.info(f"  📦 Starter pack peuplé: {len(STARTER_HOLOGRAMS)} hologrammes")
        except Exception as e:
            log.warning(f"  📦 Échec peuplement starter: {e}")


def _create_starter_hologram(holo_data: dict):
    """Crée un hologramme de base avec faits d'échantillon."""
    try:
        # Utiliser l'API du store si dispo
        if hasattr(_HOLOGRAM_STORE, 'create_hologram'):
            _HOLOGRAM_STORE.create_hologram(
                holo_id=holo_data['id'],
                name=holo_data['name'],
                category=holo_data['category'],
                description=holo_data['description'],
                tags=holo_data['tags'],
            )
        
        # Ajouter faits d'échantillon
        if hasattr(_HOLOGRAM_STORE, 'add_facts'):
            facts = [
                (s, r, o, sec, score)
                for s, r, o, sec, score in holo_data['facts_sample']
            ]
            _HOLOGRAM_STORE.add_facts(holo_data['id'], facts)
        
        log.info(f"  📦 Créé: {holo_data['id']} ({holo_data['category']})")
    except Exception as e:
        log.warning(f"  📦 Échec création {holo_data['id']}: {e}")


# ── API simplifiée pour compatibilité ───────────────────────────────────────

def list_holograms() -> List[Dict]:
    """Liste tous les hologrammes."""
    if _HOLOGRAM_STORE:
        return _HOLOGRAM_STORE.list_holograms()
    return []


def get_hologram(holo_id: str) -> Optional[Dict]:
    """Récupère un hologramme."""
    if _HOLOGRAM_STORE and hasattr(_HOLOGRAM_STORE, 'get_hologram'):
        return _HOLOGRAM_STORE.get_hologram(holo_id)
    return None


def download_hologram(holo_id: str, format: str = 'wave') -> Optional[bytes]:
    """Télécharge un hologramme."""
    if _HOLOGRAM_STORE and hasattr(_HOLOGRAM_STORE, 'download'):
        return _HOLOGRAM_STORE.download(holo_id, format=format)
    return None


def recall_hologram(holo_id: str, query: str, top_k: int = 10) -> List[tuple]:
    """Rappel holographique."""
    if _HOLOGRAM_STORE and hasattr(_HOLOGRAM_STORE, 'recall'):
        return _HOLOGRAM_STORE.recall(holo_id, query, top_k=top_k)
    return []


def has_wave_format(holo_id: str) -> bool:
    """Vérifie format wave."""
    if _HOLOGRAM_STORE and hasattr(_HOLOGRAM_STORE, 'has_wave_format'):
        return _HOLOGRAM_STORE.has_wave_format(holo_id)
    return False


# Pour compatibilité avec l'ancien code
HologramStore = None
try:
    from hologram_store import HologramStore as _HS
    HologramStore = _HS
except ImportError:
    pass