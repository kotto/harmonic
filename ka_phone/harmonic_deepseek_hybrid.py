#!/usr/bin/env python3
"""
HARMONIC + DEEPSEEK HYBRID — Le meilleur des deux mondes
==========================================================
Architecture :
  QUESTION -> Onde Sonde -> Hologramme ABC -> Base Vectorielle -> Top-k Faits
       |
       v
  API DEEPSEEK (deepseek-chat) <- recois UNIQUEMENT les faits + instruction stricte
       |
       v
  VERIFICATION (Couche 4) -> chaque phrase tracee aux faits source
       |
       v
  REPONSE : puissance DeepSeek + determinisme holographique

Usage :
  python harmonic_deepseek_hybrid.py --test
  python harmonic_deepseek_hybrid.py --query "Quelle est la capitale du Senegal ?"
  python harmonic_deepseek_hybrid.py --server  # Mode serveur HTTP
"""

import os, sys, json, time, re, hashlib, math
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

# Charger .env
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR.parent / ".env")
except ImportError:
    pass

PHI = (1 + math.sqrt(5)) / 2
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")

# =============================================================================
# HYBRID PIPELINE
# =============================================================================

class HarmonicDeepSeekHybrid:
    """
    Pipeline hybride complet :
    Hologramme ABC -> Retrieval vectoriel -> API DeepSeek contrainte -> Verification
    """

    def __init__(self):
        self.pipeline = None
        self.verifier = None
        self.api_available = bool(DEEPSEEK_API_KEY)
        self.stats = {
            "total_queries": 0,
            "api_calls": 0,
            "template_fallbacks": 0,
            "verified": 0,
            "rejected": 0,
            "total_time_ms": 0,
        }
        self._init_pipeline()

    def _init_pipeline(self):
        """Initialise le pipeline holographique."""
        try:
            from hologram_vector_bridge import (
                HologramVectorPipeline,
                DeterministicVerificationLayer,
            )
            self.pipeline = HologramVectorPipeline(use_llm=False)
            self.pipeline.build(force=False)
            self.verifier = DeterministicVerificationLayer()
            print("[Hybrid] Pipeline holographique initialise")
        except Exception as e:
            print(f"[Hybrid] Erreur initialisation pipeline : {e}")
            self.pipeline = None

    def _call_deepseek_api(self, system_prompt: str, user_prompt: str,
                           max_tokens: int = 500, temperature: float = 0.3) -> Optional[str]:
        """Appelle l'API DeepSeek officielle."""
        if not self.api_available:
            return None

        try:
            import requests

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            }

            payload = {
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.95,
                "stream": False,
            }

            response = requests.post(
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content.strip()
            else:
                print(f"[DeepSeek API] Erreur HTTP {response.status_code}: {response.text[:200]}")
                return None

        except Exception as e:
            print(f"[DeepSeek API] Erreur : {e}")
            return None

    def query(self, prompt: str, k: int = 15, style: str = "general",
              max_tokens: int = 500, temperature: float = 0.3) -> Dict[str, Any]:
        """
        Requete hybride complete.

        Args:
            prompt: Question en langage naturel
            k: Nombre de patches a recuperer
            style: "general", "concise", "creative", "technical"
            max_tokens: Tokens max pour la reponse DeepSeek
            temperature: Temperature (0.1-0.5 recommande)

        Returns:
            Dict avec text, verified, trace_score, source, etc.
        """
        self.stats["total_queries"] += 1
        t0 = time.time()

        # 1. Retrieval holographique
        if self.pipeline is None:
            return {
                "text": "Pipeline holographique non disponible.",
                "source": "error",
                "confidence": 0.0,
                "verified": False,
                "trace_score": 0.0,
                "temps_ms": 0,
            }

        hologram_result = self.pipeline.query(prompt, k=k, style=style)
        retrieved_facts = []

        # Reconstruire les faits a partir du resultat
        if hologram_result.get("facts_used", 0) > 0:
            # Les faits sont deja dans le pipeline, on les recupere via le mapper
            patch_indices = list(range(min(hologram_result.get("patches_used", 0), k)))
            if self.pipeline.mapper:
                retrieved_facts = self.pipeline.mapper.get_facts_for_patches(patch_indices or [])

        # 2. Ajouter ParametricKB si applicable
        parametric_result = None
        try:
            from parametric_kb_fr import ParametricKB
            pkb = ParametricKB()
            parametric_result = pkb.solve(prompt)
        except Exception:
            pass

        if parametric_result:
            if isinstance(parametric_result, dict):
                parametric_text = parametric_result.get("text", str(parametric_result))
            else:
                parametric_text = str(parametric_result)
            retrieved_facts.insert(0, {
                "id": "parametric",
                "text": parametric_text,
                "keywords": ["math"],
                "patch_index": -1,
            })

        # 3. Construire le contexte de faits
        fact_context = self._build_fact_context(retrieved_facts)

        # 4. Appel API DeepSeek (contrainte)
        llm_response = None
        if self.api_available and fact_context.strip():
            system_prompt = self._build_system_prompt(fact_context, style)
            user_prompt = f"Question : {prompt}\n\nReponds en francais en utilisant UNIQUEMENT les faits ci-dessus. N'invente rien."

            llm_response = self._call_deepseek_api(
                system_prompt, user_prompt,
                max_tokens=max_tokens, temperature=temperature
            )
            if llm_response:
                self.stats["api_calls"] += 1

        # 5. Fallback template si API echoue
        if llm_response is None:
            llm_response = self._template_assemble(retrieved_facts, prompt)
            self.stats["template_fallbacks"] += 1

        # 6. Verification deterministe
        if self.verifier:
            verification = self.verifier.verify(
                llm_response, retrieved_facts, prompt, strict_mode=False
            )
        else:
            verification = {
                "traceable": True, "score": 1.0,
                "hallucination_phrases": [], "verdict": "valid"
            }

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        self.stats["total_time_ms"] += elapsed_ms
        self.stats["verified" if verification["traceable"] else "rejected"] += 1

        return {
            "text": llm_response,
            "source": "deepseek_api" if (llm_response and self.api_available) else "template_fallback",
            "confidence": 0.90 if self.api_available else 0.75,
            "verified": verification["traceable"],
            "trace_score": verification["score"],
            "trace_verdict": verification["verdict"],
            "hallucination_phrases": verification.get("hallucination_phrases", []),
            "facts_used": len(retrieved_facts),
            "api_used": self.api_available and llm_response is not None,
            "temps_ms": elapsed_ms,
        }

    def _build_fact_context(self, facts: List[Dict], max_chars: int = 4000) -> str:
        """Construit le contexte de faits pour le system prompt."""
        lines = []
        seen = set()
        for fact in facts[:40]:
            text = fact.get("text", "")
            if text and len(text) > 3 and text not in seen:
                seen.add(text)
                lines.append(f"- {text.strip()}")
        context = "\n".join(lines)
        if len(context) > max_chars:
            context = context[:max_chars] + "\n... (faits supplementaires tronques)"
        return context

    def _build_system_prompt(self, fact_context: str, style: str) -> str:
        """Construit le system prompt contraignant pour DeepSeek."""
        style_instructions = {
            "general": "Sois clair, precis et concis.",
            "concise": "Repons en 2-3 phrases maximum.",
            "creative": "Utilise un style elegant et poetique tout en restant factuel.",
            "technical": "Sois technique et detaille, utilise la terminologie appropriee.",
        }

        return f"""Tu es KA, un assistant dont TOUTE la connaissance provient d'un hologramme d'ondes universelles.

REGLE ABSOLUE (la plus importante) :
Tu dois repondre EXCLUSIVEMENT en utilisant les faits fournis ci-dessous.
Tu n'as PAS le droit d'inventer quoi que ce soit - pas de dates, pas de noms, pas de details.
Si l'information demandee n'est pas dans les faits, dis exactement :
"L'hologramme ne contient pas cette information."

{style_instructions.get(style, style_instructions['general'])}

FAITS DE L'HOLOGRAMME (SEULE source autorisee - tout le reste est interdit) :
{fact_context}

IMPORTANT : Ta reponse sera verifiee phrase par phrase. Toute phrase contenant
une information absente des faits ci-dessus sera rejetee automatiquement."""

    def _template_assemble(self, facts: List[Dict], query: str) -> str:
        """Assemblage template (fallback sans API)."""
        fact_texts = []
        for f in facts[:5]:
            text = f.get("text", "")
            if text and len(text) > 3:
                fact_texts.append(text.strip())

        if not fact_texts:
            return "L'hologramme ne contient pas d'information suffisante."
        elif len(fact_texts) == 1:
            return f"D'apres l'hologramme : {fact_texts[0]}"
        else:
            return "D'apres l'hologramme :\n" + "\n".join(f"- {t}" for t in fact_texts)

    def get_stats(self) -> Dict:
        avg_time = self.stats["total_time_ms"] / max(self.stats["total_queries"], 1)
        return {
            **self.stats,
            "avg_time_ms": round(avg_time, 1),
            "api_available": self.api_available,
            "model": DEEPSEEK_MODEL,
        }


# =============================================================================
# SERVEUR HTTP
# =============================================================================

def run_server(port: int = 8421):
    """Demarre un serveur HTTP pour l'API hybride."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    hybrid = HarmonicDeepSeekHybrid()

    class HybridHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/api/query":
                self.send_error(404)
                return

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                prompt = data.get("prompt", data.get("question", ""))
                style = data.get("style", "general")
                max_tokens = data.get("max_tokens", 500)
                temperature = data.get("temperature", 0.3)
            except Exception:
                self.send_error(400, "JSON invalide")
                return

            result = hybrid.query(prompt, style=style, max_tokens=max_tokens, temperature=temperature)
            self._send_json(result)

        def do_GET(self):
            if self.path == "/health":
                self._send_json({
                    "status": "ok",
                    "version": "hybrid-1.0",
                    "api_available": hybrid.api_available,
                    "model": DEEPSEEK_MODEL,
                    "stats": hybrid.get_stats(),
                })
            elif self.path == "/stats":
                self._send_json(hybrid.get_stats())
            else:
                self.send_error(404)

        def _send_json(self, data):
            response = json.dumps(data, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))

        def log_message(self, format, *args):
            pass  # Silencieux

    server = HTTPServer(("0.0.0.0", port), HybridHandler)
    print(f"\n[Harmonic+DeepSeek Hybrid] Serveur demarre sur http://localhost:{port}")
    print(f"  DeepSeek API : {'[CONNECTE]' if hybrid.api_available else '[NON CONFIGURE]'}")
    print(f"  Modele : {DEEPSEEK_MODEL}")
    print(f"  Health : http://localhost:{port}/health")
    print(f"  Stats  : http://localhost:{port}/stats")
    print(f"  Query  : POST http://localhost:{port}/api/query")
    print(f"\nAppuyez sur Ctrl+C pour arreter.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArret du serveur.")
        server.shutdown()


# =============================================================================
# TESTS
# =============================================================================

def run_tests():
    """Tests de validation du pipeline hybride."""
    print("=" * 60)
    print("  TESTS - HARMONIC + DEEPSEEK HYBRID")
    print("=" * 60)

    hybrid = HarmonicDeepSeekHybrid()

    test_questions = [
        ("Quelle est la capitale du Senegal ?", "general"),
        ("Combien font 12 x 15 ?", "concise"),
        ("Quelle est la racine carree de 144 ?", "concise"),
        ("Qu'est-ce que la gravite ?", "general"),
        ("Parle-moi de l'empire du Mali", "creative"),
        ("Qui etait Napoleon ?", "general"),
        ("Comment calculer l'aire d'un cercle de rayon 5 ?", "technical"),
    ]

    print(f"\n  DeepSeek API : {'[CONNECTE]' if hybrid.api_available else '[NON CONFIGURE]'}")
    print(f"  Modele : {DEEPSEEK_MODEL}")
    print(f"\n{'='*60}")
    print(f"  {len(test_questions)} QUESTIONS DE TEST")
    print(f"{'='*60}")

    results = []
    for q, style in test_questions:
        result = hybrid.query(q, k=15, style=style, max_tokens=300, temperature=0.3)
        results.append(result)

        status = "OK" if result.get("verified", False) else "!!"
        api_flag = "[API]" if result.get("api_used") else "[TPL]"
        if result.get("trace_score", 0) >= 0.8:
            trace_level = "HIGH"
        elif result.get("trace_score", 0) >= 0.5:
            trace_level = "MED "
        else:
            trace_level = "LOW "

        print(f"\n  [{status}] {api_flag} Q: {q[:70]}")
        print(f"    R: {result.get('text', 'N/A')[:150]}...")
        print(f"    [{trace_level}] Traceability: {result.get('trace_score', 0):.0%} "
              f"| Facts: {result.get('facts_used', 0)} | {result.get('temps_ms', 0)}ms")

    # Stats globales
    verified = sum(1 for r in results if r.get("verified"))
    api_used = sum(1 for r in results if r.get("api_used"))
    avg_trace = sum(r.get("trace_score", 0) for r in results) / max(len(results), 1)
    avg_time = sum(r.get("temps_ms", 0) for r in results) / max(len(results), 1)

    print(f"\n{'='*60}")
    print(f"  RESUME")
    print(f"{'='*60}")
    print(f"  Questions : {len(results)}")
    print(f"  Verifiees : {verified}/{len(results)} ({verified/len(results)*100:.0f}%)")
    print(f"  Via API DeepSeek : {api_used}/{len(results)}")
    print(f"  Tracabilite moyenne : {avg_trace:.0%}")
    print(f"  Temps moyen : {avg_time:.0f}ms")

    stats = hybrid.get_stats()
    print(f"\n  Stats globales :")
    print(f"    Total queries : {stats['total_queries']}")
    print(f"    API calls : {stats['api_calls']}")
    print(f"    Template fallbacks : {stats['template_fallbacks']}")
    print(f"    Verified : {stats['verified']}")
    print(f"    Rejected : {stats['rejected']}")
    print(f"    Avg time : {stats['avg_time_ms']}ms")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Harmonic + DeepSeek Hybrid")
    parser.add_argument("--query", type=str, default=None, help="Requete a executer")
    parser.add_argument("--test", action="store_true", help="Lancer les tests")
    parser.add_argument("--server", action="store_true", help="Mode serveur HTTP")
    parser.add_argument("--port", type=int, default=8421, help="Port du serveur")
    parser.add_argument("--style", type=str, default="general",
                        choices=["general", "concise", "creative", "technical"])
    parser.add_argument("--k", type=int, default=15, help="Nombre de patches a recuperer")
    parser.add_argument("--temperature", type=float, default=0.3,
                        help="Temperature pour DeepSeek (0.1-0.5 recommande)")

    args = parser.parse_args()

    if args.server:
        run_server(port=args.port)
        return

    if args.test:
        run_tests()
        return

    if args.query:
        hybrid = HarmonicDeepSeekHybrid()
        result = hybrid.query(
            args.query, k=args.k, style=args.style,
            max_tokens=500, temperature=args.temperature
        )
        print(f"\n{'='*60}")
        print(f"  REPONSE HYBRIDE")
        print(f"{'='*60}")
        print(f"\n{result['text']}")
        print(f"\n  Source : {result['source']}")
        print(f"  Tracabilite : {result.get('trace_score', 0):.0%} ({result.get('trace_verdict', 'N/A')})")
        print(f"  Faits utilises : {result.get('facts_used', 0)}")
        print(f"  Temps : {result.get('temps_ms', 0)}ms")
        if result.get("hallucination_phrases"):
            print(f"\n  [!] Phrases non tracees :")
            for p in result["hallucination_phrases"]:
                print(f"    - {p}")
        return

    # Mode interactif
    print("=" * 60)
    print("  HARMONIC + DEEPSEEK HYBRID")
    print("  Mode interactif")
    print("=" * 60)
    print(f"\n  DeepSeek API : {'[CONNECTE]' if DEEPSEEK_API_KEY else '[NON CONFIGURE]'}")
    print(f"  Modele : {DEEPSEEK_MODEL}")
    print("\nCommandes :")
    print("  python harmonic_deepseek_hybrid.py --test")
    print("  python harmonic_deepseek_hybrid.py --query \"...\"")
    print("  python harmonic_deepseek_hybrid.py --server --port 8421")


if __name__ == "__main__":
    main()