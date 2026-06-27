"""
API de Recherche Web Harmonique — Backend Python
=================================================
Alternative serveur au moteur JS côté client.
Utilise DuckDuckGo (gratuit) + aiohttp pour le fetch.

Usage:
    python search_api.py
    # Puis requêtes POST à http://localhost:8765/api/search
    # ou GET  à http://localhost:8765/api/search?q=...
    
    # Analyse d'URL :
    # POST http://localhost:8765/api/analyze-url
    # {"url": "https://example.com"}
"""

import asyncio
import json
import re
import time
import math
from urllib.parse import quote, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from html.parser import HTMLParser

# =========================================================================
# CONSTANTES HARMONIQUES
# =========================================================================

PHI = 1.618033988749895
ALPHA = 1.1755694591
B_1_PHI = 0.8506508083

# =========================================================================
# ANALYSEUR HARMONIQUE
# =========================================================================

class HarmonicAnalyzer:
    """Analyse harmonique 7D d'un texte"""
    
    def analyze(self, text):
        if not text or len(text) < 3:
            return [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
        
        # φ_ratio : diversité lexicale
        unique_words = len(set(w.lower() for w in words))
        phi_ratio = min(1.0, unique_words / max(1, len(words)) * PHI)
        
        # α_complexity : complexité syntaxique
        avg_sentence_len = len(words) / max(1, len(sentences))
        alpha_complexity = min(1.0, avg_sentence_len / 30)
        
        # k_reasoning : raisonnement (mots de liaison, arguments)
        reasoning_words = {'donc', 'car', 'parce', 'puisque', 'alors', 'si', 'alors',
                          'donc', 'ainsi', 'cependant', 'néanmoins', 'pourtant',
                          'cependant', 'en effet', 'par conséquent', 'because',
                          'therefore', 'thus', 'hence', 'consequently', 'since',
                          'although', 'however', 'nevertheless', 'moreover',
                          'furthermore', 'additionally', 'accordingly'}
        reasoning_count = sum(1 for w in words if w.lower() in reasoning_words)
        k_reasoning = min(1.0, reasoning_count / max(1, len(words)) * 20)
        
        # k_creative : créativité (métaphores, adjectifs rares)
        creative_words = {'comme', 'tel', 'ainsi', 'semble', 'paraît', 'ressemble',
                         'magnifique', 'sublime', 'extraordinaire', 'unique',
                         'like', 'as if', 'seems', 'appears', 'beautiful',
                         'splendid', 'magnificent', 'extraordinary', 'unique',
                         'metaphor', 'poetry', 'poetic', 'imaginary'}
        creative_count = sum(1 for w in words if w.lower() in creative_words)
        k_creative = min(1.0, creative_count / max(1, len(words)) * 15)
        
        # k_mathematical : précision mathématique
        math_count = len(re.findall(r'\d+[.,]?\d*', text))
        k_mathematical = min(1.0, math_count / max(1, len(words)) * 10)
        
        # k_factual : factualité (sources, citations, données)
        factual_words = {'selon', 'd\'après', 'étude', 'recherche', 'source',
                        'données', 'statistiques', 'pourcentage', 'étude',
                        'according', 'study', 'research', 'source', 'data',
                        'statistics', 'percentage', 'report', 'survey',
                        'analysis', 'findings', 'evidence', 'study shows'}
        factual_count = sum(1 for w in words if w.lower() in factual_words)
        has_quotes = len(re.findall(r'["""]', text)) > 0
        k_factual = min(1.0, (factual_count / max(1, len(words)) * 15) + (0.1 if has_quotes else 0))
        
        # k_code : code (mots techniques, syntaxe)
        code_words = {'function', 'class', 'def', 'import', 'return', 'if', 'else',
                     'for', 'while', 'var', 'let', 'const', 'int', 'float',
                     'string', 'array', 'object', 'null', 'true', 'false',
                     'void', 'public', 'private', 'static', 'void'}
        code_count = sum(1 for w in words if w.lower() in code_words)
        has_brackets = '{' in text or '}' in text
        k_code = min(1.0, (code_count / max(1, len(words)) * 20) + (0.2 if has_brackets else 0))
        
        return [
            round(phi_ratio, 4),
            round(alpha_complexity, 4),
            round(k_reasoning, 4),
            round(k_creative, 4),
            round(k_mathematical, 4),
            round(k_factual, 4),
            round(k_code, 4)
        ]

# =========================================================================
# MOTEUR DE RECHERCHE
# =========================================================================

class WebSearchEngine:
    """Moteur de recherche web via DuckDuckGo"""
    
    def __init__(self):
        self.analyzer = HarmonicAnalyzer()
        self.cache = {}
    
    def search(self, query, max_results=8):
        """Recherche sur le web et retourne les résultats analysés"""
        cache_key = query.lower().strip()
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < 60:
                return cached['data']
        
        try:
            raw_results = self._search_duckduckgo(query, max_results)
            analyzed = []
            
            for result in raw_results:
                sig = self.analyzer.analyze(result.get('snippet', '') + ' ' + result.get('title', ''))
                result['signature'] = sig
                result['dominant_category'] = self._categorize(sig)
                result['confidence'] = min(1.0, math.sqrt(sum(v*v for v in sig)) * PHI / 3)
                analyzed.append(result)
            
            # Signature de la requête
            query_sig = self.analyzer.analyze(query)
            
            # Classement par résonance
            for r in analyzed:
                r['resonance'] = self._compute_resonance(query_sig, r['signature'])
            analyzed.sort(key=lambda x: x['resonance'], reverse=True)
            
            # Synthèse
            synthesis = self._synthesize(analyzed, query)
            
            result = {
                'query': query,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'totalResults': len(analyzed),
                'results': analyzed,
                'synthesis': synthesis,
                'querySignature': query_sig
            }
            
            self.cache[cache_key] = {'data': result, 'timestamp': time.time()}
            return result
            
        except Exception as e:
            return {
                'query': query,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'totalResults': 0,
                'results': [],
                'synthesis': f'Erreur: {str(e)}',
                'querySignature': [0, 0, 0, 0, 0, 0, 0]
            }
    
    def _search_duckduckgo(self, query, max_results):
        """Requête DuckDuckGo API"""
        url = f'https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1&t=harmonic_ai'
        req = Request(url, headers={'User-Agent': 'HarmonicAI/1.0'})
        
        with urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        results = []
        
        # Abstract
        if data.get('Abstract') and len(data['Abstract']) > 50:
            results.append({
                'title': data.get('Heading', 'Résumé'),
                'url': data.get('AbstractURL', ''),
                'snippet': data['Abstract'],
                'source': 'duckduckgo_abstract'
            })
        
        # RelatedTopics
        for topic in data.get('RelatedTopics', []):
            if len(results) >= max_results:
                break
            if 'Result' in topic:
                results.append({
                    'title': topic.get('Text', '').split(' - ')[0] if topic.get('Text') else topic['Result'],
                    'url': topic.get('FirstURL', ''),
                    'snippet': topic.get('Text', topic['Result']),
                    'source': 'duckduckgo'
                })
            if 'Topics' in topic and len(results) < max_results:
                for sub in topic['Topics']:
                    if len(results) >= max_results:
                        break
                    results.append({
                        'title': sub.get('Text', '').split(' - ')[0] if sub.get('Text') else sub.get('Result', ''),
                        'url': sub.get('FirstURL', ''),
                        'snippet': sub.get('Text', sub.get('Result', '')),
                        'source': 'duckduckgo'
                    })
        
        return results[:max_results]
    
    def _compute_resonance(self, sig1, sig2):
        """Calcule la résonance entre deux signatures"""
        dot = sum(a * b for a, b in zip(sig1, sig2))
        norm1 = math.sqrt(sum(a * a for a in sig1))
        norm2 = math.sqrt(sum(b * b for b in sig2))
        if norm1 == 0 or norm2 == 0:
            return 0
        return min(1.0, dot / (norm1 * norm2))
    
    def _categorize(self, sig):
        """Catégorisation harmonique"""
        phi, alpha, reasoning, creative, math_s, factual, code = sig
        cats = {
            'Scientifique': math_s * 0.4 + factual * 0.3 + reasoning * 0.3,
            'Créatif': creative * 0.6 + phi * 0.4,
            'Technique': code * 0.5 + math_s * 0.3 + factual * 0.2,
            'Analyse': reasoning * 0.5 + factual * 0.3 + phi * 0.2,
            'Factuel': factual * 0.6 + math_s * 0.2 + reasoning * 0.2
        }
        return max(cats, key=cats.get)
    
    def _synthesize(self, results, query):
        """Synthèse harmonique multi-sources"""
        if not results:
            return 'Aucun résultat trouvé.'
        
        top = results[:5]
        avg_resonance = sum(r['resonance'] for r in top) / len(top)
        
        cat_count = {}
        for r in top:
            cat = r['dominant_category']
            cat_count[cat] = cat_count.get(cat, 0) + 1
        main_cat = max(cat_count, key=cat_count.get)
        
        signatures = [r['signature'] for r in top]
        fused = [sum(sig[i] for sig in signatures) / len(signatures) for i in range(7)]
        consensus = min(1.0, math.sqrt(sum(v*v for v in fused)) * PHI / 3)
        
        return {
            'summary': f'Synthèse de {len(top)} sources — catégorie dominante : {main_cat}',
            'consensus': round(consensus, 4),
            'avgResonance': round(avg_resonance, 4),
            'mainCategory': main_cat,
            'sourceCount': len(top),
            'topSources': [{
                'title': r['title'],
                'url': r['url'],
                'resonance': r['resonance'],
                'category': r['dominant_category']
            } for r in top]
        }

# =========================================================================
# ANALYSEUR D'URL
# =========================================================================

class HTMLTextExtractor(HTMLParser):
    """Extrait le texte brut du HTML"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'nav', 'footer', 'header'}
        self.in_skip = False
    
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.in_skip = True
    
    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.in_skip = False
    
    def handle_data(self, data):
        if not self.in_skip:
            self.text.append(data.strip())
    
    def get_text(self):
        return ' '.join(t for t in self.text if t)


class URLHarmonicAnalyzer:
    """Analyse une URL et retourne sa signature harmonique"""
    
    def __init__(self):
        self.analyzer = HarmonicAnalyzer()
        self.cache = {}
    
    def analyze(self, url):
        """Analyse une URL"""
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        cache_key = url
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < 300:
                return cached['data']
        
        try:
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml'
            })
            
            with urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='replace')
            
            # Extraire titre
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ''
            
            # Extraire description
            desc_match = re.search(
                r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
                html, re.IGNORECASE
            )
            description = desc_match.group(1).strip() if desc_match else ''
            
            # Extraire texte
            extractor = HTMLTextExtractor()
            extractor.feed(html)
            text = extractor.get_text()
            text = re.sub(r'\s+', ' ', text).strip()[:5000]
            
            # Analyse harmonique
            sig = self.analyzer.analyze(text)
            
            # Mots-clés
            words = text.lower().split()
            stop_words = {'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et',
                         'est', 'sont', 'dans', 'pour', 'sur', 'avec', 'par', 'pas',
                         'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to',
                         'for', 'of', 'by', 'with', 'from', 'is', 'are', 'was'}
            freq = {}
            for w in words:
                w = re.sub(r'[.,!?;:()"\']', '', w)
                if len(w) > 3 and w not in stop_words:
                    freq[w] = freq.get(w, 0) + 1
            keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            result = {
                'url': url,
                'title': title,
                'description': description,
                'wordCount': len(text.split()),
                'signature': sig,
                'keywords': [f'{w} ({c})' for w, c in keywords],
                'dominantCategory': self._categorize(sig),
                'success': True
            }
            
            self.cache[cache_key] = {'data': result, 'timestamp': time.time()}
            return result
            
        except Exception as e:
            return {
                'url': url,
                'success': False,
                'error': str(e),
                'signature': [0, 0, 0, 0, 0, 0, 0]
            }
    
    def _categorize(self, sig):
        phi, alpha, reasoning, creative, math_s, factual, code = sig
        cats = {
            'Article Scientifique': math_s * 0.4 + factual * 0.3 + reasoning * 0.3,
            'Article Créatif': creative * 0.5 + phi * 0.3 + reasoning * 0.2,
            'Actualité': factual * 0.5 + phi * 0.2 + reasoning * 0.3,
            'Analyse Technique': code * 0.4 + math_s * 0.3 + factual * 0.3,
            'Opinion/Éditorial': creative * 0.4 + reasoning * 0.4 + phi * 0.2
        }
        return max(cats, key=cats.get)


# =========================================================================
# SERVEUR HTTP
# =========================================================================

class SearchAPIHandler(BaseHTTPRequestHandler):
    """Gestionnaire HTTP pour l'API de recherche"""
    
    search_engine = WebSearchEngine()
    url_analyzer = URLHarmonicAnalyzer()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/search':
            query = self._get_param(parsed.query, 'q')
            if query:
                result = self.search_engine.search(query)
                self._json_response(result)
            else:
                self._json_response({'error': 'Paramètre q requis'}, 400)
        
        elif parsed.path == '/api/health':
            self._json_response({
                'status': 'ok',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'version': '1.0',
                'harmonic': True
            })
        
        else:
            self._json_response({'error': 'Not found'}, 404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            self._json_response({'error': 'Invalid JSON'}, 400)
            return
        
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/search':
            query = data.get('q') or data.get('query')
            if query:
                result = self.search_engine.search(query)
                self._json_response(result)
            else:
                self._json_response({'error': 'Paramètre q ou query requis'}, 400)
        
        elif parsed.path == '/api/analyze-url':
            url = data.get('url')
            if url:
                result = self.url_analyzer.analyze(url)
                self._json_response(result)
            else:
                self._json_response({'error': 'Paramètre url requis'}, 400)
        
        else:
            self._json_response({'error': 'Not found'}, 404)
    
    def _get_param(self, query_string, name):
        for part in query_string.split('&'):
            if '=' in part:
                k, v = part.split('=', 1)
                if k == name:
                    from urllib.parse import unquote
                    return unquote(v)
        return None
    
    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def log_message(self, format, *args):
        print(f'[API] {args[0]} {args[1]} {args[2]}')


def main():
    port = 8765
    server = HTTPServer(('0.0.0.0', port), SearchAPIHandler)
    print(f'🌐 API de Recherche Harmonique démarrée sur http://localhost:{port}')
    print(f'   GET  /api/search?q=...  → Recherche web')
    print(f'   POST /api/search        → Recherche web (JSON)')
    print(f'   POST /api/analyze-url   → Analyse d\'URL')
    print(f'   GET  /api/health        → Santé du serveur')
    print()
    print('Exemples :')
    print(f'   curl "http://localhost:{port}/api/search?q=intelligence+artificielle"')
    print(f'   curl -X POST http://localhost:{port}/api/analyze-url -H "Content-Type: application/json" -d \'{{"url": "https://example.com"}}\'')
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nArrêt du serveur.')
        server.server_close()


if __name__ == '__main__':
    main()