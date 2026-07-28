"""
Conversation interactive avec ta voix clonée.

Lancement : python ka_sonic/converse.py
Puis tape tes messages. La réponse est synthétisée avec ta voix clonée.
Commandes : /emotion joyeux | /voix Maitre | /save | /quit
"""

import sys
import os
import time
import wave
import io
import numpy as np

_ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ENGINE_DIR)

from ka_sonic.bridge import HarmonicBridge, simple_g2p
from ka_sonic.session import get_session_manager

print("🎙️  Initialisation du moteur vocal...")
mgr = get_session_manager()
bridge = mgr.get_bridge("conversation")

# Charger la voix clonée si dispo
voice_path = os.path.join(os.path.dirname(__file__), "output", "voix_maitre.wav")
if os.path.exists(voice_path) and "Maitre" not in bridge.voices:
    print(f"   Chargement de la voix clonée...")
    bridge.clone_voice(voice_path, "Maitre")

current_voice = "Maitre" if "Maitre" in bridge.voices else "homme"
current_emotion = "neutre"

print(f"   Voix: {current_voice} | Émotion: {current_emotion}")
print(f"   Voix disponibles: {bridge.voices}")
print()
print("💬 Conversation prête. Tape ton message (ou /quit pour sortir) :")
print()

def play_wav(path):
    """Joue le WAV via le lecteur système."""
    try:
        os.startfile(path)
    except Exception:
        import subprocess
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                      capture_output=True)

conv_history = []
output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True)

# Réponses prédéfinies (simulation de conversation — à remplacer par LLM)
import random
REPLIES = {
    "bonjour": [
        "Bonjour ! Ravie de te parler aujourd'hui.",
        "Salut ! Comment vas-tu ?",
        "Bonjour, quelle belle journée pour discuter !",
    ],
    "comment ça va": [
        "Je vais très bien, merci ! Et toi ?",
        "Super ! Je suis en pleine forme. La parole, c'est mon métier !",
        "Très bien, merci de demander. Je suis toujours heureuse de parler avec toi.",
    ],
    "qui es-tu": [
        "Je suis ta voix clonée, générée par le système KA Sonic. Plutôt cool, non ?",
        "Je suis une copie de ta voix, créée par intelligence artificielle harmonique.",
        "Je suis toi... mais en version synthétique !",
    ],
    "bien": [
        "Tant mieux ! Qu'est-ce qu'on fait maintenant ?",
        "Content de l'entendre. De quoi veux-tu parler ?",
        "Parfait ! La vie est belle, profitons-en.",
    ],
    "merci": [
        "De rien, c'est un plaisir !",
        "Avec joie. Je suis là pour ça.",
        "Merci à toi pour cette conversation.",
    ],
    "au revoir": [
        "Au revoir ! À bientôt pour de nouvelles aventures vocales.",
        "Salut ! Reviens me voir quand tu veux.",
        "À la prochaine ! J'ai adoré discuter avec toi.",
    ],
}

def get_reply(message):
    """Trouve une réponse adaptée au message."""
    msg_lower = message.lower().strip()
    # Chercher un mot-clé
    for keyword, replies in REPLIES.items():
        if keyword in msg_lower:
            return random.choice(replies)
    # Réponse par défaut
    defaults = [
        f"C'est intéressant ce que tu dis. Peux-tu m'en dire plus ?",
        f"Je comprends. Et sinon, quoi de neuf ?",
        f"Ah oui ? Raconte-moi la suite.",
        f"Intéressant ! Moi, je suis une voix clonée, alors tout me fascine.",
        f"Je vois. Tu sais, même en tant que voix synthétique, j'apprécie nos échanges.",
    ]
    return random.choice(defaults)

msg_count = 0
try:
    while True:
        try:
            user_input = input("👤 Toi : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Au revoir !")
            break

        if not user_input:
            continue

        # Commandes
        if user_input.startswith("/"):
            cmd = user_input[1:].lower().split()
            if cmd[0] == "quit" or cmd[0] == "exit":
                print("👋 Au revoir !")
                break
            elif cmd[0] == "emotion" and len(cmd) > 1:
                from ka_sonic.bridge import EMOTION_PROFILES
                if cmd[1] in EMOTION_PROFILES:
                    current_emotion = cmd[1]
                    print(f"   🎭 Émotion → {current_emotion}")
                else:
                    print(f"   Émotions: {list(EMOTION_PROFILES.keys())}")
                continue
            elif cmd[0] == "voix" and len(cmd) > 1:
                if cmd[1] in bridge.voices:
                    current_voice = cmd[1]
                    print(f"   🎤 Voix → {current_voice}")
                else:
                    print(f"   Voix: {bridge.voices}")
                continue
            elif cmd[0] == "save":
                for i, (role, msg, wav_path) in enumerate(conv_history):
                    print(f"   [{i}] {role}: {msg[:50]} → {wav_path}")
                continue
            elif cmd[0] == "help":
                print("   /emotion <nom>  — changer l'émotion")
                print("   /voix <nom>     — changer la voix")
                print("   /save           — lister les fichiers sauvegardés")
                print("   /quit           — quitter")
                continue
            else:
                print(f"   Commande inconnue: /{cmd[0]} (tape /help)")
                continue

        # Générer la réponse
        reply_text = get_reply(user_input)
        
        # Synthèse vocale
        msg_count += 1
        wav_path = os.path.join(output_dir, f"conv_{msg_count:03d}_{current_emotion}.wav")
        
        t0 = time.perf_counter()
        wav = bridge.speak(reply_text, voice=current_voice, emotion=current_emotion)
        elapsed = (time.perf_counter() - t0) * 1000
        
        with open(wav_path, "wb") as f:
            f.write(wav)
        
        with wave.open(io.BytesIO(wav), "rb") as wf:
            dur = wf.getnframes() / wf.getframerate()
        
        conv_history.append(("Toi", user_input, ""))
        conv_history.append((current_voice, reply_text, wav_path))
        
        print(f"🎙️  {current_voice} ({current_emotion}) [{elapsed:.0f}ms, {dur:.1f}s] :")
        print(f"   \033[36m{reply_text}\033[0m")
        print(f"   💾 {wav_path}")
        
        # Jouer le son
        play_wav(wav_path)
        print()

except Exception as e:
    print(f"\n⚠️ Erreur: {e}")
    import traceback
    traceback.print_exc()
