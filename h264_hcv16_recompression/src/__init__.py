# HCV16 H.264 Recompression POC
# Exploitation révolution 18× lossless pour améliorer H.264 existants

__version__ = "0.1.0"
__author__ = "HCV16 Team"
__description__ = "POC recompression H.264 avec breakthrough HCV16"

from .h264_analyzer import H264Analyzer
from .h264_recompressor import H264HCV16Recompressor
from .artifact_detector import ArtifactDetector
from .performance_tracker import PerformanceTracker

__all__ = [
    'H264Analyzer',
    'H264HCV16Recompressor', 
    'ArtifactDetector',
    'PerformanceTracker'
]