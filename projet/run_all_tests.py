#!/usr/bin/env python3
"""
RUN ALL TESTS : Execute chaque test dans un sous-processus separe
===============================================================
Pour eviter les crashes memoire (STATUS_ACCESS_VIOLATION) lies a PyTorch.
Chaque test est ecrit dans un fichier .py temporaire puis execute.
Le test 3 (Initialisation Modele) est execute dans le processus principal
car PyTorch crashe en sous-processus sur Windows.
"""
import subprocess, sys, os, time, json

BASE = r'f:\SAAS - Copie'
os.chdir(BASE)

TESTS = [
    {
        "name": "Noyau ABC",
        "code": """
import math, sys, os
sys.path.insert(0, r'f:\\SAAS - Copie')
PHI = 1.618033988749895
PHI_INV = 0.6180339887498949
def gamma_approx(x):
    if x <= 0 and x == int(x): return float('nan')
    if x == 1.0 or x == 2.0: return 1.0
    if x == 0.5: return math.sqrt(math.pi)
    if x < 0.5: return math.pi / (math.sin(math.pi * x) * gamma_approx(1 - x))
    z = x - 1
    if z == 0: return 1.0
    s = 1.0; f = 1.0
    for c in [1/12, 1/288, -139/51840, -571/2488320]:
        f /= z
        s += c * f
    return math.sqrt(2*math.pi) * pow(z, z+0.5) * math.exp(-z) * s
def ml(alpha, z, terms=50):
    r = 0.0
    for k in range(terms):
        t = pow(z, k) / gamma_approx(alpha * k + 1); r += t
        if abs(t) < 1e-12: break
    return r
tests = [(PHI_INV, 0.0, 1.0), (PHI_INV, 1.0, None), (PHI_INV, -1.0, None), (PHI_INV, PHI, None), (PHI_INV, -PHI, None)]
for a, z, exp in tests:
    r = ml(a, z)
    print(f'  ml({a:.4f}, {z:.4f}) = {r:.6f}')
    if exp is not None and abs(r - exp) > 1e-6:
        print(f'  ERREUR: attendu {exp}')
        exit(1)
print('OK')
"""
    },
    {
        "name": "Initialisation Modele",
        "code": """
import sys, os
sys.path.insert(0, r'f:\\SAAS - Copie')
import torch
from harmonic_training.model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
from harmonic_weight_initializer import init_harmonic_model
config = HARMONIC_CONFIGS['harmonic-tiny']
model = HarmonicForCausalLM(config)
print(f'  Modele cree: {sum(p.numel() for p in model.parameters()):,} params')
model = init_harmonic_model(model)
print(f'  Init harmonique OK')
batch, seq_len = 1, 16
input_ids = torch.randint(1, config['vocab_size'] - 1, (batch, seq_len))
logits, loss, signatures = model(input_ids, labels=input_ids)
print(f'  Forward: logits={logits.shape}, loss={loss.item():.4f}')
print('OK')
"""
    },
    {
        "name": "Poids Harmoniques",
        "code": """
import sys, os
sys.path.insert(0, r'f:\\SAAS - Copie')
from harmonic_weight_initializer import harmonic_weight, harmonic_embedding_weight
for l in range(8):
    w = harmonic_weight(512, l, 8)
    print(f'  Couche {l}: w = {w:.4f}')
    if not (0.01 <= w <= 1.0):
        print(f'  ERREUR: poids hors limite')
        exit(1)
print('OK')
"""
    },
    {
        "name": "Agent ABC-native",
        "code": """
import sys, os
sys.path.insert(0, r'f:\\SAAS - Copie')
from harmonic_agentic.agentic_loop import HarmonicAgent, analyze_prompt
agent = HarmonicAgent(max_steps=3)
for p in ['Calcule 15% de 340', 'Ecris un poeme', 'Explique le ciel bleu']:
    sig = analyze_prompt(p)
    result = agent.run(p)
    print(f'  {p[:30]:30s} -> {result.final_answer[:50]}')
print('OK')
"""
    },
    {
        "name": "Analyse Vocale 7D",
        "code": """
import sys, os, math
sys.path.insert(0, r'f:\\SAAS - Copie')
from harmonic_agentic.voice_signature_7d import extract_voice_signature
sr = 44100
samples = [math.sin(2 * math.pi * 220 * t / sr) for t in range(int(sr * 0.5))]
sig = extract_voice_signature(samples, sr)
print(f'  Frequence: {sig.dominant_freq_hz:.1f} Hz, Emotion: {sig.emotion_label}')
print('OK')
"""
    },
    {
        "name": "Generation AV",
        "code": """
import sys, os
sys.path.insert(0, r'f:\\SAAS - Copie')
sys.path.insert(0, r'f:\\SAAS - Copie\\GENERATION_AV_HARMONIQUE')
from engine.harmonic_av_core import HarmonicAVCore
core = HarmonicAVCore()
audio = core.generate_audio('test', duration_s=0.2)
img = core.generate_image('test', width=64, height=64)
print(f'  Audio: {len(audio)} samples, Image: {img.shape}')
print('OK')
"""
    },
    {
        "name": "Moteur LM Arena",
        "code": """
import sys, os, time
sys.path.insert(0, r'f:\\SAAS - Copie')
from harmonic_lm_arena_engine import HarmonicResonanceEngine
engine = HarmonicResonanceEngine()
for p in ['Calcule 15% de 340', 'Ecris un poeme', 'Explique le ciel bleu']:
    start = time.time()
    result = engine.process(p)
    elapsed = (time.time() - start) * 1000
    print(f'  {p[:30]:30s} -> score={result.resonance_score:.4f}, pattern={result.pattern_name}, temps={elapsed:.1f}ms')
print('OK')
"""
    },
]

