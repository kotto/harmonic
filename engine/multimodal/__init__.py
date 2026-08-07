"""
engine.multimodal — Analyse multimodale harmonique
====================================================
Analyse les fichiers image, audio, vidéo et document
et produit leur signature harmonique 9D.

Interface publique :
    analyze_image(path)         → Dict signature 9D + métadonnées
    analyze_audio(path)         → Dict signature 9D + métadonnées
    analyze_video(path)         → Dict signature 9D + métadonnées
    analyze_document(path)      → Dict signature 9D + métadonnées
    analyze_multimodal(paths)   → Dict fusion de plusieurs signatures
    fuse_signatures(sigs)       → Signature harmonique fusionnée

Classes avancées :
    ImageAnalyzer               # Analyse pixel-level avec Canvas-like
    AudioAnalyzer               # Analyse FFT + spectre
    VideoAnalyzer               # Échantillonnage frame-par-frame
    DocumentAnalyzer            # Analyse textuelle
    AttachedFile                # Wrapper unifié
    HarmonicAVGenerator         # Génération AV harmonique intégrée

Principes :
    - Purement Python (Pillow pour images, numpy pour calculs)
    - Aucune dépendance externe lourde
    - Signatures 9D normalisées dans [0,1]
    - Utilise le noyau ABC et les constantes harmoniques

Référence : harmonic_web/multimodal.js (port Python complet)
"""

from .analyzers import (
    ImageAnalyzer,
    AudioAnalyzer,
    VideoAnalyzer,
    DocumentAnalyzer,
    AttachedFile,
    analyze_image,
    analyze_audio,
    analyze_video,
    analyze_document,
    analyze_multimodal,
    fuse_signatures,
    compute_resonance,
)

from .av_generator import (
    HarmonicAVGenerator,
    AVGenerationResult,
    AudioVisualTemplate,
)

# ── Génération média harmonique (Universe Language Model) ────────────────────
# Paradigme retrieval : stocke de vrais patches → indexe par descripteurs HRR
# → récupère par résonance → assemble avec phase-coherent blending
# Cascade multi-échelle √2 + corrélations de phase inter-échelles (Portilla-Simoncelli)
try:
    from .spectral_descriptor import SpectralDescriptor
    from .patch_store import PatchStore, StoredPatch
    from .visual_memory import VisualMemory
    from .visual_trainer import VisualTrainer, PhaseCoherence
    from .visual_generator import VisualGenerator, GenerationResult
    from .wave_audio import HarmonicAudioGenerator, AudioResult
    from .harmonic_media import HarmonicMediaEngine, MediaResult

    _HARMONIC_MEDIA_AVAILABLE = True
except ImportError as e:
    _HARMONIC_MEDIA_AVAILABLE = False
    _HARMONIC_MEDIA_IMPORT_ERROR = str(e)

__all__ = [
    'ImageAnalyzer', 'AudioAnalyzer', 'VideoAnalyzer', 'DocumentAnalyzer',
    'AttachedFile',
    'analyze_image', 'analyze_audio', 'analyze_video', 'analyze_document',
    'analyze_multimodal', 'fuse_signatures', 'compute_resonance',
    'HarmonicAVGenerator', 'AVGenerationResult', 'AudioVisualTemplate',
    # Génération média harmonique (retrieval-based)
    'SpectralDescriptor', 'PatchStore', 'StoredPatch',
    'VisualMemory', 'VisualTrainer', 'VisualGenerator',
    'HarmonicAudioGenerator', 'HarmonicMediaEngine', 'MediaResult',
]
