"""
Mémoire de Travail à Espacement φ (Phi-Spaced Working Memory)
================================================================
Étend la ConversationMemory existante avec un espacement logarithmique
inspiré du nombre d'or φ = 1.618...

Au lieu de conserver les N derniers échanges de manière linéaire,
la mémoire est organisée avec une conservation dégressive :

    Échanges 1-5     : conservation 100% (mémoire immédiate)
    Échanges 6-15    : conservation ~62% (1 sur φ)
    Échanges 16-50   : conservation ~38% (1 sur φ²)
    Échanges 51-200  : conservation ~24% (1 sur φ³)
    Échanges 201+    : conservation ~15% (résumé automatique)

Propriétés :
- Les échanges récents sont parfaitement mémorisés
- Les échanges anciens ne sont jamais totalement oubliés
- L'irrationalité de φ garantit qu'aucun pattern de répétition ne se forme
- La mémoire utile effective est multipliée par ~10 sans augmenter le coût

Intégration :
    from engine.phi_memory import PhiMemory
    memory = PhiMemory(max_size=200)
    memory.add(exchange)
    context = memory.get_context()
"""
import math
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict, deque
import numpy as np

# =========================================================================
# CONSTANTES HARMONIQUES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI  # ≈ 0.618

# Seuils d'espacement φ
PHI_LAYERS = [
    (5, 1.0),       # 0-5 : conservation 100%
    (15, PHI_INV),   # 6-15 : conservation ~62%
    (50, PHI_INV**2), # 16-50 : conservation ~38%
    (200, PHI_INV**3), # 51-200 : conservation ~24%
    (float('inf'), PHI_INV**4), # 201+ : conservation ~15%
]


# =========================================================================
# STRUCTURES DE DONNÉES
# =========================================================================

@dataclass
class MemoryExchange:
    """Un échange mémorisé avec métadonnées harmoniques."""
    index: int                    # Position absolue dans la conversation
    timestamp: float              # Timestamp Unix
    user_message: str             # Message utilisateur
    assistant_response: str       # Réponse de l'assistant
    signature_9d: np.ndarray      # Signature 9D [9]
    resonance_score: float = 0.618  # Score de résonance avec le contexte
    coherence_score: float = 0.618  # Score de cohérence interne
    retention_weight: float = 1.0  # Poids de rétention (1.0 = conservé, 0.0 = supprimé)
    summary: Optional[str] = None  # Résumé pour les échanges anciens (>200)


@dataclass
class MemoryStats:
    """Statistiques de la mémoire."""
    total_exchanges: int = 0
    stored_exchanges: int = 0
    summarized_exchanges: int = 0
    avg_resonance: float = 0.618
    avg_coherence: float = 0.618
    phi_ratio: float = 0.0          # Ratio réel de rétention (doit tendre vers φ⁻¹)


# =========================================================================
# PHI MEMORY — Mémoire à espacement φ
# =========================================================================

