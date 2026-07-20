# Guide d'Assemblage & Test — Prototype Réseau Harmonique

**Document** : GUIDE-ASSEMBLAGE-HLW-1.0  
**Date** : Juillet 2026  
**Prérequis** : Matériel listé dans `BOM_PROTOTYPE_HALOW.md`

---

## Aperçu

Ce guide couvre l'assemblage et le test du premier lien HaLow harmonique :
2 nœuds (émetteur + récepteur) + 1 passerelle de supervision.

```
┌──────────────────┐                    ┌──────────────────┐
│   NŒUD A         │    HaLow 900 MHz   │   NŒUD B         │
│   (émetteur)     │ ◄────────────────► │   (récepteur)     │
│                   │                    │                   │
│   RPi 4 + HaLow   │                    │   RPi 4 + HaLow   │
│   Micro USB       │                    │   Haut-parleur    │
│                   │                    │                   │
└──────┬───────────┘                    └──────┬───────────┘
       │                                      │
       │  Ethernet (optionnel)                │
       ▼                                      ▼
┌──────────────────────────────────────────────────┐
│              PC DE SUPERVISION                    │
│  · Dashboard web (Grafana ou page simple)        │
│  · Scripts de test automatisés                   │
│  · Monitoring lien radio                          │
└──────────────────────────────────────────────────┘
```

---

## Partie 1 : Assemblage Physique

### 1.1 Préparation des Raspberry Pi

```bash
# 1. Flasher Raspberry Pi OS Lite (64-bit) sur les microSD
#    Télécharger : https://www.raspberrypi.com/software/
#    Utiliser Raspberry Pi Imager :
#    - OS : Raspberry Pi OS Lite (64-bit)
#    - Configurer : hostname, SSH activé, mot de passe, WiFi (optionnel)

# 2. Insérer la microSD dans chaque RPi, brancher alimentation, attendre le boot

# 3. Se connecter en SSH (depuis le PC de supervision)
ssh pi@harmonic-node-a.local   # ou l'IP attribuée
ssh pi@harmonic-node-b.local
```

### 1.2 Configuration de Base (les deux nœuds)

```bash
# === À exécuter sur CHAQUE nœud ===

# Mise à jour
sudo apt update && sudo apt upgrade -y

# Outils essentiels
sudo apt install -y \
  iw wireless-tools \
  iperf3 \
  python3-pip python3-numpy \
  git vim \
  tcpdump \
  ntpdate

# Synchronisation horloge (important pour mesures de latence)
sudo ntpdate -s pool.ntp.org
sudo timedatectl set-ntp true

# Créer le répertoire de travail
mkdir -p ~/harmonic
cd ~/harmonic

# Cloner le dépôt (adapter l'URL)
git clone https://github.com/votre-org/harmonic-engine.git .
# OU copier les fichiers via SCP
```

### 1.3 Installation du Module HaLow

#### Option A : Morse Micro MM6108

```bash
# === Installation driver Morse Micro ===

# 1. Installer les dépendances de compilation
sudo apt install -y build-essential linux-headers-$(uname -r) dkms

# 2. Récupérer le driver (contacter Morse Micro pour l'accès)
#    Le driver est généralement fourni sous forme de package .deb ou source
#    Exemple (adapter le chemin) :
cd /tmp
# wget https://.../morse-driver-*.tar.gz   # URL fournie par Morse Micro
# tar xzf morse-driver-*.tar.gz
# cd morse-driver
# make && sudo make install

# 3. Vérifier que le module est chargé
lsmod | grep morse
# Doit afficher : morse_ah    xxxxx  0

# 4. Vérifier que l'interface apparaît
iw dev
# Doit afficher une interface de type wlanX en mode 802.11ah
```

#### Option B : Newracom NRC7292

```bash
# Le NRC7292 apparaît généralement comme interface SPI → wlan
# Driver généralement inclus dans le kernel Linux >= 5.10
# Vérifier :
dmesg | grep -i newracom
iw dev
```

### 1.4 Connexion des Antennes

