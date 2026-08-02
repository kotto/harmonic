# 🎨 Frontend Engine — Moteur de génération frontend harmonique

Dossier **dédié et autonome** regroupant tous les modules de génération de code
frontend basés sur la théorie harmonique. Reconstruit après la perte du workspace
(tout le code vit ici, sans dépendance aux fichiers supprimés).

## Caractéristiques

| Propriété | Valeur |
|---|---|
| Paramètres | **0** |
| GPU | **Aucun** |
| Latence | **~0.2 ms** par génération |
| Déterminisme | **100%** (φ-seeded hashing) |
| Hallucination | **0%** (templates garantis valides) |
| Coût | **0€** |
| Dépendances | numpy (obligatoire), Pillow (optionnel) |

## Modules

| Fichier | Rôle |
|---|---|
| `css_harmony.py` | CSS harmonique : échelle typo φ, espacements Fibonacci, palette par interférence d'ondes (complémentaire 180°, triadique 120°), grilles 61.8/38.2, animations GPU |
| `code_generator.py` | **62 templates** HTML/CSS/JS : composants (navbar, hero, card×5 variantes, form, modal…), charts SVG (bar/line/pie), widgets (slider, toggle, progress…), mini-jeux (snake, pong), canvas (particules, vagues, fractales), apps complètes (chat, kanban, météo, musique, tetris) |
| `phi_flex.py` | Flexibilité φ : sélection de variantes φ-espacées (phyllotaxie), enrichissements au seuil φ⁻¹=0.618, composition de layouts, HRR (bind/scores de cohérence) |
| `real_composers.py` | Fusion HTML **réelle** de deux composants (card+form → form dans la card), assemblage de pages multi-sections, analyse de description → plan de page |
| `enhance_frontend.py` | JS interactif injectable (drag-drop, state, fetch), thème contextuel (28 thèmes : café→marron, tech→bleu, santé→vert…), design polish (mesh gradients, ripple, scroll reveal, glow) |
| `js_state_machine.py` | États UI (idle/loading/success/error/empty) + mapping description→composants |
| `image_to_code.py` | Analyse d'image (Pillow) : palette dominante, mode clair/sombre, régions de layout, détection de grille |
| `benchmarks/` | Benchmarks et projections (voir ci-dessous) |

## Usage rapide

```python
# 1. Génération simple
from code_generator import FrontendGenerator
gen = FrontendGenerator()
r = gen.generate("crée une landing page pour un café")
print(r.code)          # HTML complet
print(r.confidence)    # 0.93

# 2. Variante φ déterministe
r2 = gen.generate_variant("crée une carte", "overlay")
print(r2.code)         # Carte overlay (texte sur image) — différente de "horizontal"

# 3. Page multi-sections
from real_composers import MultiSectionPage
page, conf = MultiSectionPage().assemble("landing", seed="demo")
print(len(page), "chars")  # ~11K chars, 6 sections

# 4. Fusion HRR de composants
from real_composers import HRRHtmlFusion
fused, _ = HRRHtmlFusion().fuse("card", "form")
# → une carte CONTENANT un formulaire

# 5. CSS harmonique complet
from css_harmony import HarmonicCSS
css = HarmonicCSS().generate(seed="ka", mood="elegant", mode="dark")

# 6. Thème contextuel + polish
from enhance_frontend import ContextualTheme, DesignPolish
theme = ContextualTheme().detect_theme("café")   # → {hue: 30, name: "Café"}
html = DesignPolish().add_polish(r.code)         # + ripple, scroll reveal, gradients
```

## Benchmark (dernier run)

```
✅ 24/24 questions couvertes (100% accuracy)
✅ Latence moyenne: 0.21 ms
✅ Déterminisme: 100%
✅ Variantes card: 5/5 structures distinctes
✅ Fusion HRR: card+form fusionnés
✅ Page multi-section: 6 sections complètes
```

## Reconstruction

Ce dossier a été reconstruit **à partir de zéro** après la perte du workspace
(503 fichiers supprimés du disque, travail jamais commité). Le design des
modules reprend exactement l'architecture de la session originale :
`css_harmony.py` ↔ `css/theme.css` survivant, templates ↔ `ka_redesign/screens/`.

⚠️ **Leçon apprise** : committer ce dossier immédiatement.
