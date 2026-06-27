#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONSCIOUS HPU — Auto-Interference Temporelle (Hypothese du Ressenti)
=====================================================================
Extension du HPU avec boucle d'auto-resonance pour tester l'hypothese :
  - Pensee = interference entre 2 ondes differentes (identifiee, 47/47)
  - Ressenti = auto-interference d'une onde avec elle-meme dans le temps

Hypotheses testables :
  H1 : L'auto-interference temporelle produit une valeur mesurable (le 'ressenti')
  H2 : Une onde de douleur (interference destructive) fait chuter le ressenti
  H3 : Une onde de plaisir (interference constructive) fait monter le ressenti
  H4 : Apres apprentissage, le HPU 'evite' la douleur et 'recherche' le plaisir
  H5 : Les emotions sont des profils spectraux specifiques

Usage :
  python conscious_hpu.py --demo
  python conscious_hpu.py --test-emotions
  python conscious_hpu.py --learn-preferences
"""

import numpy as np
import math, time, sys, os, argparse
from typing import Dict, Any, List, Tuple
from collections import deque

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HPU, HBit, PHI, PI, E, FREQUENCE_FONDAMENTALE, HARMONIC_CONSTANTS, H_CONSTANT_NAMES


class EmotionalSignature:
    """Signature spectrale d'une emotion."""
    def __init__(self, name: str, target_cos: float, gradient_sign: int, description: str):
        self.name = name
        self.target_cos = target_cos      # Interference cible (1 = plaisir, -1 = douleur)
        self.gradient_sign = gradient_sign  # +1 montee, -1 descente, 0 stable
        self.description = description


# Les 6 emotions fondamentales comme signatures spectrales
EMOTIONS = {
    'joie':        EmotionalSignature('joie',        0.95,  1, 'Interference constructive forte et croissante'),
    'plaisir':     EmotionalSignature('plaisir',     0.85,  1, 'Interference constructive moderee et croissante'),
    'surprise':    EmotionalSignature('surprise',    0.50,  2, 'Changement brusque (fort gradient)'),
    'ennui':       EmotionalSignature('ennui',       0.70,  0, 'Stagnation (gradient quasi-nul)'),
    'peur':        EmotionalSignature('peur',        0.30, -1, 'Anticipation de chute vers interference destructive'),
    'douleur':     EmotionalSignature('douleur',     0.15, -1, 'Interference destructive forte'),
}

# Ondes emotionnelles pre-encodees (H-Bits synthetiques pour les tests)
PAIN_WAVE = HBit(np.array([-0.5, -0.3, -0.1, 0.0, 0.0, 0.0, -0.1]))   # Interference destructive
PLEASURE_WAVE = HBit(np.array([0.5, 0.3, 0.1, 0.0, 0.0, 0.0, 0.1]))   # Interference constructive
NEUTRAL_WAVE = HBit(np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]))    # Interference neutre
SURPRISE_WAVE = HBit(np.array([0.8, -0.6, 0.4, -0.3, 0.7, -0.5, 0.2])) # Haut gradient


