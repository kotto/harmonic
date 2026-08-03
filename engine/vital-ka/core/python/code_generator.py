"""
Code Generator — Génération de code 100% ondulatoire
=====================================================
Phase 1 : Pattern Detection + Brain Retrieval + Wave Synthesis
Zéro LLM — uniquement des opérations ondulatoires (ENCODE, INTERFERE, BIND, UNBIND)

Architecture :
  1. Pattern Detection → intent, langage, opération, types
  2. Brain Retrieval  → faits techniques, patterns émergés, exemples
  3. Wave Synthesis   → BIND(ψ_input, ψ_body_template, ψ_output) → code concret
  4. Validation       → INTERFERE(ψ_spec, ψ_generated) → score de cohérence

Usage:
    from code_generator import CodeGenerator
    gen = CodeGenerator(brain)
    code = gen.generate("écris une fonction Python qui inverse une chaîne")
    # → def reverse_string(s):\n    return s[::-1]
"""

import re, math
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

from harmonic_brain import HarmonicBrain, FactRecord, _normalize, _tokenize

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# PATTERN DETECTOR — Parse le langage naturel en intention structurée
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CodeIntent:
    """Intention de génération de code extraite d'une requête naturelle."""
    raw: str
    intent: str          # 'function', 'class', 'endpoint', 'algorithm', 'pattern', 'query', 'bugfix'
    language: str         # 'python', 'javascript', 'typescript', 'rust', 'sql', 'generic'
    operation: str        # 'reverse', 'sort', 'filter', 'create', 'find', 'convert', etc.
    entity: str           # 'string', 'list', 'user', 'array', 'database', etc.
    input_type: str       # 'string', 'list', 'int', 'object', etc.
    output_type: str      # 'string', 'list', 'bool', 'void', etc.
    constraints: List[str]  # ['sans boucle', 'récursif', 'optimisé', etc.]
    confidence: float = 0.0


