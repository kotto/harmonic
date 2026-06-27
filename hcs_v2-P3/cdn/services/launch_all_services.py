"""
HCS MiniCDN - Lanceur de tous les services
==========================================
Lance en parallele (subprocess) tous les services CDN:
  - CDN Gateway          (port 9000)
  - TV Broadcast 4K      (port 9010)
  - TV Broadcast 8K      (port 9011)
  - Mobile 8K USA        (port 9012)
  - Mobile Africa 1Mbps  (port 9013)
  - VOD Premium          (port 9014)
  - Live Events          (port 9015)
  - Archive Storage      (port 9016)
  - Football 8K          (port 9017)
  - Audio Upscaling 8K   (port 9018)
  - Radio Broadcast HiFi (port 9019)
  - Telephonie/Video 8K  (port 9020)
  - WebRTC Signaling     (port 9021)
"""

import os
import sys
import json
import time
import signal
import subprocess
import threading
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [LAUNCHER] %(message)s")
log = logging.getLogger("CDN-Launcher")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "services.json")
SERVICES_DIR = os.path.join(BASE_DIR, "services")
CORE_DIR = os.path.join(BASE_DIR, "core")

with open(CONFIG_PATH, "r") as f:
    CDN_CONFIG = json.load(f)

SERVICES = CDN_CONFIG["services"]

# Map service_id -> script dans services/
SERVICE_SCRIPTS = {
    "tv_broadcast_4k":        "svc_tv_4k.py",
    "tv_broadcast_8k":        "svc_tv_8k.py",
    "mobile_streaming_8k_us": "svc_mobile_us.py",
    "mobile_streaming_africa":"svc_mobile_africa.py",
    "vod_premium":            "svc_vod.py",
    "live_events":            "svc_live.py",
    "archive_storage":        "svc_archive.py",
    "audio_upscale_8k":       "svc_audio_upscale_8k.py",
    "radio_broadcast":        "svc_radio_broadcast.py",
    "telephony_video_8k":     "svc_telephony_8k.py",
    "webrtc_signaling":       "svc_webrtc_signaling.py",
}

# Inclure football si le script existe
_football_script = os.path.join(SERVICES_DIR, "svc_football_8k.py")
if os.path.exists(_football_script):
    SERVICE_SCRIPTS["football_8k_bouquet"] = "svc_football_8k.py"

processes: dict = {}


def start_service(service_id: str, script_name: str, port: int):
    """Lance un service dans un sous-processus."""
    script_path = os.path.join(SERVICES_DIR, script_name)
    if not os.path.exists(script_path):
        log.warning("Script manquant: %s — generation auto", script_path)
        _generate_service_script(service_id, script_name, port)

    env = os.environ.copy()
    env["HCS_SERVICE_ID"] = service_id
    env["HCS_SERVICE_PORT"] = str(port)
    env["HCS_ORIGIN"] = CDN_CONFIG.get("origin_server", "http://localhost:8009")
    env["CDN_GATEWAY"] = f"http://localhost:{CDN_CONFIG.get('cdn_port', 9000)}"

    proc = subprocess.Popen(
        [sys.executable, script_path],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
    )
    processes[service_id] = proc
    log.info("Service %-30s demarre (PID %d, port %d)", service_id, proc.pid, port)

    # Thread pour lire les logs du subprocess
    def _reader():
        for line in iter(proc.stdout.readline, ''):
            print(f"  [{service_id[:20]:20s}] {line.rstrip()}")
        proc.stdout.close()

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    return proc


def start_gateway():
    """Lance le CDN Gateway sur le port 9000."""
    env = os.environ.copy()
    env["CDN_GATEWAY"] = f"http://localhost:{CDN_CONFIG.get('cdn_port', 9000)}"

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn",
         "cdn.core.cdn_server:app",
         "--host", "0.0.0.0",
         "--port", str(CDN_CONFIG.get("cdn_port", 9000)),
         "--log-level", "info"],
        cwd=os.path.dirname(BASE_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
    )
    processes["cdn_gateway"] = proc
    log.info("CDN Gateway demarre (PID %d, port %d)", proc.pid, CDN_CONFIG.get("cdn_port", 9000))

    def _reader():
        for line in iter(proc.stdout.readline, ''):
            print(f"  [CDN-GATEWAY            ] {line.rstrip()}")
        proc.stdout.close()

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    return proc


