"""Script generateur - cree tous les fichiers radio broadcast CDN"""
import json, os

# =============================================================================
# 1. COMPLÉTER svc_radio_broadcast.py
# =============================================================================
radio_svc = r'''import sys, os, json, random, logging
from datetime import datetime, timezone
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from services.service_base import HCSServiceBase

try:
    from core.hcs_radio_encoder import get_radio_encoder, OUTPUT_FORMATS
    _encoder = get_radio_encoder()
    ENCODER_OK = True
except ImportError as e:
    ENCODER_OK = False
    _encoder = None
    OUTPUT_FORMATS = {}
    logging.getLogger("HCS-Radio").warning("Encodeur non dispo: %s", e)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "config", "services.json")) as f:
    CDN_CONFIG = json.load(f)
service_config = CDN_CONFIG["services"]["radio_broadcast"]
PORT = int(os.getenv("HCS_SERVICE_PORT", service_config["port"]))

# Catalogue mondial de 40 stations
STATIONS = [
  {"id":"bbc_r1","name":"BBC Radio 1","country":"UK","genre":"Pop/Dance","src_fmt":"aac_128","bitrate":128,"language":"en","lat":51.5,"lon":-0.1,"color":"#FF6B6B","stream_url":"https://stream.live.vc.bbcmedia.co.uk/bbc_radio_one"},
  {"id":"bbc_r3","name":"BBC Radio 3","country":"UK","genre":"Classical","src_fmt":"aac_320","bitrate":320,"language":"en","lat":51.5,"lon":-0.1,"color":"#4ECDC4","stream_url":"https://stream.live.vc.bbcmedia.co.uk/bbc_radio_three"},
  {"id":"france_musique","name":"France Musique","country":"FR","genre":"Classical/Jazz","src_fmt":"aac_320","bitrate":320,"language":"fr","lat":48.8,"lon":2.3,"color":"#45B7D1","stream_url":"https://icecast.radiofrance.fr/francemusique-hifi.aac"},
  {"id":"france_inter","name":"France Inter","country":"FR","genre":"News/Culture","src_fmt":"aac_192","bitrate":192,"language":"fr","lat":48.8,"lon":2.3,"color":"#96CEB4","stream_url":"https://icecast.radiofrance.fr/franceinter-hifi.aac"},
  {"id":"france_culture","name":"France Culture","country":"FR","genre":"Culture/Talk","src_fmt":"aac_192","bitrate":192,"language":"fr","lat":48.8,"lon":2.3,"color":"#FECA57","stream_url":"https://icecast.radiofrance.fr/franceculture-hifi.aac"},
  {"id":"wqxr","name":"WQXR New York","country":"US","genre":"Classical","src_fmt":"mp3_128","bitrate":128,"language":"en","lat":40.7,"lon":-74.0,"color":"#FF9FF3","stream_url":"https://stream.wqxr.org/wqxr"},
  {"id":"wnyc","name":"WNYC New York","country":"US","genre":"Public Radio","src_fmt":"aac_128","bitrate":128,"language":"en","lat":40.7,"lon":-74.0,"color":"#48DBFB","stream_url":"https://fm939.wnyc.org/wnycfm"},
  {"id":"kcrw","name":"KCRW Santa Monica","country":"US","genre":"Indie/World","src_fmt":"mp3_192","bitrate":192,"language":"en","lat":34.0,"lon":-118.4,"color":"#FF6B6B","stream_url":"https://kcrw.streamguys1.com/kcrw_192k_mp3_on_air"},
  {"id":"wfmt","name":"WFMT Chicago","country":"US","genre":"Classical","src_fmt":"mp3_320","bitrate":320,"language":"en","lat":41.8,"lon":-87.6,"color":"#5F27CD","stream_url":"https://stream.wfmt.com/wfmt"},
  {"id":"deutschlandfunk","name":"Deutschlandfunk","country":"DE","genre":"News/Culture","src_fmt":"aac_256","bitrate":256,"language":"de","lat":50.9,"lon":6.9,"color":"#00D2D3","stream_url":"https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3"},
  {"id":"wdr3","name":"WDR 3 Koeln","country":"DE","genre":"Classical","src_fmt":"aac_256","bitrate":256,"language":"de","lat":51.4,"lon":7.0,"color":"#FF9F43","stream_url":"https://wdr-wdr3-live.icecastssl.wdr.de/wdr/wdr3/live/128/stream.mp3"},
  {"id":"radio_swiss_classic","name":"Radio Swiss Classic","country":"CH","genre":"Classical","src_fmt":"flac","bitrate":320,"language":"de","lat":46.8,"lon":7.1,"color":"#C0392B","stream_url":"https://stream.srg-ssr.ch/rsc_de/mp3_128.m3u"},
  {"id":"rai_classica","name":"RAI Radio Classica","country":"IT","genre":"Classical","src_fmt":"aac_128","bitrate":128,"language":"it","lat":41.9,"lon":12.5,"color":"#8E44AD","stream_url":"https://icestreaming.rai.it/13.mp3"},
  {"id":"rtve_clasica","name":"RNE Radio Clasica","country":"ES","genre":"Classical","src_fmt":"aac_192","bitrate":192,"language":"es","lat":40.4,"lon":-3.7,"color":"#E74C3C","stream_url":"https://rne.rtveradio.cires21.com/rne_rc.mp3"},
  {"id":"nrk_p2","name":"NRK P2 Oslo","country":"NO","genre":"Classical/Jazz","src_fmt":"aac_192","bitrate":192,"language":"no","lat":59.9,"lon":10.7,"color":"#3498DB","stream_url":"https://lyd.nrk.no/nrk_radio_p2_aac_h"},
  {"id":"yle_klassinen","name":"YLE Klassinen","country":"FI","genre":"Classical","src_fmt":"aac_192","bitrate":192,"language":"fi","lat":60.2,"lon":24.9,"color":"#2ECC71","stream_url":"https://icecast.yle.fi/radio/yleradio1/aacp/128"},
  {"id":"radio_swiss_jazz","name":"Radio Swiss Jazz","country":"CH","genre":"Jazz","src_fmt":"mp3_320","bitrate":320,"language":"fr","lat":46.8,"lon":7.1,"color":"#F39C12","stream_url":"https://stream.srg-ssr.ch/rsj/mp3_128.m3u"},
  {"id":"jazz24","name":"Jazz24 Seattle","country":"US","genre":"Jazz","src_fmt":"mp3_128","bitrate":128,"language":"en","lat":47.6,"lon":-122.3,"color":"#9B59B6","stream_url":"https://live.wostreaming.net/direct/ppm-jazz24aac-ibc1"},
  {"id":"tsf_jazz","name":"TSF Jazz Paris","country":"FR","genre":"Jazz","src_fmt":"aac_256","bitrate":256,"language":"fr","lat":48.8,"lon":2.3,"color":"#E67E22","stream_url":"https://tsfjazz.ice.infomaniak.ch/tsfjazz-high.mp3"},
  {"id":"nrj","name":"NRJ France","country":"FR","genre":"Pop/Dance","src_fmt":"mp3_128","bitrate":128,"language":"fr","lat":48.8,"lon":2.3,"color":"#E74C3C","stream_url":"https://scdn.nrjaudio.fm/fr/30001/mp3_128.mp3"},
  {"id":"fun_radio","name":"Fun Radio","country":"FR","genre":"Dance/EDM","src_fmt":"aac_128","bitrate":128,"language":"fr","lat":48.8,"lon":2.3,"color":"#1ABC9C","stream_url":"https://streaming.radio.rtl2.fr/funradio-mp3-128"},
  {"id":"rtl2","name":"RTL2","country":"FR","genre":"Rock","src_fmt":"aac_128","bitrate":128,"language":"fr","lat":48.8,"lon":2.3,"color":"#2C3E50","stream_url":"https://streaming.radio.rtl2.fr/rtl2-mp3-128"},
  {"id":"rfi_fr","name":"RFI Francais","country":"FR","genre":"News/International","src_fmt":"aac_128","bitrate":128,"language":"fr","lat":48.8,"lon":2.3,"color":"#16A085","stream_url":"https://rfifr.ice.infomaniak.ch/rfifr-96.mp3"},
  {"id":"dw_radio","name":"DW Radio","country":"DE","genre":"News/International","src_fmt":"aac_128","bitrate":128,"language":"de","lat":50.9,"lon":6.9,"color":"#8E44AD","stream_url":"https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3"},
  {"id":"voice_america","name":"Voice of America","country":"US","genre":"News/International","src_fmt":"mp3_128","bitrate":128,"language":"en","lat":38.9,"lon":-77.0,"color":"#C0392B","stream_url":"https://voa-instream.akamaized.net/voa/audio/english/live"},
  {"id":"nhk_world","name":"NHK World Radio","country":"JP","genre":"News/Culture","src_fmt":"aac_128","bitrate":128,"language":"ja","lat":35.7,"lon":139.7,"color":"#E74C3C","stream_url":"https://nhkworld.webcdn.stream.ne.jp/www11/nhkworld/nhkwradio/master/eng/2/stream.m3u8"},
  {"id":"cbc_r2","name":"CBC Radio 2","country":"CA","genre":"Classical/Jazz","src_fmt":"aac_128","bitrate":128,"language":"en","lat":45.4,"lon":-75.7,"color":"#E74C3C","stream_url":"https://cbcliveradio.cbc.ca/live/cbcr2"},
  {"id":"abc_classic","name":"ABC Classic","country":"AU","genre":"Classical","src_fmt":"aac_128","bitrate":128,"language":"en","lat":-33.9,"lon":151.2,"color":"#3498DB","stream_url":"https://abcradiostreams.akamaized.net/abcrn/live.mp3"},
  {"id":"sabc_radio","name":"SABC Radio","country":"ZA","genre":"Generalist","src_fmt":"mp3_128","bitrate":128,"language":"en","lat":-26.2,"lon":28.0,"color":"#F39C12","stream_url":"https://streams.sabc.co.za/sabc/trufm-aac"},
  {"id":"radio_senegal","name":"Radio Senegal","country":"SN","genre":"Generalist","src_fmt":"mp3_64","bitrate":64,"language":"fr","lat":14.7,"lon":-17.4,"color":"#27AE60","stream_url":"https://stream.zeno.fm/hjrb2fp1zf8uv"},
  {"id":"egyptian_radio","name":"Egyptian Radio","country":"EG","genre":"Classical Arabic","src_fmt":"aac_128","bitrate":128,"language":"ar","lat":30.0,"lon":31.2,"color":"#C0392B","stream_url":"https://stream.ertu.eg/live_programs"},
  {"id":"radio_nigeria","name":"Radio Nigeria","country":"NG","genre":"Generalist","src_fmt":"mp3_64","bitrate":64,"language":"en","lat":6.5,"lon":3.4,"color":"#27AE60","stream_url":"https://streaming.radionigeria.org/rnfm"},
  {"id":"dubai_radio","name":"Dubai Radio","country":"AE","genre":"Arabic/Pop","src_fmt":"aac_128","bitrate":128,"language":"ar","lat":25.2,"lon":55.3,"color":"#F1C40F","stream_url":"https://www.radiotrinity.com/dubai"},
  {"id":"radio_china","name":"China Radio International","country":"CN","genre":"News/Culture","src_fmt":"aac_128","bitrate":128,"language":"zh","lat":39.9,"lon":116.4,"color":"#C0392B","stream_url":"https://rfiristream.akamaized.net/hls/live/683565/rfichinois/index.m3u8"},
  {"id":"kbs_world","name":"KBS World Radio","country":"KR","genre":"News/Culture","src_fmt":"aac_128","bitrate":128,"language":"ko","lat":37.6,"lon":126.9,"color":"#3498DB","stream_url":"https://worldmedia.kbs.co.kr/radio/fm"},
  {"id":"all_india_radio","name":"All India Radio","country":"IN","genre":"Classical/Culture","src_fmt":"aac_128","bitrate":128,"language":"hi","lat":28.6,"lon":77.2,"color":"#F39C12","stream_url":"https://air.pc.cdn.bitgravity.com/air/live/pbaudio001/playlist.m3u8"},
  {"id":"r_nacional_arg","name":"Radio Nacional Argentina","country":"AR","genre":"Generalist","src_fmt":"mp3_128","bitrate":128,"language":"es","lat":-34.6,"lon":-58.4,"color":"#5DADE2","stream_url":"https://playerservices.streamtheworld.com/api/livestream-redirect/LT22_RNAAAM.mp3"},
  {"id":"radiobras","name":"Radio Nacional Brasil","country":"BR","genre":"Generalist","src_fmt":"aac_128","bitrate":128,"language":"pt","lat":-15.8,"lon":-47.9,"color":"#27AE60","stream_url":"https://radioebc.ebc.com.br/radiobras-nacional"},
  {"id":"rtbf_musiq3","name":"RTBF Musiq3","country":"BE","genre":"Classical","src_fmt":"aac_256","bitrate":256,"language":"fr","lat":50.8,"lon":4.3,"color":"#8E44AD","stream_url":"https://radios.rtbf.be/musiq3-256.mp3"},
  {"id":"rts_espace2","name":"RTS Espace 2","country":"CH","genre":"Classical/Culture","src_fmt":"aac_192","bitrate":192,"language":"fr","lat":46.5,"lon":6.6,"color":"#2980B9","stream_url":"https://stream.srg-ssr.ch/drs2/mp3_128.m3u"},
]

NOW_PLAYING = {
    "Classical": ["Beethoven - Symphony No.9 in D minor", "Mozart - Piano Concerto No.21", "Bach - Goldberg Variations BWV 988", "Chopin - Nocturne Op.9 No.2", "Brahms - Symphony No.4", "Debussy - Clair de Lune"],
    "Jazz": ["Miles Davis - Kind of Blue", "John Coltrane - A Love Supreme", "Bill Evans - Waltz for Debby", "Dave Brubeck - Take Five", "Thelonious Monk - Round Midnight"],
    "Pop/Dance": ["Dua Lipa - Levitating", "Coldplay - Yellow", "The Weeknd - Blinding Lights", "Adele - Hello"],
    "Dance/EDM": ["Calvin Harris - Summer", "Avicii - Wake Me Up", "Martin Garrix - Animals"],
    "Rock": ["Pink Floyd - Comfortably Numb", "Led Zeppelin - Stairway to Heaven", "AC/DC - Highway to Hell"],
    "News/Culture": ["Live News Broadcast", "Live Talk Show", "Documentary Feature"],
    "Generalist": ["Live Program", "Local News", "Morning Show"],
}

def _now_playing(genre):
    for k, v in NOW_PLAYING.items():
        if k.lower() in genre.lower():
            return random.choice(v)
    return "Live Broadcast"

svc = HCSServiceBase(service_config, PORT)
app = svc.app

@app.get("/stations")
async def list_stations(
    genre: str = Query(""),
    country: str = Query(""),
    hifi: bool = Query(False),
    search: str = Query(""),
):
    result = [dict(s) for s in STATIONS]
    if genre:
        result = [s for s in result if genre.lower() in s["genre"].lower()]
    if country:
        result = [s for s in result if s["country"].upper() == country.upper()]
    if hifi:
        result = [s for s in result if s["bitrate"] >= 192]
    if search:
        result = [s for s in result if search.lower() in s["name"].lower() or search.lower() in s["country"].lower()]
    for s in result:
        s["listeners"] = random.randint(200, 85000)
        s["now_playing"] = _now_playing(s["genre"])
        s["signal_strength"] = round(random.uniform(0.7, 1.0), 2)
    return JSONResponse({"total": len(result), "stations": result, "timestamp": datetime.now(timezone.utc).isoformat()})

@app.get("/stations/{station_id}")
async def get_station(station_id: str):
    for s in STATIONS:
        if s["id"] == station_id:
            out = dict(s)
            out["listeners"] = random.randint(200, 85000)
            out["now_playing"] = _now_playing(s["genre"])
            out["signal_strength"] = round(random.uniform(0.8, 1.0), 2)
            out["available_formats"] = list(OUTPUT_FORMATS.keys()) if OUTPUT_FORMATS else ["aac_256", "flac_24_96"]
            return JSONResponse(out)
    raise HTTPException(404, f"Station {station_id!r} introuvable")

@app.get("/formats")
async def get_formats():
    return JSONResponse({"total": len(OUTPUT_FORMATS), "formats": OUTPUT_FORMATS,
                         "hifi_formats": [k for k, v in OUTPUT_FORMATS.items() if v.get("hifi")],
                         "standard_formats": [k for k, v in OUTPUT_FORMATS.items() if not v.get("hifi")]})

@app.post("/encode")
async def encode_stream(request: Request):
    if not ENCODER_OK:
        raise HTTPException(503, "Moteur HCS Radio Encoder non disponible")
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    station_id = body.get("station_id", "bbc_r3")
    output_fmt = body.get("output_format", "flac_24_96")
    station = next((s for s in STATIONS if s["id"] == station_id), STATIONS[1])
    if output_fmt not in OUTPUT_FORMATS:
        raise HTTPException(400, f"Format {output_fmt!r} inconnu. Disponibles: {list(OUTPUT_FORMATS.keys())}")
    src_fmt = station["src_fmt"].replace("-", "_")
    session = _encoder.encode(station["id"], station["name"], src_fmt, output_fmt)
    out_info = OUTPUT_FORMATS[output_fmt]
    return JSONResponse({
        "status": "encoding_active",
        "session": asdict(session),
        "station": dict(station),
        "output_format_info": out_info,
        "stream_url": f"http://localhost:{PORT}/stream/{station_id}/{output_fmt}",
        "hls_url": f"http://localhost:{PORT}/stream/{station_id}/{output_fmt}/playlist.m3u8",
        "hifi_certified": session.hifi_certified,
        "quality": {
            "score": f"{session.quality_score:.2f}/5.0",
            "k_factor": session.hcs_k_factor,
            "snr_db": f"{session.snr_db:.1f} dB",
            "dynamic_range": f"{session.dynamic_range_db:.1f} dB",
            "lufs": f"{session.lufs_normalized:.1f} LUFS",
            "freq_response": f"0 - {session.freq_response_khz:.1f} kHz",
            "thd_pct": session.thd_pct,
            "algorithms": session.algorithms_applied,
            "enhancement_db": f"+{session.enhancement_db:.1f} dB",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/stream/{station_id}/{output_format}/playlist.m3u8")
async def hls_playlist(station_id: str, output_format: str):
    st = next((s for s in STATIONS if s["id"] == station_id), None)
    if not st:
        raise HTTPException(404, f"Station {station_id} introuvable")
    out = OUTPUT_FORMATS.get(output_format, {"bitrate_kbps": 256, "codec": "AAC-LC"})
    m3u8 = "\n".join([
        "#EXTM3U", "#EXT-X-VERSION:3",
        f"#EXT-X-STREAM-INF:BANDWIDTH={out['bitrate_kbps']*1000},CODECS=\"{out['codec']}\",NAME=\"{output_format}\"",
        st["stream_url"], "",
    ])
    return PlainTextResponse(m3u8, media_type="application/vnd.apple.mpegurl", headers={
        "X-HCS-Station": station_id, "X-HCS-Format": output_format,
        "X-HCS-Encoder": "HCS-Radio-Encoder-2.0", "Cache-Control": "no-cache"})

@app.get("/encode/batch")
async def encode_batch(output_format: str = Query("flac_24_96"), max_stations: int = Query(5, le=20)):
    if not ENCODER_OK:
        raise HTTPException(503, "Moteur non disponible")
    results = []
    for s in STATIONS[:max_stations]:
        sess = _encoder.encode(s["id"], s["name"], s["src_fmt"].replace("-","_"), output_format)
        results.append({"station": s["name"], "country": s["country"], "quality": sess.quality_score,
                        "k_factor": sess.hcs_k_factor, "hifi": sess.hifi_certified, "snr_db": sess.snr_db})
    return JSONResponse({"output_format": output_format, "count": len(results), "results": results,
                         "avg_quality": round(sum(r["quality"] for r in results)/len(results), 2) if results else 0})

@app.get("/encoder/stats")
async def encoder_stats():
    if not ENCODER_OK:
        raise HTTPException(503, "Moteur non disponible")
    stats = asdict(_encoder.get_stats())
    stats["total_stations"] = len(STATIONS)
    stats["countries"] = len(set(s["country"] for s in STATIONS))
    stats["genres"] = list(set(s["genre"] for s in STATIONS))
    return JSONResponse(stats)

@app.get("/recommend")
async def recommend(use_case: str = Query("hifi"), station_id: str = Query("bbc_r3")):
    st = next((s for s in STATIONS if s["id"] == station_id), STATIONS[1])
    fmt = _encoder.recommend_format(st["src_fmt"], use_case) if ENCODER_OK else "flac_24_96"
    return JSONResponse({"station": st["name"], "use_case": use_case, "recommended_format": fmt,
                         "format_details": OUTPUT_FORMATS.get(fmt, {})})

@app.get("/world/map")
async def world_map():
    return JSONResponse({"stations": STATIONS, "total": len(STATIONS),
                         "countries": list(set(s["country"] for s in STATIONS)),
                         "genres": list(set(s["genre"] for s in STATIONS)),
                         "hifi_count": sum(1 for s in STATIONS if s["bitrate"] >= 192)})

@app.get("/genres")
async def genres():
    g = {}
    for s in STATIONS:
        genre = s["genre"]
        if genre not in g:
            g[genre] = []
        g[genre].append(s["id"])
    return JSONResponse({"genres": g, "total": len(g)})

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [RADIO-BROADCAST] %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
'''
with open('cdn/services/svc_radio_broadcast.py', 'w', encoding='utf-8') as f:
    f.write(radio_svc)
