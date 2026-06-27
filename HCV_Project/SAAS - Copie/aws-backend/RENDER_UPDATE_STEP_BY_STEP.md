# 📋 Guide Détaillé: Mise à Jour des Services Render Existants

**Date**: 17 Avril 2026  
**Services à Mettre à Jour**:
- `hcv-pro-render-backend-3` (Web Service)
- `hcv-pro-render-frontend` (Static Site)

---

## 🎯 Objectif

Mettre à jour les deux services Render existants avec les corrections de configuration pour assurer un déploiement production optimal.

---

## ⏱️ Temps Estimé

- **Backend**: 5-10 minutes
- **Frontend**: 3-5 minutes
- **Tests**: 5 minutes
- **Total**: ~15-20 minutes

---

## 🔴 ÉTAPE 1: Mise à Jour du Backend (hcv-pro-render-backend-3)

### 1.1 Accéder au Dashboard Render

1. Ouvrir [https://render.com/dashboard](https://render.com/dashboard)
2. Se connecter avec vos identifiants
3. Chercher et cliquer sur **`hcv-pro-render-backend-3`**

### 1.2 Accéder aux Paramètres de Build & Deploy

1. Dans le menu de gauche, cliquer sur **Settings**
2. Aller à l'onglet **Build & Deploy**

### 1.3 Mettre à Jour le Start Command

**Localiser**: Section "Start Command"

**Valeur Actuelle** (à remplacer):
```
python app.py
```

**Nouvelle Valeur**:
```
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

**Actions**:
1. Cliquer dans le champ "Start Command"
2. Sélectionner tout le texte (Ctrl+A)
3. Coller la nouvelle valeur
4. Cliquer **Save**

### 1.4 Vérifier le Build Command

**Localiser**: Section "Build Command"

**Valeur Attendue**:
```
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

**Si différent**:
1. Mettre à jour avec la valeur ci-dessus
2. Cliquer **Save**

### 1.5 Mettre à Jour les Variables d'Environnement

1. Dans le menu de gauche, cliquer sur **Environment**
2. Vous verrez une liste de variables existantes

**Ajouter/Mettre à Jour les Variables Suivantes**:

#### Variable 1: HCV_PRO_SECRET
- **Key**: `HCV_PRO_SECRET`
- **Value**: `your-secret-key-here` (ou une clé sécurisée)
- **Action**: Cliquer "Add" ou mettre à jour si existe

#### Variable 2: HCV_PRO_API_KEY_REQUIRED
- **Key**: `HCV_PRO_API_KEY_REQUIRED`
- **Value**: `true`
- **Action**: Cliquer "Add" ou mettre à jour si existe

#### Variable 3: HCV_PRO_RATE_LIMIT
- **Key**: `HCV_PRO_RATE_LIMIT`
- **Value**: `100`
- **Action**: Cliquer "Add" ou mettre à jour si existe

#### Variable 4: FLASK_ENV
- **Key**: `FLASK_ENV`
- **Value**: `production`
- **Action**: Cliquer "Add" ou mettre à jour si existe

#### Variable 5: FLASK_DEBUG
- **Key**: `FLASK_DEBUG`
- **Value**: `false`
- **Action**: Cliquer "Add" ou mettre à jour si existe

**Après chaque ajout/modification**:
- Cliquer **Save**

### 1.6 Redéployer le Backend

**Option A: Redéploiement Complet (Recommandé)**

1. Aller à l'onglet **Deployments**
2. Cliquer le bouton **Trigger Deploy** (en haut à droite)
3. Attendre que le déploiement se termine (2-5 minutes)
4. Vérifier que le statut passe à "Live" (vert)

**Option B: Redémarrage Simple**

1. Aller à **Settings**
2. Cliquer le bouton **Restart** (en bas)
3. Attendre que le service redémarre (1-2 minutes)

### 1.7 Vérifier les Logs du Backend

1. Aller à l'onglet **Logs**
2. Vérifier qu'il n'y a pas d'erreurs rouges
3. Chercher le message: `"Listening on 0.0.0.0:PORT"`

**Erreurs Courantes**:
- ❌ `ModuleNotFoundError`: Les dépendances ne sont pas installées
- ❌ `Address already in use`: Le port est occupé
- ❌ `gunicorn: command not found`: Gunicorn n'est pas installé

### 1.8 Tester le Backend

Ouvrir un terminal et exécuter:

```bash
# Test 1: Health Check
curl https://hcv-pro-render-backend-3.onrender.com/health

# Réponse attendue:
# {
#   "status": "healthy",
#   "service": "HCV PRO Backend",
#   "version": "1.0.0",
#   "timestamp": "2026-04-17T...",
#   "environment": "render"
# }
```

**Si erreur 502 Bad Gateway**:
- Attendre 2-3 minutes (le service peut être en cours de démarrage)
- Vérifier les logs
- Vérifier que le Start Command est correct

---

## 🟢 ÉTAPE 2: Mise à Jour du Frontend (hcv-pro-render-frontend)

### 2.1 Accéder au Dashboard Render

1. Ouvrir [https://render.com/dashboard](https://render.com/dashboard)
2. Chercher et cliquer sur **`hcv-pro-render-frontend`**

### 2.2 Accéder aux Paramètres

1. Dans le menu de gauche, cliquer sur **Settings**

### 2.3 Vérifier le Build Command

**Localiser**: Section "Build & Deploy"

**Valeur Attendue**:
```
echo 'Static build - no build required'
```

**Si différent**:
1. Mettre à jour avec la valeur ci-dessus
2. Cliquer **Save**

### 2.4 Vérifier le Publish Directory

**Localiser**: Section "Build & Deploy"

**Valeur Attendue**:
```
.
```

**Si différent**:
1. Mettre à jour avec `.`
2. Cliquer **Save**

### 2.5 Vérifier les Headers de Sécurité

1. Aller à l'onglet **Headers**
2. Vérifier que les headers suivants sont présents:

**Header 1: X-Frame-Options**
- **Path**: `/*`
- **Name**: `X-Frame-Options`
- **Value**: `DENY`

**Header 2: X-Content-Type-Options**
- **Path**: `/*`
- **Name**: `X-Content-Type-Options`
- **Value**: `nosniff`

**Header 3: Referrer-Policy**
- **Path**: `/*`
- **Name**: `Referrer-Policy`
- **Value**: `strict-origin-when-cross-origin`

**Header 4: Permissions-Policy**
- **Path**: `/*`
- **Name**: `Permissions-Policy`
- **Value**: `geolocation=(), microphone=(), camera=()`

**Si manquants**:
1. Cliquer "Add Header"
2. Remplir les champs
3. Cliquer **Save**

### 2.6 Redéployer le Frontend

**Option A: Redéploiement Complet (Recommandé)**

1. Aller à l'onglet **Deployments**
2. Cliquer le bouton **Trigger Deploy**
3. Attendre que le déploiement se termine (1-3 minutes)
4. Vérifier que le statut passe à "Live" (vert)

**Option B: Redémarrage Simple**

1. Aller à **Settings**
2. Cliquer le bouton **Restart**
3. Attendre que le service redémarre (30 secondes - 1 minute)

### 2.7 Vérifier les Logs du Frontend

1. Aller à l'onglet **Logs**
2. Vérifier qu'il n'y a pas d'erreurs rouges

### 2.8 Tester le Frontend

Ouvrir un terminal et exécuter:

```bash
# Test 1: Vérifier que le site se charge
curl https://hcv-pro-render-frontend.onrender.com

# Réponse attendue: HTML valide (commence par <!DOCTYPE html>)

# Test 2: Vérifier les headers
curl -I https://hcv-pro-render-frontend.onrender.com

# Réponse attendue: Headers de sécurité présents
```

**Si erreur 404 ou page blanche**:
- Vérifier que `index.html` existe
- Vérifier les logs
- Vérifier que le Publish Directory est `.`

---

## 🧪 ÉTAPE 3: Tests d'Intégration

### 3.1 Test 1: Health Check Backend

```bash
curl https://hcv-pro-render-backend-3.onrender.com/health
```

**Réponse Attendue**: 200 OK avec JSON

### 3.2 Test 2: Info Codecs

```bash
curl https://hcv-pro-render-backend-3.onrender.com/info
```

**Réponse Attendue**: 200 OK avec liste des codecs

### 3.3 Test 3: Compression Broadcast

```bash
curl -X POST https://hcv-pro-render-backend-3.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

**Réponse Attendue**: 200 OK avec résultats de compression

### 3.4 Test 4: Frontend Charge

1. Ouvrir dans un navigateur: `https://hcv-pro-render-frontend.onrender.com`
2. Vérifier que la page se charge correctement
3. Vérifier qu'il n'y a pas d'erreurs dans la console (F12)

### 3.5 Test 5: Intégration Frontend-Backend

1. Ouvrir `https://hcv-pro-render-frontend.onrender.com`
2. Cliquer sur "Demo Broadcast VGA"
3. Vérifier que la compression fonctionne
4. Vérifier que les résultats s'affichent

---

## ✅ Checklist de Vérification

### Backend (hcv-pro-render-backend-3)

- [ ] Start Command mis à jour: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
- [ ] Build Command vérifié: `pip install --upgrade pip setuptools wheel && pip install -r requirements.txt`
- [ ] Variables d'env mises à jour:
  - [ ] HCV_PRO_SECRET
  - [ ] HCV_PRO_API_KEY_REQUIRED
  - [ ] HCV_PRO_RATE_LIMIT
  - [ ] FLASK_ENV
  - [ ] FLASK_DEBUG
- [ ] Redéploiement terminé
- [ ] Statut: "Live" (vert)
- [ ] Logs: Pas d'erreurs
- [ ] Health check: 200 OK
- [ ] Info codecs: 200 OK
- [ ] Compression: 200 OK

### Frontend (hcv-pro-render-frontend)

- [ ] Build Command vérifié: `echo 'Static build - no build required'`
- [ ] Publish Directory vérifié: `.`
- [ ] Headers de sécurité vérifiés (4 headers)
- [ ] Redéploiement terminé
- [ ] Statut: "Live" (vert)
- [ ] Logs: Pas d'erreurs
- [ ] Site se charge: OK
- [ ] Pas d'erreurs console: OK

### Tests d'Intégration

- [ ] Health check backend: 200 OK
- [ ] Info codecs: 200 OK
- [ ] Compression broadcast: 200 OK
- [ ] Frontend charge: OK
- [ ] Intégration frontend-backend: OK

---

## 🔍 Dépannage

### Problème: Backend ne démarre pas (Statut "Failed")

**Symptômes**:
- Statut rouge "Failed"
- Erreur 502 Bad Gateway

**Solutions**:
1. Vérifier les logs Render (onglet Logs)
2. Vérifier que le Start Command est correct
3. Vérifier que les dépendances sont installées
4. Vérifier que `app.py` n'a pas d'erreurs

**Commande de test local**:
```bash
cd render-backend
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Problème: Frontend ne se charge pas (404 ou page blanche)

**Symptômes**:
- Erreur 404
- Page blanche
- Erreurs dans la console

**Solutions**:
1. Vérifier les logs Render
2. Vérifier que `index.html` existe
3. Vérifier que le Build Command est correct
4. Vérifier que le Publish Directory est `.`

### Problème: API ne répond pas (502 Bad Gateway)

**Symptômes**:
- Erreur 502 Bad Gateway
- Health check échoue

**Solutions**:
1. Vérifier que le backend est "Live"
2. Attendre 2-3 minutes (démarrage en cours)
3. Vérifier les logs du backend
4. Vérifier que Gunicorn démarre correctement

### Problème: CORS Error

**Symptômes**:
- Erreur CORS dans la console du navigateur
- Frontend ne peut pas appeler le backend

**Solutions**:
1. Vérifier que CORS est activé dans `app.py`
2. Vérifier que l'URL du backend est correcte
3. Vérifier que les headers CORS sont corrects

---

## 📊 Vérification des Performances

### Après la Mise à Jour

1. Aller à **Metrics** pour chaque service
2. Vérifier les métriques:

**Backend**:
- CPU Usage: < 50%
- Memory Usage: < 500MB
- Requests/sec: Normal
- Response Time: < 1s

**Frontend**:
- CPU Usage: < 10%
- Memory Usage: < 100MB
- Requests/sec: Normal
- Response Time: < 100ms

---

## 🎯 Résumé des Changements

### Backend (hcv-pro-render-backend-3)

| Paramètre | Avant | Après |
|-----------|-------|-------|
| Start Command | `python app.py` | `gunicorn -w 4 -b 0.0.0.0:$PORT app:app` |
| Build Command | À vérifier | `pip install --upgrade pip setuptools wheel && pip install -r requirements.txt` |
| FLASK_ENV | À ajouter | `production` |
| FLASK_DEBUG | À ajouter | `false` |
| HCV_PRO_SECRET | À ajouter | `your-secret-key-here` |
| HCV_PRO_API_KEY_REQUIRED | À ajouter | `true` |
| HCV_PRO_RATE_LIMIT | À ajouter | `100` |

### Frontend (hcv-pro-render-frontend)

| Paramètre | Avant | Après |
|-----------|-------|-------|
| Build Command | À vérifier | `echo 'Static build - no build required'` |
| Publish Directory | À vérifier | `.` |
| Headers | À vérifier | 4 headers de sécurité |

---

## 📞 Support et Documentation

### Documentation Disponible

- [RENDER_QUICK_UPDATE.md](RENDER_QUICK_UPDATE.md) - Mise à jour rapide (10 min)
- [RENDER_UPDATE_EXISTING_SERVICES.md](RENDER_UPDATE_EXISTING_SERVICES.md) - Guide détaillé
- [RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md) - Guide complet de déploiement
- [render-backend/README.md](render-backend/README.md) - Documentation backend
- [render-frontend/README.md](render-frontend/README.md) - Documentation frontend

### Ressources Externes

- [Render Documentation](https://render.com/docs)
- [Render Dashboard](https://render.com/dashboard)
- [Gunicorn Documentation](https://gunicorn.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## 🚀 Prochaines Étapes

1. ✅ Suivre ce guide pour mettre à jour le backend
2. ✅ Suivre ce guide pour mettre à jour le frontend
3. ✅ Exécuter les tests d'intégration
4. ✅ Vérifier les performances
5. ✅ Monitorer les logs pendant 24 heures

---

## 📝 Notes

- **Temps total estimé**: 15-20 minutes
- **Pas de downtime**: Les services restent actifs pendant la mise à jour
- **Rollback possible**: Si problème, vous pouvez revenir à la configuration précédente
- **Support**: Consulter la documentation ou les logs Render

---

**Généré**: 17 Avril 2026  
**Statut**: ✅ Guide Détaillé Prêt  
**Prêt pour**: Mise à Jour Immédiate

