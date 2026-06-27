"""
Client OpenAI / compatible (GPT-4, GPT-3.5, DeepSeek, Qwen).
"""

import os
import time
import json
import logging
from typing import Optional, Generator
from .base import LLMInterface, LLMResponse, LLMConfig

logger = logging.getLogger(__name__)


class OpenAILLM(LLMInterface):
    """
    Client OpenAI (ou compatible) avec fallback sur plusieurs modeles.
    
    Usage:
        llm = OpenAILLM(LLMConfig(model="gpt-4", api_key="sk-..."))
        resp = llm.generate("Explique la relativite")
        print(resp.content)
    
    Providers supportes:
        - OpenAI: gpt-4, gpt-4-turbo, gpt-3.5-turbo
        - DeepSeek: deepseek-chat, deepseek-reasoner
        - Qwen: qwen-max, qwen-plus
        - Tous les providers compatibles OpenAI API
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        super().__init__(config)
        self._client = None
        
        # Auto-detect API key
        if not self.config.api_key:
            self.config.api_key = (
                os.environ.get("OPENAI_API_KEY") or
                os.environ.get("DEEPSEEK_API_KEY") or
                os.environ.get("QWEN_API_KEY") or
                None
            )
        
        # Auto-detect API base
        if not self.config.api_base:
            if "deepseek" in self.config.model.lower():
                self.config.api_base = "https://api.deepseek.com/v1"
            elif "qwen" in self.config.model.lower():
                self.config.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            else:
                self.config.api_base = "https://api.openai.com/v1"
    
    def _get_client(self):
        """Lazy init du client OpenAI."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.api_base,
                    timeout=self.config.timeout,
                )
            except ImportError:
                # Fallback: requete HTTP directe via requests
                self._client = None
        return self._client
    
    def _http_fallback(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Fallback HTTP si openai package non installe."""
        import requests
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
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
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
        }
        
        if config.stop_sequences:
            payload["stop"] = config.stop_sequences
        
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
                    content="", model=config.model, provider="openai",
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
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
                provider="openai",
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
                content="", model=config.model, provider="openai",
                error=str(e),
            )
    
    def generate(self, prompt: str, config: Optional[LLMConfig] = None) -> LLMResponse:
        """Generation synchrone via API OpenAI-compatible."""
        cfg = config or self.config
        client = self._get_client()
        
        if client is None:
            return self._http_fallback(prompt, cfg)
        
        messages = []
        if cfg.system_prompt:
            messages.append({"role": "system", "content": cfg.system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        start = time.time()
        try:
            resp = client.chat.completions.create(
                model=cfg.model,
                messages=messages,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                top_p=cfg.top_p,
                frequency_penalty=cfg.frequency_penalty,
                presence_penalty=cfg.presence_penalty,
                stop=cfg.stop_sequences,
            )
            latency = (time.time() - start) * 1000
            
            choice = resp.choices[0]
            usage = resp.usage
            
            self._stats["calls"] += 1
            self._stats["tokens"] += (usage.total_tokens if usage else 0)
            self._stats["latency_sum"] += latency
            
            return LLMResponse(
                content=choice.message.content or "",
                model=cfg.model,
                provider="openai",
                finish_reason=choice.finish_reason or "stop",
                usage={
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "total_tokens": usage.total_tokens if usage else 0,
                },
                latency_ms=latency,
            )
        except Exception as e:
            self._stats["calls"] += 1
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=cfg.model, provider="openai",
                error=str(e),
            )
    
    def stream(self, prompt: str, config: Optional[LLMConfig] = None):
        """Generation en streaming."""
        cfg = config or self.config
        client = self._get_client()
        
        if client is None:
            yield self._http_fallback(prompt, cfg)
            return
        
        messages = []
        if cfg.system_prompt:
            messages.append({"role": "system", "content": cfg.system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        start = time.time()
        try:
            stream = client.chat.completions.create(
                model=cfg.model,
                messages=messages,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                stream=True,
            )
            
            full_content = ""
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_content += delta.content
                    yield LLMResponse(
                        content=delta.content,
                        model=cfg.model,
                        provider="openai",
                        finish_reason="streaming",
                    )
            
            latency = (time.time() - start) * 1000
            self._stats["calls"] += 1
            self._stats["tokens"] += len(full_content) // 4
            self._stats["latency_sum"] += latency
            
            yield LLMResponse(
                content="",
                model=cfg.model,
                provider="openai",
                finish_reason="stop",
                latency_ms=latency,
            )
        except Exception as e:
            self._stats["calls"] += 1
            self._stats["errors"] += 1
            yield LLMResponse(
                content="", model=cfg.model, provider="openai",
                error=str(e),
            )
