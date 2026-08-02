"""
⚡ Enhance Frontend (reconstruit, autonome)
============================================
#2 JS Injector (drag-drop, state, fetch)
#3 ContextualTheme (sujet → couleurs)
#4 DesignPolish (gradients animés, ripple, scroll reveal)
"""

import re
from typing import Dict, List, Tuple


# ═══════════════════════════════════════════════════════════════════
# #2 — JS INJECTOR
# ═══════════════════════════════════════════════════════════════════

class JSInjector:
    """Injecte des comportements interactifs génériques."""

    DRAG_DROP_JS = """
<script>
(function(){
  document.querySelectorAll('[data-draggable="true"]').forEach(el=>{
    el.draggable=true;
    el.addEventListener('dragstart',e=>{e.dataTransfer.setData('text/plain','');el.classList.add('dragging')});
    el.addEventListener('dragend',()=>el.classList.remove('dragging'));
  });
  document.querySelectorAll('[data-drop-zone]').forEach(zone=>{
    zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('drag-over')});
    zone.addEventListener('dragleave',()=>zone.classList.remove('drag-over'));
    zone.addEventListener('drop',e=>{e.preventDefault();zone.classList.remove('drag-over');const el=document.querySelector('.dragging');if(el)zone.appendChild(el)});
  });
  window.KAState=window.KAState||{};
  window.KAInc=function(key,delta=1){KAState[key]=(KAState[key]||0)+delta;const el=document.querySelector('[data-state-display="'+key+'"]');if(el)el.textContent=KAState[key];return KAState[key]};
  window.KAToggle=function(sel,cls){cls=cls||'active';document.querySelectorAll(sel).forEach(el=>el.classList.toggle(cls))};
  window.KAFetch=function(url,targetSel){const t=document.querySelector(targetSel);if(!t)return;fetch(url).then(r=>r.json()).then(d=>{t.dispatchEvent(new CustomEvent('ka:data',{detail:d}))}).catch(()=>{t.setAttribute('data-error','true')})};
})();
</script>"""

    def inject_drag_drop(self, html: str) -> str:
        html = re.sub(r'(<(?:article|div)[^>]*class="[^"]*(?:card|item|task)[^"]*")',
                      r'\1 data-draggable="true"', html, count=10)
        html = re.sub(r'(<(?:div|ul)[^>]*class="[^"]*(?:grid|list|column)[^"]*")',
                      r'\1 data-drop-zone', html, count=5)
        if self.DRAG_DROP_JS not in html:
            html += self.DRAG_DROP_JS
        return html

    def inject_counter(self, html: str, element_class: str = "cart-count") -> str:
        counter = (f'\n<span class="{element_class}" data-state-display="count">0</span>\n'
                   f'<button onclick="KAInc(\'count\',1)">+ Ajouter</button>\n'
                   f'<button onclick="KAInc(\'count\',-1)">− Retirer</button>')
        if self.DRAG_DROP_JS not in html:
            html += self.DRAG_DROP_JS
        return html + counter


# ═══════════════════════════════════════════════════════════════════
# #3 — CONTEXTUAL THEME
# ═══════════════════════════════════════════════════════════════════

