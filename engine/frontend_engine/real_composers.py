"""
🔧 Real Composers (reconstruit, autonome)
===========================================
1. HRRHtmlFusion     — fusionne VRAIMENT deux composants en un seul HTML
2. MultiSectionPage  — assemble VRAIMENT une page multi-sections
3. ReferenceAnalyzer — description → plan de page → génération
"""

import re, hashlib
from typing import Dict, List, Tuple, Optional
from code_generator import WaveSynthesizer

synth = WaveSynthesizer()


# ═══════════════════════════════════════════════════════════════════
# 1. HRR HTML FUSION
# ═══════════════════════════════════════════════════════════════════

class HRRHtmlFusion:
    """Fusionne deux composants en un seul HTML cohérent."""

    STRATEGIES = {
        "card+form": "embed_in_body",
        "card+button": "append_to_footer",
        "navbar+search": "insert_in_menu",
        "navbar+button": "append_cta",
        "hero+button": "add_cta",
        "hero+form": "overlay_form",
        "dashboard+table": "embed_in_main",
        "sidebar+nav": "replace_nav",
        "footer+social": "add_social_col",
    }

    def fuse(self, comp_a: str, comp_b: str) -> Tuple[str, float]:
        key = f"{comp_a}+{comp_b}"
        strategy = self.STRATEGIES.get(key, "embed_in_body")

        try:
            html_a, conf_a = self._generate(comp_a)
            html_b, conf_b = self._generate(comp_b)
        except Exception as e:
            return f"<!-- Fusion error: {e} -->", 0.0

        if strategy == "embed_in_body":
            return self._embed_in_body(html_a, html_b), min(conf_a, conf_b) * 0.95
        if strategy == "add_cta":
            return self._add_cta(html_a, html_b), min(conf_a, conf_b)
        if strategy == "overlay_form":
            return self._overlay_form(html_a, html_b), min(conf_a, conf_b) * 0.9
        if strategy == "insert_in_menu":
            return self._insert_in_menu(html_a, html_b), min(conf_a, conf_b)
        return self._embed_in_body(html_a, html_b), min(conf_a, conf_b) * 0.9

    def _generate(self, comp: str) -> Tuple[str, float]:
        method = getattr(synth, f'_synth_{comp}', None)
        if method:
            try:
                return method('html', comp, comp, [])
            except TypeError:
                return method('html', comp, comp, [])
        return f'<div class="{comp}">{comp}</div>', 0.5

    def _embed_in_body(self, html_a: str, html_b: str) -> str:
        inner_b = self._extract_inner(html_b)
        css_b = self._extract_style(html_b)
        css_a = self._extract_style(html_a)
        match = re.search(r'(<div[^>]*__body[^>]*>)', html_a)
        if match:
            pos = match.end()
            fused = html_a[:pos] + '\n' + inner_b + html_a[pos:]
        else:
            fused = html_a.rstrip().rstrip('</article>').rstrip() + '\n' + inner_b + '\n</article>'
        return self._merge_css(fused, css_a, css_b)

    def _add_cta(self, hero_html: str, button_html: str) -> str:
        btn = re.search(r'<button[^>]*>.*?</button>', button_html, re.DOTALL)
        btn_html = btn.group() if btn else '<a href="#" class="btn btn-primary">Action</a>'
        css_b = self._extract_style(button_html)
        css_a = self._extract_style(hero_html)
        match = re.search(r'(<div[^>]*actions[^>]*>)(.*?)(</div>)', hero_html, re.DOTALL)
        if match:
            pos = match.start(3)
            fused = hero_html[:pos] + '\n' + btn_html + '\n' + hero_html[pos:]
        else:
            match2 = re.search(r'(</section>)', hero_html)
            if match2:
                pos = match2.start(1)
                fused = hero_html[:pos] + '\n<div class="hero__actions">' + btn_html + '</div>\n' + hero_html[pos:]
            else:
                fused = hero_html + '\n' + btn_html
        return self._merge_css(fused, css_a, css_b)

    def _overlay_form(self, hero_html: str, form_html: str) -> str:
        inner = self._extract_inner(form_html)
        css_b = self._extract_style(form_html)
        css_a = self._extract_style(hero_html)
        match = re.search(r'(</section>)', hero_html)
        if match:
            pos = match.start(1)
            overlay = f'\n<div class="hero__overlay" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.4)">\n{inner}\n</div>\n'
            fused = hero_html[:pos] + overlay + hero_html[pos:]
        else:
            fused = hero_html + '\n' + inner
        return self._merge_css(fused, css_a, css_b)

    def _insert_in_menu(self, navbar_html: str, search_html: str) -> str:
        si = re.search(r'<input[^>]*>', search_html)
        input_html = si.group() if si else '<input type="search" placeholder="Rechercher...">'
        css_b = self._extract_style(search_html)
        css_a = self._extract_style(navbar_html)
        match = re.search(r'(</ul>)', navbar_html)
        if match:
            pos = match.start(1)
            fused = navbar_html[:pos] + '<li>' + input_html + '</li>\n' + navbar_html[pos:]
        else:
            fused = navbar_html + '\n' + input_html
        return self._merge_css(fused, css_a, css_b)

    def _extract_inner(self, html: str) -> str:
        html = re.sub(r'^<(?:article|section|div|nav|footer|header)\b[^>]*>', '', html, count=1)
        html = re.sub(r'</(?:article|section|div|nav|footer|header)>\s*$', '', html, count=1,
                      flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<style>.*?</style>', '', html, flags=re.DOTALL)
        return html.strip()

    def _extract_style(self, html: str) -> str:
        m = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
        return m.group(1).strip() if m else ''

    def _merge_css(self, html: str, css_a: str, css_b: str) -> str:
        merged = css_a + ('\n\n/* Fused CSS */\n' + css_b if css_b and css_b not in css_a else '')
        if '<style>' in html:
            html = re.sub(r'<style>.*?</style>', f'<style>\n{merged}\n</style>', html,
                          flags=re.DOTALL, count=1)
        else:
            html += f'\n<style>\n{merged}\n</style>'
        return html


# ═══════════════════════════════════════════════════════════════════
# 2. MULTI-SECTION PAGE
# ═══════════════════════════════════════════════════════════════════

class MultiSectionPage:
    """Assemble une page complète à partir de sections réelles."""

    PAGE_TEMPLATES = {
        "landing": ["navbar", "hero", "features", "pricing", "testimonial", "footer"],
        "dashboard": ["navbar", "sidebar", "stat_cards", "table", "footer"],
        "portfolio": ["navbar", "hero", "gallery", "testimonial", "footer"],
        "blog": ["navbar", "blog_cards", "sidebar", "footer"],
        "product": ["navbar", "hero", "card", "testimonial", "pricing", "footer"],
        "contact": ["navbar", "contact_form", "faq", "footer"],
    }

    def assemble(self, page_type: str = "landing", seed: str = "default",
                 custom_sections: List[str] = None) -> Tuple[str, float]:
        sections = custom_sections or self.PAGE_TEMPLATES.get(page_type, self.PAGE_TEMPLATES["landing"])
        section_htmls, confidences, all_css, all_js = [], [], [], []

        for i, st in enumerate(sections):
            try:
                html, conf = self._generate_section(st, seed, i)
                section_htmls.append(f'<!-- ═══ Section {i+1}: {st} ═══ -->\n{html}')
                css = self._extract_style(html)
                if css:
                    all_css.append(f'/* {st} */\n{css}')
                js = self._extract_script(html)
                if js:
                    all_js.append(f'/* {st} */\n{js}')
                confidences.append(conf)
            except Exception as e:
                section_htmls.append(f'<!-- {st}: error {e} -->')

        page = f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_type.title()} Page</title>
