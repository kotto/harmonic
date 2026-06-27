#!/usr/bin/env python3
"""
SCENE DETECTOR — Analyse sémantique d'un prompt visuel
========================================================
Décompose un prompt en langage naturel en spécifications de scène structurées :
type de scène, heure/jour, éléments, palette, angle de caméra.

Utilisé par HarmonicImageGenerator comme première étape du pipeline.

Usage :
  from scene_detector import SceneDetector
  sd = SceneDetector()
  spec = sd.detect("une pyramide dans le désert au coucher du soleil")
  # → SceneSpec(scene_type="pyramids_desert", time_of_day="sunset", ...)
"""

import re, json, os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

# ══════════════════════════════════════════════════════════════════════════
# SCENE SPECIFICATION
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class SceneSpec:
    """Spécification complète d'une scène visuelle."""
    scene_type: str = "sunset_water"       # Type principal de scène
    time_of_day: str = "day"               # "dawn", "day", "sunset", "night"
    elements: List[str] = field(default_factory=list)  # Objets détectés
    palette: str = "crepuscule"            # Palette de couleurs recommandée
    mood: str = "neutral"                  # "peaceful", "dramatic", "mystical"
    camera_angle: Tuple[float, float, float] = (0.0, 0.0, 100.0)  # pan, tilt, distance
    lighting_direction: Tuple[float, float] = (0.5, -1.0)  # Direction de la lumière
    confidence: float = 0.75
    style: str = "realiste"

# ══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASES
# ══════════════════════════════════════════════════════════════════════════

SCENE_TYPES = {
    "pyramids_desert": ["pyramide", "pyramid", "gizeh", "kheops", "sphinx", "kemet", "egypte antique"],
    "pyramids_nil": ["pyramide.*nil", "nil.*pyramide", "pyramid.*river", "pyramide.*fleuve"],
    "sunset_water": ["coucher.*(eau|mer|ocean|lac|fleuve)", "sunset.*water", "crepuscule.*(mer|eau)"],
    "sunset_desert": ["coucher.*desert", "sunset.*desert", "crepuscule.*(sable|dune)"],
    "mountains": ["montagne", "mountain", "sommet", "peak", "alpes", "himalaya", "chaine"],
    "forest": ["foret", "forest", "bois", "arbre", "tree", "jungle", "canopee", "sous-bois"],
    "beach": ["plage", "beach", "rivage", "cote", "tropical.*beach", "sable.*mer"],
    "night_sky": ["nuit", "night", "etoile", "star", "lune", "moon", "ciel.*nocturne"],
    "fields": ["champ", "field", "prairie", "meadow", "fleur", "flower", "lave?nde", "tournesol"],
    "temple": ["temple", "karnak", "colonne", "pillar", "ruine", "acropole", "parthenon"],
    "abstract": ["abstrait", "geometric", "fractal", "spiral", "phi", "fibonacci", "onde", "resonance"],
    "city": ["ville", "city", "urbain", "skyline", "gratte.ciel", "metropole", "ruelle"],
    "village": ["village", "case", "hutte", "paillote", "africain.*village"],
    "savanna": ["savane", "savanna", "afrique.*animaux", "serengeti", "baobab", "acacia"],
    "desert": ["desert", "sable", "dune", "aride", "sahara", "cactus"],
}

TIME_OF_DAY = {
    "dawn": ["aube", "dawn", "matin", "morning", "lever.*soleil", "sunrise"],
    "day": ["jour", "day", "midi", "noon", "apres.midi", "afternoon"],
    "sunset": ["coucher", "sunset", "crepuscule", "soir", "evening", "golden hour"],
    "night": ["nuit", "night", "minuit", "midnight", "nocturne", "noir", "obscur"],
}

MOODS = {
    "peaceful": ["calme", "peaceful", "serene", "tranquille", "doux", "paisible", "zen"],
    "dramatic": ["dramatique", "epique", "intense", "orage", "storm", "tempete", "tonnerre"],
    "mystical": ["mystique", "mystical", "magique", "fantastique", "surnaturel", "etheré"],
    "melancholic": ["melancolique", "triste", "sombre", "dark", "brumeux", "foggy", "pluie"],
    "joyful": ["joyeux", "coloré", "vif", "bright", "festif", "celebration", "heureux"],
}

# ══════════════════════════════════════════════════════════════════════════
# SCENE DETECTOR
# ══════════════════════════════════════════════════════════════════════════

