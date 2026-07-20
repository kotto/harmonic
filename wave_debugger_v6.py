"""
🌊 Wave Debugger v6 — Encodeur Sémantique Harmonique
======================================================
Utilise HolographicEncoder (learned SVD + spectral + hash)
pour encoder les symptômes. Cross-lingual via co-occurrences KB.
"""

import sys, os, time, numpy as np
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass, field

_ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT_DIR))

@dataclass
class DiagnosticPattern:
    interference_type: str
    explanation: str
    strategy: str
    action_template: str
    psi_symptoms: np.ndarray

@dataclass
class WaveDiagnosis:
    symptom: str
    interference_type: str = ""
    confidence: float = 0.0
    explanation: str = ""
    strategy: str = ""
    action: str = ""
    top_matches: List[Tuple[str, float]] = field(default_factory=list)


class SemanticEncoder:
    """Wrapper autour HolographicEncoder pour les symptômes."""
    
    def __init__(self, dim: int = 128):
        self.dim = dim
        print("  📚 HolographicEncoder...", end=" ", flush=True)
        from holographic_encoder import HolographicEncoder
        import holographic_encoder as he
        self.holo = HolographicEncoder(dim=dim)
        n_learned = len(he._LEARNED.vectors) if he._LEARNED and he._LEARNED.is_trained else 0
        print(f"{n_learned} mots", end=" ", flush=True)
        
        # Attention harmonique — contextualise les tokens
        from harmonic_attention import HarmonicAttention
        self.attention = HarmonicAttention(encoder=None, dim=dim, alpha=0.25, power=2.0)
        print("+ Attention ✓")
    
    def encode(self, text: str, use_attention: bool = True) -> np.ndarray:
        tokens = [t.strip('.,!?;:()[]{}') for t in text.lower().split() 
                  if len(t.strip('.,!?;:()[]{}')) >= 2]
        if not tokens:
            return np.zeros(self.dim, dtype=complex)
        
        if use_attention and len(tokens) >= 2:
            # Pré-encoder les tokens dans l'encodeur (remplit word_vectors)
            for token in tokens:
                if token not in self.holo.word_vectors:
                    self.holo.encode_word(token)
            
            # Injecter l'encodeur dans l'attention pour utiliser ses vecteurs
            self.attention.encoder = self.holo
            
            # Contextualiser : chaque token modulé par ses voisins
            ctx = self.attention.contextualize(tokens)
            
            # Sommer les ψ contextualisés
            psi = np.zeros(self.dim, dtype=complex)
            for token in tokens:
                vec = ctx.get(token)
                if vec is None:
                    vec = self.holo.word_vectors.get(token)
                if vec is not None:
                    if len(vec) > self.dim: vec = vec[:self.dim]
                    elif len(vec) < self.dim:
                        p = np.zeros(self.dim, dtype=complex); p[:len(vec)] = vec; vec = p
                    psi += vec
            
            if np.linalg.norm(psi) > 1e-30:
                return psi / np.linalg.norm(psi)
        
        # Fallback : superposition simple
        psi = np.zeros(self.dim, dtype=complex)
        for token in tokens:
            vec = self.holo.encode_word(token)
            if vec is not None:
                if len(vec) > self.dim: vec = vec[:self.dim]
                elif len(vec) < self.dim:
                    p = np.zeros(self.dim, dtype=complex); p[:len(vec)] = vec; vec = p
                psi += vec
        
        nrm = np.linalg.norm(psi)
        return psi / nrm if nrm > 1e-30 else psi
    
    def interference(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.abs(np.dot(np.conj(a), b)) ** 2)


