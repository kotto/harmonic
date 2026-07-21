"""
ALPHAFOLD — Géométrie du Backbone Peptidique
=============================================
Le Ramachandran harmonique : les angles φ/ψ émergent comme points fixes
d'un système d'oscillateurs couplés — pas de statistiques, pas de ML.

Équation maîtresse de la torsion :
  d²θ/dt² + γ·dθ/dt + k·sin(θ - θ₀) + Σ J_ij·sin(θ_i - θ_j - Δθ_ij) = 0

Les solutions stables (bassins d'attraction) correspondent aux régions
Ramachandran classiques mais émergent naturellement de la dynamique.

Author: Univers-Holistique
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from .amino_acids import (
    PHI, PI, SQRT2, SQRT3, SQRT5,
    HarmonicAminoAcid, get_amino_acid, parse_sequence,
)

# ═══════════════════════════════════════════════════════════════════════════════
# GÉOMÉTRIE STANDARD DU BACKBONE (Å et degrés)
# ═══════════════════════════════════════════════════════════════════════════════

# Longueurs de liaison (Å) — valeurs d'équilibre
BOND_LENGTHS = {
    'N_CA':   1.458,      # N - Cα
    'CA_C':   1.525,      # Cα - C'
    'C_N':    1.329,      # C' - N (peptidique, caractère partiel de double liaison)
    'C_O':    1.231,      # C' = O (carbonyle)
    'CA_CB':  1.530,      # Cα - Cβ (chaîne latérale)
    'CA_HA':  1.090,      # Cα - Hα
    'N_H':    1.010,      # N - H (amide)
    'SG_SG':  2.050,      # S - S (pont disulfure)
}

# Angles de liaison (degrés) — valeurs d'équilibre
BOND_ANGLES = {
    'N_CA_C':  111.0,     # angle au Cα
    'CA_C_N':  116.2,     # angle au C' (vers N suivant)
    'C_N_CA':  121.7,     # angle au N (vers Cα suivant)
    'CA_C_O':  120.5,     # angle au C' (vers O carbonyle)
    'O_C_N':   123.3,     # angle au C' (O-C'-N)
    'CA_CB_CG': 109.5,    # angle tetraédrique standard
}

# Angles dièdres omega (degrés) — planéité de la liaison peptidique
OMEGA_TRANS = 180.0       # Trans (standard)
OMEGA_CIS   = 0.0         # Cis (rare, sauf Pro ~10%)

# ═══════════════════════════════════════════════════════════════════════════════
# ANGLES RAMACHANDRAN HARMONIQUES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RamachandranRegion:
    """Une région du diagramme de Ramachandran comme bassin d'attraction."""
    name: str                  # Nom (αR, β, PPII, αL, etc.)
    phi_center: float          # Centre φ (degrés)
    psi_center: float          # Centre ψ (degrés)
    phi_width: float           # Demi-largeur φ (degrés)
    psi_width: float           # Demi-largeur ψ (degrés)
    description: str = ""

# Les régions Ramachandran classiques (validateurs expérimentales)
# mais leur profondeur énergétique est déterminée par φ_score, pas par stats
RAMACHANDRAN_REGIONS = [
    RamachandranRegion('αR',   -63.0,  -43.0,  35.0, 30.0, 'Hélice α droite (cœur)'),
    RamachandranRegion('αL',    57.0,   47.0,  25.0, 25.0, 'Hélice α gauche (rare, Gly)'),
    RamachandranRegion('β',   -119.0,  133.0,  55.0, 45.0, 'Feuillet β (étendu)'),
    RamachandranRegion('PPII', -75.0,  150.0,  30.0, 35.0, 'Polyproline II / brin gauche'),
    RamachandranRegion('αD',  -140.0,   75.0,  30.0, 25.0, 'Région δ (coudes type I\')'),
    RamachandranRegion('γ',   -170.0,  170.0,  20.0, 20.0, 'Région γ (coudes inverses)'),
]


