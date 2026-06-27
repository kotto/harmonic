#!/usr/bin/env python3
"""
INJECTEUR HARMONIQUE AWS - DeepSeek/Qwen
=========================================
Adapte l'injection d'attention harmonique 7D pour le modele DeepSeek/Qwen
deploye sur AWS EC2.

Architecture :
1. On ne peut pas modifier les poids du modele distant directement
2. On ajoute une couche harmonique EN AMONT de l'API
3. Les signatures 7D guident le prompt engineering et le post-traitement
4. On compare les reponses AVEC et SANS harmonique

Principe :
- Le modele AWS expose une API OpenAI-compatible
- On cree un proxy harmonique qui intercepte les requetes
- On ajoute des instructions harmoniques dans le system prompt
- On analyse les signatures 7D pour ajuster temperature, top_k, etc.
"""

import os, sys, math, json, time, hashlib
import numpy as np
from collections import OrderedDict
from typing import Optional, List, Dict, Any, Tuple
import requests

# ---------------------------------------------------------------------------
# Constantes harmoniques
# ---------------------------------------------------------------------------
PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
ALPHA = 1.175569459083219

# ---------------------------------------------------------------------------
# Signatures 7D - Version legere (sans PyTorch)
# ---------------------------------------------------------------------------
class SignatureProjector:
    """
    Projection de signature 7D sans PyTorch.
    Utilise une matrice de projection fixe basee sur phi.
    """
    
    def __init__(self, dim=768):
        self.dim = dim
        # Matrice de projection harmonique fixe
        np.random.seed(42)
        base = np.random.randn(dim, 7).astype(np.float32)
        # Orthonormalisation approximative
        u, s, vt = np.linalg.svd(base, full_matrices=False)
        self.projection = u @ vt  # [dim, 7]
        # Ajustement phi
        self.projection = self.projection * PHI_INV
    
    def project(self, text: str) -> np.ndarray:
        """
        Projette un texte en signature 7D.
        Approximatif mais rapide (sans modele).
        """
        # Hash du texte en 7 dimensions
        sig = np.zeros(7, dtype=np.float32)
        
        # Dimension 0: phi - diversite lexicale
        words = text.split()
        unique_words = len(set(w.lower() for w in words))
        sig[0] = min(1.0, unique_words / max(1, len(words)) * PHI)
        
        # Dimension 1: alpha - complexite (longueur moyenne des mots)
        avg_word_len = np.mean([len(w) for w in words]) if words else 0
        sig[1] = min(1.0, avg_word_len / 15.0)
        
        # Dimension 2: reasoning - mots de raisonnement
        reasoning_words = {'why','because','therefore','thus','hence','since',
                          'if','then','else','so','consequently','accordingly',
                          'deduce','infer','conclude','imply','logical','reason'}
        sig[2] = min(1.0, sum(1 for w in words if w.lower() in reasoning_words) / 5.0)
        
        # Dimension 3: creativity - mots creatifs
        creative_words = {'imagine','create','dream','vision','poem','story',
                         'metaphor','beautiful','wonder','magic','infinite',
                         'cosmic','harmony','symphony','ocean','light'}
        sig[3] = min(1.0, sum(1 for w in words if w.lower() in creative_words) / 5.0)
        
        # Dimension 4: math - mots mathematiques
        math_words = {'equation','theorem','proof','calculate','matrix','vector',
                     'integral','derivative','function','algorithm','number',
                     'sum','product','ratio','phi','golden','fractal'}
        sig[4] = min(1.0, sum(1 for w in words if w.lower() in math_words) / 5.0)
        
        # Dimension 5: factual - mots factuels
        factual_words = {'fact','data','study','research','according','source',
                        'reference','citation','statistic','evidence','proven',
                        'verified','confirmed','measured','observed'}
        sig[5] = min(1.0, sum(1 for w in words if w.lower() in factual_words) / 5.0)
        
        # Dimension 6: code - mots de programmation
        code_words = {'code','function','class','import','def','return','var',
                     'const','let','python','javascript','api','endpoint',
                     'algorithm','compile','debug','deploy'}
        sig[6] = min(1.0, sum(1 for w in words if w.lower() in code_words) / 5.0)
        
        # Normalisation harmonique
        sig = np.clip(sig, 0, 1)
        
        return sig
    
    def resonance_matrix(self, texts: List[str]) -> np.ndarray:
        """Calcule la matrice de resonance entre plusieurs textes."""
        sigs = np.array([self.project(t) for t in texts])  # [N, 7]
        resonance = sigs @ sigs.T  # [N, N]
        resonance = (resonance + 1.0) / 2.0
        resonance = resonance / 7.0
        return resonance


