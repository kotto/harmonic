"""
🎨 CSS Harmony — Génération de CSS harmonique par les ondes (reconstruit, autonome)
=====================================================================================
Moteur de génération CSS utilisant les principes ondulatoires :
φ (nombre d'or), interférence des ondes, Fibonacci.

Usage:
    from css_harmony import HarmonicCSS
    hcss = HarmonicCSS()
    css = hcss.generate(seed="mon-site", mood="elegant", mode="dark")
"""

import math, hashlib, colorsys
from typing import Dict, List, Tuple, Optional

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
TAU = 2.0 * math.pi


def phi_hash(text: str) -> float:
    """Hash déterministe φ-normalisé → float ∈ [0, 1)."""
    h = hashlib.sha256(text.encode()).digest()
    return int.from_bytes(h[:4], 'big') / 2**32


class HarmonicTypeScale:
    """Échelle typographique basée sur φ : base × φ^n."""

    SCALE_NAMES = {
        -2: '--text-caption', -1: '--text-small', 0: '--text-body',
        1: '--text-h4', 2: '--text-h3', 3: '--text-h2', 4: '--text-h1', 5: '--text-hero',
    }

    def __init__(self, base_size: float = 1.0, base_unit: str = 'rem'):
        self.base_size = base_size
        self.base_unit = base_unit

    def scale(self, steps: int = 6) -> Dict[int, float]:
        return {step: round(self.base_size * (PHI ** step), 4) for step in range(-2, steps)}

    def to_css(self, steps: int = 6) -> str:
        lines = ['  /* ═══ Échelle Typographique Harmonique (φ) ═══ */']
        for step in sorted(self.scale(steps).keys()):
            name = self.SCALE_NAMES.get(step, f'--text-step-{step}')
            size = self.scale(steps)[step]
            lh = round(PHI_INV + 0.05, 2) if step >= 0 else round(PHI_INV + 0.1, 2)
            lines.append(f'  {name}: {size}{self.base_unit};')
            lines.append(f'  {name}-lh: {lh};')
        return '\n'.join(lines)


class HarmonicSpacing:
    """Système d'espacement basé sur la suite de Fibonacci × base."""

    def __init__(self, base: float = 4.0, unit: str = 'px'):
        self.base = base
        self.unit = unit
        self._fib = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]

    def space(self, level: int) -> float:
        return round(self._fib[min(level + 3, len(self._fib) - 1)] * self.base, 2)

    def to_css(self, levels: int = 9) -> str:
        names = ['micro', 'tiny', 'small', 'medium', 'large', 'xl', '2xl', '3xl', '4xl']
        lines = ['  /* ═══ Système d\'Espacement Harmonique (Fibonacci) ═══ */']
        for i in range(levels):
            name = names[i] if i < len(names) else f'level-{i}'
            lines.append(f'  --space-{name}: {self.space(i)}{self.unit};')
        lines.append('')
        lines.append('  --container-sm: 300px;')
        lines.append('  --container-md: 480px;')
        lines.append(f'  --container-lg: {round(480 * PHI)}px;')
        lines.append(f'  --container-xl: {round(480 * PHI * PHI)}px;')
        return '\n'.join(lines)


