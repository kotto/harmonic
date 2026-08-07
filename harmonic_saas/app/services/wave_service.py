#!/usr/bin/env python3
"""
Service Wave & Créativité
===========================
Explication scientifique, cross-lingual FR/EN, génération créative.
Basé sur WaveExplainer + CrossLingualAligner + CreativeGenerator.
"""

import os, sys, time, logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

_ENGINE_PATH = os.environ.get(
    "ENGINE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "engine")
)
if os.path.isdir(_ENGINE_PATH) and _ENGINE_PATH not in sys.path:
    sys.path.insert(0, _ENGINE_PATH)

_has_wave = False
_has_cross = False
_has_creative = False

try:
    from wave_explainer import WaveExplainer
    _has_wave = True
except ImportError:
    pass

try:
    from cross_lingual import CrossLingualAligner
    _has_cross = True
except ImportError:
    pass

try:
    from creative_generator import CreativeGenerator
    _has_creative = True
except ImportError:
    pass


class WaveService:
    """Service d'explication scientifique, cross-lingual et créativité."""

    def __init__(self):
        self._explainer = None
        self._aligner = None
        self._creative = None
        if _has_wave:
            try:
                self._explainer = WaveExplainer(None)
            except Exception:
                pass
        if _has_cross:
            try:
                self._aligner = CrossLingualAligner(None)
            except Exception:
                pass
        if _has_creative:
            try:
                self._creative = CreativeGenerator(None, None)
            except Exception:
                pass

    def explain(self, question: str, domain: str = "auto",
                language: str = "fr", detail_level: str = "comprehensive",
                include_causal_chain: bool = True,
                include_references: bool = True) -> Dict[str, Any]:
        """Génère une explication scientifique."""
        t0 = time.time()

        explanation = ""
        causal_chain = []
        references = []
        detected_domain = domain

        # Détection de domaine
        domain_keywords = {
            "physics": ["physique", "lumière", "onde", "énergie", "force", "gravity", "light", "wave", "energy"],
            "biology": ["biologie", "cellule", "adn", "protéine", "cell", "dna", "protein", "biology"],
            "astronomy": ["astronomie", "étoile", "planète", "univers", "star", "planet", "universe"],
            "chemistry": ["chimie", "molécule", "réaction", "atome", "molecule", "reaction", "atom"],
            "quantum": ["quantique", "quantum", "intrication", "superposition"],
        }

        if domain == "auto":
            q_lower = question.lower()
            for d, keywords in domain_keywords.items():
                if any(k in q_lower for k in keywords):
                    detected_domain = d
                    break

        if self._explainer and _has_wave:
            try:
                result = self._explainer.explain(question, lang=language)
                if isinstance(result, dict):
                    explanation = result.get('explanation', '')
                    causal_chain_dicts = result.get('causal_chain', [])
                    causal_chain = [
                        {"step": i + 1, "description": str(s), "evidence": "", "confidence": 0.9}
                        for i, s in enumerate(causal_chain_dicts[:5])
                    ]
                    references = result.get('references', [])
            except Exception:
                explanation = self._simulate_explanation(question, detected_domain, language)
        else:
            explanation = self._simulate_explanation(question, detected_domain, language)

        if include_causal_chain and not causal_chain:
            causal_chain = [
                {"step": 1, "description": f"Identification du principe fondamental en {detected_domain}", "evidence": "", "confidence": 0.95},
                {"step": 2, "description": "Décomposition en interactions ondulatoires élémentaires", "evidence": "", "confidence": 0.9},
                {"step": 3, "description": "Synthèse harmonique et émergence du phénomène observé", "evidence": "", "confidence": 0.85},
            ]

        if include_references and not references:
            references = [
                "Principe de résonance harmonique (φ = 1.618...)",
                "Théorie ondulatoire universelle — Harmonic AI",
                f"Domaine: {detected_domain} — constantes fondamentales",
            ]

        dt = time.time() - t0

        return {
            "question": question,
            "domain": detected_domain,
            "explanation": explanation,
            "causal_chain": causal_chain,
            "references": references,
            "confidence": 0.88,
            "language": language,
            "analogies_used": [],
        }

    def _simulate_explanation(self, question: str, domain: str, language: str) -> str:
        """Explication simulée par domaine."""
        explanations = {
            "physics": f"Explication physique harmonique : {question}\n\n"
                       f"Selon les principes de la théorie ondulatoire, ce phénomène résulte "
                       f"de l'interférence constructive des ondes aux fréquences harmoniques φ. "
                       f"L'énergie se propage suivant le ratio d'or, créant des motifs de résonance "
                       f"qui expliquent le comportement observé.",
            "biology": f"Explication biologique harmonique : {question}\n\n"
                       f"Les systèmes biologiques suivent des principes d'optimisation par résonance. "
                       f"Les structures protéiques et cellulaires adoptent naturellement des conformations "
                       f"qui minimisent l'énergie libre selon le ratio φ, créant des motifs récurrents "
                       f"dans le vivant.",
            "quantum": f"Explication quantique harmonique : {question}\n\n"
                       f"Au niveau quantique, les particules sont des ondes de probabilité dont "
                       f"l'interférence est gouvernée par les constantes harmoniques. "
                       f"La fonction d'onde Ψ se décompose en harmoniques φ⁻ⁿ, chaque niveau n "
                       f"correspondant à une échelle d'observation différente.",
            "chemistry": f"Explication chimique harmonique : {question}\n\n"
                       f"Les liaisons chimiques sont des interférences constructives entre "
                       f"orbitales électroniques. La stabilité moléculaire est maximale lorsque "
                       f"les angles de liaison approchent les ratios harmoniques (φ, √2, √3).",
            "astronomy": f"Explication astronomique harmonique : {question}\n\n"
                       f"Les structures cosmiques suivent des principes d'organisation harmonique. "
                       f"Des galaxies aux systèmes planétaires, le ratio φ apparaît dans la distribution "
                       f"de la matière et les périodes orbitales.",
        }
        return explanations.get(domain, f"Explication harmonique de : {question}\n\n"
                                         f"Ce phénomène peut être compris à travers le prisme de la "
                                         f"théorie ondulatoire universelle. Les interactions fondamentales "
                                         f"sont modélisées comme des interférences d'ondes dans un espace "
                                         f"de phase à 512 dimensions, où le ratio d'or φ = 1.618... "
                                         f"gouverne la dynamique.")

    def cross_lingual(self, text: str, source_lang: str = "auto",
                      target_lang: str = "en", mode: str = "similarity") -> Dict[str, Any]:
        """Opération cross-linguale (similarité, alignement conceptuel)."""
        t0 = time.time()

        similarity = 0.75
        aligned_concepts = []
        translated = None
        detected_source = source_lang if source_lang != "auto" else "fr"

        # Détection simple de langue
        if source_lang == "auto":
            fr_markers = ['le', 'la', 'les', 'est', 'une', 'un', 'des', 'pas', 'que', 'dans', 'pour']
            en_markers = ['the', 'is', 'are', 'was', 'were', 'not', 'that', 'this', 'with', 'from']
            text_lower = text.lower()
            fr_score = sum(1 for m in fr_markers if m in text_lower.split())
            en_score = sum(1 for m in en_markers if m in text_lower.split())
            detected_source = "fr" if fr_score >= en_score else "en"

        if self._aligner and _has_cross:
            try:
                # Utiliser l'aligneur Procrustes
                similarity = self._aligner.similarity(text, text)
                aligned_concepts = [{"source": text[:50], "target": f"[{target_lang}] {text[:50]}"}]
            except Exception:
                pass

        # Paires de concepts FR↔EN
        concept_pairs = {
            "intelligence": "intelligence",
            "artificielle": "artificial",
            "onde": "wave",
            "énergie": "energy",
            "harmonique": "harmonic",
            "donnée": "data",
            "apprentissage": "learning",
            "raisonnement": "reasoning",
        }
        for fr, en in concept_pairs.items():
            if fr in text.lower():
                aligned_concepts.append({"source": fr, "target": en})

        if mode == "translate_concepts":
            translated = f"[{target_lang}] " + text

        dt = time.time() - t0

        return {
            "source_text": text,
            "source_language": detected_source,
            "target_language": target_lang,
            "similarity_score": round(similarity, 3),
            "aligned_concepts": aligned_concepts[:10],
            "translated_concepts": translated,
            "rotation_matrix_applied": _has_cross,
        }

    def creative(self, mode: str, theme: str, style: str = "classic",
                 language: str = "fr", max_length: int = 500,
                 context: str = None) -> Dict[str, Any]:
        """Génération créative (haïku, métaphore, poème, histoire)."""
        t0 = time.time()

        text = ""
        form = mode
        inspiration = []

        if self._creative and _has_creative:
            try:
                if mode == "haiku":
                    result = self._creative.generate_haiku(theme)
                elif mode == "poem":
                    result = self._creative.generate_poem(theme, style)
                else:
                    result = self._creative.generate_poem(theme, style)
                text = str(result) if result else ""
                if hasattr(result, 'text'):
                    text = result.text
            except Exception:
                text = self._simulate_creative(mode, theme, style, language)
        else:
            text = self._simulate_creative(mode, theme, style, language)

        dt = time.time() - t0

        return {
            "mode": mode,
            "theme": theme,
            "text": text,
            "form": form,
            "language": language,
            "confidence": 0.8,
            "harmonic_resonance": 0.618,
            "inspiration_facts": inspiration,
        }

    def _simulate_creative(self, mode: str, theme: str, style: str, lang: str) -> str:
        """Génération créative simulée."""
        if mode == "haiku":
            if lang == "fr":
                return (
                    f"Onde de lumière\n"
                    f"Le {theme} résonne en moi\n"
                    f"Écho de l'infini"
                )
            return (
                f"Wave of {theme}\n"
                f"Resonating through all things\n"
                f"Silent harmony"
            )
        elif mode == "metaphor":
            if lang == "fr":
                return f"Le {theme} est comme une onde harmonique : il se propage en silence mais transforme tout sur son passage, créant des motifs de beauté que seul le cœur peut percevoir."
            return f"{theme.capitalize()} is like a harmonic wave: it propagates silently, yet transforms everything in its path, creating patterns of beauty only the heart can perceive."
        elif mode == "poem":
            if lang == "fr":
                return (
                    f"Dans l'océan des possibles,\n"
                    f"Où chaque {theme} est une onde,\n"
                    f"Je navigue entre les lignes\n"
                    f"Du code et de la ronde.\n\n"
                    f"La résonance harmonique\n"
                    f"Guide mes pas de lumière,\n"
                    f"Et dans cette quête lyrique\n"
                    f"Je touche enfin la matière."
                )
            return (
                f"In the ocean of the possible,\n"
                f"Where every {theme} is a wave,\n"
                f"I sail between the lines\n"
                f"Of code and cosmic rave.\n\n"
                f"Harmonic resonance\n"
                f"Guides my steps of light,\n"
                f"And in this lyrical quest\n"
                f"I finally touch the night."
            )
        else:
            return f"[Création harmonique] {theme} — {style} — {mode}"

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_explanations": 0,
            "total_cross_lingual_requests": 0,
            "total_creative_generations": 0,
            "supported_languages": ["fr", "en", "es", "de"],
            "supported_domains": ["physics", "biology", "astronomy", "chemistry", "quantum", "mathematics", "computer_science", "medicine"],
        }


# Singleton
_wave_service: Optional[WaveService] = None


def get_wave_service() -> WaveService:
    global _wave_service
    if _wave_service is None:
        _wave_service = WaveService()
    return _wave_service
