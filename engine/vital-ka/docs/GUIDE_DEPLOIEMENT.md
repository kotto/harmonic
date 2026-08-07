# Guide de Déploiement — KA Phone

## 1. Backend API → Render

### Prérequis
- Compte Render (gratuit)
- Repository GitHub : `github.com/kotto/harmonic`

### Déploiement automatique (recommandé)

1. **Connecter GitHub à Render**
   - Aller sur dashboard.render.com
   - Cliquer « New » → « Web Service »
   - Sélectionner le repo `kotto/harmonic`
   - Render détectera automatiquement `engine/render.yaml`

2. **Configurer le service**
   ```
   Name       : ka-api
   Root Dir   : engine
   Build      : pip install -r requirements_server.txt
   Start      : gunicorn ka_server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   Plan       : Starter (25$/mois) ou Free (limité)
   ```

3. **Variables d'environnement**
   ```
   PYTHON_VERSION : 3.11.8
   MODEL_NAME     : 50k
   ```

4. **Vérifier**
   - URL de l'API : `https://ka-api.onrender.com`
   - Health check : `https://ka-api.onrender.com/api/health`

### Note sur le modèle 50K
Le fichier `knowledge_base_50k.npz` (2,9 Mo) doit être inclus dans le repo sous `engine/data/bootstrapper_output/`. Sans lui, le serveur utilisera la KB qualitative intégrée (914 faits).

---

## 2. Frontend PWA → Cloudflare Pages

### Prérequis
- Compte Cloudflare (gratuit)
- Domaine : ka.phone (à acheter) ou utiliser `*.pages.dev`

### Déploiement

1. **Créer un projet Cloudflare Pages**
   - Aller sur dash.cloudflare.com → Workers & Pages
   - Créer une application → Pages → Connecter Git
   - Sélectionner le repo `kotto/harmonic`

2. **Configuration du build**
   ```
   Build command  : (aucune — fichiers statiques)
   Output dir     : engine
   Root dir       : engine
   ```

3. **Fichiers à servir (configurés dans `_headers`)**
   - `ka_index.html` → page principale
   - `manifest.json` → PWA manifest
   - `sw.js` → Service Worker
   - `icons/*.svg` → Icônes

4. **Domaine personnalisé** (optionnel)
   - Acheter `ka.phone` (ou `ka-phone.com`)
   - Ajouter dans Cloudflare Pages → Custom domains

---

## 3. Fichiers de Configuration Cloudflare

### `engine/_headers` (à créer)
```
/*
  Access-Control-Allow-Origin: *
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY

/sw.js
  Content-Type: application/javascript; charset=utf-8
  Cache-Control: no-cache

/manifest.json
  Content-Type: application/manifest+json
  Cache-Control: public, max-age=3600
```

### `_redirects` (à créer)
```
/          /ka_index.html  200
```

---

## 4. Vérification du Déploiement

### Tester l'API
```bash
# Health
curl https://ka-api.onrender.com/api/health

# Chat
curl -X POST https://ka-api.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "capitale de la France"}'
```

### Tester le PWA
1. Ouvrir `https://ka-phone.pages.dev` (ou ka.phone) sur mobile
2. Vérifier que le bandeau « Installer » apparaît
3. Installer → l'icône KA apparaît sur l'écran d'accueil
4. Ouvrir l'app → plein écran, sans barre d'adresse
5. Couper Internet → l'app fonctionne toujours (mode hors ligne)

---

## 5. Coût Mensuel Estimé

| Service | Plan | Coût |
|---------|------|------|
| Render (backend) | Starter | 25 $ |
| Cloudflare Pages | Free | 0 $ |
| Domaine ka.phone | 1 an | ~12 $ |
| **TOTAL** | | **~27 $/mois** |

---

*Guide de déploiement — Juillet 2026*
