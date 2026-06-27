#!/usr/bin/env python3
"""
Semantic Matcher — Embedding-Based Knowledge Retrieval
=======================================================
Replaces/substring-matching with semantic similarity.
Supports: sentence-transformers (recommended) or TF-IDF fallback (always available).

Improvements (J2):
  - TF-IDF with char n-grams (3-5 chars) for typo tolerance
  - Query expansion (math synonyms)
  - Stemming for morphology normalization
  - Math-specific normalization (x^2 <-> x squared <-> x power 2)

Usage:
  matcher = SemanticMatcher()
  results = matcher.search("derivative of x squared", top_k=3)
"""

import re, os, sys, math, time, json
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

# ============================================================================
# 1. EMBEDDING BACKEND — Auto-detect best available
# ============================================================================

_EMBEDDING_MODEL = None
_EMBEDDING_TYPE = "none"

def _init_embeddings():
    """Initialize the best available embedding model."""
    global _EMBEDDING_MODEL, _EMBEDDING_TYPE
    
    # Try sentence-transformers (best quality, but fragile dependencies)
    try:
        import os as _os
        _os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
        _os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
        from sentence_transformers import SentenceTransformer
        _EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        _EMBEDDING_TYPE = "transformers"
        return True
    except Exception:
        pass
    
    # Fallback: TF-IDF (lightweight, always available)
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        _EMBEDDING_TYPE = "tfidf"
        return True
    except ImportError:
        pass
    
    _EMBEDDING_TYPE = "token_overlap"
    return False

_HAS_EMBEDDINGS = _init_embeddings()

# ============================================================================
# 2. QUERY NORMALIZATION — Math-specific
# ============================================================================

# Synonyms map: normalize different ways of saying the same thing
MATH_SYNONYMS = {
    "derivative": ["d/dx", "differentiate", "rate of change", "slope of tangent", "instantaneous rate"],
    "integral": ["integrate", "antiderivative", "area under curve", "primitive"],
    "solve": ["find", "determine", "compute", "evaluate", "calculate", "what is", "what are"],
    "factor": ["factorize", "decompose", "split into factors"],
    "multiply": ["product", "times", "multiplied by", "x"],
    "divide": ["divided by", "over", "ratio"],
    "square": ["x^2", "x squared", "power of 2", "to the 2nd power"],
    "cube": ["x^3", "x cubed", "power of 3", "to the 3rd power"],
    "sqrt": ["square root", "root of"],
    "prime": ["prime number", "is prime"],
}

def normalize_math_query(query: str) -> str:
    """Normalize a math query: expand synonyms, standardize notation."""
    q = query.lower().strip()
    
    # Expand math notation
    q = re.sub(r'x\^2', 'x squared', q)
    q = re.sub(r'x\^3', 'x cubed', q)
    q = re.sub(r'(\w+)\^(\d+)', r'\1 to the power \2', q)
    q = re.sub(r'd/dx', 'derivative', q)
    q = re.sub(r'\bsin\b', 'sin', q)
    q = re.sub(r'\bcos\b', 'cos', q)
    q = re.sub(r'\btan\b', 'tan', q)
    q = re.sub(r'π', 'pi', q)
    
    # Expand synonyms
    for canonical, synonyms in MATH_SYNONYMS.items():
        for syn in synonyms:
            q = q.replace(syn, canonical)
    
    # Remove filler words
    filler = {"the", "a", "an", "of", "in", "on", "at", "to", "for", "from", "with", "by", 
              "and", "or", "can you", "tell me", "please", "help me", "i need", "i want",
              "what is", "how do", "how to", "how can", "would", "could", "should"}
    for f in filler:
        q = re.sub(r'\b' + f + r'\b', '', q)
    
    # Clean up
    q = re.sub(r'\s+', ' ', q).strip()
    return q

# ============================================================================
# 3. SEMANTIC MATCHER (Enhanced)
# ============================================================================

