"""
HCS MiniCDN - Service Bouquet Football 8K (port 9017)
=====================================================
Bouquet de chaines football en 8K Ultra HD
Grands clubs europeens + UEFA Champions League
Codec: H.266/VVC | HLS/DASH | HDR10+/DolbyVision | Dolby Atmos 9.1.6
HCS preset: cinema (ratio ~3:1)
"""

import os, sys, json, logging, random
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from services.service_base import HCSServiceBase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "config", "services.json"), encoding="utf-8") as f:
    CDN_CONFIG = json.load(f)

service_config = CDN_CONFIG["services"]["football_8k_bouquet"]
PORT = int(os.getenv("HCS_SERVICE_PORT", service_config["port"]))

svc = HCSServiceBase(service_config, PORT)
app = svc.app

# ─── Donnees du bouquet ───────────────────────────────────────────────────────

CLUBS_CHANNELS = [
    {
        "id": "fc-real-madrid",
        "name": "Real Madrid TV 8K",
        "club": "Real Madrid CF",
        "country": "Espagne",
        "league": "La Liga",
        "stadium": "Santiago Bernabeu",
        "stadium_capacity": 81044,
        "colors": {"primary": "#FFFFFF", "secondary": "#FFD700"},
        "logo_emoji": "⚽🏆",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "Real Madrid vs Atletico Madrid - LaLiga 2025/26",
        "epg_next": "Highlights - El Clasico Special",
        "viewers_live": random.randint(2000000, 5000000),
        "status": "live",
        "ucl_titles": 15,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/real-madrid/live.m3u8",
    },
    {
        "id": "fc-barcelona",
        "name": "Barca TV 8K",
        "club": "FC Barcelona",
        "country": "Espagne",
        "league": "La Liga",
        "stadium": "Estadi Olimpic Lluis Companys",
        "stadium_capacity": 54367,
        "colors": {"primary": "#004D98", "secondary": "#A50044"},
        "logo_emoji": "⚽🔵🔴",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "FC Barcelona vs Girona - LaLiga 2025/26",
        "epg_next": "FC Barcelona TV - Documentaire Xavi Era",
        "viewers_live": random.randint(1500000, 4000000),
        "status": "live",
        "ucl_titles": 5,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/barcelona/live.m3u8",
    },
    {
        "id": "fc-psg",
        "name": "PSG TV 8K",
        "club": "Paris Saint-Germain FC",
        "country": "France",
        "league": "Ligue 1",
        "stadium": "Parc des Princes",
        "stadium_capacity": 47929,
        "colors": {"primary": "#003087", "secondary": "#DA291C"},
        "logo_emoji": "⚽🗼",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "PSG vs Marseille - Le Classique 8K",
        "epg_next": "PSG Academie - Les futures stars",
        "viewers_live": random.randint(1000000, 3000000),
        "status": "live",
        "ucl_titles": 0,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/psg/live.m3u8",
    },
    {
        "id": "fc-man-city",
        "name": "CITY TV 8K",
        "club": "Manchester City FC",
        "country": "Angleterre",
        "league": "Premier League",
        "stadium": "Etihad Stadium",
        "stadium_capacity": 53400,
        "colors": {"primary": "#6CABDD", "secondary": "#FFFFFF"},
        "logo_emoji": "⚽🔵",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "Man City vs Arsenal - Premier League Matchday 28",
        "epg_next": "City TV - Treble Anniversary Special",
        "viewers_live": random.randint(1500000, 3500000),
        "status": "live",
        "ucl_titles": 1,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/man-city/live.m3u8",
    },
    {
        "id": "fc-man-united",
        "name": "MUTV 8K",
        "club": "Manchester United FC",
        "country": "Angleterre",
        "league": "Premier League",
        "stadium": "Old Trafford",
        "stadium_capacity": 74310,
        "colors": {"primary": "#DA291C", "secondary": "#FBE122"},
        "logo_emoji": "⚽🔴",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "Man United vs Liverpool - Premier League 8K",
        "epg_next": "MUTV Classic - Treble 1999",
        "viewers_live": random.randint(1200000, 3000000),
        "status": "live",
        "ucl_titles": 3,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/man-united/live.m3u8",
    },
    {
        "id": "fc-bayern",
        "name": "FC Bayern TV 8K",
        "club": "FC Bayern Munchen",
        "country": "Allemagne",
        "league": "Bundesliga",
        "stadium": "Allianz Arena",
        "stadium_capacity": 75024,
        "colors": {"primary": "#DC052D", "secondary": "#0066B2"},
        "logo_emoji": "⚽🔴⚪",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "Bayern vs Borussia Dortmund - Der Klassiker 8K",
        "epg_next": "Bayern TV - Geschichte des FC Bayern",
        "viewers_live": random.randint(1500000, 4000000),
        "status": "live",
        "ucl_titles": 6,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/bayern/live.m3u8",
    },
    {
        "id": "fc-juventus",
        "name": "Juventus TV 8K",
        "club": "Juventus FC",
        "country": "Italie",
        "league": "Serie A",
        "stadium": "Allianz Stadium",
        "stadium_capacity": 41507,
        "colors": {"primary": "#000000", "secondary": "#FFFFFF"},
        "logo_emoji": "⚽⚫⚪",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "Juventus vs Inter Milan - Derby d'Italia 8K",
        "epg_next": "Juve TV - 9 Scudetti Consecutifs",
        "viewers_live": random.randint(800000, 2500000),
        "status": "live",
        "ucl_titles": 2,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/juventus/live.m3u8",
    },
    {
        "id": "fc-ac-milan",
        "name": "Milan TV 8K",
        "club": "AC Milan",
        "country": "Italie",
        "league": "Serie A",
        "stadium": "San Siro",
        "stadium_capacity": 75923,
        "colors": {"primary": "#FB090B", "secondary": "#000000"},
        "logo_emoji": "⚽🔴⚫",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "AC Milan vs AS Roma - Serie A 8K",
        "epg_next": "Milan Channel - Legends of San Siro",
        "viewers_live": random.randint(700000, 2000000),
        "status": "live",
        "ucl_titles": 7,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/ac-milan/live.m3u8",
    },
    {
        "id": "fc-chelsea",
        "name": "Chelsea TV 8K",
        "club": "Chelsea FC",
        "country": "Angleterre",
        "league": "Premier League",
        "stadium": "Stamford Bridge",
        "stadium_capacity": 40341,
        "colors": {"primary": "#034694", "secondary": "#FFFFFF"},
        "logo_emoji": "⚽🔵🦁",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "Chelsea vs Tottenham - Premier League 8K",
        "epg_next": "Chelsea TV - Champions 2021 Documentary",
        "viewers_live": random.randint(600000, 1800000),
        "status": "live",
        "ucl_titles": 2,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/chelsea/live.m3u8",
    },
    {
        "id": "fc-liverpool",
        "name": "LFC TV 8K",
        "club": "Liverpool FC",
        "country": "Angleterre",
        "league": "Premier League",
        "stadium": "Anfield",
        "stadium_capacity": 61276,
        "colors": {"primary": "#C8102E", "secondary": "#F6EB61"},
        "logo_emoji": "⚽🔴🦅",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "Liverpool vs Everton - The Merseyside Derby 8K",
        "epg_next": "LFC TV - Istanbul 2005 Revisited",
        "viewers_live": random.randint(1000000, 3000000),
        "status": "live",
        "ucl_titles": 6,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/liverpool/live.m3u8",
    },
    {
        "id": "fc-atletico",
        "name": "Atletico TV 8K",
        "club": "Atletico de Madrid",
        "country": "Espagne",
        "league": "La Liga",
        "stadium": "Civitas Metropolitano",
        "stadium_capacity": 68456,
        "colors": {"primary": "#CE3524", "secondary": "#272E61"},
        "logo_emoji": "⚽🔴⚪",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "Atletico Madrid vs Sevilla - La Liga 8K",
        "epg_next": "Atletico TV - Colchoneros Story",
        "viewers_live": random.randint(500000, 1500000),
        "status": "live",
        "ucl_titles": 0,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/atletico/live.m3u8",
    },
    {
        "id": "fc-dortmund",
        "name": "BVB TV 8K",
        "club": "Borussia Dortmund",
        "country": "Allemagne",
        "league": "Bundesliga",
        "stadium": "Signal Iduna Park",
        "stadium_capacity": 81365,
        "colors": {"primary": "#FDE100", "secondary": "#000000"},
        "logo_emoji": "⚽🟡⚫",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "Borussia Dortmund vs Schalke - Revierderby 8K",
        "epg_next": "BVB Total - Gelbe Wand Story",
        "viewers_live": random.randint(600000, 1800000),
        "status": "live",
        "ucl_titles": 1,
        "genre": "Football Club",
        "port_sub": 9017,
        "hls_url": "http://localhost:9017/streams/dortmund/live.m3u8",
    },
]

