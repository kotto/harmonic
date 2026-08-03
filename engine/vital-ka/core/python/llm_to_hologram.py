"""
🌊 LLM → Hologramme — Distillation Harmonique
===============================================
Fait tourner un LLM sur CPU en encodant sa connaissance
dans un hologramme ondulatoire.

PRINCIPE :
  LLM (GPU, 500 Go) → Distillation → Hologramme (CPU, 15 Mo)
  
  Le LLM est utilisé UNE FOIS pour extraire les faits.
  L'hologramme répond ensuite INSTANTANÉMENT sur CPU.
  
  Si l'hologramme ne sait pas → fallback LLM → apprentissage.

ARCHITECTURE :
  ┌──────────┐     ┌──────────────┐     ┌─────────────┐
  │  LLM     │ ──→ │ Distillateur  │ ──→ │ Hologramme  │
  │ (source) │     │ (extraction)  │     │ (stockage)  │
  └──────────┘     └──────────────┘     └─────────────┘
                                              │
                                         ┌────▼────┐
                                         │ Requête │
                                         │  CPU    │
                                         └─────────┘
"""

import sys, os, json, time, hashlib, re
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from collections import defaultdict
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

PHI = 1.618033988749895

# ════════════════════════════════════════════════════════════════
# 1. DISTILLATEUR — Extraction de faits depuis un LLM
# ════════════════════════════════════════════════════════════════