class ContextualTheme:
    """Mappe un sujet vers une palette cohérente (28 thèmes)."""

    THEMES = {
        "cafe": {"hue": 30, "sat": 50, "name": "Café"},
        "restaurant": {"hue": 10, "sat": 60, "name": "Restaurant"},
        "food": {"hue": 35, "sat": 70, "name": "Food"},
        "tech": {"hue": 210, "sat": 65, "name": "Tech"},
        "software": {"hue": 210, "sat": 65, "name": "Software"},
        "startup": {"hue": 262, "sat": 60, "name": "Startup"},
        "nature": {"hue": 120, "sat": 45, "name": "Nature"},
        "ecology": {"hue": 120, "sat": 45, "name": "Ecology"},
        "health": {"hue": 150, "sat": 40, "name": "Health"},
        "medical": {"hue": 150, "sat": 40, "name": "Medical"},
        "fitness": {"hue": 100, "sat": 55, "name": "Fitness"},
        "luxury": {"hue": 45, "sat": 30, "name": "Luxury"},
        "jewelry": {"hue": 45, "sat": 30, "name": "Jewelry"},
        "finance": {"hue": 200, "sat": 50, "name": "Finance"},
        "banking": {"hue": 200, "sat": 50, "name": "Banking"},
        "kids": {"hue": 280, "sat": 75, "name": "Kids"},
        "toy": {"hue": 320, "sat": 70, "name": "Toy"},
        "music": {"hue": 280, "sat": 60, "name": "Music"},
        "art": {"hue": 340, "sat": 55, "name": "Art"},
        "photography": {"hue": 0, "sat": 0, "name": "Photography"},
        "travel": {"hue": 190, "sat": 55, "name": "Travel"},
        "education": {"hue": 220, "sat": 50, "name": "Education"},
        "gaming": {"hue": 270, "sat": 70, "name": "Gaming"},
        "real_estate": {"hue": 25, "sat": 40, "name": "Real Estate"},
        "fashion": {"hue": 330, "sat": 40, "name": "Fashion"},
        "beauty": {"hue": 340, "sat": 45, "name": "Beauty"},
        "default": {"hue": 262, "sat": 60, "name": "Default"},
    }

    KEYWORDS = {
        "cafe": ["café", "coffee", "bistro", "barista"],
        "restaurant": ["restaurant", "cuisine", "gastronomie", "menu"],
        "food": ["food", "nourriture", "recette", "delivery"],
        "tech": ["tech", "software", "saas", "app", "api", "cloud", "code"],
        "startup": ["startup", "incubator"],
        "nature": ["nature", "écologie", "green", "bio", "jardin", "plante"],
        "health": ["santé", "health", "médical", "clinic", "hôpital", "wellness"],
        "fitness": ["fitness", "gym", "sport", "yoga"],
        "luxury": ["luxe", "luxury", "premium", "gold", "bijou", "jewelry"],
        "finance": ["finance", "banking", "banque", "invest", "crypto"],
        "kids": ["enfant", "kids", "toy", "jouet"],
        "music": ["music", "musique", "playlist", "album", "concert", "spotify"],
        "art": ["art", "galerie", "painting", "sculpture"],
        "travel": ["travel", "voyage", "tourism", "hotel"],
        "education": ["education", "école", "cours", "learning", "formation"],
        "gaming": ["game", "jeu", "gaming", "esport", "tetris"],
        "fashion": ["fashion", "mode", "vêtement", "clothing"],
        "beauty": ["beauty", "cosmétique", "skincare"],
        "real_estate": ["immobilier", "real estate", "property", "maison"],
    }

    def detect_theme(self, prompt: str) -> Dict:
        p = prompt.lower()
        scores = {k: sum(1 for kw in v if kw in p) for k, v in self.KEYWORDS.items()}
        scores = {k: s for k, s in scores.items() if s > 0}
        best = max(scores, key=scores.get) if scores else "default"
        return self.THEMES.get(best, self.THEMES["default"])

    def generate_css_vars(self, prompt: str) -> str:
        theme = self.detect_theme(prompt)
        h, s = theme["hue"], theme["sat"]
        return f""":root {{
  --color-primary: hsl({h}, {s}%, 55%);
  --color-primary-hover: hsl({h}, {s+5}%, 48%);
  --color-secondary: hsl({(h+180)%360}, {s}%, 55%);
  --color-accent: hsl({(h+120)%360}, {s+10}%, 55%);
  --color-bg: hsl({h}, {s//3}%, 6%);
  --color-bg-alt: hsl({h}, {s//3}%, 10%);
  --color-text: hsl({h}, {s//4}%, 92%);
  --color-text-muted: hsl({h}, {s//5}%, 55%);
  --gradient-primary: linear-gradient(135deg, hsl({h},{s}%,55%), hsl({(h+120)%360},{s+10}%,55%));
}}"""


# ═══════════════════════════════════════════════════════════════════
# #4 — DESIGN POLISH
# ═══════════════════════════════════════════════════════════════════

