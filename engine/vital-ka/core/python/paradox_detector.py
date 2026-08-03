"""
Paradox Detector — Détection et Résolution Ondulatoire des Contradictions
==========================================================================
Détecte les contradictions dans la KB en utilisant l'interférence destructive
(produit scalaire hermitien négatif) comme signal de paradoxe.

Principe ondulatoire :
  Quand deux faits A→B et A→¬C (ou A→B et A→C où B et C sont en opposition
  de phase), leurs vecteurs d'onde interfèrent DESTRUCTIVEMENT :
  
    interférence = Re(⟨ψ_(A→B) | ψ_(A→C)⟩) 
    
  Si interférence < 0 → contradiction ondulatoire.
  
  Résolution : chercher un fait « méta » qui réconcilie les deux aspects
  (ex: « dualité onde-corpuscule » pour « la lumière est une onde » vs
  « la lumière est une particule »).

Usage :
  from paradox_detector import ParadoxDetector
  pd = ParadoxDetector(encoder, knowledge_base)
  paradoxes = pd.detect()
  resolution = pd.resolve(paradoxes[0])
"""

import sys, logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parent))

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Paradox:
    """Une contradiction détectée dans la KB."""
    sujet: str
    fait_a: Tuple[str, str, str, str]  # (sujet, relation, objet, secteur)
    fait_b: Tuple[str, str, str, str]
    interference: float                # produit scalaire hermitien (négatif = contradiction)
    severite: str                      # 'forte' | 'moyenne' | 'faible'
    resolution_naturelle: Optional[str] = None  # synthèse trouvée, ou None


# Mots d'opposition (aide à la détection lexicale en complément de l'ondulatoire)
_OPPOSITION_PAIRS = [
    ('onde', 'particule'), ('corpuscule', 'onde'),
    ('vivant', 'mort'), ('vivante', 'morte'),
    ('chaud', 'froid'), ('chaude', 'froide'),
    ('grand', 'petit'), ('grande', 'petite'),
    ('rapide', 'lent'), ('rapide', 'lente'),
    ('lumière', 'obscurité'), ('lumiere', 'obscurite'),
    ('ordre', 'chaos'), ('bien', 'mal'),
    ('vrai', 'faux'), ('vraie', 'fausse'),
    ('déterministe', 'aléatoire'), ('deterministe', 'aleatoire'),
    ('fini', 'infini'), ('finie', 'infinie'),
    ('simple', 'complexe'),
    ('création', 'destruction'), ('creation', 'destruction'),
    ('attire', 'repousse'),
    ('unité', 'diversité'), ('unite', 'diversite'),
    ('individuel', 'collectif'),
    ('nature', 'culture'),
    ('inné', 'acquis'), ('inne', 'acquis'),
]

# Mots de synthèse / résolution
_RESOLUTION_MARKERS = [
    'dualité', 'dualite', 'double nature', 'deux aspects',
    'paradoxe', 'paradoxal', 'paradoxale',
    'complémentaire', 'complementaire',
    'à la fois', 'a la fois', 'et', 'mais aussi',
    'selon le point de vue', 'selon l échelle',
    'dépend du contexte', 'depend du contexte',
    'en réalité', 'en realite', 'en fait',
    'simultanément', 'simultanement',
    'inséparable', 'inseparable',
]


# ═══════════════════════════════════════════════════════════════════════════════
# DÉTECTEUR DE PARADOXES
# ═══════════════════════════════════════════════════════════════════════════════

