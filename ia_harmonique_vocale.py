#!/usr/bin/env python3
r"""
IA HARMONIQUE VOCALE — Synthèse + Reconnaissance Vocale
==========================================================
Connecte l'IA harmonique interactive aux capacités vocales de ka_phone.

Entrée : microphone → reconnaissance vocale → texte
Traitement : IA harmonique (moteur_raisonnement_universel)
Sortie : texte → synthèse vocale → haut-parleurs

Usage :
  python ia_harmonique_vocale.py
  python ia_harmonique_vocale.py --mode voice
  python ia_harmonique_vocale.py --mode text
"""

import sys, os, time, json, threading, queue

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ka_phone'))
sys.path.insert(0, os.path.dirname(__file__))

from ia_harmonique_interactive import IAHarmoniqueInteractive, Personnalite


# ═══════════════════════════════════════════════════════════════════════════════
# PONT VOCAL — ka_phone
# ═══════════════════════════════════════════════════════════════════════════════

class PontVocal:
    """Connecte l'IA harmonique aux capacités vocales de ka_phone."""
    
    def __init__(self, ia_harmonique):
        self.ia = ia_harmonique
        self.tts = None
        self.stt = None
        self.vad = None
        self._initialise = False
    
    def initialiser(self):
        """Initialise les modules vocaux (lazy import)."""
        if self._initialise:
            return True
        
        try:
            # Synthèse vocale (TTS)
            from tts_streaming import TTSStreamer
            self.tts = TTSStreamer()
            print("  ✓ Synthèse vocale (TTS) initialisée")
        except ImportError:
            print("  ⚠️  TTS non disponible — mode texte uniquement")
            self.tts = None
        
        try:
            # Reconnaissance vocale (STT)
            from vad_service import VADService
            self.vad = VADService()
            self.stt = self.vad  # VAD inclut STT
            print("  ✓ Reconnaissance vocale (VAD+STT) initialisée")
        except ImportError:
            print("  ⚠️  Reconnaissance vocale non disponible — utilisez le clavier")
            self.vad = None
            self.stt = None
        
        self._initialise = True
        return self.tts is not None or self.stt is not None
    
    def parler(self, texte):
        """Synthétise et joue le texte."""
        if self.tts:
            try:
                self.tts.speak(texte)
                return True
            except:
                pass
        
        # Fallback : affichage uniquement
        print(f"\n🔊 {texte[:200]}...")
        return False
    
    def ecouter(self, timeout=10):
        """Écoute le microphone et retourne le texte reconnu."""
        if self.vad:
            try:
                texte = self.vad.listen(timeout=timeout)
                if texte:
                    return texte
            except:
                pass
        
        # Fallback : saisie clavier
        try:
            return input("\n🧑 Vous (parlez ou tapez) > ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
    
    def est_disponible(self):
        return self.tts is not None or self.stt is not None


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE VOCALE UNIFIÉE
# ═══════════════════════════════════════════════════════════════════════════════

class IAHarmoniqueVocale:
    """
    IA harmonique avec entrée/sortie vocale.
    Mode texte : clavier + affichage (fallback)
    Mode voix  : microphone + haut-parleurs
    """
    
    def __init__(self, personnalite="pedagogique", mode="auto"):
        print("\n🌊 IA HARMONIQUE VOCALE — Initialisation\n")
        
        # Initialiser l'IA harmonique
        self.ia = IAHarmoniqueInteractive(personnalite=personnalite)
        
        # Initialiser le pont vocal
        self.vocal = PontVocal(self.ia)
        self.vocal_dispo = self.vocal.initialiser()
        
        # Déterminer le mode
        if mode == "auto":
            self.mode = "voice" if self.vocal_dispo else "text"
        else:
            self.mode = mode
        
        self.actif = True
        self.message_queue = queue.Queue()
    
    def traiter_requete(self, question):
        """Traite une question (texte) et retourne la réponse formatée."""
        resultat = self.ia.traiter(question)
        return resultat
    
    def boucle_interactive(self):
        """Boucle principale : écoute → raisonne → parle."""
        print(f"""
╔══════════════════════════════════════════════════════════╗
║     🌊 IA HARMONIQUE VOCALE 🌊                          ║
║                                                          ║
║  Mode : {self.mode:<46s}║
║  Raisonnement : interférence d'ondes                     ║
║  Vérification : Ψ_a·Ψ_b = Ψ_{a+b}                       ║
║                                                          ║
║  Commandes :                                             ║
║    /aide     — aide                                      ║
║    /session  — résumé de la session                      ║
║    /style XX — changer de personnalité                   ║
║    /voice    — forcer le mode vocal                      ║
║    /text     — forcer le mode texte                      ║
║    /quit     — quitter                                   ║
╚══════════════════════════════════════════════════════════╝
""")
        
        if self.mode == "voice" and self.vocal.tts:
            self.vocal.parler("IA Harmonique prête. Posez votre question.")
        
        while self.actif:
            try:
                # ── ÉCOUTER ──
                if self.mode == "voice":
                    question = self.vocal.ecouter(timeout=30)
                else:
                    question = input("\n🧑 Vous > ").strip()
                
                if question is None:
                    break
                if not question:
                    continue
                
                # ── COMMANDES ──
                if question.lower() in ('/quit', '/q', 'quit', 'exit'):
                    if self.vocal.tts:
                        self.vocal.parler("Au revoir. Les ondes continuent de résonner.")
                    print("\n👋 Au revoir !\n")
                    break
                
                if question.lower() == '/session':
                    print(f"\n{self.ia.session_info()}")
                    continue
                
                if question.lower().startswith('/style '):
                    style = question.split(maxsplit=1)[1].strip().lower()
                    if style in Personnalite.STYLES:
                        self.ia.personnalite = Personnalite(style)
                        msg = f"Style changé pour : {style}"
                        print(f"\n  ✅ {msg}")
                        if self.vocal.tts:
                            self.vocal.parler(msg)
                    continue
                
                if question.lower() == '/voice':
                    self.mode = "voice"
                    print("\n  ✅ Mode vocal activé")
                    continue
                
                if question.lower() == '/text':
                    self.mode = "text"
                    print("\n  ✅ Mode texte activé")
                    continue
                
                if question.lower() in ('/aide', '/help'):
                    self._afficher_aide()
                    continue
                
                # ── RAISONNER ──
                print(f"\n🧠 Réflexion...")
                resultat = self.traiter_requete(question)
                
                # ── AFFICHER ──
                print(resultat['reponse_formatee'])
                
                # ── PARLER ──
                if self.mode == "voice" and self.vocal.tts:
                    # Version concise pour la voix
                    resume = f"Réponse : {resultat['reponse']}. {resultat.get('suggestion', '')}"
                    threading.Thread(target=self.vocal.parler, args=(resume,), daemon=True).start()
                
                # ── SUGGÉRER ──
                if resultat.get('suggestion'):
                    print(f"\n💭 {resultat['suggestion']}")
            
            except KeyboardInterrupt:
                print("\n\n👋 Au revoir !\n")
                break
            except Exception as e:
                print(f"\n  ⚠️ Erreur : {e}")
    
    def _afficher_aide(self):
        print("""
  Commandes vocales disponibles :
    Dites simplement votre question mathématique.
    Exemples : "3 plus 4", "x plus 3 égale 7", "racine de 225"
  
  Commandes texte :
    /aide     — cette aide
    /session  — résumé des échanges précédents
    /style XX — changer de personnalité (pedagogique, concis, scientifique, poetique)
    /voice    — forcer le mode vocal
    /text     — forcer le mode texte
    /quit     — quitter
        """)


if __name__ == "__main__":
    import argparse
    
    p = argparse.ArgumentParser(description="IA Harmonique Vocale")
    p.add_argument("--personnalite", type=str, default="pedagogique",
                   choices=["pedagogique", "concis", "scientifique", "poetique"])
    p.add_argument("--mode", type=str, default="auto",
                   choices=["auto", "voice", "text"],
                   help="Mode d'interaction (auto = détection automatique)")
    args = p.parse_args()
    
    ia_vocale = IAHarmoniqueVocale(
        personnalite=args.personnalite,
        mode=args.mode,
    )
    
    ia_vocale.boucle_interactive()