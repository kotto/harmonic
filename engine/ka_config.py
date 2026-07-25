"""
KA Config — Système de Configuration 3 Produits
=================================================

Définit les configurations distinctes pour :
  📱 KA Mobile  — Téléphone Harmonique (port 8765)
  💻 KA PC      — Desktop/Workstation (port 8766)
  🏢 KA Enterprise — Multi-tenant/Business (port 8767)

Chaque produit partage le même noyau (HarmonicEngine, AgentCore, VoiceEngine)
mais active des fonctionnalités, outils, écrans, et optimisations spécifiques.

Architecture :
  ka_config.py (ce fichier)     → définit les 3 profils
  ka_launcher.py                → démarre le bon produit selon --product
  ka_server.py                  → lit la config active et adapte les endpoints
  ka_redesign/                  → UI adaptée selon le produit actif

Usage :
  python ka_launcher.py --product mobile     # port 8765
  python ka_launcher.py --product pc         # port 8766
  python ka_launcher.py --product enterprise # port 8767

Auteur : Équipe HarmoniqLLM
Date   : 2026-07-25
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE DE BASE (commun aux 3 produits)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class KAProductConfig:
    """Configuration d'un produit KA."""
    
    # ── Identité ──
    product: str = 'mobile'              # mobile | pc | enterprise
    name: str = 'KA Mobile'
    name_short: str = 'KA'
    tagline: str = 'Votre compagnon harmonique'
    icon: str = '📱'
    version: str = '4.0'
    
    # ── Serveur ──
    port: int = 8765
    host: str = '0.0.0.0'
    debug: bool = False
    threaded: bool = True
    
    # ── UI ──
    theme: str = 'dark'                  # dark | light | auto
    ui_layout: str = 'mobile'            # mobile | desktop | admin
    pwa_enabled: bool = True
    offline_support: bool = True
    animations: bool = True              # désactivé sur mobile lent
    font_scale: float = 1.0
    
    # ── Écrans actifs ──
    screens: List[str] = field(default_factory=lambda: [
        'home', 'chat'
    ])
    default_screen: str = 'home'
    
    # ── Fonctionnalités ──
    features: Dict[str, bool] = field(default_factory=lambda: {
        'chat': True,
        'voice_tts': True,
        'voice_stt': False,
        'agent': True,
        'code_gen': False,
        'deep_research': False,
        'file_management': False,
        'creative_media': False,
        'health': False,
        'enterprise': False,
        'multi_tenant': False,
        'knowledge_store': True,
        'hologram_store': True,
        'page_forge': True,
        'jlens': True,
        'contacts': True,
        'calls': True,
        'messages': True,
        'calendar': True,
        'reminders': True,
        'notifications': True,
        'admin_dashboard': False,
        'team_management': False,
        'api_keys': False,
        'usage_tracking': False,
    })
    
    # ── Outils Agent ──
    agent_tools: List[str] = field(default_factory=lambda: [
        'contacts', 'voice', 'message', 'reminder', 'search'
    ])
    
    # ── Voix ──
    voice_default_emotion: str = 'warm'
    voice_auto_play: bool = True
    voice_clone_enabled: bool = True
    
    # ── Modèle AI ──
    ai_model: str = 'harmonic'           # harmonic | llm | hybrid
    ai_fast_mode: bool = True
    ai_knowledge_base: str = 'standard'  # standard | large | enterprise
    ai_personality: str = 'ka'
    ai_language: str = 'fr'
    
    # ── Sécurité ──
    rate_limit_enabled: bool = True
    rate_limit_max: int = 30
    auth_required: bool = False
    api_key_required: bool = False
    data_encryption: bool = False
    audit_log: bool = False
    
    # ── Stockage ──
    data_dir: str = 'data'
    max_upload_mb: int = 10
    cache_enabled: bool = True
    
    # ── Background Tasks ──
    background_tasks_enabled: bool = True
    max_concurrent_tasks: int = 3
    task_timeout_minutes: int = 30
    
    def to_dict(self) -> dict:
        """Sérialise la config en dictionnaire (pour l'API /api/config)."""
        return {
            'product': self.product,
            'name': self.name,
            'name_short': self.name_short,
            'tagline': self.tagline,
            'icon': self.icon,
            'version': self.version,
            'port': self.port,
            'theme': self.theme,
            'ui_layout': self.ui_layout,
            'pwa_enabled': self.pwa_enabled,
            'screens': self.screens,
            'default_screen': self.default_screen,
            'features': self.features,
            'agent_tools': self.agent_tools,
            'voice_default_emotion': self.voice_default_emotion,
            'voice_auto_play': self.voice_auto_play,
            'ai_personality': self.ai_personality,
            'ai_language': self.ai_language,
        }
    
    def has_feature(self, feature: str) -> bool:
        return self.features.get(feature, False)
    
    def enable(self, feature: str):
        self.features[feature] = True
    
    def disable(self, feature: str):
        self.features[feature] = False