class SceneDetector:
    """
    Analyse un prompt en langage naturel et le convertit en SceneSpec structurée.
    """

    def __init__(self):
        """Initialise le détecteur avec ses bases de connaissances."""
        pass

    def detect(self, prompt: str) -> SceneSpec:
        """
        Extrait la spécification de scène complète d'un prompt.
        
        Args:
            prompt: texte en langage naturel
            
        Returns:
            SceneSpec avec tous les paramètres de la scène
        """
        p = prompt.lower().strip()
        
        # Détecter le type de scène
        scene_type, scene_confidence = self._detect_scene_type(p)
        
        # Détecter l'heure / lumière
        time_of_day, time_confidence = self._detect_time_of_day(p)
        
        # Détecter les éléments/objets
        elements = self._detect_elements(p)
        
        # Sélectionner la palette
        palette = self._select_palette(scene_type, time_of_day)
        
        # Détecter le mood
        mood = self._detect_mood(p)
        
        # Déterminer l'angle de caméra
        camera_angle = self._detect_camera_angle(p)
        
        # Direction de l'éclairage
        lighting = self._time_to_lighting(time_of_day)
        
        # Style visuel
        style = self._detect_style(p)
        
        # Confiance globale
        confidence = (scene_confidence + time_confidence) / 2
        
        return SceneSpec(
            scene_type=scene_type,
            time_of_day=time_of_day,
            elements=elements,
            palette=palette,
            mood=mood,
            camera_angle=camera_angle,
            lighting_direction=lighting,
            confidence=confidence,
            style=style,
        )

    def _detect_scene_type(self, prompt: str) -> Tuple[str, float]:
        """
        Détecte le type de scène principal.
        Score basé sur le nombre de mots-clés correspondants × priorité.
        """
        scores = {}
        for scene_type, keywords in SCENE_TYPES.items():
            score = 0
            for kw in keywords:
                if re.search(kw, prompt, re.IGNORECASE):
                    score += 1.0  # Match simple
                    # Bonus pour match exact
                    if re.search(r'\b' + re.escape(kw) + r'\b', prompt, re.IGNORECASE):
                        score += 0.5
            if score > 0:
                scores[scene_type] = score
        
        if not scores:
            return ("sunset_water", 0.3)  # Default fallback
        
        best = max(scores, key=scores.get)
        confidence = min(1.0, scores[best] / 3.0)  # Normaliser
        return (best, confidence)

    def _detect_time_of_day(self, prompt: str) -> Tuple[str, float]:
        """Détecte l'heure/lumière de la scène."""
        scores = {}
        for time_key, keywords in TIME_OF_DAY.items():
            score = sum(1 for kw in keywords if re.search(kw, prompt, re.IGNORECASE))
            if score > 0:
                scores[time_key] = score
        
        if not scores:
            return ("day", 0.5)  # Default
        
        best = max(scores, key=scores.get)
        confidence = min(1.0, scores[best] / 2.0)
        return (best, confidence)

    def _detect_elements(self, prompt: str) -> List[str]:
        """
        Détecte les éléments/objets spécifiques dans le prompt.
        Utilise une approche par pattern matching.
        """
        element_patterns = {
            "pyramide": r'\b(?:pyramide|pyramid|kheops|gizeh|sphinx)\b',
            "nil": r'\b(?:nil|nile|fleuve|river)\b',
            "soleil": r'\b(?:soleil|sun)\b',
            "lune": r'\b(?:lune|moon)\b',
            "etoile": r'\b(?:etoile|star|constellation)\b',
            "arbre": r'\b(?:arbre|tree|foret|forest|bois)\b',
            "montagne": r'\b(?:montagne|mountain|sommet|peak)\b',
            "eau": r'\b(?:eau|water|mer|ocean|lac|riviere|fleuve)\b',
            "desert": r'\b(?:desert|sable|dune|aride)\b',
            "temple": r'\b(?:temple|colonne|ruine|obelisque)\b',
            "nuage": r'\b(?:nuage|cloud|brume|brouillard)\b',
            "animal": r'\b(?:animal|oiseau|lion|girafe|elephant|cheval)\b',
            "humain": r'\b(?:personne|homme|femme|enfant|silhouette)\b',
        }
        
        elements = []
        for element, pattern in element_patterns.items():
            if re.search(pattern, prompt, re.IGNORECASE):
                elements.append(element)
        
        return elements if elements else ["paysage"]  # At least one element

    def _select_palette(self, scene_type: str, time_of_day: str) -> str:
        """
        Sélectionne la palette de couleurs la plus appropriée.
        Combine le type de scène et l'heure.
        """
        # Priorité à l'heure si elle est spécifique
        time_palettes = {
            "dawn": "aube",
            "sunset": "crepuscule",
            "night": "nuit",
            "day": None,  # Use scene-based palette
        }
        
        if time_palettes.get(time_of_day):
            return time_palettes[time_of_day]
        
        # Fallback basé sur le type de scène
        scene_palettes = {
            "pyramids_desert": "desert",
            "pyramids_nil": "nil",
            "mountains": "montagne",
            "forest": "foret",
            "beach": "mer",
            "night_sky": "nuit",
            "fields": "printemps",
            "desert": "desert",
            "savanna": "savane",
            "temple": "kemet",
        }
        
        return scene_palettes.get(scene_type, "crepuscule")

    def _detect_mood(self, prompt: str) -> str:
        """Détecte l'ambiance/mood de la scène."""
        scores = {}
        for mood, keywords in MOODS.items():
            score = sum(1 for kw in keywords if re.search(kw, prompt, re.IGNORECASE))
            if score > 0:
                scores[mood] = score
        
        return max(scores, key=scores.get) if scores else "neutral"

    def _detect_camera_angle(self, prompt: str) -> Tuple[float, float, float]:
        """
        Détecte l'angle de caméra souhaité.
        (pan horizontal degrés, tilt vertical degrés, distance)
        """
        pan, tilt, distance = 0.0, 0.0, 100.0
        
        # Détection horizontale
        if re.search(r'\b(?:gauche|left)\b', prompt, re.IGNORECASE):
            pan = -30.0
        elif re.search(r'\b(?:droite|right)\b', prompt, re.IGNORECASE):
            pan = 30.0
        elif re.search(r'\b(?:profil|side)\b', prompt, re.IGNORECASE):
            pan = 90.0
        elif re.search(r'\b(?:face|front)\b', prompt, re.IGNORECASE):
            pan = 0.0
        
        # Détection verticale
        if re.search(r'\b(?:haut|top|dessus|above|plongee)\b', prompt, re.IGNORECASE):
            tilt = -20.0
        elif re.search(r'\b(?:bas|bottom|dessous|contre.plongee)\b', prompt, re.IGNORECASE):
            tilt = 20.0
        
        # Détection distance
        if re.search(r'\b(?:proche|close|gros plan|macro)\b', prompt, re.IGNORECASE):
            distance = 50.0
        elif re.search(r'\b(?:loin|far|panoramique|wide)\b', prompt, re.IGNORECASE):
            distance = 200.0
        elif re.search(r'\b(?:aerien|vue du ciel|satellite)\b', prompt, re.IGNORECASE):
            distance = 300.0
            tilt = -40.0
        
        return (pan, tilt, distance)

    def _time_to_lighting(self, time_of_day: str) -> Tuple[float, float]:
        """
        Convertit l'heure en direction d'éclairage (x, y).
        x = horizontal, y = vertical (négatif = haut)
        """
        lighting_map = {
            "dawn": (1.0, -0.3),      # Soleil bas à l'est
            "day": (0.5, -1.0),       # Soleil haut
            "sunset": (-1.0, -0.2),   # Soleil bas à l'ouest
            "night": (0.0, 1.0),      # Lune d'en haut
        }
        return lighting_map.get(time_of_day, (0.5, -1.0))

    def _detect_style(self, prompt: str) -> str:
        """Détecte le style visuel souhaité."""
        style_patterns = {
            "realiste": r'\b(?:realiste|photorealiste|photo|real)\b',
            "peinture": r'\b(?:peinture|painting|huile|impressionniste|van gogh|monet)\b',
            "croquis": r'\b(?:croquis|sketch|dessin|drawing|crayon|fusain)\b',
            "aquarelle": r'\b(?:aquarelle|watercolor|lavis)\b',
            "kemet": r'\b(?:kemet|egypte|hieroglyphe|fresque.*egypt|art.*egypt)\b',
            "geometrique": r'\b(?:geometric|abstrait|minimaliste|vectoriel)\b',
        }
        
        for style, pattern in style_patterns.items():
            if re.search(pattern, prompt, re.IGNORECASE):
                return style
        
        return "realiste"

    def get_scene_description(self, spec: SceneSpec) -> str:
        """Génère une description textuelle de la scène détectée."""
        return (
            f"Scene: {spec.scene_type} | "
            f"Time: {spec.time_of_day} | "
            f"Elements: {', '.join(spec.elements)} | "
            f"Palette: {spec.palette} | "
            f"Mood: {spec.mood} | "
            f"Camera: pan={spec.camera_angle[0]}° tilt={spec.camera_angle[1]}° dist={spec.camera_angle[2]} | "
            f"Style: {spec.style}"
        )


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sd = SceneDetector()
    
    tests = [
        "une pyramide dans le désert au coucher du soleil",
        "un temple égyptien mystique la nuit",
        "une forêt enchantée à l'aube",
        "des montagnes enneigées vues de loin",
        "une plage tropicale paisible",
        "la spirale du nombre d'or en style géométrique",
        "un village africain au crépuscule",
        "une ville futuriste vue du ciel",
        "un croquis du sphinx en noir et blanc",
        "le Nil au coucher du soleil avec les pyramides",
    ]
    
    print("=" * 60)
    print("SCENE DETECTOR - Test")
    print("=" * 60)
    
    for prompt in tests:
        spec = sd.detect(prompt)
        print(f"\nPrompt: '{prompt}'")
        print(f"  Scene: {spec.scene_type} ({spec.confidence:.0%})")
        print(f"  Time: {spec.time_of_day} | Palette: {spec.palette}")
        print(f"  Elements: {spec.elements}")
        print(f"  Mood: {spec.mood} | Style: {spec.style}")
        print(f"  Camera: pan={spec.camera_angle[0]} tilt={spec.camera_angle[1]} dist={spec.camera_angle[2]}")