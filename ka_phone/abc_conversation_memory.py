#!/usr/bin/env python3
"""
ABC CONVERSATION MEMORY — Mémoire conversationnelle à dérivée fractionnaire
=============================================================================
Applique le noyau ABC (Atangana-Baleanu-Caputo) à la mémoire conversationnelle
pour une pondération temporelle non-locale du contexte.

Contrairement à un buffer glissant classique (FIFO, N derniers tours),
la mémoire ABC donne un poids à CHAQUE tour de la conversation, avec
une décroissance contrôlée par l'ordre fractionnaire α.

Propriétés clés :
  - α = 0 : mémoire parfaite (tous les tours ont le même poids)
  - α = 0.5 : mémoire "normale" (décroissance modérée)
  - α = 1.0 : mémoire classique (seul le dernier tour compte)
  - 0 < α < 1 : mémoire non-locale (le passé lointain compte encore un peu)

Formule ABC pour le poids du tour k parmi N tours :
  w(k) = E_α(-α * (N - k)^α / (1-α))
  où E_α est la fonction de Mittag-Leffler

Intégration avec ConversationOrchestrator :
  → Remplace le simple "last_subject" par un "weighted_context"
  → Pour "Et sa population ?", le contexte n'est pas juste le dernier sujet,
    mais une combinaison pondérée de TOUS les sujets précédents
  → Les changements de topic sont plus fluides car le passé persiste

Usage :
  from abc_conversation_memory import ABCConversationMemory
  mem = ABCConversationMemory(alpha=0.7)
  mem.add_turn("Quelle est la capitale du Senegal ?", "Dakar", {"topic": "geography"})
  mem.add_turn("Et sa population ?", "18 millions", {"topic": "geography"})
  context = mem.get_weighted_context()
  # → Poids: [tour1: 0.15, tour2: 0.85], topic dominant: geography
"""

import math, time, json
from typing import List, Dict, Tuple, Optional, Any
from collections import deque
import numpy as np

# ══════════════════════════════════════════════════════════════════════════
# MITTAG-LEFFLER FUNCTION (approximation)
# ══════════════════════════════════════════════════════════════════════════

def mittag_leffler(alpha: float, z: float, terms: int = 50) -> float:
    """
    Fonction de Mittag-Leffler : E_α(z) = Σ_{k=0}^∞ z^k / Γ(αk + 1)
    Utilisée comme noyau de la dérivée ABC.
    
    Pour z négatif (décroissance), convergence rapide.
    """
    if z == 0:
        return 1.0
    
    result = 0.0
    for k in range(terms):
        try:
            term = z**k / math.gamma(alpha * k + 1)
            result += term
            if abs(term) < 1e-15:
                break
        except OverflowError:
            break
    return result


def abc_weight(position: int, total_turns: int, alpha: float = 0.7) -> float:
    """
    Calcule le poids ABC d'un tour de conversation.
    
    Args:
        position: index du tour (0 = le plus ancien)
        total_turns: nombre total de tours
        alpha: ordre fractionnaire (0 < α < 1)
               α → 0 : mémoire parfaite
               α → 1 : mémoire instantanée (seul le dernier compte)
    
    Returns:
        Poids entre 0 et 1
    
    Formule :
        w(k) = E_α( -α * (N-1-k)^α / (1-α) )
        où k est la position (0 = plus ancien, N-1 = plus récent)
    """
    if total_turns <= 1:
        return 1.0
    
    # Distance depuis le présent (le tour le plus récent a distance=0)
    distance_from_present = total_turns - 1 - position
    
    # Argument pour Mittag-Leffler
    if alpha >= 0.999:
        # α ≈ 1 : seul le dernier tour compte (mémoire classique)
        return 1.0 if position == total_turns - 1 else 0.0
    
    if alpha <= 0.001:
        # α ≈ 0 : tous les tours comptent également
        return 1.0
    
    # z = -α * t^α / (1-α)  où t est la distance au présent
    t = max(distance_from_present, 0.1)  # Éviter t=0
    z = -alpha * (t ** alpha) / (1.0 - alpha)
    
    return mittag_leffler(alpha, z)


# ══════════════════════════════════════════════════════════════════════════
# ABC CONVERSATION MEMORY
# ══════════════════════════════════════════════════════════════════════════

