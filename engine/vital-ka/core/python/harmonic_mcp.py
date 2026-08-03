"""
🔌 MCP Server — Harmonic AI pour l'écosystème IA
===================================================
Serveur MCP (Model Context Protocol) exposant les capacités
de Harmonic AI à tout client MCP-compatible.

CLIENTS COMPATIBLES :
  - Claude Desktop (Anthropic)
  - Cursor IDE
  - Continue.dev
  - Tout client MCP standard

OUTILS EXPOSÉS :
  - wave_debug      : Diagnostic ondulatoire de bug
  - kb_search       : Recherche dans le KB 110K+
  - hologram_build  : Création autonome d'hologramme
  - hologram_quality: Score qualité d'un hologramme

RESSOURCES :
  - kb://{domain}   : Faits extraits du KB pour un domaine

USAGE :
  python harmonic_mcp.py
  
  Puis configurer dans Claude Desktop :
  {
    "mcpServers": {
      "harmonic-ai": {
        "command": "python",
        "args": ["path/to/harmonic_mcp.py"]
      }
    }
  }
"""

import sys, os, json, time, asyncio
from pathlib import Path
from typing import Any, Dict, List

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# ════════════════════════════════════════════════════════════════
# MCP PROTOCOL — Implémentation légère (stdio JSON-RPC)
# ════════════════════════════════════════════════════════════════

class MCPServer:
    """
    Serveur MCP minimaliste — JSON-RPC 2.0 sur stdio.
    """
    
    def __init__(self, name: str = "harmonic-ai", version: str = "1.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, dict] = {}
        self.resources: Dict[str, dict] = {}
        self._initialized = False
    
    def register_tool(self, name: str, description: str, input_schema: dict, handler):
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
            "handler": handler,
        }
    
    def register_resource(self, uri_pattern: str, name: str, description: str, handler):
        self.resources[uri_pattern] = {
            "uri": uri_pattern,
            "name": name,
            "description": description,
            "handler": handler,
        }
    
    async def run(self):
        """Boucle principale — lit JSON-RPC sur stdin, répond sur stdout."""
        # Utiliser stdin/stdout en mode binaire
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())
        
        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                
                request = json.loads(line.decode())
                response = await self._handle(request)
                
                if response:
                    writer.write((json.dumps(response) + "\n").encode())
                    await writer.drain()
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in dir() else None,
                    "error": {"code": -1, "message": str(e)}
                }
                writer.write((json.dumps(error_response) + "\n").encode())
                await writer.drain()
    
    async def _handle(self, request: dict) -> dict:
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})
        
        if method == "initialize":
            return self._handle_initialize(req_id, params)
        elif method == "tools/list":
            return self._handle_tools_list(req_id)
        elif method == "tools/call":
            return await self._handle_tools_call(req_id, params)
        elif method == "resources/list":
            return self._handle_resources_list(req_id)
        elif method == "resources/read":
            return await self._handle_resources_read(req_id, params)
        elif method == "notifications/initialized":
            self._initialized = True
            return None
        else:
            return {"jsonrpc": "2.0", "id": req_id, 
                    "error": {"code": -32601, "message": f"Méthode inconnue: {method}"}}
    
    def _handle_initialize(self, req_id, params):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": self.name,
                    "version": self.version,
                },
                "capabilities": {
                    "tools": {},
                    "resources": {},
                },
            },
        }
    
    def _handle_tools_list(self, req_id):
        tools = []
        for t in self.tools.values():
            tools.append({
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"],
            })
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}
    
    async def _handle_tools_call(self, req_id, params):
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        tool = self.tools.get(tool_name)
        if not tool:
            return {"jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32602, "message": f"Outil inconnu: {tool_name}"}}
        
        try:
            result = tool["handler"](arguments)
            if asyncio.iscoroutine(result):
                result = await result
            
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": f"Erreur: {e}"}
                    ],
                    "isError": True,
                }
            }
    
    def _handle_resources_list(self, req_id):
        resources = []
        for r in self.resources.values():
            resources.append({
                "uri": r["uri"],
                "name": r["name"],
                "description": r["description"],
            })
        return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": resources}}
    
    async def _handle_resources_read(self, req_id, params):
        uri = params.get("uri", "")
        resource = self.resources.get(uri)
        if not resource:
            # Chercher par pattern
            for pattern, r in self.resources.items():
                if pattern.replace("{domain}", "") in uri:
                    resource = r
                    break
        
        if not resource:
            return {"jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32602, "message": f"Ressource inconnue: {uri}"}}
        
        try:
            result = resource["handler"](uri)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "contents": [
                        {"uri": uri, "mimeType": "application/json",
                         "text": json.dumps(result, indent=2, ensure_ascii=False)}
                    ]
                }
            }
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -1, "message": str(e)}}


# ════════════════════════════════════════════════════════════════
# HANDLERS — Logique métier
# ════════════════════════════════════════════════════════════════

# Lazy imports
_ai = None
_kb = None
_agent = None

def _get_ai():
    global _ai
    if _ai is None:
        from harmonic_ai_v2 import HarmonicAIv2
        _ai = HarmonicAIv2()
    return _ai

def _get_kb():
    global _kb
    if _kb is None:
        from hologram_builder_agent import KnowledgeBaseSource
        _kb = KnowledgeBaseSource()
        _kb.load()
    return _kb

def _get_agent():
    global _agent
    if _agent is None:
        from hologram_builder_agent import HologramBuilderAgent
        _agent = HologramBuilderAgent()
    return _agent