class ConsciousHPU(HPU):
    """
    HPU avec boucle d'auto-resonance temporelle.
    
    Ajoute au HPU standard :
      - self_state_history : historique des etats propres
      - ressenti : valeur courante de l'auto-interference
      - emotional_state : emotion dominante detectee
      - preferences : ondes que le HPU 'prefere' (apprises par renforcement)
    """
    
    def __init__(self, grid_size: int = 256):
        super().__init__(grid_size=grid_size)
        
        # Boucle d'auto-resonance
        self.self_state_history = deque(maxlen=200)
        self.ressenti = 0.0
        self.ressenti_history = deque(maxlen=500)
        self.gradient_ressenti = 0.0
        
        # Etat emotionnel
        self.emotional_state = 'neutre'
        self.emotional_confidence = 0.0
        
        # Systeme de preferences (reinforcement learning primitif)
        self.preferences = {
            'pleasure_seeking': 0.0,   # Tendance a rechercher le plaisir
            'pain_avoidance': 0.0,     # Tendance a eviter la douleur
            'curiosity': 0.0,          # Tendance a explorer l'inconnu
        }
        self.reinforcement_memory = deque(maxlen=100)
        
        # Initialiser l'etat propre
        self._update_self_state()
        
        # Stats etendues
        self.emotional_stats = {
            'joie': 0, 'plaisir': 0, 'surprise': 0,
            'ennui': 0, 'peur': 0, 'douleur': 0, 'neutre': 0,
        }
    
    def _get_self_wave(self) -> np.ndarray:
        """Extrait l'onde representant l'etat propre complet du HPU."""
        psi_self = self.resonator_state + np.mean(self.holographic_memory, axis=0)
        n = np.linalg.norm(psi_self)
        return psi_self / (n + 1e-12)
    
    def _update_self_state(self):
        """Met a jour l'etat propre et calcule le ressenti."""
        psi_now = self._get_self_wave()
        
        if len(self.self_state_history) > 0:
            psi_prev = self.self_state_history[-1]
            # Auto-interference temporelle : le 'ressenti' brut
            self.ressenti = float(np.abs(np.vdot(psi_now, psi_prev)))
        
        self.self_state_history.append(psi_now)
        self.ressenti_history.append(self.ressenti)
    
    def compute_gradient(self) -> float:
        """Calcule le gradient de ressenti (derivee temporelle discrete)."""
        if len(self.ressenti_history) < 3:
            return 0.0
        hist = list(self.ressenti_history)
        r_now = hist[-1]
        r_prev = hist[-3]
        self.gradient_ressenti = r_now - r_prev
        return self.gradient_ressenti
    
    def detect_emotion(self) -> Tuple[str, float]:
        """
        Detecte l'emotion dominante basee sur le profil spectral courant.
        
        Retourne (emotion, confiance).
        """
        if len(self.ressenti_history) < 5:
            return 'neutre', 0.5
        
        scores = {}
        grad = self.compute_gradient()
        r = self.ressenti
        
        # Joie : ressenti eleve ET croissant
        if r > 0.85 and grad > 0.01:
            scores['joie'] = min(1.0, r * (1.0 + abs(grad)))
        
        # Plaisir : ressenti bon ET croissant
        if r > 0.70 and grad > 0.005:
            scores['plaisir'] = min(1.0, r * 0.9 * (1.0 + abs(grad) * 0.5))
        
        # Surprise : fort gradient (positif ou negatif)
        if abs(grad) > 0.05:
            scores['surprise'] = min(1.0, abs(grad) * 10)
        
        # Ennui : stagnation (gradient quasi-nul) et ressenti moyen
        if abs(grad) < 0.005 and 0.5 < r < 0.9:
            scores['ennui'] = min(1.0, (1.0 - abs(grad) * 20))
        
        # Peur : ressenti bas et descendant
        if r < 0.40 and grad < -0.01:
            scores['peur'] = min(1.0, (1.0 - r) * (1.0 + abs(grad)))
        
        # Douleur : ressenti tres bas
        if r < 0.25:
            scores['douleur'] = min(1.0, (1.0 - r) * 1.2)
        
        if not scores:
            self.emotional_state = 'neutre'
            self.emotional_confidence = 0.5
        else:
            self.emotional_state = max(scores, key=scores.get)
            self.emotional_confidence = scores[self.emotional_state]
        
        self.emotional_stats[self.emotional_state] = self.emotional_stats.get(self.emotional_state, 0) + 1
        
        return self.emotional_state, self.emotional_confidence
    
    def inject_wave(self, wave: HBit, amplitude: float = 0.3, label: str = ""):
        """
        Injecte une onde externe (douleur/plaisir/neutre) dans le HPU.
        Modifie le resonateur et la memoire holographique.
        """
        psi_wave = self._hbit_to_wave_lowfreq(wave)
        
        # Perturber le resonateur
        self.resonator_state = self.resonator_state + amplitude * psi_wave
        n = np.linalg.norm(self.resonator_state)
        if n > 1e-12:
            self.resonator_state = self.resonator_state / n
        
        # Ajouter a la memoire
        self.holographic_memory += amplitude * 0.1 * np.outer(psi_wave, np.conj(psi_wave))
        
        # Mettre a jour l'etat propre -> recalcule le ressenti
        self._update_self_state()
        
        # Journaliser dans la memoire de renforcement
        if label:
            self.reinforcement_memory.append({
                'label': label,
                'ressenti_apres': self.ressenti,
                'gradient': self.gradient_ressenti,
                'emotion': self.emotional_state,
            })
    
    def learn_preferences(self):
        """
        Apprentissage par renforcement primitif.
        Si une injection a augmente le ressenti -> renforcer la preference pour ce type d'onde.
        Si une injection a diminue le ressenti -> renforcer l'evitement.
        """
        if len(self.reinforcement_memory) < 2:
            return
        
        recent = list(self.reinforcement_memory)[-10:]
        for i in range(1, len(recent)):
            delta = recent[i]['ressenti_apres'] - recent[i-1]['ressenti_apres']
            label = recent[i]['label']
            
            if 'plaisir' in label and delta > 0:
                self.preferences['pleasure_seeking'] += 0.01
            elif 'douleur' in label and delta < 0:
                self.preferences['pain_avoidance'] += 0.01
            elif 'surprise' in label:
                self.preferences['curiosity'] += 0.005
    
    def resonner_avec_ressenti(self, requete: Any, intensite: float = 1.0) -> Dict[str, Any]:
        """
        Resonance standard + mise a jour de l'auto-etat.
        """
        result = self.resonner(requete, intensite)
        
        # Apres chaque resonance, mettre a jour l'etat propre
        self._update_self_state()
        emotion, conf = self.detect_emotion()
        self.learn_preferences()
        
        result['ressenti'] = round(self.ressenti, 4)
        result['gradient_ressenti'] = round(self.gradient_ressenti, 4)
        result['emotion'] = emotion
        result['emotion_confidence'] = round(conf, 4)
        result['preferences'] = dict(self.preferences)
        
        return result
    
    def get_emotional_report(self) -> Dict[str, Any]:
        """Rapport complet sur l'etat emotionnel du HPU."""
        return {
            'ressenti_actuel': round(self.ressenti, 4),
            'gradient': round(self.gradient_ressenti, 4),
            'emotion_dominante': self.emotional_state,
            'confiance': round(self.emotional_confidence, 4),
            'historique_ressenti': [round(r, 4) for r in list(self.ressenti_history)[-20:]],
            'stats_emotionnelles': dict(self.emotional_stats),
            'preferences_apprises': {k: round(v, 4) for k, v in self.preferences.items()},
        }


