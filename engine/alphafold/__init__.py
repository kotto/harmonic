"""
ALPHAFOLD — Repliement Protéique par Résonance Harmonique Déterministe
=======================================================================
Approche 100% déterministe du repliement protéique :
  - Chaque acide aminé = oscillateur harmonique (fréquence ∝ score φ)
  - Chaîne polypeptidique = oscillateurs couplés
  - Repliement = cascade de résonance minimisant l'énergie d'interférence
  - Dynamique ABC à l'ordre α = 1/φ (mémoire non-locale)
  - Zéro paramètre appris, zéro GPU, zéro hallucination

Contrairement à AlphaFold (DeepMind) qui utilise des transformers
et un entraînement massif sur la PDB, cette approche est fondée
sur les premiers principes harmoniques découverts le 22/05/2026.

Constantes fondamentales gouvernant le repliement :
  {φ, π, e, √2, √3, √5, e/π}

Author: Kotto Alain / Univers-Holistique
Version: 1.0.0
"""

# ── Acides Aminés Harmoniques ──────────────────────────────────────────
from .amino_acids import (
    HarmonicAminoAcid, FunctionalGroup,
    get_amino_acid, parse_sequence, get_harmonic_profile,
    get_cysteine_pairs,
    AMINO_ACIDS,
    PHI, ALPHA, PI, E, SQRT2, SQRT3, SQRT5, E_PI,
)

# ── Géométrie Peptidique ──────────────────────────────────────────────
from .peptide_geometry import (
    RamachandranRegion, RAMACHANDRAN_REGIONS,
    harmonic_ramachandran_potential, get_optimal_angles,
    rama_score, is_rama_allowed,
    place_atom, dihedral_angle, bond_angle,
    BOND_LENGTHS, BOND_ANGLES,
)

# ── Constructeur de Backbone ──────────────────────────────────────────
from .backbone import (
    HarmonicBackbone, ProteinStructure, ResidueAtoms,
    compute_rama_score, superimpose, rmsd,
)

# ── Énergie Harmonique ────────────────────────────────────────────────
from .harmonic_energy import (
    HarmonicEnergy, EnergyBreakdown,
    compute_energy, compute_per_residue_energy,
)

# ── Dynamique de Repliement ABC ───────────────────────────────────────
from .abc_folder import (
    ABCProteinFolder, ABCMemoryKernel, FoldResult,
    fold_protein, predict_structure,
)

# ── I/O et Métriques ─────────────────────────────────────────────────
from .structure_io import (
    parse_pdb, write_pdb, parse_fasta,
    compute_tm_score, compute_gdt_ts, compare_structures,
)

# ── Visualisation ─────────────────────────────────────────────────────
from .visualization import (
    phi_color, residue_color, ribbon_data,
    wave_field_slice, pymol_script, structure_summary,
)

# ── Démonstrations ───────────────────────────────────────────────────
from .demo import (
    DEMO_PROTEINS, demo_protein, demo_compare_with_pdb,
    run_all_demos, main as demo_main,
)

__version__ = '1.0.0'
__author__ = 'Kotto Alain / Univers-Holistique'

__all__ = [
    # Acides aminés
    'HarmonicAminoAcid', 'FunctionalGroup',
    'get_amino_acid', 'parse_sequence', 'get_harmonic_profile',
    'get_cysteine_pairs', 'AMINO_ACIDS',
    # Constantes
    'PHI', 'ALPHA', 'PI', 'E', 'SQRT2', 'SQRT3', 'SQRT5', 'E_PI',
    # Géométrie
    'RamachandranRegion', 'RAMACHANDRAN_REGIONS',
    'harmonic_ramachandran_potential', 'get_optimal_angles',
    'rama_score', 'is_rama_allowed',
    'place_atom', 'dihedral_angle', 'bond_angle',
    'BOND_LENGTHS', 'BOND_ANGLES',
    # Backbone
    'HarmonicBackbone', 'ProteinStructure', 'ResidueAtoms',
    'compute_rama_score', 'superimpose', 'rmsd',
    # Énergie
    'HarmonicEnergy', 'EnergyBreakdown',
    'compute_energy', 'compute_per_residue_energy',
    # Repliement
    'ABCProteinFolder', 'ABCMemoryKernel', 'FoldResult',
    'fold_protein', 'predict_structure',
    # I/O
    'parse_pdb', 'write_pdb', 'parse_fasta',
    'compute_tm_score', 'compute_gdt_ts', 'compare_structures',
    # Visualisation
    'phi_color', 'residue_color', 'ribbon_data',
    'wave_field_slice', 'pymol_script', 'structure_summary',
    # Démo
    'DEMO_PROTEINS', 'demo_protein', 'demo_compare_with_pdb',
    'run_all_demos', 'demo_main',
]
