"""
🔗 hwat_bridge.py — Pont entre HWAT et le pipeline HarmonicBrain
==================================================================
Intègre le nouveau modèle HWAT (Harmonic Wavelet Attention Transformer)
dans le pipeline existant sans casser la rétrocompatibilité.

Usage dans harmonic_brain.py ou standalone :

  from hwat_bridge import HwatBridge
  bridge = HwatBridge()
  
  # Remplacer l'analyseur FFT globale par HWAT
  vector = bridge.encode("théorème de Pythagore")
  
  # Génération directe
  reponse = bridge.generate("explique la lumière")
  
  # Intégré au chat
  reponse = bridge.chat("Pourquoi le ciel est bleu ?")

Compatible : importe automatiquement le modèle HWAT si disponible,
sinon fallback sur l'encodeur existant (génératif + holographique).
"""

import sys, math, os
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

# Flag global
_HWAT_AVAILABLE = False
_HWAT_MODEL = None
_HWAT_TOKENIZER = None


def _try_load_hwat():
    """Charge HWAT une seule fois (lazy)."""
    global _HWAT_AVAILABLE, _HWAT_MODEL, _HWAT_TOKENIZER
    if _HWAT_MODEL is not None:
        return True
    try:
        from hwat_inference import load_hwat
        _HWAT_MODEL, _HWAT_TOKENIZER = load_hwat()
        _HWAT_AVAILABLE = True
        return True
    except Exception as e:
        print(f"  [HwatBridge] HWAT non disponible: {e}")
        _HWAT_AVAILABLE = False
        return False


class HwatBridge:
    """
    Pont entre HWAT (nouveau) et le pipeline existant.
    
    Méthodes principales :
      - encode(text) → np.ndarray  : vecteur contextuel [L, dim]
      - encode_pooled(text) → np.ndarray : vecteur moyenné [dim]
      - generate(prompt) → str     : génération de texte
      - chat(message) → str        : conversation (délégue au brain si HWAT léger)
      - is_available() → bool      : True si HWAT chargé
    """

    def __init__(self, auto_load: bool = True):
        self._loaded = False
        if auto_load:
            self._loaded = _try_load_hwat()

    @property
    def is_available(self) -> bool:
        return _HWAT_AVAILABLE

    def encode(self, text: str) -> np.ndarray:
        """Encode un texte → vecteurs par token."""
        if not _try_load_hwat():
            return self._fallback_encode(text)
        import torch
        ids = torch.tensor(_HWAT_TOKENIZER.encode(text), dtype=torch.long)
        if len(ids) == 0:
            return np.zeros((0, _HWAT_MODEL.embed.token_emb.weight.shape[1]))
        return _HWAT_MODEL.encode(ids)

    def encode_pooled(self, text: str) -> np.ndarray:
        """Encode → un seul vecteur (mean pooling)."""
        vecs = self.encode(text)
        if vecs.shape[0] == 0:
            return np.zeros(vecs.shape[1])
        return vecs.mean(axis=0)

    def generate(self, prompt: str, max_tokens: int = 30,
                 temperature: float = 0.7) -> str:
        """Génère du texte."""
        if not _try_load_hwat():
            return self._fallback_generate(prompt)
        from hwat_inference import generate as hwat_generate
        return hwat_generate(prompt, max_tokens=max_tokens,
                            temperature=temperature)

    def chat(self, message: str) -> str:
        """Réponse conversationnelle.

        Priorité : HWAT → HarmonicBrain (fallback riche) → règle simple.
        """
        # Essayer HWAT d'abord
        if _try_load_hwat():
            try:
                # Prompt système pour orienter la génération
                prompt = f"question: {message}\nreponse:"
                return self.generate(prompt, max_tokens=50, temperature=0.7)
            except Exception:
                pass

        # Fallback : utiliser le pipeline existant
        return self._fallback_chat(message)

    def _fallback_encode(self, text: str) -> np.ndarray:
        """Fallback : encodeur génératif existant."""
        try:
            from generative_encoder import GenerativeEncoder
            enc = GenerativeEncoder(dim=64)
            return enc.encode(text).reshape(1, -1)
        except Exception:
            return np.zeros(64)

    def _fallback_generate(self, prompt: str) -> str:
        """Fallback : HarmonicBrain ou réponse simple."""
        try:
            from harmonic_brain import HarmonicBrain
            brain = HarmonicBrain([])
            result = brain.process(prompt)
            return result.response if hasattr(result, 'response') else str(result)
        except Exception:
            return f"[HWAT non chargé] Je ne peux pas générer de réponse pour: {prompt[:50]}..."

    def _fallback_chat(self, message: str) -> str:
        """Fallback conversationnel."""
        try:
            from harmonic_engine import HarmonicResonanceEngine
            engine = HarmonicResonanceEngine()
            result = engine.chat(message)
            return result.get('response', str(result))
        except Exception:
            return self._fallback_generate(message)

    # --- Stats ---
    def info(self) -> Dict[str, Any]:
        if not _HWAT_AVAILABLE:
            return {"status": "HWAT non disponible"}
        return {
            "status": "OK",
            "params": sum(p.numel() for p in _HWAT_MODEL.parameters()),
            "dim": _HWAT_MODEL.embed.token_emb.weight.shape[1],
            "blocks": len(_HWAT_MODEL.blocks),
            "vocab": _HWAT_TOKENIZER.vocab_size,
        }


# ════════════════════════════════════════════════════════════════
# API GLOBALE (import direct)
# ════════════════════════════════════════════════════════════════

_bridge = None


def get_bridge() -> HwatBridge:
    global _bridge
    if _bridge is None:
        _bridge = HwatBridge()
    return _bridge


def hwat_encode(text: str) -> np.ndarray:
    return get_bridge().encode(text)


def hwat_generate(prompt: str, **kw) -> str:
    return get_bridge().generate(prompt, **kw)


def hwat_chat(message: str) -> str:
    return get_bridge().chat(message)


# ════════════════════════════════════════════════════════════════
# DÉMO
# ════════════════════════════════════════════════════════════════

def demo():
    print("═" * 55)
    print("  🔗 HWAT Bridge — Intégration au pipeline")
    print("═" * 55)

    bridge = HwatBridge()
    print(f"  HWAT disponible : {bridge.is_available}")
    if bridge.is_available:
        info = bridge.info()
        print(f"  Params : {info['params']:,}, "
              f"dim={info['dim']}, blocs={info['blocks']}")

    # Test encodage
    v = bridge.encode_pooled("théorème de Pythagore")
    print(f"  Encode → vecteur {v.shape} (norme={np.linalg.norm(v):.2f})")

    # Test génération
    print(f"\n  Générations :")
    for prompt in ["théorème de", "loi de la", "Einstein"]:
        gen = bridge.generate(prompt, max_tokens=15)
        print(f"  > {gen[:80]}")

    print(f"\n  ✅ Bridge opérationnel.")


if __name__ == "__main__":
    demo()
