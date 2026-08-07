"""
KA Server — Routes Agent (Autonomous Agents)
=============================================
Endpoints pour agents autonomes, planification, exécution de tâches.
"""

import logging
import uuid
from datetime import datetime
from flask import request, jsonify

log = logging.getLogger(__name__)

# Stockage en mémoire des agents (TODO: persister)
_AGENTS = {}
_TASKS = {}


def register_agent_routes(app, services):
    """Enregistre les routes Agent."""
    
    harmonic_ai = services.get('harmonic_ai')
    brain = services.get('brain')
    web_retriever = services.get('web_retriever')
    hologram_store = services.get('hologram_store')
    
    @app.route('/api/agent/create', methods=['POST', 'OPTIONS'])
    def api_agent_create():
        """Crée un nouvel agent autonome."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        name = data.get('name', f'Agent-{uuid.uuid4().hex[:6]}')
        role = data.get('role', 'assistant')  # assistant, researcher, coder, analyst
        goal = data.get('goal', '')
        tools = data.get('tools', ['search', 'code', 'analyze'])  # Outils disponibles
        config = data.get('config', {})
        
        agent_id = uuid.uuid4().hex[:12]
        
        agent = {
            'id': agent_id,
            'name': name,
            'role': role,
            'goal': goal,
            'tools': tools,
            'config': config,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'idle',
            'memory': [],
            'tasks_completed': 0,
        }
        
        _AGENTS[agent_id] = agent
        
        return jsonify({
            'success': True,
            'agent': agent,
        })
    
    @app.route('/api/agent/<agent_id>', methods=['GET'])
    def api_agent_get(agent_id):
        """Récupère un agent par ID."""
        agent = _AGENTS.get(agent_id)
        if not agent:
            return jsonify({'error': 'Agent non trouvé', 'code': 'NOT_FOUND'}), 404
        return jsonify(agent)
    
    @app.route('/api/agent/list', methods=['GET'])
    def api_agent_list():
        """Liste tous les agents."""
        status_filter = request.args.get('status')
        agents = list(_AGENTS.values())
        
        if status_filter:
            agents = [a for a in agents if a['status'] == status_filter]
        
        return jsonify({
            'agents': agents,
            'count': len(agents),
        })
    
    @app.route('/api/agent/<agent_id>/task', methods=['POST', 'OPTIONS'])
    def api_agent_task(agent_id):
        """Assigne une tâche à un agent."""
        if request.method == 'OPTIONS':
            return '', 200
        
        agent = _AGENTS.get(agent_id)
        if not agent:
            return jsonify({'error': 'Agent non trouvé', 'code': 'NOT_FOUND'}), 404
        
        data = request.get_json() or {}
        task_description = data.get('task', '').strip()
        priority = data.get('priority', 'normal')  # low, normal, high
        context = data.get('context', {})
        
        if not task_description:
            return jsonify({'error': 'Tâche requise', 'code': 'MISSING_TASK'}), 400
        
        task_id = uuid.uuid4().hex[:12]
        
        task = {
            'id': task_id,
            'agent_id': agent_id,
            'description': task_description,
            'priority': priority,
            'context': context,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None,
        }
        
        _TASKS[task_id] = task
        agent['status'] = 'working'
        
        # Exécuter de manière asynchrone (simulation pour l'instant)
        # TODO: Vraie exécution async avec queue
        _execute_task_async(task_id, agent)
        
        return jsonify({
            'success': True,
            'task': task,
        })
    
    @app.route('/api/agent/task/<task_id>', methods=['GET'])
    def api_agent_task_status(task_id):
        """Status d'une tâche."""
        task = _TASKS.get(task_id)
        if not task:
            return jsonify({'error': 'Tâche non trouvée', 'code': 'NOT_FOUND'}), 404
        return jsonify(task)
    
    @app.route('/api/agent/<agent_id>/tasks', methods=['GET'])
    def api_agent_tasks(agent_id):
        """Tâches d'un agent."""
        agent = _AGENTS.get(agent_id)
        if not agent:
            return jsonify({'error': 'Agent non trouvé', 'code': 'NOT_FOUND'}), 404
        
        tasks = [t for t in _TASKS.values() if t['agent_id'] == agent_id]
        return jsonify({
            'agent_id': agent_id,
            'tasks': tasks,
            'count': len(tasks),
        })
    
    @app.route('/api/agent/<agent_id>/memory', methods=['GET', 'POST', 'DELETE'])
    def api_agent_memory(agent_id):
        """Gestion mémoire agent."""
        agent = _AGENTS.get(agent_id)
        if not agent:
            return jsonify({'error': 'Agent non trouvé', 'code': 'NOT_FOUND'}), 404
        
        if request.method == 'GET':
            return jsonify({'memory': agent['memory']})
        
        elif request.method == 'POST':
            data = request.get_json() or {}
            entry = data.get('entry', '')
            if entry:
                agent['memory'].append({
                    'content': entry,
                    'timestamp': datetime.utcnow().isoformat(),
                })
                # Limiter taille mémoire
                if len(agent['memory']) > 100:
                    agent['memory'] = agent['memory'][-100:]
            return jsonify({'success': True, 'memory_size': len(agent['memory'])})
        
        elif request.method == 'DELETE':
            agent['memory'] = []
            return jsonify({'success': True, 'message': 'Mémoire effacée'})
    
    @app.route('/api/agent/<agent_id>', methods=['DELETE'])
    def api_agent_delete(agent_id):
        """Supprime un agent."""
        if agent_id not in _AGENTS:
            return jsonify({'error': 'Agent non trouvé', 'code': 'NOT_FOUND'}), 404
        
        # Supprimer tâches associées
        for task_id in list(_TASKS.keys()):
            if _TASKS[task_id]['agent_id'] == agent_id:
                del _TASKS[task_id]
        
        del _AGENTS[agent_id]
        return jsonify({'success': True, 'message': 'Agent supprimé'})
    
    # Templates
    _register_template_routes(app)


