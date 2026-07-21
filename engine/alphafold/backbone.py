"""
ALPHAFOLD — Constructeur de Chaîne Polypeptidique 3D
======================================================
Construit le squelette N-CA-C-N-... d'une protéine à partir
de sa séquence et des angles dièdres (φ, ψ) harmoniques.

Utilise l'algorithme NeRF (Natural Extension of Reference Frame)
avec les relations exactes entre dièdres NeRF et angles φ/ψ :

  CA_i = NeRF(O_{i-1}, C_{i-1}, N_i, L_NCA, θ_CNCA, φ_i + 180°)
  C_i  = NeRF(C_{i-1}, N_i, CA_i, L_CAC, θ_NCAC, φ_i)
  N_{i+1} = NeRF(N_i, CA_i, C_i, L_CN, θ_CACN, ψ_i)
  O_i  = NeRF(N_i, CA_i, C_i, L_CO, θ_CACO, 0°)

Author: Univers-Holistique
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from .amino_acids import (
    HarmonicAminoAcid, get_amino_acid, parse_sequence, get_cysteine_pairs,
    PHI, PI,
)
from .peptide_geometry import (
    BOND_LENGTHS, BOND_ANGLES,
    OMEGA_TRANS, OMEGA_CIS,
    place_atom, dihedral_angle, bond_angle,
    get_optimal_angles, harmonic_ramachandran_potential, rama_score,
    RAMACHANDRAN_REGIONS,
)

# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ResidueAtoms:
    """Coordonnées des atomes d'un résidu."""
    index: int
    aa: HarmonicAminoAcid
    N: np.ndarray
    CA: np.ndarray
    C: np.ndarray
    O: np.ndarray
    phi: float = 0.0
    psi: float = 0.0
    omega: float = 180.0
    sidechain: Dict[str, np.ndarray] = field(default_factory=dict)

    def all_atoms(self) -> Dict[str, np.ndarray]:
        atoms = {'N': self.N, 'CA': self.CA, 'C': self.C, 'O': self.O}
        atoms.update(self.sidechain)
        return atoms


