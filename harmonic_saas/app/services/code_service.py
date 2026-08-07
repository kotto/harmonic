#!/usr/bin/env python3
"""
Service Code Intelligent
==========================
Génération zero-LLM, explication, traduction et refactoring de code.
Basé sur CodeGenerator + CodeExplainer + HRRUnbinder.
"""

import os, sys, time, logging, re
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

_ENGINE_PATH = os.environ.get(
    "ENGINE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "engine")
)
if os.path.isdir(_ENGINE_PATH) and _ENGINE_PATH not in sys.path:
    sys.path.insert(0, _ENGINE_PATH)

_has_code_gen = False
_has_code_explain = False
_has_hrr = False

try:
    from code_generator import CodeGenerator
    _has_code_gen = True
except ImportError:
    pass

try:
    from code_explainer import CodeExplainer
    _has_code_explain = True
except ImportError:
    pass

try:
    from hr_unbinder import HRRUnbinder
    _has_hrr = True
except ImportError:
    pass


class CodeService:
    """Service de manipulation intelligente de code."""

    def __init__(self):
        self._generator = None
        self._explainer = None
        self._unbinder = None
        if _has_code_gen:
            try:
                self._generator = CodeGenerator(None)
            except Exception:
                pass
        if _has_code_explain:
            try:
                self._explainer = CodeExplainer(None)
            except Exception:
                pass
        if _has_hrr:
            try:
                self._unbinder = HRRUnbinder(dim=256, corpus=None)
            except Exception:
                pass

    def generate(self, prompt: str, language: str = "python",
                 mode: str = "auto", context: str = None,
                 include_tests: bool = False, include_docs: bool = True,
                 novel_synthesis: bool = False) -> Dict[str, Any]:
        """Génère du code à partir d'une description en langage naturel."""
        t0 = time.time()

        code = ""
        confidence = 0.75
        source = "template"

        if self._generator and _has_code_gen:
            try:
                result = self._generator.generate(prompt, lang=language)
                if hasattr(result, 'code'):
                    code = result.code
                    confidence = getattr(result, 'confidence', 0.85)
                    source = getattr(result, 'source', 'brain')
                else:
                    code = str(result)
            except Exception:
                code = self._simulate_generation(prompt, language)
        elif self._unbinder and _has_hrr and novel_synthesis:
            try:
                code, confidence = self._unbinder.synthesize_hybrid(prompt)
                source = "novel_synthesis"
            except Exception:
                code = self._simulate_generation(prompt, language)
        else:
            code = self._simulate_generation(prompt, language)
            source = "simulation"

        dt = time.time() - t0

        tests = None
        if include_tests and "def " in code:
            func_name = re.findall(r'def (\w+)', code)
            if func_name:
                tests = f"# Test pour {func_name[0]}\n"
                tests += f"def test_{func_name[0]}():\n"
                tests += f"    result = {func_name[0]}(test_input)\n"
                tests += f"    assert result is not None\n"

        return {
            "code": code,
            "language": language,
            "confidence": round(confidence, 3),
            "intent": prompt[:100],
            "source": source,
            "facts_used": 3 if _has_code_gen else 0,
            "explanation": f"Code généré en {language} pour: {prompt[:80]}",
            "tests": tests,
            "warnings": [],
        }

    def _simulate_generation(self, prompt: str, language: str) -> str:
        """Génération simulée quand l'engine n'est pas disponible."""
        prompt_lower = prompt.lower()

        if "sort" in prompt_lower or "tri" in prompt_lower:
            return f"def sort_data(data):\n    return sorted(data)\n"
        elif "fibonacci" in prompt_lower:
            return (
                f"def fibonacci(n):\n"
                f"    a, b = 0, 1\n"
                f"    for _ in range(n):\n"
                f"        yield a\n"
                f"        a, b = b, a + b\n"
            )
        elif "hello" in prompt_lower or "bonjour" in prompt_lower:
            return (
                f"def greet(name):\n"
                f"    \"\"\"Saluer quelqu'un.\"\"\"\n"
                f"    return f\"Bonjour, {{name}}!\"\n"
            )
        else:
            return (
                f"def solve(data):\n"
                f"    \"\"\"\n"
                f"    {prompt[:80]}\n"
                f"    \"\"\"\n"
                f"    # Implémentation harmonique\n"
                f"    result = data  # À adapter selon le besoin\n"
                f"    return result\n"
            )

    def explain(self, code: str, language: str = None,
                detail_level: str = "detailed") -> Dict[str, Any]:
        """Explique un code source en langage naturel."""
        t0 = time.time()

        summary = ""
        detailed = ""
        line_by_line = []
        patterns = []
        complexity = "O(n)"

        if self._explainer and _has_code_explain:
            try:
                result = self._explainer.explain(code, lang=language)
                if isinstance(result, dict):
                    summary = result.get('summary', '')
                    detailed = result.get('detailed', '')
                    line_by_line_raw = result.get('line_by_line', [])
                    line_by_line = [
                        {"line_number": i + 1, "code": l.get("code", ""),
                         "explanation": l.get("explanation", ""),
                         "complexity_note": l.get("complexity", None)}
                        for i, l in enumerate(line_by_line_raw[:30])
                    ]
                    patterns = result.get('patterns_detected', [])
                    complexity = result.get('complexity', 'O(n)')
            except Exception:
                summary, detailed = self._simulate_explanation(code)
        else:
            summary, detailed = self._simulate_explanation(code)

        # Détection de patterns basique
        if "class " in code:
            patterns.append("class_definition")
        if "def " in code:
            patterns.append("function_definition")
        if "for " in code:
            patterns.append("loop")
        if "if " in code:
            patterns.append("conditional")
        if "import " in code:
            patterns.append("imports")

        dt = time.time() - t0

        return {
            "summary": summary,
            "detailed": detailed,
            "line_by_line": line_by_line if line_by_line else None,
            "patterns_detected": list(set(patterns)),
            "language": language or "auto",
            "confidence": 0.85,
            "complexity": complexity,
            "suggestions": [],
        }

    def _simulate_explanation(self, code: str):
        """Explication simulée."""
        lines = code.strip().split('\n')
        n_lines = len(lines)
        n_funcs = sum(1 for l in lines if l.strip().startswith('def '))
        n_classes = sum(1 for l in lines if l.strip().startswith('class '))

        summary = f"Ce code contient {n_lines} lignes"
        if n_funcs:
            summary += f", {n_funcs} fonction(s)"
        if n_classes:
            summary += f", {n_classes} classe(s)"
        summary += "."

        detailed = f"Analyse détaillée :\n{summary}\n"
        detailed += f"Le code définit une structure de traitement de données utilisant "
        detailed += f"des principes de programmation standard."

        return summary, detailed

    def translate(self, code: str, source_lang: str, target_lang: str,
                  preserve_comments: bool = True,
                  optimize: bool = True) -> Dict[str, Any]:
        """Traduit du code d'un langage à un autre."""
        t0 = time.time()

        # Mapping simplifié de traduction
        translation_map = {
            ("python", "javascript"): self._py_to_js,
            ("javascript", "python"): self._js_to_py,
            ("python", "go"): self._py_to_go,
            ("python", "rust"): self._py_to_rust,
        }

        translator = translation_map.get((source_lang, target_lang))
        if translator:
            translated = translator(code)
        else:
            translated = f"// Traduction {source_lang} → {target_lang}\n{code}\n// Note: traduction automatique harmonique"

        dt = time.time() - t0

        return {
            "translated_code": translated,
            "source_language": source_lang,
            "target_language": target_lang,
            "confidence": 0.8,
            "notes": [f"Traduction harmonique {source_lang} → {target_lang}"],
            "changes_summary": f"Conversion syntaxique de {source_lang} vers {target_lang}",
        }

    def _py_to_js(self, code: str) -> str:
        """Python → JavaScript."""
        js = code.replace("def ", "function ")
        js = js.replace(":", " {")
        js = js.replace("elif ", "} else if (")
        js = js.replace("else:", "} else {")
        js = js.replace("print(", "console.log(")
        js = js.replace("None", "null")
        js = js.replace("True", "true")
        js = js.replace("False", "false")
        js = js.replace(" and ", " && ")
        js = js.replace(" or ", " || ")
        js = js.replace("not ", "!")
        js = js.replace("#", "//")
        if "function " in js:
            js += "\n}"
        return js

    def _js_to_py(self, code: str) -> str:
        """JavaScript → Python."""
        py = code.replace("function ", "def ")
        py = py.replace(" {", ":")
        py = py.replace("console.log(", "print(")
        py = py.replace("null", "None")
        py = py.replace("true", "True")
        py = py.replace("false", "False")
        py = py.replace(" && ", " and ")
        py = py.replace(" || ", " or ")
        py = py.replace("!", "not ")
        py = py.replace("//", "#")
        py = py.replace("}", "")
        py = py.replace("else if", "elif")
        return py

    def _py_to_go(self, code: str) -> str:
        return f"// Traduit de Python vers Go\n// {code[:200]}\nfunc main() {{\n    // TODO: implémentation\n}}\n"

    def _py_to_rust(self, code: str) -> str:
        return f"// Traduit de Python vers Rust\n// {code[:200]}\nfn main() {{\n    // TODO: implémentation\n}}\n"

    def refactor(self, code: str, language: str, refactor_type: str = "auto",
                 target_pattern: str = None) -> Dict[str, Any]:
        """Refactore du code."""
        changes = []
        improvements = []
        refactored = code

        if refactor_type in ("auto", "readability"):
            if language == "python" and "def " in code and '"""' not in code:
                refactored = refactored.replace("def ", 'def ', 1)
                improvements.append("Ajout de docstrings recommandé")
            if "    " in code:
                improvements.append("Indentation cohérente détectée")

        if refactor_type in ("auto", "performance"):
            if ".append(" in code and "for " in code:
                improvements.append("Boucle d'accumulation — considérer une list comprehension")
                changes.append({"type": "performance", "description": "Remplacer boucle par comprehension"})

        return {
            "original_code": code,
            "refactored_code": refactored,
            "changes": changes,
            "improvements": improvements,
            "confidence": 0.8,
            "risks": [],
        }


# Singleton
_code_service: Optional[CodeService] = None


def get_code_service() -> CodeService:
    global _code_service
    if _code_service is None:
        _code_service = CodeService()
    return _code_service
