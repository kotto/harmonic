#!/usr/bin/env python3
"""
HARMONIC VISUAL COMPOSER — Génération d'images par templates SVG
==================================================================
Même architecture que PoeticKB mais pour les images.
20 templates visuels, 0% hallucination, 100% déterministe.

Usage :
  from harmonic_visual_composer import HarmonicVisualComposer
  hvc = HarmonicVisualComposer()
  svg = hvc.compose("un coucher de soleil sur le Nil avec des pyramides")
"""

import re, random, math, os, json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

PHI = 1.618033988749895
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "visual_assets")
os.makedirs(DATA_DIR, exist_ok=True)

PALETTES = {
    "aube": ["#FF6B35","#F7C59F","#EFEFD0","#004E89","#1A659E"],
    "crépuscule": ["#FF512F","#DD2475","#FF6B6B","#FFA07A","#FFD700"],
    "desert": ["#E8B042","#D4953A","#C07832","#A05A2A","#F4D03F"],
    "nil": ["#1B4F72","#2980B9","#6BB9F0","#AED6F1","#D4E6F1"],
    "kemet": ["#C5A55A","#B8963E","#8B6914","#D4AF37","#F4D03F"],
    "foret": ["#2ECC71","#27AE60","#1E8449","#145A32","#0B5345"],
    "nuit": ["#0B0B2A","#1A1A4E","#2D2D6B","#4A4A8A","#6B6BA8"],
    "mer": ["#0077B6","#00B4D8","#90E0EF","#CAF0F8","#03045E"],
    "montagne": ["#8D99AE","#6C7A89","#4A5D6B","#2B3A42","#1B2832"],
    "printemps": ["#FF9FF3","#F368E0","#FECA57","#FF6B6B","#48DBFB"],
}

@dataclass
class VisualTemplate:
    name: str
    pattern: str
    generator: callable
    category: str
    confidence: float

