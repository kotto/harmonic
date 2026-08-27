# HARMONIC AI V 5 — Launcher
# ===========================
# Point d'entrée principal du Compagnon KA.
#
# Usage:
#   python launcher.py                    # Mode interactif
#   python launcher.py --demo             # Démonstration complète
#   python launcher.py --user Sophie      # Charger un profil
#   python launcher.py --test             # Tests d'intégration

import sys
import time
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from config import PHI, DIM_PSI, EMOTIONS, PHONE_TOOLS
from core.companion_core import KACompanion, demo


def print_banner():
    """Affiche la bannière de démarrage."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🧠  HARMONIC AI  V 5                                      ║
║   Compagnon KA — Agent Téléphone Harmonique                 ║
║                                                              ║
║   Performance Hermes · Zéro paramètre · 100% local          ║
║   ℂ⁵¹² · φ={phi:.4f} · CPU ARM · < 10 Mo                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""".format(phi=PHI))


def interactive_mode(ka: KACompanion):
    """Mode conversationnel interactif."""
    print(f"\n✨ {ka.state.name} est prêt. Tape 'aide' pour les commandes.\n")
    
    commands = {
        'aide': 'Affiche cette aide',
        'quit': 'Quitter',
        'save': 'Sauvegarder l\'état',
        'status': 'Afficher le tableau de bord',
        'emotion <nom>': f'Changer l\'émotion ({", ".join(list(EMOTIONS)[:5])}...)',
        'personality <nom>': 'Changer la personnalité',
        'forget': 'Réinitialiser la conversation en cours',
        'demo': 'Lancer la démonstration',
    }
    
    while True:
        try:
            user_input = input(f"\n👤 {ka.state.user_name or 'Vous'}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Au revoir !")
            break
        
        if not user_input:
            continue
        
        # Commandes spéciales
        if user_input.lower() in ('quit', 'exit', 'q'):
            print("👋 Au revoir !")
            ka.save()
            break
        
        if user_input.lower() == 'aide':
            print("\n📋 Commandes disponibles :")
            for cmd, desc in commands.items():
                print(f"  /{cmd:25s} — {desc}")
            continue
        
        if user_input.lower() == 'save':
            path = ka.save()
            print(f"💾 État sauvegardé dans {path}")
            continue
        
        if user_input.lower() == 'status':
            dash = ka.dashboard()
            print("\n📊 Tableau de bord :")
            print(f"  Sessions: {dash['state']['session_duration_min']:.0f} min")
            print(f"  Conversations: {dash['state']['total_conversations']}")
            print(f"  Faits en mémoire: {dash['memory']['total_facts']}")
            print(f"  Personnalité: {dash['state']['personality']}")
            print(f"  Émotion: {dash['state']['emotion']}")
            print(f"  Contacts: {dash['phone']['contacts_count']}")
            print(f"  Messages: {dash['phone']['messages_total']}")
            print(f"  Rappels actifs: {dash['phone']['reminders_active']}")
            print(f"  Latence moyenne: {dash['pipeline']['avg_latency_ms']:.1f} ms")
            continue
        
        if user_input.lower().startswith('emotion '):
            em = user_input[8:].strip()
            if em in EMOTIONS:
                ka.set_emotion(em)
                print(f"🎭 Émotion changée: {em}")
            else:
                print(f"❌ Émotion inconnue. Options: {', '.join(list(EMOTIONS)[:5])}...")
            continue
        
        if user_input.lower().startswith('personality '):
            pers = user_input[13:].strip()
            try:
                ka.set_personality(pers)
                print(f"🎭 Personnalité changée: {pers}")
            except ValueError as e:
                print(f"❌ {e}")
            continue
        
        if user_input.lower() == 'forget':
            ka.pipeline.memory.flush_working_to_history()
            print("🧹 Conversation réinitialisée.")
            continue
        
        if user_input.lower() == 'demo':
            demo()
            continue
        
        # Conversation normale
        result = ka.chat(user_input)
        print(f"🤖 {ka.state.name}: {result.response}")
        print(f"   [{result.intent.type}] {result.emotion_response} "
              f"cohérence={result.confidence:.3f} ⏱{result.latency_ms:.1f}ms")


def main():
    """Point d'entrée principal."""
    print_banner()
    
    # Analyser les arguments
    args = sys.argv[1:]
    
    # Mode démo
    if '--demo' in args:
        demo()
        return
    
    # Mode test
    if '--test' in args:
        from tests.test_integration import run_all_tests
        run_all_tests()
        return
    
    # Créer le compagnon
    user_name = None
    for i, arg in enumerate(args):
        if arg == '--user' and i + 1 < len(args):
            user_name = args[i + 1]
    
    personality = 'compagnon'
    for i, arg in enumerate(args):
        if arg == '--personality' and i + 1 < len(args):
            personality = args[i + 1]
    
    ka = KACompanion(name="KA", personality=personality, emotion='warm')
    
    # Charger le profil si spécifié
    if user_name:
        ka.set_user(user_name)
        loaded = ka.load(user_name)
        if loaded:
            print(f"📂 Profil '{user_name}' chargé.")
        else:
            print(f"📂 Nouveau profil: '{user_name}'")
    
    # Mode interactif
    interactive_mode(ka)


if __name__ == '__main__':
    main()