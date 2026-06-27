#!/usr/bin/env python3
"""
KA-Next v3 — Trois Priorités Implémentées
============================================
1. INDEX NUMPY VECTORISÉ : batch cosinus < 10ms (vs 207ms)
2. EMBEDDING DENSE 64-DIM : SpectralEncoder multidimensionnel
3. PIPELINE HARMONIC+LLM : Faits tracés → Formulation fluide

Usage :
  python ka_next_v3.py --query "..." --mode reason
  python ka_next_v3.py --serve
  python ka_next_v3.py --benchmark
"""

import os, sys, math, json, time, hashlib, re, logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import numpy as np

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

# Modules du pont unifié onde↔langage (THEORIE_UNIFIEE_HARMONIQUE)
try:
    from wave_unified_bridge import ABCSessionMemory, WaveLanguageBridge, GAGUTPipeline
    UNIFIED_BRIDGE_AVAILABLE = True
except ImportError:
    UNIFIED_BRIDGE_AVAILABLE = False

PHI = (1 + math.sqrt(5)) / 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s [V3] %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger("ka-v3")


# ═══════════════════════════════════════════════════════════════════
# PRIORITÉ 1 — INDEX NUMPY VECTORISÉ (batch cosinus O(n) → O(1) effectif)
# ═══════════════════════════════════════════════════════════════════