print("OK: svc_radio_broadcast.py")

# =============================================================================
# 2. MISE À JOUR de services.json
# =============================================================================
with open('cdn/config/services.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)

cfg["services"]["radio_broadcast"] = {
    "id": "radio_broadcast",
    "name": "Radio Broadcast Mondial HiFi",
    "icon": "radio",
    "description": "Broadcast radio mondial haute fidelite - 40 stations, encodage pro a la volee",
    "regions": ["EU", "NA", "AP", "AF", "ME", "SA", "GLOBAL"],
    "port": 9019,
    "protocol": "ICY/HLS/WebSocket",
    "hcs_preset": "broadcast_hd",
    "codec": "HCS-Radio-Encoder v2 (FLAC/PCM/DSD/Opus/Dolby)",
    "resolution": "N/A",
    "framerate": 0,
    "bitrate_mbps": 0,
    "audio": "FLAC 24bit/96kHz | PCM 32bit/192kHz | DSD64/128 | Dolby AC-4 | Opus | AAC",
    "audio_bitrate_kbps": 2800,
    "latency_ms": 120,
    "buffer_seconds": 5,
    "drm": "AES-128",
    "color_space": "N/A",
    "hcs_compression_ratio": 1,
    "cdn_edge_nodes": ["Paris", "London", "Frankfurt", "New York", "Tokyo", "Sydney", "Sao Paulo", "Lagos"],
    "monthly_bandwidth_tb": 30,
    "sla_uptime": "99.95%",
    "price_per_gb": 0.0,
    "status": "active",
    "color": "#7C3AED",
    "total_stations": 40,
    "countries_covered": 22,
    "output_formats": [
        "mp3_128", "mp3_320", "aac_128", "aac_256", "aac_320",
        "aache_64", "aache_96", "opus_96", "opus_192", "opus_320",
        "flac_16", "flac_24_96", "pcm_32_192", "dsd64", "dsd128",
        "dolby_ac4", "hcs_hifi"
    ],
    "hifi_formats": ["flac_16", "flac_24_96", "pcm_32_192", "dsd64", "dsd128", "dolby_ac4", "hcs_hifi"],
    "hcs_features": [
        "HCS-Resampler-Ultra", "HCS-HF-Reconstructor-X2", "HCS-Phase-Coherence",
        "HCS-Harmonic-Synthesizer", "HCS-Normalizer-LUFS-EBU-R128",
        "HCS-Psychoacoustic-Enhancer", "HCS-Dither-Noise-Shaped"
    ],
    "genres": ["Classical", "Jazz", "Pop/Dance", "Dance/EDM", "Rock", "News/Culture", "News/International", "Generalist", "Arabic/Pop", "Classical/Culture"]
}

# Mise à jour des stats globales
cfg["global_stats"]["total_edge_nodes"] = 21
cfg["global_stats"]["monthly_traffic_pb"] = 2.55
cfg["global_stats"]["active_users_million"] = 52

with open('cdn/config/services.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print("OK: services.json mis a jour (port 9019)")

# =============================================================================
# 3. MISE À JOUR de launch_all_services.py
# =============================================================================
with open('cdn/services/launch_all_services.py', 'r', encoding='utf-8') as f:
    launcher = f.read()

# Ajouter le script radio dans SERVICE_SCRIPTS
old = '"audio_upscale_8k":       "svc_audio_upscale_8k.py",'
new = '"audio_upscale_8k":       "svc_audio_upscale_8k.py",\n    "radio_broadcast":        "svc_radio_broadcast.py",'
launcher = launcher.replace(old, new)

# Ajouter le log dans le message de démarrage
old_log = '  log.info("  API Docs:       http://localhost:9000/docs")'
new_log = '  log.info("  API Docs:       http://localhost:9000/docs")\n  log.info("")\n  log.info("  Radio Broadcast: http://localhost:9019")\n  log.info("  Radio Stations:  http://localhost:9019/stations")\n  log.info("  Radio Formats:   http://localhost:9019/formats")'
launcher = launcher.replace(old_log, new_log)

with open('cdn/services/launch_all_services.py', 'w', encoding='utf-8') as f:
    f.write(launcher)
print("OK: launch_all_services.py mis a jour")

print("\n=== Tous les fichiers generes avec succes! ===")
print("  - cdn/services/svc_radio_broadcast.py")
print("  - cdn/config/services.json (port 9019 ajoute)")
print("  - cdn/services/launch_all_services.py (radio_broadcast ajoute)")