# ═══════════════════════════════════════════════════════════════════════════════
# 📱 KA MOBILE — Téléphone Harmonique
# ═══════════════════════════════════════════════════════════════════════════════

KA_MOBILE = KAProductConfig(
    product='mobile',
    name='KA Mobile',
    name_short='KA',
    tagline='Votre compagnon dans la poche',
    icon='📱',
    
    port=8765,
    ui_layout='mobile',
    pwa_enabled=True,
    offline_support=True,
    animations=False,         # économie batterie
    font_scale=1.1,           # lisible sur petit écran
    
    screens=[
        'home',               # Accueil avec résumé
        'chat',               # Conversation principale
        'agent',              # Tâches agentiques
        'contacts',           # Répertoire
        'calls',              # Journal d'appels
        'profile',            # Réglages
    ],
    default_screen='chat',
    
    features={
        'chat': True,
        'voice_tts': True,           # Synthèse vocale (essentiel)
        'voice_stt': False,          # Dictée (futur)
        'agent': True,               # Agent conversationnel
        'code_gen': False,           # Pas de code sur mobile
        'deep_research': False,      # Pas de recherche lourde
        'file_management': False,    # Pas de fichiers
        'creative_media': False,     # Pas de génération média
        'health': False,             # Santé (optionnel)
        'enterprise': False,
        'multi_tenant': False,
        'knowledge_store': True,     # Base de connaissances
        'hologram_store': False,    # Store allégé
        'page_forge': False,        # Pas nécessaire sur mobile
        'jlens': False,             # Pas nécessaire sur mobile
        'contacts': True,            # ★ Répertoire
        'calls': True,               # ★ Appels
        'messages': True,            # ★ SMS/Chat
        'calendar': True,            # ★ Agenda
        'reminders': True,           # ★ Rappels
        'notifications': True,       # ★ Notifications push
        'admin_dashboard': False,
        'team_management': False,
        'api_keys': False,
        'usage_tracking': False,
    },
    
    agent_tools=['contacts', 'voice', 'message', 'reminder', 'search'],
    voice_default_emotion='warm',
    voice_auto_play=True,           # Auto-play sur mobile
    voice_clone_enabled=True,
    ai_model='harmonic',
    ai_fast_mode=True,              # Mode rapide (CPU mobile)
    ai_personality='ka',
    ai_language='fr',
    
    rate_limit_enabled=True,
    rate_limit_max=30,
    data_encryption=True,           # Données perso chiffrées
    max_upload_mb=5,
    max_concurrent_tasks=1,         # 1 tâche à la fois sur mobile
)


# ═══════════════════════════════════════════════════════════════════════════════
# 💻 KA PC — Desktop/Workstation
# ═══════════════════════════════════════════════════════════════════════════════

KA_PC = KAProductConfig(
    product='pc',
    name='KA PC',
    name_short='KA Pro',
    tagline='Votre poste de travail harmonique',
    icon='💻',
    
    port=8766,
    ui_layout='desktop',
    pwa_enabled=False,             # Application desktop native
    offline_support=True,
    animations=True,
    font_scale=1.0,
    
    screens=[
        'home',               # Dashboard multi-panel
        'chat',               # Chat avec panneau latéral
        'code',               # ★ IDE harmonique
        'research',           # ★ Recherche approfondie
        'creative',           # ★ Génération créative
        'files',              # Gestion de fichiers
        'store',              # Hologram Store
        'memory',             # Mémoire holographique
        'agent',              # Tâches agentiques
        'profile',            # Réglages
    ],
    default_screen='home',
    
    features={
        'chat': True,
        'voice_tts': True,           # Optionnel sur PC
        'voice_stt': False,
        'agent': True,               # Agent avancé
        'code_gen': True,             # ★ Génération de code
        'deep_research': True,        # ★ Recherche approfondie
        'file_management': True,      # ★ Gestion fichiers
        'creative_media': True,       # ★ Média créatif
        'health': False,
        'enterprise': False,
        'multi_tenant': False,
        'knowledge_store': True,      # Base complète
        'hologram_store': True,      # Store complet
        'page_forge': True,          # Génération de pages
        'jlens': True,               # Analyse JLens
        'contacts': False,           # Pas de téléphone
        'calls': False,
        'messages': False,
        'calendar': False,
        'reminders': True,           # Rappels desktop
        'notifications': True,       # Notifications système
        'admin_dashboard': False,
        'team_management': False,
        'api_keys': False,
        'usage_tracking': False,
    },
    
    agent_tools=['search', 'research', 'code', 'file', 'creative'],
    voice_default_emotion='calm',
    voice_auto_play=False,          # Manuel sur desktop
    voice_clone_enabled=True,
    ai_model='hybrid',              # Harmonique + LLM fallback
    ai_fast_mode=False,             # Qualité max
    ai_knowledge_base='large',
    ai_personality='savant',
    ai_language='fr',
    
    rate_limit_enabled=True,
    rate_limit_max=60,              # Plus de requêtes sur PC
    max_upload_mb=50,               # Fichiers plus gros
    max_concurrent_tasks=5,         # Multitâche
)