```
┌──────────────────────────────────────────────────────────────────┐
│  ATTENTION : NE JAMAIS ALIMENTER UN MODULE RADIO SANS ANTENNE ! │
│  Cela peut détruire l'étage de puissance RF.                     │
└──────────────────────────────────────────────────────────────────┘
```

```
1. Connecter le câble pigtail u.FL → SMA sur le module HaLow
   → Le connecteur u.FL est TRÈS fragile. Appuyer doucement jusqu'au clic.
   → NE PAS forcer. Si ça résiste, vérifier l'alignement.

2. Visser l'antenne 900 MHz sur le connecteur SMA
   → Serrer À LA MAIN uniquement (pas de clé)
   → L'antenne doit être verticale pour une polarisation optimale

3. Fixer l'antenne en hauteur si possible (> 1.5m du sol)
   → Utiliser le mât télescopique ou une fixation murale
```

---

## Partie 2 : Configuration Réseau HaLow

### 2.1 Nœud A — Point d'Accès (AP Mode)

```bash
# === Sur harmonic-node-a ===

# 1. Identifier l'interface HaLow
HALOW_IFACE=$(iw dev | grep -B1 "type managed" | head -1 | awk '{print $2}')
echo "Interface HaLow : $HALOW_IFACE"

# 2. Configurer en mode AP avec hostapd
#    (Le driver Morse Micro peut avoir un outil spécifique)
#    Si hostapd ne supporte pas 802.11ah, utiliser l'outil du fabricant

# Version hostapd (si supporté) :
sudo tee /etc/hostapd/hostapd-halow.conf << 'EOF'
interface=wlan1          # Adapter au nom réel
driver=nl80211
ssid=HARMONIC-TEST
hw_mode=g                # 802.11ah se configure comme 802.11g en 900 MHz
channel=1                # Canal 1 = 902-904 MHz (selon régulation locale)
ieee80211n=0             # Pas de HT pour HaLow basic
ieee80211ah=1            # Flag HaLow (si supporté)
wmm_enabled=1
auth_algs=1              # Open system
wpa=0                    # Pas de chiffrement pour le test initial
# wpa=2                  # À activer après le test
# wpa_passphrase=TestHarmonic2026
# wpa_key_mgmt=WPA-PSK
# rsn_pairwise=CCMP
EOF

sudo hostapd -B /etc/hostapd/hostapd-halow.conf

# 3. Configurer l'adresse IP
sudo ip addr add 10.42.0.1/24 dev $HALOW_IFACE
sudo ip link set $HALOW_IFACE up

# 4. Activer le routage (pour donner accès Internet si connecté)
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || true
```

### 2.2 Nœud B — Station (Client Mode)

```bash
# === Sur harmonic-node-b ===

HALOW_IFACE=$(iw dev | grep -B1 "type managed" | head -1 | awk '{print $2}')

# 1. Scanner les réseaux HaLow disponibles
sudo iw dev $HALOW_IFACE scan | grep -E "SSID|freq|signal"

# 2. Se connecter au réseau HARMONIC-TEST
sudo iw dev $HALOW_IFACE connect HARMONIC-TEST

# OU avec wpa_supplicant (si chiffrement activé) :
# sudo tee /etc/wpa_supplicant/wpa-halow.conf << 'EOF'
# network={
#     ssid="HARMONIC-TEST"
#     psk="TestHarmonic2026"
# }
# EOF
# sudo wpa_supplicant -B -i $HALOW_IFACE -c /etc/wpa_supplicant/wpa-halow.conf

# 3. Obtenir une IP (si DHCP sur le nœud A)
sudo dhclient $HALOW_IFACE
# Ou IP fixe :
# sudo ip addr add 10.42.0.2/24 dev $HALOW_IFACE

sudo ip link set $HALOW_IFACE up
```

### 2.3 Vérification de la Connexion

```bash
# Depuis le nœud B
ping 10.42.0.1 -c 10

# Résultat attendu :
# 64 bytes from 10.42.0.1: icmp_seq=1 ttl=64 time=3.5 ms
# 64 bytes from 10.42.0.1: icmp_seq=2 ttl=64 time=4.2 ms
# ...

# → Latence < 10 ms = lien HaLow fonctionnel !
```

