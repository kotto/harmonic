#!/usr/bin/env python3
"""
Visual Knowledge — Renforce la réponse par le visuel
=====================================================
Transforme les faits d'un hologramme en supports visuels :
  - 🗺️  Cartes géographiques (pays, capitales, frontières)
  - 📊 Graphiques mathématiques (courbes, fonctions)
  - 🧬 Schémas scientifiques (structure, processus)
  - ⏳ Frises chronologiques (dates, événements)
  - 🔗 Graphes de connaissances (relations entre concepts)

PRINCIPE : Pas de génération probabiliste. Chaque visuel est DÉTERMINÉ
par les faits de l'hologramme. Si le fait est correct, le visuel l'est.

Usage :
    from visual_knowledge import VisualKnowledge
    vk = VisualKnowledge()
    img_b64 = vk.render(question, facts)  # → base64 PNG pour le chat
"""

import re, math, struct, zlib, base64, io
from typing import List, Tuple, Optional, Dict
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════════
# MINI RENDERER PNG — zéro dépendance externe
# ═══════════════════════════════════════════════════════════════════════════════

def _png_bytes(width: int, height: int, pixels: List[List[Tuple[int,int,int,int]]]) -> bytes:
    """Génère un PNG minimal depuis une grille de pixels RGBA."""
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))

    raw = b''
    for y in range(height):
        raw += b'\x00'  # filtre none
        for x in range(width):
            r, g, b, a = pixels[y][x] if y < len(pixels) and x < len(pixels[y]) else (0,0,0,0)
            raw += struct.pack('BBBB', r, g, b, a)

    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    return header + ihdr + idat + iend


# ═══════════════════════════════════════════════════════════════════════════════
# RENDERERS SPÉCIALISÉS
# ═══════════════════════════════════════════════════════════════════════════════