def _execute_task_async(task_id: str, agent: dict):
    """Exécute une tâche (simulation - à remplacer par vraie queue async)."""
    import threading
    
    def run_task():
        task = _TASKS[task_id]
        task['status'] = 'running'
        task['started_at'] = datetime.utcnow().isoformat()
        
        try:
            # Simuler exécution selon rôle
            result = _execute_agent_task(agent, task)
            task['result'] = result
            task['status'] = 'completed'
            agent['tasks_completed'] += 1
        except Exception as e:
            task['error'] = str(e)
            task['status'] = 'failed'
            log.error(f"Task {task_id} failed: {e}")
        finally:
            task['completed_at'] = datetime.utcnow().isoformat()
            agent['status'] = 'idle'
    
    thread = threading.Thread(target=run_task, daemon=True)
    thread.start()


def _execute_agent_task(agent: dict, task: dict) -> dict:
    """Exécute la tâche selon le rôle de l'agent."""
    role = agent['role']
    description = task['description']
    tools = agent['tools']
    
    # Construire prompt selon rôle
    role_prompts = {
        'researcher': f"Recherche et analyse: {description}. Fournis un rapport structuré avec sources.",
        'coder': f"Implémente: {description}. Fournis le code complet, tests et documentation.",
        'analyst': f"Analyse: {description}. Fournis insights, métriques et recommandations.",
        'assistant': f"Assiste pour: {description}. Réponds de manière utile et complète.",
    }
    
    prompt = role_prompts.get(role, role_prompts['assistant'])
    
    # Ajouter contexte mémoire
    if agent['memory']:
        memory_context = '\n'.join([m['content'] for m in agent['memory'][-5:]])
        prompt = f"Contexte mémoire:\n{memory_context}\n\n{prompt}"
    
    # Exécuter via Harmonic AI si dispo
    harmonic_ai = None
    try:
        from ka_server import create_app
        # Note: en vrai, on passerait les services
        harmonic_ai = None
    except Exception:
        pass
    
    if harmonic_ai and hasattr(harmonic_ai, 'ask'):
        try:
            result = harmonic_ai.ask(prompt)
            answer = result.get('answer', '') if isinstance(result, dict) else str(result)
            return {'output': answer, 'source': 'harmonic_ai'}
        except Exception:
            pass
    
    # Fallback simulation
    return {
        'output': f"[Simulation {role}] Traitement de: {description}",
        'source': 'simulation',
        'tools_used': tools,
    }


# ── Agent pré-configurés (templates) ────────────────────────────────────────

AGENT_TEMPLATES = {
    'researcher': {
        'name': 'Research Agent',
        'role': 'researcher',
        'goal': 'Effectuer des recherches approfondies et synthétiser l\'information',
        'tools': ['web_search', 'holographic_recall', 'analyze', 'summarize'],
    },
    'coder': {
        'name': 'Code Agent',
        'role': 'coder',
        'goal': 'Écrire, analyser et refactorer du code',
        'tools': ['code_generate', 'code_analyze', 'code_test', 'code_refactor'],
    },
    'analyst': {
        'name': 'Analyst Agent',
        'role': 'analyst',
        'goal': 'Analyser des données et fournir des insights',
        'tools': ['analyze', 'visualize', 'statistics', 'report'],
    },
    'assistant': {
        'name': 'General Assistant',
        'role': 'assistant',
        'goal': 'Assistance générale polyvalente',
        'tools': ['chat', 'search', 'code', 'analyze'],
    },
}


def _register_template_routes(app):
    """Enregistre les routes pour les templates d'agents."""
    
    @app.route('/api/agent/templates', methods=['GET'])
    def api_agent_templates():
        """Templates d'agents pré-configurés."""
        return jsonify({'templates': AGENT_TEMPLATES})
    
    @app.route('/api/agent/from-template', methods=['POST', 'OPTIONS'])
    def api_agent_from_template():
        """Crée un agent depuis un template."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        template_name = data.get('template', 'assistant')
        custom_name = data.get('name')
        custom_goal = data.get('goal')
        
        template = AGENT_TEMPLATES.get(template_name)
        if not template:
            return jsonify({'error': 'Template inconnu', 'code': 'INVALID_TEMPLATE'}), 400
        
        agent_data = template.copy()
        if custom_name:
            agent_data['name'] = custom_name
        if custom_goal:
            agent_data['goal'] = custom_goal
        
        # Réutiliser create - mais on ne peut pas appeler api_agent_create directement
        # car il nécessite le contexte Flask. On recrée la logique ici.
        import uuid
        from datetime import datetime
        
        agent_id = uuid.uuid4().hex[:12]
        
        agent = {
            'id': agent_id,
            'name': agent_data['name'],
            'role': agent_data['role'],
            'goal': agent_data['goal'],
            'tools': agent_data['tools'],
            'config': {},
            'created_at': datetime.utcnow().isoformat(),
            'status': 'idle',
            'memory': [],
            'tasks_completed': 0,
        }
        
        _AGENTS[agent_id] = agent
        
        return jsonify({
            'success': True,
            'agent': agent,
        })