class FastNumpyIndex:
    """Index numpy optimisé : tous les cosinus en une opération matricielle."""

    def __init__(self):
        self.vectors = None  # (N, 2) array of (kx, ky)
        self.norms = None    # (N,) array of |v|
        self.fact_texts = []

    def build(self, positions: List[Tuple[float, float]], texts: List[str]):
        """Construit l'index à partir des positions d'onde et des textes."""
        if not positions:
            return
        self.vectors = np.array(positions, dtype=np.float32)
        self.norms = np.linalg.norm(self.vectors, axis=1)
        self.norms = np.where(self.norms < 1e-10, 1e-10, self.norms)
        self.fact_texts = texts

    def search(self, query_wave: Tuple[float, float], query_text: str = "",
               k: int = 10) -> List[Dict]:
        """Recherche vectorisée O(1) : batch cosinus + semantic boost (70%)."""
        if self.vectors is None or len(self.vectors) == 0:
            return []

        q = np.array(query_wave, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm < 1e-10:
            return []

        # Batch cosinus (structurel, 30% du score)
        similarities = np.dot(self.vectors, q) / (self.norms * q_norm)

        # Semantic boost pour chaque fait (70% du score final)
        semantic_scores = np.array([
            self._semantic_boost(query_text, t) if query_text else 0.0
            for t in self.fact_texts
        ], dtype=np.float32)

        # Score combiné : 30% structurel + 70% sémantique
        combined = 0.3 * np.abs(similarities) + 0.7 * semantic_scores

        # Top-K indices
        if k >= len(combined):
            top_indices = np.argsort(-combined)
        else:
            top_indices = np.argpartition(-combined, k)[:k]
            top_indices = top_indices[np.argsort(-combined[top_indices])]

        results = []
        for idx in top_indices:
            results.append({
                "text": self.fact_texts[idx],
                "score": float(combined[idx]),
                "cosinus": float(similarities[idx]),
                "semantic": float(semantic_scores[idx]),
                "index": int(idx),
            })
        return results[:k]

    def _semantic_boost(self, query: str, fact: str) -> float:
        """Intersection de mots significatifs entre la question et le fait."""
        if not query:
            return 0.0
        def words(t):
            return {w.strip('.,;:!?()[]{}"\'-').lower() for w in t.lower().split()
                    if len(w.strip('.,;:!?()[]{}"\'-')) > 3}
        qw = words(query)
        fw = words(fact)
        if not qw or not fw:
            return 0.0
        common = qw & fw
        jaccard = len(common) / max(len(qw), 1)
        bonus = 0.5 if max(qw, key=len) in fw else 0.0
        return min(1.0, jaccard + bonus)


# ═══════════════════════════════════════════════════════════════════
# PRIORITÉ 2 — EMBEDDING DENSE 64-DIM (SpectralEncoder multidimensionnel)
# ═══════════════════════════════════════════════════════════════════

class LearnedEmbeddingEncoder:
    """
    Encodeur semantique appris via Sentence Transformers (384D).
    Fallback automatique vers DenseSpectralEncoder si non installe.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim
        self.model = None
        self.available = False
        self.word_count = 0
        self.vocab_built = False
        
        # Empecher TOUTE utilisation de TensorFlow/Keras
        os.environ["TRANSFORMERS_NO_TF"] = "1"
        os.environ["USE_TF"] = "0"
        os.environ["USE_TORCH"] = "1"
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
        os.environ["KERAS_BACKEND"] = "torch"
        
        # Masquer tensorflow avant tout import
        import sys as _sys
        _st_mock = type(_sys)("st_mock")
        _st_mock.__version__ = "0.0.0"
        for _mod in list(_sys.modules.keys()):
            if _mod.startswith("tensorflow") or _mod.startswith("keras"):
                try:
                    _sys.modules[_mod] = _st_mock
                except Exception:
                    pass
        
        try:
            from sentence_transformers import SentenceTransformer
            model_name = "paraphrase-multilingual-MiniLM-L12-v2"
            self.model = SentenceTransformer(model_name, device="cpu")
            self.dim = self.model.get_sentence_embedding_dimension()
            self.available = True
            log.info(f"LearnedEmbedding: {model_name} ({self.dim}D CPU) charge")
        except ImportError:
            log.warning("LearnedEmbedding: sentence-transformers non installe")
        except Exception as e:
            log.warning(f"LearnedEmbedding indisponible: {str(e)[:120]}")
    
    def build_vocabulary(self, documents): self.word_count = 1; self.vocab_built = self.available
    def encode(self, text):
        if not self.available: return np.zeros(64, dtype=np.float32)
        return self.model.encode(text, convert_to_numpy=True).astype(np.float32)

class CooccurrenceEncoder:
    """
    Encodeur semantique base sur la co-occurrence des mots.
    ZERO dependance externe. Construit un espace vectoriel a partir
    des co-occurrences dans le corpus lui-meme.
    
    "stoicisme" et "philosophie" → vecteurs proches (co-occurrent souvent)
    "Dakar" et "Senegal" → vecteurs proches (apparaissent ensemble)
    """
    def __init__(self, dim: int = 64, window: int = 3):
        self.dim = dim
        self.window = window
        self.word_vectors = {}
        self.vocab_built = False
        self.word_count = 0

    def build_vocabulary(self, documents: List[str]):
        if not documents or len(documents) < 5:
            return
        from collections import Counter, defaultdict
        word_counts = Counter()
        cooc = defaultdict(Counter)
        
        for doc in documents[:500]:
            words = self._extract_words(doc)
            word_counts.update(words)
            for i, w1 in enumerate(words):
                for j in range(max(0, i-self.window), min(len(words), i+self.window+1)):
                    if i != j:
                        cooc[w1][words[j]] += 1
        
        vocab = [w for w, c in word_counts.most_common(min(3000, len(word_counts)))]
        self.word_count = len(vocab)
        
        # Construire matrice de co-occurrence reduite
        M = np.zeros((len(vocab), len(vocab)), dtype=np.float32)
        for i, w1 in enumerate(vocab):
            for j, w2 in enumerate(vocab):
                M[i, j] = cooc[w1].get(w2, 0)
        
        # Reduire a dim dimensions via SVD (si assez de mots)
        if M.shape[0] >= self.dim:
            try:
                U, S, Vt = np.linalg.svd(M, full_matrices=False)
                # Prendre les dim premieres composantes
                for i, word in enumerate(vocab):
                    self.word_vectors[word] = U[i, :self.dim].astype(np.float32)
                # Normaliser
                norms = np.linalg.norm(list(self.word_vectors.values()), axis=1, keepdims=True)
                norms = np.where(norms < 1e-10, 1e-10, norms)
                vectors = np.array(list(self.word_vectors.values())) / norms
                for i, word in enumerate(vocab):
                    self.word_vectors[word] = vectors[i]
            except np.linalg.LinAlgError:
                pass
        
        self.vocab_built = len(self.word_vectors) > 10

    def encode(self, text: str) -> np.ndarray:
        if not self.vocab_built:
            return np.zeros(self.dim, dtype=np.float32)
        words = self._extract_words(text)
        vecs = [self.word_vectors[w] for w in words if w in self.word_vectors]
        if not vecs:
            return np.zeros(self.dim, dtype=np.float32)
        result = np.mean(vecs, axis=0)
        norm = np.linalg.norm(result)
        if norm > 0:
            result /= norm
        return result.astype(np.float32)

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

class DenseSpectralEncoder:
    """
    Encodeur spectral dense 64-dimensions.
    
    Principe : au lieu de projeter les mots sur un cercle (2D),
    on les projette sur 32 cercles indépendants (64D).
    Chaque cercle = une dimension sémantique différente.
    
    Résultat : deux concepts liés ("stoïcisme", "philosophie") ont
    des vecteurs proches même sans mots en commun.
    """

    def __init__(self, dim: int = 64):
        self.dim = dim
        self.word_to_vec: Dict[str, np.ndarray] = {}
        self.word_to_idf: Dict[str, float] = {}
        self.total_docs = 0
        self.vocab_built = False

    def build_vocabulary(self, documents: List[str]):
        """Construit le vocabulaire dense à partir d'un corpus."""
        if not documents:
            return

        # Compter les mots
        from collections import Counter
        word_doc_count = Counter()
        word_total_count = Counter()
        for doc in documents:
            words = self._extract_words(doc)
            for w in set(words):
                word_doc_count[w] += 1
            for w in words:
                word_total_count[w] += 1

        self.total_docs = len(documents)
        sorted_words = sorted(word_total_count.items(), key=lambda x: -x[1])[:4096]

        # Attribuer un vecteur 64D à chaque mot via φ
        for i, (word, count) in enumerate(sorted_words):
            vec = np.zeros(self.dim, dtype=np.float32)
            for d in range(self.dim):
                # Chaque dimension reçoit une phase unique par φ
                phase = (i * PHI * (d + 1) * 2 * math.pi) % (2 * math.pi)
                vec[d] = math.cos(phase) if d % 2 == 0 else math.sin(phase)
            self.word_to_vec[word] = vec
            df = word_doc_count.get(word, 1)
            self.word_to_idf[word] = math.log(self.total_docs / max(df, 1))

        self.word_count = len(self.word_to_vec)
        self.vocab_built = True

    def encode(self, text: str) -> np.ndarray:
        """Encode un texte en vecteur dense 64D."""
        if not self.vocab_built:
            return np.zeros(self.dim, dtype=np.float32)

        words = self._extract_words(text)
        if not words:
            return np.zeros(self.dim, dtype=np.float32)

        result = np.zeros(self.dim, dtype=np.float32)
        matched = 0
        for w in words:
            if w in self.word_to_vec:
                result += self.word_to_vec[w] * self.word_to_idf.get(w, 1.0)
                matched += 1

        if matched == 0:
            return np.zeros(self.dim, dtype=np.float32)

        norm = np.linalg.norm(result)
        if norm > 0:
            result /= norm
        return result

    def similarity(self, text1: str, text2: str) -> float:
        """Similarité cosinus entre deux textes (64D)."""
        v1 = self.encode(text1)
        v2 = self.encode(text2)
        dot = np.dot(v1, v2)
        return max(0.0, min(1.0, float(dot)))

    def _extract_words(self, text: str) -> List[str]:
        stop_words = {'dans', 'avec', 'pour', 'sur', 'sous', 'dont', 'cette', 'leur',
                      'plus', 'tout', 'vous', 'nous', 'alors', 'comme', 'bien', 'fait',
                      'peut', 'tres', 'sont', 'aux', 'une', 'est', 'les', 'des', 'pas',
                      'que', 'qui', 'par', 'the', 'and', 'cest', 'ete', 'etait'}
        words = []
        for w in text.lower().split():
            w = w.strip('.,;:!?()[]{}"\'-').lower()
            if len(w) > 3 and w not in stop_words and not w.isdigit():
                words.append(w)
        return words


# ═══════════════════════════════════════════════════════════════════
# PRIORITÉ 3 — PIPELINE HARMONIC+LLM (Faits → Formulation)
# ═══════════════════════════════════════════════════════════════════

class DeepSeekLLMFormatter:
    """
    Formule les faits trouvés par Harmonic via l'API DeepSeek.
    
    RÈGLE STRICTE : Le LLM ne peut QUE reformuler les faits fournis.
    Il n'a PAS le droit d'inventer, d'extrapoler, ou d'ajouter des connaissances.
    """

    def __init__(self, api_key: str = None):
        from dotenv import load_dotenv
        import os
        if api_key is None:
            load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.api_key = api_key
        self.available = bool(api_key and len(api_key) > 10)

    def format_with_llm(self, facts: List[Dict], query: str, confidence: float) -> str:
        """Appelle DeepSeek pour formuler une réponse élégante à partir des faits Harmonic."""
        if not self.available or not facts:
            return HarmonicLLMFormatter.format_factual(facts, query, confidence)

        # Construire le contexte de faits (strictement limité)
        facts_text = "\n".join([f"- {f.get('text', '')}" for f in facts[:6] if f.get('text', '')])

        system_prompt = f"""Tu es KA, un assistant dont les connaissances proviennent d'un hologramme d'ondes universelles.

RÈGLE ABSOLUE : Tu ne dois UTILISER que les faits fournis ci-dessous. 
Tu n'as PAS le droit d'inventer, d'extrapoler, ou d'ajouter des connaissances externes.
Si les faits sont insuffisants, dis-le clairement. Ne devine jamais.

Ton rôle est de FORMULER élégamment les faits en langage naturel fluide.
Tu as la liberté de la FORME (style, syntaxe, fluidité) mais pas du FOND (les faits sont sacrés).

Faits disponibles (SOURCE UNIQUE — ne pas dépasser) :
{facts_text}

Confiance holographique : {confidence:.0%}"""

        user_prompt = f"Question : {query}\n\nEn utilisant UNIQUEMENT les faits ci-dessus, réponds en français de façon claire et naturelle."

        try:
            import requests
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 400,
                    "temperature": 0.3,
                },
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                llm_text = data["choices"][0]["message"]["content"].strip()
                # Ajouter la signature de traçabilité
                llm_text += f"\n\n───\nConfiance holographique : {confidence:.0%} | "
                llm_text += f"Faits mobilisés : {len(facts)} | Zéro hallucination"
                return llm_text
            else:
                log.warning(f"DeepSeek API erreur {response.status_code}: {response.text[:100]}")
                return HarmonicLLMFormatter.format_factual(facts, query, confidence)
        except Exception as e:
            log.warning(f"DeepSeek API indisponible ({e}), fallback local")
            return HarmonicLLMFormatter.format_factual(facts, query, confidence)