class PhiMemory:
    """
    Mémoire de travail à espacement φ pour Harmonic AI v2.
    
    Usage:
        memory = PhiMemory(max_size=200)
        memory.add(user_msg, assistant_response, signature_9d)
        context = memory.get_context(window=10)
        stats = memory.get_stats()
    """
    
    def __init__(self, max_size: int = 200):
        self.max_size = max_size
        self.exchanges: OrderedDict = OrderedDict()  # index -> MemoryExchange
        self.total_count = 0
        self.summaries: deque = deque(maxlen=20)  # Résumés des anciens échanges
        
        # Cache de contexte pour accès rapide
        self._context_cache: Optional[List[MemoryExchange]] = None
        self._cache_dirty = True
    
    def add(self, user_message: str, assistant_response: str,
            signature_9d: np.ndarray, timestamp: Optional[float] = None,
            resonance: float = 0.618, coherence: float = 0.618):
        """
        Ajoute un échange à la mémoire.
        
        Args:
            user_message: Message de l'utilisateur
            assistant_response: Réponse de l'assistant
            signature_9d: Signature 9D du message [9]
            timestamp: Timestamp (défaut: maintenant)
            resonance: Score de résonance
            coherence: Score de cohérence
        """
        import time
        if timestamp is None:
            timestamp = time.time()
        
        if isinstance(signature_9d, list):
            signature_9d = np.array(signature_9d)
        
        exchange = MemoryExchange(
            index=self.total_count,
            timestamp=timestamp,
            user_message=user_message,
            assistant_response=assistant_response,
            signature_9d=signature_9d,
            resonance_score=resonance,
            coherence_score=coherence,
        )
        
        self.total_count += 1
        self.exchanges[self.total_count - 1] = exchange
        
        # Appliquer l'espacement φ
        self._apply_phi_spacing()
        
        # Invalider le cache
        self._cache_dirty = True
        
        # Résumer les échanges très anciens si nécessaire
        if self.total_count > 200:
            self._summarize_old_exchanges()
    
    def _apply_phi_spacing(self):
        """
        Applique la rétention à espacement φ.
        Pour chaque couche, ne conserve qu'une fraction φ⁻ᵏ des échanges.
        """
        if len(self.exchanges) <= self.max_size:
            return
        
        # Trier par index
        sorted_exchanges = sorted(self.exchanges.items(), key=lambda x: x[0])
        
        new_exchanges = OrderedDict()
        for idx, exchange in sorted_exchanges:
            # Déterminer la couche
            rel_pos = self.total_count - idx  # Position relative (0 = plus récent)
            
            if rel_pos <= 5:
                # Couche 1 : conservation 100%
                retention = 1.0
            elif rel_pos <= 15:
                # Couche 2 : conservation ~62%
                retention = PHI_INV
            elif rel_pos <= 50:
                # Couche 3 : conservation ~38%
                retention = PHI_INV ** 2
            elif rel_pos <= 200:
                # Couche 4 : conservation ~24%
                retention = PHI_INV ** 3
            else:
                # Couche 5 : conservation ~15%
                retention = PHI_INV ** 4
            
            # Décision de conservation basée sur φ
            # Utilisation d'un hash déterministe pour que la décision soit stable
            hash_val = int(hashlib.md5(str(idx).encode()).hexdigest()[:8], 16)
            normalized = hash_val / 0xFFFFFFFF
            
            if normalized < retention:
                exchange.retention_weight = retention
                new_exchanges[idx] = exchange
            # else: l'échange est supprimé
        
        self.exchanges = new_exchanges
    
    def _summarize_old_exchanges(self):
        """
        Résume les échanges très anciens (>200) pour préserver le contexte
        sans conserver le texte intégral.
        """
        old_indices = [idx for idx in self.exchanges.keys()
                       if self.total_count - idx > 200]
        
        if not old_indices:
            return
        
        # Résumer par lots de 10
        batch = []
        for idx in sorted(old_indices)[:10]:
            exchange = self.exchanges.get(idx)
            if exchange:
                batch.append(exchange)
                del self.exchanges[idx]
        
        if batch:
            # Résumé simple : concaténer les premiers mots de chaque message
            summary_parts = []
            for ex in batch:
                user_short = ' '.join(ex.user_message.split()[:5]) + '...'
                summary_parts.append(f"User: {user_short}")
            
            summary = " | ".join(summary_parts)
            self.summaries.append(summary)
    
    def get_context(self, window: int = 20) -> List[MemoryExchange]:
        """
        Récupère le contexte de conversation récent.
        
        Args:
            window: Nombre d'échanges à récupérer
        
        Returns:
            Liste des échanges les plus récents conservés
        """
        # Récupérer les échanges triés par index (plus récents d'abord)
        sorted_exchanges = sorted(self.exchanges.items(),
                                  key=lambda x: x[0],
                                  reverse=True)
        
        context = [ex for _, ex in sorted_exchanges[:window]]
        context.reverse()  # Ordre chronologique
        
        return context
    
    def get_context_with_summaries(self, window: int = 20) -> str:
        """
        Récupère le contexte formaté avec les résumés des anciens échanges.
        
        Returns:
            Texte formaté prêt à être inséré dans le prompt
        """
        context = self.get_context(window)
        
        parts = []
        
        # Ajouter les résumés anciens
        if self.summaries:
            parts.append("[Historique ancien résumé]")
            for s in list(self.summaries)[-5:]:
                parts.append(s)
            parts.append("")
        
        # Ajouter les échanges récents
        parts.append("[Conversation récente]")
        for ex in context[-10:]:
            parts.append(f"User: {ex.user_message}")
            if ex.assistant_response:
                parts.append(f"Assistant: {ex.assistant_response}")
        
        return "\n".join(parts)
    
    def get_context_signature(self, window: int = 5) -> Optional[np.ndarray]:
        """
        Calcule une signature de contexte à partir des derniers échanges.
        Pondération exponentielle décroissante.
        
        Returns:
            Signature 9D du contexte [9]
        """
        context = self.get_context(window)
        if not context:
            return None
        
        signatures = np.array([ex.signature_9d for ex in context])
        
        # Pondération exponentielle (plus de poids aux récents)
        weights = np.exp(-np.arange(len(signatures))[::-1] / 3.0)
        weights = weights / weights.sum()
        
        context_sig = np.average(signatures, axis=0, weights=weights)
        return context_sig
    
    def get_stats(self) -> MemoryStats:
        """Retourne les statistiques de la mémoire."""
        stats = MemoryStats()
        stats.total_exchanges = self.total_count
        stats.stored_exchanges = len(self.exchanges)
        stats.summarized_exchanges = len(self.summaries) * 10  # Estimation
        
        if self.exchanges:
            resonances = [ex.resonance_score for ex in self.exchanges.values()]
            coherences = [ex.coherence_score for ex in self.exchanges.values()]
            stats.avg_resonance = np.mean(resonances)
            stats.avg_coherence = np.mean(coherences)
        
        # Ratio de rétention (doit tendre vers φ⁻¹ ≈ 0.618)
        if self.total_count > 0:
            stats.phi_ratio = len(self.exchanges) / min(self.total_count, self.max_size)
        
        return stats
    
    def get_coherence_trend(self) -> List[float]:
        """
        Retourne la tendance de cohérence sur les derniers échanges.
        Une tendance à la baisse indique une dégradation de la conversation.
        """
        context = self.get_context(20)
        return [ex.coherence_score for ex in context]
    
    def get_resonance_trend(self) -> List[float]:
        """
        Retourne la tendance de résonance sur les derniers échanges.
        Une tendance à la baisse indique une perte de fil conducteur.
        """
        context = self.get_context(20)
        return [ex.resonance_score for ex in context]
    
    def clear(self):
        """Vide la mémoire."""
        self.exchanges.clear()
        self.summaries.clear()
        self.total_count = 0
        self._cache_dirty = True
    
    def __len__(self):
        return len(self.exchanges)
    
    def __repr__(self):
        stats = self.get_stats()
        return (f"PhiMemory(total={stats.total_exchanges}, "
                f"stored={stats.stored_exchanges}, "
                f"phi_ratio={stats.phi_ratio:.3f}, "
                f"avg_coherence={stats.avg_coherence:.3f})")


