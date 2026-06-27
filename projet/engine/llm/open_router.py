"""
Routeur Open Source — Selection du meilleur LLM 100% open-source
================================================================
Utilise exclusivement des modeles aux poids ouverts (MIT, Apache 2.0, Llama 2/3/4).

Principe :
    1. Tente de charger le modele localement (via transformers)
    2. Si pas assez de RAM/VRAM, utilise GGUF quantifie (via llama-cpp-python)
    3. Fallback vers API gratuite (Groq, Together AI, HuggingFace Inference)
    4. En dernier recours, modele nano (Phi-3, TinyLlama)

Modeles recommandes par categorie (mai 2026) :

    Categorie   | Modele principal          | Poids  | Licence    | RAM req.
    ------------|---------------------------|--------|------------|---------
    mathematical| Qwen2.5-32B-Instruct      | 32B    | Apache 2.0 | 64GB (Q4: 20GB)
    code        | Qwen2.5-Coder-32B-Inst.   | 32B    | Apache 2.0 | 64GB (Q4: 20GB)
    creative    | Mistral-Nemo-2407 (12B)   | 12B    | Apache 2.0 | 24GB (Q4: 8GB)
    reasoning   | DeepSeek-R1-Distill-Qwen-32B | 32B | MIT      | 64GB (Q4: 20GB)
    factual     | Qwen2.5-72B-Instruct      | 72B    | Apache 2.0 | 144GB (Q4: 40GB)
    general     | Llama-4-Scout-17B         | 17B    | Llama 4   | 34GB (Q4: 10GB)
    leger       | Phi-3.5-mini-instruct     | 3.8B   | MIT       | 8GB
    nano        | TinyLlama-1.1B-Chat       | 1.1B   | Apache 2.0| 4GB (CPU)

    Tous les modeles Q4 quantifies tiennent sur 8-20GB de RAM.

APIs gratuites compatibles (sans cle, rate-limited) :
    - HuggingFace Inference API (gratuit, models.open)
    - Groq API (cle gratuite, Llama 4, Mixtral, Gemma)
    - Together AI (cle gratuite, nombreux opensource)
"""

import os
import time
import math
import logging
import platform
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any, Generator, Callable
from datetime import datetime
from abc import ABC, abstractmethod

from .base import LLMInterface, LLMResponse, LLMConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTES HARMONIQUES
# ---------------------------------------------------------------------------
PHI = 1.618033988749895
PHI_INV = 1.0 / PHI


# ---------------------------------------------------------------------------
# ROUTING TABLE — 100% Open Source
# ---------------------------------------------------------------------------

# Modele principal + fallback pour chaque categorie
OPEN_ROUTING = {
    "mathematical": {
        "primary": "Qwen/Qwen2.5-32B-Instruct",
        "fallback": "Qwen/Qwen2.5-14B-Instruct",
        "q4_fallback": "Qwen/Qwen2.5-7B-Instruct",
        "config": {"temperature": 0.3, "max_tokens": 4096},
        "api_model": "qwen-2.5-32b",
    },
    "code": {
        "primary": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "fallback": "Qwen/Qwen2.5-Coder-14B-Instruct",
        "q4_fallback": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "config": {"temperature": 0.2, "max_tokens": 4096},
        "api_model": "qwen-2.5-coder-32b",
    },
    "creative": {
        "primary": "mistralai/Mistral-Nemo-Instruct-2407",
        "fallback": "mistralai/Mistral-7B-Instruct-v0.3",
        "q4_fallback": "microsoft/Phi-3.5-mini-instruct",
        "config": {"temperature": 0.85, "max_tokens": 2048},
        "api_model": "mistral-nemo-12b",
    },
    "reasoning": {
        "primary": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "fallback": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        "q4_fallback": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "config": {"temperature": 0.5, "max_tokens": 4096},
        "api_model": "deepseek-r1-distill-qwen-32b",
    },
    "factual": {
        "primary": "Qwen/Qwen2.5-72B-Instruct",
        "fallback": "Qwen/Qwen2.5-32B-Instruct",
        "q4_fallback": "Qwen/Qwen2.5-14B-Instruct",
        "config": {"temperature": 0.2, "max_tokens": 1024},
        "api_model": "qwen-2.5-72b",
    },
    "general": {
        "primary": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "fallback": "mistralai/Mistral-7B-Instruct-v0.3",
        "q4_fallback": "microsoft/Phi-3.5-mini-instruct",
        "config": {"temperature": 0.7, "max_tokens": 512},
        "api_model": "llama-4-scout-17b",
    },
}

