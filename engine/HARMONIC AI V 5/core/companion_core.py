"""
HARMONIC AI V 5 — Companion Core
==================================
Noyau agent-compagnon — le point d'entrée unique du Compagnon KA.

Intègre tous les modules en une API unifiée :
  - ConversationPipeline   → compréhension + réponse naturelle
  - MemoryCore              → mémoire holographique ℂ⁵¹²
  - PersonalityEngine       → émotions + personnalité
  - PhoneBus                → fonctions téléphone

Performance équivalente Hermes · Zéro paramètre · 100% local · CPU ARM

Architecture :
  ┌─────────────────────────────────────────────────────────┐
  │                   KACompanionCore                        │
  │                                                          │
  │  📥 Entrée :  texte, voix, contexte, capteurs            │
  │  🧠 Cerveau :  Pipeline conversationnel (6 étapes)       │
  │  🗄️ Mémoire :  HologramStore ℂ⁵¹² (persistant)          │
  │  🎭 Émotions :  PersonalityEngine (10 émotions φ)        │
  │  📞 Téléphone:  PhoneBus (contacts, appels, SMS, agenda) │
  │  📤 Sortie :   texte, audio, actions, notifications      │
  └─────────────────────────────────────────────────────────┘

Usage :
  from companion_core import KACompanion

  ka = KACompanion(name="KA", personality="compagnon")
  ka.set_user("Sophie")

  # Conversation
  response = ka.chat("Bonjour KA, comment vas-tu ?")

  # Action téléphone
  result = ka.chat("Appelle Maman")

  # Apprentissage
  ka.chat("Rappelle-toi que j'aime le thé vert le matin")

  # Sauvegarde
  ka.save()
"""

import math
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np

from config import (
    PHI, TAU, PHI_INV, DIM_PSI, DIM_HOLOGRAM,
    SAMPLE_RATE, HOLOGRAM_DIR, VOICE_DIR,
)
from core.memory_core import (
    MemoryCore, text_to_psi, psi_resonate, Fact,
)
from core.personality_engine import (
    PersonalityEngine, HarmonicPersonality,
)
from core.phone_bus import PhoneBus
from core.conversation_pipeline import (
    ConversationPipeline, PipelineResult, Intent,
)


# ═══════════════════════════════════════════════════════════
# COMPANION STATE
# ═══════════════════════════════════════════════════════════

@dataclass
class CompanionState:
    """État global du compagnon."""
    name: str = 'KA'
    user_name: str = ''
    emotion: str = 'warm'
    personality: str = 'compagnon'
    is_listening: bool = True
    is_speaking: bool = False
    is_offline: bool = False
    session_started: float = 0.0
    total_conversations: int = 0
    total_actions: int = 0
    
    def __post_init__(self):
        if self.session_started == 0.0:
            self.session_started = time.time()
    
    @property
    def session_duration_minutes(self) -> float:
        return (time.time() - self.session_started) / 60.0
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'user_name': self.user_name,
            'emotion': self.emotion,
            'personality': self.personality,
            'is_listening': self.is_listening,
            'is_speaking': self.is_speaking,
            'is_offline': self.is_offline,
            'session_duration_min': self.session_duration_minutes,
            'total_conversations': self.total_conversations,
            'total_actions': self.total_actions,
        }


# ═══════════════════════════════════════════════════════════
# KACompanion — Noyau Agent-Compagnon
# ═══════════════════════════════════════════════════════════

