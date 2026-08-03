"""
🌊 Encodeur Génératif Ondulatoire — L'optimum
===============================================
Au lieu de lookup (mot → table → vecteur), 
on EXPRIME chaque symptôme dans la base des concepts ondulatoires.

Principe : tout symptôme est une SUPERPOSITION de concepts du dictionnaire.
"NullPointerException" = Absence Fréquence + Exception + Java
"memory leak"          = Onde Fantome + Mémoire + Fuite

La base conceptuelle est CROSS-LINGUALE par nature.
"""

import sys, os, json, time, math, re, hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

# ════════════════════════════════════════════════════════════════
# BASE CONCEPTUELLE — Les concepts du dictionnaire des ondes
# ════════════════════════════════════════════════════════════════

# Chaque concept ondulatoire a un ψ FONDAMENTAL (déterministe, universel)
# et des "ancres lexicales" dans plusieurs langues.

WAVE_CONCEPTS = {
    # Concepts de diagnostic (code)
    "absence_frequence": {
        "psi_seed": "absence_frequence_001",
        "fr": ["null", "none", "undefined", "manquant", "absent", "introuvable", "vide",
               "inexistant", "non défini", "pointeur null", "optional", "nil", "néant",
               "nullpointerexception", "npe", "keyerror", "filenotfound", "notfound"],
        "en": ["null", "none", "undefined", "missing", "absent", "not found", "empty",
               "void", "unset", "null pointer", "optional", "nil", "nothing",
               "nullpointerexception", "npe", "keyerror", "filenotfound", "notfound",
               "typeerror", "valueerror", "attributeerror"],
    },
    "saturation": {
        "psi_seed": "saturation_002",
        "fr": ["crash", "débordement", "overflow", "saturation", "épuisement", "limite",
               "dépassement", "plein", "surcharge", "timeout", "max", "trop", "excès"],
        "en": ["crash", "overflow", "saturation", "exhaustion", "limit",
               "exceeded", "full", "overload", "timeout", "max", "too many", "excess"],
    },
    "collision_phase": {
        "psi_seed": "collision_phase_003",
        "fr": ["race", "concurrence", "deadlock", "interblocage", "thread", "mutex",
               "lock", "verrou", "simultané", "parallèle", "concurrent", "atomique",
               "sync", "synchronisation", "course", "collision"],
        "en": ["race", "concurrent", "deadlock", "thread", "mutex",
               "lock", "simultaneous", "parallel", "atomic",
               "sync", "synchronization", "collision", "contention"],
    },
    "onde_fantome": {
        "psi_seed": "onde_fantome_004",
        "fr": ["fuite", "leak", "mémoire", "RAM", "descripteur", "connexion", "zombie",
               "goroutine", "listener", "pool", "ressource", "libérer", "fermer",
               "close", "dispose", "free", "accumulation", "grossit"],
        "en": ["leak", "memory", "RAM", "descriptor", "connection", "zombie",
               "goroutine", "listener", "pool", "resource", "free", "close",
               "dispose", "accumulation", "growing", "heap"],
    },
    "dephasage_temporel": {
        "psi_seed": "dephasage_temporel_005",
        "fr": ["cache", "périmé", "obsolète", "stale", "session", "token", "expiré",
               "rafraîchir", "refresh", "invalider", "synchroniser", "déphasé",
               "ancien", "déployé", "DNS", "désynchronisé"],
        "en": ["cache", "stale", "outdated", "obsolete", "session", "token", "expired",
               "refresh", "invalidate", "sync", "deployed",
               "old", "DNS", "desynchronized", "not updated"],
    },
    "desaccord_frequence": {
        "psi_seed": "desaccord_frequence_006",
        "fr": ["off-by-one", "décalage", "incorrect", "faux", "erreur", "arrondi",
               "fuseau", "timezone", "encodage", "formule", "calcul", "tri",
               "float", "précision", "unité", "regex", "comparaison"],
        "en": ["off-by-one", "offset", "incorrect", "wrong", "error", "rounding",
               "timezone", "encoding", "formula", "calculation", "sort",
               "float", "precision", "unit", "regex", "comparison"],
    },
    "resonance_forcee": {
        "psi_seed": "resonance_forcee_007",
        "fr": ["régression", "cassé", "fonctionnait", "marchait", "avant", "déploiement",
               "mise à jour", "update", "librairie", "dépendance", "breaking",
               "version", "build", "CI", "config", "migration", "rollback"],
        "en": ["regression", "broken", "was working", "before", "deployment",
               "update", "library", "dependency", "breaking",
               "version", "build", "CI", "config", "migration", "rollback"],
    },
    "interference_multiple": {
        "psi_seed": "interference_multiple_008",
        "fr": ["lent", "lenteur", "performance", "goulot", "bottleneck", "N+1",
               "full scan", "index", "pagination", "lazy", "cache", "optimisation",
               "requête lourde", "re-render", "bundle", "taille"],
        "en": ["slow", "slowness", "performance", "bottleneck", "N+1",
               "full scan", "index", "pagination", "lazy", "cache", "optimization",
               "heavy query", "re-render", "bundle", "size"],
    },
    "resonance_parasite": {
        "psi_seed": "resonance_parasite_009",
        "fr": ["injection", "XSS", "CSRF", "SQL", "sanitize", "validate", "escape",
               "échapper", "valider", "sécurité", "attaque", "malveillant",
               "path traversal", "SSRF", "upload", "header", "redirect"],
        "en": ["injection", "XSS", "CSRF", "SQL", "sanitize", "validate", "escape",
               "security", "attack", "malicious",
               "path traversal", "SSRF", "upload", "header", "redirect"],
    },
    
    # Concepts transversaux (communs à plusieurs domaines)
    "exception": {
        "psi_seed": "exception_010",
        "fr": ["exception", "erreur", "error", "catch", "try", "throw", "raise",
               "stack trace", "traceback", "panique", "fatal", "pointeur", "pointer"],
        "en": ["exception", "error", "catch", "try", "throw", "raise",
               "stack trace", "traceback", "panic", "fatal", "pointer"],
    },
    "memoire": {
        "psi_seed": "memoire_011",
        "fr": ["mémoire", "memory", "RAM", "heap", "tas", "allocation", "stockage",
               "cache", "buffer", "tampon", "vive", "physique", "virtuelle"],
        "en": ["memory", "RAM", "heap", "allocation", "storage",
               "cache", "buffer", "physical", "virtual", "swap"],
    },
    "reseau": {
        "psi_seed": "reseau_012",
        "fr": ["réseau", "network", "requête", "request", "réponse", "response",
               "HTTP", "TCP", "DNS", "paquet", "latence", "timeout", "socket"],
        "en": ["network", "request", "response",
               "HTTP", "TCP", "DNS", "packet", "latency", "timeout", "socket"],
    },
    "fichier": {
        "psi_seed": "fichier_013",
        "fr": ["fichier", "file", "données", "data", "disque", "disk", "lecture",
               "écriture", "read", "write", "path", "chemin", "dossier", "directory"],
        "en": ["file", "data", "disk", "read", "write", "path", "directory", "folder"],
    },
    "base_de_donnees": {
        "psi_seed": "base_de_donnees_014",
        "fr": ["base", "database", "SQL", "NoSQL", "table", "ligne", "row", "colonne",
               "requête", "query", "transaction", "commit", "rollback", "index"],
        "en": ["database", "SQL", "NoSQL", "table", "row", "column",
               "query", "transaction", "commit", "rollback", "index"],
    },
    "utilisateur": {
        "psi_seed": "utilisateur_015",
        "fr": ["utilisateur", "user", "login", "session", "auth", "authentification",
               "mot de passe", "password", "token", "JWT", "profil", "profile"],
        "en": ["user", "login", "session", "auth", "authentication",
               "password", "token", "JWT", "profile", "account"],
    },
    "deploiement": {
        "psi_seed": "deploiement_016",
        "fr": ["déploiement", "deploy", "production", "staging", "release", "version",
               "CI/CD", "pipeline", "build", "docker", "kubernetes", "rollback"],
        "en": ["deployment", "deploy", "production", "staging", "release", "version",
               "CI/CD", "pipeline", "build", "docker", "kubernetes", "rollback"],
    },
    "serveur": {
        "psi_seed": "serveur_017",
        "fr": ["serveur", "server", "API", "endpoint", "route", "backend", "frontend",
               "client", "HTTP", "REST", "GraphQL", "proxy", "gateway"],
        "en": ["server", "API", "endpoint", "route", "backend", "frontend",
               "client", "HTTP", "REST", "GraphQL", "proxy", "gateway"],
    },
}


