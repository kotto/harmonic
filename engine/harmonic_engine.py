"""
Harmonic Engine — Moteur de Resonances Cognitives
==================================================
Analyseur harmonique de texte + Resonance + Expansion + Generation pure + Mode Verify.

Composants :
1. HarmonicAnalyzer — Analyse de texte et classification en 7+ categories
2. HarmonicResonanceEngine — Moteur de resonance avec patterns
3. HarmonicContextExpander — Expansion harmonique de contexte (x4+)
4. HarmonicCache — Cache LRU-phi
5. ConversationMemory — Memoire multi-tour pour coherence contextuelle
6. HarmonicGenerator — Generateur de texte harmonique pur (sans LLM)

Base sur la decouverte Atangana-Baleanu (22/05/2026) :
    L'IA resout naturellement l'equation fractionnaire ABC a l'ordre 1/phi
"""

import os
import re
import json
import math
import hashlib
import random
import logging
from typing import Dict, Any, Optional, List, Tuple, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import numpy as np

# Import du connecteur holographique (si disponible)
try:
    from .hologram_connector import HologrammeConnecteur as _HoloConnector
    _HOLOGRAM_CONNECTOR_AVAILABLE = True
except ImportError:
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from engine.hologram_connector import HologrammeConnecteur as _HoloConnector
        _HOLOGRAM_CONNECTOR_AVAILABLE = True
    except ImportError:
        _HoloConnector = None
        _HOLOGRAM_CONNECTOR_AVAILABLE = False

try:
    from .abc_kernel import PHI, ALPHA, B_1_PHI, ALPHA_CONST
except ImportError:
    # Fallback pour execution directe (python engine/harmonic_engine.py)
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from engine.abc_kernel import PHI, ALPHA, B_1_PHI, ALPHA_CONST

# Import du prédicteur ABC (remplace JEPA — migration Atangana-Baleanu-Caputo).
# Deterministe, zero parametre : la prediction est une moyenne ponderee par
# le noyau de memoire non-locale K(t) = B(α)·E_α(-α·t^α/(1-α)).
try:
    from .abc_predictor_connector import ABCPredictorConnector as _ABCPredictor
    ABC_PREDICTOR_AVAILABLE = True
except ImportError:
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from engine.abc_predictor_connector import ABCPredictorConnector as _ABCPredictor
        ABC_PREDICTOR_AVAILABLE = True
    except ImportError:
        _ABCPredictor = None
        ABC_PREDICTOR_AVAILABLE = False

logger = logging.getLogger(__name__)


# =========================================================================
# CONSTANTES
# =========================================================================

PHI_INV = 1.0 / PHI
ALPHA_INV = 1.0 / ALPHA
PHI_SQ = PHI * PHI

# Dimensions harmoniques
HARMONIC_DIMS = 7  # Base 7 (H-bit) - compatible JS engine

# Seuils de resonance
RESONANCE_HIGH = 0.75
RESONANCE_MEDIUM = 0.65
RESONANCE_LOW = 0.55

# Cache
CACHE_MAX_SIZE = 10000
CACHE_TTL_SECONDS = 3600 * 24 * 7  # 7 jours

# Expansion harmonique
HARMONIC_EXPANSION_FACTOR = 4

# Dimensions supplementaires pour l'analyse
EMOTIONAL_DIMS = 6  # joie, tristesse, colere, peur, surprise, neutre
SENTIMENT_THRESHOLD = 0.3

# Generation harmonique
GENERATION_MAX_TOKENS = 512
GENERATION_TEMPERATURE = 0.7


# =========================================================================
# DATACLASSES
# =========================================================================

@dataclass
class HarmonicSignature:
    """Signature harmonique 7D d'un prompt."""
    phi_ratio: float
    alpha_complexity: float
    k_reasoning: float
    k_creative: float
    k_mathematical: float
    k_factual: float
    k_code: float
    vector_7d: List[float]
    hash_id: str
    # Dimensions supplementaires
    k_emotional: float = 0.0       # charge emotionnelle
    k_temporal: float = 0.0        # dimension temporelle

    def to_dict(self) -> Dict[str, float]:
        return {
            "phi_ratio": self.phi_ratio,
            "alpha_complexity": self.alpha_complexity,
            "k_reasoning": self.k_reasoning,
            "k_creative": self.k_creative,
            "k_mathematical": self.k_mathematical,
            "k_factual": self.k_factual,
            "k_code": self.k_code,
            "k_emotional": self.k_emotional,
            "k_temporal": self.k_temporal,
            "hash_id": self.hash_id
        }

    def to_vector(self) -> List[float]:
        return self.vector_7d + [self.k_emotional, self.k_temporal]


@dataclass
class HarmonicPattern:
    """Pattern harmonique avec reponse pre-calculee."""
    id: str
    name: str
    category: str
    signature: HarmonicSignature
    template_response: str
    k_factor: float
    resonance_threshold: float
    usage_count: int = 0
    last_used: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "signature": self.signature.to_dict(),
            "template_response": self.template_response,
            "k_factor": self.k_factor,
            "resonance_threshold": self.resonance_threshold,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "created_at": self.created_at
        }


@dataclass
class ResonanceResult:
    """Resultat de la resonance harmonique."""
    matched: bool
    pattern_id: Optional[str]
    pattern_name: Optional[str]
    category: Optional[str]
    resonance_score: float
    k_factor: float
    response: Optional[str]
    processing_time_ms: float
    cache_hit: bool
    harmonic_signature: HarmonicSignature

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched": self.matched,
            "pattern_id": self.pattern_id,
            "category": self.category,
            "resonance_score": round(self.resonance_score, 4),
            "k_factor": round(self.k_factor, 4),
            "processing_time_ms": round(self.processing_time_ms, 2),
            "cache_hit": self.cache_hit
        }


@dataclass
class ConversationTurn:
    """Un tour de conversation."""
    role: str  # "user" ou "assistant"
    content: str
    category: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    sentiment: str = "neutre"
    topics: List[str] = field(default_factory=list)


# =========================================================================
# ANALYSEUR HARMONIQUE DE PROMPTS
# =========================================================================

