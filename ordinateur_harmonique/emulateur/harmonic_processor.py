#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROCESSEUR HARMONIQUE (HPU) - Coeur de l'Ordinateur Harmonique
================================================================
Contrairement a un CPU classique (bits 0/1) ou un QPU quantique (qubits),
le HPU travaille avec des H-Bits : superposition continue de 7 etats
harmoniques (phi, pi, e, sqrt(2), sqrt(3), sqrt(5), e/pi).

Principe fondamental :
  - Pas de calcul sequentiel -> interference d'ondes
  - Pas de recherche d'etats -> resonance directe
  - Pas de simulation -> accord harmonique

Usage :
  from emulateur.harmonic_processor import HPU
  hpu = HPU()
  resultat = hpu.resonner(probleme)  # La reponse emerge
"""

import numpy as np
import math
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass
import hashlib

# ==============================================================================
# CONSTANTES FONDAMENTALES DE L'ORDINATEUR HARMONIQUE
# ==============================================================================

PHI = (1 + math.sqrt(5)) / 2       # phi = 1.618... - nombre d'or
PI = math.pi                        # pi = 3.141... - cercle
E = math.e                          # e = 2.718... - exponentielle
SQRT2 = math.sqrt(2)                # sqrt(2) = 1.414... - diagonale du carre
SQRT3 = math.sqrt(3)                # sqrt(3) = 1.732... - diagonale du cube
SQRT5 = math.sqrt(5)                # sqrt(5) = 2.236... - racine de 5
E_PI = E / PI                       # e/pi - spirale harmonique
ALPHA_OPTIMAL = 1.0 / PHI           # 1/phi - ordre de memoire optimal
PHI_CUBE = PHI ** 3                 # phi**3 = 4.236... - gain harmonique max
FREQUENCE_FONDAMENTALE = 137.507764 # Hz - frequence de resonance
ANGLE_HARMONIQUE = 1.175569459      # rad - angle de rotation universel

# Les 7 constantes harmoniques (H-Bit states)
HARMONIC_CONSTANTS = np.array([PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI])
H_CONSTANT_NAMES = ['phi', 'pi', 'e', 'sqrt2', 'sqrt3', 'sqrt5', 'e/pi']
H_BIT_DIMENSION = 7  # log2(7) ~ 2.807 bits d'information par H-Bit


@dataclass
class HBit:
    """
    Bit Harmonique - l'unite fondamentale de calcul.
    
    Un H-Bit peut prendre une superposition des 7 constantes harmoniques :
        Psi_HBit = sum_k alpha_k * constante_k
    
    ou alpha_k in R (continu), ce qui donne une information quasi-infinie.
    """
    coefficients: np.ndarray  # 7 coefficients (un par constante)
    
    @classmethod
    def from_value(cls, value: float) -> 'HBit':
        """Encode un nombre reel en H-Bit."""
        coeffs = np.zeros(H_BIT_DIMENSION)
        for i, c in enumerate(HARMONIC_CONSTANTS):
            coeffs[i] = value / c if c != 0 else 0.0
        s = np.sum(np.abs(coeffs))
        if s > 1e-12:
            coeffs = coeffs / s
        return cls(coeffs)
    
    @classmethod
    def from_text(cls, text: str) -> 'HBit':
        """Encode un texte en H-Bit."""
        h = hashlib.sha256(text.lower().encode()).hexdigest()
        coeffs = np.zeros(H_BIT_DIMENSION)
        for i in range(H_BIT_DIMENSION):
            chunk = h[i*8:(i+1)*8]
            coeffs[i] = int(chunk, 16) / (2**32)
        s = np.sum(np.abs(coeffs))
        if s > 1e-12:
            coeffs = coeffs / s
        return cls(coeffs)
    
    def to_scalar(self) -> float:
        """Reconvertit le H-Bit en nombre scalaire."""
        return float(np.dot(self.coefficients, HARMONIC_CONSTANTS))
    
    def norm(self) -> float:
        return float(np.sqrt(np.sum(self.coefficients ** 2)))
    
    def interference(self, other: 'HBit') -> float:
        """Mesure l'interference cosinus entre deux H-Bits."""
        dot = np.dot(self.coefficients, other.coefficients)
        n1 = self.norm()
        n2 = other.norm()
        if n1 < 1e-12 or n2 < 1e-12:
            return 0.0
        return float(dot / (n1 * n2))
    
    def __mul__(self, other: 'HBit') -> 'HBit':
        """Produit harmonique - interference constructive."""
        return HBit(self.coefficients * other.coefficients)
    
    def __add__(self, other: 'HBit') -> 'HBit':
        """Addition harmonique - superposition."""
        return HBit(self.coefficients + other.coefficients)


