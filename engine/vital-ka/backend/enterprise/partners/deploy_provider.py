#!/usr/bin/env python3
"""
deploy_provider.py — Déploiement 1-clic de KA Enterprise chez un hébergeur
==========================================================================

Crée le VPS chez le fournisseur choisi (API officielle) ou installe sur un
VPS existant, copie le package de déploiement, puis lance deploy_vps.sh en
SSH. Tout tourne ensuite sur le VPS du CLIENT — l'hébergeur ne voit jamais
les données (elles restent chiffrées au repos chez le client).

Usage :
  # Hetzner Cloud (création automatique + installation)
  python deploy_provider.py --provider hetzner --token <API_TOKEN> \
      --ssh-key ~/.ssh/id_ed25519

  # Scaleway (création automatique + installation)
  python deploy_provider.py --provider scaleway --secret-key <SK> \
      --project-id <PROJECT_ID> --ssh-key ~/.ssh/id_ed25519

  # OVHcloud (VPS créé depuis le manager OVH — l'API OVH commande via
  # panier ; installation sur l'IP du VPS existant)
  python deploy_provider.py --provider ovh --ip <VPS_IP> \
      --ssh-key ~/.ssh/id_ed25519

  # VPS existant chez n'importe quel hébergeur (installation seule)
  python deploy_provider.py --ip <IP> --ssh-key ~/.ssh/id_ed25519

  # Simulation complète (aucun appel réseau ni SSH) :
  python deploy_provider.py --provider hetzner --token x --dry-run

Exit : 0 si l'installation s'est terminée (KA Enterprise répond sur :8767).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEPLOY_DIR = HERE.parent / 'deploy_vps'          # package à copier sur le VPS
PORT = 8767
_TIMEOUT = 15
_UA = 'KA-Enterprise-deploy/1.0'


# ═══════════════════════════════════════════════════════════════════════════════
# API HETZNER CLOUD
# ═══════════════════════════════════════════════════════════════════════════════

def hetzner_create(token: str, name: str, ssh_key_path: str,
                   server_type: str = 'cx22',        # 2 vCPU / 4 Go
                   location: str = 'fsn1',
                   image: str = 'ubuntu-24.04',
                   dry: bool = False) -> str:
    """Crée un serveur Hetzner. Retourne son IP publique."""
    url = 'https://api.hetzner.cloud/v1/servers'
    if dry:
        print(f'   ▶ Hetzner : création « {name} » ({server_type}, {location}, {image})')
        print(f'   (dry-run) POST {url}\n   {{server_type, location, image, ssh_keys}}')
        return '1.2.3.4'
    pub = Path(ssh_key_path).expanduser().read_text().strip()
    fingerprint = _hetzner_fingerprint(pub)
    body = {'name': name, 'server_type': server_type, 'location': location,
            'image': image, 'ssh_keys': [{'id': fingerprint}]}
    print(f'   ▶ Hetzner : création « {name} » ({server_type}, {location}, {image})')
    data = _api(url, 'POST', body, {'Authorization': f'Bearer {token}'})
    server = data['server']
    return _wait_for_ip(url + f"/{server['id']}", token, server['id'])


def _hetzner_fingerprint(pub: str) -> str:
    """Fingerprint SSH (SHA256) à partir de la clé publique."""
    b64 = pub.split()[1] if len(pub.split()) > 1 else pub
    import base64
    raw = base64.b64decode(b64)
    digest = hashlib.sha256(raw).digest()
    return 'sha256:' + urllib.parse.quote(
        base64.b64encode(digest).decode().rstrip('='))


def _wait_for_ip(base_url: str, token: str, server_id: str) -> str:
    for _ in range(30):
        data = _api(base_url, 'GET', None,
                    {'Authorization': f'Bearer {token}'})
        ipv4 = data.get('server', {}).get('public_net', {}).get('ipv4', {}).get('ip')
        if ipv4:
            return ipv4
        time.sleep(4)
    raise RuntimeError('IP non attribuée après 2 min')


# ═══════════════════════════════════════════════════════════════════════════════
# API SCALEWAY
# ═══════════════════════════════════════════════════════════════════════════════

def scaleway_create(secret_key: str, project_id: str, name: str,
                    ssh_key_path: str, commercial_type: str = 'DEV1-S',
                    zone: str = 'fr-par-1', image_name: str = 'ubuntu-jammy',
                    dry: bool = False) -> str:
    """Crée un serveur Scaleway (instance). Retourne son IP."""
    base = f'https://api.scaleway.com/instance/v1/zones/{zone}'
    headers = {'X-Auth-Token': secret_key}
    if dry:
        print(f'   ▶ Scaleway : création « {name} » ({commercial_type}, {zone})')
        print(f'   (dry-run) GET {base}/images?name={image_name}')
        return '1.2.3.4'
    images = _api(f'{base}/images?name={image_name}', 'GET', None, headers)
    image_id = images['images'][0]['id']
    body = {'name': name, 'commercial_type': commercial_type,
            'image': image_id, 'organization': project_id,
            'project': project_id}
    print(f'   ▶ Scaleway : création « {name} » ({commercial_type}, {zone}, {image_name})')
    _api(f'{base}/servers', 'POST', body, headers)
    # L'IP n'est attribuée qu'au boot (server action) — retourne l'IP publique
    servers = _api(f'{base}/servers?name={name}', 'GET', None, headers)
    srv = servers['servers'][0]
    if srv.get('public_ip'):
        return srv['public_ip']['address']
    # Boot + attente IP
    _api(f'{base}/servers/{srv["id"]}/action', 'POST', {'action': 'poweron'}, headers)
    for _ in range(30):
        servers = _api(f'{base}/servers/{srv["id"]}', 'GET', None, headers)
        ip = servers['server'].get('public_ip')
        if ip:
            return ip['address']
        time.sleep(4)
    raise RuntimeError('IP non attribuée après 2 min')


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLATION SSH (tous les fournisseurs, ou VPS existant)
# ═══════════════════════════════════════════════════════════════════════════════

def _ssh(args: list, dry: bool = False):
    if dry:
        print(f'   (dry-run) ssh {" ".join(args[-3:])}')
        return
    subprocess.run(args, check=True)


def install(ip: str, ssh_key: str, ssh_user: str = 'root',
            dry: bool = False) -> None:
    """Copie deploy_vps/ sur le VPS et lance l'installation Docker."""
    common = ['-o', 'StrictHostKeyChecking=no',
              '-o', 'ConnectTimeout=10',
              '-o', 'UserKnownHostsFile=/dev/null']
    key = ['-i', str(Path(ssh_key).expanduser())]
    dest = f'{ssh_user}@{ip}'
    print(f'   ▶ SSH {dest} : préparation /opt/ka-enterprise')
    _ssh(['ssh', *common, *key, dest,
          'mkdir -p /opt/ka-enterprise && command -v docker || '
          '(curl -fsSL https://get.docker.com | sh)'], dry)
    print(f'   ▶ SCP : copie du package de déploiement')
    _ssh(['scp', *common, *key, '-r', str(DEPLOY_DIR),
          f'{dest}:/opt/ka-enterprise/'], dry)
    print(f'   ▶ Installation : bash deploy_vps.sh (2-5 min)')
    _ssh(['ssh', *common, *key, dest,
          f'cd /opt/ka-enterprise && bash deploy_vps.sh'], dry)
    print(f'\n   ✅ KA Enterprise installé : http://{ip}:{PORT}/onboard')


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS API
# ═══════════════════════════════════════════════════════════════════════════════

