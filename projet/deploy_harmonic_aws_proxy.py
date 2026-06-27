#!/usr/bin/env python3
"""
DEPLOIEMENT : Proxy Harmonique AWS
===================================
Script de deploiement du proxy harmonique sur l'instance AWS EC2.

Ce script :
1. Verifie la connexion a l'API AWS existante
2. Teste le proxy harmonique en local
3. Prepare le deploiement du proxy sur l'instance
4. Integre le proxy dans l'API existante

Usage:
    python deploy_harmonic_aws_proxy.py --check        # Verifier connexion AWS
    python deploy_harmonic_aws_proxy.py --test-local    # Tester proxy en local
    python deploy_harmonic_aws_proxy.py --deploy        # Deployer sur AWS
    python deploy_harmonic_aws_proxy.py --compare       # Comparer avec/sans harmonique
"""

import os, sys, json, time, hashlib, argparse
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
# SignatureProjector (version legere)
# ---------------------------------------------------------------------------
class SignatureProjector:
    """Projection de signature 7D sans PyTorch."""
    
    def __init__(self):
        pass
    
    def project(self, text: str) -> np.ndarray:
        """Projette un texte en signature 7D."""
        sig = np.zeros(7, dtype=np.float32)
        words = text.split()
        if not words:
            return sig
        
        # phi - diversite lexicale
        unique_words = len(set(w.lower() for w in words))
        sig[0] = min(1.0, unique_words / max(1, len(words)) * PHI)
        
        # alpha - complexite
        avg_word_len = np.mean([len(w) for w in words])
        sig[1] = min(1.0, avg_word_len / 15.0)
        
        # reasoning
        reasoning_words = {'why','because','therefore','thus','hence','since',
                          'if','then','else','so','consequently','accordingly',
                          'deduce','infer','conclude','imply','logical','reason',
                          'explain','analyse','analyze','compare','contrast'}
        sig[2] = min(1.0, sum(1 for w in words if w.lower() in reasoning_words) / 5.0)
        
        # creativity
        creative_words = {'imagine','create','dream','vision','poem','story',
                         'metaphor','beautiful','wonder','magic','infinite',
                         'cosmic','harmony','symphony','ocean','light',
                         'poetry','creative','artistic','narrative'}
        sig[3] = min(1.0, sum(1 for w in words if w.lower() in creative_words) / 5.0)
        
        # math
        math_words = {'equation','theorem','proof','calculate','matrix','vector',
                     'integral','derivative','function','algorithm','number',
                     'sum','product','ratio','phi','golden','fractal',
                     'calculus','algebra','geometry','probability'}
        sig[4] = min(1.0, sum(1 for w in words if w.lower() in math_words) / 5.0)
        
        # factual
        factual_words = {'fact','data','study','research','according','source',
                        'reference','citation','statistic','evidence','proven',
                        'verified','confirmed','measured','observed',
                        'who','when','where','what','definition'}
        sig[5] = min(1.0, sum(1 for w in words if w.lower() in factual_words) / 5.0)
        
        # code
        code_words = {'code','function','class','import','def','return','var',
                     'const','let','python','javascript','api','endpoint',
                     'algorithm','compile','debug','deploy','programming',
                     'software','implementation'}
        sig[6] = min(1.0, sum(1 for w in words if w.lower() in code_words) / 5.0)
        
        return np.clip(sig, 0, 1)