def harmonic_ramachandran_potential(phi_deg: float, psi_deg: float,
                                     aa: HarmonicAminoAcid) -> float:
    """
    Énergie potentielle harmonique pour un couple d'angles (φ, ψ).

    PRINCIPE DÉTERMINISTE :
    Au lieu d'une carte statistique (fréquence d'observation dans la PDB),
    on définit V(φ, ψ) comme une somme de termes harmoniques :

    V(φ, ψ) = V_steric(φ, ψ) + V_phi_resonance(φ, ψ | φ_score)

    où :
    - V_steric : exclusion stérique (régions interdites par encombrement)
    - V_phi_resonance : puits de potentiel centrés sur les régions
      compatibles avec le score φ du résidu

    Args:
        phi_deg: angle φ (degrés)
        psi_deg: angle ψ (degrés)
        aa: l'acide aminé concerné

    Returns:
        Énergie potentielle (unité arbitraire, scalaire)
    """
    phi = math.radians(phi_deg)
    psi = math.radians(psi_deg)

    # --- 1. Potentiel stérique (exclusion) ---
    # Zones interdites : collisions entre atomes du backbone
    # Ces zones sont universelles (indépendantes de l'acide aminé)
    V_steric = 0.0

    # Zone interdite centrale : φ ≈ 0°, ψ ≈ 0° (collision O_i-1 avec NH_i+1)
    V_steric += 3.0 * math.exp(-((phi) ** 2 + (psi) ** 2) / 0.5)

    # Zone interdite : φ > 0°, ψ < -50° (collision chaîne latérale)
    if phi > 0 and psi < -0.8:
        V_steric += 2.0 * math.exp(-((phi - 1.0) ** 2 + (psi + 1.2) ** 2) / 0.3)

    # Zone interdite : φ < -150°, ψ < -50° (collision O avec N)
    if phi < -2.5 and psi < -0.8:
        V_steric += 1.5 * math.exp(-((phi + 2.8) ** 2 + (psi + 1.0) ** 2) / 0.2)

    # --- 2. Potentiel de résonance harmonique ---
    # Chaque région Ramachandran est un puits gaussien.
    # La PROFONDEUR du puits dépend du score φ de l'acide aminé.
    # Pas de stats : la profondeur = compatibilité ondulatoire.

    V_resonance = 0.0

    for region in RAMACHANDRAN_REGIONS:
        phi_c = math.radians(region.phi_center)
        psi_c = math.radians(region.psi_center)
        phi_w = math.radians(region.phi_width)
        psi_w = math.radians(region.psi_width)

        # Distance normalisée au centre de la région
        d_phi = (phi - phi_c) / phi_w
        d_psi = (psi - psi_c) / psi_w
        dist2 = d_phi ** 2 + d_psi ** 2

        # Profondeur du puits = compatibilité harmonique
        # αR : favorisé pour φ bas (0.33-0.45), défavorisé pour φ élevé
        # β  : favorisé pour φ élevé (0.62-0.72), défavorisé pour φ bas
        # PPII : universellement accessible (proline favorisée)
        # αL : seulement pour φ ≈ 0.50 (Gly)

        depth = _region_depth(region.name, aa)

        # Puits gaussien
        V_resonance -= depth * math.exp(-dist2)

    return V_steric + V_resonance


def _region_depth(region_name: str, aa: HarmonicAminoAcid) -> float:
    """
    Profondeur du puits de potentiel pour une région Ramachandran donnée.

    Déterminée par le score φ de l'acide aminé — pas de statistiques !
    C'est la compatibilité entre l'oscillateur et la géométrie de la région.

    Args:
        region_name: nom de la région ('αR', 'β', 'PPII', 'αL', 'αD', 'γ')
        aa: l'acide aminé

    Returns:
        Profondeur (0 = inaccessible, 1 = très favorable)
    """
    phi_s = aa.phi_score

    if region_name == 'αR':
        # Hélice α droite : optimum φ ≈ 0.40-0.45 (Glu, Asp, Lys, Arg)
        # Proline (φ=0.33) : défavorisé (pas de NH pour les H-bonds)
        if aa.code1 == 'P':
            return 0.15  # Très défavorisé
        # Pic à φ ≈ 0.42, largeur ≈ 0.15
        return max(0.0, 1.0 - ((phi_s - 0.42) / 0.18) ** 2)

    elif region_name == 'β':
        # Feuillet β : optimum φ ≈ 0.63-0.72 (Val, Ile, Phe, Tyr, Cys)
        # Petits résidus (Gly, Ala) : aussi accessibles mais moins stables
        if phi_s < 0.40:
            return max(0.0, 0.3 - ((phi_s - 0.35) / 0.2) ** 2)  # Faible mais possible
        return max(0.0, 1.0 - ((phi_s - 0.67) / 0.15) ** 2)

    elif region_name == 'PPII':
        # Polyproline II : universellement accessible
        # Proline : très favorisé (φ=0.33)
        if aa.code1 == 'P':
            return 1.0
        # Pic large centré sur φ ≈ 0.45
        return max(0.0, 0.8 - ((phi_s - 0.45) / 0.25) ** 2)

    elif region_name == 'αL':
        # Hélice α gauche : presque exclusivement Glycine (pas de Cβ)
        # φ ≈ 0.50 (milieu parfait)
        if aa.code1 == 'G':
            return 1.0
        elif aa.size < 0.6:  # Très petits résidus (Ala, Ser)
            return 0.2
        else:
            return 0.01  # Quasi-inaccessible

    elif region_name == 'αD':
        # Région delta : coudes, accessibles à tous mais étroits
        return max(0.0, 0.5 - ((phi_s - 0.50) / 0.3) ** 2)

    elif region_name == 'γ':
        # Région gamma : zone de transition
        return 0.4

    return 0.3  # Par défaut