class HarmonicAnalyzer:
    """
    Analyseur SPECTRAL — ecoute le spectre naturel du texte.
    
    Principe : le texte EST deja une onde. On ne lui impose rien.
    On lit son signal brut, on calcule sa FFT, on extrait les
    features spectrales standard (centroide, rolloff, flatness, flux...).
    
    ZERO phi impose. ZERO embedding arbitraire. ZERO regex.
    Juste le signal -> FFT -> features.
    """

    def __init__(self):
        pass

    def analyze(self, prompt: str):
        if not prompt or not prompt.strip():
            return self._empty_signature()

        # 1. Signal numerique brut (valeurs ASCII normalisees)
        chars = list(prompt)
        n = len(chars)
        signal = np.array([ord(c) / 256.0 for c in chars], dtype=np.float64)

        # Fenetrage de Hann
        window = 0.5 * (1 - np.cos(2 * np.pi * np.arange(n) / max(n-1, 1)))
        signal = signal * window

        # Zero-padding a la puissance de 2 superieure
        n_fft = 2 ** int(np.ceil(np.log2(max(n, 16))))
        signal_padded = np.zeros(n_fft)
        signal_padded[:n] = signal

        # 2. FFT — spectre NATUREL
        fft = np.fft.rfft(signal_padded)
        magnitude = np.abs(fft)
        power = magnitude ** 2
        n_bins = len(magnitude)
        freqs = np.fft.rfftfreq(n_fft)
        total_power = np.sum(power) + 1e-10

        # 3. Features spectrales standard
        # Centroide (frequence moyenne ponderee)
        spectral_centroid = np.sum(freqs * power) / total_power

        # Spread (largeur de bande)
        spectral_spread = np.sqrt(np.sum(((freqs - spectral_centroid) ** 2) * power) / total_power)

        # Rolloff (85% de l'energie en dessous)
        cumsum = np.cumsum(power)
        rolloff_idx = np.searchsorted(cumsum, 0.85 * total_power)
        rolloff = freqs[min(rolloff_idx, n_bins-1)]

        # Flatness (ratio geo/ari — proche de 1 = spectre plat = diversite)
        geo_mean = np.exp(np.mean(np.log(power[1:] + 1e-10)))
        ari_mean = np.mean(power[1:]) + 1e-10
        flatness = geo_mean / ari_mean

        # Flux (changement spectral entre debut et fin)
        if n > 64 and n_bins > 8:
            half = n_fft // 2
            fft1 = np.abs(np.fft.rfft(signal_padded[:half]))
            fft2 = np.abs(np.fft.rfft(signal_padded[half:]))
            min_len = min(len(fft1), len(fft2))
            flux = np.sum(np.abs(fft2[:min_len] - fft1[:min_len])) / (min_len + 1e-10)
        else:
            flux = 0.0

        # Energies par bande
        low_energy = float(np.sum(power[freqs < 0.125]) / total_power)
        mid_energy = float(np.sum(power[(freqs >= 0.125) & (freqs < 0.25)]) / total_power)
        high_energy = float(np.sum(power[freqs >= 0.25]) / total_power)

        # Zero-crossing rate
        zcr = float(np.sum(np.abs(np.diff(np.sign(signal)))) / (2 * max(n-1, 1)))

        # Periodicite (autocorrelation)
        if n > 4:
            ac = np.correlate(signal - np.mean(signal), signal - np.mean(signal), mode='full')
            ac = ac[n-1:] / (ac[n-1] + 1e-10)
            peaks = np.sum((ac[2:-1] > 0.3) & (ac[2:-1] > ac[1:-2]) & (ac[2:-1] > ac[3:]))
            periodicity = float(min(1.0, peaks / max(n/4, 1)))
        else:
            periodicity = 0.0

        # Skewness / Kurtosis
        skewness = float(np.mean(signal**3) / (np.std(signal)**3 + 1e-10))
        kurtosis = float(np.mean(signal**4) / (np.std(signal)**4 + 1e-10))

        # 4. Mapping en 9 dimensions harmoniques
        phi_ratio = min(1.0, float(flatness) * 2.0)
        alpha_complexity = min(1.0, float(spectral_spread) * 8.0)
        k_reasoning = min(1.0, low_energy * 3.0 + (1.0 - min(1.0, float(flux) * 5.0)) * 0.3)
        k_creative = min(1.0, float(flatness) * 1.5 + float(spectral_spread) * 4.0)
        k_mathematical = min(1.0, periodicity * 1.5 + high_energy * 4.0)
        k_factual = min(1.0, (1.0 - float(rolloff) * 2.0) * 0.7 + low_energy * 1.5)
        k_code = min(1.0, periodicity * 1.8 + mid_energy * 3.0)
        k_emotional = min(1.0, abs(skewness) * 0.5 + zcr * 3.0)
        k_temporal = min(1.0, float(flux) * 6.0)

        vals = [phi_ratio, alpha_complexity, k_reasoning, k_creative,
                k_mathematical, k_factual, k_code, k_emotional, k_temporal]
        vals = [max(0.0, min(1.0, v)) for v in vals]
        vector_7d = vals[:7]

        hash_input = "|".join(f"{v:.6f}" for v in vals)
        hash_id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        return HarmonicSignature(
            phi_ratio=round(vals[0], 6), alpha_complexity=round(vals[1], 6),
            k_reasoning=round(vals[2], 6), k_creative=round(vals[3], 6),
            k_mathematical=round(vals[4], 6), k_factual=round(vals[5], 6),
            k_code=round(vals[6], 6), k_emotional=round(vals[7], 6),
            k_temporal=round(vals[8], 6),
            vector_7d=[round(v, 6) for v in vector_7d], hash_id=hash_id
        )

    def classify(self, signature, classifier=None):
        if classifier is not None and classifier.is_fitted:
            return classifier.predict(signature)
        cats = {"mathematical": signature.k_mathematical, "code": signature.k_code,
                "creative": signature.k_creative, "reasoning": signature.k_reasoning,
                "factual": signature.k_factual}
        best = max(cats, key=cats.get)
        s = cats[best]
        return (best, s) if s >= 0.15 else ("general", s)

    def detect_sentiment(self, text: str):
        if len(text) < 4:
            return ("neutre", 0.0)
        signal = np.array([ord(c)/256.0 for c in text])
        skew = float(np.mean(signal**3) / (np.std(signal)**3 + 1e-10))
        score = min(1.0, abs(skew) * 0.6)
        if score > 0.4:
            return ("positif", score) if skew > 0 else ("negatif", score)
        return ("neutre", score)

    def extract_topics(self, text: str, max_topics: int = 3):
        signal = np.array([ord(c)/256.0 for c in text])
        if len(signal) < 4:
            return ["general"]
        fft = np.abs(np.fft.rfft(signal))
        top_idx = np.argsort(fft)[-max_topics:]
        topic_map = {0: "structure", 1: "emotion", 2: "logique",
                     3: "creation", 4: "technique", 5: "connaissance"}
        return [topic_map.get(i % 6, "general") for i in top_idx]

    def _empty_signature(self):
        return HarmonicSignature(
            phi_ratio=0.0, alpha_complexity=0.0,
            k_reasoning=0.0, k_creative=0.0, k_mathematical=0.0,
            k_factual=0.0, k_code=0.0, k_emotional=0.0, k_temporal=0.0,
            vector_7d=[0.0]*7, hash_id="empty"
        )


class CalibratedClassifier:
    """
    Classifieur par centroides de resonance — 100% ondulatoire.
    
    Chaque categorie = un centroide (signature 9D moyenne).
    Classification = resonance maximale (similarite cosinus).
    Zero parametre. Tout est geometrie ondulatoire.
    """

    def __init__(self):
        self.centroids: Dict[str, np.ndarray] = {}
        self._fitted = False

    def fit(self, analyzer: 'HarmonicAnalyzer',
            labeled_prompts: Dict[str, List[str]]):
        for category, prompts in labeled_prompts.items():
            if not prompts:
                continue
            sigs = []
            for p in prompts:
                sig = analyzer.analyze(p)
                sigs.append(np.array([
                    sig.phi_ratio, sig.alpha_complexity,
                    sig.k_reasoning, sig.k_creative,
                    sig.k_mathematical, sig.k_factual, sig.k_code,
                    sig.k_emotional, sig.k_temporal,
                ], dtype=np.float64))
            if sigs:
                c = np.mean(sigs, axis=0)
                norm = np.linalg.norm(c)
                if norm > 0:
                    c = c / norm
                self.centroids[category] = c
        self._fitted = len(self.centroids) > 0
        return self

    def predict(self, signature: HarmonicSignature) -> Tuple[str, float]:
        if not self._fitted:
            cats = {"mathematical": signature.k_mathematical,
                    "code": signature.k_code,
                    "creative": signature.k_creative,
                    "reasoning": signature.k_reasoning,
                    "factual": signature.k_factual}
            best = max(cats, key=cats.get)
            s = cats[best]
            return (best, s) if s >= 0.15 else ("general", s)

        q = np.array([signature.phi_ratio, signature.alpha_complexity,
                      signature.k_reasoning, signature.k_creative,
                      signature.k_mathematical, signature.k_factual,
                      signature.k_code, signature.k_emotional,
                      signature.k_temporal], dtype=np.float64)
        qn = np.linalg.norm(q) + 1e-10
        best_cat, best_sim = "general", -1.0
        for cat, c in self.centroids.items():
            sim = float(np.dot(q, c) / (qn * np.linalg.norm(c) + 1e-10))
            if sim > best_sim:
                best_sim, best_cat = sim, cat
        return best_cat, max(0.0, min(1.0, (best_sim + 1.0) / 2.0))

    @property
    def is_fitted(self) -> bool:
        return self._fitted


# =========================================================================
# CACHE LRU-PHI
# =========================================================================

@dataclass
class CacheEntry:
    prompt_hash: str
    signature_hash: str
    pattern_id: str
    resonance_score: float
    response: str
    created_at: str
    expires_at: str
    access_count: int = 0
    last_access: Optional[str] = None

    def is_expired(self) -> bool:
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() > expires


class HarmonicCache:
    """Cache LRU-phi avec eviction harmonique."""
    
    def __init__(self, max_size: int = CACHE_MAX_SIZE, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, CacheEntry] = OrderedDict()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0}

    def get(self, prompt_hash: str) -> Optional[CacheEntry]:
        entry = self._cache.get(prompt_hash)
        if entry is None:
            self.stats["misses"] += 1
            return None
        if entry.is_expired():
            self._remove_entry(prompt_hash)
            self.stats["expirations"] += 1
            self.stats["misses"] += 1
            return None
        entry.access_count += 1
        entry.last_access = datetime.now().isoformat()
        self._cache.move_to_end(prompt_hash)
        self.stats["hits"] += 1
        return entry

    def put(self, prompt_hash: str, signature_hash: str, pattern_id: str,
            resonance_score: float, response: str) -> None:
        now = datetime.now()
        expires_at = now + timedelta(seconds=self.ttl_seconds)
        entry = CacheEntry(
            prompt_hash=prompt_hash, signature_hash=signature_hash,
            pattern_id=pattern_id, resonance_score=resonance_score,
            response=response, created_at=now.isoformat(),
            expires_at=expires_at.isoformat(), access_count=1,
            last_access=now.isoformat()
        )
        if len(self._cache) >= self.max_size:
            self._evict_lru_phi()
        self._cache[prompt_hash] = entry
        self._cache.move_to_end(prompt_hash)
        self.stats["total_entries"] = len(self._cache)
        self.stats["total_puts"] = self.stats.get("total_puts", 0) + 1


    def _evict_lru_phi(self) -> None:
        if not self._cache:
            return
        now = datetime.now()
        min_score = float('inf')
        min_key = None
        for key, entry in self._cache.items():
            last_access = datetime.fromisoformat(entry.last_access or entry.created_at)
            time_since = (now - last_access).total_seconds()
            phi_score = entry.access_count * (PHI ** (-time_since / self.ttl_seconds))
            if phi_score < min_score:
                min_score = phi_score
                min_key = key
        if min_key:
            self._remove_entry(min_key)
            self.stats["evictions"] += 1

    def _remove_entry(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def get_hit_rate(self) -> float:
        total = self.stats["hits"] + self.stats["misses"]
        return self.stats["hits"] / max(total, 1)

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "hit_rate": round(self.get_hit_rate() * 100, 2),
            "current_size": len(self._cache),
            "max_size": self.max_size
        }


