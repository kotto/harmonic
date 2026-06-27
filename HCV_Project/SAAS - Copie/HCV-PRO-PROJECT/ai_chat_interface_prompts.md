# 🎨 Prompts pour Page d'Accueil IA (Style Perplexity)

## 🌊 Prompt Principal - Interface de Dialogue IA Moderne

### **Prompt Complet pour IA Génératrice:**

```
Crée une page d'accueil de type interface de dialogue IA pour "Harmonic AI Core" inspirée de Perplexity AI avec les spécifications suivantes:

**CONTEXTE:**
- Service: Harmonic AI Core
- Style: Interface de dialogue moderne (comme Perplexity)
- API Endpoint: http://15.188.57.52:8000
- Type: Chat interface avec pavé de prompt

**DESIGN REQUIS:**
- Interface épurée et minimaliste
- Fond blanc ou très clair
- Typographie moderne et lisible
- Design responsive (mobile et desktop)
- Animations subtiles de transitions
- Focus sur la zone de dialogue

**LAYOUT PRINCIPAL:**
1. Header simple avec logo "Connective AI"
2. Message de bienvenue central: "Bonjour, que puis-je faire pour vous ?"
3. Zone de saisie de prompt (grande et visible)
4. Suggestions de prompts en dessous
5. Footer minimaliste

**ZONE DE PROMPT:**
- Input large avec placeholder "Posez votre question..."
- Bouton d'envoi stylisé (flèche ou icône)
- Support pour multi-lignes
- Auto-redimensionnement selon contenu
- Animation de focus subtile

**SUGGESTIONS DE PROMPTS:**
- 3-4 suggestions cliquables sous la zone de saisie
- Style "pilule" ou "badge"
- Exemples: "Explique-moi Connective AI", "Génère du code Python", "Aide-moi à résoudre un problème"
- Animation au hover

**FONCTIONNALITÉS:**
- Appel API vers /generate quand utilisateur envoie
- Affichage de la réponse de l'IA
- Animation de "typing" pendant la génération
- Historique de conversation (côté client)
- Bouton pour effacer la conversation
- Support pour touches (Enter pour envoyer, Shift+Enter pour nouvelle ligne)

**TECHNOLOGIES:**
- HTML5 sémantique
- CSS3 avec animations fluides
- JavaScript vanilla
- Fetch API pour les appels
- Responsive design

**API INTEGRATION:**
- POST vers /generate avec format: {"prompt": "texte utilisateur"}
- Affichage de la réponse avec formatting Markdown
- Gestion des erreurs avec messages user-friendly
- Indicateur de chargement pendant la génération

Génère le code complet HTML/CSS/JavaScript dans un seul fichier avec une interface de dialogue moderne et professionnelle.
```

---

## 🎯 Prompt Minimaliste - Version Épurée

```
Crée une page d'accueil IA minimaliste pour Connective AI avec:

**INTERFACE:**
- Header simple: "Connective AI"
- Message central: "Bonjour, que puis-je faire pour vous ?"
- Zone de saisie de prompt (large, centrée)
- 3 suggestions de prompts cliquables
- Footer minimal

**STYLE:**
- Design ultra-épuré (style Perplexity)
- Fond blanc
- Typographie claire et moderne
- Espacements généreux
- Très peu d'éléments visuels

**FONCTIONNALITÉS:**
- Envoi du prompt vers /generate
- Affichage de la réponse
- Animation simple de chargement
- Support clavier (Enter pour envoyer)

**CODE:**
- HTML5, CSS3, JavaScript
- Design responsive
- Animations subtiles
- Appel API fetch

Génère une interface simple et élégante.
```

---

## 🌊 Prompt Avancé - Interface Complète

```
Crée une interface de dialogue IA complète pour Connective AI avec:

**LAYOUT COMPLET:**
1. Header avec logo et navigation
2. Zone de conversation (historique)
3. Zone de saisie avec suggestions
4. Sidebar avec paramètres
5. Footer avec informations

**CARACTÉRISTIQUES:**
- Interface de type chat (messages bulles)
- Support pour Markdown dans les réponses
- Code highlighting dans les réponses
- Mode sombre/clair
- Historique persistant (localStorage)
- Export de conversation

**ZONE DE PROMPT AVANCÉE:**
- Input multi-lignes avec redimensionnement
- Support pour pièces jointes (futur)
- Suggestions contextuelles
- Auto-complétion
- Raccourcis clavier

**FONCTIONNALITÉS AVANCÉES:**
- Streaming des réponses (si supporté)
- Gestion des erreurs avancée
- Analytics d'utilisation
- Personnalisation de l'interface
- Mode présentation

**API INTEGRATION:**
- Appels vers /health et /generate
- Gestion des timeouts
- Retry automatique
- Cache des réponses
- Rate limiting côté client

Génère une interface complète et professionnelle.
```

