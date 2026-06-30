"""
Interface de base pour les providers LLM.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime


@dataclass
class LLMConfig:
    """Configuration d'appel LLM."""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: Optional[float] = None  # None = ne pas envoyer (conflit avec temperature sur Claude 4+)
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    timeout: int = 30


@dataclass
class LLMResponse:
    """Reponse standardisee d'un LLM."""
    content: str
    model: str
    provider: str
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=lambda: {
        "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0
    })
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None
    harmonic_signature: Optional[List[float]] = None
    category: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class LLMInterface(ABC):
    """
    Interface abstraite pour tous les providers LLM.
    
    Tous les providers doivent implementer :
    - generate(prompt, config) → LLMResponse
    - stream(prompt, config) → Generator[LLMResponse]
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._stats = {"calls": 0, "tokens": 0, "errors": 0, "latency_sum": 0.0}
    
    @abstractmethod
    def generate(self, prompt: str, config: Optional[LLMConfig] = None) -> LLMResponse:
        """Generation synchrone."""
        pass
    
    @abstractmethod
    def stream(self, prompt: str, config: Optional[LLMConfig] = None):
        """Generation en streaming (generator)."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Stats du provider."""
        avg_latency = self._stats["latency_sum"] / max(self._stats["calls"], 1)
        return {
            **self._stats,
            "avg_latency_ms": round(avg_latency, 2),
            "error_rate": round(self._stats["errors"] / max(self._stats["calls"], 1) * 100, 2),
        }
