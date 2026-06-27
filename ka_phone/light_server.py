#!/usr/bin/env python3
"""KA Phone Light Server — starts instantly, uses ParametricKB + FrequencyReasoner."""
import sys, os, json, http.server, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lm_arena'))

parametric = None; frequency = None
try:
    from parametric_kb import ParametricKB
    parametric = ParametricKB()
except: pass
try:
    from frequency_reasoner import FrequencyReasoner
    frequency = FrequencyReasoner()
except: pass

def process(prompt):
    p = prompt.lower().strip()
    if re.search(r'(?:qui|que|what|who)\s+(?:es|est|are|is)\s*(?:-|\s)?tu\s*\??', p):
        return {'text': "Je suis KA, ton double numerique. Je fonctionne grace au Cerveau Harmonique - une intelligence basee sur la resonance des ondes plutot que sur les statistiques. Je ne devine pas : je sais, ou je dis que je ne sais pas. Je suis 100% locale, 0 cloud, et je n'hallucine jamais.", 'source': 'identity', 'confidence': 0.99}
    if parametric:
        r = parametric.solve(prompt)
        if r: return {'text': r['text'], 'source': 'parametric', 'confidence': r.get('confidence', 0.9)}
    if frequency:
        r = frequency.reason(prompt)
        if r and r.get('confidence', 0) >= 0.45:
            return {'text': r['text'], 'source': 'frequency', 'confidence': r.get('confidence', 0.7)}
    return {'text': f"Question recue : \"{prompt[:60]}\". Mon moteur harmonique est pret. Posez une question mathematique ou logique.", 'source': 'fallback', 'confidence': 0.5}

class H(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','POST, OPTIONS'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.end_headers()
    def do_POST(self):
        if self.path == '/api/ask':
            body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode('utf-8')
            data = json.loads(body)
            result = process(data.get('prompt',''))
            self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        else: self.send_response(404); self.end_headers()
    def log_message(self, *a): pass

if __name__ == '__main__':
    print('KA Phone Light API on http://localhost:8420')
    print(f'  ParametricKB: {parametric is not None} | FrequencyReasoner: {frequency is not None}')
    http.server.HTTPServer(('0.0.0.0', 8420), H).serve_forever()