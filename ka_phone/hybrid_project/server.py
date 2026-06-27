#!/usr/bin/env python3
"""
KA HYBRID — Serveur API Unifie v1.1
=====================================
Architecture :
  1. ParametricKB (maths, logique) -> reponse directe, 0% DeepSeek
  2. DeepSeek API (pour tout le reste, avec faits en contexte)
  3. Template fallback (si DeepSeek echoue)

Hierarchie :
  Niveau 1 : ParametricKB (confidence >= 0.90) -> reponse calculatoire
  Niveau 2 : DeepSeek API (deepseek-chat) -> faits holographiques en contexte
  Niveau 3 : Template d'assemblage (dernier recours)

Usage :
  python server.py              # Demarrer le serveur (port 8420)
  python server.py --test       # Tests integres
"""

import os, sys, json, time, re, math, hashlib, logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List, Optional, Any
from datetime import datetime
import argparse

# ---- Paths ----
BASE_DIR = Path(__file__).parent.absolute()
ROOT_DIR = BASE_DIR.parent.parent
sys.path.insert(0, str(BASE_DIR.parent))

# ---- Logger ----
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger("ka-hybrid")

# ---- Configuration ----
CONFIG_PATH = BASE_DIR / "config.json"
if CONFIG_PATH.exists():
    with open(CONFIG_PATH) as f:
        CONFIG = json.load(f)
else:
    CONFIG = {
        "server": {"host": "0.0.0.0", "port": 8420},
        "deepseek": {"model": "deepseek-chat", "base_url": "https://api.deepseek.com",
                     "timeout_seconds": 60, "max_tokens_default": 500, "temperature_default": 0.3},
        "retrieval": {"patches_per_query": 30, "max_facts_context": 4000, "max_facts_display": 40},
        "verification": {"enabled": True, "strict_mode": False},
        "styles": {
            "general": {"max_tokens": 500, "temperature": 0.3},
            "concise": {"max_tokens": 150, "temperature": 0.2},
            "creative": {"max_tokens": 600, "temperature": 0.5},
            "technical": {"max_tokens": 800, "temperature": 0.2},
        }
    }

# ---- DeepSeek API Key ----
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = CONFIG["deepseek"]["model"]
DEEPSEEK_BASE_URL = CONFIG["deepseek"]["base_url"]

# ---- Auto-Learning & TTS ----
LEARNING_DIR = BASE_DIR / "learning"
LEARNING_FILE = LEARNING_DIR / "learned_facts.json"
os.makedirs(LEARNING_DIR, exist_ok=True)

TTS_CACHE_DIR = BASE_DIR / "tts_cache"
os.makedirs(TTS_CACHE_DIR, exist_ok=True)


# ==============================================================================
# CORE ENGINE
# ==============================================================================

