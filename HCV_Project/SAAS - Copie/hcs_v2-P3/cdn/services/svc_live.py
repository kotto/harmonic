"""
HCS MiniCDN - Service Live Events (port 9015)
=============================================
Diffusion live ultra-basse latence: sports, concerts, TV en direct
Protocol: WebRTC / LL-HLS | Codec: H.264/H.265
HCS preset: broadcast_hd (ratio ~5:1)
Latence cible: <100ms (LL-HLS) / <50ms (WebRTC)
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

service_config = CDN_CONFIG["services"]["live_events"]
PORT = int(os.getenv("HCS_SERVICE_PORT", service_config["port"]))

svc = HCSServiceBase(service_config, PORT)
app = svc.app

# Evenements simulés
LIVE_EVENTS = [
    {"id": "live001", "title": "Finale Champions League 2025", "sport": "Football",    "viewers": 8500000, "latency_ms": 85,  "status": "live", "start": "2025-06-01T19:00:00Z"},
    {"id": "live002", "title": "Concert Beyonce World Tour",   "sport": "Musique",     "viewers": 2100000, "latency_ms": 92,  "status": "live", "start": "2025-06-02T21:00:00Z"},
    {"id": "live003", "title": "F1 Grand Prix Monaco",         "sport": "Motorsport",  "viewers": 1800000, "latency_ms": 78,  "status": "live", "start": "2025-05-25T14:00:00Z"},
    {"id": "live004", "title": "NBA Finals Game 7",            "sport": "Basketball",  "viewers": 4200000, "latency_ms": 95,  "status": "upcoming", "start": "2025-06-15T21:00:00Z"},
    {"id": "live005", "title": "Roland Garros Finale",         "sport": "Tennis",      "viewers": 1200000, "latency_ms": 88,  "status": "upcoming", "start": "2025-06-08T15:00:00Z"},
    {"id": "live006", "title": "Paris 2028 - Ouverture",       "sport": "Olympisme",   "viewers": 9800000, "latency_ms": 100, "status": "upcoming", "start": "2028-07-26T20:30:00Z"},
]


@app.get("/events")
async def get_events(status: str = "all"):
    """Liste des événements live disponibles."""
    events = LIVE_EVENTS
    if status != "all":
        events = [e for e in events if e["status"] == status]

    total_viewers = sum(e["viewers"] for e in events if e["status"] == "live")

    return JSONResponse(content={
        "service": "live_events",
        "live_now": len([e for e in LIVE_EVENTS if e["status"] == "live"]),
        "upcoming": len([e for e in LIVE_EVENTS if e["status"] == "upcoming"]),
        "total_viewers_now": total_viewers,
        "events": events,
        "max_concurrent_viewers": service_config.get("concurrent_viewers_max"),
        "protocol": "LL-HLS / WebRTC",
        "latency_ms": "<100",
    })


@app.get("/events/{event_id}/stream")
async def get_event_stream(event_id: str, protocol: str = "ll-hls"):
    """Obtenir l'URL de stream d'un événement live."""
    event = next((e for e in LIVE_EVENTS if e["id"] == event_id), None)
    if not event:
        return JSONResponse(status_code=404, content={"error": f"Event {event_id} not found"})

    if protocol.lower() == "webrtc":
        stream_url = f"wss://localhost:{PORT}/webrtc/{event_id}"
        latency = "<50ms"
    else:
        stream_url = f"http://localhost:{PORT}/stream/{event_id}/manifest.m3u8"
        latency = "<100ms"

    return JSONResponse(content={
        "event_id": event_id,
        "event": event,
        "stream_url": stream_url,
        "protocol": protocol.upper(),
        "latency_target": latency,
        "codec": "H.264 / H.265",
        "resolution": "1920x1080",
        "hcs_preset": "broadcast_hd",
        "hcs_compression_ratio": 5,
        "drm": "AES-128",
        "buffer_seconds": 2,
    })


@app.get("/stats/realtime")
async def realtime_stats():
    """Statistiques en temps réel du service live."""
    live_count = len([e for e in LIVE_EVENTS if e["status"] == "live"])
    return JSONResponse(content={
        "service": "live_events",
        "live_events_count": live_count,
        "total_viewers": sum(e["viewers"] for e in LIVE_EVENTS if e["status"] == "live"),
        "bandwidth_used_gbps": round(live_count * random.uniform(5, 15), 1),
        "avg_latency_ms": round(random.uniform(80, 100), 1),
        "cdn_nodes_active": len(service_config.get("cdn_edge_nodes", [])),
        "error_rate_pct": round(random.uniform(0, 0.1), 3),
        "rebuffering_ratio": round(random.uniform(0, 0.5), 2),
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.post("/events/ingest")
async def ingest_stream(request: Request):
    """Point d'ingestion RTMP/SRT pour les encodeurs live."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    event_id = body.get("event_id", f"event_{random.randint(1000,9999)}")
    return JSONResponse(content={
        "event_id": event_id,
        "ingest_url": f"rtmp://localhost:{PORT}/live/{event_id}",
        "ingest_srt": f"srt://localhost:10000?streamid={event_id}",
        "backup_ingest": f"rtmp://backup.localhost:{PORT}/live/{event_id}",
        "hcs_transcoder": "active",
        "output_protocols": ["LL-HLS", "DASH", "WebRTC"],
        "resolutions": ["1080p50", "720p50", "480p25", "360p25"],
        "hcs_preset": "broadcast_hd",
    })


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [LIVE] %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
