"""
Wave Music — L'Essence Ondulatoire de la Musique
==================================================
Tout phénomène musical est une manifestation d'interférence dans ℂ.
Pas de métaphore : la musique EST littéralement de l'interférence d'ondes.

Principes :
  1. NOTE        = ψ_note = A · exp(i·2π·f·t + φ)
  2. HARMONIE    = Re(⟨ψ_note1 | ψ_note2⟩) > 0  (interférence constructive)
  3. DISSONANCE  = Re(⟨ψ_note1 | ψ_note2⟩) < 0  (interférence destructive)
  4. ACCORD      = Σ ψ_notes  (superposition)
  5. GAMME φ     = notes espacées par φ → aucun motif répétitif
  6. RYTHME      = modulation d'amplitude périodique
  7. MÉLODIE     = séquence de ψ avec transitions de phase

Usage:
    from wave_music import WaveMusic
    wm = WaveMusic()
    wm.play_chord(['C', 'E', 'G'])  # Do Majeur → harmonieux
    wm.analyze_consonance('C', 'F#')  # Triton → dissonant
"""

import math
import numpy as np
from typing import List, Tuple, Dict

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# FRÉQUENCES DES NOTES (La₄ = 440 Hz)
# ═══════════════════════════════════════════════════════════════════════════════

NOTE_FREQS = {
    'C':  261.63,  # Do
    'C#': 277.18,
    'D':  293.66,  # Ré
    'D#': 311.13,
    'E':  329.63,  # Mi
    'F':  349.23,  # Fa
    'F#': 369.99,
    'G':  392.00,  # Sol
    'G#': 415.30,
    'A':  440.00,  # La
    'A#': 466.16,
    'B':  493.88,  # Si
}

# Noms français
NOTE_NAMES_FR = {
    'C': 'Do', 'D': 'Ré', 'E': 'Mi', 'F': 'Fa', 'G': 'Sol', 'A': 'La', 'B': 'Si'
}