class ParadoxDetector:
    """
    Détecte les contradictions dans une base de connaissance
    en utilisant l'interférence ondulatoire destructive.
    """

    def __init__(self, encoder=None, knowledge_base=None):
        self._encoder = encoder
        self.kb = knowledge_base or []

    def _encode(self, text: str) -> Optional[np.ndarray]:
        if self._encoder is None:
            return None
        try:
            return self._encoder.encode_query(text)
        except Exception:
            return None

    def _interference(self, fait_a: Tuple, fait_b: Tuple) -> float:
        """
        Mesure l'interférence entre deux faits.
        
        Retourne le produit scalaire hermitien normalisé.
        Négatif = opposition de phase = contradiction ondulatoire.
        """
        s1, r1, o1, _ = fait_a
        s2, r2, o2, _ = fait_b

        text_a = f"{s1} {r1} {o1}"
        text_b = f"{s2} {r2} {o2}"

        v_a = self._encode(text_a)
        v_b = self._encode(text_b)

        if v_a is None or v_b is None:
            return 0.0

        sim = float(np.real(np.dot(v_a, np.conj(v_b))))
        D = len(v_a)
        return sim / np.sqrt(D)  # normalisé, dans [-1, 1]

    def _lexical_opposition(self, o1: str, o2: str) -> bool:
        """Détection lexicale d'opposition (complément de l'ondulatoire)."""
        o1_lower = o1.lower().strip()
        o2_lower = o2.lower().strip()
        for w1, w2 in _OPPOSITION_PAIRS:
            if (w1 in o1_lower and w2 in o2_lower) or (w2 in o1_lower and w1 in o2_lower):
                return True
        return False

    def detect(self, knowledge_base: List[Tuple] = None,
               seuil: float = -0.05) -> List[Paradox]:
        """
        Détecte tous les paradoxes dans la KB.

        Un paradoxe est détecté quand :
          - Deux faits partagent le même sujet A
          - Leurs objets B et C sont en opposition lexicale ET/OU
          - Leur interférence ondulatoire est négative (destructive)

        Args:
            knowledge_base: KB à analyser (utilise self.kb si None)
            seuil: seuil d'interférence en-dessous duquel on considère une contradiction

        Returns:
            liste de Paradox, triés par sévérité décroissante
        """
        kb = knowledge_base or self.kb
        if not kb:
            return []

        # Grouper par sujet (limiter aux sujets avec 2+ faits pour performance)
        by_subject: Dict[str, list] = {}
        for s, r, o, sec in kb:
            key = s.lower().strip()
            if key not in by_subject:
                by_subject[key] = []
            by_subject[key].append((s, r, o, sec))
        
        # Ne garder que les sujets avec 2+ faits (optimisation O(n²) → O(k²·m))
        by_subject = {k: v for k, v in by_subject.items() if len(v) >= 2 and len(v) <= 20}

        paradoxes = []
        seen_pairs = set()

        for sujet, facts in by_subject.items():
            if len(facts) < 2:
                continue

            for i in range(len(facts)):
                for j in range(i + 1, len(facts)):
                    f_a = facts[i]
                    f_b = facts[j]

                    o1 = f_a[2].lower().strip()
                    o2 = f_b[2].lower().strip()

                    pair_key = (sujet, min(o1, o2), max(o1, o2))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    # Détection lexicale
                    lex_opp = self._lexical_opposition(o1, o2)

                    # Détection ondulatoire
                    interf = self._interference(f_a, f_b)

                    # Un paradoxe est détecté si :
                    # - interférence franchement négative (< seuil) OU
                    # - opposition lexicale ET interférence < 0
                    if interf < seuil or (lex_opp and interf < 0.01):
                        severite = 'forte' if interf < -0.1 else ('moyenne' if interf < 0 else 'faible')
                        paradoxes.append(Paradox(
                            sujet=sujet,
                            fait_a=f_a,
                            fait_b=f_b,
                            interference=interf,
                            severite=severite,
                        ))

        paradoxes.sort(key=lambda p: p.interference)  # plus négatif = plus paradoxal
        return paradoxes

    def resolve(self, paradox: Paradox,
                knowledge_base: List[Tuple] = None) -> str:
        """
        Tente de résoudre un paradoxe en cherchant un fait « méta »
        qui réconcilie les deux aspects contradictoires.

        Stratégie :
          1. Chercher un fait dans la KB dont le sujet est le même
             et dont l'objet contient un marqueur de synthèse (dualité, etc.)
          2. Si trouvé → utiliser ce fait comme résolution
          3. Sinon → générer une synthèse à partir des deux faits

        Returns:
            texte de résolution en langage naturel
        """
        kb = knowledge_base or self.kb

        s = paradox.sujet
        o1 = paradox.fait_a[2]
        o2 = paradox.fait_b[2]

        # 1. Chercher un fait « méta » de résolution
        for sbj, rel, obj, sec in kb:
            if sbj.lower().strip() == s:
                obj_lower = obj.lower()
                if any(marker in obj_lower for marker in _RESOLUTION_MARKERS):
                    return (f"Ce paradoxe n'est qu'apparent. En réalité, {s} {rel} {obj}. "
                            f"Les deux aspects — {o1} et {o2} — sont complémentaires "
                            f"et coexistent dans une même réalité.")

        # 2. Chercher un fait qui mentionne les deux objets
        for sbj, rel, obj, sec in kb:
            obj_lower = obj.lower()
            o1_lower = o1.lower()
            o2_lower = o2.lower()
            if o1_lower in obj_lower and o2_lower in obj_lower:
                return (f"La contradiction entre « {o1} » et « {o2} » se résout "
                        f"ainsi : {s} {rel} {obj}.")

        # 3. Synthèse générique
        if paradox.severite == 'faible':
            return (f"Il n'y a pas de véritable contradiction ici. {s.capitalize()} "
                    f"peut être à la fois décrit comme {o1} et comme {o2}, "
                    f"selon l'angle ou l'échelle considérée.")

        return (f"{s.capitalize()} présente deux aspects qui semblent contradictoires : "
                f"{o1} et {o2}. Ces deux descriptions peuvent coexister : "
                f"elles reflètent probablement des facettes différentes "
                f"d'une même réalité complexe.")

    def analyze_and_report(self, knowledge_base: List[Tuple] = None) -> str:
        """
        Analyse complète de la KB : détecte les paradoxes et produit
        un rapport de synthèse en langage naturel.

        Returns:
            rapport textuel
        """
        kb = knowledge_base or self.kb
        paradoxes = self.detect(kb)

        if not paradoxes:
            return ("✅ Aucune contradiction ondulatoire détectée dans "
                    "la base de connaissance. Les faits sont en cohérence de phase.")

        report = [f"🔍 {len(paradoxes)} paradoxe(s) détecté(s) :"]

        for i, p in enumerate(paradoxes[:5], 1):
            resolution = self.resolve(p, kb)
            report.append(
                f"\n{i}. **{p.sujet.capitalize()}** "
                f"(interférence={p.interference:.3f}, sévérité={p.severite})\n"
                f"   → « {p.fait_a[2]} » vs « {p.fait_b[2]} »\n"
                f"   💡 {resolution}"
            )

        return '\n'.join(report)


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    from holographic_encoder import HolographicEncoder

    print("=" * 60)
    print("PARADOX DETECTOR — Démo")
    print("=" * 60)

    # KB avec contradictions volontaires
    kb = [
        ("lumiere", "est une", "onde", "PHYSIQUE_FOND"),
        ("lumiere", "est une", "particule", "PHYSIQUE_FOND"),
        ("lumiere", "possede une", "dualite onde-corpuscule", "PHYSIQUE_FOND"),
        ("univers", "est", "fini", "COSMOLOGIE"),
        ("univers", "est", "infini", "COSMOLOGIE"),
        ("temps", "est", "lineaire", "PHYSIQUE_FOND"),
        ("temps", "est", "cyclique", "PHILOSOPHIE"),
        ("homme", "est", "bon par nature", "PHILOSOPHIE"),
        ("homme", "est", "egoiste par nature", "PHILOSOPHIE"),
        ("electron", "est une", "particule", "PHYSIQUE_FOND"),
        ("electron", "est une", "onde", "PHYSIQUE_FOND"),
    ]

    encoder = HolographicEncoder(dim=128)

    pd = ParadoxDetector(encoder, kb)

    paradoxes = pd.detect()
    print(f"\nParadoxes détectés : {len(paradoxes)}")
    for p in paradoxes:
        resolution = pd.resolve(p)
        print(f"\n  ⚡ {p.sujet} (sévérité={p.severite}, interf={p.interference:.3f})")
        print(f"     {p.fait_a[2]}  ↔  {p.fait_b[2]}")
        print(f"     💡 {resolution[:150]}...")

    # Rapport complet
    print("\n" + "=" * 60)
    print(pd.analyze_and_report())


if __name__ == '__main__':
    demo()
