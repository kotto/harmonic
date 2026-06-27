#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HarmonicDatabase - Base de donnees vectorielle des signatures harmoniques
=========================================================================
Stocke et indexe les objets visuels avec leurs signatures harmoniques 512D.
Permet un lookup ultra-rapide par tokens semantiques.

Backend : SQLite3 (zero dependance serveur) + numpy pour les vecteurs.
"""

import sqlite3
import numpy as np
import json
import uuid
import time
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

# Constantes harmoniques
PHI = 1.6180339887
PHI2 = 2.6180339887
SIGNATURE_DIM = 512

# Seuils de qualite
QUALITY_THRESHOLDS = {
    "harmony_score_min": 0.70,
    "chromatic_consistency_min": 0.65,
    "texture_richness_min": 0.60,
    "spatial_coherence_min": 0.70,
    "overall_quality_min": 0.68,
}


@dataclass
class HarmonicObject:
    """Objet visuel avec sa signature harmonique complete."""
    object_id: str
    prompt_tags: List[str]
    harmonic_signature: np.ndarray   # vecteur 512D float32
    chromatic_profile: Dict[str, Any]
    texture_dct: np.ndarray          # coefficients DCT 8x8
    spatial_phi_grid: np.ndarray     # grille phi spatiale 16x16
    source_type: str                 # "sdxl_image" | "sdxl_video" | "real"
    quality_score: float
    resolution: Tuple[int, int]
    created_at: float


@dataclass
class HarmonicDBStats:
    """Statistiques de la base de donnees."""
    total_objects: int
    sdxl_generated: int
    real_ingested: int
    avg_quality_score: float
    coverage_score: float
    unique_tags: int
    db_size_mb: float
    last_update: float


class HarmonicDatabase:
    """
    Base de donnees harmonique vectorielle.
    
    Architecture :
      - SQLite pour les metadonnees et index
      - Fichiers .npy pour les signatures volumineuses
      - Index inversé en memoire (tag -> [object_ids])
    
    Usage:
        db = HarmonicDatabase("harmonic_db/")
        obj_id = db.ingest(image, tags=["sunset", "ocean"], source="sdxl_image")
        results = db.lookup(["sunset", "warm_colors"], top_k=5)
    """

    def __init__(self, db_dir: str = "harmonic_db"):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        (self.db_dir / "signatures").mkdir(exist_ok=True)
        (self.db_dir / "index").mkdir(exist_ok=True)

        self.db_path = self.db_dir / "harmonic_objects.db"
        self._conn: Optional[sqlite3.Connection] = None

        # Index inversé en memoire : tag -> set(object_ids)
        self._tag_index: Dict[str, List[str]] = {}

        self._init_db()
        self._load_tag_index()

        logger.info(f"HarmonicDatabase initialisee: {self.db_path}")
        stats = self.get_stats()
        logger.info(f"  Objets: {stats.total_objects} | Tags uniques: {stats.unique_tags}")

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        """Cree le schema SQLite si necessaire."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS harmonic_objects (
                object_id       TEXT PRIMARY KEY,
                prompt_tags     TEXT NOT NULL,
                source_type     TEXT NOT NULL DEFAULT 'sdxl_image',
                quality_score   REAL NOT NULL DEFAULT 0.0,
                harmony_score   REAL NOT NULL DEFAULT 0.0,
                chromatic_json  TEXT,
                resolution_w    INTEGER DEFAULT 512,
                resolution_h    INTEGER DEFAULT 512,
                sig_file        TEXT,
                created_at      REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tag_index (
                tag         TEXT NOT NULL,
                object_id   TEXT NOT NULL,
                weight      REAL NOT NULL DEFAULT 1.0,
                PRIMARY KEY (tag, object_id),
                FOREIGN KEY (object_id) REFERENCES harmonic_objects(object_id)
            );

            CREATE TABLE IF NOT EXISTS compositions (
                comp_id         TEXT PRIMARY KEY,
                element_ids     TEXT NOT NULL,
                phi_layout_json TEXT,
                coherence_score REAL DEFAULT 0.0,
                created_at      REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS db_metadata (
                key     TEXT PRIMARY KEY,
                value   TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_tag ON tag_index(tag);
            CREATE INDEX IF NOT EXISTS idx_quality ON harmonic_objects(quality_score);
            CREATE INDEX IF NOT EXISTS idx_source ON harmonic_objects(source_type);
        """)
        conn.commit()

        # Metadata initiale
        self._set_meta("version", "1.0.0")
        self._set_meta("created_at", str(time.time()))

    def _set_meta(self, key: str, value: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO db_metadata(key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()

    def _get_meta(self, key: str) -> Optional[str]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT value FROM db_metadata WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def _load_tag_index(self):
        """Charge l'index inversé en memoire depuis SQLite."""
        conn = self._get_conn()
        rows = conn.execute("SELECT tag, object_id, weight FROM tag_index").fetchall()
        self._tag_index = {}
        for row in rows:
            tag = row["tag"]
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            self._tag_index[tag].append(row["object_id"])
        logger.debug(f"Index inversé charge: {len(self._tag_index)} tags uniques")

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest(
        self,
        signature: np.ndarray,
        tags: List[str],
        source_type: str = "sdxl_image",
        chromatic_profile: Optional[Dict] = None,
        quality_score: float = 0.75,
        harmony_score: float = 0.75,
        resolution: Tuple[int, int] = (512, 512),
        texture_dct: Optional[np.ndarray] = None,
        spatial_phi_grid: Optional[np.ndarray] = None,
    ) -> Optional[str]:
        """
        Ingere un objet visuel dans la BDD.
        
        Args:
            signature: vecteur harmonique 512D float32
            tags: liste de tags semantiques (ex: ["sunset", "ocean", "warm"])
            source_type: "sdxl_image" | "sdxl_video" | "real"
            chromatic_profile: profil chromatique dict
            quality_score: score qualite [0-1]
            harmony_score: score harmonie [0-1]
            resolution: (width, height)
            
        Returns:
            object_id si accepte, None si rejete (qualite insuffisante)
        """
        # Validation qualite
        if quality_score < QUALITY_THRESHOLDS["overall_quality_min"]:
            logger.debug(f"Objet rejete (qualite {quality_score:.2f} < {QUALITY_THRESHOLDS['overall_quality_min']})")
            return None

        # Validation signature
        if signature is None or len(signature) != SIGNATURE_DIM:
            logger.warning(f"Signature invalide: dim={len(signature) if signature is not None else 'None'}")
            return None

        # Normalisation de la signature
        sig_norm = signature.astype(np.float32)
        norm = np.linalg.norm(sig_norm)
        if norm > 1e-8:
            sig_norm = sig_norm / norm

        # Generation de l'ID (deterministique sur la signature)
        object_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, sig_norm.tobytes().hex()[:32]))

        # Verification doublon
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT object_id FROM harmonic_objects WHERE object_id=?", (object_id,)
        ).fetchone()
        if existing:
            logger.debug(f"Objet deja present: {object_id[:8]}...")
            return object_id

        # Sauvegarde du vecteur signature
        sig_file = str(self.db_dir / "signatures" / f"{object_id}.npy")
        np.save(sig_file, sig_norm)

        # Sauvegarde des donnees complementaires si presentes
        if texture_dct is not None:
            np.save(sig_file.replace(".npy", "_dct.npy"), texture_dct.astype(np.float32))
        if spatial_phi_grid is not None:
            np.save(sig_file.replace(".npy", "_phi.npy"), spatial_phi_grid.astype(np.float32))

        # Normalisation et deduplication des tags
        clean_tags = list(set(t.lower().strip().replace(" ", "_") for t in tags if t.strip()))

        # Insertion en base
        chromatic_json = json.dumps(chromatic_profile) if chromatic_profile else "{}"
        conn.execute(
            """INSERT INTO harmonic_objects
               (object_id, prompt_tags, source_type, quality_score, harmony_score,
                chromatic_json, resolution_w, resolution_h, sig_file, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (object_id, json.dumps(clean_tags), source_type, quality_score,
             harmony_score, chromatic_json, resolution[0], resolution[1],
             sig_file, time.time())
        )

        # Mise a jour de l'index inversé
        for tag in clean_tags:
            conn.execute(
                "INSERT OR IGNORE INTO tag_index(tag, object_id, weight) VALUES (?, ?, ?)",
                (tag, object_id, 1.0)
            )
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if object_id not in self._tag_index[tag]:
                self._tag_index[tag].append(object_id)

        conn.commit()
        self._set_meta("last_update", str(time.time()))
        logger.info(f"Objet ingere: {object_id[:8]}... | tags={clean_tags[:3]} | q={quality_score:.2f}")
        return object_id

    # ------------------------------------------------------------------
    # Lookup et recherche
    # ------------------------------------------------------------------

    def lookup(
        self,
        tokens: List[str],
        top_k: int = 5,
        min_quality: float = 0.65,
    ) -> List[Dict[str, Any]]:
        """
        Recherche les objets correspondant aux tokens semantiques.
        
        Args:
            tokens: liste de tokens semantiques
            top_k: nombre maximum de resultats
            min_quality: qualite minimum des resultats
            
        Returns:
            Liste de dicts {object_id, signature, tags, score, chromatic_profile}
        """
        # Score de correspondance par objet (nombre de tags matches)
        scores: Dict[str, float] = {}
        for token in tokens:
            token_normalized = token.lower().strip().replace(" ", "_")
            # Recherche exacte
            for obj_id in self._tag_index.get(token_normalized, []):
                scores[obj_id] = scores.get(obj_id, 0.0) + 1.0
            # Recherche partielle (sous-chaine)
            for tag, obj_ids in self._tag_index.items():
                if token_normalized in tag or tag in token_normalized:
                    for obj_id in obj_ids:
                        scores[obj_id] = scores.get(obj_id, 0.0) + 0.5

        if not scores:
            logger.debug(f"Aucun resultat pour tokens={tokens}")
            return []

        # Tri par score decroissant, top_k
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k * 2]

        # Recuperation des donnees
        results = []
        conn = self._get_conn()
        for obj_id, match_score in sorted_ids:
            row = conn.execute(
                "SELECT * FROM harmonic_objects WHERE object_id=? AND quality_score>=?",
                (obj_id, min_quality)
            ).fetchone()
            if row is None:
                continue

            # Chargement de la signature
            sig = self._load_signature(row["sig_file"])
            if sig is None:
                continue

            results.append({
                "object_id": obj_id,
                "signature": sig,
                "tags": json.loads(row["prompt_tags"]),
                "match_score": match_score,
                "quality_score": row["quality_score"],
                "harmony_score": row["harmony_score"],
                "chromatic_profile": json.loads(row["chromatic_json"] or "{}"),
                "source_type": row["source_type"],
                "resolution": (row["resolution_w"], row["resolution_h"]),
            })

            if len(results) >= top_k:
                break

        logger.debug(f"Lookup {tokens}: {len(results)} resultats")
        return results

    def lookup_with_confidence(
        self,
        tokens: List[str],
        top_k: int = 3,
    ) -> Tuple[float, List[Dict]]:
        """
        Recherche avec score de confiance.
        
        Returns:
            (confidence [0-1], results)
        """
        results = self.lookup(tokens, top_k=top_k)

        if not results:
            return 0.0, []

        # Confiance = max match_score normalise * qualite moyenne
        max_possible = float(len(tokens))
        if max_possible == 0:
            return 0.0, []

        avg_match = np.mean([r["match_score"] for r in results])
        avg_quality = np.mean([r["quality_score"] for r in results])
        confidence = min(1.0, (avg_match / max_possible) * avg_quality)

        return float(confidence), results

    def get_by_id(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Recupere un objet par son ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM harmonic_objects WHERE object_id=?", (object_id,)
        ).fetchone()
        if row is None:
            return None
        sig = self._load_signature(row["sig_file"])
        return {
            "object_id": object_id,
            "signature": sig,
            "tags": json.loads(row["prompt_tags"]),
            "quality_score": row["quality_score"],
            "harmony_score": row["harmony_score"],
            "chromatic_profile": json.loads(row["chromatic_json"] or "{}"),
            "source_type": row["source_type"],
            "resolution": (row["resolution_w"], row["resolution_h"]),
            "created_at": row["created_at"],
        }

    def _load_signature(self, sig_file: str) -> Optional[np.ndarray]:
        """Charge un vecteur signature depuis le disque."""
        try:
            if sig_file and os.path.exists(sig_file):
                return np.load(sig_file)
        except Exception as e:
            logger.warning(f"Erreur chargement signature {sig_file}: {e}")
        return None

    # ------------------------------------------------------------------
    # Composition phi
    # ------------------------------------------------------------------

    def phi_compose(self, signatures: List[np.ndarray]) -> np.ndarray:
        """
        Compose plusieurs signatures en une seule par ponderation phi.
        
        La ponderation donne plus de poids aux premieres signatures (contexte principal)
        selon la serie harmonique : w_i = 1/(i+1)^PHI
        
        Args:
            signatures: liste de vecteurs 512D
            
        Returns:
            signature composee 512D normalisee
        """
        if not signatures:
            return np.zeros(SIGNATURE_DIM, dtype=np.float32)

        if len(signatures) == 1:
            return signatures[0].copy()

        # Poids harmoniques
        weights = np.array([1.0 / ((i + 1) ** PHI) for i in range(len(signatures))],
                           dtype=np.float32)
        weights /= weights.sum()

        # Composition ponderee
        composed = np.zeros(SIGNATURE_DIM, dtype=np.float32)
        for w, sig in zip(weights, signatures):
            composed += w * sig

        # Renormalisation
        norm = np.linalg.norm(composed)
        if norm > 1e-8:
            composed /= norm

        return composed

    # ------------------------------------------------------------------
    # Statistiques et supervision
    # ------------------------------------------------------------------

    def get_stats(self) -> HarmonicDBStats:
        """Retourne les statistiques courantes de la BDD."""
        conn = self._get_conn()

        total = conn.execute("SELECT COUNT(*) FROM harmonic_objects").fetchone()[0]
        sdxl = conn.execute(
            "SELECT COUNT(*) FROM harmonic_objects WHERE source_type LIKE 'sdxl%'"
        ).fetchone()[0]
        real = conn.execute(
            "SELECT COUNT(*) FROM harmonic_objects WHERE source_type='real'"
        ).fetchone()[0]
        avg_q_row = conn.execute("SELECT AVG(quality_score) FROM harmonic_objects").fetchone()[0]
        avg_q = float(avg_q_row) if avg_q_row else 0.0
        unique_tags = len(self._tag_index)

        # Taille disque
        try:
            db_size = os.path.getsize(str(self.db_path)) / (1024 * 1024)
        except Exception:
            db_size = 0.0

        # Score de couverture : ratio tags couverts vs categories cible (500)
        coverage = min(1.0, unique_tags / 500.0)

        last_up_str = self._get_meta("last_update") or "0"
        try:
            last_up = float(last_up_str)
        except ValueError:
            last_up = 0.0

        return HarmonicDBStats(
            total_objects=total,
            sdxl_generated=sdxl,
            real_ingested=real,
            avg_quality_score=avg_q,
            coverage_score=coverage,
            unique_tags=unique_tags,
            db_size_mb=db_size,
            last_update=last_up,
        )

    def get_coverage_by_category(self) -> Dict[str, int]:
        """Retourne le nombre d'objets par categorie (tag)."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT tag, COUNT(*) as cnt FROM tag_index GROUP BY tag ORDER BY cnt DESC"
        ).fetchall()
        return {row["tag"]: row["cnt"] for row in rows}

    def get_autonomy_score(self) -> float:
        """
        Score d'autonomie du systeme Harmonic AI [0-1].
        Score > 0.85 = generation harmonique possible sans SDXL.
        """
        stats = self.get_stats()
        # Combinaison : couverture x qualite x volume
        volume_score = min(1.0, stats.total_objects / 12500.0)
        return float(stats.coverage_score * 0.4 + stats.avg_quality_score * 0.3 + volume_score * 0.3)

    def print_status(self):
        """Affiche un resume de l'etat de la BDD."""
        stats = self.get_stats()
        autonomy = self.get_autonomy_score()
        phase = (
            "AUTONOMIE COMPLETE" if autonomy > 0.85 else
            "HYBRIDE AVANCE" if autonomy > 0.60 else
            "HYBRIDE" if autonomy > 0.30 else
            "AMORÇAGE (SDXL requis)"
        )
        print("\n=== HarmonicDatabase Status ===")
        print(f"  Objets total   : {stats.total_objects:,}")
        print(f"  SDXL generes   : {stats.sdxl_generated:,}")
        print(f"  Tags uniques   : {stats.unique_tags:,}")
        print(f"  Qualite moy.   : {stats.avg_quality_score:.3f}")
        print(f"  Couverture     : {stats.coverage_score*100:.1f}%")
        print(f"  Score autonomie: {autonomy*100:.1f}%")
        print(f"  Phase actuelle : {phase}")
        print(f"  Taille DB      : {stats.db_size_mb:.2f} MB")
        print("================================\n")

    def close(self):
        """Ferme la connexion."""
        if self._conn:
            self._conn.close()
            self._conn = None


