"""
License management — création et validation de licences HMAC.

Format de licence (Base64URL):
  HEADER (1 byte) | VERSION (1 byte)
  CUSTOMER_ID (8 bytes)         — identifiant client
  FINGERPRINT (16 bytes)        — empreinte machine bindée
  EXPIRY (8 bytes, uint64)      — timestamp UNIX d'expiration
  FEATURES (4 bytes, uint32)    — bitmask features activées
  HMAC-SHA256 (32 bytes)        — signature

Sécurité:
  - HMAC empêche tampering (modification → invalidation).
  - Fingerprint bind la licence à la machine (pas de copie).
  - Master secret jamais exposé côté client (utilisé uniquement à la génération).
  - Vérification 100% offline (pas de phone-home).
"""

import hmac
import hashlib
import struct
import base64
import time
import os
from dataclasses import dataclass
from typing import Optional


HEADER = 0x48  # 'H' for HCV
VERSION = 1
LICENSE_SIZE = 1 + 1 + 8 + 16 + 8 + 4 + 32  # = 70 bytes


# Features bitmap
FEATURE_PRO_CODEC      = 1 << 0
FEATURE_VIDEO_BOOST    = 1 << 1
FEATURE_4K_SUPPORT     = 1 << 2
FEATURE_8K_SUPPORT     = 1 << 3
FEATURE_BATCH_API      = 1 << 4
FEATURE_PRIORITY_QUEUE = 1 << 5
FEATURE_WHITE_LABEL    = 1 << 6
FEATURE_ALL = 0xFFFFFFFF


@dataclass
class License:
    customer_id: int
    fingerprint: str
    expiry_ts: int
    features: int

    def has_feature(self, feature: int) -> bool:
        return bool(self.features & feature)

    def is_expired(self, now_ts: int = None) -> bool:
        return (now_ts or int(time.time())) >= self.expiry_ts

    def days_remaining(self) -> int:
        return max(0, (self.expiry_ts - int(time.time())) // 86400)


class LicenseError(Exception):
    pass


def _hmac(secret: bytes, data: bytes) -> bytes:
    return hmac.new(secret, data, hashlib.sha256).digest()


def generate_license(secret: bytes, customer_id: int, fingerprint: str,
                     valid_days: int = 365, features: int = FEATURE_ALL) -> str:
    """Génère une licence signée. À exécuter UNIQUEMENT côté serveur de licence.

    Args:
        secret: master secret (32+ bytes, jamais distribué)
        customer_id: ID client (visible)
        fingerprint: empreinte machine cible (32 hex chars)
        valid_days: durée de validité
        features: bitmask features autorisées
    """
    if len(secret) < 32:
        raise ValueError("Secret must be >= 32 bytes")
    if len(fingerprint) != 32:
        raise ValueError("Fingerprint must be 32 hex chars")

    fp_bytes = bytes.fromhex(fingerprint)
    expiry = int(time.time()) + valid_days * 86400

    payload = struct.pack(
        '<BBQ16sQI',
        HEADER, VERSION, customer_id, fp_bytes, expiry, features,
    )
    sig = _hmac(secret, payload)
    raw = payload + sig
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def verify_license(license_str: str, secret: bytes,
                   current_fingerprint: str) -> License:
    """Vérifie une licence. Lance LicenseError si invalide.

    Vérifications:
      1. Format / décodage Base64
      2. Signature HMAC
      3. Empreinte machine = empreinte de la licence
      4. Pas expirée
    """
    # Reconstruct padding
    padded = license_str + '=' * (-len(license_str) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded)
    except Exception:
        raise LicenseError("Invalid license format")

    if len(raw) != LICENSE_SIZE:
        raise LicenseError(f"Invalid license size: {len(raw)} (expected {LICENSE_SIZE})")

    payload, sig = raw[:-32], raw[-32:]
    expected = _hmac(secret, payload)
    if not hmac.compare_digest(sig, expected):
        raise LicenseError("License signature invalid (tampered or wrong secret)")

    header, ver, cust_id, fp_bytes, expiry, features = struct.unpack('<BBQ16sQI', payload)
    if header != HEADER:
        raise LicenseError("Invalid header")
    if ver != VERSION:
        raise LicenseError(f"Unsupported version: {ver}")

    fp_hex = fp_bytes.hex()
    if fp_hex != current_fingerprint:
        raise LicenseError(
            f"License bound to different machine "
            f"(expected fp {fp_hex[:8]}..., got {current_fingerprint[:8]}...)"
        )

    if int(time.time()) >= expiry:
        raise LicenseError(f"License expired on {time.ctime(expiry)}")

    return License(cust_id, fp_hex, expiry, features)


def load_license_from_file(path: str = None) -> Optional[str]:
    """Charge la licence depuis env var ou fichier."""
    if not path:
        path = os.environ.get('HCV_LICENSE_FILE', 'license.key')
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return os.environ.get('HCV_LICENSE_KEY')


# ─── Self-test ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Demo: generate + verify with the same machine
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hardware import get_fingerprint

    SECRET = b'\x00' * 32 + b'demo-secret-do-not-use-in-production'[:32]

    fp = get_fingerprint()
    lic = generate_license(SECRET, customer_id=42, fingerprint=fp,
                           valid_days=30, features=FEATURE_ALL)

    print(f"Generated license ({len(lic)} chars):\n  {lic}\n")

    verified = verify_license(lic, SECRET, fp)
    print(f"Verified: customer={verified.customer_id}, "
          f"days_left={verified.days_remaining()}, "
          f"4K={verified.has_feature(FEATURE_4K_SUPPORT)}")

    # Tampering test
    bad = lic[:-5] + 'XXXXX'
    try:
        verify_license(bad, SECRET, fp)
    except LicenseError as e:
        print(f"\n[OK] Tampered license rejected: {e}")

    # Wrong machine test
    try:
        verify_license(lic, SECRET, 'a' * 32)
    except LicenseError as e:
        print(f"[OK] Wrong machine rejected: {e}")
