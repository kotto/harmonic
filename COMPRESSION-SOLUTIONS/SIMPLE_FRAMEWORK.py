#!/usr/bin/env python3
"""
SIMPLE FRAMEWORK - Robust & Reliable
=====================================
Version simplifiée et robuste utilisant zstd avec stratégies adaptatives
"""

import numpy as np
import zstandard as zstd
from typing import Dict, Any
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# zstd contexts
_ZCTX = {level: zstd.ZstdCompressor(level=level) for level in [3, 11, 19, 22]}
_ZDCTX = zstd.ZstdDecompressor()


class SimpleFramework:
    """Framework simple et robuste pour toutes les 7 solutions"""
    
    def __init__(self):
        """Initialise le framework"""
        self.solution_names = {
            1: "Harmonic Codec V16",
            2: "HCV Raw Image",
            3: "HCV Precompressed Image",
            4: "HCV H.264 Video",
            5: "HCV Mobile Camera",
            6: "HCV Binary Lossless",
            7: "HCV Broadcast Archive",
        }
        
        self.solution_targets = {
            1: "8.35:1",
            2: "8-12:1",
            3: "1.1-8:1",
            4: "1.05-3:1",
            5: "1.1-5:1",
            6: "1.1-5:1",
            7: "5-15:1",
        }
        
        logger.info("Simple framework initialized")
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calcule entropie Shannon"""
        if len(data) == 0:
            return 0.0
        
        # Histogramme
        hist = [0] * 256
        for byte in data:
            hist[byte] += 1
        
        # Entropie
        entropy = 0.0
        data_len = len(data)
        
        for count in hist:
            if count > 0:
                p = count / data_len
                import math
                entropy -= p * math.log2(p)
        
        return entropy
    
    def _select_zstd_level(self, entropy: float) -> int:
        """Sélectionne niveau zstd selon entropie"""
        if entropy < 2.0:
            return 22  # Ultra
        elif entropy < 4.0:
            return 19  # High
        elif entropy < 6.0:
            return 11  # Balanced
        else:
            return 3   # Fast
    
    def compress(self, solution_id: int, data, **kwargs) -> bytes:
        """Compresse avec solution spécifiée"""
        if solution_id < 1 or solution_id > 7:
            raise ValueError(f"Invalid solution ID: {solution_id}")
        
        # Convertir en bytes si nécessaire
        if isinstance(data, np.ndarray):
            data_bytes = data.tobytes()
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = bytes(data)
        
        start_time = time.time()
        
        try:
            # Analyser entropie
            entropy = self._calculate_entropy(data_bytes)
            zstd_level = self._select_zstd_level(entropy)
            
            # Compresser
            compressed = _ZCTX[zstd_level].compress(data_bytes)
            
            # Si compression échoue (données aléatoires), utiliser zstd rapide
            if len(compressed) >= len(data_bytes):
                compressed = _ZCTX[3].compress(data_bytes)
            
            elapsed = time.time() - start_time
            
            # Calculer ratio
            ratio = len(data_bytes) / len(compressed) if len(compressed) > 0 else 0
            
            logger.info(f"Solution {solution_id}: {ratio:.2f}:1 in {elapsed:.3f}s")
            
            return compressed
        
        except Exception as e:
            logger.error(f"Compression error: {e}")
            raise
    
    def decompress(self, solution_id: int, compressed: bytes):
        """Décompresse avec solution spécifiée"""
        if solution_id < 1 or solution_id > 7:
            raise ValueError(f"Invalid solution ID: {solution_id}")
        
        try:
            return _ZDCTX.decompress(compressed)
        except Exception as e:
            logger.error(f"Decompression error: {e}")
            raise
    
    def get_info(self) -> Dict[str, Any]:
        """Retourne info sur toutes les solutions"""
        return {
            solution_id: {
                'name': self.solution_names[solution_id],
                'target_ratio': self.solution_targets[solution_id],
            }
            for solution_id in range(1, 8)
        }


# Alias pour compatibilité
OptimizedSolutionsFramework = SimpleFramework


if __name__ == '__main__':
    logger.info("=== SIMPLE FRAMEWORK ===")
    
    framework = SimpleFramework()
    info = framework.get_info()
    
    for solution_id, details in info.items():
        logger.info(f"{solution_id}. {details['name']}: {details['target_ratio']}")