class WaveColorPalette:
    """Palette de couleurs par interférence d'ondes (complémentaire 180°, triadique 120°)."""

    MOOD_ADJUSTMENTS = {
        'minimal':   {'sat_shift': -0.10, 'light_shift': +0.05},
        'elegant':   {'sat_shift': -0.05, 'light_shift': -0.02},
        'vibrant':   {'sat_shift': +0.15, 'light_shift': -0.05},
        'corporate': {'sat_shift': -0.15, 'light_shift': +0.00},
        'warm':      {'hue_shift': +15, 'sat_shift': +0.05},
        'cool':      {'hue_shift': +210, 'sat_shift': -0.05},
        'dark':      {'sat_shift': -0.10, 'light_shift': -0.20},
        'nature':    {'hue_shift': +90, 'sat_shift': -0.05},
    }

    def seed_to_hue(self, seed: str) -> float:
        h = hashlib.sha256(seed.encode()).digest()
        hue_seed = int.from_bytes(h[:4], 'big')
        return round((hue_seed * PHI * 360 / (2**32)) % 360, 1)

    def _harmonic_hsl(self, base_hue, phase_shift, mood='elegant'):
        hue = (base_hue + phase_shift) % 360
        sat = 0.55 + 0.15 * math.sin(phase_shift * TAU / 360)
        light = 0.50 + 0.12 * math.cos((phase_shift - 60) * TAU / 360)
        adj = self.MOOD_ADJUSTMENTS.get(mood, {})
        sat += adj.get('sat_shift', 0)
        light += adj.get('light_shift', 0)
        hue = (hue + adj.get('hue_shift', 0)) % 360
        return round(hue, 1), round(max(0.05, min(1.0, sat)), 3), round(max(0.05, min(0.95, light)), 3)

    def _css(self, h, s, l):
        return f'hsl({h}, {round(s*100)}%, {round(l*100)}%)'

    def generate(self, seed: str = 'default', mood: str = 'elegant') -> Dict[str, str]:
        base = self.seed_to_hue(seed)
        is_dark = mood == 'dark'
        p = {}

        h, s, l = self._harmonic_hsl(base, 0, mood)
        p['primary'] = self._css(h, s, l)
        p['primary-hover'] = self._css(h, min(1.0, s + 0.1), max(0.1, l - 0.08))
        p['primary-active'] = self._css(h, min(1.0, s + 0.05), max(0.05, l - 0.15))

        h2, s2, l2 = self._harmonic_hsl(base, 180, mood)
        p['secondary'] = self._css(h2, s2, l2)

        h3, s3, l3 = self._harmonic_hsl(base, 120, mood)
        p['accent'] = self._css(h3, s3, l3)

        if is_dark:
            p['bg'] = self._css(base, 0.05, 0.06); p['bg-alt'] = self._css(base, 0.05, 0.10)
            p['text'] = self._css(base, 0.05, 0.92); p['text-muted'] = self._css(base, 0.03, 0.65)
        else:
            p['bg'] = self._css(base, 0.05, 0.97); p['bg-alt'] = self._css(base, 0.05, 0.93)
            p['text'] = self._css(base, 0.08, 0.12); p['text-muted'] = self._css(base, 0.05, 0.45)

        p['muted'] = self._css(base, 0.08, 0.88 if not is_dark else 0.15)
        p['border'] = self._css(base, 0.10, 0.82 if not is_dark else 0.22)
        p['success'] = self._css(145, 0.50, 0.45)
        p['warning'] = self._css(38, 0.92, 0.50)
        p['error'] = self._css(5, 0.72, 0.52)
        p['info'] = self._css(207, 0.70, 0.52)
        p['gradient'] = f'linear-gradient(135deg, {p["primary"]}, {p["accent"]})'
        p['gradient-subtle'] = f'linear-gradient(135deg, {self._css(base, 0.15, 0.95)}, {self._css((base+30)%360, 0.10, 0.90)})'
        return p

    def to_css(self, seed: str = 'default', mood: str = 'elegant') -> str:
        p = self.generate(seed, mood)
        base = self.seed_to_hue(seed)
        lines = ['  /* ═══ Palette de Couleurs Harmonique (Interférence d\'Ondes) ═══ */',
                 f'  /* Seed: "{seed}" | Mood: {mood} | Teinte: {base}° */', '']
        for var, key in [
            ('--color-primary', 'primary'), ('--color-primary-hover', 'primary-hover'),
            ('--color-primary-active', 'primary-active'), ('--color-secondary', 'secondary'),
            ('--color-accent', 'accent'), ('--color-bg', 'bg'), ('--color-bg-alt', 'bg-alt'),
            ('--color-text', 'text'), ('--color-text-muted', 'text-muted'),
            ('--color-muted', 'muted'), ('--color-border', 'border'),
            ('--color-success', 'success'), ('--color-warning', 'warning'),
            ('--color-error', 'error'), ('--color-info', 'info')]:
            lines.append(f'  {var}: {p[key]};')
        lines.append('')
        lines.append(f'  --gradient-primary: {p["gradient"]};')
        lines.append(f'  --gradient-subtle: {p["gradient-subtle"]};')
        lines.append('')
        lines.append(f'  --shadow-sm: 0 1px 3px hsla({base}, 10%, 10%, 0.08);')
        lines.append(f'  --shadow-md: 0 4px 12px hsla({base}, 15%, 10%, 0.12);')
        lines.append(f'  --shadow-lg: 0 8px 30px hsla({base}, 20%, 10%, 0.18);')
        lines.append(f'  --shadow-xl: 0 16px 48px hsla({base}, 25%, 10%, 0.25);')
        lines.append('')
        lines.append(f'  --radius-sm: {round(4 * PHI_INV, 1)}px;')
        lines.append(f'  --radius-md: {round(4 * PHI_INV * PHI, 1)}px;')
        lines.append(f'  --radius-lg: {round(4 * PHI, 1)}px;')
        lines.append(f'  --radius-xl: {round(4 * PHI * PHI, 1)}px;')
        lines.append('  --radius-full: 9999px;')
        return '\n'.join(lines)

    def dark_theme_css(self, seed: str = 'default', mood: str = 'dark') -> str:
        p = self.generate(seed, 'dark')
        return (f'  /* ═══ Thème Sombre Harmonique ═══ */\n'
                f'  @media (prefers-color-scheme: dark) {{\n    :root {{\n'
                f'      --color-bg: {p["bg"]};\n      --color-bg-alt: {p["bg-alt"]};\n'
                f'      --color-text: {p["text"]};\n      --color-text-muted: {p["text-muted"]};\n'
                f'      --color-muted: {p["muted"]};\n      --color-border: {p["border"]};\n'
                f'    }}\n  }}\n'
                f'  [data-theme="dark"] {{\n'
                f'    --color-bg: {p["bg"]};\n    --color-bg-alt: {p["bg-alt"]};\n'
                f'    --color-text: {p["text"]};\n    --color-text-muted: {p["text-muted"]};\n'
                f'    --color-muted: {p["muted"]};\n    --color-border: {p["border"]};\n'
                f'  }}')