UEFA_CHANNELS = [
    {
        "id": "ucl-live-8k",
        "name": "UEFA Champions League 8K",
        "competition": "UEFA Champions League",
        "season": "2025/2026",
        "phase": "Quarts de finale",
        "colors": {"primary": "#003087", "secondary": "#FFD700"},
        "logo_emoji": "🏆⭐",
        "bitrate_mbps": 120,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "LIVE: Real Madrid vs Bayern Munich - UCL QF 1st leg",
        "epg_next": "LIVE: Manchester City vs PSG - UCL QF 1st leg",
        "viewers_live": random.randint(15000000, 30000000),
        "status": "live",
        "cameras": [
            "Camera principale", "Camera but N1", "Camera but N2",
            "Camera aerienne drone", "Camera ralenti 4K", "Vue tactique",
            "Camera joueur (track-cam)", "Camera stade 360"
        ],
        "genre": "UEFA",
        "hls_url": "http://localhost:9017/streams/ucl/live.m3u8",
        "multi_cam": True,
    },
    {
        "id": "uel-live-8k",
        "name": "UEFA Europa League 8K",
        "competition": "UEFA Europa League",
        "season": "2025/2026",
        "phase": "Demi-finale",
        "colors": {"primary": "#F5A623", "secondary": "#000000"},
        "logo_emoji": "🏆🟠",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "HDR10+",
        "audio": "Dolby Atmos 7.1",
        "epg_now": "LIVE: Juventus vs Atletico Madrid - UEL SF",
        "epg_next": "LIVE: Chelsea vs Lyon - UEL SF",
        "viewers_live": random.randint(5000000, 12000000),
        "status": "live",
        "cameras": [
            "Camera principale", "Camera but N1", "Camera but N2",
            "Camera aerienne", "Camera ralenti", "Vue tactique"
        ],
        "genre": "UEFA",
        "hls_url": "http://localhost:9017/streams/uel/live.m3u8",
        "multi_cam": True,
    },
    {
        "id": "uecl-live-8k",
        "name": "UEFA Conference League 8K",
        "competition": "UEFA Conference League",
        "season": "2025/2026",
        "phase": "Quarts de finale",
        "colors": {"primary": "#00B140", "secondary": "#FFFFFF"},
        "logo_emoji": "🏆🟢",
        "bitrate_mbps": 80,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "HDR10",
        "audio": "Dolby Atmos 5.1",
        "epg_now": "LIVE: Fiorentina vs Slavia Praha - UECL QF",
        "epg_next": "LIVE: Nice vs Legia Warsaw - UECL QF",
        "viewers_live": random.randint(1000000, 4000000),
        "status": "live",
        "cameras": [
            "Camera principale", "Camera but N1", "Camera but N2",
            "Camera aerienne", "Camera ralenti"
        ],
        "genre": "UEFA",
        "hls_url": "http://localhost:9017/streams/uecl/live.m3u8",
        "multi_cam": True,
    },
    {
        "id": "ucl-highlights",
        "name": "UCL Highlights 8K",
        "competition": "UEFA Champions League Highlights",
        "season": "2025/2026",
        "phase": "Replay & Highlights",
        "colors": {"primary": "#003087", "secondary": "#C0C0C0"},
        "logo_emoji": "🎬🏆",
        "bitrate_mbps": 100,
        "resolution": "7680x4320",
        "framerate": 60,
        "hdr": "Dolby Vision",
        "audio": "Dolby Atmos 9.1.6",
        "epg_now": "UCL Best Goals Saison 2025/26 - 8K Remastered",
        "epg_next": "UCL Classique - Finale 2024 Replay 8K",
        "viewers_live": random.randint(500000, 2000000),
        "status": "replay",
        "genre": "UEFA",
        "hls_url": "http://localhost:9017/streams/ucl-highlights/live.m3u8",
        "multi_cam": False,
    },
    {
        "id": "ucl-final-8k",
        "name": "Finale UCL 8K LIVE",
        "competition": "UEFA Champions League Final",
        "season": "2025/2026",
        "phase": "FINALE - Munich 2026",
        "stadium": "Allianz Arena, Munich",
        "date_finale": "30 Mai 2026",
        "colors": {"primary": "#FFD700", "secondary": "#003087"},
        "logo_emoji": "🏆🌟",
        "bitrate_mbps": 150,
        "resolution": "7680x4320",
        "framerate": 120,
        "hdr": "Dolby Vision IQ",
        "audio": "Dolby Atmos 9.1.6 Immersif",
        "epg_now": "FINAL UCL 2026: TBD vs TBD - EN DIRECT",
        "epg_next": "Ceremonie de remise du trophee",
        "viewers_live": 0,
        "status": "scheduled",
        "cameras": [
            "Camera principale 8K", "18 cameras multi-angles",
            "Drone 8K", "Camera loges VIP", "Camera sur gazon",
            "Camera but ultra-lente 8K", "Vue satellite", "360 VR"
        ],
        "genre": "UEFA Final",
        "hls_url": "http://localhost:9017/streams/ucl-final/live.m3u8",
        "multi_cam": True,
        "special": True,
    },
]

