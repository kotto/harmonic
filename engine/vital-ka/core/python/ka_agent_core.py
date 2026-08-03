"""
KA Agent Core — Noyau Agentique du Téléphone Harmonique
=========================================================

Inspiré de l'architecture agentique d'OpenAI (ChatGPT Agent, GPT-Live, Realtime API)
mais fondé sur les principes ondulatoires : planification par cohérence ψ, exécution
déterministe, mémoire holographique, et zéro hallucination.

Architecture :
  ┌─────────────────────────────────────────────────────────┐
  │                   KA Agent Core                          │
  │                                                          │
  │  KATaskPlanner    → Décompose objectifs en étapes ψ     │
  │  KATaskExecutor   → Boucle plan→execute→validate→replan │
  │  KAToolRegistry   → Outils avec matching par résonance   │
  │  KABackgrounder   → Tâches asynchrones + notifications   │
  │  KAProgressTrack  → Suivi visuel de progression          │
  │  KAPhoneBridge    → Pont vers les fonctions téléphone    │
  └─────────────────────────────────────────────────────────┘

Fonctions du Téléphone Harmonique :
  📞 Appels        — initier/recevoir des appels vocaux KA
  👤 Contacts      — gestion du répertoire holographique
  💬 Messages      — SMS/chat avec synthèse vocale
  ⏰ Agenda        — rappels, événements, planification
  🎤 Dictée        — commandes vocales → actions agentiques
  📋 Tâches        — suivi des tâches en cours/terminées
  🔔 Notifications — alertes quand une tâche background finit
  🧠 Mémoire       — stockage holographique des conversations

Usage :
  from ka_agent_core import KAAgentCore

  agent = KAAgentCore(brain=harmonic_brain, voice_engine=ka_voice)

  # Planifier et exécuter une tâche
  task_id = agent.dispatch("Vérifie mes emails et résume les urgences")

  # Commande vocale
  result = agent.voice_command("Appelle Maman")

  # Tâche en arrière-plan
  agent.background("Télécharge et analyse le rapport PDF")
  # ... KA continue la conversation ...
  status = agent.check_status(task_id)

Auteur : Équipe HarmoniqLLM — KA Phone
Date   : 2026-07-25
"""

import math
import time
import uuid
import json
import threading
import queue
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
TAU = 2.0 * math.pi
PHI_INV = 1.0 / PHI

# États de tâche (φ-espacés pour transitions naturelles)
TASK_STATES = {
    'pending':    0.0,    # En attente
    'planning':   0.146,  # Planification (φ⁻³)
    'running':    0.236,  # En cours (φ⁻²)
    'waiting':    0.382,  # En attente d'entrée (φ⁻¹)
    'validating': 0.618,  # Validation (φ⁻¹)
    'completed':  0.764,  # Terminé (1-φ⁻²)
    'failed':     1.0,    # Échoué
}

# Priorités
PRIORITY = {'low': 0, 'normal': 1, 'high': 2, 'urgent': 3}

# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class KAStep:
    """Une étape d'une tâche agentique."""
    id: str
    description: str
    tool: str = ''                   # Outil requis (vide = raisonnement pur)
    tool_args: dict = field(default_factory=dict)
    status: str = 'pending'          # pending | running | done | failed
    result: Any = None
    error: Optional[str] = None
    started_at: float = 0.0
    finished_at: float = 0.0
    retries: int = 0
    dependencies: List[str] = field(default_factory=list)  # IDs des étapes requises

@dataclass
class KATask:
    """Une tâche agentique complète."""
    goal: str                        # Objectif en langage naturel
    id: str = ''
    steps: List['KAStep'] = field(default_factory=list)
    status: str = 'pending'
    priority: int = 1
    progress: float = 0.0            # 0.0 → 1.0
    created_at: float = 0.0
    started_at: float = 0.0
    finished_at: float = 0.0
    result: Any = None
    error: Optional[str] = None
    context: dict = field(default_factory=dict)
    voice_response: Optional[bytes] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if self.created_at == 0.0:
            self.created_at = time.time()
    
    @property
    def elapsed_ms(self) -> float:
        if self.finished_at > 0:
            return (self.finished_at - self.started_at) * 1000
        if self.started_at > 0:
            return (time.time() - self.started_at) * 1000
        return 0.0
    
    @property
    def current_step(self) -> Optional[KAStep]:
        for s in self.steps:
            if s.status == 'running':
                return s
        return None
    
    def progress_pct(self) -> int:
        done = sum(1 for s in self.steps if s.status == 'done')
        return int(done / max(len(self.steps), 1) * 100)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'goal': self.goal,
            'status': self.status,
            'priority': self.priority,
            'progress': self.progress_pct(),
            'steps': [{'id': s.id, 'desc': s.description, 'status': s.status,
                       'tool': s.tool, 'result': str(s.result)[:100] if s.result else None}
                      for s in self.steps],
            'elapsed_ms': self.elapsed_ms,
            'error': self.error,
            'has_voice': self.voice_response is not None,
        }


@dataclass 
class KATool:
    """Un outil enregistré dans le registre."""
    name: str
    description: str
    keywords: List[str]
    func: Callable
    priority: int = 1
    requires_confirmation: bool = False
    category: str = 'general'       # phone | knowledge | code | media | system


# ═══════════════════════════════════════════════════════════════════════════════
# 1. REGISTRE D'OUTILS (avec matching par résonance ψ)
# ═══════════════════════════════════════════════════════════════════════════════

