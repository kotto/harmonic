# Stratégie de Déploiement HCV PRO sur Vercel

## Architecture Cible

```
┌─────────────────────────────────────────────────────────────┐
│                    Vercel Frontend (Static)                 │
│  • HTML/CSS/JS minifiés                                     │
│  • Headers de sécurité (CSP, HSTS, etc.)                    │
│  • Interface légère (10-20% du code original)               │
│  • Consomme l'API distante                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend API (Serveur dédié)                │
│  • Flask/Python (hcv_pro_server.py)                        │
│  • Code Python protégé (pas accessible au frontend)         │
│  • Endpoints: /api/compress, /api/video-boost, etc.        │
│  • WebAssembly pour codecs critiques (futur)                │
└─────────────────────────────────────────────────────────────┘
```

## Étapes de Déploiement

### Phase 1: Minification Frontend

#### 1.1 Minifier le JavaScript
```bash
# Installer terser
npm install -g terser

# Minifier le HTML avec JS intégré
npx terser web/templates/hcv_pro.html \
  --compress --mangle \
  --output web/templates/hcv_pro.min.html
```

#### 1.2 Ajouter Headers de Sécurité
```python
# Dans hcv_pro_server.py
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' cdn.tailwindcss.com; img-src 'self' data:; font-src 'self' data:; connect-src 'self' https://your-api-domain.com;"
    return response
```

### Phase 2: Frontend Léger

#### 2.1 Extraire le JavaScript
Créer un fichier JS externe:
```javascript
// web/static/app.min.js
// Code minifié extrait du HTML
```

#### 2.2 Simplifier le HTML
```html
<!-- web/templates/index.html (frontend léger) -->
<!DOCTYPE html>
<html>
<head>
  <title>HCV PRO</title>
  <script src="/static/app.min.js"></script>
</head>
<body>
  <div id="app"></div>
</body>
</html>
```

### Phase 3: Backend API

#### 3.1 Déployer le Backend Séparément
Options:
- **Vercel Serverless Functions** (recommandé)
- **Railway/Render** (conteneur Docker)
- **Heroku** (simple)

#### 3.2 Structure Vercel Serverless
```
api/
├── compress/
│   └── index.py (endpoint /api/compress)
├── video-boost/
│   └── index.py (endpoint /api/video-boost)
├── decode-hcvb/
│   └── index.py (endpoint /api/decode-hcvb)
└── history/
    └── index.py (endpoint /api/history)
```

### Phase 4: WebAssembly (Futur)

#### 4.1 Compiler le Codec en WebAssembly
```bash
# Utiliser Emscripten pour compiler Python en WebAssembly
# Ou compiler le codec HCV directement en C++ → WASM
```

#### 4.2 Intégrer WASM
```javascript
// web/static/wasm-codec.js
const codec = await WebAssembly.instantiateStreaming(fetch('/static/hcv_codec.wasm'));
```

## Déploiement Vercel

### 1. Créer `vercel.json`
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/**/*.py",
      "use": "@vercel/python"
    },
    {
      "src": "web/templates/*.html",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/web/templates/$1"
    }
  ]
}
```

### 2. Déployer
```bash
cd HCV-PRO-PROJECT
vercel
```

## Sécurité

### Headers à Ajouter
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: ...
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: ...
```

### Protection du Code
1. **Backend**: Code Python protégé (serveur)
2. **Frontend**: Minification + obfuscation
3. **API**: Authentification (JWT/API keys)
4. **WASM**: Code binaire (futur)

## Estimation de Réduction Taille

| Composant | Avant | Après | Réduction |
|-----------|-------|-------|-----------|
| HTML | 150 KB | 80 KB | 47% |
| JS | 200 KB | 120 KB | 40% |
| CSS | 50 KB | 30 KB | 40% |
| **Total** | 400 KB | 230 KB | **43%** |

## Prochaines Étapes

1. ✅ Minifier le JavaScript
2. ✅ Ajouter headers de sécurité
3. ✅ Extraire le frontend léger
4. ⏳ Déployer backend sur Vercel Serverless
5. ⏳ Compiler codecs en WebAssembly
6. ⏳ Ajouter authentification API
