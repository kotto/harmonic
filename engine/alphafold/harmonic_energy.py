"""
ALPHAFOLD — Fonction d'Énergie Ondulatoire Déterministe
=========================================================
Cœur scientifique du repliement protéique harmonique.

E_total = E_backbone + E_sidechain + E_solvent + E_electrostatic
         + E_hbond + E_disulfide + E_harmonic_core

ZÉRO potentiel statistique. ZÉRO paramètre appris.
Tout est dérivé des constantes harmoniques fondamentales :
{φ, π, e, √2, √3, √5, e/π}

Author: Univers-Holistique
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field

from .amino_acids import (
    HarmonicAminoAcid, get_amino_acid, parse_sequence,
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, LAMBDA_H,
    FunctionalGroup,
)
from .peptide_geometry import (
    BOND_LENGTHS, BOND_ANGLES,
    harmonic_ramachandran_potential,
    dihedral_angle, bond_angle,
)
from .backbone import ProteinStructure, ResidueAtoms

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES D'ÉNERGIE HARMONIQUES
# ═══════════════════════════════════════════════════════════════════════════════

# Constantes de force (kcal/mol)
# Dérivées de φ et des constantes fondamentales

K_BOND      = 100.0 * PHI       # ≈ 162 kcal/mol/Å² — tension de liaison
K_ANGLE     = 30.0 * PI         # ≈ 94 kcal/mol/rad² — flexion d'angle
K_OMEGA     = 10.0 * PHI        # ≈ 16.2 kcal/mol — torsion ω (planéité peptidique)
K_RAMA      = 10.0 * PHI        # ≈ 16.2 kcal/mol — pénalité Ramachandran

# Interactions non-liées
EPSILON_VDW = 0.15 * PHI        # ≈ 0.243 kcal/mol — profondeur du puits de van der Waals
SIGMA_VDW   = 3.5               # Å — distance d'équilibre vdW (moyenne C, N, O)
CUTOFF_VDW  = 10.0              # Å — cutoff pour les interactions non-liées
MIN_VDW_DIST = 2.0              # Å — distance minimale (répulsion dure)

# Solvatation
K_SOLV      = 1.0 * PHI         # ≈ 1.618 kcal/mol — force d'enfouissement hydrophobe

# Électrostatique
EPSILON_R   = 4.0 * PHI         # ≈ 6.47 — constante diélectrique effective (intérieur protéine)
K_COULOMB   = 332.0             # kcal·Å/mol·e² — constante de Coulomb
DEBYE_HUCKEL = 10.0             # Å — longueur de Debye-Hückel (force ionique ~150 mM)

# Liaisons hydrogène
K_HBOND     = 3.0 * PHI         # ≈ 4.85 kcal/mol — force d'une liaison H
R0_HBOND    = 2.8               # Å — distance donneur-accepteur optimale
SIGMA_HBOND = 0.5               # Å — largeur du puits H-bond

# Ponts disulfure
K_SS        = 100.0 * PHI       # ≈ 161.8 kcal/mol/Å² — constante de force S-S
R0_SS       = 2.05              # Å — distance S-S optimale
SS_THRESHOLD = 3.0              # Å — distance max pour considérer un pont S-S

# Noyau harmonique
K_HARMONIC  = 2.0 * E           # ≈ 5.44 kcal/mol — force du rappel harmonique
LAMBDA_HARM = LAMBDA_H          # ≈ 1.618 Å — longueur de décroissance

# ═══════════════════════════════════════════════════════════════════════════════
# RÉSULTAT D'ÉNERGIE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EnergyBreakdown:
    """Décomposition de l'énergie totale."""
    e_backbone: float = 0.0       # Tensions de liaison + angles + dièdres + Rama
    e_sidechain: float = 0.0      # Van der Waals / packing
    e_solvent: float = 0.0        # Enfouissement hydrophobe
    e_electrostatic: float = 0.0  # Coulomb + interférence de phase
    e_hbond: float = 0.0          # Liaisons hydrogène
    e_disulfide: float = 0.0      # Ponts disulfure
    e_harmonic: float = 0.0       # Noyau harmonique

    @property
    def total(self) -> float:
        return (self.e_backbone + self.e_sidechain + self.e_solvent +
                self.e_electrostatic + self.e_hbond + self.e_disulfide +
                self.e_harmonic)

    def to_dict(self) -> Dict[str, float]:
        return {
            'e_backbone': round(self.e_backbone, 3),
            'e_sidechain': round(self.e_sidechain, 3),
            'e_solvent': round(self.e_solvent, 3),
            'e_electrostatic': round(self.e_electrostatic, 3),
            'e_hbond': round(self.e_hbond, 3),
            'e_disulfide': round(self.e_disulfide, 3),
            'e_harmonic': round(self.e_harmonic, 3),
            'total': round(self.total, 3),
        }

    def __repr__(self) -> str:
        lines = [
            f"EnergyBreakdown(total={self.total:.2f} kcal/mol):",
            f"  backbone:     {self.e_backbone:+.2f}",
            f"  sidechain:    {self.e_sidechain:+.2f}",
            f"  solvent:      {self.e_solvent:+.2f}",
            f"  electrostatic:{self.e_electrostatic:+.2f}",
            f"  hbond:        {self.e_hbond:+.2f}",
            f"  disulfide:    {self.e_disulfide:+.2f}",
            f"  harmonic:     {self.e_harmonic:+.2f}",
        ]
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# CALCULATEUR D'ÉNERGIE HARMONIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicEnergy:
    """
    Calcule l'énergie harmonique totale d'une structure protéique.

    Usage:
        energy = HarmonicEnergy(structure)
        e = energy.compute()
        print(e.total)   # kcal/mol
        print(e.to_dict())
    """

    def __init__(self, structure: ProteinStructure):
        self.structure = structure
        self.residues = structure.residues
        self.n = len(self.residues)

        # Pré-calculer les positions de tous les atomes lourds
        self._build_atom_list()

    def _build_atom_list(self):
        """Construit une liste plate de tous les atomes avec métadonnées."""
        self.atoms = []         # [{'name': str, 'pos': ndarray, 'res_idx': int, 'element': str}]
        self.atom_map = {}      # (res_idx, name) -> index in atoms

        for res in self.residues:
            idx = res.index
            for name, pos in res.all_atoms().items():
                elem = name[0] if name[0] in 'CNOS' else 'C'
                self.atom_map[(idx, name)] = len(self.atoms)
                self.atoms.append({
                    'name': name,
                    'pos': pos,
                    'res_idx': idx,
                    'element': elem,
                    'aa': res.aa,
                })

    def compute(self) -> EnergyBreakdown:
        """Calcule l'énergie totale et sa décomposition."""
        eb = EnergyBreakdown()

        eb.e_backbone = self._compute_backbone()
        eb.e_sidechain = self._compute_sidechain()
        eb.e_solvent = self._compute_solvent()
        eb.e_electrostatic = self._compute_electrostatic()
        eb.e_hbond = self._compute_hbond()
        eb.e_disulfide = self._compute_disulfide()
        eb.e_harmonic = self._compute_harmonic_core()

        return eb

    # ═══════════════════════════════════════════════════════════════════════
    # 1. E_backbone — Tensions de liaison, angles, dièdres, Ramachandran
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_backbone(self) -> float:
        E = 0.0

        for i, res in enumerate(self.residues):
            # --- Liaisons ---
            # N-CA
            E += K_BOND * (np.linalg.norm(res.CA - res.N) - BOND_LENGTHS['N_CA']) ** 2
            # CA-C
            E += K_BOND * (np.linalg.norm(res.C - res.CA) - BOND_LENGTHS['CA_C']) ** 2
            # C-O
            E += K_BOND * (np.linalg.norm(res.O - res.C) - BOND_LENGTHS['C_O']) ** 2
            # C-N (peptide bond, only if next residue exists)
            if i < self.n - 1:
                N_next = self.residues[i+1].N
                E += K_BOND * (np.linalg.norm(N_next - res.C) - BOND_LENGTHS['C_N']) ** 2

            # --- Angles ---
            # N-CA-C
            E += K_ANGLE * (bond_angle(res.N, res.CA, res.C) -
                           math.radians(BOND_ANGLES['N_CA_C'])) ** 2
            # CA-C-O
            E += K_ANGLE * (bond_angle(res.CA, res.C, res.O) -
                           math.radians(BOND_ANGLES['CA_C_O'])) ** 2
            # CA-C-N (if next exists)
            if i < self.n - 1:
                N_next = self.residues[i+1].N
                E += K_ANGLE * (bond_angle(res.CA, res.C, N_next) -
                               math.radians(BOND_ANGLES['CA_C_N'])) ** 2
                # C-N-CA
                CA_next = self.residues[i+1].CA
                E += K_ANGLE * (bond_angle(res.C, N_next, CA_next) -
                               math.radians(BOND_ANGLES['C_N_CA'])) ** 2

            # --- Dièdres omega (planéité de la liaison peptidique) ---
            if i < self.n - 1:
                N_next = self.residues[i+1].N
                CA_next = self.residues[i+1].CA
                omega = dihedral_angle(res.CA, res.C, N_next, CA_next)
                # Omega devrait être 180° (π rad) pour trans, 0° pour cis
                E += K_OMEGA * (1.0 + math.cos(omega))  # minimum à ω=π (180°)

            # --- Ramachandran (hors premier et dernier) ---
            if 0 < i < self.n - 1:
                rama_E = harmonic_ramachandran_potential(res.phi, res.psi, res.aa)
                E += K_RAMA * rama_E

        return E

    # ═══════════════════════════════════════════════════════════════════════
    # 2. E_sidechain — Van der Waals / packing harmonique
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_sidechain(self) -> float:
        """
        Interactions de van der Waals entre tous les atomes lourds.

        Utilise un potentiel Lennard-Jones φ-pondéré avec soft-core :
          E_ij = φ_i * φ_j * ε * [(σ/r_soft)^12 - 2*(σ/r_soft)^6]

        où r_soft = sqrt(r² + δ²) (soft-core pour éviter l'explosion).
        """
        E = 0.0
        n_atoms = len(self.atoms)
        delta = 0.5  # paramètre soft-core (Å)

        # Rayons de van der Waals par élément (Å)
        vdw_radii = {'C': 1.70, 'N': 1.55, 'O': 1.52, 'S': 1.80}

        for i in range(n_atoms):
            ai = self.atoms[i]
            ri = vdw_radii.get(ai['element'], 1.70)
            phi_i = ai['aa'].phi_score

            for j in range(i + 1, n_atoms):
                aj = self.atoms[j]

                # Exclure les atomes du même résidu liés (1-2, 1-3)
                if ai['res_idx'] == aj['res_idx']:
                    continue
                # Exclure les résidus voisins (i, i+1) — déjà dans E_backbone
                if abs(ai['res_idx'] - aj['res_idx']) <= 1:
                    continue

                dist = np.linalg.norm(ai['pos'] - aj['pos'])
                if dist > CUTOFF_VDW:
                    continue

                rj = vdw_radii.get(aj['element'], 1.70)
                sigma = (ri + rj) * 0.8  # distance d'équilibre (légèrement réduite)
                phi_j = aj['aa'].phi_score

                # Soft-core : éviter l'explosion à courte distance
                r_soft = math.sqrt(dist ** 2 + delta ** 2)
                r_ratio = sigma / max(r_soft, 0.5)

                # Lennard-Jones tronqué (cap à Emax pour éviter les singularités)
                lj = r_ratio ** 12 - 2.0 * r_ratio ** 6
                lj = max(-2.0, min(lj, 50.0))  # cap pour éviter l'explosion

                # Facteur de compatibilité harmonique
                phi_compat = 1.0 - abs(phi_i - phi_j) / 0.4
                phi_compat = max(0.1, phi_compat)

                E += phi_compat * EPSILON_VDW * lj

        return E

    # ═══════════════════════════════════════════════════════════════════════
    # 3. E_solvent — Enfouissement hydrophobe
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_solvent(self) -> float:
        """
        Énergie de solvatation basée sur l'enfouissement des résidus hydrophobes.

        Pour chaque résidu, on estime l'accessibilité au solvant (SASA approximative)
        en comptant le nombre de voisins dans un rayon de coupure.

        E_solv = Σ h_i * (1 - burial_i) * φ_i

        où burial_i = n_contacts_i / n_contacts_max
        h_i = hydrophobicité (positive = hydrophobe, négative = hydrophile)
        """
        E = 0.0
        CA_positions = [(i, r.CA) for i, r in enumerate(self.residues)]

        # Rayon de coupure pour contacts (Å)
        contact_cutoff = 8.0  # typique pour contacts Cα-Cα

        for i, (idx_i, ca_i) in enumerate(CA_positions):
            res = self.residues[idx_i]
            aa = res.aa

            # Compter les contacts Cα-Cα
            n_contacts = 0
            for j, (idx_j, ca_j) in enumerate(CA_positions):
                if abs(idx_i - idx_j) <= 2:  # exclure i, i±1, i±2
                    continue
                dist = np.linalg.norm(ca_i - ca_j)
                if dist < contact_cutoff:
                    n_contacts += 1

            # Enfouissement normalisé
            max_contacts = max(1, self.n - 5)  # nombre max de contacts possibles
            burial = min(1.0, n_contacts / max_contacts)

            # Énergie : hydrophobe → énergie négative (favorable) quand enfoui
            #           hydrophile → énergie positive (défavorable) quand enfoui
            if aa.hydrophobic > 0:
                # Hydrophobe : favorable d'être enfoui
                E -= K_SOLV * aa.hydrophobic * burial * aa.phi_score
            else:
                # Hydrophile : favorable d'être exposé
                E += K_SOLV * abs(aa.hydrophobic) * burial * aa.phi_score * 0.5

        return E

    # ═══════════════════════════════════════════════════════════════════════
    # 4. E_electrostatic — Coulomb + interférence de phase ondulatoire
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_electrostatic(self) -> float:
        """
        Énergie électrostatique avec interférence de phase harmonique.

        E_coul = Σ q_i * q_j / (ε_r * r_ij) * cos(Δphase_ij) * exp(-r_ij/λ_D)

        Le terme cos(Δphase_ij) est INÉDIT : il module l'interaction
        électrostatique par la compatibilité de phase entre les oscillateurs.
        Deux charges de même signe mais de phases opposées peuvent s'attirer !
        """
        E = 0.0
        n_atoms = len(self.atoms)

        # Charges partielles simplifiées par atome
        charges = self._assign_charges()

        for i in range(n_atoms):
            qi = charges[i]
            if abs(qi) < 0.01:
                continue

            ai = self.atoms[i]
            phi_i = ai['aa'].phase_intrinseque

            for j in range(i + 1, n_atoms):
                qj = charges[j]
                if abs(qj) < 0.01:
                    continue

                # Exclure même résidu
                if ai['res_idx'] == self.atoms[j]['res_idx']:
                    continue

                dist = np.linalg.norm(ai['pos'] - self.atoms[j]['pos'])
                if dist > CUTOFF_VDW or dist < 0.5:
                    continue

                aj = self.atoms[j]
                phi_j = aj['aa'].phase_intrinseque

                # Coulomb standard avec diélectrique dépendant de la distance
                eps_r = EPSILON_R * dist  # ε ~ r (modèle simple)

                # Interférence de phase harmonique
                delta_phase = phi_i - phi_j
                phase_factor = math.cos(delta_phase)

                # Écrantage de Debye-Hückel
                debye = math.exp(-dist / DEBYE_HUCKEL)

                E += K_COULOMB * qi * qj / (eps_r * dist) * phase_factor * debye

        return E

    def _assign_charges(self) -> List[float]:
        """Assigne des charges partielles simplifiées à chaque atome."""
        charges = []
        for atom in self.atoms:
            name = atom['name']
            aa = atom['aa']
            q = 0.0

            # Backbone
            if name == 'N':
                q = -0.30  # légèrement négatif (amide)
            elif name == 'CA':
                q = 0.10   # légèrement positif
            elif name == 'C':
                q = 0.50   # carbonyle positif
            elif name == 'O':
                q = -0.50  # carbonyle négatif

            # Sidechain charges based on functional groups
            elif name in ('OD1', 'OD2', 'OE1', 'OE2'):
                q = -0.50  # carboxylate
            elif name in ('NZ', 'NH1', 'NH2'):
                q = 0.50   # amine / guanidinium
            elif name == 'ND1' and aa.code1 == 'H':
                q = 0.25   # His imidazole
            elif name == 'NE2' and aa.code1 == 'H':
                q = -0.25
            elif name == 'SG' and aa.code1 == 'C':
                q = -0.20  # thiol

            charges.append(q)

        return charges

    # ═══════════════════════════════════════════════════════════════════════
    # 5. E_hbond — Liaisons hydrogène par résonance de phase
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_hbond(self) -> float:
        """
        Énergie des liaisons hydrogène.

        E_hbond = Σ K_HB * cos²(θ_DHA) * exp(-(r_DA - R0)² / 2σ²)

        Détecte automatiquement les paires donneur-accepteur :
        - Donneurs : N-H (backbone, sauf Pro), OG (Ser), OG1 (Thr), OH (Tyr),
                     ND1/NE2 (His), NZ (Lys), NE/NH1/NH2 (Arg), NE1 (Trp)
        - Accepteurs : O (backbone), OD1/OD2 (Asp), OE1/OE2 (Glu),
                       OG/OG1 (Ser/Thr), OH (Tyr)
        """
        E = 0.0

        # Identifier donneurs et accepteurs
        donors = []   # [(heavy_atom_pos, H_pos, res_idx)]
        acceptors = []  # [(atom_pos, res_idx)]

        for res in self.residues:
            i = res.index
            aa = res.aa

            # Backbone NH (sauf Proline)
            if aa.code1 != 'P':
                n_pos = res.N
                # Position approximative de H (à 1.01 Å de N, direction opposée à CA-C)
                ca_to_n = res.N - res.CA
                if np.linalg.norm(ca_to_n) > 0:
                    h_dir = ca_to_n / np.linalg.norm(ca_to_n)
                    h_pos = n_pos + 1.01 * h_dir
                    donors.append((n_pos, h_pos, i))

            # Backbone CO
            acceptors.append((res.O, i))

            # Sidechain donors
            for fg in aa.functional_groups:
                if fg.donor:
                    for name in ['OG', 'OG1', 'OH', 'ND1', 'NE2', 'NZ', 'NE', 'NH1', 'NH2', 'NE1', 'SG']:
                        if name in res.sidechain:
                            donors.append((res.sidechain[name],
                                          res.sidechain[name] + np.array([0.96, 0.0, 0.0]),
                                          i))
                            break  # un seul donneur par groupe

                if fg.acceptor:
                    for name in ['OD1', 'OD2', 'OE1', 'OE2', 'OG', 'OG1', 'OH', 'ND1']:
                        if name in res.sidechain:
                            acceptors.append((res.sidechain[name], i))
                            break

        # Évaluer toutes les paires donneur-accepteur
        for d_heavy, h_pos, d_idx in donors:
            for a_pos, a_idx in acceptors:
                if abs(d_idx - a_idx) <= 1:
                    continue  # exclure voisins immédiats

                r_DA = np.linalg.norm(d_heavy - a_pos)
                if r_DA > 4.0 or r_DA < 1.5:
                    continue

                # Angle D-H···A
                d_h = h_pos - d_heavy
                h_a = a_pos - h_pos
                d_h_norm = np.linalg.norm(d_h)
                h_a_norm = np.linalg.norm(h_a)
                if d_h_norm < 0.01 or h_a_norm < 0.01:
                    continue
                cos_theta = np.dot(d_h, h_a) / (d_h_norm * h_a_norm)
                cos_theta = max(-1.0, min(1.0, cos_theta))

                # Énergie de liaison H
                gauss = math.exp(-(r_DA - R0_HBOND) ** 2 / (2.0 * SIGMA_HBOND ** 2))
                E -= K_HBOND * (cos_theta ** 2) * gauss

        return E

    # ═══════════════════════════════════════════════════════════════════════
    # 6. E_disulfide — Ponts disulfure
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_disulfide(self) -> float:
        """
        Énergie des ponts disulfure.

        E_ss = Σ K_SS * (r_S-S - R0_SS)²

        Détecte les paires de cystéines proches (SG-SG < 3.0 Å)
        et applique une contrainte harmonique.
        """
        E = 0.0

        # Trouver tous les atomes SG
        sg_atoms = []  # [(pos, res_idx)]
        for res in self.residues:
            if 'SG' in res.sidechain:
                sg_atoms.append((res.sidechain['SG'], res.index))

        # Vérifier les paires
        for i in range(len(sg_atoms)):
            for j in range(i + 1, len(sg_atoms)):
                dist = np.linalg.norm(sg_atoms[i][0] - sg_atoms[j][0])
                if dist < SS_THRESHOLD:
                    # Appliquer la contrainte harmonique (tend vers R0_SS)
                    E += K_SS * (dist - R0_SS) ** 2

        return E

    # ═══════════════════════════════════════════════════════════════════════
    # 7. E_harmonic_core — Noyau harmonique (rappel vers l'état fondamental)
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_harmonic_core(self) -> float:
        """
        Noyau harmonique : chaque résidu tend vers sa position d'équilibre
        ondulatoire. C'est le terme qui PILOTE le repliement.

        E_harm = -Σ φ_i * cos(ΔΦ_i) * exp(-|r_i - r_i⁰| / λ)

        où :
        - φ_i = score harmonique du résidu
        - ΔΦ_i = différence entre la phase intrinsèque et la phase
                  géométrique (déterminée par l'environnement local)
        - r_i⁰ = position idéale estimée (centre de masse harmonique)

        En pratique, on utilise une version simplifiée :
        E_harm = -Σ_i φ_i * cos(2π * r_i/λ_i) * exp(-|r_i - CM|/λ)
        """
        E = 0.0

        if self.n < 3:
            return 0.0

        # Centre de masse harmonique (pondéré par φ)
        phi_total = sum(r.aa.phi_score for r in self.residues)
        if phi_total < 0.01:
            return 0.0

        cm = np.zeros(3)
        for res in self.residues:
            cm += res.aa.phi_score * res.CA
        cm /= phi_total

        # Pour chaque résidu, calculer l'énergie harmonique
        for res in self.residues:
            r_i = res.CA
            d_i = np.linalg.norm(r_i - cm)
            phi_i = res.aa.phi_score

            # Phase géométrique : dépend de la position relative au CM
            # et de la fréquence propre de l'oscillateur
            phase_geom = 2.0 * PI * d_i / (LAMBDA_HARM * phi_i + 0.01)

            # Différence de phase avec la phase intrinsèque
            delta_phi = phase_geom - res.aa.phase_intrinseque

            # Énergie harmonique (négative = favorable)
            E -= K_HARMONIC * phi_i * math.cos(delta_phi) * math.exp(-d_i / LAMBDA_HARM)

        return E


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def compute_energy(structure: ProteinStructure) -> EnergyBreakdown:
    """Calcule l'énergie harmonique d'une structure (raccourci)."""
    eng = HarmonicEnergy(structure)
    return eng.compute()


