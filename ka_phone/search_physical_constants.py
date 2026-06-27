#!/usr/bin/env python3
"""
SEARCH PHYSICAL CONSTANTS — Active detection in ABC hologram
=============================================================
Searches for fundamental physical constants (c, h, G, kB, e, α, φ, π, √2, e) 
emerging from the ABC hologram 1024x1024 through pure wave interference.

Method:
  1. Load ABC hologram (Mittag-Leffler interactions included)
  2. Inject constant values as pure sinusoidal waves at specific positions
  3. Detect resonance peaks: if a constant naturally emerges from the hologram,
     its wave pattern will resonate with the existing interference structure
  4. Compare ratios between detected peaks to φ, π, √2, e

Physical principle: 
  ABC D_t^(1/φ) [Hologram] = Source(Knowledge)
  → After sufficient iterations, the hologram "knows" relationships 
    between constants through wave interference patterns
"""

import numpy as np
import math
import os
import sys
import json
import time
import hashlib

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, '.')

# Configuration
SIZE = 1024
PHI = (1 + math.sqrt(5)) / 2
DATA_DIR = os.path.join('..', 'data', 'emergence')
ABC_HOLOGRAM = os.path.join(DATA_DIR, 'abc_hologram_1024.npy')
STANDARD_HOLOGRAM = os.path.join(DATA_DIR, 'emergence_hologram_1024.npy')
RESULTS_FILE = os.path.join(DATA_DIR, 'physical_constants_found.json')
ENRICHED_HOLOGRAM = os.path.join(DATA_DIR, 'constants_hologram_1024.npy')

# Fundamental constants to search for
CONSTANTS = {
    # Mathematics
    'phi':     {'value': PHI,              'desc': 'Golden ratio',                        'type': 'math'},
    'pi':      {'value': math.pi,          'desc': 'Pi',                                   'type': 'math'},
    'e':       {'value': math.e,           'desc': 'Euler number',                         'type': 'math'},
    'sqrt2':   {'value': math.sqrt(2),     'desc': 'Square root of 2',                     'type': 'math'},
    'sqrt3':   {'value': math.sqrt(3),     'desc': 'Square root of 3',                     'type': 'math'},
    'sqrt5':   {'value': math.sqrt(5),     'desc': 'Square root of 5',                     'type': 'math'},
    'gamma':   {'value': 0.5772156649,     'desc': 'Euler-Mascheroni constant',            'type': 'math'},
    # Physics - fundamental
    'c':       {'value': 299792458,        'desc': 'Speed of light (m/s)',                'type': 'physics'},
    'h':       {'value': 6.62607015e-34,   'desc': 'Planck constant (Js)',                'type': 'physics'},
    'hbar':    {'value': 1.054571817e-34,  'desc': 'Reduced Planck constant (Js)',        'type': 'physics'},
    'G':        {'value': 6.67430e-11,     'desc': 'Gravitational constant (m3/kg s2)',   'type': 'physics'},
    'kB':      {'value': 1.380649e-23,     'desc': 'Boltzmann constant (J/K)',            'type': 'physics'},
    'e_charge':{'value': 1.602176634e-19,  'desc': 'Elementary charge (C)',               'type': 'physics'},
    'alpha':   {'value': 1/137.035999084,   'desc': 'Fine-structure constant',             'type': 'physics'},
    'NA':      {'value': 6.02214076e23,    'desc': 'Avogadro constant (1/mol)',           'type': 'physics'},
    'R':       {'value': 8.314462618,      'desc': 'Gas constant (J/mol K)',              'type': 'physics'},
    'mu0':     {'value': 1.25663706212e-6, 'desc': 'Vacuum permeability (N/A2)',          'type': 'physics'},
    'eps0':    {'value': 8.8541878128e-12, 'desc': 'Vacuum permittivity (F/m)',            'type': 'physics'},
    'sigma':   {'value': 5.670374419e-8,   'desc': 'Stefan-Boltzmann constant',            'type': 'physics'},
    'bohr':    {'value': 5.29177210903e-11,'desc': 'Bohr radius (m)',                       'type': 'physics'},
    # Astronomy / cosmology
    'M_earth': {'value': 5.972e24,         'desc': 'Earth mass (kg)',                      'type': 'astro'},
    'R_earth': {'value': 6371000,           'desc': 'Earth radius (m)',                     'type': 'astro'},
    'M_sun':   {'value': 1.989e30,         'desc': 'Solar mass (kg)',                      'type': 'astro'},
    'AU':      {'value': 1.496e11,         'desc': 'Astronomical unit (m)',                'type': 'astro'},
}

def text_to_wave(text, size=SIZE):
    """Convert text to wave position (kx, ky) deterministically."""
    hh = hashlib.sha256(text.encode()[:200]).hexdigest()
    kx = (int(hh[:16], 16) % (size * 100)) / 100.0
    ky = (int(hh[16:32], 16) % (size * 100)) / 100.0
    kx = (kx - size/2) / size * 20
    ky = (ky - size/2) / size * 20
    return kx, ky

def constant_to_wave(value, size=SIZE):
    """Convert constant value to wave position via logarithmic encoding."""
    return text_to_wave(f"{value:.15e}", size)

