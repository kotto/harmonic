"""
User Profile — Profils utilisateur avec preferences et signatures harmoniques.
==============================================================================
"""

import json
import time
import logging
import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class UserPreference:
    """Preference utilisateur."""
    key: str
    value: Any
    category: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "created_at": self.created_at,
        }


class UserProfile:
    """
    Profil utilisateur avec signatures harmoniques personnalisees.
    
    Usage:
        profile = UserProfile(user_id="alain")
        profile.update_preference("language", "fr")
        profile.update_preference("model", "claude-3-opus")
        
        # Enregistrer une signature harmonique
        profile.record_interaction("mathematical", resonance_score=0.85)
        
        # Obtenir le profil optimise
        config = profile.get_optimized_config()
        print(config)
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.preferences: Dict[str, UserPreference] = {}
        self.interaction_history: List[Dict] = []
        self.category_preferences: Dict[str, float] = {}
        self.created_at = datetime.now().isoformat()
        self.last_active = self.created_at
        
        # Default preferences
        self._init_defaults()
    
    def _init_defaults(self):
        """Preferences par defaut."""
        defaults = {
            "language": "fr",
            "model": "auto",
            "temperature": 0.7,
            "max_tokens": 2048,
            "style": "standard",
            "context_length": 2000,
        }
        for key, value in defaults.items():
            self.preferences[key] = UserPreference(key=key, value=value)
    
    def update_preference(self, key: str, value: Any, category: Optional[str] = None):
        """Met a jour une preference."""
        self.preferences[key] = UserPreference(
            key=key,
            value=value,
            category=category,
        )
        self.last_active = datetime.now().isoformat()
    
    def get_preference(self, key: str, default=None):
        """Recupere une preference."""
        pref = self.preferences.get(key)
        return pref.value if pref else default
    
    def record_interaction(self, category: str, resonance_score: float = 0.0,
                           model: str = "", latency_ms: float = 0.0):
        """Enregistre une interaction utilisateur."""
        self.interaction_history.append({
            "category": category,
            "resonance_score": resonance_score,
            "model": model,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Mettre a jour les preferences de categorie
        if category:
            current = self.category_preferences.get(category, 0.0)
            # Moyenne glissante
            self.category_preferences[category] = current * 0.7 + resonance_score * 0.3
        
        self.last_active = datetime.now().isoformat()
    
    def get_optimized_config(self) -> Dict:
        """
        Genere une configuration optimisee pour ce user.
        Combine les preferences explicites et implicites.
        """
        # Categorie preferee
        preferred_category = max(
            self.category_preferences,
            key=self.category_preferences.get,
        ) if self.category_preferences else "general"
        
        # Ajuster la temperature selon les preferences
        base_temp = self.get_preference("temperature", 0.7)
        
        # Ajuster selon l'historique
        if len(self.interaction_history) > 10:
            avg_latency = np.mean([h["latency_ms"] for h in self.interaction_history])
            if avg_latency > 5000:  # Si lent, reduire max_tokens
                base_temp = min(base_temp, 0.5)
        
        return {
            "user_id": self.user_id,
            "language": self.get_preference("language", "fr"),
            "model": self.get_preference("model", "auto"),
            "temperature": round(base_temp, 2),
            "max_tokens": self.get_preference("max_tokens", 2048),
            "style": self.get_preference("style", "standard"),
            "context_length": self.get_preference("context_length", 2000),
            "preferred_category": preferred_category,
            "top_categories": dict(sorted(
                self.category_preferences.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]),
            "total_interactions": len(self.interaction_history),
            "last_active": self.last_active,
        }
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "preferences": {k: v.to_dict() for k, v in self.preferences.items()},
            "category_preferences": self.category_preferences,
            "total_interactions": len(self.interaction_history),
            "created_at": self.created_at,
            "last_active": self.last_active,
        }
