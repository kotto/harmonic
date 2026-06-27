"""
Module Agentique Harmonique
===========================
Fournit les agents ABC-native pour le raisonnement harmonique.
"""
from .agentic_loop import HarmonicAgent, analyze_prompt, resonance, PromptSignature, AgentResult
from .voice_signature_7d import extract_voice_signature, VoiceSignature7D

__all__ = [
    "HarmonicAgent", "analyze_prompt", "resonance",
    "PromptSignature", "AgentResult",
    "extract_voice_signature", "VoiceSignature7D",
]