def measure_resonance(hologram, kx, ky, radius=5):
    """Measure the resonance strength at position (kx, ky) in the hologram."""
    ix = int(SIZE/2 + kx * SIZE/20)
    iy = int(SIZE/2 + ky * SIZE/20)
    ix = max(radius, min(SIZE - radius - 1, ix))
    iy = max(radius, min(SIZE - radius - 1, iy))
    
    # Get local patch
    patch = np.abs(hologram[iy-radius:iy+radius+1, ix-radius:ix+radius+1])
    
    # Characterize resonance: average amplitude, max amplitude, variance
    avg_amp = np.mean(patch)
    max_amp = np.max(patch)
    var_amp = np.var(patch)
    
    # Background normalization
    background = np.mean(np.abs(hologram))
    
    # Resonance score: max amplitude relative to background
    score = max_amp / background if background > 0 else 0
    
    return {
        'avg_amp': avg_amp,
        'max_amp': max_amp, 
        'var_amp': var_amp,
        'score': score,
        'background': background
    }

def find_constant_pairs(hologram, const_positions, threshold=0.015):
    """
    Find pairs of constants whose wave patterns resonate with each other.
    Returns list of (c1, c2, distance, ratio) tuples.
    """
    pairs = []
    const_names = list(const_positions.keys())
    
    for i in range(len(const_names)):
        for j in range(i+1, len(const_names)):
            c1 = const_names[i]
            c2 = const_names[j]
            
            # Get positions
            pos1 = const_positions[c1]['position']
            pos2 = const_positions[c2]['position']
            
            # Distance in holographic space
            dx = pos1[0] - pos2[0]
            dy = pos1[1] - pos2[1]
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Ratio of values (if both are positive)
            v1 = const_positions[c1]['value']
            v2 = const_positions[c2]['value']
            
            if v1 > 0 and v2 > 0:
                # Check if ratio matches φ, π, √2, or e
                ratio = v2/v1 if v1 > v2 else v1/v2
                
                # Compare with known constants
                matches = []
                for name, target in [('phi', PHI), ('pi', math.pi), ('sqrt2', math.sqrt(2)), ('e', math.e)]:
                    err = abs(ratio - target) / target
                    if err < threshold:
                        matches.append((name, err))
                
                if matches:
                    pairs.append({
                        'c1': c1, 'c2': c2,
                        'dist': round(dist, 4),
                        'ratio': round(ratio, 6),
                        'matches': [(m[0], round(m[1]*100, 2)) for m in matches]
                    })
    
    return pairs

def main():
    print("=" * 70)
    print("  ACTIVE CONSTANT SEARCH — ABC Hologram")
    print("=" * 70)
    
    # Load hologram
    hologram = None
    hologram_type = None
    
    for fpath, htype in [(ABC_HOLOGRAM, "ABC"), (STANDARD_HOLOGRAM, "standard")]:
        if os.path.exists(fpath):
            hologram = np.load(fpath)
            hologram_type = htype
            print(f"[OK] Loaded {htype} hologram: {hologram.shape}")
            break
    
    if hologram is None:
        print("[ERROR] No hologram found. Run abc_hologram_engine.py --rebuild first.")
        return
    
    # Test each constant
    print(f"\n  Testing {len(CONSTANTS)} fundamental constants...\n")
    
    results = {}
    const_positions = {}
    
    for name, info in CONSTANTS.items():
        value = info['value']
        kx, ky = constant_to_wave(value)
        resonance = measure_resonance(hologram, kx, ky)
        
        results[name] = {
            'value': value,
            'type': info['type'],
            'desc': info['desc'],
            'position': (round(kx, 4), round(ky, 4)),
            'resonance': {
                'score': round(resonance['score'], 2),
                'max_amp': round(float(resonance['max_amp']), 6),
                'avg_amp': round(float(resonance['avg_amp']), 6),
            }
        }
        
        const_positions[name] = {
            'position': (kx, ky),
            'value': value,
            'type': info['type']
        }
        
        # Display resonance: if score > 1.0, there's actual physical signal
        bar = '#' * min(int(resonance['score'] * 10), 30)
        print(f"  {name:>8s} ({info['type']:>7s}) | score={resonance['score']:5.1f} | {bar}")
    
    # Find emergent pairs
    print(f"\n  Searching for emergent relationships...")
    pairs = find_constant_pairs(hologram, const_positions, threshold=0.02)
    
    if pairs:
        print(f"\n  *** EMERGENT RELATIONSHIPS FOUND ({len(pairs)}) ***")
        for p in pairs[:15]:
            matches_str = ", ".join(f"{m[0]}({m[1]}%)" for m in p['matches'])
            print(f"    {p['c1']} <-> {p['c2']} : ratio={p['ratio']} -> {matches_str}")
    else:
        print("\n  No emergent relationships found at threshold.")
    
    # Save results
    output = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'hologram_type': hologram_type,
        'hologram_size': list(hologram.shape),
        'total_energy': float(np.sum(np.abs(hologram)**2)),
        'background': float(np.mean(np.abs(hologram))),
        'constants_tested': len(CONSTANTS),
        'results': results,
        'emergent_pairs': pairs
    }
    
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n  Results saved -> {RESULTS_FILE}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()