"""
KA Server — Routes Code (Génération/Analyse)
=============================================
Endpoints pour génération de code, analyse, exécution sandboxée.
"""

import logging
import re
from flask import request, jsonify

log = logging.getLogger(__name__)


def register_code_routes(app, services):
    """Enregistre les routes Code."""
    
    harmonic_ai = services.get('harmonic_ai')
    brain = services.get('brain')
    wave_code_generator = services.get('wave_code_generator')
    
    @app.route('/api/code/generate', methods=['POST', 'OPTIONS'])
    def api_code_generate():
        """Génère du code à partir d'une description."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        prompt = data.get('prompt', '').strip()
        language = data.get('language', 'python')
        style = data.get('style', 'clean')  # clean, documented, minimal, functional
        context = data.get('context', '')  # Code existant pour contexte
        
        if not prompt:
            return jsonify({'error': 'Prompt requis', 'code': 'MISSING_PROMPT'}), 400
        
        # Détecter intention wave-code
        wave_result = _try_wave_generation(prompt, language, context)
        if wave_result:
            return jsonify(wave_result)
        
        # Fallback Harmonic AI
        if harmonic_ai and hasattr(harmonic_ai, 'ask'):
            try:
                full_prompt = _build_code_prompt(prompt, language, style, context)
                result = harmonic_ai.ask(full_prompt)
                code = result.get('answer', '') if isinstance(result, dict) else str(result)
                code = _extract_code(code, language)
                
                return jsonify({
                    'success': True,
                    'code': code,
                    'language': language,
                    'source': 'harmonic_ai',
                    'prompt': prompt,
                })
            except Exception as e:
                log.warning(f"HarmonicAI code gen failed: {e}")
        
        # Fallback brain
        if brain:
            try:
                full_prompt = _build_code_prompt(prompt, language, style, context)
                response = brain.ask(full_prompt)
                code = _extract_code(response, language)
                
                return jsonify({
                    'success': True,
                    'code': code,
                    'language': language,
                    'source': 'harmonic_brain',
                    'prompt': prompt,
                })
            except Exception as e:
                log.warning(f"Brain code gen failed: {e}")
        
        return jsonify({
            'error': 'Génération de code non disponible',
            'code': 'CODE_GEN_UNAVAILABLE'
        }), 503
    
    @app.route('/api/code/analyze', methods=['POST', 'OPTIONS'])
    def api_code_analyze():
        """Analyse du code (qualité, sécurité, complexité)."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        code = data.get('code', '').strip()
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({'error': 'Code requis', 'code': 'MISSING_CODE'}), 400
        
        analysis = {
            'language': language,
            'lines': len(code.splitlines()),
            'chars': len(code),
            'functions': _count_functions(code, language),
            'classes': _count_classes(code, language),
            'complexity': _estimate_complexity(code),
            'issues': _detect_issues(code, language),
            'imports': _extract_imports(code, language),
        }
        
        return jsonify(analysis)
    
    @app.route('/api/code/explain', methods=['POST', 'OPTIONS'])
    def api_code_explain():
        """Explique le code en langage naturel."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        code = data.get('code', '').strip()
        language = data.get('language', 'python')
        detail = data.get('detail', 'medium')  # brief, medium, detailed
        
        if not code:
            return jsonify({'error': 'Code requis', 'code': 'MISSING_CODE'}), 400
        
        if harmonic_ai and hasattr(harmonic_ai, 'ask'):
            try:
                prompt = f"Explique ce code {language} ({detail}):\n```{language}\n{code}\n```"
                result = harmonic_ai.ask(prompt)
                explanation = result.get('answer', '') if isinstance(result, dict) else str(result)
                
                return jsonify({
                    'success': True,
                    'explanation': explanation,
                    'language': language,
                    'detail': detail,
                })
            except Exception as e:
                log.warning(f"Explain failed: {e}")
        
        return jsonify({
            'error': 'Explication non disponible',
            'code': 'EXPLAIN_UNAVAILABLE'
        }), 503
    
    @app.route('/api/code/refactor', methods=['POST', 'OPTIONS'])
    def api_code_refactor():
        """Propose une refactorisation du code."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        code = data.get('code', '').strip()
        language = data.get('language', 'python')
        goal = data.get('goal', 'clean')  # clean, performance, readable, modern
        
        if not code:
            return jsonify({'error': 'Code requis', 'code': 'MISSING_CODE'}), 400
        
        if harmonic_ai and hasattr(harmonic_ai, 'ask'):
            try:
                prompt = f"Refactor ce code {language} pour {goal}:\n```{language}\n{code}\n```"
                result = harmonic_ai.ask(prompt)
                refactored = result.get('answer', '') if isinstance(result, dict) else str(result)
                refactored = _extract_code(refactored, language)
                
                return jsonify({
                    'success': True,
                    'original': code,
                    'refactored': refactored,
                    'language': language,
                    'goal': goal,
                })
            except Exception as e:
                log.warning(f"Refactor failed: {e}")
        
        return jsonify({
            'error': 'Refactorisation non disponible',
            'code': 'REFACTOR_UNAVAILABLE'
        }), 503
    
    @app.route('/api/code/test', methods=['POST', 'OPTIONS'])
    def api_code_test():
        """Génère des tests unitaires pour le code."""
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json() or {}
        code = data.get('code', '').strip()
        language = data.get('language', 'python')
        framework = data.get('framework', 'pytest')  # pytest, unittest, jest, etc.
        
        if not code:
            return jsonify({'error': 'Code requis', 'code': 'MISSING_CODE'}), 400
        
        if harmonic_ai and hasattr(harmonic_ai, 'ask'):
            try:
                prompt = f"Génère des tests {framework} pour ce code {language}:\n```{language}\n{code}\n```"
                result = harmonic_ai.ask(prompt)
                tests = result.get('answer', '') if isinstance(result, dict) else str(result)
                tests = _extract_code(tests, language)
                
                return jsonify({
                    'success': True,
                    'tests': tests,
                    'language': language,
                    'framework': framework,
                })
            except Exception as e:
                log.warning(f"Test gen failed: {e}")
        
        return jsonify({
            'error': 'Génération tests non disponible',
            'code': 'TEST_GEN_UNAVAILABLE'
        }), 503
    
    @app.route('/api/code/languages', methods=['GET'])
    def api_code_languages():
        """Langages supportés."""
        return jsonify({
            'languages': [
                {'id': 'python', 'name': 'Python', 'extensions': ['.py']},
                {'id': 'javascript', 'name': 'JavaScript', 'extensions': ['.js', '.ts']},
                {'id': 'typescript', 'name': 'TypeScript', 'extensions': ['.ts']},
                {'id': 'rust', 'name': 'Rust', 'extensions': ['.rs']},
                {'id': 'go', 'name': 'Go', 'extensions': ['.go']},
                {'id': 'java', 'name': 'Java', 'extensions': ['.java']},
                {'id': 'cpp', 'name': 'C++', 'extensions': ['.cpp', '.cc', '.hpp']},
                {'id': 'c', 'name': 'C', 'extensions': ['.c', '.h']},
                {'id': 'csharp', 'name': 'C#', 'extensions': ['.cs']},
                {'id': 'php', 'name': 'PHP', 'extensions': ['.php']},
                {'id': 'ruby', 'name': 'Ruby', 'extensions': ['.rb']},
                {'id': 'swift', 'name': 'Swift', 'extensions': ['.swift']},
                {'id': 'kotlin', 'name': 'Kotlin', 'extensions': ['.kt']},
                {'id': 'bash', 'name': 'Bash', 'extensions': ['.sh']},
                {'id': 'sql', 'name': 'SQL', 'extensions': ['.sql']},
            ]
        })


