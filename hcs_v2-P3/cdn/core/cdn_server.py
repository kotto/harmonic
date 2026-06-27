"""
HCS MiniCDN - Serveur Central
==============================
Routeur central qui distribue les requetes vers les differents
services de streaming en fonction du profil client.

Ports:
  9000 - CDN Gateway (ce serveur)
  9001 - Dashboard Admin
  9010 - TV Broadcast 4K
  9011 - TV Broadcast 8K
  9012 - Mobile Streaming 8K USA
  9013 - Mobile Streaming Afrique (1 Mbps)
  9014 - VOD Premium
  9015 - Live Events
  9016 - Archive Storage
"""

import os
import sys
import json
import time
import uuid
import random
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx
from fastapi import FastAPI, Request, Response, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ─── Chemins ───────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "services.json")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
CACHE_DIR = os.path.join(BASE_DIR, "cache")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# ─── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CDN] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOGS_DIR, "cdn.log"), encoding="utf-8")
    ]
)
log = logging.getLogger("HCS-CDN")

# ─── Config ────────────────────────────────────────────────────────────────
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CDN_CONFIG = json.load(f)

SERVICES = CDN_CONFIG["services"]
EDGE_NODES = CDN_CONFIG["edge_nodes"]

# ─── Métriques en mémoire (reset au redémarrage) ───────────────────────────
class CDNMetrics:
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.requests_total = 0
        self.requests_per_service: Dict[str, int] = {sid: 0 for sid in SERVICES}
        self.bytes_served: Dict[str, int] = {sid: 0 for sid in SERVICES}
        self.errors: Dict[str, int] = {sid: 0 for sid in SERVICES}
        self.latencies: Dict[str, list] = {sid: [] for sid in SERVICES}
        self.active_sessions: Dict[str, int] = {sid: 0 for sid in SERVICES}
        self.connections_history: list = []  # [(timestamp, service_id, region)]
        # Trafic simulé (Gbps) par service - mis à jour par simulate_traffic()
        self.current_traffic_gbps: Dict[str, float] = {sid: 0.0 for sid in SERVICES}
        self.peak_traffic_gbps: Dict[str, float] = {sid: 0.0 for sid in SERVICES}

    def record_request(self, service_id: str, latency_ms: float, bytes_out: int = 0, error: bool = False):
        self.requests_total += 1
        if service_id in self.requests_per_service:
            self.requests_per_service[service_id] += 1
        if error and service_id in self.errors:
            self.errors[service_id] += 1
        if service_id in self.bytes_served:
            self.bytes_served[service_id] += bytes_out
        if service_id in self.latencies:
            self.latencies[service_id].append(latency_ms)
            if len(self.latencies[service_id]) > 1000:
                self.latencies[service_id] = self.latencies[service_id][-1000:]

    def get_avg_latency(self, service_id: str) -> float:
        lats = self.latencies.get(service_id, [])
        return round(sum(lats) / len(lats), 1) if lats else 0.0

    def uptime_str(self) -> str:
        delta = datetime.utcnow() - self.start_time
        h = int(delta.total_seconds() // 3600)
        m = int((delta.total_seconds() % 3600) // 60)
        s = int(delta.total_seconds() % 60)
        return f"{h}h {m}m {s}s"

    def to_dict(self) -> dict:
        services_stats = {}
        for sid, svc in SERVICES.items():
            req = self.requests_per_service.get(sid, 0)
            err = self.errors.get(sid, 0)
            tb = self.bytes_served.get(sid, 0) / 1e12  # en TB
            services_stats[sid] = {
                "name": svc["name"],
                "status": svc["status"],
                "color": svc.get("color", "#888"),
                "requests": req,
                "errors": err,
                "error_rate": round(err / req * 100, 2) if req > 0 else 0.0,
                "traffic_tb": round(tb, 4),
                "avg_latency_ms": self.get_avg_latency(sid),
                "active_sessions": self.active_sessions.get(sid, 0),
                "current_traffic_gbps": round(self.current_traffic_gbps.get(sid, 0), 2),
                "peak_traffic_gbps": round(self.peak_traffic_gbps.get(sid, 0), 2),
                "port": svc.get("port"),
                "protocol": svc.get("protocol"),
                "resolution": svc.get("resolution"),
                "codec": svc.get("codec"),
                "hcs_preset": svc.get("hcs_preset"),
                "hcs_compression_ratio": svc.get("hcs_compression_ratio"),
                "regions": svc.get("regions", []),
                "cdn_edge_nodes": svc.get("cdn_edge_nodes", []),
                "sla_uptime": svc.get("sla_uptime"),
            }
        return {
            "uptime": self.uptime_str(),
            "requests_total": self.requests_total,
            "start_time": self.start_time.isoformat(),
            "services": services_stats,
            "edge_nodes": EDGE_NODES,
            "global_stats": CDN_CONFIG.get("global_stats", {}),
        }


metrics = CDNMetrics()

# ─── Simulation de trafic temps réel ────────────────────────────────────────
TRAFFIC_PROFILES = {
    "tv_broadcast_4k":       {"base": 12.0, "variance": 5.0, "peak_hours": [20, 21, 22, 23]},
    "tv_broadcast_8k":       {"base": 4.0,  "variance": 2.0, "peak_hours": [20, 21, 22]},
    "mobile_streaming_8k_us":{"base": 18.0, "variance": 8.0, "peak_hours": [18, 19, 20, 21]},
    "mobile_streaming_africa":{"base": 3.0, "variance": 1.5, "peak_hours": [19, 20, 21]},
    "vod_premium":           {"base": 8.0,  "variance": 4.0, "peak_hours": [19, 20, 21, 22, 23]},
    "live_events":           {"base": 1.0,  "variance": 20.0,"peak_hours": []},
    "archive_storage":       {"base": 0.5,  "variance": 0.3, "peak_hours": [2, 3, 4]},
}

async def simulate_traffic():
    """Met à jour les métriques de trafic toutes les 5 secondes."""
    while True:
        hour = datetime.utcnow().hour
        for sid, profile in TRAFFIC_PROFILES.items():
            base = profile["base"]
            var = profile["variance"]
            # Boost heures de pointe
            if hour in profile["peak_hours"]:
                base *= 1.8
            # Variation aléatoire ±var
            gbps = max(0.0, base + random.uniform(-var * 0.3, var * 0.3))
            metrics.current_traffic_gbps[sid] = gbps
            if gbps > metrics.peak_traffic_gbps.get(sid, 0):
                metrics.peak_traffic_gbps[sid] = gbps
            # Simuler requêtes
            fake_reqs = int(gbps * 10)
            for _ in range(fake_reqs):
                lat = random.gauss(SERVICES[sid].get("latency_ms", 100), 20)
                metrics.record_request(sid, lat, int(gbps * 1e6 / 100))
            # Sessions actives
            metrics.active_sessions[sid] = int(gbps * 1000 + random.randint(-50, 50))
        await asyncio.sleep(5)


# ─── WebSocket pour métriques temps réel ────────────────────────────────────
connected_ws: list = []

async def broadcast_metrics():
    """Envoie les métriques à tous les clients WebSocket connectés."""
    while True:
        if connected_ws:
            data = json.dumps(metrics.to_dict())
            dead = []
            for ws in connected_ws:
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                connected_ws.remove(ws)
        await asyncio.sleep(3)


# ─── Application FastAPI ─────────────────────────────────────────────────────
app = FastAPI(
    title="HCS MiniCDN - Gateway",
    description="Mini CDN HCS - Distribution multi-services 4K/8K mondial",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (frontend dashboard)
if os.path.isdir(FRONTEND_DIR):
    app.mount("/dashboard", StaticFiles(directory=FRONTEND_DIR, html=True), name="dashboard")


# ─── Démarrage ──────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(simulate_traffic())
    asyncio.create_task(broadcast_metrics())
    log.info("HCS MiniCDN Gateway demarree sur :9000")


# ═══════════════════════════════════════════════════════════════════════════
#  ENDPOINTS PUBLICS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "cdn": "HCS MiniCDN",
        "version": "1.0.0",
        "status": "operational",
        "dashboard": "http://localhost:9001",
        "services": {sid: f"http://localhost:{svc['port']}" for sid, svc in SERVICES.items()},
        "uptime": metrics.uptime_str(),
        "docs": "http://localhost:9000/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "uptime": metrics.uptime_str(),
        "timestamp": datetime.utcnow().isoformat(),
        "services_up": len([s for s in SERVICES.values() if s["status"] == "active"]),
        "services_total": len(SERVICES),
    }


@app.get("/api/metrics")
async def get_metrics():
    """Retourne toutes les métriques CDN."""
    return JSONResponse(content=metrics.to_dict())


@app.get("/api/services")
async def get_services():
    """Liste tous les services disponibles avec leur configuration."""
    return JSONResponse(content={
        "services": SERVICES,
        "edge_nodes": EDGE_NODES,
        "global_stats": CDN_CONFIG.get("global_stats", {}),
    })


@app.get("/api/services/{service_id}")
async def get_service(service_id: str):
    """Détails d'un service spécifique."""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' inconnu")
    svc = SERVICES[service_id]
    stats = metrics.to_dict()["services"].get(service_id, {})
    return JSONResponse(content={**svc, "stats": stats})


@app.get("/api/edge-nodes")
async def get_edge_nodes():
    """Liste tous les nœuds edge avec leur statut."""
    nodes = []
    for name, info in EDGE_NODES.items():
        nodes.append({
            "name": name,
            **info,
            "load_percent": random.randint(15, 85),
            "response_ms": random.randint(5, 50),
            "active_connections": random.randint(1000, 50000),
        })
    return JSONResponse(content={"edge_nodes": nodes, "total": len(nodes)})


@app.get("/api/traffic")
async def get_traffic():
    """Trafic actuel par service en Gbps."""
    traffic = {}
    total_gbps = 0.0
    for sid in SERVICES:
        gbps = metrics.current_traffic_gbps.get(sid, 0.0)
        traffic[sid] = {
            "service": SERVICES[sid]["name"],
            "current_gbps": round(gbps, 2),
            "peak_gbps": round(metrics.peak_traffic_gbps.get(sid, 0.0), 2),
            "active_sessions": metrics.active_sessions.get(sid, 0),
        }
        total_gbps += gbps
    return JSONResponse(content={
        "services": traffic,
        "total_gbps": round(total_gbps, 2),
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.post("/api/route")
async def route_request(request: Request):
    """
    Routage intelligent: détermine le meilleur service selon le profil client.
    Body JSON attendu:
      {
        "region": "US" | "AF" | "EU" | "AP" ...,
        "device": "mobile" | "tv" | "desktop",
        "bandwidth_mbps": 1.0,
        "quality": "max" | "balanced" | "low"
      }
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    region = body.get("region", "EU").upper()
    device = body.get("device", "desktop").lower()
    bandwidth = float(body.get("bandwidth_mbps", 10.0))
    quality = body.get("quality", "balanced").lower()

    # Logique de routage
    recommended = _select_service(region, device, bandwidth, quality)
    svc = SERVICES[recommended]

    t0 = time.time()
    lat = (time.time() - t0) * 1000
    metrics.record_request(recommended, lat)

    return JSONResponse(content={
        "recommended_service": recommended,
        "service_name": svc["name"],
        "service_url": f"http://localhost:{svc['port']}",
        "hcs_preset": svc["hcs_preset"],
        "protocol": svc["protocol"],
        "resolution": svc.get("resolution"),
        "codec": svc.get("codec"),
        "reasoning": _routing_reasoning(region, device, bandwidth, quality, recommended),
    })


def _select_service(region: str, device: str, bandwidth: float, quality: str) -> str:
    """Algorithme de routage CDN."""
    # Afrique ou bande passante très limitée
    if region in ("AF", "NG", "ZA", "EG", "SN", "CI", "GH", "CM", "KE", "ET") or bandwidth <= 2.0:
        return "mobile_streaming_africa"

    # USA mobile 8K
    if region in ("US", "CA") and device == "mobile" and bandwidth >= 30.0:
        return "mobile_streaming_8k_us"

    # TV 8K
    if device == "tv" and bandwidth >= 80.0 and quality == "max" and region in ("EU", "JP", "KR", "AP"):
        return "tv_broadcast_8k"

    # TV 4K
    if device == "tv" and bandwidth >= 20.0:
        return "tv_broadcast_4k"

    # Live
    if quality == "live":
        return "live_events"

    # VOD premium par défaut haute qualité
    if bandwidth >= 15.0 and quality in ("max", "balanced"):
        return "vod_premium"

    # Archivage
    if quality == "archive":
        return "archive_storage"

    # Fallback
    return "vod_premium"


def _routing_reasoning(region: str, device: str, bandwidth: float, quality: str, service_id: str) -> str:
    reasons = {
        "mobile_streaming_africa": f"Region {region} ou bande passante limitee ({bandwidth} Mbps) -> profil Africa optimise",
        "mobile_streaming_8k_us":  f"USA mobile 5G ({bandwidth} Mbps) -> streaming 8K AV1",
        "tv_broadcast_8k":         f"TV 8K region {region}, bande passante {bandwidth} Mbps",
        "tv_broadcast_4k":         f"TV 4K, {bandwidth} Mbps disponibles",
        "live_events":             "Mode live demande, ultra-basse latence",
        "vod_premium":             f"VOD Premium 4K - qualite {quality}, {bandwidth} Mbps",
        "archive_storage":         "Mode archivage long terme",
    }
    return reasons.get(service_id, "Routage par defaut")


# ─── WebSocket métriques temps réel ─────────────────────────────────────────
@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket):
    await websocket.accept()
    connected_ws.append(websocket)
    log.info("Client WebSocket connecte (total: %d)", len(connected_ws))
    try:
        # Envoyer immédiatement les métriques initiales
        await websocket.send_text(json.dumps(metrics.to_dict()))
        # Maintenir la connexion ouverte
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        log.info("Client WebSocket deconnecte")
    finally:
        if websocket in connected_ws:
            connected_ws.remove(websocket)


# ─── Proxy vers l'origine (HCS Server) ──────────────────────────────────────
@app.api_route("/proxy/{service_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_service(service_id: str, path: str, request: Request):
    """
    Proxy transparent vers un service HCS.
    Exemple: GET /proxy/tv_broadcast_4k/api/v2/health
    """
    if service_id not in SERVICES:
        raise HTTPException(404, f"Service inconnu: {service_id}")

    origin = CDN_CONFIG["origin_server"]
    url = f"{origin}/{path}"
    if request.url.query:
        url += "?" + request.url.query

    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method=request.method,
                url=url,
                headers={k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")},
                content=await request.body(),
            )
        lat = (time.time() - t0) * 1000
        metrics.record_request(service_id, lat, len(resp.content))

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
            media_type=resp.headers.get("content-type"),
        )
    except Exception as e:
        lat = (time.time() - t0) * 1000
        metrics.record_request(service_id, lat, error=True)
        raise HTTPException(502, f"Erreur proxy vers {service_id}: {e}")


# ═══════════════════════════════════════════════════════════════════════════
#  ENDPOINT SIMULATION CDN (pour tests sans vrai trafic)
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/simulate/stream")
async def simulate_stream(request: Request):
    """Simule une requête de streaming et retourne les métriques."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    service_id = body.get("service_id", "vod_premium")
    duration_s = float(body.get("duration_seconds", 60))

    if service_id not in SERVICES:
        raise HTTPException(404, f"Service inconnu: {service_id}")

    svc = SERVICES[service_id]
    bitrate_mbps = svc.get("bitrate_mbps") or (svc.get("bitrate_kbps", 800) / 1000)
    bytes_served = int(duration_s * bitrate_mbps * 1e6 / 8)
    hcs_ratio = svc.get("hcs_compression_ratio", 1)

    lat = random.gauss(svc.get("latency_ms", 100), 20)
    metrics.record_request(service_id, lat, bytes_served)

    return JSONResponse(content={
        "service_id": service_id,
        "service_name": svc["name"],
        "duration_s": duration_s,
        "bitrate_mbps": bitrate_mbps,
        "bytes_served": bytes_served,
        "bytes_served_mb": round(bytes_served / 1e6, 2),
        "hcs_compression_ratio": hcs_ratio,
        "bytes_without_hcs": bytes_served * hcs_ratio,
        "savings_mb": round(bytes_served * (hcs_ratio - 1) / 1e6, 2),
        "latency_ms": round(lat, 1),
        "protocol": svc["protocol"],
        "codec": svc["codec"],
        "resolution": svc.get("resolution"),
        "hcs_preset": svc["hcs_preset"],
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.get("/api/cost-estimate")
async def cost_estimate(
    service_id: str = "tv_broadcast_4k",
    viewers: int = 1000,
    hours_per_day: float = 4.0,
    days: int = 30
):
    """Calcule le coût CDN estimé avec et sans compression HCS."""
    if service_id not in SERVICES:
        raise HTTPException(404, detail=f"Service inconnu: {service_id}")

    svc = SERVICES[service_id]
    bitrate_mbps = svc.get("bitrate_mbps") or (svc.get("bitrate_kbps", 800) / 1000)
    price_per_gb = svc.get("price_per_gb", 0.05)
    hcs_ratio = svc.get("hcs_compression_ratio", 1)

    # Total bytes servis
    total_seconds = viewers * hours_per_day * 3600 * days
    bytes_without_hcs = total_seconds * bitrate_mbps * 1e6 / 8
    bytes_with_hcs = bytes_without_hcs / hcs_ratio
    gb_without = bytes_without_hcs / 1e9
    gb_with = bytes_with_hcs / 1e9

    cost_without = gb_without * price_per_gb
    cost_with = gb_with * price_per_gb
    savings = cost_without - cost_with

    return JSONResponse(content={
        "service_id": service_id,
        "service_name": svc["name"],
        "viewers": viewers,
        "hours_per_day": hours_per_day,
        "days": days,
        "bitrate_mbps": bitrate_mbps,
        "hcs_compression_ratio": hcs_ratio,
        "traffic_without_hcs_tb": round(gb_without / 1000, 3),
        "traffic_with_hcs_tb": round(gb_with / 1000, 3),
        "cost_without_hcs_usd": round(cost_without, 2),
        "cost_with_hcs_usd": round(cost_with, 2),
        "savings_usd": round(savings, 2),
        "savings_pct": round(savings / cost_without * 100, 1) if cost_without > 0 else 0,
        "price_per_gb_usd": price_per_gb,
    })


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "cdn_server:app",
        host="0.0.0.0",
        port=9000,
        reload=False,
        access_log=True,
    )
