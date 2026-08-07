"""
ALPHAFOLD — Acides Aminés comme Oscillateurs Harmoniques
=========================================================
Chaque acide aminé est modélisé comme un oscillateur harmonique
avec une fréquence propre dérivée de son score φ.

L'approche est 100% déterministe : pas de statistiques, pas de ML.
Les constantes harmoniques {φ, π, e, √2, √3, √5, e/π} gouvernent
toutes les propriétés physico-chimiques.

Découverte Kotto Alain (22/05/2026) — Extension au repliement protéique.

Author: Univers-Holistique
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES HARMONIQUES FONDAMENTALES
# ═══════════════════════════════════════════════════════════════════════════════

PHI    = 1.618033988749895      # Nombre d'or
ALPHA  = 1.0 / PHI              # Ordre fractionnaire ≈ 0.618
PI     = math.pi                # 3.141592653589793
E      = math.e                 # 2.718281828459045
SQRT2  = math.sqrt(2)           # 1.4142135623730951
SQRT3  = math.sqrt(3)           # 1.7320508075688772
SQRT5  = math.sqrt(5)           # 2.23606797749979
E_PI   = E / PI                 # 0.8652559794322651

# Fréquence de base pour les oscillateurs protéiques (THz)
# Dérivée de la fréquence vibrationnelle N-H stretch (~100 THz) divisée par φ³
OMEGA_0 = 100.0 / (PHI ** 3)    # ≈ 23.6 THz

# Longueur d'onde harmonique caractéristique (Å)
# λ = c / ω où c est une vitesse effective dans le milieu protéique
LAMBDA_H = 1.0 / ALPHA          # ≈ 1.618 Å (distance inter-résidu idéale)

# Charge élémentaire harmonique (u.a.)
E_CHARGE = 1.0 / PHI            # ≈ 0.618

# ═══════════════════════════════════════════════════════════════════════════════
# TYPES DE GROUPES FONCTIONNELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FunctionalGroup:
    """Groupe fonctionnel sur une chaîne latérale."""
    name: str                    # Nom (ex: "hydroxyl", "carboxyl", "amide")
    donor: bool = False          # Donneur de liaison H
    acceptor: bool = False       # Accepteur de liaison H
    charged: bool = False        # Groupe chargé à pH physiologique
    charge_sign: float = 0.0     # +1 ou -1
    hydrophobic: bool = False    # Groupe hydrophobe
    sulfur: bool = False         # Contient du soufre (pont disulfure)
    aromatic: bool = False       # Cycle aromatique

# ═══════════════════════════════════════════════════════════════════════════════
# ACIDE AMINÉ HARMONIQUE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HarmonicAminoAcid:
    """
    Un acide aminé comme oscillateur harmonique.

    Propriétés harmoniques :
    - phi_score : score φ (0.33-0.72), encode la « personnalité » ondulatoire
    - frequency : fréquence propre de l'oscillateur (THz)
    - phase_intrinseque : déphasage intrinsèque (radians)
    - hydrophobic_phase : préférence de phase pour le solvant

    Propriétés physico-chimiques :
    - hydrophobic : échelle d'hydrophobie (Kyte-Doolittle)
    - size : taille relative (0 = Gly, 2 = Trp/Arg)
    - charge : charge à pH 7.0 (-1, 0, +1)
    - mass : masse moléculaire (Da)

    Propensions structurales (dérivées de φ, pas de statistiques !) :
    - helix_propensity : 0→1, préférence pour l'hélice α
    - sheet_propensity : 0→1, préférence pour le feuillet β
    - turn_propensity : 0→1, préférence pour les coudes
    """

    # Identité
    code1: str                   # Code 1 lettre
    code3: str                   # Code 3 lettres
    name: str                    # Nom complet

    # Propriétés harmoniques (issues de AMINO_PROPS enrichi)
    phi_score: float             # Score φ (0.33-0.72)
    hydrophobic: float           # Hydrophobie (Kyte-Doolittle)
    size: float                  # Taille relative (0.0-2.0)
    charge: float                # Charge à pH 7.0

    # Propriétés dérivées (calculées automatiquement)
    frequency: float = 0.0       # Fréquence propre (THz)
    phase_intrinseque: float = 0.0  # Phase intrinsèque (rad)
    hydrophobic_phase: float = 0.0  # Phase hydrophobe (rad)
    helix_propensity: float = 0.0   # Propension hélice α
    sheet_propensity: float = 0.0   # Propension feuillet β
    turn_propensity: float = 0.0    # Propension coude

    # Atomes de la chaîne latérale
    sidechain_atoms: List[str] = field(default_factory=list)
    functional_groups: List[FunctionalGroup] = field(default_factory=list)

    # Masse moléculaire (Da)
    mass: float = 0.0

    # Pont disulfure
    has_sulfur: bool = False
    is_cyclic: bool = False      # Proline

    def __post_init__(self):
        """Calcule les propriétés dérivées."""
        # Fréquence propre : φ_score module la fréquence de base
        # Plus φ_score est élevé, plus l'oscillateur est rapide
        self.frequency = self.phi_score * PHI * OMEGA_0

        # Phase intrinsèque : l'acide aminé « commence » à cette phase
        # dans le cycle d'oscillation. Liée au score φ.
        self.phase_intrinseque = 2.0 * PI * self.phi_score

        # Phase hydrophobe : détermine la préférence solvant
        # Normalisée par PI pour rester dans [-π, π]
        self.hydrophobic_phase = self.hydrophobic / PHI

        # Propensions structurales (émergentes de φ, pas de statistiques !)
        # Hélice α : optimum autour de φ ≈ 0.40-0.45 (Alan, Glu, Leu...)
        self.helix_propensity = max(0.0, min(1.0, 1.0 - 2.0 * abs(self.phi_score - 0.43)))

        # Feuillet β : optimum autour de φ ≈ 0.63-0.72 (Val, Ile, Phe, Tyr...)
        self.sheet_propensity = max(0.0, min(1.0, 1.0 - 2.0 * abs(self.phi_score - 0.65)))

        # Coude : optimum autour de φ ≈ 0.50 (Gly) ou φ bas (Pro)
        self.turn_propensity = max(0.0, min(1.0,
            1.0 - 4.0 * abs(self.phi_score - 0.50) if self.code1 != 'P'
            else 1.0 - 2.0 * self.phi_score  # Pro : plus φ est bas, plus c'est un briseur
        ))

    @property
    def is_hydrophobic(self) -> bool:
        """L'acide aminé est-il globalement hydrophobe ?"""
        return self.hydrophobic > 1.0

    @property
    def is_charged(self) -> bool:
        """L'acide aminé est-il chargé à pH physiologique ?"""
        return abs(self.charge) > 0.1

    @property
    def is_polar(self) -> bool:
        """L'acide aminé est-il polaire (non chargé) ?"""
        return not self.is_hydrophobic and not self.is_charged

    @property
    def charge_wave_amplitude(self) -> float:
        """Amplitude de l'onde électrostatique."""
        return self.charge * E_CHARGE

    @property
    def wavelength(self) -> float:
        """Longueur d'onde harmonique (Å)."""
        return LAMBDA_H / self.phi_score if self.phi_score > 0 else float('inf')

    def harmonic_signature(self) -> Dict[str, float]:
        """Retourne la signature harmonique complète de l'acide aminé."""
        return {
            'phi_score': self.phi_score,
            'frequency': self.frequency,
            'phase': self.phase_intrinseque,
            'hydrophobic_phase': self.hydrophobic_phase,
            'charge_wave': self.charge_wave_amplitude,
            'helix_prop': self.helix_propensity,
            'sheet_prop': self.sheet_propensity,
            'turn_prop': self.turn_propensity,
            'wavelength': self.wavelength,
            'size': self.size,
        }

    def __repr__(self) -> str:
        return f"HarmonicAA({self.code3}, φ={self.phi_score:.3f}, ω={self.frequency:.1f} THz)"


