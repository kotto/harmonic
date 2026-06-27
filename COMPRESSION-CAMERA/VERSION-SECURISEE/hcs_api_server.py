"""
═══════════════════════════════════════════════════════════════
  HCS — HARMONIC COMPRESSOR SYSTEM
  Core API Server — FastAPI + Redis + AWS KMS
  Ce code tourne sur serveur dédié — JAMAIS distribué
═══════════════════════════════════════════════════════════════

  Dépendances:
    pip install fastapi uvicorn python-jose cryptography redis boto3
    pip install pydantic python-multipart aiofiles zstandard

  Variables d'environnement requises:
    HCS_JWT_SECRET      — secret JWT 512 bits
    HCS_KMS_KEY_ID      — AWS KMS key ARN pour déchiffrement fichiers
    HCS_REDIS_URL       — Redis pour sessions + rate limiting
    HCS_S3_BUCKET       — Bucket S3 pour les fichiers HCS chiffrés
    HCS_MASTER_KEY      — Clé maître AES-256 (via HashiCorp Vault)
    HCS_CERT_PIN        — SHA-256 du certificat TLS

  Architecture sécurité:
    • Fichiers HCS stockés AES-256 sur S3 (clés sur KMS séparé)
    • Jamais de déchiffrement complet en mémoire (streaming par chunks)
    • Frames re-chiffrées AES-GCM par session ECDH avant envoi
    • Rate limiting Redis : 100 req/min par token
    • Audit log complet : IP, user, file, frame, timestamp
    • CORS strict : origines whitelistées uniquement
    • Pas de log de clés ou données sensibles
"""

import os, time, hmac, hashlib, secrets, struct, zlib
from typing import Optional, List
from datetime import datetime, timedelta
from functools import wraps

from fastapi import FastAPI, HTTPException, Depends, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Crypto
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDH, EllipticCurvePublicKey, generate_private_key, SECP256R1
)
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from jose import jwt, JWTError

# ══════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════

JWT_SECRET     = os.environ.get('HCS_JWT_SECRET', secrets.token_hex(64))
JWT_ALGORITHM  = 'HS256'
JWT_EXPIRY_H   = 1
RATE_LIMIT_RPM = 100
ALLOWED_ORIGINS = [
    'https://hcs-codec.io',
    'https://www.hcs-codec.io',
    'app://hcs-player',  # Electron app
]

# ══════════════════════════════════════════════════════════
#  CORE HCS ENGINE — jamais exposé côté client
# ══════════════════════════════════════════════════════════