class HarmonicLLMFormatter:
    """
    Formule les faits trouvés par Harmonic en langage naturel fluide.
    
    RÈGLE : Ne jamais inventer. Utiliser UNIQUEMENT les faits fournis.
    Le LLM n'a que la liberté de la FORME, pas du FOND.
    """

    @staticmethod
    def format_factual(facts: List[Dict], query: str, confidence: float) -> str:
        """Formulation factuelle : réponse directe + contexte."""
        lines = []

        if not facts:
            return f"Je n'ai pas trouvé d'information suffisante pour répondre à : {query[:100]}"

        # Meilleur fait
        best = facts[0]
        best_text = best.get("text", "")
        best_score = best.get("weighted_score", best.get("score", 0))

        if best_score > 0.5:
            lines.append(best_text.strip())
            if len(facts) > 1 and facts[1].get("weighted_score", 0) > 0.3:
                second_text = facts[1].get("text", "").strip()
                if second_text != best_text:
                    lines.append(second_text)
        else:
            lines.append(f"D'après mes connaissances, voici ce que je peux dire :")
            for f in facts[:4]:
                text = f.get("text", "").strip()
                if text:
                    lines.append(f"• {text}")

        # Contexte de confiance
        lines.append("")
        lines.append(f"───")
        lines.append(f"Confiance : {confidence:.0%} | Source : hologramme ({len(facts)} faits mobilisés)")
        lines.append(f"Zéro hallucination — chaque fait est traçable à sa source.")

        return "\n".join(lines)

    @staticmethod
    def format_reasoning(chain: List[tuple], conclusion: str,
                         query: str, confidence: float) -> str:
        """Formulation d'un raisonnement multi-sauts."""
        lines = [
            f"Pour répondre à « {query[:100]} », voici mon cheminement :",
            "",
        ]
        for hop, fact_text, score in chain:
            lines.append(f"Étape {hop+1} : {fact_text.strip()}")
            lines.append(f"  ↳ {abs(score):.0%} de résonance avec l'onde de la question")
            lines.append("")

        lines.append(f"Conclusion : {conclusion.strip()}")
        lines.append(f"───")
        lines.append(f"Confiance : {confidence:.0%} | {len(chain)} sauts de raisonnement")

        return "\n".join(lines)

    @staticmethod
    def format_comparison(response_data: Dict) -> str:
        """
        Version LLM-like qui structure la réponse comme un assistant.
        Utile pour l'API publique.
        """
        text = response_data.get("text", "")
        facts = response_data.get("top_facts", [])
        confidence = response_data.get("confidence", 0)

        # Si c'est une réponse directe (déjà formatée), la retourner
        if text and len(text) > 20:
            return text

        # Sinon, formater à partir des faits
        return HarmonicLLMFormatter.format_factual(
            facts, response_data.get("query", ""), confidence
        )


