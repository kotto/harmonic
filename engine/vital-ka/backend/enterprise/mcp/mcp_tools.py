#!/usr/bin/env python3
"""
mcp_tools.py — Catalogue des outils MCP de KA Enterprise
==========================================================

Les outils exposent les compétences du moteur (Q&A holographique, données →
tableaux/Excel, composition de textes, ingestion, conformité, onboarding) au
protocole MCP. Chaque outil :
  - exige un tenant authentifié (ctx['tenant'] via clé API / SSO) ;
  - vérifie l'appartenance des départements au tenant ;
  - retourne un résultat sérialisable (confiance, sources, agrégats…) ;
  - branche le gate anti-hallucination sur le chaînon D (completion_queue).
"""

import base64
import io
import json
import time
from typing import Any, Callable, Dict, List, Optional

try:
    from mcp.mcp_protocol import (McpError, ERR_INVALID_PARAMS,
                                  ERR_TOOL_EXECUTION, ERR_TOOL_NOT_FOUND)
except ImportError:  # exécution en module direct (stdio)
    from mcp_protocol import (McpError, ERR_INVALID_PARAMS,
                              ERR_TOOL_EXECUTION, ERR_TOOL_NOT_FOUND)

# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXTE D'EXÉCUTION
# ctx = {'engine': EnterpriseEngine, 'tenant': EnterpriseTenant|None,
#        'user': EnterpriseUser|None, 'data_dir': Path}
# ═══════════════════════════════════════════════════════════════════════════════


def _require_tenant(ctx: Dict) -> Any:
    tenant = ctx.get('tenant')
    if not tenant:
        raise McpError(ERR_TOOL_EXECUTION,
                       'Authentification requise — fournissez la clé API du tenant')
    return tenant


def _require_department(ctx: Dict, department_id: str) -> Any:
    """Valide que le département existe et appartient au tenant."""
    tenant = _require_tenant(ctx)
    engine = ctx['engine']
    dept = engine.departments.get(department_id)
    if not dept:
        raise McpError(ERR_TOOL_EXECUTION, f'Département inconnu: {department_id}')
    if dept.tenant_id != tenant.id:
        raise McpError(ERR_TOOL_EXECUTION,
                       f'Accès refusé — le département {department_id} '
                       f'n\'appartient pas au tenant {tenant.id}')
    user = ctx.get('user')
    if user and user.department_ids and department_id not in user.department_ids:
        raise McpError(ERR_TOOL_EXECUTION,
                       'Accès non autorisé à ce département (RBAC)')
    return dept


# ═══════════════════════════════════════════════════════════════════════════════
# OUTILS — définitions (JSON Schema) + exécution
# ═══════════════════════════════════════════════════════════════════════════════

def _t(name: str, description: str, props: Dict, required: List[str] = []) -> Dict:
    return {'name': name, 'description': description,
            'inputSchema': {'type': 'object', 'properties': props,
                            'required': required}}


def _handler_ask_department(args: Dict, ctx: Dict) -> Dict:
    department_id = args.get('department_id', '')
    question = args.get('question', '').strip()
    if not department_id or not question:
        raise McpError(ERR_INVALID_PARAMS, 'department_id et question requis')
    dept = _require_department(ctx, department_id)
    engine = ctx['engine']
    user_id = ctx['user'].id if ctx.get('user') else 'mcp'
    result = engine.ask(question, department_id, user_id=user_id)
    out = {
        'department': dept.name,
        'department_id': department_id,
        'question': question,
        'answer': result.answer,
        'confidence': round(float(result.confidence), 3),
        'sources': result.sources,
        'elapsed_ms': result.elapsed_ms,
        'admitted_uncertainty': bool(result.admitted_uncertainty),
    }
    # ⚡ Gate → chaînon D : une réponse sans réponse réelle (refus calibré
    # ou confiance faible) est enregistrée ; aux seuils (facette 2× /
    # sujet 3×), la COMPLÉTION se déclenche : Wikipedia + facettes
    # manquantes, couverture recalculée (auto-apprentissage).
    try:
        from enterprise_completion import should_register_miss
        if should_register_miss(result):
            from completion_queue import register_miss
            miss = register_miss(question, sujet=dept.name)
            out['enrichissement_planifie'] = True
            if miss.get('triggered'):
                from enterprise_completion import complete_department_background
                complete_department_background(engine, department_id, dept.name,
                                               facettes=[miss['facette']])
                out['completion_lancee'] = True
    except Exception:
        out['enrichissement_planifie'] = False
    return out


