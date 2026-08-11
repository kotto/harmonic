#!/usr/bin/env python3
"""
wave_keys.py — Gestion des clés API du service de calcul harmonique (SaaS)
===========================================================================
Le service /api/wave/* exige une clé API (X-API-Key) avec quota journalier.

Usage :
    python -m ka_server.tools.wave_keys create <email> [--plan free|pro|enterprise]
    python -m ka_server.tools.wave_keys list
    python -m ka_server.tools.wave_keys revoke <key>
    python -m ka_server.tools.wave_keys usage

Plans : free 100 req/j · pro 5 000 req/j · enterprise 50 000 req/j
"""

import argparse
import json
import sys
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ENGINE_DIR))

from ka_server.routes.wave import PLANS, _keys_path, _load_json, _save_json, _usage_path, create_key  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description='Clés API — service de calcul harmonique')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_create = sub.add_parser('create', help='Créer une clé API')
    p_create.add_argument('email')
    p_create.add_argument('--plan', default='free', choices=list(PLANS))
    p_create.add_argument('--limit', type=int, default=None, help='Quota journalier (défaut : plan)')

    sub.add_parser('list', help='Lister les clés')
    sub.add_parser('usage', help='Consommation par clé')

    p_revoke = sub.add_parser('revoke', help='Révoquer une clé')
    p_revoke.add_argument('key')

    args = parser.parse_args()

    if args.cmd == 'create':
        key = create_key(args.email, args.plan, args.limit)
        print(f"✅ Clé créée pour {args.email} [plan {args.plan}]")
        print(f"   X-API-Key : {key}")
        print(f"   Quota journalier : {args.limit or PLANS[args.plan]['daily_limit']} requêtes")
        print("   À utiliser : curl -H 'X-API-Key: <clé>' http://localhost:8765/api/wave/status")

    elif args.cmd == 'list':
        keys = _load_json(_keys_path(), {})
        if not keys:
            print("Aucune clé — créez-en une : python -m ka_server.tools.wave_keys create demo@example.com")
            return
        for email, info in keys.items():
            print(f"  {email:40s} {info['key']}  [plan {info['plan']}]  créée {info['created']}")

    elif args.cmd == 'usage':
        usage = _load_json(_usage_path(), {})
        keys = _load_json(_keys_path(), {})
        if not usage:
            print("Aucune consommation enregistrée.")
            return
        for key, days in usage.items():
            email = next((e for e, k in keys.items() if k['key'] == key), '?')
            total = sum(days.values())
            print(f"  {email:40s} {total:6d} req  {json.dumps(days, ensure_ascii=False)}")

    elif args.cmd == 'revoke':
        keys = _load_json(_keys_path(), {})
        email = next((e for e, k in keys.items() if k['key'] == args.key), None)
        if email is None:
            print(f"❌ Clé introuvable : {args.key}")
            sys.exit(1)
        del keys[email]
        _save_json(_keys_path(), keys)
        print(f"✅ Clé révoquée : {email}")


if __name__ == '__main__':
    main()