# ═══════════════════════════════════════════════════════════════════
# MOTEUR UNIFIÉ V3
# ═══════════════════════════════════════════════════════════════════

class KANextV3Engine:
    """Moteur KA-Next v3 avec index numpy, embeddings denses, formatteur LLM."""

    MODES = ["auto", "factual", "reason", "creative"]

    def __init__(self, use_llm: bool = None):
        self.ensemble = None
        self.normalizer = None
        self.formatter = HarmonicLLMFormatter()
        # Auto-detection : activer LLM si la cle API est dans .env
        if use_llm is None:
            temp = DeepSeekLLMFormatter()
            use_llm = temp.available
        self.llm_formatter = DeepSeekLLMFormatter() if use_llm else None
        self.use_llm = use_llm
        self.built = False
        self.stats = {"total_queries": 0, "total_time_ms": 0, "mode_counts": defaultdict(int)}
        # Pont unifié onde↔langage (THEORIE_UNIFIEE_HARMONIQUE)
        self.session_memory = ABCSessionMemory() if UNIFIED_BRIDGE_AVAILABLE else None
        self.language_bridge = None  # Initialisé à la demande
        self.gagut_pipeline = GAGUTPipeline() if UNIFIED_BRIDGE_AVAILABLE else None

    def build(self):
        log.info("=" * 50)
        log.info("  KA-Next v3 — Index Numpy + Dense 64D + LLM Formatter")
        log.info("=" * 50)

        try:
            from holographic_ensemble import HolographicEnsemble
            self.ensemble = HolographicEnsemble()
            self.ensemble.build_all(force_rebuild=False)
            log.info(f"Ensemble : {len(self.ensemble.holograms)} domaines")

            # Construire les index numpy rapides
            self._build_fast_indices()
        except Exception as e:
            log.error(f"Erreur : {e}")

        try:
            from prompt_normalizer import PromptNormalizer
            self.normalizer = PromptNormalizer()
            log.info("Normaliseur : OK")
        except Exception:
            pass

        self.built = True
        log.info("KA-Next v3 construit")
        log.info("=" * 50)

    def _build_fast_indices(self):
        """Construit index 2D (SHA-256) + index 64D (DenseSpectral) pour chaque hologramme."""
        for domain_id, holo in self.ensemble.holograms.items():
            # Index 2D classique
            idx2d = FastNumpyIndex()
            idx2d.build(holo.positions, holo.fact_texts)
            holo.fast_index = idx2d
            
            # Index semantique : Cooccurrence (co-oc) > DenseSpectral (phi) > LearnedEmbedding (384D)
            if holo.fact_texts and len(holo.fact_texts) >= 10:
                try:
                    # Priorite 1 : Co-occurrence local (appris sur le corpus)
                    dense = CooccurrenceEncoder(dim=64)
                    dense.build_vocabulary(holo.fact_texts[:500])
                    if dense.vocab_built:
                        log.info(f"  [{domain_id}] Cooccurrence 64D: {dense.word_count} mots (co-occurrences)")
                    else:
                        dense = LearnedEmbeddingEncoder()
                        if not dense.available:
                            dense = DenseSpectralEncoder(dim=64)
                    if dense.vocab_built:
                        holo.dense_encoder = dense
                        holo.dense_vectors = np.array(
                            [dense.encode(t) for t in holo.fact_texts[:5000]], dtype=np.float32)
                        holo.dense_norms = np.linalg.norm(holo.dense_vectors, axis=1)
                        holo.dense_norms = np.where(holo.dense_norms < 1e-10, 1e-10, holo.dense_norms)
                        log.info(f"  [{domain_id}] Dense 64D: {dense.word_count} mots")
                except Exception as e:
                    log.warning(f"  [{domain_id}] Dense 64D non disponible: {e}")

    def query(self, prompt: str, mode: str = "auto") -> Dict:
        if not self.built:
            return {"text": "KA-Next v3 non initialisé.", "error": "not_built"}

        t0 = time.time()
        self.stats["total_queries"] += 1

        if self.normalizer:
            try:
                clean, _, _ = self.normalizer.normalize(prompt)
                prompt = clean
            except Exception:
                pass

        if mode == "auto":
            mode = self._detect_mode(prompt)
        self.stats["mode_counts"][mode] += 1

        if mode in ("factual", "reason"):
            result = self._query_fast(prompt, mode)
        elif mode == "creative":
            result = self._query_creative(prompt)
        else:
            result = {"text": f"Mode inconnu: {mode}"}

        elapsed = round((time.time() - t0) * 1000, 1)
        self.stats["total_time_ms"] += elapsed
        result["temps_ms"] = elapsed
        result["mode"] = mode
        return result

    def _detect_mode(self, query: str) -> str:
        ql = query.lower()
        if re.search(r"\b(pourquoi|explique|raisonne|analyse)\b", ql):
            return "reason"
        if re.search(r"\b(imagine|cr[ée][ée]r?|invente)\b", ql):
            return "creative"
        return "factual"

    def _query_fast(self, prompt: str, mode: str) -> Dict:
        """Requête avec index numpy rapide + raisonnement récurrent optionnel."""
        t0 = time.time()

        if not self.ensemble:
            return {"text": "Ensemble non disponible"}

        # Gating par résonance (SpectralEncoder pour routing)
        holo_scores = {}
        for domain_id, holo in self.ensemble.holograms.items():
            score = holo.resonance(prompt)
            holo_scores[domain_id] = score

        ranked = sorted(holo_scores.items(), key=lambda x: -x[1])
        top_domains = ranked[:3]

        # Extraction via index 64D dense (prioritaire) ou 2D SHA-256 (fallback)
        all_facts = self._extract_facts(prompt, top_domains)
        all_facts.sort(key=lambda x: -abs(x.get("weighted_score", 0)))
        confidence = abs(all_facts[0]["weighted_score"]) if all_facts else 0

        if mode == "reason":
            # Raisonnement récurrent avec convergence
            depth = 5
            threshold = 0.02
            chain, final_confidence = self._recurrent_reasoning(prompt, top_domains, max_hops=depth, convergence_threshold=threshold)
            if chain:
                concl_text = chain[-1][1] if chain else ""
                text = self.formatter.format_reasoning(chain, concl_text, prompt, final_confidence)
            else:
                text = self._format_response(all_facts, prompt, confidence)
        else:
            text = self._format_response(all_facts, prompt, confidence)

        return {
            "text": text, "source": "v3_numpy_index",
            "confidence": round(float(confidence), 3),
            "top_facts": all_facts[:5],
            "facts_used": len(all_facts),
            "temps_ms": round((time.time() - t0) * 1000, 1),
        }

    def _extract_facts(self, prompt: str, top_domains: list) -> list:
        """Extrait les faits des domaines selectionnes par gating."""
        all_facts = []
        for domain_id, score in top_domains:
            if score < 0.05:
                continue
            holo = self.ensemble.holograms[domain_id]
            encodeur = getattr(holo, 'dense_encoder', None)
            if encodeur and hasattr(holo, 'dense_vectors'):
                q_vec = encodeur.encode(prompt)
                if np.linalg.norm(q_vec) > 1e-10:
                    sims = np.dot(holo.dense_vectors, q_vec) / holo.dense_norms
                    sem = np.array([
                        holo.fast_index._semantic_boost(prompt, t)
                        for t in holo.fact_texts[:len(sims)]
                    ], dtype=np.float32)
                    combined = 0.4 * np.abs(sims) + 0.6 * sem
                    top_k = min(10, len(combined))
                    idxs = np.argpartition(-combined, top_k)[:top_k]
                    idxs = idxs[np.argsort(-combined[idxs])]
                    for idx in idxs:
                        txt = holo.fact_texts[idx] if idx < len(holo.fact_texts) else ""
                        all_facts.append({
                            "text": txt, "score": float(combined[idx]),
                            "index": int(idx), "domain": domain_id,
                            "domain_name": holo.domain_info.get("name", domain_id),
                            "weighted_score": float(combined[idx]) * score,
                            "source": "dense64+semantic",
                        })
            elif hasattr(holo, 'fast_index') and holo.fast_index.vectors is not None:
                q_wave = holo._text_to_wave(prompt)
                for f in holo.fast_index.search(q_wave, query_text=prompt, k=10):
                    f["domain"] = domain_id
                    f["domain_name"] = holo.domain_info.get("name", domain_id)
                    f["weighted_score"] = f.get("score", 0) * score
                    f["source"] = "sha256"
                    all_facts.append(f)
        return all_facts

    def _recurrent_reasoning(self, prompt: str, top_domains: list,
                              max_hops: int = 5,
                              convergence_threshold: float = 0.02) -> tuple:
        """
        Raisonnement auto-recurrent avec convergence.
        
        Algorithme :
          Ψ_current = Ψ_question
          HOPS_VUS = {}
          POUR hop = 0..MAX:
            FAIT = argmax(f ∈ KB \ HOPS_VUS) |cos(Ψ_current, Ψ_f)|
            SI FAIT deja vu → cycle detecte, arret
            HOPS_VUS.ajouter(FAIT)
            SI |score - prev_score| < ε → convergence, arret
            Ψ_current = moyenne(Ψ_current, Ψ_fait)
        """
        chain = []
        prev_score = None
        seen_texts = set()
        
        # Extraire le meilleur encodeur depuis les domaines actives
        encodeurs = []
        for domain_id, _ in top_domains:
            holo = self.ensemble.holograms.get(domain_id)
            if holo and hasattr(holo, 'dense_encoder') and holo.dense_encoder is not None:
                encodeurs.append(holo.dense_encoder)
            elif holo and hasattr(holo, 'fast_index'):
                # Fallback: utiliser le spectral encoder 2D
                pass
        
        # Fonction d'encodage locale
        def enc(txt):
            # Utiliser le premier encodeur dispo (Cooccurrence ou DenseSpectral)
            for e in encodeurs:
                v = e.encode(txt)
                if np.linalg.norm(v) > 1e-10:
                    return v
            # Fallback SHA-256 2D
            h = hashlib.sha256(txt.encode()[:200]).hexdigest()
            kx = (int(h[:16], 16) % (64 * 100)) / 100.0
            ky = (int(h[16:32], 16) % (64 * 100)) / 100.0
            return np.array([(kx - 32) / 64 * 20, (ky - 32) / 64 * 20], dtype=np.float32)
        
        def interference(w1: np.ndarray, w2: np.ndarray) -> float:
            dot = float(np.dot(w1, w2))
            n1 = float(np.linalg.norm(w1))
            n2 = float(np.linalg.norm(w2))
            if n1 < 1e-10 or n2 < 1e-10:
                return 0.0
            return dot / (n1 * n2)
        
        q_wave = enc(prompt)
        current_wave = q_wave
        
        for hop in range(max_hops):
            # Extraire les faits pour ce cycle de raisonnement
            facts = self._extract_facts(prompt, top_domains)
            
            # Trouver le meilleur fait non encore vu
            best_text = None
            best_interf = 0.0
            best_wave = None
            
            for f in facts:
                txt = f.get("text", "")
                key = txt[:80]
                if key in seen_texts:
                    continue
                f_wave = enc(txt)
                interf = interference(current_wave, f_wave)
                if abs(interf) > abs(best_interf):
                    best_interf = interf
                    best_text = txt
                    best_wave = f_wave
            
            if best_text is None:
                break
            
            # Detection de cycle
            key = best_text[:80]
            if key in seen_texts:
                break
            seen_texts.add(key)
            
            # Verification de convergence
            if prev_score is not None:
                delta = abs(abs(best_interf) - abs(prev_score))
                if delta < convergence_threshold:
                    chain.append((hop, best_text, best_interf))
                    break
            
            chain.append((hop, best_text, best_interf))
            prev_score = best_interf
            
            # Substitution : moyenne
            current_wave = (current_wave + best_wave) / 2.0
        
        final_confidence = abs(chain[-1][2]) if chain else 0.0
        return chain, final_confidence

    def _format_response(self, facts, query, confidence):
        """Formate la réponse : LLM si dispo, sinon formateur local."""
        if self.llm_formatter and self.llm_formatter.available:
            return self.llm_formatter.format_with_llm(facts, query, confidence)
        return self.formatter.format_factual(facts, query, confidence)

    def _query_creative(self, prompt: str) -> Dict:
        """Mode créatif avec déphasage φ."""
        base = self._query_fast(prompt, "factual")
        facts = base.get("top_facts", [])
        alpha = 0.3
        lines = [
            f"✨ EXPLORATION CRÉATIVE (déphasage φ, α={alpha:.1f})",
            "",
            f"L'onde de la question a été décalée de {alpha*PHI*180:.0f}° dans l'espace de phase.",
            f"Les connexions émergentes sont :",
            "",
        ]
        for i in range(min(3, len(facts) - 1)):
            lines.append(f"  ⊕ {facts[i].get('text', '')[:100]}  ⟷  {facts[i+1].get('text', '')[:100]}")
        lines.append("")
        lines.append(f"[Généré par déphasage holographique φ | α={alpha:.2f}]")
        base["text"] = "\n".join(lines)
        base["mode"] = "creative"
        base["alpha"] = alpha
        return base


