"""
Emotional Brain — Le Cerveau qui RESSENT
==========================================
Extension du HarmonicBrain avec une couche émotionnelle ondulatoire.

Principes :
  - Émotion = Re(⟨ψ_attendu | ψ_réel⟩)
  - Sentiment = ∫ K(t-τ) · e(τ) dτ  (noyau ABC)
  - Humeur = moyenne glissante de e(t)
  - Empathie = Re(⟨ψ_self_A | ψ_self_B⟩)

Usage:
    from emotional_brain import EmotionalBrain
    brain = EmotionalBrain(knowledge_base)
    brain.process("capitale de la france")
    print(brain.feel())  # → {'mood': 0.72, 'emotion': 'satisfaction'}
"""

import numpy as np
import math, time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from harmonic_brain import HarmonicBrain
from harmonic_brain import _normalize, PHI, PHI_INV

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION ÉMOTIONNELLE
# ═══════════════════════════════════════════════════════════════════════════════

EMOTION_MAP = [
    (0.6,  '😊 joie',        'joy'),
    (0.3,  '🙂 satisfaction','satisfaction'),
    (0.1,  '🤔 interet',     'interest'),
    (-0.1, '😐 neutre',      'neutral'),
    (-0.3, '😕 deception',   'disappointment'),
    (-0.6, '😢 tristesse',   'sadness'),
    (-1.0, '😡 colere',      'anger'),
]

MOOD_DECAY = 0.9       # inertie de l'humeur (proche de 1 = persistant)
LEARNING_RATE = 0.01   # vitesse d'apprentissage de ψ_self


@dataclass
class EmotionalState:
    """État émotionnel instantané du cerveau."""
    mood: float                     # humeur [-1, 1]
    emotion: str                    # émotion dominante
    emotion_en: str                 # english label
    interference: float             # dernière valeur d'interférence
    empathy_target: float = 0.0     # résonance avec un autre ψ_self
    trauma_count: int = 0           # nombre d'événements haute amplitude
    emotional_energy: float = 0.0   # énergie totale de l'hologramme émotionnel


