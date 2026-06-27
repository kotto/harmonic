#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDXLIngestor - Pipeline d'ingestion SDXL -> Base de donnees harmonique
======================================================================
Orchestre la generation d'images via SDXL CPU et leur ingestion
dans la base de donnees harmonique avec extraction de signature.

Workflow :
  Prompt --> SDXLCPUEngine --> Image --> HarmonicSignatureExtractor
                                             --> HarmonicDatabase.ingest()

Strategies de remplissage progressif de la BDD :
  Phase 1 (Amorçage)    : 500 categories x 5 = 2500 images
  Phase 2 (Densification): 10000 images supplementaires
  Phase 3 (Specialisation): 50000 images
"""

import os
import time
import json
import logging
import threading
from typing import List, Dict, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, field, asdict

import numpy as np

from .harmonic_db import HarmonicDatabase
from .harmonic_signature import HarmonicSignatureExtractor
from .sdxl_cpu_engine import SDXLCPUEngine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Catalogue semantique de base (Phase 1 : 500 categories)
# ---------------------------------------------------------------------------

BASE_CATEGORIES = {
    "nature": [
        "a beautiful sunset over the ocean", "a dense tropical forest",
        "snow-capped mountain peaks", "a golden wheat field at harvest",
        "a misty morning lake", "colorful autumn leaves",
        "a sandy desert with dunes", "a rocky coastline with waves",
        "a waterfall in a jungle", "a flower meadow in spring",
    ],
    "urban": [
        "a modern city skyline at night", "a cobblestone alley in Europe",
        "a futuristic skyscraper", "a busy market street",
        "an empty industrial warehouse", "a neon-lit downtown area",
        "a peaceful suburban neighborhood", "an ancient city ruins",
    ],
    "celestial": [
        "a starry night sky over mountains", "a solar eclipse",
        "the aurora borealis over a lake", "a full moon over the ocean",
        "a comet crossing the night sky", "a galaxy in deep space",
        "a sunrise through clouds", "lightning storm over the sea",
    ],
    "textures": [
        "smooth marble texture", "rough stone wall texture",
        "wooden plank surface", "fabric weave close-up",
        "water ripples surface", "sand grain texture",
        "metal rust texture", "glass reflection texture",
    ],
    "light": [
        "golden hour light rays through trees", "blue hour city lights",
        "harsh midday sunlight on desert", "soft diffused overcast light",
        "candle flame close-up", "neon glow on wet pavement",
        "underwater caustic light", "fire light in darkness",
    ],
    "colors": [
        "vibrant red abstract composition", "deep ocean blue gradient",
        "emerald green natural scene", "warm orange autumn landscape",
        "purple twilight sky", "monochrome black and white scene",
        "pastel pink cherry blossoms", "golden yellow sunflower field",
    ],
    "abstract": [
        "fractal geometric pattern", "flowing liquid abstract",
        "bokeh light circles", "long exposure light trails",
        "smoke and fog abstract", "crystal formation close-up",
        "ice pattern on glass", "soap bubble iridescent",
    ],
    "elements": [
        "fire flames close-up", "water splash frozen moment",
        "earth soil and roots", "wind in grass field",
        "thunderstorm clouds", "fog over valley",
        "rain on window glass", "snow falling in forest",
    ],
}


@dataclass
class IngestionConfig:
    """Configuration du pipeline d'ingestion."""
    prompts_per_category: int = 5
    batch_size: int = 10
    min_quality_score: float = 0.68
    save_checkpoint_every: int = 50
    checkpoint_dir: str = "harmonic_db/checkpoints"
    max_retries: int = 2
    delay_between_batches_s: float = 1.0
    resolution: Tuple[int, int] = (512, 512)
    sdxl_steps: int = 2
    sdxl_model: str = "sdxl-turbo"


@dataclass
class IngestionStats:
    """Statistiques d'une session d'ingestion."""
    session_id: str = ""
    started_at: float = 0.0
    total_prompts: int = 0
    generated: int = 0
    accepted: int = 0
    rejected: int = 0
    errors: int = 0
    elapsed_s: float = 0.0
    avg_time_per_image_s: float = 0.0
    estimated_remaining_s: float = 0.0

    @property
    def acceptance_rate(self) -> float:
        if self.generated == 0:
            return 0.0
        return self.accepted / self.generated

    @property
    def progress_pct(self) -> float:
        if self.total_prompts == 0:
            return 0.0
        return self.generated / self.total_prompts * 100


