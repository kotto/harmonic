"""
🌊 DebugEmbedding — Plongement Sémantique Spécialisé pour le Diagnostic
=========================================================================
Crée un embedding dédié au diagnostic de bugs en exploitant :
1. Le corpus de patterns de debug (FR + EN, 500+ symptômes)
2. Les concepts du Dictionnaire des Ondes comme "ponts" cross-linguaux
3. La fusion avec le LearnedEmbedding général (110K faits)

Principe clé : chaque terme technique a une TRADUCTION ONDULATOIRE
qui sert de concept-pont entre les langues.

Ex: "NullPointerException" → "Absence Fréquence" ← "exception pointeur null"
"""

import sys, os, json, time, math, re
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple, Optional
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

# ════════════════════════════════════════════════════════════════
# CORPUS SPÉCIALISÉ — Symptômes + Dictionnaire
# ════════════════════════════════════════════════════════════════

# Les "ponts ondulatoires" du dictionnaire — concepts cross-linguaux
WAVE_BRIDGES = {
    "Absence Fréquence": {
        "fr": ["exception pointeur null", "variable non définie", "référence manquante",
               "clé absente", "fichier introuvable", "module manquant", "donnée vide",
               "null pointer", "undefined", "None", "nil", "optional non unwrap",
               "segment non alloué", "erreur 404", "référence null"],
        "en": ["NullPointerException", "undefined variable", "missing reference",
               "key not found", "file not found", "module not installed", "empty data",
               "null pointer", "undefined is not a function", "NoneType error",
               "optional not unwrapped", "segmentation fault", "404 not found",
               "cannot read property of null", "dereferencing null pointer"],
    },
    "Saturation": {
        "fr": ["serveur qui crash sous charge", "dépassement de capacité", "stack overflow",
               "out of memory", "timeout dépassé", "cpu saturé", "buffer overflow",
               "rate limit atteint", "queue saturée", "disque plein", "mémoire GPU pleine",
               "trop de connexions", "surcharge système"],
        "en": ["server crash under load", "capacity overflow", "stack overflow error",
               "out of memory exception", "timeout exceeded", "cpu saturated", "buffer overflow",
               "rate limit exceeded", "queue saturated", "disk full", "GPU memory exhausted",
               "too many connections", "system overload", "heap limit reached"],
    },
    "Collision Phase": {
        "fr": ["race condition", "deadlock entre threads", "accès concurrent",
               "modification concurrente", "dirty read", "lost update",
               "double réservation", "solde incohérent", "workers en conflit",
               "cache incohérent entre nœuds", "idempotence violée",
               "condition de concurrence", "interblocage", "transaction concurrente"],
        "en": ["race condition", "deadlock between threads", "concurrent access",
               "concurrent modification", "dirty read", "lost update",
               "double booking", "inconsistent balance", "conflicting workers",
               "cache inconsistency between nodes", "idempotency violation",
               "race hazard", "thread safety violation", "concurrent transaction"],
    },
    "Onde Fantome": {
        "fr": ["fuite de mémoire", "descripteurs non fermés", "connexions jamais libérées",
               "processus zombie", "goroutine qui fuit", "cache sans éviction",
               "websocket fantôme", "thread pool non libéré", "listener non retiré",
               "mémoire qui grossit", "ressource non libérée", "fuite RAM"],
        "en": ["memory leak", "file descriptors not closed", "connections never freed",
               "zombie process", "goroutine leak", "cache without eviction",
               "ghost websocket", "thread pool not released", "listener not removed",
               "memory growing", "resource not freed", "RAM leak", "heap exhaustion"],
    },
    "Déphasage Temporel": {
        "fr": ["cache périmé", "données obsolètes", "token expiré", "session périmée",
               "ancienne version affichée", "DNS cache périmé", "permissions non synchronisées",
               "fichier non actualisé", "compteur bloqué", "état déphasé",
               "cache stale", "données non rafraîchies", "désynchronisation"],
        "en": ["stale cache", "outdated data", "expired token", "stale session",
               "old version displayed", "DNS cache stale", "permissions not synced",
               "file not refreshed", "stuck counter", "out of sync state",
               "stale reference", "data not refreshed", "desynchronization"],
    },
    "Désaccord Fréquence": {
        "fr": ["off-by-one", "erreur de calcul", "arrondi incorrect", "fuseau horaire faux",
               "encodage incorrect", "formule erronée", "tri incorrect",
               "comparaison float", "unité incorrecte", "regex trop gourmand",
               "résultat décalé", "mauvais calcul", "erreur de précision"],
        "en": ["off-by-one error", "calculation error", "incorrect rounding", "wrong timezone",
               "encoding error", "wrong formula", "incorrect sorting",
               "float comparison", "wrong unit", "greedy regex",
               "off result", "miscalculation", "precision error"],
    },
    "Résonance Forcée": {
        "fr": ["régression après déploiement", "cassé après mise à jour", "API changée",
               "schéma non rétrocompatible", "design cassé sur mobile", "breaking change",
               "build passe en local pas en CI", "config production écrase dev",
               "migration échoue", "fonctionnait avant", "dépendance cassée"],
        "en": ["regression after deployment", "broken after update", "API changed",
               "schema not backward compatible", "design broken on mobile", "breaking change",
               "build passes locally not CI", "production config overrides dev",
               "migration fails", "was working before", "dependency broken"],
    },
    "Interférence Multiple": {
        "fr": ["requête lente", "API lente", "page lente à charger", "goulot d'étranglement",
               "N+1 queries", "thread principal bloqué", "JSON lent", "dashboard figé",
               "React re-render excessif", "full scan table", "performance dégradée",
               "lenteur", "temps de réponse élevé", "surcharge Base de données"],
        "en": ["slow query", "slow API", "slow page load", "bottleneck",
               "N+1 queries", "main thread blocked", "slow JSON", "frozen dashboard",
               "excessive React re-render", "full table scan", "degraded performance",
               "slowness", "high response time", "database overload"],
    },
    "Résonance Parasite": {
        "fr": ["injection SQL", "faille XSS", "CSRF", "path traversal", "command injection",
               "upload malveillant", "SSRF", "open redirect", "header injection",
               "deserialization attack", "input non validé", "échappement manquant",
               "faille de sécurité", "attaque par injection"],
        "en": ["SQL injection", "XSS vulnerability", "CSRF attack", "path traversal",
               "command injection", "malicious upload", "SSRF", "open redirect",
               "header injection", "deserialization attack", "unvalidated input",
               "missing escape", "security vulnerability", "injection attack"],
    },
}


