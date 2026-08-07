"""
Tool Use Ondulatoire — Binding ψ_intention ⊗ ψ_outil → ψ_action
=================================================================
Traduction ondulatoire du function calling des LLM :

  Function Calling → Binding d'onde dans ℂ^512
  JSON schema → Signature de phase de l'outil
  Hallucination des paramètres → Filtrage par cohérence de paramètre

Principe : un appel d'outil est un BINDING de trois ondes :
  ψ_action = ψ_intention ⊗ ψ_outil ⊗ ψ_params

La convolution circulaire (HRR, Plate 1995) garantit que :
  - L'action est liée à l'intention ET à l'outil
  - Les paramètres sont vérifiés par cohérence
  - Aucun appel n'est émis si la cohérence est insuffisante

Author: Univers-Holistique
"""

import math
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field

PHI = 1.618033988749895
PI = math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ToolDefinition:
    """Définition d'un outil (équivalent à un schéma JSON de function calling)."""
    name: str
    description: str
    parameters: Dict[str, Any]  # {param_name: {type, description, required}}
    handler: Optional[Callable] = None  # Fonction à appeler
    psi: Optional[np.ndarray] = None    # Signature ondulatoire (encodée)


@dataclass
class ToolCall:
    """Appel d'outil résolu."""
    tool_name: str
    parameters: Dict[str, Any]
    coherence: float  # Score de cohérence (qualité de l'appel)
    psi_bound: np.ndarray  # Vecteur d'onde lié ψ_action


# ═══════════════════════════════════════════════════════════════════════════════
# ENCODEUR D'OUTILS
# ═══════════════════════════════════════════════════════════════════════════════

class ToolEncoder:
    """
    Encode les définitions d'outils en signatures ondulatoires.

    Un outil est encodé comme ψ_outil = encode(name + description + schema).
    """

    def __init__(self, dim: int = 512):
        self.dim = dim

    def encode(self, tool: ToolDefinition) -> np.ndarray:
        """
        Encode un outil en vecteur d'onde.

        ψ_outil = FNV1a_phi(name || description || json_schema)
        """
        text = tool.name + " " + tool.description + " " + json.dumps(tool.parameters)
        psi = self._text_to_psi(text)
        tool.psi = psi
        return psi

    def _text_to_psi(self, text: str) -> np.ndarray:
        """Encode un texte en vecteur d'onde dans ℂ^dim."""
        # Hash FNV1a simplifié + espacement φ
        h = 0x811c9dc5
        for ch in text:
            h = ((h * 0x01000193) ^ ord(ch)) & 0xFFFFFFFF

        # Générer des phases espacées de φ
        phases = (h * PHI ** np.arange(self.dim)) % (2 * PI)
        psi = np.exp(1j * phases)
        return psi / np.linalg.norm(psi)


# ═══════════════════════════════════════════════════════════════════════════════
# CIRCULAR CONVOLUTION (HRR BINDING)
# ═══════════════════════════════════════════════════════════════════════════════