ALL_CHANNELS = CLUBS_CHANNELS + UEFA_CHANNELS


# ─── Routes API ──────────────────────────────────────────────────────────────

@app.get("/channels")
async def get_all_channels():
    """Liste de toutes les chaines du bouquet football 8K."""
    return JSONResponse(content={
        "service": "football_8k_bouquet",
        "bouquet_name": "HCS Football 8K - Le Bouquet des Champions",
        "total_channels": len(ALL_CHANNELS),
        "clubs_channels": len(CLUBS_CHANNELS),
        "uefa_channels": len(UEFA_CHANNELS),
        "resolution": "7680x4320 (8K UHD)",
        "framerate": "60fps / 120fps Finale",
        "hdr": "Dolby Vision / HDR10+ / HDR10",
        "codec": "H.266/VVC",
        "audio": "Dolby Atmos 9.1.6",
        "hcs_compression_ratio": 3,
        "bandwidth_required_mbps": 100,
        "drm": "Widevine L1 + PlayReady 4.0 + FairPlay",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channels": ALL_CHANNELS,
    })


@app.get("/channels/clubs")
async def get_club_channels():
    """Chaines des grands clubs uniquement."""
    return JSONResponse(content={
        "service": "football_8k_bouquet",
        "category": "Grands Clubs Europeens",
        "count": len(CLUBS_CHANNELS),
        "channels": CLUBS_CHANNELS,
    })


