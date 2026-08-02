"""
📸 Image → Code (reconstruit, autonome)
=========================================
Analyse d'image (Pillow optionnel) : palette dominante, mode clair/sombre,
régions de layout, détection de grille. Fallback description textuelle.
"""

import re, colorsys
from typing import Dict, List, Tuple, Optional

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ImageAnalyzer:
    """Analyse basique d'image pour Reference-Based Design."""

    def analyze_image(self, image_path: str = None, image_data: bytes = None,
                      description: str = None) -> Dict:
        if HAS_PIL and (image_path or image_data):
            return self._analyze_pil(image_path, image_data)
        if description:
            return self._analyze_description(description)
        return self._default()

    def _analyze_pil(self, path=None, data=None) -> Dict:
        try:
            from io import BytesIO
            img = Image.open(path if path else BytesIO(data))
            img = img.convert("RGB")
            img.thumbnail((200, 200))
            w, h = img.size

            quantized = img.quantize(colors=5, method=2)
            pal = quantized.getpalette()[:15]
            rgb = list(zip(pal[0::3], pal[1::3], pal[2::3]))
            hist = quantized.histogram()[:5]
            total = sum(hist) or 1
            palette = sorted([(rgb[i], hist[i] / total * 100) for i in range(5)], key=lambda x: -x[1])

            avg_brightness = sum(sum(c[:3]) / 3 for c, _ in palette) / 5
            is_dark = avg_brightness < 128

            dom = palette[0][0]
            hsv = colorsys.rgb_to_hsv(dom[0] / 255, dom[1] / 255, dom[2] / 255)
            hue = int(hsv[0] * 360)

            regions = self._detect_bands(img, w, h)
            has_grid = self._detect_grid(img, w, h)

            return {"palette": palette, "is_dark": is_dark, "dominant_hue": hue,
                    "regions": regions, "has_grid": has_grid,
                    "css_vars": self._palette_to_css(palette, is_dark, hue),
                    "source": "pillow"}
        except Exception as e:
            return self._default(str(e))

    def _detect_bands(self, img, w, h) -> List[str]:
        pixels = img.load()
        rows = []
        step_y = max(1, h // 20)
        step_x = max(1, w // 20)
        for y in range(0, h, step_y):
            vals = [sum(pixels[x, y]) / 3 for x in range(0, w, step_x)]
            rows.append(sum(vals) / len(vals))
        if not rows:
            return ["header", "body", "footer"]
        n = len(rows)
        top = sum(rows[:max(1, n // 5)]) / max(1, n // 5)
        bot = sum(rows[-max(1, n // 7):]) / max(1, n // 7)
        mid = sum(rows[n // 5:n - n // 7]) / max(1, n - n // 5 - n // 7)
        regions = []
        if abs(top - mid) > 20:
            regions.append("header")
        regions.append("body")
        if abs(bot - mid) > 20:
            regions.append("footer")
        return regions

    def _detect_grid(self, img, w, h) -> bool:
        try:
            pixels = img.load()
            darker = 0
            for x in range(0, w, 3):
                col = sum(sum(pixels[x, y]) / 3 for y in range(0, h, 5))
                nxt = sum(sum(pixels[min(x + 1, w - 1), y]) / 3 for y in range(0, h, 5))
                if col < nxt:
                    darker += 1
            return darker > w / 15
        except Exception:
            return False

    def _palette_to_css(self, palette, is_dark, hue) -> str:
        def hex_(rgb):
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        p = palette[0][0] if palette else (99, 102, 241)
        a = palette[1][0] if len(palette) > 1 else (236, 72, 153)
        acc = palette[2][0] if len(palette) > 2 else (249, 115, 22)
        bg = palette[-1][0] if palette else (10, 10, 26)
        tx = (240, 240, 250) if is_dark else (20, 20, 40)
        return f""":root {{
  --color-primary: {hex_(p)};
  --color-secondary: {hex_(a)};
  --color-accent: {hex_(acc)};
  --color-bg: {hex_(bg)};
  --color-bg-alt: {hex_((bg[0]+15, bg[1]+15, bg[2]+15))};
  --color-text: {hex_(tx)};
  --gradient-primary: linear-gradient(135deg, {hex_(p)}, {hex_(acc)});
}}"""

    def _analyze_description(self, desc: str) -> Dict:
        d = desc.lower()
        is_dark = any(w in d for w in ["dark", "sombre", "noir", "night"])
        color_hints = {"rouge": 0, "red": 0, "orange": 30, "jaune": 50, "yellow": 50,
                       "vert": 120, "green": 120, "bleu": 210, "blue": 210,
                       "violet": 270, "purple": 270, "rose": 330, "pink": 330}
        hue = 262
        for kw, h in color_hints.items():
            if kw in d:
                hue = h
                break
        regions = [r for r in ["header", "nav", "body", "main", "footer", "sidebar"] if r in d] or ["header", "body", "footer"]
        has_grid = any(w in d for w in ["grid", "grille", "cards", "cartes", "colonnes"])
        return {"palette": [], "is_dark": is_dark, "dominant_hue": hue,
                "regions": regions, "has_grid": has_grid,
                "css_vars": self._palette_to_css([(p, 40) for p in [(99, 102, 241), (236, 72, 153)]], is_dark, hue),
                "source": "description"}

    def _default(self, error: str = None) -> Dict:
        return {"palette": [], "is_dark": True, "dominant_hue": 262,
                "regions": ["header", "body", "footer"], "has_grid": False,
                "css_vars": ":root { --color-primary: hsl(262,60%,55%); }",
                "source": "default", "error": error}

    def to_page_plan(self, analysis: Dict) -> Dict:
        from real_composers import ReferenceAnalyzer
        desc_parts = list(analysis.get("regions", []))
        if analysis.get("has_grid"):
            desc_parts.append("grid of cards")
        desc = " ".join(desc_parts) or "landing page with navbar hero features footer"
        plan = ReferenceAnalyzer().analyze(desc)
        plan["css_vars"] = analysis.get("css_vars", "")
        plan["is_dark"] = analysis.get("is_dark", True)
        plan["dominant_hue"] = analysis.get("dominant_hue", 262)
        return plan


if __name__ == '__main__':
    a = ImageAnalyzer()
    print(f"PIL: {HAS_PIL}")
    for desc in ["Un dashboard sombre avec sidebar bleu et grille de cards",
                 "Une landing page claire avec navbar, hero et tarifs orange"]:
        r = a.analyze_image(description=desc)
        plan = a.to_page_plan(r)
        print(f"  \"{desc[:45]}...\" → dark={r['is_dark']} hue={r['dominant_hue']}° layout={plan['layout']}")
    print("\n✅ image_to_code.py reconstruit")