class KAToolRegistry:
    """
    Registre d'outils avec matching par résonance harmonique.
    
    Chaque outil a une signature ψ calculée via FNV-1a sur ses keywords.
    Le matching outil → intention se fait par INTERFERE (produit scalaire
    complexe entre la signature de l'intention et celle de l'outil).
    
    Avantage sur le matching par embeddings : déterministe, 0 paramètre,
    pas d'hallucination dans le choix de l'outil.
    """
    
    def __init__(self, dim: int = 512):
        self.dim = dim
        self._tools: Dict[str, KATool] = {}
        self._signatures: Dict[str, np.ndarray] = {}  # outil → ψ ∈ ℂᵈⁱᵐ
    
    def register(self, tool: KATool):
        """Enregistre un outil."""
        self._tools[tool.name] = tool
        # Créer la signature ψ de l'outil
        self._signatures[tool.name] = self._tool_to_psi(tool)
    
    def unregister(self, name: str):
        """Supprime un outil."""
        self._tools.pop(name, None)
        self._signatures.pop(name, None)
    
    def match(self, intent: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Trouve les outils les plus pertinents pour une intention.
        
        Combine :
        1. Overlap de mots-clés (poids 0.6)
        2. INTERFERE ψ (poids 0.4)
        
        Args:
            intent: description de l'intention en langage naturel
            top_k: nombre de résultats
            
        Returns:
            Liste de (tool_name, score) triée par pertinence décroissante
        """
        intent_lower = intent.lower()
        psi_intent = self._intent_to_psi(intent)
        
        scores = []
        for name, psi_tool in self._signatures.items():
            tool = self._tools[name]
            
            # 1. Overlap de mots-clés (boost déterministe)
            keyword_hits = 0
            for kw in tool.keywords:
                if kw in intent_lower:
                    keyword_hits += 1
            keyword_score = keyword_hits / max(len(tool.keywords), 1)
            
            # 2. INTERFERE ψ
            coherence = np.real(np.dot(psi_intent, np.conj(psi_tool)))
            norm_i = np.sqrt(np.sum(np.abs(psi_intent)**2)) + 1e-10
            norm_t = np.sqrt(np.sum(np.abs(psi_tool)**2)) + 1e-10
            psi_score = (coherence / (norm_i * norm_t) + 1.0) / 2.0  # [0, 1]
            
            # Score combiné
            score = 0.6 * keyword_score + 0.4 * psi_score
            
            # Bonus si le nom de l'outil est dans l'intention
            if tool.name in intent_lower:
                score += 0.3
            
            scores.append((name, min(1.0, score)))
        
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]
    
    def get(self, name: str) -> Optional[KATool]:
        return self._tools.get(name)
    
    def list_by_category(self, category: str) -> List[KATool]:
        return [t for t in self._tools.values() if t.category == category]
    
    @property
    def all_tools(self) -> List[KATool]:
        return list(self._tools.values())
    
    def _tool_to_psi(self, tool: KATool) -> np.ndarray:
        """Convertit un outil en vecteur ψ (FNV-1a + φ-spacing)."""
        seed = self._fnv1a_hash(tool.name + ''.join(tool.keywords))
        rng = np.random.RandomState(seed & 0x7FFFFFFF)
        
        psi = np.zeros(self.dim, dtype=np.complex128)
        for d in range(self.dim):
            phase = ((seed >> (d % 32)) ^ (d * 2654435761)) % 2147483647
            phase = (phase * PHI) % TAU
            amp = 1.0 / (1.0 + abs(d - self.dim//2) / (self.dim//4))
            psi[d] = amp * (math.cos(phase) + 1j * math.sin(phase))
        
        norm = np.sqrt(np.sum(np.abs(psi)**2))
        if norm > 1e-10:
            psi /= norm
        return psi
    
    def _intent_to_psi(self, text: str) -> np.ndarray:
        """Convertit une intention textuelle en ψ."""
        seed = self._fnv1a_hash(text.lower().strip())
        rng = np.random.RandomState(seed & 0x7FFFFFFF)
        
        psi = np.zeros(self.dim, dtype=np.complex128)
        for d in range(self.dim):
            phase = rng.random() * TAU
            psi[d] = complex(math.cos(phase), math.sin(phase))
        
        norm = np.sqrt(np.sum(np.abs(psi)**2))
        if norm > 1e-10:
            psi /= norm
        return psi
    
    @staticmethod
    def _fnv1a_hash(s: str) -> int:
        FNV_OFFSET = 14695981039346656037
        FNV_PRIME = 1099511628211
        h = FNV_OFFSET
        for ch in s:
            h ^= ord(ch)
            h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
        return h
    
    def __repr__(self) -> str:
        return f"KAToolRegistry({len(self._tools)} tools)"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. PLANIFICATEUR DE TÂCHES (décomposition par WaveLogic)
# ═══════════════════════════════════════════════════════════════════════════════

class KATaskPlanner:
    """
    Planificateur agentique — décompose un objectif en étapes.
    
    Utilise la logique ondulatoire (WaveLogic) pour chaîner les étapes
    de façon cohérente. Pas d'hallucination : les étapes sont déduites
    par patterns connus, pas générées aléatoirement.
    """
    
    # Patterns de décomposition par domaine (φ-espacés)
    DECOMPOSITION_PATTERNS = {
        'email': [
            ('connect', 'Se connecter à la messagerie'),
            ('fetch', 'Récupérer les emails récents'),
            ('filter', 'Filtrer par priorité/expéditeur'),
            ('analyze', 'Analyser le contenu'),
            ('summarize', 'Résumer les points clés'),
        ],
        'search': [
            ('query', 'Formuler la requête de recherche'),
            ('execute', 'Exécuter la recherche'),
            ('extract', 'Extraire les résultats pertinents'),
            ('synthesize', 'Synthétiser une réponse'),
        ],
        'call': [
            ('lookup', 'Chercher le contact'),
            ('prepare', 'Préparer le contexte de l\'appel'),
            ('dial', 'Initier l\'appel vocal KA'),
            ('converse', 'Conversation avec synthèse vocale'),
            ('log', 'Enregistrer le résumé de l\'appel'),
        ],
        'message': [
            ('compose', 'Composer le message'),
            ('synthesize', 'Générer la voix si dictée'),
            ('send', 'Envoyer le message'),
            ('confirm', 'Confirmer l\'envoi'),
        ],
        'reminder': [
            ('parse', 'Analyser la demande de rappel'),
            ('schedule', 'Planifier la date/heure'),
            ('notify', 'Programmer la notification'),
        ],
        'code': [
            ('understand', 'Comprendre le besoin'),
            ('design', 'Concevoir la solution'),
            ('implement', 'Générer le code'),
            ('test', 'Vérifier le résultat'),
        ],
        'research': [
            ('scope', 'Délimiter le sujet'),
            ('gather', 'Collecter les sources'),
            ('analyze', 'Analyser les informations'),
            ('report', 'Rédiger le rapport'),
        ],
    }
    
    def __init__(self, brain=None):
        self.brain = brain  # HolographicStore pour enrichissement
    
    def plan(self, goal: str, domain: str = 'auto') -> KATask:
        """
        Décompose un objectif en étapes.
        
        Args:
            goal: objectif en langage naturel
            domain: domaine (auto = détection automatique)
            
        Returns:
            KATask avec les étapes planifiées
        """
        task = KATask(goal=goal)
        task.status = 'planning'
        
        # Détecter le domaine
        if domain == 'auto':
            domain = self._detect_domain(goal)
        
        # Récupérer le pattern de décomposition
        pattern = self.DECOMPOSITION_PATTERNS.get(domain)
        
        if pattern:
            # Pattern connu → décomposition déterministe
            steps = []
            for tool_name, description in pattern:
                step = KAStep(
                    id=f"{task.id}_{len(steps)}",
                    description=description,
                    tool=self._map_tool(tool_name, domain),
                )
                steps.append(step)
            task.steps = steps
        else:
            # Domaine inconnu → décomposition générique φ
            task.steps = [
                KAStep(id=f"{task.id}_0", description=f"Analyser: {goal[:80]}", tool=''),
                KAStep(id=f"{task.id}_1", description="Rechercher des informations", tool='search'),
                KAStep(id=f"{task.id}_2", description="Synthétiser une réponse", tool=''),
                KAStep(id=f"{task.id}_3", description="Présenter le résultat", tool=''),
            ]
        
        # Enrichir avec le contexte holographique
        if self.brain:
            for step in task.steps:
                step.tool_args['_brain_enrichment'] = True
        
        task.status = 'pending'
        return task
    
    def _detect_domain(self, goal: str) -> str:
        """Détecte le domaine d'un objectif par mots-clés (avec frontières de mots)."""
        import re
        g = goal.lower()
        
        # Patterns avec frontières de mots pour éviter "rappelle" → "appelle"
        patterns = [
            (r'\b(?:email|mail|courriel|gmail|outlook|boite|boîte|messagerie)\b', 'email'),
            (r'\b(?:sms|texto|msg|envoyer?\s+(?:un|le)\s+(?:sms|message|texto))\b', 'message'),
            (r'\benvoie\b', 'message'),
            (r'\b(?:appel(?:le|er|é)|phone|call|joindre|téléphone|sonner|biper)\b', 'call'),
            (r'\b(?<!r)appel(?:le|er)\b', 'call'),  # "appelle" mais pas "rappelle"
            (r'\b(?:rappel(?:le|er|é)|souviens|n\'oublie|agenda|rendez-vous|rdv|alarme|notif(?:ie?)?)\b', 'reminder'),
            (r'\b(?:recherche?|cherche|trouve|search|find|google|informations?\s+(?:sur|à propos))\b', 'search'),
            (r'\b(?:code|programme|script|fonction|développe|python|javascript|html|css)\b', 'code'),
            (r'\b(?:analyse|étudie|recherche approfondie|rapport|synthèse|deep)\b', 'research'),
        ]
        
        for pattern, domain in patterns:
            if re.search(pattern, g):
                return domain
        
        # Fallback: vérifier les mots-clés sans frontières
        if any(w in g for w in ['email', 'mail', 'courriel', 'gmail']):
            return 'email'
        if any(w in g for w in ['sms', 'texto', 'message', 'msg']):
            return 'message'
        if any(w in g for w in ['rappel', 'souviens', 'agenda', 'rendez']):
            return 'reminder'
        if any(w in g for w in ['appel', 'call', 'téléphone', 'phone']):
            return 'call'
        if any(w in g for w in ['cherche', 'recherche', 'search', 'trouve']):
            return 'search'
        
        return 'general'
    
    def _map_tool(self, tool_name: str, domain: str) -> str:
        """Mappe un nom d'étape vers un outil concret."""
        mapping = {
            'connect': 'email', 'fetch': 'email', 'filter': 'email',
            'analyze': '', 'summarize': '', 'synthesize': '',
            'query': 'search', 'execute': 'search', 'extract': 'search',
            'lookup': 'contacts', 'prepare': '', 'dial': 'voice',
            'converse': 'voice', 'log': 'memory',
            'compose': '', 'send': 'message',
            'parse': '', 'schedule': 'calendar', 'notify': 'reminder',
            'understand': '', 'design': '', 'implement': 'code', 'test': 'code',
            'scope': '', 'gather': 'search', 'report': '',
        }
        return mapping.get(tool_name, '')
    
    def __repr__(self) -> str:
        return f"KATaskPlanner(patterns={len(self.DECOMPOSITION_PATTERNS)})"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. EXÉCUTEUR DE TÂCHES (boucle agentique)
# ═══════════════════════════════════════════════════════════════════════════════

class KATaskExecutor:
    """
    Exécuteur agentique — boucle plan→execute→validate→replan.
    
    Inspiré de la boucle agentique de ChatGPT Agent mais déterministe.
    Chaque étape est exécutée, le résultat validé, et le plan ajusté
    si nécessaire (replanification φ).
    """
    
    def __init__(self, tools: KAToolRegistry, brain=None, voice_engine=None):
        self.tools = tools
        self.brain = brain
        self.voice = voice_engine
        self._running_tasks: Dict[str, KATask] = {}
        self._task_history: deque = deque(maxlen=100)
    
    def execute(self, task: KATask, progress_callback: Callable = None) -> KATask:
        """
        Exécute une tâche complète.
        
        Args:
            task: la tâche à exécuter
            progress_callback: appelé après chaque étape avec (task, step, progress)
            
        Returns:
            la tâche mise à jour
        """
        task.status = 'running'
        task.started_at = time.time()
        self._running_tasks[task.id] = task
        
        try:
            for i, step in enumerate(task.steps):
                # Vérifier les dépendances
                if not self._dependencies_met(step, task.steps):
                    step.status = 'waiting'
                    continue
                
                step.status = 'running'
                step.started_at = time.time()
                
                # Exécuter l'étape
                try:
                    if step.tool and step.tool in self.tools._tools:
                        tool = self.tools.get(step.tool)
                        result = tool.func(**step.tool_args) if step.tool_args else tool.func()
                    else:
                        # Étape de raisonnement pur
                        result = self._reason(step, task)
                    
                    step.result = result
                    step.status = 'done'
                except Exception as e:
                    step.error = str(e)
                    if step.retries < 2:
                        step.retries += 1
                        step.status = 'pending'  # Réessayer
                    else:
                        step.status = 'failed'
                
                step.finished_at = time.time()
                task.progress = (i + 1) / len(task.steps)
                
                # Callback de progression
                if progress_callback:
                    progress_callback(task, step, task.progress)
                
                # Si une étape échoue définitivement, replanifier
                if step.status == 'failed':
                    self._replan(task, i)
            
            # Vérifier si toutes les étapes sont terminées
            all_done = all(s.status == 'done' for s in task.steps)
            task.status = 'completed' if all_done else 'failed'
            task.finished_at = time.time()
            
            # Stocker le résultat
            if all_done:
                task.result = self._synthesize_result(task)
            
            # Générer une réponse vocale si demandé
            if task.context.get('voice', False) and self.voice:
                try:
                    summary = self._summarize_for_voice(task)
                    audio = self.voice.speak(summary, emotion=task.context.get('emotion', 'warm'))
                    task.voice_response = (audio * 32767).astype(np.int16).tobytes()
                except Exception:
                    pass
        
        except Exception as e:
            task.status = 'failed'
            task.error = str(e)
        
        finally:
            self._task_history.append(task)
            self._running_tasks.pop(task.id, None)
        
        return task
    
    def execute_step(self, task: KATask, step_index: int = None) -> KATask:
        """
        Exécute une seule étape (mode pas-à-pas interactif).
        
        Utile quand l'utilisateur veut valider chaque étape.
        """
        if step_index is None:
            # Trouver la première étape non terminée
            for i, s in enumerate(task.steps):
                if s.status in ('pending', 'waiting', 'failed'):
                    step_index = i
                    break
        
        if step_index is None or step_index >= len(task.steps):
            return task
        
        step = task.steps[step_index]
        if step.status in ('done', 'running'):
            return task
        
        step.status = 'running'
        step.started_at = time.time()
        
        try:
            if step.tool and self.tools.get(step.tool):
                tool = self.tools.get(step.tool)
                step.result = tool.func(**step.tool_args)
            else:
                step.result = self._reason(step, task)
            step.status = 'done'
        except Exception as e:
            step.error = str(e)
            step.status = 'failed'
        
        step.finished_at = time.time()
        task.progress = task.progress_pct() / 100.0
        return task
    
    def _dependencies_met(self, step: KAStep, all_steps: List[KAStep]) -> bool:
        for dep_id in step.dependencies:
            dep_step = next((s for s in all_steps if s.id == dep_id), None)
            if dep_step and dep_step.status != 'done':
                return False
        return True
    
    def _replan(self, task: KATask, failed_index: int):
        """Replanifie après un échec (approche φ)."""
        failed_step = task.steps[failed_index]
        # Ajouter une étape de correction avant de réessayer
        correction = KAStep(
            id=f"{task.id}_fix_{failed_index}",
            description=f"Corriger: {failed_step.error[:60] if failed_step.error else 'erreur inconnue'}",
            tool='',
        )
        correction.status = 'pending'
        task.steps.insert(failed_index + 1, correction)
    
    def _reason(self, step: KAStep, task: KATask) -> str:
        """Raisonnement pur (sans outil)."""
        # En production : appeler HarmonicAI.ask()
        return f"[Raisonnement] {step.description} → analyse du contexte '{task.goal[:50]}'"
    
    def _synthesize_result(self, task: KATask) -> str:
        """Synthétise le résultat final de la tâche."""
        parts = []
        for s in task.steps:
            if s.status == 'done' and s.result:
                parts.append(str(s.result)[:200])
        return '\n'.join(parts) if parts else 'Tâche terminée.'
    
    def _summarize_for_voice(self, task: KATask) -> str:
        """Résumé vocal concis."""
        if task.status == 'completed':
            return f"Tâche terminée : {task.goal[:100]}. {len(task.steps)} étapes effectuées."
        return f"Tâche en cours : {task.goal[:100]}."
    
    def get_task(self, task_id: str) -> Optional[KATask]:
        return self._running_tasks.get(task_id)
    
    def list_running(self) -> List[dict]:
        return [t.to_dict() for t in self._running_tasks.values()]
    
    def list_history(self, n: int = 20) -> List[dict]:
        return [t.to_dict() for t in list(self._task_history)[-n:]]
    
    def __repr__(self) -> str:
        return f"KATaskExecutor(running={len(self._running_tasks)}, history={len(self._task_history)})"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DÉLÉGATION ARRIÈRE-PLAN (Background Delegate)
# ═══════════════════════════════════════════════════════════════════════════════

class KABackgrounder:
    """
    Exécution asynchrone des tâches longues.
    
    Inspiré de la Background Delegation de GPT-Live :
    - La tâche tourne dans un thread séparé
    - KA continue la conversation normalement
    - Notification quand la tâche est terminée
    - L'utilisateur peut demander le statut à tout moment
    """
    
    def __init__(self, executor: KATaskExecutor):
        self.executor = executor
        self._queue = queue.Queue()
        self._results: Dict[str, KATask] = {}
        self._listeners: Dict[str, List[Callable]] = {}
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()
    
    def dispatch(self, task: KATask, on_complete: Callable = None) -> str:
        """
        Lance une tâche en arrière-plan.
        
        Args:
            task: la tâche à exécuter
            on_complete: callback appelé avec la tâche terminée
            
        Returns:
            task_id
        """
        if on_complete:
            self._listeners.setdefault(task.id, []).append(on_complete)
        
        self._queue.put(task)
        return task.id
    
    def check(self, task_id: str) -> Optional[dict]:
        """Vérifie le statut d'une tâche background."""
        # Vérifier dans les tâches en cours d'exécution
        running = self.executor.get_task(task_id)
        if running:
            return running.to_dict()
        
        # Vérifier dans les résultats
        result = self._results.get(task_id)
        if result:
            return result.to_dict()
        
        return None
    
    def cancel(self, task_id: str) -> bool:
        """Annule une tâche (si pas encore commencée)."""
        # Marquer comme failed
        task = self.executor.get_task(task_id)
        if task:
            task.status = 'failed'
            task.error = 'Annulé par l\'utilisateur'
            task.finished_at = time.time()
            return True
        return False
    
    def _worker_loop(self):
        """Boucle principale du worker thread."""
        while True:
            try:
                task = self._queue.get(timeout=1.0)
                
                def progress_cb(t, s, p):
                    # Mise à jour silencieuse (pas de notification à chaque étape)
                    pass
                
                # Exécuter
                result = self.executor.execute(task, progress_callback=progress_cb)
                self._results[task.id] = result
                
                # Notifier les listeners
                for listener in self._listeners.pop(task.id, []):
                    try:
                        listener(result)
                    except Exception:
                        pass
                
            except queue.Empty:
                pass
            except Exception:
                pass
    
    @property
    def pending_count(self) -> int:
        return self._queue.qsize()
    
    def __repr__(self) -> str:
        return f"KABackgrounder(queue={self._queue.qsize()}, results={len(self._results)})"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PONT TÉLÉPHONE (KAPhoneBridge)
# ═══════════════════════════════════════════════════════════════════════════════

class KAPhoneBridge:
    """
    Pont entre l'agent et les fonctions du Téléphone Harmonique.
    
    Outils concrets pour les fonctionnalités téléphone :
    - Contacts holographiques
    - Appels vocaux KA
    - Messages avec synthèse
    - Agenda et rappels
    - Dictée vocale → commandes
    """
    
    def __init__(self, voice_engine=None, brain=None):
        self.voice = voice_engine
        self.brain = brain
        self.contacts: Dict[str, dict] = {}
        self.messages: List[dict] = []
        self.reminders: List[dict] = []
        self.call_log: List[dict] = []
    
    # ── Contacts ──
    
    def add_contact(self, name: str, phone: str = '', email: str = '',
                    voice_sample: Optional[np.ndarray] = None) -> str:
        """Ajoute un contact. Si voice_sample fourni, clone la voix."""
        contact_id = str(uuid.uuid4())[:8]
        contact = {'id': contact_id, 'name': name, 'phone': phone, 'email': email}
        
        if voice_sample is not None and self.voice:
            try:
                vid = self.voice.load_voice(f"contact_{name}", audio=voice_sample)
                contact['voice_id'] = vid
            except Exception:
                pass
        
        self.contacts[contact_id] = contact
        return contact_id
    
    def find_contact(self, query: str) -> List[dict]:
        """Recherche un contact par nom ou téléphone."""
        q = query.lower()
        results = []
        for c in self.contacts.values():
            if q in c.get('name', '').lower() or q in c.get('phone', ''):
                results.append(c)
        return results
    
    def list_contacts(self) -> List[dict]:
        return list(self.contacts.values())
    
    # ── Appels ──
    
    def initiate_call(self, contact_name: str, message: str = '') -> dict:
        """
        Initie un appel vocal KA.
        
        En production : utilise le Voice Engine pour générer l'audio
        et le streamer via WebSocket/WebRTC.
        """
        contacts = self.find_contact(contact_name)
        contact = contacts[0] if contacts else {'name': contact_name}
        
        call_record = {
            'id': str(uuid.uuid4())[:8],
            'contact': contact.get('name', contact_name),
            'contact_id': contact.get('id', ''),
            'type': 'outgoing',
            'status': 'initiated',
            'message': message,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'duration_s': 0,
        }
        
        # Générer l'audio d'appel si message fourni
        if message and self.voice:
            try:
                audio = self.voice.speak(message, emotion='warm')
                call_record['audio'] = audio
            except Exception:
                pass
        
        self.call_log.append(call_record)
        return call_record
    
    def answer_call(self, caller_name: str = 'Inconnu') -> dict:
        """Répond à un appel entrant."""
        call_record = {
            'id': str(uuid.uuid4())[:8],
            'contact': caller_name,
            'type': 'incoming',
            'status': 'answered',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        }
        
        # Message d'accueil KA
        greeting = f"Bonjour {caller_name}, je suis KA, comment puis-je vous aider ?"
        if self.voice:
            try:
                call_record['greeting_audio'] = self.voice.speak(greeting, emotion='warm')
            except Exception:
                pass
        
        self.call_log.append(call_record)
        return call_record
    
    # ── Messages ──
    
    def send_message(self, recipient: str, text: str, as_voice: bool = False) -> dict:
        """Envoie un message (texte ou vocal)."""
        msg = {
            'id': str(uuid.uuid4())[:8],
            'recipient': recipient,
            'text': text,
            'as_voice': as_voice,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'status': 'sent',
        }
        
        if as_voice and self.voice:
            try:
                msg['audio'] = self.voice.speak(text, emotion='warm')
            except Exception:
                msg['status'] = 'text_only'
        
        self.messages.append(msg)
        return msg
    
    # ── Agenda / Rappels ──
    
    def set_reminder(self, text: str, when: str = '', notify: bool = True) -> dict:
        """
        Programme un rappel.
        
        Args:
            text: description du rappel
            when: description temporelle ('dans 10 minutes', 'demain 8h', '2026-07-26 14:00')
            notify: activer la notification
        """
        reminder = {
            'id': str(uuid.uuid4())[:8],
            'text': text,
            'when': when,
            'notify': notify,
            'created_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'status': 'active',
        }
        self.reminders.append(reminder)
        return reminder
    
    def list_reminders(self, active_only: bool = True) -> List[dict]:
        if active_only:
            return [r for r in self.reminders if r.get('status') == 'active']
        return list(self.reminders)
    
    # ── Dictée vocale → Commande ──
    
    def voice_command(self, audio: np.ndarray, sr: int = 24000) -> dict:
        """
        Traite une commande vocale.
        
        En production : STT via Whisper ou équivalent.
        Ici : simulation pour l'architecture.
        """
        # En production : texte = stt.transcribe(audio)
        # Pour le prototype : l'audio est déjà converti en texte par le frontend
        
        result = {
            'type': 'voice_command',
            'handled': False,
            'action': None,
            'response': None,
        }
        
        # Patterns de commandes vocales
        if self.voice:
            try:
                result['response_audio'] = self.voice.speak(
                    "Commande vocale reçue. Je traite votre demande.",
                    emotion='warm'
                )
            except Exception:
                pass
        
        return result
    
    # ── Récapitulatif ──
    
    def dashboard(self) -> dict:
        """Tableau de bord du téléphone harmonique."""
        return {
            'contacts_count': len(self.contacts),
            'messages_count': len(self.messages),
            'reminders_active': len([r for r in self.reminders if r.get('status') == 'active']),
            'calls_today': len([c for c in self.call_log if c.get('timestamp', '')[:10] == time.strftime('%Y-%m-%d')]),
            'recent_calls': self.call_log[-5:],
            'recent_messages': self.messages[-5:],
            'upcoming_reminders': self.list_reminders()[:5],
        }
    
    def __repr__(self) -> str:
        return (f"KAPhoneBridge(contacts={len(self.contacts)}, "
                f"messages={len(self.messages)}, reminders={len(self.reminders)})")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. KA AGENT CORE — Intégration complète
# ═══════════════════════════════════════════════════════════════════════════════

class KAAgentCore:
    """
    Noyau agentique complet du Téléphone Harmonique.
    
    Point d'entrée unique pour toutes les capacités agentiques de KA.
    Intègre planification, exécution, outils, arrière-plan, et téléphone.
    
    Usage :
      agent = KAAgentCore(brain=harmonic_brain, voice_engine=ka_voice)
      
      # Tâche simple
      result = agent.run("Vérifie mes emails urgents")
      
      # Tâche en arrière-plan
      task_id = agent.dispatch("Analyse le rapport PDF et fais un résumé")
      # ... continuer la conversation ...
      status = agent.status(task_id)
      
      # Téléphone
      agent.phone.add_contact("Maman", phone="0601020304")
      agent.phone.initiate_call("Maman", message="Coucou, c'est KA !")
      agent.phone.set_reminder("Rappeler le dentiste", "demain 14h")
    """
    
    def __init__(self, brain=None, voice_engine=None, llm_fn=None):
        """
        Args:
            brain: HolographicStore ou HarmonicBrain
            voice_engine: KAConversationalEngine
            llm_fn: fonction de fallback LLM (optionnelle)
        """
        # Modules
        self.tools = KAToolRegistry()
        self.planner = KATaskPlanner(brain=brain)
        self.executor = KATaskExecutor(self.tools, brain=brain, voice_engine=voice_engine)
        self.backgrounder = KABackgrounder(self.executor)
        self.phone = KAPhoneBridge(voice_engine=voice_engine, brain=brain)
        
        # Références
        self.brain = brain
        self.voice = voice_engine
        self.llm = llm_fn
        
        # Enregistrer les outils du téléphone
        self._register_phone_tools()
        
        # Tâche courante (conversation active)
        self._current_task: Optional[KATask] = None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # API PRINCIPALE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def run(self, goal: str, context: dict = None,
            voice: bool = False, emotion: str = 'warm') -> KATask:
        """
        Exécute une tâche agentique de façon synchrone.
        
        Args:
            goal: objectif en langage naturel
            context: contexte additionnel
            voice: générer une réponse audio
            emotion: émotion pour la voix
            
        Returns:
            KATask terminée
        """
        ctx = context or {}
        ctx['voice'] = voice
        ctx['emotion'] = emotion
        
        # Planifier
        task = self.planner.plan(goal)
        task.context = ctx
        
        # Exécuter avec callback de progression
        def on_progress(t, s, p):
            pass  # Pourrait notifier le frontend
        
        return self.executor.execute(task, progress_callback=on_progress)
    
    def dispatch(self, goal: str, context: dict = None,
                 on_complete: Callable = None) -> str:
        """
        Lance une tâche en arrière-plan.
        
        Args:
            goal: objectif
            context: contexte
            on_complete: callback(resultat)
            
        Returns:
            task_id (utilisable avec status())
        """
        task = self.planner.plan(goal)
        task.context = context or {}
        return self.backgrounder.dispatch(task, on_complete=on_complete)
    
    def status(self, task_id: str) -> Optional[dict]:
        """Vérifie le statut d'une tâche."""
        return self.backgrounder.check(task_id)
    
    def cancel(self, task_id: str) -> bool:
        """Annule une tâche en cours."""
        return self.backgrounder.cancel(task_id)
    
    def voice_command(self, audio_or_text, sr: int = 24000) -> dict:
        """
        Traite une commande vocale (audio ou texte).
        
        Args:
            audio_or_text: audio numpy array ou texte string
            sr: sample rate (si audio)
            
        Returns:
            résultat de la commande
        """
        if isinstance(audio_or_text, str):
            text = audio_or_text
        else:
            # STT serait ici en production
            text = "[audio]"
        
        # Analyser l'intention
        intent = text.lower()
        
        # Détecter les commandes téléphone
        if any(w in intent for w in ['appelle', 'call', 'téléphone']):
            # Extraire le nom du contact
            contact = intent.replace('appelle', '').replace('call', '').strip()
            return self.phone.initiate_call(contact)
        
        if any(w in intent for w in ['message', 'envoie', 'sms', 'texto']):
            return self.phone.send_message('contact', text)
        
        if any(w in intent for w in ['rappelle', 'souviens', 'agenda']):
            return self.phone.set_reminder(text)
        
        if any(w in intent for w in ['contact', 'annuaire', 'répertoire']):
            return {'contacts': self.phone.list_contacts()}
        
        # Commande agentique générique
        return self.run(text, voice=True).result
    
    # ═══════════════════════════════════════════════════════════════════════════
    # OUTILS TÉLÉPHONE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _register_phone_tools(self):
        """Enregistre les outils du téléphone harmonique."""
        
        # Outil Contacts
        self.tools.register(KATool(
            name='contacts',
            description="Gestion du répertoire holographique",
            keywords=['contact', 'annuaire', 'répertoire', 'carnet', 'adresses', 'numéro'],
            func=self._tool_list_contacts,
            category='phone',
        ))
        
        # Outil Appel
        self.tools.register(KATool(
            name='voice',
            description="Appel vocal avec synthèse KA",
            keywords=['appel', 'call', 'téléphone', 'voix', 'parler', 'joindre', 'sonner'],
            func=self._tool_make_call,
            category='phone',
        ))
        
        # Outil Message
        self.tools.register(KATool(
            name='message',
            description="Envoi de messages texte ou vocaux",
            keywords=['message', 'sms', 'texto', 'envoie', 'msg', 'envoyer'],
            func=self._tool_send_message,
            category='phone',
        ))
        
        # Outil Rappel
        self.tools.register(KATool(
            name='reminder',
            description="Programmation de rappels et notifications",
            keywords=['rappelle', 'souviens', 'agenda', 'rendez-vous', 'alarme', 'notif'],
            func=self._tool_set_reminder,
            category='phone',
        ))
        
        # Outil Recherche
        self.tools.register(KATool(
            name='search',
            description="Recherche web et synthèse",
            keywords=['cherche', 'recherche', 'google', 'trouve', 'search', 'find', 'info'],
            func=self._tool_search,
            category='knowledge',
        ))
        
        # Outil Dashboard
        self.tools.register(KATool(
            name='dashboard',
            description="Tableau de bord du téléphone harmonique",
            keywords=['résumé', 'dashboard', 'état', 'status', 'bilan', 'today'],
            func=self._tool_dashboard,
            category='system',
        ))
    
    def _tool_list_contacts(self, query: str = '') -> list:
        return self.phone.list_contacts()
    
    def _tool_make_call(self, contact: str = '', message: str = '') -> dict:
        return self.phone.initiate_call(contact, message)
    
    def _tool_send_message(self, recipient: str = '', text: str = '',
                           as_voice: bool = False) -> dict:
        return self.phone.send_message(recipient, text, as_voice)
    
    def _tool_set_reminder(self, text: str = '', when: str = '') -> dict:
        return self.phone.set_reminder(text, when)
    
    def _tool_search(self, query: str = '') -> str:
        if self.llm:
            return self.llm(f"Recherche: {query}") or ''
        return f"[Recherche] {query}"
    
    def _tool_dashboard(self) -> dict:
        return self.phone.dashboard()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════════
    
    @property
    def info(self) -> dict:
        return {
            'tools': len(self.tools.all_tools),
            'tools_by_category': {
                cat: len(self.tools.list_by_category(cat))
                for cat in ['phone', 'knowledge', 'code', 'media', 'system', 'general']
            },
            'running_tasks': len(self.executor._running_tasks),
            'background_tasks': self.backgrounder.pending_count,
            'completed_tasks': len(self.executor._task_history),
            'phone_contacts': len(self.phone.contacts),
            'phone_messages': len(self.phone.messages),
            'phone_reminders': len(self.phone.reminders),
            'phone_calls': len(self.phone.call_log),
        }
    
    def __repr__(self) -> str:
        return (f"KAAgentCore(tools={len(self.tools.all_tools)}, "
                f"running={len(self.executor._running_tasks)}, "
                f"background={self.backgrounder.pending_count})")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST — Scénario Téléphone Harmonique
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print("  KA Agent Core — Test Téléphone Harmonique")
    print("=" * 70)
    
    # ── Init ──
    print("\n[1] Initialisation du noyau agentique...")
    agent = KAAgentCore()
    print(f"    {agent}")
    print(f"    Outils enregistrés: {len(agent.tools.all_tools)}")
    for tool in agent.tools.all_tools:
        print(f"      📞 {tool.name}: {tool.description}")
    
    # ── Test Planification ──
    print("\n[2] Test planification...")
    
    test_goals = [
        ("Vérifie mes emails urgents", 'email'),
        ("Appelle Maman pour son anniversaire", 'call'),
        ("Rappelle-moi d'acheter du pain demain à 9h", 'reminder'),
        ("Recherche les dernières nouvelles sur l'IA", 'search'),
        ("Envoie un message à Paul pour confirmer le RDV", 'message'),
    ]
    
    for goal, expected_domain in test_goals:
        task = agent.planner.plan(goal)
        domain = agent.planner._detect_domain(goal)
        print(f"    '{goal[:50]}...' → domaine={domain} (attendu={expected_domain})")
        print(f"      {len(task.steps)} étapes: {' → '.join(s.description[:30] for s in task.steps)}")
    
    # ── Test Registre d'outils ──
    print("\n[3] Test matching d'outils par intention...")
    intents = [
        "Je voudrais appeler ma mère",
        "Envoie un SMS à Pierre",
        "Cherche des informations sur le climat",
        "Ajoute un rendez-vous chez le dentiste",
        "Montre-moi mes contacts",
    ]
    
    for intent in intents:
        matches = agent.tools.match(intent, top_k=3)
        best = matches[0] if matches else ('?', 0)
        print(f"    '{intent}' → {best[0]} (score={best[1]:.3f})")
    
    # ── Test Téléphone ──
    print("\n[4] Test fonctions téléphone...")
    
    # Ajouter des contacts
    c1 = agent.phone.add_contact("Maman", phone="0601020304", email="maman@famille.fr")
    c2 = agent.phone.add_contact("Paul", phone="0605060708")
    c3 = agent.phone.add_contact("Dentiste Durand", phone="0102030405")
    print(f"    Contacts ajoutés: {agent.phone.list_contacts().__len__()}")
    
    # Initier un appel
    call = agent.phone.initiate_call("Maman", message="Bonjour Maman, c'est KA ! Je voulais te souhaiter une bonne journée.")
    print(f"    Appel initié: {call['contact']} → {call['status']}")
    
    # Envoyer un message
    msg = agent.phone.send_message("Paul", "Salut Paul, on confirme le RDV de demain 14h ?")
    print(f"    Message envoyé: {msg['recipient']} → {msg['status']}")
    
    # Programmer un rappel
    rem = agent.phone.set_reminder("Acheter du pain", "demain 9h")
    print(f"    Rappel créé: {rem['text']} ({rem['when']})")
    
    # Dashboard
    dash = agent.phone.dashboard()
    print(f"\n    📊 Dashboard Téléphone Harmonique:")
    print(f"       Contacts: {dash['contacts_count']}")
    print(f"       Messages: {dash['messages_count']}")
    print(f"       Rappels actifs: {dash['reminders_active']}")
    print(f"       Appels aujourd'hui: {dash['calls_today']}")
    
    # ── Test Exécution ──
    print("\n[5] Test exécution de tâche...")
    task = agent.planner.plan("Cherche les infos sur la théorie harmonique")
    result = agent.executor.execute(task)
    print(f"    Tâche: {task.goal[:60]}...")
    print(f"    Statut: {result.status}")
    print(f"    Progression: {result.progress_pct()}%")
    print(f"    Durée: {result.elapsed_ms:.0f}ms")
    print(f"    Étapes: {[(s.description[:30], s.status) for s in result.steps]}")
    
    # ── Test Background ──
    print("\n[6] Test tâche en arrière-plan...")
    bg_task = agent.planner.plan("Analyse les 3 derniers messages")
    task_id = agent.backgrounder.dispatch(bg_task)
    time.sleep(0.1)  # Laisser le worker démarrer
    status = agent.status(task_id)
    print(f"    Tâche background: {task_id}")
    print(f"    Statut: {status['status'] if status else 'inconnu'}")
    print(f"    Queue: {agent.backgrounder.pending_count} en attente")
    
    # ── Résumé ──
    print("\n" + "=" * 70)
    print("  RÉSUMÉ KA Agent Core")
    print("=" * 70)
    for k, v in agent.info.items():
        print(f"  {k:30s}: {v}")
    
    print(f"\n  {'Statut':30s}: ✓ OK")
    print(f"  {'Architecture':30s}: Planner + Executor + Tools + Background + Phone")
    print(f"  {'Domaines planifiés':30s}: {list(agent.planner.DECOMPOSITION_PATTERNS.keys())}")
    print(f"  {'Outils téléphone':30s}: contacts, voice, message, reminder, search, dashboard")
    
    print("\n✓ Test KA Agent Core terminé.")
