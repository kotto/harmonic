#!/usr/bin/env python3
"""Test simple du serveur web"""

import asyncio
from aiohttp import web
from pathlib import Path

async def hello(request):
    return web.Response(text="✅ Serveur HCV PRO actif!\nURL: http://127.0.0.1:7890/ui/HarmonicPhone.html")

app = web.Application()
app.add_routes([
    web.get('/', hello),
    web.static('/ui', Path(__file__).parent / 'ui')
])

if __name__ == '__main__':
    print("🚀 Démarrage serveur test sur http://127.0.0.1:7890")
    web.run_app(app, host='0.0.0.0', port=7890)