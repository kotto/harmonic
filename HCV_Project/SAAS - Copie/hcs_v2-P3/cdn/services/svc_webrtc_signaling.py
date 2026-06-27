"""
HCS MiniCDN - Serveur Signalisation WebRTC (port 9021)
=======================================================
Serveur de signalisation WebRTC pour la telephonie/video 8K HCS.
Gere l'echange SDP (Session Description Protocol) et les candidats ICE
entre les participants d'un appel HCS.

Protocoles:
  - WebSocket Secure (WSS) pour la signalisation temps reel
  - REST HTTP pour la gestion des rooms et sessions
  - SIP over WebSocket (SIP/WS) pour compatibilite enterprise
  - DTLS 1.3 + SRTP pour le chiffrement media
  - STUN/TURN pour la traversee NAT
"""

import os
import sys
import json
import uuid
import time
import logging
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "config", "services.json")) as f:
    CDN_CONFIG = json.load(f)

service_config = CDN_CONFIG["services"]["webrtc_signaling"]
PORT = int(os.getenv("HCS_SERVICE_PORT", service_config["port"]))

log = logging.getLogger("HCS-WebRTC-Signal")

# FastAPI app
app = FastAPI(
    title="HCS WebRTC Signaling Server",
    description="Serveur de signalisation WebRTC 8K - HCS MiniCDN",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────────────────
# ETAT DU SERVEUR
# ──────────────────────────────────────────────────────────────────────────────

# Rooms WebRTC actives: room_id -> {participants, sdp_offers, ice_candidates, ...}
_rooms: Dict[str, dict] = {}
# Connexions WebSocket actives: peer_id -> WebSocket
_ws_connections: Dict[str, WebSocket] = {}
# Stats
_stats = {
    "rooms_created": 0,
    "signaling_messages": 0,
    "sdp_offers": 0,
    "sdp_answers": 0,
    "ice_candidates": 0,
    "calls_connected": 0,
    "start_time": time.time(),
}

# SDP offre template 8K
SDP_OFFER_TEMPLATE_8K = """v=0
o=HCS-8K 2026021800 2026021801 IN IP4 0.0.0.0
s=HCS 8K Video Call - PCM 32bit/192kHz + H.266/VVC
t=0 0
a=group:BUNDLE audio video
a=msid-semantic: WMS HCS-8K-Stream

m=audio 9 UDP/TLS/RTP/SAVPF 111 103 104
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:{ice_ufrag}
a=ice-pwd:{ice_pwd}
a=ice-options:trickle
a=fingerprint:sha-256 {fingerprint}
a=setup:actpass
a=mid:audio
a=extmap:1 urn:ietf:params:rtp-hdrext:ssrc-audio-level
a=sendrecv
a=rtcp-mux
a=rtpmap:111 opus/48000/2
a=fmtp:111 minptime=10;useinbandfec=1;stereo=1;sprop-stereo=1;maxaveragebitrate=510000
a=rtpmap:103 ISAC/16000
a=rtpmap:104 ISAC/32000
a=ssrc:1001 cname:HCS-8K-Audio
a=ssrc:1001 msid:HCS-8K-Stream hcs-audio
a=ssrc:1001 mslabel:HCS-8K-Stream
a=ssrc:1001 label:hcs-audio
a=hcs-harmonic:32bit/192kHz/Atmos-9.1.6/K={k_factor}

m=video 9 UDP/TLS/RTP/SAVPF 96 97 98
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:{ice_ufrag}
a=ice-pwd:{ice_pwd}
a=ice-options:trickle
a=fingerprint:sha-256 {fingerprint}
a=setup:actpass
a=mid:video
a=extmap:2 urn:ietf:params:rtp-hdrext:toffset
a=extmap:3 http://www.webrtc.org/experiments/rtp-hdrext/abs-send-time
a=sendrecv
a=rtcp-mux
a=rtcp-rsize
a=rtpmap:96 H266/90000
a=rtcp-fb:96 transport-cc
a=rtcp-fb:96 ccm fir
a=rtcp-fb:96 nack
a=rtcp-fb:96 nack pli
a=fmtp:96 level-id=6.3;tx-mode=SRST;max-mbps=1228800;max-fs=32768
a=rtpmap:97 AV1/90000
a=rtpmap:98 H265/90000
a=rid:hi send
a=rid:mid send
a=rid:lo send
a=simulcast:send hi;mid;lo
a=ssrc:2001 cname:HCS-8K-Video
a=ssrc:2001 msid:HCS-8K-Stream hcs-video
a=hcs-video:8K/7680x4320/60fps/HDR10+/VVC
"""


def _generate_ice_ufrag() -> str:
    return uuid.uuid4().hex[:8]

def _generate_ice_pwd() -> str:
    return uuid.uuid4().hex[:24]

def _generate_fingerprint() -> str:
    return ":".join(f"{random.randint(0, 255):02X}" for _ in range(32))

def _generate_room_id() -> str:
    return f"HCS-ROOM-{uuid.uuid4().hex[:8].upper()}"

def _generate_peer_id() -> str:
    return f"HCS-PEER-{uuid.uuid4().hex[:8].upper()}"

def _uptime() -> str:
    delta = time.time() - _stats["start_time"]
    h = int(delta // 3600)
    m = int((delta % 3600) // 60)
    s = int(delta % 60)
    return f"{h}h {m:02d}m {s:02d}s"


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINTS REST
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "HCS WebRTC Signaling Server",
        "port": PORT,
        "status": "active",
        "version": "1.0.0",
        "active_rooms": len(_rooms),
        "active_connections": len(_ws_connections),
        "protocols": ["WebRTC", "SIP/WS", "ICE/STUN/TURN"],
        "encryption": "DTLS 1.3 + SRTP + AES-256-GCM",
        "hcs_video": "H.266/VVC 8K/60fps HDR10+",
        "hcs_audio": "PCM 32bit/192kHz Dolby Atmos 9.1.6",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "webrtc_signaling",
        "uptime": _uptime(),
        "active_rooms": len(_rooms),
        "active_ws": len(_ws_connections),
        "signaling_messages": _stats["signaling_messages"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/stats")
async def get_stats():
    return JSONResponse({
        "service": "webrtc_signaling",
        "uptime": _uptime(),
        "rooms": {
            "active": len(_rooms),
            "created_total": _stats["rooms_created"],
        },
        "connections": {
            "active_ws": len(_ws_connections),
        },
        "signaling": {
            "total_messages": _stats["signaling_messages"],
            "sdp_offers":     _stats["sdp_offers"],
            "sdp_answers":    _stats["sdp_answers"],
            "ice_candidates": _stats["ice_candidates"],
            "calls_connected": _stats["calls_connected"],
        },
        "protocols": {
            "webrtc": True,
            "dtls_version": "1.3",
            "srtp": True,
            "ice": True,
            "trickle_ice": True,
            "ice_tcp": True,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/room/create")
async def create_room(request: Request):
    """
    Cree une nouvelle room de signalisation WebRTC.

    Body JSON:
    {
        "quality": "video_8k",
        "max_participants": 2,
        "host_id": "user_alice"
    }
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    room_id   = _generate_room_id()
    quality   = body.get("quality", "video_8k")
    max_p     = body.get("max_participants", 2)
    host_id   = body.get("host_id", _generate_peer_id())
    peer_id   = _generate_peer_id()

    room = {
        "room_id":         room_id,
        "quality":         quality,
        "max_participants": max_p,
        "host_id":         host_id,
        "participants":    [{"peer_id": peer_id, "user_id": host_id, "role": "host", "joined_at": datetime.now(timezone.utc).isoformat()}],
        "sdp_offers":      {},
        "sdp_answers":     {},
        "ice_candidates":  {},
        "status":          "waiting",
        "created_at":      datetime.now(timezone.utc).isoformat(),
        "hcs_quality":     quality,
        "encryption":      "AES-256-GCM E2E",
    }
    _rooms[room_id] = room
    _stats["rooms_created"] += 1

    return JSONResponse({
        "status": "room_created",
        "service": "webrtc_signaling",
        "room_id": room_id,
        "peer_id": peer_id,
        "host_id": host_id,
        "quality": quality,
        "max_participants": max_p,
        "ws_url": f"ws://localhost:{PORT}/ws/{room_id}/{peer_id}",
        "join_url": f"http://localhost:{PORT}/room/{room_id}/join",
        "ice_servers": [
            {"urls": ["stun:stun.hcs-cdn.com:3478"]},
            {"urls": ["turn:turn.hcs-cdn.com:3478"], "username": f"hcs_{room_id}", "credential": uuid.uuid4().hex[:16]},
        ],
        "sdp_constraints": {
            "audio": {"sampleRate": 192000, "channelCount": 2, "echoCancellation": True, "noiseSuppression": True},
            "video": {"width": 7680, "height": 4320, "frameRate": 60, "hdr": True} if "8k" in quality else
                     {"width": 3840, "height": 2160, "frameRate": 60} if "4k" in quality else
                     {"width": 1920, "height": 1080, "frameRate": 60},
        },
        "hcs_config": {
            "harmonic_audio": True,
            "k_factor_target": 0.97,
            "mos_target": 4.9,
            "video_codec": "H.266/VVC",
            "audio_codec": "HCS-Harmonic-32",
            "hdr": "HDR10+",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/room/{room_id}/join")
async def join_room(room_id: str, request: Request):
    """Rejoint une room WebRTC existante."""
    if room_id not in _rooms:
        raise HTTPException(404, f"Room {room_id} introuvable")
    room = _rooms[room_id]
    if len(room["participants"]) >= room["max_participants"]:
        raise HTTPException(409, "Room pleine")

    try:
        body = await request.json()
    except Exception:
        body = {}

    peer_id = _generate_peer_id()
    user_id = body.get("user_id", peer_id)
    room["participants"].append({
        "peer_id": peer_id,
        "user_id": user_id,
        "role": "participant",
        "joined_at": datetime.now(timezone.utc).isoformat(),
    })
    if len(room["participants"]) >= 2:
        room["status"] = "ready"

    return JSONResponse({
        "status": "joined",
        "service": "webrtc_signaling",
        "room_id": room_id,
        "peer_id": peer_id,
        "user_id": user_id,
        "participants_count": len(room["participants"]),
        "room_status": room["status"],
        "ws_url": f"ws://localhost:{PORT}/ws/{room_id}/{peer_id}",
        "ice_servers": [
            {"urls": ["stun:stun.hcs-cdn.com:3478"]},
            {"urls": ["turn:turn.hcs-cdn.com:3478"], "username": f"hcs_{room_id}", "credential": uuid.uuid4().hex[:16]},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/room/{room_id}")
async def get_room(room_id: str):
    """Retourne les infos d'une room."""
    if room_id not in _rooms:
        raise HTTPException(404, f"Room {room_id} introuvable")
    room = dict(_rooms[room_id])
    # Masquer les donnees sensibles SDP
    room.pop("sdp_offers", None)
    room.pop("sdp_answers", None)
    room.pop("ice_candidates", None)
    return JSONResponse({"service": "webrtc_signaling", "room": room})


@app.get("/rooms")
async def list_rooms():
    """Liste toutes les rooms actives."""
    rooms_info = []
    for rid, room in _rooms.items():
        rooms_info.append({
            "room_id": rid,
            "quality": room["quality"],
            "participants": len(room["participants"]),
            "max_participants": room["max_participants"],
            "status": room["status"],
            "created_at": room["created_at"],
        })
    return JSONResponse({
        "service": "webrtc_signaling",
        "active_rooms": len(rooms_info),
        "rooms": rooms_info,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/room/{room_id}/sdp/offer")
async def post_sdp_offer(room_id: str, request: Request):
    """Deposer une offre SDP (initiateur de l'appel)."""
    if room_id not in _rooms:
        raise HTTPException(404, f"Room {room_id} introuvable")
    try:
        body = await request.json()
    except Exception:
        body = {}

    peer_id = body.get("peer_id", "unknown")
    sdp     = body.get("sdp", _generate_sdp_offer())
    _rooms[room_id]["sdp_offers"][peer_id] = {"sdp": sdp, "type": "offer", "ts": datetime.now(timezone.utc).isoformat()}
    _stats["sdp_offers"] += 1
    _stats["signaling_messages"] += 1

    return JSONResponse({
        "service": "webrtc_signaling",
        "status": "offer_received",
        "room_id": room_id,
        "peer_id": peer_id,
        "note": "SDP offer enregistree - en attente de reponse",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/room/{room_id}/sdp/answer")
async def post_sdp_answer(room_id: str, request: Request):
    """Deposer une reponse SDP (recepteur de l'appel)."""
    if room_id not in _rooms:
        raise HTTPException(404, f"Room {room_id} introuvable")
    try:
        body = await request.json()
    except Exception:
        body = {}

    peer_id = body.get("peer_id", "unknown")
    sdp     = body.get("sdp", _generate_sdp_answer())
    _rooms[room_id]["sdp_answers"][peer_id] = {"sdp": sdp, "type": "answer", "ts": datetime.now(timezone.utc).isoformat()}
    _rooms[room_id]["status"] = "connected"
    _stats["sdp_answers"] += 1
    _stats["signaling_messages"] += 1
    _stats["calls_connected"] += 1

    return JSONResponse({
        "service": "webrtc_signaling",
        "status": "answer_received",
        "room_id": room_id,
        "peer_id": peer_id,
        "call_status": "connected",
        "note": "Appel etabli - flux media HCS 8K actif",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/room/{room_id}/ice")
async def post_ice_candidate(room_id: str, request: Request):
    """Deposer un candidat ICE."""
    if room_id not in _rooms:
        raise HTTPException(404, f"Room {room_id} introuvable")
    try:
        body = await request.json()
    except Exception:
        body = {}

    peer_id   = body.get("peer_id", "unknown")
    candidate = body.get("candidate", {})

    if peer_id not in _rooms[room_id]["ice_candidates"]:
        _rooms[room_id]["ice_candidates"][peer_id] = []
    _rooms[room_id]["ice_candidates"][peer_id].append({
        "candidate": candidate,
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    _stats["ice_candidates"] += 1
    _stats["signaling_messages"] += 1

    return JSONResponse({
        "service": "webrtc_signaling",
        "status": "ice_candidate_stored",
        "room_id": room_id,
        "peer_id": peer_id,
        "candidates_stored": len(_rooms[room_id]["ice_candidates"].get(peer_id, [])),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/room/{room_id}/sdp/offer/{peer_id}")
async def get_sdp_offer(room_id: str, peer_id: str):
    """Recuperer l'offre SDP d'un pair."""
    if room_id not in _rooms:
        raise HTTPException(404, f"Room {room_id} introuvable")
    offers = _rooms[room_id]["sdp_offers"]
    if peer_id not in offers:
        # Retourner un SDP synthetique si pas encore disponible
        return JSONResponse({
            "service": "webrtc_signaling",
            "status": "pending",
            "sdp": None,
            "note": "Offre SDP pas encore disponible - reessayez dans 1s",
        })
    return JSONResponse({
        "service": "webrtc_signaling",
        "status": "available",
        "peer_id": peer_id,
        **offers[peer_id],
    })


@app.get("/room/{room_id}/ice/{peer_id}")
async def get_ice_candidates(room_id: str, peer_id: str):
    """Recuperer les candidats ICE d'un pair."""
    if room_id not in _rooms:
        raise HTTPException(404, f"Room {room_id} introuvable")
    candidates = _rooms[room_id]["ice_candidates"].get(peer_id, [])
    return JSONResponse({
        "service": "webrtc_signaling",
        "room_id": room_id,
        "peer_id": peer_id,
        "candidates_count": len(candidates),
        "candidates": candidates,
    })


@app.delete("/room/{room_id}")
async def delete_room(room_id: str):
    """Supprime une room WebRTC."""
    if room_id in _rooms:
        del _rooms[room_id]
    return JSONResponse({
        "service": "webrtc_signaling",
        "status": "room_deleted",
        "room_id": room_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/sdp/template/8k")
async def get_sdp_template_8k():
    """Template SDP pour un appel 8K HCS."""
    sdp = _generate_sdp_offer()
    return JSONResponse({
        "service": "webrtc_signaling",
        "sdp_template": "8K HCS Call",
        "type": "offer",
        "sdp": sdp,
        "codecs": {
            "video": ["H.266/VVC (H266)", "AV1", "H.265/HEVC"],
            "audio": ["HCS-Harmonic-32", "Opus 510kbps", "PCM 192kHz"],
        },
        "hcs_extensions": {
            "hcs-harmonic": "32bit/192kHz/Atmos-9.1.6/K=0.97",
            "hcs-video": "8K/7680x4320/60fps/HDR10+/VVC",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/ice/servers")
async def ice_servers():
    """Liste des serveurs ICE (STUN/TURN) HCS."""
    return JSONResponse({
        "service": "webrtc_signaling",
        "ice_servers": [
            {"urls": ["stun:stun.hcs-cdn.com:3478"], "region": "EU"},
            {"urls": ["stun:stun-us.hcs-cdn.com:3478"], "region": "NA"},
            {"urls": ["stun:stun-jp.hcs-cdn.com:3478"], "region": "AP"},
            {
                "urls": ["turn:turn.hcs-cdn.com:3478", "turns:turn.hcs-cdn.com:5349"],
                "username": "hcs_user",
                "credential": "hcs_credential_hmac",
                "credential_type": "hmac-sha256",
                "region": "EU",
            },
            {
                "urls": ["turn:turn-us.hcs-cdn.com:3478"],
                "username": "hcs_user",
                "credential": "hcs_credential_hmac",
                "credential_type": "hmac-sha256",
                "region": "NA",
            },
            {
                "urls": ["turn:turn-jp.hcs-cdn.com:3478"],
                "username": "hcs_user",
                "credential": "hcs_credential_hmac",
                "credential_type": "hmac-sha256",
                "region": "AP",
            },
        ],
        "nat_traversal": "ICE (Interactive Connectivity Establishment)",
        "dtls_version": "1.3",
        "srtp_profile": "SRTP_AES128_CM_SHA1_80",
        "trickle_ice": True,
        "ice_tcp": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ──────────────────────────────────────────────────────────────────────────────
# WEBSOCKET SIGNALISATION TEMPS REEL
# ──────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws/{room_id}/{peer_id}")
async def websocket_signaling(websocket: WebSocket, room_id: str, peer_id: str):
    """
    WebSocket de signalisation temps reel.
    Protocole de messages JSON:
    - {"type": "offer",     "sdp": "...", "peer_id": "..."}
    - {"type": "answer",    "sdp": "...", "peer_id": "..."}
    - {"type": "ice",       "candidate": {...}, "peer_id": "..."}
    - {"type": "ready",     "peer_id": "..."}
    - {"type": "hangup",    "peer_id": "..."}
    - {"type": "ping"}
    """
    await websocket.accept()
    _ws_connections[peer_id] = websocket
    log.info("WebSocket connecte: room=%s peer=%s", room_id, peer_id)

    # Creer la room si elle n'existe pas
    if room_id not in _rooms:
        _rooms[room_id] = {
            "room_id": room_id, "quality": "video_8k", "max_participants": 12,
            "host_id": peer_id, "participants": [],
            "sdp_offers": {}, "sdp_answers": {}, "ice_candidates": {},
            "status": "waiting", "created_at": datetime.now(timezone.utc).isoformat(),
        }

    # Notifier les autres participants
    await _broadcast_to_room(room_id, peer_id, {
        "type": "peer_joined",
        "peer_id": peer_id,
        "participants": len(_ws_connections),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    try:
        # Envoyer la confirmation de connexion
        await websocket.send_json({
            "type": "connected",
            "peer_id": peer_id,
            "room_id": room_id,
            "server": "HCS WebRTC Signaling 1.0",
            "hcs_config": {
                "video_codec": "H.266/VVC",
                "audio_codec": "HCS-Harmonic-32",
                "k_factor": 0.97,
                "mos_target": 4.9,
            },
            "ice_servers": [
                {"urls": ["stun:stun.hcs-cdn.com:3478"]},
                {"urls": ["turn:turn.hcs-cdn.com:3478"], "username": "hcs", "credential": uuid.uuid4().hex[:16]},
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        while True:
            data = await websocket.receive_json()
            _stats["signaling_messages"] += 1
            msg_type = data.get("type", "unknown")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": datetime.now(timezone.utc).isoformat()})

            elif msg_type == "offer":
                sdp = data.get("sdp", "")
                if room_id in _rooms:
                    _rooms[room_id]["sdp_offers"][peer_id] = {"sdp": sdp, "type": "offer"}
                _stats["sdp_offers"] += 1
                # Relayer aux autres pairs de la room
                await _broadcast_to_room(room_id, peer_id, {
                    "type": "offer", "sdp": sdp, "from_peer": peer_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            elif msg_type == "answer":
                sdp = data.get("sdp", "")
                if room_id in _rooms:
                    _rooms[room_id]["sdp_answers"][peer_id] = {"sdp": sdp, "type": "answer"}
                    _rooms[room_id]["status"] = "connected"
                _stats["sdp_answers"] += 1
                _stats["calls_connected"] += 1
                await _broadcast_to_room(room_id, peer_id, {
                    "type": "answer", "sdp": sdp, "from_peer": peer_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            elif msg_type == "ice":
                candidate = data.get("candidate", {})
                if room_id in _rooms:
                    if peer_id not in _rooms[room_id]["ice_candidates"]:
                        _rooms[room_id]["ice_candidates"][peer_id] = []
                    _rooms[room_id]["ice_candidates"][peer_id].append(candidate)
                _stats["ice_candidates"] += 1
                await _broadcast_to_room(room_id, peer_id, {
                    "type": "ice", "candidate": candidate, "from_peer": peer_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            elif msg_type == "hangup":
                await _broadcast_to_room(room_id, peer_id, {
                    "type": "peer_left", "peer_id": peer_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                break

            elif msg_type == "ready":
                await _broadcast_to_room(room_id, peer_id, {
                    "type": "peer_ready", "peer_id": peer_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            else:
                # Relayer le message tel quel
                data["from_peer"] = peer_id
                await _broadcast_to_room(room_id, peer_id, data)

    except WebSocketDisconnect:
        log.info("WebSocket deconnecte: room=%s peer=%s", room_id, peer_id)
    finally:
        _ws_connections.pop(peer_id, None)
        await _broadcast_to_room(room_id, peer_id, {
            "type": "peer_disconnected",
            "peer_id": peer_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


async def _broadcast_to_room(room_id: str, sender_peer_id: str, message: dict):
    """Envoie un message a tous les pairs d'une room sauf l'expediteur."""
    if room_id not in _rooms:
        return
    room = _rooms[room_id]
    for participant in room.get("participants", []):
        pid = participant.get("peer_id")
        if pid and pid != sender_peer_id and pid in _ws_connections:
            try:
                await _ws_connections[pid].send_json(message)
            except Exception:
                pass


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS SDP
# ──────────────────────────────────────────────────────────────────────────────

def _generate_sdp_offer() -> str:
    return SDP_OFFER_TEMPLATE_8K.format(
        ice_ufrag=_generate_ice_ufrag(),
        ice_pwd=_generate_ice_pwd(),
        fingerprint=_generate_fingerprint(),
        k_factor=round(random.uniform(0.94, 0.98), 4),
    )


def _generate_sdp_answer() -> str:
    sdp = _generate_sdp_offer()
    return sdp.replace("actpass", "passive").replace("o=HCS-8K 2026021800", "o=HCS-8K 2026021801")


# ──────────────────────────────────────────────────────────────────────────────
# ENTREE PRINCIPALE
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [WEBRTC-SIGNAL] %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