# ════════════════════════════════════════════════════════════════
# CONSTRUCTION DU CORPUS
# ════════════════════════════════════════════════════════════════

def build_debug_corpus(wave_bridges: dict) -> List[List[str]]:
    """
    Construit un corpus de « phrases » pour l'entraînement PPMI.
    
    Chaque « phrase » est une liste de tokens qui apparaissent ensemble.
    Stratégie :
    1. Chaque symptôme est une phrase (les tokens co-occurrent)
    2. Chaque pont ondulatoire génère des paires cross-linguales
    3. Le nom du concept ondulatoire est injecté comme token-pont
    """
    sentences = []
    cross_lingual_pairs = 0
    
    for wave_concept, langs in wave_bridges.items():
        # Le concept ondulatoire lui-même devient un token-pont
        bridge_token = wave_concept.lower().replace(" ", "_")
        
        fr_symptoms = langs.get("fr", [])
        en_symptoms = langs.get("en", [])
        
        # 1. Chaque symptôme FR est une phrase avec le token-pont
        for sym in fr_symptoms:
            tokens = [t.strip('.,!?;:()[]{}') for t in sym.lower().split() if len(t.strip('.,!?;:()[]{}')) >= 2]
            tokens.append(bridge_token)  # Injecter le pont
            if len(tokens) >= 2:
                sentences.append(tokens)
        
        # 2. Chaque symptôme EN est une phrase avec le token-pont
        for sym in en_symptoms:
            tokens = [t.strip('.,!?;:()[]{}') for t in sym.lower().split() if len(t.strip('.,!?;:()[]{}')) >= 2]
            tokens.append(bridge_token)
            if len(tokens) >= 2:
                sentences.append(tokens)
        
        # 3. Paires cross-linguales directes
        for fr_sym in fr_symptoms[:5]:
            fr_tokens = [t.strip('.,!?;:()[]{}') for t in fr_sym.lower().split() if len(t.strip('.,!?;:()[]{}')) >= 2]
            for en_sym in en_symptoms[:5]:
                en_tokens = [t.strip('.,!?;:()[]{}') for t in en_sym.lower().split() if len(t.strip('.,!?;:()[]{}')) >= 2]
                mixed = fr_tokens[:3] + [bridge_token] + en_tokens[:3]
                sentences.append(mixed)
                cross_lingual_pairs += 1
        
        # 4. 🔥 Paires de TOKENS directs FR↔EN (force l'alignement)
        # Pour chaque token FR, on crée une phrase avec son équivalent EN
        # Cela force la SVD à les rapprocher
        for fr_sym in fr_symptoms:
            for en_sym in en_symptoms:
                fr_tokens = [t.strip('.,!?;:()[]{}') for t in fr_sym.lower().split() if len(t.strip('.,!?;:()[]{}')) >= 2]
                en_tokens = [t.strip('.,!?;:()[]{}') for t in en_sym.lower().split() if len(t.strip('.,!?;:()[]{}')) >= 2]
                # Phrase : token_FR + token_EN + pont (3 mots qui DOIVENT co-occurr)
                for ft in fr_tokens[:5]:
                    for et in en_tokens[:5]:
                        if ft != et and len(ft) >= 3 and len(et) >= 3:
                            sentences.append([ft, et, bridge_token])
                            cross_lingual_pairs += 1
    
    print(f"  Corpus debug : {len(sentences)} phrases, {cross_lingual_pairs} paires cross-linguales")
    return sentences