def _handler_ask_tenant(args: Dict, ctx: Dict) -> Dict:
    question = args.get('question', '').strip()
    if not question:
        raise McpError(ERR_INVALID_PARAMS, 'question requise')
    tenant = _require_tenant(ctx)
    results = ctx['engine'].ask_cross_department(question, tenant.id)
    return {
        'question': question,
        'results': [{
            'department': r.department,
            'department_id': r.department_id if hasattr(r, 'department_id') else None,
            'confidence': round(float(r.confidence), 3),
            'answer': r.answer,
            'sources': r.sources,
        } for r in results],
    }


def _handler_query_data(args: Dict, ctx: Dict) -> Dict:
    department_id = args.get('department_id', '')
    question = args.get('question', '').strip()
    if not department_id or not question:
        raise McpError(ERR_INVALID_PARAMS, 'department_id et question requis')
    _require_department(ctx, department_id)
    from enterprise_deliverables import query_data
    return query_data(ctx['engine'], department_id, question)


def _handler_export_excel(args: Dict, ctx: Dict) -> Dict:
    department_id = args.get('department_id', '')
    question = args.get('question', '').strip()
    fmt = args.get('format', 'xlsx')
    if not department_id or not question:
        raise McpError(ERR_INVALID_PARAMS, 'department_id et question requis')
    _require_department(ctx, department_id)
    from enterprise_deliverables import build_excel, export_csv, query_data
    if fmt == 'csv':
        data = query_data(ctx['engine'], department_id, question)
        text = export_csv(data)
        payload = base64.b64encode(text.encode('utf-8-sig')).decode()
        return {'format': 'csv', 'filename': f'{department_id}.csv',
                'mime': 'text/csv', 'base64': payload, 'count': data['count'],
                'aggregates': data['aggregates']}
    bio, filename = build_excel(ctx['engine'], department_id, question)
    return {'format': 'xlsx', 'filename': filename,
            'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'base64': base64.b64encode(bio.getvalue()).decode(),
            'count': None, 'aggregates': None}


def _handler_compose_document(args: Dict, ctx: Dict) -> Dict:
    department_id = args.get('department_id', '')
    brief = args.get('brief', '').strip()
    if not department_id or not brief:
        raise McpError(ERR_INVALID_PARAMS, 'department_id et brief requis')
    dept = _require_department(ctx, department_id)
    from enterprise_deliverables import compose_document
    doc = compose_document(ctx['engine'], department_id, brief,
                           doc_format=args.get('format', 'rapport'),
                           destinataire=args.get('destinataire'),
                           objet=args.get('objet'))
    doc['department_id'] = department_id
    return doc


def _handler_summarize(args: Dict, ctx: Dict) -> Dict:
    department_id = args.get('department_id', '')
    if not department_id:
        raise McpError(ERR_INVALID_PARAMS, 'department_id requis')
    _require_department(ctx, department_id)
    from enterprise_deliverables import summarize_department
    return summarize_department(ctx['engine'], department_id)


def _handler_ingest_text(args: Dict, ctx: Dict) -> Dict:
    department_id = args.get('department_id', '')
    text = args.get('text', '')
    if not department_id or not text:
        raise McpError(ERR_INVALID_PARAMS, 'department_id et text requis')
    dept = _require_department(ctx, department_id)
    engine = ctx['engine']
    source = args.get('source') or 'mcp'
    count = engine.ingest_text(department_id, text, source=source)
    return {'department': dept.name, 'department_id': department_id,
            'facts_ingested': count, 'total_facts': dept.fact_count}


def _handler_list_departments(args: Dict, ctx: Dict) -> Dict:
    tenant = _require_tenant(ctx)
    depts = ctx['engine'].list_departments(tenant.id)
    return {'tenant': tenant.name, 'tenant_id': tenant.id,
            'departments': depts}


def _handler_department_coverage(args: Dict, ctx: Dict) -> Dict:
    department_id = args.get('department_id', '')
    if not department_id:
        raise McpError(ERR_INVALID_PARAMS, 'department_id requis')
    dept = _require_department(ctx, department_id)
    engine = ctx['engine']
    try:
        from facet_coverage import coverage_texts
        facts = engine.facts.get(department_id, [])
        texts = [f.text for f in facts]
        cov = coverage_texts(texts, dept.name) if texts else {}
        return {'department': dept.name, 'department_id': department_id,
                'facts': len(texts),
                'couverture': round(float(cov.get('couverture', 0.0)), 3),
                'facettes_manquantes': cov.get('manquantes', [])}
    except Exception as e:
        raise McpError(ERR_TOOL_EXECUTION, f'Couverture: {e}')


def _handler_check_seal(args: Dict, ctx: Dict) -> Dict:
    a = args.get('department_a', '')
    b = args.get('department_b', '')
    if not a or not b:
        raise McpError(ERR_INVALID_PARAMS, 'department_a et department_b requis')
    _require_department(ctx, a)
    _require_department(ctx, b)
    return ctx['engine'].verify_seal(a, b)


