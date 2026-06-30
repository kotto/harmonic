# Déploiement KA — Render + Vercel

## Architecture

```
┌──────────────────────────────────────────┐
│  Vercel (Frontend)                       │
│  ka-app.vercel.app                       │
│  └─ index.html (UI KA, 10 écrans)       │
│     └─ fetch() → backend API             │
└──────────────┬───────────────────────────┘
               │ HTTPS
┌──────────────▼───────────────────────────┐
│  Render (Backend)                        │
│  ka-api.onrender.com                     │
│  ├─ /api/chat    → HarmonicAI.ask()     │
│  ├─ /api/compress → HCV.encode()        │
│  ├─ /api/upscale  → HCV.upscale()       │
│  └─ /api/stats    → Métriques           │
└──────────────────────────────────────────┘
```

---

## 1. Déployer le Backend sur Render

### Prérequis
- Compte Render (https://render.com)
- Le repo Git poussé sur GitHub

### Étapes

1. Aller sur https://dashboard.render.com
2. Cliquer **New +** → **Web Service**
3. Connecter le repo GitHub `kotto/harmonic`
4. Configurer :
   - **Name**: `ka-api`
   - **Root Directory**: `engine`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements_server.txt`
   - **Start Command**: `gunicorn ka_server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan**: Starter (gratuit)
5. Ajouter une variable d'environnement :
   - `MODEL_NAME` = `50k`
6. Cliquer **Create Web Service**

Le modèle 50K sera téléchargé au premier démarrage (ou copié depuis le repo si inclus).

**Note**: Le plan gratuit Render s'endort après 15 min d'inactivité. Le premier appel peut prendre ~30s.

---

## 2. Déployer le Frontend sur Vercel

### Étapes

```bash
cd ka-web-complete/ka-web-complete

# Installer Vercel CLI
npm i -g vercel

# Déployer
vercel --prod
```

Ou via l'interface web :
1. Aller sur https://vercel.com
2. **New Project** → Importer le dossier `ka-web-complete/ka-web-complete`
3. **Deploy**

---

## 3. Tester

```bash
# Vérifier que le backend répond
curl https://ka-api.onrender.com/api/health

# Vérifier le chat
curl -X POST https://ka-api.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Bonjour"}'

# Ouvrir l'app dans le navigateur
open https://ka-app.vercel.app
```

---

## 4. Mise à jour

```bash
git push origin main
# Render et Vercel redéploient automatiquement
```

---

## Configuration actuelle

| Service | URL | Plan |
|---------|-----|------|
| Backend | `https://ka-api.onrender.com` | Render Starter (gratuit) |
| Frontend | `https://ka-app.vercel.app` | Vercel Hobby (gratuit) |

## Limitations du plan gratuit

- **Render**: 512 MB RAM, s'endort après 15 min d'inactivité, 750h/mois
- **Vercel**: 100 GB bande passante/mois, déploiements illimités
- **Modèle**: 30K faits chargés (assez pour la démo, pas pour 217K)
