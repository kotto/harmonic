"""
⚡ JS State Machine (reconstruit, autonome)
============================================
Injecte des états UI (idle/loading/success/error/empty) + mapping
de descriptions vers templates (Design→Code basique).
"""

import re, hashlib
from typing import Dict, List, Tuple, Optional


class StateMachine:
    """Moteur d'état minimaliste pour composants UI."""

    STATES = {
        "idle": {"attr": 'data-state="idle"', "html": "", "css": ""},
        "loading": {"attr": 'data-state="loading"',
                    "html": '<div class="state-loading"><div class="spinner"></div><p>Chargement...</p></div>',
                    "css": ".state-loading{text-align:center;padding:32px}.spinner{width:32px;height:32px;margin:0 auto 20px;border:3px solid var(--color-border);border-top-color:var(--color-primary);border-radius:50%;animation:spin .8s linear infinite}"},
        "success": {"attr": 'data-state="success"',
                    "html": '<div class="state-success">✅ Opération réussie !</div>',
                    "css": ".state-success{text-align:center;padding:32px;color:var(--color-success);font-weight:600}"},
        "error": {"attr": 'data-state="error"',
                  "html": '<div class="state-error">❌ Une erreur est survenue.</div>',
                  "css": ".state-error{text-align:center;padding:32px;color:var(--color-error)}"},
        "empty": {"attr": 'data-state="empty"',
                  "html": '<div class="state-empty">📭 Aucune donnée pour le moment.</div>',
                  "css": ".state-empty{text-align:center;padding:52px;color:var(--color-text-muted)}"},
    }

    TRANSITIONS = {
        "form": {"submit": "loading", "response_ok": "success", "response_error": "error"},
        "card": {"delete": "loading", "deleted": "empty", "error": "error"},
        "dashboard": {"refresh": "loading", "loaded": "idle", "no_data": "empty", "error": "error"},
    }

    def inject(self, html: str, component_type: str = "generic") -> str:
        if 'data-state' not in html:
            html = re.sub(r'(<(?:div|article|section|form|main)[^>]*)>', r'\1 data-state="idle">', html, count=1)

        state_containers = '\n'.join(
            f'<div class="state-{name}" style="display:none">{self.STATES[name]["html"]}</div>'
            for name in ['loading', 'success', 'error', 'empty'] if self.STATES[name]["html"]
        )
        html = re.sub(r'(<(?:div|article|section|form|main)[^>]*data-state="idle"[^>]*>)',
                      r'\1\n' + state_containers, html, count=1)

        display_css = '''
  [data-state="idle"] .state-loading, [data-state="idle"] .state-success,
  [data-state="idle"] .state-error, [data-state="idle"] .state-empty { display: none; }
  [data-state="loading"] > :not(.state-loading):not(style):not(script) { display: none; }
  [data-state="loading"] .state-loading { display: block; }
  [data-state="success"] > :not(.state-success):not(style):not(script) { display: none; }
  [data-state="success"] .state-success { display: block; }
  [data-state="error"] > :not(.state-error):not(style):not(script) { display: none; }
  [data-state="error"] .state-error { display: block; }
  [data-state="empty"] > :not(.state-empty):not(style):not(script) { display: none; }
  [data-state="empty"] .state-empty { display: block; }'''

        css = '\n'.join(s["css"] for s in self.STATES.values() if s["css"])
        if '<style>' in html:
            html = html.replace('</style>', f'\n{css}\n{display_css}\n</style>')
        else:
            html += f'\n<style>\n{css}\n{display_css}\n</style>'

        html += '''
<script>
(function(){ const c = document.querySelector('[data-state]'); if (!c) return;
  window.setState = (s) => c.setAttribute('data-state', s);
  window.getState = () => c.getAttribute('data-state');
})();
</script>'''
        return html


class DesignToCode:
    """Mapping description textuelle → plan de composants."""

    PATTERNS = {
        "navbar": [r'menu', r'navigation', r'barre', r'header', r'en haut'],
        "hero": [r'grande image', r'bannière', r'hero', r'accroche', r'titre principal'],
        "features": [r'colonnes', r'fonctionnalités', r'features', r'avantages'],
        "pricing": [r'tarif', r'prix', r'abonnement', r'pricing', r'forfait'],
        "testimonial": [r'témoignage', r'avis', r'client', r'review'],
        "footer": [r'pied de page', r'footer', r'bas', r'copyright'],
        "form": [r'formulaire', r'contact', r'inscription', r'login', r'email'],
        "card": [r'carte', r'fiche', r'vignette', r'produit'],
        "gallery": [r'galerie', r'images', r'photos', r'portfolio', r'grille'],
        "dashboard": [r'dashboard', r'tableau de bord', r'stats', r'kpi'],
        "faq": [r'faq', r'questions', r'réponses'],
        "sidebar": [r'sidebar', r'latéral', r'menu gauche'],
        "table": [r'tableau', r'données', r'lignes'],
        "timeline": [r'chronologie', r'timeline', r'frise', r'étapes'],
        "chart": [r'graphique', r'chart', r'courbe', r'barres', r'camembert'],
    }

    LAYOUTS = {
        "landing_page": ["navbar", "hero", "features", "pricing", "testimonial", "footer"],
        "dashboard": ["sidebar", "navbar", "card", "table", "chart"],
        "product_page": ["navbar", "hero", "card", "gallery", "footer"],
        "contact_page": ["navbar", "form", "faq", "footer"],
        "blog": ["navbar", "card", "sidebar", "footer"],
    }

    def analyze(self, description: str) -> Dict:
        desc = description.lower()
        detected, scores = [], {}
        for comp, patterns in self.PATTERNS.items():
            s = sum(1 for p in patterns if re.search(p, desc))
            if s > 0:
                scores[comp] = s
                detected.append(comp)

        best_layout, best_match = "landing_page", 0
        for name, expected in self.LAYOUTS.items():
            m = sum(1 for c in expected if c in detected)
            if m > best_match:
                best_match, best_layout = m, name

        return {"layout": best_layout,
                "components": sorted(detected, key=lambda c: -scores[c]),
                "confidence": min(1.0, best_match / max(1, len(self.LAYOUTS[best_layout])))}

    def to_prompt(self, description: str) -> str:
        a = self.analyze(description)
        return f"Crée une {a['layout'].replace('_', ' ')} avec : " + ", ".join(a["components"][:5])


if __name__ == '__main__':
    sm = StateMachine()
    enriched = sm.inject('<form><input type="text"></form>', 'form')
    print(f"StateMachine: {len(enriched)} chars, data-state={'data-state' in enriched}, setState={'setState' in enriched}")

    dtc = DesignToCode()
    for desc in ["une landing page avec hero, features, pricing et footer",
                 "un dashboard avec sidebar, stats et tableau"]:
        a = dtc.analyze(desc)
        print(f"  \"{desc[:45]}...\" → {a['layout']} ({a['components'][:5]}) conf={a['confidence']:.0%}")
    print("\n✅ js_state_machine.py reconstruit")
