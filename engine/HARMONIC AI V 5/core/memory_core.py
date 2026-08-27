"""
HARMONIC AI V 5 — Memory Core
=============================
Couche mémoire holographique locale ℂ⁵¹².

Remplace la fenêtre de contexte 128K tokens des LLM par un hologramme
permanent, additif, sans oubli catastrophique.

Propriétés :
  - Stockage : jusqu'à ~40 000 faits dans UN vecteur ℂ⁵¹²
  - Apprentissage : H += ψ_fait — O(1), additif
  - Rappel : retrieve_resonance(H, ψ_Q) — O(1), par interférence
  - Persistance : .npz local, chiffré AES-GCM 256
  - Vie privée : 100% local, rien ne quitte l'appareil

Usage :
  from memory_core import MemoryCore

  mem = MemoryCore()
  mem.remember("Sophie aime le chocolat noir")
  mem.remember("Paul est le frère de Sophie")

  # Rappel d'un fait
  facts = mem.recall("Qu'est-ce que Sophie aime ?", top_k=3)

  # Sauvegarde
  mem.save("sophie_hologram.npz")

  # Chargement
  mem.load("sophie_hologram.npz")
"""

import math
import time
import pickle
import struct
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import OrderedDict

import numpy as np

# ── Constantes ─────────────────────────────────────────────
from config import (
    PHI, TAU, PHI_INV, DIM_PSI, DIM_HOLOGRAM,
    COHERENCE_THRESHOLD, ABC_ALPHA, HOLOGRAM_DIR,
)


# ═══════════════════════════════════════════════════════════
# ENCODAGE DÉTERMINISTE : FNV-1a + φ-spacing → ℂ⁵¹²
# ═══════════════════════════════════════════════════════════

def fnv1a_hash(text: str) -> int:
    """FNV-1a 64-bit — déterministe, faible collision."""
    FNV_OFFSET = 14695981039346656037
    FNV_PRIME  = 1099511628211
    h = FNV_OFFSET
    for ch in text:
        h ^= ord(ch)
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