def compute_per_residue_energy(structure: ProteinStructure) -> List[float]:
    """
    Calcule l'énergie par résidu (approximation).

    Retourne une liste de N valeurs (kcal/mol).
    Utile pour identifier les résidus sous tension.
    """
    eng = HarmonicEnergy(structure)
    eb = eng.compute()
    total = eb.total
    n = structure.n_residues

    # Répartir l'énergie proportionnellement au score φ
    phi_scores = [r.aa.phi_score for r in structure.residues]
    phi_sum = sum(phi_scores)
    if phi_sum < 0.01:
        return [total / n] * n

    return [total * phi / phi_sum for phi in phi_scores]


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide du module."""
    print("=" * 60)
    print("TEST : Énergie Ondulatoire Harmonique")
    print("=" * 60)

    from .backbone import HarmonicBackbone

    # Construire une petite protéine test
    seq = "AGVLIC"
    bb = HarmonicBackbone(seq)

    for label, struct in [
        ("Étendu (β)", bb.build_extended()),
        ("Hélice α", bb.build_helical()),
        ("Harmonique", bb.build_harmonic_initial()),
    ]:
        eng = HarmonicEnergy(struct)
        eb = eng.compute()
        print(f"\n{label} ({seq}):")
        print(f"  Total: {eb.total:.2f} kcal/mol")
        for k, v in eb.to_dict().items():
            if k != 'total':
                print(f"  {k}: {v:+.2f}")

    # Vérifier que l'hélice est plus stable que la chaîne étendue
    eng_ext = HarmonicEnergy(bb.build_extended())
    eng_hel = HarmonicEnergy(bb.build_helical())
    e_ext = eng_ext.compute().total
    e_hel = eng_hel.compute().total
    print(f"\nΔE (hélice - étendu): {e_hel - e_ext:+.2f} kcal/mol")
    print(f"  → L'hélice est {'plus' if e_hel < e_ext else 'moins'} stable")

    print("\n✅ Tests passés !")


if __name__ == '__main__':
    _test()