class SemanticDiagnosticEngine:
    def __init__(self, dim: int = 128):
        self.dim = dim
        self.encoder = SemanticEncoder(dim=dim)
        self.patterns: List[DiagnosticPattern] = []
        self.case_count = 0
    
    def add_pattern(self, name: str, explanation: str, strategy: str,
                    action: str, symptoms: List[str]):
        psi_sum = np.zeros(self.dim, dtype=complex)
        for s in symptoms:
            psi_sum += self.encoder.encode(s)
        self.patterns.append(DiagnosticPattern(
            interference_type=name, explanation=explanation,
            strategy=strategy, action_template=action,
            psi_symptoms=psi_sum / max(len(symptoms), 1)))
    
    def diagnose(self, symptom: str) -> WaveDiagnosis:
        diag = WaveDiagnosis(symptom=symptom)
        psi = self.encoder.encode(symptom)
        scores = [(i, self.encoder.interference(psi, p.psi_symptoms), p) 
                  for i, p in enumerate(self.patterns)]
        scores.sort(key=lambda x: x[1], reverse=True)
        best = scores[0]
        diag.interference_type = best[2].interference_type
        diag.confidence = float(best[1])
        diag.explanation = best[2].explanation
        diag.strategy = best[2].strategy
        diag.action = best[2].action_template
        diag.top_matches = [(p.interference_type, float(s)) for _, s, p in scores[:3]]
        self.case_count += 1
        return diag


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   🌊 WAVE DEBUGGER v6 — Encodeur Holographique               ║
║   SVD 110K faits → vecteurs sémantiques                      ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    engine = SemanticDiagnosticEngine(dim=128)
    
    # Cross-lingual test
    print("🌍 CROSS-LINGUAL :")
    tests = [
        ("fuite de mémoire après 24 heures", "memory leak after 24 hours"),
        ("condition de concurrence sur compteur", "race condition on counter"),
        ("exception pointeur null", "NullPointerException"),
        ("cache périmé après mise à jour", "stale cache after update"),
        ("injection SQL dans formulaire", "SQL injection in form"),
        ("serveur crash sous charge", "server crash under load"),
    ]
    scores = []
    for fr, en in tests:
        s = engine.encoder.interference(engine.encoder.encode(fr), engine.encoder.encode(en))
        scores.append(s)
        print(f"  {s:.4f}  {fr[:45]} ↔ {en[:45]}")
    print(f"  → Moyenne cross-lingual : {np.mean(scores):.4f}")
    
    # Patterns
    patterns = {
        "Onde Fantome": ["memory leak", "fuite de mémoire", "mémoire qui fuit", "RAM qui grossit",
                         "leak", "oom", "out of memory", "épuisement mémoire", "fuite mémoire",
                         "descripteurs non fermés", "connexions jamais libérées", "goroutine leak"],
        "Collision Phase": ["race condition", "condition de concurrence", "race", "concurrent",
                           "deadlock", "interblocage", "thread", "mutex", "lock", "verrou",
                           "accès concurrent", "modification concurrente"],
        "Absence Fréquence": ["null", "undefined", "None", "manquant", "introuvable", "absent",
                             "NullPointer", "KeyError", "FileNotFound", "not found",
                             "variable non définie", "référence null"],
        "Déphasage Temporel": ["stale", "périmé", "obsolète", "outdated", "cache", "session",
                              "token expiré", "refresh", "déphasé", "DNS cache", "ancienne version"],
        "Résonance Parasite": ["injection", "XSS", "CSRF", "sanitize", "validation", "escape",
                              "SQL injection", "script", "malveillant", "path traversal"],
    }
    
    for name, symptoms in patterns.items():
        engine.add_pattern(name=name, explanation=f"Pattern: {name}",
                          strategy="Voir action", action=f"Corriger {name}",
                          symptoms=symptoms)
    
    # Diagnostic test
    print(f"\n🧪 DIAGNOSTIC ({len(engine.patterns)} patterns) :")
    test_cases = [
        ("memory leak causing server crash after 2 days", "Onde Fantome"),
        ("race condition between worker threads", "Collision Phase"),
        ("NullPointerException in UserService.getProfile()", "Absence Fréquence"),
        ("fuite mémoire : le processus dépasse 4 Go", "Onde Fantome"),
        ("condition de concurrence sur le cache partagé", "Collision Phase"),
        ("variable None dans le template Jinja", "Absence Fréquence"),
        ("le cache n'est pas invalidé après la mise à jour", "Déphasage Temporel"),
        ("SQL injection in the search parameter", "Résonance Parasite"),
        ("injection SQL dans le paramètre de recherche", "Résonance Parasite"),
        ("stale cache after configuration deployment", "Déphasage Temporel"),
        ("serveur plante avec out of memory après 24h", "Onde Fantome"),
        ("deadlock between thread A and thread B", "Collision Phase"),
    ]
    
    correct = 0
    for symptom, expected in test_cases:
        diag = engine.diagnose(symptom)
        ok = diag.interference_type == expected
        if ok: correct += 1
        print(f"  {'✅' if ok else '❌'} {diag.interference_type:<22} (attendu: {expected:<22}) "
              f"conf={diag.confidence:.3f} | {symptom[:55]}")
    
    acc = correct / len(test_cases) * 100
    print(f"\n  📊 Accuracy : {acc:.0f}% ({correct}/{len(test_cases)})")
    print(f"  📈 vs v3 (hash)  : 54% → v6 (sémantique) : {acc:.0f}%")


if __name__ == "__main__":
    main()