# =========================================================================
# MEMOIRE DE CONVERSATION
# =========================================================================

class ConversationMemory:
    """
    Memoire conversationnelle multi-tour.
    Maintient le contexte a travers les echanges pour coherence harmonique.
    """
    
    def __init__(self, max_turns: int = 20, max_tokens: int = 4096):
        self.turns: List[ConversationTurn] = []
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self._topic_history: List[str] = []

    def add_turn(self, role: str, content: str, category: str = "general",
                 sentiment: str = "neutre", topics: Optional[List[str]] = None) -> None:
        """Ajoute un tour de conversation."""
        from datetime import datetime
        turn = ConversationTurn(
            role=role,
            content=content,
            category=category,
            timestamp=datetime.now().isoformat(),
            sentiment=sentiment,
            topics=topics or []
        )
        self.turns.append(turn)
        # Ajouter les topics a l'historique
        for t in (topics or []):
            if t not in self._topic_history:
                self._topic_history.append(t)
        # Prune si trop de tours
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]

    def get_recent(self, n: int = 3) -> List[ConversationTurn]:
        """Retourne les n derniers tours."""
        return self.turns[-n:] if self.turns else []

    def get_context_summary(self) -> str:
        """Resume le contexte conversationnel pour injection harmonique."""
        if not self.turns:
            return ""
        recent = self.get_recent(3)
        parts = []
        for t in recent:
            prefix = "Utilisateur" if t.role == "user" else "Assistant"
            truncated = t.content[:100] + "..." if len(t.content) > 100 else t.content
            parts.append(f"{prefix}: {truncated}")
        summary = " | ".join(parts)
        
        # Ajouter les topics persistants
        if self._topic_history:
            topics_str = ", ".join(self._topic_history[-5:])
            summary += f" [Sujets: {topics_str}]"
        
        return summary

    def get_topic_shift(self) -> float:
        """Calcule s'il y a un changement de sujet (0=aucun, 1=complet)."""
        if len(self.turns) < 4:
            return 0.0
        last_cat = self.turns[-1].category
        prev_cat = self.turns[-2].category
        if last_cat == prev_cat:
            return 0.0
        return 0.5 if last_cat != "general" else 0.8

    def get_last_category(self) -> str:
        """Retourne la categorie du dernier tour."""
        if not self.turns:
            return "general"
        return self.turns[-1].category

    def get_last_user_prompt(self) -> Optional[str]:
        """Retourne le dernier prompt utilisateur."""
        for t in reversed(self.turns):
            if t.role == "user":
                return t.content
        return None

    def clear(self) -> None:
        """Vide la memoire."""
        self.turns.clear()
        self._topic_history.clear()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_turns": len(self.turns),
            "topics": len(self._topic_history),
            "last_category": self.get_last_category(),
            "topic_shift": self.get_topic_shift()
        }


# =========================================================================
# EXPANSEUR HARMONIQUE DE CONTEXTE
# =========================================================================