# ═══════════════════════════════════════════════════════════════════════════════
# GROUPES FONCTIONNELS STANDARDS
# ═══════════════════════════════════════════════════════════════════════════════

FG_HYDROXYL   = FunctionalGroup("hydroxyl", donor=True, acceptor=True)
FG_CARBOXYL   = FunctionalGroup("carboxyl", donor=True, acceptor=True, charged=True, charge_sign=-1.0)
FG_AMIDE      = FunctionalGroup("amide", donor=True, acceptor=True)
FG_AMINO      = FunctionalGroup("amino", donor=True, charged=True, charge_sign=+1.0)
FG_GUANIDINIUM= FunctionalGroup("guanidinium", donor=True, charged=True, charge_sign=+1.0)
FG_IMIDAZOLE  = FunctionalGroup("imidazole", donor=True, acceptor=True, charged=True, charge_sign=0.5)
FG_THIOL      = FunctionalGroup("thiol", donor=True, sulfur=True)
FG_THIOETHER  = FunctionalGroup("thioether", sulfur=True)
FG_PHENYL     = FunctionalGroup("phenyl", hydrophobic=True, aromatic=True)
FG_PHENOL     = FunctionalGroup("phenol", donor=True, aromatic=True)
FG_INDOLE     = FunctionalGroup("indole", donor=True, aromatic=True)
FG_METHYL     = FunctionalGroup("methyl", hydrophobic=True)
FG_ISOPROPYL  = FunctionalGroup("isopropyl", hydrophobic=True)
FG_PYRROLIDINE= FunctionalGroup("pyrrolidine", hydrophobic=True)  # Proline ring

