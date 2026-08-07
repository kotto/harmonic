#!/usr/bin/env python3
"""
mcp_agents.py — Agents spécialisés de KA Enterprise (concours d'agents)
=======================================================================

Chaque agent spécialisé expose un rôle métier et un ensemble d'outils MCP.
Une question entrante fait CONCOURIR les agents : chacun score les mots-clés
de sa spécialité, le meilleur score exécute (le support gagne en fallback).

  - 🧠 Agent Data        : chiffres, listes, tableaux, agrégats, Excel
  - ✍️ Agent Rédaction   : emails, rapports, comptes-rendus, lettres, notes
  - 🕵️ Agent Conformité  : audit, journal, étanchéité, couverture, indicateurs
  - 🌱 Agent Onboarding  : analyse d'environnement, création d'hologrammes
  - 💬 Agent Support     : toute question sur le savoir des départements

Le routage est déterministe (0 LLM) ; les réponses passent par le gate
anti-hallucination et le chaînon D (complétion pilotée par l'usage).
"""

import json
import re
from typing import Any, Dict, List, Optional

try:
    from mcp.mcp_protocol import McpError, ERR_INVALID_PARAMS, ERR_TOOL_EXECUTION
except ImportError:  # exécution en module direct (stdio)
    from mcp_protocol import McpError, ERR_INVALID_PARAMS, ERR_TOOL_EXECUTION


def _tool_executor():
    """tool_executor avec import robuste (package mcp.* ou module direct)."""
    try:
        from mcp.mcp_tools import tool_executor
    except ImportError:
        from mcp_tools import tool_executor
    return tool_executor

# ═══════════════════════════════════════════════════════════════════════════════
# LES AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

AGENTS: Dict[str, Dict] = {
    'data': {
        'nom': '🧠 Agent Data',
        'role': 'Chiffres, listes, tableaux, agrégats et Excel sur les données privées',
        'keywords': [
            'combien', 'nombre', 'total', 'somme', 'moyenne', 'maximum',
            'minimum', 'liste', 'listes', 'tableau', 'tableaux', 'clients',
            'factures', 'montant', 'montants', 'stock', 'chiffre', 'ca ',
            'stats', 'statistiques', 'excel', 'csv', 'agregat', 'agrégat',
            'recapitulatif', 'récapitulatif', 'effectif', 'volume',
        ],
        'tools': ['query_data', 'export_excel', 'ask_department'],
    },
    'redaction': {
        'nom': '✍️ Agent Rédaction',
        'role': 'Emails, rapports, comptes-rendus, lettres et notes rédigés depuis les données',
        'keywords': [
            'email', 'courriel', 'rapport', 'compte rendu', 'compte-rendu',
            'lettre', 'note', 'redige', 'rédige', 'redaction', 'rédaction',
            'ecris', 'écris', 'prepare', 'prépare', 'resume', 'résume',
            'synthese', 'synthèse', 'document', 'docx', 'courrier', 'objet',
        ],
        'tools': ['compose_document', 'summarize_department'],
    },
    'conformite': {
        'nom': '🕵️ Agent Conformité',
        'role': 'Audit, journal, étanchéité inter-départements, couverture, indicateurs de sécurité',
        'keywords': [
            'audit', 'journal', 'logs', 'conformite', 'conformité', 'securite',
            'sécurité', 'etanche', 'étanche', 'etalite', 'étanchéité',
            'couverture', 'facette', 'facettes', 'kpi', 'indicateur',
            'indicateurs', 'rbac', 'acces', 'accès', 'traçabilite',
            'traçabilité', 'trace', 'traces', 'verrou', 'isolement',
        ],
        'tools': ['dashboard', 'audit_recent', 'check_seal',
                  'department_coverage', 'list_departments'],
    },
    'onboarding': {
        'nom': '🌱 Agent Onboarding',
        'role': 'Analyse d\'environnement, proposition et création d\'hologrammes',
        'keywords': [
            'environnement', 'creer', 'créer', 'nouveau', 'nouvelle',
            'onboarding', 'hologramme', 'hologrammes', 'propose', 'propose-moi',
            'secteur', 'description de mon', 'mon entreprise', 'mon activite',
        ],
        'tools': ['analyze_environment', 'create_environment',
                  'list_departments'],
    },
    'support': {
        'nom': '💬 Agent Support',
        'role': 'Répond à toute question sur le savoir des départements (Q&A, gate, consensus)',
        'keywords': [],
        'tools': ['ask_department', 'ask_tenant', 'list_departments'],
    },
}

