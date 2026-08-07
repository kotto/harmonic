"""
LLM Backend — Interface multi-providers pour l'intelligence réelle
==================================================================
Connecte le moteur harmonique aux LLM (GPT-4, Claude, Mistral, local).

Architecture:
    LLMInterface (abstract)
    ├── OpenAILLM      → GPT-4, GPT-3.5, DeepSeek, Qwen
    ├── AnthropicLLM   → Claude 3/4
    ├── MistralLLM     → Mistral Large/Mixtral
    ├── LocalLLM       → llama.cpp / transformers (HuggingFace)
    └── HarmonicLLM   → Routeur intelligent avec fallback harmonique

Le routeur HarmonicLLM utilise les signatures 9D pour choisir
le meilleur provider et configurer les paramètres automatiquement.
"""

from .base import LLMInterface, LLMResponse, LLMConfig
from .openai_client import OpenAILLM
from .anthropic_client import AnthropicLLM
from .mistral_client import MistralLLM
from .local_llm import LocalLLM
from .router import HarmonicLLM
from .open_router import HarmonicOpenRouter, detect_machine, estimate_model_size
from .deepseek_styler import DeepSeekStyleFormatter, get_styler, polish_response

__all__ = [
    'LLMInterface', 'LLMResponse', 'LLMConfig',
    'OpenAILLM', 'AnthropicLLM', 'MistralLLM', 'LocalLLM',
    'HarmonicLLM',
    'HarmonicOpenRouter', 'detect_machine', 'estimate_model_size',
    'DeepSeekStyleFormatter', 'get_styler', 'polish_response',
]
