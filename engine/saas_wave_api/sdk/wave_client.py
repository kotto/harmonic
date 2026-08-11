"""
sdk.wave_client — client Python zéro dépendance du service Harmonic Compute
===========================================================================
Usage :
    from saas_wave_api.sdk.wave_client import WaveClient
    c = WaveClient(base_url='http://localhost:8000', api_key='hwu_...')
    c.encode('lumiere')
"""

import json
import urllib.error
import urllib.request


class WaveClient:
    """Client minimal (stdlib) de l'API /v1/*."""

    def __init__(self, base_url: str = 'http://localhost:8000', api_key: str = ''):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    # ── transport ────────────────────────────────────────────────────────────
    def _call(self, path: str, body=None, method=None):
        url = self.base_url + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header('Content-Type', 'application/json')
        if self.api_key:
            req.add_header('X-API-Key', self.api_key)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode()
            try:
                detail = json.loads(detail)
            except Exception:
                pass
            raise ApiError(e.code, detail) from None

    def _post(self, path, body):
        return self._call(path, body, method='POST')

    # ── auth ─────────────────────────────────────────────────────────────────
    def register(self, email: str) -> dict:
        """Crée une clé API (plan free)."""
        return self._post('/v1/auth/register', {'email': email})

    # ── meta ─────────────────────────────────────────────────────────────────
    def status(self) -> dict:
        return self._call('/v1/meta/status')

    def benchmark(self) -> dict:
        return self._call('/v1/meta/benchmark')

    # ── primitives ───────────────────────────────────────────────────────────
    def encode(self, entity: str) -> dict:
        return self._post('/v1/wave/encode', {'entity': entity})

    def decode(self, wave_or_entity, vocabulary=None, top_k: int = 5) -> dict:
        body = {'wave': wave_or_entity} if isinstance(wave_or_entity, dict) \
            else {'entity': wave_or_entity}
        body.update({'vocabulary': vocabulary or [], 'top_k': top_k})
        return self._post('/v1/wave/decode', body)

    def bind(self, a, b) -> dict:
        return self._post('/v1/wave/bind', {'a': a, 'b': b})

    def unbind(self, c, b) -> dict:
        return self._post('/v1/wave/unbind', {'c': c, 'b': b})

    def superpose(self, items, weights=None) -> dict:
        return self._post('/v1/wave/superpose', {'items': items, 'weights': weights})

    def resonate(self, a, b) -> dict:
        return self._post('/v1/wave/resonate', {'a': a, 'b': b})

    def rotate(self, a, angle: float) -> dict:
        return self._post('/v1/wave/rotate', {'a': a, 'angle': angle})

    def interfere(self, a, b, epsilon: float = 0.15) -> dict:
        return self._post('/v1/wave/interfere', {'a': a, 'b': b, 'epsilon': epsilon})

    def diffract(self, a, inverse: bool = False) -> dict:
        return self._post('/v1/wave/diffract', {'a': a, 'inverse': inverse})

    def filter(self, a, mode: str = 'lowpass', cutoff: float = 0.5) -> dict:
        return self._post('/v1/wave/filter', {'a': a, 'mode': mode, 'cutoff': cutoff})

    def phase_shift(self, a, shift: float) -> dict:
        return self._post('/v1/wave/phase_shift', {'a': a, 'shift': shift})

    def emerge(self, items, temperature: float = 0.5) -> dict:
        return self._post('/v1/wave/emerge', {'items': items, 'temperature': temperature})

    def solve(self, expression: str) -> dict:
        return self._post('/v1/wave/solve', {'expression': expression})

    # ── mémoire ──────────────────────────────────────────────────────────────
    def memory_store(self, facts) -> dict:
        return self._post('/v1/memory/store', {'facts': facts})

    def memory_query(self, query: str, top_k: int = 5) -> dict:
        return self._post('/v1/memory/query', {'query': query, 'top_k': top_k})

    def memory_stats(self) -> dict:
        return self._call('/v1/memory/stats')


class ApiError(Exception):
    """Erreur API (statut HTTP + détail)."""

    def __init__(self, status: int, detail):
        self.status = status
        self.detail = detail
        super().__init__(f'HTTP {status}: {detail}')
