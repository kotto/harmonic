#!/usr/bin/env python3
r"""
KA-Next — PONT UNIFIÉ ONDE↔LANGAGE (Interface Univers↔Humain)
================================================================
Implémente l'interface entre le langage ondulatoire de l'univers
(φ, fréquences, interférences) et le langage humain (mots, sens, émotions).

Inspiré de THEORIE_UNIFIEE_HARMONIQUE.md — Piliers ABC et GAGUT.

TROIS MODULES :
  1. ABC_SESSION : Mémoire de session par dérivée fractionnaire
     → Chaque échange laisse une trace qui décroît en Mittag-Leffler
     → Jamais d'oubli total (contrairement à exponentielle classique)
  
  2. WAVE_LANGUAGE : Ponte onde↔langage
     → Chaque mot → fréquence φ
     → Chaque phrase → superposition d'ondes
     → Chaque émotion → phase dans l'espace harmonique
  
  3. GAGUT_PIPELINE : Calcul arithmétique ondulatoire intégré
     → +, −, ×, / exacts via log_phi
     → a^n, √N via Newton dans l'espace φ

USAGE :
  from wave_unified_bridge import ABCSessionMemory, WaveLanguageBridge, GAGUTPipeline
"""

import math, time, hashlib
from typing import List, Dict, Tuple, Optional
import numpy as np

PHI = (1 + math.sqrt(5)) / 2

# ═══════════════════════════════════════════════════════════════════
# MODULE 1 — MÉMOIRE DE SESSION ABC (Dérivée Fractionnaire)
# ═══════════════════════════════════════════════════════════════════

class ABCSessionMemory:
    """
    Mémoire de session basée sur la dérivée fractionnaire ABC.
    
    PRINCIPE : Chaque interaction laisse une trace dans l'espace de phase
    qui décroît selon le noyau de Mittag-Leffler :
      E_α(-α·t^α)
    
    où α = 1/φ (ordre fractionnaire optimal).
    
    Contrairement à une exponentielle classique (qui oublie tout en ~5τ),
    le noyau de Mittag-Leffler garantit qu'aucune interaction n'est
    jamais complètement oubliée — la mémoire à long terme est préservée.
    """
    
    def __init__(self, alpha: float = None):
        self.alpha = alpha if alpha is not None else 1.0 / PHI
        self.history: List[Dict] = []  # (timestamp, query, response, wave)
        self.current_wave = np.zeros(64, dtype=np.float32)
    
    def mittag_leffler_weight(self, elapsed_seconds: float) -> float:
        """Poids de Mittag-Leffler : E_α(-α · t^α)."""
        t = elapsed_seconds
        alpha = self.alpha
        z = -alpha * (t ** alpha)
        # Serie : E_α(z) = Σ_{k=0}^∞ z^k / Γ(αk + 1)
        weight = 0.0
        for k in range(50):
            gamma_val = math.gamma(alpha * k + 1)
            term = (z ** k) / gamma_val
            weight += term
            if abs(term) < 1e-15:
                break
        return max(0.0, min(1.0, float(weight)))
    
    def add_interaction(self, query: str, response_wave: np.ndarray, 
                        metadata: Dict = None):
        """Ajoute une interaction à la mémoire de session."""
        self.history.append({
            "timestamp": time.time(),
            "query": query[:200],
            "wave": response_wave.copy() if isinstance(response_wave, np.ndarray) else response_wave,
            "metadata": metadata or {},
        })
        # Mise à jour de l'onde de session (moyenne pondérée par Mittag-Leffler)
        weights = []
        waves = []
        now = time.time()
        for h in self.history:
            age = now - h["timestamp"]
            w = self.mittag_leffler_weight(age)
            weights.append(w)
            waves.append(h["wave"])
        if waves:
            total_w = max(sum(weights), 1e-10)
            self.current_wave = np.sum([w * waves[i] for i, w in enumerate(weights)], axis=0) / total_w
    
    def get_context_wave(self) -> np.ndarray:
        """Retourne l'onde de contexte de la session."""
        return self.current_wave.copy()
    
    def get_recent_queries(self, n: int = 3) -> List[str]:
        """Retourne les n dernières requêtes."""
        return [h["query"] for h in self.history[-n:]]
    
    def weight(self, age_seconds: float) -> float:
        """Poids d'un souvenir d'âge donné."""
        return self.mittag_leffler_weight(age_seconds)


