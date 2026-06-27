"""
Client Anthropic (Claude 3/4).
"""

import os
import time
import logging
from typing import Optional, Generator
from .base import LLMInterface, LLMResponse, LLMConfig

logger = logging.getLogger(__name__)


class AnthropicLLM(LLMInterface):
    """
    Client Anthropic pour Claude 3/4.
    
    Usage:
        llm = AnthropicLLM(LLMConfig(model="claude-3-opus-20240229"))
        resp = llm.generate("Explique la relativite")
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        super().__init__(config)
        if not self.config.api_key:
            self.config.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.config.api_base:
            self.config.api_base = "https://api.anthropic.com/v1"
    
    def generate(self, prompt: str, config: Optional[LLMConfig] = None) -> LLMResponse:
        """Generation synchrone via API Anthropic."""
        cfg = config or self.config
        
        try:
            import anthropic
            client = anthropic.Anthropic(
                api_key=cfg.api_key,
                base_url=cfg.api_base,
            )
        except ImportError:
            return self._http_fallback(prompt, cfg)
        
        start = time.time()
        try:
            system = cfg.system_prompt or ""
            
            resp = client.messages.create(
                model=cfg.model,
                max_tokens=cfg.max_tokens,
                temperature=cfg.temperature,
                top_p=cfg.top_p,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            latency = (time.time() - start) * 1000
            
            content = resp.content[0].text if resp.content else ""
            usage = resp.usage
            
            self._stats["calls"] += 1
            self._stats["tokens"] += (usage.input_tokens + usage.output_tokens) if usage else 0
            self._stats["latency_sum"] += latency
            
            return LLMResponse(
                content=content,
                model=cfg.model,
                provider="anthropic",
                finish_reason=resp.stop_reason or "stop",
                usage={
                    "prompt_tokens": usage.input_tokens if usage else 0,
                    "completion_tokens": usage.output_tokens if usage else 0,
                    "total_tokens": (usage.input_tokens + usage.output_tokens) if usage else 0,
                },
                latency_ms=latency,
            )
        except Exception as e:
            self._stats["calls"] += 1
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=cfg.model, provider="anthropic",
                error=str(e),
            )
    
    def _http_fallback(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Fallback HTTP direct."""
        import requests
        
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if config.system_prompt:
            payload["system"] = config.system_prompt
        
        start = time.time()
        try:
            resp = requests.post(
                f"{config.api_base}/messages",
                headers=headers,
                json=payload,
                timeout=config.timeout,
            )
            latency = (time.time() - start) * 1000
            
            if resp.status_code != 200:
                return LLMResponse(
                    content="", model=config.model, provider="anthropic",
                    error=f"HTTP {resp.status_code}",
                    latency_ms=latency,
                )
            
            data = resp.json()
            content = data["content"][0]["text"]
            usage = data.get("usage", {})
            
            self._stats["calls"] += 1
            self._stats["tokens"] += usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            self._stats["latency_sum"] += latency
            
            return LLMResponse(
                content=content,
                model=config.model,
                provider="anthropic",
                finish_reason=data.get("stop_reason", "stop"),
                usage={
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                },
                latency_ms=latency,
            )
        except Exception as e:
            self._stats["calls"] += 1
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=config.model, provider="anthropic",
                error=str(e),
            )
    
    def stream(self, prompt: str, config: Optional[LLMConfig] = None):
        """Generation en streaming."""
        # Pour l'instant, fallback sur generate
        yield self.generate(prompt, config)
