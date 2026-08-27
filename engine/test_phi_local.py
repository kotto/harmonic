"""Test Phi-3.5-mini local + architecture de contexte conversationnel

Usage:
    pip install huggingface-hub
    python test_phi_local.py
"""
import os, sys, json, time, re
from pathlib import Path

# ─── Configuration ───
MODEL_DIR = Path("E:/SAAS - Copie/engine/models")
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "Phi-3.5-mini-instruct-Q4_K_M.gguf"

# ─── Téléchargement si nécessaire ───
if not MODEL_PATH.exists():
    print(f"📥 Téléchargement de Phi-3.5-mini...")
    from huggingface_hub import hf_hub_download
    MODEL_PATH = Path(hf_hub_download(
        repo_id="bartowski/Phi-3.5-mini-instruct-GGUF",
        filename="Phi-3.5-mini-instruct-Q4_K_M.gguf",
        cache_dir=str(MODEL_DIR),
        resume_download=True,
    ))
    print(f"   ✅ Téléchargé: {MODEL_PATH}")

print(f"📦 Modèle: {MODEL_PATH} ({os.path.getsize(MODEL_PATH)/1e9:.2f} Go)")

# ─── Test 1: Chargement et inférence ───
print("\n" + "="*60)
print("TEST 1: Chargement + inférence basique")
print("="*60)

from llama_cpp import Llama

t0 = time.time()
llm = Llama(
    model_path=str(MODEL_PATH),
    n_ctx=2048,
    n_threads=4,
    verbose=False,
)
print(f"✅ Chargé en {time.time()-t0:.1f}s")

# Test simple
t1 = time.time()
resp = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "Tu es un assistant utile et concis."},
        {"role": "user", "content": "Explique la compression harmonique en 2 phrases."}
    ],
    temperature=0.1,
    max_tokens=100,
)
print(f"✅ Inférence en {time.time()-t1:.1f}s")
print(f"   Réponse: {resp['choices'][0]['message']['content'][:150]}")

# ─── Test 2: Classification d'intention (PromptComprehendor renfort) ───
print("\n" + "="*60)
print("TEST 2: Classification d'intention (renfort LLM)")
print("="*60)

tests = [
    "j'aimerais que tu examines l'état de mon espace de stockage",
    "fais le ménage dans mon téléphone",
    "dis moi ce qui prend toute la place sur mon appareil",
    "pourrais-tu vérifier l'espace disque de mon téléphone",
]

for msg in tests:
    t1 = time.time()
    resp = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": (
                "Classifie l'intention de l'utilisateur. "
                "Réponds UNIQUEMENT par un objet JSON:\n"
                '{"intent": "storage_action|action_command|arithmetic|specialize_request|learning|comparison|generation|greeting|factual_question", "confidence": 0.0-1.0}'
            )},
            {"role": "user", "content": msg}
        ],
        temperature=0.05,
        max_tokens=80,
    )
    text = resp["choices"][0]["message"]["content"]
    dt = time.time() - t1
    try:
        # Extract JSON
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            print(f"✅ {data.get('intent','?'):25s} conf={data.get('confidence',0):.2f} ({dt:.1f}s) \"{msg[:50]}\"")
        else:
            print(f"⚠️ Parse error: {text[:80]} ({dt:.1f}s)")
    except:
        print(f"⚠️ JSON error: {text[:80]} ({dt:.1f}s)")

# ─── Test 3: Conversation avec contexte ───
print("\n" + "="*60)
print("TEST 3: Conversation avec mémoire (contexte)")
print("="*60)

conversation = [
    "Je voudrais libérer de l'espace sur mon téléphone",
    "Oui, lance l'analyse",
    "Combien de place puis-je gagner ?",
    "Est-ce que ça va supprimer mes photos ?",
    "Non, finalement laisse tomber",
    "Quel temps fait-il aujourd'hui ?",
]

history = []
for turn, msg in enumerate(conversation):
    # Build messages with history
    messages = [
        {"role": "system", "content": (
            "Tu es KA, un assistant harmonique. "
            "Réponds de façon naturelle et concise. "
            "Maintiens le contexte de la conversation en cours."
        )}
    ]
    # Add history (last 4 exchanges)
    for h in history[-4:]:
        messages.append(h)
    
    # Add current message
    messages.append({"role": "user", "content": msg})
    
    t1 = time.time()
    resp = llm.create_chat_completion(
        messages=messages,
        temperature=0.3,
        max_tokens=150,
    )
    answer = resp["choices"][0]["message"]["content"]
    dt = time.time() - t1
    
    # Store in history
    history.append({"role": "user", "content": msg})
    history.append({"role": "assistant", "content": answer})
    
    print(f"\n Tour {turn+1} ({dt:.1f}s):")
    print(f"   👤 \"{msg}\"")
    print(f"   🤖 {answer[:120]}")

# ─── Test 4: Mémoire holographique (contexte long) ───
print("\n" + "="*60)
print("TEST 4: Synthèse de mémoire pour contexte long")
print("="*60)

# Simuler une conversation longue (20+ tours)
print("📝 Génération d'une conversation longue...")
long_history = []
for i in range(10):
    long_history.append({"role": "user", "content": f"Question {i+1}: Parle moi du sujet {i}"})
    long_history.append({"role": "assistant", "content": f"Voici des informations sur le sujet {i}..."})

# Test avec fenêtre glissante vs résumé
print(f"🔬 Historique: {len(long_history)} messages")

# Fenêtre glissante (last 6)
t1 = time.time()
messages_window = [
    {"role": "system", "content": "Assistant utile."},
    *long_history[-6:],
    {"role": "user", "content": "Que s'est-il dit récemment ?"}
]
resp = llm.create_chat_completion(messages=messages_window, temperature=0.1, max_tokens=100)
print(f"✅ Fenêtre glissante (6 derniers): {time.time()-t1:.1f}s")
print(f"   {resp['choices'][0]['message']['content'][:100]}")

# ─── Résumé mémoire ───
print("\n" + "="*60)
print("RÉSUMÉ DES TESTS PHI-3.5 LOCAL")
print("="*60)
print(f"""
📊 Résultats Phi-3.5-mini (Windows):

  Chargement initial : {time.time()-t0:.1f}s
  Modèle: 2.4 Go, Q4_K_M, n_ctx=2048

  Utilisation prévue:
    - Renfort PromptComprehendor (conf < 0.35)
    - Génération créative
    - Questions complexes
    - Contexte conversationnel (fenêtre glissante 6-8 tours)

  RAM estimée: ~3-4 Go
  Latence: 5-15s selon complexité
""")