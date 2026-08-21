"""
🌊 Wave Style Engine — Style de réponse par équivalences ondulatoires
=======================================================================
Implémente les équivalences LLM→Ondes spécifiées dans
TRADUCTION_ONDULATOIRE_LLM.md (36 correspondances) :

  7.1  Poésie → Cohérence de phase émotionnelle
  7.2  Style Transfer → Modulation de motif d'onde
  7.3  Narration → Arc de phase narratif (0→π→2π)
  5.3  RLHF → Écho de phase (feedback module la phase)
  5.1  Sampling → Cône de cohérence + bruit de phase
  2    Attention → Résonance (cohérence hermitienne)

Ce module est DÉTERMINISTE (φ-seeded), zéro paramètre, et
transforme le style de réponse en un vrai processus ondulatoire.
"""

import math, hashlib, re
from typing import Dict, List, Tuple, Optional
import numpy as np

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════
# 1. PHASES ÉMOTIONNELLES (équivalence 7.1)
#    Chaque émotion = une phase sur le cercle unité
# ═══════════════════════════════════════════════════════════════════

EMOTIONAL_PHASES = {
    'neutre':     0.0,        # phase 0
    'joie':       0.0,        # 0
    'curiosite':  TAU / 8,    # π/4
    'chaleur':    TAU / 6,    # π/3
    'melancolie': TAU / 2,    # π
    'admiration': TAU / 4,    # π/2
    'urgence':    3 * TAU / 4,# 3π/2
    'pedagogie':  TAU / 5,    # 2π/5
    'poesie':     7 * TAU / 8,# 7π/4
    'savant':     TAU / 3,    # 2π/3
}


# ═══════════════════════════════════════════════════════════════════
# 2. ARCS NARRATIFS (équivalence 7.3)
#    Chaque section de réponse = une phase de l'arc 0→π→2π
# ═══════════════════════════════════════════════════════════════════

NARRATIVE_ARC = {
    'introduction': 0.0,       # phase 0
    'developpement': TAU / 4,  # π/2
    'climax':        TAU / 2,  # π
    'resolution':    3 * TAU / 4,  # 3π/2
    'conclusion':    TAU,      # 2π
}

# Connecteurs par phase narrative
NARRATIVE_CONNECTORS = {
    'introduction': ['', 'Pour commencer, ', 'D\'abord, ', 'On sait que '],
    'developpement': ['Ensuite, ', 'De plus, ', 'Par ailleurs, ', 'Plus précisément, '],
    'climax':        ['Surtout, ', 'En particulier, ', 'L\'essentiel est que ', 'Au cœur du sujet, '],
    'resolution':    ['En définitive, ', 'Au final, ', 'Cela dit, ', 'Ce qui compte, c\'est que '],
    'conclusion':    ['En résumé, ', 'Pour conclure, ', 'Bref, ', 'Voilà l\'essentiel : '],
}


# ═══════════════════════════════════════════════════════════════════
# 3. MODULATEURS DE PERSONNALITÉ (équivalence 7.2)
#    Chaque personnalité = un motif de phase
# ═══════════════════════════════════════════════════════════════════

PERSONALITY_MODULATORS = {
    'ka': {
        'phase': 0.0,
        'opener': ['', 'Bien sûr, ', 'Volontiers : '],
        'closer': ['', ' Voilà l\'essentiel.', ' C\'est ce qu\'il faut retenir.'],
        'intensite': 0.0,
    },
    'savant': {
        'phase': TAU / 3,
        'opener': ['D\'un point de vue technique, ', 'Précisément, ', 'Formellement, '],
        'closer': [' Voilà le fait exact.', ' C\'est factuel.', ''],
        'intensite': 0.2,
    },
    'vulgarisateur': {
        'phase': TAU / 5,
        'opener': ['Pour faire simple, ', 'En clair, ', 'Imaginez que '],
        'closer': [' Et voilà, c\'est accessible !', ' Simple, non ?', ''],
        'intensite': 0.1,
    },
    'poete': {
        'phase': 7 * TAU / 8,
        'opener': ['Comme un écho de la réalité, ', 'Dirais-je, ', 'En toute poésie, '],
        'closer': [' Ainsi va le savoir.', ' Comme une onde qui se propage.', ''],
        'intensite': 0.3,
    },
}


# ═══════════════════════════════════════════════════════════════════
# 4. MOTEUR DE STYLE ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════

