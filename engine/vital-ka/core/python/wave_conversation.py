#!/usr/bin/env python3
"""
Wave Conversation — Contexte de Conversation Ondulatoire
==========================================================
La conversation EST une onde qui grandit. Chaque tour ajoute sa
vibration au contexte accumulé. Les sujets compatibles renforcent
l'interférence ; les changements de sujet créent de la décorrélation.

PRINCIPE :
  ψ_contexte = Σ tours : amplitude_i × ψ_tour_i

  L'amplitude décroît selon le noyau ABC (φ⁻ᵗ) :
    tour récent → amplitude ~1.0
    tour ancien → amplitude ~0.2

FOLLOW-UP DETECTION :
  coh = Re(⟨ψ_Q | ψ_contexte⟩)
  coh > 0.15 → FOLLOW-UP (question de suivi)
  coh < 0.05 → NOUVEAU SUJET (reset partiel)
  entre les deux → AMBIGU (utiliser le parser)

Usage :
    from wave_conversation import WaveConversation
    conv = WaveConversation(encoder, brain)
    r1 = conv.turn("Qu'est-ce que la photosynthese ?")
    r2 = conv.turn("Et ca produit quoi ?")  # follow-up détecté
    r3 = conv.turn("Combien de continents ?")  # nouveau sujet
"""

import math
import re
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass, field

PHI = 1.618033988749895
ALPHA_ABC = 1.0 / PHI  # 0.618 — ordre optimal du noyau ABC


@dataclass
class ConversationTurn:
    """Un tour de conversation."""
    role: str           # 'user' ou 'assistant'
    content: str        # texte
    subject: str        # sujet principal extrait
    coherence: float    # cohérence avec le contexte précédent
    is_followup: bool   # était-ce un follow-up ?
    timestamp: float = 0.0


