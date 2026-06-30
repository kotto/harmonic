"""
Routeur Harmonique — Selection intelligente du meilleur provider LLM.
=====================================================================
Utilise les signatures 9D pour choisir le LLM optimal et les parametres.

Logique de routage:
    - mathematique/code  → DeepSeek (bon en raisonnement) ou GPT-4
    - creative/emotion   → Claude (bon en creativite) ou Mistral
    - factual            → GPT-4 (bon en precision)
    - reasoning          → Claude (bon en analyse) ou DeepSeek
    - general/simple     → GPT-3.5 (rapide, economique) ou Mixtral
    - offline/confidentiel → LocalLLM (tinyllama, phi-2)
"""

import os
import time
import logging
from typing import Optional, Tuple, List
from dataclasses import dataclass, field

from .base import LLMInterface, LLMResponse, LLMConfig
from .openai_client import OpenAILLM
from .anthropic_client import AnthropicLLM
from .mistral_client import MistralLLM
from .local_llm import LocalLLM

logger = logging.getLogger(__name__)


# Configuration des routes par categorie
ROUTING_TABLE = {
    "mathematical": {
        "primary": "deepseek-reasoner",
        "fallback": "deepseek-chat",
        "config_override": {"temperature": 0.3, "max_tokens": 4096}
    },
    "code": {
        "primary": "deepseek-chat",
        "fallback": "gpt-3.5-turbo",
        "config_override": {"temperature": 0.2, "max_tokens": 4096}
    },
    "creative": {
        "primary": "deepseek-chat",        # DeepSeek bon en creativite aussi
        "fallback": "claude-3-5-sonnet-20241022",
        "config_override": {"temperature": 0.85, "max_tokens": 2048}
    },
    "reasoning": {
        "primary": "deepseek-reasoner",
        "fallback": "claude-3-opus-20240229",
        "config_override": {"temperature": 0.5, "max_tokens": 2048}
    },
    "factual": {
        "primary": "claude-haiku-4-5-20251001",
        "fallback": "claude-sonnet-4-6",
        "config_override": {"temperature": 0.2, "max_tokens": 1024}
    },
    "general": {
        "primary": "claude-haiku-4-5-20251001",
        "fallback": "claude-sonnet-4-6",
        "config_override": {"temperature": 0.7, "max_tokens": 512}
    },
}