# ═══════════════════════════════════════════════════════════════════
# MODULE 2 — PONT ONDE↔LANGAGE (Interface Univers↔Humain)
# ═══════════════════════════════════════════════════════════════════

class WaveLanguageBridge:
    """
    Interface entre le langage humain et le langage ondulatoire de l'univers.
    
    PRINCIPE : 
      - Chaque mot est une fréquence (attribuée par φ)
      - Chaque phrase est une superposition de fréquences
      - Le sens émerge de l'interférence entre les fréquences des mots
      - Les émotions sont des phases dans l'espace harmonique
    
    Cette classe ne "comprend" pas le langage au sens LLM.
    Elle traduit des structures linguistiques en structures ondulatoires.
    Le SENS est la figure d'interférence — pas une représentation neuronale.
    """
    
    def __init__(self, vocab_size: int = 4096):
        self.vocab_size = vocab_size
        self.word_to_freq: Dict[str, float] = {}
        self.freq_to_word: Dict[int, str] = {}
        self.word_count = 0
    
    def build_vocabulary(self, documents: List[str]):
        """Construit le vocabulaire onde↔mot à partir d'un corpus."""
        from collections import Counter
        word_counts = Counter()
        for doc in documents[:5000]:
            for w in self._extract_words(doc):
                word_counts[w] += 1
        
        sorted_words = sorted(word_counts.items(), key=lambda x: -x[1])[:self.vocab_size]
        for i, (word, count) in enumerate(sorted_words):
            freq = (i + 1) * PHI  # Fréquence unique pour chaque mot
            self.word_to_freq[word] = freq
            self.freq_to_word[i] = word
            self.word_count += 1
    
    def word_phrase_to_wave(self, text: str, dim: int = 64) -> np.ndarray:
        """
        Texte → Onde harmonique.
        
        Chaque mot contribue une composante sinusoïdale à la fréquence
        qui lui est attribuée. La phrase est la somme de ces composantes.
        """
        wave = np.zeros(dim, dtype=np.float32)
        words = self._extract_words(text)
        if not words:
            return wave
        
        for i, word in enumerate(words):
            if word in self.word_to_freq:
                freq = self.word_to_freq[word]
                phase = i * 2 * math.pi / max(len(words), 1)
                for d in range(dim):
                    wave[d] += math.cos(freq * (d + 1) / dim + phase) / max(len(words), 1)
        
        norm = np.linalg.norm(wave)
        if norm > 1e-10:
            wave /= norm
        return wave
    
    def wave_phrase_similarity(self, text1: str, text2: str) -> float:
        """Similarité cosinus entre deux textes dans l'espace des ondes."""
        w1 = self.word_phrase_to_wave(text1)
        w2 = self.word_phrase_to_wave(text2)
        dot = float(np.dot(w1, w2))
        n1 = float(np.linalg.norm(w1))
        n2 = float(np.linalg.norm(w2))
        if n1 < 1e-10 or n2 < 1e-10:
            return 0.0
        return dot / (n1 * n2)
    
    def emotion_to_phase(self, emotion: str) -> float:
        """
        Émotion → Phase dans l'espace harmonique.
        
        Les émotions modulent la phase de l'onde :
          Joie      → 0° (phase constructive, expansion)
          Tristesse → 180° (phase destructive, contraction)
          Colère    → 90° (phase de cisaillement)
          Peur      → 270° (phase d'anticipation)
          Neutre    → 45° (phase d'équilibre)
        """
        emotion_phases = {
            "joie": 0.0,
            "tristesse": math.pi,
            "colere": math.pi / 2,
            "peur": 3 * math.pi / 2,
            "surprise": math.pi / 4,
            "neutre": math.pi / 4,
        }
        return emotion_phases.get(emotion.lower(), math.pi / 4)
    
    def _extract_words(self, text: str) -> List[str]:
        stop_words = {'dans', 'avec', 'pour', 'sur', 'sous', 'dont', 'cette', 'leur',
                      'plus', 'tout', 'vous', 'nous', 'alors', 'comme', 'bien', 'fait',
                      'peut', 'tres', 'sont', 'aux', 'une', 'est', 'les', 'des', 'pas',
                      'que', 'qui', 'par', 'the', 'and', 'cest', 'ete', 'etait'}
        words = []
        for w in text.lower().split():
            w = w.strip('.,;:!?()[]{}"\'-').lower()
            if len(w) > 2 and w not in stop_words and not w.isdigit():
                words.append(w)
        return words


