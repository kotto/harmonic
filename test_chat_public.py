import urllib.request, json

tests = [
    "cette theorie date de quand?",
    "j ai demande la date",
    "bonjour qui es tu",
    "explique la theorie harmonique",
    "quels sont tes scores aux benchmarks?"
]

for test in tests:
    body = json.dumps({"prompt": test, "temperature": 0.0, "max_tokens": 1000}).encode()
    req = urllib.request.Request(
        "http://localhost:9000/api/chat/public",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        r = urllib.request.urlopen(req, timeout=10)
        data = json.loads(r.read())
        print(f"Q: {test}")
        print(f"R: {data['response'][:200]}...")
        print(f"  Latence: {data['processing_time']*1000:.1f}ms | Confiance: {data['confidence']:.2f}")
        print()
    except Exception as e:
        print(f"Erreur pour '{test}': {e}")