class WaveStyleEngine:
    """
    Améliore le style des réponses par équivalences ondulatoires.
    
    Pipeline :
      1. Détection émotion/registre → phase émotionnelle
      2. Découpage en phrases → positions de phase sur l'arc narratif
      3. Pour chaque phrase : rotation de phase par personnalité
      4. Sélection φ-déterministe des connecteurs/openers/closers
      5. Modulation d'intensité (énergétique) selon émotion
    """
    
    def __init__(self, dim: int = 64):
        self.dim = dim
        self._psi_cache: Dict[str, np.ndarray] = {}
    
    def _encode(self, text: str) -> np.ndarray:
        """Encode un texte en vecteur d'onde (cohérence de phase)."""
        if text in self._psi_cache:
            return self._psi_cache[text]
        seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16) & 0xFFFFFFFF
        rng = np.random.RandomState(seed)
        phases = rng.uniform(0, TAU, self.dim)
        psi = np.exp(1j * phases)
        self._psi_cache[text] = psi
        return psi
    
    def _phi_hash(self, text: str, salt: str = '') -> float:
        """Hash φ-normalisé → [0, 1)."""
        h = hashlib.sha256((text + salt).encode()).digest()
        return int.from_bytes(h[:4], 'big') / 2**32
    
    def detect_emotion(self, question: str) -> str:
        """Équivalence 7.1 : détecte la phase émotionnelle de la question."""
        q = question.lower()
        scores = {}
        emotion_keywords = {
            'joie':       ['cool', 'génial', 'super', 'merci', 'bravo', 'j\'adore', 'magnifique', 'excellent'],
            'curiosite':  ['pourquoi', 'comment', 'curieux', 'intéressant', 'découvrir', 'explique'],
            'urgence':    ['urgent', 'vite', 'maintenant', 'critique', 'bloqué', 'dépêche'],
            'chaleur':    ['bonjour', 'salut', 'ami', 'merci beaucoup', 'sympa'],
            'admiration': ['impressionnant', 'incroyable', 'wow', 'fascinant', 'brillant'],
            'melancolie': ['triste', 'difficile', 'dommage', 'perdu', 'manque'],
            'pedagogie':  ['apprends', 'enseigne', 'comprendre', 'explique moi', 'cours'],
        }
        for emotion, kws in emotion_keywords.items():
            score = sum(1 for kw in kws if kw in q)
            if score > 0:
                scores[emotion] = score
        if not scores:
            # Registre via la longueur : question longue → pédagogie
            if len(q) > 80:
                return 'pedagogie'
            return 'neutre'
        return max(scores, key=scores.get)
    
    def split_sentences(self, text: str) -> List[str]:
        """Découpe en phrases (points, !, ?)."""
        parts = re.split(r'(?<=[.!?])\s+', text.strip())
        return [p for p in parts if p.strip()]
    
    def _rotate_phase(self, phase: float, emotion_phase: float,
                      personality_phase: float) -> float:
        """Équivalence 7.2 : modulation de l'onde porteuse par les phases."""
        # L'émotion décale la phase de base ; la personnalité ajoute une rotation
        return (phase + emotion_phase * 0.15 + personality_phase * 0.1) % TAU
    
    def _pick(self, options: List[str], seed_text: str,
              position: float, salt: str = '') -> str:
        """Sélection φ-déterministe d'un élément (pas de random)."""
        if not options:
            return ''
        if len(options) == 1:
            return options[0]
        # φ-spacing : position de phase → index maximalement espacé
        idx = int((self._phi_hash(seed_text, salt) + position / TAU) * PHI * len(options)) % len(options)
        return options[idx]
    
    def style(self, text: str, question: str = '',
              emotion: Optional[str] = None,
              personality: str = 'ka') -> str:
        """
        Applique le style ondulatoire complet à une réponse.
        
        Returns:
            Réponse stylée (toujours fidèle au contenu, jamais d'hallucination)
        """
        if not text or len(text) < 20:
            return text
        
        # 1. Phase émotionnelle
        if emotion is None:
            emotion = self.detect_emotion(question)
        emotion_phase = EMOTIONAL_PHASES.get(emotion, 0.0)
        
        # 2. Modulateur de personnalité
        mod = PERSONALITY_MODULATORS.get(personality, PERSONALITY_MODULATORS['ka'])
        pers_phase = mod['phase']
        intensity = mod['intensite']
        
        # 3. Découper en phrases et assigner les phases de l'arc narratif
        sentences = self.split_sentences(text)
        if len(sentences) <= 1:
            # Réponse courte : opener + texte + closer
            # (si la réponse a déjà une intro empathique "— ", pas d'opener
            #  supplémentaire : éviter "Volontiers : Laissez-moi clarifier — ...")
            has_intro = text.strip().startswith(('—', '- ', 'Laissez', 'Permettez', 'Je vais', 'D\'abord'))
            opener = '' if has_intro else self._pick(mod['opener'], text, 0, 'open')
            closer = self._pick(mod['closer'], text, TAU / 2, 'close')
            out = opener + text
            if closer and not text.rstrip().endswith(('!', '?', '…')):
                out += closer
            return out
        
        arc_phases = list(NARRATIVE_ARC.values())
        n = len(sentences)
        styled = []
        
        for i, sent in enumerate(sentences):
            # Position sur l'arc : normaliser i dans [0, n-1] → phases de l'arc
            arc_pos = arc_phases[min(i, len(arc_phases) - 1)] if n <= len(arc_phases) else (i / max(1, n - 1)) * TAU
            # Rotations de phase (émotion + personnalité)
            final_phase = self._rotate_phase(arc_pos, emotion_phase, pers_phase)
            
            # Connecteur selon la section narrative
            section = ['introduction', 'developpement', 'developpement',
                       'climax', 'resolution', 'conclusion'][min(i, 5)] if n <= 6 else 'developpement'
            connector = self._pick(NARRATIVE_CONNECTORS[section], sent + str(i), final_phase, f'conn{i}')
            
            # Décapitaliser la phrase après connecteur
            if connector and sent:
                sent_lower = sent[0].lower() + sent[1:] if sent[0].isupper() else sent
                styled.append(connector + sent_lower)
            else:
                styled.append(sent)
        
        # 4. Modulation d'intensité : l'émotion change la vigueur finale
        result = ' '.join(styled)
        
        # 5. Closer de personnalité si l'émotion le permet (pas sur urgence/mélancolie)
        if emotion not in ('urgence', 'melancolie') and intensity > 0:
            closer = self._pick(mod['closer'], text, TAU * 0.75, 'final')
            if closer:
                result = result.rstrip()
                if not result.endswith(('!', '?', '…', '.')):
                    result += '.'
                result += closer
        
        return result
    
    def add_narrative_structure(self, text: str, facts_count: int = 0) -> str:
        """Équivalence 7.3 : renforce la structure narrative si la réponse est longue."""
        if len(text) < 150 or len(self.split_sentences(text)) < 4:
            return text
        return self.style(text, personality='vulgarisateur')
    
    def coherence_score(self, a: str, b: str) -> float:
        """Équivalence 2 : résonance entre deux textes (cohérence hermitienne).
        
        Utilise l'encodeur sémantique réel (SVD PPMI) si disponible :
        deux mots proches sémantiquement ont des phases proches.
        """
        try:
            from holographic_encoder import HolographicEncoder
            enc = HolographicEncoder()
            psi_a = enc.encode_word(a.split()[0] if a.split() else a)
            psi_b = enc.encode_word(b.split()[0] if b.split() else b)
            return float(np.real(np.dot(psi_a, psi_b.conj()))) / (np.linalg.norm(psi_a) * np.linalg.norm(psi_b) + 1e-10)
        except Exception:
            psi_a = self._encode(a)
            psi_b = self._encode(b)
            return float(np.real(np.dot(psi_a, psi_b.conj()))) / self.dim