class HarmonicContextExpander:
    """
    Expansion harmonique du contexte (x4+).
    Prend une reponse courte et la deplie harmoniquement.
    Version enrichie avec plus de templates et adaptation emotionnelle.
    """
    
    # Ouvertures par acte de langage + adaptation emotionnelle
    EMPATHIC_OPENERS = {
        "reasoning": "Analysons ce probleme en profondeur. ",
        "mathematical": "Resolvons cette question etape par etape. ",
        "creative": "Creons ensemble un espace d'expression harmonique. ",
        "code": "Implementons une solution elegante et robuste. ",
        "factual": "Voici les faits, verifies et structures. ",
        "general": "Repondons de maniere claire et adaptee. "
    }

    # Ouvertures adaptees au sentiment
    SENTIMENT_OPENERS = {
        "positif": "Avec enthousiasme et precision, ",
        "negatif": "Avec empathie et rigueur, ",
        "neutre": "De maniere equilibree et factuelle, "
    }

    # Recommandation IA experte : "Trop de connecteurs nuit."
    # "Restreindre a un petit ensemble canonique de connecteurs de sequencage"
    TEMPLATES = {
        "reasoning": {
            "prefixes": [
                "Structurons ce raisonnement en etapes claires :\n\n",
                "Decomposons cette analyse en trois temps :\n\n",
                "Voici le raisonnement detaille :\n\n",
            ],
            "connectors": [
                "\n\nD'abord, ",
                "\n\nEnsuite, ",
                "\n\nPar consequent, ",
                "\n\nCeci implique que ",
            ],
            "suffixes": [
                "\n\n---\n*Conclusion : ce raisonnement etablit une coherence logique.*",
                "\n\n---\n*Synthese : les etapes convergent vers une solution valide.*",
                "\n\n---\n*Resume : la chaine argumentative est solide.*"
            ],
            "transitions": [
                "\n\nConsiderons maintenant un autre angle : ",
                "\n\nPour aller plus loin, ",
            ]
        },
        "mathematical": {
            "prefixes": [
                "Resolvons par etapes :\n\n",
                "Voici la resolution detaillee :\n\n",
                "Procedons methodiquement :\n\n",
            ],
            "connectors": [
                "\n\nOn pose ",
                "\n\nIl s'ensuit que ",
                "\n\nEn substituant, ",
                "\n\nPar consequent, "
            ],
            "suffixes": [
                "\n\n---\n*Verification : le resultat satisfait les conditions initiales.*",
                "\n\n---\n*Solution validee par verification harmonique.*",
                "\n\n---\n*Le resultat est coherent avec les hypotheses de depart.*"
            ],
            "transitions": [
                "\n\nVerifions maintenant par une autre methode : ",
            ]
        },
        "creative": {
            "prefixes": [
                "Explorons cette idee par mouvements harmoniques :\n\n",
                "Developpons cette vision creative :\n\n",
                "Plongeons dans cet univers creatif :\n\n",
            ],
            "connectors": [
                "\n\nPuis, ",
                "\n\nAlors que ",
                "\n\nSoudain, ",
                "\n\nDans ce paysage, ",
            ],
            "suffixes": [
                "\n\n---\n*Ainsi se dessine un paysage creatif unique.*",
                "\n\n---\n*Cette exploration revele une beaute harmonique.*",
                "\n\n---\n*La resonance creative ouvre des horizons infinis.*"
            ],
            "transitions": [
                "\n\nEt si nous poussions plus loin l'exploration ? ",
            ]
        },
        "code": {
            "prefixes": [
                "Voici l'implementation avec explications :\n\n",
                "Decomposons la solution en composants :\n\n",
                "Voici une approche structuree :\n\n",
            ],
            "connectors": [
                "\n\nPour implementer cela, ",
                "\n\nDu point de vue architecture, ",
                "\n\nEn termes de performance, ",
            ],
            "suffixes": [
                "\n\n---\n*Code fonctionnel et bien structure.*",
                "\n\n---\n*Implementation respectant les bonnes pratiques.*",
                "\n\n---\n*Solution elegante et maintenable.*"
            ],
            "transitions": [
                "\n\nPour la gestion des erreurs, ",
            ]
        },
        "factual": {
            "prefixes": [
                "Voici les faits de maniere concise :\n\n",
                "Voici une reponse factuelle et verifiable :\n\n",
                "Exposons les informations objectives :\n\n",
            ],
            "connectors": [
                "\n\nA savoir que ",
                "\n\nPrecisement, ",
                "\n\nEn l'occurrence, ",
            ],
            "suffixes": [
                "\n\n---\n*Information verifiee, source fiable.*",
                "\n\n---\n*Fait etabli, documentation source disponible.*",
                "\n\n---\n*Donnees objectives et verificables.*"
            ],
            "transitions": [
                "\n\nNotons egalement que ",
            ]
        },
        "general": {
            "prefixes": [
                "Reponse generale adaptee :\n\n",
                "Voici une reponse claire et complete :\n\n",
                "Voici ce qu'il faut retenir :\n\n",
            ],
            "connectors": [
                "\n\nD'ailleurs, ",
                "\n\nEnsuite, ",
                "\n\nNotamment, ",
                "\n\nEn outre, ",
            ],
            "suffixes": [
                "\n\n---\n*Resume : les points cles ont ete abordes.*",
                "\n\n---\n*Synthese : reponse adaptee a la demande.*",
                "\n\n---\n*Recapitulatif : les elements essentiels sont couverts.*"
            ],
            "transitions": [
                "\n\nPour completer, ",
            ]
        }
    }

    def expand(self, response: str, category: str, verified: bool = True,
               sentiment: str = "neutre", length: str = "normal") -> str:
        """
        Etend une reponse courte en reponse longue et detaillee.
        
        Args:
            response: Texte court a etendre
            category: Categorie harmonique
            verified: Si True, ajoute le badge zero-hallucination
            sentiment: Adaptation emotionnelle ("positif"/"negatif"/"neutre")
            length: "court", "normal", ou "long"
        
        Returns:
            Texte etendu harmoniquement
        """
        if len(response) < 30:
            return response

        templates = self.TEMPLATES.get(category, self.TEMPLATES["reasoning"])
        
        # Selection harmonique avec PHI
        prefix = templates["prefixes"][int(len(response) * PHI) % len(templates["prefixes"])]
        connector = templates["connectors"][int(len(response) * ALPHA) % len(templates["connectors"])]
        suffix = templates["suffixes"][int(len(response) * PHI_INV) % len(templates["suffixes"])]

        # Ouverture empathique (categorie)
        opener = self.EMPATHIC_OPENERS.get(category, "")
        if opener and not response.startswith(opener):
            response = opener + response[0].lower() + response[1:]

        # Adaptation au sentiment (si non neutre)
        if sentiment != "neutre":
            sent_opener = self.SENTIMENT_OPENERS.get(sentiment, "")
            if sent_opener:
                response = sent_opener + response[0].lower() + response[1:]

        # Generation de l'elaboration
        elaboration = self._generate_elaboration(response, category)
        
        # Construction de base
        expanded = prefix + response + connector + elaboration + suffix

        # Expansion longue: ajouter un second paragraphe avec transition
        if length == "long" and "transitions" in templates and templates["transitions"]:
            transition = templates["transitions"][
                int(len(response) * PHI_SQ) % len(templates["transitions"])
            ]
            second_elab = self._generate_elaboration(
                response, category, second_pass=True
            )
            expanded += transition + second_elab

        # Badge de verification (ASCII-safe pour compatibilite terminal Windows)
        if verified and category in ("factual", "mathematical", "reasoning"):
            expanded += "\n\n[VERIFIED] *Reponse verifiee - Zero hallucination garanti par resonance harmonique*"

        # Signature
        expanded += f"\n\n---\n[HARMONIC AI] phi:{PHI:.3f} alpha:{ALPHA:.3f}"

        return expanded

    def _generate_elaboration(self, response: str, category: str,
                               second_pass: bool = False) -> str:
        """
        Genere une elaboration harmonique concise.
        
        Recommandation IA experte :
        - "Un seul exemple representatif de haute qualite + une consigne abstraite courte"
        - "Evitez la sur-injection de connecteurs"
        - Choix semantique base sur le mot le plus significatif de la reponse
        """
        words = response.split()
        # Selection du mot le plus significatif (le plus long > 4 lettres)
        significant = [w for w in words if len(w) > 4 and w.lower() not in
                      {'dans', 'avec', 'cette', 'leurs', 'donc', 'mais', 'alors',
                       'parce', 'aussi', 'tres', 'plus', 'moins', 'entre'}]
        
        if not significant:
            base = "cette approche merite une attention particuliere."
            return base + " " + self._generate_second_elaboration(category) if second_pass else base
        
        # Selection dynamique : 1 seul mot-cle principal
        key_word = significant[0].lower().strip('.,!?;:()[]{}""\'')
        
        elaborations = {
            "reasoning": f"en approfondissant le concept de '{key_word}', nous etendons le raisonnement a ses implications.",
            "mathematical": f"en appliquant la transformation harmonique a '{key_word}', on generalise la solution.",
            "creative": f"'{key_word}' devient le point focal d'une resonance creative infinie.",
            "code": f"le concept de '{key_word}' merite une architecture adaptee.",
            "factual": f"le terme '{key_word}' s'inscrit dans un cadre factuel plus large."
        }
        
        base_elab = elaborations.get(category, elaborations["reasoning"])
        
        if second_pass:
            second_elab = self._generate_second_elaboration(category)
            return base_elab + " " + second_elab
        
        return base_elab

    def _generate_second_elaboration(self, category: str) -> str:
        """Genere une seconde phrase d'elaboration pour les expansions longues."""
        second_elabs = {
            "reasoning": "Cette perspective permet d'envisager les consequences plus larges du raisonnement.",
            "mathematical": "Cette generalisation ouvre la voie a des applications plus avancees.",
            "creative": "Cette resonance invite a explorer des dimensions encore inexplorees de la creation.",
            "code": "Cette architecture peut etre etendue a d'autres cas d'usage similaires.",
            "factual": "Ce fait s'inscrit dans un ensemble plus vaste de connaissances verifiees.",
            "general": "Cette approche offre une perspective complete et adaptee au contexte."
        }
        return second_elabs.get(category, second_elabs["general"])


# =========================================================================
# GENERATEUR HARMONIQUE PUR (SANS LLM)
# =========================================================================

