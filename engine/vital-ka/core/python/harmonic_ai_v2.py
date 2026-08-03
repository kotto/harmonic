"""
🌊 Harmonic AI v2 — Core Unifié (20 Juillet 2026)
===================================================
Intègre le Wave Debugger, le GenerativeEncoder, et la mémoire
holographique dans le pipeline principal de Harmonic AI.

Nouvelles capacités :
  - Diagnostic ondulatoire de bugs (4 étapes)
  - Encodeur génératif (17 concepts fondamentaux, cross-lingual)
  - Apprentissage continu (chaque diagnostic enrichit l'hologramme)
  - API unifiée (chat + debug + learn)

Usage:
  from harmonic_ai_v2 import HarmonicAIv2
  ai = HarmonicAIv2()
  ai.chat("Pourquoi mon code crash ?")        # conversation
  ai.debug("NullPointerException in loop")    # diagnostic
  ai.learn("nouveau pattern", symptomes)       # apprentissage
"""

import sys, os, json, time, hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

from generative_encoder import GenerativeEncoder, WAVE_CONCEPTS
from wave_debugger_v3 import WaveDiagnosticEngine as LegacyEngine
from wave_debugger_v6 import SemanticEncoder


@dataclass
class DebugResult:
    symptom: str
    interference_type: str
    confidence: float
    explanation: str
    strategy: str
    action: str
    cross_lingual_score: float = 0.0
    learning_applied: bool = False


