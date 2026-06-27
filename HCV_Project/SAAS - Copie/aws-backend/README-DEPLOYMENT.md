# Guide de Déploiement HCV PRO

## Options de Déploiement

### Option 1: Vercel (RECOMMANDÉ)

#### Prérequis
- Compte Vercel
- Git

#### Étapes

1. **Initialiser Git**
```bash
cd HCV-PRO-PROJECT
git init
git add .
git commit -m "Initial commit"
```

2. **Déployer**
```bash
# Installer Vercel CLI
npm i -g vercel

# Déployer
vercel
```

3. **Configuration**
- Suivre les instructions de Vercel
- Configurer les variables d'environnement si nécessaire

### Option 2: Docker

#### Build
```bash
docker build -t hcv-pro .
```

#### Run
```bash
docker run -p 3000:3000 hcv-pro
```

### Option 3: Serveur Dédié (Railway/Render/Heroku)

#### Prérequis
- Python 3.11+
- FFmpeg

#### Étapes
1. Copier les fichiers sur le serveur
2. Installer les dépendances:
```bash
pip install -r requirements.txt
```
3. Lancer le serveur:
```bash
python server/hcv_pro_server.py
```

## Sécurité

### Headers de Sécurité (Déjà configurés)
- ✅ X-Content-Type-Options: nosniff
- ✅ X-Frame-Options: DENY
- ✅ X-XSS-Protection: 1; mode=block
- ✅ Strict-Transport-Security: max-age=31536000
- ✅ Content-Security-Policy: strict
- ✅ Referrer-Policy: strict-origin-when-cross-origin
- ✅ Permissions-Policy: restrictive

### Recommandations
1. **Utiliser HTTPS** (obligatoire pour HSTS)
2. **Configurer CORS** pour votre domaine
3. **Ajouter authentification** pour les endpoints sensibles
4. **Rate limiting** pour prévenir les abus

## Minification

### Avant déploiement
```bash
# Installer les dépendances
npm install

# Minifier
npm run build
```

### Résultats attendus
- HTML: ~47% de réduction
- JS: ~40% de réduction
- CSS: ~40% de réduction

## Monitoring

### Logs
Les logs sont disponibles via:
- Vercel Dashboard
- Serveur console
- Fichier de log (à configurer)

### Métriques
- Temps de réponse
- Taille des fichiers
- Taux d'erreurs

## Maintenance

### Mises à jour
1. Mettre à jour le code
2. Tester localement
3. Déployer
4. Vérifier les logs

### Sauvegarde
- Sauvegarder les fichiers de configuration
- Sauvegarder les données utilisateur (si nécessaire)

## Support

Pour problème:
1. Vérifier les logs
2. Consulter la documentation
3. Contacter le support