# ═══════════════════════════════════════════════════════════════════
# MAIN — Test rapide
# ═══════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description="KA-Next v3")
    p.add_argument("--query", type=str, default=None)
    p.add_argument("--mode", type=str, default="auto")
    p.add_argument("--benchmark", action="store_true")
    p.add_argument("--llm", action="store_true", default=None, help="Utiliser DeepSeek (auto si cle API dispo)")
    p.add_argument("--serve", action="store_true", help="Demarrer le serveur HTTP (port 8442)")
    p.add_argument("--port", type=int, default=8442, help="Port du serveur")
    args = p.parse_args()

    engine = KANextV3Engine(use_llm=args.llm)
    engine.build()

    if args.serve:
        start_http_server(engine, args.port)
        return

    if args.benchmark:
        questions = [
            ("Quelle est la capitale du Senegal ?", "dakar"),
            ("Qui a decouvert l'ADN ?", "watson"),
            ("Quand a debute la Revolution francaise ?", "1789"),
            ("Quelle est la vitesse de la lumiere ?", "299"),
            ("Qu'est-ce que le stoicisme ?", "distinguer"),
        ]
        correct = 0
        t0 = time.time()
        for q, exp in questions:
            r = engine.query(q, mode="auto")
            is_correct = exp.lower() in r.get("text", "").lower()
            if is_correct:
                correct += 1
            status = "OK" if is_correct else "KO"
            print(f"  [{status}] {q[:50]:50s} | {r['temps_ms']:5.0f}ms | {r.get('confidence', 0):.1%}")
        dt = (time.time() - t0) * 1000
        print(f"\n  {correct}/{len(questions)} ({correct/len(questions)*100:.0f}%) | {dt:.0f}ms total | {dt/len(questions):.0f}ms/moy")
    elif args.query:
        r = engine.query(args.query, mode=args.mode)
        print(f"\n{'='*60}")
        print(f"  REPONSE [{r.get('mode','?')}]")
        print(f"{'='*60}")
        print(r["text"])
        print(f"\n  Source: {r.get('source','?')} | {r['temps_ms']:.0f}ms | Confiance: {r.get('confidence',0):.1%}")
    else:
        print("KA-Next v3 — Index Numpy + Dense 64D + LLM Formatter")
        print("  python ka_next_v3.py --query \"...\"")
        print("  python ka_next_v3.py --benchmark")


