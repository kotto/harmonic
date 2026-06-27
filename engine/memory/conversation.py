"""
Conversation Memory — Historique de session avec signatures harmoniques.
========================================================================
"""

import json
import time
import logging
import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Un message dans l'historique de conversation."""
    role: str  # user, assistant, system
    content: str
    category: Optional[str] = None
    harmonic_signature: Optional[List[float]] = None
    resonance_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    token_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "category": self.category,
            "resonance_score": round(self.resonance_score, 4),
            "timestamp": self.timestamp,
        }


class ConversationMemory:
    """
    Memoire de conversation avec signatures harmoniques.
    
    Usage:
        mem = ConversationMemory(max_messages=100)
        mem.add("user", "Calculez 15% de 340")
        mem.add("assistant", "Pour calculer 15%...", category="mathematical")
        
        # Recuperer le contexte
        ctx = mem.get_context(max_tokens=2000)
        print(ctx)
        
        # Stats
        print(mem.get_stats())
    """
    
    def __init__(self, max_messages: int = 100, session_id: Optional[str] = None):
        self.max_messages = max_messages
        self.session_id = session_id or f"session_{int(time.time())}"
        self.messages: List[ConversationMessage] = []
        self.created_at = datetime.now().isoformat()
        
        # Stats
        self.stats = {
            "total_messages": 0,
            "tokens_used": 0,
            "categories": {},
            "avg_resonance": 0.0,
        }
    
    def add(self, role: str, content: str, category: Optional[str] = None,
            harmonic_signature: Optional[List[float]] = None,
            resonance_score: float = 0.0) -> ConversationMessage:
        """Ajoute un message a l'historique."""
        msg = ConversationMessage(
            role=role,
            content=content,
            category=category,
            harmonic_signature=harmonic_signature,
            resonance_score=resonance_score,
            token_count=len(content) // 4 + 1,  # Estimation
        )
        
        self.messages.append(msg)
        self.stats["total_messages"] += 1
        self.stats["tokens_used"] += msg.token_count
        
        if category:
            self.stats["categories"][category] = self.stats["categories"].get(category, 0) + 1
        
        self._update_avg_resonance()
        
        # Eviction si trop de messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        return msg
    
    def get_context(self, max_tokens: int = 2000) -> str:
        """
        Construit le contexte de conversation pour le LLM.
        Utilise l'eviction harmonique (messages a haute resonance conserves).
        """
        if not self.messages:
            return ""
        
        # Trier les messages par score de resonance (decroissant)
        # mais garder l'ordre chronologique pour les plus recents
        context_parts = []
        tokens_used = 0
        
        # D'abord les messages recents (ordre chronologique inverse)
        recent_window = min(10, len(self.messages))
        recent_msgs = self.messages[-recent_window:]
        
        # Messages plus anciens mais a haute resonance
        older_msgs = self.messages[:-recent_window] if len(self.messages) > recent_window else []
        older_msgs.sort(key=lambda m: m.resonance_score, reverse=True)
        older_msgs = older_msgs[:5]  # Garder max 5 anciens
        
        # Assemblage
        all_msgs = older_msgs + recent_msgs
        all_msgs.sort(key=lambda m: m.timestamp)  # Re-trier chronologiquement
        
        for msg in all_msgs:
            msg_text = f"{msg.role.upper()}: {msg.content}\n"
            tokens = len(msg_text) // 4 + 1
            
            if tokens_used + tokens > max_tokens:
                break
            
            context_parts.append(msg_text)
            tokens_used += tokens
        
        return "\n".join(context_parts)
    
    def get_context_messages(self, max_tokens: int = 2000) -> List[Dict]:
        """Retourne les messages au format liste (pour API OpenAI/Anthropic)."""
        if not self.messages:
            return []
        
        recent = self.messages[-min(20, len(self.messages)):]
        
        messages = []
        tokens_used = 0
        
        for msg in recent:
            tokens = len(msg.content) // 4 + 1
            if tokens_used + tokens > max_tokens:
                break
            
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })
            tokens_used += tokens
        
        return messages
    
    def _update_avg_resonance(self):
        """Met a jour la moyenne des scores de resonance."""
        scores = [m.resonance_score for m in self.messages if m.resonance_score > 0]
        if scores:
            self.stats["avg_resonance"] = round(sum(scores) / len(scores), 4)
    
    def get_stats(self) -> Dict:
        """Stats de la session."""
        return {
            "session_id": self.session_id,
            "total_messages": self.stats["total_messages"],
            "tokens_used": self.stats["tokens_used"],
            "categories": self.stats["categories"],
            "avg_resonance": self.stats["avg_resonance"],
            "created_at": self.created_at,
            "last_message": self.messages[-1].timestamp if self.messages else None,
        }
    
    def clear(self):
        """Vide l'historique."""
        self.messages = []
        self.stats["total_messages"] = 0
        self.stats["tokens_used"] = 0
        self.stats["categories"] = {}
        self.stats["avg_resonance"] = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages[-10:]],  # Derniers 10
            "stats": self.get_stats(),
        }
