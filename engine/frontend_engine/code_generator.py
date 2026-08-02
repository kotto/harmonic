"""
💻 Code Generator Frontend — Templates HTML/CSS/JS (autonome, reconstruit)
============================================================================
Version standalone du générateur de templates frontend.
Zéro dépendance externe (numpy requis uniquement pour le WaveSynthesizer).

Usage:
    from code_generator import WaveSynthesizer, PatternDetector
    synth = WaveSynthesizer()
    code, conf = synth._synth_card('html', 'card', 'card', [], variant='overlay')
"""

import re, math, time, hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

PHI = 1.618033988749895
TAU = 2.0 * math.pi


# ═══════════════════════════════════════════════════════════════════
# HELPERS AUTONOMES (remplacent harmonic_brain._normalize/_tokenize)
# ═══════════════════════════════════════════════════════════════════

_ACCENTS = str.maketrans(
    'éèêëàâäîïôöùûüçñ',
    'eeeeaaaiioouuucn'
)
def _normalize(text: str) -> str:
    """Normalise un texte (minuscules, accents supprimés)."""
    return text.lower().translate(_ACCENTS)

def _tokenize(text: str) -> List[str]:
    """Tokenise un texte en mots."""
    return re.findall(r'[a-z0-9]+', _normalize(text))


@dataclass
class FactRecord:
    """Enregistrement de fait minimal (stub autonome)."""
    sujet: str = ''
    relation: str = ''
    objet: str = ''
    amplitude: float = 1.0


# ═══════════════════════════════════════════════════════════════════
# PATTERN DETECTOR
# ═══════════════════════════════════════════════════════════════════

@dataclass
class CodeIntent:
    raw: str
    intent: str = 'function'
    language: str = 'html'
    operation: str = 'create'
    entity: str = 'generic'
    input_type: str = 'string'
    output_type: str = 'void'
    constraints: List[str] = field(default_factory=list)
    confidence: float = 0.0


class PatternDetector:
    """Détecte l'intention frontend à partir d'une requête naturelle."""

    INTENT_MARKERS = {
        'ui_component': ['composant', 'component', 'carte', 'card', 'bouton', 'button',
                        'navbar', 'footer', 'formulaire', 'form', 'modal', 'hero',
                        'dashboard', 'tableau de bord', 'gallery', 'galerie',
                        'témoignage', 'testimonial', 'faq', 'pricing', 'tarifs'],
        'page': ['page', 'landing', 'site', 'accueil', 'portfolio', 'blog'],
    }

    LANGUAGE_MARKERS = {
        'html': ['html', 'page web', 'site web'],
        'css': ['css', 'style', 'scss', 'tailwind'],
        'javascript': ['javascript', 'js', 'react', 'vue'],
        'jsx': ['jsx', 'tsx', 'react'],
    }

    # Toutes les opérations frontend (50+)
    OPERATION_MARKERS = {
        'navbar': ['navbar', 'barre de navigation', 'menu navigation'],
        'hero': ['hero', 'bannière', 'banner', 'accroche'],
        'card': ['carte', 'card', 'fiche', 'vignette'],
        'footer': ['footer', 'pied de page', 'bas de page'],
        'form': ['formulaire', 'form', 'champ', 'input', 'contact'],
        'modal': ['modal', 'modale', 'popup', 'dialogue'],
        'button': ['bouton', 'button', 'btn', 'cta'],
        'dashboard': ['dashboard', 'tableau de bord', 'admin', 'panneau'],
        'landing_page': ['landing page', "page d'atterrissage", "page d'accueil", 'one page'],
        'pricing': ['pricing', 'tarifs', 'prix', 'abonnement'],
        'testimonial': ['témoignage', 'temoignage', 'testimonial', 'avis client', 'review'],
        'faq': ['faq', 'questions fréquentes'],
        'contact_form': ['formulaire de contact', 'nous contacter'],
        'gallery': ['galerie', 'gallery', 'portfolio', "grille d'images"],
        'sidebar': ['sidebar', 'menu latéral', 'panneau latéral', 'aside'],
        'table': ['tableau', 'table', 'données tabulaires'],
        'blog_layout': ['blog', 'articles', "liste d'articles", 'posts'],
        'color_palette': ['palette', 'couleurs', 'color palette', 'theme colors'],
        'type_scale': ['typographie', 'typo', 'font size'],
        'dark_theme': ['dark mode', 'mode sombre', 'thème sombre', 'dark theme'],
        'animation': ['animation', 'keyframe', 'transition', 'fade', 'slide', 'pulse'],
        'responsive_grid': ['grille', 'grid', 'responsive', 'colonnes'],
        'flexbox_layout': ['flexbox', 'flex', 'disposition flexible'],
        'glassmorphism': ['glassmorphism', 'verre', 'glass', 'flou'],
        'css_reset': ['reset', 'normalize', 'css reset'],
        'fetch_error': ['fetch', 'api call', 'load data', 'chargement données'],
        'bar_chart': ['bar chart', 'graphique barres', 'barres', 'histogramme'],
        'line_chart': ['line chart', 'graphique ligne', 'courbe', 'tendance'],
        'pie_chart': ['pie chart', 'camembert', 'secteurs'],
        'slider': ['slider', 'curseur', 'range'],
        'toggle': ['toggle', 'switch', 'bascule', 'interrupteur'],
        'progress': ['progression', 'progress bar', 'barre progression'],
        'star_rating': ['étoiles', 'stars', 'rating', 'notation'],
        'timeline': ['timeline', 'chronologie', 'frise'],
        'calendar': ['calendrier', 'calendar', 'date picker'],
        'snake_game': ['snake', 'serpent', 'jeu snake'],
        'pong_game': ['pong', 'jeu pong'],
        'particles': ['particules', 'particles'],
        'waves_canvas': ['vagues', 'waves', 'ondes canvas'],
        'fractal': ['fractale', 'fractal', 'mandelbrot'],
        'carousel': ['carousel', 'carrousel', 'diaporama'],
        'tabs': ['tabs', 'onglets', 'tab navigation'],
        'accordion': ['accordion', 'accordéon', 'repliable'],
        'tooltip': ['tooltip', 'infobulle', 'bulle aide'],
        'dropdown': ['dropdown', 'menu déroulant'],
        'breadcrumb': ['breadcrumb', 'fil ariane'],
        'pagination': ['pagination', 'pages', 'paginer'],
        'search_bar': ['barre recherche', 'search bar', 'autocomplete'],
        'toast': ['toast', 'notification', 'snackbar'],
        'skeleton': ['skeleton', 'squelette', 'loading placeholder'],
        'code_editor': ['éditeur code', 'éditeur de code', 'code editor', 'syntax highlighting', 'éditeur'],
        'file_upload': ['upload fichier', 'upload de fichier', 'file upload', 'dropzone', 'upload'],
        'audio_player': ['lecteur audio', 'audio player', 'music player'],
        'color_picker': ['color picker', 'sélecteur couleur'],
        'infinite_scroll': ['infinite scroll', 'défilement infini', 'load more'],
        'chat_app': ['chat app', 'application chat', 'messagerie', 'chat interface'],
        'kanban': ['kanban', 'tableau kanban', 'board tâches'],
        'weather_app': ['météo', 'weather app', 'prévision météo', 'forecast'],
        'music_player': ['lecteur musique', 'music player', 'spotify'],
        'tetris': ['tetris', 'jeu tetris', 'blocs qui tombent'],
    }

    # Operations spécifiques qui priment sur 'create'
    SPECIFIC_OPS = set(OPERATION_MARKERS.keys())

    def detect(self, question: str) -> CodeIntent:
        q = _normalize(question)
        words = set(q.split())

        intent_scores: Dict[str, float] = {}
        for intent, markers in self.INTENT_MARKERS.items():
            for m in markers:
                if m in q:
                    intent_scores[intent] = intent_scores.get(intent, 0) + 1.0
        intent = 'ui_component' if intent_scores else 'function'
        if intent_scores.get('page', 0) > intent_scores.get('ui_component', 0):
            intent = 'page'

        lang_scores: Dict[str, float] = {}
        for lang, markers in self.LANGUAGE_MARKERS.items():
            for m in markers:
                if m in q:
                    lang_scores[lang] = lang_scores.get(lang, 0) + 1.0
        language = max(lang_scores, key=lang_scores.get) if lang_scores else 'html'

        op_scores: Dict[str, float] = {}
        for op, markers in self.OPERATION_MARKERS.items():
            for m in markers:
                # Normaliser aussi les marqueurs (accents → sans accents)
                nm = _normalize(m)
                if nm in q or nm in words:
                    weight = 3.0 if op in self.SPECIFIC_OPS else 1.0
                    op_scores[op] = op_scores.get(op, 0) + weight
        operation = max(op_scores, key=op_scores.get) if op_scores else 'card'

        confidence = min(1.0, (len(intent_scores) + len(op_scores) + len(lang_scores)) / 5.0)
        return CodeIntent(raw=question, intent=intent, language=language,
                          operation=operation, confidence=confidence)


# ═══════════════════════════════════════════════════════════════════
# WAVE SYNTHESIZER — Templates frontend
# ═══════════════════════════════════════════════════════════════════

