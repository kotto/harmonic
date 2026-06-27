"""
Client Mistral AI (Mistral Large, Mixtral).
"""

import os
import time
import logging
from typing import Optional, Generator
from .base import LLMInterface, LLMResponse, LLMConfig

logger = logging.getLogger(__name__)


class MistralLLM(LLMInterface):
    """
    Client Mistral AI.
    
    Usage:
        llm = MistralLLM(LLMConfig(model="mistral-large-latest"))
        resp = llm.generate("Explique la relativite")
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        super().__init__(config)
        if not self.config.api_key:
            self.config.api_key = os.environ.get("MISTRAL_API_KEY", "")
        if not self.config.api_base:
            self.config.api_base = "https://api.mistral.ai/v1"
    
    def generate(self, prompt: str, config: Optional[LLMConfig] = None) -> LLMResponse:
        """Generation synchrone via API Mistral."""
        cfg = config or self.config
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=cfg.api_key)
        except ImportError:
            return self._http_fallback(prompt, cfg)
        
        start = time.time()
        try:
            messages = []
            if cfg.system_prompt:
                messages.append({"role": "system", "content": cfg.system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            resp = client.chat.complete(
                model=cfg.model,
                messages=messages,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                top_p=cfg.top_p,
            )
            latency = (time.time() - start) * 1000
            
            choice = resp.choices[0]
            usage = resp.usage
            
            self._stats["calls"] += 1
            self._stats["tokens"] += (usage.prompt_tokens + usage.completion_tokens) if usage else 0
            self._stats["latency_sum"] += latency
            
            return LLMResponse(
                content=choice.message.content or "",
                model=cfg.model,
                provider="mistral",
                finish_reason=choice.finish_reason or "stop",
                usage={
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "total_tokens": (usage.prompt_tokens + usage.completion_tokens) if usage else 0,
                },
                latency_ms=latency,
            )
        except Exception as e:
            self._stats["calls"] += 1
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=cfg.model, provider="mistral",
                error=str(e),
            )
    
    def _http_fallback(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Fallback HTTP direct."""
        import requests
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        
        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
        }
        
        start = time.time()
        try:
            resp = requests.post(
                f"{config.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=config.timeout,
            )
            latency = (time.time() - start) * 1000
            
            if resp.status_code != 200:
                return LLMResponse(
                    content="", model=config.model, provider="mistral",
                    error=f"HTTP {resp.status_code}",
                    latency_ms=latency,
                )
            
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            
            self._stats["calls"] += 1
            self._stats["tokens"] += usage.get("total_tokens", 0)
            self._stats["latency_sum"] += latency
            
            return LLMResponse(
                content=choice["message"]["content"],
                model=config.model,
                provider="mistral",
                finish_reason=choice.get("finish_reason", "stop"),
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                latency_ms=latency,
            )
        except Exception as e:
            self._stats["calls"] += 1
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=config.model, provider="mistral",
                error=str(e),
            )
    
    def stream(self, prompt: str, config: Optional[LLMConfig] = None):
        yield self.generate(prompt, config)