class HarmonicAIv2:
    """
    IA Harmonique v2 — Unifiée.
    
    Combine :
    - Chat conversationnel (existing pipeline)
    - Wave Debugger (diagnostic de bugs)
    - Generative Encoder (cross-lingual natif)
    - Apprentissage continu (mémoire holographique)
    """
    
    def __init__(self):
        print("🌊 Harmonic AI v2 — Initialisation...")
        
        # Encodeur génératif (optimal, 17 concepts)
        print("  📡 Encodeur Génératif...", end=" ")
        self.encoder = GenerativeEncoder(dim=128)
        print("✓")
        
        # Patterns de diagnostic (construits avec l'encodeur génératif)
        print("  🔬 Patterns de diagnostic...", end=" ")
        self.patterns: Dict[str, np.ndarray] = {}
        self.pattern_info: Dict[str, dict] = {}
        self._init_patterns()
        print(f"{len(self.patterns)} patterns ✓")
        
        # Mémoire d'apprentissage (hologramme)
        print("  🧠 Mémoire holographique...", end=" ")
        self.memory: List[Tuple[np.ndarray, str, float]] = []
        self.learned_patterns: Dict[str, List[np.ndarray]] = {}
        self.total_learned = 0
        self._load_memory()
        print(f"{self.total_learned} diagnostics stockés ✓")
        
        # Moteur ABC hybride
        from wave_debugger_v2 import ABCHybridEngine
        self.abc = ABCHybridEngine()
        
        print("  ✅ Prêt.\n")
    
    def _init_patterns(self):
        """Initialise les patterns de diagnostic avec l'encodeur génératif."""
        
        # Chaque pattern = superposition de concepts ondulatoires
        pattern_concepts = {
            "Absence Fréquence": ["absence_frequence", "exception", "utilisateur"],
            "Collision Phase": ["collision_phase"],
            "Onde Fantome": ["onde_fantome", "memoire"],
            "Déphasage Temporel": ["dephasage_temporel", "memoire"],
            "Désaccord Fréquence": ["desaccord_frequence"],
            "Résonance Forcée": ["resonance_forcee", "deploiement"],
            "Interférence Multiple": ["interference_multiple", "base_de_donnees"],
            "Résonance Parasite": ["resonance_parasite", "reseau"],
            "Saturation": ["saturation", "serveur"],
            "Résonance Forcée Math": ["resonance_forcee", "desaccord_frequence"],
        }
        
        pattern_info = {
            "Absence Fréquence": {
                "explanation": "L'onde sonde frappe un nœud (amplitude nulle). La fréquence cherchée n'existe pas dans l'hologramme.",
                "strategy": "E — Injection",
                "action": "Ajouter une garde : if (x == null) return default; Optional type. Valeur par défaut.",
            },
            "Collision Phase": {
                "explanation": "Deux ondes arrivent simultanément sur la même ressource. Résultat dépend de l'ordre d'arrivée.",
                "strategy": "B — Synchronisation",
                "action": "Ajouter lock/mutex/semaphore. Rendre l'opération atomique. Transaction isolée.",
            },
            "Onde Fantome": {
                "explanation": "Une onde persiste après sa durée de vie utile. L'amplitude fantôme s'accumule.",
                "strategy": "E — Injection (onde inverse)",
                "action": "Ajouter free()/close()/dispose(). try-with-resources. RAII. WeakRef.",
            },
            "Déphasage Temporel": {
                "explanation": "Une onde figée dans le passé (t₀) tandis que l'autre évolue (t). Déphasage croissant.",
                "strategy": "B — Synchronisation",
                "action": "Capturer l'état au moment de l'usage. Invalider le cache. Refresh. Polling.",
            },
            "Désaccord Fréquence": {
                "explanation": "ω_observed et ω_expected sont proches mais déphasées. Battement perceptible.",
                "strategy": "B — Synchronisation",
                "action": "Comparer pas à pas avec assertions. Corriger la formule. Tests unitaires.",
            },
            "Résonance Forcée": {
                "explanation": "Fréquence imposée ≠ fréquence propre du système. Vibration instable.",
                "strategy": "F — Restauration",
                "action": "Revenir à la version stable (revert). Mettre à jour les dépendances. Tests de non-régression.",
            },
            "Interférence Multiple": {
                "explanation": "Trop d'ondes superposées. L'information utile est noyée dans le bruit.",
                "strategy": "D — Dissipation",
                "action": "Index, cache, pagination, lazy loading. O(n²)→O(n log n). Load balancing.",
            },
            "Résonance Parasite": {
                "explanation": "Fréquence parasite (input malveillant) en résonance avec une vulnérabilité.",
                "strategy": "C — Filtrage",
                "action": "Valider, sanitizer, échapper. Prepared statements. CSP. Never trust input.",
            },
            "Saturation": {
                "explanation": "L'amplitude dépasse le seuil de linéarité. Le système sature et rompt.",
                "strategy": "D — Dissipation",
                "action": "Rate limiting, circuit breaker, load balancing, timeout. Try/catch global.",
            },
            "Résonance Forcée Math": {
                "explanation": "Base non-linéaire {(Ψ₁)ⁿ} forcée dans cadre PDE linéaire → contradiction.",
                "strategy": "B — Synchronisation",
                "action": "La non-linéarité doit être intrinsèque (G_μν GAGUT), pas ajoutée. ABC comme couplage.",
            },
        }
        
        for name, concepts in pattern_concepts.items():
            psi = np.zeros(self.encoder.dim, dtype=complex)
            for c in concepts:
                if c in self.encoder.concept_psi:
                    psi += self.encoder.concept_psi[c]
            nrm = np.linalg.norm(psi)
            self.patterns[name] = psi / nrm if nrm > 1e-30 else psi
            self.pattern_info[name] = pattern_info.get(name, {})
    
    def debug(self, symptom: str) -> DebugResult:
        """
        Diagnostique un symptôme de bug.
        
        Pipeline :
        1. Encoder le symptôme (génératif, cross-lingual)
        2. Interférer avec tous les patterns (standard + appris)
        3. Retourner le diagnostic + prescription
        """
        # Encoder
        psi = self.encoder.encode(symptom)
        
        # Interférer avec les patterns standard
        scores = []
        for name, pattern_psi in self.patterns.items():
            score = self.encoder.interference(psi, pattern_psi)
            scores.append((name, score, False))  # (nom, score, is_learned)
        
        # Interférer avec les patterns appris
        for name, psis in self.learned_patterns.items():
            for learned_psi in psis:
                score = self.encoder.interference(psi, learned_psi)
                scores.append((name, score, True))
        
        scores.sort(key=lambda s: s[1], reverse=True)
        best_name, best_score, is_learned = scores[0]
        
        info = self.pattern_info.get(best_name, {})
        
        return DebugResult(
            symptom=symptom,
            interference_type=best_name,
            confidence=float(best_score),
            explanation=info.get("explanation", ""),
            strategy=info.get("strategy", ""),
            action=info.get("action", ""),
            learning_applied=is_learned,
        )
    
    def chat(self, message: str) -> str:
        """Conversation — détecte automatiquement si c'est un debug."""
        # Détection de demande de debug
        debug_keywords = ["bug", "crash", "exception", "error", "erreur", "plante",
                         "null", "race", "leak", "fuite", "lent", "slow", "cache",
                         "deadlock", "timeout", "regression", "injection"]
        
        is_debug = any(kw in message.lower() for kw in debug_keywords)
        
        if is_debug:
            result = self.debug(message)
            return self._format_debug_response(result)
        
        # Sinon, réponse conversationnelle
        return self._chat_response(message)
    
    def _format_debug_response(self, r: DebugResult) -> str:
        """Formate un diagnostic en Markdown."""
        conf_bar = "█" * int(r.confidence * 10) + "░" * (10 - int(r.confidence * 10))
        learned = " 🧠 (appris)" if r.learning_applied else ""
        
        return f"""## 🌊 Diagnostic Ondulatoire{learned}

**Symptôme :** {r.symptom[:120]}

### 🔬 Interférence
| Propriété | Valeur |
|-----------|--------|
| **Type** | **{r.interference_type}** |
| **Confiance** | {conf_bar} ({r.confidence:.0%}) |

**Explication :** {r.explanation}

### 💊 Onde correctrice
**Stratégie :** {r.strategy}
> {r.action}

### ✅ Vérification
1. Le symptôme a disparu ?
2. Pas de régression ?
3. Solution autonome (pas un patch) ?
4. Harmoniques intactes ?
5. Test écrit (immunité) ?

---
*Harmonic AI v2 — Diagnostic Ondulatoire*"""
    
    def _chat_response(self, message: str) -> str:
        """Réponse conversationnelle simple."""
        return f"KA : Je comprends votre message. Pour un diagnostic de bug, décrivez le symptôme (ex: 'NullPointerException quand...')."
    
    def learn(self, symptom: str, correct_diagnosis: str, 
              language: str = "auto") -> dict:
        """
        Apprend d'un nouveau cas.
        
        Le symptôme est encodé et stocké dans l'hologramme,
        renforçant les patterns existants ou en créant de nouveaux.
        """
        psi = self.encoder.encode(symptom)
        
        if correct_diagnosis not in self.learned_patterns:
            self.learned_patterns[correct_diagnosis] = []
        
        self.learned_patterns[correct_diagnosis].append(psi)
        self.memory.append((psi, correct_diagnosis, 1.0))
        self.total_learned += 1
        
        # Sauvegarder périodiquement
        if self.total_learned % 10 == 0:
            self._save_memory()
        
        return {
            "status": "learned",
            "symptom": symptom[:80],
            "diagnosis": correct_diagnosis,
            "total_learned": self.total_learned,
        }
    
    def get_stats(self) -> dict:
        return {
            "patterns": len(self.patterns),
            "learned_patterns": len(self.learned_patterns),
            "total_learned": self.total_learned,
            "concepts": len(self.encoder.concept_psi),
            "cross_lingual_pairs": sum(
                len(data.get("fr", [])) + len(data.get("en", []))
                for data in WAVE_CONCEPTS.values()
            ),
        }
    
    def _save_memory(self):
        try:
            data = {
                "total_learned": self.total_learned,
                "patterns": {
                    name: [{"real": v.real.tolist(), "imag": v.imag.tolist()} 
                           for v in psis]
                    for name, psis in self.learned_patterns.items()
                }
            }
            path = _ENGINE_DIR / "data" / "harmonic_ai_v2_memory.json"
            with open(path, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass
    
    def _load_memory(self):
        try:
            path = _ENGINE_DIR / "data" / "harmonic_ai_v2_memory.json"
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                self.total_learned = data.get("total_learned", 0)
                for name, psis in data.get("patterns", {}).items():
                    self.learned_patterns[name] = [
                        np.array(v["real"]) + 1j * np.array(v["imag"])
                        for v in psis
                    ]
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ai = HarmonicAIv2()
    
    print("=" * 60)
    print("  TEST HARMONIC AI v2")
    print("=" * 60)
    
    # Stats
    stats = ai.get_stats()
    print(f"\n📊 Stats : {stats['patterns']} patterns, {stats['total_learned']} appris, "
          f"{stats['concepts']} concepts, {stats['cross_lingual_pairs']} ancres cross-linguales")
    
    # Test diagnostic
    tests = [
        "NullPointerException in UserService.getProfile()",
        "race condition between worker threads",
        "memory leak after 24 hours of continuous operation",
        "fuite de mémoire après quelques heures",
        "injection SQL dans le paramètre de recherche",
    ]
    
    print(f"\n🧪 Diagnostics :")
    for t in tests:
        r = ai.debug(t)
        print(f"  {r.interference_type:<24} (conf={r.confidence:.2f}) | {t[:50]}...")
    
    # Test apprentissage
    print(f"\n🧠 Apprentissage :")
    r = ai.learn("mon serveur s'arrête après 3 jours sans raison apparente", "Onde Fantome")
    print(f"  {r}")
    
    r = ai.learn("the API returns 500 when the JSON is malformed", "Saturation")
    print(f"  {r}")
    
    print(f"\n  Total appris : {ai.total_learned}")
    
    # Test chat
    print(f"\n💬 Chat :")
    print(f"  {ai.chat('Bonjour, qui es-tu ?')[:80]}...")
    print(f"  {ai.chat('mon serveur a une fuite de mémoire')[::200]}...")