def _try_wave_generation(prompt: str, language: str, context: str) -> dict | None:
    """Tente génération via wave-code-generator si dispo."""
    try:
        from wave_code_generator import generate_code
        result = generate_code(prompt, language=language, context=context)
        if result and result.get('code'):
            return {
                'success': True,
                'code': result['code'],
                'language': language,
                'source': 'wave_code_generator',
                'intent': result.get('intent', 'unknown'),
            }
    except Exception:
        pass
    return None


def _build_code_prompt(prompt: str, language: str, style: str, context: str) -> str:
    """Construit le prompt pour génération de code."""
    style_instructions = {
        'clean': 'Code propre, lisible, bien structuré',
        'documented': 'Code avec docstrings et commentaires complets',
        'minimal': 'Code minimal, concis',
        'functional': 'Style fonctionnel, immuable',
    }
    style_desc = style_instructions.get(style, style_instructions['clean'])
    
    parts = [
        f"Génère du code {language}.",
        f"Style: {style_desc}.",
        f"Demande: {prompt}",
    ]
    
    if context:
        parts.append(f"Contexte (code existant):\n```{language}\n{context}\n```")
    
    parts.append("Réponds UNIQUEMENT avec le code, sans explication.")
    
    return '\n\n'.join(parts)


def _extract_code(text: str, language: str) -> str:
    """Extrait le code d'une réponse markdown."""
    # Chercher bloc ```language
    pattern = rf'```{language}\n(.*?)\n```'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Chercher bloc ``` générique
    match = re.search(r'```\w*\n(.*?)\n```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Retourner tel quel si pas de bloc
    return text.strip()


def _count_functions(code: str, language: str) -> int:
    """Compte les fonctions."""
    if language == 'python':
        return len(re.findall(r'^\s*def\s+\w+', code, re.MULTILINE))
    elif language in ('javascript', 'typescript'):
        return len(re.findall(r'(function\s+\w+|const\s+\w+\s*=\s*\w*\s*=>)', code))
    elif language == 'rust':
        return len(re.findall(r'fn\s+\w+', code))
    return 0


def _count_classes(code: str, language: str) -> int:
    """Compte les classes."""
    if language == 'python':
        return len(re.findall(r'^\s*class\s+\w+', code, re.MULTILINE))
    elif language in ('javascript', 'typescript'):
        return len(re.findall(r'class\s+\w+', code))
    elif language in ('java', 'csharp', 'cpp'):
        return len(re.findall(r'class\s+\w+', code))
    return 0


def _estimate_complexity(code: str) -> str:
    """Estime la complexité cyclomatique approximative."""
    # Compter structures de contrôle
    control = len(re.findall(r'\b(if|else|elif|for|while|try|except|catch|switch|case)\b', code))
    if control < 5:
        return 'low'
    elif control < 15:
        return 'medium'
    return 'high'


def _detect_issues(code: str, language: str) -> list:
    """Détecte problèmes basiques."""
    issues = []
    
    if language == 'python':
        if 'eval(' in code or 'exec(' in code:
            issues.append({'type': 'security', 'message': 'Utilisation de eval/exec (risque sécurité)'})
        if 'import *' in code:
            issues.append({'type': 'style', 'message': 'Import wildcard détecté'})
        if re.search(r'^\s*except:\s*$', code, re.MULTILINE):
            issues.append({'type': 'style', 'message': 'Except nu sans exception spécifique'})
    
    # TODO: Plus de détections selon langage
    return issues


def _extract_imports(code: str, language: str) -> list:
    """Extrait les imports."""
    imports = []
    if language == 'python':
        for match in re.finditer(r'^(?:from\s+(\S+)\s+)?import\s+(.+)$', code, re.MULTILINE):
            module = match.group(1) or ''
            names = match.group(2)
            imports.append(f"{module} {names}".strip())
    elif language in ('javascript', 'typescript'):
        for match in re.finditer(r'import\s+.*?from\s+[\'"](.+?)[\'"]', code):
            imports.append(match.group(1))
    return imports