# Modeles nano pour CPU-only
NANO_MODELS = {
    "general": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "leger": "microsoft/Phi-3.5-mini-instruct",
    "ultra_leger": "google/gemma-2b-it",
}

# Configuration des APIs gratuites
FREE_APIS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "models": {
            "general": "llama-3.2-90b-vision-preview",
            "code": "llama-3.3-70b-versatile",
            "creative": "mixtral-8x7b-32768",
        },
    },
    "huggingface": {
        "base_url": "https://api-inference.huggingface.co/models",
    },
}


# ---------------------------------------------------------------------------
# DETECTION DE LA CONFIG MACHINE
# ---------------------------------------------------------------------------

@dataclass
class MachineConfig:
    """Configuration detectee de la machine."""
    total_ram_gb: float = 8.0
    has_cuda: bool = False
    cuda_memory_gb: float = 0.0
    cpu_cores: int = 4
    is_windows: bool = True
    
    @property
    def available_memory_gb(self) -> float:
        """Memoire disponible estimee pour le modele."""
        if self.has_cuda and self.cuda_memory_gb > 0:
            return min(self.total_ram_gb * 0.7, self.cuda_memory_gb * 0.9)
        return self.total_ram_gb * 0.6
    
    @property
    def tier(self) -> str:
        """Tier de capacite: 'gpu_heavy', 'gpu_light', 'cpu', 'cpu_light'."""
        if self.has_cuda and self.cuda_memory_gb >= 24:
            return "gpu_heavy"    # Peut charger des 32B+
        if self.has_cuda and self.cuda_memory_gb >= 8:
            return "gpu_light"    # 7B-14B
        if self.total_ram_gb >= 32:
            return "cpu"           # 7B via GGUF
        return "cpu_light"         # Phi-3, TinyLlama


def detect_machine() -> MachineConfig:
    """Detecte automatiquement la capacite de la machine."""
    cfg = MachineConfig()
    
    # RAM
    try:
        import psutil
        cfg.total_ram_gb = psutil.virtual_memory().total / (1024**3)
    except ImportError:
        # Fallback: detection via os
        if platform.system() == "Windows":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.GlobalMemoryStatusEx(ctypes.c_buffer(64))
                # Valeur par defaut
                cfg.total_ram_gb = 8.0
            except Exception:
                pass
        elif platform.system() == "Linux":
            try:
                with open('/proc/meminfo') as f:
                    for line in f:
                        if 'MemTotal' in line:
                            cfg.total_ram_gb = int(line.split()[1]) / (1024**2)
                            break
            except Exception:
                pass
    
    # GPU (CUDA)
    try:
        import torch
        cfg.has_cuda = torch.cuda.is_available()
        if cfg.has_cuda:
            cfg.cuda_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    except ImportError:
        pass
    
    # CPU cores
    try:
        cfg.cpu_cores = os.cpu_count() or 4
    except Exception:
        pass
    
    cfg.is_windows = platform.system() == "Windows"
    
    return cfg


# ---------------------------------------------------------------------------
# PROVIDEUR LOCAL (transformers / llama-cpp)
# ---------------------------------------------------------------------------