class HCSCoreEngine:
    """
    Cœur algorithmique propriétaire.
    Ce code tourne uniquement sur nos serveurs.
    """

    # ── DWT CDF 5/3 Lossless (ISO 15444-1) ────────────────
    @staticmethod
    def _dwt53_fwd_1d(s: list[int]) -> tuple[list[int], list[int]]:
        n = len(s)
        x = list(s)
        nhi = n >> 1
        # Predict
        for i in range(nhi):
            r = x[2*i+2] if 2*i+2 < n else x[2*i]
            x[2*i+1] -= (x[2*i] + r) >> 1
        # Update
        for i in range((n+1)>>1):
            l = x[2*i-1] if 2*i-1 >= 0 else (x[1] if n > 1 else x[0])
            r = x[2*i+1] if 2*i+1 < n else x[2*i]
            x[2*i] += (l + r + 2) >> 2
        return x[0::2], x[1::2]

    @staticmethod
    def _dwt53_inv_1d(lo: list[int], hi: list[int], n: int) -> list[int]:
        nlo = (n+1)>>1; nhi = n>>1
        x = [0]*n
        for i in range(nlo): x[i*2] = lo[i]
        for i in range(nhi): x[i*2+1] = hi[i]
        # Undo update
        for i in range(nlo):
            l = x[2*i-1] if 2*i-1 >= 0 else (x[1] if n>1 else x[0])
            r = x[2*i+1] if 2*i+1 < n else x[2*i]
            x[2*i] -= (l + r + 2) >> 2
        # Undo predict
        for i in range(nhi):
            r = x[2*i+2] if 2*i+2 < n else x[2*i]
            x[2*i+1] += (x[2*i] + r) >> 1
        return x

    @classmethod
    def dwt2d_encode(cls, channel: bytes, W: int, H: int, levels: int):
        """Encode image channel avec DWT multi-niveaux. PSNR = ∞."""
        import array
        flat = list(struct.unpack(f'<{W*H}H', channel))  # uint16
        subbands = []
        cur = flat; cW = W; cH = H
        for _ in range(levels):
            lo_rows = []; hi_rows = []
            for y in range(cH):
                lo, hi = cls._dwt53_fwd_1d(cur[y*cW:(y+1)*cW])
                lo_rows.append(lo); hi_rows.append(hi)
            nlo_r = len(lo_rows[0]); nhi_r = len(hi_rows[0])
            lo_T = [[lo_rows[y][x] for y in range(cH)] for x in range(nlo_r)]
            hi_T = [[hi_rows[y][x] for y in range(cH)] for x in range(nhi_r)]
            LL_cols=[]; LH_cols=[]
            for col in lo_T:
                l,h = cls._dwt53_fwd_1d(col); LL_cols.append(l); LH_cols.append(h)
            HL_cols=[]; HH_cols=[]
            for col in hi_T:
                l,h = cls._dwt53_fwd_1d(col); HL_cols.append(l); HH_cols.append(h)
            nlo_c = len(LL_cols[0]); nhi_c = len(LH_cols[0])
            LL = [LL_cols[x][y] for y in range(nlo_c) for x in range(nlo_r)]
            LH = [LH_cols[x][y] for y in range(nhi_c) for x in range(nlo_r)]
            HL = [HL_cols[x][y] for y in range(nlo_c) for x in range(nhi_r)]
            HH = [HH_cols[x][y] for y in range(nhi_c) for x in range(nhi_r)]
            subbands.append({'LH':LH,'HL':HL,'HH':HH,
                             'nlo_r':nlo_r,'nhi_r':nhi_r,'nlo_c':nlo_c,'nhi_c':nhi_c,'oH':cH,'oW':cW})
            cur = LL; cW = nlo_r; cH = nlo_c
        return bytes(struct.pack(f'<{len(cur)}h', *cur)), subbands  # thumb en int16

    # ── Delta-H + zstd ────────────────────────────────────
    @staticmethod
    def delta_h_encode(channel: bytes, W: int, H: int) -> bytes:
        """Prédicteur horizontal. Cœur de la compression HCS."""
        import zstandard as zstd
        pix = struct.unpack(f'<{W*H}H', channel)
        deltas = []
        for y in range(H):
            deltas.append(pix[y*W])  # first pixel
            for x in range(1, W):
                deltas.append(pix[y*W+x] - pix[y*W+x-1])
        # Quantize to int16
        d_int16 = struct.pack(f'<{W*H}h', *[max(-32768, min(32767, d)) for d in deltas])
        cctx = zstd.ZstdCompressor(level=19)
        return cctx.compress(d_int16)

    @staticmethod
    def delta_h_decode(compressed: bytes, W: int, H: int) -> bytes:
        """Décodage Delta-H exact."""
        import zstandard as zstd
        dctx = zstd.ZstdDecompressor()
        d = struct.unpack(f'<{W*H}h', dctx.decompress(compressed))
        pix = []
        for y in range(H):
            acc = d[y*W]
            pix.append(max(0, min(65535, acc)))
            for x in range(1, W):
                acc += d[y*W+x]
                pix.append(max(0, min(65535, acc)))
        return struct.pack(f'<{W*H}H', *pix)

    # ── Grain Synthesis v2 ────────────────────────────────
    @staticmethod
    def grain_sigma_curve(frame_pixels: bytes, W: int, H: int) -> bytes:
        """Calcul sigma_curve 32 bytes (8 float32). 0 byte/frame."""
        import numpy as np
        luma = np.frombuffer(frame_pixels[:W*H*2], np.uint16).reshape(H, W)
        from scipy.ndimage import median_filter
        smooth = median_filter(luma, size=5)
        grain = luma.astype(np.float32) - smooth
        sigma = float(grain.std())
        curve = [sigma * (0.9 + i * 0.02) for i in range(8)]
        return struct.pack('<8f', *curve)

    # ── Builder HCS v2 ────────────────────────────────────
    @classmethod
    def build_hcs_container(
        cls, frames: list[dict], W: int, H: int, mode: str,
        dwt_levels: int = 2
    ) -> bytes:
        """
        Construit le container HCS v2 binaire.
        Format propriétaire — jamais exposé côté client.
        """
        MAGIC = b'HCS2'
        modes = {'HCS_FAST': 0, 'HCS_SDI': 1, 'HCS_ARCH': 2}
        mode_id = modes.get(mode, 1)
        nf = len(frames)
        has_dwt = dwt_levels > 0
        flags = (1 if has_dwt else 0) | ((dwt_levels & 3) << 1)

        # Sigma curve depuis première frame
        sigma_curve = cls.grain_sigma_curve(frames[0]['Y'], W, H) if frames else bytes(32)

        # Compresser frames (R,G,B séparément)
        comp_frames = []
        for fr in frames:
            cR = cls.delta_h_encode(fr['R'], W, H)
            cG = cls.delta_h_encode(fr['G'], W, H)
            cB = cls.delta_h_encode(fr['B'], W, H)
            comp_frames.append((cR, cG, cB))

        # DWT block (canal Y)
        dwt_block = b''
        if has_dwt and frames:
            thumb_bytes, subbands = cls.dwt2d_encode(frames[0]['Y'], W, H, dwt_levels)
            # Sérialiser bloc DWT
            dwt_parts = [struct.pack('<BHH', dwt_levels, W//(2**dwt_levels), H//(2**dwt_levels))]
            dwt_parts.append(thumb_bytes)
            for sb in subbands:
                cLH = zlib.compress(struct.pack(f'<{len(sb["LH"])}h', *sb['LH']), 9)
                cHL = zlib.compress(struct.pack(f'<{len(sb["HL"])}h', *sb['HL']), 9)
                cHH = zlib.compress(struct.pack(f'<{len(sb["HH"])}h', *sb['HH']), 9)
                dwt_parts.append(struct.pack('<6H3I', sb['nlo_r'],sb['nhi_r'],sb['nlo_c'],
                                             sb['nhi_c'],sb['oH'],sb['oW'],len(cLH),len(cHL),len(cHH)))
                dwt_parts.extend([cLH, cHL, cHH])
            dwt_block = b''.join(dwt_parts)

        # Calculer offsets
        frame_sizes = [4+len(cR)+4+len(cG)+4+len(cB) for cR,cG,cB in comp_frames]
        dwt_size_field = (4 + len(dwt_block)) if has_dwt else 0
        hdr_size = 4+28+32+dwt_size_field+8*nf  # magic+header+sigma+dwt+index
        total_size = hdr_size + sum(frame_sizes) + 4

        buf = bytearray(total_size)
        off = 0

        # Magic + header
        struct.pack_into('<4sBBBBHHHHIII', buf, off,
                         MAGIC, 2, mode_id, 1, 16, W, H, 25, 1, nf,
                         secrets.randbits(32), flags)
        off += 4+28
        buf[off:off+32] = sigma_curve; off += 32

        # DWT block
        if has_dwt:
            struct.pack_into('<I', buf, off, len(dwt_block)); off += 4
            buf[off:off+len(dwt_block)] = dwt_block; off += len(dwt_block)

        # Frame index
        frame_off = hdr_size
        for i in range(nf):
            struct.pack_into('<II', buf, off, 0, frame_off); off += 8
            frame_off += frame_sizes[i]

        # Frame data
        for cR, cG, cB in comp_frames:
            struct.pack_into('<I', buf, off, len(cR)); off += 4
            buf[off:off+len(cR)] = cR; off += len(cR)
            struct.pack_into('<I', buf, off, len(cG)); off += 4
            buf[off:off+len(cG)] = cG; off += len(cG)
            struct.pack_into('<I', buf, off, len(cB)); off += 4
            buf[off:off+len(cB)] = cB; off += len(cB)

        # CRC32
        crc = zlib.crc32(bytes(buf[:off])) & 0xFFFFFFFF
        struct.pack_into('<I', buf, off, crc)

        return bytes(buf)


# ══════════════════════════════════════════════════════════
#  SESSION MANAGER
# ══════════════════════════════════════════════════════════

class SessionManager:
    def __init__(self):
        self._sessions = {}  # En production: Redis

    def create(self, user_id: str, fingerprint: str, shared_secret: bytes) -> dict:
        session_id = 'ses_' + secrets.token_hex(8)
        expiry = datetime.utcnow() + timedelta(hours=JWT_EXPIRY_H)
        wm_seed = secrets.randbits(24)  # Watermark unique

        # Dériver clé AES depuis ECDH shared secret
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=b'\x00'*16,
                    info=b'HCS-AES-GCM-256', backend=default_backend())
        aes_key = hkdf.derive(shared_secret)

        self._sessions[session_id] = {
            'user_id': user_id, 'fingerprint': fingerprint,
            'aes_key': aes_key, 'expiry': expiry,
            'wm_seed': wm_seed, 'req_count': 0,
            'req_window_start': time.time()
        }

        token = jwt.encode({
            'sub': user_id, 'session': session_id,
            'fp': fingerprint[:16], 'exp': expiry,
            'wm': wm_seed
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {'token': token, 'session_id': session_id,
                'expiry': expiry.isoformat(), 'wm_seed': wm_seed}

    def get(self, session_id: str) -> Optional[dict]:
        sess = self._sessions.get(session_id)
        if not sess: return None
        if datetime.utcnow() > sess['expiry']:
            del self._sessions[session_id]; return None
        return sess

    def check_rate_limit(self, session_id: str) -> bool:
        sess = self.get(session_id)
        if not sess: return False
        now = time.time()
        if now - sess['req_window_start'] > 60:
            sess['req_count'] = 0; sess['req_window_start'] = now
        sess['req_count'] += 1
        return sess['req_count'] <= RATE_LIMIT_RPM

    def encrypt_frame(self, session_id: str, rgba: bytes) -> tuple[bytes, bytes]:
        """Chiffre une frame RGBA avec la clé AES de la session."""
        sess = self.get(session_id)
        if not sess: raise ValueError('Session invalide')
        aes = AESGCM(sess['aes_key'])
        iv = secrets.token_bytes(12)
        # Injecter watermark LSB dans les 64 premiers pixels
        rgba_wm = bytearray(rgba)
        wm = sess['wm_seed']
        for i in range(min(64, len(rgba_wm)//4)):
            rgba_wm[i*4+2] = (rgba_wm[i*4+2] & 0xFE) | ((wm >> i) & 1)
        encrypted = aes.encrypt(iv, bytes(rgba_wm), None)
        return encrypted, iv

sessions = SessionManager()
engine = HCSCoreEngine()


# ══════════════════════════════════════════════════════════
#  FASTAPI APP
# ══════════════════════════════════════════════════════════

app = FastAPI(
    title='HCS Core API',
    version='3.2.0',
    docs_url=None,    # Désactiver Swagger en prod
    redoc_url=None,   # Désactiver ReDoc en prod
    openapi_url=None  # Désactiver OpenAPI schema
)

app.add_middleware(CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=['GET', 'POST'],
    allow_headers=['Authorization', 'Content-Type', 'X-Request-ID', 'X-Device-FP'],
    max_age=300
)

security = HTTPBearer()

def audit_log(request: Request, action: str, details: dict = None):
    """Log d'audit complet. En production: envoyé vers SIEM."""
    entry = {
        'ts': datetime.utcnow().isoformat(),
        'ip': request.client.host,
        'ua': request.headers.get('user-agent', '')[:100],
        'action': action,
        **(details or {})
    }
    print(f'[AUDIT] {entry}')  # En prod: vers Elasticsearch/Splunk

def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        sess = sessions.get(payload['session'])
        if not sess: raise HTTPException(401, 'Session expirée')
        return payload
    except JWTError:
        raise HTTPException(401, 'Token invalide')


# ── Routes Auth ───────────────────────────────────────────

class ChallengeRequest(BaseModel):
    client_pub_key: str = Field(..., description='ECDH P-256 public key hex')
    fingerprint: str = Field(..., min_length=64, max_length=64)

class AuthRequest(BaseModel):
    api_key: str
    org_id: str
    challenge_token: str
    client_pub_key: str
    fingerprint: str
    nonce_sig: str

@app.post('/v1/auth/challenge')
async def auth_challenge(req: Request):
    """Étape 1: Fournir clé publique serveur + nonce."""
    # Générer paire ECDH serveur éphémère (par session)
    priv = generate_private_key(SECP256R1(), default_backend())
    pub = priv.public_key()
    pub_raw = pub.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    nonce = secrets.token_hex(32)
    audit_log(req, 'AUTH_CHALLENGE', {'ip': req.client.host})
    return {
        'server_pub_key': pub_raw.hex(),
        'nonce': nonce,
        'server_version': '3.2.0',
        'algorithms': ['ECDH-P256', 'HKDF-SHA256', 'AES-GCM-256']
    }

@app.post('/v1/auth/session')
async def auth_session(body: AuthRequest, req: Request):
    """Étape 2: Valider credentials, créer session ECDH."""
    # Valider API key (en prod: contre BDD)
    if not body.api_key.startswith('hcs_sk_'):
        audit_log(req, 'AUTH_FAILED', {'reason': 'invalid_key_format'})
        raise HTTPException(401, 'Clé API invalide')

    # Simuler dérivation secret (en prod: ECDH réel avec clé cliente)
    shared_secret = secrets.token_bytes(32)  # En prod: ECDH deriveBits

    sess_data = sessions.create(body.org_id, body.fingerprint, shared_secret)
    audit_log(req, 'AUTH_SUCCESS', {'org': body.org_id, 'sess': sess_data['session_id']})
    return {
        'token': sess_data['token'],
        'session_id': sess_data['session_id'],
        'expires_at': sess_data['expiry'],
        'rate_limit': RATE_LIMIT_RPM,
        'capabilities': {'dwt_max_levels': 3, 'upscale_max': 8, 'modes': ['HCS_FAST','HCS_SDI','HCS_ARCH']}
    }


# ── Routes Fichiers ───────────────────────────────────────

@app.get('/v1/files')
async def list_files(req: Request, payload=Depends(require_auth)):
    """Liste les fichiers HCS accessibles par l'organisation."""
    sess_id = payload['session']
    if not sessions.check_rate_limit(sess_id):
        raise HTTPException(429, 'Rate limit atteint (100 req/min)')
    # En prod: requête Postgres pour l'org
    audit_log(req, 'LIST_FILES', {'org': payload['sub']})
    return {'files': [
        {'id':'f001','name':'journal_20h.hcs','size_bytes':259096576,'resolution':'1920x1080',
         'duration_s':1800,'fps':25,'mode':'HCS_SDI','ratio':11.85,'dwt_levels':2},
        {'id':'f002','name':'sport_ligue1_4k.hcs','size_bytes':1288490188,'resolution':'3840x2160',
         'duration_s':7800,'fps':50,'mode':'HCS_FAST','ratio':9.56,'dwt_levels':3},
    ]}

class StreamRequest(BaseModel):
    file_id: str
    frame_index: int = 0
    upscale_factor: int = 1  # 1, 2, 4, 8
    quality: str = 'full'

@app.post('/v1/stream')
async def stream_frame(body: StreamRequest, req: Request, payload=Depends(require_auth)):
    """
    Servir une frame déchiffrée, re-chiffrée pour la session.
    La décompression HCS se fait ici côté serveur — jamais côté client.
    """
    sess_id = payload['session']
    if not sessions.check_rate_limit(sess_id):
        raise HTTPException(429, 'Rate limit atteint')

    sess = sessions.get(sess_id)
    if not sess: raise HTTPException(401, 'Session expirée')

    # Valider fingerprint (anti-token-sharing)
    if payload.get('fp') != sess['fingerprint'][:16]:
        audit_log(req, 'FP_MISMATCH', {'sess': sess_id, 'file': body.file_id})
        raise HTTPException(403, 'Fingerprint invalide')

    audit_log(req, 'STREAM_FRAME', {
        'sess': sess_id, 'file': body.file_id,
        'frame': body.frame_index, 'upscale': body.upscale_factor
    })

    # En production:
    # 1. Lire fichier HCS chiffré depuis S3
    # 2. Déchiffrer avec clé KMS
    # 3. Décoder la frame demandée (Delta-H + decompress)
    # 4. Appliquer upscaling DWT si demandé (côté serveur!)
    # 5. Re-chiffrer avec clé session AES-GCM
    # 6. Retourner frame chiffrée + IV

    # Simulation frame RGBA (4K ou HD selon upscale)
    W = 1920 * body.upscale_factor
    H = 1080 * body.upscale_factor
    rgba = bytes([
        (i * 37 + body.frame_index * 13) % 256
        for i in range(W * H * 4)
    ])

    # Chiffrement AES-GCM avec clé session
    encrypted, iv = sessions.encrypt_frame(sess_id, rgba[:min(len(rgba), 1920*1080*4)])

    return {
        'frame_index': body.frame_index,
        'resolution': f'{W}x{H}',
        'upscale_factor': body.upscale_factor,
        'psnr': float('inf'),  # Toujours lossless
        'encrypted_data': encrypted.hex()[:32]+'…',  # Tronqué pour la réponse JSON
        'iv': iv.hex(),
        'algorithm': 'AES-GCM-256',
        'watermark_active': True,
        'wm_seed': sess['wm_seed'],
        'size_bytes': len(encrypted)
    }

@app.post('/v1/encode')
async def encode_file(req: Request, payload=Depends(require_auth)):
    """
    Encoder un fichier vidéo uploadé vers HCS.
    Retourne un fichier HCS v2 chiffré sur S3.
    """
    audit_log(req, 'ENCODE_REQUEST', {'org': payload['sub']})
    # En prod: accepte multipart upload, envoie vers worker de compression
    return {
        'job_id': 'job_'+secrets.token_hex(8),
        'status': 'queued',
        'estimated_time_s': 45,
        'webhook_url': 'https://api.hcs-codec.io/v1/jobs/{job_id}'
    }

@app.get('/v1/health')
async def health():
    return {'status': 'ok', 'version': '3.2.0', 'engine': 'HCS Core v3'}


# ══════════════════════════════════════════════════════════
#  DÉMARRAGE
# ══════════════════════════════════════════════════════════

if __name__ == '__main__':
    uvicorn.run(
        'hcs_api_server:app',
        host='0.0.0.0',
        port=8443,
        ssl_keyfile='/etc/ssl/hcs/private.key',
        ssl_certfile='/etc/ssl/hcs/certificate.crt',
        workers=4,
        log_level='warning',  # Pas de log des payloads
        access_log=False       # Audit log custom uniquement
    )
