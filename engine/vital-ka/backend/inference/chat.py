"""
Harmonic AI v2.0 — Interface de Démonstration Interactive
===========================================================
Chat conversationnel avec mémoire, créativité, raisonnement et apprentissage.

Usage:
  python chat.py              → charge le meilleur modèle disponible
  python chat.py --model 50k  → charge le modèle 50K
  python chat.py --model 217k → charge le modèle 217K nettoyé
  python chat.py --model 500k → charge le modèle 500K (attention: RAM)

Commandes spéciales :
  /help     → afficher l'aide
  /stats    → statistiques du système
  /create   → connexion créative entre deux domaines
  /haiku    → générer un haïku
  /reason X → raisonnement en chaîne sur X
  /reset    → effacer la mémoire de conversation
  /quit     → quitter
"""

import sys, os, time
from pathlib import Path
import numpy as np

# Setup
sys.path.insert(0, str(Path(__file__).resolve().parent))

from harmonic_ai import HarmonicAI
from reasoning_engine import ReasoningEngine

# ═══════════════════════════════════════════════════════════════════════════════
# TERMINAL COLORS (cross-platform)
# ═══════════════════════════════════════════════════════════════════════════════

class Color:
    """Codes ANSI pour terminal."""
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    DIM     = '\033[2m'
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'
    GRAY    = '\033[90m'

def c(text, color):
    """Applique une couleur si le terminal le supporte."""
    if os.environ.get('NO_COLOR') or sys.platform == 'win32':
        return text
    return f"{color}{text}{Color.RESET}"

def banner():
    """Affiche la bannière de démarrage."""
    print(c("""
╔══════════════════════════════════════════════════════╗
║   𝄞  HARMONIC AI v2.0  —  Intelligence Ondulatoire  ║
║        Ψ_a · Ψ_b = Ψ_{a+b}      0 paramètre         ║
╚══════════════════════════════════════════════════════╝""", Color.CYAN))

def show_stats(ai):
    """Affiche les statistiques du système."""
    stats = ai.stats
    auto = stats.get('autonomie', 100)
    color = Color.GREEN if auto > 70 else Color.YELLOW if auto > 30 else Color.RED
    
    print(f"""
{c('📊 STATISTIQUES', Color.BOLD)}
  {c('Faits', Color.DIM)}      : {stats['faits']:>10,}
  {c('Vocabulaire', Color.DIM)} : {stats['vocabulaire']:>10,}
  {c('Autonomie', Color.DIM)}   : {c(f'{auto:.0f}%', color)}
  {c('LLM calls', Color.DIM)}   : {stats.get('llm_calls', 0):>10}
  {c('Énergie', Color.DIM)}     : {stats.get('energie', 0):>10.0f}
""")

def show_help():
    """Affiche l'aide."""
    print(f"""
{c('🤖 COMMANDES', Color.BOLD)}
  {c('/help', Color.YELLOW)}     → cette aide
  {c('/stats', Color.YELLOW)}    → statistiques du système
  {c('/create', Color.YELLOW)}   → connexion créative entre domaines
  {c('/haiku', Color.YELLOW)}    → générer un haïku
  {c('/reason X', Color.YELLOW)} → raisonnement en chaîne sur X
  {c('/surreal', Color.YELLOW)}  → image surréaliste
  {c('/reset', Color.YELLOW)}    → effacer la mémoire
  {c('/quit', Color.YELLOW)}     → quitter

{c('💡 EXEMPLES', Color.BOLD)}
  {c('>', Color.DIM)} Qu'est-ce que la lumière ?
  {c('>', Color.DIM)} Comment fonctionne la gravité ?
  {c('>', Color.DIM)} Explique le lien entre ADN et évolution
  {c('>', Color.DIM)} What is consciousness ?
""")

