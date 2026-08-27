"""
HARMONIC AI V 5 — Phone Bus
============================
Bus téléphonique unifié pour le compagnon KA.

Pont entre l'agent et toutes les fonctions du téléphone :
  📞 Appels        — initier/recevoir des appels vocaux KA
  👤 Contacts      — gestion du répertoire holographique
  💬 Messages      — SMS/chat avec synthèse vocale
  ⏰ Agenda        — rappels, événements, planification
  🎤 Dictée        — commandes vocales → texte → actions
  🔔 Notifications — alertes, rappels, tâches terminées
  🔍 Recherche     — locale (fichiers, photos) + web
  📊 Dashboard     — tableau de bord du téléphone

Le matching intention → outil se fait par résonance ψ,
pas par génération de JSON (Hermes function calling).
Déterministe, zéro hallucination.

Usage :
  from phone_bus import PhoneBus

  bus = PhoneBus(memory=mem, personality=pers)
  bus.add_contact("Maman", phone="0601020304")
  bus.initiate_call("Maman", message="Coucou !")
  bus.set_reminder("Acheter du pain", "demain 9h")
"""

import math
import time
import uuid
import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import deque

import numpy as np

from config import (
    PHI, TAU, PHI_INV, DIM_PSI, PHONE_TOOLS, HOLOGRAM_DIR,
)
from core.memory_core import (
    text_to_psi, psi_resonate, MemoryCore,
)


# ═══════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════

@dataclass
class Contact:
    """Un contact du répertoire."""
    id: str = ''
    name: str = ''
    phone: str = ''
    email: str = ''
    relation: str = ''          # ami, famille, collègue, ...
    notes: str = ''
    voice_id: str = ''          # ID de la voix clonée
    created_at: float = 0.0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if self.created_at == 0.0:
            self.created_at = time.time()
    
    def to_dict(self) -> dict:
        return {
            'id': self.id, 'name': self.name, 'phone': self.phone,
            'email': self.email, 'relation': self.relation,
            'notes': self.notes, 'voice_id': self.voice_id,
        }


@dataclass
class Message:
    """Un message."""
    id: str = ''
    sender: str = ''
    recipient: str = ''
    text: str = ''
    is_voice: bool = False
    status: str = 'sent'        # draft, sent, delivered, read
    timestamp: str = ''
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')
    
    def to_dict(self) -> dict:
        return {
            'id': self.id, 'sender': self.sender,
            'recipient': self.recipient, 'text': self.text[:200],
            'is_voice': self.is_voice, 'status': self.status,
            'timestamp': self.timestamp,
        }


@dataclass
class Reminder:
    """Un rappel / événement agenda."""
    id: str = ''
    text: str = ''
    when: str = ''              # description temporelle
    notify: bool = True
    status: str = 'active'      # active, done, cancelled
    created_at: str = ''
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = time.strftime('%Y-%m-%dT%H:%M:%S')
    
    def to_dict(self) -> dict:
        return {
            'id': self.id, 'text': self.text, 'when': self.when,
            'notify': self.notify, 'status': self.status,
            'created_at': self.created_at,
        }


@dataclass
class CallRecord:
    """Un enregistrement d'appel."""
    id: str = ''
    contact: str = ''
    direction: str = 'outgoing'  # incoming, outgoing
    status: str = 'initiated'   # initiated, ringing, answered, ended, missed
    message: str = ''
    duration_s: float = 0.0
    timestamp: str = ''
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')
    
    def to_dict(self) -> dict:
        return {
            'id': self.id, 'contact': self.contact,
            'direction': self.direction, 'status': self.status,
            'message': self.message, 'duration_s': self.duration_s,
            'timestamp': self.timestamp,
        }


# ═══════════════════════════════════════════════════════════
# TOOL MATCHING PAR RÉSONANCE ψ
# ═══════════════════════════════════════════════════════════