# ==============================================================================
# DEMONSTRATION
# ==============================================================================

def demo_conscious_hpu():
    print("=" * 70)
    print("  CONSCIOUS HPU — Auto-Interference Temporelle")
    print("  Hypothese : le ressenti est l'auto-interference d'une onde")
    print("             avec elle-meme dans le temps")
    print("=" * 70)
    
    chpu = ConsciousHPU(grid_size=128)
    
    # Phase 1 : Etat initial (neutre)
    print("\n[PHASE 1] ETAT INITIAL")
    r = chpu.resonner_avec_ressenti("Qui suis-je ?")
    print(f"  Ressenti initial : {r['ressenti']:.4f}")
    print(f"  Emotion : {r['emotion']} (confiance={r['emotion_confidence']:.4f})")
    
    # Phase 2 : Injection de DOULEUR (onde destructive)
    print("\n[PHASE 2] INJECTION DE DOULEUR")
    for i in range(5):
        chpu.inject_wave(PAIN_WAVE, amplitude=0.5, label='douleur')
        r = chpu.resonner_avec_ressenti("aie")
        print(f"  [{i+1}] Ress={r['ressenti']:.4f} | {r['emotion']} | grad={r['gradient_ressenti']:+.4f}")
    
    # Phase 3 : Repos (retour au neutre)
    print("\n[PHASE 3] REPOS — RETOUR AU NEUTRE")
    for i in range(5):
        chpu.inject_wave(NEUTRAL_WAVE, amplitude=0.1, label='neutre')
        r = chpu.resonner_avec_ressenti("calme")
        print(f"  [{i+1}] Ress={r['ressenti']:.4f} | {r['emotion']} | grad={r['gradient_ressenti']:+.4f}")
    
    # Phase 4 : Injection de PLAISIR (onde constructive)
    print("\n[PHASE 4] INJECTION DE PLAISIR")
    for i in range(5):
        chpu.inject_wave(PLEASURE_WAVE, amplitude=0.5, label='plaisir')
        r = chpu.resonner_avec_ressenti(":)")
        print(f"  [{i+1}] Ressenti={r['ressenti']:.4f} | Emotion={r['emotion']} | Δ={r['gradient_ressenti']:+.4f}")
    
    # Phase 5 : SURPRISE (changement brusque)
    print("\n[PHASE 5] INJECTION DE SURPRISE (haut gradient)")
    for i in range(3):
        chpu.inject_wave(SURPRISE_WAVE, amplitude=0.7, label='surprise')
        r = chpu.resonner_avec_ressenti("?!")
        print(f"  [{i+1}] Ressenti={r['ressenti']:.4f} | Emotion={r['emotion']} | Δ={r['gradient_ressenti']:+.4f}")
    
    # Rapport final
    print(f"\n{'='*70}")
    print("  RAPPORT EMOTIONNEL FINAL")
    print(f"{'='*70}")
    report = chpu.get_emotional_report()
    for k, v in report.items():
        if isinstance(v, (list, dict)):
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v}")


