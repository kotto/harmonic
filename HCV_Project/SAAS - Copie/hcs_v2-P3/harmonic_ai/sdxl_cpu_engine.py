#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDXLCPUEngine - Moteur SDXL optimise pour CPU
==============================================
Charge et execute les modeles de diffusion en mode CPU avec :

  - SDXL-Turbo (1-4 steps) : 45-90s/image, 1.05 GB INT8
  - LCM (Latent Consistency) : 30-60s/image, 1.1 GB
  - Fallback harmonique pur : < 1s, zero MB (mode sans IA)

Strategies de compression :
  1. INT8 Quantization (torch.quantization.quantize_dynamic)
  2. ONNX Runtime (2-3x gain vs PyTorch CPU)
  3. Memory mapping des poids (economie RAM)
  4. Threading optimise (tous les coeurs CPU)

Usage:
    engine = SDXLCPUEngine(model="sdxl-turbo", quantize=True)
    image = engine.generate("a sunset over the ocean")
"""

import os
import sys
import time
import threading
import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Constantes
PHI = 1.6180339887
PHI2 = 2.6180339887

# Modeles disponibles
AVAILABLE_MODELS = {
    "sdxl-turbo": {
        "hf_id": "stabilityai/sdxl-turbo",
        "steps_range": (1, 4),
        "size_fp16_gb": 2.1,
        "size_int8_gb": 1.05,
        "cpu_time_s": (45, 90),
        "quality": 0.85,
    },
    "sdxl-lightning": {
        "hf_id": "ByteDance/SDXL-Lightning",
        "steps_range": (4, 8),
        "size_fp16_gb": 2.3,
        "size_int8_gb": 1.15,
        "cpu_time_s": (60, 120),
        "quality": 0.87,
    },
    "lcm": {
        "hf_id": "SimianLuo/LCM_Dreamshaper_v7",
        "steps_range": (2, 8),
        "size_fp16_gb": 1.8,
        "size_int8_gb": 1.1,
        "cpu_time_s": (30, 60),
        "quality": 0.80,
    },
    "fallback-harmonic": {
        "hf_id": None,
        "steps_range": (0, 0),
        "size_fp16_gb": 0.0,
        "size_int8_gb": 0.0,
        "cpu_time_s": (0, 1),
        "quality": 0.60,
    },
}


class SDXLCPUEngine:
    """
    Moteur de generation d'images SDXL optimise CPU.

    Strategie de chargement progressive :
      1. Tentative SDXL-Turbo avec ONNX ou INT8
      2. Fallback LCM si SDXL-Turbo echoue
      3. Fallback harmonique pur si tout echoue

    Le mode fallback harmonique garantit le fonctionnement
    meme sans diffusers/torch installe.
    """

    def __init__(
        self,
        model: str = "sdxl-turbo",
        quantize: bool = True,
        use_onnx: bool = False,
        num_steps: int = 2,
        guidance_scale: float = 0.0,
        output_resolution: Tuple[int, int] = (512, 512),
        cache_dir: Optional[str] = None,
    ):
        """
        Args:
            model: nom du modele parmi AVAILABLE_MODELS
            quantize: activer la quantization INT8
            use_onnx: utiliser ONNX Runtime (recommande sur CPU Windows)
            num_steps: nombre d'etapes de denoising
            guidance_scale: force du guidance (0=turbo mode)
            output_resolution: resolution de sortie (width, height)
            cache_dir: repertoire de cache des modeles
        """
        if model not in AVAILABLE_MODELS:
            logger.warning(f"Modele inconnu '{model}', utilisation sdxl-turbo")
            model = "sdxl-turbo"

        self.model_name = model
        self.model_info = AVAILABLE_MODELS[model]
        self.quantize = quantize
        self.use_onnx = use_onnx
        self.num_steps = max(1, min(num_steps, self.model_info["steps_range"][1]))
        self.guidance_scale = guidance_scale
        self.output_resolution = output_resolution
        self.cache_dir = cache_dir or str(Path.home() / ".cache" / "hcs_models")

        # Pipeline chargé
        self._pipeline = None
        self._onnx_session = None
        self._mode = "unloaded"  # "sdxl" | "onnx" | "harmonic"
        self._load_lock = threading.Lock()

        # Optimisations CPU
        self._setup_cpu_optimizations()

        logger.info(f"SDXLCPUEngine init: model={model}, quantize={quantize}, steps={num_steps}")

    # ------------------------------------------------------------------
    # Optimisations CPU
    # ------------------------------------------------------------------

    def _setup_cpu_optimizations(self):
        """Configure les optimisations CPU globales."""
        try:
            import torch
            # Utiliser tous les coeurs CPU
            n_threads = os.cpu_count() or 4
            torch.set_num_threads(n_threads)
            torch.set_num_interop_threads(min(4, n_threads // 2))
            logger.info(f"CPU threads: {n_threads} (intra) / {min(4, n_threads//2)} (inter)")
        except ImportError:
            pass

    # ------------------------------------------------------------------
    # Chargement du modele
    # ------------------------------------------------------------------

    def load(self) -> bool:
        """
        Charge le modele. Essaie dans l'ordre :
          1. ONNX Runtime
          2. Diffusers + quantization INT8
          3. Fallback harmonique

        Returns:
            True si charge avec succes (SDXL ou ONNX)
            False si fallback harmonique
        """
        with self._load_lock:
            if self._mode != "unloaded":
                return self._mode != "harmonic"

            # Tentative ONNX
            if self.use_onnx:
                if self._try_load_onnx():
                    return True

            # Tentative Diffusers
            if self.model_info["hf_id"] is not None:
                if self._try_load_diffusers():
                    return True

            # Fallback harmonique
            logger.warning("Tous les backends IA echouent, utilisation du generateur harmonique")
            self._mode = "harmonic"
            return False

    def _try_load_diffusers(self) -> bool:
        """Tentative de chargement via diffusers."""
        try:
            import torch
            from diffusers import AutoPipelineForText2Image

            logger.info(f"Chargement {self.model_name} via diffusers...")
            t0 = time.time()

            # Chargement du pipeline
            self._pipeline = AutoPipelineForText2Image.from_pretrained(
                self.model_info["hf_id"],
                torch_dtype=torch.float16 if not self.quantize else torch.float32,
                variant="fp16" if not self.quantize else None,
                cache_dir=self.cache_dir,
            )
            self._pipeline = self._pipeline.to("cpu")

            # Quantization INT8 si demandee
            if self.quantize:
                self._apply_int8_quantization()

            # Optimisations memoire
            self._pipeline.enable_attention_slicing()
            try:
                self._pipeline.enable_vae_slicing()
            except Exception:
                pass

            elapsed = time.time() - t0
            model_size = self._estimate_model_size()
            logger.info(f"Pipeline charge en {elapsed:.1f}s | taille ~{model_size:.1f} GB")
            self._mode = "sdxl"
            return True

        except Exception as e:
            logger.warning(f"Diffusers indisponible: {e}")
            return False

    def _try_load_onnx(self) -> bool:
        """Tentative de chargement via ONNX Runtime."""
        try:
            import onnxruntime as ort

            # Cherche un modele ONNX pre-exporte
            onnx_path = Path(self.cache_dir) / f"{self.model_name}_cpu.onnx"
            if not onnx_path.exists():
                logger.debug(f"Modele ONNX non trouve: {onnx_path}")
                return False

            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = os.cpu_count() or 4
            sess_options.inter_op_num_threads = 2
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            self._onnx_session = ort.InferenceSession(
                str(onnx_path),
                sess_options=sess_options,
                providers=["CPUExecutionProvider"],
            )
            logger.info(f"ONNX Runtime charge: {onnx_path}")
            self._mode = "onnx"
            return True

        except ImportError:
            logger.debug("onnxruntime non installe")
            return False
        except Exception as e:
            logger.warning(f"ONNX indisponible: {e}")
            return False

    def _apply_int8_quantization(self):
        """Applique la quantization INT8 dynamique au pipeline."""
        try:
            import torch
            import torch.quantization as tq

            logger.info("Application quantization INT8...")
            t0 = time.time()

            # Quantization du UNet (le plus gourmand)
            if hasattr(self._pipeline, "unet"):
                self._pipeline.unet = tq.quantize_dynamic(
                    self._pipeline.unet,
                    {torch.nn.Linear, torch.nn.Conv2d},
                    dtype=torch.qint8,
                )
                logger.debug("UNet quantize INT8")

            # Quantization du text encoder
            if hasattr(self._pipeline, "text_encoder"):
                self._pipeline.text_encoder = tq.quantize_dynamic(
                    self._pipeline.text_encoder,
                    {torch.nn.Linear},
                    dtype=torch.qint8,
                )
                logger.debug("Text encoder quantize INT8")

            elapsed = time.time() - t0
            logger.info(f"Quantization INT8 appliquee en {elapsed:.1f}s")

        except Exception as e:
            logger.warning(f"Quantization INT8 echouee: {e}")

    def _estimate_model_size(self) -> float:
        """Estime la taille du modele en memoire (GB)."""
        try:
            import torch
            total_params = 0
            if self._pipeline:
                for module in [
                    getattr(self._pipeline, "unet", None),
                    getattr(self._pipeline, "text_encoder", None),
                    getattr(self._pipeline, "vae", None),
                ]:
                    if module is not None:
                        total_params += sum(p.numel() for p in module.parameters())
            bytes_per_param = 1 if self.quantize else 2  # INT8 vs FP16
            return total_params * bytes_per_param / (1024 ** 3)
        except Exception:
            return self.model_info["size_int8_gb"] if self.quantize else self.model_info["size_fp16_gb"]

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "blurry, low quality, distorted",
        seed: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Genere une image depuis un prompt texte.

        Args:
            prompt: description textuelle de l'image
            negative_prompt: elements a eviter
            seed: graine pour reproductibilite
            width: largeur (None = defaut)
            height: hauteur (None = defaut)

        Returns:
            (image uint8 RGB, metadonnees dict)
        """
        # Chargement automatique si necessaire
        if self._mode == "unloaded":
            self.load()

        W = width or self.output_resolution[0]
        H = height or self.output_resolution[1]

        t0 = time.time()

        if self._mode == "sdxl":
            image, meta = self._generate_sdxl(prompt, negative_prompt, seed, W, H)
        elif self._mode == "onnx":
            image, meta = self._generate_onnx(prompt, negative_prompt, seed, W, H)
        else:
            # Fallback harmonique
            image, meta = self._generate_harmonic_fallback(prompt, seed, W, H)

        elapsed = time.time() - t0
        meta["total_time_s"] = elapsed
        meta["mode"] = self._mode
        meta["model"] = self.model_name
        meta["resolution"] = (W, H)

        logger.info(f"Generation '{prompt[:50]}...' en {elapsed:.1f}s | mode={self._mode}")
        return image, meta

    def _generate_sdxl(
        self, prompt: str, negative_prompt: str,
        seed: Optional[int], W: int, H: int
    ) -> Tuple[np.ndarray, Dict]:
        """Generation via pipeline diffusers."""
        try:
            import torch

            generator = torch.Generator().manual_seed(seed) if seed is not None else None

            result = self._pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt if self.guidance_scale > 0 else None,
                num_inference_steps=self.num_steps,
                guidance_scale=self.guidance_scale,
                width=W,
                height=H,
                generator=generator,
            )

            image_pil = result.images[0]
            image_np = np.array(image_pil)

            return image_np, {
                "steps": self.num_steps,
                "guidance_scale": self.guidance_scale,
                "seed": seed,
            }

        except Exception as e:
            logger.error(f"Erreur generation SDXL: {e}")
            return self._generate_harmonic_fallback(prompt, seed, W, H)

    def _generate_onnx(
        self, prompt: str, negative_prompt: str,
        seed: Optional[int], W: int, H: int
    ) -> Tuple[np.ndarray, Dict]:
        """Generation via ONNX Runtime."""
        try:
            # Preparation des inputs ONNX
            rng = np.random.RandomState(seed if seed else 42)
            latent_noise = rng.randn(1, 4, H // 8, W // 8).astype(np.float32)

            inputs = {
                "prompt": np.array([prompt]),
                "latent_noise": latent_noise,
                "num_steps": np.array([self.num_steps], dtype=np.int32),
            }

            outputs = self._onnx_session.run(None, inputs)
            image_np = (outputs[0].squeeze() * 255).clip(0, 255).astype(np.uint8)

            return image_np, {"steps": self.num_steps, "seed": seed}

        except Exception as e:
            logger.error(f"Erreur generation ONNX: {e}")
            return self._generate_harmonic_fallback(prompt, seed, W, H)

    def _generate_harmonic_fallback(
        self, prompt: str, seed: Optional[int], W: int, H: int
    ) -> Tuple[np.ndarray, Dict]:
        """
        Fallback : generation purement harmonique depuis le prompt.
        Utilise le HarmonicSynthesizer pour generer une image
        sans aucune IA. Qualite limitee mais deterministe.
        """
        from .harmonic_synthesizer import HarmonicSynthesizer

        logger.info(f"Fallback harmonique: '{prompt[:40]}...'")

        # Derive une signature depuis le prompt (hash deterministe)
        sig = self._prompt_to_signature(prompt, seed)

        # Profil chromatique base sur des mots-cles du prompt
        chroma = self._prompt_to_chromatic(prompt)

        # Synthese
        synth = HarmonicSynthesizer(quality_level="fast")
        image = synth.synthesize(sig, resolution=(W, H), chromatic_profile=chroma)

        return image, {
            "fallback": True,
            "quality_estimate": 0.60,
            "note": "Generateur harmonique pur (SDXL non disponible)",
        }

    def _prompt_to_signature(self, prompt: str, seed: Optional[int]) -> np.ndarray:
        """
        Derives une signature harmonique 512D depuis un prompt texte.
        Methode deterministe par hachage semantique.
        """
        # Hachage du prompt en vecteur
        prompt_bytes = prompt.encode("utf-8")
        np.random.seed(seed if seed else hash(prompt) % (2**31))

        sig = np.zeros(512, dtype=np.float32)

        # Chaque caractere contribue a la signature
        for i, byte in enumerate(prompt_bytes[:256]):
            freq_idx = i % 64
            chroma_idx = 64 + (i % 64)
            sig[freq_idx] += np.sin(byte * PHI / 128.0)
            sig[chroma_idx] += np.cos(byte * PHI2 / 128.0)

        # Composantes aleatoires (reproduit avec le seed)
        sig[128:] = np.random.randn(384) * 0.3

        # Modulation phi sur les composantes
        for k in range(0, 64, 4):
            sig[k] *= PHI ** (k / 64.0)
            sig[64 + k] *= PHI2 ** (k / 128.0)

        # Normalisation
        norm = np.linalg.norm(sig)
        if norm > 1e-8:
            sig = sig / norm

        return sig

    def _prompt_to_chromatic(self, prompt: str) -> Dict[str, Any]:
        """Determine le profil chromatique depuis les mots-cles du prompt."""
        prompt_lower = prompt.lower()
        chroma = {"mean_rgb": [0.5, 0.5, 0.5], "std_rgb": [0.15, 0.15, 0.15]}

        # Mapping semantique couleur
        color_keywords = {
            "sunset": {"mean_rgb": [0.8, 0.5, 0.2], "std_rgb": [0.15, 0.12, 0.10]},
            "ocean": {"mean_rgb": [0.2, 0.4, 0.7], "std_rgb": [0.10, 0.12, 0.15]},
            "forest": {"mean_rgb": [0.2, 0.5, 0.2], "std_rgb": [0.08, 0.10, 0.08]},
            "night": {"mean_rgb": [0.1, 0.1, 0.2], "std_rgb": [0.05, 0.05, 0.08]},
            "fire": {"mean_rgb": [0.8, 0.3, 0.1], "std_rgb": [0.15, 0.10, 0.05]},
            "snow": {"mean_rgb": [0.9, 0.9, 0.95], "std_rgb": [0.05, 0.05, 0.05]},
            "desert": {"mean_rgb": [0.8, 0.7, 0.4], "std_rgb": [0.10, 0.10, 0.08]},
            "golden": {"mean_rgb": [0.8, 0.7, 0.2], "std_rgb": [0.12, 0.12, 0.08]},
            "blue": {"mean_rgb": [0.2, 0.3, 0.8], "std_rgb": [0.08, 0.10, 0.15]},
            "red": {"mean_rgb": [0.8, 0.2, 0.2], "std_rgb": [0.15, 0.08, 0.08]},
            "green": {"mean_rgb": [0.2, 0.7, 0.2], "std_rgb": [0.08, 0.15, 0.08]},
            "purple": {"mean_rgb": [0.5, 0.1, 0.7], "std_rgb": [0.10, 0.08, 0.15]},
        }

        for keyword, profile in color_keywords.items():
            if keyword in prompt_lower:
                chroma = profile
                break  # Prend le premier match

        return chroma

    # ------------------------------------------------------------------
    # Batch generation pour BDD
    # ------------------------------------------------------------------

    def generate_batch(
        self,
        prompts: List[str],
        seeds: Optional[List[int]] = None,
        progress_callback=None,
    ) -> List[Tuple[np.ndarray, Dict]]:
        """
        Genere un lot d'images pour alimenter la BDD harmonique.

        Args:
            prompts: liste de prompts
            seeds: liste de seeds (None = auto)
            progress_callback: fonction(idx, total) appellee apres chaque image

        Returns:
            liste de (image, meta)
        """
        if self._mode == "unloaded":
            self.load()

        results = []
        n = len(prompts)

        for idx, prompt in enumerate(prompts):
            seed = seeds[idx] if seeds and idx < len(seeds) else idx * 1337

            try:
                image, meta = self.generate(prompt, seed=seed)
                results.append((image, meta))
                logger.info(f"[{idx+1}/{n}] '{prompt[:40]}...' OK")
            except Exception as e:
                logger.error(f"[{idx+1}/{n}] Erreur: {e}")
                # Image noire en cas d'erreur
                W, H = self.output_resolution
                results.append((np.zeros((H, W, 3), dtype=np.uint8), {"error": str(e)}))

            if progress_callback:
                progress_callback(idx + 1, n)

        return results

    # ------------------------------------------------------------------
    # Export ONNX
    # ------------------------------------------------------------------

    def export_to_onnx(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Exporte le modele SDXL charge au format ONNX pour usage futur.
        Necessite que le pipeline soit charge via diffusers.

        Returns:
            chemin du fichier ONNX si succes, None sinon
        """
        if self._mode != "sdxl":
            logger.warning("Export ONNX : pipeline SDXL requis")
            return None

        try:
            import torch
            from pathlib import Path

            output_path = output_path or str(
                Path(self.cache_dir) / f"{self.model_name}_cpu.onnx"
            )

            logger.info(f"Export ONNX vers: {output_path}")

            # Export du UNet
            W, H = self.output_resolution
            dummy_latent = torch.randn(1, 4, H // 8, W // 8)
            dummy_timestep = torch.tensor([999])
            dummy_encoder_hidden = torch.randn(1, 77, 2048)

            torch.onnx.export(
                self._pipeline.unet,
                (dummy_latent, dummy_timestep, dummy_encoder_hidden),
                output_path,
                opset_version=17,
                input_names=["latent", "timestep", "encoder_hidden_states"],
                output_names=["noise_pred"],
                dynamic_axes={
                    "latent": {0: "batch", 2: "height", 3: "width"},
                },
            )
            logger.info(f"Export ONNX reussi: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Export ONNX echoue: {e}")
            return None

    # ------------------------------------------------------------------
    # Informations et diagnostics
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du moteur."""
        return {
            "model": self.model_name,
            "mode": self._mode,
            "quantized": self.quantize,
            "onnx": self.use_onnx,
            "num_steps": self.num_steps,
            "guidance_scale": self.guidance_scale,
            "output_resolution": self.output_resolution,
            "model_info": self.model_info,
            "ready": self._mode != "unloaded",
            "cpu_threads": os.cpu_count(),
        }

    def benchmark(self, n_runs: int = 3) -> Dict[str, float]:
        """
        Benchmark du moteur sur quelques generations de test.

        Returns:
            dict avec les temps moyens
        """
        if self._mode == "unloaded":
            self.load()

        test_prompts = [
            "a beautiful sunset over the ocean",
            "a forest with golden light",
            "a mountain landscape with snow",
        ][:n_runs]

        times = []
        for prompt in test_prompts:
            t0 = time.time()
            self.generate(prompt, seed=42)
            times.append(time.time() - t0)

        return {
            "avg_time_s": np.mean(times),
            "min_time_s": np.min(times),
            "max_time_s": np.max(times),
            "std_time_s": np.std(times),
            "mode": self._mode,
            "n_runs": n_runs,
        }

    def unload(self):
        """Libere la memoire en dechargant le modele."""
        self._pipeline = None
        self._onnx_session = None
        self._mode = "unloaded"

        try:
            import torch
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

        logger.info("Modele decharge")


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def check_cpu_sdxl_availability() -> Dict[str, Any]:
    """
    Verifie la disponibilite des composants pour SDXL CPU.
    Retourne un rapport detaille.
    """
    report = {
        "torch": False,
        "torch_version": None,
        "diffusers": False,
        "diffusers_version": None,
        "onnxruntime": False,
        "onnx_version": None,
        "bitsandbytes": False,
        "scipy": False,
        "pillow": False,
        "ram_gb": None,
        "cpu_cores": os.cpu_count(),
        "recommended_model": None,
        "estimated_cpu_time_s": None,
    }

    # RAM disponible
    try:
        import psutil
        report["ram_gb"] = psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        pass

    # PyTorch
    try:
        import torch
        report["torch"] = True
        report["torch_version"] = torch.__version__
    except ImportError:
        pass

    # Diffusers
    try:
        import diffusers
        report["diffusers"] = True
        report["diffusers_version"] = diffusers.__version__
    except ImportError:
        pass

    # ONNX Runtime
    try:
        import onnxruntime
        report["onnxruntime"] = True
        report["onnx_version"] = onnxruntime.__version__
    except ImportError:
        pass

    # BitsAndBytes
    try:
        import bitsandbytes
        report["bitsandbytes"] = True
    except ImportError:
        pass

    # Scipy
    try:
        import scipy
        report["scipy"] = True
    except ImportError:
        pass

    # Pillow
    try:
        import PIL
        report["pillow"] = True
    except ImportError:
        pass

    # Recommandation
    ram = report.get("ram_gb") or 8.0
    if report["diffusers"] and report["torch"] and ram >= 8:
        report["recommended_model"] = "sdxl-turbo"
        report["estimated_cpu_time_s"] = 45
    elif report["diffusers"] and report["torch"] and ram >= 4:
        report["recommended_model"] = "lcm"
        report["estimated_cpu_time_s"] = 30
    else:
        report["recommended_model"] = "fallback-harmonic"
        report["estimated_cpu_time_s"] = 1

    return report


# ---------------------------------------------------------------------------
# Test autonome
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== Test SDXLCPUEngine ===\n")

    # Diagnostic
    print("Diagnostics systeme:")
    diag = check_cpu_sdxl_availability()
    for k, v in diag.items():
        print(f"  {k}: {v}")

    print(f"\nModele recommande: {diag['recommended_model']}")
    print(f"Temps estime: {diag['estimated_cpu_time_s']}s")

    # Test du moteur (mode fallback si pas de GPU/modele)
    print("\nTest generation (mode automatique)...")
    engine = SDXLCPUEngine(
        model=diag["recommended_model"],
        quantize=True,
        num_steps=2,
        output_resolution=(256, 256),
    )

    status = engine.get_status()
    print(f"Status moteur: {status}")

    # Generation test
    t0 = time.time()
    image, meta = engine.generate(
        "a beautiful sunset over the ocean, warm colors, golden hour",
        seed=42,
    )
    t1 = time.time()

    print(f"\nGeneration OK:")
    print(f"  Temps: {(t1-t0):.1f}s")
    print(f"  Mode: {meta.get('mode', 'unknown')}")
    print(f"  Shape: {image.shape}")
    print(f"  Plage: [{image.min()}, {image.max()}]")

    # Sauvegarde
    try:
        from PIL import Image as PILImage
        PILImage.fromarray(image).save("sdxl_cpu_test.png")
        print("Image sauvegardee: sdxl_cpu_test.png")
    except ImportError:
        pass

    print("\n=== Test termine ===")
