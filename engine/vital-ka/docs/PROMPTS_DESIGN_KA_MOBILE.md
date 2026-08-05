# Prompts de Design — KA Mobile
## Adapté au Design System v2 (`ka-design-system-v2.css`)

---

## Tokens de Design (extrait du CSS)

```
Couleurs :
  --ka-void       : #0e0e1a   (fond)
  --ka-deep       : #141428
  --ka-base       : #1c1c34
  --ka-surface    : #242440
  --ka-soul       : #9b94ff   (violet — primaire)
  --ka-life       : #4de8ae   (vert — succès)
  --ka-wisdom     : #f5cc6a   (doré — accent)
  --ka-rose       : #f2a8c4   (rose)
  --ka-sky        : #96c8f5   (bleu)

Typographie :
  --ka-font-sans  : -apple-system, "SF Pro Display", "Inter", system-ui
  --ka-font-mono  : "SF Mono", "JetBrains Mono", "Fira Code"
  Tailles : 10px → 36px (xs → 3xl)
  Graisses : 300 light, 400 regular, 500 medium

Verre (glass) :
  --ka-glass-1: rgba(255,255,255,.07)  →  --ka-glass-4: rgba(255,255,255,.24)
  --ka-blur-sm: blur(12px)  →  --ka-blur-xl: blur(64px)

Animations :
  --ka-ease-out: cubic-bezier(0,0,0.2,1)
  --ka-ease-spring: cubic-bezier(0.34,1.56,0.64,1)
  breathe 4s, blink 1.1s, drift 11s, pring 2.6s

Device : 375×812px, border-radius 48px, radial gradient fond
```

---

## Prompt 1 — Écran d'Accueil

```
Crée l'écran d'accueil de KA Mobile en utilisant le Design System v2.
CSS de référence : ka-design-system-v2.css

STRUCTURE :
1. Status bar (`.ka-statusbar`) avec l'heure
2. Sphère KA centrée (`.ka-home__sphere-wrap`) :
   - La sphère est un iframe vers /ka_sphere.html
   - Deux anneaux concentriques animés (`.ka-home__ring--1`, `.ka-home__ring--2`)
   - Animation `ka-pring` — pulsation qui s'étend
3. Message d'accueil (`.ka-home__greet`) :
   - h1: "KA" (30px, weight 300, letter-spacing -.025em)
   - p: "votre compagnon" (14px, text-3)
4. Barre d'intention (`.ka-home__ibar`) :
   - Fond glass-2, border-radius full, padding 12px 16px
   - Texte placeholder: "De quoi avez-vous besoin ?" (text-4)
   - Curseur clignotant
5. Grille d'accès rapide (`.ka-home__qa`) — 4 boutons :
   - 🖼️ Média | 💬 Compagnon | 🤖 Agent | 👤 Contacts
   - Icônes en cercle 56×56px, fond glass
6. Navigation (`.ka-nav`) : 5 icônes en bas

STYLE : utiliser EXCLUSIVEMENT les tokens CSS du design system.
Couleur primaire = var(--ka-soul) #9b94ff (violet).
Pas de or. Pas de stats. Pas de théorie. Épuré.
```

---

## Prompt 2 — Écran Média

```
Crée l'écran "Média" de KA Mobile — compression photo.

UTILISER les tokens du design system v2 :
- `.ka-stats` : grille 4 colonnes pour les métriques stockage
- `.ka-stat` : carte avec valeur + label
- `.ka-photo-grid` : grille 4 colonnes pour les miniatures
- `.ka-photo-thumb` : miniature 1:1, border-radius 10px
- `.ka-btn--life` : bouton vert pour "Compresser"
- `.ka-card` : carte glass pour le dashboard
- `.ka-bar-track` / `.ka-bar-fill` : barre de progression

STRUCTURE :
1. Stats row (.ka-stats) :
   - Utilisé | Après KA | Économisé | Ratio
   - Valeurs en --ka-text-1, labels en --ka-text-3
2. Barre de progression stockage (.ka-bar-track) :
   - Fill animé avec `ka-barGrow`
3. Grille photos (.ka-photo-grid) :
   - Miniatures avec ratio de compression
   - Dernière case "..." pour plus
4. Boutons d'action (`.ka-cta-row`) :
   - "Compresser tout" (.ka-btn--life)
   - "Choisir" (.ka-btn--soul)
5. Section outils :
   - Cards (.ka-card) pour Upscaler, Restaurer
   - Pills (.ka-pill) pour les catégories

COULEURS : vie/vert pour compression, âme/violet pour upscaling.
```

---

## Prompt 3 — Écran Compagnon (Chat)