# ═══════════════════════════════════════════════════════════════════════════════
# 🏢 KA ENTERPRISE — Multi-tenant Business
# ═══════════════════════════════════════════════════════════════════════════════

KA_ENTERPRISE = KAProductConfig(
    product='enterprise',
    name='KA Enterprise',
    name_short='KA Pro',
    tagline='Intelligence harmonique pour votre organisation',
    icon='🏢',
    
    port=8767,
    ui_layout='admin',
    pwa_enabled=False,
    offline_support=False,          # Cloud-first
    animations=True,
    font_scale=1.0,
    
    screens=[
        'admin',              # ★ Dashboard administrateur
        'dashboard',          # ★ KPIs & métriques
        'team',               # ★ Gestion d'équipe
        'chat',               # Chat interne
        'knowledge',          # Base de connaissance entreprise
        'upload',             # Ingestion de documents
        'security',           # Sécurité & audit
        'store',              # Hologram Store entreprise
        'profile',            # Profil utilisateur
    ],
    default_screen='dashboard',
    
    features={
        'chat': True,
        'voice_tts': False,          # Optionnel en entreprise
        'voice_stt': False,
        'agent': True,               # Agent pour automatisation
        'code_gen': False,           # Non prioritaire
        'deep_research': True,       # Recherche documentaire
        'file_management': True,     # Gestion documentaire
        'creative_media': False,
        'health': False,
        'enterprise': True,          # ★ Mode entreprise
        'multi_tenant': True,        # ★ Multi-tenant
        'knowledge_store': True,     # Base entreprise privée
        'hologram_store': True,     # Store partagé
        'page_forge': False,
        'jlens': False,
        'contacts': False,
        'calls': False,
        'messages': False,
        'calendar': False,
        'reminders': False,
        'notifications': True,       # Alertes admin
        'admin_dashboard': True,     # ★ Dashboard admin
        'team_management': True,     # ★ Gestion équipe
        'api_keys': True,            # ★ Clés API
        'usage_tracking': True,      # ★ Suivi utilisation
    },
    
    agent_tools=['search', 'research', 'knowledge', 'admin'],
    voice_default_emotion='neutral',
    voice_auto_play=False,
    voice_clone_enabled=False,
    ai_model='harmonic',
    ai_fast_mode=False,
    ai_knowledge_base='enterprise',
    ai_personality='ka',
    ai_language='fr',
    
    # Sécurité entreprise
    rate_limit_enabled=True,
    rate_limit_max=100,              # Plus élevé
    auth_required=True,              # ★ Authentification requise
    api_key_required=True,           # ★ Clé API obligatoire
    data_encryption=True,            # ★ Chiffrement
    audit_log=True,                  # ★ Journal d'audit
    
    max_upload_mb=100,               # Gros documents
    max_concurrent_tasks=10,         # Haute capacité
)


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRE DES PRODUITS
# ═══════════════════════════════════════════════════════════════════════════════

PRODUCTS = {
    'mobile': KA_MOBILE,
    'pc': KA_PC,
    'enterprise': KA_ENTERPRISE,
}

PRODUCT_ALIASES = {
    'phone': 'mobile',
    'tel': 'mobile',
    'desktop': 'pc',
    'pro': 'pc',
    'business': 'enterprise',
    'corp': 'enterprise',
    'org': 'enterprise',
}