# Formats de documents détectables dans une question (agent Rédaction)
_FORMAT_KEYWORDS = [
    ('email', ['email', 'courriel', 'mail']),
    ('compte_rendu', ['compte rendu', 'compte-rendu', 'cr de', 'reunion',
                      'réunion', 'réunion']),
    ('lettre', ['lettre', 'courrier']),
    ('note', ['note interne', 'note de service', 'note']),
    ('rapport', ['rapport']),
]


def _normalize(text: str) -> str:
    s = text.lower()
    for a, b in [('é', 'e'), ('è', 'e'), ('ê', 'e'), ('ë', 'e'), ('à', 'a'),
                 ('â', 'a'), ('î', 'i'), ('ï', 'i'), ('ô', 'o'), ('ù', 'u'),
                 ('û', 'u'), ('ç', 'c'), ('œ', 'oe'), ('æ', 'ae')]:
        s = s.replace(a, b)
    return s


def route_agent(question: str) -> str:
    """
    LE CONCOURS DES AGENTS : chaque agent score les mots-clés de sa
    spécialité présents dans la question ; le meilleur score gagne.
    En cas d'égalité, l'ordre de définition du dictionnaire départage
    (data > redaction > conformite > onboarding > support).
    """
    q = _normalize(question)
    best, best_score = 'support', 0
    for aid, agent in AGENTS.items():
        if aid == 'support':
            continue
        score = sum(1 for kw in agent['keywords'] if kw in q)
        if score > best_score:
            best, best_score = aid, score
    return best


def detect_format(question: str) -> str:
    """Format de document demandé dans la question (défaut : rapport)."""
    q = _normalize(question)
    for fmt, kws in _FORMAT_KEYWORDS:
        if any(kw in q for kw in kws):
            return fmt
    return 'rapport'


def _resolve_department(ctx: Dict, department_id: Optional[str],
                        question: Optional[str] = None) -> Optional[str]:
    """
    Département cible : fourni, unique du tenant, ou — si la question le
    permet — le département le PLUS RÉSONANT (consensus : celui dont le
    savoir matche le plus de mots de la question).
    """
    engine = ctx['engine']
    tenant = ctx.get('tenant')
    if department_id:
        return department_id
    if not tenant:
        return None
    depts = engine.list_departments(tenant.id)
    if len(depts) == 1:
        return depts[0]['id']
    if question:
        try:
            from enterprise_deliverables import _question_words, _wordset
            qw = _question_words(question)
            if qw:
                best, best_score = None, -1
                for dp in depts:
                    score = sum(
                        1 for f in engine.facts.get(dp['id'], [])
                        if (qw & _wordset(f.text)))
                    if score > best_score:
                        best, best_score = dp['id'], score
                if best:
                    return best
        except Exception:
            pass
    return None