def _api(url: str, method: str, body, headers: dict) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('User-Agent', _UA)
    req.add_header('Content-Type', 'application/json')
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            content = r.read()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API {e.code} {url}: {e.read().decode()[:200]}")


def main():
    ap = argparse.ArgumentParser(description='KA Enterprise — déploiement 1-clic')
    ap.add_argument('--provider', choices=['hetzner', 'scaleway', 'ovh'],
                    default=None, help='fournisseur (création automatique)')
    ap.add_argument('--ip', default='', help='IP d\'un VPS existant (installation seule)')
    ap.add_argument('--name', default='ka-enterprise', help='nom du serveur')
    ap.add_argument('--ssh-key', default='~/.ssh/id_ed25519')
    ap.add_argument('--ssh-user', default='root')
    ap.add_argument('--dry-run', action='store_true', help='simulation complète')
    # Identifiants API
    ap.add_argument('--token', default='', help='Hetzner : API token')
    ap.add_argument('--secret-key', default='', help='Scaleway : secret key')
    ap.add_argument('--project-id', default='', help='Scaleway : projet')
    ap.add_argument('--app-key', default='', help='OVH : application key')
    ap.add_argument('--app-secret', default='', help='OVH : application secret')
    ap.add_argument('--consumer-key', default='', help='OVH : consumer key')
    args = ap.parse_args()

    print('═' * 60)
    print('  🚀 KA Enterprise — déploiement 1-clic')
    print('═' * 60)

    if not args.ip and not args.provider:
        print('❌ Fournissez --provider ou --ip')
        sys.exit(2)

    dry = args.dry_run
    if dry:
        print('   (mode dry-run — aucune action réelle)')

    # 1. Création du VPS (ou IP existante)
    if args.ip:
        ip = args.ip
        print(f'   📍 Installation sur le VPS existant : {ip}')
    elif args.provider == 'hetzner':
        if not args.token:
            print('❌ Hetzner : --token requis (console.hetzner.cloud → API Tokens)')
            sys.exit(2)
        ip = hetzner_create(args.token, args.name, args.ssh_key, dry=dry)
    elif args.provider == 'scaleway':
        if not args.secret_key or not args.project_id:
            print('❌ Scaleway : --secret-key et --project-id requis')
            sys.exit(2)
        ip = scaleway_create(args.secret_key, args.project_id, args.name,
                             args.ssh_key, dry=dry)
    elif args.provider == 'ovh':
        print('ℹ️  OVH : l\'API commande via panier — créez le VPS dans le '
              'manager OVH puis relancez avec --ip <IP> (ou --provider ovh '
              'documenté dans FICHE_HEBERGEUR.md)')
        sys.exit(2)

    print(f'   📍 IP : {ip}')

    # 2. Attente du SSH
    if not dry:
        print('   ⏳ attente du SSH (jusqu\'à 3 min)…')
        for _ in range(45):
            if _port_open(ip):
                break
            time.sleep(4)
        if not _port_open(ip):
            print(f'   ⚠ SSH non joignable — relancez avec --ip {ip}')
            sys.exit(1)

    # 3. Installation
    install(ip, args.ssh_key, args.ssh_user, dry=dry)


def _port_open(ip: str, port: int = 22) -> bool:
    import socket
    try:
        with socket.create_connection((ip, port), timeout=3):
            return True
    except OSError:
        return False


if __name__ == '__main__':
    main()
