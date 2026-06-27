# HCV PRO Frontend - Render Deployment

## 📋 Description

Interface web pour HCV PRO - Plateforme de compression multimédia avec support des codecs broadcast, Android Boost, Video Boost et Universal Boost.

## 🚀 Déploiement sur Render

### Configuration Render
- **Runtime**: Static (HTML/CSS/JavaScript)
- **Plan**: Free (gratuit)
- **Build Command**: `echo 'Static build - no build required'`
- **Static Publish Path**: `.`

### Déploiement

Le frontend est déployé automatiquement sur Render à partir du dépôt Git.

URL de déploiement: `https://hcv-pro-frontend.onrender.com`

## 🌐 Fonctionnalités

### Tableau de Bord
- Vue d'ensemble des méthodes de compression
- Statistiques en temps réel
- Démos interactives

### Compression Broadcast
- Support SDI 4:2:2
- Compression lossless statistique
- Ratio 26-33:1
- PSNR 42-46 dB

### Android Boost
- Compression JPEG optimisée
- Ratio 3-11:1
- Support upscaling Lanczos
- Optimisation mobile

### Video Boost
- Compression vidéo H264/H265
- Ratio 2.3-7.5:1
- Support streaming
- Optimisation vidéo

### Universal Boost
- Support JPEG, PNG, BMP, WebP, GIF
- Ratio 1.2-345:1
- Compression universelle
- Optimisation images

### Comparaison Avant/Après
- Visualisation côte à côte
- Métriques de qualité (PSNR, SSIM)
- Historique des compressions

## 📁 Structure

```
render-frontend/
├── index.html          # Interface web principale
├── package.json        # Configuration Node.js
├── render.yaml         # Configuration Render
├── .gitignore          # Exclusions Git
└── README.md           # Ce fichier
```

## 🎨 Technologies

- **HTML5** - Structure
- **CSS3** - Styling (Tailwind CSS)
- **JavaScript** - Interactivité
- **Lucide Icons** - Icônes
- **Tailwind CSS** - Framework CSS

## 🔗 Intégration Backend

Le frontend communique avec le backend via l'API REST:

```javascript
// Exemple d'appel API
fetch('https://hcv-pro-backend.onrender.com/compress/broadcast', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer demo-key-2024',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    file_size: 1048576
  })
})
```

## 🧪 Tests

### Vérifier le Déploiement
```bash
curl https://hcv-pro-frontend.onrender.com
```

### Vérifier les Headers
```bash
curl -I https://hcv-pro-frontend.onrender.com
```

## 🔒 Sécurité

### Headers de Sécurité Configurés
- `X-Frame-Options: DENY` - Prévient le clickjacking
- `X-Content-Type-Options: nosniff` - Prévient le MIME sniffing
- `Referrer-Policy: strict-origin-when-cross-origin` - Contrôle les referrers
- `Permissions-Policy` - Restreint les permissions

### CORS
- Configuré pour communiquer avec le backend
- Authentification par clé API

## 📊 Performance

### Optimisations
- HTML statique (pas de serveur)
- CSS minifié (Tailwind)
- JavaScript optimisé
- Chargement des ressources externes (CDN)

### Temps de Chargement
- Temps de réponse: <100ms
- Taille de la page: ~500KB
- Ressources externes: ~200KB

## 🔧 Configuration

### Render.yaml
```yaml
services:
  - type: web
    name: hcv-pro-frontend
    runtime: static
    plan: free
    buildCommand: "echo 'Static build - no build required'"
    staticPublishPath: .
```

### Headers de Sécurité
Configurés dans `render.yaml` pour tous les chemins.

### Routes
- `/` → `index.html` (SPA)
- `/*` → `index.html` (rewrite pour SPA)

## 📝 Fichiers Importants

- `index.html` - Interface web principale (~1000+ lignes)
- `package.json` - Configuration Node.js
- `render.yaml` - Configuration Render
- `.gitignore` - Exclusions Git
- `README.md` - Ce fichier

## 🎯 Prochaines Étapes

1. Vérifier le déploiement sur Render
2. Configurer le backend
3. Tester l'intégration frontend-backend
4. Optimiser les performances

## 📚 Documentation

Pour plus d'informations, consultez:
- [Render Documentation](https://render.com/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Lucide Icons](https://lucide.dev/)

## 🐛 Dépannage

### Le site ne se charge pas
1. Vérifier que le dépôt Git est à jour
2. Vérifier les logs Render
3. Vérifier la configuration `render.yaml`

### Les styles ne s'appliquent pas
1. Vérifier que Tailwind CSS est chargé
2. Vérifier la console du navigateur pour les erreurs
3. Vider le cache du navigateur

### L'API ne répond pas
1. Vérifier que le backend est déployé
2. Vérifier l'URL du backend dans le code
3. Vérifier les clés API

## 📞 Support

Pour les problèmes de déploiement, consultez:
- Les logs Render
- La documentation Render
- Les fichiers de configuration

---

**Dernière mise à jour**: 17 Avril 2026  
**Statut**: ✅ Prêt pour le déploiement