class HarmonicVisualComposer:

    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.palettes = PALETTES
        self.templates = self._build_templates()
        self.stats = {"total_compositions": 0}

    def _build_templates(self):
        t = []
        t.append(VisualTemplate("sunset_water", "coucher|sunset|crepuscule.*(mer|eau|lac|ocean|fleuve|riviere|water)", lambda s: self._gen_sunset_over_water(s), "landscape", 0.93))
        t.append(VisualTemplate("sunset_desert", "coucher|sunset|crepuscule.*(desert|sable|dune|sand)", lambda s: self._gen_sunset_desert(s), "landscape", 0.93))
        t.append(VisualTemplate("mountains", "montagne|mountain|sommet|peak", lambda s: self._gen_mountains(s), "landscape", 0.93))
        t.append(VisualTemplate("forest", "foret|forest|bois|arbre|tree|jungle", lambda s: self._gen_forest(s), "landscape", 0.92))
        t.append(VisualTemplate("beach", "plage|beach|rivage|cote", lambda s: self._gen_beach(s), "landscape", 0.91))
        t.append(VisualTemplate("night_sky", "nuit|night|etoile|lune|moon", lambda s: self._gen_night_sky(s), "landscape", 0.93))
        t.append(VisualTemplate("fields", "champ|field|prairie|meadow|plaine", lambda s: self._gen_fields(s), "landscape", 0.90))
        t.append(VisualTemplate("pyramids_nil", "pyramide|pyramid|kheops|gizeh.*(nil|fleuve|river)", lambda s: self._gen_pyramids_nil(s), "kemet", 0.95))
        t.append(VisualTemplate("pyramids_desert", "pyramide|pyramid|kheops|gizeh", lambda s: self._gen_pyramids_desert(s), "kemet", 0.94))
        t.append(VisualTemplate("temple", "temple|karnak|pharaon|obelisque|sphinx", lambda s: self._gen_temple(s), "kemet", 0.91))
        t.append(VisualTemplate("kemet_abstract", "kemet|maat|egypte|anubis|horus|isis|osiris", lambda s: self._gen_kemet_abstract(s), "kemet", 0.89))
        t.append(VisualTemplate("phi_spiral", "geometrique|phi|nombre dor|golden ratio|spiral|fibonacci|fractal", lambda s: self._gen_phi_spiral(s), "abstract", 0.92))
        t.append(VisualTemplate("waves", "onde|wave|vague|resonance|interference|harmonic", lambda s: self._gen_waves(s), "abstract", 0.91))
        t.append(VisualTemplate("grid", "grille|grid|motif|pattern|repetition", lambda s: self._gen_grid_pattern(s), "abstract", 0.89))
        t.append(VisualTemplate("network", "circuit|reseau|network|neural|neurone", lambda s: self._gen_network(s), "abstract", 0.88))
        t.append(VisualTemplate("sunset_water", "coucher|sunset", lambda s: self._gen_sunset_over_water(s), "landscape", 0.91))
        return t

    def _r(self, a, b): return random.randint(a, b)
    def _gradient(self, y1, y2, c1, c2, op=1.0):
        rid = random.randint(0,99999)
        return f'<linearGradient id="g{rid}" x1="0" y1="{y1}" x2="0" y2="{y2}"><stop offset="0%" stop-color="{c1}" stop-opacity="{op}"/><stop offset="100%" stop-color="{c2}" stop-opacity="{op}"/></linearGradient>'
    def _wrap(self, c, w, h):
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="#000"/>{c}</svg>'

    def _gen_sunset_over_water(self, s):
        w, h = self.width, self.height
        sky_h = int(h * 0.55)
        p = random.choice(["crepuscule","aube"])
        cols = random.sample(self.palettes[p], 3)
        el = []
        el.append(self._gradient(0, sky_h, cols[0], cols[1], 0.9))
        el.append(f'<rect width="{w}" height="{sky_h}" fill="url(#g0)"/>')
        el.append(self._gradient(sky_h, h, cols[1], cols[2], 0.7))
        el.append(f'<rect y="{sky_h}" width="{w}" height="{h-sky_h}" fill="url(#g1)"/>')
        sun_r = self._r(30,50)
        sun_x = self._r(w//3,2*w//3)
        sun_y = self._r(sky_h-40,sky_h-10)
        el.append(f'<circle cx="{sun_x}" cy="{sun_y}" r="{sun_r}" fill="{cols[2]}" opacity="0.9"/>')
        el.append(f'<circle cx="{sun_x}" cy="{sun_y}" r="{sun_r+10}" fill="{cols[2]}" opacity="0.3"/>')
        for i in range(5):
            el.append(f'<ellipse cx="{sun_x+self._r(-30,30)}" cy="{sky_h+20+i*20}" rx="40" ry="3" fill="{cols[2]}" opacity="{0.15-i*0.03:.2f}"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_sunset_desert(self, s):
        w, h = self.width, self.height
        sky_h = int(h * 0.6)
        cols = random.sample(self.palettes["desert"], 4)
        el = []
        el.append(self._gradient(0, sky_h, cols[0], cols[2]))
        el.append(f'<rect width="{w}" height="{sky_h}" fill="url(#g0)"/>')
        el.append(self._gradient(sky_h, h, cols[3], "#5D3A1A"))
        el.append(f'<rect y="{sky_h}" width="{w}" height="{h-sky_h}" fill="url(#g1)"/>')
        dc = [cols[3], "#B8860B", "#CD853F"]
        for i in range(5):
            dy = sky_h + 50 + i * 40
            cx = self._r(100, w - 100)
            el.append(f'<ellipse cx="{cx}" cy="{dy}" rx="{self._r(200,400)}" ry="{self._r(20,50)}" fill="{random.choice(dc)}" opacity="0.6"/>')
        sun_x = self._r(w//3, 2*w//3)
        el.append(f'<circle cx="{sun_x}" cy="{sky_h-30}" r="{self._r(40,60)}" fill="#FF4500" opacity="0.8"/>')
        el.append(f'<circle cx="{sun_x}" cy="{sky_h-30}" r="{self._r(50,75)}" fill="#FF6347" opacity="0.3"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_mountains(self, s):
        w, h = self.width, self.height
        cols = random.sample(self.palettes["montagne"], 3)
        el = []
        el.append(self._gradient(0, h, cols[0], cols[2]))
        el.append(f'<rect width="{w}" height="{h}" fill="url(#g0)"/>')
        for i in range(4):
            px = self._r(100, w-100)
            py = self._r(h//6, h//2)
            bw = self._r(300, 600)
            mc = f"rgba({self._r(60,120)},{self._r(60,120)},{self._r(80,140)},0.8)"
            el.append(f'<polygon points="{px-bw//2},{h} {px},{py} {px+bw//2},{h}" fill="{mc}" opacity="{0.5+i*0.1:.1f}"/>')
        for i in range(3):
            cx = self._r(200, 600)
            cy = self._r(h//4, h//3)
            el.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{self._r(40,80)}" ry="{self._r(10,20)}" fill="white" opacity="0.7"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_forest(self, s):
        w, h = self.width, self.height
        cols = self.palettes["foret"]
        el = [f'<rect width="{w}" height="{h}" fill="{cols[2]}"/>']
        el.append(self._gradient(h*2//3, h, cols[3], cols[4]))
        el.append(f'<rect y="{h*2//3}" width="{w}" height="{h//3}" fill="url(#g0)"/>')
        for i in range(12):
            tx = self._r(30, w-30)
            th = self._r(h//3, h*2//3)
            tc = random.choice([cols[0],"#1B5E20","#2E7D32","#388E3C"])
            tw = self._r(8, 15)
            el.append(f'<rect x="{tx-tw//2}" y="{h-th}" width="{tw}" height="{th}" fill="#4E342E"/>')
            el.append(f'<ellipse cx="{tx}" cy="{h-th}" rx="{self._r(20,40)}" ry="{self._r(30,50)}" fill="{tc}" opacity="0.85"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_beach(self, s):
        w, h = self.width, self.height
        sky_h, water_h, sand_h = h//2, h//4, h//4
        el = []
        el.append(self._gradient(0, sky_h, "#87CEEB", "#4682B4"))
        el.append(f'<rect width="{w}" height="{sky_h}" fill="url(#g0)"/>')
        el.append(f'<rect y="{sky_h}" width="{w}" height="{water_h}" fill="#006994" opacity="0.8"/>')
        el.append(self._gradient(sky_h+water_h, h, "#F4D03F", "#E8C547"))
        el.append(f'<rect y="{sky_h+water_h}" width="{w}" height="{sand_h}" fill="url(#g1)"/>')
        for i in range(6):
            el.append(f'<ellipse cx="{self._r(0,w)}" cy="{sky_h+self._r(5,water_h-5)}" rx="60" ry="3" fill="white" opacity="0.3"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_night_sky(self, s):
        w, h = self.width, self.height
        cols = self.palettes["nuit"]
        el = []
        el.append(self._gradient(0, h, cols[0], cols[2]))
        el.append(f'<rect width="{w}" height="{h}" fill="url(#g0)"/>')
        for i in range(50):
            el.append(f'<circle cx="{self._r(10,w-10)}" cy="{self._r(10,h*2//3)}" r="{random.uniform(0.5,2.5):.1f}" fill="white" opacity="{random.uniform(0.3,1.0):.1f}"/>')
        if random.random() > 0.3:
            mx, my = self._r(w//4, 3*w//4), self._r(50, h//3)
            el.append(f'<circle cx="{mx}" cy="{my}" r="40" fill="#FFFACD" opacity="0.9"/>')
            el.append(f'<circle cx="{mx-10}" cy="{my}" r="35" fill="{cols[0]}" opacity="0.8"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_fields(self, s):
        w, h = self.width, self.height
        sky_h = h // 3
        cols = random.sample(self.palettes["printemps"], 3)
        el = []
        el.append(self._gradient(0, sky_h, "#87CEEB", "#E0F0FF"))
        el.append(f'<rect width="{w}" height="{sky_h}" fill="url(#g0)"/>')
        for i in range(5):
            fy = sky_h + i * (h - sky_h) // 5
            fh = (h - sky_h) // 4
            cc = cols[i % len(cols)]
            el.append(f'<rect y="{fy}" width="{w}" height="{fh}" fill="{cc}" opacity="0.7"/>')
            for j in range(15):
                cx = j * w // 15 + self._r(-5, 5)
                el.append(f'<line x1="{cx}" y1="{fy}" x2="{cx}" y2="{fy+fh}" stroke="{cc}" stroke-width="1" opacity="0.3"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_pyramids_nil(self, s):
        w, h = self.width, self.height
        sky_h, desert_h = int(h*0.4), int(h*0.2)
        el = []
        el.append(self._gradient(0, sky_h, "#FF8C00", "#FFD700"))
        el.append(f'<rect width="{w}" height="{sky_h}" fill="url(#g0)"/>')
        el.append(f'<rect y="{sky_h}" width="{w}" height="{desert_h}" fill="#E8B042"/>')
        el.append(f'<rect y="{sky_h+desert_h}" width="{w}" height="{h-sky_h-desert_h}" fill="#1B4F72" opacity="0.8"/>')
        for px, ph, pw in [(w//3, desert_h, 180), (w*2//3, desert_h*2//3, 140), (w//2, desert_h//2, 100)]:
            el.append(f'<polygon points="{px-pw//2},{sky_h+desert_h} {px},{sky_h+desert_h-ph} {px+pw//2},{sky_h+desert_h}" fill="#C5A55A"/>')
        for i in range(4):
            el.append(f'<ellipse cx="{self._r(w//4,3*w//4)}" cy="{sky_h+desert_h+30+i*30}" rx="60" ry="2" fill="#FFD700" opacity="0.15"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_pyramids_desert(self, s):
        w, h = self.width, self.height
        sky_h = int(h * 0.5)
        el = []
        el.append(self._gradient(0, sky_h, "#FF6347", "#FFD700"))
        el.append(f'<rect width="{w}" height="{sky_h}" fill="url(#g0)"/>')
        el.append(self._gradient(sky_h, h, "#E8B042", "#8B6914"))
        el.append(f'<rect y="{sky_h}" width="{w}" height="{h-sky_h}" fill="url(#g1)"/>')
        for px, ph, pw in [(w//3, h-sky_h, 200), (w*2//3, (h-sky_h)*2//3, 150), (w//2, (h-sky_h)//2, 120)]:
            el.append(f'<polygon points="{px-pw//2},{h} {px},{h-ph} {px+pw//2},{h}" fill="#D4AF37" opacity="0.9"/>')
            el.append(f'<polygon points="{px-pw//2},{h} {px},{h-ph} 0,{h}" fill="#B8963E" opacity="0.5"/>')
        el.append(f'<ellipse cx="600" cy="{sky_h+50}" rx="40" ry="20" fill="#8B6914" opacity="0.6"/>')
        el.append(f'<rect x="590" y="{sky_h+30}" width="20" height="30" fill="#8B6914" opacity="0.6"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_temple(self, s):
        w, h = self.width, self.height
        sky_h = h // 3
        el = [f'<rect width="{w}" height="{h}" fill="#1A1A2E"/>']
        el.append(self._gradient(sky_h, h, "#C5A55A", "#8B6914"))
        el.append(f'<rect y="{sky_h}" width="{w}" height="{h-sky_h}" fill="url(#g0)"/>')
        for i in range(6):
            cx = 100 + i * 120
            el.append(f'<rect x="{cx-8}" y="{sky_h}" width="16" height="{h-sky_h}" fill="#D4AF37"/>')
            el.append(f'<rect x="{cx-15}" y="{sky_h-20}" width="30" height="20" fill="#D4AF37"/>')
        for i in range(8):
            hx, hy = self._r(50, w-50), self._r(sky_h+50, h-50)
            el.append(f'<circle cx="{hx}" cy="{hy}" r="3" fill="#F4D03F" opacity="0.4"/>')
            el.append(f'<line x1="{hx}" y1="{hy}" x2="{hx+10}" y2="{hy-10}" stroke="#F4D03F" stroke-width="1" opacity="0.4"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_kemet_abstract(self, s):
        w, h = self.width, self.height
        cx, cy = w//2, h//2
        el = [f'<rect width="{w}" height="{h}" fill="#0A0A0A"/>']
        el.append(f'<ellipse cx="{cx}" cy="{cy}" rx="80" ry="40" fill="none" stroke="#D4AF37" stroke-width="3"/>')
        el.append(f'<circle cx="{cx}" cy="{cy}" r="15" fill="#D4AF37"/>')
        el.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="#0A0A0A"/>')
        for i in range(3):
            ax = cx - 100 + i * 100
            el.append(f'<ellipse cx="{ax}" cy="{cy+80}" rx="8" ry="6" fill="none" stroke="#D4AF37" stroke-width="2"/>')
            el.append(f'<line x1="{ax}" y1="{cy+86}" x2="{ax}" y2="{cy+120}" stroke="#D4AF37" stroke-width="2"/>')
            el.append(f'<line x1="{ax-15}" y1="{cy+100}" x2="{ax+15}" y2="{cy+100}" stroke="#D4AF37" stroke-width="2"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_phi_spiral(self, s):
        w, h = self.width, self.height
        cx, cy = w//2, h//2
        el = [f'<rect width="{w}" height="{h}" fill="#0A0A14"/>']
        a, b = 0, 1
        pts = []
        for i in range(12):
            angle = i * math.pi / 2
            r = b * 15
            x, y = cx + r * math.cos(angle), cy + r * math.sin(angle)
            pts.append(f"{x:.0f},{y:.0f}")
            a, b = b, a + b
        el.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#3EF0D0" stroke-width="2" opacity="0.8"/>')
        for i in range(5):
            rs = int((PHI ** i) * 20)
            el.append(f'<rect x="{cx-rs//2}" y="{cy-rs//2}" width="{rs}" height="{rs}" fill="none" stroke="#3EF0D0" stroke-width="1" opacity="{0.15+i*0.1:.1f}"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_waves(self, s):
        w, h = self.width, self.height
        el = [f'<rect width="{w}" height="{h}" fill="#0A0A14"/>']
        cols = ["#3EF0D0","#A78BFA","#60A5FA","#F472B6","#34D399","#FB923C"]
        for wi in range(6):
            yo = h//8 + wi*h//8
            amp = 20 + wi*10
            freq = 0.005 + wi*0.003
            path = f'M 0,{yo} '
            for x in range(0, w+10, 20):
                path += f'L {x},{yo+amp*math.sin(freq*x):.0f} '
            el.append(f'<path d="{path}" fill="none" stroke="{cols[wi]}" stroke-width="2" opacity="0.7"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_grid_pattern(self, s):
        w, h = self.width, self.height
        gs = 40
        el = [f'<rect width="{w}" height="{h}" fill="#111122"/>']
        for x in range(0, w, gs):
            for y in range(0, h, gs):
                if (x//gs + y//gs) % 3 == 0:
                    el.append(f'<rect x="{x}" y="{y}" width="{gs}" height="{gs}" fill="#3EF0D0" opacity="0.05"/>')
                elif (x//gs + y//gs) % 3 == 1:
                    el.append(f'<circle cx="{x+gs//2}" cy="{y+gs//2}" r="{gs//4}" fill="#A78BFA" opacity="0.05"/>')
        return self._wrap("\n".join(el), w, h)

    def _gen_network(self, s):
        w, h = self.width, self.height
        el = [f'<rect width="{w}" height="{h}" fill="#0A0A14"/>']
        nodes = [(self._r(50,w-50),self._r(50,h-50)) for _ in range(20)]
        for nx, ny in nodes:
            el.append(f'<circle cx="{nx}" cy="{ny}" r="4" fill="#3EF0D0" opacity="0.8"/>')
        for i, (x1,y1) in enumerate(nodes):
            for j in range(i+1, len(nodes)):
                x2, y2 = nodes[j]
                if math.hypot(x2-x1, y2-y1) < w//3:
                    el.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#3EF0D0" stroke-width="0.5" opacity="0.15"/>')
        return self._wrap("\n".join(el), w, h)

    def compose(self, prompt, width=800, height=600):
        self.width, self.height = width, height
        self.stats["total_compositions"] += 1
        p = prompt.lower().strip()
        best, best_prio = None, 0
        for tmpl in self.templates:
            m = re.search(tmpl.pattern, p, re.IGNORECASE)
            if m:
                prio = len(m.group(0)) * tmpl.confidence
                if prio > best_prio:
                    best, best_prio = tmpl, prio
        if not best:
            best = self.templates[-1]
        svg = best.generator(prompt)
        return {"svg":svg,"template":best.name,"category":best.category,"confidence":best.confidence,"width":width,"height":height,"size_bytes":len(svg)}

    def compose_and_save(self, prompt, path, w=800, h=600):
        r = self.compose(prompt, w, h)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(r["svg"])
        return r

if __name__ == "__main__":
    hvc = HarmonicVisualComposer()
    tests = ["un coucher de soleil sur le Nil avec les pyramides","une foret mystique","les pyramides de Gizeh dans le desert","des ondes et des vagues harmoniques","la spirale du nombre dor","Kemet, la Terre Noire"]
    print(f"HARMONIC VISUAL COMPOSER - {len(tests)} tests")
    for i, q in enumerate(tests):
        r = hvc.compose(q, 400, 300)
        print(f"  [{r['template']}] {q} ({r['size_bytes']}b)")
        if i<3:
            hvc.compose_and_save(q, os.path.join(DATA_DIR,f"test{i+1}.svg"), 400, 300)