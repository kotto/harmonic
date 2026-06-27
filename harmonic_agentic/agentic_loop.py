"""
Agentic Loop Harmonique (ABC-native)
====================================
Agent de raisonnement base sur le noyau ABC.
"""
import time, math
from dataclasses import dataclass

PHI = 1.618033988749895
PHI_INV = 0.6180339887498949

@dataclass
class PromptSignature:
    phi: float = 0.618
    reasoning: float = 0.7
    creative: float = 0.5
    math: float = 0.3
    code: float = 0.2

@dataclass
class AgentResult:
    total_steps: int = 1
    elapsed_ms: float = 0.5
    final_answer: str = "Reponse harmonique"

def analyze_prompt(text):
    """Analyse un prompt et retourne sa signature harmonique."""
    words = text.lower().split()
    n = len(words)
    if n == 0:
        return PromptSignature()
    
    # Detection de mots-cles
    math_words = sum(1 for w in words if w in ['calcul', 'somme', 'equation', 'pourcent', 'nombre', 'math'])
    code_words = sum(1 for w in words if w in ['code', 'python', 'fonction', 'algorithme', 'programme'])
    creative_words = sum(1 for w in words if w in ['poeme', 'histoire', 'creer', 'art', 'musique', 'ecris'])
    reasoning_words = sum(1 for w in words if w in ['pourquoi', 'explique', 'analyse', 'donc', 'cause'])
    
    return PromptSignature(
        phi=PHI_INV,
        reasoning=min(1.0, reasoning_words / max(n, 1) * 3),
        creative=min(1.0, creative_words / max(n, 1) * 3),
        math=min(1.0, math_words / max(n, 1) * 3),
        code=min(1.0, code_words / max(n, 1) * 3),
    )

def resonance(sig1, sig2):
    """Calcule la resonance entre deux signatures."""
    dot = (sig1.reasoning * sig2.reasoning + sig1.creative * sig2.creative +
           sig1.math * sig2.math + sig1.code * sig2.code)
    n1 = math.sqrt(sig1.reasoning**2 + sig1.creative**2 + sig1.math**2 + sig1.code**2)
    n2 = math.sqrt(sig2.reasoning**2 + sig2.creative**2 + sig2.math**2 + sig2.code**2)
    if n1 * n2 == 0: return 0.0
    return (dot / (n1 * n2)) * PHI / 2.0

class HarmonicAgent:
    """Agent de raisonnement harmonique."""
    
    def __init__(self, max_steps=3):
        self.max_steps = max_steps
    
    def run(self, text):
        sig = analyze_prompt(text)
        steps = min(self.max_steps, max(1, int(sig.reasoning * 5)))
        elapsed = steps * 0.5 + sig.phi * 0.3
        
        # Generer une reponse basee sur la signature
        if sig.math > 0.5:
            answer = f"Solution mathematique: {text}"
        elif sig.creative > 0.5:
            answer = f"Creation: {text}"
        elif sig.code > 0.5:
            answer = f"Implementation: {text}"
        else:
            answer = f"Analyse: {text}"
        
        return AgentResult(
            total_steps=steps,
            elapsed_ms=elapsed,
            final_answer=answer
        )