```
Crée l'écran de conversation du compagnon KA.

UTILISER les composants du design system :
- `.ka-msgs` : conteneur de messages, flex column, scroll caché
- `.ka-msg--them` : messages reçus (KA) — fond glass, border-radius 18px, aligné à gauche
- `.ka-msg--me` : messages envoyés — fond violet (--ka-soul-dim), aligné à droite
- `.ka-msg--meta` : messages système centrés
- `.ka-msg--ka` : badge KA (pills violet)
- `.ka-sugs` : barre de suggestions (chips horizontaux)
- `.ka-sug` : chip individuel, fond glass, border-radius full
- `.ka-ibar` : barre de saisie avec sphère miniature, texte, curseur, bouton envoi
- `.ka-ibar__sphere` : mini sphère 32px animée (breathe)
- `.ka-ibar__cursor` : curseur clignotant (blink 1.1s)
- `.ka-ibar__send` : bouton envoi, apparaît quand du texte est saisi

STRUCTURE :
1. Messages (.ka-msgs) :
   - KA: "Bonjour, je suis KA. Comment puis-je vous aider ?"
   - Utilisateur: "Quel temps fait-il ?"
   - KA: réponse
   - Animation `ka-fu` (fade-in + slide-up) sur chaque nouveau message
2. Suggestions (.ka-sugs) :
   - "Raconte-moi une blague" | "Résume ma journée" | "Qui suis-je ?"
3. Barre de saisie (.ka-ibar) :
   - Sphère miniature à gauche
   - Texte placeholder "Écrivez votre message..."
   - Curseur clignotant
   - Bouton envoi (apparaît quand texte > 0)

ANIMATIONS : ka-fu pour les messages, ka-breathe pour la sphère, ka-blink pour le curseur.
```

---

## Prompt 4 — Écran Agent

```
Crée l'écran "Agent" de KA Mobile — tâches autonomes.

UTILISER :
- `.ka-card` / `.ka-card--raised` pour les tâches
- `.ka-pill` pour les statuts (--ka-life = terminé, --ka-wisdom = en cours, --ka-rose = échoué)
- `.ka-insight` pour les suggestions
- `.ka-timeline` / `.ka-timeline__item` pour l'historique
- `.ka-btn--soul` pour les actions

STRUCTURE :
1. Barre de commande (.ka-home__ibar style) :
   - "Que voulez-vous que KA fasse ?"
2. Tâches en cours (.ka-card--raised) :
   - Icône + titre + statut (pill)
   - Barre de progression (.ka-bar-track)
   - Bouton annuler
3. Mini-dashboard (.ka-stats) :
   - 👤 Contacts | 💬 Messages | ⏰ Rappels | 📞 Appels
4. Historique (.ka-timeline) :
   - Items avec dot coloré selon statut
   - Texte compact

ANIMATIONS : ka-barGrow pour les progressions, staggered delays.
```

---

## Prompt 5 — Écran Contacts

```
Crée l'écran "Contacts" de KA Mobile.

UTILISER :
- `.ka-card` pour les fiches contact
- `.ka-participant` / `.ka-participant__avatar` pour les avatars
- `.ka-pill` pour les tags (voix clonée, favoris)

STRUCTURE :
1. Barre de recherche (style .ka-home__ibar sans sphère)
2. Liste de contacts :
   - Avatar (initiales, fond coloré)
   - Nom, téléphone
   - Tags : 🎵 voix clonée, ⭐ favori
3. Boutons rapides par contact : 📞 Appeler | 💬 Message
4. Bouton "+" en bas à droite pour ajouter

COULEURS : avatars en --ka-soul, --ka-life, --ka-wisdom, --ka-rose, --ka-sky (rotation)
```

---

## Prompt 6 — Écran Appel

```
Crée l'écran d'appel vocal KA.

UTILISER :
- `.ka-call` : fond vert foncé (gradient)
- `.ka-call__avatar` : avatar 88px avec anneaux animés (ka-pring)
- `.ka-call__name` : nom du contact
- `.ka-call__status` : statut (vert)
- `.ka-call__timer` : durée
- `.ka-call__wave` : barres d'onde audio animées (ka-wave)
- `.ka-call__controls` : boutons mute, haut-parleur, clavier
- `.ka-call__end` : bouton raccrocher (rouge)

ANIMATIONS : ka-pring pour les anneaux, ka-wave pour l'audio.
```

---

## Règles Strictes

```
✅ UTILISER exclusivement les classes et tokens du design system v2
✅ Couleur primaire = --ka-soul (#9b94ff, violet)
✅ Succès = --ka-life (#4de8ae, vert)
✅ Accent = --ka-wisdom (#f5cc6a, doré)
✅ Device shell 375×812px, border-radius 48px
✅ Animations via @keyframes du design system
✅ Typo : --ka-font-sans, tailles via --ka-size-*
✅ Glass partout : --ka-glass-1 à 4, --ka-blur-sm à xl
✅ Mobile-first, PWA

❌ NE PAS inventer de nouvelles couleurs
❌ NE PAS utiliser d'or (#c9a84c) comme primaire — c'est le violet
❌ NE PAS mentionner Enterprise, PC, alpha, théorie
❌ NE PAS ajouter de stats ou de jargon technique
❌ NE PAS utiliser de classes hors design system
```