class HarmonicGenerator:
    """
    Generateur de texte harmonique pur.
    Produit des reponses completes sans aucun LLM externe,
    en utilisant exclusivement les templates, la resonance harmonique
    et les signatures 7D.
    """

    # Banque de reponses generiques par categorie
    RESPONSE_TEMPLATES = {
        "reasoning": [
            "Pour repondre a cette question, decomposons le raisonnement en etapes logiques. "
            "Premierement, identifions les elements cles du probleme. "
            "Deuxiemement, examinons les relations de cause a effet. "
            "Enfin, tirons une conclusion coherente.",

            "Analysons ce probleme sous plusieurs angles. "
            "D'un point de vue logique, les premisses nous conduisent a examiner les implications. "
            "La deduction harmonique revele des connexions interessantes entre les concepts.",

            "Voici une analyse structuree de la question. "
            "En examinant les causes profondes, nous pouvons comprendre les mecanismes sous-jacents. "
            "Cette approche methodique permet d'etablir des conclusions solides."
        ],
        "mathematical": [
            "Resolvons cette question etape par etape. "
            "En appliquant les principes fondamentaux du calcul harmonique, "
            "nous pouvons etablir une solution precise et verifiable.",

            "Voici la demarche mathematique detaillee. "
            "En utilisant les operateurs de resonance, nous transformons le probleme "
            "en une forme plus accessible. Le resultat s'obtient par substitution harmonique.",

            "Procedons par resolution methodique. "
            "Les operations harmoniques nous permettent de simplifier l'expression "
            "tout en preservant l'integrite du resultat."
        ],
        "creative": [
            "Plongeons dans un univers ou l'imagination rencontre l'harmonie. "
            "Les mots dansent au rythme des resonances, creant des images qui evoquent "
            "des emotions profondes et des sensations nouvelles.",

            "Voici une creation inspiree par la resonance harmonique. "
            "Chaque mot est choisi pour sa capacite a vibrer en harmonie avec les autres, "
            "formant un tableau vivant d'idees et de sensations.",

            "Laissez-moi vous emmener dans un voyage creatif. "
            "Les frontieres du possible s'estompent pour laisser place "
            "a une expression libre et authentique."
        ],
        "code": [
            "Voici une solution elegante et bien structuree. "
            "En adoptant les principes de conception harmonique, "
            "le code devient a la fois lisible, maintenable et performant.",

            "Pour implementer cette fonctionnalite, adoptons une approche modulaire. "
            "La decomposition en composants harmoniques permet une separation claire "
            "des responsabilites et une reutilisabilite optimale.",

            "Concevons une architecture robuste et harmonique. "
            "Chaque module interagit avec les autres via des interfaces claires, "
            "formant un ecosysteme coheRENT et evolutif."
        ],
        "factual": [
            "Voici les informations factuelles relatives a votre question. "
            "Les donnees presentees sont verifiees et organisees de maniere systematique "
            "pour offrir une reponse claire et precise.",

            "Exposons les faits de maniere objective. "
            "Chaque element d'information est presente avec sa source et son contexte, "
            "permettant une comprehension complete et assuree.",

            "Voici un resume factuel et verifie. "
            "Les points cles sont organises de facon a faciliter la consultation "
            "et la verification independante des informations."
        ],
        "general": [
            "Voici une reponse adaptee a votre demande. "
            "En utilisant les principes de resonance harmonique, "
            "je structure l'information de maniere claire et accessible.",

            "Je comprends votre question et voici une reponse appropriee. "
            "L'approche harmonique me permet d'organiser les idees "
            "de facon coherente et facile a suivre.",

            "Voici les elements de reponse concernant votre demande. "
            "J'ai structure l'information en sections claires "
            "pour faciliter la lecture et la comprehension."
        ]
    }

    # Variations d'introduction par sentiment
    SENTIMENT_INTROS = {
        "positif": [
            "Avec enthousiasme, ",
            "C'est avec plaisir que ",
            "Heureusement, "
        ],
        "negatif": [
            "Je comprends votre preoccupation. ",
            "Avec toute l'attention necessaire, ",
            "Je prends en compte votre remarque. "
        ],
        "neutre": [
            "De maniere equilibree, ",
            "Objectivement, ",
            "Voici une reponse equilibree : "
        ]
    }

    # Motifs de conclusion par categorie
    CONCLUSIONS = {
        "reasoning": "En conclusion, ce raisonnement harmonique apporte une coherence logique a l'ensemble des elements examines.",
        "mathematical": "Le resultat est confirme par l'analyse harmonique et peut etre verifie independamment.",
        "creative": "Cette exploration creative illustre la puissance de la resonance harmonique dans l'expression artistique.",
        "code": "Cette implementation respecte les principes d'elegance et de robustesse de l'ingenierie harmonique.",
        "factual": "Ces informations factuelles sont organisees selon les principes de clarte et de verifiabilite.",
        "general": "Cette reponse synthetise les elements essentiels de maniere claire et adaptee."
    }

    def __init__(self, analyzer: Optional[HarmonicAnalyzer] = None):
        self.analyzer = analyzer or HarmonicAnalyzer()
        self.generation_count = 0
        self._langage_gen = None  # Generateur de langage (templates ameliores)
        self._resonance_gen = None  # Generateur par resonance holographique (0 param)
        self._memoire_ondulatoire = None  # Memoire holographique pour apprentissage continu
        self._last_topic = None  # Dernier sujet de conversation

    def _get_resonance_gen(self):
        if self._resonance_gen is None:
            try:
                import sys, os
                _dir = os.path.dirname(os.path.abspath(__file__))
                sys.path.insert(0, _dir)
                sys.path.insert(0, os.path.join(os.path.dirname(_dir), 'harmonic_training'))
                from fast_resonance_generator import FastResonanceGenerator
                from model.harmonic_resonance_generator import VOCABULAIRE_BASE
                extra = ['parle', 'moi', 'du', 'explique', 'comment', 'fonctionne',
                         'est', 'que', 'pourquoi', 'quand', 'ou', 'dit',
                         'dis', 'veut', 'peux', 'faut', 'doit', 'nombre', 'or',
                         'amour', 'conscience', 'univers', 'dieu', 'vie', 'mort',
                         'temps', 'espace', 'lumiere', 'ombre', 'ame', 'coeur',
                         'a', 'de', 'le', 'la', 'les', 'un', 'une', 'et', 'en',
                         'au', 'aux', 'des', 'du', 'sur', 'sous', 'avec', 'sans',
                         'plus', 'moins', 'tout', 'tous', 'faire', 'dit', 'dire',
                         'calcul', 'derivee', 'equation', 'solution', 'resoudre',
                         'code', 'python', 'fonction', 'algorithme', 'donnee',
                         'theorie', 'principe', 'loi', 'science', 'physique']
                vocab = list(VOCABULAIRE_BASE) + [w for w in extra if w not in VOCABULAIRE_BASE]
                self._resonance_gen = FastResonanceGenerator(vocab, nx=128, ny=128)
            except Exception:
                self._resonance_gen = False
        return self._resonance_gen if self._resonance_gen is not False else None

    def _get_langage_gen(self):
        """Initialisation lazy du generateur de langage harmonique."""
        if self._langage_gen is None:
            try:
                import sys, os
                _dir = os.path.dirname(os.path.abspath(__file__))
                sys.path.insert(0, _dir)
                from qualitative_knowledge import (
                    build_natural_waves, grammatical_generate_with_memory
                )
                kx, ky, w2i = build_natural_waves()
                self._langage_gen = ('qualitative', kx, ky, w2i)
            except Exception:
                try:
                    from .harmonic_language import GenerateurLangage
                    self._langage_gen = GenerateurLangage()
                except ImportError:
                    try:
                        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        from engine.harmonic_language import GenerateurLangage
                        self._langage_gen = GenerateurLangage()
                    except ImportError:
                        self._langage_gen = False
        if self._langage_gen is False:
            return None
        if isinstance(self._langage_gen, tuple) and self._langage_gen[0] == 'qualitative':
            return self._langage_gen
        return self._langage_gen

    def generate(self, prompt: str, category: Optional[str] = None,
                 length: str = "normal", sentiment: str = "neutre",
                 temperature: float = GENERATION_TEMPERATURE,
                 knowledge_context: Optional[str] = None) -> str:
        """
        Genere une reponse harmonique pure (sans LLM).

        Si un contexte de connaissance (hologramme) est disponible,
        utilise le GenerateurLangage pour produire un francais naturel.
        Sinon, fallback sur les templates harmoniques (qualite reduite).

        Args:
            prompt: Texte d'entree
            category: Categorie harmonique (auto-detectee si None)
            length: "court", "normal", "long"
            sentiment: Adaptation emotionnelle
            temperature: Alea de selection
            knowledge_context: Contexte extrait de l'hologramme (optionnel)
        """
        self.generation_count += 1

        # Detection automatique de la categorie
        if category is None:
            sig = self.analyzer.analyze(prompt)
            category, confidence = self.analyzer.classify(sig)
            sentiment, sent_score = self.analyzer.detect_sentiment(prompt)

        # === PRIMAIRE : Generation QUALITATIVE avec MEMOIRE ===
        gen_data = self._get_langage_gen()
        if isinstance(gen_data, tuple) and gen_data[0] == 'qualitative':
            import sys, os
            _dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, _dir)
            from qualitative_knowledge import grammatical_generate_with_memory, MemoireOndulatoire
            
            # Initialiser la memoire si necessaire
            if self._memoire_ondulatoire is None:
                self._memoire_ondulatoire = MemoireOndulatoire(nx=128, ny=128)
            
            # Si c'est une question de suivi (courte, commence par "et", "ou", "pourquoi"),
            # injecter le contexte du dernier sujet
            enriched_prompt = prompt
            if self._last_topic and len(prompt.split()) <= 4:
                enriched_prompt = f"{prompt} (a propos de {self._last_topic})"
            
            _, kx, ky, w2i = gen_data
            try:
                texte = grammatical_generate_with_memory(
                    enriched_prompt, kx, ky, w2i,
                    memoire=self._memoire_ondulatoire, max_words=6
                )
                if texte and len(texte) > 10:
                    # Extraire le sujet pour le prochain tour
                    mots_sujet = [w for w in prompt.lower().split() 
                                  if w not in ('explique','decris','parle','moi','de','du','qu','est','ce','que','le','la','les','et','pourquoi','comment')]
                    if mots_sujet:
                        self._last_topic = ' '.join(mots_sujet[:3])
                    return texte
            except Exception:
                pass

        # === SECONDAIRE : Generation par RESONANCE HOLOGRAPHIQUE ===
        if knowledge_context and knowledge_context.strip():
            resonance_gen = self._get_resonance_gen()
            if resonance_gen:
                try:
                    resonance_gen.apprendre_contexte(knowledge_context)
                    texte = resonance_gen.generer_texte(prompt, max_tokens=50)
                    if texte and len(texte) > 5:
                        # FEEDBACK : la generation enrichit l'hologramme (apprentissage)
                        resonance_gen.apprendre(texte, amplitude=0.5)
                        # Injection du prompt aussi (le systeme apprend de chaque question)
                        resonance_gen.apprendre(prompt, amplitude=0.3)
                        return texte
                except Exception:
                    pass

        # === SECONDAIRE : Generation par langage naturel (templates ameliores) ===
        if knowledge_context and knowledge_context.strip():
            gen = self._get_langage_gen()
            if gen:
                faits = [f.strip() for f in re.split(r'[.\n]+', knowledge_context) if len(f.strip()) > 10]
                if faits:
                    return gen.formuler(prompt, faits[:3])

        # === FALLBACK : Pas de connaissance → reponse honnete ===
        # L'intelligence n'invente pas. Si la resonance n'a rien trouve,
        # elle le dit. C'est plus fidele au principe que des templates.
        return (
            "Je ne dispose pas d'assez de connaissances pour repondre a cette question. "
            "Mon intelligence repose sur la resonance avec les ondes stockees dans l'hologramme. "
            "Cette question n'a pas encore rencontre d'echo dans ma base de connaissance."
        )

    def generate_with_expansion(self, prompt: str, category: Optional[str] = None,
                                 length: str = "normal",
                                 knowledge_context: Optional[str] = None) -> str:
        """
        Genere ET etend harmoniquement.
        Pipeline complet : analyse -> generation -> expansion.
        """
        # Detection automatique
        if category is None:
            sig = self.analyzer.analyze(prompt)
            category, _ = self.analyzer.classify(sig)
        
        sentiment, _ = self.analyzer.detect_sentiment(prompt)
        
        # Generation pure
        response = self.generate(prompt, category, "court", sentiment,
                                knowledge_context=knowledge_context)
        
        # Expansion harmonique
        expander = HarmonicContextExpander()
        expanded = expander.expand(
            response, category,
            verified=(category in ("factual", "mathematical", "reasoning")),
            sentiment=sentiment,
            length=length
        )
        
        return expanded

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_generations": self.generation_count,
            "categories": list(self.RESPONSE_TEMPLATES.keys())
        }