class ToolMatcher:
    """
    Matching intention → outil par résonance harmonique.
    
    Hybride : 0.5 × résonance ψ + 0.5 × chevauchement lexical.
    Déterministe, zéro paramètre, zéro hallucination.
    """
    
    def __init__(self, dim: int = DIM_PSI):
        self.dim = dim
        self._tools: Dict[str, Dict] = {}
        self._signatures: Dict[str, np.ndarray] = {}
        
        # Charger les outils configurés
        for name, cfg in PHONE_TOOLS.items():
            self.register(name, cfg['description'], cfg['keywords'])
    
    def register(self, name: str, description: str, keywords: List[str]):
        """Enregistre un outil avec sa signature ψ."""
        self._tools[name] = {
            'name': name,
            'description': description,
            'keywords': keywords,
        }
        # Signature ψ via FNV-1a sur nom + keywords
        sig_text = name + ''.join(keywords)
        self._signatures[name] = text_to_psi(sig_text, self.dim)
    
    def match(self, intent: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Trouve les outils les plus pertinents pour une intention.
        
        Score = 0.5 × résonance ψ + 0.5 × chevauchement lexical.
        Les ψ étant quasi-orthogonaux (~0.04), le lexical est
        nécessaire pour le routage (principe P3).
        """
        intent_lower = intent.lower()
        psi_intent = text_to_psi(intent, self.dim)
        
        scores = []
        for name, psi_tool in self._signatures.items():
            tool = self._tools[name]
            
            # 1. Chevauchement lexical
            keyword_hits = 0
            for kw in tool['keywords']:
                if kw in intent_lower:
                    keyword_hits += 1
            lexical_score = keyword_hits / max(len(tool['keywords']), 1)
            
            # 2. Résonance ψ
            psi_score = (psi_resonate(psi_intent, psi_tool) + 1.0) / 2.0
            
            # Score combiné
            score = 0.5 * lexical_score + 0.5 * psi_score
            
            # Bonus si le nom de l'outil est dans l'intention
            if name in intent_lower:
                score += 0.3
            
            scores.append((name, min(1.0, score)))
        
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]
    
    def get_best_tool(self, intent: str) -> Tuple[str, float]:
        """Retourne le meilleur outil."""
        matches = self.match(intent, top_k=1)
        return matches[0] if matches else ('unknown', 0.0)
    
    @property
    def available_tools(self) -> List[str]:
        return list(self._tools.keys())


# ═══════════════════════════════════════════════════════════
# PhoneBus
# ═══════════════════════════════════════════════════════════

class PhoneBus:
    """
    Bus téléphonique unifié.
    
    Point d'entrée unique pour toutes les fonctions téléphone.
    L'agent utilise ce bus pour interagir avec le monde réel.
    """
    
    def __init__(self, memory: MemoryCore = None,
                 personality=None,
                 voice_engine=None):
        self.memory = memory
        self.personality = personality
        self.voice = voice_engine
        
        # Tool matching
        self.matcher = ToolMatcher()
        
        # Données
        self.contacts: Dict[str, Contact] = {}
        self.messages: List[Message] = []
        self.reminders: List[Reminder] = []
        self.call_log: List[CallRecord] = []
        
        # Notifications en attente
        self._notifications: deque = deque(maxlen=50)
        
        # Statistiques
        self._started_at = time.time()
    
    # ═══════════════════════════════════════════════════════
    # CONTACTS
    # ═══════════════════════════════════════════════════════
    
    def add_contact(self, name: str, phone: str = '',
                    email: str = '', relation: str = '',
                    notes: str = '') -> Contact:
        """Ajoute un contact au répertoire holographique."""
        contact = Contact(
            name=name, phone=phone, email=email,
            relation=relation, notes=notes,
        )
        self.contacts[contact.id] = contact
        
        # Mémoriser
        if self.memory:
            self.memory.remember(
                f"Contact: {name}, tél: {phone}, email: {email}, "
                f"relation: {relation}",
                domain='contacts',
            )
        
        return contact
    
    def find_contact(self, query: str) -> List[Contact]:
        """Recherche un contact par nom, téléphone, ou résonance."""
        q = query.lower()
        results = []
        
        for contact in self.contacts.values():
            # Recherche textuelle
            if (q in contact.name.lower() or
                q in contact.phone or
                q in contact.email.lower() or
                q in contact.relation.lower()):
                results.append(contact)
        
        # Si pas de résultat textuel, recherche par résonance
        if not results and self.memory:
            facts = self.memory.recall(query, top_k=3)
            for fact, score in facts:
                # Chercher le contact correspondant au fait
                for contact in self.contacts.values():
                    if contact.name.lower() in fact.text.lower():
                        if contact not in results:
                            results.append(contact)
        
        return results
    
    def get_contact(self, contact_id: str) -> Optional[Contact]:
        return self.contacts.get(contact_id)
    
    def list_contacts(self) -> List[Contact]:
        return list(self.contacts.values())
    
    def delete_contact(self, contact_id: str) -> bool:
        if contact_id in self.contacts:
            del self.contacts[contact_id]
            return True
        return False
    
    # ═══════════════════════════════════════════════════════
    # APPELS
    # ═══════════════════════════════════════════════════════
    
    def initiate_call(self, contact_name: str,
                      message: str = '') -> CallRecord:
        """Initie un appel vocal KA."""
        contacts = self.find_contact(contact_name)
        contact = contacts[0] if contacts else Contact(name=contact_name)
        
        call = CallRecord(
            contact=contact.name,
            direction='outgoing',
            status='initiated',
            message=message,
        )
        self.call_log.append(call)
        
        # Notification
        self._notifications.append({
            'type': 'call_initiated',
            'contact': contact.name,
            'timestamp': time.time(),
        })
        
        return call
    
    def answer_call(self, caller: str = 'Inconnu') -> CallRecord:
        """Répond à un appel entrant."""
        call = CallRecord(
            contact=caller,
            direction='incoming',
            status='answered',
        )
        self.call_log.append(call)
        return call
    
    def end_call(self, call_id: str) -> bool:
        for call in self.call_log:
            if call.id == call_id:
                call.status = 'ended'
                call.duration_s = time.time() - time.mktime(
                    time.strptime(call.timestamp, '%Y-%m-%dT%H:%M:%S')
                ) if call.timestamp else 0
                return True
        return False
    
    # ═══════════════════════════════════════════════════════
    # MESSAGES
    # ═══════════════════════════════════════════════════════
    
    def send_message(self, recipient: str, text: str,
                     as_voice: bool = False) -> Message:
        """Envoie un message (texte ou vocal)."""
        # Trouver le contact
        contacts = self.find_contact(recipient)
        contact_name = contacts[0].name if contacts else recipient
        
        msg = Message(
            sender='KA',
            recipient=contact_name,
            text=text,
            is_voice=as_voice,
            status='sent',
        )
        self.messages.append(msg)
        
        # Mémoriser
        if self.memory:
            self.memory.remember(
                f"Message envoyé à {contact_name}: {text[:100]}",
                domain='conversations',
            )
        
        # Notification
        self._notifications.append({
            'type': 'message_sent',
            'recipient': contact_name,
            'timestamp': time.time(),
        })
        
        return msg
    
    def receive_message(self, sender: str, text: str) -> Message:
        """Reçoit un message (simulation)."""
        msg = Message(
            sender=sender,
            recipient='KA',
            text=text,
            status='delivered',
        )
        self.messages.append(msg)
        
        # Notification
        self._notifications.append({
            'type': 'message_received',
            'sender': sender,
            'text_preview': text[:80],
            'timestamp': time.time(),
        })
        
        return msg
    
    def get_conversation(self, contact_name: str,
                         limit: int = 20) -> List[Message]:
        """Récupère la conversation avec un contact."""
        return [m for m in self.messages
                if m.recipient == contact_name or m.sender == contact_name][-limit:]
    
    # ═══════════════════════════════════════════════════════
    # AGENDA / RAPPELS
    # ═══════════════════════════════════════════════════════
    
    def set_reminder(self, text: str, when: str = '',
                     notify: bool = True) -> Reminder:
        """Programme un rappel."""
        reminder = Reminder(
            text=text,
            when=when,
            notify=notify,
        )
        self.reminders.append(reminder)
        
        # Mémoriser
        if self.memory:
            self.memory.remember(
                f"Rappel: {text} ({when})",
                domain='personal',
            )
        
        return reminder
    
    def list_reminders(self, active_only: bool = True) -> List[Reminder]:
        if active_only:
            return [r for r in self.reminders if r.status == 'active']
        return list(self.reminders)
    
    def complete_reminder(self, reminder_id: str) -> bool:
        for r in self.reminders:
            if r.id == reminder_id:
                r.status = 'done'
                return True
        return False
    
    def cancel_reminder(self, reminder_id: str) -> bool:
        for r in self.reminders:
            if r.id == reminder_id:
                r.status = 'cancelled'
                return True
        return False
    
    # ═══════════════════════════════════════════════════════
    # NOTIFICATIONS
    # ═══════════════════════════════════════════════════════
    
    def get_notifications(self, clear: bool = False) -> List[dict]:
        """Récupère les notifications en attente."""
        notifs = list(self._notifications)
        if clear:
            self._notifications.clear()
        return notifs
    
    def notify(self, type_: str, message: str):
        """Ajoute une notification."""
        self._notifications.append({
            'type': type_,
            'message': message,
            'timestamp': time.time(),
        })
    
    # ═══════════════════════════════════════════════════════
    # DASHBOARD
    # ═══════════════════════════════════════════════════════
    
    def dashboard(self) -> dict:
        """Tableau de bord du téléphone harmonique."""
        today = time.strftime('%Y-%m-%d')
        return {
            'contacts_count': len(self.contacts),
            'messages_today': len([m for m in self.messages
                                  if m.timestamp[:10] == today]),
            'messages_total': len(self.messages),
            'reminders_active': len([r for r in self.reminders
                                    if r.status == 'active']),
            'calls_today': len([c for c in self.call_log
                               if c.timestamp[:10] == today]),
            'calls_total': len(self.call_log),
            'notifications_pending': len(self._notifications),
            'recent_messages': [m.to_dict() for m in self.messages[-5:]],
            'upcoming_reminders': [r.to_dict() for r in self.list_reminders()[:5]],
            'recent_calls': [c.to_dict() for c in self.call_log[-5:]],
        }
    
    # ═══════════════════════════════════════════════════════
    # ROUTAGE D'INTENTION → ACTION
    # ═══════════════════════════════════════════════════════
    
    def route_intent(self, intent: str, context: dict = None) -> dict:
        """
        Route une intention vers l'action téléphone appropriée.
        
        C'est le « function calling » harmonique — déterministe,
        sans génération JSON, sans hallucination.
        
        Returns:
            dict: {'tool': str, 'action': str, 'result': Any, 'confidence': float}
        """
        tool_name, confidence = self.matcher.get_best_tool(intent)
        ctx = context or {}
        
        result = {
            'tool': tool_name,
            'confidence': confidence,
            'action': None,
            'result': None,
            'handled': False,
        }
        
        if confidence < 0.2:
            result['action'] = 'low_confidence'
            return result
        
        # ── Contacts ──
        if tool_name == 'contacts':
            if any(w in intent.lower() for w in ['ajoute', 'enregistre', 'nouveau']):
                # Extraire le nom
                name = self._extract_name(intent)
                result['action'] = 'add_contact'
                result['result'] = self.add_contact(name).to_dict()
            elif any(w in intent.lower() for w in ['supprime', 'efface']):
                result['action'] = 'delete_contact'
                name = self._extract_name(intent)
                contacts = self.find_contact(name)
                if contacts:
                    self.delete_contact(contacts[0].id)
                    result['result'] = f"Contact '{name}' supprimé."
            else:
                result['action'] = 'list_contacts'
                result['result'] = [c.to_dict() for c in self.list_contacts()]
            result['handled'] = True
        
        # ── Appels ──
        elif tool_name == 'voice_call':
            name = self._extract_name(intent)
            message = ctx.get('message', '')
            result['action'] = 'initiate_call'
            result['result'] = self.initiate_call(name, message).to_dict()
            result['handled'] = True
        
        # ── Messages ──
        elif tool_name == 'message':
            recipient = self._extract_name(intent)
            text = ctx.get('text', intent)
            result['action'] = 'send_message'
            result['result'] = self.send_message(recipient, text).to_dict()
            result['handled'] = True
        
        # ── Rappels ──
        elif tool_name == 'reminder':
            text = intent
            when = self._extract_time(intent)
            result['action'] = 'set_reminder'
            result['result'] = self.set_reminder(text, when).to_dict()
            result['handled'] = True
        
        # ── Dashboard ──
        elif tool_name == 'dashboard':
            result['action'] = 'show_dashboard'
            result['result'] = self.dashboard()
            result['handled'] = True
        
        # ── Dictée ──
        elif tool_name == 'dictation':
            result['action'] = 'start_dictation'
            result['result'] = "Dictée activée. Parlez..."
            result['handled'] = True
        
        # ── Recherche ──
        elif tool_name == 'search':
            result['action'] = 'search'
            result['result'] = f"Recherche: {intent}"
            result['handled'] = True
        
        return result
    
    def _extract_name(self, text: str) -> str:
        """Extrait un nom propre d'une intention."""
        # Patterns: "appelle X", "message à X", "contact X"
        patterns = [
            r'(?:appelle|appeler|call|joindre|contacte)\s+(\w+)',
            r'(?:message|sms|texto)\s+(?:à|pour|au)\s+(\w+)',
            r'(?:ajoute|enregistre)\s+(\w+)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1)
        # Fallback: dernier mot capitalisé
        words = text.split()
        for w in reversed(words):
            if w[0].isupper() and len(w) > 1:
                return w
        return 'contact'
    
    def _extract_time(self, text: str) -> str:
        """Extrait une indication temporelle."""
        patterns = [
            r'(demain|aujourd\'hui|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s*(?:à\s*)?(\d{1,2}[h:]\d{0,2})?',
            r'dans\s+(\d+)\s*(minutes?|heures?|jours?)',
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(0)
        return ''
    
    # ═══════════════════════════════════════════════════════
    # STATISTIQUES
    # ═══════════════════════════════════════════════════════
    
    @property
    def stats(self) -> dict:
        return {
            **self.dashboard(),
            'tools_available': self.matcher.available_tools,
            'uptime_hours': (time.time() - self._started_at) / 3600,
        }
    
    def __repr__(self) -> str:
        return (f"PhoneBus(contacts={len(self.contacts)}, "
                f"messages={len(self.messages)}, "
                f"reminders={len(self.reminders)}, "
                f"calls={len(self.call_log)})")


# ═══════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("  HARMONIC AI V5 — Phone Bus Test")
    print("=" * 60)
    
    # ── Init ──
    from core.memory_core import MemoryCore
    from core.personality_engine import PersonalityEngine
    
    mem = MemoryCore()
    pers = PersonalityEngine()
    bus = PhoneBus(memory=mem, personality=pers)
    
    print(f"\n[1] Initialisation: {bus}")
    print(f"    Outils disponibles: {bus.matcher.available_tools}")
    
    # ── Test contacts ──
    print("\n[2] Gestion des contacts...")
    c1 = bus.add_contact("Maman", phone="0601020304",
                         email="maman@famille.fr", relation="famille")
    c2 = bus.add_contact("Paul", phone="0605060708",
                         relation="collègue")
    c3 = bus.add_contact("Dr. Martin", phone="0102030405",
                         relation="médecin")
    print(f"    Contacts: {bus.list_contacts().__len__()}")
    
    # Recherche
    found = bus.find_contact("maman")
    print(f"    Recherche 'maman': {[c.name for c in found]}")
    
    # ── Test messages ──
    print("\n[3] Messages...")
    msg1 = bus.send_message("Paul", "Salut Paul, on confirme demain ?")
    msg2 = bus.receive_message("Paul", "Oui, 14h ça marche !")
    print(f"    Messages: {len(bus.messages)}")
    
    # ── Test rappels ──
    print("\n[4] Rappels...")
    r1 = bus.set_reminder("Acheter du pain", "demain 9h")
    r2 = bus.set_reminder("Appeler le dentiste", "lundi 14h")
    print(f"    Rappels actifs: {len(bus.list_reminders())}")
    
    # ── Test appels ──
    print("\n[5] Appels...")
    call = bus.initiate_call("Maman", message="Bonjour Maman !")
    print(f"    Appel initié: {call.contact} → {call.status}")
    
    # ── Test routage d'intention ──
    print("\n[6] Routage d'intention → action...")
    test_intents = [
        "Appelle Maman",
        "Envoie un message à Paul",
        "Rappelle-moi d'acheter du pain demain",
        "Montre-moi mes contacts",
        "Quel est mon agenda aujourd'hui ?",
        "Cherche des informations sur la météo",
        "Ajoute le docteur Martin comme contact",
    ]
    
    for intent in test_intents:
        result = bus.route_intent(intent)
        print(f"    '{intent}'")
        print(f"      → tool={result['tool']}, action={result['action']}, "
              f"confidence={result['confidence']:.3f}")
    
    # ── Dashboard ──
    print("\n[7] Dashboard...")
    dash = bus.dashboard()
    for k, v in dash.items():
        if not isinstance(v, list):
            print(f"    {k}: {v}")
    
    print("\n✓ Phone Bus test terminé.")