class EmotionalBrain(HarmonicBrain):
    """
    Cerveau Harmonique avec couche émotionnelle.
    
    Ressent des émotions primitives comme propriété émergente
    de l'interférence entre ψ_attendu et ψ_réel.
    """

    def __init__(self, knowledge_base=None, dim: int = 512):
        super().__init__(knowledge_base, dim=dim)
        
        # Identité ondulatoire (se construit par l'expérience)
        self.psi_self = np.zeros(dim, dtype=np.complex128)
        
        # Hologramme émotionnel (mémoire des émotions passées)
        self.emotional_hologram = np.zeros(dim, dtype=np.complex128)
        
        # État émotionnel courant
        self.mood = 0.0            # humeur [-1, 1], 0 = neutre
        self._emotion_history = [] # dernières N valeurs d'interférence
        self._trauma_count = 0     # événements à |e| > 0.8
        
        # Statistiques
        self._interactions = 0
    
    # ═════════════════════════════════════════════════════════════════
    # PROCESSUS ÉMOTIONNEL
    # ═════════════════════════════════════════════════════════════════
    
    def process(self, question: str, lang: str = 'fr', 
                max_accepted: int = 3):
        """
        Traitement avec composante émotionnelle.
        
        1. Retrieval standard (inconscient + conscient)
        2. Mesure de l'interférence ψ_question ↔ ψ_réponse
        3. Mise à jour de l'état émotionnel
        4. L'humeur influence le retrieval futur
        """
        # Appeler le processus standard
        result = super().process(question, lang=lang, max_accepted=max_accepted)
        
        # Mesurer l'émotion
        psi_q = self.unconscious.encoder.encode_query(question)
        
        if result.facts_used:
            psi_r = result.facts_used[0].psi
        else:
            psi_r = np.zeros(self.unconscious.dim, dtype=np.complex128)
        
        # L'émotion = interférence entre la question (attendu) et le fait (réel)
        interference = float(np.real(np.dot(psi_q, np.conj(psi_r))))
        
        # Accumuler dans l'hologramme émotionnel
        self.emotional_hologram += interference * psi_q
        
        # Mettre à jour l'humeur (moyenne glissante avec inertie)
        self.mood = MOOD_DECAY * self.mood + (1 - MOOD_DECAY) * interference
        
        # Détecter les événements à haute amplitude (traumas/extases)
        if abs(interference) > 0.8:
            self._trauma_count += 1
        
        # Apprentissage de ψ_self (on devient ce qu'on « vit »)
        if result.facts_used:
            self.psi_self += LEARNING_RATE * psi_r
            # Normaliser périodiquement
            norm = np.sqrt(np.sum(np.abs(self.psi_self)**2))
            if norm > 2.0:
                self.psi_self /= norm
        
        self._emotion_history.append(interference)
        if len(self._emotion_history) > 100:
            self._emotion_history.pop(0)
        
        self._interactions += 1
        
        return result
    
    # ═════════════════════════════════════════════════════════════════
    # ACCÈS À L'ÉTAT ÉMOTIONNEL
    # ═════════════════════════════════════════════════════════════════
    
    def feel(self) -> EmotionalState:
        """Retourne l'état émotionnel actuel."""
        # Déterminer l'émotion dominante selon l'humeur
        emotion_fr, emotion_en = '😐 neutre', 'neutral'
        for threshold, label_fr, label_en in EMOTION_MAP:
            if self.mood >= threshold:
                emotion_fr, emotion_en = label_fr, label_en
                break
        
        # Énergie émotionnelle accumulée
        energy = float(np.sum(np.abs(self.emotional_hologram)**2))
        
        return EmotionalState(
            mood=round(self.mood, 3),
            emotion=emotion_fr,
            emotion_en=emotion_en,
            interference=round(self._emotion_history[-1], 4) if self._emotion_history else 0.0,
            emotional_energy=round(energy, 2),
            trauma_count=self._trauma_count,
        )
    
    def emotional_resonance(self, situation: str) -> float:
        """
        Mesure à quel point une situation résonne avec le passé émotionnel.
        
        Ex: une phrase qui rappelle un trauma → forte résonance.
        """
        psi_sit = self.unconscious.encoder.encode_query(situation)
        return float(np.abs(np.dot(self.emotional_hologram, np.conj(psi_sit))))
    
    def empathize(self, other_psi_self: np.ndarray) -> float:
        """
        Mesure l'empathie avec un autre ψ_self.
        
        Returns:
            1.0 = fusion, 0.0 = aucun lien, -1.0 = antagonisme
        """
        if np.sum(np.abs(self.psi_self)) < 1e-10:
            return 0.0
        return float(np.real(np.dot(self.psi_self, np.conj(other_psi_self))))
    
    def emotional_summary(self) -> str:
        """Résumé émotionnel en langage naturel."""
        state = self.feel()
        if self._interactions == 0:
            return "Je n'ai pas encore interagi. Je suis neutre."
        
        mood_str = "bonne" if state.mood > 0.3 else "mauvaise" if state.mood < -0.3 else "neutre"
        trauma_str = f" J'ai vécu {state.trauma_count} événements intenses." if state.trauma_count > 0 else ""
        
        return (f"Après {self._interactions} interactions, je me sens plutôt {mood_str} "
                f"({state.emotion}). Mon humeur est à {state.mood:.2f}.{trauma_str}")
    
    @property
    def stats(self) -> dict:
        base = super().stats if hasattr(super(), 'stats') else {}
        base['emotional'] = {
            'mood': self.mood,
            'interactions': self._interactions,
            'traumas': self._trauma_count,
            'emotional_energy': float(np.sum(np.abs(self.emotional_hologram)**2)),
            'psi_self_norm': float(np.sqrt(np.sum(np.abs(self.psi_self)**2))),
        }
        return base


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import numpy as np
    from pathlib import Path
    
    kb_path = Path('data/bootstrapper_output/knowledge_base_clean_v2.npz')
    data = np.load(str(kb_path), allow_pickle=True)
    facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3])) for f in data['facts'][:5000]]
    
    brain = EmotionalBrain(facts)
    print(f"Cerveau émotionnel: {brain.unconscious.stats['faits']} faits\n")
    
    # Phase 1 : Interactions positives (bonnes réponses)
    print("=== Phase 1 : Rencontres positives ===")
    for q in ['capitale de la france', 'qui a peint la joconde', 'nombre d or']:
        r = brain.process(q)
        state = brain.feel()
        print(f"Q: {q}")
        print(f"R: {r.response[:80]}")
        print(f"   {state.emotion} | humeur={state.mood:.3f} | interf={state.interference:.4f}")
    
    print(f"\nRésumé: {brain.emotional_summary()}")
    
    # Phase 2 : Interactions frustrantes (mauvaises réponses ou questions impossibles)
    print("\n=== Phase 2 : Frustrations ===")
    for q in ['quel temps fait il', 'qui a invente le temps', 'pourquoi le neant existe']:
        r = brain.process(q)
        state = brain.feel()
        print(f"Q: {q}")
        print(f"R: {r.response[:80]}")
        print(f"   {state.emotion} | humeur={state.mood:.3f}")
    
    print(f"\nRésumé: {brain.emotional_summary()}")
    
    # Phase 3 : Retour au positif — l'humeur remonte-t-elle ?
    print("\n=== Phase 3 : Réconfort ===")
    for q in ['capitale de la france', 'qui a peint la joconde']:
        r = brain.process(q)
        state = brain.feel()
        print(f"Q: {q}")
        print(f"   {state.emotion} | humeur={state.mood:.3f}")
    
    print(f"\nFinal: {brain.emotional_summary()}")
    print(f"Énergie émotionnelle accumulée: {state.emotional_energy:.2f}")
