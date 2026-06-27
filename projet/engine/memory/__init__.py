"""
Memory Engine — Memoire persistante pour conversations et profils utilisateurs.
================================================================================
Stocke l'historique des conversations, les preferences utilisateur,
et les patterns de resonance pour l'adaptation continue.

Composants:
    - ConversationMemory → Historique de sessions avec contexte harmonique
    - UserProfile         → Profils utilisateur avec preferences et signatures
    - LongTermMemory      → Memoire a long terme avec oubli harmonique
"""

from .conversation import ConversationMemory, ConversationMessage
from .user_profile import UserProfile, UserPreference
from .long_term import LongTermMemory

__all__ = [
    'ConversationMemory', 'ConversationMessage',
    'UserProfile', 'UserPreference',
    'LongTermMemory',
]