@app.get("/channels/uefa")
async def get_uefa_channels():
    """Chaines UEFA (UCL, UEL, UECL, Finale)."""
    return JSONResponse(content={
        "service": "football_8k_bouquet",
        "category": "UEFA - Competitions Europeennes",
        "count": len(UEFA_CHANNELS),
        "channels": UEFA_CHANNELS,
    })


@app.get("/channels/{channel_id}")
async def get_channel(channel_id: str):
    """Detail d'une chaine."""
    channel = next((c for c in ALL_CHANNELS if c["id"] == channel_id), None)
    if not channel:
        return JSONResponse(status_code=404, content={"error": f"Chaine '{channel_id}' introuvable"})
    # Mise a jour dynamique des viewers
    channel = dict(channel)
    if channel["status"] == "live":
        channel["viewers_live"] = random.randint(500000, 30000000)
    return JSONResponse(content=channel)


@app.get("/schedule")
async def get_schedule():
    """Programme des matchs en direct et a venir."""
    schedule = {
        "date": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        "live_now": [
            {
                "time": "20:45",
                "match": "Real Madrid vs Bayern Munich",
                "competition": "UEFA Champions League - QF 1st leg",
                "channel": "ucl-live-8k",
                "stadium": "Santiago Bernabeu",
                "viewers": random.randint(20000000, 35000000),
            },
            {
                "time": "20:45",
                "match": "Manchester City vs PSG",
                "competition": "UEFA Champions League - QF 1st leg",
                "channel": "ucl-live-8k",
                "stadium": "Etihad Stadium",
                "viewers": random.randint(15000000, 25000000),
            },
            {
                "time": "21:00",
                "match": "PSG vs Marseille",
                "competition": "Ligue 1 - Le Classique",
                "channel": "fc-psg",
                "stadium": "Parc des Princes",
                "viewers": random.randint(3000000, 8000000),
            },
        ],
        "upcoming_today": [
            {
                "time": "22:30",
                "match": "Barcelona vs Atletico Madrid",
                "competition": "La Liga - Matchday 30",
                "channel": "fc-barcelona",
                "stadium": "Estadi Olimpic",
            },
        ],
        "tomorrow": [
            {
                "time": "20:45",
                "match": "Juventus vs AC Milan",
                "competition": "Serie A - Derby della Mole vs Derby d'Italia",
                "channel": "fc-juventus",
                "stadium": "Allianz Stadium",
            },
            {
                "time": "20:45",
                "match": "Bayern Munich vs Borussia Dortmund",
                "competition": "Bundesliga - Der Klassiker",
                "channel": "fc-bayern",
                "stadium": "Allianz Arena",
            },
        ],
    }
    return JSONResponse(content=schedule)