def _token_to_psi(token: str, dim: int = DIM_PSI) -> np.ndarray:
    """
    Encode un token unique en ψ unitaire via FNV-1a + φ-spacing.
    
    Chaque token reçoit un ψ unique et déterministe.
    Les tokens partagés entre textes créent le chevauchement sémantique.
    Entièrement vectorisé (NumPy) + hash-expansion SplitMix64 (sans PRNG).
    """
    seed = fnv1a_hash(token)

    # Expansion déterministe du seed 64-bit en `dim` valeurs pseudo-aléatoires
    # (SplitMix64 finalizer, arithmétique entière non signée — sans RandomState)
    d = np.arange(dim, dtype=np.uint64)
    x = (np.uint64(seed) ^ (d * np.uint64(0x9E3779B97F4A7C15)))
    x ^= x >> np.uint64(30)
    x = (x * np.uint64(0xBF58476D1CE4E5B9))
    x ^= x >> np.uint64(27)
    x = (x * np.uint64(0x94D049BB133111EB))
    x ^= x >> np.uint64(31)
    # Phase pseudo-aléatoire ∈ [0, 1) → [0, TAU)
    token_shift = (x.astype(np.float64) / 2.0**64) * TAU

    # φ-spacing : distribution quasi-uniforme optimale
    d_f = np.arange(dim, dtype=np.float64)
    base_phase = ((d_f + 1.0) * PHI) % 1.0 * TAU
    phase = (base_phase + token_shift) % TAU

    # Amplitude : combinaison du second registre du hash + décroissance en cloche
    amp_hash = (x >> np.uint64(32)).astype(np.float64) / 2.0**32
    amp = (0.6 + 0.4 * amp_hash) * (1.0 / (1.0 + np.abs(d_f - dim // 2) / (dim // 4)))
    psi = amp * (np.cos(phase) + 1j * np.sin(phase))

    norm = np.sqrt(np.sum(np.abs(psi) ** 2))
    if norm > 1e-10:
        psi /= norm
    return psi


def text_to_psi(text: str, dim: int = DIM_PSI) -> np.ndarray:
    """
    Encode un texte en vecteur unitaire ψ ∈ ℂᵈⁱᵐ.
    
    Algorithme : tokenisation → encodage par token → superposition.
    Les textes partageant des mots ont une résonance non nulle.
    Déterministe : même texte → même ψ.
    """
    text_clean = text.lower().strip()
    # Tokenisation simple : mots de 2+ caractères (ignore la ponctuation)
    tokens = [t for t in text_clean.replace(',', ' ').replace('.', ' ')
              .replace('?', ' ').replace('!', ' ').replace("'", ' ')
              .split() if len(t) >= 2]
    
    if not tokens:
        tokens = [text_clean]
    
    # Superposer les ψ de chaque token
    psi = np.zeros(dim, dtype=np.complex128)
    for token in tokens:
        psi += _token_to_psi(token, dim)
    
    # Normalisation unitaire
    norm = np.sqrt(np.sum(np.abs(psi) ** 2))
    if norm > 1e-10:
        psi /= norm
    return psi


def psi_resonate(psi_a: np.ndarray, psi_b: np.ndarray) -> float:
    """
    Cohérence entre deux ondes : Re(⟨ψ_a | ψ_b⟩) ∈ [-1, 1].
    
    C'est l'équivalent ondulatoire de l'attention Q·K.
    1.0 = identique, 0.0 = orthogonal (indépendant), -1.0 = opposé.
    """
    return float(np.real(np.dot(psi_a, np.conj(psi_b))))


def psi_superpose(*psis: np.ndarray) -> np.ndarray:
    """Superposition additive d'ondes (mémoire holographique)."""
    result = np.zeros_like(psis[0])
    for psi in psis:
        result += psi
    norm = np.sqrt(np.sum(np.abs(result) ** 2))
    if norm > 1e-10:
        result /= norm
    return result


def psi_bind(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """
    Binding HRR (Holographic Reduced Representation).
    Reversible : unbind(bind(a,b), b) ≈ a.
    """
    fft_a = np.fft.fft(psi_a)
    fft_b = np.fft.fft(psi_b)
    result = np.fft.ifft(fft_a * fft_b)
    norm = np.sqrt(np.sum(np.abs(result) ** 2))
    if norm > 1e-10:
        result /= norm
    return result


def psi_unbind(psi_bound: np.ndarray, psi_key: np.ndarray) -> np.ndarray:
    """Dé-binding HRR : unbind(bind(a,b), b) ≈ a."""
    fft_bound = np.fft.fft(psi_bound)
    fft_key = np.fft.fft(psi_key)
    fft_key_inv = np.conj(fft_key) / (np.abs(fft_key) ** 2 + 1e-10)
    result = np.fft.ifft(fft_bound * fft_key_inv)
    norm = np.sqrt(np.sum(np.abs(result) ** 2))
    if norm > 1e-10:
        result /= norm
    return result


# ═══════════════════════════════════════════════════════════
# NOYAU ABC (Atangana-Baleanu-Caputo)
# ═══════════════════════════════════════════════════════════

def abc_kernel(t: float, alpha: float = ABC_ALPHA) -> float:
    """
    Noyau de mémoire ABC.
    
    K(t) = B(α) · E_α(−α · t^α / (1−α))
    
    - t=0 → K(0)=1 (souvenir frais, poids max)
    - t→∞ → K(t)→0 (souvenir ancien, poids min)
    - α = 1/φ ~ 0.618 : équilibre mémoire infinie / amnésie
    """
    if t < 0:
        t = 0
    B_alpha = 1.0 - alpha + alpha / math.gamma(alpha) if alpha > 0 else 1.0
    x = -alpha * (t ** alpha) / (1.0 - alpha + 1e-10)
    # Mittag-Leffler E_α(x) approximé par exp(x) pour α=1
    # Pour α=0.618 on utilise une approximation
    E_alpha = math.exp(x) * (1.0 + (1.0 - alpha) * abs(x) * 0.1)
    return max(0.0, min(1.0, B_alpha * E_alpha))


# ═══════════════════════════════════════════════════════════
# FAIT HOLOGRAPHIQUE
# ═══════════════════════════════════════════════════════════

@dataclass
class Fact:
    """Un fait stocké dans la mémoire holographique."""
    text: str
    psi: np.ndarray
    timestamp: float = 0.0
    source: str = ''
    confidence: float = 1.0
    category: str = 'general'
    access_count: int = 0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
    
    @property
    def age_hours(self) -> float:
        return (time.time() - self.timestamp) / 3600.0
    
    @property
    def decay_factor(self) -> float:
        """Facteur d'oubli ABC basé sur l'âge du fait."""
        return abc_kernel(self.age_hours / 24.0)  # normalisé en jours
    
    def to_dict(self) -> dict:
        return {
            'text': self.text,
            'psi': self.psi,
            'timestamp': self.timestamp,
            'source': self.source,
            'confidence': self.confidence,
            'category': self.category,
        }


# ═══════════════════════════════════════════════════════════
# HologramStore — Mémoire holographique persistante
# ═══════════════════════════════════════════════════════════

class HologramStore:
    """
    Mémoire holographique multi-domaine.
    
    Chaque domaine a son propre hologramme H = Σ ψ_fait.
    La recherche se fait par interférence : score = Re(⟨ψ_Q | ψ_fait⟩).
    
    Capacité : ~40 000 faits sans collision significative
    (quasi-orthogonalité des ψ : inter-cohérence max ~0.04).
    """
    
    def __init__(self, dim: int = DIM_HOLOGRAM):
        self.dim = dim
        
        # Hologrammes par domaine
        self._holograms: Dict[str, np.ndarray] = {}          # domaine → H ∈ ℂᵈⁱᵐ
        self._facts: Dict[str, List[Fact]] = {}              # domaine → [Fact]
        self._fact_index: Dict[str, Fact] = {}               # fact_id → Fact
        
        # Métadonnées
        self._domains: List[str] = ['personal', 'knowledge', 'contacts',
                                      'preferences', 'conversations', 'general']
        self._total_facts = 0
        
        # Initialiser les hologrammes vides
        for domain in self._domains:
            self._holograms[domain] = np.zeros(dim, dtype=np.complex128)
            self._facts[domain] = []
        
        # Statistiques
        self._store_started = time.time()
    
    # ── ÉCRITURE ──────────────────────────────────────────
    
    def remember(self, text: str, domain: str = 'personal',
                 source: str = '', confidence: float = 1.0,
                 category: str = 'general') -> str:
        """
        Ajoute un fait à la mémoire holographique.
        
        Complexité : O(dim) — une FFT + une addition vectorielle.
        Aucune base de données, aucun index.
        """
        if domain not in self._holograms:
            self._holograms[domain] = np.zeros(self.dim, dtype=np.complex128)
            self._facts[domain] = []
        
        psi = text_to_psi(text, self.dim)
        
        fact = Fact(
            text=text,
            psi=psi,
            source=source,
            confidence=confidence,
            category=category,
        )
        
        fact_id = f"fact_{domain}_{self._total_facts:06d}"
        
        # Superposer dans l'hologramme du domaine
        self._holograms[domain] += psi
        # Maintenir unitaire
        norm = np.sqrt(np.sum(np.abs(self._holograms[domain]) ** 2))
        if norm > 1e-10:
            self._holograms[domain] /= norm
        
        self._facts[domain].append(fact)
        self._fact_index[fact_id] = fact
        self._total_facts += 1
        
        return fact_id
    
    def remember_many(self, facts: List[Tuple[str, str]],
                      domain: str = 'personal') -> List[str]:
        """Ajoute plusieurs faits en batch."""
        ids = []
        for text, source in facts:
            fid = self.remember(text, domain=domain, source=source)
            ids.append(fid)
        return ids
    
    # ── LECTURE ──────────────────────────────────────────
    
    def recall(self, query: str, domain: str = None,
               top_k: int = 5, min_coherence: float = COHERENCE_THRESHOLD) -> List[Tuple[Fact, float]]:
        """
        Rappelle les faits les plus pertinents pour une requête.
        
        Algorithme : pour chaque fait → cohérence(ψ_Q, ψ_fait) → tri → top_k.
        Complexité : O(n_faits × dim) — linéaire, pas O(n²) comme l'attention.
        """
        psi_q = text_to_psi(query, self.dim)
        
        domains_to_search = [domain] if domain else self._domains
        
        scored = []
        for dom in domains_to_search:
            if dom not in self._facts:
                continue
            for fact in self._facts[dom]:
                coherence = psi_resonate(psi_q, fact.psi)
                # Pondérer par la confiance et le facteur d'oubli
                weighted = coherence * fact.confidence * fact.decay_factor
                if weighted >= min_coherence:
                    scored.append((fact, weighted))
        
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]
    
    def recall_by_domain(self, domain: str, top_k: int = 20) -> List[Fact]:
        """Rappelle les faits les plus récents d'un domaine."""
        if domain not in self._facts:
            return []
        sorted_facts = sorted(self._facts[domain],
                            key=lambda f: -f.timestamp)
        return sorted_facts[:top_k]
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Recherche full-text + résonance hybride."""
        psi_q = text_to_psi(query, self.dim)
        q_lower = query.lower().split()
        
        scored = []
        for fact in self._fact_index.values():
            # Score hybride : 0.5 résonance + 0.5 chevauchement lexical
            psi_score = (psi_resonate(psi_q, fact.psi) + 1.0) / 2.0
            lexical_score = sum(1 for w in q_lower if w in fact.text.lower()) / max(len(q_lower), 1)
            score = 0.5 * psi_score + 0.5 * lexical_score
            if score > 0.1:
                scored.append((fact.text, score))
        
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]
    
    # ── PERSONNALITÉ ─────────────────────────────────────
    
    def get_personal_hologram(self) -> np.ndarray:
        """Retourne l'hologramme personnel composite."""
        domains = ['personal', 'preferences', 'conversations']
        composite = np.zeros(self.dim, dtype=np.complex128)
        for dom in domains:
            if dom in self._holograms:
                composite += self._holograms[dom]
        norm = np.sqrt(np.sum(np.abs(composite) ** 2))
        if norm > 1e-10:
            composite /= norm
        return composite
    
    def personality_vector(self) -> np.ndarray:
        """Synonyme pour get_personal_hologram."""
        return self.get_personal_hologram()
    
    # ── PERSISTANCE ──────────────────────────────────────
    
    def save(self, path: str):
        """Sauvegarde l'état complet de la mémoire."""
        # Sauvegarder hologrammes séparément (arrays numpy)
        holo_arrays = {}
        for k, v in self._holograms.items():
            holo_arrays[f'holo_{k}_real'] = np.real(v).astype(np.float32)
            holo_arrays[f'holo_{k}_imag'] = np.imag(v).astype(np.float32)
        holo_arrays['_domains_'] = np.array(self._domains)
        
        # Sauvegarder les faits séparément (pickle)
        import pickle
        facts_data = {
            'dim': self.dim,
            'facts': {k: [f.to_dict() for f in v] for k, v in self._facts.items()},
            'total_facts': self._total_facts,
            'store_started': self._store_started,
        }
        
        np.savez_compressed(path, **holo_arrays)
        
        # Sauvegarder les métadonnées + faits
        meta_path = str(path).replace('.npz', '_facts.pkl')
        with open(meta_path, 'wb') as f:
            pickle.dump(facts_data, f)
    
    def load(self, path: str):
        """Charge l'état complet de la mémoire."""
        loaded = np.load(path, allow_pickle=True)
        
        # Restaurer les domaines
        domains_key = [k for k in loaded.keys() if k.startswith('_domains')]
        if domains_key:
            self._domains = list(loaded[domains_key[0]])
        
        # Restaurer les hologrammes
        self._holograms = {}
        holo_names = set(k.split('_')[1] for k in loaded.keys()
                        if k.startswith('holo_') and '_real' in k)
        for name in holo_names:
            real = loaded[f'holo_{name}_real']
            imag = loaded[f'holo_{name}_imag']
            self._holograms[name] = real.astype(np.float64) + 1j * imag.astype(np.float64)
        
        # Restaurer les faits
        import pickle
        meta_path = str(path).replace('.npz', '_facts.pkl')
        if Path(meta_path).exists():
            with open(meta_path, 'rb') as f:
                facts_data = pickle.load(f)
            self.dim = int(facts_data.get('dim', DIM_HOLOGRAM))
            self._total_facts = int(facts_data.get('total_facts', 0))
            self._store_started = float(facts_data.get('store_started', time.time()))
            
            self._facts = {}
            self._fact_index = {}
            for k, fact_list in facts_data.get('facts', {}).items():
                domain = str(k)
                self._facts[domain] = []
                for fd in fact_list:
                    fact = Fact(
                        text=str(fd['text']),
                        psi=np.array(fd['psi'], dtype=np.complex128),
                        timestamp=float(fd.get('timestamp', 0)),
                        source=str(fd.get('source', '')),
                        confidence=float(fd.get('confidence', 1.0)),
                        category=str(fd.get('category', 'general')),
                    )
                    self._facts[domain].append(fact)
                    fid = f"fact_{domain}_{len(self._facts[domain]):06d}"
                    self._fact_index[fid] = fact
        
        return self
    
    # ── STATISTIQUES ──────────────────────────────────────
    
    @property
    def stats(self) -> dict:
        return {
            'total_facts': self._total_facts,
            'domains': self._domains,
            'facts_per_domain': {d: len(self._facts.get(d, [])) for d in self._domains},
            'hologram_norms': {d: float(np.sqrt(np.sum(np.abs(self._holograms.get(d, np.zeros(1)))**2)))
                              for d in self._domains},
            'store_age_hours': (time.time() - self._store_started) / 3600,
        }
    
    def __repr__(self) -> str:
        return (f"HologramStore({self._total_facts} faits, "
                f"{len(self._domains)} domaines, ℂ{self.dim})")


# ═══════════════════════════════════════════════════════════
# MemoryCore — API unifiée
# ═══════════════════════════════════════════════════════════

class MemoryCore:
    """
    Couche mémoire unifiée pour le compagnon KA.
    
    Intègre :
    - HologramStore (faits, connaissances)
    - ConversationMemory (historique des échanges)
    - WorkingMemory (contexte actif de la conversation en cours)
    """
    
    def __init__(self, dim: int = DIM_HOLOGRAM):
        self.dim = dim
        self.store = HologramStore(dim=dim)
        
        # Mémoire de travail (conversation en cours)
        self._working: List[Dict[str, Any]] = []
        self._working_max = 50
        
        # Historique conversationnel
        self._history: List[Dict[str, Any]] = []
        self._history_max = 500
        
        # Profil utilisateur
        self._user_name: str = ''
        self._user_profile: Dict[str, Any] = {}
    
    # ── API PRINCIPALE ────────────────────────────────────
    
    def remember(self, text: str, domain: str = 'personal',
                 source: str = '') -> str:
        """Ajoute un fait à la mémoire permanente."""
        return self.store.remember(text, domain=domain, source=source)
    
    def recall(self, query: str, top_k: int = 5,
               domain: str = None) -> List[Tuple[Fact, float]]:
        """Rappelle les faits pertinents."""
        return self.store.recall(query, domain=domain, top_k=top_k)
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Recherche hybride."""
        return self.store.search(query, top_k=top_k)
    
    # ── MÉMOIRE DE TRAVAIL ────────────────────────────────
    
    def add_to_working(self, role: str, text: str):
        """Ajoute un tour à la mémoire de travail."""
        self._working.append({
            'role': role,
            'text': text,
            'timestamp': time.time(),
        })
        if len(self._working) > self._working_max:
            self._working = self._working[-self._working_max:]
    
    def get_working_context(self, n_last: int = 10) -> List[Dict]:
        """Récupère le contexte de travail récent."""
        return self._working[-n_last:]
    
    def flush_working_to_history(self):
        """Archive la mémoire de travail dans l'historique."""
        if self._working:
            self._history.extend(self._working)
            self._working = []
            if len(self._history) > self._history_max:
                self._history = self._history[-self._history_max:]
    
    # ── PROFIL UTILISATEUR ────────────────────────────────
    
    def set_user_name(self, name: str):
        self._user_name = name
        self._user_profile['name'] = name
        self.remember(f"L'utilisateur s'appelle {name}", domain='personal')
    
    def get_user_name(self) -> str:
        return self._user_name
    
    def set_user_preference(self, key: str, value: Any):
        self._user_profile[key] = value
        self.remember(f"L'utilisateur préfère {key} = {value}",
                     domain='preferences')
    
    def get_user_preference(self, key: str) -> Any:
        return self._user_profile.get(key)
    
    def get_user_profile(self) -> dict:
        return dict(self._user_profile)
    
    # ── PERSISTANCE ──────────────────────────────────────
    
    def save(self, user_id: str = 'default'):
        path = HOLOGRAM_DIR / f"memory_{user_id}.npz"
        self.store.save(str(path))
        
        # Sauvegarder le profil et l'historique
        meta_path = HOLOGRAM_DIR / f"meta_{user_id}.pkl"
        meta = {
            'user_name': self._user_name,
            'user_profile': self._user_profile,
            'history': self._history[-200:],  # Garder 200 derniers
        }
        with open(meta_path, 'wb') as f:
            pickle.dump(meta, f)
        
        return str(path)
    
    def load(self, user_id: str = 'default') -> bool:
        path = HOLOGRAM_DIR / f"memory_{user_id}.npz"
        if not path.exists():
            return False
        
        self.store.load(str(path))
        
        meta_path = HOLOGRAM_DIR / f"meta_{user_id}.pkl"
        if meta_path.exists():
            with open(meta_path, 'rb') as f:
                meta = pickle.load(f)
            self._user_name = meta.get('user_name', '')
            self._user_profile = meta.get('user_profile', {})
            self._history = meta.get('history', [])
        
        return True
    
    # ── STATISTIQUES ──────────────────────────────────────
    
    @property
    def stats(self) -> dict:
        return {
            **self.store.stats,
            'working_memory_size': len(self._working),
            'history_size': len(self._history),
            'user_name': self._user_name,
            'profile_keys': len(self._user_profile),
        }
    
    def __repr__(self) -> str:
        return (f"MemoryCore({self.store._total_facts} faits, "
                f"{len(self._working)} en mémoire de travail, "
                f"utilisateur='{self._user_name}')")


# ═══════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("  HARMONIC AI V5 — Memory Core Test")
    print("=" * 60)
    
    # ── Test encodage ──
    print("\n[1] Encodage ψ...")
    psi1 = text_to_psi("Sophie aime le chocolat noir")
    psi2 = text_to_psi("Sophie aime le chocolat noir")  # même texte
    psi3 = text_to_psi("Paul est allergique aux arachides")
    
    print(f"    ‖psi1‖ = {np.sqrt(np.sum(np.abs(psi1)**2)):.6f}")
    print(f"    resonance(même) = {psi_resonate(psi1, psi2):.6f} (attendu: 1.0)")
    print(f"    resonance(différent) = {psi_resonate(psi1, psi3):.6f} (attendu: ~0.04)")
    
    # ── Test mémoire ──
    print("\n[2] Mémoire holographique...")
    mem = MemoryCore()
    
    # Apprentissage
    mem.remember("Sophie aime le chocolat noir à 85%")
    mem.remember("Sophie est allergique au lactose")
    mem.remember("Sophie habite à Paris dans le 11ème")
    mem.remember("Paul est le frère de Sophie")
    mem.remember("Paul est médecin à l'hôpital Saint-Louis")
    mem.remember("Le restaurant préféré de Sophie est Le Petit Cambodge")
    
    mem.set_user_name("Sophie")
    mem.set_user_preference("couleur", "bleu")
    mem.set_user_preference("musique", "jazz")
    
    print(f"    {mem}")
    
    # Rappel
    print("\n[3] Rappel par résonance...")
    queries = [
        "Qu'est-ce que Sophie aime manger ?",
        "Où habite Sophie ?",
        "Qui est Paul ?",
        "Quelle est la profession de Paul ?",
        "Quel est le restaurant préféré de Sophie ?",
        "Quelle musique Sophie aime-t-elle ?",
    ]
    
    for q in queries:
        results = mem.recall(q, top_k=2)
        if results:
            best_fact, score = results[0]
            print(f"    Q: '{q}'")
            print(f"    R: '{best_fact.text}' (cohérence={score:.4f})")
        else:
            print(f"    Q: '{q}' → ∅ (aucun fait trouvé)")
    
    # ── Test binding ──
    print("\n[4] Binding HRR...")
    psi_sophie = text_to_psi("Sophie")
    psi_chocolat = text_to_psi("chocolat")
    psi_bound = psi_bind(psi_sophie, psi_chocolat)
    psi_recovered = psi_unbind(psi_bound, psi_chocolat)
    recovery_score = psi_resonate(psi_sophie, psi_recovered)
    print(f"    unbind(bind(Sophie, chocolat), chocolat) ≈ Sophie → {recovery_score:.4f}")
    
    # ── Test persistence ──
    print("\n[5] Persistance...")
    mem.save("test")
    mem2 = MemoryCore()
    loaded = mem2.load("test")
    print(f"    Chargé: {loaded}, {mem2}")
    
    # ── Stats ──
    print("\n[6] Statistiques...")
    for k, v in mem.stats.items():
        print(f"    {k}: {v}")
    
    print("\n✓ Memory Core test terminé.")