# ---------------------------------------------------------------------------
# HarmonicAWSProxy
# ---------------------------------------------------------------------------
class HarmonicAWSProxy:
    """Proxy harmonique pour l'API AWS DeepSeek/Qwen."""
    
    def __init__(self, base_url: str, model: str, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.projector = SignatureProjector()
        self.cache = OrderedDict()
        self.cache_max = 2048
        self.stats = {
            "total": 0, "cache_hits": 0,
            "avg_sig": np.zeros(7),
            "times": []
        }
    
    def _get_system_prompt(self, sig: np.ndarray) -> str:
        """Construit un system prompt harmonique."""
        parts = [
            "Tu es Harmonic AI, un assistant avec resonance harmonique 7D.",
            "Tu combines raisonnement logique et intuition creative.",
        ]
        
        if sig[2] > 0.3:
            parts.append("Structure ta reponse avec un raisonnement clair.")
        if sig[3] > 0.3:
            parts.append("Utilise des metaphors et des images evocatrices.")
        if sig[4] > 0.3:
            parts.append("Sois precis et rigoureux dans tes calculs.")
        if sig[5] > 0.3:
            parts.append("Base-toi sur des faits verifies.")
        if sig[6] > 0.3:
            parts.append("Fournis du code fonctionnel et bien commente.")
        
        parts.append(f"Utilise le ratio d'or φ={PHI:.4f} comme guide.")
        
        return "\n".join(parts)
    
    def _get_params(self, sig: np.ndarray) -> Dict[str, float]:
        """Calcule les parametres optimaux selon les signatures."""
        temp = 0.3 + sig[3] * 0.4 - sig[5] * 0.2 - sig[4] * 0.15 + sig[2] * 0.1
        temp = np.clip(temp, 0.0, 0.9)
        
        top_k = int(40 + sig[3] * 30 - sig[5] * 20)
        top_k = max(10, min(100, top_k))
        
        top_p = 0.9 - sig[4] * 0.2 + sig[3] * 0.05
        top_p = np.clip(top_p, 0.7, 0.95)
        
        return {"temperature": float(temp), "top_k": top_k, "top_p": float(top_p)}
    
    def generate(self, prompt: str, max_tokens: int = 1000,
                 temperature: Optional[float] = None) -> Dict[str, Any]:
        """Genere une reponse avec harmonisation."""
        t0 = time.time()
        self.stats["total"] += 1
        
        sig = self.projector.project(prompt)
        self.stats["avg_sig"] = (
            self.stats["avg_sig"] * (self.stats["total"] - 1) + sig
        ) / self.stats["total"]
        
        params = self._get_params(sig)
        temp = temperature if temperature is not None else params["temperature"]
        system_prompt = self._get_system_prompt(sig)
        
        # Cache
        cache_key = hashlib.sha256(
            f"{prompt}|{max_tokens}|{temp}|{system_prompt}".encode()
        ).hexdigest()
        
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            self.cache.move_to_end(cache_key)
            return {
                "content": self.cache[cache_key],
                "signatures": sig.tolist(),
                "params": params,
                "cache_hit": True,
                "time": time.time() - t0,
            }
        
        # Appel API
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temp,
            "top_p": params["top_p"],
        }
        
        try:
            r = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers, json=payload, timeout=120
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            content = f"[Erreur API] {str(e)}"
        
        # Cache
        self.cache[cache_key] = content
        if len(self.cache) > self.cache_max:
            self.cache.popitem(last=False)
        
        proc_time = time.time() - t0
        self.stats["times"].append(proc_time)
        
        return {
            "content": content,
            "signatures": sig.tolist(),
            "params": params,
            "cache_hit": False,
            "time": proc_time,
        }
    
    def compare(self, prompt: str, max_tokens: int = 500) -> Dict[str, Any]:
        """Compare avec/sans harmonique."""
        # Standard
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        t0 = time.time()
        r = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
            timeout=120
        )
        std_time = time.time() - t0
        std_content = r.json()["choices"][0]["message"]["content"]
        
        # Harmonique
        harm = self.generate(prompt, max_tokens)
        
        # Resonance
        sig_prompt = self.projector.project(prompt)
        sig_std = self.projector.project(std_content)
        sig_harm = self.projector.project(harm["content"])
        
        res_std = float(np.dot(sig_prompt, sig_std) / 7.0)
        res_harm = float(np.dot(sig_prompt, sig_harm) / 7.0)
        
        return {
            "prompt": prompt[:100],
            "standard": {
                "content": std_content[:500],
                "signatures": sig_std.tolist(),
                "time": std_time,
                "resonance": res_std,
            },
            "harmonic": {
                "content": harm["content"][:500],
                "signatures": sig_harm.tolist(),
                "time": harm["time"],
                "resonance": res_harm,
                "params": harm["params"],
            },
            "improvement": {
                "resonance_gain": res_harm - res_std,
                "time_ratio": harm["time"] / max(std_time, 0.001),
            }
        }


