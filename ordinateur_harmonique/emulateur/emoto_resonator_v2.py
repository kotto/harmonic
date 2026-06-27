#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMOTO RESONATOR v2 — Frequence Reelle de l'Eau comme Porteuse Emotionnelle
============================================================================
Extension du Emoto Resonator avec les FREQUENCES REELLES de la molecule d'eau.

Decouverte cle : la molecule H2O a des frequences de resonance specifiques
qui peuvent servir de PORTEUSE au champ emotionnel.

Frequences de l'eau :
  - Vibration O-H (stretch)        : 100 THz  (3 650 cm^-1, infrarouge)
  - Vibration O-H (bend)           :  48 THz  (1 595 cm^-1)
  - Rotation                       :  22 GHz  (micro-ondes)
  - Resonance micro-ondes (chauffage) : 2.45 GHz
  - Pont hydrogene                 :   5 THz  (collectif, clusters)
  - Resonance Schumann (Terre)     :   7.83 Hz (porteuse naturelle)

Hypothese : une pensee d'amour (onde constructive a la frequence de l'eau)
fait resonner les molecules en phase -> structures harmonieuses.
Une pensee de haine (onde destructive) brise cette resonance -> chaos.

Usage :
  python emoto_resonator_v2.py --demo
  python emoto_resonator_v2.py --sweep
"""

import numpy as np
import math, time, sys, os, argparse, random
from typing import Dict, Any, List, Tuple, Optional
from collections import deque
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HBit, PHI, PI, E, HARMONIC_CONSTANTS, H_CONSTANT_NAMES

# ==============================================================================
# FREQUENCES REELLES DE L'EAU (Hz)
# ==============================================================================

WATER_FREQUENCIES = {
    'oh_stretch':     100e12,     # 100 THz — vibration d'elongation O-H
    'oh_bend':         48e12,     #  48 THz — vibration de flexion H-O-H
    'rotation':        22e9,      #  22 GHz — rotation moleculaire
    'microwave':       2.45e9,    # 2.45 GHz — resonance micro-ondes (fours)
    'hydrogen_bond':    5e12,     #   5 THz — vibration des ponts hydrogene
    'cluster':          1e9,      #   1 GHz — resonance des clusters d'eau
    'schumann':         7.83,     # 7.83 Hz — resonance Schumann terrestre (porteuse naturelle)
}

# ==============================================================================
# ONDES EMOTIONNELLES (calibrees pour resonner avec l'eau)
# ==============================================================================

# Chaque emotion est un H-Bit. Mais ici, on l'applique en MODULATION
# sur la frequence porteuse de l'eau.

EMOTIONS_V2 = {
    'amour': {
        'label': 'Amour',
        'type': 'constructive',
        'modulation_depth': 0.3,      # Profondeur de modulation
        'phase_shift': 0.0,            # Alignement parfait des phases
        'coherence_boost': 1.5,        # Amplification de la coherence
        'description': 'Fait resonner les molecules en phase -> harmonie cristalline',
    },
    'compassion': {
        'label': 'Compassion',
        'type': 'constructive',
        'modulation_depth': 0.25,
        'phase_shift': PI / 16,        # Leger dephasage (douceur)
        'coherence_boost': 1.3,
        'description': 'Resonance douce -> structures organiques fluides',
    },
    'gratitude': {
        'label': 'Gratitude',
        'type': 'constructive',
        'modulation_depth': 0.28,
        'phase_shift': 0.0,
        'coherence_boost': 1.4,
        'description': 'Resonance stable -> symetrie hexagonale (beaute)',
    },
    'neutre': {
        'label': 'Neutre',
        'type': 'neutre',
        'modulation_depth': 0.05,
        'phase_shift': 0.0,
        'coherence_boost': 1.0,
        'description': 'Aucune modulation -> etat naturel aleatoire',
    },
    'peur': {
        'label': 'Peur',
        'type': 'destructive',
        'modulation_depth': 0.2,
        'phase_shift': PI / 4,         # Fort dephasage (desalignement)
        'coherence_boost': 0.7,        # Affaiblissement de la coherence
        'description': 'Desaligne les phases -> structures fragmente es',
    },
    'colere': {
        'label': 'Colere',
        'type': 'destructive',
        'modulation_depth': 0.35,
        'phase_shift': PI / 3,         # Tres fort dephasage
        'coherence_boost': 0.6,
        'description': 'Brise violemment la resonance -> eclatement chaotique',
    },
    'haine': {
        'label': 'Haine',
        'type': 'destructive',
        'modulation_depth': 0.4,
        'phase_shift': PI / 2,         # Opposition de phase totale
        'coherence_boost': 0.5,
        'description': 'Anti-resonance -> destruction de toute structure coherente',
    },
}


@dataclass
class WaterMolecule:
    """Molecule d'eau avec frequence propre et reponse a la modulation."""
    x: float = 0.0
    y: float = 0.0
    phi: float = 0.0          # Phase courante
    natural_freq: float = 0.0  # Frequence propre (depend du mode active)
    amplitude: float = 0.0     # Amplitude de vibration


