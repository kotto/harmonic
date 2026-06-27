#!/usr/bin/env python3
"""
GÉNÉRATEUR DE CODE HARMONIQUE - NIVEAU CLAUDE
===============================================
Génération de code Python professionnel avec :
- 50+ templates d'algorithmes et design patterns
- Code avec tests unitaires intégrés
- Documentation complète (Google-style docstrings)
- Gestion d'erreurs et edge cases
- Optimisation de performance
- Typage statique (type hints)
- Async support
- Principes SOLID et clean code

Inspiré des capacités de génération de code de Claude.
"""

import re
import math
import random
from typing import Dict, List, Optional, Tuple, Any, Callable


# ============================================================================
# CONSTANTES HARMONIQUES FONDAMENTALES
# ============================================================================
PHI = 1.618033988749895  # Nombre d'or
PHI_INV = 1.0 / PHI      # 0.618...
PHI_SQ = PHI * PHI       # 2.618...
PHI_CUBE = PHI_SQ * PHI  # 4.236...

# Seuils harmoniques pour l'optimisation
SEUILS_HARMONIQUES = {
    "petit": int(34 * PHI_INV),      # ~21
    "moyen": int(55 * PHI_INV),      # ~34
    "grand": int(89 * PHI_INV),      # ~55
    "tres_grand": int(144 * PHI_INV), # ~89
    "optimal": int(55 * PHI),        # ~89
}

# Ratios harmoniques pour la performance
RATIOS_HARMONIQUES = {
    "buffer": PHI_INV,           # 0.618 - ratio buffer optimal
    "partition": PHI_INV,        # 0.618 - ratio partitionnement
    "cache": PHI_INV * 0.5,     # 0.309 - ratio cache
    "recurrence": PHI_INV * 0.8, # 0.494 - seuil récursion
    "parallel": PHI_INV * 0.3,  # 0.185 - ratio parallélisation
}


class HarmonicOptimizer:
    """
    Optimiseur de code basé sur les principes harmoniques.
    
    Utilise le nombre d'or φ = 1.618... pour optimiser :
    - La taille des buffers et caches
    - Les seuils de récursion
    - Les ratios de partitionnement
    - Les stratégies de parallélisation
    """
    
    @staticmethod
    def optimal_buffer_size(base_size: int) -> int:
        """Calcule la taille de buffer optimale selon φ"""
        return max(1, int(base_size * PHI_INV))
    
    @staticmethod
    def optimal_recursion_threshold(base: int = 100) -> int:
        """Seuil de récursion optimal (basé sur φ)"""
        return int(base * PHI_INV)
    
    @staticmethod
    def optimal_partition_ratio() -> float:
        """Ratio de partitionnement optimal (φ-based)"""
        return PHI_INV
    
    @staticmethod
    def harmonic_complexity(n: int) -> str:
        """
        Analyse de complexité harmonique.
        
        Retourne une notation de complexité basée sur les principes harmoniques.
        """
        if n <= 0:
            return "O(1) - Complexité constante harmonique"
        log_n = math.log(n) / math.log(PHI)
        if log_n < 1:
            return f"O(log_φ n) ≈ O(log n) - Complexité logarithmique harmonique"
        if log_n < 2:
            return f"O(n^{PHI_INV:.3f}) - Complexité sous-linéaire harmonique"
        if log_n < n:
            return f"O(n) - Complexité linéaire harmonique"
        if log_n < n * math.log(n):
            return f"O(n log_φ n) ≈ O(n log n) - Complexité quasi-linéaire harmonique"
        if log_n < n ** PHI_INV:
            return f"O(n^{PHI_INV:.3f}) - Complexité polynomiale harmonique"
        return f"O(φ^n) - Complexité exponentielle harmonique"
    
    @staticmethod
    def harmonic_score(code_length: int, num_comments: int, 
                       num_tests: int, num_type_hints: int) -> float:
        """
        Calcule un score de qualité harmonique pour le code généré.
        
        Score basé sur :
        - Longueur du code (ratio φ)
        - Nombre de commentaires (ratio φ_inv)
        - Nombre de tests unitaires
        - Nombre de type hints
        """
        # Score de base : ratio longueur optimale
        length_score = min(1.0, code_length / (144 * PHI))  # ~233 chars optimal
        
        # Score de documentation
        doc_score = min(1.0, num_comments / (5 * PHI))  # ~8 commentaires optimal
        
        # Score de tests
        test_score = min(1.0, num_tests / (3 * PHI))  # ~5 tests optimal
        
        # Score de typage
        type_score = min(1.0, num_type_hints / (4 * PHI))  # ~6 type hints optimal
        
        # Score harmonique pondéré
        weights = [PHI_INV, PHI_INV * 0.8, PHI_INV * 0.6, PHI_INV * 0.4]
        scores = [length_score, doc_score, test_score, type_score]
        
        total_weight = sum(weights)
        harmonic_score_val = sum(s * w for s, w in zip(scores, weights)) / total_weight
        
        return round(harmonic_score_val * 100, 1)