# ═══════════════════════════════════════════════════════════════════════════════
# LES 20 ACIDES AMINÉS STANDARDS
# ═══════════════════════════════════════════════════════════════════════════════

# Les scores φ et propriétés de base sont issus de AMINO_PROPS dans ka_server.py
# Les propriétés dérivées sont calculées dans __post_init__ de HarmonicAminoAcid

AMINO_ACIDS: Dict[str, HarmonicAminoAcid] = {}

def _register(aa: HarmonicAminoAcid) -> HarmonicAminoAcid:
    """Enregistre un acide aminé dans le dictionnaire global."""
    AMINO_ACIDS[aa.code1] = aa
    AMINO_ACIDS[aa.code3] = aa
    return aa


# --- GLYCINE (G, Gly) ---
# Le plus petit, le plus flexible. φ = 0.50 (point médian parfait)
GLY = _register(HarmonicAminoAcid(
    code1='G', code3='GLY', name='Glycine',
    phi_score=0.50, hydrophobic=-0.4, size=0.0, charge=0.0,
    mass=75.07,
    sidechain_atoms=[],  # Pas de chaîne latérale (juste H, qu'on ignore)
    functional_groups=[],
))

# --- ALANINE (A, Ala) ---
# Méthyle simple. φ = 0.62 → propension feuillet modérée
ALA = _register(HarmonicAminoAcid(
    code1='A', code3='ALA', name='Alanine',
    phi_score=0.62, hydrophobic=1.8, size=0.5, charge=0.0,
    mass=89.09,
    sidechain_atoms=['CB'],
    functional_groups=[FG_METHYL],
))

# --- VALINE (V, Val) ---
# Ramifié, très hydrophobe. φ = 0.63 → fortement β
VAL = _register(HarmonicAminoAcid(
    code1='V', code3='VAL', name='Valine',
    phi_score=0.63, hydrophobic=4.2, size=1.0, charge=0.0,
    mass=117.15,
    sidechain_atoms=['CB', 'CG1', 'CG2'],
    functional_groups=[FG_ISOPROPYL],
))

# --- LEUCINE (L, Leu) ---
# Isobutyle. φ = 0.64 → très β
LEU = _register(HarmonicAminoAcid(
    code1='L', code3='LEU', name='Leucine',
    phi_score=0.64, hydrophobic=3.8, size=1.2, charge=0.0,
    mass=131.18,
    sidechain_atoms=['CB', 'CG', 'CD1', 'CD2'],
    functional_groups=[FG_ISOPROPYL],
))