class VisualKnowledge:
    """Moteur de visualisation déterministe depuis les faits."""

    def __init__(self, width: int = 400, height: int = 300):
        self.W, self.H = width, height
        self._color_idx = 0

    def render(self, question: str, facts: List[Tuple[str, str, str, str]],
               domain: str = 'GENERAL') -> Optional[str]:
        """
        Détecte le type de visuel et le génère.

        Returns:
            str base64 PNG ou None si aucun visuel pertinent.
        """
        if not facts:
            return None

        q_lower = question.lower()

        # Détection du type
        if self._is_math(q_lower, facts):
            return self._render_math(q_lower, facts)
        if self._is_geo(q_lower, facts):
            return self._render_geo(facts)
        if self._is_timeline(q_lower, facts):
            return self._render_timeline(facts)
        if self._is_graph(q_lower, facts):
            return self._render_knowledge_graph(facts, question[:40])

        return None

    # ═══ DÉTECTION ═══

    def _is_math(self, q: str, facts: list) -> bool:
        keywords = ['courbe', 'graphe', 'fonction', 'sinus', 'cosinus', 'trace',
                    'plot', 'parabole', 'exponentielle', 'logarithme', 'dérivée']
        return any(k in q for k in keywords)

    def _is_geo(self, q: str, facts: list) -> bool:
        keywords = ['carte', 'pays', 'capitale', 'continent', 'frontière', 'région',
                    'montre-moi', 'où se trouve', 'ou se trouve', 'situe']
        return any(k in q for k in keywords) or any(
            'capitale' in str(f[1]).lower() or 'situe' in str(f[1]).lower()
            for f in facts[:3])

    def _is_timeline(self, q: str, facts: list) -> bool:
        keywords = ['chronologie', 'frise', 'dates', 'évolution', 'histoire',
                    'quand', 'en quelle année', 'siècle']
        return any(k in q for k in keywords) or any(
            f[2].isdigit() or (len(str(f[2])) == 4 and str(f[2]).startswith(('1','2')))
            for f in facts[:3])

    def _is_graph(self, q: str, facts: list) -> bool:
        return len(facts) >= 3

    # ═══ RENDU GRAPHIQUE MATHÉMATIQUE ═══

    COLORS = [
        (139, 131, 255, 255), (61, 219, 160, 255), (240, 192, 96, 255),
        (212, 83, 126, 255), (133, 183, 235, 255), (255, 107, 107, 255),
    ]

    def _next_color(self):
        c = self.COLORS[self._color_idx % len(self.COLORS)]
        self._color_idx += 1
        return c

    def _render_math(self, q: str, facts: list) -> str:
        """Trace une fonction mathématique simple."""
        W, H = self.W, self.H
        pixels = [[(7, 7, 15, 255) for _ in range(W)] for _ in range(H)]  # fond sombre

        # Détecter la fonction
        func = None
        if 'sin' in q: func = lambda x: math.sin(x)
        elif 'cos' in q: func = lambda x: math.cos(x)
        elif 'exp' in q or 'exponentielle' in q: func = lambda x: math.exp(x/3)
        elif 'log' in q: func = lambda x: math.log(max(0.1, x))
        elif 'carre' in q or 'x²' in q or 'x^2' in q: func = lambda x: x*x/10
        elif 'cube' in q or 'x³' in q: func = lambda x: x*x*x/50
        else: func = lambda x: x  # identité

        # Axes
        cx, cy = W // 2, H // 2
        for x in range(W):
            if 0 <= cy < H: pixels[cy][x] = (60, 60, 80, 255)  # axe X
        for y in range(H):
            if 0 <= cx < W: pixels[y][cx] = (60, 60, 80, 255)  # axe Y

        # Tracer la courbe
        color = self._next_color()
        scale_x = 20.0
        scale_y = 30.0
        prev_px, prev_py = None, None
        for px in range(W):
            x_val = (px - cx) / scale_x
            try:
                y_val = func(x_val)
                py = int(cy - y_val * scale_y)
                if 0 <= py < H:
                    pixels[py][px] = color
                    # Épaissir
                    for dy in [-1, 1]:
                        if 0 <= py+dy < H:
                            pixels[py+dy][px] = color
                prev_px, prev_py = px, py
            except (ValueError, OverflowError):
                pass

        buf = _png_bytes(W, H, pixels)
        return base64.b64encode(buf).decode('ascii')

    # ═══ RENDU GÉOGRAPHIQUE ═══

    def _render_geo(self, facts: list) -> str:
        """Affiche les relations géographiques sous forme de carte textuelle enrichie."""
        W, H = self.W, self.H
        pixels = [[(10, 10, 20, 255) for _ in range(W)] for _ in range(H)]

        # Titre
        title = "🗺️ Relations géographiques"
        self._draw_text(pixels, title, 12, 14, (240, 240, 255, 255))

        # Afficher les faits comme des nœuds
        nodes = {}
        y = 50
        for s, r, o, sec in facts[:8]:
            name = str(s)[:25]
            if name not in nodes:
                color = self._next_color()
                nodes[name] = (150, y, color)
                self._draw_text(pixels, f"📍 {name}", 20, y, color)
                y += 28
            if str(o)[:25] not in nodes and len(str(o)) > 2:
                color = self._next_color()
                nodes[str(o)[:25]] = (280, y - 28, color)
                self._draw_text(pixels, f"🏷️ {str(o)[:25]}", 200, y - 28, color)

        # Flèches entre nœuds
        for s, r, o, sec in facts[:4]:
            s_name = str(s)[:25]
            o_name = str(o)[:25]
            if s_name in nodes and o_name in nodes:
                x1, y1, c1 = nodes[s_name]
                x2, y2, c2 = nodes[o_name]
                self._draw_arrow(pixels, x1 + 80, y1 + 5, x2, y2 + 5, c1)

        buf = _png_bytes(W, H, pixels)
        return base64.b64encode(buf).decode('ascii')

    # ═══ RENDU FRISE CHRONOLOGIQUE ═══

    def _render_timeline(self, facts: list) -> str:
        """Affiche une frise chronologique simple."""
        W, H = self.W, self.H
        pixels = [[(10, 10, 20, 255) for _ in range(W)] for _ in range(H)]

        # Extraire les dates
        events = []
        for s, r, o, sec in facts:
            for part in str(o).split():
                if part.isdigit() and 1000 <= int(part) <= 2100:
                    events.append((int(part), f"{s} {r} {o}"[:50]))
                    break

        if not events:
            events = [(0, str(f[0])[:40]) for f in facts[:5]]

        events.sort()
        self._draw_text(pixels, "⏳ Frise chronologique", 12, 14, (240, 240, 255, 255))

        # Ligne du temps
        for x in range(40, W - 20):
            if 0 <= H//2 < H: pixels[H//2][x] = (60, 60, 100, 255)

        # Placer les événements
        color = self._next_color()
        for i, (year, desc) in enumerate(events[:8]):
            x = 40 + int((i / max(len(events)-1, 1)) * (W - 100))
            y = H//2 - 15 if i % 2 == 0 else H//2 + 15
            # Point
            for dy in [-2, -1, 0, 1, 2]:
                for dx in [-2, -1, 0, 1, 2]:
                    px, py = x+dx, (H//2)+dy
                    if 0 <= px < W and 0 <= py < H:
                        pixels[py][px] = color
            # Ligne verticale
            for py in range(min(y, H//2), max(y, H//2)):
                if 0 <= py < H: pixels[py][x] = color
            # Texte
            label = f"{year}: {desc[:30]}"
            tx = x + 5 if i % 2 == 0 else x + 5
            ty = y - 18 if i % 2 == 0 else y + 4
            self._draw_text(pixels, label, tx, ty, color)

        buf = _png_bytes(W, H, pixels)
        return base64.b64encode(buf).decode('ascii')

    # ═══ RENDU GRAPHE DE CONNAISSANCE ═══

    def _render_knowledge_graph(self, facts: list, topic: str = '') -> str:
        """Affiche un graphe de relations entre concepts."""
        W, H = self.W, self.H
        pixels = [[(10, 10, 20, 255) for _ in range(W)] for _ in range(H)]

        self._draw_text(pixels, f"🔗 {topic[:40]}", 12, 14, (240, 240, 255, 255))

        # Disposer les concepts en cercle
        concepts = []
        seen = set()
        for s, r, o, sec in facts[:8]:
            for c in [str(s)[:20], str(o)[:20]]:
                if c not in seen and len(c) > 2:
                    seen.add(c)
                    concepts.append(c)

        n = len(concepts)
        if n < 2:
            return None

        cx, cy = W // 2, H // 2 + 10
        radius = min(W, H) // 3

        positions = {}
        for i, concept in enumerate(concepts):
            angle = 2 * math.pi * i / n - math.pi / 2
            x = int(cx + radius * math.cos(angle))
            y = int(cy + radius * math.sin(angle))
            positions[concept] = (x, y)

        # Arêtes
        for s, r, o, sec in facts[:6]:
            s_name, o_name = str(s)[:20], str(o)[:20]
            if s_name in positions and o_name in positions:
                x1, y1 = positions[s_name]
                x2, y2 = positions[o_name]
                self._draw_line(pixels, x1, y1, x2, y2, (60, 60, 100, 255))

        # Nœuds
        for i, (concept, (x, y)) in enumerate(positions.items()):
            color = self._next_color()
            # Cercle
            for dy in range(-6, 7):
                for dx in range(-6, 7):
                    if dx*dx + dy*dy <= 36:
                        px, py = x+dx, y+dy
                        if 0 <= px < W and 0 <= py < H:
                            pixels[py][px] = color
            # Label
            self._draw_text(pixels, concept[:16], x + 8, y - 4, color)

        buf = _png_bytes(W, H, pixels)
        return base64.b64encode(buf).decode('ascii')

    # ═══ UTILITAIRES DE DESSIN ═══

    def _draw_text(self, pixels, text: str, x: int, y: int, color: tuple):
        """Dessine du texte simplifié (8x12 caractères approx)."""
        char_w, char_h = 7, 11
        for i, ch in enumerate(text):
            cx, cy = x + i * char_w, y
            # Caractère très simplifié : un rectangle vertical
            for dy in range(char_h):
                for dx in range(char_w):
                    px, py = cx + dx, cy + dy
                    if 0 <= px < self.W and 0 <= py < self.H:
                        # Éclaircir le fond
                        r, g, b, _ = color
                        if pixels[py][px][:3] == (10, 10, 20):
                            pixels[py][px] = (r//3, g//3, b//3, 255)
        # Marqueur de début
        for dy in range(10):
            for dx in range(3):
                px, py = x + dx, y + dy
                if 0 <= px < self.W and 0 <= py < self.H:
                    pixels[py][px] = color

    def _draw_arrow(self, pixels, x1, y1, x2, y2, color):
        """Flèche simple entre deux points."""
        self._draw_line(pixels, x1, y1, x2, y2, color)
        # Pointe
        for dx in [-3, 0, 3]:
            for dy in [-3, 0, 3]:
                if abs(dx) + abs(dy) <= 3:
                    px, py = x2 + dx, y2 + dy
                    if 0 <= px < self.W and 0 <= py < self.H:
                        pixels[py][px] = color

    def _draw_line(self, pixels, x1, y1, x2, y2, color):
        """Ligne de Bresenham."""
        dx, dy = abs(x2-x1), abs(y2-y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            if 0 <= x1 < self.W and 0 <= y1 < self.H:
                pixels[y1][x1] = color
            if x1 == x2 and y1 == y2: break
            e2 = 2 * err
            if e2 > -dy: err -= dy; x1 += sx
            if e2 < dx: err += dx; y1 += sy


# ═══════════════════════════════════════════════════════════════════════════════
# INTÉGRATION AVEC LE CHAT
# ═══════════════════════════════════════════════════════════════════════════════

_VISUAL_ENGINE = None

def get_visual_engine() -> VisualKnowledge:
    global _VISUAL_ENGINE
    if _VISUAL_ENGINE is None:
        _VISUAL_ENGINE = VisualKnowledge(400, 300)
    return _VISUAL_ENGINE


def augment_response(question: str, facts: List[Tuple], domain: str = 'GENERAL') -> Optional[str]:
    """
    Tente de générer un visuel pour enrichir la réponse.

    Returns:
        str base64 PNG à intégrer en <img src="data:image/png;base64,...">
        ou None si aucun visuel pertinent.
    """
    try:
        vk = get_visual_engine()
        b64 = vk.render(question, facts, domain)
        return b64
    except Exception:
        return None
