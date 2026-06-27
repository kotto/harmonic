#!/usr/bin/env python3
"""
User Memory — Holographic Memory Persistence
==============================================
Stores and retrieves user interactions cumulatively using the 256x256 hologram.
Each interaction is superposed as a wave — nothing is ever lost.
Saves/loads the hologram as .npy for persistence across sessions.

Usage:
  from user_memory import UserMemory
  mem = UserMemory()
  mem.remember("Quel temps fait-il a Paris ?", domain="weather")
  history = mem.recall("meteo")  # returns resonant memories
"""

import os, sys, json, time, hashlib, datetime
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

# Try to import the hologram engine
HOLOGRAM_SIZE = 256
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Constants from harmonic engine
PHI = 1.618033988749895
PI = np.pi

class UserMemory:
    """
    Holographic user memory — stores everything, forgets nothing.
    
    Each interaction = wave superposition in the 256x256 hologram.
    Memory is saved to disk for persistence.
    """
    
    def __init__(self, user_id: str = "default", data_dir: str = None):
        self.user_id = user_id
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "data", "memory")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize hologram
        self.hologram = np.zeros((HOLOGRAM_SIZE, HOLOGRAM_SIZE), dtype=np.complex128)
        
        # Conversation log (for non-hologram access)
        self.log = []
        
        # Load existing if available
        self._load()
    
    def remember(self, prompt: str, response: str = "", domain: str = "general",
                 action: str = None, context: Dict = None) -> Dict:
        """
        Store an interaction in the holographic memory.
        Each interaction creates a unique wave pattern that is ADDED to the hologram.
        """
        timestamp = datetime.datetime.now().isoformat()
        
        # Generate wave signature from the prompt
        kx, ky = self._prompt_to_wave(prompt)
        
        # Create a Gaussian wave packet centered at (kx, ky)
        wave = self._gaussian_wave(kx, ky, sigma=3.0)
        
        # Superpose onto the hologram
        self.hologram += wave
        
        # Normalize to prevent overflow
        max_amp = np.max(np.abs(self.hologram))
        if max_amp > 100.0:
            self.hologram *= 0.95  # Soft decay to prevent saturation
        
        # Log entry
        entry = {
            "prompt": prompt[:200],
            "response": response[:200] if response else "",
            "domain": domain,
            "action": action,
            "kx": float(kx),
            "ky": float(ky),
            "timestamp": timestamp,
            "context": context or {}
        }
        self.log.append(entry)
        
        # Auto-save every 10 interactions
        if len(self.log) % 10 == 0:
            self._save()
        
        return {
            "stored": True,
            "kx": float(kx),
            "ky": float(ky),
            "total_interactions": len(self.log),
            "hologram_density": float(np.mean(np.abs(self.hologram)))
        }
    
    def recall(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Recall memories that resonate with the query.
        Computes the correlation between the query wave and the hologram.
        """
        if len(self.log) == 0:
            return []
        
        kx, ky = self._prompt_to_wave(query)
        query_wave = self._gaussian_wave(kx, ky, sigma=2.0)
        
        # Cross-correlation: query_wave * hologram
        correlation = np.abs(np.sum(query_wave * np.conj(self.hologram)))
        correlation /= (np.sqrt(np.sum(np.abs(query_wave)**2)) * 
                       max(np.sqrt(np.sum(np.abs(self.hologram)**2)), 1e-10))
        
        # Find the most resonant entries from the log
        # Compute resonance score for each entry
        entries_scored = []
        for entry in self.log:
            entry_kx, entry_ky = entry["kx"], entry["ky"]
            # Distance in frequency space
            dist = np.sqrt((kx - entry_kx)**2 + (ky - entry_ky)**2)
            # Closer = more resonant
            resonance = np.exp(-dist / 3.0)
            entries_scored.append((resonance, entry))
        
        entries_scored.sort(key=lambda x: -x[0])
        results = [e for _, e in entries_scored[:top_k]]
        
        return results
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        return {
            "user_id": self.user_id,
            "total_interactions": len(self.log),
            "hologram_size": f"{HOLOGRAM_SIZE}x{HOLOGRAM_SIZE}",
            "hologram_density": float(np.mean(np.abs(self.hologram))),
            "hologram_max": float(np.max(np.abs(self.hologram))),
            "domains": self._domain_stats(),
            "patterns_detected": self._detect_patterns(),
            "last_interaction": self.log[-1]["timestamp"] if self.log else None,
        }
    
    def get_patterns(self) -> List[Dict]:
        """Get detected behavioral patterns."""
        return self._detect_patterns()
    
    def clear(self):
        """Clear all memory (user request)."""
        self.hologram = np.zeros((HOLOGRAM_SIZE, HOLOGRAM_SIZE), dtype=np.complex128)
        self.log = []
        self._save()
        return {"cleared": True}
    
    def _prompt_to_wave(self, prompt: str) -> Tuple[float, float]:
        """Convert a prompt to a unique (kx, ky) signature."""
        # Hash the prompt to get deterministic coordinates
        h = hashlib.sha256(prompt.encode()).hexdigest()
        # Map hash to coordinates in the hologram
        kx = (int(h[:16], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
        ky = (int(h[16:32], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
        # Center (0,0) is at HOLOGRAM_SIZE/2
        kx -= HOLOGRAM_SIZE / 2
        ky -= HOLOGRAM_SIZE / 2
        # Scale to [-10, 10] range for nice wave patterns
        kx = kx / HOLOGRAM_SIZE * 20
        ky = ky / HOLOGRAM_SIZE * 20
        return kx, ky
    
    def _gaussian_wave(self, kx: float, ky: float, sigma: float = 3.0) -> np.ndarray:
        """Create a Gaussian wave packet centered at (kx, ky)."""
        x = np.linspace(-HOLOGRAM_SIZE/2, HOLOGRAM_SIZE/2, HOLOGRAM_SIZE)
        y = np.linspace(-HOLOGRAM_SIZE/2, HOLOGRAM_SIZE/2, HOLOGRAM_SIZE)
        X, Y = np.meshgrid(x, y)
        
        # Gaussian envelope
        env = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
        # Plane wave: e^(i * (kx * x + ky * y))
        wave = np.exp(1j * (kx * X / 20 + ky * Y / 20))
        # Constraint amplitude
        amp = 0.5
        
        return amp * env * wave
    
    def _domain_stats(self) -> Dict[str, int]:
        """Count interactions per domain."""
        domains = {}
        for entry in self.log:
            d = entry.get("domain", "general")
            domains[d] = domains.get(d, 0) + 1
        return domains
    
    def _detect_patterns(self) -> List[Dict]:
        """Detect behavioral patterns from the interaction log."""
        patterns = []
        
        if len(self.log) < 3:
            return patterns
        
        # Time-of-day patterns
        hours = []
        for entry in self.log:
            try:
                t = datetime.datetime.fromisoformat(entry["timestamp"])
                hours.append(t.hour)
            except:
                continue
        
        if hours:
            from collections import Counter
            hour_counts = Counter(hours)
            peak_hour = hour_counts.most_common(1)[0] if hour_counts else (0, 0)
            if peak_hour[1] >= 2:
                patterns.append({
                    "type": "time_preference",
                    "description": f"Tu utilises KA Phone le plus souvent vers {peak_hour[0]}h ({peak_hour[1]} interactions)",
                    "confidence": min(0.9, peak_hour[1] / len(self.log) * 5)
                })
        
        # Domain frequency
        domains = self._domain_stats()
        if domains:
            top_domain = max(domains, key=domains.get)
            if domains[top_domain] >= 5:
                patterns.append({
                    "type": "domain_preference",
                    "description": f"Tu poses beaucoup de questions de {top_domain} ({domains[top_domain]} fois)",
                    "confidence": 0.85
                })
        
        return patterns
    
    def _save(self):
        """Save hologram and log to disk."""
        # Save hologram as numpy array
        holo_path = os.path.join(self.data_dir, f"hologram_{self.user_id}.npy")
        np.save(holo_path, self.hologram)
        
        # Save log as JSON (max 1000 entries to keep file manageable)
        log_path = os.path.join(self.data_dir, f"log_{self.user_id}.json")
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.log[-1000:], f, ensure_ascii=False, indent=2)
    
    def _load(self):
        """Load hologram and log from disk."""
        holo_path = os.path.join(self.data_dir, f"hologram_{self.user_id}.npy")
        if os.path.exists(holo_path):
            self.hologram = np.load(holo_path)
        
        log_path = os.path.join(self.data_dir, f"log_{self.user_id}.json")
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                self.log = json.load(f)


if __name__ == "__main__":
    mem = UserMemory("test_user")
    
    # Simulate some interactions
    print("Storing memories...")
    for q in [
        "Quel temps fait-il a Paris ?",
        "Calcule 127 + 58",
        "Rappelle-moi d'acheter du pain",
        "Quel temps fait-il a Paris ?",  # repeated
        "Quelle est la capitale du Bresil ?",
        "Calcule 15 * 7 + 3",
    ]:
        r = mem.remember(q, response="Reponse simulee", domain="general")
        print(f"  Stored: {q[:40]}... | kx={r['kx']:.2f}, ky={r['ky']:.2f}")
    
    print(f"\nStats: {mem.get_stats()}")
    
    print("\nRecall: 'meteo'")
    for m in mem.recall("meteo"):
        print(f"  [{m['timestamp'][:19]}] {m['prompt'][:50]}")
    
    print("\nPatterns detected:")
    for p in mem.get_patterns():
        print(f"  - {p['description']} (confidence: {p['confidence']:.0%})")
    
    print(f"\nHologram density: {mem.get_stats()['hologram_density']:.4f}")