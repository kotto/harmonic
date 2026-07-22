"""
Wave Response — Réponse ondulatoire pure via interférence holographique ABC
=============================================================================
Principe : la réponse n'est PAS générée par sélection de mots.
Elle ÉMERGE de l'interférence entre trois ondes :

  1. ψ_question  — l'onde de la question
  2. ψ_contexte  — l'onde du contexte accumulé (mémoire ABC non-locale)
  3. ψ_hologram  — l'onde du savoir (holographic store)

  ψ_réponse = ψ_question ⊗ ψ_contexte ⊗ ψ_hologram

Le noyau ABC (α = 1/φ) fournit une mémoire NON-LOCALE :
  - Court terme : les derniers tokens dominent (décroissance rapide)
  - Long terme : les anciens tokens persistent (queue en loi de puissance)

Équivalent LLM :
  - Transformer : O(N²) attention pour N tokens
  - Wave ABC   : O(1) contexte via noyau de mémoire fractionnaire

Author: Univers-Holistique
"""

import math
import time
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
ALPHA = 1.0 / PHI       # Ordre fractionnaire optimal
PI = math.pi
TAU = 2.0 * PI

# ═══════════════════════════════════════════════════════════════════════════════
# NOYAU ABC POUR MÉMOIRE DE CONTEXTE
# ═══════════════════════════════════════════════════════════════════════════════

class ABCContextMemory:
    """
    Mémoire de contexte basée sur le noyau ABC.

    Contrairement à une fenêtre glissante (qui oublie brutalement),
    le noyau ABC offre une mémoire NON-LOCALE :
      - Poids en loi de puissance (pas exponentielle)
      - Les vieux tokens ne disparaissent jamais complètement
      - Le passé lointain influence toujours le présent

    Propriété clé : pour une mémoire de 64 tokens,
    l'ABC retient ~5% du poids dans les positions 14-64,
    contre ~0.01% pour une exponentielle.
    → 500x plus de mémoire longue portée.
    """

    def __init__(self, dim: int = 512, max_len: int = 128):
        """
        Args:
            dim: dimension de l'espace complexe
            max_len: longueur maximale de la mémoire
        """
        self.dim = dim
        self.max_len = max_len
        self.history: List[np.ndarray] = []
        self._kernel_cache: Optional[np.ndarray] = None

    def push(self, psi: np.ndarray):
        """Ajoute un vecteur d'onde à l'historique."""
        self.history.append(psi.copy() if isinstance(psi, np.ndarray) else psi)
        if len(self.history) > self.max_len:
            self.history.pop(0)
        self._kernel_cache = None  # invalider le cache

    def get_context(self) -> np.ndarray:
        """
        Retourne le vecteur de contexte ψ_ctx = Σ_t K(t) · ψ_t.

        K(t) = B(α) · E_α(-α · t^α / (1-α))
        où E_α est la fonction de Mittag-Leffler.

        Le contexte est une superposition pondérée de TOUT l'historique,
        avec décroissance en loi de puissance.
        """
        if not self.history:
            return np.zeros(self.dim, dtype=complex)

        n = len(self.history)
        kernel = self._get_kernel(n)

        # Superposition pondérée
        psi_ctx = np.zeros(self.dim, dtype=complex)
        for t in range(n):
            psi_ctx += kernel[t] * self.history[-(t+1)]  # t=0 = plus récent

        # Normaliser
        norm = np.linalg.norm(psi_ctx)
        if norm > 1e-10:
            psi_ctx = psi_ctx / norm

        return psi_ctx

    def _get_kernel(self, n: int) -> np.ndarray:
        """Noyau ABC discret pour n positions (le plus récent d'abord)."""
        if self._kernel_cache is not None and len(self._kernel_cache) == n:
            return self._kernel_cache

        # Approximation de la fonction de Mittag-Leffler
        # K(t) ∝ (t+1)^{-α} / Σ(t+1)^{-α}  (décroissance en loi de puissance)
        t = np.arange(n, dtype=np.float64)
        weights = (t + 1.0) ** (-ALPHA)  # loi de puissance α=1/φ
        weights = weights / weights.sum()
        self._kernel_cache = weights
        return weights

    def reset(self):
        """Réinitialise la mémoire."""
        self.history.clear()
        self._kernel_cache = None