class LocalOpenProvider(LLMInterface):
    """
    Chargement et inference de modeles open-source locaux.
    
    Supporte :
    - transformers (PyTorch) pour GPU
    - llama-cpp-python (GGUF) pour CPU/RAM limitee
    - auto-quantization si pas assez de memoire
    
    Usage:
        provider = LocalOpenProvider()
        provider.load("Qwen/Qwen2.5-7B-Instruct")
        resp = provider.generate("Question?")
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        super().__init__(config)
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self._machine = detect_machine()
        self._model_name = None
        self._use_gguf = False
        self._failed_models: set = set()
    
    def load(self, model_name: str, force_cpu: bool = False) -> bool:
        """
        Charge un modele open-source.
        
        Args:
            model_name: Nom HuggingFace (ex: "Qwen/Qwen2.5-7B-Instruct")
            force_cpu: Force le CPU meme si GPU disponible
        
        Returns:
            True si charge OK, False sinon
        """
        if self._model is not None and self._model_name == model_name:
            return True
        
        self._model_name = model_name
        logger.info(f"Chargement de {model_name}...")
        
        # Determiner la strategie de chargement
        model_size_gb = estimate_model_size(model_name)
        avail = self._machine.available_memory_gb if not force_cpu else self._machine.total_ram_gb * 0.5
        
        if self._machine.has_cuda and not force_cpu and model_size_gb * 1.2 <= avail:
            # GPU: chargement normal (transformers)
            return self._load_transformers(model_name)
        elif avail * 0.85 >= model_size_gb * 0.3:
            # CPU avec GGUF quantifie
            return self._load_gguf(model_name)
        else:
            # Trop gros pour la machine
            logger.warning(f"Modele {model_name} trop grand ({model_size_gb:.1f}GB > {avail:.1f}GB dispo)")
            return False
    
    def _load_transformers(self, model_name: str) -> bool:
        """Charge via transformers (GPU ou CPU)."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            device = "cuda" if self._machine.has_cuda else "cpu"
            
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_name, trust_remote_code=True
            )
            
            kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if device == "cuda" else torch.float32,
                "low_cpu_mem_usage": True,
            }
            
            if device == "cuda":
                kwargs["device_map"] = "auto"
            else:
                kwargs["device_map"] = {"": device}
            
            self._model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)
            
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token
            
            logger.info(f"Modele charge via transformers sur {device}")
            return True
            
        except ImportError:
            logger.warning("transformers non installe, essaie GGUF...")
            return self._load_gguf(model_name)
        except Exception as e:
            logger.warning(f"Erreur transformers: {e}, essaie GGUF...")
            return self._load_gguf(model_name)
    
    def _load_gguf(self, model_name: str) -> bool:
        """Charge via llama-cpp-python (GGUF quantifie)."""
        try:
            from llama_cpp import Llama
            
            # Mapping modele -> (org_gguf_repo, gguf_filename)
            # Les GGUF sont heberges par des contributeurs (TheBloke, bartowski, etc.)
            gguf_mapping = {
                "Qwen/Qwen2.5-7B-Instruct": ("Qwen/Qwen2.5-7B-Instruct-GGUF", "qwen2.5-7b-instruct-q4_k_m.gguf"),
                "Qwen/Qwen2.5-14B-Instruct": ("Qwen/Qwen2.5-14B-Instruct-GGUF", "qwen2.5-14b-instruct-q4_k_m.gguf"),
                "microsoft/Phi-3.5-mini-instruct": ("microsoft/Phi-3.5-mini-instruct-GGUF", "Phi-3.5-mini-instruct-Q4_K_M.gguf"),
                "TinyLlama/TinyLlama-1.1B-Chat-v1.0": ("TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF", "tinyllama-1.1b-chat-v1.0.q4_k_m.gguf"),
            }
            
            gguf_info = gguf_mapping.get(model_name)
            if not gguf_info:
                logger.warning(f"Pas de GGUF connu pour {model_name}")
                return False
            
            gguf_org, gguf_file = gguf_info
            
            # Chemin local du cache
            cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "harmonic", "gguf")
            os.makedirs(cache_dir, exist_ok=True)
            local_path = os.path.join(cache_dir, gguf_file)
            
            if not os.path.exists(local_path):
                logger.info(f"Telechargement du GGUF {gguf_file}...")
                import requests
                url = f"https://huggingface.co/{gguf_org}/resolve/main/{gguf_file}"
                response = requests.get(url, stream=True)
                response.raise_for_status()

                
                total = int(response.headers.get('content-length', 0))
                downloaded = 0
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = downloaded / total * 100
                            if int(pct) % 10 == 0:
                                logger.info(f"  Telechargement: {pct:.0f}%")
            
            # Charger le GGUF
            n_gpu_layers = -1 if self._machine.has_cuda else 0
            self._model = Llama(
                model_path=local_path,
                n_ctx=8192,
                n_gpu_layers=n_gpu_layers,
                verbose=False,
            )
            
            self._use_gguf = True
            logger.info(f"Modele GGUF charge: {gguf_file}")
            return True
            
        except ImportError:
            logger.error(
                "llama-cpp-python non installe. "
                "Installez: pip install llama-cpp-python"
            )
            return False
        except Exception as e:
            logger.error(f"Erreur chargement GGUF: {e}")
            return False
    
    def generate(self, prompt: str, config: Optional[LLMConfig] = None) -> LLMResponse:
        """Generation via le modele local."""
        if self._model is None:
            return LLMResponse(
                content="", model=self._model_name or "unknown",
                provider="local_open",
                error="Modele non charge. Appelez load() d'abord.",
            )
        
        cfg = config or self.config
        start = time.time()
        
        try:
            if self._use_gguf:
                content = self._generate_gguf(prompt, cfg)
            else:
                content = self._generate_transformers(prompt, cfg)
            
            latency = (time.time() - start) * 1000
            
            self._stats["calls"] += 1
            self._stats["latency_sum"] += latency
            
            return LLMResponse(
                content=content.strip(),
                model=self._model_name or "local",
                provider="local_open",
                latency_ms=latency,
            )
            
        except Exception as e:
            self._stats["calls"] += 1
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=self._model_name or "local",
                provider="local_open",
                error=str(e),
            )
    
    def _generate_transformers(self, prompt: str, cfg: LLMConfig) -> str:
        """Generation via transformers."""
        import torch
        
        messages = []
        if cfg.system_prompt:
            messages.append({"role": "system", "content": cfg.system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        if hasattr(self._tokenizer, 'apply_chat_template'):
            formatted = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            formatted = f"{cfg.system_prompt or ''}\n\nUser: {prompt}\n\nAssistant:"
        
        inputs = self._tokenizer(formatted, return_tensors="pt").to(
            "cuda" if self._machine.has_cuda else "cpu"
        )
        
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
        return self._tokenizer.decode(generated, skip_special_tokens=True)
    
    def _generate_gguf(self, prompt: str, cfg: LLMConfig) -> str:
        """Generation via llama-cpp-python."""
        system_msg = cfg.system_prompt or ""
        full_prompt = f"<|system|>\n{system_msg}\n</s>\n<|user|>\n{prompt}\n</s>\n<|assistant|>\n"
        
        response = self._model(
            full_prompt,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            stop=["</s>", "<|user|>", "<|assistant|>"],
        )
        
        return response["choices"][0]["text"] if response["choices"] else ""
    
    def stream(self, prompt: str, config: Optional[LLMConfig] = None):
        """Streaming (fallback: generation complete)."""
        yield self.generate(prompt, config)


# ---------------------------------------------------------------------------
# PROVIDEUR API GRATUITE (Groq, Together AI)
# ---------------------------------------------------------------------------

class FreeAPIProvider(LLMInterface):
    """
    Utilise les APIs gratuites de modeles open-source.
    
    Providers supportes :
    - Groq (cle gratuite, rate limite genereux)
    - HuggingFace Inference API (gratuit, rate-limite)
    
    Usage:
        provider = FreeAPIProvider(provider_name="groq")
        resp = provider.generate("Question?")
    """
    
    def __init__(self, provider_name: str = "groq",
                 config: Optional[LLMConfig] = None):
        super().__init__(config)
        self.provider_name = provider_name
        self._base_url = FREE_APIS[provider_name]["base_url"]
        self._api_key = self._get_api_key(provider_name)
    
    def _get_api_key(self, name: str) -> Optional[str]:
        """Recupere la cle API."""
        env_keys = {
            "groq": "GROQ_API_KEY",
            "huggingface": "HF_API_KEY",
        }
        key_name = env_keys.get(name)
        if key_name:
            return os.environ.get(key_name)
        return None
    
    def generate(self, prompt: str, config: Optional[LLMConfig] = None) -> LLMResponse:
        """Generation via API gratuite."""
        cfg = config or self.config
        start = time.time()
        
        try:
            import requests
            
            # Construction du message
            messages = []
            if cfg.system_prompt:
                messages.append({"role": "system", "content": cfg.system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            headers = {
                "Authorization": f"Bearer {self._api_key or ''}",
                "Content-Type": "application/json",
            }
            
            model = cfg.model or "llama-3.2-90b-vision-preview"
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": cfg.temperature,
                "max_tokens": cfg.max_tokens,
                "top_p": cfg.top_p,
            }
            
            resp = requests.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=cfg.timeout or 60,
            )
            resp.raise_for_status()
            data = resp.json()
            
            content = data["choices"][0]["message"]["content"]
            latency = (time.time() - start) * 1000
            
            self._stats["calls"] += 1
            self._stats["latency_sum"] += latency
            
            return LLMResponse(
                content=content.strip(),
                model=model,
                provider=f"free_{self.provider_name}",
                latency_ms=latency,
            )
            
        except ImportError:
            return LLMResponse(
                content="", model=cfg.model, provider=f"free_{self.provider_name}",
                error="requests non installe",
            )
        except Exception as e:
            self._stats["calls"] += 1
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=cfg.model, provider=f"free_{self.provider_name}",
                error=str(e),
            )
    
    def stream(self, prompt: str, config: Optional[LLMConfig] = None):
        yield self.generate(prompt, config)


# ---------------------------------------------------------------------------
# ROUTEUR OPEN SOURCE
# ---------------------------------------------------------------------------

class HarmonicOpenRouter:
    """
    Routeur 100% open-source pour l'inference LLM.
    
    Strategie :
    1. Local ouvert         → transformers (GPU) ou GGUF (CPU)
    2. API gratuite         → Groq / HuggingFace Inference
    3. Modele nano          → Phi-3.5 / TinyLlama (CPU only)
    4. Fallback harmonique  → Moteur de resonance textuelle
    
    Usage:
        router = HarmonicOpenRouter()
        
        # Auto-detection
        resp = router.generate("Explique la relativite")
        
        # Par categorie
        resp = router.generate(
            "Calcule 15% de 340",
            category="mathematical"
        )
    """
    
    def __init__(self):
        self._machine = detect_machine()
        self._providers: Dict[str, LocalOpenProvider] = {}
        self._free_api: Optional[FreeAPIProvider] = None
        self._stats = {
            "local_calls": 0, "api_calls": 0,
            "nano_calls": 0, "fallbacks": 0,
        }
        
        logger.info(
            f"Machine detectee: {self._machine.tier} "
            f"(RAM: {self._machine.total_ram_gb:.0f}GB, "
            f"GPU: {self._machine.cuda_memory_gb:.0f}GB CUDA)"
        )
    
    def select_model(self, category: str) -> Tuple[str, dict]:
        """
        Selectionne le meilleur modele pour la categorie et la machine.
        
        Returns:
            (model_name, config_dict)
        """
        route = OPEN_ROUTING.get(category, OPEN_ROUTING["general"])
        
        if self._machine.tier == "gpu_heavy":
            return route["primary"], route["config"]
        elif self._machine.tier == "gpu_light":
            return route["fallback"], route["config"]
        elif self._machine.tier == "cpu":
            return route["q4_fallback"], route["config"]
        else:
            # CPU leger: modele nano
            return NANO_MODELS["leger"], {
                "temperature": 0.7, "max_tokens": 512
            }
    
    def generate(self, prompt: str, category: str = "general",
                 config: Optional[LLMConfig] = None) -> LLMResponse:
        """
        Genere via le meilleur modele open-source disponible.
        
        Strategie complete :
        1. Tentative locale (transformers ou GGUF)
        2. Fallback API gratuite (Groq)
        3. Fallback modele nano (Phi-3.5)
        4. Fallback harmonique (generation par resonance)
        """
        model_name, override = self.select_model(category)
        
        cfg = LLMConfig(model=model_name, **override)
        if config:
            cfg = LLMConfig(**{**cfg.__dict__, **config.__dict__})
        
        # System prompt harmonique
        if not cfg.system_prompt:
            cfg.system_prompt = self._build_system_prompt(category)
        
        # --- ETAPE 1: Tentative locale ---
        resp = self._try_local(prompt, model_name, cfg, category)
        if resp and resp.success:
            self._stats["local_calls"] += 1
            return resp
        
        # --- ETAPE 2: API gratuite ---
        resp = self._try_free_api(prompt, category, cfg)
        if resp and resp.success:
            self._stats["api_calls"] += 1
            return resp
        
        # --- ETAPE 3: Modele nano ---
        nano_model = NANO_MODELS["leger"]
        resp = self._try_local(prompt, nano_model, cfg, category)
        if resp and resp.success:
            self._stats["nano_calls"] += 1
            return resp
        
        # --- ETAPE 4: Fallback harmonique ---
        self._stats["fallbacks"] += 1
        return self._harmonic_fallback(prompt, category, cfg)
    
    def _try_local(self, prompt: str, model_name: str,
                    cfg: LLMConfig, category: str) -> Optional[LLMResponse]:
        """Tente une generation via modele local."""
        try:
            if model_name not in self._providers:
                provider = LocalOpenProvider(cfg)
                if not provider.load(model_name):
                    return None
                self._providers[model_name] = provider
            
            provider = self._providers[model_name]
            resp = provider.generate(prompt, cfg)
            
            if resp.error:
                logger.warning(f"Erreur locale {model_name}: {resp.error}")
                return None
            
            return resp
            
        except Exception as e:
            logger.debug(f"Echec local {model_name}: {e}")
            return None
    
    def _try_free_api(self, prompt: str, category: str,
                       cfg: LLMConfig) -> Optional[LLMResponse]:
        """Tente une generation via API gratuite."""
        try:
            if self._free_api is None:
                # Essayer Groq d'abord
                if os.environ.get("GROQ_API_KEY"):
                    self._free_api = FreeAPIProvider("groq")
                elif os.environ.get("HF_API_KEY"):
                    self._free_api = FreeAPIProvider("huggingface")
                else:
                    logger.info("Aucune cle API gratuite trouvee")
                    return None
            
            # Modeles compatibles Groq
            groq_models = FREE_APIS["groq"]["models"]
            api_model = groq_models.get(category, groq_models["general"])
            cfg.model = api_model
            
            return self._free_api.generate(prompt, cfg)
            
        except Exception as e:
            logger.debug(f"Echec API gratuite: {e}")
            return None
    
    def _harmonic_fallback(self, prompt: str, category: str,
                            cfg: LLMConfig) -> LLMResponse:
        """
        Fallback ultime: generation par resonance harmonique.
        Utilise le moteur de resonance textuelle sans LLM.
        """
        # Construction d'une reponse par motifs harmoniques
        words = prompt.split()
        word_count = len(words)
        
        # Reponses predefinies selon la categorie (avec expansion)
        templates = {
            "mathematical": [
                "Pour resoudre ce probleme mathematique,",
                "appliquons la methode harmonique.",
                f"Le nombre d'or φ = {PHI:.6f}",
                "guide notre raisonnement.",
                "",
                f"Analyse de &#39;{prompt[:50]}&#39;:",
                f"- {word_count} mots detectes",
                "- Resonance harmonique en cours...",
                "- Utilisez un modele local pour la resolution complete.",
                "",
                "Installation recommandee:",
                "  pip install llama-cpp-python",
                "  python -c &#39;from engine.llm.open_router import HarmonicOpenRouter;",
                "  r = HarmonicOpenRouter();",
                "  print(r.generate(\"" + prompt[:30] + "...\", \"mathematical\").content)&#39;",
            ],
            "code": [
                "Voici l&#39;analyse harmonique de votre demande de code:",
                "",
                f"Prompt: {prompt[:80]}",
                f"Mots-cles: {word_count}",
                "",
                "Pour generer du code, installez un modele local:",
                "  pip install llama-cpp-python",
                "  pip install &#39;transformers[torch]&#39;",
                "",
                "Alternative: API Groq gratuite",
                "  export GROQ_API_KEY=votre_cle",
            ],
            "creative": [
                "Dans l&#39;espace harmonique de la creativite,",
                f"φ = {PHI:.4f} tisse des motifs infinis.",
                "",
                f"Votre inspiration: {prompt[:80]}",
                f"Re sonance: {PHI_INV:.4f}",
                "",
                "Pour une creation complete, activez un LLM local:",
                "  pip install llama-cpp-python",
                "  python -m engine.llm.open_router",
            ],
            "reasoning": [
                "Analyse harmonique du raisonnement:",
                "",
                f"These: {prompt[:80]}",
                f"Complexite lexicale: {(word_count / 10.0):.2f}",
                f"Re sonance cognitive: {PHI_INV * 0.85:.4f}",
                "",
                "Pour une analyse approfondie: activez un LLM local.",
            ],
            "factual": [
                "Recherche factuelle harmonique:",
                "",
                f"Requete: {prompt[:80]}",
                f"Precision estimee: 0.{(word_count * 10):.0f}",
                "",
                "Pour des faits precis, utilisez un LLM:",
                "  pip install llama-cpp-python",
            ],
            "general": [
                "Harmonic AI - Resonance cognitive",
                "=================================",
                "",
                f"Prompt: {prompt[:80]}",
                f"Mode resonance: {category}",
                f"Machine: {self._machine.tier}",
                f"RAM: {self._machine.total_ram_gb:.0f}GB",
                f"GPU: {f'{self._machine.cuda_memory_gb:.0f}GB' if self._machine.has_cuda else 'Non'}",
                "",
                "Pour une reponse complete:",
                "1. Installez un modele local: pip install llama-cpp-python",
                "2. Ou configurez Groq: export GROQ_API_KEY=...",
                "3. Re-executez cette requete.",
            ],
        }
        
        content = "\n".join(
            templates.get(category, templates["general"])
        )
        
        return LLMResponse(
            content=content,
            model="harmonic_fallback",
            provider="harmonic_resonance",
            category=category,
        )
    
    def generate_auto(self, prompt: str,
                       config: Optional[LLMConfig] = None) -> LLMResponse:
        """Auto-detection de la categorie via signature harmonique."""
        category = self._detect_category(prompt)
        return self.generate(prompt, category, config)
    
    def _detect_category(self, text: str) -> str:
        """Detecte la categorie harmonique d'un prompt."""
        t = text.lower()
        
        # Mots-cles mathematiques
        math_kw = ['calcul', 'somme', 'equation', 'nombre', 'math',
                   'fonction', 'derivee', 'integrale', 'pourcent', 'phi']
        if sum(1 for kw in math_kw if kw in t) >= 2:
            return "mathematical"
        
        # Mots-cles code
        code_kw = ['python', 'code', 'algorithme', 'programme', 'fonction',
                   'debug', 'bug', 'compiler', 'api', 'git']
        if sum(1 for kw in code_kw if kw in t) >= 2:
            return "code"
        
        # Mots-cles creatifs
        creative_kw = ['poeme', 'histoire', 'cree', 'imagine', 'art', 'reve',
                       'musique', 'peinture', 'beaute']
        if sum(1 for kw in creative_kw if kw in t) >= 2:
            return "creative"
        
        # Mots-cles raisonnement
        reasoning_kw = ['pourquoi', 'explique', 'analyse', 'cause', 'donc',
                        'raison', 'logique']
        if sum(1 for kw in reasoning_kw if kw in t) >= 2:
            return "reasoning"
        
        # Mots-cles factuels
        factual_kw = ['definition', 'liste', 'fait', 'historique', 'date',
                      'nom', 'lieu', 'capital']
        if sum(1 for kw in factual_kw if kw in t) >= 2:
            return "factual"
        
        return "general"
    
    def _build_system_prompt(self, category: str) -> str:
        """Construit le system prompt harmonique."""
        prompts = {
            "mathematical": (
                "Tu es un assistant mathematique harmonique. "
                "Resous les problemes etape par etape avec precision. "
                f"φ = {PHI:.6f} guide l'harmonie de tes calculs."
            ),
            "code": (
                "Tu es un assistant de programmation harmonique. "
                "Genere du code propre, documente et efficace."
            ),
            "creative": (
                "Tu es un assistant creatif harmonique. "
                "Laisse libre cours a l'imagination. "
                "Utilise des metaphors poetiques."
            ),
            "reasoning": (
                "Tu es un assistant de raisonnement harmonique. "
                "Analyse en profondeur, structure ta pensee."
            ),
            "factual": (
                "Tu es un assistant factuel harmonique. "
                "Precis et veridique. Base-toi sur des faits."
            ),
            "general": (
                "Tu es un assistant IA harmonique, utile et precis. "
                f"φ = {PHI:.6f} guide l'harmonie de nos echanges."
            ),
        }
        return prompts.get(category, prompts["general"])
    
    def get_stats(self) -> dict:
        """Stats du routeur open-source."""
        provider_stats = {}
        for name, provider in self._providers.items():
            provider_stats[name] = provider.get_stats()
        
        return {
            **self._stats,
            "machine_tier": self._machine.tier,
            "ram_gb": round(self._machine.total_ram_gb, 1),
            "cuda_gb": round(self._machine.cuda_memory_gb, 1) if self._machine.has_cuda else 0,
            "loaded_models": list(self._providers.keys()),
            "free_api_available": self._free_api is not None,
        }


# ---------------------------------------------------------------------------
# ESTIMATION DE LA TAILLE DES MODELES
# ---------------------------------------------------------------------------

def estimate_model_size(model_name: str) -> float:
    """
    Estime la taille RAM necessaire pour un modele (en GB).
    Basse sur le nombre de parametres * precision.
    """
    size_map = {
        "Qwen/Qwen2.5-72B-Instruct": 72.0 * 2.0,       # 144GB FP16
        "Qwen/Qwen2.5-32B-Instruct": 32.0 * 2.0,        # 64GB FP16
        "Qwen/Qwen2.5-14B-Instruct": 14.0 * 2.0,        # 28GB FP16
        "Qwen/Qwen2.5-7B-Instruct": 7.0 * 2.0,          # 14GB FP16
        "Qwen/Qwen2.5-Coder-32B-Instruct": 32.0 * 2.0,  # 64GB
        "Qwen/Qwen2.5-Coder-14B-Instruct": 14.0 * 2.0,  # 28GB
        "Qwen/Qwen2.5-Coder-7B-Instruct": 7.0 * 2.0,    # 14GB
        "mistralai/Mistral-Nemo-Instruct-2407": 12.0 * 2.0,  # 24GB
        "mistralai/Mistral-7B-Instruct-v0.3": 7.0 * 2.0,    # 14GB
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": 32.0 * 2.0,  # 64GB
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B": 14.0 * 2.0,  # 28GB
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B": 7.0 * 2.0,    # 14GB
        "meta-llama/Llama-4-Scout-17B-16E-Instruct": 17.0 * 2.0,  # 34GB
        "microsoft/Phi-3.5-mini-instruct": 3.8 * 2.0,     # 7.6GB
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0": 1.1 * 2.0,  # 2.2GB
        "google/gemma-2b-it": 2.0 * 2.0,                   # 4GB
    }
    
    # Recherche par prefixe
    for key, size in size_map.items():
        if key in model_name or model_name in key:
            return size
    
    # Estimation generique: 2GB par milliard de parametres
    # Extrait le nombre de parametres du nom
    import re
    match = re.search(r'(\d+)B', model_name)
    if match:
        params_b = float(match.group(1))
        return params_b * 2.0
    
    # Par defaut: 7B
    return 14.0


# ---------------------------------------------------------------------------
# POINT D'ENTREE EN LIGNE DE COMMANDE
# ---------------------------------------------------------------------------

def main():
    """Demo du routeur open-source."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Routeur LLM 100% open-source"
    )
    parser.add_argument("prompt", nargs="?", help="Question ou instruction")
    parser.add_argument("--category", "-c", default="general",
                        choices=list(OPEN_ROUTING.keys()),
                        help="Categorie harmonique")
    parser.add_argument("--list-models", action="store_true",
                        help="Lister les modeles disponibles")
    parser.add_argument("--machine-info", action="store_true",
                        help="Afficher les infos machine")
    
    args = parser.parse_args()
    
    if args.list_models:
        print("=== MODELES OPEN-SOURCE DISPONIBLES ===\n")
        print(f"{'Categorie':<15} {'Modele':<45} {'Taille':>6}")
        print("-" * 70)
        for cat, route in OPEN_ROUTING.items():
            print(f"{cat:<15} {route['primary']:<45} ~{estimate_model_size(route['primary']):.0f}GB")
        
        print(f"\nModeles nano (CPU):")
        for name, model in NANO_MODELS.items():
            print(f"  {name}: {model}")
        
        print(f"\nAPIs gratuites: {list(FREE_APIS.keys())}")
        return
    
    if args.machine_info:
        machine = detect_machine()
        print("=== INFORMATIONS MACHINE ===")
        print(f"  RAM: {machine.total_ram_gb:.1f}GB")
        print(f"  GPU: {f'{machine.cuda_memory_gb:.0f}GB' if machine.has_cuda else 'Non'} ")
        print(f"  CPU: {machine.cpu_cores} coeurs")
        print(f"  Tier: {machine.tier}")
        print(f"  OS: {'Windows' if machine.is_windows else 'Linux/Mac'}")
        print(f"\n  Recommandation modele:")
        
        for cat in OPEN_ROUTING:
            model, _ = HarmonicOpenRouter().select_model(cat)
            size = estimate_model_size(model)
            print(f"    {cat:<14} → {model:<45} ({size:.0f}GB)")
        return
    
    if not args.prompt:
        # Mode interactif
        router = HarmonicOpenRouter()
        print("Routeur open-source harmonic (Ctrl+C pour quitter)\n")
        
        while True:
            try:
                prompt = input("> ")
                if not prompt:
                    continue
                
                resp = router.generate_auto(prompt)
                print(f"\n[{resp.provider}] {resp.model}")
                print(resp.content)
                print(f"({resp.latency_ms:.0f}ms)\n")
                
            except KeyboardInterrupt:
                print("\nAu revoir !")
                break
    else:
        router = HarmonicOpenRouter()
        resp = router.generate(args.prompt, args.category)
        print(f"\n[{resp.provider}] {resp.model}")
        print(resp.content)
        print(f"({resp.latency_ms:.0f}ms)")


if __name__ == "__main__":
    main()
