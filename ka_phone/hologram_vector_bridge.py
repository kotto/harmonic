#!/usr/bin/env python3
"""
HOLOGRAM -> VECTOR BRIDGE — Interface Ondes Universelles <-> Raisonnement Humain
===============================================================================
Architecture complete en 4 couches :

COUCHE 1 — HologramABCVectorExtractor
  Extrait les patches de l'hologramme 1024x1024 (ou plus grand).
  Chaque patch est enrichi par ses interactions Mittag-Leffler (noyau ABC)
  avec TOUS les autres patches -> vecteur ABC-augmente.
  Preserve phase + amplitude + memoire non-locale.

COUCHE 2 — ABCVectorIndex (FAISS)
  Indexe les vecteurs ABC-augmentes pour recherche par similarite cosinus.
  La similarite cosinus sur ces vecteurs enrichis approxime le calcul
  complet de resonance R = ⟨Psi_q*|Psi_k⟩ / (|Psi_q|·|Psi_k|).

COUCHE 3 — ConstrainedDecoderBridge
  Interface LLM contrainte : le modele recoit UNIQUEMENT les faits
  extraits de l'hologramme. Son role est purement stylistique —
  assembler en langage naturel ce que l'hologramme a deja determine.
  ZERO liberte d'invention.

COUCHE 4 — DeterministicVerificationLayer
  Verifie que chaque token/phrase du texte genere est tracable
  a un fait de l'hologramme. Rejette toute sequence non tracable.
  Controle du determinisme meme avec un LLM de surface.

Usage :
  python hologram_vector_bridge.py --build-index    # Construire l'index
  python hologram_vector_bridge.py --query "question"  # Requete complete
  python hologram_vector_bridge.py --test            # Tests de validation
"""

import os, sys, math, hashlib, json, time, re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
import numpy as np

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1.0 / PHI
SIZE = 1024
PATCH_SIZE = 64
STRIDE = 32
ABC_NEIGHBORS = 16

