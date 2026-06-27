# 🚀 Guide Complet de Déploiement Render - HCV-PRO-PROJECT

## Date: 17 Avril 2026

---

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Préparation](#préparation)
3. [Déploiement Backend](#déploiement-backend)
4. [Déploiement Frontend](#déploiement-frontend)
5. [Configuration](#configuration)
6. [Tests](#tests)
7. [Dépannage](#dépannage)
8. [Maintenance](#maintenance)

---

## 🔧 Prérequis

### Compte Render
- [ ] Créer un compte sur [render.com](https://render.com)
- [ ] Vérifier l'email
- [ ] Connecter le compte GitHub

### Dépôts Git
- [ ] Dépôt `render-backend` sur GitHub
- [ ] Dépôt `render-frontend` sur GitHub
- [ ] Accès en lecture/écriture

### Outils Locaux
- [ ] Git installé
- [ ] Python 3.11+ installé
- [ ] Node.js 18+ installé (optionnel)
- [ ] curl ou Postman pour tester

---

## 📝 Préparation

### Étape 1: Vérifier les Fichiers

```bash
# Backend
ls -la render-backend/
# Doit contenir:
# - app.py
# - requirements.txt
# - runtime.txt
# - render.yaml
# - Procfile
# - .gitignore
# - .env.example
# - README.md

# Frontend
ls -la render-frontend/
# Doit contenir:
# - index.html
# - package.json
# - render.yaml
# - .gitignore
# - README.md
```

### Étape 2: Vérifier les Dépendances

```bash
# Backend
cd render-backend
pip install -r requirements.txt
python app.py
# Doit démarrer sans erreur sur http://localhost:5000

# Frontend
cd render-frontend
# Vérifier que index.html est valide
# Ouvrir dans un navigateur
```

### Étape 3: Committer les Changements

```bash
# Backend
cd render-backend
git add .
git commit -m "Prepare for Render deployment"
git push origin main

# Frontend
cd render-frontend
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

---

## 🚀 Déploiement Backend

### Étape 1: Créer le Service Backend sur Render

1. Aller sur [render.com/dashboard](https://render.com/dashboard)
2. Cliquer sur "New +" → "Web Service"
3. Sélectionner le dépôt `render-backend`
4. Configurer:
   - **Name**: `hcv-pro-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install --upgrade pip setuptools wheel && pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
   - **Plan**: `Free`

### Étape 2: Ajouter les Variables d'Environnement

1. Aller à Settings → Environment
2. Ajouter les variables:

```
HCV_PRO_SECRET=your-secret-key-here-change-this
HCV_PRO_API_KEY_REQUIRED=true
HCV_PRO_RATE_LIMIT=100
FLASK_ENV=production
FLASK_DEBUG=false
```

### Étape 3: Configurer le Health Check

1. Aller à Settings → Health Check
2. Configurer:
   - **Path**: `/health`
   - **Check Interval**: `10s`
   - **Timeout**: `5s`

### Étape 4: Déployer

1. Cliquer sur "Create Web Service"
2. Render va automatiquement:
   - Cloner le dépôt
   - Installer les dépendances
   - Démarrer le serveur
3. Attendre que le statut passe à "Live"

### Étape 5: Vérifier le Déploiement

```bash
# Vérifier la santé
curl https://hcv-pro-backend.onrender.com/health

# Réponse attendue:
# {
#   "status": "healthy",
#   "service": "HCV PRO Backend",
#   "version": "1.0.0",
#   "timestamp": "2026-04-17T...",
#   "environment": "render"
# }
```

---

## 🌐 Déploiement Frontend

### Étape 1: Créer le Service Frontend sur Render

1. Aller sur [render.com/dashboard](https://render.com/dashboard)
2. Cliquer sur "New +" → "Static Site"
3. Sélectionner le dépôt `render-frontend`
4. Configurer:
   - **Name**: `hcv-pro-frontend`
   - **Build Command**: `echo 'Static build - no build required'`
   - **Publish Directory**: `.`
   - **Plan**: `Free`

### Étape 2: Configurer les Headers

1. Aller à Settings → Headers
2. Les headers de sécurité sont déjà configurés dans `render.yaml`

### Étape 3: Configurer les Routes

1. Aller à Settings → Routes
2. Les routes SPA sont déjà configurées dans `render.yaml`

### Étape 4: Déployer

1. Cliquer sur "Create Static Site"
2. Render va automatiquement:
   - Cloner le dépôt
   - Servir les fichiers statiques
3. Attendre que le statut passe à "Live"

### Étape 5: Vérifier le Déploiement

```bash
# Vérifier que le site se charge
curl https://hcv-pro-frontend.onrender.com

# Vérifier les headers
curl -I https://hcv-pro-frontend.onrender.com
```

---

## ⚙️ Configuration

### Configuration Backend

#### Variables d'Environnement

```env
# Sécurité
HCV_PRO_SECRET=your-secret-key-here-change-this

# API
HCV_PRO_API_KEY_REQUIRED=true
HCV_PRO_RATE_LIMIT=100

# Flask
FLASK_ENV=production
FLASK_DEBUG=false
```

#### Clés API Disponibles

```
demo-key-2024
hcv-pro-client-001
test-key-frontend
```

### Configuration Frontend

#### URL du Backend

Mettre à jour dans `index.html`:

```javascript
const API_URL = 'https://hcv-pro-backend.onrender.com';
```

#### CORS

Le backend a CORS activé pour tous les domaines.

---

## 🧪 Tests

### Test 1: Vérifier la Santé du Backend

```bash
curl https://hcv-pro-backend.onrender.com/health
```

**Réponse attendue**: 200 OK avec JSON

### Test 2: Vérifier les Infos des Codecs

```bash
curl https://hcv-pro-backend.onrender.com/info
```

**Réponse attendue**: 200 OK avec liste des codecs

### Test 3: Tester la Compression Broadcast

```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

**Réponse attendue**: 200 OK avec résultats de compression

### Test 4: Tester la Compression Android Boost

```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/android-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 5242880}'
```

**Réponse attendue**: 200 OK avec résultats de compression

### Test 5: Tester la Compression Video Boost

```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/video-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 10485760}'
```

**Réponse attendue**: 200 OK avec résultats de compression

### Test 6: Tester la Compression Universal Boost

```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/universal-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 2097152}'
```

**Réponse attendue**: 200 OK avec résultats de compression

### Test 7: Vérifier le Frontend

1. Ouvrir https://hcv-pro-frontend.onrender.com
2. Vérifier que l'interface se charge
3. Vérifier que les onglets fonctionnent
4. Tester une démo

### Test 8: Tester l'Intégration

1. Ouvrir le frontend
2. Cliquer sur "Demo Broadcast VGA"
3. Vérifier que la compression fonctionne
4. Vérifier que les résultats s'affichent

---

## 🔍 Dépannage

### Problème: Backend ne démarre pas

**Symptôme**: Statut "Failed" sur Render

**Solutions**:
1. Vérifier les logs Render
2. Vérifier que `requirements.txt` est correct
3. Vérifier que `Procfile` est correct
4. Vérifier que `app.py` n'a pas d'erreurs

```bash
# Tester localement
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Problème: Frontend ne se charge pas

**Symptôme**: Erreur 404 ou page blanche

**Solutions**:
1. Vérifier que `index.html` existe
2. Vérifier que `render.yaml` est correct
3. Vérifier les logs Render
4. Vérifier que le chemin est correct

### Problème: API ne répond pas

**Symptôme**: Erreur 502 Bad Gateway

**Solutions**:
1. Vérifier que le backend est "Live"
2. Vérifier que le health check passe
3. Vérifier les logs du backend
4. Vérifier que Gunicorn démarre correctement

```bash
# Tester localement
curl http://localhost:5000/health
```

### Problème: CORS Error

**Symptôme**: Erreur CORS dans la console du navigateur

**Solutions**:
1. Vérifier que CORS est activé dans `app.py`
2. Vérifier que l'URL du backend est correcte
3. Vérifier que les headers sont corrects

### Problème: Authentification échoue

**Symptôme**: Erreur 401 Unauthorized

**Solutions**:
1. Vérifier que la clé API est correcte
2. Vérifier que le header `Authorization` est correct
3. Vérifier que `HCV_PRO_API_KEY_REQUIRED=true`

```bash
# Tester avec une clé valide
curl -X POST https://hcv-pro-backend.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

### Problème: Rate Limit dépassé

**Symptôme**: Erreur 429 Too Many Requests

**Solutions**:
1. Attendre 1 heure
2. Augmenter `HCV_PRO_RATE_LIMIT`
3. Utiliser une autre clé API

---

## 🔧 Maintenance

### Mise à Jour du Backend

1. Modifier le code dans `render-backend/`
2. Committer et pousser vers Git
3. Render va automatiquement redéployer

```bash
git add .
git commit -m "Update backend"
git push origin main
```

### Mise à Jour du Frontend

1. Modifier le code dans `render-frontend/`
2. Committer et pousser vers Git
3. Render va automatiquement redéployer

```bash
git add .
git commit -m "Update frontend"
git push origin main
```

### Vérifier les Logs

**Backend**:
1. Aller à Render Dashboard
2. Sélectionner `hcv-pro-backend`
3. Aller à Logs

**Frontend**:
1. Aller à Render Dashboard
2. Sélectionner `hcv-pro-frontend`
3. Aller à Logs

### Redémarrer le Service

**Backend**:
1. Aller à Render Dashboard
2. Sélectionner `hcv-pro-backend`
3. Cliquer sur "Restart"

**Frontend**:
1. Aller à Render Dashboard
2. Sélectionner `hcv-pro-frontend`
3. Cliquer sur "Restart"

### Monitorer les Performances

1. Aller à Render Dashboard
2. Sélectionner le service
3. Aller à Metrics
4. Vérifier:
   - CPU Usage
   - Memory Usage
   - Requests/sec
   - Response Time

---

## 📊 Checklist de Déploiement

### Avant le Déploiement
- [ ] Tous les fichiers sont en place
- [ ] Toutes les dépendances sont listées
- [ ] Configuration Render est correcte
- [ ] Variables d'environnement sont documentées
- [ ] Tests locaux réussissent

### Déploiement Backend
- [ ] Service créé sur Render
- [ ] Variables d'environnement configurées
- [ ] Health check configuré
- [ ] Déploiement réussi
- [ ] Statut "Live"

### Déploiement Frontend
- [ ] Service créé sur Render
- [ ] Headers configurés
- [ ] Routes configurées
- [ ] Déploiement réussi
- [ ] Statut "Live"

### Tests Post-Déploiement
- [ ] Backend répond sur `/health`
- [ ] Frontend se charge correctement
- [ ] API fonctionne avec authentification
- [ ] Compression fonctionne
- [ ] Intégration frontend-backend fonctionne

### Maintenance
- [ ] Logs vérifiés
- [ ] Performances acceptables
- [ ] Pas d'erreurs
- [ ] Monitoring en place

---

## 🎯 URLs de Déploiement

### Backend
- **URL**: `https://hcv-pro-backend.onrender.com`
- **Health**: `https://hcv-pro-backend.onrender.com/health`
- **Info**: `https://hcv-pro-backend.onrender.com/info`

### Frontend
- **URL**: `https://hcv-pro-frontend.onrender.com`

---

## 📞 Support

### Documentation Render
- [Render Documentation](https://render.com/docs)
- [Python on Render](https://render.com/docs/deploy-python)
- [Static Sites on Render](https://render.com/docs/static-sites)

### Documentation HCV PRO
- `render-backend/README.md` - Documentation backend
- `render-frontend/README.md` - Documentation frontend
- `RENDER_DEPLOYMENT_VERIFICATION.md` - Rapport de vérification
- `RENDER_DEPLOYMENT_FIXES.md` - Corrections appliquées

---

## 🎉 Conclusion

Ce guide couvre le déploiement complet de HCV PRO sur Render.

**Temps estimé**: 30-60 minutes

**Prochaines étapes**:
1. Suivre ce guide étape par étape
2. Tester chaque étape
3. Vérifier les logs en cas de problème
4. Contacter le support Render si nécessaire

---

**Généré**: 17 Avril 2026  
**Statut**: ✅ Guide Complet  
**Prêt pour**: Déploiement Immédiat