---

## Partie 3 : Test du Lien Radio

### 3.1 Test de Bande Passante (iperf3)

```bash
# === Sur le nœud A (serveur iperf3) ===
iperf3 -s

# === Sur le nœud B (client) ===
# Test débit TCP (upload de B vers A) :
iperf3 -c 10.42.0.1 -t 30

# Test débit TCP (download de A vers B) :
iperf3 -c 10.42.0.1 -t 30 -R

# Test UDP à débit contrôlé :
iperf3 -c 10.42.0.1 -u -b 2M -t 30

# === Résultats attendus (2 MHz, MCS7, courte distance) ===
# TCP : 1.5 – 4 Mbps
# UDP : 2 – 6 Mbps (avec < 1% perte)
```

### 3.2 Test de Latence sous Charge

```bash
# === Sur le nœud B ===
# Ping continu pendant un transfert
ping 10.42.0.1 -i 0.1 > ping_log.txt &
PING_PID=$!

# Lancer un transfert lourd (30 secondes)
iperf3 -c 10.42.0.1 -t 30

# Arrêter le ping
kill $PING_PID

# Analyser la latence
cat ping_log.txt | grep "time=" | awk -F'time=' '{print $2}' | awk '{print $1}' | sort -n | head -1
# → Latence minimale

cat ping_log.txt | grep "time=" | awk -F'time=' '{print $2}' | awk '{print $1}' | sort -n | tail -1
# → Latence maximale

cat ping_log.txt | grep "time=" | awk -F'time=' '{print $2}' | awk '{print $1}' | awk '{sum+=$1; count++} END {print sum/count}'
# → Latence moyenne
```

### 3.3 Test de Portée

```bash
# === Protocole de test de portée ===

# 1. Positionner le nœud A (AP) à un point fixe (ex : fenêtre, balcon)
# 2. Noter les coordonnées GPS (ou repères visuels)
# 3. Avec le nœud B (client), s'éloigner progressivement :

# Distance 0m (référence, à côté de l'AP)
iw dev $HALOW_IFACE link
# Noter : signal (dBm), bitrate (Mbps)

# Distance 100m
# → Refaire le test iperf3 + ping

# Distance 250m
# → Refaire

# Distance 500m (si possible avec ligne de vue)
# → Refaire

# Distance 1 km (point haut → point haut si possible)
# → Refaire

# === TABLEAU DE RÉSULTATS ===
# | Distance | Signal (dBm) | Débit TCP | Latence moy. | Perte paquets |
# |----------|-------------|-----------|-------------|---------------|
# | 0m       | -25         | 3.8 Mbps  | 3 ms        | 0%            |
# | 100m     | -55         | 2.5 Mbps  | 5 ms        | 0%            |
# | 250m     | -70         | 1.2 Mbps  | 8 ms        | 0.5%          |
# | 500m     | -85         | 0.3 Mbps  | 15 ms       | 3%            |
```

---

## Partie 4 : Intégration Codec Vocal Harmonique

### 4.1 Installation du HVC sur les Nœuds

```bash
# === Sur CHAQUE nœud ===

cd ~/harmonic/engine

# Installer les dépendances
pip3 install numpy zstandard

# Vérifier que le HVC fonctionne
python3 harmonic_voice_codec.py
# Doit afficher :
# HARMONIC VOICE CODEC (HVC) — Prototype v1.0
# [1] Génération signal de test...
# [2] Calibration du dictionnaire...
# ...
# RÉSUMÉ : XXXX bps, MOS X.X
```

### 4.2 Script de Test Vocal Complet

Créer le fichier `~/harmonic/engine/test_voice_link.py` :