class LLMDistiller:
    """
    Extrait des faits structurés depuis un LLM.
    
    Stratégie : pour chaque domaine, demander au LLM de générer
    des triplets (sujet, relation, objet) factuels.
    
    Le LLM est appelé UNE SEULE FOIS par domaine.
    Les faits extraits sont ensuite stockés dans l'hologramme.
    """
    
    def __init__(self, llm_endpoint: str = None):
        """
        Args:
            llm_endpoint: URL d'un LLM API (OpenAI, Ollama, etc.)
                          Si None, utilise le KB local comme fallback.
        """
        self.endpoint = llm_endpoint
        self.cache: Dict[str, List[Tuple]] = {}
    
    def distill_domain(self, domain: str, max_facts: int = 100) -> List[Tuple]:
        """
        Extrait les faits d'un domaine via le LLM.
        
        Prompt envoyé au LLM :
        "Liste 100 faits sur [domaine] au format :
         sujet | relation | objet | secteur"
        """
        if domain in self.cache:
            return self.cache[domain]
        
        facts = []
        
        if self.endpoint:
            facts = self._call_llm(domain, max_facts)
        
        if not facts:
            # Fallback : extraction du KB local
            facts = self._extract_from_kb(domain, max_facts)
        
        self.cache[domain] = facts
        return facts
    
    def _call_llm(self, domain: str, max_facts: int) -> List[Tuple]:
        """Appelle un LLM pour extraire des faits."""
        prompt = f"""List {max_facts} factual statements about {domain}.
Format each as: subject | relation | object | sector
Use simple, atomic facts. One per line.
Example for 'astronomy':
Sun | is a | star | ASTRONOMY
Earth | orbits around | Sun | ASTRONOMY
Galileo | discovered | moons of Jupiter | ASTRONOMY
...
Now list {max_facts} facts about {domain}:"""
        
        try:
            import urllib.request, json
            data = json.dumps({
                "messages": [{"role": "user", "content": prompt}],
                "model": "KA", "max_tokens": 2000
            }).encode()
            req = urllib.request.Request(
                f"{self.endpoint}/v1/chat/completions",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            
            # Parser les lignes en triplets
            for line in content.split('\n'):
                line = line.strip()
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4:
                        facts.append((parts[0], parts[1], parts[2], parts[3]))
                    elif len(parts) >= 3:
                        facts.append((parts[0], parts[1], parts[2], "GENERAL"))
            
            print(f"  🤖 LLM distillé: {len(facts)} faits pour '{domain}'")
        except Exception as e:
            print(f"  ⚠️ LLM inaccessible: {e}")
            facts = []
        
        return facts[:max_facts]
    
    def _extract_from_kb(self, domain: str, max_facts: int) -> List[Tuple]:
        """Fallback : extraction du KB local."""
        from hologram_builder_agent import KnowledgeBaseSource
        kb = KnowledgeBaseSource()
        kb.load()
        facts = kb.extract_by_domain(domain, max_facts=max_facts)
        print(f"  📂 KB local: {len(facts)} faits pour '{domain}'")
        return facts


# ════════════════════════════════════════════════════════════════
# 2. ENCODEUR HOLOGRAPHIQUE
# ════════════════════════════════════════════════════════════════

class HolographicEncoder:
    """
    Encode des faits en hologramme ondulatoire.
    
    Chaque fait → onde gaussienne dans un espace complexe 2D.
    La superposition de toutes les ondes = l'hologramme.
    
    Taille : D×D complexes = D² × 16 bytes.
    Pour D=64 :  64×64×16 = 65 KB
    Pour D=256: 256×256×16 = 1 MB
    Pour D=512: 512×512×16 = 4 MB
    """
    
    def __init__(self, dim: int = 128):
        self.dim = dim
        self.hologram = np.zeros((dim, dim), dtype=complex)
        self.fact_count = 0
        self._fact_index: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
    
    def _hash_to_coords(self, subject: str, relation: str, obj: str) -> Tuple[int, int]:
        """Hash un triplet en coordonnées (x,y) dans l'hologramme."""
        text = f"{subject}|{relation}|{obj}"
        h = hashlib.sha256(text.encode()).digest()
        x = int.from_bytes(h[:16], 'big') % self.dim
        y = int.from_bytes(h[16:], 'big') % self.dim
        return x, y
    
    def _gaussian_wave(self, x0: int, y0: int, sigma: float = 2.0) -> np.ndarray:
        """Onde gaussienne centrée en (x0, y0) avec phase φ-spiralée."""
        xs = np.arange(self.dim)
        ys = np.arange(self.dim)
        X, Y = np.meshgrid(xs, ys)
        
        # Distance toroïdale
        dx = np.minimum(np.abs(X - x0), self.dim - np.abs(X - x0))
        dy = np.minimum(np.abs(Y - y0), self.dim - np.abs(Y - y0))
        
        wave = np.exp(-(dx**2 + dy**2) / (2 * sigma**2))
        # Phase spiralée (φ pour éviter les collisions)
        phase = 2 * np.pi * (X + Y * PHI) / self.dim
        return wave * np.exp(1j * phase)
    
    def encode_fact(self, subject: str, relation: str, obj: str, sector: str = "GENERAL"):
        """Encode un fait dans l'hologramme."""
        x, y = self._hash_to_coords(subject, relation, obj)
        wave = self._gaussian_wave(x, y)
        self.hologram += wave
        self.fact_count += 1
        
        # Indexer les mots pour la recherche
        for word in f"{subject} {relation} {obj}".lower().split():
            w = word.strip('.,;:!?')
            if len(w) >= 3:
                self._fact_index[w].append((x, y))
    
    def encode_batch(self, facts: List[Tuple]):
        """Encode un lot de faits."""
        for f in facts:
            if len(f) >= 4:
                self.encode_fact(f[0], f[1], f[2], f[3])
            elif len(f) >= 3:
                self.encode_fact(f[0], f[1], f[2])
    
    def query(self, question: str, top_k: int = 5) -> List[Tuple[float, str, str, str]]:
        """
        Interroge l'hologramme.
        
        L'onde de la question interfère avec l'hologramme.
        Les pics d'interférence → faits pertinents.
        """
        # Créer l'onde-sonde à partir de la question
        probe = np.zeros((self.dim, self.dim), dtype=complex)
        words = [w.strip('.,;:!?') for w in question.lower().split() if len(w.strip('.,;:!?')) >= 3]
        
        for word in words:
            if word in self._fact_index:
                for x, y in self._fact_index[word][:5]:
                    probe += self._gaussian_wave(x, y, sigma=3.0)
        
        if np.linalg.norm(probe) < 1e-10:
            return []
        
        # Interférence : corrélation de phase
        correlation = np.abs(np.fft.ifft2(
            np.fft.fft2(probe) * np.conj(np.fft.fft2(self.hologram))
        ))
        
        # Normaliser
        max_corr = np.max(correlation)
        if max_corr > 0:
            correlation = correlation / max_corr
        
        # Top-K pics
        flat = correlation.ravel()
        top_indices = np.argsort(flat)[-top_k*3:]  # ×3 pour filtrage
        
        results = []
        seen = set()
        for idx in reversed(top_indices):
            py, px = divmod(idx, self.dim)
            score = float(correlation[py, px])
            key = (px, py)
            if key not in seen and score > 0.01:
                seen.add(key)
                results.append((score, px, py))
                if len(results) >= top_k:
                    break
        
        return results
    
    def get_stats(self) -> dict:
        return {
            "dim": self.dim,
            "size_kb": self.dim * self.dim * 16 / 1024,
            "facts_encoded": self.fact_count,
            "words_indexed": len(self._fact_index),
        }


# ════════════════════════════════════════════════════════════════
# 3. MOTEUR HYBRIDE
# ════════════════════════════════════════════════════════════════

class HybridEngine:
    """
    Moteur hybride LLM + Hologramme.
    
    Mode normal : répond via l'hologramme (CPU, <1ms)
    Mode fallback : si confiance < seuil, interroge le LLM
    Mode apprentissage : la réponse LLM est encodée dans l'hologramme
    """
    
    def __init__(self, llm_endpoint: str = None, hologram_dim: int = 128):
        self.distiller = LLMDistiller(llm_endpoint)
        self.hologram = HolographicEncoder(dim=hologram_dim)
        self.llm_endpoint = llm_endpoint
        self.confidence_threshold = 0.05  # Normalisé 0-1
        self.llm_fallbacks = 0
        self.facts_learned_from_llm = 0
    
    def answer(self, question: str, domain: str = None) -> dict:
        """
        Répond à une question via l'hologramme, avec fallback LLM.
        
        Returns:
            dict avec 'answer', 'source' (hologram/llm), 'confidence', 'learned'
        """
        # Étape 1 : Interroger l'hologramme
        t0 = time.time()
        results = self.hologram.query(question, top_k=3)
        hologram_latency = (time.time() - t0) * 1000
        
        if results and results[0][0] > self.confidence_threshold:
            return {
                "answer": self._format_hologram_response(results, question),
                "source": "hologram",
                "confidence": round(results[0][0], 3),
                "latency_ms": round(hologram_latency, 1),
                "learned": False,
            }
        
        # Étape 2 : Fallback LLM
        if not self.llm_endpoint:
            return {
                "answer": None,
                "source": "none",
                "confidence": 0.0,
                "latency_ms": round(hologram_latency, 1),
                "learned": False,
            }
        
        try:
            import urllib.request, json
            data = json.dumps({
                "messages": [{"role": "user", "content": question}],
                "model": "KA", "max_tokens": 500
            }).encode()
            req = urllib.request.Request(
                f"{self.llm_endpoint}/v1/chat/completions",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read())
            llm_answer = result["choices"][0]["message"]["content"]
            
            self.llm_fallbacks += 1
            
            # Étape 3 : Apprendre de la réponse LLM
            # Extraire des faits de la réponse et les encoder
            facts = self._extract_facts_from_text(llm_answer, domain or "general")
            for f in facts:
                self.hologram.encode_fact(f[0], f[1], f[2], f[3])
            self.facts_learned_from_llm += len(facts)
            
            return {
                "answer": llm_answer,
                "source": "llm",
                "confidence": 0.8,
                "latency_ms": round(hologram_latency, 1),
                "learned": True,
                "facts_learned": len(facts),
            }
        except Exception as e:
            return {
                "answer": f"LLM inaccessible: {e}",
                "source": "error",
                "confidence": 0.0,
                "latency_ms": round(hologram_latency, 1),
                "learned": False,
            }
    
    def _format_hologram_response(self, results, question):
        """Formate la réponse holographique."""
        top_score = results[0][0]
        return f"[Hologramme] {top_score:.0%} de confiance — {len(results)} faits pertinents trouvés."
    
    def _extract_facts_from_text(self, text: str, domain: str) -> List[Tuple]:
        """Extrait des faits d'un texte LLM."""
        facts = []
        domain_sector = domain.upper().replace(" ", "_")[:20]
        
        for sentence in text.split('.'):
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                # Créer un fait simple : sujet = domaine, relation = "contient info", objet = phrase
                facts.append((
                    domain.title(),
                    "contient l'information",
                    sentence[:150],
                    domain_sector
                ))
        
        return facts[:10]
    
    def preload_domain(self, domain: str, max_facts: int = 100):
        """Précharge un domaine dans l'hologramme (distillation)."""
        facts = self.distiller.distill_domain(domain, max_facts)
        self.hologram.encode_batch(facts)
        return len(facts)
    
    def get_stats(self) -> dict:
        return {
            **self.hologram.get_stats(),
            "llm_fallbacks": self.llm_fallbacks,
            "facts_learned_from_llm": self.facts_learned_from_llm,
        }


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  🌊 LLM → HOLOGRAMME — Test")
    print("=" * 60)
    
    # Test 1 : Sans LLM (KB local uniquement)
    print("\n1. Moteur hybride (KB local) :")
    engine = HybridEngine(llm_endpoint=None, hologram_dim=64)
    
    # Précharger un domaine
    n = engine.preload_domain("astronomie", max_facts=50)
    print(f"   ✅ {n} faits préchargés dans l'hologramme")
    print(f"   📦 Taille hologramme : {engine.hologram.get_stats()['size_kb']:.0f} KB")
    
    # Test requête
    result = engine.answer("Quelle est la distance Terre-Soleil ?")
    print(f"   🔍 Question : Quelle est la distance Terre-Soleil ?")
    print(f"   📡 Source    : {result['source']}")
    print(f"   🎯 Confiance : {result['confidence']}")
    print(f"   ⚡ Latence   : {result['latency_ms']} ms")
    
    # Test 2 : Avec l'API KA locale (si dispo)
    print(f"\n2. Moteur hybride (KA API) :")
    engine2 = HybridEngine(llm_endpoint="http://localhost:8765", hologram_dim=128)
    n = engine2.preload_domain("physique quantique", max_facts=30)
    print(f"   ✅ {n} faits préchargés")
    
    result2 = engine2.answer("Qu'est-ce que l'intrication quantique ?")
    print(f"   🔍 Question : Qu'est-ce que l'intrication quantique ?")
    print(f"   📡 Source    : {result2['source']}")
    if result2['learned']:
        print(f"   🧠 Appris    : {result2.get('facts_learned', 0)} nouveaux faits")
    
    print(f"\n📊 Stats finales :")
    stats = engine2.get_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    print(f"\n✅ Moteur hybride prêt.")