class ABCConversationMemory:
    """
    Mémoire conversationnelle avec pondération temporelle ABC.
    
    Contrairement à ConversationOrchestrator qui ne garde que le "last_subject",
    cette mémoire pondère TOUS les tours précédents pour construire
    un contexte riche et nuancé.
    """

    def __init__(self, alpha: float = 0.7, max_turns: int = 100):
        """
        Args:
            alpha: ordre fractionnaire (0 < α < 1)
                   0.3 = très longue mémoire (conversation profonde)
                   0.5 = mémoire équilibrée
                   0.7 = mémoire standard (défaut)
                   0.9 = mémoire courte (réponses rapides)
            max_turns: nombre maximum de tours conservés
        """
        self.alpha = max(0.01, min(0.99, alpha))
        self.max_turns = max_turns
        self.turns = deque(maxlen=max_turns)
        self.stats = {"total_turns": 0, "avg_weight_decay": 0.0}

    def add_turn(self, prompt: str, response: str = "", 
                 metadata: Dict = None) -> int:
        """
        Ajoute un tour à la mémoire.
        
        Returns:
            Nombre total de tours
        """
        self.turns.append({
            "prompt": prompt[:300],
            "response": response[:300],
            "metadata": metadata or {},
            "timestamp": time.time(),
            "turn_id": self.stats["total_turns"],
        })
        self.stats["total_turns"] += 1
        return len(self.turns)

    def get_weighted_context(self, top_k: int = 5) -> Dict:
        """
        Construit un contexte pondéré par ABC à partir de toute l'historique.
        
        Returns:
            Dict avec :
              - "dominant_subject": le sujet le plus probablement pertinent
              - "dominant_topic": le topic dominant
              - "context_string": résumé injectable dans le prompt
              - "weights": poids de chaque tour
              - "relevance_decay": courbe de décroissance
        """
        if not self.turns:
            return {
                "dominant_subject": None,
                "dominant_topic": None,
                "context_string": "",
                "weights": [],
            }

        n = len(self.turns)
        weights = [abc_weight(i, n, self.alpha) for i in range(n)]
        
        # Normaliser
        total_w = sum(weights)
        if total_w > 0:
            weights = [w / total_w for w in weights]

        # Extraire les sujets pondérés
        subject_weights = {}
        topic_weights = {}
        
        for i, turn in enumerate(self.turns):
            w = weights[i]
            meta = turn.get("metadata", {})
            
            # Sujet
            subject = meta.get("subject") or self._extract_subject(turn["prompt"])
            if subject:
                subject_weights[subject] = subject_weights.get(subject, 0) + w
            
            # Topic
            topic = meta.get("topic") or meta.get("domain")
            if topic:
                topic_weights[topic] = topic_weights.get(topic, 0) + w

        # Sujet dominant (celui avec le poids cumulé le plus élevé)
        dominant_subject = max(subject_weights, key=subject_weights.get) if subject_weights else None
        dominant_topic = max(topic_weights, key=topic_weights.get) if topic_weights else None

        # Construire un résumé contextuel
        context_parts = []
        recent_turns = list(self.turns)[-top_k:]
        recent_weights = weights[-top_k:] if len(weights) >= top_k else weights
        
        for i, (turn, w) in enumerate(zip(recent_turns, recent_weights)):
            if w > 0.01:  # Ignorer les tours quasi-invisibles
                prompt_short = turn["prompt"][:80]
                response_short = turn.get("response", "")[:80]
                if response_short:
                    context_parts.append(f"[{w:.0%}] Q: {prompt_short} → {response_short}")
                else:
                    context_parts.append(f"[{w:.0%}] Q: {prompt_short}")

        context_string = " | ".join(context_parts) if context_parts else ""

        # Décroissance de pertinence (pour debug/analyse)
        decay = [(i, round(weights[i], 4)) for i in range(max(0, n-10), n)]

        return {
            "dominant_subject": dominant_subject,
            "dominant_topic": dominant_topic,
            "context_string": context_string[:500],
            "weights": [round(w, 4) for w in weights],
            "relevance_decay": decay,
            "subject_distribution": {k: round(v, 3) for k, v in 
                                    sorted(subject_weights.items(), key=lambda x: -x[1])[:5]},
            "memory_depth": n,
            "alpha": self.alpha,
        }

    def get_last_n_weighted(self, n: int = 3) -> List[Dict]:
        """Retourne les n derniers tours avec leurs poids ABC."""
        if not self.turns:
            return []
        
        total = len(self.turns)
        result = []
        for i in range(max(0, total - n), total):
            turn = dict(self.turns[i])
            turn["abc_weight"] = round(abc_weight(i, total, self.alpha), 4)
            result.append(turn)
        return result

    def _extract_subject(self, text: str) -> Optional[str]:
        """Extrait le sujet principal d'un prompt."""
        import re
        # Nettoyer
        clean = re.sub(r'^(?:et\s+)?(?:quelle|quel|comment|pourquoi|quand|combien|qui|que|quoi)\s+', '', text, flags=re.IGNORECASE)
        clean = re.sub(r'^(?:dis-moi|parle-moi|raconte-moi)\s+(?:de |du |des? )?', '', clean, flags=re.IGNORECASE)
        clean = clean.strip().rstrip("?!.,;: ")
        if clean and len(clean) > 2:
            words = clean.split()[:5]
            stop = {'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'et', 'ou', 'a', 'au', 'en', 'dans', 'sur', 'pour', 'avec', 'sans', 'pas'}
            meaningful = [w for w in words if w.lower() not in stop]
            return ' '.join(meaningful) if meaningful else None
        return None

    def get_memory_stats(self) -> Dict:
        """Statistiques de la mémoire."""
        n = len(self.turns)
        weights = [abc_weight(i, n, self.alpha) for i in range(n)] if n > 0 else []
        return {
            "total_turns": self.stats["total_turns"],
            "active_turns": n,
            "alpha": self.alpha,
            "memory_horizon": n,  # Nombre de tours avant poids < 1%
            "weight_distribution": {
                "most_recent": round(weights[-1], 4) if weights else 0,
                "median": round(sorted(weights)[len(weights)//2], 4) if weights else 0,
                "oldest": round(weights[0], 4) if weights else 0,
            },
            "effective_depth": sum(1 for w in weights if w > 0.01) if weights else 0,
        }

    def reset(self):
        """Vide la mémoire."""
        self.turns.clear()
        self.stats = {"total_turns": 0, "avg_weight_decay": 0.0}


# ══════════════════════════════════════════════════════════════════════════
# DEMO
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("ABC CONVERSATION MEMORY — Démonstration de mémoire fractionnaire")
    print("=" * 70)

    # Comparer différents α
    for alpha in [0.3, 0.5, 0.7, 0.9]:
        mem = ABCConversationMemory(alpha=alpha)
        
        # Simuler 10 tours de conversation
        conversation = [
            ("Bonjour !", "Bonjour ! Que puis-je faire pour toi ?"),
            ("Quelle est la capitale du Senegal ?", "La capitale du Senegal est Dakar."),
            ("Et sa population ?", "La population du Senegal est d'environ 18 millions."),
            ("Parle-moi de la musique africaine", "La musique africaine est incroyablement diverse..."),
            ("Quels instruments traditionnels ?", "Le kora, le balafon, le djembé..."),
            ("Et le djembé, c'est quoi ?", "Le djembé est un tambour originaire d'Afrique de l'Ouest..."),
            ("Comment on en joue ?", "On joue du djembé avec les mains, en frappant le centre pour les basses..."),
            ("Qui sont les grands joueurs ?", "Mamady Keïta, Famoudou Konaté..."),
            ("Et la kora ?", "La kora est une harpe-luth à 21 cordes..."),
            ("Merci pour toutes ces infos !", "Avec plaisir ! Reviens quand tu veux."),
        ]
        
        for prompt, response in conversation:
            mem.add_turn(prompt, response, {"topic": "culture" if "musique" in prompt or "instrument" in prompt or "djembé" in prompt or "kora" in prompt else "geography"})
        
        ctx = mem.get_weighted_context()
        stats = mem.get_memory_stats()
        
        print(f"\nα = {alpha}")
        print(f"  Profondeur effective: {stats['effective_depth']}/{stats['active_turns']} tours")
        print(f"  Distribution: récent={stats['weight_distribution']['most_recent']:.3f}, "
              f"médian={stats['weight_distribution']['median']:.3f}, "
              f"ancien={stats['weight_distribution']['oldest']:.3f}")
        print(f"  Sujet dominant: {ctx['dominant_subject']}")
        print(f"  Topic dominant: {ctx['dominant_topic']}")
        print(f"  Top sujets: {ctx['subject_distribution']}")

    print(f"\n" + "=" * 70)
    print("Exemple de contexte pondéré (α=0.5, 5 derniers tours):")
    mem = ABCConversationMemory(alpha=0.5)
    for prompt, response in conversation:
        mem.add_turn(prompt, response)
    ctx = mem.get_weighted_context(top_k=5)
    print(ctx["context_string"][:400])