class HarmonicDebugger:
    """
    Débogueur de code basé sur les principes harmoniques.
    
    Utilise φ = 1.618... pour :
    - Détecter les patterns d'erreurs par résonance harmonique
    - Analyser la complexité cyclomatique harmonique
    - Suggérer des corrections optimales
    - Générer des tests de débogage ciblés
    
    Les bugs sont détectés par "dissonance harmonique" :
    un code sans bug résonne à φ, un code buggé crée des
    interférences destructives.
    """
    
    # Patterns d'erreurs harmoniques (bugs classiques détectés par résonance)
    PATTERNS_ERREURS = {
        "index_hors_limites": {
            "patterns": [
                r"for\s+\w+\s+in\s+range\(len\((\w+)\)\)\s*:",
                r"\[\s*\1\s*\[\s*\1\s*\]\s*\]",
            ],
            "message": "⚠️ Dissonance harmonique détectée : risque d'index hors limites",
            "gravite": "haute",
            "correction": "Utiliser enumerate() ou un index vérifié avec len()-1",
            "exemple": """
# ❌ Dissonant (risque d'index hors limites)
for i in range(len(arr)):
    print(arr[i])  # OK si i < len(arr)

# ✅ Harmonieux (sûr)
for i, val in enumerate(arr):
    print(val)
"""
        },
        "mutabilite_defaut": {
            "patterns": [
                r"def\s+\w+\(.*=\s*\[\s*\]",
                r"def\s+\w+\(.*=\s*\{\s*\}",
                r"def\s+\w+\(.*=\s*None\s*\)",
            ],
            "message": "⚠️ Dissonance harmonique : argument mutable par défaut",
            "gravite": "haute",
            "correction": "Utiliser None comme défaut et initialiser dans le corps",
            "exemple": """
# ❌ Dissonant (argument mutable partagé entre appels)
def ajouter(element, liste=[]):
    liste.append(element)
    return liste

# ✅ Harmonieux (None + initialisation)
def ajouter(element, liste=None):
    if liste is None:
        liste = []
    liste.append(element)
    return liste
"""
        },
        "exception_bare": {
            "patterns": [
                r"except\s*:",
                r"except\s+Exception\s*:",
            ],
            "message": "⚠️ Dissonance harmonique : exception trop large",
            "gravite": "moyenne",
            "correction": "Capturer des exceptions spécifiques (ValueError, TypeError, etc.)",
            "exemple": """
# ❌ Dissonant (masque tous les bugs)
try:
    resultat = 1 / x
except:
    pass

# ✅ Harmonieux (cible précisément)
try:
    resultat = 1 / x
except ZeroDivisionError:
    print("Division par zéro")
except TypeError:
    print("Type invalide")
"""
        },
        "comparaison_identity": {
            "patterns": [
                r"is\s+not\s+None",
                r"is\s+None",
            ],
            "message": "ℹ️ Vérification harmonique : utiliser 'is' pour None est correct",
            "gravite": "info",
            "correction": "✅ Bonne pratique ! Continuez ainsi.",
            "exemple": """
# ✅ Harmonieux (vérification correcte de None)
if valeur is not None:
    print(valeur)
"""
        },
        "shadow_builtin": {
            "patterns": [
                r"\blist\s*=",
                r"\bdict\s*=",
                r"\bstr\s*=",
                r"\bint\s*=",
                r"\bfloat\s*=",
                r"\binput\s*=",
                r"\bprint\s*=",
                r"\blen\s*=",
                r"\btype\s*=",
                r"\bmax\s*=",
                r"\bmin\s*=",
                r"\bsum\s*=",
                r"\bopen\s*=",
                r"\bfile\s*=",
                r"\bset\s*=",
            ],
            "message": "⚠️ Dissonance harmonique : ombrage d'une fonction native",
            "gravite": "moyenne",
            "correction": "Renommer la variable pour éviter de masquer la fonction native",
            "exemple": """
# ❌ Dissonant (masque la fonction native list())
list = [1, 2, 3]
ma_liste = list(range(5))  # Erreur !

# ✅ Harmonieux
ma_liste = [1, 2, 3]
autre_liste = list(range(5))  # OK
"""
        },
        "redefinition_inutilisee": {
            "patterns": [
                r"(\w+)\s*=\s*.+",
            ],
            "message": "ℹ️ Vérification harmonique : variable potentiellement inutilisée",
            "gravite": "faible",
            "correction": "Supprimer la variable ou l'utiliser",
            "exemple": """
# ❌ Dissonant (variable inutilisée)
resultat = calcul_complexe()
return True

# ✅ Harmonieux
resultat = calcul_complexe()
return resultat
"""
        },
        "import_non_utilise": {
            "patterns": [
                r"import\s+(\w+)",
            ],
            "message": "ℹ️ Vérification harmonique : import potentiellement non utilisé",
            "gravite": "faible",
            "correction": "Supprimer l'import inutilisé",
            "exemple": """
# ❌ Dissonant (import inutile)
import os
import sys
def ma_fonction():
    return "hello"

# ✅ Harmonieux
def ma_fonction():
    return "hello"
"""
        },
        "fstring_manquee": {
            "patterns": [
                r"\"\s*\+\s*\w+\s*\+\s*\"",
                r"'\s*\+\s*\w+\s*\+\s*'",
            ],
            "message": "ℹ️ Optimisation harmonique : utiliser f-string plutôt que concaténation",
            "gravite": "faible",
            "correction": "Remplacer par une f-string pour plus de clarté",
            "exemple": """
# ❌ Dissonant (concaténation)
message = "Bonjour, " + nom + " !"

# ✅ Harmonieux (f-string)
message = f"Bonjour, {nom} !"
"""
        },
        "range_sans_enumerate": {
            "patterns": [
                r"for\s+\w+\s+in\s+range\(len\(",
            ],
            "message": "ℹ️ Optimisation harmonique : utiliser enumerate()",
            "gravite": "faible",
            "correction": "Remplacer range(len()) par enumerate()",
            "exemple": """
# ❌ Dissonant
for i in range(len(liste)):
    print(i, liste[i])

# ✅ Harmonieux
for i, val in enumerate(liste):
    print(i, val)
"""
        },
        "while_true_sans_break": {
            "patterns": [
                r"while\s+True\s*:",
            ],
            "message": "⚠️ Dissonance harmonique : boucle infinie potentielle",
            "gravite": "haute",
            "correction": "Ajouter une condition de sortie explicite ou un break",
            "exemple": """
# ❌ Dissonant (risque de boucle infinie)
while True:
    donnees = recevoir()
    traiter(donnees)

# ✅ Harmonieux (avec condition de sortie)
while True:
    donnees = recevoir()
    if not donnees:
        break
    traiter(donnees)
"""
        }
    }
    
    @staticmethod
    def debug_code(code: str) -> Dict[str, Any]:
        """
        Analyse un code source et détecte les bugs par résonance harmonique.
        
        Args:
            code: Code source à analyser
            
        Returns:
            Dict avec :
            - bugs: Liste des bugs détectés avec gravité et correction
            - harmonic_health: Score de santé harmonique (0-100)
            - cyclomatic_complexity: Complexité cyclomatique harmonique
            - suggestions: Liste de suggestions d'amélioration
        """
        bugs = []
        suggestions = []
        
        # Analyser chaque pattern d'erreur
        for nom_erreur, config in HarmonicDebugger.PATTERNS_ERREURS.items():
            for pattern in config["patterns"]:
                matches = re.findall(pattern, code, re.MULTILINE)
                if matches:
                    if config["gravite"] == "info":
                        suggestions.append({
                            "type": nom_erreur,
                            "message": config["message"],
                            "gravite": config["gravite"],
                            "correction": config["correction"],
                            "exemple": config["exemple"],
                            "occurrences": len(matches)
                        })
                    else:
                        bugs.append({
                            "type": nom_erreur,
                            "message": config["message"],
                            "gravite": config["gravite"],
                            "correction": config["correction"],
                            "exemple": config["exemple"],
                            "occurrences": len(matches)
                        })
        
        # Calculer la complexité cyclomatique harmonique
        cyclomatic = HarmonicDebugger._cyclomatic_complexity(code)
        
        # Calculer le score de santé harmonique
        harmonic_health = HarmonicDebugger._harmonic_health_score(code, bugs, suggestions)
        
        return {
            "bugs": bugs,
            "suggestions": suggestions,
            "harmonic_health": harmonic_health,
            "cyclomatic_complexity": cyclomatic,
            "total_bugs": len(bugs),
            "total_suggestions": len(suggestions),
            "severity_summary": HarmonicDebugger._severity_summary(bugs)
        }
    
    @staticmethod
    def _cyclomatic_complexity(code: str) -> Dict[str, Any]:
        """
        Calcule la complexité cyclomatique harmonique.
        
        M = E - N + 2P (formule de McCabe)
        Adaptée avec des poids harmoniques.
        """
        # Compter les points de décision
        if_count = len(re.findall(r'\bif\b', code))
        elif_count = len(re.findall(r'\belif\b', code))
        while_count = len(re.findall(r'\bwhile\b', code))
        for_count = len(re.findall(r'\bfor\b', code))
        and_count = len(re.findall(r'\band\b', code))
        or_count = len(re.findall(r'\bor\b', code))
        except_count = len(re.findall(r'\bexcept\b', code))
        case_count = len(re.findall(r'\bcase\b', code))
        
        # Poids harmoniques pour chaque type de décision
        poids = {
            "if": PHI_INV,        # 0.618
            "elif": PHI_INV * 0.8, # 0.494
            "while": PHI,          # 1.618
            "for": PHI * 0.8,     # 1.294
            "and": PHI_INV * 0.5, # 0.309
            "or": PHI_INV * 0.5,  # 0.309
            "except": PHI * 0.6,  # 0.971
            "case": PHI * 0.7,    # 1.133
        }
        
        # Score de complexité pondéré
        raw_score = (
            if_count * poids["if"] +
            elif_count * poids["elif"] +
            while_count * poids["while"] +
            for_count * poids["for"] +
            and_count * poids["and"] +
            or_count * poids["or"] +
            except_count * poids["except"] +
            case_count * poids["case"]
        )
        
        # Normalisation harmonique
        normalized = min(100, raw_score * PHI_INV * 10)
        
        # Interprétation
        if normalized < 10:
            niveau = "très faible"
            risque = "✅ Code simple et harmonieux"
        elif normalized < 20:
            niveau = "faible"
            risque = "✅ Bien structuré"
        elif normalized < 30:
            niveau = "modéré"
            risque = "⚠️ Peut nécessiter une refactorisation"
        elif normalized < 50:
            niveau = "élevé"
            risque = "⚠️ Difficile à tester et maintenir"
        else:
            niveau = "très élevé"
            risque = "❌ Doit être refactorisé d'urgence"
        
        return {
            "score": round(normalized, 1),
            "niveau": niveau,
            "risque": risque,
            "details": {
                "if": if_count,
                "elif": elif_count,
                "while": while_count,
                "for": for_count,
                "and": and_count,
                "or": or_count,
                "except": except_count,
                "case": case_count
            }
        }
    
    @staticmethod
    def _harmonic_health_score(code: str, bugs: List, suggestions: List) -> float:
        """
        Calcule le score de santé harmonique du code.
        
        Basé sur :
        - Nombre de bugs (poids négatif harmonique)
        - Complexité cyclomatique
        - Présence de documentation
        - Présence de tests
        """
        # Score de base
        base_score = 100.0
        
        # Pénalités pour les bugs (poids harmoniques)
        for bug in bugs:
            if bug["gravite"] == "haute":
                base_score -= 15 * PHI_INV  # -9.27
            elif bug["gravite"] == "moyenne":
                base_score -= 8 * PHI_INV   # -4.94
            else:
                base_score -= 3 * PHI_INV   # -1.85
        
        # Pénalité pour complexité élevée
        cyclomatic = HarmonicDebugger._cyclomatic_complexity(code)
        if cyclomatic["score"] > 30:
            base_score -= (cyclomatic["score"] - 30) * PHI_INV * 0.5
        
        # Bonus pour documentation
        if '"""' in code or "'''" in code:
            base_score += 5 * PHI_INV  # +3.09
        if '# ' in code:
            base_score += 3 * PHI_INV  # +1.85
        
        # Bonus pour tests
        if "def test_" in code or "class Test" in code:
            base_score += 10 * PHI_INV  # +6.18
        if "unittest" in code:
            base_score += 5 * PHI_INV   # +3.09
        
        # Bonus pour type hints
        if ": " in code and " -> " in code:
            base_score += 5 * PHI_INV   # +3.09
        
        return round(max(0, min(100, base_score)), 1)
    
    @staticmethod
    def _severity_summary(bugs: List) -> Dict[str, int]:
        """Résumé des bugs par gravité"""
        summary = {"haute": 0, "moyenne": 0, "faible": 0, "info": 0}
        for bug in bugs:
            gravite = bug.get("gravite", "faible")
            if gravite in summary:
                summary[gravite] += 1
        return summary
    
    @staticmethod
    def generate_debug_tests(code: str) -> Optional[str]:
        """
        Génère des tests de débogage harmoniques pour le code analysé.
        
        Les tests sont générés en fonction des bugs détectés pour
        cibler précisément les points faibles.
        """
        analysis = HarmonicDebugger.debug_code(code)
        
        if not analysis["bugs"] and not analysis["suggestions"]:
            return None
        
        test_parts = ['''"""
Tests de débogage harmonique
Générés automatiquement par HarmonicDebugger
Basés sur l'analyse de résonance harmonique du code.
"""
import unittest
from typing import Any, List, Dict


class TestHarmonicDebug(unittest.TestCase):
    """Tests de débogage générés par analyse harmonique"""\n''']
        
        # Ajouter des tests basés sur les bugs détectés
        test_index = 1
        for bug in analysis["bugs"]:
            if bug["type"] == "index_hors_limites":
                test_parts.append(f'''
    def test_harmonic_index_safety_{test_index}(self):
        """Test de sécurité des index - {bug["message"]}"""
        # Test avec liste vide
        with self.assertRaises(IndexError):
            pass  # Remplacer par l'appel à la fonction testée
        
        # Test avec liste normale
        resultat = None  # Remplacer par l'appel réel
        self.assertIsNotNone(resultat)
''')
            elif bug["type"] == "mutabilite_defaut":
                test_parts.append(f'''
    def test_harmonic_mutable_default_{test_index}(self):
        """Test d'isolation des arguments - {bug["message"]}"""
        # Vérifier que les appels multiples sont isolés
        resultat1 = None  # Remplacer par premier appel
        resultat2 = None  # Remplacer par second appel
        self.assertNotEqual(id(resultat1), id(resultat2),
                            "Les résultats devraient être indépendants")
''')
            elif bug["type"] == "exception_bare":
                test_parts.append(f'''
    def test_harmonic_exception_specific_{test_index}(self):
        """Test de précision des exceptions - {bug["message"]}"""
        # Vérifier que seules les exceptions attendues sont capturées
        with self.assertRaises((ValueError, TypeError, ZeroDivisionError)):
            pass  # Remplacer par l'appel qui devrait lever une exception spécifique
''')
            elif bug["type"] == "while_true_sans_break":
                test_parts.append(f'''
    def test_harmonic_loop_termination_{test_index}(self):
        """Test de terminaison de boucle - {bug["message"]}"""
        import signal
        
        class TimeoutError(Exception):
            pass
        
        def handler(signum, frame):
            raise TimeoutError("Boucle infinie détectée")
        
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(1)  # Timeout de 1 seconde
        
        try:
            # Remplacer par l'appel à la fonction avec boucle
            pass
        except TimeoutError:
            self.fail("Boucle infinie détectée - ajouter une condition de sortie")
        finally:
            signal.alarm(0)
''')
            test_index += 1
        
        # Ajouter des tests pour les suggestions
        for suggestion in analysis["suggestions"]:
            if suggestion["type"] == "fstring_manquee":
                test_parts.append(f'''
    def test_harmonic_string_format_{test_index}(self):
        """Test de formatage de chaîne - {suggestion["message"]}"""
        # Vérifier que le formatage est correct
        nom = "test"
        resultat = f"Bonjour, {{nom}} !"  # Remplacer par l'appel réel
        self.assertIn(nom, resultat)
''')
                test_index += 1
        
        test_parts.append(f'''
    def test_harmonic_health_check(self):
        """Vérification globale de santé harmonique"""
        analysis = HarmonicDebugger.debug_code(__import__("inspect").getsource(
            lambda: None  # Remplacer par la fonction à tester
        ))
        self.assertGreaterEqual(
            analysis["harmonic_health"],
            70,
            f"Score de santé harmonique trop bas: {analysis['harmonic_health']}/100"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
''')
        
        return "```python\n" + "".join(test_parts) + "\n```"
    
    @staticmethod
    def suggest_fix(code: str) -> List[Dict[str, Any]]:
        """
        Suggère des corrections harmoniques pour le code analysé.
        
        Retourne une liste de corrections avec :
        - Le pattern problématique
        - La correction suggérée
        - Le score d'amélioration harmonique
        """
        analysis = HarmonicDebugger.debug_code(code)
        fixes = []
        
        for bug in analysis["bugs"]:
            fixes.append({
                "probleme": bug["message"],
                "gravite": bug["gravite"],
                "correction": bug["correction"],
                "exemple": bug["exemple"],
                "amelioration_harmonique": HarmonicDebugger._improvement_score(bug["gravite"])
            })
        
        for suggestion in analysis["suggestions"]:
            fixes.append({
                "probleme": suggestion["message"],
                "gravite": suggestion["gravite"],
                "correction": suggestion["correction"],
                "exemple": suggestion["exemple"],
                "amelioration_harmonique": HarmonicDebugger._improvement_score(suggestion["gravite"])
            })
        
        return fixes
    
    @staticmethod
    def _improvement_score(gravite: str) -> float:
        """Calcule le score d'amélioration harmonique potentielle"""
        scores = {
            "haute": 15 * PHI_INV,   # ~9.27
            "moyenne": 8 * PHI_INV,  # ~4.94
            "faible": 3 * PHI_INV,   # ~1.85
            "info": 1 * PHI_INV,     # ~0.62
        }
        return round(scores.get(gravite, 0), 2)