class EmotoResonatorV2:
    """
    Simule l'effet d'un champ emotionnel module sur la frequence de l'eau.
    
    Principe physique :
      1. Chaque molecule d'eau a une frequence propre (vibration O-H)
      2. Le champ emotionnel MODULE cette frequence (comme une radio AM/FM)
      3. Amour = modulation constructive -> molecules en phase -> structure
      4. Haine = modulation destructive -> molecules dephasees -> chaos
      
    Ce modele est physiquement plausible : la modulation de frequence
    est le mecanisme par lequel une onde (la pensee) peut influencer
    la matiere (l'eau) SANS contact direct — juste par resonance.
    """
    
    def __init__(self, n_molecules: int = 200, grid_size: int = 128,
                 carrier_freq: str = 'hydrogen_bond'):
        self.n_molecules = n_molecules
        self.grid_size = grid_size
        
        # Choisir la frequence porteuse de l'eau
        if carrier_freq in WATER_FREQUENCIES:
            self.carrier_freq = WATER_FREQUENCIES[carrier_freq]
            self.carrier_name = carrier_freq
        else:
            # La plus proche de la resonance des clusters d'eau
            self.carrier_freq = WATER_FREQUENCIES['hydrogen_bond']
            self.carrier_name = 'hydrogen_bond'
        
        self.molecules = []
        self.emotion_field = None
        self.history = deque(maxlen=100)
        
        # Initialiser
        self._init_molecules()
    
    def _init_molecules(self):
        """Cree des molecules d'eau avec des frequences propres legerement variables."""
        self.molecules = []
        for i in range(self.n_molecules):
            # Chaque molecule a une frequence propre legerement differente
            # (distribution gaussienne autour de la porteuse)
            natural_freq = self.carrier_freq * random.gauss(1.0, 0.02)  # 2% de variation
            mol = WaterMolecule(
                x=random.uniform(-1, 1),
                y=random.uniform(-1, 1),
                phi=random.uniform(0, 2 * PI),
                natural_freq=natural_freq,
                amplitude=random.uniform(0.5, 1.5),
            )
            self.molecules.append(mol)
    
    def apply_emotion(self, emotion_name: str, intensite: float = 1.0, dt: float = 0.1):
        """
        Applique un champ emotionnel en MODULANT la frequence porteuse de l'eau.
        
        Mecanisme physique (modulation d'amplitude et de phase) :
          - Amour : modulation constructive -> TOUTES les molecules en phase
          - Haine : modulation destructive -> opposition de phase, chaos
        
        dt : pas de temps (simule l'evolution temporelle)
        """
        if emotion_name not in EMOTIONS_V2:
            raise ValueError(f"Emotion inconnue: {emotion_name}")
        
        self.emotion_field = EMOTIONS_V2[emotion_name]
        emotion = self.emotion_field
        
        # La modulation emotionnelle
        mod_depth = emotion['modulation_depth'] * intensite
        phase_shift = emotion['phase_shift'] * intensite
        coherence_boost = 1.0 + (emotion['coherence_boost'] - 1.0) * intensite
        
        # Appliquer a chaque molecule
        for mol in self.molecules:
            # 1. MODULATION DE FREQUENCE : l'emotion decale la frequence propre
            if emotion['type'] == 'constructive':
                # L'amour attire TOUTES les frequences vers la porteuse (syntonisation)
                freq_shift = (self.carrier_freq - mol.natural_freq) * mod_depth
                mol.natural_freq += freq_shift * dt
            elif emotion['type'] == 'destructive':
                # La haine repousse les frequences loin de la porteuse (desyntonisation)
                freq_shift = (mol.natural_freq - self.carrier_freq) * mod_depth
                mol.natural_freq += freq_shift * dt
            
            # 2. MODULATION DE PHASE
            # La phase evolue selon la frequence instantanee
            mol.phi += 2 * PI * mol.natural_freq * dt * 1e-12  # normalise
            
            # L'emotion ajoute un dephasage direct
            if emotion['type'] == 'constructive':
                # Amour : aligner toutes les phases
                target_phase = 0.0  # Phase de reference (harmonie)
                mol.phi = mol.phi * (1 - mod_depth) + target_phase * mod_depth
            elif emotion['type'] == 'destructive':
                # Haine : dephaser aleatoirement
                mol.phi += phase_shift * random.uniform(-1, 1)
            
            # 3. EFFET SUR LA POSITION (force de resonance)
            if emotion['type'] == 'constructive':
                # L'amour attire vers les nœuds de resonance (centre)
                r = math.sqrt(mol.x**2 + mol.y**2) + 1e-6
                force = mod_depth * coherence_boost * (1.0 - r)  # Force centripete
                mol.x += force * mol.x / r * dt
                mol.y += force * mol.y / r * dt
            elif emotion['type'] == 'destructive':
                # La haine repousse vers l'exterieur
                r = math.sqrt(mol.x**2 + mol.y**2) + 1e-6
                force = mod_depth * (2.0 - coherence_boost)  # Force centrifuge
                mol.x += force * mol.x / r * dt
                mol.y += force * mol.y / r * dt
            
            # 4. AMPLITUDE : l'emotion amplifie ou attenue la vibration
            mol.amplitude *= (1.0 + (coherence_boost - 1.0) * dt * 0.5)
            mol.amplitude = max(0.1, min(3.0, mol.amplitude))
            
            # Borner les positions
            mol.x = max(-2, min(2, mol.x))
            mol.y = max(-2, min(2, mol.y))
            mol.phi = mol.phi % (2 * PI)
    
    def measure_harmony(self) -> Dict[str, float]:
        """Mesure quantifiee de l'harmonie (identique a v1)."""
        if not self.molecules:
            return {k: 0.0 for k in ['radial_symmetry', 'angular_order', 'cluster_coherence', 'geometric_score', 'phase_coherence', 'frequency_coherence']}
        
        xs = np.array([m.x for m in self.molecules])
        ys = np.array([m.y for m in self.molecules])
        phis = np.array([m.phi for m in self.molecules])
        freqs = np.array([m.natural_freq for m in self.molecules])
        
        # Symetrie radiale
        r = np.sqrt(xs**2 + ys**2)
        r_sorted = np.sort(r)
        r_diffs = np.diff(r_sorted)
        r_diffs_norm = r_diffs / (np.mean(r_diffs) + 1e-12)
        radial_symmetry = 1.0 / (1.0 + np.std(r_diffs_norm))
        
        # Ordre angulaire
        angles = np.arctan2(ys, xs) % (2 * PI)
        angular_fft = np.abs(np.fft.fft(np.exp(1j * angles)))
        angular_order = np.max(angular_fft[1:6]) / len(angles)
        
        # Coherence des clusters
        centroid_x, centroid_y = np.mean(xs), np.mean(ys)
        dist_centroid = np.sqrt((xs - centroid_x)**2 + (ys - centroid_y)**2)
        cluster_coherence = 1.0 / (1.0 + np.std(dist_centroid))
        
        # Score geometrique
        geometric_score = (radial_symmetry + angular_order * 5 + cluster_coherence) / 7
        
        # Coherence des phases
        phase_coherence = 1.0 / (1.0 + np.std(phis))
        
        # NOUVEAU : Coherence des frequences (syntonisation)
        # Plus les frequences sont proches de la porteuse, plus c'est harmonieux
        freq_deviation = np.std(freqs) / self.carrier_freq
        frequency_coherence = 1.0 / (1.0 + freq_deviation * 100)
        
        return {
            'radial_symmetry': round(radial_symmetry, 4),
            'angular_order': round(angular_order, 4),
            'cluster_coherence': round(cluster_coherence, 4),
            'geometric_score': round(geometric_score, 4),
            'phase_coherence': round(phase_coherence, 4),
            'frequency_coherence': round(frequency_coherence, 4),
        }
    
    def generate_ascii_art(self, width: int = 40, height: int = 20) -> str:
        """Genere une representation ASCII de la structure moleculaire."""
        if not self.molecules:
            return "(vide)"
        
        grid = np.zeros((height, width))
        for mol in self.molecules:
            px = int((mol.x + 2) / 4 * width)
            py = int((mol.y + 2) / 4 * height)
            if 0 <= px < width and 0 <= py < height:
                grid[py, px] += 1
        
        if grid.max() > 0:
            grid = grid / grid.max()
        
        chars = ' .:-=+*#@'
        lines = []
        for y in range(height):
            line = ''
            for x in range(width):
                idx = int(grid[y, x] * (len(chars) - 1))
                line += chars[idx]
            lines.append(line)
        return '\n'.join(lines)
    
    def get_harmony_report(self) -> Dict[str, Any]:
        """Rapport complet."""
        metrics = self.measure_harmony()
        return {
            'emotion': self.emotion_field['label'] if self.emotion_field else 'aucune',
            'emotion_type': self.emotion_field['type'] if self.emotion_field else 'neutre',
            'carrier': f"{self.carrier_name} ({self.carrier_freq/1e12:.2f} THz)",
            'metrics': metrics,
            'ascii_art': self.generate_ascii_art(),
            'n_molecules': self.n_molecules,
        }


