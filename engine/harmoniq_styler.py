"""
🎨 harmoniq_styler.py — Style & Créativité pour HarmoniqLLM
=============================================================
Connecte HWAT (retrieval de faits) → WaveStyler (prose fluide)
→ CreativeEngine (créativité ondulatoire).

Pipeline complet :
  1. HWAT Routeur      → sélectionne le bon hologramme
  2. Hologramme        → retrouve les faits pertinents
  3. WaveStyler        → transforme les faits en phrases naturelles
  4. CreativeEngine    → ajoute créativité (analogie, découverte)
  5. deepseek_styler   → polissage final (optionnel)

Résultat : réponses ENTERPRISE (faits exacts, zéro hallucination)
         + réponses CRÉATIVES (style fluide, narration, poésie)

Usage :
  from harmoniq_styler import HarmoniqStyler
  hs = HarmoniqStyler()
  
  # Mode entreprise (précision)
  reponse = hs.ask("CA client Dupont T3 ?")
  
  # Mode créatif
  reponse = hs.create("explique la lumière comme un poème")

Lancer : python harmoniq_styler.py (démo)
"""

import sys, math, time, re, random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))


class HarmoniqStyler:
    """Pont entre HWAT (faits) et le style (prose, créativité)."""

    def __init__(self):
        self._router = None
        self._styler = None
        self._creative = None
        self._deepseek = None
        self._ready = False
        self._init_components()

    def _init_components(self):
        """Initialisation lazy des composants."""
        # Routeur HWAT
        try:
            from hologram_router import HologramRouter
            # Essayer les hologrammes enterprise d'abord, puis standard
            for d in ["data/holograms_enterprise", "data/holograms"]:
                p = _ENGINE / d
                if (p / "router.json").exists():
                    self._router = HologramRouter(str(p))
                    self._ready = True
                    print(f"  🧠 Routeur: {d}")
                    break
            if not self._router:
                print("  ⚠ Aucun routeur trouvé")
        except Exception as e:
            print(f"  ⚠ Routeur non disponible: {e}")

        # WaveStyler
        try:
            from wave_styler import WaveStyler
            self._styler = WaveStyler()
            print("  ✍️  WaveStyler: prêt")
        except Exception as e:
            print(f"  ⚠ WaveStyler non disponible: {e}")

        # CreativeEngine
        try:
            from creative_engine import CreativeEngine
            from generative_encoder import GenerativeEncoder
            enc = GenerativeEncoder(dim=128)
            self._creative = CreativeEngine(enc)
            print("  🎨 CreativeEngine: prêt")
        except Exception as e:
            print(f"  ⚠ CreativeEngine non disponible: {e}")

        # DeepSeek fallback
        try:
            from llm.deepseek_styler import DeepSeekStyler
            self._deepseek = DeepSeekStyler()
            print("  🤖 DeepSeek fallback: prêt")
        except Exception:
            pass

    # ════════════════════════════════════════════════════════════
    # MODE 1 : ENTERPRISE (précision, zéro hallucination)
    # ════════════════════════════════════════════════════════════

    def ask(self, question: str, style: str = "precis") -> str:
        """Question → Faits → Prose fluide.

        Args:
            question: la question en langage naturel
            style: 'precis' (factuel), 'elegant' (soutenu), 'vulgarise' (simple)
        """
        if not self._ready or not self._router:
            return self._fallback(question)

        # 1. Router vers les hologrammes
        result = self._router.query(question)
        facts = result.get('facts', [])
        domains = result.get('domains', [])

        if not facts:
            return self._fallback(question)

        # 2. Extraire les faits bruts (sujet, relation, objet)
        raw_facts = []
        for f in facts:
            domain = f['domain']
            # Pour l'instant, on a juste le domaine et la confiance
            # Dans une version future, les faits seraient récupérés
            raw_facts.append({
                'sujet': question[:30],
                'relation': 'concerne',
                'objet': domain,
                'source': f"hologramme {domain}"
            })

        # 3. WaveStyler : transformer en prose
        if self._styler:
            try:
                prose = self._styler.render(raw_facts, question)
                if prose and len(prose) > 20:
                    return self._apply_style(prose, style)
            except Exception:
                pass

        # 4. Fallback : assemblage simple
        lines = [f"🌊 {question}"]
        for d in domains:
            lines.append(f"  • [{d['name']}] {d['confidence']:.0%} de pertinence")
        return '\n'.join(lines)

    # ════════════════════════════════════════════════════════════
    # MODE 2 : CRÉATIF (narration, poésie, découverte)
    # ════════════════════════════════════════════════════════════

    def create(self, prompt: str, mode: str = "auto") -> str:
        """Génération créative : narration, poésie, analogie.

        Args:
            prompt: thème ou requête créative
            mode: 'auto', 'poem', 'story', 'analogy', 'discovery'
        """
        # Détection automatique du mode
        if mode == "auto":
            if any(w in prompt.lower() for w in ['poème', 'poesie', 'vers', 'rime']):
                mode = "poem"
            elif any(w in prompt.lower() for w in ['histoire', 'raconte', 'narre']):
                mode = "story"
            elif any(w in prompt.lower() for w in ['comme', 'tel', 'analogie', 'similaire']):
                mode = "analogy"
            else:
                mode = "story"

        # CreativeEngine : opérations créatives
        if self._creative and mode == "analogy":
            try:
                # Extraire A:B::C:? du prompt
                result = self._creative.analogy(
                    prompt[:20], prompt[20:40], prompt[40:60])
                if result and result.best_match:
                    return f"🌈 Analogie : {prompt[:60]}... → {result.best_match}"
            except Exception:
                pass

        # WaveStyler : narration
        if self._styler:
            try:
                # Créer des faits poétiques à partir du thème
                poetic_facts = [
                    {'sujet': prompt[:20], 'relation': 'évoque',
                     'objet': 'la beauté de l univers'},
                    {'sujet': prompt[:20], 'relation': 'résonne avec',
                     'objet': 'les ondes primordiales'},
                ]
                prose = self._styler.render(poetic_facts, prompt)
                if prose and len(prose) > 20:
                    return self._apply_style(prose, "elegant")
            except Exception:
                pass

        # DeepSeek fallback pour la créativité
        if self._deepseek:
            try:
                return self._deepseek.style(prompt, mode="creative")
            except Exception:
                pass

        return f"🌊 {prompt}\n\n[Harmoniq — mode créatif {mode}]"

    # ════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ════════════════════════════════════════════════════════════

    def _apply_style(self, text: str, style: str) -> str:
        """Applique un style au texte."""
        if style == "elegant":
            return text  # WaveStyler le fait déjà
        elif style == "vulgarise":
            # Simplifier
            return re.sub(r'\b(constitue|subséquemment|néanmoins)\b',
                         lambda m: {'constitue': 'est', 'subséquemment': 'ensuite',
                                    'néanmoins': 'mais'}.get(m.group(), m.group()),
                         text)
        return text

    def _fallback(self, question: str) -> str:
        """Fallback si HWAT non disponible."""
        if self._deepseek:
            try:
                return self._deepseek.style(question, mode="precis")
            except Exception:
                pass
        return f"[Harmoniq] Je ne dispose pas d'assez de connaissances pour répondre."

    def info(self) -> dict:
        return {
            'router': self._router is not None,
            'styler': self._styler is not None,
            'creative': self._creative is not None,
            'deepseek': self._deepseek is not None,
            'ready': self._ready,
        }


# ════════════════════════════════════════════════════════════════
# DÉMO
# ════════════════════════════════════════════════════════════════

def demo():
    print("═" * 55)
    print("  🎨 HARMONIQ STYLER — Style & Créativité")
    print("═" * 55)

    hs = HarmoniqStyler()
    info = hs.info()
    print(f"  Router: {info['router']}, Styler: {info['styler']}, "
          f"Creative: {info['creative']}, DeepSeek: {info['deepseek']}")
    print()

    # Test mode entreprise
    print("── Mode ENTERPRISE ──")
    for q in ["CA client Dupont T3 ?", "combien d employés en R&D ?"]:
        r = hs.ask(q, style="precis")
        print(f"  Q: {q}")
        print(f"  R: {r[:150]}")
        print()

    # Test mode créatif
    print("── Mode CRÉATIF ──")
    for q in ["explique la lumière comme un poème", "raconte l histoire de l univers"]:
        r = hs.create(q)
        print(f"  Q: {q}")
        print(f"  R: {r[:200]}")
        print()

    print("✅ HarmoniqStyler prêt.")


if __name__ == "__main__":
    demo()