def _handler_audit_recent(args: Dict, ctx: Dict) -> Dict:
    tenant = _require_tenant(ctx)
    limit = int(args.get('limit', 25))
    engine = ctx['engine']
    entries = [e for e in engine.audit_log if e.tenant_id == tenant.id][-limit:]
    return {
        'tenant': tenant.name,
        'entries': [{
            'timestamp': e.timestamp if hasattr(e, 'timestamp') else '',
            'department_id': e.department_id,
            'user': e.user_id,
            'question': e.question,
            'confidence': round(float(e.confidence), 3),
            'response_id': e.response_id,
        } for e in entries][::-1],
    }


def _handler_dashboard(args: Dict, ctx: Dict) -> Dict:
    tenant = _require_tenant(ctx)
    data = ctx['engine'].get_dashboard(tenant.id)
    data['tenant'] = tenant.name
    data['tenant_id'] = tenant.id
    return data


def _handler_analyze_environment(args: Dict, ctx: Dict) -> Dict:
    description = args.get('description', '').strip()
    if not description or len(description) < 20:
        raise McpError(ERR_INVALID_PARAMS,
                       'description requise (au moins 20 caractères)')
    from enterprise_onboard import analyze_environment
    return analyze_environment(description, args.get('secteur'))


def _handler_create_environment(args: Dict, ctx: Dict) -> Dict:
    """Crée un environnement complet (tenant + départements) — comme le portail
    d'onboarding : accessible avec une clé API administrateur existante."""
    name = args.get('name', '').strip()
    email = args.get('email', '').strip()
    description = args.get('description', '').strip()
    if not name or not email or not description:
        raise McpError(ERR_INVALID_PARAMS, 'name, email et description requis')
    from enterprise_onboard import create_environment
    result = create_environment(ctx['engine'], name, email, description,
                                args.get('secteur'),
                                holograms=args.get('holograms'))
    if 'error' in result:
        raise McpError(ERR_TOOL_EXECUTION, result['error'])
    return result


def _handler_agent_handle(args: Dict, ctx: Dict) -> Dict:
    """
    LE CONCOURS DES AGENTS : route la question vers l'agent spécialisé le
    plus pertinent (Data, Rédaction, Conformité, Onboarding, Support) et
    exécute sa compétence — le tout en un seul appel MCP.
    """
    question = args.get('question', '').strip()
    if not question:
        raise McpError(ERR_INVALID_PARAMS, 'question requise')
    try:
        from mcp.mcp_agents import handle_agent
    except ImportError:  # exécution en module direct (stdio)
        from mcp_agents import handle_agent
    return handle_agent(question, ctx,
                        agent=args.get('agent'),
                        department_id=args.get('department_id'),
                        extra={k: args.get(k) for k in
                               ('format', 'objet', 'destinataire', 'secteur',
                                'name', 'email', 'limit', 'holograms')
                               if args.get(k) is not None})


# ═══════════════════════════════════════════════════════════════════════════════
# CATALOGUE
# ═══════════════════════════════════════════════════════════════════════════════