# ════════════════════════════════════════════════════════════════
# PPMI + SVD (inspiré de learned_embedding.py)
# ════════════════════════════════════════════════════════════════

def build_ppmi(sentences: List[List[str]], window: int = 3, 
               min_freq: int = 1) -> Tuple[np.ndarray, Dict[str, int]]:
    """Construit la matrice PPMI à partir des phrases."""
    
    # Vocabulaire
    word_counts = Counter()
    for sent in sentences:
        for w in sent:
            word_counts[w] += 1
    
    vocab = {w: i for i, (w, c) in enumerate(word_counts.items()) if c >= min_freq}
    V = len(vocab)
    print(f"  PPMI : {V} mots uniques (min_freq={min_freq})")
    
    # Co-occurrences
    cooc = Counter()
    for sent in sentences:
        indices = [vocab[w] for w in sent if w in vocab]
        for i, wi in enumerate(indices):
            for j in range(max(0, i-window), min(len(indices), i+window+1)):
                if i != j:
                    wj = indices[j]
                    cooc[(wi, wj)] += 1
                    cooc[(wj, wi)] += 1
    
    # Matrice PPMI sparse
    from scipy.sparse import lil_matrix
    ppm = lil_matrix((V, V), dtype=np.float64)
    
    total = sum(cooc.values()) + V * V  # Lissage
    word_totals = {i: sum(c for (a, b), c in cooc.items() if a == i) + V for i in range(V)}
    
    for (i, j), count in cooc.items():
        if count > 0:
            p_ij = count / total
            p_i = word_totals[i] / total
            p_j = word_totals[j] / total
            ppmi = max(0, math.log(p_ij / (p_i * p_j + 1e-30) + 1e-30))
            if ppmi > 0:
                ppm[i, j] = ppmi
    
    return ppm.tocsr(), vocab