class KACompanion:
    """
    Compagnon KA — l'agent qui vit dans votre téléphone.
    
    Point d'entrée unique pour toutes les interactions avec
    le compagnon harmonique.
    """
    
    def __init__(self, name: str = 'KA',
                 personality: str = 'compagnon',
                 emotion: str = 'warm'):
        
        # Identité
        self.state = CompanionState(
            name=name,
            personality=personality,
            emotion=emotion,
        )
        
        # Modules
        self.memory = MemoryCore(dim=DIM_HOLOGRAM)
        self.personality_engine = PersonalityEngine(dim=DIM_PSI)
        self.phone = PhoneBus(
            memory=self.memory,
            personality=self.personality_engine,
        )
        self.pipeline = ConversationPipeline(
            memory=self.memory,
            personality=self.personality_engine,
            phone_bus=self.phone,
        )
        
        # Configurer la personnalité
        self.personality_engine.set_personality(personality)
        self.personality_engine.set_emotion(emotion)
        
        # Callbacks
        self._on_response: List[Callable] = []
        self._on_action: List[Callable] = []
        self._on_notification: List[Callable] = []
        
        # Statistiques
        self._created_at = time.time()
        
        print(f"[KACompanion] {name} initialisé — "
              f"personnalité={personality}, émotion={emotion}")
    
    # ═══════════════════════════════════════════════════════
    # CONFIGURATION
    # ═══════════════════════════════════════════════════════
    
    def set_user(self, name: str, profile: dict = None):
        """Définit l'utilisateur du compagnon."""
        self.state.user_name = name
        self.memory.set_user_name(name)
        
        if profile:
            for key, value in profile.items():
                self.memory.set_user_preference(key, value)
        
        print(f"[KACompanion] Utilisateur: {name}")
    
    def set_personality(self, name: str):
        """Change la personnalité du compagnon."""
        self.state.personality = name
        self.personality_engine.set_personality(name)
    
    def set_emotion(self, emotion: str):
        """Change l'émotion courante."""
        self.state.emotion = emotion
        self.personality_engine.set_emotion(emotion)
    
    def toggle_offline(self):
        """Bascule en mode hors-ligne."""
        self.state.is_offline = not self.state.is_offline
        status = "hors-ligne" if self.state.is_offline else "en ligne"
        print(f"[KACompanion] Mode {status}")
    
    # ═══════════════════════════════════════════════════════
    # API PRINCIPALE
    # ═══════════════════════════════════════════════════════
    
    def chat(self, text: str,
             context: Dict[str, Any] = None) -> PipelineResult:
        """
        Point d'entrée principal : conversation avec le compagnon.
        
        Args:
            text: message de l'utilisateur
            context: contexte additionnel
            
        Returns:
            PipelineResult avec réponse, intention, émotion, métriques
        """
        ctx = context or {}
        ctx['user_name'] = self.state.user_name
        ctx['offline'] = self.state.is_offline
        ctx['emotion'] = self.state.emotion
        
        result = self.pipeline.process(text, context=ctx)
        
        # Mettre à jour l'état
        self.state.total_conversations += 1
        self.state.emotion = result.emotion_response
        
        # Notifier les callbacks
        for cb in self._on_response:
            try:
                cb(result)
            except Exception:
                pass
        
        return result
    
    def voice_command(self, text: str) -> dict:
        """
        Traite une commande vocale.
        
        En production : STT → texte → chat() → TTS.
        Pour le prototype : texte direct.
        """
        # Détecter si c'est une action téléphone
        intent = self.pipeline._detect_intent(text)
        
        if intent.type == 'action':
            # Router vers le bus téléphonique
            result = self.phone.route_intent(text)
            self.state.total_actions += 1
            
            for cb in self._on_action:
                try:
                    cb(result)
                except Exception:
                    pass
            
            return result
        
        # Sinon, conversation normale
        chat_result = self.chat(text)
        return chat_result.to_dict()
    
    def dispatch_background(self, text: str) -> str:
        """
        Lance une tâche en arrière-plan.
        
        Exemple : « Analyse ce PDF et résume-le »
        → La tâche tourne, KA continue la conversation normalement.
        """
        task_id = str(uuid.uuid4())[:8]
        
        # En production : thread séparé
        # Pour le prototype : traitement différé
        
        self.phone.notify('task_started',
                         f"Tâche '{text[:60]}' démarrée ({task_id})")
        
        # Simuler un traitement asynchrone
        import threading
        def _bg_task():
            time.sleep(2)  # Simulation
            self.phone.notify('task_completed',
                            f"Tâche '{text[:60]}' terminée ({task_id})")
        
        t = threading.Thread(target=_bg_task, daemon=True)
        t.start()
        
        return task_id
    
    # ═══════════════════════════════════════════════════════
    # APPRENTISSAGE
    # ═══════════════════════════════════════════════════════
    
    def learn(self, fact: str, domain: str = 'personal'):
        """Apprend un fait. Équivalent de 'Rappelle-toi que...'."""
        fact_id = self.memory.remember(fact, domain=domain)
        print(f"[KACompanion] Appris: {fact[:80]}...")
        return fact_id
    
    def learn_from_conversation(self, text: str):
        """
        Apprentissage implicite depuis une conversation.
        
        Détecte automatiquement les faits à retenir.
        """
        # Patterns d'apprentissage implicite
        patterns = [
            (r"je (?:suis|m'appelle) (\w+)", 'personal'),
            (r"j'aime (.*?)(?:\.|$)", 'preferences'),
            (r"je (?:déteste|n'aime pas) (.*?)(?:\.|$)", 'preferences'),
            (r"mon (.*?) est (.*?)(?:\.|$)", 'personal'),
            (r"j'habite (?:à|au|aux) (.*?)(?:\.|$)", 'personal'),
            (r"je travaille (?:à|au|chez|dans) (.*?)(?:\.|$)", 'personal'),
        ]
        
        import re
        for pattern, domain in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                fact = m.group(0).strip('.')
                self.memory.remember(fact, domain=domain)
    
    # ═══════════════════════════════════════════════════════
    # PERSISTANCE
    # ═══════════════════════════════════════════════════════
    
    def save(self, user_id: str = None):
        """Sauvegarde tout l'état du compagnon."""
        uid = user_id or self.state.user_name or 'default'
        
        self.memory.save(uid)
        self.personality_engine.save(uid)
        
        # Sauvegarder l'état
        import pickle
        state_path = HOLOGRAM_DIR / f"companion_state_{uid}.pkl"
        with open(state_path, 'wb') as f:
            pickle.dump(self.state.to_dict(), f)
        
        print(f"[KACompanion] État sauvegardé pour '{uid}'")
        return str(HOLOGRAM_DIR)
    
    def load(self, user_id: str = None) -> bool:
        """Charge tout l'état du compagnon."""
        uid = user_id or self.state.user_name or 'default'
        
        if not self.memory.load(uid):
            print(f"[KACompanion] Aucune sauvegarde trouvée pour '{uid}'")
            return False
        
        self.personality_engine.load(uid)
        
        # Charger l'état
        import pickle
        state_path = HOLOGRAM_DIR / f"companion_state_{uid}.pkl"
        if state_path.exists():
            with open(state_path, 'rb') as f:
                saved_state = pickle.load(f)
            self.state.user_name = saved_state.get('user_name', '')
            self.state.emotion = saved_state.get('emotion', 'warm')
            self.state.personality = saved_state.get('personality', 'compagnon')
        
        print(f"[KACompanion] État chargé pour '{uid}'")
        return True
    
    # ═══════════════════════════════════════════════════════
    # CALLBACKS
    # ═══════════════════════════════════════════════════════
    
    def on_response(self, callback: Callable):
        """Enregistre un callback appelé après chaque réponse."""
        self._on_response.append(callback)
    
    def on_action(self, callback: Callable):
        """Enregistre un callback appelé après chaque action téléphone."""
        self._on_action.append(callback)
    
    def on_notification(self, callback: Callable):
        """Enregistre un callback appelé à chaque notification."""
        self._on_notification.append(callback)
    
    # ═══════════════════════════════════════════════════════
    # INFORMATIONS
    # ═══════════════════════════════════════════════════════
    
    @property
    def info(self) -> dict:
        return {
            'state': self.state.to_dict(),
            'memory': self.memory.stats,
            'personality': self.personality_engine.stats,
            'pipeline': self.pipeline.stats,
            'phone': self.phone.stats,
            'uptime_hours': (time.time() - self._created_at) / 3600,
        }
    
    def dashboard(self) -> dict:
        """Tableau de bord complet."""
        return {
            **self.info,
            'phone_dashboard': self.phone.dashboard(),
            'notifications': self.phone.get_notifications(clear=False),
        }
    
    def __repr__(self) -> str:
        return (f"KACompanion('{self.state.name}', "
                f"user='{self.state.user_name}', "
                f"personality='{self.state.personality}', "
                f"emotion='{self.state.emotion}', "
                f"session={self.state.session_duration_minutes:.0f}min)")