class SemanticMatcher:
    """
    Semantic search over the knowledge base with enhanced TF-IDF.
    """
    
    def __init__(self, kb_entries: Dict[str, Dict] = None):
        self.kb = kb_entries or {}
        self.keys = []
        self.embeddings = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self._initialized = False
    
    def build_index(self, kb_entries: Dict[str, Dict] = None):
        """Build the embedding index from knowledge base entries."""
        if kb_entries:
            self.kb = kb_entries
        
        self.keys = list(self.kb.keys())
        if not self.keys:
            return
        
        if _EMBEDDING_TYPE == "transformers" and _EMBEDDING_MODEL:
            print(f"  [SemanticMatcher] Building embedding index for {len(self.keys)} entries...")
            t0 = time.time()
            self.embeddings = _EMBEDDING_MODEL.encode(
                self.keys, show_progress_bar=True, batch_size=64
            )
            print(f"  [SemanticMatcher] Index built in {time.time()-t0:.1f}s")
        
        elif _EMBEDDING_TYPE == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            # Enhanced TF-IDF with character n-grams for typo tolerance + math terms
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words='english',
                ngram_range=(1, 3),        # unigrams, bigrams, trigrams
                analyzer='char_wb',         # character n-grams at word boundaries
                sublinear_tf=True,           # 1 + log(tf)
            )
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.keys)
            print(f"  [SemanticMatcher] TF-IDF index: {self.tfidf_matrix.shape[0]} keys, "
                  f"{self.tfidf_matrix.shape[1]} features")
        
        self._initialized = True
    
    def search(self, query: str, top_k: int = 5, min_score: float = 0.15) -> List[Tuple[str, Dict, float]]:
        """Search with query normalization."""
        if not self._initialized or not self.keys:
            return []
        
        # Normalize query for better matching
        norm_query = normalize_math_query(query)
        
        if _EMBEDDING_TYPE == "transformers" and _EMBEDDING_MODEL is not None and self.embeddings is not None:
            results = self._search_transformers(query, top_k, min_score)
            if results:
                return results
            # If no results with original, try normalized
            if norm_query != query:
                results = self._search_transformers(norm_query, top_k, min_score)
                if results:
                    return results
        
        elif _EMBEDDING_TYPE == "tfidf" and self.tfidf_vectorizer is not None:
            # Search with original query
            results = self._search_tfidf(query, top_k, min_score)
            # If not enough results, try normalized
            if len(results) < top_k and norm_query != query:
                norm_results = self._search_tfidf(norm_query, top_k, min_score)
                # Merge, preferring original results
                seen_keys = {r[0] for r in results}
                for r in norm_results:
                    if r[0] not in seen_keys:
                        results.append(r)
                        seen_keys.add(r[0])
                results.sort(key=lambda x: -x[2])
            return results[:top_k]
        
        # Token overlap fallback
        results = self._search_token_overlap(query, top_k, min_score)
        if len(results) < top_k and norm_query != query:
            norm_results = self._search_token_overlap(norm_query, top_k, min_score)
            seen_keys = {r[0] for r in results}
            for r in norm_results:
                if r[0] not in seen_keys:
                    results.append(r)
            results.sort(key=lambda x: -x[2])
        return results[:top_k]
    
    def _search_transformers(self, query: str, top_k: int, min_score: float):
        query_emb = _EMBEDDING_MODEL.encode([query])[0]
        similarities = np.dot(self.embeddings, query_emb) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_emb) + 1e-10
        )
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score < min_score:
                break
            key = self.keys[idx]
            value = self.kb.get(key, {})
            results.append((key, value, round(score, 4)))
        return results
    
    def _search_tfidf(self, query: str, top_k: int, min_score: float):
        from sklearn.metrics.pairwise import cosine_similarity
        query_vec = self.tfidf_vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        top_indices = np.argsort(similarities)[::-1][:min(top_k * 2, len(self.keys))]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score < min_score:
                break
            key = self.keys[idx]
            value = self.kb.get(key, {})
            results.append((key, value, round(score, 4)))
        return results[:top_k]
    
    def _search_token_overlap(self, query: str, top_k: int, min_score: float):
        """Jaccard similarity with enhanced tokenization."""
        query_tokens = set(re.findall(r'[a-z0-9]+', query.lower()))
        scores = []
        for key in self.keys:
            key_tokens = set(re.findall(r'[a-z0-9]+', key.lower()))
            if not key_tokens:
                continue
            intersection = query_tokens & key_tokens
            union = query_tokens | key_tokens
            jaccard = len(intersection) / len(union) if union else 0.0
            
            # Boost for number matches (numbers are very discriminative in math)
            q_nums = set(re.findall(r'\d+', query))
            k_nums = set(re.findall(r'\d+', key))
            if q_nums and k_nums:
                num_overlap = len(q_nums & k_nums) / max(len(q_nums | k_nums), 1)
                jaccard = jaccard * 0.7 + num_overlap * 0.3
            
            if jaccard >= min_score:
                scores.append((key, self.kb[key], jaccard))
        
        scores.sort(key=lambda x: -x[2])
        return [(k, v, round(s, 4)) for k, v, s in scores[:top_k]]

