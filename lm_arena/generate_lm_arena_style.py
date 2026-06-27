#!/usr/bin/env python3
"""
Generate LM Arena Styled Answers for Knowledge Base
=====================================================
Takes the existing knowledge base and adds a 'text_lm_arena'
field with DeepSeek-reformulated answers in concise LM Arena style.
Then the engine serves 'text_lm_arena' in priority, falling back to 'text'.
"""

import os, sys, json, time, urllib.request, urllib.error, shutil

sys.path.insert(0, os.path.dirname(__file__))

def load_key():
    env_paths = [os.path.join(os.path.dirname(__file__), '..', '.env'),
                 os.path.join(os.path.dirname(__file__), '.env')]
    for p in env_paths:
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                for line in f:
                    if 'DEEPSEEK_API_KEY' in line:
                        return line.split('=',1)[1].strip().strip('"').strip("'")
    return ""

API_KEY = os.environ.get("DEEPSEEK_API_KEY", load_key())
API_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
API_MODEL = "deepseek-reasoner"

SYSTEM_PROMPT = """You refine mathematical Q&A answers into LM Arena competition style.

RULES:
1. Start DIRECTLY with the answer. No greetings, no preamble.
2. Be CONCISE. Cut all filler words.
3. Use step-by-step ONLY if the problem requires multiple steps.
4. State the final answer clearly at the end.
5. Use proper mathematical notation.
6. NEVER change mathematical values or results.
7. One-liners are fine for one-step problems.
8. Output ONLY the refined answer. No commentary, no markdown headers.

Examples:
  Q: "what is 2 + 2" → "2 + 2 = 4"
  Q: "what is the derivative of x^2" → "d/dx(x^2) = 2x. This follows from the power rule: d/dx(x^n)=nx^(n-1) with n=2."
  Q: "solve x^2 - 3x + 2 = 0" → "Factor: (x-1)(x-2) = 0\nSolutions: x = 1 or x = 2\nVerification:\n- x=1: 1^2-3(1)+2 = 0 ✓\n- x=2: 2^2-3(2)+2 = 0 ✓\n\nAnswer: x = 1, x = 2"
"""

def refine_answer(question: str, raw_answer: str, max_retries: int = 2) -> str:
    """Call DeepSeek to reformulate the answer in LM Arena style."""
    for attempt in range(max_retries):
        try:
            payload = json.dumps({
                "model": API_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Question: {question}\n\nRaw answer to refine:\n\n{raw_answer}"}
                ],
                "max_tokens": 512,
                "temperature": 0.1,
            }).encode('utf-8')
            
            req = urllib.request.Request(
                API_ENDPOINT,
                data=payload,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                text = data["choices"][0]["message"]["content"].strip()
                return text
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"  Failed: {e}")
                return raw_answer
            time.sleep(1)
    return raw_answer

def generate_style():
    from knowledge_base import PRE_COMPUTED as KB
    
    print(f"KB entries: {len(KB)}")
    print(f"API Key: {'present' if API_KEY else 'MISSING'}")
    print()
    
    if not API_KEY:
        print("ERROR: No DEEPSEEK_API_KEY found. Cannot generate styled answers.")
        return
    
    # Process entries that don't already have text_lm_arena
    to_process = []
    for key, value in KB.items():
        if "text_lm_arena" not in value:
            to_process.append((key, value))
    
    print(f"Entries to process: {len(to_process)}")
    print(f"(Already styled: {len(KB) - len(to_process)})")
    print()
    
    # Process a batch for testing
    batch_size = 20
    batch = to_process[:batch_size]
    
    print(f"Processing {len(batch)} entries as a test batch...")
    print()
    
    for i, (key, value) in enumerate(batch):
        raw = value["text"]
        styled = refine_answer(key, raw)
        
        if styled and styled != raw:
            # Add to the in-memory KB
            KB[key]["text_lm_arena"] = styled
            
        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(batch)} done...")
    
    print(f"\nProcessed {len(batch)} entries.")
    
    # Save the updated KB
    out_path = os.path.join(os.path.dirname(__file__), "knowledge_base.py")
    backup_path = os.path.join(os.path.dirname(__file__), "knowledge_base_backup.py")
    
    # Backup
    if os.path.exists(out_path) and not os.path.exists(backup_path):
        shutil.copy(out_path, backup_path)
        print(f"Backup saved: {backup_path}")
    
    # Write updated KB
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('#!/usr/bin/env python3\n')
        f.write(f'"""Knowledge Base — {len(KB)} entries with LM Arena styled answers"""\n')
        f.write('import math\nPHI=1.618033988749895;PI=math.pi;E=math.e\n\n')
        f.write('PRE_COMPUTED = {\n')
        for key, value in sorted(KB.items()):
            # Raw text
            raw = value["text"].replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            # Styled text (if available)
            styled = value.get("text_lm_arena", "")
            if styled:
                styled = styled.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            
            f.write(f'    "{key}": {{\n')
            f.write(f'        "text": "{raw}",\n')
            if styled:
                f.write(f'        "text_lm_arena": "{styled}",\n')
            f.write(f'        "coherence": {value["coherence"]},\n')
            f.write(f'        "domain": "{value["domain"]}"\n')
            f.write(f'    }},\n')
        f.write('}\n\nPRE_COMPUTED_NORMALIZED = {k.lower().strip(): v for k, v in PRE_COMPUTED.items()}\n')
    
    print(f"Written: {out_path}")
    print(f"\nNext: modify harmonic_math_engine.py to prefer text_lm_arena over text")
    print("Done.")

if __name__ == "__main__":
    generate_style()