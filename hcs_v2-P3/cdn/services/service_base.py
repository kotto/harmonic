"""
HCS MiniCDN - Classe de base pour tous les services
====================================================
Chaque service hérite de cette classe qui fournit:
- Endpoints santé, info, stream simulation
- Intégration HCS compression
- Métriques locales
- Profils ABR (Adaptive Bitrate)
"""

import os
import sys
import json
import time
import random
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Chemin vers le serveur HCS origine
HCS_ORIGIN = os.getenv("HCS_ORIGIN", "http://localhost:8009")
CDN_GATEWAY = os.getenv("CDN_GATEWAY", "http://localhost:9000")


class HCSServiceBase:
    """
    Classe de base pour un service CDN HCS.
    Crée une application FastAPI avec tous les endpoints standards.
    """

    def __init__(self, service_config: dict, port: int):
        self.config = service_config
        self.service_id = service_config["id"]
        self.port = port
        self.start_time = datetime.utcnow()

        # Métriques locales
        self.requests = 0
        self.bytes_served = 0
        self.errors = 0
        self.active_streams = 0
        self.latencies: List[float] = []

        # Logger
        self.log = logging.getLogger(f"HCS-SVC-{self.service_id}")

        # FastAPI app
        self.app = FastAPI(
            title=f"HCS CDN - {service_config['name']}",
            description=service_config["description"],
            version="1.0.0",
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Routes
        self._register_routes()

    def _register_routes(self):
        """Enregistre les routes FastAPI."""
        app = self.app
        svc = self

        @app.get("/")
        async def root():
            return {
                "service": svc.config["name"],
                "id": svc.service_id,
                "status": "active",
                "port": svc.port,
                "protocol": svc.config.get("protocol"),
                "resolution": svc.config.get("resolution"),
                "codec": svc.config.get("codec"),
                "hcs_preset": svc.config.get("hcs_preset"),
                "regions": svc.config.get("regions", []),
                "edge_nodes": svc.config.get("cdn_edge_nodes", []),
            }

        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": svc.service_id,
                "uptime": svc._uptime(),
                "requests": svc.requests,
                "active_streams": svc.active_streams,
                "error_rate": svc._error_rate(),
                "avg_latency_ms": svc._avg_latency(),
                "timestamp": datetime.utcnow().isoformat(),
            }

        @app.get("/info")
        async def info():
            return {
                "service": svc.config,
                "stats": svc._local_stats(),
                "abr_profiles": svc.config.get("abr_profiles", []),
                "drm": svc.config.get("drm"),
                "color_space": svc.config.get("color_space"),
                "sla_uptime": svc.config.get("sla_uptime"),
            }

        @app.get("/stats")
        async def stats():
            return JSONResponse(content=svc._local_stats())

        @app.post("/stream/start")
        async def stream_start(request: Request):
            """Démarre une session de streaming simulée."""
            try:
                body = await request.json()
            except Exception:
                body = {}

            client_id = body.get("client_id", f"client_{random.randint(1000,9999)}")
            quality = body.get("quality", "auto")
            region = body.get("region", "EU")

            # Sélectionner le profil ABR
            profile = svc._select_abr_profile(quality)

            svc.active_streams += 1
            svc.requests += 1

            session_id = f"{svc.service_id}_{client_id}_{int(time.time())}"

            return JSONResponse(content={
                "session_id": session_id,
                "service": svc.service_id,
                "client_id": client_id,
                "region": region,
                "profile": profile,
                "stream_url": f"http://localhost:{svc.port}/stream/{session_id}/manifest.m3u8",
                "hcs_preset": svc.config.get("hcs_preset"),
                "drm": svc.config.get("drm"),
                "started_at": datetime.utcnow().isoformat(),
            })

        @app.post("/stream/stop")
        async def stream_stop(request: Request):
            """Arrête une session de streaming."""
            try:
                body = await request.json()
            except Exception:
                body = {}
            session_id = body.get("session_id", "")
            if svc.active_streams > 0:
                svc.active_streams -= 1
            return JSONResponse(content={
                "session_id": session_id,
                "status": "stopped",
                "service": svc.service_id,
            })

        @app.get("/stream/{session_id}/manifest.m3u8")
        async def get_manifest(session_id: str):
            """Retourne un manifeste HLS simulé."""
            manifest = svc._generate_hls_manifest(session_id)
            return StreamingResponse(
                iter([manifest]),
                media_type="application/vnd.apple.mpegurl",
                headers={"X-HCS-Service": svc.service_id, "X-HCS-Preset": svc.config.get("hcs_preset", "")},
            )

        @app.get("/abr/profiles")
        async def abr_profiles():
            """Retourne les profils ABR disponibles."""
            return JSONResponse(content={
                "service": svc.service_id,
                "profiles": svc.config.get("abr_profiles", [
                    {"name": svc.config.get("resolution", "auto"),
                     "resolution": svc.config.get("resolution"),
                     "bitrate_mbps": svc.config.get("bitrate_mbps", 0)}
                ]),
            })

        @app.post("/compress")
        async def compress_content(request: Request):
            """Compresse un contenu via le serveur HCS d'origine."""
            t0 = time.time()
            try:
                form = await request.form()
                preset = svc.config.get("hcs_preset", "audiovisuel_pro")

                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{HCS_ORIGIN}/api/v2/compress/video",
                        data={"preset": preset, "max_frames": "50"},
                        files={"file": (form["file"].filename, await form["file"].read(), form["file"].content_type)},
                    )

                lat = (time.time() - t0) * 1000
                svc.latencies.append(lat)

                if resp.status_code == 200:
                    svc.bytes_served += len(resp.content)
                    return StreamingResponse(
                        iter([resp.content]),
                        media_type="application/octet-stream",
                        headers={
                            "Content-Disposition": f"attachment; filename=compressed_{preset}.hcsv2",
                            "X-HCS-Service": svc.service_id,
                            **dict(resp.headers),
                        },
                    )
                else:
                    svc.errors += 1
                    raise HTTPException(status_code=resp.status_code, detail=resp.text[:500])

            except HTTPException:
                raise
            except Exception as e:
                svc.errors += 1
                raise HTTPException(status_code=500, detail=f"Erreur compression: {e}")

    def _uptime(self) -> str:
        delta = datetime.utcnow() - self.start_time
        h = int(delta.total_seconds() // 3600)
        m = int((delta.total_seconds() % 3600) // 60)
        s = int(delta.total_seconds() % 60)
        return f"{h}h {m}m {s}s"

    def _error_rate(self) -> float:
        if self.requests == 0:
            return 0.0
        return round(self.errors / self.requests * 100, 2)

    def _avg_latency(self) -> float:
        if not self.latencies:
            return self.config.get("latency_ms", 0)
        return round(sum(self.latencies[-100:]) / len(self.latencies[-100:]), 1)

    def _local_stats(self) -> dict:
        return {
            "service_id": self.service_id,
            "uptime": self._uptime(),
            "requests": self.requests,
            "bytes_served_mb": round(self.bytes_served / 1e6, 2),
            "errors": self.errors,
            "error_rate_pct": self._error_rate(),
            "active_streams": self.active_streams,
            "avg_latency_ms": self._avg_latency(),
            "target_latency_ms": self.config.get("latency_ms", 0),
            "hcs_compression_ratio": self.config.get("hcs_compression_ratio", 1),
            "sla_uptime": self.config.get("sla_uptime"),
            "price_per_gb_usd": self.config.get("price_per_gb", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _select_abr_profile(self, quality: str) -> dict:
        """Sélectionne le profil ABR selon la qualité demandée."""
        profiles = self.config.get("abr_profiles")
        if not profiles:
            return {
                "name": self.config.get("resolution", "auto"),
                "resolution": self.config.get("resolution"),
                "bitrate_mbps": self.config.get("bitrate_mbps", 0),
                "codec": self.config.get("codec"),
            }
        if quality == "max" or quality == "auto":
            return profiles[0]
        elif quality == "low":
            return profiles[-1]
        else:
            return profiles[len(profiles) // 2]

    def _generate_hls_manifest(self, session_id: str) -> str:
        """Génère un manifeste HLS M3U8 simulé."""
        profiles = self.config.get("abr_profiles")
        lines = ["#EXTM3U", "#EXT-X-VERSION:6", ""]

        if profiles:
            for p in profiles:
                bw = int((p.get("bitrate_mbps", p.get("bitrate_kbps", 800) / 1000)) * 1_000_000)
                res = p.get("resolution", "1280x720")
                lines.append(f"#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={res},CODECS=\"{self.config.get('codec','avc1')}\",NAME=\"{p['name']}\"")
                lines.append(f"http://localhost:{self.port}/stream/{session_id}/{p['name']}/index.m3u8")
                lines.append("")
        else:
            bw = int(self.config.get("bitrate_mbps", 5) * 1_000_000)
            res = self.config.get("resolution", "1920x1080")
            lines.append(f"#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={res}")
            lines.append(f"http://localhost:{self.port}/stream/{session_id}/main/index.m3u8")

        return "\n".join(lines)

    def run(self):
        """Lance le serveur uvicorn."""
        import uvicorn
        self.log.info("Demarrage service %s sur port %d", self.service_id, self.port)
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, access_log=False)
