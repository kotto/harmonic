#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCS Harmonic AI - Module de generation d'images/videos deterministe
Architecture : BDD harmonique + SDXL CPU compresse + Generateur harmonique pur
              + Upscaling quantique-harmonique integre (jusqu'a 8K sur CPU)

Pipeline complet :
  Prompt --> AdaptiveLearner (gen. basse res.)
          --> HarmonicUpscalerBridge (upscale x2/x4 guide par signature)
          --> Image haute resolution coherente harmoniquement
"""
__version__ = "1.1.0"
__author__ = "HCS V2"

from .harmonic_db import HarmonicDatabase
from .harmonic_signature import HarmonicSignatureExtractor
from .harmonic_synthesizer import HarmonicSynthesizer
from .sdxl_cpu_engine import SDXLCPUEngine
from .adaptive_learner import AdaptiveLearner
from .harmonic_upscaler_bridge import HarmonicUpscalerBridge
from .harmonic_compressor_bridge import HarmonicCompressorBridge

__all__ = [
    "HarmonicDatabase",
    "HarmonicSignatureExtractor",
    "HarmonicSynthesizer",
    "SDXLCPUEngine",
    "AdaptiveLearner",
    "HarmonicUpscalerBridge",
    "HarmonicCompressorBridge",
]