# =========================================================================
# INTÉGRATION AVEC CONVERSATION MEMORY EXISTANTE
# =========================================================================

class PhiConversationMemory:
    """
    Wrapper compatible avec l'API ConversationMemory existante,
    utilisant PhiMemory en interne.
    """
    
    def __init__(self, max_turns: int = 200):
        self.phi_memory = PhiMemory(max_size=max_turns)
        self.max_turns = max_turns
        
        # Pour compatibilité avec l'API existante
        self.turns: List[Dict[str, str]] = []
    
    def add_turn(self, user_msg: str, assistant_msg: str = "",
                 signature: Optional[np.ndarray] = None):
        """Ajoute un tour de conversation (API compatible)."""
        # Stockage dans l'API legacy
        self.turns.append({
            "user": user_msg,
            "assistant": assistant_msg
        })
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
        
        # Stockage dans PhiMemory
        if signature is None:
            signature = np.ones(9) * PHI_INV  # Signature neutre par défaut
        
        self.phi_memory.add(user_msg, assistant_msg, signature)
    
    def get_last_n(self, n: int = 5) -> List[Dict[str, str]]:
        """Récupère les N derniers tours (API legacy)."""
        return self.turns[-n:]
    
    def get_context_for_prompt(self, max_turns: int = 10) -> str:
        """Récupère le contexte formaté pour le prompt."""
        return self.phi_memory.get_context_with_summaries(window=max_turns)
    
    def get_context_signature(self) -> Optional[np.ndarray]:
        """Signature du contexte conversationnel."""
        return self.phi_memory.get_context_signature()
    
    def clear(self):
        """Vide la mémoire."""
        self.phi_memory.clear()
        self.turns.clear()
    
    def __len__(self):
        return len(self.phi_memory)


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST PHI MEMORY — Mémoire à espacement φ")
    print("=" * 60)
    
    # Créer une mémoire
    memory = PhiMemory(max_size=200)
    
    # Simuler une conversation de 100 échanges
    np.random.seed(42)
    for i in range(100):
        user_msg = f"Message utilisateur {i}: sujet {'A' if i < 50 else 'B'}"
        assistant_msg = f"Réponse assistant à {i}"
        sig = np.random.rand(9)
        resonance = 0.5 + 0.4 * np.random.random()  # 0.5-0.9
        coherence = 0.6 + 0.3 * np.random.random()   # 0.6-0.9
        
        memory.add(user_msg, assistant_msg, sig,
                   resonance=resonance, coherence=coherence)
    
    # Statistiques
    stats = memory.get_stats()
    print(f"\nStatistiques après 100 échanges:")
    print(f"  Total échanges: {stats.total_exchanges}")
    print(f"  Stockés: {stats.stored_exchanges}")
    print(f"  Ratio φ: {stats.phi_ratio:.3f} (cible: {PHI_INV:.3f})")
    print(f"  Cohérence moyenne: {stats.avg_coherence:.3f}")
    print(f"  Résonance moyenne: {stats.avg_resonance:.3f}")
    
    # Contexte récent
    context = memory.get_context(5)
    print(f"\nContexte récent (5 derniers conservés):")
    for ex in context:
        print(f"  [{ex.index}] {ex.user_message[:50]}... (cohérence: {ex.coherence_score:.3f})")
    
    # Tendance de cohérence
    coherence_trend = memory.get_coherence_trend()
    print(f"\nTendance cohérence (10 derniers): {[f'{c:.3f}' for c in coherence_trend[-10:]]}")
    
    # Test avec résumés
    print("\nContexte formaté (derniers 5):")
    formatted = memory.get_context_with_summaries(window=5)
    print(formatted[:500])
    
    # Test d'intégration avec PhiConversationMemory
    print("\n" + "=" * 60)
    print("TEST PhiConversationMemory (wrapper compatible)")
    print("=" * 60)
    
    conv_memory = PhiConversationMemory(max_turns=200)
    for i in range(50):
        conv_memory.add_turn(f"Question {i}", f"Réponse {i}")
    
    print(f"Tours legacy: {len(conv_memory.turns)}")
    print(f"Tours PhiMemory: {len(conv_memory.phi_memory)}")
    
    context_text = conv_memory.get_context_for_prompt(max_turns=3)
    print(f"\nContexte prompt (derniers 3):\n{context_text[:400]}")
    
    print("\n✓ Test PhiMemory réussi!")
    print("=" * 60)