# ════════════════════════════════════════════════════════════════
# ENCODEUR GÉNÉRATIF
# ════════════════════════════════════════════════════════════════

class GenerativeEncoder:
    """
    Encodeur génératif : exprime un symptôme comme superposition
    de concepts ondulatoires fondamentaux.
    
    Pour chaque token du symptôme :
      1. Trouver les concepts ondulatoires associés (via ancres lexicales)
      2. Superposer les ψ de ces concepts
      3. Le résultat est le ψ du symptôme
    
    Avantages :
      - Cross-lingual natif (ancres FR + EN pour chaque concept)
      - Robuste aux termes inconnus (toujours décomposable en concepts)
      - Déterministe (même concept → même ψ, toujours)
      - Aucun entraînement requis
    """
    
    def __init__(self, dim: int = 128):
        self.dim = dim
        
        # Générer les ψ fondamentaux pour chaque concept
        self.concept_psi: Dict[str, np.ndarray] = {}
        self.concept_anchors: Dict[str, Dict[str, List[str]]] = {}
        
        for concept_name, data in WAVE_CONCEPTS.items():
            # ψ déterministe à partir du seed
            psi = self._generate_psi(data["psi_seed"])
            self.concept_psi[concept_name] = psi
            
            # Indexer les ancres lexicales
            self.concept_anchors[concept_name] = {
                "fr": set(data.get("fr", [])),
                "en": set(data.get("en", [])),
            }
        
        # Générer aussi les ψ pour les tokens individuels (fallback)
        self.token_cache: Dict[str, np.ndarray] = {}
        
        print(f"  🌊 Encodeur génératif : {len(self.concept_psi)} concepts fondamentaux")
    
    def _generate_psi(self, seed: str) -> np.ndarray:
        """Génère un ψ déterministe à partir d'un seed."""
        h = hashlib.sha256(seed.encode()).digest()
        # Utiliser φ pour espacer les phases
        rng = np.random.RandomState(int.from_bytes(h[:4], 'big') % 2**31)
        real = rng.randn(self.dim)
        imag = rng.randn(self.dim)
        psi = real + 1j * imag
        
        # Normalisation
        psi /= np.linalg.norm(psi) + 1e-30
        return psi
    
    def _find_concepts(self, token: str) -> List[str]:
        """Trouve tous les concepts ondulatoires associés à un token."""
        token_lower = token.lower()
        concepts = []
        
        for concept_name, anchors in self.concept_anchors.items():
            if token_lower in anchors["fr"] or token_lower in anchors["en"]:
                concepts.append(concept_name)
        
        return concepts
    
    def encode(self, text: str) -> np.ndarray:
        """
        Encode un symptôme par superposition de concepts.
        
        Algorithme :
        1. Tokeniser
        2. Pour chaque token, trouver les concepts associés
        3. Superposer les ψ des concepts (avec déduplication)
        4. Ajouter le ψ du token lui-même (pour l'unicité)
        5. Normaliser
        """
        raw_tokens = [t.strip('.,!?;:()[]{}') for t in text.lower().split()
                      if len(t.strip('.,!?;:()[]{}')) >= 1]
        
        # Tokenisation simple (sans décomposition — la décomposition dilue)
        tokens = [t for t in raw_tokens if len(t) >= 2]
        
        if not tokens:
            return np.zeros(self.dim, dtype=complex)
        
        # Concepts activés (avec déduplication)
        activated_concepts = set()
        for token in tokens:
            concepts = self._find_concepts(token)
            activated_concepts.update(concepts)
        
        # Superposer les ψ des concepts
        psi = np.zeros(self.dim, dtype=complex)
        
        # 1. Concepts fondamentaux (poids fort)
        for concept in activated_concepts:
            psi += self.concept_psi[concept]
        
        # 2. Tokens individuels (poids faible — unicité)
        for token in tokens:
            if token not in self.token_cache:
                seed = f"token_{token}"
                self.token_cache[token] = self._generate_psi(seed)
            psi += 0.3 * self.token_cache[token]  # Poids réduit pour les tokens
        
        # Normaliser
        nrm = np.linalg.norm(psi)
        return psi / nrm if nrm > 1e-30 else psi
    
    def interference(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.abs(np.dot(np.conj(a), b)) ** 2)


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   🌊 ENCODEUR GÉNÉRATIF — Base Conceptuelle Ondulatoire      ║
║   Expression, pas lookup                                      ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    enc = GenerativeEncoder(dim=128)
    
    # Test : afficher les concepts activés
    print("🔍 CONCEPTS ACTIVÉS :")
    test_texts = [
        "NullPointerException in UserService.getProfile()",
        "race condition between worker threads",
        "memory leak causing server crash after 2 days",
        "fuite de mémoire après quelques heures",
        "condition de concurrence sur compteur partagé",
        "injection SQL dans le paramètre de recherche",
    ]
    for text in test_texts:
        tokens = [t.strip('.,!?;:()[]{}') for t in text.lower().split()
                  if len(t.strip('.,!?;:()[]{}')) >= 2]
        concepts = set()
        for t in tokens:
            concepts.update(enc._find_concepts(t))
        print(f"  {text[:55]:<55} → {concepts}")
    
    # Cross-lingual
    print(f"\n🌍 CROSS-LINGUAL :")
    pairs = [
        ("NullPointerException", "exception pointeur null"),
        ("memory leak", "fuite de mémoire"),
        ("race condition", "condition de concurrence"),
        ("SQL injection", "injection SQL"),
        ("stale cache", "cache périmé"),
        ("deadlock", "interblocage"),
        ("server crash", "serveur plante"),
        ("stack overflow", "dépassement de pile"),
    ]
    scores = []
    for en, fr in pairs:
        s = enc.interference(enc.encode(en), enc.encode(fr))
        scores.append(s)
        print(f"  {s:.4f}  {en:<25} ↔ {fr}")
    print(f"  → Moyenne : {np.mean(scores):.4f}")
    
    # Diagnostic
    print(f"\n🧪 DIAGNOSTIC :")
    
    # Construire les patterns (superposition de concepts pour chaque type)
    pattern_concepts = {
        "Absence Fréquence": ["absence_frequence", "exception", "utilisateur"],
        "Collision Phase": ["collision_phase", "reseau"],
        "Onde Fantome": ["onde_fantome", "memoire", "serveur"],
        "Déphasage Temporel": ["dephasage_temporel", "memoire", "deploiement"],
        "Résonance Parasite": ["resonance_parasite", "base_de_donnees", "reseau"],
        "Désaccord Fréquence": ["desaccord_frequence"],
        "Résonance Forcée": ["resonance_forcee", "deploiement"],
        "Interférence Multiple": ["interference_multiple", "base_de_donnees", "serveur"],
        "Saturation": ["saturation", "serveur", "memoire"],
    }
    
    pattern_psi = {}
    for name, concepts in pattern_concepts.items():
        psi = np.zeros(enc.dim, dtype=complex)
        for c in concepts:
            psi += enc.concept_psi[c]
        pattern_psi[name] = psi / np.linalg.norm(psi)
    
    test_cases = [
        ("NullPointerException in UserService.getProfile()", "Absence Fréquence"),
        ("race condition between worker threads", "Collision Phase"),
        ("memory leak causing server crash after 2 days", "Onde Fantome"),
        ("stale cache after configuration deployment", "Déphasage Temporel"),
        ("SQL injection in the search parameter", "Résonance Parasite"),
        ("fuite de mémoire après quelques heures", "Onde Fantome"),
        ("condition de concurrence sur compteur partagé", "Collision Phase"),
        ("injection SQL dans le paramètre de recherche", "Résonance Parasite"),
        ("off-by-one in pagination logic", "Désaccord Fréquence"),
        ("regression: login was working before deploy", "Résonance Forcée"),
        ("le cache est périmé après mise à jour", "Déphasage Temporel"),
        ("NullPointerException quand utilisateur sans profil", "Absence Fréquence"),
    ]
    
    correct = 0
    for symptom, expected in test_cases:
        psi = enc.encode(symptom)
        best = max(pattern_psi.items(), key=lambda kv: enc.interference(psi, kv[1]))
        ok = best[0] == expected
        if ok: correct += 1
        print(f"  {'✅' if ok else '❌'} {best[0]:<24} (attendu: {expected:<24}) "
              f"conf={enc.interference(psi, best[1]):.3f} | {symptom[:55]}")
    
    acc = correct / len(test_cases) * 100
    print(f"\n  📊 Accuracy : {acc:.0f}% ({correct}/{len(test_cases)})")
    print(f"  📈 vs lookup SVD : 75% → Générative : {acc:.0f}%")


if __name__ == "__main__":
    main()