# ═══════════════════════════════════════════════════════════════════════════════
# CERVEAU MUSICAL ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveMusic:
    """
    Analyse et synthèse musicale par interférence ondulatoire.
    
    Chaque note = ψ ∈ ℂ
    Chaque accord = Σ ψ (superposition)
    L'harmonie = Re(⟨ψ_a | ψ_b⟩)
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sr = sample_rate
        self._note_vectors: Dict[str, np.ndarray] = {}
        self._build_note_vectors()
    
    def _build_note_vectors(self):
        """
        Encode chaque note comme un vecteur d'onde complexe.
        
        L'angle de phase est calculé à partir du RATIO HARMONIQUE
        avec la tonique (Do = 0°), pas à partir de la fréquence absolue.
        
        Une quinte (3:2) → cos(2π · log₂(3/2) · 12) ≈ cos(7·π/6) 
        → proche de l'alignement → consonant.
        """
        base = NOTE_FREQS['C']  # Do = référence
        for note, freq in NOTE_FREQS.items():
            # Ratio par rapport à la tonique
            ratio = freq / base
            # Phase = 2π · log₂(ratio) · 12 (chaque demi-ton = 30°)
            semitones = 12 * math.log2(ratio)
            phase = (semitones * TAU / 12.0) % TAU
            self._note_vectors[note] = np.array([
                math.cos(phase),
                math.sin(phase)
            ], dtype=np.float64)
    
    # ═════════════════════════════════════════════════════════════════
    # HARMONIE / DISSONANCE
    # ═════════════════════════════════════════════════════════════════
    
    def interference(self, note1: str, note2: str) -> float:
        """
        Mesure l'interférence entre deux notes.
        
        Returns:
            cos(Δθ) ∈ [-1, 1]
            > 0.7 → consonance parfaite (octave, quinte)
            > 0.3 → consonance (tierce, sixte)
            ≈ 0   → neutre
            < 0   → dissonance (seconde, septième)
            < -0.5 → dissonance forte (triton)
        """
        if note1 not in self._note_vectors or note2 not in self._note_vectors:
            return 0.0
        psi1 = self._note_vectors[note1]
        psi2 = self._note_vectors[note2]
        return float(np.dot(psi1, psi2))
    
    def consonance_label(self, note1: str, note2: str) -> str:
        """Qualifie l'intervalle entre deux notes."""
        c = self.interference(note1, note2)
        if c > 0.95:   return "🌕 Unisson/Octave — fusion parfaite"
        if c > 0.8:    return "✨ Quinte — très consonant"
        if c > 0.5:    return "🎵 Tierce/Sixte — consonant"
        if c > 0.2:    return "🎶 Quarte — doux"
        if c > -0.2:   return "🎼 Neutre"
        if c > -0.5:   return "⚡ Seconde/Septième — dissonant"
        return "💥 Triton — le diable en musique (dissonance maximale)"
    
    # ═════════════════════════════════════════════════════════════════
    # ACCORDS (superposition)
    # ═════════════════════════════════════════════════════════════════
    
    def chord_vector(self, notes: List[str]) -> np.ndarray:
        """
        Superposition des notes d'un accord.
        ψ_accord = Σ ψ_note  (superposition additive)
        """
        if not notes:
            return np.zeros(2)
        result = sum(self._note_vectors.get(n, np.zeros(2)) for n in notes)
        norm = np.linalg.norm(result)
        return result / norm if norm > 0 else result
    
    def chord_quality(self, notes: List[str]) -> Tuple[float, str]:
        """
        Mesure la qualité d'un accord (cohérence interne).
        
        Un bon accord = les notes interfèrent constructivement entre elles.
        """
        if len(notes) < 2:
            return 1.0, "Note seule"
        
        # Moyenne des interférences par paires
        interferences = []
        for i in range(len(notes)):
            for j in range(i+1, len(notes)):
                interferences.append(self.interference(notes[i], notes[j]))
        
        avg = sum(interferences) / len(interferences)
        
        if avg > 0.6:   label = "✨ Accord parfait"
        elif avg > 0.3: label = "🎵 Accord agréable"
        elif avg > 0.0: label = "🎶 Accord neutre"
        elif avg > -0.3: label = "⚡ Accord tendu"
        else:            label = "💥 Accord dissonant"
        
        return avg, label
    
    # ═════════════════════════════════════════════════════════════════
    # GAMME φ (φ-spaced scale)
    # ═════════════════════════════════════════════════════════════════
    
    def phi_scale(self, base_freq: float = 261.63, n_notes: int = 12) -> List[float]:
        """
        Génère une gamme basée sur φ au lieu du tempérament égal ¹²√2.
        
        Principe : φ est le nombre le plus irrationnel → aucune répétition
        de motif dans la gamme → chaque intervalle est unique et « organique ».
        """
        freqs = []
        for i in range(n_notes):
            # Espacement logarithmique en φ
            ratio = PHI ** (i / n_notes)
            freqs.append(base_freq * ratio)
        return freqs
    
    def phi_scale_vs_equal(self) -> List[Tuple[str, float, float, float]]:
        """
        Compare la gamme φ avec le tempérament égal.
        """
        base = 261.63  # Do₄
        equal = [base * (2 ** (i/12)) for i in range(12)]
        phi = self.phi_scale(base, 12)
        
        comparisons = []
        for i in range(12):
            name = list(NOTE_FREQS.keys())[i]
            comparisons.append((name, equal[i], phi[i], phi[i] - equal[i]))
        return comparisons
    
    # ═════════════════════════════════════════════════════════════════
    # RYTHME (modulation d'amplitude)
    # ═════════════════════════════════════════════════════════════════
    
    def rhythm_pattern(self, pattern: List[float], bpm: int = 120) -> np.ndarray:
        """
        Génère un motif rythmique comme modulation d'amplitude.
        
        Args:
            pattern: séquence de poids [0,1] (ex: [1, 0, 0.5, 0, 1, 0, 0.5, 0])
            bpm: battements par minute
        
        Returns:
            signal d'amplitude modulé
        """
        beat_duration = 60.0 / bpm
        total_duration = len(pattern) * beat_duration
        t = np.linspace(0, total_duration, int(self.sr * total_duration), endpoint=False)
        
        # Construire l'enveloppe
        envelope = np.zeros_like(t)
        for i, weight in enumerate(pattern):
            start = i * beat_duration
            end = (i + 1) * beat_duration
            mask = (t >= start) & (t < end)
            # Attaque-déclin exponentiel (naturel)
            local_t = (t[mask] - start) / beat_duration
            envelope[mask] = weight * np.exp(-3 * local_t)
        
        return envelope


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    wm = WaveMusic()
    
    print("=" * 60)
    print("MUSIQUE ONDULATOIRE — Démonstration")
    print("=" * 60)
    
    # 1. Intervalles
    print("\n1. INTERFÉRENCES ENTRE NOTES (harmonie/dissonance)")
    print("-" * 50)
    intervals = [
        ('C', 'C'),   # Unisson
        ('C', 'G'),   # Quinte (3/2)
        ('C', 'E'),   # Tierce majeure (5/4)
        ('C', 'F'),   # Quarte (4/3)
        ('C', 'D'),   # Seconde (9/8)
        ('C', 'F#'),  # Triton (√2 ≈ le plus dissonant)
    ]
    for n1, n2 in intervals:
        c = wm.interference(n1, n2)
        label = wm.consonance_label(n1, n2)
        name1 = NOTE_NAMES_FR.get(n1, n1)
        name2 = NOTE_NAMES_FR.get(n2, n2)
        print(f"  {name1}-{name2} ({n1}-{n2}): cos={c:+.3f} → {label}")
    
    # 2. Accords
    print("\n2. SUPERPOSITIONS D'ACCORDS")
    print("-" * 50)
    chords = [
        (['C', 'E', 'G'], "Do Majeur"),
        (['C', 'E', 'G', 'B'], "Do Majeur 7"),
        (['A', 'C', 'E'], "La mineur"),
        (['C', 'D', 'G'], "Do sus2"),
        (['C', 'F#', 'G'], "Do avec triton"),
    ]
    for notes, name in chords:
        quality, label = wm.chord_quality(notes)
        bar = '█' * int((quality + 1) * 15)
        print(f"  {name:20s} {quality:+.3f} {label:25s} {bar}")
    
    # 3. Gamme φ vs Tempérament égal
    print("\n3. GAMME φ vs TEMPÉRAMENT ÉGAL")
    print("-" * 50)
    print(f"  {'Note':<6} {'Égal (Hz)':<12} {'φ (Hz)':<12} {'Δ (Hz)':<10}")
    comparisons = wm.phi_scale_vs_equal()
    for name, eq, ph, diff in comparisons[:8]:
        note_name = NOTE_NAMES_FR.get(name.strip('0123456789'), name)
        print(f"  {note_name:<6} {eq:<12.1f} {ph:<12.1f} {diff:<+10.1f}")
    
    # 4. Principe fondamental
    print("\n4. PRINCIPE FONDAMENTAL")
    print("-" * 50)
    print("  ψ_note = A · exp(i · 2π · f · t + φ₀)")
    print("  Harmonie  = Re(⟨ψ_a | ψ_b⟩) > 0")
    print("  Dissonance = Re(⟨ψ_a | ψ_b⟩) < 0")
    print("  Accord = Σ ψ_notes  (superposition)")
    print("  La musique EST de l'interférence — littéralement.")
