# HCV Enterprise

Compression engine "broadcast lossless" haute performance, déploiement on-premise sécurisé.

## Quick start

```bash
# Mode démo (licence simulée, dev)
HCV_DEMO_MODE=1 python3 enterprise/server/app.py
# Ouvre http://localhost:8088

# Mode production
HCV_DEMO_MODE=0 \
HCV_LICENSE_SECRET=$(cat /etc/hcv/master.secret) \
HCV_LICENSE_FILE=/etc/hcv/license.key \
gunicorn -c gunicorn_config.py enterprise.server.app:app
```

## Architecture

```
enterprise/
├── core/
│   └── tile_codec.py        # Codec optimisé strip-parallel + zstd parallèle
├── security/
│   ├── hardware.py          # Empreinte machine (machine_id + MAC + CPU)
│   ├── license.py           # Licences HMAC-signées, binding hardware
│   └── integrity.py         # Vérification SHA256 + anti-debug
├── server/
│   └── app.py               # Flask app, routes /api/v2/*
├── web/
│   ├── index.html           # Dashboard moderne (dark + glassmorphism)
│   ├── style.css            # Design system (Inter + JetBrains Mono)
│   └── app.js               # Frontend logic
└── build/
    └── build.py             # Compilation .pyc / Cython, manifest, dist
```

## Performance vs reference codec

Benchmarks 4-core CPU, frame réaliste avec grain SDI 1 % :

| Résolution | HCV PRO (référence) | HCV Enterprise | Gain |
|-----------|---------------------|----------------|------|
| HD 720p   | 3.3 s               | **0.19 s**     | 17×  |
| FHD 1080p | 8.1 s               | **0.40 s**     | 20×  |
| 4K 2160p  | 38 s                | **1.8 s**      | 21×  |

Optimisations clés :
1. `cv2.medianBlur` 3-canaux direct (1 appel vs 3) — gain 3×
2. zstd niveau 11 + parallélisation des canaux RGB — gain 70×
3. Strip-parallel medianBlur sur 4K+ pour saturer les cœurs

## Sécurité

### Couche 1 — Compilation
- Bytecode `.pyc` optimisé (-O2, sans assertions)
- Suppression des `.py` source dans la distribution
- Optionnel : compilation Cython `.so` (anti-décompilation forte)
  ```bash
  python3 build/build.py --cython
  ```

### Couche 2 — Licence
- Format binaire 70 bytes : header + customer_id + fingerprint + expiry + features + HMAC-SHA256
- **Binding hardware** : la licence ne fonctionne que sur la machine cible
- Vérification 100 % offline (pas de phone-home)
- Expiration + features par bitmask (PRO, 4K, 8K, Batch API…)

```python
from enterprise.security import generate_license, get_fingerprint
from enterprise.security.license import FEATURE_4K_SUPPORT, FEATURE_PRO_CODEC

key = generate_license(
    secret=master_secret_bytes,
    customer_id=42,
    fingerprint='target_machine_fp',
    valid_days=365,
    features=FEATURE_PRO_CODEC | FEATURE_4K_SUPPORT,
)
```

### Couche 3 — Intégrité
- `manifest.json` contient les SHA256 de tous les `.pyc/.so`
- Vérifié au démarrage : toute modification → `IntegrityError`
- Anti-debug optionnel (`HCV_STRICT_ANTI_DEBUG=1`) :
  - détecte `sys.settrace`
  - détecte `TracerPid` dans `/proc/self/status` (Linux)
  - détecte les variables d'environnement IDE/debugger

### Modèle de menace adressé

| Attaque                       | Mitigation                              |
|-------------------------------|------------------------------------------|
| Copie sur autre machine       | Licence bind par hardware fingerprint   |
| Modification du bytecode      | Manifest SHA256 + vérification au boot  |
| Décompilation `.pyc`          | Compilation Cython optionnelle (.so)    |
| Reverse engineering passif    | Optimisations -O2, noms inlinés         |
| Debug attach                  | Anti-debug runtime (opt-in)             |
| Tampering de la licence       | HMAC-SHA256 avec master secret          |
| Réutilisation expired licence | Expiry timestamp dans le payload signé  |

**Limite honnête :** Python est un langage interprété — un attaquant motivé avec assez de temps peut casser n'importe quelle protection. L'objectif est de rendre l'effort économiquement non rentable, pas de garantir une protection absolue.

## API

### `GET /api/v2/health`
```json
{ "status": "ok", "version": "2.0.0", "license_active": true }
```

### `GET /api/v2/fingerprint`
```json
{ "fingerprint": "14a34849ca4b3ed3a90e36d328ff5656", ... }
```

### `GET /api/v2/license`
```json
{
  "active": true, "customer_id": 42,
  "expires": "2027-04-26", "days_remaining": 365,
  "features": 79
}
```

### `POST /api/v2/license/activate`
```json
{ "key": "SAEqAAAAA...." }
```

### `POST /api/v2/compress`
```bash
curl -X POST http://localhost:8088/api/v2/compress \
  -F "file=@frame.png" \
  -F "bit_depth=12" \
  -F "zstd_level=11"
```

## Build & déploiement

### 1. Build local
```bash
python3 enterprise/build/build.py              # Bytecode (rapide)
python3 enterprise/build/build.py --cython     # Cython (production)
```
→ génère `enterprise/build/dist/` avec `manifest.json`, `.pyc`, et un nouveau master secret.

### 2. Génération de licence client
```bash
python3 -c "
from enterprise.security import generate_license
import os
secret = bytes.fromhex(os.environ['HCV_LICENSE_SECRET'])
print(generate_license(secret, customer_id=42, fingerprint='<client_fp>', valid_days=365))
"
```

### 3. Déploiement
```bash
# Sur la machine cible
export HCV_LICENSE_SECRET='<from build>'
export HCV_LICENSE_FILE=/etc/hcv/license.key
echo '<license-key>' > /etc/hcv/license.key
gunicorn -c gunicorn_config.py enterprise.server.app:app
```

## Variables d'environnement

| Variable                    | Effet                                              |
|----------------------------|-----------------------------------------------------|
| `HCV_DEMO_MODE=1`          | Licence simulée active (dev only)                   |
| `HCV_LICENSE_SECRET`       | Master secret hex (jamais distribué)                |
| `HCV_LICENSE_FILE`         | Chemin du fichier de licence                        |
| `HCV_LICENSE_KEY`          | Licence inline (alternative au fichier)             |
| `HCV_STRICT_INTEGRITY=1`   | Refuse de démarrer si manifest invalide             |
| `HCV_STRICT_ANTI_DEBUG=1`  | Refuse de démarrer si debugger détecté              |
| `HCV_MAX_UPLOAD_MB=500`    | Limite uploads (default 500 MB)                     |
