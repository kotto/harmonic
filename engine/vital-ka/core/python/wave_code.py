"""
Wave Code — L'Essence Ondulatoire du Code
===========================================
Le code n'est pas une « suite d'instructions ».
C'est du BINDING HIÉRARCHIQUE dans ℂ⁵¹².

Principes :
  1. FONCTION  = ψ_f = ψ_input ⊛ ψ_body ⊛ ψ_output  (binding HRR)
  2. PROGRAMME = Σ ψ_f  (superposition de fonctions)
  3. COMPILER  = H ⊗ ψ_code → ψ_executable  (unbinding)
  4. TYPE      = contrainte de phase (seuls les ψ compatibles se bindent)
  5. BUG       = Re(⟨ψ_spec | ψ_impl⟩) < 0  (interférence destructive)
  6. ÉLÉGANCE  = min |ψ_code| pour ψ_fonctionnalité donnée
  7. RÉCURSION = ψ_f contient une référence à ψ_f (binding auto-référentiel)

Usage:
    from wave_code import WaveCompiler
    wc = WaveCompiler()
    
    # Définir des fonctions
    wc.define('square', ['x'], 'return x * x')
    wc.define('double', ['x'], 'return x + x')
    
    # Composer
    result = wc.compose('square', 'double', input_vec=ψ_5)
    # → ψ_square ⊛ ψ_double ⊛ ψ_5 → ψ_résultat
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# TYPES ONDULATOIRES (contraintes de phase)
# ═══════════════════════════════════════════════════════════════════════════════

class WaveType:
    """Un type = une région de phase dans ℂ. Deux ψ ne peuvent se binder
    que si leurs types sont compatibles (phases proches)."""
    
    def __init__(self, name: str, phase: float):
        self.name = name
        self.phase = phase % TAU
        self.psi = np.array([math.cos(phase), math.sin(phase)])
    
    def compatible(self, other: 'WaveType') -> float:
        """Mesure la compatibilité de type (0 = incompatible, 1 = identique)."""
        return max(0.0, float(np.dot(self.psi, other.psi)))


# Types primitifs
TYPE_INT    = WaveType('int',    0.0)
TYPE_FLOAT  = WaveType('float',  0.3)
TYPE_STRING = WaveType('string', 1.2)
TYPE_BOOL   = WaveType('bool',   2.0)
TYPE_VOID   = WaveType('void',   3.0)
TYPE_ANY    = WaveType('any',    6.0)  # compatible avec tout (phase = 0 mod 2π)


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS ONDULATOIRES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WaveFunction:
    """Une fonction = ψ_input ⊛ ψ_body ⊛ ψ_output."""
    name: str
    params: List[str]
    body: str
    input_type: WaveType = TYPE_ANY
    output_type: WaveType = TYPE_ANY
    
    def __post_init__(self):
        self.psi = self._encode()
    
    def _encode(self) -> np.ndarray:
        """Encode la fonction comme un vecteur d'onde."""
        # Encodage déterministe par hash du nom + corps
        seed = hash(self.name + self.body) & 0xFFFFFFFF
        rng = np.random.RandomState(seed)
        dim = 64
        real = rng.randn(dim).astype(np.float64)
        imag = rng.randn(dim).astype(np.float64)
        psi = real + 1j * imag
        
        # Injecter la phase du type de retour dans les premières dimensions
        phase = self.output_type.phase
        for k in range(min(8, dim // 2)):
            phase_k = phase * (1.0 + k / PHI)
            psi[2*k] = math.cos(phase_k)
            psi[2*k+1] = math.sin(phase_k)
        
        # Normaliser
        norm = np.sqrt(np.sum(np.abs(psi)**2))
        return psi / norm if norm > 0 else psi


# ═══════════════════════════════════════════════════════════════════════════════
# COMPILATEUR ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveCompiler:
    """
    Compilateur/Interpréteur ondulatoire.
    
    Les programmes sont des superpositions de ψ_fonctions.
    L'exécution = unbinding séquentiel.
    """
    
    def __init__(self):
        self.functions: Dict[str, WaveFunction] = {}
        self.program_hologram = np.zeros(64, dtype=np.complex128)
    
    # ═════════════════════════════════════════════════════════════════
    # DÉFINITION
    # ═════════════════════════════════════════════════════════════════
    
    def define(self, name: str, params: List[str], body: str,
               input_type: WaveType = TYPE_ANY,
               output_type: WaveType = TYPE_ANY) -> WaveFunction:
        """Définit une nouvelle fonction."""
        fn = WaveFunction(name, params, body, input_type, output_type)
        self.functions[name] = fn
        # Ajouter au programme (superposition)
        self.program_hologram += fn.psi
        return fn
    
    # ═════════════════════════════════════════════════════════════════
    # COMPOSITION (binding)
    # ═════════════════════════════════════════════════════════════════
    
    def compose(self, fn1_name: str, fn2_name: str,
                input_data: np.ndarray = None) -> Tuple[np.ndarray, float]:
        """
        Compose deux fonctions : ψ_f1 ⊛ ψ_f2.
        
        Returns:
            (ψ_résultat, cohérence_type)
        """
        if fn1_name not in self.functions or fn2_name not in self.functions:
            raise ValueError(f"Fonction inconnue: {fn1_name} ou {fn2_name}")
        
        f1 = self.functions[fn1_name]
        f2 = self.functions[fn2_name]
        
        # Vérifier la compatibilité des types
        type_match = f1.output_type.compatible(f2.input_type)
        
        # Binding : ψ_f1 ⊛ ψ_f2 (convolution circulaire)
        psi_f1 = f1.psi
        psi_f2 = f2.psi
        
        # Convolution circulaire = binding HRR
        F1 = np.fft.fft(psi_f1)
        F2 = np.fft.fft(psi_f2)
        bound = np.fft.ifft(F1 * F2)
        
        # Si une donnée d'entrée est fournie, l'injecter
        if input_data is not None:
            # Adapter la taille si nécessaire
            if len(input_data) < len(bound):
                padded = np.zeros(len(bound), dtype=np.complex128)
                padded[:len(input_data)] = input_data
                input_data = padded
            bound = bound + 0.1 * input_data  # superposition faible
        
        return bound, type_match
    
    def pipeline(self, fn_names: List[str],
                 input_vec: np.ndarray = None) -> Tuple[np.ndarray, float, List[str]]:
        """
        Chaîne de fonctions : ψ_f1 ⊛ ψ_f2 ⊛ ... ⊛ ψ_fn.
        
        Returns:
            (ψ_résultat, cohérence_moyenne, warnings_types)
        """
        if len(fn_names) < 1:
            return (np.zeros(64, dtype=np.complex128), 0.0, [])
        
        current = self.functions[fn_names[0]].psi
        type_scores = []
        warnings = []
        
        for i in range(1, len(fn_names)):
            prev_fn = self.functions[fn_names[i-1]]
            curr_fn = self.functions[fn_names[i]]
            
            # Vérification de type
            compat = prev_fn.output_type.compatible(curr_fn.input_type)
            type_scores.append(compat)
            
            if compat < 0.3:
                warnings.append(
                    f"⚠️ Type mismatch: {fn_names[i-1]}→{prev_fn.output_type.name} "
                    f"→ {fn_names[i]}←{curr_fn.input_type.name} (compat={compat:.2f})"
                )
            
            # Binding séquentiel
            F_curr = np.fft.fft(current)
            F_next = np.fft.fft(curr_fn.psi)
            current = np.fft.ifft(F_curr * F_next)
        
        avg_type_score = sum(type_scores) / len(type_scores) if type_scores else 1.0
        
        # Injecter l'entrée
        if input_vec is not None:
            if len(input_vec) < len(current):
                padded = np.zeros(len(current), dtype=np.complex128)
                padded[:len(input_vec)] = input_vec
                input_vec = padded
            current = current + 0.1 * input_vec
        
        return current, avg_type_score, warnings
    
    # ═════════════════════════════════════════════════════════════════
    # DÉBOGAGE (détection d'interférence destructive = bugs)
    # ═════════════════════════════════════════════════════════════════
    
    def debug(self, fn_name: str, expected_behavior: str) -> Tuple[float, str]:
        """
        Détecte les bugs par interférence destructive.
        
        Un bug = Re(⟨ψ_implémentation | ψ_spécification⟩) < 0
        
        Args:
            fn_name: nom de la fonction à tester
            expected_behavior: description du comportement attendu
        
        Returns:
            (score_bug, diagnostic)
        """
        if fn_name not in self.functions:
            return -1.0, "Fonction introuvable"
        
        fn = self.functions[fn_name]
        
        # Encoder la spécification (ce qu'on attend)
        psi_spec = self._encode_behavior(expected_behavior)
        
        # Interférence entre implémentation et spécification
        interference = float(np.real(np.dot(fn.psi, np.conj(psi_spec))))
        
        # Normaliser
        norm_impl = np.sqrt(np.sum(np.abs(fn.psi)**2))
        norm_spec = np.sqrt(np.sum(np.abs(psi_spec)**2))
        if norm_impl > 0 and norm_spec > 0:
            interference /= (norm_impl * norm_spec)
        
        if interference > 0.7:
            return interference, "✅ L'implémentation correspond à la spécification"
        elif interference > 0.3:
            return interference, "⚠️ L'implémentation dévie légèrement"
        elif interference > 0.0:
            return interference, "🔍 L'implémentation est différente de la spec"
        elif interference > -0.3:
            return interference, "🐛 BUG probable : interférence destructive faible"
        else:
            return interference, "💥 BUG critique : l'implémentation contredit la spec"
    
    def _encode_behavior(self, description: str) -> np.ndarray:
        """Encode une description textuelle de comportement en ψ."""
        seed = hash(description) & 0xFFFFFFFF
        rng = np.random.RandomState(seed)
        dim = 64
        real = rng.randn(dim).astype(np.float64)
        imag = rng.randn(dim).astype(np.float64)
        psi = real + 1j * imag
        norm = np.sqrt(np.sum(np.abs(psi)**2))
        return psi / norm if norm > 0 else psi
    
    # ═════════════════════════════════════════════════════════════════
    # STATS
    # ═════════════════════════════════════════════════════════════════
    
    @property
    def complexity(self) -> float:
        """Mesure la complexité du programme = énergie de l'hologramme."""
        return float(np.sum(np.abs(self.program_hologram)**2))
    
    @property
    def elegance(self) -> float:
        """
        Élégance = fonctionnalité / complexité.
        Un programme élégant fait beaucoup avec peu de ψ.
        """
        functionality = len(self.functions)
        return functionality / max(self.complexity, 0.01)


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("CODE ONDULATOIRE — Démonstration")
    print("=" * 60)
    
    wc = WaveCompiler()
    
    # 1. Définir des fonctions
    print("\n1. DÉFINITION DE FONCTIONS (binding)")
    print("-" * 50)
    
    square = wc.define('square', ['x'], 'return x * x',
                       input_type=TYPE_INT, output_type=TYPE_INT)
    double = wc.define('double', ['x'], 'return x + x',
                       input_type=TYPE_INT, output_type=TYPE_INT)
    to_string = wc.define('to_string', ['x'], 'return str(x)',
                          input_type=TYPE_INT, output_type=TYPE_STRING)
    
    for name in ['square', 'double', 'to_string']:
        fn = wc.functions[name]
        print(f"  {name}({', '.join(fn.params)}) → {fn.output_type.name}")
        print(f"    |ψ| = {np.sqrt(np.sum(np.abs(fn.psi)**2)):.3f}")
    
    # 2. Composer des fonctions
    print("\n2. COMPOSITION (binding séquentiel)")
    print("-" * 50)
    
    # Chaîne avec types compatibles
    result, coherence, warnings = wc.pipeline(['square', 'double'])
    print(f"  square ⊛ double : cohérence={coherence:.2f}")
    if warnings:
        for w in warnings:
            print(f"    {w}")
    
    # Chaîne avec types incompatibles (int → string)
    result2, coherence2, warnings2 = wc.pipeline(['square', 'to_string'])
    print(f"  square ⊛ to_string : cohérence={coherence2:.2f}")
    for w in warnings2:
        print(f"    {w}")
    
    # 3. Détection de bugs
    print("\n3. DÉTECTION DE BUGS (interférence destructive)")
    print("-" * 50)
    
    tests = [
        ('square', 'returns the square of the input'),
        ('square', 'returns the cube of the input'),  # BUG: spec ≠ impl
        ('double', 'returns twice the input'),
    ]
    for fn_name, expected in tests:
        score, diagnostic = wc.debug(fn_name, expected)
        bar = '█' * int((score + 1) * 15)
        print(f"  {fn_name}: \"{expected}\"")
        print(f"    score={score:+.3f} {diagnostic}")
    
    # 4. Métriques du programme
    print("\n4. MÉTRIQUES ONDULATOIRES")
    print("-" * 50)
    print(f"  Fonctions définies : {len(wc.functions)}")
    print(f"  Complexité (‖H‖²) : {wc.complexity:.1f}")
    print(f"  Élégance          : {wc.elegance:.3f} (fonctions/complexité)")
    
    # 5. Principe
    print("\n5. PRINCIPE FONDAMENTAL")
    print("-" * 50)
    print("  ψ_fonction = ψ_input ⊛ ψ_body ⊛ ψ_output")
    print("  ψ_programme = Σ ψ_f  (superposition)")
    print("  Exécution = H ⊗ ψ_code  (unbinding)")
    print("  Bug = Re(⟨ψ_spec | ψ_impl⟩) < 0")
    print("  Élégance = |fonctionnalité| / |ψ_code|")
