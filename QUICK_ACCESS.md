# Accès Rapide — Interface Web Unifiée

## 🚀 Démarrage rapide

### 1. Démarrer le serveur
```bash
npm start
```

### 2. Ouvrir l'interface web
```
http://localhost:3000/unified_compression.html
```

## 📋 Fichiers à intégrer

### Backend
```bash
# Copier dans api/
api/precompressed_handler.js
api/precompressed_wrapper.py
api/routes_precompressed.js
```

### Frontend
```bash
# Copier dans public/
COMPRESSION-SOLUTIONS/unified_compression.html
```

### Serveur
```javascript
// Ajouter dans server.js
const { registerPrecompressedRoutes } = require('./api/routes_precompressed');
registerPrecompressedRoutes(app);
```

## 🎯 Utilisation

### 1. Sélectionner une image
- Glisser-déposer une image JPEG, PNG, WebP, GIF
- Ou cliquer pour sélectionner

### 2. Voir la recommandation
- Format détecté automatiquement
- Qualité estimée (pour JPEG)
- Stratégie recommandée affichée

### 3. Choisir la stratégie (optionnel)
- AUTO (recommandé)
- DIRECT (rapide)
- HYBRID (équilibre)
- TRANSCODE (optimal)

### 4. Compresser
- Cliquer "Compresser"
- Voir la barre de progression
- Résultats affichés en temps réel

### 5. Télécharger
- Cliquer "Télécharger"
- Fichier compressé sauvegardé

## 📊 Résultats affichés

- **Stratégie utilisée**: AUTO, DIRECT, HYBRID, ou TRANSCODE
- **Taille originale**: Taille du fichier d'entrée
- **Taille compressée**: Taille du fichier de sortie
- **Ratio**: Ratio de compression (ex: 8:1)
- **Économie**: Pourcentage d'économie (ex: 87.5%)
- **Temps**: Temps de traitement en ms

## 🎨 Interface

### Tabs
- 🖼️ **Images Pré-Compressées** (JPEG, PNG, WebP, GIF)
- 📷 **Images RAW** (À venir)
- 🎥 **Vidéos** (À venir)

### Stratégies
- **AUTO**: Détection automatique (recommandé)
- **DIRECT**: Compression fichier (rapide, ratio 1.1-1.3:1)
- **HYBRID**: Décoder → YCbCr → Compresser (équilibre, ratio 2-3:1)
- **TRANSCODE**: Décoder → Réencoder (optimal, ratio 8:1, qualité améliorée)

## 📈 Exemples de résultats

### JPEG Qualité Basse (Q=60)
```
Stratégie: TRANSCODE
Taille originale: 500 KB
Taille compressée: 62.5 KB
Ratio: 8:1
Économie: 87.5%
Temps: 2000ms
```

### JPEG Qualité Moyenne (Q=80)
```
Stratégie: HYBRID
Taille originale: 500 KB
Taille compressée: 200 KB
Ratio: 2.5:1
Économie: 60%
Temps: 500ms
```

### PNG
```
Stratégie: DIRECT
Taille originale: 1 MB
Taille compressée: 900 KB
Ratio: 1.1:1
Économie: 10%
Temps: 100ms
```

## 🔗 URLs

| URL | Description |
|-----|-------------|
| `http://localhost:3000/unified_compression.html` | Interface web unifiée |
| `POST /api/precompressed` | API upload |
| `GET /api/precompressed/download/:id` | Téléchargement |

## 🧪 Test rapide

### Avec curl
```bash
# Upload
curl -X POST http://localhost:3000/api/precompressed \
  -F "image=@test.jpg" \
  -F "strategy=AUTO"

# Télécharger
curl -X GET http://localhost:3000/api/precompressed/download/{outputId} \
  -o compressed.hcp
```

### Avec le script de test
```bash
bash test_web_integration.sh
```

## 📱 Responsive

L'interface est responsive et fonctionne sur :
- Desktop (1200px+)
- Tablet (768px-1199px)
- Mobile (< 768px)

## 🎯 Recommandations

### Pour JPEG
- **Q < 70**: Utiliser TRANSCODE (améliore qualité)
- **Q 70-85**: Utiliser HYBRID (équilibre)
- **Q > 85**: Utiliser DIRECT (préserve qualité)

### Pour PNG/WebP
- Toujours utiliser DIRECT (déjà optimisé)

### Pour archives mixtes
- Utiliser AUTO (détection + adaptation)

## 🔐 Sécurité

- ✅ Validation des chemins
- ✅ Validation des extensions
- ✅ Limite de taille (10 GB)
- ✅ Nettoyage automatique
- ✅ Gestion des erreurs

## 📞 Support

Pour les problèmes :
1. Vérifier que le serveur est en cours d'exécution
2. Vérifier que les fichiers sont copiés
3. Vérifier les dépendances Python
4. Consulter les logs du serveur
5. Exécuter le script de test

## 🚀 Déploiement

### Production
```bash
npm start
# Ouvrir http://votre-domaine.com/unified_compression.html
```

### Docker
```bash
docker build -t hcv-compression .
docker run -p 3000:3000 hcv-compression
```

---

**Interface web unifiée prête à l'emploi.**
