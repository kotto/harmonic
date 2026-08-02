"""
🔄 PhiFlex — Flexibilité Φ (reconstruit, autonome)
====================================================
Sélection de variantes φ-espacées, enrichissements φ-seuil,
composition HRR, proportions φ-adjacentes.

Usage:
    from phi_flex import PhiFlex
    pflex = PhiFlex()
    variant = pflex.select("card", seed="mon-article")
"""

import math, hashlib
from typing import Dict, List, Tuple, Optional
import numpy as np

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
TAU = 2.0 * math.pi


def phi_hash(text: str) -> float:
    h = hashlib.sha256(text.encode()).digest()
    return int.from_bytes(h[:4], 'big') / 2**32


# ═══════════════════════════════════════════════════════════════════
# 1. PHI VARIANT SELECTOR
# ═══════════════════════════════════════════════════════════════════

class PhiVariantSelector:
    """Sélection déterministe φ-espacée de variantes."""

    VARIANTS = {
        "card": ["default", "horizontal", "overlay", "minimal", "featured"],
        "hero": ["centered", "left_aligned", "split", "gradient_bg", "minimal"],
        "navbar": ["sticky_default", "transparent", "sidebar_left", "centered_logo", "mega_menu"],
        "button": ["primary_solid", "outline_ghost", "gradient_icon", "pill_rounded", "underline"],
        "form": ["stacked", "inline", "floating_labels", "minimal", "card_contained"],
        "footer": ["three_col", "simple_centered", "mega_footer", "split_brand", "stacked"],
        "landing_page": ["saas_default", "product_showcase", "coming_soon", "lead_gen", "storytelling"],
    }

    def select(self, component_type: str, seed: str = "default",
               index_position: int = 0) -> str:
        variants = self.VARIANTS.get(component_type, ["default"])
        n = len(variants)
        if n <= 1:
            return variants[0]
        h = phi_hash(f"{seed}|{component_type}")
        idx = int((h + index_position * PHI_INV) * PHI * n) % n
        return variants[idx]

    def select_multiple(self, component_type: str, seed: str = "default",
                        count: int = 3) -> List[str]:
        variants = self.VARIANTS.get(component_type, ["default"])
        n = len(variants)
        count = min(count, n)
        h = phi_hash(f"{seed}|{component_type}")
        selected = []
        for i in range(count):
            idx = int((h + i * PHI_INV) * PHI * n) % n
            v = variants[idx]
            if v not in selected:
                selected.append(v)
        remaining = [v for v in variants if v not in selected]
        while len(selected) < count and remaining:
            selected.append(remaining.pop(0))
        return selected[:count]

    def get_variant_count(self, component_type: str) -> int:
        return len(self.VARIANTS.get(component_type, ["default"]))


# ═══════════════════════════════════════════════════════════════════
# 2. PHI THRESHOLD ENRICHER
# ═══════════════════════════════════════════════════════════════════

class PhiThresholdEnricher:
    """Enrichissements conditionnels au seuil φ⁻¹ = 0.618 (~62% appliqués)."""

    ENRICHMENTS = {
        "card": [
            ("badge", '<span class="card__badge">Nouveau</span>'),
            ("shadow_lg", "box-shadow: var(--shadow-lg)"),
            ("hover_scale", "transition: transform 0.3s"),
            ("ribbon", '<div class="card__ribbon">Populaire</div>'),
        ],
        "hero": [
            ("subtitle", '<p class="hero__subtitle">Sous-titre explicatif</p>'),
            ("cta_secondary", '<a href="#" class="btn btn-outline">En savoir plus</a>'),
            ("background_gradient", "background: var(--gradient-subtle)"),
            ("scroll_indicator", '<div class="scroll-indicator">↓</div>'),
        ],
        "navbar": [
            ("cta_button", '<a href="#" class="btn btn-primary btn-sm">Essai gratuit</a>'),
            ("search_bar", '<input type="search" class="nav__search" placeholder="Rechercher…">'),
            ("notification_badge", '<span class="nav__badge">3</span>'),
        ],
    }

    def enrich(self, component_type: str, seed: str = "default",
               threshold: float = PHI_INV) -> List[str]:
        enrichments = self.ENRICHMENTS.get(component_type, [])
        selected = []
        for name, _ in enrichments:
            if phi_hash(f"{seed}|{component_type}|{name}") < threshold:
                selected.append(name)
        return selected

    def get_enrichment_html(self, component_type: str, name: str) -> str:
        return dict(self.ENRICHMENTS.get(component_type, [])).get(name, "")


