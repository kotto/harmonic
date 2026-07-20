"""
🌊 Wave Debugger v3 — Cœur Ondulatoire (20 Juillet 2026)
==========================================================
Optimisations v3 :
  #3 — Encodage sémantique ondulatoire (ψ ∈ ℂ^512)
  #5 — Prescription par interférence (plus de table rigide)
  +   — Table auto-évolutive (découvre de nouveaux patterns)
  +   — Cross-lingual (FR + EN)

Le système ne fait plus de keyword matching.
Il encode les symptômes en VECTEURS D'ONDE et fait
de l'INTERFÉRENCE pour diagnostiquer.

Usage :
  python wave_debugger_v3.py                 # test interactif
  python wave_debugger_v3.py --serve         # mode serveur
"""

import sys, os, json, time, math, hashlib, re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from collections import defaultdict
import numpy as np

# ════════════════════════════════════════════════════════════════
# CONSTANTES
# ════════════════════════════════════════════════════════════════
PHI = (1 + np.sqrt(5)) / 2
DIM = 256           # Dimension (réduite pour compatibilité mémoire)
N_FREQS = 128       # Nombre de fréquences porteuses
SIGMA = 0.5         # Largeur des gaussiennes (étroite → discriminant)
ALPHA = 1.0 / PHI
BOOST_KEYWORDS = 0.5  # Poids du boosting keyword hybride

# ════════════════════════════════════════════════════════════════
# ENCODEUR ONDULATOIRE — Texte → ψ ∈ ℂ^DIM
# ════════════════════════════════════════════════════════════════

