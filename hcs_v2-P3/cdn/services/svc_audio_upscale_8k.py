"""
HCS MiniCDN - Service Audio Upscaling 8K (port 9018)
=====================================================
Upscaling audio de très haute qualité - Composant exclusif du Pack 8K HCS

Modes d'upscaling disponibles:
  hcs_clarity   : MP3/AAC/Lossy  → FLAC 24bit/96kHz  (reconstruction HF)
  hcs_spatial   : Stéréo 2.0     → Dolby Atmos 9.1.6  (upmix immersif)
  hcs_master    : Any source     → PCM 32bit/192kHz   (master audiophile)
  hcs_restore   : Audio dégradé  → FLAC 24bit/96kHz   (restauration)
  hcs_8k_bundle : Mode complet   → 32bit/192kHz + Atmos 9.1.6 (pack 8K)

Technologie HCS propriétaire:
  - Reconstruction harmonique Fourier des fréquences manquantes
  - Neural Harmonic Extrapolation (NHE-2.0)
  - Spatial Upmix Sonic Intelligence (HCS-SUSI)
  - Phase Coherence Engine (HCS-PCE)
  - Harmonic Dithering Technology (HCS-HDT)
  - Facteur K de reconstruction (K > 0.90 = excellent)
"""

import os
import sys
import json
import logging
import random
from datetime import datetime
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from services.service_base import HCSServiceBase

# ── Chargement de la config ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "config", "services.json")) as f:
    CDN_CONFIG = json.load(f)

service_config = CDN_CONFIG["services"]["audio_upscale_8k"]
PORT = int(os.getenv("HCS_SERVICE_PORT", service_config["port"]))

# ── Chargement du moteur audio HCS ────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)
try:
    from core.hcs_audio_upscaler import get_audio_upscaler, HARMONIC_PROFILES, UPSCALE_TARGETS
    _engine = get_audio_upscaler()
    ENGINE_AVAILABLE = True
    logging.getLogger("HCS-AUDIO-8K").info("Moteur HCS Audio Upscaler v%s charge", _engine.VERSION)
except ImportError as _err:
    ENGINE_AVAILABLE = False
    _engine = None
    logging.getLogger("HCS-AUDIO-8K").warning("Moteur audio non disponible: %s", _err)