class WaveSynthesizer:
    """Synthétise le code frontend à partir de templates."""

    def __init__(self, dim: int = 64):
        self.dim = dim

    def synthesize(self, intent: CodeIntent, brain_facts: List[FactRecord] = None) -> Tuple[str, float]:
        """Dispatch l'intention vers le template approprié."""
        op = intent.operation
        method = getattr(self, f'_synth_{op}', None)
        if method:
            try:
                return method(intent.language, op, intent.entity, brain_facts or [])
            except TypeError:
                try:
                    return method(intent.language, op, intent.entity, brain_facts or [], variant='default')
                except Exception:
                    pass
        return self._synth_generic(intent.language, op)

    def _synth_generic(self, lang: str, name: str) -> Tuple[str, float]:
        return f'<div class="{name}">\n  <!-- TODO: {name} -->\n  <p>Contenu</p>\n</div>', 0.5

    # ════════════════ CSS TEMPLATES ════════════════

    def _synth_color_palette(self, lang, name, entity, facts):
        return (f'/* ═══ Palette Harmonique ═══ */\n'
                f':root {{\n'
                f'  --color-primary: hsl(262, 60%, 55%);\n  --color-primary-hover: hsl(262, 65%, 48%);\n'
                f'  --color-secondary: hsl(82, 60%, 55%);\n  --color-accent: hsl(22, 85%, 55%);\n'
                f'  --color-bg: hsl(262, 20%, 97%);\n  --color-bg-alt: hsl(262, 15%, 93%);\n'
                f'  --color-text: hsl(262, 15%, 12%);\n  --color-text-muted: hsl(262, 10%, 45%);\n'
                f'  --color-muted: hsl(262, 10%, 88%);\n  --color-border: hsl(262, 12%, 82%);\n'
                f'  --color-success: hsl(145, 50%, 45%);\n  --color-warning: hsl(38, 92%, 50%);\n'
                f'  --color-error: hsl(5, 72%, 52%);\n  --color-info: hsl(207, 70%, 52%);\n'
                f'  --gradient-primary: linear-gradient(135deg, var(--color-primary), var(--color-accent));\n'
                f'  --shadow-md: 0 4px 12px rgba(0,0,0,0.12);\n'
                f'  --radius-md: 8px; --radius-lg: 16px; --radius-full: 9999px;\n'
                f'}}'), 0.90

    def _synth_type_scale(self, lang, name, entity, facts):
        return (f'/* ═══ Échelle Typographique (φ = 1.618) ═══ */\n'
                f':root {{\n  --text-caption: 0.618rem;\n  --text-small: 0.8rem;\n'
                f'  --text-body: 1rem;\n  --text-h4: 1.272rem;\n  --text-h3: 1.618rem;\n'
                f'  --text-h2: 2.058rem;\n  --text-h1: 2.618rem;\n  --text-hero: 3.33rem;\n'
                f'  --text-body-lh: 1.618;\n  --text-heading-lh: 1.15;\n}}\n'
                f'body {{ font-size: var(--text-body); line-height: var(--text-body-lh); }}\n'
                f'h1 {{ font-size: var(--text-h1); }} h2 {{ font-size: var(--text-h2); }}\n'
                f'h3 {{ font-size: var(--text-h3); }} h4 {{ font-size: var(--text-h4); }}'), 0.92

    def _synth_dark_theme(self, lang, name, entity, facts):
        return (f'/* ═══ Thème Sombre + Toggle ═══ */\n'
                f'@media (prefers-color-scheme: dark) {{\n  :root {{\n'
                f'    --color-bg: hsl(262, 15%, 6%);\n    --color-bg-alt: hsl(262, 12%, 10%);\n'
                f'    --color-text: hsl(262, 10%, 92%);\n    --color-text-muted: hsl(262, 8%, 65%);\n'
                f'    --color-muted: hsl(262, 8%, 15%);\n    --color-border: hsl(262, 10%, 22%);\n'
                f'  }}\n}}\n'
                f'[data-theme="dark"] {{\n'
                f'  --color-bg: hsl(262, 15%, 6%);\n  --color-bg-alt: hsl(262, 12%, 10%);\n'
                f'  --color-text: hsl(262, 10%, 92%);\n  --color-text-muted: hsl(262, 8%, 65%);\n'
                f'  --color-muted: hsl(262, 8%, 15%);\n  --color-border: hsl(262, 10%, 22%);\n}}\n'
                f'<button class="theme-toggle" onclick="var b=document.body;var t=b.dataset.theme===\'dark\'?\'light\':\'dark\';b.dataset.theme=t;this.textContent=t===\'dark\'?\'☀️\':\'🌙\'">🌙</button>\n'
                f'<style>.theme-toggle{{position:fixed;bottom:20px;right:20px;width:48px;height:48px;border-radius:50%;border:2px solid var(--color-border);background:var(--color-bg-alt);font-size:1.3rem;cursor:pointer;z-index:999}}</style>'), 0.94

    def _synth_animation(self, lang, name, entity, facts):
        return (f'/* ═══ Animations Harmoniques (GPU) ═══ */\n'
                f'@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px) translateZ(0); }} to {{ opacity: 1; transform: translateY(0) translateZ(0); }} }}\n'
                f'@keyframes slideUp {{ from {{ opacity: 0; transform: translateY(30px) translateZ(0); }} to {{ opacity: 1; transform: translateY(0) translateZ(0); }} }}\n'
                f'@keyframes scaleIn {{ from {{ opacity: 0; transform: scale(0.9) translateZ(0); }} to {{ opacity: 1; transform: scale(1) translateZ(0); }} }}\n'
                f'@keyframes wavePulse {{ 0%, 100% {{ transform: scale(1) translateZ(0); }} 50% {{ transform: scale(1.05) translateZ(0); }} }}\n'
                f'.animate-fade-in, .animate-slide-up, .animate-scale-in, .animate-pulse {{\n'
                f'  will-change: transform, opacity; backface-visibility: hidden; transform: translateZ(0); }}\n'
                f'.animate-fade-in {{ animation: fadeIn 0.618s ease-out both; }}\n'
                f'.animate-slide-up {{ animation: slideUp 1s ease-out both; }}\n'
                f'.animate-scale-in {{ animation: scaleIn 0.618s ease-out both; }}\n'
                f'.animate-pulse {{ animation: wavePulse 2.618s ease-in-out infinite; }}\n'
                f'.delay-1 {{ animation-delay: 0.15s; }} .delay-2 {{ animation-delay: 0.3s; }}'), 0.95

    def _synth_responsive_grid(self, lang, name, entity, facts):
        return (f'/* ═══ Grille Responsive Harmonique ═══ */\n'
                f'.container {{ width: 100%; max-width: 1257px; margin-inline: auto; padding-inline: 20px; }}\n'
                f'.grid-2 {{ display: grid; grid-template-columns: 62% 38%; gap: 32px; }}\n'
                f'.grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}\n'
                f'.grid-auto {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }}\n'
                f'@media (max-width: 479px) {{ .grid-2, .grid-3 {{ grid-template-columns: 1fr; }} }}\n'
                f'@media (min-width: 480px) and (max-width: 776px) {{ .grid-3 {{ grid-template-columns: 1fr 1fr; }} }}'), 0.92

    def _synth_flexbox_layout(self, lang, name, entity, facts):
        return (f'/* ═══ Utilitaires Flexbox ═══ */\n'
                f'.flex {{ display: flex; }} .flex-col {{ display: flex; flex-direction: column; }}\n'
                f'.flex-wrap {{ flex-wrap: wrap; }}\n'
                f'.flex-center {{ display: flex; align-items: center; justify-content: center; }}\n'
                f'.flex-between {{ display: flex; align-items: center; justify-content: space-between; }}\n'
                f'.flex-1 {{ flex: 1; }} .flex-gap {{ gap: 20px; }} .flex-gap-sm {{ gap: 12px; }}'), 0.94

    def _synth_glassmorphism(self, lang, name, entity, facts):
        return (f'/* ═══ Glassmorphism ═══ */\n'
                f'.glass {{\n  background: rgba(255, 255, 255, 0.1);\n'
                f'  backdrop-filter: blur(12px);\n  -webkit-backdrop-filter: blur(12px);\n'
                f'  border: 1px solid rgba(255, 255, 255, 0.18);\n'
                f'  border-radius: 16px;\n  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);\n}}'), 0.88

    def _synth_css_reset(self, lang, name, entity, facts):
        return (f'/* ═══ Reset CSS Moderne ═══ */\n'
                f'*,*::before,*::after {{ box-sizing:border-box;margin:0;padding:0; }}\n'
                f'html {{ scroll-behavior:smooth;-webkit-text-size-adjust:100%; }}\n'
                f"body {{ font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;min-height:100vh; }}\n"
                f'img,picture,video,canvas,svg {{ display:block;max-width:100%; }}\n'
                f'input,button,textarea,select {{ font:inherit;color:inherit; }}\n'
                f'a {{ color:inherit;text-decoration:none; }}\n'
                f'ul,ol {{ list-style:none; }}\n'
                f':focus-visible {{ outline:2px solid var(--color-primary, #6366f1);outline-offset:2px; }}'), 0.94

    # ════════════════ HTML COMPONENTS ════════════════

    def _synth_navbar(self, lang, name, entity, facts):
        cls = name.replace(' ', '-').lower()
        return (f'<nav class="{cls}" role="navigation" aria-label="Navigation principale">\n'
                f'  <div class="container flex-between">\n'
                f'    <a href="/" class="{cls}__brand" style="font-weight:700;color:var(--color-primary)">Logo</a>\n'
                f'    <button class="{cls}__toggle" aria-expanded="false" aria-label="Menu" onclick="this.nextElementSibling.classList.toggle(\'open\')">☰</button>\n'
                f'    <ul class="{cls}__menu flex flex-gap" role="menubar">\n'
                f'      <li><a href="/" class="active">Accueil</a></li>\n'
                f'      <li><a href="/about">À propos</a></li>\n'
                f'      <li><a href="/services">Services</a></li>\n'
                f'      <li><a href="/contact">Contact</a></li>\n'
                f'    </ul>\n'
                f'  </div>\n'
                f'</nav>\n'
                f'<style>\n'
                f'.{cls} {{ background: var(--color-bg); border-bottom: 1px solid var(--color-border); padding: 16px 0; position: sticky; top: 0; z-index: 100; backdrop-filter: blur(8px); }}\n'
                f'.{cls}__menu a {{ padding: 8px 16px; border-radius: var(--radius-md); color: var(--color-text-muted); text-decoration: none; transition: all 0.2s; }}\n'
                f'.{cls}__menu a:hover, .{cls}__menu a.active {{ background: var(--color-primary); color: #fff; }}\n'
                f'.{cls}__toggle {{ display: none; background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--color-text); }}\n'
                f'@media (max-width: 480px) {{ .{cls}__toggle {{ display: block; }} .{cls}__menu {{ display: none; flex-direction: column; position: absolute; top: 100%; left: 0; right: 0; background: var(--color-bg); padding: 16px; }} .{cls}__menu.open {{ display: flex; }} }}\n'
                f'</style>'), 0.92

    def _synth_hero(self, lang, name, entity, facts):
        cls = name.replace(' ', '-').lower()
        return (f'<section class="{cls}" role="banner">\n'
                f'  <div class="container text-center">\n'
                f'    <h1 class="{cls}__title animate-fade-in">Votre <span class="gradient-text">solution</span> moderne</h1>\n'
                f'    <p class="{cls}__subtitle animate-fade-in delay-1">Simplifiez votre workflow avec notre plateforme intuitive.</p>\n'
                f'    <div class="{cls}__actions flex flex-center flex-gap animate-fade-in delay-2">\n'
                f'      <a href="#" class="btn btn-primary">Commencer</a>\n'
                f'      <a href="#" class="btn btn-outline">En savoir plus</a>\n'
                f'    </div>\n'
                f'  </div>\n'
                f'</section>\n'
                f'<style>\n'
                f'.{cls} {{ padding: 136px 0; background: var(--gradient-subtle); text-align: center; min-height: 60vh; display: flex; align-items: center; }}\n'
                f'.{cls}__title {{ font-size: var(--text-h1); font-weight: 800; margin-bottom: 20px; line-height: 1.15; }}\n'
                f'.{cls}__subtitle {{ font-size: var(--text-h4); color: var(--color-text-muted); max-width: 600px; margin: 0 auto 32px; }}\n'
                f'.gradient-text {{ background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}\n'
                f'.{cls}__actions {{ justify-content: center; }}\n'
                f'</style>'), 0.92

    def _synth_card(self, lang, name, entity, facts, variant: str = "default"):
        """Carte avec 5 variantes structurellement DIFFÉRENTES."""
        cls = name.replace(' ', '-').lower()

        if variant == "horizontal":
            return (f'<article class="{cls}" data-variant="horizontal">\n'
                    f'  <div class="{cls}__image"><img src="https://placehold.co/300x300?text=Img" alt="Illustration" loading="lazy"></div>\n'
                    f'  <div class="{cls}__body"><span class="{cls}__tag">Catégorie</span><h3 class="{cls}__title">Titre de la carte</h3>\n'
                    f'    <p class="{cls}__text">Description concise du contenu.</p><a href="#" class="btn btn-primary btn-sm">Découvrir</a></div>\n'
                    f'</article>\n'
                    f'<style>'
                    f'.{cls}[data-variant="horizontal"]{{display:flex;background:var(--color-bg);border:1px solid var(--color-border);border-radius:var(--radius-lg);overflow:hidden;transition:transform .2s,box-shadow .2s}}'
                    f'.{cls}[data-variant="horizontal"]:hover{{transform:translateY(-3px);box-shadow:var(--shadow-lg)}}'
                    f'.{cls}[data-variant="horizontal"] .{cls}__image{{flex:0 0 40%;min-width:120px}}'
                    f'.{cls}[data-variant="horizontal"] .{cls}__image img{{width:100%;height:100%;min-height:160px;object-fit:cover}}'
                    f'.{cls}[data-variant="horizontal"] .{cls}__body{{flex:1;padding:var(--space-medium)}}'
                    f'.{cls}__tag{{display:inline-block;background:var(--color-muted);color:var(--color-primary);padding:2px 10px;border-radius:var(--radius-full);font-size:var(--text-small);margin-bottom:6px}}'
                    f'.{cls}__title{{font-size:var(--text-h4);margin-bottom:6px}}'
                    f'.{cls}__text{{color:var(--color-text-muted);font-size:var(--text-small);margin-bottom:var(--space-small)}}'
                    f'</style>'), 0.92

        if variant == "overlay":
            return (f'<article class="{cls}" data-variant="overlay">\n'
                    f'  <img src="https://placehold.co/600x400?text=Image" alt="Illustration" loading="lazy">\n'
                    f'  <div class="{cls}__overlay"><span class="{cls}__tag">Catégorie</span><h3 class="{cls}__title">Titre de la carte</h3>\n'
                    f'    <p class="{cls}__text">Description du contenu.</p></div>\n'
                    f'</article>\n'
                    f'<style>'
                    f'.{cls}[data-variant="overlay"]{{position:relative;border-radius:var(--radius-lg);overflow:hidden;cursor:pointer;transition:transform .3s}}'
                    f'.{cls}[data-variant="overlay"]:hover{{transform:scale(1.02)}}'
                    f'.{cls}[data-variant="overlay"] img{{width:100%;height:280px;object-fit:cover;transition:filter .3s}}'
                    f'.{cls}[data-variant="overlay"]:hover img{{filter:brightness(0.7)}}'
                    f'.{cls}__overlay{{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:flex-end;padding:var(--space-large);background:linear-gradient(to top,rgba(0,0,0,.8),transparent);color:#fff}}'
                    f'.{cls}__tag{{align-self:flex-start;background:rgba(255,255,255,.2);backdrop-filter:blur(4px);padding:2px 10px;border-radius:var(--radius-full);font-size:var(--text-small);margin-bottom:6px}}'
                    f'</style>'), 0.92

        if variant == "minimal":
            return (f'<article class="{cls}" data-variant="minimal">\n'
                    f'  <div class="{cls}__icon">🚀</div><h3 class="{cls}__title">Titre</h3>\n'
                    f'  <p class="{cls}__text">Description concise.</p>\n'
                    f'  <a href="#" class="{cls}__link">En savoir plus →</a>\n'
                    f'</article>\n'
                    f'<style>'
                    f'.{cls}[data-variant="minimal"]{{text-align:center;padding:var(--space-xl) var(--space-large);background:var(--color-bg-alt);border-radius:var(--radius-lg);transition:background .2s}}'
                    f'.{cls}[data-variant="minimal"]:hover{{background:var(--color-muted)}}'
                    f'.{cls}__icon{{font-size:3rem;margin-bottom:var(--space-medium)}}'
                    f'.{cls}__title{{font-size:var(--text-h4);margin-bottom:8px}}'
                    f'.{cls}__text{{color:var(--color-text-muted);font-size:var(--text-small);margin-bottom:var(--space-medium)}}'
                    f'.{cls}__link{{color:var(--color-primary);font-weight:600;font-size:var(--text-small);text-decoration:none}}'
                    f'</style>'), 0.92

        if variant == "featured":
            return (f'<article class="{cls}" data-variant="featured">\n'
                    f'  <div class="{cls}__badge">★ Populaire</div>\n'
                    f'  <div class="{cls}__image"><img src="https://placehold.co/600x400?text=Featured" alt="Illustration" loading="lazy"></div>\n'
                    f'  <div class="{cls}__body"><h3 class="{cls}__title">Titre en vedette</h3>\n'
                    f'    <p class="{cls}__text">Une carte mise en avant avec un style premium.</p>\n'
                    f'    <div class="{cls}__meta"><span>⭐ 4.9</span><span>·</span><span>1,234 téléchargements</span></div>\n'
                    f'    <a href="#" class="btn btn-primary">Obtenir maintenant</a></div>\n'
                    f'</article>\n'
                    f'<style>'
                    f'.{cls}[data-variant="featured"]{{position:relative;background:var(--color-bg);border:2px solid var(--color-accent);border-radius:var(--radius-lg);overflow:hidden;box-shadow:0 0 30px hsla(22,85%,55%,.15);transform:scale(1.02);transition:transform .2s,box-shadow .2s}}'
                    f'.{cls}[data-variant="featured"]:hover{{transform:scale(1.04);box-shadow:0 0 40px hsla(22,85%,55%,.3)}}'
                    f'.{cls}__badge{{position:absolute;top:12px;right:12px;background:var(--color-accent);color:#fff;padding:4px 12px;border-radius:var(--radius-full);font-size:var(--text-small);font-weight:700;z-index:2}}'
                    f'.{cls}[data-variant="featured"] img{{width:100%;height:220px;object-fit:cover}}'
                    f'.{cls}[data-variant="featured"] .{cls}__body{{padding:var(--space-large)}}'
                    f'.{cls}__title{{font-size:var(--text-h3);margin-bottom:8px}}'
                    f'.{cls}__meta{{display:flex;gap:6px;font-size:var(--text-small);color:var(--color-text-muted);margin-bottom:var(--space-medium)}}'
                    f'</style>'), 0.92

        # default — image en haut, texte en bas
        return (f'<article class="{cls}" data-variant="default">\n'
                f'  <div class="{cls}__image"><img src="https://placehold.co/600x400/e2e8f0/64748b?text=Image" alt="Illustration" loading="lazy"></div>\n'
                f'  <div class="{cls}__body"><span class="{cls}__tag">Catégorie</span><h3 class="{cls}__title">Titre de la carte</h3>\n'
                f'    <p class="{cls}__text">Description concise qui résume le contenu.</p><a href="#" class="btn btn-primary">Découvrir</a></div>\n'
                f'</article>\n'
                f'<style>'
                f'.{cls}[data-variant="default"]{{background:var(--color-bg);border:1px solid var(--color-border);border-radius:var(--radius-lg);overflow:hidden;transition:transform .2s,box-shadow .2s}}'
                f'.{cls}[data-variant="default"]:hover{{transform:translateY(-4px);box-shadow:var(--shadow-lg)}}'
                f'.{cls}[data-variant="default"] img{{width:100%;height:200px;object-fit:cover}}'
                f'.{cls}[data-variant="default"] .{cls}__body{{padding:var(--space-large)}}'
                f'.{cls}__tag{{display:inline-block;background:var(--color-muted);color:var(--color-primary);padding:4px 12px;border-radius:var(--radius-full);font-size:var(--text-small);font-weight:500;margin-bottom:var(--space-small)}}'
                f'.{cls}__title{{font-size:var(--text-h4);margin-bottom:var(--space-tiny)}}'
                f'.{cls}__text{{color:var(--color-text-muted);margin-bottom:var(--space-medium);line-height:1.618}}'
                f'</style>'), 0.92

    def _synth_button(self, lang, name, entity, facts):
        return (f'<!-- Boutons -->\n'
                f'<button class="btn btn-primary">Primaire</button>\n'
                f'<button class="btn btn-secondary">Secondaire</button>\n'
                f'<button class="btn btn-outline">Outline</button>\n'
                f'<button class="btn btn-ghost">Ghost</button>\n'
                f'<style>\n'
                f'.btn {{ display:inline-flex; align-items:center; justify-content:center; gap:8px; padding:12px 24px;\n'
                f'  border-radius:var(--radius-md); font-weight:600; cursor:pointer; border:2px solid transparent;\n'
                f'  transition:all var(--transition-fast, 0.2s); text-decoration:none; font:inherit; color:inherit; }}\n'
                f'.btn-primary {{ background:var(--color-primary); color:#fff; }} .btn-primary:hover {{ background:var(--color-primary-hover); transform:translateY(-1px); box-shadow:var(--shadow-md); }}\n'
                f'.btn-secondary {{ background:var(--color-secondary); color:#fff; }}\n'
                f'.btn-outline {{ background:transparent; border-color:var(--color-primary); color:var(--color-primary); }} .btn-outline:hover {{ background:var(--color-primary); color:#fff; }}\n'
                f'.btn-ghost {{ background:transparent; border-color:transparent; color:var(--color-text); }} .btn-ghost:hover {{ background:var(--color-muted); }}\n'
                f'.btn:disabled {{ opacity:0.5; cursor:not-allowed; pointer-events:none; }}\n'
                f'.btn-sm {{ padding:8px 16px; font-size:var(--text-small); }}\n'
                f'</style>'), 0.93

    def _synth_form(self, lang, name, entity, facts):
        cls = name.replace(' ', '-').lower()
        return (f'<form class="{cls}" aria-label="Formulaire">\n'
                f'  <div class="{cls}__group"><label for="{cls}-name">Nom</label>\n'
                f'    <input type="text" id="{cls}-name" placeholder="Votre nom" required></div>\n'
                f'  <div class="{cls}__group"><label for="{cls}-email">Email</label>\n'
                f'    <input type="email" id="{cls}-email" placeholder="votre@email.com" required></div>\n'
                f'  <div class="{cls}__group"><label for="{cls}-msg">Message</label>\n'
                f'    <textarea id="{cls}-msg" rows="4" placeholder="Votre message..."></textarea></div>\n'
                f'  <button type="submit" class="btn btn-primary">Envoyer</button>\n'
                f'</form>\n'
                f'<style>\n'
                f'.{cls} {{ display:flex; flex-direction:column; gap:20px; max-width:500px; }}\n'
                f'.{cls}__group {{ display:flex; flex-direction:column; gap:6px; }}\n'
                f'.{cls}__group label {{ font-weight:500; font-size:var(--text-small); }}\n'
                f'.{cls}__group input, .{cls}__group textarea, .{cls}__group select {{ padding:12px 16px;\n'
                f'  border:1px solid var(--color-border); border-radius:var(--radius-md); background:var(--color-bg); transition:border-color .2s,box-shadow .2s; color:var(--color-text); }}\n'
                f'.{cls}__group input:focus, .{cls}__group textarea:focus {{ outline:none; border-color:var(--color-primary); box-shadow:0 0 0 3px hsla(262,60%,55%,.15); }}\n'
                f'</style>'), 0.92

    def _synth_modal(self, lang, name, entity, facts):
        cls = name.replace(' ', '-').lower()
        return (f'<button class="btn btn-primary" onclick="KA.openModal(\'{cls}-modal\')">Ouvrir la modale</button>\n'
                f'<div class="modal-overlay" id="{cls}-modal" role="dialog" aria-modal="true" aria-labelledby="{cls}-title" hidden>\n'
                f'  <div class="modal" role="document">\n'
                f'    <div class="modal__header"><h2 id="{cls}-title" tabindex="-1">Titre de la modale</h2>\n'
                f'      <button class="modal__close" aria-label="Fermer" onclick="KA.closeModal(\'{cls}-modal\')">&times;</button></div>\n'
                f'    <div class="modal__body"><p>Contenu de la modale ici.</p></div>\n'
                f'    <div class="modal__footer"><button class="btn btn-ghost" onclick="KA.closeModal(\'{cls}-modal\')">Annuler</button>\n'
                f'      <button class="btn btn-primary" onclick="KA.closeModal(\'{cls}-modal\')">Confirmer</button></div>\n'
                f'  </div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.modal-overlay {{ position:fixed; inset:0; background:rgba(0,0,0,.5); backdrop-filter:blur(4px); display:flex; align-items:center; justify-content:center; z-index:1000; opacity:0; visibility:hidden; transition:opacity .3s,visibility .3s; }}\n'
                f'.modal-overlay[open] {{ opacity:1; visibility:visible; }}\n'
                f'.modal {{ background:var(--color-bg); border-radius:var(--radius-lg); padding:var(--space-large); max-width:500px; width:90%; box-shadow:var(--shadow-xl); transform:translateY(20px); transition:transform .3s; }}\n'
                f'.modal-overlay[open] .modal {{ transform:translateY(0); }}\n'
                f'.modal__header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }}\n'
                f'.modal__close {{ background:none; border:none; font-size:1.5rem; cursor:pointer; color:var(--color-text-muted); }}\n'
                f'.modal__footer {{ display:flex; justify-content:flex-end; gap:12px; margin-top:32px; }}\n'
                f'</style>\n'
                f'<script>\n'
                f'(function(){{window.KA=window.KA||{{}};var prev=null;KA.openModal=function(id){{var o=document.getElementById(id);if(!o)return;prev=document.activeElement;o.hidden=false;o.setAttribute("open","");var f=o.querySelectorAll("button,[href],input");if(f.length)f[0].focus();o.addEventListener("keydown",function(e){{if(e.key==="Escape")KA.closeModal(id);if(e.key==="Tab"){{var fs=o.querySelectorAll("button,[href],input");var first=fs[0],last=fs[fs.length-1];if(e.shiftKey&&document.activeElement===first){{e.preventDefault();last.focus()}}else if(!e.shiftKey&&document.activeElement===last){{e.preventDefault();first.focus()}}}})}};KA.closeModal=function(id){{var o=document.getElementById(id);if(!o)return;o.removeAttribute("open");setTimeout(function(){{o.hidden=true}},300);if(prev)prev.focus()}}}})();\n'
                f'</script>'), 0.92

    def _synth_footer(self, lang, name, entity, facts):
        cls = name.replace(' ', '-').lower()
        return (f'<footer class="{cls}" role="contentinfo">\n'
                f'  <div class="container">\n'
                f'    <div class="{cls}__grid grid-auto">\n'
                f'      <div class="{cls}__col"><h3 class="{cls}__brand">Logo</h3>\n'
                f'        <p class="{cls}__desc">Une brève description de votre entreprise ou projet.</p></div>\n'
                f'      <div class="{cls}__col"><h4>Liens</h4><ul>\n'
                f'        <li><a href="/">Accueil</a></li><li><a href="/about">À propos</a></li>\n'
                f'        <li><a href="/blog">Blog</a></li><li><a href="/contact">Contact</a></li></ul></div>\n'
                f'      <div class="{cls}__col"><h4>Légal</h4><ul>\n'
                f'        <li><a href="/privacy">Confidentialité</a></li><li><a href="/terms">Conditions</a></li></ul></div>\n'
                f'    </div>\n'
                f'    <div class="{cls}__bottom"><p>&copy; {time.strftime("%Y")} — Tous droits réservés.</p></div>\n'
                f'  </div>\n'
                f'</footer>\n'
                f'<style>\n'
                f'.{cls} {{ background:var(--color-bg-alt); padding:84px 0 32px; border-top:1px solid var(--color-border); margin-top:auto; }}\n'
                f'.{cls}__grid {{ margin-bottom:52px; }}\n'
                f'.{cls}__brand {{ font-size:var(--text-h4); color:var(--color-primary); margin-bottom:8px; }}\n'
                f'.{cls}__desc {{ color:var(--color-text-muted); max-width:300px; line-height:1.618; }}\n'
                f'.{cls}__col h4 {{ margin-bottom:12px; }}\n'
                f'.{cls}__col li {{ margin-bottom:8px; }}\n'
                f'.{cls}__col a {{ color:var(--color-text-muted); transition:color .2s; text-decoration:none; }} .{cls}__col a:hover {{ color:var(--color-primary); }}\n'
                f'.{cls}__bottom {{ border-top:1px solid var(--color-border); padding-top:20px; text-align:center; color:var(--color-text-muted); font-size:var(--text-small); }}\n'
                f'</style>'), 0.92

    def _synth_dashboard(self, lang, name, entity, facts):
        return (f'<div class="dashboard">\n'
                f'  <aside class="dashboard__sidebar">\n'
                f'    <div class="dashboard__logo">Logo</div>\n'
                f'    <nav class="dashboard__nav">\n'
                f'      <a href="#" class="dashboard__nav-item active">Tableau de bord</a>\n'
                f'      <a href="#" class="dashboard__nav-item">Utilisateurs</a>\n'
                f'      <a href="#" class="dashboard__nav-item">Analytiques</a>\n'
                f'      <a href="#" class="dashboard__nav-item">Paramètres</a>\n'
                f'    </nav>\n'
                f'  </aside>\n'
                f'  <main class="dashboard__main">\n'
                f'    <header class="dashboard__header flex-between"><h1>Tableau de bord</h1><div>👤 Admin</div></header>\n'
                f'    <div class="dashboard__content grid-3">\n'
                f'      <div class="stat-card"><span class="stat-card__label">Total</span><span class="stat-card__value">1,234</span></div>\n'
                f'      <div class="stat-card"><span class="stat-card__label">Actifs</span><span class="stat-card__value">892</span></div>\n'
                f'      <div class="stat-card"><span class="stat-card__label">Revenu</span><span class="stat-card__value">12,450€</span></div>\n'
                f'    </div>\n'
                f'  </main>\n'
                f'</div>\n'
                f'<style>\n'
                f'.dashboard {{ display:grid; grid-template-columns:250px 1fr; min-height:100vh; }}\n'
                f'.dashboard__sidebar {{ background:var(--color-bg-alt); border-right:1px solid var(--color-border); padding:20px; }}\n'
                f'.dashboard__logo {{ font-size:var(--text-h4); font-weight:700; color:var(--color-primary); margin-bottom:32px; }}\n'
                f'.dashboard__nav-item {{ display:block; padding:10px 16px; border-radius:var(--radius-md); margin-bottom:4px; transition:all .2s; text-decoration:none; color:var(--color-text-muted); }}\n'
                f'.dashboard__nav-item:hover, .dashboard__nav-item.active {{ background:var(--color-primary); color:#fff; }}\n'
                f'.dashboard__main {{ padding:32px; }}\n'
                f'.dashboard__header {{ margin-bottom:32px; }}\n'
                f'.stat-card {{ background:var(--color-bg); border:1px solid var(--color-border); border-radius:var(--radius-lg); padding:32px; text-align:center; }}\n'
                f'.stat-card__label {{ display:block; font-size:var(--text-small); color:var(--color-text-muted); margin-bottom:4px; }}\n'
                f'.stat-card__value {{ font-size:var(--text-h2); font-weight:700; color:var(--color-primary); }}\n'
                f'@media (max-width: 480px) {{ .dashboard {{ grid-template-columns:1fr; }} .dashboard__sidebar {{ display:none; }} }}\n'
                f'</style>'), 0.90

    def _synth_landing_page(self, lang, name, entity, facts):
        title = name.replace('-', ' ').title()
        return (f'<!DOCTYPE html>\n'
                f'<html lang="fr">\n<head>\n<meta charset="UTF-8">\n'
                f'<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                f'<title>{title} — Landing Page</title>\n'
                f'<style>\n'
                f':root {{ --color-primary:hsl(262,60%,55%); --color-accent:hsl(22,85%,55%);\n'
                f'  --color-bg:hsl(262,20%,97%); --color-text:hsl(262,15%,12%); --color-text-muted:hsl(262,10%,45%);\n'
                f'  --color-border:hsl(262,12%,82%); --gradient-primary:linear-gradient(135deg,var(--color-primary),var(--color-accent));\n'
                f'  --radius-md:8px; --radius-lg:16px; --space-medium:20px; --space-large:32px; --space-xl:52px; }}\n'
                f'*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}\n'
                f'body{{font-family:system-ui,sans-serif;background:var(--color-bg);color:var(--color-text);line-height:1.6}}\n'
                f'.container{{width:100%;max-width:1200px;margin:0 auto;padding:0 20px}}\n'
                f'.flex{{display:flex}}.flex-between{{display:flex;align-items:center;justify-content:space-between}}\n'
                f'.flex-center{{display:flex;align-items:center;justify-content:center}}\n'
                f'.flex-gap{{gap:20px}}.text-center{{text-align:center}}\n'
                f'.grid-3{{display:grid;grid-template-columns:repeat(3,1fr);gap:32px}}\n'
                f'.btn{{display:inline-flex;align-items:center;justify-content:center;padding:12px 24px;border-radius:var(--radius-md);font-weight:600;cursor:pointer;border:2px solid transparent;text-decoration:none;transition:all .2s}}\n'
                f'.btn-primary{{background:var(--color-primary);color:#fff}}.btn-primary:hover{{transform:translateY(-1px)}}\n'
                f'.btn-outline{{background:transparent;border-color:var(--color-primary);color:var(--color-primary)}}\n'
                f'.gradient-text{{background:var(--gradient-primary);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}\n'
                f'@media (max-width:768px){{.grid-3{{grid-template-columns:1fr}}}}\n'
                f'</style>\n</head>\n<body>\n'
                f'<nav class="navbar" style="padding:16px 0;border-bottom:1px solid var(--color-border);position:sticky;top:0;background:var(--color-bg);z-index:100">\n'
                f'  <div class="container flex-between">\n'
                f'    <a href="/" style="font-size:1.618rem;font-weight:700;color:var(--color-primary);text-decoration:none">{title}</a>\n'
                f'    <ul class="flex flex-gap" style="list-style:none">\n'
                f'      <li><a href="#features" style="color:var(--color-text-muted);text-decoration:none">Fonctionnalités</a></li>\n'
                f'      <li><a href="#pricing" style="color:var(--color-text-muted);text-decoration:none">Tarifs</a></li>\n'
                f'      <li><a href="#cta" class="btn btn-primary">Essai gratuit</a></li>\n'
                f'    </ul>\n'
                f'  </div>\n'
                f'</nav>\n'
                f'<section class="hero" style="padding:80px 0;text-align:center">\n'
                f'  <div class="container">\n'
                f'    <h1 style="font-size:2.618rem;font-weight:800;margin-bottom:20px">Votre <span class="gradient-text">solution</span> SaaS moderne</h1>\n'
                f'    <p style="font-size:1.272rem;color:var(--color-text-muted);max-width:600px;margin:0 auto 32px">Simplifiez votre workflow avec notre plateforme intuitive. Démarrez en 5 minutes.</p>\n'
                f'    <div class="flex flex-center flex-gap">\n'
                f'      <a href="#" class="btn btn-primary" style="font-size:1.272rem;padding:16px 32px">Démarrer gratuitement</a>\n'
                f'      <a href="#" class="btn btn-outline">Voir la démo</a>\n'
                f'    </div>\n'
                f'  </div>\n'
                f'</section>\n'
                f'<section id="features" style="padding:80px 0;background:hsl(262,15%,93%)">\n'
                f'  <div class="container"><h2 class="text-center" style="margin-bottom:52px">Fonctionnalités</h2>\n'
                f'    <div class="grid-3">\n'
                f'      <div style="text-align:center"><div style="font-size:2.5rem;margin-bottom:20px">⚡</div><h3 style="margin-bottom:8px">Ultra Rapide</h3><p style="color:var(--color-text-muted)">Temps de réponse inférieur à 20ms.</p></div>\n'
                f'      <div style="text-align:center"><div style="font-size:2.5rem;margin-bottom:20px">🔒</div><h3 style="margin-bottom:8px">100% Sécurisé</h3><p style="color:var(--color-text-muted)">Chiffrement de bout en bout.</p></div>\n'
                f'      <div style="text-align:center"><div style="font-size:2.5rem;margin-bottom:20px">🎨</div><h3 style="margin-bottom:8px">Design Adaptatif</h3><p style="color:var(--color-text-muted)">Interface responsive.</p></div>\n'
                f'    </div>\n'
                f'  </div>\n'
                f'</section>\n'
                f'<section id="pricing" style="padding:80px 0">\n'
                f'  <div class="container"><h2 class="text-center" style="margin-bottom:52px">Nos Tarifs</h2>\n'
                f'    <div class="grid-3">\n'
                f'      <div style="border:1px solid var(--color-border);border-radius:var(--radius-lg);padding:32px;text-align:center"><h3>Starter</h3><div style="font-size:2.618rem;font-weight:800;margin:20px 0">19<span style="font-size:1rem;color:var(--color-text-muted)">€/mois</span></div><a href="#" class="btn btn-outline" style="width:100%">Commencer</a></div>\n'
                f'      <div style="border:2px solid var(--color-primary);border-radius:var(--radius-lg);padding:32px;text-align:center;transform:scale(1.05)"><span style="background:var(--color-primary);color:#fff;padding:4px 16px;border-radius:9999px;font-size:.8rem;font-weight:600">Populaire</span><h3 style="margin-top:8px">Pro</h3><div style="font-size:2.618rem;font-weight:800;margin:20px 0">49<span style="font-size:1rem;color:var(--color-text-muted)">€/mois</span></div><a href="#" class="btn btn-primary" style="width:100%">Commencer</a></div>\n'
                f'      <div style="border:1px solid var(--color-border);border-radius:var(--radius-lg);padding:32px;text-align:center"><h3>Enterprise</h3><div style="font-size:2.618rem;font-weight:800;margin:20px 0">99<span style="font-size:1rem;color:var(--color-text-muted)">€/mois</span></div><a href="#" class="btn btn-outline" style="width:100%">Contactez-nous</a></div>\n'
                f'    </div>\n'
                f'  </div>\n'
                f'</section>\n'
                f'<section id="cta" class="text-center" style="padding:80px 0;background:hsl(262,15%,93%)">\n'
                f'  <div class="container"><h2 style="margin-bottom:20px">Prêt à commencer ?</h2>\n'
                f'    <p style="color:var(--color-text-muted);margin-bottom:32px">Rejoignez des milliers d\'utilisateurs satisfaits.</p>\n'
                f'    <a href="#" class="btn btn-primary" style="font-size:1.272rem;padding:16px 32px">Démarrer gratuitement</a>\n'
                f'  </div>\n'
                f'</section>\n'
                f'<footer style="padding:52px 0;border-top:1px solid var(--color-border)">\n'
                f'  <div class="container text-center"><p style="color:var(--color-text-muted)">&copy; {time.strftime("%Y")} {title}. Tous droits réservés.</p></div>\n'
                f'</footer>\n</body>\n</html>'), 0.93

    def _synth_pricing(self, lang, name, entity, facts):
        return (f'<section class="pricing">\n'
                f'  <div class="container"><h2 class="text-center">Nos Tarifs</h2>\n'
                f'    <div class="grid-3" style="margin-top:52px">\n'
                f'      <div class="pricing-card"><h3>Starter</h3><div class="pricing-card__price">19<span>€/mois</span></div>\n'
                f'        <ul><li>✓ Jusqu\'à 5 projets</li><li>✓ Support email</li><li>✓ 10 Go stockage</li></ul>\n'
                f'        <a href="#" class="btn btn-outline">Commencer</a></div>\n'
                f'      <div class="pricing-card pricing-card--featured"><span class="pricing-card__badge">Populaire</span><h3>Pro</h3>\n'
                f'        <div class="pricing-card__price">49<span>€/mois</span></div>\n'
                f'        <ul><li>✓ Projets illimités</li><li>✓ Support prioritaire</li><li>✓ 100 Go stockage</li><li>✓ Analytics</li></ul>\n'
                f'        <a href="#" class="btn btn-primary">Commencer</a></div>\n'
                f'      <div class="pricing-card"><h3>Enterprise</h3><div class="pricing-card__price">99<span>€/mois</span></div>\n'
                f'        <ul><li>✓ Tout de Pro</li><li>✓ Support 24/7</li><li>✓ Stockage illimité</li></ul>\n'
                f'        <a href="#" class="btn btn-outline">Contactez-nous</a></div>\n'
                f'    </div>\n'
                f'  </div>\n'
                f'</section>\n'
                f'<style>\n'
                f'.pricing-card {{ background:var(--color-bg); border:1px solid var(--color-border); border-radius:var(--radius-lg); padding:32px; text-align:center; transition:transform .2s; }}\n'
                f'.pricing-card:hover {{ transform:translateY(-4px); }}\n'
                f'.pricing-card--featured {{ border-color:var(--color-primary); box-shadow:var(--shadow-lg); position:relative; transform:scale(1.05); }}\n'
                f'.pricing-card__badge {{ position:absolute; top:-12px; left:50%; transform:translateX(-50%); background:var(--color-primary); color:#fff; padding:4px 16px; border-radius:9999px; font-size:var(--text-small); font-weight:600; }}\n'
                f'.pricing-card__price {{ font-size:var(--text-h1); font-weight:800; margin:20px 0; }}\n'
                f'.pricing-card__price span {{ font-size:var(--text-body); font-weight:400; color:var(--color-text-muted); }}\n'
                f'.pricing-card ul {{ list-style:none; margin:20px 0; text-align:left; }}\n'
                f'.pricing-card li {{ padding:8px 0; color:var(--color-text-muted); }}\n'
                f'</style>'), 0.92

    def _synth_testimonial(self, lang, name, entity, facts):
        return (f'<blockquote class="testimonial">\n'
                f'  <div class="testimonial__stars">★★★★★</div>\n'
                f'  <p class="testimonial__quote">"Ce produit a complètement transformé notre façon de travailler. Hautement recommandé !"</p>\n'
                f'  <div class="testimonial__author flex flex-gap-sm">\n'
                f'    <div class="testimonial__avatar">👤</div>\n'
                f'    <div><strong>Jean Dupont</strong><span class="testimonial__role">CEO, TechCorp</span></div>\n'
                f'  </div>\n'
                f'</blockquote>\n'
                f'<style>\n'
                f'.testimonial {{ background:var(--color-bg); border:1px solid var(--color-border); border-radius:var(--radius-lg); padding:32px; max-width:500px; }}\n'
                f'.testimonial__stars {{ color:var(--color-warning); font-size:var(--text-h4); margin-bottom:12px; }}\n'
                f'.testimonial__quote {{ font-style:italic; line-height:1.618; margin-bottom:20px; }}\n'
                f'.testimonial__avatar {{ width:48px; height:48px; border-radius:50%; background:var(--color-muted); display:flex; align-items:center; justify-content:center; font-size:1.5rem; }}\n'
                f'.testimonial__role {{ display:block; font-size:var(--text-small); color:var(--color-text-muted); }}\n'
                f'</style>'), 0.90

    def _synth_faq(self, lang, name, entity, facts):
        return (f'<section class="faq"><div class="container" style="max-width:777px">\n'
                f'  <h2 class="text-center">Questions Fréquentes</h2>\n'
                f'  <dl class="faq__list">\n'
                f'    <div class="faq__item"><dt><button class="faq__question" aria-expanded="false" onclick="this.setAttribute(\'aria-expanded\',this.getAttribute(\'aria-expanded\')===\'true\'?\'false\':\'true\');this.nextElementSibling.hidden=!this.nextElementSibling.hidden">Comment ça marche ?</button></dt>\n'
                f'      <dd class="faq__answer" hidden>Notre plateforme utilise une technologie innovante pour simplifier votre expérience.</dd></div>\n'
                f'    <div class="faq__item"><dt><button class="faq__question" aria-expanded="false" onclick="this.setAttribute(\'aria-expanded\',this.getAttribute(\'aria-expanded\')===\'true\'?\'false\':\'true\');this.nextElementSibling.hidden=!this.nextElementSibling.hidden">Est-ce gratuit ?</button></dt>\n'
                f'      <dd class="faq__answer" hidden>Oui, nous proposons un plan gratuit avec des fonctionnalités de base.</dd></div>\n'
                f'  </dl>\n'
                f'</div></section>\n'
                f'<style>\n'
                f'.faq__item {{ border-bottom:1px solid var(--color-border); }}\n'
                f'.faq__question {{ width:100%; text-align:left; background:none; border:none; padding:20px 0; font-size:var(--text-body); font-weight:600; cursor:pointer; display:flex; justify-content:space-between; align-items:center; color:var(--color-text); }}\n'
                f'.faq__question::after {{ content:"+"; font-size:1.5rem; transition:transform .3s; }}\n'
                f'.faq__question[aria-expanded="true"]::after {{ transform:rotate(45deg); }}\n'
                f'.faq__answer {{ padding-bottom:20px; color:var(--color-text-muted); line-height:1.618; }}\n'
                f'</style>'), 0.90

    def _synth_contact_form(self, lang, name, entity, facts):
        return (f'<section class="contact"><div class="container" style="max-width:600px">\n'
                f'  <h2 class="text-center">Contactez-nous</h2>\n'
                f'  <form class="contact__form">\n'
                f'    <div class="form-group"><label for="c-name">Nom</label><input type="text" id="c-name" required placeholder="Votre nom complet"></div>\n'
                f'    <div class="form-group"><label for="c-email">Email</label><input type="email" id="c-email" required placeholder="votre@email.com"></div>\n'
                f'    <div class="form-group"><label for="c-msg">Message</label><textarea id="c-msg" rows="6" required placeholder="Votre message..."></textarea></div>\n'
                f'    <button type="submit" class="btn btn-primary" style="width:100%">Envoyer le message</button>\n'
                f'  </form>\n'
                f'</div></section>\n'
                f'<style>\n'
                f'.contact__form {{ display:flex; flex-direction:column; gap:20px; margin-top:32px; }}\n'
                f'.form-group {{ display:flex; flex-direction:column; gap:6px; }}\n'
                f'.form-group label {{ font-weight:500; font-size:var(--text-small); }}\n'
                f'.form-group input, .form-group textarea {{ padding:12px 16px; border:1px solid var(--color-border); border-radius:var(--radius-md); background:var(--color-bg); color:var(--color-text); transition:border-color .2s; }}\n'
                f'.form-group input:focus, .form-group textarea:focus {{ outline:none; border-color:var(--color-primary); }}\n'
                f'</style>'), 0.92

    def _synth_gallery(self, lang, name, entity, facts):
        return (f'<section class="gallery"><div class="container">\n'
                f'  <h2 class="text-center">Galerie</h2>\n'
                f'  <div class="gallery__grid grid-auto" style="margin-top:52px">\n'
                f'    <figure class="gallery__item"><img src="https://placehold.co/600x400?text=Image+1" alt="Image 1" loading="lazy"><figcaption>Description 1</figcaption></figure>\n'
                f'    <figure class="gallery__item"><img src="https://placehold.co/600x400?text=Image+2" alt="Image 2" loading="lazy"><figcaption>Description 2</figcaption></figure>\n'
                f'    <figure class="gallery__item"><img src="https://placehold.co/600x400?text=Image+3" alt="Image 3" loading="lazy"><figcaption>Description 3</figcaption></figure>\n'
                f'    <figure class="gallery__item"><img src="https://placehold.co/600x400?text=Image+4" alt="Image 4" loading="lazy"><figcaption>Description 4</figcaption></figure>\n'
                f'  </div>\n'
                f'</div></section>\n'
                f'<style>\n'
                f'.gallery__item {{ border-radius:var(--radius-md); overflow:hidden; transition:transform .3s; }}\n'
                f'.gallery__item:hover {{ transform:scale(1.02); }}\n'
                f'.gallery__item img {{ width:100%; aspect-ratio:3/2; object-fit:cover; }}\n'
                f'.gallery__item figcaption {{ padding:12px; font-size:var(--text-small); color:var(--color-text-muted); text-align:center; }}\n'
                f'</style>'), 0.90

    def _synth_sidebar(self, lang, name, entity, facts):
        return (f'<aside class="sidebar" role="navigation" aria-label="Menu latéral">\n'
                f'  <nav class="sidebar__nav">\n'
                f'    <a href="#" class="sidebar__item active"><span class="sidebar__icon">📊</span><span>Dashboard</span></a>\n'
                f'    <a href="#" class="sidebar__item"><span class="sidebar__icon">📁</span><span>Projets</span></a>\n'
                f'    <a href="#" class="sidebar__item"><span class="sidebar__icon">📅</span><span>Calendrier</span></a>\n'
                f'    <a href="#" class="sidebar__item"><span class="sidebar__icon">⚙️</span><span>Paramètres</span></a>\n'
                f'  </nav>\n'
                f'</aside>\n'
                f'<style>\n'
                f'.sidebar {{ width:240px; min-height:100vh; background:var(--color-bg-alt); border-right:1px solid var(--color-border); padding:20px; }}\n'
                f'.sidebar__item {{ display:flex; align-items:center; gap:12px; padding:12px 16px; border-radius:var(--radius-md); margin-bottom:4px; transition:all .2s; text-decoration:none; color:var(--color-text-muted); }}\n'
                f'.sidebar__item:hover, .sidebar__item.active {{ background:var(--color-primary); color:#fff; }}\n'
                f'.sidebar__icon {{ font-size:1.2rem; width:24px; text-align:center; }}\n'
                f'</style>'), 0.92

    def _synth_table(self, lang, name, entity, facts):
        return (f'<div class="table-wrapper">\n'
                f'  <table class="table">\n'
                f'    <thead><tr><th>Nom</th><th>Email</th><th>Rôle</th><th>Statut</th></tr></thead>\n'
                f'    <tbody>\n'
                f'      <tr><td>Jean Dupont</td><td>jean@exemple.fr</td><td>Admin</td><td><span class="badge badge--success">Actif</span></td></tr>\n'
                f'      <tr><td>Marie Martin</td><td>marie@exemple.fr</td><td>Éditeur</td><td><span class="badge badge--success">Actif</span></td></tr>\n'
                f'      <tr><td>Paul Petit</td><td>paul@exemple.fr</td><td>Lecteur</td><td><span class="badge badge--warning">En attente</span></td></tr>\n'
                f'    </tbody>\n'
                f'  </table>\n'
                f'</div>\n'
                f'<style>\n'
                f'.table-wrapper {{ overflow-x:auto; border:1px solid var(--color-border); border-radius:var(--radius-lg); }}\n'
                f'.table {{ width:100%; border-collapse:collapse; }}\n'
                f'.table th {{ background:var(--color-bg-alt); padding:12px 16px; text-align:left; font-weight:600; font-size:var(--text-small); color:var(--color-text-muted); text-transform:uppercase; letter-spacing:.05em; }}\n'
                f'.table td {{ padding:12px 16px; border-top:1px solid var(--color-border); }}\n'
                f'.table tbody tr:hover {{ background:var(--color-bg-alt); }}\n'
                f'.badge {{ display:inline-block; padding:4px 10px; border-radius:9999px; font-size:.75rem; font-weight:500; }}\n'
                f'.badge--success {{ background:hsla(145,50%,45%,.15); color:var(--color-success); }}\n'
                f'.badge--warning {{ background:hsla(38,92%,50%,.15); color:var(--color-warning); }}\n'
                f'</style>'), 0.92

    def _synth_portfolio(self, lang, name, entity, facts):
        return (f'<section class="portfolio"><div class="container">\n'
                f'  <h2 class="text-center">Mes Projets</h2>\n'
                f'  <div class="portfolio__filters flex flex-center flex-gap" style="margin:32px 0">\n'
                f'    <button class="btn btn-ghost active">Tous</button><button class="btn btn-ghost">Web</button>\n'
                f'    <button class="btn btn-ghost">Mobile</button><button class="btn btn-ghost">Design</button>\n'
                f'  </div>\n'
                f'  <div class="grid-auto">\n'
                f'    <article class="portfolio__item"><img src="https://placehold.co/600x400?text=Projet+1" alt="Projet 1" loading="lazy"><div class="portfolio__overlay"><h3>Projet Alpha</h3><p>Design & Développement</p></div></article>\n'
                f'    <article class="portfolio__item"><img src="https://placehold.co/600x400?text=Projet+2" alt="Projet 2" loading="lazy"><div class="portfolio__overlay"><h3>Projet Beta</h3><p>Application Mobile</p></div></article>\n'
                f'    <article class="portfolio__item"><img src="https://placehold.co/600x400?text=Projet+3" alt="Projet 3" loading="lazy"><div class="portfolio__overlay"><h3>Projet Gamma</h3><p>Identité Visuelle</p></div></article>\n'
                f'  </div>\n'
                f'</div></section>\n'
                f'<style>\n'
                f'.portfolio__item {{ position:relative; border-radius:var(--radius-md); overflow:hidden; cursor:pointer; }}\n'
                f'.portfolio__item img {{ width:100%; aspect-ratio:4/3; object-fit:cover; transition:transform .4s; }}\n'
                f'.portfolio__item:hover img {{ transform:scale(1.05); }}\n'
                f'.portfolio__overlay {{ position:absolute; inset:0; background:rgba(0,0,0,.6); display:flex; flex-direction:column; align-items:center; justify-content:center; opacity:0; transition:opacity .3s; }}\n'
                f'.portfolio__item:hover .portfolio__overlay {{ opacity:1; }}\n'
                f'.portfolio__overlay h3 {{ color:#fff; margin-bottom:4px; }} .portfolio__overlay p {{ color:rgba(255,255,255,.7); font-size:var(--text-small); }}\n'
                f'</style>'), 0.90

    def _synth_blog_layout(self, lang, name, entity, facts):
        return (f'<main class="blog-layout"><div class="container">\n'
                f'  <div style="display:grid;grid-template-columns:1fr 300px;gap:32px">\n'
                f'    <div>\n'
                f'      <article class="blog-card"><img src="https://placehold.co/800x400?text=Article" alt="Article" loading="lazy">\n'
                f'        <div class="blog-card__body"><span class="blog-card__date">15 Jan 2025</span><h3><a href="#">Titre de l\'article</a></h3>\n'
                f'          <p>Extrait de l\'article qui donne envie de lire la suite...</p><a href="#" class="blog-card__read-more">Lire la suite →</a></div>\n'
                f'      </article>\n'
                f'    </div>\n'
                f'    <aside class="sidebar-widget"><h4>Catégories</h4>\n'
                f'      <ul><li><a href="#">Tech</a></li><li><a href="#">Design</a></li><li><a href="#">Business</a></li></ul></aside>\n'
                f'  </div>\n'
                f'</div></main>\n'
                f'<style>\n'
                f'.blog-card {{ background:var(--color-bg); border:1px solid var(--color-border); border-radius:var(--radius-lg); overflow:hidden; margin-bottom:32px; }}\n'
                f'.blog-card img {{ width:100%; height:200px; object-fit:cover; }}\n'
                f'.blog-card__body {{ padding:32px; }} .blog-card__date {{ font-size:var(--text-small); color:var(--color-text-muted); }}\n'
                f'.blog-card__read-more {{ color:var(--color-primary); font-weight:600; text-decoration:none; }}\n'
                f'.sidebar-widget {{ background:var(--color-bg-alt); border-radius:var(--radius-md); padding:20px; }}\n'
                f'.sidebar-widget li {{ padding:6px 0; }} .sidebar-widget a {{ color:var(--color-text-muted); text-decoration:none; }}\n'
                f'.sidebar-widget a:hover {{ color:var(--color-primary); }}\n'
                f'@media (max-width:480px) {{ .blog-layout > div {{ grid-template-columns:1fr!important; }} }}\n'
                f'</style>'), 0.90

    # ════════════════ CHARTS SVG ════════════════

    def _synth_bar_chart(self, lang, name, entity, facts):
        return (f'<div class="chart-container">\n'
                f'  <svg class="bar-chart" viewBox="0 0 400 250" role="img" aria-label="Graphique à barres">\n'
                f'    <rect x="40" y="80" width="40" height="150" fill="var(--color-primary)" rx="4"><title>Jan: 150</title></rect>\n'
                f'    <rect x="100" y="50" width="40" height="180" fill="var(--color-accent)" rx="4"><title>Fév: 180</title></rect>\n'
                f'    <rect x="160" y="100" width="40" height="130" fill="var(--color-secondary)" rx="4"><title>Mar: 130</title></rect>\n'
                f'    <rect x="220" y="40" width="40" height="190" fill="var(--color-primary)" rx="4"><title>Avr: 190</title></rect>\n'
                f'    <rect x="280" y="70" width="40" height="160" fill="var(--color-success)" rx="4"><title>Mai: 160</title></rect>\n'
                f'    <line x1="30" y1="10" x2="30" y2="230" stroke="var(--color-border)" stroke-width="2"/>\n'
                f'    <line x1="30" y1="230" x2="380" y2="230" stroke="var(--color-border)" stroke-width="2"/>\n'
                f'    <text x="60" y="245" fill="var(--color-text-muted)" font-size="11" text-anchor="middle">Jan</text>\n'
                f'    <text x="120" y="245" fill="var(--color-text-muted)" font-size="11" text-anchor="middle">Fév</text>\n'
                f'    <text x="180" y="245" fill="var(--color-text-muted)" font-size="11" text-anchor="middle">Mar</text>\n'
                f'    <text x="240" y="245" fill="var(--color-text-muted)" font-size="11" text-anchor="middle">Avr</text>\n'
                f'    <text x="300" y="245" fill="var(--color-text-muted)" font-size="11" text-anchor="middle">Mai</text>\n'
                f'  </svg>\n'
                f'</div>\n'
                f'<style>\n'
                f'.bar-chart {{ width:100%; height:auto; }} .bar-chart rect {{ transition:opacity .2s,transform .3s; transform-origin:bottom; }}\n'
                f'.bar-chart rect:hover {{ opacity:.8; transform:scaleY(1.05); }}\n'
                f'</style>'), 0.93

    def _synth_line_chart(self, lang, name, entity, facts):
        return (f'<div class="chart-container">\n'
                f'  <svg class="line-chart" viewBox="0 0 400 250" role="img" aria-label="Graphique linéaire">\n'
                f'    <line x1="30" y1="10" x2="30" y2="230" stroke="var(--color-border)" stroke-width="2"/>\n'
                f'    <line x1="30" y1="230" x2="380" y2="230" stroke="var(--color-border)" stroke-width="2"/>\n'
                f'    <polyline points="30,200 100,150 170,180 240,90 310,120 370,60" fill="none" stroke="var(--color-primary)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>\n'
                f'    <circle cx="30" cy="200" r="5" fill="var(--color-primary)"/><circle cx="100" cy="150" r="5" fill="var(--color-primary)"/>\n'
                f'    <circle cx="170" cy="180" r="5" fill="var(--color-primary)"/><circle cx="240" cy="90" r="5" fill="var(--color-primary)"/>\n'
                f'    <circle cx="310" cy="120" r="5" fill="var(--color-primary)"/><circle cx="370" cy="60" r="5" fill="var(--color-primary)"/>\n'
                f'  </svg>\n'
                f'</div>\n'
                f'<style>\n'
                f'.line-chart {{ width:100%; height:auto; }}\n'
                f'.line-chart polyline {{ animation:dashIn 1.5s ease-out; stroke-dasharray:500; stroke-dashoffset:500; }}\n'
                f'@keyframes dashIn {{ to {{ stroke-dashoffset:0; }} }}\n'
                f'</style>'), 0.92

    def _synth_pie_chart(self, lang, name, entity, facts):
        return (f'<div class="chart-container" style="max-width:280px">\n'
                f'  <svg class="pie-chart" viewBox="0 0 200 200" role="img" aria-label="Camembert">\n'
                f'    <circle cx="100" cy="100" r="80" fill="var(--color-primary)" stroke="var(--color-bg)" stroke-width="3" stroke-dasharray="251.3 502.6" transform="rotate(-90 100 100)"/>\n'
                f'    <circle cx="100" cy="100" r="80" fill="var(--color-accent)" stroke="var(--color-bg)" stroke-width="3" stroke-dasharray="125.6 502.6" stroke-dashoffset="-251.3" transform="rotate(-90 100 100)"/>\n'
                f'    <circle cx="100" cy="100" r="80" fill="var(--color-secondary)" stroke="var(--color-bg)" stroke-width="3" stroke-dasharray="125.6 502.6" stroke-dashoffset="-376.9" transform="rotate(-90 100 100)"/>\n'
                f'    <text x="100" y="105" text-anchor="middle" fill="var(--color-text)" font-size="14" font-weight="700">100%</text>\n'
                f'  </svg>\n'
                f'  <div class="pie-legend">\n'
                f'    <span><i style="background:var(--color-primary)"></i> Produit A 50%</span>\n'
                f'    <span><i style="background:var(--color-accent)"></i> Produit B 25%</span>\n'
                f'    <span><i style="background:var(--color-secondary)"></i> Produit C 25%</span>\n'
                f'  </div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.pie-legend {{ display:flex; flex-direction:column; gap:8px; margin-top:12px; font-size:var(--text-small); }}\n'
                f'.pie-legend i {{ display:inline-block; width:12px; height:12px; border-radius:2px; margin-right:6px; }}\n'
                f'</style>'), 0.92

    # ════════════════ WIDGETS ════════════════

    def _synth_slider(self, lang, name, entity, facts):
        return (f'<div class="slider-widget">\n'
                f'  <div class="flex-between" style="margin-bottom:4px"><label for="{name}-range">Valeur</label>\n'
                f'    <output for="{name}-range" id="{name}-value">50</output></div>\n'
                f'  <input type="range" id="{name}-range" min="0" max="100" value="50"\n'
                f'         oninput="document.getElementById(\'{name}-value\').textContent=this.value">\n'
                f'</div>\n'
                f'<style>\n'
                f'.slider-widget input[type=range] {{ -webkit-appearance:none; width:100%; height:8px; border-radius:4px; background:var(--color-muted); outline:none; }}\n'
                f'.slider-widget input[type=range]::-webkit-slider-thumb {{ -webkit-appearance:none; width:24px; height:24px; border-radius:50%; background:var(--color-primary); cursor:pointer; box-shadow:var(--shadow-md); }}\n'
                f'.slider-widget output {{ font-weight:700; color:var(--color-primary); font-size:var(--text-h4); }}\n'
                f'</style>'), 0.94

    def _synth_toggle(self, lang, name, entity, facts):
        return (f'<label class="toggle" aria-label="Basculer">\n'
                f'  <input type="checkbox" class="toggle__input" onchange="document.body.dataset.theme=this.checked?\'dark\':\'light\'">\n'
                f'  <span class="toggle__track"><span class="toggle__thumb"></span></span>\n'
                f'  <span class="toggle__label">Activer</span>\n'
                f'</label>\n'
                f'<style>\n'
                f'.toggle {{ display:inline-flex; align-items:center; gap:10px; cursor:pointer; }}\n'
                f'.toggle__input {{ position:absolute; opacity:0; width:0; height:0; }}\n'
                f'.toggle__track {{ width:52px; height:28px; border-radius:14px; background:var(--color-muted); position:relative; transition:background .3s; }}\n'
                f'.toggle__input:checked + .toggle__track {{ background:var(--color-primary); }}\n'
                f'.toggle__thumb {{ position:absolute; top:3px; left:3px; width:22px; height:22px; border-radius:50%; background:#fff; transition:transform .3s; }}\n'
                f'.toggle__input:checked + .toggle__track .toggle__thumb {{ transform:translateX(24px); }}\n'
                f'</style>'), 0.95

    def _synth_progress(self, lang, name, entity, facts):
        return (f'<div class="progress-widget">\n'
                f'  <div class="flex-between" style="margin-bottom:4px"><span>Progression</span><span style="font-weight:700;color:var(--color-primary)">68%</span></div>\n'
                f'  <div class="progress" role="progressbar" aria-valuenow="68" aria-valuemin="0" aria-valuemax="100">\n'
                f'    <div class="progress__fill" style="width:68%"></div>\n'
                f'  </div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.progress {{ height:12px; border-radius:6px; background:var(--color-muted); overflow:hidden; }}\n'
                f'.progress__fill {{ height:100%; border-radius:6px; background:var(--gradient-primary); animation:progressIn 1s ease-out; }}\n'
                f'@keyframes progressIn {{ from {{ width:0 }} }}\n'
                f'</style>'), 0.95

    def _synth_star_rating(self, lang, name, entity, facts):
        return (f'<div class="star-rating" role="radiogroup" aria-label="Note">\n'
                f'  <input type="radio" id="{name}-s5" name="{name}-stars" value="5"><label for="{name}-s5">★</label>\n'
                f'  <input type="radio" id="{name}-s4" name="{name}-stars" value="4"><label for="{name}-s4">★</label>\n'
                f'  <input type="radio" id="{name}-s3" name="{name}-stars" value="3" checked><label for="{name}-s3">★</label>\n'
                f'  <input type="radio" id="{name}-s2" name="{name}-stars" value="2"><label for="{name}-s2">★</label>\n'
                f'  <input type="radio" id="{name}-s1" name="{name}-stars" value="1"><label for="{name}-s1">★</label>\n'
                f'</div>\n'
                f'<style>\n'
                f'.star-rating {{ display:flex; flex-direction:row-reverse; justify-content:flex-end; gap:2px; }}\n'
                f'.star-rating input {{ display:none; }}\n'
                f'.star-rating label {{ font-size:1.8rem; color:var(--color-muted); cursor:pointer; transition:color .15s,transform .15s; }}\n'
                f'.star-rating input:checked ~ label, .star-rating label:hover, .star-rating label:hover ~ label {{ color:var(--color-warning); }}\n'
                f'</style>'), 0.94

    def _synth_timeline(self, lang, name, entity, facts):
        return (f'<div class="timeline">\n'
                f'  <div class="timeline__item"><div class="timeline__dot" style="background:var(--color-primary)"></div>\n'
                f'    <div class="timeline__content"><time class="timeline__date">Jan 2026</time><h4>Lancement du projet</h4><p>Première version déployée.</p></div></div>\n'
                f'  <div class="timeline__item"><div class="timeline__dot" style="background:var(--color-accent)"></div>\n'
                f'    <div class="timeline__content"><time class="timeline__date">Mar 2026</time><h4>Phase 2 — Croissance</h4><p>10 000 utilisateurs actifs.</p></div></div>\n'
                f'  <div class="timeline__item"><div class="timeline__dot" style="background:var(--color-success)"></div>\n'
                f'    <div class="timeline__content"><time class="timeline__date">Juil 2026</time><h4>Internationalisation</h4><p>12 langues.</p></div></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.timeline {{ position:relative; padding-left:32px; }}\n'
                f'.timeline::before {{ content:\'\'; position:absolute; left:11px; top:0; bottom:0; width:2px; background:var(--color-border); }}\n'
                f'.timeline__item {{ position:relative; margin-bottom:32px; }}\n'
                f'.timeline__dot {{ position:absolute; left:-32px; top:4px; width:14px; height:14px; border-radius:50%; border:3px solid var(--color-bg); z-index:1; }}\n'
                f'.timeline__content {{ background:var(--color-bg-alt); border:1px solid var(--color-border); border-radius:var(--radius-md); padding:20px; }}\n'
                f'.timeline__date {{ font-size:var(--text-small); color:var(--color-text-muted); }}\n'
                f'</style>'), 0.93

    def _synth_calendar(self, lang, name, entity, facts):
        days = "L M M J V S D".split()
        header = ''.join(f'<span>{d}</span>' for d in days)
        cells = ''.join(f'<button class="calendar__day{" today" if i==14 else ""}">{i+1}</button>\n' for i in range(31))
        return (f'<div class="calendar">\n'
                f'  <div class="calendar__header flex-between"><button class="btn btn-ghost btn-sm">←</button><h3>Juillet 2026</h3><button class="btn btn-ghost btn-sm">→</button></div>\n'
                f'  <div class="calendar__weekdays">{header}</div>\n'
                f'  <div class="calendar__grid">{cells}</div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.calendar {{ max-width:320px; }}\n'
                f'.calendar__weekdays {{ display:grid; grid-template-columns:repeat(7,1fr); text-align:center; font-size:var(--text-small); color:var(--color-text-muted); margin:12px 0; }}\n'
                f'.calendar__grid {{ display:grid; grid-template-columns:repeat(7,1fr); gap:2px; }}\n'
                f'.calendar__day {{ aspect-ratio:1; border:none; border-radius:var(--radius-md); background:transparent; cursor:pointer; color:var(--color-text); transition:all .15s; }}\n'
                f'.calendar__day:hover {{ background:var(--color-muted); }}\n'
                f'.calendar__day.today {{ background:var(--color-primary); color:#fff; font-weight:700; }}\n'
                f'</style>'), 0.93

    # ════════════════ MINI-JEUX ════════════════

    def _synth_snake_game(self, lang, name, entity, facts):
        return (f'<canvas id="snake-canvas" width="400" height="400" style="border:2px solid var(--color-border);border-radius:var(--radius-md);display:block;margin:0 auto;background:var(--color-bg-alt)"></canvas>\n'
                f'<div class="text-center" style="margin-top:8px"><span id="snake-score" style="font-weight:700;color:var(--color-primary)">Score: 0</span></div>\n'
                f'<button class="btn btn-primary btn-sm" onclick="startSnake()" style="margin:8px auto;display:block">🔄 Nouvelle partie</button>\n'
                f'<script>\n'
                f'let snake,food,dir,score,gameLoop,grid=20,ctx,canvas;\n'
                f'function initSnake(){{canvas=document.getElementById("snake-canvas");if(!canvas)return;ctx=canvas.getContext("2d");snake=[{{x:5,y:10}},{{x:4,y:10}},{{x:3,y:10}}];dir={{x:1,y:0}};score=0;spawnFood();document.addEventListener("keydown",e=>{{if(e.key==="ArrowUp"&&dir.y===0)dir={{x:0,y:-1}};if(e.key==="ArrowDown"&&dir.y===0)dir={{x:0,y:1}};if(e.key==="ArrowLeft"&&dir.x===0)dir={{x:-1,y:0}};if(e.key==="ArrowRight"&&dir.x===0)dir={{x:1,y:0}}}})}}\n'
                f'function spawnFood(){{food={{x:Math.floor(Math.random()*20),y:Math.floor(Math.random()*20)}}}}\n'
                f'function draw(){{ctx.fillStyle="#1a1a2e";ctx.fillRect(0,0,400,400);ctx.fillStyle="#10b981";snake.forEach(s=>ctx.fillRect(s.x*grid,s.y*grid,grid-2,grid-2));ctx.fillStyle="#f97316";ctx.fillRect(food.x*grid,food.y*grid,grid-2,grid-2)}}\n'
                f'function update(){{const head={{x:snake[0].x+dir.x,y:snake[0].y+dir.y}};if(head.x<0||head.x>=20||head.y<0||head.y>=20||snake.some(s=>s.x===head.x&&s.y===head.y)){{clearInterval(gameLoop);alert("Game Over! Score: "+score);return}}snake.unshift(head);if(head.x===food.x&&head.y===food.y){{score+=10;spawnFood()}}else{{snake.pop()}}draw()}}\n'
                f'function startSnake(){{if(gameLoop)clearInterval(gameLoop);initSnake();gameLoop=setInterval(update,120)}}startSnake();\n'
                f'</script>'), 0.90

    def _synth_pong_game(self, lang, name, entity, facts):
        return (f'<canvas id="pong-canvas" width="500" height="300" style="border:2px solid var(--color-border);border-radius:var(--radius-md);display:block;margin:0 auto;background:var(--color-bg-alt)"></canvas>\n'
                f'<div class="text-center" style="margin-top:8px"><span id="pong-score" style="font-weight:700;color:var(--color-primary)">Joueur: 0 — IA: 0</span></div>\n'
                f'<button class="btn btn-primary btn-sm" onclick="startPong()" style="margin:8px auto;display:block">🔄 Nouvelle partie</button>\n'
                f'<script>\n'
                f'let pongLoop,paddle={{y:120}},ai={{y:120}},ball={{x:250,y:150,vx:3,vy:2}},pScore=0,aScore=0;\n'
                f'function initPong(){{paddle.y=120;ai.y=120;ball.x=250;ball.y=150;ball.vx=3*(Math.random()>0.5?1:-1);ball.vy=2*(Math.random()>0.5?1:-1)}}\n'
                f'function drawPong(){{const c=document.getElementById("pong-canvas");if(!c)return;const ctx=c.getContext("2d");ctx.fillStyle="#1a1a2e";ctx.fillRect(0,0,500,300);ctx.fillStyle="#fff";ctx.fillRect(10,paddle.y,8,60);ctx.fillRect(482,ai.y,8,60);ctx.fillRect(ball.x-4,ball.y-4,8,8);for(let i=0;i<300;i+=20){{ctx.fillRect(248,i,4,12)}}}}\n'
                f'function updatePong(){{ball.x+=ball.vx;ball.y+=ball.vy;if(ball.y<=0||ball.y>=290)ball.vy*=-1;if(ball.x<=18&&ball.y>paddle.y&&ball.y<paddle.y+60){{ball.vx*=-1;ball.x=19}}if(ball.x>=478&&ball.y>ai.y&&ball.y<ai.y+60){{ball.vx*=-1;ball.x=477}}if(ball.x<0){{aScore++;initPong()}}if(ball.x>500){{pScore++;initPong()}}document.getElementById("pong-score").textContent="Joueur: "+pScore+" — IA: "+aScore;ai.y+=(ball.y-(ai.y+30))*0.12;drawPong()}}\n'
                f'document.addEventListener("mousemove",e=>{{const c=document.getElementById("pong-canvas");if(!c)return;const r=c.getBoundingClientRect();paddle.y=(e.clientY-r.top)*(300/r.height)-30}});\n'
                f'function startPong(){{if(pongLoop)clearInterval(pongLoop);pScore=aScore=0;initPong();pongLoop=setInterval(updatePong,16)}}startPong();\n'
                f'</script>'), 0.90

    # ════════════════ CANVAS DEMOS ════════════════

    def _synth_particles(self, lang, name, entity, facts):
        return (f'<canvas id="particles-canvas" width="400" height="300" style="border-radius:var(--radius-lg);display:block;margin:0 auto;background:var(--color-bg-alt)"></canvas>\n'
                f'<script>\n'
                f'(function(){{const c=document.getElementById("particles-canvas");if(!c)return;const ctx=c.getContext("2d");const pts=Array.from({{length:50}},()=>({{x:Math.random()*400,y:Math.random()*300,vx:(Math.random()-.5)*1.5,vy:(Math.random()-.5)*1.5,r:Math.random()*3+1}}));function draw(){{ctx.fillStyle="rgba(10,10,26,0.15)";ctx.fillRect(0,0,400,300);const color="#6366f1";pts.forEach(p=>{{p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>400)p.vx*=-1;if(p.y<0||p.y>300)p.vy*=-1;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle=color;ctx.fill()}});requestAnimationFrame(draw)}}draw()}})();\n'
                f'</script>'), 0.90

    def _synth_waves_canvas(self, lang, name, entity, facts):
        return (f'<canvas id="waves-canvas" width="400" height="250" style="border-radius:var(--radius-lg);display:block;margin:0 auto;background:var(--color-bg-alt)"></canvas>\n'
                f'<script>\n'
                f'(function(){{const c=document.getElementById("waves-canvas");if(!c)return;const ctx=c.getContext("2d");let t=0;const colors=["#6366f1","#f97316","#84cc16"];function draw(){{ctx.fillStyle="#1a1a2e";ctx.fillRect(0,0,400,250);for(let w=0;w<3;w++){{ctx.beginPath();ctx.strokeStyle=colors[w];ctx.lineWidth=2;ctx.globalAlpha=.8;for(let x=0;x<400;x++){{const y=125+Math.sin(x*0.02+t*0.03+w*1.5)*30*(w+1)+Math.sin(x*0.05+t*0.02)*15;x===0?ctx.moveTo(x,y):ctx.lineTo(x,y)}}ctx.stroke()}}ctx.globalAlpha=1;t++;requestAnimationFrame(draw)}}draw()}})();\n'
                f'</script>'), 0.90

    def _synth_fractal(self, lang, name, entity, facts):
        return (f'<canvas id="fractal-canvas" width="400" height="350" style="border-radius:var(--radius-lg);display:block;margin:0 auto;background:var(--color-bg-alt)"></canvas>\n'
                f'<script>\n'
                f'(function(){{const c=document.getElementById("fractal-canvas");if(!c)return;const ctx=c.getContext("2d");const color="#6366f1";function branch(x,y,len,angle,depth){{if(depth>10)return;const x2=x+Math.cos(angle)*len,y2=y+Math.sin(angle)*len;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x2,y2);ctx.strokeStyle=color;ctx.lineWidth=depth>6?1.5:depth>3?1:0.5;ctx.globalAlpha=1-depth*0.08;ctx.stroke();branch(x2,y2,len*0.7,angle-0.5,depth+1);branch(x2,y2,len*0.7,angle+0.5,depth+1)}}ctx.fillStyle="#1a1a2e";ctx.fillRect(0,0,400,350);branch(200,330,80,-Math.PI/2,0);ctx.globalAlpha=1}})();\n'
                f'</script>'), 0.90

    # ════════════════ UI AVANCÉ ════════════════

    def _synth_carousel(self, lang, name, entity, facts):
        return (f'<div class="carousel" role="region" aria-label="Carrousel">\n'
                f'  <div class="carousel__track" id="{name}-track">\n'
                f'    <div class="carousel__slide active"><div style="background:var(--gradient-primary);aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;font-size:3rem">🖼️</div></div>\n'
                f'    <div class="carousel__slide"><div style="background:var(--color-secondary);aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;font-size:3rem">🌄</div></div>\n'
                f'    <div class="carousel__slide"><div style="background:var(--color-accent);aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;font-size:3rem">🎨</div></div>\n'
                f'  </div>\n'
                f'  <button class="carousel__btn carousel__btn--prev" onclick="moveCarousel(-1)" aria-label="Précédent">‹</button>\n'
                f'  <button class="carousel__btn carousel__btn--next" onclick="moveCarousel(1)" aria-label="Suivant">›</button>\n'
                f'  <div class="carousel__dots"><span class="active"></span><span></span><span></span></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.carousel {{ position:relative; overflow:hidden; border-radius:var(--radius-lg); }}\n'
                f'.carousel__track {{ display:flex; transition:transform .5s ease; }}\n'
                f'.carousel__slide {{ min-width:100%; }}\n'
                f'.carousel__btn {{ position:absolute; top:50%; transform:translateY(-50%); background:rgba(0,0,0,.5); color:#fff; border:none; width:40px; height:40px; border-radius:50%; font-size:1.5rem; cursor:pointer; z-index:2; }}\n'
                f'.carousel__btn--prev {{ left:12px; }} .carousel__btn--next {{ right:12px; }}\n'
                f'.carousel__dots {{ display:flex; justify-content:center; gap:8px; padding:12px; }}\n'
                f'.carousel__dots span {{ width:10px; height:10px; border-radius:50%; background:var(--color-muted); cursor:pointer; }} .carousel__dots span.active {{ background:var(--color-primary); }}\n'
                f'</style>\n'
                f'<script>let cIdx=0;function moveCarousel(d){{const t=document.getElementById("{name}-track");if(!t)return;const s=t.children;cIdx=(cIdx+d+s.length)%s.length;t.style.transform=`translateX(-${{cIdx*100}}%)`;document.querySelectorAll(".carousel__dots span").forEach((d,i)=>d.classList.toggle("active",i===cIdx))}}</script>'), 0.93

    def _synth_tabs(self, lang, name, entity, facts):
        return (f'<div class="tabs">\n'
                f'  <div class="tabs__nav" role="tablist">\n'
                f'    <button class="tabs__tab active" role="tab" aria-selected="true" onclick="switchTab(\'{name}-tab1\')">Onglet 1</button>\n'
                f'    <button class="tabs__tab" role="tab" aria-selected="false" onclick="switchTab(\'{name}-tab2\')">Onglet 2</button>\n'
                f'    <button class="tabs__tab" role="tab" aria-selected="false" onclick="switchTab(\'{name}-tab3\')">Onglet 3</button>\n'
                f'  </div>\n'
                f'  <div class="tabs__panel active" id="{name}-tab1" role="tabpanel"><p>Contenu onglet 1</p></div>\n'
                f'  <div class="tabs__panel" id="{name}-tab2" role="tabpanel" hidden><p>Contenu onglet 2</p></div>\n'
                f'  <div class="tabs__panel" id="{name}-tab3" role="tabpanel" hidden><p>Contenu onglet 3</p></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.tabs__nav {{ display:flex; border-bottom:2px solid var(--color-border); }}\n'
                f'.tabs__tab {{ padding:12px 20px; border:none; background:none; cursor:pointer; color:var(--color-text-muted); border-bottom:2px solid transparent; margin-bottom:-2px; transition:all .2s; font:inherit; }}\n'
                f'.tabs__tab.active {{ color:var(--color-primary); border-bottom-color:var(--color-primary); font-weight:600; }}\n'
                f'.tabs__panel {{ padding:20px; display:none; }} .tabs__panel.active {{ display:block; }}\n'
                f'</style>\n'
                f'<script>function switchTab(id){{document.querySelectorAll(".tabs__panel").forEach(p=>{{p.hidden=true;p.classList.remove("active")}});const p=document.getElementById(id);if(p){{p.hidden=false;p.classList.add("active")}};document.querySelectorAll(".tabs__tab").forEach(t=>t.classList.toggle("active",t.getAttribute("onclick")?.includes(id)))}}</script>'), 0.93

    def _synth_accordion(self, lang, name, entity, facts):
        return (f'<dl class="accordion">\n'
                f'  <div class="accordion__item"><dt><button class="accordion__trigger" aria-expanded="false" onclick="this.setAttribute(\'aria-expanded\',this.getAttribute(\'aria-expanded\')===\'true\'?\'false\':\'true\');this.nextElementSibling.hidden=!this.nextElementSibling.hidden">Section 1 — Détails</button></dt><dd class="accordion__content" hidden><p>Contenu détaillé de la section 1.</p></dd></div>\n'
                f'  <div class="accordion__item"><dt><button class="accordion__trigger" aria-expanded="false" onclick="this.setAttribute(\'aria-expanded\',this.getAttribute(\'aria-expanded\')===\'true\'?\'false\':\'true\');this.nextElementSibling.hidden=!this.nextElementSibling.hidden">Section 2 — Plus d\'infos</button></dt><dd class="accordion__content" hidden><p>Contenu de la section 2.</p></dd></div>\n'
                f'  <div class="accordion__item"><dt><button class="accordion__trigger" aria-expanded="false" onclick="this.setAttribute(\'aria-expanded\',this.getAttribute(\'aria-expanded\')===\'true\'?\'false\':\'true\');this.nextElementSibling.hidden=!this.nextElementSibling.hidden">Section 3 — Configuration</button></dt><dd class="accordion__content" hidden><p>Paramètres avancés.</p></dd></div>\n'
                f'</dl>\n'
                f'<style>\n'
                f'.accordion__item {{ border:1px solid var(--color-border); border-radius:var(--radius-md); margin-bottom:8px; overflow:hidden; }}\n'
                f'.accordion__trigger {{ width:100%; text-align:left; padding:16px 20px; background:var(--color-bg-alt); border:none; font-weight:600; cursor:pointer; display:flex; justify-content:space-between; align-items:center; color:var(--color-text); font:inherit; }}\n'
                f'.accordion__trigger::after {{ content:"+"; font-size:1.3rem; transition:transform .3s; }}\n'
                f'.accordion__trigger[aria-expanded="true"]::after {{ content:"−"; }}\n'
                f'.accordion__content {{ padding:16px 20px; color:var(--color-text-muted); line-height:1.6; }}\n'
                f'</style>'), 0.95

    def _synth_tooltip(self, lang, name, entity, facts):
        return (f'<div class="flex flex-gap" style="padding:40px">\n'
                f'  <span class="tooltip" data-tooltip="Information utile">Survolez-moi</span>\n'
                f'  <span class="tooltip tooltip--top" data-tooltip="Tooltip en haut">Top</span>\n'
                f'</div>\n'
                f'<style>\n'
                f'.tooltip {{ position:relative; cursor:help; border-bottom:1px dashed var(--color-primary); }}\n'
                f'.tooltip::after {{ content:attr(data-tooltip); position:absolute; bottom:120%; left:50%; transform:translateX(-50%); background:var(--color-text); color:var(--color-bg); padding:6px 12px; border-radius:var(--radius-sm); font-size:var(--text-small); white-space:nowrap; opacity:0; visibility:hidden; transition:all .2s; z-index:10; }}\n'
                f'.tooltip:hover::after {{ opacity:1; visibility:visible; }}\n'
                f'.tooltip--top::after {{ bottom:auto; top:120%; }}\n'
                f'</style>'), 0.94

    def _synth_dropdown(self, lang, name, entity, facts):
        return (f'<div class="dropdown">\n'
                f'  <button class="dropdown__trigger" onclick="this.parentElement.classList.toggle(\'open\')" aria-haspopup="true">Menu <span>▾</span></button>\n'
                f'  <ul class="dropdown__menu" role="menu" hidden>\n'
                f'    <li role="none"><a href="#" role="menuitem">Profil</a></li>\n'
                f'    <li role="none"><a href="#" role="menuitem">Paramètres</a></li>\n'
                f'    <li role="none"><a href="#" role="menuitem" style="color:var(--color-error)">Déconnexion</a></li>\n'
                f'  </ul>\n'
                f'</div>\n'
                f'<style>\n'
                f'.dropdown {{ position:relative; display:inline-block; }}\n'
                f'.dropdown__trigger {{ padding:8px 16px; border:1px solid var(--color-border); border-radius:var(--radius-md); background:var(--color-bg); cursor:pointer; color:var(--color-text); font:inherit; }}\n'
                f'.dropdown__menu {{ position:absolute; top:100%; left:0; margin-top:4px; min-width:180px; background:var(--color-bg); border:1px solid var(--color-border); border-radius:var(--radius-md); box-shadow:var(--shadow-lg); z-index:50; opacity:0; transform:translateY(-8px); transition:all .2s; }}\n'
                f'.dropdown.open .dropdown__menu {{ opacity:1; transform:translateY(0); display:block!important; }}\n'
                f'.dropdown__menu a {{ display:block; padding:10px 16px; color:var(--color-text); text-decoration:none; }} .dropdown__menu a:hover {{ background:var(--color-muted); }}\n'
                f'</style>'), 0.94

    def _synth_breadcrumb(self, lang, name, entity, facts):
        return (f'<nav class="breadcrumb" aria-label="Fil d\'Ariane">\n'
                f'  <ol><li><a href="/">Accueil</a></li><li><a href="/category">Catégorie</a></li><li><a href="/page" aria-current="page">Page actuelle</a></li></ol>\n'
                f'</nav>\n'
                f'<style>\n'
                f'.breadcrumb ol {{ display:flex; align-items:center; gap:8px; list-style:none; font-size:var(--text-small); }}\n'
                f'.breadcrumb li:not(:last-child)::after {{ content:"/"; margin-left:8px; color:var(--color-text-muted); }}\n'
                f'.breadcrumb a {{ color:var(--color-text-muted); text-decoration:none; }} .breadcrumb a:hover {{ color:var(--color-primary); }}\n'
                f'.breadcrumb [aria-current] {{ color:var(--color-text); font-weight:600; }}\n'
                f'</style>'), 0.95

    def _synth_pagination(self, lang, name, entity, facts):
        return (f'<nav class="pagination" aria-label="Pagination">\n'
                f'  <button class="pagination__btn" disabled>← Précédent</button>\n'
                f'  <button class="pagination__btn active" aria-current="page">1</button>\n'
                f'  <button class="pagination__btn">2</button><button class="pagination__btn">3</button>\n'
                f'  <span class="pagination__ellipsis">…</span>\n'
                f'  <button class="pagination__btn">8</button>\n'
                f'  <button class="pagination__btn">Suivant →</button>\n'
                f'</nav>\n'
                f'<style>\n'
                f'.pagination {{ display:flex; align-items:center; gap:4px; flex-wrap:wrap; }}\n'
                f'.pagination__btn {{ min-width:40px; height:40px; border:1px solid var(--color-border); border-radius:var(--radius-md); background:var(--color-bg); cursor:pointer; color:var(--color-text); font:inherit; }}\n'
                f'.pagination__btn:hover:not(:disabled):not(.active) {{ border-color:var(--color-primary); }}\n'
                f'.pagination__btn.active {{ background:var(--color-primary); color:#fff; }} .pagination__btn:disabled {{ opacity:.4; cursor:not-allowed; }}\n'
                f'</style>'), 0.94

    def _synth_search_bar(self, lang, name, entity, facts):
        return (f'<div class="search-bar">\n'
                f'  <div class="search-bar__wrapper">\n'
                f'    <span>🔍</span>\n'
                f'    <input type="search" placeholder="Rechercher..." oninput="document.getElementById(\'{name}-suggestions\').hidden=!this.value">\n'
                f'  </div>\n'
                f'  <div class="search-bar__suggestions" id="{name}-suggestions" hidden>\n'
                f'    <ul><li>Résultat suggéré 1</li><li>Résultat suggéré 2</li><li>Résultat suggéré 3</li></ul>\n'
                f'  </div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.search-bar {{ position:relative; max-width:500px; }}\n'
                f'.search-bar__wrapper {{ display:flex; align-items:center; gap:8px; padding:10px 16px; border:2px solid var(--color-border); border-radius:var(--radius-lg); background:var(--color-bg); transition:border-color .2s; }}\n'
                f'.search-bar__wrapper:focus-within {{ border-color:var(--color-primary); }}\n'
                f'.search-bar__wrapper input {{ flex:1; border:none; background:none; font-size:var(--text-body); color:var(--color-text); outline:none; }}\n'
                f'.search-bar__suggestions {{ position:absolute; top:100%; left:0; right:0; margin-top:4px; background:var(--color-bg); border:1px solid var(--color-border); border-radius:var(--radius-md); box-shadow:var(--shadow-lg); padding:12px; z-index:20; }}\n'
                f'.search-bar__suggestions li {{ padding:6px 0; cursor:pointer; color:var(--color-text-muted); }} .search-bar__suggestions li:hover {{ color:var(--color-primary); }}\n'
                f'</style>'), 0.93

    def _synth_toast(self, lang, name, entity, facts):
        return (f'<div class="toast-container" id="{name}-toasts" aria-live="polite"></div>\n'
                f'<button class="btn btn-primary btn-sm" onclick="showToast(\'✅ Action réussie !\',\'success\')">Succès</button>\n'
                f'<button class="btn btn-ghost btn-sm" onclick="showToast(\'⚠️ Attention\',\'warning\')">Warning</button>\n'
                f'<button class="btn btn-ghost btn-sm" onclick="showToast(\'❌ Erreur\',\'error\')">Erreur</button>\n'
                f'<style>\n'
                f'.toast-container {{ position:fixed; bottom:20px; right:20px; z-index:9999; display:flex; flex-direction:column; gap:8px; }}\n'
                f'.toast {{ padding:14px 20px; border-radius:var(--radius-md); color:#fff; font-weight:500; animation:slideInRight .3s ease-out, fadeOut .3s 2.7s forwards; box-shadow:var(--shadow-lg); max-width:350px; }}\n'
                f'.toast--success {{ background:var(--color-success); }} .toast--warning {{ background:var(--color-warning); color:#000; }} .toast--error {{ background:var(--color-error); }}\n'
                f'@keyframes fadeOut {{ to {{ opacity:0; transform:translateX(30px); }} }}\n'
                f'</style>\n'
                f'<script>function showToast(msg,type){{const t=document.createElement("div");t.className=`toast toast-${{type}}`;t.textContent=msg;document.getElementById("{name}-toasts").appendChild(t);setTimeout(()=>t.remove(),3000)}}</script>'), 0.93

    def _synth_skeleton(self, lang, name, entity, facts):
        return (f'<div class="skeleton-card">\n'
                f'  <div class="skeleton skeleton--image"></div>\n'
                f'  <div class="skeleton skeleton--title"></div>\n'
                f'  <div class="skeleton skeleton--text"></div>\n'
                f'  <div class="skeleton skeleton--button"></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.skeleton {{ background:linear-gradient(90deg,var(--color-muted) 25%,var(--color-bg-alt) 50%,var(--color-muted) 75%); background-size:200% 100%; animation:shimmer 1.5s infinite; border-radius:var(--radius-sm); }}\n'
                f'.skeleton--image {{ height:180px; border-radius:var(--radius-md); margin-bottom:12px; }}\n'
                f'.skeleton--title {{ height:20px; width:70%; margin-bottom:8px; }} .skeleton--text {{ height:14px; margin-bottom:6px; }}\n'
                f'.skeleton--button {{ height:40px; width:120px; border-radius:var(--radius-md); margin-top:12px; }}\n'
                f'@keyframes shimmer {{ 0% {{ background-position:-200% 0; }} 100% {{ background-position:200% 0; }} }}\n'
                f'</style>'), 0.95

    def _synth_code_editor(self, lang, name, entity, facts):
        return (f'<div class="code-editor-widget">\n'
                f'  <div class="code-editor__header flex-between"><span style="color:var(--color-primary);font-weight:600;font-size:var(--text-small)">HTML</span>\n'
                f'    <button class="btn btn-ghost btn-sm" onclick="runCode()">▶ Exécuter</button></div>\n'
                f'  <textarea class="code-editor__textarea" id="{name}-editor" rows="8" spellcheck="false">&lt;h1&gt;Hello World&lt;/h1&gt;\n&lt;p&gt;Éditez ce code et cliquez sur Exécuter&lt;/p&gt;</textarea>\n'
                f'  <div class="code-editor__preview" id="{name}-preview"></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.code-editor-widget {{ border:1px solid var(--color-border); border-radius:var(--radius-lg); overflow:hidden; }}\n'
                f'.code-editor__header {{ padding:8px 16px; background:var(--color-bg-alt); border-bottom:1px solid var(--color-border); }}\n'
                f'.code-editor__textarea {{ width:100%; padding:16px; background:#0d0d1a; color:#e0d0ff; border:none; font-family:monospace; font-size:var(--text-small); line-height:1.6; resize:vertical; outline:none; }}\n'
                f'.code-editor__preview {{ padding:16px; min-height:60px; border-top:1px solid var(--color-border); }}\n'
                f'</style>\n'
                f'<script>function runCode(){{const e=document.getElementById("{name}-editor");const p=document.getElementById("{name}-preview");if(e&&p)p.innerHTML=e.value}}</script>'), 0.92

    def _synth_file_upload(self, lang, name, entity, facts):
        return (f'<div class="file-upload">\n'
                f'  <label class="file-upload__zone" for="{name}-file" ondragover="event.preventDefault();this.style.borderColor=\'var(--color-primary)\'" ondragleave="this.style.borderColor=\'var(--color-border)\'" ondrop="event.preventDefault();this.style.borderColor=\'var(--color-border)\';handleFiles(event.dataTransfer.files)">\n'
                f'    <span style="font-size:2.5rem">📁</span><p>Glissez-déposez vos fichiers ici</p><span style="font-size:var(--text-small);color:var(--color-text-muted)">ou cliquez pour parcourir</span>\n'
                f'  </label>\n'
                f'  <input type="file" id="{name}-file" multiple onchange="handleFiles(this.files)" hidden>\n'
                f'  <div class="file-upload__preview" id="{name}-preview"></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.file-upload__zone {{ display:flex; flex-direction:column; align-items:center; gap:8px; padding:52px; border:2px dashed var(--color-border); border-radius:var(--radius-lg); cursor:pointer; transition:border-color .3s; }}\n'
                f'.file-upload__zone:hover {{ border-color:var(--color-primary); }}\n'
                f'.file-upload__preview {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }} .file-upload__preview img {{ width:80px; height:80px; object-fit:cover; border-radius:var(--radius-md); }}\n'
                f'</style>\n'
                f'<script>function handleFiles(files){{const p=document.getElementById("{name}-preview");if(!p)return;Array.from(files).forEach(f=>{{if(f.type.startsWith("image/")){{const r=new FileReader();r.onload=e=>{{const img=document.createElement("img");img.src=e.target.result;p.appendChild(img)}};r.readAsDataURL(f)}}else{{const s=document.createElement("span");s.textContent="📄 "+f.name;p.appendChild(s)}}}})}}</script>'), 0.93

    def _synth_audio_player(self, lang, name, entity, facts):
        return (f'<div class="audio-player">\n'
                f'  <div class="audio-player__artwork">🎵</div>\n'
                f'  <div class="audio-player__info"><strong>Morceau de démonstration</strong>\n'
                f'    <span style="color:var(--color-text-muted);font-size:var(--text-small)">Artiste • Album</span></div>\n'
                f'  <div class="audio-player__controls">\n'
                f'    <button class="audio-player__btn" aria-label="Précédent">⏮</button>\n'
                f'    <button class="audio-player__btn audio-player__btn--play" aria-label="Lecture" onclick="this.textContent=this.textContent===\'▶\'?\'⏸\':\'▶\'">▶</button>\n'
                f'    <button class="audio-player__btn" aria-label="Suivant">⏭</button></div>\n'
                f'  <div class="audio-player__progress"><span style="font-size:var(--text-small)">1:23</span>\n'
                f'    <div class="progress" style="flex:1;margin:0 12px"><div class="progress__fill" style="width:35%"></div></div>\n'
                f'    <span style="font-size:var(--text-small)">3:45</span></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.audio-player {{ background:var(--color-bg-alt); border:1px solid var(--color-border); border-radius:var(--radius-lg); padding:20px; max-width:400px; }}\n'
                f'.audio-player__artwork {{ aspect-ratio:1; background:var(--gradient-subtle); border-radius:var(--radius-md); display:flex; align-items:center; justify-content:center; font-size:4rem; margin-bottom:20px; }}\n'
                f'.audio-player__controls {{ display:flex; justify-content:center; gap:16px; margin:20px 0; }}\n'
                f'.audio-player__btn {{ width:44px; height:44px; border-radius:50%; border:none; background:var(--color-bg); cursor:pointer; font-size:1.2rem; }} .audio-player__btn:hover {{ background:var(--color-primary); color:#fff; }}\n'
                f'.audio-player__btn--play {{ width:56px; height:56px; background:var(--color-primary); color:#fff; }}\n'
                f'.audio-player__progress {{ display:flex; align-items:center; }}\n'
                f'</style>'), 0.93

    def _synth_color_picker(self, lang, name, entity, facts):
        return (f'<div class="color-picker">\n'
                f'  <label style="font-weight:500">Couleur</label>\n'
                f'  <div class="flex flex-gap-sm" style="margin:8px 0;align-items:center">\n'
                f'    <input type="color" value="#6366f1" style="width:48px;height:48px;border:none;border-radius:var(--radius-md);cursor:pointer"\n'
                f'           oninput="document.getElementById(\'{name}-hex\').textContent=this.value;document.getElementById(\'{name}-preview\').style.background=this.value">\n'
                f'    <span id="{name}-hex" style="font-family:monospace;font-weight:600">#6366f1</span>\n'
                f'  </div>\n'
                f'  <div class="flex flex-gap-sm">\n'
                f'    <button style="width:28px;height:28px;border-radius:50%;background:#6366f1;border:2px solid var(--color-bg);cursor:pointer" aria-label="Violet"></button>\n'
                f'    <button style="width:28px;height:28px;border-radius:50%;background:#ec4899;border:2px solid var(--color-bg);cursor:pointer" aria-label="Rose"></button>\n'
                f'    <button style="width:28px;height:28px;border-radius:50%;background:#f97316;border:2px solid var(--color-bg);cursor:pointer" aria-label="Orange"></button>\n'
                f'    <button style="width:28px;height:28px;border-radius:50%;background:#10b981;border:2px solid var(--color-bg);cursor:pointer" aria-label="Vert"></button>\n'
                f'  </div>\n'
                f'  <div id="{name}-preview" style="background:#6366f1;height:60px;border-radius:var(--radius-md);margin-top:12px"></div>\n'
                f'</div>'), 0.94

    def _synth_infinite_scroll(self, lang, name, entity, facts):
        return (f'<div class="infinite-scroll" id="{name}-scroll">\n'
                f'  <div id="{name}-list">\n'
                f'    <div class="infinite-scroll__item">Élément 1</div><div class="infinite-scroll__item">Élément 2</div>\n'
                f'    <div class="infinite-scroll__item">Élément 3</div><div class="infinite-scroll__item">Élément 4</div>\n'
                f'    <div class="infinite-scroll__item">Élément 5</div>\n'
                f'  </div>\n'
                f'  <div class="infinite-scroll__loader" id="{name}-loader"><div class="spinner"></div><p>Chargement...</p></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.infinite-scroll {{ max-height:350px; overflow-y:auto; }}\n'
                f'.infinite-scroll__item {{ padding:16px; border-bottom:1px solid var(--color-border); }} .infinite-scroll__item:hover {{ background:var(--color-bg-alt); }}\n'
                f'.infinite-scroll__loader {{ text-align:center; padding:20px; display:none; }} .infinite-scroll__loader.visible {{ display:block; }}\n'
                f'</style>\n'
                f'<script>(function(){{const c=document.getElementById("{name}-scroll");if(!c)return;let count=5;const list=document.getElementById("{name}-list");const loader=document.getElementById("{name}-loader");c.addEventListener("scroll",()=>{{if(c.scrollTop+c.clientHeight>=c.scrollHeight-50&&!loader.classList.contains("visible")){{loader.classList.add("visible");setTimeout(()=>{{for(let i=0;i<5;i++){{const d=document.createElement("div");d.className="infinite-scroll__item";d.textContent="Élément "+(++count);list.appendChild(d)}}loader.classList.remove("visible")}},800)}}}})}})();</script>'), 0.92

    # ════════════════ APPS COMPLÈTES ════════════════

    def _synth_chat_app(self, lang, name, entity, facts):
        return (f'<div class="chat-app" id="{name}">\n'
                f'  <header class="chat-app__header"><div class="chat-app__avatar">🤖</div>\n'
                f'    <div><strong>KA Assistant</strong><span style="font-size:.7rem;color:var(--color-success);margin-left:8px">● En ligne</span></div></header>\n'
                f'  <div class="chat-app__messages" id="{name}-msgs">\n'
                f'    <div class="msg msg--them"><span>Bonjour ! Comment puis-je vous aider ?</span></div>\n'
                f'    <div class="msg msg--me"><span>Salut, raconte une blague</span></div>\n'
                f'    <div class="msg msg--them"><span>Pourquoi les développeurs détestent la nature ? Trop de bugs ! 🐛</span></div>\n'
                f'  </div>\n'
                f'  <div class="chat-app__typing" id="{name}-typing" hidden>🤖 tape...</div>\n'
                f'  <div class="chat-app__input-bar">\n'
                f'    <button onclick="insertEmoji(\'{name}\')">😀</button>\n'
                f'    <input type="text" id="{name}-input" placeholder="Écrivez un message..." onkeydown="if(event.key===\'Enter\')sendMsg(\'{name}\')">\n'
                f'    <button style="background:var(--color-primary);color:#fff" onclick="sendMsg(\'{name}\')">➤</button>\n'
                f'  </div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.chat-app {{ display:flex; flex-direction:column; height:500px; max-width:400px; border:1px solid var(--color-border); border-radius:var(--radius-lg); overflow:hidden; background:var(--color-bg); }}\n'
                f'.chat-app__header {{ display:flex; align-items:center; gap:10px; padding:12px 16px; background:var(--color-bg-alt); border-bottom:1px solid var(--color-border); }}\n'
                f'.chat-app__avatar {{ width:36px; height:36px; border-radius:50%; background:var(--gradient-primary); display:flex; align-items:center; justify-content:center; }}\n'
                f'.chat-app__messages {{ flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:8px; }}\n'
                f'.msg {{ max-width:75%; padding:10px 14px; border-radius:16px; font-size:.9rem; animation:msgIn .2s ease-out; }}\n'
                f'@keyframes msgIn {{ from {{ opacity:0; transform:translateY(8px); }} }}\n'
                f'.msg--them {{ align-self:flex-start; background:var(--color-bg-alt); border-bottom-left-radius:4px; }}\n'
                f'.msg--me {{ align-self:flex-end; background:var(--color-primary); color:#fff; border-bottom-right-radius:4px; }}\n'
                f'.chat-app__typing {{ padding:4px 16px; font-size:.75rem; color:var(--color-text-muted); animation:blink 1s infinite; }}\n'
                f'@keyframes blink {{ 50% {{ opacity:.5; }} }}\n'
                f'.chat-app__input-bar {{ display:flex; align-items:center; gap:8px; padding:10px; border-top:1px solid var(--color-border); background:var(--color-bg-alt); }}\n'
                f'.chat-app__input-bar input {{ flex:1; padding:10px 14px; border:1px solid var(--color-border); border-radius:9999px; background:var(--color-bg); color:var(--color-text); outline:none; }}\n'
                f'.chat-app__input-bar button {{ width:38px; height:38px; border:none; border-radius:50%; cursor:pointer; background:var(--color-bg); }}\n'
                f'</style>\n'
                f'<script>\n'
                f'const replies=["Intéressant !","Je comprends.","D\'accord, continuez.","Excellente question !","Voici mon avis 👇"];\n'
                f'function sendMsg(id){{const i=document.getElementById(id+"-input");const m=document.getElementById(id+"-msgs");if(!i.value.trim())return;m.innerHTML+=`<div class="msg msg--me"><span>${{i.value}}</span></div>`;i.value="";const t=document.getElementById(id+"-typing");t.hidden=false;setTimeout(()=>{{t.hidden=true;m.innerHTML+=`<div class="msg msg--them"><span>${{replies[Math.floor(Math.random()*replies.length)]}}</span></div>`;m.scrollTop=m.scrollHeight}},1200)}}\n'
                f'function insertEmoji(id){{const i=document.getElementById(id+"-input");i.value+="😀 ";i.focus()}}\n'
                f'</script>'), 0.88

    def _synth_kanban(self, lang, name, entity, facts):
        return (f'<div class="kanban">\n'
                f'  <div class="kanban__col"><h3 class="kanban__col-title">📋 À faire</h3>\n'
                f'    <div class="kanban__cards" ondrop="dropCard(event)" ondragover="event.preventDefault()">\n'
                f'      <div class="kanban__card" draggable="true" ondragstart="dragCard(event)">Configurer le serveur</div>\n'
                f'      <div class="kanban__card" draggable="true" ondragstart="dragCard(event)">Designer la maquette</div>\n'
                f'    </div></div>\n'
                f'  <div class="kanban__col"><h3 class="kanban__col-title">🚧 En cours</h3>\n'
                f'    <div class="kanban__cards" ondrop="dropCard(event)" ondragover="event.preventDefault()">\n'
                f'      <div class="kanban__card" draggable="true" ondragstart="dragCard(event)">Créer l\'API REST</div>\n'
                f'    </div></div>\n'
                f'  <div class="kanban__col"><h3 class="kanban__col-title">✅ Terminé</h3>\n'
                f'    <div class="kanban__cards" ondrop="dropCard(event)" ondragover="event.preventDefault()">\n'
                f'      <div class="kanban__card" draggable="true" ondragstart="dragCard(event)">Setup du projet</div>\n'
                f'    </div></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.kanban {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }}\n'
                f'.kanban__col {{ background:var(--color-bg-alt); border-radius:var(--radius-lg); padding:12px; min-height:200px; }}\n'
                f'.kanban__col-title {{ font-size:.9rem; font-weight:700; margin-bottom:12px; }}\n'
                f'.kanban__cards {{ min-height:120px; display:flex; flex-direction:column; gap:8px; }}\n'
                f'.kanban__card {{ padding:12px 14px; background:var(--color-bg); border:1px solid var(--color-border); border-radius:var(--radius-md); cursor:grab; font-size:.85rem; transition:all .15s; }}\n'
                f'.kanban__card:hover {{ border-color:var(--color-primary); }} .kanban__card.dragging {{ opacity:.5; }}\n'
                f'</style>\n'
                f'<script>function dragCard(e){{e.dataTransfer.setData("text/plain","card");e.target.classList.add("dragging")}}function dropCard(e){{e.preventDefault();const card=document.querySelector(".kanban__card.dragging");if(card){{e.currentTarget.appendChild(card);card.classList.remove("dragging")}}}}</script>'), 0.88

    def _synth_weather_app(self, lang, name, entity, facts):
        return (f'<div class="weather-app" id="{name}">\n'
                f'  <div class="weather-app__search">\n'
                f'    <input type="text" id="{name}-city" placeholder="🔍 Ville..." value="Paris" onkeydown="if(event.key===\'Enter\')uw(\'{name}\')">\n'
                f'    <button class="btn btn-primary btn-sm" onclick="uw(\'{name}\')">Voir</button>\n'
                f'  </div>\n'
                f'  <div class="weather-app__current">\n'
                f'    <div class="weather-app__icon" id="{name}-icon">☀️</div>\n'
                f'    <div class="weather-app__temp" id="{name}-temp">22°</div>\n'
                f'    <div class="weather-app__desc" id="{name}-desc">Ensoleillé</div>\n'
                f'    <div class="weather-app__loc" id="{name}-loc">Paris, France</div>\n'
                f'  </div>\n'
                f'  <div class="weather-app__forecast" id="{name}-forecast"></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.weather-app {{ max-width:400px; background:var(--gradient-subtle); border-radius:var(--radius-lg); padding:32px; margin:0 auto; }}\n'
                f'.weather-app__search {{ display:flex; gap:8px; margin-bottom:32px; }}\n'
                f'.weather-app__search input {{ flex:1; padding:10px 16px; border:1px solid var(--color-border); border-radius:9999px; background:var(--color-bg); color:var(--color-text); outline:none; }}\n'
                f'.weather-app__current {{ text-align:center; margin-bottom:32px; }}\n'
                f'.weather-app__icon {{ font-size:4rem; animation:floatIcon 3s ease-in-out infinite; }}\n'
                f'@keyframes floatIcon {{ 50% {{ transform:translateY(-8px); }} }}\n'
                f'.weather-app__temp {{ font-size:3.5rem; font-weight:800; color:var(--color-primary); line-height:1; }}\n'
                f'.weather-app__desc {{ color:var(--color-text-muted); font-size:1.1rem; }} .weather-app__loc {{ font-size:.85rem; color:var(--color-text-muted); }}\n'
                f'.weather-app__forecast {{ display:grid; grid-template-columns:repeat(5,1fr); gap:8px; }}\n'
                f'.forecast-card {{ text-align:center; padding:12px 4px; background:var(--color-bg); border-radius:var(--radius-md); font-size:.75rem; }}\n'
                f'.forecast-card__icon {{ font-size:1.5rem; }} .forecast-card__temp {{ color:var(--color-primary); font-weight:700; }}\n'
                f'</style>\n'
                f'<script>\n'
                f'var wd={{}};wd["Paris"]={{t:22,d:"Ensoleillé",i:"☀️",f:[[18,"🌧️"],[20,"⛅"],[23,"☀️"],[21,"⛅"],[19,"🌧️"]]}};wd["Londres"]={{t:15,d:"Nuageux",i:"☁️",f:[[12,"🌧️"],[14,"⛅"],[15,"☁️"],[13,"🌧️"],[16,"⛅"]]}};wd["Tokyo"]={{t:28,d:"Dégagé",i:"☀️",f:[[26,"☀️"],[28,"☀️"],[30,"☀️"],[27,"⛅"],[25,"🌧️"]]}};\n'
                f'var dn=["Lun","Mar","Mer","Jeu","Ven"];\n'
                f'function uw(id){{var c=document.getElementById(id+"-city").value;var d=wd[c]||wd["Paris"];document.getElementById(id+"-icon").textContent=d.i;document.getElementById(id+"-temp").textContent=d.t+"°";document.getElementById(id+"-desc").textContent=d.d;document.getElementById(id+"-loc").textContent=c;var fc=document.getElementById(id+"-forecast");var h="";for(var j=0;j<5;j++){{h+="<div class=\\"forecast-card\\"><div>"+dn[j]+"</div><div class=\\"forecast-card__icon\\">"+d.f[j][1]+"</div><div class=\\"forecast-card__temp\\">"+d.f[j][0]+"°</div></div>"}}fc.innerHTML=h}}\n'
                f'uw("{name}");\n'
                f'</script>'), 0.88

    def _synth_music_player(self, lang, name, entity, facts):
        return (f'<div class="music-player">\n'
                f'  <div class="music-player__main">\n'
                f'    <div class="music-player__cover">🎵</div>\n'
                f'    <div class="music-player__info"><strong>Midnight Waves</strong><span style="color:var(--color-text-muted);font-size:.85rem">Harmonic Collective</span></div>\n'
                f'  </div>\n'
                f'  <div class="music-player__progress"><span style="font-size:var(--text-small)">0:00</span>\n'
                f'    <div class="music-player__bar"><div class="music-player__fill" id="mp-fill"></div></div>\n'
                f'    <span style="font-size:var(--text-small)">3:24</span></div>\n'
                f'  <div class="music-player__controls">\n'
                f'    <button class="play-btn" id="mp-play" onclick="tp()">▶</button>\n'
                f'    <button onclick="nt()">⏭</button></div>\n'
                f'  <ul class="music-player__playlist" id="mp-pl">\n'
                f'    <li class="active" onclick="pt(0)"><span>🎵 Midnight Waves</span><span>3:24</span></li>\n'
                f'    <li onclick="pt(1)"><span>🎶 Golden Ratio</span><span>4:12</span></li>\n'
                f'    <li onclick="pt(2)"><span>🎵 Fibonacci Dreams</span><span>2:58</span></li>\n'
                f'  </ul>\n'
                f'</div>\n'
                f'<style>\n'
                f'.music-player {{ max-width:420px; border:1px solid var(--color-border); border-radius:var(--radius-lg); overflow:hidden; background:var(--color-bg-alt); }}\n'
                f'.music-player__main {{ display:flex; gap:16px; padding:20px; }}\n'
                f'.music-player__cover {{ width:80px; height:80px; border-radius:var(--radius-md); background:var(--gradient-primary); display:flex; align-items:center; justify-content:center; font-size:2.5rem; flex-shrink:0; }}\n'
                f'.music-player__info {{ display:flex; flex-direction:column; justify-content:center; }}\n'
                f'.music-player__progress {{ display:flex; align-items:center; gap:8px; padding:0 20px 12px; }}\n'
                f'.music-player__bar {{ flex:1; height:6px; background:var(--color-muted); border-radius:3px; cursor:pointer; overflow:hidden; }}\n'
                f'.music-player__fill {{ height:100%; width:0; background:var(--gradient-primary); transition:width .3s linear; }}\n'
                f'.music-player__controls {{ display:flex; justify-content:center; gap:20px; padding:8px; }}\n'
                f'.music-player__controls button {{ width:40px; height:40px; border-radius:50%; border:none; background:var(--color-bg); cursor:pointer; }} .play-btn {{ width:52px!important; height:52px!important; background:var(--color-primary)!important; color:#fff; }}\n'
                f'.music-player__playlist {{ list-style:none; border-top:1px solid var(--color-border); }}\n'
                f'.music-player__playlist li {{ display:flex; justify-content:space-between; padding:10px 20px; cursor:pointer; font-size:.85rem; }} .music-player__playlist li.active {{ background:hsla(262,60%,55%,.1); color:var(--color-primary); font-weight:600; }}\n'
                f'</style>\n'
                f'<script>\n'
                f'var tracks=[["Midnight Waves","3:24"],["Golden Ratio","4:12"],["Fibonacci Dreams","2:58"]];var curIdx=0,isPlaying=false,timer=null;\n'
                f'function pt(idx){{curIdx=idx;document.querySelectorAll("#mp-pl li").forEach((li,i)=>li.className=i===idx?"active":"");if(!isPlaying)tp()}}\n'
                f'function tp(){{isPlaying=!isPlaying;document.getElementById("mp-play").textContent=isPlaying?"⏸":"▶";var fill=document.getElementById("mp-fill");var pct=0;if(isPlaying){{timer=setInterval(()=>{{pct+=0.5;if(pct>=100){{nt();return}}fill.style.width=pct+"%"}},150)}}else{{clearInterval(timer)}}}}\n'
                f'function nt(){{pt((curIdx+1)%tracks.length)}}\n'
                f'</script>'), 0.88

    def _synth_tetris(self, lang, name, entity, facts):
        return (f'<canvas id="tetris-canvas" width="300" height="600" style="border:2px solid var(--color-border);border-radius:var(--radius-md);display:block;margin:0 auto;background:#0d0d1a"></canvas>\n'
                f'<div style="text-align:center;margin-top:8px"><strong id="tetris-score" style="color:var(--color-primary)">Score: 0</strong></div>\n'
                f'<div style="text-align:center;font-size:.8rem;color:var(--color-text-muted)">← → déplacer | ↑ pivoter | ↓ accélérer</div>\n'
                f'<button class="btn btn-primary btn-sm" onclick="startTetris()" style="display:block;margin:8px auto">🔄 Nouvelle partie</button>\n'
                f'<script>\n'
                f'function startTetris(){{\n'
                f'  var cv=document.getElementById("tetris-canvas");if(!cv)return;var ctx=cv.getContext("2d");var W=10,H=20,S=30;\n'
                f'  var pieces=[[[1,1,1,1]],[[1,1],[1,1]],[[0,1,0],[1,1,1]],[[1,0,0],[1,1,1]],[[0,0,1],[1,1,1]],[[0,1,1],[1,1,0]],[[1,1,0],[0,1,1]]];\n'
                f'  var colors=["#6366f1","#f97316","#10b981","#3b82f6","#ec4899","#f59e0b","#8b5cf6"];\n'
                f'  var board=[];for(var r=0;r<H;r++){{board.push([]);for(var c2=0;c2<W;c2++)board[r].push(0)}}\n'
                f'  var cur,px,py,color,score=0,loop;\n'
                f'  function newPiece(){{var i=Math.floor(Math.random()*7);color=colors[i];return JSON.parse(JSON.stringify(pieces[i]))}}\n'
                f'  function valid(dx,dy,piece){{piece=piece||cur;for(var r=0;r<piece.length;r++)for(var c=0;c<piece[r].length;c++){{if(piece[r][c]){{var nx=px+c+dx,ny=py+r+dy;if(nx<0||nx>=W||ny>=H)return false;if(ny>=0&&board[ny][nx])return false}}}}return true}}\n'
                f'  function merge(){{cur.forEach(function(row,ry){{row.forEach(function(c,cx){{if(c&&py+ry>=0)board[py+ry][px+cx]=color}})}})}}\n'
                f'  function clearLines(){{for(var r=H-1;r>=0;r--){{if(board[r].every(function(x){{return x}})){{board.splice(r,1);board.unshift([]);for(var c=0;c<W;c++)board[0].push(0);score+=100;document.getElementById("tetris-score").textContent="Score: "+score;r++}}}}}}\n'
                f'  function rotate(){{var p=cur[0].map(function(_,i){{return cur.map(function(r){{return r[i]}})}}).reverse();if(valid(0,0,p))cur=p}}\n'
                f'  function drawBlock(x,y,color){{ctx.fillStyle=color;ctx.fillRect(x*S,y*S,S-1,S-1)}}\n'
                f'  function draw(){{ctx.fillStyle="#0d0d1a";ctx.fillRect(0,0,300,600);for(var r=0;r<H;r++)for(var c=0;c<W;c++)if(board[r][c])drawBlock(c,r,board[r][c]);if(cur)cur.forEach(function(row,ry){{row.forEach(function(c,cx){{if(c)drawBlock(px+cx,py+ry,color)}})}})}}\n'
                f'  function spawn(){{cur=newPiece();px=3;py=0;if(!valid(0,0)){{clearInterval(loop);alert("Game Over! Score: "+score)}}}}\n'
                f'  spawn();\n'
                f'  document.onkeydown=function(e){{if(e.key==="ArrowLeft"&&valid(-1,0))px--;if(e.key==="ArrowRight"&&valid(1,0))px++;if(e.key==="ArrowDown"&&valid(0,1))py++;if(e.key==="ArrowUp")rotate()}};\n'
                f'  loop=setInterval(function(){{if(valid(0,1))py++;else{{merge();clearLines();spawn()}}draw()}},400);\n'
                f'}}\n'
                f'startTetris();\n'
                f'</script>'), 0.85

    # ════════════════ FETCH + STATE ════════════════

    def _synth_fetch_error(self, lang, name, entity, facts):
        return (f'<div class="data-loader" id="{name}-loader">\n'
                f'  <div id="{name}-loading"><div class="spinner"></div><p>Chargement des données...</p></div>\n'
                f'  <div id="{name}-error" style="display:none"><p>⚠️ Une erreur est survenue.</p>\n'
                f'    <button class="btn btn-outline btn-sm" onclick="location.reload()">Réessayer</button></div>\n'
                f'  <div id="{name}-results" style="display:none"></div>\n'
                f'</div>\n'
                f'<style>\n'
                f'.data-loader {{ text-align:center; padding:52px; }}\n'
                f'.spinner {{ width:40px; height:40px; margin:0 auto 20px; border:3px solid var(--color-border); border-top-color:var(--color-primary); border-radius:50%; animation:spin .8s linear infinite; }}\n'
                f'@keyframes spin {{ to {{ transform:rotate(360deg); }} }}\n'
                f'</style>\n'
                f'<script>\n'
                f'(async function(){{const load=document.getElementById("{name}-loading");const err=document.getElementById("{name}-error");const res=document.getElementById("{name}-results");try{{const r=await fetch("/api/data");if(!r.ok)throw new Error("HTTP "+r.status);const data=await r.json();load.style.display="none";res.style.display="block";res.innerHTML="<pre>"+JSON.stringify(data,null,2)+"</pre>"}}catch(e){{load.style.display="none";err.style.display="block";console.error(e)}}}})();\n'
                f'</script>'), 0.93


