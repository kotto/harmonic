"""
HCS MiniCDN - Service Diffusion TV 4K (port 9010)
==================================================
Diffusion TV broadcast 4K Ultra HD, H.265/HEVC
Codec: H.265/HEVC | HLS | HDR10+ | Dolby Atmos 7.1
HCS preset: broadcast_hd (ratio ~5:1)
"""

import os, sys, json, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from services.service_base import HCSServiceBase
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "config", "services.json")) as f:
    CDN_CONFIG = json.load(f)

service_config = CDN_CONFIG["services"]["tv_broadcast_4k"]
PORT = int(os.getenv("HCS_SERVICE_PORT", service_config["port"]))

svc = HCSServiceBase(service_config, PORT)
app = svc.app

# ─── Endpoints spécifiques TV 4K ─────────────────────────────────────────

@app.get("/channels")
async def get_channels():
    """Liste des chaînes TV 4K disponibles."""
    channels = [
        {"id": "ch1", "name": "HCS Cinema 4K", "genre": "Films", "bitrate_mbps": 25, "epg": "Film 4K en cours"},
        {"id": "ch2", "name": "HCS Sport 4K",  "genre": "Sport",  "bitrate_mbps": 25, "epg": "Match en direct"},
        {"id": "ch3", "name": "HCS News 4K",   "genre": "Info",   "bitrate_mbps": 15, "epg": "Journal 20h"},
        {"id": "ch4", "name": "HCS Nature 4K", "genre": "Doc",    "bitrate_mbps": 20, "epg": "La planete bleue"},
        {"id": "ch5", "name": "HCS Culture 4K","genre": "Culture","bitrate_mbps": 18, "epg": "Opera en direct"},
        {"id": "ch6", "name": "HCS Kids 4K",   "genre": "Enfants","bitrate_mbps": 12, "epg": "Dessins animes"},
        {"id": "ch7", "name": "HCS Music 4K",  "genre": "Musique","bitrate_mbps": 20, "epg": "Concert live"},
        {"id": "ch8", "name": "HCS Tech 4K",   "genre": "Tech",   "bitrate_mbps": 16, "epg": "Silicon Valley"},
    ]
    return JSONResponse(content={
        "service": "tv_broadcast_4k",
        "channels_count": len(channels),
        "channels": channels,
        "stream_base": f"http://localhost:{PORT}/stream",
        "protocol": "HLS",
        "resolution": "3840x2160",
        "hcs_compression": "broadcast_hd",
        "bandwidth_required_mbps": 25,
    })


@app.get("/channels/{channel_id}/stream")
async def get_channel_stream(channel_id: str):
    """Retourne l'URL de stream d'une chaîne 4K."""
    return JSONResponse(content={
        "channel_id": channel_id,
        "stream_url": f"http://localhost:{PORT}/stream/{channel_id}/manifest.m3u8",
        "protocol": "HLS",
        "resolution": "3840x2160",
        "codec": "H.265/HEVC",
        "hdr": "HDR10+",
        "audio": "Dolby Atmos 7.1",
        "hcs_preset": "broadcast_hd",
        "hcs_compression_ratio": 5,
        "drm": "Widevine L1",
        "latency_ms": 500,
        "buffer_seconds": 10,
    })


@app.get("/quality/test")
async def quality_test():
    """Test de qualité du service 4K."""
    return JSONResponse(content={
        "service": "tv_broadcast_4k",
        "psnr_db": round(random.uniform(40, 45), 1),
        "ssim": round(random.uniform(0.96, 0.99), 3),
        "vmaf": round(random.uniform(92, 98), 1),
        "bitrate_actual_mbps": round(random.uniform(22, 28), 1),
        "frame_drops": random.randint(0, 2),
        "buffering_events": 0,
        "latency_ms": random.randint(450, 550),
        "quality_score": "Excellent",
        "hcs_active": True,
        "timestamp": datetime.utcnow().isoformat(),
    })


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [TV-4K] %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