TOOL_DEFS: List[Dict] = [
    _t('list_departments',
       'Liste les départements (hologrammes) du tenant authentifié.',
       {}),
    _t('ask_department',
       'Pose une question au savoir privé d\'un département (gate anti-hallucination : '
       'confiance + sources ; une réponse incertaine déclenche un enrichissement en '
       'arrière-plan).',
       {'department_id': {'type': 'string', 'description': 'id du département'},
        'question': {'type': 'string'}},
       ['department_id', 'question']),
    _t('ask_tenant',
       'Pose une question à TOUS les départements du tenant — résultats triés par '
       'confiance (consensus inter-hologrammes).',
       {'question': {'type': 'string'}}, ['question']),
    _t('query_data',
       'Question de DONNÉES sur un département : retourne un tableau (colonnes, lignes) '
       'et des agrégats (compte, somme, moyenne, min, max) selon l\'intention de la '
       'question (« liste des clients », « chiffre d\'affaires total »…).',
       {'department_id': {'type': 'string'}, 'question': {'type': 'string'}},
       ['department_id', 'question']),
    _t('export_excel',
       'Télécharge les données d\'un département en fichier Excel (.xlsx : feuilles '
       'Données + Résumé) ou CSV — retourné en base64.',
       {'department_id': {'type': 'string'},
        'question': {'type': 'string', 'description': 'question de données (liste, agrégat)'},
        'format': {'type': 'string', 'enum': ['xlsx', 'csv'], 'default': 'xlsx'}},
       ['department_id', 'question']),
    _t('compose_document',
       'Prépare un texte structuré depuis les données privées : email, rapport, '
       'compte_rendu, lettre, note — en français corrigé.',
       {'department_id': {'type': 'string'},
        'brief': {'type': 'string', 'description': 'sujet du document'},
        'format': {'type': 'string', 'enum': ['email', 'rapport', 'compte_rendu',
                                              'lettre', 'note'], 'default': 'rapport'},
        'objet': {'type': 'string'}, 'destinataire': {'type': 'string'}},
       ['department_id', 'brief']),
    _t('summarize_department',
       'Synthèse du savoir d\'un département (prose + décompte par source).',
       {'department_id': {'type': 'string'}}, ['department_id']),
    _t('ingest_text',
       'Ingère un texte dans l\'hologramme d\'un département (source = provenance).',
       {'department_id': {'type': 'string'}, 'text': {'type': 'string'},
        'source': {'type': 'string', 'default': 'mcp'}},
       ['department_id', 'text']),
    _t('department_coverage',
       'Couverture par facettes d\'un département (complétude du savoir) + facettes '
       'manquantes.',
       {'department_id': {'type': 'string'}}, ['department_id']),
    _t('check_seal',
       'Vérifie l\'étanchéité entre deux départements (aucune fuite inter-hologrammes).',
       {'department_a': {'type': 'string'}, 'department_b': {'type': 'string'}},
       ['department_a', 'department_b']),
    _t('audit_recent',
       'Journal d\'audit récent du tenant (questions, confiances, horodatage).',
       {'limit': {'type': 'integer', 'default': 25}}),
    _t('dashboard',
       'Indicateurs du tenant : départements, faits, requêtes, confiance moyenne, '
       'top départements.',
       {}),
    _t('analyze_environment',
       'Analyse une description d\'environnement d\'entreprise → secteurs détectés + '
       'hologrammes proposés (agent Onboarding).',
       {'description': {'type': 'string'}, 'secteur': {'type': 'string'}},
       ['description']),
    _t('create_environment',
       'Crée un environnement complet : tenant + départements avec seed initial '
       '(agent Onboarding, comme le portail /onboard).',
       {'name': {'type': 'string'}, 'email': {'type': 'string'},
        'description': {'type': 'string'}, 'secteur': {'type': 'string'},
        'holograms': {'type': 'array', 'items': {'type': 'string'}}},
       ['name', 'email', 'description']),
    _t('agent_handle',
       'CONCOURS DES AGENTS : route la question vers l\'agent spécialisé le plus '
       'pertinent (🧠 Data, ✍️ Rédaction, 🕵️ Conformité, 🌱 Onboarding, '
       '💬 Support) et exécute sa compétence en un seul appel — avec gate et '
       'chaînon D.',
       {'question': {'type': 'string', 'description': 'la demande en langage naturel'},
        'agent': {'type': 'string', 'enum': ['data', 'redaction', 'conformite',
                                             'onboarding', 'support'],
                  'description': 'forcer un agent (sinon concours automatique)'},
        'department_id': {'type': 'string'},
        'format': {'type': 'string', 'enum': ['email', 'rapport', 'compte_rendu',
                                              'lettre', 'note']},
        'objet': {'type': 'string'}, 'destinataire': {'type': 'string'},
        'secteur': {'type': 'string'}, 'limit': {'type': 'integer'}},
       ['question']),
]

_HANDLERS: Dict[str, Callable] = {
    'list_departments': _handler_list_departments,
    'ask_department': _handler_ask_department,
    'ask_tenant': _handler_ask_tenant,
    'query_data': _handler_query_data,
    'export_excel': _handler_export_excel,
    'compose_document': _handler_compose_document,
    'summarize_department': _handler_summarize,
    'ingest_text': _handler_ingest_text,
    'department_coverage': _handler_department_coverage,
    'check_seal': _handler_check_seal,
    'audit_recent': _handler_audit_recent,
    'dashboard': _handler_dashboard,
    'analyze_environment': _handler_analyze_environment,
    'create_environment': _handler_create_environment,
    'agent_handle': _handler_agent_handle,
}


def tools_provider(ctx: Dict) -> Dict:
    """Provider tools/list pour McpSession."""
    return {'tools': TOOL_DEFS}


def tool_executor(name: str, arguments: Dict, ctx: Dict) -> Any:
    """Exécuteur tools/call pour McpSession."""
    handler = _HANDLERS.get(name)
    if handler is None:
        raise McpError(ERR_TOOL_NOT_FOUND, f'Outil inconnu: {name}')
    t0 = time.perf_counter()
    result = handler(arguments, ctx)
    if isinstance(result, dict):
        result['_meta'] = {'elapsed_ms': round((time.perf_counter() - t0) * 1000, 1)}
    return result