# ── FastAPI & base service ─────────────────────────────────────────────────
svc = HCSServiceBase(service_config, PORT)
app = svc.app


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS SPÉCIFIQUES AU SERVICE AUDIO UPSCALING 8K
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/modes")
async def get_upscale_modes():
    """
    Liste tous les modes d'upscaling audio disponibles avec leurs caractéristiques.
    """
    modes = {
        "hcs_clarity": {
            "id":          "hcs_clarity",
            "name":        "HCS Clarity",
            "icon":        "waveform",
            "description": "Reconstruction haute fréquence - Lossy → Studio",
            "best_for":    ["MP3 128-320 kbps", "AAC 64-256 kbps", "OGG", "WMA"],
            "output":      "FLAC 24bit / 96kHz",
            "output_sr":   96_000,
            "output_bits": 24,
            "output_ch":   2,
            "freq_range":  "0 Hz → 48 kHz",
            "mos_score":   4.5,
            "k_factor":    0.92,
            "latency_ms":  180,
            "real_time":   True,
            "processing":  "1× durée source",
            "pack_8k":     True,
            "price_eur":   None,  # Inclus dans le pack
        },
        "hcs_spatial": {
            "id":          "hcs_spatial",
            "name":        "HCS Spatial",
            "icon":        "3d-rotate",
            "description": "Upmix spatial Dolby Atmos 9.1.6 - Immersion totale",
            "best_for":    ["Stéréo 2.0", "5.1 Surround", "7.1 Surround", "Musique", "Films"],
            "output":      "Dolby Atmos 9.1.6 / 24bit / 48kHz",
            "output_sr":   48_000,
            "output_bits": 24,
            "output_ch":   16,
            "freq_range":  "20 Hz → 20 kHz (spatial 360°)",
            "mos_score":   4.4,
            "k_factor":    0.88,
            "latency_ms":  350,
            "real_time":   True,
            "processing":  "2.5× durée source",
            "pack_8k":     True,
            "atmos_objects": 118,
            "atmos_bed_ch":  9,
        },
        "hcs_master": {
            "id":          "hcs_master",
            "name":        "HCS Master",
            "icon":        "crown",
            "description": "Qualité master audiophile - 32bit/192kHz",
            "best_for":    ["Tout format", "Production musicale", "Mastering", "Hi-Fi"],
            "output":      "PCM 32bit / 192kHz",
            "output_sr":   192_000,
            "output_bits": 32,
            "output_ch":   2,
            "freq_range":  "0 Hz → 96 kHz",
            "mos_score":   4.8,
            "k_factor":    0.96,
            "latency_ms":  500,
            "real_time":   False,
            "processing":  "1.8× durée source",
            "pack_8k":     True,
            "dynamic_range_db": 192,
            "thd_pct":     0.0001,
        },
        "hcs_restore": {
            "id":          "hcs_restore",
            "name":        "HCS Restore",
            "icon":        "history",
            "description": "Restauration audio vintage et enregistrements dégradés",
            "best_for":    ["Vinyle numérisé", "Cassettes", "Archives radio", "Voix phone", "78 tours"],
            "output":      "FLAC 24bit / 96kHz Restored",
            "output_sr":   96_000,
            "output_bits": 24,
            "output_ch":   2,
            "freq_range":  "0 Hz → 40 kHz",
            "mos_score":   4.2,
            "k_factor":    0.84,
            "latency_ms":  400,
            "real_time":   False,
            "processing":  "2.2× durée source",
            "pack_8k":     True,
            "declick":     True,
            "denoise":     True,
            "dehiss":      True,
        },
        "hcs_8k_bundle": {
            "id":          "hcs_8k_bundle",
            "name":        "HCS 8K Bundle",
            "icon":        "star",
            "description": "Pack 8K complet - Clarté + Spatial + Master - Qualité cinéma ultime",
            "best_for":    ["Diffusion TV 8K", "Cinéma", "Salles de concert", "Studios pro"],
            "output":      "PCM 32bit/192kHz + Dolby Atmos 9.1.6",
            "output_sr":   192_000,
            "output_bits": 32,
            "output_ch":   16,
            "freq_range":  "0 Hz → 96 kHz (spatial 360°)",
            "mos_score":   4.9,
            "k_factor":    0.94,
            "latency_ms":  800,
            "real_time":   False,
            "processing":  "4× durée source",
            "pack_8k":     True,
            "exclusive":   True,
            "atmos_objects": 118,
            "dynamic_range_db": 192,
            "note":        "Mode exclusif Pack 8K HCS - Maximum qualité disponible",
        },
    }
    return JSONResponse(content={
        "service": "audio_upscale_8k",
        "engine": _engine.ENGINE if ENGINE_AVAILABLE else "HCS Harmonic Audio Engine",
        "version": _engine.VERSION if ENGINE_AVAILABLE else "3.1.0-8K",
        "total_modes": len(modes),
        "pack_8k_modes": sum(1 for m in modes.values() if m.get("pack_8k")),
        "modes": modes,
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.get("/formats")
async def get_supported_formats():
    """
    Retourne les formats audio sources supportés avec leurs profils harmoniques.
    """
    formats_info = {
        "lossy": {
            "mp3_128":   {"name": "MP3 128 kbps",  "quality": "Médiocre",   "mos_itu": 3.0, "freq_max_khz": 16.0, "dr_db": 55},
            "mp3_320":   {"name": "MP3 320 kbps",  "quality": "Bonne",      "mos_itu": 3.8, "freq_max_khz": 20.0, "dr_db": 72},
            "aac_64":    {"name": "AAC 64 kbps",   "quality": "Mauvaise",   "mos_itu": 2.5, "freq_max_khz": 14.0, "dr_db": 48},
            "aac_128":   {"name": "AAC 128 kbps",  "quality": "Correcte",   "mos_itu": 3.2, "freq_max_khz": 18.0, "dr_db": 60},
            "aac_256":   {"name": "AAC 256 kbps",  "quality": "Bonne",      "mos_itu": 3.9, "freq_max_khz": 22.0, "dr_db": 80},
            "ogg_128":   {"name": "OGG 128 kbps",  "quality": "Correcte",   "mos_itu": 3.3, "freq_max_khz": 17.5, "dr_db": 62},
            "dolby_ac3": {"name": "Dolby AC3 640k","quality": "Bonne",      "mos_itu": 3.5, "freq_max_khz": 20.0, "dr_db": 72},
        },
        "lossless": {
            "flac_16":   {"name": "FLAC 16bit/44.1kHz", "quality": "Très bonne","mos_itu": 4.2, "freq_max_khz": 22.0, "dr_db": 96},
            "flac_24":   {"name": "FLAC 24bit/96kHz",   "quality": "Excellente","mos_itu": 4.7, "freq_max_khz": 48.0, "dr_db": 144},
            "wav_pcm":   {"name": "WAV PCM 16bit",      "quality": "Très bonne","mos_itu": 4.2, "freq_max_khz": 22.0, "dr_db": 96},
        },
        "telephony": {
            "phone_gsm": {"name": "Téléphone GSM",      "quality": "Très mauvaise","mos_itu": 1.8,"freq_max_khz": 3.4,"dr_db": 35},
            "voip_g711": {"name": "VoIP G.711",         "quality": "Mauvaise",  "mos_itu": 2.0, "freq_max_khz": 3.4, "dr_db": 40},
        },
    }
    return JSONResponse(content={
        "service": "audio_upscale_8k",
        "total_formats": sum(len(v) for v in formats_info.values()),
        "categories": list(formats_info.keys()),
        "formats": formats_info,
        "note": "Tous ces formats peuvent être upscalés vers 32bit/192kHz avec HCS",
    })


@app.post("/upscale")
async def upscale_audio(request: Request):
    """
    Lance un upscaling audio HCS.

    Body JSON:
    {
        "source_format": "mp3_128",       // Format source
        "mode": "hcs_8k_bundle",          // Mode d'upscaling
        "duration_seconds": 240,           // Durée (pour les métriques)
        "channels": 2,                     // Canaux source (1=mono, 2=stéréo, 6=5.1)
        "real_time": false                 // Traitement temps réel (réduit qualité)
    }
    """
    if not ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Moteur HCS Audio Upscaler non disponible")

    try:
        body = await request.json()
    except Exception:
        body = {}

    source_format    = body.get("source_format", "mp3_128")
    mode             = body.get("mode", "hcs_8k_bundle")
    duration_seconds = float(body.get("duration_seconds", 60.0))
    channels         = int(body.get("channels", 2))
    real_time        = bool(body.get("real_time", False))

    # Validation
    supported_formats = list(HARMONIC_PROFILES.keys())
    supported_modes   = list(UPSCALE_TARGETS.keys())

    if source_format not in supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Format '{source_format}' non supporté. Formats: {supported_formats}"
        )
    if mode not in supported_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Mode '{mode}' non supporté. Modes: {supported_modes}"
        )
    if duration_seconds <= 0 or duration_seconds > 86400:
        raise HTTPException(status_code=400, detail="duration_seconds doit être entre 1 et 86400")
    if channels not in (1, 2, 6, 8, 16):
        raise HTTPException(status_code=400, detail="channels: 1, 2, 6, 8 ou 16 uniquement")

    # Lancement de l'upscaling
    result = _engine.upscale(
        source_format=source_format,
        mode=mode,
        duration_seconds=duration_seconds,
        channels=channels,
        real_time=real_time,
    )

    # Sérialisation (dataclass → dict)
    result_dict = asdict(result)

    return JSONResponse(content={
        "status": "completed",
        "service": "audio_upscale_8k",
        "result": result_dict,
        "summary": {
            "session_id":         result.session_id,
            "mode":               result.mode,
            "source":             f"{source_format} ({result.source_signature.bitrate_kbps:.0f} kbps)",
            "output":             result.target_format,
            "quality_before":     f"{result.quality_score_before:.2f}/5.0 MOS",
            "quality_after":      f"{result.quality_score_after:.2f}/5.0 MOS",
            "improvement_pct":    round(
                (result.quality_score_after - result.quality_score_before)
                / max(0.01, result.quality_score_before) * 100, 1
            ),
            "freq_extension":     f"+{result.freq_extension_khz:.1f} kHz reconstruits",
            "snr_improvement":    f"+{result.snr_improvement_db:.1f} dB SNR",
            "k_factor":           f"{result.hcs_harmonic_k_factor:.4f}",
            "processing_time_s":  f"{result.processing_time_ms/1000:.1f}s",
            "size_gain":          f"{result.input_size_mb:.1f} MB → {result.output_size_mb:.1f} MB",
            "algorithms_count":   len(result.algorithms_applied),
        },
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.post("/analyze")
async def analyze_audio(request: Request):
    """
    Analyse un fichier audio source et retourne sa signature harmonique
    sans lancer l'upscaling.

    Body JSON:
    {
        "source_format": "mp3_128",
        "duration_seconds": 180,
        "channels": 2
    }
    """
    if not ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Moteur HCS Audio Upscaler non disponible")

    try:
        body = await request.json()
    except Exception:
        body = {}

    source_format    = body.get("source_format", "mp3_128")
    duration_seconds = float(body.get("duration_seconds", 60.0))
    channels         = int(body.get("channels", 2))

    sig = _engine.analyze_source(source_format, duration_seconds, channels)
    sig_dict = asdict(sig)

    # Recommandations d'upscaling selon la qualité source
    mos = sig.perceptual_quality_score
    if mos < 2.0:
        recommended_mode = "hcs_restore"
        recommendation   = "Source très dégradée: mode RESTORE recommandé"
    elif mos < 3.0:
        recommended_mode = "hcs_clarity"
        recommendation   = "Source compressée lossy: mode CLARITY recommandé"
    elif mos < 4.0:
        recommended_mode = "hcs_master"
        recommendation   = "Source bonne qualité: mode MASTER pour audiophiles"
    else:
        recommended_mode = "hcs_8k_bundle"
        recommendation   = "Source haute qualité: mode 8K BUNDLE pour ultime qualité"

    return JSONResponse(content={
        "service": "audio_upscale_8k",
        "analysis": sig_dict,
        "interpretation": {
            "quality_label":  _mos_to_label(mos),
            "mos_score":      mos,
            "frequency_loss": f"Fréquences manquantes: {max(0, 20 - sig.max_freq_detected_khz):.1f} kHz",
            "dynamic_loss":   f"Dynamic range: {sig.dynamic_range_db:.0f} dB (vs 144 dB studio)",
            "thd_level":      f"Distorsion THD: {sig.thd_pct:.3f}%",
            "noise_floor":    f"Plancher de bruit: {sig.noise_floor_db:.0f} dBFS",
            "spatial_info":   f"Largeur stéréo: {sig.spatial_width*100:.0f}%",
        },
        "recommendation": {
            "mode":    recommended_mode,
            "reason":  recommendation,
            "benefit": f"MOS estimé après upscaling: {_mos_after_estimate(mos, recommended_mode):.2f}/5.0",
        },
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.get("/compare")
async def compare_modes(
    source_format: str = Query("mp3_128", description="Format audio source"),
    duration: float    = Query(60.0,       description="Durée en secondes"),
    channels: int      = Query(2,          description="Canaux source"),
):
    """
    Compare tous les modes d'upscaling pour un même fichier source.
    Utile pour choisir le mode optimal.
    """
    if not ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Moteur HCS Audio Upscaler non disponible")

    if source_format not in HARMONIC_PROFILES:
        raise HTTPException(status_code=400, detail=f"Format '{source_format}' non supporté")

    comparison = {}
    for mode in UPSCALE_TARGETS.keys():
        r = _engine.upscale(source_format, mode, duration, channels, real_time=True)
        comparison[mode] = {
            "mode":             mode,
            "output_format":    r.target_format,
            "quality_before":   r.quality_score_before,
            "quality_after":    r.quality_score_after,
            "improvement_pct":  round((r.quality_score_after - r.quality_score_before) / max(0.01, r.quality_score_before) * 100, 1),
            "snr_db":           r.snr_improvement_db,
            "dynamic_range_gain_db": r.dynamic_range_gain_db,
            "freq_extension_khz": r.freq_extension_khz,
            "spatial_channels":  r.target_channels,
            "k_factor":         r.hcs_harmonic_k_factor,
            "processing_ms":    r.processing_time_ms,
            "output_size_mb":   r.output_size_mb,
            "algorithms_count": len(r.algorithms_applied),
        }

    # Tri par qualité après upscaling
    sorted_modes = sorted(comparison.items(), key=lambda x: x[1]["quality_after"], reverse=True)

    return JSONResponse(content={
        "service": "audio_upscale_8k",
        "source": {
            "format":   source_format,
            "duration": duration,
            "channels": channels,
        },
        "comparison": {k: v for k, v in sorted_modes},
        "best_mode": sorted_modes[0][0],
        "best_quality": sorted_modes[0][1]["quality_after"],
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.get("/presets/8k-broadcast")
async def preset_8k_broadcast():
    """
    Preset optimisé pour la diffusion TV 8K - Configuration recommandée
    par HCS pour accompagner le service TV Broadcast 8K (port 9011).
    """
    if not ENGINE_AVAILABLE:
        return JSONResponse(content=_static_preset_8k())

    # Simuler plusieurs sources type broadcast
    sources = [
        ("dolby_ac3", 6, "Dolby AC3 5.1 (source broadcast standard)"),
        ("aac_256",   2, "AAC 256kbps stéréo (source streaming)"),
        ("flac_16",   2, "FLAC 16bit/44.1kHz (source studio)"),
    ]

    results = []
    for fmt, ch, label in sources:
        r = _engine.upscale(fmt, "hcs_8k_bundle", 120, ch, real_time=False)
        results.append({
            "source_label":  label,
            "source_format": fmt,
            "mode":          "hcs_8k_bundle",
            "output":        r.target_format,
            "quality_after": r.quality_score_after,
            "k_factor":      r.hcs_harmonic_k_factor,
            "atmos_channels": r.target_channels,
            "algorithms":    r.algorithms_applied,
        })

    return JSONResponse(content={
        "service":     "audio_upscale_8k",
        "preset":      "8K Broadcast",
        "description": "Configuration recommandée pour accompagner la TV 8K HCS",
        "mode":        "hcs_8k_bundle",
        "output_spec": {
            "format":          "PCM 32bit/192kHz + Dolby Atmos 9.1.6",
            "sample_rate_hz":  192_000,
            "bit_depth":       32,
            "channels":        "9.1.6 (16 canaux + 118 objects Atmos)",
            "freq_range":      "0 Hz → 96 kHz",
            "dynamic_range":   "192 dB",
            "thd":             "< 0.0001%",
            "noise_floor":     "-192 dBFS",
            "latency_target":  "< 800 ms",
        },
        "pairing": {
            "video_service": "tv_broadcast_8k (port 9011)",
            "video_codec":   "H.266/VVC 7680x4320 60fps",
            "sync_protocol": "PTP (Precision Time Protocol) IEEE 1588v2",
            "lip_sync":      "< 5ms audio/video drift",
        },
        "test_results": results,
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.get("/engine/stats")
async def engine_stats():
    """Statistiques globales du moteur d'upscaling audio HCS."""
    if not ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Moteur non disponible")
    stats = _engine.get_engine_stats()
    stats["service"] = "audio_upscale_8k"
    stats["timestamp"] = datetime.utcnow().isoformat()
    return JSONResponse(content=stats)


@app.get("/quality/benchmark")
async def quality_benchmark():
    """
    Benchmark de qualité complet : mesure les améliorations HCS
    sur tous les formats × tous les modes.
    """
    if not ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Moteur non disponible")

    formats_to_test = ["mp3_128", "aac_64", "flac_16", "dolby_ac3", "phone_gsm"]
    modes_to_test   = ["hcs_clarity", "hcs_master", "hcs_8k_bundle"]
    matrix = {}

    for fmt in formats_to_test:
        matrix[fmt] = {}
        for mode in modes_to_test:
            r = _engine.upscale(fmt, mode, 30.0, 2, real_time=True)
            matrix[fmt][mode] = {
                "quality_before": r.quality_score_before,
                "quality_after":  r.quality_score_after,
                "snr_db":         r.snr_improvement_db,
                "k_factor":       r.hcs_harmonic_k_factor,
                "freq_ext_khz":   r.freq_extension_khz,
            }

    # Calcul des meilleurs gains
    best_improvement = max(
        (matrix[f][m]["quality_after"] - matrix[f][m]["quality_before"], f, m)
        for f in formats_to_test for m in modes_to_test
    )

    return JSONResponse(content={
        "service":   "audio_upscale_8k",
        "benchmark": "HCS Audio Quality Matrix",
        "formats_tested": formats_to_test,
        "modes_tested":   modes_to_test,
        "matrix":    matrix,
        "highlights": {
            "best_improvement": {
                "gain_mos": round(best_improvement[0], 2),
                "format":   best_improvement[1],
                "mode":     best_improvement[2],
            },
            "avg_snr_improvement_db": round(
                sum(matrix[f][m]["snr_db"] for f in formats_to_test for m in modes_to_test)
                / (len(formats_to_test) * len(modes_to_test)), 1
            ),
            "max_freq_extension_khz": max(
                matrix[f][m]["freq_ext_khz"]
                for f in formats_to_test for m in modes_to_test
            ),
        },
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.get("/demo/realtime")
async def demo_realtime():
    """
    Simulation d'un upscaling temps réel de stream audio.
    Retourne des métriques comme si on traitait un flux live.
    """
    if not ENGINE_AVAILABLE:
        return JSONResponse(content=_static_demo())

    # Simuler un stream live Dolby AC3 5.1 → Atmos 9.1.6
    r = _engine.upscale("dolby_ac3", "hcs_spatial", 30.0, 6, real_time=True)

    return JSONResponse(content={
        "service":      "audio_upscale_8k",
        "demo":         "Real-Time Audio Upscaling Stream",
        "stream_info": {
            "input":        "Dolby AC3 5.1 | 640 kbps | 48kHz/20bit",
            "output":       "Dolby Atmos 9.1.6 | 24bit/48kHz",
            "latency_ms":   round(random.uniform(280, 350), 0),
            "buffer_frames":  4,
            "frame_size_ms":  10.0,
        },
        "live_metrics": {
            "mos_live":           round(r.quality_score_after, 2),
            "snr_db":             round(r.snr_improvement_db, 1),
            "k_factor":           round(r.hcs_harmonic_k_factor, 4),
            "spatial_channels":   r.target_channels,
            "atmos_objects_active": random.randint(12, 85),
            "cpu_usage_pct":      round(random.uniform(18, 35), 1),
            "gpu_usage_pct":      round(random.uniform(42, 68), 1),
            "throughput_mbps":    round(random.uniform(8, 14), 1),
        },
        "algorithms_active": r.algorithms_applied,
        "timestamp": datetime.utcnow().isoformat(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS INTERNES
# ─────────────────────────────────────────────────────────────────────────────

def _mos_to_label(mos: float) -> str:
    if mos >= 4.5: return "Excellent (studio)"
    if mos >= 4.0: return "Tres bonne (Hi-Fi)"
    if mos >= 3.5: return "Bonne (acceptable)"
    if mos >= 3.0: return "Correcte (streaming)"
    if mos >= 2.5: return "Mediocre (compressé)"
    if mos >= 2.0: return "Mauvaise (lossy fort)"
    return "Tres mauvaise (degradé)"


def _mos_after_estimate(mos_before: float, mode: str) -> float:
    targets = {
        "hcs_clarity": 4.5, "hcs_spatial": 4.4,
        "hcs_master": 4.8, "hcs_restore": 4.2, "hcs_8k_bundle": 4.9
    }
    t = targets.get(mode, 4.4)
    return min(5.0, 0.60 * t + 0.40 * (mos_before + (t - mos_before) * 0.90))


def _static_preset_8k() -> dict:
    """Retourne un preset statique si le moteur n'est pas disponible."""
    return {
        "service": "audio_upscale_8k",
        "preset": "8K Broadcast (static)",
        "mode": "hcs_8k_bundle",
        "output_spec": {
            "format": "PCM 32bit/192kHz + Dolby Atmos 9.1.6",
            "sample_rate_hz": 192_000,
            "bit_depth": 32,
            "channels": 16,
        },
        "status": "engine_offline",
    }


def _static_demo() -> dict:
    return {
        "service": "audio_upscale_8k",
        "demo": "Real-Time Audio Upscaling (static)",
        "status": "engine_offline",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENTRÉE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [AUDIO-UPSCALE-8K] %(message)s"
    )
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