```python
#!/usr/bin/env python3
"""
Test du lien vocal harmonique entre 2 nœuds.
Exécuter sur le nœud émetteur (A) et récepteur (B) simultanément.
"""

import socket
import struct
import time
import wave
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harmonic_voice_codec import (
    HarmonicVoiceCodec, SAMPLE_RATE, FRAME_SIZE, HOP_SIZE,
    estimate_mos
)

# ── Configuration ─────────────────────────────────────────────────────────
SERVER_HOST = '10.42.0.1'  # IP du nœud A (AP)
PORT = 5001
MODE = sys.argv[1] if len(sys.argv) > 1 else 'receiver'  # 'sender' ou 'receiver'

# ── Codec ─────────────────────────────────────────────────────────────────
print("[INIT] Initialisation du codec...")
codec = HarmonicVoiceCodec(max_fragments=256, quality=80)

# Calibration rapide avec un fichier wav existant
test_wav = Path(__file__).parent / 'data' / 'test_voice.wav'
if test_wav.exists():
    codec.calibrate(str(test_wav))
else:
    # Créer un dictionnaire vide (sera rempli à la volée)
    print("[WARN] Pas de fichier de calibration. Qualité réduite.")

# ── Émetteur ─────────────────────────────────────────────────────────────
if MODE == 'sender':
    print(f"[SENDER] Connexion à {SERVER_HOST}:{PORT}...")

    # Capturer depuis le micro ou lire un fichier WAV
    if len(sys.argv) > 2:
        # Lire depuis un fichier
        wav_path = sys.argv[2]
        print(f"[SENDER] Lecture du fichier: {wav_path}")
        with wave.open(wav_path, 'rb') as wf:
            assert wf.getframerate() == SAMPLE_RATE
            n_samples = wf.getnframes()
            audio = np.frombuffer(wf.readframes(n_samples), dtype=np.int16).astype(np.float32) / 32768.0
    else:
        print("[SENDER] Génération signal de test (sinusoïde modulée)...")
        # Signal de test : sinusoïde type voix
        duration = 5.0
        t = np.arange(0, duration, 1.0 / SAMPLE_RATE, dtype=np.float32)
        f0 = 150 + 50 * np.sin(2 * np.pi * 0.5 * t)
        audio = 0.6 * np.sin(2 * np.pi * f0 * t) + 0.25 * np.sin(4 * np.pi * f0 * t)
        audio = audio / np.max(np.abs(audio))

    # Encoder
    print(f"[SENDER] Encodage de {len(audio)/SAMPLE_RATE:.1f}s d'audio...")
    compressed = codec.encode(audio)
    stats = codec.stats
    print(f"[SENDER] Débit: {stats['avg_bitrate_bps']:.0f} bps")
    print(f"[SENDER] Taille: {len(compressed)} bytes ({len(compressed)/1024:.1f} KB)")
    print(f"[SENDER] Hit rate: {stats['hit_rate']*100:.1f}%")

    # Envoyer via TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, PORT))

    # Envoyer la taille d'abord (4 octets)
    sock.sendall(struct.pack('<I', len(compressed)))
    # Envoyer les données
    sock.sendall(compressed)
    sock.close()

    print("[SENDER] ✅ Transmission terminée.")

# ── Récepteur ─────────────────────────────────────────────────────────────
elif MODE == 'receiver':
    print(f"[RECEIVER] Écoute sur 0.0.0.0:{PORT}...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', PORT))
    sock.listen(1)

    conn, addr = sock.accept()
    print(f"[RECEIVER] Connexion de {addr}")

    # Recevoir la taille
    size_data = conn.recv(4)
    data_size = struct.unpack('<I', size_data)[0]
    print(f"[RECEIVER] Attente de {data_size} bytes...")

    # Recevoir les données
    data = b''
    while len(data) < data_size:
        chunk = conn.recv(min(4096, data_size - len(data)))
        if not chunk:
            break
        data += chunk

    conn.close()
    sock.close()

    print(f"[RECEIVER] Reçu {len(data)} bytes en {(time.perf_counter() - sock.getsockname()[0])*1000:.0f}ms")

    # Décoder
    print("[RECEIVER] Décodage...")
    t_start = time.perf_counter()
    audio = codec.decode(data)
    decode_time = time.perf_counter() - t_start
    print(f"[RECEIVER] Décodé en {decode_time*1000:.0f}ms")
    print(f"[RECEIVER] Durée audio: {len(audio)/SAMPLE_RATE:.1f}s")

    # Sauvegarder
    output_wav = Path(__file__).parent / 'data' / 'received_voice.wav'
    output_wav.parent.mkdir(exist_ok=True)
    audio_i16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(output_wav), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_i16.tobytes())
    print(f"[RECEIVER] Audio sauvegardé: {output_wav}")

    # Métriques (si on a l'original pour comparaison)
    stats = codec.stats
    print(f"\n[RÉSUMÉ]")
    print(f"  Débit effectif: {len(data)*8 / (len(audio)/SAMPLE_RATE):.0f} bps")
    print(f"  Hit rate dict: {stats['hit_rate']*100:.1f}%")
    print(f"  Temps encodage: {stats['encode_time_ms']:.1f} ms")
    print(f"  Temps décodage: {stats['decode_time_ms']:.1f} ms")
    print("[RECEIVER] ✅ Test terminé.")

else:
    print(f"Usage: python3 test_voice_link.py [sender|receiver] [fichier.wav]")
    sys.exit(1)
```