def get_config(product: str = 'mobile') -> KAProductConfig:
    """
    Retourne la configuration pour un produit donné.
    
    Args:
        product: 'mobile' | 'pc' | 'enterprise' (ou alias)
        
    Returns:
        KAProductConfig
    """
    product = PRODUCT_ALIASES.get(product.lower(), product.lower())
    if product not in PRODUCTS:
        raise ValueError(
            f"Produit '{product}' inconnu. Options: {list(PRODUCTS.keys())}. "
            f"Alias: {list(PRODUCT_ALIASES.keys())}"
        )
    return PRODUCTS[product]


def list_products() -> List[dict]:
    """Liste tous les produits disponibles."""
    return [
        {
            'id': p.product,
            'name': p.name,
            'icon': p.icon,
            'tagline': p.tagline,
            'port': p.port,
            'screens': len(p.screens),
            'features': sum(1 for v in p.features.values() if v),
            'tools': len(p.agent_tools),
        }
        for p in PRODUCTS.values()
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIVE CONFIG (définie au démarrage du serveur)
# ═══════════════════════════════════════════════════════════════════════════════

_active_config: Optional[KAProductConfig] = None


def set_active_config(config: KAProductConfig):
    """Définit la configuration active (appelé au démarrage)."""
    global _active_config
    _active_config = config
    # Variables d'environnement pour le frontend
    os.environ['KA_PRODUCT'] = config.product
    os.environ['KA_PORT'] = str(config.port)


def get_active_config() -> KAProductConfig:
    """Retourne la configuration active (défaut: mobile)."""
    global _active_config
    if _active_config is None:
        _active_config = KA_MOBILE
    return _active_config


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARAISON RAPIDE
# ═══════════════════════════════════════════════════════════════════════════════

def compare_products() -> str:
    """Affiche un tableau comparatif des 3 produits."""
    lines = []
    lines.append(f"{'Fonctionnalité':30s} {'📱 Mobile':15s} {'💻 PC':15s} {'🏢 Enterprise':15s}")
    lines.append("-" * 75)
    
    all_features = set()
    for p in PRODUCTS.values():
        all_features.update(p.features.keys())
    
    for feat in sorted(all_features):
        mobile = '✅' if KA_MOBILE.has_feature(feat) else '—'
        pc = '✅' if KA_PC.has_feature(feat) else '—'
        ent = '✅' if KA_ENTERPRISE.has_feature(feat) else '—'
        lines.append(f"{feat:30s} {mobile:15s} {pc:15s} {ent:15s}")
    
    lines.append("-" * 75)
    lines.append(f"{'Port':30s} {KA_MOBILE.port:<15d} {KA_PC.port:<15d} {KA_ENTERPRISE.port:<15d}")
    lines.append(f"{'Écrans':30s} {len(KA_MOBILE.screens):<15d} {len(KA_PC.screens):<15d} {len(KA_ENTERPRISE.screens):<15d}")
    lines.append(f"{'Outils Agent':30s} {len(KA_MOBILE.agent_tools):<15d} {len(KA_PC.agent_tools):<15d} {len(KA_ENTERPRISE.agent_tools):<15d}")
    
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 75)
    print("  KA Config — Système 3 Produits")
    print("=" * 75)
    
    # Liste des produits
    print("\n📦 Produits disponibles :")
    for p in list_products():
        print(f"  {p['icon']} {p['name']:20s} port={p['port']} | "
              f"{p['screens']} écrans | {p['features']} features | {p['tools']} outils")
    
    # Tableau comparatif
    print("\n" + compare_products())
    
    # Test get_config
    print("\n🔍 Test get_config() :")
    for alias in ['mobile', 'pc', 'enterprise', 'phone', 'desktop', 'corp']:
        try:
            cfg = get_config(alias)
            print(f"  '{alias}' → {cfg.name} (port {cfg.port})")
        except ValueError as e:
            print(f"  '{alias}' → ERREUR: {e}")
    
    # Test configuration active
    print("\n⚙️ Configuration active (défaut) :")
    set_active_config(KA_MOBILE)
    active = get_active_config()
    print(f"  Produit: {active.name} ({active.product})")
    print(f"  Port: {active.port}")
    print(f"  Écrans: {active.screens}")
    print(f"  Émotion voix: {active.voice_default_emotion}")
    print(f"  Auto-play: {active.voice_auto_play}")
    print(f"  Features activées: {sum(1 for v in active.features.values() if v)}/{len(active.features)}")
    
    # Test to_dict (pour API)
    print("\n📡 API /api/config :")
    d = active.to_dict()
    print(f"  {d['name']} v{d['version']} — {d['tagline']}")
    print(f"  Screens: {d['screens']}")
    print(f"  Features: {dict(list(d['features'].items())[:8])}...")
    
    print("\n✓ KA Config OK.")
