#!/usr/bin/env python3
"""
mcp_client_demo.py — Client MCP KA Enterprise (démonstration + tests)
=====================================================================

Dialogue avec le serveur MCP (agents spécialisés) en transport stdio ou
streamable HTTP, avec assertions (mode --test).

Usage :
  # stdio : lance le serveur local (même data_dir que le serveur HTTP)
  python mcp_client_demo.py --mode stdio --api-key <clé> [--test]

  # http : se connecte à un serveur KA Enterprise distant
  python mcp_client_demo.py --mode http --base http://127.0.0.1:8767 \
      --api-key <clé> [--test]
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSPORT STDiO (framing Content-Length, comme mcp_protocol)
# ═══════════════════════════════════════════════════════════════════════════════

class StdioClient:
    def __init__(self, api_key: str, data_dir: str = ''):
        env = dict(os.environ)
        if api_key:
            env['KA_API_KEY'] = api_key
        if data_dir:
            env['KA_DATA_DIR'] = data_dir
        self.proc = subprocess.Popen(
            [sys.executable, str(HERE / 'mcp_server_stdio.py')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, env=env)

    def send(self, payload: dict) -> dict:
        data = json.dumps(payload).encode('utf-8')
        self.proc.stdin.write(f'Content-Length: {len(data)}\r\n\r\n'.encode())
        self.proc.stdin.write(data)
        self.proc.stdin.flush()
        headers = {}
        while True:
            line = self.proc.stdout.readline()
            if line in (b'\r\n', b'\n'):
                break
            key, _, value = line.decode().partition(':')
            headers[key.strip().lower()] = value.strip()
        body = self.proc.stdout.read(int(headers['content-length']))
        return json.loads(body)

    def close(self):
        self.proc.terminate()


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSPORT HTTP (streamable)
# ═══════════════════════════════════════════════════════════════════════════════

class HttpClient:
    def __init__(self, base: str, api_key: str):
        self.base = base.rstrip('/')
        self.api_key = api_key

    def send(self, payload: dict) -> dict:
        req = urllib.request.Request(
            self.base + '/mcp', data=json.dumps(payload).encode(),
            method='POST')
        req.add_header('Content-Type', 'application/json')
        if self.api_key:
            req.add_header('X-API-Key', self.api_key)
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return {'jsonrpc': '2.0', 'id': payload.get('id'),
                    'error': {'code': e.code,
                              'message': e.read().decode()[:200]}}


# ═══════════════════════════════════════════════════════════════════════════════
# SCÉNARIO DE DÉMONSTRATION / TEST
# ═══════════════════════════════════════════════════════════════════════════════

def call(client, msg_id, method, params=None):
    payload = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
    if params is not None:
        payload['params'] = params
    return client.send(payload)


def extract_result(resp: dict) -> dict:
    assert 'error' not in resp, f"MCP error: {resp['error']}"
    return resp.get('result', {})


def run(client, test: bool = False) -> int:
    print('── 1. initialize ───────────────────────────────────────────')
    r = extract_result(call(client, 1, 'initialize',
                            {'protocolVersion': '2025-06-18',
                             'capabilities': {},
                             'clientInfo': {'name': 'demo', 'version': '1.0'}}))
    print(f"   serveur : {r['serverInfo']['name']} v{r['serverInfo']['version']} "
          f"· protocol {r['protocolVersion']}")

    print('── 2. tools/list ───────────────────────────────────────────')
    r = extract_result(call(client, 2, 'tools/list'))
    names = [t['name'] for t in r['tools']]
    print(f"   {len(names)} outils : {', '.join(names[:6])}…")
    if test:
        assert len(names) >= 12, f"attendu ≥ 12 outils, obtenu {len(names)}"
        assert 'agent_handle' in names and 'query_data' in names
        assert 'ask_department' in names and 'export_excel' in names

    print('── 3. CONCOURS : agent_handle « liste des clients » ────────')
    r = extract_result(call(client, 3, 'tools/call',
                            {'name': 'agent_handle',
                             'arguments': {'question': 'liste des clients'}}))
    text = json.loads(r['content'][0]['text'])
    print(f"   agent gagnant : {text.get('agent_nom')} "
          f"· {text.get('count', '?')} lignes")
    if test:
        assert text.get('agent') == 'data', f"attendu agent data, obtenu {text.get('agent')}"
        assert text.get('count', 0) >= 1, 'liste vide'

    print('── 4. CONCOURS : « rédige un email sur la situation » ──────')
    r = extract_result(call(client, 4, 'tools/call',
                            {'name': 'agent_handle',
                             'arguments': {'question': 'rédige un email sur la situation'}}))
    text = json.loads(r['content'][0]['text'])
    print(f"   agent gagnant : {text.get('agent_nom')} · format {text.get('format')} "
          f"· {text.get('facts_utilises', 0)} faits")
    if test:
        assert text.get('agent') == 'redaction', f"attendu redaction, obtenu {text.get('agent')}"
        assert text.get('format') == 'email'

    print('── 5. ask_department direct (gate + chaînon D) ─────────────')
    r = extract_result(call(client, 5, 'tools/call',
                            {'name': 'list_departments', 'arguments': {}}))
    depts = json.loads(r['content'][0]['text']).get('departments', [])
    if not depts:
        print('   (aucun département — saute)')
    else:
        dept_id = depts[0]['id']
        r = extract_result(call(client, 5, 'tools/call',
                                {'name': 'ask_department',
                                 'arguments': {'department_id': dept_id,
                                               'question': 'test de la procédure'}}))
        text = json.loads(r['content'][0]['text'])
        print(f"   {text.get('answer', '')[:60]}… "
              f"confiance {text.get('confidence')} "
              f"· chaînon D: {text.get('enrichissement_planifie', False)}")
        if test:
            assert 'confidence' in text and 'answer' in text

    print('── 6. ping ─────────────────────────────────────────────────')
    r = extract_result(call(client, 6, 'ping'))
    print('   pong')

    print('\n✅ DÉMO MCP TERMINÉE' + (' — TOUTES LES ASSERTIONS PASSENT' if test else ''))
    return 0


def main():
    ap = argparse.ArgumentParser(description='Client MCP KA Enterprise')
    ap.add_argument('--mode', choices=['stdio', 'http'], default='stdio')
    ap.add_argument('--base', default='http://127.0.0.1:8767')
    ap.add_argument('--api-key', default='')
    ap.add_argument('--data-dir', default='',
                    help='data_dir du moteur (mode stdio ; défaut : data/enterprise)')
    ap.add_argument('--test', action='store_true')
    args = ap.parse_args()

    client = (StdioClient(args.api_key, args.data_dir) if args.mode == 'stdio'
              else HttpClient(args.base, args.api_key))
    try:
        return run(client, test=args.test)
    finally:
        if isinstance(client, StdioClient):
            client.close()


if __name__ == '__main__':
    sys.exit(main())
