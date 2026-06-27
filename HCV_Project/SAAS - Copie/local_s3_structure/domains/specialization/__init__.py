#!/usr/bin/env python3
"""
🎯 HARMONIC AI SPECIALIZATION MODULE
Module de spécialisation (fine-tuning) avec fichiers textes et images
"""

from .harmonic_specialization_engine import (
    SpecializationConfig,
    SpecializationResult,
    HarmonicSpecializationEngine,
    HarmonicSpecializationModel,
    HarmonicSpecializationDataset
)

__version__ = "1.0.0"
__author__ = "Harmonic AI Team"
__description__ = "Module de spécialisation harmonique avec support textes et images"

__all__ = [
    "SpecializationConfig",
    "SpecializationResult", 
    "HarmonicSpecializationEngine",
    "HarmonicSpecializationModel",
    "HarmonicSpecializationDataset"
]