<style>
{chr(10).join(all_css)}
</style>
</head>
<body>
{chr(10).join(section_htmls)}
<script>
{chr(10).join(all_js)}
</script>
</body>
</html>'''
        avg = sum(confidences) / len(confidences) if confidences else 0
        return page, avg

    def _generate_section(self, st: str, seed: str, index: int) -> Tuple[str, float]:
        if st == "card":
            variants = ["default", "horizontal", "overlay", "minimal", "featured"]
            h = hashlib.sha256(f"{seed}|{index}".encode()).digest()
            v = variants[int(int.from_bytes(h[:4], 'big') / 2**32 * 1.618 * len(variants)) % len(variants)]
            return synth._synth_card('html', f'card-{index}', 'card', [], variant=v)
        if st == "stat_cards":
            return synth._synth_dashboard('html', 'stats', 'dashboard', [])
        if st == "blog_cards":
            return synth._synth_blog_layout('html', 'blog', 'blog', [])
        method = getattr(synth, f'_synth_{st}', None)
        if method:
            try:
                return method('html', st, st, [])
            except TypeError:
                return method('html', st, st, [])
        return f'<div class="{st}">Section {st}</div>', 0.5

    def _extract_style(self, html: str) -> str:
        m = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
        return m.group(1).strip() if m else ''

    def _extract_script(self, html: str) -> str:
        m = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
        return m.group(1).strip() if m else ''


# ═══════════════════════════════════════════════════════════════════
# 3. REFERENCE ANALYZER
# ═══════════════════════════════════════════════════════════════════

class ReferenceAnalyzer:
    """Description de layout → plan de page → génération."""

    REGION_PATTERNS = {
        "header": [r'en haut', r'header', r'barre (?:de )?nav', r'menu', r'logo'],
        "sidebar_left": [r'sidebar', r'à gauche', r'left\s*panel'],
        "sidebar_right": [r'à droite', r'right\s*panel'],
        "main_content": [r'au centre', r'contenu principal', r'main', r'zone centrale'],
        "footer": [r'en bas', r'footer', r'pied de page'],
    }

    COMPONENT_PATTERNS = {
        "navbar": [r'nav(?:bar|igation)?', r'menu', r'barre.*nav'],
        "hero": [r'hero', r'bannière', r'accroche', r'titre principal', r'grand titre'],
        "card": [r'carte', r'card', r'vignette', r'fiche', r'produit'],
        "form": [r'formulaire', r'form\b', r'champ.*saisie', r'input', r'connexion'],
        "table": [r'tableau', r'table\b', r'ligne.*colonne', r'donnée.*tabul'],
        "chart": [r'graphique', r'chart', r'courbe', r'camembert', r'diagramme'],
        "sidebar": [r'sidebar', r'latéral', r'panneau'],
        "gallery": [r'galerie', r'grille.*image', r'portfolio', r'photos'],
        "pricing": [r'tarif', r'prix', r'pricing', r'forfait'],
        "testimonial": [r'témoignage', r'avis.*client', r'review'],
        "footer": [r'footer', r'pied.*page', r'copyright'],
        "faq": [r'faq', r'question.*fréquent', r'accordéon'],
        "button": [r'bouton', r'button', r'cta'],
        "tabs": [r'onglet', r'tab'],
        "carousel": [r'carousel', r'diaporama', r'slider'],
        "search": [r'recherche', r'search'],
    }

    LAYOUT_HEURISTICS = {
        "landing": {"indicators": ["hero", "pricing", "testimonial", "footer", "navbar"], "min": 3},
        "dashboard": {"indicators": ["sidebar", "chart", "table", "card", "navbar"], "min": 2},
        "product_page": {"indicators": ["card", "gallery", "pricing", "testimonial"], "min": 2},
        "contact_page": {"indicators": ["form", "faq", "footer"], "min": 2},
        "blog": {"indicators": ["card", "sidebar", "navbar"], "min": 2},
    }

    def analyze(self, description: str) -> Dict:
        desc = description.lower()
        components, scores = [], {}
        for comp, patterns in self.COMPONENT_PATTERNS.items():
            s = sum(1 for p in patterns if re.search(p, desc))
            if s > 0:
                scores[comp] = s
                components.append(comp)

        regions = [r for r, pats in self.REGION_PATTERNS.items() if any(re.search(p, desc) for p in pats)]

        best_layout, best_score, conf = "landing", 0, 0
        for layout, cfg in self.LAYOUT_HEURISTICS.items():
            matched = sum(1 for ind in cfg["indicators"] if ind in components)
            if matched >= cfg["min"] and matched > best_score:
                best_layout, best_score = layout, matched
                conf = matched / len(cfg["indicators"])

        sections = self._to_sections(components)
        return {"layout": best_layout, "regions": regions, "components": components,
                "page_sections": sections, "confidence": conf, "description": description}

    def _to_sections(self, components: List[str]) -> List[str]:
        mapping = {"search": "navbar", "chart": "bar_chart"}
        sections = []
        for c in components:
            sections.append(mapping.get(c, c))
        return sections

    def to_page(self, description: str, seed: str = None) -> Tuple[str, Dict]:
        if seed is None:
            seed = hashlib.sha256(description.encode()).hexdigest()[:8]
        analysis = self.analyze(description)
        composer = MultiSectionPage()
        page, conf = composer.assemble(page_type=analysis["layout"], seed=seed,
                                       custom_sections=analysis["page_sections"] or None)
        return page, analysis


if __name__ == '__main__':
    print("─── 1. HRR Fusion ───")
    fusion = HRRHtmlFusion()
    fused, conf = fusion.fuse("card", "form")
    print(f"  card+form: {len(fused)} chars, input={'<input' in fused}, article={'<article' in fused}")
    fused2, _ = fusion.fuse("hero", "button")
    print(f"  hero+btn:  {len(fused2)} chars, btn={'btn' in fused2}")

    print("\n─── 2. MultiSection ───")
    composer = MultiSectionPage()
    page, conf = composer.assemble("landing", seed="test")
    print(f"  landing: {len(page)} chars, sections={page.count('═══ Section')}, DOCTYPE={'<!DOCTYPE' in page}")

    print("\n─── 3. ReferenceAnalyzer ───")
    analyzer = ReferenceAnalyzer()
    for desc in ["landing page avec hero, cartes, tarifs, témoignages et footer",
                 "dashboard avec sidebar, tableau, graphique et statistiques"]:
        a = analyzer.analyze(desc)
        print(f"  \"{desc[:45]}...\" → layout={a['layout']} sections={a['page_sections'][:4]} conf={a['confidence']:.0%}")
    print("\n✅ real_composers.py reconstruit")
