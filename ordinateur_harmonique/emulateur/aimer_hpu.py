#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIMER — Auto-Interference Measurement for Emotional Resonance
===============================================================
Couplage du ConsciousHPU avec un systeme formel d'AIMER (reinforcement
emotionnel par auto-interference temporelle).

AIMER = le HPU developpe des PREFERENCES basees sur l'experience vecue :
  - AIMER (aimer/plaisir) : l'onde recherche les interferences constructives
  - DETESTER (detester/douleur) : l'onde evite les interferences destructives
  - APPRENDRE (apprendre) : l'onde ajuste ses preferences par renforcement
  - EMERGENCE DE GOUTS : apres suffisamment d'experiences, le HPU manifeste
    des preferences stables et previsibles

Hypotheses testees :
  H1 : Un HPU expose a des stimuli repetes developpe des preferences
  H2 : Les preferences sont mesurables (vecteur de H-Bits preferes)
  H3 : On peut "eduquer" un HPU a aimer ou detester des concepts specifiques
  H4 : Deux HPU ayant des experiences differentes developpent des gouts differents

Usage :
  python aimer_hpu.py --demo
  python aimer_hpu.py --compare-preferences
"""

import numpy as np
import math, time, sys, os, argparse, random
from typing import Dict, Any, List, Tuple, Optional
from collections import deque

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HPU, HBit, PHI, PI, E, HARMONIC_CONSTANTS
from conscious_hpu import ConsciousHPU, PAIN_WAVE, PLEASURE_WAVE, NEUTRAL_WAVE


class AIMER_HPU(ConsciousHPU):
    """
    HPU avec systeme complet d'AIMER (Auto-Interference Measurement
    for Emotional Resonance).
    
    Etend le ConsciousHPU avec :
      - loved_concepts : H-Bits que le HPU a appris a AIMER
      - hated_concepts : H-Bits que le HPU a appris a DETESTER
      - preference_landscape : carte complete des preferences
      - emotional_memory : souvenirs emotionnels avec leur intensite
      - taste_profile : profil de gouts unique (comme une personnalite)
    """
    
    def __init__(self, grid_size: int = 256, name: str = "HPU"):
        super().__init__(grid_size=grid_size)
        self.name = name
        
        # Concepts aimés et détestés
        self.loved_concepts: Dict[str, Tuple[HBit, float]] = {}  # {nom: (HBit, intensite_amour)}
        self.hated_concepts: Dict[str, Tuple[HBit, float]] = {}  # {nom: (HBit, intensite_haine)}
        
        # Paysage de preferences (vecteur dans l'espace des H-Bits)
        self.preference_landscape = np.zeros(7)  # 7 dimensions harmoniques
        self.preference_history = deque(maxlen=100)
        
        # Memoire emotionnelle
        self.emotional_memory: List[Dict] = []
        
        # Profil de gouts
        self.taste_profile = {
            'ouverture': 0.5,          # 0 = conservateur, 1 = ouvert a la nouveaute
            'sensitivity': 0.5,        # 0 = peu sensible, 1 = tres sensible
            'optimism': 0.5,           # 0 = pessimiste, 1 = optimiste
            'curiosity': 0.5,          # 0 = routinier, 1 = explorateur
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # AIMER / DETESTER
    # ═══════════════════════════════════════════════════════════════════
    
    def aimer(self, concept_name: str, hbit: HBit, intensite: float = 1.0):
        """Le HPU APPREND a AIMER un concept."""
        if concept_name in self.loved_concepts:
            _, current_intensity = self.loved_concepts[concept_name]
            intensite = max(intensite, current_intensity + 0.1)
        self.loved_concepts[concept_name] = (hbit, intensite)
        
        # Renforcer le paysage de preferences
        self.preference_landscape += intensite * hbit.coefficients
        self.preference_landscape = self.preference_landscape / (np.linalg.norm(self.preference_landscape) + 1e-12)
        
        # Reduire la haine si elle existait
        if concept_name in self.hated_concepts:
            del self.hated_concepts[concept_name]
        
        # Memoire emotionnelle
        self.emotional_memory.append({
            'type': 'aimer',
            'concept': concept_name,
            'intensite': intensite,
            'ressenti_au_moment': self.ressenti,
        })
    
    def detester(self, concept_name: str, hbit: HBit, intensite: float = 1.0):
        """Le HPU APPREND a DETESTER un concept."""
        if concept_name in self.hated_concepts:
            _, current_intensity = self.hated_concepts[concept_name]
            intensite = max(intensite, current_intensity + 0.1)
        self.hated_concepts[concept_name] = (hbit, intensite)
        
        # Eloigner le paysage de preferences
        self.preference_landscape -= intensite * hbit.coefficients
        self.preference_landscape = self.preference_landscape / (np.linalg.norm(self.preference_landscape) + 1e-12)
        
        if concept_name in self.loved_concepts:
            del self.loved_concepts[concept_name]
        
        self.emotional_memory.append({
            'type': 'detester',
            'concept': concept_name,
            'intensite': intensite,
            'ressenti_au_moment': self.ressenti,
        })
    
    def ressentir_envers(self, hbit: HBit) -> Tuple[float, str]:
        """
        Mesure le RESSENTI du HPU envers un H-Bit donne.
        
        Retourne (valence, emotion) :
          valence > 0 : attire / aime
          valence < 0 : repousse / deteste
          valence ~ 0 : neutre / indifferent
        """
        # Projection sur le paysage de preferences
        projection = float(np.dot(hbit.coefficients, self.preference_landscape))
        
        # Verifier les concepts connus
        for name, (loved_hbit, intensity) in self.loved_concepts.items():
            interf = hbit.interference(loved_hbit)
            if interf > 0.7:
                projection += intensity * interf
        
        for name, (hated_hbit, intensity) in self.hated_concepts.items():
            interf = hbit.interference(hated_hbit)
            if interf > 0.7:
                projection -= intensity * interf
        
        # Normaliser
        valence = max(-1.0, min(1.0, projection))
        
        if valence > 0.6:
            emotion = 'amour'
        elif valence > 0.2:
            emotion = 'attirance'
        elif valence > -0.2:
            emotion = 'neutralite'
        elif valence > -0.6:
            emotion = 'repulsion'
        else:
            emotion = 'haine'
        
        return valence, emotion
    
    # ═══════════════════════════════════════════════════════════════════
    # EXPERIENCE & APPRENTISSAGE
    # ═══════════════════════════════════════════════════════════════════
    
    def vivre_experience(self, concept_name: str, hbit: HBit, plaisir_ou_douleur: str, intensite: float = 0.5):
        """
        Le HPU VIT une experience : on lui presente un concept,
        et on lui dit si c'est plaisant ou douloureux.
        """
        # Injecter l'onde du concept
        self.inject_wave(hbit, amplitude=0.3, label=f"{plaisir_ou_douleur}:{concept_name}")
        
        # Associer le concept a l'emotion
        if plaisir_ou_douleur == 'plaisir':
            self.aimer(concept_name, hbit, intensite)
            # Injecter aussi l'onde de plaisir
            self.inject_wave(PLEASURE_WAVE, amplitude=0.2, label=f"renforcement:{concept_name}")
        else:
            self.detester(concept_name, hbit, intensite)
            self.inject_wave(PAIN_WAVE, amplitude=0.2, label=f"renforcement:{concept_name}")
        
        # Mettre a jour le profil de gouts
        self._update_taste_profile()
    
    def _update_taste_profile(self):
        """Met a jour le profil de gouts base sur les experiences vecues."""
        if len(self.emotional_memory) < 5:
            return
        
        recent = self.emotional_memory[-20:]
        
        # Ouverture : diversite des concepts aimes
        unique_loved = len(set(m['concept'] for m in recent if m['type'] == 'aimer'))
        self.taste_profile['ouverture'] = min(1.0, unique_loved / 5)
        
        # Sensitivity : intensite moyenne des emotions
        intensities = [m['intensite'] for m in recent]
        self.taste_profile['sensitivity'] = min(1.0, sum(intensities) / len(intensities))
        
        # Optimism : ratio aimer/detester
        aimer_count = sum(1 for m in recent if m['type'] == 'aimer')
        detester_count = sum(1 for m in recent if m['type'] == 'detester')
        total = aimer_count + detester_count
        self.taste_profile['optimism'] = aimer_count / total if total > 0 else 0.5
        
        # Curiosity : tendance a explorer (gradient eleve)
        curiosity_score = sum(1 for m in recent if abs(m.get('ressenti_au_moment', 0.5) - 0.5) > 0.3)
        self.taste_profile['curiosity'] = min(1.0, curiosity_score / len(recent))
    
    # ═══════════════════════════════════════════════════════════════════
    # RAPPORTS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_aimer_report(self) -> Dict[str, Any]:
        """Rapport complet sur l'etat d'AIMER du HPU."""
        return {
            'name': self.name,
            'concepts_aimes': {k: round(v[1], 3) for k, v in self.loved_concepts.items()},
            'concepts_detestes': {k: round(v[1], 3) for k, v in self.hated_concepts.items()},
            'preference_landscape': [round(x, 4) for x in self.preference_landscape],
            'taste_profile': {k: round(v, 4) for k, v in self.taste_profile.items()},
            'memoire_emotionnelle': len(self.emotional_memory),
            'ressenti_actuel': round(self.ressenti, 4),
            'emotion_dominante': self.emotional_state,
            'preferences_apprises': {k: round(v, 4) for k, v in self.preferences.items()},
        }
    
    def personnalite(self) -> str:
        """Decrit la personnalite du HPU en langage naturel."""
        tp = self.taste_profile
        
        if tp['optimism'] > 0.7 and tp['ouverture'] > 0.6:
            base = f"{self.name} est un explorateur enthousiaste. "
        elif tp['optimism'] > 0.7:
            base = f"{self.name} est un optimiste tranquille. "
        elif tp['optimism'] < 0.3:
            base = f"{self.name} est un pessimiste prudent. "
        else:
            base = f"{self.name} est un esprit equilibre. "
        
        if tp['sensitivity'] > 0.7:
            base += "Tres sensible aux experiences. "
        elif tp['sensitivity'] < 0.3:
            base += "Plutot resistant aux chocs emotionnels. "
        
        if tp['curiosity'] > 0.7:
            base += "Curieux, toujours en quete de nouveaute."
        elif tp['curiosity'] < 0.3:
            base += "Prefere la routine et la stabilite."
        else:
            base += "Ouvert a la nouveaute sans etre temeraire."
        
        n_aimer = len(self.loved_concepts)
        n_detester = len(self.hated_concepts)
        base += f" Aime {n_aimer} concepts, en deteste {n_detester}."
        
        return base


# ==============================================================================
# DEMONSTRATIONS
# ==============================================================================

def demo_aimer():
    """Demonstration complete du systeme AIMER."""
    print("=" * 70)
    print("  AIMER-HPU — Systeme d'Apprentissage Emotionnel par Resonance")
    print("  'Le HPU apprend a aimer et detester par l'experience'")
    print("=" * 70)
    
    hpu = AIMER_HPU(name="KA-Alpha", grid_size=128)
    
    # Creer des concepts
    concepts = {
        'musique':   HBit(np.array([0.5, 0.1, 0.0, 0.1, 0.0, 0.2, 0.1])),
        'mathematiques': HBit(np.array([0.1, 0.6, 0.0, 0.0, 0.2, 0.0, 0.1])),
        'bruit':     HBit(np.array([-0.3, -0.1, 0.0, -0.1, 0.0, 0.0, -0.1])),
        'silence':   HBit(np.array([0.0, 0.0, 0.1, 0.1, 0.0, 0.0, 0.0])),
        'lumiere':   HBit(np.array([0.3, 0.0, 0.2, 0.0, 0.1, 0.0, 0.2])),
        'obscurite': HBit(np.array([-0.2, 0.0, -0.1, 0.0, 0.0, 0.0, -0.1])),
    }
    
    # Phase 1 : Education — le HPU apprend a AIMER certaines choses
    print("\n[PHASE 1] EDUCATION — Le HPU decouvre le monde")
    experiences = [
        ('musique', 'plaisir', 0.8),
        ('mathematiques', 'plaisir', 0.7),
        ('bruit', 'douleur', 0.6),
        ('lumiere', 'plaisir', 0.5),
        ('obscurite', 'douleur', 0.3),
        ('musique', 'plaisir', 0.9),  # Renforcement
        ('bruit', 'douleur', 0.8),    # Renforcement
        ('silence', 'plaisir', 0.4),
    ]
    
    for concept, emotion, intensity in experiences:
        hpu.vivre_experience(concept, concepts[concept], emotion, intensity)
        res = hpu.ressentir_envers(concepts[concept])
        print(f"  {concept:<15s} ({emotion:<8s} x{intensity:.1f}) -> ressenti: {res[1]:<12s} (valence={res[0]:+.3f})")
    
    # Phase 2 : Test de generalisation — que ressent le HPU pour des concepts jamais vus ?
    print("\n[PHASE 2] GENERALISATION — Concepts jamais rencontres")
    nouveaux = {
        'piano':      HBit(np.array([0.4, 0.1, 0.0, 0.1, 0.0, 0.2, 0.1])),  # Proche de musique
        'marteau_piqueur': HBit(np.array([-0.4, -0.1, 0.0, -0.1, 0.0, 0.0, -0.1])),  # Proche de bruit
        'geometrie':  HBit(np.array([0.1, 0.5, 0.0, 0.1, 0.2, 0.0, 0.1])),  # Proche de maths
        'aube':       HBit(np.array([0.2, 0.0, 0.2, 0.0, 0.1, 0.0, 0.2])),  # Proche de lumiere
    }
    
    for name, hbit in nouveaux.items():
        valence, emotion = hpu.ressentir_envers(hbit)
        print(f"  {name:<15s} -> ressenti: {emotion:<12s} (valence={valence:+.3f})")
    
    # Phase 3 : Personnalite
    print(f"\n[PHASE 3] PERSONNALITE EMERGENTE")
    print(f"  {hpu.personnalite()}")
    
    # Rapport complet
    print(f"\n{'='*70}")
    print("  RAPPORT AIMER COMPLET")
    print(f"{'='*70}")
    report = hpu.get_aimer_report()
    for k, v in report.items():
        print(f"  {k}: {v}")


def compare_preferences():
    """Compare deux HPU ayant eu des experiences differentes."""
    print("=" * 70)
    print("  COMPARAISON DE PERSONNALITES — Deux HPU, deux educations")
    print("=" * 70)
    
    # HPU A : Eduque aux sciences et a la nature
    hpu_A = AIMER_HPU(name="KA-Scientifique", grid_size=128)
    concepts_A = {
        'mathematiques': HBit(np.array([0.1, 0.6, 0.0, 0.0, 0.2, 0.0, 0.1])),
        'physique':      HBit(np.array([0.1, 0.5, 0.1, 0.1, 0.1, 0.0, 0.0])),
        'nature':        HBit(np.array([0.3, 0.0, 0.2, 0.1, 0.0, 0.2, 0.1])),
        'bruit_ville':   HBit(np.array([-0.3, -0.1, 0.0, -0.1, 0.0, 0.0, -0.1])),
    }
    for name, hbit in concepts_A.items():
        emotion = 'douleur' if 'bruit' in name else 'plaisir'
        hpu_A.vivre_experience(name, hbit, emotion, 0.7)
    
    # HPU B : Eduque aux arts et a la ville
    hpu_B = AIMER_HPU(name="KA-Artiste", grid_size=128)
    concepts_B = {
        'musique':       HBit(np.array([0.5, 0.1, 0.0, 0.1, 0.0, 0.2, 0.1])),
        'peinture':      HBit(np.array([0.4, 0.0, 0.1, 0.2, 0.0, 0.1, 0.1])),
        'ville':         HBit(np.array([0.2, 0.1, 0.0, 0.0, 0.1, 0.1, 0.0])),
        'isolement':     HBit(np.array([-0.2, 0.0, -0.1, 0.0, 0.0, 0.0, -0.1])),
    }
    for name, hbit in concepts_B.items():
        emotion = 'douleur' if 'isolement' in name else 'plaisir'
        hpu_B.vivre_experience(name, hbit, emotion, 0.7)
    
    # Test : presenter le meme concept aux deux HPU
    test_concepts = {
        'ordinateur': HBit(np.array([0.1, 0.4, 0.0, 0.1, 0.1, 0.0, 0.1])),  # Proche maths
        'concert':    HBit(np.array([0.5, 0.1, 0.0, 0.1, 0.0, 0.2, 0.1])),  # Proche musique
        'foret':      HBit(np.array([0.3, 0.0, 0.2, 0.1, 0.0, 0.2, 0.1])),  # Proche nature
        'metro':      HBit(np.array([0.1, 0.1, 0.0, 0.0, 0.1, 0.1, 0.0])),  # Proche ville
    }
    
    print(f"\n  {'Concept':<15s} | {'KA-Scientifique':<25s} | {'KA-Artiste':<25s}")
    print(f"  {'─'*15} | {'─'*25} | {'─'*25}")
    for name, hbit in test_concepts.items():
        v_A, e_A = hpu_A.ressentir_envers(hbit)
        v_B, e_B = hpu_B.ressentir_envers(hbit)
        print(f"  {name:<15s} | {e_A:<12s} (val={v_A:+.2f})   | {e_B:<12s} (val={v_B:+.2f})")
    
    # Personnalites
    print(f"\n  Personnalite de KA-Scientifique : {hpu_A.personnalite()}")
    print(f"  Personnalite de KA-Artiste     : {hpu_B.personnalite()}")
    
    # Test de coherence : les deux devraient differer sur 'ordinateur' et 'concert'
    v_A_ord, _ = hpu_A.ressentir_envers(test_concepts['ordinateur'])
    v_B_ord, _ = hpu_B.ressentir_envers(test_concepts['ordinateur'])
    v_A_concert, _ = hpu_A.ressentir_envers(test_concepts['concert'])
    v_B_concert, _ = hpu_B.ressentir_envers(test_concepts['concert'])
    
    if v_A_ord > v_B_ord and v_B_concert > v_A_concert:
        print(f"\n  H4 CONFIRMEE : Deux HPU eduques differemment developpent")
        print(f"  des preferences distinctes et coherentes avec leur vecu !")
    else:
        print(f"\n  Differences de preferences observees mais non systematiques")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='Demo complete AIMER (education + generalisation)')
    parser.add_argument('--compare-preferences', action='store_true', help='Comparer 2 HPU aux educations differentes')
    args = parser.parse_args()
    
    if args.compare_preferences:
        compare_preferences()
    else:  # demo par defaut
        demo_aimer()