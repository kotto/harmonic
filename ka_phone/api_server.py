#!/usr/bin/env python3
"""
KA Phone API Server — Minimal backend for the KA Phone app
============================================================
Exposes a single endpoint /api/ask that uses the full pipeline:
  ParametricKB -> SemanticMatcher -> FrequencyReasoner -> HybridWriter

Usage: python api_server.py
Runs on http://localhost:8420
"""

import sys, os, json, http.server, urllib.parse, re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lm_arena'))

# Load engines (graceful fallback if some are missing)
pipelines = {}

try:
    from parametric_kb import ParametricKB
    pipelines['parametric'] = ParametricKB()
except ImportError:
    pass

try:
    from harmonic_math_engine import HarmonicMathEngine
    from semantic_matcher import HybridMatcher
    engine = HarmonicMathEngine()
    pipelines['semantic'] = HybridMatcher(engine)
except ImportError:
    pass

try:
    from frequency_reasoner import FrequencyReasoner
    pipelines['frequency'] = FrequencyReasoner()
except ImportError:
    pass

try:
    from hybrid_writer import HybridWriter
    pipelines['writer'] = HybridWriter(langue='fr')
except ImportError:
    pass


def process_question(prompt: str) -> dict:
    """Process a question through the full pipeline."""
    p = prompt.lower().strip()
    
    # Special case: identity questions
    if re.search(r'(?:qui|que|what|who)\s+(?:es|est|are|is)\s*(?:-|\s)?tu\s*\??', p):
        return {
            'text': 'Je suis KA, ton double numérique. Je fonctionne grâce au Cerveau Harmonique — une intelligence basée sur la résonance des ondes plutôt que sur les statistiques. Je ne devine pas : je sais, ou je dis que je ne sais pas. Je suis 100% locale, 0 cloud, et je n\'hallucine jamais.',
            'source': 'identity',
            'confidence': 0.99,
            'time_ms': 0
        }
    
    if re.search(r'(?:comment|how)\s+(?:tu|vous)\s+(?:fonctionne|marche)', p):
        return {
            'text': 'Je fonctionne avec un moteur harmonique SOPC. Contrairement aux IA classiques qui "devinent" le prochain mot, je stocke mes connaissances dans un hologramme 256×256 où chaque concept est une onde. Quand tu me poses une question, je fais résonner ta question dans cet hologramme, et les connaissances qui "vibrent" à la même fréquence émergent naturellement. Zéro hallucination, 100% déterministe, et tout tourne sur ton téléphone.',
            'source': 'identity',
            'confidence': 0.99,
            'time_ms': 0
        }
    
    # Try ParametricKB
    if 'parametric' in pipelines:
        result = pipelines['parametric'].solve(prompt)
        if result:
            return {'text': result['text'], 'source': 'parametric', 
                    'confidence': result.get('confidence', 0.9), 'time_ms': 0}
    
    # Try Semantic Matcher
    if 'semantic' in pipelines:
        result = pipelines['semantic'].find_best(prompt)
        if result:
            return {'text': result['text'], 'source': 'semantic',
                    'confidence': result.get('confidence', 0.8), 'time_ms': 0}
    
    # Try Frequency Reasoner
    if 'frequency' in pipelines:
        result = pipelines['frequency'].reason(prompt)
        if result and result.get('confidence', 0) >= 0.5:
            return {'text': result['text'], 'source': 'frequency',
                    'confidence': result.get('confidence', 0.7), 'time_ms': 0}
    
    # Try HybridWriter for general conversation
    if 'writer' in pipelines:
        result = pipelines['writer'].write(prompt, raw_answer='', domain='general')
        return {'text': result, 'source': 'writer', 'confidence': 0.5, 'time_ms': 0}
    
    # Fallback
    return {
        'text': f'Je comprends votre question : "{prompt[:80]}". Mon moteur harmonique est activé mais je n\'ai pas trouvé de réponse immédiate dans ma base. Essayez de reformuler ou posez une question mathématique.',
        'source': 'fallback',
        'confidence': 0.3,
        'time_ms': 0
    }


class APIHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/ask':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
            prompt = data.get('prompt', '')
            
            result = process_question(prompt)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Silent logging


if __name__ == '__main__':
    port = 8420
    print(f'KA Phone API Server running on http://localhost:{port}')
    print(f'   Pipeline: ParametricKB={("parametric" in pipelines)} | '
          f'Semantic={("semantic" in pipelines)} | '
          f'Frequency={("frequency" in pipelines)} | '
          f'Writer={("writer" in pipelines)}')
    http.server.HTTPServer(('0.0.0.0', port), APIHandler).serve_forever()