# ═══════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════

@dataclass
class GeneratedCode:
    code: str
    language: str
    intent: CodeIntent
    confidence: float
    facts_used: int = 0
    source: str = "template"


class FrontendGenerator:
    """Générateur frontend unifié (PatternDetector + WaveSynthesizer)."""

    def __init__(self):
        self.detector = PatternDetector()
        self.synthesizer = WaveSynthesizer()

    def generate(self, question: str) -> GeneratedCode:
        intent = self.detector.detect(question)
        code, confidence = self.synthesizer.synthesize(intent, [])
        return GeneratedCode(code=code, language=intent.language, intent=intent,
                             confidence=confidence, source="template")

    def generate_variant(self, question: str, variant: str) -> GeneratedCode:
        intent = self.detector.detect(question)
        op = intent.operation
        method = getattr(self.synthesizer, f'_synth_{op}', None)
        if method:
            try:
                code, conf = method(intent.language, op, intent.entity, [], variant=variant)
                return GeneratedCode(code=code, language=intent.language, intent=intent,
                                     confidence=conf, source=f"template/{variant}")
            except TypeError:
                pass
        return self.generate(question)

    def template_count(self) -> int:
        return sum(1 for m in dir(self.synthesizer) if m.startswith('_synth_'))


if __name__ == '__main__':
    gen = FrontendGenerator()
    print(f"Templates disponibles: {gen.template_count()}\n")

    tests = [
        'crée une landing page pour un café',
        'génère un dashboard avec graphiques',
        'crée une carte avec image et bouton',
        'fais un chat app avec messages',
        'génère un lecteur musique',
        'crée un thème sombre',
        'fais un jeux snake',
    ]
    for t in tests:
        r = gen.generate(t)
        print(f"  {'✅' if r.confidence > 0.7 else '❌'} {t[:45]:47s} → op={r.intent.operation:15s} conf={r.confidence:.2f} ({len(r.code)} chars)")

    # Test variantes de card
    print("\nVariantes card:")
    for v in ['default', 'horizontal', 'overlay', 'minimal', 'featured']:
        r = gen.generate_variant('crée une carte', v)
        has_v = f'data-variant="{v}"' in r.code
        print(f"  {v:12s} → data-variant={has_v} ({len(r.code)} chars)")
