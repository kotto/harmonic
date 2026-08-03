#!/usr/bin/env python3
"""
mcp_server_stdio.py — Serveur MCP KA Enterprise (transport stdio)
=================================================================

Lance le serveur MCP en stdio (framing Content-Length) pour les clients
MCP locaux : Claude Desktop, Cursor, assistants, etc.

Usage :
  KA_API_KEY=<clé du tenant> python mcp_server_stdio.py
  KA_DATA_DIR=<chemin> python mcp_server_stdio.py   (défaut: ../data/enterprise)

Exemple de configuration Claude Desktop (claude_desktop_config.json) :
  { "mcpServers": { "ka-enterprise": {
        "command": "python",
        "args": ["/opt/ka-enterprise/mcp/mcp_server_stdio.py"],
        "env": { "KA_API_KEY": "votre_clé_tenant" } } } }
"""

import os
import sys
import json
from pathlib import Path

# Permettre l'exécution depuis le dossier mcp/ OU depuis backend/enterprise/
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_protocol import McpSession, read_stdio_message, write_stdio_message
from mcp_tools import tools_provider, tool_executor

SERVER_INFO = {'name': 'ka-enterprise-mcp', 'version': '4.1.0'}


def build_context() -> dict:
    """Contexte d'exécution : moteur partagé sur le data_dir + tenant par clé."""
    from ka_enterprise_core import EnterpriseEngine

    data_dir = Path(os.environ.get('KA_DATA_DIR', '')).resolve() if os.environ.get('KA_DATA_DIR') \
        else Path(__file__).resolve().parent.parent / 'data' / 'enterprise'
    data_dir.mkdir(parents=True, exist_ok=True)

    engine = EnterpriseEngine(data_dir=str(data_dir))
    tenant = None
    api_key = os.environ.get('KA_API_KEY', '').strip()
    if api_key:
        tenant = engine.get_tenant_by_api_key(api_key)
        if not tenant:
            print(f"⚠ KA_API_KEY inconnue — session en lecture seule sans tenant",
                  file=sys.stderr)
    return {'engine': engine, 'tenant': tenant, 'user': None,
            'data_dir': data_dir}


def main() -> int:
    session = McpSession(tools_provider, tool_executor, SERVER_INFO)
    ctx = build_context()

    if ctx['tenant']:
        print(f"🧠 KA Enterprise MCP (stdio) — tenant : {ctx['tenant'].name}",
              file=sys.stderr)
    else:
        print("🧠 KA Enterprise MCP (stdio) — configurez KA_API_KEY pour "
              "l'authentification", file=sys.stderr)
    print(f"   Outils disponibles : {len([t for t in tools_provider(ctx)['tools']])}",
          file=sys.stderr)
    sys.stderr.flush()

    while True:
        try:
            message = read_stdio_message()
            if message is None:
                break
            response = session.handle(message, ctx)
            if response is not None:
                write_stdio_message(response)
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:  # garder la session vivante
            write_stdio_message(session._error(
                None, -32603, f'Erreur interne: {e}'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