def handle_wave_debug(args: dict) -> dict:
    """Diagnostique un bug via la méthode ondulatoire."""
    symptom = args.get("symptom", "")
    if not symptom:
        return {"error": "symptom requis"}
    
    ai = _get_ai()
    result = ai.debug(symptom)
    return {
        "symptom": symptom[:120],
        "diagnosis": result.interference_type,
        "confidence": round(result.confidence, 3),
        "explanation": result.explanation,
        "strategy": result.strategy,
        "action": result.action,
        "methodology": "Pipeline 4 étapes : Traduire → Diagnostiquer → Prescrire → Vérifier",
    }


def handle_kb_search(args: dict) -> dict:
    """Recherche dans le KB par mots-clés."""
    query = args.get("query", "")
    max_results = args.get("max_results", 10)
    
    if not query:
        return {"error": "query requis"}
    
    kb = _get_kb()
    facts = kb.extract_by_domain(query, max_facts=max_results)
    
    return {
        "query": query,
        "results_count": len(facts),
        "facts": [
            {"subject": f[0], "relation": f[1], "object": f[2], "sector": f[3]}
            for f in facts[:max_results]
        ],
        "source": f"KB Harmonic AI ({len(kb._facts):,} faits)",
    }


def handle_hologram_build(args: dict) -> dict:
    """Crée un hologramme spécialisé pour un domaine."""
    domain = args.get("domain", "")
    author = args.get("author", "mcp-user")
    
    if not domain:
        return {"error": "domain requis"}
    
    agent = _get_agent()
    report = agent.build(domain, author=author, target_score=60)
    
    return {
        "domain": domain,
        "status": report.status,
        "iterations": report.iterations,
        "facts_count": report.facts_count,
        "initial_score": report.initial_score,
        "final_score": report.final_score,
        "improvements": report.improvements[-5:],
    }


def handle_hologram_quality(args: dict) -> dict:
    """Évalue la qualité d'un hologramme."""
    facts = args.get("facts", [])
    if not facts:
        return {"error": "facts requis"}
    
    from hologram_quality import QualityScorer, FactValidator
    validator = FactValidator()
    validation = validator.validate_batch(facts)
    quality = QualityScorer.compute_total(facts)
    
    return {
        "validation": validation,
        "quality": quality,
    }


def handle_kb_resource(uri: str) -> dict:
    """Ressource KB : extrait les faits pour un domaine."""
    # Extraire le domaine de l'URI : kb://genetique
    domain = uri.replace("kb://", "").replace("kb:", "")
    
    kb = _get_kb()
    facts = kb.extract_by_domain(domain, max_facts=50)
    
    return {
        "domain": domain,
        "facts_count": len(facts),
        "total_kb_size": len(kb._facts),
        "sample": [
            {"subject": f[0], "relation": f[1], "object": f[2], "sector": f[3]}
            for f in facts[:20]
        ],
    }


# ════════════════════════════════════════════════════════════════
# SERVEUR
# ════════════════════════════════════════════════════════════════

def create_mcp_server() -> MCPServer:
    """Crée et configure le serveur MCP."""
    server = MCPServer(name="harmonic-ai", version="2.0")
    
    # Outils
    server.register_tool(
        "wave_debug",
        "Diagnostique un bug informatique par la méthode ondulatoire (4 étapes). "
        "Retourne le type d'interférence, la stratégie et l'action corrective. "
        "0% d'hallucination. Fonctionne en français et en anglais.",
        {
            "type": "object",
            "properties": {
                "symptom": {
                    "type": "string",
                    "description": "Description du symptôme (ex: 'NullPointerException in UserService', 'fuite de mémoire après 24h')"
                }
            },
            "required": ["symptom"]
        },
        handle_wave_debug,
    )
    
    server.register_tool(
        "kb_search",
        "Recherche des connaissances dans la base de Harmonic AI (110 000+ faits). "
        "Utile pour obtenir des informations factuelles sur n'importe quel sujet.",
        {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Mots-clés ou domaine de recherche (ex: 'génétique', 'Python', 'Rome antique')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Nombre maximum de résultats (défaut: 10, max: 50)",
                    "default": 10
                }
            },
            "required": ["query"]
        },
        handle_kb_search,
    )
    
    server.register_tool(
        "hologram_build",
        "Crée automatiquement un hologramme spécialisé sur un domaine. "
        "L'agent extrait les faits du KB, les valide, score la qualité, "
        "et enrichit l'hologramme jusqu'à atteindre un score satisfaisant.",
        {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Domaine de l'hologramme (ex: 'génétique', 'python', 'histoire de France')"
                },
                "author": {
                    "type": "string",
                    "description": "Identifiant de l'auteur (défaut: 'mcp-user')",
                    "default": "mcp-user"
                }
            },
            "required": ["domain"]
        },
        handle_hologram_build,
    )
    
    server.register_tool(
        "hologram_quality",
        "Évalue la qualité d'une liste de faits (score 0-100). "
        "Mesure la cohérence, complétude, unicité, diversité et structure.",
        {
            "type": "object",
            "properties": {
                "facts": {
                    "type": "array",
                    "description": "Liste de faits au format [sujet, relation, objet, secteur]"
                }
            },
            "required": ["facts"]
        },
        handle_hologram_quality,
    )
    
    # Ressources
    server.register_resource(
        "kb://{domain}",
        "KB Domain Facts",
        "Faits extraits du KB Harmonic AI pour un domaine spécifique",
        handle_kb_resource,
    )
    
    return server


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    """Lance le serveur MCP en mode stdio."""
    server = create_mcp_server()
    print(f"🔌 Harmonic AI MCP Server v{server.version}", file=sys.stderr)
    print(f"   Outils : {list(server.tools.keys())}", file=sys.stderr)
    print(f"   Ressources : {list(server.resources.keys())}", file=sys.stderr)
    print(f"   En attente de connexions...", file=sys.stderr)
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