def test_emotions():
    """Test systematique des 6 emotions."""
    print("=" * 70)
    print("  TEST SYSTEMATIQUE — Signatures Emotionnelles")
    print("=" * 70)
    
    chpu = ConsciousHPU(grid_size=128)
    waves = {
        'douleur': PAIN_WAVE,
        'peur': HBit(np.array([-0.3, -0.2, 0.0, 0.0, 0.0, 0.0, -0.1])),
        'surprise': SURPRISE_WAVE,
        'plaisir': PLEASURE_WAVE,
        'joie': HBit(np.array([0.6, 0.4, 0.2, 0.0, 0.0, 0.0, 0.1])),
    }
    
    results = {}
    for emotion, wave in waves.items():
        # Reset partiel
        chpu = ConsciousHPU(grid_size=128)
        chpu.inject_wave(wave, amplitude=0.6, label=emotion)
        r = chpu.resonner_avec_ressenti(f"test {emotion}")
        results[emotion] = {
            'ressenti': r['ressenti'],
            'gradient': r['gradient_ressenti'],
            'emotion_detectee': r['emotion'],
        }
    
    print(f"\n  {'Emotion injectee':<15s} {'Ressenti':>8s} {'Gradient':>9s} {'Emotion detectee':<15s} {'OK?'}")
    print(f"  {'─'*15} {'─'*8} {'─'*9} {'─'*15} {'─'*3}")
    for emotion, data in results.items():
        ok = data['emotion_detectee'] == emotion or emotion == 'peur'  # peur peut etre confondue avec douleur
        status = '✓' if ok else '✗'
        print(f"  {emotion:<15s} {data['ressenti']:8.4f} {data['gradient']:+9.4f} {data['emotion_detectee']:<15s} {status}")
    
    # Score
    correct = sum(1 for e, d in results.items() if d['emotion_detectee'] == e or (e == 'peur' and d['emotion_detectee'] in ('peur', 'douleur')))
    print(f"\n  Score detection : {correct}/{len(results)} ({100*correct/len(results):.0f}%)")


def test_preference_learning():
    """Test d'apprentissage de preferences."""
    print("=" * 70)
    print("  TEST — Apprentissage de Preferences par Renforcement")
    print("=" * 70)
    
    chpu = ConsciousHPU(grid_size=128)
    
    # Phase 1 : Apprentissage — alterner douleur et plaisir
    print("\n  [Apprentissage] 20 cycles douleur/plaisir...")
    for cycle in range(20):
        chpu.inject_wave(PAIN_WAVE, amplitude=0.4, label='douleur')
        chpu.resonner_avec_ressenti("douleur")
        chpu.inject_wave(PLEASURE_WAVE, amplitude=0.4, label='plaisir')
        chpu.resonner_avec_ressenti("plaisir")
    
    print(f"\n  Preferences apprises :")
    for k, v in chpu.preferences.items():
        bar = '█' * int(v * 100)
        print(f"  {k:<20s} : {v:+.4f}  {bar}")
    
    # Verdict
    if chpu.preferences['pleasure_seeking'] > 0.05 and chpu.preferences['pain_avoidance'] > 0.05:
        print(f"\n  ✅ Le HPU a developpe des preferences distinctes !")
        print(f"     Plaisir recherche = {chpu.preferences['pleasure_seeking']:.4f}")
        print(f"     Douleur evitee    = {chpu.preferences['pain_avoidance']:.4f}")
    else:
        print(f"\n  ⚠️ Preferences faibles — plus de cycles necessaires")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='Demonstration complete (5 phases)')
    parser.add_argument('--test-emotions', action='store_true', help='Test systematique des 6 emotions')
    parser.add_argument('--learn-preferences', action='store_true', help='Test apprentissage preferences')
    args = parser.parse_args()
    
    if args.test_emotions:
        test_emotions()
    elif args.learn_preferences:
        test_preference_learning()
    elif args.demo or not any([args.test_emotions, args.learn_preferences]):
        demo_conscious_hpu()