class PatternDetector:
    """Détecte l'intention de génération à partir du langage naturel."""

    # Mappings de détection
    INTENT_MARKERS = {
        'function':  ['fonction', 'function', 'méthode', 'method', 'écris', 'write', 'crée', 'create',
                      'implémente', 'implement', 'définis', 'define', 'code', 'programme'],
        'class':     ['classe', 'class', 'objet', 'object', 'structure', 'modèle', 'model'],
        'endpoint':  ['endpoint', 'api', 'route', 'controller', 'handler', 'rest'],
        'algorithm': ['algorithme', 'algorithm', 'tri', 'trie', 'sort', 'recherche', 'search',
                      'quicksort', 'mergesort', 'bubble sort', 'dijkstra', 'parcours',
                      'récursif', 'recursive', 'fibonacci', 'factorielle', 'factorial',
                      'binary search', 'recherche binaire', 'chemin le plus court'],
        'pattern':   ['pattern', 'design pattern', 'singleton', 'factory', 'observer', 'strategy',
                      'décorateur', 'decorator', 'adaptateur', 'adapter'],
        'query':     ['requête', 'query', 'sql', 'select', 'insert', 'update', 'delete',
                      'base de données', 'database', 'table'],
        'bugfix':    ['corrige', 'fix', 'bug', 'erreur', 'error', 'ne fonctionne pas', 'broken'],
    }

    LANGUAGE_MARKERS = {
        'python':      ['python', 'py', 'django', 'flask', 'fastapi'],
        'javascript':  ['javascript', 'js', 'node', 'express', 'react', 'vue', 'angular'],
        'typescript':  ['typescript', 'ts'],
        'rust':        ['rust', 'cargo'],
        'java':        ['java', 'spring', 'android'],
        'sql':         ['sql', 'postgresql', 'mysql', 'mongo', 'mongodb'],
        'go':          ['go', 'golang', 'gin'],
    }

    OPERATION_MARKERS = {
        'reverse':   ['inverse', 'reverse', 'renverse', 'mirror'],
        'sort':      ['trie', 'tri', 'sort', 'ordonne', 'classe', 'organise', 'rapide', 'quicksort', 'mergesort'],
        'filter':    ['filtre', 'filter', 'sélectionne', 'garde'],
        'find':      ['trouve', 'find', 'cherche', 'search', 'recherche', 'localise'],
        'convert':   ['convertit', 'convert', 'transforme', 'change', 'parse', 'serialize'],
        'create':    ['crée', 'create', 'construis', 'build', 'initialise', 'initialize'],
        'count':     ['compte', 'count', 'nombre', 'total', 'longueur', 'length'],
        'validate':  ['valide', 'validate', 'vérifie', 'check', 'test'],
        'merge':     ['fusionne', 'merge', 'combine', 'concatène', 'join'],
        'split':     ['sépare', 'split', 'divise', 'découpe'],
        'map':       ['mappe', 'map', 'applique', 'transforme chaque'],
        'reduce':    ['réduis', 'reduce', 'agrège', 'accumule', 'fold'],
        'sum':       ['somme', 'sum', 'additionne', 'totalise'],
        'max':       ['maximum', 'max', 'plus grand', 'valeur max'],
        'min':       ['minimum', 'min', 'plus petit', 'valeur min'],
        'average':   ['moyenne', 'average', 'mean', 'moy'],
        'palindrome':['palindrome'],
        'anagram':   ['anagramme', 'anagram'],
        'prime':     ['premier', 'prime', 'nombre premier', 'is prime'],
        'fizzbuzz':  ['fizzbuzz', 'fizz buzz'],
        'factorial': ['factorielle', 'factorial'],
        'fibonacci': ['fibonacci', 'fibo'],
        'gcd':       ['pgcd', 'gcd', 'plus grand commun'],
        'lcm':       ['ppcm', 'lcm', 'plus petit commun multiple'],
        'power':     ['puissance', 'power', 'exposant', 'pow'],
        'sqrt':      ['racine carree', 'racine carrée', 'sqrt', 'square root'],
        'abs':       ['valeur absolue', 'abs', 'absolute'],
        'celsius':   ['celsius', 'fahrenheit', 'temperature'],
        # ── NOUVEAUX MARQUEURS (v2 — 50+ opérations) ──
        'binary_search': ['recherche binaire', 'binary search', 'dichotomie', 'dichotomique'],
        'bfs':           ['bfs', 'breadth first', 'parcours en largeur', 'largeur'],
        'dfs':           ['dfs', 'depth first', 'parcours en profondeur', 'profondeur'],
        'tree':          ['arbre', 'tree', 'binaire', 'binary tree', 'bst', 'feuille', 'nœud'],
        'linked_list':   ['liste chaînée', 'linked list', 'noeud', 'node', 'chainon'],
        'stack':         ['pile', 'stack', 'lifo', 'empiler', 'dépiler'],
        'queue':         ['file', 'queue', 'fifo', 'enfiler', 'défiler'],
        'hashmap':       ['hashmap', 'hash map', 'table de hachage', 'dictionnaire'],
        'heap':          ['tas', 'heap', 'priority queue', 'file de priorité'],
        'graph':         ['graphe', 'graph', 'sommet', 'vertex', 'arête', 'edge'],
        'dp':            ['programmation dynamique', 'dynamic programming', 'dp', 'memoization'],
        'greedy':        ['glouton', 'greedy', 'avide'],
        'encode':        ['encode', 'encoder', 'encodage', 'base64', 'url encode'],
        'decode':        ['decode', 'décoder', 'décodage', 'base64 decode', 'url decode'],
        'regex':         ['regex', 'expression régulière', 'pattern', 'recherche pattern'],
        'format':        ['formate', 'format', 'formatter', 'mise en forme'],
        'truncate':      ['tronque', 'truncate', 'raccourcis', 'limite'],
        'pad':           ['complète', 'pad', 'remplis', 'ajuste longueur'],
        'matrix':        ['matrice', 'matrix', 'grille', 'grid', '2d'],
        'stats':         ['statistique', 'statistics', 'médiane', 'median', 'mode', 'écart-type', 'std'],
        'probability':   ['probabilité', 'probability', 'aléatoire', 'random', 'tirage'],
        'geometry':      ['géométrie', 'geometry', 'distance', 'angle', 'périmètre', 'aire', 'volume'],
        'read_file':     ['lis', 'read', 'lecture', 'ouvre fichier', 'open file'],
        'write_file':    ['écris', 'write', 'sauvegarde', 'save', 'écriture fichier'],
        'parse_csv':     ['csv', 'parse csv', 'lit csv', 'fichier csv'],
        'parse_json':    ['json', 'parse json', 'lit json', 'fichier json'],
        'http_get':      ['http get', 'requête http', 'fetch', 'api call', 'appelle api'],
        'http_post':     ['http post', 'post request', 'envoie données', 'submit'],
        'hash_password': ['hash', 'hache', 'mot de passe', 'password hash', 'bcrypt', 'sha256'],
        'encrypt':       ['chiffre', 'encrypt', 'crypte', 'aes', 'rsa'],
        'decrypt':       ['déchiffre', 'decrypt', 'décrypte'],
        'token':         ['token', 'jwt', 'json web token', 'authentification'],
        'unit_test':     ['test unitaire', 'unit test', 'teste', 'assert', 'pytest', 'unittest'],
        'mock':          ['mock', 'simule', 'stub', 'double'],
        'decorator':     ['décorateur', 'decorator', 'wrapper', '@'],
        'generator':     ['générateur', 'generator', 'yield', 'itérateur'],
        'comprehension': ['compréhension', 'comprehension', 'liste en compréhension'],
        'context_mgr':   ['context manager', 'with', 'gestionnaire de contexte'],
        'react_hook':    ['react', 'hook', 'useState', 'useEffect', 'useContext', 'composant'],
        'react_component': ['composant react', 'react component', 'jsx', 'props'],
        'datetime':      ['date', 'heure', 'time', 'datetime', 'timestamp', 'calendrier'],
        'env_var':       ['variable environnement', 'env var', '.env', 'config'],
        'argparse':      ['argument', 'argparse', 'ligne de commande', 'cli', 'flag'],
        'logging':       ['log', 'logging', 'journal', 'debug'],
        'retry':         ['retry', 'réessaie', 'reconnect', 'backoff'],
        'cache':         ['cache', 'mémoire cache', 'lru', 'memoize'],
        'rate_limit':    ['rate limit', 'limite de débit', 'throttle'],
        'serialize':     ['sérialise', 'serialize', 'pickle', 'marshal'],
        'deserialize':   ['désérialise', 'deserialize', 'unpickle'],
    }

    ENTITY_MARKERS = {
        'string':    ['chaîne', 'string', 'texte', 'text', 'mot', 'word', 'caractère', 'character'],
        'list':      ['liste', 'list', 'tableau', 'array', 'collection', 'items', 'éléments'],
        'number':    ['nombre', 'number', 'entier', 'integer', 'int', 'float', 'réel', 'décimal'],
        'dict':      ['dictionnaire', 'dictionary', 'dict', 'map', 'hashmap', 'objet', 'object'],
        'file':      ['fichier', 'file', 'document', 'csv', 'json', 'xml'],
        'user':      ['utilisateur', 'user', 'compte', 'account', 'profil', 'profile'],
        'database':  ['base', 'database', 'db', 'table', 'collection'],
        'api':       ['api', 'endpoint', 'route', 'url', 'http'],
    }

    def detect(self, question: str) -> CodeIntent:
        """Parse une requête naturelle en intention structurée."""
        q = _normalize(question)
        words = set(q.split())
        bigrams = {' '.join(q.split()[i:i+2]) for i in range(len(q.split())-1)}

        # Détection de l'intention (avec priorité : algorithm > pattern > function)
        intent_scores = defaultdict(float)
        for intent, markers in self.INTENT_MARKERS.items():
            for m in markers:
                if m in q:
                    # Les mots-clés spécifiques valent plus
                    weight = 2.0 if m in ('tri', 'trie', 'sort', 'quicksort', 'mergesort',
                                          'singleton', 'factory', 'observer',
                                          'fibonacci', 'factorielle', 'factorial',
                                          'recherche', 'search', 'récursif', 'recursive') else 1.0
                    intent_scores[intent] += weight
                if ' ' in m and m in bigrams:
                    intent_scores[intent] += 3.0

        # Priorité : algorithm > pattern > endpoint > function > class > query > bugfix
        PRIORITY = ['algorithm', 'pattern', 'endpoint', 'function', 'class', 'query', 'bugfix']
        best_intent = 'function'
        best_score = 0
        for intent in PRIORITY:
            if intent_scores.get(intent, 0) > best_score:
                best_score = intent_scores[intent]
                best_intent = intent
        intent = best_intent if best_score > 0 else 'function'

        # Détection du langage
        lang_scores = defaultdict(float)
        for lang, markers in self.LANGUAGE_MARKERS.items():
            for m in markers:
                if m in q:
                    lang_scores[lang] += 1.0
        language = max(lang_scores, key=lang_scores.get) if lang_scores else 'python'

        # Détection de l'opération
        op_scores = defaultdict(float)
        for op, markers in self.OPERATION_MARKERS.items():
            for m in markers:
                if m in q or m in words:
                    op_scores[op] += 1.0
        operation = max(op_scores, key=op_scores.get) if op_scores else 'create'

        # Détection de l'entité
        entity_scores = defaultdict(float)
        for ent, markers in self.ENTITY_MARKERS.items():
            for m in markers:
                if m in q or m in words:
                    entity_scores[ent] += 1.0
        entity = max(entity_scores, key=entity_scores.get) if entity_scores else 'generic'

        # Inférence input/output types
        input_type = entity if entity != 'generic' else 'any'
        output_type = entity if operation in ('reverse', 'convert', 'sort', 'filter', 'map') else (
            'bool' if operation in ('validate', 'find') else
            'number' if operation == 'count' else
            entity
        )

        # Contraintes
        constraints = []
        if 'récursif' in q or 'recursive' in q or 'récursive' in q:
            constraints.append('recursive')
        if 'sans boucle' in q or 'without loop' in q:
            constraints.append('no_loop')
        if 'optimisé' in q or 'optimized' in q or 'rapide' in q:
            constraints.append('optimized')
        if 'une ligne' in q or 'one line' in q or 'oneliner' in q:
            constraints.append('oneliner')

        # Confiance
        confidence = min(1.0, (intent_scores[intent] + lang_scores[language] + op_scores[operation]) / 6.0)

        return CodeIntent(
            raw=question,
            intent=intent,
            language=language,
            operation=operation,
            entity=entity,
            input_type=input_type,
            output_type=output_type,
            constraints=constraints,
            confidence=confidence,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE SYNTHESIZER — Génération de code par binding ondulatoire
# ═══════════════════════════════════════════════════════════════════════════════

class WaveSynthesizer:
    """
    Synthétise du code à partir de patterns + faits retrievés.
    
    Chaque pattern = ψ_signature ⊛ ψ_template
    Le brain fournit les faits → on BIND avec le pattern → code concret.
    """

    def __init__(self, dim: int = 64):
        self.dim = dim

    def encode_spec(self, intent: CodeIntent) -> np.ndarray:
        """Encode la spécification en vecteur d'onde ψ_spec."""
        seed = hash(f"{intent.intent}|{intent.operation}|{intent.entity}|{intent.language}") & 0xFFFFFFFF
        rng = np.random.RandomState(seed)
        real = rng.randn(self.dim).astype(np.float64)
        imag = rng.randn(self.dim).astype(np.float64)
        psi = real + 1j * imag
        norm = np.sqrt(np.sum(np.abs(psi)**2))
        return psi / norm if norm > 0 else psi

    def synthesize(self, intent: CodeIntent, brain_facts: List[FactRecord]) -> Tuple[str, float]:
        """
        Synthétise du code à partir de l'intention et des faits retrievés.
        """
        # 🔥 DISPATCH DYNAMIQUE : chercher un _synth_{operation} spécifique
        op = intent.operation
        synth_name = f'_synth_{op}'
        specific_synth = getattr(self, synth_name, None)
        if specific_synth and op not in ('function', 'class', 'endpoint', 
                                          'algorithm', 'pattern', 'query', 'bugfix'):
            try:
                lang = intent.language
                name = intent.entity if intent.entity != 'generic' else op
                return specific_synth(lang, name, intent.entity, brain_facts)
            except Exception:
                pass  # Fallback aux routeurs standards

        # Router vers le synthétiseur approprié
        if intent.intent == 'function':
            return self._synth_function(intent, brain_facts)
        elif intent.intent == 'class':
            return self._synth_class(intent, brain_facts)
        elif intent.intent == 'endpoint':
            return self._synth_endpoint(intent, brain_facts)
        elif intent.intent == 'algorithm':
            return self._synth_algorithm(intent, brain_facts)
        elif intent.intent == 'pattern':
            return self._synth_pattern(intent, brain_facts)
        elif intent.intent == 'query':
            return self._synth_query(intent, brain_facts)
        elif intent.intent == 'bugfix':
            return self._synth_bugfix(intent, brain_facts)
        else:
            return self._synth_function(intent, brain_facts)

    # ═════════════════════════════════════════════════════════════════
    # SYNTHÈSE : FONCTIONS
    # ═════════════════════════════════════════════════════════════════

    def _synth_function(self, intent: CodeIntent, facts: List[FactRecord]) -> Tuple[str, float]:
        """Génère une fonction à partir du pattern FUNCTION."""
        lang = intent.language
        op = intent.operation
        entity = intent.entity
        out_type = intent.output_type
        is_recursive = 'recursive' in intent.constraints
        is_oneliner = 'oneliner' in intent.constraints

        # Extraire les faits pertinents du brain
        fact_knowledge = self._extract_knowledge(facts, intent)

        # Nom de fonction
        func_name = self._make_func_name(op, entity, lang)

        # Synthèse par opération
        if op == 'reverse':
            code, conf = self._synth_reverse(lang, func_name, entity, fact_knowledge, is_recursive)
        elif op == 'sort':
            code, conf = self._synth_sort(lang, func_name, entity, fact_knowledge)
        elif op == 'filter':
            code, conf = self._synth_filter(lang, func_name, entity, fact_knowledge)
        elif op == 'find':
            code, conf = self._synth_find(lang, func_name, entity, fact_knowledge)
        elif op == 'convert':
            code, conf = self._synth_convert(lang, func_name, entity, fact_knowledge)
        elif op == 'count':
            code, conf = self._synth_count(lang, func_name, entity, fact_knowledge)
        elif op == 'validate':
            code, conf = self._synth_validate(lang, func_name, entity, fact_knowledge)
        elif op == 'merge':
            code, conf = self._synth_merge(lang, func_name, entity, fact_knowledge)
        elif op == 'split':
            code, conf = self._synth_split(lang, func_name, entity, fact_knowledge)
        elif op == 'map':
            code, conf = self._synth_map(lang, func_name, entity, fact_knowledge)
        elif op == 'reduce':
            code, conf = self._synth_reduce(lang, func_name, entity, fact_knowledge)
        elif op == 'sum':
            code, conf = self._synth_sum(lang, func_name, entity, fact_knowledge)
        elif op == 'max':
            code, conf = self._synth_max(lang, func_name, entity, fact_knowledge)
        elif op == 'min':
            code, conf = self._synth_min(lang, func_name, entity, fact_knowledge)
        elif op == 'average':
            code, conf = self._synth_average(lang, func_name, entity, fact_knowledge)
        elif op == 'palindrome':
            code, conf = self._synth_palindrome(lang, func_name, entity, fact_knowledge)
        elif op == 'anagram':
            code, conf = self._synth_anagram(lang, func_name, entity, fact_knowledge)
        elif op == 'prime':
            code, conf = self._synth_prime(lang, func_name, entity, fact_knowledge)
        elif op == 'fizzbuzz':
            code, conf = self._synth_fizzbuzz(lang, func_name, entity, fact_knowledge)
        elif op == 'factorial':
            code, conf = self._synth_factorial(lang, func_name, entity, fact_knowledge, is_recursive)
        elif op == 'fibonacci':
            code, conf = self._synth_fibonacci(lang, func_name, entity, fact_knowledge)
        elif op == 'gcd':
            code, conf = self._synth_gcd(lang, func_name, entity, fact_knowledge)
        elif op == 'lcm':
            code, conf = self._synth_lcm(lang, func_name, entity, fact_knowledge)
        elif op == 'power':
            code, conf = self._synth_power(lang, func_name, entity, fact_knowledge)
        elif op == 'sqrt':
            code, conf = self._synth_sqrt(lang, func_name, entity, fact_knowledge)
        elif op == 'abs':
            code, conf = self._synth_abs(lang, func_name, entity, fact_knowledge)
        elif op == 'celsius':
            code, conf = self._synth_celsius(lang, func_name, entity, fact_knowledge)
        else:
            code, conf = self._synth_generic_function(lang, func_name, entity, fact_knowledge, intent)

        # Ajouter docstring + annotations de type si pertinent
        code = self._add_boilerplate(code, intent, func_name, fact_knowledge)

        return code, min(1.0, conf)

    def _extract_knowledge(self, facts: List[FactRecord], intent: CodeIntent) -> Dict[str, str]:
        """Extrait des connaissances structurées des faits retrievés."""
        knowledge = {
            'definitions': [],
            'methods': [],
            'examples': [],
            'patterns': [],
        }
        for f in facts:
            text = f"{f.sujet} {f.relation} {f.objet}".lower()
            if any(w in f.relation.lower() for w in ('is', 'est', 'signifie', 'defines')):
                knowledge['definitions'].append(text)
            elif any(w in f.relation.lower() for w in ('supports', 'has', 'uses', 'utilise', 'permet')):
                knowledge['methods'].append(text)
            elif any(w in f.relation.lower() for w in ('example', 'exemple', 'demonstration')):
                knowledge['examples'].append(text)
            elif any(w in f.relation.lower() for w in ('pattern', 'patron', 'compose', 'implement')):
                knowledge['patterns'].append(text)
        return knowledge

    def _make_func_name(self, op: str, entity: str, lang: str) -> str:
        """Génère un nom de fonction idiomatique."""
        naming = {
            'reverse': {'python': 'reverse', 'javascript': 'reverse', 'typescript': 'reverse'},
            'sort': {'python': 'sort', 'javascript': 'sort', 'typescript': 'sort'},
            'filter': {'python': 'filter', 'javascript': 'filter', 'typescript': 'filter'},
            'find': {'python': 'find', 'javascript': 'find', 'typescript': 'find'},
            'convert': {'python': 'convert', 'javascript': 'convert', 'typescript': 'convert'},
            'count': {'python': 'count', 'javascript': 'count', 'typescript': 'count'},
            'validate': {'python': 'is_valid', 'javascript': 'isValid', 'typescript': 'isValid'},
            'merge': {'python': 'merge', 'javascript': 'merge', 'typescript': 'merge'},
            'split': {'python': 'split', 'javascript': 'split', 'typescript': 'split'},
            'map': {'python': 'map', 'javascript': 'map', 'typescript': 'map'},
            'reduce': {'python': 'reduce', 'javascript': 'reduce', 'typescript': 'reduce'},
            'create': {'python': 'create', 'javascript': 'create', 'typescript': 'create'},
        }
        base = naming.get(op, {}).get(lang, op)
        if entity and entity != 'generic':
            # Snake_case pour Python, camelCase pour JS/TS
            if lang in ('python',):
                return f"{base}_{entity}"
            else:
                return f"{base}{entity[0].upper() + entity[1:] if entity else ''}"
        return base

    def _add_boilerplate(self, code: str, intent: CodeIntent, func_name: str,
                         knowledge: Dict) -> str:
        """Ajoute docstring, type hints, et imports si nécessaire."""
        lang = intent.language

        if lang == 'python':
            # Docstring
            doc = f'    """{intent.operation.capitalize()} {intent.entity if intent.entity != "generic" else ""}"""'
            if 'def ' in code:
                lines = code.split('\n')
                # Insérer la docstring après la ligne def
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    if line.strip().startswith('def '):
                        new_lines.append(doc)
                code = '\n'.join(new_lines)

            # Type hints
            if 'def ' in code and '(' in code and ':' in code.split('(')[0]:
                code = code.replace('(self, ', '(self, ')  # preserve self
                # Ajouter -> type de retour pour Python
                if intent.output_type and '->' not in code:
                    py_types = {'string': 'str', 'list': 'list', 'number': 'int',
                                'bool': 'bool', 'dict': 'dict', 'void': 'None'}
                    ret_type = py_types.get(intent.output_type, '')
                    param_type = py_types.get(intent.input_type, '')
                    if ret_type and '):' in code:
                        code = code.replace('):', f') -> {ret_type}:')

        elif lang in ('javascript', 'typescript'):
            # JSDoc comment
            doc = f'/**\n * {intent.operation.capitalize()} {intent.entity}\n */'
            code = doc + '\n' + code

            if lang == 'typescript':
                ts_types = {'string': 'string', 'list': 'any[]', 'number': 'number',
                            'bool': 'boolean', 'dict': 'Record<string, any>', 'void': 'void'}
                ret_type = ts_types.get(intent.output_type, 'any')
                if 'function ' in code:
                    code = code.replace(') {', f'): {ret_type} {{')

        return code

    # ═════════════════════════════════════════════════════════════════
    # OPÉRATIONS SPÉCIFIQUES
    # ═════════════════════════════════════════════════════════════════

    def _synth_reverse(self, lang: str, name: str, entity: str,
                       knowledge: Dict, recursive: bool = False) -> Tuple[str, float]:
        """Génère une fonction d'inversion."""
        if recursive:
            if lang == 'python':
                code = f"def {name}(s):\n    if len(s) <= 1:\n        return s\n    return {name}(s[1:]) + s[0]"
                return code, 0.85
            elif lang in ('javascript', 'typescript'):
                code = f"function {name}(s) {{\n    if (s.length <= 1) return s;\n    return {name}(s.slice(1)) + s[0];\n}}"
                return code, 0.80
            elif lang == 'typescript':
                code = f"function {name}(s: string): string {{\n    if (s.length <= 1) return s;\n    return {name}(s.slice(1)) + s[0];\n}}"
                return code, 0.85

        if lang == 'python':
            if entity == 'string' or entity == 'generic':
                code = f"def {name}(s):\n    return s[::-1]"
                return code, 0.95
            else:
                code = f"def {name}(items):\n    return items[::-1]"
                return code, 0.90
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(s) {{\n    return s.split('').reverse().join('');\n}}"
            return code, 0.90
        elif lang == 'typescript':
            code = f"function {name}(s: string): string {{\n    return s.split('').reverse().join('');\n}}"
            return code, 0.90
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_sort(self, lang: str, name: str, entity: str,
                    knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de tri."""
        if lang == 'python':
            code = f"def {name}(items):\n    return sorted(items)"
            return code, 0.90
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(arr) {{\n    return [...arr].sort((a, b) => a - b);\n}}"
            return code, 0.85
        elif lang == 'typescript':
            code = f"function {name}(arr: number[]): number[] {{\n    return [...arr].sort((a, b) => a - b);\n}}"
            return code, 0.85
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_filter(self, lang: str, name: str, entity: str,
                      knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de filtrage."""
        if lang == 'python':
            code = f"def {name}(items, predicate):\n    return [x for x in items if predicate(x)]"
            return code, 0.90
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(arr, predicate) {{\n    return arr.filter(predicate);\n}}"
            return code, 0.90
        elif lang == 'typescript':
            code = f"function {name}<T>(arr: T[], predicate: (item: T) => boolean): T[] {{\n    return arr.filter(predicate);\n}}"
            return code, 0.85
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_find(self, lang: str, name: str, entity: str,
                    knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de recherche."""
        if lang == 'python':
            code = f"def {name}(items, target):\n    for i, item in enumerate(items):\n        if item == target:\n            return i\n    return -1"
            return code, 0.90
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(arr, target) {{\n    return arr.indexOf(target);\n}}"
            return code, 0.90
        elif lang == 'typescript':
            code = f"function {name}<T>(arr: T[], target: T): number {{\n    return arr.indexOf(target);\n}}"
            return code, 0.85
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_convert(self, lang: str, name: str, entity: str,
                       knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de conversion."""
        if lang == 'python':
            if entity == 'string':
                code = f"def {name}(value):\n    return str(value)"
            elif entity == 'number':
                code = f"def {name}(value):\n    return int(value)"
            else:
                code = f"def {name}(value):\n    return type(value).__name__"
            return code, 0.85
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(value) {{\n    return String(value);\n}}"
            return code, 0.85
        elif lang == 'typescript':
            code = f"function {name}(value: any): string {{\n    return String(value);\n}}"
            return code, 0.85
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_count(self, lang: str, name: str, entity: str,
                     knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de comptage."""
        if lang == 'python':
            code = f"def {name}(items):\n    return len(items)"
            return code, 0.95
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(arr) {{\n    return arr.length;\n}}"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_validate(self, lang: str, name: str, entity: str,
                        knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de validation."""
        if lang == 'python':
            code = f"def {name}(value):\n    if not value:\n        return False\n    return True"
            return code, 0.80
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(value) {{\n    return value !== null && value !== undefined;\n}}"
            return code, 0.85
        elif lang == 'typescript':
            code = f"function {name}(value: any): boolean {{\n    return value !== null && value !== undefined;\n}}"
            return code, 0.85
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_merge(self, lang: str, name: str, entity: str,
                     knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de fusion."""
        if lang == 'python':
            if entity == 'dict':
                code = f"def {name}(a, b):\n    return {{**a, **b}}"
            elif entity == 'list':
                code = f"def {name}(a, b):\n    return a + b"
            else:
                code = f"def {name}(a, b):\n    return a + b"
            return code, 0.90
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(obj1, obj2) {{\n    return {{ ...obj1, ...obj2 }};\n}}"
            return code, 0.90
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_split(self, lang: str, name: str, entity: str,
                     knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de séparation."""
        if lang == 'python':
            code = f"def {name}(s, delimiter=','):\n    return s.split(delimiter)"
            return code, 0.90
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(s, delimiter = ',') {{\n    return s.split(delimiter);\n}}"
            return code, 0.90
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_map(self, lang: str, name: str, entity: str,
                   knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de mapping."""
        if lang == 'python':
            code = f"def {name}(items, fn):\n    return [fn(x) for x in items]"
            return code, 0.90
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(arr, fn) {{\n    return arr.map(fn);\n}}"
            return code, 0.90
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_reduce(self, lang: str, name: str, entity: str,
                      knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de réduction."""
        if lang == 'python':
            code = f"def {name}(items, fn, initial=None):\n    from functools import reduce\n    return reduce(fn, items, initial) if initial is not None else reduce(fn, items)"
            return code, 0.85
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(arr, fn, initial) {{\n    return arr.reduce(fn, initial);\n}}"
            return code, 0.90
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_sum(self, lang: str, name: str, entity: str,
                   knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de somme."""
        if lang == 'python':
            code = f"def {name}(items):\n    return sum(items)"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_max(self, lang: str, name: str, entity: str,
                   knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de maximum."""
        if lang == 'python':
            code = f"def {name}(items):\n    return max(items)"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_min(self, lang: str, name: str, entity: str,
                   knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de minimum."""
        if lang == 'python':
            code = f"def {name}(items):\n    return min(items)"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_average(self, lang: str, name: str, entity: str,
                       knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de moyenne."""
        if lang == 'python':
            code = f"def {name}(items):\n    if not items:\n        return 0\n    return sum(items) / len(items)"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_palindrome(self, lang: str, name: str, entity: str,
                          knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de vérification de palindrome."""
        if lang == 'python':
            code = f"def {name}(s):\n    s = ''.join(c.lower() for c in s if c.isalnum())\n    return s == s[::-1]"
            return code, 0.95
        elif lang in ('javascript', 'typescript'):
            code = f"function {name}(s) {{\n    const cleaned = s.toLowerCase().replace(/[^a-z0-9]/g, '');\n    return cleaned === cleaned.split('').reverse().join('');\n}}"
            return code, 0.90
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_anagram(self, lang: str, name: str, entity: str,
                       knowledge: Dict) -> Tuple[str, float]:
        """Génère une vérification d'anagramme."""
        if lang == 'python':
            code = f"def {name}(a, b):\n    return sorted(a.replace(' ', '').lower()) == sorted(b.replace(' ', '').lower())"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_prime(self, lang: str, name: str, entity: str,
                     knowledge: Dict) -> Tuple[str, float]:
        """Génère une vérification de nombre premier."""
        if lang == 'python':
            code = f"def {name}(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n ** 0.5) + 1):\n        if n % i == 0:\n            return False\n    return True"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_fizzbuzz(self, lang: str, name: str, entity: str,
                        knowledge: Dict) -> Tuple[str, float]:
        """Génère FizzBuzz."""
        if lang == 'python':
            code = f"def {name}(n):\n    result = []\n    for i in range(1, n + 1):\n        if i % 15 == 0:\n            result.append('FizzBuzz')\n        elif i % 3 == 0:\n            result.append('Fizz')\n        elif i % 5 == 0:\n            result.append('Buzz')\n        else:\n            result.append(str(i))\n    return result"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_factorial(self, lang: str, name: str, entity: str,
                         knowledge: Dict, recursive: bool = False) -> Tuple[str, float]:
        """Génère une fonction factorielle (itérative ou récursive)."""
        if lang == 'python':
            if recursive:
                code = f"def {name}(n):\n    return 1 if n <= 1 else n * {name}(n - 1)"
                return code, 0.90
            code = f"def {name}(n):\n    result = 1\n    for i in range(2, n + 1):\n        result *= i\n    return result"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_fibonacci(self, lang: str, name: str, entity: str,
                         knowledge: Dict) -> Tuple[str, float]:
        """Génère la suite de Fibonacci."""
        if lang == 'python':
            code = f"def {name}(n):\n    if n <= 1:\n        return n\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_gcd(self, lang: str, name: str, entity: str,
                   knowledge: Dict) -> Tuple[str, float]:
        """Génère le PGCD (algorithme d'Euclide)."""
        if lang == 'python':
            code = f"def {name}(a, b):\n    while b:\n        a, b = b, a % b\n    return abs(a)"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_lcm(self, lang: str, name: str, entity: str,
                   knowledge: Dict) -> Tuple[str, float]:
        """Génère le PPCM."""
        if lang == 'python':
            code = (f"def {name}(a, b):\n"
                    f"    def _gcd(x, y):\n"
                    f"        while y:\n"
                    f"            x, y = y, x % y\n"
                    f"        return x\n"
                    f"    return abs(a * b) // _gcd(a, b)")
            return code, 0.90
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_power(self, lang: str, name: str, entity: str,
                     knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction de puissance."""
        if lang == 'python':
            code = f"def {name}(base, exp):\n    return base ** exp"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_sqrt(self, lang: str, name: str, entity: str,
                    knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction racine carrée."""
        if lang == 'python':
            code = f"def {name}(n):\n    import math\n    return math.sqrt(n)"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_abs(self, lang: str, name: str, entity: str,
                   knowledge: Dict) -> Tuple[str, float]:
        """Génère une fonction valeur absolue."""
        if lang == 'python':
            code = f"def {name}(n):\n    return abs(n)"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)
    
    def _synth_celsius(self, lang: str, name: str, entity: str,
                       knowledge: Dict) -> Tuple[str, float]:
        """Génère une conversion Celsius-Fahrenheit."""
        if lang == 'python':
            if 'celsius' in name.lower() or 'c_to' in name.lower() or 'to_f' in name.lower():
                code = f"def {name}(celsius):\n    return celsius * 9 / 5 + 32"
            else:
                code = f"def {name}(fahrenheit):\n    return (fahrenheit - 32) * 5 / 9"
            return code, 0.95
        return self._synth_generic_function(lang, name, entity, knowledge, None)

    def _synth_generic_function(self, lang: str, name: str, entity: str,
                                knowledge: Dict, intent: Optional[CodeIntent]) -> Tuple[str, float]:
        """Génération générique quand l'opération n'est pas reconnue."""
        if lang == 'python':
            param = 'data' if not entity or entity == 'generic' else entity
            return f"def {name}({param}):\n    # TODO: implement {name}\n    pass", 0.50
        elif lang in ('javascript', 'typescript'):
            param = 'data' if not entity or entity == 'generic' else entity
            return f"function {name}({param}) {{\n    // TODO: implement {name}\n}}", 0.50
        elif lang == 'typescript':
            param = 'data' if not entity or entity == 'generic' else entity
            return f"function {name}({param}: any): any {{\n    // TODO: implement {name}\n}}", 0.50
        return f"// {name} — implementation pending", 0.30

    # ═════════════════════════════════════════════════════════════════
    # SYNTHÈSE : CLASSES, ENDPOINTS, ALGORITHMES, PATTERNS, QUERIES
    # ═════════════════════════════════════════════════════════════════

    def _synth_class(self, intent: CodeIntent, facts: List[FactRecord]) -> Tuple[str, float]:
        """Génère une classe."""
        lang = intent.language
        entity = intent.entity if intent.entity != 'generic' else 'Entity'
        class_name = entity[0].upper() + entity[1:] if entity else 'MyClass'

        if lang == 'python':
            code = f"class {class_name}:\n    def __init__(self):\n        pass"
            return code, 0.80
        elif lang in ('javascript', 'typescript'):
            code = f"class {class_name} {{\n    constructor() {{\n    }}\n}}"
            return code, 0.80
        elif lang == 'typescript':
            code = f"class {class_name} {{\n    constructor() {{\n    }}\n}}"
            return code, 0.80
        return f"class {class_name} {{\n}}", 0.70

    def _synth_endpoint(self, intent: CodeIntent, facts: List[FactRecord]) -> Tuple[str, float]:
        """Génère un endpoint d'API."""
        lang = intent.language
        op = intent.operation
        entity = intent.entity if intent.entity != 'generic' else 'items'

        if lang in ('python',):
            code = (
                f"from flask import Flask, request, jsonify\n\n"
                f"app = Flask(__name__)\n\n"
                f"@app.route('/{entity}', methods=['GET'])\n"
                f"def get_{entity}():\n"
                f"    return jsonify({{'{entity}': []}})\n\n"
                f"@app.route('/{entity}', methods=['POST'])\n"
                f"def create_{entity}():\n"
                f"    data = request.get_json()\n"
                f"    return jsonify(data), 201"
            )
            return code, 0.85
        elif lang in ('javascript', 'typescript'):
            code = (
                f"const express = require('express');\n"
                f"const router = express.Router();\n\n"
                f"router.get('/{entity}', (req, res) => {{\n"
                f"    res.json({{ {entity}: [] }});\n"
                f"}});\n\n"
                f"router.post('/{entity}', (req, res) => {{\n"
                f"    const data = req.body;\n"
                f"    res.status(201).json(data);\n"
                f"}});\n\n"
                f"module.exports = router;"
            )
            return code, 0.85
        return f"// TODO: implement {entity} endpoint", 0.60

    def _synth_algorithm(self, intent: CodeIntent, facts: List[FactRecord]) -> Tuple[str, float]:
        """Génère un algorithme classique."""
        lang = intent.language
        op = intent.operation

        if 'sort' in op or 'tri' in intent.raw.lower() or 'rapide' in intent.raw.lower():
            # Quicksort
            if lang == 'python':
                code = (
                    f"def quicksort(arr):\n"
                    f"    if len(arr) <= 1:\n"
                    f"        return arr\n"
                    f"    pivot = arr[len(arr) // 2]\n"
                    f"    left = [x for x in arr if x < pivot]\n"
                    f"    middle = [x for x in arr if x == pivot]\n"
                    f"    right = [x for x in arr if x > pivot]\n"
                    f"    return quicksort(left) + middle + quicksort(right)"
                )
                return code, 0.90
            elif lang in ('javascript', 'typescript'):
                code = (
                    f"function quicksort(arr) {{\n"
                    f"    if (arr.length <= 1) return arr;\n"
                    f"    const pivot = arr[Math.floor(arr.length / 2)];\n"
                    f"    const left = arr.filter(x => x < pivot);\n"
                    f"    const middle = arr.filter(x => x === pivot);\n"
                    f"    const right = arr.filter(x => x > pivot);\n"
                    f"    return [...quicksort(left), ...middle, ...quicksort(right)];\n"
                    f"}}"
                )
                return code, 0.85

        elif 'search' in op or 'recherche' in intent.raw.lower() or 'find' in op:
            # Binary search
            if lang == 'python':
                code = (
                    f"def binary_search(arr, target):\n"
                    f"    left, right = 0, len(arr) - 1\n"
                    f"    while left <= right:\n"
                    f"        mid = (left + right) // 2\n"
                    f"        if arr[mid] == target:\n"
                    f"            return mid\n"
                    f"        elif arr[mid] < target:\n"
                    f"            left = mid + 1\n"
                    f"        else:\n"
                    f"            right = mid - 1\n"
                    f"    return -1"
                )
                return code, 0.90

        # Fibonacci
        if 'fibo' in intent.raw.lower() or 'fibonacci' in intent.raw.lower():
            if lang == 'python':
                code = (
                    f"def fibonacci(n):\n"
                    f"    if n <= 1:\n"
                    f"        return n\n"
                    f"    a, b = 0, 1\n"
                    f"    for _ in range(2, n + 1):\n"
                    f"        a, b = b, a + b\n"
                    f"    return b"
                )
                return code, 0.95

        # Factorielle
        if 'factorielle' in intent.raw.lower() or 'factorial' in intent.raw.lower():
            if intent.constraints and 'recursive' in intent.constraints:
                if lang == 'python':
                    code = f"def factorial(n):\n    return 1 if n <= 1 else n * factorial(n - 1)"
                    return code, 0.90
            if lang == 'python':
                code = f"def factorial(n):\n    result = 1\n    for i in range(2, n + 1):\n        result *= i\n    return result"
                return code, 0.95
        
        # Merge sort
        if 'merge sort' in raw or 'mergesort' in raw or 'fusion' in raw:
            if lang == 'python':
                code = (f"def mergesort(arr):\n"
                        f"    if len(arr) <= 1:\n"
                        f"        return arr\n"
                        f"    mid = len(arr) // 2\n"
                        f"    left = mergesort(arr[:mid])\n"
                        f"    right = mergesort(arr[mid:])\n"
                        f"    return _merge(left, right)\n\n"
                        f"def _merge(left, right):\n"
                        f"    result = []\n"
                        f"    i = j = 0\n"
                        f"    while i < len(left) and j < len(right):\n"
                        f"        if left[i] <= right[j]:\n"
                        f"            result.append(left[i]); i += 1\n"
                        f"        else:\n"
                        f"            result.append(right[j]); j += 1\n"
                        f"    result.extend(left[i:])\n"
                        f"    result.extend(right[j:])\n"
                        f"    return result")
                return code, 0.90
        
        # Bubble sort
        if 'bubble' in raw or 'bulle' in raw:
            if lang == 'python':
                code = (f"def bubble_sort(arr):\n"
                        f"    n = len(arr)\n"
                        f"    for i in range(n):\n"
                        f"        for j in range(0, n - i - 1):\n"
                        f"            if arr[j] > arr[j + 1]:\n"
                        f"                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n"
                        f"    return arr")
                return code, 0.90
        
        # Two Sum
        if 'two sum' in raw or 'deux sommes' in raw:
            if lang == 'python':
                code = (f"def two_sum(nums, target):\n"
                        f"    seen = {{}}\n"
                        f"    for i, num in enumerate(nums):\n"
                        f"        complement = target - num\n"
                        f"        if complement in seen:\n"
                        f"            return [seen[complement], i]\n"
                        f"        seen[num] = i\n"
                        f"    return []")
                return code, 0.95
        
        # Palindrome (algorithm)
        if 'palindrome' in raw:
            if lang == 'python':
                code = f"def is_palindrome(s):\n    s = ''.join(c.lower() for c in s if c.isalnum())\n    return s == s[::-1]"
                return code, 0.95
        
        # FizzBuzz
        if 'fizzbuzz' in raw or 'fizz buzz' in raw:
            if lang == 'python':
                code = (f"def fizzbuzz(n):\n"
                        f"    result = []\n"
                        f"    for i in range(1, n + 1):\n"
                        f"        if i % 15 == 0:\n"
                        f"            result.append('FizzBuzz')\n"
                        f"        elif i % 3 == 0:\n"
                        f"            result.append('Fizz')\n"
                        f"        elif i % 5 == 0:\n"
                        f"            result.append('Buzz')\n"
                        f"        else:\n"
                        f"            result.append(str(i))\n"
                        f"    return result")
                return code, 0.95
        
        # Valid parentheses
        if 'parenthese' in raw or 'parentheses' in raw or 'brackets' in raw:
            if lang == 'python':
                code = (f"def is_valid_parentheses(s):\n"
                        f"    stack = []\n"
                        f"    pairs = {{')': '(', ']': '[', '}}': '{{'}}\n"
                        f"    for c in s:\n"
                        f"        if c in '([{{':\n"
                        f"            stack.append(c)\n"
                        f"        elif c in ')]}}':\n"
                        f"            if not stack or stack.pop() != pairs[c]:\n"
                        f"                return False\n"
                        f"    return not stack")
                return code, 0.90
        
        # Reverse linked list
        if 'linked list' in raw or 'liste chainee' in raw or 'liste chaînée' in raw:
            if lang == 'python':
                code = (f"class Node:\n"
                        f"    def __init__(self, val=0, next=None):\n"
                        f"        self.val = val\n"
                        f"        self.next = next\n\n"
                        f"def reverse_linked_list(head):\n"
                        f"    prev = None\n"
                        f"    current = head\n"
                        f"    while current:\n"
                        f"        nxt = current.next\n"
                        f"        current.next = prev\n"
                        f"        prev = current\n"
                        f"        current = nxt\n"
                        f"    return prev")
                return code, 0.90
        
        # Caesar cipher
        if 'caesar' in raw or 'cesar' in raw or 'cesar' in raw or 'chiffrement' in raw:
            if lang == 'python':
                code = (f"def caesar_cipher(text, shift):\n"
                        f"    result = ''\n"
                        f"    for c in text:\n"
                        f"        if c.isalpha():\n"
                        f"            base = ord('a') if c.islower() else ord('A')\n"
                        f"            result += chr((ord(c) - base + shift) % 26 + base)\n"
                        f"        else:\n"
                        f"            result += c\n"
                        f"    return result")
                return code, 0.90

        return self._synth_function(intent, facts)

    def _synth_pattern(self, intent: CodeIntent, facts: List[FactRecord]) -> Tuple[str, float]:
        """Génère un design pattern."""
        lang = intent.language
        raw = intent.raw.lower()

        if 'singleton' in raw:
            if lang == 'python':
                code = (
                    f"class Singleton:\n"
                    f"    _instance = None\n\n"
                    f"    def __new__(cls):\n"
                    f"        if cls._instance is None:\n"
                    f"            cls._instance = super().__new__(cls)\n"
                    f"        return cls._instance"
                )
                return code, 0.90
            elif lang in ('javascript', 'typescript'):
                code = (
                    f"class Singleton {{\n"
                    f"    static instance = null;\n\n"
                    f"    constructor() {{\n"
                    f"        if (Singleton.instance) return Singleton.instance;\n"
                    f"        Singleton.instance = this;\n"
                    f"    }}\n"
                    f"}}"
                )
                return code, 0.85

        elif 'factory' in raw:
            if lang == 'python':
                code = (
                    f"class Factory:\n"
                    f"    @staticmethod\n"
                    f"    def create(type_name):\n"
                    f"        if type_name == 'A':\n"
                    f"            return ProductA()\n"
                    f"        elif type_name == 'B':\n"
                    f"            return ProductB()\n"
                    f"        raise ValueError(f'Unknown type: {{type_name}}')"
                )
                return code, 0.85

        elif 'observer' in raw:
            if lang == 'python':
                code = (
                    f"class Observer:\n"
                    f"    def update(self, data):\n"
                    f"        pass\n\n"
                    f"class Subject:\n"
                    f"    def __init__(self):\n"
                    f"        self._observers = []\n"
                    f"    def attach(self, observer):\n"
                    f"        self._observers.append(observer)\n"
                    f"    def notify(self, data):\n"
                    f"        for obs in self._observers:\n"
                    f"            obs.update(data)"
                )
                return code, 0.85

        return self._synth_function(intent, facts)

    def _synth_query(self, intent: CodeIntent, facts: List[FactRecord]) -> Tuple[str, float]:
        """Génère une requête SQL."""
        entity = intent.entity if intent.entity != 'generic' else 'table'
        op = intent.operation

        if op == 'find' or op == 'create':
            code = f"SELECT * FROM {entity} WHERE id = ?;"
            return code, 0.85
        elif op == 'create':
            code = f"INSERT INTO {entity} (name, value) VALUES (?, ?);"
            return code, 0.85
        else:
            code = f"-- Query for {entity}\nSELECT * FROM {entity} LIMIT 10;"
            return code, 0.75

    def _synth_bugfix(self, intent: CodeIntent, facts: List[FactRecord]) -> Tuple[str, float]:
        """Tente de suggérer une correction de bug."""
        # Pour l'instant, retourne un template de débogage
        return (
            f"# Original buggy code:\n"
            f"# [code to fix would be here]\n\n"
            f"# Suggested fix:\n"
            f"# 1. Check for off-by-one errors\n"
            f"# 2. Verify null/undefined checks\n"
            f"# 3. Ensure type consistency"
        ), 0.50

    # ═══════════════════════════════════════════════════════════════
    # NOUVEAUX TEMPLATES V2 — 50+ opérations
    # ═══════════════════════════════════════════════════════════════

    def _synth_binary_search(self, lang, name, entity, facts):
        if lang == 'python':
            return (f"def {name}(arr, target):\n"
                    f"    left, right = 0, len(arr) - 1\n"
                    f"    while left <= right:\n"
                    f"        mid = (left + right) // 2\n"
                    f"        if arr[mid] == target:\n"
                    f"            return mid\n"
                    f"        elif arr[mid] < target:\n"
                    f"            left = mid + 1\n"
                    f"        else:\n"
                    f"            right = mid - 1\n"
                    f"    return -1"), 0.95
        return (f"function {name}(arr, target) {{\n"
                f"    let left = 0, right = arr.length - 1;\n"
                f"    while (left <= right) {{\n"
                f"        const mid = Math.floor((left + right) / 2);\n"
                f"        if (arr[mid] === target) return mid;\n"
                f"        else if (arr[mid] < target) left = mid + 1;\n"
                f"        else right = mid - 1;\n"
                f"    }}\n    return -1;\n}}"), 0.95

    def _synth_bfs(self, lang, name, entity, facts):
        return (f"from collections import deque\n\n"
                f"def {name}(graph, start):\n"
                f"    visited = set()\n"
                f"    queue = deque([start])\n"
                f"    result = []\n"
                f"    while queue:\n"
                f"        node = queue.popleft()\n"
                f"        if node not in visited:\n"
                f"            visited.add(node)\n"
                f"            result.append(node)\n"
                f"            queue.extend(graph.get(node, []))\n"
                f"    return result"), 0.95

    def _synth_dfs(self, lang, name, entity, facts):
        return (f"def {name}(graph, start, visited=None):\n"
                f"    if visited is None:\n"
                f"        visited = set()\n"
                f"    visited.add(start)\n"
                f"    for neighbor in graph.get(start, []):\n"
                f"        if neighbor not in visited:\n"
                f"            {name}(graph, neighbor, visited)\n"
                f"    return visited"), 0.95

    def _synth_tree(self, lang, name, entity, facts):
        return (f"class TreeNode:\n"
                f"    def __init__(self, val=0, left=None, right=None):\n"
                f"        self.val = val\n"
                f"        self.left = left\n"
                f"        self.right = right\n\n"
                f"def {name}(root):\n"
                f"    if not root:\n"
                f"        return []\n"
                f"    result = []\n"
                f"    def inorder(node):\n"
                f"        if node:\n"
                f"            inorder(node.left)\n"
                f"            result.append(node.val)\n"
                f"            inorder(node.right)\n"
                f"    inorder(root)\n"
                f"    return result"), 0.95

    def _synth_linked_list(self, lang, name, entity, facts):
        return (f"class ListNode:\n"
                f"    def __init__(self, val=0, next=None):\n"
                f"        self.val = val\n"
                f"        self.next = next\n\n"
                f"def {name}(head):\n"
                f"    current = head\n"
                f"    while current:\n"
                f"        # Traiter current.val\n"
                f"        current = current.next\n"
                f"    return head"), 0.90

    def _synth_stack(self, lang, name, entity, facts):
        return (f"class Stack:\n"
                f"    def __init__(self):\n"
                f"        self.items = []\n"
                f"    def push(self, item):\n"
                f"        self.items.append(item)\n"
                f"    def pop(self):\n"
                f"        return self.items.pop() if self.items else None\n"
                f"    def peek(self):\n"
                f"        return self.items[-1] if self.items else None\n"
                f"    def is_empty(self):\n"
                f"        return len(self.items) == 0"), 0.95

    def _synth_queue(self, lang, name, entity, facts):
        return (f"from collections import deque\n\n"
                f"class Queue:\n"
                f"    def __init__(self):\n"
                f"        self.items = deque()\n"
                f"    def enqueue(self, item):\n"
                f"        self.items.append(item)\n"
                f"    def dequeue(self):\n"
                f"        return self.items.popleft() if self.items else None\n"
                f"    def is_empty(self):\n"
                f"        return len(self.items) == 0"), 0.95

    def _synth_hashmap(self, lang, name, entity, facts):
        return (f"class HashMap:\n"
                f"    def __init__(self, size=100):\n"
                f"        self.size = size\n"
                f"        self.buckets = [[] for _ in range(size)]\n"
                f"    def _hash(self, key):\n"
                f"        return hash(key) % self.size\n"
                f"    def put(self, key, value):\n"
                f"        idx = self._hash(key)\n"
                f"        for i, (k, v) in enumerate(self.buckets[idx]):\n"
                f"            if k == key:\n"
                f"                self.buckets[idx][i] = (key, value)\n"
                f"                return\n"
                f"        self.buckets[idx].append((key, value))\n"
                f"    def get(self, key):\n"
                f"        idx = self._hash(key)\n"
                f"        for k, v in self.buckets[idx]:\n"
                f"            if k == key:\n"
                f"                return v\n"
                f"        return None"), 0.90

    def _synth_heap(self, lang, name, entity, facts):
        return (f"import heapq\n\n"
                f"class MinHeap:\n"
                f"    def __init__(self):\n"
                f"        self.heap = []\n"
                f"    def push(self, val):\n"
                f"        heapq.heappush(self.heap, val)\n"
                f"    def pop(self):\n"
                f"        return heapq.heappop(self.heap) if self.heap else None\n"
                f"    def peek(self):\n"
                f"        return self.heap[0] if self.heap else None"), 0.95

    def _synth_graph(self, lang, name, entity, facts):
        return (f"class Graph:\n"
                f"    def __init__(self):\n"
                f"        self.graph = {{}}\n"
                f"    def add_edge(self, u, v, weight=1):\n"
                f"        if u not in self.graph:\n"
                f"            self.graph[u] = []\n"
                f"        self.graph[u].append((v, weight))\n"
                f"    def get_neighbors(self, u):\n"
                f"        return self.graph.get(u, [])"), 0.90

    def _synth_dp(self, lang, name, entity, facts):
        return (f"def {name}(n):\n"
                f"    dp = [0] * (n + 1)\n"
                f"    dp[0] = 1\n"
                f"    for i in range(1, n + 1):\n"
                f"        dp[i] = dp[i-1] + (dp[i-2] if i >= 2 else 0)\n"
                f"    return dp[n]"), 0.85

    def _synth_greedy(self, lang, name, entity, facts):
        return (f"def {name}(items):\n"
                f"    items.sort(key=lambda x: x[1], reverse=True)\n"
                f"    result = []\n"
                f"    for item, weight in items:\n"
                f"        if weight <= capacity:\n"
                f"            result.append(item)\n"
                f"            capacity -= weight\n"
                f"    return result"), 0.85

    def _synth_encode(self, lang, name, entity, facts):
        return (f"import base64\n\n"
                f"def {name}(data: str) -> str:\n"
                f"    return base64.b64encode(data.encode()).decode()"), 0.95

    def _synth_decode(self, lang, name, entity, facts):
        return (f"import base64\n\n"
                f"def {name}(data: str) -> str:\n"
                f"    return base64.b64decode(data.encode()).decode()"), 0.95

    def _synth_regex(self, lang, name, entity, facts):
        return (f"import re\n\n"
                f"def {name}(text, pattern):\n"
                f"    matches = re.findall(pattern, text)\n"
                f"    return matches"), 0.95

    def _synth_matrix(self, lang, name, entity, facts):
        return (f"def {name}(matrix):\n"
                f"    if not matrix or not matrix[0]: return []\n"
                f"    rows, cols = len(matrix), len(matrix[0])\n"
                f"    result = [[0]*cols for _ in range(rows)]\n"
                f"    for i in range(rows):\n"
                f"        for j in range(cols):\n"
                f"            result[i][j] = matrix[i][j]\n"
                f"    return result"), 0.85

    def _synth_stats(self, lang, name, entity, facts):
        return (f"import statistics\n\n"
                f"def {name}(data):\n"
                f"    return {{\n"
                f"        'mean': statistics.mean(data),\n"
                f"        'median': statistics.median(data),\n"
                f"        'stdev': statistics.stdev(data) if len(data) > 1 else 0\n"
                f"    }}"), 0.95

    def _synth_read_file(self, lang, name, entity, facts):
        return (f"def {name}(filepath):\n"
                f"    with open(filepath, 'r', encoding='utf-8') as f:\n"
                f"        return f.read()"), 0.95

    def _synth_write_file(self, lang, name, entity, facts):
        return (f"def {name}(filepath, content):\n"
                f"    with open(filepath, 'w', encoding='utf-8') as f:\n"
                f"        f.write(content)"), 0.95

    def _synth_parse_csv(self, lang, name, entity, facts):
        return (f"import csv\n\n"
                f"def {name}(filepath):\n"
                f"    with open(filepath, 'r', encoding='utf-8') as f:\n"
                f"        reader = csv.DictReader(f)\n"
                f"        return [row for row in reader]"), 0.95

    def _synth_parse_json(self, lang, name, entity, facts):
        return (f"import json\n\n"
                f"def {name}(filepath):\n"
                f"    with open(filepath, 'r', encoding='utf-8') as f:\n"
                f"        return json.load(f)"), 0.95

    def _synth_http_get(self, lang, name, entity, facts):
        return (f"import requests\n\n"
                f"def {name}(url, headers=None):\n"
                f"    response = requests.get(url, headers=headers)\n"
                f"    response.raise_for_status()\n"
                f"    return response.json()"), 0.95

    def _synth_http_post(self, lang, name, entity, facts):
        return (f"import requests\n\n"
                f"def {name}(url, data, headers=None):\n"
                f"    response = requests.post(url, json=data, headers=headers)\n"
                f"    response.raise_for_status()\n"
                f"    return response.json()"), 0.95

    def _synth_hash_password(self, lang, name, entity, facts):
        return (f"import hashlib\n\n"
                f"def {name}(password: str) -> str:\n"
                f"    return hashlib.sha256(password.encode()).hexdigest()"), 0.95

    def _synth_encrypt(self, lang, name, entity, facts):
        return (f"from cryptography.fernet import Fernet\n\n"
                f"def {name}(data: str, key: bytes) -> str:\n"
                f"    f = Fernet(key)\n"
                f"    return f.encrypt(data.encode()).decode()"), 0.90

    def _synth_token(self, lang, name, entity, facts):
        return (f"import jwt\nimport datetime\n\n"
                f"def {name}(payload: dict, secret: str) -> str:\n"
                f"    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(hours=1)\n"
                f"    return jwt.encode(payload, secret, algorithm='HS256')"), 0.90

    def _synth_unit_test(self, lang, name, entity, facts):
        return (f"import unittest\n\n"
                f"class Test{name.capitalize()}(unittest.TestCase):\n"
                f"    def test_basic(self):\n"
                f"        result = {name}([])\n"
                f"        self.assertIsNotNone(result)\n"
                f"    def test_edge_case(self):\n"
                f"        result = {name}(None)\n"
                f"        self.assertIsNone(result)\n\n"
                f"if __name__ == '__main__':\n"
                f"    unittest.main()"), 0.90

    def _synth_decorator(self, lang, name, entity, facts):
        return (f"import functools\n\n"
                f"def {name}(func):\n"
                f"    @functools.wraps(func)\n"
                f"    def wrapper(*args, **kwargs):\n"
                f"        print(f'Calling {{func.__name__}}')\n"
                f"        result = func(*args, **kwargs)\n"
                f"        print(f'{{func.__name__}} returned {{result}}')\n"
                f"        return result\n"
                f"    return wrapper"), 0.95

    def _synth_generator(self, lang, name, entity, facts):
        return (f"def {name}(start, end):\n"
                f"    current = start\n"
                f"    while current <= end:\n"
                f"        yield current\n"
                f"        current += 1"), 0.95

    def _synth_comprehension(self, lang, name, entity, facts):
        return (f"def {name}(data):\n"
                f"    return [x for x in data if x is not None]"), 0.95

    def _synth_context_mgr(self, lang, name, entity, facts):
        return (f"from contextlib import contextmanager\n\n"
                f"@contextmanager\n"
                f"def {name}():\n"
                f"    print('Enter')\n"
                f"    try:\n"
                f"        yield\n"
                f"    finally:\n"
                f"        print('Exit')"), 0.90

    def _synth_react_hook(self, lang, name, entity, facts):
        return (f"import React, {{ useState, useEffect }} from 'react';\n\n"
                f"function {name}() {{\n"
                f"    const [data, setData] = useState(null);\n"
                f"    useEffect(() => {{\n"
                f"        fetch('/api/data')\n"
                f"            .then(res => res.json())\n"
                f"            .then(setData);\n"
                f"    }}, []);\n"
                f"    return (<div>{{JSON.stringify(data)}}</div>);\n"
                f"}}"), 0.90

    def _synth_datetime(self, lang, name, entity, facts):
        return (f"from datetime import datetime, timedelta\n\n"
                f"def {name}():\n"
                f"    now = datetime.now()\n"
                f"    return now.strftime('%Y-%m-%d %H:%M:%S')"), 0.95

    def _synth_argparse(self, lang, name, entity, facts):
        return (f"import argparse\n\n"
                f"def {name}():\n"
                f"    parser = argparse.ArgumentParser()\n"
                f"    parser.add_argument('input', help='Input file')\n"
                f"    parser.add_argument('-o', '--output', default='output.txt')\n"
                f"    parser.add_argument('-v', '--verbose', action='store_true')\n"
                f"    return parser.parse_args()"), 0.95

    def _synth_logging(self, lang, name, entity, facts):
        return (f"import logging\n\n"
                f"logging.basicConfig(level=logging.INFO)\n"
                f"logger = logging.getLogger(__name__)\n\n"
                f"def {name}():\n"
                f"    logger.info('Starting')\n"
                f"    try:\n"
                f"        # main logic\n"
                f"        pass\n"
                f"    except Exception as e:\n"
                f"        logger.error(f'Error: {{e}}')\n"
                f"    logger.info('Done')"), 0.90

    def _synth_cache(self, lang, name, entity, facts):
        return (f"from functools import lru_cache\n\n"
                f"@lru_cache(maxsize=128)\n"
                f"def {name}(n):\n"
                f"    if n <= 1:\n"
                f"        return n\n"
                f"    return {name}(n-1) + {name}(n-2)"), 0.95

    def _synth_serialize(self, lang, name, entity, facts):
        return (f"import json\n\n"
                f"def {name}(obj):\n"
                f"    return json.dumps(obj, default=str)"), 0.95

    def _synth_deserialize(self, lang, name, entity, facts):
        return (f"import json\n\n"
                f"def {name}(data: str):\n"
                f"    return json.loads(data)"), 0.95

    def _synth_retry(self, lang, name, entity, facts):
        return (f"import time\nfrom functools import wraps\n\n"
                f"def {name}(max_retries=3, delay=1):\n"
                f"    def decorator(func):\n"
                f"        @wraps(func)\n"
                f"        def wrapper(*args, **kwargs):\n"
                f"            for attempt in range(max_retries):\n"
                f"                try:\n"
                f"                    return func(*args, **kwargs)\n"
                f"                except Exception as e:\n"
                f"                    if attempt == max_retries - 1:\n"
                f"                        raise\n"
                f"                    time.sleep(delay)\n"
                f"        return wrapper\n"
                f"    return decorator"), 0.95

    def _synth_format(self, lang, name, entity, facts):
        return (f"def {name}(value, fmt='json'):\n"
                f"    if fmt == 'json':\n"
                f"        import json\n"
                f"        return json.dumps(value, indent=2, default=str)\n"
                f"    elif fmt == 'csv':\n"
                f"        return ','.join(str(v) for v in value)\n"
                f"    return str(value)"), 0.90

    def _synth_truncate(self, lang, name, entity, facts):
        return (f"def {name}(text, max_len=100):\n"
                f"    if len(text) <= max_len:\n"
                f"        return text\n"
                f"    return text[:max_len-3] + '...'"), 0.95

    def _synth_pad(self, lang, name, entity, facts):
        return (f"def {name}(text, length, char=' '):\n"
                f"    return str(text).ljust(length, char)"), 0.90

    def _synth_probability(self, lang, name, entity, facts):
        return (f"import random\n\n"
                f"def {name}(items, weights=None):\n"
                f"    return random.choices(items, weights=weights, k=1)[0]"), 0.85

    def _synth_geometry(self, lang, name, entity, facts):
        return (f"import math\n\n"
                f"def {name}(x1, y1, x2, y2):\n"
                f"    return math.sqrt((x2-x1)**2 + (y2-y1)**2)"), 0.90

    def _synth_env_var(self, lang, name, entity, facts):
        return (f"import os\n\n"
                f"def {name}(key, default=None):\n"
                f"    return os.environ.get(key, default)"), 0.95

    def _synth_rate_limit(self, lang, name, entity, facts):
        return (f"import time\nfrom collections import deque\n\n"
                f"class RateLimiter:\n"
                f"    def __init__(self, max_calls=10, period=60):\n"
                f"        self.max_calls = max_calls\n"
                f"        self.period = period\n"
                f"        self.calls = deque()\n"
                f"    def allow(self):\n"
                f"        now = time.time()\n"
                f"        while self.calls and self.calls[0] < now - self.period:\n"
                f"            self.calls.popleft()\n"
                f"        if len(self.calls) < self.max_calls:\n"
                f"            self.calls.append(now)\n"
                f"            return True\n"
                f"        return False"), 0.90

    def _synth_react_component(self, lang, name, entity, facts):
        return (f"import React from 'react';\n\n"
                f"function {name}({{ title, children }}) {{\n"
                f"    return (\n"
                f"        <div className=\"{name.lower()}\">\n"
                f"            <h1>{{title}}</h1>\n"
                f"            <div className=\"content\">{{children}}</div>\n"
                f"        </div>\n"
                f"    );\n"
                f"}}\n\n"
                f"export default {name};"), 0.90

    def _synth_mock(self, lang, name, entity, facts):
        return (f"from unittest.mock import Mock, patch\n\n"
                f"def {name}():\n"
                f"    mock_obj = Mock()\n"
                f"    mock_obj.method.return_value = 'mocked'\n"
                f"    return mock_obj"), 0.85

    def _synth_decrypt(self, lang, name, entity, facts):
        return (f"from cryptography.fernet import Fernet\n\n"
                f"def {name}(encrypted_data: str, key: bytes) -> str:\n"
                f"    f = Fernet(key)\n"
                f"    return f.decrypt(encrypted_data.encode()).decode()"), 0.90


# ═══════════════════════════════════════════════════════════════════════════════
# CODE GENERATOR — Interface publique
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GeneratedCode:
    """Résultat de génération de code."""
    code: str
    language: str
    intent: CodeIntent
    confidence: float
    facts_used: int
    pattern_used: str = ""
    source: str = "template"  # "template" ou "corpus"


class CodeGenerator:
    """
    Générateur de code ondulatoire.
    
    Combine :
      - PatternDetection (langage naturel → intention structurée)
      - Brain Retrieval (faits techniques pertinents)
      - Wave Synthesis (patterns + faits → code concret)
    """

    def __init__(self, brain: HarmonicBrain, corpus=None):
        self.brain = brain
        self.detector = PatternDetector()
        self.synthesizer = WaveSynthesizer()
        self.corpus = corpus  # CodeCorpus pour fallback

    def generate(self, question: str, lang: str = 'fr') -> GeneratedCode:
        """
        Génère du code à partir d'une requête en langage naturel.
        
        Pipeline :
          1. Pattern Detection → intent structuré
          2. Brain Retrieval → faits techniques
          3. Wave Synthesis → template (si connu)
          4. Corpus Search → fallback ondulatoire (si template faible)
        """
        # 1. PATTERN DETECTION
        intent = self.detector.detect(question)

        # 2. BRAIN RETRIEVAL
        enriched = f"{question} {intent.language} {intent.operation} {intent.entity} {intent.intent}"
        candidates = self.brain.unconscious.retrieve(enriched, max_results=10, sector_boost='code')
        facts = [rec for rec, _ in candidates[:8]]

        # 3. WAVE SYNTHESIS (template)
        code, confidence = self.synthesizer.synthesize(intent, facts)

        # Ajuster la confiance
        if facts:
            avg_amplitude = sum(f.amplitude for f in facts) / len(facts)
            confidence = min(1.0, confidence * (0.7 + 0.3 * min(1.0, avg_amplitude / 5.0)))

        # 4. FALLBACK CORPUS si le template est faible ou générique
        source = "template"
        is_generic = ('TODO' in code or 'pass' in code or 
                      code.strip().startswith('--') or
                      len(code.strip()) < 30)
        
        # 🔥 Détecter les réponses template trop génériques
        # Si la requête contient des termes spécifiques absents du code → fallback
        if not is_generic and confidence >= 0.6:
            q_tech_terms = {'email', 'pytest', 'unittest', 'docker', 'compose', 'debounce',
                          'throttle', 'memoize', 'cors', 'jwt', 'aes', 'bcrypt', 'oauth',
                          'graphql', 'kubernetes', 'terraform', 'ansible', 'nginx'}
            q_lower = question.lower()
            code_lower = code.lower()
            for term in q_tech_terms:
                if term in q_lower and term not in code_lower:
                    is_generic = True
                    break
        
        if confidence < 0.6 or is_generic:
            if self.corpus is not None and len(self.corpus.snippets) > 0:
                # Traduire les termes FR→EN pour meilleur matching
                query_en = self._fr_to_en_tech(question)
                results = self.corpus.search(query_en, top_k=2)
                if not results:
                    results = self.corpus.search(question, top_k=2)  # fallback FR
                
                if results:
                    corpus_code, corpus_lang, corpus_score = results[0]
                    # Seuil abaissé à 0.10 pour le cross-langue
                    if corpus_score > 0.10:
                        code = corpus_code
                        confidence = min(0.8, corpus_score * 2.5)
                        source = "corpus"
                        intent.language = corpus_lang

        return GeneratedCode(
            code=code,
            language=intent.language,
            intent=intent,
            confidence=confidence,
            facts_used=len(facts),
            pattern_used=f"{intent.intent}/{intent.operation}",
            source=source,
        )

    def _fr_to_en_tech(self, question: str) -> str:
        """Traduit les termes techniques FR→EN pour le corpus search."""
        FR_TO_EN = {
            'fonction': 'function', 'écris': 'write', 'crée': 'create',
            'génère': 'generate', 'implémente': 'implement', 'trie': 'sort',
            'inverse': 'reverse', 'chaîne': 'string', 'liste': 'list',
            'tableau': 'array', 'dictionnaire': 'dictionary', 'fichier': 'file',
            'mot de passe': 'password', 'hacher': 'hash', 'chiffrer': 'encrypt',
            'déchiffrer': 'decrypt', 'valide': 'validate', 'email': 'email',
            'courriel': 'email', 'requête': 'query', 'base de données': 'database',
            'jointure': 'join', 'sélectionne': 'select', 'test unitaire': 'unittest',
            'point d accès': 'endpoint', 'api': 'api', 'route': 'route',
            'compose': 'compose', 'conteneur': 'container', 'app web': 'web app',
            'amorce': 'docker', 'docker-compose': 'docker compose',
            'nuagique': 'cloud', 'déploiement': 'deployment',
            'motif': 'pattern', 'singleton': 'singleton', 'fabrique': 'factory',
            'observateur': 'observer', 'stratégie': 'strategy',
            'algorithme': 'algorithm', 'récursif': 'recursive',
            'binaire': 'binary', 'recherche': 'search', 'rapide': 'quicksort',
            'fibonacci': 'fibonacci', 'factorielle': 'factorial',
        }
        q = question.lower()
        for fr, en in FR_TO_EN.items():
            q = q.replace(fr, en)
        return q


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO / TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from pathlib import Path
    import numpy as np

    # Charger un petit cerveau
    kb_path = Path('data/bootstrapper_output/knowledge_base_100k.npz')
    if kb_path.exists():
        data = np.load(str(kb_path), allow_pickle=True)
        all_facts = list(data['facts'])
        code_facts = [f for f in all_facts if str(f[3]).upper() == 'CODE'][:5000]
        other_facts = [f for f in all_facts if str(f[3]).upper() != 'CODE'][:2000]
        selected = code_facts + other_facts

        brain = HarmonicBrain([])
        brain.ingest_batch([(str(f[0]), str(f[1]), str(f[2]), str(f[3])) for f in selected])
        gen = CodeGenerator(brain)

        tests = [
            "écris une fonction Python qui inverse une chaîne",
            "crée une fonction JavaScript pour trier un tableau",
            "génère un singleton en Python",
            "écris une fonction récursive qui inverse une chaîne en Python",
            "implémente le tri rapide en Python",
        ]

        for q in tests:
            result = gen.generate(q)
            print(f"\n{'='*60}")
            print(f"Q: {q}")
            print(f"Intent: {result.intent.intent} | Lang: {result.language} | Op: {result.intent.operation}")
            print(f"Confidence: {result.confidence:.0%} | Facts: {result.facts_used}")
            print(f"---")
            print(result.code)
    else:
        print("KB not found. Run with: python code_generator.py")