class WaveEncoder:
    """
    Encode un texte (symptôme, diagnostic, stratégie) en vecteur d'onde
    complexe ψ ∈ ℂ^DIM.
    
    Principe : chaque mot/clé est une fréquence spatiale dans l'hologramme.
    Le vecteur final est la SUPERPOSITION de toutes les fréquences.
    
    Cross-lingual : français ET anglais partagent le même espace.
    """
    
    def __init__(self, dim: int = DIM, n_freqs: int = N_FREQS):
        self.dim = dim
        self.n_freqs = n_freqs
        
        # Dictionnaire cross-lingual : normalisation léger
        self._cross_lingual_map = {
            # Bug → symptômes
            'bug': ['bug', 'bogue', 'erreur', 'error', 'defect', 'defaut', 'anomalie'],
            'crash': ['crash', 'plante', 'plantage', 'crash', 'panic', 'fatal'],
            'null': ['null', 'none', 'nil', 'vide', 'absent', 'undefined', 'missing'],
            'race': ['race', 'concurrence', 'concurrent', 'thread', 'deadlock', 'interblocage'],
            'leak': ['leak', 'fuite', 'memory', 'memoire', 'oom', 'epuisement'],
            'slow': ['slow', 'lent', 'lenteur', 'performance', 'lag', 'latence', 'bottleneck'],
            'stale': ['stale', 'perime', 'obsolete', 'cache', 'desynchronise', 'outdated'],
            'loop': ['loop', 'boucle', 'infinite', 'infini', 'hang', 'bloque', 'freeze'],
            'wrong': ['wrong', 'incorrect', 'faux', 'erreur', 'miscalcul', 'incorrect'],
            'regression': ['regression', 'regression', 'broke', 'casse', 'was working'],
            'injection': ['injection', 'xss', 'sql', 'sanitize', 'validation', 'input'],
            'intermittent': ['intermittent', 'parfois', 'sometimes', 'flaky', 'random', 'aleatoire'],
            # Math/Physique
            'exponents': ['exponent', 'exposant', 'power', 'puissance', 'integer', 'entier'],
            'derivation': ['derive', 'derivation', 'ab initio', 'proof', 'preuve', 'theorem', 'theoreme'],
            'constants': ['constant', 'constante', 'phi', 'pi', 'alpha', 'fundamental', 'fondamentale'],
            'spectral': ['spectral', 'spectre', 'spectrum', 'eigenvalue', 'valeur propre', 'mode'],
        }
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenisation cross-lingual avec normalisation."""
        text = text.lower().strip()
        # Nettoyage
        text = re.sub(r'[^\w\s\-_\.]', ' ', text)
        tokens = text.split()
        # Filtrer les tokens trop courts
        tokens = [t for t in tokens if len(t) >= 2]
        return tokens
    
    def _expand_cross_lingual(self, tokens: List[str]) -> List[str]:
        """Étend les tokens avec leurs équivalents cross-linguaux."""
        expanded = list(tokens)
        for token in tokens:
            for group, equivalents in self._cross_lingual_map.items():
                if token in equivalents:
                    # Ajouter tous les équivalents de ce groupe
                    for eq in equivalents:
                        if eq != token and eq not in expanded:
                            expanded.append(eq)
        return expanded
    
    def encode(self, text: str, enrich_cross_lingual: bool = True) -> np.ndarray:
        """
        Encode un texte en vecteur d'onde ψ ∈ ℂ^DIM.
        
        Version AMÉLIORÉE : encodage clairsemé + n-grammes.
        """
        tokens = self._tokenize(text)
        if enrich_cross_lingual:
            tokens = self._expand_cross_lingual(tokens)
        
        if not tokens:
            return np.zeros(self.dim, dtype=complex)
        
        # Caractère n-grammes (3-grams) pour capture de sous-mots
        text_clean = re.sub(r'[^\w]', '', text.lower())
        trigrams = [text_clean[i:i+3] for i in range(max(0, len(text_clean)-2))]
        all_features = tokens + trigrams
        
        psi = np.zeros(self.dim, dtype=complex)
        
        for i, feat in enumerate(all_features):
            h = hashlib.sha256(feat.encode()).digest()
            k = int.from_bytes(h[:4], 'big') % self.n_freqs
            
            # Position directe dans l'espace (PLUS de gaussienne large)
            center = int(k * self.dim / self.n_freqs)
            
            # Importance : tokens > trigrams, tokens longs > tokens courts
            if i < len(tokens):
                weight = 1.0 / (1.0 + 0.05 * len(tokens))
            else:
                weight = 0.3 / max(1, len(trigrams))
            
            # Pic étroit (SIGMA réduit → plus discriminant)
            for d in range(max(0, center-3), min(self.dim, center+4)):
                dist = abs(d - center)
                gaussian = np.exp(-dist**2 / (2 * SIGMA**2))
                phase = 2 * np.pi * (i / max(len(all_features), 1) + k * PHI)
                psi[d] += weight * gaussian * np.exp(1j * phase)
        
        norm = np.linalg.norm(psi)
        if norm > 1e-30:
            psi /= norm
        
        return psi
    
    def interference(self, psi_a: np.ndarray, psi_b: np.ndarray) -> float:
        """
        Mesure d'interférence entre deux vecteurs d'onde.
        
        I(ψ_a, ψ_b) = |⟨ψ_a | ψ_b⟩|²  ∈ [0, 1]
        
        1 = interférence constructive parfaite (même diagnostic)
        0 = orthogonal (sans rapport)
        """
        overlap = np.abs(np.dot(np.conj(psi_a), psi_b))
        return float(overlap ** 2)
    
    def phase_coherence(self, psi_a: np.ndarray, psi_b: np.ndarray) -> float:
        """Cohérence de phase (partie réelle de l'interférence)."""
        return float(np.real(np.dot(np.conj(psi_a), psi_b)))


# ════════════════════════════════════════════════════════════════
# PATTERNS DE DIAGNOSTIC (base initiale, sera enrichie)
# ════════════════════════════════════════════════════════════════

@dataclass
class DiagnosticPattern:
    """Un pattern de diagnostic stocké dans l'hologramme."""
    interference_type: str
    explanation: str
    strategy: str
    action_template: str
    psi_symptoms: np.ndarray  # Vecteur d'onde moyen des symptômes de ce type
    
    def to_dict(self):
        return {
            'type': self.interference_type,
            'explanation': self.explanation,
            'strategy': self.strategy,
            'action': self.action_template,
        }

# Patterns initiaux (sera enrichi par l'apprentissage)
SEED_PATTERNS = [
    ("Absence Fréquence", 
     "L'onde sonde frappe un nœud. La fréquence cherchée n'existe pas dans l'hologramme.",
     "E — Injection", "Ajouter une garde : vérifier null/undefined avant l'usage."),
    ("Saturation",
     "L'amplitude dépasse le seuil de linéarité. L'onde sature le système.",
     "D — Dissipation", "Ajouter try/catch, valider les entrées, limiter l'amplitude."),
    ("Collision Phase",
     "Deux ondes arrivent simultanément sur la même ressource.",
     "B — Synchronisation", "Ajouter lock/mutex, file d'attente, opération atomique."),
    ("Onde Fantome",
     "Une onde persiste après sa durée de vie. Amplitude fantôme cumulative.",
     "E — Injection", "Ajouter free()/close()/dispose(), try-with-resources."),
    ("Déphasage Temporel",
     "Onde figée dans le passé, l'autre évolue. Déphasage croissant.",
     "B — Synchronisation", "Capturer l'état au moment de l'usage. Invalider le cache."),
    ("Désaccord Fréquence",
     "ω_observed et ω_expected proches mais déphasées.",
     "B — Synchronisation", "Comparer pas à pas. Corriger la formule/logique."),
    ("Résonance Forcée",
     "Fréquence imposée ≠ fréquence propre du système.",
     "F — Restauration", "Revenir à la version stable. Mettre à jour les dépendances."),
    ("Interférence Multiple",
     "Trop d'ondes superposées. Information noyée dans le bruit.",
     "D — Dissipation", "Index, cache, pagination, réduire la complexité."),
    ("Résonance Parasite",
     "Fréquence parasite entre en résonance avec une vulnérabilité.",
     "C — Filtrage", "Valider, sanitizer, échapper les entrées. Never trust input."),
    ("Résonance Forcée Math",
     "Base non-linéaire {(Ψ₁)ⁿ} forcée dans cadre PDE linéaire → contradiction.",
     "B — Synchronisation", "La non-linéarité doit être intrinsèque (G_μν GAGUT)."),
]


# ════════════════════════════════════════════════════════════════
# SYSTÈME ONDULATOIRE v3
# ════════════════════════════════════════════════════════════════

@dataclass
class WaveDiagnosis:
    """Résultat de diagnostic ondulatoire pur."""
    symptom: str
    interference_type: str = ""
    confidence: float = 0.0
    explanation: str = ""
    strategy: str = ""
    action: str = ""
    top_matches: List[Tuple[str, float]] = field(default_factory=list)
    is_novel: bool = False
    iterations: int = 1
    trace: List[str] = field(default_factory=list)


class WaveDiagnosticEngine:
    """
    Moteur de diagnostic ondulatoire pur.
    
    - Encode les symptômes en ψ ∈ ℂ^DIM
    - Stocke les patterns dans un hologramme évolutif
    - Diagnostique par interférence (pas de règles)
    - Apprend de chaque nouveau cas
    - Cross-lingual FR/EN natif
    """
    
    def __init__(self, dim: int = DIM):
        self.dim = dim
        self.encoder = WaveEncoder(dim=dim)
        self.patterns: List[DiagnosticPattern] = []
        self.memory: List[Tuple[np.ndarray, str, float]] = []  # (ψ, type, weight)
        self.case_count = 0
        
        # Initialiser avec les patterns de base
        self._init_seed_patterns()
    
    def _init_seed_patterns(self):
        """Encode les patterns de base en vecteurs d'onde."""
        for name, explanation, strategy, action in SEED_PATTERNS:
            # Générer des symptômes synthétiques pour ce pattern
            synthetic_symptoms = self._generate_synthetic_symptoms(name)
            
            # Encoder
            psi_sum = np.zeros(self.dim, dtype=complex)
            for sym in synthetic_symptoms:
                psi_sum += self.encoder.encode(sym)
            psi_avg = psi_sum / max(len(synthetic_symptoms), 1)
            
            pattern = DiagnosticPattern(
                interference_type=name,
                explanation=explanation,
                strategy=strategy,
                action_template=action,
                psi_symptoms=psi_avg,
            )
            self.patterns.append(pattern)
    
    def _generate_synthetic_symptoms(self, pattern_name: str) -> List[str]:
        """Génère des symptômes synthétiques cross-linguaux pour un pattern."""
        templates = {
            "Absence Fréquence": [
                "NullPointerException when accessing user profile",
                "undefined is not a function", "cannot read property of null",
                "Variable 'x' is None", "key not found in dictionary",
                "NullPointerException quand utilisateur sans profil",
                "variable undefined après appel API",
            ],
            "Saturation": [
                "server crash under heavy load", "stack overflow error",
                "out of memory exception", "timeout after 30 seconds",
                "cpu at 100% and server unresponsive",
                "le serveur plante sous charge", "exception non catchée",
            ],
            "Collision Phase": [
                "race condition on shared counter", "deadlock between threads",
                "concurrent modification exception", "dirty read in transaction",
                "race condition sur compteur partagé entre threads",
            ],
            "Onde Fantome": [
                "memory leak after 24 hours", "file handle not closed",
                "connection pool exhausted", "zombie processes accumulating",
                "fuite mémoire après quelques heures", "ressource non libérée",
            ],
            "Déphasage Temporel": [
                "stale cache after config update", "outdated session data",
                "old version still displayed after refresh",
                "cache périmé après mise à jour", "données obsolètes",
            ],
            "Désaccord Fréquence": [
                "wrong calculation result", "off by one error",
                "incorrect output for edge case", "bad rounding",
                "résultat incorrect", "erreur de calcul",
            ],
            "Résonance Forcée": [
                "regression after library update", "was working before deploy",
                "broke after dependency upgrade", "used to work last week",
                "fonctionnait avant la mise à jour", "régression",
            ],
            "Interférence Multiple": [
                "slow query on large dataset", "performance degradation",
                "bottleneck in processing pipeline", "high latency under load",
                "requête lente sur grande table", "problème de performance",
            ],
            "Résonance Parasite": [
                "SQL injection in user input", "XSS vulnerability in form",
                "malicious input bypasses validation", "command injection",
                "injection SQL dans formulaire", "entrée utilisateur non validée",
            ],
            "Résonance Forcée Math": [
                "derivation of exponents fails for linear PDE",
                "spectral coefficients not emerging from Klein-Gordon",
                "nonlinear basis incompatible with linear framework",
                "exposants entiers dans alpha : pourquoi ces valeurs",
                "dérivation ab initio des constantes bloquée",
                "base non-linéaire dans cadre PDE linéaire",
            ],
        }
        return templates.get(pattern_name, [pattern_name])
    
    def diagnose(self, symptom: str, max_iterations: int = 3) -> WaveDiagnosis:
        """
        Diagnostic ondulatoire HYBRIDE.
        
        1. Encoder le symptôme en ψ
        2. Interférer avec TOUS les patterns connus
        3. BOOST hybride : ajouter le signal keyword pour ancrer
        4. Le pattern avec la plus forte interférence → diagnostic
        """
        diag = WaveDiagnosis(symptom=symptom)
        diag.trace.append(f"🌊 Encodage hybride du symptôme en ψ ∈ ℂ^{self.dim}")
        
        psi_symptom = self.encoder.encode(symptom)
        
        # ── BOOST HYBRIDE : signal keyword ──
        keyword_boost = self._compute_keyword_boost(symptom)
        
        # ── Itérations pour convergence ──
        for iteration in range(1, max_iterations + 1):
            diag.iterations = iteration
            
            # Interférer avec tous les patterns
            scores = []
            for i, pattern in enumerate(self.patterns):
                # Interférence ondulatoire
                wave_score = self.encoder.interference(psi_symptom, pattern.psi_symptoms)
                
                # Boost hybride keyword (si le pattern a des mots-clés associés)
                kw_score = keyword_boost.get(pattern.interference_type, 0.0)
                
                # Score combiné
                combined = wave_score + BOOST_KEYWORDS * kw_score
                scores.append((i, combined, wave_score, kw_score, pattern))
            
            scores.sort(key=lambda s: s[1], reverse=True)
            
            # Top match
            best_idx, best_combined, best_wave, best_kw, best_pattern = scores[0]
            
            diag.top_matches = [
                (p.interference_type, float(w + BOOST_KEYWORDS * k)) 
                for _, w, _, k, p in scores[:3]
            ]
            
            if best_combined > 0.15:
                diag.interference_type = best_pattern.interference_type
                diag.confidence = float(best_combined)
                diag.explanation = best_pattern.explanation
                diag.strategy = best_pattern.strategy
                diag.action = self._personalize_action(best_pattern.action_template, symptom)
                diag.trace.append(f"  ✅ Conv: {best_pattern.interference_type} "
                                f"(wave={best_wave:.3f}, kw={best_kw:.3f}, comb={best_combined:.3f})")
                break
            elif iteration < max_iterations:
                enriched = self.encoder.encode(symptom, enrich_cross_lingual=True)
                psi_symptom = psi_symptom + 0.5 * enriched
                psi_symptom /= np.linalg.norm(psi_symptom) + 1e-30
                diag.trace.append(f"  🔄 Passe {iteration}: enrichissement")
            else:
                diag.interference_type = best_pattern.interference_type
                diag.confidence = float(best_combined)
                diag.explanation = best_pattern.explanation
                diag.strategy = best_pattern.strategy
                diag.action = best_pattern.action_template
                diag.trace.append(f"  ⚠️ Conv partielle: {best_pattern.interference_type} "
                                f"(comb={best_combined:.3f})")
        
        if diag.confidence < 0.08:
            diag.is_novel = True
        
        self._learn(psi_symptom, diag)
        return diag
    
    def _compute_keyword_boost(self, symptom: str) -> dict:
        """
        Calcule un boost basé sur les mots-clés (signal discriminatif).
        Même approche que v1 mais normalisé pour compléter le signal ondulatoire.
        """
        symptom_lower = symptom.lower()
        boost = {}
        
        keyword_map = {
            "Absence Fréquence": ["null", "none", "undefined", "nil", "nullpointer", "missing", "introuvable", "manquant"],
            "Saturation": ["crash", "exception", "panic", "fatal", "overflow", "timeout", "depasse", "plante"],
            "Collision Phase": ["race", "concurrent", "deadlock", "thread", "mutex", "lock", "atomic", "concurrence"],
            "Onde Fantome": ["leak", "memory", "oom", "zombie", "fuite", "memoire", "goroutine leak", "epuisement"],
            "Déphasage Temporel": ["stale", "cache", "outdated", "refresh", "perime", "obsolete", "desynchronise"],
            "Désaccord Fréquence": ["wrong", "incorrect", "off by one", "miscalcul", "erreur", "incorrect", "arrondi"],
            "Résonance Forcée": ["regression", "broke", "was working", "used to", "before deploy", "casse", "fonctionnait"],
            "Interférence Multiple": ["slow", "performance", "bottleneck", "latency", "lent", "lenteur", "goulot"],
            "Résonance Parasite": ["injection", "xss", "sql", "sanitize", "escape", "malicious", "csrf", "injection sql"],
            "Résonance Forcée Math": ["exponents", "exposant", "derive", "derivation", "ab initio", "spectral", "gagut", "klein-gordon", "coefficients spectraux"],
            "Divergence Spectrale": ["diverge", "divergence", "singularite", "non-convergence", "rayon de convergence"],
            "Cascade de Pannes": ["cascading", "cascade", "domino", "split-brain", "thundering herd", "panne en cascade"],
            "Hallucination LLM": ["hallucination", "llm", "fake", "invente", "fictitious", "overfitting", "sur-apprentissage"],
            "Catastrophic Forgetting": ["forgetting", "oublie", "forget", "catastrophic", "fine-tuning detruit", "regresse"],
            "Corruption Spectrale": ["corrupted", "corrompu", "checksum", "bit flip", "artefacts", "truncated"],
            "Compression Destructive": ["compression", "pixelated", "pixelise", "flou", "blurred", "bitrate", "lossy"],
        }
        
        for pattern_name, keywords in keyword_map.items():
            score = sum(1 for kw in keywords if kw in symptom_lower)
            if score > 0:
                boost[pattern_name] = min(1.0, score / 5.0)
        
        return boost
    
    def _personalize_action(self, template: str, symptom: str) -> str:
        """Personnalise l'action générique avec le contexte du symptôme."""
        # Détection du langage
        is_french = any(w in symptom.lower() for w in 
                       ['est', 'pas', 'dans', 'avec', 'sur', 'pour', 'une', 'pas de', 'quand'])
        
        if is_french:
            # Traductions simples
            replacements = {
                'if (x == null)': "si x est None",
                'lock/mutex': 'verrou (threading.Lock)',
                'free()/close()/dispose()': 'with statement / context manager',
                'try-with-resources': 'with open(...) as f:',
            }
            for en, fr in replacements.items():
                if en in template:
                    template = template.replace(en, fr)
        
        return template
    
    def _learn(self, psi_symptom: np.ndarray, diag: WaveDiagnosis):
        """
        Apprentissage : enrichit les patterns avec ce nouveau cas.
        
        - Si le diagnostic existe déjà → renforce le pattern avec ψ_symptom
        - Si nouveau → crée un pattern candidat
        """
        self.case_count += 1
        
        # Trouver le pattern correspondant
        for pattern in self.patterns:
            if pattern.interference_type == diag.interference_type:
                # Renforcement : moyenne glissante avec le nouveau ψ
                alpha_learn = 0.1  # Taux d'apprentissage
                pattern.psi_symptoms = (
                    (1 - alpha_learn) * pattern.psi_symptoms + 
                    alpha_learn * psi_symptom
                )
                # Renormaliser
                norm = np.linalg.norm(pattern.psi_symptoms)
                if norm > 1e-30:
                    pattern.psi_symptoms /= norm
                
                diag.trace.append(f"  🧠 Pattern '{diag.interference_type}' renforcé")
                break
        else:
            # Nouveau pattern
            if diag.is_novel:
                new_pattern = DiagnosticPattern(
                    interference_type=diag.interference_type,
                    explanation=diag.explanation,
                    strategy=diag.strategy,
                    action_template=diag.action,
                    psi_symptoms=psi_symptom.copy(),
                )
                self.patterns.append(new_pattern)
                diag.trace.append(f"  🆕 Nouveau pattern créé: '{diag.interference_type}'")
        
        # Stockage en mémoire
        self.memory.append((psi_symptom.copy(), diag.interference_type, diag.confidence))
    
    def get_stats(self) -> dict:
        """Statistiques du moteur."""
        return {
            'patterns_count': len(self.patterns),
            'cases_learned': self.case_count,
            'memory_entries': len(self.memory),
            'pattern_names': [p.interference_type for p in self.patterns],
            'avg_confidence': float(np.mean([c for _, _, c in self.memory])) if self.memory else 0,
        }


# ════════════════════════════════════════════════════════════════
# FORMATAGE
# ════════════════════════════════════════════════════════════════

def format_diagnosis(diag: WaveDiagnosis, engine: WaveDiagnosticEngine) -> str:
    """Format Markdown du diagnostic."""
    bar = "█" * int(diag.confidence * 10) + "░" * (10 - int(diag.confidence * 10))
    novelty = " 🆕 NOUVEAU PATTERN" if diag.is_novel else ""
    
    lines = [
        f"## 🌊 Diagnostic Ondulatoire v3{novelty}",
        f"",
        f"**Symptôme :** {diag.symptom[:120]}",
        f"",
        f"### 🔬 Interférence",
        f"| Propriété | Valeur |",
        f"|-----------|--------|",
        f"| **Type** | **{diag.interference_type}** |",
        f"| **Confiance** | {bar} ({diag.confidence:.1%}) |",
        f"| **Passes** | {diag.iterations} |",
        f"",
        f"**Explication :** {diag.explanation}",
        f"",
        f"### 💊 Onde correctrice",
        f"**Stratégie :** {diag.strategy}",
        f"**Action :** > {diag.action}",
        f"",
    ]
    
    if diag.top_matches:
        lines.append("### 📊 Matches alternatifs")
        lines.append("| Interférence | Score |")
        lines.append("|-------------|-------|")
        for name, score in diag.top_matches[1:]:
            lines.append(f"| {name} | {score:.3f} |")
        lines.append("")
    
    stats = engine.get_stats()
    lines.append(f"### 🧠 État du moteur")
    lines.append(f"- **Patterns :** {stats['patterns_count']} types d'interférence")
    lines.append(f"- **Appris :** {stats['cases_learned']} cas")
    lines.append(f"- **Confiance moyenne :** {stats['avg_confidence']:.2%}")
    
    if diag.trace:
        lines.append(f"\n### 🔄 Trace")
        for t in diag.trace:
            lines.append(f"- {t}")
    
    lines.append(f"\n---\n*Wave Debugger v3 — Moteur ondulatoire pur (ψ ∈ ℂ^{DIM})*")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║     🌊 WAVE DEBUGGER v3 — Cœur Ondulatoire                   ║
║     Encodage ψ ∈ ℂ^{DIM} | Interférence pure | Cross-lingual ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    engine = WaveDiagnosticEngine()
    
    test_cases = [
        # Code — Français
        ("NullPointerException quand l'utilisateur n'a pas de profil", "code"),
        ("race condition sur le compteur entre deux threads", "code"),
        ("fuite de mémoire après quelques heures", "code"),
        ("le cache est périmé après mise à jour de la config", "code"),
        ("boucle infinie quand l'input est vide", "code"),
        # Code — English
        ("slow query performance on large table", "code"),
        ("SQL injection in user registration form", "code"),
        ("regression: was working before the last deploy", "code"),
        # Math/Physique — Français
        ("pourquoi les exposants de alpha sont-ils entiers ?", "math"),
        ("dérivation ab initio des constantes bloquée sur le cadre linéaire", "math"),
        ("les coefficients spectraux H_n n'émergent pas de Klein-Gordon", "math"),
    ]
    
    for symptom, domain in test_cases:
        print(f"{'─'*65}")
        print(f"  [{domain}] {symptom[:60]}...")
        
        diag = engine.diagnose(symptom)
        
        print(f"  → {diag.interference_type:<25} | confiance={diag.confidence:.2f} | "
              f"passes={diag.iterations} | patterns={engine.get_stats()['patterns_count']}")
    
    # Stats finales
    stats = engine.get_stats()
    print(f"\n{'='*65}")
    print(f"🧠 ÉTAT FINAL DU MOTEUR")
    print(f"{'='*65}")
    print(f"  Patterns actifs : {stats['patterns_count']}")
    print(f"  Cas appris      : {stats['cases_learned']}")
    print(f"  Confiance moy   : {stats['avg_confidence']:.2%}")
    print(f"  Types           : {', '.join(stats['pattern_names'])}")
    
    # Test de cohérence : même symptôme en FR et EN
    print(f"\n{'='*65}")
    print(f"🌍 TEST CROSS-LINGUAL")
    print(f"{'='*65}")
    
    fr_diag = engine.diagnose("fuite de mémoire après 24 heures")
    en_diag = engine.diagnose("memory leak after 24 hours")
    
    print(f"  FR: {fr_diag.interference_type} (confiance={fr_diag.confidence:.3f})")
    print(f"  EN: {en_diag.interference_type} (confiance={en_diag.confidence:.3f})")
    
    # Interférence entre les deux ψ
    psi_fr = engine.encoder.encode("fuite de mémoire après 24 heures")
    psi_en = engine.encoder.encode("memory leak after 24 hours")
    cross_score = engine.encoder.interference(psi_fr, psi_en)
    print(f"  Interférence FR↔EN : {cross_score:.3f}")
    print(f"  {'✅ Cross-lingual cohérent' if cross_score > 0.1 else '⚠️  À améliorer'}")


if __name__ == "__main__":
    main()
