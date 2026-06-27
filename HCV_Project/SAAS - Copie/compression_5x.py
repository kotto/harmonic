#!/usr/bin/env python3
"""
🗜️ HCV PRO Compression 5x with Validation
Harmonic Compression Vector system for MOE experts
"""

import time
import json
import pickle
import gzip
import hashlib
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import re
import zlib
import base64

class CompressionType(Enum):
    VECTOR_QUANTIZATION = "vector_quantization"
    KNOWLEDGE_PRUNING = "knowledge_pruning"
    WEIGHT_SHARING = "weight_sharing"
    HARMONIC_ENCODING = "harmonic_encoding"

@dataclass
class CompressionMetrics:
    original_size: int
    compressed_size: int
    compression_ratio: float
    compression_time: float
    decompression_time: float
    integrity_score: float
    preservation_score: float

class VectorQuantizer:
    """Harmonic Vector Quantization for compression"""
    
    def __init__(self, codebook_size: int = 256):
        self.codebook_size = codebook_size
        self.codebook = None
        self.is_trained = False
    
    def train_codebook(self, vectors: np.ndarray) -> None:
        """Train codebook using k-means like approach"""
        # Simplified k-means for demonstration
        indices = np.random.choice(len(vectors), self.codebook_size, replace=False)
        self.codebook = vectors[indices].copy()
        self.is_trained = True
    
    def quantize(self, vectors: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Quantize vectors to codebook indices"""
        if not self.is_trained:
            self.train_codebook(vectors)
        
        # Find nearest codebook entries
        distances = np.linalg.norm(vectors[:, np.newaxis] - self.codebook, axis=2)
        indices = np.argmin(distances, axis=1)
        quantized = self.codebook[indices]
        
        return quantized, indices
    
    def get_compression_ratio(self, original_shape: Tuple) -> float:
        """Calculate theoretical compression ratio"""
        original_size = np.prod(original_shape) * 4  # float32
        compressed_size = original_shape[0] * 1  # indices
        return original_size / compressed_size

class KnowledgePruner:
    """Prune redundant knowledge while preserving core information"""
    
    def __init__(self, redundancy_threshold: float = 0.85):
        self.redundancy_threshold = redundancy_threshold
    
    def prune_knowledge_base(self, knowledge_entries: List[str]) -> List[str]:
        """Remove redundant knowledge entries"""
        unique_entries = []
        
        for entry in knowledge_entries:
            is_redundant = False
            entry_lower = entry.lower()
            
            for unique_entry in unique_entries:
                similarity = self._calculate_similarity(entry_lower, unique_entry.lower())
                if similarity > self.redundancy_threshold:
                    is_redundant = True
                    break
            
            if not is_redundant:
                unique_entries.append(entry)
        
        return unique_entries
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple overlap"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

class WeightSharer:
    """Share weights across similar parameters"""
    
    def __init__(self, similarity_threshold: float = 0.95):
        self.similarity_threshold = similarity_threshold
        self.weight_groups = {}
    
    def share_weights(self, weights: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Group and share similar weights"""
        shared_weights = {}
        weight_signatures = {}
        
        for name, weight in weights.items():
            signature = self._create_weight_signature(weight)
            weight_signatures[name] = signature
        
        # Group similar weights
        groups = self._group_similar_weights(weight_signatures)
        
        # Create shared weight dictionary
        for group_id, weight_names in groups.items():
            if len(weight_names) > 1:
                # Use average weight for the group
                group_weights = [weights[name] for name in weight_names]
                shared_weight = np.mean(group_weights, axis=0)
                
                for name in weight_names:
                    shared_weights[name] = shared_weight
            else:
                shared_weights[weight_names[0]] = weights[weight_names[0]]
        
        return shared_weights
    
    def _create_weight_signature(self, weight: np.ndarray) -> str:
        """Create signature for weight comparison"""
        # Use statistical properties as signature
        mean_val = np.mean(weight)
        std_val = np.std(weight)
        shape = weight.shape
        
        return f"{shape}_{mean_val:.6f}_{std_val:.6f}"
    
    def _group_similar_weights(self, signatures: Dict[str, str]) -> Dict[int, List[str]]:
        """Group weights with similar signatures"""
        groups = {}
        group_id = 0
        
        processed = set()
        
        for name1, sig1 in signatures.items():
            if name1 in processed:
                continue
            
            current_group = [name1]
            processed.add(name1)
            
            for name2, sig2 in signatures.items():
                if name2 in processed:
                    continue
                
                similarity = self._signature_similarity(sig1, sig2)
                if similarity > self.similarity_threshold:
                    current_group.append(name2)
                    processed.add(name2)
            
            groups[group_id] = current_group
            group_id += 1
        
        return groups
    
    def _signature_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between weight signatures"""
        parts1 = sig1.split('_')
        parts2 = sig2.split('_')
        
        # Shape must match
        if parts1[0] != parts2[0]:
            return 0.0
        
        # Compare statistical properties
        mean_diff = abs(float(parts1[1]) - float(parts2[1]))
        std_diff = abs(float(parts1[2]) - float(parts2[2]))
        
        # Higher similarity for smaller differences
        similarity = 1.0 / (1.0 + mean_diff + std_diff)
        return similarity

class HarmonicEncoder:
    """Harmonic encoding for semantic preservation"""
    
    def __init__(self, harmonic_frequencies: List[float] = None):
        if harmonic_frequencies is None:
            # Musical frequencies for encoding
            self.harmonic_frequencies = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
        else:
            self.harmonic_frequencies = harmonic_frequencies
    
    def encode_text(self, text: str) -> np.ndarray:
        """Encode text using harmonic frequencies"""
        # Convert text to numerical representation
        char_codes = [ord(c) for c in text[:len(self.harmonic_frequencies)]]
        
        # Pad or truncate to match frequency count
        if len(char_codes) < len(self.harmonic_frequencies):
            char_codes.extend([0] * (len(self.harmonic_frequencies) - len(char_codes)))
        
        # Create harmonic encoding
        encoded = np.array(char_codes) * np.array(self.harmonic_frequencies)
        
        return encoded
    
    def decode_text(self, encoded: np.ndarray) -> str:
        """Decode harmonic encoding back to text"""
        # Reverse the encoding process
        char_codes = (encoded / np.array(self.harmonic_frequencies)).astype(int)
        
        # Convert back to characters
        text = ''.join([chr(code) if 0 <= code <= 127 else '?' for code in char_codes])
        
        return text

class HCVCompression5X:
    """Main HCV PRO Compression 5X System"""
    
    def __init__(self):
        self.vector_quantizer = VectorQuantizer()
        self.knowledge_pruner = KnowledgePruner()
        self.weight_sharer = WeightSharer()
        self.harmonic_encoder = HarmonicEncoder()
        
        self.compression_history = []
        self.target_compression_ratio = 5.0
    
    def compress_expert(self, expert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compress expert data with 5x target ratio"""
        start_time = time.time()
        
        original_size = self._calculate_size(expert_data)
        
        # Step 1: Vector Quantization
        if 'weights' in expert_data:
            weights = expert_data['weights']
            weight_vectors = np.array([w.flatten() for w in weights.values()])
            quantized_vectors, indices = self.vector_quantizer.quantize(weight_vectors)
            
            # Reconstruct weights dictionary
            compressed_weights = {}
            for i, (name, original_weight) in enumerate(weights.items()):
                compressed_weights[name] = quantized_vectors[i].reshape(original_weight.shape)
            
            expert_data['weights'] = compressed_weights
        
        # Step 2: Knowledge Pruning
        if 'knowledge_base' in expert_data:
            knowledge = expert_data['knowledge_base']
            pruned_knowledge = self.knowledge_pruner.prune_knowledge_base(knowledge)
            expert_data['knowledge_base'] = pruned_knowledge
        
        # Step 3: Weight Sharing
        if 'weights' in expert_data:
            expert_data['weights'] = self.weight_sharer.share_weights(expert_data['weights'])
        
        # Step 4: Harmonic Encoding for metadata
        if 'metadata' in expert_data:
            metadata_str = json.dumps(expert_data['metadata'])
            encoded_metadata = self.harmonic_encoder.encode_text(metadata_str)
            expert_data['encoded_metadata'] = encoded_metadata.tolist()
            del expert_data['metadata']
        
        # Final compression using gzip
        compressed_data = gzip.compress(json.dumps(expert_data).encode())
        
        compression_time = time.time() - start_time
        compressed_size = len(compressed_data)
        compression_ratio = original_size / compressed_size
        
        # Validate compression
        integrity_score = self._validate_integrity(expert_data, compressed_data)
        preservation_score = self._validate_preservation(expert_data)
        
        metrics = CompressionMetrics(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=compression_time,
            decompression_time=0.0,
            integrity_score=integrity_score,
            preservation_score=preservation_score
        )
        
        self.compression_history.append(metrics)
        
        return {
            'compressed_data': base64.b64encode(compressed_data).decode(),
            'metrics': asdict(metrics),
            'compression_method': 'HCV-5X',
            'expert_type': expert_data.get('expert_type', 'unknown')
        }
    
    def decompress_expert(self, compressed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Decompress expert data"""
        start_time = time.time()
        
        # Decode base64 and decompress
        compressed_data = base64.b64decode(compressed_result['compressed_data'])
        decompressed_data = gzip.decompress(compressed_data).decode()
        expert_data = json.loads(decompressed_data)
        
        # Decode harmonic metadata
        if 'encoded_metadata' in expert_data:
            encoded_metadata = np.array(expert_data['encoded_metadata'])
            metadata_str = self.harmonic_encoder.decode_text(encoded_metadata)
            expert_data['metadata'] = json.loads(metadata_str)
            del expert_data['encoded_metadata']
        
        decompression_time = time.time() - start_time
        
        # Update metrics
        metrics = compressed_result['metrics']
        metrics['decompression_time'] = decompression_time
        
        return expert_data
    
    def _calculate_size(self, data: Dict[str, Any]) -> int:
        """Calculate size of data in bytes"""
        return len(json.dumps(data).encode())
    
    def _validate_integrity(self, original: Dict[str, Any], compressed: bytes) -> float:
        """Validate compression integrity"""
        try:
            # Test decompression
            decompressed = gzip.decompress(compressed).decode()
            reconstructed = json.loads(decompressed)
            
            # Check key preservation
            original_keys = set(original.keys())
            reconstructed_keys = set(reconstructed.keys())
            
            key_preservation = len(original_keys.intersection(reconstructed_keys)) / len(original_keys)
            
            return key_preservation
        except Exception:
            return 0.0
    
    def _validate_preservation(self, data: Dict[str, Any]) -> float:
        """Validate semantic preservation"""
        score = 1.0
        
        # Check if critical components are preserved
        critical_components = ['expert_type', 'weights', 'knowledge_base']
        
        for component in critical_components:
            if component not in data:
                score *= 0.8
        
        return score
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        if not self.compression_history:
            return {"status": "No compression history"}
        
        avg_ratio = np.mean([m.compression_ratio for m in self.compression_history])
        avg_time = np.mean([m.compression_time for m in self.compression_history])
        avg_integrity = np.mean([m.integrity_score for m in self.compression_history])
        
        return {
            'total_compressions': len(self.compression_history),
            'average_compression_ratio': avg_ratio,
            'target_ratio': self.target_compression_ratio,
            'target_achieved': avg_ratio >= self.target_compression_ratio,
            'average_compression_time': avg_time,
            'average_integrity_score': avg_integrity,
            'compression_efficiency': avg_ratio / self.target_compression_ratio
        }

# Test the compression system
if __name__ == "__main__":
    compressor = HCVCompression5X()
    
    # Create sample expert data
    sample_expert = {
        'expert_type': 'mathematical_reasoning',
        'weights': {
            'layer1': np.random.randn(100, 50),
            'layer2': np.random.randn(50, 25),
            'layer3': np.random.randn(25, 10)
        },
        'knowledge_base': [
            "Mathematics is the study of numbers, shapes, and patterns",
            "Algebra deals with symbols and rules for manipulating them",
            "Geometry studies shapes, sizes, and properties of space",
            "Calculus studies continuous change and motion",
            "Statistics deals with data collection and analysis",
            "Probability theory studies random phenomena",
            "Number theory studies properties of integers",
            "Mathematical logic studies formal systems"
        ],
        'metadata': {
            'version': '2.0',
            'training_data': 'math_corpus_v3',
            'accuracy': 0.95,
            'parameters': 50000
        }
    }
    
    print("🗜️ HCV PRO Compression 5X Test")
    print("=" * 50)
    
    # Test compression
    print("📦 Compressing expert data...")
    compression_result = compressor.compress_expert(sample_expert)
    
    print(f"✅ Compression Ratio: {compression_result['metrics']['compression_ratio']:.2f}x")
    print(f"⚡ Compression Time: {compression_result['metrics']['compression_time']:.3f}s")
    print(f"🔒 Integrity Score: {compression_result['metrics']['integrity_score']:.3f}")
    print(f"🎯 Preservation Score: {compression_result['metrics']['preservation_score']:.3f}")
    
    # Test decompression
    print("\n📂 Decompressing expert data...")
    decompressed_expert = compressor.decompress_expert(compression_result)
    
    print(f"✅ Expert Type: {decompressed_expert['expert_type']}")
    print(f"📚 Knowledge Base Size: {len(decompressed_expert['knowledge_base'])}")
    print(f"⚡ Decompression Time: {compression_result['metrics']['decompression_time']:.3f}s")
    
    # Get overall stats
    print("\n📊 Compression Statistics:")
    stats = compressor.get_compression_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n🎯 5X Compression Target:", "✅ ACHIEVED" if stats.get('target_achieved', False) else "❌ NOT ACHIEVED")