class HarmonicLLM:
    """
    Routeur LLM intelligent guide par les signatures harmoniques.
    
    Usage:
        llm = HarmonicLLM()
        resp = llm.generate("Calculez 15% de 340", category="mathematical")
        
        # Auto-detect de la categorie via le moteur harmonique
        resp = llm.generate_auto("Explique la relativite")
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._providers: dict = {}
        self._stats = {"total_calls": 0, "fallbacks": 0, "errors": 0}
        
        # Integration optionnelle avec le moteur harmonique
        self._harmonic_engine = None
    
    def _get_provider(self, name: str) -> LLMInterface:
        """Cree ou recupere un provider par nom."""
        if name not in self._providers:
            if "deepseek" in name.lower():
                cfg = LLMConfig(
                    model=name,
                    api_key=os.environ.get("DEEPSEEK_API_KEY"),
                    api_base="https://api.deepseek.com/v1",
                )
                self._providers[name] = OpenAILLM(cfg)

            elif "qwen" in name.lower():
                cfg = LLMConfig(
                    model=name,
                    api_key=os.environ.get("QWEN_API_KEY"),
                    api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                )
                self._providers[name] = OpenAILLM(cfg)

            elif "claude" in name.lower() or "opus" in name.lower() or "sonnet" in name.lower():
                cfg = LLMConfig(
                    model=name,
                    api_key=os.environ.get("ANTHROPIC_API_KEY"),
                )
                self._providers[name] = AnthropicLLM(cfg)

            elif "mistral" in name.lower() or "mixtral" in name.lower():
                cfg = LLMConfig(
                    model=name,
                    api_key=os.environ.get("MISTRAL_API_KEY"),
                )
                self._providers[name] = MistralLLM(cfg)

            elif "gpt" in name.lower() or "openai" in name.lower():
                cfg = LLMConfig(
                    model=name,
                    api_key=os.environ.get("OPENAI_API_KEY"),
                )
                self._providers[name] = OpenAILLM(cfg)

            else:
                # Fallback: essayer en OpenAI (compatible)
                cfg = LLMConfig(
                    model=name,
                    api_key=os.environ.get("OPENAI_API_KEY"),
                )
                self._providers[name] = OpenAILLM(cfg)
        
        return self._providers[name]
    
    def _get_route(self, category: str) -> Tuple[str, dict]:
        """Determine le meilleur modele et ses parametres pour une categorie."""
        route = ROUTING_TABLE.get(category, ROUTING_TABLE["general"])
        
        # Verifier si la cle API du provider primaire existe
        primary = route["primary"]
        primary_api_key = None
        
        if "deepseek" in primary.lower():
            primary_api_key = os.environ.get("DEEPSEEK_API_KEY")
        elif "claude" in primary.lower() or "sonnet" in primary.lower():
            primary_api_key = os.environ.get("ANTHROPIC_API_KEY")
        elif "mistral" in primary.lower():
            primary_api_key = os.environ.get("MISTRAL_API_KEY")
        elif "gpt" in primary.lower():
            primary_api_key = os.environ.get("OPENAI_API_KEY")
        
        if primary_api_key:
            selected = primary
            self._stats["total_calls"] += 1
        else:
            selected = route["fallback"]
            self._stats["fallbacks"] += 1
            logger.info(f"Fallback: {primary} -> {selected} (cle API manquante)")
        
        return selected, route["config_override"]
    
    def _connect_harmonic_engine(self):
        """Connecte le routeur au moteur harmonique pour l'auto-classification."""
        if self._harmonic_engine is None:
            try:
                from ..harmonic_engine import HarmonicResonanceEngine
                self._harmonic_engine = HarmonicResonanceEngine()
            except ImportError:
                pass
    
    def generate(self, prompt: str, category: str = "general",
                 config: Optional[LLMConfig] = None) -> LLMResponse:
        """
        Genere une reponse via le meilleur LLM pour la categorie donnee.
        
        Args:
            prompt: Question ou instruction
            category: Categorie harmonique (mathematical, creative, code...)
            config: Configuration optionnelle (override)
        
        Returns:
            LLMResponse avec le contenu genere
        """
        model, override = self._get_route(category)
        
        # Fusionner les configs
        cfg = LLMConfig(**{**self.config.__dict__, **override})
        if config:
            cfg = LLMConfig(**{**cfg.__dict__, **config.__dict__})
        cfg.model = model
        
        # Ajouter un system prompt harmonique si non fourni
        if not cfg.system_prompt:
            cfg.system_prompt = self._build_system_prompt(category)
        
        # Generer
        provider = self._get_provider(model)
        start = time.time()
        resp = provider.generate(prompt, cfg)
        latency = (time.time() - start) * 1000
        
        # Enrichir la reponse
        resp.category = category
        
        return resp
    
    def generate_auto(self, prompt: str, config: Optional[LLMConfig] = None) -> LLMResponse:
        """
        Genere une reponse avec detection automatique de la categorie.
        Utilise le moteur harmonique pour classifier le prompt.
        """
        self._connect_harmonic_engine()
        
        if self._harmonic_engine:
            cat, conf = self._harmonic_engine.classify(prompt)
            category = cat if conf > 0.15 else "general"
        else:
            category = "general"
        
        return self.generate(prompt, category, config)
    
    def _build_system_prompt(self, category: str) -> str:
        """Construit un system prompt harmonique adapte a la categorie."""
        prompts = {
            "mathematical": (
                "Tu es un assistant mathematique harmonique. "
                "Resous les problemes etape par etape. "
                "Utilise la precision et la rigueur. "
                f"Nombre d'or φ = 1.618 optimise tes calculs."
            ),
            "code": (
                "Tu es un assistant de programmation harmonique. "
                "Genere du code propre, documente et efficace. "
                "Explique ta logique. "
                "Utilise les principes SOLID et les design patterns."
            ),
            "creative": (
                "Tu es un assistant creatif harmonique. "
                "Laisse libre cours a ton imagination. "
                "Utilise des metaphors, des images poetiques. "
                "La beaute est dans la resonance des idees."
            ),
            "reasoning": (
                "Tu es un assistant de raisonnement harmonique. "
                "Analyse les problemes en profondeur. "
                "Structure ta pensee comme une resonance cognitive. "
                "Chaque etape est une onde qui enrichit la reflexion."
            ),
            "factual": (
                "Tu es un assistant factuel harmonique. "
                "Precise et veridique. Cite tes sources. "
                "Zero hallucination garanti. "
                "Base tes reponses sur des faits etablis."
            ),
            "general": (
                "Tu es un assistant IA harmonique. "
                "Reponds de maniere naturelle, utile et precise. "
                f"φ = 1.618 guide l'harmonie de nos echanges."
            ),
        }
        return prompts.get(category, prompts["general"])
    
    def stream(self, prompt: str, category: str = "general",
               config: Optional[LLMConfig] = None):
        """Generation en streaming."""
        model, override = self._get_route(category)
        cfg = LLMConfig(**{**self.config.__dict__, **override})
        if config:
            cfg = LLMConfig(**{**cfg.__dict__, **config.__dict__})
        cfg.model = model
        
        provider = self._get_provider(model)
        yield from provider.stream(prompt, cfg)
    
    def get_stats(self) -> dict:
        """Stats du routeur."""
        provider_stats = {}
        for name, provider in self._providers.items():
            provider_stats[name] = provider.get_stats()
        
        return {
            **self._stats,
            "providers": provider_stats,
            "available_providers": list(self._providers.keys()),
        }
    
    @property
    def available_keys(self) -> dict:
        """Verifie quelles cles API sont disponibles."""
        return {
            "openai": bool(os.environ.get("OPENAI_API_KEY")),
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "deepseek": bool(os.environ.get("DEEPSEEK_API_KEY")),
            "mistral": bool(os.environ.get("MISTRAL_API_KEY")),
            "qwen": bool(os.environ.get("QWEN_API_KEY")),
        }
