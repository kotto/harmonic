# 🎨 KA Phone — Prompts de Design pour IA

*À soumettre à v0.dev, Bolt.new, Lovable, ou tout autre générateur UI*

---

## Prompt 1 — Écran d'accueil (Home)

```
Design a mobile-first PWA home screen for "KA" — a personal AI phone companion.

KEY ELEMENTS:
- A living, breathing golden sphere (the AI's avatar) that pulses gently
- The sphere should have subtle wave-like animations (gold/amber tones)
- Dark background (#0a0a14) with subtle radial gradient
- Below the sphere: "KA" in elegant typography, with tagline "Ton Double Numérique"
- Bottom: status indicators (⚡ storage saved, 🧠 facts learned today, 💬 interactions)
- Minimalist. Premium feel. Dark mode.

INTERACTIONS:
- Tapping the sphere → brief ripple effect
- Pull down → refresh stats
- The sphere's pulse speed changes based on "AI activity"

TECHNICAL:
- Tailwind CSS, vanilla JS animations
- Mobile: 420px max-width, centered
- No framework. Self-contained HTML file.
```

---

## Prompt 2 — Écran de Chat

```
Design the chat screen for "KA" — a mobile PWA AI companion.

LAYOUT:
- Top: subtle header with KA's name and a small pulsing sphere icon
- Main area: chat messages with smooth scroll
  - User messages: right-aligned, dark surface with gold border
  - KA messages: left-aligned, darker surface, preceded by small sphere avatar
  - Timestamps below each message in subtle gray
- Bottom: input area with:
  - Microphone button (left) — for voice input
  - Text input (center) — rounded pill shape, dark glass effect
  - Send button (right) — gold circle with arrow
- Debug mode: when starting with "/debug", the input border glows cyan

ANIMATIONS:
- Messages appear with fade+slide-up
- KA "thinking" state: three dots pulsing (gold)
- The sphere avatar pulses faster when KA is responding
- Mic button pulses red when recording

TECHNICAL:
- Dark theme (#0a0a14 background, gold #d4a843 accent, cyan #00bcd4 for debug)
- Tailwind CSS
- Mobile: 420px max-width
- Self-contained HTML file
```

---

## Prompt 3 — Écran de Compression (Stockage)

```
Design the storage/compression screen for "KA" — a mobile PWA.

CONCEPT:
KA uses HCV compression to save storage space on your phone. Show the impact visually.

LAYOUT:
- Top: "Stockage" title with storage used/free bar
- A visual "before/after" comparison:
  - Left: "Avant KA" — phone icon with red warning, storage nearly full
  - Right: "Avec KA" — same phone with green check, plenty of space freed
- Animated counter showing space saved (e.g., "12.4 Go libérés")
- Big CTA button: "⚡ Optimiser maintenant" (gold, full width)
- Below: list of optimizations available:
  - 📸 Photos (3.2 Go → 0.4 Go) with toggle
  - 🎥 Vidéos (8.1 Go → 1.1 Go) with toggle
  - 📁 Documents (1.2 Go → 0.3 Go) with toggle

ANIMATIONS:
- Counter animates from 0 to saved amount
- Before/after comparison has a sliding divider
- Progress bar during compression

TECHNICAL:
- Dark theme, gold accent
- Tailwind CSS
- Mobile: 420px
- Self-contained
```

---

## Prompt 4 — Écran Système (Settings)

```
Design the system/settings screen for "KA" mobile PWA.

SECTIONS:
1. Profil KA
   - Avatar sphere (customizable color)
   - Name (editable)
   - "KA apprend de vous depuis X jours" stat

2. Mémoire personnelle
   - Toggle: "Apprentissage automatique" (KA learns from your habits)
   - Toggle: "Suggérer des optimisations" 
   - "Données stockées : X Mo (local uniquement)"
   - Button: "🗑️ Réinitialiser la mémoire"

3. Compression
   - "Compression automatique" toggle
   - "Qualité photo" slider (Éco ↔ Standard ↔ Haute)
   - Dernière optimisation: "il y a 3 jours • 2.1 Go libérés"

4. À propos
   - Version, licence, liens
   - "KA fonctionne sans Internet. Vos données ne quittent jamais votre téléphone."

TECHNICAL: Dark theme, gold accent, Tailwind, 420px, self-contained.
```

---

## Prompt 5 — Écran d'Appels (si pertinent)

```
Design the calls screen for "KA" mobile PWA. 

Simple interface showing:
- Recent interactions with KA (chat history snippets)
- A large centered button: "🎤 Parler à KA" (voice call-like interface)
- Below: quick actions
  - "🔍 Diagnostiquer un problème"
  - "📸 Optimiser mes photos"  
  - "💡 Apprendre quelque chose"

TECHNICAL: Dark theme, gold accent, Tailwind, 420px, self-contained.
```

---

## Prompt 6 — Onboarding (première expérience)

```
Design a 3-step onboarding flow for "KA" mobile PWA.

STEP 1: "Bienvenue"
- Golden sphere animation
- "Je suis KA, votre double numérique"
- Swipe/button to continue

STEP 2: "Ce que KA peut faire"
- Three cards with icons:
  - 🗜️ "Libérer de l'espace" — compresser photos/vidéos
  - 🧠 "Apprendre de vous" — s'adapter à vos habitudes
  - 💬 "Vous assister" — répondre à vos questions
- Swipe/button to continue

STEP 3: "Prêt"
- "KA est prêt. Tout reste sur votre téléphone. Rien ne sort."
- "🚀 Commencer" button

TECHNICAL: Dark theme, gold accent, Tailwind, smooth transitions between steps.
```

---

## Notes d'utilisation

1. **v0.dev** : coller un prompt à la fois, itérer avec des variantes
2. **Bolt.new** : idéal pour générer l'app complète avec backend
3. **Lovable** : bon pour le polish visuel et les animations
4. **Claude/Cursor** : pour générer le code HTML/CSS/JS directement

**Contrainte importante :** Tout doit tenir dans un seul fichier HTML avec CSS/JS inline (contrainte PWA). Pas de build step, pas de npm.