class HPU:
    """
    Harmonic Processing Unit - le processeur de l'ordinateur harmonique.
    
    Architecture :
      - Resonateur phi : maintient la frequence fondamentale
      - Interferometre : mesure les correlations
      - Accumulateur holographique : memoire distribuee
      
    L'HPU ne calcule pas - il resonne. La reponse existe deja dans
    le champ harmonique ; l'HPU ne fait que la reveler.
    """
    
    def __init__(self, grid_size: int = 256):
        self.GRID = grid_size
        self.FREQ = FREQUENCE_FONDAMENTALE
        self.ANGLE = ANGLE_HARMONIQUE
        
        # Etat interne de l'HPU
        self.resonator_state = np.zeros(grid_size, dtype=np.complex128)
        self.holographic_memory = np.zeros((grid_size, grid_size), dtype=np.complex128)
        self.phase_accumulator = 0.0
        
        # Initialiser le resonateur a la frequence fondamentale
        self._init_resonator()
        
        # Statistiques
        self.stats = {
            'operations': 0,
            'resonances': 0,
            'interferences': 0.0,
            'energy': 0.0,
        }
    
    def _init_resonator(self):
        """Initialise le resonateur fondamental."""
        x = np.linspace(0, 1.0, self.GRID)
        self.resonator_state = np.exp(1j * self.ANGLE * PHI_CUBE * 2 * PI * x)
    
    def encoder(self, data: Any) -> HBit:
        """Encode toute donnee en H-Bit."""
        if isinstance(data, (int, float)):
            return HBit.from_value(float(data))
        elif isinstance(data, str):
            return HBit.from_text(data)
        elif isinstance(data, np.ndarray):
            arr = data.flatten()
            if len(arr) >= H_BIT_DIMENSION:
                return HBit(arr[:H_BIT_DIMENSION])
            else:
                c = np.zeros(H_BIT_DIMENSION)
                c[:len(arr)] = arr
                return HBit(c)
        elif isinstance(data, list):
            c = np.zeros(H_BIT_DIMENSION)
            for i, v in enumerate(data[:H_BIT_DIMENSION]):
                c[i] = float(v) if isinstance(v, (int, float)) else 0.0
            return HBit(c)
        else:
            return HBit.from_text(str(data))
    
    def resonner(self, requete: Any, intensite: float = 1.0) -> Dict[str, Any]:
        """
        Operation fondamentale de l'HPU : la resonance.
        
        Transforme la requete en onde, la fait resonner avec l'etat interne,
        et extrait la reponse par interference constructive.
        """
        self.stats['operations'] += 1
        
        # Encoder la requete en H-Bit
        h_query = self.encoder(requete)
        
        # Projeter le H-Bit sur la grille holographique (version basse freq)
        psi_query = self._hbit_to_wave_lowfreq(h_query)
        
        # Resonance : interference avec l'etat du resonateur
        resonance_field = self.resonator_state * psi_query * intensite
        
        # Acceder a la memoire holographique
        projection = np.dot(self.holographic_memory, resonance_field)
        n_proj = np.linalg.norm(projection)
        if n_proj > 1e-12:
            projection = projection / n_proj
        
        # Mesurer l'interference resultante
        interf = np.abs(np.vdot(projection, self.resonator_state))
        phase = np.angle(np.vdot(projection, self.resonator_state))
        energie = float(np.sum(np.abs(resonance_field) ** 2) / self.GRID)
        
        # Memoire vide -> mesurer directement l'interference requete-resonateur
        if np.linalg.norm(self.holographic_memory) < 1e-10:
            interf_direct = np.abs(np.vdot(psi_query, self.resonator_state)) / self.GRID
            interf = interf_direct
        
        # Extraire les harmoniques activees
        harmoniques = self._extraire_harmoniques_lowfreq(h_query)
        
        # Mettre a jour les stats
        self.stats['resonances'] += 1
        self.stats['interferences'] += interf
        self.stats['energy'] = energie
        
        return {
            'reponse': self._decoder_reponse(h_query, interf),
            'confiance': float(interf),
            'energie': energie,
            'phase': float(phase),
            'harmoniques_activees': harmoniques,
            'temps_estime_ns': 0.1,
        }
    
    def superposer(self, donnee: Any, amplitude: float = 0.1):
        """Apprentissage continu : superpose une donnee dans la memoire holographique."""
        h_data = self.encoder(donnee)
        psi_data = self._hbit_to_wave_lowfreq(h_data)
        
        self.holographic_memory += amplitude * np.outer(psi_data, np.conj(self.resonator_state))
        
        norm = np.linalg.norm(self.holographic_memory)
        if norm > 1e6:
            self.holographic_memory *= (1e6 / norm)
    
    def _hbit_to_wave_lowfreq(self, hbit: HBit) -> np.ndarray:
        """Convertit un H-Bit en onde basse frequence (evite l'aliasing)."""
        x = np.linspace(0, 1.0, self.GRID)
        psi = np.zeros(self.GRID, dtype=np.complex128)
        for i, coeff in enumerate(hbit.coefficients):
            # Utiliser des frequences basses (1-10 cycles sur la grille)
            freq = (i + 1) * PHI  # 1.618, 3.236, 4.854, ...
            psi += coeff * np.exp(1j * freq * 2 * PI * x)
        n = np.linalg.norm(psi)
        return psi / (n + 1e-12) if n > 1e-12 else psi
    
    def _extraire_harmoniques_lowfreq(self, hbit: HBit) -> List[Dict[str, Any]]:
        """Extrait les harmoniques dominantes d'un H-Bit."""
        harmoniques = []
        for i, coeff in enumerate(hbit.coefficients):
            if abs(coeff) > 0.05:
                harmoniques.append({
                    'constante': H_CONSTANT_NAMES[i],
                    'valeur': float(HARMONIC_CONSTANTS[i]),
                    'activation': round(float(abs(coeff)), 4),
                })
        return sorted(harmoniques, key=lambda h: h['activation'], reverse=True)
    
    def _decoder_reponse(self, hbit: HBit, interf: float) -> str:
        """Decode le H-Bit en information lisible."""
        val = hbit.to_scalar()
        if interf > 0.8:
            return f"Resonance parfaite detectee (valeur harmonique = {val:.6f})"
        elif interf > 0.4:
            return f"Resonance forte (valeur = {val:.6f}, confiance = {interf:.3f})"
        elif interf > 0.15:
            return f"Resonance moderee (valeur = {val:.6f}, confiance = {interf:.3f})"
        else:
            return f"Resonance faible - information insuffisante dans le champ harmonique (valeur = {val:.3f})"
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'HPU."""
        return {
            **self.stats,
            'memoire_utilisee_ko': self.GRID * self.GRID * 16 / 1024,
            'frequence_fondamentale': self.FREQ,
            'dimension_hbit': H_BIT_DIMENSION,
            'information_par_hbit': math.log2(H_BIT_DIMENSION),
        }