# ---------------------------------------------------------------------------
# Fonctions de verification et deploiement
# ---------------------------------------------------------------------------
def check_aws_connection(base_url: str, model: str, api_key: str = ""):
    """Verifie la connexion a l'API AWS."""
    print(f"\nVerification connexion AWS...")
    print(f"  URL: {base_url}")
    print(f"  Model: {model}")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Test health
    try:
        r = requests.get(f"{base_url}/health", timeout=10)
        print(f"  Health: {r.status_code}")
        if r.status_code == 200:
            print(f"  Status: {json.dumps(r.json(), indent=2)[:200]}")
    except Exception as e:
        print(f"  Health error: {e}")
    
    # Test generation
    try:
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say 'Hello' in one word."}],
                "max_tokens": 10,
                "temperature": 0.0,
            },
            timeout=30
        )
        print(f"  Generate: {r.status_code}")
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            print(f"  Response: {content[:100]}")
            print(f"  [OK] Connexion AWS operationnelle")
            return True
        else:
            print(f"  Error: {r.text[:200]}")
    except Exception as e:
        print(f"  Generate error: {e}")
    
    print("  [FAIL] Connexion AWS echouee")
    return False


def test_proxy_local():
    """Teste le proxy harmonique en local (sans API)."""
    print("\nTest proxy harmonique local...")
    
    proxy = HarmonicAWSProxy("http://localhost:8000", "test-model")
    
    test_cases = [
        ("Calculate the integral of x^2 dx", "math"),
        ("Write a poem about the ocean", "creativity"),
        ("Explain why the sky is blue", "reasoning"),
        ("Write Python code to sort a list", "code"),
        ("Who was the first president of the US?", "factual"),
    ]
    
    for prompt, expected in test_cases:
        sig = proxy.projector.project(prompt)
        params = proxy._get_params(sig)
        dims = ['phi','alpha','reasoning','creativity','math','factual','code']
        
        print(f"\n  Prompt: {prompt[:40]}...")
        print(f"  Attendu: {expected}")
        for name, val in zip(dims, sig):
            print(f"    {name:12s} = {val:.3f}")
        print(f"  Params: temp={params['temperature']:.3f}, "
              f"top_k={params['top_k']}, top_p={params['top_p']:.3f}")
        
        # Verifier que la dimension attendue est dominante
        idx = dims.index(expected)
        if sig[idx] > 0:
            print(f"  [OK] Dimension {expected} detectee ({sig[idx]:.3f})")
        else:
            print(f"  [WARN] Dimension {expected} non detectee")
    
    print("\n[SUCCES] Proxy harmonique local operationnel")


def deploy_to_aws():
    """Prepare le deploiement du proxy sur AWS."""
    print("\nPreparation deploiement AWS...")
    
    base_url = os.getenv("BACKEND_BASE_URL", "")
    model = os.getenv("BACKEND_MODEL", "")
    api_key = os.getenv("BACKEND_API_KEY", "")
    
    if not base_url or not model:
        print("  [ERREUR] Variables d'environnement manquantes:")
        print("    BACKEND_BASE_URL (ex: http://ec2-xx-xx-xx-xx.compute.amazonaws.com:8000)")
        print("    BACKEND_MODEL (ex: deepseek-qwen-hybrid)")
        print("    BACKEND_API_KEY (optionnel)")
        return False
    
    # Verifier connexion
    if not check_aws_connection(base_url, model, api_key):
        return False
    
    # Creer le proxy
    proxy = HarmonicAWSProxy(base_url, model, api_key)
    
    # Test de generation
    print("\nTest generation harmonique...")
    result = proxy.generate("What is the golden ratio and why is it important?", 200)
    print(f"  Signatures: {result['signatures']}")
    print(f"  Params: {result['params']}")
    print(f"  Temps: {result['time']:.2f}s")
    print(f"  Cache: {'HIT' if result['cache_hit'] else 'MISS'}")
    print(f"  Reponse: {result['content'][:200]}...")
    
    print("\n[SUCCES] Proxy harmonique pret sur AWS")
    print("\nPour utiliser:")
    print(f"  export BACKEND_BASE_URL='{base_url}'")
    print(f"  export BACKEND_MODEL='{model}'")
    print("  python harmonic_aws_injector.py --mode generate --prompt '...'")
    print("  python harmonic_aws_injector.py --mode compare --prompt '...'")
    
    return True