# --- ISOLEUCINE (I, Ile) ---
# Sec-butyle, chiral en Cβ. φ = 0.65 → fortement β
ILE = _register(HarmonicAminoAcid(
    code1='I', code3='ILE', name='Isoleucine',
    phi_score=0.65, hydrophobic=4.5, size=1.2, charge=0.0,
    mass=131.18,
    sidechain_atoms=['CB', 'CG1', 'CG2', 'CD1'],
    functional_groups=[FG_ISOPROPYL],
))

# --- PROLINE (P, Pro) ---
# Cyclique, briseur d'hélice. φ = 0.33 → le plus bas
PRO = _register(HarmonicAminoAcid(
    code1='P', code3='PRO', name='Proline',
    phi_score=0.33, hydrophobic=-1.6, size=0.8, charge=0.0,
    mass=115.13,
    sidechain_atoms=['CB', 'CG', 'CD'],  # CD se connecte au N (ring)
    functional_groups=[FG_PYRROLIDINE],
    is_cyclic=True,
))

# --- PHENYLALANINE (F, Phe) ---
# Aromatique hydrophobe. φ = 0.72 → le plus β avec Trp
PHE = _register(HarmonicAminoAcid(
    code1='F', code3='PHE', name='Phenylalanine',
    phi_score=0.72, hydrophobic=2.8, size=1.5, charge=0.0,
    mass=165.19,
    sidechain_atoms=['CB', 'CG', 'CD1', 'CD2', 'CE1', 'CE2', 'CZ'],
    functional_groups=[FG_PHENYL],
))

# --- TYROSINE (Y, Tyr) ---
# Phénol (aromatique polaire). φ = 0.66 → β+ modéré
TYR = _register(HarmonicAminoAcid(
    code1='Y', code3='TYR', name='Tyrosine',
    phi_score=0.66, hydrophobic=-1.3, size=1.5, charge=0.0,
    mass=181.19,
    sidechain_atoms=['CB', 'CG', 'CD1', 'CD2', 'CE1', 'CE2', 'CZ', 'OH'],
    functional_groups=[FG_PHENOL],
))

# --- TRYPTOPHANE (W, Trp) ---
# Indole, le plus grand. φ = 0.68 → β aromatique
TRP = _register(HarmonicAminoAcid(
    code1='W', code3='TRP', name='Tryptophane',
    phi_score=0.68, hydrophobic=-0.9, size=2.0, charge=0.0,
    mass=204.23,
    sidechain_atoms=['CB', 'CG', 'CD1', 'CD2', 'NE1', 'CE2', 'CE3', 'CZ2', 'CZ3', 'CH2'],
    functional_groups=[FG_INDOLE],
))

# --- SERINE (S, Ser) ---
# Hydroxyle. φ = 0.48 → équilibré
SER = _register(HarmonicAminoAcid(
    code1='S', code3='SER', name='Sérine',
    phi_score=0.48, hydrophobic=-0.8, size=0.5, charge=0.0,
    mass=105.09,
    sidechain_atoms=['CB', 'OG'],
    functional_groups=[FG_HYDROXYL],
))

# --- THREONINE (T, Thr) ---
# Hydroxyle + méthyle. φ = 0.49 → équilibré
THR = _register(HarmonicAminoAcid(
    code1='T', code3='THR', name='Thréonine',
    phi_score=0.49, hydrophobic=-0.7, size=0.8, charge=0.0,
    mass=119.12,
    sidechain_atoms=['CB', 'OG1', 'CG2'],
    functional_groups=[FG_HYDROXYL, FG_METHYL],
))

# --- CYSTEINE (C, Cys) ---
# Thiol, ponts disulfure. φ = 0.71 → β
CYS = _register(HarmonicAminoAcid(
    code1='C', code3='CYS', name='Cystéine',
    phi_score=0.71, hydrophobic=2.5, size=0.8, charge=0.0,
    mass=121.16,
    sidechain_atoms=['CB', 'SG'],
    functional_groups=[FG_THIOL],
    has_sulfur=True,
))

