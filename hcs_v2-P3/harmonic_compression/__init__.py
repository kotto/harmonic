#!/usr/bin/env python3
"""
HARMONIC COMPRESSION SYSTEM
Implémentation inspirée des principes de succès de l'upscaling harmonique
"""

__version__ = "1.0.0"
__author__ = "HCS Team"
__description__ = "Système de compression harmonique adaptative"

from .core import HarmonicCompressionEngine
from .analyzers import ImageAnalyzer, CompressionComplexityAnalyzer
from .encoders import StructuralEncoder, EntropicEncoder, AdaptiveEncoder, QuantumHarmonicEncoder
from .metrics import CompressionMetrics, QualityMetrics
from .optimizers import ResourceOptimizer, QualityOptimizer

__all__ = [
    'HarmonicCompressionEngine',
    'ImageAnalyzer',
    'CompressionComplexityAnalyzer',
    'StructuralEncoder',
    'EntropicEncoder', 
    'AdaptiveEncoder',
    'QuantumHarmonicEncoder',
    'CompressionMetrics',
    'QualityMetrics',
    'ResourceOptimizer',
    'QualityOptimizer'
]