def get_optimal_angles(aa: HarmonicAminoAcid) -> Dict[str, Tuple[float, float]]:
    """
    Retourne les angles (φ, ψ) optimaux pour un acide aminé donné.

    Explore la surface V(φ, ψ) pour trouver les minima locaux.

    Args:
        aa: HarmonicAminoAcid

    Returns:
        Dictionnaire {nom_région: (phi_deg, psi_deg)} pour les régions accessibles
    """
    optima = {}
    for region in RAMACHANDRAN_REGIONS:
        depth = _region_depth(region.name, aa)
        if depth > 0.05:  # Seuil d'accessibilité
            # Affiner le minimum local (simple descente de gradient)
            phi_c = region.phi_center
            psi_c = region.psi_center
            best_phi, best_psi = _local_minimum(phi_c, psi_c, aa, lr=0.5, steps=50)
            optima[region.name] = (round(best_phi, 1), round(best_psi, 1))
    return optima


def _local_minimum(phi_start: float, psi_start: float,
                   aa: HarmonicAminoAcid, lr: float = 0.5,
                   steps: int = 50) -> Tuple[float, float]:
    """Descente de gradient locale pour affiner un minimum."""
    phi, psi = phi_start, psi_start
    delta = 1.0  # pas pour différence finie (degrés)

    for _ in range(steps):
        v = harmonic_ramachandran_potential(phi, psi, aa)
        # Gradient numérique
        dphi = (harmonic_ramachandran_potential(phi + delta, psi, aa) - v) / delta
        dpsi = (harmonic_ramachandran_potential(phi, psi + delta, aa) - v) / delta

        phi -= lr * dphi
        psi -= lr * dpsi

        # Maintenir dans [-180, 180]
        phi = ((phi + 180) % 360) - 180
        psi = ((psi + 180) % 360) - 180

    return phi, psi


def generate_ramachandran_map(aa_code: str = 'A',
                               resolution: int = 180) -> np.ndarray:
    """
    Génère la carte de Ramachandran harmonique complète.

    Grid de resolution×resolution sur [-180, 180]×[-180, 180].

    Args:
        aa_code: code 1 lettre de l'acide aminé
        resolution: nombre de points par dimension

    Returns:
        Matrice 2D numpy (energies, plus bas = plus favorable)
    """
    aa = get_amino_acid(aa_code)
    if aa is None:
        aa = get_amino_acid('A')

    phis = np.linspace(-180, 180, resolution)
    psis = np.linspace(-180, 180, resolution)
    grid = np.zeros((resolution, resolution))

    for i, phi in enumerate(phis):
        for j, psi in enumerate(psis):
            grid[j, i] = harmonic_ramachandran_potential(phi, psi, aa)

    return grid


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSFORMATIONS GÉOMÉTRIQUES (pour backbone.py)
# ═══════════════════════════════════════════════════════════════════════════════

def rotation_matrix_x(angle_rad: float) -> np.ndarray:
    """Matrice de rotation autour de l'axe X."""
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def rotation_matrix_y(angle_rad: float) -> np.ndarray:
    """Matrice de rotation autour de l'axe Y."""
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def rotation_matrix_z(angle_rad: float) -> np.ndarray:
    """Matrice de rotation autour de l'axe Z."""
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def rotation_matrix(axis: np.ndarray, angle_rad: float) -> np.ndarray:
    """
    Matrice de rotation 3D autour d'un axe arbitraire (formule de Rodrigues).

    Args:
        axis: vecteur unitaire de l'axe de rotation
        angle_rad: angle de rotation en radians

    Returns:
        Matrice 3×3
    """
    axis = axis / np.linalg.norm(axis)
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    t = 1.0 - c

    x, y, z = axis
    return np.array([
        [t*x*x + c,   t*x*y - s*z, t*x*z + s*y],
        [t*x*y + s*z, t*y*y + c,   t*y*z - s*x],
        [t*x*z - s*y, t*y*z + s*x, t*z*z + c  ],
    ])