class HybridEngine:
    """Moteur hybride : ParametricKB -> DeepSeek API -> Auto-Learning -> Template."""

    def __init__(self):
        self.pipeline = None
        self.verifier = None
        self.learned_facts = self._load_learned_facts()
        self.stats = {
            "total_queries": 0, "api_calls": 0, "parametric_hits": 0,
            "template_fallbacks": 0, "verified": 0, "rejected": 0,
            "learned": len(self.learned_facts), "total_time_ms": 0,
            "started_at": datetime.now().isoformat()
        }
        self._init_pipeline()

    def _load_learned_facts(self) -> Dict:
        """Charge les faits appris automatiquement."""
        if LEARNING_FILE.exists():
            try:
                with open(LEARNING_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_learned_facts(self):
        """Sauvegarde les faits appris."""
        with open(LEARNING_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.learned_facts, f, ensure_ascii=False, indent=2)

    def _learn_from_response(self, prompt: str, response: str):
        """Extrait et sauvegarde les connaissances de la reponse DeepSeek."""
        # Filtrer : ne pas apprendre si la reponse est UNIQUEMENT un refus
        skip_if_only = ["je ne dispose pas de cette information", "je ne peux pas repondre",
                        "je ne sais pas", "aucune donnee concernant",
                        "ne dispose d'aucune donnee", "pas d'information a ce sujet"]
        # Compter les caracteres "utiles" hors mention de l'hologramme
        useful = response.lower()
        for phrase in ["d'apres ma connaissance externe", "l'hologramme ne contient pas",
                       "connaissance externe", "hologramme"]:
            useful = useful.replace(phrase, "")
        # Si apres nettoyage il reste moins de 30 caracteres significatifs, c'est un refus
        if len(useful.strip()) < 30:
            return

        # Extraire les phrases factuelles (contenant des noms propres, nombres, etc.)
        sentences = re.split(r'[.!?]+', response)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15 or len(sentence) > 300:
                continue
            # Au moins un nom propre (majuscule en debut de mot) ou un nombre
            has_entity = bool(re.search(r'\b[A-Z][a-z]+\b', sentence)) or bool(re.search(r'\b\d+\b', sentence))
            if has_entity:
                key = hashlib.md5(sentence.encode()[:200]).hexdigest()[:12]
                if key not in self.learned_facts:
                    self.learned_facts[key] = {
                        "text": sentence,
                        "source": "deepseek_auto_learn",
                        "question": prompt[:150],
                        "timestamp": datetime.now().isoformat(),
                    }
                    # Injecter aussi dans QuickFacts si possible
                    try:
                        from quick_facts import QuickFacts
                        qf = QuickFacts()
                        qf.add_fact(key, sentence, [])
                        log.info(f"[Apprentissage] Nouveau fait appris : {sentence[:80]}...")
                    except Exception:
                        pass

        self._save_learned_facts()
        self.stats["learned"] = len(self.learned_facts)

    def _init_pipeline(self):
        try:
            import importlib.util
            bridge_path = BASE_DIR.parent / "hologram_vector_bridge.py"
            spec = importlib.util.spec_from_file_location("hologram_vector_bridge", bridge_path)
            bridge = importlib.util.module_from_spec(spec)
            old_cwd = os.getcwd()
            os.chdir(str(BASE_DIR.parent))
            try:
                spec.loader.exec_module(bridge)
                self.pipeline = bridge.HologramVectorPipeline(use_llm=False)
                self.pipeline.build(force=False)
                self.verifier = bridge.DeterministicVerificationLayer()
                self.reasoner = bridge.ResonanceReasoner(self.pipeline)
                log.info("Pipeline holographique initialise (avec ResonanceReasoner)")
            finally:
                os.chdir(old_cwd)
        except Exception as e:
            log.error(f"Erreur initialisation pipeline : {e}")
            self.pipeline = None

    def retrieve_facts(self, query: str, k: int = 30) -> List[Dict]:
        if self.pipeline is None:
            return []
        result = self.pipeline.query(query, k=k, style="general")
        if result.get("facts_used", 0) == 0:
            return []
        patch_indices = list(range(min(result.get("patches_used", 0), k)))
        if self.pipeline.mapper and patch_indices:
            return self.pipeline.mapper.get_facts_for_patches(patch_indices)
        return []

    def query(self, prompt: str, style: str = "general",
              max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
        self.stats["total_queries"] += 1
        t0 = time.time()

        style_config = CONFIG["styles"].get(style, CONFIG["styles"]["general"])
        if max_tokens is None:
            max_tokens = style_config["max_tokens"]
        if temperature is None:
            temperature = style_config["temperature"]

        # 1. Retrieval holographique
        k_patches = CONFIG["retrieval"]["patches_per_query"]
        retrieved_facts = self.retrieve_facts(prompt, k=k_patches)

        # 2. ParametricKB
        parametric_text = None
        try:
            from parametric_kb_fr import ParametricKB
            pr = ParametricKB().solve(prompt)
            if pr:
                conf = pr.get("confidence", 0.95) if isinstance(pr, dict) else 0.95
                if conf >= 0.90:
                    parametric_text = pr.get("text", str(pr)) if isinstance(pr, dict) else str(pr)
        except Exception:
            pass

        # 3. Contexte de faits - chainage multi-hop par resonance (NOUVEAU)
        fact_context = self._build_fact_context(retrieved_facts)
        has_facts = bool(fact_context.strip())
        multi_hop_facts = retrieved_facts
        multi_hop_used = False
        
        if hasattr(self, 'reasoner') and self.reasoner and has_facts:
            try:
                reasoning_prompt, hop_facts = self.reasoner.build_reasoning_prompt(prompt, depth=3)
                if hop_facts and len(hop_facts) > 0:
                    fact_context = reasoning_prompt
                    multi_hop_facts = hop_facts
                    multi_hop_used = True
            except Exception:
                pass
        
        # has_facts already computed above

        # 4. HIERARCHIE DE DECISION
        llm_response = None
        source = "none"

        # NIVEAU 1 : ParametricKB (reponse calculatoire, 0% DeepSeek, ~0ms)
        if parametric_text:
            llm_response = parametric_text
            source = "parametric_kb"
            self.stats["parametric_hits"] += 1

        # NIVEAU 2 : DeepSeek API (pour tout le reste)
        elif DEEPSEEK_API_KEY:
            system_prompt = self._build_system_prompt(fact_context if has_facts else "Aucun fait specifique trouve.", style)
            user_prompt = f"Question : {prompt}\n\nReponds en francais. Si tu ne sais pas, dis-le clairement. N'invente rien."
            llm_response = self._call_deepseek_api(system_prompt, user_prompt,
                                                    max_tokens=max_tokens, temperature=temperature)
            if llm_response:
                self.stats["api_calls"] += 1
                source = "deepseek_api"

        # NIVEAU 3 : Template (dernier recours)
        if llm_response is None:
            llm_response = self._template_assemble(retrieved_facts, prompt)
            self.stats["template_fallbacks"] += 1
            source = "template_fallback"

        # 4.5 AUTO-APPRENTISSAGE : sauvegarder les connaissances DeepSeek
        if source == "deepseek_api" and llm_response:
            self._learn_from_response(prompt, llm_response)

        # 5. Verification
        verification = {"traceable": True, "score": 1.0, "hallucination_phrases": [], "verdict": "valid"}
        if CONFIG["verification"]["enabled"] and self.verifier and source != "parametric_kb":
            verification = self.verifier.verify(llm_response, retrieved_facts, prompt,
                                                strict_mode=CONFIG["verification"]["strict_mode"])

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        self.stats["total_time_ms"] += elapsed_ms
        self.stats["verified" if verification["traceable"] else "rejected"] += 1

        return {
            "text": llm_response, "source": source,
            "model": DEEPSEEK_MODEL if source == "deepseek_api" else "none",
            "confidence": round(0.99 if source == "parametric_kb" else 0.90 if source == "deepseek_api" else 0.70, 2),
            "verified": verification["traceable"], "trace_score": verification["score"],
            "trace_verdict": verification["verdict"],
            "hallucination_phrases": verification.get("hallucination_phrases", []),
            "facts_used": len(multi_hop_facts),
            "multi_hop": multi_hop_used,
            "style": style, "temps_ms": elapsed_ms, "timestamp": datetime.now().isoformat(),
        }

    def _build_fact_context(self, facts: List[Dict]) -> str:
        max_chars = CONFIG["retrieval"]["max_facts_context"]
        lines, seen = [], set()
        for f in facts[:CONFIG["retrieval"]["max_facts_display"]]:
            t = f.get("text", "")
            if t and len(t) > 3 and t not in seen:
                seen.add(t); lines.append(f"- {t.strip()}")
        ctx = "\n".join(lines)
        return ctx[:max_chars] + ("\n... (tronque)" if len(ctx) > max_chars else "")

    def _build_system_prompt(self, fact_context: str, style: str) -> str:
        sis = {"general":"Sois clair, precis et concis.","concise":"Reponds en 2-3 phrases maximum.",
               "creative":"Utilise un style elegant et poetique tout en restant factuel.",
               "technical":"Sois technique et detaille."}
        if fact_context and fact_context != "Aucun fait specifique trouve.":
            # Des faits sont disponibles -> les utiliser en priorite
            return f"""Tu es KA, un assistant dont la base de connaissance principale est un hologramme d'ondes universelles.

Priorite : utilise d'abord les faits de l'hologramme ci-dessous s'ils sont pertinents.
Si l'hologramme ne contient pas l'information demandee, tu peux repondre avec tes connaissances generales.
Dans ce cas, indique clairement que l'information vient de ta connaissance externe.
{sis.get(style, sis['general'])}

FAITS DE L'HOLOGRAMME (source primaire) :
{fact_context}"""
        else:
            # Aucun fait -> DeepSeek repond avec sa connaissance
            return f"""Tu es KA, un assistant. Reponds a la question de maniere utile et precise.
{sis.get(style, sis['general'])}
Si tu n'es pas sur de la reponse, dis-le clairement."""

    def _call_deepseek_api(self, sp: str, up: str, max_tokens=500, temperature=0.3) -> Optional[str]:
        try:
            import requests
            resp = requests.post(f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                headers={"Content-Type":"application/json","Authorization":f"Bearer {DEEPSEEK_API_KEY}"},
                json={"model":DEEPSEEK_MODEL,"messages":[{"role":"system","content":sp},{"role":"user","content":up}],
                      "max_tokens":max_tokens,"temperature":temperature,"top_p":0.95,"stream":False},
                timeout=CONFIG["deepseek"]["timeout_seconds"])
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            log.warning(f"DeepSeek HTTP {resp.status_code}: {resp.text[:100]}")
            return None
        except Exception as e:
            log.warning(f"DeepSeek API : {e}")
            return None

    def _template_assemble(self, facts: List[Dict], query: str) -> str:
        texts = [f.get("text","") for f in facts[:5] if f.get("text","") and len(f.get("text",""))>3]
        if not texts: return "Desole, je ne peux pas repondre a cette question pour le moment."
        if len(texts) == 1: return texts[0]
        return "\n".join(f"- {t}" for t in texts)

    def get_stats(self) -> Dict:
        return {**self.stats,
            "avg_time_ms": round(self.stats["total_time_ms"] / max(self.stats["total_queries"], 1), 1),
            "api_available": bool(DEEPSEEK_API_KEY), "model": DEEPSEEK_MODEL}


# ==============================================================================
# HTTP SERVER
# ==============================================================================

class HybridAPIHandler(BaseHTTPRequestHandler):
    engine = None

    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_html()
        elif self.path == "/mobile" or self.path == "/mobile.html":
            self._serve_mobile()
        elif self.path == "/health":
            self._json(self._health())
        elif self.path == "/stats":
            self._json(self.engine.get_stats())
        elif self.path.startswith("/tts?"):
            from urllib.parse import urlparse, parse_qs
            params = parse_qs(urlparse(self.path).query)
            text = params.get("text", params.get("q", [""]))[0]
            if text:
                self._serve_tts(text, params.get("voice", ["fr-FR-DeniseNeural"])[0])
            else:
                self.send_error(400, "Parametre 'text' requis")
        elif self.path.startswith("/query?"):
            from urllib.parse import urlparse, parse_qs
            params = parse_qs(urlparse(self.path).query)
            q = params.get("q", [""])[0]
            if q:
                self._json(self.engine.query(q, style=params.get("style", ["general"])[0]))
            else:
                self._json({"error":"Parametre 'q' requis"}, 400)
        else:
            self.send_error(404)

    def _serve_tts(self, text: str, voice: str = "fr-FR-DeniseNeural"):
        """Synthese vocale Edge-TTS directe (MP3, fiable)."""
        import asyncio, hashlib as hl, edge_tts, tempfile

        text = text.strip()
        if not text:
            self.send_error(400, "Texte vide")
            return

        cache_key = hl.md5(f"{text}|{voice}".encode()).hexdigest()[:16]
        cache_file = TTS_CACHE_DIR / f"{cache_key}.mp3"

        if cache_file.exists():
            with open(cache_file, "rb") as f:
                audio_data = f.read()
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(audio_data)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(audio_data)
            return

        async def _gen():
            tmp = os.path.join(tempfile.gettempdir(), f"ka_tts_{cache_key}.mp3")
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(tmp)
            with open(tmp, "rb") as f:
                data = f.read()
            os.remove(tmp) if os.path.exists(tmp) else None
            return data

        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(_gen(), loop)
            audio_data = future.result(timeout=60)
        except RuntimeError:
            audio_data = asyncio.run(_gen())

        if not audio_data or len(audio_data) < 100:
            self.send_error(500, "TTS n'a pas genere d'audio")
            return

        with open(cache_file, "wb") as f:
            f.write(audio_data)

        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Content-Length", str(len(audio_data)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(audio_data)

    def do_POST(self):
        if self.path == "/query":
            cl = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(cl))
                prompt = data.get("prompt", data.get("q", ""))
                if not prompt:
                    return self._json({"error":"Champ 'prompt' requis"}, 400)
                self._json(self.engine.query(prompt,
                    style=data.get("style","general"),
                    max_tokens=data.get("max_tokens"),
                    temperature=data.get("temperature")))
            except json.JSONDecodeError:
                self._json({"error":"JSON invalide"}, 400)
        elif self.path == "/health":
            self._json(self._health())
        else:
            self.send_error(404)

    def _health(self):
        s = self.engine.get_stats()
        return {"status":"ok","version":"1.1","project":"KA Hybrid","api_available":s["api_available"],
                "model":s["model"],"uptime_queries":s["total_queries"],
                "uptime_seconds":(datetime.now()-datetime.fromisoformat(s["started_at"])).total_seconds()}

    def _json(self, data, status=200):
        self.send_response(status); self._cors()
        self.send_header("Content-Type","application/json; charset=utf-8"); self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")

    def _serve_mobile(self):
        """Interface mobile immersive (Three.js, anneau neural)."""
        mobile_path = BASE_DIR.parent / "www" / "mobile.html"
        if mobile_path.exists():
            with open(mobile_path, "r", encoding="utf-8") as f:
                html = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_error(404, "mobile.html not found")

    def _serve_html(self):
        html = """<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>KA Hybrid</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',system-ui,sans-serif;background:#0a0a1a;color:#e0e0e0;min-height:100vh}
.header{background:linear-gradient(135deg,#1a1a3e,#0d0d2b);padding:30px;text-align:center;border-bottom:1px solid #2a2a5e}
.header h1{font-size:2em;color:#c9a84c;margin-bottom:8px}.header p{color:#888;font-size:.95em}
.container{max-width:900px;margin:0 auto;padding:20px}.query-box{display:flex;gap:10px;margin-bottom:20px}
.query-box input{flex:1;padding:14px 18px;border:1px solid #3a3a6e;border-radius:8px;background:#12122a;color:#e0e0e0;font-size:1em}
.query-box input:focus{outline:none;border-color:#c9a84c}
.query-box button{padding:14px 28px;background:linear-gradient(135deg,#c9a84c,#8b6914);border:none;border-radius:8px;color:#0a0a1a;font-weight:bold;cursor:pointer;font-size:1em}
.style-bar{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap}
.style-btn{padding:8px 16px;border:1px solid #3a3a6e;border-radius:20px;background:transparent;color:#aaa;cursor:pointer;font-size:.85em}
.style-btn.active{background:#c9a84c22;border-color:#c9a84c;color:#c9a84c}
.response{background:#12122a;border:1px solid #2a2a5e;border-radius:8px;padding:24px;min-height:200px;white-space:pre-wrap;line-height:1.7;font-size:.95em}
.response.loading{opacity:.5}.meta{display:flex;gap:20px;margin-top:16px;font-size:.8em;color:#666;flex-wrap:wrap}
.meta span{padding:4px 10px;background:#1a1a3e;border-radius:4px}
</style></head><body>
<div class="header"><h1>KA Hybrid</h1><p>Interface Universelle Harmonique + DeepSeek</p></div>
<div class="container">
<div class="style-bar">
<button class="style-btn active" data-style="general">General</button>
<button class="style-btn" data-style="concise">Concis</button>
<button class="style-btn" data-style="creative">Creatif</button>
<button class="style-btn" data-style="technical">Technique</button>
</div>
<div class="query-box">
<input type="text" id="query" placeholder="Posez votre question..." autofocus>
<button onclick="sendQuery()">Envoyer</button>
</div>
<div class="response" id="response">Bienvenue sur KA Hybrid.<br><br>Posez une question pour interroger l'hologramme d'ondes universelles.</div>
<div class="meta" id="meta"></div>
<div id="audioBar" style="display:none;margin-top:16px;text-align:center">
<button onclick="speakLastResponse()" style="padding:12px 24px;background:linear-gradient(135deg,#3ef0d8,#1a8a7a);border:none;border-radius:25px;color:#0a0a1a;font-weight:bold;cursor:pointer;font-size:0.95em">🔊 Ecouter la reponse</button>
<select id="voiceSelect" onchange="changeVoice()" style="margin-left:10px;padding:8px;background:#12122a;border:1px solid #3a3a6e;border-radius:8px;color:#e0e0e0;font-size:0.85em">
<option value="fr-FR-DeniseNeural">Denise (F)</option>
<option value="fr-FR-HenriNeural">Henri (H)</option>
<option value="fr-FR-EloiseNeural">Eloise (F)</option>
<option value="fr-FR-JeromeNeural">Jerome (H)</option>
</select>
</div></div>
<script>
let currentStyle='general', lastResponseText='', currentVoice='fr-FR-DeniseNeural';
document.querySelectorAll('.style-btn').forEach(b=>{b.addEventListener('click',()=>{document.querySelectorAll('.style-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');currentStyle=b.dataset.style})});
document.getElementById('query').addEventListener('keydown',e=>{if(e.key==='Enter')sendQuery()});
function changeVoice(){currentVoice=document.getElementById('voiceSelect').value}
async function sendQuery(){const q=document.getElementById('query').value.trim();if(!q)return;const r=document.getElementById('response');const m=document.getElementById('meta');const ab=document.getElementById('audioBar');r.classList.add('loading');r.textContent="Interrogation...";m.innerHTML='';ab.style.display='none';try{const res=await fetch('/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:q,style:currentStyle})});const d=await res.json();r.textContent=d.text||d.error||'Erreur';r.classList.remove('loading');lastResponseText=d.text||'';m.innerHTML=`<span>Source: ${d.source||'N/A'}</span><span>Modele: ${d.model||'N/A'}</span><span>Trace: ${(d.trace_score*100).toFixed(0)}%</span><span>Faits: ${d.facts_used||0}</span><span>Temps: ${d.temps_ms||0}ms</span><span>Verifie: ${d.verified?'Oui':'Non'}</span>`;if(d.text&&d.text.length>10)ab.style.display='block'}catch(e){r.textContent='Erreur de connexion.';r.classList.remove('loading')}}
function speakLastResponse(){if(!lastResponseText)return;const audio=new Audio(`/tts?text=${encodeURIComponent(lastResponseText.substring(0,500))}&voice=${currentVoice}`);audio.play().catch(e=>alert('Audio non disponible: '+e))}
</script></body></html>"""
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self._cors(); self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass


# ==============================================================================
# MAIN
# ==============================================================================

def run_server(host="0.0.0.0", port=8420):
    log.info("=" * 55)
    log.info("  KA HYBRID v1.1 - Serveur API Unifie")
    log.info("  ParametricKB -> DeepSeek API -> Template")
    log.info("=" * 55)
    HybridAPIHandler.engine = HybridEngine()
    log.info(f"  DeepSeek : {'[CONNECTE]' if DEEPSEEK_API_KEY else '[NON CONFIGURE]'}  Modele: {DEEPSEEK_MODEL}")
    log.info(f"  Interface: http://localhost:{port}")
    log.info(f"  Ctrl+C pour arreter")
    HTTPServer((host, port), HybridAPIHandler).serve_forever()


def run_tests():
    print("=" * 55)
    print("  TESTS - KA HYBRID v1.1")
    print("=" * 55)
    engine = HybridEngine()
    print(f"\n  DeepSeek: {'[OK]' if DEEPSEEK_API_KEY else '[--]'}  Model: {DEEPSEEK_MODEL}")
    tests = [
        ("Quelle est la capitale du Senegal ?", "general"),
        ("Combien font 12 x 15 ?", "concise"),
        ("Quelle est la racine carree de 144 ?", "concise"),
        ("Qu'est-ce que la gravite ?", "general"),
        ("Comment calculer l'aire d'un cercle de rayon 5 ?", "technical"),
    ]
    print(f"\n  {len(tests)} QUESTIONS\n")
    for q, s in tests:
        r = engine.query(q, style=s)
        stat = "OK" if r.get("verified") else "!!"
        src = {"parametric_kb":"[MATHS]","deepseek_api":"[API]","template_fallback":"[TPL]"}.get(r["source"],"[???]")
        print(f"  [{stat}] {src} Q: {q[:55]}")
        print(f"    R: {str(r.get('text',''))[:130]}...")
        print(f"    Source:{r['source']} | Trace:{r['trace_score']:.0%} | Time:{r['temps_ms']}ms | Facts:{r['facts_used']}")
    s = engine.get_stats()
    print(f"\n  Resume: {s['total_queries']} queries, {s['api_calls']} API, {s['parametric_hits']} PKB, {s['template_fallbacks']} TPL, avg {s['avg_time_ms']}ms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KA Hybrid v1.1")
    parser.add_argument("--port", type=int, default=8420)
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--query", type=str, default=None)
    args = parser.parse_args()
    if args.test:
        run_tests()
    elif args.query:
        print(json.dumps(HybridEngine().query(args.query), ensure_ascii=False, indent=2))
    else:
        run_server(port=args.port)