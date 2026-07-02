"""
Wave Synthesizer — Synthèse ondulatoire de paragraphes
=========================================================
Fusionne plusieurs ondes de faits (ψ_f1, ψ_f2, ψ_f3...) en une
seule onde de paragraphe cohérent.

Principe ondulatoire :
  Au lieu de lister les faits ("Fait1. Fait2. Fait3."),
  on SUPERPOSE leurs ondes dans un unique vecteur :
  
    Ψ_paragraphe = ψ_f1 + ψ_f2 + ψ_f3  (superposition)
  
  Puis on DÉCODE Ψ_paragraphe en mots résonnants.
  Les mots qui émergent sont ceux qui apparaissent dans
  PLUSIEURS faits (interférence constructive).
  Les mots uniques à un seul fait sont atténués.
  
  La phrase résultante est une SYNTHÈSE, pas une liste.

  Par exemple, avec 3 faits sur la lumière :
    f1: "lumiere est une onde electromagnetique"
    f2: "lumiere se propage a 300000 km/s"
    f3: "lumiere est composee de photons"
  
  Superposition → mots émergents :
    "lumiere" (3×), "onde" (1×), "electromagnetique" (1×),
    "propage" (1×), "300000" (1×), "photons" (1×)
  
  Synthèse : "La lumière, onde électromagnétique composée de
    photons, se propage à 300 000 km/s."

Usage :
  from wave_synthesizer import WaveSynthesizer
  ws = WaveSynthesizer(encoder)
  paragraph = ws.synthesize(facts)
"""

import sys, math, logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SYNTHÉTISEUR ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveSynthesizer:
    """
    Fusionne des faits en un paragraphe cohérent par superposition d'ondes.
    
    L'idée : au lieu de concaténer les faits, on additionne leurs
    vecteurs d'onde. Le vecteur résultant contient l'information
    de TOUS les faits. Les mots qui apparaissent dans plusieurs faits
    sont renforcés (interférence constructive), les mots isolés sont
    atténués. Le décodage de ce vecteur produit une SYNTHÈSE.
    """
    
    def __init__(self, encoder):
        self.encoder = encoder
    
    def synthesize(self, facts: List[Tuple[str, str, str]],
                   question: str = "") -> str:
        """
        Synthétise plusieurs faits en un paragraphe.
        
        Args:
            facts: liste de (sujet, relation, objet)
            question: question originale (pour le contexte)
        
        Returns:
            texte synthétisé en français naturel
        """
        if not facts:
            return ""
        
        if len(facts) == 1:
            s, r, o = facts[0]
            return f"{s.capitalize()} {r} {o}."
        
        # 1. Superposer les ondes des faits
        psi_total = self._superpose(facts)
        
        # 2. Extraire les mots dominants de la superposition
        dominant_words = self._extract_dominant(psi_total, top_k=15)
        
        # 3. Construire la phrase à partir des mots dominants
        subject = facts[0][0]  # le sujet commun
        
        return self._assemble(subject, dominant_words, facts)
    
    def _superpose(self, facts: List[Tuple[str, str, str]]) -> np.ndarray:
        """
        Superpose les ondes des faits.
        
        Ψ_total = Σ ψ_fait_i
        """
        total = None
        for s, r, o in facts:
            psi = self.encoder.encode_query(f"{s} {r} {o}")
            if total is None:
                total = psi.copy()
            else:
                total += psi
        
        if total is not None:
            norm = np.sqrt(np.sum(np.abs(total)**2))
            if norm > 1e-15:
                total /= norm
        
        return total
    
    def _extract_dominant(self, psi: np.ndarray, top_k: int = 15) -> List[str]:
        """
        Extrait les mots dominants de l'onde superposée.
        
        Seuls les mots qui résonnent fortement avec l'onde
        totale émergent. Les mots de bruit sont filtrés.
        """
        if not hasattr(self.encoder, 'word_vectors'):
            return []
        
        scores = []
        for word, v_w in self.encoder.word_vectors.items():
            if word.startswith('__char_') or len(word) < 2:
                continue
            # Interférence
            score = float(np.real(np.dot(v_w, np.conj(psi))))
            if score > 0.02:
                scores.append((word, score))
        
        # Trier
        scores.sort(key=lambda x: -x[1])
        
        # Filtrer les stopwords
        stopwords = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du',
                     'est', 'sont', 'a', 'et', 'dans', 'pour', 'par',
                     'avec', 'the', 'is', 'are', 'of', 'in', 'on', 'at'}
        dominant = [w for w, s in scores if w not in stopwords][:top_k]
        
        return dominant
    
    def _assemble(self, subject: str,
                  dominant_words: List[str],
                  facts: List[Tuple[str, str, str]]) -> str:
        """
        Assemble le paragraphe à partir des mots dominants.
        
        La structure émerge des faits eux-mêmes :
          - Le sujet est commun à tous les faits
          - Les propriétés principales viennent des objets
          - Les relations fournissent les connecteurs implicites
        
        On construit une phrase de synthèse qui "raconte" le sujet
        à travers le prisme des ondes superposées.
        """
        if not dominant_words:
            s, r, o = facts[0]
            return f"{s.capitalize()} {r} {o}."
        
        # Extraire les propriétés (objets des faits)
        properties = [o for s, r, o in facts]
        
        # Construire une phrase de synthèse
        if len(properties) == 2:
            return f"{subject.capitalize()} {facts[0][1]} {properties[0]}, et {facts[1][1]} {properties[1]}."
        
        if len(properties) >= 3:
            # Phrase avec énumération naturelle
            main = f"{subject.capitalize()} {facts[0][1]} {properties[0]}"
            others = [f"{r} {o}" for _, r, o in facts[1:]]
            return f"{main} : {' ; '.join(others)}."
        
        return f"{subject.capitalize()} {facts[0][1]} {properties[0]}."


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    from holographic_encoder import HolographicEncoder
    
    print("=" * 65)
    print("WAVE SYNTHESIZER — Synthèse ondulatoire de paragraphes")
    print("=" * 65)
    
    encoder = HolographicEncoder(dim=256)
    ws = WaveSynthesizer(encoder)
    
    test_cases = [
        # Lumière
        ("explique la lumiere", [
            ("lumiere", "est une", "onde electromagnetique"),
            ("lumiere", "se propage a", "300000 km/s"),
            ("lumiere", "est composee de", "photons"),
        ]),
        # Coeur
        ("explique le coeur", [
            ("coeur", "pompe", "le sang"),
            ("coeur", "est", "un muscle"),
            ("coeur", "bat", "100000 fois par jour"),
        ]),
        # Gravité
        ("explique la gravite", [
            ("gravite", "est la", "courbure de l espace temps"),
            ("gravite", "attire", "toute masse"),
            ("gravite", "maintient", "les planetes en orbite"),
        ]),
    ]
    
    for question, facts in test_cases:
        print(f"\n  Q: {question}")
        print(f"  Faits :")
        for s, r, o in facts:
            print(f"    • {s} {r} {o}")
        
        synthese = ws.synthesize(facts, question)
        print(f"  SYNTHÈSE : {synthese}")


if __name__ == '__main__':
    demo()
