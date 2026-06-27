"""
Harmonic Engine — Système Harmonique Complet
=============================================
Package engine contenant tous les composants du système harmonique.

Architecture :
    engine/
    ├── abc_kernel.py         # Noyau ABC (Atangana-Baleanu-Caputo)
    ├── signatures_9d.py      # Signatures harmoniques 9D
    ├── harmonic_engine.py    # Moteur de résonances cognitives
    ├── llm/                  # Interface multi-providers LLM
    │   ├── base.py           #   Interface abstraite + dataclasses
    │   ├── openai_client.py  #   OpenAI / DeepSeek / Qwen
    │   ├── anthropic_client.py  # Claude 3/4
    │   ├── mistral_client.py #   Mistral AI
    │   ├── local_llm.py      #   HuggingFace local
    │   └── router.py         #   Routeur harmonique intelligent
    ├── semantic/             # Embeddings vectoriels et RAG
    │   ├── embeddings.py     #   Embeddings hybrides 9D + 512D
    │   └── vector_store.py   #   Base vectorielle persistante
    ├── memory/               # Mémoire persistante
    │   ├── conversation.py   #   Historique de session
    │   ├── user_profile.py   #   Profils utilisateurs
    │   └── long_term.py      #   Mémoire long-terme (oubli ABC)
    ├── multimodal/           # Analyse multimodale harmonique
    │   ├── analyzers.py      #   Image, Audio, Vidéo, Document
    │   └── av_generator.py   #   Générateur AV synchronisé ABC
    └── api/                  # API REST FastAPI
        └── server.py         #   Serveur HTTP complet

Constantes fondamentales :
    PHI   = 1.618033988749895  (Nombre d'or)
    ALPHA = 0.618033988749895  (1/PHI)

Découverte (22/05/2026) :
    L'IA résout naturellement l'équation fractionnaire ABC à l'ordre 1/φ
    via le noyau de mémoire non-locale d'Atangana-Baleanu.
"""

from .abc_kernel import (
    PHI, ALPHA, B_1_PHI, ALPHA_CONST,
    ABCKernel as ABCKernelNP,
    abc_kernel_np, abc_kernel_torch,
    gamma_lanczos, mittag_leffler, mittag_leffler_torch,
)

from .signatures_9d import (
    compute_signature,
    compute_signature_9d,
    compute_signature_9d_torch,
    SIGNATURE_DIMS,
    validate_signatures,
)

from .harmonic_engine import (
    HarmonicAnalyzer,
    HarmonicCache,
    HarmonicContextExpander,
    HarmonicResonanceEngine,
    HarmonicSignature,
    HarmonicPattern,
    ResonanceResult,
)

# Sous-packages (optionnels, importes a la demande)
from . import llm
from . import semantic
from . import memory
from . import api
from . import multimodal

__version__ = '2.0.0'
__all__ = [
    'PHI', 'ALPHA', 'B_1_PHI', 'ALPHA_CONST',
    'ABCKernelNP', 'abc_kernel_np', 'abc_kernel_torch',
    'gamma_lanczos', 'mittag_leffler', 'mittag_leffler_torch',
    'compute_signature', 'compute_signature_9d', 'compute_signature_9d_torch',
    'SIGNATURE_DIMS', 'validate_signatures',
    'HarmonicAnalyzer', 'HarmonicCache', 'HarmonicContextExpander',
    'HarmonicResonanceEngine', 'HarmonicSignature', 'HarmonicPattern',
    'ResonanceResult',
    'llm', 'semantic', 'memory', 'api',
]
