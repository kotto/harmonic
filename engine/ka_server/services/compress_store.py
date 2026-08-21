"""
compress_store.py — Historique & statistiques de compression HCV.

Persiste les opérations de compression (Ψ Compress) dans un fichier JSON,
permet d'agréger les statistiques du dashboard : espace économisé, ratio
moyen, CO₂ évité (stockage cloud évité), nombre d'opérations.

Stockage : data/compress_history.json (léger, thread-safe via verrou).
Max 2000 entrées — les plus anciennes sont purgées.
"""

import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

_MAX_ENTRIES = 2000
_STORE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "compress_history.json"

_lock = threading.Lock()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load() -> List[Dict]:
    try:
        if _STORE_PATH.exists():
            with open(_STORE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception as e:
        log.warning(f"compress_store: lecture échouée ({e}) — démarre à zéro")
    return []


def _save(entries: List[Dict]) -> None:
    try:
        _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=1)
    except Exception as e:
        log.error(f"compress_store: écriture échouée ({e})")


def _fmt_bytes(n: int) -> str:
    """Formate une taille en octets (B / KB / MB / GB)."""
    if n < 1024:
        return f"{n} o"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} Ko"
    if n < 1024 ** 3:
        return f"{n / 1024 ** 2:.1f} Mo"
    return f"{n / 1024 ** 3:.2f} Go"


# ── API publique ─────────────────────────────────────────────────────────────

def add_entry(filename: str,
              original_size: int,
              compressed_size: int,
              quality: str = "standard",
              method: str = "auto",
              format: str = "hcv",
              duration_ms: float = 0.0,
              metadata: Optional[Dict] = None) -> Dict:
    """Enregistre une compression dans l'historique. Retourne l'entrée créée."""
    ratio = (original_size / compressed_size) if compressed_size > 0 else 1.0
    saved = max(0, original_size - compressed_size)

    entry = {
        "id": uuid.uuid4().hex[:12],
        "ts": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "filename": filename,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "ratio": round(ratio, 2),
        "saved_percent": round(100 * saved / original_size, 1) if original_size else 0.0,
        "saved_bytes": saved,
        "quality": quality,
        "method": method,
        "format": format,
        "duration_ms": round(duration_ms, 1),
        "metadata": metadata or {},
    }

    with _lock:
        entries = _load()
        entries.append(entry)
        # Purgé des plus anciennes (le file JSON reste < ~1 Mo)
        if len(entries) > _MAX_ENTRIES:
            entries = entries[-_MAX_ENTRIES:]
        _save(entries)

    return entry


def get_history(limit: int = 100) -> List[Dict]:
    """Historique des compressions, les plus récentes en premier."""
    with _lock:
        entries = _load()
    entries = list(reversed(entries))
    return entries[:limit]


def get_stats() -> Dict:
    """
    Statistiques agrégées du dashboard :
      - total_operations, total_original, total_compressed, total_saved
      - avg_ratio, best_ratio, worst_ratio
      - avg_duration_ms, co2_saved_kg, cloud_cost_saved_eur
      - formats (répartition), qualities (répartition)
      - last_24h (nombre d'opérations sur 24 h)
    """
    with _lock:
        entries = _load()

    n = len(entries)
    if n == 0:
        return {
            "total_operations": 0, "total_original": 0, "total_compressed": 0,
            "total_saved": 0, "avg_ratio": 0, "best_ratio": 0, "worst_ratio": 0,
            "avg_duration_ms": 0, "co2_saved_kg": 0, "cloud_cost_saved_eur": 0,
            "formats": {}, "qualities": {}, "last_24h": 0,
            "total_original_fmt": "0 o", "total_saved_fmt": "0 o",
        }

    total_original = sum(e.get("original_size", 0) for e in entries)
    total_compressed = sum(e.get("compressed_size", 0) for e in entries)
    total_saved = max(0, total_original - total_compressed)

    ratios = [e.get("ratio", 1) for e in entries]
    durations = [e.get("duration_ms", 0) for e in entries]

    # Répartition
    formats: Dict[str, int] = {}
    qualities: Dict[str, int] = {}
    now = time.time()
    last_24h = 0
    for e in entries:
        fmt = e.get("format", "hcv")
        formats[fmt] = formats.get(fmt, 0) + 1
        q = e.get("quality", "standard")
        qualities[q] = qualities.get(q, 0) + 1
        if now - e.get("ts", 0) <= 86400:
            last_24h += 1

    # CO₂ : 1 Go stocké ~ 0.055 kWh · 0.45 kg CO₂/kWh (moy. cloud) → ~0.025 kg/Go
    co2_kg = total_saved / (1024 ** 3) * 0.025
    # Coût cloud : ~0.023 €/Go/mois (stockage objet froid)
    cost_eur = total_saved / (1024 ** 3) * 0.023

    return {
        "total_operations": n,
        "total_original": total_original,
        "total_compressed": total_compressed,
        "total_saved": total_saved,
        "avg_ratio": round(sum(ratios) / n, 2),
        "best_ratio": round(max(ratios), 2),
        "worst_ratio": round(min(ratios), 2),
        "avg_duration_ms": round(sum(durations) / n, 1),
        "co2_saved_kg": round(co2_kg, 3),
        "cloud_cost_saved_eur": round(cost_eur, 2),
        "formats": formats,
        "qualities": qualities,
        "last_24h": last_24h,
        "total_original_fmt": _fmt_bytes(total_original),
        "total_saved_fmt": _fmt_bytes(total_saved),
        "total_compressed_fmt": _fmt_bytes(total_compressed),
    }


def reset_history() -> int:
    """Vide l'historique. Retourne le nombre d'entrées supprimées."""
    with _lock:
        entries = _load()
        count = len(entries)
        _save([])
    return count
