# Architecture de déploiement KA MOBILE

**Frontend Cloudflare · Backend caché · Zéro exposition**

---

## 1. Principe général

```
                    INTERNET
                       │
              ┌────────▼────────┐
              │  Cloudflare     │  ← WAF, DDoS, Bot Management
              │  Network        │
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
  ┌───────▼──────┐ ┌──▼───┐ ┌──────▼──────┐
  │  Pages       │ │Worker│ │  Access      │
  │  Frontend    │ │API   │ │  Admin       │
  │  kamobile.ai │ │Proxy │ │  Zero Trust  │
  └───────┬──────┘ └──┬───┘ └──────┬──────┘
          │           │            │
          │    ┌──────▼────────┐   │
          │    │  Cloudflare   │   │
          └────►  Tunnel       ◄───┘
               │  (cloudflared)│
               └──────┬────────┘
                      │
          ┌───────────▼───────────┐
          │   SERVEUR PRIVÉ VPS   │
          │   (aucune IP publique) │
          │                        │
          │  ┌──────────────────┐  │
          │  │  KA Server       │  │
          │  │  Flask/Gunicorn  │  │
          │  │                  │  │
          │  │  • HCV2 Engine   │  │
          │  │  • Modal Codec   │  │
          │  │  • THU Core      │  │
          │  │  • Voice Engine  │  │
          │  │  • Holographic   │  │
          │  └──────────────────┘  │
          │                        │
          │  ┌──────────────────┐  │
          │  │  PostgreSQL      │  │
          │  │  Redis           │  │
          │  └──────────────────┘  │
          └────────────────────────┘
```

## 2. Composants

### 2.1 Frontend — Cloudflare Pages

