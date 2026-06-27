"""
HCS MiniCDN - Service Streaming Mobile Afrique (port 9013)
===========================================================
Streaming mobile ultra-optimisé pour l'Afrique
Bande passante maximale: 1 Mbps (2G/3G compatible)
Codec: H.264 Baseline | HLS | ABR 4 profils (144p-480p)
HCS preset: web_streaming (ratio ~20:1)
Fonctionnalités: Mode hors-ligne, compression agressive, faible conso data
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

service_config = CDN_CONFIG["services"]["mobile_streaming_africa"]
PORT = int(os.getenv("HCS_SERVICE_PORT", service_config["port"]))

svc = HCSServiceBase(service_config, PORT)
app = svc.app


# Tarifs data mobile Afrique (USD/MB, approximatif)
AFRICA_DATA_PRICES = {
    "NG": {"country": "Nigeria",        "usd_per_mb": 0.015, "avg_speed_mbps": 3.5},
    "ZA": {"country": "Afrique du Sud", "usd_per_mb": 0.008, "avg_speed_mbps": 12.0},
    "EG": {"country": "Egypte",         "usd_per_mb": 0.010, "avg_speed_mbps": 8.0},
    "SN": {"country": "Senegal",        "usd_per_mb": 0.020, "avg_speed_mbps": 2.5},
    "CI": {"country": "Cote d'Ivoire",  "usd_per_mb": 0.018, "avg_speed_mbps": 3.0},
    "GH": {"country": "Ghana",          "usd_per_mb": 0.012, "avg_speed_mbps": 4.0},
    "CM": {"country": "Cameroun",       "usd_per_mb": 0.022, "avg_speed_mbps": 2.0},
    "KE": {"country": "Kenya",          "usd_per_mb": 0.009, "avg_speed_mbps": 6.0},
    "ET": {"country": "Ethiopie",       "usd_per_mb": 0.025, "avg_speed_mbps": 1.5},
    "MA": {"country": "Maroc",          "usd_per_mb": 0.008, "avg_speed_mbps": 10.0},
}


@app.post("/detect-connection")
async def detect_connection(request: Request):
    """Détecte la connexion et adapte la qualité pour l'Afrique."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    speed_kbps = float(body.get("speed_kbps", 500))
    country = body.get("country", "NG").upper()
    signal_strength = body.get("signal", "3G")

    # Profil selon la vitesse
    if speed_kbps >= 700:
        profile = {"name": "480p", "resolution": "854x480", "bitrate_kbps": 800, "codec": "H.264"}
        mode = "Standard"
    elif speed_kbps >= 350:
        profile = {"name": "360p", "resolution": "640x360", "bitrate_kbps": 450, "codec": "H.264"}
        mode = "Économique"
    elif speed_kbps >= 150:
        profile = {"name": "240p", "resolution": "426x240", "bitrate_kbps": 200, "codec": "H.264"}
        mode = "Très économique"
    else:
        profile = {"name": "144p", "resolution": "256x144", "bitrate_kbps": 80, "codec": "H.264"}
        mode = "Mode minimal (2G)"

    data_info = AFRICA_DATA_PRICES.get(country, {"usd_per_mb": 0.015, "avg_speed_mbps": 3.0})
    cost_per_hour = (profile["bitrate_kbps"] / 8) * 3600 / 1024 * data_info["usd_per_mb"]
    hcs_saving = cost_per_hour * (1 - 1/20)  # ratio 20:1

    return JSONResponse(content={
        "service": "mobile_streaming_africa",
        "country": country,
        "country_name": data_info.get("country", country),
        "detected_speed_kbps": speed_kbps,
        "signal": signal_strength,
        "mode": mode,
        "recommended_profile": profile,
        "hcs_preset": "web_streaming",
        "hcs_compression_ratio": 20,
        "cost_per_hour_usd": round(cost_per_hour, 4),
        "cost_saved_with_hcs_usd": round(hcs_saving, 4),
        "offline_mode_available": True,
        "buffer_seconds": 30,
        "data_price_usd_per_mb": data_info.get("usd_per_mb"),
    })


@app.get("/data-saver")
async def data_saver_stats():
    """Statistiques d'économie de données avec HCS."""
    return JSONResponse(content={
        "service": "mobile_streaming_africa",
        "hcs_compression_ratio": 20,
        "comparison": {
            "H.264_480p_30min_mb": 180,
            "HCS_480p_30min_mb": 9,
            "savings_pct": 95,
            "savings_mb": 171,
        },
        "monthly_30min_per_day": {
            "without_hcs_gb": round(180 * 30 / 1024, 2),
            "with_hcs_gb": round(9 * 30 / 1024, 2),
            "savings_gb": round((180 - 9) * 30 / 1024, 2),
        },
        "features": {
            "offline_download": True,
            "low_power_mode": True,
            "auto_quality": True,
            "data_budget_alerts": True,
            "background_prefetch": False,
        },
        "supported_networks": ["2G EDGE", "3G HSPA", "4G LTE", "WiFi"],
        "min_speed_kbps": 64,
    })


@app.get("/offline/catalog")
async def offline_catalog():
    """Catalogue disponible en téléchargement hors-ligne."""
    return JSONResponse(content={
        "service": "mobile_streaming_africa",
        "offline_enabled": True,
        "max_download_per_device_gb": 2,
        "hcs_format": "hcsv2",
        "note": "Les contenus sont telecharges en format .hcsv2 (20x plus compact)",
        "sample_content": [
            {"id": "af001", "title": "Les savanes africaines", "duration_min": 45, "size_hcs_mb": 25, "size_normal_mb": 500},
            {"id": "af002", "title": "Football Afrique",       "duration_min": 90, "size_hcs_mb": 50, "size_normal_mb": 1000},
            {"id": "af003", "title": "Cours de code Python",   "duration_min": 30, "size_hcs_mb": 15, "size_normal_mb": 300},
            {"id": "af004", "title": "Musique Afrobeat",       "duration_min": 60, "size_hcs_mb": 12, "size_normal_mb": 240},
        ],
    })


@app.get("/countries")
async def get_supported_countries():
    return JSONResponse(content={
        "service": "mobile_streaming_africa",
        "countries": [
            {**v, "code": k}
            for k, v in AFRICA_DATA_PRICES.items()
        ],
        "edge_nodes": service_config.get("cdn_edge_nodes", []),
        "sla_uptime": service_config.get("sla_uptime"),
    })


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [AFRICA] %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
