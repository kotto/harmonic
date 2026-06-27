#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test rapide du proxy GGUF en mode demo (sans modele LLM)."""
import sys, os, time, threading, json, urllib.request

# Forcer UTF-8 pour la console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.llm.gguf_harmonizer import GGUFHarmonicProxy, GGUFHarmonicProxyConfig

# Configuration proxy en mode demo
proxy = GGUFHarmonicProxy(GGUFHarmonicProxyConfig(
    model_path="",
    model_alias="demo-test",
    n_ctx=2048,
    n_gpu_layers=0,
    resonance_strength=0.7,
    use_memory=True,
))

# Lancer le serveur dans un thread
def serve():
    proxy.run_server(host="127.0.0.1", port=18080)

t = threading.Thread(target=serve, daemon=True)
t.start()
print("  Serveur demarre sur http://127.0.0.1:18080")
time.sleep(1.5)

# 1. Health
resp = urllib.request.urlopen("http://127.0.0.1:18080/health")
health = json.loads(resp.read())
print(f"\n[1] HEALTH (sanite):")
print(f"  model = {health.get('model')}")
print(f"  harmonic = {health.get('harmonic')}")
print(f"  memory_active = {health.get('memory_active')}")
assert health.get('harmonic') == True, "ERREUR: harmonic devrait etre True"
assert health.get('memory_active') == True, "ERREUR: memory devrait etre True"
print("  >> OK")

# 2. Signature 9D
resp = urllib.request.urlopen(
    "http://127.0.0.1:18080/harmonic/signature?prompt=Explique+la+relativite"
)
sig = json.loads(resp.read())
print(f"\n[2] SIGNATURE 9D:")
print(f"  categorie = {sig.get('category')}")
sig_dims = [round(v,3) for v in sig.get('signature_9d',[])]
print(f"  signature = {sig_dims}")
assert sig.get('category') == 'reasoning', "ERREUR: devrait etre 'reasoning'"
assert len(sig_dims) == 9, "ERREUR: signature devrait avoir 9 dimensions"
print("  >> OK")

# 3. Chat completion
req = urllib.request.Request(
    "http://127.0.0.1:18080/v1/chat/completions",
    data=json.dumps({
        "messages": [{"role": "user", "content": "Parle moi du nombre d'or phi"}],
        "max_tokens": 200,
    }).encode(),
    headers={"Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read())

print(f"\n[3] CHAT COMPLETION:")
choices = data.get("choices", [])
if choices:
    content = choices[0]["message"]["content"]
    print(f"  contenu = {content[:150]}...")
    print(f"  longueur = {len(content)} caracteres")
    assert len(content) > 20, "ERREUR: reponse trop courte"
    assert "phi" in content.lower() or "nombre" in content.lower(), "ERREUR: devrait parler de phi"
else:
    print("  contenu = (vide)")
    assert False, "ERREUR: aucune reponse"
hr = data.get("harmonic_resonance", {})
print(f"  resonance_score = {hr.get('resonance_score')}")
print(f"  category = {hr.get('category')}")
print("  >> OK")

print(f"\n  {('='*50)}")
print(f"  PROXY GGUF HARMONIQUE VALIDE EN MODE DEMO")
print(f"  {('='*50)}")
print(f"  Health:       OK")
print(f"  Signature 9D: OK ({sig.get('category')})")
print(f"  Chat:         OK ({len(choices[0]['message']['content'].split())} mots)")
print(f"  Resonance:    OK (score={hr.get('resonance_score')})")