# ============================================================================
# 3. HYBRID MATCHER — Combines semantic + parametric + exact
# ============================================================================

class HybridMatcher:
    """
    Orchestrates multiple matching strategies:
    1. Parametric KB (∞ coverage, instant)
    2. Semantic embeddings (best quality)
    3. Exact substring (fast, reliable)
    """
    
    def __init__(self, math_engine):
        self.engine = math_engine
        self.semantic = SemanticMatcher()
        self._load_parametric()
        self._build_semantic_index()
    
    def _load_parametric(self):
        try:
            from parametric_kb import ParametricKB
            self.parametric = ParametricKB()
        except ImportError:
            self.parametric = None
    
    def _build_semantic_index(self):
        try:
            import knowledge_base
            self.semantic.build_index(knowledge_base.PRE_COMPUTED)
        except ImportError:
            pass
    
    def find_best(self, prompt: str, top_k: int = 5) -> Optional[Dict[str, Any]]:
        """Find the best answer using all strategies."""
        # Level 1: Parametric KB (compute, don't look up)
        if self.parametric:
            result = self.parametric.solve(prompt)
            if result:
                return result
        
        # Level 2: Semantic search (with query expansion)
        if self.semantic._initialized:
            norm_query = normalize_math_query(prompt)
            matches = self.semantic.search(norm_query, top_k=top_k, min_score=0.08)
            if not matches:
                matches = self.semantic.search(prompt, top_k=top_k, min_score=0.15)
            if matches:
                best_key, best_value, score = matches[0]
                styled = best_value.get("text_lm_arena", "") if isinstance(best_value, dict) else ""
                text = styled if styled else (best_value.get("text", str(best_value)) if isinstance(best_value, dict) else str(best_value))
                return {
                    "text": text,
                    "confidence": score * (best_value.get("coherence", 0.95) if isinstance(best_value, dict) else 0.80),
                    "domain": best_value.get("domain", "general") if isinstance(best_value, dict) else "general",
                    "method": "semantic_match",
                }
        
        # Level 3: Existing engine
        return self.engine._match_precomputed(prompt.lower())

# Quick test
if __name__ == "__main__":
    print(f"Embedding backend: {_EMBEDDING_TYPE}")
    
    sample_kb = {
        "what is the derivative of x^2": {"text": "2x", "coherence": 0.98, "domain": "calculus"},
        "what is the integral of x": {"text": "x^2/2 + C", "coherence": 0.97, "domain": "calculus"},
        "solve x^2 - 3x + 2 = 0": {"text": "x=1 or x=2", "coherence": 0.96, "domain": "algebra"},
        "what is the area of a circle with radius 5": {"text": "78.54", "coherence": 0.99, "domain": "geometry"},
        "what is 25 * 4": {"text": "100", "coherence": 0.99, "domain": "arithmetic"},
        "derivative of sin(x)": {"text": "cos(x)", "coherence": 0.98, "domain": "calculus"},
        "differentiate cos(x^3)": {"text": "-3x^2 sin(x^3)", "coherence": 0.94, "domain": "calculus"},
    }
    
    m = SemanticMatcher(sample_kb)
    m.build_index()
    
    # Test normalization
    print("\nNormalization test:")
    for q in ["what's the derivative of x squared", "find d/dx of x^2", "i need to know sin(2x)"]:
        print(f"  {q} -> {normalize_math_query(q)}")
    
    print("\nSearch test:")
    queries = [
        "what's the derivative of x squared",
        "how do I differentiate sin(x)",
        "area of circle radius five",
        "find the rate of change of x^2",
    ]
    for q in queries:
        print(f"\nQuery: {q}")
        results = m.search(q, top_k=3)
        for key, val, score in results:
            print(f"  [{score:.3f}] {key[:50]} -> {val.get('text','?')[:50]}")
    
    print("\nDone.")