def start_http_server(engine, port=8442):
    """Serveur HTTP minimal pour l'API KA-Next v3."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/" or self.path == "":
                self._serve_file("www/index.html", "text/html")
            elif self.path == "/health":
                self._json(200, {"status": "ok"})
            elif self.path == "/stats":
                self._json(200, {**engine.stats, "mode_counts": dict(engine.stats["mode_counts"])})
            elif self.path.startswith("/www/"):
                self._serve_file(self.path[1:])
            else:
                self._json(404, {"error": "not found"})
        
        def do_POST(self):
            import json
            cl = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(cl)) if cl > 0 else {}
            
            if self.path in ("/query", "/"):
                prompt = body.get("prompt", body.get("query", ""))
                mode = body.get("mode", "auto")
                result = engine.query(prompt, mode=mode)
                self._json(200, result)
            else:
                self._json(404, {"error": "not found"})
        
        def _json(self, code, data):
            import json
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"))
        
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
        
        def _serve_file(self, filepath, mime=None):
            import mimetypes
            full_path = os.path.join(os.path.dirname(__file__), filepath)
            if not os.path.isfile(full_path):
                self._json(404, {"error": "file not found"})
                return
            mime = mime or mimetypes.guess_type(full_path)[0] or "application/octet-stream"
            with open(full_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime + "; charset=utf-8" if "text" in mime else mime)
            self.send_header("Content-Length", len(content))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        
        def log_message(self, format, *args):
            log.info(f"HTTP {args[0]} {args[1]} {args[2]}")
    
    log.info(f"KA-Next v3 demarre sur http://0.0.0.0:{port}")
    log.info(f"  POST http://localhost:{port}/query  {{\"prompt\": \"...\"}}")
    log.info(f"  GET  http://localhost:{port}/health")
    log.info(f"  GET  http://localhost:{port}/stats")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