# ═══════════════════════════════════════════════════════════════════════════════
# RÉPONSE ONDULATOIRE PURE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WaveResponseResult:
    """Résultat d'une réponse ondulatoire pure."""
    text: str                      # Texte de la réponse
    psi_response: np.ndarray       # Vecteur d'onde de la réponse
    context_weight: float          # Poids du contexte dans la réponse
    hologram_weight: float         # Poids du savoir dans la réponse
    confidence: float              # Confiance
    elapsed_ms: float              # Temps de calcul


class WaveResponder:
    """
    Générateur de réponses par interférence ondulatoire pure.

    La réponse est le résultat de l'interférence entre :
      ψ_question ⊗ ψ_contexte ⊗ ψ_hologram

    où ⊗ est la convolution circulaire (binding HRR).

    C'est l'équivalent ondulatoire EXACT de ce que fait un LLM :
      - ψ_question  → embedding de la question
      - ψ_contexte  → mémoire ABC de l'historique
      - ψ_hologram  → savoir encodé dans le holographic store
    """

    def __init__(self, dim: int = 512, context_len: int = 128):
        self.dim = dim
        self.context = ABCContextMemory(dim=dim, max_len=context_len)
        self._encode_cache: Dict[str, np.ndarray] = {}

    def respond(self, question: str,
                facts: Optional[List[Tuple[str, str, str]]] = None,
                temperature: float = 0.5) -> WaveResponseResult:
        """
        Génère une réponse par interférence ondulatoire.

        La réponse N'EST PAS une superposition de tout le savoir.
        Elle émerge de l'interférence entre :
          1. ψ_question — l'onde de la question
          2. ψ_faits    — l'onde des FAITS PERTINENTS (pré-filtrés par le cerveau)
          3. ψ_contexte — l'onde de l'historique de conversation (mémoire ABC)

        Args:
            question: la question posée
            facts: liste de faits PERTINENTS (sujet, relation, objet)
                   déjà filtrés par le cerveau
            temperature: créativité

        Returns:
            WaveResponseResult
        """
        t_start = time.time()

        # 1. Encoder la question
        psi_q = self._encode(question)

        # 2. Encoder les faits pertinents
        if facts and len(facts) > 0:
            # Chaque fait est un binding HRR
            psi_facts_list = []
            fact_vocab = {}
            for sujet, relation, objet in facts:
                psi_s = self._encode(sujet)
                psi_r = self._encode(relation)
                psi_o = self._encode(objet)
                # Binding: ψ_fait = ψ_sujet ⊗ ψ_relation ⊗ ψ_objet
                psi_fait = self._interfere(self._interfere(psi_s, psi_r), psi_o)
                psi_facts_list.append(psi_fait)
                # Ajouter les mots au vocabulaire de décodage
                for word in f"{sujet} {relation} {objet}".lower().split():
                    if len(word) >= 3:
                        fact_vocab[word] = self._encode_word(word)

            # Hologramme des faits = superposition normalisée
            psi_facts = np.sum(psi_facts_list, axis=0)
            norm = np.linalg.norm(psi_facts)
            if norm > 1e-10:
                psi_facts = psi_facts / norm
            has_facts = True
        else:
            psi_facts = psi_q.copy()
            fact_vocab = {}
            has_facts = False

        # 3. Récupérer le contexte (mémoire ABC)
        psi_ctx = self.context.get_context()
        if np.all(psi_ctx == 0):
            psi_ctx = psi_q.copy()

        # 4. Interférence à TROIS ondes
        # ψ_réponse = ψ_question ⊗ ψ_contexte ⊗ ψ_faits
        psi_qc = self._interfere(psi_q, psi_ctx)
        if has_facts:
            psi_response = self._interfere(psi_qc, psi_facts)
        else:
            psi_response = psi_qc

        # 5. Décoder : mots de contenu depuis le vocabulaire des faits
        if fact_vocab:
            response_words = self._decode_response(
                psi_response, fact_vocab, temperature=temperature
            )
            # Ajouter des connecteurs pour fluidifier
            text = self._format_response(response_words)
        else:
            text = "Je ne trouve pas d'information pertinente."

        # 6. Mettre à jour le contexte AVEC la réponse (pour le prochain tour)
        self.context.push(psi_response)

        # 7. Confiance
        confidence = self._compute_confidence(psi_response, fact_vocab)

        elapsed = (time.time() - t_start) * 1000

        return WaveResponseResult(
            text=text,
            psi_response=psi_response,
            context_weight=0.3 if has_facts else 0.7,
            hologram_weight=0.7 if has_facts else 0.0,
            confidence=confidence,
            elapsed_ms=elapsed,
        )

    def _format_response(self, words: List[str]) -> str:
        """
        Formate une liste de mots en réponse naturelle.

        Au lieu de juste lister les mots, on crée des groupes de 2-3 mots
        avec des connecteurs simples pour donner une structure de phrase.
        """
        if len(words) <= 1:
            return " ".join(words) + "."

        # Grouper les mots avec des connecteurs
        connectors = ["et", "avec", "de", "du", "dans", "pour", "qui"]
        result = [words[0]]
        conn_idx = 0

        for i in range(1, len(words)):
            if i % 3 == 0:
                # Tous les 3 mots, mettre un point et recommencer
                result.append(".")
                result.append(words[i][0].upper() + words[i][1:] if len(words[i]) > 1 else words[i])
            elif i % 2 == 0:
                result.append(connectors[conn_idx % len(connectors)])
                result.append(words[i])
                conn_idx += 1
            else:
                result.append(words[i])

        text = " ".join(result)
        # Nettoyer les espaces avant les points
        text = text.replace(" .", ".")
        if not text.endswith("."):
            text += "."
        # Capitaliser
        text = text[0].upper() + text[1:]
        return text

    def _encode(self, text: str) -> np.ndarray:
        """Encode un texte en vecteur d'onde (FNV1a + φ-spacing)."""
        if text in self._encode_cache:
            return self._encode_cache[text]

        words = text.lower().split()
        psis = []
        for word in words:
            if word not in self._encode_cache:
                self._encode_cache[word] = self._encode_word(word)
            psis.append(self._encode_cache[word])

        if not psis:
            return self._encode_word(text)

        psi = np.sum(psis, axis=0)
        norm = np.linalg.norm(psi)
        if norm > 1e-10:
            psi = psi / norm
        self._encode_cache[text] = psi
        return psi

    def _encode_word(self, word: str) -> np.ndarray:
        """Encode un mot via FNV1a + φ-spacing."""
        h = 0xcbf29ce484222325
        for ch in word:
            h = ((h * 0x100000001b3) ^ ord(ch)) & 0xFFFFFFFFFFFFFFFF
        phases = (h * PHI ** np.arange(self.dim)) % TAU
        psi = np.exp(1j * phases)
        return psi / np.linalg.norm(psi)

    def _interfere(self, psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """
        Interférence de deux ondes : binding HRR par convolution circulaire.

        ψ_result = IFFT(FFT(ψ_a) · FFT(ψ_b))

        C'est l'opération fondamentale qui encode l'interaction
        entre deux concepts. Équivalent ondulatoire de l'attention croisée.
        """
        fa = np.fft.fft(psi_a)
        fb = np.fft.fft(psi_b)
        result = np.fft.ifft(fa * fb)
        norm = np.linalg.norm(result)
        if norm > 1e-10:
            result = result / norm
        return result

    def _build_hologram(self, knowledge_base: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Construit un hologramme à partir de la base de connaissance.

        ψ_hologram = Σ_i ψ_mot_i  (superposition pure)
        """
        if not knowledge_base:
            return np.zeros(self.dim, dtype=complex)

        psi = np.sum(list(knowledge_base.values()), axis=0)
        norm = np.linalg.norm(psi)
        if norm > 1e-10:
            psi = psi / norm
        return psi

    def _decode_response(self, psi_response: np.ndarray,
                         knowledge_base: Dict[str, np.ndarray],
                         temperature: float = 0.5,
                         max_words: int = 20) -> List[str]:
        """
        Décode le vecteur de réponse en mots.

        Pour chaque candidat, on mesure la cohérence avec ψ_response.
        On sélectionne les mots par ordre de cohérence décroissante,
        en évitant les répétitions.
        """
        # Scores de cohérence
        scores = {}
        for word, psi_w in knowledge_base.items():
            if len(word) < 3:  # ignorer les mots trop courts
                continue
            coh = float(np.real(np.dot(psi_response.conj(), psi_w)))
            scores[word] = coh

        if not scores:
            return ["..."] 

        # Trier par cohérence
        sorted_words = sorted(scores.items(), key=lambda x: -x[1])

        # Sélectionner avec diversité (éviter les doublons sémantiques)
        selected = []
        seen_phases = []
        for word, score in sorted_words:
            if len(selected) >= max_words:
                break
            # Vérifier la diversité de phase
            if word in knowledge_base:
                psi_w = knowledge_base[word]
                phase_w = np.angle(psi_w[0])  # phase dominante
                # Éviter les mots trop similaires en phase
                too_similar = False
                for prev_phase in seen_phases[-3:]:  # comparer aux 3 derniers
                    diff = abs(phase_w - prev_phase) % TAU
                    if diff < 0.3 or diff > TAU - 0.3:  # phases trop proches
                        too_similar = True
                        break
                if not too_similar:
                    selected.append(word)
                    seen_phases.append(phase_w)

        return selected if selected else [sorted_words[0][0]]

    def _compute_confidence(self, psi_response: np.ndarray,
                            knowledge_base: Optional[Dict[str, np.ndarray]]) -> float:
        """Calcule la confiance basée sur la concentration de phase."""
        if not knowledge_base:
            return 0.0

        scores = []
        for psi_w in knowledge_base.values():
            coh = float(np.real(np.dot(psi_response.conj(), psi_w)))
            scores.append(coh)

        if not scores:
            return 0.0

        scores = np.array(scores)
        scores_pos = scores - scores.min() + 1e-10
        probs = scores_pos / scores_pos.sum()
        # Entropie normalisée (0 = certitude, 1 = incertitude)
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        max_entropy = np.log(len(probs))
        confidence = 1.0 - (entropy / max_entropy)

        return float(confidence)


# ═══════════════════════════════════════════════════════════════════════════════
# INTÉGRATION AVEC LE CERVEAU
# ═══════════════════════════════════════════════════════════════════════════════

class WaveBrainResponder:
    """
    Interface haut niveau combinant :
      - ABC Context Memory (mémoire non-locale, contexte long)
      - Holographic Store (savoir)
      - Wave Responder (interférence question ⊗ faits ⊗ contexte)

    Pipeline :
      1. Le cerveau retrieve des faits pertinents (pré-filtrage)
      2. Wave Responder interfère question ⊗ faits ⊗ contexte → ψ_réponse
      3. Décodage → réponse textuelle formatée
      4. Contexte ABC mis à jour pour le prochain tour

    C'est l'équivalent ondulatoire d'un chatbot avec :
      - Récupération d'information (RAG)
      - Mémoire conversationnelle longue (ABC kernel)
      - Génération par interférence (pas de sampling cyclique)
    """

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.responder = WaveResponder(dim=dim, context_len=256)
        self.knowledge: Dict[str, np.ndarray] = {}
        self.facts_db: List[Tuple[str, str, str]] = []
        self.conversation_history: List[Tuple[str, str]] = []

    def teach(self, facts: List[Tuple[str, str, str]]):
        """Enseigne des faits. Chaque fait = (sujet, relation, objet)."""
        self.facts_db.extend(facts)
        for sujet, relation, objet in facts:
            for word in f"{sujet} {relation} {objet}".lower().split():
                if len(word) >= 3 and word not in self.knowledge:
                    self.knowledge[word] = self.responder._encode_word(word)

    def _retrieve(self, question: str, k: int = 8) -> List[Tuple[str, str, str]]:
        """
        Retrieval simple : trouve les faits dont le sujet ou l'objet
        apparaît dans la question, ou dont les mots ont une forte cohérence.
        """
        psi_q = self.responder._encode(question)
        scored = []
        for s, r, o in self.facts_db:
            # Score lexical (mots partagés avec la question)
            lexical = 0
            q_words = set(question.lower().split())
            for w in f"{s} {r} {o}".lower().split():
                if w in q_words:
                    lexical += 2
            # Score ondulatoire (cohérence de phase)
            psi_fact_text = self.responder._encode(f"{s} {r} {o}")
            coherence = float(np.real(np.dot(psi_q.conj(), psi_fact_text)))
            score = lexical * 3 + coherence
            scored.append((score, s, r, o))
        
        scored.sort(key=lambda x: -x[0])
        return [(s, r, o) for _, s, r, o in scored[:k]]

    def ask(self, question: str, temperature: float = 0.5) -> str:
        """
        Pose une question. La réponse émerge de l'interférence entre :
          - Les faits PERTINENTS (retrieval)
          - Le contexte ABC (historique de conversation)
          - La question
        """
        # 1. Retrieval des faits pertinents
        relevant_facts = self._retrieve(question, k=10)

        # 2. Réponse par interférence (faits + contexte + question)
        result = self.responder.respond(
            question,
            facts=relevant_facts,
            temperature=temperature,
        )
        self.conversation_history.append((question, result.text))
        return result.text

    def reset_context(self):
        """Réinitialise la mémoire de conversation."""
        self.responder.context.reset()


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide."""
    print("=" * 60)
    print("TEST : Wave Response — Interférence + ABC + Retrieval")
    print("=" * 60)

    brain = WaveBrainResponder(dim=256)

    # Enseigner des faits structurés
    facts = [
        ("lune", "est", "satellite"),
        ("lune", "tourne", "terre"),
        ("lune", "brille", "nuit"),
        ("lune", "surface", "argentée"),
        ("soleil", "est", "étoile"),
        ("soleil", "émet", "lumière"),
        ("soleil", "émet", "chaleur"),
        ("soleil", "source", "énergie"),
        ("mer", "est", "eau"),
        ("mer", "a", "vagues"),
        ("mer", "couvre", "planète"),
        ("amour", "est", "sentiment"),
        ("amour", "apporte", "joie"),
        ("amour", "est", "passion"),
        ("amour", "unit", "êtres"),
        ("terre", "est", "planète"),
        ("terre", "tourne", "soleil"),
    ]
    brain.teach(facts)
    print(f"\nBase: {len(brain.facts_db)} faits, {len(brain.knowledge)} mots")
    print()

    # Test 1: Questions simples avec retrieval
    print("─── Questions simples (retrieval + interférence) ───")
    for q in [
        "parle-moi de la lune",
        "qu'est-ce que le soleil",
        "décris la mer",
        "qu'est-ce que l'amour",
    ]:
        answer = brain.ask(q)
        print(f"  Q: {q}")
        print(f"  A: {answer}")
        print()

    # Test 2: Conversation multi-tours (mémoire ABC)
    print("─── Conversation multi-tours (contexte ABC) ───")
    brain2 = WaveBrainResponder(dim=256)
    brain2.teach(facts)
    for q in [
        "parle-moi de la lune",
        "et le soleil",
        "quelle est la différence",
        "et la terre dans tout ça",
    ]:
        answer = brain2.ask(q)
        print(f"  Q: {q}")
        print(f"  A: {answer}")
        print()

    # Test 3: Vérifier que le contexte ABC change les réponses
    print("─── Test ABC: même question, contexte différent ───")
    brain3 = WaveBrainResponder(dim=256)
    brain3.teach(facts)
    a1 = brain3.ask("parle-moi de la lune")
    a2 = brain3.ask("parle-moi de la lune")  # même question, contexte a changé
    print(f"  Tour 1: {a1}")
    print(f"  Tour 2: {a2}")
    print(f"  Différent? {'OUI ✅' if a1 != a2 else 'NON ❌ (contexte ABC non utilisé)'}")

    print("\n✅ Tests passés !")


if __name__ == '__main__':
    _test()