def chat_loop(ai):
    """Boucle principale de chat."""
    print(c(f"\n{c('💬 CONVERSATION', Color.BOLD)} — Tapez {c('/help', Color.YELLOW)} pour l'aide, {c('/quit', Color.YELLOW)} pour quitter\n", Color.DIM))
    
    turn = 1
    while True:
        try:
            user_input = input(f"{c(f'[{turn}]', Color.DIM)} {c('Vous', Color.GREEN)} > ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{c('👋 Au revoir !', Color.CYAN)}")
            break
        
        if not user_input:
            continue
        
        # Commandes spéciales
        if user_input.startswith('/'):
            cmd = user_input.split()[0].lower()
            
            if cmd == '/quit':
                print(f"\n{c('👋 Au revoir !', Color.CYAN)}")
                print(f"  Session: {turn-1} échanges | Autonomie finale: {ai.stats.get('autonomie', 100):.0f}%")
                break
            
            elif cmd == '/help':
                show_help()
            
            elif cmd == '/stats':
                show_stats(ai)
            
            elif cmd == '/reset':
                ai.conversation.messages.clear()
                print(c('  🧹 Mémoire effacée.', Color.DIM))
            
            elif cmd == '/create':
                print(c('  🎨 Génération créative...', Color.DIM))
                ideas = ai.create(n=2)
                for i, idea in enumerate(ideas):
                    print(f"  {c(f'{i+1}.', Color.MAGENTA)} {idea[:200]}")
            
            elif cmd == '/haiku':
                print(c('  🌸 Génération de haïku...', Color.DIM))
                haiku = ai.haiku()
                for line in haiku.split('\n') if '\n' in haiku else [haiku]:
                    print(f"  {c(line.strip(), Color.MAGENTA)}")
            
            elif cmd == '/surreal':
                print(c('  🌀 Images surréalistes...', Color.DIM))
                images = ai.surreal(n=2)
                for img in images:
                    print(f"  {c(img.strip(), Color.MAGENTA)}")
            
            elif cmd == '/reason':
                topic = ' '.join(user_input.split()[1:])
                if topic:
                    print(c(f'  🔗 Raisonnement sur "{topic}"...', Color.DIM))
                    result = ai.reason(topic)
                    print(f"  {c(result.strip(), Color.BLUE)}")
                else:
                    print(c('  Usage: /reason <sujet>', Color.DIM))
            
            else:
                print(c(f'  Commande inconnue: {cmd}. Tapez /help', Color.DIM))
            
            continue
        
        # Question normale → réponse
        t0 = time.time()
        response = ai.ask(user_input)
        latency_ms = (time.time() - t0) * 1000
        
        # Déterminer la source de la réponse
        confidence = ai._confidence_score(response, user_input)
        stats = ai.stats
        
        # Affichage
        if confidence < 0.35:
            # Réponse LLM (fallback)
            print(f"{c('  IA', Color.BLUE)} {c('[LLM]', Color.YELLOW)} {c(f'({latency_ms:.0f}ms)', Color.DIM)} > {response}")
        else:
            # Réponse harmonique
            print(f"{c('  IA', Color.CYAN)} {c(f'({latency_ms:.0f}ms)', Color.DIM)} > {response}")
        
        turn += 1


# ═══════════════════════════════════════════════════════════════════════════════
# INITIALISATION
# ═══════════════════════════════════════════════════════════════════════════════

def load_model(model_name='best'):
    """Charge le modèle spécifié."""
    model_files = {
        '50k': '../data/bootstrapper_output/knowledge_base_50k.npz',
        '217k': '../data/bootstrapper_output/knowledge_base_clean.npz',
        '500k': '../data/bootstrapper_output/knowledge_base_500k.npz',
        'best': '../data/bootstrapper_output/knowledge_base_clean.npz',
    }
    
    path = model_files.get(model_name, model_files['best'])
    
    if not Path(path).exists():
        print(f"Fichier introuvable: {path}")
        print("Modèles disponibles: 50k, 217k, 500k")
        sys.exit(1)
    
    print(c(f"  Chargement: {Path(path).name}...", Color.DIM))
    data = np.load(str(path), allow_pickle=True)
    facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
    print(c(f"  {len(facts):,} faits chargés", Color.DIM))
    
    return facts


def main():
    # Parser les arguments
    model_name = 'best'
    for arg in sys.argv[1:]:
        if arg.startswith('--model='):
            model_name = arg.split('=')[1]
        elif arg == '--model' and len(sys.argv) > sys.argv.index(arg) + 1:
            model_name = sys.argv[sys.argv.index(arg) + 1]
    
    banner()
    
    # Charger
    print(c('\n📂 Initialisation...', Color.DIM))
    facts = load_model(model_name)
    
    # Créer l'IA
    ai = HarmonicAI(enable_bootstrapper=True)
    ai.model.knowledge_base = facts
    ai.model.rebuild_waves()
    ai.engine = ReasoningEngine(ai.model)
    
    # Stats
    show_stats(ai)
    
    # Entraînement rapide si pas encore fait
    if ai.model._encoder is not None and ai.model._encoder.n_facts < 10:
        print(c('  ⚡ Entraînement rapide de l\'encodeur...', Color.DIM))
        result = ai.model.train_encoder(epochs=3, lr=0.4)
        if 'precision_apres' in result:
            print(c(f"  Précision: {result['precision_avant']}% → {result['precision_apres']}% ({result.get('temps_s', 0):.1f}s)", Color.DIM))
    
    print(c('\n✨ Prêt !\n', Color.GREEN))
    
    # Lancer le chat
    chat_loop(ai)


if __name__ == '__main__':
    main()