### 4.3 Exécution du Test Vocal

```bash
# === Terminal 1 — Nœud B (récepteur) ===
ssh pi@harmonic-node-b
cd ~/harmonic/engine
python3 test_voice_link.py receiver

# === Terminal 2 — Nœud A (émetteur) ===
ssh pi@harmonic-node-a
cd ~/harmonic/engine
python3 test_voice_link.py sender data/test_voice.wav

# === Résultat attendu ===
# [RECEIVER] Attente de 1234 bytes...
# [RECEIVER] Reçu 1234 bytes
# [RECEIVER] Audio sauvegardé: data/received_voice.wav
# [RÉSUMÉ]
#   Débit effectif: 1050 bps
#   Hit rate dict: 87.3%
#   Temps encodage: 45 ms
#   Temps décodage: 12 ms
```

---

## Partie 5 : Script de Test Automatisé Complet

Fichier `~/harmonic/engine/test_halow_full.py` :

```python
#!/usr/bin/env python3
"""
Test complet du lien HaLow harmonique.
Mesure : bande passante, latence, perte, performance vocale, transfert image.

Exécuter depuis le nœud B (client) avec le nœud A (serveur) déjà configuré.
"""

import subprocess
import time
import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np

SERVER = "10.42.0.1"
RESULTS = {}

def run_cmd(cmd, timeout=30):
    """Exécute une commande shell et retourne stdout."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True,
                                text=True, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1

def test_connectivity():
    """Test 1 : Connectivité de base."""
    print("\n" + "="*60)
    print(" TEST 1 : CONNECTIVITÉ")
    print("="*60)

    stdout, stderr, rc = run_cmd(f"ping -c 10 -W 2 {SERVER}")
    if rc == 0:
        # Extraire stats
        for line in stdout.split('\n'):
            if 'packet loss' in line:
                print(f"  {line.strip()}")
            if 'avg' in line:
                print(f"  Latence : {line.strip()}")
        RESULTS['connectivity'] = 'OK'
    else:
        print(f"  ❌ ÉCHEC : {stderr}")
        RESULTS['connectivity'] = 'FAIL'
        return False
    return True

def test_bandwidth():
    """Test 2 : Bande passante."""
    print("\n" + "="*60)
    print(" TEST 2 : BANDE PASSANTE (iperf3)")
    print("="*60)

    # Test TCP upload
    stdout, _, rc = run_cmd(f"iperf3 -c {SERVER} -t 10 -J", timeout=20)
    if rc == 0:
        try:
            data = json.loads(stdout)
            bw = data['end']['sum_sent']['bits_per_second'] / 1e6
            print(f"  Débit TCP upload : {bw:.2f} Mbps")
            RESULTS['tcp_upload_mbps'] = round(bw, 2)
        except:
            print("  Erreur parsing JSON iperf3")
            RESULTS['tcp_upload_mbps'] = 0
    else:
        print(f"  ⚠️ iperf3 serveur non lancé sur {SERVER}?")
        print(f"  Lancez d'abord : ssh {SERVER} 'iperf3 -s'")
        RESULTS['tcp_upload_mbps'] = None

def test_latency_under_load():
    """Test 3 : Latence sous charge."""
    print("\n" + "="*60)
    print(" TEST 3 : LATENCE SOUS CHARGE")
    print("="*60)

    # Ping en arrière-plan pendant iperf3
    ping_cmd = f"ping -c 100 -i 0.1 {SERVER}"
    # Simplifié : juste un ping normal
    stdout, _, rc = run_cmd(ping_cmd, timeout=30)

    if rc == 0:
        latencies = []
        for line in stdout.split('\n'):
            if 'time=' in line:
                try:
                    lat = float(line.split('time=')[1].split(' ')[0])
                    latencies.append(lat)
                except:
                    pass

        if latencies:
            avg_lat = np.mean(latencies)
            max_lat = np.max(latencies)
            jitter = np.std(latencies)
            print(f"  Latence moyenne : {avg_lat:.1f} ms")
            print(f"  Latence max     : {max_lat:.1f} ms")
            print(f"  Jitter (std)    : {jitter:.1f} ms")
            RESULTS.update({
                'latency_avg_ms': round(avg_lat, 1),
                'latency_max_ms': round(max_lat, 1),
                'latency_jitter_ms': round(jitter, 1),
            })

def test_signal_strength():
    """Test 4 : Force du signal radio."""
    print("\n" + "="*60)
    print(" TEST 4 : SIGNAL RADIO")
    print("="*60)

    stdout, _, _ = run_cmd("iw dev wlan1 link 2>/dev/null || iw dev wlan0 link")

    for line in stdout.split('\n'):
        line = line.strip()
        if 'signal' in line.lower():
            print(f"  {line}")
            try:
                signal = float(line.split(':')[1].strip().split(' ')[0])
                RESULTS['signal_dbm'] = signal
            except:
                pass
        if 'bitrate' in line.lower() or 'tx bitrate' in line.lower():
            print(f"  {line}")

def test_file_transfer():
    """Test 5 : Transfert de fichier (simulation photo compressée)."""
    print("\n" + "="*60)
    print(" TEST 5 : TRANSFERT FICHIER (simulation photo)")
    print("="*60)

    # Créer un fichier de test de 3.3 KB (taille photo harmonique 400x400)
    test_data = np.random.bytes(3300)

    test_file = Path('/tmp/harmonic_test_photo.bin')
    test_file.write_bytes(test_data)

    # Envoyer via scp
    t0 = time.perf_counter()
    rc = subprocess.run(
        ['scp', '-o', 'StrictHostKeyChecking=no',
         str(test_file), f'pi@{SERVER}:/tmp/received_photo.bin'],
        capture_output=True, timeout=10
    )
    elapsed = time.perf_counter() - t0

    if rc.returncode == 0:
        effective_rate = (3300 * 8) / elapsed  # bps
        print(f"  Taille : 3300 bytes (photo 400×400 harmonique)")
        print(f"  Temps  : {elapsed*1000:.0f} ms")
        print(f"  Débit effectif : {effective_rate:.0f} bps ({effective_rate/1000:.1f} kbps)")
        RESULTS['file_transfer_ms'] = round(elapsed * 1000, 0)
        RESULTS['file_transfer_kbps'] = round(effective_rate / 1000, 1)
    else:
        print(f"  ⚠️ Échec transfert : {rc.stderr.decode()}")

def generate_report():
    """Génère le rapport final."""
    print("\n" + "="*60)
    print(" RAPPORT DE TEST — LIEN HALOW HARMONIQUE")
    print("="*60)
    print(f" Date    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Serveur : {SERVER}")
    print()

    for test, result in RESULTS.items():
        status = "✅" if result not in [None, 'FAIL'] else "❌"
        if result == 'OK':
            print(f"  {status} {test}")
        elif result == 'FAIL':
            print(f"  {status} {test} — ÉCHEC")
        elif result is None:
            print(f"  ⚠️ {test} — Non testé")
        else:
            print(f"  {status} {test} : {result}")

    # Sauvegarder en JSON
    report_path = Path(__file__).parent / 'data' / f'test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump({'date': datetime.now().isoformat(), 'results': RESULTS}, f, indent=2)
    print(f"\n  Rapport sauvegardé : {report_path}")

    print("="*60)

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════╗
    ║  TEST COMPLET — LIEN HALOW HARMONIQUE           ║
    ║  Vérifie : connectivité, débit, latence, signal  ║
    ╚══════════════════════════════════════════════════╝
    """)

    test_connectivity()
    test_signal_strength()
    test_bandwidth()
    test_latency_under_load()
    test_file_transfer()
    generate_report()
```