def svd_embed(ppm, vocab: Dict[str, int], dim: int = 128) -> Dict[str, np.ndarray]:
    """SVD sur PPMI → vecteurs sémantiques complexes."""
    from scipy.sparse.linalg import svds
    
    V = len(vocab)
    k = min(dim * 2, V - 2)
    if k < 2:
        return {}
    
    print(f"  SVD : {k} composantes...", end=" ", flush=True)
    U, S, Vt = svds(ppm, k=k)
    print("✓")
    
    # Convertir en vecteurs complexes : real = U[:dim], imag = U[dim:2*dim]
    vectors = {}
    idx_to_word = {i: w for w, i in vocab.items()}
    
    for i in range(V):
        real_part = U[i, :dim] if dim <= k else np.pad(U[i, :k], (0, dim-k))
        imag_part = U[i, dim:2*dim] if 2*dim <= k else np.zeros(dim)
        if 2*dim > k and dim <= k:
            imag_part = np.zeros(dim)
            imag_part[:k-dim] = U[i, dim:k]
        
        vec = real_part + 1j * imag_part
        nrm = np.linalg.norm(vec)
        if nrm > 1e-30:
            vec /= nrm
        
        vectors[idx_to_word[i]] = vec
    
    return vectors


# ════════════════════════════════════════════════════════════════
# DEBUG EMBEDDING
# ════════════════════════════════════════════════════════════════