class WaveConversation:
    """
    Contexte de conversation ondulatoire.

    Maintient un vecteur ψ_contexte ∈ ℂ⁵¹² qui accumule
    l'information de tous les tours, avec décroissance ABC.
    """

    # Seuils de détection (calibrés par φ)
    FOLLOWUP_THRESHOLD = 0.12   # coh > ceci → follow-up probable
    NEW_TOPIC_THRESHOLD = 0.04  # coh < ceci → nouveau sujet
    MAX_HISTORY = 50            # nombre max de tours gardés en mémoire

    # Mots qui indiquent explicitement un follow-up
    FOLLOWUP_MARKERS = {
        'et', 'donc', 'alors', 'mais', 'du coup', 'ca', 'ça', 'cela',
        'ce', 'elle', 'il', 'ils', 'on', 'le', 'la', 'les',
        'aussi', 'encore', 'sinon', 'par contre',
        'pourquoi', 'comment', 'quand', 'ou', 'où',
        'what about', 'how about', 'and', 'so', 'then', 'but',
    }

    # Mots qui indiquent explicitement un NOUVEAU sujet
    NEW_TOPIC_MARKERS = {
        'capitale', 'definis', 'qu est-ce que', "qu'est-ce que",
        'qui a', 'quelle est', 'quel est', 'combien',
        'symbole', 'formule', 'vitesse', 'masse', 'annee',
        'what is', 'who is', 'how many', 'when',
    }

    # Mots ultra-fréquents qui indiquent un follow-up même si la
    # cohérence ψ est faible — ils ne portent pas assez de sens seuls
    WEAK_KEYWORDS = {
        'ca', 'ça', 'cela', 'ce', 'cette', 'ceci',
        'il', 'elle', 'ils', 'elles', 'on',
        'et', 'donc', 'alors', 'du coup', 'aussi',
        'produit', 'fait', 'marche', 'passe', 'donne', 'sert',
        'quoi', 'comment', 'pourquoi', 'quand', 'ou', 'où',
        'plus', 'grand', 'petit', 'haut', 'bas', 'fort', 'faible',
    }

    def __init__(self, encoder, dim: int = 512):
        self.encoder = encoder
        self.dim = dim
        self.psi_context = np.zeros(dim, dtype=np.complex128)
        self.last_subject = ""
        self.last_response = ""
        self.turn_count = 0
        self.history: List[ConversationTurn] = []
        self._last_coherence = 0.0

    def _encode(self, text: str) -> np.ndarray:
        """Encode un texte en vecteur ψ."""
        if not text:
            return np.zeros(self.dim, dtype=np.complex128)
        try:
            psi = self.encoder.encode_query(text)
            if psi is None or np.all(psi == 0):
                return np.zeros(self.dim, dtype=np.complex128)
            return psi
        except Exception:
            return np.zeros(self.dim, dtype=np.complex128)

    def _normalize(self, psi: np.ndarray) -> np.ndarray:
        """Normalise un vecteur ψ."""
        norm = np.sqrt(np.sum(np.abs(psi) ** 2))
        if norm > 0:
            return psi / norm
        return psi

    def _measure_coherence(self, psi_q: np.ndarray) -> float:
        """Mesure la cohérence entre la question et le contexte."""
        if self.turn_count == 0 or np.all(self.psi_context == 0):
            return 0.0
        coh = float(np.real(np.dot(psi_q, np.conj(self.psi_context))))
        return coh

    def _is_followup_by_markers(self, question: str) -> Optional[bool]:
        """
        Détection heuristique de follow-up par marqueurs textuels.
        Retourne True (follow-up), False (nouveau sujet), ou None (incertain).
        """
        q = question.lower().strip()
        words = set(q.split())

        # Si la question contient surtout des mots faibles → follow-up forcé
        strong_words = words - self.WEAK_KEYWORDS
        if len(strong_words) <= 1 and self.turn_count > 0:
            # Ex: "et ça ?", "pourquoi ?", "et le plus grand ?"
            return True

        # Questions très courtes (1-3 mots) → probablement follow-up
        if len(q.split()) <= 3 and self.turn_count > 0:
            if words and not any(m in q for m in self.NEW_TOPIC_MARKERS):
                return True

        # Marqueurs explicites de follow-up en début de question
        for marker in self.FOLLOWUP_MARKERS:
            if q.startswith(marker + ' ') and self.turn_count > 0:
                return True

        # Marqueurs explicites de nouveau sujet
        for marker in self.NEW_TOPIC_MARKERS:
            if marker in q:
                return False

        return None

    def _detect_followup(self, question: str, psi_q: np.ndarray) -> Tuple[bool, float]:
        """
        Détecte si la question est un follow-up ou un nouveau sujet.
        Combine cohérence ondulatoire + heuristique textuelle.
        """
        # Méthode 1 : cohérence ondulatoire
        coh = self._measure_coherence(psi_q)
        self._last_coherence = coh

        # Méthode 2 : heuristique textuelle
        marker_result = self._is_followup_by_markers(question)

        # Combinaison
        if marker_result is True:
            return True, coh
        if marker_result is False:
            return False, coh

        # Si heuristique incertaine → utiliser la cohérence
        if self.turn_count == 0:
            return False, coh
        if coh > self.FOLLOWUP_THRESHOLD:
            return True, coh
        if coh < self.NEW_TOPIC_THRESHOLD:
            return False, coh

        # Zone ambiguë : préférer follow-up si le tour précédent était récent
        return self.turn_count > 0 and coh > 0.07, coh

    def _enrich_question(self, question: str) -> str:
        """
        Enrichit agressivement une question de follow-up.
        
        Le sujet DOMINE les mots de la question pour noyer le bruit.
        Ex: "et ca produit quoi" + sujet="photosynthese"
            → "photosynthese photosynthese photosynthese ca produit quoi"
        """
        if not self.last_subject:
            return question

        words = question.strip().split()
        
        # Le sujet est répété proportionnellement à la faiblesse de la question
        if len(words) <= 4:
            # Question très courte → le sujet domine massivement
            repetitions = 4  # 4× le sujet pour noyer les mots faibles
        elif len(words) <= 6:
            repetitions = 3
        else:
            repetitions = 2
        
        subject_repeated = ' '.join([self.last_subject] * repetitions)
        return f"{subject_repeated} {question}"

    def _update_context(self, psi_q: np.ndarray, psi_r: np.ndarray):
        """
        Met à jour le contexte ondulatoire avec décroissance ABC.

        ψ_contexte = ψ_contexte × decay + ψ_Q + ψ_R

        Le decay suit le noyau ABC : α^(1/n) où α = 1/φ
        Plus la conversation est longue, plus l'oubli est doux.
        """
        # Décroissance ABC : tours anciens s'affaiblissent
        n = max(self.turn_count, 1)
        decay = ALPHA_ABC ** (1.0 / n)

        # Superposition : ancien contexte × decay + nouvelle question + réponse
        self.psi_context = self.psi_context * decay + psi_q + psi_r * 0.5
        self.psi_context = self._normalize(self.psi_context)

    def turn(self, question: str, brain) -> Tuple[str, dict]:
        """
        Traite un tour de conversation complet.

        Args:
            question: texte de l'utilisateur
            brain: instance de HarmonicBrain

        Returns:
            (response, metadata) où metadata contient:
              - is_followup: bool
              - coherence: float
              - enriched: str (question enrichie si follow-up)
              - subject: str (sujet extrait)
        """
        # 1. Encoder la question
        psi_q = self._encode(question)

        # 2. Détecter follow-up
        is_followup, coherence = self._detect_followup(question, psi_q)

        # 3. Enrichir si follow-up
        if is_followup:
            enriched = self._enrich_question(question)
        else:
            enriched = question

        # 4. Processing normal via le brain
        result = brain.process(enriched)
        response = result.response

        # 5. Extraire le sujet de la réponse
        subject = ""
        if result.facts_used:
            subject = result.facts_used[0].sujet
        elif not is_followup:
            # Nouveau sujet : extraire de la question
            words = question.lower().split()
            significant = [w for w in words if len(w) >= 4
                          and w not in {'est', 'sont', 'pour', 'dans', 'avec',
                                       'mais', 'donc', 'alors', 'comment', 'pourquoi',
                                       'quelle', 'quel', 'quand', 'combien'}]
            if significant:
                subject = ' '.join(significant[:3])

        if subject:
            self.last_subject = subject
        self.last_response = response

        # 6. Mise à jour du contexte
        psi_r = self._encode(response)
        self._update_context(psi_q, psi_r)

        # 7. Enregistrer dans l'historique
        self.history.append(ConversationTurn(
            role='user', content=question,
            subject=self.last_subject,
            coherence=coherence,
            is_followup=is_followup,
        ))
        self.history.append(ConversationTurn(
            role='assistant', content=response,
            subject=self.last_subject,
            coherence=coherence,
            is_followup=is_followup,
        ))

        # Limiter l'historique
        if len(self.history) > self.MAX_HISTORY * 2:
            self.history = self.history[-self.MAX_HISTORY * 2:]

        self.turn_count += 1

        metadata = {
            'is_followup': is_followup,
            'coherence': round(coherence, 4),
            'enriched': enriched if is_followup else question,
            'subject': self.last_subject,
            'turn': self.turn_count,
        }

        return response, metadata

    def get_context_summary(self, n: int = 3) -> str:
        """Retourne un résumé textuel des n derniers tours."""
        recent = self.history[-n * 2:] if self.history else []
        if not recent:
            return "(début de conversation)"
        parts = []
        for turn in recent:
            if turn.role == 'user':
                parts.append(f"Q: {turn.content[:60]}")
            else:
                parts.append(f"R: {turn.content[:60]}")
        return ' | '.join(parts)

    def reset(self):
        """Réinitialise le contexte (nouvelle conversation)."""
        self.psi_context = np.zeros(self.dim, dtype=np.complex128)
        self.last_subject = ""
        self.last_response = ""
        self.turn_count = 0
        self.history = []
        self._last_coherence = 0.0

    def demo(self, brain):
        """Démonstration interactive de conversation multi-tours."""
        print("=" * 60)
        print("WAVE CONVERSATION — Démo Multi-Tours")
        print("=" * 60)
        print("Tapez 'quit' pour quitter, 'reset' pour nouvelle conversation\n")

        while True:
            try:
                question = input("Vous: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if question.lower() in ('quit', 'exit', 'q'):
                break
            if question.lower() == 'reset':
                self.reset()
                print("  [Contexte réinitialisé]\n")
                continue
            if not question:
                continue

            response, meta = self.turn(question, brain)

            # Afficher avec métadonnées
            fu = "↩ follow-up" if meta['is_followup'] else "★ nouveau sujet"
            print(f"  [{fu} | coh={meta['coherence']:.3f} | sujet={meta['subject'][:20]}]")
            print(f"  ULM: {response}\n")

        print("\n" + "=" * 60)
        print("Fin de conversation")
        print(f"Tours: {self.turn_count}")
        print(f"Historique: {len(self.history)} messages")


if __name__ == '__main__':
    # Démo autonome (nécessite un brain)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    from harmonic_brain import HarmonicBrain
    from harmonic_model import KNOWLEDGE_BASE

    facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in KNOWLEDGE_BASE]
    brain = HarmonicBrain(facts)

    conv = WaveConversation(brain.unconscious.encoder)
    conv.demo(brain)
