"""
KA Launcher — Démarrage Multi-Produits
========================================

Démarre le serveur KA avec la configuration produit appropriée.

Usage:
  python ka_launcher.py                          # KA Mobile (défaut)
  python ka_launcher.py --product mobile          # KA Mobile (port 8765)
  python ka_launcher.py --product pc              # KA PC (port 8766)
  python ka_launcher.py --product enterprise      # KA Enterprise (port 8767)
  python ka_launcher.py --product mobile --port 9000  # port personnalisé
  python ka_launcher.py --list                    # Lister les produits

Produits :
  📱 KA Mobile     — Téléphone Harmonique (contacts, appels, messages, rappels)
  💻 KA PC         — Desktop/Workstation (code, recherche, fichiers, créatif)
  🏢 KA Enterprise — Multi-tenant Business (équipe, admin, sécurité, API keys)

Intégration avec ka_server.py :
  Le serveur détecte la variable d'environnement KA_PRODUCT et adapte :
  - Les endpoints API exposés
  - Les écrans servis
  - Les fonctionnalités activées
  - Les middlewares de sécurité
"""

import sys
import os
import argparse
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ka_config import get_config, set_active_config, list_products, PRODUCTS


def main():
    parser = argparse.ArgumentParser(
        description='KA Launcher — Démarrage Multi-Produits',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python ka_launcher.py                         # KA Mobile (défaut)
  python ka_launcher.py --product pc            # KA PC
  python ka_launcher.py --product enterprise    # KA Enterprise
  python ka_launcher.py --product mobile --port 9000
  python ka_launcher.py --list                  # Lister les produits
        """
    )
    parser.add_argument('--product', '-p', type=str, default='mobile',
                       help='Produit à démarrer: mobile, pc, enterprise (défaut: mobile)')
    parser.add_argument('--port', type=int, default=None,
                       help='Port personnalisé (défaut: selon produit)')
    parser.add_argument('--list', action='store_true',
                       help='Lister les produits disponibles et quitter')
    parser.add_argument('--compare', action='store_true',
                       help='Afficher le tableau comparatif et quitter')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host (défaut: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true',
                       help='Mode debug Flask')
    
    args = parser.parse_args()
    
    # Mode liste
    if args.list:
        print("\n📦 Produits KA disponibles :\n")
        for p in list_products():
            print(f"  {p['icon']} {p['name']:20s} | port={p['port']} | "
                  f"{p['screens']} écrans | {p['features']} features | {p['tools']} outils")
            print(f"     {p['tagline']}")
        print()
        return
    
    # Mode comparaison
    if args.compare:
        from ka_config import compare_products
        print("\n" + compare_products())
        print()
        return
    
    # Charger la configuration
    try:
        config = get_config(args.product)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Surcharge du port
    if args.port:
        config.port = args.port
    if args.host:
        config.host = args.host
    if args.debug:
        config.debug = True
    
    # Définir la configuration active
    set_active_config(config)
    
    # Bannière
    print("=" * 60)
    print(f"  {config.icon} {config.name} v{config.version}")
    print(f"  {config.tagline}")
    print("=" * 60)
    print(f"  Produit      : {config.product}")
    print(f"  Port         : {config.port}")
    print(f"  Host         : {config.host}")
    print(f"  UI Layout    : {config.ui_layout}")
    print(f"  Écrans       : {len(config.screens)} ({', '.join(config.screens[:6])}...)")
    print(f"  Features     : {sum(1 for v in config.features.values() if v)}/{len(config.features)} activées")
    print(f"  Outils Agent : {config.agent_tools}")
    print(f"  Voix         : {'✓' if config.has_feature('voice_tts') else '✗'} "
          f"(émotion={config.voice_default_emotion}, auto-play={config.voice_auto_play})")
    print(f"  Modèle AI    : {config.ai_model} (fast={config.ai_fast_mode})")
    print(f"  Sécurité     : rate_limit={config.rate_limit_enabled}, "
          f"auth={config.auth_required}, encrypt={config.data_encryption}")
    print(f"  PWA          : {'✓' if config.pwa_enabled else '✗'}")
    print("=" * 60)
    print()
    
    # Démarrer le serveur
    print(f"🚀 Démarrage de {config.name} sur http://{config.host}:{config.port} ...\n")
    
    # Importer et lancer ka_server.py avec la config active
    import ka_server
    
    # Le serveur va lire get_active_config() pour s'adapter
    ka_server.port = config.port
    ka_server.app.run(
        host=config.host,
        port=config.port,
        debug=config.debug,
        threaded=config.threaded,
    )


if __name__ == '__main__':
    main()