---

## 🚀 Prompt Rapide - Version Simple

```
Crée une page de dialogue IA simple pour Connective AI:

HTML:
- Header: "Connective AI"
- Message: "Bonjour, que puis-je faire pour vous ?"
- Zone de saisie de prompt
- Bouton d'envoi
- Zone d'affichage des réponses

CSS:
- Style moderne et épuré
- Design responsive
- Animations simples

JavaScript:
- Envoi vers /generate
- Affichage des réponses
- Animation de chargement

Génère une page simple et fonctionnelle.
```

---

## 🎯 Prompt Spécifique - Style Perplexity Exact

```
Crée une page d'accueil exactement dans le style de Perplexity AI pour Connective AI:

**STYLE PERPLEXITY:**
- Fond blanc cassé
- Typographie Inter ou similaire
- Interface minimaliste et épurée
- Grille centrée avec espacements précis
- Ombres subtiles et bordures fines

**COMPOSANTS EXACTS:**
1. Header avec logo à gauche
2. Zone de prompt au centre de l'écran
3. Message "Bonjour, que puis-je faire pour vous ?" au-dessus
4. Input large avec placeholder
5. 3-4 suggestions en dessous (style badges)
6. Footer minimaliste

**COMPORTEMENTS:**
- Focus automatique sur l'input
- Animation de focus subtile
- Hover effects sur les suggestions
- Transition douce entre états

**FONCTIONNALITÉS:**
- Envoi du prompt vers /generate
- Affichage de la réponse
- Animation de "thinking"
- Support clavier

Génère une réplique exacte du style Perplexity pour Connective AI.
```

---

## 🌊 Prompt pour Interface avec Historique

```
Crée une interface de dialogue IA avec historique pour Connective AI:

**LAYOUT:**
- Header avec logo
- Zone de conversation (déroulable)
- Zone de saisie fixe en bas
- Suggestions au-dessus de la saisie

**HISTORIQUE:**
- Messages utilisateur et IA différenciés
- Support pour Markdown
- Timestamp sur les messages
- Scroll automatique
- Bouton pour effacer l'historique

**FONCTIONNALITÉS:**
- Persistance localStorage
- Export conversation
- Recherche dans l'historique
- Mode plein écran
- Mode sombre

Génère une interface complète avec historique.
```

---

## 🎯 Prompt pour Mobile-First

```
Crée une interface de dialogue IA optimisée mobile pour Connective AI:

**MOBILE-FIRST:**
- Design responsive centré sur mobile
- Interface adaptée aux écrans tactiles
- clavier virtuel optimisé
- Performances sur mobile

**COMPOSANTS:**
- Header compact
- Zone de conversation optimisée
- Input adapté au mobile
- Suggestions cliquables avec doigts

**FONCTIONNALITÉS MOBILE:**
- Swipe pour effacer
- Pull-to-refresh
- Mode paysage supporté
- Performances optimisées

Génère une interface mobile-first moderne.
```

---

## 🚀 Instructions d'Utilisation

### **Comment utiliser ces prompts:**

1. **Choisissez le style** selon vos besoins
2. **Copiez-collez** dans l'IA génératrice
3. **Personnalisez** les couleurs et textes
4. **Testez** avec votre API
5. **Adaptez** selon vos retours

### **Personnalisation possible:**
- Modifier les couleurs du thème
- Changer les suggestions de prompts
- Ajouter des fonctionnalités
- Adapter les animations
- Intégrer votre branding

---

## 🌊 Notes Techniques

### **Points à considérer:**
- API Endpoint: http://15.188.57.52:8000
- Format de requête: POST /generate
- Réponse format JSON
- Branding: Connective AI uniquement
- Style inspiré de Perplexity

### **Bonnes pratiques:**
- Accessibilité WCAG
- Performance optimisée
- SEO friendly
- Sécurité des appels API
- Design responsive

---

## 🎯 Exemples de Suggestions de Prompts

### **Suggestions par défaut:**
- "Explique-moi ce qu'est Connective AI"
- "Génère-moi un exemple de code Python"
- "Aide-moi à résoudre un problème technique"
- "Crée-moi une documentation API"

### **Suggestions avancées:**
- "Analyse ce code et améliore-le"
- "Génère une page web complète"
- "Explique-moi l'architecture harmonique"
- "Crée des tests unitaires"

---

*Document créé pour Connective AI Labs - Prompts interface de dialogue IA*