**Ce qui est public :**
- Page d'accueil `kamobile.ai`
- Interface app KA MOBILE (HTML/CSS/JS)
- Écran de compression, galerie, dashboard
- WASM minimal de **décompression** uniquement (pour l'affichage)

**Ce qui n'est PAS dans le frontend :**
- ❌ Le codec de compression HCV2
- ❌ Le codec modal (THU)
- ❌ Les modèles vocaux (Piper)
- ❌ Les clés API, tokens, secrets

**Sécurité :**
- Page Rules pour bloquer les bots connus
- Cache tout le statique (TTL 1 an)
- Headers de sécurité (CSP, HSTS, X-Frame-Options)

### 2.2 API Gateway — Cloudflare Worker

**Rôle :** Proxy inverse qui :
- Valide les requêtes (rate limiting, headers)
- Ajoute des headers de sécurité
- Route vers le Tunnel
- Cache les réponses GET (stats, galerie)
- Bloque les patterns suspects (tentatives d'extraction, scraping)

```javascript
// Exemple de Worker (edge)
export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    
    // Rate limiting par IP
    const key = request.headers.get('CF-Connecting-IP')
    const { success } = await env.RATE_LIMITER.limit({ key })
    if (!success) return new Response('429', { status: 429 })
    
    // Bloquer les patterns d'extraction
    if (url.pathname.includes('/api/hcv2/download') && 
        !request.headers.has('X-KA-Client')) {
      return new Response('403', { status: 403 })
    }
    
    // Forwarder vers le backend via Tunnel
    return fetch('https://backend.internal' + url.pathname, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    })
  }
}
```

### 2.3 Backend — VPS Privé sans IP publique

**Ce qui est abrité :**
- Le moteur HCV2 complet (`encode_video`, `decode_video`)
- Le codec modal (`hcv2_modal_codec.py`)
- Le noyau doré K(t) et toute la THU
- Les modèles vocaux (Piper, Vosk)
- Le Holographic Voice Store
- Les documents fondateurs THU
- Les statistiques d'utilisation

**Protection :**
- ✅ Aucun port ouvert sur Internet
- ✅ Seule connexion autorisée : `cloudflared tunnel` vers Cloudflare
- ✅ Pas d'IP publique — le VPS est invisible
- ✅ SSH uniquement via Cloudflare Access (Zero Trust) ou VPN WireGuard
- ✅ Chiffrement AES-GCM au repos (disque)
- ✅ Backups chiffrés vers un second site (via SFTP sortant uniquement)

### 2.4 Admin — Cloudflare Access (Zero Trust)

**Accès administrateur restreint :**
- Connexion obligatoire via Cloudflare Access (Google SSO, GitHub, email OTP)
- Accès : `admin.kamobile.ai` → tableau de bord, logs, métriques
- Pas d'URL publique pour l'API admin
- Sessions courtes (15 minutes)

## 3. Flux de compression (le plus sensible)

```
Utilisateur
  │
  │ 1. Dépose une photo/vidéo
  ▼
Cloudflare Pages (frontend)
  │
  │ 2. Envoie le fichier vers /api/hcv2/mobile
  │    (le codec de compression n'est PAS dans le WASM)
  ▼
Cloudflare Worker (API Gateway)
  │
  │ 3. Vérifie rate limit, headers, taille
  │ 4. Forward via Tunnel
  ▼
Cloudflare Tunnel
  │
  │ 5. Chiffré de bout en bout
  ▼
Backend VPS (KA Server)
  │
  │ 6. HCV2 encode (φ, K(t), modal codec)
  │ 7. Renvoie le blob compressé + métriques
  ▼
Chemin inverse → Utilisateur
```

**Pourquoi le WASM de compression ne doit pas être exposé :**
- Le codec modal (seuil `1/(φ·m)`, transformée de Parseval, quantification φ) serait lisible dans le binaire WASM
- Les paramètres de prédiction K(t) (poids dorés) seraient récupérables
- La logique entière de la THU serait exposée
- Le WASM ne peut pas être obfusqué efficacement (les mathématiques sont visibles)

**Solution :** Le WASM client ne contient qu'un **décodeur minimal** (lecture du blob HCV2 → image). Le codec de compression reste **exclusivement serveur**.

## 4. Coûts estimés

| Composant | Service | Coût mensuel |
|---|---|---|
| Frontend statique | Cloudflare Pages | Gratuit (plan Free) |
| API Gateway | Cloudflare Workers | 0$ (100k req/jour gratuits) |
| Tunnel | Cloudflare Tunnel | Gratuit |
| VPS (4 vCPU, 8 Go, 80 Go SSD) | Hetzner / OVH / Scaleway | ~15-25 € |
| Zero Trust | Cloudflare Access (3 users) | Gratuit |
| Nom de domaine | kamobile.ai | ~10 €/an |
| **Total** | | **~20 €/mois** |

## 5. Commandes de déploiement

### 5.1 Cloudflare Tunnel

```bash
# Installer cloudflared sur le VPS
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Authentifier
cloudflared tunnel login

# Créer le tunnel
cloudflared tunnel create ka-mobile

# Configurer (config.yml)
url: http://localhost:8765
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json

# Lancer le tunnel (service systemd)
cloudflared tunnel install
cloudflared tunnel run ka-mobile
```

### 5.2 Cloudflare Pages

```bash
# Déployer le frontend
npx wrangler pages deploy ./ka-mobile-android/www --project-name=ka-mobile
```

### 5.3 Worker API

```bash
# Déployer le worker proxy
npx wrangler deploy ./api-worker.js --name=ka-mobile-api
```

## 6. Sécurité — Checklist

- [ ] Aucun port ouvert sur le VPS (vérifier avec `ss -tlnp`)
- [ ] `cloudflared` est le SEUL processus qui écoute sur 0.0.0.0
- [ ] SSH configuré uniquement avec clé + Cloudflare Access
- [ ] Les secrets (`KA_SECRET_KEY`, clés API) sont dans Cloudflare Workers Secrets
- [ ] Les modèles THU sont chiffrés au repos (LUKS ou eCryptfs)
- [ ] Les logs d'accès sont envoyés à Cloudflare Logpush (pas de log local sensible)
- [ ] Backup automatique vers un second site (tunnel sortant uniquement)
- [ ] Mises à jour de sécurité automatiques (unattended-upgrades)
- [ ] Alertes Cloudflare sur les patterns d'attaque (WAF custom rules)
- [ ] Test d'intrusion mensuel via l'API publique (détection d'extraction)

## 7. Schéma résumé

```
kamobile.ai
  │
  ├── / (Cloudflare Pages) → app HTML/CSS/JS
  │
  ├── /api/* (Cloudflare Worker) → Cloudflare Tunnel
  │   │
  │   └── localhost:8765 (KA Server, VPS privé)
  │       │
  │       ├── /api/hcv2/mobile     ← Compression HCV2 (cœur protégé)
  │       ├── /api/hcv2/view/*     ← Décompression transparente
  │       ├── /api/hcv2/stats      ← Statistiques
  │       ├── /api/voice/tts       ← Synthèse vocale
  │       └── /api/hcv2/gallery    ← Galerie
  │
  ├── admin.kamobile.ai (Cloudflare Access) → Tunnel → VPS
  │
  └── *.kamobile.ai (WAF global) → DDoS, Bot, Rate Limiting
```

---

> **Résumé :** Le frontend sur Cloudflare Pages, l'API derrière Cloudflare Worker + Tunnel, le backend sur un VPS sans IP publique. Le codec HCV2 (THU) ne quitte jamais le serveur. Le WASM client ne contient qu'un décodeur minimal. L'utilisateur voit une app rapide, sécurisée, et le cœur de la technologie reste invisible.