# ---------------------------------------------------------------------------
# Test autonome
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== Test HarmonicDatabase ===")

    db = HarmonicDatabase("harmonic_db_test")

    # Ingestion de test
    for i in range(10):
        fake_sig = np.random.randn(SIGNATURE_DIM).astype(np.float32)
        tags = [f"test_tag_{i}", f"category_{i % 3}", "demo"]
        obj_id = db.ingest(
            signature=fake_sig,
            tags=tags,
            source_type="sdxl_image",
            quality_score=0.75 + i * 0.01,
            harmony_score=0.80,
        )
        print(f"  Ingere: {obj_id[:8] if obj_id else 'REJETE'}... tags={tags[:2]}")

    # Lookup
    results = db.lookup(["test_tag_3", "category_0"], top_k=3)
    print(f"\nLookup 'test_tag_3' + 'category_0': {len(results)} resultats")
    for r in results:
        print(f"  -> {r['object_id'][:8]}... score={r['match_score']:.1f} q={r['quality_score']:.2f}")

    # Confiance
    conf, res = db.lookup_with_confidence(["demo", "test_tag_1"])
    print(f"\nConfiance lookup ['demo', 'test_tag_1']: {conf:.2f}")

    # Stats
    db.print_status()

    # Composition phi
    sigs = [r["signature"] for r in results if r["signature"] is not None]
    if sigs:
        composed = db.phi_compose(sigs)
        print(f"Signature composee: dim={len(composed)}, norme={np.linalg.norm(composed):.4f}")

    db.close()
    print("\n=== Test termine avec succes ===")