def handle_agent(question: str, ctx: Dict, agent: Optional[str] = None,
                 department_id: Optional[str] = None,
                 extra: Optional[Dict] = None) -> Dict:
    """
    Exécute la question via l'agent le plus pertinent (concours).
    Retourne toujours un dict avec l'identité de l'agent gagnant.
    """
    extra = extra or {}
    if agent and agent not in AGENTS:
        raise McpError(ERR_INVALID_PARAMS,
                       f'Agent inconnu: {agent} — disponibles: {", ".join(AGENTS)}')
    chosen = agent or route_agent(question)
    meta = {'agent': chosen, 'agent_nom': AGENTS[chosen]['nom'],
            'question': question}

    if chosen == 'data':
        dept = _resolve_department(ctx, department_id, question)
        if not dept:
            raise McpError(ERR_INVALID_PARAMS,
                           'Agent Data : fournissez department_id '
                           '(plusieurs départements dans le tenant)')
        result = _tool_executor()('query_data',
                                  {'department_id': dept, 'question': question},
                                  ctx)
        result.pop('_meta', None)
        meta.update({'department_id': dept})
        meta.update(result)
        return meta

    if chosen == 'redaction':
        dept = _resolve_department(ctx, department_id, question)
        if not dept:
            raise McpError(ERR_INVALID_PARAMS,
                           'Agent Rédaction : fournissez department_id '
                           '(plusieurs départements dans le tenant)')
        fmt = extra.get('format') or detect_format(question)
        result = _tool_executor()('compose_document', {
            'department_id': dept, 'brief': question, 'format': fmt,
            'objet': extra.get('objet'), 'destinataire': extra.get('destinataire'),
        }, ctx)
        result.pop('_meta', None)
        meta.update(result)
        meta.update({'department_id': dept, 'format': fmt})
        return meta

    if chosen == 'conformite':
        q = _normalize(question)
        if 'audit' in q or 'journal' in q or 'log' in q:
            result = _tool_executor()('audit_recent',
                                      {'limit': extra.get('limit', 25)}, ctx)
        elif 'couverture' in q or 'facette' in q:
            dept = _resolve_department(ctx, department_id, question)
            if not dept:
                raise McpError(ERR_INVALID_PARAMS,
                               'Agent Conformité : fournissez department_id '
                               'pour la couverture')
            result = _tool_executor()('department_coverage',
                                      {'department_id': dept}, ctx)
        elif 'etanch' in q or 'isolement' in q or 'verrou' in q:
            depts = ctx['engine'].list_departments(ctx['tenant'].id)
            if len(depts) < 2:
                raise McpError(ERR_TOOL_EXECUTION,
                               'Étanchéité : il faut au moins 2 départements')
            result = _tool_executor()('check_seal',
                                      {'department_a': depts[0]['id'],
                                       'department_b': depts[1]['id']}, ctx)
        else:
            result = _tool_executor()('dashboard', {}, ctx)
        result.pop('_meta', None)
        meta.update(result)
        return meta

    if chosen == 'onboarding':
        q = _normalize(question)
        if 'creer' in q or 'nouveau' in q:
            name = extra.get('name') or (ctx['tenant'].name
                                         if ctx.get('tenant')
                                         else 'Nouvelle entreprise')
            email = extra.get('email') or 'admin@entreprise.fr'
            result = _tool_executor()('create_environment', {
                'name': name, 'email': email, 'description': question,
                'secteur': extra.get('secteur'),
                'holograms': extra.get('holograms'),
            }, ctx)
        else:
            result = _tool_executor()('analyze_environment',
                                      {'description': question,
                                       'secteur': extra.get('secteur')}, ctx)
        result.pop('_meta', None)
        meta.update(result)
        return meta

    # support (fallback) — Q&A sur le savoir, gate + chaînon D
    dept = _resolve_department(ctx, department_id, question)
    if dept:
        result = _tool_executor()('ask_department',
                                  {'department_id': dept,
                                   'question': question}, ctx)
    else:
        result = _tool_executor()('ask_tenant', {'question': question}, ctx)
    result.pop('_meta', None)
    meta.update(result)
    return meta


def agents_list() -> Dict:
    """Catalogue des agents (pour l'endpoint /mcp/agents)."""
    return {
        'agents': [{
            'id': aid, 'nom': a['nom'], 'role': a['role'],
            'tools': a['tools'],
        } for aid, a in AGENTS.items()],
    }