# ═══════════════════════════════════════════════════════════════════
# 3. PHI COMPONENT COMPOSER (plan de layout)
# ═══════════════════════════════════════════════════════════════════

class PhiComponentComposer:
    """Compose un plan de page : slots → composants (φ-sélectionnés)."""

    LAYOUTS = {
        "landing_page": {
            "slots": ["header", "hero", "section1", "section2", "section3", "cta", "footer"],
            "options": {
                "header": ["navbar"], "hero": ["hero"],
                "section1": ["features", "pricing", "testimonial", "gallery", "faq"],
                "section2": ["pricing", "testimonial", "features", "blog_layout", "table"],
                "section3": ["testimonial", "faq", "contact_form", "gallery", "pricing"],
                "cta": ["hero", "contact_form"], "footer": ["footer"],
            },
        },
        "dashboard": {
            "slots": ["sidebar", "header", "stats_row", "main_content", "secondary"],
            "options": {
                "sidebar": ["sidebar"], "header": ["navbar"],
                "stats_row": ["features", "pricing"],
                "main_content": ["table", "gallery", "blog_layout", "form"],
                "secondary": ["card", "testimonial", "faq"],
            },
        },
        "page_with_sidebar": {
            "slots": ["header", "sidebar", "content", "footer"],
            "options": {
                "header": ["navbar"], "sidebar": ["sidebar", "card", "form"],
                "content": ["hero", "features", "gallery", "table", "blog_layout", "faq", "contact_form"],
                "footer": ["footer"],
            },
        },
    }

    def compose(self, layout_type: str, seed: str = "default") -> Dict[str, str]:
        if layout_type not in self.LAYOUTS:
            return {}
        layout = self.LAYOUTS[layout_type]
        plan = {}
        for i, slot in enumerate(layout["slots"]):
            options = layout["options"].get(slot, ["card"])
            if not options:
                continue
            h = phi_hash(f"{seed}|{layout_type}|{slot}|{i}")
            plan[slot] = options[int(h * PHI * len(options)) % len(options)]
        return plan

    def get_possible_combinations(self, layout_type: str) -> int:
        if layout_type not in self.LAYOUTS:
            return 0
        total = 1
        for options in self.LAYOUTS[layout_type]["options"].values():
            total *= len(options)
        return total


# ═══════════════════════════════════════════════════════════════════
# 3b. HRR COMPOSER (fusions connues + score de cohérence)
# ═══════════════════════════════════════════════════════════════════