def demo_v2():
    """Demonstration avec la frequence reelle de l'eau."""
    print("=" * 70)
    print("  EMOTO RESONATOR v2 — Frequence Reelle de l'Eau")
    print("  Porteuse : liaison hydrogene (5 THz)")
    print("=" * 70)
    
    random.seed(42)
    np.random.seed(42)
    
    results = {}
    
    for emotion_name in ['neutre', 'amour', 'compassion', 'gratitude', 'peur', 'colere', 'haine']:
        res = EmotoResonatorV2(n_molecules=200, carrier_freq='hydrogen_bond')
        
        # Appliquer l'emotion sur 50 pas de temps
        for _ in range(50):
            res.apply_emotion(emotion_name, intensite=0.3, dt=0.2)
        
        report = res.get_harmony_report()
        results[emotion_name] = report
        
        emotion_label = EMOTIONS_V2[emotion_name]['label']
        m = report['metrics']
        gs = m['geometric_score']
        bar = '#' * int(gs * 30)
        
        print(f"\n  [{emotion_label:<12s}] Score: {gs:.4f} (freq_coh={m['frequency_coherence']:.4f}) {bar}")
        print(f"    Structure:")
        for line in report['ascii_art'].split('\n'):
            print(f"    {line}")
    
    # Tableau
    print(f"\n{'='*70}")
    print("  TABLEAU COMPARATIF — Modulation de la Frequence de l'Eau")
    print(f"{'='*70}")
    print(f"\n  {'Emotion':<12s} {'Type':<14s} {'Score Geo':>8s} {'Freq Coh':>8s} {'Phase Coh':>8s} {'Sym Rad':>8s}")
    print(f"  {'-'*12} {'-'*14} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    
    sorted_emotions = sorted(results.items(), key=lambda x: x[1]['metrics']['geometric_score'], reverse=True)
    
    for emotion_name, report in sorted_emotions:
        m = report['metrics']
        print(f"  {EMOTIONS_V2[emotion_name]['label']:<12s} {EMOTIONS_V2[emotion_name]['type']:<14s} {m['geometric_score']:8.4f} {m['frequency_coherence']:8.4f} {m['phase_coherence']:8.4f} {m['radial_symmetry']:8.4f}")
    
    # Verdict
    constructive_scores = [results[e]['metrics']['geometric_score'] for e in ['amour', 'compassion', 'gratitude']]
    destructive_scores = [results[e]['metrics']['geometric_score'] for e in ['peur', 'colere', 'haine']]
    avg_constructive = np.mean(constructive_scores)
    avg_destructive = np.mean(destructive_scores)
    
    print(f"\n  Score CONSTRUCTIF : {avg_constructive:.4f}")
    print(f"  Score DESTRUCTIF  : {avg_destructive:.4f}")
    print(f"  Ratio C/D         : {avg_constructive/avg_destructive:.2f}x")


def sweep_carrier():
    """Teste differentes frequences porteuses de l'eau."""
    print("=" * 70)
    print("  SWEEP — Quelle frequence de l'eau est la plus sensible ?")
    print("=" * 70)
    
    random.seed(42)
    np.random.seed(42)
    
    results = {}
    for carrier_name, carrier_freq in WATER_FREQUENCIES.items():
        res = EmotoResonatorV2(n_molecules=200, carrier_freq=carrier_name)
        for _ in range(50):
            res.apply_emotion('amour', intensite=0.3, dt=0.2)
        metrics = res.measure_harmony()
        results[carrier_name] = metrics
    
    print(f"\n  {'Porteuse':<20s} {'Frequence':>12s} {'Score Geo':>8s} {'Freq Coh':>8s} {'Phase Coh':>8s}")
    print(f"  {'-'*20} {'-'*12} {'-'*8} {'-'*8} {'-'*8}")
    
    sorted_results = sorted(results.items(), key=lambda x: x[1]['geometric_score'], reverse=True)
    for name, m in sorted_results:
        freq_str = f"{WATER_FREQUENCIES[name]/1e12:.2f} THz" if WATER_FREQUENCIES[name] > 1e12 else f"{WATER_FREQUENCIES[name]/1e9:.2f} GHz" if WATER_FREQUENCIES[name] > 1e9 else f"{WATER_FREQUENCIES[name]:.2f} Hz"
        print(f"  {name:<20s} {freq_str:>12s} {m['geometric_score']:8.4f} {m['frequency_coherence']:8.4f} {m['phase_coherence']:8.4f}")
    
    best = sorted_results[0]
    print(f"\n  Meilleure porteuse : {best[0]} ({WATER_FREQUENCIES[best[0]]/1e12:.2f} THz)")
    print(f"  -> L'eau est la plus sensible a la modulation sur cette frequence.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='Demo avec frequence reelle de l eau')
    parser.add_argument('--sweep', action='store_true', help='Tester toutes les frequences porteuses')
    args = parser.parse_args()
    
    if args.sweep:
        sweep_carrier()
    else:
        demo_v2()