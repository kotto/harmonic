#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdaptiveLearner - Apprentissage actif et transition SDXL -> Harmonic AI
=======================================================================
Orchestrateur central du systeme de generation adaptative.

Logique de decision (selon score d'autonomie de la BDD) :
  score < 0.30 : SDXL pur (amorçage)
  score 0.30-0.60 : SDXL + correction harmonique
  score 0.60-0.85 : Harmonic AI + raffinement SDXL partiel
  score > 0.85  : Harmonic AI pur (autonomie complete)

Chaque generation utilisateur enrichit automatiquement la BDD si
la confiance du lookup est insuffisante (< seuil).

Usage:
    learner = AdaptiveLearner("harmonic_db/")
    image = learner.generate("a sunset over the ocean")
    # -> utilise SDXL ou Harmonic AI selon l'etat de la BDD
"""

import time
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass

from .harmonic_db import HarmonicDatabase
from .harmonic_signature import HarmonicSignatureExtractor
from .harmonic_synthesizer import HarmonicSynthesizer
from .sdxl_cpu_engine import SDXLCPUEngine
from .sdxl_ingestor import SDXLIngestor, IngestionConfig

logger = logging.getLogger(__name__)

# Seuils de transition
THRESHOLDS = {
    "sdxl_pure": 0.30,         # En dessous : SDXL pur
    "sdxl_harmonic": 0.60,     # Entre les deux : hybride
    "harmonic_partial": 0.85,  # Presque autonome
    "harmonic_pure": 0.85,     # Au dessus : Harmonic AI pur
    "confidence_auto_ingest": 0.70,  # Confiance min pour eviter re-generation SDXL
}

# Resolution par defaut
DEFAULT_RESOLUTION = (512, 512)


@dataclass
class GenerationResult:
    """Resultat d'une generation adaptative."""
    image: np.ndarray
    mode: str              # "sdxl_pure" | "sdxl_harmonic" | "harmonic_partial" | "harmonic_pure"
    prompt: str
    confidence: float      # Confiance de la BDD [0-1]
    autonomy_score: float  # Score autonomie courant [0-1]
    generation_time_s: float
    object_id: Optional[str]  # Si ingere dans la BDD
    metadata: Dict[str, Any]


class AdaptiveLearner:
    """
    Orchestrateur adaptatif SDXL -> Harmonic AI.

    Il gere la transition progressive entre les deux modes de generation
    et enrichit automatiquement la BDD au fil des utilisations.

    Usage:
        learner = AdaptiveLearner("harmonic_db/")
        result = learner.generate("a beautiful sunset")
        print(f"Mode: {result.mode}, Confiance: {result.confidence:.2f}")
    """

    def __init__(
        self,
        db_dir: str = "harmonic_db",
        sdxl_model: str = "sdxl-turbo",
        resolution: Tuple[int, int] = DEFAULT_RESOLUTION,
        auto_ingest: bool = True,
        verbose: bool = True,
    ):
        """
        Args:
            db_dir: repertoire de la base de donnees harmonique
            sdxl_model: modele SDXL a utiliser
            resolution: resolution de generation (width, height)
            auto_ingest: ingerer automatiquement dans la BDD les nouvelles generations
            verbose: afficher les logs de progression
        """
        self.db_dir = db_dir
        self.resolution = resolution
        self.auto_ingest = auto_ingest
        self.verbose = verbose

        # Base de donnees harmonique
        self.db = HarmonicDatabase(db_dir)

        # Extracteur de signature
        self._extractor = HarmonicSignatureExtractor()

        # Synthétiseur harmonique
        self._synthesizer = HarmonicSynthesizer(quality_level="standard")

        # Moteur SDXL (charge a la demande)
        self._sdxl: Optional[SDXLCPUEngine] = None
        self._sdxl_model = sdxl_model

        # Bridge upscaler (charge a la demande)
        self._upscaler_bridge = None

        # Ingesteur (partage le meme moteur SDXL)
        self._ingestor: Optional[SDXLIngestor] = None

        # Stats de session
        self._session_stats = {
            "total_generations": 0,
            "sdxl_calls": 0,
            "harmonic_calls": 0,
            "auto_ingested": 0,
            "started_at": time.time(),
        }

        if verbose:
            self.db.print_status()
            logger.info(f"AdaptiveLearner pret | autonomie={self.db.get_autonomy_score()*100:.1f}%")

    # ------------------------------------------------------------------
    # Generation principale
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        seed: Optional[int] = None,
        force_mode: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> GenerationResult:
        """
        Genere une image en choisissant automatiquement le mode optimal.

        Args:
            prompt: description textuelle
            seed: graine pour reproductibilite
            force_mode: forcer un mode ("sdxl" | "harmonic" | "auto")
            width: largeur (None = resolution par defaut)
            height: hauteur (None = resolution par defaut)

        Returns:
            GenerationResult avec image et metadonnees
        """
        t0 = time.time()
        W = width or self.resolution[0]
        H = height or self.resolution[1]

        self._session_stats["total_generations"] += 1

        # Determination du mode
        autonomy = self.db.get_autonomy_score()

        if force_mode == "sdxl":
            mode = "sdxl_pure"
        elif force_mode == "harmonic":
            mode = "harmonic_pure"
        else:
            mode = self._decide_mode(autonomy)

        if self.verbose:
            logger.info(
                f"Generation '{prompt[:50]}...' | "
                f"mode={mode} | autonomie={autonomy*100:.1f}%"
            )

        # Tokenisation du prompt
        tokens = self._tokenize_prompt(prompt)

        # Lookup BDD
        confidence, db_results = self.db.lookup_with_confidence(tokens, top_k=3)

        # Generation selon le mode
        if mode in ("harmonic_pure", "harmonic_partial") and confidence >= THRESHOLDS["confidence_auto_ingest"]:
            image, gen_meta = self._generate_harmonic(db_results, (W, H), prompt)
            self._session_stats["harmonic_calls"] += 1
        elif mode == "sdxl_harmonic":
            image, gen_meta = self._generate_sdxl_harmonic(
                prompt, db_results, seed, W, H
            )
            self._session_stats["sdxl_calls"] += 1
        else:
            # SDXL pur (ou BDD insuffisante)
            image, gen_meta = self._generate_sdxl_pure(prompt, seed, W, H)
            self._session_stats["sdxl_calls"] += 1

        elapsed = time.time() - t0

        # Auto-ingestion si BDD insuffisante
        object_id = None
        if self.auto_ingest and confidence < THRESHOLDS["confidence_auto_ingest"]:
            object_id = self._auto_ingest(image, prompt, tokens)
            if object_id:
                self._session_stats["auto_ingested"] += 1

        result = GenerationResult(
            image=image,
            mode=mode,
            prompt=prompt,
            confidence=confidence,
            autonomy_score=autonomy,
            generation_time_s=elapsed,
            object_id=object_id,
            metadata={
                "tokens": tokens,
                "db_results_count": len(db_results),
                "gen_meta": gen_meta,
                "auto_ingested": object_id is not None,
            },
        )

        if self.verbose:
            self._log_result(result)

        return result

    def generate_video(
        self,
        prompt: str,
        n_frames: int = 24,
        fps: float = 24.0,
        seed: Optional[int] = None,
    ) -> List[np.ndarray]:
        """
        Genere une sequence video deterministe.

        Args:
            prompt: description textuelle
            n_frames: nombre de frames
            fps: images par seconde
            seed: graine

        Returns:
            liste de frames uint8 RGB
        """
        # Genere d'abord l'image cle
        result = self.generate(prompt, seed=seed)

        # Extrait la signature depuis l'image generee
        sig, _ = self._extractor.extract(result.image)

        # Profil chromatique depuis la BDD si disponible
        chroma = {}
        tokens = self._tokenize_prompt(prompt)
        _, db_results = self.db.lookup_with_confidence(tokens)
        if db_results:
            chroma = db_results[0].get("chromatic_profile", {})

        # Generation video harmonique
        frames = self._synthesizer.synthesize_video_frames(
            sig,
            n_frames=n_frames,
            fps=fps,
            resolution=self.resolution,
            chromatic_profile=chroma,
        )

        logger.info(f"Video generee: {len(frames)} frames @ {fps}fps")
        return frames

    # ------------------------------------------------------------------
    # Modes de generation
    # ------------------------------------------------------------------

    def _generate_harmonic(
        self,
        db_results: List[Dict],
        resolution: Tuple[int, int],
        prompt: str,
    ) -> Tuple[np.ndarray, Dict]:
        """Generation pure par mathematiques harmoniques depuis la BDD."""
        if not db_results:
            # Aucun resultat BDD : signature depuis prompt
            sig = self._prompt_to_signature_direct(prompt)
            chroma = {}
        else:
            # Composition phi des signatures BDD
            signatures = [r["signature"] for r in db_results if r.get("signature") is not None]
            if not signatures:
                sig = self._prompt_to_signature_direct(prompt)
                chroma = {}
            else:
                sig = self.db.phi_compose(signatures)
                # Fusion des profils chromatiques
                chroma_list = [r.get("chromatic_profile", {}) for r in db_results]
                chroma = self._fuse_chromatic_profiles(chroma_list)

        image = self._synthesizer.synthesize(sig, resolution=resolution, chromatic_profile=chroma)

        return image, {
            "method": "harmonic_pure",
            "db_signatures_used": len(db_results),
        }

    def _generate_sdxl_harmonic(
        self,
        prompt: str,
        db_results: List[Dict],
        seed: Optional[int],
        W: int, H: int,
    ) -> Tuple[np.ndarray, Dict]:
        """Generation hybride : SDXL + correction harmonique post-process."""
        # Generation SDXL
        sdxl = self._get_sdxl_engine()
        image_sdxl, meta = sdxl.generate(prompt, seed=seed, width=W, height=H)

        # Correction harmonique si BDD disponible
        if db_results:
            signatures = [r["signature"] for r in db_results if r.get("signature") is not None]
            if signatures:
                composed_sig = self.db.phi_compose(signatures)
                chroma = db_results[0].get("chromatic_profile", {})

                # Synthese harmonique
                image_harmonic = self._synthesizer.synthesize(
                    composed_sig, resolution=(W, H), chromatic_profile=chroma
                )

                # Fusion : 60% SDXL + 40% harmonique
                image_sdxl_f = image_sdxl.astype(np.float32)
                image_harm_f = image_harmonic.astype(np.float32)
                fused = 0.60 * image_sdxl_f + 0.40 * image_harm_f
                image = np.clip(fused, 0, 255).astype(np.uint8)

                return image, {"method": "sdxl_harmonic", "blend": 0.60}

        return image_sdxl, {"method": "sdxl_harmonic_nodbb"}

    def _generate_sdxl_pure(
        self, prompt: str, seed: Optional[int], W: int, H: int
    ) -> Tuple[np.ndarray, Dict]:
        """Generation SDXL pure."""
        sdxl = self._get_sdxl_engine()
        image, meta = sdxl.generate(prompt, seed=seed, width=W, height=H)
        return image, {"method": "sdxl_pure", "sdxl_meta": meta}

    # ------------------------------------------------------------------
    # Outils internes
    # ------------------------------------------------------------------

    def _decide_mode(self, autonomy: float) -> str:
        """Determine le mode de generation selon le score d'autonomie."""
        if autonomy >= THRESHOLDS["harmonic_pure"]:
            return "harmonic_pure"
        elif autonomy >= THRESHOLDS["sdxl_harmonic"]:
            return "harmonic_partial"
        elif autonomy >= THRESHOLDS["sdxl_pure"]:
            return "sdxl_harmonic"
        else:
            return "sdxl_pure"

    def _tokenize_prompt(self, prompt: str) -> List[str]:
        """Tokenise un prompt en mots-cles semantiques."""
        import re
        stop_words = {
            "a", "an", "the", "with", "and", "or", "in", "on", "at", "over",
            "under", "of", "to", "for", "from", "by", "is", "are",
        }
        clean = re.sub(r'[,.\-!?;:]', ' ', prompt.lower())
        words = [w for w in clean.split() if len(w) >= 3 and w not in stop_words]
        return words[:10]  # Limite a 10 tokens

    def _prompt_to_signature_direct(self, prompt: str) -> np.ndarray:
        """Genere une signature harmonique directement depuis un prompt (sans image)."""
        sig = np.zeros(512, dtype=np.float32)
        prompt_bytes = prompt.encode("utf-8")
        PHI = 1.6180339887
        PHI2 = 2.6180339887

        for i, byte in enumerate(prompt_bytes[:256]):
            sig[i % 64] += np.sin(byte * PHI / 128.0)
            sig[64 + i % 64] += np.cos(byte * PHI2 / 128.0)

        sig[128:] = np.sin(np.arange(384, dtype=np.float32) * PHI / 384.0)

        norm = np.linalg.norm(sig)
        if norm > 1e-8:
            sig /= norm
        return sig

    def _fuse_chromatic_profiles(self, profiles: List[Dict]) -> Dict:
        """Fusionne plusieurs profils chromatiques."""
        PHI = 1.6180339887
        valid = [p for p in profiles if p]
        if not valid:
            return {}

        weights = np.array([1.0 / ((i + 1) ** PHI) for i in range(len(valid))],
                           dtype=np.float64)
        weights /= weights.sum()

        fused = {}
        for key in ["mean_rgb", "std_rgb"]:
            vals = [np.asarray(p.get(key, [0.5, 0.5, 0.5]), dtype=np.float64)
                    for p in valid if key in p]
            if vals:
                fused[key] = sum(w * v for w, v in zip(weights[:len(vals)], vals))
        return fused

    def _auto_ingest(
        self, image: np.ndarray, prompt: str, tokens: List[str]
    ) -> Optional[str]:
        """Ingere automatiquement une image generee dans la BDD."""
        try:
            sig, sig_meta = self._extractor.extract(image)
            quality = sig_meta.get("overall_quality", 0.0)

            chroma = {
                "mean_rgb": (image.astype(np.float32) / 255.0).mean(axis=(0, 1)).tolist(),
                "std_rgb": (image.astype(np.float32) / 255.0).std(axis=(0, 1)).tolist(),
            }

            obj_id = self.db.ingest(
                signature=sig,
                tags=tokens,
                source_type="adaptive_generated",
                chromatic_profile=chroma,
                quality_score=quality,
                harmony_score=sig_meta.get("harmony_score", 0.70),
                resolution=(image.shape[1], image.shape[0]),
            )

            if obj_id:
                logger.debug(f"Auto-ingere: {obj_id[:8]}... | tags={tokens[:3]}")

            return obj_id

        except Exception as e:
            logger.warning(f"Erreur auto-ingestion: {e}")
            return None

    def _get_sdxl_engine(self) -> SDXLCPUEngine:
        """Retourne le moteur SDXL (charge a la demande)."""
        if self._sdxl is None:
            self._sdxl = SDXLCPUEngine(
                model=self._sdxl_model,
                quantize=True,
                num_steps=2,
                output_resolution=self.resolution,
            )
            self._sdxl.load()
        return self._sdxl

    def _log_result(self, result: GenerationResult):
        """Affiche le resultat de generation."""
        logger.info(
            f"  OK | mode={result.mode} | conf={result.confidence:.2f} | "
            f"t={result.generation_time_s*1000:.0f}ms | "
            f"ingere={'oui' if result.object_id else 'non'}"
        )

    # ------------------------------------------------------------------
    # Gestion de la BDD
    # ------------------------------------------------------------------

    def bootstrap_db(self, n_prompts: int = 50, model: Optional[str] = None) -> Dict:
        """
        Demarre l'amorçage de la BDD avec des prompts de base.
        Lance l'ingestion en mode leger (LCM ou fallback).

        Args:
            n_prompts: nombre de prompts a generer (50 = test rapide)
            model: modele a utiliser (None = automatique)

        Returns:
            stats d'ingestion
        """
        from .sdxl_ingestor import BASE_CATEGORIES, IngestionConfig, SDXLIngestor

        # Choix du modele
        if model is None:
            autonomy = self.db.get_autonomy_score()
            model = "fallback-harmonic" if autonomy > 0 else self._sdxl_model

        # Construction de prompts de bootstrap
        all_prompts = []
        for cat_prompts in BASE_CATEGORIES.values():
            all_prompts.extend(cat_prompts[:2])  # 2 par categorie
        all_prompts = all_prompts[:n_prompts]

        logger.info(f"Bootstrap BDD: {len(all_prompts)} prompts | model={model}")

        config = IngestionConfig(
            sdxl_model=model,
            sdxl_steps=1,
            resolution=(256, 256),
            batch_size=5,
            delay_between_batches_s=0.0,
        )

        ingestor = SDXLIngestor(self.db, config)
        stats = ingestor._run_ingestion(all_prompts, phase="bootstrap")

        self.db.print_status()
        return {"accepted": stats.accepted, "autonomy": self.db.get_autonomy_score()}

    def get_session_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la session courante."""
        elapsed = time.time() - self._session_stats["started_at"]
        return {
            **self._session_stats,
            "elapsed_s": elapsed,
            "harmonic_ratio": (
                self._session_stats["harmonic_calls"] /
                max(1, self._session_stats["total_generations"])
            ),
            "current_autonomy": self.db.get_autonomy_score(),
            "db_total_objects": self.db.get_stats().total_objects,
        }

    def print_session_report(self):
        """Affiche un rapport complet de la session."""
        stats = self.get_session_stats()
        print("\n=== Rapport Session AdaptiveLearner ===")
        print(f"  Generations totales : {stats['total_generations']}")
        print(f"  Appels SDXL         : {stats['sdxl_calls']}")
        print(f"  Appels Harmonique   : {stats['harmonic_calls']}")
        print(f"  Ratio harmonique    : {stats['harmonic_ratio']*100:.1f}%")
        print(f"  Auto-ingestees      : {stats['auto_ingested']}")
        print(f"  Duree session       : {stats['elapsed_s']:.1f}s")
        print(f"  Score autonomie BDD : {stats['current_autonomy']*100:.1f}%")
        print(f"  Objets en BDD       : {stats['db_total_objects']:,}")
        print("======================================\n")

    # ------------------------------------------------------------------
    # Upscaling harmonique integre
    # ------------------------------------------------------------------

    def _get_upscaler_bridge(self):
        """Retourne le bridge upscaler (charge a la demande)."""
        if self._upscaler_bridge is None:
            from .harmonic_upscaler_bridge import HarmonicUpscalerBridge
            self._upscaler_bridge = HarmonicUpscalerBridge(energy_level="standard")
            if self.verbose:
                status = self._upscaler_bridge.get_status()
                logger.info(
                    f"HarmonicUpscalerBridge charge | "
                    f"disponible={status['available']}"
                )
        return self._upscaler_bridge

    def generate_upscaled(
        self,
        prompt: str,
        target_resolution: Tuple[int, int] = (1024, 1024),
        energy_level: str = "standard",
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Pipeline complet : generation basse resolution + upscaling harmonique.

        Strategie optimale CPU :
          - SDXL 256x256 (~15s) + upscale x4 (~0.8s) = 1024x1024 en ~16s
            vs SDXL 1024x1024 (~120s) : gain x7.5
          - Harmonic 256x256 (<1ms) + upscale x4 (~0.8s) = 1024x1024 en <1s

        La signature harmonique guide l'upscaling :
          -> Correction gamma phi-base pre-upscale
          -> Renforcement des frequences coherentes post-upscale
          -> Coherence spectrale avec la signature BDD

        Args:
            prompt: description textuelle
            target_resolution: (width, height) de la sortie finale
            energy_level: qualite upscaling ("preview" | "standard" | "high" | "ultra")
            seed: graine pour reproductibilite

        Returns:
            dict avec cles :
              'image'           : np.ndarray uint8 haute resolution
              'gen_image'       : image generee avant upscale
              'signature'       : signature harmonique 512D
              'upscale_factor'  : facteur d'upscaling applique
              'gen_resolution'  : resolution de generation
              'target_resolution': resolution finale
              'time_generation_s': temps de generation
              'time_upscale_s'  : temps d'upscaling
              'time_total_s'    : temps total
              'speedup_vs_direct': gain de vitesse estime
              'gen_mode'        : mode de generation utilise
        """
        bridge = self._get_upscaler_bridge()
        return bridge.generate_and_upscale(
            learner=self,
            prompt=prompt,
            target_resolution=target_resolution,
            energy_level=energy_level,
            seed=seed,
        )

    def generate_video_upscaled(
        self,
        prompt: str,
        n_frames: int = 24,
        fps: float = 24.0,
        target_resolution: Tuple[int, int] = (1024, 1024),
        energy_level: str = "standard",
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Pipeline video complet : generation + upscaling avec coherence temporelle.

        Evite le flickering entre frames grace a la signature harmonique
        de la frame precedente qui guide l'upscaling de la suivante.

        Args:
            prompt: description textuelle
            n_frames: nombre de frames
            fps: images par seconde
            target_resolution: (width, height) de sortie
            energy_level: qualite upscaling
            seed: graine

        Returns:
            dict avec 'frames' (liste de np.ndarray), 'upscale_stats', etc.
        """
        bridge = self._get_upscaler_bridge()
        return bridge.generate_video_and_upscale(
            learner=self,
            prompt=prompt,
            n_frames=n_frames,
            fps=fps,
            target_resolution=target_resolution,
            energy_level=energy_level,
            seed=seed,
        )

    def upscale(
        self,
        image: np.ndarray,
        factor: float = 2.0,
        signature: Optional[np.ndarray] = None,
        energy_level: str = "standard",
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Upscale une image existante avec l'upscaler harmonique.

        Si une signature est fournie, l'upscaling est guide harmoniquement.
        Sinon, la signature est extraite depuis l'image automatiquement.

        Args:
            image: image RGB uint8 a upscaler
            factor: facteur d'upscaling (2.0, 3.0, 4.0...)
            signature: signature harmonique 512D (None = extraction automatique)
            energy_level: qualite upscaling

        Returns:
            (image_upscalee uint8, metadonnees dict)
        """
        bridge = self._get_upscaler_bridge()

        if signature is None:
            # Extraction automatique de la signature
            signature, sig_meta = self._extractor.extract(image)
            logger.debug(
                f"Signature extraite pour upscale | "
                f"qualite={sig_meta.get('overall_quality', 0.0):.2f}"
            )

        return bridge.upscale_with_signature(
            image, signature, factor=factor, energy_level=energy_level
        )

    def upscaler_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'upscaler harmonique."""
        bridge = self._get_upscaler_bridge()
        return bridge.get_status()

    # ------------------------------------------------------------------
    # Compression harmonique integree
    # ------------------------------------------------------------------

    def _get_compressor_bridge(self):
        """Retourne le bridge compresseur (charge a la demande)."""
        if not hasattr(self, "_compressor_bridge") or self._compressor_bridge is None:
            from .harmonic_compressor_bridge import HarmonicCompressorBridge
            self._compressor_bridge = HarmonicCompressorBridge(
                preset="balanced", auto_quality=True
            )
            if self.verbose:
                status = self._compressor_bridge.get_status()
                logger.info(
                    f"HarmonicCompressorBridge charge | "
                    f"disponible={status['available']} | "
                    f"scipy_dct={status['scipy_dct']}"
                )
        return self._compressor_bridge

    def save_compressed(
        self,
        image: np.ndarray,
        path: str,
        signature: Optional[np.ndarray] = None,
        quality: Optional[float] = None,
        extra_meta: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Sauvegarde une image en format harmonique compresse (.hce).

        Le format .hce (Harmonic Codec Encoded) offre :
          - Q=75 (equilibre)  : ratio ~18:1, PSNR ~33 dB
          - Q=60 (efficace)   : ratio ~35:1, PSNR ~27 dB
          - Q=85 (haute qual.): ratio ~8:1,  PSNR ~38 dB

        Les images generees harmoniquement compriment MIEUX que
        les images naturelles car leur contenu DCT est regulier.

        Si une signature est fournie (ou extraite automatiquement),
        elle est embeddee dans le .hce -> re-ingestion BDD automatique
        possible a la decompression.

        Args:
            image: RGB uint8 a sauvegarder
            path: chemin de sortie (.hce recommande)
            signature: signature 512D (None = extraction automatique)
            quality: qualite 1-100 (None = auto depuis signature)
            extra_meta: metadonnees supplementaires (prompt, mode, etc.)

        Returns:
            dict avec 'file_path', 'file_size_bytes', 'compression_ratio', etc.
        """
        bridge = self._get_compressor_bridge()

        # Extraction auto de la signature si non fournie
        if signature is None:
            signature, sig_meta = self._extractor.extract(image)
            if extra_meta is None:
                extra_meta = {}
            extra_meta["sig_quality"] = sig_meta.get("overall_quality", 0.0)

        return bridge.save(image, path, signature=signature, quality=quality,
                           extra_meta=extra_meta)

    def generate_compressed(
        self,
        prompt: str,
        path: str,
        quality: Optional[float] = None,
        seed: Optional[int] = None,
        upscale_target: Optional[Tuple[int, int]] = None,
        energy_level: str = "standard",
    ) -> Dict[str, Any]:
        """
        Pipeline complet : Generation + (Upscaling) + Compression harmonique.

        1. Genere l'image (mode adaptatif)
        2. Si upscale_target : upscale avec coherence harmonique
        3. Compresse en .hce avec la signature embeddee
        4. Sauvegarde le fichier

        Args:
            prompt: description textuelle
            path: chemin de sortie .hce
            quality: qualite compression (None = auto)
            seed: graine
            upscale_target: (width, height) si upscaling avant compression
            energy_level: qualite upscaling si upscale_target fourni

        Returns:
            dict avec 'image', 'file_path', 'compression_ratio',
            'gen_mode', 'time_total_s', etc.
        """
        t0 = time.time()

        if upscale_target:
            # Pipeline gen + upscale + compression
            upscale_result = self.generate_upscaled(
                prompt,
                target_resolution=upscale_target,
                energy_level=energy_level,
                seed=seed,
            )
            image = upscale_result["image"]
            signature = upscale_result.get("signature")
            gen_mode = upscale_result.get("gen_mode", "unknown")
            t_gen = upscale_result.get("time_total_s", 0.0)
        else:
            # Generation simple
            result = self.generate(prompt, seed=seed)
            image = result.image
            signature = None  # Extraction auto dans save_compressed
            gen_mode = result.mode
            t_gen = result.generation_time_s

        # Compression
        extra = {
            "prompt": prompt[:80],
            "gen_mode": gen_mode,
            "seed": seed,
            "upscaled": upscale_target is not None,
        }
        save_meta = self.save_compressed(
            image, path, signature=signature, quality=quality, extra_meta=extra
        )

        # Enrichissement des metadonnees
        save_meta["image"] = image
        save_meta["gen_mode"] = gen_mode
        save_meta["time_generation_s"] = t_gen
        save_meta["time_total_s"] = time.time() - t0
        save_meta["prompt"] = prompt

        if self.verbose:
            logger.info(
                f"generate_compressed '{prompt[:40]}' | "
                f"mode={gen_mode} | "
                f"ratio={save_meta.get('compression_ratio', 0):.1f}:1 | "
                f"{save_meta.get('file_size_bytes', 0):,}B | "
                f"{save_meta['time_total_s']*1000:.0f}ms"
            )

        return save_meta

    def generate_video_compressed(
        self,
        prompt: str,
        output_dir: str,
        n_frames: int = 24,
        fps: float = 24.0,
        quality: Optional[float] = None,
        upscale_target: Optional[Tuple[int, int]] = None,
        energy_level: str = "standard",
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Pipeline video complet : Generation + (Upscaling) + Compression par frame.

        Sauvegarde dans output_dir/ :
          manifest.json       (fps, n_frames, ratio global, stats)
          frame_0000.hce     (chaque frame compresse avec sa signature)
          frame_0001.hce
          ...

        Args:
            prompt: description textuelle
            output_dir: dossier de sortie
            n_frames: nombre de frames
            fps: images par seconde
            quality: qualite compression (None = auto par frame)
            upscale_target: (width, height) si upscaling avant compression
            energy_level: qualite upscaling
            seed: graine

        Returns:
            manifest dict avec stats completes
        """
        t0 = time.time()
        bridge = self._get_compressor_bridge()

        if upscale_target:
            result = self.generate_video_upscaled(
                prompt, n_frames=n_frames, fps=fps,
                target_resolution=upscale_target,
                energy_level=energy_level, seed=seed,
            )
            frames = result["frames"]
            # Extraction des signatures depuis les frames upscalees
            signatures = None  # bridge.save_video extrait auto
        else:
            frames = self.generate_video(prompt, n_frames=n_frames, fps=fps, seed=seed)
            signatures = None

        manifest = bridge.save_video(
            frames,
            base_path=output_dir,
            signatures=signatures,
            quality=quality,
            fps=fps,
        )

        manifest["prompt"] = prompt
        manifest["gen_mode"] = "adaptive"
        manifest["upscaled"] = upscale_target is not None
        manifest["time_total_s"] = time.time() - t0

        return manifest

    def load_compressed(
        self, path: str, re_ingest: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Dict]:
        """
        Charge un fichier .hce et optionnellement re-ingere dans la BDD.

        Args:
            path: chemin du .hce
            re_ingest: si True et signature presente, re-ingere dans la BDD

        Returns:
            (image_float32, signature_ou_None, metadonnees)
        """
        bridge = self._get_compressor_bridge()
        image, signature, meta = bridge.load(path)

        if re_ingest and signature is not None:
            # Re-ingestion dans la BDD depuis la signature embeddee
            image_u8 = (image * 255).clip(0, 255).astype(np.uint8)
            extra = meta.get("extra", {})
            tags = []
            if extra.get("prompt"):
                tags = self._tokenize_prompt(extra["prompt"])

            obj_id = self.db.ingest(
                signature=signature,
                tags=tags,
                source_type="loaded_hce",
                quality_score=meta.get("sig_quality", 0.7),
                harmony_score=0.75,
                resolution=(image.shape[1], image.shape[0]),
            )
            meta["re_ingested_id"] = obj_id
            if obj_id and self.verbose:
                logger.info(f"Re-ingere depuis .hce: {obj_id[:8]}...")

        return image, signature, meta

    def compressor_status(self) -> Dict[str, Any]:
        """Retourne le statut du compresseur harmonique."""
        bridge = self._get_compressor_bridge()
        return bridge.get_status()

    def close(self):
        """Ferme les ressources."""
        if self._sdxl:
            self._sdxl.unload()
        self.db.close()


# ---------------------------------------------------------------------------
# Test autonome
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.stdout.reconfigure(encoding="utf-8")

    print("=== Test AdaptiveLearner ===\n")

    # Creation du learner avec BDD de test
    learner = AdaptiveLearner(
        db_dir="harmonic_db_adaptive_test",
        sdxl_model="fallback-harmonic",
        resolution=(128, 128),
        auto_ingest=True,
        verbose=True,
    )

    print(f"\nScore autonomie initial: {learner.db.get_autonomy_score()*100:.1f}%")

    # Bootstrap leger
    print("\nBootstrap BDD (10 prompts)...")
    bootstrap_result = learner.bootstrap_db(n_prompts=10, model="fallback-harmonic")
    print(f"Bootstrap: {bootstrap_result}")

    # Test de generation
    test_prompts = [
        "a beautiful sunset over the ocean",
        "a dense forest with morning mist",
        "a futuristic city skyline at night",
    ]

    print("\nTest de generation adaptative:")
    for prompt in test_prompts:
        result = learner.generate(prompt, seed=42)
        print(f"\n  Prompt: '{prompt[:50]}'")
        print(f"  Mode   : {result.mode}")
        print(f"  Confiance: {result.confidence:.2f}")
        print(f"  Temps  : {result.generation_time_s*1000:.0f}ms")
        print(f"  Image  : {result.image.shape}")
        print(f"  Ingere : {'oui' if result.object_id else 'non'}")

    # Generation video
    print("\nTest generation video (6 frames 64x64)...")
    frames = learner.generate_video(
        "a sunset over the ocean",
        n_frames=6,
        fps=12.0,
    )
    print(f"  {len(frames)} frames generees | shape={frames[0].shape}")

    # Rapport final
    learner.print_session_report()

    # Sauvegarde image demo
    try:
        from PIL import Image as PILImage
        last_result = learner.generate("golden hour landscape", seed=0)
        PILImage.fromarray(last_result.image).save("adaptive_demo.png")
        print("Demo sauvegardee: adaptive_demo.png")
    except ImportError:
        pass

    learner.close()
    print("\n=== Test termine avec succes ===")