# ═══════════════════════════════════════════════════════════════════
# MODULE 3 — GAGUT PIPELINE (Calcul Ondulatoire Intégré)
# ═══════════════════════════════════════════════════════════════════

class GAGUTPipeline:
    """
    Pipeline de calcul arithmétique via l'équation GAGUT.
    
    Intègre le Wave Math Engine dans le flux de raisonnement.
    
    DÉTECTION AUTOMATIQUE : Si la question contient une expression
    mathématique, le pipeline extrait les nombres, applique les
    opérations GAGUT, et retourne le résultat.
    """
    
    @staticmethod
    def detect_math_expression(text: str) -> Optional[Dict]:
        """Détecte si le texte contient une expression mathématique évaluable."""
        import re
        
        # Pattern : "calcule X opération Y"
        patterns = [
            (r"(\d+(?:\.\d+)?)\s*[\+\-]\s*(\d+(?:\.\d+)?)", "add_sub"),
            (r"(\d+(?:\.\d+)?)\s*[\*×]\s*(\d+(?:\.\d+)?)", "multiply"),
            (r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", "divide"),
            (r"(\d+(?:\.\d+)?)\s*\^\s*(\d+(?:\.\d+)?)", "power"),
            (r"racine\s*(?:carrée\s*(?:de\s*)?)?(\d+(?:\.\d+)?)", "sqrt"),
            (r"√\s*(\d+(?:\.\d+)?)", "sqrt"),
            (r"hypot[eé]nuse.*?(\d+).*?(\d+)", "pythagore"),
            (r"pythagore.*?(\d+).*?(\d+)", "pythagore"),
            (r"triangle.*?(\d+).*?(\d+)", "pythagore"),
        ]
        
        for pattern, op_type in patterns:
            match = re.search(pattern, text.lower())
            if match:
                groups = match.groups()
                return {"type": op_type, "groups": groups, "full_match": match.group(0)}
        return None
    
    @staticmethod
    def evaluate(expr_info: Dict) -> Tuple[float, str]:
        """Évalue une expression mathématique via GAGUT."""
        from wave_math_engine_v3_oyibo import (
            oyibo_add, oyibo_subtract, oyibo_multiply, 
            oyibo_divide, oyibo_power, oyibo_sqrt
        )
        
        op = expr_info["type"]
        groups = expr_info["groups"]
        
        if op == "add_sub":
            full = expr_info["full_match"]
            if "+" in full:
                result = oyibo_add(float(groups[0]), float(groups[1]))
            else:
                result = oyibo_subtract(float(groups[0]), float(groups[1]))
            return result, f"Addition via GAGUT : log_phi(phi^{groups[0]} × phi^{groups[1]})"
        
        elif op == "multiply":
            result = oyibo_multiply(float(groups[0]), float(groups[1]))
            return result, f"Multiplication via GAGUT : log_phi((phi^{groups[0]})^{groups[1]})"
        
        elif op == "divide":
            result = oyibo_divide(float(groups[0]), float(groups[1]))
            return result, f"Division via GAGUT : log_phi((phi^{groups[0]})^(1/{groups[1]}))"
        
        elif op == "power":
            base = float(groups[0])
            exp = int(float(groups[1]))
            result = oyibo_power(base, exp)
            return result, f"Puissance via GAGUT : {base}^{exp}"
        
        elif op == "sqrt":
            n = float(groups[0])
            result = oyibo_sqrt(n)
            return result, f"Racine via Newton-GAGUT : x_(k+1) = (x_k + {n}/x_k)/2"
        
        elif op == "pythagore":
            a, b = float(groups[0]), float(groups[1])
            a2 = oyibo_power(a, 2)
            b2 = oyibo_power(b, 2)
            c2 = oyibo_add(a2, b2)
            c = oyibo_sqrt(c2)
            return c, f"Pythagore via GAGUT : √({a}² + {b}²) = √({a2} + {b2}) = √({c2})"
        
        return 0.0, "Opération inconnue"


# ═══════════════════════════════════════════════════════════════════
# DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════

def demo():
    """Démonstration des trois modules."""
    print("=" * 70)
    print("  PONT UNIFIÉ ONDE↔LANGAGE — Démonstration")
    print("=" * 70)
    
    # 1. ABC Session Memory
    print("\n── 1. MÉMOIRE DE SESSION ABC ──")
    mem = ABCSessionMemory()
    mem.add_interaction("Quelle est la capitale du Sénégal ?", 
                        np.random.randn(64).astype(np.float32) * 0.1)
    mem.add_interaction("Et le Mali ?",
                        np.random.randn(64).astype(np.float32) * 0.1)
    mem.add_interaction("Donne-moi plus de détails sur Tombouctou",
                        np.random.randn(64).astype(np.float32) * 0.1)
    
    print(f"  Interactions en mémoire : {len(mem.history)}")
    print(f"  Requêtes récentes : {mem.get_recent_queries(3)}")
    print(f"  Poids Mittag-Leffler à t=0s : {mem.weight(0):.3f}")
    print(f"  Poids Mittag-Leffler à t=60s : {mem.weight(60):.3f}")
    print(f"  Poids Mittag-Leffler à t=3600s : {mem.weight(3600):.3f}")
    print(f"  → La mémoire décroît mais ne s'annule jamais (contrairement à e^(-t)).")
    
    # 2. Wave Language Bridge
    print("\n── 2. PONT ONDE↔LANGAGE ──")
    bridge = WaveLanguageBridge()
    corpus = [
        "La capitale du Sénégal est Dakar",
        "Dakar est une ville portuaire",
        "Le Sénégal est en Afrique de l'Ouest",
        "La France est en Europe",
        "Paris est la capitale de la France",
        "Le stoïcisme est une philosophie antique",
        "La philosophie recherche la sagesse",
    ]
    bridge.build_vocabulary(corpus)
    print(f"  Vocabulaire : {bridge.word_count} mots")
    print(f"  Fréquence de 'capitale' : {bridge.word_to_freq.get('capitale', 0):.2f}")
    print(f"  Fréquence de 'philosophie' : {bridge.word_to_freq.get('philosophie', 0):.2f}")
    print(f"  Fréquence de 'Dakar' : {bridge.word_to_freq.get('dakar', 0):.2f}")
    
    sim1 = bridge.wave_phrase_similarity("Dakar est la capitale", "capitale du Sénégal Dakar")
    sim2 = bridge.wave_phrase_similarity("Dakar est la capitale", "Paris capitale France")
    sim3 = bridge.wave_phrase_similarity("stoïcisme philosophie sagesse", "pensée antique stoïcienne")
    print(f"  Similarité 'Dakar capitale' ↔ 'capitale Sénégal Dakar' : {sim1:.3f}")
    print(f"  Similarité 'Dakar capitale' ↔ 'Paris capitale France' : {sim2:.3f}")
    print(f"  Similarité 'stoïcisme philosophie' ↔ 'pensée stoïcienne' : {sim3:.3f}")
    
    # 3. GAGUT Pipeline
    print("\n── 3. PIPELINE GAGUT ──")
    pipeline = GAGUTPipeline()
    tests = [
        "Calcule 3 + 4",
        "Combien font 12 × 15 ?",
        "Racine carrée de 144",
        "Si un triangle a des côtés de 3 et 4, quelle est l'hypoténuse ?",
    ]
    for t in tests:
        expr = GAGUTPipeline.detect_math_expression(t)
        if expr:
            result, explanation = GAGUTPipeline.evaluate(expr)
            print(f"  '{t}' → {result:.6f} ({explanation[:60]}...)")
        else:
            print(f"  '{t}' → pas d'expression mathématique détectée")
    
    print("\n" + "=" * 70)
    print("  FIN DE LA DÉMONSTRATION")
    print("=" * 70)


if __name__ == "__main__":
    demo()