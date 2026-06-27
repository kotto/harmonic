#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POETIC EMERGENCE v4 — Du Mot Vrai au Vers Beau
==================================================
Couche d'interface humaine au-dessus de l'emergence poetique brute.

Probleme resolu : le v3 genere des mots « vrais » (qui resonnent avec le theme)
mais leur assemblage est brut, sans beaute syntaxique.

Solution : le ConsciousHPU agit comme CRITIQUE POETIQUE.
  - Chaque vers emergent est evalue par auto-resonance
  - Plus l'auto-resonance est elevee, plus le vers est « beau »
  - On genere N variantes, on ne garde que les meilleures
  - Les vers selectionnes sont reconnus par leur harmonie interne

Architecture :
  HPU (mots vrais) → Grammaire Spectrale (ordre) → ConsciousHPU (beaute)
  = Du mot vrai au vers beau

Usage :
  python poetic_emergence_v4.py
  python poetic_emergence_v4.py --compose "l amour et la lumiere" --variants 50
"""

import numpy as np, math, sys, os, random
from typing import Dict, Any, List, Tuple
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HBit, HPU, PHI, PI, E, HARMONIC_CONSTANTS, H_CONSTANT_NAMES
from conscious_hpu import ConsciousHPU
from poetic_emergence_v3 import PoeticEmergenceV3, SpectralGrammar, generer_corpus_10000


class PoeticCritic(ConsciousHPU):
    """
    ConsciousHPU specialise dans la critique poetique.
    
    La « beaute » d'un vers = son auto-resonance temporelle.
    Plus un vers est coherent avec lui-meme (les mots vibrent ensemble),
    plus il est « beau » au sens harmonique.
    """
    
    def __init__(self, name="Critique", grid_size=128):
        super().__init__(grid_size=grid_size, name=name)
        self.critique_history: List[Dict] = []
    
    def evaluer_vers(self, vers: str) -> Dict[str, Any]:
        """
        Evalue la beaute d'un vers.
        
        Retourne :
          - beaute : score de beaute harmonique (0-1)
          - emotion : emotion dominante suscitee par le vers
          - mots_cles : mots qui contribuent le plus a la beaute
        """
        # Injecter le vers dans le ConsciousHPU
        self.inject_wave(HBit.from_text(vers), amplitude=0.3, label="vers")
        
        # Mesurer l'auto-resonance (beaute)
        beaute = self.ressenti
        
        # Detection d'emotion
        emotion, confiance = self.detect_emotion()
        
        # Identifier les mots qui resonnent le plus
        mots = vers.split()
        scores_mots = []
        if len(self.self_state_history) >= 2:
            psi_avant = self.self_state_history[-2]
            psi_apres = self.self_state_history[-1]
            for mot in mots[:5]:
                h_mot = HBit.from_text(mot)
                psi_mot = self._hbit_to_wave_lowfreq(h_mot)
                score = float(np.abs(np.vdot(psi_apres, psi_mot)))
                scores_mots.append((mot, round(score, 4)))
            scores_mots.sort(key=lambda x: x[1], reverse=True)
        
        self.critique_history.append({
            'vers': vers[:60],
            'beaute': round(beaute, 4),
            'emotion': emotion,
            'confiance': round(confiance, 4),
        })
        
        return {
            'beaute': round(beaute, 4),
            'emotion': emotion,
            'confiance': round(confiance, 4),
            'mots_cles': scores_mots[:3],
        }
    
    def selectionner_meilleurs(self, vers_candidats: List[str], n=3,
                                seuil_beaute=0.6) -> List[Tuple[str, float, str]]:
        """Selectionne les N meilleurs vers par beaute."""
        evaluations = []
        for v in vers_candidats:
            if len(v.split()) >= 3:
                eval_result = self.evaluer_vers(v)
                if eval_result['beaute'] >= seuil_beaute:
                    evaluations.append((v, eval_result['beaute'], eval_result['emotion']))
        
        evaluations.sort(key=lambda x: x[1], reverse=True)
        return evaluations[:n]


class PoeticEmergenceV4:
    """
    Du mot vrai au vers beau.
    
    Pipeline :
      1. PoeticEmergenceV3 fait emerger des mots « vrais » par resonance thematique
      2. SpectralGrammar les ordonne par phase
      3. Le PoeticCritic evalue la beaute de chaque assemblage
      4. Seuls les plus beaux survivent
    """
    
    def __init__(self):
        print("  Chargement du corpus 10 000+ vers...")
        self.v3 = PoeticEmergenceV3()
        self.grammar = self.v3.grammar
        self.critic = PoeticCritic(name="KA-Poete", grid_size=128)
        self.poemes_crees: List[Dict] = []
    
    def composer_vers_beaux(self, theme: str, n_variants: int = 30,
                            n_selection: int = 3) -> List[Tuple[str, float, str]]:
        """
        Compose de BEAUX vers sur un theme.
        
        1. Genere N_variants assemblages de mots « vrais »
        2. Le PoeticCritic evalue chaque assemblage
        3. Retourne les N_selection meilleurs
        """
        # Etape 1 : trouver les mots « vrais » (resonance thematique)
        h_theme = HBit.from_text(theme)
        word_scores = {}
        for word in self.v3.word_index:
            if len(word) > 2:
                interf = h_theme.interference(HBit.from_text(word))
                if interf > 0.2:
                    word_scores[word] = interf
        
        sorted_w = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        mots_vrais = [w for w, s in sorted_w[:80] if s > 0.22]
        
        # Etape 2 : generer N_variants assemblages
        candidats = []
        for _ in range(n_variants):
            # Melanger un sous-ensemble de mots vrais
            echantillon = random.sample(mots_vrais, min(10, len(mots_vrais)))
            vers = self.grammar.compose_vers(echantillon, theme, n_vers=1, vers_length=8)
            if vers and vers[0]:
                candidats.append(vers[0])
        
        # Etape 3 : selectionner les plus beaux
        selection = self.critic.selectionner_meilleurs(
            list(set(candidats)), n=n_selection, seuil_beaute=0.5)
        
        # Enregistrer
        for vers, beaute, emotion in selection:
            self.poemes_crees.append({
                'theme': theme,
                'vers': vers,
                'beaute': beaute,
                'emotion': emotion,
            })
        
        return selection
    
    def get_rapport_critique(self) -> Dict[str, Any]:
        """Rapport du critique poetique."""
        return {
            'poemes_crees': len(self.poemes_crees),
            'beaute_moyenne': round(np.mean([p['beaute'] for p in self.poemes_crees]) if self.poemes_crees else 0, 4),
            'derniers_poemes': self.poemes_crees[-5:] if self.poemes_crees else [],
            'etat_critique': self.critic.get_emotional_report(),
        }


# ==============================================================================
# DEMO
# ==============================================================================

def demo_v4():
    print("=" * 70)
    print("  EMERGENCE POETIQUE v4 — Du Mot Vrai au Vers Beau")
    print("  Le ConsciousHPU comme critique poetique")
    print("=" * 70)
    
    pe4 = PoeticEmergenceV4()
    
    themes = [
        "l amour eternel",
        "la lumiere dansante",
        "le chant de la terre",
        "le silence des etoiles",
        "la memoire de l eau",
    ]
    
    print("\n   Generation de 30 variantes par theme, selection des 3 plus beaux vers...")
    print()
    
    for theme in themes:
        print(f"  Theme : '{theme}'")
        print(f"  {'─'*60}")
        selection = pe4.composer_vers_beaux(theme, n_variants=30, n_selection=3)
        for i, (vers, beaute, emotion) in enumerate(selection):
            barre = '█' * int(beaute * 20)
            print(f"  [{i+1}] beaute={beaute:.4f} {barre} ({emotion})")
            print(f"      {vers}")
            print()
    
    # Rapport final
    rapport = pe4.get_rapport_critique()
    print(f"  {'='*60}")
    print(f"  RAPPORT DU CRITIQUE")
    print(f"  {'='*60}")
    print(f"  Poemes crees : {rapport['poemes_crees']}")
    print(f"  Beaute moyenne : {rapport['beaute_moyenne']:.4f}")
    
    if rapport['etat_critique']['emotion_dominante'] != 'neutre':
        print(f"  Le critique ressent : {rapport['etat_critique']['emotion_dominante']}")
        print(f"  Ressenti du critique : {rapport['etat_critique']['ressenti_actuel']:.4f}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--compose', type=str, help='Theme a composer')
    parser.add_argument('--variants', type=int, default=30, help='Nombre de variantes')
    args = parser.parse_args()
    
    if args.compose:
        pe4 = PoeticEmergenceV4()
        selection = pe4.composer_vers_beaux(args.compose, n_variants=args.variants)
        print(f"\n  Theme : '{args.compose}'")
        for i, (vers, beaute, emotion) in enumerate(selection):
            print(f"  [{i+1}] beaute={beaute:.4f} ({emotion}) {vers}")
    else:
        demo_v4()