def _generate_service_script(service_id: str, script_name: str, port: int):
    """Genere automatiquement un script de service minimal."""
    script_path = os.path.join(SERVICES_DIR, script_name)
    content = f'''"""
HCS MiniCDN - Service {service_id} (auto-genere)
Port: {port}
"""
import os, sys, json, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.service_base import HCSServiceBase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "config", "services.json")) as f:
    config = json.load(f)

service_config = config["services"]["{service_id}"]
svc = HCSServiceBase(service_config, {port})

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(svc.app, host="0.0.0.0", port={port}, access_log=False)
'''
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)
    log.info("Script auto-genere: %s", script_path)


def shutdown_all():
    """Arrete tous les sous-processus."""
    log.info("Arret de tous les services...")
    for sid, proc in processes.items():
        try:
            proc.terminate()
            proc.wait(timeout=5)
            log.info("Service %s arrete", sid)
        except Exception as e:
            log.warning("Impossible d'arreter %s: %s", sid, e)
            try:
                proc.kill()
            except Exception:
                pass


def main():
    log.info("=" * 70)
    log.info("  HCS MiniCDN - Demarrage de tous les services")
    log.info("=" * 70)

    # Lancer le gateway CDN
    start_gateway()
    time.sleep(2)

    # Lancer tous les services
    for sid, script in SERVICE_SCRIPTS.items():
        if sid not in SERVICES:
            log.warning("Service %s absent de services.json, ignore", sid)
            continue
        port = SERVICES[sid]["port"]
        start_service(sid, script, port)
        time.sleep(0.5)

    log.info("")
    log.info("=" * 70)
    log.info("  Tous les services sont demarres!")
    log.info("")
    log.info("  CDN Gateway:           http://localhost:9000")
    log.info("  CDN Dashboard:         http://localhost:9000/dashboard")
    log.info("  API Docs:              http://localhost:9000/docs")
    log.info("")
    log.info("  --- Services Media ---")
    log.info("  TV Broadcast 4K:       http://localhost:9010")
    log.info("  TV Broadcast 8K:       http://localhost:9011")
    log.info("  Mobile 8K USA:         http://localhost:9012")
    log.info("  Mobile Africa:         http://localhost:9013")
    log.info("  VOD Premium:           http://localhost:9014")
    log.info("  Live Events:           http://localhost:9015")
    log.info("  Archive Storage:       http://localhost:9016")
    log.info("  Football 8K:           http://localhost:9017")
    log.info("  Audio Upscaling 8K:    http://localhost:9018")
    log.info("")
    log.info("  --- Nouveaux Services ---")
    log.info("  Radio Broadcast HiFi:  http://localhost:9019")
    log.info("    Stations:            http://localhost:9019/stations")
    log.info("    Encodage HiFi:       http://localhost:9019/encode")
    log.info("")
    log.info("  Telephonie/Video 8K:   http://localhost:9020")
    log.info("    Qualites appel:      http://localhost:9020/qualities")
    log.info("    Initier appel:       http://localhost:9020/call/initiate (POST)")
    log.info("    Demo 8K:             http://localhost:9020/demo/8k-call")
    log.info("    Conference 8K:       http://localhost:9020/conference/capabilities")
    log.info("    Profils audio:       http://localhost:9020/audio/profiles")
    log.info("")
    log.info("  WebRTC Signaling:      http://localhost:9021")
    log.info("    Creer room:          http://localhost:9021/room/create (POST)")
    log.info("    ICE Servers:         http://localhost:9021/ice/servers")
    log.info("    SDP Template 8K:     http://localhost:9021/sdp/template/8k")
    log.info("    WebSocket:           ws://localhost:9021/ws/{room_id}/{peer_id}")
    log.info("")
    log.info("  --- Frontend ---")
    log.info("  Telephonie 8K UI:      cdn/frontend/telephony_8k.html")
    log.info("  TV World 8K UI:        cdn/frontend/tv_world_8k.html")
    log.info("  Radio World UI:        cdn/frontend/radio_world.html")
    log.info("=" * 70)

    # Signal handler pour arret propre
    def _signal_handler(sig, frame):
        log.info("Signal recu, arret en cours...")
        shutdown_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, _signal_handler)

    # Attendre que les processus se terminent
    try:
        while True:
            time.sleep(10)
            dead = []
            for sid, proc in list(processes.items()):
                if proc.poll() is not None:
                    log.warning("Service %s s'est arrete (code %d)", sid, proc.returncode)
                    dead.append(sid)
            for sid in dead:
                del processes[sid]
            if not processes:
                log.error("Tous les services sont arretes!")
                break
    except KeyboardInterrupt:
        shutdown_all()


if __name__ == "__main__":
    main()