def run_test_subprocess(name, code):
    """Execute un test via un fichier temporaire (sous-processus)."""
    start = time.time()
    tmp_path = os.path.join(BASE, f'_test_{name.replace(" ", "_")}.py')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True, timeout=300
        )
        elapsed = time.time() - start
        output = result.stdout.strip()
        stderr = result.stderr.strip()
        
        if result.returncode == 0 and 'OK' in output:
            return {"status": "OK", "output": output, "time_ms": round(elapsed * 1000, 1)}
        else:
            full_output = output
            if stderr:
                full_output += '\n' + stderr
            return {"status": "ECHEC", "output": full_output, "time_ms": round(elapsed * 1000, 1)}
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "output": "Test depasse 300s", "time_ms": 300000}
    finally:
        try:
            os.remove(tmp_path)
        except:
            pass

def run_test_inprocess(name, code):
    """Execute un test dans le processus principal (evite crash PyTorch)."""
    start = time.time()
    tmp_path = os.path.join(BASE, f'_test_{name.replace(" ", "_")}.py')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    try:
        # Executer le fichier dans le processus courant
        exec_globals = {'__name__': '__main__', '__file__': tmp_path}
        exec(compile(open(tmp_path, encoding='utf-8').read(), tmp_path, 'exec'), exec_globals)
        elapsed = time.time() - start
        return {"status": "OK", "output": "Execution reussie", "time_ms": round(elapsed * 1000, 1)}
    except Exception as e:
        elapsed = time.time() - start
        return {"status": "ECHEC", "output": str(e), "time_ms": round(elapsed * 1000, 1)}
    finally:
        try:
            os.remove(tmp_path)
        except:
            pass

def main():
    print("=" * 60)
    print("TESTS COMPLETS DU HLM (sous-processus separes)")
    print("=" * 60)
    print()
    
    results = {}
    passed = 0
    failed = 0
    
    for test in TESTS:
        name = test["name"]
        print(f"  [{name}]...", end=" ", flush=True)
        
        # Le test 3 (Initialisation Modele) doit etre execute dans le processus principal
        # car PyTorch crashe en sous-processus sur Windows (STATUS_ACCESS_VIOLATION)
        if name == "Initialisation Modele":
            result = run_test_inprocess(name, test["code"])
        else:
            result = run_test_subprocess(name, test["code"])
        
        results[name] = result
        
        if result["status"] == "OK":
            print(f"OK ({result['time_ms']:.0f}ms)")
            passed += 1
        else:
            print(f"{result['status']} ({result['time_ms']:.0f}ms)")
            failed += 1
            if result["output"]:
                for line in result["output"].split('\n')[-15:]:
                    if line.strip():
                        print(f"    {line.strip()}")
    
    print()
    print("=" * 60)
    print("RAPPORT FINAL")
    print("=" * 60)
    for name, result in results.items():
        status = result["status"]
        print(f"  {name:30s} : {status}")
    
    print(f"\n  Total: {passed} reussis, {failed} echoues sur {len(TESTS)} tests")
    
    if failed == 0:
        print("\n  [SUCCES] Tous les tests passes !")
    else:
        print(f"\n  [ATTENTION] {failed} test(s) a corriger")
    
    # Rapport JSON
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": {k: {"status": v["status"], "time_ms": v["time_ms"]} for k, v in results.items()},
        "passed": passed,
        "failed": failed,
        "total": len(TESTS),
    }
    with open("rapport_tests_complets.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Rapport: rapport_tests_complets.json")
    
    return failed == 0

if __name__ == '__main__':
    main()