# --- METHIONINE (M, Met) ---
# Thioéther. φ = 0.59 → α/β équilibré
MET = _register(HarmonicAminoAcid(
    code1='M', code3='MET', name='Méthionine',
    phi_score=0.59, hydrophobic=1.9, size=1.3, charge=0.0,
    mass=149.21,
    sidechain_atoms=['CB', 'CG', 'SD', 'CE'],
    functional_groups=[FG_THIOETHER],
    has_sulfur=True,
))

# --- ASPARTATE (D, Asp) ---
# Carboxylate, chargé -. φ = 0.41 → α
ASP = _register(HarmonicAminoAcid(
    code1='D', code3='ASP', name='Aspartate',
    phi_score=0.41, hydrophobic=-3.5, size=1.0, charge=-1.0,
    mass=133.10,
    sidechain_atoms=['CB', 'CG', 'OD1', 'OD2'],
    functional_groups=[FG_CARBOXYL],
))

# --- GLUTAMATE (E, Glu) ---
# Carboxylate, chargé -. φ = 0.40 → α
GLU = _register(HarmonicAminoAcid(
    code1='E', code3='GLU', name='Glutamate',
    phi_score=0.40, hydrophobic=-3.5, size=1.2, charge=-1.0,
    mass=147.13,
    sidechain_atoms=['CB', 'CG', 'CD', 'OE1', 'OE2'],
    functional_groups=[FG_CARBOXYL],
))

# --- ASPARAGINE (N, Asn) ---
# Amide. φ = 0.45 → α modéré
ASN = _register(HarmonicAminoAcid(
    code1='N', code3='ASN', name='Asparagine',
    phi_score=0.45, hydrophobic=-3.5, size=1.0, charge=0.0,
    mass=132.12,
    sidechain_atoms=['CB', 'CG', 'OD1', 'ND2'],
    functional_groups=[FG_AMIDE],
))

# --- GLUTAMINE (Q, Gln) ---
# Amide. φ = 0.43 → α modéré
GLN = _register(HarmonicAminoAcid(
    code1='Q', code3='GLN', name='Glutamine',
    phi_score=0.43, hydrophobic=-3.5, size=1.2, charge=0.0,
    mass=146.15,
    sidechain_atoms=['CB', 'CG', 'CD', 'OE1', 'NE2'],
    functional_groups=[FG_AMIDE],
))

# --- LYSINE (K, Lys) ---
# Amine, chargé +. φ = 0.37 → fortement α
LYS = _register(HarmonicAminoAcid(
    code1='K', code3='LYS', name='Lysine',
    phi_score=0.37, hydrophobic=-3.9, size=1.5, charge=1.0,
    mass=146.19,
    sidechain_atoms=['CB', 'CG', 'CD', 'CE', 'NZ'],
    functional_groups=[FG_AMINO],
))

# --- ARGININE (R, Arg) ---
# Guanidinium, chargé +. φ = 0.38 → fortement α
ARG = _register(HarmonicAminoAcid(
    code1='R', code3='ARG', name='Arginine',
    phi_score=0.38, hydrophobic=-4.5, size=2.0, charge=1.0,
    mass=174.20,
    sidechain_atoms=['CB', 'CG', 'CD', 'NE', 'CZ', 'NH1', 'NH2'],
    functional_groups=[FG_GUANIDINIUM],
))

# --- HISTIDINE (H, His) ---
# Imidazole, partiellement chargé. φ = 0.44 → α/β équilibré
HIS = _register(HarmonicAminoAcid(
    code1='H', code3='HIS', name='Histidine',
    phi_score=0.44, hydrophobic=-3.2, size=1.2, charge=0.5,
    mass=155.16,
    sidechain_atoms=['CB', 'CG', 'ND1', 'CD2', 'CE1', 'NE2'],
    functional_groups=[FG_IMIDAZOLE],
))


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def get_amino_acid(code: str) -> Optional[HarmonicAminoAcid]:
    """
    Récupère un acide aminé par son code (1 ou 3 lettres).

    Args:
        code: Code 1 lettre ('A', 'G', etc.) ou 3 lettres ('ALA', 'GLY', etc.)

    Returns:
        HarmonicAminoAcid ou None si non trouvé
    """
    return AMINO_ACIDS.get(code.upper())