class DesignPolish:
    """Ajoute du polish visuel (gradients, ripple, scroll reveal)."""

    POLISH_CSS = """
/* ═══ Design Polish ═══ */
.mesh-bg { background:
  radial-gradient(at 20% 30%, hsla(262,60%,50%,.15) 0px, transparent 50%),
  radial-gradient(at 80% 20%, hsla(22,85%,50%,.1) 0px, transparent 50%);
  animation: meshShift 15s ease-in-out infinite alternate; }
@keyframes meshShift { 0% { background-position: 0% 0%, 100% 0%; } 100% { background-position: 20% 10%, 80% 20%; } }
.glass { background: rgba(255,255,255,.05); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,.1); box-shadow: 0 8px 32px rgba(0,0,0,.2); }
.ripple { position: relative; overflow: hidden; }
.ripple::after { content: ''; position: absolute; inset: 0; background: radial-gradient(circle, rgba(255,255,255,.3) 10%, transparent 10%); background-position: center; background-size: 0% 0%; opacity: 0; transition: background-size .5s, opacity .4s; pointer-events: none; }
.ripple:active::after { background-size: 200% 200%; opacity: 1; transition: 0s; }
.hover-lift { transition: transform .25s cubic-bezier(.34,1.56,.64,1), box-shadow .25s; }
.hover-lift:hover { transform: translateY(-6px); box-shadow: 0 12px 40px rgba(0,0,0,.15); }
.text-gradient-anim { background: linear-gradient(90deg, var(--color-primary), var(--color-accent), var(--color-secondary), var(--color-primary)); background-size: 300% 100%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: textGradient 4s linear infinite; }
@keyframes textGradient { to { background-position: 300% 0; } }
[data-reveal] { opacity: 0; transform: translateY(20px); transition: opacity .6s, transform .6s; }
[data-reveal].revealed { opacity: 1; transform: translateY(0); }
.glow { box-shadow: 0 0 20px hsla(262,60%,55%,.3); transition: box-shadow .3s; }
.glow:hover { box-shadow: 0 0 30px hsla(262,60%,55%,.5); }
"""

    REVEAL_JS = """
<script>
(function(){
  if (!('IntersectionObserver' in window)) return;
  const obs = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{ if (e.isIntersecting) { e.target.classList.add('revealed'); obs.unobserve(e.target); } });
  }, { threshold: 0.15 });
  document.querySelectorAll('[data-reveal]').forEach(el=>obs.observe(el));
})();
</script>"""

    def add_polish(self, html: str, features: List[str] = None) -> str:
        if features is None:
            features = ["mesh_bg", "ripple", "hover_lift", "scroll_reveal"]
        css_parts, js_parts = [], []

        css_parts.append(self.POLISH_CSS)

        if "scroll_reveal" in features:
            html = re.sub(r'(<(?:section|article|div)[^>]*class="[^"]*(?:card|hero|feature|section)[^"]*")',
                          r'\1 data-reveal', html, count=10)
            js_parts.append(self.REVEAL_JS)

        if "ripple" in features:
            html = re.sub(r'(class="btn )', r'class="btn ripple ', html)

        if "hover_lift" in features:
            html = re.sub(r'(class="[^"]*card[^"]*")',
                          lambda m: m.group().replace('class="', 'class="hover-lift ') if 'hover-lift' not in m.group() else m.group(),
                          html, count=10)

        if css_parts:
            combined = '\n'.join(css_parts)
            if '<style>' in html:
                html = html.replace('</style>', f'\n{combined}\n</style>', 1)
            else:
                html += f'\n<style>{combined}</style>'

        for js in js_parts:
            html += js

        return html


if __name__ == '__main__':
    inj = JSInjector()
    enriched = inj.inject_drag_drop('<div class="card"><p>Test</p></div><div class="grid"></div>')
    print(f"JSInjector: drag={'data-draggable' in enriched}, zone={'data-drop-zone' in enriched}")

    ct = ContextualTheme()
    for p in ["Crée un site pour un café", "Build a SaaS startup", "Fais une page médicale", "Design luxury jewelry"]:
        print(f"  {p[:40]:42s} → {ct.detect_theme(p)['name']} (hue={ct.detect_theme(p)['hue']}°)")

    dp = DesignPolish()
    polished = dp.add_polish('<section class="hero"><button class="btn btn-primary">Test</button><div class="card">C</div></section>')
    print(f"DesignPolish: ripple={'ripple' in polished}, reveal={'data-reveal' in polished}, mesh={'mesh-bg' in polished}")
    print("\n✅ enhance_frontend.py reconstruit")
