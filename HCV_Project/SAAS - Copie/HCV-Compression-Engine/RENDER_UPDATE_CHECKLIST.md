# ✅ Checklist de Mise à Jour - Services Render

**Date**: 17 Avril 2026  
**Services**: `hcv-pro-render-backend-3` et `hcv-pro-render-frontend`

---

## 🔴 BACKEND: hcv-pro-render-backend-3

### Phase 1: Accès et Navigation

- [ ] Ouvrir [render.com/dashboard](https://render.com/dashboard)
- [ ] Se connecter
- [ ] Cliquer sur `hcv-pro-render-backend-3`
- [ ] Aller à Settings → Build & Deploy

### Phase 2: Start Command

**Localisation**: Settings → Build & Deploy → Start Command

**Avant**:
```
python app.py
```

**Après**:
```
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

- [ ] Remplacer le Start Command
- [ ] Cliquer Save
- [ ] Confirmer la sauvegarde

### Phase 3: Build Command

**Localisation**: Settings → Build & Deploy → Build Command

**Valeur Attendue**:
```
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

- [ ] Vérifier que le Build Command est correct
- [ ] Si différent, mettre à jour
- [ ] Cliquer Save

### Phase 4: Variables d'Environnement

**Localisation**: Settings → Environment

#### Variable 1: HCV_PRO_SECRET
- [ ] Key: `HCV_PRO_SECRET`
- [ ] Value: `your-secret-key-here`
- [ ] Cliquer Add/Update
- [ ] Cliquer Save

#### Variable 2: HCV_PRO_API_KEY_REQUIRED
- [ ] Key: `HCV_PRO_API_KEY_REQUIRED`
- [ ] Value: `true`
- [ ] Cliquer Add/Update
- [ ] Cliquer Save

#### Variable 3: HCV_PRO_RATE_LIMIT
- [ ] Key: `HCV_PRO_RATE_LIMIT`
- [ ] Value: `100`
- [ ] Cliquer Add/Update
- [ ] Cliquer Save

#### Variable 4: FLASK_ENV
- [ ] Key: `FLASK_ENV`
- [ ] Value: `production`
- [ ] Cliquer Add/Update
- [ ] Cliquer Save

#### Variable 5: FLASK_DEBUG
- [ ] Key: `FLASK_DEBUG`
- [ ] Value: `false`
- [ ] Cliquer Add/Update
- [ ] Cliquer Save

### Phase 5: Redéploiement

**Localisation**: Deployments

- [ ] Cliquer "Trigger Deploy"
- [ ] Attendre le déploiement (2-5 minutes)
- [ ] Vérifier que le statut passe à "Live" (vert)

### Phase 6: Vérification des Logs

**Localisation**: Logs

- [ ] Vérifier qu'il n'y a pas d'erreurs rouges
- [ ] Chercher: "Listening on 0.0.0.0:PORT"
- [ ] Confirmer que le service est actif

### Phase 7: Tests

```bash
# Test 1: Health Check
curl https://hcv-pro-render-backend-3.onrender.com/health
```

- [ ] Réponse: 200 OK
- [ ] JSON valide
- [ ] Status: "healthy"

```bash
# Test 2: Info Codecs
curl https://hcv-pro-render-backend-3.onrender.com/info
```

- [ ] Réponse: 200 OK
- [ ] Liste des codecs présente

```bash
# Test 3: Compression
curl -X POST https://hcv-pro-render-backend-3.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

- [ ] Réponse: 200 OK
- [ ] Résultats de compression présents

---

## 🟢 FRONTEND: hcv-pro-render-frontend

### Phase 1: Accès et Navigation

- [ ] Ouvrir [render.com/dashboard](https://render.com/dashboard)
- [ ] Cliquer sur `hcv-pro-render-frontend`
- [ ] Aller à Settings

### Phase 2: Build Command

**Localisation**: Settings → Build & Deploy → Build Command

**Valeur Attendue**:
```
echo 'Static build - no build required'
```

- [ ] Vérifier que le Build Command est correct
- [ ] Si différent, mettre à jour
- [ ] Cliquer Save

### Phase 3: Publish Directory

**Localisation**: Settings → Build & Deploy → Publish Directory

**Valeur Attendue**:
```
.
```

- [ ] Vérifier que le Publish Directory est `.`
- [ ] Si différent, mettre à jour
- [ ] Cliquer Save

### Phase 4: Headers de Sécurité

**Localisation**: Settings → Headers

#### Header 1: X-Frame-Options
- [ ] Path: `/*`
- [ ] Name: `X-Frame-Options`
- [ ] Value: `DENY`
- [ ] Cliquer Add/Update
- [ ] Cliquer Save

#### Header 2: X-Content-Type-Options
- [ ] Path: `/*`
- [ ] Name: `X-Content-Type-Options`
- [ ] Value: `nosniff`
- [ ] Cliquer Add/Update
- [ ] Cliquer Save

#### Header 3: Referrer-Policy
- [ ] Path: `/*`
- [ ] Name: `Referrer-Policy`
- [ ] Value: `strict-origin-when-cross-origin`
- [ ] Cliquer Add/Update
- [ ] Cliquer Save

#### Header 4: Permissions-Policy
- [ ] Path: `/*`
- [ ] Name: `Permissions-Policy`
- [ ] Value: `geolocation=(), microphone=(), camera=()`
- [ ] Cliquer Add/Update
- [ ] Cliquer Save

### Phase 5: Redéploiement

**Localisation**: Deployments

- [ ] Cliquer "Trigger Deploy"
- [ ] Attendre le déploiement (1-3 minutes)
- [ ] Vérifier que le statut passe à "Live" (vert)

### Phase 6: Vérification des Logs

**Localisation**: Logs

- [ ] Vérifier qu'il n'y a pas d'erreurs rouges
- [ ] Confirmer que le service est actif

### Phase 7: Tests

```bash
# Test 1: Site se charge
curl https://hcv-pro-render-frontend.onrender.com
```

- [ ] Réponse: 200 OK
- [ ] HTML valide (commence par <!DOCTYPE html>)

```bash
# Test 2: Headers de sécurité
curl -I https://hcv-pro-render-frontend.onrender.com
```

- [ ] Headers présents
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff

---

## 🧪 TESTS D'INTÉGRATION

### Test 1: Backend Health

```bash
curl https://hcv-pro-render-backend-3.onrender.com/health
```

- [ ] Réponse: 200 OK
- [ ] Status: "healthy"

### Test 2: Frontend Charge

1. Ouvrir: `https://hcv-pro-render-frontend.onrender.com`
2. Vérifier que la page se charge

- [ ] Page se charge correctement
- [ ] Pas d'erreurs 404
- [ ] Pas d'erreurs console (F12)

### Test 3: Intégration Frontend-Backend

1. Ouvrir: `https://hcv-pro-render-frontend.onrender.com`
2. Cliquer sur "Demo Broadcast VGA"
3. Vérifier que la compression fonctionne

- [ ] Compression démarre
- [ ] Résultats s'affichent
- [ ] Pas d'erreurs CORS

### Test 4: Performances

**Backend Metrics**:
- [ ] CPU Usage: < 50%
- [ ] Memory Usage: < 500MB
- [ ] Response Time: < 1s

**Frontend Metrics**:
- [ ] CPU Usage: < 10%
- [ ] Memory Usage: < 100MB
- [ ] Response Time: < 100ms

---

## 📊 RÉSUMÉ

### Backend Changes

| Paramètre | Avant | Après | ✅ |
|-----------|-------|-------|-----|
| Start Command | `python app.py` | `gunicorn -w 4 -b 0.0.0.0:$PORT app:app` | [ ] |
| FLASK_ENV | - | `production` | [ ] |
| FLASK_DEBUG | - | `false` | [ ] |
| HCV_PRO_SECRET | - | `your-secret-key-here` | [ ] |
| HCV_PRO_API_KEY_REQUIRED | - | `true` | [ ] |
| HCV_PRO_RATE_LIMIT | - | `100` | [ ] |

### Frontend Changes

| Paramètre | Avant | Après | ✅ |
|-----------|-------|-------|-----|
| Build Command | À vérifier | `echo 'Static build - no build required'` | [ ] |
| Publish Directory | À vérifier | `.` | [ ] |
| Headers | À vérifier | 4 headers de sécurité | [ ] |

---

## 🎯 STATUT FINAL

- [ ] Backend: Mise à jour complète
- [ ] Frontend: Mise à jour complète
- [ ] Tests: Tous réussis
- [ ] Performances: Acceptables
- [ ] Logs: Pas d'erreurs
- [ ] Prêt pour production: ✅

---

## ⏱️ TEMPS ÉCOULÉ

| Phase | Temps | Statut |
|-------|-------|--------|
| Backend Setup | 5-10 min | [ ] |
| Frontend Setup | 3-5 min | [ ] |
| Tests | 5 min | [ ] |
| **Total** | **15-20 min** | [ ] |

---

## 📝 NOTES

```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```

---

**Généré**: 17 Avril 2026  
**Statut**: ✅ Checklist Prête  
**Prêt pour**: Mise à Jour Immédiate