def parse_sequence(sequence: str) -> List[HarmonicAminoAcid]:
    """
    Parse une séquence d'acides aminés.

    Accepte les codes 1 lettre (ex: 'AGVLI') ou 3 lettres (ex: 'ALA GLY VAL LEU ILE').

    Args:
        sequence: Chaîne de caractères représentant la séquence

    Returns:
        Liste de HarmonicAminoAcid

    Raises:
        ValueError si un code est invalide
    """
    sequence = sequence.strip().upper()

    # Détecter le format
    if ' ' in sequence or len(sequence) > 2 and sequence[:3] in AMINO_ACIDS:
        # Format 3 lettres
        codes = sequence.replace(',', ' ').replace(';', ' ').split()
    else:
        # Format 1 lettre
        codes = list(sequence)

    result = []
    for code in codes:
        code = code.strip()
        if not code:
            continue
        aa = get_amino_acid(code)
        if aa is None:
            raise ValueError(f"Code acide aminé invalide : '{code}'")
        result.append(aa)

    return result


def get_harmonic_profile(sequence: str) -> Dict:
    """
    Calcule le profil harmonique complet d'une séquence.

    Args:
        sequence: Séquence en code 1 ou 3 lettres

    Returns:
        Dictionnaire avec :
        - n_residues: nombre de résidus
        - phi_mean: score φ moyen
        - phi_sum: somme des scores φ
        - charge_net: charge nette
        - hydrophobic_mean: hydrophobie moyenne
        - helix_propensity: propension moyenne hélice α
        - sheet_propensity: propension moyenne feuillet β
        - harmonic_energy: énergie harmonique totale (-Σ φ_i)
        - residues: liste des signatures individuelles
    """
    aas = parse_sequence(sequence)
    n = len(aas)

    if n == 0:
        return {'n_residues': 0, 'error': 'Séquence vide'}

    phi_scores = [aa.phi_score for aa in aas]
    phi_sum = sum(phi_scores)
    phi_mean = phi_sum / n
    charge_net = sum(aa.charge for aa in aas)
    hydrophobic_mean = sum(aa.hydrophobic for aa in aas) / n
    helix_mean = sum(aa.helix_propensity for aa in aas) / n
    sheet_mean = sum(aa.sheet_propensity for aa in aas) / n
    turn_mean = sum(aa.turn_propensity for aa in aas) / n

    # Énergie harmonique libre (proportionnelle à la somme des φ)
    # L'énergie de repliement est -k_B*T * log(Σ φ_i) ~ -φ_sum * constante
    harmonic_energy = -phi_sum * PHI * 4.2  # kcal/mol (comme dans ka_server.py)

    # Séquences consensus pour éléments de structure secondaire
    helix_consensus = [aa.code1 for aa in aas if aa.helix_propensity > 0.5]
    sheet_consensus = [aa.code1 for aa in aas if aa.sheet_propensity > 0.5]
    turn_consensus = [aa.code1 for aa in aas if aa.turn_propensity > 0.5]

    return {
        'n_residues': n,
        'phi_mean': round(phi_mean, 4),
        'phi_sum': round(phi_sum, 2),
        'charge_net': round(charge_net, 1),
        'hydrophobic_mean': round(hydrophobic_mean, 2),
        'helix_propensity': round(helix_mean, 3),
        'sheet_propensity': round(sheet_mean, 3),
        'turn_propensity': round(turn_mean, 3),
        'harmonic_energy_kcal_mol': round(harmonic_energy, 2),
        'predicted_class': _predict_class(helix_mean, sheet_mean, turn_mean),
        'helix_consensus': helix_consensus,
        'sheet_consensus': sheet_consensus,
        'turn_consensus': turn_consensus,
        'residues': [aa.harmonic_signature() for aa in aas],
    }