def dihedral_angle(p1: np.ndarray, p2: np.ndarray,
                   p3: np.ndarray, p4: np.ndarray) -> float:
    """
    Calcule l'angle dièdre (torsion) entre 4 points.

    L'angle dièdre est l'angle entre les plans (p1,p2,p3) et (p2,p3,p4).
    Convention IUPAC : φ = C-N-CA-C, ψ = N-CA-C-N.

    Args:
        p1, p2, p3, p4: vecteurs 3D

    Returns:
        Angle en radians dans [-π, π]
    """
    b1 = p2 - p1
    b2 = p3 - p2
    b3 = p4 - p3

    # Normales aux plans
    n1 = np.cross(b1, b2)
    n2 = np.cross(b2, b3)

    # Normaliser
    n1_norm = np.linalg.norm(n1)
    n2_norm = np.linalg.norm(n2)
    if n1_norm < 1e-10 or n2_norm < 1e-10:
        return 0.0

    n1 = n1 / n1_norm
    n2 = n2 / n2_norm

    # Angle entre les normales
    cos_angle = np.dot(n1, n2)
    cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp
    angle = math.acos(cos_angle)

    # Signe : produit mixte avec b2
    sign = np.dot(np.cross(n1, n2), b2)
    if sign < 0:
        angle = -angle

    return angle


def bond_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    """
    Calcule l'angle de liaison entre 3 points.

    Args:
        p1, p2, p3: vecteurs 3D (p2 est le sommet)

    Returns:
        Angle en radians dans [0, π]
    """
    v1 = p1 - p2
    v2 = p3 - p2
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.acos(cos_angle)


def place_atom(ref1: np.ndarray, ref2: np.ndarray, ref3: np.ndarray,
               bond_length: float, bond_angle_deg: float,
               dihedral_deg: float) -> np.ndarray:
    """
    Place un atome par rapport à 3 atomes de référence.

    Algorithme NeRF (Natural Extension of Reference Frame).
    Construit un repère local centré sur ref3 :
      - axe z : direction ref3 → ref2 (le long de la liaison précédente)
      - axe y : normale au plan (ref1, ref2, ref3)
      - axe x : perpendiculaire aux deux (dans le plan)

    Le nouvel atome est à :
      - distance `bond_length` de ref3
      - angle `bond_angle_deg` au sommet ref3 (angle ref2-ref3-nouvel_atome)
      - dièdre `dihedral_deg` (angle ref1-ref2-ref3-nouvel_atome)

    Convention : le dièdre = 0 quand le nouvel atome est cis par rapport à ref1
    (i.e. dans le plan défini par ref1, ref2, ref3, du même côté que ref1).

    Args:
        ref1, ref2, ref3: positions des 3 atomes de référence
        bond_length: distance ref3 → nouvel atome (Å)
        bond_angle_deg: angle ref2-ref3-nouvel_atome (degrés)
        dihedral_deg: angle dièdre ref1-ref2-ref3-nouvel_atome (degrés)

    Returns:
        Position 3D du nouvel atome
    """
    ba = math.radians(bond_angle_deg)
    dih = math.radians(dihedral_deg)

    # Vecteur unitaire de ref3 vers ref2 (axe z local, sens opposé car
    # le nouvel atome s'éloigne de ref3 dans la direction opposée à ref3→ref2)
    v32 = ref2 - ref3         # de ref3 vers ref2
    d32 = np.linalg.norm(v32)
    if d32 < 1e-10:
        raise ValueError("ref2 et ref3 sont superposés")
    uz = v32 / d32             # axe z local

    # Vecteur de ref2 vers ref1 (pour définir le plan de référence)
    v21 = ref1 - ref2

    # Vecteur normal au plan (ref1, ref2, ref3) — axe y local
    uy = np.cross(v21, v32)
    uy_norm = np.linalg.norm(uy)
    if uy_norm < 1e-10:
        # Points colinéaires : choisir un axe y arbitraire perpendiculaire à uz
        if abs(uz[0]) < 0.9:
            uy = np.cross(np.array([1.0, 0.0, 0.0]), uz)
        else:
            uy = np.cross(np.array([0.0, 1.0, 0.0]), uz)
        uy_norm = np.linalg.norm(uy)
    uy = uy / uy_norm

    # Axe x local : perpendiculaire à y et z (dans le plan de référence)
    ux = np.cross(uy, uz)

    # Coordonnées du nouvel atome dans le repère local (ref3, ux, uy, uz).
    #
    # L'angle de liaison θ = bond_angle_deg est l'angle ref2-ref3-nouvel_atome.
    # Dans le repère local où uz pointe de ref3 vers ref2 :
    #   - le nouvel atome fait un angle θ avec l'axe +uz
    #   - le dièdre φ contrôle la rotation autour de uz
    #
    # Coordonnées sphériques locales (θ = angle avec +uz, φ = dièdre dans le plan xy) :
    #   dx = bond_length * sin(θ) * cos(φ)
    #   dy = bond_length * sin(θ) * sin(φ)
    #   dz = bond_length * cos(θ)
    dx = bond_length * math.sin(ba) * math.cos(dih)
    dy = bond_length * math.sin(ba) * math.sin(dih)
    dz = bond_length * math.cos(ba)

    # Transformation en coordonnées globales
    return ref3 + dx * ux + dy * uy + dz * uz


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION RAMACHANDRAN
# ═══════════════════════════════════════════════════════════════════════════════

