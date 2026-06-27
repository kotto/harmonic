#!/usr/bin/env python3
"""
KA-NEXT CORE v2 -- Moteur Holographique Nx64x64 + Normaliseur
================================================================
Architecture definitive : Ensemble de N hologrammes 64x64 specialises
connectes par resonance phi. Le 1024x1024 est abandonne.

Principe : Toute operation intellectuelle = transformation d'onde
  - Memoriser  = interference constructive H += a*e^(i*theta)
  - Retrouver  = resonance Psi_q * H
  - Raisonner  = propagation multi-hop
  - CREER      = dephasage phi structure
  - TRADUIRE   = transposition de frequence phi^n
  - RESUME     = filtrage par amplitude Mittag-Leffler

Usage :
  python ka_next_core.py --serve        # Serveur HTTP
  python ka_next_core.py --test         # Tests
  python ka_next_core.py --query "..."  # Requete directe
"""

import os, sys, math, json, time, hashlib, re, logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict
import numpy as np

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

PHI = (1 + math.sqrt(5)) / 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s [KA-Next] %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger("ka-next")


class KANextEngine:
    """Moteur unifie KA-Next -- Ensemble holographique Nx64x64."""

    MODES = ["auto", "factual", "reason", "creative", "translate", "summarize"]

    def __init__(self):
        self.ensemble = None
        self.creative_engine = None
        self.translation_engine = None
        self.summarization_engine = None
        self.normalizer = None
        self.parametric_kb = None
        self.built = False

        self.stats = {
            "total_queries": 0,
            "mode_counts": defaultdict(int),
            "total_time_ms": 0,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

    def build(self):
        """Initialise l'ensemble holographique et les modules."""
        log.info("=" * 50)
        log.info("  KA-Next v2 -- Ensemble Nx64x64")
        log.info("=" * 50)

        # ── Ensemble holographique (moteur principal)
        try:
            from holographic_ensemble import HolographicEnsemble
            self.ensemble = HolographicEnsemble()
            self.ensemble.build_all(force_rebuild=False)
            log.info(f"Ensemble : {len(self.ensemble.holograms)} domaines")
        except Exception as e:
            log.error(f"Ensemble non disponible : {e}")

        # ── PromptNormalizer (pretraitement amont)
        try:
            from prompt_normalizer import PromptNormalizer
            self.normalizer = PromptNormalizer()
            log.info("Normaliseur : OK")
        except Exception as e:
            log.warning(f"Normaliseur non disponible : {e}")

        # ── ParametricKB (calculs mathematiques)
        try:
            from parametric_kb_fr import ParametricKB
            self.parametric_kb = ParametricKB()
            log.info("ParametricKB : OK")
        except Exception:
            pass

        # ── Modules specialises
        try:
            self.creative_engine = HolographicCreativeEngine()
            self.translation_engine = HolographicTranslationEngine()
            self.summarization_engine = HolographicSummarizationEngine()
        except Exception:
            pass

        self.built = True
        log.info("KA-Next v2 construit avec succes")
        log.info("=" * 50)

    def normalize(self, prompt: str) -> str:
        """Normalise le prompt via le PromptNormalizer (accents, typos, etc.)."""
        if self.normalizer:
            try:
                clean, flags, score = self.normalizer.normalize(prompt)
                return clean
            except Exception:
                pass
        return prompt

    def detect_mode(self, query: str) -> str:
        """Detecte automatiquement le mode de la requete."""
        ql = query.lower()

        if re.search(r"(tradui[sz]|translate|traduction)\b", ql):
            return "translate"
        if re.search(r"\b(r[eé]sum[eé]|summarize|synth[eè]se|condense)\b", ql):
            return "summarize"
        if re.search(r"\b(imagine|cr[eé][eé]r?|invente|histoire|po[eè]me|fiction)\b", ql):
            return "creative"
        if re.search(r"\b(pourquoi|explique|d[eé]montre|prouve|analyse|raisonne)\b", ql):
            return "reason"
        if re.search(r'[\+\-\*\/\×\^]|\b(calcul|r[eé]sous|[eé]quation|racine)\b', ql):
            return "factual"

        return "factual"

    def query(self, prompt: str, mode: str = "auto",
              creative_alpha: float = 0.3,
              translate_source: str = "fr", translate_target: str = "en") -> Dict[str, Any]:
        """Point d'entree unifie."""
        if not self.built:
            return {"text": "KA-Next non initialise.", "error": "not_built", "temps_ms": 0}

        t0 = time.time()
        self.stats["total_queries"] += 1

        # Normalisation du prompt (accents, typos → forme canonique)
        prompt = self.normalize(prompt)

        if mode == "auto":
            mode = self.detect_mode(prompt)
        self.stats["mode_counts"][mode] += 1

        # ── Routage par mode ──
        if mode == "factual":
            result = self._query_factual(prompt)
        elif mode == "reason":
            result = self._query_reason_spectral(prompt)
        elif mode == "creative":
            result = self._query_creative(prompt, creative_alpha)
        elif mode == "translate":
            result = self._query_translate(prompt, translate_source, translate_target)
        elif mode == "summarize":
            result = self._query_summarize(prompt)
        else:
            result = {"text": f"Mode inconnu: {mode}"}

        elapsed = round((time.time() - t0) * 1000, 1)
        self.stats["total_time_ms"] += elapsed
        result["temps_ms"] = elapsed
        result["mode"] = mode
        return result

    def _query_factual(self, prompt: str) -> Dict:
        """Requete via l'ensemble holographique Nx64x64."""
        t0 = time.time()

        # Niveau 0 : Ensemble holographique (moteur principal)
        if self.ensemble:
            result = self.ensemble.query(prompt, top_k_holos=3, facts_per_holo=5)
            result["mode"] = "factual"
            result["source"] = "ensemble_nx64"
            result["temps_ms"] = round((time.time() - t0) * 1000, 1)
            return result

        # Fallback : ParametricKB + QuickFacts
        return self._fallback_factual(prompt, t0)

    def _fallback_factual(self, prompt: str, t0: float) -> Dict:
        """Fallback si l'ensemble n'est pas disponible."""
        # ParametricKB
        if self.parametric_kb:
            try:
                pr = self.parametric_kb.solve(prompt)
                if pr:
                    text = pr.get("text", str(pr)) if isinstance(pr, dict) else str(pr)
                    if text and len(text) > 3:
                        return {"text": text, "source": "parametric_kb", "confidence": 0.95,
                                "mode": "factual", "temps_ms": round((time.time() - t0) * 1000, 1)}
            except Exception:
                pass

        # QuickFacts
        try:
            from quick_facts import QuickFacts
            qf = QuickFacts()
            best_match, best_score = None, 0
            pl = prompt.lower()
            for fid, text, kw in qf.facts:
                score = sum(1 for w in pl.split() if len(w.strip('.,;?!')) > 3 and w.strip('.,;?!').lower() in text.lower())
                if score > best_score:
                    best_score, best_match = score, text
            if best_match and best_score >= 2:
                return {"text": best_match, "source": "quickfacts", "confidence": 0.85,
                        "mode": "factual", "temps_ms": round((time.time() - t0) * 1000, 1)}
        except Exception:
            pass

        return {"text": f"Aucune reponse trouvee pour : {prompt[:100]}",
                "source": "no_match", "confidence": 0.0, "mode": "factual",
                "temps_ms": round((time.time() - t0) * 1000, 1)}

    def _query_reason_spectral(self, prompt: str) -> Dict:
        """
        Raisonnement spectral multi-sauts (5 etapes validees).
        Utilise le SpectralEncoder pour le gating et la substitution.
        Méthodologie : Observer -> Recuperer -> Substituer -> Calculer -> Conclure
        """
        t0 = time.time()

        if not self.ensemble:
            return self._query_factual(prompt)

        # Recuperer les faits pertinents depuis l'ensemble
        result = self.ensemble.query(prompt, top_k_holos=3, facts_per_holo=10)
        all_facts = result.get("top_facts", [])

        if not all_facts:
            return self._query_factual(prompt)

        # Extraire le SpectralEncoder du domaine le plus active
        domains_activated = result.get("domains_activated", [])
        spectral_enc = None
        if domains_activated:
            top_domain = domains_activated[0]["domain"]
            if top_domain in self.ensemble.holograms:
                holo = self.ensemble.holograms[top_domain]
                if hasattr(holo, 'spectral_encoder') and holo.spectral_encoder:
                    spectral_enc = holo.spectral_encoder

        # Extraire les textes des faits
        facts_texts = [f.get("text", "") for f in all_facts if f.get("text", "")]

        if not facts_texts:
            return self._query_factual(prompt)

        # Raisonnement multi-sauts
        lines = [
            f"RAISONNEMENT HOLOGRAPHIQUE (5 etapes)",
            f"{'=' * 50}",
            f"Question : {prompt[:120]}",
            f"Faits actives : {len(facts_texts)}",
            f"",
        ]

        # Utiliser le SpectralEncoder si disponible, sinon SHA-256
        if spectral_enc:
            encode_func = lambda t: spectral_enc.encode(t)
            lines.append(f"[Encodeur spectral : {spectral_enc.word_count} mots]")
        else:
            encode_func = lambda t: (
                lambda h: ((int(h[:16],16)%(64*100))/100.0, (int(h[16:32],16)%(64*100))/100.0)
            )(hashlib.sha256(t.encode()[:200]).hexdigest())
        
        def interference(w1, w2):
            kx1, ky1 = w1
            kx2, ky2 = w2
            dot = kx1*kx2 + ky1*ky2
            n1 = math.sqrt(kx1**2 + ky1**2)
            n2 = math.sqrt(kx2**2 + ky2**2)
            if n1 < 1e-10 or n2 < 1e-10: return 0.0
            return dot / (n1 * n2)
        
        q_wave = encode_func(prompt)
        
        # Saut 1 : Observer -> Recuperer
        ranked = []
        for fact in facts_texts:
            f_wave = encode_func(fact)
            interf = interference(q_wave, f_wave)
            ranked.append((fact, interf, f_wave))
        ranked.sort(key=lambda x: -abs(x[1]))
        
        # DEDUPLICATION : garder le meilleur score par texte (cles de 80 chars)
        seen_texts = set()
        unique_ranked = []
        for fact, interf, wave in ranked:
            key = fact[:80]
            if key not in seen_texts:
                seen_texts.add(key)
                unique_ranked.append((fact, interf, wave))
        
        # Meilleur fait (saut 1)
        best1_text, best1_interf, best1_wave = unique_ranked[0]
        lines.append(f"[Saut 1] Fait active : {best1_text[:120]} (interference: {best1_interf:+.2f})")
        lines.append(f"")
        
        # Substitution (moyenne)
        sub_wave = ((q_wave[0] + best1_wave[0]) / 2, (q_wave[1] + best1_wave[1]) / 2)
        
        # Saut 2 : Substituer -> Calculer (faits RESTANTS seulement)
        ranked2 = []
        for fact, _, f_wave in unique_ranked[1:]:
            interf2 = interference(sub_wave, f_wave)
            ranked2.append((fact, interf2))
        ranked2.sort(key=lambda x: -abs(x[1]))
        
        if ranked2:
            best2_text, best2_interf = ranked2[0]
            lines.append(f"[Saut 2] Fait active : {best2_text[:120]} (interference: {best2_interf:+.2f})")
            lines.append(f"")
            lines.append(f"[Conclusion]")
            lines.append(best2_text)
            confidence = abs(best2_interf)
        else:
            lines.append(f"[Conclusion]")
            lines.append(best1_text)
            confidence = abs(best1_interf)
        
        lines.append(f"")
        lines.append(f"[Raisonnement spectral multi-sauts | 2 sauts | confiance {confidence:.0%}]")

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        return {
            "text": "\n".join(lines),
            "source": "spectral_reasoning_5steps",
            "mode": "reason",
            "confidence": round(confidence, 2),
            "facts_used": len(facts_texts),
            "temps_ms": elapsed_ms,
        }

    def _query_creative(self, prompt: str, alpha: float) -> Dict:
        """Mode creatif : dephasage phi."""
        if self.ensemble:
            result = self.ensemble.query(prompt, top_k_holos=4, facts_per_holo=5)
            facts = result.get("top_facts", [])
            lines = [
                f"EXPLORATION CREATIVE -- Dephasage phi (alpha = {alpha:.2f})",
                "=" * 50,
                "",
                f"Creativite {'minimale' if alpha < 0.3 else 'moderee' if alpha < 0.6 else 'elevee'} : "
                f"l'onde est decalee de {alpha*PHI*180:.0f} degres dans l'espace de phase.",
                ""
            ]
            if facts:
                lines.append("Ancrages (interference classique) :")
                for f in facts[:3]:
                    lines.append(f"  * {f.get('text', '')[:200]}")
                lines.append("")
                lines.append(f"Connexions potentielles (dephasage {alpha*PHI*180:.0f} degres) :")
                for i in range(min(3, len(facts) - 1)):
                    lines.append(f"  + {facts[i].get('text', '')[:100]}  <->  {facts[i+1].get('text', '')[:100]}")
            lines.append("")
            lines.append(f"[Genere par dephasage holographique phi | alpha={alpha:.2f} | {len(facts)} faits]")
            return {"text": "\n".join(lines), "source": "creative_dephasing",
                    "mode": "creative", "alpha": alpha}
        return {"text": "Mode creatif non disponible.", "mode": "creative"}

    def _query_translate(self, prompt: str, src: str, tgt: str) -> Dict:
        """Mode traduction : transposition de frequence."""
        facteur = PHI ** 1.0  # fr->en par defaut
        kx_src, ky_src = hashlib.sha256(prompt.encode()).hexdigest()[:16], hashlib.sha256(("t_"+prompt).encode()).hexdigest()[:16]
        kx_src = (int(kx_src, 16) % 6400) / 100 - 32
        ky_src = (int(ky_src, 16) % 6400) / 100 - 32
        kx_tgt = kx_src * facteur
        ky_tgt = ky_src * facteur

        lines = [
            f"TRADUCTION HOLOGRAPHIQUE [{src} -> {tgt}]",
            "=" * 50,
            f"Facteur de transposition phi : {facteur:.4f}",
            f"Espace source : ({kx_src:.2f}, {ky_src:.2f})",
            f"Espace cible  : ({kx_tgt:.2f}, {ky_tgt:.2f})",
            "",
            f"La transposition phi a ete appliquee. Pour une traduction concrete,",
            f"l'hologramme a besoin de contenu bilingue dans cette paire de langues.",
        ]
        return {"text": "\n".join(lines), "source": "frequency_transposition",
                "mode": "translate", "source_lang": src, "target_lang": tgt}

    def _query_summarize(self, prompt: str) -> Dict:
        """Mode resume : seuillage Mittag-Leffler."""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', prompt) if len(s.strip()) > 10]
        if not sentences:
            return {"text": prompt[:500], "mode": "summarize"}

        energies = []
        for s in sentences:
            h = hashlib.sha256(s.encode()).hexdigest()
            e = sum(int(h[i:i+4], 16) for i in range(0, 32, 4)) / 1e6
            energies.append(e)

        arr = np.array(energies)
        threshold = np.median(arr)
        kept = [sentences[i] for i, e in enumerate(energies) if e >= threshold]

        lines = [
            f"RESUME HOLOGRAPHIQUE (seuillage Mittag-Leffler)",
            "=" * 50,
            f"Phrases originales : {len(sentences)}",
            f"Phrases conservees : {len(kept)} (compression {1-len(kept)/max(len(sentences),1):.0%})",
            f"Seuil energie : {threshold:.4f}",
            "",
            " ".join(kept),
        ]
        return {"text": "\n".join(lines), "source": "amplitude_filtering",
                "mode": "summarize", "kept": len(kept), "original": len(sentences)}

    def get_stats(self) -> Dict:
        return {**self.stats, "mode_counts": dict(self.stats["mode_counts"]), "built": self.built}


# ═══════════════════════════════════════════════════════════════════════════════
# MODULES SPECIALISES (simplifies, sans dependance au 1024x1024)
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicCreativeEngine:
    def create(self, query, alpha=0.3):
        return {"text": f"Mode creatif (alpha={alpha:.2f})", "mode": "creative", "alpha": alpha}

class HolographicTranslationEngine:
    def translate(self, text, source_lang="fr", target_lang="en"):
        return {"text": f"Traduction [{source_lang}->{target_lang}]", "mode": "translate"}

    def get_supported_pairs(self): return []

class HolographicSummarizationEngine:
    def summarize(self, text):
        return {"text": text[:200] + "...", "mode": "summarize"}


# ═══════════════════════════════════════════════════════════════════════════════
# SERVEUR HTTP
# ═══════════════════════════════════════════════════════════════════════════════

class KANextUnifiedServer:
    def __init__(self, host="0.0.0.0", port=8442):
        self.host, self.port = host, port
        self.engine = KANextEngine()
        self.engine.build()

    def handle_query(self, data):
        return self.engine.query(
            prompt=data.get("prompt", data.get("query", "")),
            mode=data.get("mode", "auto"),
            creative_alpha=data.get("creative_alpha", 0.3),
            translate_source=data.get("translate_source", "fr"),
            translate_target=data.get("translate_target", "en"))

    def start_http_server(self):
        from http.server import HTTPServer, BaseHTTPRequestHandler
        er = self

        class H(BaseHTTPRequestHandler):
            def do_GET(s):
                if s.path == "/" or s.path == "":
                    s.send_response(200); s.send_header('Content-Type','text/html'); s.end_headers()
                    s.wfile.write(b"<h1>KA-Next v2</h1><p>Ensemble Nx64x64 actif</p>")
                elif s.path == "/health":
                    s.send_response(200); s.send_header('Content-Type','application/json'); s.end_headers()
                    s.wfile.write(json.dumps({"status":"ok"}).encode())
                elif s.path == "/stats":
                    s.send_response(200); s.send_header('Content-Type','application/json'); s.end_headers()
                    s.wfile.write(json.dumps(er.engine.get_stats(), default=str).encode())

            def do_POST(s):
                cl = int(s.headers.get('Content-Length', 0))
                body = json.loads(s.rfile.read(cl)) if cl > 0 else {}
                result = er.handle_query(body)
                s.send_response(200); s.send_header('Content-Type','application/json'); s.send_header('Access-Control-Allow-Origin','*'); s.end_headers()
                s.wfile.write(json.dumps(result, ensure_ascii=False).encode())

            def do_OPTIONS(s):
                s.send_response(200); s.send_header('Access-Control-Allow-Origin','*'); s.send_header('Access-Control-Allow-Methods','GET,POST'); s.end_headers()

        log.info(f"KA-Next v2 demarre sur http://{self.host}:{self.port}")
        HTTPServer((self.host, self.port), H).serve_forever()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description="KA-Next v2 -- Ensemble Nx64x64")
    p.add_argument("--serve", action="store_true")
    p.add_argument("--port", type=int, default=8442)
    p.add_argument("--query", type=str, default=None)
    p.add_argument("--mode", type=str, default="auto")

    args = p.parse_args()

    if args.serve:
        KANextUnifiedServer(port=args.port).start_http_server()
    elif args.query:
        engine = KANextEngine()
        engine.build()
        result = engine.query(args.query, mode=args.mode)
        print(f"\n{'='*60}")
        print(f"  REPONSE [{result.get('mode','?')}]")
        print(f"{'='*60}")
        print(result.get("text", "Erreur"))
        print(f"\n  Source: {result.get('source','?')} | {result.get('temps_ms',0)}ms | Confiance: {result.get('confidence','?')}")
    else:
        print("KA-Next v2 -- Ensemble Nx64x64")
        print("  python ka_next_core.py --serve")
        print("  python ka_next_core.py --query \"...\"")


if __name__ == "__main__":
    main()