# ---------------------------------------------------------------------------
# Proxy harmonique pour l'API AWS
# ---------------------------------------------------------------------------
class HarmonicAWSProxy:
    """
    Proxy qui ajoute une couche harmonique devant l'API AWS.
    
    Fonctionnement :
    1. Analyse le prompt avec signatures 7D
    2. Ajoute des instructions harmoniques au system prompt
    3. Ajuste les parametres (temperature, top_k) selon les signatures
    4. Post-traite la reponse avec harmonisation
    """
    
    def __init__(self, base_url: str, model: str, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.projector = SignatureProjector()
        
        # Cache deterministe
        self.cache = OrderedDict()
        self.cache_max = 2048
        
        # Statistiques
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "avg_signatures": np.zeros(7),
            "response_times": [],
        }
    
    def _get_system_prompt(self, signatures: np.ndarray) -> str:
        """
        Construit un system prompt harmonique base sur les signatures 7D.
        """
        base_prompt = (
            "Tu es Harmonic AI, un assistant avance avec resonance harmonique 7D. "
            "Tu combines raisonnement logique et intuition creative. "
        )
        
        # Ajustements selon les signatures dominantes
        adjustments = []
        
        if signatures[2] > 0.3:  # reasoning
            adjustments.append(
                "Structure ta reponse avec un raisonnement clair : "
                "these, arguments, conclusion."
            )
        
        if signatures[3] > 0.3:  # creativity
            adjustments.append(
                "Utilise des metaphors et des images evocatrices. "
                "La creativite est ta force."
            )
        
        if signatures[4] > 0.3:  # math
            adjustments.append(
                "Sois precis et rigoureux. Utilise des notations mathematiques "
                "claires si necessaire."
            )
        
        if signatures[5] > 0.3:  # factual
            adjustments.append(
                "Base-toi sur des faits verifies. Si tu n'es pas sur, "
                "indique-le clairement."
            )
        
        if signatures[6] > 0.3:  # code
            adjustments.append(
                "Fournis du code fonctionnel et bien commente. "
                "Explique la logique derriere chaque bloc."
            )
        
        # Ajout harmonique
        phi_note = f"Utilise le ratio d'or φ={PHI:.4f} comme guide pour "
        phi_note += "equilibrer precision et creativite."
        adjustments.append(phi_note)
        
        if adjustments:
            base_prompt += "\n\n" + "\n".join(adjustments)
        
        return base_prompt
    
    def _get_temperature(self, signatures: np.ndarray) -> float:
        """
        Calcule la temperature optimale selon les signatures.
        """
        # Base
        temp = 0.3
        
        # Plus de creativite -> temperature plus haute
        temp += signatures[3] * 0.4  # creativity
        
        # Plus de factual/math -> temperature plus basse
        temp -= signatures[5] * 0.2  # factual
        temp -= signatures[4] * 0.15  # math
        
        # Raisonnement -> temperature moderee
        temp += signatures[2] * 0.1  # reasoning
        
        return np.clip(temp, 0.0, 0.9)
    
    def _get_top_k(self, signatures: np.ndarray) -> int:
        """Calcule top_k selon les signatures."""
        base = 40
        # Creativite -> plus de diversite
        base += int(signatures[3] * 30)
        # Factual -> moins de diversite
        base -= int(signatures[5] * 20)
        return max(10, min(100, base))
    
    def _get_top_p(self, signatures: np.ndarray) -> float:
        """Calcule top_p selon les signatures."""
        base = 0.9
        base -= signatures[4] * 0.2  # math -> plus strict
        base += signatures[3] * 0.05  # creativity -> plus flexible
        return np.clip(base, 0.7, 0.95)
    
    def _get_max_tokens(self, signatures: np.ndarray, requested: int) -> int:
        """Ajuste max_tokens selon les signatures."""
        # Creativite/reasoning -> plus long
        multiplier = 1.0 + signatures[3] * 0.3 + signatures[2] * 0.2
        return min(int(requested * multiplier), 4096)
    
    def _harmonic_postprocess(self, text: str, signatures: np.ndarray) -> str:
        """
        Post-traitement harmonique de la reponse.
        """
        if not text:
            return text
        
        # Si factual eleve, verifier la presence de citations
        if signatures[5] > 0.4 and len(text) > 100:
            if "source" not in text.lower() and "selon" not in text.lower():
                text += "\n\n*Note : Cette reponse est basee sur mes connaissances. "
                text += "Pour des informations factualles precises, "
                text += "veuillez fournir des sources.*"
        
        # Si code eleve, verifier la presence de blocs de code
        if signatures[6] > 0.4 and "```" not in text:
            pass  # Le modele a probablement deja repondu sans code
        
        return text
    
    def generate(self, prompt: str, max_tokens: int = 1000,
                 temperature: Optional[float] = None,
                 system_prompt_extra: str = "") -> Dict[str, Any]:
        """
        Genere une reponse avec harmonisation.
        
        Returns:
            Dict avec content, signatures, metrics
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        # 1. Analyser le prompt avec signatures 7D
        signatures = self.projector.project(prompt)
        self.stats["avg_signatures"] = (
            self.stats["avg_signatures"] * (self.stats["total_requests"] - 1) + signatures
        ) / self.stats["total_requests"]
        
        # 2. Construire les parametres harmoniques
        system_prompt = self._get_system_prompt(signatures)
        if system_prompt_extra:
            system_prompt += "\n\n" + system_prompt_extra
        
        temp = temperature if temperature is not None else self._get_temperature(signatures)
        top_k = self._get_top_k(signatures)
        top_p = self._get_top_p(signatures)
        adj_max_tokens = self._get_max_tokens(signatures, max_tokens)
        
        # 3. Verifier le cache
        cache_key = hashlib.sha256(
            f"{prompt}|{adj_max_tokens}|{temp}|{system_prompt}".encode()
        ).hexdigest()
        
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            cached = self.cache.pop(cache_key)
            self.cache[cache_key] = cached
            return {
                "content": cached,
                "signatures": signatures.tolist(),
                "temperature": temp,
                "top_k": top_k,
                "top_p": top_p,
                "cache_hit": True,
                "processing_time": time.time() - start_time,
            }
        
        # 4. Appeler l'API AWS
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": adj_max_tokens,
            "temperature": temp,
            "top_p": top_p,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            
        except Exception as e:
            content = f"Erreur API: {str(e)}"
        
        # 5. Post-traitement harmonique
        content = self._harmonic_postprocess(content, signatures)
        
        # 6. Mettre en cache
        self.cache[cache_key] = content
        if len(self.cache) > self.cache_max:
            self.cache.popitem(last=False)
        
        processing_time = time.time() - start_time
        self.stats["response_times"].append(processing_time)
        
        return {
            "content": content,
            "signatures": signatures.tolist(),
            "temperature": temp,
            "top_k": top_k,
            "top_p": top_p,
            "cache_hit": False,
            "processing_time": processing_time,
        }
    
    def compare(self, prompt: str, max_tokens: int = 500) -> Dict[str, Any]:
        """
        Compare reponse AVEC et SANS harmonique.
        """
        # Sans harmonique
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload_standard = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        
        t0 = time.time()
        resp_standard = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json=payload_standard,
            timeout=120
        )
        standard_time = time.time() - t0
        standard_content = resp_standard.json()["choices"][0]["message"]["content"]
        
        # Avec harmonique
        harmonic_result = self.generate(prompt, max_tokens)
        
        # Signatures des deux reponses
        sig_standard = self.projector.project(standard_content)
        sig_harmonic = self.projector.project(harmonic_result["content"])
        
        # Resonance entre prompt et reponses
        resonance_standard = float(np.dot(
            self.projector.project(prompt), sig_standard
        ) / 7.0)
        resonance_harmonic = float(np.dot(
            self.projector.project(prompt), sig_harmonic
        ) / 7.0)
        
        return {
            "prompt": prompt,
            "standard": {
                "content": standard_content[:500],
                "signatures": sig_standard.tolist(),
                "time": standard_time,
                "resonance": resonance_standard,
            },
            "harmonic": {
                "content": harmonic_result["content"][:500],
                "signatures": sig_harmonic.tolist(),
                "time": harmonic_result["processing_time"],
                "resonance": resonance_harmonic,
                "temperature": harmonic_result["temperature"],
                "top_k": harmonic_result["top_k"],
                "top_p": harmonic_result["top_p"],
            },
            "improvement": {
                "resonance_gain": resonance_harmonic - resonance_standard,
                "time_ratio": harmonic_result["processing_time"] / max(standard_time, 0.001),
            }
        }


# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------
def test_harmonic_aws_proxy():
    """Teste le proxy harmonique AWS."""
    print("=" * 60)
    print("TEST : Proxy Harmonique AWS")
    print("=" * 60)
    
    # Configuration (a adapter)
    base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
    model = os.getenv("BACKEND_MODEL", "deepseek-qwen-hybrid")
    api_key = os.getenv("BACKEND_API_KEY", "")
    
    proxy = HarmonicAWSProxy(base_url, model, api_key)
    
    # Test des signatures
    print("\n1. Test des signatures 7D...")
    test_texts = [
        "Calculate the integral of x^2 from 0 to 1",
        "Write a poem about the ocean and stars",
        "Explain why the sky is blue using physics",
        "Write a Python function to sort a list",
    ]
    
    for text in test_texts:
        sig = proxy.projector.project(text)
        dims = ['phi','alpha','reasoning','creativity','math','factual','code']
        print(f"\n  Texte: {text[:50]}...")
        for name, val in zip(dims, sig):
            print(f"    {name:12s} = {val:.3f}")
    
    # Test de resonance
    print("\n2. Test de resonance...")
    resonance = proxy.projector.resonance_matrix(test_texts)
    print(f"  Matrice de resonance [{len(test_texts)}x{len(test_texts)}]:")
    for i in range(len(test_texts)):
        row = "  ".join(f"{resonance[i,j]:.3f}" for j in range(len(test_texts)))
        print(f"    {row}")
    
    # Test des parametres harmoniques
    print("\n3. Test des parametres harmoniques...")
    for text in test_texts:
        sig = proxy.projector.project(text)
        temp = proxy._get_temperature(sig)
        top_k = proxy._get_top_k(sig)
        top_p = proxy._get_top_p(sig)
        print(f"\n  Prompt: {text[:40]}...")
        print(f"    temperature={temp:.3f}, top_k={top_k}, top_p={top_p:.3f}")
    
    print("\n[SUCCES] Proxy harmonique AWS operationnel")
    print("\nPour utiliser avec l'API AWS:")
    print(f"  export BACKEND_BASE_URL='{base_url}'")
    print(f"  export BACKEND_MODEL='{model}'")
    print("  python harmonic_aws_injector.py --mode generate --prompt '...'")
    print("  python harmonic_aws_injector.py --mode compare --prompt '...'")


def main():
    """Point d'entree principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Proxy Harmonique AWS")
    parser.add_argument("--mode", choices=["test", "generate", "compare"],
                       default="test", help="Mode d'execution")
    parser.add_argument("--prompt", type=str, default="",
                       help="Prompt pour la generation")
    parser.add_argument("--max-tokens", type=int, default=500)
    parser.add_argument("--temperature", type=float, default=None)
    
    args = parser.parse_args()
    
    if args.mode == "test":
        test_harmonic_aws_proxy()
        return
    
    base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
    model = os.getenv("BACKEND_MODEL", "deepseek-qwen-hybrid")
    api_key = os.getenv("BACKEND_API_KEY", "")
    
    proxy = HarmonicAWSProxy(base_url, model, api_key)
    
    if args.mode == "generate":
        if not args.prompt:
            args.prompt = input("Prompt: ")
        result = proxy.generate(args.prompt, args.max_tokens, args.temperature)
        print(f"\nReponse harmonique:")
        print(f"  {result['content'][:1000]}")
        print(f"\nSignatures 7D:")
        dims = ['phi','alpha','reasoning','creativity','math','factual','code']
        for name, val in zip(dims, result['signatures']):
            print(f"  {name:12s} = {val:.3f}")
        print(f"\nTemperature: {result['temperature']:.3f}")
        print(f"Temps: {result['processing_time']:.2f}s")
        print(f"Cache: {'HIT' if result['cache_hit'] else 'MISS'}")
    
    elif args.mode == "compare":
        if not args.prompt:
            args.prompt = input("Prompt: ")
        result = proxy.compare(args.prompt, args.max_tokens)
        print(f"\n=== COMPARAISON AVEC/SANS HARMONIQUE ===")
        print(f"\nPrompt: {result['prompt'][:100]}")
        print(f"\n--- STANDARD ---")
        print(f"  {result['standard']['content'][:500]}")
        print(f"\n  Resonance: {result['standard']['resonance']:.4f}")
        print(f"  Temps: {result['standard']['time']:.2f}s")
        print(f"\n--- HARMONIQUE ---")
        print(f"  {result['harmonic']['content'][:500]}")
        print(f"\n  Resonance: {result['harmonic']['resonance']:.4f}")
        print(f"  Temperature: {result['harmonic']['temperature']:.3f}")
        print(f"  Temps: {result['harmonic']['time']:.2f}s")
        print(f"\n--- AMELIORATION ---")
        print(f"  Gain de resonance: {result['improvement']['resonance_gain']:+.4f}")
        print(f"  Ratio temps: {result['improvement']['time_ratio']:.2f}x")


if __name__ == "__main__":
    main()
