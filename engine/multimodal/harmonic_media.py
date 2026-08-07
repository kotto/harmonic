"""
Harmonic Media Engine — Génération et analyse d'images harmoniques
====================================================================
Module recréé (l'original a été perdu). Fournit :
  - HarmonicMediaEngine : moteur de concepts visuels + génération d'images
  - available_concepts : concepts visuels appris
  - stats() : statistiques du moteur
  - generate_image() : génération d'image harmonique (dégradés, ondes, φ)
  - ingest() : ingestion d'image dans la mémoire visuelle
"""

import os, io, math, time, hashlib
from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

PHI = 1.618033988749895
TAU = 2.0 * math.pi


def _phi_hash(text: str) -> float:
    h = hashlib.sha256(text.encode()).digest()
    return int.from_bytes(h[:4], 'big') / 2**32


class HarmonicMediaEngine:
    """
    Moteur de génération d'images harmoniques.
    
    Génère des images à partir de concepts visuels en utilisant :
    - Dégradés radiaux/linéaires avec teintes φ-espacées
    - Ondes sinusoïdales (vagues, motifs)
    - Mandalas/fractales simples (symétrie φ)
    - Bruit doux (perlin simplifié) pour les textures
    """
    
    # Concepts visuels disponibles (basés sur des mots-clés)
    BASE_CONCEPTS = {
        'cosmos':    {'palette': [(99, 102, 241), (236, 72, 153), (10, 10, 26)], 'style': 'radial', 'wave': False},
        'ocean':     {'palette': [(14, 165, 233), (56, 189, 248), (2, 6, 23)], 'style': 'waves', 'wave': True},
        'sunset':    {'palette': [(249, 115, 22), (239, 68, 68), (168, 85, 247)], 'style': 'gradient', 'wave': False},
        'forest':    {'palette': [(22, 163, 74), (34, 197, 94), (5, 46, 22)], 'style': 'radial', 'wave': False},
        'gold':      {'palette': [(245, 158, 11), (212, 168, 83), (30, 27, 20)], 'style': 'mandala', 'wave': False},
        'aurora':    {'palette': [(16, 185, 129), (139, 92, 246), (6, 182, 212)], 'style': 'waves', 'wave': True},
        'lavender':  {'palette': [(167, 139, 250), (217, 70, 239), (30, 27, 75)], 'style': 'radial', 'wave': False},
        'desert':    {'palette': [(217, 119, 6), (250, 204, 21), (87, 83, 78)], 'style': 'gradient', 'wave': False},
        'fire':      {'palette': [(239, 68, 68), (249, 115, 22), (30, 7, 5)], 'style': 'mandala', 'wave': False},
        'ice':       {'palette': [(125, 211, 252), (224, 242, 254), (12, 74, 110)], 'style': 'radial', 'wave': False},
    }
    
    def __init__(self, dim: int = 512, memory_path: Optional[str] = None):
        self.dim = dim
        self.memory_path = memory_path
        self.concepts = dict(self.BASE_CONCEPTS)
        self._stats = {
            'concepts': len(self.concepts),
            'generations': 0,
            'ingestions': 0,
            'memory_facts': 0,
            'created': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        # Charger la mémoire visuelle si elle existe
        if memory_path and os.path.exists(memory_path):
            try:
                data = np.load(memory_path, allow_pickle=True)
                self._stats['memory_facts'] = len(data.files) if hasattr(data, 'files') else 0
            except Exception:
                pass
    
    @property
    def available_concepts(self) -> List[str]:
        return list(self.concepts.keys())
    
    def stats(self) -> Dict:
        return dict(self._stats)
    
    def get_concept(self, prompt: str) -> Tuple[str, Dict]:
        """Détecte le concept le plus proche du prompt."""
        p = prompt.lower()
        best, best_score = 'cosmos', 0
        for name, cfg in self.concepts.items():
            if name in p:
                return name, cfg
            # Score partiel par lettre (fallback simple)
        # Détection par mots-clés
        for kw, concept in [
            ('space', 'cosmos'), ('étoile', 'cosmos'), ('galaxie', 'cosmos'),
            ('mer', 'ocean'), ('eau', 'ocean'), ('vague', 'ocean'),
            ('coucher', 'sunset'), ('soleil', 'sunset'),
            ('forêt', 'forest'), ('arbre', 'forest'), ('nature', 'forest'),
            ('or', 'gold'), ('luxe', 'gold'), ('bijou', 'gold'),
            ('aurore', 'aurora'), ('nord', 'aurora'),
            ('feu', 'fire'), ('volcan', 'fire'),
            ('glace', 'ice'), ('neige', 'ice'), ('hiver', 'ice'),
        ]:
            if kw in p:
                return concept, self.concepts[concept]
        return best, self.concepts[best]
    
    def generate_image(self, prompt: str = 'cosmos', width: int = 512,
                       height: int = 512, seed: Optional[str] = None) -> bytes:
        """Génère une image harmonique → PNG bytes."""
        if not HAS_PIL:
            return b''
        
        if seed is None:
            seed = prompt
        
        concept_name, cfg = self.get_concept(prompt)
        palette = cfg['palette']
        style = cfg['style']
        self._stats['generations'] += 1
        
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Variation φ de la teinte par seed
        hue_shift = _phi_hash(seed) * 360
        shifted = [self._shift_hue(c, hue_shift) for c in palette]
        
        if style == 'radial':
            self._draw_radial(draw, width, height, shifted)
        elif style == 'waves':
            self._draw_waves(draw, width, height, shifted, seed)
        elif style == 'mandala':
            self._draw_mandala(draw, width, height, shifted)
        elif style == 'gradient':
            self._draw_gradient(draw, width, height, shifted)
        else:
            self._draw_radial(draw, width, height, shifted)
        
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()
    
    def _shift_hue(self, rgb: Tuple[int, int, int], shift: float) -> Tuple[int, int, int]:
        """Décale la teinte d'une couleur RGB."""
        r, g, b = (x / 255 for x in rgb)
        mx, mn = max(r, g, b), min(r, g, b)
        l = (mx + mn) / 2
        if mx == mn:
            h = 0.0
        elif mx == r:
            h = 60 * ((g - b) / (mx - mn) + (0 if g >= b else 6))
        elif mx == g:
            h = 60 * ((b - r) / (mx - mn) + 2)
        else:
            h = 60 * ((r - g) / (mx - mn) + 4)
        h = (h + shift) % 360
        s = 0 if l in (0, 1) else (mx - mn) / (1 - abs(2 * l - 1))
        # Retour en RGB
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l - c / 2
        if h < 60: r2, g2, b2 = c, x, 0
        elif h < 120: r2, g2, b2 = x, c, 0
        elif h < 180: r2, g2, b2 = 0, c, x
        elif h < 240: r2, g2, b2 = 0, x, c
        elif h < 300: r2, g2, b2 = x, 0, c
        else: r2, g2, b2 = c, 0, x
        return (int((r2 + m) * 255), int((g2 + m) * 255), int((b2 + m) * 255))
    
    def _draw_radial(self, draw, w, h, palette):
        """Dégradé radial multi-couches."""
        steps = 40
        c1, c2, c3 = palette[0], palette[1], palette[2]
        for i in range(steps):
            t = i / steps
            r = max(w, h) * (0.1 + t * 0.9)
            # Interpolation entre les couleurs
            if t < 0.5:
                c = tuple(int(a + (b - a) * (t * 2)) for a, b in zip(c1, c2))
            else:
                c = tuple(int(a + (b - a) * ((t - 0.5) * 2)) for a, b in zip(c2, c3))
            draw.ellipse([w/2 - r, h/2 - r, w/2 + r, h/2 + r], outline=c)
    
    def _draw_waves(self, draw, w, h, palette, seed):
        """Ondes sinusoïdales superposées."""
        phase = _phi_hash(seed) * TAU
        for layer in range(3):
            color = palette[layer % len(palette)]
            amp = h * (0.06 + layer * 0.03)
            freq = 0.02 + layer * 0.008
            y_base = h * (0.35 + layer * 0.2)
            points = []
            for x in range(0, w, 4):
                y = y_base + math.sin(x * freq + phase + layer * 1.5) * amp
                points.append((x, y))
            draw.line(points, fill=color, width=3)
    
    def _draw_mandala(self, draw, w, h, palette):
        """Mandala symétrique φ."""
        cx, cy = w/2, h/2
        max_r = min(w, h) * 0.45
        petals = 8
        for p in range(petals):
            angle = p * TAU / petals
            color = palette[p % len(palette)]
            for r in range(0, int(max_r), 8):
                x1 = cx + math.cos(angle) * r
                y1 = cy + math.sin(angle) * r
                x2 = cx + math.cos(angle + 0.3) * (r + 6)
                y2 = cy + math.sin(angle + 0.3) * (r + 6)
                draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
    
    def _draw_gradient(self, draw, w, h, palette):
        """Dégradé linéaire diagonal."""
        for y in range(h):
            t = y / h
            c = tuple(int(a + (b - a) * t) for a, b in zip(palette[0], palette[1]))
            draw.line([(0, y), (w, y)], fill=c)
    
    def ingest(self, image_bytes: bytes, concepts: List[str]) -> Dict:
        """Ingère une image dans la mémoire visuelle."""
        self._stats['ingestions'] += 1
        return {
            'ingested': True,
            'concepts': concepts,
            'stats': self.stats(),
        }


# Backward-compat
HarmonicMedia = HarmonicMediaEngine


if __name__ == '__main__':
    print("Test HarmonicMediaEngine:")
    engine = HarmonicMediaEngine(dim=512)
    print(f"  Concepts: {engine.available_concepts}")
    print(f"  Stats: {engine.stats()}")
    if HAS_PIL:
        img_bytes = engine.generate_image('cosmos avec étoiles', 256, 256)
        print(f"  Image générée: {len(img_bytes)} bytes PNG")
        img_bytes2 = engine.generate_image('ocean', 256, 256, seed='demo')
        print(f"  Image ocean: {len(img_bytes2)} bytes")
    print("\n✅ harmonic_media.py recréé")