class HarmonicGrid:
    """Grilles responsive aux ratios φ (61.8/38.2) et breakpoints ×φ."""

    BREAKPOINTS = {'sm': 480, 'md': round(480 * PHI), 'lg': round(480 * PHI * PHI), 'xl': round(480 * PHI ** 3)}

    def to_css(self) -> str:
        return (f'  /* ═══ Grille Responsive (φ) ═══ */\n'
                f'  .container {{ width: 100%; max-width: {self.BREAKPOINTS["lg"]}px; margin-inline: auto; padding-inline: 20px; }}\n'
                f'  .grid-2 {{ display: grid; grid-template-columns: 62% 38%; gap: 32px; }}\n'
                f'  .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}\n'
                f'  .grid-auto {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}\n'
                f'  .flex {{ display: flex; }} .flex-col {{ display: flex; flex-direction: column; }}\n'
                f'  .flex-center {{ display: flex; align-items: center; justify-content: center; }}\n'
                f'  .flex-between {{ display: flex; align-items: center; justify-content: space-between; }}\n'
                f'  .flex-gap {{ gap: 20px; }} .flex-gap-sm {{ gap: 12px; }}\n'
                f'  @media (max-width: 479px) {{ .grid-2, .grid-3 {{ grid-template-columns: 1fr; }} }}\n')


class WaveAnimation:
    """Animations sinusoïdales avec durées φ-espacées."""

    def to_css(self) -> str:
        return ('  /* ═══ Animations Harmoniques (GPU) ═══ */\n'
                '  @keyframes fadeIn { from { opacity: 0; transform: translateY(10px) translateZ(0); } to { opacity: 1; transform: translateY(0) translateZ(0); } }\n'
                '  @keyframes slideUp { from { opacity: 0; transform: translateY(30px) translateZ(0); } to { opacity: 1; transform: translateY(0) translateZ(0); } }\n'
                '  @keyframes scaleIn { from { opacity: 0; transform: scale(0.9) translateZ(0); } to { opacity: 1; transform: scale(1) translateZ(0); } }\n'
                '  @keyframes wavePulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }\n'
                '  @keyframes spin { to { transform: rotate(360deg); } }\n'
                '  .animate-fade-in, .animate-slide-up, .animate-scale-in, .animate-pulse {\n'
                '    will-change: transform, opacity; backface-visibility: hidden; transform: translateZ(0); }\n'
                '  .animate-fade-in { animation: fadeIn 0.618s ease-out both; }\n'
                '  .animate-slide-up { animation: slideUp 1s ease-out both; }\n'
                '  .animate-scale-in { animation: scaleIn 0.618s ease-out both; }\n'
                '  .animate-pulse { animation: wavePulse 2.618s ease-in-out infinite; }\n'
                '  .delay-1 { animation-delay: 0.15s; } .delay-2 { animation-delay: 0.3s; } .delay-3 { animation-delay: 0.45s; }\n'
                '  @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }')


