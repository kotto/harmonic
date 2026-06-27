# HARMONIC AI — SaaS Frontend & Design Prompts
## À soumettre à une IA experte en frontend/design (Claude, GPT-4, Cursor AI)

**Date :** 3 Juin 2026  
**Version :** 1.0  
**Langue cible :** Anglais (Français en option, toggle dans l'interface)

---

## Prompt 1 : Design System & Brand Identity

```
I need a complete design system and brand identity for a SaaS product called
"Harmonic AI" — a mathematical reasoning engine that verifies answers using
harmonic coherence (a physics-based truth criterion). No other AI does this.

The brand should convey:
- "Powered by the forces of the universe" (physics + math + resonance)
- Trust, precision, scientific rigor
- Elegance and sophistication
- NOT corporate, NOT playful — more like a scientific instrument than an app

Color palette:
- Primary background: Deep cosmic navy (#0A0E27 or similar)
- Secondary background: Dark slate (#1A1F3A or similar)
- Accent: Golden/amber for coherence and truth (#D4A843 or similar)
- Secondary accent: Soft violet/purple for resonance (#7B68EE or similar)
- Text: Warm white (#F0EDE6) for primary, muted gray (#8A8FA8) for secondary
- Confidence levels: 
    - High (≥70%): Emerald green (#10B981)
    - Medium (≥55%): Amber (#F59E0B)
    - Low (≥40%): Orange (#F97316)
    - Null (<40%): Red (#EF4444)

Typography:
- Headings: Playfair Display (serif, elegant, scientific feel)
- Body/UI: Inter (sans-serif, clean, modern)
- Monospace/code: JetBrains Mono (for mathematical expressions and tokens)

Design tokens I want defined:
- Spacing scale (4px base: 4, 8, 12, 16, 24, 32, 48, 64, 96)
- Border radius: 8px cards, 12px buttons, 16px modals, full for avatars
- Shadows: subtle cosmic glow effects (0 0 20px rgba(212,168,67,0.15))
- Animations: smooth 200ms transitions, no bouncing, no flashy effects
- Glassmorphism: frosted glass panels (backdrop-blur-xl, bg-white/5)

Logo concept (describe in text, I'll generate the SVG):
- A golden ratio spiral (φ = 1.618) formed by overlapping sine waves
- The spiral wraps around a glowing point (representing "resonance")
- Text: "HARMONIC AI" in Playfair Display, with a subtle golden gradient
- The dot on the "i" in "HARMONIC" is a golden version of φ

Design principles:
1. Clarity over cleverness
2. Data density is good — show the math, show the scores
3. Every number has a confidence badge (green/amber/orange/red dot)
4. The interface should feel like looking at a scientific instrument dashboard
5. Dark mode is the ONLY mode (this is a cosmic/quantum themed product)

Please generate:
1. A complete Tailwind CSS theme configuration (tailwind.config.js)
2. CSS custom properties for dark mode
3. A component library spec (Button, Card, Badge, Input, Modal, Chart)
4. ASCII art or text description of the logo
5. A typography scale
6. Icon recommendations (use Heroicons or Lucide — outline style preferred)
```

---

## Prompt 2 : API Integration & Data Flow

```
I have a Python backend that exposes a mathematical reasoning API. I need
you to design the complete frontend API integration layer.

The backend runs locally (or on the same server). Here are the endpoints:

=== ENDPOINT 1: Ask a mathematical question ===
POST /api/v1/ask
Content-Type: application/json

Request:
{
  "question": "derivative of x^3 + 2x^2 - 5x + 3",
  "lang": "en"  // "en" or "fr"
}

Response:
{
  "question": "derivative of x^3 + 2x^2 - 5x + 3",
  "domaine": "derivation",
  "type_calcul": "derivee",
  "resultat_sympy": "3*x**2 + 4*x - 5",
  "expression": "x^3 + 2x^2 - 5x + 3",
  "concepts": ["puissance", "exposant", "regle", "formule", "coefficient"],
  "scores_concepts": [0.69, 0.65, 0.64, 0.63, 0.62],
  "coherence": 0.653,
  "confiance": "moyenne",
  "source": "sympy",
  "phrase": "The derivative of x^3 + 2x^2 - 5x + 3 is 3x^2 + 4x - 5.",
  "temps_ms": 1.2
}

=== ENDPOINT 2: Solve with calculation ===
POST /api/v1/solve
(same format, but forces SymPy calculation)

=== ENDPOINT 3: Get system statistics ===
GET /api/v1/stats

Response:
{
  "total_questions": 1523,
  "avg_coherence": 0.67,
  "confiance_distribution": {"haute": 0.15, "moyenne": 0.75, "basse": 0.08, "nulle": 0.02},
  "avg_latency_ms": 1.2,
  "fallback_llm_rate": 0.05
}

Design requirements for the API layer:

1. Create an api.js module with:
   - async function askQuestion(question, lang='en') -> response object
   - async function solveQuestion(question, lang='en') -> response object
   - async function getStats() -> stats object
   - Error handling with graceful fallback UI
   - Loading states with skeleton screens
   - Debounced input (300ms) for the question field

2. The chat interface should:
   - Show the user's question on the right (cosmic blue bubble)
   - Show the AI's response on the left (slate bubble)
   - BELOW the AI response, show a "Confidence Card":
     * Confidence level badge (color-coded)
     * Coherence score (large number with percentage)
     * Domain identified (tag)
     * Concepts found with individual scores (mini bar charts)
     * Calculation result (if SymPy was used — rendered with KaTeX)
     * Time taken
   - Show skeleton loading animation while waiting
   - Support LaTeX rendering (use KaTeX CDN)

3. A stats dashboard showing:
   - Total questions answered (counter animation)
   - Confidence distribution (donut chart or horizontal bars)
   - Average coherence (gauge)
   - Average latency (number with ms suffix)
   - Fallback LLM usage rate (percentage)

4. Language toggle (EN/FR) that:
   - Sends the correct "lang" parameter to the API
   - Changes all UI text (use a translations object)
   - Persists the choice in localStorage

Please generate:
- Complete api.js module (vanilla JS or framework-agnostic)
- translations.js with EN and FR strings for all UI text
- stats.js with the dashboard logic using Chart.js (CDN)
- katex-config.js for LaTeX rendering setup
```

---

## Prompt 3 : Pages & Layout

```
I need the complete HTML/CSS for a SaaS web application. Here are the pages:

=== PAGE 1: Landing Page ===
URL: /
Purpose: Convert visitors into users

Sections (single page, scrollable):
1. HERO SECTION (full viewport)
   - Background: animated golden ratio spiral with subtle glow (CSS animation)
   - Headline: "Answers You Can Trust."
   - Subheadline: "The first AI that verifies mathematical reasoning against the laws of the universe. No hallucinations. Just truth."
   - CTA button: "Try for Free" → scrolls to demo section
   - Secondary link: "How it works" → scrolls to explanation

2. HOW IT WORKS (3 cards in a row)
   - Card 1: "Ask" - icon (question mark), "Ask any mathematical question in natural language"
   - Card 2: "Verify" - icon (checkmark/shield), "Our harmonic engine checks every concept for coherence against universal physical laws"
   - Card 3: "Trust" - icon (star/badge), "Get a confidence score from 0 to 100%. If we're not sure, we tell you."
   
3. DIFFERENTIATION TABLE (comparison table)
   - Columns: Harmonic AI | ChatGPT | Claude | DeepSeek
   - Rows: Calculation (✅/❌), Confidence Score (✅/❌), Hallucination-Proof (✅/❌), <1ms Response (✅/❌), GPU-Free (✅/❌)
   - Harmonic AI column has a golden border/glow

4. DEMO SECTION (interactive)
   - Text input with placeholder: "Try asking: derivative of x^3 + 2x^2..."
   - 4 example buttons: "Derivative", "Integral", "Equation", "Trigonometry"
   - Live response area that shows the answer with confidence badge
   - "This is a live demo. No signup required."

5. PRICING SECTION (3 tiers)
   - Free: 50 questions/month, basic domains
   - Pro ($19/mo): 1000 questions/month, all domains, API access
   - Enterprise (custom): Unlimited, on-premise, custom domains
   - Highlight the Pro tier (most popular)

6. FOOTER
   - Logo + tagline
   - Links: About, Blog, API Docs, Contact, Privacy, Terms
   - Copyright: "© 2026 Harmonic AI. Built on the laws of physics."

=== PAGE 2: Dashboard / Chat ===
URL: /app
Requires authentication (for now, just show the interface)

Layout:
- Header (fixed): Logo, breadcrumb, language toggle, user avatar (placeholder)
- Main area: Chat interface with sidebar

Sidebar (left, 256px):
- New Chat button
- Chat history list (mock entries)
- Domain filter: [All] [Derivation] [Integration] [Equations] [Trigonometry] [Geometry] [Probabilities] [Limits]
- Stats link
- Settings link

Chat area (right, remaining space):
- Empty state: "Ask a mathematical question..." with example prompts
- Message list (scrollable)
- Input area (bottom, sticky):
  * Text input (expanding textarea)
  * Send button (golden, with send icon)
  * Math mode toggle (for LaTeX input)
  * Attach/latex button

=== PAGE 3: Stats Dashboard ===
URL: /stats
- Total questions counter (animated number)
- Confidence distribution (horizontal bar chart using Chart.js)
- Average coherence gauge (semi-circle)
- Average latency (big number)
- Domain breakdown (pie chart)
- Fallback LLM usage (percentage bar)

=== MOBILE RESPONSIVENESS ===
- All pages must be fully responsive
- Landing page: stack cards vertically on mobile
- Chat: full-width on mobile, sidebar becomes a slide-out drawer
- Stats: charts resize to fit viewport

Please generate complete HTML/CSS/JS for all three pages using:
- Tailwind CSS (CDN)
- Chart.js (CDN) for charts
- KaTeX (CDN) for math rendering
- Font Awesome 6 or Lucide icons (CDN)
- Vanilla JavaScript (no React/Vue — keep it simple and fast)
- All in a single index.html with JavaScript routing or separate HTML files
```

---

## Prompt 4 : Chat Interface & Confidence Display (THE KEY DIFFERENTIATOR)

```
I need the most important component of our SaaS: the mathematical chat
interface with confidence display. This is what makes us different from
ChatGPT/Claude/DeepSeek.

=== THE CONFIDENCE CARD ===

After every AI response, show this card. It MUST be visually distinct
and immediately communicate trust level.

Design spec:
```
┌─────────────────────────────────────────────────────┐
│  ✓ COHERENCE VERIFIED — 65%                         │
│  ┌─────────────────────────────────────────────┐    │
│  │ 🟢🟢🟢🟢🟢🟢🟢🟢🟢🟡🟡🟡🟡🟡⚪⚪⚪⚪⚪  │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  Domain: Derivation                                  │
│                                                      │
│  Concepts found:                                     │
│  puissance    ████████████████░░░░  69%  🟢🟢🟢🟢🟡 │
│  exposant     ██████████████░░░░░░  65%  🟢🟢🟢🟢🟡 │
│  regle        █████████████░░░░░░░  64%  🟢🟢🟢🟡🟡 │
│  formule      █████████████░░░░░░░  63%  🟢🟢🟢🟡🟡 │
│  coefficient  ████████████░░░░░░░░  62%  🟢🟢🟢🟡🟡 │
│                                                      │
│  Calculation (SymPy): 3x² + 4x - 5                   │
│  Response time: 1.2ms                                 │
└─────────────────────────────────────────────────────┘
```

Confidence level colors:
- High (≥70%): Green header, "✓ COHERENCE VERIFIED"
- Medium (≥55%): Amber header, "⚠ COHERENCE MODERATE"
- Low (≥40%): Orange header, "⚡ COHERENCE WEAK"
- Null (<40%): Red header, "✗ COHERENCE NOT FOUND — Answer rejected"

The confidence bar should use a gradient:
- Left side (high confidence): solid green
- Middle: gradient to amber
- Right side (low): gradient to gray/red
- Filled up to the coherence percentage

When the LLM fallback is used, show a special card:
```
┌─────────────────────────────────────────────────────┐
│  🤖 FALLBACK MODE — LLM ASSISTED                     │
│                                                      │
│  The harmonic engine could not verify this answer    │
│  with confidence. The response was generated by a     │
│  language model and verified post-generation.         │
│                                                      │
│  LLM Coherence: 52%  ⚠                               │
│  Source: DeepSeek-R1                                 │
│                                                      │
│  "The derivative of x^3 is 3x^2..."                  │
└─────────────────────────────────────────────────────┘
```

=== MATHEMATICAL EXPRESSION RENDERING ===

- All mathematical expressions MUST be rendered with KaTeX
- Inline expressions: $f(x) = x^2$
- Block expressions: $$\\frac{d}{dx}x^3 = 3x^2$$
- The question input should support LaTeX with a toggle button [$]
- Results from SymPy should be automatically formatted with KaTeX

=== SKELETON LOADING STATE ===

While waiting for the API response:
- Show a card with pulsing bars (skeleton animation)
- 3 bars for concepts (different widths)
- 1 bar for the answer (long)
- Animated shimmer effect

=== EMPTY STATE ===

When no conversation has started:
- Large icon (golden ratio spiral SVG)
- "Ask a mathematical question"
- Subtitle: "Try asking about derivatives, integrals, equations, or trigonometry"
- 4 example chips that auto-fill the input when clicked

Please generate the complete HTML/CSS/JS for:
1. The Confidence Card component (all 4 states)
2. The Fallback LLM card
3. The Chat Message component (user + AI bubbles)
4. The Skeleton Loading component
5. The Empty State component
6. The Chat Input with LaTeX toggle
7. All with Tailwind CSS, vanilla JS, KaTeX rendering
```

---

## Prompt 5 : Complete SaaS Package

```
Generate the COMPLETE SaaS application as a single index.html file (or
a minimal project structure) that includes ALL of the following:

=== INCLUDED PAGES (routing via hash or simple JS) ===
1. #/ (Landing page — defined in Prompt 3)
2. #/app (Chat dashboard — defined in Prompt 3)
3. #/stats (Statistics dashboard — defined in Prompt 3)

=== TECHNICAL REQUIREMENTS ===

1. NO BUILD STEP — Everything loads from CDN, works by opening index.html
2. Tailwind CSS via CDN: <script src="https://cdn.tailwindcss.com"></script>
3. Chart.js via CDN for charts
4. KaTeX via CDN for math rendering
5. Lucide icons via CDN (or Font Awesome)
6. Vanilla JavaScript — NO React, NO Vue, NO framework
7. Single Page Application with hash-based routing (#/page)
8. All API calls go to localhost:8080 (configurable)
9. Language toggle EN/FR with localStorage persistence
10. localStorage for chat history (persist conversations)
11. Fully responsive (mobile-first breakpoints)
12. Dark mode ONLY (it's a design choice, not a toggle)

=== FILE STRUCTURE ===

```
harmonic-saas/
├── index.html          (main entry point, SPA)
├── css/
│   └── styles.css      (custom styles beyond Tailwind)
├── js/
│   ├── app.js           (router, init, global state)
│   ├── api.js           (all API calls)
│   ├── translations.js  (EN/FR strings)
│   ├── components/
│   │   ├── chat.js      (chat interface logic)
│   │   ├── confidence-card.js (confidence display)
│   │   ├── stats.js     (dashboard charts)
│   │   ├── landing.js   (landing page interactions)
│   │   └── demo.js      (demo section on landing)
│   └── utils.js         (helpers, formatters)
└── assets/
    └── logo.svg         (harmonic AI logo)
```

=== FUNCTIONAL REQUIREMENTS ===

1. Landing page demo must make REAL API calls to localhost:8080/api/v1/ask
2. Chat interface must make REAL API calls and display responses
3. Stats dashboard must fetch from localhost:8080/api/v1/stats
4. If API is unavailable, show a graceful offline message
5. Chat history persists in localStorage
6. Confidence card renders correctly for all 4 confidence levels
7. KaTeX renders all mathematical expressions
8. Language toggle switches ALL UI text
9. Mobile responsive: hamburger menu for navigation
10. Keyboard shortcut: Enter to send, Shift+Enter for newline

=== EXACT API CALLS TO IMPLEMENT ===

```javascript
// API base URL (configurable)
const API_BASE = 'http://localhost:8080';

// Ask a question
async function askQuestion(question, lang = 'en') {
    const response = await fetch(`${API_BASE}/api/v1/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, lang })
    });
    return await response.json();
}

// Get stats
async function getStats() {
    const response = await fetch(`${API_BASE}/api/v1/stats`);
    return await response.json();
}
```

=== EXAMPLE RESPONSE TO RENDER ===

Given this response:
```json
{
    "question": "derivative of x^3 + 2x^2 - 5x + 3",
    "concepts": ["puissance", "exposant", "regle", "formule"],
    "scores_concepts": [0.69, 0.65, 0.64, 0.63],
    "coherence": 0.653,
    "confiance": "moyenne",
    "domaine": "derivation",
    "resultat_sympy": "3*x**2 + 4*x - 5",
    "phrase": "The derivative of x³ + 2x² - 5x + 3 is 3x² + 4x - 5.",
    "temps_ms": 1.2
}
```

The UI should show:
1. The user's question in a right-aligned bubble
2. The answer phrase in a left-aligned bubble
3. A confidence card with:
   - "⚠ COHERENCE MODERATE — 65%" header (amber)
   - Confidence bar filled to 65%
   - Domain badge: "derivation"
   - 4 concept rows with bars and scores
   - SymPy result rendered in KaTeX: $3x^2 + 4x - 5$
   - "1.2ms" response time
4. Math expressions properly formatted:
   - Convert `x^3` → `x^3`
   - Convert `3*x**2` → `3x^2`
   - Convert `3*x**2 + 4*x - 5` → `3x^2 + 4x - 5`

=== DELIVERABLES ===

Please generate ALL files needed for a complete, working SaaS application.
I will copy them to my server and they should work immediately (open index.html).
The backend API is running on localhost:8080.

DO NOT use any framework. Pure HTML/CSS/JS with CDN dependencies only.
This is a scientific/mathematical product. The design should reflect that.
```

---

## Prompt 6 : French Localization

```
Add complete French (FR) localization to the SaaS application. The English
version is the default. A language toggle (🇬🇧/🇫🇷) should switch all text.

=== ALL TEXT TO TRANSLATE ===

Navigation:
- "Home" → "Accueil"
- "Dashboard" → "Tableau de bord"  
- "Statistics" → "Statistiques"
- "API Docs" → "Documentation API"
- "Settings" → "Paramètres"

Landing Page:
- "Answers You Can Trust." → "Des réponses en qui vous pouvez avoir confiance."
- "The first AI that verifies mathematical reasoning against the laws of the universe. No hallucinations. Just truth."
  → "La première IA qui vérifie le raisonnement mathématique contre les lois de l'univers. Aucune hallucination. Juste la vérité."
- "Try for Free" → "Essayer gratuitement"
- "How it works" → "Comment ça marche"
- "Ask" → "Demandez"
- "Ask any mathematical question in natural language"
  → "Posez n'importe quelle question mathématique en langage naturel"
- "Verify" → "Vérifiez"
- "Our harmonic engine checks every concept for coherence"
  → "Notre moteur harmonique vérifie chaque concept pour sa cohérence"
- "Trust" → "Faites confiance"
- "Get a confidence score. If we're not sure, we tell you."
  → "Recevez un score de confiance. Si nous ne sommes pas sûrs, nous vous le disons."

Chat Interface:
- "Ask a mathematical question..." → "Posez une question mathématique..."
- "Try asking: derivative of x^3 + 2x^2..."
  → "Essayez : dérivée de x^3 + 2x^2..."
- "Send" → "Envoyer"
- "New Chat" → "Nouvelle discussion"
- "Chat History" → "Historique"

Confidence Card:
- "COHERENCE VERIFIED" → "COHÉRENCE VÉRIFIÉE"
- "COHERENCE MODERATE" → "COHÉRENCE MODÉRÉE"
- "COHERENCE WEAK" → "COHÉRENCE FAIBLE"
- "COHERENCE NOT FOUND" → "COHÉRENCE NON TROUVÉE"
- "Answer rejected" → "Réponse rejetée"
- "Domain:" → "Domaine :"
- "Concepts found:" → "Concepts trouvés :"
- "Calculation:" → "Calcul :"
- "Response time:" → "Temps de réponse :"
- "FALLBACK MODE — LLM ASSISTED" → "MODE FALLBACK — ASSISTÉ PAR LLM"
- "The harmonic engine could not verify this answer"
  → "Le moteur harmonique n'a pas pu vérifier cette réponse"
- "The response was generated by a language model and verified post-generation."
  → "La réponse a été générée par un modèle de langage et vérifiée a posteriori."

Stats Dashboard:
- "Total Questions" → "Questions totales"
- "Average Coherence" → "Cohérence moyenne"
- "Average Latency" → "Latence moyenne"
- "Confidence Distribution" → "Distribution de confiance"
- "Domain Breakdown" → "Répartition par domaine"
- "High" → "Haute"
- "Medium" → "Moyenne"
- "Low" → "Basse"
- "Null" → "Nulle"

Pricing:
- "Free" → "Gratuit"
- "Pro" → "Pro"
- "Enterprise" → "Entreprise"
- "questions/month" → "questions/mois"
- "Most popular" → "Le plus populaire"

Error states:
- "Unable to connect to the server" → "Impossible de se connecter au serveur"
- "Please check your internet connection" → "Veuillez vérifier votre connexion internet"
- "An error occurred" → "Une erreur s'est produite"

=== IMPLEMENTATION ===

Create a translations.js file with this structure:
```javascript
const TRANSLATIONS = {
    en: {
        nav: { home: "Home", dashboard: "Dashboard", stats: "Statistics", ... },
        landing: { hero_title: "Answers You Can Trust.", ... },
        chat: { placeholder: "Ask a mathematical question...", ... },
        confidence: { verified: "COHERENCE VERIFIED", ... },
        stats: { total: "Total Questions", ... },
        pricing: { free: "Free", ... },
        errors: { connection: "Unable to connect to the server", ... },
    },
    fr: {
        nav: { home: "Accueil", dashboard: "Tableau de bord", ... },
        // ... all French translations
    }
};

function t(key, lang = 'en') {
    // key is dot-notation: "nav.home", "landing.hero_title"
    const keys = key.split('.');
    let value = TRANSLATIONS[lang];
    for (const k of keys) {
        value = value?.[k];
    }
    return value || key;
}

function getCurrentLang() {
    return localStorage.getItem('lang') || 'en';
}

function setLang(lang) {
    localStorage.setItem('lang', lang);
    // Re-render all text
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.dataset.i18n, lang);
    });
}
```

Usage in HTML:
```html
<h1 data-i18n="landing.hero_title">Answers You Can Trust.</h1>
<button data-i18n="landing.cta">Try for Free</button>
```
```

---

## How to Use These Prompts

1. **Copy one prompt at a time** and submit to Claude, GPT-4, Cursor AI, or Copilot
2. **Start with Prompt 1** (Design System) — this establishes the visual foundation
3. **Then Prompt 2** (API Integration) — connects frontend to backend
4. **Then Prompt 3** (Pages) — builds the actual user-facing pages
5. **Then Prompt 4** (Confidence Card) — our key differentiator
6. **Then Prompt 5** (Complete Package) — assembles everything
7. **Finally Prompt 6** (French) — adds localization

**Total estimated generation time:** 1-2 hours across all prompts
**Result:** A complete, production-ready SaaS frontend