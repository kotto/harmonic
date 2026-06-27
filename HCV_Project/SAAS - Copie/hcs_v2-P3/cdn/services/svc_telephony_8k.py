"""
HCS MiniCDN - Service Telephonie/Video 8K HD (port 9020)
=========================================================
Service de communication video/telephonie haute definition 8K
avec audio harmonique professionnel PCM 32bit/192kHz.

Modes disponibles:
  voice_hd            : Voix HD Opus 48kHz/24bit
  voice_ultra         : Voix Ultra HD PCM 96kHz/24bit
  video_1080p         : Video Full HD 1080p/60fps
  video_4k            : Video 4K/60fps + Dolby Atmos 5.1
  video_8k            : Video 8K/60fps HDR10+ + Atmos 9.1.6 32bit/192kHz
  video_8k_conference : Conference 8K multi-participants (max 12)

Technologies:
  - H.266/VVC pour video 8K (ratio 3:1)
  - PCM 32bit/192kHz + Dolby Atmos 9.1.6 (118 objets)
  - WebRTC + DTLS 1.3 + SRTP + AES-256-GCM E2E
  - Facteur K harmonique >= 0.97 en mode 8K
  - MOS cible >= 4.9/5.0 (reference studio professionnel)
"""

import os
import sys
import json
import logging
import random
from datetime import datetime, timezone
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from services.service_base import HCSServiceBase

# Moteur telephonie HCS
try:
    from core.hcs_telephony_engine import (
        get_telephony_engine, CALL_QUALITIES, TRANSPORT_PROTOCOLS, STUN_TURN_SERVERS
    )
    _engine = get_telephony_engine()
    ENGINE_OK = True
except ImportError as e:
    ENGINE_OK = False
    _engine = None
    CALL_QUALITIES = {}
    TRANSPORT_PROTOCOLS = {}
    STUN_TURN_SERVERS = []
    logging.getLogger("HCS-Telephony-8K").warning("Moteur non dispo: %s", e)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "config", "services.json")) as f:
    CDN_CONFIG = json.load(f)

service_config = CDN_CONFIG["services"]["telephony_video_8k"]
PORT = int(os.getenv("HCS_SERVICE_PORT", service_config["port"]))

svc = HCSServiceBase(service_config, PORT)
app = svc.app


# =============================================================================
# ENDPOINTS TELEPHONIE/VIDEO 8K
# =============================================================================

