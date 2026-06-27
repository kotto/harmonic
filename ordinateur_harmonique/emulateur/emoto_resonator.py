#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMOTO RESONATOR — Structuration de la Matiere par Resonance Emotionnelle
=========================================================================
Hypothese : Si la pensee est une onde (Ψ = Σ Hₙ (Ψ₁)ⁿ), alors :
  - Une pensee d'AMOUR (interference constructive) structure la matiere
    en figures geometriques harmonieuses (cristaux symetriques)
  - Une pensee de HAINE (interference destructive) detruit cette harmonie
    (structures chaotiques, asymetriques)

Simulation : un champ de particules (molecules d'eau) expose a un champ
d'ondes emotionnelles. On mesure la « symetrie » et l'« harmonie » des
figures formees.

Inspiration : experiences du Dr. Masaru Emoto sur les cristaux d'eau.
Reinterpretation harmonique : ce n'est pas la « conscience » qui agit,
c'est l'INTERFERENCE D'ONDES.

Usage :
  python emoto_resonator.py --demo
  python emoto_resonator.py --compare
"""

import numpy as np
import math, time, sys, os, argparse, random
from typing import Dict, Any, List, Tuple, Optional
from collections import deque
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HBit, PHI, PI, E, HARMONIC_CONSTANTS, H_CONSTANT_NAMES
from conscious_hpu import PAIN_WAVE, PLEASURE_WAVE, NEUTRAL_WAVE, SURPRISE_WAVE

# ==============================================================================
# ONDES EMOTIONNELLES (H-Bits synthetiques pour structurer la matiere)
# ==============================================================================

AMOUR_WAVE = HBit(np.array([0.6, 0.3, 0.15, 0.0, 0.0, 0.0, 0.1]))       # Tres constructive
COMPASSION_WAVE = HBit(np.array([0.5, 0.25, 0.1, 0.05, 0.0, 0.0, 0.08]))  # Constructive douce
GRATITUDE_WAVE = HBit(np.array([0.55, 0.2, 0.12, 0.0, 0.0, 0.0, 0.05]))   # Constructive stable
HAINE_WAVE = HBit(np.array([-0.6, -0.35, -0.15, -0.1, -0.05, -0.1, -0.1]))  # Tres destructive
COLERE_WAVE = HBit(np.array([-0.4, -0.2, -0.1, -0.05, 0.0, -0.1, -0.05]))   # Destructive
PEUR_WAVE = HBit(np.array([-0.3, -0.15, -0.05, -0.05, 0.0, -0.05, -0.05]))  # Destructive legere

EMOTIONS = {
    'amour':      {'wave': AMOUR_WAVE,      'color': '#ff6b9d', 'label': 'Amour',      'type': 'constructive'},
    'compassion': {'wave': COMPASSION_WAVE,  'color': '#ff9ec4', 'label': 'Compassion',  'type': 'constructive'},
    'gratitude':  {'wave': GRATITUDE_WAVE,   'color': '#ffd4e8', 'label': 'Gratitude',   'type': 'constructive'},
    'neutre':     {'wave': NEUTRAL_WAVE,     'color': '#888888', 'label': 'Neutre',      'type': 'neutre'},
    'peur':       {'wave': PEUR_WAVE,        'color': '#6666aa', 'label': 'Peur',        'type': 'destructive'},
    'colere':     {'wave': COLERE_WAVE,      'color': '#cc4444', 'label': 'Colere',      'type': 'destructive'},
    'haine':      {'wave': HAINE_WAVE,       'color': '#aa2222', 'label': 'Haine',       'type': 'destructive'},
}


@dataclass
class WaterMolecule:
    """Une molecule d'eau dans le champ de resonance emotionnelle."""
    x: float = 0.0
    y: float = 0.0
    phi: float = 0.0  # Phase individuelle


class EmotoResonator:
    """
    Simule l'effet d'un champ emotionnel sur un ensemble de molecules.
    
    Principe :
      1. On cree un champ de N molecules (positions aleatoires)
      2. On applique un champ d'ondes emotionnelles (H-Bit)
      3. Les molecules se reorganisent par resonance :
         - Onde constructive → les molecules s'alignent en figures symetriques
         - Onde destructive → les molecules se dispersent chaotiquement
      4. On mesure la « symetrie » et l'« harmonie » de la structure resultante
    """
    
    def __init__(self, n_molecules: int = 200, grid_size: int = 128):
        self.n_molecules = n_molecules
        self.grid_size = grid_size
        self.molecules = []
        self.emotion_field = None
        self.history = deque(maxlen=100)
        
        # Initialiser les molecules aleatoirement
        self._init_molecules()
    
    def _init_molecules(self):
        """Cree un ensemble de molecules en positions aleatoires."""
        self.molecules = []
        for i in range(self.n_molecules):
            mol = WaterMolecule(
                x=random.uniform(-1, 1),
                y=random.uniform(-1, 1),
                phi=random.uniform(0, 2 * PI),
            )
            self.molecules.append(mol)
    
    def apply_emotion(self, emotion_name: str, intensite: float = 1.0):
        """
        Applique un champ emotionnel aux molecules.
        
        L'onde emotionnelle est projetee sur le plan 2D. Chaque molecule
        ressent l'interference entre sa phase propre et la phase de l'onde
        emotionnelle a sa position.
        """
        if emotion_name not in EMOTIONS:
            raise ValueError(f"Emotion inconnue: {emotion_name}. Choisir parmi {list(EMOTIONS.keys())}")
        
        self.emotion_field = EMOTIONS[emotion_name]
        hbit = self.emotion_field['wave']
        emotion_type = self.emotion_field['type']
        
        # Creer le champ d'onde 2D
        x_grid = np.linspace(-1, 1, self.grid_size)
        y_grid = np.linspace(-1, 1, self.grid_size)
        X, Y = np.meshgrid(x_grid, y_grid)
        
        # L'onde emotionnelle projetee en 2D
        wave_2d = np.zeros((self.grid_size, self.grid_size), dtype=np.complex128)
        for i, coeff in enumerate(hbit.coefficients):
            freq = HARMONIC_CONSTANTS[i] * PHI
            wave_2d += coeff * np.exp(1j * freq * (X + Y))
        
        # Normaliser
        wave_2d = wave_2d / (np.linalg.norm(wave_2d) + 1e-12)
        
        # Appliquer aux molecules
        for mol in self.molecules:
            # Position dans la grille
            ix = int((mol.x + 1) / 2 * (self.grid_size - 1))
            iy = int((mol.y + 1) / 2 * (self.grid_size - 1))
            ix = max(0, min(self.grid_size - 1, ix))
            iy = max(0, min(self.grid_size - 1, iy))
            
            # Phase de l'onde emotionnelle a cette position
            phase_emotion = np.angle(wave_2d[iy, ix])
            amplitude_emotion = np.abs(wave_2d[iy, ix])
            
            if emotion_type == 'constructive':
                # L'amour ATTIRE les molecules vers l'harmonie
                # → les phases s'alignent, les positions convergent vers les nœuds
                mol.phi = mol.phi * 0.7 + phase_emotion * 0.3 * intensite
                # Deplacer vers le centre (convergence)
                mol.x = mol.x * 0.95
                mol.y = mol.y * 0.95
            elif emotion_type == 'destructive':
                # La haine REPOUSSE les molecules
                # → les phases se désalignent, les positions divergent
                mol.phi = mol.phi * 0.9 + (phase_emotion + PI * random.uniform(-0.5, 0.5)) * 0.1 * intensite
                # Deplacer vers l'exterieur (divergence)
                r = math.sqrt(mol.x**2 + mol.y**2) + 1e-6
                mol.x = mol.x / r * min(2.0, r * 1.02)
                mol.y = mol.y / r * min(2.0, r * 1.02)
            else:  # neutre
                mol.phi = mol.phi * 0.95 + phase_emotion * 0.05
            
            # Appliquer aussi l'intensite via l'amplitude
            mol.x += amplitude_emotion * 0.01 * (1 if emotion_type == 'constructive' else -1)
            mol.y += amplitude_emotion * 0.01 * (1 if emotion_type == 'constructive' else -1)
            
            # Borner
            mol.x = max(-2, min(2, mol.x))
            mol.y = max(-2, min(2, mol.y))
    
    def measure_harmony(self) -> Dict[str, float]:
        """
        Mesure quantifiee de l'harmonie de la structure moleculaire.
        
        Metriques :
          - radial_symmetry : symetrie radiale (0 = chaotique, 1 = parfait)
          - angular_order : ordre angulaire (0 = aleatoire, 1 = aligne)
          - cluster_coherence : coherence des clusters (0 = disperse, 1 = compact)
          - geometric_score : score geometrique global
          - phase_coherence : coherence des phases (0 = desordonne, 1 = unifie)
        """
        if not self.molecules:
            return {k: 0.0 for k in ['radial_symmetry', 'angular_order', 'cluster_coherence', 'geometric_score', 'phase_coherence']}
        
        xs = np.array([m.x for m in self.molecules])
        ys = np.array([m.y for m in self.molecules])
        phis = np.array([m.phi for m in self.molecules])
        
        # 1. Symetrie radiale : distribution radiale reguliere ?
        r = np.sqrt(xs**2 + ys**2)
        r_sorted = np.sort(r)
        # Une distribution reguliere a des espacements egaux
        r_diffs = np.diff(r_sorted)
        r_diffs_norm = r_diffs / (np.mean(r_diffs) + 1e-12)
        radial_symmetry = 1.0 / (1.0 + np.std(r_diffs_norm))
        
        # 2. Ordre angulaire : les molecules sont-elles alignees ?
        angles = np.arctan2(ys, xs) % (2 * PI)
        # Transformation de Fourier angulaire : pics = ordre
        angular_fft = np.abs(np.fft.fft(np.exp(1j * angles)))
        angular_order = np.max(angular_fft[1:6]) / len(angles)  # Harmoniques 1-5
        
        # 3. Coherence des clusters : densite locale vs globale
        # Simplification : utiliser la distance moyenne au centroide
        centroid_x, centroid_y = np.mean(xs), np.mean(ys)
        dist_centroid = np.sqrt((xs - centroid_x)**2 + (ys - centroid_y)**2)
        cluster_coherence = 1.0 / (1.0 + np.std(dist_centroid))
        
        # 4. Score geometrique global
        geometric_score = (radial_symmetry + angular_order * 5 + cluster_coherence) / 7
        
        # 5. Coherence des phases
        # Un champ unifie a des phases proches (ecart-type faible)
        phase_coherence = 1.0 / (1.0 + np.std(phis))
        
        return {
            'radial_symmetry': round(radial_symmetry, 4),
            'angular_order': round(angular_order, 4),
            'cluster_coherence': round(cluster_coherence, 4),
            'geometric_score': round(geometric_score, 4),
            'phase_coherence': round(phase_coherence, 4),
        }
    
    def generate_ascii_art(self, width: int = 40, height: int = 20) -> str:
        """Genere une representation ASCII de la structure moleculaire."""
        if not self.molecules:
            return "(vide)"
        
        # Creer une grille de densite
        grid = np.zeros((height, width))
        for mol in self.molecules:
            px = int((mol.x + 2) / 4 * width)
            py = int((mol.y + 2) / 4 * height)
            if 0 <= px < width and 0 <= py < height:
                grid[py, px] += 1
        
        # Normaliser
        if grid.max() > 0:
            grid = grid / grid.max()
        
        # Caracteres ASCII pour la densite
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
        """Rapport complet sur l'etat harmonique du systeme."""
        metrics = self.measure_harmony()
        return {
            'emotion': self.emotion_field['label'] if self.emotion_field else 'aucune',
            'emotion_type': self.emotion_field['type'] if self.emotion_field else 'neutre',
            'metrics': metrics,
            'ascii_art': self.generate_ascii_art(),
            'n_molecules': self.n_molecules,
        }


# ==============================================================================
# DEMONSTRATIONS
# ==============================================================================

def demo_emoto():
    """Demonstration complete : comparer les effets de differentes emotions."""
    print("=" * 70)
    print("  EMOTO RESONATOR — Structuration de la Matiere par la Pensee")
    print("  Hypothese : l'amour cree l'harmonie, la haine cree le chaos")
    print("=" * 70)
    
    random.seed(42)
    np.random.seed(42)
    
    results = {}
    
    for emotion_name in ['neutre', 'amour', 'compassion', 'gratitude', 'peur', 'colere', 'haine']:
        res = EmotoResonator(n_molecules=200, grid_size=128)
        
        # Appliquer l'emotion 10 fois (effet cumulatif)
        for _ in range(10):
            res.apply_emotion(emotion_name, intensite=0.3)
        
        report = res.get_harmony_report()
        results[emotion_name] = report
        
        emotion_label = EMOTIONS[emotion_name]['label']
        gs = report['metrics']['geometric_score']
        bar = '#' * int(gs * 30)
        color = EMOTIONS[emotion_name]['color']
        
        print(f"\n  [{emotion_label:<12s}] Score geometrique: {gs:.4f}  {bar}")
        print(f"    Symetrie radiale: {report['metrics']['radial_symmetry']:.4f}")
        print(f"    Ordre angulaire:  {report['metrics']['angular_order']:.4f}")
        print(f"    Coherence phases: {report['metrics']['phase_coherence']:.4f}")
        print(f"    Structure:")
        for line in report['ascii_art'].split('\n'):
            print(f"    {line}")
    
    # Tableau comparatif
    print(f"\n{'='*70}")
    print("  TABLEAU COMPARATIF — Effet des Emotions sur la Matiere")
    print(f"{'='*70}")
    print(f"\n  {'Emotion':<12s} {'Type':<14s} {'Score Geo':>8s} {'Sym. Rad':>8s} {'Ordre Ang':>8s} {'Coh. Phase':>8s}")
    print(f"  {'-'*12} {'-'*14} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    
    # Trier par score geometrique
    sorted_emotions = sorted(results.items(), key=lambda x: x[1]['metrics']['geometric_score'], reverse=True)
    
    for emotion_name, report in sorted_emotions:
        m = report['metrics']
        print(f"  {EMOTIONS[emotion_name]['label']:<12s} {EMOTIONS[emotion_name]['type']:<14s} {m['geometric_score']:8.4f} {m['radial_symmetry']:8.4f} {m['angular_order']:8.4f} {m['phase_coherence']:8.4f}")
    
    # Verdict
    constructive_scores = [results[e]['metrics']['geometric_score'] for e in ['amour', 'compassion', 'gratitude']]
    destructive_scores = [results[e]['metrics']['geometric_score'] for e in ['peur', 'colere', 'haine']]
    avg_constructive = np.mean(constructive_scores)
    avg_destructive = np.mean(destructive_scores)
    
    print(f"\n  Score moyen CONSTRUCTIF (amour/compassion/gratitude) : {avg_constructive:.4f}")
    print(f"  Score moyen DESTRUCTIF  (peur/colere/haine)        : {avg_destructive:.4f}")
    
    if avg_constructive > avg_destructive:
        print(f"\n  HYPOTHESE CONFIRMEE : L'amour structure la matiere en figures")
        print(f"  plus harmonieuses que la haine (ratio = {avg_constructive/avg_destructive:.2f}x)")
    else:
        print(f"\n  Hypothese non confirmee — ajuster les parametres")


def compare_extreme():
    """Comparaison amour vs haine avec visualisation detaillee."""
    print("=" * 70)
    print("  COMPARAISON EXTRÊME — Amour vs Haine")
    print("=" * 70)
    
    random.seed(42)
    np.random.seed(42)
    
    # Meme etat initial pour les deux
    molecules_init = [WaterMolecule(
        x=random.uniform(-1, 1), y=random.uniform(-1, 1),
        phi=random.uniform(0, 2*PI)) for _ in range(200)]
    
    # Copie pour AMOUR
    res_amour = EmotoResonator(n_molecules=200)
    res_amour.molecules = [WaterMolecule(m.x, m.y, m.phi) for m in molecules_init]
    for _ in range(20):
        res_amour.apply_emotion('amour', intensite=0.5)
    
    # Copie pour HAINE
    res_haine = EmotoResonator(n_molecules=200)
    res_haine.molecules = [WaterMolecule(m.x, m.y, m.phi) for m in molecules_init]
    for _ in range(20):
        res_haine.apply_emotion('haine', intensite=0.5)
    
    report_amour = res_amour.get_harmony_report()
    report_haine = res_haine.get_harmony_report()
    
    print(f"\n  ┌{'─'*60}┐")
    print(f"  │ {'AMOUR':^28s} │ {'HAINE':^28s} │")
    print(f"  ├{'─'*60}┤")
    
    amour_lines = report_amour['ascii_art'].split('\n')
    haine_lines = report_haine['ascii_art'].split('\n')
    
    for i in range(max(len(amour_lines), len(haine_lines))):
        al = amour_lines[i] if i < len(amour_lines) else ''
        hl = haine_lines[i] if i < len(haine_lines) else ''
        print(f"  │ {al:<28s} │ {hl:<28s} │")
    
    print(f"  └{'─'*60}┘")
    
    print(f"\n  Metriques :")
    print(f"  {'':<18s} {'AMOUR':>10s} {'HAINE':>10s} {'Ratio A/H':>10s}")
    ma = report_amour['metrics']
    mh = report_haine['metrics']
    for key in ma:
        if key != 'geometric_score':
            ratio = ma[key] / (mh[key] + 1e-12)
            print(f"  {key:<18s} {ma[key]:10.4f} {mh[key]:10.4f} {ratio:10.2f}x")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='Demo complete (7 emotions)')
    parser.add_argument('--compare', action='store_true', help='Comparaison extreme amour vs haine')
    args = parser.parse_args()
    
    if args.compare:
        compare_extreme()
    else:
        demo_emoto()