class DebugEmbedding:
    """
    Plongement spécialisé pour le diagnostic de bugs.
    
    Fusionne :
    1. Embedding debug (PPMI+SVD sur le corpus spécialisé)
    2. LearnedEmbedding général (fallback)
    3. Hash (dernier recours)
    """
    
    def __init__(self, dim: int = 128):
        self.dim = dim
        self.debug_vectors: Dict[str, np.ndarray] = {}
        self.general_embedding = None
        
        # Charger le général
        try:
            from learned_embedding import get_learned_embedding
            self.general_embedding = get_learned_embedding()
            print(f"  📚 Général : {len(self.general_embedding.vectors)} mots")
        except Exception:
            pass
    
    def train(self, corpus_sentences: List[List[str]], min_freq: int = 1):
        """Entraîne l'embedding debug sur le corpus."""
        t0 = time.time()
        
        ppm, vocab = build_ppmi(corpus_sentences, min_freq=min_freq)
        if len(vocab) < 5:
            print("  ⚠️ Vocabulaire trop petit")
            return
        
        self.debug_vectors = svd_embed(ppm, vocab, dim=self.dim)
        print(f"  ✅ Debug embedding entraîné : {len(self.debug_vectors)} mots "
              f"({time.time()-t0:.1f}s)")
    
    def get_vector(self, word: str) -> Optional[np.ndarray]:
        """
        Récupère le meilleur vecteur pour un mot.
        Priorité : Debug > Général > None (→ hash)
        """
        w = word.lower().strip()
        
        # 1. Debug embedding
        if w in self.debug_vectors:
            return self.debug_vectors[w]
        
        # 2. Concept-pont (mot_composé)
        bridge = w.replace(" ", "_")
        if bridge in self.debug_vectors:
            return self.debug_vectors[bridge]
        
        # 3. Général (LearnedEmbedding)
        if self.general_embedding:
            vec = self.general_embedding.get_vector(w)
            if vec is not None:
                if len(vec) != self.dim:
                    p = np.zeros(self.dim, dtype=complex)
                    p[:min(len(vec), self.dim)] = vec[:min(len(vec), self.dim)]
                    return p
                return vec
        
        return None
    
    def encode_text(self, text: str) -> np.ndarray:
        """Encode un texte complet en vecteur d'onde."""
        tokens = [t.strip('.,!?;:()[]{}') for t in text.lower().split()
                  if len(t.strip('.,!?;:()[]{}')) >= 2]
        if not tokens:
            return np.zeros(self.dim, dtype=complex)
        
        psi = np.zeros(self.dim, dtype=complex)
        for token in tokens:
            vec = self.get_vector(token)
            if vec is None:
                # Hash fallback
                h = hash(token) & 0xFFFFFFFF
                rng = np.random.RandomState(h)
                vec = rng.randn(self.dim) + 1j * rng.randn(self.dim)
                vec /= np.linalg.norm(vec) + 1e-30
            psi += vec
        
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
║   🌊 DEBUG EMBEDDING — Plongement Sémantique Optimal         ║
║   Corpus debug + Ponts ondulatoires + Learned général         ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    # 1. Construire le corpus
    print("📝 Construction du corpus...")
    corpus = build_debug_corpus(WAVE_BRIDGES)
    
    # 2. Entraîner
    print("🧠 Entraînement du DebugEmbedding...")
    emb = DebugEmbedding(dim=128)
    emb.train(corpus, min_freq=1)
    
    # 3. Test cross-lingual
    print(f"\n🌍 TEST CROSS-LINGUAL :")
    test_pairs = [
        ("NullPointerException", "exception pointeur null"),
        ("memory leak", "fuite de mémoire"),
        ("race condition", "condition de concurrence"),
        ("SQL injection", "injection SQL"),
        ("stale cache", "cache périmé"),
        ("deadlock", "interblocage"),
        ("off-by-one", "erreur de calcul"),
        ("stack overflow", "dépassement de pile"),
    ]
    
    scores = []
    for en, fr in test_pairs:
        psi_en = emb.encode_text(en)
        psi_fr = emb.encode_text(fr)
        s = emb.interference(psi_en, psi_fr)
        scores.append(s)
        print(f"  {s:.4f}  {en:<25} ↔ {fr:<30}")
    
    avg = np.mean(scores)
    print(f"\n  📊 Cross-lingual moyen : {avg:.4f}")
    print(f"     vs v6 sans attention : 0.10 → DebugEmbedding : {avg:.4f}")
    
    # 4. Test diagnostic rapide
    print(f"\n🧪 TEST DIAGNOSTIC :")
    
    # Construire les patterns avec l'embedding debug
    patterns = {}
    for wave_concept, langs in WAVE_BRIDGES.items():
        all_symptoms = langs.get("fr", []) + langs.get("en", [])
        psi_sum = np.zeros(emb.dim, dtype=complex)
        for sym in all_symptoms:
            psi_sum += emb.encode_text(sym)
        patterns[wave_concept] = psi_sum / max(len(all_symptoms), 1)
    
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
        psi = emb.encode_text(symptom)
        best = max(patterns.items(), key=lambda kv: emb.interference(psi, kv[1]))
        ok = best[0] == expected
        if ok: correct += 1
        print(f"  {'✅' if ok else '❌'} {best[0]:<24} (attendu: {expected:<24}) "
              f"conf={emb.interference(psi, best[1]):.3f} | {symptom[:55]}")
    
    acc = correct / len(test_cases) * 100
    print(f"\n  📊 Accuracy : {acc:.0f}% ({correct}/{len(test_cases)})")
    print(f"  📈 vs v3 (hash) : 54% → v6 (général) : 75% → DebugEmbedding : {acc:.0f}%")
    
    if acc >= 90:
        print(f"\n  🎉 OBJECTIF ATTEINT !")
    
    # Sauvegarde
    save_path = Path(__file__).parent / "data" / "debug_embedding.npz"
    try:
        real_parts, imag_parts, words = [], [], []
        for w, v in emb.debug_vectors.items():
            words.append(w)
            real_parts.append(np.real(v))
            imag_parts.append(np.imag(v))
        np.savez(save_path, words=np.array(words), 
                 real=np.array(real_parts), imag=np.array(imag_parts),
                 dim=emb.dim)
        print(f"\n💾 Sauvegardé : {save_path}")
    except Exception as e:
        print(f"\n⚠️ Sauvegarde ignorée : {e}")


if __name__ == "__main__":
    main()