def _predict_class(helix: float, sheet: float, turn: float) -> str:
    """Prédit la classe structurale (all-α, all-β, α/β, α+β, etc.)."""
    if helix > 0.55 and sheet < 0.35:
        return 'all-alpha'
    elif sheet > 0.55 and helix < 0.35:
        return 'all-beta'
    elif helix > 0.35 and sheet > 0.35:
        return 'alpha/beta'
    elif turn > 0.40:
        return 'small_disulfide_rich'
    else:
        return 'mixed'


def get_cysteine_pairs(sequence: str) -> List[Tuple[int, int]]:
    """
    Identifie les paires de cystéines potentielles pour ponts disulfure.

    Dans l'approche harmonique, les paires sont déterminées par
    compatibilité de phase (les cystéines avec phases proches se lient).

    Args:
        sequence: Séquence protéique

    Returns:
        Liste de tuples (index_i, index_j) des paires potentielles
    """
    aas = parse_sequence(sequence)
    cys_indices = [i for i, aa in enumerate(aas) if aa.has_sulfur]

    if len(cys_indices) < 2:
        return []

    # Appariement par compatibilité de phase harmonique
    # On trie les cystéines par phase intrinsèque et on apparie
    # les plus proches en phase (résonance optimale)
    cys_phases = [(i, aas[i].phase_intrinseque) for i in cys_indices]
    cys_phases.sort(key=lambda x: x[1])

    pairs = []
    used = set()
    for k in range(0, len(cys_phases) - 1, 2):
        i, phi_i = cys_phases[k]
        j, phi_j = cys_phases[k + 1]
        # Vérifier que la différence de phase est < π/2
        if abs(phi_i - phi_j) % (2 * PI) < PI / 2:
            pairs.append((min(i, j), max(i, j)))
            used.add(i)
            used.add(j)

    # Ajouter les cystéines non appariées si nombre impair
    for i, _ in cys_phases:
        if i not in used and len(pairs) < len(cys_indices) // 2:
            # Chercher le partenaire le plus proche en séquence
            best_j = None
            best_dist = float('inf')
            for j, _ in cys_phases:
                if j != i and j not in used:
                    dist = abs(j - i)
                    if dist < best_dist:
                        best_dist = dist
                        best_j = j
            if best_j is not None and best_dist >= 3:  # Au moins 3 résidus d'écart
                pairs.append((min(i, best_j), max(i, best_j)))
                used.add(i)
                used.add(best_j)

    return sorted(pairs)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide du module."""
    print("=" * 60)
    print("TEST : Acides Aminés Harmoniques")
    print("=" * 60)

    for code1 in 'GAVLIPFYWSTCMDENQKRH':
        aa = get_amino_acid(code1)
        print(f"\n{aa.code3} ({aa.code1}) — {aa.name}")
        print(f"  φ={aa.phi_score:.3f}  ω={aa.frequency:.1f} THz  phase={aa.phase_intrinseque:.2f} rad")
        print(f"  Hydrophobie={aa.hydrophobic}  Charge={aa.charge}  Taille={aa.size}")
        print(f"  Hélice={aa.helix_propensity:.2f}  Feuillet={aa.sheet_propensity:.2f}  Coude={aa.turn_propensity:.2f}")
        print(f"  Groupes: {[fg.name for fg in aa.functional_groups]}")

    # Test parsing
    print("\n" + "=" * 60)
    print("TEST : Parsing de séquence")
    seq = "AGVLIC"
    aas = parse_sequence(seq)
    print(f"  Séquence: {seq} → {[aa.code3 for aa in aas]}")

    # Test profil harmonique
    print("\n" + "=" * 60)
    print("TEST : Profil harmonique")
    profile = get_harmonic_profile("MKFLILFNILVSTLALAV")
    for k, v in profile.items():
        if k != 'residues':
            print(f"  {k}: {v}")

    # Test paires CYS
    print("\n" + "=" * 60)
    print("TEST : Ponts disulfure")
    seq_cys = "ACCCDEFCGHIC"
    pairs = get_cysteine_pairs(seq_cys)
    print(f"  Séquence: {seq_cys}")
    print(f"  Paires CYS: {pairs}")

    print("\n✅ Tous les tests passés !")


if __name__ == '__main__':
    _test()