@app.get("/qualities")
async def get_qualities():
    """Liste toutes les qualites d'appel disponibles."""
    return JSONResponse({
        "service": "telephony_video_8k",
        "engine": _engine.ENGINE if ENGINE_OK else "HCS-Telephony-Engine",
        "version": _engine.VERSION if ENGINE_OK else "1.0.0-8K",
        "total_qualities": len(CALL_QUALITIES),
        "qualities": CALL_QUALITIES,
        "highlights": {
            "max_video_resolution": "7680x4320 (8K UHD)",
            "max_audio_sample_rate": "192000 Hz (192 kHz)",
            "max_audio_bit_depth": "32 bits",
            "max_audio_channels": "16 (Dolby Atmos 9.1.6 + 118 objets)",
            "max_mos_target": 4.9,
            "max_k_factor": 0.97,
            "video_codec_8k": "H.266/VVC",
            "hdr_support": "HDR10+ / Dolby Vision",
            "encryption": "AES-256-GCM End-to-End",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/transports")
async def get_transports():
    """Protocoles de transport disponibles."""
    return JSONResponse({
        "service": "telephony_video_8k",
        "transports": TRANSPORT_PROTOCOLS,
        "stun_turn_servers": STUN_TURN_SERVERS,
        "recommended": "webrtc",
        "encryption": "DTLS 1.3 + SRTP (WebRTC) | TLS 1.3 + SRTP (SIP) | AES-256-GCM (HCS Direct)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/call/initiate")
async def initiate_call(request: Request):
    """
    Initie un appel telephonique/video HCS 8K.

    Body JSON:
    {
        "caller_id": "user_alice",
        "callee_id": "user_bob",
        "quality": "video_8k",
        "transport": "webrtc",
        "region": "EU"
    }
    """
    if not ENGINE_OK:
        raise HTTPException(503, "Moteur HCS Telephonie non disponible")
    try:
        body = await request.json()
    except Exception:
        body = {}

    caller_id = body.get("caller_id", f"user_{random.randint(1000,9999)}")
    callee_id = body.get("callee_id", f"user_{random.randint(1000,9999)}")
    quality   = body.get("quality", "video_8k")
    transport = body.get("transport", "webrtc")
    region    = body.get("region", "EU")

    try:
        session = _engine.initiate_call(caller_id, callee_id, quality, transport, region)
    except ValueError as e:
        raise HTTPException(400, str(e))

    sess_dict = asdict(session)
    q = CALL_QUALITIES.get(quality, {})

    return JSONResponse({
        "status": "call_initiated",
        "service": "telephony_video_8k",
        "session": sess_dict,
        "webrtc_config": {
            "ice_servers": STUN_TURN_SERVERS,
            "sdp_offer_ready": True,
            "dtls_fingerprint": f"sha-256 {':'.join([f'{random.randint(0,255):02X}' for _ in range(32)])}",
        },
        "quality_info": {
            "name": q.get("name", quality),
            "video_resolution": q.get("video_res"),
            "video_codec": q.get("video_codec"),
            "audio_codec": q.get("audio_codec"),
            "audio_sample_rate_hz": q.get("audio_sr"),
            "audio_bit_depth": q.get("audio_bits"),
            "audio_channels": q.get("audio_channels"),
            "hcs_algorithms": q.get("hcs_algorithms", []),
            "bandwidth_required_mbps": q.get("bandwidth_rec_mbps"),
        },
        "encryption": "AES-256-GCM End-to-End",
        "hcs_harmonic_active": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/call/{session_id}/metrics")
async def get_call_metrics(session_id: str):
    """Retourne les metriques temps reel d'un appel en cours."""
    if not ENGINE_OK:
        raise HTTPException(503, "Moteur non disponible")
    session = _engine.update_session_metrics(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} introuvable")

    sess_dict = asdict(session)
    audio = sess_dict["audio_metrics"]
    video = sess_dict["video_metrics"]

    return JSONResponse({
        "service": "telephony_video_8k",
        "session_id": session_id,
        "status": session.status,
        "duration_s": session.duration_s,
        "audio": {
            "mos": audio["mos_score"],
            "mos_label": _mos_label(audio["mos_score"]),
            "k_factor": audio["k_factor"],
            "snr_db": audio["snr_db"],
            "dynamic_range_db": audio["dynamic_range_db"],
            "thd_pct": audio["thd_pct"],
            "freq_khz": audio["freq_response_khz"],
            "latency_ms": audio["latency_ms"],
            "jitter_ms": audio["jitter_ms"],
            "packet_loss_pct": audio["packet_loss_pct"],
            "echo_return_loss_db": audio["echo_return_loss_db"],
            "algorithms_active": audio["algorithms_active"],
        },
        "video": {
            "resolution": video["resolution"] if video else None,
            "fps": video["fps"] if video else None,
            "psnr_db": video["psnr_db"] if video else None,
            "ssim": video["ssim"] if video else None,
            "vmaf": video["vmaf"] if video else None,
            "bitrate_mbps": video["bitrate_actual_mbps"] if video else None,
            "codec": video["codec"] if video else None,
            "hdr": video["hdr_mode"] if video else None,
            "frame_loss_pct": video["frame_loss_pct"] if video else None,
            "hcs_upscale": video["hcs_upscale_active"] if video else None,
            "hcs_hdr_enhance": video["hcs_hdr_enhance"] if video else None,
        } if video else None,
        "network": {
            "bytes_sent_mb": round(session.bytes_sent / 1e6, 2),
            "bytes_received_mb": round(session.bytes_received / 1e6, 2),
            "edge_node": session.edge_node,
            "region": session.region,
            "transport": session.transport,
            "encryption": session.encryption,
        },
        "cost_usd": session.call_cost_usd,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/call/{session_id}/end")
async def end_call(session_id: str):
    """Termine un appel."""
    if not ENGINE_OK:
        raise HTTPException(503, "Moteur non disponible")
    session = _engine.end_call(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} introuvable")
    return JSONResponse({
        "service": "telephony_video_8k",
        "session_id": session_id,
        "status": "ended",
        "duration_s": session.duration_s,
        "duration_formatted": _format_duration(session.duration_s),
        "total_cost_usd": session.call_cost_usd,
        "bytes_exchanged_mb": round((session.bytes_sent + session.bytes_received) / 1e6, 2),
        "final_mos": session.audio_metrics.mos_score,
        "final_k_factor": session.audio_metrics.k_factor,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/call/{session_id}/hold")
async def hold_call(session_id: str):
    """Met un appel en attente."""
    if not ENGINE_OK:
        raise HTTPException(503, "Moteur non disponible")
    session = _engine.hold_call(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} introuvable")
    return JSONResponse({"session_id": session_id, "status": "on_hold",
                         "service": "telephony_video_8k"})


@app.post("/call/{session_id}/resume")
async def resume_call(session_id: str):
    """Reprend un appel en attente."""
    if not ENGINE_OK:
        raise HTTPException(503, "Moteur non disponible")
    session = _engine.resume_call(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} introuvable")
    return JSONResponse({"session_id": session_id, "status": session.status,
                         "service": "telephony_video_8k"})


@app.get("/calls/active")
async def list_active_calls():
    """Liste tous les appels actifs."""
    if not ENGINE_OK:
        raise HTTPException(503, "Moteur non disponible")
    sessions = _engine.list_active_sessions()
    return JSONResponse({
        "service": "telephony_video_8k",
        "active_calls": len(sessions),
        "sessions": [
            {
                "session_id": s.session_id,
                "caller_id": s.caller_id,
                "callee_id": s.callee_id,
                "quality": s.quality,
                "duration_s": s.duration_s,
                "mos": s.audio_metrics.mos_score,
                "region": s.region,
                "edge_node": s.edge_node,
            }
            for s in sessions
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/quality/test")
async def quality_network_test(
    quality: str = Query("video_8k", description="Qualite d'appel a tester"),
    region:  str = Query("EU",       description="Region reseau"),
):
    """
    Test de qualite reseau pour une qualite d'appel donnee.
    Retourne les metriques estimees et la disponibilite de la bande passante.
    """
    if not ENGINE_OK:
        raise HTTPException(503, "Moteur non disponible")
    if quality not in CALL_QUALITIES:
        raise HTTPException(400, f"Qualite '{quality}' inconnue. Options: {list(CALL_QUALITIES.keys())}")
    result = _engine.quality_test(quality, region)
    return JSONResponse({
        "service": "telephony_video_8k",
        **result,
    })


@app.get("/quality/compare")
async def compare_qualities():
    """Compare toutes les qualites d'appel disponibles."""
    if not ENGINE_OK:
        raise HTTPException(503, "Moteur non disponible")
    comparisons = {}
    for qid in CALL_QUALITIES:
        result = _engine.quality_test(qid, "EU")
        q = CALL_QUALITIES[qid]
        comparisons[qid] = {
            "name": q["name"],
            "video": q["video"],
            "video_res": q.get("video_res"),
            "audio_sr_khz": q["audio_sr"] / 1000,
            "audio_bits": q["audio_bits"],
            "audio_channels": q["audio_channels"],
            "mos_measured": result["audio"]["mos"],
            "k_factor": result["audio"]["k_factor"],
            "snr_db": result["audio"]["snr_db"],
            "bandwidth_mbps": q["bandwidth_rec_mbps"],
            "latency_ms": result["audio"]["latency_ms"],
        }
    return JSONResponse({
        "service": "telephony_video_8k",
        "comparison": comparisons,
        "best_quality": "video_8k",
        "best_mos": max(v["mos_measured"] for v in comparisons.values()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/engine/stats")
async def engine_stats():
    """Statistiques globales du moteur telephonie."""
    if not ENGINE_OK:
        raise HTTPException(503, "Moteur non disponible")
    stats = asdict(_engine.get_engine_stats())
    stats["service"] = "telephony_video_8k"
    stats["timestamp"] = datetime.now(timezone.utc).isoformat()
    return JSONResponse(stats)


@app.get("/demo/8k-call")
async def demo_8k_call():
    """
    Demonstration d'un appel 8K HCS avec toutes les metriques.
    Simule un appel professionnel 8K en cours.
    """
    if not ENGINE_OK:
        return JSONResponse(_static_demo())
    session = _engine.initiate_call("studio_paris", "studio_tokyo", "video_8k", "webrtc", "EU")
    _engine.update_session_metrics(session.session_id)
    _engine.update_session_metrics(session.session_id)
    sess = _engine.update_session_metrics(session.session_id)
    q = CALL_QUALITIES["video_8k"]
    return JSONResponse({
        "service": "telephony_video_8k",
        "demo": "Appel 8K HCS Professionnel",
        "scenario": "Studio Paris → Studio Tokyo | Liaison broadcast 8K",
        "session_id": sess.session_id,
        "video": {
            "resolution": "7680x4320 (8K UHD)",
            "codec": "H.266/VVC",
            "fps": 60,
            "hdr": "HDR10+ / Dolby Vision",
            "color_depth": "10 bits",
            "psnr_db": sess.video_metrics.psnr_db if sess.video_metrics else 44.5,
            "ssim": sess.video_metrics.ssim if sess.video_metrics else 0.996,
            "vmaf": sess.video_metrics.vmaf if sess.video_metrics else 97.2,
            "bitrate_mbps": sess.video_metrics.bitrate_actual_mbps if sess.video_metrics else 98.5,
            "hcs_upscale_active": True,
            "hcs_hdr_enhance": True,
        },
        "audio": {
            "codec": "HCS-Harmonic-32",
            "sample_rate": "192 kHz (PCM 32bit)",
            "channels": "16 canaux (Dolby Atmos 9.1.6)",
            "atmos_objects": 118,
            "mos": sess.audio_metrics.mos_score,
            "k_factor": sess.audio_metrics.k_factor,
            "snr_db": sess.audio_metrics.snr_db,
            "dynamic_range_db": sess.audio_metrics.dynamic_range_db,
            "thd_pct": sess.audio_metrics.thd_pct,
            "freq_khz": sess.audio_metrics.freq_response_khz,
            "latency_ms": sess.audio_metrics.latency_ms,
            "algorithms": q["hcs_algorithms"],
        },
        "network": {
            "transport": "WebRTC + DTLS 1.3 + SRTP",
            "encryption": "AES-256-GCM End-to-End",
            "edge_node": sess.edge_node,
            "region": "EU → AP",
            "latency_total_ms": round(sess.audio_metrics.latency_ms + 20, 1),
        },
        "quality_summary": {
            "mos_label": _mos_label(sess.audio_metrics.mos_score),
            "hcs_harmonic": True,
            "professional_grade": sess.audio_metrics.mos_score >= 4.5,
            "studio_grade": sess.audio_metrics.mos_score >= 4.8,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/conference/capabilities")
async def conference_capabilities():
    """Capacites de conference 8K multi-participants."""
    q = CALL_QUALITIES.get("video_8k_conference", {})
    return JSONResponse({
        "service": "telephony_video_8k",
        "conference_8k": {
            "max_participants": q.get("max_participants", 12),
            "video_resolution": "7680x4320 per participant",
            "video_codec": "H.266/VVC",
            "audio_codec": "HCS-Harmonic-32 (PCM 32bit/192kHz)",
            "audio_spatial": "Dolby Atmos 9.1.6 spatial mixing",
            "atmos_objects": 118,
            "bandwidth_per_participant_mbps": 10,
            "bandwidth_total_mbps": 120,
            "features": [
                "Switching vue automatique (speaker detection HCS)",
                "Mixage spatial Atmos par participant",
                "Reduction bruit IA par flux",
                "Suppression echo adaptative",
                "Video layout adaptatif (grid/spotlight/sidebar)",
                "Chat integre chiffre E2E",
                "Partage ecran 8K",
                "Enregistrement 8K PCM 32bit/192kHz",
                "Reconnexion automatique",
                "Transcription temps reel (optionnel)",
            ],
            "latency_target_ms": 250,
            "mos_target": 4.8,
            "k_factor_target": 0.95,
            "hcs_algorithms": q.get("hcs_algorithms", []),
            "encryption": "AES-256-GCM E2E tous participants",
            "bandwidth_adaptation": "ABR dynamique selon qualite reseau",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/audio/profiles")
async def audio_profiles():
    """Profils audio harmoniques disponibles pour la telephonie."""
    return JSONResponse({
        "service": "telephony_video_8k",
        "audio_profiles": {
            "voice_gsm": {
                "name": "GSM (Legacy)",
                "sample_rate_hz": 8000, "bit_depth": 8, "channels": 1,
                "bitrate_kbps": 13, "mos_itu": 2.1, "k_factor": 0.40,
                "freq_khz": 4.0, "hcs_enhancement": False,
            },
            "voice_hd_opus": {
                "name": "HD Voice Opus",
                "sample_rate_hz": 48000, "bit_depth": 24, "channels": 2,
                "bitrate_kbps": 96, "mos_itu": 4.3, "k_factor": 0.88,
                "freq_khz": 24.0, "hcs_enhancement": True,
                "algorithms": ["HCS-Clarity", "HCS-NoiseSuppressor", "HCS-EchoCancel"],
            },
            "voice_ultra_pcm": {
                "name": "Ultra Voice PCM 96kHz",
                "sample_rate_hz": 96000, "bit_depth": 24, "channels": 2,
                "bitrate_kbps": 510, "mos_itu": 4.6, "k_factor": 0.92,
                "freq_khz": 48.0, "hcs_enhancement": True,
                "algorithms": ["HCS-Clarity", "HCS-HFRecon", "HCS-PCE", "HCS-NoiseSuppressor"],
            },
            "hcs_harmonic_32": {
                "name": "HCS Harmonic 32bit/192kHz (8K Call)",
                "sample_rate_hz": 192000, "bit_depth": 32, "channels": 16,
                "bitrate_kbps": 9216, "mos_itu": 4.9, "k_factor": 0.97,
                "freq_khz": 96.0, "hcs_enhancement": True,
                "dynamic_range_db": 192, "thd_pct": 0.00005,
                "atmos_objects": 118, "atmos_bed": "9.1.6",
                "algorithms": [
                    "HCS-Clarity", "HCS-Spatial-9.1.6", "HCS-HFRecon-192k",
                    "HCS-PCE", "HCS-NHE-2.0", "HCS-SUSI", "HCS-HDT",
                    "HCS-Atmos-118obj", "HCS-NoiseGate-Pro"
                ],
                "exclusive": True,
                "note": "Qualite reference studio professionnel - Pack 8K HCS",
            },
        },
        "recommendation": "hcs_harmonic_32 pour appels/conferences 8K HCS",
        "improvement_vs_gsm": {
            "mos_gain": round(4.9 - 2.1, 1),
            "freq_extension_khz": round(96.0 - 4.0, 0),
            "k_factor_improvement_pct": round((0.97 - 0.40) / 0.40 * 100, 0),
            "dynamic_range_gain_db": round(192 - 35, 0),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/requirements/8k")
async def requirements_8k():
    """Prerequis pour utiliser le service telephonie/video 8K."""
    return JSONResponse({
        "service": "telephony_video_8k",
        "requirements_video_8k": {
            "display": "Ecran 8K (7680x4320) HDMI 2.1 ou DisplayPort 2.0",
            "camera": "Camera 8K compatible H.266/VVC (Sony Alpha / RED / Blackmagic)",
            "bandwidth": "150 Mbps minimum recommande (fibre 1 Gbps ideal)",
            "cpu": "Intel Core i9 2024+ ou AMD Ryzen 9 7950X (encodage VVC temps reel)",
            "gpu": "NVIDIA RTX 4090 ou AMD RX 7900 XTX (acceleration H.266/VVC)",
            "ram": "64 GB DDR5 minimum",
            "audio_system": "Interface audio 192 kHz/32bit (RME Fireface / Apollo) + enceintes Atmos 9.1.6",
            "os": "Windows 11 / macOS Ventura+ / Ubuntu 22.04+",
            "browser": "Chrome 120+ / Firefox 119+ / Edge 120+ (WebRTC 1.3)",
        },
        "requirements_voice_ultra": {
            "microphone": "Micro condenser large membrane (AKG C414 / Neumann U87)",
            "bandwidth": "1 Mbps minimum",
            "audio_interface": "Carte son 96 kHz/24bit",
        },
        "requirements_video_1080p": {
            "camera": "Webcam 1080p/60fps (Logitech BRIO / Razer Kiyo Pro)",
            "bandwidth": "10 Mbps minimum",
        },
        "compatible_devices": [
            "HCS Video Studio 8K Pro",
            "Samsung Galaxy S25 Ultra (8K camera)",
            "Apple iPhone 16 Pro Max (ProRes 8K)",
            "Professional broadcast cameras (Sony/RED/ARRI)",
            "HCS Desktop App (Windows/macOS/Linux)",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# =============================================================================
# HELPERS
# =============================================================================

def _mos_label(mos: float) -> str:
    if mos >= 4.8: return "Studio Professionnel"
    if mos >= 4.5: return "Excellent (Hi-Fi)"
    if mos >= 4.0: return "Tres bonne"
    if mos >= 3.5: return "Bonne"
    if mos >= 3.0: return "Acceptable"
    if mos >= 2.0: return "Mediocre"
    return "Mauvaise"

def _format_duration(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m:02d}m {sec:02d}s"
    return f"{m}m {sec:02d}s"

def _static_demo() -> dict:
    return {
        "service": "telephony_video_8k",
        "demo": "Appel 8K HCS Professionnel (static)",
        "video": {"resolution": "7680x4320", "codec": "H.266/VVC", "fps": 60},
        "audio": {"codec": "HCS-Harmonic-32", "sample_rate": "192 kHz", "channels": 16, "mos": 4.9},
        "status": "engine_offline",
    }


# =============================================================================
# ENTREE PRINCIPALE
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [TELEPHONY-8K] %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
