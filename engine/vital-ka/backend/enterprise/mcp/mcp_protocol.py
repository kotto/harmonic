#!/usr/bin/env python3
"""
mcp_protocol.py — Cœur du serveur MCP (Model Context Protocol) de KA Enterprise
===============================================================================

Implémentation du protocole MCP (JSON-RPC 2.0) en stdlib pure — aucune
dépendance. Conforme au transport stdio (framing Content-Length) et au
transport streamable HTTP (POST /mcp).

Méthodes supportées :
  - initialize / notifications/initialized  (négociation de session)
  - tools/list                               (catalogue des outils exposés)
  - tools/call                               (exécution d'un outil)
  - ping                                     (gardien de session)

Les outils sont déclarés dans mcp_tools.py, les agents spécialisés dans
mcp_agents.py. Le gate anti-hallucination et le chaînon D (complétion
pilotée par l'usage) s'appliquent à chaque appel.
"""

import json
import sys
from typing import Any, Callable, Dict, List, Optional

PROTOCOL_VERSION = '2025-06-18'
SERVER_NAME = 'ka-enterprise-mcp'
SERVER_VERSION = '4.1.0'

# Codes d'erreur JSON-RPC (réservés MCP : -32600..-32603, -32000..-32099)
ERR_PARSE = -32700
ERR_INVALID_REQUEST = -32600
ERR_METHOD_NOT_FOUND = -32601
ERR_INVALID_PARAMS = -32602
ERR_INTERNAL = -32603
ERR_TOOL_NOT_FOUND = -32002
ERR_TOOL_EXECUTION = -32003


class McpError(Exception):
    """Erreur MCP/JSON-RPC avec code."""

    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class McpSession:
    """
    Une session MCP : connaît le catalogue d'outils et sait traiter un
    message JSON-RPC. Le contexte d'exécution (ctx) est fourni par le
    transport (moteur + identité du tenant pour l'authentification).
    """

    def __init__(self, tools_provider: Callable[[Any], Dict],
                 tool_executor: Callable[[str, Dict, Any], Any],
                 server_info: Optional[Dict] = None):
        """
        tools_provider(ctx) -> {'tools': [{'name', 'description', 'inputSchema'}]}
        tool_executor(name, arguments, ctx) -> résultat sérialisable
        """
        self._tools_provider = tools_provider
        self._tool_executor = tool_executor
        self._server_info = server_info or {
            'name': SERVER_NAME, 'version': SERVER_VERSION}
        self._initialized = False

    # ── Traitement d'un message JSON-RPC ───────────────────────────────────────
    def handle(self, message: Dict, ctx: Any) -> Optional[Dict]:
        """Traite un message. Retourne la réponse (None pour les notifications)."""
        if not isinstance(message, dict) or message.get('jsonrpc') != '2.0':
            return self._error(None, ERR_INVALID_REQUEST,
                               'Message JSON-RPC 2.0 requis')

        method = message.get('method')
        msg_id = message.get('id')
        params = message.get('params') or {}

        # Notifications (pas d'id, pas de réponse)
        if msg_id is None:
            try:
                if method == 'notifications/initialized':
                    self._initialized = True
                elif method == 'notifications/cancelled':
                    pass
                else:
                    return self._error(None, ERR_METHOD_NOT_FOUND,
                                       f'Méthode inconnue: {method}')
            except McpError as e:
                return self._error(None, e.code, e.message)
            return None

        try:
            if method == 'initialize':
                self._initialized = True
                return self._result(msg_id, {
                    'protocolVersion': PROTOCOL_VERSION,
                    'capabilities': {'tools': {'listChanged': False}},
                    'serverInfo': self._server_info,
                    'instructions': (
                        "KA Enterprise — serveur MCP des données privées. "
                        "Chaque outil retourne confiance et sources ; une "
                        "réponse incertaine déclenche un enrichissement "
                        "en arrière-plan (chaînon D)."),
                })
            if method == 'ping':
                return self._result(msg_id, {})
            if method == 'tools/list':
                return self._result(msg_id, self._tools_provider(ctx))
            if method == 'tools/call':
                return self._call_tool(msg_id, params, ctx)
            return self._error(msg_id, ERR_METHOD_NOT_FOUND,
                               f'Méthode inconnue: {method}')
        except McpError as e:
            return self._error(msg_id, e.code, e.message, e.data)
        except Exception as e:  # pragma: no cover — sécurité
            return self._error(msg_id, ERR_INTERNAL, f'Erreur interne: {e}')

    def _call_tool(self, msg_id: Any, params: Dict, ctx: Any) -> Dict:
        name = params.get('name', '')
        arguments = params.get('arguments') or {}
        if not name:
            raise McpError(ERR_INVALID_PARAMS, 'name requis')
        if not isinstance(arguments, dict):
            raise McpError(ERR_INVALID_PARAMS, 'arguments doit être un objet')
        result = self._tool_executor(name, arguments, ctx)
        if result is None:
            raise McpError(ERR_TOOL_NOT_FOUND, f'Outil inconnu: {name}')
        # Contenu MCP : texte (JSON lisible) + contenu structuré
        payload = json.dumps(result, ensure_ascii=False, default=str)
        content = [{'type': 'text', 'text': payload}]
        if isinstance(result, dict):
            content.append({'type': 'structured', 'structured': result})
        return self._result(msg_id, {'content': content, 'isError': False})

    # ── Aides JSON-RPC ─────────────────────────────────────────────────────────
    @staticmethod
    def _result(msg_id: Any, result: Any) -> Dict:
        return {'jsonrpc': '2.0', 'id': msg_id, 'result': result}

    @staticmethod
    def _error(msg_id: Any, code: int, message: str, data: Any = None) -> Dict:
        err = {'code': code, 'message': message}
        if data is not None:
            err['data'] = data
        return {'jsonrpc': '2.0', 'id': msg_id, 'error': err}


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSPORT STDIO — framing LSP (Content-Length), fallback ligne simple
# ═══════════════════════════════════════════════════════════════════════════════

def read_stdio_message(stream=None) -> Optional[Dict]:
    """Lit un message JSON-RPC depuis stdin (framing Content-Length)."""
    stream = stream or sys.stdin.buffer
    headers: Dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in (b'\r\n', b'\n'):
            break
        try:
            key, _, value = line.decode('utf-8').partition(':')
            headers[key.strip().lower()] = value.strip()
        except UnicodeDecodeError:
            continue

    if 'content-length' in headers:
        length = int(headers['content-length'])
        body = stream.read(length)
    else:
        # Fallback : JSON sur une seule ligne (utile pour les tests)
        line = stream.readline()
        if not line:
            return None
        body = line.strip()
    if not body:
        return None
    return json.loads(body)


def write_stdio_message(message: Dict, stream=None) -> None:
    """Écrit un message JSON-RPC avec le framing Content-Length."""
    stream = stream or sys.stdout.buffer
    data = json.dumps(message, ensure_ascii=False).encode('utf-8')
    stream.write(f'Content-Length: {len(data)}\r\n\r\n'.encode('utf-8'))
    stream.write(data)
    stream.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSPORT HTTP — helper streamable (SSE) pour la route Flask /mcp
# ═══════════════════════════════════════════════════════════════════════════════

def sse_response(result: Dict) -> str:
    """Sérialise une réponse MCP en flux SSE (event: message + event: end)."""
    payload = json.dumps(result, ensure_ascii=False, default=str)
    return (f'event: message\ndata: {payload}\n\n'
            f'event: end\ndata: [DONE]\n\n')