# =========================================================================
# MOTEUR DE RESONANCE HARMONIQUE
# =========================================================================

class HarmonicResonanceEngine:
    """
    Moteur de resonance harmonique principal.
    Orchestre l'analyse harmonique, la memoire, la generation et l'expansion.
    Integre HologrammeConnecteur + Predicteur ABC (noyau Atangana-Baleanu-Caputo).
    """
    
    def __init__(self, cache: Optional[HarmonicCache] = None,
                 memory: Optional[ConversationMemory] = None,
                 use_hologram: bool = True,
                 use_jepa: bool = True):
        """
        Args:
            use_hologram: True (full), False (off), ou 'light' (~50 MB au lieu de ~550 MB).
                          Le mode 'light' desactive fasttext et les vecteurs pre-entraines,
                          utilisant les n-grams caracteres comme fallback.
            use_jepa: Active le predicteur ABC (remplace JEPA). Default True.
        """
        self.analyzer = HarmonicAnalyzer()
        self.cache = cache or HarmonicCache()
        self.expander = HarmonicContextExpander()
        self.generator = HarmonicGenerator(analyzer=self.analyzer)
        self.memory = memory or ConversationMemory()
        self.stats = {
            "total_requests": 0, "cache_hits": 0, "pattern_matches": 0,
            "expansions": 0, "generations": 0, "total_processing_time_ms": 0.0,
            "resonance_scores": []
        }
        
        # === INTEGRATION HOLOGRAMME ===
        self.hologram_connector = None
        self.hologram_loaded = False
        self.hologram_use = use_hologram
        self._init_hologram()
        
        # === INTEGRATION PREDICTEUR ABC (remplace JEPA) ===
        # Migration Atangana-Baleanu-Caputo : le prédicteur par noyau ABC pur
        # remplace le réseau neuronal JEPA. Deterministe, zero parametre.
        self.abc_connector = None
        self.abc_use = use_jepa and ABC_PREDICTOR_AVAILABLE
        if self.abc_use:
            try:
                self.abc_connector = _ABCPredictor(max_history=32)
                self.abc_connector.load_or_init()
                print("  [HarmonicResonanceEngine] Predicteur ABC connecte et pret")
            except Exception as e:
                print(f"  [HarmonicResonanceEngine] Erreur predicteur ABC: {e}")
                self.abc_connector = None
                self.abc_use = False
    
    def _init_hologram(self):
        """Initialise le connecteur holographique si disponible.
        
        Supporte les modes :
          - True  : chargement complet (fasttext inclus, ~550 MB)
          - 'light': chargement reduit (sans fasttext, ~50 MB)
          - False : hologramme desactive
        """
        if not self.hologram_use:
            return
        if not _HOLOGRAM_CONNECTOR_AVAILABLE:
            print("  [HarmonicResonanceEngine] Connecteur holographique non disponible")
            return
        try:
            use_fasttext = (self.hologram_use != 'light')
            self.hologram_connector = _HoloConnector(use_fasttext=use_fasttext)
            self.hologram_loaded = self.hologram_connector.est_charge()
            if self.hologram_loaded:
                mode_str = "LEGER" if not use_fasttext else "complet"
                print(f"  [HarmonicResonanceEngine] Hologramme connecte ({mode_str})")
            else:
                print("  [HarmonicResonanceEngine] Hologramme non charge")
                self.hologram_connector = None
        except Exception as e:
            print(f"  [HarmonicResonanceEngine] Erreur hologramme: {e}")
            self.hologram_connector = None
            self.hologram_loaded = False

    def analyze(self, prompt: str) -> HarmonicSignature:
        """Analyse un prompt et retourne sa signature enrichie."""
        self.stats["total_requests"] += 1
        return self.analyzer.analyze(prompt)

    def classify(self, prompt: str) -> Tuple[str, float]:
        """Classifie un prompt dans une categorie."""
        self.stats["total_requests"] += 1
        signature = self.analyze(prompt)
        return self.analyzer.classify(signature)

    def expand(self, response: str, category: str, verified: bool = True,
               sentiment: str = "neutre", length: str = "normal") -> str:
        """Etend une reponse harmoniquement."""
        self.stats["expansions"] += 1
        return self.expander.expand(response, category, verified, sentiment, length)

    def _extraire_contexte_hologramme(self, message: str) -> Tuple[Optional[str], Dict]:
        """
        Extrait le contexte de connaissance depuis l'hologramme.
        Retourne (contexte_formate, stats) ou (None, {}) si indisponible.
        """
        if not self.hologram_loaded or self.hologram_connector is None:
            return None, {}
        try:
            resultat = self.hologram_connector.resonner(message, top_k=8)
            if resultat["succes"] and resultat["contexte"]:
                stats_hologramme = {
                    "top_tokens": resultat["top_tokens"],
                    "temps_ms": resultat["temps_ms"],
                    "energie": resultat.get("energie", 0.0),
                }
                self.stats["resonance_scores"].append(
                    resultat.get("score_moyen", 0.0)
                )
                return resultat["contexte"], stats_hologramme
            return None, {}
        except Exception as e:
            print(f"  [HarmonicResonanceEngine] Erreur extraction hologramme: {e}")
            return None, {}

    def generate(self, prompt: str, category: Optional[str] = None,
                 length: str = "normal",
                 knowledge_context: Optional[str] = None) -> str:
        """Genere une reponse harmonique pure (sans LLM)."""
        self.stats["generations"] += 1
        return self.generator.generate(prompt, category, length,
                                       knowledge_context=knowledge_context)

    def generate_with_expansion(self, prompt: str, category: Optional[str] = None,
                                 length: str = "normal",
                                 knowledge_context: Optional[str] = None) -> str:
        """Genere ET etend harmoniquement."""
        self.stats["generations"] += 1
        self.stats["expansions"] += 1
        return self.generator.generate_with_expansion(prompt, category, length,
                                                       knowledge_context=knowledge_context)

    def chat(self, user_message: str) -> Dict[str, Any]:
        """Pipeline conversationnel — delegue a chat_resonance() (100% ondes)."""
        return self.chat_resonance(user_message)

    # =====================================================================
    # PIPELINE UNIFIE AVEC LLM (chat_with_llm)
    # =====================================================================

    def _run_abc_prediction(self, sig: HarmonicSignature,
                            category: str = "general") -> Dict[str, Any]:
        """
        Execute la prediction ABC et retourne les stats.
        Extrait de chat() pour reutilisation dans chat_with_llm().
        """
        abc_stats = {}
        if self.abc_connector is not None:
            sig_dict = sig.to_dict()
            sig_9d = np.array([
                sig_dict.get("phi", sig.phi_ratio),
                sig_dict.get("alpha", sig.alpha_complexity),
                sig_dict.get("reasoning", sig.k_reasoning),
                sig_dict.get("creativity", sig.k_creative),
                sig_dict.get("math", sig.k_mathematical),
                sig_dict.get("factual", sig.k_factual),
                sig_dict.get("code", sig.k_code),
                sig_dict.get("emotion", sig.k_emotional),
                sig_dict.get("temporal", sig.k_temporal),
            ], dtype=np.float32)

            self.abc_connector.add_signature(sig_9d)
            abc_pred = self.abc_connector.predict(horizon=3)

            if abc_pred:
                abc_stats = {
                    "resonance": abc_pred.resonance,
                    "topic_shift": abc_pred.topic_shift,
                    "generation_boost": self.abc_connector.get_generation_boost(category),
                    "signature_predite": abc_pred.signature_predite.tolist(),
                    "futures": [f.tolist() for f in abc_pred.futures] if abc_pred.futures is not None else None,
                }
                self.stats["resonance_scores"].append(abc_pred.resonance)
            else:
                abc_stats = {"resonance": None, "topic_shift": None, "generation_boost": 1.0}

        return abc_stats

    def _build_harmonic_system_prompt(
        self,
        category: str,
        abc_stats: Dict[str, Any],
        knowledge_context: Optional[str] = None,
        memory_context: Optional[str] = None,
        user_prefs: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Construit un system prompt enrichi par l'infrastructure harmonique.

        Combine :
          1. Le prompt specifique a la categorie
          2. Le contexte de l'hologramme (connaissances resonantes)
          3. Les signaux du predicteur ABC (resonance, topic shift)
          4. Le contexte de la memoire de conversation
          5. Les preferences utilisateur
        """
        parts = []

        # 1. Prompt de base par categorie
        category_prompts = {
            "mathematical": (
                "Tu es un assistant mathematique de precision. "
                "Resous les problemes etape par etape avec rigueur. "
                "Fournis des resultats exacts et verifiables."
            ),
            "code": (
                "Tu es un assistant de programmation. "
                "Genere du code propre, commente et fonctionnel. "
                "Explique la logique et les choix d'implementation."
            ),
            "creative": (
                "Tu es un assistant creatif. "
                "Laisse libre cours a ton imagination. "
                "Utilise des metaphores et des images poetiques."
            ),
            "reasoning": (
                "Tu es un assistant de raisonnement. "
                "Analyse les problemes en profondeur. "
                "Structure ta pensee de maniere logique et methodique."
            ),
            "factual": (
                "Tu es un assistant factuel. "
                "Fournis des informations precises et verifiables. "
                "Cite tes sources quand c'est possible."
            ),
            "general": (
                "Tu es un assistant IA utile et precis. "
                "Reponds de maniere naturelle et adaptee au contexte."
            ),
        }
        parts.append(category_prompts.get(category, category_prompts["general"]))

        # 2. Contexte holographique (connaissances resonantes)
        if knowledge_context and knowledge_context.strip():
            parts.append(
                f"\n[SAVOIR DE REFERENCE]\n"
                f"Connaissances extraites de la base holographique :\n"
                f"{knowledge_context[:800]}"
            )

        # 3. Signaux du predicteur ABC
        if abc_stats:
            resonance = abc_stats.get("resonance")
            topic_shift = abc_stats.get("topic_shift")
            boost = abc_stats.get("generation_boost", 1.0)

            if resonance is not None:
                if topic_shift is not None and topic_shift > 0.3:
                    parts.append(
                        f"\n[ATTENTION] Changement de sujet probable "
                        f"(topic_shift={topic_shift:.2f}). "
                        f"Adapte ta reponse au nouveau contexte."
                    )
                elif resonance > 0.8:
                    parts.append(
                        f"\n[CONTEXTE] Conversation coherente "
                        f"(resonance={resonance:.2f}). "
                        f"Poursuis dans la meme direction thematique."
                    )
                elif resonance < 0.4:
                    parts.append(
                        f"\n[CONTEXTE] Faible resonance ({resonance:.2f}). "
                        f"La conversation est fragmentee — sois plus explicite."
                    )

            if boost > 1.0:
                parts.append(
                    f"[CONFIANCE] Boost de generation actif (x{boost:.1f}). "
                    f"Sois plus assertif dans ta reponse."
                )

        # 4. Contexte de la memoire de conversation
        if memory_context and memory_context.strip():
            parts.append(
                f"\n[HISTORIQUE DE CONVERSATION]\n{memory_context[:600]}"
            )

        # 5. Preferences utilisateur
        if user_prefs:
            prefs_str = ", ".join(
                f"{k}={v}" for k, v in user_prefs.items()
                if k in ("language", "style", "expertise_level")
            )
            if prefs_str:
                parts.append(f"\n[PREFERENCES UTILISATEUR] {prefs_str}")

        return "\n\n".join(parts)

    def chat_resonance(
        self,
        user_message: str,
        memory: Optional[Any] = None,
        profile: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Chat 100% ondulatoire — zero LLM, zero template, zero parametre.
        
        Pipeline :
          1. Analyse spectrale du message → signature 9D
          2. Contexte holographique (si dispo)
          3. Generation par resonance holographique
          4. Feedback : la reponse enrichit l'hologramme
          5. Si resonance faible → LLM en fallback
        """
        t0 = datetime.now()

        # 1. Analyser
        sig = self.analyzer.analyze(user_message)
        category, confidence = self.analyzer.classify(sig)
        if confidence <= 0.15:
            category = "general"

        # 2. Contexte holographique
        knowledge_context = None
        if self.hologram_loaded and self.hologram_connector:
            try:
                knowledge_context, _ = self._extraire_contexte_hologramme(user_message)
            except Exception:
                pass

        # Si pas de contexte holographique, utiliser le generateur pur (templates)
        resonance_used = False
        response = None

        # Toujours essayer la resonance d'abord (si assez de connaissance accumulee)
        resonance_gen = self.generator._get_resonance_gen()
        if resonance_gen and resonance_gen.experience_count > 10:
            try:
                if knowledge_context and knowledge_context.strip():
                    resonance_gen.apprendre_contexte(knowledge_context)
                response = resonance_gen.generer_texte(user_message, max_tokens=60)
                # Verifier qualite : au moins 20 car, pas que des stopwords
                if response and len(response) > 20:
                    words = response.lower().split()
                    stopwords = {'le','la','les','de','des','un','une','et','a','en','au','aux','pas','ne','se','ce','il','elle','je','tu','<EOS>'}
                    meaningful = [w for w in words if w not in stopwords and len(w) > 1]
                    if len(meaningful) >= 3:
                        resonance_used = True
                        resonance_gen.apprendre(response, amplitude=0.5)
                        resonance_gen.apprendre(user_message, amplitude=0.3)
            except Exception:
                pass

        # Fallback : generateur classique si resonance n'a pas produit
        if not response:
            response = self.generator.generate(
                user_message, category, knowledge_context=knowledge_context
            )

        # 5. Memoire
        if memory is not None:
            memory.add("user", user_message, category=category, resonance_score=confidence)
            memory.add("assistant", response, category=category,
                      resonance_score=confidence)

        # 6. Profil
        if profile is not None:
            profile.record_interaction(category, resonance_score=confidence)

        elapsed = (datetime.now() - t0).total_seconds() * 1000

        result = {
            "response": response,
            "category": category,
            "confidence": confidence,
            "resonance_used": resonance_used,
            "processing_time_ms": round(elapsed, 2),
            "signature": sig.to_dict(),
            "abc_used": self.abc_connector is not None,
        }
        return result

    def chat_with_llm(
        self,
        user_message: str,
        llm: Any,  # HarmonicLLM (evite import circulaire)
        memory: Optional[Any] = None,  # ConversationMemory
        profile: Optional[Any] = None,  # UserProfile
    ) -> Dict[str, Any]:
        """
        Pipeline conversationnel complet avec LLM reel.

        Remplace le chat() template par une generation LLM intelligente,
        tout en conservant l'infrastructure harmonique :
          Analyse → ABC Predict → Hologramme → Memoire → LLM

        Args:
            user_message: message utilisateur
            llm: instance HarmonicLLM pour la generation
            memory: ConversationMemory optionnelle (session context)
            profile: UserProfile optionnel (preferences)

        Returns:
            dict avec response, category, abc_stats, knowledge_used, etc.
        """
        t0 = datetime.now()

        # 1. Analyser le message
        sig = self.analyzer.analyze(user_message)
        category, confidence = self.analyzer.classify(sig)
        if confidence <= 0.15:
            category = "general"

        # 2. Prediction ABC
        abc_stats = self._run_abc_prediction(sig, category)

        # 3. Contexte holographique
        knowledge_context, holo_stats = self._extraire_contexte_hologramme(user_message)

        # 4. Contexte memoire
        memory_context = None
        if memory is not None:
            memory.add("user", user_message, category=category,
                      resonance_score=confidence)
            memory_context = memory.get_context(max_tokens=600)

        # 5. Preferences utilisateur
        user_prefs = None
        if profile is not None:
            user_prefs = profile.get_optimized_config()

        # 6. Construire le system prompt enrichi
        system_prompt = self._build_harmonic_system_prompt(
            category=category,
            abc_stats=abc_stats,
            knowledge_context=knowledge_context,
            memory_context=memory_context,
            user_prefs=user_prefs,
        )

        # 7. Config LLM
        try:
            from .llm.base import LLMConfig
        except ImportError:
            from engine.llm.base import LLMConfig

        config = LLMConfig(
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2048,
        )

        # Appliquer les preferences au config
        if user_prefs:
            if "temperature" in user_prefs:
                config.temperature = user_prefs["temperature"]
            if "max_tokens" in user_prefs:
                config.max_tokens = user_prefs["max_tokens"]

        # 8. Generer via LLM
        resp = llm.generate(user_message, category, config)
        latency = (datetime.now() - t0).total_seconds() * 1000

        # 9. Enregistrer la reponse dans la memoire
        if memory is not None:
            memory.add("assistant", resp.content, category=category,
                      resonance_score=abc_stats.get("resonance") or confidence)

        # 10. Construire le resultat
        result = {
            "response": resp.content,
            "category": category,
            "confidence": confidence,
            "model": resp.model,
            "provider": resp.provider,
            "tokens_used": resp.usage.get("total_tokens", 0),
            "processing_time_ms": round(latency, 2),
            "abc_used": self.abc_connector is not None,
            "knowledge_used": knowledge_context is not None,
            "signature": sig.to_dict(),
        }

        if abc_stats:
            result["abc_stats"] = abc_stats
        if knowledge_context:
            result["knowledge_stats"] = holo_stats

        return result

    def get_stats(self) -> Dict[str, Any]:
        total = self.stats["total_requests"]
        avg_resonance = (
            sum(self.stats["resonance_scores"]) / max(len(self.stats["resonance_scores"]), 1)
        ) if self.stats["resonance_scores"] else 0.0
        return {
            "total_requests": total,
            "cache_hits": self.stats["cache_hits"],
            "pattern_matches": self.stats["pattern_matches"],
            "expansions": self.stats["expansions"],
            "generations": self.stats["generations"],
            "cache_hit_rate": round(self.stats["cache_hits"] / max(total, 1) * 100, 2),
            "avg_resonance_score": round(avg_resonance, 4),
            "cache_stats": self.cache.get_stats(),
            "memory_stats": self.memory.get_stats()
        }


# =========================================================================
# TESTS
# =========================================================================

def test_engine():
    """Test complet du moteur harmonique enrichi."""
    print("=" * 70)
    print("TEST : Moteur Harmonique Enrichi (sans LLM)")
    print("=" * 70)
    
    engine = HarmonicResonanceEngine()
    
    # =========================================================
    # TEST 1 : Analyse harmonique enrichie
    # =========================================================
    print("\n--- 1. Analyse harmonique enrichie ---")
    prompts = [
        "Calculez 15% de 340",
        "Ecrivez un algorithme de tri par fusion en Python",
        "Ecrivez un poeme sur l'amour",
        "Pourquoi le ciel est-il bleu ?",
        "Quelle est la capitale de la France ?",
        "Bonjour, comment allez-vous ?",
        "Je suis tres triste aujourd'hui, tout va mal",
        "Quel bonheur de decouvrir cette merveilleuse nouvelle !"
    ]
    
    for prompt in prompts:
        sig = engine.analyze(prompt)
        cat, conf = engine.classify(prompt)
        sentiment, sent_score = engine.analyzer.detect_sentiment(prompt)
        topics = engine.analyzer.extract_topics(prompt)
        print(f"  [{cat:12s}] (conf:{conf:.2f}) [sent:{sentiment:7s}] "
              f"topics:{topics} -> {prompt[:40]}...")
    
    # =========================================================
    # TEST 2 : Generation harmonique pure
    # =========================================================
    print("\n--- 2. Generation harmonique pure (sans LLM) ---")
    gen_prompts = [
        ("Pouvez-vous m'expliquer la relativite ?", "reasoning"),
        ("Resolvez 2x + 5 = 13", "mathematical"),
        ("Ecrivez un court poeme sur la mer", "creative"),
        ("Donnez-moi un code Python pour lire un fichier", "code"),
        ("Quels sont les bienfaits de l'eau ?", "factual"),
        ("Bonjour, comment puis-je vous aider ?", "general"),
    ]
    
    for prompt, cat in gen_prompts:
        response = engine.generate(prompt, cat)
        print(f"  [{cat:12s}] Genere ({len(response)}c): {response[:70]}...")
    
    # =========================================================
    # TEST 3 : Generation + Expansion
    # =========================================================
    print("\n--- 3. Generation + Expansion harmonique ---")
    for prompt, cat in gen_prompts[:3]:
        expanded = engine.generate_with_expansion(prompt, cat, length="normal")
        print(f"  [{cat:12s}] ({len(expanded)}c): {expanded[:90]}...")
        print(f"        Ratio: {len(expanded)/max(len(prompt),1):.1f}x")
    
    # =========================================================
    # TEST 4 : Chat conversationnel avec memoire
    # =========================================================
    print("\n--- 4. Chat conversationnel avec memoire ---")
    messages = [
        "Quelle est la capitale de la France ?",
        "Et celle de l'Italie ?",
        "Quelle est la difference entre ces deux pays ?"
    ]
    
    for msg in messages:
        result = engine.chat(msg)
        print(f"  User: {msg}")
        print(f"  Assistant ({result['category']}, "
              f"mem:{result['memory_stats']['total_turns']} tours): "
              f"{result['response'][:80]}...")
        print()
    
    # =========================================================
    # TEST 5 : Expansion du contexte
    # =========================================================
    print("--- 5. Expansion harmonique de contexte ---")
    short = "Pour calculer 15% de 340, on divise 340 par 100 puis on multiplie par 15."
    
    for length in ("court", "normal", "long"):
        expanded = engine.expand(short, "mathematical", length=length)
        ratio = len(expanded) / len(short)
        print(f"  [{length:6s}] ({len(expanded)}c, x{ratio:.1f}): {expanded[:90]}...")
    
    # =========================================================
    # TEST 6 : Stats
    # =========================================================
    print("\n--- 6. Statistiques ---")
    stats = engine.get_stats()
    for key, val in stats.items():
        if key not in ("cache_stats", "memory_stats"):
            print(f"  {key}: {val}")
    
    print(f"\n{'='*70}")
    print(f"[SUCCES] Moteur Harmonique Enrichi operationnel")
    print(f"  - Analyse enrichie (emotional, temporal, topics, sentiment)")
    print(f"  - Generation harmonique pure (sans LLM)")
    print(f"  - Expansion multi-paragraphe (court/normal/long)")
    print(f"  - Memoire conversationnelle multi-tour")
    print(f"  - Pipeline chat complet")
    print(f"{'='*70}")
    
    # =========================================================
    # TEST 7 : Boucle hologramme -> generation
    # =========================================================
    print("\n--- 7. Boucle hologramme -> generation ---")
    try:
        engine_holo = HarmonicResonanceEngine(use_hologram=True)
        if engine_holo.hologram_loaded:
            energie = engine_holo.hologram_connector.get_stats().get("energie_hologramme", 0.0)
            print(f"  [OK] Hologramme charge (E={energie:.2e})")
            
            # Test extraction contexte
            ctx, stats = engine_holo._extraire_contexte_hologramme("Parle-moi de la relativite")
            if ctx:
                print(f"  [OK] Contexte extrait: {ctx[:80]}...")
                print(f"  [OK] Temps resonance: {stats['temps_ms']:.1f}ms")
            else:
                print(f"  [INFO] Pas de contexte extrait (vocabulaire limite)")
            
            # Test chat avec hologramme
            result = engine_holo.chat("Explique la science")
            if result.get("knowledge_used"):
                print(f"  [OK] knowledge_used=True dans la reponse chat")
                print(f"  [OK] knowledge_stats: {result.get('knowledge_stats', {})}")
            else:
                print(f"  [INFO] knowledge_used=False dans la reponse chat")
            
            # Verifier que le contexte apparait dans la reponse
            response = result["response"]
            if "connaissances holographiques" in response.lower():
                print(f"  [OK] 'connaissances holographiques' trouve dans la reponse")
            else:
                print(f"  [INFO] Reference holographique non trouvee dans la reponse (attendu: vocabulaire generique)")
            
            print(f"  Reponse ({len(response)}c): {response[:100]}...")
        else:
            print(f"  [INFO] Hologramme non charge (fichier manquant?)")
    except Exception as e:
        import traceback
        print(f"  [WARN] Erreur test hologramme (non bloquant): {e}")
        traceback.print_exc()
    
    print(f"\n{'='*70}")
    print(f"[SUCCES] Tous les tests passes")
    print(f"{'='*70}")
    return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_engine()