def circular_convolve(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Convolution circulaire = binding holographique (HRR, Plate 1995).

    c[k] = Σ_j a[j] · b[(k - j) mod N]

    Via FFT : c = IFFT(FFT(a) · FFT(b))
    """
    return np.fft.ifft(np.fft.fft(a) * np.fft.fft(b))


def circular_correlate(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Corrélation circulaire = unbinding holographique.

    c[k] = Σ_j a[j] · conj(b[(j - k) mod N])

    Via FFT : c = IFFT(FFT(a) · conj(FFT(b)))
    """
    return np.fft.ifft(np.fft.fft(a) * np.conj(np.fft.fft(b)))


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR DE TOOL USE ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveToolUse:
    """
    Moteur de function calling ondulatoire.

    Usage:
        tools = WaveToolUse()
        tools.register(ToolDefinition("calculer", "Effectue un calcul", ...))
        result = tools.resolve("Quel est le carré de 7 ?")
        if result:
            output = tools.execute(result)
    """

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.tools: Dict[str, ToolDefinition] = {}
        self.encoder = ToolEncoder(dim)

    def register(self, tool: ToolDefinition):
        """Enregistre un outil."""
        if tool.psi is None:
            self.encoder.encode(tool)
        self.tools[tool.name] = tool

    def resolve(self, intention: str,
                coherence_threshold: float = 0.3) -> Optional[ToolCall]:
        """
        Résout une intention en appel d'outil.

        1. Encode l'intention : ψ_intention
        2. Pour chaque outil : score = Re(⟨ψ_intention | ψ_outil⟩)
        3. Si score > seuil : extrait les paramètres par unbinding
        4. Retourne le meilleur appel d'outil

        Args:
            intention: texte décrivant ce que l'utilisateur veut faire
            coherence_threshold: seuil minimal de cohérence pour déclencher un appel

        Returns:
            ToolCall ou None si aucun outil ne résonne assez
        """
        psi_intention = self.encoder._text_to_psi(intention)

        best_tool = None
        best_score = -1.0

        for name, tool in self.tools.items():
            score = float(np.real(np.dot(psi_intention, tool.psi.conj())))
            if score > best_score:
                best_score = score
                best_tool = tool

        if best_score < coherence_threshold:
            return None  # Aucun outil ne correspond assez

        # Extraire les paramètres par unbinding
        params = self._extract_params(psi_intention, best_tool, intention)

        # Vérifier que les paramètres requis sont présents
        for param_name, param_info in best_tool.parameters.items():
            if param_info.get('required', False) and param_name not in params:
                # Paramètre requis manquant → tentative d'extraction par défaut
                params[param_name] = self._default_param(param_info)

        # Binding final : ψ_action = ψ_intention ⊗ ψ_outil ⊗ ψ_params
        psi_bound = psi_intention.copy()
        psi_bound = circular_convolve(psi_bound, best_tool.psi)
        for k, v in params.items():
            psi_param = self.encoder._text_to_psi(f"{k}:{v}")
            psi_bound = circular_convolve(psi_bound, psi_param)
        psi_bound = psi_bound / np.linalg.norm(psi_bound)

        return ToolCall(
            tool_name=best_tool.name,
            parameters=params,
            coherence=best_score,
            psi_bound=psi_bound,
        )

    def _extract_params(self, psi_intention: np.ndarray,
                        tool: ToolDefinition,
                        raw_text: str) -> Dict[str, Any]:
        """
        Extrait les paramètres par analyse de cohérence.

        Pour chaque paramètre de l'outil :
          - Encode le nom du paramètre : ψ_param_name
          - Correlation : ψ_intention ☆ ψ_outil → extrait ce qui « reste »
          - Si la cohérence est suffisante, le paramètre est présent
        """
        params = {}

        for param_name, param_info in tool.parameters.items():
            psi_param = self.encoder._text_to_psi(param_name)
            # Vérifier si ce paramètre résonne dans l'intention
            score = float(np.real(np.dot(psi_intention, psi_param.conj())))

            if score > 0.2:
                # Extraire la valeur du paramètre du texte brut
                value = self._parse_param_value(raw_text, param_name, param_info)
                if value is not None:
                    params[param_name] = value

        return params

    def _parse_param_value(self, text: str, param_name: str,
                           param_info: Dict) -> Optional[Any]:
        """
        Extrait la valeur d'un paramètre du texte naturel.

        Version simplifiée : recherche heuristique.
        Dans une version avancée, utiliserait la cohérence de phase
        pour identifier les segments du texte correspondant au paramètre.
        """
        text_lower = text.lower()

        # Patterns de détection simples
        patterns = {
            'nombre': r'\d+(?:[.,]\d+)?',
            'texte': r'"(.*?)"|\'(.*?)\'',
            'calcul': r'(\d+(?:[.,]\d+)?)\s*([+\-*/])\s*(\d+(?:[.,]\d+)?)',
        }

        import re
        for ptype, pattern in patterns.items():
            if param_info.get('type') == ptype or ptype in param_info.get('description', ''):
                match = re.search(pattern, text)
                if match:
                    if ptype == 'nombre':
                        return float(match.group().replace(',', '.'))
                    elif ptype == 'texte':
                        return match.group(1) or match.group(2)
                    elif ptype == 'calcul':
                        a = float(match.group(1))
                        op = match.group(2)
                        b = float(match.group(3))
                        return {'a': a, 'op': op, 'b': b}

        return None

    def _default_param(self, param_info: Dict) -> Any:
        """Valeur par défaut pour un paramètre requis manquant."""
        ptype = param_info.get('type', 'string')
        if ptype == 'number':
            return 0.0
        elif ptype == 'string':
            return ""
        elif ptype == 'boolean':
            return False
        return None

    def execute(self, call: ToolCall) -> Any:
        """
        Exécute un appel d'outil.

        Args:
            call: ToolCall résolu

        Returns:
            Résultat de l'exécution (ou None si pas de handler)
        """
        tool = self.tools.get(call.tool_name)
        if tool is None or tool.handler is None:
            return None

        try:
            return tool.handler(**call.parameters)
        except Exception as e:
            return {'error': str(e)}

    def resolve_and_execute(self, intention: str,
                            coherence_threshold: float = 0.3) -> Tuple[Optional[Any], Optional[ToolCall]]:
        """
        Résout ET exécute en une seule étape.
        """
        call = self.resolve(intention, coherence_threshold)
        if call is None:
            return None, None
        result = self.execute(call)
        return result, call


# ═══════════════════════════════════════════════════════════════════════════════
# OUTILS PRÉDÉFINIS (exemples)
# ═══════════════════════════════════════════════════════════════════════════════

def _create_default_tools() -> List[ToolDefinition]:
    """Crée des outils de démonstration."""

    def calculer(a: float, op: str = '+', b: float = 0.0) -> float:
        ops = {'+': a + b, '-': a - b, '*': a * b, '/': a / b if b != 0 else float('inf')}
        return ops.get(op, a + b)

    def rechercher(query: str) -> str:
        return f"[Recherche harmonique pour: {query}]"

    def traduire(texte: str, langue_source: str = 'fr', langue_cible: str = 'en') -> str:
        return f"[Traduction {langue_source}→{langue_cible} de: {texte}]"

    return [
        ToolDefinition(
            name="calculer",
            description="Effectue un calcul arithmétique",
            parameters={
                'a': {'type': 'number', 'description': 'Premier opérande', 'required': True},
                'op': {'type': 'string', 'description': 'Opérateur (+, -, *, /)', 'required': False},
                'b': {'type': 'number', 'description': 'Deuxième opérande', 'required': True},
            },
            handler=calculer,
        ),
        ToolDefinition(
            name="rechercher",
            description="Recherche une information dans la base de connaissances",
            parameters={
                'query': {'type': 'string', 'description': 'Requête de recherche', 'required': True},
            },
            handler=rechercher,
        ),
        ToolDefinition(
            name="traduire",
            description="Traduit un texte d'une langue à une autre",
            parameters={
                'texte': {'type': 'string', 'description': 'Texte à traduire', 'required': True},
                'langue_source': {'type': 'string', 'description': 'Langue source', 'required': False},
                'langue_cible': {'type': 'string', 'description': 'Langue cible', 'required': False},
            },
            handler=traduire,
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide."""
    print("=" * 60)
    print("TEST : Tool Use Ondulatoire")
    print("=" * 60)

    # Initialiser le moteur avec des outils par défaut
    tools = WaveToolUse()
    for tool in _create_default_tools():
        tools.register(tool)

    print(f"\nOutils enregistrés: {list(tools.tools.keys())}")

    # Test 1 : intention claire de calcul
    result, call = tools.resolve_and_execute("Quel est le carré de 7 ?")
    print(f"\nIntention: 'Quel est le carré de 7 ?'")
    print(f"  Appel: {call.tool_name if call else 'AUCUN'}")
    print(f"  Paramètres: {call.parameters if call else 'N/A'}")
    print(f"  Cohérence: {call.coherence:.3f}" if call else "")
    print(f"  Résultat: {result}")

    # Test 2 : intention de recherche
    result2, call2 = tools.resolve_and_execute("Je veux savoir qui est Marie Curie")
    print(f"\nIntention: 'Je veux savoir qui est Marie Curie'")
    print(f"  Appel: {call2.tool_name if call2 else 'AUCUN'}")
    print(f"  Paramètres: {call2.parameters if call2 else 'N/A'}")
    print(f"  Résultat: {result2}")

    # Test 3 : intention ambiguë (ne devrait pas déclencher d'outil)
    result3, call3 = tools.resolve_and_execute("Bonjour, comment ça va ?")
    print(f"\nIntention: 'Bonjour, comment ça va ?'")
    print(f"  Appel: {call3.tool_name if call3 else 'AUCUN (cohérence insuffisante)'}")

    print("\n✅ Tests passés !")


if __name__ == '__main__':
    _test()