class HRRComposer:
    """Composition HRR : suggestions de fusion + score de cohérence."""

    DIM = 64

    FUSION_TEMPLATES = {
        ("card", "form"): ("embed", "body"),
        ("navbar", "form"): ("append", "end"),
        ("hero", "form"): ("overlay", "center"),
        ("card", "button"): ("append", "footer"),
        ("hero", "button"): ("append", "actions"),
        ("dashboard", "table"): ("embed", "main"),
        ("dashboard", "chart"): ("embed", "stats"),
        ("landing_page", "pricing"): ("replace_section", "section2"),
        ("landing_page", "testimonial"): ("replace_section", "section3"),
    }

    def __init__(self):
        self._psi_cache: Dict[str, np.ndarray] = {}

    def _encode(self, name: str) -> np.ndarray:
        if name in self._psi_cache:
            return self._psi_cache[name]
        rng = np.random.RandomState(hash(name) & 0xFFFFFFFF)
        psi = rng.randn(self.DIM) + 1j * rng.randn(self.DIM)
        psi /= (np.linalg.norm(psi) + 1e-10)
        self._psi_cache[name] = psi
        return psi

    def bind(self, comp_a: str, comp_b: str) -> str:
        mode, slot = self.FUSION_TEMPLATES.get((comp_a, comp_b), ("embed", "body"))
        return f"{comp_a}_{comp_b}_{mode}_{slot}"

    def suggest_compositions(self, components: List[str], max_pairs: int = 5) -> List[Tuple[str, str, str, float]]:
        suggestions = []
        for i, a in enumerate(components):
            for b in components[i+1:]:
                fusion = self.FUSION_TEMPLATES.get((a, b)) or self.FUSION_TEMPLATES.get((b, a))
                if not fusion:
                    continue
                mode, slot = fusion
                coherence = (float(np.real(np.dot(np.conj(self._encode(a)), self._encode(b)))) + 1.0) / 2.0
                suggestions.append((a, b, mode, coherence))
        suggestions.sort(key=lambda x: -x[3])
        return suggestions[:max_pairs]

    def composition_score(self, component_set: List[str]) -> float:
        if len(component_set) < 2:
            return 1.0
        scores = []
        for i, a in enumerate(component_set):
            for b in component_set[i+1:]:
                if self.FUSION_TEMPLATES.get((a, b)) or self.FUSION_TEMPLATES.get((b, a)):
                    scores.append(0.9)
                else:
                    scores.append((float(np.real(np.dot(np.conj(self._encode(a)), self._encode(b)))) + 1.0) / 2.0)
        return sum(scores) / len(scores)


# ═══════════════════════════════════════════════════════════════════
# 4. ORCHESTRATEUR
# ═══════════════════════════════════════════════════════════════════

class PhiFlex:
    """Orchestrateur de flexibilité φ."""

    def __init__(self):
        self.selector = PhiVariantSelector()
        self.enricher = PhiThresholdEnricher()
        self.composer = PhiComponentComposer()
        self.hrr = HRRComposer()

    def select(self, component_type: str, seed: str = "default", index: int = 0) -> str:
        return self.selector.select(component_type, seed, index)

    def select_multiple(self, component_type: str, seed: str = "default", count: int = 3) -> List[str]:
        return self.selector.select_multiple(component_type, seed, count)

    def enrich(self, component_type: str, seed: str = "default") -> List[str]:
        return self.enricher.enrich(component_type, seed)

    def compose_layout(self, layout_type: str, seed: str = "default") -> Dict[str, str]:
        return self.composer.compose(layout_type, seed)

    def stats(self) -> Dict:
        return {
            "variant_types": len(self.selector.VARIANTS),
            "total_variants": sum(len(v) for v in self.selector.VARIANTS.values()),
            "layout_types": len(self.composer.LAYOUTS),
            "total_layout_combinations": sum(self.composer.get_possible_combinations(lt)
                                             for lt in self.composer.LAYOUTS),
            "enrichment_types": len(self.enricher.ENRICHMENTS),
            "phi_threshold": PHI_INV,
        }


if __name__ == '__main__':
    pflex = PhiFlex()
    print("Variantes card pour 10 seeds:")
    for i in range(10):
        print(f"  seed {i:2d} → {pflex.select('card', seed=f'user-{i}'):15s} enrich={pflex.enrich('card', seed=f'user-{i}')}")
    print(f"\nCombos landing_page: {pflex.composer.get_possible_combinations('landing_page')}")
    plan = pflex.compose_layout('landing_page', seed='demo')
    print(f"Plan: {plan}")
    print("\n✅ phi_flex.py reconstruit")