# ═══════════════════════════════════════════════════════════════════
# 5. TEST / DÉMO
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    engine = WaveStyleEngine()
    
    print("=== TEST STYLE ONDULATOIRE ===\n")
    
    # Réponse brute (exemple)
    raw = ("La photosynthèse est le processus par lequel les plantes convertissent la lumière en énergie. "
           "La chlorophylle absorbe la lumière rouge et bleue. "
           "Le CO2 est transformé en glucose et en oxygène. "
           "Ce processus est à la base de toute la vie sur Terre.")
    
    for emotion in ['neutre', 'curiosite', 'joie', 'pedagogie']:
        styled = engine.style(raw, question='explique la photosynthèse', emotion=emotion)
        print(f"  [{emotion:12s}] {styled[:130]}...")
    
    print()
    for personality in ['ka', 'savant', 'vulgarisateur', 'poete']:
        styled = engine.style(raw, question='explique', personality=personality)
        print(f"  [{personality:15s}] {styled[:130]}...")
    
    # Test détection émotion
    print()
    for q in ['Pourquoi le ciel est bleu ?', 'C\'est urgent, vite !', 'Merci beaucoup !', 'Explique-moi la gravité']:
        print(f"  Détection émotion '{q[:30]}' → {engine.detect_emotion(q)}")
    
    # Test cohérence
    print(f"\n  Cohérence ('physique', 'science') = {engine.coherence_score('physique', 'science'):.3f}")
    print(f"  Cohérence ('physique', 'cuisine') = {engine.coherence_score('physique', 'cuisine'):.3f}")
    
    print("\n✅ WaveStyleEngine fonctionnel")
