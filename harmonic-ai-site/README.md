# Harmonic AI - Site Institutionnel

Site internet institutionnel moderne pour Harmonic AI, une entreprise spécialisée dans l'intelligence artificielle déterministe et auditable.

## 🌐 Aperçu

Site web bilingue (français/anglais) présentant les solutions d'IA déterministe d'Harmonic AI avec un design épuré, des animations fluides et une interface utilisateur intuitive.

## 🏗️ Structure du Projet

```
harmonic-ai-site/
├── index.html              # Version française
├── index-en.html           # Version anglaise
├── css/
│   ├── styles.css         # Styles principaux
│   └── animations.css     # Animations CSS avancées
├── js/
│   ├── main.js            # Fonctionnalités principales
│   ├── animations.js      # Animations JavaScript
│   └── demo.js            # Démonstration interactive
├── docs/
│   ├── partners.html      # Documentation partenaires (EN)
│   └── partners-fr.html   # Documentation partenaires (FR)
├── images/                # Assets visuels
├── fonts/                 # Polices personnalisées
└── README.md              # Documentation
```

## 🎨 Design & Typographie

### Palette de Couleurs
- **Primaire** : `#1a237e` (bleu profond)
- **Secondaire** : `#ff6f00` (orange vif)
- **Neutres** : Blanc, gris clair, noir
- **Accents** : Bleu, vert, violet

### Typographie
- **Police principale** : Inter (sans-serif)
- **Police monospace** : JetBrains Mono (code)
- **Hiérarchie** : Basée sur le ratio d'or φ = 1.618

## ✨ Fonctionnalités

### 1. Navigation Responsive
- Menu fixe avec effet de flou
- Adaptation mobile/tablette/desktop
- Sélecteur de langue intégré

### 2. Animations Avancées
- Gradients harmoniques animés
- Système de particules interactif
- Apparitions progressives au scroll
- Effets de morphing de formes

### 3. Démonstration Interactive
- Interface de test en temps réel
- Mode vérifié vs mode déterministe
- Génération de Response_ID SHA256
- Historique des réponses

### 4. Documentation Partenaires
- Documentation technique complète
- Spécifications API détaillées
- Guide d'intégration étape par étape
- Ressources de support

## 🚀 Technologies Utilisées

### Frontend
- **HTML5** : Structure sémantique
- **CSS3** : Variables, Grid, Flexbox, Animations
- **JavaScript ES6+** : Modules, Classes, Async/Await

### Design System
- **Variables CSS** : Palette, espacements, durées
- **Design Responsive** : Mobile-first approach
- **Animations CSS** : Keyframes, transitions
- **JavaScript Animations** : RAF, systèmes de particules

## 📱 Responsive Design

### Points de Rupture
- **Mobile** : < 768px
- **Tablette** : 768px - 1024px
- **Desktop** : > 1024px

### Adaptations
- Navigation hamburger sur mobile
- Grilles adaptatives
- Typographie responsive
- Images optimisées

## 🎯 Sections du Site

### 1. Hero Section
- Titre principal avec gradient animé
- Description de la mission
- Carte de démonstration interactive
- Actions principales

### 2. Solutions
- Cartes présentant les fonctionnalités clés
- Icônes descriptives
- Liens vers plus d'informations

### 3. Technologie
- Présentation de l'approche harmonique
- Stack technique
- Métriques de performance

### 4. Secteurs
- Applications par industrie
- Métriques spécifiques par secteur
- Études de cas

### 5. À Propos
- Mission et vision
- Statistiques d'impact
- Valeurs de l'entreprise

### 6. Contact
- Formulaire de contact
- Informations de l'entreprise
- Support entreprise

## 🔧 Installation & Développement

### Prérequis
- Navigateur web moderne
- Éditeur de code (VS Code recommandé)
- Serveur local (optionnel)

### Démarrage Rapide
1. Clonez le dépôt
2. Ouvrez `index.html` dans un navigateur
3. Pour développement, utilisez un serveur local

### Structure des Fichiers
- `css/styles.css` : Styles principaux et variables
- `css/animations.css` : Animations et keyframes
- `js/main.js` : Logique principale et gestion d'état
- `js/animations.js` : Systèmes d'animation avancés
- `js/demo.js` : Interface de démonstration

## 🎭 Animations & Effets

### Système de Particules
- Particules flottantes avec physique
- Couleurs basées sur la palette
- Durées et tailles aléatoires
- Nettoyage automatique

### Gradients Animés
- Déplacement de gradient basé sur φ
- Transitions fluides
- Effets de profondeur

### Morphing de Formes
- Interpolation entre formes organiques
- Transitions continues
- Effets visuels dynamiques

## 📊 Performance

### Optimisations
- Images optimisées pour le web
- Minification CSS/JS (à implémenter)
- Chargement différé des ressources
- Cache efficace

### Métriques
- Temps de chargement : < 2s
- Score Lighthouse : > 90
- Compatibilité : Chrome, Firefox, Safari, Edge

## 🌍 Internationalisation

### Langues Supportées
- **Français** : `index.html`
- **Anglais** : `index-en.html`

### Sélecteur de Langue
- Interface bilingue
- Conservation de l'état
- Redirection appropriée

## 📄 Documentation

### Pour les Développeurs
- Variables CSS documentées
- Classes utilitaires
- API JavaScript

### Pour les Partenaires
- Documentation technique
- Guide d'intégration
- Support API

## 🔒 Sécurité

### Bonnes Pratiques
- Validation des formulaires
- Protection XSS
- HTTPS recommandé
- Authentification API

## 📈 SEO

### Optimisations
- Balises méta descriptives
- Structure sémantique HTML5
- URLs propres
- Performance mobile

### Métadonnées
- Titres optimisés
- Descriptions pertinentes
- Mots-clés ciblés
- Open Graph intégré

## 🛠️ Développement Futur

### Améliorations Planifiées
1. **Mode Sombre** : Support des préférences système
2. **Dashboard Admin** : Interface de gestion
3. **API GraphQL** : Alternative à REST
4. **WebSockets** : Mises à jour en temps réel
5. **PWA** : Installation native

### Évolutions Techniques
- **WebAssembly** : Calculs intensifs
- **WebGL** : Visualisations 3D
- **Service Workers** : Offline support
- **WebRTC** : Communication en temps réel

## 🤝 Contribution

### Guidelines
1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Standards de Code
- **HTML** : Sémantique, accessibilité
- **CSS** : BEM naming, variables
- **JavaScript** : ES6+, async/await, modules

## 📞 Support

### Contact
- **Email** : support@harmonic-ai.com
- **Site** : www.harmonic-ai.com
- **Documentation** : `/docs/`

### Ressources
- Guide d'intégration
- Référence API
- Exemples de code
- Forum communauté

## 📜 Licence

© 2026 Harmonic AI Corporation. Tous droits réservés.

Ce projet est la propriété intellectuelle d'Harmonic AI Corporation. Toute reproduction, distribution ou modification sans autorisation écrite est interdite.

---

**Harmonic AI** - Intelligence artificielle déterministe pour un monde fiable.