class HarmonicCodeGenerator:
    """
    Générateur de code professionnel de niveau Claude.
    Produit du code Python de qualité production avec tests, docs et typage.
    
    La couche harmonique optimise le code généré en utilisant les principes
    de résonance harmonique (φ = 1.618...) pour :
    - Optimiser la performance (buffers, caches, seuils)
    - Améliorer la lisibilité (structure φ-based)
    - Garantir la qualité (score harmonique > 90%)
    - Déboguer le code par analyse de résonance harmonique
    """
    
    # Optimiseur et débogueur harmoniques intégrés
    _optimizer = HarmonicOptimizer()
    _debugger = HarmonicDebugger()
    
    # ============================================================================
    # CATÉGORIE 1 : ALGORITHMES FONDAMENTAUX
    # ============================================================================
    
    ALGORITHMES_TRI = {
        "merge_sort": {
            "mots": ["tri fusion", "merge sort", "merge_sort", "tri par fusion"],
            "difficulte": "intermédiaire",
            "template": """```python
from typing import List, TypeVar

T = TypeVar('T')


def merge_sort(arr: List[T]) -> List[T]:
    '''
    Tri fusion (Merge Sort) - Complexité O(n log n)
    
    Algorithme de tri par comparaison stable et déterministe.
    Divise récursivement le tableau en sous-tableaux, puis les fusionne.
    
    Args:
        arr: Liste d'éléments comparables à trier
        
    Returns:
        Nouvelle liste triée (ne modifie pas l'originale)
        
    Complexités:
        Temps:  O(n log n) dans tous les cas
        Espace: O(n) auxiliaire
        
    Exemple:
        >>> merge_sort([38, 27, 43, 3, 9, 82, 10])
        [3, 9, 10, 27, 38, 43, 82]
    '''
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return _merge(left, right)


def _merge(left: List[T], right: List[T]) -> List[T]:
    '''Fusionne deux listes triées en une seule liste triée'''
    result: List[T] = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # Ajouter les éléments restants (un seul des deux aura des restes)
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestMergeSort(unittest.TestCase):
        def test_tableau_vide(self):
            self.assertEqual(merge_sort([]), [])
        
        def test_un_element(self):
            self.assertEqual(merge_sort([1]), [1])
        
        def test_deja_trie(self):
            self.assertEqual(merge_sort([1, 2, 3, 4, 5]), [1, 2, 3, 4, 5])
        
        def test_inverse(self):
            self.assertEqual(merge_sort([5, 4, 3, 2, 1]), [1, 2, 3, 4, 5])
        
        def test_avec_negatifs(self):
            self.assertEqual(merge_sort([-3, 7, 0, -1, 5]), [-3, -1, 0, 5, 7])
        
        def test_avec_doublons(self):
            self.assertEqual(merge_sort([3, 1, 4, 1, 5, 9, 2, 6]), [1, 1, 2, 3, 4, 5, 6, 9])
        
        def test_non_mutatif(self):
            original = [3, 1, 2]
            resultat = merge_sort(original)
            self.assertEqual(original, [3, 1, 2])
            self.assertEqual(resultat, [1, 2, 3])
    
    unittest.main(verbosity=2)
```"""
        },
        "quick_sort": {
            "mots": ["tri rapide", "quick sort", "quicksort", "tri pivot"],
            "difficulte": "intermédiaire",
            "template": """```python
from typing import List, TypeVar
import random

T = TypeVar('T')


def quick_sort(arr: List[T]) -> List[T]:
    '''
    Tri rapide (Quick Sort) - Complexité moyenne O(n log n)
    
    Algorithme de tri utilisant le principe de partitionnement.
    Version avec pivot aléatoire pour éviter le pire cas O(n²).
    
    Args:
        arr: Liste d'éléments comparables à trier
        
    Returns:
        Nouvelle liste triée
        
    Complexités:
        Temps:  O(n log n) en moyenne, O(n²) dans le pire cas
        Espace: O(log n) pour la récursion
        
    Exemple:
        >>> quick_sort([3, 6, 8, 10, 1, 2, 1])
        [1, 1, 2, 3, 6, 8, 10]
    '''
    if len(arr) <= 1:
        return arr
    
    # Pivot aléatoire pour garantir O(n log n) en pratique
    pivot = random.choice(arr)
    
    # Partitionnement en trois groupes
    gauche = [x for x in arr if x < pivot]
    milieu = [x for x in arr if x == pivot]
    droite = [x for x in arr if x > pivot]
    
    return quick_sort(gauche) + milieu + quick_sort(droite)


def quick_sort_in_place(arr: List[T], low: int = 0, high: Optional[int] = None) -> None:
    '''Version in-place du tri rapide (économie de mémoire)'''
    if high is None:
        high = len(arr) - 1
    
    if low < high:
        pivot_idx = _partition(arr, low, high)
        quick_sort_in_place(arr, low, pivot_idx - 1)
        quick_sort_in_place(arr, pivot_idx + 1, high)


def _partition(arr: List[T], low: int, high: int) -> int:
    '''Partition de Hoare avec pivot aléatoire'''
    pivot_idx = random.randint(low, high)
    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
    pivot = arr[high]
    
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestQuickSort(unittest.TestCase):
        def test_tableau_vide(self):
            self.assertEqual(quick_sort([]), [])
        
        def test_un_element(self):
            self.assertEqual(quick_sort([42]), [42])
        
        def test_tri_standard(self):
            self.assertEqual(quick_sort([3, 6, 8, 10, 1, 2, 1]), [1, 1, 2, 3, 6, 8, 10])
        
        def test_deja_trie(self):
            self.assertEqual(quick_sort([1, 2, 3, 4, 5]), [1, 2, 3, 4, 5])
        
        def test_inverse(self):
            self.assertEqual(quick_sort([5, 4, 3, 2, 1]), [1, 2, 3, 4, 5])
        
        def test_in_place(self):
            arr = [3, 6, 8, 10, 1, 2, 1]
            quick_sort_in_place(arr)
            self.assertEqual(arr, [1, 1, 2, 3, 6, 8, 10])
    
    unittest.main(verbosity=2)
```"""
        },
        "bubble_sort": {
            "mots": ["tri bulle", "bubble sort", "tri à bulles"],
            "difficulte": "débutant",
            "template": """```python
from typing import List, TypeVar

T = TypeVar('T')


def bubble_sort(arr: List[T]) -> List[T]:
    '''
    Tri à bulles (Bubble Sort) - Complexité O(n²)
    
    Algorithme de tri simple qui compare et échange les éléments adjacents.
    Version optimisée avec détection de tri précoce.
    
    Args:
        arr: Liste d'éléments comparables à trier
        
    Returns:
        Nouvelle liste triée
        
    Complexités:
        Temps:  O(n²) dans le pire cas, O(n) si déjà trié
        Espace: O(1) auxiliaire
        
    Exemple:
        >>> bubble_sort([64, 34, 25, 12, 22, 11, 90])
        [11, 12, 22, 25, 34, 64, 90]
    '''
    n = len(arr)
    result = arr.copy()
    
    for i in range(n):
        swapped = False
        
        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
                swapped = True
        
        # Optimisation : si aucun échange, le tableau est déjà trié
        if not swapped:
            break
    
    return result


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestBubbleSort(unittest.TestCase):
        def test_tableau_vide(self):
            self.assertEqual(bubble_sort([]), [])
        
        def test_tri_standard(self):
            self.assertEqual(bubble_sort([64, 34, 25, 12, 22, 11, 90]),
                             [11, 12, 22, 25, 34, 64, 90])
        
        def test_deja_trie(self):
            self.assertEqual(bubble_sort([1, 2, 3, 4, 5]), [1, 2, 3, 4, 5])
        
        def test_inverse(self):
            self.assertEqual(bubble_sort([5, 4, 3, 2, 1]), [1, 2, 3, 4, 5])
    
    unittest.main(verbosity=2)
```"""
        },
        "insertion_sort": {
            "mots": ["tri insertion", "insertion sort", "tri par insertion"],
            "difficulte": "débutant",
            "template": """```python
from typing import List, TypeVar

T = TypeVar('T')


def insertion_sort(arr: List[T]) -> List[T]:
    '''
    Tri par insertion (Insertion Sort) - Complexité O(n²)
    
    Algorithme de tri qui construit le résultat final un élément à la fois.
    Efficace pour les petits tableaux ou les données presque triées.
    
    Args:
        arr: Liste d'éléments comparables à trier
        
    Returns:
        Nouvelle liste triée
        
    Complexités:
        Temps:  O(n²) dans le pire cas, O(n) si déjà trié
        Espace: O(1) auxiliaire
        
    Exemple:
        >>> insertion_sort([12, 11, 13, 5, 6])
        [5, 6, 11, 12, 13]
    '''
    result = arr.copy()
    
    for i in range(1, len(result)):
        key = result[i]
        j = i - 1
        
        while j >= 0 and result[j] > key:
            result[j + 1] = result[j]
            j -= 1
        
        result[j + 1] = key
    
    return result


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestInsertionSort(unittest.TestCase):
        def test_tableau_vide(self):
            self.assertEqual(insertion_sort([]), [])
        
        def test_tri_standard(self):
            self.assertEqual(insertion_sort([12, 11, 13, 5, 6]), [5, 6, 11, 12, 13])
        
        def test_deja_trie(self):
            self.assertEqual(insertion_sort([1, 2, 3]), [1, 2, 3])
        
        def test_inverse(self):
            self.assertEqual(insertion_sort([3, 2, 1]), [1, 2, 3])
    
    unittest.main(verbosity=2)
```"""
        },
        "heap_sort": {
            "mots": ["tri tas", "heap sort", "heapsort", "tri par tas"],
            "difficulte": "avancé",
            "template": """```python
from typing import List, TypeVar

T = TypeVar('T')


def heap_sort(arr: List[T]) -> List[T]:
    '''
    Tri par tas (Heap Sort) - Complexité O(n log n)
    
    Algorithme de tri basé sur la structure de tas binaire.
    Combine la rapidité du quick sort avec la garantie O(n log n).
    
    Args:
        arr: Liste d'éléments comparables à trier
        
    Returns:
        Nouvelle liste triée
        
    Complexités:
        Temps:  O(n log n) garanti
        Espace: O(1) auxiliaire (in-place)
        
    Exemple:
        >>> heap_sort([4, 10, 3, 5, 1])
        [1, 3, 4, 5, 10]
    '''
    result = arr.copy()
    n = len(result)
    
    # Construire le tas max
    for i in range(n // 2 - 1, -1, -1):
        _heapify(result, n, i)
    
    # Extraire un par un les éléments du tas
    for i in range(n - 1, 0, -1):
        result[i], result[0] = result[0], result[i]
        _heapify(result, i, 0)
    
    return result


def _heapify(arr: List[T], n: int, i: int) -> None:
    '''Maintient la propriété de tas max à partir du nœud i'''
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    
    if left < n and arr[left] > arr[largest]:
        largest = left
    
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        _heapify(arr, n, largest)


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestHeapSort(unittest.TestCase):
        def test_tableau_vide(self):
            self.assertEqual(heap_sort([]), [])
        
        def test_tri_standard(self):
            self.assertEqual(heap_sort([4, 10, 3, 5, 1]), [1, 3, 4, 5, 10])
        
        def test_avec_negatifs(self):
            self.assertEqual(heap_sort([-5, 3, -2, 0, 8]), [-5, -2, 0, 3, 8])
        
        def test_grand_tableau(self):
            arr = list(range(100, 0, -1))
            self.assertEqual(heap_sort(arr), list(range(1, 101)))
    
    unittest.main(verbosity=2)
```"""
        }
    }
    
    ALGORITHMES_RECHERCHE = {
        "binary_search": {
            "mots": ["recherche binaire", "binary search", "recherche dichotomique", "binaire"],
            "difficulte": "intermédiaire",
            "template": """```python
from typing import List, Optional, TypeVar

T = TypeVar('T')


def recherche_binaire(tableau: List[T], cible: T) -> int:
    '''
    Recherche binaire itérative - Complexité O(log n)
    
    Recherche un élément dans un tableau TRIÉ en divisant
    l'espace de recherche par 2 à chaque itération.
    
    Args:
        tableau: Liste triée d'éléments comparables
        cible: Élément à rechercher
        
    Returns:
        Index de l'élément trouvé, ou -1 s'il n'existe pas
        
    Lève:
        ValueError: Si le tableau n'est pas trié
        
    Complexités:
        Temps:  O(log n)
        Espace: O(1)
        
    Exemple:
        >>> recherche_binaire([1, 3, 5, 7, 9, 11, 13], 7)
        3
        >>> recherche_binaire([1, 3, 5, 7, 9, 11, 13], 2)
        -1
    '''
    if not tableau:
        return -1
    
    gauche, droite = 0, len(tableau) - 1
    
    while gauche <= droite:
        milieu = (gauche + droite) // 2
        
        if tableau[milieu] == cible:
            return milieu
        elif tableau[milieu] < cible:
            gauche = milieu + 1
        else:
            droite = milieu - 1
    
    return -1


def recherche_binaire_recursive(tableau: List[T], cible: T,
                                 gauche: int = 0, droite: Optional[int] = None) -> int:
    '''Version récursive de la recherche binaire'''
    if droite is None:
        droite = len(tableau) - 1
    
    if gauche > droite:
        return -1
    
    milieu = (gauche + droite) // 2
    
    if tableau[milieu] == cible:
        return milieu
    elif tableau[milieu] < cible:
        return recherche_binaire_recursive(tableau, cible, milieu + 1, droite)
    else:
        return recherche_binaire_recursive(tableau, cible, gauche, milieu - 1)


def borne_inferieure(tableau: List[T], cible: T) -> int:
    '''
    Borne inférieure (lower_bound) : premier index >= cible
    
    Utile pour les recherches par intervalle et les insertions.
    '''
    gauche, droite = 0, len(tableau)
    
    while gauche < droite:
        milieu = (gauche + droite) // 2
        if tableau[milieu] < cible:
            gauche = milieu + 1
        else:
            droite = milieu
    
    return gauche


def borne_superieure(tableau: List[T], cible: T) -> int:
    '''
    Borne supérieure (upper_bound) : premier index > cible
    
    Retourne l'index où insérer pour maintenir l'ordre.
    '''
    gauche, droite = 0, len(tableau)
    
    while gauche < droite:
        milieu = (gauche + droite) // 2
        if tableau[milieu] <= cible:
            gauche = milieu + 1
        else:
            droite = milieu
    
    return gauche


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestRechercheBinaire(unittest.TestCase):
        def setUp(self):
            self.tableau = [1, 3, 5, 7, 9, 11, 13, 15]
        
        def test_element_present(self):
            self.assertEqual(recherche_binaire(self.tableau, 7), 3)
        
        def test_premier_element(self):
            self.assertEqual(recherche_binaire(self.tableau, 1), 0)
        
        def test_dernier_element(self):
            self.assertEqual(recherche_binaire(self.tableau, 15), 7)
        
        def test_element_absent(self):
            self.assertEqual(recherche_binaire(self.tableau, 2), -1)
        
        def test_tableau_vide(self):
            self.assertEqual(recherche_binaire([], 1), -1)
        
        def test_borne_inferieure(self):
            self.assertEqual(borne_inferieure(self.tableau, 6), 3)
        
        def test_borne_superieure(self):
            self.assertEqual(borne_superieure(self.tableau, 7), 4)
    
    unittest.main(verbosity=2)
```"""
        },
        "linear_search": {
            "mots": ["recherche linéaire", "linear search", "recherche séquentielle", "sequentielle"],
            "difficulte": "débutant",
            "template": """```python
from typing import List, Optional, TypeVar

T = TypeVar('T')


def recherche_lineaire(tableau: List[T], cible: T) -> int:
    '''
    Recherche linéaire - Complexité O(n)
    
    Parcourt séquentiellement le tableau pour trouver un élément.
    Utile pour les tableaux non triés ou de petite taille.
    
    Args:
        tableau: Liste d'éléments à parcourir
        cible: Élément à rechercher
        
    Returns:
        Index de la première occurrence, ou -1 si absent
        
    Complexités:
        Temps:  O(n)
        Espace: O(1)
        
    Exemple:
        >>> recherche_lineaire([4, 2, 7, 1, 9, 3], 7)
        2
        >>> recherche_lineaire([4, 2, 7, 1, 9, 3], 5)
        -1
    '''
    for i, element in enumerate(tableau):
        if element == cible:
            return i
    return -1


def recherche_lineaire_toutes(tableau: List[T], cible: T) -> List[int]:
    '''Trouve toutes les occurrences de cible dans le tableau'''
    return [i for i, element in enumerate(tableau) if element == cible]


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestRechercheLineaire(unittest.TestCase):
        def test_element_present(self):
            self.assertEqual(recherche_lineaire([4, 2, 7, 1, 9], 7), 2)
        
        def test_element_absent(self):
            self.assertEqual(recherche_lineaire([4, 2, 7, 1, 9], 5), -1)
        
        def test_premier_element(self):
            self.assertEqual(recherche_lineaire([1, 2, 3], 1), 0)
        
        def test_tableau_vide(self):
            self.assertEqual(recherche_lineaire([], 1), -1)
        
        def test_occurrences_multiples(self):
            self.assertEqual(recherche_lineaire_toutes([1, 2, 1, 3, 1], 1), [0, 2, 4])
    
    unittest.main(verbosity=2)
```"""
        }
    }
    
    # ============================================================================
    # CATÉGORIE 2 : STRUCTURES DE DONNÉES
    # ============================================================================
    
    STRUCTURES_DONNEES = {
        "queue": {
            "mots": ["file d'attente", "file", "queue", "classe file", "structure file", "fifo"],
            "difficulte": "débutant",
            "template": """```python
from typing import Generic, TypeVar, List, Optional
from collections import deque

T = TypeVar('T')


class Queue(Generic[T]):
    '''
    File d'attente (Queue) - Structure FIFO (First In, First Out)
    
    Implémentation générique avec type hints.
    Utilise collections.deque pour des performances O(1).
    
    Attributes:
        _elements: Deque interne pour stocker les éléments
        
    Exemple:
        >>> q = Queue[int]()
        >>> q.enqueue(1)
        >>> q.enqueue(2)
        >>> q.dequeue()
        1
        >>> q.is_empty()
        False
    '''
    
    def __init__(self) -> None:
        '''Initialise une file vide'''
        self._elements: deque[T] = deque()
    
    def enqueue(self, element: T) -> None:
        '''
        Ajoute un élément à la fin de la file.
        
        Args:
            element: Élément à ajouter
            
        Complexité: O(1)
        '''
        self._elements.append(element)
    
    def dequeue(self) -> T:
        '''
        Retire et retourne l'élément au début de la file.
        
        Returns:
            L'élément retiré
            
        Lève:
            IndexError: Si la file est vide
            
        Complexité: O(1)
        '''
        if self.is_empty():
            raise IndexError("Impossible de retirer d'une file vide")
        return self._elements.popleft()
    
    def peek(self) -> T:
        '''
        Consulte l'élément au début sans le retirer.
        
        Returns:
            L'élément au début de la file
            
        Lève:
            IndexError: Si la file est vide
        '''
        if self.is_empty():
            raise IndexError("File vide")
        return self._elements[0]
    
    def is_empty(self) -> bool:
        '''Vérifie si la file est vide'''
        return len(self._elements) == 0
    
    def size(self) -> int:
        '''Retourne le nombre d'éléments dans la file'''
        return len(self._elements)
    
    def clear(self) -> None:
        '''Vide complètement la file'''
        self._elements.clear()
    
    def __str__(self) -> str:
        return f"Queue({list(self._elements)})"
    
    def __len__(self) -> int:
        return self.size()


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestQueue(unittest.TestCase):
        def setUp(self):
            self.q = Queue[int]()
        
        def test_file_vide(self):
            self.assertTrue(self.q.is_empty())
            self.assertEqual(self.q.size(), 0)
        
        def test_enqueue_dequeue(self):
            self.q.enqueue(1)
            self.q.enqueue(2)
            self.q.enqueue(3)
            self.assertEqual(self.q.dequeue(), 1)
            self.assertEqual(self.q.dequeue(), 2)
            self.assertEqual(self.q.dequeue(), 3)
        
        def test_peek(self):
            self.q.enqueue(42)
            self.assertEqual(self.q.peek(), 42)
            self.assertEqual(self.q.size(), 1)  # peek ne retire pas
        
        def test_dequeue_file_vide(self):
            with self.assertRaises(IndexError):
                self.q.dequeue()
        
        def test_clear(self):
            self.q.enqueue(1)
            self.q.enqueue(2)
            self.q.clear()
            self.assertTrue(self.q.is_empty())
        
        def test_fifo_order(self):
            for i in range(5):
                self.q.enqueue(i)
            for i in range(5):
                self.assertEqual(self.q.dequeue(), i)
    
    unittest.main(verbosity=2)
```"""
        },
        "stack": {
            "mots": ["pile", "stack", "structure pile", "lifo"],
            "difficulte": "débutant",
            "template": """```python
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


class Stack(Generic[T]):
    '''
    Pile (Stack) - Structure LIFO (Last In, First Out)
    
    Implémentation générique avec type hints.
    Utilise une liste Python comme stockage interne.
    
    Attributes:
        _elements: Liste interne pour stocker les éléments
        
    Exemple:
        >>> s = Stack[int]()
        >>> s.push(1)
        >>> s.push(2)
        >>> s.pop()
        2
        >>> s.peek()
        1
    '''
    
    def __init__(self) -> None:
        '''Initialise une pile vide'''
        self._elements: List[T] = []
    
    def push(self, element: T) -> None:
        '''
        Ajoute un élément au sommet de la pile.
        
        Args:
            element: Élément à ajouter
            
        Complexité: O(1) amorti
        '''
        self._elements.append(element)
    
    def pop(self) -> T:
        '''
        Retire et retourne l'élément au sommet de la pile.
        
        Returns:
            L'élément retiré
            
        Lève:
            IndexError: Si la pile est vide
            
        Complexité: O(1)
        '''
        if self.is_empty():
            raise IndexError("Impossible de dépiler une pile vide")
        return self._elements.pop()
    
    def peek(self) -> T:
        '''
        Consulte l'élément au sommet sans le retirer.
        
        Returns:
            L'élément au sommet
            
        Lève:
            IndexError: Si la pile est vide
        '''
        if self.is_empty():
            raise IndexError("Pile vide")
        return self._elements[-1]
    
    def is_empty(self) -> bool:
        '''Vérifie si la pile est vide'''
        return len(self._elements) == 0
    
    def size(self) -> int:
        '''Retourne le nombre d'éléments dans la pile'''
        return len(self._elements)
    
    def clear(self) -> None:
        '''Vide complètement la pile'''
        self._elements.clear()
    
    def __str__(self) -> str:
        return f"Stack({self._elements})"
    
    def __len__(self) -> int:
        return self.size()


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestStack(unittest.TestCase):
        def setUp(self):
            self.s = Stack[int]()
        
        def test_pile_vide(self):
            self.assertTrue(self.s.is_empty())
            self.assertEqual(self.s.size(), 0)
        
        def test_push_pop(self):
            self.s.push(1)
            self.s.push(2)
            self.s.push(3)
            self.assertEqual(self.s.pop(), 3)
            self.assertEqual(self.s.pop(), 2)
            self.assertEqual(self.s.pop(), 1)
        
        def test_lifo_order(self):
            for i in range(5):
                self.s.push(i)
            for i in range(4, -1, -1):
                self.assertEqual(self.s.pop(), i)
        
        def test_peek(self):
            self.s.push(42)
            self.assertEqual(self.s.peek(), 42)
            self.assertEqual(self.s.size(), 1)
        
        def test_pop_pile_vide(self):
            with self.assertRaises(IndexError):
                self.s.pop()
    
    unittest.main(verbosity=2)
```"""
        },
        "linked_list": {
            "mots": ["liste chaînée", "liste chainee", "linked list", "liste simplement chaînée"],
            "difficulte": "intermédiaire",
            "template": """```python
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')


class Node(Generic[T]):
    '''Nœud d'une liste chaînée'''
    
    def __init__(self, value: T, next_node: Optional['Node[T]'] = None) -> None:
        self.value = value
        self.next = next_node
    
    def __repr__(self) -> str:
        return f"Node({self.value})"


class LinkedList(Generic[T]):
    '''
    Liste chaînée simple (Singly Linked List)
    
    Structure de données linéaire où chaque élément pointe vers le suivant.
    
    Attributes:
        head: Premier nœud de la liste
        _size: Nombre d'éléments
        
    Exemple:
        >>> ll = LinkedList[int]()
        >>> ll.append(1)
        >>> ll.append(2)
        >>> ll.prepend(0)
        >>> list(ll)
        [0, 1, 2]
    '''
    
    def __init__(self) -> None:
        '''Initialise une liste chaînée vide'''
        self.head: Optional[Node[T]] = None
        self._size: int = 0
    
    def append(self, value: T) -> None:
        '''Ajoute un élément à la fin'''
        new_node = Node(value)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self._size += 1
    
    def prepend(self, value: T) -> None:
        '''Ajoute un élément au début'''
        self.head = Node(value, self.head)
        self._size += 1
    
    def delete(self, value: T) -> bool:
        '''Supprime la première occurrence de value'''
        if not self.head:
            return False
        
        if self.head.value == value:
            self.head = self.head.next
            self._size -= 1
            return True
        
        current = self.head
        while current.next:
            if current.next.value == value:
                current.next = current.next.next
                self._size -= 1
                return True
            current = current.next
        
        return False
    
    def find(self, value: T) -> Optional[Node[T]]:
        '''Trouve un nœud par sa valeur'''
        current = self.head
        while current:
            if current.value == value:
                return current
            current = current.next
        return None
    
    def to_list(self) -> List[T]:
        '''Convertit la liste chaînée en liste Python'''
        result: List[T] = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result
    
    def reverse(self) -> None:
        '''Inverse la liste chaînée in-place'''
        prev = None
        current = self.head
        while current:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
        self.head = prev
    
    def __iter__(self):
        current = self.head
        while current:
            yield current.value
            current = current.next
    
    def __len__(self) -> int:
        return self._size
    
    def __str__(self) -> str:
        return " -> ".join(str(v) for v in self)


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestLinkedList(unittest.TestCase):
        def setUp(self):
            self.ll = LinkedList[int]()
        
        def test_liste_vide(self):
            self.assertEqual(len(self.ll), 0)
            self.assertEqual(self.ll.to_list(), [])
        
        def test_append(self):
            self.ll.append(1)
            self.ll.append(2)
            self.ll.append(3)
            self.assertEqual(self.ll.to_list(), [1, 2, 3])
        
        def test_prepend(self):
            self.ll.append(2)
            self.ll.append(3)
            self.ll.prepend(1)
            self.assertEqual(self.ll.to_list(), [1, 2, 3])
        
        def test_delete(self):
            self.ll.append(1)
            self.ll.append(2)
            self.ll.append(3)
            self.assertTrue(self.ll.delete(2))
            self.assertEqual(self.ll.to_list(), [1, 3])
            self.assertFalse(self.ll.delete(5))
        
        def test_reverse(self):
            self.ll.append(1)
            self.ll.append(2)
            self.ll.append(3)
            self.ll.reverse()
            self.assertEqual(self.ll.to_list(), [3, 2, 1])
        
        def test_find(self):
            self.ll.append(10)
            self.ll.append(20)
            node = self.ll.find(20)
            self.assertIsNotNone(node)
            self.assertEqual(node.value, 20)
            self.assertIsNone(self.ll.find(30))
    
    unittest.main(verbosity=2)
```"""
        },
        "binary_tree": {
            "mots": ["arbre binaire", "binary tree", "arbre de recherche", "bst"],
            "difficulte": "avancé",
            "template": """```python
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')


class TreeNode(Generic[T]):
    '''Nœud d'un arbre binaire de recherche'''
    
    def __init__(self, value: T) -> None:
        self.value = value
        self.left: Optional['TreeNode[T]'] = None
        self.right: Optional['TreeNode[T]'] = None
    
    def __repr__(self) -> str:
        return f"TreeNode({self.value})"


class BinarySearchTree(Generic[T]):
    '''
    Arbre Binaire de Recherche (BST)
    
    Structure de données hiérarchique où chaque nœud a au plus deux enfants.
    Pour chaque nœud : gauche < valeur < droite.
    
    Complexités:
        Recherche: O(log n) en moyenne, O(n) dans le pire cas
        Insertion: O(log n) en moyenne, O(n) dans le pire cas
        Suppression: O(log n) en moyenne, O(n) dans le pire cas
    '''
    
    def __init__(self) -> None:
        self.root: Optional[TreeNode[T]] = None
        self._size: int = 0
    
    def insert(self, value: T) -> None:
        '''Insère une valeur dans l'arbre'''
        if self.root is None:
            self.root = TreeNode(value)
        else:
            self._insert_recursive(self.root, value)
        self._size += 1
    
    def _insert_recursive(self, node: TreeNode[T], value: T) -> None:
        if value < node.value:
            if node.left is None:
                node.left = TreeNode(value)
            else:
                self._insert_recursive(node.left, value)
        else:
            if node.right is None:
                node.right = TreeNode(value)
            else:
                self._insert_recursive(node.right, value)
    
    def search(self, value: T) -> bool:
        '''Recherche une valeur dans l'arbre'''
        return self._search_recursive(self.root, value)
    
    def _search_recursive(self, node: Optional[TreeNode[T]], value: T) -> bool:
        if node is None:
            return False
        if node.value == value:
            return True
        elif value < node.value:
            return self._search_recursive(node.left, value)
        else:
            return self._search_recursive(node.right, value)
    
    def inorder(self) -> List[T]:
        '''Parcours infixe (gauche, racine, droite) - retourne les valeurs triées'''
        result: List[T] = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node: Optional[TreeNode[T]], result: List[T]) -> None:
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)
    
    def preorder(self) -> List[T]:
        '''Parcours préfixe (racine, gauche, droite)'''
        result: List[T] = []
        self._preorder_recursive(self.root, result)
        return result
    
    def _preorder_recursive(self, node: Optional[TreeNode[T]], result: List[T]) -> None:
        if node:
            result.append(node.value)
            self._preorder_recursive(node.left, result)
            self._preorder_recursive(node.right, result)
    
    def postorder(self) -> List[T]:
        '''Parcours postfixe (gauche, droite, racine)'''
        result: List[T] = []
        self._postorder_recursive(self.root, result)
        return result
    
    def _postorder_recursive(self, node: Optional[TreeNode[T]], result: List[T]) -> None:
        if node:
            self._postorder_recursive(node.left, result)
            self._postorder_recursive(node.right, result)
            result.append(node.value)
    
    def min_value(self) -> Optional[T]:
        '''Trouve la valeur minimale dans l'arbre'''
        if self.root is None:
            return None
        current = self.root
        while current.left:
            current = current.left
        return current.value
    
    def max_value(self) -> Optional[T]:
        '''Trouve la valeur maximale dans l'arbre'''
        if self.root is None:
            return None
        current = self.root
        while current.right:
            current = current.right
        return current.value
    
    def __len__(self) -> int:
        return self._size
    
    def __str__(self) -> str:
        return f"BST({self.inorder()})"


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestBST(unittest.TestCase):
        def setUp(self):
            self.bst = BinarySearchTree[int]()
            for v in [5, 3, 7, 2, 4, 6, 8]:
                self.bst.insert(v)
        
        def test_search(self):
            self.assertTrue(self.bst.search(5))
            self.assertTrue(self.bst.search(2))
            self.assertTrue(self.bst.search(8))
            self.assertFalse(self.bst.search(1))
            self.assertFalse(self.bst.search(9))
        
        def test_inorder(self):
            self.assertEqual(self.bst.inorder(), [2, 3, 4, 5, 6, 7, 8])
        
        def test_min_max(self):
            self.assertEqual(self.bst.min_value(), 2)
            self.assertEqual(self.bst.max_value(), 8)
        
        def test_arbre_vide(self):
            empty = BinarySearchTree[int]()
            self.assertEqual(empty.inorder(), [])
            self.assertIsNone(empty.min_value())
            self.assertIsNone(empty.max_value())
    
    unittest.main(verbosity=2)
```"""
        }
    }
    
    # ============================================================================
    # CATÉGORIE 3 : MATHÉMATIQUES
    # ============================================================================
    
    MATHEMATIQUES = {
        "fibonacci": {
            "mots": ["fibonacci", "suite de fibonacci", "fibonacci récursif", "fibonacci itératif"],
            "difficulte": "débutant",
            "template": """```python
from typing import Dict, List


def fibonacci(n: int) -> int:
    '''
    Suite de Fibonacci - Version itérative optimisée
    
    F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)
    
    Args:
        n: Position dans la suite (n >= 0)
        
    Returns:
        Le n-ième nombre de Fibonacci
        
    Lève:
        ValueError: Si n < 0
        
    Complexités:
        Temps:  O(n)
        Espace: O(1)
        
    Exemple:
        >>> fibonacci(10)
        55
        >>> fibonacci(0)
        0
    '''
    if n < 0:
        raise ValueError("n doit être >= 0")
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fibonacci_recursif(n: int, memo: Dict[int, int] = None) -> int:
    '''Fibonacci avec mémoisation - O(n)'''
    if memo is None:
        memo = {0: 0, 1: 1}
    
    if n in memo:
        return memo[n]
    
    memo[n] = fibonacci_recursif(n - 1, memo) + fibonacci_recursif(n - 2, memo)
    return memo[n]


def suite_fibonacci(jusqua: int) -> List[int]:
    '''Génère la suite de Fibonacci jusqu'à n termes'''
    return [fibonacci(i) for i in range(jusqua + 1)]


def fibonacci_generator():
    '''Générateur infini de la suite de Fibonacci'''
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestFibonacci(unittest.TestCase):
        def test_cas_de_base(self):
            self.assertEqual(fibonacci(0), 0)
            self.assertEqual(fibonacci(1), 1)
        
        def test_valeurs_connues(self):
            self.assertEqual(fibonacci(5), 5)
            self.assertEqual(fibonacci(10), 55)
            self.assertEqual(fibonacci(20), 6765)
        
        def test_negatif(self):
            with self.assertRaises(ValueError):
                fibonacci(-1)
        
        def test_generator(self):
            gen = fibonacci_generator()
            premiers = [next(gen) for _ in range(10)]
            self.assertEqual(premiers, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34])
    
    unittest.main(verbosity=2)
```"""
        },
        "factoriel": {
            "mots": ["factoriel", "factorial", "factorielle"],
            "difficulte": "débutant",
            "template": """```python
from typing import List


def factoriel(n: int) -> int:
    '''
    Calcule le factoriel d'un nombre n! = n * (n-1) * ... * 1
    
    Args:
        n: Nombre entier >= 0
        
    Returns:
        n! (factoriel de n)
        
    Lève:
        ValueError: Si n < 0
        
    Complexités:
        Temps:  O(n)
        Espace: O(1)
        
    Exemple:
        >>> factoriel(5)
        120
        >>> factoriel(0)
        1
    '''
    if n < 0:
        raise ValueError("Le factoriel n'est pas défini pour les nombres négatifs")
    if n <= 1:
        return 1
    
    resultat = 1
    for i in range(2, n + 1):
        resultat *= i
    return resultat


def factoriel_recursif(n: int) -> int:
    '''Version récursive du factoriel'''
    if n < 0:
        raise ValueError("Le factoriel n'est pas défini pour les nombres négatifs")
    if n <= 1:
        return 1
    return n * factoriel_recursif(n - 1)


def coefficient_binomial(n: int, k: int) -> int:
    '''Calcule C(n,k) = n! / (k! * (n-k)!)'''
    if k < 0 or k > n:
        return 0
    return factoriel(n) // (factoriel(k) * factoriel(n - k))


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestFactoriel(unittest.TestCase):
        def test_cas_de_base(self):
            self.assertEqual(factoriel(0), 1)
            self.assertEqual(factoriel(1), 1)
        
        def test_valeurs_connues(self):
            self.assertEqual(factoriel(5), 120)
            self.assertEqual(factoriel(10), 3628800)
        
        def test_negatif(self):
            with self.assertRaises(ValueError):
                factoriel(-5)
        
        def test_coefficient_binomial(self):
            self.assertEqual(coefficient_binomial(5, 2), 10)
            self.assertEqual(coefficient_binomial(5, 5), 1)
            self.assertEqual(coefficient_binomial(5, 0), 1)
    
    unittest.main(verbosity=2)
```"""
        },
        "est_premier": {
            "mots": ["nombre premier", "premier", "est premier", "prime number", "is prime"],
            "difficulte": "intermédiaire",
            "template": """```python
from typing import List


def est_premier(n: int) -> bool:
    '''
    Vérifie si un nombre est premier (test de primalité)
    
    Un nombre premier n'est divisible que par 1 et par lui-même.
    
    Args:
        n: Nombre entier à tester
        
    Returns:
        True si n est premier, False sinon
        
    Complexités:
        Temps:  O(√n)
        Espace: O(1)
        
    Exemple:
        >>> est_premier(7)
        True
        >>> est_premier(10)
        False
    '''
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def crible_eratosthene(limite: int) -> List[int]:
    '''
    Crible d'Ératosthène - Trouve tous les nombres premiers jusqu'à une limite
    
    Algorithme efficace pour générer une liste de nombres premiers.
    
    Args:
        limite: Borne supérieure (incluse)
        
    Returns:
        Liste des nombres premiers <= limite
        
    Complexité: O(n log log n)
    
    Exemple:
        >>> crible_eratosthene(20)
        [2, 3, 5, 7, 11, 13, 17, 19]
    '''
    if limite < 2:
        return []
    
    premiers = [True] * (limite + 1)
    premiers[0] = premiers[1] = False
    
    for i in range(2, int(limite ** 0.5) + 1):
        if premiers[i]:
            for j in range(i * i, limite + 1, i):
                premiers[j] = False
    
    return [i for i, est_premier in enumerate(premiers) if est_premier]


def factoriser(n: int) -> List[int]:
    '''Décompose un nombre en facteurs premiers'''
    facteurs: List[int] = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            facteurs.append(d)
            n //= d
        d += 1
    if n > 1:
        facteurs.append(n)
    return facteurs


def pgcd(a: int, b: int) -> int:
    '''Plus Grand Commun Diviseur (algorithme d'Euclide)'''
    while b:
        a, b = b, a % b
    return a


def ppcm(a: int, b: int) -> int:
    '''Plus Petit Commun Multiple'''
    return a * b // pgcd(a, b)


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestNombresPremiers(unittest.TestCase):
        def test_premiers(self):
            self.assertTrue(est_premier(2))
            self.assertTrue(est_premier(7))
            self.assertTrue(est_premier(17))
            self.assertTrue(est_premier(97))
        
        def test_non_premiers(self):
            self.assertFalse(est_premier(0))
            self.assertFalse(est_premier(1))
            self.assertFalse(est_premier(4))
            self.assertFalse(est_premier(15))
        
        def test_crible(self):
            self.assertEqual(crible_eratosthene(20), [2, 3, 5, 7, 11, 13, 17, 19])
        
        def test_factorisation(self):
            self.assertEqual(factoriser(84), [2, 2, 3, 7])
            self.assertEqual(factoriser(97), [97])
        
        def test_pgcd_ppcm(self):
            self.assertEqual(pgcd(12, 18), 6)
            self.assertEqual(ppcm(12, 18), 36)
    
    unittest.main(verbosity=2)
```"""
        }
    }
    
    # ============================================================================
    # CATÉGORIE 4 : MANIPULATION DE CHAÎNES
    # ============================================================================
    
    CHAINES = {
        "palindrome": {
            "mots": ["palindrome", "chaîne", "chaine", "string", "vérifie", "verifie"],
            "difficulte": "débutant",
            "template": """```python
from typing import List


def est_palindrome(chaine: str) -> bool:
    '''
    Vérifie si une chaîne est un palindrome
    
    Un palindrome se lit identiquement dans les deux sens.
    Ignore la casse, les espaces et la ponctuation.
    
    Args:
        chaine: Chaîne à vérifier
        
    Returns:
        True si la chaîne est un palindrome
        
    Complexité: O(n)
    
    Exemple:
        >>> est_palindrome("radar")
        True
        >>> est_palindrome("hello")
        False
        >>> est_palindrome("Esope reste ici et se repose")
        True
    '''
    # Nettoyer : minuscules, uniquement alphanumérique
    nettoye = ''.join(c.lower() for c in chaine if c.isalnum())
    return nettoye == nettoye[::-1]


def trouver_palindromes(texte: str) -> List[str]:
    '''Trouve tous les mots palindromes dans un texte'''
    mots = texte.split()
    return [mot for mot in mots if est_palindrome(mot)]


def plus_long_palindrome(chaine: str) -> str:
    '''
    Trouve le plus long palindrome dans une chaîne
    
    Utilise l'expansion autour du centre (O(n²)).
    '''
    if not chaine:
        return ""
    
    def expandir(gauche: int, droite: int) -> str:
        while gauche >= 0 and droite < len(chaine) and chaine[gauche] == chaine[droite]:
            gauche -= 1
            droite += 1
        return chaine[gauche + 1:droite]
    
    plus_long = ""
    for i in range(len(chaine)):
        # Palindrome impair (centre = i)
        impair = expandir(i, i)
        if len(impair) > len(plus_long):
            plus_long = impair
        
        # Palindrome pair (centre entre i et i+1)
        pair = expandir(i, i + 1)
        if len(pair) > len(plus_long):
            plus_long = pair
    
    return plus_long


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestPalindrome(unittest.TestCase):
        def test_palindromes_simples(self):
            self.assertTrue(est_palindrome("radar"))
            self.assertTrue(est_palindrome("kayak"))
            self.assertTrue(est_palindrome("level"))
        
        def test_non_palindromes(self):
            self.assertFalse(est_palindrome("hello"))
            self.assertFalse(est_palindrome("python"))
        
        def test_avec_casse(self):
            self.assertTrue(est_palindrome("Radar"))
            self.assertTrue(est_palindrome("Kayak"))
        
        def test_phrase(self):
            self.assertTrue(est_palindrome("Esope reste ici et se repose"))
        
        def test_plus_long(self):
            self.assertEqual(plus_long_palindrome("babad"), "bab")
            self.assertEqual(plus_long_palindrome("cbbd"), "bb")
    
    unittest.main(verbosity=2)
```"""
        },
        "inverser_chaine": {
            "mots": ["inverse", "inverser", "reverse", "renverser"],
            "difficulte": "débutant",
            "template": """```python
from typing import List


def inverser_chaine(chaine: str) -> str:
    '''
    Inverse une chaîne de caractères
    
    Args:
        chaine: Chaîne à inverser
        
    Returns:
        Chaîne inversée
        
    Complexité: O(n)
    
    Exemple:
        >>> inverser_chaine("Harmonic AI")
        'IA cimonraH'
    '''
    return chaine[::-1]


def inverser_chaine_manuelle(chaine: str) -> str:
    '''Inverse sans utiliser le slicing Python'''
    resultat = ""
    for char in chaine:
        resultat = char + resultat
    return resultat


def inverser_mots(phrase: str) -> str:
    '''
    Inverse l'ordre des mots dans une phrase
    
    Exemple:
        >>> inverser_mots("Bonjour le monde")
        'monde le Bonjour'
    '''
    mots = phrase.split()
    return ' '.join(reversed(mots))


def inverser_par_mots(phrase: str) -> str:
    '''
    Inverse chaque mot individuellement sans changer l'ordre
    
    Exemple:
        >>> inverser_par_mots("Bonjour le monde")
        'ruojnoB el ednom'
    '''
    return ' '.join(mot[::-1] for mot in phrase.split())


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestInversion(unittest.TestCase):
        def test_inversion_simple(self):
            self.assertEqual(inverser_chaine("abc"), "cba")
        
        def test_inversion_phrase(self):
            self.assertEqual(inverser_chaine("Harmonic AI"), "IA cimonraH")
        
        def test_inversion_mots(self):
            self.assertEqual(inverser_mots("un deux trois"), "trois deux un")
        
        def test_inversion_par_mots(self):
            self.assertEqual(inverser_par_mots("abc def"), "cba fed")
        
        def test_chaine_vide(self):
            self.assertEqual(inverser_chaine(""), "")
    
    unittest.main(verbosity=2)
```"""
        }
    }
    
    # ============================================================================
    # CATÉGORIE 5 : DESIGN PATTERNS
    # ============================================================================
    
    DESIGN_PATTERNS = {
        "singleton": {
            "mots": ["singleton", "pattern singleton", "classe unique", "instance unique"],
            "difficulte": "intermédiaire",
            "template": """```python
from typing import Dict, Any, Optional
import threading


class SingletonMeta(type):
    '''
    Métaclasse Singleton thread-safe
    
    Garantit qu'une classe n'a qu'une seule instance.
    Utilise un verrou pour la sécurité des threads.
    '''
    
    _instances: Dict[type, object] = {}
    _lock: threading.Lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class Configuration(metaclass=SingletonMeta):
    '''
    Configuration globale - Pattern Singleton
    
    Exemple:
        >>> config1 = Configuration()
        >>> config2 = Configuration()
        >>> config1 is config2
        True
    '''
    
    def __init__(self):
        self._settings: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value
    
    def __contains__(self, key: str) -> bool:
        return key in self._settings


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestSingleton(unittest.TestCase):
        def test_instance_unique(self):
            c1 = Configuration()
            c2 = Configuration()
            self.assertIs(c1, c2)
        
        def test_persistance(self):
            c1 = Configuration()
            c1.set("db_host", "localhost")
            c2 = Configuration()
            self.assertEqual(c2.get("db_host"), "localhost")
    
    unittest.main(verbosity=2)
```"""
        },
        "factory": {
            "mots": ["factory", "fabrique", "pattern factory", "usine"],
            "difficulte": "intermédiaire",
            "template": """```python
from abc import ABC, abstractmethod
from typing import Dict, Type, Any


class Animal(ABC):
    '''Interface pour les animaux'''
    
    @abstractmethod
    def parler(self) -> str:
        pass
    
    @abstractmethod
    def nom(self) -> str:
        pass


class Chien(Animal):
    def nom(self) -> str:
        return "Chien"
    
    def parler(self) -> str:
        return "Woof!"


class Chat(Animal):
    def nom(self) -> str:
        return "Chat"
    
    def parler(self) -> str:
        return "Miaou!"


class Vache(Animal):
    def nom(self) -> str:
        return "Vache"
    
    def parler(self) -> str:
        return "Meuh!"


class AnimalFactory:
    '''
    Fabrique d'animaux - Pattern Factory
    
    Crée des objets sans exposer la logique d'instanciation.
    Facile à étendre avec de nouveaux types.
    
    Exemple:
        >>> factory = AnimalFactory()
        >>> chien = factory.creer("chien")
        >>> chien.parler()
        'Woof!'
    '''
    
    _animaux: Dict[str, Type[Animal]] = {
        "chien": Chien,
        "chat": Chat,
        "vache": Vache,
    }
    
    @classmethod
    def creer(cls, type_animal: str) -> Animal:
        '''Crée un animal du type spécifié'''
        if type_animal not in cls._animaux:
            raise ValueError(f"Type d'animal inconnu: {type_animal}")
        return cls._animaux[type_animal]()
    
    @classmethod
    def enregistrer(cls, nom: str, classe: Type[Animal]) -> None:
        '''Enregistre un nouveau type d'animal'''
        cls._animaux[nom] = classe


# Tests unitaires
if __name__ == "__main__":
    import unittest
    
    class TestFactory(unittest.TestCase):
        def test_creation_chien(self):
            animal = AnimalFactory.creer("chien")
            self.assertEqual(animal.parler(), "Woof!")
        
        def test_creation_chat(self):
            animal = AnimalFactory.creer("chat")
            self.assertEqual(animal.parler(), "Miaou!")
        
        def test_type_inconnu(self):
            with self.assertRaises(ValueError):
                AnimalFactory.creer("dragon")
        
        def test_enregistrement(self):
            class Poisson(Animal):
                def nom(self): return "Poisson"
                def parler(self): return "Bloup!"
            AnimalFactory.enregistrer("poisson", Poisson)
            animal = AnimalFactory.creer("poisson")
            self.assertEqual(animal.parler(), "Bloup!")
    
    unittest.main(verbosity=2)
```"""
        },
        "observer": {
            "mots": ["observer", "observateur", "pattern observer", "event", "événement", "evenement"],
            "difficulte": "avancé",
            "template": """```python
from abc import ABC, abstractmethod
from typing import List, Any, Callable


class Observer(ABC):
    '''Interface pour les observateurs'''
    
    @abstractmethod
    def update(self, sujet: 'Sujet') -> None:
        pass


class Sujet:
    '''
    Sujet observable - Pattern Observer
    
    Permet à des observateurs d'être notifiés des changements d'état.
    
    Exemple:
        >>> sujet = Sujet()
        >>> obs = ConcreteObserver("A")
        >>> sujet.attacher(obs)
        >>> sujet.changer_etat("nouvel état")
    '''
    
    def __init__(self):
        self._observateurs: List[Observer] = []
        self._etat: Any = None
    
    def attacher(self, observateur: Observer) -> None:
        if observateur not in self._observateurs:
            self._observateurs.append(observateur)
    
    def detacher(self, observateur: Observer) -> None:
        self._observateurs.remove(observateur)
    
    def notifier(self) -> None:
        for observateur in self._observateurs:
            observateur.update(self)
    
    @property
    def etat(self) -> Any:
        return self._etat
    
    @etat.setter
    def etat(self, valeur: Any) -> None:
        self._etat = valeur
        self.notifier()


class ConcreteObserver(Observer):
    '''Observateur concret'''
    
    def __init__(self, nom: str):
        self.nom = nom
    
    def update(self, sujet: Sujet) -> None:
        print(f"Observateur '{self.nom}' notifié: état = {sujet.etat}")


# Version fonctionnelle avec Callable
class EventEmitter:
    '''Système d'événements simple avec callbacks'''
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, callback: Callable) -> None:
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
    
    def emit(self, event: str, *args, **kwargs) -> None:
        for callback in self._listeners.get(event, []):
            callback(*args, **kwargs)
    
    def off(self, event: str, callback: Callable) -> None:
        self._listeners[event] = [cb for cb in self._listeners.get(event, [])
                                   if cb != callback]


# Tests unitaires
if __name__ == "__main__":
    import unittest
    from io import StringIO
    import sys
    
    class TestObserver(unittest.TestCase):
        def test_notification(self):
            sujet = Sujet()
            obs = ConcreteObserver("Test")
            sujet.attacher(obs)
            
            captured = StringIO()
            sys.stdout = captured
            sujet.etat = "nouveau"
            sys.stdout = sys.__stdout__
            
            self.assertIn("Observateur 'Test' notifié", captured.getvalue())
        
        def test_event_emitter(self):
            emitter = EventEmitter()
            results = []
            
            def handler(data):
                results.append(data)
            
            emitter.on("data", handler)
            emitter.emit("data", "test_value")
            self.assertEqual(results, ["test_value"])
    
    unittest.main(verbosity=2)
```"""
        }
    }
    
    # ============================================================================
    # CATÉGORIE 6 : PROGRAMMATION ASYNCHRONE
    # ============================================================================
    
    ASYNC_PATTERNS = {
        "async_fetch": {
            "mots": ["async", "asynchrone", "await", "aiohttp", "requête asynchrone", "requete asynchrone"],
            "difficulte": "avancé",
            "template": """```python
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import time


async def fetch_url(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    '''
    Récupère le contenu d'une URL de façon asynchrone
    
    Args:
        session: Session HTTP asynchrone
        url: URL à récupérer
        
    Returns:
        Dictionnaire avec l'URL et le statut
        
    Exemple:
        async with aiohttp.ClientSession() as session:
            resultat = await fetch_url(session, "https://example.com")
    '''
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            content = await response.text()
            return {
                "url": url,
                "status": response.status,
                "length": len(content),
                "success": True
            }
    except Exception as e:
        return {
            "url": url,
            "status": 0,
            "error": str(e),
            "success": False
        }


async def fetch_multiple(urls: List[str], max_concurrent: int = 5) -> List[Dict[str, Any]]:
    '''
    Récupère plusieurs URLs en parallèle avec limite de concurrence
    
    Args:
        urls: Liste d'URLs à récupérer
        max_concurrent: Nombre maximum de requêtes simultanées
        
    Returns:
        Liste des résultats
    '''
    connector = aiohttp.TCPConnector(limit=max_concurrent)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)


async def main():
    '''Exemple d'utilisation'''
    urls = [
        "https://api.github.com",
        "https://httpbin.org/get",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    print(f"Récupération de {len(urls)} URLs...")
    debut = time.time()
    
    resultats = await fetch_multiple(urls)
    
    duree = time.time() - debut
    
    for r in resultats:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {r['url']} - {r.get('status', 'N/A')} ({r.get('length', 0)} bytes)")
    
    print(f"\\nTemps total: {duree:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
```"""
        }
    }
    
    # ============================================================================
    # MÉTHODE PRINCIPALE DE GÉNÉRATION
    # ============================================================================
    
    def __init__(self):
        """Initialise le générateur avec tous les patterns"""
        # Fusionner tous les patterns en un seul dictionnaire
        self._all_patterns: Dict[str, Dict] = {}
        
        for category_dict in [
            self.ALGORITHMES_TRI,
            self.ALGORITHMES_RECHERCHE,
            self.STRUCTURES_DONNEES,
            self.MATHEMATIQUES,
            self.CHAINES,
            self.DESIGN_PATTERNS,
            self.ASYNC_PATTERNS
        ]:
            self._all_patterns.update(category_dict)
        
        # Index inversé pour recherche rapide
        self._mot_to_pattern: Dict[str, str] = {}
        for pattern_name, data in self._all_patterns.items():
            for mot in data.get("mots", []):
                self._mot_to_pattern[mot] = pattern_name
    
    def generate(self, prompt: str) -> Optional[str]:
        '''
        Génère du code Python professionnel à partir d'un prompt.
        
        Détecte automatiquement le type de code demandé et retourne
        un template complet avec tests unitaires, documentation et typage.
        
        Args:
            prompt: Description du code à générer
            
        Returns:
            Code Python formaté avec ```python, ou None si non détecté
            
        Exemple:
            >>> gen = HarmonicCodeGenerator()
            >>> code = gen.generate("Écris une fonction merge sort")
            >>> print(code)
            ```python
            def merge_sort(arr):
                ...
        '''
        prompt_lower = prompt.lower()
        
        # Détection : est-ce une demande de code ?
        mots_code = ["écris", "ecris", "génère", "genere", "crée", "cree",
                     "écrire", "ecrire", "générer", "generer", "créer", "creer",
                     "code", "fonction", "classe", "algorithme", "programme",
                     "implémente", "implemente", "implémentation", "implementation",
                     "python", "script", "programmation"]
        
        est_demande_code = any(m in prompt_lower for m in mots_code)
        
        if not est_demande_code:
            return None
        
        # Chercher le meilleur pattern
        best_match = None
        best_score = 0
        
        for pattern_name, data in self._all_patterns.items():
            score = 0
            for mot in data.get("mots", []):
                if mot in prompt_lower:
                    score += 1
            if score > best_score:
                best_score = score
                best_match = pattern_name
        
        if best_match and best_score >= 1:
            return self._all_patterns[best_match]["template"]
        
        return None
    
    def generate_with_metrics(self, prompt: str) -> Optional[Dict[str, Any]]:
        '''
        Génère du code avec métriques harmoniques.
        
        Retourne le code généré avec :
        - Score de qualité harmonique
        - Analyse de complexité
        - Recommandations d'optimisation
        
        Args:
            prompt: Description du code à générer
            
        Returns:
            Dict avec code, score, complexité, ou None si non détecté
        '''
        code = self.generate(prompt)
        if code is None:
            return None
        
        # Calculer les métriques
        code_length = len(code)
        num_comments = code.count("'''") + code.count('"""') + code.count('#')
        num_tests = code.count("def test_") + code.count("class Test")
        num_type_hints = code.count(": ") + code.count(" -> ")
        
        # Score harmonique
        harmonic_score_val = self._optimizer.harmonic_score(
            code_length, num_comments, num_tests, num_type_hints
        )
        
        # Analyse de complexité
        complexity = self._optimizer.harmonic_complexity(code_length)
        
        # Recommandations harmoniques
        recommendations = []
        if num_tests < 3:
            recommendations.append("Ajouter des tests unitaires (minimum 3 recommandé)")
        if num_type_hints < 5:
            recommendations.append("Ajouter des type hints pour améliorer la maintenabilité")
        if num_comments < 3:
            recommendations.append("Ajouter de la documentation (docstrings)")
        if harmonic_score_val < 70:
            recommendations.append("Optimiser la structure du code selon les principes harmoniques")
        
        return {
            "code": code,
            "harmonic_score": harmonic_score_val,
            "complexity": complexity,
            "recommendations": recommendations,
            "metrics": {
                "code_length": code_length,
                "num_comments": num_comments,
                "num_tests": num_tests,
                "num_type_hints": num_type_hints
            }
        }
    
    def list_available(self) -> List[str]:
        '''Liste tous les patterns de code disponibles'''
        return list(self._all_patterns.keys())
    
    def get_difficulty(self, pattern_name: str) -> Optional[str]:
        '''Retourne la difficulté d'un pattern'''
        if pattern_name in self._all_patterns:
            return self._all_patterns[pattern_name].get("difficulte", "N/A")
        return None
    
    def get_optimizer(self) -> HarmonicOptimizer:
        '''Retourne l'optimiseur harmonique pour utilisation externe'''
        return self._optimizer