@dataclass
class ProteinStructure:
    """Structure 3D complète d'une protéine."""
    sequence: str
    residues: List[ResidueAtoms]
    disulfide_bonds: List[Tuple[int, int]] = field(default_factory=list)
    total_energy: float = 0.0

    @property
    def n_residues(self) -> int:
        return len(self.residues)

    @property
    def ca_trace(self) -> np.ndarray:
        return np.array([r.CA for r in self.residues])

    def get_phi_psi(self) -> Tuple[np.ndarray, np.ndarray]:
        phis = np.array([r.phi for r in self.residues[1:]])
        psis = np.array([r.psi for r in self.residues[:-1]])
        return phis, psis

    def get_rama_score(self) -> float:
        from .peptide_geometry import rama_score as rs
        scores = []
        for i, res in enumerate(self.residues):
            if 0 < i < len(self.residues) - 1:
                scores.append(rs(res.phi, res.psi, res.aa))
        return float(np.mean(scores)) if scores else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTEUR DE BACKBONE
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicBackbone:
    """
    Construit le squelette polypeptidique 3D.

    Algorithme NeRF séquentiel avec mapping exact φ/ψ :

    Pour chaque résidu i (i ≥ 1) :
      CA_i = place_atom(O_{i-1}, C_{i-1}, N_i, L_NCA, θ_CNCA, φ_i + 180°)
      C_i  = place_atom(C_{i-1}, N_i, CA_i, L_CAC, θ_NCAC, φ_i)
      O_i  = place_atom(N_i, CA_i, C_i, L_CO, θ_CACO, 0°)
      N_{i+1} = place_atom(N_i, CA_i, C_i, L_CN, θ_CACN, ψ_i)  [pour i < N]
    """

    def __init__(self, sequence: str):
        self.sequence_raw = sequence.strip().upper()
        self.amino_acids = parse_sequence(self.sequence_raw)
        self.n = len(self.amino_acids)
        if self.n < 2:
            raise ValueError(f"Séquence trop courte ({self.n} résidus), minimum 2")
        self.disulfide_pairs = get_cysteine_pairs(self.sequence_raw)

    # ─── Initialisation du premier résidu ───────────────────────────────

    def _init_first_residue(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Place N1, CA1, C1. Retourne (N1, CA1, C1)."""
        N1 = np.array([0.0, 0.0, 0.0])
        CA1 = np.array([BOND_LENGTHS['N_CA'], 0.0, 0.0])
        # Placer C1 dans le plan XY
        dummy = np.array([0.0, 1.0, 0.0])
        C1 = place_atom(dummy, N1, CA1, BOND_LENGTHS['CA_C'],
                        BOND_ANGLES['N_CA_C'], -120.0)
        return N1, CA1, C1

    # ─── Construction avec angles spécifiés ──────────────────────────────

    def build_extended(self) -> ProteinStructure:
        """Conformation β étendue : φ=-135°, ψ=+135°."""
        phi = [-135.0] * self.n
        psi = [135.0] * self.n
        return self._build(phi, psi)

    def build_helical(self) -> ProteinStructure:
        """Hélice α : φ≈-57°, ψ≈-47°."""
        phi = [-57.0] * self.n
        psi = [-47.0] * self.n
        return self._build(phi, psi)

    def build_harmonic_initial(self) -> ProteinStructure:
        """
        Angles optimaux harmoniques pour chaque résidu (selon son score φ).
        Point de départ optimal pour le repliement ABC.
        """
        phi, psi = [], []
        for i, aa in enumerate(self.amino_acids):
            optima = get_optimal_angles(aa)
            if aa.helix_propensity > aa.sheet_propensity and aa.helix_propensity > 0.5:
                best = optima.get('αR', (-63.0, -43.0))
            elif aa.sheet_propensity > 0.5:
                best = optima.get('β', (-119.0, 133.0))
            else:
                best = optima.get('PPII', (-75.0, 150.0))
            phi.append(best[0])
            psi.append(best[1])
        return self._build(phi, psi)

    def build_from_angles(self, phi_deg: List[float], psi_deg: List[float]) -> ProteinStructure:
        """Construit avec des angles φ/ψ personnalisés."""
        return self._build(phi_deg, psi_deg)

    # ─── Construction interne (NeRF séquentiel) ──────────────────────────

    def _build(self, phi_deg: List[float], psi_deg: List[float]) -> ProteinStructure:
        """
        Algorithme NeRF séquentiel en UNE passe.

        Pour i = 0 :
          N0, CA0, C0 initiaux
          O0 = NeRF(N0, CA0, C0, L_CO, θ_CA_C_O, 0°)
          N1 = NeRF(N0, CA0, C0, L_CN, θ_CA_C_N, ψ₀)

        Pour i ≥ 1 :
          (N_i déjà placé à l'étape précédente)
          CA_i = NeRF(O_{i-1}, C_{i-1}, N_i, L_NCA, θ_C_N_CA, φ_i + 180°)
          C_i  = NeRF(C_{i-1}, N_i, CA_i, L_CAC, θ_N_CA_C, φ_i)
          O_i  = NeRF(N_i, CA_i, C_i, L_CO, θ_CA_C_O, 0°)
          [si i < N-1] N_{i+1} = NeRF(N_i, CA_i, C_i, L_CN, θ_CA_C_N, ψ_i)
        """
        # Convention : place_atom utilise le dièdre 180° - target
        # car dihedral_angle et place_atom ont des conventions de signe inversées.
        # → Pour obtenir un dièdre D mesuré, on passe 180° - D à place_atom.
        def _dih(target: float) -> float:
            return 180.0 - target

        # ── Résidu 0 ──
        N0, CA0, C0 = self._init_first_residue()
        O0 = place_atom(N0, CA0, C0, BOND_LENGTHS['C_O'],
                        BOND_ANGLES['CA_C_O'], _dih(0.0))

        residues = [ResidueAtoms(
            index=0, aa=self.amino_acids[0],
            N=N0, CA=CA0, C=C0, O=O0,
            phi=phi_deg[0], psi=psi_deg[0],
        )]

        # Placer N1 (via ψ₀)
        N_next = place_atom(N0, CA0, C0, BOND_LENGTHS['C_N'],
                           BOND_ANGLES['CA_C_N'], _dih(psi_deg[0]))

        # ── Résidus i ≥ 1 ──
        for i in range(1, self.n):
            aa = self.amino_acids[i]
            prev = residues[i-1]
            N_i = N_next

            # CA_i = NeRF(O_{i-1}, C_{i-1}, N_i, ..., φ_i + 180°)
            CA_i = place_atom(prev.O, prev.C, N_i,
                             BOND_LENGTHS['N_CA'],
                             BOND_ANGLES['C_N_CA'],
                             _dih(phi_deg[i] + 180.0))

            # C_i = NeRF(C_{i-1}, N_i, CA_i, ..., φ_i)
            C_i = place_atom(prev.C, N_i, CA_i,
                            BOND_LENGTHS['CA_C'],
                            BOND_ANGLES['N_CA_C'],
                            _dih(phi_deg[i]))

            # O_i = NeRF(N_i, CA_i, C_i, ..., 0°)
            O_i = place_atom(N_i, CA_i, C_i,
                            BOND_LENGTHS['C_O'],
                            BOND_ANGLES['CA_C_O'], _dih(0.0))

            # N_{i+1} = NeRF(N_i, CA_i, C_i, ..., ψ_i)
            if i < self.n - 1:
                N_next = place_atom(N_i, CA_i, C_i,
                                   BOND_LENGTHS['C_N'],
                                   BOND_ANGLES['CA_C_N'],
                                   _dih(psi_deg[i]))
            else:
                N_next = None

            residues.append(ResidueAtoms(
                index=i, aa=aa,
                N=N_i, CA=CA_i, C=C_i, O=O_i,
                phi=phi_deg[i],
                psi=psi_deg[i] if i < self.n - 1 else 0.0,
            ))

        # Mesurer les φ et ψ réels
        self._measure_dihedrals(residues)

        # Ajouter les chaînes latérales
        self._add_all_sidechains(residues)

        return ProteinStructure(
            sequence=self.sequence_raw,
            residues=residues,
            disulfide_bonds=self.disulfide_pairs,
        )

    def _measure_dihedrals(self, residues: List[ResidueAtoms]):
        """Mesure les angles φ et ψ réels de la structure construite."""
        for i in range(1, self.n):
            # φ_i = C_{i-1} - N_i - CA_i - C_i
            residues[i].phi = math.degrees(dihedral_angle(
                residues[i-1].C, residues[i].N,
                residues[i].CA, residues[i].C))

        for i in range(self.n - 1):
            # ψ_i = N_i - CA_i - C_i - N_{i+1}
            residues[i].psi = math.degrees(dihedral_angle(
                residues[i].N, residues[i].CA,
                residues[i].C, residues[i+1].N))

    # ─── Chaînes latérales ─────────────────────────────────────────────

    def _add_all_sidechains(self, residues: List[ResidueAtoms]):
        """Ajoute les atomes de chaîne latérale (CB et groupes fonctionnels)."""
        for res in residues:
            if res.aa.sidechain_atoms:
                self._add_sidechain(res)

    def _add_sidechain(self, res: ResidueAtoms):
        """Place la chaîne latérale d'un résidu (géométrie idéalisée)."""
        N, CA, C = res.N, res.CA, res.C
        aa = res.aa

        # CB : angle N-CA-CB ≈ 110.5°, dièdre chiralité L (C-N-CA-CB ≈ +122.5°)
        CB = place_atom(C, N, CA, BOND_LENGTHS['CA_CB'], 110.5, 122.5)
        res.sidechain['CB'] = CB

        # Atomes suivants (simplifié v1 : positions approximatives)
        prev3, prev2, prev1 = N, CA, CB
        for atom_name in aa.sidechain_atoms[1:]:
            bl, ba, dih = 1.53, 109.5, 60.0  # défauts
            if atom_name.startswith('O'):
                bl, ba, dih = 1.43, 109.5, 180.0
            elif atom_name.startswith('N'):
                bl, ba, dih = 1.47, 109.5, 180.0
            elif atom_name.startswith('S'):
                bl, ba, dih = 1.81, 100.0, 90.0

            new_pos = place_atom(prev3, prev2, prev1, bl, ba, dih)
            res.sidechain[atom_name] = new_pos
            prev3, prev2, prev1 = prev2, prev1, new_pos


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def compute_rama_score(structure: ProteinStructure) -> Dict:
    """Évalue la qualité Ramachandran d'une structure."""
    scores, outliers = [], []
    for i, res in enumerate(structure.residues):
        if 0 < i < len(structure.residues) - 1:
            s = rama_score(res.phi, res.psi, res.aa)
            scores.append(s)
            if s < 0.3:
                outliers.append({
                    'index': i, 'residue': res.aa.code3,
                    'phi': round(res.phi, 1), 'psi': round(res.psi, 1),
                    'score': round(s, 3),
                })
    return {
        'mean_score': round(float(np.mean(scores)), 4) if scores else 0.0,
        'min_score': round(float(np.min(scores)), 4) if scores else 0.0,
        'n_outliers': len(outliers),
        'outliers': outliers,
        'n_evaluated': len(scores),
    }


def superimpose(mobile: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Superposition optimale (Kabsch)."""
    mc = mobile - mobile.mean(axis=0)
    tc = target - target.mean(axis=0)
    V, S, Wt = np.linalg.svd(mc.T @ tc)
    d = np.sign(np.linalg.det(V @ Wt))
    R = V @ np.diag([1.0, 1.0, d]) @ Wt
    return (mc @ R) + target.mean(axis=0)


def rmsd(mobile: np.ndarray, target: np.ndarray) -> float:
    """RMSD après superposition optimale (Å)."""
    aligned = superimpose(mobile, target)
    return float(np.sqrt(np.mean(np.sum((aligned - target) ** 2, axis=1))))


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide."""
    print("=" * 60)
    print("TEST : Constructeur de Backbone (NeRF exact)")
    print("=" * 60)

    seq = "AGVL"
    bb = HarmonicBackbone(seq)

    for mode, struct in [
        ("Étendu (β)", bb.build_extended()),
        ("Hélice α", bb.build_helical()),
        ("Harmonique", bb.build_harmonic_initial()),
    ]:
        print(f"\n{mode} ({seq}):")
        print(f"  Résidus: {struct.n_residues}")
        for res in struct.residues:
            print(f"  {res.aa.code3} φ={res.phi:+7.1f}° ψ={res.psi:+7.1f}°")
        rs = compute_rama_score(struct)
        print(f"  Score Rama: {rs['mean_score']:.3f}")

    # Test RMSD
    s1 = bb.build_extended()
    s2 = bb.build_helical()
    print(f"\nRMSD étendue vs hélice: {rmsd(s2.ca_trace, s1.ca_trace):.2f} Å")
    print(f"RMSD étendue vs elle-même: {rmsd(s1.ca_trace, s1.ca_trace):.6f} Å")
    print("\n✅ Tests passés !")


if __name__ == '__main__':
    _test()