class HarmonicCSS:
    """Orchestrateur : génère le CSS harmonique complet."""

    def __init__(self):
        self.typography = HarmonicTypeScale()
        self.spacing = HarmonicSpacing()
        self.colors = WaveColorPalette()
        self.grid = HarmonicGrid()
        self.animation = WaveAnimation()

    def generate(self, seed: str = 'default', mood: str = 'elegant',
                 mode: str = 'light', include_dark: bool = True) -> str:
        if mood == 'dark':
            mode = 'dark'
        sections = [
            '/* ═══════════════════════════════════════════ */',
            '/* RESET HARMONIQUE                           */',
            '/* ═══════════════════════════════════════════ */',
            '*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}',
            'html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}',
            "body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;background-color:var(--color-bg);color:var(--color-text);min-height:100vh;-webkit-font-smoothing:antialiased}",
            'img,picture,video,canvas,svg{display:block;max-width:100%}',
            'input,button,textarea,select{font:inherit;color:inherit}',
            'a{color:var(--color-primary);text-decoration:none}',
            'ul,ol{list-style:none}',
            ':focus-visible{outline:2px solid var(--color-primary);outline-offset:2px}',
            '',
            ':root {',
            self.colors.to_css(seed, mood),
            '',
            self.spacing.to_css(),
            '',
            self.typography.to_css(),
            '}',
        ]
        if include_dark:
            sections += ['', self.colors.dark_theme_css(seed, mood)]
        sections += ['', self.grid.to_css(), '', self.animation.to_css()]
        return '\n'.join(sections)

    def palette_only(self, seed: str = 'default', mood: str = 'elegant') -> str:
        return ':root {\n' + self.colors.to_css(seed, mood) + '\n}\n'

    def generate_minimal(self, seed: str = 'default') -> str:
        return (':root {\n' + self.colors.to_css(seed, 'minimal') + '\n}\n' + self.grid.to_css())


def get_harmonic_design_tokens(seed: str = 'default', mood: str = 'elegant') -> Dict[str, str]:
    """Tokens de design harmoniques pour les templates."""
    hcss = HarmonicCSS()
    colors = hcss.colors.generate(seed, mood)
    spacing = HarmonicSpacing()
    return {
        'primary': 'var(--color-primary)', 'secondary': 'var(--color-secondary)',
        'accent': 'var(--color-accent)', 'bg': 'var(--color-bg)', 'bg_alt': 'var(--color-bg-alt)',
        'text': 'var(--color-text)', 'text_muted': 'var(--color-text-muted)',
        'border': 'var(--color-border)', 'success': 'var(--color-success)',
        'error': 'var(--color-error)', 'warning': 'var(--color-warning)',
        'gradient': 'var(--gradient-primary)',
        'space_sm': f'{spacing.space(2)}px', 'space_md': f'{spacing.space(3)}px',
        'space_lg': f'{spacing.space(4)}px', 'space_xl': f'{spacing.space(5)}px',
        'radius_sm': 'var(--radius-sm)', 'radius_md': 'var(--radius-md)',
        'radius_lg': 'var(--radius-lg)', 'shadow_sm': 'var(--shadow-sm)',
        'shadow_md': 'var(--shadow-md)', 'shadow_lg': 'var(--shadow-lg)',
        'font_body': 'var(--text-body)', 'font_h1': 'var(--text-h1)',
        'font_h2': 'var(--text-h2)', 'font_h3': 'var(--text-h3)',
    }


if __name__ == '__main__':
    hcss = HarmonicCSS()
    css = hcss.generate(seed='ka-harmonic', mood='elegant', mode='dark')
    print(f"CSS généré: {len(css)} chars")
    lines = css.split('\n')
    print(f"Premières lignes:")
    for l in lines[:20]:
        print(f'  {l}')
    print("\n✅ css_harmony.py reconstruit et fonctionnel")