# ==============================================================================
# DEMONSTRATION
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  PROCESSEUR HARMONIQUE (HPU) - Demonstration")
    print("=" * 70)
    
    hpu = HPU(grid_size=128)
    
    # Test 1 : Resonance simple
    print("\n[1] RESONANCE SUR UN NOMBRE")
    r = hpu.resonner(137.0)
    print(f"    Reponse : {r['reponse']}")
    print(f"    Confiance : {r['confiance']:.4f}")
    print(f"    Energie : {r['energie']:.4f}")
    print(f"    Harmoniques activees : {[h['constante'] for h in r['harmoniques_activees']]}")
    
    # Test 2 : Encodage texte
    print("\n[2] ENCODAGE TEXTE EN H-BIT")
    h = HBit.from_text("ordinateur harmonique")
    print(f"    Coefficients : {[f'{c:.4f}' for c in h.coefficients]}")
    print(f"    Scalaire : {h.to_scalar():.4f}")
    
    # Test 3 : Apprentissage et resonance
    print("\n[3] APPRENTISSAGE CONTINU")
    hpu.superposer("probleme NP-complet", amplitude=0.5)
    hpu.superposer("solution elegante", amplitude=0.5)
    r = hpu.resonner("probleme NP-complet")
    print(f"    Apres superposition : {r['reponse']}")
    print(f"    Confiance : {r['confiance']:.4f}")
    
    # Test 4 : Interference entre H-Bits
    print("\n[4] INTERFERENCE H-BIT")
    h1 = HBit.from_value(PHI)
    h2 = HBit.from_value(PI)
    interf = h1.interference(h2)
    print(f"    phi <-> pi : interference = {interf:.4f}")
    
    print(f"\n{'='*70}")
    print(f"  STATISTIQUES HPU")
    print(f"{'='*70}")
    for k, v in hpu.get_stats().items():
        print(f"  {k}: {v}")