@app.get("/stats")
async def get_bouquet_stats():
    """Statistiques globales du bouquet football 8K."""
    total_viewers = sum(
        random.randint(500000, 5000000) for _ in ALL_CHANNELS
    )
    return JSONResponse(content={
        "service": "football_8k_bouquet",
        "stats": {
            "total_channels": len(ALL_CHANNELS),
            "live_channels": len([c for c in ALL_CHANNELS if c["status"] == "live"]),
            "total_viewers_now": total_viewers,
            "bandwidth_total_gbps": round(len(ALL_CHANNELS) * 100 / 1000, 1),
            "hcs_bytes_saved_vs_raw_pct": 96.7,
            "psnr_db": round(random.uniform(44, 48), 1),
            "ssim": round(random.uniform(0.975, 0.999), 3),
            "vmaf": round(random.uniform(95, 99), 1),
            "latency_ms": random.randint(800, 1200),
            "bitrate_avg_mbps": 100,
            "codec": "H.266/VVC",
            "hcs_compression_active": True,
            "edge_nodes_serving": ["Paris", "London", "Frankfurt", "Madrid", "Milan", "Munich"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    })


@app.get("/streams/{club}/live.m3u8")
async def get_stream_url(club: str):
    """Simulation endpoint de flux HLS M3U8."""
    return JSONResponse(content={
        "club": club,
        "stream_type": "HLS",
        "resolution": "7680x4320",
        "framerate": 60,
        "codec": "H.266/VVC",
        "bitrate_mbps": 100,
        "hcs_compressed": True,
        "segments": [
            f"http://localhost:9017/segments/{club}/seg_{i:04d}.ts"
            for i in range(1, 7)
        ],
        "note": "Flux 8K HCS-VVC - Necessite decodeur HCS compatible",
    })


@app.get("/quality/test")
async def quality_test():
    """Test qualite en temps reel du bouquet football 8K."""
    return JSONResponse(content={
        "service": "football_8k_bouquet",
        "resolution": "7680x4320",
        "psnr_db": round(random.uniform(44, 48), 1),
        "ssim": round(random.uniform(0.975, 0.999), 3),
        "vmaf": round(random.uniform(95, 99), 1),
        "bitrate_actual_mbps": round(random.uniform(95, 115), 1),
        "color_depth": "10-bit",
        "hdr_mode": "Dolby Vision IQ",
        "frame_rate": "60fps",
        "codec": "H.266/VVC",
        "audio": "Dolby Atmos 9.1.6",
        "latency_ms": random.randint(800, 1100),
        "hcs_compression_active": True,
        "hcs_ratio": 3.0,
        "bytes_saved_vs_raw": "96.7%",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/requirements")
async def get_requirements():
    """Prerequis pour recevoir le bouquet football 8K."""
    return JSONResponse(content={
        "service": "football_8k_bouquet",
        "display": "TV 8K (7680x4320) avec HDMI 2.1",
        "bandwidth": "100 Mbps minimum, 200 Mbps recommande (fibre)",
        "decoder": "Decodeur HCS VVC 8K compatible (chip 2024+)",
        "drm": "Widevine L1 + PlayReady 4.0 + FairPlay",
        "audio_system": "Dolby Atmos (9.1.6 recommande)",
        "subscription": "Bouquet Football 8K Premium - 29.99 EUR/mois",
        "compatible_devices": [
            "Samsung Neo QLED 8K 2024/2025",
            "LG OLED 8K 2024/2025",
            "Sony BRAVIA 8K 2024/2025",
            "HCS SmartTV Box 8K Pro",
            "Apple TV 8K (2025)",
            "HCS Football STB 8K",
        ],
        "minimum_network": "100 Mbps (fibre optique recommandee)",
        "hcs_technology": "HCS Harmonic Compression System - H.266/VVC optimise",
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def football_dashboard():
    """Dashboard HTML du bouquet football 8K."""
    try:
        dashboard_path = os.path.join(BASE_DIR, "frontend", "football_bouquet.html")
        with open(dashboard_path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard football_bouquet.html introuvable</h1>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [FOOTBALL-8K] %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
