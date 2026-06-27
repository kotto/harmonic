"""
Integrity & anti-tampering checks for runtime modules.

Au démarrage, vérifie que les .pyc et .so n'ont pas été modifiés.
Détection de debugger via sys.settrace + ptrace check (Linux).
"""

import hashlib
import os
import sys
import json
from typing import Dict


class IntegrityError(Exception):
    pass


class TamperingDetected(Exception):
    pass


def hash_file(path: str) -> str:
    """SHA256 d'un fichier."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(root: str, patterns: tuple = ('.pyc', '.so', '.pyd')) -> Dict[str, str]:
    """Construit un manifeste {chemin_relatif: sha256} pour tous les fichiers ciblés."""
    manifest = {}
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not any(f.endswith(p) for p in patterns):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root)
            manifest[rel] = hash_file(full)
    return manifest


def verify_manifest(root: str, manifest: Dict[str, str]) -> None:
    """Vérifie tous les fichiers contre le manifeste; lance IntegrityError si différence."""
    for rel, expected in manifest.items():
        full = os.path.join(root, rel)
        if not os.path.exists(full):
            raise IntegrityError(f"Missing protected file: {rel}")
        actual = hash_file(full)
        if actual != expected:
            raise IntegrityError(f"Tampered file: {rel}")


def save_manifest(manifest: Dict[str, str], path: str) -> None:
    with open(path, 'w') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def load_manifest(path: str) -> Dict[str, str]:
    with open(path) as f:
        return json.load(f)


# ─── Anti-debug ─────────────────────────────────────────────────────────────

def is_debugger_attached() -> bool:
    """Détecte la présence d'un debugger Python (sys.settrace) ou ptrace (Linux)."""
    # Python tracing actif
    if sys.gettrace() is not None:
        return True

    # Linux : TracerPid dans /proc/self/status
    try:
        with open('/proc/self/status') as f:
            for line in f:
                if line.startswith('TracerPid:'):
                    pid = int(line.split()[1])
                    if pid != 0:
                        return True
                    break
    except Exception:
        pass

    # Variables d'environnement debug-related
    debug_envs = ['PYDEVD_LOAD_VALUES_ASYNC', 'PYCHARM_HOSTED', 'VSCODE_PID']
    if any(os.environ.get(v) for v in debug_envs):
        return True

    return False


def assert_no_debugger():
    """Refuse l'exécution si debugger détecté.

    Pour activer en production : os.environ['HCV_STRICT_ANTI_DEBUG'] = '1'.
    """
    if os.environ.get('HCV_STRICT_ANTI_DEBUG') == '1' and is_debugger_attached():
        raise TamperingDetected("Debugger detected — execution aborted")


# ─── Démarrage sécurisé ─────────────────────────────────────────────────────

def secure_startup(manifest_path: str = None, package_root: str = None) -> None:
    """Vérifications de démarrage : intégrité + anti-debug.

    À appeler au tout début de l'application avant tout import sensible.
    """
    assert_no_debugger()

    if manifest_path and os.path.exists(manifest_path):
        manifest = load_manifest(manifest_path)
        if package_root is None:
            package_root = os.path.dirname(os.path.abspath(manifest_path))
        verify_manifest(package_root, manifest)


if __name__ == '__main__':
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning {here} for .pyc/.so files...")
    m = build_manifest(here)
    print(f"Manifest: {len(m)} files")
    for k, v in list(m.items())[:5]:
        print(f"  {k}: {v[:16]}...")
    print(f"\nDebugger attached: {is_debugger_attached()}")