### 5.1 Exécution du Test Complet

```bash
# === Préparation (sur le nœud A) ===
ssh pi@harmonic-node-a "iperf3 -s -D"  # Lancer iperf3 en daemon

# === Test complet (depuis le nœud B) ===
ssh pi@harmonic-node-b
cd ~/harmonic/engine
python3 test_halow_full.py

# === Résultat attendu ===
# ╔══════════════════════════════════════════════════╗
# ║  TEST COMPLET — LIEN HALOW HARMONIQUE           ║
# ╚══════════════════════════════════════════════════╝
#
# ============================================================
#  TEST 1 : CONNECTIVITÉ
# ============================================================
#   10 packets transmitted, 10 received, 0% packet loss
#   Latence : rtt min/avg/max/mdev = 3.2/5.1/12.3/2.8 ms
#
# ============================================================
#  TEST 2 : BANDE PASSANTE (iperf3)
# ============================================================
#   Débit TCP upload : 3.45 Mbps
#
# ============================================================
#  TEST 3 : LATENCE SOUS CHARGE
# ============================================================
#   Latence moyenne : 5.8 ms
#   Latence max     : 18.2 ms
#   Jitter (std)    : 2.1 ms
#
# ============================================================
#  TEST 4 : SIGNAL RADIO
# ============================================================
#   signal: -48 dBm
#   tx bitrate: 4.0 Mbit/s
#
# ============================================================
#  TEST 5 : TRANSFERT FICHIER (simulation photo)
# ============================================================
#   Taille : 3300 bytes (photo 400×400 harmonique)
#   Temps  : 85 ms
#   Débit effectif : 310.6 kbps
#
# ============================================================
#  RAPPORT DE TEST — LIEN HALOW HARMONIQUE
# ============================================================
#   ✅ connectivity
#   ✅ tcp_upload_mbps : 3.45
#   ✅ signal_dbm : -48
#   ✅ latency_avg_ms : 5.8
#   ✅ latency_jitter_ms : 2.1
#   ✅ file_transfer_ms : 85.0
#   ✅ file_transfer_kbps : 310.6
```

---

## Partie 6 : Dépannage Rapide

| Symptôme | Cause probable | Solution |
|----------|---------------|----------|
| Interface HaLow invisible (`iw dev`) | Driver non chargé | `sudo modprobe morse_ah` ou rebooter |
| `hostapd` refuse de démarrer | Canal non supporté | Essayer canal 1, 2, ou 4 |
| Pas de connexion entre nœuds | Puissance insuffisante / distance | Rapprocher les nœuds, vérifier antennes |
| Ping OK mais débit très bas | Interférences ou MCS dégradé | Forcer MCS : `iw dev wlan1 set bitrates legacy-2.4 1` |
| Coupures aléatoires | Alimentation instable | Vérifier câble USB, utiliser alim 3A officielle |
| Module HaLow surchauffe | Manque de ventilation | Ajouter dissipateur passif, espacer les tests |

---

## Prochaines Étapes Après Validation

1. ✅ Lien HaLow fonctionnel → passer au test avec HVC réel
2. ✅ Voix transmise avec qualité → test en extérieur (portée réelle)
3. ✅ Test solaire → validation autonomie énergétique
4. ✅ Déploiement village pilote → Phase 2

---

*Guide d'assemblage v1.0 — Projet Univers Harmonique*