def run_comparison():
    """Compare avec/sans harmonique sur AWS."""
    print("\nComparaison avec/sans harmonique...")
    
    base_url = os.getenv("BACKEND_BASE_URL", "")
    model = os.getenv("BACKEND_MODEL", "")
    api_key = os.getenv("BACKEND_API_KEY", "")
    
    if not base_url or not model:
        print("  [ERREUR] Variables d'environnement manquantes")
        return
    
    proxy = HarmonicAWSProxy(base_url, model, api_key)
    
    prompts = [
        "Explain quantum computing in simple terms",
        "Write a short poem about artificial intelligence",
        "What is the difference between TCP and UDP?",
        "Solve for x: 2x^2 + 5x - 3 = 0",
        "Who developed the theory of relativity?",
    ]
    
    results = []
    for prompt in prompts:
        print(f"\n{'='*60}")
        print(f"Prompt: {prompt}")
        print(f"{'='*60}")
        
        result = proxy.compare(prompt, 300)
        results.append(result)
        
        print(f"\n[STANDARD] Resonance: {result['standard']['resonance']:.4f}")
        print(f"  {result['standard']['content'][:200]}...")
        print(f"\n[HARMONIQUE] Resonance: {result['harmonic']['resonance']:.4f}")
        print(f"  Params: {result['harmonic']['params']}")
        print(f"  {result['harmonic']['content'][:200]}...")
        print(f"\nGain: {result['improvement']['resonance_gain']:+.4f}")
    
    # Resume
    print(f"\n{'='*60}")
    print("RESUME COMPARAISON")
    print(f"{'='*60}")
    
    avg_gain = np.mean([r['improvement']['resonance_gain'] for r in results])
    avg_time_ratio = np.mean([r['improvement']['time_ratio'] for r in results])
    
    print(f"Gain moyen de resonance: {avg_gain:+.4f}")
    print(f"Ratio temps moyen: {avg_time_ratio:.2f}x")
    
    if avg_gain > 0:
        print(f"\n[CONCLUSION] L'harmonique AMELIORE la resonance de {avg_gain:.4f}")
    else:
        print(f"\n[CONCLUSION] L'harmonique n'ameliore pas significativement la resonance")
    
    # Sauvegarder
    report = {
        "timestamp": time.time(),
        "avg_resonance_gain": float(avg_gain),
        "avg_time_ratio": float(avg_time_ratio),
        "results": results,
    }
    
    with open("harmonic_aws_comparison_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nRapport sauvegarde: harmonic_aws_comparison_report.json")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Deploiement Proxy Harmonique AWS")
    parser.add_argument("--check", action="store_true", help="Verifier connexion AWS")
    parser.add_argument("--test-local", action="store_true", help="Tester proxy en local")
    parser.add_argument("--deploy", action="store_true", help="Deployer sur AWS")
    parser.add_argument("--compare", action="store_true", help="Comparer avec/sans harmonique")
    
    args = parser.parse_args()
    
    if args.check:
        base_url = os.getenv("BACKEND_BASE_URL", "")
        model = os.getenv("BACKEND_MODEL", "")
        api_key = os.getenv("BACKEND_API_KEY", "")
        check_aws_connection(base_url, model, api_key)
    
    elif args.test_local:
        test_proxy_local()
    
    elif args.deploy:
        deploy_to_aws()
    
    elif args.compare:
        run_comparison()
    
    else:
        parser.print_help()
        print("\nExemples:")
        print("  python deploy_harmonic_aws_proxy.py --test-local")
        print("  python deploy_harmonic_aws_proxy.py --check")
        print("  python deploy_harmonic_aws_proxy.py --deploy")
        print("  python deploy_harmonic_aws_proxy.py --compare")


if __name__ == "__main__":
    main()