class SDXLIngestor:
    """
    Pipeline d'ingestion SDXL -> BDD harmonique.

    Usage:
        db = HarmonicDatabase("harmonic_db/")
        ingestor = SDXLIngestor(db, config=IngestionConfig())
        stats = ingestor.run_phase1()  # Amorçage initial
    """

    def __init__(
        self,
        db: HarmonicDatabase,
        config: Optional[IngestionConfig] = None,
        sdxl_engine: Optional[SDXLCPUEngine] = None,
        signature_extractor: Optional[HarmonicSignatureExtractor] = None,
        progress_callback: Optional[Callable] = None,
    ):
        self.db = db
        self.config = config or IngestionConfig()
        self.progress_callback = progress_callback

        # Moteur SDXL
        self._sdxl = sdxl_engine or SDXLCPUEngine(
            model=self.config.sdxl_model,
            quantize=True,
            num_steps=self.config.sdxl_steps,
            output_resolution=self.config.resolution,
        )

        # Extracteur de signature
        self._extractor = signature_extractor or HarmonicSignatureExtractor()

        # Stats de session
        self._stats = IngestionStats()
        self._stop_flag = threading.Event()

        # Checkpoint
        Path(self.config.checkpoint_dir).mkdir(parents=True, exist_ok=True)

        logger.info("SDXLIngestor initialise")

    # ------------------------------------------------------------------
    # Phases d'ingestion
    # ------------------------------------------------------------------

    def run_phase1(self) -> IngestionStats:
        """
        Phase 1 : Amorçage de la BDD avec les categories de base.
        Genere ~2500 images couvrant les concepts fondamentaux.
        """
        logger.info("=== PHASE 1 : Amorçage de la BDD harmonique ===")

        prompts = self._build_phase1_prompts()
        logger.info(f"Phase 1: {len(prompts)} prompts")

        return self._run_ingestion(prompts, phase="phase1")

    def run_phase2(self, extra_prompts: Optional[List[str]] = None) -> IngestionStats:
        """
        Phase 2 : Densification - sous-categories et variantes.
        Genere ~10000 images supplementaires.
        """
        logger.info("=== PHASE 2 : Densification de la BDD harmonique ===")

        prompts = self._build_phase2_prompts()
        if extra_prompts:
            prompts.extend(extra_prompts)

        logger.info(f"Phase 2: {len(prompts)} prompts")
        return self._run_ingestion(prompts, phase="phase2")

    def ingest_single(
        self,
        prompt: str,
        tags: Optional[List[str]] = None,
        seed: Optional[int] = None,
    ) -> Optional[str]:
        """
        Ingere une seule image generee depuis un prompt.

        Args:
            prompt: texte du prompt
            tags: tags supplementaires (s'ajoutent aux tags auto-extraits)
            seed: graine pour reproductibilite

        Returns:
            object_id si accepte, None si rejete
        """
        if self._sdxl._mode == "unloaded":
            self._sdxl.load()

        # Generation
        t0 = time.time()
        try:
            image, meta = self._sdxl.generate(prompt, seed=seed)
        except Exception as e:
            logger.error(f"Erreur generation '{prompt[:40]}': {e}")
            return None

        gen_time = time.time() - t0

        # Extraction signature
        try:
            signature, sig_meta = self._extractor.extract(image)
        except Exception as e:
            logger.error(f"Erreur extraction signature: {e}")
            return None

        quality = sig_meta.get("overall_quality", 0.0)

        # Construction des tags
        auto_tags = self._extract_tags_from_prompt(prompt)
        all_tags = list(set(auto_tags + (tags or [])))

        # Profil chromatique
        chroma_profile = self._build_chromatic_profile(image, sig_meta)

        # Ingestion dans la BDD
        object_id = self.db.ingest(
            signature=signature,
            tags=all_tags,
            source_type=f"sdxl_{meta.get('mode', 'unknown')}",
            chromatic_profile=chroma_profile,
            quality_score=quality,
            harmony_score=sig_meta.get("harmony_score", 0.75),
            resolution=(image.shape[1], image.shape[0]),
        )

        if object_id:
            logger.debug(
                f"Ingere '{prompt[:40]}...' -> {object_id[:8]}... "
                f"q={quality:.2f} t={gen_time:.1f}s"
            )

        return object_id

    def ingest_custom_image(
        self,
        image: np.ndarray,
        prompt: str,
        tags: Optional[List[str]] = None,
        source: str = "real",
    ) -> Optional[str]:
        """
        Ingere une image reelle (pas generee par SDXL).
        Utile pour enrichir la BDD avec des images existantes.

        Args:
            image: image RGB uint8
            prompt: description textuelle
            tags: tags semantiques
            source: type de source ("real", "stock", "user", etc.)

        Returns:
            object_id si accepte
        """
        # Extraction signature
        try:
            signature, sig_meta = self._extractor.extract(image)
        except Exception as e:
            logger.error(f"Erreur extraction signature image custom: {e}")
            return None

        quality = sig_meta.get("overall_quality", 0.0)
        all_tags = list(set(self._extract_tags_from_prompt(prompt) + (tags or [])))
        chroma_profile = self._build_chromatic_profile(image, sig_meta)

        return self.db.ingest(
            signature=signature,
            tags=all_tags,
            source_type=source,
            chromatic_profile=chroma_profile,
            quality_score=quality,
            harmony_score=sig_meta.get("harmony_score", 0.75),
            resolution=(image.shape[1], image.shape[0]),
        )

    # ------------------------------------------------------------------
    # Moteur d'ingestion interne
    # ------------------------------------------------------------------

    def _run_ingestion(
        self, prompts: List[str], phase: str = "custom"
    ) -> IngestionStats:
        """Moteur principal d'ingestion en batch."""
        import uuid

        self._stats = IngestionStats(
            session_id=str(uuid.uuid4())[:8],
            started_at=time.time(),
            total_prompts=len(prompts),
        )
        self._stop_flag.clear()

        # Chargement du moteur SDXL
        logger.info(f"Chargement moteur SDXL ({self.config.sdxl_model})...")
        self._sdxl.load()

        logger.info(
            f"Session {self._stats.session_id} | {len(prompts)} prompts | "
            f"batch_size={self.config.batch_size}"
        )

        n_batches = (len(prompts) + self.config.batch_size - 1) // self.config.batch_size

        for batch_idx in range(n_batches):
            if self._stop_flag.is_set():
                logger.info("Arret demande, fin de l'ingestion")
                break

            batch_start = batch_idx * self.config.batch_size
            batch_end = min(batch_start + self.config.batch_size, len(prompts))
            batch = prompts[batch_start:batch_end]

            logger.info(
                f"Batch {batch_idx+1}/{n_batches} | "
                f"prompts {batch_start+1}-{batch_end}"
            )

            # Traitement du batch
            for prompt_idx, prompt in enumerate(batch):
                global_idx = batch_start + prompt_idx
                seed = global_idx * 1337 + hash(phase) % 10000

                # Tentatives
                obj_id = None
                for attempt in range(self.config.max_retries):
                    obj_id = self.ingest_single(prompt, seed=seed + attempt)
                    if obj_id:
                        break

                self._stats.generated += 1
                if obj_id:
                    self._stats.accepted += 1
                else:
                    self._stats.rejected += 1

                # Mise a jour stats
                elapsed = time.time() - self._stats.started_at
                self._stats.elapsed_s = elapsed
                if self._stats.generated > 0:
                    self._stats.avg_time_per_image_s = elapsed / self._stats.generated
                    remaining = len(prompts) - self._stats.generated
                    self._stats.estimated_remaining_s = (
                        remaining * self._stats.avg_time_per_image_s
                    )

                # Callback progression
                if self.progress_callback:
                    try:
                        self.progress_callback(self._stats)
                    except Exception:
                        pass

                # Log progression
                if (global_idx + 1) % 10 == 0 or global_idx == len(prompts) - 1:
                    self._log_progress()

            # Checkpoint periodique
            if (batch_idx + 1) % (self.config.save_checkpoint_every // self.config.batch_size + 1) == 0:
                self._save_checkpoint(phase)

            # Pause entre batches
            if self.config.delay_between_batches_s > 0 and batch_idx < n_batches - 1:
                time.sleep(self.config.delay_between_batches_s)

        # Stats finales
        self._stats.elapsed_s = time.time() - self._stats.started_at
        self._save_checkpoint(phase, final=True)

        logger.info(
            f"\n=== Ingestion terminee ===\n"
            f"  Generes  : {self._stats.generated}\n"
            f"  Acceptes : {self._stats.accepted} "
            f"({self._stats.acceptance_rate*100:.1f}%)\n"
            f"  Rejetes  : {self._stats.rejected}\n"
            f"  Temps    : {self._stats.elapsed_s:.1f}s\n"
            f"  Moy/img  : {self._stats.avg_time_per_image_s:.1f}s"
        )

        return self._stats

    def _log_progress(self):
        """Affiche la progression courante."""
        s = self._stats
        eta_min = s.estimated_remaining_s / 60.0
        logger.info(
            f"  [{s.generated}/{s.total_prompts}] "
            f"OK={s.accepted} Rej={s.rejected} "
            f"ETA={eta_min:.0f}min "
            f"Q_avg={s.acceptance_rate*100:.0f}%"
        )

    def _save_checkpoint(self, phase: str, final: bool = False):
        """Sauvegarde un checkpoint de la session."""
        checkpoint = {
            "phase": phase,
            "final": final,
            "stats": asdict(self._stats),
            "db_stats": asdict(self.db.get_stats()),
            "autonomy_score": self.db.get_autonomy_score(),
        }
        suffix = "final" if final else str(self._stats.generated)
        cp_path = Path(self.config.checkpoint_dir) / f"{phase}_{suffix}.json"
        try:
            with open(cp_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, indent=2, default=str)
            logger.debug(f"Checkpoint sauvegarde: {cp_path}")
        except Exception as e:
            logger.warning(f"Erreur checkpoint: {e}")

    # ------------------------------------------------------------------
    # Construction des prompts
    # ------------------------------------------------------------------

    def _build_phase1_prompts(self) -> List[str]:
        """Construit la liste de prompts pour la phase 1."""
        prompts = []
        n_per_prompt = self.config.prompts_per_category

        for category, base_prompts in BASE_CATEGORIES.items():
            for base_prompt in base_prompts:
                # Prompt de base
                prompts.append(base_prompt)

                # Variantes
                if n_per_prompt > 1:
                    variants = self._generate_prompt_variants(base_prompt, n_per_prompt - 1)
                    prompts.extend(variants)

        return prompts

    def _build_phase2_prompts(self) -> List[str]:
        """Construit les prompts pour la phase 2 (sous-categories et combinaisons)."""
        prompts = []

        # Combinaisons de categories
        categories_list = list(BASE_CATEGORIES.keys())
        for i, cat1 in enumerate(categories_list):
            for cat2 in categories_list[i + 1:]:
                p1 = BASE_CATEGORIES[cat1][0]
                p2 = BASE_CATEGORIES[cat2][0]
                combined = f"{p1} with {p2.lower()}"
                prompts.append(combined)

        # Variations stylistiques
        styles = ["photorealistic", "cinematic", "oil painting", "watercolor",
                  "minimalist", "dramatic lighting", "high contrast", "soft focus"]

        for category, base_prompts in BASE_CATEGORIES.items():
            for style in styles[:2]:  # 2 styles par categorie
                base = base_prompts[0]
                prompts.append(f"{base}, {style} style")

        return prompts

    def _generate_prompt_variants(self, base_prompt: str, n: int) -> List[str]:
        """Genere n variantes d'un prompt de base."""
        modifiers = [
            "at golden hour", "in dramatic lighting", "with soft colors",
            "with high contrast", "in misty atmosphere", "at blue hour",
            "with vivid colors", "in monochrome", "with bokeh background",
            "ultra detailed", "photorealistic", "cinematic composition",
        ]
        variants = []
        for i in range(min(n, len(modifiers))):
            variants.append(f"{base_prompt}, {modifiers[i]}")
        return variants

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def _extract_tags_from_prompt(self, prompt: str) -> List[str]:
        """Extrait les tags semantiques depuis un prompt texte."""
        # Nettoyage et tokenisation simple
        import re
        prompt_clean = re.sub(r'[,.\-!?;:]', ' ', prompt.lower())
        words = prompt_clean.split()

        # Filtrage des mots vides
        stop_words = {
            "a", "an", "the", "with", "and", "or", "in", "on", "at", "over",
            "under", "of", "to", "for", "from", "by", "is", "are", "was",
            "were", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might",
        }
        tags = [w for w in words if len(w) >= 3 and w not in stop_words]

        # Bigrams importants
        bigrams = []
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            if len(bigram) >= 8:
                bigrams.append(bigram)

        return list(set(tags + bigrams[:5]))  # Max 5 bigrams

    def _build_chromatic_profile(
        self, image: np.ndarray, sig_meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Construit le profil chromatique depuis l'image et les metadonnees."""
        img_float = image.astype(np.float32) / 255.0

        return {
            "mean_rgb": img_float.mean(axis=(0, 1)).tolist(),
            "std_rgb": img_float.std(axis=(0, 1)).tolist(),
            "harmony_score": sig_meta.get("harmony_score", 0.75),
            "texture_richness": sig_meta.get("texture_richness", 0.70),
        }

    def stop(self):
        """Arrete l'ingestion apres le prompt courant."""
        self._stop_flag.set()
        logger.info("Arret de l'ingestion demande")

    def get_stats(self) -> IngestionStats:
        """Retourne les statistiques courantes."""
        return self._stats


# ---------------------------------------------------------------------------
# Fonction utilitaire rapide
# ---------------------------------------------------------------------------

def quick_ingest_batch(
    prompts: List[str],
    db_dir: str = "harmonic_db",
    model: str = "fallback-harmonic",
    steps: int = 2,
) -> Tuple[HarmonicDatabase, IngestionStats]:
    """
    Ingestion rapide d'une liste de prompts.

    Args:
        prompts: liste de prompts
        db_dir: repertoire de la base de donnees
        model: modele SDXL a utiliser
        steps: nombre d'etapes de denoising

    Returns:
        (db, stats)
    """
    db = HarmonicDatabase(db_dir)
    config = IngestionConfig(sdxl_model=model, sdxl_steps=steps)
    ingestor = SDXLIngestor(db, config)
    stats = ingestor._run_ingestion(prompts, phase="quick_batch")
    return db, stats


# ---------------------------------------------------------------------------
# Test autonome
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.stdout.reconfigure(encoding="utf-8")

    print("=== Test SDXLIngestor ===\n")

    # Creation de la BDD de test
    db = HarmonicDatabase("harmonic_db_ingest_test")

    # Configuration legere pour le test
    config = IngestionConfig(
        prompts_per_category=2,
        batch_size=3,
        sdxl_model="fallback-harmonic",  # Pas besoin de SDXL pour le test
        sdxl_steps=1,
        resolution=(128, 128),
    )

    # Callback de progression
    def on_progress(stats: IngestionStats):
        print(f"  [{stats.generated}/{stats.total_prompts}] "
              f"Acceptes: {stats.accepted} "
              f"({stats.acceptance_rate*100:.0f}%)")

    # Ingesteur
    ingestor = SDXLIngestor(db, config, progress_callback=on_progress)

    # Test phase 1 (subset)
    test_prompts = [
        "a beautiful sunset over the ocean",
        "a dense tropical forest",
        "snow-capped mountain peaks",
        "a modern city skyline at night",
        "a starry night sky",
    ]

    print(f"Test ingestion de {len(test_prompts)} prompts...")
    stats = ingestor._run_ingestion(test_prompts, phase="test")

    print(f"\nResultats:")
    print(f"  Generes  : {stats.generated}")
    print(f"  Acceptes : {stats.accepted} ({stats.acceptance_rate*100:.1f}%)")
    print(f"  Rejetes  : {stats.rejected}")
    print(f"  Temps    : {stats.elapsed_s:.2f}s")

    db.print_status()
    db.close()

    print("\n=== Test termine ===")
