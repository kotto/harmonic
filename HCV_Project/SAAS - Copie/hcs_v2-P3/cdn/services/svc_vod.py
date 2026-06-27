"""
HCS MiniCDN - Service VOD Premium (port 9014)
============================================
VOD premium mondial 4K HDR
Codec: H.265/HEVC | DASH | HDR10/DolbyVision | Dolby Digital Plus 5.1
HCS preset: audiovisuel_pro (ratio ~6:1)
"""

import os, sys, json, logging, random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from services.service_base import HCSServiceBase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "config", "services.json")) as f:
    CDN_CONFIG = json.load(f)

service_config = CDN_CONFIG["services"]["vod_premium"]
PORT = int(os.getenv("HCS_SERVICE_PORT", service_config["port"]))

svc = HCSServiceBase(service_config, PORT)
app = svc.app


@app.get("/catalog")
async def get_catalog(genre: str = "all", limit: int = 20):
    """Catalogue VOD Premium."""
    catalog = [
        {"id": "v001", "title": "L'Odyssée Quantique",   "genre": "SF",       "year": 2025, "duration_min": 128, "rating": 8.4, "hdr": "Dolby Vision", "resolution": "4K"},
        {"id": "v002", "title": "La Dernière Symphonie",  "genre": "Drame",    "year": 2025, "duration_min": 142, "rating": 9.1, "hdr": "HDR10",        "resolution": "4K"},
        {"id": "v003", "title": "Safari 8K",              "genre": "Doc",      "year": 2024, "duration_min": 95,  "rating": 8.8, "hdr": "HDR10+",       "resolution": "8K"},
        {"id": "v004", "title": "Champions du Monde",     "genre": "Sport",    "year": 2025, "duration_min": 185, "rating": 8.6, "hdr": "HDR10",        "resolution": "4K"},
        {"id": "v005", "title": "Nuit de Paris",          "genre": "Thriller", "year": 2024, "duration_min": 112, "rating": 7.9, "hdr": "HDR10",        "resolution": "4K"},
        {"id": "v006", "title": "Algorithme",             "genre": "SF",       "year": 2025, "duration_min": 135, "rating": 8.2, "hdr": "Dolby Vision", "resolution": "4K"},
        {"id": "v007", "title": "Concert Mondial Live",   "genre": "Musique",  "year": 2025, "duration_min": 180, "rating": 9.3, "hdr": "HDR10",        "resolution": "4K"},
        {"id": "v008", "title": "La Forêt Primaire",      "genre": "Doc",      "year": 2024, "duration_min": 78,  "rating": 8.5, "hdr": "HDR10+",       "resolution": "4K"},
    ]
    if genre != "all":
        catalog = [c for c in catalog if c["genre"].lower() == genre.lower()]
    return JSONResponse(content={
        "service": "vod_premium",
        "total": len(catalog),
        "catalog": catalog[:limit],
        "stream_quality": "4K HDR (H.265)",
        "hcs_format": "hcsv2",
        "price_per_gb_usd": service_config.get("price_per_gb"),
    })


@app.get("/content/{content_id}/info")
async def get_content_info(content_id: str):
    """Informations sur un contenu VOD."""
    return JSONResponse(content={
        "content_id": content_id,
        "service": "vod_premium",
        "stream_url": f"http://localhost:{PORT}/stream/{content_id}/manifest.mpd",
        "manifest_type": "DASH MPD",
        "codec": "H.265/HEVC",
        "resolution": "3840x2160",
        "hdr": "HDR10 / Dolby Vision",
        "audio": "Dolby Digital Plus 5.1",
        "subtitles": ["fr", "en", "de", "es", "ar", "zh"],
        "drm": "Multi-DRM (Widevine + PlayReady + FairPlay)",
        "hcs_preset": "audiovisuel_pro",
        "hcs_ratio": 6,
        "file_size_hcs_gb": round(random.uniform(2, 8), 1),
        "file_size_raw_gb": round(random.uniform(12, 48), 1),
    })


@app.post("/watchlist/add")
async def add_to_watchlist(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    return JSONResponse(content={
        "content_id": body.get("content_id"),
        "action": "added_to_watchlist",
        "service": "vod_premium",
    })


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [VOD] %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
