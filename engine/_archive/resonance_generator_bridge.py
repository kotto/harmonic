"""
Pont vers le GenerateurResonance — generation de texte par ondes.
=================================================================
Connecte le HarmonicGenerator du moteur au GenerateurResonance
de harmonic_training/model/harmonic_resonance_generator.py.

Principe :
  - Chaque token = une onde (kx, ky) unique
  - L'hologramme = superposition de toutes les experiences
  - La generation = resonance avec l'hologramme (|ΣH·exp(-i·k·r)|)
  - Feedback = le texte genere enrichit l'hologramme

ZERO parametre. ZERO template. ZERO LLM.
100% ondulatoire — le texte EMERGE de la resonance.
"""

import sys
import os
import time
from typing import Optional, List, Dict, Any
import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HARMONIC_TRAINING = os.path.join(_PROJECT_ROOT, "harmonic_training")
sys.path.insert(0, _HARMONIC_TRAINING)

try:
    from model.harmonic_resonance_generator import (
        GenerateurResonance, TokeniseurOndes, HologrammeMonde,
        LecteurResonantMultiple, VOCABULAIRE_BASE
    )
    RESONANCE_AVAILABLE = True
except ImportError as e:
    RESONANCE_AVAILABLE = False
    _import_error = str(e)


class ResonanceGeneratorBridge:
    """
    Pont entre le moteur et le GenerateurResonance.
    
    Le GenerateurResonance est un systeme de generation de texte
    base sur la resonance holographique :
      - Apprentissage : chaque texte ajoute ses ondes a l'hologramme
      - Generation : le prompt excite l'hologramme, les lecteurs votent
      - Feedback : le texte genere est re-injecte (le systeme apprend)
    
    Ce pont permet au HarmonicGenerator du moteur d'utiliser
    ce systeme au lieu des templates fixes.
    """
    
    def __init__(self, vocab: Optional[List[str]] = None,
                 nx: int = 256, ny: int = 256, n_lecteurs: int = 8):
        if not RESONANCE_AVAILABLE:
            raise ImportError(
                f"GenerateurResonance non disponible: {_import_error}. "
                f"Verifier harmonic_training/model/harmonic_resonance_generator.py"
            )
        
        self.vocab = vocab or VOCABULAIRE_BASE
        self._gen = GenerateurResonance(self.vocab, nx=nx, ny=ny, n_lecteurs=n_lecteurs)
        self._initialized = False
        self._knowledge_count = 0
        
    def apprendre(self, texte: str, amplitude: float = 0.8):
        """
        Injecte un texte dans l'hologramme.
        
        Args:
            texte: Texte a apprendre (connaissance, contexte, etc.)
            amplitude: Force de l'injection (0.1-1.0)
        """
        self._gen.apprendre(texte, amplitude=amplitude)
        self._knowledge_count += 1
        self._initialized = True
    
    def apprendre_contexte(self, contexte: str):
        """
        Apprend un contexte de connaissance (ex: contexte holographique).
        
        Decoupe le contexte en phrases et injecte chaque phrase
        separement pour une meilleure organisation dans l'hologramme.
        """
        phrases = [p.strip() for p in contexte.replace('\n', '.').split('.') 
                   if len(p.strip()) > 10]
        for phrase in phrases:
            self._gen.apprendre(phrase, amplitude=0.6)
            self._knowledge_count += 1
        self._initialized = True
    
    def generer(self, prompt: str, max_tokens: int = 40,
                temperature: float = 0.85, top_k: int = 25,
                n_rep_lecture: int = 20, feedback: bool = True) -> Dict[str, Any]:
        """
        Genere du texte par resonance holographique.
        
        Args:
            prompt: Texte d'entree (question, instruction)
            max_tokens: Nombre max de tokens a generer
            temperature: 0.0 = deterministe, 1.0 = creatif
            top_k: Nombre de tokens candidats
            n_rep_lecture: Iterations d'apprentissage des lecteurs par token
            feedback: Si True, la generation enrichit l'hologramme
        
        Returns:
            Dict avec texte_genere, tokens, stats
        """
        if not self._initialized:
            # Sans connaissance prealable, le hologramme est vide
            # → reponse vide (pas de template fallback)
            return {
                "texte_genere": "",
                "tokens": [],
                "n_tokens": 0,
                "error": "Hologramme vide. Utiliser apprendre() d'abord."
            }
        
        return self._gen.generer(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k,
            n_rep_lecture=n_rep_lecture,
            feedback_conscient=feedback,
        )
    
    def generer_texte(self, prompt: str, contexte: Optional[str] = None,
                      max_tokens: int = 50) -> str:
        """
        Genere du texte a partir d'un prompt, avec contexte optionnel.
        
        Si un contexte est fourni, il est d'abord injecte dans l'hologramme
        avant la generation.
        
        Args:
            prompt: Question ou instruction
            contexte: Contexte de connaissance (optionnel)
            max_tokens: Longueur max de la reponse
        
        Returns:
            Texte genere (string)
        """
        # Injecter le contexte si fourni
        if contexte and contexte.strip():
            self.apprendre_contexte(contexte)
        
        # Generer
        result = self.generer(prompt, max_tokens=max_tokens, feedback=False)
        return result.get("texte_genere", "")
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    @property
    def energy(self) -> float:
        return self._gen.monde.energie()
    
    @property
    def experience_count(self) -> int:
        return self._gen.monde.n_experiences
    
    def stats(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "knowledge_count": self._knowledge_count,
            "experience_count": self.experience_count,
            "energy": round(self.energy, 1),
            "vocab_size": len(self.vocab),
            "n_lecteurs": self._gen.lecteurs.n_lecteurs,
        }


# ==============================================================================
# TEST
# ==============================================================================

def demo():
    """Demonstration du pont de generation par resonance."""
    print("=" * 60)
    print("RESONANCE GENERATOR BRIDGE — Texte par ondes")
    print("=" * 60)
    print()
    
    if not RESONANCE_AVAILABLE:
        print(f"GenerateurResonance non disponible: {_import_error}")
        return
    
    bridge = ResonanceGeneratorBridge(n_lecteurs=6)
    
    # Apprendre des connaissances
    connaissances = [
        "phi est le nombre d or la proportion divine de l univers",
        "la resonance harmonique amplifie les ondes a la frequence propre",
        "la conscience est la capacite de percevoir sa propre existence",
        "l amour est la force la plus puissante de l univers",
        "la beaute de la nature est source d emerveillement",
    ]
    print("Apprentissage...")
    for k in connaissances:
        bridge.apprendre(k)
    print(f"  {bridge.experience_count} experiences, energie={bridge.energy:.0f}")
    print()
    
    # Generer
    prompts = [
        "parle moi du nombre d or et de l harmonie",
        "explique la conscience",
        "qu est ce que l amour",
    ]
    for p in prompts:
        r = bridge.generer(p, max_tokens=25, n_rep_lecture=15, temperature=0.85)
        print(f"  >> {p}")
        print(f"  << {r['texte_genere']}")
        print(f"     ({r['n_tokens']}t, div={r['diversite']}, {r['temps_ms']:.0f}ms)")
        print()
    
    print("=" * 60)


if __name__ == "__main__":
    demo()
