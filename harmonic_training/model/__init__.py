"""
Harmonic Model Package
======================
Package complet du modele harmonique :
- Noyau ABC (Atangana-Baleanu) a l'ordre 1/phi
- Attention harmonique avec signatures 7D
- Couches de decodeur harmonique (classique et pur)
- Modele de langage causal harmonique (classique et pur)
- Signatures pures V3/V4
- Moteur hybride
- Distillation harmonique
- Applications concretes BERT
"""

# =========================================================================
# Noyau ABC
# =========================================================================
from .abc_kernel import (
    ABCKernel,
    ABCKernel as ABCKernelLayer,
    ALPHA,
    B_1_PHI,
    PHI,
    ALPHA_CONST,
)

# =========================================================================
# Attention harmonique classique
# =========================================================================
from .harmonic_attention import HarmonicAttention, SignatureProjection

# =========================================================================
# Couches classiques
# =========================================================================
from .harmonic_layers import HarmonicDecoderLayer, SwiGLUFFN

# =========================================================================
# Modele classique
# =========================================================================
from .harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS, RotaryEmbedding

# =========================================================================
# Signatures harmoniques pures
# =========================================================================
from .harmonic_pure_attention import PureHarmonicAttention, PureSignatureProjection
from .harmonic_pure_signatures_v3 import PureSignatureProjectionV3
from .harmonic_pure_signatures_v4 import PureSignatureProjectionV4
from .harmonic_pure_signatures import PureSignatureProjectionV2
from .harmonic_pure_layers import PureHarmonicDecoderLayer, HarmonicFixedTransform, create_harmonic_weight_matrix, create_harmonic_ffn_weights
from .harmonic_pure_model import HarmonicPureForCausalLM, HarmonicFixedEmbedding, HarmonicFixedLMHead
# Moteur hybride (import protege)
# =========================================================================
try:
    from .harmonic_hybrid_engine import HarmonicHybridEngine, ResonanceResult
except (ImportError, AttributeError):
    pass

# =========================================================================
# Distillation (import protege)
# =========================================================================
try:
    from .harmonic_distillation import CorpusDistillation
except (ImportError, AttributeError):
    pass
try:
    from .harmonic_distillation_v2 import HarmonicDistillationPipeline
except (ImportError, AttributeError):
    pass
try:
    from .harmonic_distilled_integration import DistilledHarmonicEngine
except (ImportError, AttributeError):
    pass

# =========================================================================
# Applications BERT (import protege)
# =========================================================================
try:
    from .harmonic_applications_bert import (
        BertToHarmonicSignature,
        analyze_with_bert,
    )
except (ImportError, AttributeError):
    pass

# =========================================================================
# Applications concretes (import protege)
# =========================================================================
try:
    from .harmonic_applications_concretes import (
        SignatureEngine9D,
        HarmonicClassifier,
        HarmonicClusterAnalyzer,
        HarmonicOptimizer,
        advanced_financial_analysis,
        medical_signature_analysis,
        industrial_maintenance_diagnosis,
        creative_style_analysis,
    )
except (ImportError, AttributeError):
    pass

# =========================================================================
# Decodeur Inverse ABC (PhiInverse)
# =========================================================================
try:
    from .harmonic_signature_decoder import PhiInverseDecoder, PhiInversePipeline
except (ImportError, AttributeError):
    pass

# =========================================================================
# Tokenizer
# =========================================================================
from .tokenizer import HarmonicTokenizer


__all__ = [
    # Noyau ABC
    "ABCKernel",
    "ABCKernelLayer",
    "ALPHA",
    "B_1_PHI",
    "PHI",
    "ALPHA_CONST",
    # Attention classique
    "HarmonicAttention",
    "SignatureProjection",
    # Couches classiques
    "HarmonicDecoderLayer",
    "SwiGLUFFN",
    # Modele classique
    "HarmonicForCausalLM",
    "HARMONIC_CONFIGS",
    "RotaryEmbedding",
    # Modeles purs
    "PureSignatureProjection",
    "PureSignatureProjectionV3",
    "PureSignatureProjectionV4",
    # "extract_keywords_batch",
    # "HarmonicSignatureProjection",
    "PureHarmonicAttention",
    "PureHarmonicDecoderLayer",
    "HarmonicFixedTransform",
    "create_harmonic_weight_matrix",
    "create_harmonic_ffn_weights",
    "HarmonicPureForCausalLM",
    "HarmonicFixedEmbedding",
    "HarmonicFixedLMHead",
    # Optionnel (import protege)
    "HarmonicHybridEngine",
    "ResonanceResult",
    "CorpusDistillation",
    "HarmonicDistillationPipeline",
    "DistilledHarmonicEngine",
    "BertToHarmonicSignature",
    "analyze_with_bert",
    "HarmonicApplicationAnalyzer",
    "analyze_harmonic_applications",
    "SignatureEngine9D",
    "HarmonicClassifier",
    "HarmonicClusterAnalyzer",
    "HarmonicOptimizer",
    # Decodeur Inverse ABC
    "PhiInverseDecoder",
    "PhiInversePipeline",
    # Tokenizer
    "HarmonicTokenizer",
]



