"""
Hardware fingerprinting — empreinte machine pour binding licence.

Combine: MAC + CPU info + machine_id + hostname → SHA256 16 bytes.
"""

import hashlib
import platform
import uuid
import os
import subprocess


def _safe_run(cmd: list, timeout: float = 2.0) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
        return (r.stdout + r.stderr).strip()
    except Exception:
        return ""


def get_machine_id() -> str:
    """Identifiant stable de la machine (Linux: /etc/machine-id, Windows: registry)."""
    if os.name == 'posix':
        for path in ['/etc/machine-id', '/var/lib/dbus/machine-id']:
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        return f.read().strip()
                except Exception:
                    pass
        return _safe_run(['hostid']) or 'unknown'
    elif os.name == 'nt':
        out = _safe_run(['wmic', 'csproduct', 'get', 'UUID'])
        for line in out.splitlines():
            line = line.strip()
            if line and 'UUID' not in line:
                return line
        return 'unknown'
    return 'unknown'


def get_mac_address() -> str:
    """Première adresse MAC stable (non-locale)."""
    try:
        mac = uuid.getnode()
        # uuid.getnode() retourne un MAC random si introuvable; bit 0x10000000000 = aléatoire
        if (mac >> 40) & 0x01:
            return '000000000000'
        return f'{mac:012x}'
    except Exception:
        return '000000000000'


def get_cpu_signature() -> str:
    """Identifiant CPU (modèle + nombre de cœurs)."""
    info = platform.processor() or platform.machine()
    cores = os.cpu_count() or 1
    return f'{info}|{cores}'


def get_fingerprint() -> str:
    """Empreinte machine 32 hex chars (SHA256 tronqué).

    Stable: même machine → même empreinte.
    Différente entre VM/conteneurs.
    """
    components = [
        get_machine_id(),
        get_mac_address(),
        get_cpu_signature(),
        platform.system(),
        platform.node(),
    ]
    blob = '|'.join(components).encode('utf-8')
    return hashlib.sha256(blob).hexdigest()[:32]


def get_fingerprint_components() -> dict:
    """Détail des composantes de l'empreinte (debugging)."""
    return {
        'machine_id': get_machine_id()[:16] + '...',
        'mac': get_mac_address(),
        'cpu': get_cpu_signature()[:40],
        'system': platform.system(),
        'hostname': platform.node(),
        'fingerprint': get_fingerprint(),
    }


if __name__ == '__main__':
    import json
    print(json.dumps(get_fingerprint_components(), indent=2))
