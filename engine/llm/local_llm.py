"""
LLM Local — Inference via transformers (HuggingFace).
"""

import os
import time
import logging
from typing import Optional, Generator
from .base import LLMInterface, LLMResponse, LLMConfig

logger = logging.getLogger(__name__)


class LocalLLM(LLMInterface):
    """
    Inference LLM locale via HuggingFace transformers.
    
    Usage:
        llm = LocalLLM(LLMConfig(model="HuggingFaceH4/zephyr-7b-beta"))
        resp = llm.generate("Explique la relativite")
    
    Modeles recommandes (sans GPU, quantifies):
        - "HuggingFaceH4/zephyr-7b-beta" (7B, bon en francais)
        - "microsoft/phi-2" (2.7B, leger)
        - "TinyLlama/TinyLlama-1.1B-Chat-v1.0" (1.1B, tres leger)
        - "google/gemma-2b-it" (2B, instruct)
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        super().__init__(config)
        self._model = None
        self._tokenizer = None
        self._device = "cpu"
        
        # Auto-detect GPU
        try:
            import torch
            if torch.cuda.is_available():
                self._device = "cuda"
                logger.info("GPU detecte pour inference locale")
        except ImportError:
            pass
    
    def _load(self):
        """Charge le modele (lazy loading)."""
        if self._model is not None:
            return
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            raise ImportError(
                "transformers non installe. "
                "Installez avec: pip install transformers torch accelerate"
            )
        
        logger.info(f"Chargement du modele local: {self.config.model}")
        start = time.time()
        
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.config.model,
            trust_remote_code=True,
        )
        
        self._model = AutoModelForCausalLM.from_pretrained(
            self.config.model,
            trust_remote_code=True,
            device_map=self._device,
            torch_dtype="auto",
            low_cpu_mem_usage=True,
        )
        
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        
        elapsed = time.time() - start
        logger.info(f"Modele charge en {elapsed:.1f}s")
    
    def generate(self, prompt: str, config: Optional[LLMConfig] = None) -> LLMResponse:
        """Generation synchrone via modele local."""
        try:
            self._load()
        except ImportError as e:
            return LLMResponse(
                content="", model=self.config.model, provider="local",
                error=str(e),
            )
        except Exception as e:
            return LLMResponse(
                content="", model=self.config.model, provider="local",
                error=f"Erreur chargement modele: {e}",
            )
        
        cfg = config or self.config
        
        # Construire le prompt avec template chat si disponible
        if self._tokenizer.chat_template:
            messages = []
            if cfg.system_prompt:
                messages.append({"role": "system", "content": cfg.system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            formatted = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            formatted = f"{cfg.system_prompt or ''}\n\nUser: {prompt}\n\nAssistant:"
        
        start = time.time()
        try:
            inputs = self._tokenizer(formatted, return_tensors="pt").to(self._device)
            
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=cfg.max_tokens,
                    temperature=cfg.temperature,
                    top_p=cfg.top_p,
                    do_sample=cfg.temperature > 0,
                    pad_token_id=self._tokenizer.pad_token_id,
                    eos_token_id=self._tokenizer.eos_token_id,
                )
            
            generated = outputs[0][inputs.input_ids.shape[1]:]
            content = self._tokenizer.decode(generated, skip_special_tokens=True)
            latency = (time.time() - start) * 1000
            
            self._stats["calls"] += 1
            self._stats["tokens"] += len(generated)
            self._stats["latency_sum"] += latency
            
            return LLMResponse(
                content=content.strip(),
                model=self.config.model,
                provider="local",
                latency_ms=latency,
            )
        except Exception as e:
            self._stats["calls"] += 1
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=self.config.model, provider="local",
                error=str(e),
            )
    
    def stream(self, prompt: str, config: Optional[LLMConfig] = None):
        yield self.generate(prompt, config)
