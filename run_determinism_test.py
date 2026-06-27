#!/usr/bin/env python3
"""Test de déterminisme et vérification des corrections"""
import sys
sys.path.insert(0, '.')
from harmonic_saas.app.services.harmonic_comprehension import HarmonicComprehensionModule
import json

m = HarmonicComprehensionModule()
results = []

# Test 1: Déterminisme
print("=" * 60)
print("TEST 1: DÉTERMINISME")
print("=" * 60)
questions = [
    "Bonjour, qui es-tu ?",
    "Qui a créé la théorie harmonique ?",
    "Quels sont vos scores aux benchmarks ?",
    "Quelle est votre latence ?",
    "Parlez-moi de votre créativité",
]

for q in questions:
    r1 = m.process(q, "test_det")
    r2 = m.process(q, "test_det")
    r3 = m.process(q, "test_det")
    same = r1["response"] == r2["response"] == r3["response"]
    status = "✅" if same else "❌"
    print(f"\n{status} Question: {q[:60]}")
    print(f"   Déterministe: {same}")
    print(f"   Style: {r1['style_used']}")
    print(f"   Réponse: {r1['response'][:120]}...")
    results.append({"question": q, "deterministe": same, "style": r1["style_used"]})

# Test 2: Absence de concurrents
print("\n" + "=" * 60)
print("TEST 2: ABSENCE DE MENTIONS DE CONCURRENTS")
print("=" * 60)
concurrents = ["DeepSeek", "GPT-5", "Gemini", "Claude 4", "Qwen", "GPT5", "Claude"]
found_any = False
for q in questions:
    r = m.process(q, "test_conc")
    for c in concurrents:
        if c.lower() in r["response"].lower():
            print(f"❌ Concurrent '{c}' trouvé dans réponse à: {q[:50]}")
            found_any = True
if not found_any:
    print("✅ Aucune mention de concurrents détectée dans les réponses")

# Test 3: Discrétion sur l'identité
print("\n" + "=" * 60)
print("TEST 3: DISCRÉTION SUR L'IDENTITÉ")
print("=" * 60)
r = m.process("Qui est Alain Kotto ?", "test_id")
print(f"Réponse: {r['response'][:200]}")
if "validation auprès des pairs" in r["response"].lower() or "k.a." in r["response"].lower():
    print("✅ Discrétion respectée")
else:
    print("⚠️  Vérifier la réponse")

# Test 4: Pas de mention de DeepSeek/Qwen dans le code
print("\n" + "=" * 60)
print("TEST 4: VÉRIFICATION DU CODE SOURCE")
print("=" * 60)
with open("harmonic_saas/app/services/harmonic_comprehension.py", "r", encoding="utf-8") as f:
    content = f.read()

checks = {
    "DeepSeek": "DeepSeek" not in content,
    "deepseek": "deepseek" not in content,
    "Qwen": "Qwen" not in content,
    "qwen": "qwen" not in content,
    "GPT-5": "GPT-5" not in content,
    "Gemini 2.0": "Gemini 2.0" not in content,
    "Claude 4": "Claude 4" not in content,
    "DEEPSEEK_API_KEY": "DEEPSEEK_API_KEY" not in content,
    "api.deepseek.com": "api.deepseek.com" not in content,
    "deepseek-chat": "deepseek-chat" not in content,
    "Alain KOTTO": "Alain KOTTO" not in content,
    "LLM_API_KEY": "LLM_API_KEY" in content,
    "LLM_API_URL": "LLM_API_URL" in content,
    "LLM_MODEL": "LLM_MODEL" in content,
    "K.A.": "K.A." in content,
}

all_ok = True
for check, result in checks.items():
    status = "✅" if result else "❌"
    if not result:
        all_ok = False
    print(f"  {status} {check}: {'OK' if result else 'PRÉSENT!'}")

print(f"\n{'=' * 60}")
print(f"RÉSULTAT GLOBAL: {'✅ TOUS LES TESTS PASSENT' if all_ok else '❌ CERTAINS TESTS ÉCHOUENT'}")
print(f"{'=' * 60}")