# ═══════════════════════════════════════════════════════════
# SCÉNARIO DE DÉMONSTRATION
# ═══════════════════════════════════════════════════════════

def demo():
    """Démonstration complète du compagnon KA."""
    print("=" * 70)
    print("  🧠 HARMONIC AI V5 — KA Companion Demo")
    print("=" * 70)
    
    # ── 1. Création du compagnon ──
    print("\n[1] Création du compagnon...")
    ka = KACompanion(name="KA", personality="compagnon", emotion="warm")
    ka.set_user("Sophie")
    print(f"    {ka}")
    
    # ── 2. Apprentissage initial ──
    print("\n[2] Apprentissage de faits initiaux...")
    ka.learn("Sophie aime le chocolat noir à 85%")
    ka.learn("Sophie habite à Paris dans le 11ème")
    ka.learn("Sophie est allergique au lactose")
    ka.learn("Paul est le frère de Sophie")
    ka.learn("Le restaurant préféré de Sophie est Le Petit Cambodge")
    ka.memory.set_user_preference("musique", "jazz")
    ka.memory.set_user_preference("couleur", "bleu")
    print(f"    {ka.memory}")
    
    # ── 3. Contacts ──
    print("\n[3] Configuration des contacts...")
    ka.phone.add_contact("Maman", phone="0601020304",
                        email="maman@famille.fr", relation="famille")
    ka.phone.add_contact("Paul", phone="0605060708",
                        relation="collègue")
    ka.phone.add_contact("Dr. Martin", phone="0102030405",
                        relation="médecin")
    print(f"    {ka.phone}")
    
    # ── 4. Conversation ──
    print("\n[4] Simulation de conversation...")
    
    conversations = [
        # --- Conversation simple ---
        ("Bonjour KA !", None),
        ("Quel est mon restaurant préféré ?", None),
        ("Où est-ce que j'habite déjà ?", None),
        
        # --- Émotion ---
        ("Je me sens un peu triste aujourd'hui...", None),
        ("Merci, ça va mieux.", None),
        
        # --- Apprentissage ---
        ("Rappelle-toi que mon anniversaire est le 15 mars", None),
        ("C'est quand mon anniversaire ?", None),
        
        # --- Action téléphone ---
        ("Appelle Maman", None),
        ("Envoie un message à Paul pour confirmer demain 14h", None),
        
        # --- Créativité ---
        ("Raconte-moi une courte histoire", None),
        
        # --- Fin de journée ---
        ("Bonne nuit KA", None),
    ]
    
    for text, ctx in conversations:
        result = ka.chat(text, context=ctx)
        print(f"\n  👤 Sophie: {text}")
        print(f"  🤖 KA:     {result.response}")
        print(f"     [{result.intent.type}] émotion={result.emotion_response} "
              f"cohérence={result.confidence:.3f} ⏱{result.latency_ms:.1f}ms")
    
    # ── 5. Dashboard ──
    print(f"\n[5] Dashboard...")
    dash = ka.dashboard()
    for k, v in dash.items():
        if isinstance(v, dict):
            print(f"    {k}:")
            for k2, v2 in v.items():
                if not isinstance(v2, (list, dict)):
                    print(f"      {k2}: {v2}")
        elif not isinstance(v, list):
            print(f"    {k}: {v}")
    
    # ── 6. Sauvegarde ──
    print("\n[6] Sauvegarde de l'état...")
    save_path = ka.save("sophie")
    print(f"    Sauvegardé dans: {save_path}")
    
    # ── 7. Restauration ──
    print("\n[7] Test de restauration...")
    ka2 = KACompanion(name="KA")
    loaded = ka2.load("sophie")
    print(f"    Chargé: {loaded}")
    print(f"    {ka2}")
    
    # Vérifier que les connaissances persistent
    result = ka2.chat("Quel est mon restaurant préféré ?")
    print(f"\n  👤 Test:  Quel est mon restaurant préféré ?")
    print(f"  🤖 KA:    {result.response}")
    print(f"     [{result.intent.type}] cohérence={result.confidence:.3f}")
    
    # ── 8. Résumé ──
    print("\n" + "=" * 70)
    print("  ✅ Démo KA Companion terminée")
    print("=" * 70)
    print(f"  Conversations: {ka.state.total_conversations}")
    print(f"  Faits en mémoire: {ka.memory.store._total_facts}")
    print(f"  Personnalité: {ka.state.personality}")
    print(f"  Émotion: {ka.state.emotion}")
    print(f"  Contacts: {len(ka.phone.contacts)}")
    print(f"  Messages: {len(ka.phone.messages)}")
    print(f"  Rappels: {len(ka.phone.reminders)}")
    print(f"  Uptime: {ka.state.session_duration_minutes:.1f} min")
    print()

    return ka


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    demo()