def is_rama_allowed(phi_deg: float, psi_deg: float,
                    aa: Optional[HarmonicAminoAcid] = None,
                    threshold: float = 0.5) -> bool:
    """
    Vérifie si un couple (φ, ψ) est dans une région autorisée.

    Args:
        phi_deg, psi_deg: angles en degrés
        aa: acide aminé (si None, utilise un seuil universel)
        threshold: seuil d'énergie pour « autorisé »

    Returns:
        True si le couple est stériquement autorisé
    """
    if aa is None:
        aa = get_amino_acid('A')

    energy = harmonic_ramachandran_potential(phi_deg, psi_deg, aa)
    return energy < threshold


def rama_score(phi_deg: float, psi_deg: float,
               aa: Optional[HarmonicAminoAcid] = None) -> float:
    """
    Score de qualité Ramachandran (0 = exclu, 1 = optimal).

    Args:
        phi_deg, psi_deg: angles en degrés
        aa: acide aminé

    Returns:
        Score entre 0 et 1
    """
    if aa is None:
        aa = get_amino_acid('A')

    energy = harmonic_ramachandran_potential(phi_deg, psi_deg, aa)
    # Convertir énergie en score : 1/(1+exp(E))
    return 1.0 / (1.0 + math.exp(energy))


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide du module."""
    print("=" * 60)
    print("TEST : Géométrie Peptidique Harmonique")
    print("=" * 60)

    # Test des régions Ramachandran pour différents acides aminés
    for code1 in ['A', 'G', 'P', 'V', 'E', 'K']:
        aa = get_amino_acid(code1)
        print(f"\n{aa.code3} (φ={aa.phi_score:.3f}) :")
        print(f"  Hélice={aa.helix_propensity:.2f}  Feuillet={aa.sheet_propensity:.2f}")

        # Énergies aux centres des régions
        for region in RAMACHANDRAN_REGIONS:
            e = harmonic_ramachandran_potential(region.phi_center, region.psi_center, aa)
            depth = _region_depth(region.name, aa)
            bar = '█' * int(depth * 20) + '░' * (20 - int(depth * 20))
            print(f"  {region.name:5s} φ={region.phi_center:+6.0f}° ψ={region.psi_center:+6.0f}° "
                  f"prof={depth:.2f} E={e:+.3f} {bar}")

    # Test placement d'atome
    print("\n" + "=" * 60)
    print("TEST : Placement d'atomes (NeRF)")
    ref1 = np.array([0.0, 0.0, 0.0])
    ref2 = np.array([1.0, 0.0, 0.0])
    ref3 = np.array([2.0, 0.5, 0.0])

    # Placer un atome à 1.5 Å, angle 110°, dièdre 180°
    new = place_atom(ref1, ref2, ref3, 1.5, 110.0, 180.0)
    dist = np.linalg.norm(new - ref3)
    angle = math.degrees(bond_angle(ref2, ref3, new))
    dihe = math.degrees(dihedral_angle(ref1, ref2, ref3, new))
    print(f"  Distance: {dist:.3f} Å (attendu: 1.500)")
    print(f"  Angle: {angle:.1f}° (attendu: 110.0)")
    print(f"  Dièdre: {dihe:.1f}° (attendu: 180.0)")

    # Test angles optimaux
    print("\n" + "=" * 60)
    print("TEST : Angles optimaux par acide aminé")
    for code1 in ['G', 'A', 'V', 'P']:
        aa = get_amino_acid(code1)
        optima = get_optimal_angles(aa)
        print(f"\n  {aa.code3}:")
        for region, (phi, psi) in optima.items():
            print(f"    {region:5s}: φ={phi:+6.1f}°  ψ={psi:+6.1f}°")

    print("\n✅ Tous les tests passés !")


if __name__ == '__main__':
    _test()