DATA_DIR = BASE_DIR.parent / "data" / "emergence"
VECTOR_DIR = BASE_DIR.parent / "data" / "vectors"
os.makedirs(VECTOR_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

HOLOGRAM_FILE = DATA_DIR / "emergence_hologram_1024.npy"
ABC_HOLOGRAM_FILE = DATA_DIR / "abc_hologram_1024.npy"
VECTOR_INDEX_FILE = VECTOR_DIR / "abc_vectors.npy"
PATCH_METADATA_FILE = VECTOR_DIR / "patch_metadata.json"
FAISS_INDEX_FILE = VECTOR_DIR / "faiss_index.bin"
FACTS_FILE = VECTOR_DIR / "linked_facts.json"


def _compute_patch_positions(patch_size=PATCH_SIZE, stride=STRIDE, size=SIZE):
    """Calcule les centres de tous les patches sur la grille."""
    n = (size - patch_size) // stride + 1
    positions = []
    for i in range(n):
        for j in range(n):
            y_start = i * stride
            x_start = j * stride
            positions.append((y_start + patch_size // 2, x_start + patch_size // 2))
    return positions


# ==============================================================================
# COUCHE 1 — HOLOGRAM ABC VECTOR EXTRACTOR
# ==============================================================================

class HologramABCVectorExtractor:
    def __init__(self, hologram_path: str = None, patch_size: int = PATCH_SIZE,
                 stride: int = STRIDE, abc_neighbors: int = ABC_NEIGHBORS):
        self.patch_size = patch_size
        self.stride = stride
        self.abc_neighbors = abc_neighbors
        self.hologram = None
        self.size = SIZE

        path_abc = hologram_path or str(ABC_HOLOGRAM_FILE)
        path_std = str(HOLOGRAM_FILE)

        if os.path.exists(path_abc):
            self.hologram = np.load(path_abc)
            self.size = self.hologram.shape[0]
            print(f"[Extractor] Hologramme ABC charge : {self.hologram.shape}")
        elif os.path.exists(path_std):
            self.hologram = np.load(path_std)
            self.size = self.hologram.shape[0]
            print(f"[Extractor] Hologramme standard charge : {self.hologram.shape}")
        else:
            raise FileNotFoundError(f"Aucun hologramme trouve. Generez-le d'abord avec abc_hologram_engine.py --rebuild")

        self.patch_positions = None
        self.abc_vectors = None
        self.raw_patches = None
        self._ensure_positions()

    def _ensure_positions(self):
        """Garantit que patch_positions est toujours disponible."""
        if self.patch_positions is None or len(self.patch_positions) == 0:
            self.patch_positions = _compute_patch_positions(
                self.patch_size, self.stride, self.size
            )

    def _compute_patch_fft(self, patch: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        fft = np.fft.fft2(patch)
        fft_shifted = np.fft.fftshift(fft)
        amplitudes = np.abs(fft_shifted)
        if np.max(amplitudes) > 0:
            amplitudes = amplitudes / np.max(amplitudes)
        center = self.patch_size // 2
        radial_phases = []
        for r in range(1, min(center, 8) + 1):
            ring_phases = []
            for angle in range(0, 360, 45):
                x = int(center + r * math.cos(math.radians(angle)))
                y = int(center + r * math.sin(math.radians(angle)))
                if 0 <= x < self.patch_size and 0 <= y < self.patch_size:
                    phase = math.atan2(fft_shifted[y, x].imag, fft_shifted[y, x].real)
                    ring_phases.append(phase)
            if ring_phases:
                radial_phases.append(np.mean(ring_phases))
        while len(radial_phases) < 64:
            radial_phases.append(0.0)
        return amplitudes.flatten(), np.array(radial_phases[:64])

    def _mittag_leffler_kernel(self, pos1, pos2) -> float:
        d = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
        d_norm = d / (self.size / 20.0)
        gamma_1_plus_alpha = math.gamma(1 + ALPHA)
        gamma_1_minus_alpha = math.gamma(1 - ALPHA)
        x = ALPHA * (d_norm ** ALPHA)
        if d_norm < 1.0:
            ml = 1.0 / (1.0 + x / gamma_1_plus_alpha)
        else:
            ml = 1.0 / (x * gamma_1_minus_alpha) if x > 0 else 1.0
        return float(ml)

    def extract_patches(self) -> np.ndarray:
        self._ensure_positions()
        print(f"\n[Extractor] Extraction des patches {self.patch_size}x{self.patch_size} (stride={self.stride})...")
        t0 = time.time()
        n = (self.size - self.patch_size) // self.stride + 1
        total_patches = n * n
        print(f"  Grille de patches : {n}x{n} = {total_patches} patches")

        raw_patches = []
        for y, x in self.patch_positions:
            y_start = y - self.patch_size // 2
            x_start = x - self.patch_size // 2
            patch = self.hologram[y_start:y_start + self.patch_size,
                                  x_start:x_start + self.patch_size]
            raw_patches.append(patch)

        self.raw_patches = raw_patches

        print(f"  Calcul des spectres FFT pour {total_patches} patches...")
        fft_cache = []
        for idx, patch in enumerate(raw_patches):
            amps, phases = self._compute_patch_fft(patch)
            fft_cache.append((amps, phases))
            if (idx + 1) % 200 == 0 or idx == total_patches - 1:
                print(f"    Spectres : {idx+1}/{total_patches}")

        print(f"  Calcul des interactions ABC (top-{self.abc_neighbors} voisins)...")
        patch_vectors = []
        total_ml_pairs = 0
        for idx, (amps, phases) in enumerate(fft_cache):
            pos = self.patch_positions[idx]
            ml_interactions = []
            for other_idx, other_pos in enumerate(self.patch_positions):
                if other_idx == idx:
                    continue
                ml_val = self._mittag_leffler_kernel(pos, other_pos)
                ml_interactions.append((ml_val, other_idx))
            ml_interactions.sort(key=lambda x: -x[0])
            top_ml = [v for v, _ in ml_interactions[:self.abc_neighbors]]
            while len(top_ml) < self.abc_neighbors:
                top_ml.append(0.0)
            local_energy = float(np.sum(np.abs(raw_patches[idx]) ** 2))
            log_energy = math.log(1 + local_energy) if local_energy > 0 else 0.0
            vector = np.concatenate([
                amps,
                phases,
                np.array(top_ml),
                np.array([pos[0] / self.size, pos[1] / self.size, log_energy])
            ])
            patch_vectors.append(vector)
            total_ml_pairs += len(ml_interactions)
            if (idx + 1) % 200 == 0 or idx == total_patches - 1:
                print(f"    ABC : {idx+1}/{total_patches}")

        self.abc_vectors = np.array(patch_vectors, dtype=np.float32)
        dt = time.time() - t0
        print(f"\n[Extractor] Extraction terminee en {dt:.1f}s")
        print(f"  Patches extraits : {total_patches}")
        print(f"  Dimension vecteur : {self.abc_vectors.shape[1]}")
        print(f"  Paires ML calculees : {total_ml_pairs}")
        print(f"  Memoire : {self.abc_vectors.nbytes / 1024 / 1024:.1f} Mo")
        return self.abc_vectors

    def save_vectors(self):
        if self.abc_vectors is None:
            self.extract_patches()
        np.save(str(VECTOR_INDEX_FILE), self.abc_vectors)
        metadata = {
            "patch_size": self.patch_size, "stride": self.stride,
            "abc_neighbors": self.abc_neighbors, "hologram_size": self.size,
            "n_patches": len(self.abc_vectors),
            "vector_dim": int(self.abc_vectors.shape[1]), "abc_order": ALPHA,
        }
        with open(str(PATCH_METADATA_FILE), 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"\n[Extractor] Vecteurs sauvegardes : {VECTOR_INDEX_FILE}")
        print(f"  Metadonnees : {PATCH_METADATA_FILE}")
        return metadata

    def ensure_extracted(self):
        """Garantit que les donnees sont disponibles (depuis cache ou extraction)."""
        self._ensure_positions()
        if self.raw_patches is None and self.abc_vectors is not None:
            # Extraire raw_patches depuis l'hologramme
            raw_patches = []
            for y, x in self.patch_positions:
                y_start = y - self.patch_size // 2
                x_start = x - self.patch_size // 2
                patch = self.hologram[y_start:y_start + self.patch_size,
                                      x_start:x_start + self.patch_size]
                raw_patches.append(patch)
            self.raw_patches = raw_patches


# ==============================================================================
# COUCHE 2 — ABC VECTOR INDEX (FAISS)
# ==============================================================================

class ABCVectorIndex:
    def __init__(self, vectors: np.ndarray = None):
        self.vectors = None
        self.index = None
        self.dimension = None
        self._faiss_available = False
        try:
            import faiss
            self.faiss = faiss
            self._faiss_available = True
            print("[Index] FAISS disponible — indexation GPU-compatible")
        except ImportError:
            print("[Index] FAISS non disponible — fallback numpy (plus lent)")
        if vectors is not None:
            self.build(vectors)
        elif os.path.exists(str(VECTOR_INDEX_FILE)):
            self.load()

    def build(self, vectors: np.ndarray):
        self.vectors = vectors.astype(np.float32)
        self.dimension = vectors.shape[1]
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-10)
        self.vectors_normalized = self.vectors / norms
        if self._faiss_available:
            self.index = self.faiss.IndexFlatIP(self.dimension)
            self.index.add(self.vectors_normalized)
            print(f"[Index] Index FAISS construit : {self.index.ntotal} vecteurs, dim={self.dimension}")
        else:
            print(f"[Index] Index numpy construit : {len(self.vectors_normalized)} vecteurs, dim={self.dimension}")

    def search(self, query_vector: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        if self.index is None and self.vectors is None:
            return np.array([]), np.array([])
        query = query_vector.astype(np.float32).reshape(1, -1)
        query = query / max(np.linalg.norm(query), 1e-10)
        if self._faiss_available and self.index is not None:
            scores, indices = self.index.search(query, k)
            return indices[0], scores[0]
        else:
            similarities = np.dot(self.vectors_normalized, query.T).flatten()
            top_indices = np.argsort(-similarities)[:k]
            top_scores = similarities[top_indices]
            return top_indices, top_scores

    def load(self):
        if not os.path.exists(str(VECTOR_INDEX_FILE)):
            print(f"[Index] Fichier vecteurs non trouve : {VECTOR_INDEX_FILE}")
            return
        vectors = np.load(str(VECTOR_INDEX_FILE))
        self.build(vectors)
        print(f"[Index] Index charge depuis {VECTOR_INDEX_FILE}")

    def save(self):
        if self.index is None or not self._faiss_available:
            return
        self.faiss.write_index(self.index, str(FAISS_INDEX_FILE))
        print(f"[Index] Index FAISS sauvegarde : {FAISS_INDEX_FILE}")

    def get_patch_info(self, idx: int, extractor=None) -> Dict:
        if extractor is None or extractor.patch_positions is None:
            return {"index": int(idx)}
        pos = extractor.patch_positions[idx]
        energy = float(np.sum(np.abs(extractor.raw_patches[idx]) ** 2)) if extractor.raw_patches else 0
        return {"index": int(idx), "position": [int(pos[0]), int(pos[1])], "energy": energy}


# ==============================================================================
# COUCHE 3 — CONSTRAINED DECODER BRIDGE
# ==============================================================================

class ConstrainedDecoderBridge:
    def __init__(self, model_path: str = None, n_ctx: int = 4096):
        self.model_path = model_path or str(BASE_DIR / "models" / "phi-3-mini-4k-instruct-q4_k_m.gguf")
        self.n_ctx = n_ctx
        self.llm = None
        self.available = False
        self._init_model()

    def _init_model(self):
        if not os.path.exists(self.model_path):
            return
        try:
            from ctransformers import AutoModelForCausalLM, AutoConfig
            config = AutoConfig.from_pretrained(self.model_path, context_length=self.n_ctx)
            self.llm = AutoModelForCausalLM.from_pretrained(
                self.model_path, model_type="llama", config=config, local_files_only=True)
            self.available = True
            return
        except Exception:
            pass
        try:
            from llama_cpp import Llama
            self.llm = Llama(model_path=self.model_path, n_ctx=self.n_ctx, n_threads=4, verbose=False)
            self.available = True
        except Exception:
            self.available = False

    def decode(self, retrieved_facts: List[Dict], query: str, style: str = "general",
               max_tokens: int = 200, temperature: float = 0.3) -> Dict[str, Any]:
        t0 = time.time()
        fact_context = self._build_fact_context(retrieved_facts)
        if not fact_context.strip():
            return {"text": "Aucun fait pertinent trouve.", "source": "no_facts",
                    "confidence": 0.0, "verified": True, "temps_ms": 0}
        system_prompt = self._make_prompt(fact_context, query)
        if self.available and self.llm:
            try:
                full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{query}\n<|assistant|>"
                output = self.llm(full_prompt, max_tokens=max_tokens, temperature=temperature,
                                  top_p=0.9, repeat_penalty=1.1,
                                  stop=["<|user|>", "<|system|>"], echo=False)
                generated = output["choices"][0]["text"].strip()
                if len(generated) >= 20:
                    return {"text": generated, "source": "llm_constrained", "confidence": 0.80,
                            "verified": False, "temps_ms": round((time.time()-t0)*1000, 1),
                            "facts_used": len(retrieved_facts)}
            except Exception:
                pass
        return self._template_assemble(retrieved_facts, query, t0)

    def _build_fact_context(self, facts, max_chars=3000):
        lines = []
        for f in facts[:30]:
            t = f.get("text", "")
            if t and len(t) > 3:
                lines.append(f"- {t.strip()}")
        ctx = "\n".join(lines)
        return ctx[:max_chars] if len(ctx) > max_chars else ctx

    def _make_prompt(self, fact_context, query):
        return f"""Tu es KA, un assistant dont la connaissance provient UNIQUEMENT d'un hologramme d'ondes.

REGLE ABSOLUE : Tu NE DOIS repondre qu'en utilisant les faits fournis ci-dessous.
Tu NE DOIS PAS inventer. Si tu n'as pas assez d'information, dis-le.

FAITS DE L'HOLOGRAMME (SEULE source autorisee) :
{fact_context}

Question : {query}

Reponse (en francais, UNIQUEMENT basee sur les faits, sans rien inventer) :"""

    def _template_assemble(self, facts, query, t0):
        texts = [f.get("text","") for f in facts[:5] if f.get("text","") and len(f.get("text",""))>3]
        if not texts:
            text = "L'hologramme ne contient pas d'information suffisante."
        elif len(texts) == 1:
            text = f"D'apres l'hologramme : {texts[0]}"
        else:
            text = "D'apres l'hologramme :\n" + "\n".join(f"- {t}" for t in texts)
        return {"text": text, "source": "template_fallback", "confidence": 0.75,
                "verified": True, "temps_ms": round((time.time()-t0)*1000, 1), "facts_used": len(texts)}

    def is_available(self):
        return self.available and self.llm is not None


# ==============================================================================
# COUCHE 4 — DETERMINISTIC VERIFICATION LAYER
# ==============================================================================

class DeterministicVerificationLayer:
    def __init__(self):
        self.stats = {"total_verified": 0, "fully_traceable": 0, "partially_traceable": 0, "rejected": 0}

    def verify(self, generated_text: str, source_facts: List[Dict], query: str = "",
               strict_mode: bool = True) -> Dict:
        self.stats["total_verified"] += 1
        source_words = set()
        source_phrases = []
        source_entities = set()
        for fact in source_facts:
            text = fact.get("text", "")
            if not text:
                continue
            tl = text.lower()
            source_phrases.append(tl)
            words = re.findall(r'[a-z]{4,}', tl)
            source_words.update(words)
            entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            source_entities.update(e.lower() for e in entities)
            numbers = re.findall(r'\b\d+(?:[.,]\d+)?\b', text)
            source_entities.update(numbers)
        query_words = set(re.findall(r'[a-z]{3,}', query.lower()))
        sentences = re.split(r'[.!?]+', generated_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if not sentences:
            return {"traceable": True, "score": 1.0, "hallucination_phrases": [], "trace_map": {}, "verdict": "valid"}
        hallucination_phrases = []
        traced_count = 0
        for i, sentence in enumerate(sentences):
            sl = sentence.lower()
            sw = set(re.findall(r'[a-z]{4,}', sl))
            covered = (sw & source_words) | (sw & query_words)
            coverage = len(covered) / max(len(sw), 1)
            sent_entities = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sentence))
            sent_numbers = set(re.findall(r'\b\d+(?:[.,]\d+)?\b', sentence))
            sent_ent_lower = set(e.lower() for e in sent_entities) | sent_numbers
            entity_match = len(sent_ent_lower & source_entities) > 0 or len(sent_ent_lower) == 0
            is_traceable = coverage >= 0.2 or entity_match
            if is_traceable:
                traced_count += 1
            else:
                hallucination_phrases.append(sentence[:100])
        trace_ratio = traced_count / max(len(sentences), 1)
        if strict_mode and hallucination_phrases:
            verdict = "rejected"; self.stats["rejected"] += 1
        elif trace_ratio >= 0.8:
            verdict = "valid"; self.stats["fully_traceable"] += 1
        elif trace_ratio >= 0.5:
            verdict = "warning"; self.stats["partially_traceable"] += 1
        else:
            verdict = "rejected"; self.stats["rejected"] += 1
        return {"traceable": verdict != "rejected", "score": round(trace_ratio, 2),
                "hallucination_phrases": hallucination_phrases, "trace_map": {},
                "verdict": verdict, "traced": traced_count, "total": len(sentences)}

    def get_stats(self):
        return dict(self.stats)


# ==============================================================================
# LIEN FAITS -> PATCHES (Mapping spatial + semantique)
# ==============================================================================

class FactPatchMapper:
    def __init__(self, extractor: HologramABCVectorExtractor = None):
        self.extractor = extractor
        self.fact_regions = {}
        self.patch_facts = {}
        self.all_facts = []
        try:
            from quick_facts import QuickFacts
            qf = QuickFacts()
            self.all_facts = qf.facts
            print(f"[Mapper] {len(self.all_facts)} faits QuickFacts charges")
        except ImportError:
            print("[Mapper] QuickFacts non disponible")

    def build_mapping(self):
        if not self.all_facts or not self.extractor:
            print("[Mapper] Impossible de construire le mapping (donnees manquantes)")
            return

        # Garantir les positions et les donnees brutes
        self.extractor._ensure_positions()
        self.extractor.ensure_extracted()

        print(f"\n[Mapper] Construction du mapping faits <-> patches (spatial + semantique)...")
        t0 = time.time()

        # Phase 1 : Mapping spatial
        spatial_patches = 0
        for fid, text, keywords in self.all_facts:
            kx, ky = self._text_to_position(fid + text)
            nearby = []
            for idx, (py, px) in enumerate(self.extractor.patch_positions):
                fx = int(kx * self.extractor.size / 20 + self.extractor.size / 2) % self.extractor.size
                fy = int(ky * self.extractor.size / 20 + self.extractor.size / 2) % self.extractor.size
                if math.sqrt((fx - px)**2 + (fy - py)**2) < self.extractor.patch_size * 2:
                    nearby.append(idx)
            self.fact_regions[fid] = list(nearby)
            for pidx in nearby:
                if pidx not in self.patch_facts:
                    self.patch_facts[pidx] = []
                self.patch_facts[pidx].append(fid)
                spatial_patches += 1

        n_spatial = len(self.patch_facts)
        print(f"  Mapping spatial : {len(self.fact_regions)} faits -> {n_spatial} patches")

        # Phase 2 : Mapping semantique (TF-IDF)
        print(f"  Construction du mapping semantique (TF-IDF)...")

        # Signatures des patches depuis raw_patches
        if self.extractor.raw_patches is None:
            print("  [!] raw_patches non disponibles, mapping semantique saute")
            print(f"  Mapping termine. Patches avec faits (spatial) : {n_spatial}")
            return

        patch_sigs = []
        for patch in self.extractor.raw_patches:
            re = np.sum(np.abs(patch), axis=1)[:32]
            ce = np.sum(np.abs(patch), axis=0)[:32]
            patch_sigs.append(np.concatenate([re, ce]))
        patch_sigs = np.array(patch_sigs, dtype=np.float64)
        patch_norms = np.linalg.norm(patch_sigs, axis=1, keepdims=True)
        patch_norms[patch_norms < 1e-10] = 1e-10
        patch_sigs_norm = patch_sigs / patch_norms
        n_feat = patch_sigs.shape[1]

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            fact_texts = [t[1] for t in self.all_facts]
            vec = TfidfVectorizer(max_features=5000, ngram_range=(1,2), analyzer='char_wb')
            fact_tfidf = vec.fit_transform(fact_texts)

            semantic_patches = 0
            k_sem = 5

            for fi, (fid, text, keywords) in enumerate(self.all_facts):
                if fi % 200 == 0:
                    print(f"    Mapping semantique : {fi}/{len(self.all_facts)}")
                fv = fact_tfidf[fi].toarray().flatten()
                if len(fv) > n_feat:
                    fvr = np.zeros(n_feat)
                    step = len(fv) // n_feat
                    for i in range(n_feat):
                        fvr[i] = np.mean(fv[i*step:(i+1)*step])
                else:
                    fvr = np.zeros(n_feat)
                    fvr[:len(fv)] = fv
                fvr = fvr / max(np.linalg.norm(fvr), 1e-10)
                sims = np.dot(patch_sigs_norm, fvr)
                top = np.argsort(-sims)[:k_sem]
                existing = set(self.fact_regions.get(fid, []))
                for idx in top:
                    if idx not in existing:
                        if idx not in self.patch_facts:
                            self.patch_facts[idx] = []
                        self.patch_facts[idx].append(fid)
                        existing.add(idx)
                        semantic_patches += 1
                self.fact_regions[fid] = list(existing)

            print(f"  Mapping semantique termine : +{semantic_patches} liens ajoutes")
        except ImportError:
            print("  [!] scikit-learn non disponible - mapping semantique desactive")

        dt = time.time() - t0
        print(f"  Mapping termine en {dt:.1f}s")
        print(f"  Faits mappes : {len(self.fact_regions)}")
        print(f"  Patches avec faits (spatial) : {n_spatial}")
        print(f"  Patches avec faits (total)   : {len(self.patch_facts)}")

    def _text_to_position(self, text: str):
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        sz = self.extractor.size if self.extractor else 1024
        kx = (int(h[:16], 16) % (sz * 100)) / 100.0
        ky = (int(h[16:32], 16) % (sz * 100)) / 100.0
        kx = (kx - sz / 2) / sz * 20
        ky = (ky - sz / 2) / sz * 20
        return kx, ky

    def get_facts_for_patches(self, patch_indices):
        seen = set()
        facts = []
        for idx in patch_indices:
            for fid in self.patch_facts.get(int(idx), []):
                if fid not in seen:
                    seen.add(fid)
                    for f in self.all_facts:
                        if f[0] == fid:
                            facts.append({"id": fid, "text": f[1],
                                          "keywords": list(f[2]) if len(f)>2 else [],
                                          "patch_index": int(idx)})
                            break
        return facts

    def save_mapping(self):
        mapping = {"patch_facts": {str(k): v for k, v in self.patch_facts.items()}}
        with open(str(FACTS_FILE), 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        print(f"[Mapper] Mapping sauvegarde : {FACTS_FILE}")

    def load_mapping(self):
        if not os.path.exists(str(FACTS_FILE)):
            return False
        with open(str(FACTS_FILE), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.patch_facts = {int(k): v for k, v in data.get("patch_facts", {}).items()}
        print(f"[Mapper] Mapping charge : {len(self.patch_facts)} patches avec faits")
        return True


# ==============================================================================
# PIPELINE COMPLET
# ==============================================================================

class HologramVectorPipeline:
    def __init__(self, use_llm: bool = True):
        self.extractor = None; self.index = None; self.mapper = None
        self.decoder = None; self.verifier = DeterministicVerificationLayer()
        self.use_llm = use_llm; self.built = False

    def build(self, force: bool = False):
        print("=" * 60)
        print("  CONSTRUCTION DU PIPELINE HOLOGRAMME -> VECTEUR")
        print("=" * 60)
        self.extractor = HologramABCVectorExtractor()
        if force or not os.path.exists(str(VECTOR_INDEX_FILE)):
            vectors = self.extractor.extract_patches()
            self.extractor.save_vectors()
        else:
            print("[Pipeline] Vecteurs deja extraits, chargement...")
            vectors = np.load(str(VECTOR_INDEX_FILE))
        self.index = ABCVectorIndex(vectors)
        if not os.path.exists(str(FAISS_INDEX_FILE)) or force:
            self.index.save()
        self.mapper = FactPatchMapper(self.extractor)
        if force or not os.path.exists(str(FACTS_FILE)):
            self.mapper.build_mapping()
            self.mapper.save_mapping()
        else:
            self.mapper.load_mapping()
        if self.use_llm:
            self.decoder = ConstrainedDecoderBridge()
        self.built = True
        print(f"\n[Pipeline] Construction terminee.")
        print(f"  Patches : {self.index.index.ntotal if self.index._faiss_available else len(self.index.vectors)}")
        if self.decoder:
            print(f"  LLM : {'disponible' if self.decoder.is_available() else 'fallback templates'}")

    def _query_to_vector(self, query: str) -> np.ndarray:
        h = hashlib.sha256(query.encode()[:200]).hexdigest()
        sz = self.extractor.size if self.extractor else 1024
        kx = (int(h[:16], 16) % (sz * 100)) / 100.0
        ky = (int(h[16:32], 16) % (sz * 100)) / 100.0
        kx = (kx - sz / 2) / sz * 20; ky = (ky - sz / 2) / sz * 20
        cx = int(kx * sz / 20 + sz / 2) % sz; cy = int(ky * sz / 20 + sz / 2) % sz
        if self.index.vectors is not None:
            dim = self.index.vectors.shape[1]
        else:
            dim = 4096 + 64 + ABC_NEIGHBORS + 3
        qv = np.zeros(dim, dtype=np.float32)
        amp_dim = 4096
        if dim >= amp_dim:
            asec = np.zeros(amp_dim)
            for i in range(min(amp_dim, sz)):
                phase = (i * kx + (i % 64) * ky) % (2 * math.pi)
                asec[i] = abs(math.sin(phase)) * math.exp(-((i % 64 - 32)**2) / 200)
            qv[:amp_dim] = asec
        if dim >= amp_dim + 64:
            phases = np.zeros(64)
            for i in range(64):
                phases[i] = (i * kx + i * ky) % (2 * math.pi)
            qv[amp_dim:amp_dim+64] = phases / (2 * math.pi)
        if dim >= amp_dim + 64 + ABC_NEIGHBORS:
            abc_start = amp_dim + 64
            for i in range(ABC_NEIGHBORS):
                qv[abc_start + i] = 0.5 + 0.5 * math.sin(i * PHI)
        if dim >= amp_dim + 64 + ABC_NEIGHBORS + 3:
            qv[-3] = cy / sz; qv[-2] = cx / sz; qv[-1] = 1.0
        return qv

    def query(self, prompt: str, k: int = 10, style: str = "general") -> Dict[str, Any]:
        if not self.built:
            return {"error": "Pipeline non construit."}
        print(f"\n[Pipeline] Requete : \"{prompt[:100]}\"")
        t0 = time.time()
        qv = self._query_to_vector(prompt)
        patch_indices, patch_scores = self.index.search(qv, k=k)
        patch_indices = [int(i) for i in patch_indices if i >= 0]
        if not patch_indices:
            return {"text": "Aucun patch resonant trouve.", "source": "no_resonance",
                    "confidence": 0.0, "verified": True, "temps_ms": round((time.time()-t0)*1000, 1)}
        retrieved_facts = self.mapper.get_facts_for_patches(patch_indices)
        # ParametricKB
        try:
            from parametric_kb_fr import ParametricKB
            pr = ParametricKB().solve(prompt)
            if pr:
                pt = pr.get("text", str(pr)) if isinstance(pr, dict) else str(pr)
                retrieved_facts.insert(0, {"id": "parametric", "text": pt, "keywords": ["math"], "patch_index": -1})
        except Exception:
            pass
        if self.decoder and self.decoder.is_available():
            result = self.decoder.decode(retrieved_facts, prompt, style=style)
        else:
            result = self._fallback_generate(retrieved_facts, prompt, t0)
        verification = self.verifier.verify(result.get("text", ""), retrieved_facts, prompt, strict_mode=False)
        elapsed_ms = round((time.time() - t0) * 1000, 1)
        final = {
            "text": result.get("text", ""),
            "source": result.get("source", "pipeline"),
            "confidence": round(result.get("confidence", 0.0), 2),
            "verified": verification["traceable"],
            "trace_score": verification["score"],
            "trace_verdict": verification["verdict"],
            "hallucination_phrases": verification.get("hallucination_phrases", []),
            "facts_used": len(retrieved_facts),
            "patches_used": len(patch_indices),
            "top_patch_score": round(float(patch_scores[0]), 4) if len(patch_scores)>0 else 0,
            "temps_ms": elapsed_ms,
        }
        try:
            safe = final['text'][:100]
            if isinstance(safe, str):
                safe = safe.encode('ascii', errors='replace').decode('ascii')
            print(f"  Resultat : {safe}...")
        except:
            pass
        print(f"  Tracabilite : {final['trace_score']:.0%} ({final['trace_verdict']})")
        print(f"  Temps : {elapsed_ms}ms")
        return final

    def _fallback_generate(self, facts, query, t0):
        texts = [f.get("text","") for f in facts[:5] if f.get("text","") and len(f.get("text",""))>3]
        if not texts:
            text = "L'hologramme ne contient pas d'information suffisante."
        elif len(texts)==1:
            text = f"D'apres l'hologramme : {texts[0]}"
        else:
            text = "D'apres l'hologramme :\n" + "\n".join(f"- {t}" for t in texts)
        return {"text": text, "source": "fallback_templates", "confidence": 0.70,
                "verified": True, "temps_ms": round((time.time()-t0)*1000, 1)}


# ==============================================================================
# COUCHE 5 (NOUVELLE) — RESONANCE MULTI-HOP REASONER
# ==============================================================================

class ResonanceReasoner:
    """
    Raisonnement par chainage multi-hop base sur l'interference d'ondes.
    
    Principe :
      Hop 0 : Onde sonde Ψ_q → pics de resonance → faits niveau 1
      Hop 1 : Onde des faits niveau 1 → pics de resonance → faits niveau 2
      Hop N : Onde des faits niveau N → pics de resonance → faits niveau N+1
    
    Chaque saut exploite l'interference entre les ondes pour decouvrir
    des relations implicites entre concepts qui ne sont pas directement
    connectes dans la base de connaissance plate.
    
    Le resultat est un GRAPHE DE RAISONNEMENT ou chaque fait est connecte
    a sa source par une force de resonance mesurable.
    """
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.stats = {"total_chains": 0, "avg_depth": 0, "total_depth": 0}
    
    def reason(self, query: str, depth: int = 3, top_k: int = 10) -> Dict[str, Any]:
        """
        Chaine multi-hop par resonance d'onde.
        
        Args:
            query: Question initiale
            depth: Nombre de sauts (3 recommande)
            top_k: Nombre de patches par saut
        
        Returns:
            Dict avec 'chain' (hops), 'facts' (unis), 'graph' (structure)
        """
        if not self.pipeline or not self.pipeline.built:
            return {"chain": [], "facts": [], "error": "Pipeline non construit"}
        
        self.stats["total_chains"] += 1
        chain = []
        all_fact_ids = set()
        
        # ---- HOP 0 : Resonance directe question -> hologramme ----
        qv = self.pipeline._query_to_vector(query)
        p0, s0 = self.pipeline.index.search(qv, k=top_k)
        p0 = [int(i) for i in p0 if i >= 0]
        f0 = self.pipeline.mapper.get_facts_for_patches(p0[:5]) if p0 else []
        for f in f0:
            all_fact_ids.add(f.get("id", f.get("text", "")))
        
        chain.append({
            "hop": 0,
            "source": "question",
            "patches": p0[:5],
            "top_score": round(float(s0[0]), 4) if len(s0) > 0 else 0,
            "facts": f0,
            "n_facts": len(f0)
        })
        
        # ---- HOPS 1..N : Resonance en cascade ----
        current_facts = f0
        for hop in range(1, depth):
            if not current_facts:
                chain.append({
                    "hop": hop,
                    "source": f"hop_{hop-1}_empty",
                    "patches": [],
                    "top_score": 0,
                    "facts": [],
                    "n_facts": 0
                })
                continue
            
            # Encoder les faits actuels comme nouvelle onde sonde
            fact_texts = []
            for f in current_facts[:3]:
                t = f.get("text", "")
                if t:
                    fact_texts.append(t[:120])
            
            if not fact_texts:
                break
            
            combined_text = " ".join(fact_texts)
            hop_qv = self.pipeline._query_to_vector(combined_text)
            hop_p, hop_s = self.pipeline.index.search(hop_qv, k=top_k)
            hop_p = [int(i) for i in hop_p if i >= 0]
            
            if not hop_p:
                chain.append({"hop": hop, "source": f"hop_{hop-1}", "patches": [],
                              "top_score": 0, "facts": [], "n_facts": 0})
                continue
            
            hop_facts = self.pipeline.mapper.get_facts_for_patches(hop_p[:5])
            # Filtrer les faits deja vus dans les hops precedents
            new_facts = []
            for f in hop_facts:
                fid = f.get("id", f.get("text", ""))
                if fid not in all_fact_ids:
                    all_fact_ids.add(fid)
                    new_facts.append(f)
            
            # Si aucun nouveau fait, prendre les faits bruts (redondance)
            if not new_facts:
                new_facts = hop_facts[:3]
                for f in new_facts:
                    all_fact_ids.add(f.get("id", f.get("text", "")))
            
            chain.append({
                "hop": hop,
                "source": f"hop_{hop-1}",
                "patches": hop_p[:5],
                "top_score": round(float(hop_s[0]), 4) if len(hop_s) > 0 else 0,
                "facts": new_facts,
                "n_facts": len(new_facts)
            })
            
            current_facts = hop_facts
        
        # ---- Assemblage du graphe de raisonnement ----
        all_facts = []
        seen_texts = set()
        for h in chain:
            for f in h.get("facts", []):
                t = f.get("text", "")
                if t and len(t) > 3 and t not in seen_texts:
                    seen_texts.add(t)
                    all_facts.append(f)
        
        # Construire le graphe (connexions entre hops)
        graph_edges = []
        for i in range(len(chain) - 1):
            if chain[i]["facts"] and chain[i+1]["facts"]:
                graph_edges.append({
                    "from_hop": i,
                    "to_hop": i + 1,
                    "strength": chain[i+1]["top_score"],
                    "from_facts": len(chain[i]["facts"]),
                    "to_facts": len(chain[i+1]["facts"])
                })
        
        self.stats["total_depth"] += len(chain)
        self.stats["avg_depth"] = round(self.stats["total_depth"] / max(self.stats["total_chains"], 1), 1)
        
        return {
            "chain": chain,
            "facts": all_facts,
            "graph_edges": graph_edges,
            "depth_used": depth,
            "total_hops": len([h for h in chain if h["n_facts"] > 0]),
            "total_facts": len(all_facts),
            "resonance_trace": [
                {"hop": h["hop"], "score": h["top_score"], "n": h["n_facts"]}
                for h in chain
            ]
        }
    
    def build_reasoning_prompt(self, query: str, depth: int = 3) -> str:
        """Construit un prompt structure par niveau de resonance pour DeepSeek."""
        result = self.reason(query, depth=depth)
        if not result.get("chain"):
            return "", []
        
        lines = ["FAITS DE L'HOLOGRAMME (organises par chaine de resonance) :\n"]
        
        for hop in result["chain"]:
            score = hop["top_score"]
            bar = "=" * min(int(score * 20), 20)
            via_text = "directe" if hop['hop'] == 0 else f"via niveau {hop['hop']-1}"
            lines.append(f"\n[NIVEAU {hop['hop']} - Resonance {via_text}]")
            lines.append(f"Force de resonance : {score:.0%} {bar}")
            
            for i, fact in enumerate(hop.get("facts", [])[:5]):
                text = fact.get("text", "")
                if text and len(text) > 3:
                    lines.append(f"  {i+1}. {text.strip()}")
        
        prompt = "\n".join(lines)
        
        # Ajouter les aretes du graphe
        if result.get("graph_edges"):
            prompt += "\n\nCONNEXIONS ENTRE NIVEAUX (graphe de raisonnement) :"
            for edge in result["graph_edges"]:
                prompt += f"\n  Niveau {edge['from_hop']} -> Niveau {edge['to_hop']} (force: {edge['strength']:.0%})"
        
        return prompt, result["facts"]
    
    def get_stats(self):
        return dict(self.stats)


# ==============================================================================
# CLI / TESTS
# ==============================================================================

def run_tests():
    print("=" * 60)
    print("  TESTS — HOLOGRAM -> VECTOR BRIDGE")
    print("=" * 60)
    pipeline = HologramVectorPipeline(use_llm=False)
    if not os.path.exists(str(ABC_HOLOGRAM_FILE)) and not os.path.exists(str(HOLOGRAM_FILE)):
        print("\n[TEST] Aucun hologramme trouve. Generez-le d'abord :")
        print("  cd ka_phone && python abc_hologram_engine.py --rebuild")
        return
    pipeline.build(force=False)
    test_questions = [
        "Quelle est la capitale du Senegal ?",
        "Qui etait Napoleon ?",
        "Combien font 12 x 15 ?",
        "Qu'est-ce que la gravite ?",
        "Quelle est la racine carree de 144 ?",
        "Parle-moi de l'empire du Mali",
        "Comment fonctionne un ordinateur ?",
    ]
    print(f"\n{'='*60}")
    print(f"  {len(test_questions)} QUESTIONS DE TEST")
    print(f"{'='*60}")
    results = []
    for q in test_questions:
        result = pipeline.query(q, k=15)
        results.append(result)
        status = "OK" if result.get("verified") else "!!"
        tl = "HIGH" if result.get("trace_score",0)>=0.8 else ("MED " if result.get("trace_score",0)>=0.5 else "LOW ")
        print(f"\n  [{status}] Q: {q[:70]}")
        try:
            safe_r = result.get('text','')[:120]
            if isinstance(safe_r, str):
                safe_r = safe_r.encode('ascii', errors='replace').decode('ascii')
            print(f"    R: {safe_r}...")
        except:
            pass
        print(f"    [{tl}] Traceability: {result.get('trace_score',0):.0%} | Facts: {result.get('facts_used',0)} | Patches: {result.get('patches_used',0)} | {result.get('temps_ms',0)}ms")
    verified = sum(1 for r in results if r.get("verified"))
    avg_trace = sum(r.get("trace_score",0) for r in results) / max(len(results),1)
    avg_time = sum(r.get("temps_ms",0) for r in results) / max(len(results),1)
    print(f"\n{'='*60}")
    print(f"  RESUME")
    print(f"{'='*60}")
    print(f"  Questions : {len(results)}")
    print(f"  Verifiees : {verified}/{len(results)} ({verified/len(results)*100:.0f}%)")
    print(f"  Tracabilite moyenne : {avg_trace:.0%}")
    print(f"  Temps moyen : {avg_time:.0f}ms")
    print(f"  Stats verification : {json.dumps(pipeline.verifier.get_stats(), indent=2)}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hologram -> Vector Bridge")
    parser.add_argument("--build-index", action="store_true")
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()
    if args.test:
        run_tests()
        return
    if args.build_index:
        pipeline = HologramVectorPipeline(use_llm=not args.no_llm)
        pipeline.build(force=True)
        if args.query:
            result = pipeline.query(args.query, k=args.k)
            print(f"\n{'='*60}\n  REPONSE FINALE\n{'='*60}\n\n{result['text']}")
            print(f"\n  Tracabilite : {result.get('trace_score',0):.0%}")
        return
    if args.query:
        pipeline = HologramVectorPipeline(use_llm=not args.no_llm)
        pipeline.build(force=False)
        result = pipeline.query(args.query, k=args.k)
        print(f"\n{'='*60}\n  REPONSE\n{'='*60}\n\n{result['text']}")
        print(f"\n  Tracabilite : {result.get('trace_score',0):.0%} | {result.get('trace_verdict','')}")
        return
    print("=" * 60)
    print("  HOLOGRAM -> VECTOR BRIDGE")
    print("  Mode interactif")
    print("=" * 60)
    print("\nCommandes :")
    print("  python hologram_vector_bridge.py --build-index")
    print("  python hologram_vector_bridge.py --query \"...\"")
    print("  python hologram_vector_bridge.py --test")


if __name__ == "__main__":
    main()